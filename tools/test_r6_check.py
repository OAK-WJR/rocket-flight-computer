"""Native geometric regressions for failures KiCad connectivity alone can miss."""
from pathlib import Path
import sys
import unittest

try:
    import pcbnew
except ImportError:
    pcbnew = None
if pcbnew:
    import check_r6 as gate


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R6Geometry(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.BOARD()
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'GND'))
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'SIGNAL'))
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'RAW_ACT'))

    def point(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def pad(self, ref, x, y, net='SIGNAL', pth=False):
        f = pcbnew.FOOTPRINT(self.board); f.SetReference(ref); self.board.Add(f)
        p = pcbnew.PAD(f); p.SetNumber('1'); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        p.SetAttribute(pcbnew.PAD_ATTRIB_PTH if pth else pcbnew.PAD_ATTRIB_SMD)
        p.SetSize(self.point(1.5, 1.5)); p.SetNet(self.board.FindNet(net))
        layers = pcbnew.LSET.AllCuMask() if pth else pcbnew.LSET()
        layers.AddLayer(pcbnew.F_Cu); layers.AddLayer(pcbnew.F_Mask); p.SetLayerSet(layers)
        if pth: p.SetDrillSize(self.point(0.8, 0.8))
        f.Add(p); p.SetPosition(self.point(x, y))
        return p

    def track(self, a, b, net='SIGNAL', width=0.2):
        t = pcbnew.PCB_TRACK(self.board); t.SetStart(self.point(*a)); t.SetEnd(self.point(*b))
        t.SetWidth(pcbnew.FromMM(width)); t.SetLayer(pcbnew.F_Cu)
        t.SetNet(self.board.FindNet(net)); self.board.Add(t); return t

    def guards(self):
        return gate.foreign_clearances(self.board, gate.copper_shapes(self.board))[0]

    def joints(self):
        return gate.overlap_only_joints(self.board, gate.copper_shapes(self.board))[0]

    def test_duplicate_uuid_across_track_and_rule_area_rejected(self):
        track = self.track((0, 0), (1, 0))
        zone = pcbnew.ZONE(self.board)
        zone.SetIsRuleArea(True)
        zone.SetUuid(pcbnew.KIID(track.m_Uuid.AsString()))
        self.board.Add(zone)
        self.assertTrue(gate.duplicate_ids(self.board))
        zone.SetUuid(pcbnew.KIID())
        self.assertFalse(gate.duplicate_ids(self.board))

    def test_testpad_foreign_track_rejects_but_same_net_passes(self):
        self.pad('TP1', 0, 0)
        t = self.track((-2, 1.7), (2, 1.7), net='GND')
        self.assertTrue(self.guards())
        t.SetNet(self.board.FindNet('SIGNAL'))
        self.assertFalse(self.guards())

    def test_testpad_exact_clearance_passes(self):
        self.pad('TP1', 0, 0)
        self.track((-2, 1.85), (2, 1.85), net='GND')
        self.assertFalse(self.guards())

    def test_tag_connect_clearance_exempts_only_its_adjacent_contacts(self):
        p = self.pad('J2', 0, 0)
        p.SetAttribute(pcbnew.PAD_ATTRIB_CONN)
        p.SetSize(self.point(0.7874, 0.7874))
        adjacent = pcbnew.PAD(p.GetParentFootprint())
        adjacent.SetNumber('2'); adjacent.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        adjacent.SetAttribute(pcbnew.PAD_ATTRIB_CONN)
        adjacent.SetSize(self.point(0.7874, 0.7874)); adjacent.SetLayerSet(p.GetLayerSet())
        adjacent.SetNet(self.board.FindNet('GND')); p.GetParentFootprint().Add(adjacent)
        adjacent.SetPosition(self.point(1.27, 0))
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); layers.AddLayer(pcbnew.F_Mask)
        p.SetLayerSet(layers); adjacent.SetLayerSet(layers)
        self.assertFalse(self.guards())
        t = self.track((-1, -0.99), (1, -0.99), 'GND')
        self.assertIn('0.508 mm', '\n'.join(self.guards()))
        t.Move(self.point(0, -0.02))
        self.assertFalse(self.guards())

    def test_foreign_filled_zone_is_checked(self):
        self.pad('TP1', 0, 0)
        zone = pcbnew.ZONE(self.board); zone.SetLayer(pcbnew.F_Cu)
        zone.SetNet(self.board.FindNet('GND')); zone.SetZoneName('ground')
        outline = zone.Outline(); outline.NewOutline()
        for x, y in ((-2, 1.6), (2, 1.6), (2, 3), (-2, 3)):
            outline.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        zone.SetFilledPolysList(pcbnew.F_Cu, outline); zone.SetIsFilled(True); self.board.Add(zone)
        self.assertIn('zone ground', '\n'.join(self.guards()))

    def test_tag_connect_requires_mask_opening_and_no_paste(self):
        p = self.pad('J2', 0, 0)
        p.SetAttribute(pcbnew.PAD_ATTRIB_CONN)
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu)
        p.SetLayerSet(layers)
        self.assertIn('exposed front copper', '\n'.join(self.guards()))
        layers.AddLayer(pcbnew.F_Mask); layers.AddLayer(pcbnew.F_Paste)
        p.SetLayerSet(layers)
        self.assertIn('no solder paste', '\n'.join(self.guards()))
        layers.RemoveLayer(pcbnew.F_Paste); p.SetLayerSet(layers)
        self.assertFalse(self.guards())

    def test_raw_pth_clearance_to_foreign_track(self):
        self.pad('J1', 0, 0, 'RAW_ACT', pth=True)
        self.track((-2, 1.1), (2, 1.1), 'GND')
        self.assertIn('0.3 mm', '\n'.join(self.guards()))

    def test_via_copper_overlap_with_pth_rejected(self):
        self.pad('J1', 0, 0, pth=True)
        via = pcbnew.PCB_VIA(self.board); via.SetPosition(self.point(0.9, 0))
        via.SetWidth(pcbnew.FromMM(0.5)); via.SetDrill(pcbnew.FromMM(0.25)); self.board.Add(via)
        self.assertTrue(gate.vias_on_through_pads(self.board))
        via.SetPosition(self.point(1.01, 0))
        self.assertFalse(gate.vias_on_through_pads(self.board))

    def test_overlap_only_track_joint_rejected(self):
        self.track((0, 0), (1, 0))
        self.track((1.1, 0), (1.1, 1))
        self.assertTrue(self.joints())

    def test_exact_t_joint_and_pad_contained_joint_pass(self):
        self.track((0, 0), (2, 0)); self.track((1, 0), (1, 1))
        self.assertFalse(self.joints())
        self.pad('R1', 3, 0)
        self.track((3.5, 0), (4, 0))
        self.assertFalse(self.joints())

    def test_direct_bypass_requires_physical_track_path(self):
        a = self.pad('U3', 0, 0); b = self.pad('C29', 1.9, 0)
        self.assertIsNone(gate.direct_route(self.board, a, b))
        self.track((0, 0), (1.9, 0))
        self.assertAlmostEqual(gate.direct_route(self.board, a, b), 1.9)

    def camera_bypass_fixture(self):
        for net in ('3V3', 'CAM_IO_3V3'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
        def footprint(ref, value, specs):
            f = pcbnew.FOOTPRINT(self.board); f.SetReference(ref); f.SetValue(value)
            f.SetLayer(pcbnew.B_Cu); self.board.Add(f)
            for number, x, y, net in specs:
                p = pcbnew.PAD(f); p.SetNumber(number); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
                p.SetShape(pcbnew.PAD_SHAPE_RECT); p.SetSize(self.point(.3, .3))
                layers = pcbnew.LSET(); layers.AddLayer(pcbnew.B_Cu); p.SetLayerSet(layers)
                p.SetNet(self.board.FindNet(net)); f.Add(p); p.SetPosition(self.point(x, y))
            return f
        footprint('U12', 'TXU0202DCUR', [('3', 0, 0, '3V3'), ('2', .84, 0, 'GND'),
                                      ('7', 0, -3, 'CAM_IO_3V3')])
        cap = footprint('C100', '100nF 50V X7R 10%', [('1', 0, 1.5, '3V3'), ('2', .84, 1.5, 'GND')])
        footprint('C93', '100nF 50V X7R 10%', [('1', 0, -4.5, 'CAM_IO_3V3'), ('2', .84, -4.5, 'GND')])
        links = []
        for a, b, net in [((0, 0), (0, 1.5), '3V3'), ((.84, 0), (.84, 1.5), 'GND'),
                          ((0, -3), (0, -4.5), 'CAM_IO_3V3')]:
            t = self.track(a, b, net); t.SetLayer(pcbnew.B_Cu); links.append(t)
        return cap, links

    def test_camera_bypass_rejects_remote_or_missing_capacitor(self):
        cap, _ = self.camera_bypass_fixture()
        self.assertFalse(gate.camera_bypass(self.board)[0])
        cap.Move(self.point(0, 8))
        self.assertIn('local bypass', '\n'.join(gate.camera_bypass(self.board)[0]))
        self.board.Delete(cap)
        self.assertIn('missing', '\n'.join(gate.camera_bypass(self.board)[0]))

    def test_camera_bypass_requires_actual_supply_and_ground_paths(self):
        _, links = self.camera_bypass_fixture()
        self.board.Delete(links[0])
        self.assertIn('local bypass', '\n'.join(gate.camera_bypass(self.board)[0]))
        self.board.Delete(links[1])
        self.assertIn('local GND return', '\n'.join(gate.camera_bypass(self.board)[0]))

    def test_camera_bypass_rejects_wrong_value_or_rail(self):
        cap, _ = self.camera_bypass_fixture()
        cap.SetValue('1uF')
        self.assertIn('must be 100nF', '\n'.join(gate.camera_bypass(self.board)[0]))
        cap.SetValue('100nF'); cap.FindPadByNumber('1').SetNet(self.board.FindNet('CAM_IO_3V3'))
        self.assertIn('3V3 to GND', '\n'.join(gate.camera_bypass(self.board)[0]))

    def test_bypass_copper_path_can_include_a_short_via_transition(self):
        cap, links = self.camera_bypass_fixture()
        self.board.Delete(links[0])
        a = self.board.FindFootprintByReference('U12').FindPadByNumber('3')
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu)
        cap.FindPadByNumber('1').SetLayerSet(layers)
        t = self.track((0, 0), (0, 1.5), '3V3')
        via = pcbnew.PCB_VIA(self.board); via.SetPosition(self.point(0, 0))
        via.SetWidth(pcbnew.FromMM(.5)); via.SetDrill(pcbnew.FromMM(.3))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(self.board.FindNet('3V3'))
        self.board.Add(via)
        self.assertIsNone(gate.direct_route(self.board, a, cap.FindPadByNumber('1')))
        self.assertAlmostEqual(gate.direct_route(self.board, a, cap.FindPadByNumber('1'), True),
                               1.5 + pcbnew.ToMM(self.board.GetDesignSettings().GetBoardThickness()))

    def test_rule_minimum_not_only_optimum(self):
        self.assertTrue(gate.thermal_policy(self.board, '(constraint thermal_relief_gap (opt 0.25mm))')[0])
        rules = '(constraint thermal_relief_gap (min 0.25mm)) (constraint thermal_spoke_width (min 0.3mm))'
        self.assertFalse(gate.thermal_policy(self.board, rules)[0])

    def test_camera_legends_follow_peripheral_direction(self):
        texts = []
        for value in ('J9 1:5V 2:GND 3:TX 4:RX',
                      'J130 1:M0 2:M1 3:RX 4:TX 5:AUX 6:5V 7:GND',
                      'J131 1:5V 2:GND 3:TX 4:RX',
                      'J2 1:3V3 2:SWDIO 3:NRST 4:SWCLK 5:GND 6:NC'):
            text = pcbnew.PCB_TEXT(self.board); text.SetText(value)
            text.SetLayer(pcbnew.F_SilkS); self.board.Add(text); texts.append(text)
        self.assertFalse(gate.pin_legends(self.board))
        texts[0].SetText('J9 1:5V 2:GND 3:RX 4:TX')
        self.assertEqual(len(gate.pin_legends(self.board)), 2)


if __name__ == '__main__':
    unittest.main()
