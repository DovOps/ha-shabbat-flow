import {request} from './transport.mjs';
import {localDateTimeCandidates,localDateTimeValue,zonedISO} from './period-model.mjs';
let catalogs,data,draft,calendar,dirty=false,language='en',saving=false,offline=false,needsReview=false,opening=false;
const $=id=>document.getElementById(id),t=k=>catalogs[language][k]??k;
const defaults=()=>({enabled:false,purposes:[],roles:{main_lights:[],night_lights:[],hvac:[]},shared_areas:[],hvac:{mode:'none',temperature:null,fan_mode:null,lead_minutes:60}});
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
function status(key){$('status').textContent=t(key);}
function changed(){dirty=true;status('dirty');}
async function api(path,body){const r=await request('/api/v2/'+path,body===undefined?{}:{method:'POST',body:JSON.stringify(body)});const v=await r.json();if(!r.ok)throw new Error(v.error??'error');return v;}
function fail(e){status(catalogs[language][e.message]?e.message:'error');}
function checkbox(text,value,onChange,id){const label=el('label',undefined,'toggle'),input=el('input');input.type='checkbox';input.checked=value;if(id)input.id=id;input.onchange=()=>{onChange(input.checked);changed();};label.append(el('span',text),input);return label;}
function select(text,value,options,onChange){const label=el('label',undefined,'field'),input=el('select');label.append(el('span',text));for(const [val,name] of options){const o=el('option',name);o.value=val;input.append(o);}input.value=value;input.onchange=()=>{onChange(input.value);changed();};label.append(input);return label;}
function input(text,value,type,onChange){const label=el('label',undefined,'field'),control=el('input');control.type=type;control.value=value??'';control.oninput=()=>{onChange(control.value);changed();};label.append(el('span',text),control);return label;}
function updateAvailability(){
 for(const box of document.querySelectorAll('[data-entity-id]')){const e=data.inventory.entities.find(v=>v.id===box.dataset.entityId);if(e)box.querySelector('span').textContent=`${e.name} · ${e.entity_id} · ${t(e.disabled?'disabled':e.available?'available':'unavailable')}`;}
}
function syncLabel(){ $('sync').textContent=offline?t('offline'):`${t('synced')}: ${new Date(data.observed_at).toLocaleTimeString(language)} · ${data.inventory.areas.length} / ${data.inventory.entities.length}`; }
function renderRooms(){
 const root=$('rooms');root.replaceChildren();root.append(el('p',t('profile_help')),el('p',t('limits'),'hint'));
 const inv=data.inventory,known=new Set(inv.areas.map(a=>a.id));
 const areas=[...inv.areas,...Object.keys(draft).filter(id=>!known.has(id)).map(id=>({id,name:id,floor_id:null}))];
 for(const area of areas){
  const room=draft[area.id]??=defaults();const card=el('section',undefined,'card');
  card.append(el('h2',area.name),el('small',inv.floors.find(f=>f.id===area.floor_id)?.name??t('no_floor'),'hint'));
  if(!known.has(area.id))card.append(el('p',t('missing_area'),'error'));
  card.append(checkbox(t('enabled'),room.enabled,value=>{room.enabled=value;renderRooms();}));
  if(room.enabled){
   for(const p of ['sleeping','recreation'])card.append(checkbox(t(p),room.purposes.includes(p),v=>{room.purposes=v?[...room.purposes,p]:room.purposes.filter(x=>x!==p);}));
   const mappings=el('details');mappings.append(el('summary',t('assign')));
   let showAll=false;const roleHost=el('div');
   const drawRoles=()=>{roleHost.replaceChildren();for(const role of ['main_lights','night_lights','hvac']){
    const fieldset=el('fieldset');fieldset.append(el('legend',t(role)));const selected=room.roles[role];
    const candidates=inv.entities.filter(e=>(role==='hvac'?e.domain==='climate':['light','switch'].includes(e.domain))&&(showAll||e.area_id===area.id||selected.includes(e.id)));
    if(!candidates.length&&!selected.length)fieldset.append(el('p',t('none_found'),'hint'));
    for(const e of candidates){
     const state=e.disabled?'disabled':e.available?'available':'unavailable';
     const box=checkbox(`${e.name} · ${e.entity_id} · ${t(state)}`,selected.includes(e.id),v=>{room.roles[role]=v?[...room.roles[role],e.id]:room.roles[role].filter(x=>x!==e.id);drawRoles();});
     box.dataset.entityId=e.id;box.querySelector('input').disabled=e.disabled&&!selected.includes(e.id);fieldset.append(box);
     if(role==='hvac'&&selected.includes(e.id))fieldset.append(el('small',`${t('capabilities')}: ${JSON.stringify(e.capabilities)}`,'hint'));
    }
    for(const id of selected.filter(id=>!inv.entities.some(e=>e.id===id)))fieldset.append(checkbox(`${t('missing_choice')} · ${id}`,true,()=>{room.roles[role]=room.roles[role].filter(x=>x!==id);drawRoles();}));
    roleHost.append(fieldset);
   }};
   const all=checkbox(t('all_entities'),false,v=>{showAll=v;drawRoles();});all.querySelector('input').onchange=event=>{showAll=event.target.checked;drawRoles();};mappings.append(all,roleHost);drawRoles();card.append(mappings);
   const shared=el('details');shared.append(el('summary',t('shared')),el('p',t('shared_help'),'hint'));
   for(const other of areas.filter(a=>a.id!==area.id))shared.append(checkbox(other.name,room.shared_areas.includes(other.id),v=>{room.shared_areas=v?[...room.shared_areas,other.id]:room.shared_areas.filter(x=>x!==other.id);}));card.append(shared);
   const h=room.hvac;const climate=el('details');climate.append(el('summary',t('mode')),
    select(t('mode'),h.mode,['none','heat','cool'].map(v=>[v,t(v)]),v=>h.mode=v),
    input(t('temperature'),h.temperature,'number',v=>h.temperature=v===''?null:Number(v)),
    input(t('fan_mode'),h.fan_mode,'text',v=>h.fan_mode=v||null),
    input(t('lead_minutes'),h.lead_minutes,'number',v=>h.lead_minutes=Number(v)));card.append(climate);
  }
  root.append(card);
 }
 $('issues').replaceChildren();for(const item of data.issues)$('issues').append(el('p',`${t(item.code)} · ${item.id}`,'error'));
 $('unassigned').replaceChildren();const details=el('details');details.append(el('summary',`${data.inventory.entities.filter(e=>!e.area_id).length}`));
 for(const e of inv.entities.filter(e=>!e.area_id))details.append(el('p',`${e.name} · ${e.entity_id}`));$('unassigned').append(details);
}
let automatic=null,manualCalendar=false,calendarLoading=false,manualZone=null;
let dateValues={candles:'',sunrise:'',end:''},kind='shabbat',observance='';
function renderCalendar(){
 const root=$('calendar-summary');root.replaceChildren();
 const format=v=>new Date(v).toLocaleString(language==='he'?'he-IL':'en-GB',{timeZone:automatic?.snapshot?.timezone??data.inventory.timezone,dateStyle:'medium',timeStyle:'short'});
 if(manualCalendar)root.append(el('p',t('manual_active')));
 else if(automatic?.status==='ready'){
  const snap=automatic.snapshot;
  root.append(el('p',`${t('calendar_source')} · ${t(snap.observance)} · ${snap.timezone}`));
  root.append(el('p',`${format(snap.start)} — ${format(snap.end)}`));
  for(const seg of snap.segments){const row=el('section',undefined,'card');row.append(el('strong',t(seg.kind)),el('p',`${t('candles')}: ${format(seg.candle_lighting)}`),el('p',`${t('sunrise')}: ${format(seg.sunrise)}`),el('p',`${t('segment_end')}: ${format(seg.end)}`));root.append(row);}
 }else root.append(el('p',t(automatic?.error??'calendar_loading'),'error'));
 $('dates').hidden=!manualCalendar;$('manual-calendar').checked=manualCalendar;
 $('calendar-refresh').disabled=calendarLoading;
}
async function refreshCalendar(){
 if(calendarLoading)return;calendarLoading=true;$('calendar-refresh').disabled=true;
 try{automatic=await api('upcoming');}catch{automatic={status:'unavailable',error:'calendar_unavailable'};}
 finally{calendarLoading=false;renderCalendar();}
}
function setManualCalendar(value){
 if(value&&!manualCalendar)manualZone=automatic?.snapshot?.timezone??data.inventory.timezone;
 if(value&&!manualCalendar&&automatic?.status==='ready'){
  const s=automatic.snapshot,first=s.segments[0];dateValues={candles:first.candle_lighting,sunrise:first.sunrise,end:first.end};kind=first.kind;observance=s.observance;
 }
 manualCalendar=value;renderDates();renderCalendar();
}
function renderDates(){
 const root=$('dates');root.replaceChildren();root.append(el('p',manualZone??data.inventory.timezone));
 for(const key of ['candles','sunrise','end']){
  const label=el('label',undefined,'field'),control=el('input'),offset=el('select');control.type='datetime-local';control.step='1';control.required=true;offset.hidden=true;offset.setAttribute('aria-label',t('offset'));
  label.append(el('span',t(key)),control,offset);try{control.value=localDateTimeValue(dateValues[key],manualZone??data.inventory.timezone);}catch{}
  control.oninput=()=>{const values=localDateTimeCandidates(control.value,manualZone??data.inventory.timezone);dateValues[key]=values.length===1?values[0]:'';control.setCustomValidity(values.length===1?'':t('invalid_time'));offset.replaceChildren();offset.hidden=values.length!==2;if(values.length===2){for(const value of ['',...values]){const o=el('option',value?value.slice(-6):t('offset'));o.value=value;offset.append(o);}}};
  offset.onchange=()=>{dateValues[key]=offset.value;control.setCustomValidity(offset.value?'':t('invalid_time'));};root.append(label);
 }
 root.append(select(t('kind'),kind,['shabbat','yom_tov'].map(v=>[v,t(v)]),v=>kind=v),select(t('observance'),observance,[['',t('choose')],...['israel','diaspora'].map(v=>[v,t(v)])],v=>observance=v));
 // Calendar choices belong to the new workspace, not the household-save dirty flag.
 for(const s of root.querySelectorAll('select'))if(s.parentElement.lastChild===s&&s.options.length>0&&['shabbat','israel',''].includes(s.options[0].value)){
  if([...s.options].some(o=>o.value==='shabbat'))s.onchange=()=>kind=s.value;
  else if([...s.options].some(o=>o.value==='israel'))s.onchange=()=>observance=s.value;
 }
}
function render(){document.documentElement.lang=language;document.documentElement.dir=language==='he'?'rtl':'ltr';$('language').value=language;document.querySelectorAll('[data-i18n]').forEach(n=>n.textContent=t(n.dataset.i18n));renderRooms();renderDates();renderCalendar();syncLabel();if(dirty)status('dirty');else $('status').textContent='';}
async function refresh(manual=false,discard=false){
 if(saving)return;
 try{const next=await api('household'),changedInventory=data&&next.inventory.revision!==data.inventory.revision;
  const staleSaved=data&&next.settings.revision!==data.settings.revision;
  if(!data||discard||!dirty){const redraw=!data||discard||changedInventory||staleSaved;if(redraw){draft=structuredClone(next.settings.rooms);dirty=false;needsReview=false;}data=next;if(redraw)render();}
  else if(staleSaved){offline=false;status('stale_household');return;}
  else {data=next;if(manual){renderRooms();needsReview=false;}else if(changedInventory){needsReview=true;status('changed');}}
  offline=false;updateAvailability();syncLabel();
 }catch{offline=true;syncLabel();}
}
async function save(){if(needsReview)return status('changed');if(saving)return;saving=true;$('save').disabled=true;try{data=await api('household',{revision:data.settings.revision,inventory_revision:data.inventory.revision,rooms:draft});draft=structuredClone(data.settings.rooms);dirty=false;needsReview=false;render();status('saved');}catch(e){fail(e);}finally{saving=false;$('save').disabled=false;}}
function planProblems(){
 const problems=[];
 if(dirty)problems.push('needs_save');
 if(!manualCalendar){
  if(automatic?.status!=='ready')problems.push(automatic?.error??'calendar_unavailable');
  else if(new Date(automatic.snapshot.start)<=new Date())problems.push('calendar_expired');
 }else{
 if(!observance)problems.push('choose_observance');
 for(const key of ['candles','sunrise','end'])if(!dateValues[key])problems.push('missing_'+key);
 if(Object.values(dateValues).every(Boolean)){
  const {candles,sunrise,end}=dateValues;
  if(![candles,sunrise,end].every(v=>Number.isFinite(+new Date(v)))||!(new Date(candles)<new Date(sunrise)&&new Date(sunrise)<new Date(end)))problems.push('date_order');
  else if(new Date(end)-new Date(candles)>36*3600000)problems.push('multi_day');
 }
 }
 const rooms=Object.values(data.settings.rooms).filter(r=>r.enabled&&r.purposes.length);
 if(!dirty&&!rooms.some(r=>r.roles.main_lights.length||r.roles.night_lights.length||(r.roles.hvac.length&&r.hvac.mode!=='none')||r.shared_areas.some(a=>{const shared=data.settings.rooms[a];return shared?.enabled&&(shared.roles.main_lights.length||shared.roles.night_lights.length);})))problems.push('needs_roles');
 if(data.issues.length)problems.push('invalid_mapping');
 return problems;
}
function planFeedback(keys){
 const box=$('plan-status');box.replaceChildren();
 for(const key of keys)box.append(el('p',t(key)));
 box.focus({preventScroll:true});box.scrollIntoView({block:'nearest'});
}
async function openPlan(){
 if(opening)return;
 const problems=planProblems();if(problems.length)return planFeedback(problems);
 opening=true;$('plan').disabled=true;$('plan').textContent=t('opening_plan');planFeedback(['opening_plan']);
 try{
  let snapshot;
  if(!manualCalendar)snapshot=structuredClone(automatic.snapshot);
  else{
  const {candles,sunrise,end}=dateValues;
  const zone=manualZone??data.inventory.timezone;
  const start=candles,preparation=new Date(+new Date(candles)-30*60000);
  // Retain correct offset in the supplied HA timezone.
  snapshot={schema_version:2,period_id:'household_period',timezone:zone,observance,source:{id:'manual_override',version:'1'},preparation_start:zonedISO(preparation,zone),start,end,
   segments:[{id:'day_1',kind,start,end,candle_lighting:candles,sunrise}]};
  }
  const bundle=await api('household_plan',{revision:data.settings.revision,inventory_revision:data.inventory.revision,snapshot});bundle.plan.language=language;
  try{sessionStorage.setItem('shabbat-flow-household-workspace',JSON.stringify(bundle));}catch{throw new Error('workspace_storage_failed');}
  location.href='./period.html?household=1';
 }catch(e){planFeedback([catalogs[language][e.message]?e.message:'error']);}
 finally{opening=false;$('plan').disabled=false;$('plan').textContent=t('open_plan');}
}
async function boot(){try{
 catalogs=await (await fetch('./household-i18n.json')).json();language=navigator.language.startsWith('he')?'he':'en';
 data=await api('household');draft=structuredClone(data.settings.rooms);calendar=await api('calendar');
 try{automatic=await api('upcoming');}catch{automatic={status:'unavailable',error:'calendar_unavailable'};}
 dateValues.candles=calendar.values?.candle_lighting?.value??'';dateValues.end=calendar.values?.end?.value??'';
 const rise=calendar.values?.sunrise?.value;if(rise&&new Date(rise)>new Date(dateValues.candles)&&new Date(rise)<new Date(dateValues.end))dateValues.sunrise=rise;
 $('calendar-refresh').onclick=refreshCalendar;$('manual-calendar').onchange=e=>setManualCalendar(e.target.checked);
 $('language').onchange=()=>{language=$('language').value;render();};$('refresh').onclick=()=>refresh(true);$('discard').onclick=()=>refresh(true,true);$('save').onclick=save;$('plan').onclick=openPlan;render();
 setInterval(()=>{if(!document.hidden)refresh();},15000);window.addEventListener('focus',()=>refresh());
 window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
 }catch{$('status').textContent='Unable to load HA household. / לא ניתן לטעון את הבית מ־HA.';}}
boot();
