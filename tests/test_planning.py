import copy
from datetime import datetime, timedelta
import unittest

from shabbat_flow.compiler import PlanError
from shabbat_flow.planning import validate_calendar, validate_room_uses


def calendar_fixture(days=3, kinds=None, observance='diaspora'):
    # Illustrative supplied times/categories, not calculated holiday dates/zmanim.
    start = datetime.fromisoformat('2027-01-07T17:00:00+02:00')
    segments = []
    for i in range(days):
        evening = start + timedelta(days=i)
        segments.append({'id': f'day_{i+1}', 'kind': (kinds or ['yom_tov']*days)[i],
                         'start': evening.isoformat(),
                         'end': (evening + timedelta(days=1)).isoformat(),
                         'candle_lighting': (evening - timedelta(minutes=20) if i == 0
                                             else evening + timedelta(hours=1)).isoformat(),
                         'sunrise': (evening + timedelta(hours=13)).isoformat()})
    return {'schema_version': 2, 'period_id': 'sample_period', 'timezone': 'Asia/Jerusalem',
            'observance': observance, 'source': {'id': 'fictional_fixture', 'version': '1'},
            'preparation_start': (start - timedelta(hours=1)).isoformat(),
            'start': start.isoformat(), 'end': (start + timedelta(days=days)).isoformat(),
            'segments': segments}


def room_use(use_id='sleep', purpose='sleeping', start='2027-01-07T23:00:00+02:00',
             end='2027-01-08T08:00:00+02:00'):
    return {'id': use_id, 'room': 'room_a', 'purpose': purpose, 'control': 'planner',
            'profile': 'late' if purpose == 'sleeping' else 'leisure', 'start': start, 'end': end}


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = calendar_fixture()
        self.profiles = {'late': 'sleeping', 'leisure': 'recreation'}

    def inspect(self, uses):
        return validate_room_uses(self.snapshot, uses, ['room_a'], self.profiles)

    def test_one_two_three_day_periods_and_both_orders(self):
        for kinds in (['shabbat'], ['yom_tov', 'yom_tov'],
                      ['yom_tov', 'yom_tov', 'shabbat'], ['shabbat', 'yom_tov', 'yom_tov']):
            for observance in ('israel', 'diaspora'):
                value = validate_calendar(calendar_fixture(len(kinds), kinds, observance))
                self.assertEqual(len(value['segments']), len(kinds))

    def test_candle_anchor_can_precede_or_follow_internal_boundary(self):
        for hour in (16, 18):
            self.snapshot['segments'][1]['candle_lighting'] = f'2027-01-08T{hour}:40:00+02:00'
            validate_calendar(self.snapshot)

    def test_gap_overlap_and_missing_final_coverage_fail(self):
        for index, field, value in ((1, 'start', '2027-01-08T17:01:00+02:00'),
                                    (1, 'start', '2027-01-08T16:59:00+02:00'),
                                    (2, 'end', '2027-01-10T16:59:00+02:00')):
            broken = copy.deepcopy(self.snapshot)
            broken['segments'][index][field] = value
            with self.assertRaises(PlanError):
                validate_calendar(broken)

    def test_missing_anchor_and_unknown_fields_fail(self):
        for mode in ('missing', 'unknown'):
            broken = copy.deepcopy(self.snapshot)
            if mode == 'missing':
                del broken['segments'][2]['sunrise']
            else:
                broken['segment_hint'] = 'unexpected'
            with self.assertRaises(PlanError):
                validate_calendar(broken)

    def test_duplicate_segments_and_bad_types_fail(self):
        for change in ('duplicate', 'boolean', 'limit', 'timezone'):
            broken = copy.deepcopy(self.snapshot)
            if change == 'duplicate':
                broken['segments'][1]['id'] = 'day_1'
            elif change == 'boolean':
                broken['schema_version'] = True
            elif change == 'limit':
                broken['segments'] *= 2
            else:
                broken['timezone'] = ['invalid']
            with self.assertRaises(PlanError):
                validate_calendar(broken)

    def test_offset_and_nonexistent_dst_time_fail(self):
        for value in ('2027-01-07T16:40:00+03:00', '2027-03-26T02:30:00+02:00'):
            broken = copy.deepcopy(self.snapshot)
            broken['segments'][0]['candle_lighting'] = value
            with self.assertRaises(PlanError) as caught:
                validate_calendar(broken)
            self.assertEqual(caught.exception.code, 'invalid_time')

    def test_dst_period_does_not_assume_24_hour_day(self):
        snapshot = calendar_fixture(1)
        snapshot.update(preparation_start='2027-03-25T16:00:00+02:00',
                        start='2027-03-25T17:00:00+02:00', end='2027-03-26T17:00:00+03:00')
        snapshot['segments'][0].update(start=snapshot['start'], end=snapshot['end'],
                                      candle_lighting='2027-03-25T16:40:00+02:00',
                                      sunrise='2027-03-26T06:30:00+03:00')
        parsed = validate_calendar(snapshot)
        self.assertEqual(parsed['end'] - parsed['start'], timedelta(hours=23))

    def test_room_can_recreate_then_sleep_at_boundary(self):
        uses = [room_use(), room_use('play', 'recreation', '2027-01-07T18:00:00+02:00',
                                    '2027-01-07T23:00:00+02:00')]
        self.assertEqual(self.inspect(uses)['overlap_conflicts'], [])

    def test_overlap_is_reported_deterministically_without_mutation(self):
        uses = [room_use(), room_use('play', 'recreation', '2027-01-07T22:00:00+02:00',
                                    '2027-01-08T01:00:00+02:00')]
        before = copy.deepcopy(uses)
        result = self.inspect(uses)
        self.assertEqual(result, self.inspect(list(reversed(uses))))
        self.assertEqual(uses, before)
        self.assertEqual(result['overlap_conflicts'][0]['uses'], ['play', 'sleep'])
        self.assertEqual(result['overlap_conflicts'][0]['start'], '2027-01-07T21:00:00+00:00')

    def test_use_can_span_segment_boundary(self):
        use = room_use(start='2027-01-08T15:00:00+02:00', end='2027-01-08T18:00:00+02:00')
        self.assertEqual(self.inspect([use])['room_use_count'], 1)

    def test_existing_control_has_no_planner_profile(self):
        use = room_use()
        use.update(control='existing', profile=None)
        self.assertEqual(self.inspect([use])['overlap_conflicts'], [])
        use['profile'] = 'late'
        with self.assertRaises(PlanError):
            self.inspect([use])

    def test_unknown_room_profile_wrong_purpose_and_bounds_fail(self):
        for field, value in (('room', 'missing'), ('profile', 'missing'), ('purpose', 'recreation'),
                             ('end', '2027-01-11T08:00:00+02:00'),
                             ('start', '2027-01-06T23:00:00+02:00')):
            use = room_use()
            use[field] = value
            with self.assertRaises(PlanError):
                self.inspect([use])

    def test_duplicate_uses_and_oversize_input_fail(self):
        for uses in ([room_use(), room_use()], [room_use()]*301):
            with self.assertRaises(PlanError):
                self.inspect(uses)

    def test_no_room_use_is_valid(self):
        self.assertEqual(self.inspect([]), {'overlap_conflicts': [], 'room_use_count': 0})
