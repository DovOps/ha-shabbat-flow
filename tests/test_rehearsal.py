"""Exact-plan projections use fictional dates and never invent starting states."""
import json
from copy import deepcopy
from pathlib import Path
import unittest
from shabbat_flow.rehearsal import catalog,project,instant
from shabbat_flow.schedule import compile_schedule
from shabbat_flow.compiler import PlanError

class RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.bundle=json.loads((Path(__file__).resolve().parents[1]/'examples/period-preview.json').read_text())
        for l in self.bundle['config']['loads'].values():l['display']={'room':'room_a','role':'main_lights','area_type':'room'}
        self.bundle['config']['loads']['bath']['display']={'room':'room_b','role':'main_lights','area_type':'bathroom'}

    def test_exact_transition_and_setup_do_not_mutate_plan(self):
        original=deepcopy(self.bundle);info=catalog(self.bundle)
        events=compile_schedule(**self.bundle)['events'];at=instant(events[2]['utc']).isoformat()
        transition=project(self.bundle,at,'transition',['room_a'])
        for row in transition['rows']:
            if row['event']:self.assertEqual(instant(row['event']['utc']),instant(at))
        setup=project(self.bundle,at,'moment',['room_a'])
        for row in setup['rows']:
            prior=[e for e in events if e['physical_id']==row['physical_id'] and instant(e['utc'])<=instant(at)]
            self.assertEqual(row['event'],prior[-1] if prior else None)
        self.assertEqual(self.bundle,original)
        self.assertTrue(any('candles' in m['kinds'] for m in info['moments']))

    def test_scope_excludes_shared_bathroom_and_unknown_not_guessed(self):
        at=catalog(self.bundle)['moments'][0]['at']
        rows=project(self.bundle,at,'moment',['room_a'])['rows']
        self.assertNotIn('bath',[r['physical_id'] for r in rows])
        self.assertTrue(any(r['reason']=='rehearsal_unknown' for r in rows))
        self.assertEqual([r['physical_id'] for r in project(self.bundle,at,'moment',['room_b'])['rows']],['bath'])
        for areas in ([],['unknown'],['room_a','room_a']):
            with self.assertRaises(PlanError):project(self.bundle,at,'moment',areas)
        with self.assertRaises(PlanError):project(self.bundle,'2027-01-01T00:00:00Z','moment',['room_a'])
