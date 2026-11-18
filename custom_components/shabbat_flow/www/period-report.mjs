export function renderPrintReport({report,bundle,result,t,lang,dayLabel,node,timeline,logo}){
  report.replaceChildren();
  if(!result?.complete){report.append(node('p',t('report_unavailable')));return;}
  report.append(logo.cloneNode(),node('h1',t('report_title')),node('p',t('report_preview'),'report-notice'));
  const snapshot=bundle.plan.snapshot;
  const date=iso=>new Intl.DateTimeFormat(lang(),{timeZone:snapshot.timezone,year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(iso));
  report.append(node('p',`${snapshot.timezone} · ${t(snapshot.observance)} · ${date(snapshot.segments[0].start)} — ${date(snapshot.segments.at(-1).end)}`));
  for(const [i,segment] of snapshot.segments.entries()){
    const section=node('section',undefined,'report-day');section.append(node('h2',`${t(segment.kind)} · ${dayLabel(segment,i)}`));
    if(segment.calendar_details?.length)section.append(node('p',segment.calendar_details.join(' · '),'calendar-details'));
    section.append(node('p',`${t('candle_lighting')}: ${date(segment.candle_lighting)} · ${t('sunrise_anchor')}: ${date(segment.sunrise)}`));
    section.append(node('h3',t('meals_title')));
    for(const meal of bundle.plan.meals.filter(m=>m.segment===segment.id))section.append(node('p',`${t('meal_'+meal.kind)}: ${t(meal.choice)} · ${date(meal.start)} — ${date(meal.end)}`));
    const uses=bundle.plan.room_uses.filter(u=>u.segment===segment.id);
    if(uses.length){section.append(node('h3',t('report_uses')));for(const use of uses)section.append(node('p',`${bundle.config.rooms[use.room]?.[lang()]??use.room} · ${t(use.purpose)} · ${date(use.start)} — ${date(use.end)}`));}
    report.append(section);
  }
  report.append(node('h2',t('report_windows')));
  for(const window of bundle.plan.availability)report.append(node('p',`${t(window.state+'_state')} · ${date(window.start)} — ${date(window.end)}`));
  report.append(node('h2',t('timeline')));
  // Reuse the visible preview's localized warnings, reasons and action badges.
  for(const child of timeline.children)if(!child.classList.contains('event'))report.append(child.cloneNode(true));
  const table=node('table'),head=node('thead'),headers=node('tr');
  for(const key of ['report_time','report_device','report_action'])headers.append(node('th',t(key)));
  head.append(headers);table.append(head);const body=node('tbody');
  for(const event of timeline.querySelectorAll('.event')){const row=node('tr');for(const cell of event.children){const td=node('td');td.append(cell.cloneNode(true));row.append(td);}body.append(row);}
  table.append(body);report.append(table,node('p',t('report_preview'),'report-notice'));
}
