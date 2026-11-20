"""Opt-in, same-local-day pre-candle push reminders. No plan activation."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from homeassistant.helpers import entity_registry as er
from .engine.schedule import digest


def status(hass):
    entries=hass.config_entries.async_entries('jewish_calendar')
    if len(entries)!=1:return {'available':False,'issur_off':False}
    entities=[e for e in er.async_get(hass).entities.values() if e.platform=='jewish_calendar' and e.config_entry_id==entries[0].entry_id and e.disabled_by is None]
    def matches(key):return [e for e in entities if e.translation_key==key]
    signals=matches('issur_melacha_in_effect')
    state=hass.states.get(signals[0].entity_id) if len(signals)==1 else None
    available=len(signals)==1 and all(len(matches(k))==1 for k in ('daily_events','yearly_events')) and hass.services.has_service('calendar','get_events')
    return {'available':available,'issur_off':bool(state and state.state=='off')}


def allowed(hass,event,now):
    try:
        candle=datetime.fromisoformat(event['candle']);due=datetime.fromisoformat(event['due']);zone=ZoneInfo(event['timezone'])
        return status(hass)['issur_off'] and due<=now<candle and (now-due).total_seconds()<=120 and now.astimezone(zone).date()==candle.astimezone(zone).date()
    except (KeyError,TypeError,ValueError):return False


async def tick(notifier,now):
    if notifier.closed or notifier.error or not notifier.data['settings']['reminder_enabled']:return
    hass=notifier.hass
    state=status(hass)
    if not state['available'] or not state['issur_off']:return
    # Date discovery is throttled independently of the minute due-time check.
    if notifier.calendar_checked is None or (now-notifier.calendar_checked).total_seconds()>=900:
        notifier.calendar_checked=now;notifier.calendar_snapshot=None
        try:
            from .upcoming import upcoming
            notifier.calendar_snapshot=(await upcoming(hass,now))['snapshot']
        except Exception:return
    snapshot=notifier.calendar_snapshot
    if not snapshot:return
    candle=datetime.fromisoformat(snapshot['start'])
    async with notifier.lock:
        data=deepcopy(notifier.data);cfg=data['settings'];changed=False
        if not cfg['reminder_enabled']:return
        for minutes in cfg['reminder_offsets']:
            due=candle-timedelta(minutes=minutes)
            rid=digest({'candle':candle.isoformat(),'offset':minutes})[:32];key=rid+':reminder:push'
            event={'key':key,'run_id':rid,'kind':'reminder','event':'reminder','channel':'push','status':'pending','revision':data['revision'],'at':now.isoformat(),'candle':candle.isoformat(),'due':due.isoformat(),'timezone':snapshot['timezone']}
            if allowed(hass,event,now) and not any(e['key']==key for e in data['events']):data['events'].append(event);changed=True
        if changed:
            data['events']=data['events'][-500:];await notifier.save(data)
    notifier.kick()
