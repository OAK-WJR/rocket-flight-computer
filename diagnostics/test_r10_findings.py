"""Saved evidence and actual C-record localization; no physical target access."""
import ctypes
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnostics import r10_firmware as r
from diagnostics import r10_findings as f
from diagnostics import test_r10_firmware as fixtures
from m3_firmware.r10 import test_r10 as cfixtures

BOARD = fixtures.BOARD


class Localization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfixtures.ActualC.setUpClass()

    @classmethod
    def tearDownClass(cls):
        cfixtures.ActualC.tearDownClass()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image, self.identity = fixtures.bundle(self.root)

    def capture(self, name='case', fillers=(), *, close_error=False, fault=False, stale=False):
        run = self.root / name
        req = r.prepare(BOARD, self.root / 'manifest.json', self.root / 'image.bin', run,
                        'SYNTHETIC-LOCALIZATION', 'FAKE-PROBE', bench_isolated=True,
                        reset_boot_confirmed=True, origin='SYNTHETIC_FIXTURE')
        reader = fixtures.FakeReader(self.image, self.identity, close_error=close_error, fault=fault)
        if not fault:
            for i, words in enumerate(reader.frames):
                buffer = (ctypes.c_uint32 * 256)(*words)
                for kind, mode in fillers:
                    function = getattr(cfixtures.ActualC.lib, 'r10_test_' + kind + '_record')
                    function(buffer, mode)
                words[:] = buffer[:]
                if fillers and fillers[0][0] == 'flash':
                    # Core fixtures retain real model batch times rather than moving
                    # them to the outer fake MCU publication clock.
                    words[5] = (4000 if i else 1000) if fillers[0][1] >= 3 else 1000
                    words[7] = words[5]
                if stale:
                    words[5] = 5000 + i
                    words[7] = words[5]
                words[-1] = zlib.crc32(struct.pack('<255I', *words[:-1]))
        code = r.worker(run, BOARD, lambda _: reader, pause=lambda _: None)
        r.write_new(run / 'supervision.json', dict(schema='r10-firmware-supervision/v1',
            run_id=req['run_id'], request_sha256=r.sha_bytes(r.canonical(req)),
            worker_exit_code=code, worker_pid=None, timed_out=False, error=None, completed_at=r.utc()))
        result = r.report(run, BOARD, self.root / (name + '-report'))
        return result, (self.root / (name + '-report') / 'report.md').read_text()

    def codes(self, result):
        return {v['code'] for v in result['fault_localization']['findings']}

    def test_complete_report_keeps_all_off_distinct_from_defective(self):
        result, text = self.capture()
        self.assertEqual(self.codes(result), {'FLASH_OFF', 'IMU_OFF', 'BARO_OFF', 'VOLTAGE_OFF'})
        self.assertIn('尚未启动', text)
        self.assertEqual(result['fault_localization']['confirmed_defects'], [])

    def test_quad_mismatch_identifies_all_reviewed_lanes_without_claiming_a_bad_lane(self):
        result, text = self.capture(fillers=(('flash', 8),))
        self.assertIn('FLASH_QUAD_INTERFACE', self.codes(result))
        finding = next(v for v in result['fault_localization']['findings'] if v['code'] == 'FLASH_QUAD_INTERFACE')
        self.assertEqual(finding['category'], 'recorded_fault')
        self.assertEqual(finding['circuit']['fitted_value'], 'W25Q128JVSIQ')
        endpoints = finding['circuit']['signals']['QSPI_IO2']
        self.assertEqual({v['endpoint'] for v in endpoints}, {'U1.1', 'U3.3'})
        self.assertIn('ee17ef17', text)
        self.assertIn('不能凭此指定某一根线损坏', text)

    def test_native_unsupported_revision_is_a_controller_issue_not_replacement_advice(self):
        result, text = self.capture(fillers=(('flash', 10),))
        self.assertIn('FLASH_CONTROLLER', self.codes(result))
        self.assertIn('DEVICE_REVISION', text)
        self.assertIn('不能定位为外部芯片损坏', text)

    def test_busy_and_qe_mismatch_keep_state_and_never_request_recovery_writes(self):
        for mode, code in ((6, 'FLASH_DEVICE_STATE'), (7, 'FLASH_PROFILE')):
            with self.subTest(mode=mode):
                result, text = self.capture(str(mode), fillers=(('flash', mode),))
                self.assertIn(code, self.codes(result))
                self.assertFalse(result['fault_localization']['automatic_target_actions'])
                self.assertIn('不提出自动' if mode == 6 else '不要据此自动写 QE', text)

    def test_read_failure_retains_last_good_bytes_and_possible_power_and_interface_causes(self):
        result, text = self.capture(fillers=(('flash', 3),))
        self.assertIn('FLASH_INTERFACE', self.codes(result))
        self.assertEqual(result['records'][1]['flash']['sample_raw']['quad_id'], 'ef17ef17')
        self.assertIn('R10', text)
        self.assertIn('可能原因（未确认）', text)

    def test_clean_up_failure_is_separate_from_original_transaction_error(self):
        result, text = self.capture(fillers=(('flash', 5),))
        self.assertIn('FLASH_CLEANUP', self.codes(result))
        self.assertIn('FLASH_INTERFACE', self.codes(result))
        self.assertIn('不自动重试', text)
        self.assertEqual(result['records'][1]['flash']['state'], 'STOPPED')

    def test_recovery_keeps_history_separate_from_present_error(self):
        result, text = self.capture(fillers=(('flash', 4),))
        self.assertIn('FLASH_HISTORY', self.codes(result))
        self.assertIn('FLASH_SAMPLE', self.codes(result))
        self.assertIn('历史错误不等于当前持续故障', text)

    def test_stale_data_is_never_a_fresh_sample_or_a_failed_chip(self):
        result, text = self.capture(fillers=(('flash', 1),), stale=True)
        self.assertIn('FLASH_STALE', self.codes(result))
        self.assertNotIn('FLASH_SAMPLE', self.codes(result))
        self.assertEqual(result['fault_localization']['confirmed_defects'], [])
        self.assertIn('发布时已经过期', text)

    def test_incomplete_capture_suppresses_localization_even_with_valid_sensor_records(self):
        result, text = self.capture(fillers=(('flash', 8),), close_error=True)
        self.assertFalse(result['complete_capture'])
        self.assertEqual(self.codes(result), {'CAPTURE_INCOMPLETE'})
        self.assertEqual(result['records'][1]['flash']['error'], 'QUAD_IDENTITY')
        self.assertIn('只保留原始记录', text)

    def test_core_fault_suppresses_inactive_peripheral_interpretation(self):
        result, text = self.capture(fault=True)
        self.assertEqual(self.codes(result), {'MCU_FAULT'})
        self.assertIn('无效 BFAR/MMFAR', text)

    def test_adc_raw_range_and_pin_drift_have_different_inspection_paths(self):
        for mode, code in ((4, 'VOLTAGE_ANALOG_EVIDENCE'), (6, 'VOLTAGE_CONTROLLER')):
            with self.subTest(mode=mode):
                result, text = self.capture(str(mode), fillers=(('voltage', mode),))
                self.assertIn(code, self.codes(result))
                if mode == 4:
                    self.assertIn('4294967295', text)
                    self.assertIn('R60.2', text)
                    self.assertIn('独立仪表', text)
                else:
                    self.assertIn('CONFIGURATION', text)

    def test_baro_crc_localizes_calibration_and_i2c_not_pressure_port_geometry(self):
        result, text = self.capture(fillers=(('baro', 2),))
        self.assertIn('BARO_CALIBRATION_DATA', self.codes(result))
        self.assertIn('U5.7', text)
        self.assertIn('R12/R13', text)
        self.assertEqual(result['records'][1]['baro']['pressure_pa'], 100009)

    def test_imu_polling_failure_does_not_blame_drdy_interrupt_wire(self):
        result, text = self.capture(fillers=(('sensor', 2),))
        self.assertIn('IMU_INTERFACE', self.codes(result))
        self.assertIn('不能据此把原因指定为 INT1', text)
        self.assertIn('U4.12', text)

    def test_positive_samples_do_not_qualify_a_synthetic_or_physical_board(self):
        result, text = self.capture(fillers=(('sensor', 0), ('baro', 0), ('voltage', 1)))
        self.assertTrue({'IMU_SAMPLE', 'BARO_SAMPLE', 'VOLTAGE_SAMPLE'} <= self.codes(result))
        loc = result['fault_localization']
        self.assertEqual(loc['origin'], 'SYNTHETIC_FIXTURE')
        self.assertFalse(loc['hardware_qualified'])
        self.assertFalse(loc['physical_fault_localization_verified'])
        self.assertTrue(all(not v['confirmed_component_failure'] for v in loc['findings']))

    def test_catalog_comes_from_checked_native_sources_and_refuses_wrong_board(self):
        c = f.catalog(BOARD)
        self.assertEqual(c['baro']['power_points'][0]['point']['net'], '3V3A')
        self.assertEqual(c['flash']['power_points'][0]['point']['net'], '3V3')
        self.assertEqual(c['voltage']['power_points'][0]['point']['net'], 'VLOGIC')
        wrong = self.root / 'wrong.kicad_pcb'
        wrong.write_bytes(b'wrong board')
        with self.assertRaises(ValueError):
            f.catalog(wrong)
        with mock.patch.object(f.flash_binding, 'NET_SHA', '0' * 64), self.assertRaises(ValueError):
            f.catalog(BOARD)

    def test_analysis_code_hash_is_separate_from_acquisition_grants(self):
        result, _ = self.capture()
        loc = result['fault_localization']
        self.assertIn('diagnostics/r10_findings.py', loc['circuit_sources'])
        self.assertNotIn('diagnostics/r10_findings.py', r.SOURCES)
        self.assertEqual(loc['circuit_sources']['diagnostics/r10_findings.py'],
                         r.sha_bytes((r.ROOT / 'diagnostics/r10_findings.py').read_bytes()))

    def test_original_abi5_capture_replays_after_analysis_extension_without_new_keys_or_grants(self):
        fixture = json.loads((r.ROOT / 'diagnostics/fixtures/r10_v5_capture.json').read_text())
        self.assertEqual(fixture['origin'], 'SYNTHETIC_FIXTURE')
        run = self.root / 'old-v5'
        run.mkdir()
        for name, data in fixture['files'].items():
            (run / name).write_bytes(bytes.fromhex(data['hex']) if 'hex' in data else data['text'].encode())
        with mock.patch.object(r, 'utc', return_value='2026-11-04T00:00:00+00:00'):
            result = r.analyze(run, BOARD)
        self.assertTrue(result['complete_capture'])
        self.assertEqual(set(r.document(run / 'request.json')['tool_sources']), set(r.SOURCES))
        self.assertNotIn('diagnostics/r10_findings.py', r.document(run / 'request.json')['tool_sources'])
        addresses = [op[2] for op in r.document(run / 'snapshot.json')['operations']
                     if op[1] == 4 and r.RAM <= op[2] < r.RAM + 2048]
        self.assertEqual(max(addresses), r.RAM + 1020)
        self.assertIn('FLASH_HISTORY', self.codes(result))

    def test_core_timebase_error_precedes_retained_native_error_detail(self):
        # Both acquisition cores preserve detail when failed(TIMEBASE) runs
        # while already retrying. No hardware failure is implied by that old
        # native reason, even though it remains valuable raw history.
        for subsystem in ('flash', 'voltage'):
            for old_reason in ('CLOCK', 'DEVICE_REVISION', 'CONFIGURATION'):
                with self.subTest(subsystem=subsystem, old_reason=old_reason):
                    code, observed, causes, checks = f._cause(subsystem, dict(
                        error='TIMEBASE', current_driver_failure={'reason': old_reason}))
                    self.assertEqual(code, 'TIMEBASE')
                    self.assertIn('时间基准', observed)
                    self.assertIn('时间基准', ' '.join(checks))
                    self.assertNotIn('外部芯片损坏', ' '.join(causes))

    def test_historical_abi_missing_fields_are_not_failed_devices(self):
        for abi, expected in ((3, {'FLASH_LEGACY', 'VOLTAGE_LEGACY'}),
                              (4, {'FLASH_LEGACY'})):
            with self.subTest(abi=abi):
                saved = json.loads((r.ROOT / ('diagnostics/fixtures/r10_v%d_capture.json' % abi)).read_text())
                run = self.root / ('old-v%d' % abi)
                run.mkdir()
                for name, value in saved['files'].items():
                    (run / name).write_bytes(bytes.fromhex(value['hex']) if 'hex' in value else value['text'].encode())
                with mock.patch.object(r, 'utc', return_value='2026-11-04T00:00:00+00:00'):
                    result = r.analyze(run, BOARD)
                self.assertTrue(expected <= self.codes(result))
                missing = [v for v in result['fault_localization']['findings'] if v['code'] in expected]
                self.assertTrue(all(v['category'] == 'historical_abi' for v in missing))

    def test_missing_trace_or_sequence_evidence_stays_a_capture_problem(self):
        run = self.root / 'no-image'
        req = r.prepare(BOARD, self.root / 'manifest.json', self.root / 'image.bin', run,
                        'SYNTHETIC-LOCALIZATION', 'FAKE-PROBE', bench_isolated=True,
                        reset_boot_confirmed=True, origin='SYNTHETIC_FIXTURE')
        reader = fixtures.FakeReader(self.image, self.identity, bad_image=True)
        code = r.worker(run, BOARD, lambda _: reader, pause=lambda _: None)
        r.write_new(run / 'supervision.json', dict(schema='r10-firmware-supervision/v1',
            run_id=req['run_id'], request_sha256=r.sha_bytes(r.canonical(req)), worker_exit_code=code,
            worker_pid=None, timed_out=False, error=None, completed_at=r.utc()))
        result = r.analyze(run, BOARD)
        self.assertEqual(self.codes(result), {'CAPTURE_INCOMPLETE'})
        self.assertFalse(result['image_bytes_match'])
        self.assertEqual(reader.ram_reads, 0)


if __name__ == '__main__':
    unittest.main()
