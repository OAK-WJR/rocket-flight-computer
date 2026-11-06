#!/usr/bin/env python3
"""Check a routing fragment (r12_routes.tsv columns: kind net layer width x0 y0 x1 y1) against its zone.

usage: python3 zone_guard.py zones.json ZONE FRAGMENT.tsv
Every track end and via must lie inside the zone polygon, or inside a strip the zone owns on that track's layer
(a via must lie inside a polygon or strip valid for every layer it touches: F, In1, In2, B). Points exactly on a
border are allowed (hand-off points). Exit 1 with a list of offending rows.
"""
import json, sys


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


def ok(Z, zone, layer, x, y):
    owns_poly = inside(Z['zones'][zone]['polygon'], x, y)
    for s in Z['strips']:
        x0, y0, x1, y1 = s['rect']
        if x0 - 1e-6 <= x <= x1 + 1e-6 and y0 - 1e-6 <= y <= y1 + 1e-6 and s['layer'] == layer:
            on_border = min(abs(x - x0), abs(x - x1), abs(y - y0), abs(y - y1)) <= 1e-6
            # D-R12-96: a point on a strip's border is a hand-off point: it belongs to the strip owner and to the zone
            # whose polygon holds it
            return s['owner'] == zone or (on_border and owns_poly)
    return owns_poly


def main(zfile, zone, frag):
    Z = json.load(open(zfile)); bad = []
    for n, line in enumerate(open(frag), 1):
        if line.startswith(('#', 'kind')) or not line.strip():
            continue
        r = line.rstrip('\n').split('\t')
        if r[0] == 'track':
            for x, y in ((float(r[4]), float(r[5])), (float(r[6]), float(r[7]))):
                if not ok(Z, zone, r[2], x, y):
                    bad.append((n, line.strip()))
        elif r[0] == 'via':
            x, y = float(r[4]), float(r[5])
            if not all(ok(Z, zone, L, x, y) for L in ('F', 'In1', 'In2', 'B')):
                bad.append((n, line.strip()))
    for b in bad:
        print('outside zone:', *b)
    print(f'{zone}: {len(bad)} rows outside the zone')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main(*sys.argv[1:4])
