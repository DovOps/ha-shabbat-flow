"""Read-only, calendar-independent climate study selections and snapshots."""
from copy import deepcopy
from datetime import timedelta
from homeassistant.helpers import entity_registry as er
from .thermal import identity, initialize
from .household import internal_id
from .engine.schedule import digest


def sources(hass):
    result = {'climates':[], 'lights':[], 'references':[]}
    for e in sorted(er.async_get(hass).entities.values(),key=lambda e:e.entity_id):
        if e.disabled_by is not None: continue
        state=hass.states.get(e.entity_id)
        key = 'climates' if e.domain=='climate' else 'lights' if e.domain in ('light','switch') else 'references' if e.domain=='sensor' and state and state.attributes.get('device_class')=='temperature' else None
        if key:
            result[key].append(identity(hass,e)|{'name':state.name if state else e.original_name or e.entity_id})
    return result


def validate(value):
    if not isinstance(value,dict) or set(value)!={'hours','zones','weather_entity_id','note'}: raise ValueError('observe_study')
    if type(value['hours']) is not int or not 1<=value['hours']<=48: raise ValueError('observe_study')
    if not isinstance(value['note'],str) or len(value['note'])>2000: raise ValueError('observe_study')
    zones=value['zones']
    if not isinstance(zones,list) or not 1<=len(zones)<=100: raise ValueError('observe_study')
    ids=set(); lights=set()
    for zone in zones:
        if not isinstance(zone,dict) or set(zone)!={'entity_id','lights','reference'}: raise ValueError('observe_study')
        if not isinstance(zone['entity_id'],str) or zone['entity_id'] in ids: raise ValueError('observe_study')
        ids.add(zone['entity_id'])
        if zone['reference'] is not None and not isinstance(zone['reference'],str): raise ValueError('observe_study')
        if not isinstance(zone['lights'],list) or any(not isinstance(v,str) for v in zone['lights']) or len(set(zone['lights']))!=len(zone['lights']): raise ValueError('observe_study')
        lights.update(zone['lights'])
    if len(lights)>100: raise ValueError('observe_study')
    if value['weather_entity_id'] is not None and not isinstance(value['weather_entity_id'],str): raise ValueError('observe_study')
    return deepcopy(value)


def snapshot(hass, value, now):
    value=validate(value); available=sources(hass)
    indexes={k:{e['entity_id']:e for e in v} for k,v in available.items()}
    thermal=initialize(hass,now,value['weather_entity_id']); thermal['climates']=[]; thermal['climates_truncated']=False
    mapping={}; loads={}
    for zone in value['zones']:
        if zone['entity_id'] not in indexes['climates'] or (zone['reference'] is not None and zone['reference'] not in indexes['references']) or any(e not in indexes['lights'] for e in zone['lights']): raise ValueError('observe_study')
        target=deepcopy(indexes['climates'][zone['entity_id']]); target['study_lights']=zone['lights']; target['reference']=deepcopy(indexes['references'].get(zone['reference']))
        thermal['climates'].append(target)
        for eid in [zone['entity_id'],*zone['lights']]:
            source=indexes['climates'].get(eid) or indexes['lights'][eid]; physical=internal_id('load_',source['registry_id'])
            mapping[physical]=deepcopy(source)
            loads[physical]={'physical_id':physical,'kind':'hvac' if eid==zone['entity_id'] else 'binary','label':{'en':source['name'],'he':source['name']},'display':{'room':source['planner_room_id'],'role':'hvac' if eid==zone['entity_id'] else 'study_lighting'}}
    end=now+timedelta(hours=value['hours'])
    bundle={'study':value,'config':{'loads':loads},'plan':{'snapshot':{'timezone':hass.config.time_zone,'preparation_start':now.isoformat(),'end':end.isoformat()}}}
    return bundle,thermal,mapping


def valid_saved(run):
    validate(run['bundle']['study'])
    from .ownership import instant
    if (instant(run['end'])-instant(run['start'])).total_seconds()!=run['bundle']['study']['hours']*3600: return False
    return run['preview']=={'complete':True,'events':[]} and not run['policy']['enabled'] and run['snapshot_hash']==digest(run['bundle'])
