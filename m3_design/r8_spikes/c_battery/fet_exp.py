"""ACT_FET_S bridge experiment: place Q121 (rot 270, drain west) and Q120 (rot 90, drain east) with a gap g and
offset d, one ACT_FET_S B.Cu zone between, fill, save. usage: fet_exp.py BASE OUT xa yc g d [margin]"""
import sys, pcbnew
mm, MM = pcbnew.ToMM, pcbnew.FromMM
src, out, xa, yc, g, d = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7])
ext = float(sys.argv[7]) if len(sys.argv) > 7 else 3.0
b = pcbnew.LoadBoard(src)
P = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
xb = xa + 6.38 + g
for ref, x, y, rot in (('Q121', xa, yc, 270), ('Q120', xb, yc + d, 90)):
    f = b.FindFootprintByReference(ref)
    f.SetOrientationDegrees(rot); f.SetPosition(P(x, y))
box = (xa - 4, yc - 6, xb + 4, yc + 6)
for f in list(b.GetFootprints()):
    if f.GetReference() in ('Q120', 'Q121') or not f.IsFlipped():
        continue
    p = f.GetPosition()
    if box[0] < mm(p.x) < box[2] and box[1] < mm(p.y) < box[3]:
        b.Delete(f)
pcbnew.SaveBoard(out, b)       # SWIG proxies break after BOARD.Remove in this build: reload
b = pcbnew.LoadBoard(out)
# move everything else away from the test area (parts within the box) -- only ACT_FET_S matters for the solve
z = pcbnew.ZONE(b); z.SetLayer(pcbnew.B_Cu); z.SetNet(b.FindNet('ACT_FET_S'))
z.SetAssignedPriority(40); z.SetMinThickness(MM(0.2)); z.SetLocalClearance(MM(0.3))
z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
ol = z.Outline(); ol.NewOutline()
x0, x1 = xa + 1.6, xb - 1.6
for x, y in ((x0, yc - ext - 1.3), (x1, yc - ext - 1.3), (x1, yc + ext), (x0, yc + ext)):
    ol.Append(MM(x), MM(y))
b.Add(z)
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(out, b)
print('Q121', xa, yc, 'Q120', xb, yc + d)
