"""Read-only Jewish Calendar event adapter. No astronomical calculations."""
from asyncio import timeout
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.exceptions import HomeAssistantError
from .engine.compiler import PlanError, require
from .engine.planning import validate_calendar


def instant(value):
    result = datetime.fromisoformat(value) if isinstance(value, str) else value
    require(isinstance(result, datetime) and result.tzinfo is not None and result.utcoffset() is not None, 'calendar_incomplete')
    return result.replace(microsecond=0)


def assemble(yearly, daily, zone_name, diaspora, now):
    """Select next whole period; daily candles are planning transition anchors."""
    zone = ZoneInfo(zone_name)
    require(type(diaspora) is bool, 'calendar_incomplete')
    require(len(yearly) <= 1000 and len(daily) <= 1000, 'calendar_incomplete')
    def times(events, summary):
        values = [instant(e['start']).astimezone(zone) for e in events if e.get('summary') == summary]
        require(len(values) == len(set(values)), 'calendar_incomplete')
        return sorted(values)
    candles, ends, rises = times(yearly, 'Candle Lighting'), times(yearly, 'Havdalah'), times(daily, 'Netz Hachama')
    require(candles and ends, 'calendar_incomplete')
    # Group all supplied candles up to each final Havdalah, including any ongoing period.
    previous_end = None
    for end in ends:
        group = [c for c in candles if (previous_end is None or c > previous_end) and c < end]
        previous_end = end
        if not group or group[0] <= now:
            continue
        first = group[0]
        days = (end.date() - first.date()).days
        require(1 <= days <= 3 and len(group) == days, 'calendar_incomplete')
        segments = []
        for i, candle in enumerate(group):
            require(candle.date() == first.date() + timedelta(days=i), 'calendar_incomplete')
            morning = candle.date() + timedelta(days=1)
            matches = [r for r in rises if r.date() == morning]
            require(len(matches) == 1, 'calendar_incomplete')
            sunsets = []
            for event in daily:
                if event.get('summary') == 'Shkia':
                    try:
                        value = instant(event['start']).astimezone(zone)
                        if value.date() == morning and value > matches[0]: sunsets.append(value)
                    except (ValueError, TypeError, KeyError, PlanError):
                        pass
            boundary = group[i+1] if i+1 < days else end
            segments.append({'id': f'day_{i+1}', 'kind': 'shabbat' if morning.weekday() == 5 else 'yom_tov',
                             'start': candle.isoformat(), 'end': boundary.isoformat(),
                             'candle_lighting': candle.isoformat(), 'sunrise': matches[0].isoformat()})
            details = sorted({e['summary'] for e in daily + yearly if str(e.get('start')) == morning.isoformat() and isinstance(e.get('summary'), str) and 0 < len(e['summary']) <= 240})
            if details: segments[-1]['calendar_details'] = details[:20]
            if len(sunsets) == 1: segments[-1]['sunset'] = sunsets[0].isoformat()
        snapshot = {'schema_version': 2, 'period_id': 'observance_' + first.strftime('%Y%m%d'),
                    'timezone': zone_name, 'observance': 'diaspora' if diaspora else 'israel',
                    'source': {'id': 'jewish_calendar', 'version': 'calendar_events_v1'},
                    'preparation_start': (first-timedelta(minutes=30)).isoformat(),
                    'start': first.isoformat(), 'end': end.isoformat(), 'segments': segments}
        validate_calendar(snapshot)
        return snapshot
    raise PlanError('calendar_no_upcoming')


async def upcoming(hass, now=None):
    now = now or datetime.now(timezone.utc)
    entries = hass.config_entries.async_entries('jewish_calendar')
    require(len(entries) == 1, 'calendar_ambiguous' if entries else 'calendar_missing')
    provider = entries[0]
    zone_name = provider.data.get('time_zone', hass.config.time_zone)
    diaspora = provider.data.get('diaspora', False)
    registry = er.async_get(hass)
    ids = {}
    for key in ('daily_events', 'yearly_events'):
        candidates = [e for e in registry.entities.values() if e.platform == 'jewish_calendar'
                      and e.config_entry_id == provider.entry_id and e.entity_id.startswith('calendar.')
                      and e.translation_key == key and e.disabled_by is None]
        require(len(candidates) == 1, 'calendar_ambiguous' if len(candidates)>1 else 'calendar_missing')
        eid = candidates[0].entity_id
        state = hass.states.get(eid)
        require(state is not None and state.state not in ('unavailable', 'unknown'), 'calendar_unavailable')
        ids[key] = eid
    try:
        async with timeout(15):
            response = await hass.services.async_call('calendar', 'get_events',
                {'entity_id': list(ids.values()), 'start_date_time': (now-timedelta(days=4)).isoformat(),
                 'end_date_time': (now+timedelta(days=14)).isoformat()}, blocking=True, return_response=True)
        snapshot = assemble(response[ids['yearly_events']]['events'], response[ids['daily_events']]['events'], zone_name, diaspora, now)
    except (HomeAssistantError, TimeoutError):
        raise PlanError('calendar_unavailable') from None
    except (ValueError, TypeError, KeyError, OverflowError):
        raise PlanError('calendar_incomplete') from None
    return {'status': 'ready', 'source': 'jewish_calendar', 'observed_at': now.isoformat(), 'snapshot': snapshot}
