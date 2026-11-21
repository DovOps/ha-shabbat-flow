"""Private bounded PDF cache and serialized background generation."""
import asyncio
import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time

from .const import VERSION
MAX_FILES=40
MAX_BYTES=64*1024*1024

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def source_hash(data):
    # Generated report metadata is stable until observed evidence or feedback changes.
    return digest(data)

def cleanup(root,valid):
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    for p in root.glob('*.tmp'):p.unlink(missing_ok=True)
    kept=[]
    for p in root.glob('*.json'):
        try:
            m=json.loads(p.read_text());pdf=p.with_suffix('.pdf');old=time.time()-m['created']> (86400 if m['kind']=='preview' else 90*86400)
            invalid=m.get('version')!=VERSION or m['kind']=='report' and (m['run_id'] not in valid or m['review_revision']!=valid[m['run_id']])
            if old or invalid or not pdf.is_file():p.unlink(missing_ok=True);pdf.unlink(missing_ok=True)
            else:kept.append((m['created'],p,pdf,pdf.stat().st_size))
        except (ValueError,KeyError,OSError,TypeError):p.unlink(missing_ok=True);p.with_suffix('.pdf').unlink(missing_ok=True)
    for pdf in root.glob('*.pdf'):
        if not pdf.with_suffix('.json').exists():pdf.unlink(missing_ok=True)
    kept.sort(reverse=True);total=0
    for i,(_,p,pdf,size) in enumerate(kept):
        total+=size
        if i>=MAX_FILES or total>MAX_BYTES:p.unlink(missing_ok=True);pdf.unlink(missing_ok=True)

def write_pdf(root,key,meta,data,lang,kind):
    from .pdf_render import render_pdf
    value=render_pdf(data,lang,kind)
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    for suffix,raw in [('.pdf',value),('.json',json.dumps(meta).encode())]:
        target=root/(key+suffix);temp=target.with_suffix(suffix+'.tmp')
        with temp.open('wb') as f:os.chmod(temp,0o600);f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(temp,target)
    return len(value)

class PdfStore:
    def __init__(self,hass):
        self.hass=hass;self.root=Path(hass.config.path('.storage','shabbat_flow_pdfs'));self.jobs={};self.lock=asyncio.Lock();self.closed=False;self.cleanup_task=None
    def valid_runs(self):return {rid:r.get('review_revision',0) for rid,r in self.hass.data['shabbat_flow']['observer'].data['runs'].items()}
    async def tidy(self):
        async with self.lock:await self.hass.async_add_executor_job(cleanup,self.root,self.valid_runs())
    def schedule_cleanup(self):
        if self.closed or self.cleanup_task and not self.cleanup_task.done():return
        async def work():
            try:await self.tidy()
            except Exception:pass
        self.cleanup_task=self.hass.async_create_background_task(work(),"shabbat-flow-pdf-cleanup")
    async def close(self):
        self.closed=True
        if self.cleanup_task:self.cleanup_task.cancel()
        await asyncio.gather(*(job['task'] for job in self.jobs.values() if job.get('task')),return_exceptions=True)
    def report(self,rid):
        if not isinstance(rid,str) or not re.fullmatch('[a-f0-9]{32}',rid):raise ValueError('pdf_invalid')
        observer=self.hass.data['shabbat_flow']['observer']
        if observer.error:raise ValueError('pdf_unavailable')
        return observer.export(rid)
    async def start(self,payload):
        if self.closed:raise ValueError('pdf_unavailable')
        lang=payload.get('language');kind=payload.get('kind')
        if lang not in ('en','he') or kind not in ('report','preview'):raise ValueError('pdf_invalid')
        if kind=='report' and set(payload)=={'op','kind','language','id'}:data=self.report(payload['id']);rid=payload['id']
        elif kind=='preview' and set(payload)=={'op','kind','language','bundle'}:
            from .engine.schedule import compile_schedule
            data={'bundle':deepcopy(payload['bundle'])};rid=None
            if type(data['bundle']) is not dict or set(data['bundle'])!={'config','plan'}:raise ValueError('pdf_invalid')
            result=await self.hass.async_add_executor_job(compile_schedule,data['bundle']['config'],data['bundle']['plan'])
            if not result['complete']:raise ValueError('pdf_invalid')
            from .ownership import forecast_ha
            data['overlay']=forecast_ha(self.hass,data['bundle']['plan']['snapshot'])
            for event in data['overlay']['events']:
                state=self.hass.states.get(event['entity_id']);event['target_name']=state.name if state else event['entity_id']
        else:raise ValueError('pdf_invalid')
        hashed=source_hash(data);key=digest([VERSION,kind,lang,hashed]);meta={'version':VERSION,'key':key,'kind':kind,'language':lang,'source':hashed,'run_id':rid,'review_revision':data.get('review',{}).get('revision',0),'created':time.time(),'filename':f'ShabbatFlow-{kind}-{lang}-{key[:8]}.pdf'}
        if key in self.jobs and self.jobs[key]['status']=='pending':return {'key':key,'status':'pending'}
        async with self.lock:
            await self.hass.async_add_executor_job(cleanup,self.root,self.valid_runs())
            exists=await self.hass.async_add_executor_job((self.root/(key+'.json')).is_file)
        if exists:return {'key':key,'status':'ready'}
        if key in self.jobs and self.jobs[key]['status']=='pending':return {'key':key,'status':'pending'}
        if sum(j['status']=='pending' for j in self.jobs.values())>=2:raise ValueError('pdf_busy')
        self.jobs={k:j for k,j in self.jobs.items() if j['status']=='pending'}
        self.jobs[key]={'status':'pending'}
        self.jobs[key]['task']=self.hass.async_create_background_task(self.generate(key,meta,data,lang,kind),'shabbat-flow-pdf')
        return {'key':key,'status':'pending'}
    async def generate(self,key,meta,data,lang,kind):
        try:
            async with self.lock:
                if self.closed:return
                await self.hass.async_add_executor_job(write_pdf,self.root,key,meta,data,lang,kind)
                await self.hass.async_add_executor_job(cleanup,self.root,self.valid_runs())
            self.jobs[key]['status']='ready'
        except asyncio.CancelledError:
            self.jobs[key]['status']='failed'
            raise
        except Exception:self.jobs[key]['status']='failed'
    async def fetch(self,key,download=False):
        if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key):raise ValueError('pdf_invalid')
        job=self.jobs.get(key)
        if job and job['status'] in ('pending','failed'):return {'key':key,'status':job['status']}
        async with self.lock:
            await self.hass.async_add_executor_job(cleanup,self.root,self.valid_runs())
            try:meta=json.loads(await self.hass.async_add_executor_job((self.root/(key+'.json')).read_text))
            except (OSError,ValueError):raise ValueError('pdf_missing') from None
            if meta['kind']=='report' and source_hash(self.report(meta['run_id']))!=meta['source']:raise ValueError('pdf_stale')
            result={'key':key,'status':'ready','filename':meta['filename']}
            if download:
                raw=await self.hass.async_add_executor_job((self.root/(key+'.pdf')).read_bytes)
                if len(raw)>8*1024*1024 or not raw.startswith(b'%PDF-'):raise ValueError('pdf_invalid')
                result.update(content_type='application/pdf',base64=base64.b64encode(raw).decode())
            return result
