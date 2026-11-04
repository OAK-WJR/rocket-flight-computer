#!/usr/bin/env python3
"""R12 drafting aid (D-R12-45, not run by the build): prune.py GEO.json IN.tsv OUT.tsv [--loops]: drop dead copper of non-plane nets (track ends touching nothing, vias with copper on
fewer than two layers, repeated until stable). Pads: F-side SMD pads (layer F) and PTH pads (all layers).
With --loops it first removes, per net, the longest segments whose removal leaves every pad group joined (track_loop).
Joints count only at a node, a centre line, a via ring or inside a pad (no overlap-only joint is created)."""
import sys, json, math, csv
PLANE = {'GND', '3V3', '3V3A', 'RAW_PROTECTED', 'PORT_4V8'}
g = json.load(open(sys.argv[1]))
pads = {}
for f in g['fps']:
    for p in f['pads']:
        pads.setdefault(p['net'], []).append(p)
def in_poly(x, y, poly):
    c = False
    for o in poly:
        n = len(o)
        for i in range(n):
            (x1, y1), (x2, y2) = o[i], o[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
    return c
def segd(px, py, a, b):
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)
head, rows = [], []
for l in open(sys.argv[2]):
    l = l.rstrip('\n')
    if l.startswith('#') or l.startswith('kind'): head.append(l); continue
    if l.strip(): rows.append(l.split('\t'))
def on_pad(net, layer, x, y):
    for p in pads.get(net, []):
        if (p['attr'] == 'pth' or layer == 'F') and in_poly(x, y, p['poly']):
            return True
    return False
removed = 0
def comps(net, T, V, P):
    """union-find over the net's tracks (T), vias (V) and pads (P); returns the partition of pads"""
    items = [('t', t) for t in T] + [('v', v) for v in V] + [('p', q) for q in P]
    par = list(range(len(items)))
    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    def u(i, j): par[f(i)] = f(j)
    for i, (ki, a) in enumerate(items):
        for j in range(i + 1, len(items)):
            kj, b = items[j]
            ok = False
            if ki == 't' and kj == 't':
                if a[1] == b[1]:
                    ok = any(segd(e[0], e[1], b[3], b[4]) <= 1e-3 for e in (a[3], a[4])) or \
                         any(segd(e[0], e[1], a[3], a[4]) <= 1e-3 for e in (b[3], b[4]))
            elif ki == 't' and kj == 'v':
                ok = any(math.hypot(e[0] - b[1], e[1] - b[2]) <= 0.225 for e in (a[3], a[4]))
            elif ki == 't' and kj == 'p':
                ok = (b['attr'] == 'pth' or a[1] == 'F') and any(in_poly(e[0], e[1], b['poly']) for e in (a[3], a[4]))
            elif ki == 'v' and kj == 'p':
                ok = in_poly(a[1], a[2], b['poly'])
            if ok: u(i, j)
    n0 = len(T) + len(V)
    groups = {}
    for k in range(len(P)):
        groups.setdefault(f(n0 + k), []).append(k)
    return sorted(tuple(g) for g in groups.values())
if '--loops' in sys.argv:
    for net in sorted({r[1] for r in rows if r[0] == 'track' and r[1] not in PLANE}):
        idx = [i for i, r in enumerate(rows) if r[1] == net]
        P = pads.get(net, [])
        def build(skip):
            T = [(i, rows[i][2], float(rows[i][3]), (float(rows[i][4]), float(rows[i][5])), (float(rows[i][6]), float(rows[i][7])))
                 for i in idx if rows[i][0] == 'track' and i not in skip]
            V = [(i, float(rows[i][4]), float(rows[i][5])) for i in idx if rows[i][0] == 'via' and i not in skip]
            return T, V
        T, V = build(set())
        if len(T) + len(V) > 80:
            continue
        base = comps(net, T, V, P)
        gone = set()
        for t in sorted(T, key=lambda t: -math.hypot(t[3][0] - t[4][0], t[3][1] - t[4][1])):
            T2, V2 = build(gone | {t[0]})
            if comps(net, T2, V2, P) == base:
                gone.add(t[0])
        if gone:
            print('  loop copper removed:', net, len(gone))
            rows = [r for i, r in enumerate(rows) if i not in gone]
            removed += len(gone)
while True:
    tr = [(i, r) for i, r in enumerate(rows) if r[0] == 'track' and r[1] not in PLANE]
    vi = [(i, r) for i, r in enumerate(rows) if r[0] == 'via' and r[1] not in PLANE]
    kill = set()
    bynet = {}
    for i, r in tr: bynet.setdefault(r[1], []).append(i)
    vbynet = {}
    for i, r in vi: vbynet.setdefault(r[1], []).append(i)
    for net in set(bynet) | set(vbynet):
        T = [(i, rows[i][2], float(rows[i][3]), (float(rows[i][4]), float(rows[i][5])), (float(rows[i][6]), float(rows[i][7]))) for i in bynet.get(net, [])]
        V = [(i, float(rows[i][4]), float(rows[i][5])) for i in vbynet.get(net, [])]
        def touches(x, y, layer, skip):
            if on_pad(net, layer, x, y): return True
            for (j, vx, vy) in V:
                if math.hypot(vx - x, vy - y) <= 0.225: return True
            for (j, l2, w2, a2, b2) in T:
                if j == skip or l2 != layer: continue
                if segd(x, y, a2, b2) <= w2 / 2 + 1e-6: return True
            return False
        for (i, layer, w, a, b) in T:
            if not touches(a[0], a[1], layer, i) or not touches(b[0], b[1], layer, i):
                kill.add(i)
        for (j, vx, vy) in V:
            lays = {l for (i, l, w, a, b) in T if segd(vx, vy, a, b) <= w / 2 + 0.225}
            if any(on_pad(net, l, vx, vy) for l in ('F', 'B', 'In2')):
                lays.add('pad')
            if len(lays) < 2: kill.add(j)
    if not kill: break
    removed += len(kill)
    rows = [r for i, r in enumerate(rows) if i not in kill]
open(sys.argv[3], 'w').write('\n'.join(head + ['\t'.join(r) for r in rows]) + '\n')
print('prune:', removed, 'rows removed')
