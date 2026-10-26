#!/usr/bin/env python3
"""Tests of the R9 post stage (silkscreen) and its gate (build step 9; R9_DECISIONS D-S9-*).

usage: (cd tools && <KiCad python3> -m unittest test_r9_post)

The board tests need the finished R9 board (m3_design/r9_build.sh through r9_post.py; they skip on an earlier board).
Each seeded defect is made on the loaded board in memory and undone (no item is removed: KiCad 10's SWIG table, step 1's
note), and must be caught by r9_post_check's legends gate or by the legend contract r9_post enforces.
"""
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r7  # noqa: E402
import check_r8  # noqa: E402
import r5_post as silk  # noqa: E402
import r9_post as POST  # noqa: E402
import r9_post_check as PC  # noqa: E402

BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
mm, MM = pcbnew.ToMM, pcbnew.FromMM


def _posted(path):
    return path.is_file() and f'(gr_text "{POST.REV}"'.encode() in path.read_bytes()


class Units(unittest.TestCase):
    PADS = [('J1', '1', (0.0, 0.0)), ('J1', '2', (5.0, 0.0)), ('J2', '1', (0.0, 10.0))]

    def test_owner_margin_own_pin_nearest(self):
        self.assertAlmostEqual(POST.owner_margin((1.0, -0.5, 2.0, 0.5), self.PADS, {('J1', '1')}), 2.0)

    def test_owner_margin_other_pin_nearer(self):
        self.assertLess(POST.owner_margin((3.0, -0.5, 4.0, 0.5), self.PADS, {('J1', '1')}), 0.0)

    def test_owner_margin_group(self):
        m = POST.owner_margin((-0.5, 4.0, 0.5, 6.0), self.PADS, {('J1', '1'), ('J2', '1')})
        self.assertAlmostEqual(m, math.hypot(4.5, 4.0) - 4.0)


@unittest.skipUnless(_posted(BOARD), 'the worktree board has no R9 silkscreen yet (run m3_design/r9_build.sh)')
class PostedBoard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = pcbnew.LoadBoard(str(BOARD))

    def texts(self, text):
        return [d for d in self.board.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == text and
                d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]

    def gate(self):
        return PC.gate_legends(self.board, BOARD)[0]

    def test_legend_contract(self):
        b = self.board
        self.assertEqual(check_r7.duplicate_ids(b) + check_r7.pin_legends(b) + check_r7.legend_subjects(b) +
                         check_r8.terminal_legends(b)[0], [])

    def test_post_gate_clean(self):
        self.assertEqual(self.gate(), [])

    def test_terminal_legends_own_their_pins(self):
        pads = POST.connector_pads(self.board)
        for ref, pins in POST.TERMINAL_PINS:
            for number, name in pins:
                own = [d for d in self.texts(f'{number}:{name}') if
                       POST.owner_margin(POST.text_box(d), pads, {(ref, number)}) >= POST.OWN_MARGIN]
                self.assertEqual(len(own), 1, f'{ref}.{number}')

    def test_plug_numbers_one_row_west_to_east(self):
        spots = []
        for plug, numbers in POST.PLUG_ROWS:
            (t,) = self.texts(plug)
            col = sum(silk.pad(self.board, 'J122', n)[0] for n in numbers) / 3
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            self.assertLessEqual(abs(x - col), POST.PLUG_SLIDE + 1e-6, plug)
            spots.append((x, y, t.GetLayer()))
        self.assertEqual(len({(round(y, 4), lay) for _, y, lay in spots}), 1)
        self.assertEqual([s[0] for s in spots], sorted(s[0] for s in spots))

    def test_pin1_dots(self):
        for ref in silk.DOT_PARTS:
            f = silk.fp_of(self.board, ref)
            layer = pcbnew.B_SilkS if f.IsFlipped() else pcbnew.F_SilkS
            pads = [(p.GetNumber(), silk.bx(p)) for p in f.Pads() if p.GetNumber()]
            dots = []
            for d in self.board.GetDrawings():
                if d.GetLayer() == layer and d.GetClass() == 'PCB_SHAPE' and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                    c = (mm(d.GetCenter().x), mm(d.GetCenter().y))
                    gaps = {n: silk._gap((c[0], c[1], c[0], c[1]), r) for n, r in pads}
                    if min(gaps.values()) <= POST.DOT_REACH + 0.2:
                        dots.append(min(gaps, key=gaps.get))
            self.assertEqual(dots, ['1'], ref)

    def test_renamed_legend_caught(self):
        (t,) = self.texts('IGN')
        t.SetText('IGX')
        try:
            issues = self.gate()
        finally:
            t.SetText('IGN')
        self.assertTrue(any("'IGN' drawn 0" in i for i in issues), issues)
        self.assertTrue(any("unexpected board silkscreen text 'IGX'" in i for i in issues), issues)

    def test_terminal_legend_on_the_wrong_pin_caught(self):
        (t,) = self.texts('2:E1+')
        before = t.GetPosition()
        x, y = silk.pad(self.board, 'J124', '1')
        t.SetPosition(silk.P(x + 2.0, y))
        try:
            issues = check_r8.terminal_legends(self.board)[0]
        finally:
            t.SetPosition(before)
        self.assertTrue(any('2:E1+' in i for i in issues), issues)

    def test_small_designator_caught(self):
        f = next(f for f in self.board.GetFootprints() if f.Reference().IsVisible())
        t = f.Reference()
        size = t.GetTextSize()
        t.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
        try:
            issues = self.gate()
        finally:
            t.SetTextSize(size)
        self.assertTrue(any(f.GetReference() in i for i in issues), issues)

    def test_value_on_silkscreen_caught(self):
        f = next(iter(self.board.GetFootprints()))
        v = f.Value()
        layer, shown = v.GetLayer(), v.IsVisible()
        v.SetLayer(pcbnew.B_SilkS if f.IsFlipped() else pcbnew.F_SilkS)
        v.SetVisible(True)
        try:
            issues = self.gate()
        finally:
            v.SetLayer(layer)
            v.SetVisible(shown)
        self.assertTrue(any('value on the silkscreen' in i for i in issues), issues)

    def test_second_pass_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / 'm3.kicad_pcb'
            shutil.copy(BOARD, copy)
            r = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'm3_design/r9_post.py'), '--board', str(copy)],
                               capture_output=True, text=True, timeout=300)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('runs once', r.stdout + r.stderr)
            self.assertEqual(copy.read_bytes(), BOARD.read_bytes())


if __name__ == '__main__':
    unittest.main()
