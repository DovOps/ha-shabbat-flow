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
  assert.equal(availableProfiles(period.config,'room_b','recreation').length,1);
  assert.equal(availableProfiles(period.config,'missing','sleeping').length,0);
});
test('generated UI selection IDs do not collide after removing a row',()=>{
  assert.equal(nextId('use',[{id:'use_1'},{id:'use_3'}]),'use_2');
});
