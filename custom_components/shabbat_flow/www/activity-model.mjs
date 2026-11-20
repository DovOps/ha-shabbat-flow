import {parsePeriodDraft} from './period-model.mjs';
// Summarize persisted observer state, never infer collection from wall-clock time.
export function activitySummary(listing,rawDraft,now=Date.now()){
 const runs=(listing?.runs??[]).map(r=>({...r,kind:r.kind??'plan'}));
 const active=runs.filter(r=>['scheduled','observing'].includes(r.status)).sort((a,b)=>new Date(a.start)-new Date(b.start));
 const latest={};
 for(const kind of ['plan','climate_study'])latest[kind]=runs.filter(r=>r.kind===kind&&!['scheduled','observing'].includes(r.status)).sort((a,b)=>new Date(b.end)-new Date(a.end))[0]??null;
 let draft=null,draftError=false;
 if(rawDraft)try{
  const {snapshot}=parsePeriodDraft(rawDraft).plan;
  if(!snapshot||!Number.isFinite(+new Date(snapshot.start))||!Number.isFinite(+new Date(snapshot.end)))throw Error();
  new Intl.DateTimeFormat('en',{timeZone:snapshot.timezone}).format();
  draft={start:snapshot.start,end:snapshot.end,timezone:snapshot.timezone,past:+new Date(snapshot.end)<now};
 }catch{draftError=true;}
 return {active,latest,draft,draftError};
}
