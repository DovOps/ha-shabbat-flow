"""Internal v2 foundation: supplied calendar and room-use validation only.

No calendar calculation, schedule generation, network, storage or device control.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .compiler import PlanError, identifier, keys, parse_instant, require

PURPOSES = ('sleeping', 'recreation', 'other')


def choice(value, allowed):
    require(type(value) is str and value in allowed)


def bounded_list(value, maximum):
    require(type(value) is list and len(value) <= maximum)


def validate_calendar(snapshot):
    """Validate 1–3 contiguous supplied segments; return parsed UTC anchors.

    Candle lighting and segment boundaries deliberately remain separate.
    Values are supplied by a future provider, not calculated here.
    """
    keys(snapshot, {'schema_version', 'period_id', 'timezone', 'observance',
                    'source', 'preparation_start', 'start', 'end', 'segments'})
    require(type(snapshot['schema_version']) is int and snapshot['schema_version'] == 2)
    identifier(snapshot['period_id'])
    choice(snapshot['observance'], ('israel', 'diaspora'))
    keys(snapshot['source'], {'id', 'version'})
    for value in snapshot['source'].values():
        require(type(value) is str and 0 < len(value.strip()) <= 100)
    require(type(snapshot['timezone']) is str and len(snapshot['timezone']) <= 100,
            'invalid_timezone')
    try:
        zone = ZoneInfo(snapshot['timezone'])
    except (ZoneInfoNotFoundError, ValueError):
        raise PlanError('invalid_timezone') from None
    preparation, start, end = (parse_instant(snapshot[k], zone)
                               for k in ('preparation_start', 'start', 'end'))
    require(preparation <= start < end, 'invalid_sequence')
    require(start - preparation <= timedelta(days=1)
            and end - start <= timedelta(days=4), 'unsupported_period')
    bounded_list(snapshot['segments'], 3)
    require(bool(snapshot['segments']), 'unsupported_period')
    segments = {}
    cursor = start
    prior_sunrise = None
    prior_candle = None
    for segment in snapshot['segments']:
        keys(segment, {'id', 'kind', 'start', 'end', 'candle_lighting', 'sunrise'} | ({'sunset'} if 'sunset' in segment else set()) | ({'calendar_details'} if 'calendar_details' in segment else set()))
        if 'calendar_details' in segment:
            bounded_list(segment['calendar_details'], 20)
            require(all(type(v) is str and 0 < len(v) <= 240 for v in segment['calendar_details']))
        identifier(segment['id'])
        require(segment['id'] not in segments, 'invalid_mapping')
        choice(segment['kind'], ('shabbat', 'yom_tov'))
        parsed = {k: parse_instant(segment[k], zone)
                  for k in ('start', 'end', 'candle_lighting', 'sunrise')}
        require(parsed['start'] == cursor and cursor < parsed['end'] <= end,
                'invalid_sequence')
        require(preparation <= parsed['candle_lighting'] < parsed['sunrise']
                and cursor < parsed['sunrise'] < parsed['end'], 'invalid_sequence')
        if segment.get('sunset') is not None:
            parsed['sunset'] = parse_instant(segment['sunset'], zone)
            require(parsed['sunrise'] < parsed['sunset'] and parsed['sunrise'].astimezone(zone).date() == parsed['sunset'].astimezone(zone).date(), 'invalid_sequence')
        if prior_sunrise is not None:
            require(parsed['sunrise'].astimezone(zone).date()
                    == prior_sunrise.astimezone(zone).date() + timedelta(days=1),
                    'invalid_sequence')
            require(parsed['candle_lighting'] > prior_sunrise
                    and parsed['candle_lighting'] > prior_candle, 'invalid_sequence')
        segments[segment['id']] = parsed
        cursor = parsed['end']
        prior_sunrise, prior_candle = parsed['sunrise'], parsed['candle_lighting']
    require(cursor == end, 'invalid_sequence')
    return {'zone': zone, 'preparation_start': preparation,
            'start': start, 'end': end, 'segments': segments}


def validate_room_uses(snapshot, uses, room_ids, profiles):
    """Return possible overlap conflicts, never resolve them by list order.

    profiles maps profile IDs to purposes; timing/capability validation belongs
    to the forthcoming profile compiler. Existing-control uses have no profile.
    Intervals are half-open, allowing a room to change purpose at a boundary.
    """
    calendar = validate_calendar(snapshot)
    bounded_list(room_ids, 100)
    require(len(room_ids) > 0)
    for room_id in room_ids:
        identifier(room_id)
    require(len(set(room_ids)) == len(room_ids), 'invalid_mapping')
    require(type(profiles) is dict and len(profiles) <= 100)
    for profile_id, purpose in profiles.items():
        identifier(profile_id)
        choice(purpose, PURPOSES)
    bounded_list(uses, 300)
    parsed_uses = []
    seen = set()
    for use in uses:
        keys(use, {'id', 'room', 'purpose', 'control', 'profile', 'start', 'end'})
        identifier(use['id'])
        require(use['id'] not in seen, 'invalid_mapping')
        seen.add(use['id'])
        require(type(use['room']) is str and use['room'] in room_ids, 'invalid_mapping')
        choice(use['purpose'], PURPOSES)
        choice(use['control'], ('planner', 'existing'))
        if use['control'] == 'existing':
            require(use['profile'] is None, 'invalid_mapping')
        else:
            require(type(use['profile']) is str
                    and profiles.get(use['profile']) == use['purpose'], 'invalid_mapping')
        start, end = (parse_instant(use[k], calendar['zone']) for k in ('start', 'end'))
        require(calendar['preparation_start'] <= start < end <= calendar['end'],
                'invalid_sequence')
        parsed_uses.append((use['room'], start, end, use['id']))
    conflicts = []
    ordered = sorted(parsed_uses)
    for i, (room, start, end, use_id) in enumerate(ordered):
        for other_room, other_start, other_end, other_id in ordered[i + 1:]:
            if room != other_room or other_start >= end:
                break
            conflicts.append({'room': room, 'uses': sorted([use_id, other_id]),
                              'start': max(start, other_start).isoformat(),
                              'end': min(end, other_end).isoformat()})
    return {'overlap_conflicts': sorted(conflicts, key=lambda v: (v['room'], v['uses'])),
            'room_use_count': len(uses)}
