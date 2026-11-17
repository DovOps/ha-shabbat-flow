import {request as fetch} from './transport.mjs';
import {translate,localeMetadata,localTime} from './model.mjs';
import {PERIOD_DRAFT_KEY,parsePeriodDraft,availableProfiles,nextId,dayHomeState,setDayHome,setRoomChoice,copyPreviousDay,resolveWindowTime,localDateTimeValue,localDateTimeCandidates} from './period-model.mjs';
const householdMode=new URLSearchParams(location.search).get('household')==='1';
let bundle,initial,catalogs,result=null,revision=0,lastMessage=null,activeDay=null,pendingCopy=null,calendarData=null;
const draftKey=householdMode?'shabbat-flow-household-draft-v2':PERIOD_DRAFT_KEY;
const $=id=>document.getElementById(id);
const lang=()=>bundle?.plan.language||'en';
const t=key=>translate(catalogs,lang(),key);
function node(tag,text,className){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;}
function message(key,error=false){lastMessage={key,error};$('status').textContent=t(key);$('status').className=error?'error':'';}
function error(error){const key='error_'+error.message;message(Object.hasOwn(catalogs[lang()],key)?key:'error_internal',true);}
function changed(){pendingCopy=null;revision++;result=null;$('export').disabled=true;$('timeline').replaceChildren();message('period_dirty');}
function button(key,fn){const n=node('button',t(key));n.type='button';n.addEventListener('click',fn);return n;}
function field(key,value,fn,options,sourceRole){
  const label=node('label',undefined,'field');label.append(node('span',t(key)));
  const input=node(options?'select':'input');
  const dateField=!options&&['window_start','window_end','preparation_start','candle_lighting','sunrise_anchor'].includes(key);
  if(options)for(const [val,text] of options){const option=node('option',text);option.value=val;input.append(option);}
  else{input.type=dateField?'datetime-local':'text';input.maxLength=100;input.dir='ltr';if(dateField)input.step='1';}
  if(dateField){
    try{input.value=localDateTimeValue(value,bundle.plan.snapshot.timezone);}catch{input.value='';}
    input.required=true;
    const choices=node('select');choices.hidden=true;choices.setAttribute('aria-label',t('choose_clock_offset'));
    input.addEventListener('input',()=>{
      let matches=[];try{matches=localDateTimeCandidates(input.value,bundle.plan.snapshot.timezone);}catch{}
      choices.replaceChildren();choices.hidden=matches.length<2;
      if(matches.length===1){input.setCustomValidity('');fn(matches[0]);}
      else{
        fn('');input.setCustomValidity(t(matches.length?'choose_clock_offset':'invalid_local_clock'));
        if(matches.length>1){const first=node('option',t('choose_clock_offset'));first.value='';choices.append(first);for(const iso of matches){const option=node('option',iso.slice(-6));option.value=iso;choices.append(option);}}
      }
      changed();
    });
    choices.addEventListener('change',()=>{if(choices.value){input.setCustomValidity('');fn(choices.value);changed();}});
    label.append(input,node('small',bundle.plan.snapshot.timezone,'hint'),choices);
    const role=sourceRole??({candle_lighting:'candle_lighting',sunrise_anchor:'sunrise'}[key]);
    const source=calendarData?.values?.[role];
    if(source?.status==='available')label.append(button('use_calendar_value',()=>{fn(source.value);changed();render();}),node('small',`${safeTime(source.value)} · ${source.entity_id}`,'hint'));
  }else{
    input.value=value;input.addEventListener(options?'change':'input',()=>{fn(input.value);changed();});label.append(input);
  }
  return label;
}
function options(keys){return keys.map(k=>[k,t(k)]);}
function section(key){const n=node('section',undefined,'card');n.append(node('h2',t(key)));return n;}
function remove(items,item){items.splice(items.indexOf(item),1);changed();render();}
function windowFields(parent,item){parent.append(field('window_start',item.start,v=>item.start=v),field('window_end',item.end,v=>item.end=v));}
function groupPicker(parent,item){
  const details=node('details');details.append(node('summary',t('selected_groups')));
  for(const [id,group] of Object.entries(bundle.config.groups)){
    if(group.activation==='home')continue;
    const label=node('label',undefined,'toggle');label.append(node('span',group.label[lang()]));
    const input=node('input');input.type='checkbox';input.checked=item.groups.includes(id);
    input.addEventListener('change',()=>{item.groups=input.checked?[...item.groups,id]:item.groups.filter(v=>v!==id);changed();});
    label.append(input);details.append(label);
  }
  parent.append(details);
}
function roomRow(use){
  const row=node('div',undefined,'period-item');
  row.append(field('room_label',use.room,v=>{
    use.room=v;use.profile=availableProfiles(bundle.config,v,use.purpose)[0]?.[0]??null;
    use.control=use.profile?'planner':'existing';render();
  },Object.entries(bundle.config.rooms).map(([id,label])=>[id,label[lang()]])));
  const profiles=availableProfiles(bundle.config,use.room,use.purpose).map(([id,p])=>[id,p.label[lang()]]);
  row.append(field('profile_label',use.profile??'',v=>{use.profile=v||null;use.control=v?'planner':'existing';},[['',t('existing_control')],...profiles]));
  windowFields(row,use);row.append(button('remove_item',()=>remove(bundle.plan.room_uses,use)));return row;
}
function addUse(segment,purpose){
  const room=Object.keys(bundle.config.rooms)[0],profile=availableProfiles(bundle.config,room,purpose)[0]?.[0]??null;
  bundle.plan.room_uses.push({id:nextId('use',bundle.plan.room_uses),room,purpose,control:profile?'planner':'existing',profile,segment:segment.id,start:segment.start,end:segment.end});
  changed();render();
}
function applyChange(next){bundle=next;changed();render();}
function safeTime(iso){try{return localTime(iso,lang(),bundle.plan.snapshot.timezone);}catch{return t('dates_needed');}}
function dayLabel(segment,index){
  try{return new Intl.DateTimeFormat(lang(),{timeZone:bundle.plan.snapshot.timezone,weekday:'short',month:'short',day:'numeric'}).format(new Date(segment.sunrise));}
  catch{return `${t('period_day')} ${index+1}`;}
}
function openAdvanced(){const details=$('advanced-setup');details.open=true;details.scrollIntoView({block:'start',behavior:'smooth'});details.querySelector('summary').focus();}
function render(){
  document.documentElement.lang=lang();document.documentElement.dir=localeMetadata[lang()].direction;$('language').value=lang();
  document.querySelectorAll('[data-i18n]').forEach(n=>n.textContent=t(householdMode&&n.dataset.i18n==='period_notice'?'household_notice':n.dataset.i18n));
  if(lastMessage)message(lastMessage.key,lastMessage.error);
  const root=$('period-form');root.replaceChildren();
  const segments=bundle.plan.snapshot.segments;
  if(!segments.some(v=>v.id===activeDay))activeDay=segments[0].id;
  const segment=segments.find(v=>v.id===activeDay),index=segments.indexOf(segment);
  const nav=node('nav',undefined,'day-tabs');nav.setAttribute('aria-label',t('choose_day'));
  segments.forEach((day,i)=>{
    const tab=node('button',dayLabel(day,i));tab.type='button';tab.setAttribute('aria-pressed',String(day.id===activeDay));
    tab.addEventListener('click',()=>{activeDay=day.id;pendingCopy=null;render();});nav.append(tab);
  });root.append(nav);
  const main=section('family_plan');main.querySelector('h2').textContent=`${t(segment.kind)} · ${dayLabel(segment,index)}`;
  main.append(node('p',`${t('candle_lighting')}: ${safeTime(segment.candle_lighting)}`,'hint'));
  const state=dayHomeState(bundle.plan,segment),homeOptions=options(['home_state','away_state','unset']).map(([id,label])=>[id.replace('_state',''),label]);
  if(state==='custom')homeOptions.push(['custom',t('custom_windows')]);
  main.append(field('home_question',state,v=>{if(v!=='custom')applyChange(setDayHome(bundle,segment.id,v));},homeOptions));
  const dayUses=bundle.plan.room_uses.filter(v=>v.segment===segment.id),meals=bundle.plan.meals.filter(v=>v.segment===segment.id);
  if(state==='custom')main.append(button('review_custom',openAdvanced));
  if(state==='away'&&(dayUses.length||meals.some(v=>['family','hosting'].includes(v.choice)))){
    const notice=node('div',undefined,'inline-issue');notice.append(node('p',t('away_selection_conflict')),button('clear_away_choices',()=>{
      const next=structuredClone(bundle);next.plan.room_uses=next.plan.room_uses.filter(v=>v.segment!==segment.id);
      next.plan.meals.filter(v=>v.segment===segment.id&&v.choice!=='none').forEach(v=>v.choice='away');applyChange(next);
    }));main.append(notice);
  }
  if(index>0)main.append(button('copy_previous',async()=>{
    const token=revision;try{const candidate=copyPreviousDay(bundle,segment.id);const check=await validate(candidate);if(token!==revision||activeDay!==segment.id)return;pendingCopy={candidate,target:segment.id,check};render();}catch(e){if(token===revision)error(e);}
  }));
  if(pendingCopy?.target===segment.id){
    const review=node('div',undefined,'copy-review');review.append(node('h3',t('review_copy')),node('p',t('copy_explanation')));
    for(const use of pendingCopy.candidate.plan.room_uses.filter(v=>v.segment===segment.id))review.append(node('p',`${bundle.config.rooms[use.room][lang()]} · ${t(use.purpose)} · ${safeTime(use.start)} — ${safeTime(use.end)}`));
    for(const meal of pendingCopy.candidate.plan.meals.filter(v=>v.segment===segment.id))review.append(node('p',`${catalogs[lang()]['meal_'+meal.kind]??meal.kind}: ${t(meal.choice)} · ${safeTime(meal.start)}`));
    if(!pendingCopy.check.complete)review.append(node('p',t('period_incomplete'),'inline-issue'));
    review.append(button('apply_copy',()=>{const candidate=pendingCopy.candidate;candidate.plan.language=lang();applyChange(candidate);}),button('cancel_copy',()=>{pendingCopy=null;render();}));main.append(review);
  }
  root.append(main);
  for(const purpose of ['sleeping','recreation']){
    const panel=section(purpose),tiles=node('div',undefined,'room-tiles');
    for(const [room,label] of Object.entries(bundle.config.rooms)){
      const matches=dayUses.filter(v=>v.room===room&&v.purpose===purpose),use=matches[0];
      if(!matches.length&&!availableProfiles(bundle.config,room,purpose).length)continue;
      const tile=node('div',undefined,'room-tile'+(use?' selected':''));tile.append(node('h3',label[lang()]));
      const choices=[['off',t('not_used')],...availableProfiles(bundle.config,room,purpose).map(([id,p])=>[id,p.label[lang()]]),['existing',t('existing_control')]];
      const select=field('profile_label',use?(use.profile??'existing'):'off',v=>{try{applyChange(setRoomChoice(bundle,segment.id,room,purpose,v));}catch(e){error(e);}},choices);
      if(matches.length>1){select.querySelector('select').disabled=true;tile.append(node('p',t('custom_windows'),'hint'),button('review_custom',openAdvanced));}
      tile.append(select);
      if(use){
        tile.append(node('p',`${safeTime(use.start)} — ${safeTime(use.end)}`,'hint'));
        const custom=node('details');custom.append(node('summary',t('adjust_window')));windowFields(custom,use);tile.append(custom);
        const overlap=bundle.plan.room_uses.some(v=>v.id!==use.id&&v.room===room&&new Date(v.start)<new Date(use.end)&&new Date(use.start)<new Date(v.end));
        if(overlap){const notice=node('div',undefined,'inline-issue');notice.append(node('p',t('room_overlap_help')),button('adjust_window',()=>{custom.open=true;custom.querySelector('input').focus();}));tile.append(notice);}
      }
      tiles.append(tile);
    }
    panel.append(tiles);root.append(panel);
  }
  const mealPanel=section('meals_title'),mealTiles=node('div',undefined,'room-tiles');
  for(const meal of meals){
    const tile=node('div',undefined,'room-tile');tile.append(node('h3',catalogs[lang()]['meal_'+meal.kind]??meal.kind),
      field('meal_choice',meal.choice,v=>{meal.choice=v;changed();render();},options(['away','family','hosting','none','unset'])),node('p',`${safeTime(meal.start)} — ${safeTime(meal.end)}`,'hint'));
    const custom=node('details');custom.append(node('summary',t('adjust_window')));windowFields(custom,meal);tile.append(custom);mealTiles.append(tile);
  }
  mealPanel.append(mealTiles);if(!meals.length)mealPanel.append(node('p',t('issue_meals_missing'),'inline-issue'),button('review_custom',openAdvanced));root.append(mealPanel);
  const timing=node('details',undefined,'card');timing.append(node('summary',t('family_timing')),node('p',t('timing_scope'),'hint'));
  const visited=new Set();
  for(const use of dayUses.filter(v=>v.purpose==='sleeping'&&v.control==='planner')){
    const profile=bundle.config.profiles[use.profile];
    for(const groupId of profile.groups)for(const rule of bundle.config.groups[groupId].rules){
      const kind=rule.action.type==='hvac'&&rule.action.mode!=='off'?'bedroom_hvac':rule.action.type==='state'&&rule.action.state==='off'&&rule.end===null?'bedroom_lights':null;
      if(!kind||rule.start.anchor!=='candle_lighting'||visited.has(groupId+'/'+rule.id))continue;visited.add(groupId+'/'+rule.id);
      const row=node('label',undefined,'field');row.append(node('span',`${bundle.config.rooms[use.room][lang()]} · ${t(kind)}`));
      const input=node('input');input.type='range';input.min='0';input.max='720';input.step='15';input.value=rule.start.offset_minutes;
      const output=node('output',safeTime(resolveWindowTime(rule.start,segment,bundle.plan.snapshot.timezone)));row.append(input,output);
      input.addEventListener('input',()=>{rule.start.offset_minutes=Number(input.value);output.textContent=safeTime(resolveWindowTime(rule.start,segment,bundle.plan.snapshot.timezone));changed();});timing.append(row);
    }
  }
  if(visited.size)root.append(timing);
  const summary=section('family_summary');
  const sleeping=dayUses.filter(v=>v.purpose==='sleeping'),recreation=dayUses.filter(v=>v.purpose==='recreation');
  summary.append(node('p',`${t('sleeping')}: ${sleeping.length? [...new Set(sleeping.map(v=>bundle.config.rooms[v.room][lang()]))].join(', '):t('not_used')}`),node('p',`${t('recreation')}: ${recreation.length?[...new Set(recreation.map(v=>bundle.config.rooms[v.room][lang()]))].join(', '):t('not_used')}`));
  for(const meal of meals)summary.append(node('p',`${catalogs[lang()]['meal_'+meal.kind]??meal.kind}: ${t(meal.choice)}`));
  const extraUses=dayUses.some(v=>v.purpose==='other'),manual=bundle.plan.groups.some(v=>v.segment===segment.id);
  if(extraUses||manual)summary.append(node('p',t('additional_custom'),'hint'),button('review_custom',openAdvanced));
  summary.append(node('p',t('summary_hint'),'hint'));root.append(summary);
  const advanced=node('details',undefined,'advanced-setup');advanced.id='advanced-setup';advanced.append(node('summary',t('advanced_setup')));
  const contents=node('div',undefined,'advanced-content');advanced.append(contents);root.append(advanced);renderAdvanced(contents);renderTimeline();
}

function renderAdvanced(root){
  const calendar=section('period_calendar'),snapshot=bundle.plan.snapshot;
  calendar.append(node('p',t('calendar_supplied'),'hint'),field('timezone',snapshot.timezone,v=>snapshot.timezone=v),
    field('observance_region',snapshot.observance,v=>snapshot.observance=v,options(['israel','diaspora'])),
    field('preparation_start',snapshot.preparation_start,v=>snapshot.preparation_start=v),
    field('window_start',snapshot.start,v=>snapshot.start=v),field('window_end',snapshot.end,v=>snapshot.end=v,undefined,'end'));
  const addDay=button('add_day',()=>{const id=nextId('day',snapshot.segments);snapshot.segments.push({id,kind:'yom_tov',start:snapshot.end,end:'',candle_lighting:'',sunrise:''});changed();render();});addDay.disabled=snapshot.segments.length>=3;calendar.append(node('p',t('day_edit_hint'),'hint'),addDay);if(calendarData?.source!=='standalone'){const source=node('div',undefined,'calendar-source');source.append(node('h3',t('calendar_source')),node('p',t('calendar_coverage'),'hint'));for(const [key,item] of Object.entries(calendarData?.values??{})){const labelKey=({candle_lighting:'candle_lighting',sunrise:'sunrise_anchor',end:'end',active:'observance_active'})[key];source.append(node('p',`${t(labelKey)}: ${item.value?safeTime(item.value):(catalogs[lang()]['source_'+item.status]??item.status)}`));}calendar.append(source);}root.append(calendar);
  const availability=section('availability_title');availability.append(node('p',t('availability_hint'),'hint'));
  for(const item of bundle.plan.availability){const row=node('div',undefined,'period-item');windowFields(row,item);row.append(field('home_status',item.state,v=>item.state=v,options(['home_state','away_state','unset']).map(([key,text])=>[key.replace('_state',''),text])),button('remove_item',()=>remove(bundle.plan.availability,item)));availability.append(row);}
  availability.append(button('add_window',()=>{bundle.plan.availability.push({id:nextId('window',bundle.plan.availability),start:snapshot.start,end:snapshot.end,state:'unset'});changed();render();}));root.append(availability);
  for(const segment of snapshot.segments){
    const day=section('period_day');const removeDay=button('remove_day',()=>{snapshot.segments=snapshot.segments.filter(v=>v.id!==segment.id);for(const key of ['room_uses','meals','groups'])bundle.plan[key]=bundle.plan[key].filter(v=>v.segment!==segment.id);changed();render();});removeDay.disabled=snapshot.segments.length<=1;day.append(removeDay);day.querySelector('h2').append(node('bdi',' · '+segment.id));
    day.append(field('day_kind',segment.kind,v=>segment.kind=v,options(['shabbat','yom_tov'])));
    const anchors=node('details');anchors.append(node('summary',t('dated_anchors')));windowFields(anchors,segment);
    anchors.append(field('candle_lighting',segment.candle_lighting,v=>segment.candle_lighting=v),field('sunrise_anchor',segment.sunrise,v=>segment.sunrise=v));day.append(anchors);
    const columns=node('div',undefined,'grid');
    for(const purpose of ['sleeping','recreation','other']){
      const uses=bundle.plan.room_uses.filter(v=>v.segment===segment.id&&v.purpose===purpose);
      if(purpose==='other'&&!uses.length)continue;
      const panel=node('div');panel.append(node('h3',t(purpose)),node('p',t('use_hint'),'hint'));
      for(const use of uses)panel.append(roomRow(use));
      panel.append(button('add_room_use',()=>addUse(segment,purpose)));columns.append(panel);
    }
    day.append(columns,node('h3',t('meals_title')));
    for(const meal of bundle.plan.meals.filter(v=>v.segment===segment.id)){
      const row=node('div',undefined,'period-item');row.append(field('meal_slot',meal.kind,v=>meal.kind=v),field('meal_choice',meal.choice,v=>meal.choice=v,options(['unset','none','away','family','hosting'])));windowFields(row,meal);groupPicker(row,meal);row.append(button('remove_item',()=>remove(bundle.plan.meals,meal)));day.append(row);
    }
    day.append(button('add_meal',()=>{bundle.plan.meals.push({id:nextId('meal',bundle.plan.meals),segment:segment.id,kind:'additional',choice:'unset',start:segment.start,end:segment.end,groups:[]});changed();render();}));root.append(day);
  }
  const manual=section('manual_groups');manual.append(node('p',t('manual_hint'),'hint'));
  for(const item of bundle.plan.groups){const row=node('div',undefined,'period-item');row.append(field('period_day',item.segment,v=>item.segment=v,snapshot.segments.map(s=>[s.id,s.id])),field('group_label',item.group,v=>item.group=v,Object.entries(bundle.config.groups).filter(([,g])=>g.activation!=='home').map(([id,g])=>[id,g.label[lang()]])));windowFields(row,item);row.append(button('remove_item',()=>remove(bundle.plan.groups,item)));manual.append(row);}
  manual.append(button('add_group',()=>{const group=Object.keys(bundle.config.groups).find(id=>bundle.config.groups[id].activation!=='home'),segment=snapshot.segments[0];if(!group)return;bundle.plan.groups.push({id:nextId('selection',bundle.plan.groups),segment:segment.id,group,start:segment.start,end:segment.end});changed();render();}));root.append(manual);
  const advanced=node('details',undefined,'card');advanced.append(node('summary',t('advanced_config')),node('p',t('advanced_hint'),'hint'));
  const label=node('label',undefined,'field');label.append(node('span',t('advanced_config')));
  const editor=node('textarea');editor.dir='ltr';editor.rows=12;editor.maxLength=120000;editor.value=JSON.stringify(bundle.config,null,2);label.append(editor);advanced.append(label,button('apply_config',async()=>{
    const token=revision;
    try{const candidate={config:JSON.parse(editor.value),plan:structuredClone(bundle.plan)};await validate(candidate);if(token!==revision)return;bundle=candidate;changed();render();message('config_applied');}catch(e){if(token===revision)error(e);}
  }));root.append(advanced);
}
function renderTimeline(){
  const root=$('timeline');root.replaceChildren();if(!result)return;
  if(!result.complete){for(const issue of result.issues){const p=node('p',t('issue_'+issue.code));p.append(node('bdi',' · '+(issue.id??issue.room)));root.append(p);}return;}
  root.append(node('p',`${t('event_count')}: ${result.events.length}`));
  for(const event of result.events){
    const row=node('div',undefined,'event');const time=node('time',localTime(event.local,lang(),bundle.plan.snapshot.timezone));time.dateTime=event.local;
    const load=Object.values(bundle.config.loads).find(v=>v.physical_id===event.physical_id);
    const description=node('div',load?.label[lang()]??event.physical_id);
    const reasons=node('small');for(const reason of event.reasons)reasons.append(node('bdi',`${dayLabel(bundle.plan.snapshot.segments.find(v=>v.id===reason.segment),0)} · ${bundle.config.groups[reason.group].label[lang()]} `));description.append(reasons);
    const action=event.action;let value=action.type==='state'?t(action.state):t('mode_'+action.mode);
    if(action.temperature!==undefined)value+=` · ${action.temperature}°${action.unit} · ${catalogs[lang()]['fan_'+action.fan_mode]??action.fan_mode}`;
    if(event.intent==='track_only')description.append(node('small',t('track_only')));
    row.append(time,description,node('bdi',value,'state'));root.append(row);
  }
}
async function validate(candidate){
  const response=await fetch('/api/v2/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(candidate)});
  const value=await response.json();if(!response.ok)throw new Error(value.error);return value;
}
async function preview(){const token=revision;try{const next=await validate(structuredClone(bundle));if(token!==revision)return;result=next;$('export').disabled=!next.complete;renderTimeline();message(next.complete?'preview_ready':'period_incomplete',!next.complete);}catch(e){if(token===revision)error(e);}}
async function boot(){
  try{
    const responses=await Promise.all([fetch('/api/v2/example'),fetch('/api/v2/i18n'),fetch('/api/v2/calendar')]);
    if(responses.some(r=>!r.ok))throw new Error('load_failed');
    [bundle,catalogs,calendarData]=await Promise.all(responses.map(r=>r.json()));if(householdMode)bundle=parsePeriodDraft(sessionStorage.getItem('shabbat-flow-household-workspace'));initial=structuredClone(bundle);
    $('language').addEventListener('change',()=>{bundle.plan.language=$('language').value;revision++;render();});
    $('preview').addEventListener('click',preview);
    $('save').addEventListener('click',async()=>{const token=revision;try{const candidate=structuredClone(bundle);await validate(candidate);if(token!==revision)return;localStorage.setItem(draftKey,JSON.stringify(candidate));message('saved');}catch(e){if(token===revision)error(e);}});
    $('load').addEventListener('click',async()=>{const token=revision;try{const candidate=parsePeriodDraft(localStorage.getItem(draftKey));await validate(candidate);if(token!==revision)return;bundle=candidate;changed();render();message('loaded');}catch(e){if(token===revision)error(e);}});
    $('delete').addEventListener('click',()=>{revision++;try{localStorage.removeItem(draftKey);message('deleted');}catch(e){error(e);}});
    $('reset').addEventListener('click',()=>{const language=lang();bundle=structuredClone(initial);bundle.plan.language=language;changed();render();message('reset_done');});
    $('export').addEventListener('click',()=>{if(!result?.complete)return;const blob=new Blob([JSON.stringify({...bundle,preview:result},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=node('a');link.href=url;link.download='shabbat-flow-period-preview.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
    render();
  }catch(e){$('status').textContent='Unable to load preview. / לא ניתן לטעון תצוגה מקדימה.';}
}
boot();
