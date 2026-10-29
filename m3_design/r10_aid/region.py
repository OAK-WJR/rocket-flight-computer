import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); side = sys.argv[2]; x0, x1, y0, y1 = map(float, sys.argv[3:7]); mm = pcbnew.ToMM
for f in sorted(b.GetFootprints(), key=lambda f: (f.GetPosition().y, f.GetPosition().x)):
    s = 'B' if f.IsFlipped() else 'F'
    cy = f.GetCourtyard(pcbnew.B_CrtYd if s == 'B' else pcbnew.F_CrtYd); bb = cy.BBox()
    bx0, by0, bx1, by1 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())
    tht = any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in f.Pads())
    if (s == side or tht) and bx0 < x1 and bx1 > x0 and by0 < y1 and by1 > y0:
        print(f'{f.GetReference():6s}{s} box x {bx0:6.2f}-{bx1:6.2f} y {by0:6.2f}-{by1:6.2f}' + (' THT' if tht else ''))
