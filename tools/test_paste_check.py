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

    def test_tiny_oversized_and_same_area_wrong_shape_apertures_fail(self):
        self.fp('R1', [(1, 1)])
        for aperture in ('0.001X0.001', '1X1', '0.25X1'):
            with self.subTest(aperture=aperture):
                layers = self.gerber(('R1', 1, 1))
                layers['F'] = layers['F'].replace('0.5X0.5', aperture)
                self.assertIn('differs from native paste geometry', '\n'.join(gate.check(self.board, layers)[0]))

    def test_circle_and_oval_geometry_pass(self):
        f = self.fp('C1', [(1, 1)])
        p = next(iter(f.Pads()))
        for shape, size, aperture in ((pcbnew.PAD_SHAPE_CIRCLE, (.5, .5), 'C,0.5'),
                                      (pcbnew.PAD_SHAPE_OVAL, (.5, 1.), 'O,0.5X1')):
            with self.subTest(aperture=aperture):
                p.SetShape(shape)
                p.SetSize(pcbnew.VECTOR2I(*(pcbnew.FromMM(x) for x in size)))
                layers = self.gerber(('C1', 1, 1))
                layers['F'] = layers['F'].replace('R,0.5X0.5', aperture)
                self.assertEqual(gate.check(self.board, layers)[0], [])

    def test_equivalent_outline_macro_passes_and_clear_cutout_fails(self):
        self.fp('R1', [(1, 1)])
        macro = '%AMBox*4,1,4,-0.25,-0.25,0.25,-0.25,0.25,0.25,-0.25,0.25,-0.25,-0.25,0*%\n'
        layers = self.gerber(('R1', 1, 1))
        layers['F'] = layers['F'].replace('%ADD10R,0.5X0.5*%', macro + '%ADD10Box*%')
        self.assertEqual(gate.check(self.board, layers)[0], [])
        layers['F'] = layers['F'].replace(',0*%', ',0*1,0,0.2,0,0*%', 1)
        self.assertIn('differs from native paste geometry', '\n'.join(gate.check(self.board, layers)[0]))

    @staticmethod
    def rounded_macro(radius, x, y, rotation=0):
        macro = ('%AMRounded*\n'
                 '4,1,4,$2,$3,-$2,$3,-$2,-$3,$2,-$3,$2,$3,$4*\n'
                 '1,1,$1+$1,$2,$3,$4*1,1,$1+$1,-$2,$3,$4*\n'
                 '1,1,$1+$1,-$2,-$3,$4*1,1,$1+$1,$2,-$3,$4*\n'
                 '20,1,$1+$1,$2,$3,-$2,$3,$4*20,1,$1+$1,-$2,$3,-$2,-$3,$4*\n'
                 '20,1,$1+$1,-$2,-$3,$2,-$3,$4*20,1,$1+$1,$2,-$3,$2,$3,$4*%\n')
        return macro + f'%ADD10Rounded,{radius}X{x}X{y}X{rotation}*%'

    def test_native_paste_margins_and_rotated_roundrect_pass(self):
        p = next(iter(self.fp('U1', [(1, 1)]).Pads()))
        p.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.), pcbnew.FromMM(2.)))
        p.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
        p.SetRoundRectRadiusRatio(.25)
        for margin, ratio, radius, x, y, rotation in ((-.1, 0., .15, .25, .75, 0),
                                                     (0., -.1, .2, .2, .6, 30)):
            with self.subTest(margin=margin, ratio=ratio, rotation=rotation):
                p.SetLocalSolderPasteMargin(pcbnew.FromMM(margin))
                p.SetLocalSolderPasteMarginRatio(ratio)
                p.SetOrientationDegrees(rotation)
                layers = self.gerber(('U1', 1, 1))
                layers['F'] = layers['F'].replace('%ADD10R,0.5X0.5*%', self.rounded_macro(radius, x, y, rotation))
                self.assertEqual(gate.check(self.board, layers)[0], [])

    def test_maker_split_exposed_pad_windows_and_explicit_dry_land_pass(self):
        # TI DSK0010A / current U401: copper EP1.2x2mm, two1.13x0.89mm stencil windows.
        f = self.fp('U401', [(10, 10)], paste=False)
        copper = next(iter(f.Pads()))
        copper.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(2.)))
        for y in (9.445, 10.555):
            p = pcbnew.PAD(f)
            p.SetNumber('')
            p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            p.SetShape(pcbnew.PAD_SHAPE_RECT)
            p.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.13), pcbnew.FromMM(.89)))
            ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Paste); p.SetLayerSet(ls)
            f.Add(p); p.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(10), pcbnew.FromMM(y)))
        # An explicit native dry/manual-process land adds no required paste flash.
        # There is no automatic C84/ref-name exemption for a pad carrying paste.
        self.fp('C84', [(20, 20)], paste=False)
        layers = self.gerber(('U401', 10, 9.445), ('U401', 10, 10.555))
        layers['F'] = layers['F'].replace('0.5X0.5', '1.13X0.89')
        self.assertEqual(gate.check(self.board, layers)[0], [])

    def test_unsupported_or_nonfinite_apertures_fail_closed(self):
        self.fp('R1', [(1, 1)])
        for old, new in (('R,0.5X0.5', 'Unsupported,0.5'), ('R,0.5X0.5', 'R,nanX0.5'),
                         ('D10*', '%LPC*%\nD10*')):
            with self.subTest(new=new):
                layers = self.gerber(('R1', 1, 1))
                layers['F'] = layers['F'].replace(old, new)
                self.assertTrue(gate.check(self.board, layers)[0])


if __name__ == '__main__':
    unittest.main()
