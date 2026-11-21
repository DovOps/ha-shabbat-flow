"""Bounded read-only comfort shadow sampling. Never controls a device."""
from .engine.flexible import gate
from .household import internal_id
from homeassistant.helpers import entity_registry as er
from datetime import datetime
from math import isfinite


def collect(hass,run,now,gap):
    conditions=run.get('preview',{}).get('flex',{}).get('conditions',[])
    if not conditions:return
    store=run.setdefault('comfort',{'version':1,'decisions':[],'last':{},'truncated':False})
    for condition in conditions:
        p=condition['policy'];target=run['mapping'].get(condition['physical_id'],{}).get('entity_id')
        source=p['sensor'] or target;state=hass.states.get(source) if source else None
        eligible=datetime.fromisoformat(condition['start'])<=now<datetime.fromisoformat(condition['end'])
        value=None;unit=None
        if state and state.state not in ('unavailable','unknown') and not state.attributes.get('restored'):
            raw=state.attributes.get('current_temperature') if source.startswith('climate.') else state.state
            try:value=float(raw)
            except (ValueError,TypeError):pass
            if value is not None and not isfinite(value):value=None
            unit=state.attributes.get('temperature_unit',hass.config.units.temperature_unit) if source.startswith('climate.') else state.attributes.get('unit_of_measurement')
            unit={'°C':'C','°F':'F','C':'C','F':'F'}.get(unit)
        signal=True
        if p['signals']:
            entries=[hass.states.get(s) for s in p['signals']]
            signal=True if any(s and s.state=='on' for s in entries) else None if any(s is None or s.state not in ('on','off') for s in entries) else False
        # Never use a planner-controlled signal as a self-reinforcing comfort gate.
        cyclical=False
        registry=er.async_get(hass)
        controlled={e['physical_id'] for e in run['preview']['events'] if e['intent']!='track_only'}
        for sid in p['signals']:
            entry=registry.async_get(sid)
            if entry and internal_id('load_',entry.id) in controlled:cyclical=True
        old=store['last'].get(condition['id'])
        decision=gate(p,value,unit,now.timestamp(),old,eligible,signal,gap or cyclical)
        if not eligible and condition['release']!='off':decision={'intent':'unknown','reason':'external_release','since':now.timestamp()}
        if cyclical:decision['reason']='planner_signal_dependency'
        # HA state timestamps are not sensor measurement timestamps. This is
        # unqualified evidence, explicitly unusable as an activation clearance.
        record={'id':condition['id'],'at':now.isoformat(),'temperature':value,'unit':unit,'source':source,'eligible':eligible,'signal':signal,'freshness':'unverified','actuated':False,**decision}
        hourly=old is None or int(now.timestamp()//3600)!=old.get('hour')
        if hourly or not old or any(old.get(k)!=decision.get(k) for k in ('intent','reason')):
            if len(store['decisions'])<20000:store['decisions'].append(record)
            else:store['truncated']=True
        store['last'][condition['id']]={**decision,'hour':int(now.timestamp()//3600)}
