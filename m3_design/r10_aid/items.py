import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); x0, x1, y0, y1 = map(float, sys.argv[2:6]); mm = pcbnew.ToMM
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        p = t.GetPosition()
        if x0 < mm(p.x) < x1 and y0 < mm(p.y) < y1: print('via', t.GetNetname(), round(mm(p.x), 3), round(mm(p.y), 3))
    else:
        a, c = t.GetStart(), t.GetEnd()
        if any(x0 < mm(q.x) < x1 and y0 < mm(q.y) < y1 for q in (a, c)):
            print('trk', t.GetNetname(), t.GetLayerName(), round(mm(t.GetWidth()), 2), (round(mm(a.x), 3), round(mm(a.y), 3)), (round(mm(c.x), 3), round(mm(c.y), 3)))
