"""Tests using real HA 2026.11.2 types and panel registry, synthetic household only."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import pytest
import pytest_asyncio
from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.components import frontend
from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar, floor_registry as fr
from custom_components.shabbat_flow import async_setup_entry, async_unload_entry
from custom_components.shabbat_flow.api import PreviewView, CalendarView, SampleView, MAX_BODY
from custom_components.shabbat_flow.config_flow import ShabbatFlowConfigFlow, schema
from custom_components.shabbat_flow.const import DOMAIN

ROOT = Path(__file__).resolve().parents[2]


@pytest_asyncio.fixture
async def host(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    hass.config.time_zone = 'Asia/Jerusalem'
    hass.http = SimpleNamespace(async_register_static_paths=AsyncMock(), register_view=Mock())
    hass.config_entries = SimpleNamespace(async_entries=Mock(return_value=[]), async_wait_initialized=AsyncMock())
    await fr.async_load(hass)
    await ar.async_load(hass)
    dr.async_setup(hass)
    await dr.async_load(hass, load_empty=True)
    await er.async_load(hass, load_empty=True)
    entry = SimpleNamespace(options={}, async_on_unload=Mock(), add_update_listener=Mock(return_value=lambda: None))
    await async_setup_entry(hass, entry)
    yield hass, entry
    await hass.async_stop(force=True)


class Content:
    def __init__(self, data): self.data = data
    async def iter_chunked(self, size):
        for start in range(0, len(self.data), size): yield self.data[start:start+size]


class Request(dict):
    def __init__(self, body=b'', admin=True, length=True):
        super().__init__(hass_user=SimpleNamespace(is_admin=admin))
        self.content_type = 'application/json'
        self.content_length = len(body) if length else None
        self.content = Content(body)


def decoded(response): return json.loads(response.body)


@pytest.mark.asyncio
async def test_real_panel_lifecycle(host):
    hass, entry = host
    panel = hass.data[frontend.DATA_PANELS]['shabbat-flow']
    assert panel.require_admin
    assert panel.config['_panel_custom']['module_url'].startswith('/shabbat_flow_static/panel.js')
    assert hass.http.async_register_static_paths.await_count == 1
    assert hass.http.register_view.call_count == 4
    await async_unload_entry(hass, entry)
    assert 'shabbat-flow' not in hass.data[frontend.DATA_PANELS]
    with pytest.raises(web.HTTPServiceUnavailable): await SampleView(hass).get(Request())
    await async_setup_entry(hass, entry)
    assert hass.http.register_view.call_count == 4  # Routes are not registered twice on reload.
    assert hass.http.async_register_static_paths.await_count == 1


@pytest.mark.asyncio
async def test_auth_and_compiler_parity(host):
    hass, _ = host
    view = PreviewView(hass)
    assert view.requires_auth is True
    body=(ROOT/'examples/period-preview.json').read_bytes()
    with pytest.raises(web.HTTPForbidden): await view.post(Request(body,admin=False))
    anonymous=Request(body);anonymous.clear()
    with pytest.raises(web.HTTPForbidden): await view.post(anonymous)
    result=decoded(await view.post(Request(body)))
    from src.shabbat_flow.schedule import compile_schedule
    source=json.loads(body)
    assert result==compile_schedule(source['config'],source['plan'])
    assert result['preview_only'] and result['complete']


@pytest.mark.asyncio
async def test_invalid_and_bounded_requests(host):
    hass, _ = host
    view=PreviewView(hass)
    for body in (b'null',b'[]',b'{',b'{"config":NaN,"plan":{}}'):
        assert (await view.post(Request(body))).status==400
    assert (await view.post(Request(b'x'*(MAX_BODY+1)))).status==413
    assert (await view.post(Request(b'x'*(MAX_BODY+1),length=False))).status==413
    request=Request(b'{}');request.content_type='text/plain'
    assert (await view.post(request)).status==400


@pytest.mark.asyncio
async def test_calendar_manual_missing_and_selected_values(host):
    hass, entry = host
    view=CalendarView(hass)
    missing=decoded(await view.get(Request()))
    assert missing['source']=='jewish_calendar' and not missing['provider_present']
    assert all(v['status']=='not_configured' for v in missing['values'].values())
    entry.options={'source_mode':'manual'}
    assert decoded(await view.get(Request()))['values']=={}
    entry.options={'source_mode':'selected_entities','candle_lighting':'sensor.sample_candle','sunrise':'sensor.sample_sunrise','active':'binary_sensor.sample_active'}
    hass.states.async_set('sensor.sample_candle','2027-01-08T14:20:37+00:00',{'private_note':'must not be returned'})
    hass.states.async_set('sensor.sample_sunrise','2027-01-09T06:00:00')
    hass.states.async_set('binary_sensor.sample_active','unavailable')
    value=decoded(await view.get(Request()))
    assert value['values']['candle_lighting']['value']=='2027-01-08T16:20:37+02:00'
    assert value['values']['sunrise']['status']=='invalid_time'
    assert value['values']['active']['status']=='unavailable'
    assert 'private_note' not in json.dumps(value)
    assert value['coverage']=='selected_values_only'


@pytest.mark.asyncio
async def test_auto_provider_uses_registry_not_display_name(host):
    hass, _=host
    registry=er.async_get(hass)
    entity=registry.async_get_or_create('sensor','jewish_calendar','fixture-candle',translation_key='upcoming_candle_lighting')
    hass.states.async_set(entity.entity_id,'2027-01-08T14:20:00+00:00')
    hass.states.async_set('sensor.not_the_provider','2027-01-08T00:00:00+00:00',{'friendly_name':'Jewish Calendar Candle Lighting'})
    value=decoded(await CalendarView(hass).get(Request()))
    assert value['values']['candle_lighting']['entity_id']==entity.entity_id
    registry.async_get_or_create('sensor','jewish_calendar','second-fixture',translation_key='upcoming_candle_lighting')
    assert decoded(await CalendarView(hass).get(Request()))['values']['candle_lighting']['status']=='ambiguous'


@pytest.mark.asyncio
async def test_config_flow_and_options_schema(host):
    hass,_=host
    flow=ShabbatFlowConfigFlow();flow.hass=hass;flow.handler=DOMAIN
    result=await flow.async_step_user()
    assert result['type']=='form' and result['step_id']=='user'
    hass.config_entries.async_entries.return_value=[SimpleNamespace(domain=DOMAIN,source='user')]
    assert (await flow.async_step_user())['reason']=='single_instance_allowed'
    fields=schema({}).schema
    assert {'source_mode','candle_lighting','sunrise','end','active'}=={str(k) for k in fields}
