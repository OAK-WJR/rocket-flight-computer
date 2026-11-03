#!/usr/bin/env python3
"""Causes of the R9 board's unreferenced critical samples (scorecard R6b; R9_DECISIONS D-S8-17, session 2):
critical_reference.py's R6 sampling (centre and both copper edges every 0.01 mm; F.Cu against In1 GND, B.Cu against In2
GND / 3V3 / 3V3A), each unreferenced sample classed by r9_ground_check.reference_sides: inside its own net's via antipad
(within REF_OWN_R of a same-net via), per via side, or outside (a keep-out, a split, another net's antipad). A side is
"one-branch" when one track of the net leaves the via's antipad on that layer, else "multi-branch".

usage: <KiCad python3> -I reference_causes.py BOARD
"""
import collections
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
import critical_reference as CR  # noqa: E402
import r9_ground_check as GC  # noqa: E402

mm = pcbnew.ToMM


def branches(b):
    """{(net, via centre, layer name): the net's tracks on that layer leaving the via's antipad (a segment with one end
    within GC.REF_OWN_R of the via centre and the other beyond it)}"""
    vias = [(t.GetNetname(), (round(mm(t.GetPosition().x), 4), round(mm(t.GetPosition().y), 4)))
            for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() in CR.R6_NETS]
    out = collections.Counter()
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetNetname() not in CR.R6_NETS:
            continue
        a = (mm(t.GetStart().x), mm(t.GetStart().y))
        c = (mm(t.GetEnd().x), mm(t.GetEnd().y))
        for net, q in vias:
            if net == t.GetNetname() and (math.dist(a, q) < GC.REF_OWN_R) != (math.dist(c, q) < GC.REF_OWN_R):
                out[(net, q, pcbnew.LayerName(t.GetLayer()))] += 1
    return out


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    rep = CR.compare(b, b, 0.0, False)
    sides, stray = GC.reference_sides(b)
    br = branches(b)
    one = {k: v for k, v in sides.items() if br.get(tuple(_key(k)), 1) == 1}
    multi = {k: v for k, v in sides.items() if k not in one}
    n, tot = rep['candidate_unreferenced'], rep['candidate_samples']
    print(f'samples {tot}, unreferenced {n} ({n / tot:.4f})')
    print(f'  own antipad, one-branch sides: {len(one)} sides, {sum(one.values())} samples')
    print(f'  own antipad, multi-branch sides: {len(multi)} sides, {sum(multi.values())} samples')
    by = collections.Counter(f'{net} {layer}' for net, layer, _, _ in stray)
    print(f'  outside every own antipad: {len(stray)} {dict(sorted(by.items()))} e.g. {stray[:2]}')
    print(f'  critical layer-change vias: {len({k.rsplit(" ", 1)[0] for k in sides})}')
    for k in sorted(sides):
        print(f'    {k:40s} {sides[k]:5d}  branches {br.get(tuple(_key(k)), "?")}')


def _key(k):
    """'NET (x, y) F.Cu' -> (net, (x, y), layer)"""
    net, rest = k.split(' ', 1)
    xy, layer = rest.rsplit(' ', 1)
    x, y = (float(v) for v in xy.strip('()').split(','))
    return net, (round(x, 4), round(y, 4)), layer


if __name__ == '__main__':
    main()
