"""Persistent sampled observation. Intentionally has no actuator/service adapter."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import tempfile
from uuid import uuid4

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_interval
from .engine.schedule import compile_schedule, digest
from .household import internal_id
from .comfort import collect as comfort_collect
from .thermal import initialize as thermal_initialize, collect as thermal_collect, weather_sources
from .ownership import instant, forecast_ha, ownership_report

SCHEMA = 1
ACTIVE = {'scheduled', 'observing'}
DEFAULT_POLICY = {'enabled': True, 'boot_delay_minutes': 5, 'interval_minutes': 30}


def policy(value):
    if not isinstance(value, dict) or set(value) != set(DEFAULT_POLICY) or type(value['enabled']) is not bool:
        raise ValueError('observe_policy')
    for key, low, high in [('boot_delay_minutes', 1, 60), ('interval_minutes', 5, 1440)]:
        if type(value[key]) is not int or not low <= value[key] <= high: raise ValueError('observe_policy')
    return deepcopy(value)


def atomic_save(path, data):
    """Explicit error propagation; HA Store currently logs some write failures."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps({'checksum':digest(data),'data':data}, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
    if len(raw) > 50 * 1024 * 1024: raise ValueError('observe_limit')
    fd, name = tempfile.mkstemp(prefix=path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
        parent = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(parent)
        finally: os.close(parent)
    finally:
        if os.path.exists(name): os.unlink(name)


def read_store(path):
    if not path.exists(): return {'schema_version':SCHEMA, 'runs':{}}
    if path.stat().st_size > 50 * 1024 * 1024: raise ValueError('observe_store')
    envelope = json.loads(path.read_text())
    data = envelope['data']
    if envelope['checksum'] != digest(data): raise ValueError('observe_store')
    if not isinstance(data, dict) or data.get('schema_version') != SCHEMA or not isinstance(data.get('runs'), dict) or len(data['runs']) > 20:
        raise ValueError('observe_store')
    for rid, run in data['runs'].items():
        if run['id'] != rid or run['mode'] != 'observe' or digest(run['bundle']) != run['snapshot_hash']:
            raise ValueError('observe_store')
        if run['status'] not in ACTIVE | {'completed','stopped'}: raise ValueError('observe_store')
        if not isinstance(run['mapping'],dict) or len(run['mapping']) > (200 if run.get('kind')=='climate_study' else 100): raise ValueError('observe_store')
        from .reports import validate_review
        if run.get('review') is not None: validate_review(run['review'])
        if type(run.get('review_revision',0)) is not int or run.get('review_revision',0)<0: raise ValueError('observe_store')
        if not isinstance(run.get('review_history',[]),list) or len(run.get('review_history',[]))>10: raise ValueError('observe_store')
        for prior in run.get('review_history',[]): validate_review(prior['value'])
        policy(run['policy']); instant(run['start']); instant(run['end']); instant(run['last_sample'])
        if run.get('kind')=='climate_study':
            from .study import valid_saved
            if not valid_saved(run): raise ValueError('observe_store')
        elif compile_schedule(**run['bundle']) != run['preview']: raise ValueError('observe_store')
    return data


def resolve_mapping(hass, bundle):
    registry = er.async_get(hass)
    known = {internal_id('load_', e.id): e for e in registry.entities.values() if e.disabled_by is None}
    mapping, unresolved = {}, []
    for physical in sorted({load['physical_id'] for load in bundle['config']['loads'].values()}):
        entity = known.get(physical)
        if not entity or entity.domain not in ('light','switch','climate','fan'):
            unresolved.append(physical); continue
        mapping[physical] = {'entity_id':entity.entity_id, 'registry_id':entity.id, 'platform':entity.platform}
    return mapping, unresolved


def reading(hass, target):
    entry = er.async_get(hass).async_get(target['entity_id'])
    if entry is None or entry.id != target['registry_id'] or entry.disabled_by is not None:
        return {'state':'unknown', 'reason':'mapping_changed'}
    state = hass.states.get(target['entity_id'])
    if state is None or state.state in ('unknown','unavailable') or state.attributes.get('restored') is True:
        return {'state':'unknown', 'reason':'unavailable'}
    power = state.state
    if state.domain == 'climate':
        power = 'off' if state.state == 'off' else 'on' if state.state in ('heat','cool','heat_cool','auto','dry','fan_only') else 'unknown'
    if power not in ('on','off'): power = 'unknown'
    fields = ('temperature','target_temp_low','target_temp_high','fan_mode','preset_mode','swing_mode','swing_horizontal_mode')
    return {'state':power, 'mode':state.state if state.domain == 'climate' else None,
            'settings':{k:state.attributes[k] for k in fields if isinstance(state.attributes.get(k),str) or (type(state.attributes.get(k)) in (int,float) and math.isfinite(state.attributes[k]))},
            'unit':state.attributes.get('temperature_unit')}


def expected(events, physical, at):
    found = None
    for event in events:
        if event['physical_id'] == physical and event['intent'] != 'track_only' and instant(event['utc']) <= at:
            found = event['action']
    return found


def classify(action, observed):
    if action is None: return 'unplanned'
    if observed.get('state') not in ('on','off'): return 'unknown'
    desired = action.get('state', 'off' if action.get('mode') == 'off' else 'on')
    return 'matched' if desired == observed['state'] else 'mismatched'



def settings_classify(action, observed, baseline):
    if action is None or action.get('type') not in ('hvac','hvac_power'):
        return 'unplanned'
    if action.get('state') == 'off' or action.get('mode') == 'off': return 'unplanned'
    if observed.get('state') != 'on': return 'unknown'
    if action['type'] == 'hvac_power':
        if not baseline: return 'unknown'
        keys = baseline.get('settings', {})
        if any(k not in observed.get('settings', {}) for k in keys): return 'unknown'
        return 'matched' if observed.get('mode') == baseline.get('mode') and observed.get('settings') == keys else 'mismatched'
    wanted = {'temperature':action['temperature'],'fan_mode':action['fan_mode']}
    if any(k not in observed.get('settings', {}) for k in wanted) or not observed.get('unit'): return 'unknown'
    unit = str(observed['unit']).replace('°','')
    return 'matched' if observed['mode']==action['mode'] and unit==action['unit'] and all(observed['settings'][k]==v for k,v in wanted.items()) else 'mismatched'


def accumulate(run, left, right, gap):
    if right <= left: return
    for physical in run['mapping']:
        cuts = sorted({left, right} | {instant(e['utc']) for e in run['preview']['events'] if e['physical_id']==physical and left < instant(e['utc']) < right})
        previous = run['last_states'].get(physical, {'state':'unknown'})
        stats = run['summary'][physical]
        for a, b in zip(cuts,cuts[1:]):
            action = expected(run['preview']['events'],physical,a)
            category = 'unknown' if gap else classify(action,previous)
            stats[category+'_seconds'] += (b-a).total_seconds()
            if run['mapping'][physical]['entity_id'].startswith('climate.'):
                setting = 'unknown' if gap else settings_classify(action,previous,run['baselines'].get(physical))
                stats['settings_'+setting+'_seconds'] += (b-a).total_seconds()


class Observer:
    def __init__(self, hass):
        self.hass = hass
        self.path = Path(hass.config.path('.storage', 'shabbat_flow.observe'))
        self.data = {'schema_version':SCHEMA,'runs':{}}
        self.lock = asyncio.Lock(); self.error = None; self.cancel = None
        self.boot = datetime.now(timezone.utc); self.resumed = set(); self.closed = False

    async def load(self):
        try:
            self.data = await self.hass.async_add_executor_job(read_store,self.path)
            self.resumed = {r['id'] for r in self.data['runs'].values() if r['status'] in ACTIVE}
        except Exception:
            self.error = 'observe_store'
        self.cancel = async_track_time_interval(self.hass,self.tick,timedelta(seconds=60))

    def close(self):
        self.closed = True
        if self.cancel: self.cancel(); self.cancel = None

    async def commit(self, candidate):
        try: await self.hass.async_add_executor_job(atomic_save,self.path,candidate)
        except Exception:
            self.error = 'observe_store'; raise ValueError('observe_store') from None
        previous=self.data
        self.data = candidate
        pdf=self.hass.data.get("shabbat_flow",{}).get("pdf")
        if pdf:
            pdf.schedule_cleanup()
        notifications=self.hass.data.get('shabbat_flow',{}).get('notifications')
        if notifications:
            try: await notifications.record(previous,candidate)
            except Exception: notifications.error='store'

    async def start(self, bundle, options, request_id, actor, now=None, weather_entity_id=None):
        now = now or datetime.now(timezone.utc)
        if set(bundle) != {'config','plan'}: raise ValueError('invalid_request')
        options = policy(options)
        if not isinstance(request_id,str) or not 8 <= len(request_id) <= 100: raise ValueError('invalid_request')
        preview = await self.hass.async_add_executor_job(compile_schedule,bundle['config'],bundle['plan'])
        if not preview['complete']: raise ValueError('observe_incomplete')
        start, end = (instant(bundle['plan']['snapshot'][k]) for k in ('preparation_start','end'))
        if not 0 < (end-start).total_seconds() <= 96*3600 or len(preview['events'])>5000 or now >= end: raise ValueError('observe_period')
        mapping, unresolved = resolve_mapping(self.hass,bundle)
        if not mapping or len(mapping)>100: raise ValueError('observe_mapping')
        overlay = forecast_ha(self.hass,bundle['plan']['snapshot'])
        thermal = thermal_initialize(self.hass,now,weather_entity_id)
        snapshot_hash = digest(bundle)
        async with self.lock:
            if self.error or self.closed: raise ValueError('observe_store')
            for run in self.data['runs'].values():
                if run['request_id'] == request_id:
                    if run['snapshot_hash'] != snapshot_hash or run['policy'] != options or run.get('weather_selection') != weather_entity_id: raise ValueError('observe_conflict')
                    return deepcopy(run)
                if run.get('kind')!='climate_study' and run['status'] in ACTIVE and start < instant(run['end']) and end > instant(run['start']) and set(mapping)&set(run['mapping']):
                    raise ValueError('observe_conflict')
            candidate = deepcopy(self.data)
            candidate['runs'] = {k:r for k,r in candidate['runs'].items() if r['status'] in ACTIVE or (now-instant(r.get('finished_at',r['end']))).days < 90}
            if len(candidate['runs']) >= 20: raise ValueError('observe_limit')
            rid = uuid4().hex
            run = {'id':rid,'mode':'observe','status':'scheduled' if now<start else 'observing','bundle':deepcopy(bundle),
                   'snapshot_hash':snapshot_hash,'preview':preview,'mapping':mapping,'unmapped':unresolved,'policy':options,
                   'thermal':thermal,'weather_selection':weather_entity_id,
                   'request_id':request_id,'actor':actor,'created_at':now.isoformat(),'start':start.isoformat(),'end':end.isoformat(),
                   'last_sample':start.isoformat(),'last_states':{},'baselines':{},'changes':[],'truncated':False,'gaps':[],
                   'overlay':overlay,'ownership':ownership_report(preview['events'],mapping,overlay),
                   'summary':{p:{k+'_seconds':0 for k in ('matched','mismatched','unknown','unplanned','settings_matched','settings_mismatched','settings_unknown','settings_unplanned')} for p in mapping},
                   'checks':[],'event_checks':{},'last_check':None,'source_changed':False}
            candidate['runs'][rid] = run
            await self.commit(candidate)
        await self.tick(now)
        if self.error: raise ValueError(self.error)
        return deepcopy(self.data['runs'][rid])

    async def start_study(self, selection, request_id, actor, now=None):
        from .study import snapshot, validate
        now=now or datetime.now(timezone.utc)
        selection=validate(selection)
        if not isinstance(request_id,str) or not 8<=len(request_id)<=100: raise ValueError('invalid_request')
        async with self.lock:
            if self.error or self.closed: raise ValueError('observe_store')
            for run in self.data['runs'].values():
                if run['request_id']==request_id:
                    if run.get('kind')!='climate_study' or run['bundle']['study']!=selection: raise ValueError('observe_conflict')
                    return deepcopy(run)
                if run.get('kind')=='climate_study' and run['status'] in ACTIVE: raise ValueError('observe_conflict')
            bundle,thermal,mapping=snapshot(self.hass,selection,now)
            candidate=deepcopy(self.data)
            candidate['runs']={k:r for k,r in candidate['runs'].items() if r['status'] in ACTIVE or (now-instant(r.get('finished_at',r['end']))).days<90}
            if len(candidate['runs'])>=20: raise ValueError('observe_limit')
            rid=uuid4().hex
            run={'id':rid,'kind':'climate_study','mode':'observe','status':'observing','bundle':bundle,'snapshot_hash':digest(bundle),
                 'preview':{'complete':True,'events':[]},'mapping':mapping,'unmapped':[],
                 'policy':{**DEFAULT_POLICY,'enabled':False},'thermal':thermal,'request_id':request_id,'actor':actor,
                 'created_at':now.isoformat(),'start':now.isoformat(),'end':bundle['plan']['snapshot']['end'],
                 'last_sample':now.isoformat(),'last_states':{},'baselines':{},'changes':[],'truncated':False,'gaps':[],
                 'summary':{p:{k+'_seconds':0 for k in ('matched','mismatched','unknown','unplanned','settings_matched','settings_mismatched','settings_unknown','settings_unplanned')} for p in mapping},
                 'checks':[],'event_checks':{},'last_check':None,'source_changed':False}
            candidate['runs'][rid]=run
            await self.commit(candidate)
        await self.tick(now)
        if self.error: raise ValueError(self.error)
        return deepcopy(self.data['runs'][rid])

    async def tick(self, now):
        async with self.lock:
            if self.closed or self.error: return
            candidate = deepcopy(self.data); changed = False; resumed_done = set()
            for rid, run in list(candidate['runs'].items()):
                if run['status'] not in ACTIVE and (now-instant(run.get('finished_at',run['end']))).days >= 90:
                    del candidate['runs'][rid]; changed=True; continue
                if run['status'] not in ACTIVE or now < instant(run['start']): continue
                left, right = instant(run['last_sample']), min(now,instant(run['end']))
                if right <= left and run['last_states']: continue
                changed = True
                thermal_collect(self.hass,run,now,rid in self.resumed)
                gap = rid in self.resumed or not run['last_states'] or (now-left).total_seconds()>90
                comfort_collect(self.hass,run,now,gap)
                accumulate(run,left,right,gap)
                if gap and right>left and len(run['gaps'])<1000: run['gaps'].append({'start':left.isoformat(),'end':right.isoformat(),'reason':'restart_or_collection_gap'})
                states = {p:reading(self.hass,t) for p,t in run['mapping'].items()}
                for p,value in states.items():
                    if p not in run['baselines']:
                        run['baselines'][p] = deepcopy(value) if value.get('mode') not in (None,'off') and value['state']=='on' else None
                    if value != run['last_states'].get(p):
                        if len(run['changes']) < 20000: run['changes'].append({'physical_id':p,'observed_at':now.isoformat(),**value})
                        else: run['truncated'] = True
                for event in run['preview']['events']:
                    at = instant(event['utc'])
                    if at > right or event['id'] in run['event_checks']: continue
                    observed = states.get(event['physical_id'], {'state':'unknown'})
                    if event['intent'] == 'track_only': outcome = 'track_only'
                    elif gap and at < now: outcome = 'missed_observation'
                    elif expected(run['preview']['events'],event['physical_id'],right) != event['action']: outcome = 'superseded_before_sample'
                    else: outcome = classify(event['action'],observed)
                    run['event_checks'][event['id']] = {'due':event['utc'],'sampled_at':now.isoformat(),
                        'lateness_seconds':max(0,(now-at).total_seconds()),'outcome':outcome,'actuated':False}
                run['last_states']=states; run['last_sample']=right.isoformat()
                run['status']='completed' if now>=instant(run['end']) else 'observing'
                if run['status']=='completed': run['finished_at']=now.isoformat()
                cfg=run['policy']; due=self.boot+timedelta(minutes=cfg['boot_delay_minutes'])
                if run['last_check']: due=max(due,instant(run['last_check'])+timedelta(minutes=cfg['interval_minutes']))
                if cfg['enabled'] and now>=due:
                    current=forecast_ha(self.hass,run['bundle']['plan']['snapshot'])
                    run['source_changed'] = current['fingerprints'] != run['overlay']['fingerprints']
                    check={'at':now.isoformat(),'report_only':True,'states':{p:classify(expected(run['preview']['events'],p,right),v) for p,v in states.items()}}
                    if len(run['checks'])<1200: run['checks'].append(check)
                    run['last_check']=now.isoformat()
                resumed_done.add(rid)
            if changed:
                try: await self.commit(candidate)
                except ValueError: return
                self.resumed -= resumed_done

    async def stop(self, rid, now=None):
        now=now or datetime.now(timezone.utc)
        await self.tick(now)
        async with self.lock:
            if self.error: raise ValueError('observe_store')
            candidate=deepcopy(self.data)
            if rid not in candidate['runs']: raise ValueError('observe_missing')
            if candidate['runs'][rid]['status'] in ACTIVE:
                candidate['runs'][rid].update(status='stopped',finished_at=now.isoformat())
                await self.commit(candidate)
        return self.export(rid)

    async def configure(self, rid, value):
        value = policy(value)
        async with self.lock:
            if self.error or self.closed: raise ValueError('observe_store')
            candidate = deepcopy(self.data)
            if rid not in candidate['runs']: raise ValueError('observe_missing')
            run = candidate['runs'][rid]
            if run.get('kind')=='climate_study' or run['status'] not in ACTIVE: raise ValueError('observe_conflict')
            history = run.setdefault('policy_history', [])
            if len(history) >= 100: raise ValueError('observe_limit')
            history.append({'at':datetime.now(timezone.utc).isoformat(),'previous':run['policy']})
            run['policy'] = value
            await self.commit(candidate)
        return self.export(rid)

    async def review(self, rid, revision, value):
        from .reports import validate_review, review_state
        if type(revision) is not int or revision < 0: raise ValueError('observe_review_invalid')
        if value is not None: value=validate_review(value)
        async with self.lock:
            if self.error or self.closed: raise ValueError('observe_store')
            candidate=deepcopy(self.data)
            if rid not in candidate['runs']: raise ValueError('observe_missing')
            run=candidate['runs'][rid]
            if run.get('review_revision',0)!=revision: raise ValueError('observe_review_conflict')
            history=run.setdefault('review_history',[])
            if value is None: history.clear()
            elif run.get('review') is not None:
                history.append({'revision':run.get('review_revision',0),'updated_at':run.get('review_updated_at'),'value':run['review']})
                del history[:-10]
            run.update(review=value,review_revision=revision+1,review_updated_at=datetime.now(timezone.utc).isoformat())
            await self.commit(candidate)
            return review_state(run)

    def reports(self):
        from .reports import performance
        return {'mode':'observe','error':self.error,'retention_days':90,'max_runs':20,'runs':[
            {k:r[k] for k in ('id','status','start','end','snapshot_hash')} |
            {'kind':r.get('kind','plan'),'timezone':r['bundle']['plan']['snapshot']['timezone'],
             'reviewed':r.get('review') is not None,'review_revision':r.get('review_revision',0),
             'performance':performance(r)['totals']}
            for r in sorted(self.data['runs'].values(),key=lambda r:r['start'],reverse=True)]}

    def listing(self):
        from .study import sources
        return {'execution':self.hass.data['shabbat_flow']['executor'].listing() if self.hass.data.get('shabbat_flow',{}).get('executor') else None,'study_sources':sources(self.hass),'mode':'observe','error':self.error,'weather_sources':weather_sources(self.hass),'runs':[{k:r[k] for k in ('id','status','created_at','start','end','snapshot_hash')} | {'kind':r.get('kind','plan'),'timezone':r['bundle']['plan']['snapshot']['timezone']} for r in self.data['runs'].values()]}

    def export(self,rid):
        if rid not in self.data['runs']: raise ValueError('observe_missing')
        from .reports import performance, review_state
        run=deepcopy(self.data['runs'][rid]); run.pop('actor',None); run.pop('request_id',None)
        executor=self.hass.data.get('shabbat_flow',{}).get('executor')
        execution=executor.for_observation(rid) if executor else None
        sent=sum(a.get('status') not in ('already_correct','superseded','not_dispatched') and 'context_id' in a for a in execution['ledger'].values()) if execution else 0
        return {'execution':execution,'schema_version':1,'collection_error':self.error,'sample_seconds':60,'mode':'control_and_observe' if execution else 'observe','device_commands_sent':None if execution else 0,'dispatch_attempts':sent,
                'limitations':['sampled_not_exact_history','no_occupancy_inference','preserve_settings_baseline_may_be_unknown','unmanaged_forecast_not_guaranteed','thermal_reports_not_verified_room_temperatures','weather_report_not_local_outdoor_sensor','state_update_time_not_measurement_time','no_automatic_thermostat_calibration'],
                'performance':performance(run),'review':review_state(run),'run':run}
