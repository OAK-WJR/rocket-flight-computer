"""Replay reviewed R5 bypass, routing, land and spacing repairs, then refill.

Native CAD remains authoritative. The recorded patch removes only old capacitor
spurs, moves C83/C86 opposite U10, and adds C97/C98/C99 near U11. Existing copper
outside these patches is preserved. C100 supplies local U12 VCCA bypass; C73
is moved 0.6 mm away from U7. Replay is idempotent and rejects partial state.
Run fill_part_metadata.py --write and the full board gate after a rebuild.

TI TPS2553, sections 10.2.1.2.4 and 12.1:
https://www.ti.com/lit/ds/symlink/tps2553.pdf
TI TPS2121, section 11:
https://www.ti.com/lit/ds/symlink/tps2121.pdf
C97/C98 reuse C86 (Samsung CL10B105KA8NNNC, C29936);
C99 reuses C88 (100 nF, 50 V, C307331). C28, C82, C6/C7 and C84 stay.
C100 reuses C13 (100 nF, 16 V, C1525); C90 remains on the rail.
TI TXU0202, section 12.1: https://www.ti.com/lit/ds/symlink/txu0202.pdf
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'quality_audit'))
from sexpr import read, properties, patch
from r5_scoped_patch import apply_delta, semantic


def references(root):
    return {properties(n)['Reference'].items[2].atom for n in root.items
            if n.key in ('footprint', 'symbol') and 'Reference' in properties(n)}


def apply(project):
    data = json.loads(Path(__file__).with_suffix('.json').read_text())
    board = project / 'm3.kicad_pcb'
    text = board.read_text()
    root = read(text)
    present = references(root) & {'C97', 'C98', 'C99'}
    if present and present != {'C97', 'C98', 'C99'}:
        raise RuntimeError('Partial capacitor repair; inspect native CAD before replay.')
    if not present:
        objects = {n.children('uuid')[0].items[1].atom: n for n in root.items
                   if n.key in ('footprint', 'segment', 'via')}
        needed = set(data['remove']) | set(data['replace'])
        if not needed <= objects.keys():
            raise RuntimeError('Board is not the recorded R5 baseline; missing patch objects.')
        edits = [(objects[k].start, objects[k].end, '') for k in data['remove']]
        edits += [(objects[k].start, objects[k].end, value) for k, value in data['replace'].items()]
        edits.append((root.end - 1, root.end - 1, '\n\t' + '\n\t'.join(data['add']) + '\n'))
        board.write_text(patch(text, edits))
    schematic = project / 'logic_power_path.kicad_sch'
    text = schematic.read_text()
    root = read(text)
    present = references(root) & {'C97', 'C98', 'C99'}
    if present and present != {'C97', 'C98', 'C99'}:
        raise RuntimeError('Partial schematic repair; inspect native CAD before replay.')
    if not present:
        schematic.write_text(patch(text, [(root.end - 1, root.end - 1,
                                          '\n\t' + '\n\t'.join(data['schematic_add']) + '\n')]))
    apply_vcca_spacing(project, data['vcca_spacing'])
    # Reviewed footprint preimages include verified part identities. Fill before
    # the guarded geometry stages; UUID-only differences from a rebuild are safe.
    subprocess.run([sys.executable, str(ROOT / 'tools/fill_part_metadata.py'),
                    '--project', str(project), '--write'], check=True)
    original = board.read_text()
    updated = original
    for name, delta in data.get('scoped_repairs', {}).items():
        try:
            updated = apply_delta(updated, delta)
        except RuntimeError as exc:
            raise RuntimeError(name + ': ' + str(exc)) from exc
    library_edits = []
    for relative, delta in data.get('libraries', {}).items():
        path = project / relative
        text = path.read_text()
        if semantic(read(text).value()) == semantic(read(delta['after']).value()):
            continue
        if semantic(read(text).value()) != semantic(read(delta['before']).value()):
            raise RuntimeError('Library footprint changed since review: ' + relative)
        library_edits.append((path, text, delta['after']))
    if board.read_text() != original or any(p.read_text() != old for p, old, _ in library_edits):
        raise RuntimeError('CAD changed during replay; no scoped repair written.')
    if updated != original:
        board.write_text(updated)
    for path, _, after in library_edits:
        path.write_text(after)
    return board


def apply_vcca_spacing(project, data):
    board = project / 'm3.kicad_pcb'
    schematic = project / 'camera_uart.kicad_sch'
    pcb_text, sch_text = board.read_text(), schematic.read_text()
    pcb_root, sch_root = read(pcb_text), read(sch_text)
    present = ('C100' in references(pcb_root), 'C100' in references(sch_root))
    if any(present):
        if not all(present):
            raise RuntimeError('Partial C100 repair; inspect native CAD before replay.')
        c73 = next(n for n in pcb_root.items if n.key == 'footprint'
                   and properties(n)['Reference'].items[2].atom == 'C73')
        at = c73.children('at')[0]
        if tuple(float(v.atom) for v in at.items[1:3]) != (42.4, 69.4):
            raise RuntimeError('C100 exists but C73 spacing repair is absent; inspect native CAD.')
        return
    objects = {n.children('uuid')[0].items[1].atom: n for n in pcb_root.items
               if n.key in ('footprint', 'segment', 'via')}
    needed = set(data['remove']) | set(data['replace'])
    if not needed <= objects.keys():
        raise RuntimeError('Board is not the recorded bypass-repaired baseline; missing patch objects.')
    edits = [(objects[k].start, objects[k].end, '') for k in data['remove']]
    edits += [(objects[k].start, objects[k].end, value) for k, value in data['replace'].items()]
    edits.append((pcb_root.end - 1, pcb_root.end - 1, '\n\t' + '\n\t'.join(data['add']) + '\n'))
    pcb_text = patch(pcb_text, edits)
    sch_text = patch(sch_text, [(sch_root.end - 1, sch_root.end - 1,
                               '\n\t' + '\n\t'.join(data['schematic_add']) + '\n')])
    board.write_text(pcb_text)
    schematic.write_text(sch_text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=ROOT / 'm3_design' / 'assembly_review')
    parser.add_argument('--no-refill', action='store_true', help='Caller must refill zones before checking.')
    args = parser.parse_args()
    board = apply(args.project)
    if not args.no_refill:
        cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli')
        if not cli:
            raise RuntimeError('Set KICAD_CLI or refill the saved board in KiCad before checking.')
        with tempfile.TemporaryDirectory() as out:
            report = Path(out) / 'drc.json'
            subprocess.run([cli, 'pcb', 'drc', '--refill-zones', '--save-board', '--severity-all',
                            '--schematic-parity', '--format', 'json', '-o', str(report), str(board)], check=True)
            result = json.loads(report.read_text())
            if any(result.get(k) for k in ('violations', 'unconnected_items', 'schematic_parity')):
                raise RuntimeError('Replayed CAD did not pass DRC/parity; inspect it before use.')
    print('Reviewed R5 CAD repairs present:', board)


if __name__ == '__main__':
    main()
