import {request} from './transport.mjs';
import {setupSMS} from './notifications.mjs';
const $=id=>document.getElementById(id),node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
let catalogs,language='en',data;
const t=k=>catalogs[language][k]??k;
async function api(body){const r=await request('/api/v2/observe',{method:'POST',body:JSON.stringify(body)});if(!r.ok)throw Error();return r.json();}
function draw(){
 document.documentElement.lang=language;document.documentElement.dir=language==='he'?'rtl':'ltr';
 for(const [id,key] of Object.entries({home:'house_setup',study:'study_title',settings:'settings_title',title:'settings_title',intro:'settings_intro',refresh:'sms_refresh','sms-title':'sms_title','jump-sms':'sms_title'}))$(id).textContent=t(key);
 const root=$('dependencies');root.replaceChildren();
 for(const d of data.dependencies){const card=node('section',undefined,'card');card.append(node('h2',t('dep_'+d.id)),node('p',t('dep_'+d.requirement)),node('strong',(d.ready?'✓ ':d.detected?'⚠ ':'○ ')+t('dep_'+d.status),d.ready?'':'error'),node('p',t('dep_hint_'+d.hint)));root.append(card);}
 setupSMS({root:$('sms'),api,node,t});
}
async function refresh(){try{data=await api({op:'dependencies'});$('error').textContent='';draw();}catch{$('error').textContent=catalogs?t('sms_error'):'Open Settings inside Home Assistant. / יש לפתוח הגדרות מתוך Home Assistant.';}}
$('refresh').onclick=refresh;$('language').onchange=()=>{language=$('language').value;if(data)draw();};
async function init(){try{const r=await request('/api/v2/i18n');if(!r.ok)throw Error();catalogs=await r.json();await refresh();}catch{$('error').textContent='Open Settings inside Home Assistant. / יש לפתוח הגדרות מתוך Home Assistant.';}}init();
