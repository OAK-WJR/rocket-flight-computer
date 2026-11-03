#!/usr/bin/env python3
"""Build the M3-ASSY-R11 placed board (r11_plan.md section 4, stage B) from the stage-A netlist and r11_place.tsv.

usage: <KiCad python3> -I -B m3_design/r11_pcb.py [--project m3_design/r11] [--place m3_design/r11_place.tsv]
                                                  [--draft]

1. A new six-layer board (D-R11-03): F.Cu / In1.Cu (GND) / In2.Cu (power) / In3.Cu (signal) / In4.Cu (GND) / B.Cu,
   JLCPCB stackup JLC06161H-3313 (STACKUP below, from https://jlcpcb.com/impedance, read 2026-11-02), 1.6 mm, ENIG.
2. Every part of schematic.net.xml (stage A) is loaded from the project library (kilib/rocket.pretty), with its
   reference, value, fields, schematic path and pad nets from the netlist; no other footprint source.
3. Outline and holes from the table's '@' rows: one 46 x L rectangle from (0, 0) and the M3 supports as 3.2 mm
   Edge.Cuts circles (fit_check --profile r11: one support within 6 mm of each corner).
4. Every part placed from r11_place.tsv (each reference exactly once; side F or B; rotation in KiCad degrees after
   the flip). The sensor rule areas (R10's IMU_body_B / IMU_no_internal_tracks / BARO_body_B /
   BARO_no_inter_row_tracks, on the parts' own side) are derived from U4 / U5's placed courtyard and pads.
5. No copper but the footprints' own: no track, via or zone fill (stage C draws copper from explicit tables).
6. Title block M3-ASSY-R11; the gate data the stage records (r11/design/r11_gate_data.json: imu,
   short_edge_queries) is rewritten from the placed board, keeping any other key.
Deterministic: fixed KIID seed, table order, no search; a rebuild reproduces the board byte for byte.
The legality checks (courtyards, edges, supports) run here and stop the build; --draft saves an illegal board for
inspection (r11_build.sh never passes it).
"""
import argparse
import csv
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'm3_design/r11'
PLACE = ROOT / 'm3_design/r11_place.tsv'
REV = 'M3-ASSY-R11'
KIID_SEED = 11011
WIDTH = 46.0
MAX_LENGTH = 56.0                       # D-R11-02 ceiling
HOLE_R = 1.6                            # 3.2 mm M3 clearance hole, nylon hardware (P2)
EDGE_W = 0.05
EDGE_MIN = 0.25                         # courtyard to any edge (stage B rule; J3's shell overhang excepted below)
SHORT_EDGE_DFM = 0.5                    # courtyard to a short edge with the JLC panel's 5 mm rails there (D-R11-12)
SUPPORTS = ((3.5, 3.5), (42.5, 3.5), (3.5, 46.5), (42.5, 46.5))   # D-R11-10: the four corner M3 supports (M-3 pin)
TOP_HARDWARE = 3.8                      # top bodies / pads to a support centre (fit_check TOP_HARDWARE_RADIUS)
BOTTOM_STANDOFF = 3.5                   # bottom courtyards to a support centre (P2, check_r10.m6)
BOTTOM_THT = 1.5                        # bottom courtyards to a foreign plated pad (check_r10.m6)
EDGE_EXCEPT = {'J3': 'USB-C receptacle mouth reaches the east edge (as R10 J3, shell 0.45 mm proud); bench only'}
MM = pcbnew.FromMM
mm = pcbnew.ToMM

# JLC06161H-3313, top to bottom (https://jlcpcb.com/impedance, 6-layer table, item 2; read 2026-11-02):
# copper outer 0.035 mm (1 oz finished), inner 0.0152 mm (0.5 oz), prepreg 3313 x1 0.0994, core 0.55, prepreg 2116 x1
# 0.1088, core 0.55, prepreg 3313 x1 0.0994. Dielectric constants are not used: R11 has no controlled-impedance line.
STACKUP = (('F.Cu', 0.035), ('prepreg', 0.0994, '3313'), ('In1.Cu', 0.0152), ('core', 0.55, 'core'),
           ('In2.Cu', 0.0152), ('prepreg', 0.1088, '2116'), ('In3.Cu', 0.0152), ('core', 0.55, 'core'),
           ('In4.Cu', 0.0152), ('prepreg', 0.0994, '3313'), ('B.Cu', 0.035))
LAYER_ROLE = {'In1.Cu': 'power', 'In2.Cu': 'power', 'In3.Cu': 'signal', 'In4.Cu': 'power'}   # GND, rails, signal, GND


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def read_place(path):
    rows, feat = {}, dict(outline=None, supports=[])
    with open(path) as fh:
        for r in csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t'):
            ref, x, y = r['ref'], float(r['x']), float(r['y'])
            if ref == '@OUTLINE':
                assert feat['outline'] is None, '@OUTLINE twice'
                feat['outline'] = (x, y)
            elif ref == '@M3':
                feat['supports'].append((x, y))
            else:
                assert not ref.startswith('@'), f'unknown feature row {ref}'
                assert ref not in rows, f'{ref} twice in {path}'
                assert r['side'] in ('F', 'B'), r
                rows[ref] = (x, y, float(r['rot']), r['side'])
    w, length = feat['outline']
    assert abs(w - WIDTH) < 1e-9 and 0 < length <= MAX_LENGTH, f'outline {w} x {length} (D-R11-02)'
    assert 4 <= len(feat['supports']) <= 5, 'four or five @M3 rows'
    return rows, feat


def netlist(project):
    root = ET.parse(project / 'schematic.net.xml').getroot()
    comps = {n.attrib['ref']: n for n in root.findall('./components/comp')}
    pin_nets, names = {}, []
    for node in root.findall('./nets/net'):
        name = node.attrib['name']
        if name.startswith('unconnected-('):          # KiCad escapes '/' inside a pin-derived net name
            name = name.replace('/', '{slash}')
        names.append(name)
        for pin in node.findall('node'):
            pin_nets[(pin.attrib['ref'], pin.attrib['pin'])] = name
    return comps, pin_nets, names


def kiid_path(s):
    p = pcbnew.KIID_PATH()
    for part in s.split('/'):
        if part:
            p.push_back(pcbnew.KIID(part))
    return p


def layers(board):
    board.SetCopperLayerCount(6)
    enabled = board.GetEnabledLayers()
    for name, role in LAYER_ROLE.items():
        lid = board.GetLayerID(name)
        enabled.addLayer(lid)
        board.SetLayerType(lid, {'power': pcbnew.LT_POWER, 'signal': pcbnew.LT_SIGNAL}[role])
    board.SetEnabledLayers(enabled)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))


def stackup_text(text):
    """Replace the saved (stackup ...) block with JLC06161H-3313 (string edit: deterministic, no API defaults)."""
    lines = ['\t\t(stackup',
             '\t\t\t(layer "F.SilkS"\n\t\t\t\t(type "Top Silk Screen")\n\t\t\t)',
             '\t\t\t(layer "F.Paste"\n\t\t\t\t(type "Top Solder Paste")\n\t\t\t)',
             '\t\t\t(layer "F.Mask"\n\t\t\t\t(type "Top Solder Mask")\n\t\t\t\t(thickness 0.01)\n\t\t\t)']
    n = 0
    for item in STACKUP:
        if item[0].endswith('.Cu'):
            lines.append(f'\t\t\t(layer "{item[0]}"\n\t\t\t\t(type "copper")\n\t\t\t\t(thickness {item[1]})\n\t\t\t)')
        else:
            n += 1
            lines.append(f'\t\t\t(layer "dielectric {n}"\n\t\t\t\t(type "{item[0]}")\n\t\t\t\t(color "FR4 natural")'
                         f'\n\t\t\t\t(thickness {item[1]})\n\t\t\t\t(material "FR4 {item[2]}")\n\t\t\t\t(epsilon_r 4.5)'
                         f'\n\t\t\t\t(loss_tangent 0.02)\n\t\t\t)')
    lines += ['\t\t\t(layer "B.Mask"\n\t\t\t\t(type "Bottom Solder Mask")\n\t\t\t\t(thickness 0.01)\n\t\t\t)',
              '\t\t\t(layer "B.Paste"\n\t\t\t\t(type "Bottom Solder Paste")\n\t\t\t)',
              '\t\t\t(layer "B.SilkS"\n\t\t\t\t(type "Bottom Silk Screen")\n\t\t\t)',
              '\t\t\t(copper_finish "ENIG")', '\t\t\t(dielectric_constraints no)', '\t\t)']
    block = '\n'.join(lines)
    start = text.find('\t\t(stackup')
    if start < 0:
        anchor = text.find('\t(setup\n') + len('\t(setup\n')
        return text[:anchor] + block + '\n' + text[anchor:]
    depth, i = 0, start
    while True:
        c = text[i]
        depth += c == '('
        depth -= c == ')'
        i += 1
        if depth == 0 and c == ')':
            break
    return text[:start] + block + text[i:]


def load_parts(board, project, comps, pin_nets, names):
    lib = project / 'kilib/rocket.pretty'
    for name in names:
        board.Add(pcbnew.NETINFO_ITEM(board, name))
    for ref in sorted(comps):
        node = comps[ref]
        nick, item = node.findtext('footprint').split(':', 1)
        assert nick == 'rocket', f'{ref}: footprint outside the project library ({nick})'
        f = pcbnew.FootprintLoad(str(lib), item)
        assert f is not None, f'{ref}: cannot load {item}'
        f.SetFPID(pcbnew.LIB_ID(nick, item))
        f.SetReference(ref)
        f.SetValue(node.findtext('value', ''))
        fields = {fl.attrib['name']: fl.text or '' for fl in node.findall('./fields/field')}
        for name, value in fields.items():
            if name not in ('Footprint', 'Reference', 'Value'):
                f.SetField(name, value)
        f.SetPath(kiid_path(node.find('sheetpath').attrib['tstamps'] + node.findtext('tstamps')))
        board.Add(f)
        for p in f.Pads():
            net = pin_nets.get((ref, p.GetNumber()))
            p.SetNet(board.FindNet(net) if net else board.FindNet(0))
        if ref.startswith('TP') or ref == 'J2':      # bare probe / programming contacts: no part, no placement
            f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        for p in f.Pads():
            if ref.startswith('TP'):
                p.SetLocalClearance(MM(1.0))            # the DRU's TP floor, also a native-fill override (R10)
            elif ref.startswith(('R', 'C')) and p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD \
                    and max(mm(p.GetSize().x), mm(p.GetSize().y)) <= 2.0:
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)   # R10 policy; gap / spoke from the DRU
            elif ref == 'J1' and p.GetNetname() == 'GND':
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)   # solderable plated GND barrel (R10)
        for field in f.GetFields():
            field.SetVisible(False)
    missing = sorted({r for r, _ in pin_nets} - set(comps))
    assert not missing, f'netlist nodes without a part: {missing}'


def outline(board, feat):
    w, length = feat['outline']
    pts = [(0, 0), (w, 0), (w, length), (0, length)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(V(*pts[i]))
        s.SetEnd(V(*pts[(i + 1) % 4]))
        s.SetWidth(MM(EDGE_W))
        board.Add(s)
    for c in feat['supports']:
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetCenter(V(*c))
        s.SetEnd(V(c[0] + HOLE_R, c[1]))
        s.SetWidth(MM(EDGE_W))
        board.Add(s)


def place(board, rows):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    assert set(rows) == set(fps), (f'placement table must name every part: missing {sorted(set(fps) - set(rows))}, '
                                   f'unknown {sorted(set(rows) - set(fps))}')
    for ref in sorted(rows):
        x, y, rot, side = rows[ref]
        f = fps[ref]
        if side == 'B':
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        f.SetOrientationDegrees(rot)
        f.SetPosition(V(x, y))
        f.Value().SetLayer(pcbnew.B_Fab if side == 'B' else pcbnew.F_Fab)


def courtyard(f):
    return f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)


def box(f):
    bb = courtyard(f).BBox()
    return mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())


def rule_area(board, name, layer, rect, tracks, pour):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetLayer(layer)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(not tracks)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowZoneFills(not pour)
    z.SetDoNotAllowFootprints(False)
    x0, y0, x1, y1 = rect
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(MM(x), MM(y))
    board.Add(z)


def sensor_areas(board):
    """R10's four sensor rule areas, re-derived for the placed U4 / U5 on their own copper side: the body (courtyard
    less 0.25 mm: no via, no pour; tracks allowed) and the pad-ring interior (U4) / the inter-row band (U5): no track,
    no via."""
    out = {}
    for ref, body_name, inner_name in (('U4', 'IMU_body_B', 'IMU_no_internal_tracks'),
                                       ('U5', 'BARO_body_B', 'BARO_no_inter_row_tracks')):
        f = board.FindFootprintByReference(ref)
        assert f.IsFlipped(), f'{ref} must be on the bottom (R10 sensor areas are B.Cu; M-7)'
        x0, y0, x1, y1 = box(f)
        body = (x0 + 0.25, y0 + 0.25, x1 - 0.25, y1 - 0.25)
        pads = [p for p in f.Pads()]
        px = sorted(mm(p.GetPosition().x) for p in pads)
        py = sorted(mm(p.GetPosition().y) for p in pads)
        if ref == 'U4':        # interior of the pad ring: inside the inner pad edges
            halfx = min(abs(mm(p.GetPosition().x) - mm(f.GetPosition().x)) - mm(p.GetBoundingBox().GetWidth()) / 2
                        for p in pads if abs(mm(p.GetPosition().x) - mm(f.GetPosition().x)) > 1.0)
            halfy = min(abs(mm(p.GetPosition().y) - mm(f.GetPosition().y)) - mm(p.GetBoundingBox().GetHeight()) / 2
                        for p in pads if abs(mm(p.GetPosition().y) - mm(f.GetPosition().y)) > 0.8)
            cx, cy = mm(f.GetPosition().x), mm(f.GetPosition().y)
            inner = (cx - halfx, cy - halfy, cx + halfx, cy + halfy)
        else:                  # band between the two pad rows, full body width
            cy = mm(f.GetPosition().y)
            rows_y = sorted({round(v, 3) for v in py})
            top = max(v for v in rows_y if v < cy)
            bot = min(v for v in rows_y if v > cy)
            hh = max(mm(p.GetBoundingBox().GetHeight()) for p in pads) / 2
            inner = (body[0], top + hh, body[2], bot - hh)
        rule_area(board, body_name, pcbnew.B_Cu, body, tracks=True, pour=False)
        rule_area(board, inner_name, pcbnew.B_Cu, inner, tracks=False, pour=True)
        out[ref] = dict(body=[round(v, 4) for v in body], inner=[round(v, 4) for v in inner])
    return out


def point_box(p, b):
    dx = max(b[0] - p[0], 0, p[0] - b[2])
    dy = max(b[1] - p[1], 0, p[1] - b[3])
    return math.hypot(dx, dy)


def legality(board, feat):
    """Placement rules this stage holds (the gate re-checks them): courtyards apart on each face, inside the outline
    by EDGE_MIN (long edges) / SHORT_EDGE_DFM (short edges), bottom courtyards >= 3.5 mm from support centres and
    >= 1.5 mm from foreign plated pads, top courtyards >= 3.8 mm from support centres."""
    w, length = feat['outline']
    fps = sorted(board.GetFootprints(), key=lambda f: f.GetReference())
    issues, near = [], {}
    for i, f in enumerate(fps):
        a = courtyard(f)
        for g in fps[i + 1:]:
            if f.IsFlipped() != g.IsFlipped():
                continue
            if a.Collide(courtyard(g), 0):
                inter = pcbnew.SHAPE_POLY_SET(a)
                inter.BooleanIntersection(courtyard(g))
                if inter.Area() > 0:
                    issues.append(f'courtyards overlap: {f.GetReference()} / {g.GetReference()} '
                                  f'({inter.Area() / 1e12:.3f} mm2)')
    tht = [(f.GetReference(), p) for f in fps for p in f.Pads()
           if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for f in fps:
        ref = f.GetReference()
        x0, y0, x1, y1 = box(f)
        long_gap, short_gap = min(x0, w - x1), min(y0, length - y1)
        near[ref] = round(short_gap, 3)
        if ref not in EDGE_EXCEPT and (long_gap < EDGE_MIN - 1e-6 or short_gap < SHORT_EDGE_DFM - 1e-6):
            issues.append(f'{ref} courtyard {long_gap:.3f} mm from a long edge / {short_gap:.3f} mm from a short edge')
        for c in feat['supports']:
            d = point_box(c, (x0, y0, x1, y1))
            lim = BOTTOM_STANDOFF if f.IsFlipped() else TOP_HARDWARE
            if d < lim - 1e-6:
                issues.append(f'{ref} courtyard {d:.3f} mm from support {c} (minimum {lim})')
        if f.IsFlipped():
            cy = courtyard(f)
            for other, p in tht:
                if other == ref:
                    continue
                shape = p.GetEffectiveShape(pcbnew.B_Cu)
                if cy.Collide(shape, MM(BOTTOM_THT)):
                    issues.append(f'bottom {ref} within {BOTTOM_THT} mm of {other}.{p.GetNumber()} (plated)')
    return issues, near


def gate_data(project, board, feat, near):
    """Rewrite the stage-B keys of r11_gate_data.json from the placed board; other keys are kept."""
    path = project / 'design/r11_gate_data.json'
    data = json.loads(path.read_text()) if path.is_file() else {}
    u4 = board.FindFootprintByReference('U4')
    data['imu'] = dict(rotation=round(u4.GetOrientationDegrees(), 3), side='B',
                       lever_mm=round(mm(u4.GetPosition().x) - 23.0, 3), tol_mm=0.05,
                       basis='stageB.md section 6 (D-R11-11): R10 axis map kept, roll = -gyro_Y')
    # D-R11-10 / D-R11-32: check_r11 M-3 pins the four corner supports by this key; the build writes the reviewed
    # centres (SUPPORTS) and stops if the placement table's @M3 rows differ from them
    assert sorted(feat['supports']) == sorted(SUPPORTS), ('@M3 rows differ from D-R11-10', feat['supports'])
    data['supports'] = [list(c) for c in SUPPORTS]
    data['short_edge_queries'] = {ref: ['aft' if box(board.FindFootprintByReference(ref))[1] < feat['outline'][1] / 2
                                        else 'forward', d]
                                  for ref, d in sorted(near.items()) if d < 2.5 - 1e-6}
    data['short_edge_basis'] = ('D-R11-12: the JLC assembly panel carries 5 mm rails on both short edges, so the '
                                'board short edges are not conveyor edges; courtyards hold >= 0.5 mm there')
    path.write_text(json.dumps(data, indent=1, sort_keys=True) + '\n')
    return data


def build(project, table, draft=False):
    rows, feat = read_place(table)
    comps, pin_nets, names = netlist(project)
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    board = pcbnew.CreateEmptyBoard() if hasattr(pcbnew, 'CreateEmptyBoard') else pcbnew.BOARD()
    layers(board)
    load_parts(board, project, comps, pin_nets, names)
    outline(board, feat)
    place(board, rows)
    areas = sensor_areas(board)
    title = board.GetTitleBlock()
    title.SetTitle('Flight computer R11 — CAD candidate')
    title.SetRevision(REV)
    title.SetCompany('Aerodynamic roll-control rocket')
    title.SetDate('2026-11-02')
    board.BuildConnectivity()
    issues, near = legality(board, feat)
    for i in issues:
        print('r11_pcb: ILLEGAL', i)
    if issues and not draft:
        sys.exit(f'r11_pcb: {len(issues)} placement issues; nothing saved')
    out = project / 'm3.kicad_pcb'
    assert pcbnew.SaveBoard(str(out), board, True), 'save failed'
    out.write_text(stackup_text(out.read_text()))
    data = gate_data(project, board, feat, near)
    print(f'r11_pcb: {len(rows)} parts; outline {feat["outline"][0]:g} x {feat["outline"][1]:g} mm; '
          f'{len(feat["supports"])} supports; sensor areas {sorted(areas)}; short-edge queries '
          f'{len(data["short_edge_queries"])}; no tracks, vias or fills')
    return board


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--project', type=Path, default=PROJECT)
    ap.add_argument('--place', type=Path, default=PLACE)
    ap.add_argument('--draft', action='store_true')
    a = ap.parse_args()
    build(a.project.resolve(), a.place, a.draft)


if __name__ == '__main__':
    main()
