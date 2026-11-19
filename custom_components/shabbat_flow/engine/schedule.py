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
    if load['kind'] in ('binary', 'hvac_power'):
        keys(action, {'type', 'state'})
        require(action['type'] == ('hvac_power' if load['kind'] == 'hvac_power' else 'state'))
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
        keys(value, {'anchor', 'offset_minutes'} | ({'not_before'} if 'not_before' in value else set()))
        if 'not_before' in value:
            require(value['not_before'] == 'preparation_start' and value['anchor'] == 'use_start')
        choice(value['anchor'], ('candle_lighting', 'sunrise', 'use_start', 'use_end', 'entertaining_end'))
        require(type(value['offset_minutes']) is int and abs(value['offset_minutes']) <= 1440)


def validate_rest_defaults(value):
    keys(value, {'nap_after_sunrise', 'nap_duration', 'lead_minutes', 'late_wake_after_sunrise'})
    for key, low, high in [('nap_after_sunrise',0,720), ('nap_duration',15,480), ('lead_minutes',0,240), ('late_wake_after_sunrise',0,720)]:
        require(type(value[key]) is int and low <= value[key] <= high)


def validate_configuration(config):
    keys(config, {'schema_version', 'rooms', 'loads', 'groups', 'profiles'} | ({'post_shutoff'} if 'post_shutoff' in config else set()))
    if 'post_shutoff' in config: require(type(config['post_shutoff']) is bool)
    require(type(config['schema_version']) is int and config['schema_version'] == 2)
    for field in ('rooms', 'loads', 'groups', 'profiles'):
        catalog(config[field])
    require(bool(config['rooms']) and bool(config['loads']))
    for label in config['rooms'].values():
        labels(label)
    physical = {}
    for load in config['loads'].values():
        keys(load, {'label', 'physical_id', 'owner', 'kind', 'capabilities'} | ({'display'} if 'display' in load else set()))
        if 'display' in load:
            display = load['display']
            keys(display, {'room', 'area_type', 'role'})
            require(display['room'] in config['rooms'], 'invalid_mapping')
            choice(display['area_type'], ('room', 'common', 'bathroom', 'hallway', 'legacy'))
            choice(display['role'], ('main_lights', 'night_lights', 'hvac'))
        labels(load['label'])
        identifier(load['physical_id'])
        identifier(load['owner'])
        choice(load['kind'], ('binary', 'hvac', 'hvac_power'))
        caps = load['capabilities']
        if load['kind'] in ('binary', 'hvac_power'):
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
        keys(group, {'label', 'track_only', 'rules'} | ({'activation'} if 'activation' in group else set()) | ({'include_preparation'} if 'include_preparation' in group else set()))
        if 'include_preparation' in group: require(type(group['include_preparation']) is bool and group.get('activation') == 'home')
        if 'activation' in group:
            choice(group['activation'], ('home',))
        labels(group['label'])
        require(type(group['track_only']) is bool)
        bounded_list(group['rules'], 50)
        seen = set()
        for rule in group['rules']:
            keys(rule, {'id', 'targets', 'start', 'end', 'action', 'release'} | ({'active_windows'} if 'active_windows' in rule else set()) | ({'warnings'} if 'warnings' in rule else set()) | ({'skip_empty'} if 'skip_empty' in rule else set()) | ({'external_release'} if 'external_release' in rule else set()))
            if 'external_release' in rule: require(type(rule['external_release']) is bool and rule['end'] is None and rule['release'] is None)
            if 'skip_empty' in rule: require(type(rule['skip_empty']) is bool)
            if 'active_windows' in rule:
                require(rule['end'] is not None)
                bounded_list(rule['active_windows'], 20)
                for window in rule['active_windows']:
                    keys(window, {'start', 'end'})
                    require(all(type(window[k]) is str and len(window[k]) <= 40 for k in ('start', 'end')))
            if 'warnings' in rule:
                bounded_list(rule['warnings'], 2)
                for warning in rule['warnings']: choice(warning, ('bathroom_daylight_fallback', 'bathroom_night_fallback', 'phase_empty', 'external_night_release'))
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
        require(type(profile) is dict)
        expected = {'label', 'room', 'purpose', 'groups'}
        keys(profile, expected | ({'window'} if 'window' in profile else set()) | ({'rest_defaults'} if 'rest_defaults' in profile else set()))
        if 'rest_defaults' in profile: validate_rest_defaults(profile['rest_defaults'])
        if 'window' in profile:
            keys(profile['window'], {'start', 'end'})
            for value in profile['window'].values():
                validate_time(value)
                require('at' in value or value['anchor'] in ('candle_lighting', 'sunrise'))
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
    keys(plan, {'schema_version', 'language', 'snapshot', 'availability', 'room_uses', 'meals', 'groups'} | ({'naps'} if 'naps' in plan else set()))
    require(type(plan['schema_version']) is int and plan['schema_version'] == 2)
    choice(plan['language'], ('en', 'he'))
    calendar = validate_calendar(plan['snapshot'])
    # Validate fixed timestamps even in currently unselected groups.
    for group in config['groups'].values():
        for rule in group['rules']:
            for time in (rule['start'], rule['end']):
                if time is not None and 'at' in time:
                    parse_instant(time['at'], calendar['zone'])
    for profile in config['profiles'].values():
        for time in profile.get('window', {}).values():
            if 'at' in time:
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
                               'group': group, 'use_start': start, 'use_end': end,
                               **({'hvac_end': parse_instant(item['hvac_end'], calendar['zone'])} if 'hvac_end' in item else {}),
                               **({'nap': item} if kind == 'nap' else {})})
        return start, end

    bounded_list(plan['room_uses'], 300)
    uses = []
    for use in plan['room_uses']:
        keys(use, {'id', 'room', 'purpose', 'control', 'profile', 'start', 'end', 'segment'} | ({'hvac_end'} if 'hvac_end' in use else set()))
        if 'hvac_end' in use:
            require(use['purpose'] == 'sleeping' and use['control'] == 'planner', 'invalid_mapping')
            wake = parse_instant(use['hvac_end'], calendar['zone'])
            require(use['segment'] in calendar['segments'], 'invalid_mapping')
            require(parse_instant(use['start'], calendar['zone']) < wake <= calendar['segments'][use['segment']]['end'], 'invalid_sequence')
            at_home(parse_instant(use['start'], calendar['zone']), max(wake, parse_instant(use['end'], calendar['zone'])))
        uses.append({k: v for k, v in use.items() if k not in ('segment','hvac_end')})
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
    naps = plan.get('naps', [])
    bounded_list(naps, 100)
    nap_ids = set()
    for nap in naps:
        keys(nap, {'id','room','profile','segment','start','end','lead_minutes','bathroom_targets'})
        identifier(nap['id']); require(nap['id'] not in nap_ids, 'invalid_mapping'); nap_ids.add(nap['id'])
        identifier(nap['room']); identifier(nap['profile'])
        require(nap['room'] in config['rooms'] and nap['profile'] in config['profiles'], 'invalid_mapping')
        profile = config['profiles'][nap['profile']]
        require(profile['room'] == nap['room'] and profile['purpose'] == 'sleeping', 'invalid_mapping')
        require(type(nap['lead_minutes']) is int and 0 <= nap['lead_minutes'] <= 240)
        references(nap['bathroom_targets'], config['loads'])
        allowed = {target for gid in profile['groups'] for rule in config['groups'][gid]['rules']
                   if rule['release'] is not None and rule['action'] == {'type':'state','state':'on'} for target in rule['targets']
                   if config['loads'][target].get('display', {}).get('room') not in (None, nap['room'])}
        require(set(nap['bathroom_targets']) <= allowed, 'invalid_mapping')
        a, b = selection(nap, profile['groups'], 'nap')
        seg = calendar['segments'][nap['segment']]
        require(seg['sunrise'] <= a < b <= seg['end'], 'invalid_sequence')
        lead = max(calendar['preparation_start'], a-timedelta(minutes=nap['lead_minutes']))
        at_home(lead,b)
        for use in plan['room_uses']:
            if use['room'] == nap['room'] and use['control'] == 'existing' and parse_instant(use['start'],calendar['zone']) < b and lead < parse_instant(use['end'],calendar['zone']):
                issues.append({'code':'room_overlap','room':nap['room'],'uses':sorted([nap['id'],use['id']])})
    for use in plan['room_uses']:
        if 'hvac_end' not in use: continue
        for other in plan['room_uses']:
            if other['room'] == use['room'] and other['control'] == 'existing' and parse_instant(other['start'],calendar['zone']) < parse_instant(use['hvac_end'],calendar['zone']) and parse_instant(use['start'],calendar['zone']) < parse_instant(other['end'],calendar['zone']):
                issues.append({'code':'room_overlap','room':use['room'],'uses':sorted([use['id'],other['id']])})
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
        require(config['groups'].get(item['group'], {}).get('activation') != 'home', 'invalid_mapping')
        selection(item, [item['group']], 'group')
    # Home policies follow explicit availability, never inferred occupancy.
    for gid, group in config['groups'].items():
        if group.get('activation') != 'home':
            continue
        for index, (start, end, state) in enumerate(availability):
            if state != 'home':
                continue
            for sid, seg in calendar['segments'].items():
                boundary = calendar['preparation_start'] if group.get('include_preparation') and seg['start'] == calendar['start'] else seg['start']
                a, b = max(start, boundary), min(end, seg['end'])
                if a < b:
                    selections.append({'id': 'home_' + str(index), 'kind': 'group', 'segment': sid,
                                       'group': gid, 'use_start': a, 'use_end': b})
    # Canonicalize unordered input collections, preserving ordered calendar segments.
    clean_config = json.loads(canonical(config))
    for load in clean_config['loads'].values():
        del load['label']
        load.pop('display', None)
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
    for segment in clean_plan['snapshot']['segments']:
        segment.pop('calendar_details', None)
    for field in ('room_uses', 'meals', 'groups', *(['naps'] if 'naps' in clean_plan else [])):
        clean_plan[field].sort(key=lambda v: v['id'])
    for nap in clean_plan.get('naps', []): nap['bathroom_targets'].sort()
    for meal in clean_plan['meals']:
        meal['groups'].sort()
    result = {'preview_only': True, 'complete': not issues, 'issues': issues,
              'digest': digest({'compiler': 'generic-v2.6', 'config': clean_config, 'plan': clean_plan}),
              'events': [], 'warnings': []}
    if issues:
        result['issues'] = sorted(issues, key=canonical)
        return result
    entertaining = {}
    for sid, seg in calendar['segments'].items():
        windows = [u for u in plan['room_uses'] if u['segment']==sid and u['purpose']=='recreation'] + [m for m in plan['meals'] if m['segment']==sid and m['kind']=='evening' and m['choice'] in ('family','hosting')]
        ends = [parse_instant(v['end'],calendar['zone']) for v in windows if parse_instant(v['start'],calendar['zone']) < seg['sunrise']]
        entertaining[sid] = max(ends) if ends else seg['candle_lighting']+timedelta(minutes=360)
    demands, tracked = defaultdict(list), []
    count = 0

    def resolve(time, selection, clamp=False):
        if 'at' in time:
            instant = parse_instant(time['at'], calendar['zone'])
        else:
            anchors = {**calendar['segments'][selection['segment']], **selection, 'entertaining_end':entertaining[selection['segment']]}
            try:
                instant = anchors[time['anchor']] + timedelta(minutes=time['offset_minutes'])
            except OverflowError:
                raise PlanError('invalid_time') from None
        if time.get('not_before') == 'preparation_start':
            instant = max(instant, calendar['preparation_start'])
        if clamp: instant = max(calendar['preparation_start'], min(instant, calendar['end']))
        require(calendar['preparation_start'] <= instant <= calendar['end'], 'invalid_sequence')
        return instant

    for selected in sorted(selections, key=lambda v: (v['kind'], v['id'], v['segment'], v['group'])):
        group = config['groups'][selected['group']]
        for original_rule in group['rules']:
            rule = original_rule
            hvac_rule = rule['action']['type'] in ('hvac','hvac_power')
            if 'nap' in selected:
                nap = selected['nap']
                if rule['release'] is None or (hvac_rule and rule['action'].get('state', rule['action'].get('mode')) == 'off'): continue
                targets = rule['targets'] if hvac_rule else [t for t in rule['targets'] if t in nap['bathroom_targets'] and rule['action'] == {'type':'state','state':'on'}]
                if not targets: continue
                rule = {**rule, 'targets':targets, 'start':{'anchor':'use_start','offset_minutes':-nap['lead_minutes'] if hvac_rule else 0,'not_before':'preparation_start'}, 'end':{'anchor':'use_end','offset_minutes':0}, 'release':rule['release']}
            effective = {**selected, 'use_end':selected['hvac_end']} if hvac_rule and 'hvac_end' in selected else selected
            start = resolve(rule['start'], effective, rule.get('skip_empty', False))
            end = resolve(rule['end'], effective, rule.get('skip_empty', False)) if rule['end'] is not None else None
            if hvac_rule and 'hvac_end' in selected and end is not None and rule['action'].get('state', rule['action'].get('mode')) != 'off':
                end = selected['hvac_end']
            if group.get('activation')=='home':
                if end is None and not selected['use_start'] <= start < selected['use_end']: continue
                if end is not None:
                    start, end = max(start,selected['use_start']), min(end,selected['use_end'])
            if rule.get('skip_empty') and end is not None and start >= end:
                entry = {'code': 'phase_empty', 'group': selected['group']}
                if entry not in result['warnings']: result['warnings'].append(entry)
                continue
            require(start < calendar['end'] and (end is None or start < end), 'invalid_sequence')
            reason = {k: selected[k] for k in ('id', 'kind', 'segment', 'group')}
            reason['rule'] = rule['id']
            if hvac_rule and 'hvac_end' in selected: reason['kind'] = 'overnight_hvac'
            for warning in rule.get('warnings', []):
                entry = {'code': warning, 'group': selected['group']}
                if entry not in result['warnings']: result['warnings'].append(entry)
            windows = [(start, end)]
            if 'active_windows' in rule:
                windows = []
                for window in rule['active_windows']:
                    a, b = (parse_instant(window[k], calendar['zone']) for k in ('start', 'end'))
                    require(calendar['preparation_start'] <= a < b <= calendar['end'], 'invalid_sequence')
                    left, right = max(start, a), min(end, b)
                    if left < right: windows.append((left, right))
            for left, right in windows:
                for target in rule['targets']:
                    count += 1
                    require(count <= MAX_EXPANDED)
                    physical = config['loads'][target]['physical_id']
                    demand = {'start': left, 'end': right, 'action': rule['action'],
                              'release': rule['release'], 'reason': reason, 'repeat':rule.get('external_release',False)}
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
            ending = [v for v in items if v['end'] == when and (when != calendar['end'] or config.get('post_shutoff', True))]
            wanted = [(v['action'], v['reason']) for v in active + points]
            if not wanted:
                wanted = [(v['release'], v['reason']) for v in ending]
            if not wanted: continue
            actions = {canonical(action) for action, _ in wanted}
            require(len(actions) == 1, 'event_conflict')
            action = wanted[0][0]
            if action != last or any(v.get('repeat') for v in points):
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
        if item['end'] is not None and (item['end'] != calendar['end'] or config.get('post_shutoff', True)):
            result['events'].append(event(physical, item['end'], item['release'], [item['reason']], 'track_only'))
    result['events'] = sorted({v['id']: v for v in result['events']}.values(), key=lambda v: (v['utc'], v['physical_id'], v['id']))
    return result
