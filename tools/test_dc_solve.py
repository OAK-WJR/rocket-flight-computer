"""tools/dc_solve.py: the copper stack comes from the board file's own stack-up (P4-DOCS-02)."""
from pathlib import Path
import sys
import tempfile
import unittest

try:
    import pcbnew
except ImportError:
    pcbnew = None
if pcbnew:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dc_solve

STACK = '''(kicad_pcb
\t(setup
\t\t(stackup
\t\t\t(layer "F.SilkS"
\t\t\t\t(type "Top Silk Screen")
\t\t\t)
\t\t\t(layer "F.Mask"
\t\t\t\t(type "Top Solder Mask")
\t\t\t\t(thickness 0.01)
\t\t\t)
\t\t\t(layer "F.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.035)
\t\t\t)
\t\t\t(layer "dielectric 1"
\t\t\t\t(type "prepreg")
\t\t\t\t(thickness 0.203)
\t\t\t)
\t\t\t(layer "In1.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.03)
\t\t\t)
\t\t\t(layer "dielectric 2"
\t\t\t\t(type "core")
\t\t\t\t(thickness 1.03)
\t\t\t)
\t\t\t(layer "In2.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.03)
\t\t\t)
\t\t\t(layer "dielectric 3"
\t\t\t\t(type "prepreg")
\t\t\t\t(thickness 0.203)
\t\t\t)
\t\t\t(layer "B.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.035)
\t\t\t)
\t\t\t(layer "B.Mask"
\t\t\t\t(type "Bottom Solder Mask")
\t\t\t\t(thickness 0.01)
\t\t\t)
\t\t\t(copper_finish "ENIG")
\t\t)
\t)
)
'''


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class StackUp(unittest.TestCase):
    def write(self, text):
        d = tempfile.mkdtemp()
        p = Path(d) / 'b.kicad_pcb'
        p.write_text(text)
        return str(p)

    def test_reads_each_copper_thickness_and_mid_plane(self):
        s = dc_solve.stackup(self.write(STACK))
        self.assertEqual({k: v[0] for k, v in s.items()}, {'F.Cu': 0.035, 'In1.Cu': 0.03, 'In2.Cu': 0.03, 'B.Cu': 0.035})
        self.assertAlmostEqual(s['F.Cu'][1], 0.0175)
        self.assertAlmostEqual(s['In1.Cu'][1], 0.035 + 0.203 + 0.015)
        self.assertAlmostEqual(s['In2.Cu'][1], 0.035 + 0.203 + 0.03 + 1.03 + 0.015)
        self.assertAlmostEqual(s['B.Cu'][1] - s['F.Cu'][1], 0.035 / 2 + 0.203 + 0.03 + 1.03 + 0.03 + 0.203 + 0.035 / 2)

    def test_no_stackup_or_a_missing_copper_thickness_is_an_error(self):
        with self.assertRaises(ValueError):
            dc_solve.stackup(self.write('(kicad_pcb\n\t(setup\n\t)\n)\n'))
        with self.assertRaises(ValueError):
            dc_solve.stackup(self.write(STACK.replace('(layer "In2.Cu"\n\t\t\t\t(type "copper")\n\t\t\t\t(thickness 0.03)\n',
                                                      '(layer "In2.Cu"\n\t\t\t\t(type "copper")\n')))

    def test_the_board_stack_is_jlc041611_7628(self):
        board = Path(__file__).resolve().parents[1] / 'm3_design/assembly_review/m3.kicad_pcb'
        s = dc_solve.stackup(str(board))
        self.assertEqual([round(s[n][0], 3) for n in dc_solve.CU_NAMES], [0.035, 0.03, 0.03, 0.035])


if __name__ == '__main__':
    unittest.main()
