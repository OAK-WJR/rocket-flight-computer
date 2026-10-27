"""Placement iteration tool. usage: ptool.py base.kicad_pcb moves.tsv out_prefix [L]
moves.tsv rows: ref x y rot side  (or '@group dx dy refs...' to translate a set). Writes out_prefix.kicad_pcb,
prints violations, and makes out_prefix_map.kicad_pcb for rendering."""
import pcbnew, sys, math
base, moves, out = sys.argv[1:4]
MM, mm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(base)
fp = {f.GetReference(): f for f in b.GetFootprints()}
def setpos(f, x, y, rot, side):
    want_b = side == 'B'
    if f.IsFlipped() != want_b: f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(float(rot)); f.SetPosition(pcbnew.VECTOR2I(MM(float(x)), MM(float(y))))
for line in open(moves):
    t = line.split('#')[0].split()
    if not t: continue
    if t[0] == '@group':
        dx, dy = float(t[1]), float(t[2])
        for r in t[3:]:
            p = fp[r].GetPosition(); fp[r].SetPosition(pcbnew.VECTOR2I(p.x + MM(dx), p.y + MM(dy)))
    else:
        setpos(fp[t[0]], *t[1:5])
b.BuildConnectivity()
pcbnew.SaveBoard(out + '.kicad_pcb', b)
# checks
ol = b.GetBoardEdgesBoundingBox()
X0, Y0, X1, Y1 = mm(ol.GetX()), mm(ol.GetY()), mm(ol.GetRight()), mm(ol.GetBottom())
holes = []
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
        c = d.GetCenter(); holes.append((mm(c.x), mm(c.y), mm(d.GetRadius())))
EDGEOK = {'J3', 'J9', 'J410', 'J420'}
boxes = {}
for r, f in fp.items():
    back = f.IsFlipped()
    cy = f.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
    boxes[r] = ('B' if back else 'F', mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))
tht = [(r, mm(p.GetPosition().x), mm(p.GetPosition().y)) for r, f in fp.items() for p in f.Pads()
       if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
bad = []
rs = sorted(boxes)
for i, a in enumerate(rs):
    sa, ax0, ay0, ax1, ay1 = boxes[a]
    if a not in EDGEOK and (ax0 < X0 - 1e-6 or ay0 < Y0 - 1e-6 or ax1 > X1 + 1e-6 or ay1 > Y1 + 1e-6):
        bad.append(f'outline {a}')
    for hx, hy, hr in holes:
        if ax0 - hr < hx < ax1 + hr and ay0 - hr < hy < ay1 + hr:
            # circle-rect test
            cx = min(max(hx, ax0), ax1); cy_ = min(max(hy, ay0), ay1)
            if math.hypot(hx - cx, hy - cy_) < hr: bad.append(f'hole {a} ({hx},{hy})')
    if sa == 'B':
        for r, px, py in tht:
            if r != a and ax0 - 1.0 < px < ax1 + 1.0 and ay0 - 1.0 < py < ay1 + 1.0: bad.append(f'tht {a} near {r} pin')
    for bref in rs[i + 1:]:
        sb, bx0, by0, bx1, by1 = boxes[bref]
        if sa == sb and ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1:
            # exact courtyard polygon test
            fa, fb = fp[a], fp[bref]
            la = pcbnew.B_CrtYd if sa == 'B' else pcbnew.F_CrtYd
            pa, pb = fa.GetCourtyard(la), fb.GetCourtyard(la)
            if pa.OutlineCount() and pb.OutlineCount() and not pa.Collide(pb.Outline(0)) and not pb.Collide(pa.Outline(0)):
                cA = pa.Outline(0); cB = pb.Outline(0)
                hit = any(cA.PointInside(cB.CPoint(k)) for k in range(cB.PointCount())) or \
                      any(cB.PointInside(cA.CPoint(k)) for k in range(cA.PointCount()))
                if not hit: continue
            bad.append(f'overlap {sa} {a} {bref}')
print(f'outline {X1-X0:.1f} x {Y1-Y0:.1f}; {len(bad)} placement violations')
for x in bad: print('  ' + x)
