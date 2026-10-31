"""Bind fabrication outputs to the exact CAD and placement inputs used to export them, only after their content checks.

R18-GATE-04: tools/export_fab.py no longer binds. With --pending it records the export (the inputs as they were when it
started, the outputs as it wrote them); bind() then runs the content checks (CONTENT_CHECKS: check_r10 S-4 on the
exported BOM and CPL, jlc_orient --verify-cpl, paste_check) and writes the manifest only when every check passes and
neither the inputs nor the outputs changed since the export. A failed check leaves no manifest, so tools/check.sh fails.
check.sh runs --content on the repository board: the hash binding and the same content checks on the bound package.

usage: python3 tools/fab_manifest.py [board]                  verify the binding (hashes only)
       python3 tools/fab_manifest.py [board] --content        verify the binding, then run the content checks
       python3 tools/fab_manifest.py [board] --bind RECORD    content checks on export_fab's record, then bind
The content checks run under KiCad's Python (KICAD_PY, else KiCad's default macOS location).
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent.parent
KICAD_PY_DEFAULT = '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
OUTPUTS = ('gerber.zip', 'bom_jlc.csv', 'cpl_jlc.csv', 'assembly_top.pdf', 'assembly_bottom.pdf')
NOISE = ('Debug: Adding duplicate', 'create wxApp', 'Fontconfig')     # KiCad's console chatter, not check output


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_hashes(board):
    board = Path(board).resolve()
    paths = {board, *(board.with_suffix(ext) for ext in ('.kicad_pro', '.kicad_dru'))}
    paths.update(board.parent.glob('*.kicad_sch'))
    for pattern in ('*.kicad_mod', '*.kicad_sym', '*.wrl', '*.step', '*.stp'):
        paths.update((board.parent / 'kilib').rglob(pattern))
    paths.update(board.parent / name for name in ('fp-lib-table', 'sym-lib-table'))
    result = {'cad/' + str(path.relative_to(board.parent)): sha256(path) for path in sorted(paths)}
    for name in ('export_fab.py', 'jlc_orient.py', 'jlc_corrections.json', 'jlc_easyeda/pads.json',
                 'fab_manifest.py'):
        result['tools/' + name] = sha256(ROOT / 'tools' / name)
    result['quality_audit/sexpr.py'] = sha256(ROOT / 'quality_audit/sexpr.py')
    return result


def output_names(board, out):
    stem = Path(board).stem
    names = [f'{stem}_{suffix}' for suffix in OUTPUTS]
    owner = Path(out) / f'{stem}_bom_owner.csv'
    if owner.exists():
        names.append(owner.name)
    return names


def write_manifest(board, out, before):
    """The binding itself (no checks): bind() is the only command-line path that writes it."""
    after = input_hashes(board)
    if before != after:
        raise ValueError('CAD or export inputs changed during fabrication export')
    manifest = {'schema': 1, 'inputs_sha256': after,
                'outputs_sha256': {name: sha256(out / name) for name in output_names(board, out)}}
    path = out / f'{Path(board).stem}_fab_manifest.json'
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return path


def write_pending(board, out, before, record):
    """export_fab's unbound export record: the inputs at the start of the export (unchanged at its end) and the
    outputs it wrote. It is not a manifest; bind() turns it into one after the content checks."""
    after = input_hashes(board)
    if before != after:
        raise ValueError('CAD or export inputs changed during fabrication export')
    data = {'schema': 1, 'kind': 'unbound fab export (tools/fab_manifest.py --bind)', 'board': Path(board).name,
            'inputs_sha256': after,
            'outputs_sha256': {name: sha256(out / name) for name in output_names(board, out)}}
    Path(record).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    return Path(record)


def verify_manifest(board, out):
    stem = Path(board).stem
    path = out / f'{stem}_fab_manifest.json'
    data = json.loads(path.read_text())
    if data.get('schema') != 1 or data.get('inputs_sha256') != input_hashes(board):
        raise ValueError('fabrication package does not match current CAD/export inputs; regenerate it')
    outputs = data.get('outputs_sha256', {})
    required = {f'{stem}_{suffix}' for suffix in OUTPUTS}
    if not required <= outputs.keys():
        raise ValueError('fabrication manifest is missing required outputs')
    for name, expected in outputs.items():
        if Path(name).name != name or sha256(out / name) != expected:
            raise ValueError(f'fabrication output missing or changed: {name}')
    return len(outputs)


def kicad_python():
    exe = os.environ.get('KICAD_PY') or KICAD_PY_DEFAULT
    if not Path(exe).exists():
        raise ValueError(f'KiCad Python {exe} unavailable for the fab content checks; set KICAD_PY')
    return exe


def content_checks(board, out, kicad_py):
    """(label, argv) of every content check on a package (R18-GATE-04). R1-07 / R3-GATE-05: every required-fitted part
    is in the exported BOM and CPL with its native identity; every CPL row rebuilt from JLC's own footprint lands on our
    pads (orientation included); one paste opening per pasted pad and none stray."""
    board, out, tools = Path(board), Path(out), ROOT / 'tools'
    stem = board.stem
    return [
        ('S-4 BOM / CPL', [kicad_py, '-I', str(tools / 'check_r10.py'), str(board), '--only', 'S-4',
                           '--bom', str(out / f'{stem}_bom_jlc.csv'), '--cpl', str(out / f'{stem}_cpl_jlc.csv')]),
        ('CPL rebuilt from JLC footprints', [kicad_py, '-I', str(tools / 'jlc_orient.py'),
                                             str(tools / 'jlc_easyeda/pads.json'), str(board),
                                             '--verify-cpl', str(out / f'{stem}_cpl_jlc.csv')]),
        ('paste openings', [kicad_py, '-I', str(tools / 'paste_check.py'), str(board), str(out / f'{stem}_gerber.zip')]),
    ]


def run_content_checks(board, out, kicad_py=None, echo=print):
    """Run every content check; returns [(label, exit code)] of the failing ones (each failure's output is echoed)."""
    kicad_py = kicad_py or kicad_python()
    failures = []
    for label, argv in content_checks(board, out, kicad_py):
        result = subprocess.run(argv, capture_output=True, text=True, timeout=600,
                                env=dict(os.environ, PYTHONUNBUFFERED='1'))
        lines = [line for line in (result.stdout + result.stderr).splitlines()
                 if line.strip() and not any(word in line for word in NOISE)]
        if result.returncode:
            failures.append((label, result.returncode))
            echo(f'fab content check {label}: FAIL (exit {result.returncode})')
            for line in lines[-40:]:
                echo('  ' + line)
        else:
            echo(f'fab content check {label}: OK' + (f' ({lines[-1].strip()})' if lines else ''))
    return failures


def bind(board, out, record, kicad_py=None, echo=print):
    """Turn export_fab's record into the manifest: nothing changed since the export, every content check passes."""
    board, out, record = Path(board), Path(out), Path(record)
    data = json.loads(record.read_text())
    if data.get('schema') != 1 or data.get('board') != board.name or not isinstance(data.get('outputs_sha256'), dict):
        raise ValueError(f'{record} is not an export record for {board.name}')
    if data.get('inputs_sha256') != input_hashes(board):
        raise ValueError('CAD or export inputs changed since the export; run m3_design/r10_fab.sh again')
    names = output_names(board, out)
    if sorted(data['outputs_sha256']) != sorted(names) or any(
            not (out / name).is_file() or sha256(out / name) != data['outputs_sha256'][name] for name in names):
        raise ValueError('fabrication outputs changed since the export; run m3_design/r10_fab.sh again')
    failures = run_content_checks(board, out, kicad_py, echo)
    if failures:
        raise ValueError('content checks failed (' + ', '.join(label for label, _ in failures) +
                         '): the package is not bound')
    path = write_manifest(board, out, data['inputs_sha256'])
    if json.loads(path.read_text())['outputs_sha256'] != data['outputs_sha256']:
        path.unlink()
        raise ValueError('fabrication outputs changed during the content checks; the package is not bound')
    record.unlink()
    return path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('board', nargs='?', type=Path,
                        default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    parser.add_argument('--out', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--bind', type=Path, metavar='RECORD', help="export_fab.py --pending's record to bind")
    mode.add_argument('--content', action='store_true', help='also run the content checks on the bound package')
    args = parser.parse_args()
    out = args.out or args.board.parent / 'fab'
    try:
        if args.bind:
            path = bind(args.board, out, args.bind)
            print(f'Fab manifest: bound {path.name} after the content checks')
        count = verify_manifest(args.board, out)
        if args.content:
            failures = run_content_checks(args.board, out)
            if failures:
                raise ValueError('content checks failed: ' + ', '.join(label for label, _ in failures))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(1, f'Fab manifest: FAIL: {error}\n')
    print(f'Fab manifest: OK; {count} outputs match the current CAD and export inputs'
          + ('; content checks pass' if args.content or args.bind else ''))
