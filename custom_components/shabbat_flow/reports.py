"""Pure projections and bounded owner reviews; never controls a device."""
from collections import Counter
from copy import deepcopy
from math import isfinite

FIELDS = {'overall','lighting','climate','period_type','worked','differed','next_change','destination','decision'}

def validate_review(value):
    if type(value) is not dict or set(value)!=FIELDS: raise ValueError('observe_review_invalid')
    for key in ('overall','lighting','climate'):
        v=value[key]
        if v is not None and v!='na' and not (type(v) is int and 1<=v<=5): raise ValueError('observe_review_invalid')
    for key,options in [('period_type',('ordinary','exceptional','uncertain')),('destination',('settings','app','uncertain')),('decision',('proposed','applied','deferred','dismissed'))]:
        if value[key] not in options: raise ValueError('observe_review_invalid')
    for key in ('worked','differed','next_change'):
        if type(value[key]) is not str or len(value[key])>2000: raise ValueError('observe_review_invalid')
    return deepcopy(value)

def performance(run):
    """Device-minutes are sampled evidence, never a measure of actuation success."""
    fields=('matched','mismatched','unknown','unplanned')
    totals={k:0.0 for k in fields}; rooms={}; config=run['bundle'].get('config',{})
    loads={l['physical_id']:l for l in config.get('loads',{}).values()}
    for physical,stats in run.get('summary',{}).items():
        room=loads.get(physical,{}).get('display',{}).get('room','unassigned')
        row=rooms.setdefault(room,{'room':room,'label':config.get('rooms',{}).get(room),'devices':0,**{k:0.0 for k in fields}})
        row['devices']+=1
        for key in fields:
            seconds=stats.get(key+'_seconds',0)
            if type(seconds) not in (int,float) or not isfinite(seconds) or seconds<0: seconds=0
            row[key]+=seconds/60;totals[key]+=seconds/60
    for row in [totals,*rooms.values()]:
        known=row['matched']+row['mismatched'];total=sum(row[k] for k in fields)
        row['agreement_percent']=round(100*row['matched']/known,1) if known and run.get('kind')!='climate_study' else None
        row['assessed_percent']=round(100*known/total,1) if total and run.get('kind')!='climate_study' else None
        for key in fields:row[key]=round(row[key],1)
    return {'version':1,'mode':'observe','partial':run['status']!='completed','device_commands_sent':0,'totals':totals,
            'rooms':sorted(rooms.values(),key=lambda r:(-r['mismatched'],-r['unknown'],r['room'])),
            'event_outcomes':dict(Counter(v.get('outcome','unknown') for v in run.get('event_checks',{}).values())),
            'gaps':len(run.get('gaps',[])),'truncated':bool(run.get('truncated')),'source_changed':bool(run.get('source_changed'))}

def review_state(run):
    return {'revision':run.get('review_revision',0),'updated_at':run.get('review_updated_at'),'value':deepcopy(run.get('review')),'history':deepcopy(run.get('review_history',[]))}
