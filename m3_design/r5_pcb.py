#!/usr/bin/env python3
"""M3-ASSY-R4 -> R5 board: two-sided re-floorplan at 46 x 100 mm (docs/M3_R5.md).

usage: <KiCad python3> m3_design/r5_pcb.py [m3_design/assembly_review/m3.kicad_pcb]
KiCad python on macOS: /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3

Run on the R4 board (m3_design/r5_build.sh restores it from git first). The schematic and BOM are
unchanged; this is a placement and routing redesign. Steps:
  1. strip all R4 copper, zones, outline, holes and board-level silkscreen (footprints stay);
  2. new 46 x L outline, four M3 mounting holes, J122's two tie holes, tooling holes;
  3. place every footprint from the PLACE table (side F or B); the R4 pyro block (terminals, FETs,
     gate networks, sense dividers) is moved as one rigid group with its own copper, so the spacing
     work of R4 passes 2-14 carries over unchanged (pyro rules A-H still run on the whole board);
  4. rule areas (PYRO_BLOCK, MEMS keep-outs, bottom-side keep-outs under through-hole pin tails);
  5. zones (In1 GND plane, In2 power islands, outer GND pours) and scripted critical routes, then the slow nets
     the autorouter could not fit in the trial runs (r5_routes.slow_links, long_links).
The non-critical nets are then routed by Freerouting (m3_design/r5_route.py, session file in git).
Idempotence: every run starts from the restored R4 board.
"""
import math
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r5_routes  # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
PCB = ARGS[0] if ARGS else 'm3_design/assembly_review/m3.kicad_pcb'
mm, MM = pcbnew.ToMM, pcbnew.FromMM
W, L = 46.0, 100.0                # board outline (mm); y = 0 is the aft (battery) edge
PYRO_C = (23.0, 57.2)             # the R4 pyro block (y 42.0-72.4) turns 180° about its centre ...
PYRO_DY = 24.0                    # ... and moves 24 mm forward: y 66.0-96.4
HOLES = [(4.0, 4.0), (42.3, 4.0), (4.0, 96.4), (42.0, 96.4)]   # M3, Ø3.2
# J122's plug-retention tie (MARGIN_PRESCRIPTION P1-13, REQUIREMENTS P3): Ø3.2 holes beyond the header's aft end and
# its forward end, the forward one right of the RAW_ACT column (on the axis it would cut the servo feed); the tie runs
# from one to the other diagonally over all four plugs (x 22.3-26.3 across them) and closes under the board
ZIP = [(21.5, 50.6), (27.0, 64.6)]
ZIP_R = 2.6                       # parts keep 1.0 mm from a tie hole's edge (the tie's head and its run)


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def fp_of(b, ref):
    f = b.FindFootprintByReference(ref)
    assert f is not None, f'{ref} missing'
    return f


def net(b, name):
    n = b.FindNet(name)
    assert n is not None, f'net {name} missing'
    return n


# --- 1. strip ------------------------------------------------------------------------------------

PYRO_BLOCK = ('J120 J121 J124 J125 Q124 Q125 R126 R127 R128 R129 R130 R131 R132 R133 R134 R135 R138 R139 '
              'R140 R141 R142 R143 R144 R145 R173 R174 R175 R176 R178 R180 R181 C126 C127 C128 C129 C138 '
              'C139 C140 C141 D120 TP122 TP123 R124 R125 R177 R182 C122').split()
PYRO_NETS = {'PYRO1_BUS', 'PYRO2_BUS', 'PYRO1_IGN', 'PYRO2_IGN', 'PYRO1_OUT', 'PYRO2_OUT', 'PYRO1_GATE',
             'PYRO2_GATE', 'PYRO1_GATE_N', 'PYRO2_GATE_N', 'ARM1_SENSE', 'ARM2_SENSE', 'PYRO1_CONT',
             'PYRO2_CONT', 'PYRO1_COLD', 'PYRO2_COLD', 'PYRO1_CONT_MID', 'PYRO2_CONT_MID', 'ARM1_SENSE_MID',
             'ARM2_SENSE_MID', 'RAW_ACT_SENSE', 'RAW_ACT_SENSE_MID'}


BLOCK_NETS = PYRO_NETS | {'GND', '3V3'}


def strip(b):
    """Keep the R4 pyro block's own copper (pyro, GND and 3V3 segments and vias with every end inside
    x 4-42, y 42.0-72.4), moved with the block later; delete every other track, via, zone and drawing.
    prune_stubs() then removes what R4 used to leave the block toward its forward MCU."""
    drawings = list(b.GetDrawings())
    zones = list(b.Zones())
    keep = []
    for t in list(b.GetTracks()):
        pts = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
        inside = all(42.0 <= mm(p.y) <= 72.4 for p in pts) and all(4.0 <= mm(p.x) <= 42.0 for p in pts)
        if inside and t.GetNetname() in BLOCK_NETS:
            keep.append(t)
        else:
            b.Delete(t)
    for z in zones:
        b.Delete(z)
    for d in drawings:
        b.Delete(d)
    return keep


# --- 2. outline and holes ------------------------------------------------------------------------

def edge_line(b, a, c):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.1))
    s.SetStart(P(*a))
    s.SetEnd(P(*c))
    b.Add(s)


def edge_circle(b, c, d):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.05))
    s.SetCenter(P(*c))
    s.SetEnd(P(c[0] + d / 2, c[1]))
    b.Add(s)


def outline(b):
    for a, c in (((0, 0), (W, 0)), ((W, 0), (W, L)), ((W, L), (0, L)), ((0, L), (0, 0))):
        edge_line(b, a, c)
    for h in HOLES + ZIP:
        edge_circle(b, h, 3.2)


# --- 3. placement --------------------------------------------------------------------------------

def place(b, ref, x, y, rot=0.0, side='F'):
    f = fp_of(b, ref)
    if f.IsFlipped() != (side == 'B'):
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(rot)
    f.SetPosition(P(x, y))


def move_pyro_block(b, keep):
    """Turn the R4 pyro block 180° in place: its gate and sense nets left it toward R4's forward
    MCU, and R5's MCU is aft of it. The ARM terminals move to the left edge, the igniters to the right."""
    c = P(*PYRO_C)
    for r in PYRO_BLOCK:
        fp_of(b, r).Rotate(c, pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T))
        fp_of(b, r).Move(P(0, PYRO_DY))
    for t in keep:
        t.Rotate(c, pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T))
        t.Move(P(0, PYRO_DY))


# (ref, x, y, rot, side). Top: heavy, tall and through-hole parts and the MCU.
PLACE = [
    ('J1', 19.5, 5.5, 0, 'F'),          # battery terminal on the aft edge, wire entries aft
    ('J123', 34.5, 3.8, 0, 'F'),        # pull-pin
    ('J9', 36.25, 30.7, -90, 'F'),      # camera terminal, right edge, entries to the wall
    ('C84', 7.5, 33.3, 90, 'F'),        # tallest part: 15.5 mm off the axis, as in R4
    ('U1', 21.85, 35.5, 90, 'F'),
    ('J3', 4.6, 57.3, -90, 'F'),        # USB-C on the left edge beside U1's USB pins
    ('J2', 43.7, 58.65, 90, 'F'),       # SWD, right edge
    ('LS120', 14.1, 58.0, 0, 'F'),
    ('J122', 23.0, 57.7, 90, 'F'),      # servo header on the bore axis
    ('C121', 32.6, 57.4, 0, 'F'),
]


# Bottom-side rule (DFM, engineering choice): no bottom part within 1.5 mm of a through-hole pad (the
# pin tails are hand- or selectively soldered from the bottom), none within 3.5 mm of a mounting-hole
# centre (standoff and washer), none within 1.0 mm of a pyro via and 2.0 mm of the bare gate test pads.
THT_GAP, STANDOFF_R, PYRO_VIA_GAP, GATE_TP_GAP, PART_GAP = 1.5, 3.5, 1.0, 2.0, 0.3
# Bottom corridors kept free of auto-placed parts for the scripted critical copper (USB fan-out and run to U1).
KEEP_B = [(7.6, 53.6, 10.4, 61.6), (9.6, 38.0, 14.0, 54.4),
          (21.8, 8.6, 27.6, 12.9),     # ... and between the 3V3 buck and U11 (VLOGIC and RAW_PROTECTED pass there)
          (9.4, 16.9, 13.6, 27.6)]     # ... and under U9's network (its vias)

# Manual placements of the bottom ICs and large parts (x, y as seen from the top; side B).
PLACE_B = [
    ('Q120', 4.0, 13.0, 180), ('Q121', 4.0, 27.3, 0),          # load switch under C84: drains to BAT_IN / RAW_ACT
    ('D8', 11.9, 13.2, 90),                                    # input TVS
    # 3V3 buck as R4: input capacitor C7 between U2's VIN/GND pins and L1, bootstrap capacitor C5 straight under
    # U2's BST and SW pins, L1 right of U2 (SW leaves below C7); the power mux U11 beyond L1
    ('U11', 29.2, 10.2, 0), ('U2', 18.0, 15.0, 0), ('L1', 24.5, 15.0, 0), ('C7', 20.8, 15.0, 270), ('C5', 17.5, 17.65, 180),
    ('C8', 28.6, 15.6, 90),                                    # output capacitor east of L1's 3V3 pad, below U11
    ('U4', 36.0, 60.3, 0), ('U5', 36.3, 55.0, 0),             # MEMS under C121, clear of the In2 pyro lanes
    ('Y1', 25.6, 35.75, 180), ('C25', 27.12, 39.1, 0), ('C26', 22.6, 34.88, 90),   # HSE crystal under U1
    ('U12', 41.8, 33.0, 90), ('U13', 41.5, 13.5, 0),          # camera UART buffer and its LDO, by J9
    # camera 5 V buck, one stack in the right strip: eFuse, input capacitors at U8's VIN/GND end, U8, bootstrap
    # capacitor beside SW/BST, inductor, output capacitors (AP63300 datasheet layout order)
    ('U7', 38.2, 69.0, -90),                                   # camera eFuse beside the buck's input capacitor
    ('C73', 41.8, 69.4, 0), ('C72', 41.8, 72.8, 0), ('U8', 41.8, 76.4, 0),
    ('C74', 44.7, 76.6, 270), ('L3', 41.8, 82.1, 270), ('C75', 41.8, 87.5, 0), ('C76', 41.8, 90.9, 0),
    ('D4', 11.0, 56.0, 0), ('R7', 13.7, 56.05, 0), ('R8', 9.6, 61.0, 0),   # USB ESD, CC pull-downs
    ('U10', 15.0, 62.6, 0), ('Q123', 10.6, 64.2, 0),
    ('D121', 32.0, 64.4, 0), ('C151', 15.0, 66.7, 0), ('C150', 15.0, 69.0, 0),   # servo clamp, RAW_ACT bulk
    ('R169', 32.0, 33.3, 90), ('R168', 32.6, 34.9, 180), ('R170', 24.4, 28.0, 90),   # ADC series resistors
    ('R171', 24.8, 30.4, 0), ('R172', 22.6, 30.4, 0), ('R179', 27.69, 92.4, 0),
]
PLACE_T = [('R166', 2.4, 14.0, 90), ('U9', 11.2, 22.6, 90),
           # U9's network beside its own pins (as R4: short F.Cu links, r5_routes.u9_network): the output capacitor
           # on the OUT end; ILIM, DVDT north; enable parts west; the OVLO divider (BAT_IN end over the In2 strip) and
           # the fault pull-up in a row in the 2.4 mm between U9 and C84
           ('C82', 14.95, 22.35, 0), ('R84', 10.65, 19.3, -90), ('C81', 12.6, 19.15, 90), ('TP89', 10.4, 16.6, 0),
           ('R82', 8.63, 25.25, 180), ('R83', 5.35, 25.25, 180), ('R89', 12.8, 25.1, 180),
           ('R81', 7.6, 23.3, 180), ('C87', 7.25, 21.7, 180), ('R165', 5.35, 20.3, 90), ('C88', 9.15, 20.85, 90),
           # the camera eFuse's fault pull-up on the top, over U7: its FLT pin leaves south into J121's pin-tail zone
           ('R77', 38.6, 67.4, -90), ('D9', 16.0, 13.2, 0), ('U3', 24.6, 16.0, 90), ('TH1', 44.8, 9.2, 0), ('TH2', 1.4, 64.6, 0), ('TH3', 1.4, 90.0, 0),
           ('R72', 43.7, 74.0, 0), ('R71', 43.7, 75.9, 0), ('C77', 43.7, 80.6, 0)]   # camera buck FB, above U8
           # (clear of y 77-78.7, where J121.2's E1+ legend goes in the edge strip)

# Auto-placed parts: (refs, region, anchor pads or None = by net); a region may name fallbacks "A/B".
REG = {
    'TS': ('F', (8.6, 11.4, 30.5, 26.25)),     # top strip between J1 and U1
    'BK': ('B', (19.0, 17.4, 31.0, 26.6)),     # bottom, south of the 3V3 buck's inductor (its output capacitors)
    'TR': ('F', (30.8, 0.3, 45.7, 13.4)),      # top, right of J1 (pull-pin corner)
    'TL': ('F', (0.4, 7.7, 8.3, 26.3)),        # top, left of J1 (input damper and capacitors)
    'AG': ('B', (6.75, 15.4, 13.9, 37.5)),     # beside the load switch: its gate network, BAT_IN capacitors
    'TT': ('F', (25.0, 63.1, 41.5, 66.0)),     # top strip between the servo row and the pyro block (test pads)
    'LA': ('B', (0.3, 7.6, 13.4, 43.4)),       # left-aft, under C84
    'J1': ('B', (9.1, 8.4, 33.3, 26.8)),       # under the J1 body, forward of its pins
    'U1': ('B', (13.4, 26.8, 33.3, 44.0)),     # under U1
    'RA': ('B', (30.6, 7.6, 45.7, 42.3)),      # right-aft, under J9
    'LS': ('B', (0.3, 43.6, 19.0, 66.0)),      # under LS120 and J3
    'CC': ('B', (27.0, 44.2, 41.3, 66.0)),     # under C121
    'PC': ('B', (12.8, 65.5, 33.2, 95.0)),     # under the pyro block, centre
    'PL': ('B', (0.3, 65.5, 7.2, 93.0)),
    'PR': ('B', (37.5, 64.0, 45.7, 93.0)),     # under the igniter terminals' outer half
    'FW': ('B', (7.5, 91.0, 38.5, 99.7)),      # forward strip
    'UC': ('B', (33.3, 61.8, 37.6, 70.6)),     # beside the camera eFuse U7, between the servo clamp and J121's pins
    'UT': ('F', (30.0, 66.2, 37.8, 70.2)),     # top, over and west of U7: between the test-pad strip and J121's body,
                                               # clear of R77 and U7's fault-pin run up to it (x 38-39)
    'BL': ('B', (14.0, 44.2, 30.0, 52.4)),     # the band south of U1 (bottom)
}
AUTO = [
    # 3V3 buck (power loop first): the second input capacitor on VIN/GND, the output capacitors on L1's 3V3 end
    ('C6', 'J1', ['U2.2']), ('C9', 'BK/J1', ['L1.2']),
    ('R80', 'TS/J1', None),
    ('C89 C95', 'TL', None),
    ('R120 C120 R121 Q122 R122 R123', 'AG/LA', None),
    ('C80 C96 R167', 'AG/LA', None),
    ('TP80', 'AG/LA/TT', None),
    ('TP121', 'LA/AG/TT', None),                  # the actuator switch's gate, by its gate network
    ('TP84 TP85', 'AG/LA/TT', None),               # BAT_ENABLE and BAT_FAULT_N, by U9's network (in the test-pad
                                                  # strip TP84 was 45 mm from its net)
    ('TP120', 'PL', None),
    # U11's network beside its own pins: ILIM, soft-start and the status pull-up first, by pins 10, 11 and 9 on its
    # south row (TI: the ILIM resistor close to its pin), then the OVLO divider (pin 5, north row, toward J1's pin
    # tails); R92 on the RAW_PROTECTED output by U9's capacitor
    ('R86', 'J1/RA', ['U11.10']), ('C85', 'J1/RA', ['U11.11']), ('R91', 'J1/RA', ['U11.9']),
    ('R88 R87', 'TS/J1/RA', ['U11.5']), ('R92', 'J1/TS', ['C82.1']),   # (the OVLO divider on the top, by U11.5's via:
                                                  # under J1 it sat 11 mm away, boxed in by USB_LIMITED)
    ('TP87', 'TT/J1/U1', None), ('TP83', 'J1/RA/TT', None),   # VLOGIC by U11
    # MCU decoupling first (each on its pin), then the flash and the crystal
    ('C13', 'U1', ['U1.6']), ('C14', 'U1', ['U1.11']), ('C23', 'U1', ['U1.11']), ('C15', 'U1', ['U1.27']),
    ('C16', 'U1', ['U1.50']), ('C19', 'U1', ['U1.48']), ('C17', 'U1', ['U1.75']), ('C20', 'U1', ['U1.73']),
    ('C18', 'U1', ['U1.100']), ('C21', 'U1', ['U1.20']), ('C22', 'U1/RA', ['U1.21']),
    ('C29', 'TS', ['U3.8']),
    ('C24', 'U1/RA', ['U1.14']), ('R5', 'BL/U1/CC', ['U1.94']), ('R10', 'TS/U1', ['U3.1']),
    ('R164 C10 C11', 'RA/U1/CC', ['U1.21']), ('R60 R61 C60 R62 R63', 'RA/U1/J1', None),
    ('C30', 'CC', ['U4.8']), ('C31', 'CC', ['U4.8']), ('C32', 'CC', ['U5.1']), ('R11 R12 R13 R64', 'CC', None),
    ('C93 C90 C92 C91 R100 R101 R102 R103 R104 R105 C94', 'RA/CC/J1', None),
    ('TP90 TP91 TP75', 'TT/RA/CC', None), ('TP76', 'RA/CC/TT', None),   # camera TX by J9
    ('D122 R160 R161 C160', 'TR/RA/U1/J1', None),
    # the camera eFuse's network beside its own pins: the input capacitor on the bottom by IN; the enable divider,
    # DVDT capacitor and ILIM resistor on the bottom where they fit, else on the top over U7 (UT; a via each)
    ('C71', 'UC/PR/PC', ['U7.3']), ('R74 R75', 'UC/UT/PC', ['U7.2']), ('C70', 'UC/UT/PC', ['U7.1']),
    ('R70', 'UC/UT/PC', ['U7.7']),
    ('TP81', 'UC/CC/TT', None),                   # RAW_PROTECTED on the bottom by U7, on its feed (from the strip
                                                  # no router reached it)
    ('TP70 TP71 TP73', 'PR/TT/PC/FW', None),
    ('R78 TP72 TP74', 'PR/PC/TT', None),
    ('R9 R110 C28', 'LS', None),
    ('TP92', 'TT/LS', None),
    ('R90', 'LS/U1', ['U10.4']), ('R85 C83 C86', 'LS/U1', None),
    ('TP82 TP86', 'TT/LS/U1', None),
    ('R162 R163 D123', 'LS/PL', None),
    ('R150 R151 R152 R153 R154 R155 R156 R157', 'PC/CC', None),
    ('LED1 R32 LED2 R33', 'TR/FW', None),
    ('R76', 'PC', None),
    ('TP88', 'TT/PC', None),
]


def _local_geom(f, side, rot):
    """Courtyard bbox and pad centres of f relative to its origin at (side, rot)."""
    pos0, rot0, flip0 = f.GetPosition(), f.GetOrientationDegrees(), f.IsFlipped()
    place(f.GetBoard(), f.GetReference(), 0, 0, rot, side)
    cy = f.GetCourtyard(pcbnew.B_CrtYd if side == 'B' else pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
    box = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))
    pads = [(p.GetNumber(), p.GetNetname(), mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in f.Pads()]
    place(f.GetBoard(), f.GetReference(), mm(pos0.x), mm(pos0.y), rot0, 'B' if flip0 else 'F')
    return box, pads


def _box(f):
    cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
    return (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))


def _rect_gap(a, c):
    dx = max(c[0] - a[2], a[0] - c[2], 0)
    dy = max(c[1] - a[3], a[1] - c[3], 0)
    return math.hypot(dx, dy)


def obstacles(b, side, skip=()):
    """Rectangles and circles a new part on `side` must keep clear of, with the gap to keep."""
    rects, circs = [], []
    for f in b.GetFootprints():
        if f.GetReference() in skip or mm(f.GetPosition().x) > W + 1:
            continue
        if f.IsFlipped() == (side == 'B'):
            rects.append((_box(f), PART_GAP))
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and f.GetReference().startswith('TH'):
                circs.append((mm(p.GetPosition().x), mm(p.GetPosition().y), 1.0 + PART_GAP))
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and side == 'B' and not f.IsFlipped():
                r = mm(max(p.GetSize(pcbnew.F_Cu).x, p.GetSize(pcbnew.F_Cu).y)) / 2
                circs.append((mm(p.GetPosition().x), mm(p.GetPosition().y), r + THT_GAP))
    for h in HOLES:
        circs.append((h[0], h[1], STANDOFF_R))
    for h in ZIP:
        circs.append((h[0], h[1], ZIP_R))
    lay = pcbnew.B_Cu if side == 'B' else pcbnew.F_Cu
    for t in b.GetTracks():                          # scripted critical copper already on the board
        if t.GetNetname() in PYRO_NETS:
            continue                                 # (the moved pyro copper is handled below)
        if t.GetClass() == 'PCB_VIA':
            circs.append((mm(t.GetPosition().x), mm(t.GetPosition().y), 0.3 + 0.2))
        elif t.GetLayer() == lay:
            (sx, sy), (ex, ey) = (mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y))
            n = max(1, int(math.hypot(ex - sx, ey - sy) / 0.3))
            for i in range(n + 1):
                circs.append((sx + (ex - sx) * i / n, sy + (ey - sy) * i / n, mm(t.GetWidth()) / 2 + 0.2))
    if side == 'B':
        for r in KEEP_B:
            rects.append((r, 0.01))
    if side == 'B':                                  # U1's fan-out vias: a ring just outside its pads and one
        c = fp_of(b, 'U1').GetPosition()             # just inside them stay free of bottom parts
        ux, uy = mm(c.x), mm(c.y)
        for a0, a1 in ((8.5, 9.6), (5.6, 6.5)):
            for r in ((ux - a1, uy - a1, ux + a1, uy - a0), (ux - a1, uy + a0, ux + a1, uy + a1),
                      (ux - a1, uy - a1, ux - a0, uy + a1), (ux + a0, uy - a1, ux + a1, uy + a1)):
                rects.append((r, 0.01))
    if side == 'B':
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_VIA' and t.GetNetname() in PYRO_NETS:
                circs.append((mm(t.GetPosition().x), mm(t.GetPosition().y), 0.3 + PYRO_VIA_GAP))
        for t in b.GetTracks():
            if t.GetClass() != 'PCB_VIA' and t.GetLayer() == pcbnew.B_Cu and t.GetNetname() in PYRO_NETS:
                (sx, sy), (ex, ey) = (mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y))
                n = max(1, int(math.hypot(ex - sx, ey - sy) / 0.5))
                for i in range(n + 1):
                    circs.append((sx + (ex - sx) * i / n, sy + (ey - sy) * i / n, 0.1 + PYRO_VIA_GAP))
        for r in ('TP122', 'TP123'):
            c = fp_of(b, r).GetPosition()
            circs.append((mm(c.x), mm(c.y), 1.05 + GATE_TP_GAP))
    return rects, circs


def pours(b, side):
    """(outline, net) of the power pours on `side` (not GND): a part keeps out unless it has a pad on that net."""
    lay = pcbnew.B_Cu if side == 'B' else pcbnew.F_Cu
    return [(z.Outline(), z.GetNetname()) for z in b.Zones()
            if not z.GetIsRuleArea() and z.IsOnLayer(lay) and z.GetNetname() != 'GND']


def _poly_hit(box, polys):
    for o in polys:
        bb = o.BBox()
        if box[2] < mm(bb.GetX()) or box[0] > mm(bb.GetRight()) or box[3] < mm(bb.GetY()) or box[1] > mm(bb.GetBottom()):
            continue
        if any(o.Contains(P(box[0] + (box[2] - box[0]) * i / 4, box[1] + (box[3] - box[1]) * j / 4))
               for i in range(5) for j in range(5)):
            return True
        ol = o.COutline(0)
        if any(box[0] < mm(ol.CPoint(k).x) < box[2] and box[1] < mm(ol.CPoint(k).y) < box[3]
               for k in range(ol.PointCount())):
            return True
    return False


def _fits(box, rects, circs, region, polys=()):
    x0, y0, x1, y1 = region
    if box[0] < max(x0, 0.3) or box[1] < max(y0, 0.3) or box[2] > min(x1, W - 0.3) or box[3] > min(y1, L - 0.3):
        return False
    for r, g in rects:
        if _rect_gap(box, r) < g:
            return False
    for cx, cy, cr in circs:
        dx = max(box[0] - cx, 0, cx - box[2])
        dy = max(box[1] - cy, 0, cy - box[3])
        if math.hypot(dx, dy) < cr:
            return False
    return not _poly_hit(box, polys)


def _targets(b, f, anchors):
    """Pad -> target point. Explicit anchors pull every non-GND pad; otherwise each non-GND pad goes
    to the nearest placed pad of its net (3V3/3V3A/GND never pull: they are planes)."""
    if anchors:
        pts = []
        for a in anchors:
            r, n = a.split('.')
            pd = next(p for p in fp_of(b, r).Pads() if p.GetNumber() == n)
            pts.append((mm(pd.GetPosition().x), mm(pd.GetPosition().y)))
        return {'*': pts}
    out = {}
    for p in f.Pads():
        n = p.GetNetname()
        if n in ('GND', '3V3', '3V3A', '') or n.startswith('unconnected'):
            continue
        pts = []
        for g in b.GetFootprints():
            if g.GetReference() == f.GetReference() or mm(g.GetPosition().x) > W + 1:
                continue
            for q in g.Pads():
                if q.GetNetname() == n:
                    pts.append((mm(q.GetPosition().x), mm(q.GetPosition().y)))
        if pts:
            out[p.GetNumber()] = pts
    return out


def autoplace(b, ref, region_keys, anchors):
    for k in region_keys.split('/'):
        if _autoplace(b, ref, k, anchors):
            return
    print(f'  no spot for {ref} in {region_keys}')


def _autoplace(b, ref, region_key, anchors):
    f = fp_of(b, ref)
    side, region = REG[region_key]
    tg = _targets(b, f, anchors)
    rects, circs = obstacles(b, side, skip=(ref,))
    nets = {p.GetNetname() for p in f.Pads()}
    polys = [o for o, zn in pours(b, side) if zn not in nets]
    geoms = {rot: _local_geom(f, side, rot) for rot in (0, 90, 180, 270)}
    if not tg:                                   # nothing to pull toward: region centre
        tg = {'*': [((region[0] + region[2]) / 2, (region[1] + region[3]) / 2)]}
    allpts = [q for v in tg.values() for q in v]
    cx = sum(q[0] for q in allpts) / len(allpts)
    cy = sum(q[1] for q in allpts) / len(allpts)
    best = None
    xs = [region[0] + 0.5 * i for i in range(int((region[2] - region[0]) / 0.5) + 1)]
    ys = [region[1] + 0.5 * j for j in range(int((region[3] - region[1]) / 0.5) + 1)]
    for stage in (0, 1):
        if stage == 1:
            if best is None:
                break
            xs = [round(best[1] + 0.1 * i, 2) for i in range(-5, 6)]
            ys = [round(best[2] + 0.1 * j, 2) for j in range(-5, 6)]
        for x in xs:
            for y in ys:
                for rot, (bx, pads) in geoms.items():
                    box = (bx[0] + x, bx[1] + y, bx[2] + x, bx[3] + y)
                    if box[0] < region[0] or box[2] > region[2] or box[1] < region[1] or box[3] > region[3]:
                        continue
                    cost = 0.0
                    for num, nn, px, py in pads:
                        pts = tg.get('*') if '*' in tg else tg.get(num)
                        if not pts or (('*' in tg) and (nn in ('GND', '') and len(pads) > 1)):
                            continue
                        cost += min(math.hypot(px + x - qx, py + y - qy) for qx, qy in pts)
                    cost += 0.02 * math.hypot(x - cx, y - cy)
                    if best is not None and cost >= best[0]:
                        continue
                    if _fits(box, rects, circs, region, polys):
                        best = (cost, x, y, rot)
    if best is None:
        return False
    place(b, ref, best[1], best[2], best[3], side)
    return True


PLACE_TSV = Path(__file__).resolve().parent / 'r5_place.tsv'

# Manual moves applied after the frozen table (critical routing, review fixes): (ref, x, y, rot, side).
OVERRIDES = [
    # load-switch gate network beside the source pour's right corner: source pins toward the pour, gate pins
    # outward, so Q121's gate link (below them) and the source pour never cross (power())
    ('C120', 8.15, 16.0, 0, 'B'), ('R120', 6.65, 17.3, 0, 'B'),     # (R120 1 mm west: room for C88's GND via)
    # BAT_ENABLE's test pad on the top beside R165 and C87 (BAT_ENABLE is on the top only; auto-placed on the bottom
    # it sat right under C87.1, where no via fits)
    ('TP84', 2.4, 21.9, 0, 'F'),
    # BAT_FAULT_N's test pad in the row under U1 by its MCU pin 81 (auto-placed, it sat 17 mm from U9's end and 10 mm
    # from the MCU's, and no router reached it)
    ('TP85', 16.4, 40.0, 0, 'B'),
]


def prune_stubs(b):
    """Remove moved block copper left dangling (repeat until stable): a segment end that touches no pad,
    via or other segment of its net, and a via that reaches copper on fewer than two layers (GND vias
    count the In1 plane as one)."""
    def pads_at(netname, pos, layer):
        return any(p.GetNetname() == netname and p.IsOnLayer(layer) and p.HitTest(pos)
                   for f in b.GetFootprints() for p in f.Pads())
    while True:
        items = [t for t in b.GetTracks() if t.GetNetname() in BLOCK_NETS]
        segs = [t for t in items if t.GetClass() != 'PCB_VIA']
        vias = [t for t in items if t.GetClass() == 'PCB_VIA']
        dead = []
        for t in segs:
            for e in (t.GetStart(), t.GetEnd()):
                hit = any(o is not t and o.GetNetname() == t.GetNetname() and o.GetLayer() == t.GetLayer() and
                          (o.GetStart() == e or o.GetEnd() == e or o.HitTest(e, 1)) for o in segs)
                hit = hit or any(v.GetNetname() == t.GetNetname() and (v.GetPosition() - e).EuclideanNorm() < MM(0.01)
                                 for v in vias)
                hit = hit or pads_at(t.GetNetname(), e, t.GetLayer())
                if not hit:
                    dead.append(t)
                    break
        for v in vias:
            layers = {s.GetLayer() for s in segs if s.GetNetname() == v.GetNetname() and
                      min((v.GetPosition() - s.GetStart()).EuclideanNorm(),
                          (v.GetPosition() - s.GetEnd()).EuclideanNorm()) < MM(0.01)}
            layers |= {lay for lay in (pcbnew.F_Cu, pcbnew.B_Cu) if pads_at(v.GetNetname(), v.GetPosition(), lay)}
            if v.GetNetname() == 'GND':
                layers.add(pcbnew.In1_Cu)
            if len(layers) < 2:
                dead.append(v)
        if not dead:
            return
        for t in dead:
            b.Delete(t)


PLANE_NETS = {'GND', '3V3', '3V3A', 'BAT_IN', 'RAW_ACT', 'CAM_5V'}


def drop_single_layer_vias(b):
    """A scripted via whose copper (tracks, or its own pad, e.g. the bottom gate test pads TP122/TP123 that
    R4 reaches through a via in the pad) is all on one layer, and that sits in no plane or pour of its net, is not
    needed."""
    segs = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA']
    planes = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() in PLANE_NETS]
    for v in [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']:
        p = v.GetPosition()
        if any(z.GetNetname() == v.GetNetname() and z.Outline().Contains(p) for z in planes):
            continue                                  # reaches its plane or pour
        if (round(mm(p.x), 3), round(mm(p.y), 3)) in r5_routes.KEEP_VIAS:
            continue                                  # a fan-out via the autorouter continues from
        layers = {s.GetLayer() for s in segs if s.GetNetname() == v.GetNetname() and
                  min((s.GetStart() - p).EuclideanNorm(), (s.GetEnd() - p).EuclideanNorm()) < MM(0.01)}
        layers |= {lay for f in b.GetFootprints() for q in f.Pads() if q.GetNetname() == v.GetNetname() and
                   q.HitTest(p) for lay in (pcbnew.F_Cu, pcbnew.B_Cu) if q.IsOnLayer(lay)}
        if len(layers) < 2:
            b.Delete(v)


def place_manual(b):
    """The PLACE tables (hand-placed parts); everything else is parked off the board until place_rest."""
    manual = {p[0] for p in PLACE + PLACE_B + PLACE_T} | set(PYRO_BLOCK)
    k = 0
    for f in b.GetFootprints():
        if f.GetReference() not in manual:
            place(b, f.GetReference(), 60 + (k % 10) * 6, 2 + (k // 10) * 5, 0, 'F')
            k += 1
    for ref, x, y, rot, side in PLACE:
        place(b, ref, x, y, rot, side)
    for ref, x, y, rot in PLACE_B:
        place(b, ref, x, y, rot, 'B')
    for ref, x, y, rot in PLACE_T:
        place(b, ref, x, y, rot, 'F')


def place_rest(b, autoplace_now=False):
    """Either the auto-placer (autoplace_now; it keeps clear of the scripted copper) or the frozen table
    r5_place.tsv it wrote, then OVERRIDES."""
    auto = [r for g in AUTO for r in g[0].split()]
    if autoplace_now or not PLACE_TSV.exists():
        for refs, reg, anchors in AUTO:
            for r in refs.split():
                autoplace(b, r, reg, anchors)
        with open(PLACE_TSV, 'w') as fh:
            fh.write('# ref\tx\ty\trot\tside   (written by r5_pcb.py --autoplace; do not edit, use OVERRIDES)\n')
            for r in auto:
                f = fp_of(b, r)
                fh.write(f'{r}\t{mm(f.GetPosition().x):.3f}\t{mm(f.GetPosition().y):.3f}\t'
                         f'{f.GetOrientationDegrees():.1f}\t{"B" if f.IsFlipped() else "F"}\n')
    else:
        for line in PLACE_TSV.read_text().splitlines():
            if line.startswith('#') or not line.strip():
                continue
            r, x, y, rot, side = line.split('\t')
            if r in auto:                             # (a part since placed by hand keeps its PLACE entry)
                place(b, r, float(x), float(y), float(rot), side)
        listed = {ln.split('\t')[0] for ln in PLACE_TSV.read_text().splitlines() if ln and not ln.startswith('#')}
        for refs, reg, anchors in AUTO:                  # parts new to the auto list since the table was written
            for r in refs.split():
                if r not in listed:
                    autoplace(b, r, reg, anchors)
                    print(f'  placed {r} (not in the frozen table)')
    for ref, x, y, rot, side in OVERRIDES:
        place(b, ref, x, y, rot, side)
    left = [f.GetReference() for f in b.GetFootprints() if mm(f.GetPosition().x) > W + 1]
    assert not left, f'not placed: {left}'
    repair_overlaps(b)


def _overlap(a, c):
    return a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]


def repair_overlaps(b):
    """An auto-placed part whose courtyard a later manual move (PLACE tables, OVERRIDES) or a tie hole overlaps is placed
    again by the auto-placer (deterministic; the frozen table keeps every other part where it was)."""
    fixed = {r for g in (PLACE, PLACE_B, PLACE_T) for r in (x[0] for x in g)} | set(PYRO_BLOCK) | \
        {o[0] for o in OVERRIDES}
    copper = [t for t in b.GetTracks()]
    for refs, reg, anchors in AUTO:
        for r in refs.split():
            f = fp_of(b, r)
            if r in fixed:
                continue
            bx = _box(f)
            hit = [g.GetReference() for g in b.GetFootprints() if g.GetReference() != r and
                   g.IsFlipped() == f.IsFlipped() and _overlap(bx, _box(g))]
            hit += ['tie hole' for h in ZIP if _rect_gap(bx, (h[0], h[1], h[0], h[1])) < ZIP_R]
            lay = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
            for p in f.Pads():                        # scripted copper of another net under a pad (it moved since)
                pb = p.GetBoundingBox()
                pb.Inflate(MM(0.2))
                if any(t.GetNetname() != p.GetNetname() and (t.GetClass() == 'PCB_VIA' or t.GetLayer() == lay) and
                       pb.Intersects(t.GetBoundingBox()) and t.HitTest(pb, False) for t in copper):
                    hit.append('copper')
                    break
            if hit:
                x, y = mm(f.GetPosition().x), mm(f.GetPosition().y)
                rest = sorted((k for k in REG if k not in reg.split('/')), key=lambda k: _region_dist(k, x, y))
                autoplace(b, r, '/'.join(reg.split('/') + rest), anchors)     # its regions, then the nearest
                print(f'  re-placed {r} (overlapped {" ".join(hit)}): ({x:.2f}, {y:.2f}) -> '
                      f'({mm(f.GetPosition().x):.2f}, {mm(f.GetPosition().y):.2f}) {"B" if f.IsFlipped() else "F"}')


def _region_dist(k, x, y):
    x0, y0, x1, y1 = REG[k][1]
    return math.hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1))


# --- 4/5. rule areas and zones -------------------------------------------------------------------

def _layerset(layers):
    ls = pcbnew.LSET()
    for layer in layers:
        ls.AddLayer(layer)
    return ls


def add_zone(b, netname, layers, pts, prio, name, clr=0.25, minw=0.2, conn=pcbnew.ZONE_CONNECTION_THERMAL,
             tgap=0.25, spoke=0.4):
    z = pcbnew.ZONE(b)
    z.SetLayerSet(_layerset(layers))
    z.SetNet(net(b, netname))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(MM(x), MM(y))
    z.SetLocalClearance(MM(clr))
    z.SetMinThickness(MM(minw))
    z.SetPadConnection(conn)
    z.SetThermalReliefGap(MM(tgap))
    z.SetThermalReliefSpokeWidth(MM(spoke))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetAssignedPriority(prio)
    z.SetZoneName(name)
    assert not ol.IsSelfIntersecting(), f'zone {name}: outline crosses itself'
    b.Add(z)
    return z


def rule_area(b, name, layers, pts, tracks=False, vias=False, fill=False, footprints=False):
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetLayerSet(_layerset(layers))
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowZoneFills(fill)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(footprints)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(MM(x), MM(y))
    b.Add(z)
    return z


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


CU4 = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)


def zones(b):
    """In1: one GND plane. In2: power islands (BAT_IN, RAW_ACT, 3V3, 3V3A, CAM_5V). Outer layers: power pours
    (made here, before any route, so that the scripted router and Freerouting keep out of them) and GND pours
    (which fill round everything). The filler honours the pyro DRC rules (RAW_ACT 1.0 mm from bus/igniter
    copper, and so on)."""
    rule_area(b, 'PYRO_BLOCK', CU4, rect(4.0, 66.0, 42.0, 96.4))    # rule G's scope; restricts nothing
    for side, layer in (('F', pcbnew.F_Cu), ('B', pcbnew.B_Cu)):
        for r, nm in (('U4', 'IMU_body'), ('U5', 'BARO_body')):
            f = fp_of(b, r)
            if f.IsFlipped() == (side == 'B'):
                x0, y0, x1, y1 = _box(f)
                rule_area(b, f'{nm}_{side}', (layer,), rect(x0 + 0.25, y0 + 0.25, x1 - 0.25, y1 - 0.25), vias=True, fill=True)
    edge = rect(0.3, 0.3, W - 0.3, L - 0.3)
    add_zone(b, 'GND', (pcbnew.In1_Cu,), edge, 1, 'GND_In1')
    # the outer GND pours keep the board's 0.15 mm clearance and fill down to 0.15 mm, so they reach between the dense
    # traces (at R4's 0.25/0.2 mm they left SMD GND pads on cut-off islands; the pyro rules still apply through DRC)
    add_zone(b, 'GND', (pcbnew.F_Cu,), edge, 0, 'GND_F', clr=0.15, minw=0.15, conn=pcbnew.ZONE_CONNECTION_THT_THERMAL,
             tgap=0.5, spoke=0.5)
    add_zone(b, 'GND', (pcbnew.B_Cu,), edge, 0, 'GND_B', clr=0.15, minw=0.15, conn=pcbnew.ZONE_CONNECTION_THT_THERMAL,
             tgap=0.5, spoke=0.5)
    In2 = (pcbnew.In2_Cu,)
    # BAT_IN: J1.1 -> the In2 island and a B.Cu pour round Q120's drains and D8 (stitched), an F.Cu pour over the
    # input damper only (U9's pins stay free). The island stops at y 15 left of x 9 so Q120's gate can cross to Q121's
    # under the source pour; a 0.9 mm strip (x 9-9.9: U9's input, about 1.5 A at most, and the bulk capacitors) runs
    # south past U9, leaving In2 under U9's pins free for their vias (a tab at y 25.4-27 takes R82's via).
    add_zone(b, 'BAT_IN', In2, [(0.3, 0.3), (15.0, 0.3), (15.0, 14.6), (9.9, 14.6), (9.9, 25.4), (10.5, 25.4),
                                (10.5, 27.0), (9.9, 27.0), (9.9, 37.0), (9.0, 37.0), (9.0, 15.0), (0.3, 15.0)], 5,
             'BAT_IN_In2',
             clr=0.3, minw=0.3, conn=pcbnew.ZONE_CONNECTION_FULL)
    full = dict(clr=0.3, minw=0.3, conn=pcbnew.ZONE_CONNECTION_FULL)
    add_zone(b, 'BAT_IN', (pcbnew.B_Cu,), [(0.6, 2.9), (13.6, 2.9), (13.6, 16.4), (10.2, 16.4), (10.2, 14.9),
                                           (0.6, 14.9)], 30, 'BAT_IN_B', **full)
    # (to x 9.0: the strip east of the damper capacitors keeps the pour whole where their BAT_DAMP links cross it)
    add_zone(b, 'BAT_IN', (pcbnew.F_Cu,), rect(4.4, 7.7, 9.0, 18.9), 30, 'BAT_IN_F', **full)
    # the actuator load switch: a B.Cu pour joins the two FETs' sources (7.7 A), another takes Q121's drains to
    # the In2 RAW_ACT strip through a via row
    # (notched round the two gate pins: Q120's at the upper left, Q121's at the lower right; C120's source pin
    # sits in the pour's right end)
    add_zone(b, 'ACT_FET_S', (pcbnew.B_Cu,), [(2.7, 15.3), (7.5, 15.3), (7.5, 16.9), (5.3, 16.9), (5.3, 25.0),
                                              (1.3, 25.0), (1.3, 16.8), (2.7, 16.8)], 30, 'ACT_FET_S_B', **full)
    add_zone(b, 'RAW_ACT', (pcbnew.B_Cu,), rect(0.6, 25.6, 7.2, 32.8), 30, 'RAW_ACT_B', **full)
    # RAW_ACT (servo feed and the ARM terminals' RAW pins): Q121 -> In2 left strip (tabs to the RAW pins and
    # R177; its top corner is cut back for the load-switch gate's In2 crossing, where it carries no current); to J122 an F.Cu band and a column between J122's GND and signal pins, stitched to the strip, so
    # In2 stays open between the pyro block and the MCU for the pyro exits and the MCU's forward-pin vias.
    add_zone(b, 'RAW_ACT', In2, [(0.3, 25.4), (5.5, 25.4), (5.5, 26.6), (8.6, 26.6), (8.6, 70.3), (11.8, 70.3), (11.8, 75.0), (8.6, 75.0),
                                 (8.6, 85.6), (11.8, 85.6), (11.8, 92.8), (8.6, 92.8), (8.6, 96.4), (0.3, 96.4)],
             6, 'RAW_ACT_In2', clr=0.3, minw=0.3, conn=pcbnew.ZONE_CONNECTION_FULL)
    add_zone(b, 'RAW_ACT', (pcbnew.F_Cu,), [(4.6, 63.2), (21.5, 63.2), (21.5, 53.9), (24.5, 53.9), (24.5, 67.8),
                                           (21.0, 67.8), (21.0, 69.8), (4.6, 69.8)],
             30, 'RAW_ACT_F', clr=0.3, minw=0.3, conn=pcbnew.ZONE_CONNECTION_FULL)
    add_zone(b, '3V3', In2, [(9.2, 9.0), (34.5, 9.0), (34.5, 52.2), (9.2, 52.2)], 2, '3V3_In2')
    add_zone(b, '3V3A', In2, rect(31.0, 52.6, 38.6, 65.6), 3, '3V3A_In2')
    # CAM_5V (1 A): a 1.8 mm In2 strip from the buck's output up to J9.1 (about 16 mOhm), leaving room for vias
    # (narrowed to x 39.2-40.4 beside and below U7 so its fault and current-limit pins can drop vias)
    add_zone(b, 'CAM_5V', In2, [(38.6, 15.4), (40.4, 15.4), (40.4, 89.0), (38.6, 89.0), (38.6, 73.0), (39.2, 73.0),
                                (39.2, 65.5), (38.6, 65.5), (38.6, 24.8), (34.6, 24.8), (34.6, 21.4), (38.6, 21.4)],
             4, 'CAM_5V_In2', clr=0.3, minw=0.3, conn=pcbnew.ZONE_CONNECTION_FULL)


def main():
    pcbnew.KIID.SeedGenerator(5101)   # new items' UUIDs repeat from build to build (each script has its own seed)
    b = pcbnew.LoadBoard(PCB)
    try:
        build(b)
    except Exception:
        pcbnew.SaveBoard(PCB.replace('.kicad_pcb', '_failed.kicad_pcb'), b)   # for debugging the failed step
        raise
    pcbnew.SaveBoard(PCB, b)
    print('saved', PCB)
    print('  necked legs:', len(r5_routes.NECKS), ' left to the autorouter:', r5_routes.SKIPPED)


# Through-hole GND pins whose outer-layer thermal spokes are starved keep a full connection (REQUIREMENTS M2,
# M3_R4 section 2; R4 already does this for J122.12, J2.1 and J3 leg 4): J122.3 sits between the RAW_ACT column
# and the F.Cu feed band, so the GND pour reaches it from one side only (J122.6 and .9 likewise, between the column
# and the S pins' lanes); J123.2 (the pull-pin's GND) sits in the aft-edge strip between J1's body and the hole;
# J3's shell leg 1 sits between the board edge, its own locating hole and the USB fan-out on B.Cu; J9.2 (the camera's
# GND) between the GND vias of its neighbours.
FULL_PADS = [('J122', '3'), ('J122', '6'), ('J122', '9'), ('J123', '2'), ('J3', '1'), ('J9', '2')]


def pad_connections(b):
    for ref, num in FULL_PADS:
        p = next(q for q in fp_of(b, ref).Pads() if q.GetNumber() == num)
        p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)


def escape_bands(b, depth=1.2):
    """r5_maze.BANDS: a band `depth` mm wide outside U1's right-hand pin row on F.Cu (the pad ends): a scripted route
    (QSPI_IO2 from pin 1) had run along it and boxed in pins 7, 8 and 22-24. On B.Cu, bands under and outside both
    side rows keep the pins' fan-out vias possible (VLOGIC had run under the left row), and on In2 bands outside
    them."""
    import r5_maze
    f = fp_of(b, 'U1')
    cx, cy = mm(f.GetPosition().x), mm(f.GetPosition().y)
    pads = [(mm(p.GetBoundingBox().GetX()), mm(p.GetBoundingBox().GetY()), mm(p.GetBoundingBox().GetRight()),
             mm(p.GetBoundingBox().GetBottom())) for p in f.Pads()]
    x0, y0 = min(p[0] for p in pads), min(p[1] for p in pads)
    x1, y1 = max(p[2] for p in pads), max(p[3] for p in pads)
    r5_maze.BANDS[:] = [(pcbnew.F_Cu, (x1, y0, x1 + depth, y1), 'x', 'U1'),
                        # the fan-out vias of the side rows also need B.Cu clear under and outside the pads
                        (pcbnew.B_Cu, (x1 - 1.0, y0, x1 + depth, y1), 'x', 'U1'),
                        (pcbnew.B_Cu, (x0 - depth, y0, x0 + 1.0, y1), 'x', 'U1'),
                        # ... and In2 outside them (a sense link run along the right-hand row on In2 had taken the
                        # GND and decoupling vias' spots of pins 17-24)
                        (pcbnew.In2_Cu, (x1, y0, x1 + depth, y1), 'x', 'U1'),
                        (pcbnew.In2_Cu, (x0 - depth, y0, x0, y1), 'x', 'U1')]


def build(b):
    keep = strip(b)
    outline(b)
    move_pyro_block(b, keep)
    place_manual(b)
    prune_stubs(b)
    zones(b)
    escape_bands(b)
    r5_routes.usb(b)
    r5_routes.crystal(b)
    r5_routes.pyro_exits(b)
    place_rest(b, '--autoplace' in sys.argv)
    r5_routes.early_escapes(b)
    r5_routes.buck_loops(b)
    r5_routes.u9_escapes(b)
    r5_routes.u9_network(b)
    r5_routes.raw_act_link(b)
    r5_routes.power_main(b)
    r5_routes.usb_limited(b)
    r5_routes.sensor_links(b)
    r5_routes.decoupling_vias(b)
    r5_routes.gnd_pin_vias(b, r5_routes.GND_PIN_EARLY)
    r5_routes.sense_mcu_links(b)
    r5_routes.qspi_spi(b)
    r5_routes.slow_links(b)
    r5_routes.decoupling(b)
    r5_routes.feed_3v3(b)
    r5_routes.power(b)
    r5_routes.power2(b)
    r5_routes.gnd_pin_vias(b)
    r5_routes.gnd_pin_vias(b, r5_routes.GND_PIN_TRACK, own_via=False)
    r5_routes.long_links(b)
    r5_routes.gnd_pin_vias(b, r5_routes.GND_PIN_LAST)
    r5_routes.return_vias(b)
    drop_single_layer_vias(b)
    pad_connections(b)
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


if __name__ == '__main__':
    main()
