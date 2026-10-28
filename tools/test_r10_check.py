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

    def test_uart_isolation_and_bias_seeds(self):
        import json
        contract = json.loads((gate.ROOT / 'm3_design/assembly_review/sources/r10_design/circuit.json').read_text())
        pins, values, codes = {}, {}, {}
        for ref, part in contract['parts'].items():
            values[ref] = part['value']; codes[ref] = part['fields']['LCSC']
            pins.update({f'{ref}.{p}': n for p, n in part['nets'].items()})
        self.assertEqual(gate.uart_ports(pins, values, codes), [])
        for pin, net in (('U411.7', 'GPS_4V8'), ('U421.6', '3V3'), ('R442.2', '3V3'),
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
        self.assertIn('isolation requires OE low', states['off_external_uart_active'])
        self.assertIn('main 3V3 itself is off', states['off_external_uart_active'])
        self.assertIn('Camera VCCB retains U13', states['off_external_uart_active'])
        self.assertIn('no state sensor', states['port_device_backfeed'])
        self.assertNotIn('when the power switch opens', obligations)


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
        for n in ('RAW_ACT_SENSE_MCU', 'ARM1_SENSE_MCU', 'RAW_ACT_SENSE'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, n))
        for raw, armed in (('RAW_ACT_SENSE_MCU', 'ARM1_SENSE_MCU'), ('RAW_ACT_SENSE', 'ARM1_SENSE')):
            with self.subTest(raw=raw):
                u = self.part('U12', [('1', 0, 0, raw), ('2', 1, 0, armed), ('3', 2, 0, 'GND'), ('4', 3, 0, '3V3'),
                                      ('5', 4, 0, 'GPS_TX_MCU')], at=(30, 30))
                for fn, rid in ((gate.s1, 'S-1'), (gate.s2, 'S-2')):
                    self.assertTrue(any('bypasses the named pyro / sense chain' in i for i in fn(self.ctx())[0]), (rid, fn(self.ctx())[0]))
                self.board.Remove(u)
        u = self.part('U12', [('1', 0, 0, 'RAW_ACT_SENSE_MCU'), ('2', 1, 0, 'GND'), ('3', 2, 0, '3V3'),
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
        self.part('R123', [('1', 0, 0, 'ACT_EN'), ('2', 1.5, 0, 'GND')], at=(35, 72)).SetValue('100k')

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
                    'R129', 'R130', 'R131', 'R132', 'R133', 'R173', 'R175', 'R178', 'R180', 'R168', 'R170', 'C128'):
            self.assertIn(ref, gate.SAFETY_FITTED)

    # --- S-5 single screw switch -------------------------------------------------------------------------------
    def power_switch(self):
        self.part('J400', [('1', 0, 0, 'BAT_SW_SOURCE'), ('2', 3.5, 0, 'BAT_SW_RETURN')], at=(5, 10))
        self.part('R80', [('1', 0, 0, 'BAT_IN'), ('2', 1.5, 0, 'BAT_SW_SOURCE')], at=(15, 10)).SetValue('470k 1%')
        self.part('R165', [('1', 0, 0, 'BAT_SW_RETURN'), ('2', 1.5, 0, 'BAT_ENABLE')], at=(20, 10)).SetValue('470k 1%')
        self.part('U9', [('1', 0, 0, 'BAT_ENABLE')], at=(25, 10))

    def test_s5_switch_topology_and_resistor_values(self):
        self.power_switch()
        self.assertEqual(gate.s5(self.ctx())[0], [])
        for ref, num, net in (('J400', '1', 'BAT_IN'), ('R165', '2', 'RAW_PROTECTED'), ('U9', '1', 'RAW_ACT')):
            p = self.board.FindFootprintByReference(ref).FindPadByNumber(num)
            old = p.GetNet(); p.SetNet(self.board.FindNet(net))
            self.assertTrue(any(f'{ref}.{num} must be' in i for i in gate.s5(self.ctx())[0]))
            p.SetNet(old)
        self.board.FindFootprintByReference('R80').SetValue('0R')
        self.assertTrue(any('R80 must be 470k' in i for i in gate.s5(self.ctx())[0]))

    def test_s5_switch_contact_cannot_be_bypassed(self):
        self.power_switch()
        f = self.part('R999', [('1', 0, 0, 'BAT_SW_SOURCE'), ('2', 1.5, 0, 'BAT_SW_RETURN')], at=(30, 10))
        self.assertTrue(any('bypasses the open J400 switch' in i for i in gate.s5(self.ctx())[0]))
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
        self.track((20, 30), (22.5, 30), 'PYRO1_GATE', pcbnew.B_Cu)
        gnd = pcbnew.SHAPE_POLY_SET(); gnd.NewOutline()
        for x, y in ((10, 10), (40, 10), (40, 40), (10, 40)):
            gnd.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        with patch.object(cr, 'fills', return_value={pcbnew.B_Cu: pcbnew.SHAPE_POLY_SET()}):
            issues, ev = gate.references(self.board)
        self.assertTrue(issues and 'PYRO1_GATE B.Cu' in ev['by_net_layer'], (issues, ev))
        with patch.object(cr, 'fills', return_value={pcbnew.B_Cu: gnd}):
            self.assertEqual(gate.references(self.board)[0], [])

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

    # --- R3-SAF-01 pyro barrels ----------------------------------------------------------------------
    def test_s8_inner_copper_near_pyro_barrel(self):
        self.via(30, 30, 'RAW_ACT', drill=0.3)
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
class AuditScope(SyntheticBase):
    plane = R4Synthetic.plane

    def setUp(self):
        super().setUp()
        for net in ('SPI1_SCK', 'GPS_PWR_EN', 'CAM_UART_OE'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))

    def test_aud2_exact_whitelist_and_fast_reference_boundary(self):
        import critical_reference as cr
        self.assertTrue({'ARM1_SENSE_MID', 'RAW_ACT_SENSE_MCU', 'ACT_EN_MCU', 'CAM_UART_OE'} <= cr.R10_SLOW_RETURN_NETS)
        for net in ('RAW_ACT', 'PYRO1_GATE', 'PYRO1_GATE_N', 'PYRO1_COLD', 'GPS_TX_MCU', 'ACT_EN_EXTRA', 'ARM1_SENSE_EXTRA'):
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
        for ref in ('J410', 'J420', 'J122'):
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
        for x, y in gate.VIPPO_CENTRES:
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


@unittest.skipUnless(plate, 'NumPy required (run under a python3 with numpy)')
class Plate(unittest.TestCase):
    """R3-MEC-01: every R10 mass key is placed (own row, or a mated allowance on its parent's box) or refused."""
    def setUp(self):
        self.spec = json.loads((Path(__file__).resolve().parents[1] /
                                'm3_design/assembly_review/sources/r10_design/masses.json').read_text())
        refs = ['J1', 'J121', 'J122', 'C84', 'LS120', 'J3', 'J9', 'J400', 'J410', 'J420',
                'J9 mated', 'J400 mated', 'J410 mated', 'J420 mated', 'J122 mated']
        self.fit = dict(profile='r10', outline=[0, 0, 46, 84], supports=[[4, 4], [42, 4], [4, 80], [42, 80], [42, 42]],
                        rows=[(1, ref, 'F', [20 + i, 40, 22 + i, 42, 0, 2]) for i, ref in enumerate(refs)])

    def test_mated_allowance_on_parent_and_unmatched_key_refused(self):
        _, masses, _ = plate.build(self.fit, 5, False, 'r10_mated', 'r10', self.spec)
        for ref in ('J1', 'J121'):
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

    def test_r10_fab_selects_the_r10_procurement_limits(self):
        text = (gate.ROOT / 'm3_design/r10_fab.sh').read_text()
        self.assertIn('python3 tools/jlc_cost.py --max-total 84.41 --max-extended 52', text)
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
        via = pcbnew.PCB_VIA(b); via.SetPosition(self.P(27.6, 13.6)); via.SetNet(b.FindNet('GND'))
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

    def test_screw_switch_contacts_and_protection(self):
        self.seeded('S-5', lambda b: self.pad(b, 'J400', '1').SetNet(b.FindNet('BAT_IN')), 'J400.1 must be')
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
        self.seeded('S-7', lambda b: self.pad(b, 'J122', '3').SetNet(b.FindNet('3V3')), 'J122.3')

    def test_raw_act_fed_from_raw_protected(self):
        self.seeded('S-2', lambda b: self.pad(b, 'R177', '2').SetNet(b.FindNet('RAW_PROTECTED')), 'RAW_PROTECTED')
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
        for net, ends in (('RAW_ACT', (7., 67.6, 13.5, 67.6)), ('BAT_IN', (12., 74.1, 13.5, 72.6))):
            board = self.load()
            fp = board.FindFootprintByReference('Q121' if net == 'RAW_ACT' else 'Q120')
            self.assertAlmostEqual(pcbnew.ToMM(fp.FindPadByNumber('9').GetSize().x), .43)
            tracks = []
            for t in gate.fire_path(board, net, gate.FIRE_TERMINALS[net])[0]:
                points = sorted((pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)) for p in (t.GetStart(), t.GetEnd()))
                if all(abs(a - b) < .001 for a, b in zip(points[0] + points[1], ends)):
                    tracks.append(t)
            self.assertEqual(len(tracks), 1, (net, ends))
            tracks[0].SetWidth(pcbnew.FromMM(.43))
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
        for original, wrong, marker in (('J410 2:GND', 'J410 2:3V3', 'J410.2'),
                ('J420 3:TXO', 'J420 3:RXI', 'J420.3'),
                ('J122 1:S 2:NC 3:GND', 'J122 1:S 2:NC 3:NC', 'J122.3'),
                (gate.SERVO_HARNESS_NOTE, 'SERVO + FROM BOARD', 'J122:')):
            def seed(b, original=original, wrong=wrong):
                matches = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT)
                           and d.GetText() == original]
                self.assertEqual(len(matches), 1, original)
                matches[0].SetText(wrong)
            self.seeded('K-legends', seed, marker)

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

        def narrow(b):                      # the B.Cu BAT_IN run (17.35, 86.6) -> (36.725, 86.6) narrowed to 0.3 mm
            for t in b.GetTracks():
                if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'BAT_IN' and t.GetLayer() == pcbnew.B_Cu and \
                        abs(pcbnew.ToMM(t.GetWidth()) - 1.0) < 1e-6 and abs(pcbnew.ToMM(t.GetStart().y) - 86.6) < 1e-3 \
                        and abs(pcbnew.ToMM(t.GetEnd().y) - 86.6) < 1e-3:
                    t.SetWidth(pcbnew.FromMM(0.3))
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
        for raw, armed in (('RAW_ACT_SENSE_MCU', 'ARM1_SENSE_MCU'), ('RAW_ACT_SENSE', 'ARM1_SENSE')):
            for rid in ('S-1', 'S-2'):
                self.seeded(rid, bridge(raw, armed), 'bypasses the named pyro / sense chain')

    def test_supply_ties_seeds(self):
        """R4-SAF-02 / R4-GATE-03: RAW_ACT -> 3V3 resistor chain (two parts), a U9 pad on RAW_ACT."""
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

    def test_j1_wire_entry(self):
        """R3-MEC-02: J1 turned away from the west face."""
        self.seeded('P-11', lambda b: b.FindFootprintByReference('J1').SetOrientationDegrees(90), 'J1 wires enter')

    def move(self, b, ref, dx, dy):
        f = b.FindFootprintByReference(ref)
        f.SetPosition(pcbnew.VECTOR2I(f.GetPosition().x + pcbnew.FromMM(dx), f.GetPosition().y + pcbnew.FromMM(dy)))

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
        self.seeded('S-1', lambda b: self.pad(b, 'R168', '1').SetNet(b.FindNet('GND')) if self.pad(b, 'R168', '1').GetNetname() == 'PYRO1_CONT_MCU' else self.pad(b, 'R168', '2').SetNet(b.FindNet('GND')), 'PYRO1_CONT')

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
