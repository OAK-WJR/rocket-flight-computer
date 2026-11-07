#!/usr/bin/env python3
"""Check a routing fragment (r12_routes.tsv columns: kind net layer width x0 y0 x1 y1) against its zone.

usage: python3 zone_guard.py zones.json ZONE FRAGMENT.tsv [BOARD.kicad_pcb]
Every track end and via must lie inside the zone polygon, or inside a strip the zone owns on that track's layer
(a via must lie inside a polygon or strip valid for every layer it touches: F, In1, In2, B). Points exactly on a
border are allowed (hand-off points). Exit 1 with a list of offending rows.
R12F4-TRI-08: every point must also lie inside the board outline, the bounding box of BOARD's Edge.Cuts segments and
rectangles (default: m3_design/r12/m3.kicad_pcb; support circles excluded, as export_geom.py), and the zone's polygon
must not extend beyond it (W5 ended at y 100 on the 90 mm board).
"""
import json, re, sys
from pathlib import Path

BOARD = Path(__file__).resolve().parents[2] / 'r12/m3.kicad_pcb'
# a gr_line / gr_rect on Edge.Cuts: its start and end, with no other graphic item between them and the layer
EDGE = re.compile(r'\(gr_(?:line|rect)\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)'
                  r'(?:(?!\(gr_).)*?\(layer "Edge\.Cuts"\)', re.S)


def outline(board=BOARD):
    """(x0, y0, x1, y1): the bounding box of the board's Edge.Cuts segments and rectangles, read from the file text."""
    xs, ys = [], []
    for m in EDGE.finditer(Path(board).read_text()):
        x0, y0, x1, y1 = map(float, m.groups())
        xs += [x0, x1]
        ys += [y0, y1]
    if not xs:
        raise SystemExit(f'zone_guard: no Edge.Cuts segment or rectangle in {board}')
    return min(xs), min(ys), max(xs), max(ys)


def on_board(box, x, y, eps=1e-6):
    return box[0] - eps <= x <= box[2] + eps and box[1] - eps <= y <= box[3] + eps


def inside(poly, x, y, eps=1e-6):
    n = len(poly); c = False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        # on edge
        if min(x1, x2) - eps <= x <= max(x1, x2) + eps and min(y1, y2) - eps <= y <= max(y1, y2) + eps:
            if abs((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) < eps * max(1, abs(x2 - x1) + abs(y2 - y1)):
                return True
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def ok(Z, zone, layer, x, y, box=None):
    if box is not None and not on_board(box, x, y):
        return False
    owns_poly = inside(Z['zones'][zone]['polygon'], x, y)
    for s in Z['strips']:
        x0, y0, x1, y1 = s['rect']
        if x0 - 1e-6 <= x <= x1 + 1e-6 and y0 - 1e-6 <= y <= y1 + 1e-6 and s['layer'] == layer:
            on_border = min(abs(x - x0), abs(x - x1), abs(y - y0), abs(y - y1)) <= 1e-6
            # D-R12-96: a point on a strip's border is a hand-off point: it belongs to the strip owner and to the zone
            # whose polygon holds it
            return s['owner'] == zone or (on_border and owns_poly)
    return owns_poly


def polygon_issues(Z, zone, box):
    """Zone polygon vertices outside the board outline (R12F4-TRI-08)."""
    return [(x, y) for x, y in Z['zones'][zone]['polygon'] if not on_board(box, x, y)]


def check(Z, zone, rows, box):
    """[(line number, row)] of fragment rows outside the zone or the board, one entry per distinct row (R12F6-TRI-17: a
    track with both ends outside was listed, and counted, twice); rows are the fragment's text lines."""
    bad = []
    for n, line in enumerate(rows, 1):
        if line.startswith(('#', 'kind')) or not line.strip():
            continue
        r = line.rstrip('\n').split('\t')
        if r[0] == 'track':
            if not all(ok(Z, zone, r[2], x, y, box) for x, y in ((float(r[4]), float(r[5])), (float(r[6]), float(r[7])))):
                bad.append((n, line.strip()))
        elif r[0] == 'via':
            x, y = float(r[4]), float(r[5])
            if not all(ok(Z, zone, L, x, y, box) for L in ('F', 'In1', 'In2', 'B')):
                bad.append((n, line.strip()))
    return bad


def main(zfile, zone, frag, board=BOARD):
    Z = json.load(open(zfile))
    box = outline(board)
    off = polygon_issues(Z, zone, box)
    for x, y in off:
        print(f'zone polygon vertex outside the board outline {box}: ({x:g}, {y:g})')
    bad = check(Z, zone, open(frag).readlines(), box)
    for b in bad:
        print('outside zone:', *b)
    print(f'{zone}: {len(bad)} rows outside the zone')
    sys.exit(1 if bad or off else 0)


if __name__ == '__main__':
    main(*sys.argv[1:5])
