"""Guarded CAD replay: corrupted or partial geometry must never be overwritten."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
from r5_scoped_patch import apply_delta


def track(uid, x=1, width='.2', net='GND'):
    return f'(segment (start {x} 1) (end {x} 2) (width {width}) (layer "B.Cu") (net "{net}") (uuid "{uid}"))'


def board(*objects):
    return '(kicad_pcb\n' + '\n'.join(objects) + '\n)'


class ScopedReplayTests(unittest.TestCase):
    def setUp(self):
        self.old = track('old')
        self.new = track('new', 2)
        self.unrelated = track('untouched', 20, net='3V3')
        self.delta = {'before': [self.old], 'after': [self.new]}
        self.source = board(self.old, self.unrelated)

    def test_apply_preserves_unrelated_text_and_repeats_without_changes(self):
        result = apply_delta(self.source, self.delta)
        self.assertIn(self.unrelated, result)
        self.assertIn(self.new, result)
        self.assertNotIn(self.old, result)
        self.assertEqual(result, apply_delta(result, self.delta))

    def test_generated_source_uuid_is_allowed(self):
        result = apply_delta(self.source.replace('"old"', '"regenerated"'), self.delta)
        self.assertIn(self.new, result)

    def test_changed_preimage_is_rejected(self):
        for changed in (track('old', 1.001), track('old', width='.201'), track('old', net='3V3')):
            with self.subTest(changed=changed), self.assertRaises(RuntimeError):
                apply_delta(board(changed, self.unrelated), self.delta)

    def test_changed_postimage_is_rejected(self):
        with self.assertRaises(RuntimeError):
            apply_delta(board(track('new', 2.001), self.unrelated), self.delta)

    def test_missing_preimage_is_rejected(self):
        with self.assertRaises(RuntimeError):
            apply_delta(board(self.unrelated), self.delta)

    def test_duplicate_preimage_is_rejected(self):
        with self.assertRaises(RuntimeError):
            apply_delta(board(self.old, track('duplicate'), self.unrelated), self.delta)

    def test_duplicate_postimage_is_rejected(self):
        with self.assertRaises(RuntimeError):
            apply_delta(board(self.new, track('duplicate', 2), self.unrelated), self.delta)

    def test_mixed_states_are_rejected(self):
        with self.assertRaises(RuntimeError):
            apply_delta(board(self.old, self.new, self.unrelated), self.delta)

    def test_new_uuid_collision_is_rejected(self):
        with self.assertRaises(RuntimeError):
            apply_delta(board(self.old, track('new', 20)), self.delta)

    def test_partial_multi_object_repair_is_rejected(self):
        data = {'before': [self.old, track('second', 3)], 'after': [self.new, track('fourth', 4)]}
        for objects in ((self.old,), (self.new,), (self.old, track('fourth', 4))):
            with self.subTest(objects=objects), self.assertRaises(RuntimeError):
                apply_delta(board(*objects), data)

    def test_pure_add_is_idempotent_and_partial_add_is_rejected(self):
        zones = [f'(zone (layer "B.Cu") (uuid "zone-{i}") (name "guard-{i}") (keepout (tracks not_allowed)))' for i in range(2)]
        data = {'before': [], 'after': zones}
        result = apply_delta(board(self.unrelated), data)
        self.assertEqual(result, apply_delta(result, data))
        for zone in zones:
            with self.subTest(zone=zone), self.assertRaises(RuntimeError):
                apply_delta(board(self.unrelated, zone), data)

    def test_silkscreen_replacement_rejects_modified_legend(self):
        old = '(gr_text "SW" (at 1 2) (layer "F.SilkS") (uuid "legend"))'
        new = '(gr_text "J1 SW 3-4" (at 2 3) (layer "B.SilkS") (uuid "legend"))'
        data = {'before': [old], 'after': [new]}
        result = apply_delta(board(old, self.unrelated), data)
        self.assertIn(new, result)
        self.assertEqual(result, apply_delta(result, data))
        with self.assertRaises(RuntimeError):
            apply_delta(board(old.replace('"SW"', '"BAT"'), self.unrelated), data)

    def test_current_native_project_has_all_recorded_scoped_repairs(self):
        text = (ROOT / 'm3_design/assembly_review/m3.kicad_pcb').read_text()
        data = json.loads((ROOT / 'm3_design/r5_repair.json').read_text())
        for name, delta in data['scoped_repairs'].items():
            with self.subTest(stage=name):
                self.assertEqual(text, apply_delta(text, delta))


if __name__ == '__main__':
    unittest.main()
