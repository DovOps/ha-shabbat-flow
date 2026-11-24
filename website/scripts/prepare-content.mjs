import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const site=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),repo=path.resolve(site,'..');
const list=async(dir)=>{const out=[];for(const e of await fs.readdir(dir,{withFileTypes:true})){const p=path.join(dir,e.name);if(e.isDirectory())out.push(...await list(p));else if(e.name.endsWith('.md'))out.push(p);}return out.sort();};
const adoption=JSON.parse(await fs.readFile(path.join(repo,'src/shabbat_flow/web/adoption-guide.json'),'utf8'));
const specs=await list(path.join(repo,'specs'));
const maintained=['requirements-status.md','roadmap.md','dependencies.md','setup-tips.md','dry-run-to-live.md'].map(n=>path.join(repo,'docs',n));
const version=JSON.parse(await fs.readFile(path.join(repo,'custom_components/shabbat_flow/manifest.json'),'utf8')).version;
await fs.mkdir(path.join(site,'generated'),{recursive:true});await fs.writeFile(path.join(site,'generated/version.json'),JSON.stringify({version}));
await fs.mkdir(path.join(site,'static/img'),{recursive:true});await fs.copyFile(path.join(repo,'assets/logo.png'),path.join(site,'static/img/logo.png'));
for(const lang of ['en','he']){
 const dest=path.join(site,lang==='en'?'generated/docs':'i18n/he/docusaurus-plugin-content-docs/current');
 await fs.mkdir(path.dirname(dest),{recursive:true});
 if(lang==='he')await fs.writeFile(path.join(path.dirname(dest),'current.json'),JSON.stringify({'sidebar.docs.category.Technical reference · English':{message:'מקור טכני · אנגלית'}}));
 await fs.rm(dest,{recursive:true,force:true});await fs.mkdir(dest,{recursive:true});
 for(const f of await list(path.join(site,'content',lang)))await fs.copyFile(f,path.join(dest,path.basename(f)));
 const guide=adoption[lang];
 const guideBody=`# ${guide.title}\n\n${guide.intro}\n\n> ${guide.scope}\n\n`+guide.sections.map(s=>`## ${s.title} {#${s.id}}\n\n${s.body.join('\n\n')}\n\n**${guide.gate}:** ${s.gate}\n`).join('\n');
 await fs.writeFile(path.join(dest,'adoption.md'),guideBody);
 for(const source of [...specs,...maintained]){
  const rel=path.relative(repo,source).split(path.sep).join('/'),target=path.join(dest,'reference',rel);
  let body=await fs.readFile(source,'utf8');
  // Canonical source links stay valid even for files outside the publication allowlist.
  body=body.replace(/\]\(([^\s)]+)([^)]*)\)/g,(full,href,tail)=>{
   if(/^(?:[a-z]+:|#|\/)/i.test(href))return full;
   const [file,anchor]=href.split('#');const resolved=path.relative(repo,path.resolve(path.dirname(source),file)).split(path.sep).join('/');
   return `](https://github.com/DovOps/ha-shabbat-flow/blob/main/${resolved}${anchor?'#'+anchor:''}${tail})`;
  });
  const note=lang==='he'?'מקור טכני באנגלית, מסונכרן אוטומטית מהמאגר.':'Canonical technical source, synchronized from the repository at build time.';
  await fs.mkdir(path.dirname(target),{recursive:true});
  let category=path.dirname(target);
  while(category!==dest){await fs.writeFile(path.join(category,'_category_.json'),JSON.stringify({key:path.relative(dest,category),label:path.basename(category)}));category=path.dirname(category);}
  await fs.writeFile(target,`> ${note} [GitHub](https://github.com/DovOps/ha-shabbat-flow/blob/main/${rel})\n\n${body}`);
 }
 const heading=lang==='he'?'מפרטים ודרישות':'Specifications & requirements';
 const intro=lang==='he'?'המפרטים הטכניים נשמרים באנגלית כמקור מוסמך יחיד. כל בנייה של האתר מעתיקה את הגרסה העדכנית מהמאגר. תוכנית עתידית אינה יכולת שכבר הופעלה.':'The repository is the source of truth. These pages are generated from the current specs on every build. A specified future feature is not necessarily implemented or enabled.';
 const indexes=specs.filter(f=>path.basename(f)==='spec.md');
 let text=`# ${heading}\n\n${intro}\n\n`;
 for(const f of indexes){const rel=path.relative(repo,f).split(path.sep).join('/');const title=(await fs.readFile(f,'utf8')).match(/^# (.+)$/m)?.[1]??rel;text+=`- [${title}](reference/${rel})\n`;}
 text+='\n'+(lang==='he'?'[מצב הדרישות והיישום]':'[Requirements and implementation status]')+'(reference/docs/requirements-status.md)\n';
 await fs.writeFile(path.join(dest,'specifications.md'),text);
}
console.log(`Prepared ${specs.length} canonical specification files, ${maintained.length} maintained references and two guide locales; integration ${version}.`);
