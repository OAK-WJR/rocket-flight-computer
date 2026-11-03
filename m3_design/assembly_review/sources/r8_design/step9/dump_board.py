#!/usr/bin/env python3
"""Dump a board's parts, pads, vias, holes and silkscreen texts to JSON for the step-9 requalification measurements.

usage: <KiCad python3> dump_board.py BOARD.kicad_pcb OUT.json

Read-only. Coordinates are KiCad mm (x = 0 the left long edge, y = 0 the aft edge on R7/R8). For each footprint:
reference, value, LCSC field, position, rotation, side, attributes (SMD / THT / board-only / DNP / excluded from
BOM or position files), the courtyard bounding box on its side, and every pad (number, net, centre, layers, whether its
copper is exposed by a solder-mask opening on F or B, drill size, and its bounding box). Vias (net, position, sizes)
and Edge.Cuts circles (the milled holes) follow, then every silkscreen text with its layer and bounding box.
"""
import json
import sys

import pcbnew

mm = pcbnew.ToMM


def box(b):
    return [round(mm(b.GetX()), 4), round(mm(b.GetY()), 4), round(mm(b.GetRight()), 4), round(mm(b.GetBottom()), 4)]


def main(path, out):
    b = pcbnew.LoadBoard(path)
    fps = []
    for f in b.GetFootprints():
        side = 'B' if f.GetLayer() == pcbnew.B_Cu else 'F'
        crt = f.GetCourtyard(pcbnew.B_CrtYd if side == 'B' else pcbnew.F_CrtYd)
        cbox = box(crt.BBox()) if crt.OutlineCount() else None
        attrs = f.GetAttributes()
        pads = []
        for p in f.Pads():
            pb = p.GetBoundingBox()
            pads.append(dict(
                num=p.GetNumber(), net=p.GetNetname(), x=round(mm(p.GetPosition().x), 4),
                y=round(mm(p.GetPosition().y), 4), box=box(pb),
                attrib={pcbnew.PAD_ATTRIB_PTH: 'PTH', pcbnew.PAD_ATTRIB_SMD: 'SMD', pcbnew.PAD_ATTRIB_CONN: 'CONN',
                        pcbnew.PAD_ATTRIB_NPTH: 'NPTH'}.get(p.GetAttribute(), '?'),
                F=p.IsOnLayer(pcbnew.F_Cu), B=p.IsOnLayer(pcbnew.B_Cu),
                maskF=p.IsOnLayer(pcbnew.F_Mask), maskB=p.IsOnLayer(pcbnew.B_Mask),
                pasteF=p.IsOnLayer(pcbnew.F_Paste), pasteB=p.IsOnLayer(pcbnew.B_Paste),
                drill=round(mm(p.GetDrillSize().x), 4)))
        lcsc = f.GetField('LCSC').GetText() if f.HasField('LCSC') else ''
        fps.append(dict(
            ref=f.GetReference(), value=f.GetValue(), lcsc=lcsc, fpid=str(f.GetFPID().GetLibItemName()),
            x=round(mm(f.GetPosition().x), 4), y=round(mm(f.GetPosition().y), 4),
            rot=round(f.GetOrientationDegrees(), 3), side=side,
            smd=bool(attrs & pcbnew.FP_SMD), tht=bool(attrs & pcbnew.FP_THROUGH_HOLE),
            board_only=bool(attrs & pcbnew.FP_BOARD_ONLY), dnp=bool(attrs & pcbnew.FP_DNP),
            no_bom=bool(attrs & pcbnew.FP_EXCLUDE_FROM_BOM), no_pos=bool(attrs & pcbnew.FP_EXCLUDE_FROM_POS_FILES),
            courtyard=cbox, ref_visible=f.Reference().IsVisible(), ref_layer=f.Reference().GetLayerName(),
            pads=pads))
    vias = []
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            vias.append(dict(net=t.GetNetname(), x=round(mm(t.GetPosition().x), 4), y=round(mm(t.GetPosition().y), 4),
                             size=round(mm(t.GetWidth(pcbnew.F_Cu)), 4), drill=round(mm(t.GetDrillValue()), 4)))
    holes, texts = [], []
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetClass() == 'PCB_SHAPE' and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            holes.append(dict(x=round(mm(d.GetCenter().x), 4), y=round(mm(d.GetCenter().y), 4),
                              r=round(mm(d.GetRadius()), 4)))
        if d.GetClass() in ('PCB_TEXT', 'PCB_TEXTBOX') and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            texts.append(dict(text=d.GetText(), layer=d.GetLayerName(), box=box(d.GetBoundingBox()),
                              x=round(mm(d.GetPosition().x), 4), y=round(mm(d.GetPosition().y), 4)))
    edge = box(b.GetBoardEdgesBoundingBox())
    json.dump(dict(board=path, edge_bbox=edge, footprints=fps, vias=vias, holes=holes, texts=texts),
              open(out, 'w'), indent=0)
    print(f'{len(fps)} footprints, {len(vias)} vias, {len(holes)} Edge.Cuts circles, {len(texts)} silk texts -> {out}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
