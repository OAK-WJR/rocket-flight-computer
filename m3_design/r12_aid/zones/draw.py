import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); out = sys.argv[2]
mm = pcbnew.ToMM
bb = b.GetBoardEdgesBoundingBox(); x0, y0 = mm(bb.GetX()), mm(bb.GetY()); W, H = mm(bb.GetWidth()), mm(bb.GetHeight())
side = max(W, H) + 4; ox = x0 - (side - W) / 2; oy = y0 - (side - H) / 2
col = {'F.Cu': '#d23c3c', 'B.Cu': '#2f6fd6', 'In2.Cu': '#2fa84f', 'In1.Cu': '#999999'}
for want, name in ((['F.Cu'], 'top'), (['B.Cu'], 'bot'), (['F.Cu', 'B.Cu'], 'both'), (['In2.Cu'], 'in2')):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{ox} {oy} {side} {side}" width="2400" height="2400"><rect x="{ox}" y="{oy}" width="{side}" height="{side}" fill="white"/>',
         f'<rect x="{x0}" y="{y0}" width="{W}" height="{H}" fill="#f4f1e6" stroke="black" stroke-width="0.1"/>']
    for fp in b.GetFootprints():
        r = fp.GetBoundingBox(False)
        s.append(f'<rect x="{mm(r.GetX())}" y="{mm(r.GetY())}" width="{mm(r.GetWidth())}" height="{mm(r.GetHeight())}" fill="none" stroke="#bbbbbb" stroke-width="0.05"/>')
        s.append(f'<text x="{mm(fp.GetPosition().x)}" y="{mm(fp.GetPosition().y)}" font-size="0.6" fill="#888" text-anchor="middle">{fp.GetReference()}</text>')
        for p in fp.Pads():
            if not any(p.IsOnLayer(b.GetLayerID(l)) for l in want): continue
            r = p.GetBoundingBox()
            s.append(f'<rect x="{mm(r.GetX())}" y="{mm(r.GetY())}" width="{mm(r.GetWidth())}" height="{mm(r.GetHeight())}" fill="#c9a14a" opacity="0.8"/>')
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            c = t.GetPosition(); s.append(f'<circle cx="{mm(c.x)}" cy="{mm(c.y)}" r="{mm(t.GetWidth(pcbnew.F_Cu))/2}" fill="#333"/>'); continue
        ln = b.GetLayerName(t.GetLayer())
        if ln not in want: continue
        a, e = t.GetStart(), t.GetEnd()
        s.append(f'<line x1="{mm(a.x)}" y1="{mm(a.y)}" x2="{mm(e.x)}" y2="{mm(e.y)}" stroke="{col[ln]}" stroke-width="{mm(t.GetWidth())}" stroke-linecap="round" opacity="0.85"/>')
    s.append('</svg>')
    open(f'{out}/{name}.svg', 'w').write('\n'.join(s))
