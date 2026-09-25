"""python -m diagnostics: inventory, bounded SWD capture, and offline reports."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from .engine import HERE, analyze, digest, load_json, markdown
from .transport import PyOCDReader, atomic_json, capture, probes


def write_report(snapshot_path, out, bench_path=None, binding_path=HERE/'board_binding.json'):
    snapshot = load_json(snapshot_path)
    binding = load_json(binding_path)
    result = analyze(snapshot, binding, load_json(bench_path) if bench_path else None)
    result['input_sha256'] = digest(snapshot_path)
    result['bench_input_sha256'] = digest(bench_path) if bench_path else None
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    atomic_json(out/'report.json', result)
    (out/'report.md').write_text(markdown(result))
    print(f"{result['overall']} — {out/'report.md'}")
    return 2 if result['overall'] == 'ISSUES_FOUND' else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('probes', help='List probes; does not connect to the target chip')
    for name in ('capture', '_worker'):
        p = sub.add_parser(name)
        p.add_argument('--probe-id', required=True)
        p.add_argument('--assembly-id', required=True)
        p.add_argument('--out', type=Path, required=True)
        p.add_argument('--binding', type=Path, default=HERE/'board_binding.json')
    p = sub.add_parser('report', help='Interpret a raw snapshot offline, optionally with bench measurements from the same session')
    p.add_argument('snapshot', type=Path)
    p.add_argument('--bench', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--binding', type=Path, default=HERE/'board_binding.json')
    p = sub.add_parser('bench-template', help='Generate an empty measurement sheet; never fills in fake measurements')
    p.add_argument('snapshot', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--binding', type=Path, default=HERE/'board_binding.json')
    args = parser.parse_args()
    if args.command == 'probes':
        ps = probes()
        print(json.dumps({'probes': [dict(id=p.unique_id, description=p.description) for p in ps],
                          'target_connected_by_this_command': False}, ensure_ascii=False, indent=2))
        return 0
    if args.command == 'report':
        return write_report(args.snapshot, args.out, args.bench, args.binding)
    args.binding=args.binding.resolve()
    binding = load_json(args.binding)
    if args.command == 'bench-template':
        from .engine import validate_snapshot
        s = load_json(args.snapshot)
        validate_snapshot(s, binding)
        if args.out.exists():
            raise FileExistsError(str(args.out))
        b = dict(schema=1, origin='SYNTHETIC_FIXTURE' if s['origin']=='SYNTHETIC_FIXTURE' else 'MANUAL_BENCH',
                 assembly_id=s['assembly_id'], capture_id=s['capture_id'],
                 board_sha256=binding['board_sha256'], points=[
                     dict(net=n, **p, measurement=None) for n, p in binding['probes'].items()])
        atomic_json(args.out, b)
        print(args.out)
        return 0
    args.out = args.out.resolve()
    if not args.assembly_id.strip():
        raise ValueError('Nonempty assembly-id required')
    if args.command == '_worker':
        capture(PyOCDReader(args.probe_id), binding, args.assembly_id, args.out)
        return 0
    args.out.mkdir(parents=True, exist_ok=False)
    snapshot_path = args.out/'snapshot.json'
    cmd = [sys.executable, '-m', 'diagnostics', '_worker', '--probe-id', args.probe_id,
           '--assembly-id', args.assembly_id, '--out', str(snapshot_path), '--binding',str(args.binding)]
    # No shell, no indefinitely blocking USB enumeration/driver call. Preserve
    # partial snapshots on timeout; a failed capture never becomes an empty pass.
    with (args.out/'driver.log').open('w') as log:
        proc = subprocess.Popen(cmd, cwd=HERE.parent, stdout=log, stderr=subprocess.STDOUT)
        try:
            code = proc.wait(timeout=25)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait()
            code = -1
    if not snapshot_path.exists():
        raise RuntimeError('Driver failed to start, see driver.log; no hardware readings were produced.')
    if code:
        s = load_json(snapshot_path)
        s['state'], s['error'] = 'ABORTED', 'Capture worker failed/timed out; see driver.log'
        atomic_json(snapshot_path, s)
    write_report(snapshot_path, args.out/'analysis', binding_path=args.binding)
    state = load_json(snapshot_path)['state']
    return 0 if state == 'CAPTURED' else 3


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError) as e:
        print(type(e).__name__ + ': ' + str(e), file=sys.stderr)
        raise SystemExit(3)
