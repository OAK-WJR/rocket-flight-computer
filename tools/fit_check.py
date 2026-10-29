#!/usr/bin/env python3
"""CAD envelope and five-support check (REQUIREMENTS P2); physical harness fit remains unmeasured.

usage: <KiCad python3> tools/fit_check.py [board.kicad_pcb] [--radius 24.9] [--axis-x 23.0] [--tol 0.3]
       exit 0 = every margin >= 0

The board sits with its top face on the bore axis and its centreline on the axis (P2). Each footprint's 3D
model (WRL boxes and point sets, or STEP CARTESIAN_POINTs; KiCad's model offset, rotation and scale applied)
gives a bounding box in board coordinates; top-side boxes rise from z = 0, bottom-side boxes hang from
z = -1.6 (the board's bottom face). The margin of a box is the usable radius minus the distance from the axis
to its farthest corner, after moving the board by the sled tolerance (--tol, both axes, worst direction).
The default radius 24.9 mm is the Ø50.8 mm coupler bore less the 0.5 mm wall allowance; R5 checks the whole
board against it, so the result holds wherever the board sits in the bay.
M3 supports require 3.5 mm bottom standoff clearance and 3.8 mm top body/exposed-pad clearance
(a 7 mm OD washer plus 0.3 mm radial assembly margin). Masked routing is not a top hardware obstacle.

Mated envelopes use footprint-local x/y (KiCad top-view y down), with positive z away from the component
side. Rotation and bottom-side mirroring apply to every envelope. Existing J122/J123 wire allocations
are assumptions from R5, not measurements. R7's SMA jacks (J30/J31) overhang the aft edge: their bodies and
mated plugs are checked radially like every other envelope, wherever they sit along the axis. New connector allocations must be reviewed against the
maker's mating drawing and the actual harness. The check does not model insertion tools, wire stiffness,
the camera shroud, sled structure, vibration, or a fitted Tag-Connect probe.
"""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import pcbnew

mm = pcbnew.ToMM
BOARD_T = 1.6
MATED = {
    'M3_GH_BM04B_GHS_TBT': {
        'refs': ('J9',), 'box': (-4.125, -2.5, 4.125, 1.75, 0.0, 10.3),
        'basis': 'JST eGH.pdf pages 2–3: 8.25 x 4.25 mm header, 7.3 mm mated height; '
                 '3 mm additional straight-wire allocation, physical bend unverified',
        'source': 'https://www.jst-mfg.com/product/pdf/eng/eGH.pdf'},
    'M3_SMA_KH_KE8_EDGE': {
        'refs': ('J30', 'J31'), 'box': (-4.6, -25.5, 4.6, 0.0, -4.1, 5.1),
        'basis': 'R7 edge-launch SMA jack on the aft edge (local y = 0 on the edge, body toward -y): the jack body '
                 'reaches 9.5 mm beyond the edge (flange 1.5 + thread 8, Kinghelm KH-SMA-KE8-G drawing) and a straight '
                 'SMA plug about 16 mm more (5/16 in coupling nut, 9.17 mm across corners; Inference, pass1_layout '
                 '6.1/6.4), x +-4.6 about the axis, z -4.1..+5.1 about the top face. The coax loop beyond the plug '
                 'is a separate harness allocation (bay stack, parent VEHICLE.md); physical fit unverified',
        'source': 'https://www.lcsc.com/product-detail/C530661.html'},
    'HDR-TH_12P-P2.54-V-M-R3-C4-S2.54': {
        'refs': ('J122',), 'box': (-5.08, -4.0, 5.08, 4.0, 0.0, 23.5),
        'basis': 'R5 engineering allocation: four servo plugs and their wire bend; physical fit unverified'},
    # R9: the same header with its plug columns numbered from +x (m3_design/r9_lib.py, R9_DECISIONS D-S2-09): the same
    # body, so the same envelope (it is symmetric about local x = 0)
    'HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR': {
        'refs': ('J122',), 'box': (-5.08, -4.0, 5.08, 4.0, 0.0, 23.5),
        'basis': 'R5 engineering allocation: four servo plugs and their wire bend; physical fit unverified'},
    'M3_JST_PH_B2B_2P': {
        'refs': ('J123',), 'box': (-3.0, -1.75, 3.0, 2.85, 0.0, 9.5),
        'basis': 'R5 engineering allocation: JST PH plug and wire; physical fit unverified'},
}
# R10: explicit reference coverage, including both new port plugs and the split switch.
# GH geometry: JST eGH.pdf pp.2–3; 3 mm wire allocation remains an inference.
R10_MATED = {k: dict(v) for k, v in MATED.items() if k not in ('M3_SMA_KH_KE8_EDGE', 'M3_JST_PH_B2B_2P')}
R10_MATED['M3_GH_BM04B_GHS_TBT'] = dict(MATED['M3_GH_BM04B_GHS_TBT'], refs=('J9', 'J410', 'J420'))
R10_MATED['M3_GH_BM02B_GHS_TBT'] = dict(
    MATED['M3_GH_BM04B_GHS_TBT'], refs=('J400',), box=(-2.875, -2.5, 2.875, 1.75, 0.0, 10.3))  # AUD-4.
R10_MATED_REFS = {'J9', 'J122', 'J400', 'J410', 'J420'}
REQUIRED_MATED = {'M3_GH_BM04B_GHS_TBT', 'M3_SMA_KH_KE8_EDGE'}
# These are bare board features, not an escape hatch for missing fitted-part geometry.
BOARD_FEATURES = {'M3_TestPad_1.5': r'TP\d+', 'M3_ToolingHole_JLC': r'TH[123]',
                  'M3_TC2030_IDC_NL': r'J2'}
RETENTION_HOLES = ((21.5, 68.6), (27.0, 82.6))   # J122 tie (R7: +18 mm); all other Ø3.2 circles are M3 supports
# R9: check_board derives the tie holes from J122 (retention_holes, R9_DECISIONS D-S1-21); on R7 / R8 they are these
STANDOFF_RADIUS = 3.5
TOP_HARDWARE_RADIUS = 3.5 + 0.3   # 7 mm OD washer plus radial assembly margin
SIDE_ENTRY = ('J9', 'J121', 'J124')
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
        if not p.is_absolute():
            p = prj / p
        if not p.is_file():
            continue
        raw = wrl_points(p) if p.suffix.lower() == '.wrl' else step_points(p) if p.suffix.lower() in ('.step', '.stp') else []
        if not raw or not all(math.isfinite(value) for point in raw for value in point):
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
    return footprint_points_box(f, [(x, -y, z) for x, y, z in pts])


def footprint_points_box(f, points):
    """Transform local KiCad top-view geometry into the board frame, including bottom mirroring."""
    a = math.radians(f.GetOrientationDegrees())
    ox, oy = mm(f.GetPosition().x), mm(f.GetPosition().y)
    out = []
    for x, y, z in points:
        if f.IsFlipped():
            y, z = -y, -z - BOARD_T
        bx = x * math.cos(a) + y * math.sin(a)
        by = -x * math.sin(a) + y * math.cos(a)
        out.append((ox + bx, oy + by, z))
    xs, ys, zs = zip(*out)
    return min(xs), min(ys), max(xs), max(ys), min(zs), max(zs)


def footprint_box(f, box):
    x0, y0, x1, y1, z0, z1 = box
    return footprint_points_box(f, [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])


def fp_name(f):
    return str(f.GetFPID().GetLibItemName())


def board_feature(f):
    pattern = BOARD_FEATURES.get(fp_name(f))
    return bool(pattern and re.fullmatch(pattern, f.GetReference())
                and f.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM)


def point_box_distance(point, box):
    x, y = point
    return math.hypot(max(box[0] - x, 0, x - box[2]), max(box[1] - y, 0, y - box[3]))


def box_overlap(a, b):
    return all(min(a[high], b[high]) - max(a[low], b[low]) > 1e-4
               for low, high in ((0, 2), (1, 3), (4, 5)))


TIE_PAST = (1.0, 4.0)     # mm a tie hole's centre lies past J122's courtyard end, along J122's long axis (R9 M-3)
TIE_LATERAL = 6.0         # mm: a hole further off J122's long axis is not a tie-hole candidate


def retention_holes(b, holes=None, with_info=False):
    """The two J122 tie holes, derived from J122 instead of R7's coordinates (R9 gate M-3; survey_constraints.md 10):
    one Ø3.2 hole beyond each end of J122 (centre TIE_PAST mm past the courtyard end along the plug row), with the
    hole-to-hole line crossing each plug's centre line within the plug's length (its three pins +- half a pitch).
    Returns the two hole centres (RETENTION_HOLES when J122 is absent, the R7 / R8 constants); with_info also the
    problems found and the measured geometry."""
    f = next((g for g in b.GetFootprints() if g.GetReference() == 'J122'), None)
    if holes is None:
        holes = board_geometry(b)[0]
    if f is None:
        return (list(RETENTION_HOLES), ['J122 missing'], {}) if with_info else list(RETENTION_HOLES)
    th = math.radians(f.GetOrientationDegrees())
    c, s = math.cos(th), math.sin(th)
    ox, oy = mm(f.GetPosition().x), mm(f.GetPosition().y)

    def local(x, y):
        dx, dy = x - ox, y - oy
        return dx * c - dy * s, dx * s + dy * c
    cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    pts = []
    for i in range(cy.OutlineCount()):
        ch = cy.Outline(i)
        pts += [local(mm(ch.CPoint(k).x), mm(ch.CPoint(k).y)) for k in range(ch.PointCount())]
    pads = [local(mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in f.Pads()]
    if not pts or not pads:
        return (list(RETENTION_HOLES), ['J122 courtyard or pads missing'], {}) if with_info else list(RETENTION_HOLES)
    u0, u1 = min(p[0] for p in pts), max(p[0] for p in pts)
    cols = sorted({round(p[0], 3) for p in pads})
    pitch = min(b_ - a for a, b_ in zip(cols, cols[1:])) if len(cols) > 1 else 2.54
    half_plug = (max(p[1] for p in pads) - min(p[1] for p in pads)) / 2 + pitch / 2
    ends = {'-': [], '+': []}
    for h in holes:
        u, v = local(*h)
        if abs(v) > TIE_LATERAL:
            continue
        if TIE_PAST[0] - 1e-6 <= u0 - u <= TIE_PAST[1] + 1e-6:
            ends['-'].append((h, (u, v)))
        elif TIE_PAST[0] - 1e-6 <= u - u1 <= TIE_PAST[1] + 1e-6:
            ends['+'].append((h, (u, v)))
    problems = [f'J122 {k} end: expected one tie hole {TIE_PAST[0]}-{TIE_PAST[1]} mm past the courtyard, found '
                f'{len(v)}' for k, v in ends.items() if len(v) != 1]
    info = dict(columns=cols, half_plug=round(half_plug, 3), courtyard_u=[round(u0, 3), round(u1, 3)])
    if problems:
        return (list(RETENTION_HOLES), problems, info) if with_info else list(RETENTION_HOLES)
    (ha, (ua, va)), (hb, (ub, vb)) = ends['-'][0], ends['+'][0]
    cross = []
    for u in cols:
        v = va + (u - ua) * (vb - va) / (ub - ua)
        cross.append(round(v, 3))
        if abs(v) > half_plug + 1e-6:
            problems.append(f'J122 tie line crosses the plug at u {u:.2f} at v {v:.2f} (outside +-{half_plug:.2f})')
    info.update(holes=[list(ha), list(hb)], line_v_at_plugs=cross)
    return ([ha, hb], problems, info) if with_info else [ha, hb]


def support_check(holes, outline, bottom_boxes, retention=RETENTION_HOLES):
    """Inspect actual Ø3.2 cutouts, excluding only the two declared retention holes."""
    issues, supports = [], list(holes)
    for tie in retention:
        matches = [hole for hole in supports if math.dist(hole, tie) < 0.02]
        if len(matches) != 1:
            issues.append(f'retention hole {tie}: expected one Ø3.2 cutout, found {len(matches)}')
        else:
            supports.remove(matches[0])
    if len(supports) != 5:
        issues.append(f'expected five M3 supports, found {len(supports)}')
    x0, y0, x1, y1 = outline
    corners = []
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        near = [hole for hole in supports if abs(hole[0] - x) <= 6 and abs(hole[1] - y) <= 6]
        if len(near) != 1:
            issues.append(f'corner ({x:g}, {y:g}) needs one M3 support within 6 mm on both axes')
        corners.extend(near)
    middle = [hole for hole in supports if hole not in corners]
    if len(middle) != 1 or not y0 + (y1 - y0) / 3 <= middle[0][1] <= y0 + 2 * (y1 - y0) / 3:
        issues.append('one M3 support must lie in the middle third of board length')
    nearest = None
    for hole in supports:
        for ref, box in bottom_boxes:
            distance = point_box_distance(hole, box)
            if nearest is None or distance < nearest[0]:
                nearest = (distance, ref, hole)
            if distance < STANDOFF_RADIUS - 1e-4:
                issues.append(f'{ref} bottom/pin envelope {distance:.3f} mm from support {hole}; need >=3.5 mm')
    return supports, nearest, issues


def mounting_pad(pad, hole):
    """Only an explicit M3 mounting land concentric with a support is exempt."""
    footprint = pad.GetParentFootprint()
    drill = pad.GetDrillSize()
    return (bool(re.fullmatch(r'MountingHole_3\.2mm_M3(?:_Pad(?:_TopOnly|_Via)?)?', fp_name(footprint)))
            and pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            and abs(mm(drill.x) - 3.2) < .01 and abs(mm(drill.y) - 3.2) < .01
            and math.dist(hole, (mm(pad.GetPosition().x), mm(pad.GetPosition().y))) < .02)


def copper_distance(pad, point):
    """Native collision distance; SHAPE.Distance omits rounded-pad stroke width."""
    shape = pad.GetEffectiveShape(pcbnew.F_Cu)
    if shape.Collide(point, 0):
        return 0.0
    box = shape.BBox()
    dx = max(abs(point.x - box.GetX()), abs(point.x - box.GetRight()))
    dy = max(abs(point.y - box.GetY()), abs(point.y - box.GetBottom()))
    low, high = 0, math.ceil(math.hypot(dx, dy)) + 1
    while high - low > 1:
        middle = (low + high) // 2
        if shape.Collide(point, middle):
            high = middle
        else:
            low = middle
    return mm(high)


def top_support_check(supports, bodies, pads):
    """Top washers must clear bodies and exposed pads; masked routing is excluded."""
    issues, nearest = [], None
    for hole in supports:
        point = pcbnew.VECTOR2I(pcbnew.FromMM(hole[0]), pcbnew.FromMM(hole[1]))
        measured = [(ref + ' top body', point_box_distance(hole, box)) for ref, box in bodies]
        measured.extend((ref + ' exposed top pad', copper_distance(pad, point))
                        for ref, pad in pads if not mounting_pad(pad, hole))
        for ref, distance in measured:
            if nearest is None or distance < nearest[0]:
                nearest = (distance, ref, hole)
            if distance < TOP_HARDWARE_RADIUS - 1e-4:
                issues.append(f'{ref} {distance:.3f} mm from support {hole}; need >=3.8 mm '
                              '(7 mm OD washer + 0.3 mm radial margin)')
    return nearest, issues


def board_geometry(b):
    holes, points = [], []
    for drawing in b.GetDrawings():
        if drawing.GetLayer() != pcbnew.Edge_Cuts:
            continue
        if drawing.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            if abs(mm(drawing.GetRadius()) - 1.6) < 0.01:
                center = drawing.GetCenter()
                holes.append((mm(center.x), mm(center.y)))
        else:
            points.extend((mm(p.x), mm(p.y)) for p in (drawing.GetStart(), drawing.GetEnd()))
    if not points:
        raise ValueError('no board outline')
    xs, ys = zip(*points)
    return holes, (min(xs), min(ys), max(xs), max(ys))


def input_hashes(board):
    paths = [board]
    for suffix in ('*.wrl', '*.step', '*.stp'):
        paths.extend((board.parent / 'kilib').rglob(suffix))
    return {str(path.relative_to(board.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def pad_box(p):
    bounds = p.GetBoundingBox()
    return mm(bounds.GetX()), mm(bounds.GetY()), mm(bounds.GetRight()), mm(bounds.GetBottom()), -BOARD_T, 0.0


def check_board(b, prj, radius=24.9, axis_x=23.0, tol=0.3, profile='r9'):
    if profile not in ('r9', 'r10'):
        raise ValueError(f'unknown fit profile {profile!r}')
    mated = R10_MATED if profile == 'r10' else MATED
    required_refs = R10_MATED_REFS if profile == 'r10' else {'J9', 'J122', 'J123', 'J30', 'J31'}
    rows, bodies, mating, bottom, issues, excluded = [], [], [], [], [], []
    top_bodies, top_pads = [], []
    if not all(math.isfinite(value) for value in (radius, axis_x, tol)) or radius <= 0 or tol < 0:
        raise ValueError('finite positive bore radius, finite axis and nonnegative sled tolerance required')
    if abs(mm(b.GetDesignSettings().GetBoardThickness()) - BOARD_T) > 0.01:
        issues.append('board thickness differs from the 1.6 mm envelope transform')
    for f in b.GetFootprints():
        ref, side = f.GetReference(), 'B' if f.IsFlipped() else 'F'
        # Bare test/debug lands and DNP footprints still leave exposed copper.
        top_pads.extend((ref + '.' + p.GetNumber(), p) for p in f.Pads()
                        if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH
                        and p.IsOnLayer(pcbnew.F_Cu) and p.IsOnLayer(pcbnew.F_Mask)
                        and not p.IsTented(pcbnew.F_Cu))
        if board_feature(f) or f.GetAttributes() & pcbnew.FP_DNP:
            excluded.append(ref)
            # their exposed bottom lands still meet the standoff hardware (P3-MECHANICAL-04); NPTH tooling holes have none
            bottom.extend((ref + '.' + p.GetNumber() + ' exposed bottom pad', pad_box(p)) for p in f.Pads()
                          if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH
                          and p.IsOnLayer(pcbnew.B_Cu) and p.IsOnLayer(pcbnew.B_Mask)
                          and not p.IsTented(pcbnew.B_Cu))
            continue
        box = model_box(f, prj)
        if box is None:
            issues.append(f'{ref}: no readable model (only explicit bare board features/DNP are excluded)')
            continue
        rows.append((margin(box, radius, axis_x, tol), ref, side, box))
        bodies.append((ref, box))
        if f.IsFlipped():
            bottom.append((ref, box))
            bottom.extend((ref + '.' + p.GetNumber(), pad_box(p)) for p in f.Pads() if p.IsOnLayer(pcbnew.B_Cu))
        else:
            top_bodies.append((ref, box))
            bottom.extend((ref + '.' + p.GetNumber() + ' pin', pad_box(p)) for p in f.Pads()
                          if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)
        spec = mated.get(fp_name(f))
        if spec:
            if ref not in spec['refs']:
                issues.append(f'{ref}: mated envelope is not reviewed for this reference')
                continue
            mb = footprint_box(f, spec['box'])
            rows.append((margin(mb, radius, axis_x, tol), ref + ' mated', side, mb))
            mating.append((ref, mb))
        elif fp_name(f) in REQUIRED_MATED or (ref in required_refs
                                             and not fp_name(f).startswith('M3_DB128')):
            issues.append(f'{ref}: mated housing/wire envelope has not been reviewed')
    if profile == 'r10':
        missing = required_refs - {ref for ref, box in mating}
        issues.extend(f'{ref}: required R10 mated envelope missing' for ref in sorted(missing))
        _, tie_issues, _ = retention_holes(b, with_info=True)
        issues.extend(tie_issues)
    for index, (ref, box) in enumerate(mating):
        for other, body in bodies:
            if other != ref and box_overlap(box, body):
                issues.append(f'{ref} mated envelope intersects {other} model box')
        for other, other_box in mating[index + 1:]:
            if box_overlap(box, other_box):
                issues.append(f'{ref} and {other} mated envelopes intersect')
    holes, outline = board_geometry(b)
    width, length = outline[2] - outline[0], outline[3] - outline[1]
    if abs(width - 46.0) > 0.01:
        issues.append(f'board width {width:g} mm; P1 requires 46 mm')
    if length > 120.01:
        issues.append(f'board length {length:g} mm exceeds the P1 120 mm maximum (outline only; the SMA overhang '
                      'and mated plugs count in the bay stack)')
    supports, nearest, support_issues = support_check(holes, outline, bottom, retention_holes(b, holes))
    issues.extend(support_issues)
    nearest_top, top_issues = top_support_check(supports, top_bodies, top_pads)
    issues.extend(top_issues)
    issues.extend(f'{ref}: outside bore by {-mgn:.3f} mm' for mgn, ref, _, _ in rows if mgn < 0)
    return dict(profile=profile, rows=sorted(rows), issues=issues, supports=supports, nearest_support=nearest,
                nearest_top_support=nearest_top, top_hardware_radius_mm=TOP_HARDWARE_RADIUS,
                outline=outline, width_mm=width, length_mm=length, excluded=sorted(excluded), ok=not issues)


def margin(box, radius, axis_x, tol):
    x0, _, x1, _, z0, z1 = box
    dx = max(abs(x0 - axis_x), abs(x1 - axis_x)) + tol
    dz = max(abs(z0), abs(z1)) + tol
    return radius - math.hypot(dx, dz)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board', nargs='?', default='m3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--profile', choices=('r9', 'r10'), default='r9')
    ap.add_argument('--radius', type=float, default=24.9)
    ap.add_argument('--axis-x', type=float, default=23.0)
    ap.add_argument('--tol', type=float, default=0.3)
    ap.add_argument('--report', type=Path, help='write CAD fit evidence, bound to this board and checker')
    a = ap.parse_args()
    board_path = Path(a.board).resolve()
    before = input_hashes(board_path)
    b = pcbnew.LoadBoard(a.board)
    prj = Path(a.board).resolve().parent
    report = check_board(b, prj, a.radius, a.axis_x, a.tol, a.profile)
    if before != input_hashes(board_path):
        report['issues'].append('board or model inputs changed during fit check')
        report['ok'] = False
    rows = report['rows']
    print(f'radius {a.radius} mm, axis x {a.axis_x} mm, sled tolerance {a.tol} mm; top face on the axis')
    for mgn, ref, side, box in rows[:15]:
        print(f'  {ref:12s} {side}  margin {mgn:6.2f} mm   x {box[0]:6.2f}..{box[2]:6.2f}  z {box[4]:6.2f}..{box[5]:6.2f}')
    bot = [r for r in rows if r[2] == 'B']
    if bot:
        print(f'  deepest bottom part: {min(bot, key=lambda r: r[3][4])[1]} '
              f'(z {min(r[3][4] for r in bot):.2f} mm), worst bottom margin {bot[0][0]:.2f} mm ({bot[0][1]})')
    print('  five-support geometry:', report['supports'])
    print(f"  board: {report['width_mm']:g} x {report['length_mm']:g} mm; 120 mm maximum (P1)")
    if report['nearest_support']:
        distance, ref, hole = report['nearest_support']
        print(f'  nearest bottom/pin envelope: {ref}, {distance:.3f} mm from support {hole} (minimum 3.5 mm)')
    if report['nearest_top_support']:
        distance, ref, hole = report['nearest_top_support']
        print(f'  nearest top hardware clearance: {ref}, {distance:.3f} mm from support {hole} (minimum 3.8 mm)')
    walls = []                                       # wire bend room: the entry face (the model box's side nearest
    # its long edge) to the wall at WIRE_Z, sled tolerance both ways; profile r10 (R3-MEC-02): also J1 and R10's DB125
    # terminals (the same west face)
    side_entry, lands = (SIDE_ENTRY + ('J1',), ('M3_DB128', 'M3_DB125')) if a.profile == 'r10' else \
        (SIDE_ENTRY, ('M3_DB128',))
    for mgn, ref, side, box in rows:
        if ref in side_entry and fp_name(b.FindFootprintByReference(ref)).startswith(lands):
            face = box[0] if abs(box[0] - a.axis_x) > abs(box[2] - a.axis_x) else box[2]
            room = math.sqrt(BORE_R ** 2 - WIRE_Z ** 2) - abs(face - a.axis_x)
            walls.append(f'{ref} {room - a.tol:.2f}-{room + a.tol:.2f}')
    if walls:
        print(f'  wire entry to the bore wall at {WIRE_Z} mm height: ' + ', '.join(sorted(walls)))
    for issue in report['issues']:
        print('  FAIL', issue)
    print('fit check:', 'OK (CAD envelopes only)' if report['ok'] else f"FAIL ({len(report['issues'])} findings)")
    if a.report:
        report.update(board_sha256=before[board_path.name], inputs_sha256=before,
                      checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      radius_mm=a.radius, axis_x_mm=a.axis_x, tolerance_mm=a.tol,
                      mated_envelopes=R10_MATED if a.profile == 'r10' else MATED, physical_fit_verified=False)
        a.report.write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
