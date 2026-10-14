"""Native geometry regressions for missing models, mated envelopes and five-point support."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    import pcbnew
except ImportError:
    pcbnew = None

if pcbnew:
    import fit_check as fit


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class FitValidation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.model = self.folder / 'part.step'
        self.model.write_text("#1=CARTESIAN_POINT('',(-1,-1,0));\n#2=CARTESIAN_POINT('',(1,1,1));\n")
        self.board = pcbnew.BOARD()
        self.holes = []
        for a, b in (((0, 0), (46, 0)), ((46, 0), (46, 100)), ((46, 100), (0, 100)), ((0, 100), (0, 0))):
            edge = pcbnew.PCB_SHAPE(self.board)
            edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
            edge.SetLayer(pcbnew.Edge_Cuts)
            edge.SetStart(self.point(*a)); edge.SetEnd(self.point(*b)); self.board.Add(edge)
        for x, y in ((4, 4), (42.3, 4), (4, 96.4), (42, 96.4), (4, 46), *fit.RETENTION_HOLES):
            hole = pcbnew.PCB_SHAPE(self.board)
            hole.SetShape(pcbnew.SHAPE_T_CIRCLE)
            hole.SetLayer(pcbnew.Edge_Cuts)
            hole.SetCenter(self.point(x, y)); hole.SetEnd(self.point(x + 1.6, y))
            self.board.Add(hole); self.holes.append(hole)
        self.part = self.add_part('U1', 23, 20)

    def point(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def add_part(self, ref, x, y, model=True, footprint='TestPart'):
        part = pcbnew.FOOTPRINT(self.board)
        part.SetReference(ref)
        part.SetFPIDAsString('rocket:' + footprint)
        part.SetAttributes(pcbnew.FP_SMD)
        part.SetPosition(self.point(x, y))
        if model:
            item = pcbnew.FP_3DMODEL()
            item.m_Filename = '${KIPRJMOD}/part.step'
            part.Add3DModel(item)
        self.board.Add(part)
        return part

    def report(self):
        return fit.check_board(self.board, self.folder)

    def add_test_pad(self, x, y, exposed=True, shape=pcbnew.PAD_SHAPE_RECT if pcbnew else None):
        part = self.add_part('TP1', x, y, model=False, footprint='M3_TestPad_1.5')
        part.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        pad = pcbnew.PAD(part)
        pad.SetNumber('1'); pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetSize(self.point(1, 1)); pad.SetShape(shape)
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu)
        if exposed:
            layers.AddLayer(pcbnew.F_Mask)
        pad.SetLayerSet(layers)
        part.Add(pad); pad.SetPosition(self.point(x, y))
        return pad

    def test_five_supports_and_valid_models_pass(self):
        self.assertTrue(self.report()['ok'], self.report()['issues'])

    def test_r6_width_and_length_are_measured_from_outline(self):
        for drawing in self.board.GetDrawings():
            if drawing.GetLayer() == pcbnew.Edge_Cuts and drawing.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                drawing.SetEnd(self.point(47, 111))
                break
        issues = '\n'.join(self.report()['issues'])
        self.assertIn('R6 requires 46 mm', issues)
        self.assertIn('110 mm maximum', issues)

    def test_length_target_is_reported_separately_from_hard_limit(self):
        report = self.report()
        self.assertEqual(report['length_mm'], 100)
        self.assertFalse(report['target_length_met'])
        self.assertTrue(report['ok'])

    def test_missing_model_cannot_be_hidden_by_bom_exclusion(self):
        part = self.add_part('U2', 30, 20, model=False)
        part.SetAttributes(pcbnew.FP_SMD | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        self.assertIn('U2: no readable model', '\n'.join(self.report()['issues']))

    def test_only_named_board_features_are_exempt(self):
        part = self.add_part('J2', 30, 20, model=False, footprint='M3_TC2030_IDC_NL')
        part.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        self.assertTrue(self.report()['ok'])
        part.SetReference('U2')
        self.assertFalse(self.report()['ok'])

    def test_missing_or_unreadable_model_fails(self):
        for content in ('not a 3D model', "#1=CARTESIAN_POINT('',(1e999,0,0));"):
            with self.subTest(content=content):
                self.model.write_text(content)
                self.assertFalse(self.report()['ok'])
        self.model.unlink()
        self.assertFalse(self.report()['ok'])

    def test_missing_midspan_support_fails(self):
        self.board.Delete(self.holes[4])
        issues = '\n'.join(self.report()['issues'])
        self.assertIn('expected five M3 supports, found 4', issues)
        self.assertIn('middle third', issues)

    def test_a_fifth_hole_near_one_end_is_not_midspan_support(self):
        self.holes[4].Move(self.point(0, -25))
        self.assertIn('middle third', '\n'.join(self.report()['issues']))

    def test_bottom_body_must_clear_support_hardware(self):
        self.part.Flip(self.part.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        self.part.SetPosition(self.point(8.5, 46))
        self.assertTrue(self.report()['ok'])
        self.part.SetPosition(self.point(7.8, 46))
        self.assertIn('need >=3.5 mm', '\n'.join(self.report()['issues']))

    def test_top_body_requires_washer_and_radial_margin(self):
        self.part.SetPosition(self.point(8.8, 46))
        self.assertTrue(self.report()['ok'], self.report()['issues'])
        self.part.SetPosition(self.point(8.799, 46))
        self.assertIn('U1 top body', '\n'.join(self.report()['issues']))
        self.assertIn('need >=3.8 mm', '\n'.join(self.report()['issues']))

    def test_exposed_test_pad_boundary_and_masked_copper(self):
        pad = self.add_test_pad(8.3, 46)
        self.assertTrue(self.report()['ok'], self.report()['issues'])
        pad.SetPosition(self.point(8.298, 46))
        self.assertIn('TP1.1 exposed top pad', '\n'.join(self.report()['issues']))
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu)
        pad.SetLayerSet(layers)
        self.assertTrue(self.report()['ok'], self.report()['issues'])

    def test_top_pad_clearance_uses_copper_shape_not_bounding_box(self):
        pad = self.add_test_pad(7.1, 49.1, shape=pcbnew.PAD_SHAPE_CIRCLE)
        self.assertTrue(self.report()['ok'], self.report()['issues'])
        pad.SetShape(pcbnew.PAD_SHAPE_RECT)
        self.assertIn('TP1.1 exposed top pad', '\n'.join(self.report()['issues']))

    def test_rounded_pad_stroke_is_included_in_clearance(self):
        pad = self.add_test_pad(8.29, 46, shape=pcbnew.PAD_SHAPE_ROUNDRECT)
        pad.SetRoundRectRadiusRatio(.25)
        self.assertAlmostEqual(fit.copper_distance(pad, self.point(4, 46)), 3.79, places=5)
        self.assertIn('TP1.1 exposed top pad', '\n'.join(self.report()['issues']))

    def test_retention_holes_do_not_require_m3_washer_clearance(self):
        self.add_test_pad(*fit.RETENTION_HOLES[0])
        self.assertTrue(self.report()['ok'], self.report()['issues'])

    def test_only_explicit_concentric_m3_mounting_pad_is_exempt(self):
        pad = self.add_test_pad(4, 46)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetDrillSize(self.point(3.2, 3.2))
        self.assertFalse(fit.mounting_pad(pad, (4, 46)))
        pad.GetParentFootprint().SetFPIDAsString('MountingHole:MountingHole_3.2mm_M3_Pad')
        self.assertTrue(fit.mounting_pad(pad, (4, 46)))
        pad.SetPosition(self.point(4.1, 46))
        self.assertFalse(fit.mounting_pad(pad, (4, 46)))

    def test_pth_pin_envelope_must_clear_support_even_with_body_above_board(self):
        pad = pcbnew.PAD(self.part)
        pad.SetNumber('1'); pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetSize(self.point(1.5, 1.5)); pad.SetDrillSize(self.point(0.8, 0.8))
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        self.part.Add(pad); pad.SetPosition(self.point(4, 46))
        self.assertIn('U1.1 pin', '\n'.join(self.report()['issues']))

    def test_mated_bore_envelope_follows_rotation(self):
        self.part.SetPosition(self.point(39, 30))
        spec = {'TestPart': dict(refs=('U1',), box=(-1, -1, 1, 8, 0, 10), basis='test')}
        with patch.dict(fit.MATED, spec):
            self.assertTrue(self.report()['ok'])
            self.part.SetOrientationDegrees(90)
            self.assertIn('U1 mated: outside bore', '\n'.join(self.report()['issues']))

    def test_bottom_mating_transform_flips_y_and_height(self):
        self.part.SetPosition(self.point(20, 30))
        self.part.Flip(self.part.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        self.part.SetOrientationDegrees(90)
        box = fit.footprint_box(self.part, (-1, -2, 3, 4, 0, 5))
        for actual, expected in zip(box, (16, 27, 22, 31, -6.6, -1.6)):
            self.assertAlmostEqual(actual, expected)

    def test_mated_plug_collision_with_sibling_is_rejected(self):
        self.add_part('U2', 23, 24)
        spec = {'TestPart': dict(refs=('U1', 'U2'), box=(-1, -1, 1, 8, 0, 10), basis='test')}
        with patch.dict(fit.MATED, spec):
            self.assertIn('U1 mated envelope intersects U2', '\n'.join(self.report()['issues']))

    def test_new_connector_without_reviewed_mate_does_not_pass(self):
        self.add_part('J130', 30, 30, footprint='M3_SH_BM07B_SRSS_TB')
        with patch.dict(fit.MATED, {}, clear=True):
            self.assertIn('J130: mated housing/wire envelope', '\n'.join(self.report()['issues']))

    def test_thickness_and_invalid_bore_assumptions_are_rejected(self):
        self.board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(2))
        self.assertIn('thickness differs', '\n'.join(self.report()['issues']))
        with self.assertRaises(ValueError):
            fit.check_board(self.board, self.folder, tol=-0.3)


if __name__ == '__main__':
    unittest.main()
