"""Live HA inventory and explicitly reviewed household intent; no actuators."""
from copy import deepcopy
from datetime import timedelta, datetime, timezone
from hashlib import sha256
import json
import math
from homeassistant.components.climate import ClimateEntityFeature
from homeassistant.helpers import area_registry as ar, floor_registry as fr, label_registry as lr
from homeassistant.helpers import device_registry as dr, entity_registry as er
from .engine.compiler import PlanError, require
from .engine.schedule import validate_configuration
from .engine.planning import validate_calendar

ROLES = ('main_lights', 'night_lights', 'hvac')
DOMAINS = ('light', 'switch', 'climate', 'binary_sensor', 'sensor', 'automation')


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def strings(value):
    return [v for v in value if isinstance(v, str) and len(v) <= 100][:40] if isinstance(value, (list, tuple)) else []


def inventory(hass):
    areas = [{'id': a.id, 'name': a.name, 'floor_id': a.floor_id, 'labels': sorted(a.labels)} for a in ar.async_get(hass).async_list_areas()]
    floors = [{'id': f.floor_id, 'name': f.name} for f in fr.async_get(hass).async_list_floors()]
    device_registry = dr.async_get(hass)
    devices = {}
    entities = []
    for e in er.async_get(hass).entities.values():
        domain = e.entity_id.split('.')[0]
        if domain not in DOMAINS:
            continue
        state = hass.states.get(e.entity_id)
        attrs = state.attributes if state else {}
        # Read only relevant sensor classes; never expose a sensor's state or arbitrary attributes.
        if domain in ('binary_sensor', 'sensor') and attrs.get('device_class') not in ('occupancy', 'motion', 'presence', 'temperature'):
            continue
        device = device_registry.async_get(e.device_id) if e.device_id else None
        if device:
            devices[device.id] = device
        caps = {}
        if domain == 'climate':
            caps = {'modes': [m for m in strings(attrs.get('hvac_modes')) if m in ('off', 'heat', 'cool')],
                    'fan_modes': strings(attrs.get('fan_modes')),
                    'min_temperature': attrs.get('min_temp') if finite(attrs.get('min_temp')) else None,
                    'max_temperature': attrs.get('max_temp') if finite(attrs.get('max_temp')) else None,
                    'unit': {'°C': 'C', '°F': 'F'}.get(hass.config.units.temperature_unit)}
        entities.append({'id': e.id, 'entity_id': e.entity_id, 'name': e.name or attrs.get('friendly_name') or e.original_name or e.entity_id,
                         'domain': domain, 'device_id': e.device_id, 'labels': sorted(e.labels),
                         'device_labels': sorted(device.labels) if device else [],
                         'area_id': e.area_id or (device.area_id if device else None),
                         'area_source': 'entity' if e.area_id else ('device' if device and device.area_id else 'unassigned'),
                         'disabled': e.disabled_by is not None,
                         'available': bool(state and state.state not in ('unknown', 'unavailable') and e.disabled_by is None),
                         'capabilities': caps,
                         'power_support': {'turn_on': bool((attrs.get('supported_features', 0) if isinstance(attrs.get('supported_features', 0), int) and not isinstance(attrs.get('supported_features', 0), bool) else 0) & ClimateEntityFeature.TURN_ON),
                                           'turn_off': bool((attrs.get('supported_features', 0) if isinstance(attrs.get('supported_features', 0), int) and not isinstance(attrs.get('supported_features', 0), bool) else 0) & ClimateEntityFeature.TURN_OFF)} if domain == 'climate' else None,
                         'current': {'mode': state.state if state else None,
                                     'temperature': attrs.get('temperature') if finite(attrs.get('temperature')) else None,
                                     'fan_mode': attrs.get('fan_mode') if attrs.get('fan_mode') in caps.get('fan_modes', []) else None,
                                     'observed_at': datetime.now(timezone.utc).isoformat()} if domain == 'climate' else None})
    used_devices = {e['device_id'] for e in entities}
    result = {'labels': sorted([{'id': l.label_id, 'name': l.name} for l in lr.async_get(hass).async_list_labels()], key=lambda v: v['id']), 'floors': sorted(floors, key=lambda v: v['id']), 'areas': sorted(areas, key=lambda v: v['id']),
              'devices': sorted([{'id': d.id, 'name': d.name_by_user or d.name or d.id, 'area_id': d.area_id, 'labels': sorted(d.labels)}
                                 for d in devices.values() if d.id in used_devices], key=lambda v: v['id']),
              'entities': sorted(entities, key=lambda v: v['id']), 'timezone': hass.config.time_zone}
    # Availability is live telemetry; renames/moves/capability changes affect the structural revision.
    result['revision'] = digest({**result, 'entities': [{k: v for k, v in e.items() if k not in ('available', 'current')} for e in result['entities']]})
    return result


def empty_settings():
    return {'schema_version': 1, 'revision': 0, 'rooms': {}, 'bindings': {}}


def ready(room):
    return room.get('enabled', False) and room.get('setup', {}).get('status', 'ready') == 'ready'


def migrate_settings(saved):
    result = deepcopy(saved)
    require(result.get('schema_version') in (1, 2), 'invalid_mapping')
    if result['schema_version'] == 1:
        for room in result['rooms'].values():
            has_lights = bool(room['roles']['main_lights'] or room['roles']['night_lights'])
            has_hvac = bool(room['roles']['hvac'] and room['hvac']['mode'] != 'none')
            schedulable = has_lights or has_hvac or bool(room['shared_areas'])
            room['setup'] = {'status': 'ready' if room['enabled'] and schedulable else 'draft',
                             'service': not bool(room['purposes']), 'home': False,
                             'bathroom_timing': {a: 'use_window' for a in room['shared_areas']}}
        # A selected-but-unconfigured shared area cannot make a dependent room ready.
        for room in result['rooms'].values():
            if any(not ready(result['rooms'].get(a, {})) for a in room['shared_areas']):
                room['setup']['status'] = 'draft'
        result['schema_version'] = 2
    result['label_filters'] = {**empty_label_filters(), **result.get('label_filters', {})}
    result.setdefault('post_shutoff', False)
    return result


LABEL_ROLES = ('bathroom', 'main_lights', 'night_lights', 'bedroom', 'common_area', 'bathroom_area', 'hallway_area')


def empty_label_filters():
    return dict.fromkeys(LABEL_ROLES, None)


def validate_label_filters(value, inv, previous):
    require(type(value) is dict and set(value) in (set(LABEL_ROLES), set(LABEL_ROLES) - {'bathroom_area', 'hallway_area'}), 'invalid_mapping')
    value = {**empty_label_filters(), **previous, **value}
    known = {label['id'] for label in inv.get('labels', [])}
    for role, label_id in value.items():
        require(label_id is None or isinstance(label_id, str) and 0 < len(label_id) <= 100
                and (label_id in known or label_id == previous.get(role)), 'invalid_mapping')
    return deepcopy(value)


def binding(entity):
    return {k: entity[k] for k in ('area_id', 'domain', 'capabilities')}


def issues(settings, inv):
    entities = {e['id']: e for e in inv['entities']}
    areas = {a['id'] for a in inv['areas']}
    result = []
    for area_id, room in settings['rooms'].items():
        if not ready(room):
            continue
        if area_id not in areas:
            result.append({'code': 'missing_area', 'id': area_id})
        for shared in room['shared_areas']:
            if shared not in areas or not ready(settings['rooms'].get(shared, {})):
                result.append({'code': 'missing_shared', 'id': shared})
        for ids in room['roles'].values():
            for rid in ids:
                e = entities.get(rid)
                code = ('missing_entity' if not e else 'disabled_entity' if e['disabled'] else
                        'binding_changed' if binding(e) != settings['bindings'].get(rid) else
                        'unavailable_entity' if not e['available'] else None)
                if code:
                    result.append({'code': code, 'id': e['entity_id'] if e else rid})
    return sorted(result, key=lambda v: (v['code'], v['id']))


def validate_settings(rooms, inv):
    require(type(rooms) is dict and len(rooms) <= 200)
    areas = {a['id'] for a in inv['areas']}
    entities = {e['id']: e for e in inv['entities']}
    mapped = set()
    bindings = {}
    enabled = 0
    for aid, room in rooms.items():
        require(isinstance(aid, str) and len(aid) <= 100 and type(room) is dict)
        require(set(room) == {'enabled', 'purposes', 'roles', 'shared_areas', 'hvac'} | ({'setup'} if 'setup' in room else set()))
        setup = room.get('setup')
        if setup is not None:
            require(type(setup) is dict and set(setup) == {'status', 'service', 'home', 'bathroom_timing'} | ({'lighting'} if 'lighting' in setup else set()) | ({'phases'} if 'phases' in setup else set()) | ({'area_type'} if 'area_type' in setup else set()))
            require(setup.get('area_type', 'legacy') in ('legacy', 'room', 'common', 'bathroom', 'hallway'))
            require('area_type' not in setup or setup['area_type'] == 'legacy' or setup['service'] == (setup['area_type'] != 'room'))
            phase = room_phases(room)
            require(type(phase) is dict and set(phase) == {'night', 'night_start', 'night_end', 'morning', 'morning_start', 'evening_main', 'evening_meal', 'daytime_meal'})
            require(phase['night'] in ('none', 'after_use', 'home'))
            for key in ('morning', 'evening_main', 'evening_meal', 'daytime_meal'): require(type(phase[key]) is bool)
            for key, low, high in [('night_start', 0, 720), ('night_end', -180, 360), ('morning_start', 0, 360)]: require(type(phase[key]) is int and low <= phase[key] <= high)
            policy = bathroom_policy(room)
            require(type(policy) is dict and set(policy) == {'mode', 'off_after_sunrise', 'on_before_sunset', 'night_enabled', 'night_after_candles', 'morning_after_sunrise'})
            require(policy['mode'] in ('always', 'daylight') and type(policy['night_enabled']) is bool)
            for key, maximum in [('off_after_sunrise', 360), ('on_before_sunset', 360), ('night_after_candles', 720), ('morning_after_sunrise', 180)]:
                require(type(policy[key]) is int and 0 <= policy[key] <= maximum)
            require(setup['status'] in ('draft', 'ready') and type(setup['service']) is bool and type(setup['home']) is bool)
            require(type(setup['bathroom_timing']) is dict and len(setup['bathroom_timing']) <= 20)
            require(all(isinstance(k, str) and len(k) <= 100 and v in ('use_window', 'whole_observance') for k,v in setup['bathroom_timing'].items()))
        require(type(room['enabled']) is bool)
        require(type(room['purposes']) is list and len(room['purposes']) == len(set(room['purposes']))
                and all(p in ('sleeping', 'recreation') for p in room['purposes']))
        require(type(room['shared_areas']) is list and len(room['shared_areas']) <= 20
                and all(isinstance(a, str) for a in room['shared_areas']))
        require(type(room['roles']) is dict and set(room['roles']) == set(ROLES))
        hvac = room['hvac']
        require(type(hvac) is dict and set(hvac) == {'mode', 'temperature', 'fan_mode', 'lead_minutes'})
        require(hvac['mode'] in ('none', 'preserve', 'profile', 'heat', 'cool'))
        require(hvac['temperature'] is None or finite(hvac['temperature']))
        require(hvac['fan_mode'] is None or isinstance(hvac['fan_mode'], str) and len(hvac['fan_mode']) <= 100)
        require(type(hvac['lead_minutes']) is int and 0 <= hvac['lead_minutes'] <= 180)
        if room['enabled']:
            enabled += 1
            require(aid in areas, 'invalid_mapping')
            if ready(room):
                phase = room_phases(room)
                require(phase['night'] == 'none' or bool(room['roles']['night_lights']), 'phase_needs_lights')
                require(not (phase['morning'] or phase['evening_main']) or bool(room['roles']['main_lights']), 'phase_needs_lights')
                require(phase['night'] != 'after_use' or 'recreation' in room['purposes'] or phase['evening_meal'], 'phase_needs_recreation')
                require(not ((phase['night'] != 'none' or phase['morning']) and bathroom_policy(room)['night_enabled']), 'phase_bathroom_conflict')
                require(not bathroom_policy(room)['night_enabled'] or bool(room['roles']['main_lights'] and room['roles']['night_lights']), 'bathroom_night_needs_lights')
                require(hvac['mode'] != 'profile', 'hvac_profile_required')
                require(hvac['mode'] == 'none' or bool(room['roles']['hvac']), 'needs_hvac_device')
                require(hvac['mode'] == 'none' or bool(room['purposes']) or room_phases(room)['evening_meal'] or room_phases(room)['daytime_meal'], 'needs_hvac_use')
                require(all(a != aid and a in areas and ready(rooms.get(a, {})) for a in room['shared_areas']), 'missing_shared')
                if setup:
                    require(bool(room['purposes']) or setup['service'], 'needs_purpose')
                    require(bool(room['roles']['main_lights'] or room['roles']['night_lights'] or room['shared_areas']) or bool(room['roles']['hvac'] and hvac['mode'] != 'none'), 'needs_roles')
                    require(not is_bathroom(room) or bool(room['roles']['main_lights'] or room['roles']['night_lights']), 'needs_roles')
                    require(not setup['home'] or setup['service'], 'invalid_mapping')
                    require(not is_bathroom(room) or not room['shared_areas'], 'invalid_mapping')
                    require(all(not rooms[a]['shared_areas'] for a in room['shared_areas']), 'invalid_mapping')
                    require(all(rooms[a]['roles']['main_lights'] or rooms[a]['roles']['night_lights'] for a in room['shared_areas']), 'missing_shared')
        for role, ids in room['roles'].items():
            require(type(ids) is list and len(ids) <= 100 and all(isinstance(i, str) and len(i) <= 100 for i in ids))
            require(len(ids) == len(set(ids)))
            if not ready(room):
                continue
            for rid in ids:
                e = entities.get(rid)
                require(e is not None and not e['disabled'], 'invalid_mapping')
                require(e['domain'] in (('climate',) if role == 'hvac' else ('light', 'switch')), 'invalid_mapping')
                # A load has one assigned room/role; shared dependencies reuse that assignment.
                require(rid not in mapped, 'invalid_mapping'); mapped.add(rid)
                bindings[rid] = binding(e)
                if role == 'hvac' and hvac['mode'] not in ('none', 'preserve'):
                    c = e['capabilities']
                    require(hvac['mode'] in c['modes'] and 'off' in c['modes'] and hvac['fan_mode'] in c['fan_modes'], 'invalid_mapping')
                    require(finite(hvac['temperature']) and finite(c['min_temperature']) and finite(c['max_temperature'])
                            and c['min_temperature'] <= hvac['temperature'] <= c['max_temperature'] and c['unit'] in ('C', 'F'), 'invalid_mapping')
    require(enabled <= 20 and len(mapped) <= 100, 'invalid_mapping')
    return bindings


def room_phases(room):
    return room.get('setup', {}).get('phases', {'night': 'after_use' if 'recreation' in room.get('purposes', []) and room.get('roles', {}).get('night_lights') else 'none',
        'night_start': 360, 'night_end': -60, 'morning': False, 'morning_start': 120,
        'evening_main': False, 'evening_meal': False, 'daytime_meal': False})


def is_bathroom(room):
    setup = room.get('setup', {})
    return setup.get('area_type', 'legacy') == 'bathroom' or (setup.get('area_type', 'legacy') == 'legacy' and setup.get('service', False))


def bathroom_policy(room):
    return room.get('setup', {}).get('lighting', {'mode': 'always', 'off_after_sunrise': 180,
        'on_before_sunset': 120, 'night_enabled': False, 'night_after_candles': 360, 'morning_after_sunrise': 0})


def bathroom_windows(room, calendar):
    """Allowed light intervals, resolved once from a dated calendar snapshot."""
    policy = bathroom_policy(room)
    windows = {role: [(calendar['preparation_start'], calendar['end'])] for role in ('main_lights', 'night_lights')}
    warnings = []
    def subtract(role, left, right):
        if left >= right: return
        result = []
        for a, b in windows[role]:
            if right <= a or left >= b: result.append((a, b)); continue
            if a < left: result.append((a, left))
            if right < b: result.append((right, b))
        windows[role] = result
    for seg in calendar['segments'].values():
        lo, hi = (calendar['preparation_start'] if seg['start'] == calendar['start'] else seg['start']), seg['end']
        if policy['night_enabled']:
            night = max(lo, seg['candle_lighting'] + timedelta(minutes=policy['night_after_candles']))
            morning = min(hi, seg['sunrise'] + timedelta(minutes=policy['morning_after_sunrise']))
            if night < morning:
                subtract('main_lights', night, morning)
                subtract('night_lights', lo, night)
                subtract('night_lights', morning, hi)
            else: warnings.append('bathroom_night_fallback')
        if policy['mode'] == 'daylight':
            left = seg['sunrise'] + timedelta(minutes=policy['off_after_sunrise'])
            right = seg.get('sunset')
            right = right - timedelta(minutes=policy['on_before_sunset']) if right else None
            if right is not None and lo <= left < right <= hi:
                for role in windows: subtract(role, left, right)
            else: warnings.append('bathroom_daylight_fallback')
    return {role: [{'start': a.astimezone(calendar['zone']).isoformat(), 'end': b.astimezone(calendar['zone']).isoformat()} for a, b in values] for role, values in windows.items()}, sorted(set(warnings))


def internal_id(prefix, value):
    return prefix + sha256(value.encode()).hexdigest()[:20]


def workspace(settings, inv, snapshot):
    """Create a separate planner snapshot; never mutate stored household intent."""
    require(not issues(settings, inv), 'invalid_mapping')
    calendar = validate_calendar(snapshot)
    entities = {e['id']: e for e in inv['entities']}
    areas = {a['id']: a for a in inv['areas']}
    config = {'post_shutoff': settings.get('post_shutoff', False), 'schema_version': 2, 'rooms': {}, 'loads': {}, 'groups': {}, 'profiles': {}}
    label = lambda text: {'en': text[:100], 'he': text[:100]}
    rooms = {a: r for a, r in settings['rooms'].items() if ready(r)}

    def targets(aid, role):
        result = []
        for rid in rooms[aid]['roles'][role]:
            e = entities[rid]
            lid = internal_id('load_', rid)
            if role == 'hvac' and rooms[aid]['hvac']['mode'] == 'none':
                continue
            power_only = role == 'hvac' and rooms[aid]['hvac']['mode'] == 'preserve'
            config['loads'][lid] = {'label': label(e['name']), 'physical_id': lid, 'owner': 'planner',
                                    'kind': 'hvac_power' if power_only else 'hvac' if role == 'hvac' else 'binary', 'capabilities': e['capabilities'] if role == 'hvac' and not power_only else {}}
            result.append(lid)
        return result

    for aid, room in sorted(rooms.items()):
        room_id = internal_id('room_', aid)
        config['rooms'][room_id] = label(areas[aid]['name'])
        phase = room_phases(room)
        for purpose in room['purposes']:
            gid = internal_id('group_', aid + purpose)
            rules = []
            def rule(ids, start, end, action, release):
                if ids:
                    rules.append({'id': 'rule_' + str(len(rules)), 'targets': sorted(set(ids)), 'start': start,
                                  'end': end, 'action': action, 'release': release})
            start = {'anchor': 'use_start', 'offset_minutes': 0}
            end = {'anchor': 'use_end', 'offset_minutes': 0}
            on, off = {'type': 'state', 'state': 'on'}, {'type': 'state', 'state': 'off'}
            main = targets(aid, 'main_lights')
            rule(main, start, None if purpose == 'sleeping' else end, off if purpose == 'sleeping' else on, None if purpose == 'sleeping' else off)
            night = targets(aid, 'night_lights')
            for shared in room['shared_areas']:
                allowed, warnings = bathroom_windows(rooms[shared], calendar)
                for role in ('main_lights', 'night_lights'):
                    ids = targets(shared, role)
                    if not ids: continue
                    whole = room.get('setup', {}).get('bathroom_timing', {}).get(shared) == 'whole_observance'
                    rule(ids, {'at': snapshot['start']} if whole else start,
                         {'at': snapshot['end']} if whole else end, on, off)
                    rules[-1].update(active_windows=allowed[role], warnings=warnings)
            if purpose == 'recreation' and phase['night'] == 'after_use':
                rule(night, end, {'anchor': 'sunrise', 'offset_minutes': phase['night_end']}, on, off)
                if night: rules[-1]['skip_empty'] = True
            elif phase['night'] != 'home':
                rule(night, start, end, on, off)
            for lid in targets(aid, 'hvac'):
                h = room['hvac']; c = config['loads'][lid]['capabilities']
                power_only = h['mode'] == 'preserve'
                rule([lid], {'anchor': 'use_start', 'offset_minutes': -h['lead_minutes'], 'not_before': 'preparation_start'}, end,
                     {'type': 'hvac_power', 'state': 'on'} if power_only else
                     {'type': 'hvac', 'mode': h['mode'], 'temperature': h['temperature'], 'unit': c['unit'], 'fan_mode': h['fan_mode']},
                     {'type': 'hvac_power', 'state': 'off'} if power_only else {'type': 'hvac', 'mode': 'off'})
            config['groups'][gid] = {'label': label(areas[aid]['name']), 'track_only': False, 'rules': rules}
            variants = [('early', 240, 60, 'Early', 'מוקדם'), ('standard', 360, 120, 'Standard', 'רגיל'), ('late', 480, 180, 'Late', 'מאוחר')] if purpose == 'sleeping' else [('evening', 0, 360, 'Evening', 'ערב')]
            for name, delay, duration, en, he in variants:
                window = {'start': {'anchor': 'candle_lighting', 'offset_minutes': delay},
                          'end': {'anchor': 'sunrise' if purpose == 'sleeping' else 'candle_lighting', 'offset_minutes': duration}}
                config['profiles'][internal_id('profile_', aid + purpose + name)] = {'label': {'en': en, 'he': he}, 'room': room_id,
                    'purpose': purpose, 'groups': [gid], 'window': window}
        if room.get('setup', {}).get('home') and phase['night'] == 'none' and not phase['morning']:
            allowed, warnings = bathroom_windows(room, calendar)
            home_rules = []
            for role in ('main_lights', 'night_lights'):
                ids = targets(aid, role)
                if ids:
                    home_rules.append({'id': role, 'targets': sorted(set(ids)),
                        'start': {'anchor': 'use_start', 'offset_minutes': 0},
                        'end': {'anchor': 'use_end', 'offset_minutes': 0},
                        'action': {'type': 'state', 'state': 'on'}, 'release': {'type': 'state', 'state': 'off'},
                        'active_windows': allowed[role], 'warnings': warnings})
            require(bool(home_rules), 'needs_roles')
            config['groups'][internal_id('home_', aid)] = {
                'label': label(areas[aid]['name']), 'track_only': False, 'activation': 'home', 'rules': home_rules}
        # Home-driven phases are clipped to explicit availability before union.
        if phase['night'] == 'home' or phase['morning']:
            phase_rules = []
            for role in ('main_lights', 'night_lights'):
                ids = targets(aid, role)
                if not ids: continue
                intervals, notices = [], []
                for seg in calendar['segments'].values():
                    lo = calendar['preparation_start'] if seg['start'] == calendar['start'] else seg['start']
                    hi = seg['end']
                    night_start = min(hi, max(lo, seg['candle_lighting'] + timedelta(minutes=phase['night_start'])))
                    night_end = min(hi, max(lo, seg['sunrise'] + timedelta(minutes=phase['night_end'])))
                    if role == 'night_lights' and phase['night'] == 'home':
                        if night_start < night_end: intervals.append((night_start, night_end))
                        else: notices.append('phase_empty')
                    if role == 'main_lights':
                        if phase['night'] == 'home' and phase['evening_main'] and lo < night_start: intervals.append((lo, night_start))
                        morning = min(hi, max(lo, seg['sunrise'] + timedelta(minutes=phase['morning_start'])))
                        if phase['morning'] and morning < hi: intervals.append((morning, hi))
                phase_rules.append({'id': role, 'targets': ids, 'start': {'anchor':'use_start','offset_minutes':0},
                    'end': {'anchor':'use_end','offset_minutes':0}, 'action': {'type':'state','state':'on'}, 'release': {'type':'state','state':'off'},
                    'active_windows':[{'start':a.astimezone(calendar['zone']).isoformat(),'end':b.astimezone(calendar['zone']).isoformat()} for a,b in intervals], 'warnings':sorted(set(notices))})
            if phase_rules: config['groups'][internal_id('phases_',aid)]={'label':label(areas[aid]['name']), 'track_only':False, 'activation':'home','include_preparation':True,'rules':phase_rules}
        if phase['evening_meal'] or phase['daytime_meal']:
            meal_rules=[]
            ids=targets(aid,'main_lights')
            if ids: meal_rules.append({'id':'meal_lights','targets':ids,'start':{'anchor':'use_start','offset_minutes':0},'end':{'anchor':'use_end','offset_minutes':0},'action':{'type':'state','state':'on'},'release':{'type':'state','state':'off'}})
            for lid in targets(aid,'hvac'):
                h=room['hvac'];c=config['loads'][lid]['capabilities'];power=h['mode']=='preserve'
                meal_rules.append({'id':'meal_hvac_'+str(len(meal_rules)),'targets':[lid],'start':{'anchor':'use_start','offset_minutes':-h['lead_minutes'],'not_before':'preparation_start'},'end':{'anchor':'use_end','offset_minutes':0},
                    'action':{'type':'hvac_power','state':'on'} if power else {'type':'hvac','mode':h['mode'],'temperature':h['temperature'],'unit':c['unit'],'fan_mode':h['fan_mode']},
                    'release':{'type':'hvac_power','state':'off'} if power else {'type':'hvac','mode':'off'}})
            for kind in ('evening', 'daytime'):
                if not phase[kind+'_meal']: continue
                rules = deepcopy(meal_rules)
                if kind == 'evening' and phase['night'] == 'after_use':
                    ids = targets(aid, 'night_lights')
                    if ids: rules.append({'id':'meal_background','targets':ids,'start':{'anchor':'use_end','offset_minutes':0},
                        'end':{'anchor':'sunrise','offset_minutes':phase['night_end']},'action':{'type':'state','state':'on'},
                        'release':{'type':'state','state':'off'},'skip_empty':True})
                if rules: config['groups'][internal_id('meal_',aid+kind)]={'label':label(areas[aid]['name']), 'track_only':False,'rules':rules}
    # Daylight is an independent lighting mask, never an HVAC override.
    for aid, room in rooms.items():
        if bathroom_policy(room)['mode'] != 'daylight': continue
        daylight_room = deepcopy(room)
        daylight_room['setup']['lighting'] = {**bathroom_policy(room), 'night_enabled': False}
        allowed, notices = bathroom_windows(daylight_room, calendar)
        light_ids = {internal_id('load_', rid) for role in ('main_lights', 'night_lights') for rid in room['roles'][role]}
        for group in config['groups'].values():
            for rule in group['rules']:
                if rule['action'] != {'type': 'state', 'state': 'on'} or not light_ids.intersection(rule['targets']): continue
                require(set(rule['targets']) <= light_ids, 'invalid_mapping')
                windows = allowed['main_lights']
                if 'active_windows' in rule:
                    intersections = []
                    for a in rule['active_windows']:
                        for b in windows:
                            start = max(datetime.fromisoformat(a['start']), datetime.fromisoformat(b['start']))
                            end = min(datetime.fromisoformat(a['end']), datetime.fromisoformat(b['end']))
                            if start < end: intersections.append({'start': start.isoformat(), 'end': end.isoformat()})
                    windows = intersections
                rule['active_windows'] = windows
                rule['warnings'] = sorted(set(rule.get('warnings', []) + notices))
    # Explicit zero-target groups are valid, but compiler requires at least one mapped load.
    require(bool(config['loads']) and (bool(config['groups'])), 'invalid_mapping')
    validate_configuration(config)
    plan = {'schema_version': 2, 'language': 'en', 'snapshot': deepcopy(snapshot),
            'availability': [{'id': 'home_1', 'start': snapshot['preparation_start'], 'end': snapshot['end'], 'state': 'unset'}],
            'room_uses': [], 'meals': [], 'groups': []}
    for sid, seg in calendar['segments'].items():
        for kind, anchor, delay, duration in [('evening', seg['candle_lighting'], 120, 180), ('daytime', seg['sunrise'], 300, 120)]:
            start = max(seg['start'], min(anchor + timedelta(minutes=delay), seg['end'] - timedelta(minutes=1)))
            end = min(start + timedelta(minutes=duration), seg['end'])
            plan['meals'].append({'id': sid + '_' + kind, 'segment': sid, 'kind': kind, 'choice': 'unset',
                                 'start': start.astimezone(calendar['zone']).isoformat(),
                                 'end': end.astimezone(calendar['zone']).isoformat(), 'groups': [internal_id('meal_',aid+kind) for aid,r in rooms.items() if room_phases(r)[kind+'_meal'] and internal_id('meal_',aid+kind) in config['groups']]})
    return {'config': config, 'plan': plan}
