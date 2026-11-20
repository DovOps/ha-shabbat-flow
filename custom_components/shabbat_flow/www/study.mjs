import {request as fetch} from './transport.mjs';
import {setupObservation} from './observe.mjs';
import {renderObservationPrint} from './thermal-report.mjs';
const $=id=>document.getElementById(id),node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
let language='en',catalogs,sources,printData;
const selection={hours:24,zones:[],note:''};
const t=k=>catalogs[language][k]??k,lang=()=>language;
function print(){if(printData)renderObservationPrint({report:$('print-report'),data:printData,node,t,lang,logo:document.querySelector('.brand-logo')});}
function draw(){
 document.documentElement.lang=language;document.documentElement.dir=language==='he'?'rtl':'ltr';
 $('title').textContent=t('study_title');$('intro').textContent=t('study_intro');$('home').textContent=t('house_setup');
 const root=$('study-setup');root.replaceChildren();
 const field=(text,input)=>{const label=node('label',undefined,'study-field');label.append(node('span',text),input);root.append(label);};
 const hours=node('input');hours.type='number';hours.min='1';hours.max='48';hours.step='1';hours.value=selection.hours;hours.oninput=()=>selection.hours=Number(hours.value);field(t('study_hours'),hours);
 const note=node('textarea');note.maxLength=2000;note.rows=2;note.value=selection.note;note.oninput=()=>selection.note=note.value;field(t('study_note'),note);
 root.append(node('p',t('study_select_hint'),'hint'));
 for(const zone of sources.climates){
  const card=node('section',undefined,'card');const label=node('label'),box=node('input');box.type='checkbox';box.checked=selection.zones.some(z=>z.entity_id===zone.entity_id);label.append(box,node('span',`${zone.area_name??''} · ${zone.name} · ${zone.entity_id}`));card.append(label);
  box.onchange=()=>{selection.zones=selection.zones.filter(z=>z.entity_id!==zone.entity_id);if(box.checked)selection.zones.push({entity_id:zone.entity_id,lights:[],reference:null});draw();};
  const selected=selection.zones.find(z=>z.entity_id===zone.entity_id);
  if(selected){
   const refLabel=node('label',undefined,'study-field'),ref=node('select');refLabel.append(node('span',t('study_reference')),ref);const empty=node('option',t('study_none'));empty.value='';ref.append(empty);
   for(const source of sources.references){const option=node('option',`${source.area_name??''} · ${source.name} · ${source.entity_id}`);option.value=source.entity_id;ref.append(option);}ref.value=selected.reference??'';ref.onchange=()=>selected.reference=ref.value||null;card.append(refLabel);
   const lighting=node('fieldset');lighting.append(node('legend',t('study_lights')));
   const addLight=e=>{const label=node('label',undefined,'toggle'),input=node('input');input.type='checkbox';input.checked=selected.lights.includes(e.entity_id);input.onchange=()=>{selected.lights=selected.lights.filter(id=>id!==e.entity_id);if(input.checked)selected.lights.push(e.entity_id);};label.append(input,node('span',`${e.name} · ${e.entity_id}`));return label;};
   const same=sources.lights.filter(e=>zone.area_id&&e.area_id===zone.area_id);
   for(const e of same)lighting.append(addLight(e));
   const more=node('details');more.append(node('summary',t('study_other_lights')));for(const e of sources.lights.filter(e=>!same.includes(e)))more.append(addLight(e));lighting.append(more);card.append(lighting);
  }root.append(card);
 }
 if(!sources.climates.length)root.append(node('p',t('observe_thermal_empty')));
 setupObservation({root:$('observe-panel'),fetch,node,t,lang,study:()=>structuredClone(selection),onPrint:data=>{printData=data;print();window.print();}});
}
window.addEventListener('beforeprint',print);
async function init(){try{const [c,s]=await Promise.all([fetch('/api/v2/i18n'),fetch('/api/v2/observe')]);if(!c.ok||!s.ok)throw Error();catalogs=await c.json();const listing=await s.json();sources=listing.study_sources;draw();$('language').onchange=()=>{language=$('language').value;draw();};}catch{$('error').textContent='Unable to load climate studies. Open this page inside Home Assistant. / לא ניתן לטעון מחקרי אקלים. יש לפתוח מתוך Home Assistant.';}}
init();
