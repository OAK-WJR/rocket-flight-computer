"""Seeded R10 safety/profile regressions (tools/check_r10.py, route_check r10): synthetic boards for every new or
changed rule, and seeded faults on a temporary copy of a real R10 board (R10_BOARD, else the repository board when it
is M3-ASSY-R10). No git or writes beside the source board; real DRC mutations use temporary projects.
Run with KiCad's Python: python3 -I tools/test_r10_check.py (R10_BOARD=path/to/m3.kicad_pcb for real-board seeds;
KICAD_CLI selects the same actual CLI/environment as tools/check.sh for the real DRC mutations)."""
import json
import math
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import Mock, patch
import copy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_r10 as gate
import r10_hotplug as hotplug
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

    def test_bom_quantities_and_quantity_free_cpl(self):
        self.assertEqual(gate.assembly_population('Designator,Qty\n"U1,U1",1\n', {'U1'}, require_qty=True), [])
        for qty in ('0', '-1', '1.5', 'bad', '', '2'):
            with self.subTest(qty=qty):
                self.assertTrue(gate.assembly_population(f'Designator,Qty\nU1,{qty}\n', {'U1'}, require_qty=True))
        self.assertEqual(gate.assembly_population('Designator\nU1\n', {'U1'}), [])
        self.assertIn('Qty column required for BOM',
                      gate.assembly_population('Designator\nU1\n', {'U1'}, require_qty=True))

    def test_assembly_designators_may_not_recur_on_another_row(self):
        for header, first, second in (('Designator,Qty,Manufacturer Part', 'R134,1,2R00', 'R134,1,20R0'),
                                      ('Designator,Qty', '"R127,R134",2', '"R134,R128",2'),
                                      ('Designator', 'R134', ' R134 ')):
            with self.subTest(header=header):
                text = f'{header}\n{first}\n{second}\n'
                self.assertIn('line 3: R134 already appears on line 2',
                              gate.assembly_population(text, {'R134'}, require_qty='Qty' in header))
        # Distinct-within-row Qty semantics and quantity-free CPL remain valid.
        self.assertEqual(gate.assembly_population('Designator,Qty\n"R134,R134",1\nR127,1\n',
                                                 {'R127', 'R134'}, require_qty=True), [])
        self.assertEqual(gate.assembly_population('Designator\nR134\nR127\n', {'R127', 'R134'}), [])

    def test_reviewed_fitted_population_includes_core_and_support(self):
        import r10_sch_check as sch
        parts, _ = sch.read_netlist(gate.ROOT / 'm3_design/assembly_review/schematic.net.xml')
        expected = {ref for ref, part in parts.items()
                    if not ({p.get('name') for p in part.findall('property')} &
                            {'dnp', 'exclude_from_bom', 'exclude_from_board'})}
        self.assertEqual(gate.REQUIRED_FITTED, expected)
        full = 'Designator\n' + '\n'.join(sorted(expected)) + '\n'
        self.assertEqual(gate.assembly_population(full), [])
        for ref in ('U1', 'U2', 'L1', 'U3', 'U4', 'U5', 'Y1', 'C13', 'C25', 'C6', 'R5'):
            with self.subTest(ref=ref):
                self.assertTrue(any(ref + ':' in i for i in gate.assembly_population(full.replace(ref + '\n', ''))))

    def circuit_pins(self):
        import json
        contract = json.loads((gate.ROOT / 'm3_design/assembly_review/sources/r10_design/circuit.json').read_text())
        pins, values, codes = {}, {}, {}
        for ref, part in contract['parts'].items():
            values[ref] = part['value']; codes[ref] = part['fields']['LCSC']
            pins.update({f'{ref}.{p}': n for p, n in part['nets'].items()})
        pins.update({f'U1.{p}': n for p, n in gate.mcu_pin_table().items() if n != 'NC'})
        return pins, values, codes

    def test_direct_uart_series_esd_and_obsolete_parts_seeds(self):
        pins, values, codes = self.circuit_pins()
        self.assertEqual(gate.uart_ports(pins, values, codes), [])
        for pin, net in (('R440.2', 'GPS_RX_WIRE'), ('R450.2', 'RADIO_RX_WIRE'), ('D410.2', '3V3'),
                         ('J410.1', '3V3'), ('C421.1', 'CAM_5V'), ('U1.64', 'GPS_TX_MCU'),
                         ('U411.1', 'GPS_RX_MCU'), ('R412.1', '3V3'),
                         # D-R19-14: the AUX port is held to the same contract, and J410 to its USART3 pins
                         ('R470.2', 'AUX_RX_WIRE'), ('D440.2', '3V3'), ('J440.1', '3V3'), ('C445.1', 'CAM_5V'),
                         ('U1.63', 'AUX_TX_WIRE'), ('U1.55', None), ('J440.4', 'AUX_TX_WIRE')):
            with self.subTest(pin=pin):
                mutant = dict(pins); mutant[pin] = net
                self.assertTrue(gate.uart_ports(mutant, values, codes))
        for ref in ('R440', 'R441', 'R450', 'R451', 'R470', 'R471'):
            mutant = dict(values); mutant[ref] = '0R'
            self.assertTrue(gate.uart_ports(pins, mutant, codes))

    def test_port_supply_enable_fault_and_limit_seeds(self):
        pins, values, codes = self.circuit_pins()
        self.assertEqual(gate.port_power(pins, values, codes), [])
        for pin, net in (('U400.3', '3V3'), ('U402.6', 'PORT_4V8'), ('U401.9', 'RAW_PROTECTED'),
                         ('R431.2', '3V3'), ('R432.2', 'PORT_4V8'), ('R430.2', 'CAM_FAULT_N')):
            with self.subTest(pin=pin):
                mutant = dict(pins); mutant[pin] = net
                self.assertTrue(gate.port_power(mutant, values, codes))
        mutant = dict(values); mutant['R430'] = '1k 1%'
        self.assertTrue(gate.port_power(pins, mutant, codes))
        mutant = dict(pins); mutant['J9.5'] = 'CAM_PWR_EN'
        self.assertTrue(gate.port_power(mutant, values, codes))

    def test_micro_sd_pinout_supply_pullups_and_retention_part_seeds(self):
        pins, values, codes = self.circuit_pins()
        self.assertEqual(gate.micro_sd(pins, values, codes), [])
        for pin, net in (('J430.1', None), ('J430.2', 'SD_SCK'), ('J430.4', 'PORT_4V8'),
                         ('J430.6', '3V3'), ('J430.9', None), ('U1.79', 'SD_MOSI'),
                         ('R460.2', 'GND'), ('R462.1', 'SD_SCK'), ('C460.2', '3V3'),
                         ('U1.82', 'SD_DAT1')):
            with self.subTest(pin=pin):
                mutant = dict(pins); mutant[pin] = net
                self.assertTrue(gate.micro_sd(mutant, values, codes))
        for ref in ('R460', 'R461', 'R462', 'R463', 'R464'):
            mutant = dict(values); mutant[ref] = '100R'
            self.assertTrue(gate.micro_sd(pins, mutant, codes))
        mutant = dict(codes); mutant['J430'] = 'push-push socket'
        self.assertTrue(gate.micro_sd(pins, values, mutant))
        for ref in ('J430', 'R460', 'R464', 'C460', 'C461'):
            self.assertIn(ref, gate.REQUIRED_FITTED)
            self.assertTrue(gate.population('(kicad_pcb)', {ref}))


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class TerminalLegends(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.BOARD()
        self.connector = pcbnew.FOOTPRINT(self.board); self.connector.SetReference('J1')
        self.board.Add(self.connector)
        for number, x in (('1', 10), ('2', 16)):
            pad = pcbnew.PAD(self.connector); pad.SetNumber(number)
            pad.SetPosition(self.P(x, 10)); self.connector.Add(pad)

    def P(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def label(self, value, x, textbox=False, footprint=False):
        owner = self.connector if footprint else self.board
        item = (pcbnew.PCB_TEXTBOX if textbox else pcbnew.PCB_TEXT)(owner)
        item.SetText(value); item.SetLayer(pcbnew.F_SilkS); item.SetTextSize(self.P(1, 1))
        item.SetTextThickness(pcbnew.FromMM(.15))
        if textbox:
            item.SetStart(self.P(x - 2.5, 6)); item.SetEnd(self.P(x + 2.5, 8)); item.SetBorderEnabled(False)
        else:
            item.SetPosition(self.P(x, 7))
        owner.Add(item)
        return item

    def test_correct_individual_labels_support_every_representation(self):
        for textbox, footprint in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(textbox=textbox, footprint=footprint):
                items = [self.label('1:BAT+', 10, textbox, footprint), self.label('2:GND', 16, textbox, footprint)]
                self.assertEqual(gate.terminal_legends(self.board)[0], [])
                for item in items:
                    (self.connector if footprint else self.board).Remove(item)

    def test_wrong_duplicate_missing_or_ambiguous_pin_labels_fail(self):
        first = self.label('1:BAT+', 10); self.label('2:GND', 16)
        self.assertEqual(gate.terminal_legends(self.board)[0], [])
        for word in ('1:BAT+', '1:BAT-', '1:E1+', 'J1 1:BAT-', 'J1 1:BAT+'):
            for footprint in (False, True):
                with self.subTest(word=word, footprint=footprint):
                    item = self.label(word, 10, textbox=True, footprint=footprint)
                    self.assertTrue(any('J1.1:' in i for i in gate.terminal_legends(self.board)[0]))
                    (self.connector if footprint else self.board).Remove(item)
        first.SetPosition(self.P(13, 7))
        self.assertTrue(gate.terminal_legends(self.board)[0])
        self.board.Remove(first)
        self.assertTrue(any('J1.1: 0 legends' in i for i in gate.terminal_legends(self.board)[0]))


class RuleSelection(unittest.TestCase):
    def test_invalid_explicit_scope_fails_before_context(self):
        for only in (set(), {''}, {'NO-SUCH-RULE'}, {'S-1', 'NO-SUCH-RULE'}, {'S-1', ''}):
            with self.subTest(only=only), patch.object(gate, 'make_ctx') as context:
                with self.assertRaisesRegex(ValueError, 'rule (selection|ids)'):
                    gate.check_board(None, only=only)
                context.assert_not_called()

    def test_valid_selection_and_default_stages_keep_their_scope(self):
        rules = [(rid, title, Mock(return_value=([], {}))) for rid, title, _ in gate.RULES]
        route = Mock(PROFILE='r9')
        with patch.object(gate, 'RULES', rules), patch.object(gate, 'make_ctx', return_value=object()), \
                patch.dict(sys.modules, {'route_check': route}):
            for stage in gate.STAGES:
                report = gate.check_board(None, stage=stage)
                self.assertEqual(set(report['rules']), gate.STAGES[stage])
                self.assertEqual(report['complete'], stage == 'full')
                self.assertTrue(report['ok'])
            report = gate.check_board(None, only={'S-9', 'K-legends'}, stage='functional')
            self.assertEqual(set(report['rules']), {'S-9', 'K-legends'})
            self.assertFalse(report['complete'])
            self.assertTrue(report['ok'])

    def test_cli_rejects_invalid_scope_before_loading_cad(self):
        import subprocess
        for only in ('NO-SUCH-RULE', 'S-1,NO-SUCH-RULE', '', ',', 'S-1,'):
            with self.subTest(only=only):
                result = subprocess.run([sys.executable, '-I', str(Path(gate.__file__)),
                    str(gate.ROOT / 'missing-scope-test.kicad_pcb'), '--only', only],
                    capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertRegex(result.stderr, r'rule (selection|ids)')
                self.assertNotIn('Traceback', result.stderr)
                self.assertNotIn('R10 CAD contract', result.stdout)


class SchematicContract(unittest.TestCase):
    def test_single_switch_contract_and_seeds(self):
        import xml.etree.ElementTree as ET
        import r10_sch_check as sch
        expected, pins = sch.expected()
        parts = {}
        for ref, part in expected.items():
            if isinstance(part, ET.Element):
                parts[ref] = copy.deepcopy(part)
                continue
            comp = ET.Element('comp', ref=ref)
            for key in ('value', 'footprint'):
                ET.SubElement(comp, key).text = part[key]
            ET.SubElement(comp, 'libsource', part=part['lib'].removeprefix('M3:'))
            fields = ET.SubElement(comp, 'fields')
            for key, value in part['fields'].items():
                ET.SubElement(fields, 'field', name=key).text = value
            parts[ref] = comp
        self.assertEqual(sch.contract(parts, pins), [])
        # A wrong source and schematic can agree; BOM grouping must still reject the C92 split.
        parts['C92'].find('footprint').text = 'rocket:C_0603_1608Metric'
        with patch.object(sch, 'expected', return_value=(parts, pins)):
            self.assertTrue(any('BOM contract: LCSC C19666' in i and 'C92' in i
                                for i in sch.contract(parts, pins)))
        parts['C92'].find('footprint').text = 'rocket:C0603'
        seeded = sch.seeds(parts, pins)
        self.assertTrue(all(seeded.values()), seeded)
        self.assertTrue({'obsolete ARM terminal restored', 'obsolete separate pyro bus',
                         'pyro feed directly from pack', 'load switch follows logic rail',
                         'load switch enable pull-down missing', 'C92 split assembly footprint',
                         'C120 split assembly footprint'} <= seeded.keys())

    def test_r27_port_terminal_pin_names(self):
        """D-R27-03 (R27-TRI-07): J410 / J420 / J440 use M3:PortTerminal, whose pin names are REQUIREMENTS F10's and the
        board legends' (1 4V8, 2 GND, 3 TXO, 4 RXI); J9 keeps M3:CameraTerminal. With the camera terminal's names back on
        the ports (round 27's netlist) the gate fails, and its four seeded name faults are each caught."""
        import json
        import r10_sch_check as sch
        sys.path.insert(0, str(gate.ROOT / 'm3_design'))
        import r10_parts
        names = sch.read_pin_names(gate.ROOT / 'm3_design/assembly_review/schematic.net.xml')
        self.assertEqual(sch.terminal_pin_issues(names), [])
        legends = dict(gate.TERMINAL_PINS_R10)
        for ref in ('J410', 'J420', 'J440'):
            self.assertEqual(dict(legends[ref]), sch.PORT_PIN_NAMES, ref)
        self.assertEqual(dict(r10_parts.PORT_TERMINAL_PINS), sch.PORT_PIN_NAMES)
        circuit = json.loads((gate.ROOT / 'm3_design/assembly_review/sources/r10_design/circuit.json').read_text())
        self.assertEqual({ref: circuit['parts'][ref]['lib'] for ref in ('J410', 'J420', 'J440')},
                         dict.fromkeys(('J410', 'J420', 'J440'), 'M3:PortTerminal'))
        self.assertEqual(circuit['replacements']['J9']['lib'], 'M3:CameraTerminal')
        old = dict(names)
        old.update({(ref, pin): name for ref in ('J410', 'J420', 'J440') for pin, name in sch.CAMERA_PIN_NAMES.items()})
        self.assertEqual(len(sch.terminal_pin_issues(old)), 3)
        seeded = sch.name_seeds(names)
        self.assertEqual(len(seeded), 4)
        self.assertTrue(all(seeded.values()), seeded)

    def test_assembly_groups_match_separate_owner_and_jlc_boms(self):
        import xml.etree.ElementTree as ET
        import r10_sch_check as sch
        def part(ref):
            p = ET.Element('comp', ref=ref)
            ET.SubElement(p, 'footprint').text = 'rocket:C0603'
            fields = ET.SubElement(p, 'fields')
            ET.SubElement(fields, 'field', name='LCSC').text = 'C19666'
            ET.SubElement(fields, 'field', name='Manufacturer Part').text = 'CL10A475KO8NNNC'
            return p
        parts = {ref: part(ref) for ref in ('C23', 'C28', 'C92')}
        self.assertEqual(sch.assembly_groups(parts), [])
        mpn = next(f for f in parts['C92'].findall('./fields/field') if f.get('name') == 'Manufacturer Part')
        mpn.text = 'different-capacitor'
        self.assertTrue(sch.assembly_groups(parts))
        mpn.text = 'CL10A475KO8NNNC'
        parts['C92'].find('footprint').text = 'rocket:C_0603_1608Metric'
        self.assertTrue(sch.assembly_groups(parts))
        ET.SubElement(parts['C92'], 'property', name='exclude_from_bom')
        self.assertEqual(sch.assembly_groups(parts), [])
        parts['C92'].remove(parts['C92'].find('property'))
        ET.SubElement(parts['C92'], 'property', name='dnp')
        self.assertEqual(sch.assembly_groups(parts), [])  # One member in the separate owner BOM.
        ET.SubElement(parts['C28'], 'property', name='dnp')
        self.assertTrue(sch.assembly_groups(parts))

    def test_binding_note_has_pad_policy_and_both_trace_locks(self):
        import r10_sch_check as sch
        note = sch.binding_note(gate.ROOT / 'm3_design/assembly_review')
        self.assertIn('not a separate ARM-link state', note['arming_policy']['limits'])
        obligations = '\n'.join(note['firmware_obligations'])
        for text in ('PC1 ACT_EN_MCU', 'GPIOC_LCKR', 'GPIOE_LCKR', 'accelerometer and barometer',
                     'in flight they are logged and annunciated and never veto a fire',
                     'at least 100ms', 'at least 1s', 'BEFORE PC1 enable', 'before powered-bus checks'):
            self.assertIn(text, obligations)
        cold = next(rule for rule in note['firmware_obligations'] if rule.startswith('D-SS-04 / AUD-3:'))
        self.assertIn('hold BOTH PC1 ACT_EN_MCU and PE4 low', cold)
        self.assertLess(cold.index('passive cold screening'),
                        cold.index('Only after a valid passive check may PC1 go high'))
        self.assertNotIn('PE3/PE5/PE6/PC1/PC4', obligations)
        self.assertNotIn('ARM link out', obligations)
        self.assertNotIn('ARM link in:', obligations)
        timing = note['fire_timing']
        watchdog = timing['watchdog']
        self.assertEqual((watchdog['prescaler_divisor'], watchdog['PR_register'], watchdog['RLR'],
                          watchdog['LSI_cycles']), (4, 0, 239, 960))
        self.assertAlmostEqual(watchdog['minimum_ms'], 28.5714285714)
        self.assertAlmostEqual(watchdog['maximum_ms'], 32.6530612245)
        self.assertEqual(timing['normal_physical_current_max_ms'], 20.)
        self.assertLess(watchdog['maximum_ms'] + timing['prefire_sync_max_ms'] + timing['reset_HiZ_max_ms']
                        + timing['actual_gate_current_tail_max_ms'], timing['fault_physical_current_max_ms'])
        self.assertEqual(timing['postfire_safety_pass_and_refeed_max_ms'], 5.)
        self.assertIn('No IWDG refresh from prefire', timing['refresh_contract'])
        self.assertIn('until physical firing current has ended (including tail)', timing['refresh_contract'])
        states = note['port_states']
        self.assertIn('GPS/radio/AUX ports have no powered-off isolation', states['off_external_uart_active'])
        self.assertIn('no self-powered GPS/radio with the board off', states['off_external_uart_active'])
        self.assertIn('SD card remains on main3V3', states['off_external_uart_active'])
        self.assertIn('Camera EN100k/OE10k pulldowns', states['reset_boot'])
        self.assertIn('no state sensor', states['port_device_backfeed'])
        self.assertNotIn('when the power switch opens', obligations)
        # R19-MCU-01 / -02 / -04 and D-R19-11: the port TX rule on U11's ST polarity, one DS12110 revision, VREFBUF
        # kept off, and the two IMU parts' differing high-g codes.
        self.assertIn('only while PA4 LOGIC_SOURCE_ST reads low', states['startup'])
        self.assertIn('ST low = IN2 = RAW_PROTECTED', states['startup'])
        self.assertIn('park PD8 / PB13 / PC6 in analog mode, no pull', states['shutdown_shedding'])
        # D-R19-14: the identical-port map and the AUX allowance are firmware obligations.
        self.assertTrue(any(r.startswith('Configurable port map (D-R19-14') and '100 mA at 4.8 V' in r
                            for r in note['firmware_obligations']))
        self.assertNotIn('GPS/radio are always powered', obligations)
        self.assertNotIn('Rev 11 Table', obligations.replace('read from Rev 11 Table 109 in round 14', ''))
        self.assertTrue(any(r.startswith('VREFBUF (R19-MCU-04)') for r in note['firmware_obligations']))
        self.assertTrue(any('use only 001 (+/-64 g) or 010 (+/-128 g)' in r for r in note['firmware_obligations']))
        self.assertIn('Rev 8', note['sources']['mcu_revision'])

    def test_r23_sheet_replay_catches_a_hand_edited_note(self):
        """D-R23-10 (R23-GATE-06): the schematic contract's replay (which check.sh now runs) fails a committed sheet
        whose note was hand-edited: the gate lens's d01 (the diagnostics note reverted to round 21's text) is named as a
        nonreproducible diagnostics.kicad_sch; the unedited copy has no such finding."""
        import shutil
        import tempfile
        import r10_sch_check as sch
        src = gate.ROOT / 'm3_design/assembly_review'

        def copy():
            d = Path(tempfile.mkdtemp(prefix='r10_replay_'))
            self.addCleanup(shutil.rmtree, d, ignore_errors=True)
            for f in src.iterdir():
                if f.suffix in ('.kicad_sch', '.kicad_pro', '.kicad_dru') or f.name in ('schematic.net.xml', 'fp-lib-table',
                                                                                        'sym-lib-table'):
                    shutil.copyfile(f, d / f.name)
            (d / 'kilib').symlink_to(src / 'kilib', target_is_directory=True)
            return d
        clean, edited = copy(), copy()
        diag = edited / 'diagnostics.kicad_sch'
        text = diag.read_text()
        new = "Nominal 5.456 V (PORT_5V3 via U402) reads 0.496 V; a failed U400 passes RAW_PROTECTED"
        self.assertIn(new, text)
        diag.write_text(text.replace(new, '5.25 V reads 0.477 V; a failed regulator passes RAW_PROTECTED'))
        import contextlib
        import io
        import warnings
        with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():   # keep check.sh's summary lines
            warnings.simplefilter('ignore', ResourceWarning)
            clean_issues, edited_issues = sch.check(clean)['issues'], sch.check(edited)['issues']
        self.assertNotIn('nonreproducible generated artifact: diagnostics.kicad_sch', clean_issues)
        self.assertIn('nonreproducible generated artifact: diagnostics.kicad_sch', edited_issues)

    def test_r23_binding_note_rules_and_pin_table(self):
        """D-R23-03 (R23-MCU-04 / DOCS_BINDING-03 / -08, POWER-04 and the root's rules 1-13): the binding note carries
        the 13 round 23 firmware rules in the root's wording, PB1 as TT_u, the LSM6DSV320X as the second-fallback
        alternate; pin_table names the R10 pull resistor where one exists (no 'as R7' on those rows) and gives PA5's
        reverse-blocking meaning."""
        import csv
        import r10_sch_check as sch
        note = sch.binding_note(gate.ROOT / 'm3_design/assembly_review')
        rules = [r for r in note['firmware_obligations'] if r.startswith('R23 firmware rule ')]
        self.assertEqual([int(r.split()[3].rstrip(',')) for r in rules], list(range(1, 14)))
        text = '\n'.join(note['firmware_obligations'])
        for words in ('LIFTOFF from the accelerometer AND a barometric altitude gain (LAUNCH_CORROBORATED)',
                      'wait at least 1 s, and verify that RAW_ACT has discharged and ACT_GATE is off',
                      "Q124's gate capacitor is C126, 220 nF, not C128", 'run a QSPI quad read-verify of a known pattern',
                      # D-R28-02 (R28-TRI-05): unpowered, both polarities, since the U1 / U3 input clamps conduct one
                      # way; the fight figures with the MCU driving IO2 high, in all but one modelled corner
                      'with the board unpowered (pack and USB disconnected), meter U3.3 (QSPI_IO2) to R127.1 (the PE4 '
                      'gate network) in resistance mode, both polarities: an intact board reads above 0.9 kΩ, or open, '
                      'both ways (red lead on R127.1: a diode drop plus about 0.91 kΩ through the U1 / U3 input clamps; '
                      'reversed: open or slowly rising); a continuity beep or under 100 Ω in either polarity is a '
                      "bridge: reject (0.91 kΩ is R127's 1 kΩ in parallel with R126 + R128, Calculation; the meter's "
                      'reading through the clamps is an Inference)',
                      'a steady IO2-against-PE4 fight with the MCU driving IO2 high puts 1.19–1.98 V on the gate and '
                      'fires the match after about 0.55 ms in all but one modelled corner',
                      'First article, before first power and coating: inspect U1 pins 1–5 for bridges',
                      # the root's round 28 siblings from ORDERING 8.3: rule 4's Q120 pass criterion, and the port
                      # supply's lead over 3V3 (44 ms was VLOGIC's full slew plus tSET, not a lower bound)
                      'must settle at |VGS| of at least 4.5 V (a Q120 gate cut off from R121 sits near 0 V)',
                      'during the dummy-load fire BAT_IN − RAW_ACT above 0.2 V fails the board',
                      'because PORT_4V8 can rise tens of ms before 3V3',
                      'so 3V3 regulates about 21–26 ms into the slew; Calculation / Inference',
                      'the powered BUS must read at least 0.96 × the pack voltage derived from VLOGIC_SENSE',
                      'PC1 may go high only while PA4 reads low', 'PC1 never re-enables in the same power session',
                      'PA5 low also means U9 is blocking reverse current (SLVSFC9C Table 7-3 p38)',
                      'The PA6 trip window is VLOGIC about 4.8–5.2 V (PA6 0.44–0.47 V)'.replace('The', 'the'),
                      'refuses the pad READY state below 7.4 V plus the measured PA6 divider error',
                      'BOOT_ADD0 = 0x0800, IWDG1_SW software start', 'U5 MS5611 on I2C1 PB8 / PB9 at 0x77 (PS high, CSB low)',
                      'within ±1.023 MHz of 1575.42 MHz', "Never use ST's ism6hg256x driver's 256 g enum",
                      'open R105 puts CAM_5V on a TT_u pin', 'the LSM6DSV320X is the second-fallback alternate (needs part fields'):
            self.assertIn(words, text)
        self.assertNotIn('TT_a pin', text)
        self.assertNotIn('consigned alternate', text)
        # D-R24-19 (R24-TRI-02 / -04): rules 4, 5 and 8 and the chatter worst cases after D-R24-02 / -08 / -11;
        # D-R25-01 / -02 (R25-TRI-01 / -02): the sliding-window chatter criterion and rule 8's hold-up over the trip window;
        # D-R26-03 (R26-TRI-02 / -03 / -04): the bound four-stall point 5.71 V (with the AUX allowance), the late-block
        # worst train in place of the sampled search, and rule 8's corner without the fire current counted twice
        for words in ('leaving Q120 off this way takes two opens', 'R91.1 and U1.28 each have a second via since D-R24-08',
                      "above U9's 4.80 V BAT_IN turn-off corner",
                      'a single J400 drop-out shorter than 10.3/20.1/26.0 ms worst case',
                      'about 8.1 ms (8.07 ms) at the fire budget four-stall BAT_IN of 5.71 V (5.713 V, parts_budget.json',
                      'and 6.3 ms at 5.5 V cannot trip U9',
                      'Repeated drop-outs add up (R25-TRI-01)',
                      'falls from 19.6 % at 0.1 ms drop-outs to 14.8 % at 4 ms and 4.5 % at 8 ms (5.71 V)',
                      '19.7 / 24.4 % is only the fast-chatter limit',
                      'total open time in every sliding 100 ms window is under 7 ms and U9 stays on for the whole run at 5.71 V',
                      'worst-corner limit 7.50 ms per 100 ms window at 5.71 V, a 0.50 ms margin over the 7 ms line',
                      'The worst admissible train is one open block per 100 ms placed late in the window',
                      'at the 7 ms pass line it holds EN at 1.1295 V at 5.71 V (1.1330 V at 5.73 V) against 1.116 V',
                      'replay of its recorded contact waveform through the worst-corner EN model',
                      'after a 30-130 ms EN turn-on delay',
                      'below the four-stall-plus-fire corner: BAT_IN 5.71 V with a healthy match',
                      '5.55–5.56 V with the match shorted and 5.50 V with the match and leads shorted',
                      'Hold-up after the trip is 0.103–0.164 ms with all ports on and 0.291–0.430 ms with the camera off / shed, '
                      '0.22–0.31 of the break-to-3.8 V hold-up', 'from VLOGIC 4.84–5.17 V, the PA6 0.44–0.47 V window'):
            self.assertIn(words, text)
        for gone in ('Respin: a second via', 'hang on one via', '4.78 V BAT_IN', '10.6/20.5/26.4', '5.92 V', '30-129 ms',
                     'J400 drop-outs shorter than', 'longest measured drop-out < 10 ms', '5.96 V', 'from 5.3 V at 300.8',
                     '0.157–0.182', '0.44–0.48 ms', '18 %', 'about 8.2 ms', 'four-stall BAT_IN of 5.73 V',
                     'whole run at 5.73 V', '7.63 ms per 100 ms window', 'adversarial search', '1.1173 V', '20.0 / 24.4 %',
                     '19.9 % at 0.1 ms', '5.37 V'):
            self.assertNotIn(gone, text)
        # D-R27-02 (R27-TRI-04): the note's Rev 8 statement names the R5-MCU-04 obligation's two Rev 11 limits
        revision = note['sources']['mcu_revision']
        self.assertIn('the LCSC copy is byte-identical), except the two design limits labelled as read from Rev 11 '
                      'Table 109 in round 14 (the 6.0 V FT cap and the 4.0 V ADC-mode maximum; R5-MCU-04 obligation, '
                      'Inference); Rev 11 and RM0433 were not re-read in round 19 (R19-MCU-02)', revision)
        self.assertNotIn('byte-identical); Rev 11', revision)
        self.assertIn('were read from Rev 11 Table 109 in round 14', text)
        # D-R28-03 (R28-TRI-09 and the AGENTS 2.5 sweep): figures resting on inferred inputs carry their label
        for words in ('at least 50× below the 0.30 A no-fire (Calculation / Simulation; driver resistances, flash drive, '
                      'the AON7524 sub-amp curve and the match thermal model are Inference)',
                      'with the inferred 110 C/W theta-JA, Inference; parts_budget.json',
                      'within the 36ms contract (Calculation on allocations: the 0.2 / 0.5 / 1.5 ms need bench tests',
                      'cannot trip U9 (Calculation / Inference, R20-SAF-04 / R24-TRI-02',
                      "C87's 0.72 x minimum takes its X7R DC-bias loss as at most 6 % without the maker's curve",
                      'against 1.116 V (Calculation / Inference, R26-TRI-03: the same EN model)',
                      "Calculation / Inference: the fire budget's hot Q124 factor is inferred",
                      'fire_current_GAP1 model, Calculation / Inference: its hot Q124 factor is inferred',
                      '(Calculation / Inference, D-R25-02: constant power at 300.8 µF'):
            self.assertIn(words, text)
        for gone in ('it must read open', 'reads above 0.9 kOhm both ways', 'fight puts 1.19',
                     'First article, before coating', 'and record the dummy-load drop',
                     'rises about 44 ms or more before 3V3',
                     'cannot trip U9 (Calculation, R20', 'against 1.116 V (Calculation, R26',
                     '(fire_current_GAP1 model, Calculation, R26', '(Calculation, D-R25-02',
                     '(U401 thermal floor, parts_budget.json)', '=34.853ms, within the 36ms contract. '):
            self.assertNotIn(gone, text)
        # D-R28-04: DS15034 Rev 1's Table 2 (pin description) is on p. 11; p. 10 is section 3.1 / Figure 6
        self.assertIn('DS15034 Rev 1 Figure 5 p. 9 and Table 2 p. 11', text)
        self.assertNotIn('Table 2 pp. 10-11', text)
        with (gate.ROOT / 'm3_design/assembly_review/sources/r10_design/pin_table.tsv').open() as table:
            rows = {r['port']: r for r in csv.DictReader(table, delimiter='\t')}
        pulls = {'PA0': 'R154 10k to GND', 'PA1': 'R155 10k to GND', 'PA2': 'R156 10k to GND', 'PA3': 'R157 10k to GND',
                 'PB1': 'R105 1k to GND', 'PD6': 'R90 10k to 3V3', 'PB6': 'R10 10k to 3V3', 'PB7': 'R11 10k to 3V3',
                 'PB8': 'R12 4.7k to 3V3', 'PB9': 'R13 4.7k to 3V3'}
        for port, start in pulls.items():
            self.assertTrue(rows[port]['reset_contract'].startswith(start), (port, rows[port]['reset_contract']))
        self.assertEqual(sum('as R7' in r['reset_contract'] for r in rows.values()), 15)
        self.assertIn('PA5 low also means U9 is blocking reverse current', rows['PA5']['reset_contract'])

    def test_r21_sheet_notes(self):
        """D-R21-03 (R21-REQ-01 / -02): the sensors sheet names the fitted ISM6HG256X (DS15034) with the LSM6DSV320X as
        the second-fallback alternate (D-R23-03); the diagnostics note has no USB self-test of a camera regulator "U8" (the camera rail
        is off on USB-only power); the battery_entry note states OQ-6's no-fuse decision, what is limited only by the
        pack (C88 included), U9's limit and R134's on the RAW_ACT path, whose Q120 drain sits on BAT_IN."""
        import shutil
        import tempfile
        sys.path.insert(0, str(gate.ROOT / 'm3_design'))
        import r10_sch
        import contextlib
        import io
        import warnings
        d = Path(tempfile.mkdtemp(prefix='r10_sch_'))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():   # keep check.sh's summary lines
            warnings.simplefilter('ignore', ResourceWarning)
            r10_sch.build(d, netlist=False)
        sensors, diag, battery = ((d / f'{n}.kicad_sch').read_text() for n in ('sensors', 'diagnostics', 'battery_entry'))
        self.assertIn('U4 = ST ISM6HG256X (D-R19-11; the LSM6DSV320X is the second-fallback alternate (needs part fields, '
                      'BOM and CPL regenerated: ORDERING 8.1) on the same land)', sensors)              # D-R23-03
        self.assertNotIn('consigned alternate', sensors)
        self.assertIn('Pins 10/11 open per DS15034 Table 25 p52.', sensors)
        self.assertNotIn('U4 = ST LSM6DSV320X (R4)', sensors)
        self.assertNotIn('+/-32..320 g', sensors)
        self.assertIn('on USB-only power PORT_5V3 and CAM_5V are off', diag)
        self.assertNotIn('camera regulator (U8)', diag)
        self.assertNotIn('USB self-test', diag)
        # D-R22-03 (R22-MCU-01): R10's camera supply and the real worst cases
        self.assertIn('Nominal 5.456 V (PORT_5V3 via U402) reads 0.496 V', diag)
        self.assertIn("a failed U400 passes RAW_PROTECTED (held under U9's OVLO, 9.77 V nominal) and reads about 0.89 V",
                      diag)
        self.assertIn("even D8's 19.9 V clamp would read 1.81 V", diag)
        self.assertNotIn('5.25 V reads 0.477 V', diag)
        self.assertNotIn('TVS clamp, failed regulator', diag)
        self.assertIn('No battery-lead fuse (owner decision OQ-6, 2026-10-28)', battery)
        self.assertIn('C88 (100 nF)', battery)
        self.assertIn('U9 (TPS259470L) current-limits and latches off RAW_PROTECTED', battery)
        self.assertIn("Q120's drain is on BAT_IN, so the RAW_ACT fire path bypasses U9; R134 (2 Ohm) limits it", battery)
        self.assertNotIn('must be fused', battery)
        # D-R24-19 (R24-TRI-02 / -03): D402's leakage in the worst cases; the pack windows over every corner
        self.assertIn("worst case 10.3/20.1/26.0 ms with 0.1 uA EN leakage plus D402's 50 nA", battery)
        self.assertIn('the pack turns U9 on at 4.72-5.25 V and off at 4.29-4.80 V (nominal 4.96 / 4.51 V)', battery)
        self.assertIn('30-130 ms worst case', battery)
        for gone in ('UVLO on 4.89-5.05 V', 'off 4.45-4.61 V', '30-129 ms', '10.6/20.5/26.4'):
            self.assertNotIn(gone, battery)
        # D-R25-01 (R25-TRI-01): the immunity figure is for a single drop-out; repeated ones add up
        self.assertIn('so a single J400 drop-out shorter than 19/33/41 ms', battery)
        self.assertIn('repeated drop-outs add up (D-R25-01)', battery)
        self.assertNotIn('so J400 drop-outs shorter than', battery)


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class BindingEvidence(unittest.TestCase):
    """Saved evidence faults on a native project copy; validation never repairs its inputs."""
    def setUp(self):
        import shutil
        import tempfile
        source = r10_board()
        self.assertIsNotNone(source, 'no M3-ASSY-R10 board found')
        self.originals = (source, source.parent / 'schematic.net.xml', source.parent / gate.R10_BINDING_NOTE)
        temp = tempfile.TemporaryDirectory(prefix='r10_binding_')
        self.addCleanup(temp.cleanup)
        self.project = Path(temp.name)
        self.board, self.note = self.project / 'm3.kicad_pcb', self.project / gate.R10_BINDING_NOTE
        self.note.parent.mkdir(parents=True)
        for src, dst in zip(self.originals, (self.board, self.project / 'schematic.net.xml', self.note)):
            shutil.copyfile(src, dst)
        self.saved = json.loads(self.note.read_text())

    def snapshot(self):
        return {str(p): p.read_bytes() for p in (*self.originals, *self.project.rglob('*')) if p.is_file()}

    def check(self, ok=True, word=None):
        before = self.snapshot()
        report = gate.check_board(pcbnew.LoadBoard(str(self.board)), self.project, self.board, only={'K-binding'})
        self.assertEqual(self.snapshot(), before, 'binding checker changed an artifact')
        self.assertEqual(report['ok'], ok, report['issues'])
        if word:
            self.assertTrue(any(word in issue for issue in report['issues']), report['issues'])
        return report['rules']['K-binding']['evidence']

    def test_saved_native_note_and_reformatted_json_pass_without_mutation(self):
        evidence = self.check()
        self.assertEqual(evidence['board_sha256'], gate.file_sha(self.board))
        self.assertEqual(evidence['status'], 'record only; R1 binding invalid; no R10 firmware or flight approval')
        self.assertIs(evidence['u1_board_map_checked'], True)
        self.note.write_text(json.dumps(self.saved, sort_keys=True))
        self.check()

    def test_missing_or_malformed_saved_note_fails_without_repair(self):
        for contents in (None, '{', '[]', 'null'):
            with self.subTest(contents=contents):
                if contents is None:
                    self.note.unlink()
                else:
                    self.note.write_text(contents)
                self.check(False, 'binding note')

    def test_saved_hash_pin_axis_and_record_status_faults_fail_independently(self):
        mutant = dict(self.saved)
        del mutant['board_sha256']
        self.note.write_text(json.dumps(mutant))
        self.check(False, 'board_sha256')
        cases = [((name,), '0' * 64) for name in
                 ('board_sha256', 'netlist_sha256', 'pin_table_sha256', 'circuit_sha256')]
        cases += [(('u1_pins', '3', 'net'), 'GND'), (('imu', 'roll_about_forward_axis'), '+gyro_Y'),
                  (('status',), 'approved'), (('u1_board_map_checked',), 1)]
        for keys, value in cases:
            with self.subTest(field=keys):
                mutant = copy.deepcopy(self.saved)
                member = mutant
                for key in keys[:-1]:
                    member = member[key]
                member[keys[-1]] = value
                self.note.write_text(json.dumps(mutant))
                self.check(False, keys[0])

    def test_native_board_hash_pin_and_axis_changes_invalidate_saved_evidence(self):
        mutations = (
            ('board_sha256', lambda b: b.GetTitleBlock().SetComment(0, 'binding regression'), False),
            ('U1.3', lambda b: b.FindFootprintByReference('U1').FindPadByNumber('3').SetNet(b.FindNet('GND')), True),
            ('imu', lambda b: b.FindFootprintByReference('U4').SetOrientationDegrees(0), True),
        )
        for word, mutate, rehash in mutations:
            with self.subTest(field=word):
                board = pcbnew.LoadBoard(str(self.originals[0]))
                mutate(board)
                pcbnew.SaveBoard(str(self.board), board)
                note = dict(self.saved)
                if rehash:
                    note['board_sha256'] = gate.file_sha(self.board)
                self.note.write_text(json.dumps(note))
                self.check(False, word)


class HotplugEvidence(unittest.TestCase):
    """Faults in model artifacts must fail even when their summary says pass."""
    def setUp(self):
        parts = {ref: dict(value=value, fields={'LCSC': code, 'Manufacturer Part': part},
                           pads=[dict(number=str(i), net=net) for i, net in enumerate(nets, 1)])
                 for ref, (value, code, part, nets) in hotplug.MODEL_PARTS.items()}
        parts['C84'] = dict(value='470uF 25V polymer',
                           fields={'Manufacturer Part': 'MA25V470M8x10', 'LCSC': 'C46550466'},
                           pads=[dict(number='1', net='VLOGIC'), dict(number='2', net='GND')])
        parts['U9'] = dict(fields={'Manufacturer Part': 'TPS259470LRPWR'}, pads=[dict(number='6', net='RAW_PROTECTED')])
        edge = dict(length_mm=1., R_ohm=.001, L_near_nH=.5, L_gnd_nH=.5)
        self.inputs = dict(schema=hotplug.SCHEMA, electrical_sha256='electrical fixture', parts=parts,
                           terminals={'J1.1': 'source', 'C88.1': 'bypass', 'U9.5': 'u9'},
                           edges=[dict(edge, a='source', b='bypass'), dict(edge, a='bypass', b='u9')])
        self.rows = [dict(corner=c, minimum_V=-14., maximum_V=2., falling_V_per_us=8., rising_V_per_us=3.)
                     for c in hotplug.cases()]
        self.result = dict(schema=hotplug.SCHEMA, inputs_sha256=hotplug.digest(self.inputs),
                           model_sha256=hotplug.model_sha(), limits=hotplug.LIMITS, topology='board',
                           pack_V=-8.4, initial_input_V=2., step_scale=1., end_us=150., rows=self.rows,
                           passed=True, qualification='pass', convergence_passed=True,
                           retained_output=hotplug.retained_output(self.inputs),
                           no_clamp_control=dict(rows=[dict(self.rows[0], corner=dict(self.rows[0]['corner'], vbr_V=1000.))]),
                           convergence=dict(step_scale=.5, rows=[copy.deepcopy(self.rows[0])]))
        local = [dict(self.rows[0], corner=c) for c in hotplug.local_sensitivity_corners(self.rows)]
        self.result['local_path_sensitivity'] = dict(rows=local, step_scale=hotplug.SENSITIVITY_STEP,
            end_us=hotplug.SENSITIVITY_US, refined_rows=[copy.deepcopy(local[0])],
            refined_step_scale=hotplug.SENSITIVITY_STEP / 2, passed=True)
        self.assertEqual(self.check(self.result), [])

    def check(self, result):
        return hotplug.validate(self.inputs, result, self.inputs['electrical_sha256'])

    def test_failing_corner_cannot_hide_behind_pass_summary(self):
        for key, value in (('minimum_V', -15.001), ('maximum_V', 28.001), ('falling_V_per_us', 10.001),
                           ('rising_V_per_us', 100.001), ('minimum_V', float('nan')),
                           ('falling_V_per_us', float('inf'))):
            with self.subTest(metric=key, value=value):
                bad = copy.deepcopy(self.result); bad['rows'][3][key] = value
                self.assertTrue(self.check(bad))

    def test_stale_or_incomplete_artifacts(self):
        for key, value in (('model_sha256', 'old'), ('inputs_sha256', 'old'), ('topology', 'lumped'),
                           ('pack_V', -7.4), ('initial_input_V', 0.), ('end_us', 0.),
                           ('step_scale', 10.), ('step_scale', float('nan')), ('qualification', 'failed')):
            with self.subTest(field=key):
                bad = copy.deepcopy(self.result); bad[key] = value
                self.assertTrue(self.check(bad))
        bad = copy.deepcopy(self.result); bad['rows'].pop()
        self.assertTrue(self.check(bad))
        bad = copy.deepcopy(self.result); bad['limits']['falling_V_per_us'] = 20.
        # Keep the fixture from mutating the module's independent limit constant.
        with patch.object(hotplug, 'LIMITS', dict(minimum_V=-15., maximum_V=28., falling_V_per_us=10., rising_V_per_us=100.)):
            self.assertTrue(self.check(bad))
        self.assertTrue(hotplug.validate(self.inputs, self.result, 'moved copper'))

    def test_impossible_extrema_fail_even_when_all_controls_agree(self):
        for key, value in (('minimum_V', 27.), ('maximum_V', -100.),
                           ('falling_V_per_us', -1.), ('rising_V_per_us', -1.),
                           ('maximum_V', True)):
            with self.subTest(metric=key, value=value):
                bad = copy.deepcopy(self.result)
                for rows in (bad['rows'], bad['convergence']['rows'], bad['no_clamp_control']['rows']):
                    for row in rows:
                        row[key] = value
                self.assertTrue(self.check(bad))

    def test_numerical_convergence_is_checked_not_just_its_boolean(self):
        for seed in ('missing', 'step', 'delta', 'nan'):
            with self.subTest(seed=seed):
                bad = copy.deepcopy(self.result)
                if seed == 'missing': bad['convergence']['rows'] = []
                if seed == 'step': bad['convergence']['step_scale'] = 1.
                if seed == 'delta': bad['convergence']['rows'][0]['falling_V_per_us'] += .02
                if seed == 'nan': bad['convergence']['rows'][0]['falling_V_per_us'] = float('nan')
                self.assertTrue(self.check(bad))

    def test_component_substitution_cannot_be_qualified_by_refreshing_hashes(self):
        for ref, key, value in (('C80', 'Manufacturer Part', 'different-capacitor'),
                                ('R92', 'LCSC', 'C25804')):
            with self.subTest(ref=ref):
                inputs = copy.deepcopy(self.inputs); result = copy.deepcopy(self.result)
                inputs['parts'][ref]['fields'][key] = value
                result['inputs_sha256'] = hotplug.digest(inputs)
                self.assertTrue(hotplug.validate(inputs, result, inputs['electrical_sha256']))
        inputs = copy.deepcopy(self.inputs); result = copy.deepcopy(self.result)
        inputs['parts']['R92']['pads'][0]['net'] = 'VLOGIC'
        result['inputs_sha256'] = hotplug.digest(inputs)
        self.assertTrue(hotplug.validate(inputs, result, inputs['electrical_sha256']))

    def test_retained_output_and_no_clamp_control_are_required(self):
        for key in ('retained_output', 'no_clamp_control'):
            bad = copy.deepcopy(self.result); bad.pop(key)
            self.assertTrue(self.check(bad))
        inputs = copy.deepcopy(self.inputs); result = copy.deepcopy(self.result)
        for i in range(100):
            inputs['parts']['C' + str(1000 + i)] = dict(value='22uF',
                fields={'Manufacturer Part': 'CL21A226MAQNNNE', 'LCSC': 'C45783'})
        result['inputs_sha256'] = hotplug.digest(inputs)
        result['retained_output'] = hotplug.retained_output(inputs)
        self.assertTrue(hotplug.validate(inputs, result, inputs['electrical_sha256']))

    def test_local_path_topology_and_sensitivity_cannot_be_bypassed(self):
        bad_inputs = copy.deepcopy(self.inputs)
        bad_inputs['edges'].append(dict(bad_inputs['edges'][0], a='source', b='u9'))
        bad = copy.deepcopy(self.result)
        bad['inputs_sha256'] = hotplug.digest(bad_inputs)
        self.assertTrue(hotplug.validate(bad_inputs, bad, bad_inputs['electrical_sha256']))
        for seed in ('missing', 'coarse', 'short', 'corner', 'fails', 'convergence'):
            with self.subTest(seed=seed):
                bad = copy.deepcopy(self.result)
                local = bad['local_path_sensitivity']
                if seed == 'missing': bad.pop('local_path_sensitivity')
                if seed == 'coarse': local['step_scale'] *= 2
                if seed == 'short': local['end_us'] /= 2
                if seed == 'corner': local['rows'].pop()
                if seed == 'fails': local['rows'][0]['falling_V_per_us'] = 10.1
                if seed == 'convergence': local['refined_rows'][0]['falling_V_per_us'] += .02
                self.assertTrue(self.check(bad))


@unittest.skipUnless(plate, 'numpy required')
class HotplugNumerics(unittest.TestCase):
    def test_charge_solver_matches_constant_capacitance_control(self):
        """Independent Python MNA and compiled nonlinear charge solver agree when C is constant."""
        import numpy as np
        inputs = json.loads((hotplug.DESIGN / 'hotplug_baseline_inputs.json').read_text())
        linear = dict(lh_uH=.1, rh_ohm=.03, cap_scale='derated', cb_nF=50., vbr_V=13.3, reference='gnd')
        nonlinear = dict(lh_uH=.1, rh_ohm=.03, bulk='low', damper='low', bypass='low',
                         vbr_V=13.3, reference='gnd', rdamp_ohm=.33)
        ns = np.full(3, 2, dtype=np.int32)
        xs = np.zeros((3, 160)); xs[:, 1] = 30.
        cs = np.ones((3, 160)); qs = xs.copy()
        factors = [dict(low=.47), dict(low=16.7/44.), dict(low=.5)]
        expected = hotplug.run(inputs, [linear], dt_ns=.25, end_us=2.)[0]
        with patch.object(hotplug, 'curves', return_value=(ns, xs, cs, qs, factors)):
            actual = hotplug.run_nonlinear(inputs, [nonlinear], step_scale=.5, end_us=2.)[0]
        self.assertAlmostEqual(actual['minimum_V'], expected['minimum_V'], delta=.002)
        self.assertAlmostEqual(actual['falling_V_per_us'], expected['falling_V_per_us'], delta=.01)
        self.assertGreater(actual['falling_V_per_us'], 10.)  # the real baseline split feed must fail

    def test_invalid_circuit_and_integration_inputs_fail(self):
        inputs = json.loads((hotplug.DESIGN / 'hotplug_baseline_inputs.json').read_text())
        corner = hotplug.cases()[0]
        for kwargs in ({'step_scale': 0.}, {'step_scale': float('nan')}, {'end_us': 0.}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                hotplug.run_nonlinear(inputs, [corner], **kwargs)
        inputs['edges'][0]['L_gnd_nH'] = float('nan')
        with self.assertRaises(ValueError):
            hotplug.run_nonlinear(inputs, [dict(corner, reference='gnd')], end_us=.1)


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class Native(unittest.TestCase):
    def point(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def setUp(self):
        import route_check
        self.addCleanup(route_check.set_profile, 'r8')
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(4)
        for net in ('RAW_ACT', 'GPS_TX_MCU', 'GND'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))

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
    NETS = ('RAW_ACT', 'PYRO1_IGN', 'PYRO1_OUT', 'BAT_IN', 'ACT_FET_S', 'ACT_GATE', 'ACT_DRV', 'PYRO1_GATE',
            'PYRO1_GATE_N', 'GND', 'GPS_TX_MCU', 'SERVO1_OUT', 'RAW_PROTECTED', '3V3', 'ARM1_SENSE', 'PYRO1_COLD',
            'PYRO1_CONT', 'ARM1_SENSE_MID', 'ACT_EN_MCU', 'ACT_EN', 'BAT_SW_SOURCE', 'BAT_SW_RETURN', 'BAT_ENABLE')

    def P(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def setUp(self):
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(4)
        for net in self.NETS:
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
        self.outline(46, 90)
        self.r134 = self.part('R134', [('2', 0, 0, 'RAW_ACT'), ('1', 3.5, 0, 'PYRO1_IGN')], at=(5, 20), tht=True)
        self.r132 = self.part('R132', [('1', 0, 0, 'RAW_ACT'), ('2', 1, 0, 'ARM1_SENSE_MID')], at=(30, 45))

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
    # --- S-1 canonical RAW_ACT bus --------------------------------------------------------------------------------------------
    def test_s1_clean_unified_bus(self):
        self.assertEqual(gate.s1(self.ctx())[0], [])

    def test_s1_track_bypasses_r134(self):
        for net in (None, 'RAW_ACT', 'GND'):
            with self.subTest(net=net):
                t = self.track((5, 20), (8.5, 20), net, pcbnew.B_Cu)
                self.assertTrue(any('firing / sense chain is bypassed' in i for i in gate.s1(self.ctx())[0]))
                self.board.Remove(t)

    def test_s1_track_chain_and_via_bridge(self):
        self.track((5, 20), (5, 25), None, pcbnew.F_Cu)
        v = pcbnew.PCB_VIA(self.board); v.SetPosition(self.P(5, 25)); v.SetWidth(pcbnew.FromMM(0.6))
        v.SetDrill(pcbnew.FromMM(0.3)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); self.board.Add(v)
        self.track((5, 25), (8.5, 25), None, pcbnew.B_Cu)
        self.assertEqual(gate.s1(self.ctx())[0], [])            # not yet joined to R134.1
        self.track((8.5, 25), (8.5, 20), None, pcbnew.B_Cu)
        self.assertTrue(any('bypassed' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_part_bypasses_r134(self):
        self.part('R999', [('1', 0, 0, 'RAW_ACT'), ('2', 1.5, 0, 'PYRO1_IGN')], at=(30, 30))
        self.assertTrue(any('outside R134 / R132' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_part_bypass_through_another_net(self):
        self.part('R998', [('1', 0, 0, 'RAW_ACT'), ('2', 1.5, 0, 'PYRO1_GATE_N')], at=(30, 30))
        self.part('R997', [('1', 0, 0, 'PYRO1_GATE_N'), ('2', 1.5, 0, 'PYRO1_IGN')], at=(30, 35))
        self.assertTrue(any('RAW_ACT reaches PYRO1_IGN outside R134 / R132' in i for i in gate.s1(self.ctx())[0]))

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
                                  ('R992', '3V3', 'PYRO1_IGN', 'S-1'), ('R989', 'PYRO1_CONT', 'BAT_IN', 'S-2'),
                                  ('R988', 'PYRO1_COLD', 'GND', 'S-2')):
            with self.subTest(ref=ref):
                f = self.part(ref, [('1', 0, 0, a), ('2', 1.5, 0, sup)], at=(30, 30))
                run = gate.s1 if rule == 'S-1' else gate.s2
                self.assertTrue(any(f'{ref} has pads on' in i for i in run(self.ctx())[0]), run(self.ctx())[0])
                self.board.Remove(f)

    def test_s1_s2_chain_through_3v3_and_big_part(self):
        self.load_switch()
        self.part('R991', [('1', 0, 0, 'RAW_ACT'), ('2', 1.5, 0, '3V3')], at=(30, 30))
        self.part('R992', [('1', 0, 0, '3V3'), ('2', 1.5, 0, 'PYRO1_IGN')], at=(30, 35))
        self.assertEqual(len([i for i in gate.s1(self.ctx())[0] if 'has pads on' in i]), 2)
        # a six-net part (past MAX_PART_NETS) with one pad on RAW_ACT and one on BAT_IN
        self.part('U9', [('1', 0, 0, 'RAW_ACT'), ('2', 1, 0, 'BAT_IN'), ('3', 2, 0, 'GND'), ('4', 3, 0, 'ACT_DRV'),
                         ('5', 4, 0, 'ACT_GATE'), ('6', 5, 0, 'SERVO1_OUT')], at=(35, 60))
        self.assertTrue(any('U9 has pads on' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_test_pad_on_armed_copper(self):
        self.part('TP9', [('1', 0, 0, 'RAW_ACT')], at=(30, 30))
        self.assertTrue(any('test pad TP9' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_any_part_on_armed_copper(self):
        """R6-GATE-07 / R6-SAF-01: any part but the named armed-side ones, whatever its reference."""
        self.part('PT121', [('1', 0, 0, 'RAW_ACT')], at=(30, 30))
        self.assertTrue(any('PT121' in i and 'named armed-side' in i for i in gate.s1(self.ctx())[0]))
        self.board.Remove(self.board.FindFootprintByReference('PT121'))
        self.part('U77', [('1', 0, 0, 'PYRO1_IGN'), ('2', 1, 0, 'GND')], at=(30, 35))
        self.assertTrue(any('U77' in i for i in gate.s1(self.ctx())[0]))
        self.board.Remove(self.board.FindFootprintByReference('U77'))
        self.assertEqual(gate.s1(self.ctx())[0], [])
        self.board.FindFootprintByReference('R132').FindPadByNumber('1').SetNet(self.board.FindNet('PYRO1_IGN'))
        self.assertTrue(any('R132 is on armed net' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_removed_terminal_and_separate_bus(self):
        f = self.part('J124', [('1', 0, 0, 'RAW_ACT'), ('2', 3.5, 0, 'PYRO1_IGN')], at=(5, 10), tht=True)
        self.assertTrue(any('obsolete J124' in i for i in gate.s1(self.ctx())[0]))
        self.board.Remove(f)
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'PYRO1_BUS'))
        self.assertTrue(any('obsolete PYRO1_BUS' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_feed_and_bus_sense_must_be_on_raw_act(self):
        for f, num in ((self.r134, '2'), (self.r132, '1')):
            with self.subTest(ref=f.GetReference()):
                p = f.FindPadByNumber(num)
                p.SetNet(self.board.FindNet('BAT_IN'))
                self.assertTrue(any(f'{f.GetReference()}.{num} must be on RAW_ACT' in i for i in gate.s1(self.ctx())[0]))
                p.SetNet(self.board.FindNet('RAW_ACT'))

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
        self.part('R993', [('1', 0, 0, 'RAW_ACT'), ('2', 1.5, 0, 'BAT_IN')], at=(30, 30))
        self.assertTrue(any('RAW_ACT is joined to BAT_IN' in i for i in gate.s2(self.ctx())[0]))

    def test_s2_copper_short_to_supply(self):
        self.load_switch()
        self.part('C999', [('1', 0, 0, 'BAT_IN'), ('2', 1.5, 0, 'GND')], at=(30, 30))
        self.track((5, 20), (30, 30), None)
        self.assertTrue(any('RAW_ACT copper touches C999.1 (BAT_IN)' in i for i in gate.s2(self.ctx())[0]))

    def test_s1_s2_multinet_part_bridge(self):
        """R5-SAF-01: a part with more than MAX_PART_NETS nets joining a RAW-side and an armed-side net fails S-1 and S-2."""
        self.load_switch()
        for raw, armed in (('ACT_EN_MCU', 'ARM1_SENSE'), ('ACT_GATE', 'PYRO1_CONT')):
            with self.subTest(raw=raw):
                u = self.part('U12', [('1', 0, 0, raw), ('2', 1, 0, armed), ('3', 2, 0, 'GND'), ('4', 3, 0, '3V3'),
                                      ('5', 4, 0, 'GPS_TX_MCU')], at=(30, 30))
                for fn, rid in ((gate.s1, 'S-1'), (gate.s2, 'S-2')):
                    self.assertTrue(any('bypasses the named pyro / sense chain' in i for i in fn(self.ctx())[0]), (rid, fn(self.ctx())[0]))
                self.board.Remove(u)
        u = self.part('U12', [('1', 0, 0, 'ACT_EN_MCU'), ('2', 1, 0, 'GND'), ('3', 2, 0, '3V3'),
                              ('4', 3, 0, 'GPS_TX_MCU'), ('5', 4, 0, 'ACT_DRV')], at=(30, 30))   # one side only: fine
        self.assertFalse(any('bridges' in i for i in gate.s1(self.ctx())[0] + gate.s2(self.ctx())[0]))

    # --- S-3 gate networks ----------------------------------------------------------------------------------------
    def gates(self):
        self.load_switch()
        self.part('U1', [('3', 0, 0, 'PYRO1_GATE_N'), ('5', 1, 0, 'GND'), ('6', 2, 0, 'GND'), ('7', 3, 0, 'GND'),
                         ('8', 4, 0, 'GND'), ('9', 5, 0, 'GND'), ('16', 6, 0, 'ACT_EN_MCU')], at=(25, 70))
        self.part('Q124', [('1', 0, 0, 'GND'), ('2', 1, 0, 'GND'), ('3', 2, 0, 'GND'), ('4', 3, 0, 'PYRO1_GATE'),
                           ('5', 1, 3, 'PYRO1_IGN')], at=(10, 60))
        self.part('R128', [('1', 0, 0, 'PYRO1_GATE'), ('2', 1.5, 0, 'GND')], at=(10, 70))
        self.part('C126', [('1', 0, 0, 'PYRO1_GATE'), ('2', 1.5, 0, 'GND')], at=(10, 72))
        self.part('R126', [('1', 0, 0, 'PYRO1_GATE_N'), ('2', 1.5, 0, 'PYRO1_GATE')], at=(10, 74))
        self.part('R127', [('1', 0, 0, 'PYRO1_GATE_N'), ('2', 1.5, 0, 'GND')], at=(10, 76))
        self.part('R120', [('1', 0, 0, 'ACT_FET_S'), ('2', 1.5, 0, 'ACT_GATE')], at=(30, 70))
        self.part('C120', [('1', 0, 0, 'ACT_FET_S'), ('2', 1.5, 0, 'ACT_GATE')], at=(30, 72))
        self.part('R121', [('1', 0, 0, 'ACT_GATE'), ('2', 1.5, 0, 'ACT_DRV')], at=(30, 74))
        self.part('Q122', [('1', 0, 0, 'ACT_EN'), ('2', 1, 0, 'GND'), ('3', 2, 0, 'ACT_DRV')], at=(35, 65))
        self.part('R122', [('1', 0, 0, 'ACT_EN_MCU'), ('2', 1.5, 0, 'ACT_EN')], at=(35, 68)).SetValue('1k')
        self.part('R123', [('1', 0, 0, 'ACT_EN'), ('2', 1.5, 0, 'GND')], at=(35, 72)).SetValue('2k')
        # D-R19-04: Q122's gate-source capacitor
        self.part('C123', [('1', 0, 0, 'ACT_EN'), ('2', 1.5, 0, 'GND')], at=(35, 74)).SetValue('10nF 50V X7R 10%')
        # D-R18-02: each P-FET's gate-source resistor joined to its gate and source pads by its own layer's copper
        self.part('R119', [('1', 0, 0, 'ACT_GATE'), ('2', 1.5, 0, 'ACT_FET_S')], at=(24, 53)).SetValue('100k')
        self.local = [self.track((23, 50), (24, 53), 'ACT_GATE'), self.track((22, 50), (25.5, 53), 'ACT_FET_S'),
                      self.track((23, 40), (31.5, 70), 'ACT_GATE'), self.track((22, 40), (30, 70), 'ACT_FET_S')]

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

    def test_s3_independent_mcu_enable_and_reset_pull(self):
        self.gates()
        self.assertEqual(gate.s3(self.ctx())[0], [])
        for ref, num, net in (('U1', '16', 'PYRO1_GATE_N'), ('R122', '1', 'RAW_PROTECTED'),
                              ('R123', '2', '3V3'), ('Q122', '2', 'ACT_GATE')):
            with self.subTest(ref=ref, num=num):
                p = self.board.FindFootprintByReference(ref).FindPadByNumber(num)
                old = p.GetNet(); p.SetNet(self.board.FindNet(net))
                self.assertTrue(any('independent load-switch enable' in i for i in gate.s3(self.ctx())[0]))
                p.SetNet(old)
        for ref, value in (('R122', '0R'), ('R123', '1M')):
            f = self.board.FindFootprintByReference(ref); old = f.GetValue(); f.SetValue(value)
            self.assertTrue(any(f'{ref} must be' in i for i in gate.s3(self.ctx())[0]))
            f.SetValue(old)
        self.board.Remove(self.board.FindFootprintByReference('R123'))
        self.assertTrue(any('R123' in i for i in gate.s3(self.ctx())[0]))

    def test_r19_s3_q122_gate_source_capacitor(self):
        """D-R19-04 (R19-SAF-06): S-3 fails a missing, misplaced or wrong-valued Q122 gate-source capacitor C123 and a
        fourth part on ACT_EN; the full network passes."""
        self.gates()
        self.assertEqual(gate.s3(self.ctx())[0], [])
        c = self.board.FindFootprintByReference('C123')
        c.SetValue('100nF 50V X7R 10%')
        self.assertTrue(any('C123 must be 1e-08 F' in i for i in gate.s3(self.ctx())[0]))
        c.SetValue('10nF 50V X7R 10%')
        p = c.FindPadByNumber('2'); p.SetNet(self.board.FindNet('3V3'))
        self.assertTrue(any('C123.2 must be GND' in i for i in gate.s3(self.ctx())[0]))
        p.SetNet(self.board.FindNet('GND'))
        self.part('C124', [('1', 0, 0, 'ACT_EN'), ('2', 1.5, 0, 'GND')], at=(35, 76)).SetValue('10nF')
        self.assertTrue(any("ACT_EN must touch only ['C123', 'Q122', 'R122', 'R123']" in i
                            for i in gate.s3(self.ctx())[0]))
        self.board.Remove(self.board.FindFootprintByReference('C124'))
        self.board.Remove(c)
        self.assertTrue(any('C123.1 must be ACT_EN (is None)' in i for i in gate.s3(self.ctx())[0]))

    def test_s3_local_gate_bias_needs_same_layer_copper(self):
        """R18-SAF-02 / D-R18-02: a gate-source resistor reached only through a layer change (or not at all) leaves the
        P-FET gate floating when that via opens; S-3 requires one joined by the FET's own layer."""
        self.gates()
        self.assertEqual(gate.s3(self.ctx())[0], [])
        self.board.Remove(self.local[0])                                  # R119 now reaches Q121's gate by no copper
        found = gate.s3(self.ctx())[0]
        self.assertTrue(any('load switch Q121: no gate-source resistor' in i and 'F.Cu copper alone' in i
                            for i in found), found)
        self.assertFalse(any('Q120: no gate-source resistor' in i for i in found), found)
        self.via(23.5, 51.5, 'ACT_GATE')                                  # a layer change does not count
        self.track((23, 50), (23.5, 51.5), 'ACT_GATE', pcbnew.B_Cu); self.track((23.5, 51.5), (24, 53), 'ACT_GATE', pcbnew.B_Cu)
        self.assertTrue(any('Q121: no gate-source resistor' in i for i in gate.s3(self.ctx())[0]))
        self.track((23, 50), (24, 53), 'ACT_GATE')
        self.assertEqual(gate.s3(self.ctx())[0], [])

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

    def test_parse_value_spaced_unit_and_mu(self):
        """R7-GATE-01: a space before the multiplier or unit, Omega after the multiplier, Greek mu."""
        for text, want in (('4.7 k\u03a9', 4700.0), ('220 \u03a9', 220.0), ('220 k\u03a9', 220e3), ('4.7k\u03a9', 4700.0),
                           ('4.7 k', 4700.0), ('10 ohm', 10.0), ('1 M', 1e6), ('4.7k\u2126 1%', 4700.0)):
            self.assertAlmostEqual(gate.parse_value(text, 'R'), want, msg=text)
        for text in ('4.7 kx', '4.7k\u03a9x', '220 kk'):
            self.assertIsNone(gate.parse_value(text, 'R'), text)
        self.assertAlmostEqual(gate.parse_value('2.2 \u03bcF', 'C'), 2.2e-6)
        self.assertAlmostEqual(gate.parse_value('2.2\u00b5F', 'C'), 2.2e-6)
        self.assertIsNone(gate.parse_value('100m', 'C'))
        self.assertAlmostEqual(gate.parse_value('100mF', 'C'), 0.1)
        self.assertAlmostEqual(gate.parse_value('100 nF', 'C'), 100e-9)

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
        f = self.r134
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
        for ref in ('R134', 'R126', 'R127', 'R128', 'C126', 'Q124', 'Q120', 'Q121', 'R120', 'C120', 'J400', 'R80', 'R165', 'R122', 'R123', 'J121',
                    'R129', 'R130', 'R131', 'R132', 'R133', 'R173', 'R175', 'R178', 'R180', 'C128'):
            self.assertIn(ref, gate.SAFETY_FITTED)

    # --- S-5 single screw switch -------------------------------------------------------------------------------
    def power_switch(self):
        self.part('J400', [('1', 0, 0, 'BAT_SW_SOURCE'), ('2', 3.5, 0, 'BAT_SW_RETURN')], at=(5, 10))
        self.part('R80', [('1', 0, 0, 'BAT_IN'), ('2', 1.5, 0, 'BAT_SW_SOURCE')], at=(15, 10)).SetValue('470k 1%')
        self.part('R165', [('1', 0, 0, 'BAT_SW_RETURN'), ('2', 1.5, 0, 'BAT_ENABLE')], at=(20, 10)).SetValue('470k 1%')
        self.part('U9', [('1', 0, 0, 'BAT_ENABLE')], at=(25, 10))
        # D-R24-11: J400.2's ESD clamp to GND, the one further member of BAT_SW_RETURN
        d = self.part('D402', [('1', 0, 0, 'BAT_SW_RETURN'), ('2', 0.65, 0, 'GND')], at=(5, 14))
        d.SetValue('ESD103-B1-02EL'); d.SetField('LCSC', 'C535146')
        return d

    def test_s5_switch_topology_and_resistor_values(self):
        clamp = self.power_switch()
        self.assertEqual(gate.s5(self.ctx())[0], [])
        for ref, num, net in (('J400', '1', 'BAT_IN'), ('R165', '2', 'RAW_PROTECTED'), ('U9', '1', 'RAW_ACT'),
                              ('D402', '2', 'BAT_ENABLE'), ('D402', '2', 'BAT_SW_RETURN'), ('D402', '1', 'GND')):
            p = self.board.FindFootprintByReference(ref).FindPadByNumber(num)
            old = p.GetNet(); p.SetNet(self.board.FindNet(net))
            self.assertTrue(any(f'{ref}.{num} must be' in i for i in gate.s5(self.ctx())[0]))
            p.SetNet(old)
        self.assertEqual(gate.s5(self.ctx())[0], [])
        clamp.SetValue('SMBJ12CA')
        self.assertTrue(any('D402 must be the two-pad ESD103-B1-02EL C535146' in i for i in gate.s5(self.ctx())[0]))
        clamp.SetValue('ESD103-B1-02EL')
        clamp.SetReference('D999')          # the clamp missing (renamed, not removed: KiCad 10 SWIG ownership)
        found = gate.s5(self.ctx())[0]
        self.assertTrue(any("D402 (J400.2's ESD clamp, D-R24-11) is missing" in i for i in found), found)
        self.assertTrue(any("BAT_SW_RETURN must touch only ['D402', 'J400', 'R165']" in i for i in found), found)
        clamp.SetReference('D402')
        self.board.FindFootprintByReference('R80').SetValue('0R')
        self.assertTrue(any('R80 must be 470k' in i for i in gate.s5(self.ctx())[0]))

    def test_s5_switch_contact_cannot_be_bypassed(self):
        self.power_switch()
        f = self.part('R999', [('1', 0, 0, 'BAT_SW_SOURCE'), ('2', 1.5, 0, 'BAT_SW_RETURN')], at=(30, 10))
        found = gate.s5(self.ctx())[0]
        self.assertTrue(any('bypasses the open J400 switch' in i for i in found))
        # D-R24-11: any fourth member of BAT_SW_RETURN fails the exact pad set as well
        self.assertTrue(any("BAT_SW_RETURN pads must be exactly ['D402.1', 'J400.2', 'R165.1']" in i for i in found), found)
        self.board.Remove(f)
        self.track((5, 10), (8.5, 10), None)
        self.assertTrue(any('switch contact / resistor bypass' in i for i in gate.s5(self.ctx())[0]))

    # --- S-6 external ports ---------------------------------------------------------------------------------------
    def test_s6_port_net_beside_pyro_bus(self):
        self.track((5, 22.0), (12, 22.0), 'GPS_TX_MCU')         # 1.0 mm from the pad edges: fine
        self.assertEqual(gate.s6(self.ctx())[0], [])
        self.track((3, 21.1), (7, 21.1), 'GPS_TX_MCU')          # 0.05 mm from R134.2's synthetic pad
        self.assertTrue(any('GPS_TX_MCU' in i and 'RAW_ACT' in i for i in gate.s6(self.ctx())[0]))

    def test_s6_shared_copper_and_shared_part(self):
        self.track((5, 20), (5, 26), 'GPS_TX_MCU')
        self.assertTrue(any('shared copper' in i for i in gate.s6(self.ctx())[0]))
        self.board.Remove(self.board.GetTracks()[0])
        self.part('R992', [('1', 0, 0, 'GPS_TX_MCU'), ('2', 1.5, 0, 'ACT_GATE')], at=(30, 30))
        self.assertTrue(any('R992 joins port nets' in i for i in gate.s6(self.ctx())[0]))
        self.part('U1', [('1', 0, 0, 'GPS_TX_MCU'), ('2', 1.5, 0, 'PYRO1_GATE_N')], at=(30, 60))
        self.assertFalse(any('U1 joins' in i for i in gate.s6(self.ctx())[0]))

    # --- S-7 J122 -------------------------------------------------------------------------------------------------
    def servo_terminal(self):
        for net in ('SERVO2_OUT', 'SERVO3_OUT', 'SERVO4_OUT'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
        return self.part('J122', [(str(i), 3.5 * (i - 1), 0, net)
                                 for i, net in enumerate(gate.SERVO_TERMINAL, 1)], at=(15, 80), tht=True, size=1.9)

    def test_s7_five_signal_reference_contacts(self):
        f = self.servo_terminal()
        self.assertEqual(gate.s7(self.ctx())[0], [])
        f.FindPadByNumber('2').SetNet(self.board.FindNet('RAW_ACT'))
        self.assertTrue(any('J122.2 must be SERVO2_OUT' in i for i in gate.s7(self.ctx())[0]))
        f.FindPadByNumber('2').SetNet(self.board.FindNet('SERVO2_OUT'))
        extra = pcbnew.Cast_to_PAD(f.FindPadByNumber('5').Duplicate())
        extra.SetNumber('6'); f.Add(extra)
        self.assertTrue(any('exactly five' in i for i in gate.s7(self.ctx())[0]))

    def test_s7_common_signal_reference(self):
        f = self.servo_terminal()
        f.FindPadByNumber('5').SetNet(self.board.FindNet('BAT_IN'))
        self.assertTrue(any('J122.5 must be GND' in i for i in gate.s7(self.ctx())[0]))

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
        f = self.r134
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
        expect = {'PYRO1_GATE': 'pyro', 'PYRO1_BUS': 'pyro', 'ARM1_SENSE': 'pyro', 'HSE_IN': 'crystal', 'USB_DP': 'usb', 'USB_DM': 'usb',
                  'QSPI_CLK': 'spi', 'SPI1_SCK': 'spi', 'IMU_CS': 'spi', 'GPS_TX_MCU': 'uart', 'RADIO_RX_MCU': 'uart',
                  'GND': 'power', '3V3': 'power', 'RAW_ACT': 'power', 'PORT_5V3': 'power', 'GPS_4V8': 'power',
                  'RADIO_4V8': 'power', 'CAM_5V': 'power', 'GPS_IO_3V3': 'power', 'SERVO1_OUT': 'actuator'}
        for net, cls in expect.items():
            self.assertEqual(rc.net_class(net), cls, net)
        for net in expect:
            if expect[net] not in ('power', 'actuator'):
                self.assertIn(rc.net_class(net), rc.SIGNAL_CRITICAL, net)
        # R3-RTE-01 / R3-SAF-03: every external-port signal and the pyro-bus load-switch drive are critical
        for net, cls in (('CAM_PWR_EN', 'portctl'), ('CAM_FAULT_N', 'portctl'), ('CAM_UART_OE', 'portctl'),
                         ('CAM_MCU_TX', 'uart'), ('CAM_MCU_RX', 'uart'), ('GPS_TX_WIRE', 'uart'),
                         ('RADIO_RX_MCU', 'uart'), ('CAM_TX_WIRE', 'uart'), ('ACT_GATE', 'pyro'),
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
        names = {f'{p}_{s}' for p in ('GPS', 'RADIO', 'AUX', 'CAM') for s in ('TX_MCU', 'RX_MCU', 'TX_WIRE', 'RX_WIRE',
                 'TX_BUFFER', 'RX_BUFFER', 'PWR_EN', 'FAULT_N', 'UART_OE', '4V8', '5V', 'ILIM', 'IO_3V3')}
        names |= {'CAM_MCU_TX', 'CAM_MCU_RX'}
        self.assertEqual({n for n in names if rc.net_class(n) in ('uart', 'portctl')},
                         {n for n in names if n in cr.R10_PORT_NETS})

    def test_spi3_sd_nets_keep_critical_returns_and_qspi(self):
        import critical_reference as cr
        import route_check as rc
        self.addCleanup(rc.set_profile, 'r8'); rc.set_profile('r10')
        for net in cr.R10_SD_NETS:
            self.assertEqual(rc.net_class(net), 'spi')
            self.assertTrue(rc.return_required(net))
            self.assertFalse(cr.r10_slow_return_net(net))
        self.assertEqual(rc.net_class('QSPI_CLK'), 'spi')
        self.assertEqual(rc.net_class('SPI1_SCK'), 'spi')

    def test_direct_adc_contract_has_no_series_tail_or_mandatory_plate(self):
        pins = gate.mcu_pin_table()
        self.assertEqual((pins['15'], pins['33'], pins['34']), ('PYRO1_CONT', 'ARM1_SENSE', 'NC'))
        for ref in ('R168', 'R170', 'R172', 'R177', 'R124', 'R125', 'R182', 'C122'):
            self.assertNotIn(ref, gate.REQUIRED_FITTED)
            self.assertIn(ref, gate.REMOVED)
        self.assertNotIn('P-8', gate.STAGES['full'])
        self.assertNotIn('M-2', gate.STAGES['full'])


    def test_rule_list_and_stages(self):
        ids = [rid for rid, _, _ in gate.RULES]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({'S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7'} <= gate.STAGES['functional'])
        self.assertTrue(gate.STAGES['functional'] < gate.STAGES['placement'] < gate.STAGES['full'])
        self.assertIn('K-binding', gate.STAGES['full'])
        self.assertNotIn('K-binding', gate.STAGES['placement'])
        for gone in ('P-0', 'P-1', 'P-3', 'P-4', 'P-5', 'P-6', 'P-7', 'K-power-pyro') + tuple(f'R-{i}' for i in range(1, 14)):
            self.assertNotIn(gone, ids)
        for rid in ('K-power', 'K-lands'):                  # R18-GATE-02 / -03 / -09: finished copper and library
            self.assertIn(rid, gate.STAGES['full'])
            self.assertNotIn(rid, gate.STAGES['placement'])


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

    def test_k_fill_geometry_equivalence_and_difference_tolerance(self):
        import tempfile
        layer = pcbnew.In2_Cu
        zone = self.plane('GND', 10, 10, 20, 20, layer)
        zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        original = pcbnew.SHAPE_POLY_SET(zone.GetFilledPolysList(layer))
        self.assertEqual(original.OutlineCount(), 1)
        self.assertEqual(original.HoleCount(0), 0)
        chain = original.Outline(0)
        points = [(chain.CPoint(i).x, chain.CPoint(i).y) for i in range(chain.PointCount())]
        self.assertGreater(original.Area(), 0)

        def polygon(vertices):
            poly = pcbnew.SHAPE_POLY_SET(); poly.NewOutline()
            for x, y in vertices:
                poly.Append(x, y)
            return poly

        # A different vertex origin and an extra collinear node describe the same copper.
        equivalent = points[1:] + points[:1]
        a, b = equivalent[:2]
        equivalent.insert(1, ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2))
        reshaped = polygon([(x + y - points[0][1], y) for x, y in points])  # area-preserving shear
        self.assertEqual(reshaped.Area(), original.Area())
        height = max(y for x, y in points) - min(y for x, y in points)
        inside = int(gate.FILL_TOLERANCE * 1e12 / (2 * height))
        cases = [('equivalent', polygon(equivalent), False), ('equal-area reshape', reshaped, True)]
        for delta, reject in ((inside, False), (inside + 1, True)):
            poly = pcbnew.SHAPE_POLY_SET(original); poly.Move(pcbnew.VECTOR2I(delta, 0))
            self.assertEqual(poly.Area(), original.Area())
            cases.append((f'translation {delta} nm', poly, reject))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'm3.kicad_pcb'
            for name, poly, reject in cases:
                with self.subTest(name=name):
                    zone.SetFilledPolysList(layer, poly)
                    pcbnew.SaveBoard(str(path), self.board)
                    issues, evidence = gate.fill_freshness(path)
                    self.assertEqual(bool(issues), reject, (issues, evidence))

    def test_signal_critical_nets_share_route_check_definition(self):
        import route_check as rc
        got = gate.signal_critical_nets(self.board)
        self.assertTrue({'PYRO1_CONT', 'ARM1_SENSE', 'ARM1_SENSE_MID', 'PYRO1_GATE', 'SPI1_SCK'} <= got)
        self.assertFalse({'GND', '3V3', 'BAT_IN', 'PORT_5V3'} & got)
        rc.set_profile('r10')
        self.assertTrue(all(rc.net_class(n) in rc.SIGNAL_CRITICAL for n in got))

    def test_k_reference_samples_the_pyro_class(self):
        import critical_reference as cr
        self.track((20, 30), (22.5, 30), 'PYRO1_GATE', pcbnew.B_Cu)
        gnd = pcbnew.SHAPE_POLY_SET(); gnd.NewOutline()
        for x, y in ((10, 10), (40, 10), (40, 40), (10, 40)):
            gnd.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        with patch.object(cr, 'fills', return_value={pcbnew.B_Cu: pcbnew.SHAPE_POLY_SET()}):
            issues, ev = gate.references(self.board)
        self.assertTrue(issues and 'PYRO1_GATE B.Cu' in ev['by_net_layer'], (issues, ev))
        with patch.object(cr, 'fills', return_value={pcbnew.B_Cu: gnd}):
            self.assertEqual(gate.references(self.board)[0], [])

    def test_sd_returns_cannot_use_the_slow_control_exemption(self):
        import critical_reference as cr
        for index, net in enumerate(cr.R10_SD_NETS):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
            self.track((20, 25 + index), (22, 25 + index), net, pcbnew.B_Cu)
        with patch.object(cr, 'fills', return_value={pcbnew.B_Cu: pcbnew.SHAPE_POLY_SET()}):
            issues, evidence = gate.references(self.board)
        self.assertTrue(issues)
        self.assertTrue(all(net + ' B.Cu' in evidence['by_net_layer'] for net in cr.R10_SD_NETS))
        issues, evidence = gate.region_issues(self.board)
        self.assertTrue(all(any(net + ' ' in issue for issue in issues) for net in cr.R10_SD_NETS))

    def test_k_region_one_plane_per_run(self):
        self.plane('GND', 10, 10, 30, 40)
        self.track((12, 30), (28, 30), 'PYRO1_GATE', pcbnew.B_Cu)
        self.assertEqual(gate.region_issues(self.board)[0], [])
        self.track((12, 32), (28, 32), 'GND', pcbnew.B_Cu)                       # not signal-critical: ignored
        self.assertEqual(gate.region_issues(self.board)[0], [])
        self.plane('3V3', 30.05, 10, 40, 40)                                    # a second plane, a 0.05 mm seam
        self.track((24, 20), (36, 20), 'GPS_TX_MCU', pcbnew.B_Cu)           # crosses GND -> 3V3
        issues = gate.region_issues(self.board)[0]
        self.assertTrue(any('GPS_TX_MCU' in i and "['3V3', 'GND']" in i for i in issues), issues)
        self.assertFalse(any('PYRO1_GATE' in i for i in issues))

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

    def test_r19_own_barrel_void_is_exempt_for_hazard_nets_only(self):
        """D-R19-01: inside the S-8 void round a PYRO1_OUT (GND-hazard) barrel, K-region and K-reference skip that net's
        own samples; beyond the void, for a non-hazard net (PYRO1_GATE) and for a fast net crossing the void, they do not."""
        import critical_reference as cr
        import math as m
        via = pcbnew.PCB_VIA(self.board); via.SetPosition(self.P(20, 25)); via.SetWidth(pcbnew.FromMM(0.5))
        via.SetDrill(pcbnew.FromMM(0.3)); via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(self.board.FindNet('PYRO1_OUT')); self.board.Add(via)
        keep = pcbnew.ZONE(self.board); keep.SetIsRuleArea(True); keep.SetDoNotAllowZoneFills(True)
        keep.SetDoNotAllowTracks(False); keep.SetDoNotAllowVias(False); keep.SetDoNotAllowPads(False)
        keep.SetDoNotAllowFootprints(False); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.In2_Cu); keep.SetLayerSet(ls)
        o = keep.Outline(); o.NewOutline()
        rr = 1.2 / m.cos(m.pi / 16)
        for k in range(16):
            a = 2 * m.pi * (k + .5) / 16
            o.Append(pcbnew.FromMM(20 + rr * m.cos(a)), pcbnew.FromMM(25 + rr * m.sin(a)))
        self.board.Add(keep)
        self.plane('GND', 10, 10, 30, 40)
        self.track((20, 25), (24, 25), 'PYRO1_OUT', pcbnew.B_Cu)
        self.assertEqual(gate.region_issues(self.board)[0], [])
        with patch.object(gate, 'BARREL_GND_HAZARD', frozenset({'ACT_GATE', 'ACT_DRV'})):
            issues = gate.region_issues(self.board)[0]
        self.assertTrue(any('PYRO1_OUT' in i and 'no In2 copper' in i for i in issues), issues)
        self.track((18, 25.6), (22, 25.6), 'SPI1_SCK', pcbnew.B_Cu)               # a fast net across the void
        issues = gate.region_issues(self.board)[0]
        self.assertTrue(any('SPI1_SCK' in i and 'no In2 copper' in i for i in issues), issues)
        self.assertFalse(any('PYRO1_OUT' in i for i in issues), issues)
        # K-reference with no reference copper anywhere: PYRO1_OUT passes within 1.221 mm of its barrel only
        for item in [x for x in self.board.GetTracks() if x.GetNetname() == 'SPI1_SCK']:
            self.board.Remove(item)
        out = self.track((40, 5), (41.0, 5), 'PYRO1_OUT', pcbnew.F_Cu)
        out_via = pcbnew.PCB_VIA(self.board); out_via.SetPosition(self.P(40, 5)); out_via.SetWidth(pcbnew.FromMM(0.5))
        out_via.SetDrill(pcbnew.FromMM(0.3)); out_via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        out_via.SetNet(self.board.FindNet('PYRO1_OUT')); self.board.Add(out_via)
        empty = {pcbnew.F_Cu: pcbnew.SHAPE_POLY_SET(), pcbnew.B_Cu: pcbnew.SHAPE_POLY_SET()}
        for item in [x for x in self.board.GetTracks() if x.GetNetname() == 'PYRO1_OUT' and x.GetLayer() == pcbnew.B_Cu]:
            self.board.Remove(item)
        with patch.object(cr, 'fills', return_value=empty):
            self.assertFalse(any('PYRO1_OUT' in k for k in gate.references(self.board)[1].get('by_net_layer', {})))
            out.SetEnd(self.P(42.0, 5))
            self.assertIn('PYRO1_OUT F.Cu', gate.references(self.board)[1]['by_net_layer'])

    def test_k_region_margin_pad_and_chain(self):
        """R5-RTE-01 / -02 / -06: edges pushed 0.1 mm out, SMD pads sampled, connected chains one plane in total."""
        self.plane('GND', 10, 10, 30, 40)
        t = self.track((12, 39.95), (28, 39.95), 'PYRO1_GATE', pcbnew.B_Cu)       # edge 0.1 inside the plane edge
        self.assertTrue(gate.region_issues(self.board)[0])                       # edge + 0.1 margin is off the plane
        self.board.Remove(t)
        self.track((12, 39.5), (28, 39.5), 'PYRO1_GATE', pcbnew.B_Cu)
        self.assertEqual(gate.region_issues(self.board)[0], [])
        # a B.Cu SMD pad straddling the seam of two planes
        self.plane('3V3', 30.05, 10, 45, 40)
        f = self.part('R991', [('1', 0, 0, 'PYRO1_GATE')], at=(30.025, 20))
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
        pad = self.r134.FindPadByNumber('2')                                     # (5, 20), RAW_ACT
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
        self.track((12, 39.85), (28, 39.85), 'PYRO1_GATE', pcbnew.B_Cu)               # copper edge at 39.95
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
        self.track((12, 30), (38, 30), 'PYRO1_GATE', pcbnew.B_Cu)
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
        self.r134.FindPadByNumber('2').SetNet(self.board.FindNet('SPI1_SCK'))
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
        self.r134.FindPadByNumber('2').SetNet(self.board.FindNet('SPI1_SCK'))
        self.assertTrue(gate.OwnPadVoids(self.board, fill(0)).exempt('SPI1_SCK', 5, 20.3))
        for width in (0.03, 0.02):
            with self.subTest(width=width):
                self.assertFalse(gate.OwnPadVoids(self.board, fill(width)).exempt('SPI1_SCK', 5, 20.3))

    def test_r26_own_pad_void_with_its_gnd_partner_via(self):
        """D-R26-01 (R26-TRI-09): a GND via within 1.5 mm of a through-hole pad (its D-R19-15 partner) opens an In2
        antipad that cannot stay apart from the pad's own void (J440.3 / J440.4: void 1.2 mm, antipad 0.40 mm, 1.5 mm
        apart). The merged void stays exempt inside the pad disc and the partner's antipad disc. The same hole without
        the via, with a 3V3 via there, with the GND via 1.6 mm away, or with a slot out of the partner's disc is not."""
        def poly(*pts):
            ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
            for x, y in pts:
                ps.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
            return ps

        def disc(cx, cy, r):
            return poly(*[(cx + r * math.cos(k * math.pi / 16), cy + r * math.sin(k * math.pi / 16)) for k in range(32)])

        def fill(*holes):
            ps = poly(*self.box(0, 10, 46, 40))
            for h in holes:
                ps.BooleanSubtract(h)
            return {'3V3': ps}

        def exempt(*holes):
            return gate.OwnPadVoids(self.board, fill(*holes)).exempt('SPI1_SCK', 5, 20.3)
        pad = self.r134.FindPadByNumber('2')                                         # the pad at (5, 20)
        pad.SetNet(self.board.FindNet('SPI1_SCK'))
        pad.SetSize(self.P(2.4, 2.4))           # no zone clearance on this board: the disc is 1.2 + 0.05, the board's 1.25
        void, antipad = disc(5, 20, 1.2), disc(5, 18.5, 0.4)
        self.assertTrue(exempt(void))
        self.assertFalse(exempt(void, antipad))                                       # no via: a hole leaving the disc
        v = self.via(5, 18.5, 'GND', d=0.5)
        self.assertTrue(exempt(void, antipad))                                        # its GND partner
        v.SetNet(self.board.FindNet('3V3'))
        self.assertFalse(exempt(void, antipad))
        v.SetNet(self.board.FindNet('GND')); v.SetPosition(self.P(5, 18.4))
        self.assertFalse(exempt(void, disc(5, 18.4, 0.45)))                           # 1.6 mm: no partner
        v.SetPosition(self.P(5, 18.5))
        self.assertFalse(exempt(void, antipad, poly(*self.box(4.98, 17.0, 5.02, 18.5))))   # a slot out of its disc

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

    def hole_table(self, hole_pts, vias):
        ps = pcbnew.SHAPE_POLY_SET()
        ps.NewOutline()
        for x, y in ((-5, -5), (30, -5), (30, 10), (-5, 10)):
            ps.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        h = ps.NewHole()
        for x, y in hole_pts:
            ps.Append(pcbnew.FromMM(x), pcbnew.FromMM(y), -1, h)
        return gate.fill_hole_table({'GND': ps}, [(x, y, n, 0.3) for x, y, n in vias])

    def test_fill_hole_slot_between_vias_is_no_via_hole(self):
        """R7-GATE-02: a 10 mm slot whose end vertices sit by two vias is not covered by the via discs."""
        slot = [(-0.4, -0.4), (10.4, -0.4), (10.4, 0.4), (-0.4, 0.4)]
        self.assertEqual(self.hole_table(slot, [(0, 0, 'A'), (10, 0, 'B')]), [])
        # the same outline with vias along it (merged antipads) is a via hole
        merged = [(-0.4, -0.4), (2.0, -0.4), (2.0, 0.4), (-0.4, 0.4)]
        self.assertEqual(len(self.hole_table(merged, [(0, 0, 'A'), (0.8, 0, 'B'), (1.6, 0, 'C')])), 1)
        self.assertEqual(len(self.hole_table([(-0.4, -0.4), (0.4, -0.4), (0.4, 0.4), (-0.4, 0.4)], [(0, 0, 'A')])), 1)

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
    MORE = ('PYRO1_OUT', 'PYRO1_GATE', '3V3', 'USB_DP', 'SPI1_SCK', 'CAM_PWR_EN', 'CAM_UART_OE', 'BUZZ_DRV',
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

    def test_fast_uart_layer_change_needs_gnd_via(self):
        import route_check as rc
        rc.set_profile('r10')
        self.hop('GPS_TX_MCU')
        self.assertEqual(len([d for d in rc.scan(self.board) if d['cat'] == 'critical_via_no_gnd']), 2)
        self.via(23, 31.2, 'GND'); self.via(27, 31.2, 'GND')
        self.assertFalse([d for d in rc.scan(self.board) if d['cat'] == 'critical_via_no_gnd'])

    def test_needless_hop(self):
        import route_check as rc
        rc.set_profile('r10')
        self.hop('CAM_PWR_EN')
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

    # --- R3-SAF-01 pyro barrels ----------------------------------------------------------------------
    def test_s8_inner_copper_near_pyro_barrel(self):
        v = self.via(30, 30, 'RAW_ACT', drill=0.3)
        v.Padstack().SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_EXCEPT_START_AND_END)  # as the board
        self.assertEqual(gate.s8(self.ctx())[0], [])
        t = self.track((30.75, 28), (30.75, 32), '3V3', pcbnew.In2_Cu)    # barrel wall 0.15 + 0.5 gap + 0.1 half
        found = gate.s8(self.ctx())[0]
        self.assertTrue(any('3V3 copper on In2.Cu is 0.500 mm' in i for i in found), found)
        t.SetNet(self.board.FindNet('GND'))
        self.assertEqual(gate.s8(self.ctx())[0], [])
        t.SetNet(self.board.FindNet('3V3')); t.SetStart(self.P(31.3, 28)); t.SetEnd(self.P(31.3, 32))   # 1.05 mm
        self.assertEqual(gate.s8(self.ctx())[0], [])
        # D-R20-05: an unconnected inner ring (r 0.3 mm) the barrel keeps sits 0.9 mm from the same track and fails.
        v.Padstack().SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL)
        found = gate.s8(self.ctx())[0]
        self.assertTrue(any('3V3 copper on In2.Cu is 0.900 mm from the via (30.000, 30.000) inner ring' in i
                            for i in found), found)
        v.Padstack().SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_EXCEPT_START_AND_END)
        self.part('X3', [('1', 0, 0, 'PYRO1_IGN')], at=(10, 50), tht=True)     # a plated pad hole counts too
        self.track((10.6, 48), (10.6, 52), 'SERVO1_OUT', pcbnew.In1_Cu)
        self.assertTrue(any('X3.1 hole' in i and 'In1.Cu' in i for i in gate.s8(self.ctx())[0]))

    def test_s8_load_switch_gate_and_enable_barrels(self):
        """R18-SAF-01 / R18-GATE-01: the round-17 geometry (an ACT_GATE barrel 0.251 mm from In1 GND) fails, because GND
        on a P-FET gate turns Q120 / Q121 on; the same GND beside a BAT_ENABLE barrel passes (it holds U9 off) while
        RAW_PROTECTED there fails; 1.1 mm clears both."""
        self.assertTrue({'ACT_GATE', 'ACT_DRV', 'BAT_ENABLE', 'BAT_SW_RETURN'} <= set(gate.BARREL_NETS))
        self.assertTrue({'ACT_GATE', 'ACT_DRV'} <= gate.BARREL_GND_HAZARD)
        self.via(30, 30, 'ACT_GATE', d=0.5, drill=0.3)
        t = self.track((30.501, 28), (30.501, 32), 'GND', pcbnew.In1_Cu)     # wall 0.15, track edge 0.401: 0.251 mm
        found = gate.s8(self.ctx())[0]
        self.assertTrue(any('GND copper on In1.Cu is 0.251 mm' in i and 'ACT_GATE' in i for i in found), found)
        t.SetStart(self.P(31.351, 28)); t.SetEnd(self.P(31.351, 32))      # 1.101 mm
        self.assertEqual(gate.s8(self.ctx())[0], [])
        self.via(10, 60, 'BAT_ENABLE', d=0.5, drill=0.3)
        e = self.track((10.501, 58), (10.501, 62), 'GND', pcbnew.In1_Cu)
        self.assertEqual(gate.s8(self.ctx())[0], [])                       # GND is fail-safe for the enable chain
        e.SetNet(self.board.FindNet('RAW_PROTECTED')); e.SetLayer(pcbnew.In2_Cu)
        self.assertTrue(any('RAW_PROTECTED copper on In2.Cu is 0.251 mm' in i and 'BAT_ENABLE' in i
                            for i in gate.s8(self.ctx())[0]))

    def test_k_plane_split_fill_needs_two_links(self):
        """R18-RTE-01 / R18-PWR-01 (D-R18-06): a power fill in two pieces fails with one >= 0.5 mm link, passes with
        two, and a 0.3 mm link does not count; one piece always passes."""
        def zone(x0, x1):
            z = pcbnew.ZONE(self.board); z.SetLayer(pcbnew.In2_Cu); z.SetNet(self.board.FindNet('3V3'))
            o = z.Outline(); o.NewOutline()
            for x, y in ((x0, 0), (x1, 0), (x1, 10), (x0, 10)):
                o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
            fill = pcbnew.SHAPE_POLY_SET(); fill.NewOutline()
            for x, y in ((x0, 0), (x1, 0), (x1, 10), (x0, 10)):
                fill.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
            z.SetFilledPolysList(pcbnew.In2_Cu, fill); z.SetIsFilled(True); self.board.Add(z)
            return z
        zone(0.5, 10)
        self.assertEqual(gate.plane_issues(self.board)[0], [])
        zone(12, 20)
        self.via(5, 5, '3V3'); self.via(15, 5, '3V3')
        self.track((5, 5), (15, 5), '3V3', pcbnew.F_Cu, width=0.5)
        found = gate.plane_issues(self.board)[0]
        self.assertTrue(any('3V3 on In2.Cu fills as 2 pieces' in i and '1 link(s)' in i for i in found), found)
        self.via(5, 7, '3V3'); self.via(15, 7, '3V3')
        thin = self.track((5, 7), (15, 7), '3V3', pcbnew.B_Cu, width=0.3)
        self.assertTrue(gate.plane_issues(self.board)[0])
        thin.SetWidth(pcbnew.FromMM(0.5))
        self.assertEqual(gate.plane_issues(self.board)[0], [])

    def test_s8_plated_pad_and_raw_act_barrel(self):
        """R6-SAF-02: a foreign plated pad's inner copper counts; RAW_ACT's barrel is a barrel net."""
        self.assertIn('RAW_ACT', gate.BARREL_NETS)
        self.part('X5', [('1', 0, 0, 'RAW_ACT')], at=(10, 50), tht=True)
        self.assertEqual(gate.s8(self.ctx())[0], [])
        self.part('X6', [('1', 0, 0, 'SERVO1_OUT')], at=(11.9, 50), tht=True)      # pad edge 0.4 mm from the barrel wall
        self.assertTrue(any('SERVO1_OUT copper' in i and 'X5.1' in i for i in gate.s8(self.ctx())[0]))
        self.part('X7', [('1', 0, 0, 'RAW_ACT')], at=(30, 60), tht=True)
        self.track((30.9, 58), (30.9, 62), '3V3', pcbnew.In2_Cu)                    # 0.25 mm from the RAW_ACT hole wall
        self.assertTrue(any('X7.1 hole' in i for i in gate.s8(self.ctx())[0]))

    # --- R3-GATE-02 copper text, footprint zones, multi-net parts -------------------------------------------------
    def test_s1_copper_text_bridge(self):
        t = pcbnew.PCB_TEXT(self.board); t.SetText('I'); t.SetLayer(pcbnew.B_Cu); t.SetTextAngleDegrees(90)
        t.SetTextSize(self.P(4.5, 4.5)); t.SetTextThickness(pcbnew.FromMM(0.6)); t.SetPosition(self.P(6.75, 20))
        self.board.Add(t)
        self.assertTrue(any('bypassed' in i and 'copper text' in i for i in gate.s1(self.ctx())[0]))
        self.board.Remove(t)
        f = self.part('X4', [], at=(6.75, 20))
        ft = pcbnew.PCB_TEXT(f); ft.SetText('I'); ft.SetLayer(pcbnew.F_Cu); ft.SetTextAngleDegrees(90)
        ft.SetTextSize(self.P(4.5, 4.5)); ft.SetTextThickness(pcbnew.FromMM(0.6)); ft.SetPosition(self.P(6.75, 20))
        f.Add(ft)
        self.assertTrue(any('bypassed' in i and 'X4 copper text' in i for i in gate.s1(self.ctx())[0]))

    def test_s1_multi_net_part(self):
        nets = ['RAW_ACT', 'GND', 'BAT_IN', 'ACT_GATE', 'GPS_TX_MCU', 'SERVO1_OUT']
        f = self.part('U99', [(str(k), k, 0, n) for k, n in enumerate(nets, 1)], at=(30, 70))
        # R4-SAF-02: a part with more than four nets and a pad on RAW_ACT beside a supply pad is flagged too
        self.assertTrue(any('U99 has pads on the armed / RAW_ACT side net RAW_ACT' in i for i in gate.s1(self.ctx())[0]))
        f.FindPadByNumber('6').SetNet(self.board.FindNet('PYRO1_IGN'))
        self.assertTrue(any('U99 has pads on RAW_ACT' in i for i in gate.s1(self.ctx())[0]))

    # --- R3-GATE-07 fire-loop width -------------------------------------------------------------------------------
    def test_s9_fire_path_and_sense_tap(self):
        self.board.Remove(self.r134); self.board.Remove(self.r132)
        self.part('Q121', [('9', 0, 0, 'RAW_ACT')], at=(5, 20))
        self.part('R134', [('1', 0, 0, 'PYRO1_IGN'), ('2', 4, 0, 'RAW_ACT')], at=(20, 20))
        self.part('R132', [('1', 0, 0, 'RAW_ACT'), ('2', 1, 0, 'GND')], at=(14, 26))
        main = [self.track((5, 20), (10, 20), 'RAW_ACT', width=1.0), self.track((10, 20), (24, 20), 'RAW_ACT', width=1.0)]
        self.track((10, 20), (14, 26), 'RAW_ACT', width=0.2)              # sense tap is pruned from the fire path
        segs, joined, _ = gate.fire_path(self.board, 'RAW_ACT', gate.FIRE_TERMINALS['RAW_ACT'])
        self.assertTrue(joined)
        self.assertEqual(sorted(round(pcbnew.ToMM(t.GetWidth()), 2) for t in segs), [1.0, 1.0])
        self.assertFalse([i for i in gate.s9(self.ctx())[0] if 'RAW_ACT fire-path' in i])
        main[1].SetWidth(pcbnew.FromMM(0.4))
        self.assertTrue([i for i in gate.s9(self.ctx())[0] if 'RAW_ACT fire-path track 0.400 mm' in i])
        main[1].SetWidth(pcbnew.FromMM(0.5))
        self.assertFalse([i for i in gate.s9(self.ctx())[0] if 'RAW_ACT fire-path' in i])  # AUD-6 boundary.

    def test_aud6_does_not_narrow_the_continuous_battery_feed(self):
        self.part('J1', [('1', 0, 0, 'BAT_IN')], at=(5, 30))
        self.part('Q120', [('9', 0, 0, 'BAT_IN')], at=(24, 30))
        self.track((5, 30), (10, 30), 'BAT_IN', width=1.)
        self.track((10, 30), (24, 30), 'BAT_IN', width=.5)
        with patch.object(gate, 'FIRE_TERMINALS', {'BAT_IN': ({'J1': ('1',)}, {'Q120': ('9',)})}):
            self.assertTrue(any('BAT_IN fire-path track 0.500 mm' in i for i in gate.s9(self.ctx(), narrow=[])[0]))

    def test_s9_small_pad_anchor_does_not_exempt_a_current_path(self):
        self.board.Remove(self.r134); self.board.Remove(self.r132)
        for net, left, right, minimum, y in (('RAW_ACT', 'Q121', 'R134', .5, 20),
                                            ('BAT_IN', 'J1', 'Q120', 1., 30)):
            a = self.part(left, [('9' if left == 'Q121' else '1', 0, 0, net)], at=(5, y))
            b = self.part(right, [('2' if right == 'R134' else '9', 0, 0, net)], at=(24, y))
            for f in (a, b):
                for p in f.Pads():
                    p.SetSize(self.P(.43, .43))
            track = self.track((5, y), (24, y), net, width=minimum)
            terminals = {net: gate.FIRE_TERMINALS[net]}
            with patch.object(gate, 'FIRE_TERMINALS', terminals):
                self.assertEqual(gate.s9(self.ctx(), narrow=[])[0], [])
                track.SetWidth(pcbnew.FromMM(.43))
                self.assertTrue(any(f'{net} fire-path track 0.430 mm' in i
                                    for i in gate.s9(self.ctx(), narrow=[])[0]))

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


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class Audit2(SyntheticBase):
    def setUp(self):
        super().setUp()
        import route_check as rc
        rc.set_profile('r10'); self.addCleanup(rc.set_profile, 'r8')

    def test_only_named_resistor_dead_ends_get_the_015_width_and_no_length_cap(self):
        self.part('J1', [('1', 0, 0, 'BAT_IN')], at=(5, 10))
        self.part('Q120', [('9', 0, 0, 'BAT_IN')], at=(25, 10))
        self.part('R80', [('1', 0, 0, 'BAT_IN'), ('2', 1, 0, 'BAT_SW_SOURCE')], at=(10, 25))
        self.track((5, 10), (10, 10), 'BAT_IN', width=1.)
        feed = self.track((10, 10), (25, 10), 'BAT_IN', width=1.)
        tap = self.track((10, 25), (10, 10), 'BAT_IN', width=.15)
        self.assertEqual(gate.k_width(self.board)[0], [])
        qualified, evidence = gate.resistor_tap_tracks(self.board)
        self.assertIn(tap.m_Uuid.AsString(), qualified)
        self.assertNotIn(feed.m_Uuid.AsString(), qualified)
        self.assertEqual(evidence['R80.1']['length_mm'], 15.)
        feed.SetWidth(pcbnew.FromMM(.15))
        self.assertTrue(any('minimum 0.3 mm' in i for i in gate.k_width(self.board)[0]))
        feed.SetWidth(pcbnew.FromMM(1.)); tap.SetWidth(pcbnew.FromMM(.14))
        self.assertTrue(any('minimum 0.15 mm' in i for i in gate.k_width(self.board)[0]))

    def test_a_tap_exemption_does_not_continue_through_a_capacitor_feed(self):
        self.part('J1', [('1', 0, 0, 'BAT_IN')], at=(5, 10))
        self.part('Q120', [('9', 0, 0, 'BAT_IN')], at=(25, 10))
        self.part('R80', [('1', 0, 0, 'BAT_IN'), ('2', 1, 0, 'BAT_SW_SOURCE')], at=(10, 25))
        self.part('C80', [('1', 0, 0, 'BAT_IN'), ('2', 1, 0, 'GND')], at=(10, 20))
        self.track((5, 10), (10, 10), 'BAT_IN', width=1.)
        self.track((10, 10), (25, 10), 'BAT_IN', width=1.)
        tap = self.track((10, 25), (10, 20), 'BAT_IN', width=.15)
        cap_feed = self.track((10, 20), (10, 10), 'BAT_IN', width=.15)
        qualified, _ = gate.resistor_tap_tracks(self.board)
        self.assertIn(tap.m_Uuid.AsString(), qualified)
        self.assertNotIn(cap_feed.m_Uuid.AsString(), qualified)
        self.assertTrue(gate.k_width(self.board)[0])
        cap_feed.SetWidth(pcbnew.FromMM(.5))
        self.assertEqual(gate.k_width(self.board)[0], [])

    def test_source_path_05_passes_below_floor_fails_and_battery_stays_10(self):
        self.part('Q120', [('1', 0, 0, 'ACT_FET_S')], at=(5, 30))
        self.part('Q121', [('1', 0, 0, 'ACT_FET_S')], at=(25, 30))
        track = self.track((5, 30), (25, 30), 'ACT_FET_S', width=.5)
        terminals = {'ACT_FET_S': ({'Q120': ('1',)}, {'Q121': ('1',)})}
        with patch.object(gate, 'FIRE_TERMINALS', terminals):
            self.assertEqual(gate.s9(self.ctx(), narrow=[])[0], [])
            track.SetWidth(pcbnew.FromMM(.49))
            self.assertTrue(any('minimum 0.5 mm' in i for i in gate.s9(self.ctx(), narrow=[])[0]))
        self.assertNotIn('BAT_IN', gate.FIRE_ONLY)
        self.assertEqual(len(gate.FIRE_NARROW), 7)

    def test_in1_only_ground_and_in2_only_power_are_kept(self):
        self.track((10, 10), (20, 10), 'GND', pcbnew.In1_Cu)
        self.track((10, 12), (20, 12), '3V3', pcbnew.In2_Cu)
        self.assertEqual(gate.k_inner_signal(self.ctx())[0], [])
        bad = self.track((10, 14), (20, 14), '3V3', pcbnew.In1_Cu)
        self.assertTrue(any('In1.Cu track of 3V3' in i for i in gate.k_inner_signal(self.ctx())[0]))
        bad.SetLayer(pcbnew.In2_Cu); bad.SetNet(self.board.FindNet('GPS_TX_MCU'))
        self.assertTrue(any('In2.Cu track of GPS_TX_MCU' in i for i in gate.k_inner_signal(self.ctx())[0]))

    def test_clearance_overrides_cannot_lower_probe_debug_or_board_floors(self):
        import check_r9 as r9
        for ref, minimum in (('J2', .508), ('TP988', 1.), ('X988', .15)):
            with self.subTest(ref=ref):
                f = self.part(ref, [('1', 0, 0, 'GND')], at=(35, 70))
                p = f.FindPadByNumber('1')
                f.SetLocalClearance(pcbnew.FromMM(minimum)); p.SetLocalClearance(pcbnew.FromMM(minimum))
                self.assertEqual(gate.lc1(self.board)[0], [])
                self.assertTrue(r9.lc1(self.board)[0])  # Legacy R9 still rejects every local override.
                f.SetLocalClearance(pcbnew.FromMM(minimum - .01))
                self.assertTrue(any(ref in i for i in gate.lc1(self.board)[0]))
                f.SetLocalClearance(pcbnew.FromMM(minimum)); p.SetLocalClearance(pcbnew.FromMM(minimum - .01))
                self.assertTrue(any(ref + '.1' in i for i in gate.lc1(self.board)[0]))
                p.SetLocalClearance(pcbnew.FromMM(minimum + .1))
                self.assertEqual(gate.lc1(self.board)[0], [])

    def test_direct_adc_inputs_are_the_only_named_mcu_supply_ties(self):
        u1 = self.part('U1', [('15', 0, 0, 'PYRO1_CONT'), ('33', 1, 0, 'ARM1_SENSE'),
                              ('50', 2, 0, '3V3'), ('51', 3, 0, 'GND')], at=(30, 70))
        self.assertFalse([r for r in gate.supply_ties(self.board) if r[0] == 'U1'])
        u1.FindPadByNumber('50').SetNet(self.board.FindNet('ARM1_SENSE'))
        self.assertTrue(any('ARM1_SENSE' in i for i in gate.mcu_side_issues(self.board)))
        u1.FindPadByNumber('50').SetNet(self.board.FindNet('RAW_ACT'))
        self.assertTrue(any(r[0] == 'U1' and r[1] == 'RAW_ACT' for r in gate.supply_ties(self.board)))

    def test_pin_table_is_complete_and_optional_plate_has_no_release_threshold(self):
        import csv
        import io
        import tempfile
        with gate.R10_PIN_TABLE.open() as source:
            rows = list(csv.DictReader(source, delimiter='\t'))
        self.assertEqual(len(gate.mcu_pin_table()), 100)
        for mutant in (rows[:-1], rows[:-1] + [dict(rows[0])], [dict(r, r10_net='') if i == 0 else r
                                                               for i, r in enumerate(rows)]):
            out = io.StringIO(); writer = csv.DictWriter(out, fieldnames=list(rows[0]), delimiter='\t')
            writer.writeheader(); writer.writerows(mutant)
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.tsv') as path:
                path.write(out.getvalue()); path.flush()
                with self.assertRaises(ValueError):
                    gate.mcu_pin_table(path.name)
        self.assertEqual(gate.m2(Mock(plate=None))[0], [])
        self.assertEqual(gate.m2(Mock(plate={'f1': 1, 'board_sha256': 'stale'}))[0], [])


@unittest.skipUnless(pcbnew, 'KiCad Python required')
@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R18Gate(SyntheticBase):
    """Round 18 gate hardening on small synthetic boards: K-power's path, via and return rules, the word legends."""
    def setUp(self):
        super().setUp()
        self.board.Add(pcbnew.NETINFO_ITEM(self.board, 'BAT_FAULT_N'))

    def fill(self, net, layer, x0, y0, x1, y1):
        z = pcbnew.ZONE(self.board); z.SetLayer(layer); z.SetNet(self.board.FindNet(net))
        poly = pcbnew.SHAPE_POLY_SET(); poly.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            poly.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        z.Outline().NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            z.Outline().Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        z.SetFilledPolysList(layer, poly); z.SetIsFilled(True); self.board.Add(z)
        return z

    def out_path(self):
        """U9.6 -> 0.7 mm run -> two In2 RAW_PROTECTED vias, and an unrelated RAW_PROTECTED cluster elsewhere."""
        self.part('U9', [('6', 0, 0, 'RAW_PROTECTED')], at=(20, 60))
        run = self.track((20, 60), (25, 60), 'RAW_PROTECTED', width=0.7)
        link = self.track((25, 60), (26, 60), 'RAW_PROTECTED', width=0.7)
        vias = [self.via(25, 60, 'RAW_PROTECTED', d=0.5), self.via(26, 60, 'RAW_PROTECTED', d=0.5)]
        self.via(35, 75, 'RAW_PROTECTED', d=0.5)
        self.track((35, 75), (38, 75), 'RAW_PROTECTED', width=0.2)                    # another region's thin tap
        self.fill('RAW_PROTECTED', pcbnew.In2_Cu, 15, 55, 40, 80)
        return run, link, vias

    SPEC = dict(name='U9 OUT', net='RAW_PROTECTED', start={'U9': ('6',)}, end=None, through={}, floor=0.7,
                vias=dict(count=2, drill=0.3, pad=0.5, plane='In2.Cu'))

    def test_out_path_ends_at_its_own_plane_vias(self):
        run, link, vias = self.out_path()
        segs, joined, on_vias, pads = gate.path_graph(self.board, 'RAW_PROTECTED', {'U9': ('6',)})
        self.assertTrue(joined)
        self.assertEqual(sorted(t.m_Uuid.AsString() for t in segs), sorted(t.m_Uuid.AsString() for t in (run, link)))
        self.assertEqual(len(on_vias), 2)                            # the unrelated region's via is not on the path
        self.assertEqual(gate.power_paths(self.board, paths=(self.SPEC,), narrow=[])[0], [])
        run.SetWidth(pcbnew.FromMM(0.31))                            # s03: the OUT run necked to 0.31 mm
        found = gate.power_paths(self.board, paths=(self.SPEC,), narrow=[])[0]
        self.assertTrue(any('U9 OUT: RAW_PROTECTED track 0.310 mm wide' in i for i in found), found)

    def test_out_vias_count_size_and_plane(self):
        run, link, vias = self.out_path()
        self.board.Remove(vias[1]); self.board.Remove(link)          # s11: one transition left
        found = gate.power_paths(self.board, paths=(self.SPEC,), narrow=[])[0]
        self.assertTrue(any('1 via(s) on the path; at least 2' in i for i in found), found)
        self.board.Add(vias[1]); self.board.Add(link)
        vias[0].SetDrill(pcbnew.FromMM(0.2))
        found = gate.power_paths(self.board, paths=(self.SPEC,), narrow=[])[0]
        self.assertTrue(any('via (25.000, 60.000) 0.500 / 0.200 mm' in i for i in found), found)
        vias[0].SetDrill(pcbnew.FromMM(0.3))
        self.assertTrue(gate.plane_via(self.board, vias[0], pcbnew.In2_Cu, 'RAW_PROTECTED'))
        self.board.Remove(next(z for z in self.board.Zones()))       # no In2 fill: the vias reach no plane
        found = gate.power_paths(self.board, paths=(self.SPEC,), narrow=[])[0]
        self.assertTrue(any('is not joined to the In2.Cu RAW_PROTECTED fill' in i for i in found), found)

    def test_named_narrow_entry_matches_exactly_and_goes_stale(self):
        run, link, vias = self.out_path()
        link.SetWidth(pcbnew.FromMM(0.4))
        entry = [('RAW_PROTECTED', 'F.Cu', 0.4, 1.0, (25.0, 60.0, 26.0, 60.0), 'via link')]
        self.assertEqual(gate.power_paths(self.board, paths=(self.SPEC,), narrow=entry)[0], [])
        link.SetWidth(pcbnew.FromMM(0.35))
        found = gate.power_paths(self.board, paths=(self.SPEC,), narrow=entry)[0]
        self.assertTrue(any('RAW_PROTECTED track 0.350 mm' in i for i in found), found)
        self.assertTrue(any('stale POWER_NARROW' in i for i in found), found)

    def test_in_path_through_its_bypass_capacitor_and_feed_via(self):
        spec = dict(name='U9 IN', net='BAT_IN', start={'J1': ('1',)}, end={'U9': ('5',)}, through={'C88': ('1',)},
                    floor=1.0, vias=dict(count=1, drill=0.5, pad=1.0, plane=None))
        self.part('J1', [('1', 0, 0, 'BAT_IN')], at=(5, 70), tht=True)
        for ref, x in (('C88', 20), ('U9', 25)):                     # bottom-side parts, as on the R10 board
            self.part(ref, [('1' if ref == 'C88' else '5', 0, 0, 'BAT_IN')], at=(x, 70)).SetLayerAndFlip(pcbnew.B_Cu)
        self.track((5, 70), (12, 70), 'BAT_IN', width=1.0)
        via = self.via(12, 70, 'BAT_IN', d=1.0, drill=0.5)
        self.track((12, 70), (20, 70), 'BAT_IN', pcbnew.B_Cu, width=1.0)
        bypass = self.track((20, 70), (25, 70), 'BAT_IN', pcbnew.B_Cu, width=1.0)
        self.assertEqual(gate.power_paths(self.board, paths=(spec,), narrow=[])[0], [])
        via.SetWidth(pcbnew.FromMM(0.5)); via.SetDrill(pcbnew.FromMM(0.3))       # s11b: the feed via shrunk
        found = gate.power_paths(self.board, paths=(spec,), narrow=[])[0]
        self.assertTrue(any('U9 IN: via (12.000, 70.000) 0.500 / 0.300 mm' in i for i in found), found)
        via.SetWidth(pcbnew.FromMM(1.0)); via.SetDrill(pcbnew.FromMM(0.5))
        self.board.Remove(bypass)                                    # a direct feed that skips C88
        self.track((12, 70), (25, 72), 'BAT_IN', pcbnew.B_Cu, width=1.0)
        self.track((25, 72), (25, 70), 'BAT_IN', pcbnew.B_Cu, width=1.0)
        found = gate.power_paths(self.board, paths=(spec,), narrow=[])[0]
        self.assertTrue(any('does not pass C88.1' in i for i in found), found)

    def q124(self):
        self.part('Q124', [('1', 0, 1.3, 'GND'), ('2', 0, 0.65, 'GND'), ('3', 0, 0, 'GND'), ('4', 0, -0.65, 'PYRO1_GATE')],
                  at=(15, 50))
        bar = self.track((15, 50), (15, 51.3), 'GND', width=0.3)
        stubs = [self.track((15, 50.65), (15.55, 50.65), 'GND', width=0.3),
                 self.track((15, 51.3), (15.55, 51.3), 'GND', width=0.3)]
        vias = [self.via(15.55, 50.65, 'GND', d=0.5), self.via(15.55, 51.3, 'GND', d=0.5)]
        self.fill('GND', pcbnew.In1_Cu, 10, 45, 20, 55)
        return bar, stubs, vias

    def test_fire_return_width_vias_and_every_source_pad(self):
        bar, stubs, vias = self.q124()
        self.assertEqual(gate.fire_return(self.board)[0], [])
        for t in [bar] + stubs:                                      # s26: the source bar and stubs at 0.15 mm
            t.SetWidth(pcbnew.FromMM(0.15))
        found = gate.fire_return(self.board)[0]
        self.assertEqual(sum('Q124 fire return: GND track 0.150 mm' in i for i in found), 3, found)
        for t in [bar] + stubs:
            t.SetWidth(pcbnew.FromMM(0.3))
        self.board.Remove(vias[0])
        found = gate.fire_return(self.board)[0]
        self.assertTrue(any('1 via(s) on the path; at least 2' in i for i in found), found)
        self.board.Add(vias[0]); self.board.Remove(bar)
        found = gate.fire_return(self.board)[0]
        self.assertTrue(any('source pad Q124.3 is on no return track' in i for i in found), found)

    def word(self, text, x, y, layer=None):
        t = pcbnew.PCB_TEXT(self.board); t.SetText(text); t.SetLayer(pcbnew.F_SilkS if layer is None else layer)
        t.SetTextSize(self.P(1, 1)); t.SetTextThickness(pcbnew.FromMM(0.15)); t.SetPosition(self.P(x, y))
        self.board.Add(t)
        return t

    def terminal(self, ref, y):
        """A two-way terminal whose courtyard spans y - 2 .. y + 6 at x 3 .. 11."""
        f = self.part(ref, [('1', 0, 0, 'BAT_IN'), ('2', 0, 3.5, 'GND')], at=(7, y), tht=True)
        crt = pcbnew.PCB_SHAPE(f); crt.SetShape(pcbnew.SHAPE_T_RECT); crt.SetLayer(pcbnew.F_CrtYd)
        crt.SetStart(self.P(3, y - 2)); crt.SetEnd(self.P(11, y + 6)); crt.SetWidth(pcbnew.FromMM(0.05)); f.Add(crt)
        return f

    def test_word_legends_identity_seam_and_count(self):
        subjects = {'IGN': 'J121', 'BAT': 'J1'}
        self.terminal('J121', 20); self.terminal('J1', 28)          # abutting courtyards (y 18-26 and 26-34)
        ign, bat = self.word('IGN', 7, 17.4), self.word('BAT', 1, 31)
        self.assertEqual(gate.word_legends(self.board, subjects=subjects, seams=[])[0], [])
        ign.SetText('BAT'); bat.SetText('IGN')                       # s16c: the two words exchanged
        found = gate.word_legends(self.board, subjects=subjects, seams=[])[0]
        self.assertTrue(any("J1: word legend 'BAT'" in i and 'from J121' in i for i in found), found)
        self.assertTrue(any("J121: word legend 'IGN'" in i and 'from J1 ' in i for i in found), found)
        ign.SetText('IGN'); bat.SetText('IGN')                       # BAT gone, IGN twice
        found = gate.word_legends(self.board, subjects=subjects, seams=[])[0]
        self.assertTrue(any("'BAT' appears 0 times" in i for i in found), found)
        self.assertTrue(any("'IGN' appears 2 times" in i for i in found), found)
        bat.SetText('BAT'); bat.SetPosition(self.P(1, 26))           # west of the seam: equally near both
        found = gate.word_legends(self.board, subjects=subjects, seams=[])[0]
        self.assertTrue(any("J1: word legend 'BAT'" in i for i in found), found)
        seam = [('BAT', 'J1', 'J121', 'measured seam')]
        self.assertEqual(gate.word_legends(self.board, subjects=subjects, seams=seam)[0], [])
        bat.SetPosition(self.P(1, 31))                               # beside J1 alone: the seam entry is stale
        found = gate.word_legends(self.board, subjects=subjects, seams=seam)[0]
        self.assertEqual([i for i in found if 'stale WORD_SEAMS' in i] and len(found), 1, found)
        bat.SetPosition(self.P(1, 24))                               # beside J121: no seam excuses it
        found = gate.word_legends(self.board, subjects=subjects, seams=seam)[0]
        self.assertTrue(any("J1: word legend 'BAT'" in i and 'from J121' in i for i in found), found)

    def test_word_legend_face_and_subject_map(self):
        # D-R19-06: one word list; r10_post places exactly these words, in this order.
        import r10_post
        self.assertEqual(gate.WORD_LEGENDS_R10['SWITCH'], 'J400')
        self.assertFalse(hasattr(gate, 'WORD_SUBJECTS_R10'))
        self.assertEqual(r10_post.WORDS, tuple((ref, word) for word, ref in gate.WORD_LEGENDS_R10.items()))
        self.assertEqual(list(gate.WORD_LEGENDS_R10)[-1], 'SWITCH')
        self.assertEqual(gate.WORD_SEAMS, [])
        self.terminal('J1', 30)
        sd = self.part('J430', [('1', 0, 0, 'GND')], at=(7, 26))     # a bottom SMD socket under the legend
        sd.SetLayerAndFlip(pcbnew.B_Cu)
        crt = pcbnew.PCB_SHAPE(sd); crt.SetShape(pcbnew.SHAPE_T_RECT); crt.SetLayer(pcbnew.B_CrtYd)
        crt.SetStart(self.P(2, 25)); crt.SetEnd(self.P(12, 27.6)); sd.Add(crt)
        self.word('BAT', 7, 27.4)
        self.assertEqual(gate.word_legends(self.board, subjects={'BAT': 'J1'}, seams=[])[0], [])
        self.word('BAT', 7, 27.4, layer=pcbnew.B_SilkS).SetMirrored(True)
        found = gate.word_legends(self.board, subjects={'BAT': 'J1'}, seams=[])[0]
        self.assertTrue(any("J1: word legend 'BAT'" in i and 'J430' in i for i in found), found)


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R19Gate(SyntheticBase):
    """Round 19 check changes on small synthetic boards: S-8 GND at PYRO1_OUT, K-power's named bridge via, the port
    word span."""
    fill = R18Gate.fill
    word = R18Gate.word
    terminal = R18Gate.terminal

    def test_r19_s8_gnd_is_a_hazard_at_pyro1_out(self):
        """D-R19-01 (R19-SAF-01): In1 GND 0.251 mm from a PYRO1_OUT barrel fails (it bypasses Q124); 1.101 mm passes;
        GND beside a RAW_ACT barrel still passes (it only shorts the bus)."""
        self.assertEqual(gate.BARREL_GND_HAZARD, frozenset({'ACT_GATE', 'ACT_DRV', 'PYRO1_OUT'}))
        self.via(30, 30, 'PYRO1_OUT', d=0.5, drill=0.3)
        t = self.track((30.501, 28), (30.501, 32), 'GND', pcbnew.In1_Cu)     # wall 0.15, track edge 0.401: 0.251 mm
        found = gate.s8(self.ctx())[0]
        self.assertTrue(any('GND copper on In1.Cu is 0.251 mm' in i and 'PYRO1_OUT' in i for i in found), found)
        t.SetLayer(pcbnew.In2_Cu)
        found = gate.s8(self.ctx())[0]
        self.assertTrue(any('GND copper on In2.Cu is 0.251 mm' in i and 'PYRO1_OUT' in i for i in found), found)
        t.SetStart(self.P(31.351, 28)); t.SetEnd(self.P(31.351, 32))      # 1.101 mm
        self.assertEqual(gate.s8(self.ctx())[0], [])
        self.via(10, 70, 'RAW_ACT', d=0.5, drill=0.3)
        self.track((10.501, 68), (10.501, 72), 'GND', pcbnew.In1_Cu)
        self.assertEqual(gate.s8(self.ctx())[0], [])

    def test_r19_named_bridge_via(self):
        """D-R19-09: a named bridge via is size-checked but needs no plane join and does not count; a named bridge that
        is not on the path fails, and so does a count that only the bridge would meet."""
        self.fill('3V3', pcbnew.In2_Cu, 0, 0, 10, 10)
        joined, bridge = self.via(5, 5, '3V3', d=0.5), self.via(20, 5, '3V3', d=0.5)
        spec = dict(count=1, drill=0.3, pad=0.5, plane='In2.Cu', bridges=(((20, 5), 'test bridge'),))
        self.assertEqual(gate.via_issues(self.board, 'X', [joined, bridge], spec, '3V3'), [])
        found = gate.via_issues(self.board, 'X', [joined, bridge], dict(spec, bridges=()), '3V3')
        self.assertTrue(any('via (20.000, 5.000) is not joined to the In2.Cu 3V3 fill' in i for i in found), found)
        found = gate.via_issues(self.board, 'X', [joined], spec, '3V3')
        self.assertTrue(any('named bridge via (20, 5) is not on the path' in i for i in found), found)
        found = gate.via_issues(self.board, 'X', [bridge], spec, '3V3')
        self.assertTrue(any('X: 0 via(s) on the path; at least 1 required' in i for i in found), found)
        bridge.SetWidth(pcbnew.FromMM(0.4))
        found = gate.via_issues(self.board, 'X', [joined, bridge], spec, '3V3')
        self.assertTrue(any('via (20.000, 5.000) 0.400 / 0.300 mm' in i for i in found), found)

    def test_r19_port_words_inside_their_own_span(self):
        """D-R19-06: GPS / RADIO name the two identically pinned port terminals, so each must lie inside its own
        courtyard y-span by WORD_SPAN_MARGIN: the old seam spot fails, a spot well inside passes."""
        subjects = {'GPS': 'J410', 'RADIO': 'J420'}
        self.terminal('J410', 20); self.terminal('J420', 28)         # courtyards y 18-26 and 26-34, x 3-11
        gps, radio = self.word('GPS', 1, 22), self.word('RADIO', 1, 30)
        self.assertEqual(gate.word_legends(self.board, subjects=subjects, seams=[])[0], [])
        radio.SetPosition(self.P(1, 26.3))                           # ink about 25.7-26.9: across the seam
        found = gate.word_legends(self.board, subjects=subjects, seams=[])[0]
        self.assertTrue(any("J420: word legend 'RADIO'" in i and 'inside its courtyard y-span' in i for i in found),
                        found)
        radio.SetPosition(self.P(1, 30)); gps.SetPosition(self.P(1, 18.6))   # GPS 0.1-0.3 mm inside J410's top
        found = gate.word_legends(self.board, subjects=subjects, seams=[])[0]
        self.assertTrue(any("J410: word legend 'GPS'" in i and 'inside its courtyard y-span' in i for i in found),
                        found)
        self.assertEqual(gate.word_legends(self.board, subjects=subjects, seams=[], spans={})[0], [])
        self.assertEqual(gate.WORD_SPAN_R10, {'GPS': 'J410', 'RADIO': 'J420', 'AUX': 'J440'})

    def test_r19_aux_word_inside_j440_span(self):
        """D-R19-14: J440 carries the same pin legends as J410 / J420, so AUX must lie inside its courtyard y-span too."""
        subjects = {'AUX': 'J440'}
        self.terminal('J440', 20)                                    # courtyard y 18-26
        aux = self.word('AUX', 1, 22)
        self.assertEqual(gate.word_legends(self.board, subjects=subjects, seams=[])[0], [])
        aux.SetPosition(self.P(1, 18.3))                             # ink about 17.7-18.9: across the courtyard end
        found = gate.word_legends(self.board, subjects=subjects, seams=[])[0]
        self.assertTrue(any("J440: word legend 'AUX'" in i and 'inside its courtyard y-span' in i for i in found), found)


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class R19GateFix(SyntheticBase):
    """Round 19 gate pass on small synthetic boards: simple-path fire / power copper and the U9 IN via rule
    (R19-GATE-05), IPC floors (R19-GATE-04), word centre margins (R19-GATE-06), the silkscreen allowlist (R19-GATE-07),
    plane necks (R19-GATE-03), pour debris (R19-RTE-01) and MPN values (R19-GATE-02)."""
    fill = R18Gate.fill
    word = R18Gate.word
    terminal = R18Gate.terminal

    def bottom(self, ref, number, net, at):
        f = self.part(ref, [(number, 0, 0, net)], at=at)
        f.SetLayerAndFlip(pcbnew.B_Cu)
        return f

    def side_loop_board(self):
        """J1.1 -> Q120.9 (the fire feed), and a side branch from it to U9.5 through two parallel vias (a loop)."""
        self.part('J1', [('1', 0, 0, 'BAT_IN')], at=(5, 30), tht=True)
        self.part('Q120', [('9', 0, 0, 'BAT_IN')], at=(25, 30))
        self.bottom('U9', '5', 'BAT_IN', (18, 40))
        main = [self.track((5, 30), (10, 30), 'BAT_IN', width=1.0), self.track((10, 30), (25, 30), 'BAT_IN', width=1.0)]
        self.track((10, 30), (10, 40), 'BAT_IN', width=1.0)
        self.via(10, 40, 'BAT_IN', d=1.0, drill=0.5); self.via(12, 40, 'BAT_IN', d=1.0, drill=0.5)
        self.track((10, 40), (12, 40), 'BAT_IN', width=1.0)
        self.track((10, 40), (12, 40), 'BAT_IN', pcbnew.B_Cu, width=1.0)
        self.track((12, 40), (18, 40), 'BAT_IN', pcbnew.B_Cu, width=1.0)
        return main

    def test_simple_paths_drop_a_side_branch_loop(self):
        """R19-GATE-05: leaf pruning kept a loop on a side branch, and the run to it, as fire copper; the block-cut tree
        path keeps only the two main segments, while a loop on a path (the parallel vias towards U9.5) stays."""
        main = self.side_loop_board()
        segs, joined, _ = gate.fire_path(self.board, 'BAT_IN', ({'J1': ('1',)}, {'Q120': ('9',)}))
        self.assertTrue(joined)
        self.assertEqual(sorted(t.m_Uuid.AsString() for t in segs), sorted(t.m_Uuid.AsString() for t in main))
        segs, joined, vias, pads = gate.path_graph(self.board, 'BAT_IN', {'J1': ('1',)}, {'U9': ('5',)})
        self.assertTrue(joined)
        self.assertEqual(len(vias), 2)
        self.assertEqual(len(segs), 5)                             # J1 run, side run, F and B links, B run to U9
        self.assertEqual(gate.simple_path_edges({}, {'a'}, {'b'}), ({}, False))

    def test_u9_in_one_sized_via_and_board_minimum_parallel_vias(self):
        """R19-GATE-05: one IN via of >= 1.0 / 0.5 mm, a parallel one may be 0.5 / 0.3 mm (D-R18-11's wording)."""
        spec = next(p for p in gate.POWER_PATHS if p['name'] == 'U9 IN')['vias']
        big, small = self.via(10, 10, 'BAT_IN', d=1.0, drill=0.5), self.via(12, 10, 'BAT_IN', d=0.6, drill=0.3)
        self.assertEqual(gate.via_issues(self.board, 'U9 IN', [big, small], spec, 'BAT_IN'), [])
        big.SetWidth(pcbnew.FromMM(0.6)); big.SetDrill(pcbnew.FromMM(0.3))
        found = gate.via_issues(self.board, 'U9 IN', [big, small], spec, 'BAT_IN')
        self.assertTrue(any('0 via(s) of at least 1.0 / 0.5 mm' in i for i in found), found)
        big.SetWidth(pcbnew.FromMM(1.0)); big.SetDrill(pcbnew.FromMM(0.5)); small.SetDrill(pcbnew.FromMM(0.2))
        found = gate.via_issues(self.board, 'U9 IN', [big, small], spec, 'BAT_IN')
        self.assertTrue(any('a further via needs at least 0.5 / 0.3 mm' in i for i in found), found)

    def test_power_floor_must_hold_the_ipc_width(self):
        """R19-GATE-04: a path whose floor is below the IPC-2152 width at its design current fails as a table error."""
        self.part('J1', [('1', 0, 0, 'BAT_IN')], at=(5, 30), tht=True)
        self.part('U9', [('5', 0, 0, 'BAT_IN')], at=(25, 30))
        self.track((5, 30), (25, 30), 'BAT_IN', width=0.7)
        spec = dict(name='feed', net='BAT_IN', start={'J1': ('1',)}, end={'U9': ('5',)}, through={}, floor=0.4,
                    amps=2.9, vias=dict(count=0, drill=0.3, pad=0.5, plane=None))
        found = gate.power_paths(self.board, paths=(spec,), narrow=[])[0]
        self.assertTrue(any('floor 0.4 mm is below the IPC-2152 width 0.68' in i for i in found), found)
        self.assertEqual(gate.power_paths(self.board, paths=(dict(spec, floor=0.7),), narrow=[])[0], [])

    def test_word_centre_margin_blocks_named_words_only(self):
        """R19-GATE-06: a word whose ink centre is less than 1.0 mm nearer its own courtyard fails when it is in the
        blocking list and is only reported otherwise."""
        self.terminal('J400', 18); self.terminal('J1', 28)                 # courtyards y 16-24 and 26-34
        bat = self.word('BAT', 1, 25.2)
        args = dict(subjects={'BAT': 'J1'}, seams=[], spans={})
        found, ev = gate.word_legends(self.board, centre_words=('BAT',), **args)
        self.assertTrue(any('must be nearer its own by 1.0 mm' in i for i in found), found)
        found, ev = gate.word_legends(self.board, centre_words=(), **args)
        self.assertFalse(any('must be nearer its own' in i for i in found), found)
        self.assertLess(next(iter(ev.values()))['centre_margin'], 1.0)
        bat.SetPosition(self.P(1, 30))
        found, _ = gate.word_legends(self.board, centre_words=('BAT',), **args)
        self.assertFalse(any('must be nearer its own' in i for i in found), found)

    def test_silk_allowlist(self):
        """R19-GATE-07: only designators and the allowed legends on silkscreen."""
        r5 = self.part('R5', [('1', 0, 0, '3V3')], at=(30, 30))
        r5.Reference().SetLayer(pcbnew.F_SilkS); r5.Reference().SetVisible(True)
        for text in ('J2 1:3V3', 'J2 4:SWCLK 5:GND', 'M3-ASSY-R10', 'GPS', '1:BAT+', 'R134'):
            self.word(text, 20, 20)
        self.assertEqual(gate.silk_allowlist(self.board)[0], [])
        # D-R24-13: JLC withdrew the order-number mark; its JLCJLCJLCJLC placeholder now fails like any other text
        for text in ('BATT+', 'J2 1:SWDIO', 'IGN2', gate.JLC_ORDER_MARK):
            bad = self.word(text, 20, 40)
            found = gate.silk_allowlist(self.board)[0]
            self.assertTrue(any(repr(text) in i for i in found), (text, found))
            self.board.Remove(bad)
        r5.Value().SetLayer(pcbnew.F_SilkS); r5.Value().SetVisible(True)
        self.assertTrue(any('R5 Value field' in i for i in gate.silk_allowlist(self.board)[0]))

    def test_pour_debris(self):
        """R19-RTE-01: a fill piece with no via of its net and at most one of its pads fails; a via or a second pad
        makes it live; a named, measured entry admits exactly that piece and goes stale without it."""
        self.part('U1', [('19', 0, 0, 'GND'), ('20', 3, 0, 'GND')], at=(10, 20))
        self.fill('GND', pcbnew.F_Cu, 9.5, 19.5, 11, 21)                   # 2.25 mm^2 touching U1.19 only
        found = gate.pour_debris(self.board, named=[])[0]
        self.assertTrue(any('2.250 mm^2 piece' in i and 'only U1.19' in i for i in found), found)
        entry = [('GND', 'F.Cu', ('U1.19',), 2.25, 'measured')]
        self.assertEqual(gate.pour_debris(self.board, named=entry)[0], [])
        stale = [('GND', 'F.Cu', ('U1.19',), 3.0, 'other size')]
        found = gate.pour_debris(self.board, named=stale)[0]
        self.assertTrue(any('stale POUR_DEBRIS' in i for i in found), found)
        self.via(10.2, 20.8, 'GND', d=0.5)
        self.assertEqual(gate.pour_debris(self.board, named=[])[0], [])

    def neck_board(self, neck):
        """An In2 3V3 fill: a 12 x 10 mm block (the main piece) and a 10 x 10 mm block joined by a 2 mm long neck `neck`
        mm wide, one via in each block."""
        z = pcbnew.ZONE(self.board); z.SetLayer(pcbnew.In2_Cu); z.SetNet(self.board.FindNet('3V3'))
        poly = pcbnew.SHAPE_POLY_SET(); poly.NewOutline()
        h = neck / 2
        for x, y in ((0, 0), (12, 0), (12, 5 - h), (14, 5 - h), (14, 0), (24, 0), (24, 10), (14, 10), (14, 5 + h),
                     (12, 5 + h), (12, 10), (0, 10)):
            poly.Append(pcbnew.FromMM(x + 2), pcbnew.FromMM(y + 60))
        z.Outline().NewOutline()
        for i in range(poly.Outline(0).PointCount()):
            z.Outline().Append(poly.Outline(0).CPoint(i))
        z.SetFilledPolysList(pcbnew.In2_Cu, poly); z.SetIsFilled(True); self.board.Add(z)
        return [self.via(7, 65, '3V3'), self.via(21, 65, '3V3')]

    def test_plane_neck_counts_as_a_split(self):
        """R19-GATE-03: a 0.3 mm neck splits the fill (two >= 0.5 mm links needed and reported); 0.6 mm does not."""
        self.neck_board(0.3)
        found, ev = gate.plane_necks(self.board)
        self.assertTrue(any('neck under 0.5 mm and 0 link(s)' in i for i in found), found)
        self.assertTrue(ev['necks']['3V3 In2.Cu'] and ev['necks']['3V3 In2.Cu'][0]['width_mm'] < 0.32)
        for y in (64, 66):                                              # two 0.5 mm outer links across
            self.via(6, y, '3V3'); self.via(22, y, '3V3')
            self.track((6, y), (22, y), '3V3', pcbnew.F_Cu, width=0.5)
        self.assertEqual(gate.plane_necks(self.board)[0], [])

    def test_plane_neck_over_half_a_millimetre_passes(self):
        self.neck_board(0.6)
        found, ev = gate.plane_necks(self.board)
        self.assertEqual(found, [])
        self.assertAlmostEqual(ev['necks']['3V3 In2.Cu'][0]['width_mm'], 0.6, delta=0.02)

    def test_mpn_values(self):
        """R19-GATE-02: maker part numbers decode to their values; a value, tolerance, voltage or dielectric that
        disagrees with the Value field fails; an unknown family is listed."""
        table = {'0402WGF1002TCE': ('R', 10e3, 1), '0603WAF220KT5E': ('R', 2.2, 1), '25121WF360LT4E': ('R', 0.36, 1),
                 'FRC0603F2262TS': ('R', 22.6e3, 1), 'RC0603FR-0766K5L': ('R', 66.5e3, 1),
                 'RT0603BRD0749K9L': ('R', 49.9e3, 0.1), 'CRM2512-FX-2R00ELF': ('R', 2.0, 1),
                 'MCT0603MD2004BP500': ('R', 2e6, 0.1), 'CL05B104KB54PNC': ('C', 100e-9, 10),
                 'CL05C100JB5NNNC': ('C', 10e-12, 5), 'GRM32ER71E226KE15L': ('C', 22e-6, 10),
                 'GCJ188R71H104KA12D': ('C', 100e-9, 10), 'CC0603KRX7R9BB104': ('C', 100e-9, 10),
                 '0603B103K500NT': ('C', 10e-9, 10)}
        for mpn, (kind, value, tol) in table.items():
            got = gate.mpn_decode(mpn)
            self.assertEqual(got[0], kind, mpn)
            self.assertAlmostEqual(got[2]['value'] / value, 1.0, places=9, msg=mpn)
            self.assertEqual(got[2]['tol'], tol, mpn)
        self.assertEqual(gate.mpn_decode('MA25V470M8x10'), (None, None, None))
        self.assertEqual((gate.mpn_decode('CL05B104KB54PNC')[2]['volts'], gate.mpn_decode('CL05B104KB54PNC')[2]['diel']),
                         (50, 'X7R'))
        r = self.part('R131', [('1', 0, 0, 'PYRO1_OUT')], at=(30, 30)); r.SetValue('10k')
        r.SetField('Manufacturer Part', '0402WGF1002TCE')
        c = self.part('C127', [('1', 0, 0, 'GND')], at=(30, 35)); c.SetValue('10nF 50V X7R 10%')
        c.SetField('Manufacturer Part', 'CL05B103KB5NNNC')
        k = self.part('C84', [('1', 0, 0, 'GND')], at=(30, 40)); k.SetValue('470uF 25V polymer')
        k.SetField('Manufacturer Part', 'MA25V470M8x10')
        found, ev = gate.mpn_values(self.board)
        self.assertEqual(found, [])
        self.assertIn('aluminium polymer', ev['not_decoded']['C84'])
        r.SetField('Manufacturer Part', '0402WGF1001TCE')                   # b08e: R131 re-coded to 1 kohm
        c.SetValue('10nF 16V X5R 10%')
        found, _ = gate.mpn_values(self.board)
        self.assertTrue(any("R131: Value '10k' but 0402WGF1001TCE" in i for i in found), found)
        self.assertTrue(any('C127' in i and 'states 16 V' in i for i in found), found)
        self.assertTrue(any('C127' in i and 'states X5R' in i for i in found), found)


class AuditScope(SyntheticBase):
    plane = R4Synthetic.plane

    def setUp(self):
        super().setUp()
        for net in ('SPI1_SCK', 'GPS_PWR_EN', 'CAM_UART_OE'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))

    def test_aud2_exact_whitelist_and_fast_reference_boundary(self):
        import critical_reference as cr
        self.assertTrue({'ARM1_SENSE_MID', 'ARM1_SENSE', 'ACT_EN_MCU', 'CAM_UART_OE'} <= cr.R10_SLOW_RETURN_NETS)
        for net in ('RAW_ACT', 'RAW_ACT_SENSE_MCU', 'PYRO1_GATE', 'PYRO1_GATE_N', 'PYRO1_COLD', 'GPS_TX_MCU',
                    'ACT_EN_EXTRA', 'ARM1_SENSE_EXTRA', 'SD_SCK', 'SD_MISO', 'SD_MOSI', 'SD_CS', 'SD_DAT1', 'SD_DAT2'):
            self.assertFalse(cr.r10_slow_return_net(net), net)
        self.track((12, 30), (38, 30), 'ARM1_SENSE', pcbnew.B_Cu)
        self.track((20, 15), (22, 15), 'GPS_TX_MCU', pcbnew.F_Cu)
        gnd = pcbnew.SHAPE_POLY_SET(); gnd.NewOutline()
        for x, y in ((10, 10), (40, 10), (40, 20), (10, 20)):
            gnd.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        with patch.object(cr, 'fills', return_value={pcbnew.F_Cu: gnd}):
            issues, evidence = gate.references(self.board)
        self.assertEqual(issues, [], evidence)
        self.assertEqual(gate.region_issues(self.board)[0], [])
        self.track((12, 32), (38, 32), 'SPI1_SCK', pcbnew.B_Cu)
        self.assertTrue(any('SPI1_SCK' in i for i in gate.region_issues(self.board)[0]))
        with patch.object(cr, 'fills', return_value={pcbnew.F_Cu: gnd}):
            self.assertTrue(gate.references(self.board)[0])
        report = cr.compare(self.board, self.board, 0., True, 'r10')
        self.assertNotIn('GPS_PWR_EN', report['nets'])
        self.assertIn('GPS_TX_MCU', report['nets'])

    def test_aud10_distance_only_is_review_missing_subject_still_blocks(self):
        import check_r7 as r7
        text = pcbnew.PCB_TEXT(self.board); text.SetText('R134 terminal'); text.SetLayer(pcbnew.F_SilkS)
        text.SetTextSize(self.P(1, 1)); text.SetPosition(self.P(40, 80)); self.board.Add(text)
        review = []
        self.assertEqual(r7.legend_subjects(self.board, distance_review=review), [])
        self.assertEqual(len(review), 1)
        self.assertTrue(r7.legend_subjects(self.board))  # Legacy default still blocks distance.
        text.SetText('R999 terminal')
        self.assertTrue(any('not on the board' in i for i in r7.legend_subjects(self.board, distance_review=[])))

    def test_port_and_servo_tables_require_each_correct_pin_once(self):
        def text(value):
            item = pcbnew.PCB_TEXT(self.board); item.SetText(value); item.SetLayer(pcbnew.F_SilkS)
            self.board.Add(item)
            return item
        rows = {ref: text(ref + ' ' + ' '.join(f'{pin}:{name}' for pin, name in enumerate(names, 1)))
                for ref, names in gate.PORT_LEGENDS_R10.items()}
        text(gate.SERVO_HARNESS_NOTE)
        self.assertEqual(gate.port_legends(self.board), [])
        for ref in ('J2',):
            row, original = rows[ref], rows[ref].GetText()
            for pin, name in enumerate(gate.PORT_LEGENDS_R10[ref], 1):
                for replacement in ('', f'{pin}:WRONG'):
                    with self.subTest(ref=ref, pin=pin, replacement=replacement):
                        row.SetText(original.replace(f'{pin}:{name}', replacement))
                        self.assertTrue(any(f'{ref}.{pin}:' in i for i in gate.port_legends(self.board)))
                        row.SetText(original)
            for extra in (original, f'{ref} 2:WRONG', f'{ref} 99:NC', original + '!'):
                with self.subTest(extra=extra):
                    duplicate = text(extra)
                    self.assertTrue(gate.port_legends(self.board))
                    self.board.Remove(duplicate)
        self.assertEqual(gate.port_legends(self.board), [])

    def test_servo_harness_note_is_required_unique_and_without_conflicts(self):
        def text(value):
            item = pcbnew.PCB_TEXT(self.board); item.SetText(value); item.SetLayer(pcbnew.B_SilkS)
            self.board.Add(item)
            return item
        for ref, names in gate.PORT_LEGENDS_R10.items():
            text(ref + ' ' + ' '.join(f'{pin}:{name}' for pin, name in enumerate(names, 1)))
        note = text(gate.SERVO_HARNESS_NOTE)
        self.assertEqual(gate.port_legends(self.board), [])
        for value in ('', 'SERVO + FROM BOARD', 'SERVO + FROM HARNESSX'):
            note.SetText(value)
            self.assertTrue(any('J122:' in i for i in gate.port_legends(self.board)))
        note.SetText(gate.SERVO_HARNESS_NOTE)
        for value in (gate.SERVO_HARNESS_NOTE, 'SERVO + FROM BOARD'):
            duplicate = text(value)
            self.assertTrue(any('J122:' in i for i in gate.port_legends(self.board)))
            self.board.Remove(duplicate)
        self.assertEqual(gate.port_legends(self.board), [])

    def vippo(self):
        for f in list(self.board.GetFootprints()):
            if f.GetReference() == 'U401': self.board.Remove(f)
        for v in list(self.board.GetTracks()):
            if v.GetClass() == 'PCB_VIA': self.board.Remove(v)
        f = pcbnew.FootprintLoad(str(gate.ROOT / 'm3_design/assembly_review/kilib/rocket.pretty'), 'M3_TPS7A91_DSK10')
        self.assertIsNotNone(f)
        self.board.Add(f); f.SetReference('U401'); f.SetPosition(self.P(27.6, 13.6))
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT); f.SetOrientationDegrees(180)
        f.FindPadByNumber('11').SetNet(self.board.FindNet('GND'))
        vias = []
        for x, y in gate.vippo_centres(f):
            v = self.via(x, y, 'GND', d=.5, drill=.3)
            v.SetFillingMode(pcbnew.FILLING_MODE_FILLED); v.SetCappingMode(pcbnew.CAPPING_MODE_CAPPED); vias.append(v)
        return f, vias

    def test_gap3_exact_vippo_is_the_only_pad_paste_exception(self):
        import check_r7 as r7
        f, vias = self.vippo()
        issues, evidence, allowed = gate.thermal_vias(self.board)
        self.assertEqual(issues, [], evidence); self.assertEqual(len(allowed), 2)
        self.assertTrue(r7.vias_in_smd_pads(self.board)[0])  # Legacy default admits no thermal exception.
        ctx = gate.make_ctx(self.board, dru='(constraint thermal_relief_gap (min 0.25mm)) (constraint thermal_spoke_width (min 0.3mm))')
        self.assertEqual(gate.k_copper(ctx)[0], [])
        extra = self.part('X8', [], at=(27.3, 13.6))
        paste = pcbnew.PAD(extra); paste.SetAttribute(pcbnew.PAD_ATTRIB_SMD); paste.SetShape(pcbnew.PAD_SHAPE_RECT)
        paste.SetSize(self.P(.2, .2)); paste.SetPosition(self.P(27.3, 13.6))
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.B_Paste); paste.SetLayerSet(layers); extra.Add(paste)
        self.assertTrue(any('X8' in i for i in gate.k_copper(ctx)[0]))
        self.board.Remove(extra)
        self.part('X9', [('1', 0, 0, 'GND')], at=(35, 55))
        p = self.board.FindFootprintByReference('X9').FindPadByNumber('1')
        layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); layers.AddLayer(pcbnew.F_Mask); p.SetLayerSet(layers)
        self.via(35, 55, 'GND')
        self.assertTrue(any('X9.1' in i for i in gate.k_copper(ctx)[0]))

    def test_gap3_rigid_pose_preserves_only_the_maker_local_exception(self):
        f, vias = self.vippo()
        f.SetPosition(self.P(31.2, 17.8)); f.SetOrientationDegrees(90.)
        for via, point in zip(vias, gate.vippo_centres(f)):
            via.SetPosition(self.P(*point))
        issues, evidence, allowed = gate.thermal_vias(self.board)
        self.assertEqual(issues, [], evidence)
        self.assertEqual(len(allowed), 2)
        vias[0].Move(self.P(.002, 0))
        self.assertTrue(gate.thermal_vias(self.board)[0])

    def test_micro_sd_local_bypass_missing_or_remote_fails(self):
        self.part('J430', [('4', 0, 0, '3V3')], at=(20, 30))
        c100 = self.part('C460', [('1', 0, 0, '3V3'), ('2', 0, 1, 'GND')], at=(22, 30))
        bulk = self.part('C461', [('1', 0, 0, '3V3'), ('2', 0, 1, 'GND')], at=(25, 30))
        self.assertEqual(gate.sd_bypass(self.board)[0], [])
        c100.Move(self.P(1.1, 0))
        self.assertTrue(any('C460' in i for i in gate.sd_bypass(self.board)[0]))
        c100.Move(self.P(-1.1, 0)); bulk.Move(self.P(1.1, 0))
        self.assertTrue(any('C461' in i for i in gate.sd_bypass(self.board)[0]))
        self.board.Delete(c100)
        self.assertTrue(any('C460' in i for i in gate.sd_bypass(self.board)[0]))

    def test_gap3_wrong_net_extra_moved_size_pad_or_unfilled_is_rejected(self):
        mutations = (
            lambda f, vs: vs[0].SetNet(self.board.FindNet('RAW_ACT')),
            lambda f, vs: self.via(27.6, 13.6, 'GND', d=.5, drill=.3),
            lambda f, vs: vs[0].SetPosition(self.P(27.32, 13.6)),
            lambda f, vs: vs[0].SetPosition(self.P(27.302, 13.6)),
            lambda f, vs: vs[0].SetDrill(pcbnew.FromMM(.2)),
            lambda f, vs: vs[0].SetDrill(pcbnew.FromMM(.001)),  # Zero means inherit the board drill in KiCad.
            lambda f, vs: vs[0].SetWidth(pcbnew.FromMM(.6)),
            lambda f, vs: vs[0].SetViaType(pcbnew.VIATYPE_BLIND),
            lambda f, vs: vs[0].SetFillingMode(pcbnew.FILLING_MODE_NOT_FILLED),
            lambda f, vs: vs[0].SetCappingMode(pcbnew.CAPPING_MODE_FROM_BOARD),
            lambda f, vs: f.FindPadByNumber('11').SetNumber('12'),
            lambda f, vs: f.FindPadByNumber('11').SetSize(self.P(1.3, 2)),
            lambda f, vs: next(p for p in f.Pads() if not p.GetNumber()).Move(self.P(.02, 0)),
            lambda f, vs: next(p for p in f.Pads() if not p.GetNumber()).SetShape(pcbnew.PAD_SHAPE_OVAL),
        )
        for i, mutate in enumerate(mutations):
            with self.subTest(seed=i):
                f, vias = self.vippo(); mutate(f, vias)
                self.assertTrue(gate.thermal_vias(self.board)[0])

    def output_cell(self):
        parts = {}
        for ref, pads, at, value in (
            ('U9', [('6', 0, 0, 'RAW_PROTECTED'), ('8', 0, 2, 'GND')], (20, 50), 'TPS259470LRPWR'),
            ('C82', [('1', 0, 0, 'RAW_PROTECTED'), ('2', 0, 2, 'GND')], (23, 50), '22uF 25V X7R'),
            ('D9', [('1', 0, 0, 'RAW_PROTECTED'), ('2', 0, 2, 'GND')], (20, 46), 'B340A-13-F')):
            f = self.part(ref, pads, at=at); f.SetValue(value)
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT); parts[ref] = f
        self.out = self.track((20, 50), (23, 50), 'RAW_PROTECTED', pcbnew.B_Cu, width=.5)
        self.track((20, 50), (20, 46), 'RAW_PROTECTED', pcbnew.B_Cu, width=.5)
        self.ret = self.track((23, 52), (20, 52), 'GND', pcbnew.B_Cu, width=.5)
        self.track((20, 48), (20, 52), 'GND', pcbnew.B_Cu, width=.5)
        return parts

    def test_gap2_actual_routes_and_missing_return_not_pad_distance(self):
        parts = self.output_cell()
        issues, evidence = gate.output_loop(self.ctx())
        self.assertEqual(issues, [], evidence)
        self.assertEqual(evidence['C82']['ground_path']['layers'], ['B.Cu'])
        self.assertEqual(evidence['C82']['out_path']['path_mm'], [[20., 50.], [23., 50.]])
        self.assertGreater(evidence['C82']['projected_loop_area_mm2'], 0.)
        self.board.Remove(self.out)
        # Still under the absolute OUT limit: the route's detour must independently fail.
        detour = [self.track(a, b, 'RAW_PROTECTED', pcbnew.B_Cu, width=.5) for a, b in
                  (((20, 50), (20, 50.5)), ((20, 50.5), (23, 50.5)), ((23, 50.5), (23, 50)))]
        issues, evidence = gate.output_loop(self.ctx())
        self.assertLessEqual(evidence['C82']['out_route_mm'], evidence['bounds_mm']['C82'][0])
        self.assertTrue(any('C82' in i for i in issues))
        for t in detour: self.board.Remove(t)
        for a, b in (((20, 50), (20, 58)), ((20, 58), (23, 58)), ((23, 58), (23, 50))):
            self.track(a, b, 'RAW_PROTECTED', pcbnew.B_Cu, width=.5)
        self.assertTrue(any('C82' in i for i in gate.output_loop(self.ctx())[0]))
        self.board.Remove(self.ret)
        self.assertIsNone(gate.local_ground_return(self.board, parts['C82'].FindPadByNumber('2'),
                                                  parts['U9'].FindPadByNumber('8')))


@unittest.skipUnless(plate, 'optional plate diagnostic: NumPy unavailable')
class Plate(unittest.TestCase):
    """R3-MEC-01: every R10 mass key is placed (own row, or a mated allowance on its parent's box) or refused."""
    def setUp(self):
        self.spec = json.loads((Path(__file__).resolve().parents[1] /
                                'm3_design/assembly_review/sources/r10_design/masses.json').read_text())
        refs = ['J1', 'J121', 'J122', 'C84', 'LS120', 'J3', 'J9', 'J400', 'J410', 'J420', 'J430', 'J440',
                'J430 mated']
        self.fit = dict(profile='r10', outline=[0, 0, 46, 84], supports=[[4, 4], [42, 4], [4, 80], [42, 80], [42, 42]],
                        rows=[(1, ref, 'F', [20 + i, 40, 22 + i, 42, 0, 2]) for i, ref in enumerate(refs)])

    def test_mated_allowance_on_parent_and_unmatched_key_refused(self):
        _, masses, _ = plate.build(self.fit, 5, False, 'r10_mated', 'r10', self.spec)
        for ref in ('J1', 'J121', 'J122', 'J9', 'J400', 'J410', 'J420', 'J440'):
            self.assertIn(f'{ref} mated', masses)
            self.assertEqual(masses[f'{ref} mated'][1:3], masses[ref][1:3])
        for key in ('J2', 'J5 mated', 'U77'):
            mutant = dict(self.spec, masses_g=dict(self.spec['masses_g'], **{key: 1.0}))
            with self.assertRaises(ValueError):
                plate.build(self.fit, 5, False, 'r10_mated', 'r10', mutant)

    def test_r18_east_edge_terminals_and_capacitors_in_the_strain_table(self):
        """R18-MEC-01: the 100 g strain table reports the east-edge terminals, J400 and C431 / C421 / C411."""
        wanted = ('J410', 'J420', 'J9', 'J400', 'C431', 'C421', 'C411', 'J440', 'C445')    # D-R19-14: J440 / C445
        self.assertTrue(set(wanted) <= set(plate.STRAIN_PARTS))
        rows = self.fit['rows'] + [(1, ref, 'F', [30 + i, 50, 31.5 + i, 52.5, 0, 2.5])
                                   for i, ref in enumerate(('C431', 'C421', 'C411', 'C445'))]
        strain = plate.run(dict(self.fit, rows=rows), 'r18', 'r10', self.spec)['static']['r10_mated']['strain_ue']
        for ref in wanted:
            self.assertIn(ref, strain)
            self.assertGreater(strain[ref], 0)

    def test_r19_servo_resistors_in_the_strain_table(self):
        """R18-MEC-01 (rest): R150-R155 beside J122 are in the 100 g strain table."""
        wanted = ('R150', 'R151', 'R152', 'R153', 'R154', 'R155')
        self.assertTrue(set(wanted) <= set(plate.STRAIN_PARTS))
        rows = self.fit['rows'] + [(1, ref, 'F', [33 + i, 60, 33.8 + i, 60.8, 0, 0.5]) for i, ref in enumerate(wanted)]
        strain = plate.run(dict(self.fit, rows=rows), 'r19', 'r10', self.spec)['static']['r10_mated']['strain_ue']
        for ref in wanted:
            self.assertIn(ref, strain)
            self.assertGreater(strain[ref], 0)

    def test_terminal_tail_collision_rows_do_not_add_connector_mass(self):
        _, baseline, total = plate.build(self.fit, 5, False, 'r10_mated', 'r10', self.spec)
        extra = (1, 'J1.1 terminal tail', 'B', [6.45, 74, 8.35, 76, -3.8, -1.6])
        fit = dict(self.fit, rows=self.fit['rows'] + [extra])
        _, masses, actual = plate.build(fit, 5, False, 'r10_mated', 'r10', self.spec)
        self.assertEqual(masses, baseline)
        self.assertEqual(actual, total)
        for key in (extra[1], extra[1] + ' mated'):
            mutant = dict(self.spec, masses_g=dict(self.spec['masses_g'], **{key: 1.0}))
            with self.assertRaises(ValueError):
                plate.build(fit, 5, False, 'r10_mated', 'r10', mutant)


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class CriticalReferenceNames(unittest.TestCase):
    def test_r10_lists_hold_only_live_names_and_stale_ones_fail(self):
        """R19-REQ-10: no removed or dead names in the R10 lists (V3V3_SENSE, the R7-R9 radio SPI, CAM_TX_MCU); the
        port UART nets stay out of the slow list (strict partner-via / one-region rules); a name missing from the
        board is reported as stale (K-reference fails on it)."""
        import critical_reference as cr
        self.assertNotIn('V3V3_SENSE', cr.R10_SLOW_RETURN_NETS)
        self.assertFalse([n for n in cr.EXTENDED_R10 if n.startswith('RADIO_')])
        self.assertFalse({'CAM_TX_MCU', 'CAM_RX_MCU'} & set(cr.R10_PORT_NETS))
        self.assertFalse([n for n in cr.R10_SLOW_RETURN_NETS if cr.r10_port_net(n) and cr.R10_PORT_UART.match(n)])
        live = {n for names in cr.r10_names().values() for n in names}
        self.assertEqual(cr.r10_stale_names(live), [])
        self.assertEqual(cr.r10_stale_names(live - {'SWDIO'}), [('EXTENDED_R10', 'SWDIO')])


class FabScript(unittest.TestCase):
    def test_r10_fab_checks_required_fitted_on_the_exported_lists(self):
        """R3-GATE-05 / R18-GATE-04: r10_fab.sh exports an unbound package, then fab_manifest --bind runs check_r10 S-4
        on the exported BOM and CPL (with --verify-cpl and paste_check) and binds only after they pass, failing the run."""
        import fab_manifest
        text = (gate.ROOT / 'm3_design/r10_fab.sh').read_text()
        self.assertIn('set -euo pipefail', text)
        export = text.index('tools/export_fab.py "$B" --pending "$RECORD_DIR/export.json"')
        bind = text.index('tools/fab_manifest.py "$B" --bind "$RECORD_DIR/export.json"')
        self.assertLess(export, bind)
        self.assertNotIn('write_manifest', (gate.ROOT / 'tools/export_fab.py').read_text())
        checks = dict(fab_manifest.content_checks(Path('m3.kicad_pcb'), Path('fab'), 'kicad-python'))
        self.assertEqual(checks['S-4 BOM / CPL'][4:],
                         ['--only', 'S-4', '--bom', str(Path('fab/m3_bom_jlc.csv')), '--cpl', str(Path('fab/m3_cpl_jlc.csv'))])
        self.assertEqual(len(checks), 3)

    def test_r10_fab_selects_the_r10_procurement_limits(self):
        text = (gate.ROOT / 'm3_design/r10_fab.sh').read_text()
        self.assertIn('python3 tools/jlc_cost.py --profile r10', text)
        self.assertNotIn('--max-extended', text)
        self.assertIn('python3 tools/check_procurement.py --profile r10 --cost-only || STATUS=1', text)


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

    # Rules that read the saved board file's text (the s-expression netlist), not the loaded board object.
    TEXT_RULES = frozenset({'K-contract', 'K-actuators'})

    def saved_text(self, board):
        """The board as KiCad would save it: a seed made on the loaded object must reach a text-reading rule."""
        import tempfile
        with tempfile.TemporaryDirectory(prefix='r10_text_') as name:
            pcbnew.SaveBoard(str(Path(name) / 'm3.kicad_pcb'), board)
            return (Path(name) / 'm3.kicad_pcb').read_text()

    def run_rule(self, rid, board, path=None):
        folder = real_project()
        text = self.saved_text(board) if rid in self.TEXT_RULES and path is None else None
        rep = gate.check_board(board, folder, path or folder / 'm3.kicad_pcb', only={rid}, text=text)
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

    def drop(self, board, item):
        """Remove `item` from `board` and leave it undeleted: KiCad 10's SWIG hands a removed item to its Python proxy
        (thisown), which deletes it while the board's caches still point at it, and later reads of any board then fail
        ('SwigPyObject' footprints). The test leaks the item instead."""
        board.Remove(item)
        item.thisown = False

    def copper_clear(self, board, layer, start, end, width, netcode, clearance=.25):
        """True when a track from start to end on `layer` lies >= `clearance` mm from every pad, track, via and zone
        fill of another net (the contact under test included)."""
        shape = pcbnew.SHAPE_SEGMENT(start, end, width)
        margin = pcbnew.FromMM(clearance)
        for f in board.GetFootprints():
            for p in f.Pads():
                if p.IsOnLayer(layer) and p.GetNetCode() != netcode \
                        and p.GetEffectiveShape(layer).Collide(shape, margin):
                    return False
        for t in board.GetTracks():
            if t.IsOnLayer(layer) and t.GetNetCode() != netcode and t.GetEffectiveShape(layer).Collide(shape, margin):
                return False
        for z in board.Zones():
            if z.IsOnLayer(layer) and z.GetNetCode() != netcode and not z.GetIsRuleArea() \
                    and z.HasFilledPolysForLayer(layer) and z.GetFilledPolysList(layer).Collide(shape, margin):
                return False
        return True

    def test_drc_debug_and_probe_clearance_survive_the_duplicate_walk_removal(self):
        """The surviving real DRC rules, not an unrelated failing check, reject each new track's UUID."""
        import os
        import shutil
        import subprocess
        import tempfile
        cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli')
        if not cli:
            cli = next((p for p in ('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli',
                                    '/Applications/KiCad.app/Contents/MacOS/kicad-cli') if Path(p).is_file()), None)
        self.assertTrue(cli, 'real KiCad CLI required for surviving J2/TP DRC mutation tests')
        source = real_project()
        with tempfile.TemporaryDirectory(prefix='r10_contact_drc_') as name:
            folder = Path(name)
            for path in source.iterdir():
                if path.is_file():
                    shutil.copyfile(path, folder / path.name)
            (folder / 'kilib').symlink_to((source / 'kilib').resolve())
            board_path, report_path = folder / 'm3.kicad_pcb', folder / 'drc.json'

            def drc(board):
                pcbnew.SaveBoard(str(board_path), board)
                result = subprocess.run([str(cli), 'pcb', 'drc', '--severity-all', '--schematic-parity',
                    '--format', 'json', '-o', str(report_path), str(board_path)], capture_output=True, text=True,
                    timeout=120)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(report_path.is_file(), result.stdout + result.stderr)
                return json.loads(report_path.read_text())

            baseline = drc(self.load())
            self.assertEqual(baseline['violations'], [], 'unseeded board must be DRC-clean')
            self.assertEqual(baseline['unconnected_items'], [], 'unseeded board must be connected')
            self.assertEqual(baseline.get('schematic_parity', []), [], 'unseeded board must match its schematic')
            for ref, number, gap, expected_rule in (
                    ('J2', '1', .30, 'Tag-Connect contact to foreign copper'),
                    ('TP122', '1', .60, 'R9 bare test pads to foreign copper')):
                with self.subTest(ref=ref):
                    board = self.load(); pad = self.pad(board, ref, number)
                    # Prove the saved custom rule independently of equal floor overrides used by zone filling.
                    footprint = pad.GetParentFootprint(); footprint.SetLocalClearance(None)
                    for contact in footprint.Pads():
                        contact.SetLocalClearance(None)
                    # The gap exceeds default 0.15 mm but violates this contact's surviving custom rule. The seeded
                    # track stands `gap` mm (copper edge to pad box) from a contact of the part, on the first side
                    # (right, left, below, above) of the named pad, then of its sibling pads, where the track is
                    # >= 0.25 mm (the board's copper-to-hole clearance, above the 0.15 mm default) from all copper
                    # and holes of another net: the finding is this contact's rule, not a short or a neighbour's.
                    reach, half = pcbnew.FromMM(gap + .1), pcbnew.FromMM(.025)
                    found = None
                    for contact in [pad] + [q for q in footprint.Pads() if q.GetNumber() not in ('', number)]:
                        layer = pcbnew.F_Cu if contact.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
                        box, centre = contact.GetEffectiveShape(layer).BBox(), contact.GetPosition()
                        net = board.FindNet('GND' if contact.GetNetname() != 'GND' else '3V3')
                        sides = ((box.GetRight() + reach, centre.y, 0, half), (box.GetLeft() - reach, centre.y, 0, half),
                                 (centre.x, box.GetBottom() + reach, half, 0), (centre.x, box.GetTop() - reach, half, 0))
                        for x, y, hx, hy in sides:
                            start, end = pcbnew.VECTOR2I(x - hx, y - hy), pcbnew.VECTOR2I(x + hx, y + hy)
                            if self.copper_clear(board, layer, start, end, pcbnew.FromMM(.2), net.GetNetCode()):
                                found = layer, net, start, end
                                break
                        if found:
                            break
                    self.assertTrue(found, f'{ref}: no side of any contact leaves the seeded track clear of other copper')
                    layer, net, start, end = found
                    track = pcbnew.PCB_TRACK(board); track.SetLayer(layer); track.SetWidth(pcbnew.FromMM(.2))
                    track.SetStart(start); track.SetEnd(end)
                    track.SetNet(net); board.Add(track)
                    uuid = track.m_Uuid.AsString()
                    violations = drc(board)['violations']
                    hits = [v for v in violations if uuid in json.dumps(v) and expected_rule in json.dumps(v)
                            and v['type'] == 'clearance']
                    self.assertTrue(hits, f'{ref}: no {expected_rule!r} clearance violation for seeded track {uuid}; '
                                    + json.dumps([v for v in violations if uuid in json.dumps(v)], indent=1))

    def test_gap2_real_output_detour_and_absent_return(self):
        b = self.load()
        issues, evidence = gate.output_loop(gate.make_ctx(b))
        self.assertEqual(issues, [], evidence)
        for ref in ('C82', 'D9'):
            self.assertTrue(evidence[ref]['ground_path']['path_mm'])
            self.assertGreater(evidence[ref]['projected_loop_area_mm2'], 0.)
        start = self.pad(b, 'U9', '6')
        neck = next(t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK'
                    and t.GetNetname() == 'RAW_PROTECTED' and t.GetLayer() == pcbnew.B_Cu
                    and (t.GetStart() == start.GetPosition() or t.GetEnd() == start.GetPosition()))
        a, c = neck.GetStart(), neck.GetEnd()
        detour = (a, self.P(pcbnew.ToMM(a.x) - 6, pcbnew.ToMM(a.y)),
                  self.P(pcbnew.ToMM(c.x) - 6, pcbnew.ToMM(c.y)), c)
        for p, q in zip(detour, detour[1:]):
            t = pcbnew.Cast_to_PCB_TRACK(neck.Duplicate()); t.SetStart(p); t.SetEnd(q); b.Add(t)
        b.Delete(neck)
        self.assertTrue(any('short actual OUT / GND loop' in i for i in gate.output_loop(gate.make_ctx(b))[0]))
        b = self.load()
        for t in list(b.GetTracks()):
            if t.GetNetname() == 'GND': b.Delete(t)
        for z in list(b.Zones()):
            if z.GetNetname() == 'GND' and not z.GetIsRuleArea(): b.Delete(z)
        issues, evidence = gate.output_loop(gate.make_ctx(b))
        self.assertTrue(any('C82' in i for i in issues))
        self.assertIsNone(evidence['C82']['local_ground_route_mm'])

    def test_gap3_real_vippo_wrong_net_and_extra_via(self):
        b = self.load()
        issues, evidence, allowed = gate.thermal_vias(b)
        self.assertEqual(issues, [], evidence); self.assertEqual(len(allowed), 2)
        via = next(t for t in b.GetTracks() if t.m_Uuid.AsString() in allowed)
        via.SetNet(b.FindNet('RAW_PROTECTED'))
        self.assertTrue(gate.thermal_vias(b)[0])
        b = self.load()
        via = pcbnew.PCB_VIA(b); via.SetPosition(b.FindFootprintByReference('U401').GetPosition()); via.SetNet(b.FindNet('GND'))
        via.SetWidth(pcbnew.FromMM(.5)); via.SetDrill(pcbnew.FromMM(.3)); b.Add(via)
        self.assertTrue(any('exactly two' in i for i in gate.thermal_vias(b)[0]))

    def test_bypass_r134_with_a_track(self):
        def seed(b):
            p1, p2 = self.pad(b, 'R134', '1'), self.pad(b, 'R134', '2')
            t = pcbnew.PCB_TRACK(b); t.SetStart(p1.GetPosition()); t.SetEnd(p2.GetPosition())
            t.SetWidth(pcbnew.FromMM(0.25)); t.SetLayer(pcbnew.B_Cu); b.Add(t)
        self.seeded('S-1', seed, 'firing / sense chain is bypassed')

    def test_single_switch_feed_and_bus_sense(self):
        self.seeded('S-1', lambda b: self.pad(b, 'R132', '2').SetNet(b.FindNet('RAW_ACT')), 'R132.2 must be on')
        self.seeded('S-1', lambda b: self.pad(b, 'R134', '2').SetNet(b.FindNet('BAT_IN')), 'R134.2 must be on RAW_ACT')
        def old_bus(b):
            b.Add(pcbnew.NETINFO_ITEM(b, 'PYRO1_BUS'))
            self.pad(b, 'R134', '2').SetNet(b.FindNet('PYRO1_BUS'))
        self.seeded('S-1', old_bus, 'obsolete PYRO1_BUS')
        def old_terminal(b):
            f = pcbnew.Cast_to_FOOTPRINT(b.FindFootprintByReference('J121').Duplicate(False))
            f.SetReference('J124'); b.Add(f)
        self.seeded('S-1', old_terminal, 'obsolete J124')

    def test_micro_sd_topology_and_local_bypass_seeds(self):
        self.seeded('K-contract', lambda b: self.pad(b, 'J430', '4').SetNet(b.FindNet('PORT_4V8')), 'J430')
        self.seeded('K-contract', lambda b: b.FindFootprintByReference('R460').SetValue('100R'), 'R460')
        self.seeded('K-contract', lambda b: self.pad(b, 'U1', '79').SetNet(b.FindNet('SD_MOSI')), 'U1.79')
        self.seeded('K-contract', lambda b: b.FindFootprintByReference('J430').SetValue('push-push'), 'microSD')
        self.seeded('K-retained', lambda b: b.FindFootprintByReference('C460').Move(self.P(10, 0)), 'C460')
        self.seeded('S-4', lambda b: b.Delete(b.FindFootprintByReference('R464')), 'R464')

    def test_ava_removed_duplicate_bus_and_freed_pin_seeds(self):
        self.seeded('K-contract', lambda b: self.pad(b, 'U1', '34').SetNet(b.FindNet('ARM1_SENSE')), 'U1.34')
        def restored(b):
            f = pcbnew.Cast_to_FOOTPRINT(b.FindFootprintByReference('R132').Duplicate(False))
            f.SetReference('R177'); f.Move(self.P(0, 5)); b.Add(f)
        self.seeded('K-contract', restored, 'R177: removed R10 component')

    def test_screw_switch_contacts_and_protection(self):
        self.seeded('S-5', lambda b: self.pad(b, 'J400', '1').SetNet(b.FindNet('BAT_IN')), 'J400.1 must be')
        # D-R24-22 (R24-TRI-17): K-actuators names R10's own switch pins, not R9's J1.3 / J1.4
        self.seeded('K-actuators', lambda b: self.pad(b, 'R80', '2').SetNet(b.FindNet('BAT_IN')),
                    'J400.1 only through R80 to BAT_IN')
        self.seeded('S-5', lambda b: b.FindFootprintByReference('R165').SetValue('0R'), 'R165 must be 470k')
        def bridge(b):
            p1, p2 = self.pad(b, 'J400', '1'), self.pad(b, 'J400', '2')
            t = pcbnew.PCB_TRACK(b); t.SetStart(p1.GetPosition()); t.SetEnd(p2.GetPosition())
            t.SetWidth(pcbnew.FromMM(0.25)); t.SetLayer(pcbnew.F_Cu); b.Add(t)
        self.seeded('S-5', bridge, 'switch contact / resistor bypass')

    def test_independent_load_enable_default_off(self):
        self.seeded('S-3', lambda b: self.pad(b, 'R122', '1').SetNet(b.FindNet('RAW_PROTECTED')), 'R122.1 must be ACT_EN_MCU')
        self.seeded('S-3', lambda b: self.pad(b, 'U1', '16').SetNet(b.FindNet('PYRO1_GATE_N')), 'U1.16 must be ACT_EN_MCU')
        self.seeded('S-3', lambda b: self.pad(b, 'R123', '2').SetNet(b.FindNet('3V3')), 'R123.2 must be GND')
        self.seeded('S-3', lambda b: b.Delete(b.FindFootprintByReference('R123')), 'R123')

    def test_required_fitted_seeds(self):
        for ref, flag in (('R134', pcbnew.FP_DNP), ('R127', pcbnew.FP_EXCLUDE_FROM_BOM),
                          ('C126', pcbnew.FP_EXCLUDE_FROM_POS_FILES), ('R128', pcbnew.FP_BOARD_ONLY)):
            with self.subTest(ref=ref):
                def seed(b, ref=ref, flag=flag):
                    f = b.FindFootprintByReference(ref); f.SetAttributes(f.GetAttributes() | flag)
                self.seeded('S-4', seed, ref)
        with self.subTest(ref='R180 removed'):
            self.seeded('S-4', lambda b: b.Delete(b.FindFootprintByReference('R180')), 'R180')

    def test_functional_core_native_dnp_and_export_omission_seeds(self):
        import csv
        import io
        self.assertEqual(gate.board_population(self.load()), [])
        for ref in ('U1', 'U2', 'L1', 'U3', 'U4', 'U5', 'Y1', 'C13', 'C25', 'C6', 'R5'):
            with self.subTest(ref=ref):
                board = self.load(); part = board.FindFootprintByReference(ref)
                part.SetAttributes(part.GetAttributes() | pcbnew.FP_DNP)
                self.assertTrue(any(ref + ':' in i for i in gate.board_population(board)))
        for name in ('m3_bom_jlc.csv', 'm3_cpl_jlc.csv'):
            with (r10_board().parent / 'fab' / name).open() as source:
                rows = list(csv.DictReader(source))
            fields = list(rows[0])
            for ref in ('U1', 'U3', 'U4'):
                with self.subTest(file=name, ref=ref):
                    out = io.StringIO(); writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader()
                    for row in rows:
                        row = dict(row); members = [r.strip() for r in row['Designator'].split(',') if r.strip() != ref]
                        if members:
                            row['Designator'] = ','.join(members); writer.writerow(row)
                    self.assertTrue(any(ref + ':' in i for i in gate.assembly_population(out.getvalue())))

    def test_native_bom_zero_and_missing_qty_fail_s4_but_quantity_free_cpl_passes(self):
        import csv
        import io
        import tempfile
        source = real_project()
        with (r10_board().parent / 'fab/m3_bom_jlc.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        fields = list(rows[0])
        self.assertEqual(gate.s4(gate.make_ctx(self.load(), source, source / 'm3.kicad_pcb',
                         bom=r10_board().parent / 'fab/m3_bom_jlc.csv',
                         cpl=r10_board().parent / 'fab/m3_cpl_jlc.csv'))[0], [])
        for missing in (False, True):
            with self.subTest(missing_qty=missing), tempfile.TemporaryDirectory() as temp:
                columns = [field for field in fields if field != 'Qty'] if missing else fields
                output = io.StringIO(); writer = csv.DictWriter(output, columns, extrasaction='ignore')
                writer.writeheader()
                for row in rows:
                    row = dict(row)
                    if row['Designator'] == 'U1':
                        row['Qty'] = '0'
                    writer.writerow(row)
                path = Path(temp) / 'bom.csv'; path.write_text(output.getvalue())
                issues = gate.s4(gate.make_ctx(self.load(), source, source / 'm3.kicad_pcb', bom=path,
                                cpl=r10_board().parent / 'fab/m3_cpl_jlc.csv'))[0]
                self.assertTrue(any('BOM:' in issue and 'Qty' in issue for issue in issues), issues)

    def test_native_bom_identities_and_unexpected_designators_fail_s4(self):
        import csv
        import io
        import shutil
        import tempfile
        source = real_project()
        rows = list(csv.DictReader((r10_board().parent / 'fab/m3_bom_jlc.csv').read_text().splitlines()))
        columns = list(rows[0])
        cpl = r10_board().parent / 'fab/m3_cpl_jlc.csv'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'm3_bom_jlc.csv'       # D-R18-09: the owner BOM (hand-fitted C84) sits beside it
            shutil.copyfile(r10_board().parent / 'fab/m3_bom_owner.csv', Path(temp) / 'm3_bom_owner.csv')

            def check(changed, fields=columns):
                output = io.StringIO(); writer = csv.DictWriter(output, fields, extrasaction='ignore')
                writer.writeheader(); writer.writerows(changed); path.write_text(output.getvalue())
                return gate.s4(gate.make_ctx(self.load(), source, source / 'm3.kicad_pcb', bom=path, cpl=cpl))[0]

            self.assertTrue(any(',' in row['Designator'] for row in rows))
            self.assertEqual(check(rows), [])  # Real merged rows and the quantity-free CPL remain valid.
            for column, wrong in (('LCSC Part #', 'C168925'), ('Manufacturer Part', '25121WF360LT4E'),
                                  ('Footprint', 'R0402')):
                for value in (wrong, ''):
                    with self.subTest(column=column, value=value):
                        changed = copy.deepcopy(rows)
                        next(row for row in changed if row['Designator'] == 'R134')[column] = value
                        self.assertTrue(any('R134' in issue and column in issue for issue in check(changed)))
                with self.subTest(missing_column=column):
                    self.assertTrue(any('R134' in issue and column in issue
                                        for issue in check(rows, [key for key in columns if key != column])))
            changed = copy.deepcopy(rows)
            resistor = next(row for row in changed if row['Designator'] == 'R134')
            alternate = next(row for row in changed if row['Designator'] == 'R166')
            for column in ('LCSC Part #', 'Manufacturer Part', 'Footprint', 'Comment'):
                resistor[column] = alternate[column]
            self.assertTrue(any('R134' in issue and 'Manufacturer Part' in issue for issue in check(changed)))
            changed = copy.deepcopy(rows)
            row = next(row for row in changed if row['Designator'] == 'R134')
            row['Designator'] = 'R134,J2'; row['Qty'] = '2'
            self.assertTrue(any('J2' in issue and 'native fitted' in issue for issue in check(changed)))
            # Every merged member is compared, even when the first member has the right identity.
            row['Designator'] = 'R134,U1'
            changed = [row for row in changed if row['Designator'] != 'U1']
            self.assertTrue(any('U1' in issue and 'Manufacturer Part' in issue for issue in check(changed)))

    def test_r18_manual_fit_c84_s4(self):
        """R18-REQ-10 / R18-MFG-06 (D-R18-09): C84 is hand-fitted after both reflows: S-4 fails a C84 row in the JLC BOM
        or CPL, and a missing or wrong owner-BOM row; the real package passes."""
        import csv
        import io
        import shutil
        import tempfile
        source = real_project()
        fab = r10_board().parent / 'fab'
        self.assertIn('C84', gate.REQUIRED_FITTED)
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            for name in ('m3_bom_jlc.csv', 'm3_bom_owner.csv', 'm3_cpl_jlc.csv'):
                shutil.copyfile(fab / name, temp / name)

            def check():
                return gate.s4(gate.make_ctx(self.load(), source, source / 'm3.kicad_pcb', bom=temp / 'm3_bom_jlc.csv',
                                             cpl=temp / 'm3_cpl_jlc.csv'))[0]
            self.assertEqual(check(), [])
            owner = (temp / 'm3_bom_owner.csv').read_text()
            rows = list(csv.DictReader(io.StringIO(owner)))
            self.assertEqual([r['Designator'] for r in rows if 'C84' in r['Designator']], ['C84'])
            bom = (temp / 'm3_bom_jlc.csv').read_text()
            jlc_fields = list(csv.DictReader(io.StringIO(bom)).fieldnames)
            out = io.StringIO(); writer = csv.DictWriter(out, jlc_fields, extrasaction='ignore')
            writer.writerow({**next(r for r in rows if r['Designator'] == 'C84'), 'Qty': '1'})
            (temp / 'm3_bom_jlc.csv').write_text(bom + out.getvalue())
            self.assertTrue(any('BOM: C84 is fitted by hand after reflow' in i for i in check()), check())
            (temp / 'm3_bom_jlc.csv').write_text(bom)
            cpl = (temp / 'm3_cpl_jlc.csv').read_text()
            (temp / 'm3_cpl_jlc.csv').write_text(cpl + 'C84,27.5000mm,-78.5000mm,Top,90\n')
            self.assertTrue(any('CPL: C84 is fitted by hand after reflow' in i for i in check()), check())
            (temp / 'm3_cpl_jlc.csv').write_text(cpl)
            (temp / 'm3_bom_owner.csv').write_text(owner.replace('C46550466', 'C46550467'))
            self.assertTrue(any('owner BOM: hand-fitted C84 missing or not the native part' in i for i in check()))
            (temp / 'm3_bom_owner.csv').unlink()
            self.assertTrue(any('owner BOM: hand-fitted C84 missing or not the native part' in i for i in check()))

    def test_reviewed_models_reject_positive_shrinkage_and_pose_drift(self):
        import fit_check as fit
        for ref in (*gate.WIRE_ENTRY, 'J430', 'C84'):
            for field, axis, value in (('m_Scale', 'x', .01), ('m_Scale', 'y', .99999),
                                       ('m_Offset', 'y', .1), ('m_Offset', 'y', 3e-5),
                                       ('m_Rotation', 'z', 45. if ref == 'C84' else 90.)):
                with self.subTest(ref=ref, field=field):
                    board = self.load(); part = board.FindFootprintByReference(ref)
                    setattr(getattr(part.Models()[0], field), axis, value)
                    report = fit.check_board(board, real_project(), profile='r10')
                    self.assertTrue(any(ref + ': model envelope differs from reviewed dimensions/pose' in issue
                                        for issue in report['issues']), report['issues'])
                    if ref in gate.WIRE_ENTRY:
                        self.assertTrue(any(ref + ': model envelope differs from reviewed dimensions/pose' in issue
                                            for issue in self.run_rule('P-11', board)))

    def test_reviewed_models_allow_equivalent_metre_to_mm_conversion(self):
        import fit_check as fit
        import tempfile
        for ref in (*gate.WIRE_ENTRY, 'J430', 'C84'):
            with self.subTest(ref=ref), tempfile.TemporaryDirectory() as temp:
                board = self.load(); part = board.FindFootprintByReference(ref); model = part.Models()[0]
                original = fit.model_box(part, real_project())
                raw = fit.wrl_points(Path(model.m_Filename.replace('${KIPRJMOD}', str(real_project()))))
                xs, ys, zs = zip(*raw)
                path = Path(temp) / 'metres.step'
                path.write_text("#1=CARTESIAN_POINT('',(" + ','.join(str(min(a)/1000) for a in (xs, ys, zs))
                                + "));\n#2=CARTESIAN_POINT('',(" + ','.join(str(max(a)/1000) for a in (xs, ys, zs)) + "));\n")
                model.m_Filename = str(path)
                for axis in ('x', 'y', 'z'):
                    setattr(model.m_Scale, axis, getattr(model.m_Scale, axis)*1000)
                for actual, expected in zip(fit.model_box(part, real_project()), original):
                    self.assertAlmostEqual(actual, expected, places=6)
                self.assertTrue(fit.check_board(board, real_project(), profile='r10')['ok'])
                self.assertEqual(self.run_rule('P-11', board), set())

    def test_connected_foreign_inner_drawings_and_zones_fail_k_inner(self):
        self.assertEqual(self.run_rule('K-inner', self.load()), set())
        for footprint, zone in ((False, False), (True, False), (False, True)):
            with self.subTest(footprint=footprint, zone=zone):
                board = self.load()
                via = min((item for item in board.GetTracks() if item.GetClass() == 'PCB_VIA'
                           and item.GetNetname() == '3V3'),
                          key=lambda item: (item.GetPosition() - self.P(28.1, 60)).EuclideanNorm())
                centre = via.GetPosition()
                owner = board.FindFootprintByReference('U1') if footprint else board
                if zone:
                    item = pcbnew.ZONE(owner); item.SetLayer(pcbnew.In1_Cu)
                    item.SetNet(board.FindNet('3V3')); item.SetAssignedPriority(10)
                    item.SetLocalClearance(pcbnew.FromMM(.15)); outline = item.Outline(); outline.NewOutline()
                    for dx, dy in ((-.6, -.6), (.6, -.6), (.6, .6), (-.6, .6)):
                        point = centre + self.P(dx, dy); outline.Append(point.x, point.y)
                else:
                    item = pcbnew.PCB_SHAPE(owner); item.SetShape(pcbnew.SHAPE_T_SEGMENT)
                    item.SetLayer(pcbnew.In1_Cu); item.SetNet(board.FindNet('3V3'))
                    item.SetStart(centre); item.SetEnd(centre + self.P(1, 0)); item.SetWidth(pcbnew.FromMM(.2))
                owner.Add(item)
                pcbnew.ZONE_FILLER(board).Fill(board.Zones())
                if zone:
                    self.assertTrue(item.HasFilledPolysForLayer(pcbnew.In1_Cu))
                    self.assertTrue(pcbnew.SHAPE.Collide(item.GetFilledPolysList(pcbnew.In1_Cu),
                                    via.GetEffectiveShape(pcbnew.In1_Cu), 1))
                issues = self.run_rule('K-inner', board)
                self.assertTrue(any('In1.Cu' in issue and '3V3' in issue for issue in issues), issues)
                # This assertion proves real connected copper, rather than an unfilled-zone metadata seed.
                nodes = [node for node in gate.copper_nodes(board) if node[5] == '3V3'
                         and node[1] == pcbnew.In1_Cu and node[6].endswith('copper drawing')]
                if not zone:
                    self.assertTrue(any(node[2].Collide(via.GetPosition(), 0) for node in nodes))

    def test_individual_terminal_textbox_conflicts_and_duplicates(self):
        self.assertEqual(self.run_rule('K-legends', self.load()), set())
        for word, expected in (('4:TXO', 'J410.4'), ('J1 1:BAT-', 'J1.1')):
            with self.subTest(word=word):
                board = self.load(); item = pcbnew.PCB_TEXTBOX(board)
                item.SetText(word); item.SetLayer(pcbnew.F_SilkS)
                item.SetStart(self.P(29, 10)); item.SetEnd(self.P(34, 12))
                item.SetTextSize(self.P(1, 1)); item.SetTextThickness(pcbnew.FromMM(.15))
                item.SetBorderEnabled(False); board.Add(item)
                self.assertEqual(gate.silk_mask_overlaps(board), [])
                self.assertTrue(any(expected in i for i in self.run_rule('K-legends', board)))

    def test_invalid_models_fail_fit_and_p11(self):
        import fit_check as fit
        self.assertTrue(fit.check_board(self.load(), real_project(), profile='r10')['ok'])
        board = self.load(); part = board.FindFootprintByReference('J410'); part.Move(self.P(1, 0))
        self.assertTrue(any('wire room' in i for i in self.run_rule('P-11', board)))
        for axis in ('x', 'y', 'z'):
            setattr(part.Models()[0].m_Scale, axis, 0.)
        self.assertTrue(any('J410: invalid model transform' in i for i in self.run_rule('P-11', board)))
        self.assertFalse(fit.check_board(board, real_project(), profile='r10')['ok'])
        board = self.load(); board.FindFootprintByReference('J430').Models()[0].m_Scale.x = float('nan')
        report = fit.check_board(board, real_project(), profile='r10')
        self.assertFalse(report['ok'])
        self.assertTrue(any('J430: invalid model transform' in i for i in report['issues']))
        self.assertNotIn('J430', {row[1] for row in report['rows']})

    def test_gps_net_next_to_pyro_bus(self):
        def seed(b):
            p = self.pad(b, 'R134', '2')
            c, r = p.GetPosition(), p.GetSize().x // 2
            t = pcbnew.PCB_TRACK(b); t.SetNet(b.FindNet('GPS_TX_MCU')); t.SetLayer(pcbnew.B_Cu)
            t.SetWidth(pcbnew.FromMM(0.2))
            y = c.y - r - pcbnew.FromMM(0.15)                    # 0.05 mm from the pad's copper
            t.SetStart(pcbnew.VECTOR2I(c.x - pcbnew.FromMM(1), y)); t.SetEnd(pcbnew.VECTOR2I(c.x + pcbnew.FromMM(1), y))
            b.Add(t)
        self.seeded('S-6', seed, 'GPS_TX_MCU')

    def test_j122_middle_pin_given_a_net(self):
        self.seeded('S-7', lambda b: self.pad(b, 'J122', '2').SetNet(b.FindNet('RAW_ACT')), 'J122.2')
        self.seeded('S-7', lambda b: self.pad(b, 'J122', '5').SetNet(b.FindNet('3V3')), 'J122.5')

    def test_raw_act_fed_from_raw_protected(self):
        self.seeded('S-2', lambda b: self.pad(b, 'R132', '2').SetNet(b.FindNet('RAW_PROTECTED')), 'RAW_PROTECTED')
        self.seeded('S-2', lambda b: self.pad(b, 'Q121', '5').SetNet(b.FindNet('BAT_IN')), 'Q121')

    def test_gate_pull_down_moved(self):
        self.seeded('S-3', lambda b: self.pad(b, 'R128', '2').SetNet(b.FindNet('3V3')), 'resistor from the gate')

    def test_imu_rotation_and_terminal_entry(self):
        self.seeded('M-7', lambda b: b.FindFootprintByReference('U4').SetOrientationDegrees(0), 'rotation')
        self.seeded('P-11', lambda b: b.FindFootprintByReference('J121').SetOrientationDegrees(90), 'enter from')

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

    def test_fast_uart_layer_change_without_gnd_via(self):
        """R3-RTE-01: a new GPS_TX_MCU layer change with no GND via within 1.5 mm fails critical_via_no_gnd."""
        def seed(b):
            t = max((t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'GPS_TX_MCU'),
                    key=lambda t: t.GetLength())
            s, e, w, net = t.GetStart(), t.GetEnd(), t.GetWidth(), t.GetNet()
            source = t.GetLayer(); target = pcbnew.B_Cu if source == pcbnew.F_Cu else pcbnew.F_Cu
            m = pcbnew.VECTOR2I((s.x + e.x) // 2, (s.y + e.y) // 2)
            b.Remove(t)
            for a, c, lay in ((s, m, source), (m, e, target)):
                x = pcbnew.PCB_TRACK(b); x.SetStart(a); x.SetEnd(c); x.SetWidth(w); x.SetLayer(lay); x.SetNet(net)
                b.Add(x)
            v = pcbnew.PCB_VIA(b); v.SetPosition(m); v.SetWidth(pcbnew.FromMM(0.45)); v.SetDrill(pcbnew.FromMM(0.2))
            v.SetNet(net); b.Add(v)
            for g in [x for x in b.GetTracks() if x.GetClass() == 'PCB_VIA' and x.GetNetname() == 'GND'
                      and (x.GetPosition() - m).EuclideanNorm() < pcbnew.FromMM(1.6)]:
                b.Remove(g)
        new = self.route_new(seed, 'critical_via_no_gnd')
        self.assertTrue(any(d['net'] == 'GPS_TX_MCU' for d in new), new)

    def test_loader_pin_seeds(self):
        """R3-MCU-01: a net on a loader-driven pin, a changed member value and an extra part on an allowed net."""
        self.seeded('K-loader', lambda b: self.pad(b, 'U1', '68').SetNet(b.FindNet('BUZZ_DRV')), 'PA9')
        self.seeded('K-loader', lambda b: self.pad(b, 'U1', '43').SetNet(b.FindNet('LED_RED')), 'PE13')
        self.seeded('K-loader', lambda b: b.FindFootprintByReference('R61').SetValue('100'), 'VLOGIC_SENSE')
        self.seeded('K-loader', lambda b: self.pad(b, 'R156', '1').SetNet(b.FindNet('CAM_PWR_EN')), 'CAM_PWR_EN')

    def test_inner_copper_near_igniter_barrel(self):
        """R3-SAF-01: a 3V3 In1 track 0.5 mm from J121.2's plated barrel."""
        def near_barrel(b):
            p = self.pad(b, 'J121', '2')
            c, r = p.GetPosition(), p.GetDrillSize().x // 2
            x = c.x - r - pcbnew.FromMM(0.5) - pcbnew.FromMM(0.1)
            t = pcbnew.PCB_TRACK(b); t.SetNet(b.FindNet('3V3')); t.SetLayer(pcbnew.In1_Cu)
            t.SetWidth(pcbnew.FromMM(0.2)); t.SetStart(pcbnew.VECTOR2I(x, c.y - pcbnew.FromMM(1)))
            t.SetEnd(pcbnew.VECTOR2I(x, c.y + pcbnew.FromMM(1))); b.Add(t)
        self.seeded('S-8', near_barrel, 'In1.Cu')

    def test_r18_barrel_keepouts_removed(self):
        """R18-SAF-01 regression on the real board: without the R18 barrel keep-outs the refilled planes return to
        0.251 mm of In1 GND from the ACT_GATE barrels and S-8 fails."""
        def seed(b):
            for z in b.Zones():
                if z.GetIsRuleArea() and z.GetZoneName().startswith('R18_BARREL_KEEPOUT_'):
                    z.SetDoNotAllowZoneFills(False)        # disabled, not removed (SWIG zone lifetime)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        base = self.run_rule('S-8', self.load())
        board = self.load(); seed(board)
        new = self.run_rule('S-8', board) - base
        self.assertTrue(any('GND copper on In1.Cu' in i and 'ACT_GATE' in i for i in new), sorted(new)[:4])
        self.assertTrue(any('RAW_PROTECTED copper on In2.Cu' in i and 'BAT_ENABLE' in i for i in new), sorted(new)[:4])

    def test_r18_split_power_plane(self):
        """R18-RTE-01: an In2 track across the 3V3 region splits its fill and K-plane fails on the real board."""
        def seed(b):
            t = pcbnew.PCB_TRACK(b); t.SetLayer(pcbnew.In2_Cu); t.SetWidth(pcbnew.FromMM(0.4))
            t.SetNet(b.FindNet('USB_LIMITED')); t.SetStart(self.P(0.3, 40.5)); t.SetEnd(self.P(45.7, 40.5)); b.Add(t)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        self.seeded('K-plane', seed, '3V3 on In2.Cu fills as')

    def test_r18_q121_local_bias_seed(self):
        """R18-SAF-02: cut R119's bottom-copper join to Q121's gate and S-3 names Q121."""
        def seed(b):
            r119 = self.pad(b, 'R119', '1').GetPosition()
            for t in [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'ACT_GATE'
                      and t.GetLayer() == pcbnew.B_Cu and r119 in (t.GetStart(), t.GetEnd())]:
                b.Remove(t)
        self.seeded('S-3', seed, 'load switch Q121')

    def test_r18_k_rules_silkscreen_text_floors(self):
        """R18-GATE-06: lowering the project's silkscreen text height / stroke, silk clearance or spoke floor fails
        K-rules (DRC then no longer holds a 0.6 mm safety designator)."""
        folder = real_project()
        pro = folder / 'm3.kicad_pro'
        old = pro.read_text()
        self.assertEqual(self.run_rule('K-rules', self.load()), set())
        try:
            for key, value in (('min_text_height', 0.5), ('min_text_thickness', 0.08), ('min_silk_clearance', 0.05),
                               ('min_resolved_spokes', 1)):
                with self.subTest(key=key):
                    d = json.loads(old); d['board']['design_settings']['rules'][key] = value; pro.write_text(json.dumps(d))
                    found = self.run_rule('K-rules', self.load(), folder / 'm3.kicad_pcb')
                    self.assertTrue(any(f'design rule {key} = {value}' in i for i in found), found)
                    pro.write_text(old)
        finally:
            pro.write_text(old)

    def test_r18_support_centres_are_pinned(self):
        """R18-GATE-07: s15b's fit-clean 2.55 mm move of the middle support, and a corner move, fail M-3."""
        self.assertEqual(self.run_rule('M-3', self.load()), set())
        for old, new in (((4.0, 44.3), (3.5, 46.8)), ((42.0, 86.0), (40.0, 84.0))):
            def move(b, old=old, new=new):
                hole = next(d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts
                            and d.GetShape() == pcbnew.SHAPE_T_CIRCLE
                            and math.dist((pcbnew.ToMM(d.GetCenter().x), pcbnew.ToMM(d.GetCenter().y)), old) < .01)
                radius = hole.GetRadius()
                hole.SetCenter(self.P(*new)); hole.SetEnd(self.P(*new) + pcbnew.VECTOR2I(radius, 0))
            self.seeded('M-3', move, f'support ({old[0]:g}, {old[1]:g})')

    def texts(self, b, text):
        return [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == text]

    def test_r18_word_legends_are_beside_their_own_terminal(self):
        """R18-GATE-08: s16c (BAT and IGN exchanged), BAT / SWITCH exchanged, GPS / RADIO exchanged, SWITCH removed and
        RADIO moved off its J410 / J420 seam each fail K-legends; the real legends pass."""
        def swap(a, c):
            def seed(b):
                ta, tc = self.texts(b, a), self.texts(b, c)
                self.assertEqual((len(ta), len(tc)), (1, 1))
                ta[0].SetText(c); tc[0].SetText(a)
            return seed
        self.seeded('K-legends', swap('BAT', 'IGN'), "J1: word legend 'BAT'")
        self.seeded('K-legends', swap('BAT', 'SWITCH'), "J400: word legend 'SWITCH'")
        self.seeded('K-legends', swap('GPS', 'RADIO'), "J420: word legend 'RADIO'")
        self.seeded('K-legends', lambda b: b.Remove(self.texts(b, 'SWITCH')[0]), "'SWITCH' appears 0 times")

        def to(word, xy):
            def seed(b):
                self.texts(b, word)[0].SetPosition(self.P(*xy))
            return seed
        # D-R19-06: RADIO back on its round 18 seam spot, and GPS lifted to J410's courtyard edge, fail; no seam is named.
        self.seeded('K-legends', to('RADIO', (32.18, 23.525)), "J420: word legend 'RADIO'")
        self.seeded('K-legends', to('GPS', (32.894, 8.6)), "J410: word legend 'GPS'")
        rep = gate.check_board(self.load(), real_project(), real_project() / 'm3.kicad_pcb', only={'K-legends'})
        words = rep['rules']['K-legends']['evidence']['word_legends']
        self.assertEqual(sorted(w.split("'")[1] for w in words), sorted(gate.WORD_LEGENDS_R10))
        spans = {w.split("'")[1]: v.get('own_y_span_margin') for w, v in words.items()}
        self.assertGreaterEqual(spans['RADIO'], gate.WORD_SPAN_MARGIN)
        self.assertGreaterEqual(spans['GPS'], gate.WORD_SPAN_MARGIN)

    def path_tracks(self, b, name):
        spec = next(p for p in gate.POWER_PATHS if p['name'] == name)
        return gate.path_graph(b, spec['net'], spec['start'], spec['end'])[0]

    def test_r18_u9_power_path_seeds(self):
        """R18-GATE-02 / -03: s03 (the U9 OUT 0.7 mm runs at 0.31 mm), s03c (the IN feed upstream of C88 at 0.31 mm), a
        named C88-local run at 0.6 mm, s11 (one OUT via and its link removed) and s11b (the IN via 0.5 / 0.3 mm)."""
        board = self.load()
        issues, evidence = gate.power_paths(board)
        self.assertEqual(issues, [], evidence)
        self.assertEqual(len(evidence['narrow_used']), len(gate.POWER_NARROW))

        def neck(name, width, layer=None):
            def seed(b):
                hit = [t for t in self.path_tracks(b, name) if abs(pcbnew.ToMM(t.GetWidth()) - width) < .001
                       and (layer is None or t.GetLayer() == layer)]
                self.assertTrue(hit)
                for t in hit:
                    t.SetWidth(pcbnew.FromMM(0.31))
            return seed
        self.seeded('K-power', neck('U9 OUT', 0.7), 'U9 OUT: RAW_PROTECTED track 0.310 mm wide')
        self.seeded('K-power', neck('U9 IN', 1.0, pcbnew.F_Cu), 'U9 IN: BAT_IN track 0.310 mm wide')

        def local(b):                       # D-R24-17: the C88-local 0.7 mm piece is 1.74 mm (tap T to C88.1)
            t = next(t for t in self.path_tracks(b, 'U9 IN') if abs(pcbnew.ToMM(t.GetLength()) - 1.74) < .001)
            t.SetWidth(pcbnew.FromMM(0.6))
        self.seeded('K-power', local, 'U9 IN: BAT_IN track 0.600 mm wide')

        def one_via(b):                     # D-R24-17: the second OUT via sits east of C82.1's edge on its own leg
            via = next(v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'RAW_PROTECTED'
                       and v.GetPosition() == self.P(21.1, 78.25))
            leg = next(t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'RAW_PROTECTED'
                       and self.P(21.1, 78.25) in (t.GetStart(), t.GetEnd()))
            b.Remove(via); b.Remove(leg)
        self.seeded('K-power', one_via, 'U9 OUT: 1 via(s) on the path; at least 2 required')

        def small_feed_via(b):
            via = next(v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'BAT_IN')
            via.SetWidth(pcbnew.FromMM(0.5)); via.SetDrill(pcbnew.FromMM(0.3))
        self.seeded('K-power', small_feed_via, 'U9 IN: 0 via(s) of at least 1.0 / 0.5 mm on the path')   # R19-GATE-05

    def test_r18_q124_fire_return_seeds(self):
        """R18-GATE-03: s26 (Q124's source bar and via stubs at 0.15 mm) and one of its two GND vias removed."""
        issues, evidence = gate.fire_return(self.load())
        self.assertEqual(issues, [], evidence)
        self.assertEqual(len(evidence['vias']), 2)

        def thin(b):
            q124 = b.FindFootprintByReference('Q124')
            sources = [p for p in q124.Pads() if p.GetNumber() in ('1', '2', '3')]
            hit = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'GND'
                   and any(p.HitTest(q) for p in sources for q in (t.GetStart(), t.GetEnd()))]
            self.assertEqual(len(hit), 3)
            for t in hit:
                t.SetWidth(pcbnew.FromMM(0.15))
        self.seeded('K-power', thin, 'Q124 fire return: GND track 0.150 mm wide')

        def drop_via(b):
            self.drop(b, [v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA'
                          and v.GetPosition() == self.P(15.85, 57.695)][0])
        self.seeded('K-power', drop_via, 'Q124 fire return: 1 via(s) on the path; at least 2 required')

    def test_r19_load_switch_enable_cap_and_removed_probe(self):
        """D-R19-03 / -04 (R19-SAF-03 / -06): S-3 fails a wrong-valued or missing C123 (Q122's gate-source 10 nF);
        K-actuators fails C123's identity, C87 back on the 2.2 uF code and any part named TP121; the real board passes."""
        def value(ref, v):
            return lambda b: b.FindFootprintByReference(ref).SetValue(v)

        def lcsc(ref, code):
            return lambda b: b.FindFootprintByReference(ref).SetField('LCSC', code)
        self.assertEqual(self.run_rule('S-3', self.load()), set())
        self.assertEqual(self.run_rule('K-actuators', self.load()), set())
        self.seeded('S-3', value('C123', '100nF 50V X7R 10%'), 'C123 must be 1e-08 F')
        self.seeded('S-3', lambda b: b.Remove(b.FindFootprintByReference('C123')), 'C123.1 must be ACT_EN')
        self.seeded('K-actuators', value('C123', '1nF 50V X7R 10%'), 'C123 must be the 10nF 0402 (C15195)')
        self.seeded('K-actuators', lcsc('C87', 'C23630'), 'C87 must be LCSC C21120')
        self.seeded('K-actuators', lambda b: b.FindFootprintByReference('TP74').SetReference('TP121'),
                    'TP121 must be removed')

    def test_r19_doubled_feeds_keep_two_vias(self):
        """D-R19-09 (R19-PWR-01 / R19-GATE-04): removing either via of a doubled feed, one of L400.2's two In2 vias (the
        round 19 reviewer's seed) or L1.2's direct via fails K-power; dropping the F/B-only bridge via fails it as a
        missing named bridge. D-R24-09: R402 / R403 sit on B.Cu beside U401 (R402.1's own via is gone) and U401's OUT
        run reaches In2 through (29.75, 11.65) and (29.75, 9.95) on the C406.1 run, and through the latter's F.Cu run
        J440's (30.5, 9.95): dropping (29.75, 9.95) leaves one (dropping (29.75, 11.65) leaves two by the count)."""
        def drop(net, *xys):
            def seed(b):
                for xy in xys:
                    self.drop(b, [v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == net
                                  and v.GetPosition() == self.P(*xy)][0])
            return seed
        for name, net, xys in (('U401 IN', 'PORT_5V3', [(26.45, 11.95)]), ('U401 IN', 'PORT_5V3', [(25.9, 8.6)]),
                               ('U401 EN', 'PORT_5V3', [(24.9, 14.9)]),
                               ('U401 OUT', 'PORT_4V8', [(29.75, 9.95)]),
                               ('U402 IN', 'PORT_5V3', [(42.75, 61.8)]), ('C84 hold-up', 'VLOGIC', [(29.8, 81.15)]),
                               ('U400 OUT', 'PORT_5V3', [(26.0, 8.0)]), ('U2 OUT', '3V3', [(23.1, 78.1)])):
            self.seeded('K-power', drop(net, *xys), f'{name}: 1 via(s) on the path; at least 2 required')
        self.seeded('K-power', drop('3V3', (26.4, 79.26)), 'named bridge via (26.4, 79.26) is not on the path')

    def test_r19_aux_port_feed_and_contract(self):
        """D-R19-14: the AUX port's F.Cu feed keeps two In2 vias (dropping the second fails K-power); J440 is held to the
        port terminal's part and nets (K-contract), and its AUX word to J440's courtyard span (K-legends)."""
        def drop(b):
            self.drop(b, [v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'PORT_4V8'
                          and v.GetPosition() == self.P(29.75, 9.95)][0])
        self.seeded('K-power', drop, 'J440 feed: 1 via(s) on the path; at least 2 required')

        self.seeded('K-contract', lambda b: self.pad(b, 'J440', '1').SetNet(b.FindNet('3V3')),
                    'J440: connector pin mapping must be')

        def word(b):
            t = next(d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == 'AUX')
            t.SetPosition(self.P(13.4, 7.2))
        self.seeded('K-legends', word, "word legend 'AUX'")

    def test_r19_hand_fitted_c84_has_no_paste(self):
        """D-R19-07 (R19-MFG-02): S-4 fails paste on the hand-fitted C84's lands; the real board has none."""
        pads = self.load().FindFootprintByReference('C84').Pads()
        self.assertFalse(any(p.IsOnLayer(pcbnew.F_Paste) for p in pads))

        def paste(b):
            pad = b.FindFootprintByReference('C84').FindPadByNumber('1')
            layers = pad.GetLayerSet(); layers.AddLayer(pcbnew.F_Paste); pad.SetLayerSet(layers)
        self.seeded('S-4', paste, "C84 is fitted by hand after reflow")

    def test_r19_pyro_out_barrels_clear_gnd(self):
        """D-R19-01 (R19-SAF-01): S-8 now counts GND at the PYRO1_OUT barrels: an In1 GND track 0.30 mm from the OUT via
        wall fails; the real board's keep-outs pass."""
        self.assertEqual(self.run_rule('S-8', self.load()), set())

        def gnd(b):
            t = pcbnew.PCB_TRACK(b); t.SetLayer(pcbnew.In1_Cu); t.SetNet(b.FindNet('GND'))
            t.SetStart(self.P(12.18, 54.4)); t.SetEnd(self.P(12.18, 55.8)); t.SetWidth(pcbnew.FromMM(0.2)); b.Add(t)
        self.seeded('S-8', gnd, 'GND copper on In1.Cu is 0.300 mm')

    def test_r18_unpinned_land_edit_fails(self):
        """R18-GATE-09: s25 (Q124's gate pad moved 0.08 mm in the library, as a consistent library + board edit would)
        fails K-lands, and so do an unpinned footprint, a stale pin and a second footprint library."""
        import shutil
        import tempfile
        src = r10_board()
        with tempfile.TemporaryDirectory(prefix='r10_lands_') as name:
            folder = Path(name)
            shutil.copyfile(src, folder / 'm3.kicad_pcb')
            shutil.copyfile(src.parent / 'fp-lib-table', folder / 'fp-lib-table')
            shutil.copytree(src.parent / 'kilib/rocket.pretty', folder / 'kilib/rocket.pretty')
            board = pcbnew.LoadBoard(str(folder / 'm3.kicad_pcb'))
            ctx = gate.make_ctx(board, folder, folder / 'm3.kicad_pcb')
            self.assertEqual(gate.k_lands(ctx)[0], [])
            land = folder / 'kilib/rocket.pretty/M3_AON7524_DFN3x3A.kicad_mod'
            text = land.read_text()
            self.assertEqual(text.count('(at 0.975 1.4'), 1)
            land.write_text(text.replace('(at 0.975 1.4', '(at 1.055 1.4'))
            found = gate.k_lands(ctx)[0]
            self.assertTrue(any('M3_AON7524_DFN3x3A (Q124) library file SHA-256' in i for i in found), found)
            land.write_text(text)
            pins = dict(gate.FOOTPRINT_SHA256)
            del pins['R0402']
            pins['M3_UNUSED_LAND'] = '0' * 64
            found = gate.k_lands(ctx, pins=pins)[0]
            self.assertTrue(any('R0402' in i and 'neither generated by r10_parts nor pinned' in i for i in found), found)
            self.assertTrue(any('stale FOOTPRINT_SHA256 entry M3_UNUSED_LAND' in i for i in found), found)
            table = folder / 'fp-lib-table'
            table.write_text(table.read_text().rstrip()[:-1] + '\n\t(lib (name "other") (type "KiCad") '
                             '(uri "${KIPRJMOD}/other.pretty") (options "") (descr "")))\n')
            self.assertTrue(any('fp-lib-table lists' in i for i in gate.k_lands(ctx)[0]))

    def test_inner_graphics_near_pyro_barrel(self):
        for footprint in (False, True):
            for net in ('', '3V3'):
                with self.subTest(footprint=footprint, net=net):
                    def seed(b):
                        owner = b.FindFootprintByReference('J121') if footprint else b
                        item = pcbnew.PCB_SHAPE(owner); item.SetShape(pcbnew.SHAPE_T_SEGMENT)
                        item.SetLayer(pcbnew.In2_Cu); item.SetWidth(pcbnew.FromMM(0.2))
                        item.SetStart(self.P(5.75, 53.7)); item.SetEnd(self.P(5.75, 54.5))
                        if net: item.SetNet(b.FindNet(net))
                        owner.Add(item)
                    self.seeded('S-8', seed, 'J121.1')

    def test_inner_copper_text_near_pyro_barrel(self):
        for footprint in (False, True):
            with self.subTest(footprint=footprint):
                def seed(b):
                    owner = b.FindFootprintByReference('J121') if footprint else b
                    item = pcbnew.PCB_TEXT(owner); item.SetText('I'); item.SetLayer(pcbnew.In2_Cu)
                    item.SetTextSize(self.P(1, 1)); item.SetTextThickness(pcbnew.FromMM(0.2))
                    item.SetPosition(self.P(5.75, 54.1)); owner.Add(item)
                self.seeded('S-8', seed, 'J121.1')

    def test_conflicting_silkscreen_textboxes(self):
        # 'J420 3:...' is a combined table beside individual pin legends; the bare '2:RXI' (no terminal has that word)
        # is nearest J430.11, a nonterminal connector contact. All individual labels use the same nearest-pin rule.
        for value, word in (('J420 3:RXI', 'J420.3'), ('J420 3:TXO', 'J420.3'), ('2:RXI', 'J430.11'),
                            ('SERVO + FROM BOARD', 'J122:'), (gate.SERVO_HARNESS_NOTE, 'J122:')):
            with self.subTest(text=value):
                def seed(b):
                    # A free top-side spot (no pad mask opening): only the legend's content can be the finding.
                    item = pcbnew.PCB_TEXTBOX(b); item.SetText(value); item.SetLayer(pcbnew.F_SilkS)
                    # D-R19-14: the AUX cell now fills the former (9-21, 12-14) spot; this one stays nearest J430.11
                    item.SetStart(self.P(11.8, 22.6)); item.SetEnd(self.P(18.0, 24.4))
                    item.SetTextSize(self.P(1, 1)); item.SetTextThickness(pcbnew.FromMM(0.15))
                    item.SetBorderEnabled(False); b.Add(item)
                self.seeded('K-legends', seed, word)
                board = self.load(); seed(board)
                self.assertEqual(gate.silk_mask_overlaps(board), gate.silk_mask_overlaps(self.load()),
                                 'the seed text box must sit clear of every solder mask opening')

    def test_copper_text_and_multi_net_part_bridge(self):
        """R3-GATE-02: copper text bypassing R134; U1 (> 4 nets) on both RAW_ACT and PYRO1_IGN."""
        def text(b):
            p1, p2 = self.pad(b, 'R134', '1'), self.pad(b, 'R134', '2')
            a, c = p1.GetPosition(), p2.GetPosition()
            t = pcbnew.PCB_TEXT(b); t.SetText('I'); t.SetLayer(pcbnew.B_Cu)
            span = (c - a).EuclideanNorm()
            t.SetTextSize(pcbnew.VECTOR2I(int(span * 1.3), int(span * 1.3))); t.SetTextThickness(pcbnew.FromMM(0.6))
            if abs(c.x - a.x) > abs(c.y - a.y):
                t.SetTextAngleDegrees(90)
            t.SetPosition(pcbnew.VECTOR2I((a.x + c.x) // 2, (a.y + c.y) // 2)); b.Add(t)
        self.seeded('S-1', text, 'firing / sense chain is bypassed')

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

    def test_s9_custom_pad_anchor_cannot_exempt_long_supply_tracks(self):
        board = self.load()
        issues, evidence = gate.s9(gate.make_ctx(board))
        self.assertEqual(issues, [], evidence)
        self.assertEqual(len(gate.FIRE_NARROW), 7)
        self.assertEqual(len(evidence['narrow_used']), 7)
        for net in ('RAW_ACT', 'BAT_IN'):
            board = self.load()
            fp = board.FindFootprintByReference('Q121' if net == 'RAW_ACT' else 'Q120')
            self.assertAlmostEqual(pcbnew.ToMM(fp.FindPadByNumber('9').GetSize().x), .43)
            # Follow the actual terminal-to-FET path, rather than the circuit-pass coordinates.
            tracks = gate.fire_path(board, net, gate.FIRE_TERMINALS[net])[0]
            self.assertTrue(tracks, net)
            track = max(tracks, key=lambda t: t.GetLength())
            self.assertGreater(pcbnew.ToMM(track.GetLength()), 2.0, net)
            track.SetWidth(pcbnew.FromMM(.43))
            self.assertTrue(any(f'{net} fire-path track 0.430 mm' in i
                                for i in gate.s9(gate.make_ctx(board))[0]))
        for entry in gate.FIRE_NARROW:
            with self.subTest(bridge=entry[5]):
                board = self.load()
                tracks = []
                for t in gate.fire_path(board, entry[0], gate.FIRE_TERMINALS[entry[0]])[0]:
                    points = sorted((pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)) for p in (t.GetStart(), t.GetEnd()))
                    if all(abs(a - b) < .001 for a, b in zip(points[0] + points[1], entry[4])):
                        tracks.append(t)
                self.assertEqual(len(tracks), 1, entry)
                tracks[0].SetWidth(pcbnew.FromMM(.35))
                issues = gate.s9(gate.make_ctx(board))[0]
                self.assertTrue(any('ACT_FET_S fire-path track 0.350 mm' in i for i in issues), issues)
                self.assertTrue(any('stale FIRE_NARROW' in i and entry[5] in i for i in issues), issues)

    def test_external_port_and_servo_legend_faults(self):
        self.assertEqual(self.run_rule('K-legends', self.load()), set())
        for ref, number, old, wrong in (('J410', '2', 'GND', '3V3'), ('J420', '3', 'TXO', 'RXI'),
                                       ('J122', '5', 'GND', 'NC')):
            def seed(b, ref=ref, number=number, old=old, wrong=wrong):
                point = self.pad(b, ref, number).GetPosition()
                matches = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT)
                           and d.GetText() == number + ':' + old]
                self.assertTrue(matches, (ref, number, old))
                closest = min(matches, key=lambda d: (d.GetPosition() - point).EuclideanNorm())
                closest.SetText(number + ':' + wrong)
            self.seeded('K-legends', seed, ref + '.' + number)
        def note(b):
            next(d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT)
                 and d.GetText() == gate.SERVO_HARNESS_NOTE).SetText('SERVO + FROM BOARD')
        self.seeded('K-legends', note, 'J122:')

    def test_r8_gate_text_hidden_width(self):
        """R8-GATE-02 / 03 / 04: pinned legends, shown safety references, BAT_IN / RAW_PROTECTED width floor."""
        for rid in ('K-legends', 'K-width'):
            self.assertEqual(self.run_rule(rid, self.load()), set(), rid)
        for _, text in gate.PINNED_TEXTS:
            def seed(b, text=text):
                for d in b.GetDrawings():
                    if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == text:
                        d.SetText(text + 'X')
            self.seeded('K-legends', seed, repr(text))
        for ref in ('J400', 'Q120'):
            self.seeded('K-legends', lambda b, ref=ref: b.FindFootprintByReference(ref).Reference().SetVisible(False),
                        f'{ref}: reference designator hidden')
        rep = gate.check_board(self.load(), real_project(), real_project() / 'm3.kicad_pcb', only={'K-legends'})
        ev = rep['rules']['K-legends']['evidence']
        self.assertEqual(ev['hidden_count'], len(ev['hidden']))

        def narrow(b):
            # A real battery load-feed segment; a stale coordinate must not silently inject no fault.
            tracks = gate.fire_path(b, 'BAT_IN', gate.FIRE_TERMINALS['BAT_IN'])[0]
            self.assertTrue(tracks)
            track = max(tracks, key=lambda t: t.GetLength())
            self.assertGreater(pcbnew.ToMM(track.GetLength()), 2.0)
            track.SetWidth(pcbnew.FromMM(0.3))
        self.seeded('K-width', narrow, 'BAT_IN: 0.3 mm-wide run')

        def thin(b):
            for t in b.GetTracks():
                if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'RAW_PROTECTED':
                    t.SetWidth(pcbnew.FromMM(0.2)); break
        self.seeded('K-width', thin, 'RAW_PROTECTED track 0.200')

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
        """R6-GATE-07 / R6-SAF-01 / R6-SAF-02: a renamed test point on RAW_ACT (S-1); R913 100R from PYRO1_GATE_N to
        3V3 (S-3); an In2 RAW_PROTECTED track 0.425 mm from J121.2's hole (S-8); a PTH pad of another net near it."""
        def renamed_tp(b):
            tp = b.FindFootprintByReference('TP120')
            tp.SetReference('PT121'); tp.FindPadByNumber('1').SetNet(b.FindNet('RAW_ACT'))
        self.seeded('S-1', renamed_tp, 'PT121')

        def pull_up(b):
            f = pcbnew.Cast_to_FOOTPRINT(b.FindFootprintByReference('R127').Duplicate(False))
            f.SetReference('R913'); f.SetValue('100R'); b.Add(f)
            next(q for q in f.Pads() if q.GetNetname() == 'GND').SetNet(b.FindNet('3V3'))
        self.seeded('S-3', pull_up, 'R913')

        def in2_track(b):
            p = self.pad(b, 'J121', '2')
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
        for raw, armed in (('ACT_EN_MCU', 'ARM1_SENSE'), ('ACT_GATE', 'PYRO1_CONT')):
            for rid in ('S-1', 'S-2'):
                self.seeded(rid, bridge(raw, armed), 'bypasses the named pyro / sense chain')

    def test_supply_ties_seeds(self):
        """R4-SAF-02 / R4-GATE-03: RAW_ACT -> 3V3 resistor chain (two parts), a U9 pad on RAW_ACT."""
        def chain(b):
            self.pad(b, 'R175', '2').SetNet(b.FindNet('3V3'))
        self.seeded('S-2', chain, 'not a named tie')
        self.seeded('S-1', lambda b: self.pad(b, 'R132', '2').SetNet(b.FindNet('3V3')), 'not a named tie')
        self.seeded('S-1', lambda b: self.pad(b, 'U9', '1').SetNet(b.FindNet('RAW_ACT')), 'U9 has pads on')

    def test_imu_pad1_offset_and_lever_arm(self):
        """R4-MEC-05: U4 pad 1 displaced, and U4 moved 2 mm along x."""
        def pad1(b):
            p = self.pad(b, 'U4', '1'); q = p.GetPosition(); p.SetPosition(pcbnew.VECTOR2I(q.x + self.P(0.3, 0).x, q.y))
        self.seeded('M-7', pad1, 'pad 1')
        self.seeded('M-7', lambda b: b.FindFootprintByReference('U4').Move(self.P(2, 0)), 'roll axis')

    def test_k_rules_seeds(self):
        """R4-GATE-01: a RAW_ACT / 3V3 zero-clearance rule in m3.kicad_dru, min_clearance 0 and a net class
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
            'rule': lambda: dru.write_text(old_dru + '\n(rule "x" (condition "A.NetName==\'RAW_ACT\' && '
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
        v.SetDrill(pcbnew.FromMM(0.3)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('RAW_ACT'))
        b.Add(v)
        pcbnew.SaveBoard(str(d / 'm3.kicad_pcb'), b)
        issues, ev = gate.fill_freshness(d / 'm3.kicad_pcb')
        self.assertTrue(issues, ev)

    def test_equal_area_saved_fill_translation_rejects_then_native_refill_passes(self):
        import shutil
        import tempfile
        board = self.load()
        zone = next(z for z in board.Zones() if z.GetZoneName() == 'R10_GND_In2_CH1')
        layer = pcbnew.In2_Cu
        poly = pcbnew.SHAPE_POLY_SET(zone.GetFilledPolysList(layer))
        area = poly.Area()
        poly.Move(self.P(.1, 0)); zone.SetFilledPolysList(layer, poly)
        self.assertEqual(poly.Area(), area)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'm3.kicad_pcb'
            for suffix in ('.kicad_pro', '.kicad_dru'):
                shutil.copyfile(real_project() / ('m3' + suffix), path.with_suffix(suffix))
            pcbnew.SaveBoard(str(path), board)
            issues, evidence = gate.fill_freshness(path)
            self.assertTrue(any('In2.Cu' in issue and 'geometry' in issue for issue in issues), evidence)
            pcbnew.ZONE_FILLER(board).Fill(board.Zones())
            pcbnew.SaveBoard(str(path), board)
            self.assertEqual(gate.fill_freshness(path)[0], [])

    def test_j1_wire_entry(self):
        """R3-MEC-02: J1 turned away from the west face."""
        self.seeded('P-11', lambda b: b.FindFootprintByReference('J1').SetOrientationDegrees(90), 'J1 wires enter')

    def move(self, b, ref, dx, dy):
        f = b.FindFootprintByReference(ref)
        f.SetPosition(pcbnew.VECTOR2I(f.GetPosition().x + pcbnew.FromMM(dx), f.GetPosition().y + pcbnew.FromMM(dy)))

    def test_p11_all_db125_wire_room(self):
        for ref, dx in [('J400', -0.6), ('J410', 0.6), ('J420', 0.6), ('J9', 0.6), ('J122', 0.6)]:
            with self.subTest(ref=ref):
                self.seeded('P-11', lambda b: self.move(b, ref, dx, 0), 'wire room')

    def test_p11_j121_moved_west_loses_wire_room(self):
        """R7-GATE-04: J121 0.6 mm west leaves 4.35 mm of wire room, below WIRE_ROOM_R10 (4.95)."""
        self.assertEqual(gate.WIRE_ROOM_R10, 4.95)
        self.assertEqual(self.run_rule('P-11', self.load()), set())
        self.seeded('P-11', lambda b: self.move(b, 'J121', -0.6, 0), 'wire room')

    def test_f9_1_d8_moved_away(self):
        """OQ-2: D8 movement invalidates the electrical model even if the result still claims a pass."""
        self.assertEqual(self.run_rule('F9-1', self.load()), set())
        self.seeded('F9-1', lambda b: self.move(b, 'D8', 3, 0), 'D8')

    def test_f9_1_changed_feed_copper_invalidates_model(self):
        def narrow(b):
            track = next(t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'BAT_IN')
            track.SetWidth(pcbnew.FromMM(.2))
        self.seeded('F9-1', narrow, 'stale')

    def test_obsolete_arm_and_fuse_legends_rejected(self):
        self.assertEqual(gate.PINNED_TEXTS, (('B.Silkscreen', 'M3-ASSY-R10'),))
        for legend in ('J1 BAT 15A FUSE', 'J124 ARM LAST', 'J124 5A FAST 2S', 'ARM', 'ARM1', 'ARM CH1'):
            with self.subTest(legend=legend):
                def seed(b):
                    text = pcbnew.PCB_TEXT(b); text.SetLayer(pcbnew.B_SilkS); text.SetText(legend); b.Add(text)
                self.seeded('K-legends', seed, 'obsolete ARM terminal or fuse legend')

    def test_armed_side_extra_parts(self):
        """R7-GATE-03 / R7-SAF-01 seeds."""
        def r133(b):                                  # R133 rewired as a PYRO1_GATE - PYRO1_COLD pull-up
            self.pad(b, 'R133', '1').SetNet(b.FindNet('PYRO1_GATE')); self.pad(b, 'R133', '2').SetNet(b.FindNet('PYRO1_COLD'))
        self.seeded('S-1', r133, 'R133')
        self.seeded('S-3', r133, 'R133')
        self.seeded('S-1', lambda b: self.pad(b, 'TP122', '1').SetNet(b.FindNet('PYRO1_COLD')), 'TP122')
        self.seeded('S-1', lambda b: self.pad(b, 'TP122', '1').SetNet(b.FindNet('ARM1_SENSE_MID')), 'TP122')
        self.seeded('S-3', lambda b: self.pad(b, 'C129', '1').SetNet(b.FindNet('PYRO1_GATE')), 'C129')

    def test_misnamed_armed_net_is_caught(self):
        """R7-SAF-02: an armed net renamed to an MCU-side name has the wrong topology."""
        def seed(b):
            b.Add(pcbnew.NETINFO_ITEM(b, 'PYRO1_COLD_MCU'))
            for ref in ('D120', 'R131'):
                for p in b.FindFootprintByReference(ref).Pads():
                    if p.GetNetname() == 'PYRO1_COLD':
                        p.SetNet(b.FindNet('PYRO1_COLD_MCU'))
        self.seeded('S-1', seed, 'PYRO1_COLD_MCU')
        self.seeded('S-1', lambda b: self.pad(b, 'U1', '33').SetNet(b.FindNet('PYRO1_CONT')), 'PYRO1_CONT')

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

    # --- round 19 gate pass ---------------------------------------------------------------------------------------
    def test_r19_board_paste_and_mask_overrides_fail_k_lands(self):
        """R19-GATE-01: b19a (Q124's pads at a -0.1 mm board paste margin), a board paste ratio on U9's IN / OUT bars,
        a footprint mask margin on R134 and a pad that loses its paste layer each fail K-lands."""
        def margin(b):
            for pad in b.FindFootprintByReference('Q124').Pads():
                pad.SetLocalSolderPasteMargin(pcbnew.FromMM(-0.1))
        self.seeded('K-lands', margin, 'Q124.4: pad paste margin -0.100 mm, library none')

        def ratio(b):
            for n in ('5', '6'):
                self.pad(b, 'U9', n).SetLocalSolderPasteMarginRatio(-0.6)
        self.seeded('K-lands', ratio, 'U9.5: pad paste ratio -0.6, library -0.047')     # the library bar's own ratio
        self.seeded('K-lands', lambda b: b.FindFootprintByReference('R134').SetLocalSolderMaskMargin(pcbnew.FromMM(0.05)),
                    'R134: footprint mask margin 0.050 mm')

        def layers(b):
            pad = self.pad(b, 'Q124', '1')
            lset = pad.GetLayerSet(); lset.RemoveLayer(pcbnew.F_Paste); pad.SetLayerSet(lset)
        self.seeded('K-lands', layers, 'Q124.1: paste layers')

    def test_r19_r131_recode_fails_k_actuators_and_s4(self):
        """R19-GATE-02: b08e (R131 re-coded to C11702, the 1 kohm 0402WGF1001TCE, Value still 10k) fails the R131 pin
        (K-actuators) and the MPN value (S-4); a C127 / C129 code change fails the pin."""
        def recode(b):
            f = b.FindFootprintByReference('R131')
            f.SetField('LCSC', 'C11702'); f.SetField('Manufacturer Part', '0402WGF1001TCE')
        self.seeded('K-actuators', recode, 'R10 R131 must be the 10k 0402 cold pull-up')
        self.seeded('S-4', recode, "R131: Value '10k' but 0402WGF1001TCE (UNI-ROYAL) is 1000 ohm")
        for ref in ('C127', 'C129'):
            self.seeded('K-actuators', lambda b, ref=ref: b.FindFootprintByReference(ref).SetField('LCSC', 'C15195'),
                        f'R10 {ref} must be the 10nF 50V X7R sense filter capacitor')
        rep = gate.check_board(self.load(), real_project(), real_project() / 'm3.kicad_pcb', only={'S-4'})
        values = rep['rules']['S-4']['evidence']['mpn_values']
        self.assertGreaterEqual(values['decoded'], 150)
        self.assertEqual(sorted(values['not_decoded']), ['C84'])

    def test_r19_plane_neck_seed(self):
        """R19-GATE-03: b10b on the post-CAD board (an In2 keep-out leaving a 0.30 mm neck on the 3V3 buck finger)."""
        def neck(b):
            z3 = next(z for z in b.Zones() if z.GetZoneName() == 'R10_3V3_In2')
            fill = z3.GetFilledPolysList(pcbnew.In2_Cu)
            east = max(x / 100 for x in range(2200, 2420) if fill.Contains(self.P(x / 100, 72.6)))
            z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetLayer(pcbnew.In2_Cu); z.SetZoneName('R19_SEED_3V3_NECK')
            z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False)
            z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
            o = z.Outline(); o.NewOutline()
            for x, y in ((21.9, 72.4), (east - 0.3, 72.4), (east - 0.3, 72.8), (21.9, 72.8)):
                o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
            b.Add(z)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        self.seeded('K-plane', neck, 'via (23.100, 78.100) join(s) the main fill only through a neck under 0.5 mm')
        rep = gate.check_board(self.load(), real_project(), real_project() / 'm3.kicad_pcb', only={'K-plane'})
        necks = rep['rules']['K-plane']['evidence']['necks']['necks']['3V3 In2.Cu']
        self.assertGreaterEqual(min(n['width_mm'] for n in necks), 0.5)

    def test_r19_rail_runs_at_0_2_mm_fail_k_power(self):
        """R19-GATE-04: a 0.2 mm run on each R19 rail's current path (VLOGIC, PORT_5V3, CAM_5V, PORT_4V8, 3V3)."""
        for name in ('VLOGIC trunk', 'U400 OUT', 'CAM_5V out', 'J410 feed', 'U2 OUT', 'U401 IN'):
            spec = next(p for p in gate.POWER_PATHS if p['name'] == name)

            def neck(b, spec=spec):
                segs = gate.path_graph(b, spec['net'], spec['start'], spec['end'], spec.get('layers'))[0]
                max(segs, key=lambda t: t.GetLength()).SetWidth(pcbnew.FromMM(0.2))
            self.seeded('K-power', neck, f'{name}: {spec["net"]} track 0.200 mm wide')
        issues, ev = gate.power_paths(self.load())
        self.assertEqual(issues, [])
        for name in ('VLOGIC trunk', 'CAM_5V out', 'J410 feed', 'J420 feed', 'U401 OUT'):
            self.assertLessEqual(ev[name]['ipc_floor_mm'], next(p for p in gate.POWER_PATHS if p['name'] == name)['floor'])

    def second_in_via(self, b, dia, drill):
        """The legitimate second U9 IN via of seeds c01 / c01b, drawn cleanly on the post-CAD board: since D-R24-17 at
        the 1.0 mm F.Cu feed's chamfer end (17.5, 88.171), 1.021 mm below the IN via (17.5, 87.15)."""
        v = pcbnew.PCB_VIA(b); v.SetPosition(self.P(17.5, 88.171)); v.SetWidth(pcbnew.FromMM(dia))
        v.SetDrill(pcbnew.FromMM(drill)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('BAT_IN')); b.Add(v)
        t = pcbnew.PCB_TRACK(b); t.SetLayer(pcbnew.B_Cu); t.SetWidth(pcbnew.FromMM(1.0)); t.SetNet(b.FindNet('BAT_IN'))
        t.SetStart(self.P(17.5, 88.171)); t.SetEnd(self.P(17.5, 87.15)); b.Add(t)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())

    def test_r19_second_u9_in_via_passes(self):
        """R19-GATE-05: c01 (1.0 / 0.5 mm) and c01b (0.6 / 0.3 mm) second U9 IN vias pass K-power and S-9 with the fire
        path, K-power paths and native budget copper unchanged; route_check admits them with one PARALLEL_VIAS line."""
        import route_check as rc
        sys.path.insert(0, str(gate.ROOT / 'm3_design'))
        import r10_parts
        base = self.load()
        fire = {net: sorted(t.m_Uuid.AsString() for t in gate.fire_path(base, net, terms)[0])
                for net, terms in gate.FIRE_TERMINALS.items()}
        budget = r10_parts.native_fire_copper(base)
        for dia, drill in ((1.0, 0.5), (0.6, 0.3)):
            with self.subTest(via=(dia, drill)):
                b = self.load()
                self.second_in_via(b, dia, drill)
                for rid in ('K-power', 'S-9'):
                    self.assertEqual(self.run_rule(rid, b), set(), rid)
                self.assertEqual({net: sorted(t.m_Uuid.AsString() for t in gate.fire_path(b, net, terms)[0])
                                  for net, terms in gate.FIRE_TERMINALS.items()}, fire)
                self.assertEqual(r10_parts.native_fire_copper(b), budget)
                self.addCleanup(rc.set_profile, 'r8')
                rc.set_profile('r10')
                loops = [d for d in rc.scan(b) if d['cat'] == 'track_loop' and d['net'] == 'BAT_IN']
                self.assertTrue(loops)
                entry = ('BAT_IN', (17.5, 88.171), 'second U9 IN via beside (17.5, 87.15) (seed)')
                with patch.object(rc, 'PARALLEL_VIAS', rc.PARALLEL_VIAS + [entry]):
                    failing = [d for d in rc.scan(b) if rc.gated(d) and d['net'] == 'BAT_IN']
                self.assertEqual(failing, [])

    def test_r19_adversary_c01_drawing_keeps_fire_and_budget_copper(self):
        """R19-GATE-05: the adversary's c01 drawing (its loop hangs off J1.1's U9 branch) no longer becomes BAT_IN fire
        copper: S-9 and the native budget see the same single B.Cu segment."""
        sys.path.insert(0, str(gate.ROOT / 'm3_design'))
        import r10_parts
        b = self.load()
        # D-R24-17: the drawing re-attached to the new feed (F.Cu run at y 88.891 west of its chamfer, B.Cu IN trunk at x 18.25)
        for lay, a, c in ((pcbnew.F_Cu, (16.0, 88.891), (18.9, 88.891)), (pcbnew.B_Cu, (18.9, 88.891), (18.9, 86.65)),
                          (pcbnew.B_Cu, (18.9, 86.65), (18.25, 86.0))):
            t = pcbnew.PCB_TRACK(b); t.SetLayer(lay); t.SetWidth(pcbnew.FromMM(1.0)); t.SetNet(b.FindNet('BAT_IN'))
            t.SetStart(self.P(*a)); t.SetEnd(self.P(*c)); b.Add(t)
        v = pcbnew.PCB_VIA(b); v.SetPosition(self.P(18.9, 88.891)); v.SetWidth(pcbnew.FromMM(1.0))
        v.SetDrill(pcbnew.FromMM(0.5)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet('BAT_IN')); b.Add(v)
        segs = gate.fire_path(b, 'BAT_IN', gate.FIRE_TERMINALS['BAT_IN'])[0]
        self.assertEqual({b.GetLayerName(t.GetLayer()) for t in segs}, {'B.Cu'})
        self.assertEqual(r10_parts.native_fire_copper(b), r10_parts.native_fire_copper(self.load()))

    def test_r19_aux_feed_second_via(self):
        """Item 11: losing only the AUX feed's added via (30.5, 9.95) fails K-power (the feed's path is held to F.Cu)."""
        def drop(b):
            self.drop(b, [v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'PORT_4V8'
                          and v.GetPosition() == self.P(30.5, 9.95)][0])
        self.seeded('K-power', drop, 'J440 feed: 1 via(s) on the path; at least 2 required')

    def test_r19_word_centre_margins(self):
        """R19-GATE-06: every blocking word clears 1.0 mm on the real board, BAT / SWITCH are reported below it, and RADIO
        moved near the J410 / J420 seam fails."""
        rep = gate.check_board(self.load(), real_project(), real_project() / 'm3.kicad_pcb', only={'K-legends'})
        margins = {w.split("'")[1]: e['centre_margin'] for w, e in rep['rules']['K-legends']['evidence']['word_legends'].items()}
        self.assertTrue(all(margins[w] >= 1.0 for w in gate.WORD_CENTRE_BLOCKING), margins)
        self.assertTrue(margins['BAT'] < 1.0 and margins['SWITCH'] < 1.0, margins)

        def move(b):
            t = next(d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == 'RADIO')
            t.SetPosition(t.GetPosition() - self.P(0, 4.2))
        self.seeded('K-legends', move, "word legend 'RADIO'")
        b = self.load(); move(b)
        found, _ = gate.word_legends(b)
        self.assertTrue(any('RADIO' in i and 'must be nearer its own by 1.0 mm' in i for i in found), found)

    def test_r19_silk_text_allowlist(self):
        """R19-GATE-07: b21b ('BATT+' beside J121) and a Value field shown on silkscreen fail K-legends."""
        def batt(b):
            t = pcbnew.PCB_TEXT(b); t.SetText('BATT+'); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(self.P(1.55, 55.4))
            t.SetTextAngleDegrees(90); t.SetTextSize(self.P(1, 1)); t.SetTextThickness(pcbnew.FromMM(0.15)); b.Add(t)
        self.seeded('K-legends', batt, "silkscreen text 'BATT+'")

        def value(b):
            f = b.FindFootprintByReference('R134')
            f.Value().SetLayer(pcbnew.F_SilkS); f.Value().SetVisible(True)
        self.seeded('K-legends', value, 'R134 Value field')

    def test_r19_pour_debris_seed(self):
        """R19-RTE-01: U1.19's pour connection restored (the round 18 fragment, 1.693 mm^2) fails K-copper. D-R20-03
        (R20-RTE-02): so does U1.74's (the round 19 fragment, 0.282 mm^2 on its pin tip), and the board has no pour
        debris and no named entry left."""
        def fragment(b):
            self.pad(b, 'U1', '19').SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_INHERITED)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        self.seeded('K-copper', fragment, '1.693 mm^2 piece at (26.13, 52.34) with no via and only U1.19')

        def tip(b):
            self.pad(b, 'U1', '74').SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_INHERITED)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        self.seeded('K-copper', tip, '0.282 mm^2 piece')
        self.assertEqual(gate.POUR_DEBRIS, [])
        self.assertEqual(gate.pour_debris(self.load(), named=[])[0], [])

    def test_r19_stale_critical_reference_name_fails_k_reference(self):
        """R19-REQ-10: a name the R10 gates list that no board net carries (V3V3_SENSE back in AUD-2's list) fails."""
        import critical_reference as cr
        ctx = gate.make_ctx(self.load())
        with patch.object(gate, 'references', return_value=([], {})):
            self.assertEqual(gate.k_reference(ctx)[0], [])
            with patch.object(cr, 'R10_SLOW_RETURN_NETS', cr.R10_SLOW_RETURN_NETS | {'V3V3_SENSE'}):
                found = gate.k_reference(ctx)[0]
        self.assertTrue(any("stale critical_reference.R10_SLOW_RETURN_NETS entry 'V3V3_SENSE'" in i for i in found), found)

    def test_r20_designators_inside_a_large_neighbours_courtyard(self):
        """R20-MFG-02 / D-R20-06: the generator's courtyard test reaches courtyards of any size, so the rebuilt board has
        no designator nearer another part's courtyard (C400 moved, C94 and R461 hidden) and the gate names none; each
        round 19 spot (inside J440's / U1's / J430's courtyard) fails again, so does a designator moved into U1's far
        corner, and a named entry the board no longer meets is stale."""
        sys.path.insert(0, str(gate.ROOT / 'm3_design'))
        import r7_post
        import r8_post
        b = self.load()
        self.assertEqual(sorted(r7_post.courtyard_offenders(b)), [])
        self.assertEqual([f.GetReference() for f in b.GetFootprints() if r8_post.courtyard_fails(b, f)], [])
        issues, ev = gate.designator_courtyards(b)
        self.assertEqual((issues, ev['offenders']), ([], []))
        self.assertEqual(gate.DESIGNATOR_COURTYARD_R20, [])

        def back(ref, layer, xy, angle):                     # its round 19 spot, visible
            def seed(board):
                t = board.FindFootprintByReference(ref).Reference()
                t.SetVisible(True); t.SetLayer(layer); t.SetPosition(self.P(*xy)); t.SetTextAngleDegrees(angle)
            return seed
        for ref, layer, xy, angle, other in (('C400', pcbnew.F_SilkS, (9.743, 6.048), 90, 'J440'),
                                             ('C94', pcbnew.F_SilkS, (32.103, 51.304), 90, 'U1'),
                                             ('R461', pcbnew.B_SilkS, (22.258, 18.211), 0, 'J430')):
            self.seeded('K-legends', back(ref, layer, xy, angle), f"designator {ref} is nearer {other}'s courtyard")

        def corner(board):                  # ink centre 8.1 mm from U1's courtyard centre in x and y
            t = board.FindFootprintByReference('R165').Reference()
            t.SetPosition(self.P(31.1, 51.1)); t.SetTextAngleDegrees(0)
        self.seeded('K-legends', corner, "designator R165 is nearer U1's courtyard")
        stale = [('C400', 'J440', 0.082, 0.151, 'round 19 entry')]
        self.assertIn("stale DESIGNATOR_COURTYARD_R20 entry ('C400'", ' '.join(gate.designator_courtyards(b, named=stale)[0]))

    def test_r20_fab_reference_crosses_its_own_fab_outline(self):
        """R20-MFG-03 / D-R20-07: no Fab reference crosses its own Fab outline and no entry is named; R165's at 1.0 mm
        fails, each of the six fixed parts' round 19 text fails again (C445 0.8 mm, D440 / D441 0.4 mm on their bodies,
        C123 centred on its pin-1 mark, R119 1.0 mm, R173 0.1 mm east), and an entry for a clear part is stale."""
        sys.path.insert(0, str(gate.ROOT / 'm3_design'))
        import r5_post as silk
        b = self.load()
        issues, ev = gate.fab_ref_crossings(b)
        self.assertEqual((issues, ev['crossings']), ([], {}))
        self.assertEqual(gate.FAB_REF_CROSSINGS_R20, {})

        def text(ref, mm, dx=0.0, dy=0.0):
            def seed(board):
                f = board.FindFootprintByReference(ref)
                t = silk._fab_ref(f)
                t.SetTextSize(self.P(mm, mm)); t.SetTextThickness(pcbnew.FromMM(0.15 * mm))
                t.SetPosition(f.GetPosition() + self.P(dx, dy))
            return seed
        self.seeded('K-legends', text('R165', 1.0), 'Fab reference R165 crosses its own Fab outline')
        for ref, mm, dx in (('C445', 0.8, 0.0), ('D440', 0.4, 0.0), ('D441', 0.4, 0.0), ('C123', 0.4, 0.0),
                            ('R119', 1.0, 0.0), ('R173', 0.4, 0.1)):
            b = self.load()
            text(ref, mm, dx)(b)
            found = gate.fab_ref_crossings(b)[0]
            self.assertTrue(any(i.startswith(f'Fab reference {ref} crosses') for i in found), (ref, found))
        self.assertEqual([i.split(' (')[0] for i in gate.fab_ref_crossings(self.load(), named={'C445': (0.1915, 'x')})[0]],
                         ['stale FAB_REF_CROSSINGS_R20 entry C445'])

    def test_r20_s8_terminal_inner_rings(self):
        """D-R20-05 (R20-SAF-05): S-8 measures the inner ring a protected barrel keeps; J121.1 and J400.2 keep none (their
        footprints drop unconnected inner rings), and restoring them brings back round 19's 0.750 mm rings (GND at
        J121.1, In2 RAW_PROTECTED at J400.2), which fail. J121.2 (PYRO1_IGN, GND exempt) keeps its rings."""
        b = self.load()
        self.assertEqual(self.run_rule('S-8', b), set())
        flashed = lambda board, ref, num: [board.GetLayerName(lay) for lay in (pcbnew.In1_Cu, pcbnew.In2_Cu)  # noqa: E731
                                          if self.pad(board, ref, num).FlashLayer(lay)]
        self.assertEqual((flashed(b, 'J121', '1'), flashed(b, 'J400', '2')), ([], []))
        self.assertEqual(flashed(b, 'J121', '2'), ['In1.Cu', 'In2.Cu'])

        def rings(ref, num):
            def seed(board):
                self.pad(board, ref, num).Padstack().SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL)
                pcbnew.ZONE_FILLER(board).Fill(board.Zones())
            return seed
        self.seeded('S-8', rings('J121', '1'), 'GND copper on In1.Cu is 0.750 mm from the J121.1 inner ring')
        self.seeded('S-8', rings('J400', '2'), 'RAW_PROTECTED copper on In2.Cu is 0.750 mm from the J400.2 inner ring')

    def test_r20_fb_tap_survives_one_via_open(self):
        """D-R20-02 (R20-PWR-02) / D-R24-09: U401's feedback divider sits on B.Cu beside U401, so R402.1 (its top),
        U401.3 (FB) and R403.2 (its bottom) join U401's pins with no via: no single point. The OUT run's T (29.75,
        12.85) lies 0.075 mm inside R402.1's land, so its three pieces (the link from U401's pins, the C406.1 drop and
        the stub to the land centre) all reach the land; with the three cut, K-power names R402.1 as not joined (round
        19's via-only route and round 20's extra via are gone)."""
        issues, ev = gate.single_via_opens(self.load())
        self.assertEqual(issues, [])
        for tap in ('R402.1', 'U401.3', 'R403.2'):
            self.assertEqual(ev[tap]['single_points'], [], tap)

        def cut(board):
            for a in ((28.75, 12.85), (29.75, 11.65), (30.075, 12.85)):
                self.drop(board, next(t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK'
                                      and t.GetNetname() == 'PORT_4V8' and {tuple(t.GetStart()), tuple(t.GetEnd())}
                                      == {tuple(self.P(29.75, 12.85)), tuple(self.P(*a))}))
        self.seeded('K-power', cut, "R402.1 (U401's feedback divider top (R20-PWR-02)) is not joined to U401.1/U401.2")

    def test_r20_s6_sees_aux_and_the_switch_enable_chain(self):
        """R20-SAF-02: each new S-6 pattern seeded on the board. AUX_ (port): the reviewer's AUX_TX_WIRE track 0.100 mm
        from the PYRO1_OUT run, and an AUX pad on R165; BAT_ENABLE and BAT_SW_ (protected): a GPS track 0.100 mm from
        each, and R80 joining a GPS net to BAT_SW_SOURCE. The real board passes."""
        self.assertEqual(self.run_rule('S-6', self.load()), set())

        def track(net, layer, a, c):
            def seed(board):
                t = pcbnew.PCB_TRACK(board); t.SetLayer(layer); t.SetWidth(pcbnew.FromMM(0.2))
                t.SetStart(self.P(*a)); t.SetEnd(self.P(*c)); t.SetNet(board.FindNet(net)); board.Add(t)
            return seed
        self.seeded('S-6', track('AUX_TX_WIRE', pcbnew.B_Cu, (12.0, 56.3), (13.0, 56.3)),
                    'AUX_TX_WIRE track (12.0, 56.3) to PYRO1_OUT')
        self.seeded('S-6', track('GPS_TX_WIRE', pcbnew.F_Cu, (21.6, 70.0), (21.6, 71.0)),
                    'GPS_TX_WIRE track (21.6, 70.0) to BAT_ENABLE')
        self.seeded('S-6', track('GPS_TX_WIRE', pcbnew.F_Cu, (9.0, 67.3), (10.0, 67.3)),
                    'GPS_TX_WIRE track (9.0, 67.3) to BAT_SW_RETURN')

        def pad_net(ref, num, net):
            return lambda board: self.pad(board, ref, num).SetNet(board.FindNet(net))
        self.seeded('S-6', pad_net('R165', '1', 'AUX_TX_WIRE'),
                    "R165 joins port nets ['AUX_TX_WIRE'] to pyro / arming nets ['BAT_ENABLE']")
        self.seeded('S-6', pad_net('R80', '1', 'GPS_TX_WIRE'),
                    "R80 joins port nets ['GPS_TX_WIRE'] to pyro / arming nets ['BAT_SW_SOURCE']")


    # ------------------------------------------------------------------------------------------------ round 21 fix pass
    def test_r21_jlc_hole_table_pinned_in_k_rules(self):
        """D-R21-01 (R21-PWR-02 / R21-GATE-02): the DRU holds JLC's hole table (via hole to inner copper 0.2, PTH pad
        hole to inner copper 0.3, PTH hole to outer track 0.28, pad hole to hole 0.45 mm) with the inner PTH rule at
        0.55 mm; the inner rule at 0.25 mm, dropped or narrowed, the outer rule or the hole-to-hole rule looser, a later
        rule that can override the inner one and a hole rule under 0.2 mm each fail, and the 0.25 mm inner rule fails
        K-rules itself even with the DRU re-pinned."""
        import hashlib
        folder = real_project()
        dru = (folder / 'm3.kicad_dru').read_text()
        issues, ev = gate.jlc_hole_table(dru)
        self.assertEqual(issues, [])
        self.assertEqual([(e['rule'], e['min_mm'], e['jlc_min_mm']) for e in ev],
                         [('General copper to hole clearance', 0.25, 0.2),
                          ('JLC inner-layer PTH pad hole to copper', 0.55, 0.3),
                          ('JLC outer-layer PTH hole to track', 0.28, 0.28), ('JLC pad hole to hole', 0.45, 0.45)])
        a = dru.index('(rule "JLC inner-layer PTH pad hole to copper"')
        block = dru[a:dru.index('(rule "JLC outer-layer PTH hole to track"')]
        seeds = {
            'inner at 0.25 mm': dru.replace(block, block.replace('(min 0.55mm)', '(min 0.25mm)')),
            'inner dropped': dru.replace(block, ''),
            'inner narrowed': dru.replace(block, block.replace(" && (B.Type != 'Pad' || B.Pad_Type == 'Through-hole')",
                                                               '')),
            'outer at 0.25 mm': dru.replace('(min 0.28mm)', '(min 0.25mm)'),
            'hole to hole at 0.4 mm': dru.replace('(constraint hole_to_hole (min 0.45mm))',
                                                  '(constraint hole_to_hole (min 0.4mm))'),
            'later inner override': dru + '\n(rule "later"\n  (layer inner)\n  (condition "A.Type == \'Pad\'")\n'
                                          '  (constraint hole_clearance (min 0.25mm)))\n',
            'general under 0.2 mm': dru.replace('(constraint hole_clearance (min 0.25mm))',
                                                '(constraint hole_clearance (min 0.15mm))', 1),
        }
        for name, text in seeds.items():
            with self.subTest(seed=name):
                self.assertNotEqual(text, dru)
                self.assertTrue(gate.jlc_hole_table(text)[0], name)
        # an outer-layer rule cannot override the inner one: a later 0.28 mm outer rule is not an inner finding
        self.assertEqual(gate.jlc_hole_table(dru + '\n(rule "later outer"\n  (layer outer)\n  (condition "A.Type == '
                                             '\'Pad\'")\n  (constraint hole_clearance (min 0.28mm)))\n')[0], [])
        path, text = folder / 'm3.kicad_dru', seeds['inner at 0.25 mm']
        try:
            path.write_text(text)
            with patch.object(gate, 'DRU_SHA256', hashlib.sha256(text.encode('utf-8')).hexdigest()):
                found = self.run_rule('K-rules', self.load(), folder / 'm3.kicad_pcb')
            self.assertTrue(any('JLC table' in i and "0.25 mm is below JLC's 0.3 mm" in i for i in found), sorted(found))
        finally:
            path.write_text(dru)

    def test_r21_pth_holes_clear_inner_copper(self):
        """D-R21-01 (R21-PWR-02): every plated pad hole wall is >= 0.3 mm (JLC) from foreign In1 / In2 copper on the
        board, 0.550 mm at J1.2 (In2 RAW_PROTECTED) and J400.2 (In1 GND) (round 20: 0.250); refilled under the round 20
        DRU (no inner PTH rule, the general 0.25 mm) both come back at 0.25 mm and K-rules names them."""
        import shutil
        import tempfile
        issues, ev = gate.pth_inner_copper(self.load())
        self.assertEqual(issues, [])
        self.assertGreaterEqual(min(v[0] for pad in ev.values() for v in pad.values()), 0.549)
        self.assertAlmostEqual(ev['J1.2']['In2.Cu'][0], 0.55, delta=0.002)
        self.assertAlmostEqual(ev['J400.2']['In1.Cu'][0], 0.55, delta=0.002)
        folder = real_project()
        d = Path(tempfile.mkdtemp(prefix='r10_pth_'))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        for name in ('m3.kicad_pcb', 'm3.kicad_pro'):
            shutil.copyfile(folder / name, d / name)
        dru = (folder / 'm3.kicad_dru').read_text()
        cut = dru.index('(rule "JLC inner-layer PTH pad hole to copper"'), dru.index('(rule "JLC outer-layer PTH')
        (d / 'm3.kicad_dru').write_text(dru[:cut[0]] + dru[cut[1]:])
        board = pcbnew.LoadBoard(str(d / 'm3.kicad_pcb'))
        self.assertTrue(pcbnew.ZONE_FILLER(board).Fill(board.Zones()))
        found = gate.pth_inner_copper(board)[0]
        for pad, net, layer in (('J1.2', 'RAW_PROTECTED', 'In2.Cu'), ('J400.2', 'GND', 'In1.Cu')):
            self.assertTrue(any(f'the {pad} ' in i and f'is 0.25' in i and f'{net} fill on {layer}' in i for i in found),
                            (pad, found))
        new = self.run_rule('K-rules', board, d / 'm3.kicad_pcb')
        self.assertTrue(any('J1.2' in i and "JLC's 0.3 mm inner-layer PTH" in i for i in new), sorted(new)[:4])

    def test_r21_regulator_taps_survive_one_via_open(self):
        """D-R21-02 (R21-PWR-01 / R21-GATE-01): every regulator FB / OVLO / EN / ILIM tap in SINGLE_OPEN_TAPS reaches
        its source with any one via open, except for the exact SINGLE_OPEN_EXCEPTIONS entries, each still met. U2.1 has
        a second path (the f01b run into R89's via); without it the via (23.2, 68.6) is a single point K-power names.
        An entry the board no longer meets is stale, and a tap whose entry is dropped fails."""
        issues, ev = gate.single_via_opens(self.load())
        self.assertEqual(issues, [])
        self.assertEqual(len(gate.SINGLE_OPEN_TAPS), 40)    # 26 (round 21) + 7 (D-R22-02) + 5 (D-R23-01 / -02) + 2 (D-R23-11)
        self.assertEqual(set(ev), {t[1] for t in gate.SINGLE_OPEN_TAPS})
        # D-R24-02 / -03 / -04 / -07 / -08 / -09 / -10: second vias (and U401's divider beside it) leave these single points
        self.assertEqual({tap: e['single_points'] for tap, e in ev.items() if e['single_points']}, {
            'R81.1': ['via BAT_ENABLE (17.10, 82.80)'], 'C87.1': ['via BAT_ENABLE (17.10, 82.80)'],
            'R87.1': ['via USB_LIMITED (22.00, 62.25)'],
            'R85.1': ['via USB_ILIM (14.82, 26.00)'], 'R85.2': ['via GND (9.00, 27.84)'],
            'U10.2': ['via GND (9.00, 27.84)'], 'R7.2': ['via GND (9.00, 27.84)'],
            'R8.2': ['via GND (9.95, 30.60)'], 'U1.48': ['via VCAP1 (29.25, 38.00)'],
            'U4.6': ['via GND (16.75, 47.60)'], 'U4.7': ['via GND (16.75, 47.60)']})

        def no_run(board):
            self.drop(board, next(t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == '3V3'
                                  and {tuple(t.GetStart()), tuple(t.GetEnd())}
                                  == {tuple(self.P(24.05, 68.95)), tuple(self.P(23.0, 70.0))}))
        u2 = [t for t in gate.SINGLE_OPEN_TAPS if t[1] == 'U2.1']
        board = self.load()
        no_run(board)
        self.assertEqual(gate.single_via_opens(board, taps=u2)[0],
                         ["U2.1 (U2's FB / output-sense pin (R21-PWR-01)) hangs on one via: opening via 3V3 (23.20, 68.60) "
                          'cuts it off from L1.2'])
        self.assertEqual(gate.single_via_opens(self.load(), taps=u2,
                                               exceptions=[('U2.1', 'via 3V3 (23.20, 68.60)', 'round 20')])[0],
                         ['stale SINGLE_OPEN_EXCEPTIONS entry U2.1 / via 3V3 (23.20, 68.60) (round 20)'])
        for tap, via, why in (('R85.1', 'via USB_ILIM (14.82, 26.00)', "U10's ILIM"),
                              ('R81.1', 'via BAT_ENABLE (17.10, 82.80)', "U9's EN pull-down (R20-SAF-01)")):
            with self.subTest(tap=tap):
                one = [t for t in gate.SINGLE_OPEN_TAPS if t[1] == tap]
                self.assertEqual(gate.single_via_opens(self.load(), taps=one, exceptions=[])[0],
                                 [f'{tap} ({why}) hangs on one via: opening {via} cuts it off from {one[0][2][0]}'])

    def test_r21_en_pull_down_and_filter_at_u9(self):
        """D-R21-05 (R21-SAF-01): R81 and C87 sit on the F.Cu EN run at U9's end, pads 1 on the run (C87.1 on its last
        bend) and pads 2 in the F.Cu GND of U9.8's via, so the via (17.1, 82.8) is the only one between them and U9.1
        (3.890 / 2.013 mm of track; round 20: three vias, 20.920 / 24.295 mm); the switch-end stubs and the GND via
        (20.706, 65.619), 0.196 mm from R134.2 (RAW_ACT), are gone. Round 20's two switch-end vias, as exceptions, are
        stale."""
        b = self.load()
        for ref, xy in (('R81', (18.8482, 80.0)), ('C87', (18.7232, 81.8768))):
            f = b.FindFootprintByReference(ref)
            self.assertFalse(f.IsFlipped(), ref)
            self.assertEqual(f.GetPosition(), self.P(*xy), ref)
            self.assertEqual([p.GetNetname() for p in sorted(f.Pads(), key=lambda q: q.GetNumber())], ['BAT_ENABLE', 'GND'])
        self.assertFalse([v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetPosition() == self.P(20.706, 65.619)])
        self.assertFalse([t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'BAT_ENABLE'
                          and self.P(19.675, 65.0) in (t.GetStart(), t.GetEnd())])
        taps = [t for t in gate.SINGLE_OPEN_TAPS if t[1] in ('R81.1', 'C87.1')]
        old = [(tap, via, 'round 20') for tap in ('R81.1', 'C87.1')
               for via in ('via BAT_ENABLE (19.68, 66.60)', 'via BAT_ENABLE (21.30, 68.90)')]
        found = gate.single_via_opens(b, taps=taps, exceptions=list(gate.SINGLE_OPEN_EXCEPTIONS) + old)[0]
        self.assertEqual(len(found), 4)
        self.assertTrue(all(i.startswith('stale SINGLE_OPEN_EXCEPTIONS entry') for i in found), found)

    def test_r21_tab_keepout_and_bands_held(self):
        """D-R21-06 (R21-GATE-03): the west aft In2 keep-out is pinned (name, layer, outline, fill-only) and the non-GND
        inner copper under the four tab bands is the recorded none / none / RAW_PROTECTED 7.497 + PORT_5V3 3.077 /
        RAW_PROTECTED 12.244 mm^2. The gate lens's d07 (keep-out deleted and refilled: 12.498 mm^2 of In2 3V3 under the
        tab) fails, as do a moved outline corner and a keep-out that also bars tracks; a figure above the board's is
        stale."""
        b = self.load()
        issues, ev = gate.tab_keepouts(b)
        self.assertEqual(issues, [])
        self.assertEqual(ev['bands'], {'west aft': {}, 'west forward': {},
                                       'east aft': {'In2.Cu PORT_5V3': 3.077, 'In2.Cu RAW_PROTECTED': 7.497},
                                       'east forward': {'In2.Cu RAW_PROTECTED': 12.244}})
        keepout = lambda board: next(z for z in board.Zones() if z.GetZoneName() == 'R20_TAB_KEEPOUT_WEST_AFT')  # noqa: E731

        def d07(board):
            self.drop(board, keepout(board))
            board.BuildConnectivity()
            pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        self.seeded('K-plane', d07, '3V3 on In2.Cu under the west aft tab band (0.0-3.0, 12.5-17.5) is 12.498 mm^2')
        self.seeded('K-plane', lambda board: keepout(board).Outline().SetVertex(1, self.P(2.0, 12.5)),
                    'tab keep-out R20_TAB_KEEPOUT_WEST_AFT outline')
        self.seeded('K-plane', lambda board: keepout(board).SetDoNotAllowTracks(True), 'pinned fill-only')
        bands = [(n, box, {**rec, ('In2.Cu', 'RAW_PROTECTED'): 13.0} if n == 'east forward' else rec)
                 for n, box, rec in gate.TAB_BANDS_R10]
        self.assertEqual(gate.tab_keepouts(b, bands=bands)[0],
                         ['stale TAB_BANDS_R10 figure: RAW_PROTECTED on In2.Cu under the east forward tab band is '
                          '12.244 mm^2, recorded 13.000 (re-record it)'])

    def test_r21_port_clamps_beside_their_pins(self):
        """D-R21-07 (R21-GATE-04): every port clamp is <= 4.5 mm of track from its terminal pin without passing the 1 k
        resistor (3.864-4.388 mm centre to centre; D-R24-17's chamfer at J440's clamp corners took 0.211 mm off each;
        D-R24-11's J400.2 clamp D402, on the screw side of R165, 4.114 mm);
        the gate lens's d08 (D440 back on F.Cu at F(13.9, 17.2), round 19's run) fails, and so does a clamp re-fed from
        its resistor's far side."""
        issues, ev = gate.port_clamps(self.load())
        self.assertEqual(issues, [])
        self.assertEqual({k: v[1] for k, v in ev.items()},
                         {'J410.3': 4.288, 'J410.4': 4.388, 'J420.3': 3.975, 'J420.4': 3.975, 'J440.3': 3.864,
                          'J440.4': 3.964, 'J9.3': 3.975, 'J9.4': 3.975, 'J400.2': 4.114})

        def track(board, net, a, c):
            return next(t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net
                        and {tuple(t.GetStart()), tuple(t.GetEnd())} == {tuple(self.P(*a)), tuple(self.P(*c))})

        def add(board, net, layer, a, c):
            t = pcbnew.PCB_TRACK(board); t.SetLayer(layer); t.SetWidth(pcbnew.FromMM(0.2))
            t.SetStart(self.P(*a)); t.SetEnd(self.P(*c)); t.SetNet(board.FindNet(net)); board.Add(t)

        def via(board, net, xy):
            v = pcbnew.PCB_VIA(board); v.SetPosition(self.P(*xy)); v.SetWidth(pcbnew.FromMM(0.5))
            v.SetDrill(pcbnew.FromMM(0.3)); v.SetNet(board.FindNet(net)); board.Add(v)
            return v

        def d08(board):
            for t in (track(board, 'AUX_TX_WIRE', (7.4, 18.0), (4.81, 18.0)),
                      track(board, 'AUX_TX_WIRE', (4.81, 18.0), (4.45, 18.36)),
                      track(board, 'AUX_TX_WIRE', (4.45, 18.36), (4.45, 19.125)),
                      track(board, 'GND', (4.45, 19.775), (3.75, 19.775)),
                      next(v for v in board.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND'
                           and v.GetPosition() == self.P(3.75, 19.775))):
                self.drop(board, t)
            f = board.FindFootprintByReference('D440')
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            f.SetPosition(self.P(13.9, 17.2)); f.SetOrientationDegrees(0)
            add(board, 'AUX_TX_WIRE', pcbnew.F_Cu, (13.575, 18.0), (13.575, 17.2))
            add(board, 'GND', pcbnew.F_Cu, (14.225, 17.2), (14.225, 16.45)); via(board, 'GND', (14.225, 16.45))
        self.seeded('K-ports', d08, 'J440.3 (AUX_TX_WIRE): its clamp D440.1 is 6.975 mm of track from the pin')

        def behind(board):            # J440.3's B.Cu run to D440 cut at the pin; D440 fed from R471.2 instead
            self.drop(board, track(board, 'AUX_TX_WIRE', (7.4, 18.0), (4.81, 18.0)))
            add(board, 'AUX_TX_WIRE', pcbnew.F_Cu, (15.275, 18.0), (15.275, 19.5)); via(board, 'AUX_TX_WIRE', (15.275, 19.5))
            add(board, 'AUX_TX_WIRE', pcbnew.B_Cu, (15.275, 19.5), (4.81, 18.0))
        self.seeded('K-ports', behind, 'J440.3 (AUX_TX_WIRE): its clamp D440.1 is reached only through R471')

    def test_r21_fab_references_present_readable_and_apart(self):
        """D-R21-08 (R21-GATE-05): every footprint has one visible Fab ${REFERENCE} on its own side, >= 0.3 mm high,
        clear of every other footprint's Fab outline and reference, and LS120's '+' / '-' are the only other Fab texts.
        The gate lens's d06a (Q120's deleted), d06b (R134's as the literal 'R143'), d06d (R120's on Q120's body) and
        d06e (R119's 0.1 mm high) fail, and so do a stray Fab text, a reference on the other side's Fab layer and one
        wholly on another part's body (R81's on C84's can)."""
        b = self.load()
        issues, ev = gate.fab_ref_crossings(b)
        self.assertEqual(issues, [])
        self.assertEqual((ev['fab_references_checked'], ev['neighbour_crossings']), (len(list(b.GetFootprints())), []))
        self.assertAlmostEqual(ev['least_height_mm'], 0.3)
        ref = lambda board, r: next(g for g in board.FindFootprintByReference(r).GraphicalItems()  # noqa: E731
                                    if isinstance(g, pcbnew.PCB_TEXT) and g.GetText() == '${REFERENCE}')

        def d06a(board):
            f, t = board.FindFootprintByReference('Q120'), ref(board, 'Q120')
            f.Remove(t)
            t.thisown = False
        self.seeded('K-legends', d06a, 'Q120 carries 0 Fab references')       # through the rule; the rest direct

        def d06e(board):
            t = ref(board, 'R119'); t.SetTextSize(self.P(0.1, 0.1)); t.SetTextThickness(pcbnew.FromMM(0.015))

        def stray(board):
            f = board.FindFootprintByReference('C87')
            t = pcbnew.PCB_TEXT(f); t.SetText('R81'); t.SetLayer(pcbnew.F_Fab); t.SetPosition(f.GetPosition()); f.Add(t)
        for name, seed, word in (
                ('d06b', lambda board: ref(board, 'R134').SetText('R143'), "Fab text ['R143'] on R134"),
                ('d06d', lambda board: ref(board, 'R120').SetPosition(self.P(13.5, 72.6)),
                 "Fab reference R120 crosses Q120's Fab outline"),
                ('d06e', d06e, 'Fab reference R119 is 0.100 mm high'),
                ('stray', stray, "Fab text ['R81'] on C87"),
                ('inside', lambda board: ref(board, 'R81').SetPosition(self.P(27.5, 76.0)),      # on C84's can
                 "Fab reference R81 crosses C84's Fab outline box (inside it)"),
                ('side', lambda board: ref(board, 'R81').SetLayer(pcbnew.B_Fab),
                 'Fab reference R81 is on B.Fab, not its own side F.Fab')):
            with self.subTest(seed=name):
                board = self.load()
                seed(board)
                found = gate.fab_ref_crossings(board)[0]
                self.assertTrue(any(i.startswith(word) for i in found), found)


    # ------------------------------------------------------------------------------------------------ round 22 pass
    def test_r22_jlc_board_holes(self):
        """D-R22-01 (R22-REQUIREMENTS-02): K-rules measures the board against the rest of JLC's hole rows, whatever the
        DRU says: plated holes >= 0.15 mm, PTH rings >= 0.20 mm, via rings >= 0.05 mm, non-plated holes >= 0.50 mm,
        NPTH copper rings >= 0.45 mm (none on this board) and NPTH hole to copper >= 0.2 mm (J3's 0.200 mm to its GND
        lands, at the limit). The lens's seeds (J122.5 ring 0.10 mm, a J2 NPTH hole at 0.40 mm) fail, and so do a
        0.18 mm ring, a 0.025 mm via ring, a 0.1 mm via hole, a 0.20 mm NPTH copper ring and a track 0.1 mm from an
        NPTH hole."""
        issues, ev = gate.jlc_board_holes(self.load())
        self.assertEqual(issues, [])
        least = {k: v[0] for k, v in ev['least'].items()}
        self.assertEqual((least['plated_hole'], least['pth_ring'], least['via_ring'], least['npth_hole']),
                         (0.3, 0.2, 0.1, 0.6))
        self.assertAlmostEqual(least['npth_to_copper'], 0.2, delta=0.0015)
        self.assertTrue(ev['least']['npth_to_copper'][1].startswith('J3 NPTH'))
        self.assertNotIn('npth_ring', least)
        P = self.P

        def via(board):
            return next(v for v in board.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'USB_ILIM'
                        and v.GetPosition() == P(14.825, 26.0))

        def npth(board):
            return min((p for p in board.FindFootprintByReference('J2').Pads()
                        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH), key=lambda p: (p.GetPosition().x, p.GetPosition().y))

        def small_via(board):
            v = via(board); v.SetDrill(pcbnew.FromMM(0.1)); v.SetWidth(pcbnew.FromMM(0.3))

        def near(board):                    # a GND track whose edge is 0.1 mm from the NPTH hole wall
            p = npth(board); c, r = p.GetPosition(), p.GetDrillSize().x // 2
            t = pcbnew.PCB_TRACK(board); t.SetLayer(pcbnew.F_Cu); t.SetWidth(pcbnew.FromMM(0.2)); t.SetNet(board.FindNet('GND'))
            x = c.x + r + pcbnew.FromMM(0.2)
            t.SetStart(pcbnew.VECTOR2I(x, c.y - pcbnew.FromMM(0.5))); t.SetEnd(pcbnew.VECTOR2I(x, c.y + pcbnew.FromMM(0.5)))
            board.Add(t)
        j122_5 = lambda board, d: board.FindFootprintByReference('J122').FindPadByNumber('5').SetDrillSize(P(d, d))  # noqa: E731
        for name, seed, word in (
                ('ring 0.10', lambda b: j122_5(b, 1.7), 'JLC holes: J122.5 annular ring 0.100 mm on F.Cu'),
                ('ring 0.18', lambda b: j122_5(b, 1.54), 'JLC holes: J122.5 annular ring 0.180 mm'),
                ('via ring', lambda b: via(b).SetDrill(pcbnew.FromMM(0.45)),
                 'JLC holes: via USB_ILIM (14.82, 26.00) ring 0.025 mm'),
                ('via hole', small_via, 'JLC holes: via USB_ILIM (14.82, 26.00) hole 0.100 mm'),
                ('npth 0.40', lambda b: npth(b).SetDrillSize(P(0.4, 0.4)),
                 'JLC holes: J2 NPTH (2.46, 39.40) non-plated hole 0.400 mm'),
                ('npth ring', lambda b: npth(b).SetSize(P(1.391, 1.391)),
                 'JLC holes: J2 NPTH (2.46, 39.40) NPTH pad ring 0.200 mm'),
                ('npth to copper', near, 'JLC holes: J2 NPTH (2.46, 39.40) is 0.1')):
            with self.subTest(seed=name):
                board = self.load()
                seed(board)
                found = gate.jlc_board_holes(board)[0]
                self.assertTrue(any(i.startswith(word) for i in found), found)
        self.seeded('K-rules', lambda b: npth(b).SetDrillSize(P(0.4, 0.4)), "non-plated hole 0.400 mm is under JLC's")
        self.seeded('K-rules', lambda b: j122_5(b, 1.7), "J122.5 annular ring 0.100 mm on F.Cu is under JLC's 0.2 mm")

    def test_r22_monitor_and_ic_ground_taps(self):
        """D-R22-02 (R22-POWER-01 / -02) / D-R24-07 / -08: the TPS2553 GND pins, R8.2 and the power-state monitor taps
        are single-open taps. Since round 24 U402.2 (with R430.2), R60.1 (PA6), U1.28 (PA4) and R91.1 have a second via
        and no entry; U10.2 (with R7.2, R85.2) and R8.2 keep theirs (measured). With its second via dropped (kept
        referenced) each fixed tap hangs on the first again and fails naming it; an entry the board does not meet is
        stale."""
        taps = {t[1]: t for t in gate.SINGLE_OPEN_TAPS}
        self.assertEqual((len(gate.SINGLE_OPEN_TAPS), len(gate.SINGLE_OPEN_EXCEPTIONS)), (40, 11))   # D-R24: 22 -> 11
        kept = {'U10.2': 'via GND (9.00, 27.84)', 'R7.2': 'via GND (9.00, 27.84)', 'R8.2': 'via GND (9.95, 30.60)'}
        fixed = {'U402.2': ('GND', (32.3, 60.1), 'via GND (32.30, 59.50)'),
                 'R60.1': ('VLOGIC', (34.5, 62.4), 'via VLOGIC (34.50, 63.00)'),
                 'U1.28': ('LOGIC_SOURCE_ST', (30.45, 51.4), 'via LOGIC_SOURCE_ST (30.85, 51.80)'),
                 'R91.1': ('3V3', (28.1, 59.4), 'via 3V3 (28.10, 60.00)')}
        b = self.load()
        issues, ev = gate.single_via_opens(b, taps=[taps[t] for t in [*kept, *fixed]])
        self.assertEqual(issues, [])
        self.assertEqual({t: ev[t]['single_points'] for t in [*kept, *fixed]},
                         {**{t: [v] for t, v in kept.items()}, **{t: [] for t in fixed}})
        for tap in ('R85.2', 'U10.2'):
            self.assertIn("floats the TPS2553's ground", next(x[2] for x in gate.SINGLE_OPEN_EXCEPTIONS if x[0] == tap))
        for tap, (net, second, first) in fixed.items():
            with self.subTest(tap=tap):
                board = self.load()
                self.drop(board, next(v for v in board.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == net
                                      and v.GetPosition() == self.P(*second)))
                pcbnew.ZONE_FILLER(board).Fill(board.Zones())
                t = taps[tap]
                self.assertEqual(gate.single_via_opens(board, taps=[t])[0],
                                 [f'{tap} ({t[3]}) hangs on one via: opening {first} cuts it off from {"/".join(t[2])}'])
        extra = list(gate.SINGLE_OPEN_EXCEPTIONS) + [('R60.1', 'via VLOGIC (29.80, 67.70)', 'not met')]
        self.assertEqual(gate.single_via_opens(b, taps=[taps['R60.1']], exceptions=extra)[0],
                         ['stale SINGLE_OPEN_EXCEPTIONS entry R60.1 / via VLOGIC (29.80, 67.70) (not met)'])


    def test_r22_dru_override_spellings(self):
        """D-R22-05 (R22-GATE-01): every (min ...) in a constraint is read whatever its unit or position, an unreadable
        one fails, and a later rule on any layer that can meet a pinned row overrides it. The gate lens's seeds: g01f
        (a 10 mil PTH override), g01g (a 6 mil via rule, 0.152 mm), g01h ((opt) before (min)), g01e (an override on
        In1.Cu), a um spelling, an outer override on F.Cu at 0.21 mm and an 8 mil hole-to-hole rule each fail; an
        unknown unit fails as unreadable; a later 0.28 mm F.Cu rule does not. Refilled under g01f's DRU, KiCad honours
        10 mil (J1.2 and J400.2 come back at 0.255 mm), and K-rules names the override and the walls."""
        import hashlib
        import shutil
        import tempfile
        folder = real_project()
        dru = (folder / 'm3.kicad_dru').read_text()

        def rule(name, constraint, layer=None, cond="A.Type == 'Pad' && A.Pad_Type == 'Through-hole'"):
            return (dru + f'\n(rule "{name}"\n' + (f'  (layer {layer})\n' if layer else '') +
                    f'  (condition "{cond}")\n  (constraint {constraint}))\n')
        self.assertEqual((gate.dru_min_mm('10mil'), gate.dru_min_mm('150um'), gate.dru_min_mm('0.01in'),
                          gate.dru_min_mm('0.25mm'), gate.dru_min_mm('3 furlong')), (0.254, 0.15, 0.254, 0.25, None))
        seeds = {
            'g01f 10 mil PTH': (rule('Terminal relief', 'hole_clearance (min 10mil)'), 'follows "JLC inner-layer PTH'),
            'g01g 6 mil via': (rule('Via relief', 'hole_clearance (min 6mil)', cond="A.Type == 'Via'"),
                               "hole_clearance min 0.1524 mm is below JLC's 0.2 mm hole figure"),
            'g01h opt first': (rule('Via relief', 'hole_clearance (opt 0.25mm) (min 0.15mm)', cond="A.Type == 'Via'"),
                               "hole_clearance min 0.15 mm is below JLC's 0.2 mm hole figure"),
            'g01e In1.Cu': (rule('In1 terminal relief', 'hole_clearance (min 0.25mm)', layer='In1.Cu'),
                            'on layer In1.Cu) follows "JLC inner-layer PTH'),
            'um spelling': (rule('x', 'hole_clearance (min 150um)'), "min 0.15 mm is below JLC's 0.2 mm hole figure"),
            'F.Cu outer': (rule('x', 'hole_clearance (min 0.21mm)', layer='F.Cu'),
                           'on layer F.Cu) follows "JLC outer-layer PTH hole to track"'),
            'hole to hole 8 mil': (rule('x', 'hole_to_hole (min 8mil)', cond="A.Type == 'Pad'"),
                                   'follows "JLC pad hole to hole"'),
            'unreadable unit': (rule('x', 'hole_clearance (min 0.3furlong)'), 'has an unreadable minimum'),
        }
        for name, (text, word) in seeds.items():
            with self.subTest(seed=name):
                found = gate.jlc_hole_table(text)[0]
                self.assertTrue(any(word in i for i in found), found)
        self.assertEqual(gate.jlc_hole_table(rule('x', 'hole_clearance (min 0.28mm)', layer='F.Cu'))[0], [])
        # g01f end to end: KiCad honours the mil value, so the fills move to 0.255 mm; K-rules (DRU re-pinned) names both
        d = Path(tempfile.mkdtemp(prefix='r10_g01f_'))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        for name in ('m3.kicad_pcb', 'm3.kicad_pro'):
            shutil.copyfile(folder / name, d / name)
        text = seeds['g01f 10 mil PTH'][0]
        (d / 'm3.kicad_dru').write_text(text)
        board = pcbnew.LoadBoard(str(d / 'm3.kicad_pcb'))
        self.assertTrue(pcbnew.ZONE_FILLER(board).Fill(board.Zones()))
        walls = gate.pth_inner_copper(board)[1]
        self.assertAlmostEqual(walls['J1.2']['In2.Cu'][0], 0.255, delta=0.002)
        with patch.object(gate, 'DRU_SHA256', hashlib.sha256(text.encode('utf-8')).hexdigest()):
            found = self.run_rule('K-rules', board, d / 'm3.kicad_pcb')
        self.assertTrue(any('"Terminal relief"' in i and 'can override' in i for i in found), sorted(found)[:4])
        self.assertTrue(any('J1.2' in i and "JLC's 0.3 mm inner-layer PTH" in i for i in found), sorted(found)[:4])

    def test_r22_board_hole_rows(self):
        """D-R22-05 (R22-GATE-01): three more JLC rows measured on the board, independent of the DRU: via hole wall to
        foreign copper >= 0.2 mm (least 0.25 mm today), PTH hole wall to outer copper >= 0.28 mm (least 0.55 mm) and
        pad hole to pad hole >= 0.45 mm (least 0.835 mm, J3's NPTH to J3.4). A 3V3 track on In1 0.1 mm from a via
        hole, a GND track 0.2 mm from J122.1's hole on F.Cu and a J2 NPTH hole moved 0.3 mm from another each fail."""
        ev = gate.jlc_board_holes(self.load())[1]['least']
        self.assertEqual((ev['via_hole_to_copper'][0], ev['pth_hole_to_outer_copper'][0], ev['pad_hole_to_hole'][0]),
                         (0.25, 0.55, 0.835))
        P, MM = self.P, pcbnew.FromMM

        def track(board, net, layer, a, c):
            t = pcbnew.PCB_TRACK(board); t.SetLayer(layer); t.SetWidth(MM(0.2)); t.SetNet(board.FindNet(net))
            t.SetStart(a); t.SetEnd(c); board.Add(t)

        def via_seed(board):               # USB_ILIM via (14.825, 26.0), hole radius 0.15: track edge 0.1 mm off the wall
            x = MM(14.825) + MM(0.15) + MM(0.1) + MM(0.1)
            track(board, '3V3', pcbnew.In1_Cu, pcbnew.VECTOR2I(x, MM(25.5)), pcbnew.VECTOR2I(x, MM(26.5)))

        def pth_seed(board):               # J122.1's hole (1.3 mm) wall + 0.2 mm, on F.Cu
            c = board.FindFootprintByReference('J122').FindPadByNumber('1').GetPosition()
            x = c.x + MM(0.65) + MM(0.2) + MM(0.1)
            track(board, 'GND', pcbnew.F_Cu, pcbnew.VECTOR2I(x, c.y - MM(0.3)), pcbnew.VECTOR2I(x, c.y + MM(0.3)))

        def hole_seed(board):              # one J2 NPTH 0.3 mm (wall to wall) from another
            holes = sorted((p for p in board.FindFootprintByReference('J2').Pads()
                            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH), key=lambda p: (p.GetPosition().x, p.GetPosition().y))
            a, c = holes[0], holes[1]
            v = a.GetPosition() - c.GetPosition()
            k = (a.GetDrillSize().x / 2 + c.GetDrillSize().x / 2 + MM(0.3)) / v.EuclideanNorm()
            a.SetPosition(c.GetPosition() + pcbnew.VECTOR2I(int(v.x * k), int(v.y * k)))
        for name, seed, word in (
                ('via', via_seed, 'JLC holes: via USB_ILIM (14.82, 26.00) hole wall is 0.1'),
                ('pth outer', pth_seed, 'JLC holes: J122.1 hole wall is 0.2'),
                ('hole to hole', hole_seed, 'JLC holes: J2 NPTH')):
            with self.subTest(seed=name):
                board = self.load()
                seed(board)
                found = gate.jlc_board_holes(board)[0]
                self.assertTrue(any(i.startswith(word) and ('apart' in i if name == 'hole to hole' else True)
                                    for i in found), found)
        self.seeded('K-rules', via_seed, "under JLC's 0.2 mm via hole to copper")

    def test_r22_fab_reference_placement_and_stroke(self):
        """D-R22-06 (R22-GATE-02): each Fab reference's ink centre is within 1.5 mm of its own part's Fab body box (the
        courtyard box for the 14 parts with only a pin-1 dot or no Fab marks; farthest today D9, 0.968 mm), its stroke
        is at least 0.1 x height or 0.05 mm (0.15 x everywhere today), and no board-level text sits on a Fab layer. The
        gate lens's g08a (R134's 8.4 mm away, 5.147 mm from its body box), g08c (a board-level B.Fab 'Q121' on Q120) and
        g08d (R119's at a 0.005 mm stroke) fail, and so does U1's (courtyard-boxed) moved 3 mm off its courtyard."""
        issues, ev = gate.fab_ref_crossings(self.load())
        self.assertEqual(issues, [])
        self.assertEqual(ev['farthest_from_own_box_mm'], ('D9', 0.968))
        self.assertEqual(len(ev['courtyard_boxed']), 14)
        self.assertAlmostEqual(ev['least_stroke_ratio'], 0.15)
        ref = lambda board, r: next(g for g in board.FindFootprintByReference(r).GraphicalItems()  # noqa: E731
                                    if isinstance(g, pcbnew.PCB_TEXT) and g.GetText() == '${REFERENCE}')

        def g08c(board):
            t = pcbnew.PCB_TEXT(board); t.SetText('Q121'); t.SetLayer(pcbnew.B_Fab)
            t.SetPosition(board.FindFootprintByReference('Q120').GetPosition())
            t.SetTextSize(self.P(0.6, 0.6)); t.SetTextThickness(pcbnew.FromMM(0.09)); t.SetMirrored(True); board.Add(t)

        def u1_far(board):
            cy = board.FindFootprintByReference('U1').GetCourtyard(pcbnew.F_CrtYd).BBox()
            ref(board, 'U1').SetPosition(pcbnew.VECTOR2I(cy.GetRight() + pcbnew.FromMM(3.0), cy.Centre().y))
        for name, seed, word in (
                ('g08a', lambda b: ref(b, 'R134').SetPosition(self.P(8.2, 65.5)),     # 8.4 mm from R134's centre,
                 "Fab reference R134 sits 5.147 mm from its own part's Fab body box"),  # 5.1 from its 2512 body box
                ('g08c', g08c, "board-level text 'Q121' on B.Fab"),
                ('g08d', lambda b: ref(b, 'R119').SetTextThickness(pcbnew.FromMM(0.005)),
                 'Fab reference R119 stroke 0.005 mm'),
                ('U1 far', u1_far, "Fab reference U1 sits 3.")):
            with self.subTest(seed=name):
                board = self.load()
                seed(board)
                found = gate.fab_ref_crossings(board)[0]
                self.assertTrue(any(i.startswith(word) for i in found), found)
        self.seeded('K-legends', g08c, "board-level text 'Q121' on B.Fab")

    def test_r24_j400_contact_clamp(self):
        """D-R24-11: J400.2's ESD clamp D402 (a ninth ESD103-B1-02EL, C535146) sits on BAT_SW_RETURN on the screw side of
        R165 with its second pad on GND only. S-5 and K-actuators pin BAT_SW_RETURN to exactly J400.2, R165.1 and
        D402.1, and each fails with the clamp's second pad on another net, with a fourth member on the net and with the
        clamp missing (S-4 too: it is a required safety part). K-ports fails a clamp fed only through R165."""
        b = self.load()
        self.assertEqual(self.run_rule('S-5', b), set())
        self.assertEqual(self.run_rule('K-actuators', b), set())
        self.assertEqual({f'{f.GetReference()}.{q.GetNumber()}' for f in b.GetFootprints() for q in f.Pads()
                          if q.GetNetname() == 'BAT_SW_RETURN'}, {'J400.2', 'R165.1', 'D402.1'})
        self.assertIn('D402', gate.SAFETY_FITTED)

        def net(ref, num, name):
            return lambda board: self.pad(board, ref, num).SetNet(board.FindNet(name))
        for other in ('BAT_ENABLE', 'BAT_SW_RETURN', '3V3'):
            self.seeded('S-5', net('D402', '2', other), 'S-5: D402.2 must be GND')
            self.seeded('K-actuators', net('D402', '2', other), 'with its clamp D402 (C535146) to GND')
        fourth = net('R81', '2', 'BAT_SW_RETURN')            # a fourth member on the switch return
        self.seeded('S-5', fourth, "S-5: BAT_SW_RETURN pads must be exactly ['D402.1', 'J400.2', 'R165.1']")
        self.seeded('K-actuators', fourth, 'with its clamp D402 (C535146) to GND')

        def missing(board):
            board.Delete(board.FindFootprintByReference('D402'))
        self.seeded('S-5', missing, "S-5: D402 (J400.2's ESD clamp, D-R24-11) is missing")
        self.seeded('K-actuators', missing, 'with its clamp D402 (C535146) to GND')
        self.seeded('S-4', missing, 'D402')
        self.seeded('K-actuators', lambda board: board.FindFootprintByReference('D402').SetField('LCSC', 'C15195'),
                    'with its clamp D402 (C535146) to GND')

        def track(board, net, a, c):
            return next(t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net
                        and {tuple(t.GetStart()), tuple(t.GetEnd())} == {tuple(self.P(*a)), tuple(self.P(*c))})

        def behind(board):            # J400.2's B.Cu tap cut at the pin; D402 fed from R165.1 instead
            self.drop(board, track(board, 'BAT_SW_RETURN', (7.4, 67.6), (4.81, 67.6)))
            for layer, a, c in ((pcbnew.F_Cu, (12.425, 67.0), (12.425, 66.0)), (pcbnew.B_Cu, (12.425, 66.0), (4.81, 67.6))):
                t = pcbnew.PCB_TRACK(board); t.SetLayer(layer); t.SetWidth(pcbnew.FromMM(0.2))
                t.SetStart(self.P(*a)); t.SetEnd(self.P(*c)); t.SetNet(board.FindNet('BAT_SW_RETURN')); board.Add(t)
            v = pcbnew.PCB_VIA(board); v.SetPosition(self.P(12.425, 66.0)); v.SetWidth(pcbnew.FromMM(0.5))
            v.SetDrill(pcbnew.FromMM(0.3)); v.SetNet(board.FindNet('BAT_SW_RETURN')); board.Add(v)
        self.seeded('K-ports', behind, 'J400.2 (BAT_SW_RETURN): its clamp D402.1 is reached only through R165')

    def test_r24_short_edge_clearance(self):
        """D-R24-20 (R24-TRI-15): M-8 holds every courtyard 2.5 mm from the rail-less short edges (JLC assembly terms
        section 2.3, ORDERING 8.1) but the six recorded DFM queries at their measured distances. R92 back at its
        5516eeec pose F(31, 87.5) fails (the gate lens's F1), and so do TP88 back at F(35.5, 87.0), R166 0.2 mm nearer
        the edge (grown), R400 0.1 mm further (re-record), C95 moved clear (stale) and C403 deleted (missing)."""
        b = self.load()
        self.assertEqual(self.run_rule('M-8', b), set())
        issues, ev = gate.m8(gate.make_ctx(b))
        self.assertEqual(issues, [])
        self.assertEqual(ev['near'], {'R400': ['aft', 1.025], 'R401': ['aft', 1.025], 'R404': ['aft', 1.025],
                                      'C403': ['aft', 1.955], 'C95': ['forward', 1.505], 'R166': ['forward', 1.755]})

        def put(ref, x, y):
            return lambda board: board.FindFootprintByReference(ref).SetPosition(self.P(x, y))

        def move(ref, dy):
            return lambda board: board.FindFootprintByReference(ref).Move(self.P(0, dy))
        self.seeded('M-8', put('R92', 31.0, 87.5),
                    'M-8: R92 courtyard is 1.725 mm from the forward short edge, under 2.5 mm')
        self.seeded('M-8', put('TP88', 35.5, 87.0), 'M-8: TP88 courtyard is 1.955 mm from the forward short edge')
        self.seeded('M-8', move('R166', 0.2), 'M-8: R166 courtyard is 1.555 mm from the forward short edge, nearer than')
        self.seeded('M-8', move('R400', 0.1), 'M-8: SHORT_EDGE_QUERIES R400 records 1.025 mm, the board gives 1.125 mm')
        self.seeded('M-8', move('C95', -1.5), 'M-8: stale SHORT_EDGE_QUERIES entry C95')
        self.seeded('M-8', lambda board: board.Delete(board.FindFootprintByReference('C403')),
                    'M-8: SHORT_EDGE_QUERIES entry C403: no such part on the board')

    def test_r26_aux_pins_have_gnd_partner_vias(self):
        """D-R26-01 (R26-TRI-09): J440.3 / J440.4 carry AUX_TX_WIRE / AUX_RX_WIRE on F.Cu (from the cell) and B.Cu (to
        the clamps, D-R20-09), so route_check r10 counts each plated pin as a layer change. They are the board's only
        such pins (J400.2's BAT_SW_RETURN is AUD-2-slow, J1.1's BAT_IN power). On the board each has its GND via 1.5 mm
        north and no pad fails; with those two vias removed both fail again at the round 26 figures, 3.900 / 4.037 mm."""
        import route_check as rc
        rc.set_profile('r10')
        self.addCleanup(rc.set_profile, 'r8')

        def pads(board):
            return sorted((d.get('pad'), d['gnd_mm']) for d in rc.scan(board) if d['cat'] == 'critical_via_no_gnd')
        b = self.load()
        self.assertEqual(sorted((n, net) for n, net, _, _ in rc.pad_layer_changes(b)),
                         [('J440.3', 'AUX_TX_WIRE'), ('J440.4', 'AUX_RX_WIRE')])
        self.assertEqual(pads(b), [])
        partners = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND' and
                    (round(pcbnew.ToMM(t.GetPosition().x), 4), round(pcbnew.ToMM(t.GetPosition().y), 4))
                    in ((7.4, 16.5), (7.4, 20.0))]
        self.assertEqual(len(partners), 2)
        for v in partners:
            self.drop(b, v)
        self.assertEqual(pads(b), [('J440.3', 3.9), ('J440.4', 4.037)])

    def copper_gap(self, board, nets_a, nets_b, limit=1.0):
        """D-R26-02 / -04: the least edge-to-edge distance (mm) between copper of nets_a and of nets_b on one copper layer
        (tracks, vias and pads where they are flashed, and nets_b's zone fills), or None when none is within limit +
        0.1 mm. Bisected with KiCad's own shape collision to 1 nm."""
        cu = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

        def shapes(nets):
            out = []
            for t in board.GetTracks():
                if t.GetNetname() in nets:
                    out += [(lid, t.GetEffectiveShape(lid)) for lid in cu
                            if t.IsOnLayer(lid) and (t.GetClass() != 'PCB_VIA' or t.FlashLayer(lid))]
            for f in board.GetFootprints():
                for p in f.Pads():
                    if p.GetNetname() in nets:
                        out += [(lid, p.GetEffectiveShape(lid)) for lid in cu if p.IsOnLayer(lid) and p.FlashLayer(lid)]
            return out
        fills = [(lid, z.GetFilledPolysList(lid)) for z in board.Zones() if z.GetNetname() in nets_b
                 and not z.GetIsRuleArea() for lid in cu if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid)]
        best = None
        for la, sa in shapes(set(nets_a)):
            for lb, sb in shapes(set(nets_b)) + fills:
                if la != lb or not sb.Collide(sa, pcbnew.FromMM(limit + 0.1)):
                    continue
                lo, hi = 0.0, limit + 0.1
                for _ in range(30):
                    mid = (lo + hi) / 2
                    lo, hi = (lo, mid) if sb.Collide(sa, pcbnew.FromMM(mid)) else (mid, hi)
                best = hi if best is None else min(best, hi)
        return best

    def moved_via(self, net, frm, to):
        """A copy of the board with the `net` via at `frm` (mm) put at `to`."""
        board = self.load()
        via = next(t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == net
                   and abs(pcbnew.ToMM(t.GetPosition().x) - frm[0]) < 1e-3 and abs(pcbnew.ToMM(t.GetPosition().y) - frm[1]) < 1e-3)
        via.SetPosition(self.P(*to))
        return board

    def test_r26_pyro1_out_clear_of_3v3_and_3v3a(self):
        """D-R26-02 (R26-TRI-01's respin item): no PYRO1_OUT copper lies within 1.0 mm of 3V3 or 3V3A copper on any
        layer, so a bridge that forms after PC1 is high cannot drive the bus through R134 and the match into a logic
        rail. Round 26's three spots fail again with their parts or via put back: R173 at (16.87, 59.7) (OUT pad 0.5135
        mm from D120.3), the C11 / C10 / R164 column back south (0.566 mm from R164.2) and R13's 3V3 via at
        (9.2, 52.98) (0.620 mm from J121.1's F.Cu run)."""
        rails = ('3V3', '3V3A')
        self.assertGreaterEqual(round(self.copper_gap(self.load(), ('PYRO1_OUT',), rails), 3), 1.0)

        def moved(dys):
            board = self.load()
            for ref, dy in dys.items():
                board.FindFootprintByReference(ref).Move(self.P(0, dy))
            return board
        self.assertAlmostEqual(self.copper_gap(moved({'R173': 0.65}), ('PYRO1_OUT',), rails), 0.5135, places=3)
        self.assertAlmostEqual(self.copper_gap(moved({'C11': 0.65, 'C10': 0.6, 'R164': 0.65}), ('PYRO1_OUT',), rails),
                               0.566, places=2)
        self.assertAlmostEqual(self.copper_gap(self.moved_via('3V3', (9.2, 52.55), (9.2, 52.98)), ('PYRO1_OUT',), rails),
                               0.62, places=3)

    def test_r26_gate_nets_clear_of_3v3_and_3v3a(self):
        """D-R26-04 (round 26 follow-up): no 3V3 or 3V3A copper lies within 1.0 mm of PYRO1_GATE_N (PE4's net) or
        PYRO1_GATE copper on any layer: a 3V3 bridge to PYRO1_GATE_N puts about 3.2 V on Q124's gate through R126 against
        R128's 10 k, one to PYRO1_GATE 3.3 V directly, and either fires an enabled match. R164's 3V3 via (19.55, 55.825) is
        1.059 mm from R128.1. Put back where D-R26-02
        first drew it, (19.05, 55.25), it is 0.331 mm from R126.1; at its 92c3ad59 spot, (19.05, 55.9), 0.676 mm from
        R128.1: both fail."""
        rails, gates = ('3V3', '3V3A'), ('PYRO1_GATE_N', 'PYRO1_GATE')
        self.assertGreaterEqual(round(self.copper_gap(self.load(), gates, rails), 3), 1.0)
        for spot, want in (((19.05, 55.25), 0.331), ((19.05, 55.9), 0.676)):
            with self.subTest(spot=spot):
                got = self.copper_gap(self.moved_via('3V3', (19.55, 55.825), spot), gates, rails)
                self.assertAlmostEqual(got, want, places=3)
                self.assertLess(got, 1.0)

    def test_r22_clamp_gnd_returns(self):
        """D-R22-07 (R22-GATE-03): every port clamp's GND pad reaches a GND via through tracks within 1.0 mm (0.7 mm,
        D400 / D401 0.8 mm, today; D-R24-11's D402 0.7 mm). The gate lens's g07b (D420's GND stub and via removed: the pour alone) fails, and so
        does D410's return re-drawn 1.5 mm long."""
        issues, ev = gate.clamp_returns(self.load())
        self.assertEqual(issues, [])
        self.assertEqual({k: v[0] for k, v in ev.items()},
                         {'D400.2': 0.8, 'D401.2': 0.8, 'D410.2': 0.7, 'D411.2': 0.7, 'D420.2': 0.7, 'D421.2': 0.7,
                          'D440.2': 0.7, 'D441.2': 0.7, 'D402.2': 0.7})

        def find(board, cls, net, pts):
            want = {tuple(self.P(*q)) for q in pts}
            return next(t for t in board.GetTracks() if t.GetClass() == cls and t.GetNetname() == net
                        and ({tuple(t.GetStart()), tuple(t.GetEnd())} == want if cls == 'PCB_TRACK'
                             else tuple(t.GetPosition()) in want))

        def g07b(board):
            self.drop(board, find(board, 'PCB_TRACK', 'GND', [(35.75, 31.525), (35.75, 32.225)]))
            self.drop(board, find(board, 'PCB_VIA', 'GND', [(35.75, 32.225)]))
        self.seeded('K-ports', g07b, "D420.2 (the D420 clamp's GND) reaches no GND via through tracks")
        board = self.load()                 # D410's return stub lengthened 0.8 mm: its via moves along the stub
        via = find(board, 'PCB_VIA', 'GND', [(36.45, 12.625)])
        at = via.GetPosition()
        stub = next(t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'GND'
                    and at in (t.GetStart(), t.GetEnd()))
        q = stub.GetStart() if stub.GetEnd() == at else stub.GetEnd()
        d = at - q
        k = pcbnew.FromMM(0.8) / d.EuclideanNorm()
        far = at + pcbnew.VECTOR2I(int(round(d.x * k)), int(round(d.y * k)))
        via.SetPosition(far)
        stub.SetEnd(far) if stub.GetEnd() == at else stub.SetStart(far)
        found = gate.clamp_returns(board)[0]
        self.assertTrue(any(i.startswith("D410.2 (the D410 clamp's GND) is 1.5") for i in found), found)


    # ------------------------------------------------------------------------------------------------ round 23 pass
    def test_r23_boot0_vcap_and_gate_drive_taps(self):
        """D-R23-01 / -02 (R23-MCU-02, R23-SAFETY-05) / D-R24-02 / -03 / -04: BOOT0's pull-down, both VCAP capacitors and
        the gate drive from R121 to Q120 / Q121 are single-open taps. Since round 24 BOOT0, VCAP2 and both gate drives
        have a second via and no entry; VCAP1 keeps its entry (measured). With its second via dropped (kept referenced)
        each fixed tap hangs on its first via again and fails naming it, with both gate vias gone Q120.4 is cut off from
        R121 entirely, and an entry the board does not meet is stale."""
        taps = {t[1]: t for t in gate.SINGLE_OPEN_TAPS}
        fixed = {'U1.94': ('BOOT0', (14.2, 46.0), 'via BOOT0 (13.80, 45.60)'),
                 'U1.73': ('VCAP2', (18.3, 36.8), 'via VCAP2 (18.00, 37.30)'),
                 'Q120.4': ('ACT_GATE', (15.4, 72.85), 'via ACT_GATE (16.20, 73.30)'),
                 'Q121.4': ('ACT_GATE', (11.74, 72.3), 'via ACT_GATE (11.14, 71.70)')}
        b = self.load()
        issues, ev = gate.single_via_opens(b, taps=[taps[t] for t in [*fixed, 'U1.48']])
        self.assertEqual(issues, [])
        self.assertEqual({t: ev[t]['single_points'] for t in [*fixed, 'U1.48']},
                         {**{t: [] for t in fixed}, 'U1.48': ['via VCAP1 (29.25, 38.00)']})
        self.assertIn('Table 124 p. 216', next(x[2] for x in gate.SINGLE_OPEN_EXCEPTIONS if x[0] == 'U1.48'))

        def drop(net, xy):
            def seed(board):
                self.drop(board, next(v for v in board.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == net
                                      and v.GetPosition() == self.P(*xy)))
            return seed
        for tap, (net, second, first) in fixed.items():
            with self.subTest(tap=tap):
                board = self.load()
                drop(net, second)(board)
                t = taps[tap]
                self.assertEqual(gate.single_via_opens(board, taps=[t])[0],
                                 [f'{tap} ({t[3]}) hangs on one via: opening {first} cuts it off from {"/".join(t[2])}'])
        extra = list(gate.SINGLE_OPEN_EXCEPTIONS) + [('U1.94', 'via BOOT0 (13.80, 45.60)', 'not met')]
        self.assertEqual(gate.single_via_opens(b, taps=[taps['U1.94']], exceptions=extra)[0],
                         ['stale SINGLE_OPEN_EXCEPTIONS entry U1.94 / via BOOT0 (13.80, 45.60) (not met)'])

        def no_gate_vias(board):
            drop('ACT_GATE', (16.2, 73.3))(board)
            drop('ACT_GATE', (15.4, 72.85))(board)
        self.seeded('K-power', no_gate_vias, "Q120.4 (Q120's gate drive from R121 (R23-SAFETY-05)) is not joined to R121.1")


    def test_r23_dru_reader_spellings_and_floors(self):
        """D-R23-05 / -07 (R23-GATE-01 / -03): the DRU is read as KiCad reads it ('#' comments stripped, rule names and
        layers quoted or bare) and every minimum is floored, with no severity but error. The gate lens's seeds fail: h01
        (an unquoted 0.10 mm relief rule), a quoted (layer "In1.Cu") / (layer "inner") override, the pinned inner rule
        commented out, unbalanced text, h03 ((severity ignore) on SERVO1) and h04 (SERVO1 clearance 0.05 mm), and so do
        track width 0.05, edge clearance 0, annular width 0.01, text height 0.3, hole size 0.1 and a constraint with no
        floor; through K-rules (re-pinned) h01 fails too."""
        import hashlib
        folder = real_project()
        dru = (folder / 'm3.kicad_dru').read_text()
        self.assertEqual(gate.jlc_hole_table(dru)[0], [])
        rules = gate.dru_rules(dru)
        self.assertEqual(len(rules), 8)
        self.assertTrue(all(r['name'] and not r['bad'] and r['severity'] is None for r in rules))

        def rule(name, body, layer=None, cond="A.Type == 'Pad'", sev=None):
            return (dru + f'\n(rule {name}\n' + (f'  (layer {layer})\n' if layer else '') +
                    (f'  (severity {sev})\n' if sev else '') + f'  (condition "{cond}")\n  (constraint {body}))\n')
        a = dru.index('(rule "JLC inner-layer PTH pad hole to copper"')
        z = dru.index('(rule "JLC outer-layer PTH hole to track"')
        commented = dru[:a] + ''.join('# ' + line + '\n' for line in dru[a:z].rstrip('\n').split('\n')) + '\n' + dru[z:]
        servo = "A.NetName == 'SERVO1_MCU' || B.NetName == 'SERVO1_MCU'"
        seeds = {
            'h01 unquoted relief': (rule('relief', 'hole_clearance (min 0.10mm)', cond="A.Type == 'Via' && B.Type != 'Zone'"),
                                    'DRU rule "relief" hole_clearance min 0.1 mm is below JLC'),
            'quoted In1.Cu': (rule('"x"', 'hole_clearance (min 0.25mm)', layer='"In1.Cu"'),
                              'on layer In1.Cu) follows "JLC inner-layer PTH'),
            'quoted inner': (rule('"x"', 'hole_clearance (min 0.25mm)', layer='"inner"'),
                             'on layer inner) follows "JLC inner-layer PTH'),
            'pinned rule commented': (commented, 'needs one DRU rule "JLC inner-layer PTH pad hole to copper", found 0'),
            'unbalanced': (dru + '\n(rule "x" (constraint clearance (min 0.2mm))\n', 'cannot be read'),
            'h03 severity ignore': (rule('"Servo pair"', 'clearance (min 0.15mm)', cond=servo, sev='ignore'),
                                    'sets severity ignore'),
            'h04 clearance 0.05': (rule('"Servo pair"', 'clearance (min 0.05mm)', cond=servo),
                                   'clearance min 0.05 mm is below the 0.15 mm floor'),
            'track width': (rule('"x"', 'track_width (min 0.05mm)'), 'track_width min 0.05 mm is below the 0.15 mm'),
            'edge clearance': (rule('"x"', 'edge_clearance (min 0mm)'), 'edge_clearance min 0 mm is below the 0.5 mm'),
            'annular width': (rule('"x"', 'annular_width (min 0.01mm)'), 'annular_width min 0.01 mm is below the 0.1 mm'),
            'text height': (rule('"x"', 'text_height (min 0.3mm)'), 'text_height min 0.3 mm is below the 1.0 mm'),
            'hole size': (rule('"x"', 'hole_size (min 0.1mm)'), 'hole_size min 0.1 mm is below the 0.3 mm'),
            'no floor': (rule('"x"', 'length (min 1mm)'), 'DRU_FLOORS has no floor for it'),
        }
        for name, (text, word) in seeds.items():
            with self.subTest(seed=name):
                self.assertNotEqual(text, dru)
                found = gate.jlc_hole_table(text)[0]
                self.assertTrue(any(word in i for i in found), found)
        path, text = folder / 'm3.kicad_dru', seeds['h01 unquoted relief'][0]
        try:
            path.write_text(text)
            with patch.object(gate, 'DRU_SHA256', hashlib.sha256(text.encode('utf-8')).hexdigest()):
                found = self.run_rule('K-rules', self.load(), folder / 'm3.kicad_pcb')
            self.assertTrue(any('DRU rule "relief"' in i for i in found), sorted(found))
        finally:
            path.write_text(dru)

    def test_r23_copper_drawing_near_a_via_hole(self):
        """D-R23-06 (R23-GATE-02): the JLC board measures take S-8's copper set (copper_nodes), so a board copper
        drawing counts: the gate lens's h01 board copper, an In1 GND drawing 0.16 mm from via 3V3 (36.13, 58.8)'s hole
        wall, fails the 0.2 mm via-hole row, in jlc_board_holes and through K-rules."""
        def drawing(board):
            x = pcbnew.FromMM(36.13 + 0.15 + 0.16 + 0.10)
            s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(pcbnew.VECTOR2I(x, pcbnew.FromMM(58.5))); s.SetEnd(pcbnew.VECTOR2I(x, pcbnew.FromMM(59.1)))
            s.SetWidth(pcbnew.FromMM(0.2)); s.SetLayer(pcbnew.In1_Cu); s.SetNet(board.FindNet('GND')); board.Add(s)
        board = self.load()
        self.assertTrue(any(v.GetClass() == 'PCB_VIA' and v.GetNetname() == '3V3' and v.GetPosition() == self.P(36.13, 58.8)
                            for v in board.GetTracks()))
        drawing(board)
        found = gate.jlc_board_holes(board)[0]
        self.assertTrue(any(i.startswith('JLC holes: via 3V3 (36.13, 58.80) hole wall is 0.16') and 'copper drawing' in i
                            for i in found), found)
        self.seeded('K-rules', drawing, 'via 3V3 (36.13, 58.80) hole wall is 0.16')

    def test_r23_fab_labels(self):
        """D-R23-08 (R23-GATE-04): footprint text boxes and visible fields on a Fab layer are Fab text, a reference's
        characters are at least half its height wide (or 0.3 mm), and no board-level shape sits on a Fab layer. The gate
        lens's f01b (a text box 'Q121' in Q120), f02 (Q120's Value shown), f03 (R119's reference 0.02 mm wide) and f05 (a
        board-level B.Fab rectangle over R134's reference) each fail."""
        self.assertEqual(gate.fab_ref_crossings(self.load())[0], [])
        ref = lambda board, r: next(g for g in board.FindFootprintByReference(r).GraphicalItems()  # noqa: E731
                                    if isinstance(g, pcbnew.PCB_TEXT) and g.GetText() == '${REFERENCE}')
        MM = pcbnew.FromMM

        def f01b(board):
            f = board.FindFootprintByReference('Q120'); c = f.GetPosition()
            t = pcbnew.PCB_TEXTBOX(f); t.SetText('Q121'); t.SetLayer(pcbnew.B_Fab)
            t.SetStart(pcbnew.VECTOR2I(c.x - MM(0.9), c.y + MM(2.8))); t.SetEnd(pcbnew.VECTOR2I(c.x + MM(0.9), c.y + MM(3.6)))
            t.SetTextSize(self.P(0.6, 0.6)); t.SetTextThickness(MM(0.09)); t.SetMirrored(True); t.SetBorderEnabled(False)
            f.Add(t)

        def f02(board):
            f = board.FindFootprintByReference('Q120'); v = f.Value()
            self.assertEqual(board.GetLayerName(v.GetLayer()), 'B.Fab')
            v.SetVisible(True); v.SetPosition(f.GetPosition())

        def f05(board):
            c = ref(board, 'R134').GetPosition()
            s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_RECT)
            s.SetStart(pcbnew.VECTOR2I(c.x - MM(1.6), c.y - MM(0.8))); s.SetEnd(pcbnew.VECTOR2I(c.x + MM(1.6), c.y + MM(0.8)))
            s.SetFilled(True); s.SetWidth(MM(0.1)); s.SetLayer(pcbnew.B_Fab); board.Add(s)
        for name, seed, word in (('f01b', f01b, "Fab text ['Q121'] on Q120"),
                                 ('f02', f02, "Fab text ['AONR21357'] on Q120"),
                                 ('f03', lambda b: ref(b, 'R119').SetTextWidth(MM(0.02)),
                                  'Fab reference R119 characters are 0.020 mm wide'),
                                 ('f05', f05, 'board-level PCB_SHAPE on B.Fab')):
            with self.subTest(seed=name):
                board = self.load()
                seed(board)
                found = gate.fab_ref_crossings(board)[0]
                self.assertTrue(any(i.startswith(word) for i in found), found)
        self.seeded('K-legends', f02, "Fab text ['AONR21357'] on Q120")

    def test_r23_generated_footprints_and_paste_totals(self):
        """D-R23-09 (R23-GATE-05): K-lands pins r10_parts' own footprint files by SHA-256 and the board's pasted pads
        per side (249 F.Paste / 381 B.Paste since D-R24-09 moved R402 / R403 to B.Cu and D-R24-11 added D402). The gate
        lens's x02 (Q120 / Q121's paste stripped by a generator edit: the library file changes and the board's 18 pads lose
        paste, 381 -> 363)
        fails both ways."""
        import shutil
        import tempfile
        self.assertEqual(gate.paste_totals(self.load()), ([], {'F.Paste': 249, 'B.Paste': 381}))

        def unpaste(board):
            for ref in ('Q120', 'Q121'):
                for q in board.FindFootprintByReference(ref).Pads():
                    ls = q.GetLayerSet(); ls.RemoveLayer(pcbnew.B_Paste); ls.RemoveLayer(pcbnew.F_Paste); q.SetLayerSet(ls)
        self.seeded('K-lands', unpaste, 'B.Paste: 363 pasted pads, pinned 381')
        src = gate.ROOT / 'm3_design/assembly_review'
        d = Path(tempfile.mkdtemp(prefix='r10_x02_'))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copyfile(src / 'fp-lib-table', d / 'fp-lib-table')
        shutil.copytree(src / 'kilib/rocket.pretty', d / 'kilib/rocket.pretty')
        shutil.copyfile(real_project() / 'm3.kicad_pcb', d / 'm3.kicad_pcb')
        mod = d / 'kilib/rocket.pretty/M3_AONR21357_DFN3x3A_EP1.kicad_mod'
        text = mod.read_text()
        self.assertIn('"F.Paste"', text)
        mod.write_text(text.replace(' "F.Paste"', ''))
        found = self.run_rule('K-lands', self.load(), d / 'm3.kicad_pcb')
        self.assertTrue(any('generated footprint M3_AONR21357_DFN3x3A_EP1 file SHA-256' in i for i in found), sorted(found))

    def test_r23_imu_ground_taps(self):
        """D-R23-11 (R23-GATE-07): U4's power-ground pins U4.6 / U4.7 hang on the GND via (16.75, 47.60) alone, an exact
        entry with its consequence (IMU dead: no launch detect, the primary does not fire; roll control lost). With the
        entry dropped each fails naming the via."""
        taps = {t[1]: t for t in gate.SINGLE_OPEN_TAPS}
        b = self.load()
        issues, ev = gate.single_via_opens(b, taps=[taps['U4.6'], taps['U4.7']])
        self.assertEqual((issues, ev['U4.6']['single_points'], ev['U4.7']['single_points']),
                         ([], ['via GND (16.75, 47.60)'], ['via GND (16.75, 47.60)']))
        self.assertIn('the primary does not fire', next(x[2] for x in gate.SINGLE_OPEN_EXCEPTIONS if x[0] == 'U4.6'))
        for tap in ('U4.6', 'U4.7'):
            with self.subTest(tap=tap):
                self.assertEqual(gate.single_via_opens(b, taps=[taps[tap]], exceptions=[])[0],
                                 [f'{tap} ({taps[tap][3]}) hangs on one via: opening via GND (16.75, 47.60) cuts it off '
                                  'from J1.2'])


if __name__ == '__main__':
    unittest.main()
