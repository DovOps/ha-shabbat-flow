import {reviewWords} from './review-ui.mjs';
import {haIcon} from './ha-icons.mjs';
import {renderThermalReport} from './thermal-report.mjs';
import {localTime} from './model.mjs';
export function groupExistingEvents(events){
 const groups=new Map();for(const event of events){const key=JSON.stringify([event.source,event.utc,event.action]);if(!groups.has(key))groups.set(key,{...event,devices:[]});const group=groups.get(key);if(!group.devices.some(e=>e.entity_id===event.entity_id))group.devices.push(event);}return [...groups.values()];
}
export function renderUnmanaged(root,result,bundle,{node,t,lang,icon=haIcon}){
  if(!result.unmanaged)return;
  const info=result.unmanaged,overlay=info.overlay??{},events=overlay.events??[],unresolved=overlay.unresolved??[];
  const excluded=overlay.excluded?.length??0;
  const issues=unresolved.length+(info.unmapped?.length??0)+(info.ownership?.conflicts?.length??0)+(info.error?1:0);
  if(events.length){root.append(node('h3',t('observe_unmanaged')),node('p',t('observe_forecast_hint'),'hint'));}
  if(issues||excluded){
    root.append(node('p',`${t('observe_forecast_summary')} ${t('observe_review_count')}: ${issues}. ${t('observe_excluded_count')}: ${excluded}.`,'hint forecast-note'));
    const details=node('details',undefined,'forecast-diagnostics');details.append(node('summary',t('observe_diagnostics')));
    if(info.error)details.append(node('p',t('observe_unresolved'),'hint'));
    for(const id of info.unmapped??[])details.append(node('p',`${t('observe_unmapped')} · ${id}`,'hint'));
    for(const item of unresolved)details.append(node('p',`${item.source_name??item.source} · ${t('observe_reason_'+item.reason)}`,'hint'));
    for(const c of info.ownership?.conflicts??[])details.append(node('p',`${t('observe_conflict_hint')} · ${c.source} · ${c.physical_id}`,'hint'));
    if(excluded)details.append(node('p',t('observe_excluded_help'),'hint'));
    root.append(details);
  }
  for(const event of groupExistingEvents(events)){
    const row=node('div',undefined,'event');row.dataset.utc=event.utc;
    const time=node('time',localTime(event.local,lang(),bundle.plan.snapshot.timezone));time.dateTime=event.utc;
    const description=node('div');description.append(node('strong','↻ '+(event.source_name??event.source)),node('small',t('observe_unmanaged'),'existing-automation-label'));
    for(const device of event.devices){const line=node('div',undefined,'existing-device');line.append(icon(device.entity_icon,device.entity_id.startsWith('climate.')?'mdi:thermostat':'mdi:lightbulb-outline'),node('span',device.entity_name??device.entity_id));description.append(line);}
    const ids=node('details',undefined,'forecast-identifiers');ids.append(node('summary',t('observe_identifiers')),node('small',event.source+' · '+event.devices.map(d=>d.entity_id).join(', ')));description.append(ids);
    row.append(time,description,node('bdi',t(event.action.state),event.action.state==='on'?'state on':'state off'));root.append(row);
  }
  const rows=[...root.querySelectorAll('.event')];
  rows.sort((a,b)=>Date.parse(a.querySelector('time').dateTime)-Date.parse(b.querySelector('time').dateTime));
  for(const row of rows)root.append(row);
}

export function setupObservation({root,fetch,node,t,getBundle,isReady,onPrint,lang,study=null,uiState={}}){
  root.hidden=false;root.replaceChildren();root.append(node('h2',t(study?'study_runs_title':'observe_title')),node('p',t(study?'study_collect_hint':'observe_hint')));
  const words=reviewWords[lang()],archive=node('a','▤ '+words.review_link,'command-link');archive.href='./reports.html';root.append(archive);const startBox=node('div',undefined,'observation-start');root.append(startBox);let container=startBox;
  const errorText=e=>{try{return t('error_'+e.message);}catch{return t('observe_error')+' · '+e.message;}};
  const status=node('p');status.setAttribute('role','status');const select=node('select');select.setAttribute('aria-label',t('observe_runs'));
  const field=(key,value,type='number')=>{const label=node('label');label.append(node('span',t(key)));const input=node('input');input.type=type;if(type==='checkbox')input.checked=value;else input.value=value;label.append(input);container.append(label);return input;};
  const weather=node('select');weather.setAttribute('aria-label',t('observe_weather'));const weatherLabel=node('label');weatherLabel.append(node('span',t('observe_weather')),weather);container.append(weatherLabel,node('p',t(study?'study_thermal_hint':'observe_thermal_hint'),'hint'));
  const enabled=study?{checked:false}:field('observe_checks',true,'checkbox'),boot=study?{}:field('observe_boot',5),interval=study?{}:field('observe_interval',30);
  boot.min='1';boot.max='60';interval.min='5';interval.max='1440';
  const api=async body=>{const r=await fetch('/api/v2/observe',body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const data=await r.json();if(!r.ok)throw Error(data.error);return data;};
  const refresh=async()=>{const old=select.value||uiState.run||'';const data=await api();const priorWeather=weather.value||uiState.weather||'';weather.replaceChildren();const automatic=node('option',t('observe_weather_auto'));automatic.value='';weather.append(automatic);for(const source of data.weather_sources??[]){const option=node('option',`${source.name} · ${source.entity_id}`);option.value=source.entity_id;weather.append(option);}weather.value=priorWeather;if((data.weather_sources??[]).length>1&&!weather.value)status.textContent=t('observe_weather_choose');select.replaceChildren();for(const run of [...data.runs].filter(r=>study?r.kind==='climate_study':r.kind!=='climate_study').reverse()){const opt=node('option',`${new Intl.DateTimeFormat(document.documentElement.lang,{timeZone:run.timezone,dateStyle:'medium',timeStyle:'short'}).format(new Date(run.start))} · ${t('observe_status_'+run.status)} · ${run.id.slice(0,8)}`);opt.value=run.id;select.append(opt);}if([...select.options].some(o=>o.value===old))select.value=old;if(data.error)throw Error(data.error);};
  const summary=node('div');
  let key=null,keyBundle=null;
  const action=(label,fn)=>{const b=node('button',t(label));b.type='button';b.onclick=async()=>{b.disabled=true;try{await fn();status.textContent=t('observe_done');status.className='';}catch(e){status.textContent=errorText(e);status.className='error';}finally{b.disabled=false;}};container.append(b);};
  if(study)action('study_start',async()=>{const selection={...study(),weather_entity_id:weather.value||null};const identity=JSON.stringify(selection);if(keyBundle!==identity){key=crypto.randomUUID();keyBundle=identity;}const run=await api({op:'study_start',selection,request_id:key});await refresh();select.value=run.id;});
  else action('observe_start',async()=>{if(!isReady())throw Error(t('observe_preview_first'));const bundle=getBundle();const options={enabled:enabled.checked,boot_delay_minutes:Number(boot.value),interval_minutes:Number(interval.value)};const identity=JSON.stringify({bundle,options,weather:weather.value});if(keyBundle!==identity){key=crypto.randomUUID();keyBundle=identity;}const run=await api({op:'start',bundle,policy:options,request_id:key,weather_entity_id:weather.value||null});await refresh();select.value=run.id;});
  weather.onchange=()=>uiState.weather=weather.value;select.onchange=()=>uiState.run=select.value;
  const manage=node('details',undefined,'observation-manage');manage.append(node('summary',words.manage));root.append(manage);container=manage;container.append(select);action('observe_refresh',refresh);
  if(!study)action('observe_configure',async()=>{if(!select.value)return;await api({op:'configure',id:select.value,policy:{enabled:enabled.checked,boot_delay_minutes:Number(boot.value),interval_minutes:Number(interval.value)}});});
  action('observe_summary',async()=>{if(!select.value)return;const data=await api({op:'export',id:select.value});summary.replaceChildren();summary.append(node('p',t(study?'study_report_hint':'observe_sample_notice')));if(data.collection_error)summary.append(node('p',t('observe_error'),'error'));const table=node('table'),head=node('tr');for(const k of ['report_device','observe_match','observe_mismatch','observe_unknown','observe_unplanned'])head.append(node('th',t(k)));table.append(head);for(const [id,totals] of Object.entries(data.run.summary)){const row=node('tr');row.append(node('td',data.run.mapping[id].entity_id));for(const k of ['matched','mismatched','unknown','unplanned'])row.append(node('td',(totals[k+'_seconds']/60).toFixed(1)));table.append(row);}if(!study)summary.append(table);if(study)summary.append(node('p',data.run.bundle.study.note),node('p',`${t('study_finished')}: ${data.run.finished_at?new Intl.DateTimeFormat(lang(),{timeZone:data.run.bundle.plan.snapshot.timezone,dateStyle:'medium',timeStyle:'short'}).format(new Date(data.run.finished_at)):t('observe_status_observing')}`));const thermal=data.run.thermal;if(thermal){summary.append(node('h3',t('observe_thermal_title')),node('p',`${t('observe_thermal_samples')}: ${thermal.samples.filter(s=>s.status==='sampled').length} / ${thermal.samples.length} · ${t('observe_weather')}: ${thermal.outdoor?.entity_id??t('observe_weather_missing')}`),node('p',t(study?'study_thermal_hint':'observe_thermal_hint'),'hint'));if(thermal.climates_truncated)summary.append(node('p',t('observe_thermal_truncated'),'error'));}else summary.append(node('p',t('observe_thermal_legacy')));summary.append(renderThermalReport(data,{node,t,lang}));});
  action('observe_print',async()=>{if(!select.value)return;const data=await api({op:'export',id:select.value});onPrint(data);});
  action('observe_stop',async()=>{if(!select.value)return;await api({op:'stop',id:select.value});key=null;keyBundle=null;await refresh();});
  action(study?'study_export':'observe_export',async()=>{if(!select.value)return;const data=await api({op:'export',id:select.value});const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=node('a');a.href=url;a.download='shabbat-flow-observation-'+select.value.slice(0,8)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  const settingsLink=node('a',t('settings_title'));settingsLink.href='./settings.html';root.append(settingsLink);
  root.append(status);manage.append(summary);refresh().catch(e=>{status.textContent=errorText(e);});
}
