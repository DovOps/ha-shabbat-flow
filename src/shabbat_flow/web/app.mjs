import {DRAFT_KEY,localeMetadata,parseDraft,translate,localTime} from './model.mjs';
const $=id=>document.getElementById(id);
let catalogs,bundle,initial,result=null,revision=0,statusKey='ready';
let language='en';
const t=key=>translate(catalogs,language,key);
const offsets=['bedroom_hvac','shared_hvac_off','night_lights','bedroom_lights'];

function node(tag,text,className){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;}
function status(key){statusKey=key;$('status').textContent=t(key);$('status').classList.toggle('error',key.startsWith('error_'));}
function errorKey(error){const key='error_'+error.message;return Object.hasOwn(catalogs[language],key)?key:'error_internal';}

function readForm(){
  const plan=structuredClone(bundle.plan);
  plan.language=language;plan.home=$('home').checked;
  plan.used_rooms=Object.keys(bundle.config.rooms).filter(id=>$('room-'+id).checked);
  for(const key of ['dinner','lunch','timezone','candle_lighting','sunrise','end'])plan[key]=$(key).value;
  for(const key of offsets)plan.offsets[key]=Number($('offset-'+key).value);
  return {config:bundle.config,plan};
}

function populate(){
  const plan=bundle.plan;$('home').checked=plan.home;
  for(const key of ['dinner','lunch','timezone','candle_lighting','sunrise','end'])$(key).value=plan[key];
  $('rooms').replaceChildren();
  for(const [id,room] of Object.entries(bundle.config.rooms)){
    const label=node('label',undefined,'toggle');const span=node('span',room.label[language]);span.dataset.roomLabel=id;
    const input=node('input');input.type='checkbox';input.id='room-'+id;input.checked=plan.used_rooms.includes(id);
    label.append(span,input);$('rooms').append(label);
  }
  $('offsets').replaceChildren();
  for(const key of offsets){
    const row=node('div',undefined,'range-row');const label=node('label');label.htmlFor='offset-'+key;
    const span=node('span');span.dataset.i18n=key;const output=node('output');output.id='value-'+key;
    label.append(span,output);const input=node('input');input.type='range';input.id='offset-'+key;input.min=0;input.max=720;input.step=15;input.value=plan.offsets[key];
    row.append(label,input);$('offsets').append(row);
  }
  localize();
}

function updateOutputs(){for(const key of offsets)$('value-'+key).textContent=new Intl.NumberFormat(language).format(Number($('offset-'+key).value)/60)+' '+t('hours');}
function localize(){
  document.documentElement.lang=language;document.documentElement.dir=localeMetadata[language].direction;$('language').value=language;
  document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=t(el.dataset.i18n));
  document.querySelectorAll('[data-room-label]').forEach(el=>el.textContent=bundle.config.rooms[el.dataset.roomLabel].label[language]);
  updateOutputs();status(statusKey);renderTimeline();
}
function invalidate(){revision++;result=null;$('export').disabled=true;status('stale');updateOutputs();renderTimeline();}

function renderTimeline(){
  $('timeline').replaceChildren();$('count').textContent=result?result.events.length+' '+t('events'):'';
  if(!result)return;
  if(!result.events.length){$('timeline').append(node('p',t('empty')));return;}
  const list=node('div',undefined,'events');list.setAttribute('role','list');
  for(const event of result.events){
    const row=node('div',undefined,'event');row.setAttribute('role','listitem');
    const time=node('time');time.dateTime=event.local;time.append(node('bdi',localTime(event.local,language,bundle.plan.timezone)));
    const resource=node('div',bundle.config.loads[event.load][language]);resource.append(node('small',t('rule_'+event.rule)));
    row.append(time,resource,node('span',t(event.state),'state '+event.state));list.append(row);
  }
  $('timeline').append(list);
}

async function requestPreview(value){
  let response;
  try{response=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});}catch{throw new Error('network');}
  let data;try{data=await response.json();}catch{throw new Error('internal');}
  if(!response.ok)throw new Error(data.error||'internal');return data;
}

async function preview(){
  const token=++revision;const candidate=readForm();status('working');
  try{const next=await requestPreview(candidate);if(token!==revision)return;bundle=candidate;result=next;$('export').disabled=false;status('ready');renderTimeline();}
  catch(error){if(token!==revision)return;result=null;$('export').disabled=true;renderTimeline();status(errorKey(error));}
}

async function save(){
  const token=++revision;const candidate=readForm();
  try{await requestPreview(candidate);if(token!==revision)return;try{localStorage.setItem(DRAFT_KEY,JSON.stringify(candidate));}catch{throw new Error('storage');}status('saved');}
  catch(error){if(token===revision)status(errorKey(error));}
}

async function load(){
  const token=++revision;
  try{let raw;try{raw=localStorage.getItem(DRAFT_KEY);}catch{throw new Error('storage');}
    const candidate=parseDraft(raw);let next;
    try{next=await requestPreview(candidate);}catch(error){if(error.message==='network')throw error;throw new Error('bad_draft');}
    if(token!==revision)return;bundle=candidate;language=candidate.plan.language;result=next;populate();$('export').disabled=false;status('loaded');
  }catch(error){if(token===revision)status(errorKey(error));}
}

async function init(){
  try{
    const responses=await Promise.all([fetch('/api/i18n'),fetch('/api/example')]);
    if(responses.some(r=>!r.ok))throw new Error('network');
    [catalogs,initial]=await Promise.all(responses.map(r=>r.json()));bundle=structuredClone(initial);populate();
    $('language').addEventListener('change',()=>{language=$('language').value;bundle.plan.language=language;localize();});
    $('planner').addEventListener('input',invalidate);
    $('planner').addEventListener('submit',e=>{e.preventDefault();preview();});
    $('save').addEventListener('click',save);$('load').addEventListener('click',load);
    $('delete').addEventListener('click',()=>{revision++;try{localStorage.removeItem(DRAFT_KEY);status('deleted');}catch{status('error_storage');}});
    $('reset').addEventListener('click',()=>{revision++;bundle=structuredClone(initial);bundle.plan.language=language;result=null;populate();$('export').disabled=true;status('reset_done');});
    $('export').addEventListener('click',()=>{if(!result)return;const data=JSON.stringify({...readForm(),preview:result},null,2);const url=URL.createObjectURL(new Blob([data],{type:'application/json'}));const link=node('a');link.href=url;link.download='shabbat-flow-preview.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
    await preview();
  }catch{ $('status').textContent='Unable to load local preview. / לא ניתן לטעון את התצוגה המקומית.'; }
}
init();
