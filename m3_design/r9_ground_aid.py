#!/usr/bin/env python3
"""Design aid (not in the build): generate m3_design/r9_ground.tsv, the R9 GND stitching (build step 8, D-S8-*).

usage: <KiCad python3> -I m3_design/r9_ground_aid.py BOARD OUT.tsv [--check]

BOARD is the step-7 board (r9_route.py links output) with m3.kicad_pro / m3.kicad_dru beside it; it is read, never
written. The aid grows the GND pours as r9_ground.py does (r9_ground.grow_pours), refills, and generates the rows in
the stages below, each on the board refilled after the stage before. --check: the table it generates must equal the
frozen m3_design/r9_ground.tsv byte for byte (the frozen table stays the source; r9_ground.py draws it). R8's
make_ground.py (sources/r8_design/step7) is the model; R9 differences are named.

Stages (row basis in brackets):
  return  [return NET]  a GND via within RETURN_REACH (1.5 mm, route_check GND_REACH) of every power-net layer change
          that has none (route_check power_via_no_gnd; AGENTS 3 asks it of critical signals, which step 7 already meets)
  pad     [pad REF.PIN] every GND SMD pad of an IC (a U part with four or more pads, forward of the strip) whose copper
          reaches a GND via or plated GND hole only beyond PAD_REACH (4 mm of copper) gets the legal spot its copper
          reaches soonest (R8 fix pass 2, D102: TI SLVSFC9C 8.4.1 asks for U9's GND tied to the plane at the IC)
  grid    [grid]  one GND via per node of a PITCH (4 mm, r9_plan step 8 / plan_spine section 9 step 8) lattice, at the
          legal spot nearest the node within SNAP, unless a GND via already lies within SERVED of it
  cover   [cover]  greedy: while a board point (0.5 mm raster inside the outline, survey_metrics' P9 / P10 points) lies
          more than COVER from every GND via or plated GND hole, the legal spot that brings most such points within
          COVER, while it brings at least MIN_GAIN; a spot may revive a removed GND island, and its via is dropped again
          when the island stage cannot give that island a second via
  island  [island F|B]  every outer GND pour island with fewer than two GND vias or plated GND holes gets them (P7),
          up to four rounds, with SPACING_ISLAND between GND vias and the RF strip's pockets open too (RF_GAP from RF
          copper, outside the launch windows; the strip's own stitching is step 4's, R-7)
  patch   [patch]  a second cover pass after the islands: radius PATCH_COVER, SPACING_ISLAND apart, any gain, reviving
          and dropping as the cover stage (the board points left beyond P9's 3.5 mm lie next to the power pours, where
          one via serves few points)
  finger  [finger F|B]  every GND pour finger route_check flags (a fill piece under 0.5 mm wide and over 3 mm long
          with a point more than 4 mm of copper from a GND via) gets the legal spot that serves it, if one exists
  strap   [strap REF.PIN]  each STRAPS pad gets a short octilinear GND track to a GND via, a STRAP_PADS_OK pad or a
          new legal via (a via row with the same basis)
  reach   [reach]  while P9 is above REACH_TARGET, the legal spot that brings most board points beyond 3.5 mm
          within it, even where it revives a removed GND island held by that via alone (P9 met at a P7 pocket's cost)
  copper  [copper pad REF.PIN, copper F|B]  last (R9 review pass 1, R9P1-PLANES-01 / -02; D-F1-07): P9 and the cover
          stages judge straight lines, so a via counts for copper it is not joined to. (a) Every GND SMD pad of a C,
          U, Q or J part forward of the strip whose copper reaches a GND via or plated GND hole only beyond
          PAD_REACH_ALL (5 mm of copper) gets the legal spot its copper reaches soonest; a pad of CORRIDOR_EXCEPT may
          use its recorded box, where its via cuts the RAW_ACT pours inside the 7.7 A corridor (C121.2, the servo bulk
          capacitor: the RAW_ACT solve is unchanged, D-F1-07). (b) While an outer GND copper point lies beyond
          COPPER_REACH (8 mm of copper) of every GND via, the worst cluster of such copper (8-connected raster cells,
          a dead end's far part) gets a via at the legal spot nearest its worst point along the copper, among the spots
          at least COPPER_MIN_GAIN of copper from every via; a cluster with no such spot is logged (r9_ground_check's
          copper gate lists it as a recorded exception). A copper-stage via goes only where it leaves no new island
          with fewer than two GND vias (place_safe: it must not revive a removed sliver or cut one off)
Every via is r9_ground.VIA (0.5 / 0.3 mm) and keeps >= SPACING (1.0 mm) from every GND via in the return, pad, grid and
cover stages, >= SPACING_ISLAND (0.6 mm) in the later ones.

A legal spot (legal()) is a via centre that, on every copper layer:
  - lies in an outer GND pour fill (F or B), >= EDGE from the outline, forward of STRIP_Y (the strip's GND vias are
    step 4's, R-7);
  - keeps the board rule plus MARGIN from every other net's track, via and pad (0.15 mm; RF nets 0.25; J30 / J31 pads
    0.30; bare test pads 1.0; J2 0.508; RAW_ACT through-hole pins 0.30); 0.75 mm (rule D plus its fill margin,
    D-S5-12, so Z1d keeps >= 0.2) from the copper and fills of the armed nets (bus, igniter, drain) and 0.5 mm from
    every other pyro / arming net's copper (R8 make_ground's practice);
  - keeps hole to hole and copper to hole 0.25 mm, 0.52 mm from Edge.Cuts circles, stays out of rule areas that
    forbid vias (the sensors' bodies, M-7) and off GND tracks;
  - stays off the body of every part with two to four pads (the convex hull of its pads);
  - is 0.3 mm (SMD) / 0.25 mm (through-hole) clear of GND pads, 0.1 mm from paste apertures and its hole 0.1 mm from
    SMD mask openings (check_r7 vias_in_smd_pads);
  - cuts no outer power pour (0.3 mm from every non-GND F / B fill), no In2 power region inside its 7.7 A corridor
    (the box round tools/run_dc.sh's terminal pads + 2 mm: RAW_ACT, BAT_IN, ACT_FET_S; its antipad reaching in from
    just outside the box included, D-S8-19), and puts no In2 antipad under
    a critical B.Cu track (route_check's critical signal classes and the survey's reference net sets) that runs over a
    non-GND In2 fill (its reference; R8 guarded every B.Cu track, D-S8-02);
  - cuts no narrow part of an In2 power region (its outline narrower than IN2_NARROW: the 3V3 finger up the spine),
    where an antipad would split it (the step-6 In2 gate: each region one piece);
  - revives no removed GND island on an outer layer (an island held by that one via), except in the island stage
    (which gives every island it revives a second via in a later round), the cover and patch passes (which drop such
    a via if its island stays under two) and the reach stage.
MARGIN is 0.05 mm, so every new via keeps >= 0.2 mm from foreign copper (scorecard Y1 / Y1b count pairs under 0.2).
legal(relax=BOX) lifts two of these rules inside BOX only, for RAW_ACT alone: the outer RAW_ACT pours' 0.3 mm and the
RAW_ACT In2 corridor (the copper stage's recorded CORRIDOR_EXCEPT).
"""
import argparse
import csv
import io
import heapq
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import r9_ground  # noqa: E402
import route_check as rc  # noqa: E402

TABLE = r9_ground.TABLE
mm, MM = pcbnew.ToMM, pcbnew.FromMM
F, IN1, IN2, B = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
CU4 = (F, IN1, IN2, B)
ERR = MM(0.005)

VIA = r9_ground.VIA
MARGIN = 0.05
EDGE = 0.8                    # mm, via centre to the outline: the DRU's 0.5 copper-edge clearance + 0.25 + MARGIN
STRIP_Y = 23.5                # the strip pours end at 23.0 (D-S4-07); the fence row is y 22.2 (R-7)
SPACING = 1.0                 # mm, GND via centre to GND via centre
SPACING_ISLAND = 0.6          # the island / patch / strap / reach stages': rings 0.1 mm apart, holes 0.3 mm (>= the
                              # project's 0.25 mm min_hole_to_hole): a pocket's second via
RF_GAP = 1.0                  # the island stage in the strip: mm from RF copper (step 4's GCPW field, R-5)
LAUNCH_X, LAUNCH_Y = 2.0, 4.6 # the jacks' launch windows (r9_rf_aid; R-4)
# The strap stage: GND SMD pads the pours leave with a starved thermal relief (DRC starved_thermal on the poured board,
# 1 spoke of the rule's 2: C17.2 boxed by C17.1, the 3V3 tap and USB_FAULT_N's via; C24.2 by NRST's C24.1 and the 3V3A
# feed); a strap (a track) to a GND via completes each (measured: with the straps DRC finds no starved_thermal, without
# them it finds these two; step 4's C301.2 precedent, D-S4-06)
STRAPS = ('C17.2', 'C24.2')
STRAP_PADS_OK = ()             # GND pads a strap may end on (none needed: each strap ends on a GND via)
STRAP_W = 0.3                  # mm (the board's 0.3 mm width; R5 pass 4's thermal spoke is 0.3 mm)
STRAP_GAP = 0.15               # mm to other-net copper (+ MARGIN)
STRAP_REACH = 1.6
STRAP_SEG = 0.25               # mm, the shortest strap segment (route_check short_segment / tiny_jog)
EPS2 = 1e-4
RETURN_REACH = 1.5            # route_check GND_REACH
PAD_REACH = 4.0               # mm of copper (R8 D102)
PAD_RASTER = 0.1
PITCH = 4.0                   # r9_plan step 8 (plan_spine section 9): a 4 mm GND grid
GRID_X0, GRID_Y0 = 3.0, 25.5  # columns 3, 7, ... 43; rows from 25.5 (the strip's grid ends at y 23)
SNAP = 1.0
SERVED = 2.0
COVER = 3.4                   # P9's 3.5 mm less a 0.1 mm margin
CAND_STEP = 0.1               # the cover stage's spot grid
RASTER = 0.5                  # survey_metrics' stitching raster
MIN_GAIN = 6
REACH_TARGET = 3.45            # mm: the reach stage's P9 target (the done row's 3.5 less 0.05)
PATCH_COVER = 3.45            # the patch pass: P9's 3.5 mm less 0.05
STEP = 0.05                   # spot search grid
ARMED = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
ARMED_GAP = 0.75              # rule D 0.5 + its fill margin (m3.kicad_dru "R9 fill margin D")
PYRO_GAP = 0.5
RF_NETS = ('GNSS_RF_ANT', 'GNSS_RF_IN', 'RADIO_RF_ANT', 'RADIO_RF')
PYRO = re.compile(r'^(PYRO1_|ARM1_)')
BARE = re.compile(r'^(TP\d+|J2)$')
IN2_NARROW = 2.5              # mm: an In2 power region narrower than this takes no GND via (its antipad would cut it)
REF_NETS = ('USB_DP', 'USB_DM', 'HSE_IN', 'HSE_OUT', 'QSPI_CLK', 'QSPI_NCS', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2',
            'QSPI_IO3', 'SPI1_SCK', 'SPI1_MOSI', 'SPI1_MISO', 'IMU_CS', 'SWDIO', 'SWCLK', 'NRST', 'RADIO_NSS',
            'RADIO_SCK', 'RADIO_SCK_MCU', 'RADIO_MOSI', 'RADIO_MOSI_MCU', 'RADIO_MISO', 'RADIO_MISO_MCU')
PAD_REACH_ALL = 5.0           # mm of copper: the copper stage's GND SMD pads of C / U / Q / J parts (R9P1-PLANES-01)
REACH_PARTS = re.compile(r'^(C|U|Q|J)\d+$')
COPPER_REACH = 8.0            # mm of copper: the copper stage's outer GND copper points (R9P1-PLANES-02)
COPPER_MIN_GAIN = 2.0         # mm of copper a copper-stage spot must lie from the vias (a spot nearer gains little)
COPPER_RASTER = 0.1           # mm, the copper stage's reach raster
COPPER_ROUNDS = 40           # the copper stage's cap (each round places one via or logs one cluster)
COPPER_TRIES = 60            # spots tried per via before the copper stage gives up on it (place_safe)
# Recorded exceptions to the corridor rules (D-F1-07): pad -> (box x0, y0, x1, y1 mm, reason). C121.2, the 470 uF servo
# bulk capacitor's GND pad, sat in a 60 mm2 F.Cu GND region with no legal GND via (R9P1-PLANES-01: 11.98 mOhm of return
# through a 0.37 mm neck): its east side, off the RAW_ACT path from Q121 to J122's RAW row, takes its via; the RAW_ACT
# solve is unchanged (0.79 mOhm, the neck at Q121), r9_ground_check's stitch gate allows the cut inside the box only
CORRIDOR_EXCEPT = {'C121.2': ((34.55, 61.3, 35.75, 64.85), "C121's GND return (D-F1-07)")}
CORRIDORS = {'BAT_IN': [('J1', {'1'}), ('Q120', {'5', '6', '7', '8', '9'})],          # tools/run_dc.sh terminals
             'RAW_ACT': [('Q121', {'5', '6', '7', '8', '9'}), ('J122', {'2', '5', '8', '11'})],
             'ACT_FET_S': [('Q120', {'1', '2', '3'}), ('Q121', {'1', '2', '3'})]}


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def r4(v):
    return round(v + 0.0, 4)


def rect(x0, y0, x1, y1):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        s.Append(MM(x), MM(y))
    return s


def fill(z, lid):
    f = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid))
    f.Unfracture()
    return f


def board_box(b):
    """The outline polygon's box (survey_metrics.inventory's bbox; not the edge drawings' box, which adds their width)."""
    o = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(o, False)
    bb = o.BBox()
    return mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())


def clearance(net, pad=None):
    """Rule (mm) between a new GND via and other-net copper, plus MARGIN."""
    c = 0.15
    if net in RF_NETS:
        c = 0.25
    if PYRO.match(net or ''):
        c = PYRO_GAP
    if net in ARMED:
        c = ARMED_GAP
    if pad is not None:
        ref = pad.GetParentFootprint().GetReference()
        if ref in ('J30', 'J31'):
            c = max(c, 0.30)
        if ref.startswith('TP'):
            c = max(c, 1.0)
        if ref == 'J2':
            c = max(c, 0.508)
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and net == 'RAW_ACT':
            c = max(c, 0.3)
    return c + MARGIN


def circle(p, radius, out):
    pcbnew.SHAPE_CIRCLE(p, MM(radius)).TransformToPolygon(out, ERR, pcbnew.ERROR_OUTSIDE)


def refill(b):
    for z in b.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    b.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    b.BuildConnectivity()


def outer_gnd(b):
    out = {}
    for lid in (F, B):
        ps = pcbnew.SHAPE_POLY_SET()
        for z in b.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                ps.BooleanAdd(fill(z, lid))
        out[lid] = ps
    return out


def dormant(b):
    """{layer: SHAPE_POLY_SET} of the outer GND pours' removed islands (what a fill that kept islands would add)."""
    zones = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND']
    before = outer_gnd(b)
    modes = [z.GetIslandRemovalMode() for z in zones]
    for z in zones:
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    refill(b)
    kept = outer_gnd(b)
    for z, m in zip(zones, modes):
        z.SetIslandRemovalMode(m)
    refill(b)
    after = outer_gnd(b)
    out = {}
    for lid in (F, B):
        assert abs(before[lid].Area() - after[lid].Area()) < 1e6, 'a refill changed the outer GND fill'
        extra = pcbnew.SHAPE_POLY_SET(kept[lid])
        extra.BooleanSubtract(after[lid])
        out[lid] = extra
    return out


def small_body(f):
    """The convex hull of the copper pads of a part with two to four of them; None for other parts."""
    pads = [p for p in f.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
    if not 2 <= len(pads) <= 4:
        return None
    pts = set()
    for p in pads:
        lid = F if p.IsOnLayer(F) else B
        ps = pcbnew.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(ps, lid, 0, ERR, pcbnew.ERROR_OUTSIDE)
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i)
            pts.update((o.CPoint(k).x, o.CPoint(k).y) for k in range(o.PointCount()))
    pts = sorted(pts)

    def cross(o, a, c):
        return (a[0] - o[0]) * (c[1] - o[1]) - (a[1] - o[1]) * (c[0] - o[0])
    lo, hi = [], []
    for q in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], q) <= 0:
            hi.pop()
        hi.append(q)
    hull = pcbnew.SHAPE_POLY_SET()
    hull.NewOutline()
    for x, y in lo[:-1] + hi[:-1]:
        hull.Append(int(x), int(y))
    return hull


def corridor_boxes(b):
    out = {}
    for net, ends in CORRIDORS.items():
        xs, ys = [], []
        for ref, pins in ends:
            for p in b.FindFootprintByReference(ref).Pads():
                if p.GetNumber() in pins:
                    xs.append(mm(p.GetPosition().x))
                    ys.append(mm(p.GetPosition().y))
        out[net] = (min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2)
    return out


def referenced(net):
    """Nets whose B.Cu tracks keep their In2 reference free of new antipads: route_check's critical signal classes and
    the survey's reference sets (survey_metrics R6_NETS / EXT_NETS: the R6b and extended critical-reference rows)."""
    return net in REF_NETS or rc.net_class(net) in rc.SIGNAL_CRITICAL


def legal(b, revive=False, spacing=SPACING, strip=False, relax=None):
    """SHAPE_POLY_SET of the legal centres of a new VIA GND via (module docstring); spacing: from every GND via;
    strip: the island stage may also stitch the RF strip's pockets (y >= EDGE), RF_GAP from RF copper and outside the
    launch windows; relax: a box (mm) inside which the RAW_ACT pours' outer 0.3 mm and the RAW_ACT In2 corridor do
    not forbid (CORRIDOR_EXCEPT)."""
    lifted = rect(*relax) if relax else None
    r = VIA[0] / 2
    hole = VIA[1] / 2
    sleeping = {F: pcbnew.SHAPE_POLY_SET(), B: pcbnew.SHAPE_POLY_SET()} if revive else dormant(b)
    forbid = pcbnew.SHAPE_POLY_SET()
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            if n == 'GND':
                circle(t.GetPosition(), spacing, forbid)
            else:
                for lid in CU4:
                    t.TransformShapeToPolygon(forbid, lid, MM(clearance(n) + r), ERR, pcbnew.ERROR_OUTSIDE)
            circle(t.GetPosition(), mm(t.GetDrillValue()) / 2 + 0.25 + hole + MARGIN, forbid)
        elif n == 'GND':
            t.TransformShapeToPolygon(forbid, t.GetLayer(), MM(r + 0.05), ERR, pcbnew.ERROR_OUTSIDE)
        else:
            t.TransformShapeToPolygon(forbid, t.GetLayer(), MM(clearance(n) + r), ERR, pcbnew.ERROR_OUTSIDE)
    for f in b.GetFootprints():
        ref = f.GetReference()
        body = small_body(f)
        if body is not None:
            body.Inflate(MM(r + MARGIN), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
            forbid.BooleanAdd(body)
        for p in f.Pads():
            n = p.GetNetname()
            att = p.GetAttribute()
            for lid in CU4:
                if not p.IsOnLayer(lid) or att == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                if n == 'GND':
                    c = 0.3 if att == pcbnew.PAD_ATTRIB_SMD else 0.25
                else:
                    c = clearance(n, p)
                p.TransformShapeToPolygon(forbid, lid, MM(c + r), ERR, pcbnew.ERROR_OUTSIDE)
            for lid in (pcbnew.F_Paste, pcbnew.B_Paste):
                if p.IsOnLayer(lid):
                    p.TransformShapeToPolygon(forbid, lid, MM(0.1 + r + MARGIN), ERR, pcbnew.ERROR_OUTSIDE)
            if att in (pcbnew.PAD_ATTRIB_SMD, pcbnew.PAD_ATTRIB_CONN) and not BARE.match(ref):
                for cu, mk in ((F, pcbnew.F_Mask), (B, pcbnew.B_Mask)):
                    if p.IsOnLayer(cu) and p.IsOnLayer(mk):
                        grow = max(0.0, mm(p.GetSolderMaskExpansion(mk))) + 0.1 + hole + MARGIN
                        p.TransformShapeToPolygon(forbid, cu, MM(grow), ERR, pcbnew.ERROR_OUTSIDE)
            if att in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                circle(p.GetPosition(), mm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2 + 0.25 + r + MARGIN,
                       forbid)
    in2_power = pcbnew.SHAPE_POLY_SET()
    for z in b.Zones():
        if z.GetIsRuleArea():
            if z.GetDoNotAllowVias():
                o = pcbnew.SHAPE_POLY_SET(z.Outline())
                o.Inflate(MM(r + MARGIN), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
                forbid.BooleanAdd(o)
            continue
        n = z.GetNetname()
        for lid in CU4:
            if not (z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid)) or n == 'GND':
                continue
            if lid == IN2:
                in2_power.BooleanAdd(fill(z, lid))
            grow = ARMED_GAP if n in ARMED else PYRO_GAP if PYRO.match(n) else 0.3 if lid in (F, B) else None
            if grow is None:
                continue
            fp = fill(z, lid)
            fp.Inflate(MM(grow + r + MARGIN), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
            if lifted is not None and n == 'RAW_ACT':
                fp.BooleanSubtract(lifted)
            forbid.BooleanAdd(fp)
    for net, box in corridor_boxes(b).items():
        corridor = rect(*box)
        for z in b.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() == net and z.IsOnLayer(IN2) and z.HasFilledPolysForLayer(IN2):
                fp = fill(z, IN2)
                inside = pcbnew.SHAPE_POLY_SET(fp)
                fp.Inflate(MM(0.3 + r + MARGIN), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
                fp.BooleanIntersection(corridor)
                # and no antipad reaching into the corridor from just outside it (r9_ground_check's stitch gate tests
                # the via's circle against the region's fill inside the corridor; D-S8-19)
                inside.BooleanIntersection(corridor)
                inside.Inflate(MM(0.3 + r + MARGIN), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
                if lifted is not None and net == 'RAW_ACT':
                    fp.BooleanSubtract(lifted)
                    inside.BooleanSubtract(lifted)
                forbid.BooleanAdd(fp)
                forbid.BooleanAdd(inside)
    # an In2 power region's narrow parts (its outline narrower than IN2_NARROW: the 3V3 finger) take no antipad
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() != 'GND' and z.IsOnLayer(IN2) and z.HasFilledPolysForLayer(IN2):
            fp = pcbnew.SHAPE_POLY_SET(z.Outline())        # the region's own shape (step 6's outline), not its holes
            opened = pcbnew.SHAPE_POLY_SET(fp)
            opened.Deflate(MM(IN2_NARROW / 2), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
            opened.Inflate(MM(IN2_NARROW / 2 + 0.01), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
            fp.BooleanSubtract(opened)
            fp.Inflate(MM(r + 0.3 + MARGIN), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
            forbid.BooleanAdd(fp)
    guard = pcbnew.SHAPE_POLY_SET()
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA' and t.GetLayer() == B and referenced(t.GetNetname()):
            t.TransformShapeToPolygon(guard, B, MM(0.3 + r + MARGIN), ERR, pcbnew.ERROR_OUTSIDE)
    in2_power.Inflate(MM(r + 0.3), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
    guard.BooleanIntersection(in2_power)
    forbid.BooleanAdd(guard)
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            circle(d.GetCenter(), mm(d.GetRadius()) + 0.52 + r, forbid)
    allow = pcbnew.SHAPE_POLY_SET()
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == 'GND':
            for lid in (F, B):
                if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                    allow.BooleanAdd(fill(z, lid))
    x0, y0, x1, y1 = board_box(b)
    allow.BooleanIntersection(rect(x0 + EDGE, y0 + EDGE if strip else STRIP_Y, x1 - EDGE, y1 - EDGE))
    if strip:
        for t in b.GetTracks():
            if t.GetNetname() in RF_NETS:
                for lid in CU4:
                    if t.IsOnLayer(lid):
                        t.TransformShapeToPolygon(forbid, lid, MM(RF_GAP + r), ERR, pcbnew.ERROR_OUTSIDE)
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetname() in RF_NETS:
                    for lid in CU4:
                        if p.IsOnLayer(lid):
                            p.TransformShapeToPolygon(forbid, lid, MM(RF_GAP + r), ERR, pcbnew.ERROR_OUTSIDE)
        for z in b.Zones():
            if z.GetIsRuleArea() and z.GetZoneName().endswith('_launch_In1'):
                bb = z.GetBoundingBox()
                cx = mm(bb.Centre().x)
                forbid.BooleanAdd(rect(cx - LAUNCH_X - r, -1.0, cx + LAUNCH_X + r, LAUNCH_Y + r))
    for lid in (F, B):
        sl = sleeping[lid]
        sl.Inflate(MM(r), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
        forbid.BooleanAdd(sl)
    allow.BooleanSubtract(forbid)
    return allow


class Spots:
    """The legal region less the spacing round every via placed so far."""

    def __init__(self, b, revive=False, spacing=SPACING, strip=False, relax=None):
        self.region = legal(b, revive, spacing, strip, relax)
        self.spacing = spacing
        self.placed = []

    def ok(self, q):
        return self.region.Contains(P(*q)) and all(math.dist(q, v) >= self.spacing - 1e-9 for v in self.placed)

    def nearest(self, q, reach, inside=None):
        """The legal spot on the STEP grid round q nearest it within reach (ties: lower y, then lower x)."""
        n = int(round(reach / STEP))
        cand = sorted((math.hypot(i, j) * STEP, r4(q[1] + j * STEP), r4(q[0] + i * STEP))
                      for j in range(-n, n + 1) for i in range(-n, n + 1) if math.hypot(i, j) * STEP <= reach + 1e-9)
        for _, y, x in cand:
            if (inside is None or inside.Contains(P(x, y))) and self.ok((x, y)):
                return (x, y)
        return None

    def add(self, q):
        self.placed.append(q)


def gnd_points(b):
    pts = [(mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in b.GetTracks()
           if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    pts += [(mm(p.GetPosition().x), mm(p.GetPosition().y)) for f in b.GetFootprints() for p in f.Pads()
            if p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    return pts


class Near:
    """Nearest-point queries over a growing point set (bucket grid)."""

    def __init__(self, pts, cell=2.0):
        self.cell = cell
        self.bk = defaultdict(list)
        for p in pts:
            self.add(p)

    def add(self, p):
        self.bk[(int(p[0] // self.cell), int(p[1] // self.cell))].append(p)

    def dist(self, q, cap=60.0):
        ci, cj = int(q[0] // self.cell), int(q[1] // self.cell)
        best, ring = math.inf, 0
        while ring * self.cell <= cap + self.cell:
            for di in range(-ring, ring + 1):
                for dj in range(-ring, ring + 1):
                    if max(abs(di), abs(dj)) == ring:
                        for p in self.bk.get((ci + di, cj + dj), ()):
                            best = min(best, math.dist(p, q))
            if best <= ring * self.cell:
                return best
            ring += 1
        return best


def islands(ps):
    out = []
    for i in range(ps.OutlineCount()):
        one = pcbnew.SHAPE_POLY_SET()
        one.AddOutline(ps.Outline(i))
        for j in range(ps.HoleCount(i)):
            one.AddHole(ps.Hole(i, j))
        out.append(one)
    return out


def in_island(one, q):
    return one.Collide(P(*q), MM(0.15))          # survey_metrics' P7 test


def power_layer_changes(b):
    """Vias of power nets (route_check class 'power', GND excepted) whose net has tracks on two or more of the via's
    layers ending at it: route_check's power_via_no_gnd population."""
    out = []
    tracks = defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA':
            tracks[t.GetNetname()].append(t)
    for v in b.GetTracks():
        n = v.GetNetname()
        if v.GetClass() != 'PCB_VIA' or n == 'GND' or rc.net_class(n) != 'power':
            continue
        p = v.GetPosition()
        rad = v.GetWidth(F) / 2
        layers = {t.GetLayer() for t in tracks[n]
                  if min(math.hypot(e.x - p.x, e.y - p.y) for e in (t.GetStart(), t.GetEnd())) <= rad}
        if len(layers) >= 2:
            out.append((n, (r4(mm(p.x)), r4(mm(p.y)))))
    return sorted(out, key=lambda t: (t[1][1], t[1][0], t[0]))


def draw_vias(b, qs):
    gnd = b.FindNet('GND')
    for q in qs:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(P(*q))
        v.SetWidth(MM(VIA[0]))
        v.SetDrill(MM(VIA[1]))
        v.SetLayerPair(F, B)
        v.SetNet(gnd)
        b.Add(v)


def weak_islands(b):
    """[(layer name, island)] of the outer GND pour islands with fewer than two GND vias / plated GND holes (P7)."""
    have = gnd_points(b)
    pours = outer_gnd(b)
    out = []
    for lid, name in ((F, 'F'), (B, 'B')):
        for one in islands(pours[lid]):
            if sum(1 for q in have if in_island(one, q)) < 2:
                out.append((name, one))
    return out


def board_points(b):
    """The 0.5 mm raster points inside the outline (survey_metrics.stitching)."""
    o = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(o, False)
    x0, y0, x1, y1 = board_box(b)
    pts = []
    y = y0 + RASTER / 2
    while y < y1:
        x = x0 + RASTER / 2
        while x < x1:
            if o.Contains(P(x, y)):
                pts.append((r4(x), r4(y)))
            x += RASTER
        y += RASTER
    return pts


def ic_gnd_pads(b):
    out = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        if not re.match(r'^U\d+$', ref) or len(f.Pads()) < 4:
            continue
        for p in f.Pads():
            if p.GetNetname() != 'GND' or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            if mm(p.GetPosition().y) < STRIP_Y:
                continue
            out.append((f'{ref}.{p.GetNumber()}', p, F if p.IsOnLayer(F) else B))
    return sorted(out, key=lambda t: (t[0].split('.')[0], t[0]))


def copper_reach(b, lid, src, win, limit, extra=()):
    """(raster, distance array): through-copper distance from the source polygons over the layer's GND copper (with the
    extra via centres added as copper and stitching), the window win (mm), out to limit; and the stitching cells."""
    r = rc.Raster(tuple(v / rc.NM for v in win), PAD_RASTER / rc.NM)
    cop, stitch = rc.net_copper(b, 'GND', lid)
    for q in extra:
        ps = pcbnew.SHAPE_POLY_SET()
        circle(P(*q), VIA[0] / 2, ps)
        cop.append(ps)
        stitch.append(ps)
    copper = r.fill(cop)
    d = rc.reach(r, copper, r.fill(src), limit)
    return r, d, r.fill(stitch)


def cell(r, q):
    ci = int((q[0] / rc.NM - r.x0) // r.step)
    cj = int((q[1] / rc.NM - r.y0) // r.step)
    return cj * r.nx + ci if 0 <= ci < r.nx and 0 <= cj < r.ny else None


def pad_returns(b, sp, via_row, log=print):
    new = []
    for name, pad, lid in ic_gnd_pads(b):
        c = (mm(pad.GetPosition().x), mm(pad.GetPosition().y))
        w = PAD_REACH + 1.5
        src = pcbnew.SHAPE_POLY_SET()
        pad.TransformShapeToPolygon(src, lid, 0, ERR, pcbnew.ERROR_INSIDE)
        r, d, st = copper_reach(b, lid, [src], (c[0] - w, c[1] - w, c[0] + w, c[1] + w), PAD_REACH + 1.0, new)
        d0 = min((d[k] for k in range(r.nx * r.ny) if st[k] and d[k] >= 0), default=None)
        if d0 is not None and d0 <= PAD_REACH:
            continue
        n = int(round(PAD_REACH / STEP))
        best = None
        for j in range(-n, n + 1):
            for i in range(-n, n + 1):
                q = (r4(c[0] + i * STEP), r4(c[1] + j * STEP))
                if math.dist(q, c) > PAD_REACH + 1e-9 or not sp.ok(q):
                    continue
                k = cell(r, q)
                if k is None or d[k] < 0 or d[k] > PAD_REACH:
                    continue
                key = (round(d[k], 6), q[1], q[0])
                if best is None or key < best[0]:
                    best = (key, q)
        if best is None:
            log(f'  pad: {name} ({c[0]:.2f}, {c[1]:.2f}) beyond {PAD_REACH} mm of copper; no legal spot')
            continue
        sp.add(best[1])
        new.append(best[1])
        via_row(best[1], f'pad {name}')
    return new


def finger_returns(b, sp, via_row, log=print):
    """A via for each failing GND pour finger (route_check.pour_pieces): the legal spot within FINGER_REACH of the
    finger that leaves the fewest of its cells beyond reach (zero required), nearest the finger's far point."""
    new = []
    for pc in rc.pour_pieces(b):
        if pc['cat'] != 'pour_finger':
            continue
        lid = pc['lid']
        box = [mm(v) for v in pc['box']]
        m = rc.FINGER_REACH + 0.5
        win = (box[0] - m, box[1] - m, box[2] + m, box[3] + m)
        name = 'F' if lid == F else 'B'
        best = None
        x = win[0] + STEP / 2
        cands = []
        while x < win[2]:
            y = win[1] + STEP / 2
            while y < win[3]:
                q = (r4(x), r4(y))
                if sp.ok(q):
                    cands.append(q)
                y += 4 * STEP
            x += 4 * STEP
        far = pc['at']
        cands.sort(key=lambda q: (math.dist(q, far), q[1], q[0]))
        for q in cands[:400]:
            r = rc.Raster(tuple(v / rc.NM for v in win), rc.RASTER / rc.NM)
            cop, stitch = rc.net_copper(b, 'GND', lid)
            ps = pcbnew.SHAPE_POLY_SET()
            circle(P(*q), VIA[0] / 2, ps)
            cop.append(ps)
            stitch.append(ps)
            for v in new:
                ps2 = pcbnew.SHAPE_POLY_SET()
                circle(P(*v), VIA[0] / 2, ps2)
                cop.append(ps2)
                stitch.append(ps2)
            copper = r.fill(cop)
            d = rc.reach(r, copper, r.fill(stitch), rc.FINGER_REACH)
            tgt = r.fill([pc['poly']])
            beyond = sum(1 for k in range(r.nx * r.ny) if tgt[k] and copper[k] and d[k] < 0)
            if beyond == 0:
                best = q
                break
        if best is None:
            log(f'  finger {name}.Cu at {pc["at"]} ({pc["len_mm"]} mm): no legal spot serves it')
            continue
        sp.add(best)
        new.append(best)
        via_row(best, f'finger {name}')
    return new


def cover(b, sp, near, radius=None, min_gain=None):
    """The cover stage (module docstring): lazy greedy over the legal spots on a CAND_STEP grid; a spot's gain is the
    number of board points within COVER of it that lie farther than COVER from every GND via / plated hole so far
    (gains only fall as vias are added, so a popped spot whose fresh gain still tops the heap is the greedy choice)."""
    COVER_, MIN_GAIN_ = radius or COVER, min_gain or MIN_GAIN
    pts = [q for q in board_points(b) if near.dist(q, COVER_ + 1) > COVER_]
    bad = set(pts)
    bk = defaultdict(list)
    for q in pts:
        bk[(int(q[0] // COVER_), int(q[1] // COVER_))].append(q)

    def gain(c):
        ci, cj = int(c[0] // COVER_), int(c[1] // COVER_)
        return sum(1 for di in (-1, 0, 1) for dj in (-1, 0, 1) for q in bk.get((ci + di, cj + dj), ())
                   if q in bad and math.dist(q, c) <= COVER_)
    x0, y0, x1, y1 = board_box(b)
    ras = rc.Raster((x0 / rc.NM, STRIP_Y / rc.NM, x1 / rc.NM, y1 / rc.NM), CAND_STEP / rc.NM)
    grid = ras.fill([sp.region])
    heap = []
    for k in range(ras.nx * ras.ny):
        if grid[k]:
            c = tuple(r4(mm(v)) for v in ras.centre(k))
            g = gain(c)
            if g >= MIN_GAIN_:
                heap.append((-g, c[1], c[0]))
    heapq.heapify(heap)
    out = []
    while heap:
        g0, y, x = heapq.heappop(heap)
        c = (x, y)
        if not sp.ok(c):
            continue
        g = gain(c)
        if g < MIN_GAIN_:
            continue
        if heap and -heap[0][0] > g:
            heapq.heappush(heap, (-g, y, x))
            continue
        out.append(c)
        sp.add(c)
        near.add(c)
        for q in [q for q in bad if math.dist(q, c) <= COVER_]:
            bad.discard(q)
    return out


def reach_pads(b):
    """[(name, pad, layer)]: the GND SMD pads of C / U / Q / J parts forward of the strip (the copper stage, its gate)."""
    out = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        if not REACH_PARTS.match(ref):
            continue
        for p in f.Pads():
            if p.GetNetname() != 'GND' or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or mm(p.GetPosition().y) < STRIP_Y:
                continue
            out.append((f'{ref}.{p.GetNumber()}', p, F if p.IsOnLayer(F) else B))
    return sorted(out, key=lambda t: t[0])


def reach_maps(b, step=COPPER_RASTER, limit=80.0):
    """{layer: (raster, copper, distance)} over the board forward of the strip: each outer layer's GND copper and its
    through-copper distance (mm) to the nearest GND via or plated GND hole (-1: copper no via reaches within limit)."""
    x0, _, x1, y1 = board_box(b)
    out = {}
    for lid in (F, B):
        r = rc.Raster((x0 / rc.NM, STRIP_Y / rc.NM, x1 / rc.NM, y1 / rc.NM), step / rc.NM)
        cop, stitch = rc.net_copper(b, 'GND', lid)
        copper = r.fill(cop)
        out[lid] = (r, copper, rc.reach(r, copper, r.fill(stitch), limit))
    return out


def over_clusters(r, copper, d, limit=COPPER_REACH):
    """The copper beyond `limit` mm of copper from every GND via or plated GND hole, as 8-connected clusters of raster
    cells (each a dead end's far part; one copper piece may hold several): [(worst mm, worst cell, frozenset of cells)],
    worst first. Copper no via reaches within reach_maps' limit (-1) is not counted (raster-disconnected slivers; dead
    copper is route_check's)."""
    n = r.nx * r.ny
    over = bytearray(n)
    for k in range(n):
        if copper[k] and d[k] > limit:
            over[k] = 1
    seen = bytearray(n)
    out = []
    for k0 in range(n):
        if not over[k0] or seen[k0]:
            continue
        seen[k0] = 1
        todo, cells = [k0], []
        while todo:
            k = todo.pop()
            cells.append(k)
            i, j = k % r.nx, k // r.nx
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    a, c = i + di, j + dj
                    if 0 <= a < r.nx and 0 <= c < r.ny:
                        q = c * r.nx + a
                        if over[q] and not seen[q]:
                            seen[q] = 1
                            todo.append(q)
        worst = max(cells, key=lambda q: (d[q], -q))
        out.append((d[worst], worst, frozenset(cells)))
    return sorted(out, key=lambda t: (-t[0], t[1]))


def pad_reach(maps, pad, lid):
    """Through-copper distance (mm) from the pad to the nearest GND via or plated GND hole (None: none reaches it)."""
    r, copper, d = maps[lid]
    src = pcbnew.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(src, lid, 0, ERR, pcbnew.ERROR_INSIDE)
    cells = r.fill([src])
    vals = [d[k] for k in range(r.nx * r.ny) if cells[k] and copper[k] and d[k] >= 0]
    return min(vals) if vals else None


def weak_keys(b):
    """[(layer, centre x, centre y)] of the weak islands (weak_islands), for before / after comparisons."""
    return [(n, mm(one.BBox().Centre().x), mm(one.BBox().Centre().y)) for n, one in weak_islands(b)]


def place_safe(b, cands, log=print, tries=COPPER_TRIES):
    """Draw the first spot of cands (in order) whose via leaves no new weak island (P7: an island with fewer than two
    GND vias that the board did not have, as a via that revives a removed island or cuts a sliver off does), refilled;
    returns it, or None. A rejected spot's via is removed and the board refilled."""
    before = weak_keys(b)
    for q in cands[:tries]:
        draw_vias(b, [q])
        refill(b)
        new = [w for w in weak_keys(b) if not any(w[0] == o[0] and math.dist(w[1:], o[1:]) <= 0.3 for o in before)]
        if not new:
            return q
        for v in list(b.GetTracks()):
            if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND' and v.GetPosition() == P(*q):
                b.Remove(v)
        refill(b)
        log(f'  copper: spot {q} would leave a new weak {new[0][0]}.Cu island at ({new[0][1]:.2f}, {new[0][2]:.2f}): '
            f'next spot')
    return None


def copper_stage(b, via_row, log=print):
    """The copper stage (module docstring): (a) the reach pads beyond PAD_REACH_ALL, (b) the copper beyond COPPER_REACH.
    Draws its vias (board refilled after each); returns them."""
    added = []
    maps = reach_maps(b)
    for name, pad, lid in reach_pads(b):
        d0 = pad_reach(maps, pad, lid)
        if d0 is not None and d0 <= PAD_REACH_ALL:
            continue
        relax = CORRIDOR_EXCEPT.get(name, (None,))[0]
        sp = Spots(b, spacing=SPACING_ISLAND, relax=relax)
        c = (mm(pad.GetPosition().x), mm(pad.GetPosition().y))
        w = PAD_REACH_ALL + 1.5
        src = pcbnew.SHAPE_POLY_SET()
        pad.TransformShapeToPolygon(src, lid, 0, ERR, pcbnew.ERROR_INSIDE)
        r, d, _ = copper_reach(b, lid, [src], (c[0] - w, c[1] - w, c[0] + w, c[1] + w), PAD_REACH_ALL + 1.0)
        n = int(round(PAD_REACH_ALL / STEP))
        cand = []
        for j in range(-n, n + 1):
            for i in range(-n, n + 1):
                q = (r4(c[0] + i * STEP), r4(c[1] + j * STEP))
                if math.dist(q, c) > PAD_REACH_ALL + 1e-9 or not sp.ok(q):
                    continue
                k = cell(r, q)
                if k is None or d[k] < 0 or d[k] > PAD_REACH_ALL:
                    continue
                cand.append(((round(d[k], 6), q[1], q[0]), q))
        q = place_safe(b, [q for _, q in sorted(cand)], log)
        if q is None:
            log(f'  copper: pad {name} ({c[0]:.2f}, {c[1]:.2f}) {d0:.2f} mm of copper; no legal spot')
            continue
        via_row(q, f'copper pad {name}')
        added.append(q)
        log(f'  copper: pad {name} {d0:.2f} mm -> via {q}')
        maps = reach_maps(b)
    # (b) the worst cluster of copper beyond COPPER_REACH first: the legal spot nearest (along the copper) to its worst
    # point that lies at least COPPER_MIN_GAIN of copper from every via, among the copper that point reaches within its
    # own distance to a via (a spot farther off along the copper serves it no better than the via already there)
    logged = {F: set(), B: set()}                  # cells of clusters no spot serves (r9_ground_check's exceptions)
    for _ in range(COPPER_ROUNDS):
        worst = None
        for lid, (r, copper, d) in maps.items():
            for dk, k, cells in over_clusters(r, copper, d):
                if cells & logged[lid]:
                    continue
                if worst is None or dk > worst[0] + 1e-9:
                    worst = (dk, lid, k, cells)
                break
        if worst is None:
            break
        dk, lid, k, cells = worst
        r, copper, d = maps[lid]
        at = tuple(r4(mm(v)) for v in r.centre(k))
        seed = bytearray(r.nx * r.ny)
        seed[k] = 1
        dw = rc.reach(r, copper, seed, dk)
        relax = None
        for name, (box, _) in sorted(CORRIDOR_EXCEPT.items()):
            pad = next((p for n2, p, l2 in reach_pads(b) if n2 == name and l2 == lid), None)
            kp = cell(r, (mm(pad.GetPosition().x), mm(pad.GetPosition().y))) if pad is not None else None
            if kp is not None and dw[kp] >= 0:
                relax = box
        sp = Spots(b, spacing=SPACING_ISLAND, relax=relax)
        # candidates on the STEP lattice (the spot searches' grid; a legal area can be smaller than a raster cell), in
        # the copper cells the worst point reaches with at least COPPER_MIN_GAIN to every via, nearest along the copper
        # first
        cand = []
        st = mm(r.step)
        sub = int(round(st / STEP))
        for q in range(r.nx * r.ny):
            if copper[q] and dw[q] >= 0 and d[q] >= COPPER_MIN_GAIN:
                cx, cy = (mm(v) for v in r.centre(q))
                for i in range(sub):
                    for j in range(sub):
                        c = (r4(cx - st / 2 + i * STEP), r4(cy - st / 2 + j * STEP))     # multiples of STEP
                        cand.append((round(dw[q], 6), c[1], c[0], c))
        cand.sort()
        along = {key[3]: key[0] for key in cand}
        q = place_safe(b, [key[3] for key in cand if sp.ok(key[3])], log)
        layer = 'F' if lid == F else 'B'
        if q is None:
            log(f'  copper: {layer}.Cu cluster at {at}, {dk:.2f} mm of copper from a GND via: no legal spot '
                f'{COPPER_MIN_GAIN} mm out within its reach')
            logged[lid] |= cells
            continue
        via_row(q, f'copper {layer}')
        added.append(q)
        log(f'  copper: {layer}.Cu {dk:.2f} mm at {at} -> via {q} ({along[q]:.2f} mm along the copper)')
        maps = reach_maps(b)
    else:
        raise SystemExit(f'copper stage: still copper beyond {COPPER_REACH} mm after {COPPER_ROUNDS} rounds')
    return added


def draw_track(b, layer, w, a, c):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(P(*a))
    t.SetEnd(P(*c))
    t.SetWidth(MM(w))
    t.SetLayer(F if layer == 'F' else B)
    t.SetNet(b.FindNet('GND'))
    b.Add(t)


def foreign(b, lid):
    """SHAPE_POLY_SET of every non-GND copper item and fill on layer lid (a strap keeps STRAP_GAP from it)."""
    ps = pcbnew.SHAPE_POLY_SET()
    for t in b.GetTracks():
        if t.GetNetname() != 'GND' and t.IsOnLayer(lid):
            t.TransformShapeToPolygon(ps, lid, 0, ERR, pcbnew.ERROR_OUTSIDE)
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != 'GND' and p.IsOnLayer(lid) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                p.TransformShapeToPolygon(ps, lid, 0, ERR, pcbnew.ERROR_OUTSIDE)
            elif p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                circle(p.GetPosition(), mm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2, ps)
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() != 'GND' and z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
            ps.BooleanAdd(fill(z, lid))
    return ps


def strap_paths(c, t):
    """Octilinear polylines from c to t: straight, or one bend (horizontal / vertical and 45 degrees, either order;
    or horizontal and vertical); every segment >= STRAP_SEG."""
    dx, dy = t[0] - c[0], t[1] - c[1]
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    adx, ady = abs(dx), abs(dy)
    out = []
    if adx < EPS2 or ady < EPS2 or abs(adx - ady) < EPS2:
        out.append([c, t])
    else:
        if adx > ady:
            ks = [(t[0] - sx * ady, c[1]), (c[0] + sx * ady, t[1])]
        else:
            ks = [(c[0], t[1] - sy * adx), (t[0], c[1] + sy * adx)]
        ks += [(t[0], c[1]), (c[0], t[1])]
        for k in ks:
            k = (r4(k[0]), r4(k[1]))
            if math.dist(c, k) >= STRAP_SEG and math.dist(k, t) >= STRAP_SEG:
                out.append([c, k, t])
    return out


def strap_clear(b, path, w, lid, bad):
    ps = pcbnew.SHAPE_POLY_SET()
    for a, c in zip(path, path[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(P(*a))
        t.SetEnd(P(*c))
        t.SetWidth(MM(w))
        t.SetLayer(lid)
        t.TransformShapeToPolygon(ps, lid, MM(STRAP_GAP + MARGIN), ERR, pcbnew.ERROR_OUTSIDE)
    hit = pcbnew.SHAPE_POLY_SET(ps)
    hit.BooleanIntersection(bad)
    return hit.OutlineCount() == 0


def straps(b, log=print):
    """The strap stage: each STRAPS pad gets the shortest octilinear GND strap (one segment or one bend, STRAP_W) to a GND
    via, a GND pad of STRAP_PADS_OK or a new legal via spot within STRAP_REACH (SPACING_ISLAND apart), STRAP_GAP + MARGIN clear of every other
    net's copper on its layer. Returns ([(layer, w, a, c, basis)], [(new via, basis)])."""
    tracks, new = [], []
    sp = Spots(b, revive=True, spacing=SPACING_ISLAND)
    pads = {f'{f.GetReference()}.{p.GetNumber()}': p for f in b.GetFootprints() for p in f.Pads()}
    for name in STRAPS:
        p = pads[name]
        assert p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD, name
        lid = F if p.IsOnLayer(F) else B
        layer = 'F' if lid == F else 'B'
        c = (r4(mm(p.GetPosition().x)), r4(mm(p.GetPosition().y)))
        bad = foreign(b, lid)
        targets = [(q, None) for q in gnd_points(b) + [v for v, _ in new] if math.dist(q, c) <= STRAP_REACH]
        targets += [((r4(mm(q.GetPosition().x)), r4(mm(q.GetPosition().y))), None) for k, q in pads.items()
                    if k in STRAP_PADS_OK and q.IsOnLayer(lid) and
                    math.dist(c, (mm(q.GetPosition().x), mm(q.GetPosition().y))) <= STRAP_REACH]
        n = int(round(STRAP_REACH / STEP))
        for j in range(-n, n + 1):
            for i in range(-n, n + 1):
                q = (r4(c[0] + i * STEP), r4(c[1] + j * STEP))
                if math.dist(q, c) <= STRAP_REACH and sp.ok(q):
                    targets.append((q, 'via'))
        best = None
        for q, kind in targets:
            for path in strap_paths(c, q):
                L = sum(math.dist(a, e) for a, e in zip(path, path[1:]))
                key = (round(L + (0.5 if kind else 0.0), 6), len(path), q[1], q[0])
                if (best is None or key < best[0]) and strap_clear(b, path, STRAP_W, lid, bad):
                    best = (key, path, q, kind)
        if best is None:
            log(f'  strap: {name} ({c[0]:.2f}, {c[1]:.2f}): no clear strap within {STRAP_REACH} mm')
            continue
        _, path, q, kind = best
        if kind == 'via':
            sp.add(q)
            new.append((q, f'strap {name}'))
        for a, e in zip(path, path[1:]):
            tracks.append((layer, STRAP_W, a, e, f'strap {name}'))
    return tracks, new


def reviving(b, rows, via_row, new, basis):
    """Draw the vias of a reviving pass (rows with basis), run the island stage, and drop each of them that still sits
    in an outer GND island with fewer than two GND vias (an island it revived alone); the board is left refilled."""
    if not new:
        return []
    draw_vias(b, new)
    refill(b)
    kept = list(new)
    for q in new:
        rows.append(('via', 'GND', 'FB', f'{VIA[0]}/{VIA[1]}', q[0], q[1], '', '', basis))
    island_stage(b, via_row)
    for _ in range(3):
        drop = [q for name, one in weak_islands(b) for q in kept if in_island(one, q)]
        if not drop:
            break
        for q in drop:
            kept.remove(q)
            rows[:] = [r for r in rows if not (r[0] == 'via' and (r[4], r[5]) == q)]
            for t in list(b.GetTracks()):
                if t.GetClass() == 'PCB_VIA' and (r4(mm(t.GetPosition().x)), r4(mm(t.GetPosition().y))) == q:
                    b.Delete(t)
        refill(b)
    return kept


def island_stage(b, via_row, rounds=4):
    """The island stage (module docstring): every weak outer GND island gets GND vias up to two, the spot farthest from
    its vias first; returns the vias added (drawn, board refilled)."""
    added = []
    for _ in range(rounds):
        weak = weak_islands(b)
        if not weak:
            break
        sp = Spots(b, revive=True, spacing=SPACING_ISLAND, strip=True)
        new = []
        for name, one in weak:
            inside = [q for q in gnd_points(b) if in_island(one, q)]
            while len(inside) < 2:
                bb = one.BBox()
                best = None
                yy = mm(bb.GetTop()) + STEP / 2
                while yy < mm(bb.GetBottom()):
                    xx = mm(bb.GetLeft()) + STEP / 2
                    while xx < mm(bb.GetRight()):
                        q = (r4(xx), r4(yy))
                        if one.Contains(P(*q)) and sp.ok(q):
                            d = min((math.dist(q, v) for v in inside), default=0.0)
                            if best is None or d > best[0] + 1e-9:
                                best = (d, q)
                        xx += STEP
                    yy += STEP
                if best is None:
                    break
                sp.add(best[1])
                new.append(best[1])
                inside.append(best[1])
                via_row(best[1], f'island {name}')
        if not new:
            break
        draw_vias(b, new)
        refill(b)
        added += new
    return added


def generate(b, log=print):
    rows = []

    def via_row(q, basis):
        rows.append(('via', 'GND', 'FB', f'{VIA[0]}/{VIA[1]}', q[0], q[1], '', '', basis))

    # 1. returns, pads, grid and cover on the legal region of the poured board
    sp = Spots(b)
    near = Near(gnd_points(b))
    new = []

    def put(q, basis):
        sp.add(q)
        near.add(q)
        new.append(q)
        via_row(q, basis)

    for net, q in power_layer_changes(b):
        if near.dist(q) <= RETURN_REACH:
            continue
        s = sp.nearest(q, RETURN_REACH)
        if s:
            put(s, f'return {net}')
        else:
            log(f'  return: no legal spot within {RETURN_REACH} mm of the {net} layer change {q}')
    pads = pad_returns(b, sp, via_row, log)
    for q in pads:
        near.add(q)
        new.append(q)
    x0, y0, x1, y1 = board_box(b)
    y = GRID_Y0
    while y < y1 - EDGE:
        x = GRID_X0
        while x < x1 - EDGE:
            node = (r4(x), r4(y))
            if near.dist(node) > SERVED:
                s = sp.nearest(node, SNAP)
                if s:
                    put(s, 'grid')
            x += PITCH
        y += PITCH
    draw_vias(b, new)
    refill(b)
    # cover: may revive a removed GND island when the island stage then gives it a second via (else the via is dropped)
    sp2 = Spots(b, revive=True)
    sp2.placed = list(sp.placed)
    reviving(b, rows, via_row, cover(b, sp2, near), 'cover')
    # 2. islands
    island_stage(b, via_row)
    # 3. the reach patch: a second cover pass at the P9 limit, SPACING_ISLAND apart, a via for any gain, reviving as above
    sp = Spots(b, revive=True, spacing=SPACING_ISLAND)
    reviving(b, rows, via_row, cover(b, sp, Near(gnd_points(b)), PATCH_COVER, 1), 'patch')
    for name, one in weak_islands(b):
        bb = one.BBox()
        log(f'  island {name}.Cu ({mm(bb.GetLeft()):.2f}, {mm(bb.GetTop()):.2f})-({mm(bb.GetRight()):.2f}, '
            f'{mm(bb.GetBottom()):.2f}), {one.Area() / 1e12:.2f} mm2: fewer than two GND vias, no legal spot')
    # 4. fingers
    new = finger_returns(b, Spots(b), via_row, log)
    if new:
        draw_vias(b, new)
        refill(b)
    # 5. straps
    tracks, vias = straps(b, log)
    for q, basis in vias:
        via_row(q, basis)
    for layer, w, a, c, basis in tracks:
        rows.append(('track', 'GND', layer, f'{w:g}', a[0], a[1], c[0], c[1], basis))
    if tracks:
        draw_vias(b, [q for q, _ in vias])
        for layer, w, a, c, _ in tracks:
            draw_track(b, layer, w, a, c)
        refill(b)
    # 6. reach: while P9 (the board points' p95 distance to a GND via) is above REACH_TARGET, the legal spot (a removed
    # island may be revived, then held by that via alone) that brings most points beyond P9's 3.5 mm within it
    for _ in range(5):
        near = Near(gnd_points(b))
        pts = board_points(b)
        d = sorted(near.dist(q) for q in pts)
        k = (len(d) - 1) * 0.95                     # survey_metrics.pctl (linear between the sorted values)
        p95 = d[int(math.floor(k))] + (d[int(math.ceil(k))] - d[int(math.floor(k))]) * (k - math.floor(k))
        if p95 <= REACH_TARGET:
            break
        far = [q for q in pts if near.dist(q) > 3.5]
        sp = Spots(b, revive=True, spacing=SPACING_ISLAND)
        ras = rc.Raster((0.0, STRIP_Y / rc.NM, board_box(b)[2] / rc.NM, board_box(b)[3] / rc.NM), CAND_STEP / rc.NM)
        grid = ras.fill([sp.region])
        best = None
        for k in range(ras.nx * ras.ny):
            if grid[k]:
                c = tuple(r4(mm(v)) for v in ras.centre(k))
                g = sum(1 for q in far if math.dist(q, c) <= 3.5)
                if g and (best is None or (g, -c[1], -c[0]) > best[0]):
                    best = ((g, -c[1], -c[0]), c)
        if best is None:
            log(f'  reach: P9 {p95:.3f} mm, no spot brings a point within 3.5 mm')
            break
        via_row(best[1], 'reach')
        draw_vias(b, [best[1]])
        refill(b)
        log(f'  reach: P9 {p95:.3f} mm -> via {best[1]} ({best[0][0]} points)')
    # 7. copper: pads and copper the straight-line stages counted as covered (R9P1-PLANES-01 / -02, D-F1-07)
    copper_stage(b, via_row, log)
    for pc in rc.pour_pieces(b):
        log(f'  left: {pc["cat"]} {pcbnew.LayerName(pc["lid"])} box {[round(mm(v), 2) for v in pc["box"]]} '
            f'{pc["len_mm"]} mm')
    return rows


HEADER = ('# R9 GND stitching (m3_design/r9_ground_aid.py; R9_DECISIONS D-S8-*, D-F1-07): drawn by m3_design/r9_ground.py '
          'in this order. item via: layer FB, size diameter/drill; item track: size = width. basis: return NET, pad '
          'REF.PIN, grid, cover, island F|B, patch, finger F|B, strap REF.PIN, reach, copper pad REF.PIN, copper F|B\n')
COLS = ('item', 'net', 'layer', 'size', 'x0', 'y0', 'x1', 'y1', 'basis')


def text(rows):
    fh = io.StringIO()
    fh.write(HEADER)
    w = csv.writer(fh, delimiter='\t', lineterminator='\n')
    w.writerow(COLS)
    for row in rows:
        w.writerow([f'{v:g}' if isinstance(v, float) else v for v in row])
    return fh.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--check', action='store_true', help='the generated table must equal the frozen r9_ground.tsv')
    a = ap.parse_args()
    b = pcbnew.LoadBoard(str(a.board.resolve()))
    r9_ground.grow_pours(b)
    refill(b)
    rows = generate(b)
    out = text(rows)
    a.out.write_text(out)
    count = defaultdict(int)
    for row in rows:
        count[row[8].split()[0]] += 1
    print(f'r9_ground_aid: {len(rows)} rows', dict(count))
    if a.check:
        same = TABLE.read_text() == out
        print('frozen table reproduced' if same else 'DIFFERS from the frozen r9_ground.tsv')
        return 0 if same else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
