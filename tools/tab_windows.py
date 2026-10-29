#!/usr/bin/env python3
"""Panel-tab windows on the long edges (R9 gate T-1; docs/ORDERING.md section 3; r9_plan.md section 1, from plan C).

usage: <KiCad python3> -I tools/tab_windows.py BOARD.kicad_pcb [--json OUT]       exit 0 = the tab rule holds

A 5 mm tab (JLC's minimum width) at y0..y0 + 5 on the west (x = 0) or east (x = W) edge is legal when every
courtyard and pad box clears it by TAB_PART (1.5 mm, JLC's mouse-bite clearance), every capacitor, R166, LED2 and both
RF modules by TAB_SOFT (5 mm, the house stress margin), every connector by TAB_CONN (2 mm, JLC) and every Edge.Cuts
hole by TAB_HOLE (1.5 mm); the aft edge carries no tab (the SMA jacks overhang it), so the jacks are left out of the
search, and the board's own outline sets W and L (r8_place_check.tab_windows with R8's fixed L and W removed).
The rule (survey_constraints.md section 3): each long edge admits a legal tab wholly in the aft third of the length
and one wholly in the forward third, so rails can be held at both ends. Reported, not gated: the In2 net under each
window's inner 0.5-3 mm (ORDERING: keep tabs off In2 regions other than GND where possible, R8P3-POWER-05).
"""
import argparse
import json
import math
from pathlib import Path
import re
import sys

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_r8 as C8                                           # noqa: E402
from fit_check import board_geometry                            # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
TAB_LEN, TAB_PART, TAB_SOFT, TAB_CONN, TAB_HOLE = 5.0, 1.5, 5.0, 2.0, 1.5
TAB_SOFT_REFS = re.compile(r'^(C\d+|R166|LED2|U30|U31)$')
JACK_FP = 'M3_SMA_KH_KE8_EDGE'
STEP = 0.25
END_SHARE = 1.0 / 3.0


def _box(shape):
    b = shape.BBox()
    return mm(b.GetLeft()), mm(b.GetTop()), mm(b.GetRight()), mm(b.GetBottom())


def obstacles(board):
    out = []
    for f in board.GetFootprints():
        if str(f.GetFPID().GetLibItemName()) == JACK_FP:
            continue
        ref = f.GetReference()
        need = TAB_SOFT if TAB_SOFT_REFS.match(ref) else TAB_CONN if ref.startswith('J') else TAB_PART
        out.append((ref, _box(C8.courtyard(f)), need))
        for p in f.Pads():
            b = p.GetBoundingBox()
            out.append((ref, (mm(b.GetLeft()), mm(b.GetTop()), mm(b.GetRight()), mm(b.GetBottom())), need))
    return out


def windows(board):
    """{'west': [(start, end)], 'east': [...]}: the legal spans (a tab fits anywhere inside each)."""
    holes = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    holes = [((mm(d.GetCenter().x), mm(d.GetCenter().y)), mm(d.GetRadius())) for d in holes]
    _, (x0, y0, x1, y1) = board_geometry(board)
    obs = obstacles(board)
    out = {}
    for edge, x in (('west', x0), ('east', x1)):
        ok, y = [], y0 + 0.5
        while y + TAB_LEN <= y1 - 0.5 + 1e-9:
            a, b = y, y + TAB_LEN
            good = True
            for ref, bb, need in obs:
                dx = max(bb[0] - x, x - bb[2], 0)
                dy = max(bb[1] - b, a - bb[3], 0)
                if math.hypot(dx, dy) < need - 1e-6:
                    good = False
                    break
            if good:
                for (cx, cy), r in holes:
                    dx = max(abs(cx - x) - r, 0)
                    dy = max(cy - r - b, a - (cy + r), 0)
                    if math.hypot(dx, dy) < TAB_HOLE - 1e-6:
                        good = False
                        break
            if good:
                ok.append(round(y, 2))
            y = round(y + STEP, 2)
        spans = []
        for s in ok:
            if spans and s - spans[-1][1] <= STEP + 0.01:
                spans[-1][1] = s
            else:
                spans.append([s, s])
        out[edge] = [(a, round(b + TAB_LEN, 2)) for a, b in spans]
    return out


def in2_under(board, edge_x, a, b):
    """Nets of the In2 fills under the tab's inner strip (0.5-3 mm from the edge)."""
    nets = set()
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.In2_Cu) or not z.HasFilledPolysForLayer(pcbnew.In2_Cu):
            continue
        for y in (a + 0.5, (a + b) / 2, b - 0.5):
            for d in (0.6, 1.5, 3.0):
                x = edge_x + d if edge_x < 1 else edge_x - d
                if z.HitTestFilledArea(pcbnew.In2_Cu, pcbnew.VECTOR2I(MM(x), MM(y))):
                    nets.add(z.GetNetname())
    return sorted(nets)


def check(board):
    """(issues, evidence) of the tab rule."""
    _, (x0, y0, x1, y1) = board_geometry(board)
    length = y1 - y0
    wins = windows(board)
    issues, ev = [], dict(windows=wins, length=round(length, 3), in2_under={})
    for edge, spans in wins.items():
        aft = [s for s in spans if s[0] <= y0 + END_SHARE * length - TAB_LEN + 1e-6]
        fwd = [s for s in spans if s[1] >= y1 - END_SHARE * length + TAB_LEN - 1e-6]
        if not aft:
            issues.append(f'tab windows: no legal 5 mm tab on the {edge} edge within the aft third (y <= '
                          f'{y0 + END_SHARE * length:.1f}); spans {spans}')
        if not fwd:
            issues.append(f'tab windows: no legal 5 mm tab on the {edge} edge within the forward third (y >= '
                          f'{y1 - END_SHARE * length:.1f}); spans {spans}')
        ex = x0 if edge == 'west' else x1
        for a, b in spans:
            ev['in2_under'][f'{edge} {a}-{b}'] = in2_under(board, ex, a, min(b, a + TAB_LEN))
    return issues, ev


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', type=Path)
    ap.add_argument('--json', type=Path)
    a = ap.parse_args()
    issues, ev = check(pcbnew.LoadBoard(str(a.board.resolve())))
    for edge, spans in ev['windows'].items():
        print(f'{edge}: ' + ', '.join(f'{s}-{e}' for s, e in spans))
    for k, v in ev['in2_under'].items():
        print(f'  In2 under {k}: {", ".join(v) or "none"}')
    for i in issues:
        print('FAIL', i)
    print('tab windows:', 'OK' if not issues else f'FAIL ({len(issues)})')
    if a.json:
        a.json.write_text(json.dumps(dict(ev, issues=issues), indent=1) + '\n')
    return 0 if not issues else 1


if __name__ == '__main__':
    raise SystemExit(main())
