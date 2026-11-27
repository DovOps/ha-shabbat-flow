import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {parseDraft,translate,localTime,localeMetadata} from '../src/shabbat_flow/web/model.mjs';
const catalogs=JSON.parse(fs.readFileSync(new URL('../src/shabbat_flow/web/i18n.json',import.meta.url)));
const plan=JSON.parse(fs.readFileSync(new URL('../examples/plan.json',import.meta.url)));
const config=JSON.parse(fs.readFileSync(new URL('../examples/household.json',import.meta.url)));

test('default languages have full key parity and direction metadata',()=>{
  assert.deepEqual(Object.keys(catalogs.en).sort(),Object.keys(catalogs.he).sort());
  assert.deepEqual(Object.keys(localeMetadata).sort(),Object.keys(catalogs).sort());
  for(const language of Object.keys(catalogs))for(const key of Object.keys(catalogs.en))assert.ok(translate(catalogs,language,key).trim());
  assert.equal(localeMetadata.he.direction,'rtl');
});
test('all statically referenced labels are translated',()=>{
  const html=fs.readFileSync(new URL('../src/shabbat_flow/web/index.html',import.meta.url),'utf8');
  for(const match of html.matchAll(/data-i18n="([^"]+)"/g))for(const language of Object.keys(catalogs))assert.ok(translate(catalogs,language,match[1]));
});
test('invalid drafts fail without fallback guesses',()=>{
  for(const raw of [null,'not json','{}','[]','null','{"plan":{"schema_version":2},"config":{}}'])assert.throws(()=>parseDraft(raw));
  const decoded=parseDraft(JSON.stringify({config,plan}));
  assert.deepEqual(decoded,{config,plan});
});
test('missing keys are visible programming errors',()=>assert.throws(()=>translate(catalogs,'he','unknown')));
test('local formatted times preserve explicit timezone',()=>{
  const result=localTime('2027-01-08T14:20:00Z','en','Asia/Jerusalem');
  assert.match(result,/16:20/);
  assert.ok(localTime('2027-01-08T14:20:00Z','he','Asia/Jerusalem'));
});

const period=JSON.parse(fs.readFileSync(new URL('../examples/period-preview.json',import.meta.url)));
const extra=JSON.parse(fs.readFileSync(new URL('../src/shabbat_flow/web/period-i18n.json',import.meta.url)));
const {parsePeriodDraft,availableProfiles,nextId,PERIOD_DRAFT_KEY}=await import('../src/shabbat_flow/web/period-model.mjs');
test('period UI has translated labels, issues and independent draft storage',()=>{
  assert.deepEqual(Object.keys(extra.en).sort(),Object.keys(extra.he).sort());
  const html=fs.readFileSync(new URL('../src/shabbat_flow/web/period.html',import.meta.url),'utf8');
  const js=fs.readFileSync(new URL('../src/shabbat_flow/web/period.mjs',import.meta.url),'utf8');
  for(const language of ['en','he']){
    const merged={...catalogs[language],...extra[language]};
    for(const [,key] of html.matchAll(/data-i18n="([^"]+)"/g))assert.ok(merged[key],key);
    for(const [,key] of js.matchAll(/\b(?:t|message|field|button|section)\('([^']+)'(?=[,)])/g))assert.ok(merged[key],key);
    for(const code of ['room_overlap','availability_unset','meal_unset','meals_missing'])assert.ok(merged['issue_'+code]);
  }
  assert.equal(PERIOD_DRAFT_KEY,'shabbat-flow-draft-v2');
});
test('v2 draft reader rejects v1 instead of silently migrating',()=>{
  assert.deepEqual(parsePeriodDraft(JSON.stringify(period)),period);
  for(const raw of [null,'{}','null','[]','oops',JSON.stringify({config,plan})])assert.throws(()=>parsePeriodDraft(raw));
});
test('room profile choices are scoped by room and purpose',()=>{
  const profiles=availableProfiles(period.config,'room_a','sleeping');
  assert.equal(profiles.length,3);
  assert.ok(profiles.every(([,v])=>v.room==='room_a'&&v.purpose==='sleeping'));
  assert.equal(availableProfiles(period.config,'room_b','recreation').length,2);
  assert.equal(availableProfiles(period.config,'missing','sleeping').length,0);
});
test('generated UI selection IDs do not collide after removing a row',()=>{
  assert.equal(nextId('use',[{id:'use_1'},{id:'use_3'}]),'use_2');
});

const {dayHomeState,setDayHome,setRoomChoice,copyPreviousDay,shiftWallDays,resolveWindowTime}=await import('../src/shabbat_flow/web/period-model.mjs');
test('day-level home choice preserves other days and selected room/meal intent',()=>{
  const before=structuredClone(period),next=setDayHome(period,'day_2','away');
  assert.deepEqual(period,before);
  assert.deepEqual(next.plan.room_uses,period.plan.room_uses);
  assert.deepEqual(next.plan.meals.filter(m=>m.segment!=='day_2'),period.plan.meals.filter(m=>m.segment!=='day_2'));
  assert.ok(next.plan.meals.filter(m=>m.segment==='day_2').every(m=>m.choice==='away'||m.choice==='none'));
  assert.deepEqual(next.plan.snapshot.segments.map(s=>dayHomeState(next.plan,s)),['home','away','home']);
  assert.equal(next.plan.availability[0].start,period.plan.snapshot.preparation_start);
  assert.equal(next.plan.availability.at(-1).end,period.plan.snapshot.end);
});
test('room tiles change one purpose and preserve recreation and other days',()=>{
  let next=setRoomChoice(period,'day_1','room_a','recreation','room_a_recreation');
  const rec=next.plan.room_uses.find(v=>v.purpose==='recreation');
  next=setRoomChoice(next,'day_1','room_a','sleeping','room_a_early');
  assert.deepEqual(next.plan.room_uses.find(v=>v.purpose==='recreation'),rec);
  const sleep=next.plan.room_uses.find(v=>v.segment==='day_1'&&v.purpose==='sleeping');
  assert.equal(sleep.profile,'room_a_early');
  assert.equal(sleep.start,'2027-01-07T20:40:00+02:00');
  next=setRoomChoice(next,'day_1','room_a','sleeping','off');
  assert.ok(next.plan.room_uses.some(v=>v.purpose==='recreation'));
  assert.equal(next.plan.room_uses.filter(v=>v.purpose==='sleeping').length,2);
});
test('custom room windows survive profile changes; multiple uses require advanced review',()=>{
  const custom=structuredClone(period);custom.plan.room_uses[0].start='2027-01-07T22:00:00+02:00';
  const next=setRoomChoice(custom,'day_1','room_a','sleeping','room_a_early');
  assert.equal(next.plan.room_uses.find(v=>v.segment==='day_1').start,custom.plan.room_uses[0].start);
  custom.plan.room_uses.push({...custom.plan.room_uses[0],id:'another'});
  assert.throws(()=>setRoomChoice(custom,'day_1','room_a','sleeping','off'),/custom_room/);
});
test('copy previous day stages room/meal choices without modifying source',()=>{
  const original=structuredClone(period),copied=copyPreviousDay(period,'day_2');
  assert.deepEqual(period,original);
  assert.deepEqual(copied.plan.groups,period.plan.groups);
  const use=copied.plan.room_uses.find(v=>v.segment==='day_2');
  assert.equal(use.start,'2027-01-08T21:40:00+02:00');
  assert.equal(use.end,'2027-01-09T08:00:00+02:00');
  assert.equal(new Set(copied.plan.room_uses.map(v=>v.id)).size,copied.plan.room_uses.length);
  const originalStart=copied.plan.snapshot.segments[1].candle_lighting;
  assert.equal(originalStart,period.plan.snapshot.segments[1].candle_lighting);
});
test('copy dates uses local clock across DST and rejects nonexistent or ambiguous times',()=>{
  assert.equal(shiftWallDays('2027-03-25T08:00:00+02:00',1,'Asia/Jerusalem'),'2027-03-26T08:00:00+03:00');
  assert.throws(()=>shiftWallDays('2027-03-25T02:30:00+02:00',1,'Asia/Jerusalem'),/copy_time/);
  assert.throws(()=>shiftWallDays('2027-11-06T01:30:00-04:00',1,'America/New_York'),/copy_time/);
});
test('copy rejects incomplete custom availability and out-of-period copied uses',()=>{
  const custom=structuredClone(period);custom.plan.availability=[];
  assert.throws(()=>copyPreviousDay(custom,'day_2'),/copy_custom/);
  const cross=structuredClone(period);cross.plan.room_uses.find(v=>v.segment==='day_2').end=cross.plan.snapshot.end;
  assert.throws(()=>copyPreviousDay(cross,'day_3'),/copy_bounds/);
});
test('profile window defaults resolve supplied anchors independently',()=>{
  const segment=period.plan.snapshot.segments[1];
  assert.equal(resolveWindowTime({anchor:'candle_lighting',offset_minutes:60},segment,'Asia/Jerusalem'),'2027-01-08T19:00:00+02:00');
  assert.equal(resolveWindowTime({anchor:'sunrise',offset_minutes:120},segment,'Asia/Jerusalem'),'2027-01-09T08:00:00+02:00');
});

const {localDateTimeCandidates,localDateTimeValue}=await import('../src/shabbat_flow/web/period-model.mjs');
test('date controls preserve seconds, reject gaps and expose both fold offsets',()=>{
  const zone='Asia/Jerusalem';
  assert.equal(localDateTimeValue('2027-01-08T14:20:37Z',zone),'2027-01-08T16:20:37');
  assert.deepEqual(localDateTimeCandidates('2027-01-08T16:20:37',zone),['2027-01-08T16:20:37+02:00']);
  assert.deepEqual(localDateTimeCandidates('2027-03-26T02:30',zone),[]);
  assert.deepEqual(localDateTimeCandidates('2027-10-31T01:30',zone),['2027-10-31T01:30:00+03:00','2027-10-31T01:30:00+02:00']);
  assert.deepEqual(localDateTimeCandidates('2027-02-30T12:00',zone),[]);
  assert.equal(shiftWallDays('2027-01-08T16:20:37+02:00',1,zone),'2027-01-09T16:20:37+02:00');
});

test('household setup has complete English/Hebrew catalogs and versioned bridge routes',()=>{
  const base=new URL('../src/shabbat_flow/',import.meta.url);
  const c=JSON.parse(fs.readFileSync(new URL('web/household-i18n.json',base)));
  assert.deepEqual(Object.keys(c.en).sort(),Object.keys(c.he).sort());
  const html=fs.readFileSync(new URL('web/household.html',base),'utf8');
  const script=fs.readFileSync(new URL('web/household.mjs',base),'utf8');
  for(const match of (html+script).matchAll(/(?:data-i18n="|t\(')([a-z_]+)(?:"|'\))/g))for(const lang of ['en','he'])assert.ok(c[lang][match[1]],match[1]);
  const panel=fs.readFileSync(new URL('ha_panel.js',base),'utf8');
  assert.ok(panel.includes("new URL('./household.html',import.meta.url)"));
  assert.ok(panel.includes('POST /api/v2/household'));
  assert.ok(!panel.includes('callService'));
});

test('household polling preserves the form-bound draft until a redraw is needed',async()=>{
  const {runInNewContext}=await import('node:vm');
  const source=fs.readFileSync(new URL('../src/shabbat_flow/web/household.mjs',import.meta.url),'utf8');
  const refresh=source.slice(source.indexOf('async function refresh('),source.indexOf('async function save('));
  const initial={inventory:{revision:'a'},settings:{revision:0,rooms:{}}};
  const context={updatePlannerFeedback:()=>{},updateRoomFeedback:()=>{},staleSettings:false,saveError:null,labelFilters:{...emptyLabelFilters(),bathroom:"draft_label"},emptyLabelFilters,data:structuredClone(initial),next:structuredClone(initial),draft:{room_a:{enabled:false}},dirty:false,saving:false,needsReview:false,offline:false,structuredClone,
    api:async()=>structuredClone(context.next),render:()=>{context.renders++;},renderRooms:()=>{context.renders++;},updateAvailability:()=>{},syncLabel:()=>{},status:value=>{context.message=value;},renders:0};
  runInNewContext(refresh,context);
  const boundRoom=context.draft.room_a;
  await context.refresh();
  assert.equal(context.draft.room_a,boundRoom);
  boundRoom.enabled=true;context.dirty=true;
  context.next.inventory.revision='b';await context.refresh();
  assert.equal(context.draft.room_a,boundRoom);assert.equal(context.needsReview,true);assert.equal(context.labelFilters.bathroom,'draft_label');
  await context.refresh(true);assert.equal(context.needsReview,false);
  context.next.settings.revision=1;await context.refresh();
  assert.equal(context.message,'stale_household');assert.equal(context.data.settings.revision,0);
});

test('open household planner shows local actionable errors and handles request lifecycle',async()=>{
  const {runInNewContext}=await import('node:vm');
  const source=fs.readFileSync(new URL('../src/shabbat_flow/web/household.mjs',import.meta.url),'utf8');
  const code=source.slice(source.indexOf('function planProblems('),source.indexOf('async function boot('));
  const box={messages:[],replaceChildren(){this.messages=[];},append(p){this.messages.push(p);},focus(){this.focused=true;},scrollIntoView(){this.visible=true;}};
  const button={},topButton={},room={enabled:true,purposes:['sleeping'],roles:{main_lights:['fictional_light'],night_lights:[],hvac:[]},shared_areas:[],hvac:{mode:'none'}};
  const context={offline:false,plannerFailure:null,plannerAttempted:false,plannerAnchor:"plan-top",manualZone:null,manualCalendar:true,automatic:null,structuredClone,dirty:false,opening:false,observance:'',dateValues:{candles:'2027-01-08T16:00:00+02:00',sunrise:'',end:'2027-01-09T18:00:00+02:00'},kind:'shabbat',language:'en',catalogs:{en:{invalid_mapping:'Mapping issue',workspace_storage_failed:'Storage issue'}},data:{settings:{rooms:{},revision:1},inventory:{timezone:'Asia/Jerusalem',revision:'a'},issues:[]},
    document:{querySelectorAll:()=>[button,topButton]},$:id=>id==='plan'?button:box,t:key=>key,el:(_,text)=>text,zonedISO:d=>d.toISOString(),api:async()=>{throw new Error('unexpected request');},sessionStorage:{setItem(){}},location:{href:''}};
  runInNewContext(code,context);
  context.updatePlannerFeedback=(focus=false)=>{box.messages=Array.from(context.opening?['opening_plan']:context.plannerFailure??context.planProblems());if(focus){box.focus();box.scrollIntoView();}};
  await context.openPlan();assert.deepEqual(box.messages,['choose_observance','missing_sunrise','needs_roles']);assert.ok(box.focused&&box.visible);assert.equal(context.location.href,'');
  context.dirty=true;await context.openPlan();assert.ok(box.messages.includes('needs_save'));
  context.dirty=false;context.observance='israel';context.dateValues.sunrise='2027-01-09T06:00:00+02:00';context.data.settings.rooms={room_a:room};
  context.api=async()=>{throw new Error('invalid_mapping');};await context.openPlan();assert.deepEqual(box.messages,['invalid_mapping']);assert.equal(button.disabled,false);
  let calls=0,resolve;context.api=()=>{calls++;return new Promise(r=>resolve=r);};
  const pending=context.openPlan();assert.equal(button.disabled,true);assert.equal(topButton.disabled,true);assert.deepEqual(box.messages,['opening_plan']);await context.openPlan();assert.equal(calls,1);
  resolve({plan:{}});await pending;assert.equal(context.location.href,'./period.html?household=1');assert.equal(button.disabled,false);assert.equal(topButton.disabled,false);
  context.location.href='';context.api=async()=>({plan:{}});context.sessionStorage.setItem=()=>{throw new Error('blocked');};await context.openPlan();assert.deepEqual(box.messages,['workspace_storage_failed']);assert.equal(context.location.href,'');
  context.dateValues.sunrise='2027-01-08T06:00:00+02:00';await context.openPlan();assert.deepEqual(box.messages,['date_order']);
});

test('automatic calendar passes the whole snapshot and refresh preserves manual dates',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=fs.readFileSync(new URL('../src/shabbat_flow/web/household.mjs',import.meta.url),'utf8');
 const code=source.slice(source.indexOf('function planProblems('),source.indexOf('async function boot('));
 const snapshot=structuredClone(period.plan.snapshot);snapshot.start='2099-01-01T16:00:00+02:00';
 const box={replaceChildren(){},append(){},focus(){},scrollIntoView(){}},button={};let received;
 const context={offline:false,plannerFailure:null,plannerAttempted:false,plannerAnchor:"plan-top",manualZone:null,manualCalendar:false,automatic:{status:'ready',snapshot},structuredClone,dirty:false,opening:false,language:'en',catalogs:{en:{}},
 data:{settings:{revision:1,rooms:{a:{enabled:true,purposes:['sleeping'],roles:{main_lights:['load'],night_lights:[],hvac:[]},shared_areas:[],hvac:{mode:'none'}}}},inventory:{revision:'a'},issues:[]},
 document:{querySelectorAll:()=>[button]},$:id=>id==='plan'?button:box,t:v=>v,el:(_,v)=>v,api:async(_,body)=>{received=body;return {plan:{}};},sessionStorage:{setItem(){}},location:{href:''}};
 runInNewContext(code,context);context.updatePlannerFeedback=()=>{};await context.openPlan();assert.deepEqual(received.snapshot,snapshot);assert.notEqual(received.snapshot,snapshot);assert.equal(received.snapshot.segments.length,3);
 context.automatic={status:'unavailable',error:'calendar_missing'};assert.ok(context.planProblems().includes('calendar_missing'));
 context.calendarLoading=false;context.dateValues={candles:'manual',sunrise:'manual',end:'manual'};context.manualCalendar=true;context.renderCalendar=()=>{};context.renderDates=()=>{};context.manualZone='Europe/London';
 runInNewContext(source.slice(source.indexOf('async function refreshCalendar('),source.indexOf('function renderDates(')),context);
 context.api=async()=>({status:'ready',snapshot});await context.refreshCalendar();assert.deepEqual(context.dateValues,{candles:'manual',sunrise:'manual',end:'manual'});assert.equal(context.manualZone,'Europe/London');
 context.manualCalendar=false;context.setManualCalendar(true);assert.equal(context.dateValues.end,snapshot.segments[0].end);assert.equal(context.observance,snapshot.observance);
 const html=fs.readFileSync(new URL('../src/shabbat_flow/web/household.html',import.meta.url),'utf8');assert.ok(html.includes('<div id="dates" hidden>'));assert.ok(html.includes('<details id="calendar-advanced">'));
});

test('wizard saves freeze controls, reject duplicate submits and preserve edits on failure',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=fs.readFileSync(new URL('../src/shabbat_flow/web/household.mjs',import.meta.url),'utf8');
 const controls=[{disabled:false},{disabled:true}],button={disabled:false};let resolve;
 const context={updatePlannerFeedback:()=>{},updateRoomFeedback:()=>{},staleSettings:false,offline:false,saveError:null,postShutoff:false,labelFilters:emptyLabelFilters(),emptyLabelFilters,needsReview:false,saving:false,dirty:true,draft:{example:{enabled:true}},data:{settings:{revision:3},inventory:{revision:'a'}},structuredClone,
  document:{querySelector:()=>null,querySelectorAll:()=>controls},$:()=>button,status:()=>{},fail:()=>{},wizardError:()=>{},catalogs:{en:{}},language:'en',api:()=>new Promise(r=>resolve=r)};
 runInNewContext(source.slice(source.indexOf('async function save('),source.indexOf('function planProblems(')),context);
 const pending=context.save();assert.ok(controls.every(c=>c.disabled));assert.equal(await context.save(),false);
 resolve({settings:{revision:4,rooms:{example:{enabled:true}}},inventory:{revision:'a'}});assert.equal(await pending,true);assert.equal(context.dirty,false);assert.equal(controls[0].disabled,false);assert.equal(controls[1].disabled,true);
 context.dirty=true;const draft=context.draft;context.api=async()=>{throw new Error('storage_failed');};assert.equal(await context.save(),false);assert.equal(context.draft,draft);assert.equal(context.dirty,true);assert.equal(context.saving,false);
 context.needsReview=true;assert.equal(await context.save(),false);
});

test('wizard next waits for persistence and blocks unfinished bathroom dependencies',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=fs.readFileSync(new URL('../src/shabbat_flow/web/household.mjs',import.meta.url),'utf8');
 const room={enabled:true,purposes:['sleeping'],roles:{main_lights:['lamp'],night_lights:[],hvac:[]},hvac:{mode:'none'},shared_areas:['bath'],setup:{status:'draft'}};
 const bath={enabled:true,setup:{status:'draft'}};let error,navigation;
 const context={roomProblems,saving:false,draft:{room,bath},activeRoom:'room',setup:r=>r.setup,returnToRoom:null,changed:()=>{},wizardError:k=>error=k,renderRooms:()=>{},save:async()=>true,selectedRooms:()=>['room','bath'],go:(...v)=>navigation=v};
 runInNewContext(source.slice(source.indexOf('async function finishRoom('),source.indexOf('function wizardError(')),context);
 await context.finishRoom();assert.equal(error,'missing_shared');assert.equal(navigation,undefined);
 bath.setup.status='ready';context.save=async()=>false;await context.finishRoom();assert.equal(navigation,undefined);assert.equal(room.setup.status,'draft');
 context.save=async()=>true;await context.finishRoom();assert.equal(room.setup.status,'ready');assert.deepEqual(navigation,['room','bath']);
});

test('planned action badges separate on/off, HVAC and informational intent without changing events',async()=>{
 const {actionBadge}=await import('../src/shabbat_flow/web/period-model.mjs');
 const cases=[['state','on','on'],['state','off','off'],['hvac_power','on','on'],['hvac_power','off','off'],['hvac','heat','heat'],['hvac','cool','cool'],['hvac','off','off']];
 for(const [type,value,semantic] of cases){const event={action:{type,[type==='hvac'?'mode':'state']:value},intent:'set_state'};const before=structuredClone(event);const b=actionBadge(event);assert.equal(b.className,'state '+semantic);assert.equal(b.preserve,type==='hvac_power');assert.deepEqual(event,before);assert.equal(actionBadge({...event,intent:'track_only'}).className,'state tracked');}
 assert.equal(actionBadge({action:{type:'unexpected'},intent:'set_state'}).className,'state neutral');
 const base=JSON.parse(fs.readFileSync(new URL('../src/shabbat_flow/web/i18n.json',import.meta.url)));
 const extra=JSON.parse(fs.readFileSync(new URL('../src/shabbat_flow/web/period-i18n.json',import.meta.url)));
 for(const lang of ['en','he'])for(const key of ['on','off','mode_heat','mode_cool','mode_off','power_only_preview','action_unknown'])assert.ok({...base[lang],...extra[lang]}[key]);
});

test('planned badge foreground/background colors meet 4.5 to 1 text contrast',()=>{
 const css=fs.readFileSync(new URL('../src/shabbat_flow/web/style.css',import.meta.url),'utf8');
 const lum=hex=>{const rgb=hex.match(/../g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;};
 const colors=[];
 for(const semantic of ['on','off','heat','cool','neutral']){const matches=[...css.matchAll(new RegExp('\\.state\\.'+semantic+'\\{background:#([0-9a-f]{6});color:#([0-9a-f]{6})','g'))];assert.ok(matches.length,semantic);const [,bg,fg]=matches.at(-1);const a=lum(bg),b=lum(fg);assert.ok((Math.max(a,b)+.05)/(Math.min(a,b)+.05)>=4.5,semantic);colors.push(bg);}
 assert.equal(new Set(colors).size,colors.length);
});

import {suggestedAreaTypes,classifyRoom,areaType,roomProblems,phases,emptyLabelFilters,roleCandidates,bathroomCandidates,suggestedPurposes,filteredAreas} from '../src/shabbat_flow/web/household-model.mjs';
test('label candidates combine entity/device labels, preserve selection and separate area scope',()=>{
 const entities=[
  {id:'direct',domain:'light',area_id:'a',labels:['main']},
  {id:'device',domain:'switch',area_id:'a',device_labels:['main','night']},
  {id:'plain',domain:'light',area_id:'a',labels:[]},
  {id:'outside',domain:'light',area_id:null,labels:['main']},
  {id:'selected',domain:'switch',area_id:'b',labels:[]},
  {id:'disabled',domain:'light',area_id:'a',labels:['main'],disabled:true},
  {id:'sensor',domain:'sensor',area_id:'a',labels:['main']},
  {id:'hvac',domain:'climate',area_id:'a',labels:[]},
 ];
 const inventory={entities,areas:[{id:'a',labels:['main']},{id:'b',labels:[]}]};
 const room={roles:{main_lights:['selected'],night_lights:[],hvac:[]},setup:{service:false}};
 const filters={...emptyLabelFilters(),main_lights:'main',night_lights:'night'};
 const ids=(role,options)=>roleCandidates(inventory,room,'a',role,filters,options).map(e=>e.id);
 assert.deepEqual(ids('main_lights'),['direct','device','selected','disabled']);
 assert.deepEqual(ids('night_lights'),['device']);
 assert.deepEqual(ids('hvac'),['hvac']);
 assert.ok(ids('main_lights',{allRoom:true}).includes('plain'));
 assert.ok(!ids('main_lights',{allRoom:true}).includes('outside'));
 assert.ok(ids('main_lights',{allAreas:true}).includes('outside'));
 assert.ok(!ids('main_lights',{allAreas:true}).includes('plain'));
 assert.equal(roleCandidates(inventory,room,'a','main_lights',{...filters,main_lights:'deleted'}).length,1);
 assert.ok(roleCandidates(inventory,room,'a','main_lights',emptyLabelFilters()).some(e=>e.id==='plain'));
 const original=structuredClone({inventory,room,filters});ids('main_lights');assert.deepEqual({inventory,room,filters},original);
});
test('bathrooms follow labeled lights, room labels only suggest explicit purposes',()=>{
 const inventory={areas:[{id:'bed',labels:['sleep','common']},{id:'bath',labels:[]},{id:'other',labels:['bath']}],entities:[{id:'lamp',domain:'light',area_id:'bath',device_labels:['bath']}]};
 const filters={...emptyLabelFilters(),bathroom:'bath',bedroom:'sleep',common_area:'common'};
 assert.deepEqual(bathroomCandidates(inventory,'bed',[],filters).map(a=>a.id),['bath']);
 assert.deepEqual(bathroomCandidates(inventory,'bed',['bath'],filters),[]);
 assert.equal(bathroomCandidates(inventory,'bed',[],filters,true).length,2);
 assert.deepEqual(suggestedPurposes(inventory.areas[0],filters),['sleeping']);
 assert.deepEqual(filteredAreas(inventory.areas,{other:{enabled:true}},filters,'bedroom').map(a=>a.id),['bed','other']);
 const room={roles:{main_lights:[],night_lights:[],hvac:[]},setup:{service:true}};
 assert.deepEqual(roleCandidates(inventory,room,'bath','main_lights',filters).map(e=>e.id),['lamp']);
});

test('room completion explains valid drafts and all actionable missing selections without mutating them',()=>{
 const bath={enabled:true,purposes:[],roles:{main_lights:['lamp'],night_lights:[],hvac:[]},shared_areas:[],hvac:{mode:'none'},setup:{status:'draft',service:true}};
 const original=structuredClone(bath);
 assert.deepEqual(roomProblems(bath,{bath}),[]);assert.deepEqual(bath,original);
 bath.setup.lighting={night_enabled:true};assert.deepEqual(roomProblems(bath,{bath}),['bathroom_night_needs_lights']);
 bath.setup.lighting={night_enabled:false};bath.roles.main_lights=[];
 assert.deepEqual(roomProblems(bath,{bath}),['needs_roles']);
 bath.setup.service=false;assert.deepEqual(roomProblems(bath,{bath}),['needs_roles','needs_purpose']);
 bath.hvac.mode='preserve';assert.ok(roomProblems(bath,{bath}).includes('needs_hvac_device'));assert.ok(roomProblems(bath,{bath}).includes('needs_hvac_use'));
 bath.roles.hvac=['unit'];bath.setup.phases={night:'none',daytime_meal:true};bath.purposes=['recreation'];assert.deepEqual(roomProblems(bath,{bath}),[]);
});

test('room feedback retains blocking reasons, offers non-destructive refresh and distinguishes draft from error',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=fs.readFileSync(new URL('../src/shabbat_flow/web/household.mjs',import.meta.url),'utf8');
 const element=(tag,text)=>({tag,text,children:[],dataset:{},append(...v){this.children.push(...v);},replaceChildren(){this.children=[];},setAttribute(){}});
 const box=element('div');box.dataset.roomFeedback='bath';const error=element('p');
 const room={enabled:true,purposes:[],roles:{main_lights:['lamp'],night_lights:[],hvac:[]},shared_areas:[],hvac:{mode:'none'},setup:{status:'draft',service:true}};
 const context={selectedRooms:()=>[],data:{inventory:{areas:[{id:'bath'}]}},draft:{bath:room},saveError:null,needsReview:false,staleSettings:false,offline:false,language:'en',roomProblems,setup:r=>r.setup,t:k=>k,$:()=>error,el:element,document:{querySelectorAll:()=>[box]},button:(key,action)=>({key,action}),refresh:manual=>{context.refreshed=manual;}};
 runInNewContext(source.slice(source.indexOf('function saveProblems('),source.indexOf('function drawRole(')),context);
 context.updateRoomFeedback();assert.equal(box.className,'room-feedback draft');assert.equal(box.children[1].text,'draft_help');
 context.needsReview=true;context.updateRoomFeedback();assert.equal(box.className,'room-feedback blocked');assert.equal(box.children[1].children[0].text,'changed');box.children[2].action();assert.equal(context.refreshed,true);assert.deepEqual(room.roles.main_lights,['lamp']);
 context.needsReview=false;context.saveError='storage_failed';context.updateRoomFeedback();assert.equal(error.hidden,false);assert.equal(error.textContent,'⚠ storage_failed');assert.equal(box.children[1].children[0].text,'storage_failed');
 context.saveError=null;context.staleSettings=true;context.updateRoomFeedback();assert.equal(box.children[1].children[0].text,'stale_household');
 context.staleSettings=false;context.offline=true;context.updateRoomFeedback();assert.equal(box.children[1].children[0].text,'offline_save');
 context.offline=false;room.setup.status='ready';context.updateRoomFeedback();assert.equal(box.className,'room-feedback ready');assert.equal(error.hidden,true);
});

test('room warning and draft text meet accessible contrast',()=>{
 const css=fs.readFileSync(new URL('../src/shabbat_flow/web/style.css',import.meta.url),'utf8');
 const luminance=hex=>{const [r,g,b]=hex.match(/../g).map(x=>parseInt(x,16)/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return .2126*r+.7152*g+.0722*b;};
 for(const state of ['blocked','draft','ready']){const match=css.match(new RegExp('\\.room-feedback\\.'+state+'\\{background:#([0-9a-f]{6});color:#([0-9a-f]{6})'));assert.ok(match);const a=luminance(match[1]),b=luminance(match[2]);assert.ok((Math.max(a,b)+.05)/(Math.min(a,b)+.05)>=4.5);}
});

test('area classification uses explicit labels and safely converts legacy night policy',()=>{
 const legacy={enabled:true,purposes:[],roles:{main_lights:['main'],night_lights:['night'],hvac:[]},shared_areas:[],hvac:{mode:'none'},setup:{service:true,status:'draft',home:false,lighting:{mode:'daylight',night_enabled:true,night_after_candles:300,morning_after_sunrise:90,off_after_sunrise:180,on_before_sunset:120}}};
 const original=structuredClone(legacy),common=classifyRoom(legacy,'common');assert.deepEqual(legacy,original);
 assert.equal(areaType(common),'common');assert.equal(common.setup.lighting.night_enabled,false);assert.equal(common.setup.lighting.mode,'daylight');assert.equal(common.setup.phases.night_start,300);assert.equal(common.setup.phases.morning_start,90);assert.deepEqual(common.roles,legacy.roles);assert.deepEqual(roomProblems(common,{common}),[]);
 legacy.setup.phases={...phases(common),night_start:360,evening_meal:true};
 const kept=classifyRoom(legacy,'common');assert.equal(kept.setup.phases.night_start,360);assert.ok(kept.setup.phases.evening_meal);
 assert.deepEqual(suggestedAreaTypes({labels:['common']},{common_area:'common'}),['common']);
 assert.deepEqual(suggestedAreaTypes({labels:['common','bath']},{common_area:'common',bathroom_area:'bath'}),['common','bathroom']);
 const inventory={entities:[{id:'main',domain:'light',area_id:'a',labels:['main']},{id:'bath',domain:'light',area_id:'a',labels:['bath']}]};
 common.roles.main_lights=[];
 assert.deepEqual(roleCandidates(inventory,common,'a','main_lights',{main_lights:'main',bathroom:'bath'}).map(e=>e.id),['main']);
});


test('print report contains all dated days and events, localized warnings, and no raw config',async()=>{
 const {renderPrintReport}=await import('../src/shabbat_flow/web/period-report.mjs');
 const bundle=JSON.parse(fs.readFileSync(new URL('../examples/period-preview.json',import.meta.url)));
 const before=JSON.stringify(bundle),catalog=JSON.parse(fs.readFileSync(new URL('../src/shabbat_flow/web/period-i18n.json',import.meta.url)));
 const node=(tag,text='',className='')=>({tag,text,children:[],className,append(...items){this.children.push(...items);},replaceChildren(){this.children=[];},querySelectorAll(){return [];},cloneNode(){const copy=node(this.tag,this.text,this.className);copy.children=this.children.map(c=>c.cloneNode());return copy;},classList:{contains:value=>className.split(' ').includes(value)}});
 const text=n=>[n.text,...n.children.map(text)].join(' ');
 const event=node('div','','event');event.append(node('time','Jan 8 10:00'),node('div','Example light'),node('bdi','Off','state off'));
 const timeline=node('div');timeline.append(node('p','Example retained warning'),node('details','Hidden forecast diagnostic','forecast-diagnostics'),node('p','Brief forecast count','forecast-note'),event);timeline.querySelectorAll=()=>[event];
 for(const language of ['en','he']){
  const report=node('article'),t=key=>{const value=catalog[language][key]??catalogs[language][key];assert.ok(value,key);return value;};
  renderPrintReport({report,bundle,result:{complete:true},t,lang:()=>language,dayLabel:s=>s.id,node,timeline,logo:node('img')});
  assert.equal(report.children.filter(n=>n.tag==='section').length,3);
  assert.match(text(report),/Asia\/Jerusalem/);assert.match(text(report),/2027/);assert.match(text(report),/Example retained warning/);
  const table=report.children.find(n=>n.tag==='table');assert.equal(table.children[0].tag,'thead');assert.equal(table.children[1].children.length,1);
  assert.match(text(table),/Example light.*Off/);assert.doesNotMatch(text(report),/physical_id|schema_version|Hidden forecast diagnostic/);assert.match(text(report),/Brief forecast count/);
  renderPrintReport({report,bundle,result:null,t,lang:()=>language,dayLabel:s=>s.id,node,timeline,logo:node('img')});
  assert.equal(report.children.length,1);assert.equal(text(report).trim(),t('report_unavailable'));
 }
 assert.equal(JSON.stringify(bundle),before);
});

test('lighting map carries planned state, preserves unknown and plots DST days',async()=>{
 const {lightingMap}=await import('../src/shabbat_flow/web/lighting-map.mjs');
 const make=(start,end)=>({config:{loads:{light:{kind:'binary',physical_id:'light'}}},plan:{snapshot:{timezone:'America/New_York',preparation_start:start,end}}});
 const bundle=make('2027-03-13T22:00:00-05:00','2027-03-15T02:00:00-04:00');
 const result={complete:true,events:[{physical_id:'light',local:'2027-03-13T23:00:00-05:00',action:{type:'state',state:'on'},intent:'planner'},{physical_id:'light',local:'2027-03-14T02:00:00-05:00',action:{type:'state',state:'off'},intent:'track_only'}]};
 const days=lightingMap(bundle,result);assert.equal(days.length,3);assert.equal((days[1].end-days[1].start)/3600000,23);
 assert.deepEqual(days[0].lanes[0].intervals.map(x=>x.state),['unknown','on']);assert.deepEqual(days[1].lanes[0].intervals.map(x=>x.state),['on']);assert.equal(days[2].lanes[0].intervals.at(-1).end,Date.parse(bundle.plan.snapshot.end));
 const fall=lightingMap(make('2027-11-07T00:00:00-04:00','2027-11-08T00:00:00-05:00'),{complete:true,events:[]});assert.equal((fall[0].end-fall[0].start)/3600000,25);
 assert.deepEqual(lightingMap(bundle,{complete:false}),[]);
});

test('HVAC whole-period cells preserve partial episodes, state carryover and physical identity',async()=>{
 const {hvacMap}=await import('../src/shabbat_flow/web/hvac-map.mjs');
 const bundle={config:{loads:{a:{physical_id:'unit',kind:'hvac'},alias:{physical_id:'unit',kind:'hvac'},power:{physical_id:'power',kind:'hvac_power'},light:{physical_id:'light',kind:'binary'}}},plan:{snapshot:{segments:[{candle_lighting:'2027-01-08T16:00:00+02:00'}],end:'2027-01-09T17:10:00+02:00'}}};
 const events=[{physical_id:'unit',local:'2027-01-08T15:50:00+02:00',action:{type:'hvac',mode:'heat'}},{physical_id:'unit',local:'2027-01-08T16:07:00+02:00',action:{type:'hvac',mode:'off'}},{physical_id:'unit',local:'2027-01-08T16:11:00+02:00',action:{type:'hvac',mode:'cool'}},{physical_id:'unit',local:'2027-01-08T17:00:00+02:00',intent:'track_only',action:{type:'hvac',mode:'off'}},{physical_id:'power',local:'2027-01-08T17:05:00+02:00',action:{type:'hvac_power',state:'on'}},{physical_id:'power',local:'2027-01-09T17:10:00+02:00',action:{type:'hvac_power',state:'off'}}];
 const input=JSON.stringify({bundle,events}),map=hvacMap(bundle,{complete:true,events});
 assert.equal(map.lanes.length,2);assert.equal(map.lanes[0].cells.length,51);assert.equal(map.lanes[0].cells.at(-1).end-map.lanes[0].cells.at(-1).start,600000);
 assert.deepEqual(map.lanes[0].cells[0].parts.map(v=>v.state),['on','off','on']);assert.equal(map.lanes[0].cells[0].parts[1].end-map.lanes[0].cells[0].parts[1].start,240000);
 assert.equal(map.lanes[0].intervals.at(-1).state,'on');assert.equal(map.lanes[1].intervals[0].state,'unknown');assert.equal(map.lanes[1].intervals.at(-1).end,map.end);
 assert.equal(JSON.stringify({bundle,events}),input);assert.equal(hvacMap(bundle,{complete:false}),null);
});

test('HVAC chart uses actual multi-day and DST elapsed bounds, not fixed 25 hours',async()=>{
 const {hvacMap}=await import('../src/shabbat_flow/web/hvac-map.mjs');
 for(const [start,end,hours] of [['2027-03-13T18:00:00-05:00','2027-03-14T19:00:00-04:00',24],['2027-11-06T18:00:00-04:00','2027-11-07T19:00:00-05:00',26],['2027-01-07T16:00:00+02:00','2027-01-10T17:00:00+02:00',73]]){
  const bundle={config:{loads:{unit:{kind:'hvac_power',physical_id:'unit'}}},plan:{snapshot:{segments:[{candle_lighting:start}],end}}};
  const map=hvacMap(bundle,{complete:true,events:[{physical_id:'unit',local:start,action:{type:'hvac_power',state:'on'}}]});assert.equal((map.end-map.start)/3600000,hours);assert.equal(map.lanes[0].cells.length,hours*2);
 }
});

const {addNap,restDefaults,afternoonActivity,napBathroomTargets}=await import('../src/shabbat_flow/web/period-model.mjs');
test('nap is optional, independently dated, immutable, and copied with wake overrides',()=>{
 const before=structuredClone(period),next=addNap(period,'day_1','room_a');
 assert.deepEqual(period,before);assert.equal(next.plan.naps.length,1);
 assert.equal(next.plan.naps[0].start,'2027-01-08T14:00:00+02:00');
 assert.equal(next.plan.naps[0].end,'2027-01-08T16:00:00+02:00');
 assert.deepEqual(next.plan.naps[0].bathroom_targets,[]);
 next.plan.room_uses[0].hvac_end='2027-01-08T11:00:00+02:00';
 const copied=copyPreviousDay(next,'day_2');
 assert.equal(copied.plan.naps[1].start,'2027-01-09T14:00:00+02:00');
 assert.equal(copied.plan.room_uses.find(u=>u.segment==='day_2').hvac_end,'2027-01-09T11:00:00+02:00');
 assert.deepEqual(parsePeriodDraft(JSON.stringify(copied)),copied);
});
test('saved rest defaults drive new naps but not existing selections',()=>{
 const input=structuredClone(period);
 input.config.profiles.room_a_standard.rest_defaults={nap_after_sunrise:360,nap_duration:90,lead_minutes:30,late_wake_after_sunrise:300};
 const next=addNap(input,'day_1','room_a');
 assert.equal(next.plan.naps[0].start,'2027-01-08T12:00:00+02:00');
 assert.equal(next.plan.naps[0].end,'2027-01-08T13:30:00+02:00');
 assert.equal(next.plan.naps[0].lead_minutes,30);
 assert.deepEqual(next.plan.room_uses,input.plan.room_uses);
});
test('afternoon hosting is disabled initially, only Shabbat, end-relative only at reliable final end',()=>{
 assert.deepEqual(afternoonActivity(period,'day_1'),period);
 const next=afternoonActivity(period,'day_3'),activity=next.plan.meals.at(-1);
 assert.equal(activity.choice,'none');assert.equal(activity.start,'2027-01-10T14:30:00+02:00');
 assert.deepEqual(activity.groups,['meal']);assert.deepEqual(afternoonActivity(next,'day_3'),next);
 const intermediate=structuredClone(period);intermediate.plan.snapshot.segments[0].kind='shabbat';
 const manual=afternoonActivity(intermediate,'day_1').plan.meals.at(-1);
 assert.equal(manual.start,'');assert.equal(manual.end,'');
});

test('independent meal HVAC inherits old combined settings and can be explicitly disabled',async()=>{
 const {mealHvac}=await import('../src/shabbat_flow/web/household-model.mjs');
 const r={purposes:[],roles:{main_lights:['main'],night_lights:[],hvac:['ac']},shared_areas:[],hvac:{mode:'preserve'},setup:{service:true,area_type:'common'}};
 r.setup.phases={...phases(r),daytime_meal:true};assert.equal(mealHvac(r,'daytime'),true);
 r.setup.phases.daytime_hvac=false;assert.equal(mealHvac(r,'daytime'),false);
 r.setup.phases.daytime_meal=false;r.setup.phases.daytime_hvac=true;
 assert.ok(!roomProblems(r,{}).includes('needs_hvac_use'));
 r.setup.phases.morning=true;r.setup.phases.morning_end=60;
 assert.ok(roomProblems(r,{}).includes('phase_morning_bounds'));
 r.setup.phases.constant_main=true;
 assert.ok(roomProblems(r,{}).includes('phase_constant_conflict'));
});

import {renderUnmanaged} from '../src/shabbat_flow/web/observe.mjs';
test('unmanaged forecast rows interleave without changing planner events and keep action colors',()=>{
 const node=(tag,text='',className='')=>({tag,textContent:text,className,children:[],dataset:{},append(...children){for(const child of children){if(child.parent)child.parent.children=child.parent.children.filter(x=>x!==child);child.parent=this;this.children.push(child);}},querySelector(selector){return this.children.find(c=>c.tag===selector);},querySelectorAll(selector){return this.children.filter(c=>selector==='.event'&&c.className==='event');}});
 const root=node('div'),row=node('div','','event'),time=node('time');time.dateTime='2027-01-08T08:00:00Z';row.append(time,node('div','planned'));root.append(row);
 const result={events:[{id:'unchanged'}],unmanaged:{overlay:{unresolved:[],events:[{id:'external',entity_id:'light.hall',source:'automation.hall_off',utc:'2027-01-08T07:00:00Z',local:'2027-01-08T09:00:00+02:00',action:{state:'off'}}]},ownership:{conflicts:[]}}};
 const before=JSON.stringify(result);renderUnmanaged(root,result,{plan:{snapshot:{timezone:'Asia/Jerusalem'}}},{node,t:k=>k,lang:()=> 'en',icon:()=>node('span')});
 const rows=root.querySelectorAll('.event');assert.equal(rows.length,2);assert.equal(rows[0].children[2].className,'state off');assert.ok(rows[0].children[1].children.some(n=>n.textContent==='observe_unmanaged'));assert.equal(JSON.stringify(result),before);
});
test('observe UI strings have English and Hebrew parity',()=>{
 const labels=JSON.parse(fs.readFileSync(new URL('../src/shabbat_flow/web/period-i18n.json',import.meta.url)));
 for(const key of Object.keys(labels.en).filter(k=>k.startsWith('observe_'))){assert.ok(labels.en[key]);assert.ok(labels.he[key]);}
});

import {thermalModel,lineSegments,renderObservationPrint} from '../src/shabbat_flow/web/thermal-report.mjs';
test('thermal reports retain missing gaps, target ranges and source without mutating evidence',()=>{
 const reading=(v)=>({celsius:v});
 const data={run:{start:'2027-01-08T14:00:00Z',end:'2027-01-09T15:00:00Z',bundle:{plan:{snapshot:{timezone:'Asia/Jerusalem'}}},thermal:{outdoor:{entity_id:'weather.sample'},climates:[{entity_id:'climate.study',area_name:'Study'}],samples:[
  {due:'2027-01-08T14:00:00Z',status:'sampled',climates:{'climate.study':{mode:'heat',hvac_action:'idle',current_temperature:reading(20),target_low:reading(21),target_high:reading(23)}},outdoor:{current_temperature:reading(12)}},
  {due:'2027-01-08T15:00:00Z',status:'missing'},
  {due:'2027-01-08T16:00:00Z',status:'sampled',climates:{'climate.study':{mode:'off',current_temperature:reading(22),target_temperature:reading(23)}},outdoor:{current_temperature:reading(13)}}
 ]}}};const before=JSON.stringify(data),model=thermalModel(data),points=model.lanes[0].points;
 assert.equal(model.source,'weather.sample');assert.equal(points[0].low,21);assert.equal(points[0].target,null);assert.equal(points[1].current,null);assert.equal(points[2].mode,'off');
 assert.equal(lineSegments(points,'current').length,2);assert.equal(lineSegments(points,'outdoor').length,2);assert.equal(model.low,11);assert.equal(model.high,24);
 assert.equal(JSON.stringify(data),before);assert.equal(thermalModel({run:{}}),null);
});
test('observation print renders frozen provenance and handles legacy runs without a chart',()=>{
 const node=(tag,text='',className='')=>({tag,textContent:text,className,children:[],append(...items){this.children.push(...items);},replaceChildren(){this.children=[];}});
 const data={run:{id:'frozen-observation',snapshot_hash:'frozen-digest',start:'2027-01-08T14:00:00Z',end:'2027-01-09T15:00:00Z'}};
 const report=node('section');renderObservationPrint({report,data,node,t:k=>k,lang:()=> 'en',logo:null});
 const flatten=n=>[n.textContent,...n.children.flatMap(flatten)].join(' ');
 assert.match(flatten(report),/frozen-observation.*frozen-digest/);assert.match(flatten(report),/observe_thermal_legacy/);
 assert.match(flatten(report),/Jan 8, 2027/);assert.match(flatten(report),/UTC/);
});

test('zone ranking uses minute durations across the period, keeps inactive and unknown distinct',()=>{
 const make=(id,on,off,seen,mode)=>({id,on,off,seen,mode});const entries=[make('b',60,60,true,'off'),make('a',600,0,true,'cool'),make('d',0,600,false,'off'),make('c',0,0,false,'unknown')];
 const data={run:{start:'2027-01-01T00:00Z',end:'2027-01-02T00:00Z',bundle:{plan:{snapshot:{timezone:'UTC'}}},thermal:{climates:entries.map(e=>({entity_id:e.id})),activity:{totals:Object.fromEntries(entries.map(e=>[e.id,{on_seconds:e.on,off_seconds:e.off,unknown_seconds:0,seen_on:e.seen}]))},samples:[{due:'2027-01-01T00:00Z',status:'sampled',climates:Object.fromEntries(entries.map(e=>[e.id,{mode:e.mode}]))}]}}};
 const before=JSON.stringify(data),lanes=thermalModel(data).lanes;
 assert.deepEqual(lanes.map(l=>l.target.entity_id),['a','b','d','c']);assert.deepEqual(lanes.map(l=>l.group),['active','active','inactive','unknown']);assert.equal(lanes[0].onMinutes,10);assert.equal(JSON.stringify(data),before);
 delete data.run.thermal.activity;assert.equal(thermalModel(data).lanes[0].onMinutes,null);
});

import {thermalBands} from '../src/shabbat_flow/web/thermal-report.mjs';
test('room bands associate exact room, retain naps/meals and break observed light at gaps',()=>{
 const at=h=>`2027-01-01T${String(h).padStart(2,'0')}:00:00Z`;
 const run={start:at(0),end:at(6),last_sample:at(5),gaps:[{start:at(2),end:at(3)}],mapping:{lamp:{entity_id:'light.study'}},bundle:{config:{loads:{lamp:{kind:'binary',physical_id:'lamp',display:{room:'study',role:'main_lights'}}},groups:{meal:{rules:[{targets:['lamp']}]}}},plan:{room_uses:[{room:'study',purpose:'sleeping',start:at(1),end:at(2)},{room:'other',purpose:'sleeping',start:at(0),end:at(6)}],naps:[{room:'study',start:at(4),end:at(5)}],meals:[{choice:'family',start:at(3),end:at(4),groups:['meal']}]}},preview:{events:[{physical_id:'lamp',utc:at(0),intent:'set_state',action:{type:'state',state:'on'}}]},changes:[{physical_id:'lamp',observed_at:at(0),state:'on'},{physical_id:'lamp',observed_at:at(4),state:'off'}]};
 const bands=thermalBands(run,{planner_room_id:'study'});assert.deepEqual(bands.filter(b=>b.kind==='use').map(b=>b.purpose),['sleeping','nap','meal']);
 const actual=bands.find(b=>b.kind==='observed').intervals;assert.equal(actual.find(i=>i.start===Date.parse(at(2))).state,'unknown');assert.equal(actual.at(-1).state,'unknown');assert.equal(actual.find(i=>i.start===Date.parse(at(4))).state,'off');assert.deepEqual(thermalBands(run,{planner_room_id:'not-mapped'}),[]);
});

test('standalone studies show explicit observed lighting and references without invented plans',()=>{
 const start='2027-01-01T00:00:00Z',end='2027-01-02T00:00:00Z';
 const run={kind:'climate_study',start,end,last_sample:end,bundle:{plan:{snapshot:{timezone:'UTC'}},config:{loads:{lamp:{physical_id:'lamp',kind:'binary',display:{room:null,role:'main_lights'}}}}},mapping:{lamp:{entity_id:'light.example'}},changes:[{physical_id:'lamp',observed_at:start,state:'on'}],thermal:{climates:[{entity_id:'climate.example',study_lights:['light.example'],reference:{entity_id:'sensor.reference'}}],samples:[{due:start,status:'sampled',climates:{'climate.example':{mode:'heat',current_temperature:{celsius:23}}},references:{'climate.example':{current_temperature:{celsius:21}}}}]}};
 const lane=thermalModel({run}).lanes[0];assert.equal(lane.points[0].reference,21);assert.equal(lane.points[0].current,23);
 assert.deepEqual(lane.bands.map(b=>b.kind),['observed']);assert.equal(lane.bands[0].intervals[0].state,'on');
 run.thermal.climates[0].study_lights=[];assert.deepEqual(thermalModel({run}).lanes[0].bands,[]);
 run.thermal.samples[0].status='missing';assert.equal(thermalModel({run}).lanes[0].points[0].reference,null);
});

test('climate study reports have no plan-compliance heading and retain private user notes as text',()=>{
 const node=(tag,text='',className='')=>({tag,textContent:text,className,children:[],append(...items){this.children.push(...items);},replaceChildren(){this.children=[];}});
 const data={run:{kind:'climate_study',id:'study-only',snapshot_hash:'selection-digest',start:'2027-01-05T14:00:00Z',end:'2027-01-06T14:00:00Z',finished_at:'2027-01-05T16:00:00Z',bundle:{study:{note:'<b>Comfort note</b>'},plan:{snapshot:{timezone:'Asia/Jerusalem'}}}}};
 const report=node('section');renderObservationPrint({report,data,node,t:k=>k,lang:()=> 'en',logo:null});
 const flatten=n=>[n.textContent,...n.children.flatMap(flatten)].join(' '),text=flatten(report);
 assert.match(text,/study_report_title/);assert.match(text,/study_context/);assert.match(text,/<b>Comfort note<\/b>/);assert.doesNotMatch(text,/observe_report_totals|observe_hint|observe_run_id/);
});

test('study switch activity stays separate from light signals and preserves unknown gaps',()=>{
 const start='2027-01-05T10:00:00Z',middle='2027-01-05T10:30:00Z',end='2027-01-05T11:00:00Z';
 const run={kind:'climate_study',start,end,last_sample:end,bundle:{config:{loads:{outlet:{kind:'binary',physical_id:'outlet',display:{role:'study_lighting',signal_kind:'switch'}}}}},mapping:{outlet:{entity_id:'switch.desk'}},changes:[{physical_id:'outlet',observed_at:start,state:'on'},{physical_id:'outlet',observed_at:middle,state:'off'}],gaps:[{start,end:middle}]};
 const bands=thermalBands(run,{study_lights:['switch.desk']});assert.equal(bands.length,1);assert.equal(bands[0].signalKind,'switch');assert.equal(bands[0].kind,'observed');assert.deepEqual(bands[0].intervals.map(i=>i.state),['unknown','off']);
 delete run.bundle.config.loads.outlet.display.signal_kind;assert.equal(thermalBands(run,{study_lights:['switch.desk']})[0].signalKind,'switch');
});

test('clock rest defaults resolve local afternoon, boundary end and late wake; reject DST gaps and folds',async()=>{
 const {lateWakeTime,restClockTime}=await import('../src/shabbat_flow/web/period-model.mjs');
 const b=structuredClone(period),profile=Object.values(b.config.profiles).find(p=>p.room==='room_a'&&p.label.en==='Standard');
 profile.rest_defaults={...restDefaults(profile),nap_start_mode:'clock',nap_start_time:'14:00',nap_end_mode:'period_end',wake_mode:'clock',wake_time:'11:00'};
 const n=addNap(b,'day_1','room_a').plan.naps.at(-1),seg=b.plan.snapshot.segments[0];
 assert.equal(n.start.slice(11,16),'14:00');assert.equal(n.end,seg.end);
 assert.equal(lateWakeTime(profile,seg,b.plan.snapshot.timezone).slice(11,16),'11:00');
 assert.throws(()=>restClockTime({sunrise:'2027-03-14T12:00:00Z'},'02:30','America/New_York'));
 assert.throws(()=>restClockTime({sunrise:'2027-11-07T12:00:00Z'},'01:30','America/New_York'));
 profile.rest_defaults.nap_end_mode='clock';profile.rest_defaults.nap_end_time='13:00';assert.throws(()=>addNap(b,'day_1','room_a'));
});
test('HH:MM offsets preserve signed minutes and reject malformed or out-of-range text',async()=>{
 const {parseOffset,formatOffset}=await import('../src/shabbat_flow/web/time-input.mjs');
 for(const n of [-180,-60,0,360,1440])assert.equal(parseOffset(formatOffset(n)),n);
 for(const v of ['1:60','abc','01:99','1','-00:01'])assert.equal(parseOffset(v,0,720),null);
 assert.equal(parseOffset('12:01',0,720),null);
});
test('icon names accept HA namespaces but never URLs or markup',async()=>{
 const {validIcon}=await import('../src/shabbat_flow/web/ha-icons.mjs');
 assert.equal(validIcon('mdi:bed'),'mdi:bed');assert.equal(validIcon('custom:lamp'),'custom:lamp');
 for(const v of ['https://example.com/icon','<svg>',null,'mdi:bad name'])assert.equal(validIcon(v),null);
});

test('existing automation grouping preserves separate actions and raw records',async()=>{
 const {groupExistingEvents}=await import('../src/shabbat_flow/web/observe.mjs');
 const a={source:'automation.example',utc:'2027-01-08T21:00:00Z',action:{type:'state',state:'off'},entity_id:'light.porch'};
 const events=[a,{...a,entity_id:'light.deck'},{...a,action:{type:'state',state:'on'},entity_id:'light.shelf'},{...a,utc:'2027-01-08T22:00:00Z'}];
 const before=JSON.stringify(events),groups=groupExistingEvents(events);
 assert.equal(groups.length,3);assert.equal(groups[0].devices.length,2);assert.equal(JSON.stringify(events),before);
});

test('study zone selection keeps controls and other zones, and defers cross-room devices',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=fs.readFileSync(new URL('../src/shabbat_flow/web/study.mjs',import.meta.url),'utf8').replace(/^import .*;\n/gm,'').replace(/init\(\);\s*$/,'');
 class Element{
  constructor(tag){this.tag=tag;this.children=[];this.style={};}
  append(...items){for(const item of items){if(item.tag==='fragment')this.children.push(...item.children);else this.children.push(item);}}
  prepend(...items){this.children.unshift(...items);}
  replaceChildren(...items){this.children=[];this.append(...items);}
  insertBefore(item,before){const index=this.children.indexOf(before);this.children.splice(index,0,...(item.tag==='fragment'?item.children:[item]));}
  setAttribute(){}
 }
 const roots=new Map(),document={documentElement:{},createElement:tag=>new Element(tag),createDocumentFragment:()=>new Element('fragment'),getElementById:id=>{if(!roots.has(id))roots.set(id,new Element('root'));return roots.get(id);}};
 const sources={climates:Array.from({length:100},(_,i)=>({entity_id:'climate.'+i,area_id:'room'+i,name:'Zone '+i})),lights:Array.from({length:2000},(_,i)=>({entity_id:'switch.'+i,area_id:'room'+(i%100),name:'Signal '+i})),references:[]};
 let observations=0;
 const context={fetch:()=>{},document,window:{addEventListener(){}},itemIcon:()=>new Element('icon'),setupObservation:()=>observations++,structuredClone,sourcesFixture:sources};
 runInNewContext(source+'\ncatalogs={en:{}};sources=sourcesFixture;draw();',context);
 const root=roots.get('study-setup'),cards=root.children.filter(e=>e.tag==='section'),all=e=>[e,...e.children.flatMap(all)],box=card=>all(card).find(e=>e.type==='checkbox');
 const note=root.children.find(e=>e.children.some(c=>c.tag==='textarea')).children.find(e=>e.tag==='textarea');note.value='Keep context';note.oninput();
 box(cards[0]).checked=true;box(cards[0]).onchange();
 assert.equal(observations,1);assert.equal(root.children.filter(e=>e.tag==='section')[0],cards[0]);
 assert.equal(all(cards[0]).filter(e=>e.type==='checkbox').length,21);
 const firstSignal=all(cards[0]).filter(e=>e.type==='checkbox')[1];firstSignal.checked=true;firstSignal.onchange();
 box(cards[1]).checked=true;box(cards[1]).onchange();assert.equal(firstSignal.checked,true);assert.equal(note.value,'Keep context');assert.equal(observations,1);
 const more=all(cards[0]).find(e=>e.tag==='details');assert.equal(all(more).filter(e=>e.type==='checkbox').length,0);more.open=true;more.ontoggle();assert.equal(all(more).filter(e=>e.type==='checkbox').length,50);more.ontoggle();assert.equal(all(more).filter(e=>e.type==='checkbox').length,50);
 const next=more.children.find(e=>e.tag==='button');next.onclick();assert.equal(all(more).filter(e=>e.type==='checkbox').length,100);
 runInNewContext('catalogs.he={};language="he";draw();',context);
 const translatedCards=root.children.filter(e=>e.tag==='section');assert.equal(document.documentElement.dir,'rtl');assert.equal(box(translatedCards[0]).checked,true);assert.equal(all(translatedCards[0]).filter(e=>e.type==='checkbox')[1].checked,true);assert.equal(all(translatedCards[0]).find(e=>e.tag==='details').children.length,1);
 assert.equal(all(translatedCards[0]).find(e=>e.tag==='option').textContent,'study_builtin_default');
 assert.equal(all(translatedCards[0]).find(e=>e.tag==='label').children[0].type,'checkbox');
 runInNewContext('language="en";draw();',context);assert.equal(document.documentElement.dir,'ltr');
});

test('HA icons render once per name in their owner document and copy SVG into the iframe',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=fs.readFileSync(new URL('../src/shabbat_flow/web/ha-icons.mjs',import.meta.url),'utf8').replace(/^import .*;\n/gm,'').replace(/export /g,'');
 let created=0,removed=0,imported=0;
 const svg={localName:'svg',querySelector:()=>({}),cloneNode:()=>({kind:'svg'})};
 const parent={customElements:{get:()=>true},document:{body:{append(){}},createElement:()=>{created++;return {style:{},setAttribute(){},shadowRoot:{querySelectorAll:()=>[svg]},remove(){removed++;}};}}};
 const document={createElement:()=>({setAttribute(){},replaceChildren(node){this.rendered=node;}}),importNode:node=>{imported++;return {...node};}};
 const context={window:{parent},document,setTimeout,request:()=>{},Map};
 runInNewContext(source+'\nthis.a=haIcon("mdi:lamp");this.b=haIcon("mdi:lamp");',context);
 await Promise.resolve();
 assert.equal(created,1);assert.equal(removed,1);assert.equal(imported,2);assert.equal(context.a.rendered.kind,'svg');assert.notEqual(context.a.rendered,context.b.rendered);
});

const {setMealChoice,markDayHomeFromUse}=await import('../src/shabbat_flow/web/period-model.mjs');
const {activitySummary}=await import('../src/shabbat_flow/web/activity-model.mjs');
test('explicit room and meal selections mark only their day home and removal never marks away',()=>{
 const away=setDayHome(setDayHome(period,'day_1','away'),'day_2','away'),before=structuredClone(away);
 let next=setRoomChoice(away,'day_1','room_a','sleeping','existing');
 assert.deepEqual(next.plan.snapshot.segments.map(s=>dayHomeState(next.plan,s)),['home','away','home']);
 next=setRoomChoice(next,'day_1','room_a','sleeping','off');
 assert.equal(dayHomeState(next.plan,next.plan.snapshot.segments[0]),'home');
 const meal=away.plan.meals.find(m=>m.segment==='day_2');
 next=setMealChoice(away,meal.id,'family');assert.equal(dayHomeState(next.plan,next.plan.snapshot.segments[1]),'home');
 next=setMealChoice(next,meal.id,'none');assert.equal(dayHomeState(next.plan,next.plan.snapshot.segments[1]),'home');
 assert.equal(dayHomeState(setMealChoice(away,meal.id,'away').plan,away.plan.snapshot.segments[1]),'away');
 assert.deepEqual(away,before);
});
test('explicit-use defaults preserve advanced partial availability and unavailable day choices',()=>{
 const custom=structuredClone(period);custom.plan.availability[0].end=custom.plan.snapshot.segments[0].sunrise;
 assert.equal(dayHomeState(custom.plan,custom.plan.snapshot.segments[0]),'custom');
 const next=setRoomChoice(custom,'day_1','room_a','sleeping','room_a_early');
 assert.deepEqual(next.plan.availability,custom.plan.availability);
 const unset=setDayHome(period,'day_1','unset');
 assert.equal(dayHomeState(markDayHomeFromUse(unset,'day_1').plan,unset.plan.snapshot.segments[0]),'home');
 const nap=addNap(setDayHome(period,'day_1','away'),'day_1','room_a');
 assert.equal(dayHomeState(nap.plan,nap.plan.snapshot.segments[0]),'home');
});
test('home activity separates concurrent persisted runs, terminal runs and browser drafts',()=>{
 const run=(id,kind,status)=>({id,kind,status,start:period.plan.snapshot.start,end:period.plan.snapshot.end,timezone:'Asia/Jerusalem'});
 const listing={runs:[run('a','plan','observing'),run('b','climate_study','observing'),run('c','plan','scheduled'),run('d','plan','completed'),run('e','climate_study','stopped')]};
 const summary=activitySummary(listing,JSON.stringify(period),0);
 assert.deepEqual(summary.active.map(r=>r.id),['a','b','c']);
 assert.equal(summary.latest.plan.status,'completed');assert.equal(summary.latest.climate_study.status,'stopped');
 assert.equal(summary.draft.past,false);assert.equal(activitySummary(listing,JSON.stringify(period),Infinity).draft.past,true);
 assert.equal(activitySummary(null,'broken').draftError,true);
 assert.deepEqual(activitySummary({runs:[]},null).active,[]);
 assert.equal(activitySummary({runs:[]},null).draft,null);
 assert.equal(listing.runs[2].status,'scheduled');
});

test('home overview renders concurrent run links and distinguishes API failure from no runs',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=fs.readFileSync(new URL('../src/shabbat_flow/web/household.mjs',import.meta.url),'utf8');
 const el=(tag,text)=>({tag,text,dataset:{},children:[],append(...items){this.children.push(...items);},replaceChildren(...items){this.children=[...items];}}),root=el('section');
 const run=(id,kind,status)=>({id,kind,status,start:'2027-01-08T16:00:00+02:00',end:'2027-01-09T18:00:00+02:00',timezone:'Asia/Jerusalem'});
 const context={executionWords,el,$:()=>root,t:k=>k,language:'en',activitySummary,activityError:false,activityData:{runs:[run('a'.repeat(32),'plan','scheduled'),run('b'.repeat(32),'climate_study','observing')]},localStorage:{getItem:()=>null}};
 runInNewContext(source.slice(source.indexOf('function renderActivity('),source.indexOf('async function refreshActivity(')),context);
 const all=()=>{const walk=n=>[n,...n.children.flatMap(walk)];return walk(root);};
 context.renderActivity();assert.ok(all().some(n=>n.text==='activity_scheduled'));assert.ok(all().some(n=>n.text==='activity_observing'));
 assert.equal(all().filter(n=>n.href?.includes('observation.html?run=')).length,2);
 const preserved=root.children[1];context.renderActivity();assert.equal(root.children[1],preserved);
 context.activityError=true;context.renderActivity();assert.equal(all().filter(n=>n.text==='activity_unavailable').length,2);assert.ok(!all().some(n=>n.href?.includes('observation.html?run=')));
 context.activityError=false;context.activityData={runs:[]};context.renderActivity();assert.equal(all().filter(n=>n.text==='activity_none').length,2);
 context.localStorage.getItem=()=>{throw Error('unavailable');};context.renderActivity();assert.ok(all().some(n=>n.text==='activity_draft_unavailable'));
});

// Flexible planning choices never mutate existing saved drafts implicitly.
test('flexible meal presets are explicit and immutable',async()=>{
 const {mealPreset,emptyFlex,words}=await import('../src/shabbat_flow/web/flexible.mjs');
 const bundle={config:{},plan:{meals:[{id:'dinner',start:'2027-01-08T18:00:00+02:00',end:'2027-01-08T21:00:00+02:00'}]}};
 const old=structuredClone(bundle),next=mealPreset(bundle,'dinner','early');
 assert.deepEqual(bundle,old);assert.equal(next.plan.flex.meals[0].duration,90);assert.equal(next.plan.meals[0].end,old.plan.meals[0].end);
 assert.deepEqual(mealPreset(next,'dinner','custom').plan.flex.meals,[]);
 assert.deepEqual(Object.keys(words.en).sort(),Object.keys(words.he).sort());assert.deepEqual(emptyFlex().windows,[]);
});

test('activity day copy remaps meal bindings and preserves anchor offsets',async()=>{
 const {mealPreset,emptyFlex,effectiveMealEnd}=await import('../src/shabbat_flow/web/flexible.mjs');
 const original=structuredClone(period),meal=original.plan.meals.find(m=>m.segment==='day_1');
 original.plan.flex=emptyFlex();original.plan.flex.windows.push({id:'activity_1',segment:'day_1',room:'room_a',start:meal.start,end:meal.end,meal:meal.id,timing:{start:{anchor:'candle_lighting',offset_minutes:30}}});
 const chosen=mealPreset(original,meal.id,'early'),copied=copyPreviousDay(chosen,'day_2');
 const window=copied.plan.flex.windows.find(w=>w.segment==='day_2'),nextMeal=copied.plan.meals.find(m=>m.id===window.meal);
 assert.equal(nextMeal.segment,'day_2');assert.deepEqual(window.timing,original.plan.flex.windows[0].timing);
 assert.equal(+new Date(effectiveMealEnd(copied,nextMeal))-+new Date(nextMeal.start),120*60000);
 assert.equal(chosen.plan.flex.windows.length,1);
});
test('report filters, bilingual review fields and private export boundary',async()=>{
 const {reviewWords,blankReview,filterReports,reviewBundle}=await import('../src/shabbat_flow/web/review-ui.mjs');
 assert.deepEqual(Object.keys(reviewWords.en).sort(),Object.keys(reviewWords.he).sort());
 const a={id:'a',start:'2027-01-01T10:00:00Z',kind:'plan',status:'completed',reviewed:false},b={...a,id:'b',start:'2027-01-02T10:00:00Z',kind:'climate_study',reviewed:true};
 assert.deepEqual(filterReports([a,b],{}).map(r=>r.id),['b','a']);assert.deepEqual(filterReports([a,b],{type:'plan',review:'needs_review'}),[a]);
 const review=blankReview();assert.equal(review.overall,null);assert.equal(review.decision,'proposed');
 const out=reviewBundle({run:{id:'a',snapshot_hash:'hash',start:a.start,end:b.start,bundle:{plan:{snapshot:{timezone:'UTC'}}},actor:'private'},review:{value:review},performance:{}});
 assert.equal(out.run_id,'a');assert.equal(out.device_commands_sent,0);assert.ok(!JSON.stringify(out).includes('private'));assert.ok(!('bundle' in out));
});
test('planner has one top action per command and no duplicate export IDs',()=>{
 const html=fs.readFileSync(new URL('../src/shabbat_flow/web/period.html',import.meta.url),'utf8');
 for(const id of ['preview','save','export','export-pdf','load','delete','reset'])assert.equal([...html.matchAll(new RegExp('id="'+id+'"','g'))].length,1);
 assert.ok(html.indexOf('id="plan-commands"')<html.indexOf('id="period-form"'));assert.ok(html.includes('id="workflow-note"'));
});

test('stored PDF commands have complete default language catalogs',async()=>{
 const {pdfWords}=await import('../src/shabbat_flow/web/pdf-download.mjs');
 assert.deepEqual(Object.keys(pdfWords.en).sort(),Object.keys(pdfWords.he).sort());
 for(const language of ['en','he'])for(const key of ['generate','working','ready','download','open','share','error','stale','print'])assert.ok(pdfWords[language][key]);
});


test('temperature units stay LTR within Hebrew text',async()=>{
 const {isolateTemperatureText}=await import('../src/shabbat_flow/web/thermal-report.mjs');
 const value=isolateTemperatureText('טמפרטורה (°C): 23 °C');
 assert.ok(value.includes('\u200e(°C)\u200e'));
 assert.ok(value.includes('\u200e23 °C\u200e'));
 assert.equal(isolateTemperatureText(value),value);
});


test('permanent fan candidates use optional entity/device labels without assigning devices',()=>{
 const inventory={entities:[{id:'f',domain:'fan',area_id:'bed',labels:['fans']},{id:'s',domain:'switch',area_id:'bed',device_labels:['fans']},{id:'plain',domain:'switch',area_id:'bed'},{id:'light',domain:'light',area_id:'bed',labels:['fans']},{id:'elsewhere',domain:'fan',area_id:'other'},{id:'selected',domain:'switch',area_id:'other'}]};
 const room={roles:{fans:['selected']}};
 const filters={...emptyLabelFilters(),fans:'fans'};
 const ids=(options)=>roleCandidates(inventory,room,'bed','fans',filters,options).map(e=>e.id);
 assert.deepEqual(ids(),['f','s','selected']);
 assert.deepEqual(ids({allRoom:true}),['f','s','plain','selected']);
 assert.ok(ids({allRoom:true,allAreas:true}).includes('elsewhere'));
 assert.deepEqual(room.roles.fans,['selected']);
 assert.ok(roleCandidates(inventory,{roles:{}},'bed','fans',emptyLabelFilters()).some(e=>e.id==='plain'));
 assert.deepEqual(ids({}),['f','s','selected']);
});

const {normalizeAwayMeals}=await import('../src/shabbat_flow/web/period-model.mjs');
const {executionWords}=await import('../src/shabbat_flow/web/execution.mjs');
test('away defaults meals and returning home asks fresh choices',()=>{
 const away=setDayHome(period,'day_1','away');
 assert.ok(away.plan.meals.filter(m=>m.segment==='day_1').every(m=>m.choice==='away'||m.choice==='none'));
 const home=setDayHome(away,'day_1','home');assert.ok(home.plan.meals.filter(m=>m.segment==='day_1').every(m=>m.choice==='unset'||m.choice==='none'));
 for(const m of away.plan.meals.filter(m=>m.segment==='day_1'))m.choice='unset';
 const before=structuredClone(away),normalized=normalizeAwayMeals(away);assert.deepEqual(away,before);
 assert.ok(normalized.plan.meals.filter(m=>m.segment==='day_1').every(m=>m.choice==='away'||m.choice==='none'));
 assert.deepEqual(Object.keys(executionWords.en).sort(),Object.keys(executionWords.he).sort());
});

const {rehearsalWords}=await import('../src/shabbat_flow/web/rehearsal.mjs');
test('rehearsal strings cover both default languages and keep explicit control boundaries',()=>{
 assert.deepEqual(Object.keys(rehearsalWords.en).sort(),Object.keys(rehearsalWords.he).sort());
 assert.match(rehearsalWords.en.intro,/never schedules the weekend/);
 assert.match(rehearsalWords.en.apply,/now/);
});

test('duration nap clips at the day boundary without changing room defaults or other rooms',()=>{
 const b=structuredClone(period),profile=Object.values(b.config.profiles).find(p=>p.room==='room_a'&&p.label.en==='Standard');
 profile.rest_defaults={...restDefaults(profile),nap_start_mode:'clock',nap_start_time:'16:00',nap_end_mode:'duration',nap_duration:180};
 const original=structuredClone(b);const next=addNap(b,'day_1','room_a'),nap=next.plan.naps.at(-1);
 assert.equal(nap.end,next.plan.snapshot.segments[0].end);assert.equal(nap.room,'room_a');assert.deepEqual(b,original);assert.equal(profile.rest_defaults.nap_duration,180);
});

test('planner blockers retain affected room context for a missing inventory entry',async()=>{
 const {plannerIssueDetails}=await import('../src/shabbat_flow/web/household-model.mjs');
 const inv={areas:[{id:'room_a',name:'Room A'}],entities:[{id:'registry_b',entity_id:'switch.example_b',name:'Example B'}]};
 const rooms={room_a:{roles:{main_lights:['registry_missing','registry_b']},shared_areas:[]}};
 const details=plannerIssueDetails([{code:'missing_entity',id:'registry_missing'},{code:'unavailable_entity',id:'switch.example_b'}],inv,rooms);
 assert.equal(details[0].entity_id,'registry_missing');assert.deepEqual(details[0].areas,[{id:'room_a',name:'Room A'}]);
 assert.equal(details[1].name,'Example B');assert.equal(details[1].areas[0].id,'room_a');
 assert.deepEqual(plannerIssueDetails([],inv,rooms),[]);
 assert.equal(plannerIssueDetails([{code:'missing_entity',id:'orphan'}],inv,rooms)[0].name,'orphan');
});

test('supervised rehearsal readiness needs only eligible selection and consent',async()=>{
 const {rehearsalSelectionState:state}=await import('../src/shabbat_flow/web/rehearsal.mjs');
 const entry=(checked,disabled=false)=>({choice:{checked,disabled}});
 assert.equal(state([entry(false),entry(true,true)],true,true).reason,'select_devices');
 assert.equal(state([entry(true),entry(true,true)],true,true).count,1);
 assert.equal(state([entry(true)],true,true).canApply,true);
 assert.equal(state([entry(true)],true,false).reason,'consent_needed');
 assert.equal(state([entry(true)],false,true).reason,'rehearsal_observance');
 assert.equal(state(Array.from({length:101},()=>entry(true)),true,true).reason,'selection_limit');
});
