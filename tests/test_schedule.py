import copy
import json
from pathlib import Path
import unittest

from shabbat_flow.compiler import PlanError
from shabbat_flow.schedule import compile_schedule

ROOT = Path(__file__).resolve().parents[1]


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads((ROOT / 'examples/period-preview.json').read_text())
        self.config, self.plan = self.bundle['config'], self.bundle['plan']

    def nap(self, start='2027-01-08T14:00:00+02:00', end='2027-01-08T16:00:00+02:00'):
        return {'id':'nap_1','room':'room_a','profile':'room_a_standard','segment':'day_1',
                'start':start,'end':end,'lead_minutes':60,'bathroom_targets':[]}

    def hvac_events(self, result):
        physical=self.config['loads']['room_a_hvac']['physical_id']
        return [e for e in result['events'] if e['physical_id']==physical]

    def test_nap_only_preserves_profile_and_does_not_add_lighting(self):
        self.plan['room_uses']=[]
        baseline=self.compile()
        self.plan['naps']=[self.nap()]
        before=copy.deepcopy(self.bundle)
        result=self.compile();self.assertTrue(result['complete'])
        events=self.hvac_events(result)
        self.assertEqual([e['local'] for e in events],['2027-01-08T13:00:00+02:00','2027-01-08T16:00:00+02:00'])
        self.assertEqual(events[0]['action'],self.config['groups']['room_a_sleep_standard']['rules'][0]['action'])
        self.assertTrue(all(r['kind']=='nap' for e in events for r in e['reasons']))
        self.assertEqual([e for e in result['events'] if e not in events],baseline['events'])
        self.assertEqual(self.bundle,before)

    def test_wake_override_changes_hvac_release_not_lighting(self):
        baseline=self.compile()
        self.plan['room_uses'][0]['hvac_end']='2027-01-08T11:00:00+02:00'
        result=self.compile();physical=self.config['loads']['room_a_hvac']['physical_id']
        self.assertEqual([e for e in result['events'] if e['physical_id']!=physical],
                         [e for e in baseline['events'] if e['physical_id']!=physical])
        self.assertEqual(self.hvac_events(result)[1]['local'],'2027-01-08T11:00:00+02:00')
        self.assertEqual(self.hvac_events(result)[1]['reasons'][0]['kind'],'overnight_hvac')

    def test_wake_and_nap_union_has_no_intermediate_off(self):
        self.plan['room_uses'][0]['hvac_end']='2027-01-08T14:00:00+02:00'
        self.plan['naps']=[self.nap()]
        events=self.hvac_events(self.compile())
        self.assertEqual(events[1]['local'],'2027-01-08T16:00:00+02:00')
        self.assertEqual(len(events),6)

    def test_power_only_nap_has_no_temperature_or_mode(self):
        self.plan['room_uses']=[];self.plan['naps']=[self.nap()]
        self.config['loads']['room_a_hvac']['kind']='hvac_power'
        self.config['loads']['room_a_hvac']['capabilities']={}
        for group in self.config['groups'].values():
            for rule in group['rules']:
                if 'room_a_hvac' in rule['targets']:
                    rule['action']={'type':'hvac_power','state':'on'}
                    rule['release']={'type':'hvac_power','state':'off'}
        events=self.hvac_events(self.compile())
        self.assertEqual([e['action'] for e in events],[{'type':'hvac_power','state':'on'},{'type':'hvac_power','state':'off'}])

    def test_nap_existing_control_overlap_blocks_preview(self):
        self.plan['room_uses']=[{**self.plan['room_uses'][0], 'control':'existing','profile':None,
            'start':'2027-01-08T12:00:00+02:00','end':'2027-01-08T15:00:00+02:00'}]
        self.plan['naps']=[self.nap()]
        result=self.compile();self.assertFalse(result['complete'])
        self.assertIn('room_overlap',[i['code'] for i in result['issues']])

    def test_nap_lead_requires_home_coverage(self):
        self.plan['room_uses']=[]
        for m in self.plan['meals']:m['choice']='none'
        self.plan['availability']=[{'id':'away','start':self.plan['snapshot']['preparation_start'],'end':'2027-01-08T13:30:00+02:00','state':'away'},
            {'id':'home','start':'2027-01-08T13:30:00+02:00','end':self.plan['snapshot']['end'],'state':'home'}]
        self.plan['naps']=[self.nap()];self.fails('away_conflict')

    def test_nap_optional_shared_lights_obey_daylight_mask(self):
        self.plan['room_uses']=[];self.plan['naps']=[self.nap()]
        target='room_a_spots';self.config['loads'][target]['display']={'room':'room_b','area_type':'bathroom','role':'main_lights'}
        rule={'id':'shared_nap','targets':[target],'start':{'anchor':'use_start','offset_minutes':0},
              'end':{'anchor':'use_end','offset_minutes':0},'action':{'type':'state','state':'on'},'release':{'type':'state','state':'off'},
              'active_windows':[{'start':'2027-01-08T15:00:00+02:00','end':'2027-01-08T17:00:00+02:00'}]}
        self.config['groups']['room_a_sleep_standard']['rules'].append(rule)
        physical=self.config['loads'][target]['physical_id']
        self.assertFalse(any(e['physical_id']==physical for e in self.compile()['events']))
        self.plan['naps'][0]['bathroom_targets']=[target]
        events=[e for e in self.compile()['events'] if e['physical_id']==physical]
        self.assertEqual([e['local'] for e in events],['2027-01-08T15:00:00+02:00','2027-01-08T16:00:00+02:00'])

    def test_nap_bounds_and_wake_segment_are_validated(self):
        self.plan['naps']=[self.nap(start='2027-01-08T05:00:00+02:00')]
        self.fails('invalid_sequence')
        self.plan['naps']=[self.nap()];self.plan['naps'][0]['lead_minutes']=True;self.fails()
        self.plan['naps']=[];self.plan['room_uses'][0]['hvac_end']='2027-01-09T10:00:00+02:00'
        self.fails('invalid_sequence')

    def test_afternoon_hosting_is_opt_in_and_unions_with_lunch(self):
        baseline=self.compile()
        activity={'id':'afternoon_3','segment':'day_3','kind':'afternoon','choice':'none',
            'start':'2027-01-10T13:30:00+02:00','end':'2027-01-10T17:00:00+02:00','groups':['meal']}
        self.plan['meals'].append(activity)
        self.assertEqual(self.compile()['events'],baseline['events'])
        activity['choice']='hosting';result=self.compile();self.assertTrue(result['complete'])
        self.assertTrue(any(r['id']=='afternoon_3' for e in result['events'] for r in e['reasons']))
        physical=self.config['loads'][self.config['groups']['meal']['rules'][0]['targets'][0]]['physical_id']
        self.assertFalse(any(e['physical_id']==physical and e['local']=='2027-01-10T14:00:00+02:00' for e in result['events']))

    def test_display_metadata_does_not_change_schedule(self):
        before = self.compile()
        self.plan['snapshot']['segments'][0]['calendar_details'] = ['Example Hebrew date', 'Example weekly portion']
        load = next(iter(self.config['loads'].values()))
        load['display'] = {'room': next(iter(self.config['rooms'])), 'area_type': 'common', 'role': 'main_lights'}
        self.assertEqual(self.compile(), before)
        load['display']['area_type'] = 'invented'
        with self.assertRaises(PlanError): self.compile()
        load['display']['area_type'] = 'common'
        self.plan['snapshot']['segments'][0]['calendar_details'] = ['x' * 241]
        with self.assertRaises(PlanError): self.compile()

    def test_allowed_windows_clip_union_and_empty(self):
        group=self.config['groups']['room_a_sleep_standard']
        rule=group['rules'][0]
        rule['active_windows']=[{'start':'2027-01-07T23:00:00+02:00','end':'2027-01-08T05:00:00+02:00'}]
        before=copy.deepcopy(self.bundle)
        result=self.compile()
        target=rule['targets'][0];physical=self.config['loads'][target]['physical_id']
        events=[e for e in result['events'] if e['physical_id']==physical and any(r['group']=='room_a_sleep_standard' for r in e['reasons'])]
        assert any(e['local']=='2027-01-07T23:00:00+02:00' for e in events)
        assert any(e['local']=='2027-01-08T05:00:00+02:00' for e in events)
        self.assertEqual(self.bundle,before)
        rule['active_windows']=[]
        result=self.compile()
        assert not any(any(r['group']=='room_a_sleep_standard' and r['rule']==rule['id'] for r in e['reasons']) for e in result['events'])
        rule['active_windows']=[{'start':'2027-01-08T05:00:00+02:00','end':'2027-01-07T23:00:00+02:00'}]
        self.fails('invalid_sequence')

    def compile(self):
        return compile_schedule(self.config, self.plan)

    def fails(self, code=None):
        with self.assertRaises(PlanError) as caught:
            self.compile()
        if code:
            self.assertEqual(caught.exception.code, code)

    def test_sample_compiles_all_three_days_without_mutation(self):
        before = copy.deepcopy(self.bundle)
        result = self.compile()
        self.assertTrue(result['preview_only'] and result['complete'])
        self.assertTrue(result['events'])
        self.assertEqual({r['segment'] for e in result['events'] for r in e['reasons']},
                         {'day_1', 'day_2', 'day_3'})
        self.assertEqual(self.bundle, before)
        self.assertEqual(result, self.compile())

    def test_language_and_label_changes_do_not_change_schedule_or_digest(self):
        first = self.compile()
        self.plan['language'] = 'he'
        self.config['rooms']['room_a']['en'] = 'Another label'
        self.config['loads']['bath']['label']['en'] = 'Bathroom alias'
        self.assertEqual(first, self.compile())

    def test_unordered_selections_and_rules_are_canonical(self):
        first = self.compile()
        for field in ('room_uses', 'meals', 'groups'):
            self.plan[field].reverse()
        for group in self.config['groups'].values():
            group['rules'].reverse()
        self.assertEqual(first, self.compile())

    def test_missing_meals_and_unset_choices_produce_no_events(self):
        self.plan['meals'] = [v for v in self.plan['meals'] if v['segment'] != 'day_3']
        result = self.compile()
        self.assertFalse(result['complete'])
        self.assertEqual(result['events'], [])
        self.assertIn({'code': 'meals_missing', 'id': 'day_3'}, result['issues'])
        self.plan['availability'][0]['state'] = 'unset'
        self.plan['meals'][0]['choice'] = 'unset'
        codes = {v['code'] for v in self.compile()['issues']}
        self.assertTrue({'availability_unset', 'meal_unset'} <= codes)

    def test_explicit_no_meals_and_away_plan(self):
        self.plan['room_uses'] = []
        self.plan['groups'] = []
        self.plan['availability'][0]['state'] = 'away'
        for meal in self.plan['meals']:
            meal['choice'] = 'none'
        result = self.compile()
        self.assertTrue(result['complete'])
        self.assertEqual(result['events'], [])

    def test_home_meal_and_used_room_require_home(self):
        self.plan['availability'][0]['state'] = 'away'
        self.fails('away_conflict')
        self.plan['room_uses'] = []
        self.fails('away_conflict')

    def test_room_profiles_must_match_room_and_purpose(self):
        self.plan['room_uses'][0]['profile'] = 'room_b_standard'
        self.fails('invalid_mapping')

    def test_room_overlap_is_visible_not_silently_resolved(self):
        use = copy.deepcopy(self.plan['room_uses'][0])
        use.update(id='second_use', purpose='recreation', profile='room_a_recreation')
        self.plan['room_uses'].append(use)
        result = self.compile()
        self.assertFalse(result['complete'])
        self.assertEqual(result['events'], [])
        self.assertIn('room_overlap', {v['code'] for v in result['issues']})

    def test_shared_bathroom_is_not_released_while_other_room_needs_it(self):
        first = self.plan['room_uses'][0]
        second = copy.deepcopy(first)
        second.update(id='other_sleep', room='room_b', profile='room_b_standard',
                      end='2027-01-08T10:00:00+02:00')
        self.plan['room_uses'].append(second)
        events = [v for v in self.compile()['events'] if v['physical_id'] == 'bath']
        first_off = next(v for v in events if v['action']['state'] == 'off')
        self.assertEqual(first_off['local'], '2027-01-08T10:00:00+02:00')
        self.assertEqual(len(events[0]['reasons']), 2)

    def test_cross_day_demand_has_no_intermediate_reset(self):
        self.plan['room_uses'] = [self.plan['room_uses'][0]]
        self.plan['room_uses'][0]['end'] = '2027-01-10T08:00:00+02:00'
        events = [v for v in self.compile()['events'] if v['physical_id'] == 'bath']
        self.assertEqual(len(events), 2)
        self.assertEqual(events[-1]['local'], '2027-01-10T08:00:00+02:00')

    def test_physical_aliases_deduplicate_and_ownership_must_match(self):
        self.config['loads']['bath_alias'] = copy.deepcopy(self.config['loads']['bath'])
        rule = self.config['groups']['shared_bath']['rules'][0]
        rule['targets'].append('bath_alias')
        events = [v for v in self.compile()['events'] if v['physical_id'] == 'bath']
        self.assertEqual(len(events), 6)
        self.config['loads']['bath_alias']['owner'] = 'other_owner'
        self.fails('invalid_mapping')

    def test_point_off_cannot_override_held_shared_demand(self):
        group = self.config['groups']['shared_bath']
        group['rules'].append({'id': 'bad_cutoff', 'targets': ['bath'],
                              'start': {'anchor': 'use_start', 'offset_minutes': 30},
                              'end': None, 'action': {'type': 'state', 'state': 'off'}, 'release': None})
        self.fails('event_conflict')

    def test_hvac_validates_mode_unit_temperature_and_fan(self):
        action = self.config['groups']['room_a_sleep_standard']['rules'][0]['action']
        original = copy.deepcopy(action)
        for field, value in (('mode', 'auto'), ('unit', 'F'), ('temperature', 100),
                             ('temperature', float('nan')), ('fan_mode', 'turbo')):
            action.clear(); action.update(original); action[field] = value
            self.fails()
        action.clear(); action.update(original); action['mode'] = 'heat'
        result = self.compile()
        self.assertTrue(any(v['action'].get('mode') == 'heat' for v in result['events']))

    def test_configuration_can_add_outdoor_fixed_time_group(self):
        self.config['groups']['patio'] = {
            'label': {'en': 'Patio', 'he': 'מרפסת'}, 'track_only': False,
            'rules': [{'id': 'evening', 'targets': ['patio'],
                       'start': {'anchor': 'candle_lighting', 'offset_minutes': -20},
                       'end': {'at': '2027-01-07T23:00:00+02:00'},
                       'action': {'type': 'state', 'state': 'on'},
                       'release': {'type': 'state', 'state': 'off'}}]}
        self.plan['groups'] = [{'id': 'patio_evening', 'segment': 'day_1', 'group': 'patio',
                               'start': '2027-01-07T17:00:00+02:00', 'end': '2027-01-07T23:00:00+02:00'}]
        events = [v for v in self.compile()['events'] if v['physical_id'] == 'patio']
        self.assertEqual([v['local'] for v in events],
                         ['2027-01-07T16:20:00+02:00', '2027-01-07T23:00:00+02:00'])

    def test_track_only_has_no_set_state_intent(self):
        self.config['groups']['shared_bath']['track_only'] = True
        events = [v for v in self.compile()['events'] if v['physical_id'] == 'bath']
        self.assertTrue(events)
        self.assertTrue(all(v['intent'] == 'track_only' for v in events))

    def test_existing_control_emits_no_room_actions(self):
        for use in self.plan['room_uses']:
            use.update(control='existing', profile=None)
        self.assertFalse(any(r['kind'] == 'room_use' for v in self.compile()['events'] for r in v['reasons']))

    def test_no_arbitrary_action_even_in_unselected_group(self):
        self.config['groups']['room_b_sleep_standard']['rules'][0]['action'] = {'type': 'script', 'code': 'anything'}
        self.fails()

    def test_uncovered_times_and_missing_availability_rejected(self):
        self.config['groups']['shared_bath']['rules'][0]['start']['offset_minutes'] = -1440
        self.fails('invalid_sequence')
        self.config['groups']['shared_bath']['rules'][0]['start']['offset_minutes'] = 0
        self.plan['availability'] = []
        self.fails('invalid_sequence')

    def test_hvac_timing_changes_independently_of_lighting(self):
        first = self.compile()['events']
        rule = self.config['groups']['room_a_sleep_standard']['rules'][0]
        rule['start']['offset_minutes'] += 30
        second = self.compile()['events']
        unaffected = lambda events: [v for v in events if v['physical_id'] != 'room_a_hvac']
        self.assertEqual(unaffected(first), unaffected(second))
        before = [v['utc'] for v in first if v['physical_id'] == 'room_a_hvac' and v['action']['mode'] != 'off']
        after = [v['utc'] for v in second if v['physical_id'] == 'room_a_hvac' and v['action']['mode'] != 'off']
        self.assertNotEqual(before, after)

    def test_expansion_limit_prevents_unbounded_cross_product(self):
        group = copy.deepcopy(self.config['groups']['meal'])
        rule = group['rules'][0]
        rule['targets'] = ['dining', 'lounge', 'patio']
        group['rules'] = [{**copy.deepcopy(rule), 'id': f'rule_{i}'} for i in range(50)]
        self.config['groups']['expanded'] = group
        self.plan['groups'] = [dict(id=f'selection_{i}', segment='day_1', group='expanded',
                                   start='2027-01-07T19:00:00+02:00',
                                   end='2027-01-07T22:00:00+02:00') for i in range(100)]
        self.fails('invalid_schema')

    def power_only_fixture(self):
        for load in self.config['loads'].values():
            if load['kind'] == 'hvac':
                load['kind'], load['capabilities'] = 'hvac_power', {}
        for group in self.config['groups'].values():
            for rule in group['rules']:
                for key in ('action', 'release'):
                    action = rule[key]
                    if action and action['type'] == 'hvac':
                        rule[key] = {'type': 'hvac_power', 'state': 'off' if action['mode'] == 'off' else 'on'}

    def test_power_only_rejects_setting_overrides_and_wrong_action_types(self):
        self.power_only_fixture()
        rule = self.config['groups']['room_a_sleep_standard']['rules'][0]
        original = copy.deepcopy(rule['action'])
        for field, value in [('mode', 'heat'), ('temperature', 22), ('fan_mode', 'auto'), ('unit', 'C')]:
            rule['action'] = {**original, field: value}
            self.fails()
        rule['action'] = {'type': 'state', 'state': 'on'}
        self.fails()
        rule['action'] = original
        self.assertTrue(self.compile()['complete'])

    def test_power_only_overlapping_demands_union_and_conflicts_are_explicit(self):
        self.power_only_fixture()
        group = copy.deepcopy(self.config['groups']['room_a_sleep_standard'])
        self.config['groups']['extra_power'] = group
        original = self.compile()
        self.plan['groups'].append({'id': 'extra_power', 'segment': 'day_1', 'group': 'extra_power',
                                   'start': '2027-01-07T22:00:00+02:00', 'end': '2027-01-08T08:00:00+02:00'})
        result = self.compile()
        self.assertTrue(result['complete'])
        power = [e for e in result['events'] if e['physical_id'] == 'room_a_hvac']
        self.assertTrue(all(set(e['action']) == {'type', 'state'} for e in power))
        projection = lambda events: [(e['local'], e['action']) for e in events if e['physical_id'] == 'room_a_hvac']
        self.assertEqual(projection(original['events']), projection(result['events']))
        group['rules'][0]['action'] = {'type': 'hvac_power', 'state': 'off'}
        self.fails('event_conflict')
