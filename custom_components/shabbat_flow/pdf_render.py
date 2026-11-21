"""Local, vector PDF reports from frozen data. No network or device operations."""
import io
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from bidi.algorithm import get_display
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Flowable, Table, TableStyle, Spacer, Image, PageBreak

ROOT = Path(__file__).parent
RENDERER = '1'
TEAL = '#087d7b'
WORDS = {
'en': {'map_legend':'Teal: On · Grey: Off · Amber: Unknown · Purple: Planned room use','external_release':'Release left to existing control','threshold':'Temperature threshold','minimum_dwell':'Minimum dwell','outside_window':'Outside window','missing_evidence':'Missing evidence','activity_gate_off':'Activity signals off','planner_signal_dependency':'Planner-controlled signal','clock_rollback':'Clock rollback','unassigned':'Unassigned room','low':'Target low','high':'Target high','power':'Power','hvac_action':'HVAC action','reason':'Reason','existing':'Existing Automation','track_only':'Track only','generated':'Generated','preview':'Plan preview — no device commands','report':'Observation report','climate':'Climate study','partial':'Partial observation','notice':'Sampled observations are not proof of occupancy, comfort or automation execution. No device commands were sent.','review':'Saved feedback','summary':'Expected versus observed (device-minutes)','room':'Room','matched':'Matched','mismatched':'Different','unknown':'Unknown','unplanned':'No plan','overall':'Overall fit','lighting':'Lighting fit','climate_rating':'HVAC comfort','worked':'What worked well','differed':'What differed','next_change':'Next adjustment','destination':'Improvement destination','decision':'Follow-up status','period_type':'Period context','settings':'Settings / future plan','app':'Application / requirements','uncertain':'Uncertain','ordinary':'Ordinary','exceptional':'Exceptional','proposed':'Proposed','applied':'Reported as applied','deferred':'Deferred','dismissed':'Dismissed','na':'Not applicable','zones':'HVAC zones (most active first)','active':'Active','inactive':'Inactive throughout','on':'On','off':'Off','current':'Unit reading','target':'Target','reference':'Reference','outdoor':'Outdoor','time':'Local time','mode':'Mode','use':'Planned room use','planned':'Planned','observed':'Observed activity signal','table':'Hourly temperature samples (°C)','light_hint':'Light/switch states are activity signals, not occupancy. Unknown intervals and gaps are not inferred.','schedule':'Schedule','device':'Device','action':'Action','meals':'Meals and room use','preserve':'On/off only — preserve settings','days':'Day','no_data':'No recorded samples','coverage':'Assessed share','agreement':'Agreement among assessed minutes','gaps':'Collection gaps','truncated':'Data was truncated or automation definitions changed; interpret with care.','comfort':'Comfort-policy shadow evidence (no commands)','key':'Policy','eligible':'Eligible samples','would':'Would request on','hold':'Would keep off','floor':'Below release threshold','ignored':'Unknown / unavailable','heat':'Heat','cool':'Cool','auto':'Auto','heat_cool':'Heat/cool','dry':'Dry','fan_only':'Fan only'},
'he': {'map_legend':'טורקיז: פועל · אפור: כבוי · כתום: לא ידוע · סגול: שימוש מתוכנן','external_release':'סיום בשליטה חיצונית','threshold':'סף טמפרטורה','minimum_dwell':'משך מזערי','outside_window':'מחוץ לחלון','missing_evidence':'חסר מידע','activity_gate_off':'סימני פעילות כבויים','planner_signal_dependency':'תלות בסימן בשליטת המתכנן','clock_rollback':'שעון נסוג','unassigned':'חדר לא משויך','low':'יעד תחתון','high':'יעד עליון','power':'הפעלה','hvac_action':'פעולת מיזוג','reason':'סיבה','existing':'אוטומציה קיימת','track_only':'מעקב בלבד','generated':'נוצר','preview':'תצוגת תוכנית — ללא פקודות למכשירים','report':'דוח מעקב','climate':'מחקר אקלים','partial':'מעקב חלקי','notice':'דגימות אינן הוכחה לנוכחות, לנוחות או להפעלת אוטומציות. לא נשלחו פקודות למכשירים.','review':'משוב שמור','summary':'צפוי לעומת נצפה (דקות־מכשיר)','room':'חדר','matched':'תואם','mismatched':'שונה','unknown':'לא ידוע','unplanned':'ללא תוכנית','overall':'התאמה כללית','lighting':'התאמת תאורה','climate_rating':'נוחות מיזוג','worked':'מה עבד היטב','differed':'מה השתנה','next_change':'שינוי לפעם הבאה','destination':'יעד השיפור','decision':'מצב הטיפול','period_type':'אופי התקופה','settings':'הגדרות / תוכנית עתידית','app':'יישום / דרישות','uncertain':'לא ודאי','ordinary':'רגיל','exceptional':'חריג','proposed':'מוצע','applied':'דווח כמיושם','deferred':'נדחה להמשך','dismissed':'לא ייושם','na':'לא רלוונטי','zones':'אזורי מיזוג (הפעילים ביותר תחילה)','active':'פעיל','inactive':'לא פעל לאורך התקופה','on':'פועל','off':'כבוי','current':'קריאת היחידה','target':'יעד','reference':'ייחוס','outdoor':'חוץ','time':'זמן מקומי','mode':'מצב','use':'שימוש מתוכנן בחדר','planned':'מתוכנן','observed':'סימן פעילות שנצפה','table':'דגימות טמפרטורה שעתיות (°C)','light_hint':'מצבי תאורה ומתגים הם סימני פעילות, לא נוכחות. פרקי זמן לא ידועים ופערים אינם מושלמים בהשערה.','schedule':'לוח זמנים','device':'מכשיר','action':'פעולה','meals':'ארוחות ושימוש בחדרים','preserve':'הפעלה וכיבוי בלבד — שמירת הגדרות','days':'יום','no_data':'אין דגימות שנרשמו','coverage':'שיעור דקות שנבדקו','agreement':'התאמה בדקות שנבדקו','gaps':'פערים באיסוף','truncated':'נתונים נקטעו או שהגדרות אוטומציות השתנו; יש לפרש בזהירות.','comfort':'ראיות מדיניות נוחות במעקב בלבד','key':'מדיניות','eligible':'דגימות כשירות','would':'היה מבקש הפעלה','hold':'היה משאיר כבוי','floor':'מתחת לסף השחרור','ignored':'לא ידוע / לא זמין','heat':'חימום','cool':'קירור','auto':'אוטומטי','heat_cool':'חימום וקירור','dry':'ייבוש','fan_only':'אוורור בלבד'}}

def stamp(value):
    return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()

def number(value):
    return value if type(value) in (int,float) and math.isfinite(value) else None

def clean(value):
    # Strip directional/control overrides; bidi computes direction from actual text.
    text=''.join(c for c in str(value) if c in '\n\t' or ord(c)>=32 and not 0x202a<=ord(c)<=0x202e and not 0x2066<=ord(c)<=0x2069)
    return re.sub(r'\u200e?(\(°[CF]\)|(?:-?\d+(?:\.\d+)?\s*)?°[CF])\u200e?',lambda m:'\u200e'+m[1]+'\u200e',text)

class Text(Flowable):
    def __init__(self,text,lang='en',size=9,bold=False,lines=None):
        super().__init__();self.text=clean(text);self.lang=lang;self.size=size;self.font='SFBold' if bold else 'SF';self.lines=lines;self.leading=size*1.45
    def wrap(self,width,height):
        self.width=max(12,width)
        if self.lines is None:
            self.lines=[]
            for paragraph in self.text.split('\n'):
                line=''
                for word in paragraph.split():
                    # Split long identifiers without losing text or overflowing a cell.
                    parts=[];part=''
                    for c in word:
                        if part and pdfmetrics.stringWidth(part+c,self.font,self.size)>self.width:parts.append(part);part=''
                        part+=c
                    parts.append(part)
                    for piece in parts:
                        trial=(line+' '+piece).strip()
                        if line and pdfmetrics.stringWidth(trial,self.font,self.size)>self.width:self.lines.append(line);line=piece
                        else:line=trial
                self.lines.append(line)
        self.height=max(1,len(self.lines))*self.leading
        return self.width,self.height
    def split(self,width,height):
        self.wrap(width,height);n=int(height/self.leading)
        if n<1:return []
        return [Text('',self.lang,self.size,self.font=='SFBold',self.lines[:n]),Text('',self.lang,self.size,self.font=='SFBold',self.lines[n:])] if n<len(self.lines) else [self]
    def draw(self):
        c=self.canv;c.setFont(self.font,self.size);c.setFillColor(colors.HexColor('#173448'))
        for i,line in enumerate(self.lines):
            value=get_display(line,base_dir='R' if self.lang=='he' else 'L')
            fn=c.drawRightString if self.lang=='he' else c.drawString
            fn(self.width if self.lang=='he' else 0,self.height-(i+1)*self.leading+3,value)

class Chart(Flowable):
    """Temperature series and categorical interval bands, all vector primitives."""
    def __init__(self,start,end,series,bands,lang,zone):
        super().__init__();self.start=start;self.end=end;self.series=series;self.bands=bands;self.lang=lang;self.zone=zone;self.height=(190 if series else 30)+len(bands)*31;self.width=500
    def wrap(self,width,height):self.width=width;return width,self.height
    def draw(self):
        c=self.canv;w=self.width;left=34;right=w-8;plot=self.height-30;lowy=plot-130;x=lambda a:left+(a-self.start)/max(1,self.end-self.start)*(right-left)
        def label(text,xx,yy,size=7):
            text=clean(text)
            while pdfmetrics.stringWidth(text,'SF',size)>w-xx and len(text)>1:text=text[:-2]+'…'
            c.setFont('SF',size);c.setFillColor(colors.HexColor('#173448'));c.drawString(xx,yy,get_display(clean(text),base_dir='R' if self.lang=='he' else 'L'))
        if self.series:
            vals=[v for _,_,points in self.series for _,v in points if v is not None];lo=math.floor(min(vals))-1 if vals else 0;hi=math.ceil(max(vals))+1 if vals else 30;y=lambda v:lowy+(v-lo)/(hi-lo)*130
            for i in range(5):
                yy=lowy+130*i/4;c.setStrokeColor(colors.HexColor('#d8e3e7'));c.line(left,yy,right,yy);label(f'{lo+(hi-lo)*i/4:.1f}',0,yy-2)
            for name,color,points in self.series:
                c.setStrokeColor(colors.HexColor(color));c.setFillColor(colors.HexColor(color));c.setLineWidth(1.2);prev=None
                for at,v in points:
                    if v is None:prev=None;continue
                    xy=x(at),y(v)
                    if prev:c.line(*prev,*xy)
                    c.circle(*xy,1.7,stroke=0,fill=1);prev=xy
            # Two-row legend to avoid clipping in Hebrew or long labels.
            for i,(name,color,_) in enumerate(self.series):
                xx=(i%3)*w/3;c.setFillColor(colors.HexColor(color));c.rect(xx,self.height-9-(i//3)*11,8,3,fill=1,stroke=0);label(name,xx+12,self.height-10-(i//3)*11)
            top=lowy-24
        else:top=self.height-20
        for i in range(5):
            at=self.start+(self.end-self.start)*i/4;txt=datetime.fromtimestamp(at,self.zone).strftime('%d/%m %H:%M');xx=max(0,min(w-65,x(at)-25));label(txt,xx,top+10,6.5)
        for i,(name,intervals) in enumerate(self.bands):
            yy=top-15-i*31;label(name,0,yy+8,7)
            c.setFillColor(colors.HexColor('#edf1f3'));c.rect(left,yy-4,right-left,6,fill=1,stroke=0)
            for a,b,state in intervals:
                color={'on':TEAL,'use':'#8b68b0','off':'#dce3e8','unknown':'#dda548','heat':'#d36536','cool':'#2589c4','auto':'#8867aa','heat_cool':'#8867aa','dry':'#b78531','fan_only':'#53875f'}.get(state,'#dda548')
                a=max(a,self.start);b=min(b,self.end)
                if b>a:c.setFillColor(colors.HexColor(color));c.rect(x(a),yy-4,x(b)-x(a),6,fill=1,stroke=0)

def intervals(points,start,end,gaps=(),last=None,truncated=False):
    points=sorted(points);cuts=sorted({start,end,*[a for a,_ in points if start<a<end],*[v for g in gaps for v in g if start<v<end],*([last] if last and start<last<end else [])});out=[]
    for a,b in zip(cuts,cuts[1:]):
        state='unknown'
        for at,v in points:
            if at>a:break
            state=v
        if truncated or last is not None and a>=last or any(ga<b and gb>a for ga,gb in gaps):state='unknown'
        out.append((a,b,state))
    return out

def render_pdf(data,lang,kind):
    for name,file in [('SF','DejaVuSans.ttf'),('SFBold','DejaVuSans-Bold.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(name,str(ROOT/'fonts'/file)))
    words=WORDS[lang];catalogs={}
    for file in ('i18n.json','period-i18n.json'):catalogs.update(json.loads((ROOT/'www'/file).read_text())[lang])
    t=lambda key:words.get(key,catalogs.get(key,key));story=[];out=io.BytesIO()
    def text(value,size=9,bold=False):story.append(Text(value,lang,size,bold));story.append(Spacer(1,5))
    def title(value):text(value,14,True)
    def label(value):return value.get(lang,next(iter(value.values()),'')) if isinstance(value,dict) else t(str(value))
    def table(headers,rows,widths=None):
        if not rows:return
        rows=[[Text(label(v),lang,7.5,i==0) for v in row] for i,row in enumerate([headers,*rows])]
        if lang=='he':rows=[list(reversed(r)) for r in rows];widths=list(reversed(widths)) if widths else None
        tb=Table(rows,colWidths=widths or [499/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT',splitByRow=1,splitInRow=1)
        tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f3f4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#d8e3e7')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(tb);story.append(Spacer(1,10))
    run=data.get('run');bundle=run['bundle'] if run else data['bundle'];plan=bundle['plan'];config=bundle.get('config',{});snapshot=plan['snapshot'];zone=ZoneInfo(snapshot['timezone']);fmt=lambda v:datetime.fromisoformat(v.replace('Z','+00:00')).astimezone(zone).strftime('%d/%m/%Y %H:%M')
    start=run['start'] if run else snapshot['preparation_start'];end=run['end'] if run else snapshot['end'];a,b=stamp(start),stamp(end)
    image=Image(str(ROOT/'www/logo.png'),width=210,height=210*100/320,kind='proportional');image.hAlign='RIGHT' if lang=='he' else 'LEFT';story.append(image);story.append(Spacer(1,12));title(t('preview') if not run else t('climate' if run.get('kind')=='climate_study' else 'report'))
    text(f'{fmt(start)} — {fmt(end)} · {snapshot["timezone"]}');text(t('generated')+': '+datetime.now(zone).strftime('%d/%m/%Y %H:%M'));text(('Control and observation — see execution ledger; state agreement is not proof of command success.' if lang=='en' else 'ביצוע ומעקב — עיינו ביומן הביצוע; התאמת מצב אינה הוכחה להצלחת פקודה.') if data.get('execution') else t('notice') if run else t('report_preview'))
    if data.get('execution'):
        execution=data['execution'];title('Execution ledger' if lang=='en' else 'יומן ביצוע')
        text(execution['status']+' · '+execution['id'])
        table([t('device'),t('action'),t('time'),'Outcome' if lang=='en' else 'תוצאה'],[[execution['mapping'].get(v['physical_id'],{}).get('entity_id',v['physical_id']),t(v.get('wanted','unknown')),fmt(v['at']),v['status']] for v in execution['ledger'].values()])
    if run:
        text(run['id']+' · '+run.get('snapshot_hash',''),7)
        if run['status']!='completed':text(t('partial'),11,True)
        p=data.get('performance',{});tot=p.get('totals',{})
        title(t('summary'));text(f'{t("agreement")}: {tot.get("agreement_percent") if tot.get("agreement_percent") is not None else "—"}% · {t("coverage")}: {tot.get("assessed_percent") if tot.get("assessed_percent") is not None else "—"}%')
        table([t(k) for k in ('room','matched','mismatched','unknown','unplanned')],[[label(r.get('label') or r['room']),*[r[k] for k in ('matched','mismatched','unknown','unplanned')]] for r in p.get('rooms',[])],[175,81,81,81,81])
        text(f'{t("gaps")}: {p.get("gaps",0)}')
        if p.get('truncated') or p.get('source_changed'):text(t('truncated'))
        table([t(k) for k in ('device','matched','mismatched','unknown','unplanned')],[[run.get('mapping',{}).get(pid,{}).get('entity_id',pid),*[round(v.get(k+'_seconds',0)/60,1) for k in ('matched','mismatched','unknown','unplanned')]] for pid,v in run.get('summary',{}).items()],[175,81,81,81,81])
        if run.get('kind')=='climate_study':text(run['bundle'].get('study',{}).get('note',''))
        review=data.get('review',{}).get('value')
        if review:
            title(t('review'))
            for k,v in review.items():
                if v not in (None,''):text(t('climate_rating' if k=='climate' else k)+': '+t(str(v)))
        thermal=run.get('thermal') or {};frames=thermal.get('samples',[]);targets=thermal.get('climates',[])
        totals=thermal.get('activity',{}).get('totals',{})
        def rank(target):
            eid=target['entity_id'];on=totals.get(eid,{}).get('on_seconds',0);modes=[f.get('climates',{}).get(eid,{}).get('mode') for f in frames if f.get('status')=='sampled'];active=on>0 or totals.get(eid,{}).get('seen_on') or any(m in ('heat','cool','auto','heat_cool','dry','fan_only') for m in modes);return (0 if active else 1 if 'off' in modes or totals.get(eid,{}).get('off_seconds',0) else 2,-on,eid)
        title(t('zones'));text(t('light_hint'));text(t('outdoor')+': '+str((thermal.get('outdoor') or {}).get('entity_id') or '—'))
        allrows=[]
        for target in sorted(targets,key=rank):
            eid=target['entity_id'];story.append(PageBreak());title((target.get('area_name') or eid)+' · '+eid);stats=totals.get(eid,{})
            text(t(['active','inactive','unknown'][rank(target)[0]])+' · '+ ' · '.join(t(k)+': '+str(round(stats[k+'_seconds']/60,1)) if k+'_seconds' in stats else t(k)+': —' for k in ('on','off','unknown')))
            pairs=[]
            for f in frames:
                unit=(f.get('climates',{}).get(eid,{}).get('current_temperature') or {}).get('celsius');ref=(f.get('references',{}).get(eid,{}).get('current_temperature') or {}).get('celsius')
                if f.get('status')=='sampled' and number(unit) is not None and number(ref) is not None:pairs.append(unit-ref)
            if run.get('kind')=='climate_study':
                text(t('study_reference')+': '+str((target.get('reference') or {}).get('entity_id') or t('study_none')))
                text(t('study_delta')+': '+(str(round(sum(pairs)/len(pairs),2))+' °C' if pairs else '—')+' · '+t('study_pairs')+': '+str(len(pairs)));text(t('study_calibration_hint'))
            series=[];rows=[];modes=[]
            for key,color in [('current','#087d7b'),('target','#8c5bb6'),('reference','#c06d20'),('outdoor','#2589c4'),('low','#b075a5'),('high','#b075a5')]:
                pts=[]
                for f in frames:
                    sample=f.get('climates',{}).get(eid,{}) if f.get('status')=='sampled' else {};temp={'current':'current_temperature','target':'target_temperature','low':'target_low','high':'target_high'}.get(key)
                    value=(f.get('references',{}).get(eid,{}) if key=='reference' else f.get('outdoor',{}) if key=='outdoor' else sample).get(temp or 'current_temperature',{}).get('celsius') if f.get('status')=='sampled' else None
                    pts.append((stamp(f['due']),number(value)))
                if any(v is not None for _,v in pts):series.append((t(key),color,pts))
            for f in frames:
                sample=f.get('climates',{}).get(eid,{}) if f.get('status')=='sampled' else {};mode=sample.get('mode','unknown');at=stamp(f['due']);modes.append((at,mode));values=[]
                for source,key in [(sample,'current_temperature'),(sample,'target_temperature'),(f.get('references',{}).get(eid,{}),'current_temperature'),(f.get('outdoor',{}),'current_temperature')]:
                    v=number(source.get(key,{}).get('celsius')) if f.get('status')=='sampled' else None;values.append('—' if v is None else str(v))
                power=sample.get('power') or ('off' if mode=='off' else 'on' if mode in ('heat','cool','auto','heat_cool','dry','fan_only') else 'unknown')
                if values[1]=='—' and sample.get('target_low') and sample.get('target_high'):values[1]=str(sample['target_low'].get('celsius','—'))+'–'+str(sample['target_high'].get('celsius','—'))
                rows.append([fmt(f['due']),t(power),t(mode),t('observe_activity_'+(sample.get('hvac_action') if sample.get('hvac_action') in ('off','heating','cooling','drying','idle','fan','defrosting','preheating') else 'unknown')),*values])
            # Mode dots represent point samples only, never continuous compressor state.
            modebands=[(t('mode'),[(at,min(at+60,b),mode) for at,mode in modes])]
            story.append(Chart(a,b,series,modebands,lang,zone));text(' · '.join(t(k) for k in sorted(set(m for _,m in modes))))
            loads=config.get('loads',{});mapping=run.get('mapping',{});room=target.get('planner_room_id')
            for load in loads.values():
                if mapping.get(load['physical_id'],{}).get('entity_id')==eid:room=load.get('display',{}).get('room',room)
            bands=[];windows=[]
            for use in [*plan.get('room_uses',[]),*plan.get('naps',[])]:
                if room and use.get('room')==room:windows.append((stamp(use['start']),stamp(use['end']),'use'))
            for meal in plan.get('meals',[]):
                if meal.get('choice') not in ('family','hosting'):continue
                if any(loads.get(lid,{}).get('display',{}).get('room')==room for group in meal.get('groups',[]) for rule in config.get('groups',{}).get(group,{}).get('rules',[]) for lid in rule.get('targets',[])):windows.append((stamp(meal['start']),stamp(meal['end']),'use'))
            if windows:bands.append((t('use'),windows))
            gaps=[(stamp(g['start']),stamp(g['end'])) for g in run.get('gaps',[])];last=stamp(run.get('last_sample',start));seen=set()
            for load in loads.values():
                physical=load['physical_id'];entity=mapping.get(physical,{}).get('entity_id');display=load.get('display',{})
                if physical in seen or load.get('kind')!='binary' or (entity not in target.get('study_lights',[]) if run.get('kind')=='climate_study' else not room or display.get('room')!=room):continue
                seen.add(physical);name=label(load.get('label',entity or physical))
                if run.get('kind')!='climate_study':
                    points=[(stamp(e['utc']),e['action']['state']) for e in run.get('preview',{}).get('events',[]) if e['physical_id']==physical and e.get('intent')!='track_only' and e.get('action',{}).get('type')=='state'];bands.append((t('planned')+' · '+name,intervals(points,a,b)))
                points=[(stamp(e['observed_at']),e['state']) for e in run.get('changes',[]) if e['physical_id']==physical];bands.append((t('observed')+' · '+name,intervals(points,a,b,gaps,last,run.get('truncated',False))))
            for offset in range(0,len(bands),10):story.append(Chart(a,b,[],bands[offset:offset+10],lang,zone))
            title(t('table'));table([t(k) for k in ('time','power','mode','hvac_action','current','target','reference','outdoor')],rows,[99,48,58,58,59,59,59,59])
        if not targets:text(t('no_data'))
        if run.get('comfort'):
            title(t('comfort'));text(t('notice'));conditions={c['id']:c for c in run.get('preview',{}).get('flex',{}).get('conditions',[])}
            table([t(k) for k in ('time','device','current','action','reason')],[[fmt(d['at']),label(config.get('loads',{}).get(conditions.get(d['id'],{}).get('load'),{}).get('label',d.get('source','—'))),str(d.get('temperature','—'))+' '+str(d.get('unit') or ''),t(d.get('intent','unknown')),t(d.get('reason','unknown'))] for d in run['comfort'].get('decisions',[])],[99,130,60,60,150])
    else:
        from .engine.schedule import compile_schedule
        preview=compile_schedule(config,plan)
        title(t('meals'))
        for segment in snapshot.get('segments',[]):
            text(fmt(segment['start'])+' · '+ ' · '.join(segment.get('calendar_details',[])),11,True)
        for meal in plan.get('meals',[]):text(f'{t('meal_'+meal['kind'])} · {t(meal['choice'])} · {fmt(meal["start"])} — {fmt(meal["end"])}')
        for use in [*plan.get('room_uses',[]),*plan.get('naps',[])]:text(f'{label(config.get("rooms",{}).get(use["room"],use["room"]))} · {fmt(use["start"])} — {fmt(use["end"])}')
        events=preview['events'];title(t('schedule'));text(t('map_legend'));bands=[];seen=set()
        for load in config.get('loads',{}).values():
            physical=load['physical_id']
            if physical in seen or not any(e['physical_id']==physical and e.get('intent')!='track_only' for e in events):continue
            seen.add(physical);points=[(stamp(e['utc']),e['action'].get('state',('off' if e['action'].get('mode')=='off' else 'on') if e['action'].get('type')=='hvac' else 'unknown')) for e in events if e['physical_id']==physical and e.get('intent')!='track_only'];bands.append((label(load.get('label',physical)),intervals(points,a,b)))
        for offset in range(0,len(bands),12):story.append(Chart(a,b,[],bands[offset:offset+12],lang,zone))
        table([t('time'),t('device'),t('action')],[[fmt(e['utc']),label(next((l.get('label',e['physical_id']) for l in config['loads'].values() if l['physical_id']==e['physical_id']),e['physical_id'])),t('track_only') if e.get('intent')=='track_only' else t(e['action'].get('state',e['action'].get('mode','unknown')))+(' · '+str(e['action']['temperature'])+' °'+e['action'].get('unit','') if 'temperature' in e['action'] else '')+(' · '+t('preserve') if e['action']['type']=='hvac_power' else '')] for e in events],[115,275,109])
    if not run and data.get('overlay'):
        title(t('existing'));text(t('observe_forecast_hint'))
        overlay=data['overlay'];groups={}
        for event in overlay.get('events',[]):
            key=(event['utc'],event.get('source_name') or event.get('source',''),event['action']['state']);groups.setdefault(key,[]).append(event.get('target_name') or event['entity_id'])
        table([t('time'),t('device'),t('action')],[[fmt(at),name+' · '+', '.join(sorted(set(targets))),t(state)] for (at,name,state),targets in groups.items()],[115,275,109])
    def footer(c,doc):
        if doc.page>300:raise ValueError('pdf_too_large')
        c.setFont('SF',7);c.setFillColor(colors.HexColor('#526774'));c.drawString(48,24,'Shabbat Flow');c.drawRightString(A4[0]-48,24,str(doc.page))
    SimpleDocTemplate(out,pagesize=A4,rightMargin=48,leftMargin=48,topMargin=35,bottomMargin=40,title='Shabbat Flow',author='Shabbat Flow',pageCompression=1).build(story,onFirstPage=footer,onLaterPages=footer)
    value=out.getvalue()
    if len(value)>8*1024*1024:raise ValueError('pdf_too_large')
    return value
