#!/usr/bin/env python3
"""Octilinear grid maze router (design aid, not a build stage). KiCad python; numpy through R10_NUMPY_PATH.

usage: sigroute.py board.kicad_pcb nets.txt out.json [--res 0.1]
nets.txt: one net per line (routing order). For each net the pads are joined as a tree: the first pad is the root,
each further pad is reached from the tree (T junctions at 90 deg) or ends a branch at its centre. Every segment is
0/45/90 deg, turns are 45 or 90 deg only, straight runs between turns >= MINRUN, vias cost VIA_COST.
"""
import heapq
import json
import math
import os
import sys

sys.path += [p for p in os.environ.get('R10_NUMPY_PATH', '').split(os.pathsep) if p]   # numpy for KiCad's python
import numpy as np
import pcbnew

MM, mm = pcbnew.FromMM, pcbnew.ToMM
W = 0.2                 # signal width
CLR = 0.165             # board 0.15 + margin for raster error
VIA_D = 0.5
EDGE = 0.5
T45, T90 = 0.8, 1.2     # bend costs, mm
VIA_COST = 1.0
MINRUN = 0.5            # mm straight between bends
DIRS = [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1)]   # E NE N NW W SW S SE (y down)
LAYERS = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}


def item_clear(it):
    if it.GetClass() == 'PAD':
        ref = it.GetParentFootprint().GetReference()
        if ref.startswith('TP'):
            return 1.01
        if ref == 'J2':
            return 0.518
    return CLR


class Grid:
    def __init__(self, board, res):
        self.b, self.res = board, res
        bb = board.GetBoardEdgesBoundingBox()
        self.X0, self.Y0 = mm(bb.GetX()), mm(bb.GetY())
        self.X1, self.Y1 = mm(bb.GetRight()), mm(bb.GetBottom())
        self.nx = int(round((self.X1 - self.X0) / res)) + 1
        self.ny = int(round((self.Y1 - self.Y0) / res)) + 1
        self.trk = {l: np.zeros((self.ny, self.nx), np.int32) for l in LAYERS}
        self.via = {l: np.zeros((self.ny, self.nx), np.int32) for l in LAYERS}
        self.xs = self.X0 + np.arange(self.nx) * res
        self.ys = self.Y0 + np.arange(self.ny) * res

    def mark(self, arr, poly_pts, owner):
        pts = np.array(poly_pts)
        x0, y0 = pts.min(0); x1, y1 = pts.max(0)
        i0 = max(0, int(math.floor((x0 - self.X0) / self.res))); i1 = min(self.nx - 1, int(math.ceil((x1 - self.X0) / self.res)))
        j0 = max(0, int(math.floor((y0 - self.Y0) / self.res))); j1 = min(self.ny - 1, int(math.ceil((y1 - self.Y0) / self.res)))
        if i1 < i0 or j1 < j0:
            return
        gx, gy = np.meshgrid(self.xs[i0:i1 + 1], self.ys[j0:j1 + 1])
        inside = np.zeros(gx.shape, bool)
        n = len(pts)
        for k in range(n):
            (ax, ay), (bx, by) = pts[k], pts[(k + 1) % n]
            cond = (ay > gy) != (by > gy)
            with np.errstate(divide='ignore', invalid='ignore'):
                xint = ax + (gy - ay) * (bx - ax) / (by - ay)
            inside ^= cond & (gx < xint)
        sub = arr[j0:j1 + 1, i0:i1 + 1]
        cur = sub[inside]
        new = np.where(cur == 0, owner, np.where(cur == owner, owner, -1))
        sub[inside] = new

    def mark_shape(self, it, layer, owner, infl_trk, infl_via):
        for arr, infl in ((self.trk, infl_trk), (self.via, infl_via)):
            ps = pcbnew.SHAPE_POLY_SET()
            it.TransformShapeToPolygon(ps, LAYERS[layer], MM(infl), MM(0.005), pcbnew.ERROR_OUTSIDE)
            for i in range(ps.OutlineCount()):
                o = ps.Outline(i)
                self.mark(arr[layer], [(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())], owner)

    def build(self):
        b = self.b
        for f in b.GetFootprints():
            for p in f.Pads():
                owner = p.GetNetCode() if p.GetNetCode() > 0 else -1
                c = item_clear(p)
                for l in LAYERS:
                    if p.IsOnLayer(LAYERS[l]):
                        self.mark_shape(p, l, owner, c + W / 2, c + VIA_D / 2)
                if p.GetDrillSizeX() > 0:          # hole clearance 0.25 on every layer (NPTH included)
                    r = mm(p.GetDrillSizeX()) / 2
                    cx, cy = mm(p.GetPosition().x), mm(p.GetPosition().y)
                    for l in LAYERS:
                        for arr, infl in ((self.trk, 0.3 + W / 2), (self.via, 0.3 + VIA_D / 2)):
                            self.mark(arr[l], circle(cx, cy, r + infl), owner if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else -1)
        for t in b.GetTracks():
            owner = t.GetNetCode()
            if t.GetClass() == 'PCB_VIA':
                for l in LAYERS:
                    self.mark_shape(t, l, owner, CLR + W / 2, CLR + VIA_D / 2 + 0.05)
            else:
                for l, lid in LAYERS.items():
                    if t.GetLayer() == lid:
                        self.mark_shape(t, l, owner, CLR + W / 2, CLR + VIA_D / 2)
        # board edge and Edge.Cuts holes
        e = EDGE + 0.05
        for l in LAYERS:
            for arr, infl in ((self.trk, e + W / 2), (self.via, e + VIA_D / 2)):
                k = int(math.ceil(infl / self.res))
                arr[l][:k, :] = -1; arr[l][-k:, :] = -1; arr[l][:, :k] = -1; arr[l][:, -k:] = -1
        for d in b.GetDrawings():
            if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                cx, cy, r = mm(d.GetCenter().x), mm(d.GetCenter().y), mm(d.GetRadius())
                for l in LAYERS:
                    self.mark(self.trk[l], circle(cx, cy, r + e + W / 2), -1)
                    self.mark(self.via[l], circle(cx, cy, r + e + VIA_D / 2), -1)
        # rule areas that forbid tracks / vias
        for z in b.Zones():
            if not z.GetIsRuleArea():
                continue
            o = z.Outline().Outline(0)
            pts = [(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())]
            for l, lid in LAYERS.items():
                if z.IsOnLayer(lid):
                    if z.GetDoNotAllowTracks():
                        self.mark(self.trk[l], pts, -1)
                    if z.GetDoNotAllowVias():
                        self.mark(self.via[l], pts, -1)

    def cell(self, x, y):
        return int(round((x - self.X0) / self.res)), int(round((y - self.Y0) / self.res))

    def free(self, layer, x, y, net, via=False):
        i, j = self.cell(x, y)
        if not (0 <= i < self.nx and 0 <= j < self.ny):
            return False
        v = (self.via if via else self.trk)[layer][j, i]
        return v == 0 or v == net

    def seg_free(self, layer, a, b, net):
        L = math.dist(a, b)
        n = max(1, int(L / (self.res / 2)))
        return all(self.free(layer, a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n, net) for k in range(n + 1))

    def add_path(self, net, layer, pts):
        for a, b in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
            t.SetWidth(MM(W)); t.SetLayer(LAYERS[layer])
            self.mark_shape(t, layer, net, CLR + W / 2, CLR + VIA_D / 2)

    def add_via(self, net, at):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pcbnew.VECTOR2I(MM(at[0]), MM(at[1]))); v.SetWidth(MM(VIA_D)); v.SetDrill(MM(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        for l in LAYERS:
            self.mark_shape(v, l, net, CLR + W / 2, CLR + VIA_D / 2 + 0.05)


def circle(cx, cy, r, n=24):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def octi(dx, dy):
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return None
    if abs(dy) < 1e-6:
        return 0 if dx > 0 else 4
    if abs(dx) < 1e-6:
        return 6 if dy > 0 else 2
    if abs(abs(dx) - abs(dy)) < 1e-6:
        return {(1, -1): 1, (-1, -1): 3, (-1, 1): 5, (1, 1): 7}[(int(math.copysign(1, dx)), int(math.copysign(1, dy)))]
    return None


def turn_cost(d1, d2):
    if d1 < 0 or d1 == d2:
        return 0.0
    k = min((d1 - d2) % 8, (d2 - d1) % 8)
    return {1: T45, 2: T90}.get(k)


def route(g, net, start, slayers, goals, tree, res, window, extra=None, vextra=None, maxexp=3_000_000):
    """start: (x, y) grid origin; slayers: layers allowed at start; goals: list of (cx, cy, layers);
    tree: dict layer -> {(i, j): axis_dir} cells where a perpendicular T may end.
    Returns (layer-tagged point list) or None."""
    ox, oy = start
    minrun = int(math.ceil(MINRUN / res))
    xlo, xhi, ylo, yhi = window

    def P(i, j):
        return (round(ox + i * res, 4), round(oy + j * res, 4))

    def h(i, j):
        x, y = P(i, j)
        best = 1e9
        for cx, cy, _ in goals:
            dx, dy = abs(cx - x), abs(cy - y)
            best = min(best, max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy))
        for l in tree:
            for (ti, tj) in tree[l]:
                pass
        return best if goals else 0.0

    # state: (i, j, layer, dir, run)
    openh = []
    came = {}
    gbest = {}
    for l in slayers:
        s = (0, 0, l, -1, minrun)
        gbest[s] = 0.0
        heapq.heappush(openh, (h(0, 0), 0.0, s))
        came[s] = None
    tree_cells = {l: tree.get(l, {}) for l in LAYERS}
    expanded = 0
    while openh:
        f, gc, s = heapq.heappop(openh)
        if gc > gbest.get(s, 1e18) + 1e-9:
            continue
        expanded += 1
        if expanded > maxexp:
            return None
        i, j, l, d, run = s
        x, y = P(i, j)
        # goal: T onto the tree (perpendicular, not the start cell)
        if (i, j) != (0, 0) and d >= 0 and (round(x, 3), round(y, 3)) in tree_cells[l]:
            ax = tree_cells[l][(round(x, 3), round(y, 3))]
            if (d - ax) % 4 == 2 and run >= 1:
                return finish(came, s, P, [(x, y, l)])
        # goal edges: straight on (and one bend) to a goal pad centre
        for cx, cy, gl in goals:
            if l not in gl:
                continue
            ds = [d] if d >= 0 else range(8)
            for d1 in ds:
                ux, uy = DIRS[d1]
                for d2 in (d1, (d1 + 1) % 8, (d1 - 1) % 8, (d1 + 2) % 8, (d1 - 2) % 8):
                    vx, vy = DIRS[d2]
                    # solve (x,y) + t*(ux,uy) + u*(vx,vy) = (cx,cy), t,u >= 0
                    det = ux * vy - vx * uy
                    rx, ry = cx - x, cy - y
                    if d2 == d1:
                        dd = octi(rx, ry)
                        if dd != d1:
                            continue
                        t, u = math.hypot(rx, ry) / math.hypot(ux, uy), 0.0
                    else:
                        if abs(det) < 1e-12:
                            continue
                        t = (rx * vy - vx * ry) / det
                        u = (ux * ry - uy * rx) / det
                        if t < -1e-9 or u < -1e-9:
                            continue
                    px, py = x + t * ux, y + t * uy
                    L1 = t * math.hypot(ux, uy); L2 = u * math.hypot(vx, vy)
                    if d2 != d1:
                        if run * res + L1 < MINRUN - 1e-6 and d >= 0:
                            continue
                        if L2 < min(MINRUN, 0.3) and L2 > 1e-6:
                            continue
                    if not g.seg_free(l, (x, y), (px, py), net) or not g.seg_free(l, (px, py), (cx, cy), net):
                        continue
                    tail = [(round(px, 4), round(py, 4), l)] if L1 > 1e-6 and L2 > 1e-6 else []
                    return finish(came, s, P, tail + [(cx, cy, l)])
        # moves
        for nd in (range(8) if d < 0 else (d, (d + 1) % 8, (d - 1) % 8, (d + 2) % 8, (d - 2) % 8)):
            tc = turn_cost(d, nd)
            if tc is None:
                continue
            if d >= 0 and nd != d and run < minrun:
                continue
            ni, nj = i + DIRS[nd][0], j + DIRS[nd][1]
            nx_, ny_ = P(ni, nj)
            if not (xlo <= nx_ <= xhi and ylo <= ny_ <= yhi):
                continue
            if not g.free(l, nx_, ny_, net):
                continue
            step = res * (math.sqrt(2) if nd % 2 else 1.0)
            if extra is not None:
                step += extra(l, nx_, ny_) * step
            nrun = min(minrun, (run + 1) if nd == d else 1)
            ns = (ni, nj, l, nd, nrun)
            ng = gc + step + tc
            if ng < gbest.get(ns, 1e18) - 1e-9:
                gbest[ns] = ng; came[ns] = s
                heapq.heappush(openh, (ng + h(ni, nj), ng, ns))
        # via
        if d >= 0 and run >= minrun or d < 0 and (i, j) != (0, 0):
            for nl in LAYERS:
                if nl != l and all(g.free(q, x, y, net, via=True) for q in LAYERS):
                    ns = (i, j, nl, -1, 0)
                    ng = gc + VIA_COST + (vextra(x, y) if vextra is not None else 0.0)
                    if ng < gbest.get(ns, 1e18) - 1e-9:
                        gbest[ns] = ng; came[ns] = s
                        heapq.heappush(openh, (ng + h(i, j), ng, ns))
    return None


def finish(came, s, P, tail):
    seq = []
    while s is not None:
        i, j, l, d, run = s
        x, y = P(i, j)
        seq.append((x, y, l))
        s = came[s]
    seq.reverse()
    return seq + tail


def simplify(seq):
    """split into per-layer polylines and vias; drop collinear points."""
    paths, vias = [], []
    cur = [seq[0]]
    for p in seq[1:]:
        if p[2] != cur[-1][2] and (p[0], p[1]) == (cur[-1][0], cur[-1][1]):
            paths.append(cur); vias.append((p[0], p[1])); cur = [p]
        else:
            cur.append(p)
    paths.append(cur)
    out = []
    for path in paths:
        pts = [(round(x, 4), round(y, 4)) for x, y, _ in path]
        dedup = [pts[0]]
        for q in pts[1:]:
            if q != dedup[-1]:
                dedup.append(q)
        pts = dedup
        keep = [pts[0]]
        for k in range(1, len(pts) - 1):
            a, b, c = keep[-1], pts[k], pts[k + 1]
            if octi(b[0] - a[0], b[1] - a[1]) != octi(c[0] - b[0], c[1] - b[1]):
                keep.append(b)
        if len(pts) > 1:
            keep.append(pts[-1])
        if len(keep) > 1:
            out.append((path[0][2], keep))
    return out, vias


def octd(p, q):
    dx, dy = abs(p[1] - q[1]), abs(p[2] - q[2])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def pads_of(board, net):
    res = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net:
                ls = [l for l, lid in LAYERS.items() if p.IsOnLayer(lid)]
                res.append((f'{f.GetReference()}.{p.GetNumber()}', mm(p.GetPosition().x), mm(p.GetPosition().y), ls))
    return res


def main():
    board_path, nets_path, out_path = sys.argv[1:4]
    res = float(sys.argv[sys.argv.index('--res') + 1]) if '--res' in sys.argv else 0.1
    b = pcbnew.LoadBoard(board_path)
    g = Grid(b, res)
    g.build()
    results = {}
    order = [l.split('#')[0].strip() for l in open(nets_path)]
    for spec in [o for o in order if o]:
        net, *opts = spec.split()
        code = b.FindNet(net).GetNetCode()
        pads = pads_of(b, net)
        # group pads already joined by copper (hand-routed or power-family tracks)
        conn = b.GetConnectivity()
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
        first = [o[6:] for o in opts if o.startswith('first=')]
        if first:
            groups.sort(key=lambda gp: all(p[0] != first[0] for p in gp['pads']))
        done = list(groups[0]['pads'])
        todo = groups[1:]
        polys, vias = [], []
        ok = True
        while todo:
            todo.sort(key=lambda gp: min(octd(p, q) for p in gp['pads'] for q in done))
            gp = todo.pop(0)
            src, tgt = min(((q, p) for p in gp['pads'] for q in done), key=lambda st: octd(*st))
            seq = None
            for m in (3.0, 8.0, 25.0):
                win = (min(src[1], tgt[1]) - m, max(src[1], tgt[1]) + m, min(src[2], tgt[2]) - m, max(src[2], tgt[2]) + m)
                seq = route(g, code, (src[1], src[2]), src[3], [(tgt[1], tgt[2], tgt[3])], {}, res, win)
                if seq is not None:
                    break
            if seq is None:
                print(f'{net}: FAILED {src[0]} -> {tgt[0]}', flush=True)
                ok = False
                done.extend(gp['pads'])
                continue
            ps, vs = simplify(seq)
            for l, pts in ps:
                g.add_path(code, l, pts)
                polys.append((l, pts, src[0], tgt[0]))
            for v in vs:
                g.add_via(code, v)
                vias.append(v)
            done.extend(gp['pads'])
            L = sum(math.dist(a, c) for _, p in ps for a, c in zip(p, p[1:]))
            print(f'{net}: {src[0]} -> {tgt[0]}: {len(ps)} polylines, {len(vs)} vias, {L:.2f} mm '
                  f'(octilinear {octd(src, tgt):.2f})', flush=True)
        results[net] = {'ok': ok, 'polys': polys, 'vias': vias}
        json.dump(results, open(out_path, 'w'), indent=1)


if __name__ == '__main__':
    main()
