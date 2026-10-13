#!/usr/bin/env python3
"""Envelope check (REQUIREMENTS P2): every part's 3D model, and the assumed mated envelopes, inside the bore.

usage: <KiCad python3> tools/fit_check.py [board.kicad_pcb] [--radius 24.9] [--axis-x 23.0] [--tol 0.3]
       exit 0 = every margin >= 0

The board sits with its top face on the bore axis and its centreline on the axis (P2). Each footprint's 3D
model (WRL boxes and point sets, or STEP CARTESIAN_POINTs; KiCad's model offset, rotation and scale applied)
gives a bounding box in board coordinates; top-side boxes rise from z = 0, bottom-side boxes hang from
z = -1.6 (the board's bottom face). The margin of a box is the usable radius minus the distance from the axis
to its farthest corner, after moving the board by the sled tolerance (--tol, both axes, worst direction).
The default radius 24.9 mm is the Ø50.8 mm coupler bore less the 0.5 mm wall allowance; R5 checks the whole
board against it, so the result holds wherever the board sits in the bay.

Mated envelopes (assumptions, not models; see docs/M3_R5.md): J122 with four servo plugs and their wire bend
(±4.0 mm about the header centre in x, 23.5 mm above the board, as in the R4 fit calculation), J123 with its
PH plug and wire (±3.0 mm, 9.5 mm). Wire entries of the screw terminals face the walls or the aft end; the side-facing
ones' bend room is reported separately (from the entry face to the Ø50.8 mm wall at 5 mm height, sled tolerance
both ways).
"""
import argparse
import math
import re
import sys
from pathlib import Path

import pcbnew

mm = pcbnew.ToMM
BOARD_T = 1.6
MATED = {'J122': (4.0, 23.5), 'J123': (3.0, 9.5)}
SIDE_ENTRY = ('J9', 'J120', 'J121', 'J124', 'J125')   # screw terminals whose wire entries face a long edge (the wall)
BORE_R, WIRE_Z = 25.4, 5.0                             # the coupler bore's wall; wire height above the top face


def _nums(s):
    return [float(v) for v in re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', s)]


def wrl_points(path):
    """All vertices of a KiCad VRML model in mm (1 VRML unit = 2.54 mm)."""
    t = Path(path).read_text(errors='ignore')
    pts = []
    for m in re.finditer(r'Transform\s*\{\s*translation\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+).*?Box\s*\{\s*size\s+'
                         r'([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)', t, re.S):
        tx, ty, tz, sx, sy, sz = map(float, m.groups())
        for dx in (-sx / 2, sx / 2):
            for dy in (-sy / 2, sy / 2):
                for dz in (-sz / 2, sz / 2):
                    pts.append(((tx + dx) * 2.54, (ty + dy) * 2.54, (tz + dz) * 2.54))
    for m in re.finditer(r'point\s*\[([^\]]*)\]', t):
        v = _nums(m.group(1))
        pts += [(v[i] * 2.54, v[i + 1] * 2.54, v[i + 2] * 2.54) for i in range(0, len(v) - 2, 3)]
    return pts


def step_points(path):
    t = Path(path).read_text(errors='ignore')
    pts = []
    for m in re.finditer(r'CARTESIAN_POINT\s*\(\s*\'[^\']*\'\s*,\s*\(([^)]*)\)', t):
        v = _nums(m.group(1))
        if len(v) == 3:
            pts.append(tuple(v))
    return pts


def _rot(p, rx, ry, rz):
    x, y, z = p
    for ang, ax in ((rx, 'x'), (ry, 'y'), (rz, 'z')):
        a = math.radians(ang)
        c, s = math.cos(a), math.sin(a)
        if ax == 'x':
            y, z = y * c - z * s, y * s + z * c
        elif ax == 'y':
            x, z = x * c + z * s, -x * s + z * c
        else:
            x, y = x * c - y * s, x * s + y * c
    return x, y, z


def model_box(f, prj):
    """(x0, y0, x1, y1, z0, z1) in board mm for footprint f, or None when it has no readable model."""
    pts = []
    for m in f.Models():
        if not m.m_Show:
            continue
        p = Path(m.m_Filename.replace('${KIPRJMOD}', str(prj)))
        if not p.exists():
            continue
        raw = wrl_points(p) if p.suffix.lower() == '.wrl' else step_points(p)
        if not raw:
            continue
        xs, ys, zs = zip(*raw)                       # STEP files carry construction points: box of all of them
        corners = [(x, y, z) for x in (min(xs), max(xs)) for y in (min(ys), max(ys)) for z in (min(zs), max(zs))]
        for c in corners:
            q = (c[0] * m.m_Scale.x, c[1] * m.m_Scale.y, c[2] * m.m_Scale.z)
            q = _rot(q, m.m_Rotation.x, m.m_Rotation.y, m.m_Rotation.z)
            q = (q[0] + m.m_Offset.x, q[1] + m.m_Offset.y, q[2] + m.m_Offset.z)
            pts.append(q)
    if not pts:
        return None
    a = math.radians(f.GetOrientationDegrees())
    ox, oy = mm(f.GetPosition().x), mm(f.GetPosition().y)
    out = []
    for x, y, z in pts:
        if f.IsFlipped():                            # bottom: KiCad mirrors the part in board y (180° about the
            z = -z - BOARD_T                         # board's x axis), so model +y is board +y; it hangs below
        else:                                        # the bottom face
            y = -y                                   # top: model +y is board -y
        bx = x * math.cos(a) + y * math.sin(a)
        by = -x * math.sin(a) + y * math.cos(a)
        out.append((ox + bx, oy + by, z))
    xs, ys, zs = zip(*out)
    return min(xs), min(ys), max(xs), max(ys), min(zs), max(zs)


def margin(box, radius, axis_x, tol):
    x0, _, x1, _, z0, z1 = box
    dx = max(abs(x0 - axis_x), abs(x1 - axis_x)) + tol
    dz = max(abs(z0), abs(z1)) + tol
    return radius - math.hypot(dx, dz)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board', nargs='?', default='m3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--radius', type=float, default=24.9)
    ap.add_argument('--axis-x', type=float, default=23.0)
    ap.add_argument('--tol', type=float, default=0.3)
    a = ap.parse_args()
    b = pcbnew.LoadBoard(a.board)
    prj = Path(a.board).resolve().parent
    rows, missing = [], []
    for f in b.GetFootprints():
        box = model_box(f, prj)
        if box is None:
            if len(f.Models()):
                missing.append(f.GetReference())
            continue
        rows.append((margin(box, a.radius, a.axis_x, a.tol), f.GetReference(), 'B' if f.IsFlipped() else 'F', box))
        if f.GetReference() in MATED:
            hw, h = MATED[f.GetReference()]
            cx = mm(f.GetPosition().x)
            mb = (cx - hw, box[1], cx + hw, box[3], 0.0, h)
            rows.append((margin(mb, a.radius, a.axis_x, a.tol), f.GetReference() + ' mated', 'F', mb))
    rows.sort()
    print(f'radius {a.radius} mm, axis x {a.axis_x} mm, sled tolerance {a.tol} mm; top face on the axis')
    for mgn, ref, side, box in rows[:15]:
        print(f'  {ref:12s} {side}  margin {mgn:6.2f} mm   x {box[0]:6.2f}..{box[2]:6.2f}  z {box[4]:6.2f}..{box[5]:6.2f}')
    bot = [r for r in rows if r[2] == 'B']
    if bot:
        print(f'  deepest bottom part: {min(bot, key=lambda r: r[3][4])[1]} '
              f'(z {min(r[3][4] for r in bot):.2f} mm), worst bottom margin {bot[0][0]:.2f} mm ({bot[0][1]})')
    if missing:
        print('  no readable model:', ' '.join(sorted(missing)))
    walls = []                                       # wire bend room: the entry face (the model box's side nearest
    for mgn, ref, side, box in rows:                 # its long edge) to the wall at WIRE_Z, sled tolerance both ways
        if ref in SIDE_ENTRY:
            face = box[0] if abs(box[0] - a.axis_x) > abs(box[2] - a.axis_x) else box[2]
            room = math.sqrt(BORE_R ** 2 - WIRE_Z ** 2) - abs(face - a.axis_x)
            walls.append(f'{ref} {room - a.tol:.1f}-{room + a.tol:.1f}')
    if walls:
        print(f'  wire entry to the bore wall at {WIRE_Z} mm height: ' + ', '.join(sorted(walls)))
    bad = [r for r in rows if r[0] < 0]
    print('fit check:', 'OK' if not bad and not missing else f'{len(bad)} part(s) outside, {len(missing)} without a model')
    return 1 if bad or missing else 0


if __name__ == '__main__':
    raise SystemExit(main())
