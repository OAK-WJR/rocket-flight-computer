"""Seeded defects for tools/paste_check.py: stray, missing, doubled and dry-pad paste must each fail."""
from pathlib import Path
import sys
import unittest

try:
    import pcbnew
except ImportError:
    pcbnew = None
if pcbnew:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import paste_check as gate

HEAD = '%FSLAX46Y46*%\n%MOMM*%\n%ADD10R,0.5X0.5*%\nD10*\n'


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class PasteCheck(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.BOARD()

    def fp(self, ref, pads, paste=True, attrs=0):
        f = pcbnew.FOOTPRINT(self.board)
        f.SetReference(ref)
        f.SetAttributes(attrs)
        self.board.Add(f)
        for num, (x, y) in enumerate(pads, 1):
            p = pcbnew.PAD(f)
            p.SetNumber(str(num))
            p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            p.SetShape(pcbnew.PAD_SHAPE_RECT)
            p.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.5), pcbnew.FromMM(0.5)))
            ls = pcbnew.LSET()
            ls.AddLayer(pcbnew.F_Cu)
            ls.AddLayer(pcbnew.F_Mask)
            if paste:
                ls.AddLayer(pcbnew.F_Paste)
            p.SetLayerSet(ls)
            f.Add(p)
            p.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        return f

    @staticmethod
    def gerber(*flashes):
        body = ''.join(f'%TO.C,{c}*%\nX{int(x * 1e6)}Y{int(-y * 1e6)}D03*\n%TD*%\n' for c, x, y in flashes)
        return {'F': HEAD + body + 'M02*\n', 'B': HEAD + 'M02*\n'}

    def issues(self, *flashes):
        return gate.check(self.board, self.gerber(*flashes))[0]

    def test_one_flash_per_pasted_pad_passes(self):
        self.fp('R1', [(1, 1), (2, 1)])
        self.assertEqual(self.issues(('R1', 1, 1), ('R1', 2, 1)), [])

    def test_missing_and_doubled_paste_fail(self):
        self.fp('R1', [(1, 1), (2, 1)])
        self.assertIn('0 flashes', '\n'.join(self.issues(('R1', 1, 1))))
        self.assertIn('2 flashes', '\n'.join(self.issues(('R1', 1, 1), ('R1', 1, 1), ('R1', 2, 1))))

    def test_stray_flash_fails(self):
        self.fp('R1', [(1, 1), (2, 1)])
        self.assertIn('matches 0 pads', '\n'.join(self.issues(('R1', 1, 1), ('R1', 2, 1), ('R1', 5, 5))))

    def test_flash_on_a_dry_pad_fails(self):
        self.fp('J30', [(10, 1)], paste=False)                                # SMA jack: no paste
        self.fp('C303', [(20, 1)], paste=False, attrs=pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM)
        self.fp('R1', [(10, 1), (20, 1)])                                     # a part whose pads overlap them
        out = '\n'.join(self.issues(('R1', 10, 1), ('R1', 20, 1)))
        self.assertIn('J30.1, which must stay dry', out)
        self.assertIn('C303.1, which must stay dry', out)

    def test_region_fails(self):
        self.fp('R1', [(1, 1)])
        layers = self.gerber(('R1', 1, 1))
        layers['F'] = layers['F'].replace('M02*', 'G36*\nX0Y0D02*\nX1000000Y0D01*\nG37*\nM02*')
        out = '\n'.join(gate.check(self.board, layers)[0])
        self.assertIn('region', out)
        self.assertIn('draw', out)


if __name__ == '__main__':
    unittest.main()
