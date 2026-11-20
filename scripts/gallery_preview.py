"""Loopback-only fictional gallery fixture. Never connects to Home Assistant."""
import json
from datetime import datetime, timezone
from shabbat_flow.server import Handler, ThreadingHTTPServer, ROOT, WEB

areas = [('room_a', 'Room A / חדר א׳', 'bedroom'), ('family_room', 'Family room / חדר משפחה', 'common_area'), ('bathroom', 'Bathroom / חדר רחצה', 'bathroom')]
entities=[]
rooms={}
for aid,name,kind in areas:
    roles={}
    for role,domain,label in [('main_lights','light','Main / ראשי'),('night_lights','light','Night / לילה'),('hvac','climate','HVAC / מיזוג')]:
        if kind=='bathroom' and role=='hvac':roles[role]=[];continue
        eid=f'{domain}.{aid}_{role}'
        roles[role]=[eid]
        entities.append(dict(id=eid,entity_id=eid,name=label,domain=domain,area_id=aid,available=True,disabled=False,labels=[role],capabilities={'hvac_modes':['off','heat','cool'],'fan_modes':['auto']}))
    rooms[aid]={'enabled':True,'setup':{'status':'ready','area_type':{'bedroom':'room','common_area':'common'}.get(kind,kind),'service':kind!='bedroom','home':kind=='bathroom','bathroom_timing':{'bathroom':'use_window'}},'purposes':['sleeping'] if kind=='bedroom' else [],'roles':roles,'shared_areas':['bathroom'] if kind=='bedroom' else [],'hvac':{'mode':'none','temperature':None,'fan_mode':None,'lead_minutes':60}}
fixture={'observed_at':datetime.now(timezone.utc).isoformat(),'issues':[],'inventory':{'revision':'fictional','timezone':'Asia/Jerusalem','areas':[{'id':a,'name':n,'labels':[k],'floor_id':'floor'} for a,n,k in areas],'floors':[{'id':'floor','name':'Example floor / קומת הדגמה'}],'labels':[{'id':v,'name':v} for v in ['main_lights','night_lights','bedroom','common_area','bathroom']],'entities':entities},'settings':{'revision':1,'rooms':rooms,'label_filters':{'main_lights':'main_lights','night_lights':'night_lights','bathroom':'main_lights'},'post_shutoff':False}}
class GalleryHandler(Handler):
    def do_GET(self):
        if not self.permitted(): return
        path=self.path.split('?')[0]
        if path=='/api/v2/household':self.reply(200,fixture)
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
    print('Fictional gallery fixture: http://127.0.0.1:8771',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8771),GalleryHandler).serve_forever()
