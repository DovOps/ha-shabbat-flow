// Label filters only guide explicit selection; they never assign schedule targets.
export const labelRoles=['bathroom','main_lights','night_lights','bedroom','common_area','bathroom_area','hallway_area'];
export const emptyLabelFilters=()=>Object.fromEntries(labelRoles.map(role=>[role,null]));
export const entityMatchesLabel=(entity,id)=>!id||[...(entity.labels??[]),...(entity.device_labels??[])].includes(id);
export function roleCandidates(inventory,room,area,role,filters,{allRoom=false,allAreas=false}={}){
 const selected=room.roles[role];
 const label=role==='hvac'?null:role==='main_lights'&&isBathroom(room)?(filters.bathroom??filters.main_lights):filters[role];
 return inventory.entities.filter(e=>(role==='hvac'?e.domain==='climate':['light','switch'].includes(e.domain))&&
  (selected.includes(e.id)||((allAreas||e.area_id===area)&&(allRoom||entityMatchesLabel(e,label)))));
}
export function bathroomCandidates(inventory,area,linked,filters,all=false){
 const eligible=new Set(inventory.entities.filter(e=>['light','switch'].includes(e.domain)&&entityMatchesLabel(e,filters.bathroom)).map(e=>e.area_id));
 return inventory.areas.filter(a=>a.id!==area&&!linked.includes(a.id)&&(all||!filters.bathroom||eligible.has(a.id)));
}
export function suggestedPurposes(area,filters){
 return [['bedroom','sleeping']].filter(([role])=>filters[role]&&(area.labels??[]).includes(filters[role])).map(([,purpose])=>purpose);
}
export function filteredAreas(areas,rooms,filters,kind){
 if(kind==='all')return areas;
 return areas.filter(a=>rooms[a.id]?.enabled||(filters[kind]&&(a.labels??[]).includes(filters[kind])));
}

export function phases(r){return r.setup?.phases??{night:r.purposes.includes('recreation')&&r.roles.night_lights.length?'after_use':'none',night_start:360,night_end:-60,morning:false,morning_start:120,evening_main:false,evening_meal:false,daytime_meal:false};}
export function roomProblems(r,rooms){
 const s=r.setup??{service:!r.purposes.length};const draft=rooms,errors=[];
  const phase=phases(r);
  if((phase.night!=='none'&&!r.roles.night_lights.length)||((phase.morning||phase.evening_main)&&!r.roles.main_lights.length))errors.push('phase_needs_lights');
  if(phase.night==='after_use'&&!r.purposes.includes('recreation')&&!phase.evening_meal)errors.push('phase_needs_recreation');
  if((phase.night!=='none'||phase.morning)&&s.lighting?.night_enabled)errors.push('phase_bathroom_conflict');
  if(!r.roles.main_lights.length&&!r.roles.night_lights.length&&!(r.roles.hvac.length&&r.hvac.mode!=='none')&&!r.shared_areas.length)errors.push('needs_roles');
  if(r.hvac.mode!=='none'&&!r.roles.hvac.length)errors.push('needs_hvac_device');
  if(r.hvac.mode!=='none'&&!r.purposes.length&&!phases(r).evening_meal&&!phases(r).daytime_meal)errors.push('needs_hvac_use');
  if(s.lighting?.night_enabled&&(!r.roles.main_lights.length||!r.roles.night_lights.length))errors.push('bathroom_night_needs_lights');
  if(r.hvac.mode==='profile')errors.push('hvac_profile_required');
  if(!r.purposes.length&&!s.service)errors.push('needs_purpose');
  if(isBathroom(r)&&!r.roles.main_lights.length&&!r.roles.night_lights.length)errors.push('needs_roles');
  if(r.shared_areas.some(a=>!draft[a]?.enabled||draft[a].setup?.status!=='ready'))errors.push('missing_shared');
 return [...new Set(errors)];
}

export const areaType=r=>r.setup?.area_type??(r.setup?.service?'legacy':'room');
export const isBathroom=r=>['bathroom','legacy'].includes(areaType(r));
export function classifyRoom(room,kind){
 const result=structuredClone(room),s=result.setup;
 s.area_type=kind;s.service=kind!=='room';if(!s.service)s.home=false;
 if(['common','room','hallway'].includes(kind)&&s.lighting?.night_enabled){
  const p=phases(result);
  if(p.night==='none'&&!p.morning)s.phases={...p,night:'home',night_start:s.lighting.night_after_candles,night_end:s.lighting.morning_after_sunrise,morning:true,morning_start:s.lighting.morning_after_sunrise,evening_main:true};
  s.lighting.night_enabled=false;
 }
 return result;
}

export function suggestedAreaTypes(area,filters){
 return [['bedroom','room'],['common_area','common'],['bathroom_area','bathroom'],['hallway_area','hallway']].filter(([role])=>filters[role]&&(area.labels??[]).includes(filters[role])).map(([,kind])=>kind);
}
