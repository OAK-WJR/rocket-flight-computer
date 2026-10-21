#!/usr/bin/env python3
"""Seeded-defect tests of the R8 GND stitching build and gate (build step 7; m3_design/r8_ground.py,
r8_ground_check.py, sources/r8_design/step7/make_ground.py, R8_DECISIONS D62-D67).

usage: (cd tools && <KiCad python3> -m unittest test_r8_ground)

Needs the built board (m3_design/r8_build.sh writes m3_design/assembly_review/m3.kicad_pcb). Each test seeds one defect
on a copy and expects the stage or the gate to name it: a non-GND or off-angle table row, a table item missing, an
island left on one via, a region left without vias, a via in a power pour, a 7.7 A corridor or by pyro copper, a trim
over another net's fill; and the generator's legal-spot model refuses the strip, a two-pad body and a pyro margin. The
DRC-backed gates (drc, route, contract) run in r8_build.sh on the real board.
"""
import math
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design/assembly_review/sources/r8_design/step7'))
import make_ground as MG  # noqa: E402
import r8_ground as R  # noqa: E402
import r8_ground_check as G  # noqa: E402

BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
mm, MM = pcbnew.ToMM, pcbnew.FromMM


def via_at(board, q, tol=1e-4):
    return next((t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and
                 math.dist((mm(t.GetPosition().x), mm(t.GetPosition().y)), q) < tol), None)


def refill(board):
    for z in board.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    board.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()


class Copy(unittest.TestCase):
    """A copy of the built board beside its project files."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / BOARD.name
        for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
            shutil.copyfile(BOARD.with_suffix(ext), self.path.with_suffix(ext))
        self.board = pcbnew.LoadBoard(str(self.path))
        self.rows = R.read()

    def tearDown(self):
        self.tmp.cleanup()


class Stage(Copy):
    def test_draw_refuses_a_non_gnd_row_and_an_off_angle_track(self):
        with self.assertRaises(AssertionError):
            R.draw(self.board, [dict(item='via', net='3V3', layer='FB', size='0.5/0.3', x0='1', y0='30', x1='', y1='',
                                     basis='grid', points='')])
        with self.assertRaises(AssertionError):
            R.draw(self.board, [dict(item='track', net='GND', layer='B', size='0.2', x0='1', y0='30', x1='2',
                                     y1='30.5', basis='c24', points='')])

    def test_the_stage_runs_once(self):
        self.assertEqual(len(R.existing(self.board, self.rows)), len(self.rows))   # all built: a rerun is refused


class Gate(Copy):
    def test_built_board_passes_the_geometric_gates(self):
        for name, fn in (('table', lambda: G.table(self.board, self.rows)),
                         ('islands', lambda: G.island_gate(self.board)),
                         ('reach', lambda: G.reach(self.board)), ('power', lambda: G.power(self.board, self.rows))):
            issues, _ = fn()
            self.assertEqual(issues, [], name)

    def test_a_missing_table_via_and_trim_are_named(self):
        row = next(r for r in self.rows if r['basis'] == 'grid')
        self.board.Delete(via_at(self.board, (float(row['x0']), float(row['y0']))))
        trim = next(z for z in self.board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'R8_POUR_TRIM_G3')
        trim.SetDoNotAllowVias(True)
        issues, _ = G.table(self.board, self.rows)
        self.assertTrue(any(f"({row['x0']}" in i or f"{float(row['x0'])}" in i for i in issues), issues)
        self.assertTrue(any('R8_POUR_TRIM_G3' in i for i in issues), issues)

    def test_an_island_on_one_via_fails(self):
        pts = [t for t in self.board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
        target = None
        for lid, pours in G.outer_gnd(self.board).items():          # an island held by exactly two vias
            for i in range(pours.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET()
                one.AddOutline(pours.Outline(i))
                for j in range(pours.HoleCount(i)):
                    one.AddHole(pours.Hole(i, j))
                inside = [v for v in pts if one.Collide(v.GetPosition(), MM(0.15))]
                plated = [p for f in self.board.GetFootprints() for p in f.Pads() if p.GetNetname() == 'GND' and
                          p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and one.Collide(p.GetPosition(), MM(0.15))]
                if len(inside) == 2 and not plated and mm(min(v.GetPosition().y for v in inside)) > 23.5:
                    target = inside[0]
                    break
            if target:
                break
        self.assertIsNotNone(target)
        self.board.Delete(target)
        issues, _ = G.island_gate(self.board)
        self.assertTrue(issues and any('two needed' in i for i in issues), issues)

    def test_the_allowed_pocket_needs_its_via(self):
        pocket = next(i for i in G.islands(self.board) if 'D4.2' in i['pads'] and i['vias'] == 1)
        x0, y0, x1, y1 = pocket['box']
        v = next(t for t in self.board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND' and
                 x0 <= mm(t.GetPosition().x) <= x1 and y0 <= mm(t.GetPosition().y) <= y1)
        self.board.Delete(v)
        issues, ev = G.island_gate(self.board)
        self.assertTrue(any('D4.2' in i for i in issues), (issues, ev))

    def test_a_region_without_vias_fails_reach(self):
        for t in list(self.board.GetTracks()):          # clear every GND via of x 30-46, y 55-75
            q = (mm(t.GetPosition().x), mm(t.GetPosition().y))
            if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND' and 30 <= q[0] <= 46 and 55 <= q[1] <= 75:
                self.board.Delete(t)
        issues, ev = G.reach(self.board)
        self.assertTrue(any('pour_max' in i for i in issues), (issues, ev))

    def fake(self, x, y):
        return dict(item='via', net='GND', layer='FB', size='0.5/0.3', x0=str(x), y0=str(y), x1='', y1='', basis='test',
                    points='')

    def test_a_via_in_a_power_pour_a_corridor_or_by_pyro_copper_fails(self):
        cases = [((5.0, 95.0), 'zone on F.Cu'),               # the RAW_ACT west pour (F, In2, B)
                 ((25.0, 108.0), '7.7 A corridor'),            # In2 BAT_IN between J1.1 and Q120
                 ((36.0, 94.0), 'pyro')]                       # 0.31 mm from J121.2 (PYRO1_IGN, r 1.3 at (36, 95.86))
        for q, words in cases:
            issues, _ = G.power(self.board, [self.fake(*q)])
            self.assertTrue(any(words in i for i in issues), (q, issues))

    def test_a_trim_over_another_nets_fill_fails(self):
        z = pcbnew.ZONE(self.board)
        z.SetIsRuleArea(True)
        z.SetLayer(pcbnew.In2_Cu)
        z.SetZoneName('R8_POUR_TRIM_G9')
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        o = z.Outline()
        o.NewOutline()
        for x, y in ((10.0, 40.0), (12.0, 40.0), (12.0, 42.0), (10.0, 42.0)):    # In2 3V3 region
            o.Append(MM(x), MM(y))
        self.board.Add(z)
        refill(self.board)
        pcbnew.SaveBoard(str(self.path), self.board, True)
        b = pcbnew.LoadBoard(str(self.path))
        issues, _ = G.trims(self.path, b)
        self.assertTrue(any('R8_POUR_TRIM_G9' in i and '3V3' in i for i in issues), issues)


class Legal(unittest.TestCase):
    """The generator's legal-spot model on the built board."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        path = Path(cls.tmp.name) / BOARD.name
        for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
            shutil.copyfile(BOARD.with_suffix(ext), path.with_suffix(ext))
        b = pcbnew.LoadBoard(str(path))
        cls.row = next(r for r in R.read() if r['basis'] == 'grid')
        cls.q = (float(cls.row['x0']), float(cls.row['y0']))
        b.Delete(via_at(b, cls.q))                           # a grid via's spot, freed again
        cls.region = MG.legal(b)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def legal(self, q):
        return self.region.Contains(MG.P(*q))

    def test_a_freed_grid_spot_is_legal_again(self):
        self.assertTrue(self.legal(self.q), self.row)

    def test_refused_spots(self):
        for q, why in (((20.0, 20.0), 'RF strip (strip_gnd is rigid)'),
                       ((39.5, 32.3), "R72's body between its pads"),
                       ((36.0, 94.0), 'Pyro D margin of J121.2'),
                       ((5.0, 95.0), 'RAW_ACT west pour'),
                       ((0.6, 60.0), '1.0 mm from the outline')):
            self.assertFalse(self.legal(q), why)


if __name__ == '__main__':
    unittest.main()
