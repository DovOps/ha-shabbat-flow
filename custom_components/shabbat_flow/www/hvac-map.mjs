import {itemIcon} from './ha-icons.mjs';
const HALF_HOUR=30*60*1000;
export function hvacMap(bundle,result){
 if(!result?.complete)return null;
 const snapshot=bundle.plan.snapshot,start=Date.parse(snapshot.segments[0].candle_lighting),end=Date.parse(snapshot.end);
 const lanes=[],seen=new Set();
 for(const [id,load] of Object.entries(bundle.config.loads).sort(([a],[b])=>a.localeCompare(b))){
  if(!['hvac','hvac_power'].includes(load.kind)||seen.has(load.physical_id))continue;
  const events=result.events.filter(e=>e.physical_id===load.physical_id&&['hvac','hvac_power'].includes(e.action.type)&&e.intent!=='track_only'&&Date.parse(e.local)<end).sort((a,b)=>Date.parse(a.local)-Date.parse(b.local));
  if(!events.length)continue;
  seen.add(load.physical_id);
  const intervals=[];let state='unknown',cursor=start;
  for(const event of events){const at=Date.parse(event.local),next=(event.action.type==='hvac_power'?event.action.state:event.action.mode)==='off'?'off':'on';
   if(at<=start){state=next;continue;}
   if(at>cursor)intervals.push({start:cursor,end:at,state});cursor=at;state=next;
  }
  if(cursor<end)intervals.push({start:cursor,end,state});
  const cells=[];
  for(let a=start;a<end;a+=HALF_HOUR){const b=Math.min(a+HALF_HOUR,end);cells.push({start:a,end:b,parts:intervals.filter(v=>v.start<b&&v.end>a).map(v=>({start:Math.max(a,v.start),end:Math.min(b,v.end),state:v.state}))});}
  lanes.push({id,load,intervals,cells});
 }
 return {start,end,lanes};
}

export function renderHvacMap({bundle,result,node,t,lang}){
 const map=hvacMap(bundle,result),root=node('section',undefined,'hvac-map');
 if(!map)return root;
 root.append(node('h2',t('hvac_map_title')),node('p',t('hvac_map_help'),'hint'));
 if(!map.lanes.length){root.append(node('p',t('hvac_map_empty')));return root;}
 const zone=bundle.plan.snapshot.timezone;
 const time=ms=>new Intl.DateTimeFormat(lang(),{timeZone:zone,month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZoneName:'shortOffset'}).format(new Date(ms));
 const colors={on:'#087d7b',off:'#e8edef',unknown:'#9aabb3'};
 for(let index=0;index<map.lanes.length;index+=8){
  const card=node('section',undefined,'map-day hvac-period');card.append(node('h3',`${time(map.start)} — ${time(map.end)} · ${zone}`));
  const scroll=node('div',undefined,'map-scroll'),chart=node('div',undefined,'map-chart'),axis=node('div',undefined,'map-axis');axis.append(node('span',t('hvac_map_unit')));
  const ticks=node('div',undefined,'map-ticks');for(let i=0;i<=4;i++)ticks.append(node('span',time(map.start+(map.end-map.start)*i/4)));axis.append(ticks);chart.append(axis);
  for(const lane of map.lanes.slice(index,index+8)){
   const row=node('div',undefined,'map-row'),label=node('div',lane.load.label[lang()],'map-label');label.prepend(itemIcon(lane.load.physical_id,'mdi:thermostat'));
   const room=bundle.config.rooms[lane.load.display?.room];if(room)label.append(node('small',room[lang()]));row.append(label);
   const cells=node('div',undefined,'hvac-cells');cells.setAttribute('role','img');cells.tabIndex=0;
   cells.setAttribute('aria-label',lane.intervals.map(v=>`${t('map_'+v.state)} ${time(v.start)} — ${time(v.end)}`).join('; '));
   for(const cell of lane.cells){
    const square=node('span',undefined,'hvac-cell');square.style.flexGrow=String(cell.end-cell.start);
    const stops=cell.parts.flatMap(v=>[`${colors[v.state]} ${(v.start-cell.start)/(cell.end-cell.start)*100}%`,`${colors[v.state]} ${(v.end-cell.start)/(cell.end-cell.start)*100}%`]);
    square.style.background=`linear-gradient(to right, ${stops.join(',')})`;
    if(cell.parts.every(v=>v.state==='unknown'))square.classList.add('hvac-unknown');
    square.title=cell.parts.map(v=>`${t('map_'+v.state)} ${time(v.start)} — ${time(v.end)}`).join('; ');cells.append(square);
   }
   row.append(cells);chart.append(row);
  }
  scroll.append(chart);card.append(scroll);root.append(card);
 }
 return root;
}
