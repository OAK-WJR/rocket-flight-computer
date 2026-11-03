#!/usr/bin/env python3
"""Silkscreen inside the board outline (REQUIREMENTS M2). KiCad's DRC does not test silkscreen that lies
wholly outside Edge.Cuts (validation pass 4: C89's reference text sat off the left edge and DRC passed),
so this exports the silkscreen and Edge.Cuts Gerbers and checks every stroke, aperture included,
against the outline's extent.

usage: python3 tools/silk_check.py [board.kicad_pcb] [--cli kicad-cli]      exit 0 = all silkscreen on the board
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def strokes(path):
    """(x, y, r) for every flash and draw end point of a Gerber file, r = aperture radius (mm)."""
    t = path.read_text()
    fs = re.search(r'%FSLAX(\d)(\d)Y(\d)(\d)\*%', t)
    assert fs and '%MOMM*%' in t, f'{path.name}: expected metric Gerber with a format statement'
    scale = 10 ** int(fs.group(2))
    apert = {}
    for m in re.finditer(r'%ADD(\d+)([A-Za-z_]+),([\d.]+)(?:X([\d.]+))?', t):
        w, h = float(m.group(3)), float(m.group(4) or m.group(3))
        apert[m.group(1)] = (w / 2) if m.group(2) == 'C' else (w * w + h * h) ** 0.5 / 2
    out, x, y, r = [], 0.0, 0.0, 0.0
    for cmd in re.findall(r'[^*%]+(?=\*)', t):
        cmd = cmd.strip()
        d = re.fullmatch(r'D(\d+)', cmd) or re.fullmatch(r'G54D(\d+)', cmd)
        if d and int(d.group(1)) >= 10:
            r = apert.get(d.group(1), 0.0)
            continue
        m = re.fullmatch(r'(?:G0?[123])?(?:X(-?\d+))?(?:Y(-?\d+))?(?:I-?\d+)?(?:J-?\d+)?D0?([123])', cmd)
        if not m:
            continue
        if m.group(1) is not None:
            x = int(m.group(1)) / scale
        if m.group(2) is not None:
            y = int(m.group(2)) / scale
        out.append((x, y, r))                # D01 draw end, D02 move (a draw's start), D03 flash
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', default=str(ROOT / 'm3_design/assembly_review/m3.kicad_pcb'))
    ap.add_argument('--cli', default='kicad-cli')
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([a.cli, 'pcb', 'export', 'gerbers', '--no-protel-ext', '--layers', 'F.Silkscreen,B.Silkscreen,Edge.Cuts',
                        '-o', tmp + '/', a.board], check=True, capture_output=True)
        files = {p.name: p for p in Path(tmp).iterdir()}
        edge = next(p for n, p in files.items() if 'Edge_Cuts' in n)
        ex = [(x, y) for x, y, _ in strokes(edge)]
        x0, x1 = min(v[0] for v in ex), max(v[0] for v in ex)
        y0, y1 = min(v[1] for v in ex), max(v[1] for v in ex)
        bad = []
        for n, p in sorted(files.items()):
            if 'Silkscreen' not in n:
                continue
            for x, y, r in strokes(p):
                if x - r < x0 or x + r > x1 or y - r < y0 or y + r > y1:
                    bad.append((n, round(x, 3), round(-y, 3)))
    print(f'silkscreen outside the board outline ({x1 - x0:.2f} x {y1 - y0:.2f} mm): {len(bad)} stroke points')
    for b in bad[:10]:
        print('  ', b[0], f'at ({b[1]}, {b[2]}) mm (KiCad coordinates)')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
