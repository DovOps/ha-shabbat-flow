"""Synthetic providers only: no network or SMS delivery."""
import asyncio
from copy import deepcopy
import json
from unittest.mock import AsyncMock, Mock
import pytest
from homeassistant.core import ServiceRegistry
from custom_components.shabbat_flow.notifications import Notifications, DEFAULT, capability, validate
from custom_components.shabbat_flow.api import ObserveView
from test_integration import host, Request, decoded

RID='a'*32

def provider(hass):
    hass.data['twilio_sms_ui']={'fixture':{'phone_numbers':['+12025550100'],'external_url':'https://ha.example.test'}}
    hass.services.async_register('twilio_sms_ui','send_message',lambda call:None)
    return dict(DEFAULT,enabled=True,sender='+12025550100',recipient='+12025550101')

def runs(status,kind='climate_study',rid=RID):
    return {'runs':{rid:{'status':status,'kind':kind}}}

@pytest.mark.asyncio
async def test_discovery_validation_and_admin(host):
    hass,_=host;n=hass.data['shabbat_flow']['notifications']
    assert not capability(hass)['available']
    hass.services.async_register('twilio_sms_ui','send_message',lambda call:None)
    assert not capability(hass)['available']
    cfg=provider(hass)
    assert capability(hass)['available']
    for field,value in [('recipient','123'),('sender','+12025550109'),('enabled',1)]:
        with pytest.raises(ValueError):validate(dict(cfg,**{field:value}),hass)
    hass.data['twilio_sms_ui']['fixture']['external_url']='http://ha.example.test'
    assert not capability(hass)['report_url_available']
    from aiohttp import web
    with pytest.raises(web.HTTPForbidden):await ObserveView(hass).post(Request(b'{"op":"sms_get"}',admin=False))
    assert decoded(await ObserveView(hass).post(Request(b'{"op":"sms_get"}')))['settings']['enabled'] is False

@pytest.mark.asyncio
async def test_optin_lifecycle_dedup_and_private_settings(host,monkeypatch):
    hass,_=host;n=hass.data['shabbat_flow']['notifications'];cfg=provider(hass)
    call=AsyncMock();monkeypatch.setattr(ServiceRegistry,'async_call',call)
    await n.record({'runs':{}},runs('observing'));await hass.async_block_till_done();call.assert_not_called()
    await n.configure(cfg);call.assert_not_called()
    await n.record({'runs':{}},runs('scheduled'));await hass.async_block_till_done();call.assert_not_called()
    await n.record(runs('scheduled'),runs('observing'));await hass.async_block_till_done()
    await n.record(runs('scheduled'),runs('observing'));await hass.async_block_till_done()
    assert call.await_count==1
    await n.record(runs('observing'),runs('completed'));await hass.async_block_till_done()
    assert call.await_count==2
    args=call.call_args.args
    assert args[:2]==('twilio_sms_ui','send_message')
    assert args[2]['target']==['+12025550101']
    assert args[2]['message'].endswith('https://ha.example.test/shabbat-flow?report='+RID)
    assert all(e['status']=='submitted_unconfirmed' for e in n.data['events'])
    assert '+12025550101' not in json.dumps(hass.data['shabbat_flow']['observer'].data)
    restored=Notifications(hass);await restored.load();await hass.async_block_till_done()
    await restored.record(runs('observing'),runs('completed'));await hass.async_block_till_done()
    assert call.await_count==2
    restored.close()

@pytest.mark.asyncio
async def test_filters_failure_interrupted_and_revision(host,monkeypatch):
    hass,_=host;n=hass.data['shabbat_flow']['notifications'];cfg=provider(hass)
    call=AsyncMock(side_effect=TimeoutError());monkeypatch.setattr(ServiceRegistry,'async_call',call)
    await n.configure(dict(cfg,climate=False))
    await n.record({'runs':{}},runs('observing'));await hass.async_block_till_done();call.assert_not_called()
    await n.record(runs('observing','plan'),runs('stopped','plan'));await hass.async_block_till_done()
    assert n.data['events'][0]['status']=='failed'
    data=deepcopy(n.data);data['events'][0]['status']='dispatching';await n.save(data)
    restored=Notifications(hass);await restored.load();await hass.async_block_till_done()
    assert restored.data['events'][0]['status']=='interrupted_unknown';assert call.await_count==1
    restored.close()
    monkeypatch.setattr(n,'kick',lambda:None)
    await n.record(runs('observing','plan'),runs('completed','plan'))
    await n.configure(dict(cfg,enabled=False));await n.flush()
    assert n.data['events'][-1]['status']=='cancelled';assert call.await_count==1

@pytest.mark.asyncio
async def test_disable_cancels_waiting_without_blocking_inflight(host,monkeypatch):
    hass,_=host;n=hass.data['shabbat_flow']['notifications'];cfg=provider(hass)
    await n.configure(cfg)
    started=asyncio.Event();finish=asyncio.Event()
    async def sending(*args,**kwargs):started.set();await finish.wait()
    call=AsyncMock(side_effect=sending);monkeypatch.setattr(ServiceRegistry,'async_call',call)
    await n.record({'runs':{}},runs('observing'))
    await started.wait()
    await n.record({'runs':{}},runs('observing',rid='b'*32))
    await asyncio.wait_for(n.configure(dict(cfg,enabled=False)),1)
    finish.set();await hass.async_block_till_done()
    assert call.await_count==1
    assert [e['status'] for e in n.data['events']]==['submitted_unconfirmed','cancelled']

@pytest.mark.asyncio
async def test_missing_provider_and_failed_store_no_dispatch(host,monkeypatch):
    hass,_=host;n=hass.data['shabbat_flow']['notifications'];cfg=provider(hass)
    await n.configure(cfg);monkeypatch.setattr(n,'kick',lambda:None)
    call=AsyncMock();monkeypatch.setattr(ServiceRegistry,'async_call',call)
    await n.record({'runs':{}},runs('observing'))
    hass.data.pop('twilio_sms_ui');await n.flush()
    assert n.data['events'][0]['status']=='unavailable';call.assert_not_called()
    provider(hass)
    await n.record(runs('observing'),runs('completed'))
    from custom_components.shabbat_flow import observe
    monkeypatch.setattr(observe,'atomic_save',lambda *args:(_ for _ in ()).throw(OSError()))
    await n.flush();call.assert_not_called();assert n.error=='store'

@pytest.mark.asyncio
async def test_push_only_both_channels_and_safe_targets(host,monkeypatch):
    hass,_=host;n=hass.data['shabbat_flow']['notifications'];cfg=provider(hass)
    hass.data['mobile_app']={}
    hass.services.async_register('notify','mobile_app_fixture',lambda call:None)
    # A registered action without a loaded provider is not sufficient.
    assert not capability(hass)['push_available']
    hass.data['mobile_app']={'fixture':{}}
    assert capability(hass)['push_services']==['mobile_app_fixture']
    with pytest.raises(ValueError):validate(dict(cfg,push_enabled=True,push_service='notify_everyone'),hass)
    call=AsyncMock();monkeypatch.setattr(ServiceRegistry,'async_call',call)
    await n.configure(dict(cfg,enabled=False,push_enabled=True,push_service='mobile_app_fixture'))
    call.assert_not_called()
    await n.record(runs('observing'),runs('completed'));await hass.async_block_till_done()
    assert call.await_count==1
    args=call.call_args.args
    assert args[:2]==('notify','mobile_app_fixture')
    assert args[2]['data']=={'url':'/shabbat-flow?report='+RID,'clickAction':'/shabbat-flow?report='+RID}
    assert 'target' not in args[2]
    await n.configure(dict(cfg,push_enabled=True,push_service='mobile_app_fixture'))
    await n.record({'runs':{}},runs('observing',rid='c'*32));await hass.async_block_till_done()
    assert call.await_count==3
    restored=Notifications(hass);await restored.load();await hass.async_block_till_done()
    assert restored.error is None
    await restored.record({'runs':{}},runs('observing',rid='c'*32));await hass.async_block_till_done()
    assert call.await_count==3
    restored.close()

@pytest.mark.asyncio
async def test_dependency_status_missing_partial_ready_and_readonly(host,monkeypatch):
    hass,entry=host
    from custom_components.shabbat_flow.dependencies import discover
    from homeassistant.helpers import entity_registry as er
    from types import SimpleNamespace
    call=AsyncMock();monkeypatch.setattr(ServiceRegistry,'async_call',call)
    rows={d['id']:d for d in discover(hass)['dependencies']}
    assert rows['core']['requirement']=='required' and rows['calendar']['status']=='missing'
    hass.config_entries.async_entries.return_value=[SimpleNamespace(entry_id='fixture')]
    assert next(d for d in discover(hass)['dependencies'] if d['id']=='calendar')['status']=='needs_setup'
    hass.config_entries.async_get_entry=Mock(return_value=SimpleNamespace(domain='jewish_calendar',pref_disable_new_entities=False,disabled_by=None,entry_id='fixture'))
    registry=er.async_get(hass)
    for key in ('daily_events','yearly_events'):
        e=registry.async_get_or_create('calendar','jewish_calendar',key,config_entry=SimpleNamespace(entry_id='fixture',pref_disable_new_entities=False,source='user',disabled_by=None),translation_key=key)
        hass.states.async_set(e.entity_id,'off')
    hass.services.async_register('calendar','get_events',lambda call:None)
    assert next(d for d in discover(hass)['dependencies'] if d['id']=='calendar')['ready']
    entry.options={'source_mode':'manual'}
    assert discover(hass)['calendar_mode']=='manual'
    call.assert_not_called()
    response=decoded(await ObserveView(hass).post(Request(b'{"op":"dependencies"}')))
    assert response['dependencies']

@pytest.mark.asyncio
async def test_pre_candle_reminders_same_day_off_only_dedup_and_restart(host,monkeypatch):
    from datetime import datetime,timezone,timedelta
    from custom_components.shabbat_flow import reminders, upcoming, notifications
    hass,_=host;n=hass.data['shabbat_flow']['notifications']
    hass.data['mobile_app']={'fixture':{}};hass.services.async_register('notify','mobile_app_fixture',lambda call:None)
    state={'available':True,'issur_off':True}
    monkeypatch.setattr(reminders,'status',lambda hass:state)
    now=datetime(2026,11,20,12,tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):return now
    monkeypatch.setattr(notifications,'datetime',Clock)
    snapshot={'start':(now+timedelta(hours=1)).isoformat(),'timezone':'Asia/Jerusalem'}
    read=AsyncMock(return_value={'snapshot':snapshot});monkeypatch.setattr(upcoming,'upcoming',read)
    call=AsyncMock();monkeypatch.setattr(ServiceRegistry,'async_call',call)
    await n.configure(dict(DEFAULT,reminder_enabled=True,push_service='mobile_app_fixture',reminder_offsets=[60,30]))
    await n.reminder_tick(now);await hass.async_block_till_done()
    assert call.await_count==1 and call.call_args.args[:2]==('notify','mobile_app_fixture')
    assert call.call_args.args[2]['data']['url']=='/shabbat-flow'
    await n.reminder_tick(now+timedelta(seconds=60));await hass.async_block_till_done();assert call.await_count==1
    restored=Notifications(hass);await restored.load();await restored.reminder_tick(now);await hass.async_block_till_done();assert call.await_count==1;restored.close()
    now+=timedelta(minutes=30)
    state['issur_off']=False
    await n.reminder_tick(now);await hass.async_block_till_done();assert call.await_count==1
    state['issur_off']=True
    await n.reminder_tick(now);await hass.async_block_till_done();assert call.await_count==2
    event=n.data['events'][-1]
    assert not reminders.allowed(hass,event,now+timedelta(minutes=3))
    assert not reminders.allowed(hass,event,datetime.fromisoformat(event['candle']))
    previous=dict(event,candle='2026-11-21T00:30:00+02:00',due='2026-11-20T23:30:00+02:00')
    assert not reminders.allowed(hass,previous,datetime.fromisoformat(previous['due']))
    for offsets in ([],[0],[30,30],[721],['30']):
        with pytest.raises(ValueError):validate(dict(DEFAULT,reminder_offsets=offsets),hass)

@pytest.mark.asyncio
async def test_product_name_and_only_legacy_default_title_migration(host):
    from custom_components.shabbat_flow import async_setup_entry, async_unload_entry
    from homeassistant.components import frontend
    hass,entry=host
    hass.config_entries.async_update_entry=Mock()
    await async_unload_entry(hass,entry)
    entry.title='ShabbatFlow Preview'
    await async_setup_entry(hass,entry)
    hass.config_entries.async_update_entry.assert_called_once_with(entry,title='Shabbat Flow')
    assert hass.data[frontend.DATA_PANELS]['shabbat-flow'].sidebar_title=='Shabbat Flow'
    await async_unload_entry(hass,entry)
    hass.config_entries.async_update_entry.reset_mock();entry.title='Custom title'
    await async_setup_entry(hass,entry)
    hass.config_entries.async_update_entry.assert_not_called()
