"""Seeded faults for the R11 contract (tools/check_r11.py) and the r11 fit profile on synthetic six-layer boards
(route_check's six-layer seeds are in tools/test_route_check.py, R11SixLayer, built with Six below); and, when R11_BOARD names the R11 board, on temporary copies of it.

R11_BOARD_REQUIRED=1 (set by tools/check.sh once its R11 section has run) turns a missing R11_BOARD into a failure, so
the real-board seeds cannot be skipped silently while the R11 board exists.
"""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

try:
    import pcbnew
except ImportError:
    pcbnew = None
if pcbnew:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_r10 as r10
    import check_r11 as r11
    import fit_check as fc
    import route_check as rc

NETS = ('GND', 'SIGNAL', '3V3', 'PORT_4V8', 'RAW_ACT', 'ACT_GATE', 'USB_DP', 'BAT_IN', 'PYRO1_OUT', 'PYRO1_IGN',
        'GPS_TX_WIRE', 'GPS_RX_WIRE', 'CAM_5V', 'CAM_RX_WIRE', 'CAM_TX_WIRE')


class Six:
    """A synthetic six-layer R11 board: 46 x 50 mm outline, title-block revision M3-ASSY-R11."""

    def __init__(self, length=50.0):
        self.board = b = pcbnew.BOARD()
        b.SetCopperLayerCount(6)
        tb = b.GetTitleBlock(); tb.SetRevision(r11.REVISION); b.SetTitleBlock(tb)
        for n in NETS:
            b.Add(pcbnew.NETINFO_ITEM(b, n))
        for a, c in (((0, 0), (46, 0)), ((46, 0), (46, length)), ((46, length), (0, length)), ((0, length), (0, 0))):
            e = pcbnew.PCB_SHAPE(b); e.SetShape(pcbnew.SHAPE_T_SEGMENT); e.SetLayer(pcbnew.Edge_Cuts)
            e.SetStart(self.P(*a)); e.SetEnd(self.P(*c)); b.Add(e)

    def net(self, name):
        if not self.board.FindNet(name):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, name))
        return self.board.FindNet(name)

    @staticmethod
    def P(x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def hole(self, x, y):
        h = pcbnew.PCB_SHAPE(self.board); h.SetShape(pcbnew.SHAPE_T_CIRCLE); h.SetLayer(pcbnew.Edge_Cuts)
        h.SetCenter(self.P(x, y)); h.SetEnd(self.P(x + 1.6, y)); self.board.Add(h)

    def track(self, a, c, net='SIGNAL', layer=None, width=0.2):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(self.P(*a)); t.SetEnd(self.P(*c)); t.SetWidth(pcbnew.FromMM(width))
        t.SetLayer(pcbnew.F_Cu if layer is None else layer); t.SetNet(self.net(net)); self.board.Add(t)
        return t

    def via(self, x, y, net='SIGNAL', d=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(self.P(x, y)); v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(drill))
        v.SetNet(self.net(net)); self.board.Add(v)
        return v

    def part(self, ref, x, y, pads, part=None):
        """pads: [(number, net, (dx, dy), 'smd' | 'pth')]."""
        f = pcbnew.FOOTPRINT(self.board); f.SetReference(ref); f.SetPosition(self.P(x, y))
        if part:
            f.SetField('Manufacturer Part', part)
        self.board.Add(f)
        for num, net, (dx, dy), kind in pads:
            p = pcbnew.PAD(f); p.SetNumber(num)
            if kind == 'pth':
                p.SetAttribute(pcbnew.PAD_ATTRIB_PTH); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
                p.SetSize(self.P(1.8, 1.8)); p.SetDrillSize(self.P(1.0, 1.0)); p.SetLayerSet(pcbnew.PAD.PTHMask())
            else:
                p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetShape(pcbnew.PAD_SHAPE_RECT); p.SetSize(self.P(0.6, 1.7))
                ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); p.SetLayerSet(ls)
            if net:
                p.SetNet(self.net(net))
            f.Add(p); p.SetPosition(self.P(x + dx, y + dy))
        return f

    def gh(self, ref, x, y, nets, mouth=(0, 1), tab_net='GND'):
        """A side-entry GH header: contact pads in a row at 1.25 mm pitch, two fixing tabs 3.2 mm toward the mouth."""
        n = len(nets)
        ux, uy = mouth
        vx, vy = -uy, ux
        pads = [(str(i + 1), net, ((i - (n - 1) / 2) * 1.25 * vx, (i - (n - 1) / 2) * 1.25 * vy), 'smd')
                for i, net in enumerate(nets)]
        half = ((n - 1) * 1.25 + 3.7) / 2
        pads += [('MP', tab_net, (s * half * vx + 3.2 * ux, s * half * vy + 3.2 * uy), 'smd') for s in (-1, 1)]
        return self.part(ref, x, y, pads, part=f'SM{n:02d}B-GHS-TB(LF)(SN)')

    def zone(self, net, pts, layer):
        z = pcbnew.ZONE(self.board); z.SetNet(self.board.FindNet(net)); z.SetLayer(layer)
        z.SetMinThickness(pcbnew.FromMM(0.15)); z.SetLocalClearance(pcbnew.FromMM(0.2))
        o = z.Outline(); o.NewOutline()
        for x, y in pts:
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        return z

    def fill(self):
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())

    def run(self, only, **kw):
        kw.setdefault('data', {})
        kw.setdefault('port_pin', {'PC0': 'A1', 'PC5': 'A2', 'PC1': 'A3'})
        return r11.check_board(self.board, only=set(only), **kw)


def failing(report, rid):
    return report['rules'][rid]['issues']


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R11Rules(unittest.TestCase):
    def test_s8_covers_in3_and_in4(self):
        """D-R11-08: S-8 holds 1.0 mm from a pyro barrel on all four inner layers; R10's S-8 looks at In1 / In2 only."""
        s = Six()
        s.via(10, 10, 'RAW_ACT')
        s.track((10.8, 5), (10.8, 15), 'SIGNAL', pcbnew.In3_Cu)        # 0.65 mm from the 0.3 mm barrel wall
        rep = s.run({'S-8'})
        self.assertTrue(any('In3.Cu' in i and 'RAW_ACT' in i for i in failing(rep, 'S-8')), rep['rules']['S-8'])
        ctx = r11.make_ctx(s.board, data={})
        self.assertEqual(r10.s8(ctx)[0], [])                           # the R10 rule cannot see In3
        s2 = Six()
        s2.via(10, 10, 'ACT_GATE')
        s2.track((10.8, 5), (10.8, 15), 'GND', pcbnew.In4_Cu)          # GND counts for the gate-drive hazard nets
        self.assertTrue(failing(s2.run({'S-8'}), 'S-8'))
        s3 = Six()
        s3.via(10, 10, 'RAW_ACT')
        s3.track((10.8, 5), (10.8, 15), 'GND', pcbnew.In4_Cu)          # ... not for RAW_ACT
        s3.track((12.0, 5), (12.0, 15), 'SIGNAL', pcbnew.In3_Cu)       # 1.85 mm away
        self.assertEqual(failing(s3.run({'S-8'}), 'S-8'), [])

    def test_k_inner_six_layers(self):
        s = Six()
        s.track((1, 1), (5, 1), 'GND', pcbnew.In1_Cu)
        s.track((1, 2), (5, 2), 'GND', pcbnew.In4_Cu)
        s.track((1, 3), (5, 3), '3V3', pcbnew.In2_Cu)
        s.track((1, 4), (5, 4), 'USB_DP', pcbnew.In3_Cu)
        self.assertEqual(failing(s.run({'K-inner'}), 'K-inner'), [])
        for net, layer in (('SIGNAL', pcbnew.In4_Cu), ('3V3', pcbnew.In1_Cu), ('USB_DP', pcbnew.In2_Cu)):
            with self.subTest(net=net, layer=layer):
                s = Six()
                s.track((1, 1), (5, 1), net, layer)
                self.assertEqual(len(failing(s.run({'K-inner'}), 'K-inner')), 1)

    def test_w1_wire_pads(self):
        def build(j1=(('1', 'BAT_IN', 'pth'), ('2', 'GND', 'pth')), j121=(('1', 'PYRO1_OUT', 'pth'),
                                                                          ('2', 'PYRO1_IGN', 'pth'))):
            s = Six()
            s.part('J1', 5, 10, [(n, net, (0, 3 * i), k) for i, (n, net, k) in enumerate(j1)])
            s.part('J121', 5, 30, [(n, net, (0, 3 * i), k) for i, (n, net, k) in enumerate(j121)])
            return failing(s.run({'W-1'}), 'W-1')
        self.assertEqual(build(), [])
        self.assertTrue(build(j1=(('1', 'BAT_IN', 'smd'), ('2', 'GND', 'pth'))))                 # not plated
        self.assertTrue(build(j121=(('1', 'PYRO1_IGN', 'pth'), ('2', 'PYRO1_OUT', 'pth'))))      # swapped
        self.assertTrue(build(j1=(('1', 'BAT_IN', 'pth'), ('2', 'GND', 'pth'), ('3', 'GND', 'pth'))))
        self.assertTrue(build(j1=(('1', 'BAT_IN', 'pth'), ('MP', 'GND', 'pth'), ('2', 'GND', 'pth'))))

    def test_w2_and_s7_gh_ports(self):
        def build(**over):
            s = Six()
            nets = {ref: [want[str(i)] for i in range(1, len(want) + 1)] for ref, want in r11.GH_PORTS.items()}
            nets.update(over.get('nets', {}))
            for k, (ref, ns) in enumerate(sorted(nets.items())):
                f = s.gh(ref, 10 + 5 * k, 40, ns, tab_net=over.get('tab', {}).get(ref, 'GND'))
                if ref in over.get('part', {}):
                    f.SetField('Manufacturer Part', over['part'][ref])
            rep = s.run({'W-2', 'S-7'})
            return failing(rep, 'W-2') + failing(rep, 'S-7')
        self.assertEqual(build(), [])
        self.assertTrue(build(nets={'J9': ['CAM_5V', 'CAM_5V', 'GND', 'GND', 'CAM_TX_WIRE', 'CAM_RX_WIRE']}))
        self.assertTrue(build(nets={'J410': ['PORT_4V8', 'GND', 'GPS_RX_WIRE', 'GPS_TX_WIRE']}))
        self.assertTrue(build(tab={'J420': 'PORT_4V8'}))                 # a fixing tab on a supply
        self.assertTrue(build(tab={'J122': 'SIGNAL'}))
        self.assertTrue(build(part={'J440': 'SM05B-GHS-TB'}))            # wrong circuit count
        self.assertTrue(build(part={'J400': 'BM02B-GHS-TBT'}))           # top entry, not the side-entry header

    def test_m1_outline_and_m3_supports(self):
        pins = {'supports': [[4, 4], [42, 4], [4, 46], [42, 46]]}
        s = Six()
        for x, y in ((4, 4), (42, 4), (4, 46), (42, 46)):
            s.hole(x, y)
        rep = s.run({'M-1', 'M-3'}, data=pins)
        self.assertEqual(failing(rep, 'M-1') + failing(rep, 'M-3'), [])
        self.assertTrue(failing(s.run({'M-3'}), 'M-3'))                 # unpinned supports fail (D-R11-10)
        s.hole(23, 25)                                                   # a fifth, unpinned circle
        self.assertTrue(any('not a pinned support' in i for i in failing(s.run({'M-3'}, data=pins), 'M-3')))
        s = Six(length=60)
        for x, y in ((4, 4), (42, 4), (4, 56), (42, 56)):
            s.hole(x, y)
        self.assertTrue(failing(s.run({'M-1'}), 'M-1'))                 # above the 56 mm ceiling
        s = Six()
        for x, y in ((4, 4), (42, 4), (4, 46), (30, 25)):
            s.hole(x, y)                                                 # no support at the (46, 50) corner
        self.assertTrue(failing(s.run({'M-3'}, data={'supports': [[4, 4], [42, 4], [4, 46], [30, 25]]}), 'M-3'))
        s = Six()
        for x, y in ((4, 4), (42, 4), (4, 46), (42, 46)):
            s.hole(x, y)
        self.assertTrue(failing(s.run({'M-3'}, data={'supports': [[4, 4], [42, 4], [4, 46], [42, 45]]}), 'M-3'))

    def test_m7_needs_the_recorded_imu_pose(self):
        s = Six()
        self.assertTrue(any('imu record' in i for i in failing(s.run({'M-7'}), 'M-7')))

    def test_k_reference_and_k_region_on_the_six_layer_stack(self):
        def build(in2=(('3V3', (0, 0, 46, 50)),), in1=True, in4=True, layer=None, x=(5, 30)):
            s = Six()
            for net, (x0, y0, x1, y1) in in2:
                s.zone(net, ((x0, y0), (x1, y0), (x1, y1), (x0, y1)), pcbnew.In2_Cu)
            if in1:
                s.zone('GND', ((0, 0), (46, 0), (46, 50), (0, 50)), pcbnew.In1_Cu)
            if in4:
                s.zone('GND', ((0, 0), (46, 0), (46, 50), (0, 50)), pcbnew.In4_Cu)
            s.fill()
            s.track((x[0], 20), (x[1], 20), 'USB_DP', layer if layer is not None else pcbnew.In3_Cu)
            rep = s.run({'K-reference', 'K-region'})
            ref = [i for i in failing(rep, 'K-reference') if 'stale critical_reference' not in i]   # a synthetic board
            return ref, failing(rep, 'K-region')
        self.assertEqual(build(), ([], []))
        ref, region = build(in2=(('3V3', (0, 0, 20, 50)), ('PORT_4V8', (20.5, 0, 46, 50))))
        self.assertEqual(ref, [])                                        # In4 GND still lies under it
        self.assertTrue(region)                                          # but the In3 run crosses two In2 planes
        self.assertTrue(build(in2=(('3V3', (0, 0, 20, 50)),))[1])        # ... or runs off In2 copper
        self.assertTrue(build(in4=False)[0])                             # In3 over no In4 GND (D-R11-03)
        self.assertEqual(build(layer=pcbnew.F_Cu, in2=()), ([], []))     # F.Cu over In1 GND
        self.assertTrue(build(layer=pcbnew.F_Cu, in1=False)[0])
        self.assertEqual(build(layer=pcbnew.B_Cu), ([], []))             # B.Cu over In4 GND
        self.assertTrue(build(layer=pcbnew.B_Cu, in4=False)[0])
        s = Six()
        stale = [i for i in failing(s.run({'K-reference'}), 'K-reference') if 'stale critical_reference' in i]
        self.assertTrue(stale)                                           # listed names that are no net still fail

    def test_k_ports_use_j9s_r11_uart_pins(self):
        self.assertIn(('J9', '5', 'D401.1', 'R100'), r11.PORT_CLAMPS_R11)
        self.assertIn(('J9', '6', 'D400.1', 'R101'), r11.PORT_CLAMPS_R11)
        self.assertEqual(len(r11.PORT_CLAMPS_R11), len(r10.PORT_CLAMPS))

    def test_power_paths_keep_floors_but_drop_r10_coordinates(self):
        self.assertEqual([(p['name'], p['floor'], p['vias']['count']) for p in r11.POWER_PATHS_R11],
                         [(p['name'], p['floor'], p['vias']['count']) for p in r10.POWER_PATHS])
        self.assertFalse(any('bridges' in p['vias'] or 'layers' in p for p in r11.POWER_PATHS_R11))

    def test_rule_selection_fails_closed(self):
        with self.assertRaises(ValueError):
            r11.selected_rules(set())
        with self.assertRaises(ValueError):
            r11.selected_rules({'P-11'})                                 # a dropped R10 rule is not an R11 id
        self.assertLess(r11.STAGES['functional'], r11.STAGES['full'])
        s = Six()
        rep = s.run({'S-1'}, port_pin={})                                # no ball for PC0: the rule cannot run
        self.assertFalse(rep['ok'])
        self.assertIn('could not run', rep['issues'][0])


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R11Fixes(unittest.TestCase):
    """The stage B follow-up: the R11 pin table's balls, the sense-node exemption on them, S-3c, the wire pads."""

    def test_pin_table_reads_r11_balls_and_skips_comments(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'pin_table.tsv'
            p.write_text('# comment line\npin\tport\tr11_ball\tr11_net\n15\tPC0\tF1\tPYRO1_CONT\n-\tVREF+\t-\t-\n')
            self.assertEqual(r11.pin_table(p), {'PC0': 'F1'})              # the ball, not the LQFP pin 15
            p.write_text('pin\tport\n15\tPC0\n')
            with self.assertRaises(ValueError):
                r11.pin_table(p)                                          # no r11_ball column: fail, never guess
        table = r11.pin_table()
        self.assertEqual((table['PC0'], table['PC5'], table['PC1']), ('F1', 'H4', 'F2'))

    def board(self, adc_ball='F1'):
        s = Six()
        s.part('U1', 23, 25, [('F1', 'PYRO1_CONT' if adc_ball == 'F1' else 'SIGNAL', (0, 0), 'smd'),
                              ('H4', 'ARM1_SENSE', (1, 0), 'smd'), ('E5', '3V3', (2, 0), 'smd'),
                              ('E6', 'GND', (3, 0), 'smd')] +
               ([] if adc_ball == 'F1' else [(adc_ball, 'PYRO1_CONT', (4, 0), 'smd')]))
        return s

    def test_s2_exempts_the_sense_nodes_only_on_their_own_balls(self):
        ties = [i for i in failing(self.board().run({'S-2'}, port_pin={'PC0': 'F1', 'PC5': 'H4', 'PC1': 'F2'}), 'S-2')
                if 'U1 has pads' in i]
        self.assertEqual(ties, [])
        ties = [i for i in failing(self.board('G1').run({'S-2'}, port_pin={'PC0': 'F1', 'PC5': 'H4', 'PC1': 'F2'}),
                                   'S-2') if 'U1 has pads' in i and 'PYRO1_CONT' in i]
        self.assertTrue(ties)                                            # PYRO1_CONT on a second ball is a tie

    def test_s3c_is_full_stage_only_and_holds_the_copper_rule(self):
        self.assertIn('S-3c', r11.STAGES['full'])
        self.assertNotIn('S-3c', r11.STAGES['placement'])
        rep = Six().run({'S-3c'})
        self.assertTrue(failing(rep, 'S-3c'))                            # no load switch / no copper: fails

    def test_wire_pads_must_be_off_the_jlc_upload_and_fitted(self):
        def issues(attrs):
            s = Six()
            for ref, nets in r11.WIRE_PADS.items():
                f = s.part(ref, 5, 10 if ref == 'J1' else 30,
                           [(n, net, (0, 3 * i), 'pth') for i, (n, net) in enumerate(sorted(nets.items()))])
                f.SetAttributes(attrs)
            ctx = r11.make_ctx(s.board, data={})
            return r11.wire_pad_population(ctx)
        off = pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
        self.assertEqual(issues(off), [])
        self.assertEqual(len(issues(pcbnew.FP_EXCLUDE_FROM_BOM)), 2)     # still in the position file
        self.assertEqual(len(issues(off | pcbnew.FP_DNP)), 2)
        with tempfile.TemporaryDirectory() as d:
            bom = Path(d) / 'bom.csv'
            bom.write_text('Designator,Qty\nJ121,1\n')
            s = Six()
            ctx = r11.make_ctx(s.board, data={}); ctx.bom = bom
            self.assertTrue(any('J121 are in the JLC upload' in i for i in r11.wire_pad_population(ctx)))


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R11Fit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_gh_envelope_follows_the_mouth_and_must_face_its_edge(self):
        s = Six()
        f = s.gh('J410', 44.5, 25, ['PORT_4V8', 'GND', 'GPS_TX_WIRE', 'GPS_RX_WIRE'], mouth=(1, 0))
        n = fc.gh_circuits(f)
        self.assertEqual(n, 4)
        header, mated, mouth, problems = fc.gh_envelope(f, n, (0, 0, 46, 50))
        self.assertEqual((mouth, problems), ((1.0, 0.0), []))
        g = fc.GH_DRAWING
        self.assertAlmostEqual(mated[2] - mated[0], g['housing_length'] + fc.GH_WIRE_STRAIGHT, places=6)
        self.assertAlmostEqual(mated[3] - mated[1], 1.25 * 3 + g['header_extra_width'], places=6)
        self.assertAlmostEqual(mated[5], g['header_height'], places=6)
        self.assertLess(fc.margin(mated, 24.9, 23.0, 0.3), 0)            # a plug straight out of the long edge
        s = Six()
        f = s.gh('J420', 30, 25, ['PORT_4V8', 'GND', 'RADIO_TX_WIRE', 'RADIO_RX_WIRE'], mouth=(1, 0))
        self.assertTrue(fc.gh_envelope(f, 4, (0, 0, 46, 50))[3])        # mid-board, facing no edge
        s = Six()
        f = s.gh('J400', 23, 1.5, ['BAT_IN', 'GND'], mouth=(0, -1))      # aft short edge: the plug leaves axially
        _, mated, _, problems = fc.gh_envelope(f, 2, (0, 0, 46, 50))
        self.assertEqual(problems, [])
        self.assertGreater(fc.margin(mated, 24.9, 23.0, 0.3), 0)

    def test_r11_profile_requires_six_layers_ports_wire_pads_and_corner_supports(self):
        s = Six()
        for x, y in ((4, 4), (42, 4), (4, 46), (42, 46)):
            s.hole(x, y)
        rep = fc.check_board(s.board, self.folder, profile='r11')
        text = '\n'.join(rep['issues'])
        for ref in sorted(fc.R11_MATED_REFS):
            self.assertIn(f'{ref}: required R11 mated envelope missing', text)
        for ref in sorted(fc.WIRE_PAD_REFS):
            self.assertIn(f'{ref}: required R11 wire-pad footprint missing', text)
        self.assertNotIn('corner', text)
        b4 = pcbnew.BOARD(); b4.SetCopperLayerCount(4)
        for a, c in (((0, 0), (46, 0)), ((46, 0), (46, 50)), ((46, 50), (0, 50)), ((0, 50), (0, 0))):
            e = pcbnew.PCB_SHAPE(b4); e.SetShape(pcbnew.SHAPE_T_SEGMENT); e.SetLayer(pcbnew.Edge_Cuts)
            e.SetStart(Six.P(*a)); e.SetEnd(Six.P(*c)); b4.Add(e)
        self.assertTrue(any('six-layer' in i for i in fc.check_board(b4, self.folder, profile='r11')['issues']))

    def test_wire_pad_allocation_meets_other_bodies(self):
        s = Six()
        s.part('J1', 3, 25, [('1', 'BAT_IN', (0, 0), 'pth'), ('2', 'GND', (0, 3), 'pth')])
        boxes = fc.wire_pad_boxes(s.board.FindFootprintByReference('J1'))
        self.assertEqual(len(boxes), 2)
        label, above, below = boxes[0]
        self.assertAlmostEqual(above[5], fc.WIRE_ALLOWANCE['above'])
        self.assertAlmostEqual(below[4], -fc.BOARD_T - fc.WIRE_ALLOWANCE['tail'])
        rep = fc.check_board(s.board, self.folder, profile='r11')
        self.assertIn('J1.1 wire', rep['wire_pads'])


def real_board():
    path = os.environ.get('R11_BOARD')
    if path and Path(path).is_file():
        return Path(path)
    return None


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R11RealBoard(unittest.TestCase):
    """Seeds on temporary copies of the R11 board (R11_BOARD); skipped without it unless R11_BOARD_REQUIRED=1."""

    def setUp(self):
        self.path = real_board()
        if self.path is None:
            if os.environ.get('R11_BOARD_REQUIRED') == '1':
                self.fail('R11_BOARD_REQUIRED=1 but R11_BOARD names no board: the real-board seeds may not be skipped')
            self.skipTest('R11_BOARD not set (no R11 board yet)')
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.copy = Path(self.temp.name) / 'r11'
        shutil.copytree(self.path.parent, self.copy, ignore=shutil.ignore_patterns('fab', '*.lck', '__pycache__'))
        self.board = pcbnew.LoadBoard(str(self.copy / self.path.name))

    def run_rules(self, only):
        return r11.check_board(self.board, self.copy, self.copy / self.path.name, only=set(only))

    def test_board_is_r11_and_six_layers(self):
        self.assertEqual(self.board.GetTitleBlock().GetRevision(), r11.REVISION)
        self.assertEqual(self.board.GetCopperLayerCount(), 6)

    def test_safety_rules_hold_and_catch_a_seeded_in3_track_at_a_pyro_barrel(self):
        self.assertEqual(self.run_rules({'S-1', 'S-2', 'S-3', 'S-5', 'S-8', 'W-1', 'W-2'})['issues'], [])
        vias = [t for t in self.board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() in r10.BARREL_NETS]
        pads = [p for f in self.board.GetFootprints() for p in f.Pads()
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() in r10.BARREL_NETS]
        at = (vias[0] if vias else pads[0]).GetPosition()
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(at.x + pcbnew.FromMM(0.7), at.y - pcbnew.FromMM(2)))
        t.SetEnd(pcbnew.VECTOR2I(at.x + pcbnew.FromMM(0.7), at.y + pcbnew.FromMM(2)))
        t.SetWidth(pcbnew.FromMM(0.1)); t.SetLayer(pcbnew.In3_Cu)
        t.SetNet(self.board.FindNet('3V3'))                           # foreign, non-GND copper on In3
        self.board.Add(t)
        self.assertTrue(self.run_rules({'S-8'})['issues'])

    def test_placement_stage_passes_and_catches_seeded_placement_faults(self):
        full = r11.check_board(self.board, self.copy, self.copy / self.path.name, stage='placement')
        self.assertEqual(full['issues'], [])
        j1 = self.board.FindFootprintByReference('J1')
        j1.SetAttributes(j1.GetAttributes() & ~pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        self.assertTrue(self.run_rules({'S-4'})['issues'])
        hole = next(d for d in self.board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts
                    and d.GetShape() == pcbnew.SHAPE_T_CIRCLE)
        hole.Move(pcbnew.VECTOR2I(pcbnew.FromMM(0.05), 0))
        self.assertTrue(self.run_rules({'M-3'})['issues'])
        u1 = self.board.FindFootprintByReference('U1')
        ball = r11.pin_table()['PC0']
        spare = next(p for p in u1.Pads() if p.GetNumber() != ball and p.GetNetname().startswith('unconnected'))
        spare.SetNet(self.board.FindNet('PYRO1_CONT'))
        self.assertTrue(self.run_rules({'S-2'})['issues'])

    def test_a_swapped_pyro_wire_pad_fails(self):
        j121 = self.board.FindFootprintByReference('J121')
        a, b = j121.FindPadByNumber('1'), j121.FindPadByNumber('2')
        na, nb = a.GetNet(), b.GetNet()
        a.SetNet(nb); b.SetNet(na)
        self.assertTrue(self.run_rules({'W-1'})['issues'])

    def test_route_check_r11_is_clean(self):
        rc.set_profile('r11'); self.addCleanup(rc.set_profile, 'r8')
        failures, _, stale = rc.evaluate(rc.scan(self.board))
        self.assertEqual((failures, stale), ([], []))


if __name__ == '__main__':
    unittest.main()
