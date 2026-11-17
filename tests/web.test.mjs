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
  const context={data:structuredClone(initial),next:structuredClone(initial),draft:{room_a:{enabled:false}},dirty:false,saving:false,needsReview:false,offline:false,structuredClone,
    api:async()=>structuredClone(context.next),render:()=>{context.renders++;},renderRooms:()=>{context.renders++;},updateAvailability:()=>{},syncLabel:()=>{},status:value=>{context.message=value;},renders:0};
  runInNewContext(refresh,context);
  const boundRoom=context.draft.room_a;
  await context.refresh();
  assert.equal(context.draft.room_a,boundRoom);
  boundRoom.enabled=true;context.dirty=true;
  context.next.inventory.revision='b';await context.refresh();
  assert.equal(context.draft.room_a,boundRoom);assert.equal(context.needsReview,true);
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
