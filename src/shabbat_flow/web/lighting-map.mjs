import {localDateTimeCandidates} from './period-model.mjs';

// An event-free interval is unknown until a scheduled state command establishes intent.
export function lightingMap(bundle,result){
 if(!result?.complete)return [];
 const snapshot=bundle.plan.snapshot,zone=snapshot.timezone,start=Date.parse(snapshot.preparation_start),end=Date.parse(snapshot.end);
 const localDate=ms=>new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(ms));
 const days=[];let day=localDate(start);
 for(let guard=0;guard<6;guard++){
  const next=new Date(Date.parse(day+'T12:00:00Z')+86400000).toISOString().slice(0,10);
  const a=Date.parse(localDateTimeCandidates(day+'T00:00',zone)[0]),b=Date.parse(localDateTimeCandidates(next+'T00:00',zone)[0]);
  if(!Number.isFinite(a)||!Number.isFinite(b))throw new Error('invalid_local_clock');
  if(a>=end)break;
  const lanes=[];
  for(const [id,load] of Object.entries(bundle.config.loads)){
   if(load.kind!=='binary')continue;
   const events=result.events.filter(e=>e.physical_id===load.physical_id&&e.action.type==='state'&&e.intent!=='track_only').sort((x,y)=>Date.parse(x.local)-Date.parse(y.local));
   if(!events.length)continue;
   const left=Math.max(a,start),right=Math.min(b,end),intervals=[];let cursor=left,state='unknown';
   for(const e of events){const at=Date.parse(e.local);if(at<=left){state=e.action.state;continue;}if(at>=right)break;intervals.push({start:cursor,end:at,state});cursor=at;state=e.action.state;}
   if(cursor<right)intervals.push({start:cursor,end:right,state});
   lanes.push({id,load,intervals});
  }
  lanes.sort((x,y)=>(x.load.display?.area_type??'legacy').localeCompare(y.load.display?.area_type??'legacy')||(x.load.display?.room??'').localeCompare(y.load.display?.room??'')||x.id.localeCompare(y.id));
  days.push({date:day,start:a,end:b,lanes});day=next;
 }
 return days;
}

export function renderLightingMap({bundle,result,node,t,lang}){
 const root=node('section',undefined,'lighting-map');root.append(node('h2',t('map_title')),node('p',t('map_help'),'hint'));
 const zone=bundle.plan.snapshot.timezone;
 const time=ms=>new Intl.DateTimeFormat(lang(),{timeZone:zone,hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZoneName:'shortOffset'}).format(new Date(ms));
 for(const day of lightingMap(bundle,result)){
  // Small chunks keep each PDF chart readable without an oversized unbreakable block.
  for(let offset=0;offset<Math.max(day.lanes.length,1);offset+=8){
   const card=node('section',undefined,'map-day');card.append(node('h3',`${day.date} · ${zone} · ${(day.end-day.start)/3600000} ${t('map_hours')}`));
   const scroll=node('div',undefined,'map-scroll'),chart=node('div',undefined,'map-chart'),axis=node('div',undefined,'map-axis');
   axis.append(node('span',t('map_load')));const ticks=node('div',undefined,'map-ticks');
   for(let i=0;i<=4;i++){const tick=node('span',time(day.start+(day.end-day.start)*i/4));ticks.append(tick);}axis.append(ticks);chart.append(axis);
   let previous=null;
   for(const lane of day.lanes.slice(offset,offset+8)){
    const display=lane.load.display,group=`${t('map_type_'+(display?.area_type??'legacy'))} · ${bundle.config.rooms[display?.room]?.[lang()]??t('map_unassigned')}`;
    if(group!==previous){chart.append(node('h4',group));previous=group;}
    const row=node('div',undefined,'map-row'),label=node('div',lane.load.label[lang()],'map-label');if(display)label.append(node('small',t('map_role_'+display.role)));row.append(label);
    const track=node('div',undefined,'map-track');track.setAttribute('role','img');
    const summary=lane.intervals.map(v=>`${t('map_'+v.state)} ${time(v.start)} — ${time(v.end)}`).join('; ');track.setAttribute('aria-label',summary);track.title=summary;
    // CSS grid positions are set through CSSOM, not inserted HTML or provider content.
    for(const interval of lane.intervals){const bar=node('span',undefined,'map-bar map-'+interval.state);bar.style.left=((interval.start-day.start)/(day.end-day.start)*100)+'%';bar.style.width=((interval.end-interval.start)/(day.end-day.start)*100)+'%';bar.title=`${t('map_'+interval.state)} ${time(interval.start)} — ${time(interval.end)}`;track.append(bar);}
    row.append(track);chart.append(row);
   }
   scroll.append(chart);card.append(scroll);root.append(card);
  }
 }
 return root;
}
