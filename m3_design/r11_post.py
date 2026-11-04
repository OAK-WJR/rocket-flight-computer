#!/usr/bin/env python3
"""R11 post stage (M3-ASSY-R11, r11_plan.md section 4 stage D; D-R11-64 ... D-R11-66): silkscreen, designators, Fab
references, part-number fields, the title block and the saved zone fill, from the frozen table m3_design/r11_legends.tsv.
No search (D-R11-07): m3_design/r11_legends_aid.py drafted the table once; this stage only applies and checks it.

usage: <KiCad python3> -I -B m3_design/r11_post.py [--board m3_design/r11/m3.kicad_pcb] [--report out.json]
       [--table m3_design/r11_legends.tsv]

Steps (AGENTS.md section 3 silkscreen rules):
  1. every zone filled (the routing families save them unfilled); R8's digest of copper, zones, fills, pads and
     footprint positions is taken;
  2. every board-level silkscreen item deleted and every footprint field hidden; the part-number fields (LCSC,
     LCSC Part, Manufacturer, Manufacturer Part, KiLib_Generator) moved to the Fab layer of their part's face, hidden;
  3. the table applied: board texts (terminal pin legends, connector words, J122's harness note, J2's SWD rows, the
     revision M3-ASSY-R11 on B.Silkscreen) and pin-1 dots at their recorded positions; every designator at its
     recorded face / position / angle at 1.0 mm (0.15 mm stroke), or hidden (kept on the Fab layer: the table's
     'hidden' rows, listed in the report and in m3_design/r11/design/stageD.md); one Fab ${REFERENCE} per footprint at
     its recorded size and position;
  4. the title-block revision M3-ASSY-R11; every zone filled again, which must reproduce step 1's digest;
  5. the contract, fail closed: every applied item's ink box equals the table's (0.002 mm), texts and designators
     >= 1.0 mm / 0.15 mm, r10_post's silkscreen-to-mask-opening test (0.15 mm) on everything this stage draws (a
     footprint's own library graphics near another part's opening is printed as a NOTE for the placement lane), pin-1
     mark ownership and support-hardware tests, then, on the saved board, tools/check_r11.py --only K-legends,K-fill:
     K-fill clean and K-legends reporting exactly the table's 'open' rows, each a legend or designator K-legends
     requires for which the aid found no legal spot on this board (D-R11-66). Those stay K-legends failures in
     tools/check.sh; the stage fails on any other finding and on an open row K-legends no longer reports.
Deterministic (fixed KIID seed, integer nanometre table): a rebuild reproduces the board byte for byte.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r10  # noqa: E402
import r10_post as P  # noqa: E402
import r5_post as silk  # noqa: E402
import r8_post  # noqa: E402
import r9_post  # noqa: E402

REV = 'M3-ASSY-R11'
KIID_SEED = 11120               # r11 families use their own seeds; the post stage 11120
TABLE = ROOT / 'm3_design/r11_legends.tsv'
GATE_DATA = ROOT / 'm3_design/r11/design/r11_gate_data.json'
PART_FIELDS = ('LCSC', 'LCSC Part', 'Manufacturer', 'Manufacturer Part', 'KiLib_Generator')
COLUMNS = ('kind', 'name', 'layer', 'x_nm', 'y_nm', 'angle', 'h_nm', 'w_nm', 'stroke_nm', 'ink_x0', 'ink_y0', 'ink_x1',
           'ink_y1')
INK_TOL = 0.002                 # mm


def supports(b=None):
    """The D-R11-10 support centres pinned in the gate data (check_r11 M-3)."""
    return [tuple(c) for c in json.loads(GATE_DATA.read_text())['supports']]


def ink(item):
    return tuple(round(v, 4) for v in silk.ink(item))


def _num(v):
    return int(round(v))


def table_rows(b):
    """The silkscreen, designator and Fab-reference state of board b as table rows (integer nanometres)."""
    rows = []
    for d in sorted(b.GetDrawings(), key=lambda d: (d.GetLayer(), d.GetPosition().x, d.GetPosition().y)):
        if d.GetLayer() not in P.SILKS:
            continue
        layer = b.GetLayerName(d.GetLayer())
        if isinstance(d, pcbnew.PCB_TEXT):
            rows.append(('text', d.GetText(), layer, d.GetPosition().x, d.GetPosition().y, d.GetTextAngleDegrees(),
                         d.GetTextHeight(), d.GetTextWidth(), d.GetTextThickness()) + ink(d))
        elif d.GetClass() == 'PCB_SHAPE' and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            rows.append(('dot', '', layer, d.GetStart().x, d.GetStart().y, 0, d.GetEnd().x - d.GetStart().x, 0,
                         d.GetWidth()) + silk.bx(d))
        else:
            raise RuntimeError(f'unexpected board silkscreen item {d.GetClass()}')
    for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        t = f.Reference()
        if t.IsVisible():
            rows.append(('ref', f.GetReference(), b.GetLayerName(t.GetLayer()), t.GetPosition().x, t.GetPosition().y,
                         t.GetTextAngleDegrees(), t.GetTextHeight(), t.GetTextWidth(), t.GetTextThickness()) + ink(t))
        else:
            rows.append(('ref', f.GetReference(), 'hidden', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        t = silk._fab_ref(f)
        rows.append(('fab', f.GetReference(), b.GetLayerName(t.GetLayer()), t.GetPosition().x, t.GetPosition().y,
                     t.GetTextAngleDegrees(), t.GetTextHeight(), t.GetTextWidth(), t.GetTextThickness()) + ink(t))
    return rows


def write_table(path, rows):
    with open(path, 'w', newline='') as fh:
        w = csv.writer(fh, delimiter='\t', lineterminator='\n')
        w.writerow(COLUMNS)
        for r in rows:
            w.writerow([r[0], r[1], r[2]] + [_num(v) for v in r[3:5]] + [f'{float(r[5]):g}']
                       + [_num(v) for v in r[6:9]] + [f'{float(v):.4f}' for v in r[9:13]])


def read_table(path):
    with open(path, newline='') as fh:
        rows = list(csv.DictReader(fh, delimiter='\t'))
    if not rows or tuple(rows[0].keys()) != COLUMNS:
        raise RuntimeError(f'{path}: not an R11 legend table')
    return rows


def _text_attrs(t, r, layer):
    t.SetLayer(layer)
    t.SetMirrored(layer in (pcbnew.B_SilkS, pcbnew.B_Fab))
    t.SetTextSize(pcbnew.VECTOR2I(int(r['w_nm']), int(r['h_nm'])))
    t.SetTextThickness(int(r['stroke_nm']))
    t.SetTextAngleDegrees(float(r['angle']))
    t.SetPosition(pcbnew.VECTOR2I(int(r['x_nm']), int(r['y_nm'])))


def apply(b, rows):
    """Steps 2-4 without the fills; returns the hidden designators."""
    for d in list(b.GetDrawings()):
        if d.GetLayer() in P.SILKS:
            b.Delete(d)
    for f in b.GetFootprints():
        fab = pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab
        for field in f.GetFields():
            field.SetVisible(False)
            if field.GetName() in PART_FIELDS:
                field.SetLayer(fab)
                field.SetMirrored(f.IsFlipped())
    refs = {r['name'] for r in rows if r['kind'] == 'ref'}
    fabs = {r['name'] for r in rows if r['kind'] == 'fab'}
    board_refs = {f.GetReference() for f in b.GetFootprints()}
    if refs != board_refs or fabs != board_refs:
        raise RuntimeError(f'legend table does not cover the board: designators {sorted(refs ^ board_refs)}, '
                           f'Fab {sorted(fabs ^ board_refs)}')
    hidden = []
    for r in rows:
        if r['kind'] == 'text':
            t = pcbnew.PCB_TEXT(b)
            t.SetText(r['name'])
            _text_attrs(t, r, b.GetLayerID(r['layer']))
            b.Add(t)
        elif r['kind'] == 'dot':
            d = pcbnew.PCB_SHAPE(b)
            d.SetShape(pcbnew.SHAPE_T_CIRCLE)
            d.SetLayer(b.GetLayerID(r['layer']))
            d.SetStart(pcbnew.VECTOR2I(int(r['x_nm']), int(r['y_nm'])))
            d.SetEnd(pcbnew.VECTOR2I(int(r['x_nm']) + int(r['h_nm']), int(r['y_nm'])))
            d.SetWidth(int(r['stroke_nm']))
            d.SetFilled(True)
            b.Add(d)
        elif r['kind'] == 'ref':
            f = b.FindFootprintByReference(r['name'])
            t = f.Reference()
            if r['layer'] == 'hidden':
                t.SetVisible(False)
                hidden.append(r['name'])
                continue
            _text_attrs(t, r, b.GetLayerID(r['layer']))
            t.SetVisible(True)
        elif r['kind'] == 'fab':
            f = b.FindFootprintByReference(r['name'])
            mine = [g for g in f.GraphicalItems() if isinstance(g, pcbnew.PCB_TEXT) and g.GetText() == '${REFERENCE}']
            for g in mine[1:]:
                f.Remove(g)
            if mine:
                t = mine[0]
            else:
                t = pcbnew.PCB_TEXT(f)
                t.SetText('${REFERENCE}')
                f.Add(t)
            t.SetKeepUpright(False)
            t.SetVisible(True)
            _text_attrs(t, r, b.GetLayerID(r['layer']))
        elif r['kind'] != 'open':
            raise RuntimeError(f'unknown legend table row kind {r["kind"]!r}')
    b.GetTitleBlock().SetRevision(REV)
    return hidden


def contract(b, rows):
    """Step 5's in-process tests; returns the issues."""
    issues, notes = [], []
    got = {}
    for r in table_rows(b):
        got.setdefault((r[0], r[1], r[2]), []).append([float(v) for v in r[9:13]])
    want = {}
    for r in rows:
        if r['kind'] not in ('dot', 'open'):
            want.setdefault((r['kind'], r['name'], r['layer']), []).append(
                [float(r[k]) for k in ('ink_x0', 'ink_y0', 'ink_x1', 'ink_y1')])
    for key in sorted(set(got) | set(want)):
        if key[0] == 'dot':
            continue
        a, c = sorted(got.get(key, [])), sorted(want.get(key, []))
        if len(a) != len(c) or any(max(abs(u - v) for u, v in zip(x, y)) > INK_TOL for x, y in zip(a, c)):
            issues.append(f'{key}: applied ink {a} differs from the table {c}')
    small = [f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible()
             and (silk.mm(f.Reference().GetTextHeight()) < 1.0 - 1e-6
                  or silk.mm(f.Reference().GetTextThickness()) < 0.15 - 1e-6)]
    issues += [f'designator {r} below 1.0 mm / 0.15 mm (REQUIREMENTS M2)' for r in small]
    texts = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in P.SILKS
             and (silk.mm(d.GetTextHeight()) < 1.0 - 1e-6 or silk.mm(d.GetTextThickness()) < 0.15 - 1e-6)]
    issues += [f'legend {d.GetText()!r} below 1.0 mm / 0.15 mm (REQUIREMENTS M2)' for d in texts]
    # JLC's 0.15 mm pad-to-silkscreen (R3-MFG-02) on everything this stage draws (board items, designators); a
    # footprint's own library graphics near another part's opening is a placement finding, reported (D-R11-66)
    drawn = {f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible()}
    for gap, who, what, pad in P.silk_to_openings(b):
        line = f'silkscreen {what!r} of {who} {gap} mm from {pad} opening (< {P.SILK_PAD})'
        if who == 'board' or (who in drawn and what == who):
            issues.append(line)
        else:
            notes.append(line)
    bad, _ = P.pin1_marks(b)
    issues += [f'pin-1 mark of {o} at ({x}, {y}) only {m} mm nearer its pad 1' for o, x, y, m in bad]
    issues += [f'{name!r} inside a support hardware circle' for name in P.in_hardware(b)]
    return issues, notes


def open_findings(rows):
    """The K-legends findings each 'open' row stands for: a legend K-legends requires that has no legal spot on this
    board (the aid's search found none; D-R11-66). They stay K-legends failures in tools/check.sh."""
    out = []
    for r in rows:
        if r['kind'] != 'open':
            continue
        text, what = r['name'], r['layer']
        if what == 'pin':
            ref, pin = text.split(' ', 1)
            out.append(f'{ref}.{pin.split(":")[0]}: 0 legends "{pin}" nearest it, expected one')
        elif what == 'word':
            out.append(f"{check_r10.WORD_LEGENDS_R10[text]}: word legend {text!r} appears 0 times on silkscreen, "
                       'expected once')
        elif what == 'port':
            ref, pin = text.split(' ', 1)
            n, name = pin.split(':')
            out.append(f'{ref}.{n}: silkscreen must identify {name} exactly once (R10 port table)')
        elif what == 'ref':
            out.append(f'K-legends: {text}: reference designator hidden (a safety / connector part must show it)')
        elif what == 'note':
            out.append(f'J122: silkscreen must identify {text!r} exactly once')
        else:
            raise RuntimeError(f'unknown open legend kind {what!r}')
    return out


def gate(board, rows, report):
    """tools/check_r11.py --only K-legends,K-fill on the saved board: K-fill OK, and K-legends' findings exactly the
    table's open rows (any other finding, or an open row K-legends no longer reports, fails the stage)."""
    out = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'tools/check_r11.py'), str(board),
                          '--only', 'K-legends,K-fill', '--report', str(report)], capture_output=True, text=True,
                         env=dict(os.environ, PYTHONUNBUFFERED='1'))
    data = json.loads(Path(report).read_text())
    expected = set(open_findings(rows))
    found = set(data['rules']['K-legends']['issues'])
    problems = [f'K-fill: {i}' for i in data['rules']['K-fill']['issues']]
    problems += [f'K-legends: {i}' for i in sorted(found - expected)]
    problems += [f'stale open legend row (K-legends no longer reports it): {i}' for i in sorted(expected - found)]
    if out.returncode and not data['rules']['K-legends']['issues'] and not data['rules']['K-fill']['issues']:
        problems.append(f'check_r11 exit {out.returncode}')
    return problems, sorted(expected)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', type=Path, default=ROOT / 'm3_design/r11/m3.kicad_pcb')
    ap.add_argument('--table', type=Path, default=TABLE)
    ap.add_argument('--report', type=Path, help='write the evidence (JSON)')
    args = ap.parse_args()
    board = args.board.resolve()
    rows = read_table(args.table)
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    b = pcbnew.LoadBoard(str(board))
    if any(isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in P.SILKS for d in b.GetDrawings()):
        raise SystemExit('r11_post runs once, on the routed board: this board already carries silkscreen text')
    silk.W, silk.L = r9_post.outline(b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    before = r8_post.fixed_digest(b)
    with check_r10.patched(P, supports=supports):
        hidden = apply(b, rows)
        assert r8_post.fixed_digest(b) == before, 'r11_post changed copper, a zone, a pad or a footprint position'
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        assert r8_post.fixed_digest(b) == before, 'the final zone fill differs from the first'
        issues, notes = contract(b, rows)
    if issues:
        raise SystemExit('r11_post legend contract: ' + '; '.join(issues))
    assert pcbnew.SaveBoard(str(board), b, True), 'save failed'
    b = pcbnew.LoadBoard(str(board))
    assert r8_post.fixed_digest(b) == before, 'the saved board differs in copper, zones, pads or footprint positions'
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        problems, still_open = gate(board, rows, Path(tmp) / 'k.json')
    if problems:
        raise SystemExit('r11_post: check_r11 K-legends / K-fill FAIL:\n' + '\n'.join(problems))
    shown = sum(1 for f in b.GetFootprints() if f.Reference().IsVisible())
    under = sorted(f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible() and not f.IsFlipped()
                   and f.Reference().GetLayer() == pcbnew.B_SilkS)
    legends = [r['name'] for r in rows if r['kind'] == 'text']
    print(f'r11_post: saved {board.name}; {len(legends)} legends, {shown} designators shown ({len(under)} top parts\' '
          f'under their part on the bottom), {len(hidden)} hidden (Fab only): {" ".join(sorted(hidden))}')
    print('r11_post: copper, zones, pads and footprint positions unchanged; zones filled; K-fill OK; K-legends: only '
          f'the table\'s {len(still_open)} open rows')
    for i in notes:
        print(f'  NOTE (footprint library graphics, not drawn here): {i}')
    for i in still_open:
        print(f'  OPEN (no legal spot, K-legends fails in tools/check.sh): {i}')
    if args.report:
        args.report.write_text(json.dumps(dict(revision=REV, legends=legends, designators_shown=shown,
                                               top_designators_under_part_on_bottom=under, hidden_references=hidden,
                                               open_legends=still_open, footprint_graphics_notes=notes,
                                               digest=before), indent=1) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
