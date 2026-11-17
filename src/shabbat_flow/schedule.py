"""Generic preview compiler. Explicit intentions only; never calls devices."""
from collections import defaultdict
from datetime import timedelta
from hashlib import sha256
import json
import math

from .compiler import PlanError, identifier, keys, labels, parse_instant, references, require
from .planning import bounded_list, choice, validate_calendar, validate_room_uses

MAX_EXPANDED = 10000


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(value):
    return sha256(canonical(value).encode()).hexdigest()


def number(value):
    require(type(value) in (int, float) and math.isfinite(value))


def catalog(value):
    require(type(value) is dict and len(value) <= 100)
    for key in value:
        identifier(key)


def validate_action(action, load):
    require(type(action) is dict)
    if load['kind'] == 'binary':
        keys(action, {'type', 'state'})
        require(action['type'] == 'state')
        choice(action['state'], ('on', 'off'))
    else:
        caps = load['capabilities']
        require(action.get('type') == 'hvac')
        choice(action.get('mode'), caps['modes'])
        if action['mode'] == 'off':
            keys(action, {'type', 'mode'})
        else:
            keys(action, {'type', 'mode', 'temperature', 'unit', 'fan_mode'})
            number(action['temperature'])
            require(caps['min_temperature'] <= action['temperature'] <= caps['max_temperature'])
            require(action['unit'] == caps['unit'])
            choice(action['fan_mode'], caps['fan_modes'])


def validate_time(value):
    require(type(value) is dict)
    if 'at' in value:
        keys(value, {'at'})
        require(type(value['at']) is str and len(value['at']) <= 40, 'invalid_time')
    else:
        keys(value, {'anchor', 'offset_minutes'})
        choice(value['anchor'], ('candle_lighting', 'sunrise', 'use_start', 'use_end'))
        require(type(value['offset_minutes']) is int and abs(value['offset_minutes']) <= 1440)


def validate_configuration(config):
    keys(config, {'schema_version', 'rooms', 'loads', 'groups', 'profiles'})
    require(type(config['schema_version']) is int and config['schema_version'] == 2)
    for field in ('rooms', 'loads', 'groups', 'profiles'):
        catalog(config[field])
    require(bool(config['rooms']) and bool(config['loads']))
    for label in config['rooms'].values():
        labels(label)
    physical = {}
    for load in config['loads'].values():
        keys(load, {'label', 'physical_id', 'owner', 'kind', 'capabilities'})
        labels(load['label'])
        identifier(load['physical_id'])
        identifier(load['owner'])
        choice(load['kind'], ('binary', 'hvac'))
        caps = load['capabilities']
        if load['kind'] == 'binary':
            keys(caps, set())
        else:
            keys(caps, {'modes', 'unit', 'min_temperature', 'max_temperature', 'fan_modes'})
            references(caps['modes'], ('off', 'heat', 'cool'))
            require(bool(caps['modes']))
            choice(caps['unit'], ('C', 'F'))
            number(caps['min_temperature']); number(caps['max_temperature'])
            require(caps['min_temperature'] <= caps['max_temperature'])
            bounded_list(caps['fan_modes'], 20)
            require(bool(caps['fan_modes']))
            for mode in caps['fan_modes']:
                identifier(mode)
            require(len(caps['fan_modes']) == len(set(caps['fan_modes'])))
        identity = {key: load[key] for key in ('owner', 'kind', 'capabilities')}
        prior = physical.setdefault(load['physical_id'], identity)
        require(prior == identity, 'invalid_mapping')
    for group in config['groups'].values():
        keys(group, {'label', 'track_only', 'rules'})
        labels(group['label'])
        require(type(group['track_only']) is bool)
        bounded_list(group['rules'], 50)
        seen = set()
        for rule in group['rules']:
            keys(rule, {'id', 'targets', 'start', 'end', 'action', 'release'})
            identifier(rule['id'])
            require(rule['id'] not in seen, 'invalid_mapping'); seen.add(rule['id'])
            references(rule['targets'], config['loads'])
            require(bool(rule['targets']))
            validate_time(rule['start'])
            if rule['end'] is None:
                require(rule['release'] is None)
            else:
                validate_time(rule['end'])
                require(rule['release'] is not None)
            for target in rule['targets']:
                validate_action(rule['action'], config['loads'][target])
                if rule['release'] is not None:
                    validate_action(rule['release'], config['loads'][target])
    for profile in config['profiles'].values():
        keys(profile, {'label', 'room', 'purpose', 'groups'})
        labels(profile['label'])
        require(type(profile['room']) is str and profile['room'] in config['rooms'], 'invalid_mapping')
        choice(profile['purpose'], ('sleeping', 'recreation', 'other'))
        references(profile['groups'], config['groups'])


def interval(item, calendar):
    start, end = (parse_instant(item[k], calendar['zone']) for k in ('start', 'end'))
    require(calendar['preparation_start'] <= start < end <= calendar['end'], 'invalid_sequence')
    return start, end


def compile_schedule(config, plan):
    validate_configuration(config)
    keys(plan, {'schema_version', 'language', 'snapshot', 'availability', 'room_uses', 'meals', 'groups'})
    require(type(plan['schema_version']) is int and plan['schema_version'] == 2)
    choice(plan['language'], ('en', 'he'))
    calendar = validate_calendar(plan['snapshot'])
    # Validate fixed timestamps even in currently unselected groups.
    for group in config['groups'].values():
        for rule in group['rules']:
            for time in (rule['start'], rule['end']):
                if time is not None and 'at' in time:
                    parse_instant(time['at'], calendar['zone'])
    issues, availability, selections = [], [], []
    bounded_list(plan['availability'], 100)
    cursor = calendar['preparation_start']
    seen = set()
    for item in plan['availability']:
        keys(item, {'id', 'start', 'end', 'state'})
        identifier(item['id'])
        require(item['id'] not in seen, 'invalid_mapping'); seen.add(item['id'])
        choice(item['state'], ('home', 'away', 'unset'))
        start, end = interval(item, calendar)
        require(start == cursor, 'invalid_sequence')
        availability.append((start, end, item['state']))
        cursor = end
        if item['state'] == 'unset':
            issues.append({'code': 'availability_unset', 'id': item['id']})
    require(cursor == calendar['end'], 'invalid_sequence')

    def at_home(start, end):
        require(not any(state == 'away' and a < end and start < b
                        for a, b, state in availability), 'away_conflict')

    def selection(item, groups, kind):
        require(type(item['segment']) is str and item['segment'] in calendar['segments'], 'invalid_mapping')
        start, end = interval(item, calendar)
        segment = calendar['segments'][item['segment']]
        require(start < segment['end'] and end > segment['start'], 'invalid_sequence')
        references(groups, config['groups'])
        for group in groups:
            selections.append({'id': item['id'], 'kind': kind, 'segment': item['segment'],
                               'group': group, 'use_start': start, 'use_end': end})
        return start, end

    bounded_list(plan['room_uses'], 300)
    uses = []
    for use in plan['room_uses']:
        keys(use, {'id', 'room', 'purpose', 'control', 'profile', 'start', 'end', 'segment'})
        uses.append({k: v for k, v in use.items() if k != 'segment'})
    room_result = validate_room_uses(plan['snapshot'], uses, list(config['rooms']),
                                     {k: v['purpose'] for k, v in config['profiles'].items()})
    for conflict in room_result['overlap_conflicts']:
        issues.append({'code': 'room_overlap', **conflict})
    for use in plan['room_uses']:
        groups = []
        if use['control'] == 'planner':
            profile = config['profiles'][use['profile']]
            require(profile['room'] == use['room'], 'invalid_mapping')
            groups = profile['groups']
        start, end = selection(use, groups, 'room_use')
        at_home(start, end)
    bounded_list(plan['meals'], 100)
    meal_segments, seen = set(), set()
    for meal in plan['meals']:
        keys(meal, {'id', 'segment', 'kind', 'choice', 'start', 'end', 'groups'})
        identifier(meal['id']); identifier(meal['kind'])
        require(meal['id'] not in seen, 'invalid_mapping'); seen.add(meal['id'])
        choice(meal['choice'], ('unset', 'none', 'away', 'family', 'hosting'))
        references(meal['groups'], config['groups'])
        home = meal['choice'] in ('family', 'hosting')
        start, end = selection(meal, meal['groups'] if home else [], 'meal')
        meal_segments.add(meal['segment'])
        if home:
            at_home(start, end)
        elif meal['choice'] == 'unset':
            issues.append({'code': 'meal_unset', 'id': meal['id']})
    for segment in sorted(set(calendar['segments']) - meal_segments):
        issues.append({'code': 'meals_missing', 'id': segment})
    bounded_list(plan['groups'], 100)
    seen = set()
    for item in plan['groups']:
        keys(item, {'id', 'segment', 'group', 'start', 'end'})
        identifier(item['id'])
        require(item['id'] not in seen, 'invalid_mapping'); seen.add(item['id'])
        selection(item, [item['group']], 'group')
    # Canonicalize unordered input collections, preserving ordered calendar segments.
    clean_config = json.loads(canonical(config))
    for load in clean_config['loads'].values():
        del load['label']
    for group in clean_config['groups'].values():
        del group['label']
        group['rules'].sort(key=lambda v: v['id'])
        for rule in group['rules']:
            rule['targets'].sort()
    for profile in clean_config['profiles'].values():
        del profile['label']; profile['groups'].sort()
    clean_config['rooms'] = sorted(config['rooms'])
    clean_plan = {k: v for k, v in plan.items() if k != 'language'}
    clean_plan = json.loads(canonical(clean_plan))
    for field in ('room_uses', 'meals', 'groups'):
        clean_plan[field].sort(key=lambda v: v['id'])
    for meal in clean_plan['meals']:
        meal['groups'].sort()
    result = {'preview_only': True, 'complete': not issues, 'issues': issues,
              'digest': digest({'compiler': 'generic-v2.1', 'config': clean_config, 'plan': clean_plan}),
              'events': []}
    if issues:
        result['issues'] = sorted(issues, key=canonical)
        return result
    demands, tracked = defaultdict(list), []
    count = 0

    def resolve(time, selection):
        if 'at' in time:
            instant = parse_instant(time['at'], calendar['zone'])
        else:
            anchors = {**calendar['segments'][selection['segment']], **selection}
            try:
                instant = anchors[time['anchor']] + timedelta(minutes=time['offset_minutes'])
            except OverflowError:
                raise PlanError('invalid_time') from None
        require(calendar['preparation_start'] <= instant <= calendar['end'], 'invalid_sequence')
        return instant

    for selected in sorted(selections, key=lambda v: (v['kind'], v['id'], v['segment'], v['group'])):
        group = config['groups'][selected['group']]
        for rule in group['rules']:
            start = resolve(rule['start'], selected)
            end = resolve(rule['end'], selected) if rule['end'] is not None else None
            require(start < calendar['end'] and (end is None or start < end), 'invalid_sequence')
            reason = {k: selected[k] for k in ('id', 'kind', 'segment', 'group')}
            reason['rule'] = rule['id']
            for target in rule['targets']:
                count += 1
                require(count <= MAX_EXPANDED)
                physical = config['loads'][target]['physical_id']
                demand = {'start': start, 'end': end, 'action': rule['action'],
                          'release': rule['release'], 'reason': reason}
                if group['track_only']:
                    tracked.append((physical, demand))
                else:
                    demands[physical].append(demand)

    def event(physical, when, action, reasons, intent):
        reasons = sorted({canonical(v): v for v in reasons}.values(), key=canonical)
        utc = when.isoformat().replace('+00:00', 'Z')
        entry = {'physical_id': physical, 'utc': utc, 'local': when.astimezone(calendar['zone']).isoformat(),
                 'action': action, 'reasons': reasons, 'intent': intent}
        entry['id'] = digest({'period': plan['snapshot']['period_id'], **entry})[:20]
        return entry

    for physical, items in sorted(demands.items()):
        last = None
        times = sorted({v[k] for v in items for k in ('start', 'end') if v[k] is not None})
        for when in times:
            active = [v for v in items if v['end'] is not None and v['start'] <= when < v['end']]
            points = [v for v in items if v['end'] is None and v['start'] == when]
            ending = [v for v in items if v['end'] == when]
            wanted = [(v['action'], v['reason']) for v in active + points]
            if not wanted:
                wanted = [(v['release'], v['reason']) for v in ending]
            require(bool(wanted))
            actions = {canonical(action) for action, _ in wanted}
            require(len(actions) == 1, 'event_conflict')
            action = wanted[0][0]
            if action != last:
                result['events'].append(event(physical, when, action, [r for _, r in wanted], 'set_state'))
                last = action
            elif result['events']:
                # Preserve additional dependency reasons even when no new command is needed.
                previous = next(v for v in reversed(result['events']) if v['physical_id'] == physical)
                merged = previous['reasons'] + [r for _, r in wanted]
                previous.update(event(physical, parse_instant(previous['local'], calendar['zone']),
                                      action, merged, 'set_state'))
    for physical, item in tracked:
        result['events'].append(event(physical, item['start'], item['action'], [item['reason']], 'track_only'))
        if item['end'] is not None:
            result['events'].append(event(physical, item['end'], item['release'], [item['reason']], 'track_only'))
    result['events'] = sorted({v['id']: v for v in result['events']}.values(), key=lambda v: (v['utc'], v['physical_id'], v['id']))
    return result
