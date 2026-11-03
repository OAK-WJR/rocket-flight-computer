#!/usr/bin/env python3
"""Seeded-defect tests of the R8 placement legaliser and gate (build step 4; R8_DECISIONS D29-D31).

usage: (cd tools && <KiCad python3> -m unittest test_r8_place)

Needs the built board (m3_design/r8_build.sh writes m3_design/assembly_review/m3.kicad_pcb). Each test moves one
part of an in-memory copy and expects the legaliser to name the broken rule; the reserved-route gate is checked with
one conflicting reservation added to a temporary copy of r8_keepclear.tsv. The legaliser sees the copper it sees in
the build (r8_pcb.py): the rigid R7 copper; the later steps' copper has its own gates (r8_power_check, r8_route_check).
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r8  # noqa: E402
import r8_legalise as L  # noqa: E402
import r8_pcb  # noqa: E402
import r8_place_check  # noqa: E402
import r8_power_check  # noqa: E402

import r8_record  # noqa: E402

# R8's board: the worktree's while it is R8's, else R8's committed project (r8_record; R9 step 3 built the R9 board)
BOARD = r8_record.board()
RIGID = set(check_r8.STRIP_PARTS) | set(check_r8.CH1_PARTS) | {'J1', 'J122'}


class Placement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = pcbnew.LoadBoard(str(BOARD))
        cls.rows = r8_pcb.read_place(r8_pcb.PLACE)
        cls.rigid = r8_power_check.rigid_items(cls.board)

    def setUp(self):
        self.model = L.Model(self.board, self.rows, copper=self.rigid)
        self.moved = []

    def tearDown(self):
        for f, pos, rot in self.moved:
            f.SetOrientationDegrees(rot)
            f.SetPosition(pos)

    def move(self, ref, x, y, rot=None):
        f = self.board.FindFootprintByReference(ref)
        self.moved.append((f, f.GetPosition(), f.GetOrientationDegrees()))
        if rot is not None:
            f.SetOrientationDegrees(rot)
        f.SetPosition(L.V(x, y))
        return self.model.violations(ref)

    def expect(self, found, text):
        self.assertTrue(any(text in v for v in found), f'{text!r} not in {found}')

    def test_table_names_exactly_the_movable_parts(self):
        refs = {f.GetReference() for f in self.board.GetFootprints()}
        self.assertEqual(set(self.rows), refs - RIGID)
        self.assertEqual(len(self.rows), 203)

    def test_built_board_is_legal(self):
        self.assertEqual(L.check(self.board, self.rows, copper=self.rigid), {})

    def test_courtyard_overlap(self):
        x, y = L.mm(self.board.FindFootprintByReference('R60').GetPosition().x), 55.3
        self.expect(self.move('R61', x, y), 'courtyard overlaps R60')

    def test_bottom_part_beside_a_through_hole_pin(self):            # R5 L10, 1.5 mm
        self.expect(self.move('C81', 38.0, 90.78, 90), 'within 1.5 mm of a through-hole pad of J121')

    def test_bare_test_pad_clearance(self):                           # 1.0 mm local pad clearance
        self.expect(self.move('TP80', 41.25, 89.6), 'closer than 1.0 mm')

    def test_rule_h_live_pad_to_sense_pad(self):                      # RAW_ACT pad 1.0 mm from RAW_ACT_SENSE pads
        found = self.move('C122', 27.4, 69.7)                     # C122.1 (RAW_ACT_SENSE) beside R177.1 (RAW_ACT)
        self.expect(found, '(RAW_ACT_SENSE) closer than 1.0 mm to R177.1 (RAW_ACT)')

    def test_reserved_route(self):      # a reservation blocks a pad: spike (d)'s strip stitch via, which step 7 has built
        with tempfile.TemporaryDirectory() as tmp:          # since (D66: r8_keepclear.tsv is empty from step 7 on)
            kc = Path(tmp) / 'r8_keepclear.tsv'
            kc.write_text('family\tnet\tlayer\tw\tx0\ty0\tx1\ty1\nd\tGND\tFB\t0.5\t22.1\t26.7\t22.1\t26.7\n')
            self.model = L.Model(self.board, self.rows, keepclear=L.read_keepclear(kc), copper=self.rigid)
        self.expect(self.move('R105', 22.53, 26.7), 'blocks the reserved')

    def test_f10_rf_separation(self):
        self.expect(self.move('C73', 36.0, 27.0), 'F10: 5.0 mm RF separation')

    def test_rf_strip_content(self):
        self.expect(self.move('R74', 33.5, 22.0, 0), 'in the RF strip')

    def test_tie_path(self):
        self.expect(self.move('TP81', 24.3, 75.7), 'J122 tie path')

    def test_support_washer(self):
        self.expect(self.move('C30', 5.0, 61.5), 'mm of M3')

    def test_rule_clearances(self):
        rc = L.rule_clearance
        self.assertEqual(rc('RAW_ACT', 'PYRO1_BUS', None, None, False, False), 1.0)        # E
        self.assertEqual(rc('RAW_ACT', 'ARM1_SENSE', 'A', 'B', True, False), 1.0)          # H (pads)
        self.assertEqual(rc('RAW_ACT', 'ARM1_SENSE', None, None, False, False), 0.5)       # A (tracks)
        self.assertEqual(rc('RAW_ACT', 'RAW_ACT_SENSE', None, None, False, False), 0.3)    # A2
        self.assertEqual(rc('PYRO1_OUT', '3V3', None, None, False, False), 0.5)            # F
        self.assertEqual(rc('GND', 'PYRO1_BUS', None, None, False, False), 0.5)            # D
        self.assertEqual(rc('PYRO1_GATE', 'PYRO1_OUT', 'Q124', 'Q124', True, True), 0.15)  # Q124's own pads
        self.assertEqual(rc('3V3', 'GND', None, None, True, False), 0.15)

    def test_reserved_gate_fires_on_a_conflicting_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            # R8's own board and project rules from git: R9 build step 2 rewrote the worktree's m3.kicad_dru, whose rule
            # G (P-1b scope) also reports R8's GATE_N via 0.22 mm from ARM1_SENSE (a recorded R8 fact,
            # r9_step1_handoff.md), which this R8 gate test is not about
            proj = Path(tmp) / 'r8'
            proj.mkdir()
            for name in ('m3.kicad_pcb', 'm3.kicad_pro', 'm3.kicad_dru'):
                (proj / name).write_bytes(subprocess.run(
                    ['git', '-C', str(ROOT), 'show', f'9c8179b:m3_design/assembly_review/{name}'],
                    capture_output=True, check=True).stdout)
            kc = Path(tmp) / 'r8_keepclear.tsv'
            shutil.copyfile(L.KEEPCLEAR, kc)
            with open(kc, 'a') as fh:      # a 3V3 lane 0.05 mm beside SERVO1's F.Cu lane (built, step 6)
                fh.write('test\t3V3\tF\t0.2\t27.25\t63.0\t27.25\t66.0\n')
            saved = L.KEEPCLEAR
            L.KEEPCLEAR = kc
            try:
                issues, _ = r8_place_check.reserved(proj / 'm3.kicad_pcb')
            finally:
                L.KEEPCLEAR = saved
        self.assertTrue(issues and all('[3V3]' in i and 'SERVO' in i for i in issues), issues)


if __name__ == '__main__':
    unittest.main()
