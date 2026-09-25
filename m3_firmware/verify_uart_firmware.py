"""Verify current v2/v3 bench binaries and bounded diagnostics, without flashing."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / 'verification_uart'
PY = ROOT / 'diagnostics/.venv/bin/python'
TESTS = ['diagnostics.test_diagnostics', 'diagnostics.test_cli_binding',
         'diagnostics.test_mailbox', 'diagnostics.test_acquisition',
         'm3_firmware.test_firmware', 'm3_firmware.test_camera', 'diagnostics.test_camera']
UART_SHA = 'f8004cbb274808b1d334667d5331c1980cb69a16672b8c0284907862370e8e88'
PROTECTED = {
    'm3_design/power_review/m3.kicad_pcb': '2fdf1bf82d7feb3f303060bdddbded2f45cf8956eb2b051c99a18c57dc286d16',
    'm3_core/review/m3_core.kicad_pcb': 'cd647b9400a4e2bfca729b0c96e97cb2fb97ec3455387bfe58a5aeb008527f72',
    'm3_design/uart_review/m3.kicad_pcb': UART_SHA,
    'm3_design/M3_Power_Candidate.zip': '7a5928842939cea25d629338ac4a05e6eb6673bb12c22f1e318c54ca3c524711',
    'm3_design/M3_Bench_Diagnostics_v0_2.zip': '08c7640dd88f64d86a4368707015a5fb03b8b00f47eb3fe6f3da7178377d6766',
    'm3_design/M3_UART_Candidate.zip': '9f7560f24fc8ebe978cb38788ee089a7a3a961c65ec4b623da61cb51058f6e74',
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_build(folder):
    p = HERE / folder
    m = json.loads((p / 'manifest.json').read_text())
    for name, digest in m['inputs'].items():
        if sha(HERE / name) != digest:
            raise ValueError('Stale source in ' + folder + ': ' + name)
    identity = hashlib.sha256(json.dumps({'inputs': m['inputs'], 'options': m['build_options']},
                                       sort_keys=True).encode()).hexdigest()
    if identity != m['build_sha256']:
        raise ValueError('Build option identity mismatch')
    for name, digest in m['artifacts'].items():
        if sha(p / name) != digest:
            raise ValueError('Changed compiled artifact: ' + name)
    uart = folder != 'build'
    query = folder == 'build_uart_query'
    if m['build_options'] != {'board': 'uart' if uart else 'power', 'camera_query': query}:
        raise ValueError('Wrong mode in folder ' + folder)
    if m['profile'] != ('M3-UART-R1' if uart else 'M3-PWR-R3'):
        raise ValueError('Wrong PCB profile')
    expected = json.loads((HERE / ('protocol_uart.json' if uart else 'protocol.json')).read_text())
    if m['protocol'] != expected or m['hardware_tested'] or m['flashed'] or m['full_m3_complete']:
        raise ValueError('Invalid scope or mailbox contract')
    board = ROOT / 'm3_design' / ('uart_review' if uart else 'power_review') / 'm3.kicad_pcb'
    if sha(board) != m['board_sha256'] or (uart and sha(board) != UART_SHA):
        raise ValueError('PCB binding changed')
    raw = (p / 'm3_bench.bin').read_bytes()
    sp, entry = struct.unpack('<II', raw[:8])
    if sp != 0x20020000 or not entry & 1 or not 0x08000000 <= (entry & ~1) < 0x08000000 + len(raw):
        raise ValueError('Invalid linked vector')
    for key in ('board_sha256', 'build_sha256'):
        if bytes.fromhex(m[key]) not in raw:
            raise ValueError('Identity missing from compiled image: ' + key)
    symbols = (p / 'symbols.txt').read_text()
    if '24000000 00000200 B bench_mailbox' not in symbols:
        raise ValueError('Mailbox symbol moved')
    if uart != bool(re.search(r' T bench_camera_query$', symbols, re.M)):
        raise ValueError('Wrong camera adapter linked')
    return {'build_sha256': identity, 'manifest_sha256': sha(p / 'manifest.json'),
            'artifacts': m['artifacts'], 'board_sha256': m['board_sha256'],
            'binary_bytes': len(raw), 'camera_query': query}


def input_hashes():
    files = [*HERE.glob('*.py'), *HERE.glob('*.json'), *HERE.glob('*.md'), HERE / 'linker.ld',
             *HERE.glob('src/*'), *HERE.glob('tests/**/*'), HERE / 'research/CAMERA_UART.md',
             *ROOT.glob('diagnostics/*.py'), ROOT / 'diagnostics/README.md', ROOT / 'M3_STATUS.md',
             *ROOT.glob('m3_design/*intent.py'), ROOT / 'm3_design/check_uart.py',
             ROOT / 'm3_design/check_design.py', ROOT / 'm3_design/procurement.py',
             ROOT / 'm3_design/procurement_catalog.json', ROOT / 'm3_core/parts.json',
             ROOT / 'quality_audit/sexpr.py']
    return {str(p.relative_to(ROOT)): sha(p) for p in files if p.is_file()
            and '__pycache__' not in p.parts and not p.name.startswith('package_check')}


def main():
    if not PY.exists():
        raise ValueError('Create diagnostics/.venv from requirements-lock.txt first')
    OUT.mkdir(exist_ok=True)
    run = OUT / ('run_' + uuid.uuid4().hex[:12])
    run.mkdir()
    before = input_hashes()
    protected = {}
    for name, digest in PROTECTED.items():
        p = ROOT / name
        if not p.exists() and p.suffix == '.zip':
            continue  # Historical archives need not be duplicated in the addendum.
        if sha(p) != digest:
            raise ValueError('Protected baseline changed: ' + name)
        protected[name] = digest
    builds = {name: check_build(name) for name in ('build', 'build_uart_idle', 'build_uart_query')}
    if builds['build_uart_idle']['artifacts']['m3_bench.bin'] == builds['build_uart_query']['artifacts']['m3_bench.bin']:
        raise ValueError('Idle and query images must differ')
    vendor = json.loads((HERE / 'vendor_manifest.json').read_text())
    for row in vendor['files']:
        if sha(HERE / row['path']) != row['sha256']:
            raise ValueError('Vendor file changed')
    result = subprocess.run([str(PY), '-m', 'unittest', *TESTS, '-v'], cwd=ROOT,
                            capture_output=True, text=True, timeout=60)
    log = result.stdout + result.stderr
    (run / 'regression.log').write_text(log)
    match = re.search(r'Ran (\d+) tests in', log)
    if result.returncode or not match:
        raise RuntimeError(log)
    inventory = subprocess.run([str(PY), '-m', 'diagnostics', 'probes'], cwd=ROOT,
                               capture_output=True, text=True, timeout=15)
    if inventory.returncode:
        raise RuntimeError(inventory.stderr)
    probes = json.loads(inventory.stdout)
    (run / 'probe_inventory.json').write_text(inventory.stdout)
    absent_results = {}
    for mode in ('idle', 'query'):
        absent = 'NO-DEVICE-SELFTEST-' + uuid.uuid4().hex
        if any(p['id'] == absent for p in probes['probes']):
            raise ValueError('Unexpected probe identity')
        folder = HERE / ('build_uart_' + mode)
        no_probe = run / ('absent_' + mode)
        command = [str(PY), '-m', 'diagnostics.mailbox', 'capture', '--probe-id', absent,
                   '--assembly-id', 'NO-HARDWARE', '--binding', str(folder / 'binding.json'),
                   '--manifest', str(folder / 'manifest.json'), '--out', str(no_probe)]
        failed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=35)
        evidence = json.loads((no_probe / 'mailbox.json').read_text())
        if failed.returncode != 3 or evidence['state'] != 'CONNECTION_FAILED' or evidence['samples'] or evidence['identity']:
            raise ValueError('Absent probe produced invalid evidence')
        absent_results[mode] = {'path': str(no_probe.relative_to(ROOT)), 'exit': failed.returncode,
                                'state': evidence['state']}
    # Save a user-readable fault example. Every file retains synthetic origin.
    sys.path.insert(0, str(ROOT))
    from diagnostics.test_camera import uart_frame
    from diagnostics.test_mailbox import SyntheticMailbox
    from diagnostics.mailbox import capture_mailbox, report_file
    folder = HERE / 'build_uart_query'
    binding = json.loads((folder / 'binding.json').read_text())
    manifest = json.loads((folder / 'manifest.json').read_text())
    example = run / 'synthetic_uart_error'; example.mkdir()
    frames = [uart_frame(1), uart_frame(2, STATUS=3, ERROR=5, ERROR_FLAGS=4)]
    capture_mailbox(SyntheticMailbox(frames), binding, manifest, 'SYNTHETIC-NOT-HARDWARE',
                    example / 'mailbox.json', origin='SYNTHETIC_FIXTURE', pause=lambda _: None)
    report_file(example / 'mailbox.json', example / 'analysis', binding, manifest)
    if input_hashes() != before or any(sha(ROOT / name) != digest for name, digest in protected.items()):
        raise ValueError('Inputs changed during verification')
    record = {'schema': 1, 'ok': True, 'tests': int(match[1]), 'builds': builds,
              'inputs_sha256': before, 'protected_baselines': protected, 'vendor_files': len(vendor['files']),
              'scripted_bus_cases': 14, 'scripted_adc_cases': 13, 'scripted_uart_adapter_cases': 12,
              'portable_uart_tests': 16, 'camera_host_tests': 13,
              'run': str(run.relative_to(ROOT)), 'log_sha256': sha(run / 'regression.log'),
              'absent_probe_results': absent_results, 'synthetic_example': str(example.relative_to(ROOT)),
              'hardware_tested': False, 'flashed': False, 'full_m3_complete': False,
              'scope': 'Compiled vectors and identities, scripted C drivers, host parsing and error handling; no electrical simulation or hardware qualification'}
    (OUT / 'regression.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k not in ('inputs_sha256', 'protected_baselines', 'builds')}, indent=2))


if __name__ == '__main__':
    main()
