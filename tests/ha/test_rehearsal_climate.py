"""Synthetic HVAC/fan rehearsals; service spies never contact hardware."""
from copy import deepcopy
from datetime import timedelta
import pytest
from homeassistant.core import Context
from homeassistant.helpers import entity_registry as er
from homeassistant.components.fan import FanEntityFeature
from test_integration import host
from test_rehearsal import fixture,finish
from custom_components.shabbat_flow.household import internal_id
from custom_components.shabbat_flow.rehearsal_devices import snapshot

async def climate_fixture(host,monkeypatch,domain='climate'):
    f,s,review,payload=await fixture(host,monkeypatch);hass,x,b,old,e,c,now,base=f
    entity=er.async_get(hass).async_get_or_create(domain,'fixture','thermal_example',suggested_object_id='thermal_example')
    entity=er.async_get(hass).async_update_entity(entity.entity_id,area_id=e.area_id)
    p=internal_id('load_',entity.id);b=deepcopy(b)
    load=b['config']['loads'].pop(old);load['physical_id']=p;load['kind']='hvac_power' if domain=='climate' else 'binary';load['display']['role']='hvac' if domain=='climate' else 'fan';b['config']['loads'][p]=load
    for group in b['config']['groups'].values():
        for rule in group['rules']:
            rule['targets']=[p if t==old else t for t in rule['targets']]
            if p in rule['targets'] and domain=='climate':
                rule['action']['type']='hvac_power'
                if rule.get('release'):rule['release']['type']='hvac_power'
    room=next(iter(hass.data['shabbat_flow']['household']['rooms'].values()));room['roles']['hvac' if domain=='climate' else 'fans']=[entity.id]
    attrs={'temperature':23,'fan_mode':'auto','hvac_modes':['off','heat','cool'],'supported_features':385} if domain=='climate' else {'percentage':40,'preset_mode':None,'preset_modes':[],'direction':'forward','oscillating':False,'supported_features':int(FanEntityFeature.TURN_ON|FanEntityFeature.TURN_OFF|FanEntityFeature.SET_SPEED)} if domain=='fan' else {}
    hass.states.async_set(entity.entity_id,'cool' if domain=='climate' else 'on',attrs)
    async def service(call):
        c.append(call);current=deepcopy(dict(hass.states.get(entity.entity_id).attributes))
        state=call.data['hvac_mode'] if domain=='climate' else 'on' if call.service=='turn_on' else 'off'
        if domain=='fan':current['percentage']=call.data.get('percentage',40) if state=='on' else 0
        hass.states.async_set(entity.entity_id,state,current,context=call.context)
    for name in (['set_hvac_mode'] if domain=='climate' else ['turn_on','turn_off']):hass.services.async_register(domain,name,service)
    payload.update(bundle=b,included=[p],qualifications={p:'Verified native device power and settings during a weekday.'})
    return hass,x,b,p,entity,c,now,s,payload,attrs

async def reviewed(s,payload):
    review=await s.review_test(payload['bundle'],payload['selection']);payload={**payload,'review_digest':review['review_digest'],'reviewed_at':review['reviewed_at']};return review,payload

@pytest.mark.asyncio
@pytest.mark.parametrize('domain',['climate','fan','switch'])
async def test_capture_on_off_restore_preserves_settings(host,monkeypatch,domain):
    hass,x,b,p,e,c,now,s,payload,attrs=await climate_fixture(host,monkeypatch,domain)
    await s.capture(b,p);assert not c
    hass.states.async_set(e.entity_id,'off',{**attrs,**({'percentage':0} if domain=='fan' else {})})
    report,payload=await reviewed(s,payload);assert not report['rows'][0]['reasons'],report
    assert 'execute_unsupported' in (await x.review(b))['loads'][0]['reasons'] # scheduled pilot stays lighting-only
    r=await s.apply(payload,'owner');await finish(s);run=s.export(r['id'])
    assert next(iter(run['ledger'].values()))['status']=='confirmed'
    assert len(c)==1
    if domain=='climate':assert c[0].data=={'entity_id':e.entity_id,'hvac_mode':'cool'} and hass.states.get(e.entity_id).attributes['temperature']==23
    if domain=='fan':assert c[0].data=={'entity_id':e.entity_id,'percentage':40}
    restore=await s.restore_review(r['id']);assert not restore['rows'][0]['reasons'],restore
    await s.apply({**payload,'review_digest':restore['review_digest'],'reviewed_at':restore['reviewed_at'],'restore_of':r['id'],'request_id':'restore-thermal'},'owner');await finish(s)
    assert len(c)==2 and hass.states.get(e.entity_id).state=='off'
    assert not x.data['runs']

@pytest.mark.asyncio
@pytest.mark.parametrize('fault',['missing','expired','identity','drift','manual','mode','temperature'])
async def test_climate_fail_closed(host,monkeypatch,fault):
    hass,x,b,p,e,c,now,s,payload,attrs=await climate_fixture(host,monkeypatch)
    if fault!='missing':await s.capture(b,p)
    hass.states.async_set(e.entity_id,'off',attrs)
    if fault=='expired':s.data['baselines'][p]['at']=(now-timedelta(days=91)).isoformat()
    if fault=='identity':s.data['baselines'][p]['target']['registry_id']='wrong'
    if fault=='mode':hass.states.async_set(e.entity_id,'off',{**attrs,'hvac_modes':['off','heat']})
    if fault=='temperature':hass.states.async_set(e.entity_id,'off',{'hvac_modes':['off','cool']})
    report,payload=await reviewed(s,payload)
    if fault in ('drift','manual'):
        original=s.dispatch
        async def changed(*args,**kwargs):
            hass.states.async_set(e.entity_id,'off',{**attrs,'temperature':24},context=Context())
            await original(*args,**kwargs)
        monkeypatch.setattr(s,'dispatch',changed)
        r=await s.apply(payload,'owner');await finish(s);assert s.export(r['id'])['blocked'][p]=='rehearsal_intervened'
    else:
        assert report['rows'][0]['reasons']
        with pytest.raises(ValueError):await s.apply(payload,'owner')
    assert not c

@pytest.mark.asyncio
async def test_device_setting_reset_is_not_success_and_not_restored(host,monkeypatch):
    hass,x,b,p,e,c,now,s,payload,attrs=await climate_fixture(host,monkeypatch)
    await s.capture(b,p);hass.states.async_set(e.entity_id,'off',attrs)
    async def broken(call):
        c.append(call);hass.states.async_set(e.entity_id,'cool',{**attrs,'temperature':18},context=call.context)
    hass.services.async_register('climate','set_hvac_mode',broken)
    report,payload=await reviewed(s,payload);r=await s.apply(payload,'owner');await finish(s)
    run=s.export(r['id']);assert run['blocked'][p]=='rehearsal_settings_changed' and len(c)==1
    assert 'rehearsal_intervened' in (await s.restore_review(r['id']))['rows'][0]['reasons']

@pytest.mark.asyncio
async def test_capture_invalidates_review_and_missing_event_remains_excluded(host,monkeypatch):
    hass,x,b,p,e,c,now,s,payload,attrs=await climate_fixture(host,monkeypatch)
    report,payload=await reviewed(s,payload);await s.capture(b,p)
    with pytest.raises(ValueError,match='execute_stale'):await s.apply(payload,'owner')
    assert not c

@pytest.mark.asyncio
@pytest.mark.parametrize('domain',['climate','fan'])
async def test_off_then_restore_on_and_matching_noop(host,monkeypatch,domain):
    from custom_components.shabbat_flow.engine.schedule import compile_schedule
    from custom_components.shabbat_flow.ownership import instant
    hass,x,b,p,e,c,now,s,payload,attrs=await climate_fixture(host,monkeypatch,domain)
    report,no_op=await reviewed(s,payload);r=await s.apply(no_op,'owner');await finish(s)
    assert not c and next(iter(s.export(r['id'])['ledger'].values()))['status']=='already_correct'
    off=next(event for event in compile_schedule(**b)['events'] if event['action']['state']=='off')
    payload={**payload,'selection':{**payload['selection'],'at':instant(off['utc']).isoformat()},'request_id':'turn-off-native'}
    report,payload=await reviewed(s,payload);r=await s.apply(payload,'owner');await finish(s)
    assert hass.states.get(e.entity_id).state=='off' and p in s.data['baselines']
    report=await s.restore_review(r['id']);assert not report['rows'][0]['reasons'],report
    await s.apply({**payload,'review_digest':report['review_digest'],'reviewed_at':report['reviewed_at'],'restore_of':r['id'],'request_id':'restore-on-native'},'owner');await finish(s)
    assert len(c)==2 and hass.states.get(e.entity_id).state==('cool' if domain=='climate' else 'on')
    assert snapshot(hass.states.get(e.entity_id))['settings']==snapshot(type('State',(),{'domain':domain,'state':'on','context':Context(),'attributes':attrs})())['settings']

@pytest.mark.asyncio
async def test_fan_preset_and_climate_writer_detection(host,monkeypatch):
    from types import SimpleNamespace
    from custom_components.shabbat_flow.execution import source_scope
    hass,x,b,p,e,c,now,s,payload,attrs=await climate_fixture(host,monkeypatch,'fan')
    attrs={**attrs,'preset_mode':'sleep','preset_modes':['sleep'],'supported_features':attrs['supported_features']|int(FanEntityFeature.PRESET_MODE)}
    hass.states.async_set(e.entity_id,'on',attrs);await s.capture(b,p);hass.states.async_set(e.entity_id,'off',{**attrs,'percentage':0})
    report,payload=await reviewed(s,payload);r=await s.apply(payload,'owner');await finish(s)
    assert c[0].data=={'entity_id':e.entity_id,'preset_mode':'sleep'}
    hass.states.async_set('automation.fixture','on',{'friendly_name':'Fixture'})
    hass.data['automation']=SimpleNamespace(get_entity=lambda eid:SimpleNamespace(raw_config={'triggers':[{'trigger':'time','at':'23:00'}],'actions':[{'action':'climate.set_temperature','target':{'entity_id':e.entity_id},'data':{'temperature':22}}]}))
    scope=source_scope(hass);assert e.entity_id in scope['sources'][0]['targets']
