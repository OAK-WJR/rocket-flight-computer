"""Native geometry regressions for missing models, mated envelopes and five-point support."""
import math
import os
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
    def test_r10_screw_terminals_have_no_plug_envelopes_but_sd_card_is_required(self):
        self.assertEqual(fit.R10_MATED_REFS, {'J430'})
        self.assertNotIn('M3_GH_BM02B_GHS_TBT', fit.R10_MATED)
        self.assertNotIn('HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR', fit.R10_MATED)
        self.assertEqual(fit.MATED['M3_JST_PH_B2B_2P']['refs'], ('J123',))  # Legacy fit policy stays intact.

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

    def test_micro_sd_locked_card_has_a_required_envelope_and_clears_hardware(self):
        socket = self.add_part('J430', 12, 17, footprint='M3_MICROSD_MOLEX_472192001')
        model = self.folder / 'closed_sd.step'
        model.write_text("#1=CARTESIAN_POINT('',(-7.525,-6,0));\n#2=CARTESIAN_POINT('',(7.525,9.7,2.1));\n")
        socket.Models()[0].m_Filename = '${KIPRJMOD}/closed_sd.step'

        report = fit.check_board(self.board, self.folder, profile='r10')
        self.assertIn('J430 mated', {row[1] for row in report['rows']})
        self.assertTrue(any('J430 mated top body' in issue for issue in report['issues']))
        socket.Move(self.point(0, .5))
        report = fit.check_board(self.board, self.folder, profile='r10')
        self.assertFalse(any('J430 mated top body' in issue for issue in report['issues']))
        socket.SetFPIDAsString('rocket:unreviewed_socket')
        report = fit.check_board(self.board, self.folder, profile='r10')
        self.assertTrue(any('J430: required R10 mated envelope missing' in issue for issue in report['issues']))

    def test_r10_terminal_tail_detects_a_bottom_body_collision(self):
        terminal = self.add_part('J1', 23, 40, footprint='M3_DB125_2P_GN')
        model = self.folder / 'terminal.step'
        model.write_text("#1=CARTESIAN_POINT('',(-4.62,-4,0));\n#2=CARTESIAN_POINT('',(3.7,4.1,8.9));\n")
        terminal.Models()[0].m_Filename = '${KIPRJMOD}/terminal.step'
        pin = pcbnew.PAD(terminal)
        pin.SetNumber('1'); pin.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pin.SetSize(self.point(1.9, 1.9)); pin.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pin.SetLayerSet(pcbnew.LSET.AllCuMask())
        terminal.Add(pin); pin.SetPosition(self.point(23, 40))
        part = self.add_part('U2', 30, 40)
        part.Flip(part.GetPosition(), False)
        report = fit.check_board(self.board, self.folder, profile='r10')
        self.assertFalse(any('terminal tail intersects' in issue for issue in report['issues']))
        part.Move(self.point(-7, 0))
        report = fit.check_board(self.board, self.folder, profile='r10')
        self.assertIn('J1.1 terminal tail intersects U2 model box', report['issues'])
        self.assertEqual(report['terminal_tails']['count'], 1)
        self.assertAlmostEqual(report['terminal_tails']['nominal_4mm_standoff_plate_clearance_mm'], 1.8)

    def test_width_and_length_are_measured_from_outline(self):
        for drawing in self.board.GetDrawings():
            if drawing.GetLayer() == pcbnew.Edge_Cuts and drawing.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                drawing.SetEnd(self.point(47, 121))
                break
        issues = '\n'.join(self.report()['issues'])
        self.assertIn('P1 requires 46 mm', issues)
        self.assertIn('120 mm maximum', issues)

    def test_r7_length_within_the_120_mm_maximum_passes(self):
        for drawing in self.board.GetDrawings():
            if drawing.GetLayer() == pcbnew.Edge_Cuts and drawing.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                drawing.SetEnd(self.point(46, 118))
                break
        report = self.report()
        self.assertNotIn('120 mm maximum', '\n'.join(report['issues']))

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

    def test_invalid_model_transforms_fail_without_nonfinite_rows(self):
        self.assertTrue(self.report()['ok'])
        for field in ('m_Scale', 'm_Offset', 'm_Rotation'):
            for axis in ('x', 'y', 'z'):
                values = (float('nan'), float('inf'), -float('inf'))
                if field == 'm_Scale':
                    values += (0., -1.)
                for value in values:
                    with self.subTest(field=field, axis=axis, value=value):
                        vector = getattr(self.part.Models()[0], field)
                        original = getattr(vector, axis)
                        setattr(vector, axis, value)
                        report = self.report()
                        self.assertFalse(report['ok'])
                        self.assertIn('U1: invalid model transform', '\n'.join(report['issues']))
                        self.assertNotIn('U1', {row[1] for row in report['rows']})
                        setattr(vector, axis, original)

    def test_degenerate_or_overflowed_model_geometry_fails(self):
        self.model.write_text("#1=CARTESIAN_POINT('',(-1,-1,0));\n#2=CARTESIAN_POINT('',(1,1,0));\n")
        self.assertIn('degenerate model envelope', '\n'.join(self.report()['issues']))
        self.model.write_text("#1=CARTESIAN_POINT('',(-2,-2,0));\n#2=CARTESIAN_POINT('',(2,2,1));\n")
        self.part.Models()[0].m_Scale.x = 1e308
        self.assertIn('nonfinite transformed model envelope', '\n'.join(self.report()['issues']))

    def test_positive_unit_conversions_and_rigid_transforms_remain_valid(self):
        model = self.part.Models()[0]
        model.m_Scale.x = 2.54; model.m_Scale.y = .5; model.m_Scale.z = .001
        model.m_Offset.x = .2; model.m_Offset.y = -.2; model.m_Offset.z = .3
        model.m_Rotation.x = 10; model.m_Rotation.y = 20; model.m_Rotation.z = 30
        self.assertTrue(self.report()['ok'], self.report()['issues'])

    def test_reviewed_terminal_envelope_uses_physical_dimensions_not_scale_literals(self):
        terminal = self.add_part('J410', 30, 35, footprint='M3_DB125_4P_GN')
        model = self.folder / 'terminal.step'
        # T0-1/D-R11-01 maximum union; STEP's model y is opposite footprint y.
        model.write_text("#1=CARTESIAN_POINT('',(-8.32,-4,0));\n#2=CARTESIAN_POINT('',(7.2,4.1,8.9));\n")
        part_model = terminal.Models()[0]
        part_model.m_Filename = '${KIPRJMOD}/terminal.step'
        original = fit.model_box(terminal, self.folder)
        for scale in (.01, .99999):
            part_model.m_Scale.x = scale
            with self.assertRaisesRegex(ValueError, 'reviewed dimensions/pose'):
                fit.model_box(terminal, self.folder)
        part_model.m_Scale.x = 1.
        for shift in (.1, 3e-5):
            part_model.m_Offset.x = shift
            with self.assertRaisesRegex(ValueError, 'reviewed dimensions/pose'):
                fit.model_box(terminal, self.folder)
        part_model.m_Offset.x = 0.
        model.write_text("#1=CARTESIAN_POINT('',(-.00832,-.004,0));\n#2=CARTESIAN_POINT('',(.0072,.0041,.0089));\n")
        for axis in ('x', 'y', 'z'):
            setattr(part_model.m_Scale, axis, 1000.)
        for actual, expected in zip(fit.model_box(terminal, self.folder), original):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_c84_conservative_envelope_and_equivalent_units(self):
        capacitor = self.add_part('C84', 27.5, 78.5, footprint='M3_MA_8x10')
        model = self.folder / 'capacitor.step'
        model.write_text("#1=CARTESIAN_POINT('',(-4.25,-4.25,0));\n#2=CARTESIAN_POINT('',(4.25,4.25,10.8));\n")
        item = capacitor.Models()[0]; item.m_Filename = '${KIPRJMOD}/capacitor.step'
        original = fit.model_box(capacitor, self.folder)
        self.assertTrue(self.report()['ok'], self.report()['issues'])
        for scale in (.01, .99999):
            with self.subTest(scale=scale):
                for axis in ('x', 'y', 'z'):
                    setattr(item.m_Scale, axis, scale)
                with self.assertRaisesRegex(ValueError, 'reviewed dimensions/pose'):
                    fit.model_box(capacitor, self.folder)
        for axis in ('x', 'y', 'z'):
            setattr(item.m_Scale, axis, 1.)
        for offset, reject in ((1.9e-5, False), (2.1e-5, True)):
            with self.subTest(offset=offset):
                item.m_Offset.z = offset
                if reject:
                    with self.assertRaisesRegex(ValueError, 'reviewed dimensions/pose'):
                        fit.model_box(capacitor, self.folder)
                else:
                    self.assertIsNotNone(fit.model_box(capacitor, self.folder))
        item.m_Offset.z = 0.
        model.write_text("#1=CARTESIAN_POINT('',(-.00425,-.00425,0));\n#2=CARTESIAN_POINT('',(.00425,.00425,.0108));\n")
        for axis in ('x', 'y', 'z'):
            setattr(item.m_Scale, axis, 1000.)
        for actual, expected in zip(fit.model_box(capacitor, self.folder), original):
            self.assertAlmostEqual(actual, expected, places=6)
        self.assertTrue(self.report()['ok'], self.report()['issues'])

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

    def test_bare_or_unfitted_bottom_pad_must_clear_support_hardware(self):
        # P3-MECHANICAL-04: a bottom test pad (a board feature) and an unfitted bottom land count in the 3.5 mm rule
        pad = self.add_test_pad(8.3, 46)
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.B_Cu); layers.AddLayer(pcbnew.B_Mask)
        pad.SetLayerSet(layers)
        pad.SetPosition(self.point(8.1, 46))
        self.assertTrue(self.report()['ok'], self.report()['issues'])
        pad.SetPosition(self.point(7.9, 46))
        self.assertIn('TP1.1 exposed bottom pad', '\n'.join(self.report()['issues']))
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.B_Cu)              # tented: not exposed
        pad.SetLayerSet(layers)
        self.assertTrue(self.report()['ok'], self.report()['issues'])
        dnp = self.add_part('C9', 7.9, 46, model=False)
        dnp.SetAttributes(pcbnew.FP_SMD | pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM)
        land = pcbnew.PAD(dnp); land.SetNumber('1'); land.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        land.SetSize(self.point(1, 1)); land.SetShape(pcbnew.PAD_SHAPE_RECT)
        lay = pcbnew.LSET(); lay.AddLayer(pcbnew.B_Cu); lay.AddLayer(pcbnew.B_Mask); land.SetLayerSet(lay)
        dnp.Add(land); land.SetPosition(self.point(7.9, 46))
        self.assertIn('C9.1 exposed bottom pad', '\n'.join(self.report()['issues']))

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
        self.add_part('J30', 30, 30, footprint='M3_SMA_KH_KE8_EDGE')
        with patch.dict(fit.MATED, {}, clear=True):
            self.assertIn('J30: mated housing/wire envelope', '\n'.join(self.report()['issues']))

    def test_sma_mated_plug_envelope_lies_beyond_the_aft_edge(self):
        jack = self.add_part('J30', 12.85, 0, footprint='M3_SMA_KH_KE8_EDGE')
        box = fit.footprint_box(jack, fit.MATED['M3_SMA_KH_KE8_EDGE']['box'])
        self.assertAlmostEqual(box[1], -25.5)            # the plug reaches 25.5 mm beyond the edge
        self.assertAlmostEqual(box[3], 0.0)
        self.assertAlmostEqual(box[0], 12.85 - 4.6)
        self.assertGreater(fit.margin(box, 24.9, 23.0, 0.3), 0)

    DB125 = {'J1': 'M3_DB125_2P_GN', 'J121': 'M3_DB125_2P_BK', 'J400': 'M3_DB125_2P_GN', 'J410': 'M3_DB125_4P_GN',
             'J420': 'M3_DB125_4P_GN', 'J9': 'M3_DB125_4P_GN', 'J122': 'M3_DB125_5P_GN'}

    def test_r10_wire_room_lists_every_db125_terminal(self):
        """R18-MEC-03: the R10 report and printout give the wire room of all seven DB125 terminals (the west entry
        face is the box's x0, the east one its x1), not only J1 / J121 / J9."""
        rows = []
        for i, (ref, name) in enumerate(self.DB125.items()):
            west = ref in ('J1', 'J121', 'J400')
            self.add_part(ref, 7.4 if west else 38.6, 10 + 10 * i, model=False, footprint=name)
            rows.append((1.0, ref, 'F', (3.4, 8 + 10 * i, 11.5, 12 + 10 * i, 0, 8.9) if west
                         else (34.5, 8 + 10 * i, 42.6, 12 + 10 * i, 0, 8.9)))
        rows.append((1.0, 'J1.1 terminal tail', 'B', (6.4, 9, 8.4, 11, -3.8, -1.6)))
        rooms = fit.wire_rooms(self.board, rows, 'r10', 23.0, 0.3)
        self.assertEqual(sorted(rooms), sorted(self.DB125))
        wall = math.sqrt(fit.BORE_R ** 2 - fit.WIRE_Z ** 2)
        self.assertAlmostEqual(rooms['J400'][0], wall - (23.0 - 3.4) - 0.3, places=3)
        self.assertAlmostEqual(rooms['J420'][1], wall - (42.6 - 23.0) + 0.3, places=3)
        self.assertEqual(fit.wire_rooms(self.board, rows, 'r9', 23.0, 0.3), {})     # R9 lists its DB128 entries only

    def test_real_r10_board_reports_seven_wire_rooms(self):
        board = Path(os.environ.get('R10_BOARD') or
                     Path(__file__).resolve().parents[1] / 'm3_design/assembly_review/m3.kicad_pcb')
        if not board.is_file() or 'M3-ASSY-R10' not in board.read_text()[:20000]:
            self.skipTest('no R10 board')
        report = fit.check_board(pcbnew.LoadBoard(str(board)), board.parent, profile='r10')
        self.assertEqual(sorted(report['wire_room_mm']), sorted(self.DB125))
        self.assertGreaterEqual(min(low for low, _ in report['wire_room_mm'].values()), 4.95 - 1e-3)

    def test_thickness_and_invalid_bore_assumptions_are_rejected(self):
        self.board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(2))
        self.assertIn('thickness differs', '\n'.join(self.report()['issues']))
        with self.assertRaises(ValueError):
            fit.check_board(self.board, self.folder, tol=-0.3)


if __name__ == '__main__':
    unittest.main()
