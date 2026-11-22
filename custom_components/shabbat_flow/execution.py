"""Explicitly armed binary-lighting pilot. Preview and observation never call this adapter."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from uuid import uuid4

from homeassistant.core import Context
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.helpers.event import async_track_time_interval
from .engine.schedule import compile_schedule, digest
from .observe import atomic_save, reading, resolve_mapping, DEFAULT_POLICY
from .ownership import automation_sources, instant
from .household import internal_id

CONTRACT = 1
ACTIVE = {'armed', 'running'}
TERMINAL = {'confirmed', 'already_correct', 'satisfied_uncertain', 'superseded'}
DEFAULT_RECOVERY = {'enabled': False, 'boot_delay_minutes': 5, 'interval_minutes': 30}


def now_utc(): return datetime.now(timezone.utc)


def recovery(value):
    if not isinstance(value, dict) or set(value) != set(DEFAULT_RECOVERY) or type(value['enabled']) is not bool:
        raise ValueError('execute_invalid')
    for key, lo, hi in [('boot_delay_minutes', 1, 60), ('interval_minutes', 5, 1440)]:
        if type(value[key]) is not int or not lo <= value[key] <= hi: raise ValueError('execute_invalid')
    return deepcopy(value)


def source_scope(hass):
    """Conservative write sets, including reactive automations omitted from the timeline."""
    from homeassistant.helpers.target import TargetSelection, async_extract_referenced_entity_ids
    sources, accessible = automation_sources(hass)
    result = []
    for source in sources:
        if source['available'] and not source['enabled']: continue
        targets, unknown = set(), []
        raw = source['config']
        def walk(node, depth=0):
            if depth > 20: unknown.append(True); return
            if isinstance(node, list):
                for item in node: walk(item, depth+1)
                return
            if not isinstance(node, dict): unknown.append(True); return
            if node.get('enabled') is False: return
            service = node.get('action', node.get('service'))
            if service is not None:
                if not isinstance(service, str) or service not in ({'climate.'+s for s in ('set_hvac_mode','set_temperature','set_fan_mode','set_preset_mode','set_swing_mode','set_swing_horizontal_mode')}|{'fan.'+s for s in ('set_percentage','set_preset_mode','set_direction','oscillate')}|{d+'.'+s for d in ('light','switch','climate','fan','homeassistant') for s in ('turn_on','turn_off','toggle')}):
                    unknown.append(True); return
                selection = node.get('target', {})
                data = node.get('data', node.get('service_data', {}))
                if not isinstance(selection, dict) or not isinstance(data, dict) or 'data_template' in node:
                    unknown.append(True); return
                selection = {**selection, **({'entity_id':data['entity_id']} if 'entity_id' in data else {})}
                if not selection or set(selection)-{'entity_id','device_id','area_id','floor_id','label_id'} or '{{' in json.dumps(selection):
                    unknown.append(True); return
                try:
                    found = async_extract_referenced_entity_ids(hass, TargetSelection(selection))
                    ids = found.referenced | found.indirectly_referenced
                    if not ids or any(getattr(found,k,set()) for k in ('missing_devices','missing_areas','missing_labels','missing_floors')): unknown.append(True)
                    targets.update(ids)
                except Exception: unknown.append(True)
                return
            handled = False
            for key in ('sequence','default','parallel'):
                if key in node: handled=True; walk(node[key],depth+1)
            if 'choose' in node:
                if not isinstance(node['choose'],list):unknown.append(True)
                handled=True
                for item in node['choose'] if isinstance(node['choose'],list) else []: walk(item,depth+1)
            if 'repeat' in node:
                handled=True; walk(node['repeat'],depth+1)
            if not handled and not set(node) & {'condition','delay','wait_template','wait_for_trigger','stop','variables'}:
                unknown.append(True)
        if not raw or not source['available']: unknown.append(True)
        else: walk(raw.get('actions',raw.get('action',[])))
        result.append({'id':source['id'],'name':source['name'],'targets':sorted(targets),'unknown':bool(unknown),
                       'unreadable':not raw or not source['available']})
    fingerprint = digest({'sources':sources,'resolved':result,'accessible':accessible})
    return {'accessible':accessible,'sources':result,'fingerprint':fingerprint}


def load_store(path):
    if not path.exists(): return {'schema_version':CONTRACT,'runs':{}}
    if path.stat().st_size > 50*1024*1024: raise ValueError('execute_store')
    envelope=json.loads(path.read_text()); data=envelope['data']
    if digest(data)!=envelope['checksum'] or data['schema_version']!=CONTRACT or not isinstance(data['runs'],dict) or len(data['runs'])>20:
        raise ValueError('execute_store')
    for rid,r in data['runs'].items():
        if r['id']!=rid or r['contract']!=CONTRACT or digest(r['bundle'])!=r['snapshot_hash'] or r['status'] not in {'approved','armed','running','completed','disarmed','blocked'}:
            raise ValueError('execute_store')
        recovery(r['recovery'])
        compiled=compile_schedule(**r['bundle'])
        expected=[e for e in compiled['events'] if e['physical_id'] in r['included'] and e['intent']!='track_only']
        if expected!=r['events'] or len(expected)>5000 or set(r['mapping'])!=set(r['included']): raise ValueError('execute_store')
        if digest(r['sealed'])!=r['approval_digest'] or r['sealed']!={k:r[k] for k in ('snapshot_hash','included','mapping','events','source_fingerprint','recovery','qualifications','attestations','start','end','contract')}:
            raise ValueError('execute_store')
        if not isinstance(r['ledger'],dict) or len(r['ledger'])>5200: raise ValueError('execute_store')
    return data


class Executor:
    def __init__(self,hass):
        self.hass=hass; self.path=Path(hass.config.path('.storage','shabbat_flow.execution'))
        self.data={'schema_version':CONTRACT,'runs':{}};self.lock=asyncio.Lock();self.tick_lock=asyncio.Lock()
        self.error=None;self.closed=False;self.cancel=None;self.boot=now_utc();self.resumed=set();self.inflight=set()

    async def load(self):
        try:
            self.data=await self.hass.async_add_executor_job(load_store,self.path)
            self.resumed={r['id'] for r in self.data['runs'].values() if r['status'] in ACTIVE}
        except Exception: self.error='execute_store'
        self.cancel=async_track_time_interval(self.hass,self.tick,timedelta(seconds=1))

    async def close(self):
        self.closed=True
        if self.cancel:self.cancel();self.cancel=None
        async with self.tick_lock: pass  # Await bounded calls already dispatched; never start another.

    async def commit(self,data):
        try:await self.hass.async_add_executor_job(atomic_save,self.path,data)
        except Exception:self.error='execute_store';raise ValueError('execute_store') from None
        self.data=data

    def public(self,r):
        return {'timezone':r['bundle']['plan']['snapshot']['timezone'], **{k:deepcopy(r[k]) for k in ('id','status','revision','approval_digest','snapshot_hash','start','end','included','excluded','mapping','ledger','blocked','changed','recovery','observer_id','events') if k in r}}

    def listing(self):return {'error':self.error,'runs':[{k:v for k,v in self.public(r).items() if k not in ('ledger','events','changed')} for r in self.data['runs'].values()]}

    async def review(self,bundle,now=None):
        now=now or now_utc()
        if self.error or self.closed:raise ValueError('execute_store')
        if not isinstance(bundle,dict) or set(bundle)!={'config','plan'}:raise ValueError('execute_invalid')
        preview=await self.hass.async_add_executor_job(compile_schedule,bundle['config'],bundle['plan'])
        if not preview['complete']:raise ValueError('execute_incomplete')
        snapshot=bundle['plan']['snapshot'];start,end=instant(snapshot['preparation_start']),instant(snapshot['end'])
        if not 0<(end-start).total_seconds()<=96*3600 or len(preview['events'])>5000:raise ValueError('execute_invalid')
        scope=source_scope(self.hass);mapping,_=resolve_mapping(self.hass,bundle)
        mapping={p:{**t,**self.target_identity(t)} for p,t in mapping.items()}
        household=self.hass.data['shabbat_flow']['household']
        approved_lighting={internal_id('load_',eid) for room in household['rooms'].values() if room.get('enabled') and room.get('setup',{}).get('status','ready')=='ready' for role in ('main_lights','night_lights') for eid in room['roles'][role]}
        loads=[]
        for physical in sorted({l['physical_id'] for l in bundle['config']['loads'].values()}):
            aliases=[l for l in bundle['config']['loads'].values() if l['physical_id']==physical]
            target=mapping.get(physical);events=[e for e in preview['events'] if e['physical_id']==physical];reasons=[]
            if not target: reasons.append('execute_mapping')
            if physical not in approved_lighting or any(l['kind']!='binary' or l.get('display',{}).get('role') not in ('main_lights','night_lights') for l in aliases) or not target or target['entity_id'].split('.')[0] not in ('light','switch'): reasons.append('execute_unsupported')
            if not events or any(e['intent']=='track_only' or e['action'].get('type')!='state' for e in events):reasons.append('execute_no_events')
            # Existing external releases cannot be reconciled or owned by this pilot.
            if any(rule.get('external_release') and any(bundle['config']['loads'][t]['physical_id']==physical for t in rule['targets']) for g in bundle['config']['groups'].values() for rule in g['rules']):reasons.append('execute_handoff')
            state=self.hass.states.get(target['entity_id']) if target else None
            if target and (target['platform'] in ('group','template') or state and state.attributes.get('entity_id')):reasons.append('execute_unsupported')
            observed=reading(self.hass,target) if target else {'state':'unknown'}
            if observed['state']=='unknown':reasons.append('execute_unavailable')
            if target and any(not self.hass.services.has_service(target['entity_id'].split('.')[0],s) for s in ('turn_on','turn_off')):reasons.append('execute_service')
            writers=[s['id'] for s in scope['sources'] if target and target['entity_id'] in s['targets']]
            if writers:reasons.append('execute_writer')
            if not scope['accessible'] or any(s['unreadable'] for s in scope['sources']):reasons.append('execute_source')
            loads.append({'physical_id':physical,'name':aliases[0]['label'],'entity_id':target['entity_id'] if target else None,'state':observed['state'],'first_event':events[0] if events else None,'last_event':events[-1] if events else None,'reasons':sorted(set(reasons)),'writers':writers})
        result={'snapshot_hash':digest(bundle),'source_fingerprint':scope['fingerprint'],'mapping':mapping,'loads':loads,'unknown_sources':[{'id':s['id'],'name':s['name']} for s in scope['sources'] if s['unknown'] and not s['unreadable']], 'start':start.isoformat(),'end':end.isoformat(),'deadline':(start-timedelta(minutes=5)).isoformat(),'has_home':any(a['state']=='home' for a in bundle['plan']['availability'])}
        result['review_digest']=digest(result);return result

    async def approve(self,bundle,included,review_digest,qualifications,attestations,options,request_id,actor,now=None,acknowledge_exclusions=False):
        now=now or now_utc();options=recovery(options)
        if acknowledge_exclusions is not True:raise ValueError('execute_exclusions')
        if not isinstance(request_id,str) or not 8<=len(request_id)<=100 or not isinstance(included,list) or not 0<len(included)<=100 or len(set(included))!=len(included):raise ValueError('execute_invalid')
        if not isinstance(qualifications,dict) or set(qualifications)!=set(included) or any(not isinstance(v,str) or not 10<=len(v)<=1000 for v in qualifications.values()):raise ValueError('execute_qualification')
        if not isinstance(attestations,dict) or len(attestations)>200 or any(not isinstance(v,str) or not 10<=len(v)<=1000 for v in attestations.values()):raise ValueError('execute_attestation')
        identity=digest([bundle,sorted(included),qualifications,attestations,options])
        async with self.lock:
            for r in self.data['runs'].values():
                if r['request_id']==request_id:
                    if r['identity']!=identity:raise ValueError('execute_stale')
                    return self.public(r)
            report=await self.review(bundle,now)
            if report['review_digest']!=review_digest:raise ValueError('execute_stale')
            if not report['has_home']:raise ValueError('execute_away')
            if now>=instant(report['deadline']):raise ValueError('execute_deadline')
            by_id={l['physical_id']:l for l in report['loads']}
            if any(i not in by_id or by_id[i]['reasons'] for i in included):raise ValueError('execute_blocked')
            required={s['id']+'|'+i for s in report['unknown_sources'] for i in included}
            if set(attestations)!=required:raise ValueError('execute_attestation')
            compiled=compile_schedule(**bundle);events=[e for e in compiled['events'] if e['physical_id'] in included and e['intent']!='track_only']
            if any(instant(e['utc'])<instant(report['start']) for e in events):raise ValueError('execute_invalid')
            data=deepcopy(self.data);data['runs']={k:r for k,r in data['runs'].items() if r['status'] in ACTIVE or (now-instant(r['end'])).days<90}
            if len(data['runs'])>=20:raise ValueError('execute_limit')
            rid=uuid4().hex
            r={'id':rid,'contract':CONTRACT,'status':'approved','revision':1,'request_id':request_id,'identity':identity,'actor':actor,'bundle':deepcopy(bundle),'snapshot_hash':digest(bundle),'included':sorted(included),'excluded':sorted(set(by_id)-set(included)),'mapping':{i:report['mapping'][i] for i in included},'events':events,'source_fingerprint':report['source_fingerprint'],'recovery':options,'qualifications':deepcopy(qualifications),'attestations':deepcopy(attestations),'start':report['start'],'end':report['end'],'ledger':{},'blocked':{},'changed':{},'observer_id':None,'created_at':now.isoformat(),'last_tick':now.isoformat()}
            r['sealed']={k:deepcopy(r[k]) for k in ('snapshot_hash','included','mapping','events','source_fingerprint','recovery','qualifications','attestations','start','end','contract')};r['approval_digest']=digest(r['sealed']);data['runs'][rid]=r
            await self.commit(data);return self.public(r)

    async def arm(self,rid,revision,approval_digest,now=None):
        now=now or now_utc()
        async with self.lock:
            if self.error or self.closed:raise ValueError('execute_store')
            r=self.data['runs'].get(rid)
            if not r:raise ValueError('execute_missing')
            if r['status'] in ACTIVE and r['approval_digest']==approval_digest and r.get('armed_revision')==revision:return self.public(r)
            if r['status']!='approved' or r['revision']!=revision or r['approval_digest']!=approval_digest:raise ValueError('execute_stale')
            report=await self.review(r['bundle'],now)
            if now>=instant(report['deadline']):raise ValueError('execute_deadline')
            if report['source_fingerprint']!=r['source_fingerprint'] or any(l['reasons'] for l in report['loads'] if l['physical_id'] in r['included']) or any(report['mapping'].get(i)!=r['mapping'][i] for i in r['included']):raise ValueError('execute_stale')
            for old in self.data['runs'].values():
                if old['status'] in ACTIVE and instant(old['start'])<instant(r['end']) and instant(old['end'])>instant(r['start']) and set(old['included'])&set(r['included']):raise ValueError('execute_overlap')
            rehearsal=self.hass.data['shabbat_flow'].get('rehearsal')
            if rehearsal and rehearsal.overlaps(r['included'],instant(r['start']),instant(r['end'])):raise ValueError('execute_overlap')
            observer=self.hass.data['shabbat_flow']['observer']
            observation=await observer.start(r['bundle'],DEFAULT_POLICY,'execution-'+rid,r['actor'],now)
            data=deepcopy(self.data);r=data['runs'][rid];r.update(status='armed',revision=revision+1,armed_revision=revision,observer_id=observation['id'],armed_at=now.isoformat())
            await self.commit(data);return self.public(r)

    async def disarm(self,rid,revision):
        async with self.lock:
            if self.error:raise ValueError('execute_store')
            r=self.data['runs'].get(rid)
            if not r:raise ValueError('execute_missing')
            if r['status']=='disarmed':return self.public(r)
            if r['revision']!=revision:raise ValueError('execute_stale')
            data=deepcopy(self.data);r=data['runs'][rid];r.update(status='disarmed',revision=revision+1,disarmed_at=now_utc().isoformat());await self.commit(data)
            return {**self.public(r),'inflight':sum(k[0]==rid for k in self.inflight)}

    async def block(self,rid,physical,reason):
        async with self.lock:
            if self.error:return
            data=deepcopy(self.data);r=data['runs'][rid];r['blocked'][physical]=reason
            await self.commit(data)

    def target_identity(self,target):
        entry=er.async_get(self.hass).async_get(target['entity_id'])
        device=dr.async_get(self.hass).async_get(entry.device_id) if entry and entry.device_id else None
        return {'device_id':entry.device_id if entry else None,'config_entry_id':entry.config_entry_id if entry else None,'area_id':entry.area_id or (device.area_id if device else None) if entry else None}

    def valid_target(self,r,physical):
        target=r['mapping'][physical];entry=er.async_get(self.hass).async_get(target['entity_id'])
        rooms=self.hass.data['shabbat_flow']['household']['rooms'].values()
        approved=any(room.get('enabled') and room.get('setup',{}).get('status','ready')=='ready' and any(entry and entry.id in room['roles'][role] for role in ('main_lights','night_lights')) for room in rooms)
        return bool(approved and entry and entry.id==target['registry_id'] and entry.platform==target['platform'] and entry.disabled_by is None and all(target.get(k)==v for k,v in self.target_identity(target).items()))

    def dispatch_guard(self,r,physical):return None

    def service_command(self,r,physical,wanted):
        entity=r['mapping'][physical]['entity_id']
        return entity.split('.')[0],'turn_'+wanted,{'entity_id':entity}

    async def dispatch(self,rid,physical,event,key,now,correction=False):
        now=max(now,now_utc())
        async with self.lock:
            if self.error or self.closed:return
            observer=self.hass.data['shabbat_flow']['observer']
            if observer.error or observer.closed:self.error='execute_observer';return
            data=deepcopy(self.data);r=data['runs'][rid]
            if r['status'] not in ACTIVE or physical in r['blocked'] or (now>instant(r['end']) and not (not correction and instant(event['utc'])==instant(r['end']) and now<=instant(r['end'])+timedelta(seconds=120))):return
            if not self.valid_target(r,physical):
                r['blocked'][physical]='execute_mapping';await self.commit(data);return
            if not correction and (now-instant(event['utc'])).total_seconds()>120:
                r['blocked'][physical]='execute_missed';await self.commit(data);return
            if source_scope(self.hass)['fingerprint']!=r['source_fingerprint']:
                r['blocked'][physical]='execute_source_changed';await self.commit(data);return
            guard=self.dispatch_guard(r,physical)
            if guard:r['blocked'][physical]=guard;await self.commit(data);return
            state=reading(self.hass,r['mapping'][physical]);wanted=event['action']['state']
            if state['state']=='unknown':r['blocked'][physical]='execute_unavailable';await self.commit(data);return
            record={'event_id':event['id'],'physical_id':physical,'wanted':wanted,'scheduled_at':event['utc'],'at':now.isoformat(),'correction':correction,'status':'already_correct' if state['state']==wanted else 'dispatching'}
            r['ledger'][key]=record
            if correction:
                changed=r['changed'][physical];changed['corrections']=changed.get('corrections',0)+1;changed['last_correction']=now.isoformat()
            if record['status']=='already_correct':await self.commit(data);return
            context=Context();record['context_id']=context.id
            await self.commit(data)  # Write-ahead: failure prevents the physical call.
            if self.closed:return
            if (max(now,now_utc())-instant(event['utc'])).total_seconds()>120 and not correction:
                data=deepcopy(self.data);data['runs'][rid]['ledger'][key]['status']='not_dispatched';data['runs'][rid]['blocked'][physical]='execute_missed';await self.commit(data);return
            guard=self.dispatch_guard(r,physical)
            if guard or not self.valid_target(r,physical) or source_scope(self.hass)['fingerprint']!=r['source_fingerprint']:
                data=deepcopy(self.data);data['runs'][rid]['ledger'][key]['status']='not_dispatched';data['runs'][rid]['blocked'][physical]=guard or 'execute_source_changed';await self.commit(data);return
            latest=reading(self.hass,r['mapping'][physical])
            if latest['state']!=state['state']:
                data=deepcopy(self.data)
                if latest['state']==wanted:data['runs'][rid]['ledger'][key]['status']='already_correct'
                else:
                    data['runs'][rid]['ledger'][key]['status']='not_dispatched';data['runs'][rid]['blocked'][physical]='execute_unavailable'
                await self.commit(data);return
            self.inflight.add((rid,key))
            domain,service,service_data=self.service_command(r,physical,wanted)
            # No yield between the final lifecycle check and starting the explicit service call.
            call=self.hass.services.async_call(domain,service,service_data,blocking=True,context=context)
        try:
            async with asyncio.timeout(10):await call
            outcome='acknowledged'
        except Exception:outcome='uncertain'
        finally:self.inflight.discard((rid,key))
        async with self.lock:
            if self.error:return
            data=deepcopy(self.data);record=data['runs'][rid]['ledger'][key];record.update(status=outcome,acknowledged_at=now_utc().isoformat());await self.commit(data)

    async def tick(self,now):
        if self.error or self.closed or self.tick_lock.locked():return
        async with self.tick_lock:
            try:await self._tick(now)
            except Exception:self.error='execute_store'

    async def _tick(self,now):
        pending=[]
        async with self.lock:
            data=deepcopy(self.data)
            for rid,r in data['runs'].items():
                if r['status'] not in ACTIVE:continue
                start,end=instant(r['start']),instant(r['end'])
                if now<start:continue
                if now<instant(r['last_tick']):continue
                if rid in self.resumed and now<self.boot+timedelta(minutes=r['recovery']['boot_delay_minutes']):continue
                r['status']='running'
                if source_scope(self.hass)['fingerprint']!=r['source_fingerprint']:
                    r['blocked'].update({p:'execute_source_changed' for p in r['included']})
                for physical in r['included']:
                    if physical in r['blocked']:continue
                    if not self.valid_target(r,physical):r['blocked'][physical]='execute_mapping';continue
                    events=[e for e in r['events'] if e['physical_id']==physical and instant(e['utc'])<=now]
                    if not events:continue
                    event=events[-1];key=event['id'];wanted=event['action']['state'];observed=reading(self.hass,r['mapping'][physical])
                    for old in events[:-1]:
                        if old['id'] not in r['ledger']:r['ledger'][old['id']]={'status':'superseded','event_id':old['id'],'physical_id':physical,'at':now.isoformat()}
                    # Confirm dispatch from fresh state; acknowledgment is not confirmation.
                    for attempt_key,attempt in list(r['ledger'].items()):
                        if attempt.get('physical_id')!=physical or attempt['status'] not in ('dispatching','acknowledged','uncertain') or (rid,attempt_key) in self.inflight:continue
                        if observed['state']==attempt['wanted']:
                            current=self.hass.states.get(r['mapping'][physical]['entity_id'])
                            attempt['status']='confirmed' if attempt['status']=='acknowledged' and current and current.context.id==attempt.get('context_id') else 'satisfied_uncertain';attempt['confirmed_at']=now.isoformat()
                            if attempt['status']=='confirmed':r['changed'][physical]={**r['changed'].get(physical,{}),'state':attempt['wanted'],'at':now.isoformat()}
                        elif (now-instant(attempt['at'])).total_seconds()>=30:
                            attempt['status']='uncertain';r['blocked'][physical]='execute_unconfirmed'
                    if physical in r['blocked']:continue
                    final_grace=instant(event['utc'])==end and now<=end+timedelta(seconds=120)
                    if now>end and not final_grace:continue
                    previous=r['ledger'].get(key)
                    if not previous:
                        if (now-instant(event['utc'])).total_seconds()>120:r['blocked'][physical]='execute_missed'
                        else:pending.append((rid,physical,event,key,now,False))
                        continue
                    if previous['status'] not in TERMINAL or now>end:continue
                    if observed['state']=='unknown':r['blocked'][physical]='execute_unavailable';continue
                    if observed['state']==wanted:continue
                    state=self.hass.states.get(r['mapping'][physical]['entity_id'])
                    if state and state.context.user_id:r['blocked'][physical]='execute_external_change';continue
                    changed=r['changed'].get(physical);options=r['recovery']
                    if not options['enabled'] or not changed:r['blocked'][physical]='execute_external_change';continue
                    if changed.get('corrections',0)>=2:r['blocked'][physical]='execute_recovery_budget';continue
                    last=instant(changed.get('last_correction',changed['at']))
                    if (now-last).total_seconds()>=options['interval_minutes']*60:
                        pending.append((rid,physical,event,key+'-recovery-'+str(changed.get('corrections',0)+1),now,True))
                final_pending=any(instant(e['utc'])==end and e['id'] not in r['ledger'] and e['physical_id'] not in r['blocked'] for e in r['events'])
                unconfirmed=any(a['status'] in ('dispatching','acknowledged') for a in r['ledger'].values())
                if now>end and not any(k[0]==rid for k in self.inflight) and not unconfirmed and (not final_pending or now>end+timedelta(seconds=120)):r['status']='completed';r['finished_at']=now.isoformat()
                elif set(r['blocked'])==set(r['included']):r['status']='blocked'
            if data!=self.data:
                for r in data['runs'].values():
                    if r['status'] in ACTIVE:r['last_tick']=now.isoformat()
                await self.commit(data)
        semaphore=asyncio.Semaphore(4)
        async def one(args):
            async with semaphore:
                # Recheck the real deadline after queued service calls; fixtures supply a frozen clock.
                await self.dispatch(*args)
        await asyncio.gather(*(one(args) for args in pending))

    def for_observation(self,observer_id):
        return next((self.public(r) for r in self.data['runs'].values() if r['observer_id']==observer_id),None)
