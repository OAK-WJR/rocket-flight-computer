#!/usr/bin/env python3
"""Seeded-defect tests of the R9 routing families and their gate (build step 7; R9_DECISIONS D-S7-*).

usage: (cd tools && <KiCad python3> -m unittest test_r9_route)

The Draw primitives (m3_design/r9_route.py) are tested on a dry run against the built board; the DRC judge of
m3_design/r9_route_check.py on synthetic reports; the board gates (template, budget, totals) on the built R9 board
(m3_design/r9_build.sh writes m3_design/assembly_review/m3.kicad_pcb; those tests skip while the worktree board has no
family copper). Each test changes an in-memory copy or a module attribute and expects the gate to name the defect.
Items are moved off the board, never removed (the SWIG note of the step-1 handoff).
"""
import sys
import unittest
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import r9_route as RT  # noqa: E402
import r9_route_check as G  # noqa: E402

BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
_BOARD = None


def board():
    global _BOARD
    if _BOARD is None:
        _BOARD = pcbnew.LoadBoard(str(BOARD))
    return _BOARD


def built_families(b):
    """The leading families (r9_route.FAMILIES order) whose module exists and whose nets all carry copper."""
    nets = {t.GetNetname() for t in b.GetTracks()}
    out = []
    for f in RT.FAMILIES:
        if not (ROOT / f'm3_design/r9_route_{f}.py').is_file() or not set(RT.load_family(f).NETS) <= nets:
            break
        out.append(f)
    return out


class DrawPrimitives(unittest.TestCase):
    def setUp(self):
        self.d = RT.Draw(board(), 'rf_if', dry=True)

    def test_octilinear_only(self):
        with self.assertRaises(AssertionError):
            self.d.track('GNSS_TXD_MCU', 'F', RT.W, [(10.0, 10.0), (11.0, 10.5)])

    def test_zero_length(self):
        with self.assertRaises(AssertionError):
            self.d.track('GNSS_TXD_MCU', 'F', RT.W, [(10.0, 10.0), (10.0, 10.0)])

    def test_width_set(self):
        with self.assertRaises(AssertionError):
            self.d.track('GNSS_TXD_MCU', 'F', 0.22, [(10.0, 10.0), (11.0, 10.0)])

    def test_pad_position_and_net(self):
        with self.assertRaises(AssertionError):
            self.d.pad('U1', '64', 'GNSS_TXD_MCU', (17.6, 36.95))        # the table off by 0.1 mm
        with self.assertRaises(AssertionError):
            self.d.pad('U1', '64', 'GNSS_RXD_MCU', RT.u1_pin(64))        # the wrong net

    def test_two_vias_one_point(self):
        self.d.via('GND', (5.0, 30.0))
        with self.assertRaises(AssertionError):
            self.d.via('GND', (5.0, 30.0))

    def test_move_via_needs_the_via(self):
        d = RT.Draw(board(), 'rf_if', dry=False)
        with self.assertRaises(AssertionError):
            d.move_via('GND', (0.7, 0.7), (0.9, 0.9))                     # no via there

    def test_u1_pins(self):
        self.assertEqual(RT.u1_pin(1), (12.0, 52.05))
        self.assertEqual(RT.u1_pin(26), (25.55, 50.5))
        self.assertEqual(RT.u1_pin(51), (24.0, 36.95))
        self.assertEqual(RT.u1_pin(76), (10.45, 38.5))

    def test_family_owns_its_nets(self):
        fam = RT.load_family('qspi_hse')
        saved = fam.NETS
        try:
            fam.NETS = tuple(n for n in saved if n != 'HSE_OUT')         # draws a net it does not own
            with self.assertRaises(AssertionError):
                RT.build(board(), 'qspi_hse', dry=True)
            fam.NETS = saved + ('QSPI_NCS',)                             # owns a net it does not draw
            with self.assertRaises(AssertionError):
                RT.build(board(), 'qspi_hse', dry=True)
        finally:
            fam.NETS = saved


def report(violations=(), unconnected=(), parity=()):
    return dict(violations=list(violations), unconnected_items=list(unconnected), schematic_parity=list(parity))


def item(desc, x=0.0, y=0.0):
    return dict(description=desc, pos=dict(x=x, y=y))


class DrcJudge(unittest.TestCase):
    done = ('rf_if', 'qspi_hse')

    def test_pending_via_passes(self):
        x, y = RT.load_family('qspi_hse').PENDING[0]
        bad, _ = G.judge_drc(report([dict(type='via_dangling', items=[item('Via [GND] on F.Cu - B.Cu', x, y)])]),
                             self.done)
        self.assertEqual(bad, [])

    def test_other_dangling_via_fails(self):
        bad, _ = G.judge_drc(report([dict(type='via_dangling', items=[item('Via [GND] on F.Cu - B.Cu', 1.0, 1.0)])]),
                             self.done)
        self.assertTrue(bad)

    def test_unconnected_done_net_fails(self):
        u = dict(items=[item('Pad 2 [HSE_OUT] of C26 on B.Cu'), item('Via [HSE_OUT] on F.Cu - B.Cu')])
        bad, _ = G.judge_drc(report(unconnected=[u]), self.done)
        self.assertTrue(any('HSE_OUT' in b for b in bad))

    def test_joined_rail_pad_unconnected_fails(self):
        u = dict(items=[item('Pad 1 [3V3] of FB30 on F.Cu'), item('Zone [3V3] on In2.Cu')])
        bad, _ = G.judge_drc(report(unconnected=[u]), self.done)
        self.assertTrue(any('FB30.1' in b for b in bad))

    def test_later_net_and_gnd_pads_pass(self):
        u1 = dict(items=[item('Pad 1 [IMU_CS] of R11 on B.Cu'), item('Pad 93 [IMU_CS] of U1 on F.Cu')])
        u2 = dict(items=[item('Pad 2 [GND] of C26 on B.Cu'), item('Via [GND] on F.Cu - B.Cu')])
        bad, ev = G.judge_drc(report(unconnected=[u1, u2]), self.done)
        self.assertEqual(bad, [])
        self.assertEqual(ev['open_elsewhere'].get('IMU_CS'), 1)

    def test_violation_fails(self):
        v = dict(type='clearance', items=[item('Track [QSPI_CLK] on F.Cu'), item('Via [3V3] on F.Cu - B.Cu')])
        bad, _ = G.judge_drc(report([v]), self.done)
        self.assertTrue(bad)


class BoardGates(unittest.TestCase):
    def setUp(self):
        self.b = board()
        self.done = built_families(self.b)
        if not self.done or self.done[0] != 'rf_if':
            self.skipTest('the worktree board has no step-7 copper (run m3_design/r9_build.sh)')

    def test_template_clean(self):
        issues, _ = G.gate_template(self.b, self.done)
        self.assertEqual(issues, [])

    def test_template_finds_a_moved_segment(self):
        net = RT.load_family(self.done[-1]).NETS[0]
        t = next(t for t in self.b.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_TRACK')
        t.Move(pcbnew.VECTOR2I(MM(0.3), 0))
        try:
            issues, _ = G.gate_template(self.b, self.done)
            self.assertTrue(any('not on the board' in i for i in issues))
            self.assertTrue(any('no family table draws' in i for i in issues))
        finally:
            t.Move(pcbnew.VECTOR2I(MM(-0.3), 0))

    def test_template_finds_an_unmoved_fence_via(self):
        v = next(v for v in self.b.GetTracks() if v.GetClass() == 'PCB_VIA' and
                 abs(mm(v.GetPosition().x) - 17.25) < 1e-3 and abs(mm(v.GetPosition().y) - 22.2) < 1e-3)
        v.Move(pcbnew.VECTOR2I(MM(0.2), 0))                              # back on step 4's spot (17.45, 22.2)
        try:
            issues, _ = G.gate_template(self.b, self.done)
            self.assertTrue(any('which the family moved' in i for i in issues))
        finally:
            v.Move(pcbnew.VECTOR2I(MM(-0.2), 0))

    def test_budget(self):
        fam = RT.load_family(self.done[-1])
        saved = dict(fam.BUDGET)
        try:
            issues, ev = G.gate_budget(self.b, self.done[-1], [])
            self.assertEqual(issues, [])
            fam.BUDGET = dict(saved, length_mm=ev['family']['signal_track_mm'] - 1.0)
            issues, _ = G.gate_budget(self.b, self.done[-1], [])
            self.assertTrue(any('length_mm' in i for i in issues))
        finally:
            fam.BUDGET = saved

    def test_s4_total(self):
        saved = G.S4_DONE
        try:
            issues, ev = G.gate_totals(self.b, self.done, [])
            self.assertEqual(issues, [])
            G.S4_DONE = ev['board_signal_vias'] - 1
            issues, _ = G.gate_totals(self.b, self.done, [])
            self.assertTrue(issues)
        finally:
            G.S4_DONE = saved



class LinksStage(unittest.TestCase):
    """The links stage's own constraint (r9_route docstring; D-S7-17): one layer, no via, copper <= RATIO_MAX x the
    octilinear pad-to-pad distance, asserted while the family draws."""

    def test_links_hold_their_cap(self):
        d = RT.build(board(), 'links', dry=True)
        self.assertFalse(d.vias)
        self.assertEqual({layer for _, layer, *_ in d.tracks}, {'B'})

    def test_link_over_the_cap_fails(self):
        fam = RT.load_family('links')
        saved = list(fam.LINKS)
        i = next(k for k, ln in enumerate(saved) if ln[0] == 'BAT_DVDT')
        net, layer, a, c, pts = saved[i]
        (x, y0), (_, y1) = pts[0], pts[-1]
        fam.LINKS = saved[:i] + [(net, layer, a, c, [(x, y0), (x + 1.0, y0), (x + 1.0, y1), (x, y1)])] + saved[i + 1:]
        try:
            with self.assertRaisesRegex(AssertionError, 'octilinear distance'):
                RT.build(board(), 'links', dry=True)
        finally:
            fam.LINKS = saved


if __name__ == '__main__':
    unittest.main()
