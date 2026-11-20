import {offsetControl} from './time-input.mjs';
import {haIcon} from './ha-icons.mjs';
import {mealHvac,suggestedAreaTypes,areaType,isBathroom,classifyRoom,roomProblems,phases,labelRoles,emptyLabelFilters,roleCandidates,bathroomCandidates,suggestedPurposes,filteredAreas} from './household-model.mjs';
import {request} from './transport.mjs';
import {localDateTimeCandidates,localDateTimeValue,zonedISO} from './period-model.mjs';
let postShutoff=false,saveError=null,staleSettings=false;
let catalogs,data,draft,calendar,dirty=false,language='en',saving=false,offline=false,needsReview=false,opening=false;
const $=id=>document.getElementById(id),t=k=>catalogs[language][k]??k;
const defaults=()=>({enabled:false,setup:{status:'draft',service:false,home:false,bathroom_timing:{}},purposes:[],roles:{main_lights:[],night_lights:[],hvac:[]},shared_areas:[],hvac:{mode:'none',temperature:null,fan_mode:null,lead_minutes:60}});
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
function status(key){const problem=!['dirty','saved','inventory_reviewed'].includes(key);$('status').className=problem?'room-feedback blocked':'';$('status').textContent=(problem?'⚠ ':'')+t(key);}
function changed(){dirty=true;saveError=null;status('dirty');updateRoomFeedback();}
async function api(path,body){const r=await request('/api/v2/'+path,body===undefined?{}:{method:'POST',body:JSON.stringify(body)});const v=await r.json();if(!r.ok)throw new Error(v.error??'error');return v;}
function fail(e){saveError=catalogs[language][e.message]?e.message:'error';status(saveError);updateRoomFeedback();}
function checkbox(text,value,onChange,id){const label=el('label',undefined,'toggle'),input=el('input');input.type='checkbox';input.checked=value;if(id)input.id=id;input.onchange=()=>{onChange(input.checked);changed();};label.append(el('span',text),input);return label;}
let restOpen=false;let helpId=0;const presetNotes={};
function select(text,value,options,onChange){
 const label=el('label',undefined,'field'),input=el('select');label.append(el('span',text));
 for(const [val,name] of options){const o=el('option',name);o.value=val;input.append(o);}input.value=value;input.setAttribute('aria-label',text);
 const key=['phase_preset','phase_night','phase_night_release','bathroom_day_policy','hvac_intent','bathroom_timing','area_type'].find(k=>t(k)===text);
 const help=key?el('small',undefined,'hint selection-help'):null;
 const update=()=>{if(help)help.textContent=t('help_'+key+'_'+input.value);};
 if(help){help.id='selection-help-'+(++helpId);help.setAttribute('aria-live','polite');input.setAttribute('aria-describedby',help.id);update();}
 input.onchange=()=>{update();onChange(input.value);changed();};label.append(input);if(help)label.append(help);return label;
}

function input(text,value,type,onChange){const label=el('label',undefined,'field'),control=el('input');control.type=type;control.value=value??'';control.oninput=()=>{onChange(control.value);changed();};label.append(el('span',text),control);return label;}
function updateAvailability(){
 for(const box of document.querySelectorAll('[data-entity-id]')){const e=data.inventory.entities.find(v=>v.id===box.dataset.entityId);if(e)box.querySelector('span:not(.ha-assigned-icon)').textContent=`${e.name} · ${e.entity_id} · ${t(e.disabled?'disabled':e.available?'available':'unavailable')}`;}
}
function syncLabel(){ $('sync').textContent=offline?t('offline'):`${t('synced')}: ${new Date(data.observed_at).toLocaleTimeString(language)} · ${data.inventory.areas.length} / ${data.inventory.entities.length}`; }
let stage='select',activeRoom=null,showAll=false,allRoom=false,allBathrooms=false,areaFilter='all',labelsOpen=false,phaseOpen=false,hvacOpen=false,returnToRoom=null,labelFilters=emptyLabelFilters();
const setup=r=>r.setup??={status:r.enabled?'ready':'draft',service:!r.purposes.length,home:false,bathroom_timing:Object.fromEntries(r.shared_areas.map(a=>[a,'use_window']))};
const selectedRooms=()=>Object.keys(draft).filter(a=>draft[a].enabled);
function button(key,action,primary=false){const b=el('button',t(key),primary?'primary':'');b.type='button';b.disabled=saving;b.onclick=action;return b;}
function go(next,id=null){stage=next;activeRoom=id;showAll=false;allRoom=false;allBathrooms=false;hvacOpen=false;renderRooms();const heading=$('wizard-heading');heading?.focus();heading?.scrollIntoView({block:'start'});}
function roomName(id){return data.inventory.areas.find(a=>a.id===id)?.name??id;}
function markDraft(id){setup(draft[id]).status='draft';for(const [other,r] of Object.entries(draft))if(r.shared_areas.includes(id)&&r.enabled)setup(r).status='draft';}
function mutate(id,fn){fn();markDraft(id);changed();}
async function finishRoom(skip=false){
 if(saving)return;
 const r=draft[activeRoom],s=setup(r);
 if(!skip){
  const problems=roomProblems(r,draft);
  if(problems.length)return wizardError(problems[0]);
 }
 if(skip)markDraft(activeRoom);else s.status='ready';changed();
 if(!await save()){s.status='draft';renderRooms();return;}
 if(returnToRoom){const previous=returnToRoom;returnToRoom=null;go('room',previous);return;}
 const ids=selectedRooms(),index=ids.indexOf(activeRoom);go(index+1<ids.length?'room':'summary',ids[index+1]);
}
function wizardError(key){saveError=key;updateRoomFeedback();const box=$('wizard-error');box.textContent='⚠ '+t(key);box.hidden=false;box.focus();box.scrollIntoView({block:'nearest'});}
function saveProblems(){return [...new Set([...(needsReview?['changed']:[]),...(staleSettings?['stale_household']:[]),...(offline?['offline_save']:[]),...(saveError?[saveError]:[])])];}
function feedbackBox(aid){const box=el('div');box.dataset.roomFeedback=aid;box.setAttribute('aria-live','polite');return box;}
function updateRoomFeedback(){
 if(!data||!draft)return;
 const error=$('wizard-error');if(error){error.hidden=!saveError;error.textContent=saveError?'⚠ '+t(saveError):'';}
 for(const box of document.querySelectorAll('[data-room-feedback]')){
  const aid=box.dataset.roomFeedback,r=draft[aid];if(!r)continue;
  const problems=[...new Set([...saveProblems(),...roomProblems(r,draft),...(!data.inventory.areas.some(a=>a.id===aid)?['missing_area']:[])])];
  const state=problems.length?'blocked':setup(r).status==='ready'?'ready':'draft';
  const signature=JSON.stringify([language,state,problems]);if(box.dataset.signature===signature)continue;
  box.dataset.signature=signature;box.className='room-feedback '+state;box.replaceChildren();
  box.append(el('strong',(state==='blocked'?'⚠ ':state==='ready'?'✓ ':'○ ')+t('room_'+state)));
  if(problems.length){const list=el('ul');for(const key of problems)list.append(el('li',t(key)));box.append(list);}
  else if(state==='draft')box.append(el('p',t('draft_help')));
  if(needsReview)box.append(button('refresh',()=>refresh(true)));
 }
}

function drawRole(host,aid,role){
 const room=draft[aid],selected=room.roles[role],field=el('fieldset');field.append(el('legend',t(role)));
 const candidates=roleCandidates(data.inventory,room,aid,role,labelFilters,{allRoom,allAreas:showAll});
 if(!candidates.length)field.append(el('p',t('none_found'),'hint'));
 for(const e of candidates){
  const owner=Object.entries(draft).find(([a,r])=>r.enabled&&Object.entries(r.roles).some(([key,ids])=>ids.includes(e.id)&&(a!==aid||key!==role)));
  const box=checkbox(`${e.name} · ${e.entity_id} · ${t(e.disabled?'disabled':e.available?'available':'unavailable')}`,selected.includes(e.id),v=>{mutate(aid,()=>room.roles[role]=v?[...room.roles[role],e.id]:room.roles[role].filter(x=>x!==e.id));renderRooms();});
  box.prepend(haIcon(e.icon,e.domain==='climate'?'mdi:thermostat':'mdi:lightbulb-outline'));box.dataset.entityId=e.id;box.querySelector('input').id='role-'+role+'-'+e.id;box.querySelector('input').disabled=!selected.includes(e.id)&&(e.disabled||!!owner);
  field.append(box);if(owner)field.append(el('small',`${t('assigned_to')}: ${roomName(owner[0])}`,'hint'));
 }
 for(const id of selected.filter(id=>!data.inventory.entities.some(e=>e.id===id)))field.append(checkbox(`${t('missing_choice')} · ${id}`,true,()=>{mutate(aid,()=>room.roles[role]=room.roles[role].filter(x=>x!==id));renderRooms();}));
 host.append(field);
}
function drawHvac(card,aid){
 const room=draft[aid],h=room.hvac,entities=room.roles.hvac.map(id=>data.inventory.entities.find(e=>e.id===id)).filter(Boolean);
 const section=el('details');section.id='wizard-hvac';section.open=hvacOpen||h.mode!=='none';section.append(el('summary',t('hvac')),el('p',t('hvac_help'),'hint'));drawRole(section,aid,'hvac');
 const common=key=>entities.length?entities[0].capabilities[key].filter(v=>entities.every(e=>e.capabilities[key].includes(v))):[];
 const intent=['none','preserve'].includes(h.mode)?h.mode:'profile';
 section.append(select(t('hvac_intent'),intent,['none','preserve','profile'].map(v=>[v,t(v)]),v=>{mutate(aid,()=>h.mode=v);renderRooms();}));
 if(intent==='preserve'){
  section.append(el('p',t('preserve_help'),'hint'));
  for(const e of entities)section.append(el('small',`${e.name}: ${t(e.power_support?.turn_on&&e.power_support?.turn_off?'native_power_advertised':'native_power_unknown')}`,'hint'));
 }
 if(intent==='profile'){
 section.append(select(t('mode'),h.mode,[['profile',t('choose')],...common('modes').filter(v=>v!=='off').map(v=>[v,t(v)])],v=>{mutate(aid,()=>h.mode=v);renderRooms();}));
 section.append(button('copy_current',()=>{
  const values=entities.map(e=>e.current),v=values[0];
  if(!entities.length||entities.some(e=>!e.available)||!v||!['heat','cool'].includes(v.mode)||!Number.isFinite(v.temperature)||!common('fan_modes').includes(v.fan_mode)||values.some(x=>!x||x.mode!==v.mode||x.temperature!==v.temperature||x.fan_mode!==v.fan_mode))return wizardError('current_unusable');
  mutate(aid,()=>Object.assign(h,{mode:v.mode,temperature:v.temperature,fan_mode:v.fan_mode}));renderRooms();
 }));
 for(const e of entities)if(e.current)section.append(el('small',`${e.name}: ${t(e.current.mode??'unknown')} · ${e.current.temperature??'—'}°${e.capabilities.unit??''} · ${e.current.fan_mode??'—'} · ${new Date(e.current.observed_at).toLocaleTimeString(language)}`,'hint'));
  const temp=input(t('temperature'),h.temperature,'number',v=>mutate(aid,()=>h.temperature=v===''?null:Number(v)));const control=temp.querySelector('input');control.step='any';if(entities.length){control.min=Math.max(...entities.map(e=>e.capabilities.min_temperature));control.max=Math.min(...entities.map(e=>e.capabilities.max_temperature));}
  section.append(temp,select(t('fan_mode'),h.fan_mode??'',[['',t('choose')],...common('fan_modes').map(v=>[v,v])],v=>mutate(aid,()=>h.fan_mode=v||null)));
 }
 if(intent!=='none'){const lead=input(t('lead_minutes'),h.lead_minutes,'text',()=>{});offsetControl(lead.querySelector('input'),h.lead_minutes,0,240,v=>mutate(aid,()=>h.lead_minutes=v),t('offset_invalid'));section.append(lead);}
 card.append(section);
}
function viewToggle(key,value,fn){const box=checkbox(t(key),value,fn);box.querySelector('input').onchange=e=>{fn(e.target.checked);renderRooms();};return box;}
function drawLabels(root){
 const section=el('details',undefined,'card');section.id='label-setup';section.open=stage==='select'||labelsOpen;section.append(el('summary',t('label_setup')),el('p',t('label_help')));
 for(const role of labelRoles){
  const value=labelFilters[role],options=[['',t('no_label')],...(data.inventory.labels??[]).map(l=>[l.id,l.name])];
  if(value&&!options.some(([id])=>id===value)){options.push([value,`${t('missing_label')}: ${value}`]);section.append(el('p',`${t('label_'+role)}: ${t('missing_label_help')}`,'error'));}
  const field=select(t('label_'+role),value??'',options,v=>{labelFilters[role]=v||null;renderRooms();});field.querySelector('select').id='label-'+role;section.append(field);
 }
 const tips=el('a',t('setup_tips'));tips.href='./tips.html';tips.target='_blank';tips.rel='noopener';section.append(tips);root.append(section);
}
function drawPhases(card,aid){
 const r=draft[aid],s=setup(r),p=phases(r),section=el('details');section.id='phase-controls';section.open=phaseOpen||areaType(r)==='hallway';
 section.append(el('summary',t('phase_title')),el('p',t('phase_bedroom_help'),'hint'),el('p',t('phase_help'),'hint'));
 const set=(key,value)=>{mutate(aid,()=>s.phases={...p,[key]:value});renderRooms();};
 if(areaType(r)==='hallway')section.append(el('p',t('hallway_help'),'hint'));
 section.append(el('p',t('help_phase_preset'),'hint'));const guide=el('a',t('setup_tips'));guide.href='./tips.html';guide.target='_blank';guide.rel='noopener';section.append(guide);
 section.append(select(t('phase_preset'),'custom',['custom','none','background','kitchen','hallway','access','circulation'].map(k=>[k,t('phase_'+k)]),v=>{
  const presets={none:{night:'none',morning:false,evening_main:false},background:{night:'after_use',night_end:-60,morning:false,evening_main:false},kitchen:{night:'home',night_start:360,night_end:120,morning:true,morning_start:120,evening_main:true},hallway:{night_main_off:true,night:'home',night_start:0,night_end:-60,morning:false,evening_main:false,constant_main:false,night_release:'planner'},access:{night:'none',constant_main:true,morning:false,evening_main:false,night_release:'planner'},circulation:{night_main_off:true,night:'entertaining',constant_main:false,evening_main:true,morning:true,morning_start:120,morning_end:240,night_end:-60,night_release:'planner'}};
  if(presets[v]){presetNotes[aid]=v;mutate(aid,()=>s.phases={...p,night_main_off:false,constant_main:false,morning_end:null,night_release:'planner',...presets[v]});renderRooms();}
 }));
 if(presetNotes[aid])section.append(el('p',t('phase_'+presetNotes[aid])+': '+t('help_phase_preset_'+presetNotes[aid]),'hint selection-help'));
 section.append(select(t('phase_night'),p.night,['none','after_use','home','entertaining'].map(k=>[k,t('phase_night_'+k)]),v=>{mutate(aid,()=>s.phases={...p,night:v,night_release:'planner'});renderRooms();}));
 const number=(key,min,max)=>{const field=input(t('phase_'+key),p[key],'number',v=>mutate(aid,()=>s.phases={...(s.phases??p),[key]:Number(v)}));offsetControl(field.querySelector('input'),p[key],min,max,v=>mutate(aid,()=>s.phases={...(s.phases??p),[key]:v}),t('offset_invalid'));section.append(field);};
 section.append(checkbox(t('phase_constant_main'),p.constant_main,v=>set('constant_main',v)));
 if(p.night==='entertaining')section.append(el('p',t('phase_entertaining_help'),'hint'),checkbox(t('phase_evening_main'),p.evening_main,v=>set('evening_main',v)));
 if(['home','entertaining'].includes(p.night))section.append(select(t('phase_night_release'),p.night_release,['planner','existing'].map(k=>[k,t('phase_release_'+k)]),v=>set('night_release',v)),el('p',t('phase_external_help'),'hint'));
 if(p.night==='home'){number('night_start',0,720);section.append(checkbox(t('phase_night_main_off'),p.night_main_off,v=>set('night_main_off',v)));section.append(checkbox(t('phase_evening_main'),p.evening_main,v=>set('evening_main',v)));}
 if(p.night!=='none'&&p.night_release==='planner')number('night_end',-180,360);
 section.append(checkbox(t('phase_morning'),p.morning,v=>set('morning',v)));if(p.morning){number('morning_start',0,360);section.append(checkbox(t('phase_morning_bounded'),p.morning_end!==null,v=>set('morning_end',v?Math.min(720,p.morning_start+120):null)));if(p.morning_end!==null)number('morning_end',0,720);}
 for(const kind of ['evening','daytime']){section.append(checkbox(t('phase_'+kind+'_meal'),p[kind+'_meal'],v=>{mutate(aid,()=>s.phases={...p,[kind+'_meal']:v,[kind+'_hvac']:mealHvac(r,kind)});renderRooms();}),checkbox(t('phase_'+kind+'_hvac'),mealHvac(r,kind),v=>set(kind+'_hvac',v)));}
 if(r.purposes.includes('recreation'))section.append(checkbox(t('phase_recreation_hvac'),p.recreation_hvac,v=>set('recreation_hvac',v)));
 section.append(el('p',t('phase_hvac_help'),'hint'));
 card.append(section);
}
function drawBathroomLighting(card,aid){
 const s=setup(draft[aid]),policy=s.lighting??{mode:'always',off_after_sunrise:180,on_before_sunset:120,night_enabled:false,night_after_candles:360,morning_after_sunrise:0};
 const change=(key,value)=>{mutate(aid,()=>s.lighting={...policy,[key]:value});renderRooms();};
 card.append(el('h3',t(isBathroom(draft[aid])?'bathroom_lighting':'area_lighting')),el('p',t('area_lighting_help'),'hint'));
 card.append(select(t('bathroom_day_policy'),policy.mode,['always','daylight'].map(v=>[v,t('bathroom_'+v)]),v=>change('mode',v)));
 const number=(key,max)=>{const field=input(t('bathroom_'+key),policy[key],'number',v=>mutate(aid,()=>s.lighting={...(s.lighting??policy),[key]:Number(v)}));const control=field.querySelector('input');offsetControl(control,policy[key],0,max,v=>mutate(aid,()=>s.lighting={...(s.lighting??policy),[key]:v}),t('offset_invalid'));card.append(field);};
 if(policy.mode==='daylight'){number('off_after_sunrise',360);number('on_before_sunset',360);}
 if(isBathroom(draft[aid]))card.append(checkbox(t('bathroom_night_enabled'),policy.night_enabled,v=>change('night_enabled',v)));
 if(isBathroom(draft[aid])&&policy.night_enabled){number('night_after_candles',720);number('morning_after_sunrise',180);}
}
function renderRooms(){
 const focused=document.activeElement?.id;phaseOpen=$('phase-controls')?.open??phaseOpen;labelsOpen=$('label-setup')?.open??labelsOpen;hvacOpen=$('wizard-hvac')?.open??hvacOpen;
 restOpen=$('rest-controls')?.open??restOpen;const root=$('rooms');root.replaceChildren();$('weekly-planning').hidden=stage!=='summary';
 const known=new Set(data.inventory.areas.map(a=>a.id));
 const areas=[...data.inventory.areas,...Object.keys(draft).filter(id=>!known.has(id)).map(id=>({id,name:id}))];
 for(const [id,r] of Object.entries(draft))setup(r);
 if(stage==='room'&&!draft[activeRoom]?.enabled){stage='select';activeRoom=null;}
 const title=el('h2',t(stage==='select'?'select_rooms':stage==='summary'?'review_setup':'configure_room'));title.id='wizard-heading';title.tabIndex=-1;root.append(title);
 const error=el('p',saveError?'⚠ '+t(saveError):undefined,'room-feedback blocked');error.hidden=!saveError;error.id='wizard-error';error.tabIndex=-1;error.setAttribute('role','alert');root.append(error);drawLabels(root);root.append(checkbox(t('post_shutoff'),postShutoff,v=>postShutoff=v),el('p',t('post_shutoff_help'),'hint'));
 if(stage==='select'){
  root.append(el('p',t('selection_help')));
  const areaChoice=select(t('area_filter'),areaFilter,['all','bedroom','common_area'].map(k=>[k,t('area_filter_'+k)]),v=>{areaFilter=v;renderRooms();});areaChoice.querySelector('select').onchange=e=>{areaFilter=e.target.value;renderRooms();};root.append(areaChoice);const grid=el('div',undefined,'room-selection');
  for(const area of filteredAreas(areas,draft,labelFilters,areaFilter)){const r=draft[area.id]??=defaults();const label=`${area.name} · ${data.inventory.floors.find(f=>f.id===area.floor_id)?.name??t('no_floor')}`;const choice=checkbox(label,r.enabled,v=>{mutate(area.id,()=>{r.enabled=v;const kinds=suggestedAreaTypes(area,labelFilters);if(v&&!r.setup?.area_type&&!r.purposes.length&&!Object.values(r.roles).some(ids=>ids.length)&&kinds.length===1)draft[area.id]=classifyRoom(r,kinds[0]);});renderRooms();},'area-'+area.id);choice.prepend(haIcon(area.icon));grid.append(choice);}
  root.append(grid,button('start_setup',async()=>{if(!selectedRooms().length)return wizardError('select_one');if(await save()){const ids=selectedRooms();go('room',ids.find(id=>setup(draft[id]).status!=='ready')??ids[0]);}},true),button('review_setup',()=>go('summary')));
 }else if(stage==='room'){
  const aid=activeRoom,r=draft[aid],s=setup(r),ids=selectedRooms(),card=el('section',undefined,'card');
  card.append(el('p',`${t('room_progress')} ${ids.indexOf(aid)+1} / ${ids.length}`,'hint'),el('h3',roomName(aid)),feedbackBox(aid));
  if(!known.has(aid))card.append(el('p',t('missing_area'),'error'));
  card.querySelector('h3')?.prepend(haIcon(areas.find(a=>a.id===aid)?.icon));
  card.append(el('p',t('purpose_help')));
  const types=suggestedAreaTypes(areas.find(a=>a.id===aid)??{},labelFilters);
  if(types.length===1)card.append(el('p',`${t('suggested_type')}: ${t('area_type_'+types[0])}`,'hint'),button('apply_area_type',()=>{mutate(aid,()=>draft[aid]=classifyRoom(r,types[0]));phaseOpen=true;renderRooms();}));
  else if(types.length>1)card.append(el('p',t('conflicting_area_labels'),'room-feedback draft'));
  const suggestions=suggestedPurposes(areas.find(a=>a.id===aid)??{},labelFilters);if(suggestions.length){card.append(el('p',`${t('label_suggestions')}: ${suggestions.map(t).join(', ')}`,'hint'),button('apply_suggestions',()=>{mutate(aid,()=>r.purposes=[...new Set([...r.purposes,...suggestions])]);renderRooms();}));}
  for(const purpose of ['sleeping','recreation'])card.append(checkbox(t(purpose),r.purposes.includes(purpose),v=>mutate(aid,()=>r.purposes=v?[...r.purposes,purpose]:r.purposes.filter(p=>p!==purpose))));
  card.append(select(t('area_type'),areaType(r),['room','common','bathroom','hallway',...(areaType(r)==='legacy'?['legacy']:[])].map(k=>[k,t('area_type_'+k)]),v=>{mutate(aid,()=>draft[aid]=classifyRoom(r,v));phaseOpen=true;renderRooms();}),el('p',t('area_type_help'),'hint'));
  const advanced=el('details');advanced.append(el('summary',t('profile_details')),el('p',t('profile_help')));card.append(advanced);
  card.append(viewToggle('all_room_entities',allRoom,v=>allRoom=v),viewToggle('all_entities',showAll,v=>showAll=v),el('p',t('filter_help'),'hint'));
  drawRole(card,aid,'main_lights');drawRole(card,aid,'night_lights');drawHvac(card,aid);drawPhases(card,aid);
  drawBathroomLighting(card,aid);
  if(r.purposes.includes('sleeping')){
   const rest=el('details');rest.id='rest-controls';rest.open=restOpen;rest.append(el('summary',t('rest_defaults')),el('p',t('rest_defaults_help'),'hint'));
   const values={nap_after_sunrise:480,nap_duration:120,lead_minutes:r.hvac.lead_minutes,late_wake_after_sunrise:240,nap_start_mode:'sunrise',nap_start_time:'14:00',nap_end_mode:'duration',nap_end_time:'16:00',wake_mode:'sunrise',wake_time:'11:00',...s.rest_defaults};
   const update=(key,value)=>{mutate(aid,()=>s.rest_defaults={...values,[key]:value});};
   const mode=(key,choices)=>rest.append(select(t('rest_'+key),values[key],choices.map(v=>[v,t('rest_choice_'+v)]),v=>{update(key,v);renderRooms();}));
   const clock=key=>rest.append(input(t('rest_'+key),values[key],'time',v=>update(key,v)));
   const duration=(key,min,max)=>{const label=input(t('rest_'+key),values[key],'text',()=>{});offsetControl(label.querySelector('input'),values[key],min,max,v=>update(key,v),t('offset_invalid'));rest.append(label);};
   mode('nap_start_mode',['sunrise','clock']);if(values.nap_start_mode==='clock')clock('nap_start_time');else duration('nap_after_sunrise',0,720);
   mode('nap_end_mode',['duration','clock','period_end']);if(values.nap_end_mode==='clock')clock('nap_end_time');else if(values.nap_end_mode==='duration')duration('nap_duration',15,480);
   duration('lead_minutes',0,240);mode('wake_mode',['sunrise','clock']);if(values.wake_mode==='clock')clock('wake_time');else duration('late_wake_after_sunrise',0,720);
   rest.append(el('p',t('rest_clock_help'),'hint'));card.append(rest);
  }

  if(s.service){
   card.append(checkbox(t('when_home'),s.home,v=>mutate(aid,()=>s.home=v)),el('p',t('home_help'),'hint'));
   const links=Object.entries(draft).filter(([id,room])=>room.enabled&&room.shared_areas.includes(aid));card.append(el('p',`${t('linked_rooms')}: ${links.map(([id])=>roomName(id)).join(', ')||t('none_linked')}`));
   if(isBathroom(r)&&r.shared_areas.length)card.append(button('remove_links',()=>{mutate(aid,()=>{r.shared_areas=[];s.bathroom_timing={};});renderRooms();}));
  }
  if(!isBathroom(r)){
   card.append(el('h3',t('bathroom_question')),el('p',t('bathroom_help'),'hint'));
   card.append(viewToggle('all_bathrooms',allBathrooms,v=>allBathrooms=v),el('p',t('bathroom_filter_help'),'hint'));
   const add=select(t('add_bathroom'),'', [['',t('none_later')],...bathroomCandidates(data.inventory,aid,r.shared_areas,labelFilters,allBathrooms).map(a=>[a.id,a.name])],id=>{if(!id)return;mutate(aid,()=>{r.shared_areas.push(id);s.bathroom_timing[id]='whole_observance';const bath=draft[id]??=defaults();bath.enabled=true;if(!setup(bath).area_type)setup(bath).service=true;});renderRooms();});card.append(add);
   for(const id of r.shared_areas){const bath=draft[id],link=el('section',undefined,'bathroom-link');link.append(el('strong',roomName(id)),feedbackBox(id),
    select(t('bathroom_timing'),s.bathroom_timing[id]??'use_window',['use_window','whole_observance'].map(v=>[v,t(v)]),v=>mutate(aid,()=>s.bathroom_timing[id]=v)),
    button('configure_bathroom',async()=>{if(await save()){returnToRoom=aid;go('room',id);}}),button('remove_link',()=>{mutate(aid,()=>{r.shared_areas=r.shared_areas.filter(a=>a!==id);delete s.bathroom_timing[id];});renderRooms();}));card.append(link);}
  }
  const nav=el('div',undefined,'toolbar');nav.append(button('back',()=>{const i=ids.indexOf(aid);go(i>0?'room':'select',ids[i-1]);}),button('save_next',()=>finishRoom(),true),button('skip_room',()=>finishRoom(true)),button('review_setup',()=>go('summary')));card.append(feedbackBox(aid),nav);root.append(card);
 }else{
  const ids=selectedRooms(),ready=ids.filter(id=>setup(draft[id]).status==='ready');root.append(el('p',`${ready.length} / ${ids.length} ${t('rooms_ready')}`),el('p',t('summary_help')));
  for(const id of ids){const r=draft[id],s=setup(r),card=el('section',undefined,'card');card.append(el('h3',roomName(id)),feedbackBox(id),el('p',[...r.purposes.map(t),t('area_type_'+areaType(r))].join(' · ')));
   card.querySelector('h3').prepend(haIcon(data.inventory.areas.find(a=>a.id===id)?.icon));
   for(const role of ['main_lights','night_lights','hvac'])if(r.roles[role].length){const row=el('p',t(role)+': ');for(const rid of r.roles[role]){const e=data.inventory.entities.find(e=>e.id===rid);const name=el('span',e?.name??rid);name.prepend(haIcon(e?.icon,role==='hvac'?'mdi:thermostat':'mdi:lightbulb-outline'));row.append(name,document.createTextNode(' '));}card.append(row);}
   card.append(el('p',`${t('hvac')}: ${t(r.hvac.mode)}${r.hvac.mode==='none'?'':r.hvac.mode==='preserve'?` · ${r.hvac.lead_minutes} ${t('minutes_early')}`:` · ${r.hvac.temperature} · ${r.hvac.fan_mode} · ${r.hvac.lead_minutes} ${t('minutes_early')}`}`));
   const phase=phases(r);if(phase.constant_main)card.append(el('p',t('phase_constant_main')));for(const k of ['evening','daytime'])if(mealHvac(r,k))card.append(el('p',t('phase_'+k+'_hvac')));if(phase.night_release==='existing')card.append(el('p',t('phase_external_help'),'hint'));card.append(el('p',`${t('phase_title')}: ${t('phase_night_'+phase.night)}${phase.morning?' · '+t('phase_morning'):''}${phase.evening_meal?' · '+t('phase_evening_meal'):''}${phase.daytime_meal?' · '+t('phase_daytime_meal'):''}`));
   {const p=s.lighting;card.append(el('p',`${t(isBathroom(r)?'bathroom_lighting':'area_lighting')}: ${t('bathroom_'+(p?.mode??'always'))}${p?.night_enabled?' · '+t('bathroom_night_enabled'):''}`));}
   if(r.hvac.mode==='preserve')card.append(el('p',t('preserve_help'),'hint'));
   for(const a of r.shared_areas)card.append(el('p',`${roomName(a)} · ${t(s.bathroom_timing[a]??'use_window')}`));if(s.home)card.append(el('p',t('when_home')));
   card.append(button('edit_room',()=>go('room',id)));root.append(card);
  }
  root.append(button('select_rooms',()=>go('select')));
 }
 updateRoomFeedback();$('issues').replaceChildren();for(const item of data.issues)$('issues').append(el('p',`${t(item.code)} · ${item.id}`,'error'));
 $('unassigned').replaceChildren();const details=el('details');details.append(el('summary',`${data.inventory.entities.filter(e=>!e.area_id).length}`));
 for(const e of data.inventory.entities.filter(e=>!e.area_id))details.append(el('p',`${e.name} · ${e.entity_id}`));$('unassigned').append(details);if(focused)$(focused)?.focus({preventScroll:true});
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
  for(const seg of snap.segments){const row=el('section',undefined,'card');row.append(el('strong',t(seg.kind)),el('p',`${t('candles')}: ${format(seg.candle_lighting)}`),el('p',`${t('sunrise')}: ${format(seg.sunrise)}`),el('p',`${t('segment_end')}: ${format(seg.end)}`));if(seg.sunset)row.append(el('p',`${t('sunset')}: ${format(seg.sunset)}`));root.append(row);}
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
  if(!data||discard||!dirty){const iconChanged=data&&JSON.stringify([data.inventory.areas.map(a=>a.icon),data.inventory.entities.map(e=>e.icon)])!==JSON.stringify([next.inventory.areas.map(a=>a.icon),next.inventory.entities.map(e=>e.icon)]);const redraw=!data||discard||changedInventory||staleSaved||iconChanged;if(redraw){draft=structuredClone(next.settings.rooms);labelFilters={...emptyLabelFilters(),...next.settings.label_filters};postShutoff=next.settings.post_shutoff??false;dirty=false;needsReview=false;staleSettings=false;saveError=null;}data=next;if(redraw)render();}
  else if(staleSaved){offline=false;staleSettings=true;status('stale_household');updateRoomFeedback();return;}
  else {data=next;if(manual){needsReview=false;saveError=null;renderRooms();status('inventory_reviewed');}else if(changedInventory){needsReview=true;status('changed');}}
  offline=false;updateAvailability();syncLabel();updateRoomFeedback();
 }catch{offline=true;syncLabel();updateRoomFeedback();}
}
async function save(){if(document.querySelector('#rooms input:invalid')){document.querySelector('#rooms input:invalid').reportValidity();return false;}
 if(needsReview||staleSettings||offline){wizardError(needsReview?'changed':staleSettings?'stale_household':'offline_save');return false;}if(saving)return false;
 saving=true;$('save').disabled=true;const payload=structuredClone(draft);
 // Freeze controls while a write is pending so late edits cannot be lost.
 const controls=[...document.querySelectorAll('#rooms input,#rooms select,#rooms button,#language,#refresh,#discard')];
 const disabled=controls.map(c=>c.disabled);controls.forEach(c=>c.disabled=true);
 try{data=await api('household',{revision:data.settings.revision,inventory_revision:data.inventory.revision,rooms:payload,label_filters:structuredClone(labelFilters),post_shutoff:postShutoff});draft=structuredClone(data.settings.rooms);labelFilters={...emptyLabelFilters(),...data.settings.label_filters};postShutoff=data.settings.post_shutoff??false;dirty=false;needsReview=false;staleSettings=false;saveError=null;status('saved');updateRoomFeedback();return true;}
 catch(e){fail(e);wizardError(catalogs[language][e.message]?e.message:'error');return false;}
 finally{saving=false;$('save').disabled=false;controls.forEach((c,i)=>c.disabled=disabled[i]);}
}
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
 const rooms=Object.values(data.settings.rooms).filter(r=>r.enabled&&(r.setup?.status??'ready')==='ready'&&(r.purposes.length||r.setup?.home||phases(r).night==='home'||phases(r).morning||phases(r).evening_meal||phases(r).daytime_meal||mealHvac(r,'evening')||mealHvac(r,'daytime')||phases(r).constant_main||phases(r).night==='entertaining'));
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
 data=await api('household');draft=structuredClone(data.settings.rooms);labelFilters={...emptyLabelFilters(),...data.settings.label_filters};postShutoff=data.settings.post_shutoff??false;const ids=selectedRooms();if(ids.length){activeRoom=ids.find(id=>setup(draft[id]).status!=='ready');stage=activeRoom?'room':'summary';}calendar=await api('calendar');
 try{automatic=await api('upcoming');}catch{automatic={status:'unavailable',error:'calendar_unavailable'};}
 dateValues.candles=calendar.values?.candle_lighting?.value??'';dateValues.end=calendar.values?.end?.value??'';
 const rise=calendar.values?.sunrise?.value;if(rise&&new Date(rise)>new Date(dateValues.candles)&&new Date(rise)<new Date(dateValues.end))dateValues.sunrise=rise;
 $('calendar-refresh').onclick=refreshCalendar;$('manual-calendar').onchange=e=>setManualCalendar(e.target.checked);
 $('language').onchange=()=>{language=$('language').value;render();};$('refresh').onclick=()=>refresh(true);$('discard').onclick=()=>refresh(true,true);$('save').onclick=save;$('plan').onclick=openPlan;render();
 setInterval(()=>{if(!document.hidden)refresh();},15000);window.addEventListener('focus',()=>refresh());
 window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
 }catch{$('status').textContent='Unable to load HA household. / לא ניתן לטעון את הבית מ־HA.';}}
boot();
