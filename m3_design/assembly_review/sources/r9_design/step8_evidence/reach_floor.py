#!/usr/bin/env python3
"""P9 / P10 floor of the R9 stitching (R9_DECISIONS D-S8-16): the survey's reach metric (0.5 mm raster inside the
outline, distance to the nearest GND via or plated GND hole) with every legal via spot of r9_ground_aid.legal (at the
aid's closest spacing, SPACING_ISLAND, from the existing GND vias) used at
once (no spacing between them): the best any stitching under those rules can reach.

usage: <KiCad python3> -I reach_floor.py STEP7_BOARD [--revive] [--grid 0.1]
STEP7_BOARD is the step-7 board (no step-8 copper; the pours are grown here as r9_ground.py grows them). --revive also
lets a via revive a removed GND island (then held by that via alone: the reach stage's case).
"""
import argparse
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'm3_design'))
import r9_ground  # noqa: E402
import r9_ground_aid as A  # noqa: E402


def pctl(vals, q):
    s = sorted(vals)
    k = (len(s) - 1) * q
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', type=Path)
    ap.add_argument('--revive', action='store_true')
    ap.add_argument('--grid', type=float, default=0.1)
    a = ap.parse_args()
    b = pcbnew.LoadBoard(str(a.board))
    r9_ground.grow_pours(b)
    A.refill(b)
    reg = A.legal(b, revive=a.revive, spacing=A.SPACING_ISLAND)
    x0, y0, x1, y1 = A.board_box(b)
    ras = A.rc.Raster((x0 / A.rc.NM, A.STRIP_Y / A.rc.NM, x1 / A.rc.NM, y1 / A.rc.NM), a.grid / A.rc.NM)
    g = ras.fill([reg])
    spots = [tuple(A.mm(v) for v in ras.centre(k)) for k in range(ras.nx * ras.ny) if g[k]]
    near = A.Near(A.gnd_points(b) + spots, cell=1.0)
    d = sorted((near.dist(q), q) for q in A.board_points(b))
    vals = [v for v, _ in d]
    print(f'legal spots {len(spots)} (grid {a.grid} mm, revive {a.revive}); board points {len(d)}')
    print(f'floor P9 (p95) {pctl(vals, 0.95):.2f} mm, P10 (max) {d[-1][0]:.2f} mm at {d[-1][1]}; '
          f'points beyond 3.5 mm {sum(1 for v in vals if v > 3.5)} (p95 <= 3.5 allows {int(0.05 * (len(d) - 1))})')


if __name__ == '__main__':
    main()
