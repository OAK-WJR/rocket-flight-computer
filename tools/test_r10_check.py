"""Seeded R10 safety/profile regressions; no git, saved CAD changes or headless DRC."""
from pathlib import Path
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
        pins.update({'U1.42': 'CAM_PWR_EN', 'U1.41': 'CAM_FAULT_N'})
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


if __name__ == '__main__':
    unittest.main()
