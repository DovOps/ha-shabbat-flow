export function setupSMS({root,api,node,t}){
 const status=node('p');status.setAttribute('role','status');
 const show=async()=>{try{
  const data=await api({op:'sms_get'}),cfg=structuredClone(data.settings),cap=data.capability;
  root.replaceChildren();root.append(node('p',t(cap.available?'sms_available':'sms_unavailable')),node('p',t('sms_hint'),'hint'));
  root.append(node('p',t(cap.push_available?'sms_push_available':'sms_push_unavailable')));
  if(!cap.report_url_available)root.append(node('p',t('sms_no_url'),'hint'));
  const field=(key,input)=>{const label=node('label',undefined,input.type==='checkbox'?'toggle':'study-field');label.append(node('span',t('sms_'+key)),input);root.append(label);};
  for(const key of ['enabled','push_enabled','climate','plan','started','stopped','completed','report_link']){const input=node('input');input.type='checkbox';input.checked=cfg[key];input.disabled=(key==='enabled'&&!cap.available&&!cfg.enabled)||(key==='push_enabled'&&!cap.push_available&&!cfg.push_enabled);input.onchange=()=>cfg[key]=input.checked;field(key,input);}
  const reminder=node('input');reminder.type='checkbox';reminder.checked=cfg.reminder_enabled;reminder.disabled=!cap.reminder_available&&!cfg.reminder_enabled;reminder.onchange=()=>cfg.reminder_enabled=reminder.checked;field('reminder_enabled',reminder);
  root.append(node('p',t(cap.reminder_available?'sms_reminder_hint':'sms_reminder_missing'),'hint'));
  const offsets=node('input');offsets.type='text';offsets.value=cfg.reminder_offsets.join(', ');offsets.oninput=()=>cfg.reminder_offsets=offsets.value.split(',').map(s=>Number(s.trim()));field('reminder_offsets',offsets);
  const sender=node('select');const empty=node('option',t('study_none'));empty.value='';sender.append(empty);for(const value of new Set([...cap.senders,...(cfg.sender?[cfg.sender]:[])])){const option=node('option',value);option.value=value;sender.append(option);}sender.value=cfg.sender;sender.onchange=()=>cfg.sender=sender.value;field('sender',sender);
  const push=node('select');const noPush=node('option',t('study_none'));noPush.value='';push.append(noPush);for(const value of new Set([...cap.push_services,...(cfg.push_service?[cfg.push_service]:[])])){const option=node('option',value);option.value=value;push.append(option);}push.value=cfg.push_service;push.onchange=()=>cfg.push_service=push.value;field('push_service',push);
  const recipient=node('input');recipient.type='tel';recipient.autocomplete='off';recipient.value=cfg.recipient;recipient.placeholder='+…';recipient.oninput=()=>cfg.recipient=recipient.value.trim();field('recipient',recipient);
  const language=node('select');for(const [value,label] of [['en','English'],['he','עברית']]){const option=node('option',label);option.value=value;language.append(option);}language.value=cfg.language;language.onchange=()=>cfg.language=language.value;field('language',language);
  const save=node('button',t('sms_save'));save.type='button';save.onclick=async()=>{save.disabled=true;try{await api({op:'sms_save',settings:cfg});await show();status.textContent=t('sms_saved');}catch{status.textContent=t('sms_error');}finally{save.disabled=false;}};root.append(save);
  const refresh=node('button',t('sms_refresh'));refresh.type='button';refresh.onclick=show;root.append(refresh);
  if(data.error||data.reminder_error)root.append(node('p',t('sms_error'),'error'));
  if(data.events.length){root.append(node('h3',t('sms_recent')));for(const e of data.events)root.append(node('p',`${e.channel==='push'?t('sms_push_enabled'):t('sms_enabled')} · ${e.at} · ${e.run_id.slice(0,8)} · ${t('sms_'+e.event)} · ${t('sms_status_'+e.status)}`));}
  root.append(status);
 }catch{root.replaceChildren(node('p',t('sms_error'),'error'));}};
 show();
}
