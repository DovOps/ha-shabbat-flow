"""Immediate rehearsal tests with real HA types and service spies only."""
import asyncio
from copy import deepcopy
from datetime import timedelta
import json
from unittest.mock import Mock
import pytest
from homeassistant.core import Context
from test_integration import host,Request,decoded
from test_execution import prepared,approved
from custom_components.shabbat_flow.engine.rehearsal import catalog
from custom_components.shabbat_flow.api import RehearsalView
from custom_components.shabbat_flow.rehearsal import Rehearsal,read_store

async def fixture(host,monkeypatch):
    f=await prepared(host,monkeypatch);hass,x,b,p,e,c,now,base=f
    monkeypatch.setattr('custom_components.shabbat_flow.rehearsal.now_utc',lambda:now)
    monkeypatch.setattr('custom_components.shabbat_flow.rehearsal.calendar_status',lambda hass:{'issur_off':True})
    rehearsal=hass.data['shabbat_flow']['rehearsal'];event=base['loads'][0]['first_event']
    area=b['config']['loads'][p]['display']['room']
    from custom_components.shabbat_flow.ownership import instant
    selection={'at':instant(event['utc']).isoformat(),'mode':'transition','areas':[area]}
    report=await rehearsal.review_test(b,selection)
    payload={'bundle':b,'selection':selection,'review_digest':report['review_digest'],'reviewed_at':report['reviewed_at'],'included':[p],'qualifications':{p:'Weekday On and Off verified.'},'attestations':{},'request_id':'fictional-rehearsal','confirm':True,'restore_of':None}
    return f,rehearsal,report,payload

async def finish(service):
    if service.tasks:await asyncio.gather(*list(service.tasks))

@pytest.mark.asyncio
async def test_rehearsal_exact_plan_and_reviewed_restore(host,monkeypatch):
    f,s,report,payload=await fixture(host,monkeypatch);hass,x,b,p,e,c,now,base=f;before=deepcopy(b)
    assert not c
    r=await s.apply(payload,'owner');await finish(s)
    assert len(c)==1 and c[0].service=='turn_on' and not x.data['runs']
    r=s.export(r['id']);assert r['bundle']==before and b==before and r['status']=='completed'
    assert next(iter(r['ledger'].values()))['status']=='confirmed'
    assert (await s.apply(payload,'owner'))['id']==r['id'] and len(c)==1
    restore=await s.restore_review(r['id']);assert not restore['rows'][0]['reasons']
    restored=await s.apply({**payload,'review_digest':restore['review_digest'],'reviewed_at':restore['reviewed_at'],'restore_of':r['id'],'request_id':'fictional-restore'},'owner');await finish(s)
    assert len(c)==2 and c[-1].service=='turn_off' and s.export(restored['id'])['kind']=='restore'
    assert not x.data['runs'] and not hass.data['shabbat_flow']['observer'].data['runs']
    assert read_store(s.path)['runs'][r['id']]['snapshot_hash']==report['snapshot_hash']
    await s.feedback(r['id'],'The example lamp responded correctly.');assert s.export(r['id'])['feedback']

@pytest.mark.asyncio
async def test_matching_noop_and_restore_skips_manual_intervention(host,monkeypatch):
    f,s,report,payload=await fixture(host,monkeypatch);hass,x,b,p,e,c,now,base=f
    r=await s.apply(payload,'owner');await finish(s)
    hass.states.async_set(e.entity_id,'on',{'changed':True},context=Context(user_id='example'))
    restore=await s.restore_review(r['id']);assert 'rehearsal_intervened' in restore['rows'][0]['reasons']
    review=await s.review_test(b,payload['selection']);r2=await s.apply({**payload,'review_digest':review['review_digest'],'reviewed_at':review['reviewed_at'],'request_id':'another-rehearsal'},'owner');await finish(s)
    assert len(c)==1 and next(iter(s.export(r2['id'])['ledger'].values()))['status']=='already_correct'
    assert 'rehearsal_intervened' in (await s.restore_review(r2['id']))['rows'][0]['reasons']

@pytest.mark.asyncio
@pytest.mark.parametrize('fault',['issur','stale','write','confirmation','expiry'])
async def test_apply_failures_never_dispatch(host,monkeypatch,fault):
    f,s,report,payload=await fixture(host,monkeypatch);hass,x,b,p,e,c,now,base=f
    if fault=='issur':monkeypatch.setattr('custom_components.shabbat_flow.rehearsal.calendar_status',lambda hass:{'issur_off':False})
    elif fault=='stale':hass.states.async_set(e.entity_id,'unavailable')
    elif fault=='write':monkeypatch.setattr('custom_components.shabbat_flow.execution.atomic_save',Mock(side_effect=OSError('fixture failure')))
    elif fault=='confirmation':payload['confirm']=False
    else:monkeypatch.setattr('custom_components.shabbat_flow.rehearsal.now_utc',lambda:now+timedelta(minutes=3))
    with pytest.raises(ValueError):await s.apply(payload,'owner')
    assert not c and not x.data['runs']

@pytest.mark.asyncio
async def test_stop_and_restart_do_not_replay(host,monkeypatch):
    f,s,report,payload=await fixture(host,monkeypatch);hass,x,b,p,e,c,now,base=f
    entered=asyncio.Event();release=asyncio.Event()
    async def command(call):c.append(call);entered.set();await release.wait()
    hass.services.async_register('light','turn_on',command)
    r=await s.apply(payload,'owner');await entered.wait();await s.disarm(r['id'],r['revision']);release.set();await finish(s)
    assert len(c)==1 and s.export(r['id'])['status']=='disarmed'
    data=deepcopy(s.data);data['runs'][r['id']]['status']='running';await s.commit(data)
    restored=Rehearsal(hass);await restored.load()
    assert restored.data['runs'][r['id']]['status']=='interrupted' and not restored.tasks and len(c)==1
    restored.path.write_text('{}');bad=Rehearsal(hass);await bad.load();assert bad.error

@pytest.mark.asyncio
async def test_overlapping_execution_and_dispatch_guard(host,monkeypatch):
    f,s,report,payload=await fixture(host,monkeypatch);hass,x,b,p,e,c,now,base=f
    # An active scheduled owner reserves this target, even though the rehearsal is separate.
    x.data['runs']['example']={'status':'running','included':[p],'start':now.isoformat(),'end':(now+timedelta(hours=1)).isoformat()}
    with pytest.raises(ValueError,match='execute_overlap'):await s.apply(payload,'owner')
    x.data['runs'].clear()
    original=s.dispatch
    async def changed(*args,**kwargs):
        monkeypatch.setattr('custom_components.shabbat_flow.rehearsal.calendar_status',lambda hass:{'issur_off':False})
        await original(*args,**kwargs)
    monkeypatch.setattr(s,'dispatch',changed)
    r=await s.apply(payload,'owner');await finish(s)
    assert not c and s.export(r['id'])['blocked'][p]=='rehearsal_observance'

@pytest.mark.asyncio
async def test_admin_api_and_unselected_devices(host,monkeypatch):
    from aiohttp import web
    f,s,report,payload=await fixture(host,monkeypatch);hass,x,b,p,e,c,now,base=f
    view=RehearsalView(hass)
    with pytest.raises(web.HTTPForbidden):await view.post(Request(json.dumps({'op':'apply','payload':payload}).encode(),admin=False))
    response=await view.post(Request(json.dumps({'op':'catalog','bundle':b}).encode()));assert decoded(response)['snapshot_hash']==report['snapshot_hash']
    response=await view.post(Request(json.dumps({'op':'apply','payload':{**payload,'included':['not-selected']}}).encode()));assert response.status==400
    assert not c

@pytest.mark.asyncio
@pytest.mark.parametrize('fault',['context','mapping','source'])
async def test_drift_after_review_blocks_dispatch(host,monkeypatch,fault):
    f,s,report,payload=await fixture(host,monkeypatch);hass,x,b,p,e,c,now,base=f
    original=s.dispatch
    async def changed(*args,**kwargs):
        if fault=='context':hass.states.async_set(e.entity_id,'off',{'outside':True},context=Context())
        elif fault=='mapping':monkeypatch.setattr(s,'valid_target',lambda *args:False)
        else:monkeypatch.setattr('custom_components.shabbat_flow.execution.source_scope',lambda hass:{'fingerprint':'changed'})
        await original(*args,**kwargs)
    monkeypatch.setattr(s,'dispatch',changed)
    r=await s.apply(payload,'owner');await finish(s)
    assert not c and s.export(r['id'])['blocked'][p]

@pytest.mark.asyncio
async def test_restart_invalidates_unapplied_review(host,monkeypatch):
    f,s,report,payload=await fixture(host,monkeypatch)
    restarted=Rehearsal(f[0]);await restarted.load()
    with pytest.raises(ValueError,match='execute_stale'):await restarted.apply(payload,'owner')
    assert not f[5]
