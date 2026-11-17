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
