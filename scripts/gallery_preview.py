"""Loopback-only fictional gallery fixture. Never connects to Home Assistant."""
import argparse
import json
import importlib.util
from copy import deepcopy
from datetime import datetime, timezone
from shabbat_flow.server import Handler, ThreadingHTTPServer, ROOT, WEB

areas = [('room_a', 'Room A / חדר א׳', 'bedroom'), ('family_room', 'Family room / חדר משפחה', 'common_area'), ('bathroom', 'Bathroom / חדר רחצה', 'bathroom')]
entities=[]
rooms={}
for aid,name,kind in areas:
    roles={}
    for role,domain,label in [('main_lights','light','Main / ראשי'),('night_lights','light','Night / לילה'),('hvac','climate','HVAC / מיזוג'),('fans','fan','Ceiling fan / מאוורר תקרה')]:
        if role=='fans' and kind!='bedroom':roles[role]=[];continue
        if kind=='bathroom' and role=='hvac':roles[role]=[];continue
        eid=f'{domain}.{aid}_{role}'
        roles[role]=[eid]
        entities.append(dict(id=eid,entity_id=eid,name=label,domain=domain,area_id=aid,available=True,disabled=False,labels=[role],capabilities={'hvac_modes':['off','heat','cool'],'fan_modes':['auto']}))
    rooms[aid]={'enabled':True,'setup':{'status':'ready','area_type':{'bedroom':'room','common_area':'common'}.get(kind,kind),'service':kind!='bedroom','home':kind=='bathroom','bathroom_timing':{'bathroom':'use_window'}},'purposes':['sleeping'] if kind=='bedroom' else [],'roles':roles,'shared_areas':['bathroom'] if kind=='bedroom' else [],'hvac':{'mode':'none','temperature':None,'fan_mode':None,'lead_minutes':60}}
fixture={'observed_at':datetime.now(timezone.utc).isoformat(),'issues':[],'inventory':{'revision':'fictional','timezone':'Asia/Jerusalem','areas':[{'id':a,'name':n,'labels':[k],'floor_id':'floor'} for a,n,k in areas],'floors':[{'id':'floor','name':'Example floor / קומת הדגמה'}],'labels':[{'id':v,'name':v} for v in ['main_lights','night_lights','fans','bedroom','common_area','bathroom']],'entities':entities},'settings':{'revision':1,'rooms':rooms,'label_filters':{'main_lights':'main_lights','night_lights':'night_lights','bathroom':'main_lights'},'post_shutoff':False}}
# Public screenshots and performance checks use only fictional capabilities/devices.
dependencies=[{'id':i,'requirement':r,'hint':i,'ready':True,'detected':True,'status':'ready'} for i,r in [('core','required'),('areas','required_for_rooms'),('calendar','preferred'),('twilio','optional'),('push','optional'),('external_url','optional'),('climate','required_for_climate'),('weather','optional'),('temperature','optional'),('labels','optional'),('automations','optional'),('issur','optional')]]
study_sources={'climates':[{'entity_id':f'climate.zone_{i}','name':f'Zone {i}','area_id':f'area_{i}','area_name':f'Room {i}'} for i in range(100)],'lights':[{'entity_id':f'switch.signal_{i}','name':f'Signal {i}','area_id':f'area_{i%100}'} for i in range(2000)],'references':[],'weather':[]}
activity_examples = False
example_runs = [
    {'id': 'a'*32, 'kind': 'plan', 'status': 'scheduled', 'start': '2027-01-08T15:30:00+02:00', 'end': '2027-01-09T18:00:00+02:00', 'timezone': 'Asia/Jerusalem'},
    {'id': 'b'*32, 'kind': 'climate_study', 'status': 'observing', 'start': '2027-01-08T09:00:00+02:00', 'end': '2027-01-09T09:00:00+02:00', 'timezone': 'Asia/Jerusalem'},
]
# Minimal, explicitly fictional report data for gallery and review UX checks.
spec=importlib.util.spec_from_file_location('sf_report_fixture',ROOT/'custom_components/shabbat_flow/reports.py')
report_model=importlib.util.module_from_spec(spec);spec.loader.exec_module(report_model)
report_run={'id':'c'*32,'kind':'plan','mode':'observe','status':'completed','start':'2027-01-08T14:20:00Z','end':'2027-01-09T15:30:00Z','snapshot_hash':'fictional-plan-revision','bundle':{'config':{'rooms':{'room_a':{'en':'Room A','he':'חדר א׳'}},'loads':{'main':{'physical_id':'p','display':{'room':'room_a'}}}},'plan':{'snapshot':{'timezone':'Asia/Jerusalem'}}},'summary':{'p':{'matched_seconds':42000,'mismatched_seconds':1800,'unknown_seconds':600,'unplanned_seconds':300}},'mapping':{'p':{'entity_id':'light.example'}},'preview':{'events':[]},'event_checks':{'one':{'outcome':'matched'},'two':{'outcome':'mismatched'}},'gaps':[]}
report_review={'revision':0,'value':None,'history':[]}
def report_fixture():return {'run':deepcopy(report_run),'performance':report_model.performance(report_run),'review':deepcopy(report_review),'mode':'observe','device_commands_sent':0}
class GalleryHandler(Handler):
    def do_POST(self):
        if not self.permitted(): return
        if self.path=='/api/v2/execution':
            body=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
            if body.get('op')!='review':self.reply(400,{'error':'fixture_read_only'});return
            from shabbat_flow.schedule import compile_schedule
            bundle=body['bundle'];preview=compile_schedule(**bundle);snap=bundle['plan']['snapshot']
            self.reply(200,{'has_home':any(a['state']=='home' for a in bundle['plan']['availability']),'start':snap['preparation_start'],'end':snap['end'],'deadline':snap['preparation_start'],'unknown_sources':[],'review_digest':'fictional','loads':[{'physical_id':k,'entity_id':'light.example_'+k,'name':v['label'],'reasons':[] if v['kind']=='binary' else ['execute_unsupported'],'writers':[],'first_event':next((e for e in preview['events'] if e['physical_id']==k),None),'last_event':next((e for e in reversed(preview['events']) if e['physical_id']==k),None)} for k,v in bundle['config']['loads'].items()]});return
        if self.path=='/api/v2/observe':
            body=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
            if body.get('op')=='reports':
                self.reply(200,{'runs':[{'id':report_run['id'],'kind':'plan','status':'completed','start':report_run['start'],'end':report_run['end'],'timezone':'Asia/Jerusalem','reviewed':report_review['value'] is not None,'performance':report_model.performance(report_run)['totals']},*example_runs]});return
            if body.get('op')=='export' and body.get('id')==report_run['id']:self.reply(200,report_fixture());return
            if body.get('op')=='review' and body.get('id')==report_run['id']:
                if body['revision']!=report_review['revision']:self.reply(409,{'error':'observe_review_conflict'});return
                report_review.update(value=body['value'],revision=report_review['revision']+1,updated_at='2027-01-10T12:00:00Z');self.reply(200,report_review);return
            if body.get('op')=='dependencies': self.reply(200,{'dependencies':dependencies});return
            if body.get('op')=='sms_get':
                self.reply(200,{'settings':{'enabled':False,'push_enabled':False,'climate':True,'plan':True,'started':True,'stopped':True,'completed':True,'report_link':True,'reminder_enabled':False,'reminder_offsets':[180,60,30],'sender':'','push_service':'','recipient':'','language':'en'},'capability':{'available':True,'push_available':True,'report_url_available':True,'reminder_available':True,'senders':[],'push_services':[]},'events':[]});return
            self.reply(400,{'error':'fixture_read_only'});return
        super().do_POST()

    def do_GET(self):
        if not self.permitted(): return
        path=self.path.split('?')[0]
        if path in ('/execution-demo','/execution-demo.mjs'):
            sample=json.loads((ROOT/'examples/period-preview.json').read_text())
            code='sessionStorage.setItem("shabbat-flow-household-workspace",'+json.dumps(json.dumps(sample))+');location.replace("/period.html?household=1")'
            self.reply(200,code.encode() if path.endswith('.mjs') else b'<script type="module" src="/execution-demo.mjs"></script>','text/javascript' if path.endswith('.mjs') else 'text/html; charset=utf-8');return
        if path=='/api/v2/execution':self.reply(200,{'error':None,'runs':[]});return
        if path=='/api/v2/observe':self.reply(200,{'study_sources':study_sources,'runs':example_runs if activity_examples else [],'thermal_sources':{'climates':[],'weather':[]}})
        elif path=='/api/v2/household':self.reply(200,fixture)
        elif path=='/api/v2/upcoming':self.reply(200,{'status':'unavailable','error':'calendar_unavailable'})
        elif path.startswith('/sample-'):
            file=ROOT/'dist'/('shabbat-flow-sample-climate-study.html' if path=='/sample-climate.html' else 'shabbat-flow-sample-observation-report.html')
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(file.read_bytes())
        elif path not in ('/','/v2') and (WEB/path.lstrip('/')).is_file() and '/' not in path.lstrip('/'):
            file=WEB/path.lstrip('/');mime={'.mjs':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html'}.get(file.suffix)
            if mime:self.reply(200,json.loads(file.read_text()) if mime=='application/json' else file.read_bytes(),mime)
            else:self.reply(404,{'error':'not_found'})
        else:super().do_GET()
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8773)
    parser.add_argument('--activity-examples',action='store_true')
    args=parser.parse_args()
    activity_examples=args.activity_examples
    if activity_examples:
        rooms['family_room']['setup']['status']='draft'
        rooms['bathroom']['roles']['main_lights']=[]
        rooms['bathroom']['roles']['night_lights']=[]
    print(f'Fictional gallery fixture: http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),GalleryHandler).serve_forever()
