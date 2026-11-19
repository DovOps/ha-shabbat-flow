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
    assert panel.config['_panel_custom']['module_url'].startswith('/shabbat_flow_static/0.12.1/panel.js')
    assert hass.http.async_register_static_paths.await_count == 1
    assert hass.http.register_view.call_count == 8
    await async_unload_entry(hass, entry)
    assert 'shabbat-flow' not in hass.data[frontend.DATA_PANELS]
    with pytest.raises(web.HTTPServiceUnavailable): await SampleView(hass).get(Request())
    await async_setup_entry(hass, entry)
    assert hass.http.register_view.call_count == 8  # Routes are not registered twice on reload.
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
    saved={**empty_settings(),'post_shutoff':True,'rooms':rooms,'bindings':validate_settings(rooms,inv)}
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
    saved={**empty_settings(),'post_shutoff':True,'rooms':rooms,'bindings':validate_settings(rooms,inv)}
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
    saved={**empty_settings(),'post_shutoff':True,'rooms':rooms,'bindings':validate_settings(rooms,inv),'revision':1}
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
    saved={**empty_settings(),'post_shutoff':True,'rooms':rooms,'bindings':validate_settings(rooms,inv)}
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
    result=compile_schedule(bundle['config'],p);assert len(result['events'])==1  # Default retains final state.
    assert result['events'][0]['local']=='2027-01-07T20:00:00+02:00'
    bundle['config']['post_shutoff']=True
    assert len(compile_schedule(bundle['config'],p)['events'])==2


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
    saved={**empty_settings(),'post_shutoff':True,'rooms':{bed.id:r},'bindings':validate_settings({bed.id:r},inv)}
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
    saved={**empty_settings(),'post_shutoff':True,'rooms':{bed.id:r},'bindings':validate_settings({bed.id:r},inv)}
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

@pytest.mark.asyncio
@pytest.mark.parametrize('days',[1,2,3])
async def test_bathroom_daylight_and_night_policy(host,days):
    from custom_components.shabbat_flow.household import bathroom_policy
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;bed,bath,light,shared=fixtures(hass)
    night=er.async_get(hass).async_get_or_create('light','test','example-bath-night')
    er.async_get(hass).async_update_entity(night.entity_id,area_id=bath.id)
    hass.states.async_set(night.entity_id,'off')
    inv=inventory(hass)
    r=wizard_room(room(lights=[shared.id]),service=True,home=True);r['roles']['night_lights']=[night.id]
    r['setup']['lighting']={**bathroom_policy(r),'mode':'daylight','night_enabled':True}
    rooms={bath.id:r,bed.id:wizard_room(room(['sleeping'],shared=[bath.id]),timing={bath.id:'whole_observance'})}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];snap['segments']=snap['segments'][:days];snap['end']=snap['segments'][-1]['end']
    for seg in snap['segments']:seg['sunset']=seg['sunrise'][:10]+'T16:30:00+02:00'
    saved={**empty_settings(),'post_shutoff':True,'rooms':rooms,'bindings':validate_settings(rooms,inv)}
    bundle=workspace(saved,inv,snap);p=bundle['plan'];p['availability'][0]['state']='home'
    for meal in p['meals']:meal['choice']='none'
    profile=next(iter(bundle['config']['profiles']))
    p['room_uses']=[{'id':'sleep','room':internal_id('room_',bed.id),'purpose':'sleeping','control':'planner','profile':profile,'segment':'day_1','start':'2027-01-07T22:00:00+02:00','end':'2027-01-08T08:00:00+02:00'}]
    result=compile_schedule(bundle['config'],p);assert result['complete'] and result['warnings']==[]
    main=[(e['local'],e['action']['state']) for e in result['events'] if e['physical_id']==internal_id('load_',shared.id)]
    nights=[(e['local'],e['action']['state']) for e in result['events'] if e['physical_id']==internal_id('load_',night.id)]
    for seg in snap['segments']:
        day=seg['sunrise'][:10]
        assert (day+'T09:00:00+02:00','off') in main
        assert (day+'T14:30:00+02:00','on') in main
        assert (day+'T06:00:00+02:00','on') in main
        assert (day+'T06:00:00+02:00','off') in nights
    assert ('2027-01-07T22:40:00+02:00','off') in main
    assert ('2027-01-07T22:40:00+02:00','on') in nights
    assert len(main)==2+4*days and len(nights)==2*days
    # Neither a whole-period link nor home demand overrides the daylight break.
    original=deepcopy(saved);workspace(saved,inv,snap);assert saved==original
    del snap['segments'][0]['sunset']
    fallback=workspace(saved,inv,snap);fallback['plan'].update(availability=p['availability'],meals=p['meals'],room_uses=p['room_uses'])
    result=compile_schedule(fallback['config'],fallback['plan'])
    assert any(w['code']=='bathroom_daylight_fallback' for w in result['warnings'])
    assert not any(e['local']=='2027-01-08T09:00:00+02:00' for e in result['events'])
    # Night switching requires actual selections, not a label or an assumption.
    r['roles']['night_lights']=[]
    with pytest.raises(ValueError,match='bathroom_night_needs_lights'):validate_settings(rooms,inv)


def test_bathroom_policy_invalid_windows_and_dst():
    from custom_components.shabbat_flow.household import bathroom_policy, bathroom_windows
    from custom_components.shabbat_flow.engine.planning import validate_calendar
    snap={'schema_version':2,'period_id':'dst','timezone':'Europe/London','observance':'diaspora','source':{'id':'fixture','version':'1'},
          'preparation_start':'2027-03-27T17:30:00+00:00','start':'2027-03-27T18:00:00+00:00','end':'2027-03-28T20:00:00+01:00',
          'segments':[{'id':'day','kind':'yom_tov','start':'2027-03-27T18:00:00+00:00','end':'2027-03-28T20:00:00+01:00','candle_lighting':'2027-03-27T18:00:00+00:00','sunrise':'2027-03-28T06:00:00+01:00','sunset':'2027-03-28T19:00:00+01:00'}]}
    r={'setup':{'lighting':{**bathroom_policy({}),'mode':'daylight','night_enabled':True}}}
    windows,warnings=bathroom_windows(r,validate_calendar(snap));assert not warnings
    assert any(w['end']=='2027-03-28T09:00:00+01:00' for w in windows['main_lights'])
    r['setup']['lighting'].update(night_after_candles=720,off_after_sunrise=360,on_before_sunset=360)
    snap['segments'][0]['sunset']='2027-03-28T12:00:00+01:00'
    windows,warnings=bathroom_windows(r,validate_calendar(snap))
    assert set(warnings)=={'bathroom_daylight_fallback','bathroom_night_fallback'}
    assert windows['main_lights']==windows['night_lights'] and len(windows['main_lights'])==1

@pytest.mark.asyncio
@pytest.mark.parametrize('kind',['kitchen','background','hallway'])
async def test_room_night_morning_phases(host,kind):
    from custom_components.shabbat_flow.household import room_phases
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;bed,bath,light,shared=fixtures(hass);inv=inventory(hass)
    r=wizard_room(room(['recreation'],[light.id]));r['roles']['night_lights']=[shared.id]
    p=room_phases(r)
    if kind=='kitchen':p.update(night='home',evening_main=True,morning=True,night_end=120)
    elif kind=='hallway':p.update(night='home',night_start=0)
    r['setup']['phases']=p
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']
    snap['segments']=snap['segments'][:1];snap['end']=snap['segments'][-1]['end']
    b=workspace({**empty_settings(),'rooms':{bed.id:r},'bindings':validate_settings({bed.id:r},inv)},inv,snap)
    b['plan']['availability'][0]['state']='home'
    for meal in b['plan']['meals']:meal['choice']='none'
    if kind=='background':
        profile=next(iter(b['config']['profiles']))
        b['plan']['room_uses']=[{'id':'use','room':internal_id('room_',bed.id),'purpose':'recreation','control':'planner','profile':profile,'segment':'day_1','start':snap['start'],'end':'2027-01-07T23:00:00+02:00'}]
    result=compile_schedule(b['config'],b['plan']);assert result['complete'] and not result['warnings']
    def events(rid):return [(e['local'],e['action']['state']) for e in result['events'] if e['physical_id']==internal_id('load_',rid)]
    if kind=='kitchen':
        assert events(light.id)==[(snap['preparation_start'],'on'),('2027-01-07T22:40:00+02:00','off'),('2027-01-08T08:00:00+02:00','on')]
        assert events(shared.id)==[('2027-01-07T22:40:00+02:00','on'),('2027-01-08T08:00:00+02:00','off')]
    elif kind=='background':
        assert events(light.id)==[(snap['start'],'on'),('2027-01-07T23:00:00+02:00','off')]
        assert events(shared.id)==[('2027-01-07T23:00:00+02:00','on'),('2027-01-08T05:00:00+02:00','off')]
    else:
        assert not events(light.id)
        assert events(shared.id)==[('2027-01-07T16:40:00+02:00','on'),('2027-01-08T05:00:00+02:00','off')]
    b['config']['post_shutoff']=True
    if kind=='kitchen':assert any(e['local']==snap['end'] and e['action']['state']=='off' for e in compile_schedule(b['config'],b['plan'])['events'])


@pytest.mark.asyncio
@pytest.mark.parametrize('choice',['family','hosting','away','none'])
async def test_meal_room_lighting_and_power_only_hvac(host,choice):
    from custom_components.shabbat_flow.household import room_phases
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;bed,bath,light,shared=fixtures(hass)
    climate=er.async_get(hass).async_get_or_create('climate','test','meal-unit');hass.states.async_set(climate.entity_id,'off')
    inv=inventory(hass);r=wizard_room(room(['recreation'],[light.id]));r['roles']['hvac']=[climate.id];r['hvac']['mode']='preserve'
    r['setup']['phases']={**room_phases(r),'daytime_meal':True}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];snap['segments']=snap['segments'][:1];snap['end']=snap['segments'][-1]['end']
    b=workspace({**empty_settings(),'rooms':{bed.id:r},'bindings':validate_settings({bed.id:r},inv)},inv,snap)
    b['plan']['availability'][0]['state']='home'
    for meal in b['plan']['meals']:meal['choice']=choice if meal['kind']=='daytime' else 'none'
    lunch=next(m for m in b['plan']['meals'] if m['kind']=='daytime');assert lunch['groups']
    result=compile_schedule(b['config'],b['plan']);assert result['complete']
    if choice in ('away','none'):assert not result['events']
    else:
        assert len(result['events'])==4
        first=result['events'][0];assert first['action']=={'type':'hvac_power','state':'on'}
        assert first['local']=='2027-01-08T10:00:00+02:00'
        assert any(e['local']==lunch['start'] and e['action']=={'type':'state','state':'on'} for e in result['events'])

@pytest.mark.asyncio
async def test_post_shutoff_persistence_and_legacy_request(host):
    hass,_=host;bed,bath,light,shared=fixtures(hass);view=HouseholdView(hass)
    assert decoded(await view.get(Request()))['settings']['post_shutoff'] is False
    payload={'revision':0,'inventory_revision':inventory(hass)['revision'],'rooms':{bed.id:room(['sleeping'],[light.id])},'post_shutoff':True}
    result=decoded(await view.post(Request(json.dumps(payload).encode())))
    assert result['settings']['post_shutoff'] is True
    payload.pop('post_shutoff');payload['revision']=1
    assert decoded(await view.post(Request(json.dumps(payload).encode())))['settings']['post_shutoff'] is True
    payload.update(revision=2,post_shutoff='false')
    assert (await view.post(Request(json.dumps(payload).encode()))).status==400

@pytest.mark.asyncio
async def test_evening_meal_starts_background_without_recreation_selection(host):
    from custom_components.shabbat_flow.household import room_phases
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;bed,bath,light,shared=fixtures(hass);inv=inventory(hass)
    r=wizard_room(room(['recreation'],[light.id]));r['roles']['night_lights']=[shared.id]
    r['setup']['phases']={**room_phases(r),'evening_meal':True,'daytime_meal':True}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];snap['segments']=snap['segments'][:1];snap['end']=snap['segments'][-1]['end']
    b=workspace({**empty_settings(),'rooms':{bed.id:r},'bindings':validate_settings({bed.id:r},inv)},inv,snap);p=b['plan'];p['availability'][0]['state']='home'
    for m in p['meals']:m['choice']='family'
    dinner=next(m for m in p['meals'] if m['kind']=='evening')
    result=compile_schedule(b['config'],p);assert result['complete'] and not result['warnings']
    night=[(e['local'],e['action']['state']) for e in result['events'] if e['physical_id']==internal_id('load_',shared.id)]
    assert night==[(dinner['end'],'on'),('2027-01-08T05:00:00+02:00','off')]

@pytest.mark.asyncio
@pytest.mark.parametrize('days',[1,2,3])
@pytest.mark.parametrize('sunset_present',[True,False])
async def test_common_meals_night_and_daylight_compose_without_bathroom(host,days,sunset_present):
    from custom_components.shabbat_flow.household import room_phases, bathroom_policy
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;area,unused,light,night=fixtures(hass)
    climate=er.async_get(hass).async_get_or_create('climate','test','common-unit');hass.states.async_set(climate.entity_id,'off')
    inv=inventory(hass);r=wizard_room(room(lights=[light.id]),service=True)
    r['roles'].update(night_lights=[night.id],hvac=[climate.id]);r['hvac'].update(mode='preserve',lead_minutes=30)
    r['setup'].update(area_type='common',phases={**room_phases(r),'night':'home','evening_main':True,'morning':True,'night_end':120,'evening_meal':True,'daytime_meal':True},lighting={**bathroom_policy(r),'mode':'daylight'})
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];snap['segments']=snap['segments'][:days];snap['end']=snap['segments'][-1]['end']
    if sunset_present:
        for seg in snap['segments']:seg['sunset']=seg['sunrise'][:10]+'T16:30:00+02:00'
    before=deepcopy(r)
    saved={**empty_settings(),'rooms':{area.id:r},'bindings':validate_settings({area.id:r},inv)}
    b=workspace(saved,inv,snap);assert r==before and not r['purposes'] and not r['shared_areas']
    b['plan']['availability'][0]['state']='home'
    for m in b['plan']['meals']:m['choice']='family'
    result=compile_schedule(b['config'],b['plan']);assert result['complete']
    events=lambda rid:[e for e in result['events'] if e['physical_id']==internal_id('load_',rid)]
    assert len(events(climate.id))==days*4
    assert any(e['action']['state']=='on' for e in events(night.id))
    for seg in snap['segments']:
        day=seg['sunrise'][:10]
        main=[(e['local'],e['action']['state']) for e in events(light.id)]
        if sunset_present:
            assert (day+'T09:00:00+02:00','off') in main
            assert (day+'T14:30:00+02:00','on') in main
            assert not any(day+'T09:00:00+02:00'<e['local']<day+'T14:30:00+02:00' and e['action']['state']=='on' for e in events(light.id))
        else:assert not (day+'T09:00:00+02:00','off') in main
    assert bool(result['warnings']) != sunset_present
    assert not any(e['local']==snap['end'] and e['action'].get('state')=='off' for e in result['events'])

@pytest.mark.asyncio
async def test_area_types_persist_and_legacy_not_inferred(host):
    from custom_components.shabbat_flow.household import migrate_settings, room_phases
    hass,_=host;area,bath,light,shared=fixtures(hass);view=HouseholdView(hass)
    r=wizard_room(room(lights=[light.id]),service=True);r['setup']['phases']={**room_phases(r),'daytime_meal':True}
    legacy={**empty_settings(),'schema_version':2,'rooms':{area.id:r}}
    assert 'area_type' not in migrate_settings(legacy)['rooms'][area.id]['setup']
    r['setup']['area_type']='common'
    payload={'revision':0,'inventory_revision':inventory(hass)['revision'],'rooms':{area.id:r}}
    result=decoded(await view.post(Request(json.dumps(payload).encode())))
    assert result['settings']['rooms'][area.id]['setup']['area_type']=='common'
    assert not result['settings']['rooms'][area.id]['purposes']
    r['setup']['area_type']='hallway';payload['revision']=1
    assert (await view.post(Request(json.dumps(payload).encode()))).status==200

@pytest.mark.asyncio
async def test_area_label_bindings_survive_legacy_clients(host):
    from custom_components.shabbat_flow.household import empty_label_filters, validate_label_filters
    hass,_=host
    bath=lr.async_get(hass).async_create('Bathroom areas');hall=lr.async_get(hass).async_create('Hallway areas')
    inv=inventory(hass);filters={**empty_label_filters(),'bathroom_area':bath.label_id,'hallway_area':hall.label_id}
    old={k:v for k,v in filters.items() if k not in ('bathroom_area','hallway_area')}
    assert validate_label_filters(old,inv,filters)==filters
    assert validate_label_filters(filters,inv,empty_label_filters())==filters

@pytest.mark.asyncio
async def test_rest_defaults_persist_without_enabling_naps(host):
    hass,_=host;bed,bath,light,shared=fixtures(hass);inv=inventory(hass)
    r=wizard_room(room(['sleeping'],[light.id]))
    defaults={'nap_after_sunrise':420,'nap_duration':90,'lead_minutes':30,'late_wake_after_sunrise':300}
    r['setup']['rest_defaults']=defaults
    rooms={bed.id:r};saved={**empty_settings(),'rooms':rooms,'bindings':validate_settings(rooms,inv)}
    snapshot=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']
    before=deepcopy(saved);b=workspace(saved,inv,snapshot)
    assert saved==before and not b['plan'].get('naps') and not b['plan']['room_uses']
    assert all(p['rest_defaults']==defaults for p in b['config']['profiles'].values() if p['purpose']=='sleeping')
    view=HouseholdView(hass)
    result=decoded(await view.post(Request(json.dumps({'revision':0,'inventory_revision':inv['revision'],'rooms':rooms}).encode())))
    assert result['settings']['rooms'][bed.id]['setup']['rest_defaults']==defaults
    assert (await Store(hass,1,DOMAIN+'.household').async_load())['rooms'][bed.id]['setup']['rest_defaults']==defaults
    r['setup']['rest_defaults']['nap_duration']=0
    with pytest.raises(ValueError):validate_settings(rooms,inv)

@pytest.mark.asyncio
@pytest.mark.parametrize('days',[1,2,3])
@pytest.mark.parametrize('release',['planner','existing'])
async def test_circulation_entertaining_morning_and_external_owner(host,days,release):
    from custom_components.shabbat_flow.household import room_phases
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;area,bath,main,night=fixtures(hass);inv=inventory(hass)
    r=wizard_room(room(lights=[main.id]),service=True);r['setup']['area_type']='hallway';r['roles']['night_lights']=[night.id]
    r['setup']['phases']={**room_phases(r),'night':'entertaining','night_release':release,'evening_main':True,'morning':True,'morning_start':120,'morning_end':240}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];snap['segments']=snap['segments'][:days];snap['end']=snap['segments'][-1]['end']
    saved={**empty_settings(),'rooms':{area.id:r},'bindings':validate_settings({area.id:r},inv)}
    b=workspace(saved,inv,snap);p=b['plan'];p['availability'][0]['state']='home'
    for m in p['meals']:m['choice']='family' if m['kind']=='evening' else 'none'
    result=compile_schedule(b['config'],p);assert result['complete']
    for seg in snap['segments']:
        dinner=next(m for m in p['meals'] if m['segment']==seg['id'] and m['kind']=='evening')
        assert any(e['physical_id']==internal_id('load_',night.id) and e['local']==dinner['end'] and e['action']['state']=='on' for e in result['events'])
        date=seg['sunrise'][:10]
        for clock,state in [('08:00:00','on'),('10:00:00','off')]:
            assert any(e['physical_id']==internal_id('load_',main.id) and e['local']==date+'T'+clock+'+02:00' and e['action']['state']==state for e in result['events'])
    if release=='existing':
        assert any(w['code']=='external_night_release' for w in result['warnings'])
        assert not any(e['physical_id']==internal_id('load_',night.id) and e['action']['state']=='off' for e in result['events'])
    else:assert not result['warnings']
    p['availability'][0]['state']='away'
    for m in p['meals']:m['choice']='none'
    assert compile_schedule(b['config'],p)['events']==[]

@pytest.mark.asyncio
async def test_constant_main_ignores_daylight_and_preserves_end_policy(host):
    from custom_components.shabbat_flow.household import room_phases,bathroom_policy
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;area,_,main,_=fixtures(hass);inv=inventory(hass)
    r=wizard_room(room(lights=[main.id]),service=True);r['setup']['area_type']='common'
    r['setup']['phases']={**room_phases(r),'constant_main':True};r['setup']['lighting']={**bathroom_policy(r),'mode':'daylight'}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];snap['segments']=snap['segments'][:1];snap['end']=snap['segments'][-1]['end'];snap['segments'][0]['sunset']='2027-01-08T16:30:00+02:00'
    saved={**empty_settings(),'rooms':{area.id:r},'bindings':validate_settings({area.id:r},inv)}
    for shutoff in (False,True):
        saved['post_shutoff']=shutoff;b=workspace(saved,inv,snap);b['plan']['availability'][0]['state']='home'
        for m in b['plan']['meals']:m['choice']='none'
        events=compile_schedule(b['config'],b['plan'])['events'];assert [e['action']['state'] for e in events]==(['on','off'] if shutoff else ['on'])
        assert events[0]['local']==snap['start']
    r['setup']['phases']['morning']=True
    with pytest.raises(ValueError):validate_settings({area.id:r},inv)

@pytest.mark.asyncio
async def test_daytime_hvac_binding_without_meal_lighting_or_recreation(host):
    from custom_components.shabbat_flow.household import room_phases
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;area,_,main,_=fixtures(hass)
    ac=er.async_get(hass).async_get_or_create('climate','test','daytime-example');hass.states.async_set(ac.entity_id,'cool',{})
    inv=inventory(hass);r=wizard_room(room(lights=[main.id]),service=True);r['setup']['area_type']='common';r['roles']['hvac']=[ac.id];r['hvac']['mode']='preserve'
    r['setup']['phases']={**room_phases(r),'daytime_hvac':True,'evening_hvac':False,'evening_meal':True,'recreation_hvac':False}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];snap['segments']=snap['segments'][:1];snap['end']=snap['segments'][-1]['end']
    saved={**empty_settings(),'rooms':{area.id:r},'bindings':validate_settings({area.id:r},inv)}
    b=workspace(saved,inv,snap);b['plan']['availability'][0]['state']='home'
    for m in b['plan']['meals']:m['choice']='family'
    result=compile_schedule(b['config'],b['plan']);assert result['complete']
    events=result['events'];ac_events=[e for e in events if e['physical_id']==internal_id('load_',ac.id)]
    assert [e['action'] for e in ac_events]==[{'type':'hvac_power','state':'on'},{'type':'hvac_power','state':'off'}]
    assert all(e['local'].startswith('2027-01-08') for e in ac_events)
    assert all(e['local'].startswith('2027-01-07') for e in events if e['physical_id']==internal_id('load_',main.id))

@pytest.mark.asyncio
async def test_candle_night_can_explicitly_switch_main_off_without_evening_on(host):
    from custom_components.shabbat_flow.household import room_phases
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    hass,_=host;area,_,main,night=fixtures(hass);inv=inventory(hass)
    r=wizard_room(room(lights=[main.id]),service=True);r['setup']['area_type']='hallway';r['roles']['night_lights']=[night.id]
    r['setup']['phases']={**room_phases(r),'night':'home','night_start':0,'night_main_off':True}
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];snap['start']=snap['segments'][0]['start']=snap['segments'][0]['candle_lighting'];snap['segments']=snap['segments'][:1];snap['end']=snap['segments'][-1]['end']
    b=workspace({**empty_settings(),'rooms':{area.id:r},'bindings':validate_settings({area.id:r},inv)},inv,snap)
    b['plan']['availability'][0]['state']='home'
    for m in b['plan']['meals']:m['choice']='none'
    result=compile_schedule(b['config'],b['plan']);assert result['complete']
    main_events=[e for e in result['events'] if e['physical_id']==internal_id('load_',main.id)]
    assert len(main_events)==1 and main_events[0]['action']['state']=='off' and main_events[0]['local']==snap['start']

# Observe-only execution foundation: fictional states, no service adapter.
def observation_bundle(hass):
    from copy import deepcopy
    from custom_components.shabbat_flow.household import internal_id
    bundle=deepcopy(json.loads((ROOT/'examples/period-preview.json').read_text()))
    registry=er.async_get(hass)
    physical_map={}
    for old,load in bundle['config']['loads'].items():
        domain='climate' if load['kind'] in ('hvac','hvac_power') else 'switch'
        entity=registry.async_get_or_create(domain,'fixture_observe',old)
        hass.states.async_set(entity.entity_id,'off',{'temperature':22,'fan_mode':'auto'})
        physical_map[old]=entity
        load['physical_id']=internal_id('load_',entity.id)
    return bundle,physical_map


@pytest.mark.asyncio
async def test_observe_persist_restart_gaps_and_no_actuation(host,monkeypatch):
    from custom_components.shabbat_flow.observe import Observer,DEFAULT_POLICY
    from custom_components.shabbat_flow.ownership import instant
    from datetime import timedelta
    hass,_=host; bundle,entities=observation_bundle(hass)
    observer=hass.data[DOMAIN]['observer']; start=instant(bundle['plan']['snapshot']['preparation_start'])
    original=type(hass.services).async_call; monkeypatch.setattr(type(hass.services),'async_call',AsyncMock(side_effect=AssertionError('no services')))
    try:
        run=await observer.start(bundle,DEFAULT_POLICY,'request-001','admin',now=start)
        rid=run['id']; assert run['mode']=='observe'
        event=next(e for e in run['preview']['events'] if e['intent']=='set_state')
        at=instant(event['utc']); target=run['mapping'][event['physical_id']]['entity_id']
        hass.states.async_set(target,'on')
        await observer.tick(at)
        await observer.tick(at+timedelta(seconds=60))
        exported=observer.export(rid)
        assert exported['device_commands_sent']==0 and exported['run']['changes']
        assert 'actor' not in exported['run']
        observer.close(); restored=Observer(hass); await restored.load()
        assert not restored.error
        await restored.tick(at+timedelta(seconds=120))
        assert restored.export(rid)['run']['gaps'][-1]['reason']=='restart_or_collection_gap'
        assert restored.export(rid)['run']['summary'][event['physical_id']]['unknown_seconds']>=60
        stopped=await restored.stop(rid,now=at+timedelta(seconds=150)); assert stopped['run']['status']=='stopped'
        assert stopped['run']['bundle']==bundle
        hass.services.async_call.assert_not_called(); restored.close()
    finally: monkeypatch.setattr(type(hass.services),'async_call',original)


@pytest.mark.asyncio
async def test_observe_idempotence_overlap_failure_corrupt_store(host,monkeypatch):
    from custom_components.shabbat_flow.observe import Observer,DEFAULT_POLICY
    from custom_components.shabbat_flow.ownership import instant
    hass,_=host; bundle,_=observation_bundle(hass); observer=hass.data[DOMAIN]['observer']
    start=instant(bundle['plan']['snapshot']['preparation_start'])
    run=await observer.start(bundle,DEFAULT_POLICY,'request-002','admin',now=start)
    again=await observer.start(bundle,DEFAULT_POLICY,'request-002','admin',now=start)
    assert run['id']==again['id']
    with pytest.raises(ValueError,match='observe_conflict'): await observer.start(bundle,DEFAULT_POLICY,'request-003','admin',now=start)
    before=json.dumps(observer.data,sort_keys=True)
    def fail(*args):raise OSError('disk full')
    monkeypatch.setattr('custom_components.shabbat_flow.observe.atomic_save',fail)
    with pytest.raises(ValueError,match='observe_store'): await observer.stop(run['id'],now=start)
    assert json.dumps(observer.data,sort_keys=True)==before
    observer.close();observer.path.write_text('{broken')
    restored=Observer(hass);await restored.load();assert restored.error=='observe_store'
    with pytest.raises(ValueError,match='observe_store'): await restored.start(bundle,DEFAULT_POLICY,'request-004','admin',now=start)
    restored.close()


@pytest.mark.asyncio
async def test_observe_report_checks_bounds_disabled_and_clock_rollback(host):
    from custom_components.shabbat_flow.observe import DEFAULT_POLICY,policy
    from custom_components.shabbat_flow.ownership import instant
    from datetime import timedelta
    hass,_=host;bundle,_=observation_bundle(hass);observer=hass.data[DOMAIN]['observer']
    start=instant(bundle['plan']['snapshot']['preparation_start']);observer.boot=start
    for key,value in [('boot_delay_minutes',0),('interval_minutes',1),('enabled','yes')]:
        with pytest.raises(ValueError):policy({**DEFAULT_POLICY,key:value})
    run=await observer.start(bundle,DEFAULT_POLICY,'request-005','admin',now=start)
    await observer.tick(start+timedelta(minutes=4));assert not observer.data['runs'][run['id']]['checks']
    await observer.tick(start+timedelta(minutes=5));assert len(observer.data['runs'][run['id']]['checks'])==1
    await observer.tick(start+timedelta(minutes=6));assert len(observer.data['runs'][run['id']]['checks'])==1
    await observer.tick(start+timedelta(minutes=35));assert len(observer.data['runs'][run['id']]['checks'])==2
    before=json.dumps(observer.data,sort_keys=True);await observer.tick(start);assert json.dumps(observer.data,sort_keys=True)==before


def test_forecast_unmanaged_time_sun_conditions_and_conflicts():
    from custom_components.shabbat_flow.ownership import forecast,ownership_report
    snapshot=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']
    sources=[{'id':'automation.outdoor','enabled':True,'config':{'triggers':[{'trigger':'time','at':'23:00:00'}],'actions':[{'action':'switch.turn_off','target':{'entity_id':'switch.outdoor'}}]}},
             {'id':'automation.sun','enabled':True,'config':{'trigger':[{'platform':'sun','event':'sunrise','offset':'-01:00:00'}],'action':[{'service':'light.turn_off','target':{'entity_id':'light.hall'}}]}},
             {'id':'automation.conditional','enabled':True,'config':{'trigger':[{'platform':'time','at':'08:00'}],'condition':[{'condition':'state','entity_id':'binary_sensor.unresolved','state':'on'}],'action':[]}},
             {'id':'automation.disabled','enabled':False,'config':None}]
    overlay=forecast(snapshot,sources)
    assert len([e for e in overlay['events'] if e['source']=='automation.outdoor'])==3
    assert len([e for e in overlay['events'] if e['source']=='automation.sun'])==3
    assert any(v['source']=='automation.conditional' for v in overlay['unresolved'])
    assert not any(v['source']=='automation.disabled' for v in overlay['unresolved'])
    assert all(e['unmanaged'] for e in overlay['events'])
    first=overlay['events'][0]
    report=ownership_report([{'physical_id':'load','utc':snapshot['preparation_start'],'action':{'type':'state','state':'on'},'intent':'set_state'}],{'load':{'entity_id':first['entity_id']}},overlay)
    assert report['conflicts'][0]['kind']=='contradictory_state' and not report['live_clearance']
    assert forecast(snapshot,[],False)['unresolved']


@pytest.mark.asyncio
async def test_observe_api_auth_and_invalid_requests(host):
    from custom_components.shabbat_flow.api import ObserveView
    hass,_=host;view=ObserveView(hass)
    with pytest.raises(web.HTTPForbidden): await view.get(Request(admin=False))
    for payload in ({'op':'activate'},{'op':'export','id':[]},{'op':'forecast','bundle':{}},{'op':'stop','id':'missing'}):
        assert (await view.post(Request(json.dumps(payload).encode()))).status==400
    bundle,_=observation_bundle(hass)
    response=await view.post(Request(json.dumps({'op':'forecast','bundle':bundle}).encode()))
    assert response.status==200 and not decoded(response)['ownership']['live_clearance']
    assert decoded(await view.get(Request()))['runs']==[]

@pytest.mark.asyncio
async def test_observe_disable_checks_and_mapping_invalidation(host):
    from custom_components.shabbat_flow.observe import DEFAULT_POLICY
    from custom_components.shabbat_flow.ownership import instant
    from datetime import timedelta
    hass,_=host;bundle,entities=observation_bundle(hass);observer=hass.data[DOMAIN]['observer']
    start=instant(bundle['plan']['snapshot']['preparation_start']);observer.boot=start
    run=await observer.start(bundle,{**DEFAULT_POLICY,'enabled':False},'request-006','admin',now=start)
    await observer.tick(start+timedelta(minutes=10));assert not observer.data['runs'][run['id']]['checks']
    await observer.configure(run['id'],DEFAULT_POLICY)
    await observer.tick(start+timedelta(minutes=11));assert len(observer.data['runs'][run['id']]['checks'])==1
    physical=next(iter(run['mapping']));entity=run['mapping'][physical]['entity_id']
    er.async_get(hass).async_remove(entity)
    await observer.tick(start+timedelta(minutes=12))
    assert observer.data['runs'][run['id']]['last_states'][physical]['reason']=='mapping_changed'
    await observer.tick(instant(bundle['plan']['snapshot']['end'])+timedelta(minutes=1))
    result=observer.export(run['id']);assert result['run']['status']=='completed'
    assert len(result['run']['event_checks'])==len(result['run']['preview']['events'])
    assert all(not r['actuated'] for r in result['run']['event_checks'].values())
    for row in result['run']['summary'].values():
        assert sum(row[k+'_seconds'] for k in ('matched','mismatched','unknown','unplanned'))==73*3600


def test_observe_settings_baseline_and_profile_are_separate():
    from custom_components.shabbat_flow.observe import classify,settings_classify
    action={'type':'hvac_power','state':'on'}
    base={'state':'on','mode':'heat','settings':{'temperature':22,'fan_mode':'auto'},'unit':'°C'}
    wrong={**base,'mode':'cool'}
    assert classify(action,wrong)=='matched'
    assert settings_classify(action,wrong,base)=='mismatched'
    assert settings_classify(action,base,None)=='unknown'
    assert settings_classify(action,base,base)=='matched'
    assert settings_classify({'type':'hvac','mode':'heat','temperature':22,'fan_mode':'auto','unit':'C'},base,None)=='matched'


def test_forecast_dst_and_dynamic_targets_are_unresolved():
    from custom_components.shabbat_flow.ownership import forecast
    snapshot={'preparation_start':'2026-10-31T18:00:00-04:00','end':'2026-11-01T18:00:00-05:00','timezone':'America/New_York','segments':[]}
    source={'id':'automation.clock','enabled':True,'config':{'trigger':{'platform':'time','at':'01:30:00'},'action':{'service':'switch.turn_on','target':{'entity_id':'switch.sample'}}}}
    result=forecast(snapshot,[source]);assert not result['events'] and result['unresolved']
    source['config']['trigger']['at']='09:00:00';source['config']['action']['target']={'area_id':'sample'}
    result=forecast(snapshot,[source]);assert not result['events'] and result['unresolved']


@pytest.mark.asyncio
async def test_forecast_editor_metadata_and_registry_targets_without_calls(host, monkeypatch):
    from custom_components.shabbat_flow.ownership import forecast_ha
    hass,_=host
    label=lr.async_get(hass).async_create('Exterior')
    registry=er.async_get(hass)
    first=registry.async_get_or_create('switch','test','exterior-one',suggested_object_id='exterior_one')
    registry.async_update_entity(first.entity_id, labels={label.label_id})
    sensor=registry.async_get_or_create('sensor','test','exterior-temperature')
    registry.async_update_entity(sensor.entity_id, labels={label.label_id})
    raw={'triggers':[{'trigger':'time','at':'23:00:00'}], 'actions':[{'action':'switch.turn_off','metadata':{},'data':{},'target':{'label_id':label.label_id}}]}
    entity=SimpleNamespace(raw_config=raw)
    hass.data['automation']=SimpleNamespace(get_entity=lambda _:entity)
    hass.states.async_set('automation.exterior','on')
    spy=AsyncMock()
    monkeypatch.setattr(type(hass.services), "async_call", spy)
    snapshot=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot']
    result=forecast_ha(hass,snapshot)
    assert not result['unresolved']
    assert {e['entity_id'] for e in result['events']}=={first.entity_id}
    assert len(result['events'])==3
    second=registry.async_get_or_create('switch','test','exterior-two')
    registry.async_update_entity(second.entity_id, labels={label.label_id})
    changed=forecast_ha(hass,snapshot)
    assert {e['entity_id'] for e in changed['events']}=={first.entity_id,second.entity_id}
    assert result['fingerprints']!=changed['fingerprints']
    raw['actions'][0]['target']={'label_id':'missing-label'}
    missing=forecast_ha(hass,snapshot)
    assert not missing['events'] and missing['unresolved']
    raw['actions'][0]['target']={'entity_id':first.entity_id}
    assert forecast_ha(hass,snapshot)['events']
    raw['actions'].append({'action':'script.unknown'})
    unsupported=forecast_ha(hass,snapshot)
    assert not unsupported['events'] and unsupported['unresolved']
    spy.assert_not_called()
