import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
for r in sys.argv[2:]:
    f = b.FindFootprintByReference(r); back = f.IsFlipped()
    cy = f.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd); bb = cy.BBox()
    p = f.GetPosition()
    print(f'{r} {"B" if back else "F"} pos ({mm(p.x):.2f},{mm(p.y):.2f}) r{f.GetOrientationDegrees():.0f} box x {mm(bb.GetX()):.2f}-{mm(bb.GetRight()):.2f} y {mm(bb.GetY()):.2f}-{mm(bb.GetBottom()):.2f}',
          ' pads ' + ' '.join(f'{pd.GetNumber()}:({mm(pd.GetPosition().x):.2f},{mm(pd.GetPosition().y):.2f})' for pd in f.Pads()) if f.GetPadCount() <= 4 else '')
