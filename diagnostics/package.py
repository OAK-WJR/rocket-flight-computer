"""Run regressions and produce a portable diagnostic tool/evidence archive."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from .engine import HERE, digest, load_json
from .transport import atomic_json


def main():
    command = [sys.executable, '-m', 'unittest', 'diagnostics.test_diagnostics', 'diagnostics.test_cli_binding', '-v']
    result = subprocess.run(command, cwd=HERE.parent, capture_output=True, text=True, timeout=60)
    test_dir = HERE/'runs'/datetime.now(timezone.utc).strftime('regression_%Y%m%dT%H%M%S')
    test_dir.mkdir(parents=True, exist_ok=False)
    (test_dir/'stdout.txt').write_text(result.stdout)
    (test_dir/'stderr.txt').write_text(result.stderr)
    evidence = dict(command=command, returncode=result.returncode,
                    source_sha256={p.name:digest(p) for p in HERE.glob('*.py')},
                    board_binding_sha256=digest(HERE/'board_binding.json'),
                    hardware_connection_tested=False)
    atomic_json(test_dir/'result.json', evidence)
    if result.returncode:
        print(result.stdout + result.stderr)
        raise SystemExit(result.returncode)
    smoke = load_json(HERE/'runs/no_probe_final_20260907/snapshot.json')
    if smoke['state'] != 'CONNECTION_FAILED' or smoke['reads']:
        raise ValueError('Expected explicit no-target smoke evidence')
    files = [p for p in HERE.iterdir() if p.suffix in ('.py','.md','.json','.txt') and p.name != 'package_manifest.json']
    for directory in ('sources','examples','runs'):
        files += [p for p in (HERE/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    manifest = dict(schema=1, profile='Read-only diagnostics v0.2; default CORE-R3, explicit candidate binding supported',
                    board_sha256=load_json(HERE/'board_binding.json')['board_sha256'],
                    files={str(p.relative_to(HERE)):digest(p) for p in sorted(files)},
                    hardware_connection_tested=False, fabrication_release=False,
                    latest_test_evidence=str((test_dir/'result.json').relative_to(HERE)))
    atomic_json(HERE/'package_manifest.json', manifest)
    files.append(HERE/'package_manifest.json')
    out = HERE/'M3_Diagnostics.zip'
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            z.write(p, 'diagnostics/'+str(p.relative_to(HERE)))
    # Extract exactly what will be delivered and check every byte. No .venv,
    # system paths, hidden credentials, or synthetic-to-hardware relabelling.
    with tempfile.TemporaryDirectory(prefix='m3-diagnostics-archive-') as d:
        with zipfile.ZipFile(out) as z:
            if z.testzip(): raise ValueError('ZIP CRC error')
            z.extractall(d)
        base = Path(d)/'diagnostics'
        for name, sha in manifest['files'].items():
            if digest(base/name) != sha: raise ValueError('Archive mismatch: '+name)
        for snapshot in (base/'examples').glob('*/snapshot.json'):
            if load_json(snapshot)['origin'] != 'SYNTHETIC_FIXTURE':
                raise ValueError('Example lost its synthetic label')
    print(f'{out}: {out.stat().st_size} bytes; {len(files)} files; regression+ZIP round trip passed')


if __name__ == '__main__':
    main()
