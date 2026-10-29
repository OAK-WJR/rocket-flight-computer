#!/usr/bin/env python3
"""Panel-tab window scan of a board's long edges (the Strategy B prototype's partial/tabs.py rule, unchanged):
a 5 mm tab window on an edge must keep 1.5 mm from part courtyards, 5 mm from capacitors / R166 / LED2 / the modules
and 2 mm from connectors, and 1.5 mm from the M3 and tie holes.

usage: <KiCad python3> -I tab_scan.py board.kicad_pcb
"""
import re
import sys

import pcbnew

mm = pcbnew.ToMM
CAPLIKE = re.compile(r'^(C\d+|R166|LED2|TH\d|U30|U31)$')
CONN = re.compile(r'^(J\d+)$')
HOLES = [(4, 4), (42.3, 4), (4, 64), (4, 114.4), (42, 114.4), (21.5, 68.6), (27.0, 82.6)]


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    items = []
    for f in b.GetFootprints():
        for lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            s = f.GetCourtyard(lay)
            if s and s.OutlineCount():
                bb = s.BBox()
                items.append((f.GetReference(), mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()),
                              mm(bb.GetBottom())))

    def ok(edge, y0, y1):
        x = 0.0 if edge == 'L' else 46.0
        for ref, left, top, right, bottom in items:
            if ref in ('J30', 'J31'):
                continue
            dx = max(left - x, x - right, 0)
            dy = max(top - y1, y0 - bottom, 0)
            need = 5.0 if CAPLIKE.match(ref) else 2.0 if CONN.match(ref) else 1.5
            if (dx * dx + dy * dy) ** 0.5 < need:
                return False
        for hx, hy in HOLES:
            dx = abs(hx - x) - 1.6
            dy = max(y0 - hy, hy - y1, 0)
            if (max(dx, 0) ** 2 + dy ** 2) ** 0.5 < 1.5:
                return False
        return True
    for edge in ('L', 'R'):
        spans = []
        y = 0.5
        while y + 5 <= 117.5:
            if ok(edge, y, y + 5):
                if spans and y - spans[-1][1] <= 0.51:
                    spans[-1][1] = y
                else:
                    spans.append([y, y])
            y += 0.5
        print(edge, 'edge 5 mm tab windows (y ranges):', [(round(a, 1), round(c + 5, 1)) for a, c in spans])


if __name__ == '__main__':
    main()
