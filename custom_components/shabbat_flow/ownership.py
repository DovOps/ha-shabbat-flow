"""Read-only, deliberately bounded automation forecasts and ownership diagnostics."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from .engine.schedule import digest


def instant(value):
    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('invalid_time')
    return value.astimezone(timezone.utc)


def automation_sources(hass):
    """Same raw_config source used by HA's admin automation/config websocket.

    Internal access is guarded; absent/changed access is unresolved, never empty-safe.
    """
    component = hass.data.get('automation')
    result = []
    for state in hass.states.async_all('automation'):
        entity = component.get_entity(state.entity_id) if hasattr(component, 'get_entity') else None
        raw = getattr(entity, 'raw_config', None)
        result.append({'id': state.entity_id, 'enabled': state.state == 'on',
                       'config': raw if isinstance(raw, dict) else None,
                       'name': state.attributes.get('friendly_name') or (raw or {}).get('alias') or state.entity_id,
                       'available': state.state in ('on', 'off')})
    return result, component is not None


def seconds(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = int(value)
    elif isinstance(value, str):
        sign = -1 if value.startswith('-') else 1
        parts = value.lstrip('+-').split(':')
        if len(parts) != 3: raise ValueError('unresolved_delay')
        result = sign * sum(int(v) * f for v, f in zip(parts, (3600, 60, 1)))
    elif isinstance(value, dict) and set(value) <= {'hours', 'minutes', 'seconds'}:
        result = sum(int(value.get(k, 0)) * f for k, f in [('hours', 3600), ('minutes', 60), ('seconds', 1)])
    else: raise ValueError('unresolved_delay')
    if abs(result) > 86400: raise ValueError('unresolved_delay')
    return result


def scheduled_trigger(trigger, calendar_entities):
    if not isinstance(trigger, dict) or trigger.get('enabled') is False: return False
    kind = trigger.get('trigger', trigger.get('platform'))
    if kind in ('time', 'sun', 'time_pattern'): return True
    ids = trigger.get('entity_id', [])
    ids = ids if isinstance(ids, list) else [ids]
    return kind in ('state', 'calendar') and any(e in calendar_entities for e in ids)


def forecast(snapshot, sources, accessible=True, solar=None, source_timezone=None, resolve_target=None, calendar_entities=None):
    start, end = instant(snapshot['preparation_start']), instant(snapshot['end'])
    zone = ZoneInfo(source_timezone or snapshot['timezone'])
    events, unresolved, fingerprints, excluded = [], [], {}, []
    calendar_entities = calendar_entities or {}
    trusted_calendar = snapshot.get('source', {}).get('id') == 'jewish_calendar'
    def active_at(at): return instant(snapshot['start']) <= at < end
    if not accessible: unresolved.append({'source': 'automation', 'reason': 'source_unavailable'})
    for source in sources:
        sid, raw = source['id'], source['config']
        fingerprints[sid] = digest({'enabled': source['enabled'], 'config': raw, 'available': source.get('available', True)})
        triggers = (raw or {}).get('triggers', (raw or {}).get('trigger', []))
        if isinstance(triggers, dict): triggers = [triggers]
        if raw and triggers and not any(scheduled_trigger(t, calendar_entities) for t in triggers):
            excluded.append({'source':sid,'reason':'outside_forecast_scope'}); continue
        if not source.get('available', True):
            unresolved.append({'source': sid, 'reason': 'source_unavailable'}); continue
        if not source['enabled']: continue
        try:
            if not raw: raise ValueError('source_unavailable')
            conditions = raw.get('conditions', raw.get('condition', []))
            if isinstance(conditions, dict): conditions = [conditions]
            weekdays = set(range(7)); calendar_conditions = []
            for c in conditions:
                if c.get('enabled') is False: continue
                if c.get('condition') == 'state' and calendar_entities.get(c.get('entity_id')) == 'issur_melacha_in_effect' and trusted_calendar:
                    if set(c)-{'condition','entity_id','state','alias','enabled'} or c.get('state') not in ('on','off'): raise ValueError('unresolved_condition')
                    calendar_conditions.append(c['state']); continue
                if c.get('condition') != 'time' or set(c) - {'condition', 'weekday', 'alias', 'enabled'} or c.get('enabled') is False:
                    raise ValueError('unresolved_condition')
                days = c.get('weekday', [])
                if isinstance(days, str): days = [days]
                if days: weekdays &= {['mon','tue','wed','thu','fri','sat','sun'].index(d) for d in days}
            triggers = raw.get('triggers', raw.get('trigger', []))
            if isinstance(triggers, dict): triggers = [triggers]
            if not triggers: raise ValueError('unresolved_trigger')
            times = []
            for trigger in triggers:
                kind = trigger.get('trigger', trigger.get('platform'))
                if trigger.get('enabled') is False: continue
                if kind == 'time':
                    if set(trigger) - {'trigger','platform','at','id','alias','enabled'}: raise ValueError('unresolved_trigger')
                    ats = trigger.get('at'); ats = ats if isinstance(ats, list) else [ats]
                    for at in ats:
                        if not isinstance(at, str): raise ValueError('unresolved_trigger')
                        parts = at.split(':')
                        if len(parts) not in (2, 3): raise ValueError('unresolved_trigger')
                        h, m = int(parts[0]), int(parts[1]); sec = int(parts[2]) if len(parts) == 3 else 0
                        day = start.astimezone(zone).date() - timedelta(days=1)
                        while day <= end.astimezone(zone).date():
                            naive = datetime.combine(day, datetime.min.time()).replace(hour=h, minute=m, second=sec)
                            candidates = {naive.replace(tzinfo=zone, fold=f).astimezone(timezone.utc) for f in (0, 1)
                                          if naive.replace(tzinfo=zone, fold=f).astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == naive}
                            if len(candidates) != 1: raise ValueError('ambiguous_time')
                            times.extend(candidates); day += timedelta(days=1)
                elif kind == 'sun':
                    if set(trigger) - {'trigger','platform','event','offset','id','alias','enabled'}: raise ValueError('unresolved_trigger')
                    anchor = trigger.get('event')
                    if anchor not in ('sunrise', 'sunset'): raise ValueError('unresolved_trigger')
                    anchors = solar.get(anchor, []) if solar is not None else [seg.get(anchor) for seg in snapshot['segments']]
                    if not anchors or not all(anchors): raise ValueError('missing_sun_anchor')
                    times += [instant(a) + timedelta(seconds=seconds(trigger.get('offset', 0))) for a in anchors]
                    # Snapshot supplies one morning/evening per segment, not every preparation-day sun event.
                    if solar is None: unresolved.append({'source': sid, 'reason': 'partial_sun_coverage'})
                elif kind == 'state' and trusted_calendar and calendar_entities.get(trigger.get('entity_id') if isinstance(trigger.get('entity_id'),str) else None) == 'issur_melacha_in_effect':
                    if set(trigger)-{'trigger','platform','entity_id','from','to','id','alias','enabled'} or trigger.get('to') not in ('on','off') or trigger.get('from') not in (None,'on','off'): raise ValueError('unresolved_trigger')
                    if trigger.get('from') != trigger['to']: times.append(instant(snapshot['start']) if trigger['to']=='on' else end)
                elif not scheduled_trigger(trigger, calendar_entities):
                    continue  # Reactive triggers do not predict dated events.
                else: raise ValueError('unresolved_trigger')
            actions = raw.get('actions', raw.get('action', []))
            if isinstance(actions, dict): actions = [actions]
            if not actions or len(actions) > 100: raise ValueError('unresolved_action')
            parsed, delay = [], 0
            for action in actions:
                if set(action) <= {'delay','alias'} and 'delay' in action:
                    delta = seconds(action['delay'])
                    if delta < 0: raise ValueError('unresolved_delay')
                    delay += delta
                    if delay > 86400: raise ValueError('unresolved_delay')
                    continue
                if set(action) - {'action','service','target','data','alias','metadata'} or not isinstance(action.get('metadata', {}), dict):
                    raise ValueError('unresolved_action')
                service = action.get('action', action.get('service', ''))
                if service not in {f'{d}.turn_{s}' for d in ('light','switch','climate') for s in ('on','off')}:
                    raise ValueError('unresolved_action')
                target = action.get('target', {}); data = action.get('data', {})
                if set(target) - {'entity_id','label_id','area_id','device_id'} or set(data) - {'entity_id'}: raise ValueError('unresolved_target')
                selection = {**data, **target}
                for value in selection.values():
                    values = value if isinstance(value, list) else [value]
                    if not values or any(not isinstance(v, str) or not v or any(c in v for c in '{}%') or v in ('all','none') for v in values):
                        raise ValueError('unresolved_target')
                if set(selection) - {'entity_id'}:
                    if resolve_target is None: raise ValueError('unresolved_target')
                    ids = resolve_target(selection, service.split('.')[0])
                else:
                    ids = selection.get('entity_id', []); ids = ids if isinstance(ids, list) else [ids]
                if not ids or any(not isinstance(e, str) or '{{' in e or e.split('.')[0] != service.split('.')[0] for e in ids):
                    raise ValueError('unresolved_target')
                parsed += [(delay, e, service.rsplit('_', 1)[1]) for e in ids]
            fingerprints[sid] = digest({'source': fingerprints[sid], 'resolved_actions': parsed})
            pending = []
            for when in sorted(set(times)):
                if when.astimezone(zone).weekday() not in weekdays: continue
                if any(active_at(when) != (state=='on') for state in calendar_conditions): continue
                for offset, entity, state in parsed:
                    at = when + timedelta(seconds=offset)
                    if start <= at <= end:
                        event = {'source': sid, 'source_name': source.get('name') or raw.get('alias') or sid, 'entity_id': entity, 'utc': at.isoformat(), 'local': at.astimezone(zone).isoformat(),
                                 'action': {'type':'state','state':state}, 'unmanaged': True, 'source_hash': fingerprints[sid]}
                        event['id'] = digest({k:v for k,v in event.items() if k!='source_name'})[:20]; pending.append(event)
            if len(events) + len(pending) > 5000: raise ValueError('forecast_limit')
            events.extend(pending)
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
            reason=str(exc) if str(exc) in {'source_unavailable','unresolved_condition','unresolved_trigger','missing_sun_anchor','unresolved_action','unresolved_target','unresolved_delay','ambiguous_time','forecast_limit'} else 'unsupported_or_unresolved'
            unresolved.append({'source':sid, 'source_name':source.get('name') or (raw or {}).get('alias') or sid, 'reason':reason})
    return {'events': sorted({e['id']:e for e in events}.values(), key=lambda e:(e['utc'],e['id'])),
            'unresolved': unresolved, 'excluded': excluded, 'fingerprints': fingerprints, 'forecast_only': True}


def ownership_report(events, mapping, overlay):
    """Conservative interval conflicts; never a live ownership clearance."""
    conflicts = []
    for external in overlay['events']:
        for physical, target in mapping.items():
            if external['entity_id'] != target['entity_id']: continue
            previous = [e for e in events if e['physical_id'] == physical and instant(e['utc']) <= instant(external['utc']) and e['intent'] != 'track_only']
            if not previous: continue
            action = previous[-1]['action']; state = action.get('state', 'off' if action.get('mode') == 'off' else 'on')
            conflicts.append({'physical_id':physical, 'external_event':external['id'], 'source':external['source'],
                              'kind':'same_state_overlap' if state == external['action']['state'] else 'contradictory_state'})
    return {'conflicts':conflicts, 'unresolved':overlay['unresolved'] + overlay.get('excluded', []), 'live_clearance':False,
            'reason':'observe_only_no_ownership_granted'}


def forecast_ha(hass, snapshot):
    # Forecast HA sun triggers using HA's own location/elevation helper, not a
    # guessed candle offset or the Jewish Calendar's potentially different location.
    from homeassistant.helpers.sun import get_astral_event_date
    sources, accessible = automation_sources(hass)
    zone = ZoneInfo(hass.config.time_zone)
    solar = {'sunrise': [], 'sunset': []}
    day = instant(snapshot['preparation_start']).astimezone(zone).date() - timedelta(days=2)
    final = instant(snapshot['end']).astimezone(zone).date() + timedelta(days=1)
    for _ in range(10):
        if day > final: break
        for anchor in solar:
            try: value = get_astral_event_date(hass, anchor, day)
            except (ValueError, ImportError): value = None
            solar[anchor].append(value.isoformat() if value else None)
        day += timedelta(days=1)
    from homeassistant.helpers.target import TargetSelection, async_extract_referenced_entity_ids

    def resolve_target(selection, domain):
        selected = async_extract_referenced_entity_ids(hass, TargetSelection(selection))
        if any(getattr(selected, key, set()) for key in ('missing_devices','missing_areas','missing_labels')):
            raise ValueError('unresolved_target')
        return sorted(e for e in selected.referenced | selected.indirectly_referenced if e.startswith(domain + '.'))

    from homeassistant.helpers import entity_registry as er
    registry=er.async_get(hass)
    calendar_entries=hass.config_entries.async_entries('jewish_calendar')
    calendar_entities={e.entity_id:e.translation_key for e in registry.entities.values() if e.platform=='jewish_calendar' and e.disabled_by is None}
    # Only one provider can safely match the snapshot's provider provenance.
    if len(calendar_entries)!=1:
        calendar_entities={eid:'unresolved_provider' for eid in calendar_entities}
    result = forecast(snapshot, sources, accessible, solar, hass.config.time_zone, resolve_target, calendar_entities)
    for event in result['events']:
        entity=registry.async_get(event['entity_id']);state=hass.states.get(event['entity_id']);attrs=state.attributes if state else {}
        event['entity_name']=(entity.name if entity else None) or attrs.get('friendly_name') or (entity.original_name if entity else None) or event['entity_id']
        event['entity_icon']=(entity.icon if entity else None) or attrs.get('icon') or (entity.original_icon if entity else None)
    result['source_timezone'] = hass.config.time_zone
    result['sun_source'] = 'home_assistant_sun_helper'
    result['fingerprints']['sun_configuration'] = digest([hass.config.time_zone,hass.config.latitude,hass.config.longitude,hass.config.elevation])
    return result
