#!/usr/bin/env python3
"""Tests of tools/reference_audit.py (R8 step 9's absolute critical-reference audit).

usage: (cd tools && <KiCad python3> -m unittest test_reference_audit)

Needs the built board (m3_design/r8_build.sh writes m3_design/assembly_review/m3.kicad_pcb). The audit's unreferenced
count must equal critical_reference.py's candidate_unreferenced on the same board (same sampling); each cause class is
named at a seeded point (a crystal keep-out, another net's In2 fill, a net's own via, another net's via); and a seeded
B.Cu critical track over a non-reference In2 fill adds exactly its samples, every one attributed to that fill.
"""
import math
import sys
import unittest
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import critical_reference as CR  # noqa: E402
import reference_audit as RA  # noqa: E402

import r8_record  # noqa: E402

# R8's board: the worktree's while it is R8's, else R8's committed project (r8_record; R9 step 3 built the R9 board)
BOARD = r8_record.board()
mm, MM = pcbnew.ToMM, pcbnew.FromMM


class ReferenceAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = pcbnew.LoadBoard(str(BOARD))
        cls.rep = RA.audit(cls.board)

    def test_count_equals_critical_reference(self):
        cr = CR.compare(self.board, self.board, 0.0, False)
        self.assertEqual(self.rep['samples'], cr['candidate_samples'])
        self.assertEqual(self.rep['unreferenced'], cr['candidate_unreferenced'])
        self.assertEqual(sum(self.rep['by_cause'].values()), self.rep['unreferenced'])
        self.assertEqual(sum(e['samples'] for e in self.rep['entries']), self.rep['unreferenced'])

    def test_causes_at_seeded_points(self):
        scene = RA.Scene(self.board, [pcbnew.In1_Cu, pcbnew.In2_Cu])
        y1 = next(z for z in self.board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'Y1_In2_keepout')
        c = y1.Outline().BBox().Centre()
        self.assertEqual(scene.cause(pcbnew.In2_Cu, mm(c.x), mm(c.y), 'HSE_IN'), ('keepout', 'Y1_In2_keepout'))
        raw = next(z for z in self.board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'RAW_ACT'
                   and z.IsOnLayer(pcbnew.In2_Cu) and z.HasFilledPolysForLayer(pcbnew.In2_Cu))
        v = raw.GetFilledPolysList(pcbnew.In2_Cu).COutline(0).CPoint(0)
        inside = next(pcbnew.VECTOR2I(v.x + dx, v.y + dy) for dx in range(-MM(1), MM(1), MM(0.05))
                      for dy in range(-MM(1), MM(1), MM(0.05))
                      if raw.GetFilledPolysList(pcbnew.In2_Cu).Contains(pcbnew.VECTOR2I(v.x + dx, v.y + dy), -1, 0, True))
        self.assertEqual(scene.cause(pcbnew.In2_Cu, mm(inside.x), mm(inside.y), 'QSPI_CLK'), ('over_fill', 'RAW_ACT fill'))
        via = next(t for t in self.board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'QSPI_CLK')
        x, y = mm(via.GetPosition().x), mm(via.GetPosition().y)
        self.assertEqual(scene.cause(pcbnew.In1_Cu, x + 0.35, y, 'QSPI_CLK')[0], 'own_via')
        self.assertEqual(scene.cause(pcbnew.In1_Cu, x + 0.35, y, 'QSPI_NCS')[0], 'other_via')

    def test_seeded_track_over_foreign_fill(self):
        b = pcbnew.LoadBoard(str(BOARD))
        raw = next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'RAW_ACT'
                   and z.IsOnLayer(pcbnew.In2_Cu) and z.HasFilledPolysForLayer(pcbnew.In2_Cu))
        ps = raw.GetFilledPolysList(pcbnew.In2_Cu)
        bb = ps.BBox()
        # a 1 mm horizontal B.Cu QSPI_CLK track wholly over the RAW_ACT In2 fill, at least 0.3 mm inside its outline
        # (searched on a 0.25 mm raster; a sample exactly on the fill boundary is ambiguous)
        span = None
        for y in range(bb.GetY() + MM(0.5), bb.GetBottom(), MM(0.25)):
            for x in range(bb.GetX() + MM(0.5), bb.GetRight() - MM(1.5), MM(0.25)):
                pts = [pcbnew.VECTOR2I(x + MM(dx), y + MM(dy)) for dx in (-0.3, 0, 0.5, 1.0, 1.3)
                       for dy in (-0.3, 0, 0.3)]
                if all(ps.Contains(p, -1, 0, True) for p in pts):
                    span = (x, y)
                    break
            if span:
                break
        self.assertIsNotNone(span, 'no 1 mm span inside the RAW_ACT In2 fill')
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(*span))
        t.SetEnd(pcbnew.VECTOR2I(span[0] + MM(1.0), span[1]))
        t.SetWidth(MM(0.2))
        t.SetLayer(pcbnew.B_Cu)
        t.SetNet(b.FindNet('QSPI_CLK'))
        b.Add(t)
        rep = RA.audit(b)
        length = mm(span[0] + MM(1.0)) - mm(span[0])
        added = (math.ceil(length / CR.STEP) + 1) * 3          # centre and both edges at each step, ends included
        self.assertEqual(rep['unreferenced'] - self.rep['unreferenced'], added)
        self.assertEqual(rep['by_cause'].get('over_fill', 0) - self.rep['by_cause'].get('over_fill', 0), added)


if __name__ == '__main__':
    unittest.main()
