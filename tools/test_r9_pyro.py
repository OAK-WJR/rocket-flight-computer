#!/usr/bin/env python3
"""Seeded-defect tests of the R9 pyro column builder and its gate (build step 5; R9_DECISIONS D-S5-*).

usage: (cd tools && <KiCad python3> -m unittest test_r9_pyro)

Needs the built R9 board with the pyro copper (m3_design/r9_build.sh writes m3_design/assembly_review/m3.kicad_pcb;
the tests skip while the worktree board has none). Each test changes an in-memory copy and expects the template or a
gate of m3_design/r9_pyro_check.py to name the defect, so every check the step leans on is shown to fire on this
board's geometry. Items are moved off the board, never removed (the SWIG note of the step-1 handoff). The fill-margin
test fills a scratch copy of the project (board, rules) in a temporary folder.
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
import bridge_table as BT  # noqa: E402
import check_r9 as C9  # noqa: E402
import pyro_probe as PP  # noqa: E402
import r9_dru  # noqa: E402
import r9_legalise  # noqa: E402
import r9_pyro  # noqa: E402
import r9_pyro_check as G  # noqa: E402

BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
OFF = pcbnew.VECTOR2I(MM(500), MM(500))


def _has_pyro(path):
    if not path.is_file():
        return False
    text = path.read_bytes()
    return b'PYRO1_GATE_N' in text and b'(segment' in text and b'"PYRO1_IGN"' in text


@unittest.skipUnless(_has_pyro(BOARD), 'the worktree board has no R9 pyro copper (run m3_design/r9_build.sh)')
class Column(unittest.TestCase):
    def setUp(self):
        # a fresh board per test: the changes below are never undone, and nothing is removed (the SWIG note)
        self.board = pcbnew.LoadBoard(str(BOARD))
        self.fps = {f.GetReference(): f for f in self.board.GetFootprints()}
        self.assertTrue(any(t.GetNetname() == 'PYRO1_IGN' for t in self.board.GetTracks()))

    def shift(self, ref, dx, dy=0.0):
        f = self.fps[ref]
        p = f.GetPosition()
        f.SetPosition(pcbnew.VECTOR2I(p.x + MM(dx), p.y + MM(dy)))

    def add_track(self, net, a, c, layer=pcbnew.F_Cu, w=0.2):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
        t.SetWidth(MM(w))
        t.SetLayer(layer)
        t.SetNet(self.board.FindNet(net))
        self.board.Add(t)
        return t

    def add_via(self, x, y, net='GND', size=(0.6, 0.3)):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(size[0]))
        v.SetDrill(MM(size[1]))
        v.SetNet(self.board.FindNet(net))
        self.board.Add(v)
        return v

    def track_at(self, net, a):
        for t in self.board.GetTracks():
            if t.GetClass() != 'PCB_VIA' and t.GetNetname() == net and \
                    (round(mm(t.GetStart().x), 3), round(mm(t.GetStart().y), 3)) == a:
                return t
        raise AssertionError(f'no {net} track from {a}')

    def expect(self, issues, text):
        self.assertTrue(any(text in i for i in issues), f'{text!r} not in {issues[:6]}')

    def P(self):
        return r9_pyro.Pads(self.board)

    # --- template -----------------------------------------------------------------------------------------------------
    def test_template_holds_on_the_built_board(self):
        issues, ev = G.gate_template(self.board)
        self.assertEqual(issues, [])
        self.assertGreater(ev['segments'], 40)

    def test_drawn_nets_are_the_step_nets(self):
        tracks, vias = r9_pyro.copper(self.P())
        nets = {n for n, *_ in tracks} | {n for n, *_ in vias}
        self.assertEqual(nets - set(r9_pyro.NETS), {'GND', '3V3'})
        self.assertEqual(set(r9_pyro.NETS) - nets, set())

    def test_a_moved_part_stops_the_template(self):
        for ref, dx, dy, what in (('R131', 0.1, 0.0, 'COLD'), ('R134', 0.0, 0.1, 'bar'), ('Q124', 0.1, 0.0, 'OUT bar'),
                                  ('C128', 0.0, 0.2, 'drain tab'), ('R178', 0.05, 0.0, 'CONT column')):
            self.setUp()
            self.shift(ref, dx, dy)
            with self.assertRaises(AssertionError, msg=ref) as cm:
                r9_pyro.copper(self.P())
            self.assertIn(what, str(cm.exception), ref)

    def test_a_turned_part_stops_the_template(self):
        self.fps['R170'].SetOrientationDegrees(0)
        with self.assertRaises(AssertionError):
            r9_pyro.Pads(self.board)

    def test_extra_and_moved_copper_is_caught(self):
        self.add_track('PYRO1_CONT', (11.59, 59.08), (11.59, 58.5))
        t = self.track_at('ARM1_SENSE_MCU', (25.55, 47.0))
        t.SetEnd(pcbnew.VECTOR2I(t.GetEnd().x - MM(0.1), t.GetEnd().y))
        issues, _ = G.gate_template(self.board)
        self.expect(issues, 'extra PYRO1_CONT')
        self.expect(issues, 'missing ARM1_SENSE_MCU')
        self.expect(issues, 'extra ARM1_SENSE_MCU')

    # --- margins ------------------------------------------------------------------------------------------------------
    def test_margins_hold_and_name_the_one_exception(self):
        issues, ev = G.gate_margins(self.board)
        self.assertEqual(issues, [])
        ex = ev['excepted']
        self.assertTrue(ex and all(e['rule'] == 'G' and 'PYRO1_GATE_N' in e['a'] + e['b'] for e in ex))
        self.assertTrue(all(('U1.2' in e['a'] + e['b']) or ('U1.4' in e['a'] + e['b']) for e in ex))
        for k, floor in G.FLOOR.items():
            m = ev['rules'][k]['margin']
            if m is not None and k != 'G':
                self.assertGreaterEqual(m, floor, k)

    def test_a_divider_track_at_its_pad_centre_breaks_rule_c_margin(self):
        # the BUS tap ending at R132.1's centre: 0.477 mm from R132.2 (rule C 0.3 holds, + 0.2 does not)
        P = self.P()
        t = self.track_at('PYRO1_BUS', P['R134.2'])
        self.assertAlmostEqual(mm(t.GetWidth()), r9_pyro.W_SIG)
        t.SetEnd(pcbnew.VECTOR2I(MM(P.x('R132.1')), MM(P.y('R132.1'))))
        issues, _ = G.gate_margins(self.board)
        self.expect(issues, 'margin C')
        self.assertFalse([i for i in issues if i.startswith('pyro rule')], 'rule C itself still holds')

    def test_gnd_copper_inside_the_d_margin_is_caught(self):
        dl, dt, dr, db = self.P().box['Q124.5']
        self.add_via(dr + 0.6 + 0.3, (dt + db) / 2)                 # 0.6 mm from the drain: rule D holds, D + 0.2 not
        issues, _ = G.gate_margins(self.board)
        self.expect(issues, 'margin D')

    def test_the_g_exception_covers_only_the_sentinel_pins(self):
        y = self.P().y('R127.1') - 0.55                             # 0.35 mm from GATE_N's run: rule G holds, G + 0.2 not
        self.add_track('3V3', (6.0, y), (7.5, y))
        issues, _ = G.gate_margins(self.board)
        self.expect(issues, 'margin G')
        self.assertFalse([i for i in issues if i.startswith('pyro rule')])

    # --- bridges ------------------------------------------------------------------------------------------------------
    def test_bridges_hold(self):
        issues, ev = G.gate_bridges(self.board)
        self.assertEqual(issues, [])
        self.assertFalse([r for r in ev['fires_class'] if r.split()[1].split('.')[0] != r.split('--')[1].split('.')[0]
                          .strip()])

    def test_a_fires_class_pair_under_1p5_is_caught(self):
        # C128's GND pad 1.12 mm from the drain land's west tab: a forbidden class above BT's 1.0 mm but under the
        # step's 1.5 mm
        self.shift('C128', 0.9, 0.9)
        rows = BT.table(self.board)
        self.assertFalse(BT.issues_of(rows))
        issues, _ = G.gate_bridges(self.board)
        self.expect(issues, 'fires-class')

    # --- GATE_N neighbours --------------------------------------------------------------------------------------------
    def test_gate_n_neighbours_hold(self):
        ctx = C9.Ctx(self.board, BOARD.parent, BOARD)
        issues, ev = G.gate_neighbours(self.board, ctx)
        self.assertEqual(issues, [])
        self.assertEqual(set(ev['neighbours']) - {'GND'}, set())

    def test_a_live_neighbour_of_gate_n_is_caught_and_gnd_is_not(self):
        # 1.2 mm south of GATE_N's run (beyond P-7's 0.5 mm, inside the step's 1.5 mm)
        P = self.P()
        y = P.y('R127.1') - 1.4
        for net, bad in (('GND', False), ('3V3', True), ('PYRO1_CONT', True)):
            self.setUp()
            self.add_track(net, (6.0, y), (7.5, y))
            ctx = C9.Ctx(self.board, BOARD.parent, BOARD)
            issues, _ = G.gate_neighbours(self.board, ctx)
            self.assertEqual(bool(issues), bad, net)

    # --- armed-live neighbourhood (X2) ----------------------------------------------------------------------------
    def test_no_foreign_net_within_3mm_of_armed_copper(self):
        ctx = C9.Ctx(self.board, BOARD.parent, BOARD)
        issues, ev = G.gate_armed(self.board, ctx)
        self.assertEqual(issues, [])
        self.assertEqual(ev['foreign'], {})

    def test_a_foreign_net_near_armed_copper_is_caught(self):
        P = self.P()
        self.add_track('3V3', (P.x('R134.2') + 3.4, 84.0), (P.x('R134.2') + 3.4, 85.0))    # 2.9 mm (plan) off R134.2
        ctx = C9.Ctx(self.board, BOARD.parent, BOARD)
        issues, _ = G.gate_armed(self.board, ctx)
        self.expect(issues, 'armed: 3V3')
        self.setUp()
        x = self.P().box['J121.2'][0] - 2.3                                               # 2.2 mm west of J121.2's
        self.add_track('BAT_IN', (x, 75.3), (x, 76.3), layer=pcbnew.B_Cu)                 # barrel, on B.Cu
        ctx = C9.Ctx(self.board, BOARD.parent, BOARD)
        issues, _ = G.gate_armed(self.board, ctx)
        self.expect(issues, 'armed: BAT_IN')

    # --- route pending ------------------------------------------------------------------------------------------------
    def test_route_pending_is_the_step_copper_only(self):
        # a dangling GND via that is not the step's: in J124.1's barrel, where no layer has GND copper (since step 8's
        # pours, a GND via anywhere else joins the In1 plane)
        x, y = (round(v, 4) for v in self.P()['J124.1'])
        self.add_via(x, y)
        issues, ev = G.gate_route(self.board)
        self.expect(issues, f'dangling_via GND via ({x}, {y})')
        self.assertFalse(any(f'({x}, {y})' in p for p in ev['pending']))      # not excused as the step's own copper

    # --- PYRO_BLOCK ---------------------------------------------------------------------------------------------------
    def test_block_area_is_the_derived_one_and_stays_off_u1(self):
        z = [z for z in self.board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK'][0]
        o = z.Outline().Outline(0)
        pts = [(round(mm(o.CPoint(k).x), 3), round(mm(o.CPoint(k).y), 3)) for k in range(o.PointCount())]
        self.assertEqual(pts, r9_legalise.block_area(self.board))
        u1 = C9.r8.courtyard(self.fps['U1'])
        self.assertFalse(pcbnew.SHAPE.Collide(pcbnew.SHAPE_POLY_SET(z.Outline()), u1, 0))

    def test_an_exit_lane_counts_only_near_its_ch1_pad(self):
        # a far GATE_N stub does not grow the area; a far GATE (block-internal) track does
        before = r9_legalise.block_area(self.board)
        self.add_track('PYRO1_GATE_N', (30.0, 95.0), (31.0, 95.0))
        self.assertEqual(r9_legalise.block_area(self.board), before)
        self.add_track('PYRO1_GATE', (30.0, 95.0), (31.0, 95.0))
        self.assertNotEqual(r9_legalise.block_area(self.board), before)


@unittest.skipUnless(_has_pyro(BOARD), 'the worktree board has no R9 pyro copper (run m3_design/r9_build.sh)')
class FillMargins(unittest.TestCase):
    """The DRU's zone fill margins (D-S5-12) are live: a GND pour over the column keeps rule D + 0.25 mm under R9's
    rules and only rule D's 0.5 mm without them."""

    def fill_d(self, dru_text):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            shutil.copy(BOARD, work / 'm3.kicad_pcb')
            shutil.copy(BOARD.with_suffix('.kicad_pro'), work / 'm3.kicad_pro')
            (work / 'm3.kicad_dru').write_text(dru_text)
            b = pcbnew.LoadBoard(str(work / 'm3.kicad_pcb'))
            z = pcbnew.ZONE(b)
            z.SetLayer(pcbnew.F_Cu)
            z.SetNet(b.FindNet('GND'))
            z.SetLocalClearance(MM(0.15))
            z.SetMinThickness(MM(0.15))
            o = z.Outline()
            o.NewOutline()
            for x, y in ((2.0, 60.0), (22.0, 60.0), (22.0, 88.0), (2.0, 88.0)):
                o.Append(MM(x), MM(y))
            b.Add(z)
            b.BuildConnectivity()
            self.assertTrue(pcbnew.ZONE_FILLER(b).Fill(b.Zones()))
            res = PP.probe(b, rules={'D': PP.RULES['D']})
            return res['D']['closest']['mm']

    def test_gnd_fill_keeps_rule_d_plus_its_margin(self):
        dru = BOARD.with_suffix('.kicad_dru').read_text()
        self.assertGreaterEqual(self.fill_d(dru) - 0.5, r9_dru.FILL_MARGIN['D'] - 0.002)
        blk = r9_dru.rule_block(dru, 'R9 fill margin D: GND to bus, igniter and drain')
        self.assertLess(self.fill_d(dru.replace(blk, '')) - 0.5, 0.05)


if __name__ == '__main__':
    unittest.main()
