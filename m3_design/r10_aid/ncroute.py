#!/usr/bin/env python3
"""R10 signal design aid (not a build stage): negotiated-congestion routing of the non-critical signal nets
(R10_DECISIONS D-R2-04, D-R2-07) on the octilinear A* kernel astar.c (compile: cc -O2 -o astar astar.c -lm, beside
this file). Every segment is 0/45/90 deg, bends are 45/90 deg with >= 0.5 mm runs; nets in signal_nets.txt may carry
path=PAD;x,y;@x,y;PAD waypoints (x,y a new via, @x,y an existing via of the net). The result is frozen into
m3_design/r10_route_signals.py's AUTO table by freeze_signals.py and then hand-cleaned; the build never searches.
usage: R10_NUMPY_PATH=... KiCad python3 -I ncroute.py board.kicad_pcb signal_nets.txt out.json [iterations]
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sigroute as sr
import numpy as np
import pcbnew
import struct, subprocess
ASTAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'astar')


def croute(g, occ, pres, code, src, tgt, win, maxexp=4_000_000):
    i0 = max(0, int((win[0] - g.X0) / g.res)); i1 = min(g.nx - 1, int((win[1] - g.X0) / g.res) + 1)
    j0 = max(0, int((win[2] - g.Y0) / g.res)); j1 = min(g.ny - 1, int((win[3] - g.Y0) / g.res) + 1)
    sl = (slice(j0, j1 + 1), slice(i0, i1 + 1))
    tf = [((g.trk[l][sl] == 0) | (g.trk[l][sl] == code)).astype(np.uint8) for l in ('F', 'B')]
    vf = (((g.via['F'][sl] == 0) | (g.via['F'][sl] == code)) & ((g.via['B'][sl] == 0) | (g.via['B'][sl] == code))).astype(np.uint8)
    ex = [(pres * occ.T[l][sl] + occ.H[l][sl]).astype(np.float32) for l in ('F', 'B')]
    vx = (4 * (pres * (occ.V['F'][sl] + occ.V['B'][sl]) + occ.HV[sl])).astype(np.float32)
    lm = lambda ls: sum(1 << ('F', 'B').index(l) for l in ls)
    hdr = struct.pack('6i', i1 - i0 + 1, j1 - j0 + 1, lm(src[3]), lm(tgt[3]), maxexp, 0)
    dh = struct.pack('13d', g.X0 + i0 * g.res, g.Y0 + j0 * g.res, g.res, src[1], src[2], tgt[1], tgt[2], g.res,
                     sr.T45, sr.T90, sr.VIA_COST, sr.MINRUN, min(sr.MINRUN, 0.3))
    data = hdr + dh + b''.join(a.tobytes() for a in tf) + vf.tobytes() + b''.join(a.tobytes() for a in ex) + vx.tobytes()
    out = subprocess.run([ASTAR], input=data, capture_output=True).stdout.decode().split('\n')
    if not out[0].startswith('OK'):
        return None
    n = int(out[0].split()[1])
    pts = [tuple(float(v) for v in ln.split()[:2]) + ('FB'[int(ln.split()[2])],) for ln in out[1:1 + n]]
    pts.reverse()
    e = out[1 + n].split()
    px, py, gx, gy, l, bend = float(e[1]), float(e[2]), float(e[3]), float(e[4]), 'FB'[int(e[5])], int(e[6])
    tail = ([(round(px, 4), round(py, 4), l)] if bend else []) + [(gx, gy, l)]
    return [(round(x, 4), round(y, 4), l) for x, y, l in pts] + tail


RT = sr.CLR + sr.W            # track centre to other track centre
RTV = sr.CLR + sr.W / 2 + sr.VIA_D / 2
RVV = sr.CLR + sr.VIA_D


class Occ:
    def __init__(self, g):
        self.g = g
        self.T = {l: np.zeros((g.ny, g.nx), np.int16) for l in sr.LAYERS}   # cells a track centre of another net may not use
        self.V = {l: np.zeros((g.ny, g.nx), np.int16) for l in sr.LAYERS}   # cells a via centre of another net may not use
        self.H = {l: np.zeros((g.ny, g.nx), np.float32) for l in sr.LAYERS}
        self.HV = np.zeros((g.ny, g.nx), np.float32)

    def disk_seg(self, arr, a, b, r, delta):
        g = self.g
        x0, x1 = min(a[0], b[0]) - r, max(a[0], b[0]) + r
        y0, y1 = min(a[1], b[1]) - r, max(a[1], b[1]) + r
        i0 = max(0, int((x0 - g.X0) / g.res)); i1 = min(g.nx - 1, int((x1 - g.X0) / g.res) + 1)
        j0 = max(0, int((y0 - g.Y0) / g.res)); j1 = min(g.ny - 1, int((y1 - g.Y0) / g.res) + 1)
        gx, gy = np.meshgrid(g.xs[i0:i1 + 1], g.ys[j0:j1 + 1])
        vx, vy = b[0] - a[0], b[1] - a[1]
        L2 = vx * vx + vy * vy or 1e-12
        t = np.clip(((gx - a[0]) * vx + (gy - a[1]) * vy) / L2, 0, 1)
        d = np.hypot(gx - a[0] - t * vx, gy - a[1] - t * vy)
        arr[j0:j1 + 1, i0:i1 + 1][d < r] += delta

    def apply(self, route, delta):
        for l, pts, *_ in route['polys']:
            for a, b in zip(pts, pts[1:]):
                self.disk_seg(self.T[l], a, b, RT, delta)
                self.disk_seg(self.V[l], a, b, RTV, delta)
        for v in route['vias']:
            for l in sr.LAYERS:
                self.disk_seg(self.T[l], v, v, RTV, delta)
                self.disk_seg(self.V[l], v, v, RVV, delta)

    def cell(self, x, y):
        return self.g.cell(x, y)


def main():
    board, nets_path, out = sys.argv[1:4]
    iters = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    b = pcbnew.LoadBoard(board)
    g = sr.Grid(b, float(os.environ.get('RES', '0.1'))); g.build()
    occ = Occ(g)
    specs = [l.split('#')[0].strip() for l in open(nets_path)]
    specs = [s for s in specs if s]
    # connections per net (pad groups as in sigroute)
    conns = {}
    conn = b.GetConnectivity()
    for spec in specs:
        net = spec.split()[0]
        pads = sr.pads_of(b, net)
        groups = []
        for pd in pads:
            ref, num = pd[0].split('.')
            obj = [q for q in b.FindFootprintByReference(ref).Pads() if q.GetNumber() == num][0]
            ids = {it.m_Uuid.AsString() for it in conn.GetConnectedItems(obj)} | {obj.m_Uuid.AsString()}
            for gp in groups:
                if gp['ids'] & ids:
                    gp['pads'].append(pd); gp['ids'] |= ids; break
            else:
                groups.append({'pads': [pd], 'ids': ids})
        cl = []
        bypad = {p[0]: p for p in pads}
        for tok in spec.split()[1:]:
            if not tok.startswith('path='):
                continue
            elems = []
            for e in tok[5:].split(';'):
                if e in bypad:
                    elems.append(bypad[e])
                elif e.startswith('@'):                  # an existing via of the net: either layer, no new via
                    x, y = map(float, e[1:].split(','))
                    elems.append(('pt', x, y, ['F', 'B']))
                else:
                    x, y = map(float, e.split(','))
                    elems.append(('via', x, y, ['F', 'B']))
            for a, c in zip(elems, elems[1:]):
                if a[0] == 'via' and c[0] == 'via':      # a hop between two waypoints runs on the other layer (B.Cu)
                    a, c = ('via', a[1], a[2], ['B']), ('via', c[1], c[2], ['B'])
                elif a[0] == 'via':
                    a = ('via', a[1], a[2], [l for l in c[3] if l != 'B'] or c[3])
                elif c[0] == 'via':
                    c = ('via', c[1], c[2], [l for l in a[3] if l != 'B'] or a[3])
                cl.append((a, c))
            # merge the groups the path joins
            names = [e[0] for e in elems if e[0] != 'via']
            hit = [gp for gp in groups if any(p[0] in names for p in gp['pads'])]
            if len(hit) > 1:
                for gp in hit[1:]:
                    hit[0]['pads'] += gp['pads']; hit[0]['ids'] |= gp['ids']; groups.remove(gp)
        done = list(groups[0]['pads']); todo = groups[1:]
        if '@' in spec:                                  # a path onto existing copper completes the net
            todo = []
        while todo:
            todo.sort(key=lambda gp: min(sr.octd(p, q) for p in gp['pads'] for q in done))
            gp = todo.pop(0)
            src, tgt = min(((q, p) for p in gp['pads'] for q in done), key=lambda st: sr.octd(*st))
            cl.append((src, tgt)); done.extend(gp['pads'])
        conns[net] = cl
    routes = {}
    pres = 0.5
    for it in range(iters):
        nconf = 0
        for spec in specs:
            net = spec.split()[0]
            code = b.FindNet(net).GetNetCode()
            if net in routes:
                occ.apply(routes[net], -1)
            r = {'polys': [], 'vias': [], 'ok': True}

            def extra(l, x, y):
                i, j = g.cell(x, y)
                return pres * occ.T[l][j, i] + occ.H[l][j, i]

            def vextra(x, y):
                i, j = g.cell(x, y)
                return 4 * (pres * (occ.V['F'][j, i] + occ.V['B'][j, i]) + occ.HV[j, i])

            own = {'polys': [], 'vias': []}
            for src, tgt in conns[net]:
                seq = None
                for m in (4.0, 12.0, 40.0):
                    win = (min(src[1], tgt[1]) - m, max(src[1], tgt[1]) + m, min(src[2], tgt[2]) - m, max(src[2], tgt[2]) + m)
                    seq = croute(g, occ, pres, code, src, tgt, win)
                    if seq is not None:
                        break
                if seq is None:
                    r['ok'] = False
                    print(f'  {net}: FAILED {src[0]} -> {tgt[0]}', flush=True)
                    continue
                ps, vs = sr.simplify(seq)
                r['polys'] += [[l, pts, src[0], tgt[0]] for l, pts in ps]
                r['vias'] += vs
                if tgt[0] == 'via' and (tgt[1], tgt[2]) not in [tuple(v) for v in r['vias']]:
                    r['vias'].append((tgt[1], tgt[2]))
            routes[net] = r
            occ.apply(r, +1)
        # conflicts: a track centre / via of a net inside another net's halo
        conflicts = 0
        where = {}
        for net, r in routes.items():
            occ.apply(r, -1)
            for l, pts, *_ in r['polys']:
                for a, c in zip(pts, pts[1:]):
                    n = max(1, int(math.dist(a, c) / 0.05))
                    for k in range(n + 1):
                        x, y = a[0] + (c[0] - a[0]) * k / n, a[1] + (c[1] - a[1]) * k / n
                        i, j = g.cell(x, y)
                        if occ.T[l][j, i] > 0:
                            conflicts += 1; occ.H[l][j, i] += 1.0; where.setdefault(net, set()).add((round(x), round(y), l))
            for v in r['vias']:
                i, j = g.cell(*v)
                if occ.V['F'][j, i] > 0 or occ.V['B'][j, i] > 0:
                    conflicts += 1; occ.HV[j, i] += 1.5
            occ.apply(r, +1)
        fails = [n for n, r in routes.items() if not r['ok']]
        if it == iters - 1 or conflicts == 0:
            for n, w in sorted(where.items()):
                print('   conflict', n, sorted(w)[:6])
        print(f'iteration {it}: conflicts {conflicts}, failed {fails}', flush=True)
        json.dump(routes, open(out, 'w'), indent=0)
        if conflicts == 0 and not fails:
            break
        pres = min(pres * 1.5, 300.0)


if __name__ == '__main__':
    main()
