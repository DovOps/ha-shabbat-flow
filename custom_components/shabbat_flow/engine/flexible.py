"""Additive activity planning and deterministic comfort shadow evaluation. No actuators."""
from copy import deepcopy
from datetime import timedelta
from math import isfinite
from .compiler import require, keys, identifier, parse_instant, references
from .planning import validate_calendar, bounded_list, choice

CATEGORIES = ('recreation','playtime','service','fan','appliance')
FEEDBACK = ('intentional','exceptional','configuration','comfort','missing','uncertain')


def numeric(v, lo, hi):
    require(type(v) in (int,float) and isfinite(v) and lo <= v <= hi)


def comfort(value):
    keys(value, {'mode','target','tolerance','hysteresis','minimum_on','minimum_off','sensor','unit','signals'})
    choice(value['mode'], ('cool','heat')); choice(value['unit'], ('C','F'))
    numeric(value['target'],-50,150); numeric(value['tolerance'],0,20)
    numeric(value['hysteresis'],0,20); require(value['hysteresis'] <= value['tolerance'])
    for k in ('minimum_on','minimum_off'): numeric(value[k],1,120)
    require(type(value['sensor']) is str and len(value['sensor'])<=150)
    require(not value['sensor'] or value['sensor'].startswith(('sensor.','climate.')))
    bounded_list(value['signals'],30)
    require(all(type(s) is str and s.startswith(('light.','switch.')) and len(s)<=150 for s in value['signals']))


def expand(config,plan):
    """Transform opt-in extensions into the unchanged generic demand compiler."""
    from .schedule import digest, validate_configuration
    validate_configuration(config)
    c,p=deepcopy(config),deepcopy(plan); f=p.pop('flex'); cal=validate_calendar(p['snapshot'])
    keys(f,{'version','windows','meals','overrides','feedback'}); require(f['version']==1 and type(f['version']) is int)
    for field in ('windows','meals','overrides','feedback'): bounded_list(f[field],100)
    conditions=[]; fixed_hvac=[]; notes=[]; seen=set()
    for entry in f['feedback']:
        keys(entry,{'category','room','note'});choice(entry['category'],FEEDBACK)
        require(entry['room'] in c['rooms'] or entry['room']=='')
        require(type(entry['note']) is str and len(entry['note'])<=2000)
    for entry in f['meals']:
        keys(entry,{'id','preset','duration','cleanup'});choice(entry['preset'],('early','family','hosting','custom'))
        numeric(entry['duration'],15,600);numeric(entry['cleanup'],0,240)
        require(entry['id'] not in seen,'invalid_mapping');seen.add(entry['id'])
        m=next((m for m in p['meals'] if m['id']==entry['id']),None);require(m is not None,'invalid_mapping')
        m['end']=(parse_instant(m['start'],cal['zone'])+timedelta(minutes=entry['duration']+entry['cleanup'])).astimezone(cal['zone']).isoformat()
    # Explicit per-load choices remove old demands, never invent an initial Off.
    overridden=set()
    for entry in f['overrides']:
        keys(entry,{'load','mode'});references([entry['load']],c['loads']);choice(entry['mode'],('unchanged','replace'))
        require(entry['load'] not in overridden,'invalid_mapping');overridden.add(entry['load'])
    for group in c['groups'].values():
        for rule in group['rules']: rule['targets']=[t for t in rule['targets'] if t not in overridden]
        group['rules']=[r for r in group['rules'] if r['targets']]
    ids=set()
    for w in f['windows']:
        keys(w,{'id','room','segment','category','start','end','targets','hvac','policy','comfort','release','home_only','sleep_conflict','initial_state','resume'} | ({'meal'} if 'meal' in w else set()) | ({'timing'} if 'timing' in w else set()))
        identifier(w['id']);require(w['id'] not in ids,'invalid_mapping');ids.add(w['id'])
        require(w['room'] in c['rooms'] and w['segment'] in cal['segments'],'invalid_mapping')
        choice(w['category'],CATEGORIES);choice(w['policy'],('none','scheduled','gated'));comfort(w['comfort'])
        choice(w['release'],('off','existing','leave'));choice(w['sleep_conflict'],('review','allow'))
        choice(w['initial_state'],('review','already_set'));choice(w['resume'],('unknown','stays_off','resumes'))
        require(type(w['home_only']) is bool)
        references(w['targets'],c['loads']);references(w['hvac'],c['loads'])
        require(all(c['loads'][x]['kind']=='binary' for x in w['targets']),'invalid_mapping')
        require(all(c['loads'][x]['kind']=='hvac_power' for x in w['hvac']),'invalid_mapping')
        require(not(w['policy']=='none' and w['hvac']),'invalid_mapping')
        require(w['targets'] or w['hvac'],'invalid_mapping')
        require(not any(o['mode']=='unchanged' and o['load'] in w['targets']+w['hvac'] for o in f['overrides']),'invalid_mapping')
        for target in w['targets']:
            role=c['loads'][target].get('display',{}).get('role')
            require(role not in ('fan','appliance') or w['category']==role,'invalid_mapping')
        if 'timing' in w:
            require(type(w['timing']) is dict and set(w['timing']) <= {'start','end'})
            for side,timing in w['timing'].items():
                keys(timing,{'anchor','offset_minutes'});choice(timing['anchor'],('candle_lighting','sunrise','sunset','end'))
                require(type(timing['offset_minutes']) is int and abs(timing['offset_minutes'])<=1440)
                anchor=cal['segments'][w['segment']].get(timing['anchor']);require(anchor is not None,'invalid_time')
                w={**w,side:(anchor+timedelta(minutes=timing['offset_minutes'])).astimezone(cal['zone']).isoformat()}
        if 'meal' in w:
            meal=next((m for m in p['meals'] if m['id']==w['meal'] and m['segment']==w['segment']),None)
            require(meal is not None,'invalid_mapping')
            if meal['choice'] not in ('family','hosting'): continue
            w={**w,'start':meal['start'],'end':meal['end']}
        a,b=[parse_instant(w[k],cal['zone']) for k in ('start','end')];seg=cal['segments'][w['segment']]
        require(cal['preparation_start']<=a<b<=seg['end'] and b>seg['start'],'invalid_sequence')
        if w['category']=='playtime' and w['sleep_conflict']=='review':
            require(not any(u['room']==w['room'] and u['purpose']=='sleeping' and parse_instant(u['start'],cal['zone'])<b and a<parse_instant(u['end'],cal['zone']) for u in p['room_uses']),'activity_sleep_conflict')
        windows=[(a,b)]
        if w['home_only']:
            windows=[(max(a,parse_instant(h['start'],cal['zone'])),min(b,parse_instant(h['end'],cal['zone']))) for h in p['availability'] if h['state']=='home']
            windows=[(x,y) for x,y in windows if x<y]
        else:
            require(w['category'] in ('appliance','service'),'invalid_mapping')
        for index,(left,right) in enumerate(windows):
            gid='flex_'+w['id']+'_'+str(index);require(gid not in c['groups'],'invalid_mapping')
            label=c['rooms'][w['room']];rules=[]
            for target in w['targets']+(w['hvac'] if w['policy']=='scheduled' else []):
                kind='hvac_power' if target in w['hvac'] else 'state'
                if kind=='hvac_power': fixed_hvac.append({'physical_id':c['loads'][target]['physical_id'],'start':left.isoformat(),'end':right.isoformat()})
                external=w['release']!='off'
                rules.append({'id':'r_'+str(len(rules)),'targets':[target],'start':{'at':left.astimezone(cal['zone']).isoformat()},'end':None if external else {'at':right.astimezone(cal['zone']).isoformat()},'action':{'type':kind,'state':'on'},'release':None if external else {'type':kind,'state':'off'}})
            c['groups'][gid]={'label':label,'track_only':w['category'] in ('fan','appliance'),'rules':rules}
            p['groups'].append({'id':gid,'segment':w['segment'],'group':gid,'start':left.astimezone(cal['zone']).isoformat(),'end':right.astimezone(cal['zone']).isoformat()})
            if w['policy']=='gated':
                comfort(w['comfort'])
                for target in w['hvac']:
                    require(target in overridden,'gated_needs_replacement')
                    conditions.append({'id':gid+'_'+target,'room':w['room'],'load':target,'physical_id':c['loads'][target]['physical_id'],'start':left.isoformat(),'end':right.isoformat(),'policy':w['comfort'],'release':('leave' if right==cal['end'] and not c.get('post_shutoff',True) else w['release']),'live_eligible':False})
        notes.append({'id':w['id'],'room':w['room'],'category':w['category'],'start':w['start'],'end':w['end'],'release':w['release'],'live_eligible':False})
    # Different conditional policies for the same unit require deliberate reconciliation.
    for i,x in enumerate(conditions):
        for y in conditions[i+1:]+fixed_hvac:
            require(x['physical_id']!=y['physical_id'] or max(x['start'],y['start'])>=min(x['end'],y['end']),'conditional_overlap')
    return c,p,{'conditions':conditions,'activities':notes,'feedback':f['feedback'],'extension_digest':digest(f)}


def gate(policy, temperature, unit, now, previous=None, eligible=True, signal=True, gap=False):
    """Shadow intent only. Unknown evidence resets dwell history; no state commands."""
    numeric(now,0,100000000000); comfort(policy); previous=previous or {}; prior=previous.get('intent','unknown')
    if not eligible: return {'intent':'off','reason':'outside_window','since':now}
    if gap or temperature is None or type(temperature) not in (int,float) or not isfinite(temperature) or unit not in ('C','F') or signal is None:
        return {'intent':'unknown','reason':'missing_evidence','since':now}
    if not signal:return {'intent':'off','reason':'activity_gate_off','since':now}
    value=temperature if unit==policy['unit'] else (temperature-32)*5/9 if unit=='F' else temperature*9/5+32
    deviation=(value-policy['target'])*(1 if policy['mode']=='cool' else -1)
    want='on' if deviation>policy['tolerance'] else 'off'
    if prior=='on' and deviation>policy['tolerance']-policy['hysteresis']:want='on'
    since=previous.get('since',now)
    if now<since:return {'intent':'unknown','reason':'clock_rollback','since':now}
    if prior in ('on','off') and want!=prior and now-since<policy['minimum_'+prior]*60:
        return {'intent':prior,'reason':'minimum_dwell','since':since}
    return {'intent':want,'reason':'threshold','since':since if want==prior else now,'deviation':round(deviation,4)}
