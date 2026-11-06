#!/usr/bin/env python3
"""D-R12-96: dump the placed R12 board's geometry as JSON for zone routers that cannot run KiCad: every pad (ref, number,
net, centre, size, shape, rotation, copper layers, drill), every footprint courtyard (bounding box), the rule areas,
the outline, the via and width rules, and the zone polygons. Board mm, x east, y forward from the aft edge.

usage: <KiCad python3> -I -B m3_design/r12_aid/zones/export_geom.py BOARD OUT.json
"""
import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
mm = pcbnew.ToMM


def main(board_path, out):
    b = pcbnew.LoadBoard(board_path)
    names = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
    pads, parts = [], []
    for fp in b.GetFootprints():
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
        parts.append(dict(ref=fp.GetReference(), value=fp.GetValue(), x=round(mm(fp.GetPosition().x), 4),
                          y=round(mm(fp.GetPosition().y), 4), rot=round(fp.GetOrientationDegrees(), 2),
                          courtyard=[round(mm(bb.GetLeft()), 4), round(mm(bb.GetTop()), 4),
                                     round(mm(bb.GetRight()), 4), round(mm(bb.GetBottom()), 4)]))
        for p in fp.Pads():
            layers = [n for l, n in names.items() if p.IsOnLayer(l)]
            sz = p.GetSize(pcbnew.F_Cu) if hasattr(p, 'GetSize') else p.GetSize()
            pb = p.GetBoundingBox()
            pads.append(dict(ref=fp.GetReference(), pad=p.GetNumber(), net=p.GetNetname(),
                             x=round(mm(p.GetPosition().x), 4), y=round(mm(p.GetPosition().y), 4),
                             w=round(mm(sz.x), 4), h=round(mm(sz.y), 4), rot=round(p.GetOrientationDegrees(), 2),
                             shape=p.ShapeType(p.GetShape(pcbnew.F_Cu)) if False else str(p.GetShape(pcbnew.F_Cu)),
                             bbox=[round(mm(pb.GetLeft()), 4), round(mm(pb.GetTop()), 4),
                                   round(mm(pb.GetRight()), 4), round(mm(pb.GetBottom()), 4)],
                             layers=layers, drill=round(mm(p.GetDrillSize().x), 4) if p.GetDrillSize().x else 0))
    areas = []
    for z in b.Zones():
        if z.GetIsRuleArea():
            o = z.Outline()
            pts = [(round(mm(o.CVertex(i).x), 4), round(mm(o.CVertex(i).y), 4)) for i in range(o.TotalVertices())]
            areas.append(dict(name=z.GetZoneName(), layers=[names[l] for l in names if z.GetLayerSet().Contains(l)],
                              no_tracks=z.GetDoNotAllowTracks(), no_vias=z.GetDoNotAllowVias(), points=pts))
    d = dict(note=__doc__.split('\n')[0], board=dict(w=46, l=100),
             rules=dict(via_pad=0.45, via_drill=0.3, min_track=0.1, min_clearance=0.1, board_floor_clearance=0.1,
                        widths=[0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.8, 1.0], angles='0/45/90 only'),
             parts=parts, pads=pads, rule_areas=areas, zones=json.loads((HERE / 'zones.json').read_text()))
    Path(out).write_text(json.dumps(d, indent=0))
    print(f'export_geom: {len(parts)} parts, {len(pads)} pads, {len(areas)} rule areas -> {out}')


if __name__ == '__main__':
    main(*sys.argv[1:3])
