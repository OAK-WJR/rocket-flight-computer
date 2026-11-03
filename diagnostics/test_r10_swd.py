"""R10 capture faults and provenance. All register values are synthetic."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnostics import r10_swd as r
from diagnostics import r10_offline as offline
from diagnostics.registers import REGISTERS

BOARD = r.ROOT / 'm3_design/assembly_review/m3.kicad_pcb'


class FakeReader:
    def __init__(self, values=None, open_error=None, close_error=None):
        self.values = dict(CPUID=0x411FC271, DBGMCU_IDCODE=0x20030450, FLASH_SIZE_KIB=2048,
            UID0=0, UID1=0x12345678, UID2=0xABCDEF01, RCC_RSR=1 << 23,
            RCC_CR=5, RCC_CFGR=0, PWR_D3CR=0x6000, CFSR=0, HFSR=0, MMFAR=0, BFAR=0)
        self.values.update(values or {})
        self.seen, self.closed = [], False
        self.open_error, self.close_error = open_error, close_error

    def open(self):
        if self.open_error:
            raise self.open_error
        return {'kind': 'SYNTHETIC_FIXTURE', 'not_a_hardware_driver': True}

    def read(self, name):
        self.seen.append(name)
        value = self.values[name]
        if isinstance(value, Exception):
            raise value
        return value

    def close(self):
        self.closed = True
        if self.close_error:
            raise self.close_error


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / 'capture'

    def stage(self, reader=None, *, supervised=True):
        reader = reader or FakeReader()
        req = r.prepare(BOARD, 'SYNTHETIC-NOT-A-BOARD', 'FAKE-PROBE', self.run,
                        bench_isolated=True, origin='SYNTHETIC_FIXTURE')
        code = r.worker(self.run, BOARD, reader_factory=lambda _: reader, pause=lambda _: None)
        if supervised:
            r.write_new(self.run / 'supervision.json', dict(schema='r10-swd-supervision/v1',
                run_id=req['run_id'], request_sha256=r.sha_bytes(r.canonical(req)),
                worker_exit_code=code, timed_out=False, error=None, completed_at=r.utc()))
        return reader, r.document(self.run / 'snapshot.json')

    def overwrite(self, name, value):
        (self.run / name).write_text(json.dumps(value))

    def test_native_j2_is_distinct_from_old_binding(self):
        old = (r.HERE / 'board_binding.json').read_bytes()
        value = r.binding(BOARD)
        self.assertEqual([value['connector'][str(i)]['role'] for i in range(1, 7)],
                         ['3V3', 'SWDIO', 'NRST', 'SWCLK', 'GND', 'NC'])
        self.assertEqual(value['connector']['1']['xy_mm'], [3.73, 40.035])
        self.assertEqual(value['connector']['5']['net'], 'GND')
        self.assertTrue(value['connector']['6']['net'].startswith('unconnected-'))
        self.assertEqual((r.HERE / 'board_binding.json').read_bytes(), old)

    def test_normal_register_capture_is_not_firmware_or_board_qualification(self):
        reader, raw = self.stage()
        report = r.analyze(self.run, BOARD)
        self.assertTrue(reader.closed)
        self.assertEqual(len(reader.seen), len(REGISTERS) + 3)
        self.assertTrue(report['complete_register_capture'])
        self.assertEqual(report['overall'], 'INCOMPLETE')
        self.assertEqual(report['origin'], 'SYNTHETIC_FIXTURE')
        for name in ('hardware_qualified', 'firmware_verified', 'fabrication_release', 'physical_board_identity_verified'):
            self.assertIs(report[name], False)
        self.assertEqual(raw['board_sha256'], r.BOARD_SHA)

    def test_wrong_board_and_missing_bench_context_fail_before_transport(self):
        bad = self.root / 'old.pcb'; bad.write_text('not current R10')
        with self.assertRaises(ValueError):
            r.prepare(bad, 'A', 'P', self.run, bench_isolated=True)
        self.assertFalse(self.run.exists())
        with self.assertRaises(ValueError):
            r.prepare(BOARD, 'A', 'P', self.run, bench_isolated=False)
        self.assertFalse(self.run.exists())
        with mock.patch.object(r, 'supervise') as supervise, contextlib.redirect_stderr(io.StringIO()):
            code = r.main(['capture', '--board', str(bad), '--out', str(self.run),
                           '--probe-id', 'P', '--assembly-id', 'A', '--bench-isolated'])
        self.assertEqual(code, 3)
        supervise.assert_not_called()

    def test_connection_failure_still_produces_correct_r10_pin_guidance(self):
        reader, raw = self.stage(FakeReader(open_error=OSError('synthetic no probe')))
        report = r.write_report(self.run, BOARD, self.root / 'analysis')
        self.assertTrue(reader.closed)
        self.assertEqual(raw['reads'], [])
        self.assertEqual(raw['state'], 'CONNECTION_FAILED')
        text = r.markdown(report)
        self.assertIn('J2.1=3V3 reference', text)
        self.assertIn('J2.5=GND', text)
        self.assertNotIn('J2.5 supply reference', text)
        self.assertFalse(report['complete_register_capture'])

    def test_wrong_family_stops_before_family_specific_reads(self):
        reader, raw = self.stage(FakeReader({'DBGMCU_IDCODE': 0x12300483}))
        self.assertEqual(reader.seen, ['CPUID', 'DBGMCU_IDCODE'])
        self.assertEqual(raw['state'], 'IDENTITY_UNCONFIRMED')
        self.assertEqual(r.analyze(self.run, BOARD)['overall'], 'ISSUES_FOUND')

    def test_read_and_cleanup_errors_are_preserved_not_zero(self):
        reader, raw = self.stage(FakeReader({'RCC_RSR': TimeoutError('synthetic bus timeout')},
                                           close_error=OSError('synthetic close failure')))
        self.assertTrue(reader.closed)
        self.assertEqual(raw['state'], 'CLEANUP_FAILED')
        rows = [v for v in raw['reads'] if v['name'] == 'RCC_RSR']
        self.assertTrue(all(x['value'] is None and 'TimeoutError' in x['error'] for x in rows))
        report = r.analyze(self.run, BOARD)
        self.assertFalse(report['complete_register_capture'])
        self.assertIn('close failure', report['capture_error'])

    def test_missing_supervisor_receipt_never_counts_complete(self):
        self.stage(supervised=False)
        report = r.analyze(self.run, BOARD)
        self.assertEqual(report['capture_state'], 'CAPTURED')
        self.assertFalse(report['complete_register_capture'])
        self.assertEqual(report['checks'][0]['status'], 'INCONCLUSIVE')

    def test_snapshot_byte_change_after_receipt_is_rejected(self):
        self.stage()
        with (self.run / 'snapshot.json').open('a') as stream:
            stream.write('\n')
        with self.assertRaisesRegex(ValueError, 'changed after'):
            r.analyze(self.run, BOARD)

    def test_prohibited_memory_writes_or_non_register_addresses_rejected(self):
        self.stage()
        original = r.document(self.run / 'snapshot.json')
        for operation in [['AP_CONFIG_WRITE', 12, 0], ['AP_CONFIG_WRITE', 4, 0x24000000],
                          ['AP_CONFIG_WRITE', 4, 0x58020014]]:
            with self.subTest(operation=operation):
                bad = copy.deepcopy(original); bad['debug_address_operations'] = [operation]
                self.overwrite('snapshot.json', bad)
                with self.assertRaisesRegex(ValueError, 'outside register allowlist'):
                    r.analyze(self.run, BOARD)

    def test_false_complete_and_wrong_order_do_not_pass(self):
        self.stage()
        original = r.document(self.run / 'snapshot.json')
        for mutate in (lambda d: d['reads'].pop(), lambda d: d['reads'].reverse(),
                       lambda d: d.pop('finished_at'), lambda d: d.update(schema=True),
                       lambda d: d.update(error='SYNTHETIC terminal error'),
                       lambda d: d.update(board_sha256='0' * 64)):
            bad = copy.deepcopy(original); mutate(bad); self.overwrite('snapshot.json', bad)
            with self.assertRaises(ValueError):
                r.analyze(self.run, BOARD)

    def test_driver_identity_mismatch_rejected_even_with_live_label(self):
        _, raw = self.stage()
        req = r.document(self.run / 'request.json'); req['origin'] = 'SWD_CAPTURE'
        raw['origin'] = 'SWD_CAPTURE'
        raw['driver'] = dict(probe_id='OTHER-PROBE', pyocd_version='0.45.1', target_init_executed=False)
        with self.assertRaisesRegex(ValueError, 'probe/driver'):
            r.validate_raw(raw, req)
        raw['driver'] = None
        with self.assertRaises(ValueError):
            r.validate_raw(raw, req)

    def test_timeout_escalation_preserves_partial_snapshot(self):
        r.prepare(BOARD, 'SYNTHETIC-REQUEST-ONLY', 'FAKE-PROBE', self.run, bench_isolated=True)
        raw = b'{"synthetic_partial_marker":true}\n'
        (self.run / 'snapshot.json').write_bytes(raw)
        proc = mock.Mock()
        proc.pid = 12345
        proc.wait.side_effect = [subprocess.TimeoutExpired('fake', 25),
                                 subprocess.TimeoutExpired('fake', 3), -9]
        start = mock.Mock(return_value=proc)
        result = r.supervise(self.run, BOARD, popen=start)
        self.assertTrue(result['timed_out'])
        proc.terminate.assert_called_once(); proc.kill.assert_called_once()
        self.assertEqual((self.run / 'snapshot.json').read_bytes(), raw)
        command = start.call_args.args[0]
        self.assertEqual(command[:4], [sys.executable, '-I', '-B', '-c'])
        self.assertEqual(command[4], r.WORKER_BOOTSTRAP)

    def test_worker_start_failure_has_a_missing_data_report(self):
        r.prepare(BOARD, 'SYNTHETIC-REQUEST-ONLY', 'FAKE-PROBE', self.run, bench_isolated=True)
        result = r.supervise(self.run, BOARD, popen=mock.Mock(side_effect=OSError('synthetic spawn failure')))
        self.assertIn('spawn failure', result['error'])
        report = r.analyze(self.run, BOARD)
        self.assertFalse(report['raw_available'])
        self.assertFalse(report['complete_register_capture'])
        self.assertEqual(report['capture_state'], 'NO_SNAPSHOT')

    def test_existing_output_and_prior_evidence_are_never_overwritten(self):
        self.stage()
        before = {p.name:p.read_bytes() for p in self.run.iterdir()}
        with self.assertRaises(FileExistsError):
            r.prepare(BOARD, 'A', 'P', self.run, bench_isolated=True)
        out = self.root / 'analysis'; r.write_report(self.run, BOARD, out)
        text = (out / 'report.md').read_bytes()
        with self.assertRaises(FileExistsError):
            r.write_report(self.run, BOARD, out)
        self.assertEqual((out / 'report.md').read_bytes(), text)
        self.assertEqual({p.name:p.read_bytes() for p in self.run.iterdir()}, before)

    def test_cli_worker_will_not_relabel_synthetic_request_as_live(self):
        self.stage()
        with mock.patch.object(r, 'worker') as worker, contextlib.redirect_stderr(io.StringIO()):
            code = r.main(['_worker', '--board', str(BOARD), '--run', str(self.run)])
        self.assertEqual(code, 3)
        worker.assert_not_called()

    def test_wrong_run_and_false_receipt_types_rejected(self):
        self.stage()
        original = r.document(self.run / 'execution.json')
        for key, value in [('run_id', 'OTHER-RUN'), ('worker_exit_code', False), ('request_sha256', '0' * 64)]:
            bad = copy.deepcopy(original); bad[key] = value
            self.overwrite('execution.json', bad)
            with self.assertRaises(ValueError):
                r.analyze(self.run, BOARD)

    def manual_record(self, raw):
        record = r.bench_template(self.run, BOARD)
        record['power_context'].update(attached_source='PACK', selected_source='PACK',
            configuration_id='SYNTHETIC-STEADY', source_note='Invented source for software test only',
            source_reference_v=[6, 8.4], battery_path_expected=True,
            ground_reference_verified=True, backfeed_excluded=True)
        for key, voltage in [('C9.1', 3.3), ('R164.2', 0.0)]:
            profile = offline.Profile(synthetic=True)
            point = profile.point(key)
            record['measurements'].append(dict(type='measurement', status='AVAILABLE',
                origin='MANUAL_OFFLINE', epoch=record['epoch'], point=point, ground=profile.ground(point),
                unit='V', interval=[voltage - .01, voltage + .01], uncertainty_abs_v=.01,
                assembly_id=record['assembly_id'], session_id=record['session_id'],
                configuration_id='SYNTHETIC-STEADY', measured_at=raw['captured_at'],
                instrument='SYNTHETIC METER, NOT PHYSICAL EVIDENCE', uncertainty_basis='Invented +/- .01 V test bound'))
        return record

    def test_blank_measurement_template_links_capture_but_invents_no_data(self):
        _, raw = self.stage()
        template = r.bench_template(self.run, BOARD)
        self.assertEqual(template['session_id'], raw['capture_id'])
        self.assertEqual(template['epoch'], r.request(self.run, BOARD)['run_id'])
        self.assertEqual(template['measurements'], [])
        self.assertEqual(template['module_supplies'], {})
        self.assertFalse(template['power_context']['ground_reference_verified'])

    def test_saved_register_and_meter_evidence_form_one_bound_report(self):
        _, raw = self.stage()
        record = self.manual_record(raw)
        path = self.root / 'synthetic-manual.json'; r.write_new(path, record)
        report = r.write_report(self.run, BOARD, self.root / 'combined', path)
        self.assertTrue(report['synthetic'])
        self.assertEqual(report['overall'], 'ISSUES_FOUND')
        external = report['external_voltage_report']
        self.assertEqual(external['result']['candidate_causes'], ['sensor_supply_branch'])
        self.assertEqual(external['session_id'], raw['capture_id'])
        self.assertEqual(report['external_record_sha256'], r.sha_bytes(path.read_bytes()))
        self.assertIn('R164.2', r.markdown(report))
        self.assertFalse(report['hardware_qualified'])

    def test_voltage_session_and_epoch_must_match_actual_capture(self):
        _, raw = self.stage()
        original = self.manual_record(raw)
        for key in ('assembly_id', 'session_id', 'epoch'):
            record = copy.deepcopy(original)
            record[key] = 'DIFFERENT'
            # Keep the manual file internally coherent; cross-capture pairing must still reject it.
            for row in record['measurements']:
                row[key] = 'DIFFERENT'
            path = self.root / (key + '.json'); r.write_new(path, record)
            with self.assertRaisesRegex(ValueError, 'another capture/session'):
                r.analyze(self.run, BOARD, path)

    def test_voltage_window_must_cover_capture_not_only_meter_time(self):
        _, raw = self.stage()
        record = self.manual_record(raw)
        record['observed_window'] = {'start':'2020-01-01T12:00:00Z', 'end':'2020-01-01T12:01:00Z'}
        for row in record['measurements']:
            row['measured_at'] = '2020-01-01T12:00:30Z'
        path = self.root / 'old.json'; r.write_new(path, record)
        with self.assertRaisesRegex(ValueError, 'outside the declared'):
            r.analyze(self.run, BOARD, path)

    def test_source_drift_is_rejected_before_reader_construction(self):
        r.prepare(BOARD, 'SYNTHETIC', 'FAKE', self.run, bench_isolated=True, origin='SYNTHETIC_FIXTURE')
        changed = r.source_hashes(); changed['transport.py'] = '0' * 64
        factory = mock.Mock()
        with mock.patch.object(r, 'source_hashes', return_value=changed):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                r.worker(self.run, BOARD, reader_factory=factory)
        factory.assert_not_called()
        self.assertFalse((self.run / 'snapshot.json').exists())

    def test_old_acquisition_source_record_survives_a_later_analysis_version(self):
        self.stage()
        current = r.source_hashes(); current['engine.py'] = '1' * 64
        with mock.patch.object(r, 'source_hashes', return_value=current):
            report = r.analyze(self.run, BOARD)
        self.assertNotEqual(report['acquisition_source_hashes'], report['analysis_source_hashes'])
        self.assertTrue(report['complete_register_capture'])
        self.assertFalse(report['hardware_qualified'])

    def test_offline_cli_reports_do_not_require_a_probe_or_driver_package(self):
        _, raw = self.stage()
        record = self.manual_record(raw)
        path = self.root / 'manual.json'; r.write_new(path, record)
        proc = subprocess.run([sys.executable, '-B', '-m', 'diagnostics.r10_swd', 'report',
            '--run', str(self.run), '--board', str(BOARD), '--out', str(self.root / 'cli-report'),
            '--manual', str(path)], cwd=r.ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        report = json.loads((self.root / 'cli-report/report.json').read_text())
        self.assertEqual(report['external_voltage_report']['session_id'], raw['capture_id'])
        self.assertFalse(report['firmware_verified'])
        proc = subprocess.run([sys.executable, '-B', '-m', 'diagnostics.r10_swd', 'bench-template',
            '--run', str(self.run), '--board', str(BOARD), '--out', str(self.root / 'cli-template.json')],
            cwd=r.ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads((self.root / 'cli-template.json').read_text())['measurements'], [])

    def test_unreaped_worker_is_explicitly_incomplete_not_a_hang_or_success(self):
        r.prepare(BOARD, 'SYNTHETIC-REQUEST-ONLY', 'FAKE-PROBE', self.run, bench_isolated=True)
        proc = mock.Mock(); proc.pid = 12345
        proc.wait.side_effect = subprocess.TimeoutExpired('fake', 1)
        result = r.supervise(self.run, BOARD, popen=mock.Mock(return_value=proc))
        self.assertIsNone(result['worker_exit_code'])
        self.assertEqual(result['worker_pid'], 12345)
        self.assertIn('did not exit', result['error'])
        report = r.analyze(self.run, BOARD)
        self.assertFalse(report['complete_register_capture'])

    def test_isolated_worker_bootstrap_ignores_pythonpath_shadow_packages(self):
        poison = self.root / 'poison'; poison.mkdir()
        (poison / 'json.py').write_text('raise RuntimeError("POISON_MODULE")\n')
        env = dict(os.environ, PYTHONPATH=str(poison))
        proc = subprocess.run([sys.executable, '-I', '-B', '-c', r.WORKER_BOOTSTRAP,
            str(r.ROOT), 'wiring', '--board', str(BOARD)], cwd=self.root,
            env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['connector']['1']['role'], '3V3')

    def test_receipt_nonobjects_are_controlled_cli_errors(self):
        self.stage()
        originals = {name:(self.run/name).read_bytes() for name in ('execution.json', 'supervision.json')}
        for name in originals:
            for value in ([], 'text', 7, True, None):
                with self.subTest(receipt=name, value=value):
                    self.overwrite(name, value)
                    out = self.root / 'should-not-be-created'
                    err = io.StringIO()
                    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                        code = r.main(['report', '--run', str(self.run), '--board', str(BOARD), '--out', str(out)])
                    self.assertEqual(code, 3)
                    self.assertIn('receipt must be an object', err.getvalue())
                    self.assertNotIn('Traceback', err.getvalue())
                    self.assertFalse(out.exists())
                    (self.run/name).write_bytes(originals[name])

    def test_live_schema_cannot_drop_synthetic_markers_or_required_provenance(self):
        # Invented values only: exercise the live producer schema in memory,
        # never serialize or present this fixture as a physical capture.
        _, raw = self.stage()
        req = r.request(self.run, BOARD); req['origin'] = raw['origin'] = 'SWD_CAPTURE'
        driver = dict(probe_id='FAKE-PROBE', pyocd_version='0.45.1', target_init_executed=False,
            probe_description='SYNTHETIC PRODUCER-SHAPED TEST', dpidr='0x6ba02477', frequency_hz=100000,
            driver_sources={'dap.py':'0'*64, 'minimal_mem_ap.py':'1'*64, 'fake_probe.py':'2'*64})
        raw['driver'] = driver
        raw['debug_address_operations'] = [['AP_CONFIG_WRITE', 0, 0x03000012]] + [
            ['AP_CONFIG_WRITE', 4, address] for address,bits in REGISTERS.values()]
        r.validate_raw(raw, req)
        for mutate in (lambda d:d['driver'].update(kind='SYNTHETIC_FIXTURE', not_a_hardware_driver=True),
                       lambda d:d['driver'].pop('driver_sources'), lambda d:d.pop('debug_address_operations'),
                       lambda d:d['driver'].update(frequency_hz=True)):
            bad = copy.deepcopy(raw); mutate(bad)
            with self.assertRaises(ValueError):
                r.validate_raw(bad, req)

    def test_partial_capture_without_end_cannot_bind_meter_window(self):
        _, raw = self.stage()
        record = self.manual_record(raw)
        path = self.root / 'manual.json'; r.write_new(path, record)
        raw['state'] = 'STARTED'; raw.pop('finished_at')
        self.overwrite('snapshot.json', raw)
        (self.run/'execution.json').unlink()
        supervision = r.document(self.run/'supervision.json')
        supervision.update(timed_out=True, worker_exit_code=-15)
        self.overwrite('supervision.json', supervision)
        self.assertFalse(r.analyze(self.run, BOARD)['complete_register_capture'])
        with self.assertRaisesRegex(ValueError, 'Known coherent capture end'):
            r.analyze(self.run, BOARD, path)
        with self.assertRaisesRegex(ValueError, 'Known capture end'):
            r.bench_template(self.run, BOARD)

    def test_receipt_clock_discontinuity_is_incomplete_but_keeps_raw_data(self):
        self.stage()
        before = (self.run/'snapshot.json').read_bytes()
        original = r.document(self.run/'execution.json')
        for when in ('2000-01-01T00:00:00Z', '2099-01-01T00:00:00Z'):
            bad = copy.deepcopy(original); bad['completed_at'] = when
            self.overwrite('execution.json', bad)
            report = r.analyze(self.run, BOARD)
            self.assertFalse(report['temporal_coherence'])
            self.assertFalse(report['complete_register_capture'])
            self.assertEqual(report['checks'][0]['id'], 'CAPTURE_TIMELINE')
            self.assertEqual((self.run/'snapshot.json').read_bytes(), before)

    def test_literal_null_snapshot_is_not_silently_missing_data(self):
        self.stage()
        (self.run/'snapshot.json').write_text('null')
        with self.assertRaisesRegex(ValueError, 'Expected object'):
            r.analyze(self.run, BOARD)


if __name__ == '__main__':
    unittest.main()
