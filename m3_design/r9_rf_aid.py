#!/usr/bin/env python3
"""Design aid (not in the build): propose the RF strip's fence and stitching GND vias (R9 step 4, D-S4-04).

usage: <KiCad python3> -I m3_design/r9_rf_aid.py BOARD OUT.json [PITCH TARGET PATCH_ROUNDS rect|tri SNAP]
       r9_rf_aid.py board.kicad_pcb out.json 2.5 3.6 3 rect 0.45     (the frozen r9_rf.GRID came from this)

BOARD is r9_rf.py's output built with --no-board-vias (the strip copper without the fence and the grid). The aid
writes OUT.json (fence x list, fence y, grid list) and OUT.kicad_pcb (the board with them, for inspection); the
result is frozen by hand into r9_rf.py (FENCE_X, GRID), which stays the source. Legal spots: 0.5 / 0.6 mm GND vias
clear of every non-GND copper item by its rule clearance (0.15; 0.25 to RF nets; 0.30 to the SMA centre pads; 1.0 to
bare test pads), of GND pads (no via in a pad), of paste apertures, of other vias (rings apart, holes 0.25 mm apart),
0.5 mm from the edge and the holes, outside the launch windows (|x| <= 2.0, y <= 4.6 of each jack), outside part
courtyards (but the modules', the jacks' and the SOT-23s', between whose pads a tented via may sit) and outside the
lane corridors (r9_rf.CORRIDORS). The fence: the farthest legal spot within 1.95 mm, from x 0 to 46 at FENCE_Y. The
grid: a lattice snapped to the nearest legal spot within SNAP mm, then PATCH_ROUNDS rounds that add a via near each
GND copper point farther than TARGET mm (route_check.gnd_reach) from a via.
"""
import json
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
import route_check as rc  # noqa: E402
import check_r9 as C9  # noqa: E402

MM, mm = pcbnew.FromMM, pcbnew.ToMM
RF = {'GNSS_RF_ANT', 'GNSS_RF_IN', 'RADIO_RF_ANT', 'RADIO_RF'}
ALLOW_IN_COURTYARD = {'U30', 'U31', 'J30', 'J31', 'Q30', 'Q31', 'Q32'}
Y_F = C9.Y_F
FENCE_Y = 22.2
SEEDS = [(11.3, 10.66)]      # the limiter pocket under Q30 (hand-placed)


_B = None


def corridors():
    import r9_rf
    return r9_rf.corridor_boxes(r9_rf.Frames(_B))


def build_model(b, r, use_corridors=True):
    """Shapes (SHAPE_POLY_SET) where a via centre of radius r may NOT go."""
    bad = pcbnew.SHAPE_POLY_SET()

    def add(poly):
        bad.BooleanAdd(poly)

    for f in b.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            net = p.GetNetname()
            for lid in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu):
                if not p.IsOnLayer(lid):
                    continue
                if net == 'GND':
                    c = r + 0.12
                else:
                    c = r + 0.15
                    if net in RF:
                        c = r + 0.25
                    if ref in ('J30', 'J31'):
                        c = r + 0.30
                    if ref.startswith('TP'):
                        c = r + 1.0
                ps = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(ps, lid, MM(c), MM(0.005), pcbnew.ERROR_OUTSIDE)
                add(ps)
            for paste in (pcbnew.F_Paste, pcbnew.B_Paste):
                if p.IsOnLayer(paste):
                    ps = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(ps, paste, MM(r + 0.05), MM(0.005), pcbnew.ERROR_OUTSIDE)
                    add(ps)
        if ref not in ALLOW_IN_COURTYARD:
            cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
            if cy.OutlineCount():
                c2 = pcbnew.SHAPE_POLY_SET(cy)
                c2.Inflate(MM(0.05), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MM(0.005))
                add(c2)
    for t in b.GetTracks():
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            c = r + mm(t.GetWidth(pcbnew.F_Cu)) / 2 + (0.15 if net != 'GND' else 0.05)
            c = max(c, 0.15 + 0.25 + mm(t.GetDrillValue()) / 2)      # hole to hole 0.25 (0.3 drills)
            add(circle(t.GetPosition(), c))
            continue
        if net == 'GND':
            continue
        c = r + (0.25 if net in RF else 0.15)
        ps = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(ps, t.GetLayer(), MM(c), MM(0.005), pcbnew.ERROR_OUTSIDE)
        add(ps)
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            add(circle(d.GetCenter(), mm(d.GetRadius()) + 0.5 + r + 0.03))      # min_copper_edge_clearance
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetZoneName().endswith('_launch_In1'):
            bb = z.GetBoundingBox()
            cx = mm(bb.Centre().x)
            add(box(cx - 2.0 - r, -1.0, cx + 2.0 + r, 4.6 + r))    # the launch window stays R7's (r9_rf_check)
    for x0, y0, x1, y1, _ in (corridors() if use_corridors else []):
        add(box(x0 - r, y0 - r, x1 + r, y1 + r))
    bad.Simplify()
    return bad


def circle(c, rad):
    ps = pcbnew.SHAPE_POLY_SET()
    ps.NewOutline()
    for k in range(64):
        a = 2 * math.pi * k / 64
        ps.Append(int(c.x + MM(rad) * math.cos(a)), int(c.y + MM(rad) * math.sin(a)))
    return ps


def box(x0, y0, x1, y1):
    ps = pcbnew.SHAPE_POLY_SET()
    ps.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ps.Append(MM(x), MM(y))
    return ps


def legal(bad, x, y, r):
    if not (0.5 + r <= x <= 46 - 0.5 - r and 0.5 + r <= y):
        return False
    return not bad.Contains(pcbnew.VECTOR2I(MM(x), MM(y)))


def add_via(b, x, y, size):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(size[0]))
    v.SetDrill(MM(size[1]))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(b.FindNet('GND'))
    b.Add(v)
    return v


def fence(b, size=(0.5, 0.3)):
    r = size[0] / 2
    bad = build_model(b, r, use_corridors=False)
    xs = [round(0.05 * k, 2) for k in range(int(46 / 0.05) + 1)]
    ok = [x for x in xs if legal(bad, x, FENCE_Y, r)]
    out, last = [], 0.0
    while True:
        cand = [x for x in ok if last < x <= last + 1.95]
        if last + 1.95 >= 46.0:
            break
        assert cand, f'fence: no legal spot in ({last}, {last + 1.95}]'
        x = max(cand)
        out.append(x)
        last = x
    return out


def nearest_legal(bad, x, y, r, radius=0.9, ymax=None):
    for k in range(0, int(radius / 0.05) + 1):
        rr = 0.05 * k
        n = max(1, int(2 * math.pi * rr / 0.05))
        for i in range(n):
            a = 2 * math.pi * i / n
            px, py = round(x + rr * math.cos(a), 2), round(y + rr * math.sin(a), 2)
            if (ymax is None or py <= ymax) and legal(bad, px, py, r):
                return px, py
    return None


def reach(b, target):
    import time
    t0 = time.time()
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    worst = []
    for lid in (pcbnew.F_Cu, pcbnew.B_Cu):
        pts = rc.gnd_reach(b, lid, (0.0, -1.0, 46.0, Y_F + 5.0), (0.0, -1.0, 46.0, Y_F), limit=40)
        worst += [(9e9 if d is None else d, x, y, b.GetLayerName(lid)) for d, x, y in pts if d is None or d > target]
    worst.sort(reverse=True)
    print('  reach', round(time.time() - t0, 1), 's;', len(worst), 'points beyond', target, worst[:4])
    return worst


def main():
    global _B
    board, out = sys.argv[1], sys.argv[2]
    pitch = float(sys.argv[3]) if len(sys.argv) > 3 else 2.4
    target = float(sys.argv[4]) if len(sys.argv) > 4 else 3.6
    b = pcbnew.LoadBoard(board)
    _B = b
    fx = fence(b)
    for x in fx:
        add_via(b, x, FENCE_Y, (0.5, 0.3))
    print('fence', len(fx), fx)
    grid = []
    for sx, sy in SEEDS:
        add_via(b, sx, sy, (0.6, 0.3))
        grid.append((sx, sy))
    bad = build_model(b, 0.3)
    row = 0
    y = 1.0
    rect_mode = len(sys.argv) > 6 and sys.argv[6] == 'rect'
    snap = float(sys.argv[7]) if len(sys.argv) > 7 else 0.9
    while y <= Y_F - 0.6:
        x = 1.0 + (pitch / 2 if row % 2 and not rect_mode else 0.0)
        while x <= 45.0:
            spot = nearest_legal(bad, x, y, 0.3, radius=snap, ymax=Y_F - 0.5)
            if spot and all(math.dist(spot, g) >= 0.65 for g in grid):
                add_via(b, spot[0], spot[1], (0.6, 0.3))
                grid.append(spot)
                bad.BooleanAdd(circle(pcbnew.VECTOR2I(MM(spot[0]), MM(spot[1])), 0.3 + 0.3 + 0.05))
            x += pitch
        y += pitch if rect_mode else pitch * 0.866
        row += 1
    print('grid', len(grid))
    for it in range(int(sys.argv[5]) if len(sys.argv) > 5 else 0):
        worst = reach(b, target)
        if not worst:
            break
        chosen = []
        bad = build_model(b, 0.3)
        for d, x, y, lay in worst:
            if any(math.dist((x, y), c) < 2.5 for c in chosen):
                continue
            spot = nearest_legal(bad, x, y, 0.3, radius=1.5, ymax=Y_F - 0.5)
            if spot is None:
                print('  no spot near', (round(x, 2), round(y, 2)), lay, round(d, 2))
                continue
            chosen.append(spot)
            bad.BooleanAdd(circle(pcbnew.VECTOR2I(MM(spot[0]), MM(spot[1])), 0.65))
        for sp in chosen:
            add_via(b, sp[0], sp[1], (0.6, 0.3))
            grid.append(sp)
        print('  patch', it, chosen)
        if not chosen:
            break
    worst = reach(b, target)
    clusters = []
    for d, x, y, lay in worst:
        if all(math.dist((x, y), (c[1], c[2])) > 1.0 or lay != c[3] for c in clusters):
            clusters.append((round(d, 2), round(x, 2), round(y, 2), lay))
    print('far clusters', clusters[:40])
    json.dump(dict(fence=fx, fence_y=FENCE_Y, grid=grid), open(out, 'w'), indent=1)
    pcbnew.SaveBoard(out.replace('.json', '.kicad_pcb'), b, True)
    print('grid total', len(grid))


if __name__ == '__main__':
    main()
