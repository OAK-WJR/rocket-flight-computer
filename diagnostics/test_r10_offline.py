"""Readiness tests only. Hand-built observations; no evaluator or truth access.

Tests use hand-built observations, the committed protocol and the saved PCB.
No board connection, serial transport or native libraries are used.
"""
import copy
import io
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnostics import r10_offline as r

HERE = Path(__file__).resolve().parent
BOARD = HERE.parent / 'm3_design/assembly_review/m3.kicad_pcb'
SCHEMA = HERE / 'r10_protocol.schema.json'
P = r.Profile(synthetic=True)
NORMAL = {'BAT_IN': 7.8, 'RAW_PROTECTED': 7.7, 'VBUS': 5.0, 'USB_LIMITED': 4.95,
          'VLOGIC': 7.6, '3V3': 3.3, '3V3A': 3.28, 'PORT_5V3': 5.45,
          'PORT_4V8': 4.8, 'CAM_5V': 5.42, 'CAM_IO_3V3': 3.3, 'CAM_PWR_EN': 3.3}


def measurement(point, value, ground=None, origin='SYNTHETIC_FIXTURE', epoch='steady_1'):
    p = P.point(point)
    m = {'type': 'measurement', 'point': p, 'ground': ground or P.ground(p),
         'status': 'NOT_AVAILABLE' if value is None else 'AVAILABLE', 'origin': origin, 'epoch': epoch}
    if value is not None:
        m.update(unit='V', interval=[value - .01, value + .01], uncertainty_abs_v=.01)
    return m


def initial(values=None, modules=None, ports=None, source='PACK'):
    values = {**NORMAL, **(values or {})}
    ports = ports or dict(zip(r.MODULES, (*r.DIRECT, 'J9')))
    ms = {m: 4.78 if m != 'CAMERA' else 5.40 for m in r.MODULES}
    if source == 'USB':
        ms = {m: 0 for m in r.MODULES}
    ms.update(modules or {})
    supplies = {}
    wiring = {}
    for m in r.MODULES:
        v = measurement('C9.1', ms[m])
        for k in ('type', 'point', 'ground'):
            del v[k]
        v.update(location_kind='FIXTURE_MODULE_TERMINALS', positive='VPLUS', negative='GND', installed_port=ports[m])
        supplies[m] = v
        tx, rx = ('3', '4') if m == 'CAMERA' else ('4', '3')
        wiring[m] = {'status': 'AVAILABLE', 'origin': 'SYNTHETIC_FIXTURE', 'method': r.METHOD,
                     'module_TX_to': P.point(ports[m] + '.' + tx), 'module_RX_to': P.point(ports[m] + '.' + rx)}
    return {'type': 'initial', 'protocol': 'r10-offline-diagnostic/v1', 'profile': r.PROFILE,
            'board_sha256': r.BOARD_SHA, 'origin': 'SYNTHETIC_FIXTURE', 'installed_port_map': ports,
            'power_context': {'attached_source': source, 'steady_observation_epoch': 'steady_1',
                              'external_self_power': False, 'recovery_loads_connected': False,
                              'camera_control': 'hypothetical_static_state_not_a_firmware_claim'},
            'observations': {'logic_supply': measurement('C9.1', values['3V3']), 'module_supplies': supplies,
                             'harness_continuity': wiring,
                             'serial': {'status': 'NOT_AVAILABLE', 'reason': 'NO_BOUND_R10_FIRMWARE'}},
            'probe_budget': 6, 'physical_qualified': False, 'firmware_verified': False}


def simulate(i=None, values=None, unavailable=()):
    values = {**NORMAL, **(values or {})}
    s = r.Session(i or initial(values), P)
    message = s.advance()
    transcript = []
    while message['type'] == 'probe':
        transcript.append(message)
        pt = message['point']
        v = None if pt['point_id'] in unavailable else values.get(pt['net'])
        message = s.advance(measurement(pt['point_id'], v, message['ground']))
    return message, transcript, s


def manual_record(values=None):
    """Illustrative hand-entry record. Not a real physical measurement."""
    doc = r.template(BOARD)
    doc.update(assembly_id='EXAMPLE-ONLY-NO-PHYSICAL-CLAIM', session_id='manual-example-1', epoch='steady-a',
               observed_window={'start': '2026-01-01T12:00:00Z', 'end': '2026-01-01T12:01:00Z'})
    doc['power_context'].update(attached_source='PACK', selected_source='PACK', configuration_id='unchanged-a',
        source_note='Illustrative operator-declared source window, not measured', source_reference_v=[6.0, 8.4],
        battery_path_expected=True, ground_reference_verified=True, backfeed_excluded=True)
    for net, v in (values or {'3V3': 3.3, '3V3A': 0}).items():
        m = measurement(r.PREFERRED[net], v, origin='MANUAL_OFFLINE', epoch=doc['epoch'])
        m.update(assembly_id=doc['assembly_id'], session_id=doc['session_id'], configuration_id='unchanged-a',
                 measured_at='2026-01-01T12:00:30Z', instrument='EXAMPLE instrument, no physical capture',
                 uncertainty_basis='Illustrative absolute enclosure +/-0.01 V; no confidence level asserted')
        doc['measurements'].append(m)
    return doc


def validate_schema(value, schema, root):
    """Test-only interpreter for keywords used by the public candidate schema."""
    if '$ref' in schema:
        node = root
        for part in schema['$ref'].split('/')[1:]:
            node = node[part]
        return validate_schema(value, node, root)
    if 'oneOf' in schema:
        successes = 0
        for choice in schema['oneOf']:
            try:
                validate_schema(value, choice, root)
                successes += 1
            except AssertionError:
                pass
        assert successes == 1
        return
    if 'const' in schema:
        assert value == schema['const'] and (not isinstance(value, bool) or type(value) is type(schema['const']))
    if 'enum' in schema:
        assert value in schema['enum']
    types = {'object': dict, 'array': list, 'string': str, 'null': type(None), 'number': (int, float)}
    if 'type' in schema:
        allowed = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        assert any(isinstance(value, types[t]) and not (t == 'number' and isinstance(value, bool)) for t in allowed)
    if isinstance(value, dict):
        assert set(schema.get('required', [])) <= value.keys()
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            assert value.keys() <= props.keys()
        for k, v in value.items():
            if k in props:
                validate_schema(v, props[k], root)
    if isinstance(value, list):
        assert len(value) >= schema.get('minItems', 0)
        assert len(value) <= schema.get('maxItems', float('inf'))
        if schema.get('uniqueItems'):
            assert len({json.dumps(v, sort_keys=True) for v in value}) == len(value)
        for v in value:
            if 'items' in schema:
                validate_schema(v, schema['items'], root)
    if isinstance(value, str) and 'pattern' in schema:
        assert r.re.search(schema['pattern'], value)


class ProbeTests(unittest.TestCase):
    def test_native_profile_and_board_bytes(self):
        p = r.Profile(board=BOARD)
        self.assertTrue(p.board_checked)
        self.assertEqual(p.point('R164.2')['xy_mm'], [16.5, 55.25])
        self.assertEqual(p.point('R164.2')['side'], 'B.Cu')
        self.assertEqual((p.data['native_footprints'], p.data['native_pads']), (216, 705))
        with self.assertRaises(ValueError):
            r.Profile()

    def test_wrong_board_and_tampered_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'wrong.pcb'
            path.write_bytes(b'not the saved R10 board')
            with self.assertRaisesRegex(ValueError, 'Wrong board bytes'):
                r.Profile(board=path)
            bad = copy.deepcopy(P.data)
            bad['points']['R164.2']['xy_mm'][0] = 29.5
            path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, 'catalog'):
                r.Profile(path, synthetic=True)

    def test_native_identity_accepts_numeric_aliases_not_boolean_or_shift(self):
        point = P.point('R431.1')
        point['xy_mm'][0] = int(point['xy_mm'][0])
        self.assertEqual(P.identity(point), 'CAM_PWR_EN')
        for bad in (True, point['xy_mm'][0] + .001):
            changed = copy.deepcopy(point); changed['xy_mm'][0] = bad
            with self.assertRaises(ValueError):
                P.identity(changed)

    def test_sensor_branch_and_native_targets(self):
        result, transcript, _ = simulate(values={'3V3A': 0})
        self.assertEqual(result['candidate_causes'], ['sensor_supply_branch'])
        self.assertEqual([p['point_id'] for p in result['next_step']['target_points']], ['R164.1', 'R164.2'])
        self.assertLessEqual(len(transcript), 6)

    def test_supply_topology_boundaries(self):
        scenarios = [
            ('battery_input', {'BAT_IN': 0, 'RAW_PROTECTED': 0, 'VLOGIC': 0, '3V3': 0}),
            ('battery_protected_branch', {'RAW_PROTECTED': 0, 'VLOGIC': 0, '3V3': 0}),
            ('logic_selection_branch', {'VLOGIC': 0, '3V3': 0}),
            ('logic_conversion_branch', {'3V3': 0}),
        ]
        for cause, values in scenarios:
            with self.subTest(cause=cause):
                result, _, _ = simulate(initial(values), values)
                self.assertIn(cause, result['candidate_causes'])
                self.assertNotIn('sensor_supply_branch', result['candidate_causes'])

    def test_usb_source_path_and_expected_off_peripherals(self):
        for cause, values in [
            ('usb_input', {'VBUS': 0, 'USB_LIMITED': 0, 'VLOGIC': 0, '3V3': 0}),
            ('usb_limited_branch', {'USB_LIMITED': 0, 'VLOGIC': 0, '3V3': 0}),
            ('logic_selection_branch', {'VLOGIC': 0, '3V3': 0}),
        ]:
            with self.subTest(cause=cause):
                result, probes, _ = simulate(initial(values, source='USB'), values)
                self.assertEqual(result['candidate_causes'], [cause])
                self.assertFalse(any(x['point']['net'] in ('PORT_4V8', 'PORT_5V3') for x in probes))
        result, _, _ = simulate(initial(source='USB'))
        self.assertEqual(result['status'], 'NO_DEMONSTRATED_FAULT_WITHIN_OBSERVATIONS')

    def test_shared_port_upstream_not_individual_switch(self):
        for cause, values in [('direct_port_supply_branch', {'PORT_4V8': 0}),
                              ('peripheral_conversion_branch', {'PORT_5V3': 0, 'PORT_4V8': 0})]:
            result, _, _ = simulate(initial(values, {m: 0 for m in r.MODULES[:3]}), values)
            self.assertIn(cause, result['candidate_causes'])
            self.assertFalse(any(c.startswith('module_power:') for c in result['candidate_causes']))

    def test_all_direct_port_permutations_harness_supply_and_return(self):
        for ports in itertools.permutations(r.DIRECT):
            for module in r.MODULES[:3]:
                mapping = dict(zip(r.MODULES, (*ports, 'J9')))
                i = initial(modules={module: 0}, ports=mapping)
                result, _, _ = simulate(i)
                self.assertEqual(result['candidate_causes'], ['module_power:' + module])
                self.assertEqual([p['point_id'] for p in result['next_step']['target_points']],
                                 [mapping[module] + '.1', mapping[module] + '.2'])

    def test_uart_uses_prior_record_and_correct_camera_order(self):
        for module in r.MODULES:
            i = initial()
            w = i['observations']['harness_continuity'][module]
            w['module_TX_to'], w['module_RX_to'] = w['module_RX_to'], w['module_TX_to']
            result, _, _ = simulate(i)
            self.assertEqual(result['candidate_causes'], ['uart_harness:' + module])
            self.assertEqual(result['evidence'][0]['observations'], ['wiring:' + module])
            self.assertEqual([x['pad'] for x in result['next_step']['target_points']], ['3', '4'])
        i = initial()
        i['observations']['harness_continuity']['GPS']['method'] = 'live_uart_dc'
        with self.assertRaises(ValueError):
            r.Session(i, P)

    def test_camera_power_interface_and_default_off(self):
        result, _, _ = simulate(initial(modules={'CAMERA': 0}), {'CAM_5V': 0, 'CAM_IO_3V3': 0})
        self.assertEqual(result['candidate_causes'], ['camera_power_branch'])
        result, _, _ = simulate(values={'CAM_IO_3V3': 0})
        self.assertEqual(result['candidate_causes'], ['camera_interface_supply_branch'])
        result, _, _ = simulate(initial(modules={'CAMERA': 0}), {'CAM_5V': 0, 'CAM_PWR_EN': 0, 'CAM_IO_3V3': 0})
        self.assertEqual(result['status'], 'INSUFFICIENT_EVIDENCE')  # enclosure crosses the EN operating floor
        result, _, _ = simulate(initial(modules={'CAMERA': 0}), {'CAM_5V': 0, 'CAM_PWR_EN': .02, 'CAM_IO_3V3': 0})
        self.assertEqual(result['status'], 'NO_DEMONSTRATED_FAULT_WITHIN_OBSERVATIONS')

    def test_combined_supported_branches(self):
        result, probes, _ = simulate(initial(modules={'GPS': 0}), {'3V3A': 0, 'CAM_IO_3V3': 0})
        self.assertEqual(set(result['candidate_causes']), {'module_power:GPS', 'sensor_supply_branch', 'camera_interface_supply_branch'})
        self.assertLessEqual(len(probes), 6)

    def test_healthy_is_no_demonstrated_fault_never_pass(self):
        result, _, _ = simulate()
        self.assertEqual(result['status'], 'NO_DEMONSTRATED_FAULT_WITHIN_OBSERVATIONS')
        self.assertEqual(result['candidate_causes'], [])
        self.assertFalse(result['physical_qualified'])
        self.assertFalse(result['firmware_verified'])

    def test_missing_not_zero_and_budget_counts_unavailable(self):
        i = initial({'3V3': None}, {m: None for m in r.MODULES})
        result, probes, _ = simulate(i, unavailable=tuple(P.points))
        self.assertEqual(result['status'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(result['candidate_causes'], [])
        self.assertEqual(len(probes), 6)
        self.assertEqual(len({x['point']['point_id'] for x in probes}), 6)

    def test_uncertainty_and_nonzero_ambiguous_sensor_remain_unresolved(self):
        i = initial({'3V3': 3.135})
        result, _, _ = simulate(i, {'3V3A': 0})
        self.assertNotIn('sensor_supply_branch', result['candidate_causes'])
        self.assertEqual(result['status'], 'INSUFFICIENT_EVIDENCE')
        result, _, _ = simulate(values={'3V3A': 1.5})
        self.assertEqual(result['status'], 'INSUFFICIENT_EVIDENCE')
        s = r.Session(initial(), P)
        m = measurement('R164.2', 0)
        m['interval'] = [-4.0, 4.0]
        s.engine.add(m)
        self.assertEqual(s.engine.causes(), {})

    def test_profile_origin_unit_time_identity_rejections(self):
        mutations = [
            lambda i: i.update(profile='M3-ASSY-R1'),
            lambda i: i.update(board_sha256='0' * 64),
            lambda i: i.update(origin='MANUAL_OFFLINE'),
            lambda i: i.update(probe_budget=7),
            lambda i: i['installed_port_map'].update(GPS='J9'),
            lambda i: i['installed_port_map'].update(RADIO='J410'),
            lambda i: i['observations']['logic_supply'].update(unit='mV'),
            lambda i: i['observations']['logic_supply'].update(epoch='old'),
            lambda i: i['observations']['logic_supply'].update(interval=[float('nan'), 3.3]),
            lambda i: i['observations']['logic_supply'].update(interval=[3.30, 3.31]),
            lambda i: i['observations']['logic_supply']['point'].update(side='F.Cu'),
            lambda i: i['observations']['logic_supply']['point'].update(xy_mm=[0, 0]),
            lambda i: i['observations']['logic_supply']['point'].update(frame='mirrored bottom'),
            lambda i: i['observations']['logic_supply']['ground'].update(net='BAT_IN'),
        ]
        for f in mutations:
            with self.subTest(mutation=f):
                i = initial(); f(i)
                with self.assertRaises(ValueError):
                    r.Session(i, P)

    def test_response_echo_pending_and_closed_session(self):
        s = r.Session(initial(), P)
        request = s.advance()
        with self.assertRaises(ValueError):
            s.advance()
        m = measurement(request['point']['point_id'], 3.3, P.point('J410.2'))
        with self.assertRaisesRegex(ValueError, 'echo'):
            s.advance(m)
        _, _, s = simulate()
        with self.assertRaisesRegex(ValueError, 'terminated'):
            s.advance()

    def test_same_net_conflict_refuses_inference_no_precision_gain(self):
        s = r.Session(initial(), P)
        s.engine.add(measurement('R164.1', 3.31))
        self.assertEqual(s.engine.interval('3V3'), [3.29, 3.32])
        s.engine.add(measurement('R164.1', 0))
        s.engine.add(measurement('R164.2', 0))
        self.assertEqual(s.engine.result()['status'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(s.engine.causes(), {})

    def test_voltage_conflict_retains_independent_uart_evidence(self):
        i = initial()
        for module in ('GPS', 'CAMERA'):
            w = i['observations']['harness_continuity'][module]
            w['module_TX_to'], w['module_RX_to'] = w['module_RX_to'], w['module_TX_to']
        s = r.Session(i, P)
        s.engine.add(measurement('R164.1', 0))
        s.engine.add(measurement('R164.2', 0))
        result = s.engine.result()
        self.assertEqual(s.engine.conflicts, {'net:3V3'})
        self.assertEqual(result['candidate_causes'], ['uart_harness:GPS', 'uart_harness:CAMERA'])
        self.assertEqual(result['evidence'], [
            {'cause': 'uart_harness:GPS', 'observations': ['wiring:GPS']},
            {'cause': 'uart_harness:CAMERA', 'observations': ['wiring:CAMERA']}])
        self.assertEqual(result['next_step']['action'], 'VERIFY_UNPOWERED_UART_ORDER')
        self.assertEqual([p['point_id'] for p in result['next_step']['target_points']], ['J410.3', 'J410.4'])
        self.assertIsNone(s.engine.next_probe())
        self.assertFalse(s.engine.screening_complete())
        self.assertFalse(result['physical_qualified'])
        self.assertFalse(result['firmware_verified'])
        schema = r.document(SCHEMA)
        validate_schema(result, schema, schema)

    def test_manual_voltage_conflict_preserves_bound_harness_finding(self):
        d = manual_record()
        w = copy.deepcopy(initial()['observations']['harness_continuity']['GPS'])
        w.update(origin='MANUAL_OFFLINE', assembly_id=d['assembly_id'], session_id=d['session_id'],
                 board_sha256=r.BOARD_SHA, harness_id='example-unchanged-gps-harness',
                 observed_at='2026-01-01T11:00:00Z', power_state='UNPOWERED', unchanged_since=True)
        w['module_TX_to'], w['module_RX_to'] = w['module_RX_to'], w['module_TX_to']
        d['harness_continuity']['GPS'] = w
        contradictory = copy.deepcopy(d['measurements'][0])
        contradictory['interval'] = [-.01, .01]
        d['measurements'].append(contradictory)
        report = r.analyze_manual(d, board=BOARD)
        self.assertEqual(report['conflicting_tokens'], ['net:3V3'])
        self.assertEqual(report['result']['candidate_causes'], ['uart_harness:GPS'])
        self.assertEqual(report['wiring_observed']['GPS'], w)
        self.assertEqual(report['observation_records']['net:3V3'], [d['measurements'][0], contradictory])
        text = r.render_zh(report)
        for marker in ('同网记录互相矛盾', 'UART 线序', 'J410.3', 'J410.4'):
            self.assertIn(marker, text)
        # A correct harness or an unavailable record supplies no fault finding.
        correct = copy.deepcopy(d)
        cw = correct['harness_continuity']['GPS']
        cw['module_TX_to'], cw['module_RX_to'] = cw['module_RX_to'], cw['module_TX_to']
        self.assertEqual(r.analyze_manual(correct, board=BOARD)['result']['candidate_causes'], [])
        unavailable = copy.deepcopy(d)
        unavailable['harness_continuity']['GPS'] = {'status': 'NOT_AVAILABLE', 'origin': 'MANUAL_OFFLINE'}
        self.assertEqual(r.analyze_manual(unavailable, board=BOARD)['result']['candidate_causes'], [])
        # Voltage conflicts must not relax the independent harness binding rules.
        for key, value in [('unchanged_since', False), ('session_id', 'other-session'),
                           ('power_state', 'POWERED'), ('observed_at', '2026-01-01T12:00:01Z')]:
            bad = copy.deepcopy(d)
            bad['harness_continuity']['GPS'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.analyze_manual(bad, board=BOARD)

    def test_bridging_interval_cannot_hide_conflicts_in_any_input_order(self):
        record = manual_record()
        readings = []
        for key, interval in [('C9.1', [3.14, 3.25]), ('R164.1', [3.20, 3.40]),
                              ('C9.1', [3.35, 3.46])]:
            m = copy.deepcopy(record['measurements'][0])
            m.update(point=P.point(key), ground=P.ground(P.point(key)), interval=interval)
            readings.append(m)
        for order in itertools.permutations(readings):
            doc = copy.deepcopy(record)
            doc['measurements'] = list(order) + [record['measurements'][1]]
            report = r.analyze_manual(doc, board=BOARD)
            self.assertEqual(report['conflicting_tokens'], ['net:3V3'])
            self.assertEqual(report['result']['status'], 'INSUFFICIENT_EVIDENCE')
            self.assertEqual(report['result']['candidate_causes'], [])
            self.assertEqual(report['observed']['net:3V3']['interval'], [3.14, 3.46])

    def test_net_envelope_never_relabels_individual_instrument_records(self):
        record = manual_record()
        a = copy.deepcopy(record['measurements'][0])
        a.update(interval=[3.14, 3.35], uncertainty_abs_v=.10, instrument='synthetic-wide-A',
                 measured_at='2026-01-01T12:00:10Z', uncertainty_basis='original basis A')
        b = copy.deepcopy(a)
        b.update(point=P.point('R164.1'), ground=P.ground(P.point('R164.1')),
                 interval=[3.29, 3.31], uncertainty_abs_v=.01, instrument='synthetic-narrow-B',
                 measured_at='2026-01-01T12:00:20Z', uncertainty_basis='original basis B')
        record['measurements'] = [a, b, record['measurements'][1]]
        report = r.analyze_manual(record, board=BOARD)
        self.assertEqual(report['observation_records']['net:3V3'], [a, b])
        envelope = report['observed']['net:3V3']
        self.assertEqual(envelope['interval'], [3.14, 3.35])
        self.assertEqual(envelope['max_declared_uncertainty_abs_v'], .10)
        self.assertNotIn('point', envelope)
        self.assertNotIn('instrument', envelope)
        self.assertNotIn('measured_at', envelope)
        rendered = r.render_zh(report)
        for marker in ('synthetic-wide-A', 'synthetic-narrow-B', 'original basis A', 'original basis B'):
            self.assertIn(marker, rendered)

    def test_camera_certainty_depends_on_enclosure_not_declared_uncertainty(self):
        for interval, uncertainties, expected in [
            ([-.018, .018], [.017, .018], 'UNKNOWN'),
            ([-.018103, .017897], [.017, .018], 'UNKNOWN'),
            ([-.3, .3], [.25, .3], 'UNKNOWN'),
            ([0, .036], [.017, .018], 'OFF'),
            ([.65, .67], [.009, .01], 'UNKNOWN'),
            ([1.1, 1.14], [.01, .02], 'ON')]:
            for u in uncertainties:
                with self.subTest(interval=interval, uncertainty=u):
                    session = r.Session(initial(), P)
                    m = measurement('R431.1', 0)
                    m.update(interval=interval, uncertainty_abs_v=u)
                    r.validate_measurement(m, P, 'SYNTHETIC_FIXTURE', 'steady_1')
                    session.engine.add(m)
                    self.assertEqual(session.engine.camera(), expected)

    def test_positive_uncertainty_never_allows_zero_width_enclosure(self):
        for u in (.01, 1e-14):
            m = measurement('C9.1', 3.3)
            m.update(interval=[3.3, 3.3], uncertainty_abs_v=u)
            with self.assertRaisesRegex(ValueError, 'understates'):
                r.validate_interval(m)
        # Normal floating-point endpoint subtraction retains its harmless rounding tolerance.
        r.validate_interval(measurement('C9.1', 3.3))

    def test_finite_endpoints_cannot_overflow_derived_width_checks(self):
        for interval, u in [([-10 ** 308, 10 ** 308], 1), ([0, 10 ** 308], 10 ** 308)]:
            with self.subTest(interval=interval, uncertainty=u):
                m = measurement('C9.1', 3.3)
                m.update(interval=interval, uncertainty_abs_v=u)
                with self.assertRaisesRegex(ValueError, 'finite number'):
                    r.validate_interval(m)

    def test_only_actual_available_evidence_and_strict_output_schema(self):
        schema = r.document(SCHEMA)
        for i, vals in [(initial(), NORMAL), (initial(modules={'GPS': 0}), {'3V3A': 0}),
                        (initial({'3V3': 0}), {'3V3': 0, 'VLOGIC': 0})]:
            result, probes, s = simulate(i, vals)
            for message in probes + [result]:
                validate_schema(message, schema, schema)
            for ev in result['evidence']:
                for token in ev['observations']:
                    if token.startswith('wiring:'):
                        self.assertEqual(s.engine.wiring[token.split(':')[1]]['status'], 'AVAILABLE')
                    else:
                        self.assertIn(token, s.engine.rows)

    def test_manual_sensor_record_and_chinese_locations(self):
        report = r.analyze_manual(manual_record(), board=BOARD)
        self.assertEqual(report['result']['candidate_causes'], ['sensor_supply_branch'])
        rendered = r.render_zh(report)
        for expected in ('MANUAL_OFFLINE', 'R164.2', 'B.Cu', '55.25', 'TP74.1', '未验证'):
            self.assertIn(expected, rendered)

    def test_manual_report_explains_ambiguous_voltage_and_control_state(self):
        report = r.analyze_manual(manual_record({'3V3': 3.3, '3V3A': 2.0,
            'CAM_PWR_EN': .8}), board=BOARD)
        self.assertEqual(report['result']['status'], 'INSUFFICIENT_EVIDENCE')
        reasons = '\n'.join(report['unresolved_reasons_zh'])
        self.assertIn('3V3A', reasons)
        self.assertIn('相机使能', reasons)
        self.assertIn('尚未确定', r.render_zh(report))

    def test_manual_source_backfeed_and_session_guards(self):
        for field, value in [('backfeed_excluded', False), ('ground_reference_verified', False),
                             ('external_self_power', True), ('selected_source', 'UNKNOWN')]:
            d = manual_record(); d['power_context'][field] = value
            report = r.analyze_manual(d, board=BOARD)
            self.assertEqual(report['result']['status'], 'INSUFFICIENT_EVIDENCE')
        for field, value in [('session_id', 'other'), ('assembly_id', 'other'), ('epoch', 'old'),
                             ('measured_at', '2025-01-01T00:00:00Z'), ('configuration_id', 'changed')]:
            d = manual_record(); d['measurements'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                r.analyze_manual(d, board=BOARD)

    def test_manual_healthy_missing_usb_and_dual_source(self):
        d = manual_record({'3V3': 3.3, '3V3A': 3.28, 'PORT_4V8': 4.8, 'CAM_5V': 5.42, 'CAM_IO_3V3': 3.3})
        def add_modules(doc, usb=False):
            obs = initial(source='USB' if usb else 'PACK')['observations']['module_supplies']
            for m, value in obs.items():
                value.update(origin='MANUAL_OFFLINE', location_kind='MANUAL_MODULE_TERMINALS', epoch=doc['epoch'])
                value.update({k: doc['measurements'][0][k] for k in r.MANUAL_META})
                doc['module_supplies'][m] = value
        add_modules(d)
        self.assertEqual(r.analyze_manual(d, board=BOARD)['result']['status'], 'NO_DEMONSTRATED_FAULT_WITHIN_OBSERVATIONS')
        bad = copy.deepcopy(d); bad['module_supplies']['GPS']['interval'] = [.09, .11]
        self.assertEqual(r.analyze_manual(bad, board=BOARD)['result']['status'], 'INSUFFICIENT_EVIDENCE')
        bad = copy.deepcopy(d); del bad['module_supplies']['GPS']
        self.assertEqual(r.analyze_manual(bad, board=BOARD)['result']['status'], 'INSUFFICIENT_EVIDENCE')
        bad = manual_record(); bad['power_context']['attached_source'] = 'BOTH'
        self.assertEqual(r.analyze_manual(bad, board=BOARD)['result']['status'], 'INSUFFICIENT_EVIDENCE')
        usb = manual_record({'3V3': 3.3, '3V3A': 3.28})
        usb['power_context'].update(attached_source='USB', selected_source='USB', source_reference_v=[4.9, 5.1], battery_path_expected=False)
        add_modules(usb, usb=True)
        self.assertEqual(r.analyze_manual(usb, board=BOARD)['result']['status'], 'NO_DEMONSTRATED_FAULT_WITHIN_OBSERVATIONS')

    def test_manual_module_harness_uses_recorded_endpoints(self):
        d = manual_record({'3V3': 3.3, 'PORT_4V8': 4.8})
        d['installed_port_map'].update(GPS='J440', AUX='J410')
        m = initial(modules={'GPS': 0}, ports=d['installed_port_map'])['observations']['module_supplies']['GPS']
        m.update(origin='MANUAL_OFFLINE', location_kind='MANUAL_MODULE_TERMINALS', epoch=d['epoch'])
        m.update({k: d['measurements'][0][k] for k in r.MANUAL_META})
        d['module_supplies']['GPS'] = m
        report = r.analyze_manual(d, board=BOARD)
        self.assertEqual(report['result']['candidate_causes'], ['module_power:GPS'])
        self.assertEqual([p['point_id'] for p in report['result']['next_step']['target_points']], ['J440.1', 'J440.2'])

    def test_uncertain_camera_enable_is_not_on_or_off(self):
        s = r.Session(initial(modules={'CAMERA': 0}), P)
        s.engine.add(measurement('J9.1', 0))
        s.engine.add(measurement('C403.1', 5.45))
        s.engine.add(measurement('R431.1', .9))
        self.assertEqual(s.engine.camera(), 'UNKNOWN')
        self.assertNotIn('camera_power_branch', s.engine.causes())

    def test_contradictory_off_supply_and_low_camera_input_stay_unresolved(self):
        _, _, s = simulate()
        s.engine.add(measurement('R431.1', 0))
        self.assertEqual(s.engine.result()['status'], 'INSUFFICIENT_EVIDENCE')
        result, _, _ = simulate(initial(modules={'CAMERA': 2.5}), {'CAM_5V': 2.5, 'CAM_IO_3V3': 0})
        self.assertNotIn('camera_interface_supply_branch', result['candidate_causes'])
        self.assertEqual(result['status'], 'INSUFFICIENT_EVIDENCE')
        s = r.Session(initial(source='USB'), P)
        s.engine.add(measurement('R164.2', 3.28))
        s.engine.add(measurement('J410.1', 4.8))
        self.assertEqual(s.engine.result()['status'], 'INSUFFICIENT_EVIDENCE')

    def test_bad_standalone_input_uses_stderr_only(self):
        i = initial(); i['board_sha256'] = '0' * 64
        proc = subprocess.run([sys.executable, '-B', str(HERE / 'r10_offline.py')], cwd=HERE,
                              input=json.dumps(i) + '\n', capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, '')
        self.assertIn('拒绝输入', proc.stderr)

    def test_manual_prior_unpowered_continuity(self):
        d = manual_record({'3V3': 3.3})
        w = copy.deepcopy(initial()['observations']['harness_continuity']['CAMERA'])
        w.update(origin='MANUAL_OFFLINE', assembly_id=d['assembly_id'], session_id=d['session_id'],
                 board_sha256=r.BOARD_SHA, harness_id='camera-harness-a', observed_at='2026-01-01T11:00:00Z',
                 power_state='UNPOWERED', unchanged_since=True)
        w['module_TX_to'], w['module_RX_to'] = w['module_RX_to'], w['module_TX_to']
        d['harness_continuity']['CAMERA'] = w
        self.assertEqual(r.analyze_manual(d, board=BOARD)['result']['candidate_causes'], ['uart_harness:CAMERA'])
        for k, v in [('power_state', 'POWERED'), ('unchanged_since', False), ('observed_at', '2026-01-01T12:00:01Z')]:
            bad = copy.deepcopy(d); bad['harness_continuity']['CAMERA'][k] = v
            with self.assertRaises(ValueError):
                r.analyze_manual(bad, board=BOARD)

    def test_json_parser_refuses_duplicates_nonfinite_and_wrong_types(self):
        for text in ('{"a":1,"a":2}', '{"v":NaN}', '{"v":Infinity}', '{"v":1e999}'):
            with self.assertRaises(ValueError):
                r.loads(text)
        i = initial(); i['observations']['logic_supply']['interval'][0] = True
        with self.assertRaises(ValueError):
            r.Session(i, P)

    def test_noarg_copied_candidate_independent_of_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            shutil.copyfile(HERE / 'r10_offline.py', stage / 'candidate.py')
            # Root's trusted profile may use different whitespace; shape/values bind it.
            (stage / 'r10_profile.json').write_text(json.dumps(P.data))
            (stage / 'point_catalog.json').write_text(json.dumps(P.points))
            result, probes, s = simulate(values={'3V3A': 0})
            input_rows = [initial()] + [measurement(x['point']['point_id'],
                          0 if x['point']['net'] == '3V3A' else NORMAL[x['point']['net']], x['ground']) for x in probes]
            proc = subprocess.run([sys.executable, '-I', '-B', str(stage / 'candidate.py')], cwd=stage,
                input=''.join(json.dumps(x) + '\n' for x in input_rows), text=True,
                capture_output=True, timeout=10)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            actual = [json.loads(line) for line in proc.stdout.splitlines()]
            self.assertEqual(actual, probes + [result])
            self.assertEqual(proc.stderr, '')
            self.assertEqual(set(p.name for p in stage.iterdir()), {'candidate.py', 'r10_profile.json', 'point_catalog.json'})

    def test_protocol_eof_does_not_invent_result(self):
        out = io.StringIO()
        with self.assertRaisesRegex(ValueError, 'EOF'):
            r.protocol(io.StringIO(json.dumps(initial()) + '\n'), out, P)
        self.assertEqual(json.loads(out.getvalue())['type'], 'probe')

    def test_exhausted_unresolved_result_has_no_unexplained_targets(self):
        result, probes, session = simulate(unavailable=tuple(P.points))
        self.assertEqual(len(probes), 6)
        self.assertEqual(result['status'], 'INSUFFICIENT_EVIDENCE')
        self.assertIsNone(result['next_step']['target_cause'])
        self.assertNotIn('target_points', result['next_step'])
        self.assertFalse(result['physical_qualified'])

    def test_host_reads_reject_symlink_fifo(self):
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / 'link'; link.symlink_to(BOARD)
            fifo = Path(tmp) / 'fifo'; os.mkfifo(fifo)
            for path in (link, fifo):
                with self.assertRaises(ValueError):
                    r.regular_bytes(path)

    def test_file_replaced_after_lstat_cannot_follow_symlink_or_block(self):
        for replacement in ('symlink', 'fifo'):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'record.json'
                path.write_bytes(b'{}')
                original = os.open
                def replace_before_open(p, flags):
                    path.unlink()
                    if replacement == 'symlink':
                        path.symlink_to(BOARD)
                    else:
                        os.mkfifo(path)
                    return original(p, flags)
                with mock.patch.object(r.os, 'open', side_effect=replace_before_open):
                    with self.assertRaises(ValueError):
                        r.regular_bytes(path)

    def test_growing_file_read_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'record.json'; path.write_bytes(b'{}')
            original = os.fstat
            def grow_after_fstat(fd):
                before = original(fd)
                path.write_bytes(b'x' * 100)
                return before
            with mock.patch.object(r.os, 'fstat', side_effect=grow_after_fstat):
                with self.assertRaisesRegex(ValueError, 'grew beyond'):
                    r.regular_bytes(path, maximum=4)

    def test_oversized_integer_is_a_controlled_input_error(self):
        record = manual_record()
        record['measurements'][0]['interval'][1] = 10 ** 1000
        with self.assertRaisesRegex(ValueError, 'finite number'):
            r.analyze_manual(record, board=BOARD)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'record.json'; path.write_text(json.dumps(record))
            proc = subprocess.run([sys.executable, '-B', str(HERE / 'r10_offline.py'),
                'manual', str(path), '--board', str(BOARD)], capture_output=True, text=True, timeout=5)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(proc.stdout, '')
            self.assertNotIn('Traceback', proc.stderr)

    def test_points_cli_supplies_native_identities_and_ground_without_hardware(self):
        proc = subprocess.run([sys.executable, '-B', '-m', 'diagnostics.r10_offline',
            'points', '--board', str(BOARD), '--json'], cwd=HERE.parent,
            capture_output=True, text=True, timeout=5)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = json.loads(proc.stdout)
        self.assertEqual({row['point']['point_id'] for row in rows},
                         {k for k,p in P.points.items() if p['net'] != 'GND'})
        for row in rows:
            P.identity(row['point'])
            P.identity(row['ground'], ground=True)
        proc = subprocess.run([sys.executable, '-B', '-m', 'diagnostics.r10_offline',
            'points', '--board', str(SCHEMA)], cwd=HERE.parent,
            capture_output=True, text=True, timeout=5)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, '')


if __name__ == '__main__':
    unittest.main()
