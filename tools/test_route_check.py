"""Synthetic regressions for the routing hygiene gate (tools/route_check.py): every category on a small board."""
import math
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
        self.chain([(0, 0), (4, 0), (6, 2), (8, 2), (10, 0)])      # D-R24-17: 45-degree turns only (no right_angle)
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

    def test_r24_right_angle(self):
        """D-R24-17 (the owner: "why not 45"): a 90-degree bend of two track ends fails on every net; its chamfered form
        passes; at a pad or via it counts only when the inner corner of the two tracks' copper lies outside the holder
        (a 0.2 mm track at a 0.6 mm via or a 0.6 mm pad passes); a 0.5 mm track bending at a 0.5 mm via fails; a T is not
        a bend."""
        def cats():
            return [d for d in rc.scan(self.board) if d['cat'] == 'right_angle']
        self.two_pads()
        self.chain([(0, 0), (5, 0), (5, 3), (10, 3), (10, 0)])        # three plain 90-degree corners
        found = cats()
        self.assertEqual(sorted((d['x'], d['y'], d['at']) for d in found),
                         [(5.0, 0.0, 'free'), (5.0, 3.0, 'free'), (10.0, 3.0, 'free')])
        self.assertTrue(all(rc.gated(d) for d in found))
        self.assertTrue(rc.evaluate(found, [])[0])
        self.board = pcbnew.BOARD(); self.setUp(); self.two_pads()
        self.chain([(0, 0), (4.5, 0), (5, 0.5), (5, 2.5), (5.5, 3), (9.5, 3), (10, 2.5), (10, 0)])    # the chamfered form
        self.assertEqual(cats(), [])
        self.board = pcbnew.BOARD(); self.setUp(); self.two_pads()
        self.chain([(0, 0), (5, 0)]); self.via(5, 0, d=0.6); self.chain([(5, 0), (5, 3)], layer=pcbnew.B_Cu)
        self.chain([(5, 0), (5, -3)])                                 # a 90-degree turn inside the 0.6 mm via's copper
        self.assertEqual(cats(), [])
        self.pad('A3', 5, 6, size=(0.6, 0.6))
        self.chain([(5, 6), (8, 6)]); self.chain([(5, 6), (5, 8)])    # ... and inside a 0.6 mm pad
        self.assertEqual(cats(), [])
        self.board = pcbnew.BOARD(); self.setUp(); self.two_pads()
        self.track((0, 0), (5, 0), width=0.5); self.via(5, 0, d=0.5)
        self.track((5, 0), (5, -3), width=0.5)                        # 0.25 x sqrt 2 = 0.354 mm > the 0.25 mm radius
        self.assertEqual([(d['x'], d['y'], d['at']) for d in cats()], [(5.0, 0.0, 'via')])
        self.board = pcbnew.BOARD(); self.setUp(); self.two_pads()
        self.pad('A3', 5, 4)
        self.chain([(0, 0), (10, 0)]); self.chain([(5, 0), (5, 4)])   # a T on the run's body: not a bend
        self.assertEqual(cats(), [])

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

    # --- R12F7-TRI-06 / -07: in-pad debris and same-net pad slits -----------------------------------------------------
    def test_r12f7_pad_debris_at_any_length(self):
        """A 0.1 mm segment wholly inside a pad, joined to nothing, is pad_debris (gated); the same piece as the end of a
        run into the pad is not (its end meets the run)."""
        self.pad('A1', 0, 0, 'PYRO1_COLD', size=(1.0, 1.0))
        self.pad('A2', 10, 0, 'PYRO1_COLD')
        self.chain([(0.3, 0), (10, 0)], 'PYRO1_COLD')
        self.track((0, 0.1), (0, 0.2), 'PYRO1_COLD')                        # debris: 0.1 mm, inside A1, joins nothing
        hits = self.cats('pad_debris')
        self.assertEqual([(d['x'], d['y'], d['pad']) for d in hits], [(0.0, 0.1, 'A1.1')], hits)
        self.assertIn('pad_debris', rc.RULE)
        failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
        self.assertTrue([f for f in failures if f['cat'] == 'pad_debris'], failures)
        self.setUp()
        self.pad('A1', 0, 0, 'PYRO1_COLD', size=(1.0, 1.0))
        self.pad('A2', 10, 0, 'PYRO1_COLD')
        self.chain([(0, 0.1), (0, 0.2), (0.3, 0.2), (10, 0.2), (10, 0)], 'PYRO1_COLD')   # joined at (0, 0.2)
        self.assertFalse(self.cats('pad_debris'))

    def test_r12f7_pad_slit_beside_a_same_net_pad(self):
        """A run passing a same-net pad it does not join at 0.03 mm is pad_slit (gated); the same run at 0.15 mm, a run
        touching the pad, and a pad exit leaving along the pad's edge are not."""
        def board(gap, join=False):
            self.setUp()
            self.pad('A1', 0, 0, 'PYRO1_COLD'); self.pad('A2', 10, 0, 'PYRO1_COLD')
            self.pad('B1', 5, 0, 'PYRO1_COLD')                              # 0.6 mm pad; its edge at y 0.3
            y = 0.3 + 0.1 + gap                                             # 0.2 mm track: copper edge at 0.3 + gap
            if join:
                self.chain([(0, 0), (4, 0), (5, 0), (5, y), (10, y), (10, 0)], 'PYRO1_COLD')
            else:
                self.chain([(0, 0), (4, 0), (4, y), (10, y), (10, 0)], 'PYRO1_COLD')
            return self.cats('pad_slit')
        hits = board(0.03)
        self.assertTrue([d for d in hits if d['pad'] == 'B1.1' and abs(d['gap_mm'] - 0.03) < 0.002], hits)
        self.assertIn('pad_slit', rc.RULE)
        self.assertFalse(board(0.15))
        self.assertFalse(board(-0.05))                                      # touching: the pad's copper, not a slit
        self.assertFalse(board(0.03, join=True))                            # the run joins B1 at (5, 0): its exit

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
        for name in (rc.TRIM_PREFIX + '1', 'R8_POUR_TRIM_G1'):          # R7's generated trims and R8's (D65)
            z.SetZoneName(name)
            b = self.saved()
            cuts = [d for d in rc.scan(b) if d['cat'] == 'pad_pour_cut']
            self.assertEqual([d['pad'] for d in cuts], ['A2.1'], name)
            failures, _, _ = rc.evaluate(rc.scan(b), allowlist=[])
            self.assertTrue([d for d in failures if d['cat'] == 'pad_pour_cut'], name)

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

    # --- R8: profiles and the keep-out-aware detour baseline (R8_DECISIONS D10) ---------------------------------------
    def module_with_two_pads(self, net='RADIO_TXEN'):
        """A 10 x 10 mm module body U31 at (20, 20) and two pads of `net` on opposite sides, 0.05 mm inside the body
        (as the E22's castellated pads 9 and 19 are)."""
        if not self.board.FindNet(net):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
        f = pcbnew.FOOTPRINT(self.board); f.SetReference('U31'); self.board.Add(f); f.SetPosition(self.P(20, 20))
        for num, (x, y) in (('9', (18, 15.05)), ('19', (22, 24.95))):
            p = pcbnew.PAD(f); p.SetNumber(num); p.SetShape(pcbnew.PAD_SHAPE_RECT)
            p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetSize(self.P(0.9, 1.5))
            layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); p.SetLayerSet(layers)
            p.SetNet(self.board.FindNet(net)); f.Add(p); p.SetPosition(self.P(x, y))

    def detours(self, log=None):
        return [d for d in rc.scan(self.board, log) if d['cat'] == 'detour']

    def test_profiles_select_the_lists_and_the_baseline(self):
        try:
            rc.set_profile('r7')
            self.assertEqual((len(rc.ALLOWLIST), len(rc.LEFTOVERS), rc.KEEPOUT_BASELINE), (45, 29, False))
            self.assertIn('RADIO_TXEN', rc.ROUTE_FIGURES)
        finally:
            rc.set_profile('r8')
        # A8 (D9) and the limiter's two keep-out-forced detours (D51, D11's fallback), nothing else
        self.assertEqual([e[:2] for e in rc.ALLOWLIST], [('critical_via_no_gnd', 'PYRO1_GATE'),
                                                         ('detour', 'GNSS_LNA_EN'), ('detour', 'GNSS_VCC_RF')])
        self.assertEqual((rc.LEFTOVERS, sorted(rc.ROUTE_FIGURES), rc.KEEPOUT_BASELINE),
                         ([], ['GNSS_LNA_EN', 'GNSS_VCC_RF'], True))
        with self.assertRaises(ValueError):
            rc.set_profile('r6')

    def test_a_loop_round_a_module_body_is_judged_on_the_keepout_aware_baseline(self):
        # RADIO_TXEN's case: pins on opposite sides of U31, nothing but GND may cross its body, so the copper goes round
        self.module_with_two_pads()
        self.chain([(18, 15.05), (18, 14.75), (14.75, 14.75), (14.75, 25.25), (22, 25.25), (22, 24.95)], 'RADIO_TXEN')
        try:
            rc.set_profile('r7')                     # plain baseline: 21.3 mm against 11.6 mm is a detour
            self.assertEqual([d['net'] for d in self.detours()], ['RADIO_TXEN'])
        finally:
            rc.set_profile('r8')
        log = []
        self.assertEqual(self.detours(log), [])      # keep-out-aware: about 20.1 mm round the body, ratio 1.06
        row = log[0]
        self.assertEqual(row['net'], 'RADIO_TXEN')
        self.assertAlmostEqual(row['keepout_mst_mm'], 0.05 + 3 + 10 + 7 + 0.05, delta=0.02)
        self.assertGreater(row['ratio'], 1.6)
        self.assertLess(row['keepout_ratio'], 1.2)
        self.assertIn('U31 body', ' '.join(row['crossing']))

    def test_a_detour_beside_the_keepout_still_fails(self):
        # the same pins, but the copper wanders 10 mm further out than the way round the body needs
        self.module_with_two_pads()
        self.chain([(18, 15.05), (18, 14.75), (4.75, 14.75), (4.75, 25.25), (22, 25.25), (22, 24.95)], 'RADIO_TXEN')
        log = []
        found = self.detours(log)
        self.assertEqual([d['net'] for d in found], ['RADIO_TXEN'])
        self.assertGreater(found[0]['len_mm'], 1.6 * found[0]['keepout_mst_mm'])
        self.assertEqual(log[0]['net'], 'RADIO_TXEN')            # listed with both ratios

    def keepout(self, layers, tracks=True, box=(3, -3, 7, 3)):
        z = pcbnew.ZONE(self.board); z.SetIsRuleArea(True)
        ls = pcbnew.LSET(); [ls.AddLayer(lid) for lid in layers]; z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(False); z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        o = z.Outline(); o.NewOutline()
        x0, y0, x1, y1 = box
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        return z

    def test_only_a_keepout_closed_on_every_layer_refines_the_baseline(self):
        self.two_pads('SIGNAL')                                   # pads at (0, 0) and (10, 0)
        self.chain([(0, 0), (0, 4), (10, 4), (10, 0)], 'SIGNAL')  # 18 mm round a box across the straight line
        self.keepout([pcbnew.F_Cu])                               # soft: B.Cu and the inner layers stay open
        log = []
        self.assertEqual([d['net'] for d in self.detours(log)], ['SIGNAL'])
        self.assertEqual(log, [])
        self.setUp()
        self.two_pads('SIGNAL')
        self.chain([(0, 0), (0, 4), (10, 4), (10, 0)], 'SIGNAL')
        self.keepout(rc.CU4)                                       # closed to tracks on every copper layer
        log = []
        self.assertEqual(self.detours(log), [])
        self.assertAlmostEqual(log[0]['keepout_mst_mm'], 2 * 3 * math.sqrt(2) + 4, delta=0.02)   # 45 deg round a corner
        self.assertEqual(log[0]['crossing'], ['track keep-out on every layer'])

    def test_parts_and_other_nets_copper_are_never_obstacles(self):
        self.two_pads('SIGNAL')
        self.pad('X1', 5, 0, 'GND', size=(3, 3))                  # a big foreign pad on the straight line
        self.track((5, -3), (5, 3), 'GND', width=2)               # and foreign copper
        self.chain([(0, 0), (0, 4), (10, 4), (10, 0)], 'SIGNAL')
        log = []
        self.assertEqual([d['net'] for d in self.detours(log)], ['SIGNAL'])
        self.assertEqual(log, [])

    def test_an_npth_hole_is_a_hard_keepout(self):
        self.two_pads('SIGNAL')
        f = pcbnew.FOOTPRINT(self.board); f.SetReference('H1'); self.board.Add(f)
        h = pcbnew.PAD(f); h.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); h.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        h.SetSize(self.P(3.2, 3.2)); h.SetDrillSize(self.P(3.2, 3.2)); f.Add(h); h.SetPosition(self.P(5, 0))
        self.chain([(0, 0), (0, 2.5), (10, 2.5), (10, 0)], 'SIGNAL')    # 15 mm: 1.5 x the plain 10 mm
        log = []
        rc.scan(self.board, log)
        self.assertEqual(log[0]['net'], 'SIGNAL')
        self.assertGreater(log[0]['keepout_mst_mm'], 10.0)
        self.assertIn('H1 NPTH', log[0]['crossing'])

    def test_every_r7_list_entry_still_has_a_reason(self):
        import route_lists_r7 as old
        for e in old.ALLOWLIST + old.LEFTOVERS:
            self.assertGreater(len(e[4]), 20, e[:4])
            if e[0] in rc.MEASURED_CATS:
                self.assertIn(e[1], old.ROUTE_FIGURES, e[:4])

    def test_every_allowlist_entry_has_a_reason(self):
        for e in rc.ALLOWLIST:
            cat, net, layer, xy, reason = e[:5]
            self.assertIn(cat, rc.RULE + rc.HYGIENE + rc.REMOVABLE + rc.POUR)
            self.assertGreater(len(reason), 20)
            if cat in rc.MEASURED_CATS:
                self.assertIn(net, rc.ROUTE_FIGURES, e[:4])
            if cat in rc.CHAIN_MEASURED:                  # fix pass 6: the run's measured length rides in the entry
                self.assertTrue(len(e) > 5 and 'path_mm' in e[5], e[:4])


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R10AuditScope(unittest.TestCase):
    def setUp(self):
        self.helper = RouteCheck(); self.helper.setUp()
        self.board = self.helper.board; self.board.SetCopperLayerCount(4)
        rc.set_profile('r10'); self.addCleanup(rc.set_profile, 'r8')

    def test_r19_named_parallel_via_closes_only_its_own_loop(self):
        """D-R19-09 (R19-PWR-01): a via named in PARALLEL_VIAS beside a supply's single-via layer change leaves the
        loop search, so its own loop passes; without the entry it is a track_loop; a named via that is missing or not
        parallel fails as parallel_via (gated), and any other loop on the net still fails."""
        from unittest.mock import patch
        h = self.helper
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'VLOGIC'))
        h.pad('A1', 0, 0, 'VLOGIC'); h.pad('A2', 10, 0, 'VLOGIC')
        h.track((0, 0), (2, 0), 'VLOGIC', 0.4); h.via(2, 0, 'VLOGIC', d=0.5)
        h.track((2, 0), (8, 0), 'VLOGIC', 0.4, pcbnew.B_Cu); h.via(8, 0, 'VLOGIC', d=0.5)
        h.track((8, 0), (10, 0), 'VLOGIC', 0.4)
        h.via(2.75, 0.75, 'VLOGIC', d=0.5)                           # the parallel barrel and its two stubs
        h.track((2.75, 0.75), (2, 0), 'VLOGIC', 0.4)
        h.track((2.75, 0.75), (2.75, 0), 'VLOGIC', 0.4, pcbnew.B_Cu)

        def found(entries):
            with patch.object(rc, 'PARALLEL_VIAS', entries):
                inst = rc.scan(self.board)
            hits = [d for d in inst if d['net'] == 'VLOGIC' and d['cat'] in ('track_loop', 'parallel_via')]
            self.assertTrue(all(rc.gated(d) for d in hits))
            return sorted(d['cat'] for d in hits)
        self.assertEqual(found([]), ['track_loop'])
        self.assertEqual(found([('VLOGIC', (2.75, 0.75), 'test')]), [])
        self.assertEqual(found([('VLOGIC', (2.75, 0.75), 'test'), ('VLOGIC', (5.0, 5.0), 'stale')]), ['parallel_via'])
        self.assertEqual(found([('VLOGIC', (8.0, 0.0), 'not parallel')]), ['parallel_via', 'track_loop'])
        h.chain([(0, 0), (1, 1), (2, 0)], 'VLOGIC', 0.4)                 # a second, unrelated loop on F.Cu
        self.assertEqual(found([('VLOGIC', (2.75, 0.75), 'test')]), ['track_loop'])
        self.assertIn(('VLOGIC', (29.8, 81.15)), [e[:2] for e in rc.PARALLEL_VIAS])

    def test_r24_named_parallel_via_on_a_critical_net(self):
        """D-R24-02: on a critical signal net a named second barrel beside a single-via layer change is left out of the
        net's via count (extra_vias) and of the needless-hop pairs as well as the loop search; unnamed, the same barrel
        fails all three ways, and a named via that is not parallel still fails."""
        from unittest.mock import patch
        h = self.helper
        for net in ('ACT_GATE', 'OTHER'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
        h.pad('A1', 0, 0, 'ACT_GATE'); h.pad('A2', 10, 0, 'ACT_GATE')
        h.track((0, 0), (2, 0), 'ACT_GATE', 0.3); h.via(2, 0, 'ACT_GATE', d=0.5)
        h.track((2, 0), (8, 0), 'ACT_GATE', 0.3, pcbnew.B_Cu); h.via(8, 0, 'ACT_GATE', d=0.5)
        h.track((8, 0), (10, 0), 'ACT_GATE', 0.3)
        h.track((5, -2), (5, 2), 'OTHER', 0.2)                         # the B.Cu run crosses it: a needed hop
        h.via(2.75, 0.75, 'ACT_GATE', d=0.5)                         # the second barrel and its two stubs
        h.track((2.75, 0.75), (2, 0), 'ACT_GATE', 0.3)
        h.track((2.75, 0.75), (2.75, 0), 'ACT_GATE', 0.3, pcbnew.B_Cu)

        def found(entries):
            with patch.object(rc, 'PARALLEL_VIAS', entries):
                inst = rc.scan(self.board)
            hits = [d for d in inst if d['net'] == 'ACT_GATE' and d['cat'] in ('track_loop', 'parallel_via',
                                                                                 'extra_vias')]
            self.assertTrue(all(rc.gated(d) for d in hits))
            return sorted({(d['cat'], bool(d.get('hop'))) for d in hits})
        self.assertEqual(found([]), [('extra_vias', False), ('extra_vias', True), ('track_loop', False)])
        self.assertEqual(found([('ACT_GATE', (2.75, 0.75), 'test')]), [])
        # a named via that is not parallel fails as parallel_via, and the real barrel's loop and hop still fail
        self.assertEqual(found([('ACT_GATE', (8.0, 0.0), 'not parallel')]),
                         [('extra_vias', True), ('parallel_via', False), ('track_loop', False)])

    def test_aud2_return_exclusions_keep_other_critical_checks(self):
        slow = ('ARM1_SENSE_MID', 'ARM1_SENSE', 'ACT_GATE', 'ACT_DRV', 'ACT_EN_MCU', 'CAM_PWR_EN', 'CAM_UART_OE')
        fast = ('USB_DP', 'HSE_IN', 'QSPI_CLK', 'SPI1_SCK', 'IMU_CS', 'GPS_TX_WIRE', 'PYRO1_GATE_N', 'PYRO1_COLD',
                'SD_SCK', 'SD_MISO', 'SD_MOSI', 'SD_CS', 'SD_DAT1', 'SD_DAT2')
        for net in slow + fast:
            if not self.board.FindNet(net): self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
            self.helper.track((0, 0), (5, 0), net, layer=pcbnew.F_Cu)
            self.helper.via(5, 0, net)
            self.helper.track((5, 0), (10, 0), net, layer=pcbnew.B_Cu)
        found = {d['net'] for d in rc.scan(self.board) if d['cat'] == 'critical_via_no_gnd'}
        self.assertEqual(found, set(fast))
        self.assertEqual({n for n, _, _ in rc.critical_transitions(self.board)}, set(fast))
        for net in slow:
            self.assertIn(rc.net_class(net), rc.SIGNAL_CRITICAL)
        self.helper.track((20, 20), (25, 20.3), 'ACT_GATE')
        off = [d for d in rc.scan(self.board) if d['net'] == 'ACT_GATE' and d['cat'] == 'off_angle']
        self.assertTrue(off and rc.evaluate(off, [])[0])
        self.assertTrue(rc.return_required('RAW_ACT'))
        rc.set_profile('r9')
        self.assertTrue(rc.return_required('ACT_GATE'))

    def test_r26_plated_pad_layer_change_needs_a_gnd_via(self):
        """D-R26-01 (R26-TRI-09): a plated (PTH) pad that carries a return-required critical signal net's tracks on two
        copper layers is a layer change through its barrel, as J440.3 / J440.4's AUX wires are since D-R20-09. With no
        GND via centre within 1.5 mm of the pad centre it fails as critical_via_no_gnd (layer 'pad'); a GND via 1.6 mm
        away does not clear it, one 1.5 mm away does. Tracks on one layer, an AUD-2 slow net (J400.2's BAT_SW_RETURN) and
        a power net (J1.1's BAT_IN) give no instance, and the R7-R9 profiles keep their via-only test."""
        def build(net, layers=(pcbnew.F_Cu, pcbnew.B_Cu), gnd=()):
            self.setUp()
            h = self.helper
            if not self.board.FindNet(net):
                self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
            f = pcbnew.FOOTPRINT(self.board); f.SetReference('J9'); self.board.Add(f)
            p = pcbnew.PAD(f); p.SetNumber('3'); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            p.SetAttribute(pcbnew.PAD_ATTRIB_PTH); p.SetSize(h.P(1.9, 1.9)); p.SetDrillSize(h.P(1.3, 1.3))
            p.SetLayerSet(pcbnew.PAD.PTHMask()); p.SetNet(self.board.FindNet(net)); f.Add(p); p.SetPosition(h.P(5, 5))
            h.pad('U1', 12, 5, net)
            h.track((5, 5), (12, 5), net, layer=layers[0])
            if len(layers) > 1:
                h.pad('D1', 0, 5, net)
                h.track((5, 5), (0, 5), net, layer=layers[1])
            for xy in gnd:
                h.via(*xy, 'GND')
            return [d for d in rc.scan(self.board) if d['cat'] == 'critical_via_no_gnd']

        hits = build('AUX_TX_WIRE')
        self.assertEqual([(d['net'], d['layer'], d['pad'], d['x'], d['y'], d['gnd_mm'], d['layers']) for d in hits],
                         [('AUX_TX_WIRE', 'pad', 'J9.3', 5.0, 5.0, None, ['F.Cu', 'B.Cu'])])
        self.assertTrue(rc.gated(hits[0]) and rc.evaluate(hits, [])[0])
        self.assertEqual([n for n, _, _, _ in rc.pad_layer_changes(self.board)], ['J9.3'])
        self.assertEqual([d['gnd_mm'] for d in build('AUX_TX_WIRE', gnd=[(5, 6.6)])], [1.6])
        self.assertEqual(build('AUX_TX_WIRE', gnd=[(5, 6.6), (5, 3.5)]), [])
        self.assertEqual(build('AUX_TX_WIRE', layers=(pcbnew.F_Cu,)), [])
        self.assertEqual(build('BAT_SW_RETURN'), [])                    # AUD-2: a slow filtered switch node
        self.assertIn(rc.net_class('BAT_SW_RETURN'), rc.SIGNAL_CRITICAL)
        self.assertEqual(build('BAT_IN'), [])                           # a power rail (power_via_no_gnd is for vias)
        self.assertEqual(build('AUX_TX_WIRE', layers=(pcbnew.F_Cu, pcbnew.In2_Cu))[0]['layers'], ['F.Cu', 'In2.Cu'])
        build('AUX_TX_WIRE')
        rc.set_profile('r9')
        self.assertEqual(rc.pad_layer_changes(self.board), [])
        self.assertFalse([d for d in rc.scan(self.board) if d['cat'] == 'critical_via_no_gnd'])

    def test_r21_arming_chain_is_critical_slow_and_its_old_jog_fails(self):
        """D-R21-04 (R21-REQ-04): J400's arming chain (BAT_SW_SOURCE, BAT_SW_RETURN, BAT_ENABLE) is a pyro / arming net
        with critical hygiene, on AUD-2's slow list (no GND partner via at its layer changes). Round 20's BAT_ENABLE
        B.Cu hop, (19.675, 66.6) -> (21, 67.925) -> (21, 68.6) -> (21.3, 68.9), ends in a 0.424 mm jog 0.3 mm off the
        F.Cu run below: gated. The round 21 hop, its last bend at (20.7, 68.3), passes."""
        for net in ('BAT_SW_SOURCE', 'BAT_SW_RETURN', 'BAT_ENABLE'):
            self.assertEqual(rc.net_class(net), 'pyro')
            self.assertIn(rc.net_class(net), rc.SIGNAL_CRITICAL)
            self.assertFalse(rc.return_required(net), net)
        self.assertNotEqual(rc.net_class('BAT_IN'), 'pyro')

        def hop(bends):
            self.setUp()
            h = self.helper
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'BAT_ENABLE'))
            h.pad('A1', 16.3, 66.0, 'BAT_ENABLE'); h.pad('A2', 21.3, 75.2, 'BAT_ENABLE')
            h.chain([(16.3, 66.0), (19.075, 66.0), (19.675, 66.6)], 'BAT_ENABLE')
            h.via(19.675, 66.6, 'BAT_ENABLE', d=0.5)
            h.chain([(19.675, 66.6)] + bends + [(21.3, 68.9)], 'BAT_ENABLE', layer=pcbnew.B_Cu)
            h.via(21.3, 68.9, 'BAT_ENABLE', d=0.5)
            h.track((21.3, 68.9), (21.3, 75.2), 'BAT_ENABLE')
            failures, _, _ = rc.evaluate(rc.scan(self.board), allowlist=[])
            return {d['cat'] for d in failures if d['net'] == 'BAT_ENABLE'}
        old, new = hop([(21.0, 67.925), (21.0, 68.6)]), hop([(20.7, 67.625), (20.7, 68.3)])
        self.assertIn('tiny_jog', old)                       # (the bare test board has no obstacle: extra_vias too)
        self.assertNotIn('tiny_jog', new)
        self.assertFalse({'critical_via_no_gnd', 'local_bump'} & (old | new), (old, new))

    def test_noncritical_metadata_is_informational_but_critical_faults_still_block(self):
        from contextlib import redirect_stdout
        import io
        from unittest.mock import patch
        noncritical = [dict(cat='detour', net='SIGNAL', cls='other', layer='net', x=1., y=1., len_mm=20., vias=2),
                       dict(cat='tiny_jog', net='OTHER', cls='other', layer='F.Cu', x=2., y=2.)]
        records = [('detour', 'SIGNAL', 'net', (1., 1.), 'stale figures are informational', dict(len_mm=1., vias=0)),
                   ('tiny_jog', 'GONE', 'F.Cu', (9., 9.), 'stale coordinate is informational')]
        fault = dict(cat='off_angle', net='QSPI_CLK', cls='spi', layer='F.Cu', x=3., y=3.)

        def run(profile, instances):
            rc.set_profile(profile)
            output = io.StringIO()
            with patch.object(sys, 'argv', ['route_check.py', 'unused.kicad_pcb', '--profile', profile]), \
                    patch.object(rc, 'set_profile'), patch.object(rc.pcbnew, 'LoadBoard', return_value=self.board), \
                    patch.object(rc, 'scan', return_value=list(instances)), \
                    patch.object(rc, 'bump_audit', return_value=([], 0)), \
                    patch.object(rc, 'LEFTOVERS', records), \
                    patch.object(rc, 'measured_check', wraps=rc.measured_check) as measured, \
                    patch.object(rc, 'alt_audit', return_value=[]) as alternative, redirect_stdout(output):
                result = rc.main()
                if profile == 'r10':
                    measured.assert_called_once_with([])
                    alternative.assert_called_once_with(self.board, [])
            return result, output.getvalue()

        result, output = run('r10', noncritical)
        self.assertEqual(result, 0, output)
        self.assertIn('INFO non-critical leftover', output)
        self.assertIn('INFO stale LEFTOVERS', output)
        result, output = run('r10', noncritical + [fault])
        self.assertEqual(result, 1, output)
        self.assertIn('FAIL off_angle', output)
        result, output = run('r9', noncritical)
        self.assertEqual(result, 1, output)  # Legacy bookkeeping still blocks.

    def test_aud10_exact_representations_count_without_leftover_but_real_overlaps_block(self):
        self.helper.two_pads('3V3')
        self.helper.chain([(0, 0), (5, 0), (10, 0)], '3V3')
        self.helper.track((0, 0), (5, 0), '3V3')
        instances = rc.scan(self.board)
        review = [d for d in instances if d['cat'] in rc.R10_REVIEW]
        self.assertTrue(any(d['cat'] == 'duplicate_segment' for d in review))
        self.assertEqual(rc.evaluate(instances, [])[0], [])
        self.assertEqual(rc.leftover_check([dict(d, cls='other') for d in review], []), ([], [], []))
        self.helper.track((2, 0), (8, 0), '3V3')
        self.helper.track((4, -3), (4, 3), '3V3')
        failures, _, _ = rc.evaluate(rc.scan(self.board), [])
        harmful = [d for d in failures if d['cat'] in ('collinear_overlap', 'crossing_without_node')]
        self.assertEqual({d['cat'] for d in harmful}, {'collinear_overlap', 'crossing_without_node'})
        self.assertTrue(all(rc.gated(d) for d in harmful))
        for category in ('collinear_overlap', 'crossing_without_node', 'overlap_only_joint', 'via_on_track'):
            fault = dict(cat=category, cls='spi', net='QSPI_CLK', layer='F.Cu', x=0., y=0.)
            self.assertTrue(rc.evaluate([fault], [])[0], category)
        rc.set_profile('r9')
        self.assertTrue(rc.evaluate(review, [])[0])

    def straight_route(self):
        self.helper.setUp()
        self.board = self.helper.board
        self.board.SetCopperLayerCount(4)
        self.helper.two_pads('QSPI_CLK')
        self.helper.track((0, 0), (10, 0), 'QSPI_CLK')

    def test_aud10_exact_duplicate_and_reverse_preserve_routes_and_connectivity(self):
        for a, b in (((0, 0), (10, 0)), ((10, 0), (0, 0))):
            with self.subTest(a=a, b=b):
                self.straight_route()
                baseline = rc.pad_groups(rc.collect(self.board)['QSPI_CLK'])
                self.assertEqual(rc.evaluate(rc.scan(self.board), [])[0], [])
                self.helper.track(a, b, 'QSPI_CLK')
                self.helper.track(b, a, 'QSPI_CLK')
                instances = rc.scan(self.board)
                self.assertEqual(rc.evaluate(instances, [])[0], [])
                self.assertEqual(sum(d['cat'] == 'duplicate_segment' for d in instances), 3)
                nc = rc.collect(self.board)['QSPI_CLK']
                self.assertEqual(rc.net_route(nc)['len'], 10.)
                self.assertEqual(rc.pad_groups(nc), baseline)
                # Removing one representation leaves the same physical connection; removing all does not.
                self.assertEqual(rc.pad_groups(nc, skip={id(nc.tracks[0]['obj'])}), baseline)
                self.assertNotEqual(rc.pad_groups(nc, skip={id(t['obj']) for t in nc.tracks}), baseline)

    def test_aud10_partial_overlap_width_and_endpoint_changes_still_block(self):
        for a, b, width in (((2, 0), (8, 0), .2), ((0, 0), (10, 0), .4),
                            ((.0005, 0), (10.0005, 0), .2)):
            with self.subTest(a=a, b=b, width=width):
                self.straight_route()
                self.helper.track(a, b, 'QSPI_CLK', width)
                instances = rc.scan(self.board)
                failures, _, _ = rc.evaluate(instances, [])
                self.assertTrue(any(d['cat'] == 'collinear_overlap' for d in failures), failures)
                self.assertFalse(any(d['cat'] == 'duplicate_segment' for d in instances), instances)
                self.assertGreater(rc.net_route(rc.collect(self.board)['QSPI_CLK'])['len'], 10.)

    def test_aud10_crossings_and_genuine_loops_still_block_with_duplicates(self):
        for category in ('crossing_without_node', 'track_loop'):
            with self.subTest(category=category):
                self.straight_route()
                self.helper.track((10, 0), (0, 0), 'QSPI_CLK')
                if category == 'crossing_without_node':
                    self.helper.pad('A3', 5, -3, 'QSPI_CLK')
                    self.helper.pad('A4', 5, 3, 'QSPI_CLK')
                    self.helper.track((5, -3), (5, 3), 'QSPI_CLK')
                else:
                    self.helper.chain([(0, 0), (3, 3), (7, 3), (10, 0)], 'QSPI_CLK')
                failures, _, _ = rc.evaluate(rc.scan(self.board), [])
                self.assertTrue(any(d['cat'] == category for d in failures), failures)

    def test_aud10_duplicate_keeps_true_segment_and_dead_copper_failures(self):
        self.straight_route()
        self.helper.track((10, 0), (0, 0), 'QSPI_CLK')
        self.helper.track((5, 0), (5.1, 3), 'QSPI_CLK')
        failures, _, _ = rc.evaluate(rc.scan(self.board), [])
        for category in ('off_angle', 'dead_copper'):
            self.assertTrue(any(d['cat'] == category for d in failures), failures)

    def test_aud10_exact_geometry_on_other_nets_or_layers_is_not_collapsed(self):
        self.straight_route()
        self.helper.two_pads('USB_DP')
        self.helper.track((0, 0), (10, 0), 'USB_DP')
        self.helper.track((0, 0), (10, 0), 'QSPI_CLK', layer=pcbnew.B_Cu)
        instances = rc.scan(self.board)
        failures, _, _ = rc.evaluate(instances, [])
        self.assertFalse(any(d['cat'] == 'duplicate_segment' for d in instances))
        self.assertTrue(any(d['cat'] == 'dead_copper' and d['layer'] == 'B.Cu' for d in failures), failures)
        self.assertEqual(len(rc.Copper(self.board).segs), 3)
        self.assertEqual(rc.net_route(rc.collect(self.board)['QSPI_CLK'])['len'], 20.)

    def test_aud10_preserves_legacy_duplicate_gate_and_route_length(self):
        self.straight_route()
        self.helper.track((10, 0), (0, 0), 'QSPI_CLK')
        for profile in ('r7', 'r8', 'r9'):
            with self.subTest(profile=profile):
                rc.set_profile(profile)
                failures, _, _ = rc.evaluate(rc.scan(self.board), [])
                for category in ('duplicate_segment', 'fold_back', 'track_loop'):
                    self.assertTrue(any(d['cat'] == category for d in failures), failures)
                self.assertEqual(rc.net_route(rc.collect(self.board)['QSPI_CLK'])['len'], 20.)

    def test_aud10_real_target_exact_duplicate_has_no_collateral_failures(self):
        board = pcbnew.LoadBoard(str(Path(__file__).resolve().parents[1] / 'm3_design/assembly_review/m3.kicad_pcb'))
        baseline = rc.scan(board)
        self.assertEqual(rc.evaluate(baseline, [])[0], [])
        # D-R19-14: GPS_RX's run now starts at PD9; D-R24-17: its corner at (28.8, 11.0) is chamfered 0.75 mm back
        a, b = self.helper.P(28.8, 29.6), self.helper.P(28.8, 11.75)
        matches = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'GPS_RX_MCU'
                   and t.GetLayer() == pcbnew.F_Cu and t.GetWidth() == pcbnew.FromMM(.2)
                   and {tuple(t.GetStart()), tuple(t.GetEnd())} == {tuple(a), tuple(b)}]
        self.assertEqual(len(matches), 1)
        nc = rc.collect(board)['GPS_RX_MCU']
        length, connected = rc.net_route(nc)['len'], rc.pad_groups(nc)
        for start, end in ((a, b), (b, a)):
            with self.subTest(start=tuple(start)):
                duplicate = pcbnew.PCB_TRACK(board)
                duplicate.SetNet(matches[0].GetNet()); duplicate.SetLayer(pcbnew.F_Cu)
                duplicate.SetStart(start); duplicate.SetEnd(end); duplicate.SetWidth(pcbnew.FromMM(.2))
                board.Add(duplicate)
                instances = rc.scan(board)
                self.assertEqual(rc.evaluate(instances, [])[0], [])
                self.assertEqual(sum(d['cat'] == 'duplicate_segment' for d in instances), 1)
                self.assertEqual(len(instances), len(baseline) + 1)
                nc = rc.collect(board)['GPS_RX_MCU']
                self.assertEqual(rc.net_route(nc)['len'], length)
                self.assertEqual(rc.pad_groups(nc), connected)
                board.Remove(duplicate)



@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R11SixLayer(unittest.TestCase):
    """D-R11-08: route_check profile r11 on synthetic six-layer boards (test_r11_check.Six): R10's classes and rules on
    every layer of the F / In1 / In2 / In3 / In4 / B stack."""

    @classmethod
    def setUpClass(cls):
        global Six
        from test_r11_check import Six                            # noqa: E402 (the shared six-layer board builder)

    def setUp(self):
        rc.set_profile('r11', gate_data={}); self.addCleanup(rc.set_profile, 'r8')

    def scan(self, s, cat):
        return [d for d in rc.scan(s.board) if d['cat'] == cat]

    def test_profile_reads_r10_classes_and_starts_empty(self):
        # D-R11-61: r11's allowlist is ALLOWLIST_R11 (forced findings only); leftovers and parallel vias start empty
        self.assertEqual((rc.ALLOWLIST, rc.LEFTOVERS, rc.ROUTE_FIGURES, rc.PARALLEL_VIAS),
                         (rc.ALLOWLIST_R11, [], rc.ROUTE_FIGURES_R11, []))
        rc.set_profile('r10')
        self.assertEqual((rc.ALLOWLIST, rc.LEFTOVERS, rc.ROUTE_FIGURES), ([], [], {}))   # R10's gate unchanged
        rc.set_profile('r11', gate_data={})
        for net in ('USB_DP', 'GPS_TX_WIRE', 'PYRO1_GATE', 'BAT_SW_RETURN', 'SD_SCK', '3V3'):
            rc.set_profile('r10'); want = rc.net_class(net)
            rc.set_profile('r11')
            self.assertEqual(rc.net_class(net), want)
        self.assertFalse(rc.return_required('BAT_SW_RETURN'))             # AUD-2's slow list, read from R10's
        self.assertEqual(rc.cu_layers(Six().board), rc.CU6)
        b4 = pcbnew.BOARD(); b4.SetCopperLayerCount(4)
        self.assertEqual(rc.cu_layers(b4), rc.CU4)                        # R7-R10 boards keep their four layers

    # --- D-R11-61: the r11 allowlist, its measured figures and the six-layer GND via audit -----------------------
    def test_r11_allowlist_entries_carry_measured_reasons(self):
        self.assertEqual(sorted((e[0], e[1]) for e in rc.ALLOWLIST_R11),
                         [('critical_via_no_gnd', 'CAM_MCU_RX'), ('critical_via_no_gnd', 'SD_MOSI'),
                          ('extra_vias', 'CAM_RX_BUFFER')])               # D-R11-85 added CAM_MCU_RX's C6 via
        for e in rc.ALLOWLIST_R11:
            self.assertTrue(e[4].startswith(('D-R11-61', 'D-R11-85')) and len(e[4]) > 100, e[:4])
        for e in rc.ALLOWLIST_R11:                                  # every measured category quotes its figures
            if e[0] in rc.MEASURED_CATS:
                self.assertIn(e[1], rc.ROUTE_FIGURES_R11)

    def test_r11_allowlist_matches_goes_stale_and_checks_figures(self):
        d = dict(cat='extra_vias', net='CAM_RX_BUFFER', cls='uart', layer='net', x=31.6, y=1.57, len_mm=19.2, vias=4)
        failures, allowed, stale = rc.evaluate([d])
        self.assertEqual((failures, len(allowed)), ([], 1))
        self.assertEqual(sorted(e[1] for e in stale), ['CAM_MCU_RX', 'SD_MOSI'])   # the no-GND entries matched nothing: stale
        self.assertEqual(rc.measured_check(allowed), [])
        moved = dict(d, len_mm=18.0, vias=3)                         # a redrawn route: the entry is out of date
        _, allowed, _ = rc.evaluate([moved])
        self.assertEqual(len(rc.measured_check(allowed)), 1)
        other = dict(d, x=31.0)                                      # 0.6 mm away: not this entry, so it fails
        failures, allowed, _ = rc.evaluate([other])
        self.assertEqual((len(failures), allowed), (1, []))
        rc.set_profile('r10')                                        # the r10 profile allows nothing
        failures, allowed, stale = rc.evaluate([d])
        self.assertEqual((len(failures), allowed, stale), (1, [], []))

    def test_r11_no_gnd_audit_uses_the_six_layer_search(self):
        s = Six()
        s.track((3, 20), (5, 20), 'SD_MOSI', width=0.1)
        s.track((5, 20), (7, 20), 'SD_MOSI', pcbnew.B_Cu, width=0.1)
        s.via(5, 20, 'SD_MOSI', d=0.4, drill=0.2)
        d = dict(cat='critical_via_no_gnd', net='SD_MOSI', layer='via', x=5.0, y=20.0)
        hit = rc.nognd_audit(s.board, [d])                           # open board: a legal spot, so the entry is stale
        self.assertEqual(len(hit), 1)
        self.assertLessEqual(hit[0][1][2], rc.GND_REACH)
        # In3 copper of another net over the whole reach blocks every spot on the six-layer stack (R7's four-layer
        # search would not see In3); a via keep-out on In4 alone does too
        for blocker in ('in3', 'in4_keepout'):
            with self.subTest(blocker=blocker):
                t = Six()
                t.track((3, 20), (5, 20), 'SD_MOSI', width=0.1)
                t.track((5, 20), (7, 20), 'SD_MOSI', pcbnew.B_Cu, width=0.1)
                t.via(5, 20, 'SD_MOSI', d=0.4, drill=0.2)
                if blocker == 'in3':
                    for k in range(-9, 10):
                        t.track((2.5, 20 + 0.2 * k), (7.5, 20 + 0.2 * k), 'SD_CS', pcbnew.In3_Cu, width=0.1)
                else:
                    z = pcbnew.ZONE(t.board); z.SetIsRuleArea(True)
                    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.In4_Cu); z.SetLayerSet(ls)
                    z.SetDoNotAllowVias(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowZoneFills(False)
                    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
                    o = z.Outline(); o.NewOutline()
                    for x, y in ((2, 17), (8, 17), (8, 23), (2, 23)):
                        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
                    t.board.Add(z)
                self.assertEqual(rc.nognd_audit(t.board, [d]), [])

    def test_r11_gnd_spot_rules(self):
        import r11_gnd_spots as g
        s = Six()
        s.track((10, 10), (20, 10), 'SD_CS', pcbnew.In3_Cu, width=0.1)
        s.via(30, 10, 'SD_SCK', d=0.4, drill=0.2)
        s.part('J1', 30, 30, [('1', 'BAT_IN', (0, 0), 'pth')])
        s.part('R1', 15, 30, [('1', 'GND', (0, 0), 'smd')])
        s.part('TP1', 15, 40, [('1', 'SD_MISO', (0, 0), 'smd')])
        s.via(10, 40, 'ACT_DRV', d=0.6, drill=0.3)
        sites = g.Sites(s.board, (0, 0, 46, 50))
        # copper clearance 0.1 mm or hole clearance 0.25 mm, whichever is larger (0.4 / 0.2 via: hole 0.35 mm reach)
        self.assertIsNotNone(sites.why((15, 10.39), 0.4, 0.2))
        self.assertIsNone(sites.why((15, 10.41), 0.4, 0.2))
        # hole to hole 0.2 mm from any via, whatever its net
        self.assertIsNotNone(sites.why((30.0, 10.39), 0.25, 0.15))
        self.assertIsNone(sites.why((30.0, 10.61), 0.4, 0.2))
        # a PTH hole of another net: 0.55 mm to the via's inner ring (hole 0.5 + 0.55 + 0.2 = 1.25 mm)
        self.assertIsNotNone(sites.why((31.24, 30), 0.4, 0.2))
        self.assertIsNone(sites.why((31.26, 30), 0.4, 0.2))
        # no hole in an SMD pad, even a GND one; a bare test pad keeps 1.0 mm
        self.assertEqual(sites.why((15, 30.5), 0.4, 0.2), 'hole in an SMD pad')
        self.assertIsNotNone(sites.why((15.3 + 0.2 + 0.95, 40), 0.4, 0.2))
        self.assertIsNone(sites.why((15.3 + 0.2 + 1.05, 40), 0.4, 0.2))
        # S-8: GND keeps 1.0 mm from an ACT_DRV barrel; the board edge 0.5 mm
        self.assertTrue(sites.why((11.45, 40), 0.4, 0.2).startswith('S-8'))   # ring 0.3 + 1.0 + 0.2
        self.assertIsNone(sites.why((11.55, 40), 0.4, 0.2))
        self.assertEqual(sites.why((0.65, 25), 0.4, 0.2), 'board edge')
        self.assertIsNone(sites.why((0.75, 25), 0.4, 0.2))

    def test_layer_change_to_in3_or_in4_needs_a_gnd_via(self):
        for layer in (pcbnew.In3_Cu, pcbnew.In4_Cu):
            with self.subTest(layer=layer):
                s = Six()
                s.part('A1', 5, 5, [('1', 'USB_DP', (0, 0), 'smd')])
                s.part('A2', 20, 5, [('1', 'USB_DP', (0, 0), 'smd')])
                s.track((5, 5), (10, 5), 'USB_DP')
                s.via(10, 5, 'USB_DP')
                s.track((10, 5), (15, 5), 'USB_DP', layer)
                s.via(15, 5, 'USB_DP')
                s.track((15, 5), (20, 5), 'USB_DP')
                hits = self.scan(s, 'critical_via_no_gnd')
                self.assertEqual(len(hits), 2)
                self.assertTrue(all(rc.gated(d) for d in hits))
                s.via(10, 6.2, 'GND'); s.via(15, 6.2, 'GND')
                self.assertEqual(self.scan(s, 'critical_via_no_gnd'), [])

    def test_plated_pad_layer_change_through_in3(self):
        s = Six()
        s.part('J9', 10, 10, [('5', 'CAM_RX_WIRE', (0, 0), 'pth')])
        s.part('U1', 20, 10, [('1', 'CAM_RX_WIRE', (0, 0), 'smd')])
        s.part('D1', 0.5, 10, [('1', 'CAM_RX_WIRE', (0, 0), 'smd')])
        s.track((10, 10), (20, 10), 'CAM_RX_WIRE')
        s.track((10, 10), (0.5, 10), 'CAM_RX_WIRE', pcbnew.In3_Cu)
        self.assertEqual([n for n, _, _, lays in rc.pad_layer_changes(s.board)], ['J9.5'])
        self.assertEqual(rc.pad_layer_changes(s.board)[0][3], sorted([pcbnew.F_Cu, pcbnew.In3_Cu]))

    def test_right_angle_and_off_angle_on_in3_and_in4(self):
        for layer in (pcbnew.In3_Cu, pcbnew.In4_Cu):
            with self.subTest(layer=layer):
                s = Six()
                s.part('A1', 5, 5, [('1', 'SIGNAL', (0, 0), 'smd')])
                s.part('A2', 15, 10, [('1', 'SIGNAL', (0, 0), 'smd')])
                s.via(5, 5, 'SIGNAL'); s.via(15, 10, 'SIGNAL')
                s.track((5, 5), (15, 5), 'SIGNAL', layer); s.track((15, 5), (15, 10), 'SIGNAL', layer)
                self.assertTrue(self.scan(s, 'right_angle'))
                s.track((20, 20), (25, 20.3), 'SIGNAL', layer)
                self.assertTrue(self.scan(s, 'off_angle'))

    def test_dangling_via_counts_inner_layers(self):
        s = Six()
        s.part('A1', 5, 5, [('1', 'SIGNAL', (0, 0), 'smd')])
        s.part('A2', 15, 5, [('1', 'SIGNAL', (0, 0), 'smd')])
        s.track((5, 5), (10, 5), 'SIGNAL'); s.via(10, 5, 'SIGNAL')
        s.track((10, 5), (15, 5), 'SIGNAL', pcbnew.In3_Cu)               # joins F.Cu and In3 at the via: not dangling
        self.assertEqual([d for d in self.scan(s, 'dangling_via') if d['net'] == 'SIGNAL'], [])

    def gate_board(self, second=True):
        """ACT_GATE between two pads: F.Cu, a barrel at (7, 5), B.Cu under an OTHER track (a needed hop), a barrel at
        (13, 5), F.Cu; with `second` a second barrel at (7.75, 5.75) beside the first, joined on F.Cu and B.Cu."""
        s = Six()
        s.part('A1', 5, 5, [('1', 'ACT_GATE', (0, 0), 'smd')])
        s.part('A2', 15, 5, [('1', 'ACT_GATE', (0, 0), 'smd')])
        s.track((5, 5), (7, 5), 'ACT_GATE', width=0.3); s.via(7, 5, 'ACT_GATE', d=0.6)
        s.track((7, 5), (13, 5), 'ACT_GATE', pcbnew.B_Cu, 0.3); s.via(13, 5, 'ACT_GATE', d=0.6)
        s.track((13, 5), (15, 5), 'ACT_GATE', width=0.3)
        s.track((10, 2), (10, 8), 'OTHER')                             # the B.Cu run passes under it: a needed hop
        for xy in ((7, 6.2), (13, 6.2)):
            s.via(*xy, 'GND')                                          # GND partners within 1.5 mm
        if second:
            s.via(7.75, 5.75, 'ACT_GATE', d=0.6)
            s.track((7.75, 5.75), (7, 5), 'ACT_GATE', width=0.3)
            s.track((7.75, 5.75), (7.75, 5), 'ACT_GATE', pcbnew.B_Cu, 0.3)
        return s

    def gate_hits(self, s, pairs):
        rc.set_profile('r11', gate_data={'parallel_vias': pairs})
        hits = [d for d in rc.scan(s.board) if d['net'] == 'ACT_GATE' and d['cat'] in ('track_loop', 'parallel_via',
                                                                                       'extra_vias')]
        self.assertTrue(all(rc.gated(d) for d in hits))
        return sorted((d['cat'], d.get('problem', '')[:5]) for d in hits)

    def test_o_c2_5_listed_parallel_pair_passes_unlisted_fails(self):
        """O-C2-5: a second barrel beside a single-via tap passes route_check r11 only as a listed pair from the gate
        data; unlisted it is a track_loop and an extra via (both gated)."""
        pair = {'net': 'ACT_GATE', 'vias': [[7, 5], [7.75, 5.75]], 'reason': 'test: second ACT_GATE barrel'}
        s = self.gate_board()
        self.assertEqual(self.gate_hits(s, []), [('extra_vias', ''), ('extra_vias', ''), ('track_loop', '')])
        self.assertEqual(self.gate_hits(s, [pair]), [])
        self.assertEqual(rc.PARALLEL_VIAS, [('ACT_GATE', (7.75, 5.75), 'test: second ACT_GATE barrel')])
        # either order names the same pair: the barrel left out of the loop search is the second one named
        self.assertEqual(self.gate_hits(s, [dict(pair, vias=[[7.75, 5.75], [7, 5]])]), [])
        # a pair on another net does not cover this one
        self.assertEqual(self.gate_hits(s, [dict(pair, net='OTHER')]),
                         [('extra_vias', ''), ('extra_vias', ''), ('track_loop', '')])
        self.assertEqual(self.gate_hits(self.gate_board(second=False), []), [])        # one barrel: clean

    def test_o_c2_5_stale_and_series_pairs_fail(self):
        s = self.gate_board()
        pair = {'net': 'ACT_GATE', 'vias': [[7, 5], [7.75, 5.75]], 'reason': 'test'}
        # stale: the first barrel moved away (no via at the named spot), the second gone, or a net with no copper
        self.assertIn(('parallel_via', 'stale'), self.gate_hits(s, [dict(pair, vias=[[6, 5], [7.75, 5.75]])]))
        self.assertIn(('parallel_via', 'stale'), self.gate_hits(self.gate_board(second=False), [pair]))
        rc.set_profile('r11', gate_data={'parallel_vias': [dict(pair, net='NO_COPPER')]})
        stale = [d for d in rc.scan(s.board) if d['cat'] == 'parallel_via']
        self.assertEqual([(d['net'], d['problem'][:5]) for d in stale], [('NO_COPPER', 'stale')])
        self.assertTrue(rc.gated(stale[0]))
        # two barrels in series (the run's two layer changes) are not a pair: the second named one fails as not
        # parallel, and the real second barrel's loop still fails
        hits = self.gate_hits(s, [dict(pair, vias=[[7, 5], [13, 5]])])
        self.assertIn(('parallel_via', 'not p'), hits)
        self.assertIn(('track_loop', ''), hits)
        # the first barrel named must be redundant too: (13, 5) is not, though (7.75, 5.75) beside (7, 5) is
        rc.set_profile('r11', gate_data={'parallel_vias': [dict(pair, vias=[[13, 5], [7.75, 5.75]])]})
        bad = [d for d in rc.scan(s.board) if d['cat'] == 'parallel_via']
        self.assertEqual([((d['x'], d['y']), d['problem'][:40]) for d in bad],
                         [((13.0, 5.0), 'not parallel: without the first barrel o')])

    def test_o_c2_5_gate_data_schema(self):
        self.assertEqual(rc.load_parallel_pairs({}), [])               # no key: an empty list
        ok = {'net': 'GND', 'vias': [[1, 2], [1.6, 2]], 'reason': 'R7.2 second GND barrel'}
        self.assertEqual(rc.load_parallel_pairs({'parallel_vias': [ok]}), [('GND', (1.0, 2.0), (1.6, 2.0), ok['reason'])])
        for bad in ({'parallel_vias': {}}, {'parallel_vias': [dict(ok, reason=' ')]},
                    {'parallel_vias': [dict(ok, vias=[[1, 2]])]}, {'parallel_vias': [dict(ok, vias=[[1, 2], [1, 2]])]},
                    {'parallel_vias': [dict(ok, extra=1)]}, {'parallel_vias': [dict(ok, net='')]},
                    {'parallel_vias': [dict(ok, vias=[[1, 2], [1, True]])]}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                rc.load_parallel_pairs(bad)
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'gate.json'
            self.assertEqual(rc.read_gate_data(path), {})              # no file: no pairs
            path.write_text(json.dumps({'parallel_vias': [ok]}))
            rc.set_profile('r11', gate_data=rc.read_gate_data(path))
            self.assertEqual(rc.PARALLEL_VIAS, [('GND', (1.6, 2.0), ok['reason'])])
        rc.set_profile('r10')
        self.assertEqual(rc.PARALLEL_PAIRS, [])                        # r10 keeps its own frozen list
        self.assertEqual(rc.PARALLEL_VIAS, rc.PARALLEL_VIAS_R10)

    def test_reference_pairs_follow_the_r11_stack(self):
        pairs = rc.ref_pairs()
        self.assertEqual(pairs[pcbnew.In3_Cu], {pcbnew.In2_Cu, pcbnew.In4_Cu})
        self.assertEqual(pairs[pcbnew.B_Cu], {pcbnew.In4_Cu})
        rc.set_profile('r10')
        self.assertEqual(rc.ref_pairs(), {pcbnew.B_Cu: {pcbnew.In2_Cu}, pcbnew.In2_Cu: {pcbnew.B_Cu}})


if __name__ == '__main__':
    unittest.main()
