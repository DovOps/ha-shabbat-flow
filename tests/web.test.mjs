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
    for(const [,key] of js.matchAll(/(?:t|message|field|button|section)\('([^']+)'(?=[,)])/g))assert.ok(merged[key],key);
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
