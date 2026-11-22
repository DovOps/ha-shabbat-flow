"""Read-only projection of exact compiled plan moments; never shifts calendar dates."""
from copy import deepcopy
from datetime import datetime
from .schedule import compile_schedule, digest
from .compiler import require


def instant(value):return datetime.fromisoformat(value.replace('Z','+00:00'))


def catalog(bundle):
    preview=compile_schedule(**bundle)
    require(preview['complete'],'rehearsal_incomplete')
    loads=bundle['config']['loads'];plan=bundle['plan'];moments={}
    for segment in plan['snapshot']['segments']:
        at=instant(segment['candle_lighting']).isoformat()
        moments.setdefault(at,{'at':at,'kinds':set(),'areas':set()})['kinds'].add('candles')
    for e in preview['events']:
        at=instant(e['utc']).isoformat();m=moments.setdefault(at,{'at':at,'kinds':set(),'areas':set()})
        aliases=[l for l in loads.values() if l['physical_id']==e['physical_id']]
        for load in aliases:
            display=load.get('display',{});area=display.get('room')
            if area:m['areas'].add(area)
            state=e['action'].get('state',e['action'].get('mode'));on=state not in ('off',None)
            kinds={r['kind'] for r in e['reasons']}
            if 'nap' in kinds:kind='nap' if on else 'wake'
            elif 'meal' in kinds:kind='meal'
            elif 'overnight_hvac' in kinds:kind='wake'
            elif display.get('area_type')=='bathroom':
                daytime=any(instant(s['sunrise'])<=instant(at)<instant(s.get('sunset',s['end'])) for s in plan['snapshot']['segments'])
                kind=('bathroom_return' if on else 'daylight_break') if daytime else 'bathroom'
            elif display.get('role')=='night_lights':kind='night' if on else 'morning'
            else:kind='transition'
            m['kinds'].add(kind)
    return {'snapshot_hash':digest(bundle),'timezone':plan['snapshot']['timezone'],'areas':deepcopy(bundle['config']['rooms']),
            'moments':[{**m,'kinds':sorted(m['kinds']),'areas':sorted(m['areas'])} for m in sorted(moments.values(),key=lambda m:instant(m['at']))]}


def project(bundle,at,mode,areas):
    info=catalog(bundle)
    require(mode in ('transition','moment'),'rehearsal_invalid')
    require(isinstance(areas,list) and 0<len(areas)<=100 and all(isinstance(a,str) and a in info['areas'] for a in areas) and len(set(areas))==len(areas),'rehearsal_areas')
    require(isinstance(at,str) and at in {m['at'] for m in info['moments']},'rehearsal_moment')
    events=compile_schedule(**bundle)['events'];selected={}
    for e in events:
        if instant(e['utc'])>instant(at):continue
        if mode=='transition' and instant(e['utc'])!=instant(at):continue
        selected[e['physical_id']]=e
    loads=bundle['config']['loads'];scope={l['physical_id'] for l in loads.values() if l.get('display',{}).get('room') in areas}
    result=[]
    for physical in sorted(scope):
        aliases=[l for l in loads.values() if l['physical_id']==physical];event=selected.get(physical)
        result.append({'physical_id':physical,'name':aliases[0]['label'],'areas':sorted({l.get('display',{}).get('room') for l in aliases if l.get('display',{}).get('room')}),'event':deepcopy(event),'reason':None if event else 'rehearsal_unknown'})
    # Related resources from the complete plan, never implicitly selected.
    groups={r['group'] for row in result if row['event'] for r in row['event']['reasons']}
    related={l.get('display',{}).get('room') for e in selected.values() if any(r['group'] in groups for r in e['reasons']) for l in loads.values() if l['physical_id']==e['physical_id']}
    return {**info,'at':at,'mode':mode,'selected_areas':sorted(areas),'rows':result,'related_areas':sorted(a for a in related if a and a not in areas)}
