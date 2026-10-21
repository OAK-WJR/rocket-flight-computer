#!/usr/bin/env python3
"""Compare check_r8's strip_gcpw profile of a board with R7's, sample by sample.

usage: <KiCad python3> -I gcpw_compare.py r7.kicad_pcb board.kicad_pcb

check_r8 hashes the profile (the F.Cu GND distance beside every RF track, every 0.05 mm, to 1.5 mm in 0.01 mm steps).
This tool says where a changed digest comes from: each differing sample with both distances, and whether the
coplanar gap itself (the first GND within GAP_LIMIT of the line edge, the geometry of the pass-2 field solve) moved.
"""
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import check_r8  # noqa: E402

GAP_LIMIT = 30          # 0.30 mm in scan steps: the 0.25 mm coplanar gap plus margin


def main():
    a = check_r8.gcpw_profile(pcbnew.LoadBoard(sys.argv[1]))
    b = check_r8.gcpw_profile(pcbnew.LoadBoard(sys.argv[2]))
    assert set(a) == set(b), 'RF track sets differ'
    total = diff = gap_moved = 0
    for key in sorted(a):
        step = check_r8.GCPW_STEP
        for i, (sa, sb) in enumerate(zip(a[key], b[key])):
            for side, va, vb in (('left', sa[0], sb[0]), ('right', sa[1], sb[1])):
                total += 1
                if va == vb:
                    continue
                diff += 1
                near = 0 <= va <= GAP_LIMIT or 0 <= vb <= GAP_LIMIT
                gap_moved += near
                da = va / 100 if va >= 0 else 'none'
                db = vb / 100 if vb >= 0 else 'none'
                print(f'{key[:40]:40s} sample {i:3d} (+{i * step:.2f} mm) {side:5s}: R7 {da} -> {db} mm'
                      f'{"  <-- coplanar gap" if near else ""}')
    print(f'{diff} of {total} side samples differ; {gap_moved} within {GAP_LIMIT / 100:.2f} mm of the line '
          f'(the coplanar gap)')


if __name__ == '__main__':
    main()
