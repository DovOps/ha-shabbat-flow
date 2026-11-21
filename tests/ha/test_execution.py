"""Binary pilot tests: synthetic devices only; no production service calls."""
from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock
import json
import pytest
from test_integration import host,fixtures,room,wizard_room,ROOT,Request,decoded
from custom_components.shabbat_flow.household import empty_settings,inventory,validate_settings,workspace,internal_id
from custom_components.shabbat_flow.execution import DEFAULT_RECOVERY,load_store,source_scope
from custom_components.shabbat_flow.ownership import instant
from custom_components.shabbat_flow.api import ExecutionView
from homeassistant.helpers import entity_registry as er

async def prepared(host,monkeypatch):
    hass,_=host;bed,bath,light,shared=fixtures(hass)
    rooms={bed.id:wizard_room(room(lights=[light.id]),home=True,service=True)}
    inv=inventory(hass);saved={**empty_settings(),'rooms':rooms,'bindings':validate_settings(rooms,inv),'post_shutoff':True}
    hass.data['shabbat_flow']['household']=saved
    snap=json.loads((ROOT/'examples/period-preview.json').read_text())['plan']['snapshot'];snap['segments']=snap['segments'][:1];snap['end']=snap['segments'][0]['end']
    bundle=workspace(saved,inv,snap)
    for a in bundle['plan']['availability']:a['state']='home'
    for m in bundle['plan']['meals']:m['choice']='away'
    hass.data['automation']=SimpleNamespace(get_entity=lambda eid:None)
    calls=[]
    async def service(call):
        calls.append(call)
        hass.states.async_set(light.entity_id,'on' if call.service=='turn_on' else 'off',context=call.context)
    for s in ('turn_on','turn_off'):hass.services.async_register('light',s,service)
    executor=hass.data['shabbat_flow']['executor'];now=instant(snap['preparation_start'])-timedelta(hours=1)
    monkeypatch.setattr('custom_components.shabbat_flow.execution.now_utc',lambda:now)
    report=await executor.review(bundle,now);physical=internal_id('load_',light.id)
    assert not report['loads'][0]['reasons'], report
    assert report['loads'][0]['first_event']
    return hass,executor,bundle,physical,light,calls,now,report

async def approved(f,options=None,key='example-request'):
    hass,x,b,p,e,c,now,report=f
    return await x.approve(b,[p],report['review_digest'],{p:'Verified explicit on and off in weekday test.'},{},options or DEFAULT_RECOVERY,key,'example-owner',now,True)

@pytest.mark.asyncio
async def test_approve_arm_idempotency_matching_and_report(host,monkeypatch):
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    r=await approved(f);assert await approved(f)==r
    assert not c and load_store(x.path)['runs'][r['id']]['status']=='approved'
    r=await x.arm(r['id'],r['revision'],r['approval_digest'],now)
    duplicate=await x.arm(r['id'],1,r['approval_digest'],now);assert duplicate==r
    assert len(hass.data['shabbat_flow']['observer'].data['runs'])==1 and not c
    on=next(event for event in r['events'] if event['action']['state']=='on');at=instant(on['utc'])
    hass.states.async_set(e.entity_id,'on');await x.tick(at)
    assert not c and x.data['runs'][r['id']]['ledger'][on['id']]['status']=='already_correct'
    off=next(event for event in r['events'] if event['action']['state']=='off');at=instant(off['utc'])
    await x.tick(at);assert len(c)==1 and c[0].service=='turn_off' and c[0].data=={'entity_id':e.entity_id}
    await x.tick(at+timedelta(seconds=1));assert len(c)==1
    assert x.data['runs'][r['id']]['ledger'][off['id']]['status']=='confirmed'
    export=hass.data['shabbat_flow']['observer'].export(r['observer_id'])
    assert export['mode']=='control_and_observe' and export['dispatch_attempts']==1 and export['device_commands_sent'] is None

@pytest.mark.asyncio
@pytest.mark.parametrize('failure',['storage','source','mapping','unavailable','missed','disarmed'])
async def test_failure_no_dispatch(host,monkeypatch,failure):
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    r=await approved(f);r=await x.arm(r['id'],r['revision'],r['approval_digest'],now)
    at=instant(r['events'][0]['utc'])
    if failure=='storage':monkeypatch.setattr('custom_components.shabbat_flow.execution.atomic_save',Mock(side_effect=OSError('fixture fault')))
    if failure=='source':hass.states.async_set('automation.new_source','on')
    if failure=='mapping':er.async_get(hass).async_update_entity(e.entity_id,area_id=None)
    if failure=='unavailable':hass.states.async_set(e.entity_id,'unavailable')
    if failure=='missed':at+=timedelta(seconds=121)
    if failure=='disarmed':await x.disarm(r['id'],r['revision'])
    await x.tick(at);assert not c
    assert x.error or x.data['runs'][r['id']]['blocked'] or failure=='disarmed'

@pytest.mark.asyncio
async def test_known_reactive_writer_and_unknown_attestation(host,monkeypatch):
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    raw={'triggers':[{'trigger':'state','entity_id':'switch.example'}],'actions':[{'action':'light.turn_on','target':{'entity_id':e.entity_id}}]}
    hass.states.async_set('automation.example_sync','on')
    hass.data['automation']=SimpleNamespace(get_entity=lambda eid:SimpleNamespace(raw_config=raw))
    report=await x.review(b,now);assert 'execute_writer' in report['loads'][0]['reasons']
    raw['actions']=[{'action':'script.example'}]
    report=await x.review(b,now);assert report['unknown_sources']
    f=(*f[:-1],report)
    with pytest.raises(ValueError,match='execute_attestation'):await approved(f)
    r=await x.approve(b,[p],report['review_digest'],{p:'Weekday test verified.'},{'automation.example_sync|'+p:'Reviewed script has no access to this light.'},DEFAULT_RECOVERY,'unknown-example','owner',now,True)
    assert r['status']=='approved' and not c

@pytest.mark.asyncio
async def test_away_cannot_approve_and_admin_only(host,monkeypatch):
    from aiohttp import web
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    for a in b['plan']['availability']:a['state']='away'
    report=await x.review(b,now);assert not report['has_home']
    with pytest.raises(ValueError,match='execute_away'):await approved((*f[:-1],report))
    with pytest.raises(web.HTTPForbidden):await ExecutionView(hass).get(Request(admin=False))
    assert not c

@pytest.mark.asyncio
async def test_uncertain_ack_and_restart_never_replay(host,monkeypatch):
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    r=await approved(f);r=await x.arm(r['id'],r['revision'],r['approval_digest'],now)
    event=r['events'][0];at=instant(event['utc'])
    data=deepcopy(x.data);data['runs'][r['id']]['ledger'][event['id']]={'event_id':event['id'],'physical_id':p,'wanted':'on','at':at.isoformat(),'status':'dispatching','context_id':'example-intent'}
    await x.commit(data);x.resumed.add(r['id']);x.boot=at
    await x.tick(at+timedelta(minutes=1));assert not c
    await x.tick(at+timedelta(minutes=5));assert not c and x.data['runs'][r['id']]['blocked'][p]=='execute_unconfirmed'
    x.path.write_text('{}')
    with pytest.raises((KeyError,ValueError)):load_store(x.path)

@pytest.mark.asyncio
async def test_bounded_correction_and_manual_override(host,monkeypatch):
    from homeassistant.core import Context
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    r=await approved(f,{**DEFAULT_RECOVERY,'enabled':True,'interval_minutes':5});r=await x.arm(r['id'],r['revision'],r['approval_digest'],now)
    at=instant(r['events'][0]['utc']);await x.tick(at);await x.tick(at+timedelta(seconds=1));assert len(c)==1
    for i in range(2):
        hass.states.async_set(e.entity_id,'off');at+=timedelta(minutes=6);await x.tick(at);await x.tick(at+timedelta(seconds=1))
    assert len(c)==3
    hass.states.async_set(e.entity_id,'off',context=Context(user_id='example-user'));await x.tick(at+timedelta(minutes=6))
    assert len(c)==3 and x.data['runs'][r['id']]['blocked'][p]=='execute_external_change'

@pytest.mark.asyncio
async def test_disarm_inflight_and_overlapping_approval(host,monkeypatch):
    import asyncio
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    r=await approved(f);other=await approved(f,key='second-example')
    r=await x.arm(r['id'],r['revision'],r['approval_digest'],now)
    with pytest.raises(ValueError,match='execute_overlap'):await x.arm(other['id'],other['revision'],other['approval_digest'],now)
    entered=asyncio.Event();release=asyncio.Event()
    async def service(call):c.append(call);entered.set();await release.wait()
    hass.services.async_register('light','turn_on',service)
    task=asyncio.create_task(x.tick(instant(r['events'][0]['utc'])))
    await entered.wait();stopped=await x.disarm(r['id'],r['revision']);assert stopped['inflight']==1
    release.set();await task
    await x.tick(instant(r['events'][-1]['utc']));assert len(c)==1

@pytest.mark.asyncio
async def test_expired_and_stale_review_no_arm(host,monkeypatch):
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    r=await approved(f)
    with pytest.raises(ValueError,match='execute_stale'):await x.arm(r['id'],99,r['approval_digest'],now)
    with pytest.raises(ValueError,match='execute_deadline'):await x.arm(r['id'],r['revision'],r['approval_digest'],instant(r['start']))
    assert not c

@pytest.mark.asyncio
async def test_matching_without_context_is_not_owned_for_recovery(host,monkeypatch):
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    async def service(call):c.append(call);hass.states.async_set(e.entity_id,'on')
    hass.services.async_register('light','turn_on',service)
    r=await approved(f);r=await x.arm(r['id'],r['revision'],r['approval_digest'],now)
    at=instant(r['events'][0]['utc']);await x.tick(at);await x.tick(at+timedelta(seconds=1))
    assert not x.data['runs'][r['id']]['changed']
    assert x.data['runs'][r['id']]['ledger'][r['events'][0]['id']]['status']=='satisfied_uncertain'

@pytest.mark.asyncio
async def test_execution_api_bounds_and_explicit_export(host,monkeypatch):
    from aiohttp import web
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    view=ExecutionView(hass);r=await approved(f)
    assert 'ledger' not in decoded(await view.get(Request()))['runs'][0]
    response=await view.post(Request(json.dumps({'op':'export','id':r['id']}).encode()))
    assert decoded(response)['ledger']=={}
    bad=await view.post(Request(json.dumps({'op':'arm','id':r['id'],'revision':True,'approval_digest':r['approval_digest']}).encode()))
    assert bad.status==400
    with pytest.raises(web.HTTPForbidden):await view.post(Request(json.dumps({'op':'review','bundle':b}).encode(),admin=False))
    assert not c

@pytest.mark.asyncio
async def test_control_report_pdf_both_languages(host,monkeypatch):
    from custom_components.shabbat_flow.pdf_render import render_pdf
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,report=f
    r=await approved(f);r=await x.arm(r['id'],r['revision'],r['approval_digest'],now)
    at=instant(r['events'][0]['utc']);await x.tick(at);await x.tick(at+timedelta(seconds=1))
    data=hass.data['shabbat_flow']['observer'].export(r['observer_id'])
    for language in ('en','he'):
        pdf=await hass.async_add_executor_job(render_pdf,data,language,"report")
        assert pdf.startswith(b'%PDF-')
