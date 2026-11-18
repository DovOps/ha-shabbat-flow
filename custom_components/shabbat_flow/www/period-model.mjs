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

export function zonedParts(instant,zone){
  const parts=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date(instant));
  return Object.fromEntries(parts.filter(v=>v.type!=='literal').map(v=>[v.type,v.value]));
}
export function zonedISO(instant,zone){
  const p=zonedParts(instant,zone),ms=+new Date(instant);
  const local=Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute,+p.second);
  const offset=Math.round((local-ms)/60000),sign=offset<0?'-':'+';
  const abs=Math.abs(offset);
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}${sign}${String(Math.floor(abs/60)).padStart(2,'0')}:${String(abs%60).padStart(2,'0')}`;
}
export function resolveWindowTime(value,segment,zone){
  if(value.at)return zonedISO(value.at,zone);
  if(!['candle_lighting','sunrise'].includes(value.anchor))throw new Error('invalid_time');
  return zonedISO(+new Date(segment[value.anchor])+value.offset_minutes*60000,zone);
}
export function dayBounds(plan,segment){
  return {start:plan.snapshot.segments[0].id===segment.id?plan.snapshot.preparation_start:segment.start,end:segment.end};
}
export function dayHomeState(plan,segment){
  const bounds=dayBounds(plan,segment),start=+new Date(bounds.start),end=+new Date(bounds.end);
  let cursor=start;const states=new Set();
  for(const item of plan.availability){
    const a=Math.max(start,+new Date(item.start)),b=Math.min(end,+new Date(item.end));
    if(a>=b)continue;if(a!==cursor)return 'custom';cursor=b;states.add(item.state);
  }
  return cursor===end&&states.size===1?[...states][0]:'custom';
}
export function setDayHome(bundle,segmentId,state){
  const next=structuredClone(bundle),plan=next.plan,segment=plan.snapshot.segments.find(v=>v.id===segmentId);
  const bounds=dayBounds(plan,segment),start=+new Date(bounds.start),end=+new Date(bounds.end),items=[];
  for(const item of plan.availability){
    const a=+new Date(item.start),b=+new Date(item.end);
    if(b<=start||a>=end){items.push({...item});continue;}
    if(a<start)items.push({...item,end:bounds.start});
    if(b>end)items.push({...item,start:bounds.end});
  }
  items.push({id:'replacement',...bounds,state});items.sort((a,b)=>new Date(a.start)-new Date(b.start));
  plan.availability=items.map((v,i)=>({...v,id:`availability_${i+1}`}));return next;
}
export function setRoomChoice(bundle,segmentId,room,purpose,profileId){
  const next=structuredClone(bundle),plan=next.plan,segment=plan.snapshot.segments.find(v=>v.id===segmentId);
  const matches=plan.room_uses.filter(v=>v.segment===segmentId&&v.room===room&&v.purpose===purpose);
  if(matches.length>1)throw new Error('custom_room');
  const existing=matches[0];plan.room_uses=plan.room_uses.filter(v=>!matches.includes(v));
  if(profileId==='off')return next;
  const profile=next.config.profiles[profileId];
  if(profileId!=='existing'&&(!profile||profile.room!==room||profile.purpose!==purpose))throw new Error('invalid_mapping');
  let window=existing?{start:existing.start,end:existing.end}:{start:segment.start,end:segment.end};
  const oldProfile=existing&&next.config.profiles[existing.profile];
  const oldDefault=oldProfile?.window&&Object.fromEntries(['start','end'].map(k=>[k,resolveWindowTime(oldProfile.window[k],segment,plan.snapshot.timezone)]));
  if(profile?.window&&(!existing||(oldDefault&&existing.start===oldDefault.start&&existing.end===oldDefault.end))){
    window=Object.fromEntries(['start','end'].map(k=>[k,resolveWindowTime(profile.window[k],segment,plan.snapshot.timezone)]));
  }
  plan.room_uses.push({id:existing?.id??nextId('use',plan.room_uses),room,purpose,segment:segmentId,
    control:profileId==='existing'?'existing':'planner',profile:profileId==='existing'?null:profileId,...window,...(existing?.hvac_end&&profileId!=='existing'?{hvac_end:existing.hvac_end}:{})});
  return next;
}
function wallDate(iso,zone){const p=zonedParts(iso,zone);return Date.UTC(+p.year,+p.month-1,+p.day);}
export function localDateTimeValue(iso,zone){
  const p=zonedParts(iso,zone);return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}`;
}
export function localDateTimeCandidates(value,zone){
  if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/.test(value))return [];
  const desired=value.length===16?value+':00':value,wall=+new Date(desired+'Z'),matches=[];
  if(!Number.isFinite(wall))return [];
  for(let offset=-14*60;offset<=14*60;offset+=15){
    const candidate=wall-offset*60000;
    if(localDateTimeValue(candidate,zone)===desired)matches.push(zonedISO(candidate,zone));
  }
  return matches.sort((a,b)=>new Date(a)-new Date(b));
}
export function shiftWallDays(iso,days,zone){
  const p=zonedParts(iso,zone),wall=Date.UTC(+p.year,+p.month-1,+p.day+days,+p.hour,+p.minute,+p.second);
  const matches=localDateTimeCandidates(new Date(wall).toISOString().slice(0,19),zone);
  if(matches.length!==1)throw new Error('copy_time');return matches[0];
}
export function copyPreviousDay(bundle,targetId){
  let next=structuredClone(bundle),plan=next.plan,index=plan.snapshot.segments.findIndex(v=>v.id===targetId);
  if(index<=0)throw new Error('invalid_mapping');
  const source=plan.snapshot.segments[index-1],target=plan.snapshot.segments[index],zone=plan.snapshot.timezone;
  const state=dayHomeState(plan,source);if(state==='custom')throw new Error('copy_custom');
  const days=(wallDate(target.start,zone)-wallDate(source.start,zone))/86400000;
  for(const field of ['room_uses','meals',...('naps' in plan?['naps']:[])]){
    const sourceItems=plan[field].filter(v=>v.segment===source.id);
    plan[field]=plan[field].filter(v=>v.segment!==targetId);
    for(const item of sourceItems){
      const copy={...item,id:nextId(field==='meals'?'meal':field==='naps'?'nap':'use',plan[field]),segment:targetId,
        start:shiftWallDays(item.start,days,zone),end:shiftWallDays(item.end,days,zone)};
      if(item.hvac_end)copy.hvac_end=shiftWallDays(item.hvac_end,days,zone);
      if(copy.kind==='afternoon'&&target.kind!=='shabbat')continue;
      if(new Date(copy.start)<new Date(plan.snapshot.preparation_start)||new Date(copy.end)>new Date(plan.snapshot.end))throw new Error('copy_bounds');
      plan[field].push(copy);
    }
  }
  next=setDayHome(next,targetId,state);return next;
}


// Presentation only: never modify the planned action or infer live device state.
export function actionBadge(event){
  const a=event.action,tracked=event.intent==='track_only';
  let key='action_unknown',semantic='neutral';
  if(['state','hvac_power'].includes(a.type)&&['on','off'].includes(a.state)){key=a.state;semantic=a.state;}
  else if(a.type==='hvac'&&['heat','cool','off'].includes(a.mode)){key='mode_'+a.mode;semantic=a.mode;}
  return {key,className:'state '+(tracked?'tracked':semantic),preserve:a.type==='hvac_power',tracked};
}

export function restDefaults(profile){return profile?.rest_defaults??{nap_after_sunrise:480,nap_duration:120,lead_minutes:60,late_wake_after_sunrise:240};}
export function addNap(bundle,segmentId,room){
 const next=structuredClone(bundle),seg=next.plan.snapshot.segments.find(v=>v.id===segmentId),profiles=availableProfiles(next.config,room,'sleeping');
 if(!profiles.length)throw new Error('invalid_mapping');
 const [id,profile]=profiles.find(([,p])=>p.label.en==='Standard')??profiles[0],d=restDefaults(profile),zone=next.plan.snapshot.timezone;
 const start=+new Date(seg.sunrise)+d.nap_after_sunrise*60000,end=start+d.nap_duration*60000;
 const naps=next.plan.naps??=[];naps.push({id:nextId('nap',naps),room,profile:id,segment:segmentId,start:zonedISO(start,zone),end:zonedISO(end,zone),lead_minutes:d.lead_minutes,bathroom_targets:[]});return next;
}
export function napBathroomTargets(config,nap){
 const profile=config.profiles[nap.profile];
 return [...new Set(profile.groups.flatMap(g=>config.groups[g].rules.filter(r=>r.release&&r.action.type==='state'&&r.action.state==='on').flatMap(r=>r.targets)))].filter(id=>config.loads[id].display?.room&&config.loads[id].display.room!==nap.room);
}
export function afternoonActivity(bundle,segmentId){
 const next=structuredClone(bundle),seg=next.plan.snapshot.segments.find(v=>v.id===segmentId);
 if(seg.kind!=='shabbat'||next.plan.meals.some(m=>m.segment===segmentId&&m.kind==='afternoon'))return next;
 const final=seg.id===next.plan.snapshot.segments.at(-1).id,zone=next.plan.snapshot.timezone;
 next.plan.meals.push({id:nextId('afternoon',next.plan.meals),segment:segmentId,kind:'afternoon',choice:'none',start:final?zonedISO(+new Date(seg.end)-150*60000,zone):'',end:final?seg.end:'',groups:[...new Set(next.plan.meals.filter(m=>m.segment===segmentId&&m.kind==='daytime').flatMap(m=>m.groups))]});return next;
}
