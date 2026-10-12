"""Deterministic grid router for R5's scripted critical copper (docs/M3_R5.md "How R5 is built").

maze(b, net, layer, a, c, w) finds a path for one connection on one copper layer between two points that
the caller chose (pad centres, or vias the caller places), on a 0.1 mm grid with eight directions, so every
segment is 0, 45 or 90 degrees. Moves are charged their length plus a penalty per change of direction, so
paths are straight runs, not staircases. Obstacles are every other net's tracks, vias and pads on that layer,
the outlines of other nets' power pours and In2 islands (the GND and 3V3/3V3A pours are filled afterwards
and adapt, and so does a power pour round pads of the net being routed, such as BAT_IN_F round the damper),
the board edge (0.5 mm) and holes. The clearance to each obstacle is the larger of 0.15 mm and the pyro
spacing rules of m3.kicad_dru (A-G, A2) for that pair of nets, plus 0.05 mm; DRC checks the result. The
caller decides layers, vias and endpoints; this only draws the copper between them.
"""
import heapq
import math
from collections import deque

import pcbnew

mm, MM = pcbnew.ToMM, pcbnew.FromMM
G = 0.1                                           # grid (mm)
GATES = {'PYRO1_GATE', 'PYRO2_GATE', 'PYRO1_GATE_N', 'PYRO2_GATE_N'}
SENSES = {'ARM1_SENSE', 'ARM2_SENSE', 'PYRO1_CONT', 'PYRO2_CONT', 'PYRO1_COLD', 'PYRO2_COLD', 'PYRO1_CONT_MID',
          'PYRO2_CONT_MID', 'ARM1_SENSE_MID', 'ARM2_SENSE_MID'}
BUSIGN = {'PYRO1_BUS', 'PYRO2_BUS', 'PYRO1_IGN', 'PYRO2_IGN'}
BUSDRAIN = BUSIGN | {'PYRO1_OUT', 'PYRO2_OUT'}
CH = {n: ('1' if '1' in n else '2') for n in GATES | BUSDRAIN}
PLANES_AFTER = {'3V3', '3V3A'}
MARGIN = 0.05          # mm over the rule: the grid's 0.1 mm cells test clearance at their centres
PASSABLE_IN2 = set()   # In2 islands whose fill may clear round new copper (r5_post.return_vias sets it)


BLOCK = (4.0, 66.0, 42.0, 96.4)                  # the PYRO_BLOCK rule area (rule G's scope)
# Pin-escape bands (set by r5_pcb before the scripted routes): (layer, (x0, y0, x1, y1), axis, ref). Inside a band
# only a net's own pins of footprint `ref` may be left, straight along `axis`, so no scripted route runs along a
# fine-pitch pin row and boxes in the pins the autorouter has still to take out.
BANDS = []


def rule_clearance(a, c, in_block=True):
    """Minimum copper clearance between nets a and c from m3.kicad_dru's pyro rules (board default 0.15),
    plus MARGIN. Rule G (gate nets 0.3 mm from other live nets) applies inside the PYRO_BLOCK area."""
    best = 0.15
    for x, y in ((a, c), (c, a)):
        if x == 'RAW_ACT' and (y in GATES or y in SENSES):
            best = max(best, 0.5)
        if x == 'RAW_ACT' and y == 'RAW_ACT_SENSE':
            best = max(best, 0.3)
        if x in BUSDRAIN and y in GATES:
            best = max(best, 0.5)
        if x in BUSDRAIN and y in SENSES:
            best = max(best, 0.3)
        if x == 'GND' and y in BUSDRAIN:
            best = max(best, 0.5)
        if x == 'RAW_ACT' and y in BUSIGN:
            best = max(best, 1.0)
        if x in BUSDRAIN and y not in ('', 'GND') and y not in SENSES and y not in GATES and \
                not (y in BUSDRAIN and CH[x] == CH[y]) and not (x in BUSIGN and y == 'RAW_ACT'):
            best = max(best, 0.5)
        if in_block and x in GATES and y not in ('', 'GND', 'RAW_ACT') and y not in BUSDRAIN and \
                not (y in GATES and CH[x] == CH[y]):
            best = max(best, 0.3)
    return best + MARGIN


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


class Grid:
    def __init__(self, b, net, layer, box, w, origin, skip=None):
        """skip: uuids of tracks and vias to leave out (autorouted copper a rip-up may remove)."""
        self.x0 = origin[0] - math.ceil((origin[0] - box[0]) / G) * G      # the start point is a grid node
        self.y0 = origin[1] - math.ceil((origin[1] - box[1]) / G) * G
        self.nx = int(round((box[2] - self.x0) / G)) + 1
        self.ny = int(round((box[3] - self.y0) / G)) + 1
        self.blk = bytearray(self.nx * self.ny)
        hw = w / 2

        def inb(x0, y0, x1, y1):
            return x1 >= BLOCK[0] - 1 and x0 <= BLOCK[2] + 1 and y1 >= BLOCK[1] - 1 and y0 <= BLOCK[3] + 1
        bb = pcbnew.BOX2I(pcbnew.VECTOR2I(MM(box[0] - 3), MM(box[1] - 3)), pcbnew.VECTOR2L(MM(box[2] - box[0] + 6),
                                                                                     MM(box[3] - box[1] + 6)))

        def mark(x0, y0, x1, y1, fn):
            i0, i1 = max(0, int((x0 - self.x0) / G) - 1), min(self.nx - 1, int((x1 - self.x0) / G) + 1)
            j0, j1 = max(0, int((y0 - self.y0) / G) - 1), min(self.ny - 1, int((y1 - self.y0) / G) + 1)
            for j in range(j0, j1 + 1):
                y = self.y0 + j * G
                row = j * self.nx
                for i in range(i0, i1 + 1):
                    if not self.blk[row + i] and fn(self.x0 + i * G, y):
                        self.blk[row + i] = 1

        for t in b.GetTracks():
            if t.GetNetname() == net or not bb.Intersects(t.GetBoundingBox()):
                continue
            if skip and t.m_Uuid.AsString() in skip:
                continue
            tb = t.GetBoundingBox()
            k = rule_clearance(net, t.GetNetname(), inb(mm(tb.GetX()), mm(tb.GetY()), mm(tb.GetRight()),
                                                        mm(tb.GetBottom()))) + hw
            if t.GetClass() == 'PCB_VIA':
                cx, cy, r = mm(t.GetPosition().x), mm(t.GetPosition().y), mm(t.GetWidth(pcbnew.F_Cu)) / 2 + k
                mark(cx - r, cy - r, cx + r, cy + r, lambda x, y: math.hypot(x - cx, y - cy) < r)
            elif t.GetLayer() == layer:
                ax, ay, cx, cy = mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y)
                r = mm(t.GetWidth()) / 2 + k
                mark(min(ax, cx) - r, min(ay, cy) - r, max(ax, cx) + r, max(ay, cy) + r,
                     lambda x, y: _seg_dist(x, y, ax, ay, cx, cy) < r)
        for f in b.GetFootprints():
            if not bb.Intersects(f.GetBoundingBox(False)):
                continue
            for p in f.Pads():
                if p.GetNetname() == net and p.GetNetname() != '':
                    continue
                if not (p.IsOnLayer(layer) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH):
                    continue
                pb = p.GetBoundingBox()
                x0, y0, x1, y1 = mm(pb.GetX()), mm(pb.GetY()), mm(pb.GetRight()), mm(pb.GetBottom())
                k = rule_clearance(net, p.GetNetname(), inb(x0, y0, x1, y1)) + hw
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:  # a bare hole: m3.kicad_dru's 0.25 mm to copper
                    k = max(k, 0.25 + MARGIN + hw)
                mark(x0 - k, y0 - k, x1 + k, y1 + k,
                     lambda x, y: math.hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1)) < k)
        own = [p.GetPosition() for f in b.GetFootprints() for p in f.Pads()
               if net and p.GetNetname() == net and p.IsOnLayer(layer)]
        for z in b.Zones():
            if z.GetIsRuleArea():
                if z.IsOnLayer(layer) and z.GetDoNotAllowTracks():
                    o = z.Outline()
                    zb = z.GetBoundingBox()
                    mark(mm(zb.GetX()), mm(zb.GetY()), mm(zb.GetRight()), mm(zb.GetBottom()),
                         lambda x, y: o.Contains(pcbnew.VECTOR2I(MM(x), MM(y))))
                continue
            if not z.IsOnLayer(layer) or z.GetNetname() in (net, 'GND', *PLANES_AFTER):
                continue                                     # the GND and 3V3/3V3A pours fill round the routes
            if layer == pcbnew.In2_Cu and z.GetNetname() in PASSABLE_IN2:
                continue
            if layer in (pcbnew.F_Cu, pcbnew.B_Cu) and any(z.Outline().Contains(q) for q in own):
                continue                                     # an outer pour round this net's own pads fills round its routes
            k = max(rule_clearance(net, z.GetNetname()), mm(z.GetLocalClearance() or 0) + 0.05) + hw
            o = z.Outline()                              # (the pour's own clearance: a via must not neck it)
            zb = z.GetBoundingBox()
            mark(mm(zb.GetX()) - k, mm(zb.GetY()) - k, mm(zb.GetRight()) + k, mm(zb.GetBottom()) + k,
                 lambda x, y: o.Contains(pcbnew.VECTOR2I(MM(x), MM(y))) or
                 o.SquaredDistance(pcbnew.VECTOR2I(MM(x), MM(y))) < MM(k) ** 2)
        for blay, (bx0, by0, bx1, by1), axis, ref in BANDS:
            if blay != layer:
                continue
            own = [(mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in b.FindFootprintByReference(ref).Pads()
                   if net and p.GetNetname() == net]
            for j in range(self.ny):                      # the band, less a straight corridor out of each own pin
                y = self.y0 + j * G
                if not (by0 <= y <= by1):
                    continue
                for i in range(self.nx):
                    x = self.x0 + i * G
                    if bx0 <= x <= bx1 and not any((axis == 'x' and abs(y - py) < G * 0.6) or
                                                   (axis == 'y' and abs(x - px) < G * 0.6) for px, py in own):
                        self.blk[j * self.nx + i] = 1
        eb = b.GetBoardEdgesBoundingBox()
        ex0, ey0, ex1, ey1 = mm(eb.GetX()), mm(eb.GetY()), mm(eb.GetRight()), mm(eb.GetBottom())
        m = 0.5 + hw
        mark(self.x0, self.y0, self.x0 + self.nx * G, self.y0 + self.ny * G,
             lambda x, y: x < ex0 + m or x > ex1 - m or y < ey0 + m or y > ey1 - m)
        for d in b.GetDrawings():
            if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                cx, cy, r = mm(d.GetCenter().x), mm(d.GetCenter().y), mm(d.GetRadius()) + 0.5 + hw
                mark(cx - r, cy - r, cx + r, cy + r, lambda x, y: math.hypot(x - cx, y - cy) < r)

    def cell(self, x, y):
        return int(round((x - self.x0) / G)), int(round((y - self.y0) / G))

    def xy(self, i, j):
        return round(self.x0 + i * G, 4), round(self.y0 + j * G, 4)


DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
# turn cost in units of `turn`, by the change of direction in 45 degree steps: a 135 degree turn (an acute corner,
# AGENTS.md) costs as much as about 3.6 mm of extra track at the default turn cost, so it is taken only where
# nothing else fits; a reversal (a spike) is never taken
TURN = {0: 0, 1: 1, 7: 1, 2: 2, 6: 2, 3: 12, 5: 12}


def maze(b, net, layer, a, c, w=0.2, margin=8.0, turn=3.0, box=None):
    """Route net on layer from a to c; returns the polyline. The grid is anchored at a; if c is off that
    lattice the path ends at the nearest node and a 45 + 0/90 deg dog-leg under 0.1 mm reaches c. Turns cost
    `turn` times TURN (acute corners only where nothing else fits, no reversals)."""
    if box is None:
        box = (min(a[0], c[0]) - margin, min(a[1], c[1]) - margin, max(a[0], c[0]) + margin, max(a[1], c[1]) + margin)
    g = Grid(b, net, layer, box, w, a)
    s, t = g.cell(*a), g.cell(*c)
    nx = g.nx
    for (ci, cj) in (s, t):                        # the end cells themselves (own pad or via) stay usable
        if 0 <= ci < g.nx and 0 <= cj < g.ny:
            g.blk[cj * nx + ci] = 0
    INF = float('inf')
    best = {}
    h = lambda i, j: (math.hypot(i - t[0], j - t[1]))  # noqa: E731
    pq = [(h(*s), 0.0, s[0], s[1], -1, None)]
    parent = {}
    while pq:
        f, gc, i, j, d, par = heapq.heappop(pq)
        key = (i, j, d)
        if best.get(key, INF) <= gc and key in parent:
            continue
        best[key] = gc
        parent[key] = par
        if (i, j) == t:
            pts = []
            k = key
            while k is not None:
                pts.append(g.xy(k[0], k[1]))
                k = parent[k]
            pts.reverse()
            out = [pts[0]]
            for p, q, r in zip(pts, pts[1:], pts[2:]):
                if (q[0] - p[0], q[1] - p[1]) != (r[0] - q[0], r[1] - q[1]):
                    out.append(q)
            out.append(pts[-1])
            out = _clean(out)
            out[0] = (a[0], a[1])
            end = out[-1]
            dx, dy = c[0] - end[0], c[1] - end[1]
            if abs(dx) > 1e-6 or abs(dy) > 1e-6:
                m = min(abs(dx), abs(dy))
                knee = (end[0] + math.copysign(m, dx), end[1] + math.copysign(m, dy))
                for q in (knee, (c[0], c[1])):
                    if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 1e-6:
                        out.append(q)
            return out
        for nd, (di, dj) in enumerate(DIRS):
            if d != -1 and (nd - d) % 8 == 4:
                continue
            ii, jj = i + di, j + dj
            if not (0 <= ii < g.nx and 0 <= jj < g.ny) or g.blk[jj * nx + ii]:
                continue
            step = 1.41421356 if di and dj else 1.0
            cost = gc + step + (0 if d == -1 else turn * TURN[(nd - d) % 8])
            nk = (ii, jj, nd)
            if cost < best.get(nk, INF):
                best[nk] = cost
                heapq.heappush(pq, (cost + h(ii, jj), cost, ii, jj, nd, key))
    raise RuntimeError(f'maze: no path for {net} on {pcbnew.LayerName(layer)} from {a} to {c}')


def _clean(pts):
    """Merge collinear points (direction computed on the rounded grid)."""
    out = [pts[0]]
    for q in pts[1:]:
        if len(out) >= 2:
            p0, p1 = out[-2], out[-1]
            d1 = (round((p1[0] - p0[0]) / G), round((p1[1] - p0[1]) / G))
            d2 = (round((q[0] - p1[0]) / G), round((q[1] - p1[1]) / G))
            n1 = max(abs(d1[0]), abs(d1[1])) or 1
            n2 = max(abs(d2[0]), abs(d2[1])) or 1
            if (d1[0] / n1, d1[1] / n1) == (d2[0] / n2, d2[1] / n2):
                out[-1] = q
                continue
        out.append(q)
    return out


def via_spot(b, net, near, anchor, d=0.6, drill=0.3, r=2.5, exclude=()):
    """Nearest point to `near`, on the 0.1 mm lattice through `anchor`, where a through via of net keeps
    the rule clearances to everything on every copper layer (and 0.3 mm hole-to-copper), and stays 0.15 mm off
    its own net's SMD pads (no via-in-pad: JLC Standard does not fill vias)."""
    box = (near[0] - r - 1, near[1] - r - 1, near[0] + r + 1, near[1] + r + 1)
    grids = [Grid(b, net, lay, box, d, anchor) for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)]
    if net == 'GND':
        grids = [grids[0], grids[2], grids[3]]
    g0 = grids[0]
    ci, cj = g0.cell(*near)
    cands = []
    n = int(r / G)
    for dj in range(-n, n + 1):
        for di in range(-n, n + 1):
            i, j = ci + di, cj + dj
            if 0 <= i < g0.nx and 0 <= j < g0.ny:
                cands.append((math.hypot(di, dj), i, j))
    cands.sort()
    vias = [(mm(v.GetPosition().x), mm(v.GetPosition().y)) for v in b.GetTracks() if v.GetClass() == 'PCB_VIA']
    holes = [(mm(q.GetPosition().x), mm(q.GetPosition().y), mm(max(q.GetDrillSize().x, q.GetDrillSize().y)) / 2)
             for f in b.GetFootprints() for q in f.Pads()
             if q.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)]
    novia = [z.Outline() for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    for _, i, j in cands:
        if all(not g.blk[j * g.nx + i] for g in grids):
            x, y = g0.xy(i, j)
            if any(abs(x - ex) < 1e-6 and abs(y - ey) < 1e-6 for ex, ey in exclude):
                continue
            if any(o.Contains(pcbnew.VECTOR2I(MM(x), MM(y))) or
                   o.SquaredDistance(pcbnew.VECTOR2I(MM(x), MM(y))) < MM(d / 2) ** 2 for o in novia):
                continue                                  # keep-out (MEMS bodies)
            if any(math.hypot(x - vx, y - vy) < d + 0.15 for vx, vy in vias):   # hole-to-hole, same net too
                continue
            if any(math.hypot(x - hx, y - hy) < drill / 2 + hr + 0.3 for hx, hy, hr in holes):
                continue                                  # hole-to-hole with through-hole pins (0.25 mm, any net)
            # hole-to-copper (0.25 mm, m3.kicad_dru) against other nets' pads
            ok = True
            for f in b.GetFootprints():
                for p in f.Pads():
                    pb = p.GetBoundingBox()
                    dd = math.hypot(max(mm(pb.GetX()) - x, 0, x - mm(pb.GetRight())),
                                    max(mm(pb.GetY()) - y, 0, y - mm(pb.GetBottom())))
                    if p.GetNetname() == net and net:
                        if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and dd < d / 2 + 0.15:
                            ok = False                # no via in, or touching, its own SMD pad (solder wicking)
                            break
                        continue
                    if dd < drill / 2 + 0.3:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return x, y
    raise RuntimeError(f'via_spot: no place for a {net} via near {near}')


def _via_blocked(b, net, box, origin, d=0.6, drill=0.3, skip=None):
    """Cells of the grid anchored at `origin` where a through via of net may not go (the via_spot rules)."""
    grids = [Grid(b, net, lay, box, d, origin, skip) for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
                                                                  pcbnew.B_Cu)]
    if net == 'GND':
        grids = [grids[0], grids[2], grids[3]]
    g0 = grids[0]
    blk = bytearray(g0.nx * g0.ny)
    for g in grids:
        for k, v in enumerate(g.blk):
            if v:
                blk[k] = 1

    def mark(cx, cy, r, rect=None):
        x0, y0, x1, y1 = rect if rect else (cx, cy, cx, cy)
        i0, i1 = max(0, int((x0 - r - g0.x0) / G) - 1), min(g0.nx - 1, int((x1 + r - g0.x0) / G) + 1)
        j0, j1 = max(0, int((y0 - r - g0.y0) / G) - 1), min(g0.ny - 1, int((y1 + r - g0.y0) / G) + 1)
        for j in range(j0, j1 + 1):
            y = g0.y0 + j * G
            for i in range(i0, i1 + 1):
                x = g0.x0 + i * G
                if math.hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1)) < r:
                    blk[j * g0.nx + i] = 1
    for v in b.GetTracks():
        if v.GetClass() == 'PCB_VIA' and not (skip and v.m_Uuid.AsString() in skip):
            mark(mm(v.GetPosition().x), mm(v.GetPosition().y), d + 0.15)       # hole to hole, same net too
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias():                       # keep-outs (MEMS bodies)
            o, zb = z.Outline(), z.GetBoundingBox()
            zx0, zy0, zx1, zy1 = mm(zb.GetX()), mm(zb.GetY()), mm(zb.GetRight()), mm(zb.GetBottom())
            for j in range(max(0, int((zy0 - d - g0.y0) / G)), min(g0.ny, int((zy1 + d - g0.y0) / G) + 1)):
                for i in range(max(0, int((zx0 - d - g0.x0) / G)), min(g0.nx, int((zx1 + d - g0.x0) / G) + 1)):
                    q = pcbnew.VECTOR2I(MM(g0.x0 + i * G), MM(g0.y0 + j * G))
                    if o.Contains(q) or o.SquaredDistance(q) < MM(d / 2) ** 2:
                        blk[j * g0.nx + i] = 1
    for f in b.GetFootprints():
        for p in f.Pads():
            pb = p.GetBoundingBox()
            rect = (mm(pb.GetX()), mm(pb.GetY()), mm(pb.GetRight()), mm(pb.GetBottom()))
            if rect[2] < box[0] - 2 or rect[0] > box[2] + 2 or rect[3] < box[1] - 2 or rect[1] > box[3] + 2:
                continue
            if p.GetNetname() == net and net:
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    mark(0, 0, d / 2 + 0.15, rect)          # no via in or touching its own SMD pad
            else:
                mark(0, 0, drill / 2 + 0.3, rect)           # hole to other nets' copper
    return g0, blk


def maze_multi(b, net, layers, a, c, w=0.2, a_layers=None, c_layers=None, margin=8.0, turn=3.0, via_cost=15.0,
               soft=3.0, box=None, rip=None, rip_cost=6.0, targets=None):
    """maze() over several copper layers joined by through vias (0.6/0.3, placed by the via_spot rules).
    a_layers/c_layers: the layers each end may be on (default all). Cells of the 3V3/3V3A pours on In2 cost
    `soft` times more, so a route crosses them rather than running inside them. rip: uuids of copper the route
    may cross at `rip_cost` per cell (r5_finish then removes what it crosses and routes that again). targets:
    instead of c, any of these (x, y, layer) grid points may end the route (r5_finish: every point inside the copper
    of the island to reach); c then only sizes the box. Returns (runs, vias): runs is a list of (layer, polyline),
    vias the points where the route changes layer."""
    if box is None:
        box = (min(a[0], c[0]) - margin, min(a[1], c[1]) - margin, max(a[0], c[0]) + margin, max(a[1], c[1]) + margin)
    grids = [Grid(b, net, lay, box, w, a) for lay in layers]
    g0, vblk = _via_blocked(b, net, box, a)
    if rip:                                           # the same obstacles without the copper that may be ripped
        sgrids = [Grid(b, net, lay, box, w, a, rip) for lay in layers]
        _, vsoft = _via_blocked(b, net, box, a, skip=rip)
    nx, ny, n = g0.nx, g0.ny, len(layers)
    softc = [bytearray(nx * ny) for _ in layers]
    for li, lay in enumerate(layers):
        for z in b.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(lay) or z.GetNetname() not in PLANES_AFTER:
                continue
            o = z.Outline()
            zb = z.GetBoundingBox()
            i0, i1 = max(0, int((mm(zb.GetX()) - g0.x0) / G) - 1), min(nx - 1, int((mm(zb.GetRight()) - g0.x0) / G) + 1)
            j0, j1 = max(0, int((mm(zb.GetY()) - g0.y0) / G) - 1), min(ny - 1, int((mm(zb.GetBottom()) - g0.y0) / G) + 1)
            for j in range(j0, j1 + 1):
                y = g0.y0 + j * G
                for i in range(i0, i1 + 1):
                    if o.Contains(pcbnew.VECTOR2I(MM(g0.x0 + i * G), MM(y))):
                        softc[li][j * nx + i] = 1
    s, t = g0.cell(*a), g0.cell(*c)
    al = [k for k, lay in enumerate(layers) if a_layers is None or lay in a_layers]
    cl = {k for k, lay in enumerate(layers) if c_layers is None or lay in c_layers}
    tset = None
    if targets:
        tset = {}
        for x, y, lay in targets:
            if lay in layers:
                ti, tj = g0.cell(x, y)
                if 0 <= ti < nx and 0 <= tj < ny:
                    tset[(ti, tj, layers.index(lay))] = (x, y)
        if not tset:
            raise RuntimeError(f'maze_multi: no target inside the box for {net}')
        tx = [k[0] for k in tset]
        ty = [k[1] for k in tset]
        tb = (min(tx), min(ty), max(tx), max(ty))
    for g in grids + (sgrids if rip else []):
        for (ci, cj) in (s, t):
            if 0 <= ci < nx and 0 <= cj < ny:
                g.blk[cj * nx + ci] = 0
    if not _reachable(grids, sgrids if rip else None, vblk, vsoft if rip else None, nx, ny, s, t, al, cl, tset):
        raise RuntimeError(f'maze_multi: no path for {net} from {a} to {c}')
    INF = float('inf')
    best, parent = {}, {}
    if tset:                                          # distance to the targets' bounding box (admissible)
        h = lambda i, j: math.hypot(max(tb[0] - i, 0, i - tb[2]), max(tb[1] - j, 0, j - tb[3]))  # noqa: E731
    else:
        h = lambda i, j: math.hypot(i - t[0], j - t[1])  # noqa: E731
    pq = [(h(*s), 0.0, s[0], s[1], k, -1, None) for k in al]
    heapq.heapify(pq)
    while pq:
        f, gc, i, j, li, d, par = heapq.heappop(pq)
        key = (i, j, li, d)
        if key in parent:
            continue
        parent[key] = par
        if (tset is not None and (i, j, li) in tset) or (tset is None and (i, j) == t and li in cl):
            seq = []
            k = key
            while k is not None:
                seq.append(k)
                k = parent[k]
            seq.reverse()
            return _runs(g0, layers, seq, a, tset[(i, j, li)] if tset is not None else c)   # exact target point
        blk = grids[li].blk
        for nd, (di, dj) in enumerate(DIRS):
            if d != -1 and (nd - d) % 8 == 4:
                continue
            ii, jj = i + di, j + dj
            if not (0 <= ii < nx and 0 <= jj < ny):
                continue
            extra = 0.0
            if blk[jj * nx + ii]:
                if not rip or sgrids[li].blk[jj * nx + ii]:
                    continue
                extra = rip_cost
            step = 1.41421356 if di and dj else 1.0
            if softc[li][jj * nx + ii]:
                step *= soft
            cost = gc + step + extra + (0 if d == -1 else turn * TURN[(nd - d) % 8])
            nk = (ii, jj, li, nd)
            if cost < best.get(nk, INF):
                best[nk] = cost
                heapq.heappush(pq, (cost + h(ii, jj), cost, ii, jj, li, nd, key))
        k0 = j * nx + i
        vfree = not vblk[k0] or (rip and not vsoft[k0])
        if vfree and (i, j) not in (s, t):
            vx = 0.0 if not vblk[k0] else rip_cost * 6
            for lj in range(n):
                hard = grids[lj].blk[k0]
                if lj != li and (not hard or (rip and not sgrids[lj].blk[k0])):
                    nk = (i, j, lj, -1)
                    cost = gc + via_cost + vx + (rip_cost if hard else 0.0)
                    if cost < best.get(nk, INF):
                        best[nk] = cost
                        heapq.heappush(pq, (cost + h(i, j), cost, i, j, lj, -1, key))
    raise RuntimeError(f'maze_multi: no path for {net} from {a} to {c}')


def _reachable(grids, sgrids, vblk, vsoft, nx, ny, s, t, al, cl, tset):
    """Whether maze_multi's search can reach an end at all: a flood fill over cells and layers with every move
    the search allows (costs and directions aside), so a connection with no path fails without the full search."""
    n = len(grids)
    nn = nx * ny
    free = [bytearray(1 if not grids[li].blk[k] or (sgrids is not None and not sgrids[li].blk[k]) else 0
                      for k in range(nn)) for li in range(n)]
    vok = bytearray(1 if not vblk[k] or (vsoft is not None and not vsoft[k]) else 0 for k in range(nn))
    for ci, cj in (s, t):                             # the ends are free on every layer (as in the search)
        if 0 <= ci < nx and 0 <= cj < ny:
            for li in range(n):
                free[li][cj * nx + ci] = 1
    ends = {(cj * nx + ci) for ci, cj in (s, t) if 0 <= ci < nx and 0 <= cj < ny}
    if tset is not None:
        goal = {li * nn + tj * nx + ti for ti, tj, li in tset}
    else:
        goal = {li * nn + t[1] * nx + t[0] for li in cl} if 0 <= t[0] < nx and 0 <= t[1] < ny else set()
    seen = bytearray(n * nn)
    q = deque()
    for li in al:
        k = li * nn + s[1] * nx + s[0]
        seen[k] = 1
        q.append(k)
    while q:
        k = q.popleft()
        if k in goal:
            return True
        li, k0 = divmod(k, nn)
        j, i = divmod(k0, nx)
        f = free[li]
        base = li * nn
        for di, dj in DIRS:
            ii, jj = i + di, j + dj
            if 0 <= ii < nx and 0 <= jj < ny:
                k1 = jj * nx + ii
                if f[k1] and not seen[base + k1]:
                    seen[base + k1] = 1
                    q.append(base + k1)
        if vok[k0] and k0 not in ends:
            for lj in range(n):
                if lj != li and free[lj][k0] and not seen[lj * nn + k0]:
                    seen[lj * nn + k0] = 1
                    q.append(lj * nn + k0)
    return False


def _runs(g, layers, seq, a, c):
    runs, vias, cur = [], [], []
    for k, (i, j, li, d) in enumerate(seq):
        if cur and li != cur[-1][2]:
            runs.append(cur)
            vias.append(g.xy(i, j))
            cur = []
        cur.append((i, j, li))
    runs.append(cur)
    out = []
    for r, run in enumerate(runs):
        pts = [g.xy(i, j) for i, j, _ in run]
        q = [pts[0]]
        for p0, p1, p2 in zip(pts, pts[1:], pts[2:]):
            if (p1[0] - p0[0], p1[1] - p0[1]) != (p2[0] - p1[0], p2[1] - p1[1]):
                q.append(p1)
        if len(pts) > 1:
            q.append(pts[-1])
        q = _clean(q)
        if r == 0:
            q[0] = (a[0], a[1])
        if r == len(runs) - 1:
            end = q[-1]
            dx, dy = c[0] - end[0], c[1] - end[1]
            if abs(dx) > 1e-6 or abs(dy) > 1e-6:
                m = min(abs(dx), abs(dy))
                knee = (end[0] + math.copysign(m, dx), end[1] + math.copysign(m, dy))
                for p in (knee, (c[0], c[1])):
                    if math.hypot(p[0] - q[-1][0], p[1] - q[-1][1]) > 1e-6:
                        q.append(p)
        out.append((layers[run[0][2]], q))
    return out, vias
