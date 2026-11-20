"""Build a self-contained fictional report using the production HTML renderer."""
import base64
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
start=datetime(2027,1,8,14,tzinfo=timezone.utc)
end=start+timedelta(hours=25)
series=[]
for i in range(26):
    climates={}
    for name,offset in [('study',0),('guest_room',1.3),('unused_room',-.8)]:
        mode='off' if name=='unused_room' else ('heat' if i<5 else 'off' if i<21 else 'cool') if name=='guest_room' else ('heat' if i<8 else 'off' if i<17 else 'cool')
        climates['climate.'+name]={'mode':mode,'power':'off' if mode=='off' else 'on',
          'hvac_action':{'heat':'heating','cool':'cooling','off':'off'}[mode],
          'current_temperature':{'celsius':round(20+offset+math.sin(i/4)*2,1)},
          'target_temperature':{'celsius':22 if i<17 else 21}}
    at=(start+timedelta(hours=i)).isoformat()
    series.append({'due':at,'sampled_at':at if i not in (9,10) else None,'status':'missing' if i in (9,10) else 'sampled',
                   'climates':climates,'outdoor':{'current_temperature':{'celsius':round(15+math.sin(i/4)*4,1)}}})
run={'id':'fictional-example-only','snapshot_hash':'synthetic-demonstration-not-a-household-plan',
     'start':start.isoformat(),'end':end.isoformat(),'bundle':{'plan':{'snapshot':{'timezone':'Asia/Jerusalem'}}},
     'mapping':{},'summary':{},'thermal':{'outdoor':{'entity_id':'weather.example'},'climates':[
         {'entity_id':'climate.study','area_name':'Study','planner_room_id':'study'},{'entity_id':'climate.guest_room','area_name':'Guest room','planner_room_id':'guest'},{'entity_id':'climate.unused_room','area_name':'Unused room','planner_room_id':'unused'}],'samples':series}}
for name,minutes in [('climate.study',(1350,60,60,30)),('climate.guest_room',(1290,120,60,30)),('light.hall',(1380,30,60,30))]:
    run['mapping'][name]={'entity_id':name};run['summary'][name]={key+'_seconds':value*60 for key,value in zip(('matched','mismatched','unknown','unplanned'),minutes)}
def stamp(hours): return (start+timedelta(hours=hours)).isoformat()
run['status']='completed';run['last_sample']=end.isoformat();run['gaps']=[{'start':stamp(9),'end':stamp(10)}]
run['thermal']['activity']={'totals':{eid:{'on_seconds':on*60,'off_seconds':off*60,'unknown_seconds':60*60,'seen_on':on>0} for eid,on,off in [('climate.study',960,480),('climate.guest_room',540,900),('climate.unused_room',0,1440)]}}
run['bundle']['plan'].update(room_uses=[{'room':'study','purpose':'sleeping','start':stamp(7),'end':stamp(16)}],naps=[{'room':'study','start':stamp(21),'end':stamp(23)}])
run['bundle']['config']={'loads':{},'groups':{}}
run['preview']={'events':[]};run['changes']=[]
for role,name,events,actual in [('main_lights','Study main',[(0,'on'),(7,'off'),(17,'on')],[(0,'on'),(7.5,'off'),(17,'on')]),('night_lights','Study background',[(0,'off'),(7,'on'),(14,'off')],[(0,'off'),(7.5,'on'),(14,'off')])]:
    physical='study_'+role
    run['bundle']['config']['loads'][physical]={'kind':'binary','physical_id':physical,'display':{'room':'study','role':role},'label':{'en':name,'he':name}}
    run['mapping'][physical]={'entity_id':'light.'+physical}
    for hour,state in events:run['preview']['events'].append({'physical_id':physical,'utc':stamp(hour),'action':{'type':'state','state':state},'intent':'set_state'})
    for hour,state in actual:run['changes'].append({'physical_id':physical,'observed_at':stamp(hour),'state':state})
labels=json.loads((ROOT/'src/shabbat_flow/web/period-i18n.json').read_text())
renderer=(ROOT/'src/shabbat_flow/web/thermal-report.mjs').read_text().replace('export function','function')
css=(ROOT/'src/shabbat_flow/web/style.css').read_text()
logo=base64.b64encode((ROOT/'assets/logo.png').read_bytes()).decode()
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ShabbatFlow - fictional observation summary</title><style>'''+css+'''
body{padding:24px}#print-report{display:block;max-width:1100px;margin:auto}#print-report>.brand-logo{width:280px}.sample-banner{padding:16px;background:#fff1d6;border:2px solid #9c6100;max-width:1068px;margin:0 auto 20px;font-weight:700}table{width:100%;border-collapse:collapse}td,th{padding:12px;border-bottom:1px solid #d8e3e7;text-align:start}#print-report>p{overflow-wrap:anywhere}@media print{body{padding:0}.sample-banner{display:block!important}}
</style><div class="sample-banner">FICTIONAL SAMPLE - not your household data. Illustrates the actual report layout; no devices were controlled.</div><section id="print-report"></section><script type="module">'''+renderer+'''
const data='''+json.dumps({'run':run})+''';const labels='''+json.dumps(labels)+''';
const lang=()=>new URLSearchParams(location.search).get('lang')==='he'?'he':'en';document.documentElement.lang=lang();document.documentElement.dir=lang()==='he'?'rtl':'ltr';
const node=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};const logo=node('img');logo.src="data:image/png;base64,'''+logo+'''";logo.alt='ShabbatFlow';renderObservationPrint({report:document.getElementById('print-report'),data,node,t:k=>labels[lang()][k],lang,logo});
document.querySelector('.thermal-card').id='sample-zone-first';document.querySelector('.thermal-combined').id='sample-combined';
</script></html>'''
output=ROOT/'dist'/'shabbat-flow-sample-observation-report.html'
output.parent.mkdir(exist_ok=True);output.write_text(html)
print(output)
