import {localeMetadata} from './model.mjs';
export const PERIOD_DRAFT_KEY='shabbat-flow-draft-v2';
export function parsePeriodDraft(raw){
  if(!raw)throw new Error('no_draft');
  let value;try{value=JSON.parse(raw);}catch{throw new Error('bad_draft');}
  if(!value||Array.isArray(value)||Object.keys(value).sort().join(',')!=='config,plan'||
     value.config?.schema_version!==2||value.plan?.schema_version!==2||
     !localeMetadata[value.plan.language])throw new Error('bad_draft');
  return value; // Full validation uses the same server compiler before replacement.
}
export function availableProfiles(config,room,purpose){
  return Object.entries(config.profiles).filter(([,p])=>p.room===room&&p.purpose===purpose);
}
export function nextId(prefix,items){
  let i=1;const used=new Set(items.map(v=>v.id));while(used.has(`${prefix}_${i}`))i++;
  return `${prefix}_${i}`;
}
