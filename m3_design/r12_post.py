#!/usr/bin/env python3
"""R12 post stage (M3-ASSY-R12, r12_plan.md section 4 stage D; D-R12-80): silkscreen, designators, Fab references,
part-number fields, the title block and the saved zone fill, from the frozen table m3_design/r12_legends.tsv.
No search (D-R12-26): m3_design/r12_legends_aid.py drafted the table once; this stage only applies and checks it.

usage: <KiCad python3> -I -B m3_design/r12_post.py [--board m3_design/r12/m3.kicad_pcb] [--report out.json]
       [--table m3_design/r12_legends.tsv]

R11's post stage (m3_design/r11_post.py: apply, contract, table format) run with R12's revision, KIID seed, table and
gate data, and gated by tools/check_r12.py --only K-legends,K-fill instead of check_r11. Steps as r11_post:
  1. every zone filled; R8's digest of copper, zones, fills, pads and footprint positions taken;
  2. board silkscreen deleted, every footprint field hidden, the part-number fields moved to F.Fab, hidden (AGENTS §3);
  3. the table applied (terminal / port pin legends, connector words, J2's SWD rows, J122's harness note, the revision
     M3-ASSY-R12 on B.Silkscreen, pin-1 dots, designators at 1.0 mm / 0.15 mm or hidden on the Fab layer, one Fab
     ${REFERENCE} per footprint); title-block revision M3-ASSY-R12;
  4. every zone filled again, which must reproduce step 1's digest;
  5. the contract (r11_post.contract: ink boxes, sizes, 0.15 mm to mask openings, pin-1 ownership, support hardware),
     then check_r12 K-legends and K-fill on the saved board. R12 has no open rows: any K-legends finding fails the
     stage (D-R12-80; check_r12 has no optional-legend exemptions, D-R12-29 ... -31).
Deterministic (fixed KIID seed, integer nanometre table): a rebuild reproduces the board byte for byte.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r10  # noqa: E402
import r10_post as P  # noqa: E402
import r11_post as base  # noqa: E402
import r5_post as silk  # noqa: E402
import r8_post  # noqa: E402
import r9_post  # noqa: E402

REV = 'M3-ASSY-R12'
KIID_SEED = 12120
TABLE = ROOT / 'm3_design/r12_legends.tsv'
GATE_DATA = ROOT / 'm3_design/r12/design/r12_gate_data.json'
BOARD = ROOT / 'm3_design/r12/m3.kicad_pcb'


def r12(**extra):
    """r11_post's module constants switched to R12's for the duration of a call."""
    return check_r10.patched(base, REV=REV, TABLE=TABLE, GATE_DATA=GATE_DATA, **extra)


def supports(b=None):
    """The D-R12-24 support centres from the gate data (check_r12 M-3)."""
    return [tuple(c) for c in json.loads(GATE_DATA.read_text())['supports']]


table_rows, write_table, read_table = base.table_rows, base.write_table, base.read_table


def gate(board, report):
    """tools/check_r12.py --only K-legends,K-fill on the saved board: every finding fails the stage."""
    out = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'tools/check_r12.py'), str(board),
                          '--only', 'K-legends,K-fill', '--report', str(report)], capture_output=True, text=True,
                         env=dict(os.environ, PYTHONUNBUFFERED='1'))
    data = json.loads(Path(report).read_text())
    problems = [f'{rid}: {i}' for rid in ('K-legends', 'K-fill') for i in data['rules'][rid]['issues']]
    if out.returncode and not problems:
        problems.append(f'check_r12 exit {out.returncode}: {out.stdout[-400:]} {out.stderr[-400:]}')
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', type=Path, default=BOARD)
    ap.add_argument('--table', type=Path, default=TABLE)
    ap.add_argument('--report', type=Path, help='write the evidence (JSON)')
    args = ap.parse_args()
    board = args.board.resolve()
    rows = read_table(args.table)
    if any(r['kind'] == 'open' for r in rows):
        raise SystemExit('r12_post: the legend table has open rows; R12 allows none (D-R12-80)')
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    b = pcbnew.LoadBoard(str(board))
    if any(isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in P.SILKS for d in b.GetDrawings()):
        raise SystemExit('r12_post runs once, on the routed board: this board already carries silkscreen text')
    silk.W, silk.L = r9_post.outline(b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    before = r8_post.fixed_digest(b)
    with r12(), check_r10.patched(P, supports=supports):
        hidden = base.apply(b, rows)
        assert r8_post.fixed_digest(b) == before, 'r12_post changed copper, a zone, a pad or a footprint position'
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        assert r8_post.fixed_digest(b) == before, 'the final zone fill differs from the first'
        issues, notes = base.contract(b, rows)
    if issues:
        raise SystemExit('r12_post legend contract: ' + '; '.join(issues))
    assert pcbnew.SaveBoard(str(board), b, True), 'save failed'
    b = pcbnew.LoadBoard(str(board))
    assert r8_post.fixed_digest(b) == before, 'the saved board differs in copper, zones, pads or footprint positions'
    with tempfile.TemporaryDirectory() as tmp:
        problems = gate(board, Path(tmp) / 'k.json')
    if problems:
        raise SystemExit('r12_post: check_r12 K-legends / K-fill FAIL:\n' + '\n'.join(problems))
    shown = sum(1 for f in b.GetFootprints() if f.Reference().IsVisible())
    on_bottom = sorted(f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible()
                       and f.Reference().GetLayer() == pcbnew.B_SilkS)
    legends = [r['name'] for r in rows if r['kind'] == 'text']
    print(f'r12_post: saved {board.name}; {len(legends)} legends, {shown} designators shown ({len(on_bottom)} on the '
          f'bottom under their part), {len(hidden)} hidden (Fab only): {" ".join(sorted(hidden))}')
    print('r12_post: copper, zones, pads and footprint positions unchanged; zones filled; K-fill and K-legends OK')
    for i in notes:
        print(f'  NOTE (footprint library graphics, not drawn here): {i}')
    if args.report:
        args.report.write_text(json.dumps(dict(revision=REV, legends=legends, designators_shown=shown,
                                               designators_on_bottom=on_bottom, hidden_references=hidden,
                                               footprint_graphics_notes=notes, digest=before), indent=1) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
