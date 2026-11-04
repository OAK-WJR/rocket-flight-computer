#!/usr/bin/env python3
"""R12 routing drafting aid, step 1 (D-R12-26): export the placed board's geometry for the router (route.py).
Not part of the build. usage: <KiCad python3> -I -B m3_design/r12_aid/export.py BOARD OUT.json"""
import json
import sys

import pcbnew

mm = pcbnew.ToMM
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}


def poly(ps):
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        out.append([(round(mm(o.CPoint(j).x), 5), round(mm(o.CPoint(j).y), 5)) for j in range(o.PointCount())])
    return out


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    fps = []
    for f in b.GetFootprints():
        pads = []
        for p in f.Pads():
            lay = [LN[l] for l in LN if p.IsOnLayer(l)]
            attr = {pcbnew.PAD_ATTRIB_SMD: 'smd', pcbnew.PAD_ATTRIB_PTH: 'pth', pcbnew.PAD_ATTRIB_NPTH: 'npth'}.get(
                p.GetAttribute(), 'conn')
            shape = p.GetEffectivePolygon(pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu)
            lc = p.GetLocalClearance()
            pads.append(dict(num=p.GetNumber(), net=p.GetNetname(), x=mm(p.GetPosition().x), y=mm(p.GetPosition().y),
                             attr=attr, layers=lay, drill=mm(p.GetDrillSize().x), poly=poly(shape) if lay else [],
                             clr=mm(lc) if lc else 0.0))
        cb = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
        fps.append(dict(ref=f.GetReference(), x=mm(f.GetPosition().x), y=mm(f.GetPosition().y),
                        rot=f.GetOrientationDegrees(), pads=pads,
                        crt=[mm(cb.GetLeft()), mm(cb.GetTop()), mm(cb.GetRight()), mm(cb.GetBottom())]))
    zones = [dict(name=z.GetZoneName(), rule=z.GetIsRuleArea(), layers=[LN[l] for l in LN if z.IsOnLayer(l)],
                  net=z.GetNetname(), outline=poly(z.Outline()),
                  notracks=bool(z.GetIsRuleArea() and z.GetDoNotAllowTracks()),
                  novias=bool(z.GetIsRuleArea() and z.GetDoNotAllowVias())) for z in b.Zones()]
    holes = [(mm(d.GetCenter().x), mm(d.GetCenter().y), mm(d.GetRadius())) for d in b.GetDrawings()
             if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    bb = b.GetBoardEdgesBoundingBox()
    json.dump(dict(fps=fps, zones=zones, holes=holes,
                   outline=[mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())]),
              open(sys.argv[2], 'w'))
    print('export:', len(fps), 'footprints')


if __name__ == '__main__':
    main()
