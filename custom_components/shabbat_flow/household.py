"""Live HA inventory and explicitly reviewed household intent; no actuators."""
from copy import deepcopy
from datetime import timedelta, datetime, timezone
from hashlib import sha256
import json
import math
from homeassistant.helpers import area_registry as ar, floor_registry as fr
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
    areas = [{'id': a.id, 'name': a.name, 'floor_id': a.floor_id} for a in ar.async_get(hass).async_list_areas()]
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
                         'domain': domain, 'device_id': e.device_id,
                         'area_id': e.area_id or (device.area_id if device else None),
                         'area_source': 'entity' if e.area_id else ('device' if device and device.area_id else 'unassigned'),
                         'disabled': e.disabled_by is not None,
                         'available': bool(state and state.state not in ('unknown', 'unavailable') and e.disabled_by is None),
                         'capabilities': caps,
                         'current': {'mode': state.state if state else None,
                                     'temperature': attrs.get('temperature') if finite(attrs.get('temperature')) else None,
                                     'fan_mode': attrs.get('fan_mode') if attrs.get('fan_mode') in caps.get('fan_modes', []) else None,
                                     'observed_at': datetime.now(timezone.utc).isoformat()} if domain == 'climate' else None})
    used_devices = {e['device_id'] for e in entities}
    result = {'floors': sorted(floors, key=lambda v: v['id']), 'areas': sorted(areas, key=lambda v: v['id']),
              'devices': sorted([{'id': d.id, 'name': d.name_by_user or d.name or d.id, 'area_id': d.area_id}
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
    return result


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
            require(type(setup) is dict and set(setup) == {'status', 'service', 'home', 'bathroom_timing'})
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
        require(hvac['mode'] in ('none', 'heat', 'cool'))
        require(hvac['temperature'] is None or finite(hvac['temperature']))
        require(hvac['fan_mode'] is None or isinstance(hvac['fan_mode'], str) and len(hvac['fan_mode']) <= 100)
        require(type(hvac['lead_minutes']) is int and 0 <= hvac['lead_minutes'] <= 180)
        if room['enabled']:
            enabled += 1
            require(aid in areas, 'invalid_mapping')
            if ready(room):
                require(all(a != aid and a in areas and ready(rooms.get(a, {})) for a in room['shared_areas']), 'missing_shared')
                if setup:
                    require(bool(room['purposes']) or setup['service'], 'needs_purpose')
                    require(bool(room['roles']['main_lights'] or room['roles']['night_lights'] or room['shared_areas']) or bool(room['roles']['hvac'] and hvac['mode'] != 'none'), 'needs_roles')
                    require(not setup['service'] or bool(room['roles']['main_lights'] or room['roles']['night_lights']), 'needs_roles')
                    require(not setup['home'] or setup['service'], 'invalid_mapping')
                    require(not setup['service'] or not room['shared_areas'], 'invalid_mapping')
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
                if role == 'hvac' and hvac['mode'] != 'none':
                    c = e['capabilities']
                    require(hvac['mode'] in c['modes'] and 'off' in c['modes'] and hvac['fan_mode'] in c['fan_modes'], 'invalid_mapping')
                    require(finite(hvac['temperature']) and finite(c['min_temperature']) and finite(c['max_temperature'])
                            and c['min_temperature'] <= hvac['temperature'] <= c['max_temperature'] and c['unit'] in ('C', 'F'), 'invalid_mapping')
    require(enabled <= 20 and len(mapped) <= 100, 'invalid_mapping')
    return bindings


def internal_id(prefix, value):
    return prefix + sha256(value.encode()).hexdigest()[:20]


def workspace(settings, inv, snapshot):
    """Create a separate planner snapshot; never mutate stored household intent."""
    require(not issues(settings, inv), 'invalid_mapping')
    calendar = validate_calendar(snapshot)
    entities = {e['id']: e for e in inv['entities']}
    areas = {a['id']: a for a in inv['areas']}
    config = {'schema_version': 2, 'rooms': {}, 'loads': {}, 'groups': {}, 'profiles': {}}
    label = lambda text: {'en': text[:100], 'he': text[:100]}
    rooms = {a: r for a, r in settings['rooms'].items() if ready(r)}

    def targets(aid, role):
        result = []
        for rid in rooms[aid]['roles'][role]:
            e = entities[rid]
            lid = internal_id('load_', rid)
            if role == 'hvac' and rooms[aid]['hvac']['mode'] == 'none':
                continue
            config['loads'][lid] = {'label': label(e['name']), 'physical_id': lid, 'owner': 'planner',
                                    'kind': 'hvac' if role == 'hvac' else 'binary', 'capabilities': e['capabilities'] if role == 'hvac' else {}}
            result.append(lid)
        return result

    for aid, room in sorted(rooms.items()):
        room_id = internal_id('room_', aid)
        config['rooms'][room_id] = label(areas[aid]['name'])
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
                shared_targets = targets(shared, 'night_lights') + targets(shared, 'main_lights')
                if room.get('setup', {}).get('bathroom_timing', {}).get(shared) == 'whole_observance':
                    rule(shared_targets, {'at': snapshot['start']}, {'at': snapshot['end']}, on, off)
                else:
                    night.extend(shared_targets)
            rule(night, start, end, on, off)
            for lid in targets(aid, 'hvac'):
                h = room['hvac']; c = config['loads'][lid]['capabilities']
                rule([lid], {'anchor': 'use_start', 'offset_minutes': -h['lead_minutes']}, end,
                     {'type': 'hvac', 'mode': h['mode'], 'temperature': h['temperature'], 'unit': c['unit'], 'fan_mode': h['fan_mode']},
                     {'type': 'hvac', 'mode': 'off'})
            config['groups'][gid] = {'label': label(areas[aid]['name']), 'track_only': False, 'rules': rules}
            variants = [('early', 240, 60, 'Early', 'מוקדם'), ('standard', 360, 120, 'Standard', 'רגיל'), ('late', 480, 180, 'Late', 'מאוחר')] if purpose == 'sleeping' else [('evening', 0, 360, 'Evening', 'ערב')]
            for name, delay, duration, en, he in variants:
                window = {'start': {'anchor': 'candle_lighting', 'offset_minutes': delay},
                          'end': {'anchor': 'sunrise' if purpose == 'sleeping' else 'candle_lighting', 'offset_minutes': duration}}
                config['profiles'][internal_id('profile_', aid + purpose + name)] = {'label': {'en': en, 'he': he}, 'room': room_id,
                    'purpose': purpose, 'groups': [gid], 'window': window}
        if room.get('setup', {}).get('home'):
            ids = targets(aid, 'main_lights') + targets(aid, 'night_lights')
            require(bool(ids), 'needs_roles')
            config['groups'][internal_id('home_', aid)] = {
                'label': label(areas[aid]['name']), 'track_only': False, 'activation': 'home',
                'rules': [{'id': 'home_lights', 'targets': sorted(set(ids)),
                           'start': {'anchor': 'use_start', 'offset_minutes': 0},
                           'end': {'anchor': 'use_end', 'offset_minutes': 0},
                           'action': {'type': 'state', 'state': 'on'}, 'release': {'type': 'state', 'state': 'off'}}]}
    # Explicit zero-target groups are valid, but compiler requires at least one mapped load.
    require(bool(config['loads']) and (bool(config['profiles']) or any(g.get('activation') == 'home' for g in config['groups'].values())), 'invalid_mapping')
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
                                 'end': end.astimezone(calendar['zone']).isoformat(), 'groups': []})
    return {'config': config, 'plan': plan}
