#!/usr/bin/env python3
"""R9 build step 8 gate: the board's ground (r9_plan.md section 4 step 8; R9_DECISIONS D-S8-*).

usage: <KiCad python3> -I m3_design/r9_ground_check.py [board] [--report OUT.json] [--seed SEED.json]
       exit 0 = every gate passes

The board is r9_ground.py's output: every net routed (steps 4-7) plus the board-wide GND pours and the GND stitching of
m3_design/r9_ground.tsv. Gates (tools/check_r9.py, route_check.py, critical_reference.py, check_actuators.py and the
step-5 gate's pyro functions are called, never restated or weakened):
  table      the three GND pours are the grown strip pours (r9_ground.POURS: settings, BOARD_BOX outline, names) and
             every row of r9_ground.tsv is on the board: a GND via of r9_ground.VIA at its point, each track; the
             crystal's In2 GND plane is r9_ground.XTAL_ZONE (R9_GND_In2's settings, the rule area's outline less
             r9_ground.xtal_outline's notches, its priority) and the rule area keeps In2 tracks out without barring
             fills (D-S8-20); every via keeps pads only on the layers it connects (r9_ground.VIA_MODE, D-S8-19)
  drc        kicad-cli DRC with schematic parity, every severity: no violation but the silkscreen classes r9_post.py
             settles (step 9), no unconnected item (every net whole, GND included), no parity item
  route      tools/route_check.py, profile r9 (empty allowlist and leftover list): no failing instance, so no GND pour
             sliver or finger, no pad pour cut, no dangling or dead GND copper, and a GND via within 1.5 mm of every
             critical layer change (AGENTS 3)
  stitch     every table via: inside no non-GND F.Cu / B.Cu fill, no In2 power region within its 7.7 A corridor
             (tools/run_dc.sh terminals + 2 mm; a RAW_ACT cut is allowed only inside a box of the aid's recorded
             CORRIDOR_EXCEPT, D-F1-07), >= ARMED_GAP from bus / igniter / drain copper and >= PYRO_GAP from every
             other pyro / arming net's copper (geometric, independent of DRC); >= SPACING_MIN from every GND via
  in2        the step-6 In2 gate (r9_power_check.gate_in2) on the stitched board: the four regions each one piece (no
             GND antipad splits a power region), no In1 / In2 track
  xtal       In2 inside the crystal's area (Y1_In2_keepout: Y1, C25, C26, R5 V1) is GND only: no other net's fill there
             beyond the In2 pads of its own vias (a via ring may lie across the area's edge), the plane fills
             >= XTAL_COVER of the area as one piece holding >= 2 GND vias (AN2867 section 5.1, D-S8-20)
  islands    survey P7: every F.Cu / B.Cu GND pour island holds two or more GND vias or plated GND holes, except the
             recorded pockets of WEAK_EXCEPT at no more than their measured area and via count (a stale entry fails)
  reach      survey P9 / P10 (0.5 mm raster inside the outline, distance to the nearest GND via or plated GND hole):
             p95 <= P9_MAX and max <= P10_MAX (the done rows of r9_plan section 2, or the recorded ceiling with its
             measured cause)
  copper     through-copper reach (R9 review pass 1, R9P1-PLANES-01 / -03; the aid's copper stage and its raster):
             every GND SMD pad of a C / U / Q / J part forward of the strip within PAD_REACH_ALL (5 mm) of copper of a
             GND via or plated GND hole, and every outer GND copper point within COPPER_REACH (8 mm), judged per
             cluster of the copper beyond it (the aid's over_clusters: a dead end's far part, at its worst point), but
             the recorded exceptions (COPPER_PAD_EXCEPT, COPPER_EXCEPT: each at no more than its measured reach + 0.1 mm;
             a stale entry fails)
  reference  critical_reference.py BOARD BOARD (scorecard R6b): no more unreferenced samples than REF_UNREF_MAX, the
             measured count of the built board, and no unreferenced sample that is not inside its own net's via antipad
             (REF_OWN_R of a same-net via; the crystal plane removed the keep-out class, the vias' pads the other-via
             class, D-S8-17) but the recorded REF_STRAY ones, in the R6 set and in critical_reference's extended set
             (SWD, NRST, the radio SPI); the share and the per-side counts are reported
  pyro       the step-5 gate's functions: margins (A-H, A2), bridge table, GATE_N's neighbours, sense MCU sides, X2
  contract   check_r9: every rule but M-2 (placement-bound, step 3's gate) and K-legends (step 9), P-4 with this board's
             seeded report
  actuators  m3_design/check_actuators.py on the board and m3.kicad_dru: no finding
"""
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r9 as C9  # noqa: E402
import critical_reference as CR  # noqa: E402
import route_check as rc  # noqa: E402
import r9_ground as G  # noqa: E402
import r9_ground_aid as A  # noqa: E402
import r9_power_check as PW  # noqa: E402
import r9_pyro_check as PC  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
DRC_DEFERRED = {'silk_over_copper', 'silk_overlap', 'silk_edge_clearance'}      # r9_post.py (step 9)
CONTRACT_SKIP = {'M-2', 'K-legends'}
ARMED_GAP, PYRO_GAP = A.ARMED_GAP, A.PYRO_GAP
SPACING_MIN = A.SPACING_ISLAND  # mm, GND via centre to GND via centre (the aid's closest spacing, 0.6)
# r9_plan section 2 done rows P9 <= 3.5 and P10 <= 7.0. P10 carries a recorded ceiling (D-S8-16): its maximum lies in the
# battery entry (J1.1 -> Q120: BAT_IN pours on F.Cu, B.Cu and In2), where a GND via would cut the 7.7 A path; with every
# legal spot of the step-7 board used at once the maximum is 7.28 mm (step8_evidence/reach_floor.py); the stitching 7.32
P9_MAX, P10_MAX = 3.5, 7.35
# critical_reference unreferenced samples of the built board (D-S8-17): every one inside the own antipad (r 0.40 mm: hole
# r 0.15 + the 0.25 mm hole clearance) of one of the 12 critical layer-change vias, 24 via sides
REF_UNREF_MAX = 3206
REF_OWN_R = 0.45              # mm: a sample this close to a same-net via centre lies in that via's own antipad
XTAL_COVER = 0.9              # the crystal plane's share of its area (the rest: the clearance round non-GND via holes)
# unreferenced samples outside their own net's via antipads, recorded (net, layer, x, y, reason); a sample matches within
# 0.01 mm; an unmatched sample or an entry matching nothing fails the gate
REF_STRAY = [
    ('USB_DM', 'F.Cu', 8.0793, 33.0793, "the copper edge of USB_DM's 45-degree run grazes CC1's via antipad (7.85, 32.75), "
                                        "r 0.40 mm: 0.401 mm from the via centre (usb_swd; one edge sample)"),
]
# Outer GND pour islands allowed fewer than two GND vias / plated GND holes: (layer, centre x, y of the island's box,
# measured area mm2, vias, reason). An island matches an entry when its box centre is within 0.3 mm.
# Recorded pockets (D-S8-15): no legal spot for a second via, and the alternative is a pour trim (X8c = 0) or re-routing
# steps 4-7's copper round them.
WEAK_EXCEPT = [
    ('F', 31.4, 73.6, 0.27, 1, "C150 / C151's GND via (r9_power) inside the F.Cu RAW_ACT spine pour: the island is the "
                               "via's own pad"),
    ('F', 13.03, 47.7, 6.03, 1, "U1's interior west of its lanes, over U4: IMU_body_B (M-7) bars a via under U4; its via "
                                "is imu_baro's U4 GND via (11.75, 49.1)"),
    ('F', 9.24, 34.1, 2.82, 1, "D4.2's pocket under D4 (usb_swd's GND via (9.95, 34.1)); R8 D63's exception, same "
                               "geometry"),
    ('F', 24.35, 14.64, 0.71, 1, "between RADIO_MOSI and RADIO_NSS at U31.13 / 14 (rf_if), step 4's via; R8 trimmed it "
                                 "(G5)"),
    ('B', 11.64, 49.16, 0.78, 1, "inside U4's 3V3A loop round its GND via (imu_baro); R8 trimmed it (G3)"),
    ('B', 40.43, 36.77, 3.51, 1, "between the CAM_INPUT_LIMITED 1.0 mm bar and U8's pin row, R72.2's GND via (r9_power); "
                                 "R8 trimmed it (G6)"),
    ('B', 31.4, 73.6, 0.88, 1, "C150.2 / C151.2 inside the B.Cu RAW_ACT spine pour, their GND via (r9_power)"),
    ('B', 31.16, 55.1, 7.71, 1, "the RAW_ACT_SENSE divider's GND pads, walled by its column, USB_LIMITED and the J122 tie "
                                "hole; TP90 / TP91's 1.0 mm keep-outs and the VLOGIC tap leave one via spot"),
    ('B', 31.53, 51.13, 1.77, 1, "between LOGIC_SOURCE_ST and USB_LIMITED under CAM_MCU_TX's F.Cu corner: the reach "
                                 "stage's via, which meets P9 (D-S8-16)"),
]


# Recorded through-copper reach exceptions (D-F1-07; R9_VALIDATION C22): GND pads (name, measured mm, reason) and
# clusters of outer GND copper beyond COPPER_REACH (layer, x, y of the cluster's farthest point, measured mm, reason);
# a cluster matches an entry whose point lies in it. Each is a spot the aid's copper stage logged with no legal via at
# least COPPER_MIN_GAIN of copper from a via within its reach; the layers under it are measured on the board.
COPPER_PAD_EXCEPT = [
    ('J9.2', 6.99, "J9's camera-return pad in J9's GND piece between its pins and mounting pads, which holds no legal "
                   "via spot (R8 C15 recorded J9.2 at 6.92 mm)"),
]
COPPER_EXCEPT = [
    ('F', 37.45, 73.75, 9.50, "the strip x 36.15-37.35 between the RAW_ACT F.Cu pour and VLOGIC's sense tap, dead-ended "
                              "at y 74: In2 under it is the 3V3 finger, whose 1.49 mm takes no antipad (D-S8-02); the "
                              "copper stage's via (35.6, 64.8) serves its north end (28.41 mm on fc3d5b34, R9P1-PLANES-01)"),
    ('F', 28.95, 68.35, 9.37, "D-S8-05's 0.66 mm guard strip between the ARM1_SENSE lane (x 28.53) and the RAW_ACT F.Cu "
                              "pour, joined at both ends: RAW_ACT on In2 and B.Cu under it (the 7.7 A corridor) and the "
                              "pyro lane's PYRO_GAP leave no via spot"),
    ('F', 41.75, 48.45, 8.95, "J9's GND piece (J9.2, the camera return) between its pins and mounting pads"),
    ('F', 28.85, 59.95, 8.61, "the guard strip's north end at the RAW_ACT spine-to-row corner: RAW_ACT on In2 and B.Cu "
                              "under it"),
    ('F', 31.15, 87.75, 8.48, "the F.Cu GND piece between the power pours over the FET pair: ACT_FET_S on B.Cu under it "
                              "(the 7.7 A corridor)"),
    ('F', 39.85, 48.45, 8.05, "a 0.02 mm2 corner of J9's GND piece"),
]


def r4(v):
    return round(v + 0.0, 4)


def gate_table(b):
    issues = []
    zones = {z.GetZoneName(): z for z in b.Zones() if not z.GetIsRuleArea()}
    for old, new, lid, prio, clr, minw, conn, gap, spoke in G.POURS:
        z = zones.get(new)
        if z is None:
            issues.append(f'table: pour {new} missing')
            continue
        layers = list(z.GetLayerSet().Seq())
        got = (z.GetNetname(), layers, z.GetAssignedPriority(), r4(mm(z.GetLocalClearance())),
               r4(mm(z.GetMinThickness())), z.GetPadConnection(), r4(mm(z.GetThermalReliefGap())),
               r4(mm(z.GetThermalReliefSpokeWidth())), z.GetIslandRemovalMode(), G.outline(z))
        want = ('GND', [lid], prio, clr, minw, conn, gap, spoke, pcbnew.ISLAND_REMOVAL_MODE_ALWAYS,
                G.box_points(G.BOARD_BOX))
        if got != want:
            issues.append(f'table: pour {new} is {got}, not {want}')
        if old in zones:
            issues.append(f'table: the strip pour {old} is still on the board')
    rows = G.read()
    vias = {(r4(mm(t.GetPosition().x)), r4(mm(t.GetPosition().y))): t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA'}
    ends = {(t.GetNetname(), pcbnew.LayerName(t.GetLayer())[0], r4(mm(t.GetWidth())),
             tuple(sorted(((r4(mm(t.GetStart().x)), r4(mm(t.GetStart().y))), (r4(mm(t.GetEnd().x)), r4(mm(t.GetEnd().y)))))))
            for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK'}
    nv = nt = 0
    for r in rows:
        if r['item'] == 'via':
            nv += 1
            q = (r4(float(r['x0'])), r4(float(r['y0'])))
            v = vias.get(q)
            if v is None or v.GetNetname() != 'GND' or (r4(mm(v.GetWidth(pcbnew.F_Cu))), r4(mm(v.GetDrillValue()))) != G.VIA:
                issues.append(f'table: GND via {q} ({r["basis"]}) not on the board as drawn')
        elif r['item'] == 'track':
            nt += 1
            key = ('GND', r['layer'], r4(float(r['size'])),
                   tuple(sorted(((r4(float(r['x0'])), r4(float(r['y0']))), (r4(float(r['x1'])), r4(float(r['y1'])))))))
            if key not in ends:
                issues.append(f'table: GND track {key} ({r["basis"]}) not on the board')
        else:
            issues.append(f'table: unknown item {r}')
    more, nvias = gate_xtal_table(b)
    issues += more
    return issues, dict(vias=nv, tracks=nt, pours=[p[1] for p in G.POURS], board_vias=nvias,
                        crystal_plane=G.XTAL_ZONE[0])


def gate_xtal_table(b):
    """The crystal plane, its rule area and the vias' pad mode as r9_ground.py makes them (D-S8-19 / 20)."""
    issues = []
    every = {z.GetZoneName(): z for z in b.Zones()}
    ko, xz, like = every.get(G.XTAL_AREA), every.get(G.XTAL_ZONE[0]), every.get(G.XTAL_LIKE)
    if ko is None or not ko.GetIsRuleArea() or list(ko.GetLayerSet().Seq()) != [pcbnew.In2_Cu] or \
            G.area_flags(ko) != G.XTAL_FLAGS:
        issues.append(f'table: rule area {G.XTAL_AREA} is not the In2 track keep-out r9_ground.py leaves '
                      f'({G.area_flags(ko) if ko is not None else None}, want {G.XTAL_FLAGS})')
    if xz is None or like is None or xz.GetIsRuleArea():
        issues.append(f'table: the crystal plane {G.XTAL_ZONE[0]} (or {G.XTAL_LIKE}) missing')
    else:
        if G.zone_settings(xz) != G.zone_settings(like) or xz.GetAssignedPriority() != G.XTAL_ZONE[1]:
            issues.append(f'table: {G.XTAL_ZONE[0]} {G.zone_settings(xz)} priority {xz.GetAssignedPriority()} is not '
                          f'{G.XTAL_LIKE}\'s settings at priority {G.XTAL_ZONE[1]}')
        if ko is not None:
            want, notches = G.xtal_outline(b, ko)
            if G.outline(xz) != want:
                issues.append(f'table: {G.XTAL_ZONE[0]} outline {G.outline(xz)} is not {want} ({G.XTAL_AREA} less the '
                              f'notches {notches})')
    vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    keep = [(r4(mm(t.GetPosition().x)), r4(mm(t.GetPosition().y))) for t in vias
            if t.Padstack().UnconnectedLayerMode() != G.VIA_MODE]
    issues += [f'table: via {q} keeps pads on unconnected layers (D-S8-19)' for q in keep[:20]]
    return issues, len(vias)


def gate_xtal(b):
    """In2 under the crystal is GND only, one plane holding >= 2 GND vias (D-S8-20)."""
    issues = []
    every = {z.GetZoneName(): z for z in b.Zones()}
    ko = every.get(G.XTAL_AREA)
    if ko is None:
        return [f'xtal: rule area {G.XTAL_AREA} missing'], {}
    area = ko.Outline().CloneDropTriangulation()
    total = area.Area() / 1e12
    pads, rings = pcbnew.SHAPE_POLY_SET(), []
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA' and t.FlashLayer(pcbnew.In2_Cu):
            one = pcbnew.SHAPE_POLY_SET()
            t.TransformShapeToPolygon(one, pcbnew.In2_Cu, MM(0.001), MM(0.001), pcbnew.ERROR_OUTSIDE)
            pads.BooleanAdd(one)
            one.BooleanIntersection(area)
            if t.GetNetname() != 'GND' and one.Area() > 0:
                rings.append(f'{t.GetNetname()} ({r4(mm(t.GetPosition().x))}, {r4(mm(t.GetPosition().y))})')
    plane, foreign = None, {}
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.In2_Cu) or not z.HasFilledPolysForLayer(pcbnew.In2_Cu):
            continue
        f = z.GetFilledPolysList(pcbnew.In2_Cu).CloneDropTriangulation()
        f.BooleanIntersection(area)
        if z.GetZoneName() == G.XTAL_ZONE[0]:
            plane = f
            if z.GetNetname() != 'GND':
                issues.append(f'xtal: {G.XTAL_ZONE[0]} is on {z.GetNetname()}, not GND')
            continue
        f.BooleanSubtract(pads)
        a = f.Area() / 1e12
        if a > 1e-6:
            foreign[z.GetZoneName()] = round(a, 4)
    for name, a in foreign.items():
        issues.append(f'xtal: {name} fills {a} mm2 of In2 under the crystal ({G.XTAL_AREA})')
    if plane is None:
        return issues + [f'xtal: {G.XTAL_ZONE[0]} has no fill'], dict(foreign=foreign)
    gnd = [q for q in A.gnd_points(b) if plane.Contains(A.P(*q))]
    cover = plane.Area() / 1e12 / total
    if plane.OutlineCount() != 1:
        issues.append(f'xtal: the crystal plane fills as {plane.OutlineCount()} pieces')
    if cover < XTAL_COVER:
        issues.append(f'xtal: the crystal plane covers {cover:.3f} of its area (< {XTAL_COVER})')
    if len(gnd) < 2:
        issues.append(f'xtal: the crystal plane holds {len(gnd)} GND via(s) (< 2)')
    return issues, dict(area_mm2=round(total, 2), cover=round(cover, 4), pieces=plane.OutlineCount(),
                        gnd_vias=sorted(gnd), foreign=foreign, foreign_via_rings=rings)


def gate_drc(path):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(path)], capture_output=True)
        if not out.is_file():
            return ['drc: kicad-cli produced no report'], {}
        rep = json.loads(out.read_text())
    return judge_drc(rep)


def judge_drc(rep):
    bad, deferred = [], {}
    for v in rep['violations']:
        if v['type'] in DRC_DEFERRED:
            deferred[v['type']] = deferred.get(v['type'], 0) + 1
            continue
        bad.append(f"drc: {v['type']}: " + ' | '.join(i['description'] for i in v['items']))
    for p in rep.get('schematic_parity', []):
        bad.append(f"drc: parity {p['type']}: " + ' | '.join(i['description'] for i in p.get('items', [])))
    for u in rep.get('unconnected_items', []):
        bad.append('drc: unconnected ' + ' | '.join(i['description'] for i in u['items']))
    return bad, dict(unconnected=len(rep.get('unconnected_items', [])), deferred=deferred)


def gate_route(b):
    rc.set_profile('r9')
    inst = rc.scan(b, [])
    bumps, searched = rc.bump_audit(b)
    inst += bumps
    failures, allowed, stale = rc.evaluate(inst)
    _, missing, _ = rc.leftover_check(inst)
    issues = [f"route: {x['cat']} {x['net']} {x['layer']} ({x['x']}, {x['y']})" for x in failures]
    issues += [f"route: unrecorded leftover {x['cat']} {x['net']} {x['layer']} ({x['x']}, {x['y']})" for x in missing]
    issues += [f'route: allowlist entry {e[:4]}' for e in allowed + stale]
    gnd_info = sorted({x['cat'] for x in inst if x['net'] == 'GND'})
    pv = [f"{x['net']} ({x['x']}, {x['y']})" for x in inst if x['cat'] == 'power_via_no_gnd']
    return issues, dict(instances=len(inst), gnd_categories=gnd_info, power_via_no_gnd=pv, bump_windows=searched)


def pyro_copper(b):
    """{net: SHAPE_POLY_SET} of every PYRO1_ / ARM1_ net's copper (tracks, vias, pads, fills) on all layers, flattened."""
    out = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        if A.PYRO.match(n):
            for lid in A.CU4:
                if t.IsOnLayer(lid):
                    t.TransformShapeToPolygon(out.setdefault(n, pcbnew.SHAPE_POLY_SET()), lid, 0, A.ERR,
                                              pcbnew.ERROR_OUTSIDE)
    for f in b.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if A.PYRO.match(n):
                for lid in A.CU4:
                    if p.IsOnLayer(lid):
                        p.TransformShapeToPolygon(out.setdefault(n, pcbnew.SHAPE_POLY_SET()), lid, 0, A.ERR,
                                                  pcbnew.ERROR_OUTSIDE)
    for z in b.Zones():
        n = z.GetNetname()
        if not z.GetIsRuleArea() and A.PYRO.match(n):
            for lid in A.CU4:
                if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                    out.setdefault(n, pcbnew.SHAPE_POLY_SET()).BooleanAdd(A.fill(z, lid))
    return out


def gate_stitch(b, qs=None):
    """qs: the via centres judged (default: the table's vias)."""
    issues = []
    if qs is None:
        qs = [(r4(float(r['x0'])), r4(float(r['y0']))) for r in G.read() if r['item'] == 'via']
    r = G.VIA[0] / 2
    for q, net, layer in G.foreign_fill(b, qs):
        issues.append(f'stitch: via {q} inside the {net} {layer} fill')
    corr = A.corridor_boxes(b)
    excepted = []
    for z in b.Zones():
        n = z.GetNetname()
        if z.GetIsRuleArea() or n not in corr or not (z.IsOnLayer(A.IN2) and z.HasFilledPolysForLayer(A.IN2)):
            continue
        f = A.fill(z, A.IN2)
        box = A.rect(*corr[n])
        f.BooleanIntersection(box)
        for q in qs:
            if f.Collide(A.P(*q), MM(r + 0.3)):
                lifted = [k for k, (bx, _) in A.CORRIDOR_EXCEPT.items()
                          if n == 'RAW_ACT' and bx[0] <= q[0] <= bx[2] and bx[1] <= q[1] <= bx[3]]
                if lifted:
                    excepted.append((q, n, lifted[0]))
                    continue
                issues.append(f'stitch: via {q} cuts the In2 {n} region inside its 7.7 A corridor')
    near = {}
    for n, ps in pyro_copper(b).items():
        gap = ARMED_GAP if n in A.ARMED else PYRO_GAP
        for q in qs:
            if ps.Collide(A.P(*q), MM(r + gap - 0.001)):
                issues.append(f'stitch: via {q} within {gap} mm of {n} copper')
            d = ps.SquaredDistance(A.P(*q)) ** 0.5 / 1e6 - r if ps.OutlineCount() else 99.0
            near[n] = round(min(near.get(n, 99.0), d), 3)
    gnd = A.gnd_points(b)
    for q in qs:
        close = [p for p in gnd if 1e-6 < math.dist(p, q) < SPACING_MIN - 1e-6]
        if close:
            issues.append(f'stitch: via {q} {round(min(math.dist(p, q) for p in close), 3)} mm from a GND via')
    return issues, dict(vias=len(qs), nearest_pyro_copper=near, corridor_exceptions=excepted)


def islands(b):
    have = A.gnd_points(b)
    pours = A.outer_gnd(b)
    out = []
    for lid, name in ((A.F, 'F'), (A.B, 'B')):
        for one in A.islands(pours[lid]):
            n = sum(1 for q in have if A.in_island(one, q))
            bb = one.BBox()
            out.append(dict(layer=name, vias=n, area=round(one.Area() / 1e12, 2),
                            centre=(round(mm(bb.Centre().x), 2), round(mm(bb.Centre().y), 2)),
                            box=[round(mm(v), 2) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]))
    return out


def gate_islands(b):
    isl = islands(b)
    weak = [i for i in isl if i['vias'] < 2]
    issues, used = [], set()
    for i in weak:
        hit = [k for k, e in enumerate(WEAK_EXCEPT) if e[0] == i['layer'] and math.dist(e[1:3], i['centre']) <= 0.3]
        if not hit:
            issues.append(f"islands: {i['layer']}.Cu island {i['box']} ({i['area']} mm2) holds {i['vias']} GND via(s)")
            continue
        e = WEAK_EXCEPT[hit[0]]
        used.add(hit[0])
        if i['area'] > e[3] + 0.05 or i['vias'] < e[4]:
            issues.append(f"islands: {i['layer']}.Cu island {i['box']} grew past its recorded exception {e[:5]}")
    issues += [f'islands: stale exception {e[:5]}' for k, e in enumerate(WEAK_EXCEPT) if k not in used]
    return issues, dict(islands=len(isl), p7=len(weak), weak=weak, exceptions=len(WEAK_EXCEPT))


def pctl(vals, q):
    """survey_metrics.pctl (linear interpolation between the sorted values)."""
    s = sorted(vals)
    k = (len(s) - 1) * q
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def reach(b):
    near = A.Near(A.gnd_points(b))
    pts = A.board_points(b)
    d = sorted((near.dist(q), q) for q in pts)
    p95 = pctl([v for v, _ in d], 0.95)
    return dict(points=len(d), p95=round(p95, 2), max=round(d[-1][0], 2), max_at=d[-1][1],
                over_3p5=sum(1 for v, _ in d if v > 3.5))


def gate_reach(b):
    ev = reach(b)
    issues = []
    if ev['p95'] > P9_MAX:
        issues.append(f"reach: P9 p95 {ev['p95']} mm > {P9_MAX}")
    if ev['max'] > P10_MAX:
        issues.append(f"reach: P10 max {ev['max']} mm at {ev['max_at']} > {P10_MAX}")
    return issues, ev


def gate_copper(b):
    """Through-copper reach of the GND pads and the outer GND copper (the aid's reach_maps: 0.1 mm raster); the copper
    beyond COPPER_REACH as the aid's clusters (8-connected cells, a dead end's far part), each judged at its worst
    point."""
    maps = A.reach_maps(b)
    issues, pads, used_p, used_c = [], {}, set(), set()
    for name, pad, lid in A.reach_pads(b):
        d0 = A.pad_reach(maps, pad, lid)
        if d0 is not None and d0 <= 3.0:
            continue
        pads[name] = None if d0 is None else round(d0, 2)
        if d0 is not None and d0 <= A.PAD_REACH_ALL:
            continue
        hit = [k for k, e in enumerate(COPPER_PAD_EXCEPT) if e[0] == name]
        if hit and d0 is not None and d0 <= COPPER_PAD_EXCEPT[hit[0]][1] + 0.1:
            used_p.add(hit[0])
            continue
        issues.append(f'copper: GND pad {name} is {d0} mm of copper from a GND via (> {A.PAD_REACH_ALL})')
    pieces = []
    for lid, (r, copper, d) in maps.items():
        layer = 'F' if lid == A.F else 'B'
        for dk, k, cells in A.over_clusters(r, copper, d):
            at = tuple(r4(mm(v)) for v in r.centre(k))
            pieces.append(dict(layer=layer, at=at, mm=round(dk, 2), cells=len(cells)))
            hit = [i for i, e in enumerate(COPPER_EXCEPT) if e[0] == layer and A.cell(r, e[1:3]) in cells]
            if hit and dk <= COPPER_EXCEPT[hit[0]][3] + 0.1:
                used_c.add(hit[0])
                continue
            issues.append(f'copper: {layer}.Cu GND copper at {at} is {dk:.2f} mm of copper from a GND via '
                          f'(> {A.COPPER_REACH})')
    issues += [f'copper: stale pad exception {e[:2]}' for k, e in enumerate(COPPER_PAD_EXCEPT) if k not in used_p]
    issues += [f'copper: stale copper exception {e[:4]}' for k, e in enumerate(COPPER_EXCEPT) if k not in used_c]
    return issues, dict(pads_over_3mm=dict(sorted(pads.items())), clusters_over=pieces,
                        pad_limit=A.PAD_REACH_ALL, copper_limit=A.COPPER_REACH, raster=A.COPPER_RASTER)


def reference_sides(b, extended=False):
    """critical_reference's R6 samples (CR.samples; extended: its extended set, In1 / In2 tracks and the SWD, NRST and
    radio SPI nets too), the unreferenced ones grouped by their own via and side; samples beyond REF_OWN_R of every
    same-net via are listed apart (a keep-out, a split, another net's antipad)."""
    refs = CR.references(extended)
    nets = CR.R6_NETS + (CR.EXTENDED if extended else ())
    fills = CR.fills(b, refs)
    own = {}
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            own.setdefault(t.GetNetname(), []).append((r4(mm(t.GetPosition().x)), r4(mm(t.GetPosition().y))))
    sides, stray = {}, []
    for net, lay, x, y in CR.samples(b, nets, refs):
        if CR.inside(fills[lay], x, y):
            continue
        d, q = min(((math.dist((x, y), v), v) for v in own.get(net, [])), default=(99.0, None))
        if d <= REF_OWN_R:
            k = f'{net} {q} {pcbnew.LayerName(lay)}'
            sides[k] = sides.get(k, 0) + 1
        else:
            stray.append((net, pcbnew.LayerName(lay), x, y))
    return sides, stray


def gate_reference(b):
    rep = CR.compare(b, b, 0.0, False)
    n, tot = rep['candidate_unreferenced'], rep['candidate_samples']
    issues = [] if n <= REF_UNREF_MAX else [f'reference: {n} unreferenced critical samples > {REF_UNREF_MAX}']
    sides, stray = reference_sides(b)
    ext_sides, ext_stray = reference_sides(b, extended=True)
    used, loose = set(), []
    for s in sorted(set(stray) | set(ext_stray)):
        hit = [k for k, e in enumerate(REF_STRAY) if e[:2] == s[:2] and math.dist(e[2:4], s[2:4]) <= 0.01]
        if hit:
            used.add(hit[0])
        else:
            loose.append(s)
    if loose:
        issues.append(f'reference: {len(loose)} unreferenced samples outside their own via antipads (R6 or extended '
                      f'set), e.g. {loose[:3]}')
    issues += [f'reference: stale REF_STRAY entry {e[:4]}' for k, e in enumerate(REF_STRAY) if k not in used]
    return issues, dict(samples=tot, unreferenced=n, r6b=round(n / tot, 4) if tot else None, own_sides=sides,
                        outside_own=len(stray), extended_own=sum(ext_sides.values()), extended_outside_own=len(ext_stray),
                        recorded_stray=len(used))


def gate_contract(b, path, seed):
    only = {rid for rid, _, _ in C9.RULES} - CONTRACT_SKIP
    res = C9.check_board(b, path.parent, path, only=only, seed=seed,
                         board_sha=hashlib.sha256(path.read_bytes()).hexdigest())
    return res['issues'], {k: v['evidence'] for k, v in res['rules'].items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--report', type=Path)
    ap.add_argument('--seed', type=Path, help='a rule_h_seed.py report of this board')
    args = ap.parse_args()
    path = args.board.resolve()
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    seed = PC.run_seed(path, args.seed)
    board = pcbnew.LoadBoard(str(path))
    ctx = C9.Ctx(board, path.parent, path)
    report, fails = {}, {}

    def gate(name, result):
        issues, ev = result
        report[name] = dict(ok=not issues, issues=issues, evidence=ev)
        fails[name] = len(issues)
    gate('table', gate_table(board))
    gate('drc', gate_drc(path))
    gate('route', gate_route(board))
    gate('stitch', gate_stitch(board))
    gate('in2', PW.gate_in2(board))
    gate('xtal', gate_xtal(board))
    gate('islands', gate_islands(board))
    gate('reach', gate_reach(board))
    gate('copper', gate_copper(board))
    gate('reference', gate_reference(board))
    gate('pyro', PW.gate_pyro(board, ctx))
    gate('contract', gate_contract(board, path, seed))
    gate('actuators', PW.gate_actuators(path))
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name   # no local absolute paths (AGENTS.md)
    report.update(board=str(shown), board_sha256=sha,
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  table_sha256=hashlib.sha256(G.TABLE.read_bytes()).hexdigest())
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:25]:
            print('    ', i)
    print('reach', report['reach']['evidence'], 'P7', report['islands']['evidence']['p7'],
          'reference', report['reference']['evidence'])
    ok = not any(fails.values())
    print('R9 ground gate:', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
