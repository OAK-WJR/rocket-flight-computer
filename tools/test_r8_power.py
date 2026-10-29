#!/usr/bin/env python3
"""Seeded-defect tests of the R8 power gate (build step 5; m3_design/r8_power_check.py, R8_DECISIONS D47-D49).

usage: (cd tools && <KiCad python3> -m unittest test_r8_power)

Needs the built board (m3_design/r8_build.sh writes m3_design/assembly_review/m3.kicad_pcb). Each test seeds one
defect into a copy of it and expects the gate to name it: a power fill under a servo lane or a CH1 pad, an inner track,
a cut power net, a stray via, a stale reservation; and the exemptions stay narrow (rigid exits, the one PENDING end).
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
import r8_power_check as G  # noqa: E402

import r8_record  # noqa: E402

# R8's board: the worktree's while it is R8's, else R8's committed project (r8_record; R9 step 3 built the R9 board)
BOARD = r8_record.board()
MM = pcbnew.FromMM


def _zone(board, net, pts, prio=50):
    z = pcbnew.ZONE(board)
    z.SetLayer(pcbnew.In2_Cu)
    z.SetNet(board.FindNet(net))
    z.SetAssignedPriority(prio)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(MM(x), MM(y))
    board.Add(z)
    return z


def _refill(board):
    for z in board.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


class PowerGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / BOARD.name
        for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
            shutil.copyfile(BOARD.with_suffix(ext), self.path.with_suffix(ext))
        self.board = pcbnew.LoadBoard(str(self.path))
        self.rows = G.keepclear_rows()

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        pcbnew.SaveBoard(str(self.path), self.board, True)

    def expect(self, issues, text):
        self.assertTrue(any(text in i for i in issues), f'{text!r} not in {issues}')

    def test_built_board_in2_and_inner_pass(self):
        self.assertEqual(G.in2(self.board, self.rows)[0], [])
        self.assertEqual(G.inner(self.board, G.rigid_items(self.board))[0], [])
        self.assertEqual(G.stale(self.path, self.rows), [])

    def test_power_fill_under_a_servo_lane(self):         # a 3V3 patch under the servo rows west of D121
        _zone(self.board, '3V3', [(26.0, 72.5), (30.0, 72.5), (30.0, 78.5), (26.0, 78.5)])
        _refill(self.board)
        issues, _ = G.in2(self.board, self.rows)
        self.assertTrue(any(('under the reserved SERVO' in i or 'under the built SERVO' in i) and 'In2 3V3' in i
                            for i in issues), issues)          # built from step 6 on (D60), reserved before
        self.expect(issues, 'In2 islands')

    def test_power_fill_under_a_ch1_pad(self):            # the J122 RAW_ACT finger stretched under C127
        _zone(self.board, 'RAW_ACT', [(22.0, 85.0), (25.0, 85.0), (25.0, 87.6), (22.0, 87.6)])
        _refill(self.board)
        self.expect(G.in2(self.board, self.rows)[0], 'In2 RAW_ACT under C127')

    def test_inner_track(self):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(MM(5.0), MM(40.0)))
        t.SetEnd(pcbnew.VECTOR2I(MM(8.0), MM(40.0)))
        t.SetWidth(MM(0.3))
        t.SetLayer(pcbnew.In2_Cu)
        t.SetNet(self.board.FindNet('3V3'))
        self.board.Add(t)
        self.expect(G.inner(self.board, G.rigid_items(self.board))[0], '3V3 track on In2.Cu')

    def test_cut_power_net_and_stray_via(self):
        cut = [t for t in self.board.GetTracks() if t.GetNetname() == 'VLOGIC' and t.GetClass() != 'PCB_VIA'
               and abs(G._xy(t.GetStart())[0] - 36.75) < 1e-3 and abs(G._xy(t.GetEnd())[0] - 36.75) < 1e-3]
        self.assertTrue(cut)
        for t in cut:                                     # VLOGIC's column x 36.75 (C99 / C6 / U2.3 / U2.2)
            self.board.Delete(t)
        v = pcbnew.PCB_VIA(self.board)                    # a lone CAM_FB via in free copper
        v.SetPosition(pcbnew.VECTOR2I(MM(3.0), MM(12.0)))
        v.SetWidth(MM(0.6))
        v.SetDrill(MM(0.3))
        v.SetNet(self.board.FindNet('CAM_FB'))
        self.board.Add(v)
        _refill(self.board)
        self.save()
        rigid = G.rigid_items(self.board)
        bad, _, open_nets = G.drc(self.path, rigid)
        self.expect(bad, 'via_dangling')
        self.expect(G.complete(self.board, rigid, open_nets)[0], 'VLOGIC')

    def test_exemptions_stay_narrow(self):
        rigid = G.rigid_items(self.board)
        self.assertTrue(G.on_items('ARM1_SENSE', (18.18, 91.3), rigid))       # a rigid exit via (step 6)
        self.assertFalse(G.on_items('ARM1_SENSE', (18.18, 80.0), rigid))      # the lane beyond it is not rigid
        self.assertTrue(G.pending('3V3A', (15.0, 62.2)))
        self.assertIsNone(G.pending('3V3', (15.0, 62.2)))
        self.assertIsNone(G.pending('3V3A', (15.0, 63.0)))

    def test_stale_reservation(self):                     # a reservation the power copper already builds
        row = dict(family='test', net='3V3', layer='F', w='0.3', x0='35.2', y0='74.0', x1='35.2', y1='82.0')
        self.expect(G.stale(self.path, self.rows + [row]), 'stale reservation test 3V3')
        row = dict(family='test', net='RAW_PROTECTED', layer='B', w='0.2', x0='1.0', y0='1.0', x1='2.0', y1='1.0')
        self.expect(G.stale(self.path, self.rows + [row]), 'stale reservation test RAW_PROTECTED')


if __name__ == '__main__':
    unittest.main()
