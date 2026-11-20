// Reported point samples, not continuous room temperature or compressor runtime.
export function thermalModel(data){
 const run=data?.run,thermal=run?.thermal;
 if(!thermal)return null;
 const frames=thermal.samples??[],number=v=>typeof v==='number'&&Number.isFinite(v)?v:null;
 const lanes=thermal.climates.slice(0,100).map(target=>({target,points:frames.map(frame=>{
  const sample=frame.status==='sampled'?frame.climates?.[target.entity_id]:null;
  return {at:Date.parse(frame.due),sampledAt:frame.sampled_at,mode:sample?.mode??'unknown',activity:sample?.hvac_action??'unknown',
   current:number(sample?.current_temperature?.celsius),target:number(sample?.target_temperature?.celsius),
   low:number(sample?.target_low?.celsius),high:number(sample?.target_high?.celsius),outdoor:number(frame.status==='sampled'?frame.outdoor?.current_temperature?.celsius:null)};
 })}));
 const values=lanes.flatMap(l=>l.points.flatMap(p=>[p.current,p.target,p.low,p.high,p.outdoor].filter(v=>v!==null)));
 const low=values.length?Math.floor(Math.min(...values))-1:0,high=values.length?Math.ceil(Math.max(...values))+1:30;
 return {start:Date.parse(run.start),end:Date.parse(run.end),zone:run.bundle.plan.snapshot.timezone,low,high,lanes,source:thermal.outdoor?.entity_id??null};
}
export function lineSegments(points,key){
 const paths=[];let current=[];
 for(const p of points){if(p[key]===null){if(current.length)paths.push(current);current=[];}else current.push({at:p.at,value:p[key]});}
 if(current.length)paths.push(current);return paths;
}
export function renderThermalReport(data,{node,t,lang}){
 const root=node('section',undefined,'thermal-report'),model=thermalModel(data);
 root.append(node('h2',t('observe_thermal_title')),node('p',t('observe_thermal_chart_hint'),'hint'));
 if(!model){root.append(node('p',t('observe_thermal_legacy')));return root;}
 root.append(node('p',`${t('observe_weather')}: ${model.source??t('observe_weather_missing')} · °C · ${model.zone}`));
 const time=at=>new Intl.DateTimeFormat(lang(),{timeZone:model.zone,month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZoneName:'shortOffset'}).format(new Date(at));
 const series=[['current','#0075ba',''],['target','#8d3891','7 4'],['low','#8d3891','2 4'],['high','#aa4d70','9 3 2 3'],['outdoor','#b26000','3 3']];
 const modeColors={cool:'#0075ba',heat:'#bb4820',off:'#687581',unknown:'#bec6cb',auto:'#72539b',heat_cool:'#72539b',fan_only:'#16796f',dry:'#9b791a'};
 const activity=value=>t('observe_activity_'+(['off','heating','cooling','drying','idle','fan','defrosting','preheating'].includes(value)?value:'unknown'));
 const mode=value=>t('observe_mode_'+(Object.hasOwn(modeColors,value)?value:'unknown'));
 const svg=(name,attrs={},text)=>{const el=document.createElementNS('http://www.w3.org/2000/svg',name);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,String(v));if(text!==undefined)el.textContent=text;return el;};
 for(const lane of model.lanes){
  const card=node('section',undefined,'thermal-card');card.append(node('h3',`${lane.target.area_name??''} · ${lane.target.entity_id}`));
  const chart=svg('svg',{viewBox:'0 0 800 260',role:'img','aria-label':`${lane.target.entity_id} · ${t('observe_thermal_chart_hint')}`,direction:'ltr'});
  chart.append(svg('title',{},`${lane.target.entity_id} · ${time(model.start)} — ${time(model.end)}`));
  const x=at=>54+(at-model.start)/(model.end-model.start)*724,y=v=>190-(v-model.low)/(model.high-model.low)*166;
  for(let i=0;i<=4;i++){const val=model.low+(model.high-model.low)*i/4,at=model.start+(model.end-model.start)*i/4;
   chart.append(svg('line',{x1:54,x2:778,y1:y(val),y2:y(val),stroke:'#d4dfe4'}),svg('text',{x:46,y:y(val)+4,'text-anchor':'end','font-size':12},val.toFixed(1)),svg('text',{x:x(at),y:248,'text-anchor':i===0?'start':i===4?'end':'middle','font-size':10},time(at)));
  }
  const legend=node('p',undefined,'thermal-legend');
  for(const [key,color,dash] of series){const paths=lineSegments(lane.points,key);if(!paths.length)continue;
   legend.append(node('span',t('observe_series_'+key)));
   legend.lastChild.style.color=color;
   for(const path of paths){chart.append(svg('polyline',{points:path.map(p=>`${x(p.at)},${y(p.value)}`).join(' '),fill:'none',stroke:color,'stroke-width':2,'stroke-dasharray':dash}));for(const p of path)chart.append(svg('circle',{cx:x(p.at),cy:y(p.value),r:2.5,fill:color}));}
  }
  chart.append(svg('text',{x:4,y:218,'font-size':10},t('observe_mode')));
  for(const p of lane.points){const dot=svg('circle',{cx:x(p.at),cy:214,r:4,fill:modeColors[p.mode]??modeColors.unknown});dot.append(svg('title',{},`${time(p.at)} · ${mode(p.mode)} · ${activity(p.activity)}`));chart.append(dot);}
  card.append(legend,chart);
  const modes=node('p',undefined,'thermal-legend');for(const value of [...new Set(lane.points.map(p=>Object.hasOwn(modeColors,p.mode)?p.mode:'unknown'))]){const label=node('span',`● ${mode(value)}`);label.style.color=modeColors[value];modes.append(label);}card.append(node('p',t('observe_mode_legend'),'hint'),modes);
  const detail=node('details',undefined,'thermal-data'),table=node('table'),head=node('tr');detail.append(node('summary',t('observe_thermal_data')));
  for(const key of ['observe_time','observe_series_current','observe_series_target','observe_series_outdoor','observe_mode','observe_activity'])head.append(node('th',t(key)));table.append(head);
  const fmt=v=>v===null?'—':v.toFixed(1);
  for(const p of lane.points){const row=node('tr');for(const value of [time(p.at),fmt(p.current),p.target!==null?fmt(p.target):`${fmt(p.low)}–${fmt(p.high)}`,fmt(p.outdoor),mode(p.mode),activity(p.activity)])row.append(node('td',value));table.append(row);}detail.append(table);card.append(detail);root.append(card);
 }
 if(!model.lanes.length)root.append(node('p',t('observe_thermal_empty')));
 return root;
}
export function renderObservationPrint({report,data,node,t,lang,logo}){
 report.replaceChildren();if(logo){const img=logo.cloneNode(true);img.className='brand-logo';report.append(img);}
 report.append(node('h1',t('observe_title')),node('p',`${data.run.start} — ${data.run.end}`),node('p',`${t('observe_run_id')}: ${data.run.id} · ${data.run.snapshot_hash}`),node('p',t('observe_hint'),'report-notice'),renderThermalReport(data,{node,t,lang}));
}
