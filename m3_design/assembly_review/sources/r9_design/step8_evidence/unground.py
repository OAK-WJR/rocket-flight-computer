#!/usr/bin/env python3
"""The step-7 board back from a built R9 board (evidence aid, not in the build): the rows of m3_design/r9_ground.tsv
deleted, R9_GND_F / _B / _In1 shrunk to the strip (r9_ground.STRIP_BOX) under their step-4 names, the crystal plane
(r9_ground.XTAL_ZONE) deleted and its rule area's step-3 flags restored, every via's pads back on every layer
(D-S8-19 / 20), refilled. It lets
r9_ground_aid.py --check and the step-8 deltas (step8_deltas.txt) run from the built board alone.

usage: <KiCad python3> -I unground.py BUILT.kicad_pcb OUT.kicad_pcb      (OUT beside m3.kicad_pro / m3.kicad_dru)
"""
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'm3_design'))
import r9_ground as G  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    rows = G.read()
    vq = {(G.r4(float(r['x0'])), G.r4(float(r['y0']))) for r in rows if r['item'] == 'via'}
    tq = {tuple(G.r4(float(r[k])) for k in ('x0', 'y0', 'x1', 'y1')) for r in rows if r['item'] == 'track'}
    n = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() != 'GND':
            continue
        if t.GetClass() == 'PCB_VIA' and (G.r4(mm(t.GetPosition().x)), G.r4(mm(t.GetPosition().y))) in vq:
            b.Delete(t)
            n += 1
        elif t.GetClass() == 'PCB_TRACK' and (G.r4(mm(t.GetStart().x)), G.r4(mm(t.GetStart().y)),
                                              G.r4(mm(t.GetEnd().x)), G.r4(mm(t.GetEnd().y))) in tq:
            b.Delete(t)
            n += 1
    for old, new, *_ in G.POURS:
        z = [z for z in b.Zones() if z.GetZoneName() == new][0]
        o = z.Outline()
        o.RemoveAllContours()
        o.NewOutline()
        for x, y in G.box_points(G.STRIP_BOX):
            o.Append(MM(x), MM(y))
        z.SetZoneName(old)
    for z in list(b.Zones()):
        if z.GetZoneName() == G.XTAL_ZONE[0]:
            b.Delete(z)
        elif z.GetZoneName() == G.XTAL_AREA:
            z.SetDoNotAllowTracks(G.XTAL_FLAGS_STEP3[0])
            z.SetDoNotAllowZoneFills(G.XTAL_FLAGS_STEP3[3])
            assert G.area_flags(z) == G.XTAL_FLAGS_STEP3
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            t.Padstack().SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL)
    for z in b.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    b.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    assert pcbnew.SaveBoard(sys.argv[2], b, True)
    print(f'removed {n} of {len(vq) + len(tq)} table items; pours back to the strip')


if __name__ == '__main__':
    main()
