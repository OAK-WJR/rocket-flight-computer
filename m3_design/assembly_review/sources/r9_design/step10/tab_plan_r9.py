#!/usr/bin/env python3
"""R9 step 10: the panel-tab plan for docs/ORDERING.md section 3 (R9_DECISIONS D-S10-03), bound to the board SHA-256.

usage: <KiCad python3> -I tab_plan_r9.py BOARD.kicad_pcb OUT.json

Read-only. Every legal 5 mm tab position on the long edges (tools/tab_windows.py's windows and 0.25 mm step: JLC's
1.5 mm part / pad clearance, the house 5 mm capacitor / R166 / LED2 / module margin, JLC's 2 mm connector and 1.5 mm hole
clearances; the aft edge carries none, the SMA jacks overhang it) is scored by:
  - its clearance to the nearest part or pad, capacitor-class item, connector and hole, and each clearance less its rule
    (the margin);
  - the nets of the copper on every layer within the tab's inner band (0.5-3 mm from the edge: fills sampled at three
    depths x three points along the tab, and any track, via or pad reaching into the band);
  - its distance to the PYRO_BLOCK rule area.
One tab is chosen in the aft third and one in the forward third of each long edge (T-1's four slots), by:
  1. GND only on every copper layer of the band (R8P3-POWER-05: a crack that joins a live region to a neighbouring layer
     is a short);
  2. >= 5 mm (the house stress margin, TAB_SOFT) from the PYRO_BLOCK area: no depaneling stress beside the CH1 column,
     where a flex-cracked MLCC is a drain-to-GND (C128) or gate (C126) short;
  3. the largest smallest margin; a tie goes to the position nearer the board end (rail support).
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import tab_windows as TW  # noqa: E402
from fit_check import board_geometry  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
BAND = (0.5, 3.0)
PYRO_MARGIN = TW.TAB_SOFT
CU = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def segs_dist(a0, a1, b0, b1):
    return min(seg_dist(a0, b0, b1), seg_dist(a1, b0, b1), seg_dist(b0, a0, a1), seg_dist(b1, a0, a1))


def block_outline(board):
    z = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK'][0]
    poly = z.Outline().Outline(0)
    return [(mm(poly.CPoint(i).x), mm(poly.CPoint(i).y)) for i in range(poly.PointCount())]


def band_copper(board, x_edge, a, b):
    """{layer: sorted nets} of the copper within the tab's inner band."""
    inward = 1 if x_edge < 1 else -1
    out = {board.GetLayerName(lay): set() for lay in CU}
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for lay in CU:
            if not z.IsOnLayer(lay) or not z.HasFilledPolysForLayer(lay):
                continue
            for y in (a + 0.5, (a + b) / 2, b - 0.5):
                for d in (BAND[0] + 0.1, 1.5, BAND[1]):
                    if z.HitTestFilledArea(lay, pcbnew.VECTOR2I(MM(x_edge + inward * d), MM(y))):
                        out[board.GetLayerName(lay)].add(z.GetNetname())
    xs = sorted((x_edge + inward * BAND[0], x_edge + inward * BAND[1]))
    box = pcbnew.BOX2I(pcbnew.VECTOR2I(MM(xs[0]), MM(a)), pcbnew.VECTOR2I(MM(xs[1] - xs[0]), MM(b - a)))
    items = list(board.GetTracks()) + [p for f in board.GetFootprints() for p in f.Pads()]
    for it in items:
        if not it.GetBoundingBox().Intersects(box):
            continue
        for lay in CU:
            if it.IsOnLayer(lay):
                out[board.GetLayerName(lay)].add(it.GetNetname())
    return {k: sorted(v) for k, v in out.items()}


def score(board, obs, holes, outline, edge, x_edge, a):
    b = a + TW.TAB_LEN
    near = {}
    for ref, bb, need in obs:
        dx = max(bb[0] - x_edge, x_edge - bb[2], 0)
        dy = max(bb[1] - b, a - bb[3], 0)
        d = math.hypot(dx, dy)
        cls = 'soft' if TW.TAB_SOFT_REFS.match(ref) else 'connector' if ref.startswith('J') else 'part'
        for k in ('part_or_pad', cls):
            if k not in near or d < near[k][0]:
                near[k] = (d, ref)
    hole = min((math.hypot(max(abs(cx - x_edge) - r, 0), max(cy - r - b, a - (cy + r), 0)), (cx, cy))
               for (cx, cy), r in holes)
    rules = dict(part_or_pad=TW.TAB_PART, soft=TW.TAB_SOFT, connector=TW.TAB_CONN)
    margins = {k: round(near[k][0] - rules[k], 3) for k in rules if k in near}
    margins['hole'] = round(hole[0] - TW.TAB_HOLE, 3)
    pyro = min(segs_dist((x_edge, a), (x_edge, b), outline[i], outline[(i + 1) % len(outline)])
               for i in range(len(outline)))
    cu = band_copper(board, x_edge, a, b)
    jacks = {}                                   # tab_windows leaves the overhanging jacks out; report them here
    for f in board.GetFootprints():
        if str(f.GetFPID().GetLibItemName()) == TW.JACK_FP:
            bb = TW._box(TW.C8.courtyard(f))
            dx = max(bb[0] - x_edge, x_edge - bb[2], 0)
            dy = max(bb[1] - b, a - bb[3], 0)
            jacks[f.GetReference()] = round(math.hypot(dx, dy), 3)
    return dict(edge=edge, kicad_y=[round(a, 2), round(b, 2)], gerber_y=[round(-b, 2), round(-a, 2)],
                jack_courtyard_mm=jacks,
                nearest={k: dict(mm=round(v[0], 3), ref=v[1]) for k, v in near.items()},
                nearest_hole=dict(mm=round(hole[0], 3), at=list(hole[1])), margins=margins,
                min_margin=min(margins.values()), pyro_block_mm=round(pyro, 3), band_copper=cu,
                gnd_only=all(v == ['GND'] for v in cu.values()))


def main():
    board_path = Path(sys.argv[1]).resolve()
    out_path = Path(sys.argv[2])
    board = pcbnew.LoadBoard(str(board_path))
    _, (x0, y0, x1, y1) = board_geometry(board)
    length = y1 - y0
    wins = TW.windows(board)
    obs = TW.obstacles(board)
    holes = [((mm(d.GetCenter().x), mm(d.GetCenter().y)), mm(d.GetRadius())) for d in board.GetDrawings()
             if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    outline = block_outline(board)
    slots, chosen, middle = {}, {}, {}
    for edge, x_edge in (('west', x0), ('east', x1)):
        mids = []                                  # legal positions overlapping the middle third: why no mid-span tab
        for s, e in wins[edge]:
            a = s
            while a + TW.TAB_LEN <= e + 1e-9:
                if a + TW.TAB_LEN > y0 + length / 3 and a < y1 - length / 3:
                    mids.append(score(board, obs, holes, outline, edge, x_edge, a))
                a = round(a + TW.STEP, 2)
        middle[edge] = dict(positions=len(mids),
                            max_pyro_block_mm=max((c['pyro_block_mm'] for c in mids), default=None),
                            usable=sum(1 for c in mids if c['gnd_only'] and c['pyro_block_mm'] >= PYRO_MARGIN))
        for third in ('aft', 'forward'):
            cands = []
            for s, e in wins[edge]:
                a = s
                while a + TW.TAB_LEN <= e + 1e-9:
                    b = a + TW.TAB_LEN
                    inside = (b <= y0 + length / 3 + 1e-9) if third == 'aft' else (a >= y1 - length / 3 - 1e-9)
                    if inside:
                        cands.append(score(board, obs, holes, outline, edge, x_edge, a))
                    a = round(a + TW.STEP, 2)
            legal = [c for c in cands if c['gnd_only'] and c['pyro_block_mm'] >= PYRO_MARGIN]
            end = (lambda c: c['kicad_y'][0]) if third == 'aft' else (lambda c: -c['kicad_y'][1])
            legal.sort(key=lambda c: (-c['min_margin'], end(c)))
            key = f'{edge} {third}'
            starts = sorted(c['kicad_y'][0] for c in legal)
            slots[key] = dict(candidates=len(cands), legal=len(legal),
                              legal_starts=[starts[0], starts[-1]] if starts else None,
                              rejected_live_copper=sum(1 for c in cands if not c['gnd_only']),
                              rejected_pyro_block=sum(1 for c in cands if c['gnd_only']
                                                      and c['pyro_block_mm'] < PYRO_MARGIN))
            if legal:
                chosen[key] = legal[0]
    rep = dict(board=board_path.name, board_sha256=hashlib.sha256(board_path.read_bytes()).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               length_mm=round(length, 3), windows=wins, pyro_block_outline=outline,
               rules=dict(length=TW.TAB_LEN, part=TW.TAB_PART, soft=TW.TAB_SOFT, connector=TW.TAB_CONN,
                          hole=TW.TAB_HOLE, band_mm=list(BAND), pyro_block=PYRO_MARGIN),
               slots=slots, chosen=chosen, middle_third=middle, ok=len(chosen) == 4)
    out_path.write_text(json.dumps(rep, indent=1) + '\n')
    for k, c in chosen.items():
        print(f'{k:12s} y {c["kicad_y"][0]:6.2f}-{c["kicad_y"][1]:6.2f}  min margin {c["min_margin"]:.2f}  '
              f'pyro {c["pyro_block_mm"]:.1f}  nearest {c["nearest"]["part_or_pad"]}')
    for k, s in slots.items():
        print(k, s)
    for k, m in middle.items():
        print(f'{k} middle third: {m}')
    print('tab plan:', 'OK (4 slots)' if rep['ok'] else 'FAIL')
    return 0 if rep['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
