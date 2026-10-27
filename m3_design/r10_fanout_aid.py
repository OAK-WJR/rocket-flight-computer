#!/usr/bin/env python3
"""R10 design aid (not a build stage): find a plane via for every rail pad that has none, and freeze the result.

For each SMD pad on a plane net (GND, 3V3, RAW_PROTECTED, PORT_5V3, PORT_4V8) whose same-layer copper island holds no
via of its net, try via spots on the eight octilinear rays from the pad centre (nearest first) and keep the first spot
whose via and stub clear every other net's copper by CLEAR mm, the board edge, holes and keep-out rule areas. The result
is written to m3_design/r10_fanout.tsv (net, pad, layer, via x, via y); r10_route_ground.py draws it as is, so the build
needs no search (R9's r9_ground_aid.py / r9_ground.tsv pattern).

usage: KiCad python3 r10_fanout_aid.py board.kicad_pcb [--out m3_design/r10_fanout.tsv]
"""
import argparse
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
NETS = ('GND', '3V3', 'RAW_PROTECTED', 'PORT_5V3', 'PORT_4V8')
VIA_D, VIA_H = 0.5, 0.3
CLEAR = 0.2          # mm to other nets' copper (board default 0.15 plus margin)
TP_CLEAR = 1.0       # bare test pads keep 1.0 mm (DRU)
EDGE = 0.6
PLANE_MARGIN = 0.35   # via centre to its plane region's outline
MM, mm = pcbnew.FromMM, pcbnew.ToMM
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy or 1e-12)))
    return math.hypot(px - ax - t * vx, py - ay - t * vy)


def island_has_via(board, pad, net):
    conn = board.GetConnectivity()
    for it in conn.GetConnectedItems(pad):
        if it.GetClass() == 'PCB_VIA' and it.GetNetname() == net:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board')
    ap.add_argument('--out', default=str(ROOT / 'm3_design/r10_fanout.tsv'))
    a = ap.parse_args()
    b = pcbnew.LoadBoard(a.board)
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill([z for z in b.Zones() if not z.GetIsRuleArea()])
    b.BuildConnectivity()
    edge = b.GetBoardEdgesBoundingBox()
    X0, Y0, X1, Y1 = mm(edge.GetX()), mm(edge.GetY()), mm(edge.GetRight()), mm(edge.GetBottom())
    holes = [(mm(d.GetCenter().x), mm(d.GetCenter().y), mm(d.GetRadius())) for d in b.GetDrawings()
             if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    keepouts = [z for z in b.Zones() if z.GetIsRuleArea()]
    # The via must land inside its own net's plane: GND on In1, the rails on their In2 region (D-R2-06).
    planes = {}
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() in NETS and \
                z.GetLayer() == (pcbnew.In1_Cu if z.GetNetname() == 'GND' else pcbnew.In2_Cu):
            o = z.Outline().Outline(0)
            pts = [(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())]
            planes.setdefault(z.GetNetname(), []).append((z.Outline(), pts))

    def in_plane(net, x, y):
        pt = pcbnew.VECTOR2I(MM(x), MM(y))
        return any(o.Contains(pt) and min(seg_dist(x, y, *a, *b) for a, b in zip(pts, pts[1:] + pts[:1])) >= PLANE_MARGIN
                   for o, pts in planes.get(net, ()))
    pads = [p for f in b.GetFootprints() for p in f.Pads()]
    items = [(p, p.GetNetname(), p.GetParentFootprint().GetReference().startswith('TP')) for p in pads] + \
            [(t, t.GetNetname(), False) for t in b.GetTracks()]
    placed = []      # vias chosen in this run, (x, y)
    vias = [(mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    new = []         # (net, layer, shape) of the stubs and vias chosen in this run

    cand = {}

    def min_dist_to(geo, shape_layer_pairs, layer, seg=False):
        # distance from a stored item to the candidate via (both layers) or its stub (pad layer only)
        pts = [(cand['x'], cand['y'])]
        out = []
        for gx in ([geo] if not seg else [geo]):
            if not seg:
                out.append(math.hypot(gx[0] - cand['x'], gx[1] - cand['y']) - VIA_D / 2)
                if layer == cand['layer']:
                    out.append(seg_dist(gx[0], gx[1], cand['cx'], cand['cy'], cand['x'], cand['y']) - 0.15)
            else:
                ax, ay, bx, by = gx
                out.append(seg_dist(cand['x'], cand['y'], ax, ay, bx, by) - VIA_D / 2)
                if layer == cand['layer']:
                    for k in range(11):
                        qx = cand['cx'] + (cand['x'] - cand['cx']) * k / 10
                        qy = cand['cy'] + (cand['y'] - cand['cy']) * k / 10
                        out.append(seg_dist(qx, qy, ax, ay, bx, by) - 0.15)
        return min(out) + (VIA_D / 2 if not seg else 0.15)

    def clear(shape_layer_pairs, net, x, y, own):
        for layer, shape in shape_layer_pairs:
            for it, n, tp in items:
                if it.m_Uuid.AsString() == own or not it.IsOnLayer(layer):
                    continue
                if n == net:             # the via overlaps no other copper of its net (no off-centre joins)
                    if shape.Type() == pcbnew.SH_CIRCLE and it.GetEffectiveShape(layer).Collide(shape, 0):
                        return False
                    continue
                c = TP_CLEAR if tp else CLEAR
                if it.GetEffectiveShape(layer).Collide(shape, MM(c)):
                    return False
        for n, l2, geo in new:                   # this run's own stubs and vias (plain geometry)
            if n == net or l2 not in [l for l, _ in shape_layer_pairs]:
                continue
            if geo[0] == 'via' and min_dist_to(geo[1:], shape_layer_pairs, l2) < VIA_D / 2 + CLEAR:
                return False
            if geo[0] == 'seg' and min_dist_to(geo[1:], shape_layer_pairs, l2, seg=True) < 0.15 + CLEAR:
                return False
        for hx, hy, hr in holes:                 # Edge.Cuts holes: copper-to-edge 0.5 mm
            if math.hypot(hx - x, hy - y) < hr + VIA_D / 2 + 0.55:
                return False
        for px, py in placed + vias:             # hole-to-hole 0.25 mm and no ring overlap, any net
            if math.hypot(px - x, py - y) < VIA_D + 0.15:
                return False
        for z in keepouts:
            if z.GetDoNotAllowVias() and z.Outline().Contains(pcbnew.VECTOR2I(MM(x), MM(y))):
                return False
        return X0 + EDGE < x < X1 - EDGE and Y0 + EDGE < y < Y1 - EDGE and in_plane(net, x, y)

    rows, missing = [], []
    served = set()   # pads whose island got a via earlier in this run
    for p in sorted(pads, key=lambda p: (p.GetNetname(), p.GetParentFootprint().GetReference(), p.GetNumber())):
        net = p.GetNetname()
        if net not in NETS or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        if island_has_via(b, p, net) or p.m_Uuid.AsString() in served:
            continue
        ref = f'{p.GetParentFootprint().GetReference()}.{p.GetNumber()}'
        layer = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
        cx, cy = mm(p.GetPosition().x), mm(p.GetPosition().y)
        half = max(mm(p.GetBoundingBox().GetWidth()), mm(p.GetBoundingBox().GetHeight())) / 2
        best = None
        for dist in [round(half + 0.35 + 0.05 * i, 3) for i in range(40)]:
            for dx, dy in DIRS:
                k = round(dist / math.hypot(dx, dy), 3) if dx and dy else dist
                x, y = round(cx + dx * k, 4), round(cy + dy * k, 4)
                via = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(x), MM(y)), MM(VIA_D / 2))
                stub = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(cx), MM(cy)), pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.3))
                if any(seg_dist(px, py, cx, cy, x, y) < VIA_D / 2 + 0.15 + 0.1 for px, py in placed + vias):
                    continue
                cand.update(x=x, y=y, cx=cx, cy=cy, layer=layer)
                if clear([(pcbnew.F_Cu, via), (pcbnew.B_Cu, via), (layer, stub)], net, x, y, p.m_Uuid.AsString()):
                    best = (x, y)
                    break
            if best:
                break
        if best:
            placed.append(best)
            served.update(it.m_Uuid.AsString() for it in b.GetConnectivity().GetConnectedItems(p)
                          if it.GetClass() == 'PAD')
            vx, vy = best
            new.append((net, pcbnew.F_Cu, ('via', vx, vy)))
            new.append((net, pcbnew.B_Cu, ('via', vx, vy)))
            new.append((net, layer, ('seg', cx, cy, vx, vy)))
            rows.append((net, ref, 'B' if layer == pcbnew.B_Cu else 'F', *best))
        else:
            missing.append(ref)
    with open(a.out, 'w') as fh:
        fh.write('# r10_fanout_aid.py output (frozen): net, pad, pad layer, via x, via y; stub 0.3 mm pad centre -> via\n')
        fh.write('net\tpad\tlayer\tx\ty\n')
        for r in rows:
            fh.write('\t'.join(str(v) for v in r) + '\n')
    print(f'{len(rows)} vias written to {a.out}; {len(missing)} pads without a legal spot: {" ".join(missing)}')


if __name__ == '__main__':
    main()
