import {request} from './transport.mjs';
export const planStatusWords={
 en:{title:'Plans and studies',actions:'Plan actions',run_menu:'Test, observe or arm',review_arm:'Review arming',draft:'Draft — not activated',ready:'Preview ready — not activated',draft_help:'This workspace is an editable draft. Saved observations and armed plans keep their own frozen snapshot; edits here do not update them.',control:'Scheduled control',observation:'Plan observation',climate:'Climate study',none:'Nothing active or pending.',loading:'Checking saved status…',stale:'Status could not be refreshed. Previous information may be out of date.',refresh:'Refresh status',manage:'Review control and disarm',report:'View report',included:'Selected devices',excluded:'Excluded devices',next:'Next pending action',attention:'Needs attention',latest:'Latest',approved:'Approved — NOT armed',armed:'Armed',running:'Running',completed:'Completed',disarmed:'Disarmed',blocked:'Blocked',scheduled:'Scheduled — observation only',observing:'Observing — no device control',stopped:'Stopped',interrupted:'Interrupted',failed:'Failed'},
 he:{title:'תוכניות ומחקרים',actions:'פעולות בתוכנית',run_menu:'בדיקה, מעקב או הפעלה',review_arm:'בדיקה לקראת הפעלה',draft:'טיוטה — לא הופעלה',ready:'התצוגה מוכנה — לא הופעלה',draft_help:'סביבת עבודה זו היא טיוטה ניתנת לעריכה. מעקבים שמורים ותוכניות דרוכות שומרים עותק קפוא משלהם; עריכה כאן אינה מעדכנת אותם.',control:'שליטה מתוזמנת',observation:'מעקב תוכנית',climate:'מחקר אקלים',none:'אין פעילות או תכנון ממתינים.',loading:'בודק מצב שמור…',stale:'לא ניתן לרענן את המצב. המידע הקודם עשוי להיות לא עדכני.',refresh:'רענון מצב',manage:'בדיקת שליטה וביטול דריכה',report:'הצגת דוח',included:'מכשירים שנבחרו',excluded:'מכשירים שהוחרגו',next:'הפעולה הממתינה הבאה',attention:'נדרשת תשומת לב',latest:'אחרון',approved:'אושר — לא נדרך',armed:'דרוך',running:'פועל',completed:'הושלם',disarmed:'בוטל',blocked:'חסום',scheduled:'מתוזמן — מעקב בלבד',observing:'במעקב — ללא שליטה במכשירים',stopped:'נעצר',interrupted:'נקטע',failed:'נכשל'}
};
export function commandBarOpen(saved,mobile){return saved==='open'?true:saved==='closed'?false:!mobile;}
export function operationalSummary(data){
 const control=data?.execution?.runs??[],observations=data?.runs??[];
 const groups={control,observation:observations.filter(r=>(r.kind??'plan')==='plan'),climate:observations.filter(r=>r.kind==='climate_study')};
 return Object.fromEntries(Object.entries(groups).map(([kind,runs])=>[kind,{
  active:runs.filter(r=>['approved','armed','running','blocked','scheduled','observing'].includes(r.status)).sort((a,b)=>new Date(a.start)-new Date(b.start)),
  latest:runs.filter(r=>!['approved','armed','running','blocked','scheduled','observing'].includes(r.status)).sort((a,b)=>new Date(b.end)-new Date(a.end))[0]??null
 }]));
}
const node=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
export function setupPlanStatus({root,lang}){
 let data=null,failed=false,busy=false,last=0,disposed=false;
 const t=k=>planStatusWords[lang()][k]??k;
 const date=(v,zone)=>new Intl.DateTimeFormat(lang(),{timeZone:zone,dateStyle:'medium',timeStyle:'short'}).format(new Date(v));
 const heading=node('h2'),refresh=node('button'),message=node('p'),cards=node('div',undefined,'operational-cards');
 refresh.type='button';message.setAttribute('role','status');root.replaceChildren(heading,refresh,message,cards);root.hidden=false;
 function render(){
  heading.textContent=t('title');refresh.textContent=t('refresh');refresh.disabled=busy;
  message.textContent=failed||data?.error||data?.execution?.error?t('stale'):!data?t('loading'):'';message.className=failed?'error':'hint';
  if(!data)return;
  const signature=JSON.stringify([lang(),data]);if(cards.dataset.signature===signature)return;cards.dataset.signature=signature;cards.replaceChildren();
  for(const [kind,group]of Object.entries(operationalSummary(data))){
   const card=node('section',undefined,'activity-tile');card.append(node('h3',t(kind)));
   const sourceError=kind==='control'?data.execution?.error||!data.execution:data.error;
   if(sourceError)card.append(node('p',t('stale'),'error'));
   else if(!group.active.length)card.append(node('p',t('none')));
   const runs=group.active.length?group.active:group.latest?[group.latest]:[];
   for(const r of runs){
    card.append(node('strong',(!group.active.length?t('latest')+': ':'')+t(r.status)),node('p',date(r.start,r.timezone)+' — '+date(r.end,r.timezone)));
    if(kind==='control'){
     card.append(node('p',`${t('included')}: ${r.included?.length??0} · ${t('excluded')}: ${r.excluded?.length??0}`));
     if(r.blocked&&Object.keys(r.blocked).length)card.append(node('p',t('attention')+': '+Object.keys(r.blocked).length,'error'));
     if(r.next_event)card.append(node('p',t('next')+': '+date(r.next_event.utc,r.timezone)+' · '+r.next_event.entity_id+' · '+r.next_event.state));
     const link=node('a',t('manage'));link.href='#execution-panel';card.append(link);
    }
    if(r.observer_id||kind!=='control'){const link=node('a',t('report'));link.href='./observation.html?run='+encodeURIComponent(r.observer_id??r.id);card.append(link);}
   }
   cards.append(card);
  }
 }
 async function update(force=false){
  if(disposed||busy||(!force&&Date.now()-last<5000))return;busy=true;last=Date.now();render();
  try{const response=await request('/api/v2/observe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:'status'})});if(!response.ok)throw Error();const next=await response.json();if(next.error||!Array.isArray(next.runs))throw Error();data=next;failed=false;}catch{failed=true;}finally{busy=false;if(!disposed)render();}
 }
 refresh.onclick=()=>update(true);const focus=()=>{if(!document.hidden)update();};window.addEventListener('focus',focus);
 const timer=setInterval(()=>{if(!document.hidden)update();},30000);render();update(true);
 return {render,refresh:()=>update(true),dispose:()=>{disposed=true;clearInterval(timer);window.removeEventListener('focus',focus);}};
}
