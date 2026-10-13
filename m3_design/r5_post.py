#!/usr/bin/env python3
"""M3-ASSY-R5 finishing after the autorouter (docs/M3_R5.md "How R5 is built").

usage: <KiCad python3> m3_design/r5_post.py [m3_design/assembly_review/m3.kicad_pcb]

Runs on the board that r5_pcb.py made, r5_route.py import filled with the Freerouting session and r5_finish.py
completed:
  1. track clean-up: zero-length, duplicate and covered segments, collinear fragments (R4's m_track_cleanup);
  2. pours: the In2 3V3 fill grows under the USB pair (usb_reference), GND stitching vias join the outer GND pours
     to the In1 plane (stitch), a GND via goes next to each critical layer change that has none (return_vias),
     and every GND island the grid missed gets its own via (island_vias);
  3. silkscreen: the terminal, arming, connector, servo, UART and battery legends (REQUIREMENTS F8, AGENTS.md),
     pin-1 dots for the ICs whose footprints carry none (R4 m_pin1_marks), JLC's order-number placeholder and
     the revision legend, then every designator by the R4 rule (AGENTS.md: legible, never over a pad or off the
     board, nearer its own part than any other, clear of vias; a top part may put it on the bottom under itself;
     one with no such spot is hidden, kept on F.Fab and listed in docs/M3_R5.md);
  4. fab-layer designators for the assembly drawing (R4 z_fab_refs);
  5. title block M3-ASSY-R5, zone refill.
Idempotent: legends and dots it made earlier (board-level silkscreen) are deleted first.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pcbnew

PCB = sys.argv[1] if len(sys.argv) > 1 else 'm3_design/assembly_review/m3.kicad_pcb'
mm, MM = pcbnew.ToMM, pcbnew.FromMM
W, L = 46.0, 100.0
REV = 'M3-ASSY-R5'
GAP = 0.15                     # silkscreen to pads, vias, holes and other silkscreen
EDGE = 0.3                     # silkscreen inside the outline
CELL = 2.0                     # spatial index (mm)


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def fp_of(b, ref):
    f = b.FindFootprintByReference(ref)
    assert f is not None, ref
    return f


def pad(b, ref, num):
    p = next(q for q in fp_of(b, ref).Pads() if q.GetNumber() == num)
    return mm(p.GetPosition().x), mm(p.GetPosition().y)


def bx(item):
    r = item.GetBoundingBox()
    return mm(r.GetX()), mm(r.GetY()), mm(r.GetRight()), mm(r.GetBottom())


def ink(t):
    """The box of a text's strokes (DRC tests the strokes; GetBoundingBox adds about 0.5 mm of font cell)."""
    ps = pcbnew.SHAPE_POLY_SET()
    t.TransformShapeToPolygon(ps, t.GetLayer(), 0, MM(0.005), pcbnew.ERROR_INSIDE)
    r = ps.BBox()
    return mm(r.GetX()), mm(r.GetY()), mm(r.GetRight()), mm(r.GetBottom())


# --- 1. track clean-up ---------------------------------------------------------------------------

def _in_block(t):
    """The track touches the PYRO_BLOCK rule area (m3.kicad_dru rule G's scope)."""
    import r5_maze
    x0, y0, x1, y1 = r5_maze.BLOCK
    hw = mm(t.GetWidth()) / 2
    ax, ay, cx, cy = mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y)
    return max(ax, cx) + hw >= x0 and min(ax, cx) - hw <= x1 and max(ay, cy) + hw >= y0 and min(ay, cy) - hw <= y1


def close_joints(b):
    """Two ends of one net's tracks on one layer that nearly meet (closer than the wider track) but are not the same
    point, with neither end on a pad, a via or another track's body, join only where their round ends overlap: pass 4
    found a PULLPIN joint 0.06 mm wide, which can etch open. Each such gap gets a bridging segment when it runs at
    0/45/90 degrees (and is reported otherwise)."""
    tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vias = [v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA']
    pads = [q for f in b.GetFootprints() for q in f.Pads()]

    def seg_dist(x, y, t):
        s, e = t.GetStart(), t.GetEnd()
        vx, vy = e.x - s.x, e.y - s.y
        ll = vx * vx + vy * vy
        u = 0 if ll == 0 else max(0.0, min(1.0, ((x - s.x) * vx + (y - s.y) * vy) / ll))
        return math.hypot(s.x + u * vx - x, s.y + u * vy - y)

    def covered(x, y, net, lay):
        pt = pcbnew.VECTOR2I(x, y)
        if any(v.GetNetname() == net and (v.GetPosition() - pt).EuclideanNorm() <= v.GetWidth(lay) / 2 for v in vias):
            return True
        if any(q.GetNetname() == net and q.IsOnLayer(lay) and q.HitTest(pt) for q in pads):
            return True
        return any(t.GetNetname() == net and t.GetLayer() == lay and pt not in (t.GetStart(), t.GetEnd())
                   and seg_dist(x, y, t) <= t.GetWidth() / 2 for t in tracks)
    ends = {}
    for t in tracks:
        for q in (t.GetStart(), t.GetEnd()):
            ends.setdefault((t.GetNetname(), t.GetLayer()), {})
            w = ends[(t.GetNetname(), t.GetLayer())]
            w[(q.x, q.y)] = max(t.GetWidth(), w.get((q.x, q.y), 0))
    done, odd = 0, []
    for (net, lay), width in ends.items():
        uniq = sorted(width)
        for i, (ax, ay) in enumerate(uniq):
            for bx_, by_ in uniq[i + 1:]:
                if bx_ - ax > MM(0.5):
                    break
                dx, dy = bx_ - ax, by_ - ay
                if not 0 < math.hypot(dx, dy) < max(width[(ax, ay)], width[(bx_, by_)]):
                    continue
                if covered(ax, ay, net, lay) or covered(bx_, by_, net, lay):
                    continue
                if not (dx == 0 or dy == 0 or abs(abs(dx) - abs(dy)) <= 2):
                    odd.append((net, round(mm(ax), 3), round(mm(ay), 3)))
                    continue
                s = pcbnew.PCB_TRACK(b)
                s.SetStart(pcbnew.VECTOR2I(ax, ay))
                s.SetEnd(pcbnew.VECTOR2I(bx_, by_))
                s.SetWidth(min(width[(ax, ay)], width[(bx_, by_)]))
                s.SetLayer(lay)
                s.SetNet(b.FindNet(net))
                b.Add(s)
                done += 1
    print(f'  overlap-only joints bridged: {done}; off-angle, left: {odd or "none"}')


def track_cleanup(b):
    tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    dead, seen = [], set()
    for t in tracks:
        s, e = t.GetStart(), t.GetEnd()
        if s.x == e.x and s.y == e.y:
            dead.append(t)
            continue
        key = (t.GetNetname(), t.GetLayer(), t.GetWidth()) + tuple(sorted(((s.x, s.y), (e.x, e.y))))
        if key in seen:
            dead.append(t)
        seen.add(key)
    for t in dead:
        b.Delete(t)
    vias = {(v.GetPosition().x, v.GetPosition().y) for v in b.GetTracks() if v.GetClass() == 'PCB_VIA'}
    padboxes = [(pd.GetBoundingBox(), pd) for f in b.GetFootprints() for pd in f.Pads()]
    merged, changed = 0, True
    while changed:
        changed = False
        ends = {}
        for t in b.GetTracks():
            if t.GetClass() != 'PCB_TRACK':
                continue
            for pt in (t.GetStart(), t.GetEnd()):
                ends.setdefault((t.GetLayer(), pt.x, pt.y), []).append(t)
        for (layer, x, y), ts in ends.items():
            if len(ts) != 2 or (x, y) in vias:
                continue
            a, c = ts
            if a.GetNetname() != c.GetNetname() or a.GetWidth() != c.GetWidth():
                continue
            pt = pcbnew.VECTOR2I(x, y)
            if any(pd.IsOnLayer(layer) and r.Contains(pt) for r, pd in padboxes):
                continue
            pa = a.GetEnd() if (a.GetStart().x, a.GetStart().y) == (x, y) else a.GetStart()
            pc = c.GetEnd() if (c.GetStart().x, c.GetStart().y) == (x, y) else c.GetStart()
            v1, v2 = (x - pa.x, y - pa.y), (pc.x - x, pc.y - y)
            if v1[0] * v2[1] - v1[1] * v2[0] != 0 or v1[0] * v2[0] + v1[1] * v2[1] <= 0:
                continue
            if _in_block(a) != _in_block(c):
                continue                               # DRC rule G applies to a whole track touching the block
            a.SetStart(pa)
            a.SetEnd(pc)
            b.Delete(c)
            merged += 1
            changed = True
            break
    segs = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vias = {(v.GetPosition().x, v.GetPosition().y) for v in b.GetTracks() if v.GetClass() == 'PCB_VIA'}
    endcount = {}
    for s_ in segs:
        for pt in (s_.GetStart(), s_.GetEnd()):
            k = (s_.GetLayer(), pt.x, pt.y)
            endcount[k] = endcount.get(k, 0) + 1

    def attached(t, pt):
        """Something besides t itself ends at pt: a via, a pad, another segment (keep t: it makes that joint)."""
        return (pt.x, pt.y) in vias or endcount.get((t.GetLayer(), pt.x, pt.y), 0) > 1 or \
            any(pd.IsOnLayer(t.GetLayer()) and r.Contains(pt) for r, pd in padboxes)
    covered = []
    for a in segs:
        if attached(a, a.GetStart()) or attached(a, a.GetEnd()):
            continue
        (ax, ay), (bx_, by_) = (mm(a.GetStart().x), mm(a.GetStart().y)), (mm(a.GetEnd().x), mm(a.GetEnd().y))
        for c in segs:
            if c is a or c in covered or c.GetNetname() != a.GetNetname() or c.GetLayer() != a.GetLayer() \
                    or c.GetWidth() < a.GetWidth():
                continue
            (cx, cy), (dx, dy) = (mm(c.GetStart().x), mm(c.GetStart().y)), (mm(c.GetEnd().x), mm(c.GetEnd().y))
            ln = math.hypot(dx - cx, dy - cy)
            if ln < 1e-6:
                continue
            ux, uy = (dx - cx) / ln, (dy - cy) / ln
            if all(abs((px - cx) * uy - (py - cy) * ux) < 1e-3 and -1e-3 <= (px - cx) * ux + (py - cy) * uy <= ln + 1e-3
                   for px, py in ((ax, ay), (bx_, by_))):
                covered.append(a)
                break
    for t in covered:
        b.Delete(t)
    print(f'  track clean-up: {len(dead)} zero-length/duplicate, {merged} collinear merges, {len(covered)} covered')


def pth_vias(b):
    """No via on a through-hole pad's copper or under 0.45 mm hole to hole from its hole (pass 2, D1: the router left a
    CAM_RX_WIRE via inside J9.3's pad, its hole in the pad's solder opening; DRC passes it, same net). Such a via is
    redundant (the pad reaches every layer): it goes, with the tracks that then lie wholly on the pad, as long as every
    other track that ended at it still ends on the pad's copper (a via beside the pad, whose tracks lead elsewhere, is
    reported and kept)."""
    pths = [p for f in b.GetFootprints() for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    removed, bad = 0, []
    for v in [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']:
        vp = v.GetPosition()
        for p in pths:
            hr = mm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2
            near = mm((vp - p.GetPosition()).EuclideanNorm()) < hr + mm(v.GetDrillValue()) / 2 + 0.45
            if p.GetNetname() != v.GetNetname() or not (near or p.HitTest(vp)):
                continue                                 # (another net's hole: DRC's hole clearance)
            at = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and vp in (t.GetStart(), t.GetEnd())]
            on_pad = lambda t: all(p.HitTest(q) for q in (t.GetStart(), t.GetEnd()))  # noqa: E731
            if not all(p.HitTest(vp) or on_pad(t) for t in at):
                bad.append((v.GetNetname(), round(mm(vp.x), 2), round(mm(vp.y), 2), p.GetParentFootprint().GetReference()))
                break
            for t in at:
                if on_pad(t):
                    b.Delete(t)
            b.Delete(v)
            removed += 1
            break
    print(f'  vias on through-hole pads removed: {removed}; kept beside one (own tracks elsewhere): {bad or "none"}')


def acute_corners(b):
    """AGENTS.md: no acute angles. At a free joint (two segments of one net meeting outside any pad or via) where the
    path turns by more than 90 degrees: a spike (the shorter segment lying back along the longer one) is trimmed off;
    a 45 degree wedge is cut by a segment from the shorter arm's far end square across to the longer arm (a 45 degree
    turn at that end, 90 at the other), kept only where the grid router's clearance grid (r5_maze.Grid, 0.05 mm
    margin) shows the cut clear and it makes no new acute turn where the shorter arm meets the next copper. Returns
    what is left."""
    import r5_maze
    vias = [(v.GetPosition(), v.GetWidth(pcbnew.F_Cu) / 2) for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]
    pads = [q for f in b.GetFootprints() for q in f.Pads()]

    def anchored(pt, lay):
        return any((pt.x - q.x) ** 2 + (pt.y - q.y) ** 2 < r * r for q, r in vias) or \
            any(q.IsOnLayer(lay) and q.HitTest(pt) for q in pads)

    def far_end(t, x, y):
        return t.GetEnd() if (t.GetStart().x, t.GetStart().y) == (x, y) else t.GetStart()

    def move_end(t, x, y, q):
        if (t.GetStart().x, t.GetStart().y) == (x, y):
            t.SetStart(q)
        else:
            t.SetEnd(q)

    spikes = cut = 0
    left, tried = [], set()
    while True:
        ends = {}
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_TRACK':
                for q in (t.GetStart(), t.GetEnd()):
                    ends.setdefault((t.GetLayer(), q.x, q.y), []).append(t)
        found = None
        for (lay, x, y), ts in ends.items():
            if len(ts) != 2 or ts[0].GetNetname() != ts[1].GetNetname() or (lay, x, y) in tried:
                continue
            if anchored(pcbnew.VECTOR2I(x, y), lay):
                continue
            fa = [far_end(t, x, y) for t in ts]
            v = [(q.x - x, q.y - y) for q in fa]
            n = [math.hypot(*vv) for vv in v]
            if n[0] and n[1] and (v[0][0] * v[1][0] + v[0][1] * v[1][1]) / n[0] / n[1] > 0.01:
                found = (lay, x, y, ts, fa, v, n)
                break
        if found is None:
            break
        lay, x, y, ts, fa, v, n = found
        k = 0 if n[0] <= n[1] else 1
        short, long_, a, c = ts[k], ts[1 - k], fa[k], fa[1 - k]
        cos = (v[0][0] * v[1][0] + v[0][1] * v[1][1]) / n[0] / n[1]
        if cos > 0.999:                                  # spike: the long segment now starts at the short one's end
            move_end(long_, x, y, a)
            b.Delete(short)
            spikes += 1
            continue
        ux, uy = (c.x - x) / n[1 - k], (c.y - y) / n[1 - k]
        d = (a.x - x) * ux + (a.y - y) * uy
        foot = pcbnew.VECTOR2I(int(round(x + ux * d)), int(round(y + uy * d)))
        ok = True
        if not anchored(a, lay):                         # the turn where the short arm meets the next copper
            for t in ends.get((lay, a.x, a.y), []):
                if t is short:
                    continue
                q = far_end(t, a.x, a.y)
                w1, w2 = (q.x - a.x, q.y - a.y), (foot.x - a.x, foot.y - a.y)
                if w1[0] * w2[0] + w1[1] * w2[1] > 0.01 * math.hypot(*w1) * math.hypot(*w2):
                    ok = False
        if ok:
            ax, ay, fx, fy = mm(a.x), mm(a.y), mm(foot.x), mm(foot.y)
            g = r5_maze.Grid(b, short.GetNetname(), lay, (min(ax, fx) - 1, min(ay, fy) - 1, max(ax, fx) + 1,
                                                           max(ay, fy) + 1), mm(short.GetWidth()) + 0.1, (ax, ay))
            steps = max(2, int(math.hypot(fx - ax, fy - ay) / 0.05))
            for i in range(steps + 1):
                ci, cj = g.cell(ax + (fx - ax) * i / steps, ay + (fy - ay) * i / steps)
                if not (0 <= ci < g.nx and 0 <= cj < g.ny) or g.blk[cj * g.nx + ci]:
                    ok = False
                    break
        if not ok:
            tried.add((lay, x, y))
            left.append((short.GetNetname(), round(mm(x), 2), round(mm(y), 2)))
            continue
        move_end(short, x, y, foot)
        move_end(long_, x, y, foot)
        cut += 1
    ends = {}                                            # what is left: a joint skipped above may have been
    for t in b.GetTracks():                              # resolved since (a spike trimmed at its other end)
        if t.GetClass() == 'PCB_TRACK':
            for q in (t.GetStart(), t.GetEnd()):
                ends.setdefault((t.GetLayer(), q.x, q.y), []).append(t)
    still = []
    for net, xm, ym in left:
        for (lay, x, y), ts in ends.items():
            if len(ts) != 2 or abs(mm(x) - xm) > 0.01 or abs(mm(y) - ym) > 0.01:
                continue
            v = [(q.x - x, q.y - y) for q in (far_end(t, x, y) for t in ts)]
            n = [math.hypot(*vv) for vv in v]
            if n[0] and n[1] and (v[0][0] * v[1][0] + v[0][1] * v[1][1]) / n[0] / n[1] > 0.01:
                still.append((net, xm, ym))
                break
    print(f'  acute corners: {spikes} spikes trimmed, {cut} wedges cut; left: {still or "none"}')
    return still


# --- 2. silkscreen --------------------------------------------------------------------------------

class Silk:
    """Obstacle boxes for one silkscreen side (inflated by their own clearance), bucketed on a grid: pads,
    vias, holes and silkscreen 0.15 mm (JLC clips ink nearer an opening), the package bodies of parts on this
    side (their fab outline: ink under a body is hidden after assembly)."""

    def __init__(self, b, side, strict_bodies=False):
        # Legacy default preserves the recorded R5 build; final placement checks
        # opt in so a pin-1 dot cannot suppress the courtyard body fallback.
        self.side = side
        self.layer = pcbnew.F_SilkS if side == 'F' else pcbnew.B_SilkS
        cu = pcbnew.F_Cu if side == 'F' else pcbnew.B_Cu
        fab = pcbnew.F_Fab if side == 'F' else pcbnew.B_Fab
        self.grid = {}
        for f in b.GetFootprints():
            for g in f.GraphicalItems():
                if g.GetLayer() == self.layer:
                    self.add(bx(g), GAP)
            for p in f.Pads():
                if p.IsOnLayer(cu) or p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                    self.add(bx(p), GAP)
            if f.IsFlipped() == (side == 'B'):
                body = None
                for g in f.GraphicalItems():
                    if g.GetLayer() == fab and g.GetClass() == 'PCB_SHAPE':
                        if strict_bodies and g.GetShape() == pcbnew.SHAPE_T_CIRCLE and mm(g.GetRadius()) <= 0.3:
                            continue  # Tiny pin-1 markers are not package bodies.
                        r = bx(g)
                        body = r if body is None else (min(body[0], r[0]), min(body[1], r[1]),
                                                       max(body[2], r[2]), max(body[3], r[3]))
                if body is None:
                    cy = f.GetCourtyard(pcbnew.B_CrtYd if side == 'B' else pcbnew.F_CrtYd)
                    if cy.OutlineCount():
                        r = cy.BBox()
                        body = (mm(r.GetX()) + 0.25, mm(r.GetY()) + 0.25, mm(r.GetRight()) - 0.25, mm(r.GetBottom()) - 0.25)
                if body is not None:
                    self.add(body, 0.0)
        for v in b.GetTracks():
            if v.GetClass() == 'PCB_VIA':
                self.add(bx(v), GAP)
        for d in b.GetDrawings():
            if d.GetLayer() == self.layer:
                self.add(bx(d), GAP)
            elif d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                self.add(bx(d), GAP)                       # mounting holes

    def add(self, r, gap=GAP):
        r = (r[0] - gap, r[1] - gap, r[2] + gap, r[3] + gap)
        for i in range(int(r[0] // CELL), int(r[2] // CELL) + 1):
            for j in range(int(r[1] // CELL), int(r[3] // CELL) + 1):
                self.grid.setdefault((i, j), []).append(r)

    def free(self, r):
        if r[0] < EDGE or r[1] < EDGE or r[2] > W - EDGE or r[3] > L - EDGE:
            return False
        for i in range(int(r[0] // CELL), int(r[2] // CELL) + 1):
            for j in range(int(r[1] // CELL), int(r[3] // CELL) + 1):
                for o in self.grid.get((i, j), ()):
                    if r[0] < o[2] and o[0] < r[2] and r[1] < o[3] and o[1] < r[3]:
                        return False
        return True


def _text(b, text, layer, size=1.0):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetMirrored(layer == pcbnew.B_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(0.15))
    return t


def label(b, silks, text, near, box, angles=(0, 90), sides=('F', 'B'), size=1.0):
    """A board-level legend at the free spot in box (x0, y0, x1, y1) nearest `near`, on the first side that has
    one; returns (side, x, y, angle) or None."""
    for side in sides:
        s = silks[side]
        t = _text(b, text, s.layer, size)
        cands = []
        x0, y0, x1, y1 = box
        st = 0.1 if (x1 - x0) * (y1 - y0) < 200 else 0.25
        for i in range(int((x1 - x0) / st) + 1):
            for j in range(int((y1 - y0) / st) + 1):
                x, y = x0 + st * i, y0 + st * j
                cands.append(((x - near[0]) ** 2 + (y - near[1]) ** 2, x, y))
        cands.sort()
        for ang in angles:
            t.SetTextAngleDegrees(ang)
            t.SetPosition(P(0, 0))
            r0 = ink(t)
            for _, x, y in cands:
                r = (r0[0] + x, r0[1] + y, r0[2] + x, r0[3] + y)
                if s.free(r):
                    t.SetPosition(P(x, y))
                    b.Add(t)
                    s.add(r)
                    return side, x, y, ang
    print(f'  no room for legend {text!r} near {near}')
    return None


def legends(b, silks):
    """Terminal, arming and connector legends (the R4 set, moved with the parts)."""
    placed = []

    def put(text, near, box, angles=(0, 90), sides=('F', 'B')):
        placed.append((text, label(b, silks, text, near, box, angles, sides)))

    # battery terminal J1 (wire entries aft): pin names forward of the body on the top only (F8; on the bottom the
    # parts under pin 2 left GND no spot, and a row without it read wrong), the input notes on the bottom
    for num, text in (('1', 'BAT+'), ('2', 'GND')):
        x, y = pad(b, 'J1', num)
        # within half the 5.08 mm pitch of its own pin (a wider search put GND under the switch pin)
        put(text, (x, 11.7), (x - 1.6, 11.1, x + 1.6, 18.5), angles=(90, 0), sides=('F',))
    x3, _ = pad(b, 'J1', '3')
    x4, _ = pad(b, 'J1', '4')
    put('SW', ((x3 + x4) / 2, 11.7), (x3 - 1.0, 11.1, x4 + 1.0, 15.5), angles=(0, 90), sides=('F',))
    put('2S INPUT / ' + REV, (23.0, 1.4), (2.0, 0.4, 44.0, 12.0), angles=(0,), sides=('B', 'F'))
    put('15A FUSE IN BATTERY LEAD', (23.0, 2.9), (2.0, 0.4, 44.0, 14.0), angles=(0,), sides=('B', 'F'))
    # camera terminal J9 (right edge, entries to the wall): pin names in the edge strip
    for num, text in (('1', '5V'), ('2', 'GND'), ('3', 'RX'), ('4', 'TX')):
        x, y = pad(b, 'J9', num)
        put(text, (44.2, y), (42.2, y - 2.0, 45.7, y + 2.0), angles=(0, 90), sides=('F', 'B'))
    put('CAM', (36.25, 18.8), (30.0, 14.0, 45.6, 19.5), angles=(0,), sides=('F', 'B'))
    put('UART 3V3', (36.25, 42.6), (28.0, 41.9, 45.6, 46.0), angles=(0, 90), sides=('F', 'B'))   # (vias may fill the strip)
    # ARM terminals J124/J120 (left edge) and igniter terminals J121/J125 (right edge): R4's legends
    for ref, num, text in (('J124', '2', 'RAW'), ('J124', '1', 'BUS1'), ('J120', '2', 'BUS2'), ('J120', '1', 'RAW')):
        x, y = pad(b, ref, num)
        put(text, (2.3, y), (0.3, y - 2.2, 4.5, y + 2.2), angles=(90, 0), sides=('F',))
        put(text, (x + 6.0, y), (x + 1.5, y - 2.0, x + 14.0, y + 2.0), angles=(0, 90), sides=('B',))
    for ref, num, text in (('J121', '1', 'E1-'), ('J121', '2', 'E1+'), ('J125', '1', 'E2+'), ('J125', '2', 'E2-')):
        x, y = pad(b, ref, num)
        put(text, (43.7, y), (41.5, y - 2.2, 45.7, y + 2.2), angles=(90, 0), sides=('F',))
        put(text, (x - 6.0, y), (x - 14.0, y - 2.0, x - 1.5, y + 2.0), angles=(0, 90), sides=('B',))
    put('ARM', (2.3, 67.5), (0.3, 63.5, 9.0, 70.2), angles=(0, 90), sides=('F', 'B'))
    put('IGN', (43.7, 67.5), (37.0, 63.5, 45.7, 70.2), angles=(0, 90), sides=('F', 'B'))
    put('ARM PLUG: J124 2-F1-1 / J120 1-F2-2', (23.0, 98.4), (2.0, 90.0, 44.0, 99.7), angles=(0,), sides=('B', 'F'))
    put('5A FAST FUSES, PLUG IN LAST', (23.0, 97.0), (2.0, 90.0, 44.0, 99.7), angles=(0,), sides=('B', 'F'))
    # servo header J122: column legends forward of it, servo numbers beside the rows
    for num, text in (('3', '-'), ('2', '+'), ('1', 'S')):
        x, y = pad(b, 'J122', num)
        put(text, (x, 63.5), (x - 0.9, 62.9, x + 0.9, 65.0), angles=(0,), sides=('F', 'B'))
    for num, text in (('3', '1'), ('6', '2'), ('9', '3'), ('12', '4')):
        x, y = pad(b, 'J122', num)
        put(text, (x - 1.9, y), (x - 2.8, y - 1.0, x - 1.2, y + 1.0), angles=(0,), sides=('B', 'F'))
    put('SERVO', (23.0, 65.2), (17.0, 62.9, 29.0, 66.0), angles=(0,), sides=('F', 'B'))
    # pull-pin J123
    for num, text in (('1', 'PULL'), ('2', 'GND')):
        x, y = pad(b, 'J123', num)
        put(text, (x, 8.0), (x - 3.5, 7.0, x + 3.5, 11.0), angles=(0, 90), sides=('F', 'B'))
    # C84 (OS-CON): its + terminal, readable after assembly
    x, y = pad(b, 'C84', '1')
    put('+', (x, y + 3.0), (x - 4.0, y + 2.2, x + 4.0, y + 4.5), angles=(0,), sides=('F', 'B'))
    # revision legend (R4: "M3-ASSY-R4 - DATA" / "USB / SWD - PROTOTYPE")
    put(REV + ' - DATA', (23.0, 93.0), (2.0, 2.0, 44.0, 99.7), angles=(0,), sides=('F', 'B'))
    put('USB / SWD - PROTOTYPE', (23.0, 94.6), (2.0, 2.0, 44.0, 99.7), angles=(0,), sides=('F', 'B'))
    missing = [t for t, r in placed if r is None]
    print(f'  legends: {len(placed) - len(missing)} placed, missing: {missing or "none"}')
    return placed


DOT_PARTS = ('U7', 'U8', 'U9', 'U10', 'U11', 'U13')


def pin1_dots(b, silks):
    """R4 m_pin1_marks: a filled dot beside pin 1, outside the package body, on the part's own side."""
    for ref in DOT_PARTS:
        f = fp_of(b, ref)
        s = silks['B' if f.IsFlipped() else 'F']
        fab = pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab
        body = None
        for g in f.GraphicalItems():
            if g.GetLayer() == fab and g.GetClass() == 'PCB_SHAPE':
                r = bx(g)
                body = r if body is None else (min(body[0], r[0]), min(body[1], r[1]), max(body[2], r[2]), max(body[3], r[3]))
        p1 = next(p for p in f.Pads() if p.GetNumber() == '1')
        c, q = f.GetPosition(), p1.GetPosition()
        base = math.atan2(q.y - c.y, q.x - c.x)
        half = mm(max(p1.GetBoundingBox().GetWidth(), p1.GetBoundingBox().GetHeight())) / 2
        qx, qy = mm(q.x), mm(q.y)
        for k in range(16 * 9):
            reach = half + 0.35 + 0.1 * (k // 16)
            ang = base + ((k % 16) // 2) * (1 if k % 2 else -1) * math.pi / 8
            x, y = qx + reach * math.cos(ang), qy + reach * math.sin(ang)
            r = (x - 0.2, y - 0.2, x + 0.2, y + 0.2)
            if body and r[0] < body[2] and body[0] < r[2] and r[1] < body[3] and body[1] < r[3]:
                continue
            if s.free(r):
                dot = pcbnew.PCB_SHAPE(b)
                dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
                dot.SetLayer(s.layer)
                dot.SetStart(P(x, y))
                dot.SetEnd(P(x + 0.1, y))
                dot.SetWidth(MM(0.2))
                dot.SetFilled(True)
                b.Add(dot)
                s.add(r)
                break
        else:
            print('  no room for a pin-1 dot at', ref)


def order_mark(b, silks):
    """JLC's "specify a location" order number needs a JLCJLCJLCJLC placeholder (ORDERING)."""
    r = label(b, silks, 'JLCJLCJLCJLC', (23.0, 74.0), (2.0, 2.0, 44.0, 98.0), angles=(0, 90), sides=('B', 'F'))
    print('  order-number placeholder:', r)


HIDDEN = []                    # designators with no unambiguous spot (docs/M3_R5.md section 2)


def _gap(a, c):
    dx = max(c[0] - a[2], a[0] - c[2], 0.0)
    dy = max(c[1] - a[3], a[1] - c[3], 0.0)
    return math.hypot(dx, dy)


def designators(b, silks, rmax=5.0, cap=1.5, big_cap=3.0, margin=0.15):
    """R4 place_ref_clear for every part: the text keeps GAP from pads, vias, holes and other silkscreen and stays
    off every package body, sits at most `cap` mm from its own pads (`big_cap` for parts over 5 mm) and nearer
    them (by `margin`) than any other part's pads. A top part tries the top first, then the bottom with the text
    centred within its own pads' extent and 1.2 mm (ink) clear of every bottom part's pads (AGENTS: crowded designators go
    to the bottom side under their part, never next to another part); a
    bottom part's designator stays on the bottom (on the top it read as a top part's). The most constrained
    parts are placed first."""
    HIDDEN[:] = []
    pads = [(f.GetReference(), p, bx(p)) for f in b.GetFootprints() for p in f.Pads()]

    def candidates(f, limit=None):
        """Valid (side, x, y, angle, box) spots for f's designator, nearest first."""
        ref = f.GetReference()
        t = f.Reference()
        own = [r for who, _, r in pads if who == ref]
        cx, cy = mm(f.GetPosition().x), mm(f.GetPosition().y)
        ext = max(max(r[2] for r in own) - min(r[0] for r in own), max(r[3] for r in own) - min(r[1] for r in own))
        c_ = big_cap if ext >= 5.0 else cap
        out = []
        for side in (('B',) if f.IsFlipped() else ('F', 'B')):   # a bottom part's designator stays on the bottom
            s = silks[side]
            part_cu = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
            label_cu = pcbnew.F_Cu if side == 'F' else pcbnew.B_Cu
            others = [r for who, p, r in pads if who != ref and (p.IsOnLayer(part_cu) or p.IsOnLayer(label_cu))
                      and abs((r[0] + r[2]) / 2 - cx) < rmax + 8 and abs((r[1] + r[3]) / 2 - cy) < rmax + 8]
            under = side == 'B' and not f.IsFlipped()      # a top part's designator under it, on the bottom
            bottom_pads = [r for who, p, r in pads if who != ref and p.IsOnLayer(pcbnew.B_Cu)
                           and abs((r[0] + r[2]) / 2 - cx) < rmax + 8 and abs((r[1] + r[3]) / 2 - cy) < rmax + 8] \
                if under else []
            t.SetLayer(s.layer)
            t.SetMirrored(side == 'B')
            boxes = {}
            for ang in (0, 90):
                t.SetTextAngleDegrees(ang)
                t.SetPosition(P(0, 0))
                boxes[ang] = ink(t)
            reach = max(math.hypot(max(abs(o[0] - cx), abs(o[2] - cx)), max(abs(o[1] - cy), abs(o[3] - cy)))
                        for o in own) + c_ + max(max(r[2] - r[0], r[3] - r[1]) for r in boxes.values()) / 2
            rr = 0.0
            while rr <= min(rmax + ext / 2, reach):
                n = max(1, int(2 * math.pi * rr / 0.2))
                for k in range(n):
                    a = 2 * math.pi * k / n
                    x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
                    for ang in (0, 90):
                        r0 = boxes[ang]
                        r = (r0[0] + x, r0[1] + y, r0[2] + x, r0[3] + y)
                        d_own = min(_gap(r, o) for o in own)
                        if d_own > c_ or not s.free(r):
                            continue
                        if side == 'B' and not f.IsFlipped() and not (
                                min(o[0] for o in own) <= x <= max(o[2] for o in own) and
                                min(o[1] for o in own) <= y <= max(o[3] for o in own)):
                            continue                       # on the other side only under the part itself
                        if under and any(_gap(r, o) < 1.2 for o in bottom_pads):
                            continue                       # pass 2: not beside a bottom part (it read as its label)
                        near = [_gap(r, o) for o in others if abs((o[0] + o[2]) / 2 - x) < 7 and abs((o[1] + o[3]) / 2 - y) < 7]
                        if near and d_own + margin > min(near):
                            continue                       # as near another part's pads: ambiguous
                        out.append((side, x, y, ang, r))
                        if limit and len(out) >= limit:
                            return out
                rr += 0.2
        return out

    for f in b.GetFootprints():
        t = f.Reference()
        if t.GetTextHeight() < MM(1.0):
            t.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0)))
        if t.GetTextThickness() < MM(0.15):
            t.SetTextThickness(MM(0.15))
    todo = {f.GetReference(): f for f in b.GetFootprints()}
    counts = {ref: len(candidates(f, limit=60)) for ref, f in todo.items()}
    for ref in sorted(todo, key=lambda r: (counts[r], r)):
        f = todo[ref]
        t = f.Reference()
        c = candidates(f, limit=1)
        if not c:
            t.SetVisible(False)
            HIDDEN.append(ref)
            continue
        side, x, y, ang, r = c[0]
        s = silks[side]
        t.SetLayer(s.layer)
        t.SetMirrored(side == 'B')
        t.SetTextAngleDegrees(ang)
        t.SetPosition(P(x, y))
        t.SetVisible(True)
        s.add(r)
    print(f'  designators hidden (no unambiguous spot, F.Fab keeps them): {len(HIDDEN)}: {" ".join(sorted(HIDDEN))}')


# --- pours -------------------------------------------------------------------------------------

# small GND pads that would be left on one spoke or starved (pass 6: the pour reaches them from one side) stay solid
RELIEF_KEEP_FULL = {('R128', '2'), ('C25', '2'), ('C128', '2'), ('R142', '2'), ('C22', '2'), ('R105', '2')}


def pour_relief(b):
    """Pass 4 robustness items, on the pours only (no copper moves):
    - the RAW_ACT through-hole pins (J120.1, J124.2, J122.2/5/8/11) keep 0.3 mm from other nets' pours, not the outer
      GND pours' 0.15 mm (m3.kicad_dru; tracks and vias keep the board rules): a bridge there, at the hand-soldered joints, shorts the servo feed to GND (R4 had 0.25 mm);
    - the GND pads of two-pad 0402/0603 parts join the outer GND pours through thermal spokes (0.25 mm gap, 0.3 mm
      spokes, m3.kicad_dru), not solidly: a pad buried in a stitched pour heats slower than its trace-fed partner and tombstones."""
    raw = sum(1 for f in b.GetFootprints() for q in f.Pads()   # (the clearance itself: m3.kicad_dru, pours only)
              if q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and q.GetNetname() == 'RAW_ACT')
    small = 0
    for f in b.GetFootprints():
        pads = list(f.Pads())
        if len(pads) != 2 or any(q.GetAttribute() != pcbnew.PAD_ATTRIB_SMD for q in pads):
            continue
        if max(mm(q.GetSize(q.GetLayer()).x) for q in pads) > 1.0 or max(mm(q.GetSize(q.GetLayer()).y) for q in pads) > 1.0:
            continue                                     # 0402 and 0603 only
        for q in pads:
            if q.GetNetname() == 'GND' and (f.GetReference(), q.GetNumber()) not in RELIEF_KEEP_FULL:
                q.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)   # gap and spokes: m3.kicad_dru
                small += 1
    print(f'  pour relief: {raw} RAW_ACT pins at 0.3 mm, {small} small GND pads on spokes')


def usb_reference(b):
    """The In2 3V3 fill grows north (left of the In2 sense lanes) under USB D+/D- on B.Cu between J3, D4 and U1, so
    those traces have a plane beneath them (done after routing: the fill only takes what the routes leave)."""
    z = next(z for z in b.Zones() if z.GetZoneName() == '3V3_In2')
    ol = z.Outline()
    ol.RemoveAllContours()
    ol.NewOutline()
    for x, y in ((9.2, 9.0), (34.5, 9.0), (34.5, 52.2), (14.0, 52.2), (14.0, 61.5), (8.9, 61.5), (8.9, 52.2), (9.2, 52.2)):
        ol.Append(MM(x), MM(y))


def stitch(b, pitch=3.0):
    """GND stitching vias (0.6/0.3) on a `pitch` grid wherever the F.Cu and B.Cu GND fills both reach and a via keeps
    the rule clearances on every layer (r5_maze.via_spot, 0.5 mm search), joining the outer pours to the In1 plane.
    Not inside the pyro block (rule D keeps GND 0.5 mm from its bus copper; the block keeps R4's own vias)."""
    import r5_maze
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    fills = {lay: [z.GetFilledPolysList(lay) for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND'
                   and z.IsOnLayer(lay)] for lay in (pcbnew.F_Cu, pcbnew.B_Cu)}
    ends = _gnd_track_ends(b)
    pth = [(p.GetBoundingBox(), mm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2, mm(p.GetPosition().x),
            mm(p.GetPosition().y)) for f in b.GetFootprints() for p in f.Pads()
           if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)]

    def clear_of_pth(v):
        """Outside every through-hole pad's copper (0.15 mm) and 0.45 mm hole to hole (JLC; via_spot allows a GND via
        on a GND through-hole pad, which would sit in its solder opening)."""
        for bb, hr, hx, hy in pth:
            dd = math.hypot(max(mm(bb.GetX()) - v[0], 0, v[0] - mm(bb.GetRight())),
                            max(mm(bb.GetY()) - v[1], 0, v[1] - mm(bb.GetBottom())))
            if dd < 0.3 + 0.15 or math.hypot(v[0] - hx, v[1] - hy) < hr + 0.15 + 0.45:
                return False
        return True
    n = 0
    y = 4.5                                            # the aft and forward 2.6 mm strips carry the input and
    while y < L - 2.6:                                 # arming legends
        x = 1.5
        while x < W - 1.0:
            q = P(x, y)
            inside = all(any(ps.Contains(q) for ps in fills[lay]) for lay in fills)
            if inside and not (r5_maze.BLOCK[0] <= x <= r5_maze.BLOCK[2] and r5_maze.BLOCK[1] <= y <= r5_maze.BLOCK[3]):
                try:
                    v = r5_maze.via_spot(b, 'GND', (x, y), (x, y), r=0.5)
                    if all(ps.Contains(P(*v)) for lay in fills for ps in fills[lay][:1]) and not _near_end(v, ends) \
                            and clear_of_pth(v):
                        via = pcbnew.PCB_VIA(b)
                        via.SetPosition(P(*v))
                        via.SetWidth(MM(0.6))
                        via.SetDrill(MM(0.3))
                        via.SetNet(b.FindNet('GND'))
                        b.Add(via)
                        n += 1
                except RuntimeError:
                    pass
            x += pitch
        y += pitch
    print(f'  GND stitching vias: {n}')


def return_vias(b, reach=(1.5, 2.5), step=0.1):
    """AGENTS.md: a GND via next to every layer change of a critical net (USB, HSE, QSPI, SPI1). r5_routes placed
    them before the autorouter where one fitted; here, with everything routed and the pours filled, a critical via
    with no GND via or through-hole GND pin within 1.5 mm gets the nearest GND via (within 1.5 mm, else 2.5 mm) that
    lands in an outer GND fill (so it joins that pour to the In1 plane) and keeps every rule clearance
    (r5_maze.via_spot). Here the In2 power islands may fill round it (r5_maze.PASSABLE_IN2), which the routers could
    not allow: a via there before routing would have necked the island where a route had to pass. What still has
    none within 2.5 mm is listed (docs/M3_R5.md section 2)."""
    import r5_maze
    import r5_route
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    fills = [z.GetFilledPolysList(lay) for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND'
             for lay in (pcbnew.F_Cu, pcbnew.B_Cu) if z.IsOnLayer(lay)]
    ends = _gnd_track_ends(b)
    tht = [(mm(q.GetPosition().x), mm(q.GetPosition().y)) for f in b.GetFootprints() for q in f.Pads()
           if q.GetNetname() == 'GND' and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    sig = [(mm(v.GetPosition().x), mm(v.GetPosition().y), v.GetNetname()) for v in b.GetTracks()
           if v.GetClass() == 'PCB_VIA' and v.GetNetname() in r5_route.CRITICAL]
    bx0, by0, bx1, by1 = r5_maze.BLOCK
    added, far, none = 0, [], []
    r5_maze.PASSABLE_IN2 = {'RAW_ACT', 'BAT_IN', 'CAM_5V'}
    try:
        for x, y, net in sig:
            gnd = tht + [(mm(v.GetPosition().x), mm(v.GetPosition().y)) for v in b.GetTracks()
                         if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND']
            if min(math.hypot(x - gx, y - gy) for gx, gy in gnd) <= reach[0]:
                continue
            n = int(reach[-1] / step)
            cands = sorted((math.hypot(i, j) * step, round(x + i * step, 3), round(y + j * step, 3))
                           for i in range(-n, n + 1) for j in range(-n, n + 1))
            spot = None
            for d, cx, cy in cands:
                if d > reach[-1]:
                    break
                if (bx0 <= cx <= bx1 and by0 <= cy <= by1) or _near_end((cx, cy), ends):
                    continue
                if not any(ps.Contains(P(cx, cy)) for ps in fills):
                    continue
                try:
                    spot = r5_maze.via_spot(b, 'GND', (cx, cy), (cx, cy), r=0.05), d
                    break
                except RuntimeError:
                    continue
            if spot is None:
                none.append((net, (round(x, 2), round(y, 2))))
                continue
            (vx, vy), d = spot
            via = pcbnew.PCB_VIA(b)
            via.SetPosition(P(vx, vy))
            via.SetWidth(MM(0.6))
            via.SetDrill(MM(0.3))
            via.SetNet(b.FindNet('GND'))
            b.Add(via)
            added += 1
            if d > reach[0]:
                far.append((net, (round(x, 2), round(y, 2)), round(d, 2)))
    finally:
        r5_maze.PASSABLE_IN2 = set()
    print(f'  return vias added: {added}; 1.5-2.5 mm away: {far or "none"}; none within 2.5 mm: {none or "none"}')


def _gnd_track_ends(b):
    return [(mm(q.x), mm(q.y)) for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'GND'
            for q in (t.GetStart(), t.GetEnd())]


def _near_end(v, ends):
    """A GND track end inside a new via but off its centre (DRC: track not centred on via)."""
    return any(0.01 < math.hypot(v[0] - x, v[1] - y) < 0.45 for x, y in ends)


def island_vias(b, step=0.4):
    """A GND via inside every outer GND fill island that has none and holds no through-hole GND pin, so every island
    reaches the In1 plane (the grid stitching misses islands on one side only or smaller than its pitch; DRC lists
    them as unconnected zone pieces). The via keeps every rule clearance (r5_maze.via_spot, pyro rules included);
    where none fits, one of the island's GND pads is tied to a via beside it, or joined by a short outer-layer track
    to the nearest GND via (the grid router)."""
    import r5_maze
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    gnd = [v.GetPosition() for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND']
    gnd += [q.GetPosition() for f in b.GetFootprints() for q in f.Pads()
            if q.GetNetname() == 'GND' and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    n, left = 0, 0
    ends = _gnd_track_ends(b)
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != 'GND' or z.IsOnLayer(pcbnew.In1_Cu):
            continue
        for lay in z.GetLayerSet().CuStack():
            fill = z.GetFilledPolysList(lay)
            for k in range(fill.OutlineCount()):
                ol = fill.Outline(k)
                if any(ol.PointInside(q) for q in gnd):
                    continue
                bb = ol.BBox()
                x0, y0, x1, y1 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())
                pts = [(round(x0 + step * i, 2), round(y0 + step * j, 2)) for j in range(int((y1 - y0) / step) + 1)
                       for i in range(int((x1 - x0) / step) + 1)]
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                for x, y in sorted(pts, key=lambda q: math.hypot(q[0] - cx, q[1] - cy)):
                    if not ol.PointInside(P(x, y)):
                        continue
                    try:
                        v = r5_maze.via_spot(b, 'GND', (x, y), (x, y), r=0.2)
                    except RuntimeError:
                        continue
                    if ol.PointInside(P(*v)) and not _near_end(v, ends):
                        via = pcbnew.PCB_VIA(b)
                        via.SetPosition(P(*v))
                        via.SetWidth(MM(0.6))
                        via.SetDrill(MM(0.3))
                        via.SetNet(b.FindNet('GND'))
                        b.Add(via)
                        gnd.append(P(*v))
                        n += 1
                        break
                else:                                   # no room inside: tie one of its GND pads to a via nearby
                    import r5_routes
                    pads = [q for f in b.GetFootprints() for q in f.Pads() if q.GetNetname() == 'GND' and
                            q.IsOnLayer(lay) and q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and ol.PointInside(q.GetPosition())]
                    for q in pads:
                        pq = (round(mm(q.GetPosition().x), 4), round(mm(q.GetPosition().y), 4))
                        try:
                            v = r5_routes.tie(b, 'GND', pq, r5_routes.escape(b, pq, extra=0.7) or pq, lay, w=0.25, tries=10)
                        except RuntimeError:
                            continue
                        gnd.append(P(*v))
                        n += 1
                        break
                    else:                               # last resort: a track from one of its GND pads to a GND via
                        vias = [(mm(v.GetPosition().x), mm(v.GetPosition().y)) for v in b.GetTracks()
                                if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND']
                        joined = False
                        for q in pads:
                            pq = (round(mm(q.GetPosition().x), 4), round(mm(q.GetPosition().y), 4))
                            for v in sorted(vias, key=lambda c: math.hypot(c[0] - pq[0], c[1] - pq[1]))[:4]:
                                try:
                                    r5_routes.multi(b, 'GND', pq, v, 0.25, (pcbnew.F_Cu, pcbnew.B_Cu), via_cost=10.0,
                                                    margin=3)
                                except RuntimeError:
                                    continue
                                joined = True
                                break
                            if joined:
                                break
                        if joined:
                            n += 1
                        else:
                            left += 1
    print(f'  GND island vias: {n}; islands still without one: {left}')


# --- 3. fab-layer designators (R4 z_fab_refs) ----------------------------------------------------

def _fab_ref(f):
    fab = pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab
    for g in f.GraphicalItems():
        if isinstance(g, pcbnew.PCB_TEXT) and g.GetText() == '${REFERENCE}' and g.GetLayer() == fab:
            return g
    return None


def fab_refs(b):
    added = []
    for f in b.GetFootprints():
        if _fab_ref(f) is not None:
            continue
        cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        c = cy.BBox().Centre() if cy.OutlineCount() else f.GetPosition()
        tx = pcbnew.PCB_TEXT(f)
        tx.SetText('${REFERENCE}')
        tx.SetLayer(pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab)
        tx.SetMirrored(f.IsFlipped())
        tx.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
        tx.SetTextThickness(MM(0.12))
        tx.SetPosition(pcbnew.VECTOR2I(c.x, c.y))
        f.Add(tx)
        added.append(f.GetReference())

    def overlaps():
        boxes = [(f.GetReference(), f.IsFlipped(), _fab_ref(f).GetBoundingBox()) for f in b.GetFootprints()]
        hit = set()
        for i, (r1, s1, b1) in enumerate(boxes):
            for r2, s2, b2 in boxes[i + 1:]:
                if s1 == s2 and b1.Intersects(b2):
                    hit.update((r1, r2))
        return hit
    for size in (0.4, 0.3):
        hit = overlaps()
        for f in b.GetFootprints():
            tx = _fab_ref(f)
            if f.GetReference() in hit and mm(tx.GetTextHeight()) > size:
                tx.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
                tx.SetTextThickness(MM(size * 0.15))
    print(f'  fab designators added: {len(added)}; still overlapping at 0.3 mm: {sorted(overlaps()) or "none"}')


# --- main ----------------------------------------------------------------------------------------

def main():
    import r5_maze
    r5_maze.MARGIN = 0.02                              # as r5_finish: 0.02 mm over each clearance rule (DRC checks)
    pcbnew.KIID.SeedGenerator(5104)                    # repeatable UUIDs (r5_pcb.main)
    b = pcbnew.LoadBoard(PCB)
    for z in list(b.Zones()):                          # routing-only keep-outs (r5_routes._keep_area)
        if z.GetIsRuleArea() and z.GetZoneName().startswith('KEEP_'):
            b.Delete(z)
    for d in list(b.GetDrawings()):                    # idempotent: the board-level silkscreen is ours
        if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.Delete(d)
    close_joints(b)
    track_cleanup(b)
    pth_vias(b)
    acute_corners(b)
    usb_reference(b)
    stitch(b)
    return_vias(b)
    island_vias(b)
    for f in b.GetFootprints():                        # designators out of the way while legends are placed
        f.Reference().SetVisible(False)
    silks = {s: Silk(b, s) for s in ('F', 'B')}
    legends(b, silks)
    pin1_dots(b, silks)
    order_mark(b, silks)
    designators(b, silks)
    fab_refs(b)
    pour_relief(b)
    tb = b.GetTitleBlock()
    tb.SetTitle('M3 flight computer')
    tb.SetRevision(REV)
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    print('saved', PCB)


if __name__ == '__main__':
    main()
