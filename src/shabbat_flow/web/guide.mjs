const $=id=>document.getElementById(id);
const node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
let language=new URLSearchParams(location.search).get('lang')==='he'?'he':'en';
try{
 const response=await fetch('./adoption-guide.json');if(!response.ok)throw Error();const content=await response.json();
 function draw(){
  const c=content[language];document.documentElement.lang=language;document.documentElement.dir=language==='he'?'rtl':'ltr';document.title='Shabbat Flow · '+c.nav;$('language').value=language;
  for(const key of ['title','intro','scope','contents','print','home'])$(key).textContent=c[key];
  $('home').textContent=language==='he'?'חזרה ל־Shabbat Flow':'Back to Shabbat Flow';for(const id of ['home','brand-home'])$(id).href=location.pathname.includes('/shabbat_flow_static/')?'/shabbat-flow':'./household.html';
  $('toc').replaceChildren();$('sections').replaceChildren();
  for(const s of c.sections){const item=node('li',''),a=node('a',s.title.replace(/^\d+\. /,''));a.href='#'+s.id;item.append(a);$('toc').append(item);const section=node('section','');section.id=s.id;section.className='card guide-section';section.append(node('h2',s.title));for(const text of s.body)section.append(node('p',text));const gate=node('p','');gate.className='guide-gate';gate.append(node('strong',c.gate+': '),document.createTextNode(s.gate));section.append(gate);$('sections').append(section);}
 }
 $('language').onchange=()=>{language=$('language').value;const url=new URL(location.href);url.searchParams.set('lang',language);history.replaceState(null,'',url);draw();};$('print').onclick=()=>window.print();draw();
 if(location.hash)document.getElementById(location.hash.slice(1))?.scrollIntoView();
}catch{$('error').textContent='The guide could not load. Refresh to retry. / לא ניתן לטעון את המדריך. רעננו ונסו שוב.';}
