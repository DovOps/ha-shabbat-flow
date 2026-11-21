import {renderFlexibleSummary,words as flexWords} from './flexible.mjs';
// Reported point samples, not continuous room temperature or compressor runtime.
export function thermalModel(data){
 const run=data?.run,thermal=run?.thermal;
 if(!thermal)return null;
 const frames=thermal.samples??[],number=v=>typeof v==='number'&&Number.isFinite(v)?v:null;
 const lanes=thermal.climates.slice(0,100).map(target=>({target,points:frames.map(frame=>{
  const sample=frame.status==='sampled'?frame.climates?.[target.entity_id]:null;
  return {at:Date.parse(frame.due),sampledAt:frame.sampled_at,power:sample?.power??(sample?.mode==='off'?'off':['heat','cool','auto','heat_cool','dry','fan_only'].includes(sample?.mode)?'on':'unknown'),mode:sample?.mode??'unknown',activity:sample?.hvac_action??'unknown',
   reference:number(frame.status==='sampled'?frame.references?.[target.entity_id]?.current_temperature?.celsius:null),current:number(sample?.current_temperature?.celsius),target:number(sample?.target_temperature?.celsius),
   low:number(sample?.target_low?.celsius),high:number(sample?.target_high?.celsius),outdoor:number(frame.status==='sampled'?frame.outdoor?.current_temperature?.celsius:null)};
 })}));
 for(const lane of lanes){
  const totals=thermal.activity?.totals?.[lane.target.entity_id];lane.onMinutes=totals?totals.on_seconds/60:null;lane.offMinutes=totals?totals.off_seconds/60:null;lane.unknownMinutes=totals?totals.unknown_seconds/60:null;
  const on=totals?.seen_on||totals?.on_seconds>0||lane.points.some(p=>p.power==='on'),off=totals?.off_seconds>0||lane.points.some(p=>p.power==='off');
  lane.group=on?'active':off?'inactive':'unknown';
 }
 const rank={active:0,inactive:1,unknown:2};lanes.sort((a,b)=>rank[a.group]-rank[b.group]||(b.onMinutes??-1)-(a.onMinutes??-1)||(a.target.area_name??'').localeCompare(b.target.area_name??'')||a.target.entity_id.localeCompare(b.target.entity_id));
 for(const lane of lanes)lane.bands=thermalBands(run,lane.target);
 const values=lanes.flatMap(l=>l.points.flatMap(p=>[p.current,p.target,p.low,p.high,p.outdoor,p.reference].filter(v=>v!==null)));
 const low=values.length?Math.floor(Math.min(...values))-1:0,high=values.length?Math.ceil(Math.max(...values))+1:30;
 return {start:Date.parse(run.start),end:Date.parse(run.end),zone:run.bundle.plan.snapshot.timezone,low,high,lanes,source:thermal.outdoor?.entity_id??null};
}
export function thermalBands(run,target){
 const config=run.bundle?.config??{},plan=run.bundle?.plan??{},loads=Object.values(config.loads??{}),start=Date.parse(run.start),end=Date.parse(run.end);
 const hvac=loads.find(l=>run.mapping?.[l.physical_id]?.entity_id===target.entity_id),room=hvac?.display?.room??target.planner_room_id;
 if(!room&&run.kind!=='climate_study')return [];
 const clip=(a,b)=>({start:Math.max(start,Date.parse(a)),end:Math.min(end,Date.parse(b))});
 const bands=[];const windows=[];
 for(const u of plan.room_uses??[])if(u.room===room)windows.push({...clip(u.start,u.end),state:'use',purpose:u.purpose});
 for(const n of plan.naps??[])if(n.room===room)windows.push({...clip(n.start,n.end),state:'use',purpose:'nap'});
 for(const m of plan.meals??[])if(['family','hosting'].includes(m.choice)&&(m.groups??[]).some(g=>(config.groups?.[g]?.rules??[]).some(r=>(r.targets??[]).some(id=>config.loads?.[id]?.display?.room===room))))windows.push({...clip(m.start,m.end),state:'use',purpose:'meal'});
 for(const purpose of [...new Set(windows.map(w=>w.purpose))])bands.push({kind:'use',purpose,intervals:windows.filter(w=>w.purpose===purpose&&w.end>w.start)});
 const intervals=(changes,observed)=>{
  const points=changes.filter(e=>Number.isFinite(e.at)).sort((a,b)=>a.at-b.at),last=Date.parse(run.last_sample??run.start);
  const gaps=observed?(run.gaps??[]).map(g=>clip(g.start,g.end)):[];
  const cuts=[...new Set([start,end,...points.map(e=>e.at),...(observed?[last]:[]),...gaps.flatMap(g=>[g.start,g.end])])].filter(v=>v>=start&&v<=end).sort((a,b)=>a-b);
  return cuts.slice(0,-1).map((a,i)=>{const b=cuts[i+1];let state='unknown';for(const p of points){if(p.at>a)break;state=p.state;}
   if(observed&&(a>=last||run.truncated||gaps.some(g=>g.start<b&&g.end>a)))state='unknown';
   return {start:a,end:b,state:['on','off'].includes(state)?state:'unknown'};});
 };
 const seen=new Set();for(const l of loads){if(l.kind!=='binary'||(run.kind==='climate_study'?!target.study_lights?.includes(run.mapping?.[l.physical_id]?.entity_id):l.display?.room!==room)||!['main_lights','night_lights','study_lighting'].includes(l.display?.role)||seen.has(l.physical_id))continue;seen.add(l.physical_id);
  const base={label:l.label,entity:run.mapping?.[l.physical_id]?.entity_id??l.physical_id,role:l.display.role,signalKind:l.display.signal_kind??(run.mapping?.[l.physical_id]?.entity_id?.startsWith('switch.')?'switch':'light')};
  const planned=(run.preview?.events??[]).filter(e=>e.physical_id===l.physical_id&&e.intent!=='track_only'&&e.action?.type==='state').map(e=>({at:Date.parse(e.utc??e.local),state:e.action.state}));
  if(run.kind!=='climate_study')bands.push({...base,kind:'planned',intervals:intervals(planned,false)});
  const observed=(run.changes??[]).filter(e=>e.physical_id===l.physical_id).map(e=>({at:Date.parse(e.observed_at),state:e.state}));
  bands.push({...base,kind:'observed',intervals:intervals(observed,true)});
 }
 return bands;
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
 root.append(node('p',`${t('observe_weather_source')}: ${model.source??t('observe_weather_missing')} · °C · ${model.zone}`));
 const time=at=>new Intl.DateTimeFormat(lang(),{timeZone:model.zone,month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZoneName:'shortOffset'}).format(new Date(at));
 const series=[['current','#0075ba',''],['target','#8d3891','7 4'],['low','#8d3891','2 4'],['high','#aa4d70','9 3 2 3'],['outdoor','#b26000','3 3'],['reference','#306d27','10 3']];
 const modeColors={cool:'#0075ba',heat:'#bb4820',off:'#687581',unknown:'#bec6cb',auto:'#72539b',heat_cool:'#72539b',fan_only:'#16796f',dry:'#9b791a'};
 const activity=value=>t('observe_activity_'+(['off','heating','cooling','drying','idle','fan','defrosting','preheating'].includes(value)?value:'unknown'));
 const mode=value=>t('observe_mode_'+(Object.hasOwn(modeColors,value)?value:'unknown'));
 const svg=(name,attrs={},text)=>{const el=document.createElementNS('http://www.w3.org/2000/svg',name);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,String(v));if(text!==undefined)el.textContent=text;return el;};
 let priorGroup=null;
 for(const lane of model.lanes){
  if(lane.group!==priorGroup){root.append(node('h3',t('observe_zones_'+lane.group)));priorGroup=lane.group;}
  const card=node('section',undefined,'thermal-card');card.append(node('h3',`${lane.target.area_name??''} · ${lane.target.entity_id}`));
  card.append(node('p',zoneMinutes(lane,t),'hint'));
  if(data.run.kind==='climate_study'){
   const pairs=lane.points.filter(p=>p.current!==null&&p.reference!==null),mean=pairs.length?pairs.reduce((sum,p)=>sum+p.current-p.reference,0)/pairs.length:null;
   card.append(node('p',`${t('study_reference')}: ${lane.target.reference?.entity_id??t('study_none')}`),node('p',`${t('study_delta')}: ${mean===null?'—':mean.toFixed(1)+' °C'} · ${t('study_pairs')}: ${pairs.length}`),node('p',t('study_calibration_hint'),'hint'));
  }
  const chart=svg('svg',{viewBox:`0 0 800 ${260+lane.bands.length*30}`,role:'img','aria-label':`${lane.target.entity_id} · ${t('observe_thermal_chart_hint')}`,direction:'ltr'});
  chart.append(svg('title',{},`${lane.target.entity_id} · ${time(model.start)} — ${time(model.end)}`));
  const x=at=>54+(at-model.start)/(model.end-model.start)*724,y=v=>190-(v-model.low)/(model.high-model.low)*166;
  for(let i=0;i<=4;i++){const val=model.low+(model.high-model.low)*i/4,at=model.start+(model.end-model.start)*i/4;
   chart.append(svg('line',{x1:54,x2:778,y1:y(val),y2:y(val),stroke:'#d4dfe4'}),svg('text',{x:46,y:y(val)+4,'text-anchor':'end','font-size':12},val.toFixed(1)),svg('text',{x:x(at),y:248+lane.bands.length*30,'text-anchor':i===0?'start':i===4?'end':'middle','font-size':10},time(at)));
  }
  const legend=node('p',undefined,'thermal-legend');
  for(const [key,color,dash] of series){const paths=lineSegments(lane.points,key);if(!paths.length)continue;
   legend.append(node('span',t('observe_series_'+key)));
   legend.lastChild.style.color=color;
   for(const path of paths){chart.append(svg('polyline',{points:path.map(p=>`${x(p.at)},${y(p.value)}`).join(' '),fill:'none',stroke:color,'stroke-width':2,'stroke-dasharray':dash}));for(const p of path)chart.append(svg('circle',{cx:x(p.at),cy:y(p.value),r:2.5,fill:color}));}
  }
  chart.append(svg('text',{x:4,y:218,'font-size':10},t('observe_mode')));
  for(const p of lane.points){const dot=svg('circle',{cx:x(p.at),cy:214,r:4,fill:modeColors[p.mode]??modeColors.unknown});dot.append(svg('title',{},`${time(p.at)} · ${mode(p.mode)} · ${activity(p.activity)}`));chart.append(dot);}
  const bandDescriptions=[];
  lane.bands.forEach((band,index)=>{
   const top=235+index*30,description=band.kind==='use'?t('observe_band_use')+' · '+t('observe_use_'+(['sleeping','recreation','nap','meal'].includes(band.purpose)?band.purpose:'other')):t(data.run.kind==='climate_study'&&band.kind==='observed'?(band.signalKind==='switch'?'study_observed_switch':'study_observed_light'):'observe_band_'+band.kind)+(band.role==='study_lighting'?'':' · '+t('map_role_'+band.role))+' · '+(band.label?.[lang()]??band.entity);
   bandDescriptions.push(description+' · '+band.intervals.map(v=>`${v.state==='use'?t('observe_band_use'):t('observe_power_'+v.state)} ${time(v.start)} — ${time(v.end)}`).join('; '));
   chart.append(svg('text',{x:54,y:top,'font-size':10},description));
   chart.append(svg('rect',{x:54,y:top+4,width:724,height:9,fill:'#f0f3f5'}));
   for(const interval of band.intervals){const rect=svg('rect',{x:x(interval.start),y:top+4,width:Math.max(0,x(interval.end)-x(interval.start)),height:9,fill:interval.state==='use'?'#72539b':interval.state==='on'?(band.kind==='planned'?'#0075ba':'#087d7b'):interval.state==='off'?'#d1d9df':'#f1e7ce',stroke:interval.state==='unknown'?'#b18a44':'none','stroke-dasharray':'2 2'});rect.append(svg('title',{},`${description} · ${interval.state==='use'?t('observe_band_use'):t('observe_power_'+interval.state)} · ${time(interval.start)} — ${time(interval.end)}`));chart.append(rect);}
  });
  chart.setAttribute('aria-label',`${lane.target.entity_id} · ${t('observe_thermal_chart_hint')} · ${bandDescriptions.join(' · ')}`);
  card.append(legend,chart,node('p',t(data.run.kind==='climate_study'?'study_band_hint':'observe_band_hint'),'hint'));
  if(!lane.bands.length)card.append(node('p',t('observe_band_missing'),'hint'));
  const modes=node('p',undefined,'thermal-legend');for(const value of [...new Set(lane.points.map(p=>Object.hasOwn(modeColors,p.mode)?p.mode:'unknown'))]){const label=node('span',`● ${mode(value)}`);label.style.color=modeColors[value];modes.append(label);}card.append(node('p',t('observe_mode_legend'),'hint'),modes);
  const detail=node('details',undefined,'thermal-data'),table=node('table'),head=node('tr');detail.append(node('summary',t('observe_thermal_data')));
  for(const key of ['observe_time','observe_series_current','observe_series_target','observe_series_outdoor','observe_series_reference','observe_mode','observe_activity'])head.append(node('th',t(key)));table.append(head);
  const fmt=v=>v===null?'—':v.toFixed(1);
  for(const p of lane.points){const row=node('tr');for(const value of [time(p.at),fmt(p.current),p.target!==null?fmt(p.target):`${fmt(p.low)}–${fmt(p.high)}`,fmt(p.outdoor),fmt(p.reference),mode(p.mode),activity(p.activity)])row.append(node('td',value));table.append(row);}detail.append(table);card.append(detail);root.append(card);
 }
 root.append(renderCombinedThermalTable(model,{node,t,lang}));
 if(!model.lanes.length)root.append(node('p',t('observe_thermal_empty')));
 return root;
}
function zoneMinutes(lane,t){
 const value=v=>v===null?t('observe_duration_missing'):v.toFixed(1);
 return `${t('observe_on_minutes')}: ${value(lane.onMinutes)} · ${t('observe_off_minutes')}: ${value(lane.offMinutes)} · ${t('observe_unknown')}: ${value(lane.unknownMinutes)}`;
}
export function renderCombinedThermalTable(model,{node,t,lang}){
 const root=node('section',undefined,'thermal-combined');root.append(node('h2',t('observe_combined_title')),node('p',t('observe_zone_ranking_hint'),'hint'));
 const scroll=node('div',undefined,'thermal-combined-scroll'),table=node('table'),thead=node('thead'),head=node('tr');
 for(const key of ['observe_zone','observe_time','observe_power','observe_mode','observe_activity','observe_reading','observe_target','observe_outdoor','observe_series_reference'])head.append(node('th',t(key)));thead.append(head);table.append(thead);
 const time=at=>new Intl.DateTimeFormat(lang(),{timeZone:model.zone,month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZoneName:'shortOffset'}).format(new Date(at));
 const fmt=v=>v===null?'—':v.toFixed(1);let priorGroup=null;
 for(const lane of model.lanes){
  if(priorGroup!==lane.group){const body=node('tbody'),row=node('tr',undefined,'thermal-group'),cell=node('th',t('observe_zones_'+lane.group));cell.colSpan=9;row.append(cell);body.append(row);table.append(body);priorGroup=lane.group;}
  const body=node('tbody');const title=node('tr',undefined,'thermal-zone-heading'),cell=node('th',`${lane.target.area_name??''} · ${lane.target.entity_id} · ${zoneMinutes(lane,t)}`);cell.colSpan=9;title.append(cell);body.append(title);
  for(const p of lane.points){const row=node('tr');const mode=['cool','heat','off','auto','heat_cool','fan_only','dry'].includes(p.mode)?p.mode:'unknown',activity=['off','heating','cooling','drying','idle','fan','defrosting','preheating'].includes(p.activity)?p.activity:'unknown';
   for(const value of [lane.target.area_name||lane.target.entity_id,time(p.at),t('observe_power_'+p.power),t('observe_mode_'+mode),t('observe_activity_'+activity),fmt(p.current),p.target!==null?fmt(p.target):`${fmt(p.low)}–${fmt(p.high)}`,fmt(p.outdoor),fmt(p.reference)])row.append(node('td',value));body.append(row);
  }table.append(body);
 }
 scroll.append(table);root.append(scroll);return root;
}
export function renderObservationTotals(data,{node,t,lang=()=> 'en'}){
 const root=node('section');root.append(node('h2',t(data.run.kind==='climate_study'?'study_context':'observe_report_totals')));
 root.append(node('p',t(data.run.kind==='climate_study'?'study_report_hint':'observe_sample_notice')));
 if(data.run.kind==='climate_study'){root.append(node('p',data.run.bundle.study.note),node('p',`${t('study_finished')}: ${data.run.finished_at?new Intl.DateTimeFormat(lang(),{timeZone:data.run.bundle.plan.snapshot.timezone,dateStyle:'medium',timeStyle:'short'}).format(new Date(data.run.finished_at)):t('observe_status_observing')}`));return root;}
 const table=node('table'),head=node('tr');for(const key of ['report_device','observe_match','observe_mismatch','observe_unknown','observe_unplanned'])head.append(node('th',t(key)));table.append(head);
 for(const [id,totals] of Object.entries(data.run.summary??{})){const row=node('tr');row.append(node('td',data.run.mapping?.[id]?.entity_id??id));for(const key of ['matched','mismatched','unknown','unplanned'])row.append(node('td',((totals[key+'_seconds']??0)/60).toFixed(1)));table.append(row);}root.append(table);
 const thermal=data.run.thermal;if(thermal)root.append(node('p',`${t('observe_thermal_samples')}: ${thermal.samples.filter(s=>s.status==='sampled').length} / ${thermal.samples.length}`));
 if(data.collection_error)root.append(node('p',t('observe_error'),'error'));
 return root;
}
function renderComfort(data,{node,lang}){
 const root=node('section'),he=lang()==='he';
 if(!data.run.comfort)return root;
 root.append(node('h2',he?'החלטות מיזוג במעקב בלבד':'HVAC shadow decisions'),node('p',he?'אין שליטה במכשירים. טריות מדידת החיישן לא אומתה; אין אישור להפעלה.':'No device control. Sensor measurement freshness is unverified; these decisions are not activation clearance.','hint'));
 const table=node('table'),head=node('tr');for(const label of he?['שעה','חדר / יחידה','טמפרטורה','כוונה','סיבה']:['Time','Room / unit','Temperature','Intent','Reason'])head.append(node('th',label));table.append(head);
 const reasonLabels={external_release:he?'סיום בשליטה חיצונית':'Release left to existing control',threshold:he?'סף טמפרטורה':'Temperature threshold',minimum_dwell:he?'משך מזערי':'Minimum dwell',outside_window:he?'מחוץ לחלון':'Outside window',missing_evidence:he?'חסר מידע':'Missing evidence',activity_gate_off:he?'סימני פעילות כבויים':'Activity signals off',planner_signal_dependency:he?'תלות בסימן בשליטת המתכנן':'Planner-controlled signal',clock_rollback:he?'שעון נסוג':'Clock rollback'};
 for(const d of data.run.comfort.decisions??[]){const c=data.run.preview.flex.conditions.find(c=>c.id===d.id),load=data.run.bundle.config.loads[c?.load],row=node('tr');for(const v of [new Date(d.at).toLocaleString(he?'he-IL':'en-GB',{timeZone:data.run.bundle.plan.snapshot.timezone}),load?.label[lang()]??d.source,d.temperature===null?'—':d.temperature+' °'+d.unit,he?({on:'הפעלה',off:'כיבוי',unknown:'לא ידוע'}[d.intent]):d.intent,reasonLabels[d.reason]??d.reason])row.append(node('td',String(v)));table.append(row);}root.append(table);return root;
}
export function renderObservationPrint({report,data,node,t,lang,logo}){
 report.replaceChildren();if(logo){const img=logo.cloneNode(true);img.className='brand-logo';report.append(img);}
 const zone=data.run.bundle?.plan?.snapshot?.timezone??'UTC';const time=value=>new Intl.DateTimeFormat(lang(),{timeZone:zone,dateStyle:'medium',timeStyle:'short'}).format(new Date(value));
 report.append(node('h1',t(data.run.kind==='climate_study'?'study_report_title':'observe_report_title')),node('p',`${time(data.run.start)} — ${time(data.run.end)} · ${zone}`),node('p',`${t(data.run.kind==='climate_study'?'study_id':'observe_run_id')}: ${data.run.id} · ${data.run.snapshot_hash}`),node('p',t(data.run.kind==='climate_study'?'study_collect_hint':'observe_hint'),'report-notice'),renderObservationTotals(data,{node,t,lang}),renderThermalReport(data,{node,t,lang}),renderComfort(data,{node,lang}));
 if(data.run.preview?.flex)report.append(renderFlexibleSummary({bundle:data.run.bundle,result:data.run.preview,node,lang}));
}
