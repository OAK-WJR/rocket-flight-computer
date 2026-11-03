#!/usr/bin/env python3
"""Seeded-defect tests of the R9 ground builder and its gate (build step 8; R9_DECISIONS D-S8-*).

usage: (cd tools && <KiCad python3> -m unittest test_r9_ground)

The DRC judging and the reach percentile of m3_design/r9_ground_check.py are tested on synthetic inputs; the board
gates (table with the crystal plane and the vias' pad mode, stitch with its corridor exception, xtal, islands, reach,
copper, reference) on the built R9 board (m3_design/r9_build.sh writes
m3_design/assembly_review/m3.kicad_pcb; those tests skip while the worktree board has no step-8 pours). Each test
changes an in-memory copy and expects the gate to name the defect. Items are moved, never removed (the SWIG note of the
step-1 handoff).
"""
import sys
import unittest
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import r9_ground as RG  # noqa: E402
import r9_ground_check as G  # noqa: E402
import survey_metrics as SM  # noqa: E402

BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
MM, mm = pcbnew.FromMM, pcbnew.ToMM


def item(desc, x=1.0, y=1.0):
    return dict(description=desc, pos=dict(x=x, y=y))


class Judges(unittest.TestCase):
    def test_drc_silk_deferred_others_caught(self):
        rep = dict(violations=[dict(type='silk_overlap', items=[item('a')]),
                               dict(type='starved_thermal', items=[item('Pad 2 [GND] of C17 on B.Cu')])],
                   unconnected_items=[], schematic_parity=[])
        bad, ev = G.judge_drc(rep)
        self.assertEqual(len(bad), 1)
        self.assertIn('starved_thermal', bad[0])
        self.assertEqual(ev['deferred'], {'silk_overlap': 1})

    def test_drc_unconnected_gnd_and_parity_caught(self):
        rep = dict(violations=[], unconnected_items=[dict(items=[item('Pad 1 [GND] of TP74 on F.Cu'),
                                                                 item("Zone 'R9_GND_F' [GND] on F.Cu")])],
                   schematic_parity=[dict(type='extra_footprint', items=[item('X1')])])
        bad, _ = G.judge_drc(rep)
        self.assertTrue(any('unconnected' in b and 'TP74' in b for b in bad), bad)
        self.assertTrue(any('parity' in b for b in bad), bad)

    def test_pctl_is_the_survey_percentile(self):
        vals = [0.3, 1.0, 2.2, 2.9, 3.1, 3.4, 3.6, 7.0]
        self.assertAlmostEqual(G.pctl(vals, 0.95), SM.pctl(vals, 0.95))

    def test_table_draws_gnd_only_and_no_trims(self):
        rows = RG.read()
        self.assertTrue(rows)
        self.assertEqual({r['net'] for r in rows}, {'GND'})
        self.assertTrue({r['item'] for r in rows} <= {'via', 'track'})
        self.assertEqual({r['size'] for r in rows if r['item'] == 'via'}, {f'{RG.VIA[0]}/{RG.VIA[1]}'})


def _has_ground(path):
    if not path.is_file():
        return False
    b = pcbnew.LoadBoard(str(path))
    return any(z.GetZoneName() == 'R9_GND_F' for z in b.Zones())


@unittest.skipUnless(_has_ground(BOARD), 'the worktree board has no R9 ground (run m3_design/r9_build.sh)')
class Board(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.LoadBoard(str(BOARD))
        self.rows = [r for r in RG.read() if r['item'] == 'via']

    def table_via(self, k=0):
        q = (float(self.rows[k]['x0']), float(self.rows[k]['y0']))
        for t in self.board.GetTracks():
            if t.GetClass() == 'PCB_VIA' and abs(mm(t.GetPosition().x) - q[0]) < 1e-4 and \
                    abs(mm(t.GetPosition().y) - q[1]) < 1e-4:
                return t, q
        raise AssertionError(f'table via {q} not on the board')

    def test_built_board_gates_hold(self):
        for name, fn in (('table', G.gate_table), ('stitch', G.gate_stitch), ('islands', G.gate_islands)):
            issues, _ = fn(self.board)
            self.assertEqual(issues, [], name)

    def test_moved_table_via_caught(self):
        v, q = self.table_via()
        v.SetPosition(pcbnew.VECTOR2I(MM(q[0] + 0.3), MM(q[1])))
        issues, _ = G.gate_table(self.board)
        self.assertTrue(any(str(q) in i for i in issues), issues)

    def test_changed_pour_caught(self):
        z = [z for z in self.board.Zones() if z.GetZoneName() == 'R9_GND_B'][0]
        z.SetLocalClearance(MM(0.2))
        issues, _ = G.gate_table(self.board)
        self.assertTrue(any('R9_GND_B' in i for i in issues), issues)

    def test_via_in_a_power_pour_caught(self):
        issues, _ = G.gate_stitch(self.board, [(32.6, 70.5)])          # inside the RAW_ACT spine pours (F / B / In2)
        self.assertTrue(any('RAW_ACT' in i and 'F.Cu' in i for i in issues), issues)
        self.assertTrue(any('In2 RAW_ACT' in i for i in issues), issues)

    def test_via_near_armed_copper_caught(self):
        pad = [p for p in self.board.FindFootprintByReference('J121').Pads() if p.GetNumber() == '2'][0]
        bb = pad.GetBoundingBox()
        at = (round(mm(bb.Centre().x), 4), round(mm(bb.GetBottom()) + 0.25 + 0.6, 4))    # ring 0.6 mm off the pad
        issues, _ = G.gate_stitch(self.board, [at])
        self.assertTrue(any('PYRO1_IGN' in i for i in issues), issues)

    def test_via_too_close_to_a_gnd_via_caught(self):
        q = (float(self.rows[0]['x0']), float(self.rows[0]['y0']))
        issues, _ = G.gate_stitch(self.board, [(q[0] + 0.4, q[1])])
        self.assertTrue(any('from a GND via' in i for i in issues), issues)

    def test_stale_island_exception_caught(self):
        keep = G.WEAK_EXCEPT
        G.WEAK_EXCEPT = keep + [('F', 1.0, 1.0, 0.1, 1, 'seeded')]
        try:
            issues, _ = G.gate_islands(self.board)
        finally:
            G.WEAK_EXCEPT = keep
        self.assertTrue(any('stale' in i for i in issues), issues)

    def zone(self, name):
        return [z for z in self.board.Zones() if z.GetZoneName() == name][0]

    def test_via_keeping_unconnected_pads_caught(self):
        v, q = self.table_via()
        v.Padstack().SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL)
        issues, _ = G.gate_table(self.board)
        self.assertTrue(any('unconnected layers' in i and str(q) in i for i in issues), issues)

    def test_crystal_area_barring_fills_again_caught(self):
        self.zone(RG.XTAL_AREA).SetDoNotAllowZoneFills(True)
        issues, _ = G.gate_table(self.board)
        self.assertTrue(any(RG.XTAL_AREA in i for i in issues), issues)

    def test_crystal_plane_priority_caught(self):
        self.zone(RG.XTAL_ZONE[0]).SetAssignedPriority(9)           # under the 3V3 region: 3V3 would fill there
        issues, _ = G.gate_table(self.board)
        self.assertTrue(any(RG.XTAL_ZONE[0] in i and 'priority' in i for i in issues), issues)

    def test_crystal_plane_notch_and_outline_caught(self):
        ko, xz = self.zone(RG.XTAL_AREA), self.zone(RG.XTAL_ZONE[0])
        _, notches = RG.xtal_outline(self.board, ko)
        self.assertEqual([n[4] for n in notches], ['NRST'])          # NRST's B.Cu run to C24.1 just forward of the area
        o = xz.Outline()
        o.RemoveAllContours()
        o.NewOutline()
        for x, y in RG.outline(ko):                                  # the full rectangle: no notch under NRST
            o.Append(MM(x), MM(y))
        issues, _ = G.gate_table(self.board)
        self.assertTrue(any(RG.XTAL_ZONE[0] in i and 'outline' in i for i in issues), issues)

    def test_crystal_plane_holds_and_foreign_net_caught(self):
        issues, ev = G.gate_xtal(self.board)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(len(ev['gnd_vias']), 2)
        self.zone(RG.XTAL_ZONE[0]).SetNet(self.board.FindNet('3V3'))
        issues, _ = G.gate_xtal(self.board)
        self.assertTrue(any('not GND' in i for i in issues), issues)

    def test_stale_reference_stray_entry_caught(self):
        keep = G.REF_STRAY
        G.REF_STRAY = keep + [('QSPI_CLK', 'F.Cu', 1.0, 1.0, 'seeded')]
        try:
            issues, ev = G.gate_reference(self.board)
        finally:
            G.REF_STRAY = keep
        self.assertTrue(any('stale REF_STRAY' in i for i in issues), issues)
        self.assertLessEqual(ev['unreferenced'], G.REF_UNREF_MAX)

    def test_copper_gate_holds_and_stale_exception_caught(self):
        issues, ev = G.gate_copper(self.board)
        self.assertEqual(issues, [])
        keep = G.COPPER_EXCEPT
        G.COPPER_EXCEPT = keep + [('F', 1.0, 30.0, 9.0, 'seeded')]
        try:
            issues, _ = G.gate_copper(self.board)
        finally:
            G.COPPER_EXCEPT = keep
        self.assertTrue(any('stale copper exception' in i for i in issues), issues)

    def test_copper_gate_catches_a_lost_pad_via(self):
        # the copper-stage via that serves C121.2 (the one nearest the pad) moved 9 mm away (pours not refilled): C121's
        # GND pad is again far from any via
        pad = [p for p in self.board.FindFootprintByReference('C121').Pads() if p.GetNumber() == '2'][0]
        c = (mm(pad.GetPosition().x), mm(pad.GetPosition().y))
        k = min((k for k, r in enumerate(self.rows) if r['basis'].startswith('copper')),
                key=lambda k: (float(self.rows[k]['x0']) - c[0]) ** 2 + (float(self.rows[k]['y0']) - c[1]) ** 2)
        v, q = self.table_via(k)
        self.assertLess(((q[0] - c[0]) ** 2 + (q[1] - c[1]) ** 2) ** 0.5, 5.0)
        v.SetPosition(pcbnew.VECTOR2I(MM(q[0]), MM(q[1] - 9.0)))
        issues, _ = G.gate_copper(self.board)
        self.assertTrue(any('C121.2' in i for i in issues), issues)

    def test_corridor_exception_only_inside_its_box(self):
        box = G.A.CORRIDOR_EXCEPT['C121.2'][0]
        inside = (round((box[0] + box[2]) / 2, 4), round((box[1] + box[3]) / 2, 4))
        issues, ev = G.gate_stitch(self.board, [inside])
        self.assertFalse(any('cuts the In2 RAW_ACT' in i for i in issues), issues)
        self.assertTrue(ev['corridor_exceptions'], ev)
        issues, _ = G.gate_stitch(self.board, [(32.6, 70.5)])          # the spine, outside every exception box
        self.assertTrue(any('cuts the In2 RAW_ACT' in i for i in issues), issues)

    def test_reach_ceiling_caught(self):
        keep = G.P9_MAX
        G.P9_MAX = 1.0
        try:
            issues, ev = G.gate_reach(self.board)
        finally:
            G.P9_MAX = keep
        self.assertTrue(any('P9' in i for i in issues), issues)


if __name__ == '__main__':
    unittest.main()
