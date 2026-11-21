import copy,json,unittest
from pathlib import Path
from shabbat_flow.schedule import compile_schedule
from shabbat_flow.flexible import gate
from shabbat_flow.compiler import PlanError

class FlexibleTests(unittest.TestCase):
 def setUp(self):
  self.b=json.loads((Path(__file__).parents[1]/'examples/period-preview.json').read_text())
  self.p={'mode':'cool','target':22,'tolerance':1,'hysteresis':.5,'minimum_on':15,'minimum_off':10,'sensor':'','unit':'C','signals':[]}
 def flex(self):
  f={'version':1,'windows':[],'meals':[],'overrides':[],'feedback':[]};self.b['plan']['flex']=f;return f
 def window(self):
  return {'id':'test','room':'room_a','segment':'day_1','category':'playtime','start':'2027-01-08T14:00:00+02:00','end':'2027-01-08T16:00:00+02:00','targets':['room_a_light'],'hvac':[],'policy':'none','comfort':self.p,'release':'off','home_only':True,'sleep_conflict':'review','initial_state':'review','resume':'unknown'}
 def test_gate_strict_direction_units_hysteresis(self):
  self.assertEqual(gate(self.p,23,'C',1000)['intent'],'off')
  on=gate(self.p,24,'C',1000);self.assertEqual(on['intent'],'on')
  self.assertEqual(gate(self.p,23,'C',2000,on)['intent'],'on')
  self.assertEqual(gate(self.p,22.4,'C',2000,on)['intent'],'off')
  self.assertEqual(gate(self.p,75.2,'F',1000)['intent'],'on')
  self.p['mode']='heat';self.assertEqual(gate(self.p,20,'C',1000)['intent'],'on')
 def test_dwell_gap_clock_and_activity(self):
  on=gate(self.p,24,'C',1000)
  self.assertEqual(gate(self.p,22,'C',1100,on)['reason'],'minimum_dwell')
  self.assertEqual(gate(self.p,24,'C',1100,on,gap=True)['intent'],'unknown')
  self.assertEqual(gate(self.p,24,'C',900,on)['reason'],'clock_rollback')
  self.assertEqual(gate(self.p,24,'C',2000,on,signal=False)['intent'],'off')
  self.assertEqual(gate(self.p,None,'C',2000,on)['intent'],'unknown')
  self.assertEqual(gate(self.p,24,'C',2000,on,eligible=False)['intent'],'off')
 def test_empty_extension_preserves_commands_and_input(self):
  original=compile_schedule(**self.b);self.flex();before=copy.deepcopy(self.b);result=compile_schedule(**self.b)
  self.assertEqual(original['events'],result['events']);self.assertEqual(before,self.b)
 def test_meal_preset_does_not_mutate_snapshot(self):
  m=self.b['plan']['meals'][0];f=self.flex();f['meals']=[{'id':m['id'],'preset':'early','duration':90,'cleanup':30}]
  old=copy.deepcopy(self.b);r=compile_schedule(**self.b);self.assertEqual(self.b,old);self.assertIn('flex',r)
 def test_replace_removes_existing_not_initial_off(self):
  f=self.flex();f['overrides']=[{'load':'room_a_hvac','mode':'unchanged'}];r=compile_schedule(**self.b)
  physical=self.b['config']['loads']['room_a_hvac']['physical_id'];self.assertFalse(any(e['physical_id']==physical for e in r['events']))
 def test_activity_uses_native_union(self):
  f=self.flex();w=self.window();w['targets']=[next(k for k,v in self.b['config']['loads'].items() if v['kind']=='binary')];f['windows']=[w]
  r=compile_schedule(**self.b);self.assertTrue(r['complete']);self.assertEqual(len(r['flex']['activities']),1)
 def test_gated_requires_replacement_and_no_fixed_on(self):
  c=self.b['config'];c['loads']['extra_hvac']={'label':{'en':'Extra HVAC','he':'מיזוג נוסף'},'physical_id':'extra_hvac','kind':'hvac_power','capabilities':{},'owner':'planner'}
  f=self.flex();w=self.window();w.update(targets=[],hvac=['extra_hvac'],policy='gated');f['windows']=[w]
  with self.assertRaises(PlanError):compile_schedule(**self.b)
  f['overrides']=[{'load':'extra_hvac','mode':'replace'}];r=compile_schedule(**self.b);self.assertEqual(len(r['flex']['conditions']),1);self.assertFalse(any(e['physical_id']=='extra_hvac' for e in r['events']))
 def test_feedback_is_bounded(self):
  self.flex()['feedback']=[{'category':'exceptional','room':'','note':'x'*2001}]
  with self.assertRaises(PlanError):compile_schedule(**self.b)
 def test_conditional_overlap_rejected(self):
  c=self.b['config'];c['loads']['extra_hvac']={'label':{'en':'Extra HVAC','he':'מיזוג נוסף'},'physical_id':'extra_hvac','kind':'hvac_power','capabilities':{},'owner':'planner'}
  f=self.flex();w=self.window();w.update(targets=[],hvac=['extra_hvac'],policy='gated');f['windows']=[w,{**copy.deepcopy(w),'id':'second'}];f['overrides']=[{'load':'extra_hvac','mode':'replace'}]
  with self.assertRaises(PlanError):compile_schedule(**self.b)
 def test_meal_bound_window_follows_cleanup_and_away(self):
  f=self.flex();m=self.b['plan']['meals'][1];w=self.window();w['category']='service';w['targets']=[next(k for k,v in self.b['config']['loads'].items() if v['kind']=='binary')];w['meal']=m['id'];f['windows']=[w];f['meals']=[{'id':m['id'],'preset':'early','duration':60,'cleanup':30}]
  r=compile_schedule(**self.b);self.assertTrue(r['complete']);self.assertEqual(r['flex']['activities'][0]['start'],m['start'])
  m['choice']='away';r=compile_schedule(**self.b);self.assertEqual(r['flex']['activities'],[])
 def test_sleep_overlap_blocks_and_explicit_allow(self):
  f=self.flex();w=self.window();use=self.b['plan']['room_uses'][0];w.update(start=use['start'],end=use['end']);w['targets']=[next(k for k,v in self.b['config']['loads'].items() if v['kind']=='binary')];f['windows']=[w]
  with self.assertRaises(PlanError):compile_schedule(**self.b)
 def test_fan_intent_is_track_only(self):
  c=self.b['config'];c['loads']['fan']={'label':{'en':'Fan','he':'מאוורר'},'physical_id':'fan','kind':'binary','capabilities':{},'owner':'planner','display':{'room':'room_a','area_type':'room','role':'fan'}}
  f=self.flex();w=self.window();w.update(category='fan',targets=['fan']);f['windows']=[w];r=compile_schedule(**self.b)
  self.assertTrue(all(e['intent']=='track_only' for e in r['events'] if e['physical_id']=='fan'))
 def test_activity_anchor_is_resolved_from_snapshot(self):
  f=self.flex();w=self.window();w['targets']=[next(k for k,v in self.b['config']['loads'].items() if v['kind']=='binary')];w['timing']={'start':{'anchor':'sunrise','offset_minutes':180},'end':{'anchor':'sunrise','offset_minutes':240}};f['windows']=[w];r=compile_schedule(**self.b)
  self.assertNotEqual(r['flex']['activities'][0]['start'],w['start']);self.assertEqual(w['start'],'2027-01-08T14:00:00+02:00')

 def test_scheduled_and_conditional_overlap_rejected(self):
  c=self.b['config'];c['loads']['extra_hvac']={'label':{'en':'Extra HVAC','he':'מיזוג נוסף'},'physical_id':'extra_hvac','kind':'hvac_power','capabilities':{},'owner':'planner'}
  f=self.flex();w=self.window();w.update(targets=[],hvac=['extra_hvac'],policy='gated');f['windows']=[w,{**copy.deepcopy(w),'id':'fixed','policy':'scheduled'}];f['overrides']=[{'load':'extra_hvac','mode':'replace'}]
  with self.assertRaises(PlanError):compile_schedule(**self.b)
