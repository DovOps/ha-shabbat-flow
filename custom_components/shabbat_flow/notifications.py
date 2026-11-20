"""Optional, explicit lifecycle SMS; never device control or public reports."""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from .engine.schedule import digest

PHONE = re.compile(r'\+[1-9][0-9]{6,14}\Z')
DEFAULT = {'enabled':False,'reminder_enabled':False,'reminder_offsets':[180,60,30],'push_enabled':False,'push_service':'','sender':'','recipient':'','language':'en','climate':True,'plan':True,'started':True,'stopped':True,'completed':True,'report_link':True}


def capability(hass):
    providers=hass.data.get('twilio_sms_ui',{})
    senders=sorted({n for data in providers.values() if isinstance(data,dict) for n in data.get('phone_numbers',[]) if isinstance(n,str) and PHONE.fullmatch(n)}) if isinstance(providers,dict) else []
    available=bool(senders and hass.services.has_service('twilio_sms_ui','send_message'))
    raw=getattr(hass.config,'external_url',None)
    if not raw and isinstance(providers,dict):
        urls={d.get('external_url') for d in providers.values() if isinstance(d,dict) and isinstance(d.get('external_url'),str) and d['external_url']}
        raw=next(iter(urls)) if len(urls)==1 else None
    url=None
    if isinstance(raw,str):
        try:
            parsed=urlsplit(raw)
            if parsed.scheme=='https' and parsed.hostname and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment and not any(c in raw for c in ('{','}','\n','\r')): url=raw.rstrip('/')
        except ValueError: pass
    push=sorted(n for n in hass.services.async_services().get('notify',{}) if re.fullmatch(r'mobile_app_[a-z0-9_]+',n)) if hass.data.get('mobile_app') else []
    from .reminders import status
    reminder=status(hass)
    return {'reminder_available':bool(push and reminder['available']),'issur_off':reminder['issur_off'],'push_available':bool(push),'push_services':push,'available':available,'senders':senders,'report_url_available':bool(url),'external_url':url,
            'reason':'available' if available else 'unavailable'}


def validate(value,hass,check_capability=True):
    if not isinstance(value,dict) or set(value)!=set(DEFAULT): raise ValueError('observe_sms_settings')
    for key in ('enabled','push_enabled','reminder_enabled','climate','plan','started','stopped','completed','report_link'):
        if type(value[key]) is not bool: raise ValueError('observe_sms_settings')
    if value['language'] not in ('en','he') or not isinstance(value['sender'],str) or not isinstance(value['recipient'],str): raise ValueError('observe_sms_settings')
    if value['recipient'] and not PHONE.fullmatch(value['recipient']): raise ValueError('observe_sms_settings')
    if value['sender'] and not PHONE.fullmatch(value['sender']): raise ValueError('observe_sms_settings')
    offsets=value['reminder_offsets']
    if not isinstance(offsets,list) or not 1<=len(offsets)<=8 or any(type(v) is not int or not 5<=v<=720 for v in offsets) or len(set(offsets))!=len(offsets): raise ValueError('observe_sms_settings')
    cap=capability(hass) if check_capability else {'available':False,'senders':[],'push_services':[],'reminder_available':False}
    if value['enabled'] and (not cap['available'] or value['sender'] not in cap['senders'] or not PHONE.fullmatch(value['recipient'])): raise ValueError('observe_sms_unavailable')
    if not isinstance(value['push_service'],str) or (value['push_service'] and not re.fullmatch(r'mobile_app_[a-z0-9_]+',value['push_service'])): raise ValueError('observe_sms_settings')
    if value['push_enabled'] and value['push_service'] not in cap['push_services']: raise ValueError('observe_sms_unavailable')
    if value['reminder_enabled'] and (not cap['reminder_available'] or value['push_service'] not in cap['push_services']): raise ValueError('observe_sms_unavailable')
    return deepcopy(value)


class Notifications:
    def __init__(self,hass):
        self.hass=hass;self.path=Path(hass.config.path('.storage','shabbat_flow.notifications'))
        self.data={'settings':deepcopy(DEFAULT),'revision':0,'events':[]};self.error=None;self.lock=asyncio.Lock();self.worker=None;self.closed=False;self.unsubscribe=None;self.calendar_checked=None;self.calendar_snapshot=None;self.reminder_error=None

    async def load(self):
        def read():
            if not self.path.exists(): return self.data
            if self.path.stat().st_size>2*1024*1024: raise ValueError()
            wrapper=json.loads(self.path.read_text());data=wrapper['data']
            if digest(data)!=wrapper['checksum'] or not isinstance(data['events'],list) or len(data['events'])>500 or type(data['revision']) is not int or data['revision']<0: raise ValueError()
            settings=deepcopy(data['settings']);settings['enabled']=False;settings['push_enabled']=False;settings['reminder_enabled']=False
            validate(settings,self.hass,check_capability=False)
            if type(data['settings']['enabled']) is not bool or type(data['settings']['push_enabled']) is not bool or type(data['settings']['reminder_enabled']) is not bool: raise ValueError()
            keys=set()
            for e in data['events']:
                if not isinstance(e,dict) or not re.fullmatch('[a-f0-9]{32}',e['run_id']) or e['kind'] not in ('climate','plan','reminder') or e['event'] not in ('started','stopped','completed','reminder') or e['status'] not in ('pending','dispatching','interrupted_unknown','submitted_unconfirmed','cancelled','unavailable','failed') or type(e['revision']) is not int or e['revision']>data['revision'] or not isinstance(e['at'],str): raise ValueError()
                if e.get('channel') not in ('sms','push') or e['key']!=e['run_id']+':'+e['event']+':'+e['channel'] or e['key'] in keys: raise ValueError()
                if e['kind']=='reminder':
                    if e['event']!='reminder' or e['channel']!='push':raise ValueError()
                    for k in ('due','candle'):
                        if datetime.fromisoformat(e[k]).tzinfo is None:raise ValueError()
                keys.add(e['key'])
            return data
        try: self.data=await self.hass.async_add_executor_job(read)
        except Exception: self.error='store'
        # A persisted claim has uncertain delivery; never replay it.
        for event in self.data['events']:
            if event['status']=='dispatching':event['status']='interrupted_unknown'
        self.kick()
        from homeassistant.helpers.event import async_track_time_interval
        self.unsubscribe=async_track_time_interval(self.hass,self.reminder_tick,timedelta(minutes=1))

    async def reminder_tick(self,now):
        from .reminders import tick
        try:
            await tick(self,now);self.reminder_error=None
        except Exception:self.reminder_error='reminder_check'

    async def save(self,data):
        from .observe import atomic_save
        try: await self.hass.async_add_executor_job(atomic_save,self.path,data)
        except Exception:
            self.error='store';raise ValueError('observe_sms_store') from None
        self.data=data

    def listing(self):
        cap=capability(self.hass);cap.pop('external_url',None)
        return {'capability':cap,'settings':deepcopy(self.data['settings']),'error':self.error,'reminder_error':self.reminder_error,
                'events':[{k:e[k] for k in ('run_id','event','status','at','channel')} for e in self.data['events'][-20:]]}

    async def configure(self,value):
        value=validate(value,self.hass)
        async with self.lock:
            if self.error or self.closed:raise ValueError('observe_sms_store')
            data=deepcopy(self.data);data['settings']=value;data['revision']+=1
            for e in data['events']:
                if e['status']=='pending':e['status']='cancelled'
            await self.save(data)
        return self.listing()

    async def record(self,old,new):
        if self.error or self.closed:return
        async with self.lock:
            data=deepcopy(self.data);cfg=data['settings'];changed=False
            if not cfg['enabled'] and not cfg['push_enabled']:return
            for rid,run in new['runs'].items():
                previous=old['runs'].get(rid,{}).get('status');status=run['status']
                kind='climate' if run.get('kind')=='climate_study' else 'plan'
                event={'observing':'started','stopped':'stopped','completed':'completed'}.get(status)
                if previous==status or not event or not cfg[kind] or not cfg[event]:continue
                for channel,enabled in [('sms',cfg['enabled']),('push',cfg['push_enabled'])]:
                    key=rid+':'+event+':'+channel
                    if not enabled or any(e['key']==key for e in data['events']):continue
                    data['events'].append({'key':key,'channel':channel,'run_id':rid,'kind':kind,'event':event,'status':'pending','revision':data['revision'],'at':datetime.now(timezone.utc).isoformat()});changed=True
            if changed:
                data['events']=data['events'][-500:];await self.save(data)
        self.kick()

    def kick(self):
        if not self.closed and not self.error and (self.worker is None or self.worker.done()):
            self.worker=self.hass.async_create_task(self.flush())

    async def flush(self):
        while not self.closed and not self.error:
            async with self.lock:
                existing=next((e for e in self.data['events'] if e['status']=='pending'),None)
                if existing is None:return
                data=deepcopy(self.data);event=next(e for e in data['events'] if e['key']==existing['key']);cfg=data['settings'];cap=capability(self.hass)
                if not cfg['reminder_enabled' if event['kind']=='reminder' else 'enabled' if event['channel']=='sms' else 'push_enabled'] or event['revision']!=data['revision']:event['status']='cancelled'
                elif (event['channel']=='sms' and (not cap['available'] or cfg['sender'] not in cap['senders'])) or (event['channel']=='push' and cfg['push_service'] not in cap['push_services']):event['status']='unavailable'
                else:event['status']='dispatching'
                if event['kind']=='reminder':
                    from .reminders import allowed
                    if not allowed(self.hass,event,datetime.now(timezone.utc)):event['status']='cancelled'
                try:await self.save(data)
                except ValueError:return
            if event['status']!='dispatching':continue
            if event['kind']=='reminder':
                message='ShabbatFlow: נא להכין ולבדוק את תוכנית השבת / החג לפני הדלקת נרות.' if cfg['language']=='he' else 'ShabbatFlow: Please prepare and review your Shabbat / Yom Tov plan before candle lighting.'
            elif cfg['language']=='he':
                kind='מחקר אקלים' if event['kind']=='climate' else 'מעקב שבת / חג'
                message='ShabbatFlow: '+kind+' '+{'started':'התחיל','stopped':'הופסק','completed':'הושלם'}[event['event']]+'.'
            else:message='ShabbatFlow: '+('Climate study' if event['kind']=='climate' else 'Shabbat / Yom Tov observation')+' '+event['event']+'.'
            if event['channel']=='sms' and cfg['report_link'] and event['event'] in ('stopped','completed') and cap['external_url']:
                message+=' '+cap['external_url']+'/shabbat-flow?report='+event['run_id']
            outcome='submitted_unconfirmed'
            try:
                domain,service,payload='twilio_sms_ui','send_message',{'target':[cfg['recipient']],'from_number':cfg['sender'],'message':message}
                if event['channel']=='push':
                    domain,service,payload='notify',cfg['push_service'],{'title':'ShabbatFlow','message':message}
                    if event['kind']=='reminder':payload['data']={'url':'/shabbat-flow','clickAction':'/shabbat-flow'}
                    if cfg['report_link'] and event['event'] in ('stopped','completed'):
                        path='/shabbat-flow?report='+event['run_id']
                        payload['data']={'url':path,'clickAction':path}
                await asyncio.wait_for(self.hass.services.async_call(domain,service,payload,blocking=True),timeout=10)
            except asyncio.CancelledError:raise
            except Exception:outcome='failed'
            async with self.lock:
                data=deepcopy(self.data)
                saved=next((e for e in data['events'] if e['key']==event['key']),None)
                if saved is not None:saved['status']=outcome
                try:await self.save(data)
                except ValueError:return

    def close(self):
        self.closed=True
        if self.unsubscribe:self.unsubscribe();self.unsubscribe=None
        if self.worker and not self.worker.done():self.worker.cancel()
