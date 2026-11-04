#!/usr/bin/env python3
"""R12 routing drafting aid, step 2 (D-R12-26): route the placed R12 board on a 0.1 mm octilinear grid and write the
copper as an explicit table (m3_design/r12_routes.tsv) that m3_design/r12_route.py replays. Not part of the build:
the build never searches; this aid's output is reviewed and frozen (as R11's r11_legends_aid.py).

usage: python3 m3_design/r12_aid/route.py GEOMETRY.json PLAN.json OUT.tsv --lib astar.so [--report R.json]
needs numpy and the compiled astar.c (cc -O2 -shared -fPIC -o astar.so astar.c); GEOMETRY.json from export.py.

Model: F.Cu and B.Cu are routed; In1 (GND) and In2 (3V3) are planes reached by vias. Clearances are exact distances
from grid nodes to pad polygons, track capsules and via discs (KiCad DRC is the judge afterwards): 0.1 mm copper,
test pads 1.0 mm, Tag-Connect pads 0.508 mm, copper to the board edge 0.5 mm, a via hole 0.2 mm from foreign copper
(D-R12-23), via holes 0.25 mm apart. Segments are 0 / 45 / 90 degrees, bends 45 degrees, a middle segment at least
0.5 mm (no tiny jog), an end segment at least 0.2 mm.
"""
import argparse
import ctypes
import json
import math
from pathlib import Path

import numpy as np

G = 0.1                     # grid pitch, mm
CLR = 0.1                   # board copper clearance
EPS = 0.004
VIA_D, VIA_R_KEEP = 0.45, 0.25      # via pad; its keep radius for foreign tracks (hole 0.15 + 0.2 - CLR 0.1)
VIA_FOREIGN = 0.35          # via centre to foreign copper (hole clearance 0.2 + hole radius 0.15)
VIA_PAD = 0.30              # via centre to any pad copper (V-2 hole off SMD pads, ring off same-net pads)
VIA_VIA = 0.60              # via centre to via centre (hole to hole 0.25 + 0.3, rings apart)
EDGE = 0.5                  # copper to board edge (project min_copper_edge_clearance)
RMAX = 2.5                  # field update radius
LAYERS = ('F', 'B')


class Board:
    def __init__(self, geo, length):
        self.geo = geo
        self.W, self.L = 46.0, length
        self.NX, self.NY = int(round(self.W / G)) + 1, int(round(self.L / G)) + 1
        self.xs = np.arange(self.NX) * G
        self.ys = np.arange(self.NY) * G
        shp = (self.NY, self.NX)
        self.dA = [np.full(shp, 99.0, np.float32) for _ in LAYERS]
        self.dB = [np.full(shp, 99.0, np.float32) for _ in LAYERS]
        self.nA = [np.full(shp, -9, np.int32) for _ in LAYERS]
        self.nB = [np.full(shp, -9, np.int32) for _ in LAYERS]
        self.padany = np.full(shp, 99.0, np.float32)
        self.viad = np.full(shp, 99.0, np.float32)
        self.novia = np.zeros(shp, bool)
        self.nets = {}
        self.pads = []              # dict(ref, num, net, layers, poly, x, y, attr)
        self.tracks = []            # (net, layer, w, (x0,y0), (x1,y1))
        self.vias = []              # (net, x, y)
        self.tunit, self.vunit = [], []   # the routing unit that drew each (rip-up)
        self.unit = 'fixed'
        self.inside = {}            # pad key -> {layer: [(ix, iy)]}
        self._load()

    def load_planes(self, path):
        """m3_design/r12_planes.tsv: the In2 islands; a plane net's via must land inside its own island (0.5 mm in),
        a 3V3 via 0.6 mm clear of every island, and no plane via inside an S-8 keep-out."""
        X, Y = np.meshgrid(self.xs, self.ys)
        self.island = {}
        for line in Path(path).read_text().splitlines():
            if line.startswith('#') or line.startswith('net\t') or not line.strip():
                continue
            net, layer, prio, pts = line.split('\t')
            if layer != 'In2' or prio == '0':
                continue
            poly = [tuple(float(v) for v in q.split(',')) for q in pts.split()]
            self.island[net] = self.poly_sdist(X, Y, poly)
        self.s8 = np.zeros(X.shape, bool)
        for p in self.pads:
            if p['ref'] == 'J121':
                self.s8 |= np.hypot(X - p['x'], Y - p['y']) < 2.1

    def region_ok(self, net):
        if net == 'GND':
            return ~self.s8
        if net in self.island:
            return (self.island[net] <= -0.5) & ~self.s8
        ok = ~self.s8
        for d in self.island.values():
            ok &= d >= 0.6
        return ok

    def nid(self, name):
        if name not in self.nets:
            self.nets[name] = len(self.nets) + 1
        return self.nets[name]

    # ---------------- field primitives
    def region(self, x0, y0, x1, y1):
        i0 = max(0, int(math.floor((x0 - RMAX) / G)))
        i1 = min(self.NX, int(math.ceil((x1 + RMAX) / G)) + 1)
        j0 = max(0, int(math.floor((y0 - RMAX) / G)))
        j1 = min(self.NY, int(math.ceil((y1 + RMAX) / G)) + 1)
        X, Y = np.meshgrid(self.xs[i0:i1], self.ys[j0:j1])
        return (slice(j0, j1), slice(i0, i1)), X, Y

    def merge(self, li, sl, d, k):
        dA, nA, dB, nB = self.dA[li][sl], self.nA[li][sl], self.dB[li][sl], self.nB[li][sl]
        same_a = nA == k
        dA[same_a] = np.minimum(dA[same_a], d[same_a])
        same_b = (~same_a) & (nB == k)
        dB[same_b] = np.minimum(dB[same_b], d[same_b])
        sw = same_b & (dB < dA)
        if sw.any():
            ta, tn = dA[sw].copy(), nA[sw].copy()
            dA[sw], nA[sw] = dB[sw], nB[sw]
            dB[sw], nB[sw] = ta, tn
        other = (~same_a) & (~same_b)
        first = other & (d < dA)
        second = other & (~first) & (d < dB)
        dB[first], nB[first] = dA[first], nA[first]
        dA[first], nA[first] = d[first], k
        dB[second], nB[second] = d[second], k

    @staticmethod
    def poly_sdist(X, Y, pts):
        P = np.asarray(pts, float)
        A, B = P, np.roll(P, -1, axis=0)
        px, py = X[..., None], Y[..., None]
        ax, ay, bx, by = A[:, 0], A[:, 1], B[:, 0], B[:, 1]
        dx, dy = bx - ax, by - ay
        ll = dx * dx + dy * dy
        ll[ll == 0] = 1e-12
        t = np.clip(((px - ax) * dx + (py - ay) * dy) / ll, 0, 1)
        d = np.hypot(px - (ax + t * dx), py - (ay + t * dy)).min(axis=-1)
        cond = ((ay <= py) & (by > py)) | ((by <= py) & (ay > py))
        xint = ax + (py - ay) * dx / np.where(dy == 0, 1e-12, dy)
        inside = (cond & (px < xint)).sum(axis=-1) % 2 == 1
        return np.where(inside, -d, d)

    @staticmethod
    def seg_dist(X, Y, a, b):
        ax, ay = a
        dx, dy = b[0] - ax, b[1] - ay
        ll = dx * dx + dy * dy
        if ll == 0:
            return np.hypot(X - ax, Y - ay)
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / ll, 0, 1)
        return np.hypot(X - (ax + t * dx), Y - (ay + t * dy))

    # ---------------- loading
    def _load(self):
        g = self.geo
        # board edge and mounting holes: global obstacles (net -1)
        X, Y = np.meshgrid(self.xs, self.ys)
        de = np.minimum.reduce([X, self.W - X, Y, self.L - Y]) - (EDGE - CLR)
        for li in range(2):
            self.merge(li, (slice(None), slice(None)), de.astype(np.float32), -1)
        self.edge = np.minimum.reduce([X, self.W - X, Y, self.L - Y])
        for hx, hy, r in g['holes']:
            sl, X, Y = self.region(hx - r, hy - r, hx + r, hy + r)
            d = np.hypot(X - hx, Y - hy) - r - (EDGE - CLR)
            for li in range(2):
                self.merge(li, sl, d.astype(np.float32), -1)
            self.novia[sl] |= np.hypot(X - hx, Y - hy) < r + 0.8
        for f in g['fps']:
            for p in f['pads']:
                key = (f['ref'], p['num'], round(p['x'], 3), round(p['y'], 3))
                if p['attr'] == 'npth' or not p['layers'] or not p['poly']:
                    if p['attr'] == 'npth':     # a plain hole: copper >= 0.2 mm from its edge (JLC NPTH to track)
                        r = p['drill'] / 2
                        sl, X, Y = self.region(p['x'] - r, p['y'] - r, p['x'] + r, p['y'] + r)
                        d = np.hypot(X - p['x'], Y - p['y']) - r - 0.1
                        for li in range(2):
                            self.merge(li, sl, d.astype(np.float32), -1)
                        self.padany[sl] = np.minimum(self.padany[sl], d + 0.1)
                    continue
                pts = p['poly'][0]
                xs_, ys_ = [q[0] for q in pts], [q[1] for q in pts]
                sl, X, Y = self.region(min(xs_), min(ys_), max(xs_), max(ys_))
                sd = self.poly_sdist(X, Y, pts).astype(np.float32)
                extra = max(0.0, (p['clr'] or 0) - CLR)
                if f['ref'] == 'J2':
                    extra = 0.508 - CLR
                if f['ref'].startswith('TP'):
                    extra = 1.0 - CLR
                net = p['net'] if p['net'] and not p['net'].startswith('unconnected') else f'~{f["ref"]}.{p["num"]}'
                k = self.nid(net)
                for li, ln in enumerate(LAYERS):
                    if ln in p['layers']:
                        self.merge(li, sl, sd - extra, k)
                self.padany[sl] = np.minimum(self.padany[sl], sd)
                if p['attr'] == 'pth':     # PTH hole: vias keep the 0.45 mm pad-hole rule's spirit (0.6 centre)
                    hx, hy, r = p['x'], p['y'], p['drill'] / 2
                    self.novia[sl] |= np.hypot(X - hx, Y - hy) < r + 0.55 + VIA_D / 2 + 0.03   # JLC inner PTH hole rule
                lays = [ln for ln in LAYERS if ln in p['layers']]
                ins = {}
                minor = min(max(xs_) - min(xs_), max(ys_) - min(ys_))
                need = -min(0.15, 0.35 * minor)
                for ln in lays:
                    m = sd <= need + 1e-6
                    if not m.any():
                        m = sd < 0
                        if m.any():
                            dd = np.hypot(X - p['x'], Y - p['y'])
                            m = m & (dd <= dd[m].min() + 1e-6)
                    jj, ii = np.nonzero(m)
                    ins[ln] = [(int(i + sl[1].start), int(j + sl[0].start)) for j, i in zip(jj, ii)]
                self.inside[key] = ins
                self.pads.append(dict(ref=f['ref'], num=p['num'], net=net, layers=lays, poly=pts, x=p['x'], y=p['y'],
                                      attr=p['attr'], key=key, minor=minor))
        for z in g['zones']:
            if not z['rule'] or 'F' not in z['layers'] and 'B' not in z['layers']:
                continue
            for o in z['outline']:
                xs_, ys_ = [q[0] for q in o], [q[1] for q in o]
                sl, X, Y = self.region(min(xs_), min(ys_), max(xs_), max(ys_))
                sd = self.poly_sdist(X, Y, o).astype(np.float32)
                if z['notracks']:
                    for li, ln in enumerate(LAYERS):
                        if ln in z['layers']:
                            self.merge(li, sl, sd, -1)
                if z['novias']:
                    self.novia[sl] |= sd < VIA_D / 2 + 0.05

    # ---------------- copper
    def add_track(self, net, layer, w, a, b, record=True):
        li = LAYERS.index(layer)
        sl, X, Y = self.region(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
        d = (self.seg_dist(X, Y, a, b) - w / 2).astype(np.float32)
        self.merge(li, sl, d, self.nid(net))
        if record:
            self.tracks.append((net, layer, w, a, b))
            self.tunit.append(self.unit)

    def add_via(self, net, x, y, record=True):
        sl, X, Y = self.region(x, y, x, y)
        dd = np.hypot(X - x, Y - y)
        d = (dd - VIA_R_KEEP).astype(np.float32)
        for li in range(2):
            self.merge(li, sl, d, self.nid(net))
        self.viad[sl] = np.minimum(self.viad[sl], dd)
        if record:
            self.vias.append((net, x, y))
            self.vunit.append(self.unit)

    # ---------------- rip-up support (drafting): the fixed copper is in the snapshot, routed copper is re-merged
    def snapshot(self):
        self.snap = [a.copy() for a in self.dA + self.dB + self.nA + self.nB] + [self.viad.copy()]
        self.nfixed = (len(self.tracks), len(self.vias))

    def foreign_base(self, li, k):
        dA, dB, nA = self.snap[li], self.snap[2 + li], self.snap[4 + li]
        return np.where(nA != k, dA, dB)

    def remove_units(self, units):
        keep_t = [(t, u) for t, u in zip(self.tracks, self.tunit) if u not in units]
        keep_v = [(v, u) for v, u in zip(self.vias, self.vunit) if u not in units]
        removed = (len(self.tracks) - len(keep_t), len(self.vias) - len(keep_v))
        self.tracks, self.tunit = [t for t, _ in keep_t], [u for _, u in keep_t]
        self.vias, self.vunit = [v for v, _ in keep_v], [u for _, u in keep_v]
        s = self.snap
        self.dA, self.dB = [s[0].copy(), s[1].copy()], [s[2].copy(), s[3].copy()]
        self.nA, self.nB = [s[4].copy(), s[5].copy()], [s[6].copy(), s[7].copy()]
        self.viad = s[8].copy()
        for (net, layer, w, a, b), u in zip(self.tracks, self.tunit):
            if u != 'fixed':
                self.add_track(net, layer, w, a, b, record=False)
        for (net, x, y), u in zip(self.vias, self.vunit):
            if u != 'fixed':
                self.add_via(net, x, y, record=False)
        return removed

    def foreign(self, li, k):
        return np.where(self.nA[li] != k, self.dA[li], self.dB[li])

    def via_ok_base(self, k):
        return ((self.foreign_base(0, k) >= VIA_FOREIGN) & (self.foreign_base(1, k) >= VIA_FOREIGN)
                & (self.padany >= VIA_PAD) & (self.snap[8] >= VIA_VIA) & (~self.novia)
                & (self.edge >= EDGE + VIA_D / 2 + 0.1))

    def via_ok(self, k):
        return ((self.foreign(0, k) >= VIA_FOREIGN) & (self.foreign(1, k) >= VIA_FOREIGN) & (self.padany >= VIA_PAD)
                & (self.viad >= VIA_VIA) & (~self.novia) & (self.edge >= EDGE + VIA_D / 2 + 0.1))


class Router:
    def __init__(self, board, lib):
        self.b = board
        self.lib = ctypes.CDLL(lib)
        self.lib.astar.restype = ctypes.c_int
        self.fail = []
        self.log = []
        self.terms = {}
        self.hweight = 1.3

    def own_block(self, net, h, sl):
        """Nodes too close to this net's own tracks (no side-by-side copper, no crossing), except near own pads /
        own via centres, where branches meet."""
        b = self.b
        js, is_ = sl
        X, Y = np.meshgrid(b.xs[is_], b.ys[js])
        out = [np.zeros(X.shape, bool), np.zeros(X.shape, bool)]
        for (n, layer, w, a, bb) in b.tracks:
            if n != net:
                continue
            if max(a[0], bb[0]) < X[0, 0] - 2 or min(a[0], bb[0]) > X[0, -1] + 2 or \
                    max(a[1], bb[1]) < Y[0, 0] - 2 or min(a[1], bb[1]) > Y[-1, 0] + 2:
                continue
            d = b.seg_dist(X, Y, a, bb)
            out[LAYERS.index(layer)] |= d < w / 2 + h + CLR - EPS
        free = np.zeros(X.shape, bool)
        for (n, x, y) in b.vias:
            if n == net:
                free |= np.hypot(X - x, Y - y) < 0.2
        for p in b.pads:
            if p['net'] == net:
                for ln, nodes in b.inside[p['key']].items():
                    for (i, j) in nodes:
                        if is_.start <= i < is_.stop and js.start <= j < js.stop:
                            free[j - js.start, i - is_.start] = True
        for (l, i, j, m) in self.terms.get(net, []):
            free |= np.hypot(X - i * G, Y - j * G) < h + 0.6
        for li in range(2):
            out[li] &= ~free
        return out

    def search(self, net, w, starts, goals, window, layers=('F', 'B'), vias=True, via_cost=5.0, turn=1.0,
               avoid=None, maxexp=3_000_000, goal_via=False, maxvia=2, noown=False, extra_block=None, via_block=None, base=False):
        """starts: [(layer, ix, iy)]; goals: [(layer, ix, iy, dirmask)]; window: (i0, j0, i1, j1) node bounds.
        goal_via: any via-legal node is a goal (plane fan-out); the path then ends in a new via."""
        b = self.b
        k = b.nid(net)
        h = w / 2
        i0, j0, i1, j1 = window
        i0, j0 = max(0, i0), max(0, j0)
        i1, j1 = min(b.NX, i1), min(b.NY, j1)
        sl = (slice(j0, j1), slice(i0, i1))
        Wn, Hn = i1 - i0, j1 - j0
        own = self.own_block(net, h, sl) if not noown else [np.zeros((Hn, Wn), bool)] * 2
        blocked = np.zeros((2, Hn, Wn), np.uint8)
        for li in range(2):
            fo = b.foreign_base(li, k) if base else b.foreign(li, k)
            blocked[li] = (fo[sl] < h + CLR + EPS) | own[li]
            if extra_block is not None:
                blocked[li] |= extra_block[li][sl]
        vok = (b.via_ok_base(k) if base else b.via_ok(k))[sl] if (vias or goal_via) else np.zeros((Hn, Wn), bool)
        if via_block is not None:
            vok = vok & ~via_block[sl]
        goal = np.zeros((2, Hn, Wn), np.uint16)
        gc = []
        for (l, i, j, m) in goals:
            if i0 <= i < i1 and j0 <= j < j1:
                goal[l, j - j0, i - i0] |= m
                gc.append((i - i0, j - j0))
        if goal_via:
            for l in (0, 1):
                if LAYERS[l] in layers:
                    goal[l][vok & (blocked[l] == 0)] = 255
            jj, ii = np.nonzero(goal[0] | goal[1])
            if len(ii):
                step = max(1, len(ii) // 300)
                gc += [(float(i), float(j)) for i, j in zip(ii[::step], jj[::step])]
        st = [(l, i - i0, j - j0) for (l, i, j) in starts if i0 <= i < i1 and j0 <= j < j1]
        for (l, i, j) in st:
            blocked[l, j, i] = 0
        for (l, i, j, m) in goals:
            if i0 <= i < i1 and j0 <= j < j1:
                blocked[l, j - j0, i - i0] = 0
        if getattr(self, 'debug', None) == net:
            self.dbgn = getattr(self, 'dbgn', 0) + 1
            np.savez(self.debug_out + str(self.dbgn), blocked=blocked, goal=goal, vok=vok, starts=np.array(st), win=np.array([i0, j0, i1, j1]))
            print('   debug saved', net, (i0, j0, i1, j1), len(st), int((goal > 0).sum()))
        if not st or not (goal.any()):
            return None
        # heuristic centres: cluster goals coarsely (admissible: radius = max distance in the cluster)
        if goal_via:
            pts = np.array(gc, float)
            gx, gy, gr = list(pts[:, 0]), list(pts[:, 1]), [2.0] * len(pts)
        else:
            pts = np.array(gc, float)
            cx, cy = pts[:, 0].mean(), pts[:, 1].mean()
            r = float(np.hypot(pts[:, 0] - cx, pts[:, 1] - cy).max())
            if r > 20:
                gx, gy, gr = list(pts[:, 0]), list(pts[:, 1]), [0.0] * len(pts)
            else:
                gx, gy, gr = [cx], [cy], [r]
        if not vias:
            vok = np.zeros_like(vok)
        av = avoid[sl].astype(np.uint8) if avoid is not None else np.zeros((2, Hn, Wn), np.uint8)
        end_l = max(w, 0.2) + 0.005
        mid_l = max(0.5, w + 0.05)
        es, ed = int(end_l / G) + 1, int(end_l / (G * math.sqrt(2))) + 1
        ms, md = math.ceil(mid_l / G - 1e-9), math.ceil(mid_l / (G * math.sqrt(2)) - 1e-9)
        rm = max(es, ed, ms, md)
        params = np.array([1.0, 1.41421356, turn, via_cost, 1.0, 1.0, ms, md, es, ed, 0.2,
                           1 if 'F' in layers else 0, 1 if 'B' in layers else 0, rm, maxvia if vias else 0,
                           self.hweight, 6], np.float32)
        sarr = np.array(st, np.int32).ravel()
        out = np.zeros(3 * 200000, np.int32)
        fl = lambda a: a.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        n = self.lib.astar(ctypes.c_int(Wn), ctypes.c_int(Hn),
                           np.ascontiguousarray(blocked).ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                           np.ascontiguousarray(vok.astype(np.uint8)).ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                           np.ascontiguousarray(goal).ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                           np.ascontiguousarray(av).ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                           ctypes.c_int(len(st)), sarr.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                           ctypes.c_int(len(gx)), fl(np.array(gx, np.float32)), fl(np.array(gy, np.float32)),
                           fl(np.array(gr, np.float32)), fl(params), ctypes.c_int(200000),
                           out.ctypes.data_as(ctypes.POINTER(ctypes.c_int)), ctypes.c_long(maxexp))
        if n <= 0:
            self.last_status = n
            return None
        self.last_status = n
        path = [(int(out[3 * q]), int(out[3 * q + 1]) + i0, int(out[3 * q + 2]) + j0) for q in range(n)][::-1]
        return path

    def commit(self, net, w, path, end_via=False):
        """Path nodes -> segments (collinear merged) and vias; add to the board."""
        b = self.b
        segs, vias = [], []
        run = [path[0]]
        for p in path[1:]:
            if p[0] != run[-1][0]:            # layer change: a via at this node
                segs.append(run)
                vias.append((p[1], p[2]))
                run = [p]
            else:
                run.append(p)
        segs.append(run)
        if end_via:
            vias.append((path[-1][1], path[-1][2]))
        n_tr = 0
        for run in segs:
            if len(run) < 2:
                continue
            pts = [run[0]]
            for q in run[1:]:
                pts.append(q)
                if len(pts) >= 3:
                    a, m, c = pts[-3], pts[-2], pts[-1]
                    sg = lambda v: (v > 0) - (v < 0)
                    if (sg(m[1] - a[1]), sg(m[2] - a[2])) == (sg(c[1] - m[1]), sg(c[2] - m[2])):
                        pts.pop(-2)
            layer = LAYERS[run[0][0]]
            for a, c in zip(pts, pts[1:]):
                b.add_track(net, layer, w, (round(a[1] * G, 4), round(a[2] * G, 4)), (round(c[1] * G, 4), round(c[2] * G, 4)))
                n_tr += 1
        for (i, j) in vias:
            if not any(v[0] == net and abs(v[1] - i * G) < 1e-6 and abs(v[2] - j * G) < 1e-6 for v in b.vias):
                b.add_via(net, round(i * G, 4), round(j * G, 4))
        return n_tr, len(vias)

    # ---------------- terminals
    def pad_nodes(self, p, layers=('F', 'B'), dirmask=255):
        out = []
        for ln, nodes in self.b.inside[p['key']].items():
            if ln in layers:
                li = LAYERS.index(ln)
                out += [(li, i, j) if dirmask is None else (li, i, j, dirmask) for (i, j) in nodes]
        return out

    def via_nodes(self, net):
        out = []
        for (n, x, y) in self.b.vias:
            if n == net:
                i, j = int(round(x / G)), int(round(y / G))
                out += [(0, i, j, 255), (1, i, j, 255)]
        return out


def blockers(b, net, w, path):
    """Routing units whose (non-fixed) copper lies within clearance of a base-mode path."""
    out = set()
    pts = {0: [], 1: []}
    for (l, i, j) in path:
        pts[l].append((i * G, j * G))
    vias_on_path = [(path[q][1] * G, path[q][2] * G) for q in range(1, len(path)) if path[q][0] != path[q - 1][0]]
    P = {l: np.array(v) if v else np.zeros((0, 2)) for l, v in pts.items()}
    allp = np.array([(i * G, j * G) for (_, i, j) in path])
    for (n, layer, tw, a, c), u in zip(b.tracks, b.tunit):
        if u == 'fixed' or n == net or u in out:
            continue
        li = LAYERS.index(layer)
        Q = P[li]
        if len(Q) == 0:
            continue
        if min(a[0], c[0]) - 2 > Q[:, 0].max() or max(a[0], c[0]) + 2 < Q[:, 0].min() or \
                min(a[1], c[1]) - 2 > Q[:, 1].max() or max(a[1], c[1]) + 2 < Q[:, 1].min():
            continue
        d = Board.seg_dist(Q[:, 0], Q[:, 1], a, c)
        if (d < w / 2 + tw / 2 + CLR + EPS).any():
            out.add(u)
        elif vias_on_path:
            V = np.array(vias_on_path)
            if (Board.seg_dist(V[:, 0], V[:, 1], a, c) < VIA_FOREIGN + tw / 2).any():
                out.add(u)
    for (n, x, y), u in zip(b.vias, b.vunit):
        if u == 'fixed' or n == net or u in out:
            continue
        if len(allp) and (np.hypot(allp[:, 0] - x, allp[:, 1] - y) < VIA_R_KEEP + w / 2 + CLR + EPS).any():
            out.add(u)
        elif vias_on_path and min(math.hypot(x - vx, y - vy) for vx, vy in vias_on_path) < VIA_VIA:
            out.add(u)
    return out


def window_of(nodes, margin):
    i = [n[1] for n in nodes]
    j = [n[2] for n in nodes]
    m = int(margin / G)
    return min(i) - m, min(j) - m, max(i) + m + 1, max(j) + m + 1
