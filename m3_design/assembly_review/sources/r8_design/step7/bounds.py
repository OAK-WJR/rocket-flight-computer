#!/usr/bin/env python3
"""Floors of the GND via distance metrics P9 (p95) and P10 (max) on a board (R8_DECISIONS D64): no GND via placement
can do better than these. Design aid; read-only.

usage: <KiCad python3> -I bounds.py BOARD [--built]   (BOARD with m3.kicad_pro / m3.kicad_dru beside it: the step-6
       board, or with --built the built board, whose r8_ground.tsv items are removed in memory first)

Each board raster point (0.5 mm, survey_metrics' P9 raster) is at least its distance to the nearest place a new GND via
may go, or to an existing GND via or plated GND hole. Two sets of places, sampled on a 0.25 mm grid:
  any    a GND via must join an outer (F.Cu / B.Cu) GND pour fill (else it joins In1 only and dangles), and must not open
         an antipad in RAW_ACT / BAT_IN / ACT_FET_S copper on any layer inside its 7.7 A corridor (tools/run_dc.sh's
         terminal pads + 2 mm; D12). Nothing else is applied: an optimistic floor for any placement.
  rules  the legal spots of make_ground.legal() (D62's rules), every one of them filled.
"""
import math
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_ground as mg  # noqa: E402

MM = pcbnew.FromMM


def corridor_places(b):
    allow = pcbnew.SHAPE_POLY_SET()
    for lid, ps in mg.outer_gnd(b).items():
        allow.BooleanAdd(ps)
    forbid = pcbnew.SHAPE_POLY_SET()
    for net, ends in mg.CORRIDORS.items():
        xs, ys = [], []
        for ref, pins in ends:
            for p in b.FindFootprintByReference(ref).Pads():
                if p.GetNumber() in pins:
                    xs.append(pcbnew.ToMM(p.GetPosition().x))
                    ys.append(pcbnew.ToMM(p.GetPosition().y))
        box = mg.rect(min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2)
        for z in b.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() == net:
                for lid in mg.CU4:
                    if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                        f = mg.fill(z, lid)
                        f.Inflate(MM(mg.VIA[0] / 2 + 0.3), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, mg.ERR)
                        f.BooleanIntersection(box)
                        forbid.BooleanAdd(f)
    allow.BooleanSubtract(forbid)
    return allow


def floor(b, places):
    pts = []
    y = 0.125
    while y < 118:
        x = 0.125
        while x < 46:
            if places.Contains(mg.P(x, y)):
                pts.append((x, y))
            x += 0.25
        y += 0.25
    near = mg.Near(pts + mg.gnd_points(b))
    outline = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(outline, False)
    d = []
    y = 0.25
    while y < 118:
        x = 0.25
        while x < 46:
            if outline.Contains(mg.P(x, y)):
                d.append((near.dist((x, y)), x, y))
            x += 0.5
        y += 0.5
    v = sorted(t[0] for t in d)
    worst = max(d)
    return dict(p95=round(v[int(0.95 * (len(v) - 1))], 2), max=round(worst[0], 2), max_at=worst[1:],
                share_over_3_5=round(sum(1 for t in v if t > 3.5) / len(v), 4))


def main():
    b = pcbnew.LoadBoard(str(Path(sys.argv[1]).resolve()))
    if '--built' in sys.argv[2:]:
        mg.strip_built(b, mg.read())
    print('any  ', floor(b, corridor_places(b)))
    print('rules', floor(b, mg.legal(b)))


if __name__ == '__main__':
    main()
