"""Finite, explicit rehearsals of an unchanged plan; no auto-resume or auto-restore."""
import asyncio
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
from uuid import uuid4
from .execution import Executor, ACTIVE, DEFAULT_RECOVERY, now_utc
from .ownership import instant
from .engine.schedule import digest
from .engine.rehearsal import catalog, project
from .reminders import status as calendar_status


def read_store(path):
    if not path.exists():return {'schema_version':1,'runs':{}}
    if path.stat().st_size>50*1024*1024:raise ValueError('execute_store')
    envelope=json.loads(path.read_text());data=envelope['data']
    if digest(data)!=envelope['checksum'] or data['schema_version']!=1 or len(data['runs'])>20:raise ValueError('execute_store')
    for rid,r in data['runs'].items():
        if rid!=r['id'] or digest(r['bundle'])!=r['snapshot_hash'] or r['kind'] not in ('rehearsal','restore'):raise ValueError('execute_store')
        if r['status'] not in ACTIVE|{'completed','disarmed','interrupted'}:raise ValueError('execute_store')
        if not isinstance(r['ledger'],dict) or len(r['ledger'])>100:raise ValueError('execute_store')
    return data


class Rehearsal(Executor):
    def __init__(self,hass):
        super().__init__(hass)
        self.path=Path(hass.config.path('.storage','shabbat_flow.rehearsal'));self.tasks=set();self.reviews={};self.slots=asyncio.Semaphore(4)

    async def load(self):
        try:
            self.data=await self.hass.async_add_executor_job(read_store,self.path)
            data=deepcopy(self.data)
            for r in data['runs'].values():
                if r['status'] in ACTIVE:r['status']='interrupted'
            if data!=self.data:await self.commit(data)
        except Exception:self.error='execute_store'

    async def close(self):
        self.closed=True
        if self.tasks:await asyncio.gather(*self.tasks,return_exceptions=True)

    def overlaps(self,physical,start,end):
        return any((r['status'] in ACTIVE or any(k[0]==r['id'] for k in self.inflight)) and set(physical)&set(r['included']) and start<=instant(r['end']) and end>=instant(r['start']) for r in self.data['runs'].values())

    def public(self,r):
        return {**super().public(r),**{k:deepcopy(r[k]) for k in ('kind','selection','before','feedback','restore_of') if k in r}}

    def export(self,rid):
        if rid not in self.data['runs']:raise ValueError('execute_missing')
        r=self.data['runs'][rid]
        return {**self.public(r),'bundle':deepcopy(r['bundle']),'limitations':['rehearsal_not_weekend_activation','point_observations_not_continuous_study','unselected_devices_not_failures']}

    def dispatch_guard(self,r,physical):
        if not calendar_status(self.hass)['issur_off']:return 'rehearsal_observance'
        state=self.hass.states.get(r['mapping'][physical]['entity_id'])
        before=r['before'][physical]
        if not state or state.state!=before['state'] or state.context.id!=before['context_id']:return 'rehearsal_intervened'
        executor=self.hass.data['shabbat_flow']['executor']
        if any((old['status'] in ACTIVE or any(k[0]==old['id'] for k in executor.inflight)) and physical in old['included'] and instant(old['start'])<=now_utc()+timedelta(minutes=2) and instant(old['end'])>=now_utc() for old in executor.data['runs'].values()):return 'execute_overlap'
        return None

    async def review_test(self,bundle,selection,restore_of=None,issue=True):
        if self.error or self.closed:raise ValueError('execute_store')
        if not isinstance(selection,dict) or set(selection)!={'at','mode','areas'}:raise ValueError('rehearsal_invalid')
        projection=await self.hass.async_add_executor_job(project,bundle,selection['at'],selection['mode'],selection['areas'])
        base=await self.hass.data['shabbat_flow']['executor'].review(bundle)
        by_id={l['physical_id']:l for l in base['loads']}
        rows=[];original=self.data['runs'].get(restore_of) if restore_of else None
        if restore_of and (not original or original['status'] in ACTIVE or original['kind']!='rehearsal'):raise ValueError('rehearsal_restore')
        if original and (digest(bundle)!=original['snapshot_hash'] or selection!=original['selection']):raise ValueError('execute_stale')
        for row in projection['rows']:
            physical=row['physical_id'];load=by_id[physical];reasons=list(load['reasons'])
            if row['reason']:reasons.append(row['reason'])
            event=row['event'];state=self.hass.states.get(load['entity_id']) if load['entity_id'] else None
            before={'state':state.state if state else 'unknown','context_id':state.context.id if state else None}
            if original:
                attempt=next((a for a in original['ledger'].values() if a.get('physical_id')==physical and a['status']=='confirmed'),None)
                if physical not in original['included'] or not attempt or not state or state.context.id!=attempt.get('context_id') or state.state!=attempt['wanted'] or base['mapping'].get(physical)!=original['mapping'].get(physical) or base['source_fingerprint']!=original['source_fingerprint']:
                    reasons.append('rehearsal_intervened')
                elif original['before'][physical]['state'] in ('on','off'):
                    event={**event,'action':{'type':'state','state':original['before'][physical]['state']}}
                else:reasons.append('rehearsal_unknown')
            rows.append({**row,'event':event,'entity_id':load['entity_id'],'before':before,'reasons':sorted(set(reasons)),'writers':load['writers']})
        result={'snapshot_hash':digest(bundle),'selection':deepcopy(selection),'timezone':projection['timezone'],'related_areas':projection['related_areas'],'areas':projection['areas'],'rows':rows,'mapping':base['mapping'],'source_fingerprint':base['source_fingerprint'],'unknown_sources':base['unknown_sources'],'can_apply':calendar_status(self.hass)['issur_off'],'restore_of':restore_of}
        result['review_digest']=digest(result)
        # Expiry is explicit but is not part of the digest (repeat read must remain comparable).
        result['reviewed_at']=now_utc().isoformat()
        if issue:
            self.reviews={k:v for k,v in self.reviews.items() if (now_utc()-instant(v)).total_seconds()<120}
            if len(self.reviews)>=20:self.reviews.pop(next(iter(self.reviews)))
            self.reviews[result['review_digest']]=result['reviewed_at']
        return result

    async def restore_review(self,rid):
        if rid not in self.data['runs']:raise ValueError('execute_missing')
        r=self.data['runs'][rid]
        return await self.review_test(r['bundle'],r['selection'],rid)

    async def apply(self,payload,actor):
        required={'bundle','selection','review_digest','reviewed_at','included','qualifications','attestations','request_id','confirm','restore_of'}
        if not isinstance(payload,dict) or set(payload)!=required or payload['confirm'] is not True:raise ValueError('rehearsal_invalid')
        included=payload['included'];request=payload['request_id'];notes=payload['qualifications'];attest=payload['attestations']
        if not isinstance(included,list) or not 0<len(included)<=100 or any(not isinstance(p,str) for p in included) or len(set(included))!=len(included):raise ValueError('rehearsal_invalid')
        if not isinstance(request,str) or not 8<=len(request)<=100:raise ValueError('rehearsal_invalid')
        if not isinstance(notes,dict) or set(notes)!=set(included) or any(not isinstance(n,str) or not 10<=len(n)<=1000 for n in notes.values()):raise ValueError('execute_qualification')
        if not isinstance(attest,dict) or len(attest)>200 or any(not isinstance(n,str) or not 10<=len(n)<=1000 for n in attest.values()):raise ValueError('execute_attestation')
        identity=digest({k:v for k,v in payload.items() if k!='reviewed_at'})
        executor=self.hass.data['shabbat_flow']['executor']
        async with executor.lock, self.lock:
            if self.error or self.closed:raise ValueError('execute_store')
            for old in self.data['runs'].values():
                if old['request_id']==request:
                    if old['identity']!=identity:raise ValueError('execute_stale')
                    return self.public(old)
            now=now_utc();age=(now-instant(payload['reviewed_at'])).total_seconds()
            if not 0<=age<=120 or self.reviews.get(payload['review_digest'])!=payload['reviewed_at']:raise ValueError('execute_stale')
            report=await self.review_test(payload['bundle'],payload['selection'],payload['restore_of'],issue=False)
            if report['review_digest']!=payload['review_digest']:raise ValueError('execute_stale')
            if not report['can_apply']:raise ValueError('rehearsal_observance')
            by_id={r['physical_id']:r for r in report['rows']}
            if any(p not in by_id or by_id[p]['reasons'] for p in included):raise ValueError('execute_blocked')
            expected={s['id']+'|'+p for s in report['unknown_sources'] for p in included}
            if set(attest)!=expected:raise ValueError('execute_attestation')
            end=now+timedelta(minutes=2)
            if self.overlaps(included,now,end) or any((r['status'] in ACTIVE or any(k[0]==r.get('id') for k in executor.inflight)) and set(included)&set(r['included']) and instant(r['start'])<=end and instant(r['end'])>=now for r in executor.data['runs'].values()):raise ValueError('execute_overlap')
            rid=uuid4().hex;data=deepcopy(self.data)
            data['runs']={k:r for k,r in data['runs'].items() if r['status'] in ACTIVE or (now-instant(r['end'])).days<90}
            if len(data['runs'])>=20:
                removable=[r for r in data['runs'].values() if r['status'] not in ACTIVE and r['id']!=payload['restore_of']]
                if not removable:raise ValueError('execute_limit')
                oldest=min(removable,key=lambda r:instant(r['start']));del data['runs'][oldest['id']]
            events=[{**deepcopy(by_id[p]['event']),'source_utc':by_id[p]['event']['utc'],'utc':now.isoformat()} for p in included]
            r={'id':rid,'kind':'restore' if payload['restore_of'] else 'rehearsal','restore_of':payload['restore_of'],'status':'running','revision':1,'request_id':request,'identity':identity,'actor':actor,'bundle':deepcopy(payload['bundle']),'snapshot_hash':report['snapshot_hash'],'selection':deepcopy(payload['selection']),'included':sorted(included),'excluded':sorted(set(by_id)-set(included)),'mapping':{p:report['mapping'][p] for p in included},'source_fingerprint':report['source_fingerprint'],'before':{p:by_id[p]['before'] for p in included},'events':events,'start':now.isoformat(),'end':end.isoformat(),'ledger':{},'blocked':{},'changed':{},'recovery':deepcopy(DEFAULT_RECOVERY),'observer_id':None,'feedback':'','qualifications':deepcopy(notes),'attestations':deepcopy(attest)}
            data['runs'][rid]=r;await self.commit(data)
            task=self.hass.async_create_background_task(self.run(rid),'shabbat_flow_rehearsal')
            self.tasks.add(task);task.add_done_callback(self.tasks.discard)
            return self.public(r)

    async def run(self,rid):
        async def one(event):
            async with self.slots:
                p=event['physical_id'];key=event['id']
                await self.dispatch(rid,p,event,key,now_utc())
                for _ in range(31):
                    async with self.lock:
                        if self.error:return
                        r=self.data['runs'][rid];record=r['ledger'].get(key)
                        if not record or record['status'] in ('already_correct','not_dispatched'):return
                        if self.closed or r['status'] not in ACTIVE:return
                        state=self.hass.states.get(r['mapping'][p]['entity_id'])
                        if state and state.state==record['wanted']:
                            data=deepcopy(self.data);attempt=data['runs'][rid]['ledger'][key]
                            attempt['status']='confirmed' if record['status']=='acknowledged' and state.context.id==record.get('context_id') else 'satisfied_uncertain'
                            attempt['confirmed_at']=now_utc().isoformat();await self.commit(data);return
                        if (now_utc()-instant(record['at'])).total_seconds()>=30:break
                    await asyncio.sleep(1)
                async with self.lock:
                    if self.error:return
                    data=deepcopy(self.data);data['runs'][rid]['blocked'][p]='execute_unconfirmed';await self.commit(data)
        try:
            await asyncio.gather(*(one(e) for e in self.data['runs'][rid]['events']))
            async with self.lock:
                if self.error:return
                data=deepcopy(self.data);r=data['runs'][rid]
                if r['status'] in ACTIVE:r['status']='interrupted' if self.closed else 'completed'
                r['finished_at']=now_utc().isoformat();await self.commit(data)
        except Exception:self.error='execute_store'

    async def feedback(self,rid,value):
        if not isinstance(value,str) or len(value)>2000:raise ValueError('rehearsal_invalid')
        async with self.lock:
            if self.error or self.closed:raise ValueError('execute_store')
            if rid not in self.data['runs']:raise ValueError('execute_missing')
            data=deepcopy(self.data);data['runs'][rid]['feedback']=value;await self.commit(data)
            return self.public(data['runs'][rid])
