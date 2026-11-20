import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const site=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),build=path.join(site,'build'),repo=path.resolve(site,'..'),base='/ha-shabbat-flow/';
async function files(dir){const all=[];for(const e of await fs.readdir(dir,{withFileTypes:true})){const p=path.join(dir,e.name);if(e.isDirectory())all.push(...await files(p));else all.push(p);}return all;}
const output=await files(build),exists=new Set(output),html=output.filter(f=>f.endsWith('.html'));
const version=JSON.parse(await fs.readFile(path.join(repo,'custom_components/shabbat_flow/manifest.json'),'utf8')).version;
for(const locale of ['','he/']){
 const home=await fs.readFile(path.join(build,locale,'index.html'),'utf8');assert.ok(home.replace(/<!--.*?-->/g,'').includes('v'+version));assert.ok(home.includes(locale?'dir="rtl"':'dir="ltr"'));
 for(const page of ['room-options','start','capabilities','specifications','contributing'])assert.ok(exists.has(path.join(build,locale,'docs',page,'index.html')),`Missing ${locale}${page}`);
 for(const f of (await files(path.join(repo,'specs'))).filter(f=>f.endsWith('.md'))){const rel=path.relative(repo,f).replace(/\.md$/,'');assert.ok(exists.has(path.join(build,locale,'docs/reference',rel,'index.html')),`Missing canonical reference ${locale}${rel}`);}
}
let links=0;
for(const file of html){
 const body=await fs.readFile(file,'utf8');
 for(const match of body.matchAll(/(?:href|src)="([^"#]+)(?:#[^"]*)?"/g)){
  const href=match[1];if(!href.startsWith('/')||href.startsWith('//'))continue;
  assert.ok(href.startsWith(base),`Root-relative URL escapes project base: ${href}`);
  const rel=decodeURIComponent(href.slice(base.length).split(/[?#]/)[0]);const target=path.join(build,rel);
  assert.ok(exists.has(target)||exists.has(target.replace(/\/$/,'')+'.html')||exists.has(path.join(target,'index.html')),`Missing ${href} in ${path.relative(build,file)}`);links++;
 }
}
assert.ok(!output.some(f=>/\.(?:db|sqlite|pem|key)$/.test(f)));
console.log(`Checked ${html.length} pages, ${links} project-relative links/assets, canonical spec coverage, both locales and version ${version}.`);
