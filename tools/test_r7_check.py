"""Native geometric regressions for the R7 contract (check_r7), including the R7 legends and RF strip."""
from pathlib import Path
import sys
import unittest

try:
    import pcbnew
except ImportError:
    pcbnew = None
if pcbnew:
    import check_r7 as gate


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R7Geometry(unittest.TestCase):
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
                      'J2 1:3V3 2:SWDIO 3:NRST 4:SWCLK 5:GND 6:NC'):
            text = pcbnew.PCB_TEXT(self.board); text.SetText(value)
            text.SetLayer(pcbnew.F_SilkS); self.board.Add(text); texts.append(text)
        self.assertFalse(gate.pin_legends(self.board))
        texts[0].SetText('J9 1:5V 2:GND 3:RX 4:TX')
        self.assertEqual(len(gate.pin_legends(self.board)), 2)

    def test_sma_legends_must_sit_at_their_own_jack(self):
        for ref, x in (('J30', 12.85), ('J31', 31.54)):
            f = pcbnew.FOOTPRINT(self.board); f.SetReference(ref); self.board.Add(f)
            f.SetPosition(self.point(x, 0))
        texts = []
        for word, x in (('GNSS', 12.85), ('RADIO', 31.54)):
            text = pcbnew.PCB_TEXT(self.board); text.SetText(word); text.SetLayer(pcbnew.F_SilkS)
            text.SetPosition(self.point(x, 6)); self.board.Add(text); texts.append(text)
        jacks = lambda: [i for i in gate.pin_legends(self.board) if i.startswith(('J30', 'J31'))]  # noqa: E731
        self.assertFalse(jacks())
        texts[0].SetPosition(self.point(31.54, 8))       # GNSS beside the radio jack
        self.assertIn('J30', '\n'.join(jacks()))

    def test_a_part_legend_sits_beside_its_part(self):
        # fix pass 7: 'J124: 5A FAST / 2S' had landed 73 mm from J124, and a legend may not name a part the board lacks
        self.pad('J124', 10, 90)
        text = pcbnew.PCB_TEXT(self.board); text.SetText('J124: 5A FAST / 2S'); text.SetLayer(pcbnew.B_SilkS)
        text.SetPosition(self.point(10, 94)); self.board.Add(text)
        word = pcbnew.PCB_TEXT(self.board); word.SetText('ARM'); word.SetLayer(pcbnew.F_SilkS)
        word.SetPosition(self.point(10, 87)); self.board.Add(word)
        rev = pcbnew.PCB_TEXT(self.board); rev.SetText('M3-ASSY-R7'); rev.SetLayer(pcbnew.B_SilkS)
        rev.SetPosition(self.point(30, 30)); self.board.Add(rev)       # not about a part: never checked
        self.assertEqual(gate.legend_subjects(self.board), [])
        text.SetPosition(self.point(27, 22))
        self.assertIn('J124', '\n'.join(gate.legend_subjects(self.board)))
        text.SetPosition(self.point(10, 94))
        text.SetText('J130 3V3 / RX-TX AT MODULE')
        self.assertIn('not on the board', '\n'.join(gate.legend_subjects(self.board)))

    def test_rf_strip_rejects_foreign_copper(self):
        t = self.track((5, 10), (8, 10), net='SIGNAL')
        t.SetLayer(pcbnew.In1_Cu)
        self.assertIn('track of SIGNAL', '\n'.join(gate.rf_strip(self.board)[0]))
        t.SetNet(self.board.FindNet('GND'))
        self.assertNotIn('track of', '\n'.join(gate.rf_strip(self.board)[0]))
        t.Move(self.point(0, 20))                        # forward of the strip: anything goes
        t.SetNet(self.board.FindNet('SIGNAL'))
        self.assertNotIn('track of', '\n'.join(gate.rf_strip(self.board)[0]))


    # --- pass 2 additions (fix2_F1) ---------------------------------------------------------------------------------
    def via(self, x, y, net='SIGNAL', d=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(self.board); v.SetPosition(self.point(x, y)); v.SetWidth(pcbnew.FromMM(d))
        v.SetDrill(pcbnew.FromMM(drill)); v.SetNet(self.board.FindNet(net)); self.board.Add(v); return v

    def smd(self, ref, x, y, net='SIGNAL', size=(0.8, 0.95), paste=True, attrs=0):
        f = pcbnew.FOOTPRINT(self.board); f.SetReference(ref); self.board.Add(f)
        p = pcbnew.PAD(f); p.SetNumber('1'); p.SetShape(pcbnew.PAD_SHAPE_RECTANGLE)
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetSize(self.point(*size)); p.SetNet(self.board.FindNet(net))
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); layers.AddLayer(pcbnew.F_Mask)
        if paste:
            layers.AddLayer(pcbnew.F_Paste)
        p.SetLayerSet(layers); f.Add(p); p.SetPosition(self.point(x, y))
        if attrs:
            f.SetAttributes(f.GetAttributes() | attrs)
        return f, p

    def test_via_hole_in_or_near_a_soldered_pad_rejected(self):
        self.smd('R1', 0, 0)                                  # pad spans y -0.475..0.475
        v = self.via(0, -0.4, net='SIGNAL')                   # hole inside the opening (DFM-01's R100.1 case)
        self.assertTrue(gate.vias_in_smd_pads(self.board)[0])
        v.SetPosition(self.point(0, -0.70))                   # hole edge 0.075 mm from the opening: still too near
        self.assertTrue(gate.vias_in_smd_pads(self.board)[0])
        v.SetPosition(self.point(0, -0.75))                   # hole edge 0.125 mm away
        self.assertFalse(gate.vias_in_smd_pads(self.board)[0])

    def test_via_in_a_bare_test_pad_is_exempt(self):
        self.smd('TP5', 0, 0, size=(1.5, 1.5), paste=False)
        self.via(0, 0)
        self.assertFalse(gate.vias_in_smd_pads(self.board)[0])

    def test_unfitted_placeholder_carries_no_paste(self):
        dnp = pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM
        self.smd('C9', 0, 0, attrs=dnp)
        self.assertTrue(gate.dnp_paste(self.board))
        self.board.Remove(self.board.FindFootprintByReference('C9'))
        self.smd('C9', 0, 0, attrs=dnp, paste=False)
        self.assertFalse(gate.dnp_paste(self.board))
        self.smd('C10', 3, 0, attrs=pcbnew.FP_DNP)            # owner-fitted DNP (still in the BOM) keeps its paste
        self.assertFalse(gate.dnp_paste(self.board))

    def test_rf_ground_pads_solid_with_a_via_beside(self):
        f = pcbnew.FOOTPRINT(self.board); f.SetReference('D30'); self.board.Add(f)
        pad = pcbnew.PAD(f); pad.SetNumber('2'); pad.SetShape(pcbnew.PAD_SHAPE_RECTANGLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD); pad.SetSize(self.point(0.35, 0.6))
        pad.SetNet(self.board.FindNet('GND'))
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); layers.AddLayer(pcbnew.F_Mask); pad.SetLayerSet(layers)
        f.Add(pad); pad.SetPosition(self.point(10, 10))
        pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        found = [i for i in gate.rf_grounds(self.board, '')[0] if i.startswith('D30.2')]
        self.assertTrue(any('solid' in i for i in found) and any('no GND via' in i for i in found))
        pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        self.via(10, 10.3 + 0.16 + 0.3, net='GND')            # 0.16 mm from the pad edge
        self.assertFalse([i for i in gate.rf_grounds(self.board, '')[0] if i.startswith('D30.2')])

    def test_small_rf_ground_pad_is_exempt_from_the_relief_policy(self):
        f = pcbnew.FOOTPRINT(self.board); f.SetReference('C303'); self.board.Add(f)
        for num, x, net in (('1', 0, 'SIGNAL'), ('2', 0.84, 'GND')):
            q = pcbnew.PAD(f); q.SetNumber(num); q.SetShape(pcbnew.PAD_SHAPE_RECTANGLE)
            q.SetAttribute(pcbnew.PAD_ATTRIB_SMD); q.SetSize(self.point(0.5, 0.54)); q.SetNet(self.board.FindNet(net))
            layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); q.SetLayerSet(layers); f.Add(q)
            q.SetPosition(self.point(x, 0))
            if net == 'GND':
                q.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        rules = '(constraint thermal_relief_gap (min 0.25mm)) (constraint thermal_spoke_width (min 0.3mm))'
        self.assertFalse(gate.thermal_policy(self.board, rules)[0])

    def test_fence_pitch_only_opens_at_the_named_openings(self):
        xs = [0.9 + 2.0 * k for k in range(23) if not (6.0 < 0.9 + 2.0 * k < 12.7 or 19.7 < 0.9 + 2.0 * k < 24.1)]
        xs += [6.3, 12.4, 20.0, 23.8, 45.1]
        for x in xs:
            self.via(x, gate.FENCE_Y, net='GND')
        self.assertFalse([i for i in gate.rf_stitching(self.board)[0] if i.startswith('strip fence')])
        self.board.Remove(next(t for t in self.board.GetTracks() if abs(pcbnew.ToMM(t.GetPosition().x) - 28.9) < 1e-3))
        self.assertTrue([i for i in gate.rf_stitching(self.board)[0] if i.startswith('strip fence')])

    def test_u31_body_keepout_on_bcu_and_in2(self):
        self.assertEqual(len(gate.u31_body_keepout(self.board)), 2)
        x0, y0, x1, y1 = gate.U31_BODY
        z = pcbnew.ZONE(self.board); z.SetIsRuleArea(True); z.SetZoneName('U31_KEEPOUT')
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.B_Cu); ls.AddLayer(pcbnew.In2_Cu); z.SetLayerSet(ls)
        o = z.Outline(); o.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        self.assertFalse(gate.u31_body_keepout(self.board))

    def test_in1_ground_under_rf_tracks(self):
        t = self.track((10, 6), (10, 9), net='SIGNAL', width=0.3)
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'GNSS_RF_IN')); t.SetNet(self.board.FindNet('GNSS_RF_IN'))
        z = pcbnew.ZONE(self.board); z.SetNet(self.board.FindNet('GND')); z.SetLayer(pcbnew.In1_Cu)
        o = z.Outline(); o.NewOutline()
        for x, y in ((9, 5), (11, 5), (11, 7.4), (9, 7.4)):          # stops short of the track's far end
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        self.assertTrue([i for i in gate.rf_stitching(self.board)[0] if i.startswith('In1:')])
        o.RemoveAllContours(); o.NewOutline()
        for x, y in ((9, 5), (11, 5), (11, 10), (9, 10)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        self.assertFalse([i for i in gate.rf_stitching(self.board)[0] if i.startswith('In1:')])

    def test_stitching_gap_beside_an_rf_line(self):
        for net in ('GNSS_RF_ANT', 'GNSS_RF_IN'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
        for ref, num, net, x, y in (('J30', '5', 'GNSS_RF_ANT', 12.85, 2.3), ('U30', '11', 'GNSS_RF_IN', 12.85, 10.2)):
            f = pcbnew.FOOTPRINT(self.board); f.SetReference(ref); self.board.Add(f)
            q = pcbnew.PAD(f); q.SetNumber(num); q.SetShape(pcbnew.PAD_SHAPE_RECTANGLE)
            q.SetAttribute(pcbnew.PAD_ATTRIB_SMD); q.SetSize(self.point(0.8, 1.8 if ref == 'U30' else 4.2))
            q.SetNet(self.board.FindNet(net))
            layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); q.SetLayerSet(layers); f.Add(q)
            q.SetPosition(self.point(x, y))
        self.track((12.85, 2.3), (12.85, 6.0), net='GNSS_RF_ANT', width=0.3)
        self.track((12.85, 6.0), (12.85, 10.2), net='GNSS_RF_IN', width=0.3)
        for y in (5.0, 7.0, 9.0):                          # the line runs y 4.4 (jack pad end) to 9.3 (module pad)
            self.via(11.85, y, net='GND'); self.via(13.85, y, net='GND')
        gaps = lambda: [i for i in gate.rf_stitching(self.board)[0] if i.startswith('GNSS')]  # noqa: E731
        self.assertFalse(gaps())
        self.board.Remove(next(t for t in self.board.GetTracks() if t.GetClass() == 'PCB_VIA'
                               and abs(pcbnew.ToMM(t.GetPosition().x) - 13.85) < 1e-3
                               and abs(pcbnew.ToMM(t.GetPosition().y) - 7.0) < 1e-3))
        self.assertIn('GNSS east', '\n'.join(gaps()))         # 4.0 mm gap, over the 2.7 mm accepted ceiling


    # --- fix pass 3: RF-part filter, launch reference, strip GND reach ------------------------------------------------
    def test_rf_part_filter_covers_the_limiter_transistors(self):
        for ref in ('Q30', 'Q31', 'Q32', 'R300', 'C304', 'D30', 'L30', 'FB31', 'TP30', 'U31', 'J30'):
            self.assertTrue(gate.RF_PART.fullmatch(ref), ref)
        for ref in ('C30', 'R32', 'U1', 'Q124'):
            self.assertFalse(gate.RF_PART.fullmatch(ref), ref)

    def test_rf_part_coverage_flags_a_radio_part_outside_the_filter(self):
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'RADIO_BUSY'))
        self.pad('Q30', 0, 0, net='RADIO_BUSY')
        self.assertFalse(gate.rf_part_coverage(self.board))
        self.pad('X9', 5, 0, net='RADIO_BUSY')
        self.assertIn('X9', '\n'.join(gate.rf_part_coverage(self.board)))

    def test_c304_is_in_the_dnp_contract(self):
        self.assertIn('C304', gate.DNP)

    def zone(self, net, layer, pts, minw=0.15, fill=True):
        z = pcbnew.ZONE(self.board); z.SetNet(self.board.FindNet(net)); z.SetLayer(layer)
        z.SetMinThickness(pcbnew.FromMM(minw)); z.SetLocalClearance(pcbnew.FromMM(0.15))
        o = z.Outline(); o.NewOutline()
        for x, y in pts:
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        if fill:
            pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        return z

    def test_launch_reference_needs_in2_gnd_under_the_cut_out(self):
        ra = pcbnew.ZONE(self.board); ra.SetIsRuleArea(True); ra.SetZoneName('R7_J30_launch_In1')
        ra.SetLayer(pcbnew.In1_Cu); ra.SetDoNotAllowZoneFills(True)
        o = ra.Outline(); o.NewOutline()
        for x, y in ((11.95, 0.0), (13.75, 0.0), (13.75, 4.6), (11.95, 4.6)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(ra)
        z = self.zone('GND', pcbnew.In2_Cu, ((10, 0.3), (16, 0.3), (16, 3.0), (10, 3.0)))     # stops at y 3.0
        self.assertTrue(gate.launch_reference(self.board)[0])
        o = z.Outline(); o.RemoveAllContours(); o.NewOutline()
        for x, y in ((10, 0.3), (16, 0.3), (16, 6.0), (10, 6.0)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        self.assertFalse(gate.launch_reference(self.board)[0])

    def test_ground_under_the_radio_module_on_both_inner_layers(self):
        self.zone('GND', pcbnew.In1_Cu, ((0.3, 0.3), (45.7, 0.3), (45.7, 23.5), (0.3, 23.5)), fill=False)
        z2 = self.zone('GND', pcbnew.In2_Cu, ((0.3, 0.3), (30, 0.3), (30, 23.5), (0.3, 23.5)))   # stops under U31
        self.assertIn('U31 body: In2.Cu', '\n'.join(gate.module_ground(self.board)[0]))
        o = z2.Outline(); o.RemoveAllContours(); o.NewOutline()
        for x, y in ((0.3, 0.3), (45.7, 0.3), (45.7, 23.5), (0.3, 23.5)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        self.assertFalse(gate.module_ground(self.board)[0])

    def test_strip_gnd_finger_without_a_via_fails_and_passes_with_one(self):
        # a 0.4 mm wide, 9 mm long F.Cu GND finger off a stitched square in the strip
        self.zone('GND', pcbnew.F_Cu, ((2, 2), (6, 2), (6, 6), (4.2, 6), (4.2, 15), (3.8, 15), (3.8, 6), (2, 6)), minw=0.1)
        self.via(4, 4, net='GND')
        issues = gate.rf_gnd_reach(self.board)[0]
        self.assertTrue([i for i in issues if i.startswith('F.Cu')], issues)
        self.via(4, 11.5, net='GND')
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        self.assertFalse([i for i in gate.rf_gnd_reach(self.board)[0] if i.startswith('F.Cu')])


if __name__ == '__main__':
    unittest.main()
