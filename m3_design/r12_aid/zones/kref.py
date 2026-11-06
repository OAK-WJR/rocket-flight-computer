#!/usr/bin/env python3
"""D-R12-96 diagnostic: list check_r12 K-reference loose samples grouped by net and layer, with their extent, so a
router can see which runs lose their reference plane. usage: <KiCad python3> -I -B kref.py BOARD"""
import collections
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import pcbnew                    # noqa: E402
import check_r12 as r12          # noqa: E402
import critical_reference as cr  # noqa: E402

orig = cr.inside
loose = []


def main(path):
    board = pcbnew.LoadBoard(path)

    class C:                     # the only attribute k_reference reads
        pass
    c = C()
    c.board = board
    real_append = list.append
    issues, ev = r12.k_reference(c)
    # recompute the loose list the same way k_reference does, keeping it
    refs = {pcbnew.F_Cu: (pcbnew.In1_Cu, ('GND',)), pcbnew.In2_Cu: (pcbnew.In1_Cu, ('GND',)),
            pcbnew.B_Cu: (pcbnew.In2_Cu, r12.REF_PLANES)}
    nets = r12.reference_nets(board)
    own, voids = r12.r10.own_antipads(board), r12.r10.own_barrel_voids(board)
    empty = pcbnew.SHAPE_POLY_SET()
    out = []
    for rf, tag in ((refs, 'up'), ({pcbnew.In2_Cu: (pcbnew.B_Cu, ('GND',))}, 'In2-vs-B')):
        samples, fill = cr.samples(board, nets, rf), cr.fills(board, rf)
        out += [(s, tag) for s in samples if not cr.inside(fill.get(s[1], empty), s[2], s[3])
                and not r12.r10.in_own_antipad(own, s[0], s[2], s[3])
                and not r12.r10.in_own_antipad(voids, s[0], s[2], s[3])]
    g = collections.defaultdict(list)
    for s, tag in out:
        g[(s[0], board.GetLayerName(s[1]) if isinstance(s[1], int) else s[1], tag)].append((s[2], s[3]))
    print(f'K-reference loose samples: {len(out)} (check_r12 says {ev})')
    for k, pts in sorted(g.items(), key=lambda kv: -len(kv[1])):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        print(f'{len(pts):5d} {k[0]:16s} {k[1]:7s} {k[2]:9s} x {min(xs):.2f}-{max(xs):.2f} y {min(ys):.2f}-{max(ys):.2f}')


if __name__ == '__main__':
    main(sys.argv[1])
