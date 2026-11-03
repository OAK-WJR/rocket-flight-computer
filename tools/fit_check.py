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

Profile r11 (M3-ASSY-R11, D-R11-02 / -05 / -08): 46 mm wide x <= 56 mm (the outline read from the board), the same bore,
axis and sled tolerance (P2). Each side-entry JST GH header (Manufacturer Part SMnnB-GHS-TB, any footprint name) gets a
mated plug-and-wire envelope built from JST's drawing (GH_DRAWING) along its mouth, the direction from its contact pad
row to its two fixing-tab pads, so it does not depend on the footprint's local axes; the mouth must face the board edge
the header sits on (GH_EDGE_REACH) and the envelope is checked radially and against every other body. The battery and
pyro wire pads (WIRE_PAD_REFS) carry no model: each plated wire pad gets a solder-and-bend allocation (WIRE_ALLOWANCE),
an Inference until the harness is built. Supports: one M3 support within 6 mm of each corner (a fifth is optional on
the <= 56 mm board) with the same 3.5 / 3.8 mm hardware clearances.
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
# R10 screw-terminal amendment: every wired connection uses DB125 clamps; there are no port or servo plugs.
# Terminal bodies are read from their models. Wire/ferrule bend and screwdriver access require physical qualification.
R10_MATED = {'M3_MICROSD_MOLEX_472192001': dict(
    refs=('J430',), box=(-7.525, -9.7, 7.525, 6., 0., 2.1),
    basis='Molex SD-47219-001G sheet1: width(13.60+0.15)+2x(0.50+0.15)=15.05mm including fitting nails; '
          'independent y-datum stack -9.70..5.35mm and closed height<=2.05mm. '
          'Inference: common centred datum, zero seating offset and retained card-front+6.00mm/height2.10mm; '
          'card seating, hinge locking and retention under 100 g/vibration require physical qualification. '
          'Open/insertion envelope is bench-only with the board out of the bay and unpowered',
    source='https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf')}
# R12-GATE-01: normalized maximum envelopes, in footprint-local KiCad x/y and
# component-side z (mm), before placement/flip. D-R11-01 / T0-1 p1 for DB125;
# the SD entry is the existing conservative closed socket/card union above.
# C84: MA supplier sheet p2; retain the reviewed conservative 8.5 x 8.5 x 10.8 mm
# allocation (base 8.3 +/- 0.2, height 10 +/- 0.5, plus inferred 0.3 mm projection).
# Compare physical coordinates, not scale literals: equivalent unit conversions remain legal.
R10_MODEL_BOXES = {
    'M3_DB125_2P_BK': (-4.62, -4.10, 3.70, 4.00, 0., 8.90),
    'M3_DB125_2P_GN': (-4.62, -4.10, 3.70, 4.00, 0., 8.90),
    'M3_DB125_4P_GN': (-8.32, -4.10, 7.20, 4.00, 0., 8.90),
    'M3_DB125_5P_GN': (-10.07, -4.10, 8.95, 4.00, 0., 8.90),
    'M3_MICROSD_MOLEX_472192001': R10_MATED['M3_MICROSD_MOLEX_472192001']['box'],
    'M3_MA_8x10': (-4.25, -4.25, 4.25, 4.25, 0., 10.80),
}
R10_MODEL_TOL = 2e-5  # mm; six-decimal VRML endpoint error <=1.905e-6 mm, with a numeric guard
R10_TERMINAL_TAIL_MM = 3.8  # DORABO T0-1 sheet1:3.50+/-0.30mm below seating plane
R10_MATED_REFS = {'J430'}
REQUIRED_MATED = {'M3_GH_BM04B_GHS_TBT', 'M3_SMA_KH_KE8_EDGE'}
# These are bare board features, not an escape hatch for missing fitted-part geometry.
BOARD_FEATURES = {'M3_TestPad_1.5': r'TP\d+', 'M3_ToolingHole_JLC': r'TH[123]',
                  'M3_TC2030_IDC_NL': r'J2'}
RETENTION_HOLES = ((21.5, 68.6), (27.0, 82.6))   # J122 tie (R7: +18 mm); all other Ø3.2 circles are M3 supports
# R9: check_board derives the tie holes from J122 (retention_holes, R9_DECISIONS D-S1-21); on R7 / R8 they are these
STANDOFF_RADIUS = 3.5
TOP_HARDWARE_RADIUS = 3.5 + 0.3   # 7 mm OD washer plus radial assembly margin
SIDE_ENTRY = ('J9', 'J121', 'J124')
# ---- profile r11 (D-R11-05) ------------------------------------------------------------------------------------------
# JST GH (1.25 mm) catalogue eGH.pdf, page 3 (https://www.jst-mfg.com/product/pdf/eng/eGH.pdf, read 2026-11-02 with
# pdftotext): side-entry header SMnnB-GHS-TB width B = 1.25 (n - 1) + 4.5 mm (SM04B 8.25, SM06B 10.75), depth 4.25 mm
# and height 4.25 mm (the drawing gives 4.05 / 4.25: the larger is taken); housing GHR-nnV-S width B = 1.25 (n + 1) mm
# (GHR-04V-S 6.25), length 5.7 mm, height 4.15 mm. The header's contact pads sit at its rear: KiCad's
# JST_GH_SM04B-GHS-TB footprint (the same drawing) has the pad row 0.25 mm behind the body's rear wall and the mouth
# 4.30 mm in front of the pad row (Datasheet, via KiCad's library). The plug is counted in front of the header for its
# whole 5.7 mm length (no insertion overlap credited: conservative) and GH_WIRE_STRAIGHT mm of straight wire beyond it,
# R7's GH allocation (the bend itself is a harness item, unverified).
GH_DRAWING = dict(source='https://www.jst-mfg.com/product/pdf/eng/eGH.pdf', page=3,
                  header_extra_width=4.5, header_depth=4.25, header_height=4.25,
                  housing_extra_width=1.25, housing_length=5.7, housing_height=4.15,
                  pad_behind_rear=0.25, mouth_ahead_of_pads=4.30)
GH_WIRE_STRAIGHT = 3.0          # mm of straight wire beyond the plug (R7 basis, Inference)
GH_PART = re.compile(r'^SM(\d\d)B-GHS-TB')
GH_EDGE_REACH = 3.0             # mm: the header's mouth lies within this of the outline edge it faces
R11_GH_REFS = {'J9', 'J122', 'J400', 'J410', 'J420', 'J440'}
R11_MATED_REFS = {'J430'} | R11_GH_REFS
WIRE_PAD_REFS = {'J1', 'J121'}
# A wire soldered into a plated pad from the component side: a fillet (1.0 mm), a bend of inner radius 1 x OD and the
# OD itself above the face, the pad grown by one OD round it, and a 1.5 mm solder / lead tail below the board
# (P2's <= 1.8 mm insulation OD and 1 x OD bend; Inference until the harness is built)
WIRE_OD = 1.8
WIRE_ALLOWANCE = dict(above=1.0 + 2 * WIRE_OD, grow=WIRE_OD, tail=1.5)
R11_MAX_LENGTH = 56.0           # mm, D-R11-02 ceiling
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
    """Board-mm envelope, or None without a readable model; invalid visible geometry raises ValueError."""
    pts = []
    for m in f.Models():
        if not m.m_Show:
            continue
        scale = (m.m_Scale.x, m.m_Scale.y, m.m_Scale.z)
        transform = scale + (m.m_Offset.x, m.m_Offset.y, m.m_Offset.z,
                             m.m_Rotation.x, m.m_Rotation.y, m.m_Rotation.z)
        if not all(math.isfinite(v) for v in transform) or any(v <= 0 for v in scale):
            raise ValueError(f'{f.GetReference()}: invalid model transform; finite values and positive scales required')
        p = Path(m.m_Filename.replace('${KIPRJMOD}', str(prj)))
        if not p.is_absolute():
            p = prj / p
        if not p.is_file():
            continue
        raw = wrl_points(p) if p.suffix.lower() == '.wrl' else step_points(p) if p.suffix.lower() in ('.step', '.stp') else []
        if not raw:
            continue
        if not all(math.isfinite(value) for point in raw for value in point):
            raise ValueError(f'{f.GetReference()}: nonfinite model vertices')
        xs, ys, zs = zip(*raw)                       # STEP files carry construction points: box of all of them
        if any(min(axis) >= max(axis) for axis in (xs, ys, zs)):
            raise ValueError(f'{f.GetReference()}: degenerate model envelope')
        corners = [(x, y, z) for x in (min(xs), max(xs)) for y in (min(ys), max(ys)) for z in (min(zs), max(zs))]
        for c in corners:
            q = (c[0] * m.m_Scale.x, c[1] * m.m_Scale.y, c[2] * m.m_Scale.z)
            q = _rot(q, m.m_Rotation.x, m.m_Rotation.y, m.m_Rotation.z)
            q = (q[0] + m.m_Offset.x, q[1] + m.m_Offset.y, q[2] + m.m_Offset.z)
            if not all(math.isfinite(v) for v in q):
                raise ValueError(f'{f.GetReference()}: nonfinite transformed model envelope')
            pts.append(q)
    if not pts:
        return None
    local = [(x, -y, z) for x, y, z in pts]
    expected = R10_MODEL_BOXES.get(fp_name(f))
    if expected is not None:
        xs, ys, zs = zip(*local)
        actual = (min(xs), min(ys), max(xs), max(ys), min(zs), max(zs))
        if any(abs(a - e) > R10_MODEL_TOL for a, e in zip(actual, expected)):
            raise ValueError(f'{f.GetReference()}: model envelope differs from reviewed dimensions/pose '
                             f'of {fp_name(f)}: {actual}, expected {expected} mm')
    box = footprint_points_box(f, local)
    if not all(math.isfinite(v) for v in box) or any(box[lo] >= box[hi] for lo, hi in ((0, 2), (1, 3), (4, 5))):
        raise ValueError(f'{f.GetReference()}: nonfinite or degenerate transformed model envelope')
    return box


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


def retention_holes(b, holes=None, with_info=False, profile='r9'):
    """The two J122 tie holes, derived from J122 instead of R7's coordinates (R9 gate M-3; survey_constraints.md 10):
    one Ø3.2 hole beyond each end of J122 (centre TIE_PAST mm past the courtyard end along the plug row), with the
    hole-to-hole line crossing each plug's centre line within the plug's length (its three pins +- half a pitch).
    Returns the two hole centres (RETENTION_HOLES when J122 is absent, the R7 / R8 constants); with_info also the
    problems found and the measured geometry."""
    if profile == 'r10':
        return ([], [], {'required': False, 'basis': 'J122 is a five-contact screw terminal'}) if with_info else []
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


def terminal_tail_box(f, p):
    # Inference: use the whole native copper-pad AABB transversely, larger
    # than the metal pin; solder/seating/bent-lead tolerances need inspection.
    z = (0., R10_TERMINAL_TAIL_MM-BOARD_T) if f.IsFlipped() else (-R10_TERMINAL_TAIL_MM, -BOARD_T)
    return (*pad_box(p)[:4], *z)


def gh_circuits(f):
    """The circuit count of a side-entry JST GH header (Manufacturer Part SMnnB-GHS-TB), else None."""
    part = f.GetFieldText('Manufacturer Part') if f.HasField('Manufacturer Part') else ''
    m = GH_PART.match(part or '')
    return int(m.group(1)) if m else None


def gh_envelope(f, n, outline):
    """(header box, mated box, mouth unit vector, problems) of a side-entry GH header, in board mm. The mouth points
    from the contact pad row (the numbered pads) to the two fixing tabs (the unnumbered / MP pads)."""
    g = GH_DRAWING
    sig = [p for p in f.Pads() if p.GetNumber().isdigit()]
    tabs = [p for p in f.Pads() if not p.GetNumber().isdigit()]
    if len(sig) != n or len(tabs) != 2:
        return None, None, None, [f'{f.GetReference()}: GH header needs {n} contact pads and 2 fixing tabs, has '
                                  f'{len(sig)} / {len(tabs)}']
    cx = sum(mm(p.GetPosition().x) for p in sig) / n
    cy = sum(mm(p.GetPosition().y) for p in sig) / n
    tx = sum(mm(p.GetPosition().x) for p in tabs) / 2
    ty = sum(mm(p.GetPosition().y) for p in tabs) / 2
    L = math.hypot(tx - cx, ty - cy)
    if L < 1e-6:
        return None, None, None, [f'{f.GetReference()}: GH header mouth undefined (tabs on the pad row)']
    ux, uy = (tx - cx) / L, (ty - cy) / L
    if abs(ux) > 1e-6 and abs(uy) > 1e-6:
        return None, None, None, [f'{f.GetReference()}: GH header mouth not along a board axis']
    vx, vy = -uy, ux
    half = max((n - 1) * 1.25 + g['header_extra_width'], (n + 1) * g['housing_extra_width']) / 2
    rear = -g['pad_behind_rear']
    mouth = g['mouth_ahead_of_pads']
    tip = mouth + g['housing_length'] + GH_WIRE_STRAIGHT
    z0, z1 = (-BOARD_T - g['header_height'], -BOARD_T) if f.IsFlipped() else (0.0, g['header_height'])

    def box(a, b_):
        pts = [(cx + ux * t + vx * w, cy + uy * t + vy * w) for t in (a, b_) for w in (-half, half)]
        xs, ys = zip(*pts)
        return (min(xs), min(ys), max(xs), max(ys), z0, z1)
    problems = []
    x0, y0, x1, y1 = outline
    mx, my = cx + ux * mouth, cy + uy * mouth
    edge = {(1, 0): x1 - mx, (-1, 0): mx - x0, (0, 1): y1 - my, (0, -1): my - y0}[(round(ux), round(uy))]
    if edge > GH_EDGE_REACH + 1e-6 or edge < -GH_EDGE_REACH - 1e-6:
        problems.append(f'{f.GetReference()}: GH mouth {edge:.2f} mm from the edge it faces (must face its own edge '
                        f'within {GH_EDGE_REACH} mm)')
    return box(rear, mouth), box(mouth, tip), (ux, uy), problems


def wire_pad_boxes(f):
    """[(label, box above, box below)] of each plated wire pad of a battery / pyro wire-pad footprint."""
    out, w = [], WIRE_ALLOWANCE
    for p in f.Pads():
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
            continue
        x0, y0, x1, y1 = pad_box(p)[:4]
        g = w['grow']
        top = (0.0, w['above']) if not f.IsFlipped() else (-BOARD_T - w['above'], -BOARD_T)
        bot = (-BOARD_T - w['tail'], -BOARD_T) if not f.IsFlipped() else (0.0, w['tail'])
        out.append((f'{f.GetReference()}.{p.GetNumber()} wire', (x0 - g, y0 - g, x1 + g, y1 + g, *top),
                    (x0, y0, x1, y1, *bot)))
    return out


def check_board(b, prj, radius=24.9, axis_x=23.0, tol=0.3, profile='r9'):
    if profile not in ('r9', 'r10', 'r11'):
        raise ValueError(f'unknown fit profile {profile!r}')
    if profile == 'r11':
        return check_board_r11(b, prj, radius, axis_x, tol)
    mated = R10_MATED if profile == 'r10' else MATED
    required_refs = R10_MATED_REFS if profile == 'r10' else {'J9', 'J122', 'J123', 'J30', 'J31'}
    rows, bodies, mating, bottom, issues, excluded = [], [], [], [], [], []
    tails = []
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
        try:
            box = model_box(f, prj)
        except ValueError as error:
            issues.append(str(error))
            continue
        if box is None:
            issues.append(f'{ref}: no readable model (only explicit bare board features/DNP are excluded)')
            continue
        rows.append((margin(box, radius, axis_x, tol), ref, side, box))
        bodies.append((ref, box))
        if profile == 'r10' and fp_name(f).startswith('M3_DB125_'):
            for p in f.Pads():
                if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
                    continue
                tail = terminal_tail_box(f, p)
                label = ref + '.' + p.GetNumber() + ' terminal tail'
                tails.append((ref, label, tail))
                rows.append((margin(tail, radius, axis_x, tol), label, 'F' if f.IsFlipped() else 'B', tail))
                (top_bodies if f.IsFlipped() else bottom).append((label, tail))
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
            # The locked microSD card is a rigid flight body; its allocation must also clear support hardware.
            if profile == 'r10' and ref == 'J430':
                (bottom if f.IsFlipped() else top_bodies).append((ref + ' mated', mb))
        elif fp_name(f) in REQUIRED_MATED or (ref in required_refs
                                             and not fp_name(f).startswith('M3_DB128')):
            issues.append(f'{ref}: mated housing/wire envelope has not been reviewed')
    if profile == 'r10':
        missing = required_refs - {ref for ref, box in mating}
        issues.extend(f'{ref}: required R10 mated envelope missing' for ref in sorted(missing))
        _, tie_issues, _ = retention_holes(b, with_info=True, profile=profile)
        issues.extend(tie_issues)
    for ref, label, tail in tails:
        for other, body in bodies:
            if other != ref and box_overlap(tail, body):
                issues.append(f'{label} intersects {other} model box')
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
    supports, nearest, support_issues = support_check(holes, outline, bottom, retention_holes(b, holes, profile=profile))
    issues.extend(support_issues)
    nearest_top, top_issues = top_support_check(supports, top_bodies, top_pads)
    issues.extend(top_issues)
    issues.extend(f'{ref}: outside bore by {-mgn:.3f} mm' for mgn, ref, _, _ in rows if mgn < 0)
    return dict(profile=profile, rows=sorted(rows), issues=issues, supports=supports, nearest_support=nearest,
                nearest_top_support=nearest_top, top_hardware_radius_mm=TOP_HARDWARE_RADIUS,
                wire_room_mm=wire_rooms(b, rows, profile, axis_x, tol),
                outline=outline, width_mm=width, length_mm=length, excluded=sorted(excluded),
                terminal_tails=dict(count=len(tails), max_below_seating_mm=R10_TERMINAL_TAIL_MM,
                                    transverse_allocation='Inference: native copper-pad AABB, not a pin/solder model',
                                    minimum_bore_margin_mm=min((margin(box, radius, axis_x, tol) for _, _, box in tails), default=None),
                                    max_projection_below_board_mm=R10_TERMINAL_TAIL_MM-BOARD_T,
                                    nominal_4mm_standoff_plate_clearance_mm=4-(R10_TERMINAL_TAIL_MM-BOARD_T),
                                    source='https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf'),
                ok=not issues)


def corner_supports(holes, outline, bottom_boxes):
    """R11: one M3 support within 6 mm of each corner, at most one more anywhere; the 3.5 mm bottom clearance."""
    issues, x0, y0, x1, y1 = [], *outline
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        near = [h for h in holes if abs(h[0] - x) <= 6 and abs(h[1] - y) <= 6]
        if len(near) != 1:
            issues.append(f'corner ({x:g}, {y:g}) needs one M3 support within 6 mm on both axes, found {len(near)}')
    if not 4 <= len(holes) <= 5:
        issues.append(f'expected four or five M3 supports, found {len(holes)}')
    nearest = None
    for hole in holes:
        for ref, box in bottom_boxes:
            d = point_box_distance(hole, box)
            if nearest is None or d < nearest[0]:
                nearest = (d, ref, hole)
            if d < STANDOFF_RADIUS - 1e-4:
                issues.append(f'{ref} bottom/pin envelope {d:.3f} mm from support {hole}; need >=3.5 mm')
    return list(holes), nearest, issues


def check_board_r11(b, prj, radius, axis_x, tol):
    """Profile r11: see the module docstring."""
    rows, bodies, mating, bottom, issues, excluded, top_bodies, top_pads = [], [], [], [], [], [], [], []
    gh, wires = {}, []
    if not all(math.isfinite(v) for v in (radius, axis_x, tol)) or radius <= 0 or tol < 0:
        raise ValueError('finite positive bore radius, finite axis and nonnegative sled tolerance required')
    if abs(mm(b.GetDesignSettings().GetBoardThickness()) - BOARD_T) > 0.01:
        issues.append('board thickness differs from the 1.6 mm envelope transform')
    if b.GetCopperLayerCount() != 6:
        issues.append(f'R11 is a six-layer board (D-R11-03); this one has {b.GetCopperLayerCount()} copper layers')
    holes, outline = board_geometry(b)
    for f in b.GetFootprints():
        ref, side = f.GetReference(), 'B' if f.IsFlipped() else 'F'
        top_pads.extend((ref + '.' + p.GetNumber(), p) for p in f.Pads()
                        if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH
                        and p.IsOnLayer(pcbnew.F_Cu) and p.IsOnLayer(pcbnew.F_Mask) and not p.IsTented(pcbnew.F_Cu))
        if ref in WIRE_PAD_REFS:
            boxes = wire_pad_boxes(f)
            if not boxes:
                issues.append(f'{ref}: wire-pad footprint has no plated wire pad')
            for label, above, below in boxes:
                for box, face in ((above, 'F' if not f.IsFlipped() else 'B'), (below, 'B' if not f.IsFlipped() else 'F')):
                    rows.append((margin(box, radius, axis_x, tol), label, face, box))
                    bodies.append((label, box))
                    (bottom if box[4] < -BOARD_T + 1e-9 else top_bodies).append((label, box))
                wires.append(label)
            continue
        if board_feature(f) or f.GetAttributes() & pcbnew.FP_DNP:
            excluded.append(ref)
            bottom.extend((ref + '.' + p.GetNumber() + ' exposed bottom pad', pad_box(p)) for p in f.Pads()
                          if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH
                          and p.IsOnLayer(pcbnew.B_Cu) and p.IsOnLayer(pcbnew.B_Mask) and not p.IsTented(pcbnew.B_Cu))
            continue
        try:
            box = model_box(f, prj)
        except ValueError as error:
            issues.append(str(error))
            continue
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
        n = gh_circuits(f)
        if n is not None:
            if ref not in R11_GH_REFS:
                issues.append(f'{ref}: GH mated envelope is not reviewed for this reference')
                continue
            header, mb, mouth, probs = gh_envelope(f, n, outline)
            issues.extend(probs)
            if mb is None:
                continue
            rows.append((margin(mb, radius, axis_x, tol), ref + ' mated', side, mb))
            mating.append((ref, mb))
            gh[ref] = dict(circuits=n, mouth=[round(mouth[0]), round(mouth[1])], header=[round(v, 3) for v in header],
                           mated=[round(v, 3) for v in mb],
                           beyond_outline_mm=round(max(outline[0] - mb[0], mb[2] - outline[2], outline[1] - mb[1],
                                                       mb[3] - outline[3], 0.0), 3))
            continue
        spec = R10_MATED.get(fp_name(f))
        if spec:
            if ref not in spec['refs']:
                issues.append(f'{ref}: mated envelope is not reviewed for this reference')
                continue
            mb = footprint_box(f, spec['box'])
            rows.append((margin(mb, radius, axis_x, tol), ref + ' mated', side, mb))
            mating.append((ref, mb))
            (bottom if f.IsFlipped() else top_bodies).append((ref + ' mated', mb))
        elif ref in R11_MATED_REFS:
            issues.append(f'{ref}: mated housing/wire envelope has not been reviewed (a GH port needs Manufacturer Part '
                          f'SMnnB-GHS-TB)')
    missing = R11_MATED_REFS - {ref for ref, _ in mating}
    issues.extend(f'{ref}: required R11 mated envelope missing' for ref in sorted(missing))
    missing_wires = WIRE_PAD_REFS - {w.split('.')[0] for w in wires}
    issues.extend(f'{ref}: required R11 wire-pad footprint missing' for ref in sorted(missing_wires))
    for index, (ref, box) in enumerate(mating):
        for other, body in bodies:
            if other != ref and box_overlap(box, body):
                issues.append(f'{ref} mated envelope intersects {other} model box')
        for other, other_box in mating[index + 1:]:
            if box_overlap(box, other_box):
                issues.append(f'{ref} and {other} mated envelopes intersect')
    for label in wires:
        ref = label.split('.')[0]
        mine = [bx for lb, bx in bodies if lb == label]
        for other, body in bodies + mating:
            if other.split('.')[0].split(' ')[0] == ref:
                continue
            if any(box_overlap(m, body) for m in mine):
                issues.append(f'{label} allocation intersects {other}')
    width, length = outline[2] - outline[0], outline[3] - outline[1]
    if abs(width - 46.0) > 0.01:
        issues.append(f'board width {width:g} mm; P1 / D-R11-02 require 46 mm')
    if length > R11_MAX_LENGTH + 0.01:
        issues.append(f'board length {length:g} mm exceeds the D-R11-02 {R11_MAX_LENGTH:g} mm ceiling')
    supports, nearest, support_issues = corner_supports(holes, outline, bottom)
    issues.extend(support_issues)
    nearest_top, top_issues = top_support_check(supports, top_bodies, top_pads)
    issues.extend(top_issues)
    issues.extend(f'{ref}: outside bore by {-mgn:.3f} mm' for mgn, ref, _, _ in rows if mgn < 0)
    return dict(profile='r11', rows=sorted(rows), issues=issues, supports=supports, nearest_support=nearest,
                nearest_top_support=nearest_top, top_hardware_radius_mm=TOP_HARDWARE_RADIUS, wire_room_mm={},
                gh_ports=gh, gh_drawing=GH_DRAWING, gh_wire_straight_mm=GH_WIRE_STRAIGHT,
                wire_pads=sorted(wires), wire_allowance=dict(WIRE_ALLOWANCE, od=WIRE_OD, basis='Inference'),
                outline=outline, width_mm=width, length_mm=length, excluded=sorted(excluded), ok=not issues)


def wire_rooms(b, rows, profile, axis_x, tol):
    """Wire bend room from each side-entry terminal's entry face (its model box side farther from the axis, nearest
    the long edge) to the bore wall at WIRE_Z, sled tolerance both ways: {ref: (low, high) mm}. Profile r10 (R3-MEC-02,
    R18-MEC-03, D-R19-14): every DB125 terminal (all eight, J1 / J121 / J400 / J440 west and J410 / J420 / J9 / J122
    east); else
    SIDE_ENTRY's DB128 terminals. To the nominal bore wall (BORE_R), as P-11 measures it."""
    out = {}
    for _, ref, _, box in rows:
        f = b.FindFootprintByReference(ref)
        if f is None or ref in out:
            continue
        if profile == 'r10':
            if not fp_name(f).startswith(('M3_DB125', 'M3_DB128')):
                continue
        elif ref not in SIDE_ENTRY or not fp_name(f).startswith('M3_DB128'):
            continue
        face = box[0] if abs(box[0] - axis_x) > abs(box[2] - axis_x) else box[2]
        room = math.sqrt(BORE_R ** 2 - WIRE_Z ** 2) - abs(face - axis_x)
        out[ref] = (round(room - tol, 3), round(room + tol, 3))
    return dict(sorted(out.items()))


def margin(box, radius, axis_x, tol):
    x0, _, x1, _, z0, z1 = box
    dx = max(abs(x0 - axis_x), abs(x1 - axis_x)) + tol
    dz = max(abs(z0), abs(z1)) + tol
    return radius - math.hypot(dx, dz)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board', nargs='?', default='m3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--profile', choices=('r9', 'r10', 'r11'), default='r9')
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
    print(f"  board: {report['width_mm']:g} x {report['length_mm']:g} mm; "
          + (f"{R11_MAX_LENGTH:g} mm ceiling (D-R11-02)" if a.profile == 'r11' else '120 mm maximum (P1)'))
    if report['nearest_support']:
        distance, ref, hole = report['nearest_support']
        print(f'  nearest bottom/pin envelope: {ref}, {distance:.3f} mm from support {hole} (minimum 3.5 mm)')
    if report['nearest_top_support']:
        distance, ref, hole = report['nearest_top_support']
        print(f'  nearest top hardware clearance: {ref}, {distance:.3f} mm from support {hole} (minimum 3.8 mm)')
    walls = [f'{ref} {low:.2f}-{high:.2f}' for ref, (low, high) in report['wire_room_mm'].items()]
    if walls:                                        # wire_rooms(): every R10 DB125 terminal (R18-MEC-03)
        print(f'  wire entry to the bore wall at {WIRE_Z} mm height: ' + ', '.join(walls))
    for issue in report['issues']:
        print('  FAIL', issue)
    print('fit check:', 'OK (CAD envelopes only)' if report['ok'] else f"FAIL ({len(report['issues'])} findings)")
    if a.report:
        report.update(board_sha256=before[board_path.name], inputs_sha256=before,
                      checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      radius_mm=a.radius, axis_x_mm=a.axis_x, tolerance_mm=a.tol,
                      mated_envelopes=R10_MATED if a.profile in ('r10', 'r11') else MATED, physical_fit_verified=False)
        a.report.write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
