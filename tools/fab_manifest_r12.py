#!/usr/bin/env python3
"""R12 fab package binding and content checks (r12_plan.md section 4, stage D): tools/fab_manifest.py's binding and
verification for m3_design/r12/m3.kicad_pcb and its package m3_design/r12/fab/, with R12's own content checks. A
separate file because tools/fab_manifest.py's own SHA-256 is one of the inputs R10's frozen package is bound to.

R12 is one-sided JLC Economic PCBA (D-R12-01): every placed part on F, four copper layers. The content checks, each run
under KiCad's Python (KICAD_PY, else KiCad's default macOS location) by --content and --bind:
  S-4 (tools/check_r12.py --only S-4 --bom --cpl, as R10's and R11's packages run check_r10 / check_r11; R12F3-TRI-03):
    every required-fitted part in the JLC BOM and the CPL with its native identity: BOM quantity, LCSC code, Manufacturer
    Part and Footprint against the board's part fields, and the owner BOM's identities. check_r12.py is therefore
    bound among the package inputs, as check_r11.py is in R11's.
  BOM / CPL (--verify-cpl): the JLC BOM's and the CPL's designator sets are equal, with no duplicate; they are exactly
    the parts m3_design/r12_parts.py bom_lines() puts in the JLC BOM (LCSC code, not owner-fitted, not excluded from
    the BOM), with the board's LCSC codes; the owner BOM is exactly the owner-fitted parts (none since D-R12-85, so
    no owner BOM may exist); every board part out of
    the BOM is in neither; every CPL row is on the Top layer; then tools/jlc_orient_r12.py --verify-cpl rebuilds every
    CPL row from JLC's own footprint and compares it with our pads (rotation and offset corrections).
  Gerber / paste (--paste): the zip holds exactly F / In1 / In2 / B copper, both masks, F paste, both silks, Edge.Cuts,
    PTH and NPTH drills and the job file; tools/paste_check.py's rules on F paste; the paste counts: one flash per
    pasted pad, and only parts in the CPL carry paste.
The binding (tools/fab_manifest.py) hashes the board (its SHA-256), project, schematics, library, the R12 export tools
and data, tools/check_r12.py, m3_design/r12_parts.py and design/circuit.json against the five outputs (and an owner BOM
if one existed).

usage: python3 tools/fab_manifest_r12.py [board]                   verify the binding (hashes only)
       python3 tools/fab_manifest_r12.py [board] --content         verify the binding, then run the content checks
       python3 tools/fab_manifest_r12.py [board] --bind RECORD     content checks on export_fab_r12's record, then bind
       <KiCad python3> -I tools/fab_manifest_r12.py [board] --verify-cpl   the BOM / CPL check alone (no binding)
       <KiCad python3> -I tools/fab_manifest_r12.py [board] --paste        the Gerber / paste check alone (no binding)
--out DIR selects the package folder (default: the board's folder / fab).
"""
import argparse
from collections import Counter
import csv
from pathlib import Path
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fab_manifest as fm                                        # noqa: E402

ROOT = fm.ROOT
R12_BOARD = ROOT / 'm3_design/r12/m3.kicad_pcb'
_base_inputs = fm.input_hashes
R10_ONLY = ('tools/jlc_corrections.json', 'tools/jlc_easyeda/pads.json')     # R10's data: not an R12 input
R12_INPUTS = ('tools/export_fab_r12.py', 'tools/jlc_orient_r12.py', 'tools/fab_manifest_r12.py', 'tools/paste_check.py',
              'tools/check_r12.py', 'm3_design/r12_fire.py',
              'tools/jlc_corrections_r12.json', 'tools/jlc_easyeda/pads_r12.json', 'm3_design/r12_parts.py',
              'm3_design/r12/design/circuit.json')
# the Gerber zip (kicad-cli --no-protel-ext; tools/export_fab.py): file name suffixes after "<board stem>-"
GERBER_FILES = ('F_Cu.gbr', 'In1_Cu.gbr', 'In2_Cu.gbr', 'B_Cu.gbr', 'F_Mask.gbr', 'B_Mask.gbr', 'F_Paste.gbr',
                'F_Silkscreen.gbr', 'B_Silkscreen.gbr', 'Edge_Cuts.gbr', 'PTH.drl', 'NPTH.drl', 'job.gbrjob')


def input_hashes(board):
    result = {k: v for k, v in _base_inputs(board).items() if k not in R10_ONLY}
    for name in R12_INPUTS:
        result[name] = fm.sha256(ROOT / name)
    return result


def content_checks(board, out, kicad_py):
    this = str(Path(__file__).resolve())
    common = [kicad_py, '-I', this, str(board), '--out', str(out)]
    stem = Path(board).stem
    return [('S-4 BOM / CPL identities', [kicad_py, '-I', str(ROOT / 'tools/check_r12.py'), str(board), '--only', 'S-4',
                                          '--bom', str(Path(out) / f'{stem}_bom_jlc.csv'),
                                          '--cpl', str(Path(out) / f'{stem}_cpl_jlc.csv')]),
            ('BOM / CPL inventory, CPL rebuilt from JLC footprints', common + ['--verify-cpl']),
            ('Gerber layers and paste openings', common + ['--paste'])]


def install():
    """Route fab_manifest's module-level functions through the R12 variants (they call each other by name)."""
    fm.input_hashes, fm.content_checks = input_hashes, content_checks


def r12_parts_bom():
    """{'jlc': {ref: LCSC code}, 'owner': {ref: circuit.json note}} from m3_design/r12_parts.py bom_lines() (KiCad
    Python: it reads the lands with pcbnew). Parts excluded from the BOM are in neither."""
    sys.path.insert(0, str(ROOT / 'm3_design'))
    import r12_parts
    notes = r12_parts.r12.circuit()['owner_fit']
    jlc, owner = {}, {}
    for code, line in r12_parts.bom_lines().items():
        for ref in line['refs']:
            if ref in notes:
                owner[ref] = f'owner-fitted by hand after reflow: {notes[ref]}'
            else:
                jlc[ref] = code
    return {'jlc': jlc, 'owner': owner}


def _csv(path, column):
    with open(path, newline='') as source:
        reader = csv.DictReader(source)
        rows = list(reader)
    if column not in (reader.fieldnames or []):
        raise ValueError(f'{path.name}: no {column!r} column')
    return rows


def verify_cpl(board, out):
    """The BOM / CPL content check (KiCad Python). Returns the list of issues."""
    import pcbnew
    board, out = Path(board).resolve(), Path(out)
    stem = board.stem
    issues = []
    model = r12_parts_bom()
    b = pcbnew.LoadBoard(str(board))
    on_board = {}
    out_of_bom = set()
    for f in b.GetFootprints():
        ref = f.GetReference()
        if not ref or ref.startswith('#'):
            continue
        if f.IsExcludedFromBOM():
            out_of_bom.add(ref)
        else:
            on_board[ref] = f.GetField('LCSC').GetText() if f.HasField('LCSC') else ''
        if f.IsFlipped():
            issues.append(f'{ref} is on the bottom side (D-R12-01: every part on F)')
    expected = set(model['jlc']) | set(model['owner'])
    if set(on_board) != expected:
        issues.append(f'board BOM parts differ from r12_parts.bom_lines(): board only {sorted(set(on_board) - expected)}, '
                      f'r12_parts only {sorted(expected - set(on_board))}')
    for ref, code in model['jlc'].items():
        if ref in on_board and on_board[ref] != code:
            issues.append(f'{ref}: board LCSC {on_board[ref]!r}, r12_parts {code!r}')

    def designators(rows, name):
        refs = [r.strip() for row in rows for r in row['Designator'].split(',') if r.strip()]
        dup = sorted(r for r, n in Counter(refs).items() if n > 1)
        if dup:
            issues.append(f'{name}: duplicate designators {dup}')
        return set(refs)

    bom_rows = _csv(out / f'{stem}_bom_jlc.csv', 'Designator')
    bom = designators(bom_rows, 'JLC BOM')
    for row in bom_rows:
        for ref in (r.strip() for r in row['Designator'].split(',')):
            if ref in model['jlc'] and row.get('LCSC Part #') != model['jlc'][ref]:
                issues.append(f'JLC BOM: {ref} on LCSC {row.get("LCSC Part #")!r}, r12_parts {model["jlc"][ref]!r}')
    cpl_rows = _csv(out / f'{stem}_cpl_jlc.csv', 'Designator')
    cpl = designators(cpl_rows, 'CPL')
    owner_path = out / f'{stem}_bom_owner.csv'
    owner = designators(_csv(owner_path, 'Designator'), 'owner BOM') if owner_path.exists() else set()
    if bom != cpl:
        issues.append(f'JLC BOM and CPL designators differ: BOM only {sorted(bom - cpl)}, CPL only {sorted(cpl - bom)}')
    if bom != set(model['jlc']):
        issues.append(f'JLC BOM is not r12_parts\' JLC set: extra {sorted(bom - set(model["jlc"]))}, '
                      f'missing {sorted(set(model["jlc"]) - bom)}')
    if owner != set(model['owner']):
        issues.append(f'owner BOM {sorted(owner)} is not r12_parts\' owner-fitted set {sorted(model["owner"])}')
    stray = sorted((bom | cpl) & (out_of_bom | set(model['owner'])))
    if stray:
        issues.append(f'owner-fitted or out-of-BOM parts in the JLC BOM / CPL: {stray}')
    layers = Counter(row.get('Layer') for row in cpl_rows)
    if set(layers) - {'Top'}:
        issues.append(f'CPL rows off the Top layer: {dict(layers)}')
    result = subprocess.run([sys.executable, '-I', str(ROOT / 'tools/jlc_orient_r12.py'),
                             str(ROOT / 'tools/jlc_easyeda/pads_r12.json'), str(board),
                             '--verify-cpl', str(out / f'{stem}_cpl_jlc.csv')], capture_output=True, text=True,
                            timeout=600)
    lines = [line for line in (result.stdout + result.stderr).splitlines()
             if line.strip() and not any(word in line for word in fm.NOISE)]
    if result.returncode:
        issues += ['jlc_orient_r12 --verify-cpl: ' + line for line in lines[-20:]] or ['jlc_orient_r12 failed']
    print(f'BOM / CPL: {len(bom_rows)} JLC BOM lines, {len(bom)} JLC parts = {len(cpl)} CPL rows '
          f'({layers.get("Top", 0)} Top), owner BOM {sorted(owner)}, {len(out_of_bom)} parts out of the BOM'
          + (f'; {lines[-1].strip()}' if lines else ''))
    return issues


def paste(board, out):
    """The Gerber layer and paste check (KiCad Python). Returns the list of issues."""
    import pcbnew
    import paste_check
    board, out = Path(board).resolve(), Path(out)
    stem = board.stem
    issues = []
    zpath = out / f'{stem}_gerber.zip'
    with zipfile.ZipFile(zpath) as z:
        names = set(z.namelist())
    want = {f'{stem}-{suffix}' for suffix in GERBER_FILES}
    if names != want:
        issues.append(f'Gerber zip: missing {sorted(want - names)}, unexpected {sorted(names - want)}')
    paste_check.SIDES = {'F': paste_check.SIDES['F']}           # one assembled side: no B paste layer (D-R12-01)
    b = pcbnew.LoadBoard(str(board))
    try:
        found, evidence = paste_check.check(b, paste_check.gerbers(zpath))
    except ValueError as error:
        return issues + [f'paste: {error}']
    issues += found
    cpl = {row['Designator'] for row in _csv(out / f'{stem}_cpl_jlc.csv', 'Designator')}
    pasted = {}
    for f in b.GetFootprints():
        n = sum(1 for p in f.Pads() if p.IsOnLayer(pcbnew.F_Paste) or p.IsOnLayer(pcbnew.B_Paste))
        if n:
            pasted[f.GetReference()] = n
    stray = sorted(set(pasted) - cpl)
    if stray:
        issues.append(f'paste on parts JLC does not place (not in the CPL): {stray}')
    front = evidence.get('F_Paste', {})
    if front.get('flashes') != sum(pasted.values()):
        issues.append(f'paste count: {front.get("flashes")} flashes, {sum(pasted.values())} pasted pads')
    print(f'Gerber / paste: {len(names)} files; F paste {front.get("flashes")} flashes on {front.get("pads_with_paste")} '
          f'pasted pads of {len(pasted)} parts; {len(cpl) - len(set(pasted) & cpl)} CPL parts unpasted (THT)')
    return issues


def main():
    install()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('board', nargs='?', type=Path, default=R12_BOARD)
    parser.add_argument('--out', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--bind', type=Path, metavar='RECORD')
    mode.add_argument('--content', action='store_true')
    mode.add_argument('--verify-cpl', action='store_true')
    mode.add_argument('--paste', action='store_true')
    args = parser.parse_args()
    out = args.out or args.board.parent / 'fab'
    if args.verify_cpl or args.paste:
        issues = (verify_cpl if args.verify_cpl else paste)(args.board, out)
        for issue in issues:
            print('FAIL', issue)
        sys.exit(1 if issues else 0)
    try:
        if args.bind:
            path = fm.bind(args.board, out, args.bind)
            print(f'R12 fab manifest: bound {path.name} after the content checks')
        count = fm.verify_manifest(args.board, out)
        if args.content:
            failures = fm.run_content_checks(args.board, out)
            if failures:
                raise ValueError('content checks failed: ' + ', '.join(label for label, _ in failures))
    except (OSError, ValueError, KeyError, TypeError, AssertionError, subprocess.SubprocessError) as error:
        parser.exit(1, f'R12 fab manifest: FAIL: {error}\n')
    print(f'R12 fab manifest: OK; {count} outputs match the current CAD and export inputs'
          + ('; content checks pass' if args.content or args.bind else ''))


if __name__ == '__main__':
    main()
