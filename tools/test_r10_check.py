"""Seeded R10 safety/profile regressions (tools/check_r10.py, route_check r10): synthetic boards for every new or
changed rule, and seeded faults on a temporary copy of a real R10 board (R10_BOARD, else the repository board when it
is M3-ASSY-R10). No git, no writes beside the source board, no headless DRC.
Run with KiCad's Python: python3 -I tools/test_r10_check.py  (R10_BOARD=path/to/m3.kicad_pcb for the real-board seeds)"""
import json
import math
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
try:
    import plate_model as plate
except ImportError:                                  # numpy missing (KiCad's Python): the plate tests skip
    plate = None


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
VALUES = {'R126': '220R', 'R127': '1k', 'R128': '10k', 'C126': '220nF 25V X7R', 'R120': '100k', 'C120': '2.2uF', 'R121': '10k'}


class SyntheticBase(unittest.TestCase):
    """Helpers for the synthetic boards (no tests of its own)."""
    NETS = ('RAW_ACT', 'PYRO1_BUS', 'PYRO1_IGN', 'BAT_IN', 'ACT_FET_S', 'ACT_GATE', 'ACT_DRV', 'PYRO1_GATE',
            'PYRO1_GATE_N', 'GND', 'GPS_TX_MCU', 'SERVO1_OUT', 'RAW_PROTECTED', '3V3', 'ARM1_SENSE', 'PYRO1_COLD',
            'PYRO1_CONT', 'ARM1_SENSE_MID')

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
        f.SetValue(VALUES.get(ref, ref))
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

    def via(self, x, y, net, d=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(self.board); v.SetPosition(self.P(x, y)); v.SetWidth(pcbnew.FromMM(d))
        v.SetDrill(pcbnew.FromMM(drill)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(self.board.FindNet(net))
        self.board.Add(v)
        return v

    def arc(self, a, mid, b, net, layer=None, width=0.2):
        t = pcbnew.PCB_ARC(self.board)
        t.SetStart(self.P(*a)); t.SetMid(self.P(*mid)); t.SetEnd(self.P(*b)); t.SetWidth(pcbnew.FromMM(width))
        t.SetLayer(pcbnew.F_Cu if layer is None else layer); t.SetNet(self.board.FindNet(net)); self.board.Add(t)
        return t

    def ctx(self):
        return gate.make_ctx(self.board)

    def load_switch(self):
        for ref, drain, y in (('Q120', 'BAT_IN', 40), ('Q121', 'RAW_ACT', 50)):
            self.part(ref, [('1', 0, 0, 'ACT_FET_S'), ('2', 1, 0, 'ACT_FET_S'), ('3', 2, 0, 'ACT_FET_S'),
                            ('4', 3, 0, 'ACT_GATE')] + [(str(k), k - 5, 3, drain) for k in range(5, 10)], at=(20, y))


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class Synthetic(SyntheticBase):
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
        self.part('R133', [('1', 0, 0, 'ARM1_SENSE'), ('2', 1.5, 0, 'GND')], at=(30, 30))   # a named GND tie
        self.part('C128', [('1', 0, 0, 'PYRO1_OUT'), ('2', 1.5, 0, 'GND')], at=(30, 35))
        self.assertEqual(gate.s1(self.ctx())[0], [])
        self.load_switch()
        self.assertEqual(gate.s2(self.ctx())[0], [])

    def test_s1_s2_unnamed_supply_ties(self):
        """R4-SAF-02 / R4-GATE-03: a part with pads on the armed / RAW_ACT side and on a supply or rail is flagged
        unless it is a named tie, whatever its net count and whichever rail."""
        self.load_switch()
        self.part('D120', [('1', 0, 0, '3V3'), ('2', 1.5, 0, 'PYRO1_COLD')], at=(30, 25))     # named tie
        self.assertEqual(gate.s1(self.ctx())[0], [])
        self.assertEqual(gate.s2(self.ctx())[0], [])
        for ref, a, sup, rule in (('R990', 'RAW_ACT', 'GND', 'S-1'), ('R991', 'RAW_ACT', '3V3', 'S-1'),
                                  ('R992', '3V3', 'PYRO1_BUS', 'S-1'), ('R989', 'PYRO1_CONT', 'BAT_IN', 'S-2'),
                                  ('R988', 'PYRO1_COLD', 'GND', 'S-2')):
            with self.subTest(ref=ref):
                f = self.part(ref, [('1', 0, 0, a), ('2', 1.5, 0, sup)], at=(30, 30))
                run = gate.s1 if rule == 'S-1' else gate.s2
                self.assertTrue(any(f'{ref} has pads on' in i for i in run(self.ctx())[0]), run(self.ctx())[0])
                self.board.Remove(f)

    def test_s1_s2_chain_through_3v3_and_big_part(self):
        self.load_switch()
        self.part('R991', [('1', 0, 0, 'RAW_ACT'), ('2', 1.5, 0, '3V3')], at=(30, 30))
        self.part('R992', [('1', 0, 0, '3V3'), ('2', 1.5, 0, 'PYRO1_BUS')], at=(30, 35))
        self.assertEqual(len([i for i in gate.s1(self.ctx())[0] if 'has pads on' in i]), 2)
        # a six-net part (past MAX_PART_NETS) with one pad on RAW_ACT and one on BAT_IN
        self.part('U9', [('1', 0, 0, 'RAW_ACT'), ('2', 1, 0, 'BAT_IN'), ('3', 2, 0, 'GND'), ('4', 3, 0, 'ACT_DRV'),
                         ('5', 4, 0, 'ACT_GATE'), ('6', 5, 0, 'SERVO1_OUT')], at=(35, 60))
        self.assertTrue(any('U9 has pads on' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_test_pad_on_armed_copper(self):
        self.part('TP9', [('1', 0, 0, 'PYRO1_BUS')], at=(30, 30))
        self.assertTrue(any('test pad TP9' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_any_part_on_armed_copper(self):
        """R6-GATE-07 / R6-SAF-01: any part but the named armed-side ones, whatever its reference."""
        self.part('PT121', [('1', 0, 0, 'PYRO1_BUS')], at=(30, 30))
        self.assertTrue(any('PT121' in i and 'named armed-side' in i for i in gate.s1(self.ctx())[0]))
        self.board.Remove(self.board.FindFootprintByReference('PT121'))
        self.part('U77', [('1', 0, 0, 'PYRO1_IGN'), ('2', 1, 0, 'GND')], at=(30, 35))
        self.assertTrue(any('U77' in i for i in gate.s1(self.ctx())[0]))
        self.board.Remove(self.board.FindFootprintByReference('U77'))
        self.part('R132', [('1', 0, 0, 'PYRO1_BUS'), ('2', 1, 0, 'ARM1_SENSE_MID')], at=(30, 40))   # named: fine
        self.assertEqual(gate.s1(self.ctx())[0], [])
        self.board.FindFootprintByReference('R132').FindPadByNumber('1').SetNet(self.board.FindNet('PYRO1_IGN'))
        self.assertTrue(any('R132 is on armed net' in i for i in gate.s1(self.ctx())[0]))

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

    def test_s1_s2_multinet_part_bridge(self):
        """R5-SAF-01: a part with more than MAX_PART_NETS nets joining a RAW-side and an armed-side net fails S-1 and S-2."""
        self.load_switch()
        for n in ('RAW_ACT_SENSE_MCU', 'ARM1_SENSE_MCU', 'RAW_ACT_SENSE'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, n))
        for raw, armed in (('RAW_ACT_SENSE_MCU', 'ARM1_SENSE_MCU'), ('RAW_ACT_SENSE', 'ARM1_SENSE')):
            with self.subTest(raw=raw):
                u = self.part('U12', [('1', 0, 0, raw), ('2', 1, 0, armed), ('3', 2, 0, 'GND'), ('4', 3, 0, '3V3'),
                                      ('5', 4, 0, 'GPS_TX_MCU')], at=(30, 30))
                for fn, rid in ((gate.s1, 'S-1'), (gate.s2, 'S-2')):
                    self.assertTrue(any('bridges the ARM break' in i for i in fn(self.ctx())[0]), (rid, fn(self.ctx())[0]))
                self.board.Remove(u)
        u = self.part('U12', [('1', 0, 0, 'RAW_ACT_SENSE_MCU'), ('2', 1, 0, 'GND'), ('3', 2, 0, '3V3'),
                              ('4', 3, 0, 'GPS_TX_MCU'), ('5', 4, 0, 'ACT_DRV')], at=(30, 30))   # one side only: fine
        self.assertFalse(any('bridges' in i for i in gate.s1(self.ctx())[0] + gate.s2(self.ctx())[0]))

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
        self.part('R127', [('1', 0, 0, 'PYRO1_GATE_N'), ('2', 1.5, 0, 'GND')], at=(10, 76))
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

    def test_s3_round5_values_and_mcu_pull(self):
        """R5-SAF-02: series 100 ohm - 10 k, no unitless capacitor value, an MCU-side pull (R127) of 100 ohm - 100 k."""
        self.gates()
        self.assertEqual(gate.s3(self.ctx())[0], [])
        self.assertIsNone(gate.parse_value('220', 'C'))
        self.assertEqual(gate.parse_value('220F', 'C'), 220.0)
        self.assertEqual(gate.parse_value('220', 'R'), 220.0)
        for ref, value, word in (('R126', '0R', 'series resistor'), ('R126', '22k', 'series resistor'),
                                 ('C126', '220', 'capacitor'), ('R127', '47', 'MCU-side'), ('R127', '1M', 'MCU-side')):
            with self.subTest(ref=ref, value=value):
                f = self.board.FindFootprintByReference(ref); old = f.GetValue(); f.SetValue(value)
                self.assertTrue(any(word in i for i in gate.s3(self.ctx())[0]), gate.s3(self.ctx())[0])
                f.SetValue(old)
        p = self.board.FindFootprintByReference('R127').FindPadByNumber('2')
        p.SetNet(self.board.FindNet('3V3'))                                  # R127.2 moved to 3V3
        self.assertTrue(any('MCU-side' in i for i in gate.s3(self.ctx())[0]))
        p.SetNet(self.board.FindNet('GND'))
        self.board.Remove(self.board.FindFootprintByReference('R127'))
        self.assertTrue(any('MCU-side' in i for i in gate.s3(self.ctx())[0]))

    def test_s3_mcu_side_gate_node_only_u1_series_and_gnd_resistors(self):
        """R6-SAF-02: a pull-up (or anything else) on PYRO1_GATE_N fails."""
        self.gates()
        self.assertEqual(gate.s3(self.ctx())[0], [])
        f = self.part('R13', [('1', 0, 0, 'PYRO1_GATE_N'), ('2', 1, 0, '3V3')], at=(30, 30)); f.SetValue('100R')
        self.assertTrue(any('R13 is on the MCU-side gate node' in i for i in gate.s3(self.ctx())[0]))
        f.FindPadByNumber('2').SetNet(self.board.FindNet('GND'))                         # a second pull-down: allowed
        self.assertEqual(gate.s3(self.ctx())[0], [])
        c = self.part('C13', [('1', 0, 0, 'PYRO1_GATE_N'), ('2', 1, 0, 'GND')], at=(30, 35))
        self.assertTrue(any('C13 is on the MCU-side gate node' in i for i in gate.s3(self.ctx())[0]))

    def test_parse_value_infix_and_whole_token(self):
        """R6-GATE-06."""
        for text, want in (('4k7', 4700.0), ('1k5', 1500.0), ('2R2', 2.2), ('100k5', 100500.0), ('4.7k', 4700.0),
                           ('2R 1%', 2.0), ('1M', 1e6), ('10k 1%', 1e4)):
            self.assertAlmostEqual(gate.parse_value(text, 'R'), want, msg=text)
        for text in ('1e3', '1,5k', '4k7x', '', None, 'abc', '10kk'):
            self.assertIsNone(gate.parse_value(text, 'R'), text)
        self.assertAlmostEqual(gate.parse_value('4n7', 'C'), 4.7e-9)
        self.assertAlmostEqual(gate.parse_value('220nF 25V X7R', 'C'), 220e-9)
        self.assertIsNone(gate.parse_value('1e-6', 'C'))
        self.assertIsNone(gate.parse_value('220', 'C'))

    def test_s3_series_resistor_far_net_and_values(self):
        """R4-SAF-01: the series resistor's far net is a non-rail U1 net; the pull is 1 k - 100 k and the capacitor
        >= 100 nF."""
        self.gates()
        self.assertEqual(gate.s3(self.ctx())[0], [])
        for net in ('3V3', 'GND'):
            with self.subTest(far=net):
                p = self.board.FindFootprintByReference('R126').FindPadByNumber('1')
                old = p.GetNet(); p.SetNet(self.board.FindNet(net))
                self.assertTrue(any('series resistor' in i or 'U1 GPIO' in i for i in gate.s3(self.ctx())[0]))
                p.SetNet(old)
        for ref, value, word in (('R128', '1M', 'of 1 k - 100 k'), ('R128', '220R', 'of 1 k - 100 k'),
                                 ('C126', '10nF', 'capacitor >= 100 nF'), ('R120', '470k', 'of 1 k - 100 k'),
                                 ('C120', '47nF', 'capacitor >= 100 nF')):
            with self.subTest(ref=ref, value=value):
                f = self.board.FindFootprintByReference(ref); old = f.GetValue(); f.SetValue(value)
                self.assertTrue(any(word in i for i in gate.s3(self.ctx())[0]), gate.s3(self.ctx())[0])
                f.SetValue(old)
        self.assertEqual(gate.parse_value('4.7k', 'R'), 4700.0)
        self.assertEqual(gate.parse_value('2R 1% 2W pulse', 'R'), 2.0)
        self.assertAlmostEqual(gate.parse_value('220nF 25V X7R', 'C'), 220e-9)
        self.assertAlmostEqual(gate.parse_value('2.2uF', 'C'), 2.2e-6)

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
        # R3-RTE-01 / R3-SAF-03: every external-port signal and the pyro-bus load-switch drive are critical
        for net, cls in (('GPS_PWR_EN', 'portctl'), ('RADIO_FAULT_N', 'portctl'), ('CAM_UART_OE', 'portctl'),
                         ('CAM_MCU_TX', 'uart'), ('CAM_MCU_RX', 'uart'), ('GPS_TX_WIRE', 'uart'),
                         ('RADIO_RX_BUFFER', 'uart'), ('CAM_TX_WIRE', 'uart'), ('ACT_GATE', 'pyro'),
                         ('ACT_DRV', 'pyro'), ('ACT_EN', 'pyro')):
            self.assertEqual(rc.net_class(net), cls, net)
            self.assertIn(rc.net_class(net), rc.SIGNAL_CRITICAL, net)
        self.assertEqual(rc.net_class('ACT_FET_S'), 'power')
        for net in ('GNSS_RF_ANT', 'RADIO_RF', 'RADIO_SCK', 'NRST', 'CAM_5V_SENSE', 'GPS_ILIM', 'GPS_IO_3V3'):
            self.assertNotIn(rc.net_class(net), rc.SIGNAL_CRITICAL, net)
        rc.set_profile('r9')                                  # r9 unchanged: RF classes still critical
        self.assertEqual((rc.net_class('GNSS_RF_ANT'), rc.net_class('RADIO_SCK'), rc.net_class('GPS_TX_MCU')),
                         ('rf', 'spi', 'other'))
        self.assertEqual((rc.net_class('ACT_GATE'), rc.net_class('GPS_PWR_EN')), ('actuator', 'other'))

    def test_one_port_definition_for_both_gates(self):
        """R3-GATE-04: route_check r10's uart / portctl classes and K-reference's port nets are one definition."""
        import critical_reference as cr
        import route_check as rc
        self.addCleanup(rc.set_profile, 'r8')
        rc.set_profile('r10')
        for net in cr.R10_PORT_NETS:
            self.assertIn(rc.net_class(net), ('uart', 'portctl'), net)
        names = {f'{p}_{s}' for p in ('GPS', 'RADIO', 'CAM') for s in ('TX_MCU', 'RX_MCU', 'TX_WIRE', 'RX_WIRE',
                 'TX_BUFFER', 'RX_BUFFER', 'PWR_EN', 'FAULT_N', 'UART_OE', '4V8', '5V', 'ILIM', 'IO_3V3')}
        names |= {'CAM_MCU_TX', 'CAM_MCU_RX'}
        self.assertEqual({n for n in names if rc.net_class(n) in ('uart', 'portctl')},
                         {n for n in names if n in cr.R10_PORT_NETS})

    def test_rule_list_and_stages(self):
        ids = [rid for rid, _, _ in gate.RULES]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({'S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7'} <= gate.STAGES['functional'])
        self.assertTrue(gate.STAGES['functional'] < gate.STAGES['placement'] < gate.STAGES['full'])
        for gone in ('P-0', 'P-1', 'P-3', 'P-4', 'P-5', 'P-6', 'P-7', 'K-power-pyro') + tuple(f'R-{i}' for i in range(1, 14)):
            self.assertNotIn(gone, ids)


# ======================================================================================================================
# Round 4 gate fixes on small synthetic boards (R4-RTE-01/02, R4-GATE-04)
# ======================================================================================================================
@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R4Synthetic(SyntheticBase):
    def setUp(self):
        super().setUp()
        for net in ('PORT_5V3', 'SPI1_SCK'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
        import route_check as rc
        self.addCleanup(rc.set_profile, 'r8')

    def plane(self, net, x0, y0, x1, y1, layer=None):
        z = pcbnew.ZONE(self.board); z.SetLayer(pcbnew.In2_Cu if layer is None else layer)
        z.SetNet(self.board.FindNet(net))
        o = z.Outline(); o.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(z)
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        return z

    def test_signal_critical_nets_share_route_check_definition(self):
        import route_check as rc
        got = gate.signal_critical_nets(self.board)
        self.assertTrue({'PYRO1_CONT', 'ARM1_SENSE', 'ARM1_SENSE_MID', 'PYRO1_GATE', 'SPI1_SCK'} <= got)
        self.assertFalse({'GND', '3V3', 'BAT_IN', 'PORT_5V3'} & got)
        rc.set_profile('r10')
        self.assertTrue(all(rc.net_class(n) in rc.SIGNAL_CRITICAL for n in got))

    def test_k_reference_samples_the_pyro_class(self):
        import critical_reference as cr
        self.track((20, 30), (22.5, 30), 'PYRO1_CONT', pcbnew.B_Cu)
        gnd = pcbnew.SHAPE_POLY_SET(); gnd.NewOutline()
        for x, y in ((10, 10), (40, 10), (40, 40), (10, 40)):
            gnd.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        with patch.object(cr, 'fills', return_value={pcbnew.B_Cu: pcbnew.SHAPE_POLY_SET()}):
            issues, ev = gate.references(self.board)
        self.assertTrue(issues and 'PYRO1_CONT B.Cu' in ev['by_net_layer'], (issues, ev))
        with patch.object(cr, 'fills', return_value={pcbnew.B_Cu: gnd}):
            self.assertEqual(gate.references(self.board)[0], [])

    def test_k_region_one_plane_per_run(self):
        self.plane('GND', 10, 10, 30, 40)
        self.track((12, 30), (28, 30), 'PYRO1_CONT', pcbnew.B_Cu)
        self.assertEqual(gate.region_issues(self.board)[0], [])
        self.track((12, 32), (28, 32), 'GND', pcbnew.B_Cu)                       # not signal-critical: ignored
        self.assertEqual(gate.region_issues(self.board)[0], [])
        self.plane('3V3', 30.05, 10, 40, 40)                                    # a second plane, a 0.05 mm seam
        self.track((24, 20), (36, 20), 'ARM1_SENSE_MID', pcbnew.B_Cu)           # crosses GND -> 3V3
        issues = gate.region_issues(self.board)[0]
        self.assertTrue(any('ARM1_SENSE_MID' in i and "['3V3', 'GND']" in i for i in issues), issues)
        self.assertFalse(any('PYRO1_CONT' in i for i in issues))

    def test_k_region_no_in2_copper_and_own_via_antipad(self):
        self.plane('GND', 10, 10, 30, 40)
        self.track((25, 25), (34, 25), 'SPI1_SCK', pcbnew.B_Cu)                  # runs off the plane's end
        issues = gate.region_issues(self.board)[0]
        self.assertTrue(any('SPI1_SCK' in i and 'no In2 copper' in i for i in issues), issues)
        self.board.Remove(self.board.GetTracks()[0])
        # the same overhang inside the net's own via antipad (0.45 mm) is not a finding
        self.track((29.8, 25), (30.4, 25), 'SPI1_SCK', pcbnew.B_Cu)
        v = pcbnew.PCB_VIA(self.board); v.SetPosition(self.P(30.4, 25)); v.SetWidth(pcbnew.FromMM(0.6))
        v.SetDrill(pcbnew.FromMM(0.3)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(self.board.FindNet('SPI1_SCK'))
        self.board.Add(v)
        self.assertEqual(gate.region_issues(self.board)[0], [])
        t = self.track((29.8, 28), (30.9, 28), 'SPI1_SCK', pcbnew.B_Cu)          # no own via near: flagged
        self.assertTrue(gate.region_issues(self.board)[0])

    def test_k_region_margin_pad_and_chain(self):
        """R5-RTE-01 / -02 / -06: edges pushed 0.1 mm out, SMD pads sampled, connected chains one plane in total."""
        self.plane('GND', 10, 10, 30, 40)
        t = self.track((12, 39.95), (28, 39.95), 'PYRO1_CONT', pcbnew.B_Cu)       # edge 0.1 inside the plane edge
        self.assertTrue(gate.region_issues(self.board)[0])                       # edge + 0.1 margin is off the plane
        self.board.Remove(t)
        self.track((12, 39.5), (28, 39.5), 'PYRO1_CONT', pcbnew.B_Cu)
        self.assertEqual(gate.region_issues(self.board)[0], [])
        # a B.Cu SMD pad straddling the seam of two planes
        self.plane('3V3', 30.05, 10, 45, 40)
        f = self.part('R991', [('1', 0, 0, 'PYRO1_CONT')], at=(30.025, 20))
        pad = f.FindPadByNumber('1'); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.B_Cu); pad.SetLayerSet(ls)
        issues = gate.region_issues(self.board)[0]
        self.assertTrue(any('pad R991.1' in i for i in issues), issues)
        f.SetPosition(self.P(20, 20)); pad.SetPosition(self.P(20, 20))            # wholly on GND: fine
        self.assertFalse(any('R991' in i for i in gate.region_issues(self.board)[0]))

    def test_k_region_chain_crossing(self):
        self.plane('GND', 10, 10, 24.85, 40)
        self.plane('3V3', 25.15, 10, 40, 40)
        a = self.track((12, 30), (25, 30), 'SPI1_SCK', pcbnew.B_Cu)              # each half over one plane ...
        b = self.track((25, 30), (38, 30), 'SPI1_SCK', pcbnew.B_Cu)
        v = pcbnew.PCB_VIA(self.board); v.SetPosition(self.P(25, 30)); v.SetWidth(pcbnew.FromMM(0.6))
        v.SetDrill(pcbnew.FromMM(0.3)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(self.board.FindNet('SPI1_SCK'))
        self.board.Add(v)
        issues = gate.region_issues(self.board)[0]
        self.assertEqual([i for i in issues if 'connected' not in i], [], issues)
        self.assertTrue(any('connected B.Cu chain' in i and "['3V3', 'GND']" in i for i in issues), issues)
        self.board.Remove(b)                                                     # one half alone: clean
        self.assertEqual(gate.region_issues(self.board)[0], [])

    def test_k_region_own_pad_void_needs_a_real_void(self):
        """R5-GATE-01: the own through-hole pad exemption holds only inside the pad's own clearance void."""
        self.plane('GND', 0, 10, 46, 40)
        pad = self.j124.FindPadByNumber('1')                                     # (5, 20), PYRO1_BUS (not critical net?)
        for n in ('SPI1_SCK',):
            pad.SetNet(self.board.FindNet(n))
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        self.track((5, 20.3), (5, 21.0), 'SPI1_SCK', pcbnew.B_Cu)               # inside the pad's own void: exempt
        self.assertEqual(gate.region_issues(self.board)[0], [])
        # a stub over a slot cut across the plane 0.4 - 0.8 mm from the pad centre: not a void of the pad
        slot = pcbnew.ZONE(self.board); slot.SetIsRuleArea(True); slot.SetDoNotAllowZoneFills(True)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.In2_Cu); slot.SetLayerSet(ls)
        o = slot.Outline(); o.NewOutline()
        for x, y in ((0, 20.4), (46, 20.4), (46, 20.8), (0, 20.8)):
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(slot)
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        issues = gate.region_issues(self.board)[0]
        self.assertTrue(any('no In2 copper' in i for i in issues), issues)

    def keepout(self, pts, layer=None):
        slot = pcbnew.ZONE(self.board); slot.SetIsRuleArea(True); slot.SetDoNotAllowZoneFills(True)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.In2_Cu if layer is None else layer); slot.SetLayerSet(ls)
        o = slot.Outline(); o.NewOutline()
        for x, y in pts:
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        self.board.Add(slot)
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        return slot

    def box(self, x0, y0, x1, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    def test_k_region_margin_isolated(self):
        """R6-GATE-02: a copper edge 0.05 mm inside the plane edge fails with REGION_MARGIN 0.1, passes with 0."""
        self.plane('GND', 10, 10, 30, 40)
        self.track((12, 39.85), (28, 39.85), 'PYRO1_CONT', pcbnew.B_Cu)               # copper edge at 39.95
        self.assertTrue(gate.region_issues(self.board)[0])
        with patch.object(gate, 'REGION_MARGIN', 0.0):
            self.assertEqual(gate.region_issues(self.board)[0], [])

    def test_k_region_arc_beside_plane_edge_and_arc_in_chain(self):
        """R6-GATE-03: an arc track is sampled with the margin, and an arc joins a chain by its ends."""
        self.plane('GND', 10, 10, 30, 40)
        self.arc((12, 38), (20, 39.85), (28, 38), 'SPI1_SCK', pcbnew.B_Cu)           # apex copper edge at 39.95
        self.assertTrue(gate.region_issues(self.board)[0])
        with patch.object(gate, 'REGION_MARGIN', 0.0):
            self.assertEqual(gate.region_issues(self.board)[0], [])
        self.board.Remove(self.board.GetTracks()[0])
        self.arc((12, 37), (20, 38.5), (28, 37), 'SPI1_SCK', pcbnew.B_Cu)            # well inside: clean
        self.assertEqual(gate.region_issues(self.board)[0], [])
        # a chain: a straight run over GND, an arc over 3V3, joined end to end at a seam covered by an own via
        for t in list(self.board.GetTracks()):
            self.board.Remove(t)
        self.plane('3V3', 25.15, 10, 45, 40)
        self.board.Remove(self.board.Zones()[0]); self.plane('GND', 10, 10, 24.85, 40)
        self.track((12, 30), (25, 30), 'SPI1_SCK', pcbnew.B_Cu)
        self.arc((25, 30), (30, 30.5), (35, 30), 'SPI1_SCK', pcbnew.B_Cu)
        self.via(25, 30, 'SPI1_SCK')
        issues = gate.region_issues(self.board)[0]
        self.assertTrue(any('connected B.Cu chain' in i for i in issues), issues)
        self.assertFalse([i for i in issues if 'connected' not in i], issues)

    def test_k_region_step_catches_a_narrow_plane_gap(self):
        """R6-GATE-04: REGION_STEP: a 0.03 mm gap between two same-net planes is seen at 0.02, missed at 1 mm."""
        self.plane('GND', 10, 10, 25.01, 40)
        self.plane('GND', 25.04, 10, 40, 40)
        self.track((12, 30), (38, 30), 'PYRO1_CONT', pcbnew.B_Cu)
        self.assertTrue(any('no In2 copper' in i for i in gate.region_issues(self.board)[0]))
        with patch.object(gate, 'REGION_STEP', 1.0):
            self.assertEqual(gate.region_issues(self.board)[0], [])

    def test_k_region_track_end_on_smd_pad_joins_a_pad_only_chain(self):
        """R6-GATE-04: a track over GND ending on an SMD pad over 3V3: each clean alone, one chain together."""
        for z in (self.plane('GND', 10, 10, 24.85, 40), self.plane('3V3', 25.15, 10, 45, 40)):
            z.SetLocalClearance(pcbnew.FromMM(0.15))
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        self.via(25.0, 30, 'SPI1_SCK')                                            # covers the seam
        f = self.part('R992', [('1', 0, 0, 'SPI1_SCK')], at=(25.5, 30))
        pad = f.FindPadByNumber('1'); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.B_Cu); pad.SetLayerSet(ls)
        t = self.track((12, 30), (24.0, 30), 'SPI1_SCK', pcbnew.B_Cu, width=0.1)
        self.assertEqual(gate.region_issues(self.board)[0], [])                   # apart
        t.SetEnd(self.P(25.25, 30))                                                # the end now lies on the pad
        issues = gate.region_issues(self.board)[0]
        self.assertEqual([i for i in issues if 'connected' not in i], [], issues)
        self.assertTrue(any('connected B.Cu chain' in i and 'pad R992.1' in i for i in issues), issues)

    def test_k_region_own_pad_void_disc_radius(self):
        """R6-GATE-04: a closed no-copper hole 3 mm from a through-hole pad is not that pad's void."""
        self.plane('GND', 0, 10, 46, 40)
        self.j124.FindPadByNumber('1').SetNet(self.board.FindNet('SPI1_SCK'))
        self.keepout(self.box(4.7, 22.7, 5.3, 23.3))                              # a closed hole, centre 3 mm from (5, 20)
        self.track((5, 22.9), (5, 23.1), 'SPI1_SCK', pcbnew.B_Cu)
        self.assertTrue(any('no In2 copper' in i for i in gate.region_issues(self.board)[0]))

    def test_own_pad_void_exit_slot_of_0_03(self):
        """R6-GATE-05: a 0.03 mm slot from the void to outside the pad disc defeats the exemption."""
        def poly(*pts):
            ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
            for x, y in pts:
                ps.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
            return ps
        def fill(slot_width):
            ps = poly(*self.box(0, 10, 46, 40))
            ps.BooleanSubtract(poly(*[(5 + 0.9 * math.cos(k * math.pi / 16), 20 + 0.9 * math.sin(k * math.pi / 16))
                                      for k in range(32)]))
            if slot_width:
                ps.BooleanSubtract(poly(*self.box(0, 20 - slot_width / 2, 5, 20 + slot_width / 2)))
            return {'GND': ps}
        self.j124.FindPadByNumber('1').SetNet(self.board.FindNet('SPI1_SCK'))
        self.assertTrue(gate.OwnPadVoids(self.board, fill(0)).exempt('SPI1_SCK', 5, 20.3))
        for width in (0.03, 0.02):
            with self.subTest(width=width):
                self.assertFalse(gate.OwnPadVoids(self.board, fill(width)).exempt('SPI1_SCK', 5, 20.3))

    def test_k_region_foreign_via_hole_geometry(self):
        """R6-RTE-02 / R6-GATE-01: a no-copper sample is exempt only inside a via clearance hole of the fill."""
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'FOREIGN'))
        z = self.plane('GND', 0, 10, 46, 40)
        z.SetLocalClearance(pcbnew.FromMM(0.15))                                   # hole radius 0.3 + 0.15
        self.via(20, 25, 'FOREIGN')
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        self.track((19.7, 24.4), (19.7, 25.6), 'SPI1_SCK', pcbnew.B_Cu)            # centre line 0.3 from the via
        issues = gate.region_issues(self.board)[0]
        self.assertFalse([i for i in issues if 'no In2 copper' in i], issues)      # in the real hole: exempt
        # a pull-back: the same hole widened to a 1 mm square is no via hole
        self.keepout(self.box(19.5, 24.5, 20.5, 25.5))
        self.assertTrue(any('no In2 copper' in i for i in gate.region_issues(self.board)[0]))
        # a slot through the via, out of the plane: not a hole at all
        self.board.Remove(self.board.Zones()[1])
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        self.assertEqual([i for i in gate.region_issues(self.board)[0] if 'no In2 copper' in i], [])
        self.keepout(self.box(0, 24.8, 46, 25.2))
        self.assertTrue(any('no In2 copper' in i for i in gate.region_issues(self.board)[0]))

    def test_k_region_in_rule_list(self):
        self.assertIn('K-region', [rid for rid, _, _ in gate.RULES])
        self.assertIn('K-rules', [rid for rid, _, _ in gate.RULES])

    def test_npth_pad_with_copper_joins_connectivity(self):
        """R4-GATE-04: an NPTH pad that carries copper layers is a copper node."""
        f = self.part('H9', [('1', 0, 0, None)], at=(20, 40), tht=True)
        pad = f.FindPadByNumber('1')
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        nodes = gate.copper_nodes(self.board)
        self.assertTrue(any(n[4] is not None and n[4].GetParentFootprint().GetReference() == 'H9' for n in nodes))
        self.track((5, 20), (20, 40), None, pcbnew.B_Cu)                         # RAW_ACT pad -> NPTH copper
        self.track((8.5, 20), (20.2, 40), None, pcbnew.B_Cu)
        self.assertEqual(gate.copper_reach(nodes, 'RAW_ACT')[1] > 0, True)

    def test_m7_lever_arm_and_pad1(self):
        """R4-MEC-05: U4's lever arm and pad 1 offset are held, not only side and rotation."""
        u4 = self.part('U4', [('1', 1.21, -0.75, None), ('2', -1.21, 0.75, None)], at=(17, 45.9))
        u4.SetOrientationDegrees(180); u4.Flip(self.P(17, 45.9), True)
        u4.SetPosition(self.P(17, 45.9))
        ev = gate.m7(self.ctx())[1]
        self.assertAlmostEqual(ev['imu_lever_arm_signed_mm'], -6.0, places=2)
        u4.SetPosition(self.P(19, 45.9))
        self.assertTrue(any('lever' in i or 'roll axis' in i for i in gate.m7(self.ctx())[0]))

    def test_parse_and_tables_in_report(self):
        for n, p in (('r8', 'sources/r8_design/pin_table.tsv'), ('r10', 'sources/r10_design/pin_table.tsv'),
                     ('masses', 'sources/r10_design/masses.json')):
            self.assertTrue((gate.ROOT / 'm3_design/assembly_review' / p).is_file(), n)


# ======================================================================================================================
# R3 gate fixes on small synthetic boards (R3-GATE-01 .. R3-MEC-01)
# ======================================================================================================================
@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R3Synthetic(SyntheticBase):
    MORE = ('PYRO1_OUT', 'PYRO1_GATE', '3V3', 'USB_DP', 'SPI1_SCK', 'GPS_PWR_EN', 'CAM_UART_OE', 'BUZZ_DRV',
            'SERVO2_OUT')

    def setUp(self):
        super().setUp()
        for net in self.MORE:
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
        import route_check as rc
        self.addCleanup(rc.set_profile, 'r8')

    # --- R3-GATE-01 arcs ------------------------------------------------------------------------------------------
    def test_arc_segment_fails_r10_only(self):
        import route_check as rc
        self.part('X1', [('1', 0, 0, 'USB_DP')], at=(20, 30)); self.part('X2', [('1', 0, 0, 'USB_DP')], at=(24, 30))
        self.arc((20, 30), (22, 31), (24, 30), 'USB_DP')
        rc.set_profile('r10')
        found = [d for d in rc.scan(self.board) if d['cat'] == 'arc_segment']
        self.assertTrue(found and rc.gated(found[0]) and rc.evaluate(found, allowlist=[])[0])
        rc.set_profile('r9')
        self.assertFalse([d for d in rc.scan(self.board) if d['cat'] == 'arc_segment'])

    def test_reference_samples_follow_the_arc(self):
        import critical_reference as cr
        a = self.arc((0, 0), (1, 1), (2, 0), 'SPI1_SCK')
        pts = cr.arc_samples(a)
        self.assertTrue(max(p[3] for p in pts) > 1.0)              # the curve (and its +0.1 mm edge), not the chord
        radii = sorted({round(math.hypot(p[2] - 1, p[3]), 2) for p in pts})
        self.assertEqual(radii, [0.9, 1.0, 1.1])                  # centre (1, 0): centre line and both edges
        chord = pcbnew.SHAPE_POLY_SET(); chord.NewOutline()      # reference copper under the chord only
        for x, y in ((-1, -0.5), (3, -0.5), (3, 0.5), (-1, 0.5)):
            chord.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        with patch.object(cr, 'fills', return_value={pcbnew.F_Cu: chord}):
            self.assertTrue(gate.references(self.board)[0])
        whole = pcbnew.SHAPE_POLY_SET(); whole.NewOutline()
        for x, y in ((-1, -0.5), (3, -0.5), (3, 1.5), (-1, 1.5)):
            whole.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        with patch.object(cr, 'fills', return_value={pcbnew.F_Cu: whole}):
            self.assertEqual(gate.references(self.board)[0], [])

    # --- R3-RTE-01 port layer changes, R3-GATE-03 needless hops ---------------------------------------------------
    def hop(self, net):
        self.part('X1', [('1', 0, 0, net)], at=(20, 30)); self.part('X2', [('1', 0, 0, net)], at=(30, 30))
        self.track((20, 30), (23, 30), net, pcbnew.F_Cu); self.via(23, 30, net)
        self.track((23, 30), (27, 30), net, pcbnew.B_Cu); self.via(27, 30, net)
        self.track((27, 30), (30, 30), net, pcbnew.F_Cu)

    def test_port_control_layer_change_needs_gnd_via(self):
        import route_check as rc
        rc.set_profile('r10')
        self.hop('CAM_UART_OE')
        self.assertEqual(len([d for d in rc.scan(self.board) if d['cat'] == 'critical_via_no_gnd']), 2)
        self.via(23, 31.2, 'GND'); self.via(27, 31.2, 'GND')
        self.assertFalse([d for d in rc.scan(self.board) if d['cat'] == 'critical_via_no_gnd'])

    def test_needless_hop(self):
        import route_check as rc
        rc.set_profile('r10')
        self.hop('GPS_PWR_EN')
        self.via(23, 31.2, 'GND'); self.via(27, 31.2, 'GND')
        hops = [d for d in rc.scan(self.board) if d['cat'] == 'extra_vias' and d.get('hop')]
        self.assertEqual(len(hops), 1, hops)
        self.assertTrue(rc.gated(hops[0]))
        self.track((25, 28), (25, 32), 'SERVO2_OUT', pcbnew.F_Cu)      # other-net F.Cu copper under the B.Cu run
        self.assertFalse([d for d in rc.scan(self.board) if d['cat'] == 'extra_vias' and d.get('hop')])
        rc.set_profile('r9')
        self.board.Remove([t for t in self.board.GetTracks() if t.GetNetname() == 'SERVO2_OUT'][0])
        self.assertFalse([d for d in rc.scan(self.board) if d['cat'] == 'extra_vias' and d.get('hop')])

    # --- R3-MCU-01 loader pins ------------------------------------------------------------------------------------
    def test_loader_pins(self):
        u1 = self.part('U1', [('68', 0, 0, None), ('30', 1, 0, 'GND')], at=(25, 60))
        self.assertEqual(gate.loader_pins(self.board, {'PA9': '68'}, {})[0], [])
        u1.FindPadByNumber('68').SetNet(self.board.FindNet('BUZZ_DRV'))
        found = gate.loader_pins(self.board, {'PA9': '68'}, {})[0]
        self.assertTrue(any('PA9' in i and 'drives' in i for i in found), found)
        allowed = {'PA9': ('BUZZ_DRV', {}, 'test reason')}
        self.assertEqual(gate.loader_pins(self.board, {'PA9': '68'}, allowed)[0], [])
        self.part('R9', [('1', 0, 0, 'BUZZ_DRV'), ('2', 1, 0, 'GND')], at=(30, 60))
        self.assertTrue(any('members differ' in i for i in gate.loader_pins(self.board, {'PA9': '68'}, allowed)[0]))
        stale = gate.loader_pins(self.board, {'PA9': '68'}, dict(allowed, PA10=('X', None, 'r')))[0]
        self.assertTrue(any('stale' in i for i in stale))
        self.assertEqual(set(gate.LOADER_R10) - set(gate.LOADER_H74X), set())
        for port, (role, use) in gate.LOADER_H74X.items():
            if use in gate.LOADER_DRIVES and port in gate.LOADER_R10:
                self.assertTrue(len(gate.LOADER_R10[port][2]) > 40, port)

    # --- R3-SAF-01 barrels and J124's window ----------------------------------------------------------------------
    def test_s8_inner_copper_near_pyro_barrel(self):
        self.via(30, 30, 'PYRO1_BUS', drill=0.3)
        self.assertEqual(gate.s8(self.ctx())[0], [])
        t = self.track((30.75, 28), (30.75, 32), '3V3', pcbnew.In2_Cu)    # barrel wall 0.15 + 0.5 gap + 0.1 half
        found = gate.s8(self.ctx())[0]
        self.assertTrue(any('3V3 copper on In2.Cu is 0.500 mm' in i for i in found), found)
        t.SetNet(self.board.FindNet('GND'))
        self.assertEqual(gate.s8(self.ctx())[0], [])
        t.SetNet(self.board.FindNet('3V3')); t.SetStart(self.P(31.3, 28)); t.SetEnd(self.P(31.3, 32))   # 1.05 mm
        self.assertEqual(gate.s8(self.ctx())[0], [])
        self.part('X3', [('1', 0, 0, 'PYRO1_IGN')], at=(10, 50), tht=True)     # a plated pad hole counts too
        self.track((10.6, 48), (10.6, 52), 'SERVO1_OUT', pcbnew.In1_Cu)
        self.assertTrue(any('X3.1 hole' in i and 'In1.Cu' in i for i in gate.s8(self.ctx())[0]))

    def test_s8_plated_pad_and_raw_act_barrel(self):
        """R6-SAF-02: a foreign plated pad's inner copper counts; RAW_ACT's barrel is a barrel net."""
        self.assertIn('RAW_ACT', gate.BARREL_NETS)
        self.part('X5', [('1', 0, 0, 'PYRO1_BUS')], at=(10, 50), tht=True)
        self.assertEqual(gate.s8(self.ctx())[0], [])
        self.part('X6', [('1', 0, 0, 'SERVO1_OUT')], at=(11.9, 50), tht=True)      # pad edge 0.4 mm from the barrel wall
        self.assertTrue(any('SERVO1_OUT copper' in i and 'X5.1' in i for i in gate.s8(self.ctx())[0]))
        self.part('X7', [('1', 0, 0, 'RAW_ACT')], at=(30, 60), tht=True)
        self.track((30.9, 58), (30.9, 62), '3V3', pcbnew.In2_Cu)                    # 0.25 mm from the RAW_ACT hole wall
        self.assertTrue(any('X7.1 hole' in i for i in gate.s8(self.ctx())[0]))

    def test_s5_foreign_copper_between_j124_pads(self):
        self.assertEqual(gate.arm_window(self.board)[0], [])
        t = self.track((6.75, 19), (6.75, 21), 'RAW_PROTECTED', pcbnew.In2_Cu)
        self.assertTrue(any('RAW_PROTECTED' in i for i in gate.s5(self.ctx())[0]))
        t.SetNet(self.board.FindNet('GND'))
        self.assertEqual(gate.arm_window(self.board)[0], [])

    # --- R3-GATE-02 copper text, footprint zones, multi-net parts -------------------------------------------------
    def test_s1_copper_text_bridge(self):
        t = pcbnew.PCB_TEXT(self.board); t.SetText('I'); t.SetLayer(pcbnew.B_Cu); t.SetTextAngleDegrees(90)
        t.SetTextSize(self.P(4.5, 4.5)); t.SetTextThickness(pcbnew.FromMM(0.6)); t.SetPosition(self.P(6.75, 20))
        self.board.Add(t)
        self.assertTrue(any('bridged' in i and 'copper text' in i for i in gate.s1(self.ctx())[0]))
        self.board.Remove(t)
        f = self.part('X4', [], at=(6.75, 20))
        ft = pcbnew.PCB_TEXT(f); ft.SetText('I'); ft.SetLayer(pcbnew.F_Cu); ft.SetTextAngleDegrees(90)
        ft.SetTextSize(self.P(4.5, 4.5)); ft.SetTextThickness(pcbnew.FromMM(0.6)); ft.SetPosition(self.P(6.75, 20))
        f.Add(ft)
        self.assertTrue(any('bridged' in i and 'X4 copper text' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_multi_net_part(self):
        nets = ['RAW_ACT', 'GND', 'BAT_IN', 'ACT_GATE', 'GPS_TX_MCU', 'SERVO1_OUT']
        f = self.part('U99', [(str(k), k, 0, n) for k, n in enumerate(nets, 1)], at=(30, 70))
        # R4-SAF-02: a part with more than four nets and a pad on RAW_ACT beside a supply pad is flagged too
        self.assertTrue(any('U99 has pads on the armed / RAW_ACT side net RAW_ACT' in i for i in gate.s1(self.ctx())[0]))
        f.FindPadByNumber('6').SetNet(self.board.FindNet('PYRO1_IGN'))
        self.assertTrue(any('U99 has pads on RAW_ACT' in i for i in gate.s1(self.ctx())[0]))

    # --- R3-GATE-07 fire-loop width -------------------------------------------------------------------------------
    def test_s9_fire_path_and_sense_tap(self):
        self.part('R134', [('1', 0, 0, 'PYRO1_IGN'), ('2', 4, 0, 'PYRO1_BUS')], at=(20, 20))
        self.part('R132', [('1', 0, 0, 'PYRO1_BUS'), ('2', 1, 0, 'GND')], at=(14, 26))
        main = [self.track((5, 20), (10, 20), 'PYRO1_BUS', width=1.0), self.track((10, 20), (24, 20), 'PYRO1_BUS',
                                                                                    width=1.0)]
        self.track((10, 20), (14, 26), 'PYRO1_BUS', width=0.2)            # a sense tap at a T: pruned, not fire path
        segs, joined, _ = gate.fire_path(self.board, 'PYRO1_BUS', gate.FIRE_TERMINALS['PYRO1_BUS'])
        self.assertTrue(joined)
        self.assertEqual(sorted(round(pcbnew.ToMM(t.GetWidth()), 2) for t in segs), [1.0, 1.0])
        self.assertFalse([i for i in gate.s9(self.ctx())[0] if 'PYRO1_BUS fire-path' in i])
        main[1].SetWidth(pcbnew.FromMM(0.5))
        self.assertTrue([i for i in gate.s9(self.ctx())[0] if 'PYRO1_BUS fire-path track 0.500 mm' in i])

    # --- R3-MFG-01 silk over mask openings ------------------------------------------------------------------------
    def test_silk_over_mask_opening(self):
        f = self.part('X5', [('1', 0, 0, 'GND')], at=(30, 40))
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.F_Mask)
        f.FindPadByNumber('1').SetLayerSet(ls)
        found = gate.silk_mask_overlaps(self.board)                  # the default reference text sits on the pad
        self.assertEqual([x[0] for x in found], ['X5 field Reference'])
        f.Reference().SetVisible(False)
        self.assertEqual(gate.silk_mask_overlaps(self.board), [])
        s = pcbnew.PCB_SHAPE(f); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.F_SilkS)
        s.SetWidth(pcbnew.FromMM(0.5))
        s.SetArcGeometry(self.P(29.65, 40), self.P(29.41, 40.001), self.P(29.650025, 40.002245))   # near-zero length
        f.Add(s)
        found = gate.silk_mask_overlaps(self.board)
        self.assertTrue(found and found[0][1].startswith('X5.1') and found[0][2] > 0.1, found)
        s.SetArcGeometry(self.P(28.4, 40), self.P(28.16, 40.001), self.P(28.400025, 40.002245))
        self.assertEqual(gate.silk_mask_overlaps(self.board), [])


@unittest.skipUnless(plate, 'NumPy required (run under a python3 with numpy)')
class Plate(unittest.TestCase):
    """R3-MEC-01: every R10 mass key is placed (own row, or a mated allowance on its parent's box) or refused."""
    def setUp(self):
        self.spec = json.loads((Path(__file__).resolve().parents[1] /
                                'm3_design/assembly_review/sources/r10_design/masses.json').read_text())
        refs = ['J1', 'J121', 'J124', 'J122', 'C84', 'LS120', 'J3', 'J9', 'J123', 'J400', 'J410', 'J420',
                'J9 mated', 'J123 mated', 'J400 mated', 'J410 mated', 'J420 mated', 'J122 mated']
        self.fit = dict(profile='r10', outline=[0, 0, 46, 84], supports=[[4, 4], [42, 4], [4, 80], [42, 80], [42, 42]],
                        rows=[(1, ref, 'F', [20 + i, 40, 22 + i, 42, 0, 2]) for i, ref in enumerate(refs)])

    def test_mated_allowance_on_parent_and_unmatched_key_refused(self):
        _, masses, _ = plate.build(self.fit, 5, False, 'r10_mated', 'r10', self.spec)
        for ref in ('J1', 'J121', 'J124'):
            self.assertIn(f'{ref} mated', masses)
            self.assertEqual(masses[f'{ref} mated'][1:3], masses[ref][1:3])
        for key in ('J2', 'J5 mated', 'U77'):
            mutant = dict(self.spec, masses_g=dict(self.spec['masses_g'], **{key: 1.0}))
            with self.assertRaises(ValueError):
                plate.build(self.fit, 5, False, 'r10_mated', 'r10', mutant)


class FabScript(unittest.TestCase):
    def test_r10_fab_checks_required_fitted_on_the_exported_lists(self):
        """R3-GATE-05: r10_fab.sh runs check_r10 S-4 on the exported BOM and CPL, after export_fab, failing the run."""
        text = (gate.ROOT / 'm3_design/r10_fab.sh').read_text()
        self.assertIn('set -euo pipefail', text)
        export = text.index('tools/export_fab.py "$B"')
        s4 = text.index('tools/check_r10.py "$B" --only S-4 --bom "$D/fab/m3_bom_jlc.csv"')
        self.assertLess(export, s4)
        self.assertIn('--cpl "$D/fab/m3_cpl_jlc.csv"', text[s4:s4 + 200])


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


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class RealBoardSeeds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # R4-GATE-02: with pcbnew importable a missing or non-R10 board fails the gate's own tests, it never skips them
        if r10_board() is None:
            raise AssertionError('no M3-ASSY-R10 board found: set R10_BOARD or run in a checkout with the R10 board')

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

    # --- R3 gate seeds on the real board (R3-GATE-01 .. R3-MEC-02) -------------------------------------------------
    def route_new(self, seed, cat):
        """route_check r10 instances of `cat` the seed adds (by net / layer / place) to the real board's."""
        import route_check as rc
        self.addCleanup(rc.set_profile, 'r8')
        rc.set_profile('r10')
        key = lambda d: (d['cat'], d['net'], d['layer'], round(d['x'], 2), round(d['y'], 2))   # noqa: E731
        base = {key(d) for d in rc.scan(self.load()) if d['cat'] == cat}
        b = self.load()
        seed(b)
        return [d for d in rc.scan(b) if d['cat'] == cat and key(d) not in base]

    def longest(self, b, net, layer):
        ts = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net
              and t.GetLayer() == layer]
        return max(ts, key=lambda t: t.GetLength())

    def test_usb_dp_arc_fails_route_check(self):
        """R3-GATE-01: a USB_DP straight segment redrawn as an arc (same ends) is an arc_segment failure."""
        import route_check as rc

        def seed(b):
            t = self.longest(b, 'USB_DP', pcbnew.F_Cu)
            s, e = t.GetStart(), t.GetEnd()
            a = pcbnew.PCB_ARC(b)
            a.SetStart(s); a.SetEnd(e); a.SetWidth(t.GetWidth()); a.SetLayer(t.GetLayer()); a.SetNet(t.GetNet())
            dx, dy = e.x - s.x, e.y - s.y
            n = math.hypot(dx, dy)
            a.SetMid(pcbnew.VECTOR2I(int((s.x + e.x) / 2 - dy / n * 200000), int((s.y + e.y) / 2 + dx / n * 200000)))
            b.Remove(t); b.Add(a)
        new = self.route_new(seed, 'arc_segment')
        self.assertTrue(new and new[0]['net'] == 'USB_DP', new)
        self.assertTrue(all(rc.gated(d) for d in new))

    def test_spi1_sck_arc_across_split_fails_k_reference(self):
        """R3-GATE-01: an SPI1_SCK B.Cu arc whose chord is referenced but whose curve crosses a point with no In2
        reference plane: K-reference samples the curve, not the chord."""
        import critical_reference as cr
        b0 = self.load()
        refs = cr.references(True)
        refs[pcbnew.B_Cu] = (pcbnew.In2_Cu, gate.REF_PLANES_B)
        fill = cr.fills(b0, refs)[pcbnew.B_Cu]
        t = self.longest(b0, 'SPI1_SCK', pcbnew.B_Cu)
        s, e = t.GetStart(), t.GetEnd()
        cx, cy = pcbnew.ToMM((s.x + e.x) // 2), pcbnew.ToMM((s.y + e.y) // 2)
        holes = sorted(((x / 4, y / 4) for x in range(4, 180) for y in range(4, 356)
                        if not cr.inside(fill, x / 4, y / 4)), key=lambda p: math.dist(p, (cx, cy)))
        mid = holes[0]                                    # the nearest board point without In2 reference copper

        def seed(b):
            o = self.longest(b, 'SPI1_SCK', pcbnew.B_Cu)
            a = pcbnew.PCB_ARC(b)
            a.SetStart(o.GetStart()); a.SetEnd(o.GetEnd()); a.SetMid(self.P(*mid)); a.SetWidth(o.GetWidth())
            a.SetLayer(pcbnew.B_Cu); a.SetNet(o.GetNet()); b.Add(a)
        b = self.load()
        seed(b)
        arcs = [x for x in b.GetTracks() if x.GetClass() == 'PCB_ARC']
        self.assertTrue(any(not cr.inside(fill, p[2], p[3]) for p in cr.arc_samples(arcs[0])))
        base = gate.references(self.load())[1]['by_net_layer'].get('SPI1_SCK B.Cu', {}).get('samples', 0)
        issues, ev = gate.references(b)
        self.assertGreater(ev['by_net_layer'].get('SPI1_SCK B.Cu', {}).get('samples', 0), base)
        self.assertTrue(issues)

    def test_needless_hop_on_a_critical_net(self):
        """R3-GATE-03: the longest straight F.Cu run of a critical signal net redrawn F -> B -> F (the F.Cu path under
        the B.Cu run is the original track's own, so it crosses nothing)."""
        import route_check as rc
        self.addCleanup(rc.set_profile, 'r8')
        rc.set_profile('r10')
        b0 = self.load()
        pick = max((t for t in b0.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetLayer() == pcbnew.F_Cu
                    and rc.net_class(t.GetNetname()) in rc.SIGNAL_CRITICAL), key=lambda t: t.GetLength())
        net_name = pick.GetNetname()

        def seed(b):
            t = self.longest(b, net_name, pcbnew.F_Cu)
            s, e, w, net = t.GetStart(), t.GetEnd(), t.GetWidth(), t.GetNet()
            p1 = pcbnew.VECTOR2I(s.x + (e.x - s.x) // 4, s.y + (e.y - s.y) // 4)
            p2 = pcbnew.VECTOR2I(s.x + 3 * (e.x - s.x) // 4, s.y + 3 * (e.y - s.y) // 4)
            b.Remove(t)
            for a, c, lay in ((s, p1, pcbnew.F_Cu), (p1, p2, pcbnew.B_Cu), (p2, e, pcbnew.F_Cu)):
                x = pcbnew.PCB_TRACK(b); x.SetStart(a); x.SetEnd(c); x.SetWidth(w); x.SetLayer(lay); x.SetNet(net)
                b.Add(x)
            for p in (p1, p2):
                v = pcbnew.PCB_VIA(b); v.SetPosition(p); v.SetWidth(pcbnew.FromMM(0.45)); v.SetDrill(pcbnew.FromMM(0.2))
                v.SetNet(net); b.Add(v)
        new = self.route_new(seed, 'extra_vias')
        self.assertTrue(any(d['net'] == net_name and d.get('hop') for d in new), (net_name, new))

    def test_port_layer_change_without_gnd_via(self):
        """R3-RTE-01: a new GPS_PWR_EN layer change with no GND via within 1.5 mm fails critical_via_no_gnd."""
        def seed(b):
            t = self.longest(b, 'GPS_PWR_EN', pcbnew.B_Cu)
            s, e, w, net = t.GetStart(), t.GetEnd(), t.GetWidth(), t.GetNet()
            m = pcbnew.VECTOR2I((s.x + e.x) // 2, (s.y + e.y) // 2)
            b.Remove(t)
            for a, c, lay in ((s, m, pcbnew.B_Cu), (m, e, pcbnew.F_Cu)):
                x = pcbnew.PCB_TRACK(b); x.SetStart(a); x.SetEnd(c); x.SetWidth(w); x.SetLayer(lay); x.SetNet(net)
                b.Add(x)
            v = pcbnew.PCB_VIA(b); v.SetPosition(m); v.SetWidth(pcbnew.FromMM(0.45)); v.SetDrill(pcbnew.FromMM(0.2))
            v.SetNet(net); b.Add(v)
            for g in [x for x in b.GetTracks() if x.GetClass() == 'PCB_VIA' and x.GetNetname() == 'GND'
                      and (x.GetPosition() - m).EuclideanNorm() < pcbnew.FromMM(1.6)]:
                b.Remove(g)
        new = self.route_new(seed, 'critical_via_no_gnd')
        self.assertTrue(any(d['net'] == 'GPS_PWR_EN' for d in new), new)

    def test_loader_pin_seeds(self):
        """R3-MCU-01: a net on a loader-driven pin, a changed member value and an extra part on an allowed net."""
        self.seeded('K-loader', lambda b: self.pad(b, 'U1', '68').SetNet(b.FindNet('BUZZ_DRV')), 'PA9')
        self.seeded('K-loader', lambda b: self.pad(b, 'U1', '43').SetNet(b.FindNet('LED_RED')), 'PE13')
        self.seeded('K-loader', lambda b: b.FindFootprintByReference('R61').SetValue('100'), 'VLOGIC_SENSE')
        self.seeded('K-loader', lambda b: self.pad(b, 'R156', '1').SetNet(b.FindNet('CAM_PWR_EN')), 'CAM_PWR_EN')

    def test_barrel_and_arm_window_seeds(self):
        """R3-SAF-01: a 3V3 In1 track 0.5 mm from J124.1's barrel (S-8); a SERVO1_OUT In1 track across J124's
        inter-pad window (S-5)."""
        def near_barrel(b):
            p = self.pad(b, 'J124', '1')
            c, r = p.GetPosition(), p.GetDrillSize().x // 2
            x = c.x - r - pcbnew.FromMM(0.5) - pcbnew.FromMM(0.1)
            t = pcbnew.PCB_TRACK(b); t.SetNet(b.FindNet('3V3')); t.SetLayer(pcbnew.In1_Cu)
            t.SetWidth(pcbnew.FromMM(0.2)); t.SetStart(pcbnew.VECTOR2I(x, c.y - pcbnew.FromMM(1)))
            t.SetEnd(pcbnew.VECTOR2I(x, c.y + pcbnew.FromMM(1))); b.Add(t)
        self.seeded('S-8', near_barrel, 'In1.Cu')

        def across(b):
            p1, p2 = self.pad(b, 'J124', '1'), self.pad(b, 'J124', '2')
            t = pcbnew.PCB_TRACK(b); t.SetNet(b.FindNet('SERVO1_OUT')); t.SetLayer(pcbnew.In1_Cu)
            t.SetWidth(pcbnew.FromMM(0.2))
            m = pcbnew.VECTOR2I((p1.GetPosition().x + p2.GetPosition().x) // 2, (p1.GetPosition().y + p2.GetPosition().y) // 2)
            t.SetStart(m - pcbnew.VECTOR2I(pcbnew.FromMM(1.5), 0)); t.SetEnd(m + pcbnew.VECTOR2I(pcbnew.FromMM(1.5), 0))
            b.Add(t)
        self.seeded('S-5', across, 'SERVO1_OUT')

    def test_copper_text_and_multi_net_part_bridge(self):
        """R3-GATE-02: copper text joining J124's pads; U1 (> 4 nets) on both RAW_ACT and PYRO1_IGN."""
        def text(b):
            p1, p2 = self.pad(b, 'J124', '1'), self.pad(b, 'J124', '2')
            a, c = p1.GetPosition(), p2.GetPosition()
            t = pcbnew.PCB_TEXT(b); t.SetText('I'); t.SetLayer(pcbnew.B_Cu)
            span = (c - a).EuclideanNorm()
            t.SetTextSize(pcbnew.VECTOR2I(int(span * 1.3), int(span * 1.3))); t.SetTextThickness(pcbnew.FromMM(0.6))
            if abs(c.x - a.x) > abs(c.y - a.y):
                t.SetTextAngleDegrees(90)
            t.SetPosition(pcbnew.VECTOR2I((a.x + c.x) // 2, (a.y + c.y) // 2)); b.Add(t)
        self.seeded('S-1', text, 'ARM break is bridged')

        def u1(b):
            self.pad(b, 'U1', '68').SetNet(b.FindNet('RAW_ACT'))
            self.pad(b, 'U1', '69').SetNet(b.FindNet('PYRO1_IGN'))
        self.seeded('S-1', u1, 'U1 has pads on RAW_ACT')

    def test_fire_loop_width_floor(self):
        """R3-GATE-07: every fire-loop segment set to 0.2 mm; one ACT_FET_S leg narrowed to 0.3 mm."""
        def thin(b):
            for net, terms in gate.FIRE_TERMINALS.items():
                for t in gate.fire_path(b, net, terms)[0]:
                    t.SetWidth(pcbnew.FromMM(0.2))
        self.seeded('S-9', thin, 'fire-path track 0.200 mm')

        def leg(b):
            for t in gate.fire_path(b, 'ACT_FET_S', gate.FIRE_TERMINALS['ACT_FET_S'])[0]:
                if abs(pcbnew.ToMM(t.GetLength()) - 1.1) < 0.01:
                    t.SetWidth(pcbnew.FromMM(0.3))
                    break
        self.seeded('S-9', leg, 'ACT_FET_S fire-path track 0.300 mm')

    def test_silk_over_mask_opening(self):
        """R3-MFG-01: a near-zero-length silk arc (drawn as a nearly full circle, as Q121's pin-1 dot) and a silk line
        over a top pad's mask opening."""
        def dot(b):
            p = self.pad(b, 'R134', '1')
            side = pcbnew.B_SilkS if p.GetParentFootprint().IsFlipped() else pcbnew.F_SilkS
            c = p.GetPosition()
            r = min(p.GetSize().x, p.GetSize().y) // 2
            a = pcbnew.PCB_SHAPE(b); a.SetShape(pcbnew.SHAPE_T_ARC); a.SetLayer(side); a.SetWidth(pcbnew.FromMM(0.5))
            x0 = c.x - r - pcbnew.FromMM(0.1)
            a.SetArcGeometry(pcbnew.VECTOR2I(x0, c.y), pcbnew.VECTOR2I(x0 - pcbnew.FromMM(0.24), c.y + 1000),
                             pcbnew.VECTOR2I(x0 + 25, c.y + 2245))
            b.Add(a)
        self.seeded('K-legends', dot, 'R134.1')

    def test_round6_gate_seeds(self):
        """R6-GATE-07 / R6-SAF-01 / R6-SAF-02: a renamed test point on PYRO1_BUS (S-1); R913 100R from PYRO1_GATE_N to
        3V3 (S-3); an In2 RAW_PROTECTED track 0.425 mm from J124.2's hole (S-8); a PTH pad of another net near it."""
        def renamed_tp(b):
            tp = b.FindFootprintByReference('TP120')
            tp.SetReference('PT121'); tp.FindPadByNumber('1').SetNet(b.FindNet('PYRO1_BUS'))
        self.seeded('S-1', renamed_tp, 'PT121')

        def pull_up(b):
            f = pcbnew.Cast_to_FOOTPRINT(b.FindFootprintByReference('R127').Duplicate(False))
            f.SetReference('R913'); f.SetValue('100R'); b.Add(f)
            next(q for q in f.Pads() if q.GetNetname() == 'GND').SetNet(b.FindNet('3V3'))
        self.seeded('S-3', pull_up, 'R913')

        def in2_track(b):
            p = self.pad(b, 'J124', '2')
            c, r = p.GetPosition(), p.GetDrillSize().x // 2
            x = c.x + r + pcbnew.FromMM(0.425 + 0.1)
            t = pcbnew.PCB_TRACK(b); t.SetNet(b.FindNet('RAW_PROTECTED')); t.SetLayer(pcbnew.In2_Cu)
            t.SetWidth(pcbnew.FromMM(0.2)); t.SetStart(pcbnew.VECTOR2I(x, c.y - pcbnew.FromMM(1)))
            t.SetEnd(pcbnew.VECTOR2I(x, c.y + pcbnew.FromMM(1))); b.Add(t)
        self.seeded('S-8', in2_track, 'RAW_PROTECTED')

    def test_s3_series_resistor_moved_to_3v3(self):
        """R4-SAF-01: R126.1 moved from PYRO1_GATE_N to 3V3."""
        self.seeded('S-3', lambda b: self.pad(b, 'R126', '1').SetNet(b.FindNet('3V3')), 'Q124')

    def test_round5_gate_seeds(self):
        """R5-SAF-02: R126 0R, C126 '220' (unitless), R127.2 on 3V3. R5-SAF-01: U12 bridging the RAW and armed sense
        nets (MCU side, and the divider side)."""
        def value(ref, v):
            return lambda b: b.FindFootprintByReference(ref).SetValue(v)
        self.seeded('S-3', value('R126', '0R'), 'series resistor')
        self.seeded('S-3', value('C126', '220'), 'capacitor')
        self.seeded('S-3', lambda b: self.pad(b, 'R127', '2').SetNet(b.FindNet('3V3')), 'MCU-side')

        def bridge(raw, armed):
            def seed(b):
                u = b.FindFootprintByReference('U12')
                pads = [p for p in u.Pads() if p.GetNetname() not in ('GND', '3V3')]
                pads[0].SetNet(b.FindNet(raw)); pads[1].SetNet(b.FindNet(armed))
            return seed
        for raw, armed in (('RAW_ACT_SENSE_MCU', 'ARM1_SENSE_MCU'), ('RAW_ACT_SENSE', 'ARM1_SENSE')):
            for rid in ('S-1', 'S-2'):
                self.seeded(rid, bridge(raw, armed), 'bridges the ARM break')

    def test_supply_ties_seeds(self):
        """R4-SAF-02 / R4-GATE-03: RAW_ACT -> 3V3 -> PYRO1_BUS resistor chain (two parts), a U9 pad on RAW_ACT."""
        def chain(b):
            self.pad(b, 'R132', '1').SetNet(b.FindNet('3V3'))
            self.pad(b, 'R177', '2').SetNet(b.FindNet('3V3'))
        self.seeded('S-1', chain, 'not a named tie')
        self.seeded('S-1', lambda b: self.pad(b, 'U9', '1').SetNet(b.FindNet('RAW_ACT')), 'U9 has pads on')

    def test_imu_pad1_offset_and_lever_arm(self):
        """R4-MEC-05: U4 pad 1 displaced, and U4 moved 2 mm along x."""
        def pad1(b):
            p = self.pad(b, 'U4', '1'); q = p.GetPosition(); p.SetPosition(pcbnew.VECTOR2I(q.x + self.P(0.3, 0).x, q.y))
        self.seeded('M-7', pad1, 'pad 1')
        self.seeded('M-7', lambda b: b.FindFootprintByReference('U4').Move(self.P(2, 0)), 'roll axis')

    def test_k_rules_seeds(self):
        """R4-GATE-01: a PYRO1_BUS / 3V3 zero-clearance rule in m3.kicad_dru, min_clearance 0 and a net class
        clearance 0 in .kicad_pro, a severity set to ignore, a DRC exclusion."""
        folder = real_project()
        board = self.load()
        self.assertEqual(self.run_rule('K-rules', board), set())
        dru, pro = folder / 'm3.kicad_dru', folder / 'm3.kicad_pro'
        old_dru, old_pro = dru.read_text(), pro.read_text()

        def edit_pro(f):
            def go():
                d = json.loads(old_pro); f(d['board']['design_settings'], d); pro.write_text(json.dumps(d))
            return go
        seeds = {
            'rule': lambda: dru.write_text(old_dru + '\n(rule "x" (condition "A.NetName==\'PYRO1_BUS\' && '
                                           'B.NetName==\'3V3\'") (constraint clearance (min 0mm)))\n'),
            'min_clearance': edit_pro(lambda ds, d: ds['rules'].__setitem__('min_clearance', 0)),
            'netclass': edit_pro(lambda ds, d: d['net_settings']['classes'][0].__setitem__('clearance', 0.0)),
            'ignore': edit_pro(lambda ds, d: ds['rule_severities'].__setitem__('clearance', 'ignore')),
            'exclusion': edit_pro(lambda ds, d: ds.__setitem__('drc_exclusions', ['clearance|1|2|3'])),
            'track_width': edit_pro(lambda ds, d: ds['rules'].__setitem__('min_track_width', 0.05)),
        }
        try:
            for name, seed in seeds.items():
                with self.subTest(seed=name):
                    seed()
                    found = self.run_rule('K-rules', self.load(), folder / 'm3.kicad_pcb')
                    self.assertTrue(found, f'{name} seed not caught')
                    dru.write_text(old_dru); pro.write_text(old_pro)
        finally:
            dru.write_text(old_dru); pro.write_text(old_pro)

    def test_stale_zone_fill(self):
        """R4-GATE-05: a via added in a plane and the board saved without refilling leaves a stale fill."""
        import shutil
        import tempfile
        folder = real_project()
        self.assertEqual(self.run_rule('K-fill', self.load()), set())
        d = Path(tempfile.mkdtemp(prefix='r10_fill_'))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        b = self.load()
        v = pcbnew.PCB_VIA(b); v.SetPosition(self.P(23, 30)); v.SetWidth(pcbnew.FromMM(0.6))
        v.SetDrill(pcbnew.FromMM(0.3)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('PYRO1_BUS'))
        b.Add(v)
        pcbnew.SaveBoard(str(d / 'm3.kicad_pcb'), b)
        issues, ev = gate.fill_freshness(d / 'm3.kicad_pcb')
        self.assertTrue(issues, ev)

    def test_j1_wire_entry(self):
        """R3-MEC-02: J1 turned away from the west face."""
        self.seeded('P-11', lambda b: b.FindFootprintByReference('J1').SetOrientationDegrees(90), 'J1 wires enter')

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
