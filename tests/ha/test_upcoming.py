"""Calendar source tests: fictional provider settings, no household exports."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import pytest
from homeassistant.helpers import entity_registry as er
from custom_components.shabbat_flow.upcoming import assemble, upcoming
from custom_components.shabbat_flow.api import UpcomingView
from custom_components.shabbat_flow.engine.compiler import PlanError
from test_integration import host, Request, decoded


def event(name, time): return {'summary': name, 'start': time}


def fixtures(days=1):
    start=datetime(2027,1,7,16,tzinfo=timezone.utc)
    candles=[start+timedelta(days=i) for i in range(days)]
    end=start+timedelta(days=days,hours=2)
    yearly=[event('Candle Lighting',c.isoformat()) for c in candles]+[event('Havdalah',end.isoformat())]
    daily=[event('Netz Hachama',(c+timedelta(hours=14)).isoformat()) for c in candles]
    return yearly,daily,start-timedelta(days=1)


@pytest.mark.parametrize('days',[1,2,3])
@pytest.mark.parametrize('diaspora',[True,False])
def test_complete_periods(days,diaspora):
    yearly,daily,now=fixtures(days)
    snap=assemble(yearly,daily,'Europe/London',diaspora,now)
    assert len(snap['segments'])==days
    assert snap['observance']==('diaspora' if diaspora else 'israel')
    assert snap['segments'][0]['sunrise'].startswith('2027-01-08')
    if days>1:
        assert snap['segments'][1]['kind']=='shabbat'
        assert snap['segments'][0]['end']==snap['segments'][1]['start']


@pytest.mark.parametrize('fault',['sunrise','duplicate','gap','no_end','naive'])
def test_missing_or_ambiguous_coverage(fault):
    yearly,daily,now=fixtures(3)
    if fault=='sunrise':daily.pop()
    if fault=='duplicate':daily.append(daily[0])
    if fault=='gap':yearly.pop(1)
    if fault=='no_end':yearly.pop()
    if fault=='naive':daily[0]['start']='2027-01-08T06:00:00'
    with pytest.raises(PlanError):assemble(yearly,daily,'Europe/London',False,now)


def test_rollover_skips_started_whole_period():
    y,d,n=fixtures(2)
    y2=[{**e,'start':(datetime.fromisoformat(e['start'])+timedelta(days=7)).isoformat()} for e in y]
    d2=[{**e,'start':(datetime.fromisoformat(e['start'])+timedelta(days=7)).isoformat()} for e in d]
    result=assemble(y+y2,d+d2,'Europe/London',True,n+timedelta(days=2))
    assert result['start'].startswith('2027-01-14')


def test_dst_uses_source_offsets():
    y=[event('Candle Lighting','2027-03-26T17:00:00+00:00'),event('Candle Lighting','2027-03-27T18:00:00+00:00'),event('Candle Lighting','2027-03-28T19:00:00+01:00'),event('Havdalah','2027-03-29T20:00:00+01:00')]
    d=[event('Netz Hachama','2027-03-27T06:00:00+00:00'),event('Netz Hachama','2027-03-28T06:00:00+01:00'),event('Netz Hachama','2027-03-29T06:00:00+01:00')]
    result=assemble(y,d,'Europe/London',False,datetime(2027,3,25,tzinfo=timezone.utc))
    rises=[datetime.fromisoformat(s['sunrise']) for s in result['segments']]
    assert result['segments'][1]['sunrise']=='2027-03-28T06:00:00+01:00'
    assert rises[1]-rises[0]==timedelta(hours=23)


@pytest.mark.asyncio
async def test_adapter_discovery_auth_and_failures(host,monkeypatch):
    hass,entry=host
    provider=SimpleNamespace(domain='jewish_calendar',pref_disable_new_entities=False,disabled_by=None,entry_id='calendar_fixture',data={'time_zone':'Europe/London','diaspora':True})
    hass.config_entries.async_entries=Mock(return_value=[provider])
    hass.config_entries.async_get_entry=Mock(return_value=provider)
    registry=er.async_get(hass)
    ids={}
    for key in ['daily_events','yearly_events']:
        e=registry.async_get_or_create('calendar','jewish_calendar',key,config_entry=provider,translation_key=key)
        ids[key]=e.entity_id;hass.states.async_set(e.entity_id,'off')
    y,d,n=fixtures(3)
    monkeypatch.setattr(type(hass.services),'async_call',AsyncMock(return_value={ids['daily_events']:{'events':d},ids['yearly_events']:{'events':y}}))
    result=await upcoming(hass,n)
    assert len(result['snapshot']['segments'])==3
    args,kw=hass.services.async_call.call_args
    assert args[:2]==('calendar','get_events') and kw['return_response'] and kw['blocking']
    assert set(args[2]['entity_id'])==set(ids.values())
    assert 'latitude' not in str(result)
    with pytest.raises(Exception):await UpcomingView(hass).get(Request(admin=False))
    entry.options={'source_mode':'manual'}
    assert decoded(await UpcomingView(hass).get(Request()))['error']=='calendar_manual'
    entry.options={}
    hass.services.async_call.side_effect=TimeoutError()
    assert decoded(await UpcomingView(hass).get(Request()))['error']=='calendar_unavailable'
    registry.async_update_entity(ids['daily_events'],disabled_by=er.RegistryEntryDisabler.USER)
    with pytest.raises(PlanError,match='calendar_missing'):await upcoming(hass,n)
    hass.config_entries.async_entries.return_value=[provider,provider]
    with pytest.raises(PlanError,match='calendar_ambiguous'):await upcoming(hass,n)


@pytest.mark.asyncio
async def test_real_provider_event_contract():
    from hdate import Location,Zmanim
    from homeassistant.components.jewish_calendar.calendar import JewishCalendar,CALENDARS
    from homeassistant.components.jewish_calendar.const import DEFAULT_CALENDAR_EVENTS
    from zoneinfo import ZoneInfo
    # Exercise actual HA provider event generation, including a real two-day Rosh Hashanah.
    for diaspora in (False,True):
        location=Location('Fixture',latitude=51.5,longitude=-0.1,timezone='Europe/London',diaspora=diaspora)
        coordinator=SimpleNamespace(data=SimpleNamespace(diaspora=diaspora,language='en'),make_zmanim=lambda day:Zmanim(date=day,location=location))
        calendars=[]
        for description in (CALENDARS[0],CALENDARS[2]):
            cal=object.__new__(JewishCalendar);cal.entity_description=description;cal.coordinator=coordinator
            cal._events_config=DEFAULT_CALENDAR_EVENTS[description.key];calendars.append(cal)
        # Ordinary Shabbat, Rosh Hashanah, and diaspora Pesach Thu/Fri followed by Shabbat.
        for month,day,count in [(11,17,1),(9,10,2),(4,1,3 if diaspora else 1)]:
            start=datetime(2026,month,day,tzinfo=ZoneInfo('Europe/London'));end=start+timedelta(days=10)
            results=[]
            for cal in calendars:
                events=await cal.async_get_events(None,start,end)
                results.append([{'summary':e.summary,'start':e.start} for e in events])
            snapshot=assemble(results[1],results[0],'Europe/London',diaspora,start)
            assert len(snapshot['segments'])==count
            if month==9:assert [s['kind'] for s in snapshot['segments']]==['shabbat','yom_tov']
            if count==3:assert [s['kind'] for s in snapshot['segments']]==['yom_tov','yom_tov','shabbat']
