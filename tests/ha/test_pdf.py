"""Stored artifacts: authentication, evidence binding, retention and real rendering."""
import asyncio
import base64
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from aiohttp import web
from test_integration import host, Request, decoded, ROOT
from custom_components.shabbat_flow.api import PdfView
from custom_components.shabbat_flow.pdf_store import PdfStore, cleanup
from custom_components.shabbat_flow.pdf_render import render_pdf, intervals, WORDS


def report_fixture():
    bundle=json.loads((ROOT/'examples/period-preview.json').read_text())
    snapshot=bundle['plan']['snapshot']
    return {'id':'a'*32,'status':'completed','kind':'plan','bundle':bundle,'start':snapshot['preparation_start'],'end':snapshot['end'],'last_sample':snapshot['end'],'snapshot_hash':'fictional','mapping':{},'summary':{},'review_revision':0,'preview':{'events':[]},'thermal':{'samples':[],'climates':[],'outdoor':None}}

async def ready(store,key):
    task=store.jobs.get(key,{}).get('task')
    if task:await task
    return await store.fetch(key)

@pytest.mark.asyncio
async def test_pdf_auth_cache_revision_restart_and_expiry(host,monkeypatch):
    hass,_=host;observer=hass.data['shabbat_flow']['observer'];r=report_fixture();observer.data['runs'][r['id']]=r;store=hass.data['shabbat_flow']['pdf'];view=PdfView(hass)
    body={'op':'generate','kind':'report','id':r['id'],'language':'he'}
    with pytest.raises(web.HTTPForbidden):await view.post(Request(json.dumps(body).encode(),admin=False))
    calls=Mock(side_effect=AssertionError('device call'));monkeypatch.setattr(type(hass.services),'async_call',calls)
    job=decoded(await view.post(Request(json.dumps(body).encode())));assert (await ready(store,job['key']))['status']=='ready'
    result=await store.fetch(job['key'],True);assert base64.b64decode(result['base64']).startswith(b'%PDF-');assert result['content_type']=='application/pdf'
    assert (store.root/(job['key']+'.pdf')).stat().st_mode & 0o777==0o600
    again=await store.start(body);assert again['key']==job['key'] and again['status']=='ready'
    restored=PdfStore(hass);assert (await restored.fetch(job['key']))['status']=='ready'
    r['last_sample']=r['start']
    with pytest.raises(ValueError,match='pdf_stale'):await restored.fetch(job['key'],True)
    r['review_revision']=1;await store.tidy();assert not (store.root/(job['key']+'.pdf')).exists()
    fresh=await store.start(body);await ready(store,fresh['key']);observer.data['runs'].clear();await store.tidy();assert not list(store.root.glob('*.pdf'))
    calls.assert_not_called()

@pytest.mark.asyncio
async def test_pdf_invalid_inputs_and_failure_isolated(host,monkeypatch):
    hass,_=host;store=hass.data['shabbat_flow']['pdf'];r=report_fixture();hass.data['shabbat_flow']['observer'].data['runs'][r['id']]=r
    for key in ('../secrets','a'*63,3,None):
        with pytest.raises(ValueError,match='pdf_invalid'):await store.fetch(key,True)
    for language in ('xx','../../'):
        with pytest.raises(ValueError,match='pdf_invalid'):await store.start({'op':'generate','kind':'report','id':r['id'],'language':language})
    import custom_components.shabbat_flow.pdf_store as module
    monkeypatch.setattr(module,'write_pdf',Mock(side_effect=OSError('disk full')))
    job=await store.start({'op':'generate','kind':'report','id':r['id'],'language':'en'});assert (await ready(store,job['key']))['status']=='failed';assert hass.data['shabbat_flow']['observer'].error is None
    assert not list(store.root.glob('*.pdf'))

@pytest.mark.asyncio
async def test_pdf_queue_bounds_and_deduplication(host,monkeypatch):
    hass,_=host;store=hass.data['shabbat_flow']['pdf'];observer=hass.data['shabbat_flow']['observer'];r=report_fixture();observer.data['runs'][r['id']]=r
    # Block worker through a test hook before disk rendering, not HA's event loop.
    original=store.generate;gate=asyncio.Event()
    async def delayed(*args):await gate.wait();await original(*args)
    monkeypatch.setattr(store,'generate',delayed)
    base={'op':'generate','kind':'report','id':r['id']}
    first=await store.start({**base,'language':'en'});assert await store.start({**base,'language':'en'})==first
    second=await store.start({**base,'language':'he'});r['last_sample']=r['start']
    with pytest.raises(ValueError,match='pdf_busy'):await store.start({**base,'language':'en'})
    gate.set();await asyncio.gather(*(j['task'] for j in store.jobs.values()))

@pytest.mark.asyncio
async def test_pdf_preview_is_validated_and_does_not_change_bundle(host):
    hass,_=host;store=hass.data['shabbat_flow']['pdf'];bundle=report_fixture()['bundle'];before=deepcopy(bundle)
    job=await store.start({'op':'generate','kind':'preview','language':'en','bundle':bundle});assert (await ready(store,job['key']))['status']=='ready';assert bundle==before
    with pytest.raises(Exception):await store.start({'op':'generate','kind':'preview','language':'en','bundle':{'config':{},'plan':{}}})


def test_pdf_intervals_and_translation_keys():
    assert WORDS['en'].keys()==WORDS['he'].keys()
    assert intervals([(0,'on'),(10,'off')],0,20,[(5,8)],15)==[(0,5,'on'),(5,8,'unknown'),(8,10,'on'),(10,15,'off'),(15,20,'unknown')]


def test_hebrew_temperature_units_and_parentheses():
    from custom_components.shabbat_flow.pdf_render import clean,get_display
    visual=get_display(clean('טמפרטורה (°C): 23 °C'),base_dir='R').replace('\u200e','')
    assert '(°C)' in visual and '23 °C' in visual
    assert ')C°(' not in visual
    assert get_display('בדיקה (חדר)',base_dir='R').startswith('(רדח)')
