// Label filters only guide explicit selection; they never assign schedule targets.
export const labelRoles=['bathroom','main_lights','night_lights','bedroom','common_area'];
export const emptyLabelFilters=()=>Object.fromEntries(labelRoles.map(role=>[role,null]));
export const entityMatchesLabel=(entity,id)=>!id||[...(entity.labels??[]),...(entity.device_labels??[])].includes(id);
export function roleCandidates(inventory,room,area,role,filters,{allRoom=false,allAreas=false}={}){
 const selected=room.roles[role];
 const label=role==='hvac'?null:role==='main_lights'&&room.setup?.service?(filters.bathroom??filters.main_lights):filters[role];
 return inventory.entities.filter(e=>(role==='hvac'?e.domain==='climate':['light','switch'].includes(e.domain))&&
  (selected.includes(e.id)||((allAreas||e.area_id===area)&&(allRoom||entityMatchesLabel(e,label)))));
}
export function bathroomCandidates(inventory,area,linked,filters,all=false){
 const eligible=new Set(inventory.entities.filter(e=>['light','switch'].includes(e.domain)&&entityMatchesLabel(e,filters.bathroom)).map(e=>e.area_id));
 return inventory.areas.filter(a=>a.id!==area&&!linked.includes(a.id)&&(all||!filters.bathroom||eligible.has(a.id)));
}
export function suggestedPurposes(area,filters){
 return [['bedroom','sleeping'],['common_area','recreation']].filter(([role])=>filters[role]&&(area.labels??[]).includes(filters[role])).map(([,purpose])=>purpose);
}
export function filteredAreas(areas,rooms,filters,kind){
 if(kind==='all')return areas;
 return areas.filter(a=>rooms[a.id]?.enabled||(filters[kind]&&(a.labels??[]).includes(filters[kind])));
}
