import copy
import json
from pathlib import Path
import unittest

from shabbat_flow.compiler import compile_plan, PlanError, parse_instant
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


class CompilerTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'examples/household.json').read_text())
        self.plan = json.loads((ROOT / 'examples/plan.json').read_text())

    def preview(self):
        return compile_plan(self.config, self.plan)

    def error(self, code):
        with self.assertRaises(PlanError) as caught:
            self.preview()
        self.assertEqual(caught.exception.code, code)

    def test_determinism_and_locale_independence(self):
        first = self.preview()
        self.assertEqual(first, self.preview())
        self.plan['language'] = 'he'
        self.assertEqual(first, self.preview())
        self.assertTrue(first['preview_only'])

    def test_dependency_union_and_no_unused_bedroom_hvac(self):
        events = self.preview()['events']
        on = {e['load'] for e in events if e['state'] == 'on'}
        self.assertTrue({'room_a_wall','room_b_wall','shared_bath','room_a_hvac'} <= on)
        self.assertNotIn('room_b_hvac', on)
        self.plan['used_rooms'].append('room_b')
        events = self.preview()['events']
        self.assertEqual(sum(e['load']=='shared_bath' for e in events), 1)

    def test_independent_offsets(self):
        before = self.preview()['events']
        self.plan['offsets']['bedroom_hvac'] = 240
        after = self.preview()['events']
        without_bedroom = lambda es: [e for e in es if e['rule'] != 'bedroom_hvac_start']
        self.assertEqual(without_bedroom(before), without_bedroom(after))
        event = next(e for e in after if e['rule']=='bedroom_hvac_start')
        self.assertEqual(event['local'], '2027-01-08T20:20:00+02:00')

    def test_midnight_and_sunrise(self):
        events = self.preview()['events']
        midnight = next(e for e in events if e['rule']=='entry_end')
        self.assertEqual(midnight['local'], '2027-01-09T00:00:00+02:00')
        morning = next(e for e in events if e['rule']=='kitchen_morning' and e['state']=='on')
        self.assertEqual(morning['local'], '2027-01-09T08:30:00+02:00')

    def test_away_contradiction_and_valid_away(self):
        self.plan['home'] = False
        self.error('away_conflict')
        self.plan.update(used_rooms=[], dinner='away', lunch='away')
        self.assertEqual(self.preview()['events'], [])

    def test_no_shared_cooling_for_dinner_away(self):
        self.plan['dinner'] = 'away'
        self.assertFalse(any(e['rule']=='dinner_hvac_start' for e in self.preview()['events']))
        self.assertTrue(any(e['rule']=='bedroom_hvac_start' for e in self.preview()['events']))

    def test_bad_mapping(self):
        self.config['rooms']['room_a']['wall']='unknown'
        self.error('invalid_mapping')

    def test_bedroom_sleep_cutoff_only_selected_room(self):
        events=[e for e in self.preview()['events'] if e['rule']=='bedroom_lights_off']
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]['load'],'room_a_spots')
        self.assertEqual(events[0]['state'],'off')
        self.assertEqual(events[0]['local'],'2027-01-08T20:20:00+02:00')
        before=[e for e in self.preview()['events'] if e['rule']!='bedroom_lights_off']
        self.plan['offsets']['bedroom_lights']=270
        self.assertEqual(before,[e for e in self.preview()['events'] if e['rule']!='bedroom_lights_off'])

    def test_shared_resource_cannot_be_sleep_cutoff_target(self):
        self.config['rooms']['room_a']['sleep_lights']=['shared_bath']
        self.error('invalid_mapping')

    def test_empty_sleep_selection_is_supported(self):
        self.config['rooms']['room_a']['sleep_lights']=[]
        self.assertFalse(any(e['rule']=='bedroom_lights_off' for e in self.preview()['events']))

    def test_alternate_house_configuration(self):
        self.config['dependencies']=[]
        self.config['rooms']={'studio':self.config['rooms']['room_a']}
        self.plan['used_rooms']=['studio']
        self.assertFalse(any(e['load']=='shared_bath' for e in self.preview()['events']))

    def test_conflicting_roles(self):
        self.config['roles']['bedroom_hall']=['nightlights']
        self.error('event_conflict')

    def test_reject_unknown_fields_and_ids(self):
        self.plan['token']='not-a-real-token'
        self.error('invalid_schema')
        del self.plan['token']
        self.plan['used_rooms']=['unknown']
        self.error('invalid_mapping')

    def test_reject_invalid_types(self):
        for change in ({'home':1}, {'language':'fr'}, {'offsets':None}, {'schema_version':True}, {'used_rooms':['room_a','room_a']}):
            with self.subTest(change=change):
                original=copy.deepcopy(self.plan)
                self.plan.update(change)
                self.error('invalid_schema')
                self.plan=original

    def test_reject_timing_out_of_bounds(self):
        self.plan['offsets']['night_lights']=720
        self.plan['sunrise']='2027-01-09T05:00:00+02:00'
        self.error('invalid_sequence')
        self.plan['offsets']['night_lights']=360
        self.plan['offsets']['shared_hvac_off']=30
        self.error('invalid_sequence')

    def test_timezone_and_calendar_validation(self):
        for zone,code in [('Not/AZone','invalid_timezone'), ('UTC','invalid_time')]:
            with self.subTest(zone=zone):
                self.plan['timezone']=zone
                self.error(code)

    def test_multiday_and_wrong_weekday(self):
        self.plan['end']='2027-01-10T18:00:00+02:00'
        self.error('unsupported_period')
        self.plan['end']='2027-01-09T18:00:00+02:00'
        self.plan['candle_lighting']='2027-01-07T16:20:00+02:00'
        self.error('unsupported_period')

    def test_nonexistent_dst_and_naive_times_rejected(self):
        zone=ZoneInfo('Asia/Jerusalem')
        for value in ['2027-03-26T02:30:00+02:00','2027-01-08T16:20:00']:
            with self.assertRaises(PlanError):
                parse_instant(value,zone)

    def test_dst_offset_and_elapsed_math(self):
        self.plan.update(candle_lighting='2027-03-26T18:20:00+03:00',sunrise='2027-03-27T06:30:00+03:00',end='2027-03-27T19:00:00+03:00')
        e=next(e for e in self.preview()['events'] if e['rule']=='bedroom_hvac_start')
        self.assertEqual(e['utc'],'2027-03-26T20:20:00Z')
        self.assertEqual(e['local'],'2027-03-26T23:20:00+03:00')

    def test_limits(self):
        self.config['loads'].update({f'load{i}':{'en':'x','he':'י'} for i in range(101)})
        self.error('invalid_schema')


if __name__ == '__main__':
    unittest.main()
