"""Bind fabrication outputs to the exact CAD and placement inputs used to export them."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


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


def write_manifest(board, out, before):
    after = input_hashes(board)
    if before != after:
        raise ValueError('CAD or export inputs changed during fabrication export')
    stem = Path(board).stem
    names = [f'{stem}_{suffix}' for suffix in ('gerber.zip', 'bom_jlc.csv', 'cpl_jlc.csv',
                                              'assembly_top.pdf', 'assembly_bottom.pdf')]
    owner = out / f'{stem}_bom_owner.csv'
    if owner.exists():
        names.append(owner.name)
    manifest = {'schema': 1, 'inputs_sha256': after,
                'outputs_sha256': {name: sha256(out / name) for name in names}}
    path = out / f'{stem}_fab_manifest.json'
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return path


def verify_manifest(board, out):
    stem = Path(board).stem
    path = out / f'{stem}_fab_manifest.json'
    data = json.loads(path.read_text())
    if data.get('schema') != 1 or data.get('inputs_sha256') != input_hashes(board):
        raise ValueError('fabrication package does not match current CAD/export inputs; regenerate it')
    outputs = data.get('outputs_sha256', {})
    required = {f'{stem}_{suffix}' for suffix in ('gerber.zip', 'bom_jlc.csv', 'cpl_jlc.csv',
                                               'assembly_top.pdf', 'assembly_bottom.pdf')}
    if not required <= outputs.keys():
        raise ValueError('fabrication manifest is missing required outputs')
    for name, expected in outputs.items():
        if Path(name).name != name or sha256(out / name) != expected:
            raise ValueError(f'fabrication output missing or changed: {name}')
    return len(outputs)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', nargs='?', type=Path,
                        default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    try:
        count = verify_manifest(args.board, args.out or args.board.parent / 'fab')
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Fab manifest: FAIL: {error}\n')
    print(f'Fab manifest: OK; {count} outputs match the current CAD and export inputs')
