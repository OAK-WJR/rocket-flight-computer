#!/usr/bin/env python3
"""Seeded-defect tests of the R9 placement legaliser, builder table and gate (build step 3; R9_DECISIONS D-S3-*).

usage: (cd tools && <KiCad python3> -m unittest test_r9_place)

Needs the built R9 placement board (m3_design/r9_build.sh writes m3_design/assembly_review/m3.kicad_pcb; the tests skip
while the worktree still holds R8's board). Each test moves one part of an in-memory copy and expects the legaliser to
name the broken rule, so every rule the gate leans on is shown to fire on this board's geometry.
"""
import math
import sys
import tempfile
import unittest
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r9 as C9  # noqa: E402
import r9_legalise as L  # noqa: E402
import r9_pcb  # noqa: E402

BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
mm = pcbnew.ToMM


def _is_r9(path):
    return path.is_file() and r9_pcb.REV.encode() in path.read_bytes()[:200000]


@unittest.skipUnless(_is_r9(BOARD), 'the worktree board is not the R9 placement board (run m3_design/r9_build.sh)')
class Placement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = pcbnew.LoadBoard(str(BOARD))
        cls.rows, cls.feat = r9_pcb.read_place(r9_pcb.PLACE)
        cls.fps = {f.GetReference(): f for f in cls.board.GetFootprints()}

    def setUp(self):
        self.model = L.Model(self.board, list(self.fps))
        self.moved = []

    def tearDown(self):
        for f, pos, rot, flipped in reversed(self.moved):
            if f.IsFlipped() != flipped:
                f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            f.SetOrientationDegrees(rot)
            f.SetPosition(pos)

    def move(self, ref, x, y, rot=None, side=None, check=None):
        f = self.fps[ref]
        self.moved.append((f, f.GetPosition(), f.GetOrientationDegrees(), f.IsFlipped()))
        if side is not None and (side == 'B') != f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        if rot is not None:
            f.SetOrientationDegrees(rot)
        f.SetPosition(L.V(x, y))
        return self.model.violations(check or ref)

    def at(self, ref):
        p = self.fps[ref].GetPosition()
        return mm(p.x), mm(p.y)

    def expect(self, found, text):
        self.assertTrue(any(text in v for v in found), f'{text!r} not in {found}')

    # --- the table and the built board ----------------------------------------------------------------------------
    def test_table_names_every_part_once(self):
        self.assertEqual(set(self.rows), set(self.fps))
        self.assertEqual(len(self.rows), 249)
        self.assertEqual(len(self.feat['supports']), 5)
        self.assertEqual(len(self.feat['ties']), 2)

    def test_board_matches_the_table(self):
        for ref, (x, y, rot, side) in self.rows.items():
            f = self.fps[ref]
            self.assertAlmostEqual(mm(f.GetPosition().x), x, places=4, msg=ref)
            self.assertAlmostEqual(mm(f.GetPosition().y), y, places=4, msg=ref)
            self.assertEqual(f.IsFlipped(), side == 'B', ref)

    def test_outline_and_supports_from_the_table(self):
        w, length = self.feat['outline']
        self.assertEqual((self.model.W, self.model.L), (w, length))
        self.assertEqual(sorted(self.model.supports), sorted(self.feat['supports']))
        self.assertEqual(sorted(self.model.ties), sorted(self.feat['ties']))

    def test_built_board_is_legal(self):
        self.assertEqual(L.check(self.board, list(self.fps)), {})

    def test_pyro_block_is_derived(self):
        zs = [z for z in self.board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK']
        self.assertEqual(len(zs), 1)
        o = zs[0].Outline().Outline(0)
        pts = [(round(mm(o.CPoint(i).x), 4), round(mm(o.CPoint(i).y), 4)) for i in range(o.PointCount())]
        self.assertEqual(pts, [(round(x, 4), round(y, 4)) for x, y in L.block_area(self.board)])

    def test_read_place_refuses_a_bad_table(self):
        text = r9_pcb.PLACE.read_text()
        first = next(line for line in text.splitlines() if line and not line.startswith(('#', 'ref', '@')))
        with tempfile.TemporaryDirectory() as tmp:
            dup = Path(tmp) / 'dup.tsv'
            dup.write_text(text + first + '\n')
            with self.assertRaises(AssertionError):
                r9_pcb.read_place(dup)
            nosup = Path(tmp) / 'nosup.tsv'
            nosup.write_text('\n'.join(line for line in text.splitlines() if not line.startswith('@M3')) + '\n')
            with self.assertRaises(AssertionError):
                r9_pcb.read_place(nosup)

    # --- seeded defects: one rule each ----------------------------------------------------------------------------
    def test_courtyard_overlap(self):
        x, y = self.at('R61')
        self.expect(self.move('R60', x, y), 'courtyard overlaps R61')

    def test_outline(self):
        self.expect(self.move('C14', 45.9, 50.0), 'courtyard outside the outline')

    def test_rf_strip_boundary(self):                                 # R-1, owner decision 3
        x, y = self.at('C301')
        self.expect(self.move('C301', x, C9.Y_F + 0.2), 'strip boundary y_f 22.0')

    def test_non_rf_pad_in_the_strip(self):                           # R-1
        self.expect(self.move('R164', 20.0, C9.Y_F - 1.0, side='F'), 'in the RF strip')

    def test_f10_rf_separation(self):                                 # R-10, 5.94 mm courtyards
        ux, uy = self.at('U1')
        self.expect(self.move('R306', ux, uy - 8.6 - 3.0, 90, 'F'), 'R-10: 5.94 mm RF separation to U1')

    def test_strict_pad_rule_gate_to_sense(self):                     # GS 1.2 mm, r9_plan section 1
        found = self.move('R178', *self.near('R128', '1', 0.9))
        self.expect(found, 'pad 1 (PYRO1_CONT) closer than 1.2 mm to R128.1 (PYRO1_GATE)')

    def test_support_floor(self):                                     # M-5 top floor 5.008 mm
        sx, sy = self.feat['supports'][-1]
        self.expect(self.move('C14', sx - 4.0, sy, 0, 'F'), 'from support')

    def test_tie_path(self):                                          # M-3
        tx, ty = self.feat['ties'][0]
        self.expect(self.move('C14', tx + 2.6, ty - 1.4, 0, 'B'), 'J122 tie path')

    def test_bottom_beside_through_hole(self):                        # M-6, 1.5 mm
        x, y = self.at('J1')                                          # between J1's pins 2 and 3, under the body
        self.expect(self.move('C14', x, y, 0, 'B'), 'through-hole pad of J1')

    def test_coat_keep_off_inside_the_coat_region(self):              # P-10 (ORDERING 5)
        bx = L._box(L.poly_of(L.block_area(self.board)))
        self.expect(self.move('U5', bx[0] + 4.0, (bx[1] + bx[3]) / 2), 'P-10: inside the coat region')

    def test_j1_front_corridor(self):                                 # M-4
        x, y = self.at('J1')
        self.expect(self.move('C14', x, self.model.L - 0.8, 0, 'F'), "in front of J1")

    def test_rule_clearances(self):
        rc = L.rule_clearance
        self.assertEqual(rc('RAW_ACT', 'PYRO1_BUS', None, None, False, False), 1.0)        # E
        self.assertEqual(rc('PYRO1_GATE', '3V3', None, None), 0.3)                          # G: P-1b scope
        self.assertEqual(rc('PYRO1_GATE', '3V3', None, None, g_scope_a=False, g_scope_b=False), 0.15)  # in U1's courtyard
        raw = self.fps['J124'].FindPadByNumber('2')                                        # RAW_ACT through-hole
        self.assertEqual(raw.GetNetname(), 'RAW_ACT')
        self.assertEqual(rc('RAW_ACT', 'GND', 'J124', None, pad_a=raw), 0.3)                # R9 RAW_ACT pins (LC-1)
        tp = self.fps['TP80'].Pads()[0]
        self.assertEqual(rc(tp.GetNetname(), '3V3', 'TP80', None, pad_a=tp), 1.0)          # R9 bare test pads (LC-1)
        self.assertEqual(rc('3V3', 'GND', None, None), 0.15)

    def near(self, ref, pad, gap):
        """A spot that puts the moved part's nearest pad about `gap` mm from ref.pad (used for the strict pad rules)."""
        p = self.fps[ref].FindPadByNumber(pad).GetPosition()
        return mm(p.x) + gap + 0.5, mm(p.y)


class GateDrc(unittest.TestCase):
    """The step-3 gate defers only the silkscreen violations r9_post.py settles (a text among the items); footprint
    graphics against another footprint's graphics, pad or the edge fail at placement (R9_DECISIONS D-S9-01)."""

    @staticmethod
    def report(*violations):
        return dict(violations=[dict(type=t, items=[dict(description=d) for d in items]) for t, items in violations],
                    unconnected_items=[], schematic_parity=[])

    def setUp(self):
        import r9_place_check
        self.judge = r9_place_check.judge_drc

    def test_designator_silk_deferred(self):
        issues, ev = self.judge(self.report(('silk_overlap', ('Reference field of C1', 'Segment of Q30 on B.Silkscreen')),
                                            ('silk_over_copper', ('Reference field of R2', 'Pad 1 [GND] of C3 on F.Cu')),
                                            ('silk_edge_clearance', ('Reference field of C4', 'Segment on Edge.Cuts')),
                                            ('silk_over_copper', ("PCB text 'ARM' on F.Silkscreen", 'Pad 1 [GND] of TP74 on F.Cu'))))
        self.assertEqual(issues, [])
        self.assertEqual(ev['deferred'], {'silk_overlap': 1, 'silk_over_copper': 2, 'silk_edge_clearance': 1})

    def test_footprint_silk_fails(self):
        for kind, items in (('silk_overlap', ('Segment of Q30 on B.Silkscreen', 'Segment of Q31 on B.Silkscreen')),
                            ('silk_overlap', ('Circle of D123 on B.Silkscreen', 'Circle of Q123 on B.Silkscreen')),
                            ('silk_over_copper', ('Segment of C84 on F.Silkscreen', 'Pad 1 [GND] of TP88 on F.Cu')),
                            ('silk_edge_clearance', ('Segment of J30 on F.Silkscreen', 'Segment on Edge.Cuts'))):
            issues, _ = self.judge(self.report((kind, items)))
            self.assertEqual(len(issues), 1, (kind, items))

    def test_other_violations_fail(self):
        issues, _ = self.judge(self.report(('clearance', ('Pad 1 of R1', 'Pad 2 of R2'))))
        self.assertEqual(len(issues), 1)


if __name__ == '__main__':
    unittest.main()
