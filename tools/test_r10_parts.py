"""The electrical budget follows native firing copper and rejects stale geometry without writing it."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'm3_design'), str(ROOT / 'tools')]
import pcbnew
import check_r10
import r10_parts as parts


class NativeFireBudget(unittest.TestCase):
    def setUp(self):
        self.source = Path(os.environ.get('R10_BOARD', ROOT / 'm3_design/assembly_review/m3.kicad_pcb'))
        self.board = pcbnew.LoadBoard(str(self.source))

    def test_routed_drain_entry_and_one_aligned_source_path_are_included(self):
        paths, entries = parts.native_fire_copper(self.board)
        external, joined, _ = check_r10.fire_path(self.board, 'BAT_IN', check_r10.FIRE_TERMINALS['BAT_IN'])
        self.assertTrue(joined)
        self.assertAlmostEqual(entries['BAT_IN'], 2 ** -.5, places=6)
        self.assertAlmostEqual(paths['BAT_IN'][0], sum(pcbnew.ToMM(t.GetLength()) for t in external) + entries['BAT_IN'])
        self.assertEqual(entries['RAW_ACT'], 0)
        self.assertAlmostEqual(paths['ACT_FET_S'][0], 2.2, places=6)
        self.assertEqual(paths['ACT_FET_S'][1], .4)

    def test_dead_branch_inside_firing_resistor_pad_is_excluded(self):
        before = parts.native_fire_copper(self.board)
        fp = next(f for f in self.board.GetFootprints() if f.GetReference() == 'R134')
        pad = fp.FindPadByNumber('2')
        branch = pcbnew.PCB_TRACK(self.board)
        branch.SetNetCode(pad.GetNetCode())
        branch.SetLayer(pcbnew.B_Cu)
        branch.SetWidth(pcbnew.FromMM(.5))
        branch.SetStart(pad.GetPosition())
        branch.SetEnd(pad.GetPosition() + pcbnew.VECTOR2I(pcbnew.FromMM(.2), pcbnew.FromMM(.2)))
        self.assertTrue(pad.HitTest(branch.GetEnd()))
        self.board.Add(branch)
        self.assertEqual(parts.native_fire_copper(self.board), before)

    def test_longer_connected_route_changes_current_and_makes_saved_budget_stale(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            board_path = folder / 'm3.kicad_pcb'
            pcbnew.SaveBoard(str(board_path), self.board)
            argv = ['r10_parts.py', '--budget-only', '--board', str(board_path)]
            with patch.object(parts, 'NOTES', folder), patch.object(sys, 'argv', argv), \
                    patch.object(parts, 'generated', side_effect=AssertionError('budget must not rewrite libraries')), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(parts.main(), 0)
            budget_path = folder / 'parts_budget.json'
            saved = budget_path.read_bytes()
            before = json.loads(saved)
            tracks, _, _ = check_r10.fire_path(self.board, 'PYRO1_IGN', check_r10.FIRE_TERMINALS['PYRO1_IGN'])
            track = next(t for t in tracks if t.GetStart().x == t.GetEnd().x)
            a, b, layer, net, width = track.GetStart(), track.GetEnd(), track.GetLayer(), track.GetNetCode(), track.GetWidth()
            self.board.Remove(track)
            offset = pcbnew.VECTOR2I(pcbnew.FromMM(-1), 0)
            points = (a, a + offset, b + offset, b)
            for start, end in zip(points, points[1:]):
                extra = pcbnew.PCB_TRACK(self.board)
                extra.SetStart(start); extra.SetEnd(end)
                extra.SetLayer(layer); extra.SetNetCode(net); extra.SetWidth(width)
                self.board.Add(extra)
            pcbnew.SaveBoard(str(board_path), self.board)
            after = parts.power_budget(board_path)
            old, new = before['fire_current_GAP1'], after['fire_current_GAP1']
            self.assertAlmostEqual(new['CAD_track_length_width_mm']['PYRO1_IGN'][0] - old['CAD_track_length_width_mm']['PYRO1_IGN'][0], 2, places=6)
            self.assertGreater(new['copper_20C_ohm'], old['copper_20C_ohm'])
            self.assertLess(new['primary_40mohm_FETs']['pack_7V4_by_stall_count']['4']['fire_A'],
                            old['primary_40mohm_FETs']['pack_7V4_by_stall_count']['4']['fire_A'])
            self.assertNotEqual(new['board_sha256'], old['board_sha256'])
            with patch.object(parts, 'NOTES', folder), patch.object(sys, 'argv', argv + ['--check']), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(parts.main(), 1)
            self.assertEqual(budget_path.read_bytes(), saved)

    def test_disconnected_native_fire_path_cannot_generate_a_budget(self):
        tracks, _, _ = check_r10.fire_path(self.board, 'PYRO1_IGN', check_r10.FIRE_TERMINALS['PYRO1_IGN'])
        self.board.Remove(max(tracks, key=lambda t: t.GetLength()))
        with self.assertRaisesRegex(ValueError, 'PYRO1_IGN: no native fire path'):
            parts.native_fire_copper(self.board)

    def test_library_stage_has_no_previous_board_dependency(self):
        with patch.object(sys, 'argv', ['r10_parts.py', '--library-only', '--check', '--board', 'missing.kicad_pcb']), \
                patch.object(parts, 'generated', return_value={}), patch.object(parts, 'geometry_checks', return_value={}), \
                patch.object(parts, 'power_budget', side_effect=AssertionError('library stage read the previous board')), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(parts.main(), 0)


if __name__ == '__main__':
    unittest.main()
