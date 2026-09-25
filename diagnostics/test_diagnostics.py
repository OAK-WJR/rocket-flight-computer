"""Fault-driven regression, including the pinned real MinimalMemAP implementation."""
import copy
import inspect
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import Mock, patch

from .engine import HERE, analyze, digest, load_json, validate_snapshot
from .registers import REGISTERS, CPUID_MASK, EXPECTED_CPUID, RESET_BITS
from .transport import capture, PyOCDReader, ReadOnlyAPGuard, atomic_json

BINDING = load_json(HERE/'board_binding.json')


class SyntheticReader:
    """Fabricated register responses ONLY; never presents itself as a board."""
    def __init__(self, overrides=None):
        self.values = dict(CPUID=0x411FC271, DBGMCU_IDCODE=0x20030450,
                           FLASH_SIZE_KIB=2048, UID0=0, UID1=0x01234567, UID2=0x89ABCDEF,
                           RCC_RSR=1 << 23, RCC_CR=5, RCC_CFGR=0,
                           PWR_D3CR=0x6000, CFSR=0, HFSR=0, MMFAR=0, BFAR=0)
        self.values.update(overrides or {})
        self.seen = []
        self.closed = False
    def open(self):
        return {'kind': 'SYNTHETIC_FIXTURE', 'not_a_hardware_driver': True}
    def read(self, name):
        self.seen.append(name)
        v = self.values[name]
        if isinstance(v, Exception):
            raise v
        return v
    def close(self):
        self.closed = True


def fixture(overrides=None):
    reader = SyntheticReader(overrides)
    with tempfile.TemporaryDirectory() as d:
        s = capture(reader, BINDING, 'SYNTHETIC-NOT-A-BOARD', Path(d)/'raw.json',
                    origin='SYNTHETIC_FIXTURE', pause=lambda _: None)
    return s


def statuses(report):
    return {c['id']: c['status'] for c in report['checks']}


def bench_fixture(s, overrides=None, rin=10e6):
    voltages = {'VBUS': 5., 'VLOGIC': 4.6, '3V3': 3.3, '3V3A': 3.29,
                'VLOGIC_SENSE': 4.6/11, 'V3V3_SENSE': 1.65}
    voltages.update(overrides or {})
    return dict(schema=1, origin='SYNTHETIC_FIXTURE', assembly_id=s['assembly_id'],
                capture_id=s['capture_id'], board_sha256=BINDING['board_sha256'],
                points=[dict(net=n, **BINDING['probes'][n], measurement=dict(
                    value=v, unit='V', uncertainty_v=.002, input_ohm=rin,
                    instrument='SYNTHETIC METER', measured_at=s['captured_at'])) for n, v in voltages.items()])


class FaultTests(unittest.TestCase):
    def test_normal_blank_firmware_is_not_false_hse_failure_or_board_pass(self):
        r = analyze(fixture(), BINDING)
        self.assertEqual(r['overall'], 'INCOMPLETE')
        self.assertEqual(statuses(r)['HSE_STATE'], 'NOT_TESTED')
        self.assertEqual(statuses(r)['BOARD_UID'], 'PASS')  # a zero word is legitimate
        self.assertEqual(statuses(r)['GNSS'], 'NOT_POPULATED')
        self.assertFalse(r['fabrication_release'])
        self.assertTrue(r['synthetic'])

    def test_cpuid_variant_not_hardcoded(self):
        r = analyze(fixture({'CPUID': 0x412FC273}), BINDING)
        self.assertEqual(statuses(r)['DBG_IDENTITY'], 'PASS')

    def test_wrong_device_stops_before_family_addresses(self):
        reader = SyntheticReader({'DBGMCU_IDCODE': 0x12300483})
        with tempfile.TemporaryDirectory() as d:
            s = capture(reader, BINDING, 'fake', Path(d)/'s.json', 'SYNTHETIC_FIXTURE')
        self.assertEqual(reader.seen, ['CPUID', 'DBGMCU_IDCODE'])
        self.assertTrue(reader.closed)
        self.assertEqual(statuses(analyze(s, BINDING))['DBG_IDENTITY'], 'FAIL')

    def test_wrong_capacity_not_silently_accepted_fallback(self):
        self.assertEqual(statuses(analyze(fixture({'FLASH_SIZE_KIB': 1024}), BINDING))['FLASH_CAPACITY'], 'FAIL')

    def test_transport_error_preserved_never_zero_substitute(self):
        s = fixture({'RCC_RSR': TimeoutError('probe read timeout')})
        self.assertEqual(s['state'], 'PARTIAL')
        self.assertIsNone(next(r for r in s['reads'] if r['name']=='RCC_RSR')['value'])
        self.assertEqual(statuses(analyze(s, BINDING))['RESET_HISTORY'], 'NOT_TESTED')

    def test_failed_connect_closes_and_keeps_evidence(self):
        r = SyntheticReader()
        r.open = Mock(side_effect=OSError('No probe'))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'s.json'
            s = capture(r, BINDING, 'fake', p, 'SYNTHETIC_FIXTURE')
            self.assertEqual(load_json(p)['state'], 'CONNECTION_FAILED')
        self.assertEqual(s['reads'], [])
        self.assertTrue(r.closed)
        self.assertEqual(statuses(analyze(s, BINDING))['DBG_LINK'], 'INCONCLUSIVE')

    def test_clock_changes_are_not_combined_into_fake_snapshot(self):
        s = fixture()
        for row in s['reads']:
            if row['name']=='RCC_CR' and row['sample']==1:
                row['value'] = '0x00030005'
        self.assertEqual(statuses(analyze(s, BINDING))['CLOCK_SNAPSHOT'], 'INCONCLUSIVE')

    def test_sticky_watchdog_is_history_not_unique_diagnosis(self):
        r = analyze(fixture({'RCC_RSR': (1 << 26) | (1 << 23)}), BINDING)
        c = next(c for c in r['checks'] if c['id']=='RESET_HISTORY')
        self.assertEqual(c['status'], 'INFO')
        self.assertEqual(set(c['evidence']), {'POR', 'IWDG1'})

    def test_fault_address_requires_valid_bit(self):
        r = analyze(fixture({'HFSR': 1 << 30, 'BFAR': 0x12345678}), BINDING)
        c = next(c for c in r['checks'] if c['id']=='CPU_FAULT_FLAGS')
        self.assertEqual(c['status'], 'WARNING')
        self.assertNotIn('BFAR', c['evidence'])
        r = analyze(fixture({'CFSR': 1 << 15, 'BFAR': 0x12345678}), BINDING)
        self.assertEqual(next(c for c in r['checks'] if c['id']=='CPU_FAULT_FLAGS')['evidence']['BFAR'], 0x12345678)

    def test_corrupted_evidence_rejected(self):
        for kind in ('duplicate', 'wrong_address', 'value_and_error', 'wrong_revision', 'unknown_origin'):
            s = fixture()
            if kind == 'duplicate': s['reads'].append(copy.deepcopy(s['reads'][0]))
            if kind == 'wrong_address': s['reads'][0]['address'] = '0x00000000'
            if kind == 'value_and_error': s['reads'][0]['error'] = 'timeout'
            if kind == 'wrong_revision': s['board_sha256'] = '0'*64
            if kind == 'unknown_origin': s['origin'] = 'UNSPECIFIED'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                analyze(s, BINDING)

    def test_empty_bench_does_not_pass_voltage_checks(self):
        s = fixture(); b = bench_fixture(s)
        for p in b['points']: p['measurement'] = None
        r = analyze(s, BINDING, b)
        self.assertEqual(statuses(r)['DC_3V3'], 'NOT_TESTED')

    def test_filter_open_localizes_after_main_rail(self):
        s = fixture(); r = analyze(s, BINDING, bench_fixture(s, {'3V3A': .05}))
        c = next(c for c in r['checks'] if c['id']=='POWER_PATH')
        self.assertEqual(c['status'], 'FAIL')
        self.assertIn('L2', c['next_step'])
        self.assertEqual(r['overall'], 'ISSUES_FOUND')

    def test_upper_lower_divider_swap_detected(self):
        s = fixture(); r = analyze(s, BINDING, bench_fixture(s, {'VLOGIC_SENSE': 4.18}))
        self.assertEqual(statuses(r)['DIV_VLOGIC'], 'FAIL')

    def test_meter_loading_is_included(self):
        s = fixture()
        # Deliberately low-impedance meter: loaded output = 4.6 / 21, not /11.
        b = bench_fixture(s, {'VLOGIC_SENSE': 4.6/21}, rin=10000)
        self.assertEqual(statuses(analyze(s, BINDING, b))['DIV_VLOGIC'], 'INFO')

    def test_uncertainty_crosses_voltage_screen_boundary(self):
        s = fixture(); b = bench_fixture(s, {'3V3': 3.134})
        self.assertEqual(statuses(analyze(s, BINDING, b))['DC_3V3'], 'INCONCLUSIVE')

    def test_bench_wrong_board_session_and_missing_error_budget_rejected(self):
        s = fixture()
        for key in ('capture_id', 'board_sha256', 'origin', 'uncertainty_v'):
            b = bench_fixture(s)
            if key == 'uncertainty_v': del b['points'][0]['measurement'][key]
            else: b[key] = 'wrong'
            with self.subTest(key=key), self.assertRaises(ValueError):
                analyze(s, BINDING, b)

    def test_existing_evidence_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'s.json'; p.write_text('ORIGINAL')
            with self.assertRaises(FileExistsError):
                capture(SyntheticReader(), BINDING, 'fake', p)
            self.assertEqual(p.read_text(), 'ORIGINAL')

    def test_ap_guard_blocks_all_memory_writes_and_unknown_reads(self):
        dp = Mock()
        guard = ReadOnlyAPGuard(dp)
        guard.write_ap(0, 0x03000012)
        guard.write_ap(4, 0xE000ED00)
        for address, value in [(0x0C, 1), (0x10, 1), (0, 0), (4, 0x08000000), (0x1000004, 0)]:
            with self.assertRaises(RuntimeError): guard.write_ap(address, value)
        self.assertEqual(dp.write_ap.call_count, 2)

    def test_bad_ap_id_is_rejected_without_python_assert(self):
        dp = Mock(); dp.read_ap.return_value = 0
        with self.assertRaises(RuntimeError): ReadOnlyAPGuard(dp).read_ap(0xFC)
        dp.write_ap.assert_not_called()

    def test_duplicate_json_and_nonfinite_measurements_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'bad.json'
            for text in ('{"value":1,"value":2}', '{"value":NaN}'):
                p.write_text(text)
                with self.assertRaises(ValueError): load_json(p)
        s = fixture(); b = bench_fixture(s)
        b['points'][0]['measurement']['value'] = float('inf')
        with self.assertRaises(ValueError): analyze(s, BINDING, b)

    def test_real_pyocd_minimal_ap_works_through_guard(self):
        from pyocd.coresight.minimal_mem_ap import MinimalMemAP
        dp = Mock()
        dp.read_ap.side_effect = [0x24770011, 0x411FC271]
        guard = ReadOnlyAPGuard(dp)
        ap = MinimalMemAP(guard)
        ap.init()
        self.assertEqual(ap.read32(REGISTERS['CPUID'][0]), 0x411FC271)
        with self.assertRaises(RuntimeError): ap.write32(REGISTERS['CPUID'][0], 1)
        self.assertFalse(any(c.args[0]==0x0C for c in dp.write_ap.call_args_list))

    def test_reader_uses_probe_only_session_no_init(self):
        from pyocd.core.session import Session
        probe = Mock(unique_id='EXACT-ID', description='Synthetic API test probe')
        probe.create_associated_board.return_value = None
        # Real Session construction proves isolated config and built-in target
        # construction without invoking target.init/flash methods.
        with patch('diagnostics.transport.probes', return_value=[probe]), \
             patch.object(Session, 'open') as open_session, \
             patch('pyocd.coresight.dap.DebugPort.connect'), \
             patch('pyocd.coresight.dap.DebugPort.power_up_debug', return_value=True), \
             patch('pyocd.coresight.dap.DebugPort.read_ap', return_value=0x24770011), \
             patch('pyocd.coresight.dap.DebugPort.write_ap'), \
             patch('pyocd.coresight.dap.DebugPort.disconnect'):
            r = PyOCDReader('EXACT-ID')
            try:
                result = r.open()
                open_session.assert_called_once_with(init_board=False)
                self.assertFalse(result['target_init_executed'])
                self.assertFalse(r.session.options.get('auto_unlock'))
                self.assertTrue(r.session.options.get('no_config'))
                self.assertIsNone(r.session.delegate)
                self.assertFalse(r.session.target.cores)
            finally: r.close()

    def test_binding_still_names_actual_board(self):
        board = HERE.parent/'m3_core/review/m3_core.kicad_pcb'
        if not board.exists(): self.skipTest('Standalone diagnostics archive; no PCB included')
        self.assertEqual(digest(board), BINDING['board_sha256'])

    def test_primary_source_hashes_and_constants(self):
        for row in load_json(HERE/'sources/manifest.json'):
            self.assertEqual(digest(HERE/'sources'/row['file']), row['sha256'])
        h = (HERE/'sources/stm32h743xx.h').read_text()
        for symbol, value in [('UID_BASE', '0x1FF1E800'), ('FLASHSIZE_BASE', '0x1FF1E880'), ('DBGMCU_BASE', '0x5C001000')]:
            self.assertRegex(h, r'#define '+symbol+r'\s+\('+value+r'UL\)')
        for bit, suffix in RESET_BITS.items():
            name = {'CPU':'CPURSTF','D1':'D1RSTF','D2':'D2RSTF','BOR':'BORRSTF','PIN':'PINRSTF',
                    'POR':'PORRSTF','SOFTWARE':'SFTRSTF','IWDG1':'IWDG1RSTF',
                    'WWDG1':'WWDG1RSTF','LOW_POWER':'LPWRRSTF'}[suffix]
            self.assertRegex(h, rf'#define RCC_RSR_{name}_Pos\s+\({bit}U\)')
        self.assertRegex(h, r'RSR;[^\n]*Address offset: 0xD0')
        self.assertRegex(h, r'CFGR;[^\n]*Address offset: 0x10')
        arm = (HERE/'sources/core_cm7.h').read_text()
        for name, bit in [('IMPLEMENTER',24),('VARIANT',20),('PARTNO',4),('REVISION',0)]:
            self.assertRegex(arm, rf'SCB_CPUID_{name}_Pos\s+{bit}U')

    def test_register_addresses_derived_from_primary_headers(self):
        # Resolve the small, explicit macro/structure subset from original
        # vendor text, rather than comparing two copies of our address table.
        import ast
        text = (HERE/'sources/stm32h743xx.h').read_text() + '\n' + (HERE/'sources/core_cm7.h').read_text()
        def macro(name):
            line = re.search(r'^#define\s+'+name+r'\s+(.+)$', text, re.M).group(1).split('/*')[0].strip()
            line = re.sub(r'(0x[0-9a-fA-F]+|\d+)(?:UL|U)\b', r'\1', line)
            def resolve(n):
                if isinstance(n, ast.Constant) and type(n.value) is int: return n.value
                if isinstance(n, ast.Name): return macro(n.id)
                if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add): return resolve(n.left)+resolve(n.right)
                raise ValueError('Unsupported vendor macro: '+line)
            return resolve(ast.parse(line, mode='eval').body)
        def offset(type_name, field):
            block = re.search(r'typedef struct\s*\{([^{}]*)\}\s*'+type_name+r';', text).group(1)
            return int(re.search(r"\b"+field+r";[^\n]*?offset:\s*(0x[0-9a-fA-F]+)", block, re.I).group(1), 16)
        for name, base, type_name, field in [
                ('RCC_RSR','RCC_BASE','RCC_TypeDef','RSR'),('RCC_CR','RCC_BASE','RCC_TypeDef','CR'),
                ('RCC_CFGR','RCC_BASE','RCC_TypeDef','CFGR'),('PWR_D3CR','PWR_BASE','PWR_TypeDef','D3CR'),
                ('CPUID','SCB_BASE','SCB_Type','CPUID'),('CFSR','SCB_BASE','SCB_Type','CFSR'),
                ('HFSR','SCB_BASE','SCB_Type','HFSR'),('MMFAR','SCB_BASE','SCB_Type','MMFAR'),
                ('BFAR','SCB_BASE','SCB_Type','BFAR')]:
            with self.subTest(register=name):
                self.assertEqual(REGISTERS[name][0], macro(base)+offset(type_name,field))


if __name__ == '__main__':
    unittest.main()
