"""Seeded R10 safety/profile regressions (tools/check_r10.py, route_check r10): synthetic boards for every new or
changed rule, and seeded faults on a temporary copy of a real R10 board (R10_BOARD, else the repository board when it
is M3-ASSY-R10). No git, no writes beside the source board, no headless DRC.
Run with KiCad's Python: python3 -I tools/test_r10_check.py  (R10_BOARD=path/to/m3.kicad_pcb for the real-board seeds)"""
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_r10 as gate
try:
    import pcbnew
except ImportError:
    pcbnew = None


class Assembly(unittest.TestCase):
    def test_required_safety_part_exclusion_flags_and_omission(self):
        for ref in ('R134', 'R127', 'R128', 'C126'):
            clean = f'(kicad_pcb (footprint "part" (property "Reference" "{ref}") (attr smd)))'
            self.assertEqual(gate.population(clean, {ref}), [])
            for flag in ('dnp', 'exclude_from_bom', 'exclude_from_pos_files', 'board_only'):
                with self.subTest(ref=ref, flag=flag):
                    mutant = clean.replace('(attr smd)', f'(attr smd {flag})')
                    self.assertTrue(gate.population(mutant, {ref}))
            self.assertTrue(gate.population('(kicad_pcb)', {ref}))

    def test_schematic_required_part_flags(self):
        for flag in ('(dnp yes)', '(in_bom no)', '(on_board no)'):
            text = f'(kicad_sch (symbol (property "Reference" "R134") {flag}))'
            self.assertTrue(gate.population(text, {'R134'}, schematic=True))
        clean = '(kicad_sch (symbol (property "Reference" "R134") (in_bom yes) (on_board yes) (dnp no)))'
        self.assertEqual(gate.population(clean, {'R134'}, schematic=True), [])

    def test_bom_and_cpl_omissions(self):
        self.assertEqual(gate.assembly_population('Designator,Qty\n"R127,R128",2\nR134,1\n', {'R127', 'R128', 'R134'}), [])
        self.assertTrue(gate.assembly_population('Designator,Qty\nR127,1\n', {'R134'}))

    def test_uart_isolation_and_bias_seeds(self):
        import json
        contract = json.loads((gate.ROOT / 'm3_design/assembly_review/sources/r10_design/circuit.json').read_text())
        pins, values, codes = {}, {}, {}
        for ref, part in contract['parts'].items():
            values[ref] = part['value']; codes[ref] = part['fields']['LCSC']
            pins.update({f'{ref}.{p}': n for p, n in part['nets'].items()})
        self.assertEqual(gate.uart_ports(pins, values, codes), [])
        for pin, net in (('U411.7', '3V3'), ('U421.6', '3V3'), ('R442.2', '3V3'),
                         ('U422.1', 'PORT_4V8'), ('R450.2', 'RADIO_RX_MCU'), ('D410.2', '3V3')):
            with self.subTest(pin=pin):
                mutant = dict(pins); mutant[pin] = net
                self.assertTrue(gate.uart_ports(mutant, values, codes))

    def test_port_supply_enable_fault_and_limit_seeds(self):
        import json
        contract = json.loads((gate.ROOT / 'm3_design/assembly_review/sources/r10_design/circuit.json').read_text())
        pins, values, codes = {}, {}, {}
        for ref, part in contract['parts'].items():
            values[ref] = part['value']; codes[ref] = part['fields']['LCSC']
            pins.update({f'{ref}.{p}': n for p, n in part['nets'].items()})
        pins.update({f'U1.{p}': n for p, n in gate.MCU.items()})
        pins.update({'U1.41': 'CAM_PWR_EN', 'U1.42': 'CAM_FAULT_N'})          # D-R2-07 pin swap
        self.assertEqual(gate.port_power(pins, values, codes), [])
        for pin, net in (('U410.1', '3V3'), ('U420.6', 'CAM_5V'), ('U401.9', 'RAW_PROTECTED'),
                         ('R431.2', '3V3'), ('R412.2', 'GPS_4V8'), ('R420.2', 'RADIO_FAULT_N')):
            with self.subTest(pin=pin):
                mutant = dict(pins); mutant[pin] = net
                self.assertTrue(gate.port_power(mutant, values, codes))
        mutant = dict(values); mutant['R430'] = '1k 1%'
        self.assertTrue(gate.port_power(pins, mutant, codes))
        mutant = dict(pins); mutant['J420.5'] = 'RADIO_PWR_EN'
        self.assertTrue(gate.port_power(mutant, values, codes))


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class Native(unittest.TestCase):
    def point(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def setUp(self):
        import route_check
        self.addCleanup(route_check.set_profile, 'r8')
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(4)
        for net in ('RAW_ACT', 'PYRO1_BUS', 'GPS_TX_MCU', 'GND'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))

    def terminal(self, diameter=1.9):
        f = pcbnew.FOOTPRINT(self.board); f.SetReference('J124'); self.board.Add(f)
        pads = []
        for num, x, net in (('1', 0, 'PYRO1_BUS'), ('2', 3.5, 'RAW_ACT')):
            p = pcbnew.PAD(f); p.SetNumber(num); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            p.SetAttribute(pcbnew.PAD_ATTRIB_PTH); p.SetLayerSet(pcbnew.LSET.AllCuMask())
            p.SetSize(self.point(diameter, diameter)); p.SetDrillSize(self.point(1.3, 1.3))
            p.SetPosition(self.point(x, 0)); p.SetNet(self.board.FindNet(net)); f.Add(p); pads.append(p)
        return pads

    def test_same_part_actual_gap_and_1_49_seed(self):
        pads = self.terminal()
        issues, evidence = gate.arm_gap(self.board)
        self.assertEqual(issues, [], evidence)
        self.assertAlmostEqual(evidence['closest'][0], 1.6, places=2)
        for p in pads:
            p.SetSize(self.point(2.01, 2.01))
        self.assertTrue(gate.arm_gap(self.board)[0])

    def test_adjoining_copper_gap(self):
        self.terminal()
        self.assertEqual(gate.arm_gap(self.board)[0], [])
        t = pcbnew.PCB_TRACK(self.board); t.SetNet(self.board.FindNet('RAW_ACT'))
        t.SetLayer(pcbnew.F_Cu); t.SetWidth(pcbnew.FromMM(.2))
        t.SetStart(self.point(3.5, 0)); t.SetEnd(self.point(2, 0)); self.board.Add(t)
        self.assertTrue(gate.arm_gap(self.board)[0])

    def test_route_profile_restores_r9_and_has_no_exceptions(self):
        import route_check as rc
        rc.set_profile('r10')
        self.assertEqual((rc.ALLOWLIST, rc.LEFTOVERS, rc.ROUTE_FIGURES), ([], [], {}))
        self.assertIn(rc.net_class('GPS_TX_MCU'), rc.SIGNAL_CRITICAL)
        self.assertEqual(rc.net_class('GPS_4V8'), 'power')
        rc.set_profile('r9')
        self.assertEqual(rc.net_class('GPS_TX_MCU'), 'other')
        self.assertEqual((rc.ALLOWLIST, rc.LEFTOVERS, rc.ROUTE_FIGURES), ([], [], {}))

    def test_new_uart_split_reference_seed(self):
        import critical_reference as cr
        track = pcbnew.PCB_TRACK(self.board); track.SetNet(self.board.FindNet('GPS_TX_MCU'))
        track.SetLayer(pcbnew.F_Cu); track.SetWidth(pcbnew.FromMM(.2))
        track.SetStart(self.point(0, 0)); track.SetEnd(self.point(2, 0)); self.board.Add(track)
        poly = pcbnew.SHAPE_POLY_SET(); poly.NewOutline()
        for x, y in ((-1, -1), (3, -1), (3, 1), (-1, 1)):
            poly.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        with patch.object(cr, 'fills', return_value={pcbnew.F_Cu: poly}):
            self.assertEqual(gate.references(self.board)[0], [])
        split = pcbnew.SHAPE_POLY_SET(); split.NewOutline()
        for x, y in ((-1, -1), (.9, -1), (.9, 1), (-1, 1)):
            split.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        with patch.object(cr, 'fills', return_value={pcbnew.F_Cu: split}):
            self.assertTrue(gate.references(self.board)[0])

    def test_fifth_support_and_all_new_plug_refs(self):
        import fit_check as fit
        holes = [(4, 4), (42, 4), (4, 80), (42, 80), (42, 42)]
        self.assertEqual(fit.support_check(holes, (0, 0, 46, 84), [], retention=[])[2], [])
        self.assertTrue(fit.support_check(holes[:-1], (0, 0, 46, 84), [], retention=[])[2])
        refs = {r for spec in fit.R10_MATED.values() for r in spec['refs']}
        self.assertTrue(fit.R10_MATED_REFS <= refs)
        with patch.dict(fit.R10_MATED, {}, clear=True), patch.object(
                fit, 'board_geometry', return_value=(holes, (0, 0, 46, 84))):
            report = fit.check_board(self.board, Path('/tmp'), profile='r10')
        self.assertTrue(any('required R10 mated envelope missing' in s for s in report['issues']))


# ======================================================================================================================
# check_r10 rules S-1..S-7 and M-1 on small synthetic boards (no board file needed)
# ======================================================================================================================
@unittest.skipUnless(pcbnew, 'KiCad Python required')
class Synthetic(unittest.TestCase):
    NETS = ('RAW_ACT', 'PYRO1_BUS', 'PYRO1_IGN', 'BAT_IN', 'ACT_FET_S', 'ACT_GATE', 'ACT_DRV', 'PYRO1_GATE',
            'PYRO1_GATE_N', 'GND', 'GPS_TX_MCU', 'SERVO1_OUT', 'RAW_PROTECTED')

    def P(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def setUp(self):
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(4)
        for net in self.NETS:
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
        self.outline(46, 90)
        self.j124 = self.part('J124', [('1', 0, 0, 'PYRO1_BUS'), ('2', 3.5, 0, 'RAW_ACT')], at=(5, 20), tht=True)

    def outline(self, w, h):
        r = pcbnew.PCB_SHAPE(self.board)
        r.SetShape(pcbnew.SHAPE_T_RECT); r.SetLayer(pcbnew.Edge_Cuts)
        r.SetStart(self.P(0, 0)); r.SetEnd(self.P(w, h)); self.board.Add(r)
        return r

    def part(self, ref, pads, at=(0, 0), tht=False, size=1.9):
        f = pcbnew.FOOTPRINT(self.board); f.SetReference(ref); self.board.Add(f)
        f.SetPosition(self.P(*at))
        for num, x, y, net in pads:
            p = pcbnew.PAD(f); p.SetNumber(num); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            if tht:
                p.SetAttribute(pcbnew.PAD_ATTRIB_PTH); p.SetLayerSet(pcbnew.LSET.AllCuMask())
                p.SetDrillSize(self.P(1.3, 1.3))
            else:
                p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); p.SetLayerSet(ls)
            s = size if tht else 0.6
            p.SetSize(self.P(s, s)); p.SetPosition(self.P(at[0] + x, at[1] + y))
            if net:
                p.SetNet(self.board.FindNet(net))
            f.Add(p)
        return f

    def track(self, a, b, net=None, layer=None, width=0.2):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(self.P(*a)); t.SetEnd(self.P(*b)); t.SetWidth(pcbnew.FromMM(width))
        t.SetLayer(pcbnew.F_Cu if layer is None else layer)
        if net:
            t.SetNet(self.board.FindNet(net))
        self.board.Add(t)
        return t

    def ctx(self):
        return gate.make_ctx(self.board)

    def load_switch(self):
        for ref, drain, y in (('Q120', 'BAT_IN', 40), ('Q121', 'RAW_ACT', 50)):
            self.part(ref, [('1', 0, 0, 'ACT_FET_S'), ('2', 1, 0, 'ACT_FET_S'), ('3', 2, 0, 'ACT_FET_S'),
                            ('4', 3, 0, 'ACT_GATE')] + [(str(k), k - 5, 3, drain) for k in range(5, 10)], at=(20, y))

    # --- S-1 ARM break --------------------------------------------------------------------------------------------
    def test_s1_clean_terminal(self):
        self.assertEqual(gate.s1(self.ctx())[0], [])

    def test_s1_track_bridges_j124(self):
        for net in (None, 'RAW_ACT', 'GND'):
            with self.subTest(net=net):
                t = self.track((5, 20), (8.5, 20), net, pcbnew.B_Cu)
                self.assertTrue(any('ARM break is bridged' in i for i in gate.s1(self.ctx())[0]))
                self.board.Remove(t)

    def test_s1_track_chain_and_via_bridge(self):
        self.track((5, 20), (5, 25), None, pcbnew.F_Cu)
        v = pcbnew.PCB_VIA(self.board); v.SetPosition(self.P(5, 25)); v.SetWidth(pcbnew.FromMM(0.6))
        v.SetDrill(pcbnew.FromMM(0.3)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); self.board.Add(v)
        self.track((5, 25), (8.5, 25), None, pcbnew.B_Cu)
        self.assertEqual(gate.s1(self.ctx())[0], [])            # not yet joined to J124.2
        self.track((8.5, 25), (8.5, 20), None, pcbnew.B_Cu)
        self.assertTrue(any('bridged' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_part_bypasses_j124(self):
        self.part('R999', [('1', 0, 0, 'RAW_ACT'), ('2', 1.5, 0, 'PYRO1_BUS')], at=(30, 30))
        self.assertTrue(any('without J124' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_part_bypass_through_another_net(self):
        self.part('R998', [('1', 0, 0, 'RAW_ACT'), ('2', 1.5, 0, 'PYRO1_GATE_N')], at=(30, 30))
        self.part('R997', [('1', 0, 0, 'PYRO1_GATE_N'), ('2', 1.5, 0, 'PYRO1_IGN')], at=(30, 35))
        self.assertTrue(any('PYRO1_IGN without J124' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_divider_feet_on_gnd_do_not_bridge(self):
        self.part('R996', [('1', 0, 0, 'RAW_ACT'), ('2', 1.5, 0, 'GND')], at=(30, 30))
        self.part('R995', [('1', 0, 0, 'PYRO1_BUS'), ('2', 1.5, 0, 'GND')], at=(30, 35))
        self.assertEqual(gate.s1(self.ctx())[0], [])

    def test_s1_test_pad_on_armed_copper(self):
        self.part('TP9', [('1', 0, 0, 'PYRO1_BUS')], at=(30, 30))
        self.assertTrue(any('test pad TP9' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_j124_pad_nets(self):
        self.j124.FindPadByNumber('2').SetNet(self.board.FindNet('BAT_IN'))
        self.assertTrue(any('exactly one RAW_ACT' in i for i in gate.s1(self.ctx())[0]))

    # --- S-2 pyro feed --------------------------------------------------------------------------------------------
    def test_s2_load_switch_topology(self):
        self.load_switch()
        self.assertEqual(gate.s2(self.ctx())[0], [])
        self.board.FindFootprintByReference('Q121').FindPadByNumber('5').SetNet(self.board.FindNet('BAT_IN'))
        self.assertTrue(any('Q121 must be drain RAW_ACT' in i for i in gate.s2(self.ctx())[0]))

    def test_s2_raw_act_fed_from_raw_protected(self):
        self.load_switch()
        self.part('R994', [('1', 0, 0, 'RAW_ACT'), ('2', 1.5, 0, 'RAW_PROTECTED')], at=(30, 30))
        self.assertTrue(any('RAW_ACT is joined to RAW_PROTECTED' in i for i in gate.s2(self.ctx())[0]))

    def test_s2_armed_bus_fed_from_battery(self):
        self.load_switch()
        self.part('R993', [('1', 0, 0, 'PYRO1_BUS'), ('2', 1.5, 0, 'BAT_IN')], at=(30, 30))
        self.assertTrue(any('armed bus is joined to BAT_IN' in i for i in gate.s2(self.ctx())[0]))

    def test_s2_copper_short_to_supply(self):
        self.load_switch()
        self.part('C999', [('1', 0, 0, 'BAT_IN'), ('2', 1.5, 0, 'GND')], at=(30, 30))
        self.track((8.5, 20), (30, 30), None)
        self.assertTrue(any('RAW_ACT copper touches C999.1 (BAT_IN)' in i for i in gate.s2(self.ctx())[0]))

    # --- S-3 gate networks ----------------------------------------------------------------------------------------
    def gates(self):
        self.load_switch()
        self.part('U1', [('3', 0, 0, 'PYRO1_GATE_N'), ('5', 1, 0, 'GND'), ('6', 2, 0, 'GND'), ('7', 3, 0, 'GND'),
                         ('8', 4, 0, 'GND'), ('9', 5, 0, 'GND')], at=(25, 70))
        self.part('Q124', [('1', 0, 0, 'GND'), ('2', 1, 0, 'GND'), ('3', 2, 0, 'GND'), ('4', 3, 0, 'PYRO1_GATE'),
                           ('5', 1, 3, 'PYRO1_IGN')], at=(10, 60))
        self.part('R128', [('1', 0, 0, 'PYRO1_GATE'), ('2', 1.5, 0, 'GND')], at=(10, 70))
        self.part('C126', [('1', 0, 0, 'PYRO1_GATE'), ('2', 1.5, 0, 'GND')], at=(10, 72))
        self.part('R126', [('1', 0, 0, 'PYRO1_GATE_N'), ('2', 1.5, 0, 'PYRO1_GATE')], at=(10, 74))
        self.part('R120', [('1', 0, 0, 'ACT_FET_S'), ('2', 1.5, 0, 'ACT_GATE')], at=(30, 70))
        self.part('C120', [('1', 0, 0, 'ACT_FET_S'), ('2', 1.5, 0, 'ACT_GATE')], at=(30, 72))
        self.part('R121', [('1', 0, 0, 'ACT_GATE'), ('2', 1.5, 0, 'ACT_DRV')], at=(30, 74))

    def test_s3_gate_networks(self):
        self.gates()
        self.assertEqual(gate.s3(self.ctx())[0], [])
        for ref, pad, net, word in (('R128', '2', 'PYRO1_IGN', 'pull'), ('C126', '2', 'PYRO1_IGN', 'capacitor'),
                                    ('R120', '1', 'BAT_IN', 'resistor from the gate'),
                                    ('C120', '1', 'BAT_IN', 'gate-source capacitor')):
            with self.subTest(ref=ref):
                p = self.board.FindFootprintByReference(ref).FindPadByNumber(pad)
                old = p.GetNet()
                p.SetNet(self.board.FindNet(net))
                self.assertTrue(gate.s3(self.ctx())[0], ref)
                p.SetNet(old)
        self.board.Remove(self.board.FindFootprintByReference('R126'))
        self.assertTrue(any('series resistor' in i for i in gate.s3(self.ctx())[0]))

    # --- S-4 required fitted (board flags) ------------------------------------------------------------------------
    def test_s4_board_flags_and_omission(self):
        f = self.part('R134', [('1', 0, 0, 'PYRO1_IGN'), ('2', 1.5, 0, 'PYRO1_BUS')], at=(30, 30))
        self.assertEqual(gate.board_population(self.board, {'R134'}), [])
        for flag in (pcbnew.FP_DNP, pcbnew.FP_EXCLUDE_FROM_BOM, pcbnew.FP_EXCLUDE_FROM_POS_FILES,
                     pcbnew.FP_BOARD_ONLY):
            with self.subTest(flag=flag):
                f.SetAttributes(f.GetAttributes() | flag)
                self.assertTrue(gate.board_population(self.board, {'R134'}))
                f.SetAttributes(f.GetAttributes() & ~flag)
        f.SetValue('DNP')
        self.assertTrue(gate.board_population(self.board, {'R134'}))
        self.assertTrue(gate.board_population(self.board, {'R127'}))
        self.assertTrue(gate.SAFETY_FITTED <= gate.REQUIRED_FITTED)
        for ref in ('R134', 'R126', 'R127', 'R128', 'C126', 'Q124', 'Q120', 'Q121', 'R120', 'C120', 'J124', 'J121',
                    'R129', 'R130', 'R131', 'R132', 'R133', 'R173', 'R175', 'R178', 'R180', 'R168', 'R170', 'C128'):
            self.assertIn(ref, gate.SAFETY_FITTED)

    # --- S-5 J124 gap ---------------------------------------------------------------------------------------------
    def test_s5_pad_moved_closer(self):
        self.assertEqual(gate.s5(self.ctx())[0], [])
        self.j124.FindPadByNumber('2').SetPosition(self.P(8.3, 20))
        found = gate.s5(self.ctx())[0]
        self.assertTrue(any('pad to pad 1.400' in i for i in found), found)

    def test_s5_bus_track_inside_courtyard(self):
        self.track((5, 20), (6.9, 20), 'PYRO1_BUS')
        self.assertTrue(any('copper gap' in i for i in gate.s5(self.ctx())[0]))

    # --- S-6 external ports ---------------------------------------------------------------------------------------
    def test_s6_port_net_beside_pyro_bus(self):
        self.track((5, 22.0), (12, 22.0), 'GPS_TX_MCU')         # 1.0 mm from the pad edges: fine
        self.assertEqual(gate.s6(self.ctx())[0], [])
        self.track((3, 21.1), (7, 21.1), 'GPS_TX_MCU')          # 0.05 mm from J124.1's copper
        self.assertTrue(any('GPS_TX_MCU' in i and 'PYRO1_BUS' in i for i in gate.s6(self.ctx())[0]))

    def test_s6_shared_copper_and_shared_part(self):
        self.track((5, 20), (5, 26), 'GPS_TX_MCU')
        self.assertTrue(any('shared copper' in i for i in gate.s6(self.ctx())[0]))
        self.board.Remove(self.board.GetTracks()[0])
        self.part('R992', [('1', 0, 0, 'GPS_TX_MCU'), ('2', 1.5, 0, 'ACT_GATE')], at=(30, 30))
        self.assertTrue(any('R992 joins port nets' in i for i in gate.s6(self.ctx())[0]))
        self.part('U1', [('1', 0, 0, 'GPS_TX_MCU'), ('2', 1.5, 0, 'PYRO1_GATE_N')], at=(30, 60))
        self.assertFalse(any('U1 joins' in i for i in gate.s6(self.ctx())[0]))

    # --- S-7 J122 -------------------------------------------------------------------------------------------------
    def servo_header(self):
        pads = []
        for i in range(4):
            pads += [(str(3 * i + 1), 2.54 * i, 0, 'SERVO1_OUT' if i == 0 else None), (str(3 * i + 2), 2.54 * i, 2.54, None),
                     (str(3 * i + 3), 2.54 * i, 5.08, 'GND')]
        for n in ('SERVO2_OUT', 'SERVO3_OUT', 'SERVO4_OUT'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, n))
        f = self.part('J122', pads, at=(15, 80), tht=True, size=1.7)
        for i in (2, 3, 4):
            f.FindPadByNumber(str(3 * i - 2)).SetNet(self.board.FindNet(f'SERVO{i}_OUT'))
        return f

    def test_s7_servo_plus_row(self):
        f = self.servo_header()
        self.assertEqual(gate.s7(self.ctx())[0], [])
        f.FindPadByNumber('2').SetNet(self.board.FindNet('RAW_ACT'))
        self.assertTrue(any('J122.2 (servo + row) carries RAW_ACT' in i for i in gate.s7(self.ctx())[0]))
        f.FindPadByNumber('2').SetNet(self.board.FindNet(''))
        self.track((15, 82.54), (15, 86), 'BAT_IN', pcbnew.B_Cu)
        self.assertTrue(any('touches J122.2' in i for i in gate.s7(self.ctx())[0]))

    def test_s7_ground_row(self):
        f = self.servo_header()
        f.FindPadByNumber('6').SetNet(self.board.FindNet('BAT_IN'))
        self.assertTrue(any('J122.6 (ground row)' in i for i in gate.s7(self.ctx())[0]))

    # --- M-1 outline ----------------------------------------------------------------------------------------------
    def test_m1_outline(self):
        issues, ev = gate.m1(self.ctx())
        self.assertEqual((issues, ev['length_mm']), ([], 90.0))
        for w, h, word in ((47, 90, 'width'), (46, 121, 'length')):
            with self.subTest(w=w, h=h):
                board = self.board
                for d in list(board.GetDrawings()):
                    if d.GetLayer() == pcbnew.Edge_Cuts:
                        board.Remove(d)
                self.outline(w, h)
                self.assertTrue(any(word in i for i in gate.m1(self.ctx())[0]))

    def test_entry_direction_from_footprint_description(self):
        f = self.j124
        f.SetLibDescription('DORABO DB125-3.5-2P; wire entry +y')
        f.SetOrientationDegrees(-90)
        self.assertEqual(gate.entry_dir(f), '-x')
        f.SetOrientationDegrees(90)
        self.assertEqual(gate.entry_dir(f), '+x')
        f.SetLibDescription('DB128 (no entry note)')
        f.SetOrientationDegrees(0)
        self.assertEqual(gate.entry_dir(f), '-y')

    def test_route_profile_r10_critical_nets(self):
        import route_check as rc
        self.addCleanup(rc.set_profile, 'r8')
        rc.set_profile('r10')
        self.assertEqual((rc.ALLOWLIST, rc.LEFTOVERS, rc.ROUTE_FIGURES), ([], [], {}))
        expect = {'PYRO1_GATE': 'pyro', 'PYRO1_BUS': 'pyro', 'ARM1_SENSE_MCU': 'pyro', 'RAW_ACT_SENSE': 'pyro',
                  'RAW_ACT_SENSE_MCU': 'pyro', 'HSE_IN': 'crystal', 'USB_DP': 'usb', 'USB_DM': 'usb',
                  'QSPI_CLK': 'spi', 'SPI1_SCK': 'spi', 'IMU_CS': 'spi', 'GPS_TX_MCU': 'uart', 'RADIO_RX_MCU': 'uart',
                  'GND': 'power', '3V3': 'power', 'RAW_ACT': 'power', 'PORT_5V3': 'power', 'GPS_4V8': 'power',
                  'RADIO_4V8': 'power', 'CAM_5V': 'power', 'GPS_IO_3V3': 'power', 'SERVO1_OUT': 'actuator'}
        for net, cls in expect.items():
            self.assertEqual(rc.net_class(net), cls, net)
        for net in expect:
            if expect[net] not in ('power', 'actuator'):
                self.assertIn(rc.net_class(net), rc.SIGNAL_CRITICAL, net)
        for net in ('GNSS_RF_ANT', 'RADIO_RF', 'RADIO_SCK', 'GPS_PWR_EN', 'CAM_MCU_TX', 'GPS_TX_WIRE', 'NRST'):
            self.assertNotIn(rc.net_class(net), rc.SIGNAL_CRITICAL, net)
        rc.set_profile('r9')                                  # r9 unchanged: RF classes still critical
        self.assertEqual((rc.net_class('GNSS_RF_ANT'), rc.net_class('RADIO_SCK'), rc.net_class('GPS_TX_MCU')),
                         ('rf', 'spi', 'other'))

    def test_rule_list_and_stages(self):
        ids = [rid for rid, _, _ in gate.RULES]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({'S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7'} <= gate.STAGES['functional'])
        self.assertTrue(gate.STAGES['functional'] < gate.STAGES['placement'] < gate.STAGES['full'])
        for gone in ('P-0', 'P-1', 'P-3', 'P-4', 'P-5', 'P-6', 'P-7', 'K-power-pyro') + tuple(f'R-{i}' for i in range(1, 14)):
            self.assertNotIn(gone, ids)


# ======================================================================================================================
# Seeded faults on a real R10 board (R10_BOARD, else the repository board when its revision is M3-ASSY-R10). The
# project is copied to a temporary folder; nothing is written beside the source. A WIP board may fail rules already,
# so each seed must add a finding the unseeded board does not have.
# ======================================================================================================================
def r10_board():
    import os
    path = Path(os.environ.get('R10_BOARD') or gate.ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    if not path.is_file() or pcbnew is None:
        return None
    return path if 'M3-ASSY-R10' in path.read_text()[:20000] else None


_REAL = {}


def real_project():
    """A temporary copy of the R10 project (board, project, rules, every schematic sheet, kilib linked)."""
    import shutil
    import tempfile
    if 'dir' not in _REAL:
        src = r10_board()
        d = Path(tempfile.mkdtemp(prefix='r10_test_'))
        for f in src.parent.iterdir():
            if f.suffix in ('.kicad_pro', '.kicad_dru', '.kicad_sch') or f.name in ('fp-lib-table', 'sym-lib-table'):
                shutil.copyfile(f, d / f.name)
        shutil.copyfile(src, d / 'm3.kicad_pcb')
        if src.with_suffix('.kicad_pro').name != 'm3.kicad_pro':
            shutil.copyfile(src.with_suffix('.kicad_pro'), d / 'm3.kicad_pro')
        kilib = src.parent / 'kilib'
        (d / 'kilib').symlink_to(kilib if kilib.is_dir() else gate.ROOT / 'm3_design/assembly_review/kilib')
        _REAL['dir'] = d
    return _REAL['dir']


def tearDownModule():
    import shutil
    if 'dir' in _REAL:
        shutil.rmtree(_REAL['dir'], ignore_errors=True)


@unittest.skipUnless(pcbnew and r10_board(), 'an R10 board is required (set R10_BOARD)')
class RealBoardSeeds(unittest.TestCase):
    def P(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def load(self):
        return pcbnew.LoadBoard(str(real_project() / 'm3.kicad_pcb'))

    def run_rule(self, rid, board, path=None):
        folder = real_project()
        rep = gate.check_board(board, folder, path or folder / 'm3.kicad_pcb', only={rid})
        return set(rep['rules'][rid]['issues'])

    def seeded(self, rid, seed, word, path=None):
        """The seed adds a finding to rule `rid` that names `word`."""
        base = self.run_rule(rid, self.load())
        board = self.load()
        seed(board)
        new = self.run_rule(rid, board, path) - base
        self.assertTrue(any(word in i for i in new), f'{rid}: no new finding with {word!r}; new {sorted(new)[:5]}')

    def pad(self, board, ref, num):
        return board.FindFootprintByReference(ref).FindPadByNumber(num)

    def test_bridge_j124_with_a_track(self):
        def seed(b):
            p1, p2 = self.pad(b, 'J124', '1'), self.pad(b, 'J124', '2')
            t = pcbnew.PCB_TRACK(b); t.SetStart(p1.GetPosition()); t.SetEnd(p2.GetPosition())
            t.SetWidth(pcbnew.FromMM(0.25)); t.SetLayer(pcbnew.B_Cu); b.Add(t)
        self.seeded('S-1', seed, 'ARM break is bridged')

    def test_part_bypasses_j124(self):
        self.seeded('S-1', lambda b: self.pad(b, 'R132', '2').SetNet(b.FindNet('RAW_ACT')), 'without J124')

    def test_j124_pad_moved_closer(self):
        def seed(b):
            p1, p2 = self.pad(b, 'J124', '1'), self.pad(b, 'J124', '2')
            a, c = p1.GetPosition(), p2.GetPosition()
            p1.SetPosition(pcbnew.VECTOR2I(a.x + (c.x - a.x) // 10, a.y + (c.y - a.y) // 10))   # 0.35 mm closer
        self.seeded('S-5', seed, 'pad to pad')

    def test_required_fitted_seeds(self):
        for ref, flag in (('R134', pcbnew.FP_DNP), ('R127', pcbnew.FP_EXCLUDE_FROM_BOM),
                          ('C126', pcbnew.FP_EXCLUDE_FROM_POS_FILES), ('R128', pcbnew.FP_BOARD_ONLY)):
            with self.subTest(ref=ref):
                def seed(b, ref=ref, flag=flag):
                    f = b.FindFootprintByReference(ref); f.SetAttributes(f.GetAttributes() | flag)
                self.seeded('S-4', seed, ref)
        with self.subTest(ref='R180 removed'):
            self.seeded('S-4', lambda b: b.Remove(b.FindFootprintByReference('R180')), 'R180')

    def test_gps_net_next_to_pyro_bus(self):
        def seed(b):
            p = self.pad(b, 'J124', '1')
            c, r = p.GetPosition(), p.GetSize().x // 2
            t = pcbnew.PCB_TRACK(b); t.SetNet(b.FindNet('GPS_TX_MCU')); t.SetLayer(pcbnew.B_Cu)
            t.SetWidth(pcbnew.FromMM(0.2))
            y = c.y - r - pcbnew.FromMM(0.15)                    # 0.05 mm from the pad's copper
            t.SetStart(pcbnew.VECTOR2I(c.x - pcbnew.FromMM(1), y)); t.SetEnd(pcbnew.VECTOR2I(c.x + pcbnew.FromMM(1), y))
            b.Add(t)
        self.seeded('S-6', seed, 'GPS_TX_MCU')

    def test_j122_middle_pin_given_a_net(self):
        self.seeded('S-7', lambda b: self.pad(b, 'J122', '2').SetNet(b.FindNet('RAW_ACT')), 'J122.2')
        self.seeded('S-7', lambda b: self.pad(b, 'J122', '3').SetNet(b.FindNet('3V3')), 'J122.3')

    def test_raw_act_fed_from_raw_protected(self):
        self.seeded('S-2', lambda b: self.pad(b, 'R177', '2').SetNet(b.FindNet('RAW_PROTECTED')), 'RAW_PROTECTED')
        self.seeded('S-2', lambda b: self.pad(b, 'Q121', '5').SetNet(b.FindNet('BAT_IN')), 'Q121')

    def test_gate_pull_down_moved(self):
        self.seeded('S-3', lambda b: self.pad(b, 'R128', '2').SetNet(b.FindNet('3V3')), 'resistor from the gate')

    def test_imu_rotation_and_terminal_entry(self):
        self.seeded('M-7', lambda b: b.FindFootprintByReference('U4').SetOrientationDegrees(0), 'rotation')
        self.seeded('P-11', lambda b: b.FindFootprintByReference('J124').SetOrientationDegrees(90), 'enter from')

    def test_cli_end_to_end_on_a_saved_seed(self):
        """A seeded board saved in a temporary copy: the CLI prints a named line per rule and exits non-zero."""
        import shutil
        import subprocess
        import tempfile
        d = Path(tempfile.mkdtemp(prefix='r10_cli_'))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        for f in real_project().iterdir():
            if f.name != 'kilib':
                shutil.copyfile(f, d / f.name)
        (d / 'kilib').symlink_to((real_project() / 'kilib').resolve())
        b = pcbnew.LoadBoard(str(d / 'm3.kicad_pcb'))
        f = b.FindFootprintByReference('R134')
        f.SetAttributes(f.GetAttributes() | pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM)
        pcbnew.SaveBoard(str(d / 'm3.kicad_pcb'), b)
        out = subprocess.run([sys.executable, '-I', str(Path(gate.__file__)), str(d / 'm3.kicad_pcb'),
                              '--stage', 'functional', '--report', str(d / 'r10.json')],
                             capture_output=True, text=True, timeout=300)
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        for rid in gate.STAGES['functional']:
            self.assertRegex(out.stdout, rf'(?m)^{re.escape(rid)}\s+(OK|FAIL)')
        self.assertRegex(out.stdout, r'(?m)^S-4\s+FAIL')
        self.assertIn('R134: required fitted part excluded', out.stdout)
        report = __import__('json').loads((d / 'r10.json').read_text())
        self.assertFalse(report['ok'])
        self.assertTrue(any('R134' in i and 'dnp' in i for i in report['rules']['S-4']['issues']))


if __name__ == '__main__':
    unittest.main()
