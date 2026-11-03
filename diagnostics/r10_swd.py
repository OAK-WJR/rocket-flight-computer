"""R10-only bounded SWD register capture and offline reports.

No firmware is installed, halted, reset or commanded. Uses the existing pinned
DP/AP-only transport; attaching a debugger still affects debug/system power.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

from . import engine
from .registers import CPUID_MASK, EXPECTED_CPUID, EXPECTED_FAMILY, PY_OCD_VERSION, REGISTERS
from .r10_offline import (Profile, BOARD_SHA, PROFILE, canonical, document, fields,
                          identifier, loads, regular_bytes, require, timestamp,
                          analyze_manual, render_zh, template)
from .transport import PyOCDReader, capture, utc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BINDING_SHA = '076c815e7a8d66bf242fc5420754af78a81b4d0c6bcd58ce08228379d31a8747'
REQUEST_KEYS = ('schema', 'profile', 'board_sha256', 'binding_sha256', 'run_id',
                'assembly_id', 'probe_id', 'origin', 'bench_isolated', 'created_at', 'tool_sources')
SOURCE_NAMES = ('r10_swd.py', 'r10_swd_binding.json', 'r10_profile.json', 'r10_offline.py',
                'transport.py', 'registers.py', 'engine.py')
WORKER_BOOTSTRAP = ('import sys; sys.path.insert(0, sys.argv.pop(1)); '
                    'from diagnostics.r10_swd import main; raise SystemExit(main())')


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def source_hashes():
    return {name:sha_bytes(regular_bytes(HERE / name, 2_000_000)) for name in SOURCE_NAMES}


def write_new(path, value):
    """Evidence/output files are exclusive creations; never replace an old run."""
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(data)


def binding(board):
    Profile(board=board)
    value = document(HERE / 'r10_swd_binding.json')
    require(sha_bytes(canonical(value)) == BINDING_SHA, 'Wrong R10 SWD binding')
    require(value['board_sha256'] == BOARD_SHA and value['profile'] == PROFILE, 'Wrong R10 board revision')
    return value


def request(run, board):
    binding(board)
    value = document(Path(run) / 'request.json')
    fields(value, REQUEST_KEYS)
    require(value['schema'] == 'r10-swd-request/v1' and value['profile'] == PROFILE and
            value['board_sha256'] == BOARD_SHA and value['binding_sha256'] == BINDING_SHA,
            'Wrong request revision/binding')
    for key in ('assembly_id', 'probe_id', 'run_id'):
        identifier(value[key])
    timestamp(value['created_at'])
    require(value['origin'] in ('SWD_CAPTURE', 'SYNTHETIC_FIXTURE'), 'Wrong capture origin')
    require(value['bench_isolated'] is True, 'Only isolated bench capture is supported')
    fields(value['tool_sources'], SOURCE_NAMES)
    require(all(isinstance(v, str) and len(v) == 64 and set(v) <= set('0123456789abcdef')
                for v in value['tool_sources'].values()), 'Invalid acquisition source hashes')
    return value


def prepare(board, assembly, probe, out, *, bench_isolated, origin='SWD_CAPTURE'):
    binding(board)  # Fail before creating evidence or opening a probe.
    identifier(assembly); identifier(probe)
    require(bench_isolated is True, 'Declare isolated bench context before capture')
    require(origin in ('SWD_CAPTURE', 'SYNTHETIC_FIXTURE'), 'Wrong capture origin')
    out = Path(out)
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    value = dict(schema='r10-swd-request/v1', profile=PROFILE, board_sha256=BOARD_SHA,
        binding_sha256=BINDING_SHA, run_id=str(uuid.uuid4()), assembly_id=assembly,
        probe_id=probe, origin=origin, bench_isolated=True, created_at=utc(), tool_sources=source_hashes())
    write_new(out / 'request.json', value)
    return value


def worker(run, board, reader_factory=PyOCDReader, pause=None):
    """Invoked in its own bounded process; factory injection is for software tests."""
    run = Path(run)
    req = request(run, board)
    require(req['tool_sources'] == source_hashes(), 'Acquisition source changed before worker start')
    kwargs = {'origin': req['origin']}
    if pause is not None:
        kwargs['pause'] = pause
    snapshot = capture(reader_factory(req['probe_id']), {'board_sha256': BOARD_SHA},
                       req['assembly_id'], run / 'snapshot.json', **kwargs)
    code = 0 if snapshot['state'] == 'CAPTURED' else 3
    write_new(run / 'execution.json', dict(schema='r10-swd-execution/v1',
        run_id=req['run_id'], request_sha256=sha_bytes(canonical(req)),
        snapshot_sha256=sha_bytes(regular_bytes(run / 'snapshot.json', 2_000_000)),
        worker_exit_code=code, completed_at=utc()))
    return code


def supervise(run, board, *, timeout_s=25, grace_s=3, popen=subprocess.Popen):
    run = Path(run)
    req = request(run, board)
    require(req['origin'] == 'SWD_CAPTURE', 'Live CLI worker requires a live request')
    command = [sys.executable, '-I', '-B', '-c', WORKER_BOOTSTRAP, str(ROOT), '_worker',
               '--run', str(run.resolve()), '--board', str(Path(board).resolve())]
    timed_out = False
    error = None
    pid = None
    with (run / 'driver.log').open('x', encoding='utf-8') as log:
        try:
            proc = popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        except OSError as exc:
            code, error = 3, type(exc).__name__ + ': ' + str(exc)
            log.write(error + '\n')
        else:
            pid = proc.pid
            try:
                code = proc.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.terminate()
                try:
                    code = proc.wait(timeout=grace_s)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    try:
                        code = proc.wait(timeout=grace_s)
                    except subprocess.TimeoutExpired:
                        code = None
                        error = 'Worker did not exit after kill; inspect worker_pid before any further capture.'
    # Preserve the worker's last raw snapshot exactly, even after a timeout.
    value = dict(schema='r10-swd-supervision/v1', run_id=req['run_id'],
        request_sha256=sha_bytes(canonical(req)), timed_out=timed_out,
        worker_exit_code=code, worker_pid=pid, error=error, completed_at=utc())
    write_new(run / 'supervision.json', value)
    return value


def validate_raw(raw, req):
    fields(raw, ('schema', 'origin', 'capture_id', 'captured_at', 'assembly_id', 'board_sha256',
                 'state', 'driver', 'error', 'reads'), ('finished_at', 'debug_address_operations'))
    require(type(raw['schema']) is int and raw['schema'] == 1, 'Invalid snapshot schema')
    identifier(raw['capture_id']); timestamp(raw['captured_at'])
    if 'finished_at' in raw:
        require(timestamp(raw['captured_at']) <= timestamp(raw['finished_at']), 'Invalid capture time order')
    require(raw['error'] is None or isinstance(raw['error'], str), 'Invalid capture error')
    require(isinstance(raw['reads'], list) and len(raw['reads']) <= len(REGISTERS) + 3, 'Invalid read inventory')
    expected_order = [(0, name) for name in REGISTERS] + [(1, name) for name in ('RCC_RSR', 'RCC_CR', 'RCC_CFGR')]
    for index, row in enumerate(raw['reads']):
        fields(row, ('name', 'sample', 'address', 'bits', 'value', 'error', 'elapsed_ms'))
        require((row['sample'], row['name']) == expected_order[index], 'Read sequence differs from allowlist')
        require(row['error'] is None or isinstance(row['error'], str), 'Invalid register error')
    require(raw.get('origin') == req['origin'] and raw.get('assembly_id') == req['assembly_id'],
            'Snapshot origin/assembly does not match capture request')
    try:
        values = engine.validate_snapshot(raw, {'board_sha256': BOARD_SHA})
    except OverflowError as exc:
        raise ValueError('Unsupported numeric value in snapshot') from exc
    c, d = values.get((0, 'CPUID')), values.get((0, 'DBGMCU_IDCODE'))
    identity = (c is not None and d is not None and c & CPUID_MASK == EXPECTED_CPUID
                and d & 0xFFF == EXPECTED_FAMILY)
    if not identity:
        require(set(values) <= {(0, 'CPUID'), (0, 'DBGMCU_IDCODE')},
                'Family-specific reads without confirmed identity')
    if raw['state'] == 'CAPTURED':
        require('finished_at' in raw, 'Completed capture lacks a finish timestamp')
        require(raw['error'] is None, 'Completed capture carries an error')
        expected = {(0, name) for name in REGISTERS} | {(1, name) for name in ('RCC_RSR', 'RCC_CR', 'RCC_CFGR')}
        require(identity and set(values) == expected and all(v is not None for v in values.values()),
                'CAPTURED state contradicts complete allowlisted reads')
    if req['origin'] == 'SWD_CAPTURE' and (raw.get('driver') is not None or raw['reads']):
        driver = raw['driver']
        required_driver = {'probe_id', 'pyocd_version', 'target_init_executed', 'probe_description',
                           'dpidr', 'frequency_hz', 'driver_sources'}
        require(isinstance(driver, dict) and set(driver) == required_driver, 'Unexpected probe/driver schema')
        require(driver.get('probe_id') == req['probe_id'] and
                driver.get('pyocd_version') == PY_OCD_VERSION and driver.get('target_init_executed') is False,
                'Unexpected probe/driver/initialization evidence')
        require(isinstance(driver['probe_description'], str) and type(driver['frequency_hz']) is int and
                driver['frequency_hz'] == 100000, 'Unexpected probe description/frequency')
        dpidr = driver['dpidr']
        require(isinstance(dpidr, str) and len(dpidr) == 10 and dpidr.startswith('0x') and
                set(dpidr[2:]) <= set('0123456789abcdef'), 'Invalid DP identity syntax')
        sources = driver['driver_sources']
        require(isinstance(sources, dict) and len(sources) == 3 and
                {'dap.py', 'minimal_mem_ap.py'} <= sources.keys(), 'Missing live driver source evidence')
        require(all(isinstance(k, str) and k.endswith('.py') and '/' not in k and '\\' not in k and
                    isinstance(v, str) and len(v) == 64 and set(v) <= set('0123456789abcdef')
                    for k,v in sources.items()), 'Invalid driver source hashes')
    operations = raw.get('debug_address_operations', [])
    require(isinstance(operations, list) and len(operations) <= 128, 'Invalid debug address trace')
    for op in operations:
        require(isinstance(op, list) and len(op) == 3 and op[0] == 'AP_CONFIG_WRITE' and
                type(op[1]) is int and type(op[2]) is int and
                ((op[1] == 0 and op[2] == 0x03000012) or
                 (op[1] == 4 and op[2] in {v[0] for v in REGISTERS.values()})),
                'Unexpected target-memory write or address outside register allowlist')
    if req['origin'] == 'SWD_CAPTURE' and raw['state'] == 'CAPTURED':
        require('debug_address_operations' in raw and {v[0] for v in REGISTERS.values()} <=
                {op[2] for op in operations if op[1] == 4}, 'Completed live capture lacks its address trace')
    return values


def analyze(run, board, manual=None):
    run = Path(run)
    info, req = binding(board), request(run, board)
    raw_bytes = regular_bytes(run / 'snapshot.json', 2_000_000) if (run / 'snapshot.json').exists() else None
    raw = loads(raw_bytes.decode('utf-8')) if raw_bytes is not None else None
    raw_sha = sha_bytes(raw_bytes) if raw_bytes is not None else None
    if raw_bytes is not None:
        validate_raw(raw, req)
    def read_receipt(name):
        path = run / name
        if not path.exists():
            return None
        value = document(path)
        require(isinstance(value, dict), 'Capture receipt must be an object: ' + name)
        return value
    execution = read_receipt('execution.json')
    supervision = read_receipt('supervision.json')
    for receipt in (execution, supervision):
        if receipt is not None:
            require(receipt.get('run_id') == req['run_id'] and
                    receipt.get('request_sha256') == sha_bytes(canonical(req)), 'Wrong run receipt')
    if execution is not None:
        fields(execution, ('schema', 'run_id', 'request_sha256', 'snapshot_sha256', 'worker_exit_code', 'completed_at'))
        require(execution['schema'] == 'r10-swd-execution/v1' and execution['snapshot_sha256'] == raw_sha,
                'Snapshot changed after worker completion')
        require(type(execution['worker_exit_code']) is int and execution['worker_exit_code'] in (0, 3), 'Bad worker exit')
        timestamp(execution['completed_at'])
    if supervision is not None:
        fields(supervision, ('schema', 'run_id', 'request_sha256', 'timed_out', 'worker_exit_code', 'error', 'completed_at'),
               ('worker_pid',))
        require(supervision['schema'] == 'r10-swd-supervision/v1' and type(supervision['timed_out']) is bool and
                (type(supervision['worker_exit_code']) is int or
                 (supervision['worker_exit_code'] is None and supervision['timed_out'] and supervision['error'])) and
                (supervision['error'] is None or isinstance(supervision['error'], str)), 'Bad supervision receipt')
        if supervision.get('worker_pid') is not None:
            require(type(supervision['worker_pid']) is int and supervision['worker_pid'] > 0, 'Invalid worker PID')
        timestamp(supervision['completed_at'])
    timeline = [timestamp(req['created_at'])]
    if raw is not None:
        timeline.append(timestamp(raw['captured_at']))
        if 'finished_at' in raw:
            timeline.append(timestamp(raw['finished_at']))
    for receipt in (execution, supervision):
        if receipt is not None:
            timeline.append(timestamp(receipt['completed_at']))
    temporal_coherence = all(a <= b for a,b in zip(timeline, timeline[1:])) and timeline[-1] <= timestamp(utc())
    complete = (raw is not None and raw['state'] == 'CAPTURED' and execution is not None and
                execution['worker_exit_code'] == 0 and supervision is not None and
                supervision['worker_exit_code'] == 0 and not supervision['timed_out'] and supervision['error'] is None
                and temporal_coherence)
    if raw is None:
        checks = [dict(id='RAW_CAPTURE_MISSING', status='INCONCLUSIVE',
            finding='Worker produced no register snapshot. No readings are invented.', next_step='Inspect driver.log and J2 wiring.')]
        overall = 'INCOMPLETE'
    else:
        # Reuse reviewed MCU decoding; never use R1 bench probes or its connector wording.
        decoded = engine.analyze(raw, {'board_sha256': BOARD_SHA, 'gnss_dnp': False})
        checks, overall = decoded['checks'], decoded['overall']
        for row in checks:
            if row['id'] == 'DBG_LINK':
                row['next_step'] = 'R10 J2.1=3V3 reference, J2.5=GND, J2.2=SWDIO, J2.4=SWCLK, J2.3=NRST; J2.6 is NC. No halt/reset fallback.'
            if row['id'] == 'HSE_STATE':
                row['next_step'] = 'An inactive HSE is not a failed crystal. Check software state and oscillator measurements separately.'
            if row['id'] == 'GNSS':
                row['finding'] = 'External GPS/radio/AUX ports and their firmware/communications are not tested by SWD register reads.'
    if not complete:
        checks.insert(0, dict(id='SUPERVISED_CAPTURE_COMPLETENESS', status='INCONCLUSIVE',
            finding='Capture lacks a complete successful worker and supervisor record.',
            next_step='Retain partial observations; inspect driver.log and execution/supervision receipts.'))
    if not temporal_coherence:
        checks.insert(0, dict(id='CAPTURE_TIMELINE', status='INCONCLUSIVE',
            finding='Capture/request/completion times are inconsistent or in the future.',
            next_step='Inspect host clock changes and record provenance; no power or chip fault is inferred from this.'))
    external = None
    external_sha = None
    if manual is not None:
        require(raw is not None, 'A raw capture is needed to bind external measurements')
        require('finished_at' in raw and temporal_coherence,
                'Known coherent capture end required to pair external measurements')
        record_bytes = regular_bytes(manual, 2_000_000)
        record = loads(record_bytes.decode('utf-8'))
        external = analyze_manual(record, board=board)
        require(record['assembly_id'] == req['assembly_id'] and record['session_id'] == raw['capture_id'] and
                record['epoch'] == req['run_id'], 'External measurements belong to another capture/session')
        start, end = (timestamp(record['observed_window'][name]) for name in ('start', 'end'))
        require(start <= timestamp(raw['captured_at']) <= end and
                ('finished_at' not in raw or start <= timestamp(raw['finished_at']) <= end),
                'Capture falls outside the declared steady measurement window')
        external_sha = sha_bytes(record_bytes)
        if external['result']['candidate_causes']:
            overall = 'ISSUES_FOUND'
    return dict(schema='r10-swd-report/v1', profile=PROFILE, board_sha256=BOARD_SHA,
        assembly_id=req['assembly_id'], run_id=req['run_id'], origin=req['origin'],
        synthetic=req['origin'] == 'SYNTHETIC_FIXTURE',
        overall=overall, complete_register_capture=complete,
        raw_available=raw is not None, raw_snapshot_sha256=raw_sha,
        capture_state=raw['state'] if raw is not None else 'NO_SNAPSHOT',
        capture_error=raw.get('error') if raw is not None else None,
        temporal_coherence=temporal_coherence, driver=raw.get('driver') if raw is not None else None,
        connector=info['connector'], coordinate_frame=info['coordinate_frame'],
        checks=checks, execution=execution, supervision=supervision,
        external_voltage_report=external, external_record_sha256=external_sha,
        acquisition_source_hashes=req['tool_sources'], analysis_source_hashes=source_hashes(),
        hardware_qualified=False, firmware_verified=False, fabrication_release=False,
        physical_board_identity_verified=False,
        limitations=[
            'Design-file identity and an operator assembly tag do not authenticate the physical PCB.',
            'No firmware image is installed or verified; a ready/status bit is not a functional hardware test.',
            'SWD writes DP/AP configuration and requests debug/system power. This is not zero-disturbance observation.',
            'No ADC, sensor transaction, flash read/program/erase, GPIO change or actuator test is performed.'])


def bench_template(run, board):
    """Fill provenance only. Actual voltages, source state and meter data stay empty."""
    run = Path(run)
    req = request(run, board)
    raw = document(run / 'snapshot.json')
    validate_raw(raw, req)
    require('finished_at' in raw, 'Known capture end required for paired measurement template')
    record = template(board)
    record.update(assembly_id=req['assembly_id'], session_id=raw['capture_id'], epoch=req['run_id'],
                  observed_window={'start': raw['captured_at'], 'end': utc()})
    return record


def markdown(report):
    lines = ['# R10 register diagnostic report', '',
        'Origin: ' + report['origin'] + '; overall: ' + report['overall'],
        'Profile: ' + PROFILE + '; board SHA-256: ' + BOARD_SHA,
        'Assembly: ' + report['assembly_id'] + '; run: ' + report['run_id'],
        'Complete register capture: ' + str(report['complete_register_capture']),
        'Hardware qualified: false; firmware verified: false; fabrication release: false.', '',
        '## R10 J2 — PCB top projection, not a mirrored bottom view', '']
    for n, p in sorted(report['connector'].items()):
        lines.append('- J2.%s: %s, %s, XY=(%s, %s) mm' % (n, p['role'], p['side'], *p['xy_mm']))
    lines += ['', '## Findings', '']
    for check in report['checks']:
        lines += ['- [%s] %s: %s' % (check['status'], check['id'], check['finding'])]
        if check.get('next_step'):
            lines.append('  Next: ' + check['next_step'])
    if report['external_voltage_report'] is not None:
        lines += ['', '## Saved external instrument evidence', '', render_zh(report['external_voltage_report'])]
    lines += ['', '## Limits', ''] + ['- ' + x for x in report['limitations']]
    return '\n'.join(lines) + '\n'


def write_report(run, board, out, manual=None):
    result = analyze(run, board, manual)
    out = Path(out); out.mkdir(mode=0o700, parents=True, exist_ok=False)
    write_new(out / 'report.json', result)
    with (out / 'report.md').open('x', encoding='utf-8') as stream:
        stream.write(markdown(result))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    for name in ('capture', '_worker', 'report', 'wiring', 'bench-template'):
        sub = subs.add_parser(name)
        sub.add_argument('--board', type=Path, required=True)
        if name in ('_worker', 'report', 'bench-template'):
            sub.add_argument('--run', type=Path, required=True)
        if name in ('capture', 'report', 'bench-template'):
            sub.add_argument('--out', type=Path, required=True)
        if name == 'report':
            sub.add_argument('--manual', type=Path)
        if name == 'capture':
            sub.add_argument('--probe-id', required=True)
            sub.add_argument('--assembly-id', required=True)
            sub.add_argument('--bench-isolated', action='store_true', required=True)
    try:
        a = parser.parse_args(argv)
        binding(a.board)
        if a.command == 'wiring':
            print(json.dumps(binding(a.board), indent=2))
            return 0
        if a.command == '_worker':
            require(request(a.run, a.board)['origin'] == 'SWD_CAPTURE', 'CLI requires live request')
            return worker(a.run, a.board)
        if a.command == 'bench-template':
            write_new(a.out, bench_template(a.run, a.board))
            print(a.out)
            return 0
        if a.command == 'report':
            report = write_report(a.run, a.board, a.out, a.manual)
        else:
            prepare(a.board, a.assembly_id, a.probe_id, a.out, bench_isolated=a.bench_isolated)
            supervise(a.out, a.board)
            report = write_report(a.out, a.board, a.out / 'analysis')
        print(report['overall'] + ' — ' + str(a.out))
        return 2 if report['overall'] == 'ISSUES_FOUND' else 0 if report['complete_register_capture'] else 3
    except (ValueError, OSError, RuntimeError, TypeError, KeyError, OverflowError, subprocess.SubprocessError) as exc:
        print('R10 capture rejected: ' + str(exc), file=sys.stderr)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
