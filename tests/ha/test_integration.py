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
from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar, floor_registry as fr, label_registry as lr
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
    await lr.async_load(hass)
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
    assert panel.config['_panel_custom']['module_url'].startswith('/shabbat_flow_static/0.6.0/panel.js')
    assert hass.http.async_register_static_paths.await_count == 1
    assert hass.http.register_view.call_count == 7
    await async_unload_entry(hass, entry)
    assert 'shabbat-flow' not in hass.data[frontend.DATA_PANELS]
    with pytest.raises(web.HTTPServiceUnavailable): await SampleView(hass).get(Request())
    await async_setup_entry(hass, entry)
    assert hass.http.register_view.call_count == 7  # Routes are not registered twice on reload.
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

from copy import deepcopy
from custom_components.shabbat_flow.household import inventory, empty_settings, validate_settings, issues, workspace, internal_id
from custom_components.shabbat_flow.api import HouseholdView, HouseholdPlanView
from homeassistant.helpers.storage import Store


def room(purposes=None, lights=None, shared=None):
    return {'enabled': True, 'purposes': purposes or [], 'roles': {'main_lights': lights or [], 'night_lights': [], 'hvac': []},
            'shared_areas': shared or [], 'hvac': {'mode': 'none', 'temperature': None, 'fan_mode': None, 'lead_minutes': 60}}


def fixtures(hass):
    areas=ar.async_get(hass);reg=er.async_get(hass)
    bed=areas.async_create('Example bedroom');bath=areas.async_create('Example bathroom')
    light=reg.async_get_or_create('light','test','fixture-light',suggested_object_id='example_light')
    light=reg.async_update_entity(light.entity_id,area_id=bed.id)
    shared=reg.async_get_or_create('switch','test','fixture-shared',suggested_object_id='example_shared')
    shared=reg.async_update_entity(shared.entity_id,area_id=bath.id)
    for e in (light,shared):hass.states.async_set(e.entity_id,'off',{'friendly_name':'Example light','secret_attribute':'excluded'})
    return bed,bath,light,shared


@pytest.mark.asyncio
async def test_inventory_identity_drift_and_no_auto_assign(host):
    hass,_=host;bed,bath,light,shared=fixtures(hass)
    inv=inventory(hass);rooms={bed.id:room(['sleeping','recreation'],[light.id],[bath.id]),bath.id:room(lights=[shared.id])}
    saved={**empty_settings(),'rooms':rooms,'bindings':validate_settings(rooms,inv)}
    before=deepcopy(saved);reg=er.async_get(hass)
    assert issues(saved,inv)==[]
    renamed=reg.async_update_entity(light.entity_id,new_entity_id='light.renamed_example')
    hass.states.async_set(renamed.entity_id,'off')
    ar.async_get(hass).async_update(bed.id,name='Renamed room')
    assert renamed.id==light.id and issues(saved,inventory(hass))==[]
    extra=reg.async_get_or_create('light','test','new-light')
    assert extra.id not in saved['bindings'] and saved==before
    reg.async_update_entity(renamed.entity_id,area_id=bath.id)
    assert any(i['code']=='binding_changed' for i in issues(saved,inventory(hass)))
    reg.async_remove(renamed.entity_id)
    assert any(i['code']=='missing_entity' for i in issues(saved,inventory(hass)))
    assert 'secret_attribute' not in json.dumps(inv)


@pytest.mark.asyncio
async def test_store_reload_conflicts_and_authorization(host):
    hass,entry=host;bed,bath,light,shared=fixtures(hass);view=HouseholdView(hass)
    current=decoded(await view.get(Request()));payload={'revision':0,'inventory_revision':current['inventory']['revision'],
      'rooms':{bed.id:room(['sleeping'],[light.id]),bath.id:room(lights=[shared.id])}}
    raw=json.dumps(payload).encode()
    with pytest.raises(web.HTTPForbidden):await view.post(Request(raw,admin=False))
    result=decoded(await view.post(Request(raw)));assert result['settings']['revision']==1
    assert (await view.post(Request(raw))).status==409
    assert (await Store(hass,1,DOMAIN+'.household').async_load())['rooms']==payload['rooms']
    await async_unload_entry(hass,entry);await async_setup_entry(hass,entry)
    assert decoded(await view.get(Request()))['settings']['rooms']==payload['rooms']
    for body in (b'null',b'[]',b'{"x":NaN}'):
        assert (await view.post(Request(body))).status==400
    with pytest.raises(web.HTTPRequestEntityTooLarge):await view.post(Request(b'x'*(MAX_BODY+1),length=False))
    stale={**payload,'revision':1};ar.async_get(hass).async_update(bed.id,name='Moved name')
    assert (await view.post(Request(json.dumps(stale).encode()))).status==409


@pytest.mark.asyncio
async def test_personalized_workspace_and_shared_identity(host):
    hass,_=host;bed,bath,light,shared=fixtures(hass);inv=inventory(hass)
    rooms={bed.id:room(['sleeping','recreation'],[light.id],[bath.id]),bath.id:room(lights=[shared.id])}
    saved={**empty_settings(),'rooms':rooms,'bindings':validate_settings(rooms,inv)}
    snapshot=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']
    b=workspace(saved,inv,snapshot)
    assert 'Example bedroom' in [v['en'] for v in b['config']['rooms'].values()]
    assert len(b['config']['loads'])==2 and len(b['config']['profiles'])==4
    assert b['plan']['room_uses']==[] and b['plan']['availability'][0]['state']=='unset'
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    result=compile_schedule(b['config'],b['plan']);assert not result['complete']
    b['plan']['availability'][0]['state']='home'
    for meal in b['plan']['meals']:meal['choice']='none'
    profile=next(k for k,p in b['config']['profiles'].items() if p['purpose']=='sleeping')
    b['plan']['room_uses']=[{'id':'use_1','room':internal_id('room_',bed.id),'purpose':'sleeping','control':'planner',
        'profile':profile,'segment':snapshot['segments'][0]['id'],'start':'2027-01-07T22:00:00+02:00','end':'2027-01-08T08:00:00+02:00'}]
    result=compile_schedule(b['config'],b['plan']);assert result['complete'] and len(result['events'])==3
    assert workspace(saved,inv,snapshot)==workspace(saved,inv,snapshot)
    hass.states.async_set(light.entity_id,'unavailable')
    assert any(i['code']=='unavailable_entity' for i in issues(saved,inventory(hass)))
    with pytest.raises(ValueError):workspace(saved,inventory(hass),snapshot)


@pytest.mark.asyncio
async def test_storage_failure_does_not_acknowledge_save(host):
    hass,_=host;bed,bath,light,shared=fixtures(hass);view=HouseholdView(hass)
    inv=inventory(hass);payload={'revision':0,'inventory_revision':inv['revision'],'rooms':{bed.id:room(['sleeping'],[light.id])}}
    hass.data[DOMAIN]['household_store']=SimpleNamespace(async_save=AsyncMock(side_effect=OSError('disk error')))
    assert (await view.post(Request(json.dumps(payload).encode()))).status==500
    assert hass.data[DOMAIN]['household']['revision']==0


@pytest.mark.asyncio
async def test_inherited_area_and_explicit_hvac(host):
    hass,_=host;bed,bath,light,shared=fixtures(hass);reg=er.async_get(hass)
    # Synthetic device registration requires a config-entry record in HA's real registry.
    hass.config_entries.async_get_entry=Mock(return_value=SimpleNamespace(domain='test',pref_disable_new_entities=False,disabled_by=None,entry_id='fixture'))
    device=dr.async_get(hass).async_get_or_create(config_entry_id='fixture',identifiers={('test','example-device')},name='Example HVAC')
    dr.async_get(hass).async_update_device(device.id,area_id=bed.id)
    climate=reg.async_get_or_create('climate','test','fixture-climate',device_id=device.id)
    hass.states.async_set(climate.entity_id,'off',{'hvac_modes':['off','heat','cool'],'fan_modes':['auto'],'min_temp':16,'max_temp':30})
    inv=inventory(hass);e=next(e for e in inv['entities'] if e['id']==climate.id)
    assert e['area_id']==bed.id and e['area_source']=='device'
    r=room(['sleeping'],[light.id]);r['roles']['hvac']=[climate.id];r['hvac'].update(mode='heat',temperature=22,fan_mode='auto')
    validate_settings({bed.id:r},inv)
    r['hvac']['temperature']=60
    with pytest.raises(ValueError):validate_settings({bed.id:r},inv)

@pytest.mark.asyncio
async def test_household_plan_api_stale_and_snapshot_unchanged(host):
    hass,_=host;bed,bath,light,shared=fixtures(hass);inv=inventory(hass)
    rooms={bed.id:room(['sleeping'],[light.id])}
    hass.data[DOMAIN]['household']={**empty_settings(),'rooms':rooms,'bindings':validate_settings(rooms,inv)}
    payload={'revision':0,'inventory_revision':inv['revision'],'snapshot':json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']}
    view=HouseholdPlanView(hass)
    with pytest.raises(web.HTTPForbidden):await view.post(Request(json.dumps(payload).encode(),admin=False))
    result=decoded(await view.post(Request(json.dumps(payload).encode())))
    frozen=deepcopy(result)
    ar.async_get(hass).async_update(bed.id,name='Changed label')
    assert (await view.post(Request(json.dumps(payload).encode()))).status==409
    assert result==frozen
    assert (await view.post(Request(b'[]'))).status==400


@pytest.mark.asyncio
async def test_floors_deleted_areas_and_persistent_reload(host):
    hass,_=host;bed,bath,light,shared=fixtures(hass)
    floor=fr.async_get(hass).async_create('Example floor',level=1)
    ar.async_get(hass).async_update(bed.id,floor_id=floor.floor_id)
    inv=inventory(hass);assert any(a['floor_id']==floor.floor_id for a in inv['areas'])
    rooms={bed.id:room(['sleeping'],[light.id])}
    saved={**empty_settings(),'rooms':rooms,'bindings':validate_settings(rooms,inv),'revision':1}
    await hass.data[DOMAIN]['household_store'].async_save(saved)
    stored=await Store(hass,1,DOMAIN+'.household').async_load();assert stored==saved
    ar.async_get(hass).async_delete(bed.id)
    assert any(i['code']=='missing_area' for i in issues(stored,inventory(hass)))


def wizard_room(base, status='ready', service=False, home=False, timing=None):
    return {**base, 'setup': {'status':status,'service':service,'home':home,'bathroom_timing':timing or {}}}


@pytest.mark.asyncio
async def test_wizard_migration_drafts_and_dependencies(host):
    from custom_components.shabbat_flow.household import migrate_settings
    hass,_=host;bed,bath,light,shared=fixtures(hass);inv=inventory(hass)
    old={**empty_settings(),'rooms':{bed.id:room(['sleeping'],[light.id],[bath.id]),bath.id:room(lights=[shared.id])}}
    upgraded=migrate_settings(old)
    assert 'setup' not in old['rooms'][bed.id]
    assert upgraded['schema_version']==2 and upgraded['rooms'][bed.id]['setup']['bathroom_timing']=={bath.id:'use_window'}
    assert migrate_settings(upgraded)==upgraded
    rooms=upgraded['rooms'];rooms[bed.id]['setup']['status']='draft'
    rooms[bed.id]['roles']['main_lights']=['removed-reference']
    rooms[bath.id]['setup']['home']=True
    saved={**upgraded,'bindings':validate_settings(rooms,inv)}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']
    bundle=workspace(saved,inv,snap)
    assert len(bundle['config']['loads'])==1 and not bundle['config']['profiles']
    rooms[bed.id]['roles']['main_lights']=[light.id];rooms[bed.id]['setup']['status']='ready';rooms[bath.id]['setup']['status']='draft'
    with pytest.raises(ValueError):validate_settings(rooms,inv)


@pytest.mark.asyncio
@pytest.mark.parametrize('timing',['use_window','whole_observance'])
@pytest.mark.parametrize('days',[1,2,3])
async def test_wizard_bathroom_union_and_period_policy(host,timing,days):
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;bed,bath,light,shared=fixtures(hass);second=ar.async_get(hass).async_create('Example second bedroom');inv=inventory(hass)
    rooms={bed.id:wizard_room(room(['sleeping'],shared=[bath.id]),timing={bath.id:timing}),
           second.id:wizard_room(room(['sleeping'],shared=[bath.id]),timing={bath.id:timing}),
           bath.id:wizard_room(room(lights=[shared.id]),service=True)}
    saved={**empty_settings(),'rooms':rooms,'bindings':validate_settings(rooms,inv)}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];snap['segments']=snap['segments'][:days];snap['end']=snap['segments'][-1]['end'];bundle=workspace(saved,inv,snap);plan=bundle['plan']
    plan['availability'][0]['state']='home'
    for m in plan['meals']:m['choice']='none'
    for i,aid in enumerate((bed.id,second.id)):
        rid=internal_id('room_',aid);pid=next(k for k,p in bundle['config']['profiles'].items() if p['room']==rid)
        plan['room_uses'].append({'id':'use_'+str(i),'room':rid,'purpose':'sleeping','control':'planner','profile':pid,'segment':snap['segments'][0]['id'],
                                 'start':f'2027-01-07T{21+i:02}:00:00+02:00','end':f'2027-01-08T{7+i:02}:00:00+02:00'})
    result=compile_schedule(bundle['config'],plan)
    assert result['complete'] and len(result['events'])==2
    assert result['events'][0]['local']==(snap['start'] if timing=='whole_observance' else '2027-01-07T21:00:00+02:00')
    assert result['events'][1]['local']==(snap['end'] if timing=='whole_observance' else '2027-01-08T08:00:00+02:00')


@pytest.mark.asyncio
async def test_wizard_home_lights_follow_explicit_availability(host):
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;bed,bath,light,shared=fixtures(hass);inv=inventory(hass)
    rooms={bath.id:wizard_room(room(lights=[shared.id]),service=True,home=True)}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']
    bundle=workspace({**empty_settings(),'rooms':rooms,'bindings':validate_settings(rooms,inv)},inv,snap);p=bundle['plan']
    for m in p['meals']:m['choice']='none'
    assert not compile_schedule(bundle['config'],p)['complete']
    p['availability'][0]['state']='away';assert compile_schedule(bundle['config'],p)['events']==[]
    p['availability']=[{'id':'away','start':snap['preparation_start'],'end':'2027-01-07T20:00:00+02:00','state':'away'},
                       {'id':'home','start':'2027-01-07T20:00:00+02:00','end':snap['end'],'state':'home'}]
    result=compile_schedule(bundle['config'],p);assert len(result['events'])==2
    assert result['events'][0]['local']=='2027-01-07T20:00:00+02:00'


@pytest.mark.asyncio
async def test_current_hvac_is_sanitized_nonstructural_telemetry(host):
    hass,_=host;reg=er.async_get(hass);climate=reg.async_get_or_create('climate','test','example-current')
    attrs={'hvac_modes':['off','heat','cool'],'fan_modes':['auto'],'min_temp':16,'max_temp':30,'temperature':22,'fan_mode':'auto','secret':'not-exported'}
    hass.states.async_set(climate.entity_id,'heat',attrs);first=inventory(hass)
    current=first['entities'][0]['current'];assert current['mode']=='heat' and current['temperature']==22
    assert 'secret' not in json.dumps(first)
    hass.states.async_set(climate.entity_id,'cool',{**attrs,'temperature':24});second=inventory(hass)
    assert first['revision']==second['revision'] and second['entities'][0]['current']['temperature']==24


@pytest.mark.asyncio
@pytest.mark.parametrize('second_start,expected_count',[('2027-01-08T07:00:00+02:00',2),('2027-01-08T08:00:00+02:00',4)])
async def test_wizard_bathroom_touching_and_disjoint_demands(host,second_start,expected_count):
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;bed,bath,light,shared=fixtures(hass);inv=inventory(hass)
    rooms={bed.id:wizard_room(room(['sleeping'],shared=[bath.id])),bath.id:wizard_room(room(lights=[shared.id]),service=True)}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']
    b=workspace({**empty_settings(),'rooms':rooms,'bindings':validate_settings(rooms,inv)},inv,snap)
    p=b['plan'];p['availability'][0]['state']='home'
    for m in p['meals']:m['choice']='none'
    pid=next(iter(b['config']['profiles']))
    for i,(start,end) in enumerate([('2027-01-07T21:00:00+02:00','2027-01-08T07:00:00+02:00'),(second_start,'2027-01-08T10:00:00+02:00')]):
        p['room_uses'].append({'id':f'use_{i}','room':internal_id('room_',bed.id),'purpose':'sleeping','control':'planner','profile':pid,'segment':snap['segments'][0]['id'],'start':start,'end':end})
    result=compile_schedule(b['config'],p);assert result['complete'] and len(result['events'])==expected_count


@pytest.mark.asyncio
async def test_wizard_draft_persists_through_integration_reload(host):
    hass,entry=host;bed,bath,light,shared=fixtures(hass);inv=inventory(hass)
    pending=wizard_room(room(['sleeping'],[light.id],[bath.id]),status='draft',timing={bath.id:'whole_observance'})
    payload={'revision':0,'inventory_revision':inv['revision'],'rooms':{bed.id:pending,bath.id:wizard_room(room(lights=[shared.id]),status='draft',service=True)}}
    response=await HouseholdView(hass).post(Request(json.dumps(payload).encode()))
    assert response.status==200 and decoded(response)['settings']['rooms'][bed.id]==pending
    await async_unload_entry(hass,entry);hass.data[DOMAIN].pop('household')
    await async_setup_entry(hass,entry)
    stored=hass.data[DOMAIN]['household'];assert stored['schema_version']==2 and stored['rooms'][bed.id]==pending
    assert stored['revision']==1 and not issues(stored,inventory(hass))


@pytest.mark.asyncio
async def test_legacy_selection_without_devices_resumes_unfinished(host):
    from custom_components.shabbat_flow.household import migrate_settings
    hass,_=host;bed,bath,light,shared=fixtures(hass)
    old={**empty_settings(),'rooms':{bed.id:room(['sleeping']),bath.id:room()}}
    migrated=migrate_settings(old)
    assert all(r['enabled'] and r['setup']['status']=='draft' for r in migrated['rooms'].values())
    validate_settings(migrated['rooms'],inventory(hass))
    old['rooms'][bed.id]['shared_areas']=[bath.id]
    migrated=migrate_settings(old)
    assert migrated['rooms'][bed.id]['setup']['status']=='draft'


@pytest.mark.asyncio
@pytest.mark.parametrize('live_mode',['off','heat','cool'])
async def test_power_only_hvac_without_target_or_fan_metadata(host,live_mode):
    from homeassistant.components.climate import ClimateEntityFeature
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;bed,bath,light,shared=fixtures(hass)
    climate=er.async_get(hass).async_get_or_create('climate','test','example-power-only')
    climate=er.async_get(hass).async_update_entity(climate.entity_id,area_id=bed.id)
    hass.states.async_set(climate.entity_id,live_mode,{'supported_features':ClimateEntityFeature.TURN_ON|ClimateEntityFeature.TURN_OFF})
    inv=inventory(hass);entity=next(e for e in inv['entities'] if e['id']==climate.id)
    assert entity['power_support']=={'turn_on':True,'turn_off':True}
    r=wizard_room(room(['sleeping']));r['roles']['hvac']=[climate.id];r['hvac']['mode']='preserve'
    saved={**empty_settings(),'rooms':{bed.id:r},'bindings':validate_settings({bed.id:r},inv)}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];b=workspace(saved,inv,snap);p=b['plan']
    p['availability'][0]['state']='home'
    for m in p['meals']:m['choice']='none'
    p['room_uses']=[{'id':'sleep','room':internal_id('room_',bed.id),'purpose':'sleeping','control':'planner','profile':next(iter(b['config']['profiles'])),'segment':'day_1','start':'2027-01-07T22:00:00+02:00','end':'2027-01-08T08:00:00+02:00'}]
    result=compile_schedule(b['config'],p)
    assert result['complete'] and [e['action'] for e in result['events']]==[{'type':'hvac_power','state':'on'},{'type':'hvac_power','state':'off'}]
    assert result['events'][0]['local']=='2027-01-07T21:00:00+02:00'
    assert result['events'][1]['local']=='2027-01-08T08:00:00+02:00'
    assert all(load['kind']=='hvac_power' and load['capabilities']=={} for load in b['config']['loads'].values())
    # Missing advertised power support remains visibly unknown, not a guessed mode.
    hass.states.async_set(climate.entity_id,'off',{})
    assert next(e for e in inventory(hass)['entities'] if e['id']==climate.id)['power_support']=={'turn_on':False,'turn_off':False}


@pytest.mark.asyncio
async def test_power_only_does_not_reinterpret_unscheduled_and_clamps_preparation(host):
    from custom_components.shabbat_flow.household import migrate_settings
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;bed,bath,light,shared=fixtures(hass)
    climate=er.async_get(hass).async_get_or_create('climate','test','example-power-clamp')
    hass.states.async_set(climate.entity_id,'off',{})
    inv=inventory(hass);r=wizard_room(room(['recreation'],[light.id]));r['roles']['hvac']=[climate.id]
    saved={**empty_settings(),'rooms':{bed.id:r},'bindings':validate_settings({bed.id:r},inv)}
    assert migrate_settings(saved)['rooms'][bed.id]['hvac']['mode']=='none'
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']
    b=workspace(saved,inv,snap);assert all(load['kind']=='binary' for load in b['config']['loads'].values())
    r['hvac']['mode']='preserve';r['hvac']['lead_minutes']=180
    b=workspace(saved,inv,snap);p=b['plan'];p['availability'][0]['state']='home'
    for m in p['meals']:m['choice']='none'
    p['room_uses']=[{'id':'evening','room':internal_id('room_',bed.id),'purpose':'recreation','control':'planner','profile':next(iter(b['config']['profiles'])),'segment':'day_1','start':snap['start'],'end':'2027-01-07T23:00:00+02:00'}]
    events=compile_schedule(b['config'],p)['events'];power=[e for e in events if e['action']['type']=='hvac_power']
    assert power[0]['local']==snap['preparation_start'] and power[1]['action']['state']=='off'
    r['roles']['hvac']=[]
    with pytest.raises(ValueError):validate_settings({bed.id:r},inv)
    r['roles']['hvac']=[climate.id];r['purposes']=[];r['setup']['service']=True
    with pytest.raises(ValueError):validate_settings({bed.id:r},inv)
    r['purposes']=['recreation'];r['hvac']['mode']='profile'
    with pytest.raises(ValueError):validate_settings({bed.id:r},inv)

@pytest.mark.asyncio
async def test_label_inventory_revision_and_settings_persistence(host):
    from custom_components.shabbat_flow.household import empty_label_filters, migrate_settings
    hass,entry=host;bed,bath,light,shared=fixtures(hass);labels=lr.async_get(hass)
    label=labels.async_create('Example bathroom',description='Excluded private note')
    before=inventory(hass)
    er.async_get(hass).async_update_entity(shared.entity_id,labels={label.label_id})
    ar.async_get(hass).async_update(bed.id,labels={label.label_id})
    hass.config_entries.async_get_entry=Mock(return_value=SimpleNamespace(domain='test',pref_disable_new_entities=False,disabled_by=None,entry_id='fixture'))
    device=dr.async_get(hass).async_get_or_create(config_entry_id='fixture',identifiers={('test','label-device')},name='Example device')
    dr.async_get(hass).async_update_device(device.id,labels={label.label_id},area_id=bath.id)
    other=er.async_get(hass).async_get_or_create('light','test','label-light',device_id=device.id)
    inv=inventory(hass)
    assert inv['revision']!=before['revision']
    assert inv['labels']==[{'id':label.label_id,'name':'Example bathroom'}]
    assert next(a for a in inv['areas'] if a['id']==bed.id)['labels']==[label.label_id]
    assert next(e for e in inv['entities'] if e['id']==shared.id)['labels']==[label.label_id]
    assert next(e for e in inv['entities'] if e['id']==other.id)['device_labels']==[label.label_id]
    assert 'Excluded private note' not in json.dumps(inv)
    filters={**empty_label_filters(),'bathroom':label.label_id}
    rooms={bed.id:room(['sleeping'],[light.id])};view=HouseholdView(hass)
    payload={'revision':0,'inventory_revision':inv['revision'],'rooms':rooms,'label_filters':filters}
    result=decoded(await view.post(Request(json.dumps(payload).encode())))
    assert result['settings']['label_filters']==filters
    await async_unload_entry(hass,entry);hass.data[DOMAIN].pop('household');await async_setup_entry(hass,entry)
    assert hass.data[DOMAIN]['household']['label_filters']==filters
    labels.async_update(label.label_id,name='Renamed example')
    assert inventory(hass)['revision']!=inv['revision']
    stale={**payload,'revision':1}
    assert (await view.post(Request(json.dumps(stale).encode()))).status==409
    # Older clients must not erase configured filters.
    legacy={'revision':1,'inventory_revision':inventory(hass)['revision'],'rooms':rooms}
    assert decoded(await view.post(Request(json.dumps(legacy).encode())))['settings']['label_filters']==filters
    labels.async_delete(label.label_id)
    missing={'revision':2,'inventory_revision':inventory(hass)['revision'],'rooms':rooms,'label_filters':filters}
    assert (await view.post(Request(json.dumps(missing).encode()))).status==200
    invalid={**missing,'revision':3,'label_filters':{**filters,'main_lights':'never_existed'}}
    assert (await view.post(Request(json.dumps(invalid).encode()))).status==400
    assert migrate_settings(empty_settings())['label_filters']==empty_label_filters()
    saved=hass.data[DOMAIN]['household'];snapshot=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']
    assert workspace(saved,inventory(hass),snapshot)==workspace({**saved,'label_filters':empty_label_filters()},inventory(hass),snapshot)
