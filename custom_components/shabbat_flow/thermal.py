"""Hourly reported thermal evidence; no services or device control."""
from datetime import timedelta
import math
from zoneinfo import ZoneInfo
from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar
from .ownership import instant
from .household import internal_id


def weather_sources(hass):
    registry = er.async_get(hass)
    return [{'entity_id': e.entity_id, 'name': (hass.states.get(e.entity_id).name if hass.states.get(e.entity_id) else e.original_name) or e.entity_id}
            for e in sorted(registry.entities.values(), key=lambda e:e.entity_id)
            if e.domain == 'weather' and e.disabled_by is None]


def identity(hass, entry):
    device = dr.async_get(hass).async_get(entry.device_id) if entry.device_id else None
    area_id = entry.area_id or (device.area_id if device else None)
    area = ar.async_get(hass).async_get_area(area_id) if area_id else None
    return {'entity_id':entry.entity_id, 'registry_id':entry.id, 'platform':entry.platform,
            'area_id':area_id, 'planner_room_id':internal_id('room_',area_id) if area_id else None, 'area_name':area.name if area else None}


def initialize(hass, now, weather_entity_id=None):
    registry = er.async_get(hass)
    climates = sorted((e for e in registry.entities.values() if e.domain=='climate' and e.disabled_by is None), key=lambda e:e.entity_id)
    candidates = weather_sources(hass)
    if weather_entity_id is not None and (not isinstance(weather_entity_id,str) or weather_entity_id not in {c['entity_id'] for c in candidates}):
        raise ValueError('observe_weather')
    selected = weather_entity_id or (candidates[0]['entity_id'] if len(candidates)==1 else None)
    return {'schema_version':1, 'interval_seconds':3600, 'collection_added_at':now.isoformat(),
            'climates':[identity(hass,e) for e in climates[:100]], 'climates_truncated':len(climates)>100,
            'outdoor':identity(hass,registry.async_get(selected)) if selected else None,
            'outdoor_status':'selected' if selected else 'multiple_sources_choose_one' if candidates else 'no_weather_source',
            'samples':[], 'last_slot':-1}


def temperature(value, unit):
    raw = value if type(value) in (int,float) and math.isfinite(value) else None
    celsius = None
    if raw is not None:
        if unit in ('°C','C'): celsius = raw
        elif unit in ('°F','F'): celsius = (raw-32)*5/9
    return {'value':raw, 'unit':unit, 'celsius':round(celsius,4) if celsius is not None else None}


def sample_entity(hass, target, now, climate=False):
    entry = er.async_get(hass).async_get(target['entity_id'])
    if entry is None or entry.id != target['registry_id'] or entry.disabled_by is not None:
        return {'status':'mapping_changed'}
    state = hass.states.get(target['entity_id'])
    if state is None or state.state in ('unknown','unavailable') or state.attributes.get('restored') is True:
        return {'status':'unavailable'}
    attrs = state.attributes
    unit = attrs.get('unit_of_measurement') if state.domain=='sensor' else attrs.get('temperature_unit') or (str(hass.config.units.temperature_unit) if climate else None)
    if unit not in ('°C','C','°F','F'): unit = None
    value=attrs.get('current_temperature' if climate else 'temperature')
    if state.domain=='sensor':
        try: value=float(state.state)
        except (ValueError,TypeError): value=None
    result = {'status':'available', 'state_updated_at':state.last_updated.isoformat(),
              'state_age_seconds':max(0,(now-state.last_updated).total_seconds()),
              'current_temperature':temperature(value,unit)}
    if climate:
        mode = state.state
        result.update(mode=mode, power='off' if mode=='off' else 'on' if mode in ('heat','cool','heat_cool','auto','dry','fan_only') else 'unknown',
                      hvac_action=attrs.get('hvac_action') if attrs.get('hvac_action') in ('off','heating','cooling','drying','idle','fan','defrosting','preheating') else None,
                      target_temperature=temperature(attrs.get('temperature'),unit),
                      target_low=temperature(attrs.get('target_temp_low'),unit),target_high=temperature(attrs.get('target_temp_high'),unit))
    return result


def collect(hass, run, now, resumed=False):
    thermal = run.get('thermal')
    if thermal is None:
        thermal = run['thermal'] = initialize(hass,now)
    start, end = instant(run['start']), instant(run['end'])
    if now < start: return
    # Activity duration is sampled each minute, independently of hourly temperatures.
    activity = thermal.setdefault('activity', {'last_at':start.isoformat(), 'last_power':{},
        'totals':{t['entity_id']:{'on_seconds':0,'off_seconds':0,'unknown_seconds':0,'seen_on':False} for t in thermal['climates']}})
    left, right = instant(activity['last_at']), min(now,end)
    if right >= left:
        gap = resumed or not activity['last_power'] or (now-left).total_seconds()>90
        for target in thermal['climates']:
            eid = target['entity_id']; totals = activity['totals'][eid]
            prior = 'unknown' if gap else activity['last_power'].get(eid,'unknown')
            totals[prior+'_seconds'] += (right-left).total_seconds()
            current = sample_entity(hass,target,now,True).get('power','unknown')
            if now <= end and current == 'on': totals['seen_on'] = True
            activity['last_power'][eid] = current
        activity['last_at'] = right.isoformat()
    last = min(96,int((min(now,end)-start).total_seconds()//3600))
    for slot in range(thermal['last_slot']+1,last+1):
        due = start+timedelta(hours=slot)
        timely = 0 <= (now-due).total_seconds() <= 90 and due >= instant(thermal['collection_added_at']) and now <= end
        record = {'slot':slot,'due':due.isoformat(),'local':due.astimezone(ZoneInfo(run['bundle']['plan']['snapshot']['timezone'])).isoformat(),
                  'sampled_at':now.isoformat() if timely else None,'status':'sampled' if timely else 'missing',
                  'reason':None if timely else 'late_start_upgrade_or_collection_gap'}
        if timely:
            record['climates'] = {t['entity_id']:sample_entity(hass,t,now,True) for t in thermal['climates']}
            record['references'] = {t['entity_id']:sample_entity(hass,t['reference'],now) for t in thermal['climates'] if t.get('reference')}
            record['outdoor'] = sample_entity(hass,thermal['outdoor'],now) if thermal['outdoor'] else {'status':thermal['outdoor_status']}
        thermal['samples'].append(record)
        thermal['last_slot'] = slot
