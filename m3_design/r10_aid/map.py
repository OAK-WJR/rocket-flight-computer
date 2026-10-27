# Placement map: copy the board, draw every courtyard bbox and designator on silk, render both faces.
import pcbnew, sys, subprocess
src, out = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
for f in b.GetFootprints():
    back = f.IsFlipped()
    lay = pcbnew.B_SilkS if back else pcbnew.F_SilkS
    for it in list(f.GraphicalItems()):
        if it.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS): f.Remove(it)
    cy = f.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
    r = pcbnew.PCB_SHAPE(b); r.SetShape(pcbnew.SHAPE_T_RECT); r.SetLayer(lay)
    r.SetStart(bb.GetOrigin()); r.SetEnd(bb.GetEnd()); r.SetWidth(pcbnew.FromMM(0.05)); b.Add(r)
    t = pcbnew.PCB_TEXT(b); t.SetText(f.GetReference()); t.SetLayer(lay)
    s = max(0.45, min(1.2, pcbnew.ToMM(min(bb.GetWidth(), bb.GetHeight())) * 0.35))
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(s), pcbnew.FromMM(s))); t.SetTextThickness(pcbnew.FromMM(s * 0.15))
    t.SetPosition(bb.GetCenter()); t.SetMirrored(back); b.Add(t)
    f.Reference().SetVisible(False); f.Value().SetVisible(False)
pcbnew.SaveBoard(out, b)
