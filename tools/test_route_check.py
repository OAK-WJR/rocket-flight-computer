"""Synthetic regressions for the routing hygiene gate (tools/route_check.py): every category on a small board."""
from pathlib import Path
import sys
import unittest

try:
    import pcbnew
except ImportError:
    pcbnew = None
if pcbnew:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import route_check as rc


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class RouteCheck(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.BOARD()
        for n in ('GND', 'SIGNAL', '3V3', 'QSPI_CLK', 'USB_DP', 'PYRO1_COLD'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, n))

    def P(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def track(self, a, b, net='SIGNAL', width=0.2, layer=None):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(self.P(*a)); t.SetEnd(self.P(*b)); t.SetWidth(pcbnew.FromMM(width))
        t.SetLayer(pcbnew.F_Cu if layer is None else layer); t.SetNet(self.board.FindNet(net))
        self.board.Add(t)
        return t

    def chain(self, pts, net='SIGNAL', width=0.2, layer=None):
        return [self.track(a, b, net, width, layer) for a, b in zip(pts, pts[1:])]

    def via(self, x, y, net='SIGNAL', d=0.6):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(self.P(x, y)); v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(0.3))
        v.SetNet(self.board.FindNet(net)); self.board.Add(v)
        return v

    def pad(self, ref, x, y, net='SIGNAL', size=(0.6, 0.6)):
        f = pcbnew.FOOTPRINT(self.board); f.SetReference(ref); self.board.Add(f)
        p = pcbnew.PAD(f); p.SetNumber('1'); p.SetShape(pcbnew.PAD_SHAPE_RECT)
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetSize(self.P(*size))
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); p.SetLayerSet(layers)
        p.SetNet(self.board.FindNet(net)); f.Add(p); p.SetPosition(self.P(x, y))
        return p

    def cats(self, cat=None):
        inst = rc.scan(self.board)
        return [d for d in inst if cat is None or d['cat'] == cat]

    def two_pads(self, net='SIGNAL'):
        self.pad('A1', 0, 0, net)
        self.pad('A2', 10, 0, net)

    # --- a clean route ------------------------------------------------------------------------------------------------
    def test_clean_route_has_no_gated_instance(self):
        self.two_pads()
        self.chain([(0, 0), (4, 0), (6, 2), (10, 2), (10, 0)])
        failures, allowed, stale = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertEqual(failures, [])

    # --- §3 rule categories -------------------------------------------------------------------------------------------
    def test_off_angle(self):
        self.two_pads()
        self.chain([(0, 0), (5, 0.3), (10, 0)])
        self.assertTrue(self.cats('off_angle'))

    def test_staircase_and_extra_bends(self):
        self.two_pads()
        self.chain([(0, 0), (2, 0), (2.3, 0.3), (2.8, 0.3), (3.1, 0.6), (10, 0.6), (10, 0)])
        self.assertTrue(self.cats('staircase'))
        self.board = pcbnew.BOARD()
        self.setUp()
        self.two_pads()
        self.chain([(0, 0), (2, 0), (3.5, 1.5), (5, 1.5), (6.5, 3), (10, 3), (10, 0)])
        self.assertFalse(self.cats('staircase'))
        self.assertTrue(self.cats('extra_bends'))

    def test_acute_t_flagged_and_square_t_not(self):
        self.two_pads()
        self.pad('A3', 3, 5)
        self.track((0, 0), (10, 0))
        self.chain([(3, 5), (3, 3), (6, 0)])            # meets the trunk at 45°
        self.assertTrue(self.cats('acute_angle'))
        self.setUp()
        self.two_pads()
        self.pad('A3', 3, 5)
        self.track((0, 0), (10, 0))
        self.chain([(3, 5), (3, 0)])                    # square T
        self.assertFalse(self.cats('acute_angle'))

    def test_acute_inside_a_big_pad_is_not_flagged(self):
        self.pad('A1', 0, 0, size=(3, 3))
        self.pad('A2', 10, 0)
        self.track((0, 0), (10, 0))
        self.track((0, 0), (5, 5))
        self.pad('A3', 5, 5)
        self.assertFalse([d for d in self.cats('acute_angle') if d['at'] == 'free'])

    def test_fold_back(self):
        self.two_pads()
        self.chain([(0, 0), (10, 0), (8, 0)])
        self.assertTrue(self.cats('fold_back') or self.cats('collinear_overlap'))

    def test_dead_stub_and_hidden_dead_loop(self):
        self.two_pads('PYRO1_COLD')
        self.track((0, 0), (10, 0), 'PYRO1_COLD')
        self.track((5, 0), (5, 3), 'PYRO1_COLD')       # stub
        self.assertTrue(self.cats('dead_copper'))
        self.setUp()
        self.two_pads('PYRO1_COLD')
        self.track((0, 0), (10, 0), 'PYRO1_COLD')
        # a dead branch whose far end closes a 30 um loop (KiCad's track_dangling misses it)
        self.chain([(5, 0), (5, 3), (5.03, 3), (5.0, 2.97), (5, 3)], 'PYRO1_COLD', 0.15)
        self.assertTrue(self.cats('dead_copper'))

    def test_dangling_via(self):
        self.two_pads()
        self.track((0, 0), (10, 0))
        self.via(5, 0)
        self.assertTrue(self.cats('dangling_via'))

    def test_critical_layer_change_needs_a_gnd_via(self):
        self.pad('U1', 0, 0, 'QSPI_CLK')
        self.pad('U2', 10, 0, 'QSPI_CLK')
        self.track((0, 0), (5, 0), 'QSPI_CLK')
        self.track((5, 0), (10, 0), 'QSPI_CLK', layer=pcbnew.B_Cu)
        self.via(5, 0, 'QSPI_CLK')
        self.assertTrue(self.cats('critical_via_no_gnd'))
        self.via(5, 1.2, 'GND')
        self.assertFalse(self.cats('critical_via_no_gnd'))

    # --- hygiene categories ---------------------------------------------------------------------------------------------
    def test_micro_segment_and_tiny_jog(self):
        self.two_pads('3V3')
        self.chain([(0, 0), (4, 0), (4.03, 0), (10, 0)], '3V3')
        self.assertTrue(self.cats('micro_segment'))
        self.setUp()
        self.two_pads('3V3')
        self.chain([(0, 0), (4, 0), (4.2, 0.2), (10, 0.2), (10, 0)], '3V3')
        self.assertTrue(self.cats('tiny_jog'))

    def test_collinear_unmerged(self):
        self.two_pads('3V3')
        self.chain([(0, 0), (5, 0), (10, 0)], '3V3')
        self.assertTrue(self.cats('collinear_unmerged'))

    def test_duplicates_overlaps_and_crossings(self):
        self.two_pads('3V3')
        self.track((0, 0), (10, 0), '3V3')
        self.track((0, 0), (10, 0), '3V3')
        self.assertTrue(self.cats('duplicate_segment'))
        self.setUp()
        self.two_pads('3V3')
        self.track((0, 0), (10, 0), '3V3', 0.4)
        self.track((0, 0.05), (10, 0.05), '3V3', 0.3)
        self.assertTrue(self.cats('side_by_side_overlap'))
        self.setUp()
        self.two_pads('3V3')
        self.pad('A3', 5, 3, '3V3'); self.pad('A4', 5, -3, '3V3')
        self.track((0, 0), (10, 0), '3V3')
        self.track((5, 3), (5, -3), '3V3')
        self.assertTrue(self.cats('crossing_without_node'))

    def test_overlap_only_joint_and_offcentre_via(self):
        self.two_pads('3V3')
        self.track((0, 0), (10, 0), '3V3')
        self.pad('A3', 5, 3, '3V3')
        self.track((5, 3), (5, 0.08), '3V3')           # ends in the trunk's copper, off its centre line
        self.assertTrue(self.cats('overlap_only_joint'))
        self.setUp()
        self.two_pads('3V3')
        self.via(5, 0, '3V3')
        self.track((0, 0), (4.85, 0), '3V3')            # ends 0.15 mm off the via centre
        self.track((5, 0), (10, 0), '3V3', layer=pcbnew.B_Cu)
        self.assertTrue(self.cats('via_offcentre_joint'))

    def test_short_stub_beside_its_own_run_is_a_stub_not_an_overlap_joint(self):
        self.two_pads('SIGNAL')
        self.track((0, 0), (10, 0), 'SIGNAL', 0.4)
        self.track((5, 0), (5, 0.3), 'SIGNAL', 0.4)      # free end within the run's copper reach, joined at (5, 0)
        self.assertFalse(self.cats('overlap_only_joint'))
        self.assertTrue(self.cats('dead_copper'))

    def test_neck_down_and_pad_entry_exemption(self):
        self.two_pads('3V3')
        self.track((0, 0), (5, 0), '3V3', 0.4)
        self.track((5, 0), (10, 0), '3V3', 0.2)
        self.assertTrue(self.cats('neck_down'))
        self.setUp()
        self.two_pads('3V3')
        self.track((0, 0), (9.4, 0), '3V3', 0.4)
        self.track((9.4, 0), (10, 0), '3V3', 0.2)      # narrows 0.1 mm from the pad: a pad-entry neck
        self.assertFalse(self.cats('neck_down'))

    def test_track_loop_on_a_net_without_pour(self):
        self.two_pads()
        self.track((0, 0), (10, 0))
        self.chain([(0, 0), (3, 3), (7, 3), (10, 0)])
        self.assertTrue(self.cats('track_loop'))

    # --- fix pass 3: jogs inside runs, short segments, pour-island dead copper, detours, pours ------------------------
    def zone(self, net, pts, layer=None, minw=0.15):
        z = pcbnew.ZONE(self.board); z.SetNet(self.board.FindNet(net)); z.SetLayer(pcbnew.F_Cu if layer is None else layer)
        z.SetMinThickness(pcbnew.FromMM(minw)); z.SetLocalClearance(pcbnew.FromMM(0.15))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        o = z.Outline(); o.NewOutline()
        for x, y in pts:
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        return z

    def fill(self):
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())

    def test_tiny_jog_inside_a_longer_run(self):
        # E 2, NE 1.1, E 0.4, NE 1.7: an extra-bend run whose inner E 0.4 mm is a tiny jog (P3-ROUTING_GEOMETRY-01)
        self.pad('A1', 0, 0, '3V3')
        pts = [(0, 0), (2, 0)]
        for dx, dy in ((0.7778, -0.7778), (0.4, 0), (1.2021, -1.2021)):
            pts.append((pts[-1][0] + dx, pts[-1][1] + dy))
        self.pad('A2', *pts[-1], '3V3')
        self.chain(pts, '3V3')
        jogs = self.cats('tiny_jog')
        self.assertTrue([d for d in jogs if d.get('inside') == 'extra_bends'], jogs)
        failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'tiny_jog'])

    def test_short_segment_in_open_routing_and_the_pad_exemption(self):
        self.two_pads('QSPI_CLK')
        self.chain([(0, 0), (4, 0), (4.1, 0.1), (4.1, 3), (10, 3), (10, 0)], 'QSPI_CLK')      # 0.141 mm 45° piece
        self.assertTrue(self.cats('short_segment'))
        self.setUp()
        self.pad('A1', 0, 0, 'QSPI_CLK', size=(1.0, 1.0))
        self.pad('A2', 10, 0, 'QSPI_CLK')
        self.chain([(0.1, 0.1), (0.2, 0.0), (10, 0)], 'QSPI_CLK')          # the short piece lies inside A1's copper
        self.assertFalse(self.cats('short_segment'))

    def test_copper_touching_one_pour_island_is_dead(self):
        self.pad('A1', 0, 0, 'GND'); self.pad('A2', 9, 0, 'GND')
        self.zone('GND', ((-1, -1), (10, -1), (10, 6), (-1, 6)))
        self.track((3, 3), (6, 3), 'GND')                                # floating in the pour
        self.fill()
        dead = self.cats('dead_copper')
        self.assertTrue([d for d in dead if d['net'] == 'GND'], dead)

    def test_stub_ending_in_a_pour_is_dead_but_a_bridge_between_islands_is_not(self):
        self.pad('A1', 0, 0, 'GND'); self.pad('A2', 9, 0, 'GND')
        self.zone('GND', ((-1, -1), (10, -1), (10, 6), (-1, 6)))
        self.track((0, 0), (0, 3), 'GND')                                # pad (already in the pour) -> pour only
        self.fill()
        self.assertTrue(self.cats('dead_copper'))
        self.setUp()
        self.pad('A1', 0, 0, 'GND'); self.pad('A2', 9, 0, 'GND')
        self.zone('GND', ((-1, -1), (3, -1), (3, 2), (-1, 2)))           # two islands, each holding one pad
        self.zone('GND', ((6, -1), (10, -1), (10, 2), (6, 2)))
        self.track((2, 1), (7, 1), 'GND')                                # the only link between them
        self.fill()
        self.assertFalse(self.cats('dead_copper'))

    def test_detour_and_extra_vias_on_a_critical_net(self):
        self.two_pads('QSPI_CLK')
        self.chain([(0, 0), (0, 6), (10, 6), (10, 0)], 'QSPI_CLK')        # 22 mm for a 10 mm octile distance
        failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'detour'])
        self.setUp()
        self.two_pads('QSPI_CLK')
        xs = [0, 2, 4, 6, 8, 10]
        for k, (a, c) in enumerate(zip(xs, xs[1:])):                    # F/B/F/B/F: 4 layer changes, needs 0
            self.track((a, 0), (c, 0), 'QSPI_CLK', layer=pcbnew.B_Cu if k % 2 else pcbnew.F_Cu)
        for x in xs[1:-1]:
            self.via(x, 0, 'QSPI_CLK')
        failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'extra_vias'])
        self.assertFalse([d for d in failures if d['cat'] == 'detour'])

    def test_detour_on_a_slow_net_is_counted_not_gated(self):
        self.two_pads('SIGNAL')
        self.chain([(0, 0), (0, 6), (10, 6), (10, 0)], 'SIGNAL')
        inst = rc.scan(self.board)
        self.assertTrue([d for d in inst if d['cat'] == 'detour'])
        failures, _, _ = rc.evaluate(inst, allowlist=[])
        self.assertFalse([d for d in failures if d['cat'] == 'detour'])

    def test_pour_sliver_and_unstitched_finger_fail_a_stitched_finger_passes(self):
        self.pad('A1', 0, 0, 'GND')
        # a 4 x 4 mm square with a 0.2 mm wide, 6 mm long finger (a sliver) and no via on the finger
        self.zone('GND', ((-1, -1), (3, -1), (3, 3), (1.1, 3), (1.1, 9), (0.9, 9), (0.9, 3), (-1, 3)), minw=0.1)
        self.via(1, 1, 'GND')
        self.fill()
        cats = {d['cat'] for d in self.cats()}
        self.assertIn('pour_sliver', cats)
        self.assertIn('pour_finger', cats)
        failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'pour_sliver'])
        self.setUp()
        self.pad('A1', 0, 0, 'GND')
        # a 0.4 mm finger (no sliver) stitched near its tip passes; unstitched it is a finger
        self.zone('GND', ((-1, -1), (3, -1), (3, 3), (1.2, 3), (1.2, 9), (0.8, 9), (0.8, 3), (-1, 3)), minw=0.1)
        self.via(1, 1, 'GND')
        self.fill()
        self.assertTrue(self.cats('pour_finger'))
        self.assertFalse(self.cats('pour_sliver'))
        self.via(1, 7, 'GND', d=0.4)
        self.fill()
        self.assertFalse(self.cats('pour_finger'))

    def test_power_layer_change_without_gnd_via_is_reported_not_gated(self):
        self.two_pads('3V3')
        self.track((0, 0), (5, 0), '3V3')
        self.track((5, 0), (10, 0), '3V3', layer=pcbnew.B_Cu)
        self.via(5, 0, '3V3')
        inst = rc.scan(self.board)
        self.assertTrue([d for d in inst if d['cat'] == 'power_via_no_gnd'])
        failures, _, _ = rc.evaluate(inst, allowlist=[])
        self.assertFalse([d for d in failures if d['cat'] == 'power_via_no_gnd'])

    # --- fix pass 4: pad relief rings, pads cut off their pour, out-of-date no-GND reasons, leftovers ---------------
    def test_a_pads_relief_ring_is_not_a_finger(self):
        # a 0.4 mm finger, 3.2 mm long, unstitched: a finger; with a GND pad on its tip, the pad's ring (outline +
        # PAD_RING) is its relief and the 2.25 mm left is too short to be one
        for with_pad in (False, True):
            self.setUp()
            self.pad('A1', 0, 0, 'GND')
            self.zone('GND', ((-1, -1), (3, -1), (3, 3), (1.2, 3), (1.2, 6.2), (0.8, 6.2), (0.8, 3), (-1, 3)), minw=0.1)
            self.via(1, 1, 'GND')
            if with_pad:
                self.pad('A2', 1, 6.0, 'GND', size=(0.3, 0.3))
            self.fill()
            self.assertEqual(bool(self.cats('pour_finger')), not with_pad, with_pad)

    def saved(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        path = str(Path(tmp) / 't.kicad_pcb')
        pcbnew.SaveBoard(path, self.board)
        return pcbnew.LoadBoard(path)

    def test_a_keepout_taking_a_pads_last_pour_contact_fails(self):
        self.pad('A1', 0, 0, 'GND')
        self.pad('A2', 5, 0, 'GND')
        self.zone('GND', ((-2, -2), (7, -2), (7, 2), (-2, 2)))
        self.fill()
        self.assertFalse([d for d in rc.scan(self.saved()) if d['cat'] == 'pad_pour_cut'])
        z = pcbnew.ZONE(self.board); z.SetIsRuleArea(True); z.SetLayer(pcbnew.F_Cu); z.SetZoneName(rc.TRIM_PREFIX + '1')
        z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        o = z.Outline(); o.NewOutline()
        for x, y in ((3.5, -1.5), (6.5, -1.5), (6.5, 1.5), (3.5, 1.5)):        # round A2: its spokes go
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        self.fill()
        z.SetZoneName('BODY_KEEPOUT')                                    # a design keep-out is intended
        self.assertFalse([d for d in rc.scan(self.saved()) if d['cat'] == 'pad_pour_cut'])
        z.SetZoneName(rc.TRIM_PREFIX + '1')
        b = self.saved()
        cuts = [d for d in rc.scan(b) if d['cat'] == 'pad_pour_cut']
        self.assertEqual([d['pad'] for d in cuts], ['A2.1'])
        failures, _, _ = rc.evaluate(rc.scan(b), allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'pad_pour_cut'])

    def test_an_allowlisted_no_gnd_layer_change_with_a_legal_spot_is_reported(self):
        d = dict(cat='critical_via_no_gnd', net='QSPI_CLK', layer='via', x=5.0, y=5.0)
        self.assertEqual(len(rc.nognd_audit(self.board, [d], search=lambda b, q: [((5.5, 5.0), 0.6, 0.5)])), 1)
        self.assertEqual(rc.nognd_audit(self.board, [d], search=lambda b, q: []), [])
        # the project's own search (m3_design/r7_hygiene.gnd_spots) on an empty board finds a spot; inside a via
        # keep-out it finds none
        self.track((3, 20), (5, 20), 'QSPI_CLK'); self.track((5, 20), (7, 20), 'QSPI_CLK', layer=pcbnew.B_Cu)
        self.via(5, 20, 'QSPI_CLK')
        d = dict(cat='critical_via_no_gnd', net='QSPI_CLK', layer='via', x=5.0, y=20.0)
        self.assertEqual(len(rc.nognd_audit(self.board, [d])), 1)
        z = pcbnew.ZONE(self.board); z.SetIsRuleArea(True)
        ls = pcbnew.LSET(); [ls.AddLayer(l) for l in rc.CU4]; z.SetLayerSet(ls)
        z.SetDoNotAllowVias(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        o = z.Outline(); o.NewOutline()
        for x, y in ((2, 17), (8, 17), (8, 23), (2, 23)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        self.assertEqual(rc.nognd_audit(self.board, [d]), [])

    def test_every_non_critical_leftover_needs_a_recorded_reason(self):
        inst = [dict(cat='tiny_jog', net='SIGNAL', cls='other', layer='F.Cu', x=1.0, y=1.0),
                dict(cat='tiny_jog', net='QSPI_CLK', cls='spi', layer='F.Cu', x=2.0, y=2.0),      # critical: gated
                dict(cat='detour', net='SIGNAL', cls='other', layer='net', x=3.0, y=3.0)]
        entry = ('tiny_jog', 'SIGNAL', 'F.Cu', (1.0, 1.0), 'measured reason')
        recorded, missing, stale = rc.leftover_check(inst, [entry, ('detour', 'OTHER', 'net', (9, 9), 'r')])
        self.assertEqual([d['net'] for d in recorded], ['SIGNAL'])
        self.assertEqual([(d['cat'], d['net']) for d in missing], [('detour', 'SIGNAL')])
        self.assertEqual(len(stale), 1)

    def test_every_leftover_entry_has_a_reason(self):
        for e in rc.LEFTOVERS:
            cat, net, layer, xy, reason = e[:5]
            self.assertIn(cat, rc.LEFTOVER_CATS)
            self.assertGreater(len(reason), 20)
            if cat in rc.MEASURED_CATS:                  # fix pass 5: every detour / extra_vias entry states its route
                self.assertIn(net, rc.ROUTE_FIGURES, e[:4])

    # --- fix pass 5: jogs and staircases through nodes, every acute pair, pour stubs, pad layer changes, via overlap,
    # measured route figures and the re-measured jog reasons -------------------------------------------------------
    def test_tiny_jog_across_a_via_is_a_jog_but_a_via_fan_out_off_a_straight_run_is_not(self):
        self.pad('A1', 0, 0, 'QSPI_CLK')
        self.pad('A2', 0.25, 10, 'QSPI_CLK', size=(0.6, 0.6))
        self.pad('A2', 0.25, 10, 'QSPI_CLK')
        self.chain([(0, 0), (0, 4.75), (0.25, 5.0)], 'QSPI_CLK')          # F.Cu down x 0, a 0.35 mm step into the via
        self.via(0.25, 5.0, 'QSPI_CLK')
        self.track((0.25, 5.0), (0.25, 10), 'QSPI_CLK', layer=pcbnew.B_Cu)  # B.Cu on down x 0.25
        jogs = [d for d in self.cats('tiny_jog') if 'via' in d.get('at', '')]
        self.assertTrue(jogs, self.cats('tiny_jog'))
        self.setUp()
        self.pad('A1', 0, 0, 'SIGNAL')
        self.pad('A2', 0, 10, 'SIGNAL')
        self.pad('A3', 0.4, 12, 'SIGNAL')
        self.track((0, 0), (0, 10))                                        # a straight run with a via fan-out off it
        self.track((0, 5), (0.4, 5))
        self.via(0.4, 5)
        self.track((0.4, 5), (0.4, 12), layer=pcbnew.B_Cu)
        self.assertFalse([d for d in self.cats('tiny_jog') if d.get('at')])

    def test_staircase_through_a_t_node(self):
        self.two_pads('SIGNAL')
        self.pad('A3', 2.5, -3, 'SIGNAL')
        # E 2, NE 0.42, E 0.5 (a branch tees in at its far end), NE 0.42, E: a staircase the plain chains split
        self.chain([(0, 0), (2, 0), (2.3, -0.3), (2.8, -0.3), (3.1, -0.6), (10, -0.6), (10, 0)])
        self.track((2.8, -3), (2.8, -0.3))
        self.chain([(2.5, -3), (2.8, -3)])
        st = [d for d in self.cats('staircase') if d.get('at') == 'node']
        self.assertTrue(st, self.cats('staircase'))

    def test_every_acute_pair_at_a_node_is_tested(self):
        # three branches at a small pad: E and NE (thin) meet at 45 deg inside the pad, NE and N (wide) at 45 deg with
        # the wedge outside it; only testing the sharpest pair (the first found) missed the second
        self.pad('A1', 0, 0, 'SIGNAL', size=(0.4, 0.4))
        self.pad('A2', 5, 0, 'SIGNAL'); self.pad('A3', 3, -3, 'SIGNAL'); self.pad('A4', 0, -5, 'SIGNAL')
        self.track((0, 0), (5, 0), width=0.1)
        self.track((0, 0), (3, -3), width=0.1)
        self.track((0, 0), (0, -5), width=0.6)
        self.assertTrue([d for d in self.cats('acute_angle') if d['at'] == 'pad/via'])

    def test_a_track_running_on_inside_its_own_pour_is_a_stub(self):
        for inside, want in ((3.0, True), (0.5, False)):
            self.setUp()
            self.pad('A1', -3, 0, 'GND'); self.pad('A2', 9, 0, 'GND')
            self.zone('GND', ((0, -1), (10, -1), (10, 6), (0, 6)))
            self.track((-3, 0), (0 + inside, 0), 'GND')                  # from a pad outside into the pour
            self.fill()
            self.assertEqual(bool(self.cats('pour_stub')), want, inside)

    def test_a_layer_change_into_a_test_pad_needs_a_gnd_via(self):
        self.pad('U1', 0, 0, 'QSPI_CLK')
        f = pcbnew.FOOTPRINT(self.board); f.SetReference('TP1'); self.board.Add(f)
        p = pcbnew.PAD(f); p.SetNumber('1'); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetSize(self.P(1.5, 1.5)); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.B_Cu); p.SetLayerSet(ls)
        p.SetNet(self.board.FindNet('QSPI_CLK')); f.Add(p); p.SetPosition(self.P(5, 0))
        self.track((0, 0), (5, 0), 'QSPI_CLK')
        self.via(5, 0, 'QSPI_CLK')
        hits = self.cats('critical_via_no_gnd')
        self.assertTrue(hits and hits[0]['into_pad'], hits)

    def test_overlapping_same_net_vias(self):
        self.two_pads('GND')
        self.track((0, 0), (10, 0), 'GND')
        self.via(4, 0, 'GND'); self.via(4.2, 0.55, 'GND')                 # 0.585 mm apart, 0.6 mm rings
        self.assertTrue(self.cats('via_overlap'))
        self.setUp()
        self.two_pads('GND')
        self.track((0, 0), (10, 0), 'GND')
        self.via(4, 0, 'GND'); self.via(4.2, 0.6, 'GND')                  # 0.632 mm: clear
        self.assertFalse(self.cats('via_overlap'))

    def test_detour_entries_must_quote_the_present_route(self):
        d = dict(cat='detour', net='SIGNAL', cls='other', layer='net', x=1.0, y=1.0, len_mm=20.0, vias=2)
        self.assertEqual(rc.measured_check([dict(d, measured=dict(len_mm=20.03, vias=2))]), [])
        self.assertEqual(len(rc.measured_check([dict(d, measured=dict(len_mm=21.0, vias=2))])), 1)
        self.assertEqual(len(rc.measured_check([dict(d, measured=dict(len_mm=20.0, vias=3))])), 1)
        self.assertEqual(len(rc.measured_check([dict(d, measured=None)])), 1)
        e = ('detour', 'SIGNAL', 'net', (1.0, 1.0), 'a measured reason', dict(len_mm=20.0, vias=2))
        recorded, missing, stale = rc.leftover_check([d], [e])
        self.assertEqual(recorded[0]['measured'], dict(len_mm=20.0, vias=2))

    # --- fix pass 6: compound jogs, poured-net chain detours and layer hops ---------------------------------------
    def test_a_jog_with_a_two_segment_middle_is_a_tiny_jog(self):
        # E 3, NE 0.42, SE 0.28, E: the run comes back 0.1 mm off its line (an A,B,C,A knee: P6-ROUTING_GEOMETRY-02)
        self.pad('A1', 0, 0, 'QSPI_CLK'); self.pad('A2', 10, -0.1, 'QSPI_CLK')
        self.chain([(0, 0), (3, 0), (3.3, -0.3), (3.5, -0.1), (10, -0.1)], 'QSPI_CLK')
        jogs = [d for d in self.cats('tiny_jog') if d.get('compound') == 2]
        self.assertTrue(jogs, self.cats('tiny_jog'))
        self.assertAlmostEqual(jogs[0]['offset_mm'], 0.1, places=3)
        failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'tiny_jog'])
        self.setUp()                                   # the same knee 1 mm out and 0.5 mm back: a plain dogleg
        self.pad('A1', 0, 0, 'QSPI_CLK'); self.pad('A2', 10, -0.5, 'QSPI_CLK')
        self.chain([(0, 0), (3, 0), (4, -1), (4.5, -0.5), (10, -0.5)], 'QSPI_CLK')
        self.assertFalse([d for d in self.cats('tiny_jog') if d.get('compound')])
        self.assertEqual(rc.path_defects([(0, 3, True), (7, 0.42, True), (1, 0.28, True), (0, 3, True)], 0.2), 'tiny_jog')
        self.assertIsNone(rc.path_defects([(0, 3, True), (7, 1.41, True), (1, 0.71, True), (0, 3, True)], 0.2))

    def test_chain_detour_on_a_poured_net_is_gated_and_measured(self):
        # a GND run between two pads that wanders 3 mm out and back, on a net with a pour elsewhere
        self.pad('A1', 0, 0, 'GND'); self.pad('A2', 4, 0, 'GND')
        self.zone('GND', ((20, 20), (25, 20), (25, 25), (20, 25)))
        self.chain([(0, 0), (0, -3), (4, -3), (4, 0)], 'GND')
        self.fill()
        inst = rc.scan(self.board)
        det = [d for d in inst if d['cat'] == 'chain_detour']
        self.assertEqual(len(det), 1, det)
        self.assertAlmostEqual(det[0]['path_mm'], 10.0, places=3)
        failures, allowed, _ = rc.evaluate(inst, allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'chain_detour'])
        e = ('chain_detour', 'GND', 'F.Cu', (det[0]['x'], det[0]['y']), 'a measured reason', dict(path_mm=10.0))
        failures, allowed, _ = rc.evaluate(inst, allowlist=[e])
        self.assertFalse([d for d in failures if d['cat'] == 'chain_detour'])
        self.assertEqual(rc.measured_check(allowed), [])
        stale = ('chain_detour', 'GND', 'F.Cu', (det[0]['x'], det[0]['y']), 'a measured reason', dict(path_mm=9.0))
        _, allowed, _ = rc.evaluate(inst, allowlist=[stale])
        self.assertEqual(len(rc.measured_check(allowed)), 1)
        self.assertEqual(len(rc.alt_audit(self.board, allowed)), 1)          # the straight run is clean: removable
        self.setUp()                                   # the same run on a net without a pour: the net-level test only
        self.pad('A1', 0, 0, 'QSPI_CLK'); self.pad('A2', 4, 0, 'QSPI_CLK')
        self.chain([(0, 0), (0, -3), (4, -3), (4, 0)], 'QSPI_CLK')
        self.assertFalse(self.cats('chain_detour'))

    def test_two_pure_layer_changes_in_series_on_a_poured_net(self):
        # 3V3 (poured elsewhere) F pad -> via -> B.Cu under other copper -> via -> F pad: a hop
        self.pad('A1', 0, 0, '3V3'); self.pad('A2', 8, 0, '3V3')
        self.zone('3V3', ((20, 20), (25, 20), (25, 25), (20, 25)))
        self.track((0, 0), (2, 0), '3V3'); self.via(2, 0, '3V3')
        self.track((2, 0), (6, 0), '3V3', layer=pcbnew.B_Cu); self.via(6, 0, '3V3')
        self.track((6, 0), (8, 0), '3V3')
        self.fill()
        hops = self.cats('pour_net_hop')
        self.assertEqual(len(hops), 1, hops)
        self.assertEqual(hops[0]['vias_n'], 2)
        failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'pour_net_hop'])
        self.setUp()                                   # a via that also stitches into its own pour joins something
        self.pad('A1', 0, 0, '3V3'); self.pad('A2', 8, 0, '3V3')
        self.zone('3V3', ((5, -1), (7, -1), (7, 1), (5, 1)), layer=pcbnew.In2_Cu)
        self.track((0, 0), (2, 0), '3V3'); self.via(2, 0, '3V3')
        self.track((2, 0), (6, 0), '3V3', layer=pcbnew.B_Cu); self.via(6, 0, '3V3')
        self.track((6, 0), (8, 0), '3V3')
        self.fill()
        self.assertFalse(self.cats('pour_net_hop'))

    def test_alt_audit_keeps_the_copper_to_hole_rule_at_non_plated_holes(self):
        # the blocked layout of the test below, with the pad that blocks "straight on at y 0" replaced by a non-plated
        # hole 0.18 mm from that redraw's copper: Clearance passes it (no copper), the 0.25 mm copper-to-hole rule not
        def jogs(check):
            self.setUp()
            self.two_pads('SIGNAL')
            self.chain([(0, 0), (4, 0), (4.2, 0.2), (8, 0.2), (8.8, 1.0), (10, 1.0), (10, 0)], 'SIGNAL')
            f = pcbnew.FOOTPRINT(self.board); f.SetReference('H1'); self.board.Add(f)
            p = pcbnew.PAD(f); p.SetNumber(''); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); p.SetSize(self.P(0.3, 0.3)); p.SetDrillSize(self.P(0.3, 0.3))
            ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); p.SetLayerSet(ls)
            f.Add(p); p.SetPosition(self.P(6.0, -0.43))
            self.pad('X2', 2.0, 0.42, '3V3', size=(0.6, 0.2))
            self.pad('X3', 7.0, 1.0, '3V3', size=(0.6, 0.3))
            self.pad('X4', 6.5, 1.6, '3V3', size=(0.6, 0.6))
            self.pad('X5', 4.0, 1.0, '3V3', size=(6.0, 0.4))
            self.pad('X6', 4.0, -1.0, '3V3', size=(6.0, 0.4))
            jog = [d for d in rc.scan(self.board) if d['cat'] == 'tiny_jog'][0]
            keep = rc.NPTH_CLEAR
            rc.NPTH_CLEAR = keep if check else -1.0
            try:
                return rc.alt_audit(self.board, [jog])
            finally:
                rc.NPTH_CLEAR = keep
        self.assertEqual(len(jogs(False)), 1)          # without the hole rule the redraw past the hole is "clean"
        self.assertEqual(jogs(True), [])

    def test_path_defects(self):
        E, NE, N = 0, 7, 6                                                # DIRS8 indices (y down: N = (0, -1))
        self.assertIsNone(rc.path_defects([(E, 3, True), (NE, 1.5, True), (E, 3, True)], 0.2))
        self.assertEqual(rc.path_defects([(E, 3, True), (NE, 0.3, True), (E, 3, True)], 0.2), 'tiny_jog')
        self.assertEqual(rc.path_defects([(E, 3, True), (NE, 0.6, True), (E, 0.6, True), (NE, 3, True)], 0.2),
                         'staircase')
        self.assertEqual(rc.path_defects([(E, 3, True), (3, 3, True)], 0.2), 'acute')      # E then SW: 135 deg turn
        self.assertEqual(rc.path_defects([(E, 3, True), (N, 0.1, True), (E, 3, True)], 0.2), 'short')

    def test_alt_audit_finds_a_clean_redraw_and_respects_blockers(self):
        # a tiny jog in open space is removable; with pads of another net on both alternatives it is forced
        def board(blocked):
            self.setUp()
            self.two_pads('SIGNAL')
            self.chain([(0, 0), (4, 0), (4.2, 0.2), (8, 0.2), (8.8, 1.0), (10, 1.0), (10, 0)], 'SIGNAL')
            if blocked:                                    # pads of another net that allow only the present step:
                self.pad('X1', 6.0, -0.25, '3V3', size=(0.6, 0.2))   # straight on at y 0 collides,
                self.pad('X2', 2.0, 0.45, '3V3', size=(0.6, 0.2))    # straight on at y 0.2 collides,
                self.pad('X3', 7.0, 1.0, '3V3', size=(0.6, 0.3))     # and so does a 1 mm step onto the last run's line
                self.pad('X4', 6.5, 1.6, '3V3', size=(0.6, 0.6))     # or a dip south (the rest exceed ALT_SLACK)
                self.pad('X5', 4.0, 1.0, '3V3', size=(6.0, 0.4))
                self.pad('X6', 4.0, -1.0, '3V3', size=(6.0, 0.4))
            inst = rc.scan(self.board)
            jog = [d for d in inst if d['cat'] == 'tiny_jog'][0]
            return rc.alt_audit(self.board, [jog])
        self.assertEqual(len(board(False)), 1)
        self.assertEqual(board(True), [])

    # --- fix pass 7 ---------------------------------------------------------------------------------------------------
    def test_a_via_joined_to_a_track_only_by_overlap(self):
        # a 3V3 via on the body of a 3V3 track (no track end in it): gated on a critical net
        self.pad('A1', 0, 0, '3V3'); self.pad('A2', 10, 0, '3V3')
        self.track((0, 0), (10, 0), '3V3')
        self.via(5, 0.03, '3V3')
        self.track((5, 0.03), (5, 4), '3V3', layer=pcbnew.B_Cu)
        hits = self.cats('via_on_track')
        self.assertEqual([(d['layer'], d['x'], d['y']) for d in hits], [('F.Cu', 5.0, 0.03)])
        failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'via_on_track'])
        self.setUp()                                   # the run split at the via: a node, nothing to report
        self.pad('A1', 0, 0, '3V3'); self.pad('A2', 10, 0, '3V3')
        self.chain([(0, 0), (5, 0), (10, 0)], '3V3')
        self.via(5, 0, '3V3')
        self.track((5, 0), (5, 4), '3V3', layer=pcbnew.B_Cu)
        self.assertFalse(self.cats('via_on_track'))
        self.setUp()                                   # a run passing 0.23 mm off a via with no track end on that layer
        self.pad('A1', 0, 0, '3V3'); self.pad('A2', 10, 0, '3V3')
        self.track((0, 0), (10, 0), '3V3')
        self.via(5, 0.23, '3V3')
        self.track((5, 0.23), (5, 4), '3V3', layer=pcbnew.B_Cu)
        self.assertEqual(len(self.cats('via_on_track')), 1)
        self.setUp()                                   # the same via also ending a run on that layer: it is a node there
        self.pad('A1', 0, 0, '3V3'); self.pad('A2', 10, 0, '3V3')
        self.track((0, 0), (10, 0), '3V3')
        self.via(5, 0.23, '3V3')
        self.track((5, 0.23), (5, 4), '3V3')
        self.assertFalse(self.cats('via_on_track'))
        self.setUp()                                   # inside its own net's fill: the fill makes the joint (information)
        self.pad('A1', 0, 0, 'GND'); self.pad('A2', 10, 0, 'GND')
        self.zone('GND', ((3, -2), (7, -2), (7, 2), (3, 2)))
        self.track((0, 0), (10, 0), 'GND')
        self.via(5, 0.03, 'GND')
        self.fill()
        self.assertFalse(self.cats('via_on_track'))
        self.assertEqual(len(self.cats('via_on_track_in_fill')), 1)

    def bump_board(self, net, wall):
        # E 4, N 2, E 2, S 2, E 4 between two pads: a 4 mm bump that a straight run removes, unless pads of another net
        # wall the line off and hug the bump's sides (then only the same rectangular drawing, tighter, is shorter)
        self.setUp()
        self.pad('A1', 0, 0, net); self.pad('A2', 10, 0, net)
        self.chain([(0, 0), (4, 0), (4, -2), (6, -2), (6, 0), (10, 0)], net)
        if wall:
            self.pad('X1', 5.0, 2.0, 'GND', size=(0.6, 7.0))      # y -1.5 .. 5.5: no way round it below either
            self.pad('X2', 2.1, -1.7, 'GND', size=(3.0, 2.6))     # beside the bump's west leg: no corner chamfer
            self.pad('X3', 7.9, -1.7, 'GND', size=(3.0, 2.6))     # and its east leg
        return rc.bump_audit(self.board)

    def test_local_bump_is_gated_and_a_walled_one_is_not_removable(self):
        bumps, searched = self.bump_board('QSPI_CLK', wall=False)
        self.assertEqual(len(bumps), 1, bumps)
        self.assertEqual(bumps[0]['end'], (6.0, 0.0))                # the window ends after the bump's last bend
        self.assertAlmostEqual(bumps[0]['path_mm'] - bumps[0]['redraw_mm'], 4.0, places=3)   # the 4 mm bump goes
        failures, _, _ = rc.evaluate(rc.scan(self.board) + bumps, allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'local_bump'])
        e = ('local_bump', 'QSPI_CLK', 'F.Cu', (bumps[0]['x'], bumps[0]['y']), 'a measured reason')
        failures, allowed, stale = rc.evaluate(rc.scan(self.board) + bumps, allowlist=[e])
        self.assertFalse([d for d in failures if d['cat'] == 'local_bump'])
        self.assertEqual(stale, [])
        bumps, searched = self.bump_board('QSPI_CLK', wall=True)
        self.assertEqual(bumps, [])
        self.assertGreater(searched, 0)
        bumps, _ = self.bump_board('SIGNAL', wall=False)      # a non-critical net is not searched by default
        self.assertEqual(bumps, [])
        bumps, _ = rc.bump_audit(self.board, nets=lambda n: True)
        self.assertEqual(len(bumps), 1)

    def test_a_bump_redraw_may_not_cut_a_critical_lines_reference(self):
        # an In2 redraw near a QSPI_CLK B.Cu line cuts the In2 pour that line takes as its reference, unless the window's
        # present copper already runs there (fix pass 7: LED_RED's straight run under QSPI_NCS)
        self.pad('A1', 0, 0, 'SIGNAL'); self.pad('A2', 10, 0, 'SIGNAL')
        self.chain([(0, 0), (4, 0), (4, -2), (6, -2), (6, 0), (10, 0)], 'SIGNAL', layer=pcbnew.In2_Cu)
        self.track((5, -1.2), (5, 1.5), 'QSPI_CLK', layer=pcbnew.B_Cu)
        cu = rc.Copper(self.board)
        chk = rc.RedrawCheck(self.board)
        F, w = pcbnew.FromMM, pcbnew.FromMM(0.2)
        win = [x for x in cu.segs if x['net'] == 'SIGNAL' and x['lid'] == pcbnew.In2_Cu][1:4]
        straight = [(F(4), 0), (F(6), 0)]
        why = chk.why('SIGNAL', pcbnew.In2_Cu, straight, w, gone={x['uid'] for x in win}, strict=True, cu=cu,
                      ends=straight, present=win)
        self.assertEqual(why, 'cuts the reference of QSPI_CLK')
        self.assertIsNone(chk.why('SIGNAL', pcbnew.In2_Cu, straight, w, gone={x['uid'] for x in win}, strict=False))
        self.setUp()                                   # a line that also crosses the present bump: one crossing moved
        self.pad('A1', 0, 0, 'SIGNAL'); self.pad('A2', 10, 0, 'SIGNAL')
        self.chain([(0, 0), (4, 0), (4, -2), (6, -2), (6, 0), (10, 0)], 'SIGNAL', layer=pcbnew.In2_Cu)
        self.track((5, -2.5), (5, 1.5), 'QSPI_CLK', layer=pcbnew.B_Cu)
        chk = rc.RedrawCheck(self.board)
        cu = rc.Copper(self.board)
        win = [x for x in cu.segs if x['net'] == 'SIGNAL' and x['lid'] == pcbnew.In2_Cu][1:4]
        self.assertIsNone(chk.why('SIGNAL', pcbnew.In2_Cu, straight, w, gone={x['uid'] for x in win}, strict=True,
                                  cu=cu, ends=straight, present=win))

    def test_alt_audit_does_not_take_a_tighter_copy_of_a_chain_detour_as_its_fix(self):
        # a GND chain detour N 1.2 / E 2.4 / S 1.2 round nothing: a candidate with the same headings and the E leg pulled
        # in (it passes the chain metric, P7-ROUTING-04) is not the detour's fix; one with other headings is
        self.pad('A1', 0, 0, 'GND'); self.pad('A2', 2.4, 0, 'GND')
        self.zone('GND', ((20, 20), (25, 20), (25, 25), (20, 25)))
        self.chain([(0, 0), (0, -1.2), (2.4, -1.2), (2.4, 0)], 'GND')
        self.fill()
        det = [d for d in rc.scan(self.board) if d['cat'] == 'chain_detour']
        self.assertEqual(len(det), 1, det)
        F = pcbnew.FromMM
        tighter = [(0, 0), (0, F(-0.25)), (F(2.4), F(-0.25)), (F(2.4), 0)]           # N, E, S again: 2.9 mm
        other = [(0, 0), (F(0.25), F(-0.25)), (F(2.15), F(-0.25)), (F(2.4), 0)]      # NE, E, SE
        keep = rc.alt_candidates
        try:
            rc.alt_candidates = lambda win, step=None: [tighter]
            self.assertEqual(rc.alt_audit(self.board, det), [])
            rc.alt_candidates = lambda win, step=None: [other]
            self.assertEqual(len(rc.alt_audit(self.board, det)), 1)
        finally:
            rc.alt_candidates = keep

    def test_redraw_check_keeps_the_edge_clearance_at_an_edge_cuts_hole(self):
        for (x0, y0), (x1, y1) in (((-5, -5), (15, -5)), ((15, -5), (15, 5)), ((15, 5), (-5, 5)), ((-5, 5), (-5, -5))):
            s = pcbnew.PCB_SHAPE(self.board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
            s.SetStart(self.P(x0, y0)); s.SetEnd(self.P(x1, y1)); s.SetWidth(pcbnew.FromMM(0.1)); self.board.Add(s)
        c = pcbnew.PCB_SHAPE(self.board); c.SetShape(pcbnew.SHAPE_T_CIRCLE); c.SetLayer(pcbnew.Edge_Cuts)
        c.SetCenter(self.P(5, 2)); c.SetEnd(self.P(6, 2)); c.SetWidth(pcbnew.FromMM(0.1)); self.board.Add(c)
        chk = rc.RedrawCheck(self.board)
        w = pcbnew.FromMM(0.2)
        near = [(pcbnew.FromMM(0), pcbnew.FromMM(0.65)), (pcbnew.FromMM(10), pcbnew.FromMM(0.65))]   # 0.25 mm from it
        far = [(pcbnew.FromMM(0), pcbnew.FromMM(0.35)), (pcbnew.FromMM(10), pcbnew.FromMM(0.35))]    # 0.55 mm
        self.assertEqual(chk.why('SIGNAL', pcbnew.F_Cu, near, w), 'edge')
        self.assertIsNone(chk.why('SIGNAL', pcbnew.F_Cu, far, w))
        edge = [(pcbnew.FromMM(0), pcbnew.FromMM(4.7)), (pcbnew.FromMM(10), pcbnew.FromMM(4.7))]   # 0.2 mm from the outline
        self.assertEqual(chk.why('SIGNAL', pcbnew.F_Cu, edge, w), 'edge')

    # --- gate logic ---------------------------------------------------------------------------------------------------
    def test_gate_rules_everywhere_hygiene_only_on_critical_nets(self):
        self.two_pads('SIGNAL')
        self.chain([(0, 0), (4, 0), (4.03, 0), (10, 0)], 'SIGNAL')      # micro segment on a slow net: info
        failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertFalse([d for d in failures if d['cat'] == 'micro_segment'])
        self.setUp()
        self.two_pads('SIGNAL')
        self.chain([(0, 0), (5, 0.3), (10, 0)], 'SIGNAL')               # off-angle on a slow net: a rule
        failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertTrue([d for d in failures if d['cat'] == 'off_angle'])

    def test_allowlist_matches_and_stale_entries_fail(self):
        self.two_pads()
        self.chain([(0, 0), (5, 0.3), (10, 0)])
        inst = rc.scan(self.board)
        d = [x for x in inst if x['cat'] == 'off_angle'][0]
        entry = ('off_angle', 'SIGNAL', 'F.Cu', (d['x'], d['y']), 'test')
        failures, allowed, stale = rc.evaluate(inst, allowlist=[entry])
        self.assertNotIn(d, failures)
        self.assertEqual(len(allowed), 1)
        self.assertEqual(stale, [])
        failures, allowed, stale = rc.evaluate(inst, allowlist=[entry, ('off_angle', 'SIGNAL', 'F.Cu', (1, 1), 't')])
        self.assertEqual(len(stale), 1)

    def test_every_allowlist_entry_has_a_reason(self):
        for e in rc.ALLOWLIST:
            cat, net, layer, xy, reason = e[:5]
            self.assertIn(cat, rc.RULE + rc.HYGIENE + rc.REMOVABLE + rc.POUR)
            self.assertGreater(len(reason), 20)
            if cat in rc.MEASURED_CATS:
                self.assertIn(net, rc.ROUTE_FIGURES, e[:4])
            if cat in rc.CHAIN_MEASURED:                  # fix pass 6: the run's measured length rides in the entry
                self.assertTrue(len(e) > 5 and 'path_mm' in e[5], e[:4])


if __name__ == '__main__':
    unittest.main()
