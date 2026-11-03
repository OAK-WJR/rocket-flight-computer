#!/usr/bin/env python3
"""Seeded-defect tests of the R9 power builder and its gate (build step 6; R9_DECISIONS D-S6-*).

usage: (cd tools && <KiCad python3> -m unittest test_r9_power)

The judging functions of m3_design/r9_power_check.py (DC rows, the hot-plug result, the DRC report, the pending-copper
chains) are tested on synthetic inputs; the board gates (template, In2) on the built R9 board
(m3_design/r9_build.sh writes m3_design/assembly_review/m3.kicad_pcb; those tests skip while the worktree board has
no power copper). Each test changes an in-memory copy and expects the gate to name the defect. Items are moved off
the board, never removed (the SWIG note of the step-1 handoff).
"""
import copy
import sys
import unittest
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import r9_power as RP  # noqa: E402
import r9_power_check as G  # noqa: E402

BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
SHA = 'a' * 64
DC_TEXT = """./src/common/stdpbase.cpp(59): assert ""traits"" failed in Get(): create wxApp before calling this
board /x/m3.kicad_pcb sha256 {sha}
RAW_ACT: Q121:5,6,7,8,9 -> J122:2,5,8,11, grid 0.1 mm, 52877 free cells, CG 1572 iterations, residual 9.9e-11
  R = {mohm} mOhm; at 7.7 A: drop 6.1 mV, copper loss 0.047 W
  vias: 31 carry current; largest barrel currents at 7.7 A: {via} A at (32.2, 78.2) (In2.Cu-B.Cu), 0.46 A at (31.0, 78.)
  vias over 0.5 A: 0; over 1.0 A: {over}
  IPC-2152 (no plane credit): neck 7.82 mm on B.Cu rises {rise} C at 7.7 A; 20 C needs 5.28 mm there
"""


def dc(mohm=0.79, rise=12.7, via=0.46, over=0, sha=SHA):
    return G.parse_dc(DC_TEXT.format(mohm=mohm, rise=rise, via=via, over=over, sha=sha))


def good_rows():
    return {'raw': dc(), 'bat': dc(0.17, 12.1, 0.65), 'fet': dc(0.27, 20.8, 0.25)}


class Judges(unittest.TestCase):
    def test_parse_dc(self):
        r = dc()
        self.assertEqual((r['mohm'], r['rise_c'], r['via_max_a'], r['vias_over_1a'], r['sha']),
                         (0.79, 12.7, 0.46, 0, SHA))

    def test_dc_good_rows_pass(self):
        self.assertEqual(G.judge_dc(good_rows(), SHA), [])

    def test_dc_rise_over_r8_caught(self):
        rows = good_rows()
        rows['fet'] = dc(0.27, 22.9, 0.25)                 # under D12's 30 C, over R8's 22.3 C
        issues = G.judge_dc(rows, SHA)
        self.assertTrue(any('R8' in i and 'fet' in i for i in issues), issues)
        self.assertFalse(any('D12' in i for i in issues), issues)

    def test_dc_d12_caught(self):
        rows = good_rows()
        rows['raw'] = dc(0.79, 21.0)
        self.assertTrue(any('D12' in i for i in G.judge_dc(rows, SHA)))

    def test_dc_raw_resistance_caught(self):
        rows = good_rows()
        rows['raw'] = dc(1.2, 12.7)
        self.assertTrue(any('D_raw' in i for i in G.judge_dc(rows, SHA)))

    def test_dc_via_current_caught(self):
        rows = good_rows()
        rows['bat'] = dc(0.17, 12.1, 1.05, 1)
        issues = G.judge_dc(rows, SHA)
        self.assertTrue(any('via barrel' in i for i in issues) and any('over 1.0 A' in i for i in issues), issues)

    def test_dc_unbound_or_missing_solve_caught(self):
        rows = good_rows()
        rows['bat'] = dc(sha='b' * 64)
        self.assertTrue(any('not bound' in i for i in G.judge_dc(rows, SHA)))
        rows = good_rows()
        rows['fet'] = None
        self.assertTrue(any('fet solve failed' in i for i in G.judge_dc(rows, SHA)))

    def test_f9_judging(self):
        res = dict(feed_estimate_nH=3.2, by_feed_nH={'3.2': dict(extra_negative_V=0.002, slew_ratio=1.03),
                                                       '5.0': dict(extra_negative_V=0.004, slew_ratio=1.04),
                                                       '15.0': dict(extra_negative_V=0.02, slew_ratio=1.08)})
        self.assertEqual(G.judge_f9(res), [])                # 15 nH is past R8's 5 nH bound: reported, not gated
        bad = copy.deepcopy(res)
        bad['by_feed_nH']['5.0']['slew_ratio'] = 1.06
        self.assertTrue(G.judge_f9(bad))
        bad = copy.deepcopy(res)
        bad['by_feed_nH']['3.2']['extra_negative_V'] = 0.02
        self.assertTrue(G.judge_f9(bad))
        bad = copy.deepcopy(res)
        bad['feed_estimate_nH'] = 6.0
        self.assertTrue(any('estimate' in i for i in G.judge_f9(bad)))

    def drc_report(self, violations=(), unconnected=(), parity=()):
        return dict(violations=list(violations), unconnected_items=list(unconnected), schematic_parity=list(parity))

    @staticmethod
    def item(desc, x=0.0, y=0.0):
        return dict(description=desc, pos=dict(x=x, y=y))

    def test_drc_pending_via_allowed_other_dangling_caught(self):
        x, y = RP.PENDING[0]
        ok = self.drc_report([dict(type='via_dangling', items=[self.item('Via [GND] on F.Cu - B.Cu', x, y)])])
        self.assertEqual(G.judge_drc(ok)[0], [])
        bad = self.drc_report([dict(type='via_dangling', items=[self.item('Via [GND] on F.Cu - B.Cu', x + 1, y)])])
        self.assertTrue(G.judge_drc(bad)[0])
        bad = self.drc_report([dict(type='clearance', items=[self.item('Track [RAW_ACT] on F.Cu'),
                                                              self.item('Track [ARM1_SENSE] on F.Cu')])])
        self.assertTrue(G.judge_drc(bad)[0])

    def test_drc_silk_deferred_parity_caught(self):
        ok = self.drc_report([dict(type='silk_overlap', items=[self.item('Reference field of C1')])])
        self.assertEqual(G.judge_drc(ok)[0], [])
        bad = self.drc_report(parity=[dict(type='missing_footprint', items=[self.item('R999')])])
        self.assertTrue(G.judge_drc(bad)[0])

    def test_drc_unconnected_step_net_caught(self):
        bad = self.drc_report(unconnected=[dict(items=[self.item('Pad 2 [RAW_PROTECTED] of R122 on B.Cu'),
                                                       self.item('Via [RAW_PROTECTED] on F.Cu - B.Cu')])])
        self.assertTrue(G.judge_drc(bad)[0])

    def test_drc_partial_nets(self):
        ok = self.drc_report(unconnected=[dict(items=[self.item('Pad 1 [RAW_ACT] of R177 on B.Cu'),
                                                      self.item("Zone 'R9_RAW_ACT_B' [RAW_ACT] on B.Cu")])])
        issues, ev = G.judge_drc(ok)
        self.assertEqual(issues, [])
        self.assertEqual(ev['partial_left'], {'RAW_ACT': ['R177.1']})
        bad = self.drc_report(unconnected=[dict(items=[self.item('Pad 2 [RAW_ACT] of J122 on F.Cu'),
                                                       self.item("Zone 'R9_RAW_ACT_B' [RAW_ACT] on B.Cu")])])
        self.assertTrue(G.judge_drc(bad)[0])

    def test_chains(self):
        segs = [((0, 0), (1, 0)), ((1, 0), (1, 1)), ((5, 5), (6, 5))]
        self.assertEqual(G.chains(segs, [(0, 0)]), segs[:2])
        self.assertEqual(G.chains(segs, [(9, 9)]), [])

    def test_tables(self):
        """The template's tables use the board's widths and via sizes only, every polyline octilinear."""
        widths = {round(w, 3) for _, w, _ in RP.RP_TRACKS} | {round(w, 3) for _, _, w, _ in RP.LOGIC_TRACKS} | \
            {round(w, 3) for _, _, w, _ in RP.CAMERA_TRACKS} | {round(w, 3) for _, w, _ in RP.GND_TRACKS}
        self.assertLessEqual(widths, {0.15, 0.2, 0.25, 0.3, 0.4, 1.0})
        for table in (RP.RP_TRACKS, RP.GND_TRACKS):
            for row in table:
                pts = row[-1]
                for a, c in zip(pts, pts[1:]):
                    self.assertTrue(RP.octilinear(a, c), (a, c))
        self.assertFalse(set(RP.NETS) & set(RP.PARTIAL))


def _has_power(path):
    if not path.is_file():
        return False
    return b'R9_RAW_PROTECTED_F' in path.read_bytes()


def continued_extras(b):
    """The template's 'extra' items a later board legitimately carries: the copper each drawn step-7 family's table adds
    to a PARTIAL net it CONTINUES (r9_route; R9_DECISIONS D-S7-08). r9_power_check stays a step-6 gate (it runs on the
    step-6 board in the build, step-6 handoff section 4), so the test, not the gate, expects exactly these items."""
    import r9_route as RT
    nets = {t.GetNetname() for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK'}
    out = []
    for f in RT.FAMILIES:
        if not (ROOT / 'm3_design' / f'r9_route_{f}.py').is_file():
            continue
        fam = RT.load_family(f)
        cont = set(getattr(fam, 'CONTINUES', ())) & set(RP.PARTIAL)
        if not cont or not set(fam.NETS) <= nets:
            continue
        d = RT.build(b, f, dry=True)
        for k in (G.seg_key(*t) for t in d.tracks if t[0] in cont):
            out.append(f'template: extra {k[0]} {k[1]} w{k[2]} {k[3]}')
        out += [f'template: extra via {(net, at, d.via_size[at])}' for at, net in d.vias.items() if net in cont]
    return sorted(out)


@unittest.skipUnless(_has_power(BOARD), 'the worktree board has no R9 power copper (run m3_design/r9_build.sh)')
class Board(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.LoadBoard(str(BOARD))
        self.fps = {f.GetReference(): f for f in self.board.GetFootprints()}

    def add_track(self, net, a, c, layer=pcbnew.B_Cu, w=0.3):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
        t.SetWidth(MM(w))
        t.SetLayer(layer)
        t.SetNet(self.board.FindNet(net))
        self.board.Add(t)
        return t

    def test_built_board_template_and_in2_hold(self):
        # on a step-7 board: exactly the continuing families' table copper on the PARTIAL nets, nothing else
        self.assertEqual(sorted(G.gate_template(self.board)[0]), continued_extras(self.board))
        self.assertEqual(G.gate_in2(self.board)[0], [])

    def test_moved_part_stops_the_template(self):
        f = self.fps['U2']
        p = f.GetPosition()
        f.SetPosition(pcbnew.VECTOR2I(p.x + MM(0.2), p.y))
        with self.assertRaises(AssertionError) as cm:
            RP.Pads(self.board)
        self.assertIn('U2', str(cm.exception))

    def test_extra_copper_on_a_step_net_caught(self):
        self.add_track('RAW_PROTECTED', (43.0, 60.0), (43.0, 61.0), pcbnew.F_Cu)
        self.assertTrue(any('extra RAW_PROTECTED' in i for i in G.gate_template(self.board)[0]))

    def test_partial_net_copper_beyond_the_continuing_table_caught(self):
        # the expected items are the continuing table's own; other copper on a PARTIAL net is still named
        before = continued_extras(self.board)
        self.add_track('RAW_ACT', (27.45, 58.6), (27.45, 59.4), pcbnew.B_Cu, w=0.2)   # beside pyro's tap, not its table
        new = sorted(set(G.gate_template(self.board)[0]) - set(before))
        self.assertEqual(new, ['template: extra RAW_ACT B w0.2 ((27.45, 58.6), (27.45, 59.4))'])

    def test_missing_template_copper_caught(self):
        for t in self.board.GetTracks():
            if t.GetClass() != 'PCB_VIA' and t.GetNetname() == 'SW_NODE':
                t.SetNet(self.board.FindNet('GND'))        # the strap is no longer the template's SW_NODE copper
                break
        issues = G.gate_template(self.board)[0]
        self.assertTrue(any('missing SW_NODE' in i for i in issues), issues)

    def test_in2_track_and_foreign_zone_caught(self):
        self.add_track('3V3', (10.0, 30.0), (12.0, 30.0), pcbnew.In2_Cu)
        self.assertTrue(any('In2.Cu track' in i for i in G.gate_in2(self.board)[0]))
        z = pcbnew.ZONE(self.board)
        z.SetLayer(pcbnew.In2_Cu)
        z.SetNet(self.board.FindNet('VLOGIC'))
        z.SetZoneName('X_VLOGIC_In2')
        o = z.Outline()
        o.NewOutline()
        for x, y in ((40, 60), (41, 60), (41, 61), (40, 61)):
            o.Append(MM(x), MM(y))
        self.board.Add(z)
        self.assertTrue(any('X_VLOGIC_In2' in i for i in G.gate_in2(self.board)[0]))

    def test_later_in2_zone_must_stay_gnd(self):
        # step 8's crystal plane (IN2_LATER) is accepted on GND only
        zs = [z for z in self.board.Zones() if z.GetZoneName() in G.IN2_LATER]
        if not zs:
            self.skipTest('no step-8 In2 zone on this board')
        zs[0].SetNet(self.board.FindNet('3V3'))
        self.assertTrue(any(zs[0].GetZoneName() in i for i in G.gate_in2(self.board)[0]))


if __name__ == '__main__':
    unittest.main()
