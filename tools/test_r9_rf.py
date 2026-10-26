#!/usr/bin/env python3
"""Seeded-defect tests of the R9 RF strip builder and its gate (build step 4; R9_DECISIONS D-S4-*).

usage: (cd tools && <KiCad python3> -m unittest test_r9_rf)

Needs the built R9 board with the strip copper (m3_design/r9_build.sh writes m3_design/assembly_review/m3.kicad_pcb;
the tests skip while the worktree board has none). Each test changes an in-memory copy and expects the template check
or the gate to name the defect, so every gate the step leans on is shown to fire on this board's geometry. Items are
moved off the board, never removed (the SWIG note of the step-1 handoff).
"""
import collections
import sys
import unittest
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r9 as C9  # noqa: E402
import r9_rf  # noqa: E402
import r9_rf_check as G  # noqa: E402

BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
MM, mm = pcbnew.FromMM, pcbnew.ToMM


def _has_strip(path):
    """The strip's copper is on the board: its F.Cu GND pour by step 4's name, or by step 8's (r9_ground grows it)."""
    return path.is_file() and (b'R9_GND_F_strip' in path.read_bytes() or b'"R9_GND_F"' in path.read_bytes())


@unittest.skipUnless(_has_strip(BOARD), 'the worktree board has no R9 strip copper (run m3_design/r9_build.sh)')
class Strip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r7, cls._keep = G.r7_board()
        cls.board = pcbnew.LoadBoard(str(BOARD))
        cls.fps = {f.GetReference(): f for f in cls.board.GetFootprints()}

    def setUp(self):
        self.undo = []

    def tearDown(self):
        for fn in reversed(self.undo):
            fn()

    def shift(self, ref, dx, dy=0.0):
        f = self.fps[ref]
        p = f.GetPosition()
        f.SetPosition(pcbnew.VECTOR2I(p.x + MM(dx), p.y + MM(dy)))
        self.undo.append(lambda: f.SetPosition(p))

    def add_via(self, x, y, net='GND', size=(0.6, 0.3)):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(size[0]))
        v.SetDrill(MM(size[1]))
        v.SetNet(self.board.FindNet(net))
        self.board.Add(v)
        self.undo.append(lambda: v.SetPosition(pcbnew.VECTOR2I(MM(500), MM(500))))     # off the board
        return v

    def add_track(self, net, a, c, layer=pcbnew.F_Cu, w=0.2):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
        t.SetWidth(MM(w))
        t.SetLayer(layer)
        t.SetNet(self.board.FindNet(net))
        self.board.Add(t)
        self.undo.append(lambda: (t.SetStart(pcbnew.VECTOR2I(MM(500), MM(500))),
                                  t.SetEnd(pcbnew.VECTOR2I(MM(501), MM(500)))))
        return t

    def expect(self, issues, text):
        self.assertTrue(any(text in i for i in issues), f'{text!r} not in {issues[:6]}')

    # --- templates ---------------------------------------------------------------------------------------------------
    def test_frames_hold_on_the_built_board(self):
        issues, ev = G.gate_frames(self.board)
        self.assertEqual(issues, [])
        self.assertEqual(set(ev['origins']), set(r9_rf.FRAME_ROT))

    def test_a_moved_chain_part_is_refused(self):
        self.shift('C303', 0.1)
        issues, _ = G.gate_frames(self.board)
        self.expect(issues, 'C303')

    def test_a_jack_off_its_module_pin_is_refused(self):
        self.shift('J30', 0.1)
        issues, _ = G.gate_frames(self.board)
        self.expect(issues, 'U30.11')

    def test_the_drawn_nets_are_the_strip_nets(self):
        # the step's own tables (later steps draw other nets on the same board, step 5 first: R9_DECISIONS D-S5-07)
        drawn = {net for _, net, *_ in r9_rf.GNSS_RF + r9_rf.RADIO_RF + r9_rf.U30_COPPER + r9_rf.LIMITER +
                 r9_rf.U31_COPPER} - {'GND'}
        self.assertEqual(drawn, set(r9_rf.strip_nets(self.board)))
        on_board = {t.GetNetname() for t in self.board.GetTracks()}
        self.assertEqual(drawn - on_board, set())
        self.assertIn('RADIO_TXEN', drawn)
        self.assertNotIn('GNSS_RXD', drawn)              # an interface net that crosses y_f: step 7's

    # --- R7 congruence and the launches -------------------------------------------------------------------------------
    def test_r7_congruence_holds_with_the_recorded_deviations(self):
        issues, ev = G.gate_r7(self.board, self.r7, r9_rf.Frames(self.board))
        self.assertEqual(issues, [])
        self.assertEqual({r for r, v in ev.items() if v['deviation']}, set(r9_rf.R7_DEVIATIONS))

    def test_an_undeclared_chain_change_fails_r7(self):
        self.shift('L30', 0.05)
        frames = r9_rf.Frames(self.board)
        issues, _ = G.gate_r7(self.board, self.r7, frames)
        self.expect(issues, 'L30')

    def test_a_stale_deviation_fails_r7(self):
        r9_rf.R7_DEVIATIONS['R304'] = 'test'
        self.undo.append(lambda: r9_rf.R7_DEVIATIONS.pop('R304'))
        issues, _ = G.gate_r7(self.board, self.r7, r9_rf.Frames(self.board))
        self.expect(issues, 'R304 is R7\'s')

    def test_launches_equal_r7(self):
        issues, ev = G.gate_launch(self.board, self.r7, r9_rf.Frames(self.board))
        self.assertEqual(issues, [])
        self.assertLessEqual(ev['J30_vs_J31_mm2'], G.LAUNCH_XOR_MAX)

    def test_an_extra_launch_via_fails(self):
        x = r9_rf.Frames(self.board).origin['J30'][0]
        self.add_via(x + 1.7, 1.65)
        issues, _ = G.gate_launch(self.board, self.r7, r9_rf.Frames(self.board))
        self.expect(issues, 'J30: GND vias in the launch window')

    def test_foreign_copper_in_a_launch_fails(self):
        x = r9_rf.Frames(self.board).origin['J31'][0]
        self.add_via(x - 1.7, 2.9, net='GNSS_LNA_EN', size=(0.5, 0.3))
        issues, _ = G.gate_launch(self.board, self.r7, r9_rf.Frames(self.board))
        self.expect(issues, 'J31: foreign copper')

    # --- GCPW, corridors, contract ------------------------------------------------------------------------------------
    def test_gcpw_judges_each_gap_pair(self):
        ok, z, _ = G.judge_pairs(collections.Counter({(0.25, 0.25): 3, (0.25, 0.31): 1}))
        self.assertEqual(ok, [])
        self.assertTrue(all(abs(v - G.Z_NOM) <= G.Z_TOL for v in z.values()))
        bad, _, worst = G.judge_pairs(collections.Counter({(0.9, 0.9): 1}))
        self.expect(bad, 'gaps (0.9, 0.9)')
        self.assertGreater(worst[0], G.Z_NOM + G.Z_TOL)

    def test_line_samples_cover_both_chains(self):
        samples = G.line_samples(self.board)
        self.assertEqual({s[0] for s in samples}, {'GNSS', 'RADIO'})
        self.assertTrue(all(C9.GAP_LO * C9.GCPW_SCAN - 1e-9 <= min(s[4], s[5]) for s in samples))

    def test_a_via_in_a_lane_corridor_fails(self):
        x0, y0, x1, y1, lanes = r9_rf.corridor_boxes(r9_rf.Frames(self.board))[0]
        self.add_via((x0 + x1) / 2, (y0 + y1) / 2)
        issues, _ = G.gate_corridors(self.board, r9_rf.Frames(self.board))
        self.expect(issues, lanes)

    def test_bcu_copper_may_cross_a_corridor(self):
        x0, y0, x1, y1, _ = r9_rf.corridor_boxes(r9_rf.Frames(self.board))[0]
        before, _ = G.gate_corridors(self.board, r9_rf.Frames(self.board))   # step 7's rf_if lanes on a built board
        self.add_track('GNSS_ANT_GATE', ((x0 + x1) / 2, y0 + 0.1), ((x0 + x1) / 2, y1 - 0.1), layer=pcbnew.B_Cu)
        issues, _ = G.gate_corridors(self.board, r9_rf.Frames(self.board))
        self.assertEqual(issues, before)

    def test_contract_rules_hold(self):
        res = C9.check_board(self.board, BOARD.parent, BOARD, only=set(G.CONTRACT_RULES))
        self.assertEqual(res['issues'], [])

    def test_a_missing_stitch_fails_r7(self):
        frames = r9_rf.Frames(self.board)
        x, y = frames.at('J30', -0.79, 6.9)                       # the GNSS west stitch at the pi row
        via = next(t for t in self.board.GetTracks() if t.GetClass() == 'PCB_VIA' and
                   abs(mm(t.GetPosition().x) - x) < 1e-3 and abs(mm(t.GetPosition().y) - y) < 1e-3)
        p = via.GetPosition()
        via.SetPosition(pcbnew.VECTOR2I(MM(500), MM(500)))
        self.undo.append(lambda: via.SetPosition(p))
        issues, _ = C9.r7_rule(C9.Ctx(self.board))
        self.expect(issues, 'GND stitching gap')


if __name__ == '__main__':
    unittest.main()
