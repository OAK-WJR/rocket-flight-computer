import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
for r in sys.argv[2:]:
    f = b.FindFootprintByReference(r)
    s = 'B' if f.IsFlipped() else 'F'
    out = []
    for p in sorted(f.Pads(), key=lambda p: p.GetNumber()):
        sz = p.GetSize(pcbnew.F_Cu if s == 'F' else pcbnew.B_Cu)
        out.append(f'{p.GetNumber()}:{p.GetNetname()}@({mm(p.GetPosition().x):.3f},{mm(p.GetPosition().y):.3f}){mm(sz.x):.2f}x{mm(sz.y):.2f}')
    print(r, s, ' '.join(out))
