#!/usr/bin/env python3
"""Fresh read-only DRC with hashed evidence; nonzero on any unresolved finding.

A zero exit status covers only the checks explicitly recorded, never flight readiness.
No routing/build scripts are invoked. No report from a previous run is reused.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from audit_artifacts import audit
from normalize_metadata import part_table, table_drift


def input_hashes(board):
    paths = [board]
    paths += [board.with_suffix(ext) for ext in ('.kicad_pro', '.kicad_dru', '.kicad_sch')]
    paths += [board.parent / name for name in ('fp-lib-table', 'sym-lib-table')]
    # Hierarchical sheets and pinned symbol libraries are electrical inputs too.
    # Hash all project-local sheets, not just the root; also cover referenced
    # local model assets so archived review evidence includes its 3D inputs.
    paths += sorted(board.parent.rglob('*.kicad_sch'))
    paths += sorted(board.parent.rglob('*.kicad_sym'))
    for ext in ('*.kicad_mod','*.step','*.stp','*.wrl'):
        paths += sorted((board.parent / 'kilib').rglob(ext))
    paths += sorted((board.parent / 'sources').rglob('*.pdf'))
    paths += [board.parent / name for name in
              ('circuit_connections.json','parts.json','schematic.net.xml')]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def report_findings(report):
    for key in ('violations', 'unconnected_items', 'schematic_parity'):
        if key not in report or not isinstance(report[key], list):
            raise ValueError('Missing/malformed DRC section: ' + key)
    severities = report.get('included_severities', [])
    if 'error' not in severities or 'warning' not in severities:
        raise ValueError('DRC report does not cover errors AND warnings')
    return {key: len(report[key]) for key in
            ('violations', 'unconnected_items', 'schematic_parity')}


def erc_findings(report):
    if not isinstance(report.get('sheets'),list) or not report['sheets']:
        raise ValueError('Missing/malformed ERC sheets')
    if not {'error','warning'}<=set(report.get('included_severities',[])):
        raise ValueError('ERC report does not cover errors AND warnings')
    if any(not isinstance(s.get('violations'),list) for s in report['sheets']):
        raise ValueError('Missing/malformed ERC violations')
    return sum(len(s['violations']) for s in report['sheets'])


def native_refill_python(cli):
    """Find KiCad's Python for macOS CLI builds whose GUI refill needs a screen."""
    configured = os.environ.get('KICAD_PY')
    if configured:
        return Path(configured)
    if sys.platform == 'darwin':
        bundled = (cli.resolve().parent.parent / 'Frameworks' / 'Python.framework' /
                   'Versions' / 'Current' / 'bin' / 'python3')
        if bundled.is_file():
            return bundled
    return None


def refill_snapshot(board, directory, python, result, timeout):
    """Fill an isolated native project; never substitute its previously saved fill."""
    project = directory / 'project'
    shutil.copytree(board.parent, project,
                    ignore=shutil.ignore_patterns('fab', '__pycache__', '*.lck', '*.kicad_prl'))
    snapshot = project / board.name
    command = [str(python), '-I', str(Path(__file__).with_name('refill_zones.py')), str(snapshot)]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    result['refill'] = {'method': 'native pcbnew.ZONE_FILLER on isolated project',
                        'command': command, 'returncode': proc.returncode,
                        'stdout': proc.stdout, 'stderr': proc.stderr}
    if proc.returncode != 0 or 'Native zone fill complete' not in proc.stdout:
        raise ValueError('Native zone fill failed; saved fill is not accepted')
    result['refill']['board_sha256'] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    return snapshot


def verify(board, cli, evidence, builder=None, timeout=60, refill_python=None):
    if evidence.exists():
        raise ValueError('Evidence already exists; use a fresh filename')
    before = input_hashes(board)
    result = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'board': str(board), 'inputs_sha256': before, 'ok': False,
              'scope': 'Metadata, source-table drift, ERC, PCB/schematic parity and configured DRC.',
              'electrical_validation': 'not performed',
              'mechanical_validation': 'not performed', 'issues': []}
    issues = result['issues']
    try:
        metadata = audit(board)
        result['metadata'] = metadata
        if metadata['missing_required_part_fields']:
            issues.append('Missing required fitted-part identity fields')
        if metadata['conflicting_part_fields']:
            issues.append('Conflicting distributor part fields')
        if any(m['exists'] is not True for m in metadata['models']):
            issues.append('Missing or unresolved model paths')
        if any(m['absolute_path'] for m in metadata['models']):
            issues.append('Non-portable absolute model paths')
        if builder:
            result['builder_sha256'] = hashlib.sha256(builder.read_bytes()).hexdigest()
            drift = table_drift(board.read_text(), part_table(builder))
            result['builder_drift'] = drift
            if drift:
                issues.append('PCB metadata differs from builder PARTS table')
        result['tool_version'] = subprocess.run(
            [str(cli), '--version'], check=True, text=True,
            capture_output=True, timeout=10).stdout.strip()
        with tempfile.TemporaryDirectory(prefix='pcb_drc_') as temp:
            refill_python = refill_python or native_refill_python(cli)
            checked_board = (refill_snapshot(board, Path(temp), refill_python, result, timeout)
                             if refill_python else board)
            report_path = Path(temp) / 'drc.json'
            command = [str(cli), 'pcb', 'drc', '--format', 'json',
                       '--severity-all', '--all-track-errors',
                       '--exit-code-violations', '--output', str(report_path)]
            if not refill_python:
                command.append('--refill-zones')
            has_schematic = board.with_suffix('.kicad_sch').is_file()
            if has_schematic:
                command.append('--schematic-parity')
            result['schematic_parity_requested'] = has_schematic
            command.append(str(checked_board))
            result['command'] = command
            proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            result.update(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
            if proc.returncode not in (0, 5):
                issues.append('DRC tool failed with exit code %s' % proc.returncode)
            report_bytes = report_path.read_bytes()
            report = json.loads(report_bytes)
            result['drc'] = report
            result['drc_sha256'] = hashlib.sha256(report_bytes).hexdigest()
            counts = report_findings(report)
            result['counts'] = counts
            result['violation_types'] = dict(Counter(v['type'] for v in report['violations']))
            if any(counts.values()) or proc.returncode == 5:
                issues.append('Unresolved DRC findings (including warnings/exclusions)')
            result['ignored_checks'] = report.get('ignored_checks', [])
            if result['ignored_checks']:
                issues.append('DRC has disabled checks requiring explicit review')
            if not has_schematic:
                issues.append('No sibling schematic: independent PCB/schematic parity unavailable')
            else:
                erc_path=Path(temp)/'erc.json'
                command=[str(cli),'sch','erc','--format','json','--severity-all',
                         '--exit-code-violations','--output',str(erc_path),
                         str(board.with_suffix('.kicad_sch'))]
                ep=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
                result['erc_command']=command;result['erc_returncode']=ep.returncode
                result['erc_stderr']=ep.stderr
                if ep.returncode not in (0,5):issues.append('ERC tool failed with exit code %s'%ep.returncode)
                data=erc_path.read_bytes();erc=json.loads(data)
                result['erc']=erc;result['erc_sha256']=hashlib.sha256(data).hexdigest()
                result['erc_violations']=erc_findings(erc)
                if result['erc_violations'] or ep.returncode==5:issues.append('Unresolved ERC findings')
                if erc.get('ignored_checks',[]):issues.append('ERC has disabled checks requiring explicit review')
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        issues.append('%s: %s' % (type(exc).__name__, exc))
    after = input_hashes(board)
    result['inputs_unchanged'] = before == after
    if before != after:
        issues.append('Input changed during verification; evidence is invalid')
    if builder and result.get('builder_sha256') != hashlib.sha256(builder.read_bytes()).hexdigest():
        issues.append('Builder changed during verification')
    result['ok'] = not issues
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('--builder', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cli', type=Path, default=Path(
        '/Applications/KiCad.app/Contents/MacOS/kicad-cli'))
    parser.add_argument('--timeout', type=int, default=60)
    parser.add_argument('--refill-python', type=Path,
                        help='KiCad Python: refill an isolated project before native CLI DRC')
    args = parser.parse_args()
    result = verify(args.board.resolve(), args.cli, args.output,
                    args.builder.resolve() if args.builder else None, args.timeout, args.refill_python)
    print(args.board.name, 'PASS' if result['ok'] else 'BLOCKED', result.get('counts', {}))
    for issue in result['issues']:
        print(' -', issue)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
