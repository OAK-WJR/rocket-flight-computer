#!/usr/bin/env python3
"""Nearest copper of every other net to the armed-live pyro copper (PYRO1_BUS / IGN / OUT), per layer and net, with
the exposed-or-covered state of both items (R8 step 9 pyro requalification; compare R7 and R8).

usage: <KiCad python3> pyro_neighbours.py BOARD.kicad_pcb [OUT.json]

Read-only. For each other net within 3 mm of any PYRO1_BUS / PYRO1_IGN / PYRO1_OUT pad, track, via or fill on the same
copper layer: the closest approach, both items, and whether each is bare (a pad with a mask opening on that face) or
covered (mask or inner layer). DRC rules A-H (m3.kicad_dru) bound every pair; this lists what sits at or near them.
"""
import json
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'tools'))
import check_r8 as C8  # noqa: E402

LIVE = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
REACH = 3.0


def bare(it, lay):
    obj = it[4]
    if not isinstance(obj, pcbnew.PAD):
        return False
    return (lay == pcbnew.F_Cu and obj.IsOnLayer(pcbnew.F_Mask)) or (lay == pcbnew.B_Cu and obj.IsOnLayer(pcbnew.B_Mask))


def main(path, out=None):
    b = pcbnew.LoadBoard(path)
    items = C8.net_items(b, lambda n: True)
    live = [it for it in items if it[1] in LIVE]
    rows = {}
    for it in items:
        if it[1] in LIVE or not it[1]:
            continue
        for lv in live:
            if lv[2] != it[2]:
                continue
            A, B = lv[3].BBox(), it[3].BBox()
            g0 = pcbnew.FromMM(REACH)
            if A.GetRight() + g0 < B.GetLeft() or B.GetRight() + g0 < A.GetLeft() or A.GetBottom() + g0 < B.GetTop() \
                    or B.GetBottom() + g0 < A.GetTop():
                continue
            g = C8.min_gap(lv[3], it[3], REACH)
            if g is None:
                continue
            key = (it[1], b.GetLayerName(it[2]))
            if key not in rows or g < rows[key]['mm']:
                rows[key] = dict(mm=g, live=f'{lv[0]} ({lv[1]}, {"bare" if bare(lv, lv[2]) else "covered"})',
                                 other=f'{it[0]} ({"bare" if bare(it, it[2]) else "covered"})')
    res = [dict(net=k[0], layer=k[1], **v) for k, v in sorted(rows.items(), key=lambda kv: kv[1]['mm'])]
    for r in res:
        print(f"{r['mm']:6.3f}  {r['net']:18s} {r['layer']:7s} {r['live']:40s} {r['other']}")
    if out:
        json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:])
