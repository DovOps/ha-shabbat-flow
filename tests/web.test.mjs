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
  assert.deepEqual(next.plan.meals,period.plan.meals);
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
  const context={updateRoomFeedback:()=>{},staleSettings:false,saveError:null,labelFilters:{...emptyLabelFilters(),bathroom:"draft_label"},emptyLabelFilters,data:structuredClone(initial),next:structuredClone(initial),draft:{room_a:{enabled:false}},dirty:false,saving:false,needsReview:false,offline:false,structuredClone,
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
  const button={},room={enabled:true,purposes:['sleeping'],roles:{main_lights:['fictional_light'],night_lights:[],hvac:[]},shared_areas:[],hvac:{mode:'none'}};
  const context={manualZone:null,manualCalendar:true,automatic:null,structuredClone,dirty:false,opening:false,observance:'',dateValues:{candles:'2027-01-08T16:00:00+02:00',sunrise:'',end:'2027-01-09T18:00:00+02:00'},kind:'shabbat',language:'en',catalogs:{en:{invalid_mapping:'Mapping issue',workspace_storage_failed:'Storage issue'}},data:{settings:{rooms:{},revision:1},inventory:{timezone:'Asia/Jerusalem',revision:'a'},issues:[]},
    $:id=>id==='plan'?button:box,t:key=>key,el:(_,text)=>text,zonedISO:d=>d.toISOString(),api:async()=>{throw new Error('unexpected request');},sessionStorage:{setItem(){}},location:{href:''}};
  runInNewContext(code,context);
  await context.openPlan();assert.deepEqual(box.messages,['choose_observance','missing_sunrise','needs_roles']);assert.ok(box.focused&&box.visible);assert.equal(context.location.href,'');
  context.dirty=true;await context.openPlan();assert.ok(box.messages.includes('needs_save'));
  context.dirty=false;context.observance='israel';context.dateValues.sunrise='2027-01-09T06:00:00+02:00';context.data.settings.rooms={room_a:room};
  context.api=async()=>{throw new Error('invalid_mapping');};await context.openPlan();assert.deepEqual(box.messages,['invalid_mapping']);assert.equal(button.disabled,false);
  let calls=0,resolve;context.api=()=>{calls++;return new Promise(r=>resolve=r);};
  const pending=context.openPlan();assert.equal(button.disabled,true);assert.deepEqual(box.messages,['opening_plan']);await context.openPlan();assert.equal(calls,1);
  resolve({plan:{}});await pending;assert.equal(context.location.href,'./period.html?household=1');assert.equal(button.disabled,false);
  context.location.href='';context.api=async()=>({plan:{}});context.sessionStorage.setItem=()=>{throw new Error('blocked');};await context.openPlan();assert.deepEqual(box.messages,['workspace_storage_failed']);assert.equal(context.location.href,'');
  context.dateValues.sunrise='2027-01-08T06:00:00+02:00';await context.openPlan();assert.deepEqual(box.messages,['date_order']);
});

test('automatic calendar passes the whole snapshot and refresh preserves manual dates',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=fs.readFileSync(new URL('../src/shabbat_flow/web/household.mjs',import.meta.url),'utf8');
 const code=source.slice(source.indexOf('function planProblems('),source.indexOf('async function boot('));
 const snapshot=structuredClone(period.plan.snapshot);snapshot.start='2099-01-01T16:00:00+02:00';
 const box={replaceChildren(){},append(){},focus(){},scrollIntoView(){}},button={};let received;
 const context={manualZone:null,manualCalendar:false,automatic:{status:'ready',snapshot},structuredClone,dirty:false,opening:false,language:'en',catalogs:{en:{}},
 data:{settings:{revision:1,rooms:{a:{enabled:true,purposes:['sleeping'],roles:{main_lights:['load'],night_lights:[],hvac:[]},shared_areas:[],hvac:{mode:'none'}}}},inventory:{revision:'a'},issues:[]},
 $:id=>id==='plan'?button:box,t:v=>v,el:(_,v)=>v,api:async(_,body)=>{received=body;return {plan:{}};},sessionStorage:{setItem(){}},location:{href:''}};
 runInNewContext(code,context);await context.openPlan();assert.deepEqual(received.snapshot,snapshot);assert.notEqual(received.snapshot,snapshot);assert.equal(received.snapshot.segments.length,3);
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
 const context={updateRoomFeedback:()=>{},staleSettings:false,offline:false,saveError:null,postShutoff:false,labelFilters:emptyLabelFilters(),emptyLabelFilters,needsReview:false,saving:false,dirty:true,draft:{example:{enabled:true}},data:{settings:{revision:3},inventory:{revision:'a'}},structuredClone,
  document:{querySelectorAll:()=>controls},$:()=>button,status:()=>{},fail:()=>{},wizardError:()=>{},catalogs:{en:{}},language:'en',api:()=>new Promise(r=>resolve=r)};
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
 const context={data:{inventory:{areas:[{id:'bath'}]}},draft:{bath:room},saveError:null,needsReview:false,staleSettings:false,offline:false,language:'en',roomProblems,setup:r=>r.setup,t:k=>k,$:()=>error,el:element,document:{querySelectorAll:()=>[box]},button:(key,action)=>({key,action}),refresh:manual=>{context.refreshed=manual;}};
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
 const node=(tag,text='',className='')=>({tag,text,children:[],className,append(...items){this.children.push(...items);},replaceChildren(){this.children=[];},cloneNode(){const copy=node(this.tag,this.text,this.className);copy.children=this.children.map(c=>c.cloneNode());return copy;},classList:{contains:value=>className.split(' ').includes(value)}});
 const text=n=>[n.text,...n.children.map(text)].join(' ');
 const event=node('div','','event');event.append(node('time','Jan 8 10:00'),node('div','Example light'),node('bdi','Off','state off'));
 const timeline=node('div');timeline.append(node('p','Example retained warning'),event);timeline.querySelectorAll=()=>[event];
 for(const language of ['en','he']){
  const report=node('article'),t=key=>{const value=catalog[language][key]??catalogs[language][key];assert.ok(value,key);return value;};
  renderPrintReport({report,bundle,result:{complete:true},t,lang:()=>language,dayLabel:s=>s.id,node,timeline,logo:node('img')});
  assert.equal(report.children.filter(n=>n.tag==='section').length,3);
  assert.match(text(report),/Asia\/Jerusalem/);assert.match(text(report),/2027/);assert.match(text(report),/Example retained warning/);
  const table=report.children.find(n=>n.tag==='table');assert.equal(table.children[0].tag,'thead');assert.equal(table.children[1].children.length,1);
  assert.match(text(table),/Example light.*Off/);assert.doesNotMatch(text(report),/physical_id|schema_version/);
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
 const before=JSON.stringify(result);renderUnmanaged(root,result,{plan:{snapshot:{timezone:'Asia/Jerusalem'}}},{node,t:k=>k,lang:()=> 'en'});
 const rows=root.querySelectorAll('.event');assert.equal(rows.length,2);assert.equal(rows[0].children[2].className,'state off');assert.match(rows[0].children[1].textContent,/observe_unmanaged/);assert.equal(JSON.stringify(result),before);
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
