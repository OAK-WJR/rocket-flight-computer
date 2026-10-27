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
MM, mm = pcbnew.FromMM, pcbnew.ToMM
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


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
    pads = [p for f in b.GetFootprints() for p in f.Pads()]
    items = [(p, p.GetNetname(), p.GetParentFootprint().GetReference().startswith('TP')) for p in pads] + \
            [(t, t.GetNetname(), False) for t in b.GetTracks()]
    placed = []      # vias chosen in this run, (x, y)

    def clear(shape_layer_pairs, net, x, y):
        for layer, shape in shape_layer_pairs:
            for it, n, tp in items:
                if n == net or not it.IsOnLayer(layer):
                    continue
                c = TP_CLEAR if tp else CLEAR
                if it.GetEffectiveShape(layer).Collide(shape, MM(c)):
                    return False
        for hx, hy, hr in holes:
            if math.hypot(hx - x, hy - y) < hr + VIA_D / 2 + 0.25:
                return False
        for px, py in placed:
            if math.hypot(px - x, py - y) < VIA_D + CLEAR:
                return False
        for z in keepouts:
            if z.GetDoNotAllowVias() and z.Outline().Contains(pcbnew.VECTOR2I(MM(x), MM(y))):
                return False
        return X0 + EDGE < x < X1 - EDGE and Y0 + EDGE < y < Y1 - EDGE

    rows, missing = [], []
    for p in sorted(pads, key=lambda p: (p.GetNetname(), p.GetParentFootprint().GetReference(), p.GetNumber())):
        net = p.GetNetname()
        if net not in NETS or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        if island_has_via(b, p, net):
            continue
        ref = f'{p.GetParentFootprint().GetReference()}.{p.GetNumber()}'
        layer = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
        cx, cy = mm(p.GetPosition().x), mm(p.GetPosition().y)
        half = max(mm(p.GetBoundingBox().GetWidth()), mm(p.GetBoundingBox().GetHeight())) / 2
        best = None
        for dist in [round(half + 0.35 + 0.05 * i, 3) for i in range(40)]:
            for dx, dy in DIRS:
                k = dist / math.hypot(dx, dy) if dx and dy else dist
                x, y = round(cx + dx * k, 2), round(cy + dy * k, 2)
                if dx and dy and abs(abs(x - cx) - abs(y - cy)) > 1e-6:
                    y = round(cy + dy * abs(x - cx), 2)
                via = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(x), MM(y)), MM(VIA_D / 2))
                stub = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(cx), MM(cy)), pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.3))
                if clear([(pcbnew.F_Cu, via), (pcbnew.B_Cu, via), (layer, stub)], net, x, y):
                    best = (x, y)
                    break
            if best:
                break
        if best:
            placed.append(best)
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
