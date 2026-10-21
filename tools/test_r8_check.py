"""Native geometric regressions for the R8 contract (check_r8): every R8 change and new check fires on a seeded defect."""
import copy
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
    import check_r8 as gate

NETS = ('GND', 'SIGNAL', '3V3', '3V3_RADIO', 'RAW_ACT', 'BAT_IN', 'PYRO1_BUS', 'PYRO1_OUT', 'PYRO1_GATE', 'PYRO1_GATE_N',
        'SERVO1_MCU', 'SERVO2_OUT', 'RADIO_NSS', 'RADIO_DIO1', 'RADIO_TXEN', 'RADIO_SCK_MCU', 'CAM_MCU_TX', 'LED_RED',
        'LED_RED_A', 'QSPI_CLK', 'GNSS_RF_IN', 'ARM1_SENSE', 'ACT_FET_S', 'PYRO1_IGN', 'BAT_SW_SOURCE',
        'BAT_SW_RETURN')


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R8Contract(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(4)
        for n in NETS:
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, n))

    # --- builders ------------------------------------------------------------------------------------------------------
    def P(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def outline(self, w=46, h=118):
        for a, b in (((0, 0), (w, 0)), ((w, 0), (w, h)), ((w, h), (0, h)), ((0, h), (0, 0))):
            s = pcbnew.PCB_SHAPE(self.board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
            s.SetStart(self.P(*a)); s.SetEnd(self.P(*b)); self.board.Add(s)

    def circle(self, x, y, r=1.6):
        s = pcbnew.PCB_SHAPE(self.board); s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetCenter(self.P(x, y)); s.SetEnd(self.P(x + r, y)); self.board.Add(s)
        return s

    def fp(self, ref, x=0, y=0, value=''):
        f = pcbnew.FOOTPRINT(self.board); f.SetReference(ref); f.SetValue(value); self.board.Add(f)
        f.SetPosition(self.P(x, y))
        return f

    def courtyard(self, f, w, h):
        """A w x h mm courtyard rectangle centred on the footprint."""
        c = f.GetPosition()
        s = pcbnew.PCB_SHAPE(f); s.SetShape(pcbnew.SHAPE_T_RECT); s.SetLayer(pcbnew.F_CrtYd)
        s.SetStart(pcbnew.VECTOR2I(c.x - pcbnew.FromMM(w / 2), c.y - pcbnew.FromMM(h / 2)))
        s.SetEnd(pcbnew.VECTOR2I(c.x + pcbnew.FromMM(w / 2), c.y + pcbnew.FromMM(h / 2)))
        s.SetWidth(pcbnew.FromMM(0.05)); f.Add(s); f.BuildCourtyardCaches()
        return f

    def pad(self, f, num, x, y, net=None, size=(0.6, 0.6), layer=None, pth=False):
        p = pcbnew.PAD(f); p.SetNumber(str(num)); p.SetShape(pcbnew.PAD_SHAPE_RECT)
        p.SetAttribute(pcbnew.PAD_ATTRIB_PTH if pth else pcbnew.PAD_ATTRIB_SMD); p.SetSize(self.P(*size))
        if pth:
            p.SetShape(pcbnew.PAD_SHAPE_CIRCLE); p.SetDrillSize(self.P(1.6, 1.6)); ls = pcbnew.LSET.AllCuMask()
        else:
            ls = pcbnew.LSET(); ls.AddLayer(layer if layer is not None else pcbnew.F_Cu)
        p.SetLayerSet(ls)
        if net:
            p.SetNet(self.board.FindNet(net))
        f.Add(p); p.SetPosition(self.P(x, y))
        return p

    def track(self, a, b, net='SIGNAL', width=0.2, layer=None):
        t = pcbnew.PCB_TRACK(self.board); t.SetStart(self.P(*a)); t.SetEnd(self.P(*b))
        t.SetWidth(pcbnew.FromMM(width)); t.SetLayer(pcbnew.F_Cu if layer is None else layer)
        t.SetNet(self.board.FindNet(net)); self.board.Add(t)
        return t

    def via(self, x, y, net='GND', d=0.6):
        v = pcbnew.PCB_VIA(self.board); v.SetPosition(self.P(x, y)); v.SetWidth(pcbnew.FromMM(d))
        v.SetDrill(pcbnew.FromMM(0.3)); v.SetNet(self.board.FindNet(net)); self.board.Add(v)
        return v

    def area(self, name, layers, box, tracks=False):
        z = pcbnew.ZONE(self.board); z.SetIsRuleArea(True); z.SetZoneName(name)
        ls = pcbnew.LSET(); [ls.AddLayer(lid) for lid in layers]; z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(False); z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        o = z.Outline(); o.NewOutline()
        x0, y0, x1, y1 = box
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        return z

    def zone(self, net, layer, box):
        z = pcbnew.ZONE(self.board); z.SetNet(self.board.FindNet(net)); z.SetLayer(layer)
        z.SetMinThickness(pcbnew.FromMM(0.15)); z.SetLocalClearance(pcbnew.FromMM(0.25))
        o = z.Outline(); o.NewOutline()
        x0, y0, x1, y1 = box
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        return z

    # --- pin table and pin map (D2, D3, D14) ---------------------------------------------------------------------------
    def test_the_pin_table_on_disk_is_consistent(self):
        rows = gate.load_pin_table()
        self.assertEqual(len(rows), 100)
        self.assertEqual(gate.pin_table_issues(rows), [])

    def test_pin_table_guards_fire(self):
        rows = gate.load_pin_table()
        for change, word in ((lambda r: r[2].update(r8_net='LED_RED'), 'contract pin 3'),
                             (lambda r: r[29].update(an2606_t135_loader_role='x'), 'loader-driven'),
                             (lambda r: r[27].update(r8_net='SWDIO'), 'more than one pin'),
                             (lambda r: r.pop(50), 'pins must be 1-100')):
            bad = copy.deepcopy(rows)
            change(bad)
            self.assertIn(word, '\n'.join(gate.pin_table_issues(bad)), word)

    def test_u1_pin_map_follows_the_table(self):
        u1 = self.fp('U1')
        self.pad(u1, 1, 0, 0, 'QSPI_CLK'); self.pad(u1, 2, 1, 0); self.pad(u1, 3, 2, 0, 'PYRO1_GATE_N')
        rows = [dict(pin='1', r8_net='QSPI_CLK'), dict(pin='2', r8_net='NC'), dict(pin='3', r8_net='PYRO1_GATE_N')]
        self.assertEqual(gate.u1_pin_map(self.board, rows), [])
        u1.FindPadByNumber('2').SetNet(self.board.FindNet('SIGNAL'))          # a sentinel with a net
        self.assertIn('U1.2: expected NC', '\n'.join(gate.u1_pin_map(self.board, rows)))
        u1.FindPadByNumber('2').SetNet(self.board.FindNet(''))
        rows[1]['r8_net'] = 'SIGNAL'                                           # the table may not give it one either
        self.assertIn('pyro sentinel', '\n'.join(gate.u1_pin_map(self.board, rows)))

    def test_r310_pulls_nss_to_3v3(self):
        r = self.fp('R310', value='100k')
        self.pad(r, 1, 0, 0, '3V3_RADIO'); self.pad(r, 2, 1, 0, 'RADIO_NSS')     # R7's rail
        self.assertIn('R310: must pull RADIO_NSS to 3V3', gate.pulls(self.board))
        r.FindPadByNumber('1').SetNet(self.board.FindNet('3V3'))
        self.assertFalse([i for i in gate.pulls(self.board) if i.startswith('R310')])
        self.fp('U1', 23, 45); self.fp('U31', 29.86, 14)                     # D4: at the MCU end of the lane
        r.SetPosition(self.P(25, 22))
        self.assertIn('R310: must sit at the U1 end of its lane (D4)', gate.pulls(self.board))
        r.SetPosition(self.P(25, 35))
        self.assertFalse([i for i in gate.pulls(self.board) if i.startswith('R310')])

    # --- RF strip ------------------------------------------------------------------------------------------------------
    def test_strip_no_longer_admits_nss_or_dio1_below_fcu(self):
        t = self.track((20, 15), (20, 17), 'RADIO_NSS', layer=pcbnew.B_Cu)
        self.via(32.4, 20.15, 'RADIO_DIO1')
        found = '\n'.join(gate.rf_strip(self.board)[0])
        self.assertIn('B.Cu track of RADIO_NSS', found)
        self.assertIn('via of RADIO_DIO1', found)
        t.SetNet(self.board.FindNet('RADIO_TXEN'))                            # TXEN's loop round U31 stays legal
        self.assertNotIn('track of RADIO_TXEN', '\n'.join(gate.rf_strip(self.board)[0]))

    def test_line_stitching_keeps_r7s_gaps_without_the_fence(self):
        # rf_line_stitching is R7's rf_stitching minus its fence part (fence() replaces that, D16)
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'GNSS_RF_ANT'))
        for ref, num, net, y, h in (('J30', '5', 'GNSS_RF_ANT', 2.3, 4.2), ('U30', '11', 'GNSS_RF_IN', 10.2, 1.8)):
            self.pad(self.fp(ref, 12.85, y), num, 12.85, y, net, size=(0.8, h))
        self.track((12.85, 2.3), (12.85, 6.0), 'GNSS_RF_ANT', width=0.3)
        self.track((12.85, 6.0), (12.85, 10.2), 'GNSS_RF_IN', width=0.3)
        for y in (5.0, 7.0, 9.0):
            self.via(11.85, y); self.via(13.85, y)
        gaps = lambda: [i for i in gate.rf_line_stitching(self.board)[0] if i.startswith('GNSS')]  # noqa: E731
        self.assertFalse(gaps())
        self.assertFalse([i for i in gate.rf_line_stitching(self.board)[0] if 'fence' in i])
        self.board.Remove(next(t for t in self.board.GetTracks() if t.GetClass() == 'PCB_VIA'
                               and abs(pcbnew.ToMM(t.GetPosition().x) - 13.85) < 1e-3
                               and abs(pcbnew.ToMM(t.GetPosition().y) - 7.0) < 1e-3))
        self.assertIn('GNSS east', '\n'.join(gaps()))                         # 4.0 mm, over the 2.7 mm ceiling

    def fence_board(self, gap=(20.0, 22.5), lane=True):
        self.outline()
        xs = [x for x in (1.0 + 2 * k for k in range(23)) if x < gap[0]] + list(gap)
        xs += [gap[1] + 2 * k for k in range(1, 13) if gap[1] + 2 * k <= 45]
        for x in xs:
            self.via(x, gate.r7.FENCE_Y)
        if lane:
            self.track((21.2, 20), (21.2, 27), 'RADIO_NSS')

    def fence_issues(self):
        return [i for i in gate.fence(self.board)[0]]

    def test_fence_opening_needs_a_lane_and_at_most_2_7_mm(self):
        self.fence_board()
        self.assertEqual(self.fence_issues(), [])
        self.assertEqual(gate.fence(self.board)[1]['openings'][0]['lanes'], ['RADIO_NSS'])
        self.setUp(); self.fence_board(lane=False)                            # a gap no lane needs
        self.assertIn('no lane', '\n'.join(self.fence_issues()))
        self.setUp(); self.fence_board(gap=(19.5, 22.5))                      # 3.0 mm: wider than D16 allows
        self.assertIn('3.00 mm wide', '\n'.join(self.fence_issues()))

    # --- D5 loader pins ------------------------------------------------------------------------------------------------
    def loader_board(self):
        rows = gate.load_pin_table()
        u1 = self.fp('U1')
        for k, port in enumerate(gate.LOADER_DRIVEN):                         # every loader-driven pin, NC
            self.pad(u1, next(r['pin'] for r in rows if r['port'] == port), k, 0)
        return u1, rows

    def loader_issues(self, rows):
        return gate.loader_pins(self.board, rows)[0]

    def test_loader_driven_pins_carry_only_their_d5_net_an_led_or_nothing(self):
        u1, rows = self.loader_board()
        self.assertEqual(self.loader_issues(rows), [])                        # both NC
        u1.FindPadByNumber('46').SetNet(self.board.FindNet('CAM_MCU_TX'))     # R7's camera UART on the loader port
        self.assertIn('PB10', '\n'.join(self.loader_issues(rows)))
        u1.FindPadByNumber('46').SetNet(self.board.FindNet('RADIO_SCK_MCU'))  # D2 / D5
        self.assertEqual(self.loader_issues(rows), [])
        u1.FindPadByNumber('30').SetNet(self.board.FindNet('LED_RED'))        # PA6 drives an LED through R32
        r = self.fp('R32'); self.pad(r, 1, 5, 0, 'LED_RED'); self.pad(r, 2, 6, 0, 'LED_RED_A')
        led = self.fp('LED1'); self.pad(led, 1, 8, 0, 'LED_RED_A'); self.pad(led, 2, 9, 0, 'GND')
        self.assertEqual(self.loader_issues(rows), [])
        self.board.Remove(led)                                                # the same net without an LED
        self.assertIn('PA6', '\n'.join(self.loader_issues(rows)))

    # --- D17 F10 separation --------------------------------------------------------------------------------------------
    def test_rf_part_keeps_5_mm_from_the_mcu_and_from_fast_lines(self):
        self.courtyard(self.fp('U1'), 16, 16)                                 # courtyard x -8..8
        r = self.courtyard(self.fp('R313', 11.0, 0), 1.0, 0.6); self.pad(r, 1, 11.0, 0, size=(0.5, 0.5))
        found = gate.rf_separation(self.board)                                # courtyards 2.5 mm apart
        self.assertRegex('\n'.join(found[0]), r'R313 is 2\.5\d mm from U1')       # to the courtyard's 0.01 mm
        r.SetPosition(self.P(14.0, 0))                                        # 5.5 mm
        self.assertFalse(gate.rf_separation(self.board)[0])
        self.track((14.0, 4.0), (20, 4.0), 'QSPI_CLK')                        # a fast line 3.6 mm from the courtyard
        self.assertIn('fast line QSPI_CLK', '\n'.join(gate.rf_separation(self.board)[0]))

    def test_switching_parts_are_restricted(self):
        sw = self.courtyard(self.fp('L1'), 3, 3); self.pad(sw, 1, 0, 0, size=(2, 2))
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'SW_NODE')); sw.Pads()[0].SetNet(self.board.FindNet('SW_NODE'))
        fb = self.courtyard(self.fp('FB30', 4, 0), 1.0, 1.0); self.pad(fb, 1, 4, 0, size=(0.6, 0.6))
        issues, ev = gate.rf_separation(self.board)
        self.assertIn('L1', ev['restricted'])
        self.assertRegex('\n'.join(issues), r'FB30 is 2\.0\d mm from L1')
        self.assertIn('FB30 is 2.50 mm from fast line SW_NODE', '\n'.join(issues))   # L1's switch-node pad edge x 1

    # --- D18 inner power near pyro -------------------------------------------------------------------------------------
    def test_inner_raw_or_bat_copper_keeps_2_5_mm_from_pyro_live_copper(self):
        self.track((0, 0), (10, 0), 'PYRO1_BUS', width=1.0)                   # F.Cu bus
        t = self.track((0, 2.6), (10, 2.6), 'RAW_ACT', width=0.5, layer=pcbnew.In2_Cu)   # 1.85 mm away in plan view
        self.assertIn('RAW_ACT track', '\n'.join(gate.inner_power_pyro(self.board)[0]))
        t.Move(self.P(0, 1.0))                                                # 2.85 mm
        self.assertFalse(gate.inner_power_pyro(self.board)[0])
        self.zone('BAT_IN', pcbnew.In2_Cu, (20, -5, 30, 5))                   # a BAT_IN plane under a PYRO1_OUT track
        self.track((22, 0), (28, 0), 'PYRO1_OUT')
        self.assertIn('BAT_IN zone', '\n'.join(gate.inner_power_pyro(self.board)[0]))

    def test_the_arm_terminals_own_raw_contact_is_exempt(self):
        j = self.fp('J124')
        self.pad(j, 1, 0, 0, 'PYRO1_BUS', size=(2.6, 2.6), pth=True)
        self.pad(j, 2, 5.08, 0, 'RAW_ACT', size=(2.6, 2.6), pth=True)        # 2.48 mm ring to ring
        self.assertFalse(gate.inner_power_pyro(self.board)[0])
        other = self.fp('J1'); self.pad(other, 1, 0, 5.08, 'RAW_ACT', size=(2.6, 2.6), pth=True)
        self.assertIn('J1.1', '\n'.join(gate.inner_power_pyro(self.board)[0]))

    # --- D85 battery-live copper beside the ARM bus and igniter (fix pass 1) ---------------------------------------------
    def test_battery_live_copper_keeps_1_mm_from_the_bus_igniter_and_drain(self):
        self.track((0, 0), (10, 0), 'PYRO1_BUS', width=1.0)                   # F.Cu bus
        t = self.track((0, 1.1), (10, 1.1), 'ACT_FET_S', width=0.2)           # 0.5 mm edge to edge, rule F's minimum
        self.assertIn('ACT_FET_S track', '\n'.join(gate.battery_pyro(self.board)[0]))
        t.SetLayer(pcbnew.B_Cu)                                               # another layer: not this rule's pair
        self.assertFalse(gate.battery_pyro(self.board)[0])
        t.SetLayer(pcbnew.F_Cu); t.Move(self.P(0, 0.6))                       # 1.1 mm
        self.assertFalse(gate.battery_pyro(self.board)[0])
        self.zone('BAT_IN', pcbnew.B_Cu, (20, -5, 30, 5))                     # a BAT_IN pour beside an igniter pad
        j = self.fp('J121'); self.pad(j, 2, 31.0, 0, 'PYRO1_IGN', size=(1.0, 1.0), pth=True)
        self.assertIn('BAT_IN zone', '\n'.join(gate.battery_pyro(self.board)[0]))
        self.zone('BAT_IN', pcbnew.B_Cu, (40, -5, 50, 5))                     # R8P2-PYRO-01: a BAT_IN pour beside the
        self.pad(j, 1, 51.0, 0, 'PYRO1_OUT', size=(1.0, 1.0), pth=True)       # drain pad, 0.5 mm: fires
        self.assertIn('from PYRO1_OUT J121.1', '\n'.join(gate.battery_pyro(self.board)[0]))

    # --- D87 vias against paste apertures (fix pass 1) -------------------------------------------------------------------
    def paste_pad(self, f, num, x, y, size=(0.8, 1.4), copper=True):
        p = pcbnew.PAD(f); p.SetNumber(str(num)); p.SetShape(pcbnew.PAD_SHAPE_RECT)
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetSize(self.P(*size))
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Paste)
        if copper:
            ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.F_Mask)
        p.SetLayerSet(ls); f.Add(p); p.SetPosition(self.P(x, y))
        return p

    def test_a_via_keeps_its_ring_off_and_its_hole_0_1_mm_from_paste(self):
        f = self.fp('U30')
        self.paste_pad(f, '', 0, 0, copper=False)                            # u-blox's paste-only T extension
        v = self.via(0, 0.9, 'SIGNAL', d=0.5)                                 # hole inside the aperture (R8P1-DFM-01)
        self.assertIn('ring overlaps', '\n'.join(gate.via_paste(self.board)[0]))
        v.SetPosition(self.P(0, 1.1))                                         # ring 0.15 mm clear (R7's spot)
        self.assertFalse(gate.via_paste(self.board)[0])
        v.SetWidth(pcbnew.FromMM(0.32)); v.SetPosition(self.P(0, 0.9))       # small ring clear by 0.04, hole by 0.05
        self.assertIn('within 0.1 mm', '\n'.join(gate.via_paste(self.board)[0]))
        c = self.fp('C7', 10, 0); self.paste_pad(c, 1, 10, 0, size=(1.4, 1.35))
        v.SetWidth(pcbnew.FromMM(0.6)); v.SetPosition(self.P(10.9, 0.85))   # a power via ring on a pasted pad's corner
        self.assertIn("C7.1's paste", '\n'.join(gate.via_paste(self.board)[0]))

    # --- D92 terminal pin legends nearest their own pins (fix pass 1) ----------------------------------------------------
    def text(self, s, x, y, angle=0):
        t = pcbnew.PCB_TEXT(self.board); t.SetText(s); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(self.P(1.0, 1.0)); t.SetTextThickness(pcbnew.FromMM(0.15)); t.SetTextAngleDegrees(angle)
        t.SetPosition(self.P(x, y)); self.board.Add(t)
        return t

    def test_terminal_pin_legends_sit_nearest_their_own_pins(self):
        j1 = self.fp('J1', 23, 110.4)
        for num, (x, net) in enumerate(((30.62, 'BAT_IN'), (25.54, 'GND'), (20.46, 'BAT_SW_SOURCE'),
                                        (15.38, 'BAT_SW_RETURN')), 1):
            self.pad(j1, num, x, 110.4, net, size=(2.6, 2.6), pth=True)
        legends = [self.text(s, x, 116.8) for s, x in (('1:BAT+', 30.62), ('2:GND', 25.54), ('3:SW', 20.46),
                                                         ('4:SW', 15.38))]
        self.assertEqual(gate.terminal_legends(self.board)[0], [])
        legends[3].SetPosition(self.P(11.68, 103.1)); legends[3].SetTextAngleDegrees(90)   # R8 pass 1's spot
        j124 = self.fp('J124', 10, 93.32); self.pad(j124, 1, 10.0, 95.86, 'PYRO1_BUS', size=(2.6, 2.6), pth=True)
        issues = '\n'.join(gate.terminal_legends(self.board)[0])
        self.assertIn('"4:SW"', issues); self.assertIn('J124.1', issues); self.assertIn('J1.4: 0 legends', issues)
        legends[3].SetPosition(self.P(15.38, 116.8)); legends[3].SetTextAngleDegrees(0)
        legends[1].SetPosition(self.P(23.0, 116.8))                          # halfway between J1.2 and J1.3: a tie
        self.assertIn('"2:GND"', '\n'.join(gate.terminal_legends(self.board)[0]))
        legends[1].SetPosition(self.P(25.54, 116.8))
        self.text('3:SW', 20.46, 104.0)                                       # a second legend for one pin
        self.assertIn('J1.3: 2 legends', '\n'.join(gate.terminal_legends(self.board)[0]))

    # --- D19 gate drive beside servo PWM -------------------------------------------------------------------------------
    PAIRS = {(a, a) for a in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)} | \
        {(pcbnew.F_Cu, pcbnew.In1_Cu), (pcbnew.In1_Cu, pcbnew.F_Cu), (pcbnew.In2_Cu, pcbnew.B_Cu), (pcbnew.B_Cu, pcbnew.In2_Cu)}

    def test_gate_keeps_0_5_mm_from_servo_pwm_on_the_same_or_a_close_layer(self):
        self.track((0, 0), (10, 0), 'PYRO1_GATE_N')
        s = self.track((0, 0.6), (10, 0.6), 'SERVO1_MCU')                     # 0.4 mm edge to edge
        self.assertIn('0.400 mm', '\n'.join(gate.gate_servo(self.board, self.PAIRS)[0]))
        s.Move(self.P(0, 0.15))                                               # 0.55 mm
        self.assertFalse(gate.gate_servo(self.board, self.PAIRS)[0])
        s.Move(self.P(0, -0.75)); s.SetLayer(pcbnew.B_Cu)                     # right under the gate, through the core
        self.assertFalse(gate.gate_servo(self.board, self.PAIRS)[0])
        self.track((0, 0), (10, 0), 'SERVO2_OUT', layer=pcbnew.In1_Cu)        # 0.2 mm prepreg away: too close
        self.assertIn('SERVO2_OUT', '\n'.join(gate.gate_servo(self.board, self.PAIRS)[0]))

    def test_close_layer_pairs_come_from_the_stackup(self):
        import test_dc_solve                                                  # its JLC 4-layer stack-up text
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'b.kicad_pcb'
            path.write_text(test_dc_solve.STACK)
            pairs = gate.close_layer_pairs(str(path))
        self.assertIn((pcbnew.F_Cu, pcbnew.In1_Cu), pairs)
        self.assertIn((pcbnew.B_Cu, pcbnew.In2_Cu), pairs)
        self.assertNotIn((pcbnew.In1_Cu, pcbnew.In2_Cu), pairs)              # 1.06 mm of core
        self.assertNotIn((pcbnew.F_Cu, pcbnew.B_Cu), pairs)

    # --- D20 S15 / S16 -------------------------------------------------------------------------------------------------
    def test_in1_carries_no_track_and_in2_no_signal(self):
        self.track((0, 0), (5, 0), '3V3', layer=pcbnew.In2_Cu)                # power on In2: allowed
        self.assertFalse(gate.inner_signal(self.board)[0])
        self.track((0, 1), (5, 1), 'SERVO1_MCU', layer=pcbnew.In2_Cu)
        self.track((0, 2), (5, 2), 'GND', layer=pcbnew.In1_Cu)
        issues, length = gate.inner_signal(self.board)
        self.assertEqual(len(issues), 2)
        self.assertEqual(length, {'In2_signal': 5.0, 'In1': 5.0})

    def test_only_the_rigid_arm1_sense_in2_link_is_exempt(self):
        link = self.track((14.55, 94.15), (14.55, 97.55), 'ARM1_SENSE', layer=pcbnew.In2_Cu)   # R7's CH1 link (D70)
        issues, length = gate.inner_signal(self.board)
        self.assertEqual(issues, [])
        self.assertEqual(length, {'In2_rigid_exempt': 3.4})
        link.SetEnd(self.P(14.55, 97.6))                                      # extended: no longer R7's segment
        self.assertEqual(len(gate.inner_signal(self.board)[0]), 1)
        link.SetEnd(self.P(14.55, 97.55)); link.SetWidth(pcbnew.FromMM(0.25))  # widened
        self.assertEqual(len(gate.inner_signal(self.board)[0]), 1)
        link.SetWidth(pcbnew.FromMM(0.2))
        self.assertEqual(gate.inner_signal(self.board)[0], [])
        self.track((14.55, 97.55), (16.0, 97.55), 'ARM1_SENSE', layer=pcbnew.In2_Cu)   # any other ARM1_SENSE In2 copper
        self.assertEqual(len(gate.inner_signal(self.board)[0]), 1)

    # --- D11 / D15 rigid hash groups -----------------------------------------------------------------------------------
    def rigid_board(self):
        self.outline()
        self.circle(4, 4); self.circle(21.5, 68.6)                            # an M3 hole and a tie hole
        j30 = self.fp('J30', 12.85, 0); self.pad(j30, 5, 12.85, 2.3, 'GNSS_RF_IN', size=(1.0, 4.2))
        rf = self.track((12.85, 2.3), (12.85, 8), 'GNSS_RF_IN', width=0.3)
        self.via(11.85, 5.0)                                                  # line stitching
        self.via(10.0, gate.r7.FENCE_Y)                                       # fence row
        self.area('PYRO_BLOCK', gate.rc.CU4, (4, 84, 42, 114.4))
        self.area('U31_KEEPOUT', gate.rc.CU4, (25.66, 9.8, 34.06, 18.2))
        tp = self.fp('TP122', 20.45, 92.4); self.pad(tp, 1, 20.45, 92.4, 'PYRO1_GATE', size=(1.5, 1.5))
        r126 = self.fp('R126', 21.6, 91.4); self.pad(r126, 2, 21.6, 92.4, 'PYRO1_GATE')
        self.track((20.45, 92.4), (21.6, 92.4), 'PYRO1_GATE')
        r127 = self.fp('R127', 21.9, 88.4); self.pad(r127, 1, 21.9, 88.83, 'PYRO1_GATE_N')
        self.track((21.9, 88.83), (22.5, 88.83), 'PYRO1_GATE_N'); self.track((22.5, 88.83), (23.0, 88.33), 'PYRO1_GATE_N')
        self.via(23.0, 88.33, 'PYRO1_GATE_N')                                 # the exit via
        lane = self.track((23.0, 88.33), (23.0, 80.0), 'PYRO1_GATE_N', layer=pcbnew.In2_Cu)   # the lane beyond it
        j1 = self.fp('J1', 23, 110.4); self.pad(j1, 1, 18, 110.4, 'BAT_IN', size=(2.6, 2.6), pth=True)
        j122 = self.fp('J122', 23, 75.7); self.pad(j122, 2, 23, 75.7, 'RAW_ACT', size=(1.7, 1.7), pth=True)
        return rf, lane

    def digests(self):
        return {k: gate.digest(v) for k, v in gate.rigid_groups(self.board).items()}

    def test_rigid_digests_ignore_item_order_and_uuids(self):
        self.rigid_board()
        first = self.digests()
        self.setUp()
        self.rigid_board()                                                    # rebuilt: new UUIDs, same geometry
        self.assertEqual(self.digests(), first)
        self.assertEqual(gate.rigid(self.board, first)[0], [])

    def test_rigid_groups_fire_on_a_seeded_change(self):
        rf, lane = self.rigid_board()
        base = self.digests()

        def changed():
            now = self.digests()
            return sorted(k for k in now if now[k] != base[k])
        rf.SetWidth(pcbnew.FromMM(0.31))
        self.assertEqual(changed(), ['strip_gcpw', 'strip_rf_copper'])
        rf.SetWidth(pcbnew.FromMM(0.3))
        self.board.FindFootprintByReference('J30').Move(self.P(0.001, 0))     # 1 um
        self.assertIn('strip_parts', changed())
        self.board.FindFootprintByReference('J30').Move(self.P(-0.001, 0))
        self.assertEqual(changed(), [])
        v = self.via(30.0, 21.0)                                              # a new strip GND via
        self.assertEqual(changed(), ['strip_gnd'])
        self.board.Remove(v)
        self.via(14.0, gate.r7.FENCE_Y)                                       # the fence row is not rigid (D15/D16)
        self.assertEqual(changed(), [])
        lane.SetEnd(self.P(23.0, 70.0))                                       # the exit lane beyond the exit via
        self.assertEqual(changed(), [])
        self.board.FindFootprintByReference('TP122').Pads()[0].SetSize(self.P(1.4, 1.4))
        self.assertEqual(changed(), ['ch1_parts'])
        self.board.FindFootprintByReference('TP122').Pads()[0].SetSize(self.P(1.5, 1.5))
        g = [t for t in self.board.GetTracks() if t.GetNetname() == 'PYRO1_GATE'][0]
        g.SetWidth(pcbnew.FromMM(0.25))
        self.assertEqual(changed(), ['ch1_copper'])
        g.SetWidth(pcbnew.FromMM(0.2))
        z = [a for a in self.board.Zones() if a.GetZoneName() == 'PYRO_BLOCK'][0]
        z.Outline().SetVertex(0, self.P(4, 83.9))
        self.assertEqual(changed(), ['pyro_block_area'])
        z.Outline().SetVertex(0, self.P(4, 84))
        hole = [d for d in self.board.GetDrawings() if d.GetShape() == pcbnew.SHAPE_T_CIRCLE and
                abs(pcbnew.ToMM(d.GetCenter().x) - 4) < 1e-6][0]
        hole.Move(self.P(0.01, 0))
        self.assertEqual(changed(), ['m3_holes'])
        hole.Move(self.P(-0.01, 0))
        tie = [d for d in self.board.GetDrawings() if d.GetShape() == pcbnew.SHAPE_T_CIRCLE and
               abs(pcbnew.ToMM(d.GetCenter().x) - 21.5) < 1e-6][0]
        tie.Move(self.P(0, 0.005))
        self.assertEqual(changed(), ['j122_tie'])
        tie.Move(self.P(0, -0.005))
        self.board.FindFootprintByReference('J122').SetOrientationDegrees(180)
        self.assertEqual(changed(), ['j122_tie'])
        self.board.FindFootprintByReference('J122').SetOrientationDegrees(0)
        self.board.FindFootprintByReference('J1').Move(self.P(0, 1))
        self.assertEqual(changed(), ['j1'])
        self.board.FindFootprintByReference('J1').Move(self.P(0, -1))
        edge = [d for d in self.board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and
                d.GetShape() == pcbnew.SHAPE_T_SEGMENT][0]
        edge.SetEnd(edge.GetEnd() + self.P(0, 0.001))
        self.assertIn('outline', changed())
        edge.SetEnd(edge.GetEnd() - self.P(0, 0.001))
        ko = [a for a in self.board.Zones() if a.GetZoneName() == 'U31_KEEPOUT'][0]
        ko.SetDoNotAllowTracks(True)                                          # even a flag of a rigid rule area
        self.assertEqual(changed(), ['strip_rule_areas'])
        ko.SetDoNotAllowTracks(False)
        self.assertEqual(changed(), [])
        hole.Move(self.P(0.01, 0))
        self.assertTrue(gate.rigid(self.board, base)[0])

    def test_gcpw_profile_sees_the_coplanar_ground_move(self):
        self.track((10, 2), (10, 8), 'GNSS_RF_IN', width=0.3)
        g = self.track((10.555, 1), (10.555, 9), 'GND', width=0.3)            # 0.255 mm gap to the line edge
        first = gate.gcpw_profile(self.board)
        row = list(first.values())[0]
        self.assertEqual({r[1] for r in row}, {26})                           # right side: 0.26 mm in 0.01 mm steps
        self.assertEqual({r[0] for r in row}, {-1})                           # left: no GND within 1.5 mm
        g.Move(self.P(0.1, 0))
        self.assertNotEqual(gate.gcpw_profile(self.board), first)

    # --- D14 ---------------------------------------------------------------------------------------------------------
    def test_check_actuators_must_stay_r7s(self):
        self.assertEqual(gate.actuators_unchanged()[0], [])
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'check_actuators.py'
            p.write_text(gate.CHECK_ACTUATORS.read_text() + '\n# edited\n')
            self.assertTrue(gate.actuators_unchanged(p)[0])


if __name__ == '__main__':
    unittest.main()
