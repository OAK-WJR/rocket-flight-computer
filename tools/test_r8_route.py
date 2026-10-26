#!/usr/bin/env python3
"""Seeded-defect tests of the R8 signal-family build and gate (build step 6; m3_design/r8_route.py,
r8_route_check.py, R8_DECISIONS D51-D60).

usage: (cd tools && <KiCad python3> -m unittest test_r8_route)

Needs the built board (m3_design/r8_build.sh writes m3_design/assembly_review/m3.kicad_pcb). Each test seeds one defect
and expects the primitive or the gate to refuse it: an off-angle, zero-length or doubled item, a pad the table misplaces,
a family run twice, a link over the plan's ratio, a family over its budget, an open GND after imu, a stale reservation.
The DRC-backed gates (drc, complete, route, reserved) run in r8_build.sh on the real board.
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import r8_route as R  # noqa: E402
import r8_route_check as G  # noqa: E402
import r8_route_links as LINKS  # noqa: E402

import r8_record  # noqa: E402

# R8's board: the worktree's while it is R8's, else R8's committed project (r8_record; R9 step 3 built the R9 board)
BOARD = r8_record.board()


class Primitives(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / BOARD.name
        for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
            shutil.copyfile(BOARD.with_suffix(ext), self.path.with_suffix(ext))
        self.board = pcbnew.LoadBoard(str(self.path))
        self.d = R.Draw(self.board, 'test')

    def tearDown(self):
        self.tmp.cleanup()

    def test_geometry_helpers(self):
        self.assertTrue(R.octilinear((0, 0), (1, 1)))
        self.assertTrue(R.octilinear((0, 0), (0, 2)))
        self.assertFalse(R.octilinear((0, 0), (1, 0.5)))
        self.assertAlmostEqual(R.octile((0, 0), (3, 1)), 3 + (2 ** 0.5 - 1))

    def test_track_refuses_off_angle_and_zero_length(self):
        with self.assertRaises(AssertionError):
            self.d.track('GND', 'F', 0.2, [(1.0, 1.0), (2.0, 1.5)])
        with self.assertRaises(AssertionError):
            self.d.track('GND', 'F', 0.2, [(1.0, 1.0), (1.0, 1.0)])

    def test_via_refuses_a_second_via_at_one_point(self):
        self.d.via('GND', 1.0, 1.0)
        with self.assertRaises(AssertionError):
            self.d.via('GND', 1.0, 1.0)

    def test_pad_assumption_is_checked(self):
        self.assertEqual(self.d.pad('U12', '4', 'CAM_MCU_RX', (34.45, 44.0)), (34.45, 44.0))
        with self.assertRaises(AssertionError):
            self.d.pad('U12', '4', 'CAM_MCU_RX', (34.6, 44.0))       # a placement change moved it
        with self.assertRaises(AssertionError):
            self.d.pad('U12', '4', 'CAM_MCU_TX')                     # wrong net

    def test_family_runs_once(self):
        with self.assertRaises(AssertionError):
            R.check_input(self.board, R.load_family('links'))       # its nets carry copper already

    def test_link_over_the_plan_ratio_fails(self):
        saved = LINKS.LINKS
        try:
            LINKS.LINKS = [('LOGIC_ILIM', 'B', ('U11', '10'), ('R86', '1'),
                            [(36.75, 58.35), (36.75, 57.35), (38.125, 57.35), (38.125, 58.35)])]   # 1.73 x
            with self.assertRaises(AssertionError):
                LINKS.draw(self.d)
        finally:
            LINKS.LINKS = saved


class GateLogic(unittest.TestCase):
    def test_gnd_must_be_whole_from_imu_on(self):
        nets = {'SPI1_SCK'}
        issues, _ = G.complete({'GND': 1}, nets, False, 'usb_swd')
        self.assertEqual(issues, [])                                 # the sensors' GND pads wait for imu
        issues, _ = G.complete({'GND': 1}, nets, False, 'imu')
        self.assertTrue(any(i.startswith('GND') for i in issues))
        issues, _ = G.complete({'GND': 1}, nets, False, 'camera')
        self.assertTrue(any(i.startswith('GND') for i in issues))

    def test_done_net_must_be_complete(self):
        issues, _ = G.complete({'CAM_MCU_RX': 1}, {'CAM_MCU_RX'}, False, 'camera')
        self.assertTrue(issues)

    def test_budget_overrun_is_named(self):
        fam = R.load_family('camera')
        fig = dict(signal_track_mm=fam.BUDGET['length_mm'] + 1, signal_vias=fam.BUDGET['vias'],
                   critical_layer_changes=0, worst_ratio=1.0)
        self.assertTrue(any('length_mm' in i for i in G.budget(fam, fig)))
        fig.update(signal_track_mm=1.0, signal_vias=fam.BUDGET['vias'] + 1)
        self.assertTrue(any('vias' in i for i in G.budget(fam, fig)))

    def test_stale_reservation_is_named(self):
        rows = [dict(family='s5', net='LOGIC_SOURCE_ST'), dict(family='d', net='GND')]
        self.assertTrue(G.stale(rows, G.family_nets(R.FAMILIES)))
        self.assertFalse(G.stale(rows[1:], G.family_nets(R.FAMILIES)))   # step 7's GND rows stay

    def test_l10_names_a_bottom_part_beside_a_pyro_via(self):
        board = pcbnew.LoadBoard(str(BOARD))
        self.assertEqual(G.l10(board)[0], [])
        f = board.FindFootprintByReference('R163')                     # a bottom part, moved beside GATE_N's dive
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(17.6), pcbnew.FromMM(55.5)))
        self.assertTrue(any('R163' in i and 'PYRO1_GATE_N' in i for i in G.l10(board)[0]))

    def test_build_order_is_the_family_order(self):
        text = (ROOT / 'm3_design/r8_build.sh').read_text()
        self.assertIn('for FAMILY in ' + ' '.join(R.FAMILIES) + ';', text)


if __name__ == '__main__':
    unittest.main()
