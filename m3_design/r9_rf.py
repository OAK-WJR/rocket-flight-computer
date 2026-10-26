#!/usr/bin/env python3
"""Build the R9 RF strip copper (M3-ASSY-R9, build step 4) on the step-3 placement board.

usage: <KiCad python3> -I m3_design/r9_rf.py [--board m3_design/assembly_review/m3.kicad_pcb] [--out OUT]
       design aids (r9_build.sh never passes them): --no-fill, --no-board-vias (leave out the fence and the grid)

r9_plan.md section 4 step 4; R9_OWNER_DECISIONS.md item 3 (strip y 0-22.0); R9_DECISIONS.md D-S4-*. The board is
rebuilt in place (the project's m3.kicad_pro and m3.kicad_dru apply while it is filled). Every number below is in
the frame of the part it belongs to, so the copper is a template regenerated wherever r9_place.tsv puts that part:

  jack frames   J30 / J31 (rotation 0 on the aft edge): x relative to the jack axis, y board y (the jack sits at
                y 0, check_r9 R-3). The launch (In1 cut-out, its eight GND vias) and the RF chain (ESD, bias tap,
                pi network, their GND vias) are R7's qualified geometry in that frame (D-S4-01).
  module frames U30 (rotation 90) / U31 (rotation 180): x, y relative to the module centre. Each module's own
                copper: its supply and decoupling, its strip-internal leads, U31's TXEN loop and U30's limiter.
  board         the GND pours, the fence on y_f and the strip stitching grid.
PARTS lists every strip part with its frame position (asserted against the board, so a placement change cannot
leave the copper behind). The step draws only strip-internal nets (every pad of the net lies in the strip, y < y_f;
D-S4-05); the interface nets that cross y_f (U1 to the modules, the 3V3 feeds of FB30 / FB31) are step 7's family
rf_if: it opens lane gaps in the fence (FENCE_X) and routes inside the lane corridors this step keeps free
(CORRIDORS).

Copper:
  - rule areas: U30_KEEPOUT (F.Cu, In1) and U31_KEEPOUT (F.Cu, In1 the pad-ring interior; In2, B.Cu the body),
    derived from the footprints exactly as check_r9 R-8 derives the regions it requires (check_r9.module_regions);
    the In1 launch cut-out of each jack (check_r9.LAUNCH, no fill);
  - pours: GND on all four layers over the strip to STRIP_POUR_Y (R7 / R8's settings per layer); step 8 extends
    F.Cu, B.Cu and In1 over the board, step 6 owns In2 forward of it (D-S4-07);
  - the two RF lines (W 0.30 GCPW, check_r9.RF_W) and their stubs, the ANT_DC feed, the limiter (B.Cu under U30,
    D-S4-03), the module leads (D-S4-06);
  - GND vias: the launches, the RF ground pads' vias, the side stitching (check_r9 R-7), the fence on y_f, the strip
    grid, the GND partners of the critical layer changes.
Deterministic (fixed KIID seed, tables only): a rebuild reproduces the board byte for byte.
"""
import argparse
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r9 as C9  # noqa: E402

PROJECT = ROOT / 'm3_design/assembly_review'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
KIID_SEED = 9904
LAYER = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}
W_SIG, W_RF, W_RAIL, W_RAIL_R, W_DC = 0.2, C9.RF_W, 0.30, 0.40, 0.25
W_TXEN = W_SIG                                      # R7's loop at the signal width, not R7's 0.15 (R9P1-ROUTING-01)
W_Q30 = 0.40                                        # Q30's drain lead: copper for its short-circuit dissipation (D-S4-03)
VIA_SIG, VIA_GND = (0.5, 0.3), (0.6, 0.3)          # R8's signal / fence vias; R7's strip GND vias
FRAME_ROT = {'J30': 0.0, 'J31': 0.0, 'U30': 90.0, 'U31': 180.0}
STRIP_POUR_Y = 23.0                                 # the strip pours' forward edge (beyond the fence row, D-S4-07)
EPS = 1e-4

# ---------------------------------------------------------------------------------------------------------------------
# Parts in their frames: ref -> (frame, dx, dy, rotation, side). The values r9_place.tsv must hold (asserted).
PARTS = {
    # GNSS chain, J30 frame (D-S4-01, D-S4-02): R7's rows (ESD y 5.2, bias tap 6.18, pi 7.13), the line on the jack
    # axis, R304 jogging +0.86 onto U30.11; D30's GND pad and L30's cold end west, both pi shunts east (C303 at the
    # bias-tap node, turned so its GND end hangs aft)
    'D30': ('J30', -0.325, 5.2, 180.0, 'F'),
    'L30': ('J30', -0.463, 6.18, 0.0, 'F'),
    'C302': ('J30', -2.27, 6.18, 180.0, 'F'),
    'C303': ('J30', 0.94, 5.76, 90.0, 'F'),
    'R304': ('J30', 0.43, 7.13, 0.0, 'F'),
    'C305': ('J30', 2.22, 7.13, 0.0, 'F'),
    # radio chain, J31 frame: R7's chain exactly (R8's positions)
    'D31': ('J31', 0.325, 5.2, 0.0, 'F'),
    'R316': ('J31', 0.43, 7.6, 0.0, 'F'),
    'C313': ('J31', -1.36, 7.6, 180.0, 'F'),
    'C314': ('J31', 2.22, 7.6, 0.0, 'F'),
    # U30 frame: the GNSS supply / interface row (step 3, D-S3-04) and the limiter on B.Cu (D-S4-03)
    'R305': ('U30', -3.73, 6.88, 180.0, 'F'),
    'R307': ('U30', -1.63, 6.88, 180.0, 'F'),
    'C300': ('U30', 0.65, 7.16, 180.0, 'F'),
    'C301': ('U30', 2.88, 6.88, 180.0, 'F'),
    'FB30': ('U30', 4.86, 7.01, 180.0, 'F'),
    'TP30': ('U30', -9.15, -4.45, 0.0, 'F'),
    'R300': ('U30', -2.375, -6.65, 180.0, 'B'),
    'Q32': ('U30', -3.1, -4.15, 90.0, 'B'),           # 0.1 west of D-S4-03's spot: outline clear of Q30's (D-S9-01)
    'Q30': ('U30', 0.15, -3.9, -90.0, 'B'),
    'R301': ('U30', 0.15, -1.6, 0.0, 'B'),
    'R303': ('U30', 2.05, -6.13, 0.0, 'B'),
    'Q31': ('U30', 3.38, -3.95, 90.0, 'B'),           # 0.15 east of D-S4-03's spot: outline clear of Q30's (D-S9-01)
    'R302': ('U30', 2.37, -1.0, 0.0, 'B'),
    'C304': ('U30', -1.55, -0.08, -90.0, 'B'),
    # U31 frame: R8's radio parts (FB31 turned forward of U31 in step 3)
    'C310': ('U31', 7.92, 5.6, 0.0, 'F'),
    'C311': ('U31', 7.34, 2.54, 0.0, 'F'),
    'C312': ('U31', 7.34, 3.5, 0.0, 'F'),
    'R311': ('U31', 7.14, 0.43, -90.0, 'F'),
    'R312': ('U31', -4.06, -6.85, 90.0, 'F'),
    'R314': ('U31', -6.86, -1.27, 180.0, 'F'),
    'FB31': ('U31', 4.54, 6.95, 0.0, 'F'),
}
# where the chains differ from R7's in the jack frame (r9_rf_check gate r7 fails on any other difference)
R7_DEVIATIONS = {
    'D30': 'turned 180 degrees: its GND pad west of the line, so the east side keeps a stitching spot (D-S4-02)',
    'C303': 'the pi network\'s first shunt at the bias-tap node, east of the line, turned 90 degrees with its GND end '
            'aft: the west side is free for the limiter vias and the east keeps a stitching spot (D-S4-02)',
}
# the frames themselves: the jacks on the aft edge, U30.11 on the GNSS line's module segment (J30 + 0.86), U31.6 on the
# radio's (J31 + 0.86)
LINKS = (('J30', 'U30', '11', 0.86), ('J31', 'U31', '6', 0.86))

# ---------------------------------------------------------------------------------------------------------------------
# Copper: (frame, net, layer, width, [(dx, dy), ...]) polylines and (frame, net, dx, dy, size, basis) vias.
GNSS_RF = [
    ('J30', 'GNSS_RF_ANT', 'F', W_RF, [(0, 2.3), (0, 6.18)]),            # jack pad centre to L30's line pad
    ('J30', 'GNSS_RF_ANT', 'F', W_RF, [(0, 6.18), (0, 7.13)]),           # on to R304.1
    ('J30', 'GNSS_RF_ANT', 'F', W_RF, [(0, 6.18), (0.94, 6.18)]),        # C303's stub (0.94, R7's length)
    ('J30', 'GNSS_RF_IN', 'F', W_RF, [(0.86, 7.13), (0.86, 9.3)]),       # R304.2 to U30.11 (pad centre, y 9.3)
    ('J30', 'GNSS_RF_IN', 'F', W_RF, [(0.86, 7.13), (1.80, 7.13)]),      # C305's stub
    ('J30', 'GNSS_ANT_DC', 'F', W_DC, [(-1.85, 6.18), (-0.925, 6.18)]),  # C302.1 to L30.1 (R7)
    ('J30', 'GNSS_ANT_DC', 'F', W_DC, [(-1.85, 6.18), (-1.85, 6.5), (-2.29, 6.94), (-2.29, 7.4)]),   # to V3
]
RADIO_RF = [
    ('J31', 'RADIO_RF_ANT', 'F', W_RF, [(0, 2.3), (0, 7.6)]),
    ('J31', 'RADIO_RF_ANT', 'F', W_RF, [(0, 7.6), (-0.94, 7.6)]),
    ('J31', 'RADIO_RF', 'F', W_RF, [(0.86, 7.6), (0.86, 9.05)]),
    ('J31', 'RADIO_RF', 'F', W_RF, [(0.86, 7.6), (1.80, 7.6)]),
]
# U30 (centre (11.15, 14.05) in the step-3 table; rotation 90): pins 1-9 forward at dy +4.75, dx -4.4 + 1.1 (n - 1);
# pins 10-18 aft at dy -4.75, dx +4.4 - 1.1 (n - 10)
U30_COPPER = [
    ('U30', 'GNSS_TXD', 'F', W_SIG, [(-3.3, 4.75), (-3.3, 6.88)]),                       # pin 2 -> R305.1
    ('U30', 'GNSS_TIMEPULSE', 'F', W_SIG, [(-1.15, 4.75), (-1.15, 6.88)]),               # pin 4 -> R307.1 (D-S4-06)
    ('U30', 'GNSS_SAFEBOOT_N', 'F', W_SIG, [(-4.4, -4.75), (-8.85, -4.75), (-9.15, -4.45)]),   # pin 18 -> TP30
    # 3V3_GNSS (D-S4-06): pin 8 straight up to C301.1, on to FB30.2; pins 7 / 8 joined just beyond their pad ends,
    # under their own T-paste (R7 / R8's join); C300.1 off pin 7 by one 45-degree run
    ('U30', '3V3_GNSS', 'F', W_RAIL, [(3.3, 4.75), (3.3, 5.9)]),
    ('U30', '3V3_GNSS', 'F', W_RAIL, [(3.3, 5.9), (3.3, 6.95)]),
    ('U30', '3V3_GNSS', 'F', W_RAIL, [(3.3, 6.95), (4.21, 6.95)]),
    ('U30', '3V3_GNSS', 'F', W_SIG, [(3.3, 5.9), (2.2, 5.9)]),
    ('U30', '3V3_GNSS', 'F', W_SIG, [(2.2, 4.75), (2.2, 5.9)]),
    ('U30', '3V3_GNSS', 'F', W_SIG, [(2.2, 5.9), (1.35, 6.75), (1.35, 7.16)]),
    ('U30', 'GND', 'F', W_RAIL, [(2.46, 6.88), (2.46, 7.6)]),    # C301.2 -> its via (boxed: D-S4-06)
]

# the antenna-bias limiter (D-S4-03): pins 14 (VCC_RF) and 13 (LNA_EN) drop aft of the T-paste to vias V1 / V2,
# ANT_DC rises from C302 to V3 between them; on B.Cu the cluster sits forward of the vias under U30, each net entering
# at the pad nearest its via (no lead doubles back: route_check detour)
LIMITER = [
    ('U30', 'GNSS_VCC_RF', 'F', W_DC, [(0.0, -4.75), (0.0, -5.9), (-0.75, -6.65)]),     # pin 14 -> V1
    ('U30', 'GNSS_LNA_EN', 'F', W_SIG, [(1.1, -4.75), (1.1, -6.65)]),                   # pin 13 -> V2
    ('U30', 'GNSS_VCC_RF', 'B', W_DC, [(-0.75, -6.65), (-1.55, -6.65)]),                # V1 -> R300.1
    ('U30', 'GNSS_VCC_RF', 'B', W_DC, [(-1.55, -6.65), (-1.55, -5.75), (-2.15, -5.15)]),   # R300.1 -> Q32.E
    ('U30', 'GNSS_ANT_SRC', 'B', W_DC, [(-3.2, -6.65), (-3.2, -6.0), (-4.05, -5.15)]),      # R300.2 -> Q32.B
    ('U30', 'GNSS_ANT_SRC', 'B', W_DC, [(-4.05, -5.15), (-3.05, -4.15), (-2.05, -4.15), (-0.8, -2.9)]),  # -> Q30.S
    ('U30', 'GNSS_ANT_SRC', 'B', W_SIG, [(-0.8, -2.9), (-0.8, -2.12), (-0.28, -1.6)]),  # Q30.S -> R301.1
    ('U30', 'GNSS_ANT_DC', 'B', W_Q30, [(0.15, -6.65), (0.15, -4.9)]),                  # V3 -> Q30.D (drain)
    ('U30', 'GNSS_ANT_GATE', 'B', W_SIG, [(1.1, -2.9), (1.1, -2.12), (0.58, -1.6)]),    # Q30.G -> R301.2
    ('U30', 'GNSS_ANT_GATE', 'B', W_SIG, [(0.58, -1.6), (0.58, -1.0)]),                 # R301.2 -> trunk
    ('U30', 'GNSS_ANT_GATE', 'B', W_SIG, [(-3.1, -3.15), (-3.1, -1.0), (-1.55, -1.0)]),  # Q32.C -> trunk
    ('U30', 'GNSS_ANT_GATE', 'B', W_SIG, [(-1.55, -1.0), (0.58, -1.0)]),
    ('U30', 'GNSS_ANT_GATE', 'B', W_SIG, [(0.58, -1.0), (1.94, -1.0)]),                 # -> R302.1
    ('U30', 'GNSS_ANT_GATE', 'B', W_SIG, [(-1.55, -1.0), (-1.55, -0.5)]),               # -> C304.1
    ('U30', 'GNSS_ANT_PD', 'B', W_SIG, [(3.38, -2.95), (3.38, -1.58), (2.80, -1.0)]),   # Q31.D -> R302.2
    ('U30', 'GNSS_LNA_EN', 'B', W_SIG, [(1.1, -6.65), (1.62, -6.13)]),                  # V2 -> R303.1
    # R303.1 -> Q31.G: D-S4-03's 0.52 mm rise clear of R303.2, then 45 degrees into Q31.G (0.15 east, D-S9-01), ending
    # 0.15 mm short of the pad centre: ending on it would cut the rise to a 0.37 mm tiny jog
    ('U30', 'GNSS_LNA_EN', 'B', W_SIG, [(1.62, -6.13), (1.62, -5.61), (2.43, -4.80)]),
]
LIMITER_VIAS = [('U30', 'GNSS_VCC_RF', -0.75, -6.65, VIA_SIG, 'V1'),
                ('U30', 'GNSS_LNA_EN', 1.1, -6.65, VIA_SIG, 'V2'),
                ('U30', 'GNSS_ANT_DC', 0.15, -6.65, VIA_SIG, 'V3')]
# U31 (centre (30.61, 14.0), rotation 180): R8's module copper in U31's frame; 3V3_RADIO re-drawn for step 3's FB31
U31_COPPER = [
    ('U31', '3V3_RADIO', 'F', W_RAIL_R, [(5.19, 6.95), (6.54, 5.6), (6.92, 5.6)]),     # FB31.2 -> C310.1
    ('U31', '3V3_RADIO', 'F', W_RAIL_R, [(6.92, 5.6), (6.92, 3.5), (6.92, 2.54), (4.95, 2.54)]),   # C312, C311, U31.1
    ('U31', 'RADIO_MISO', 'F', W_SIG, [(-4.95, -1.27), (-6.43, -1.27)]),               # U31.12 -> R314.1
    ('U31', 'RADIO_TXEN', 'F', W_TXEN, [(-1.27, -4.95), (-1.27, -6.2)]),               # U31.9 -> via
    ('U31', 'RADIO_TXEN', 'B', W_TXEN, [(-1.27, -6.2), (-5.06, -6.2), (-5.36, -5.9), (-5.36, 5.85), (-5.06, 6.15),
                                        (1.27, 6.15)]),                                  # R7's loop round U31's west
    ('U31', 'RADIO_TXEN', 'F', W_TXEN, [(1.27, 6.15), (1.27, 4.95)]),                  # via -> U31.19
]
U31_VIAS = [('U31', 'RADIO_TXEN', -1.27, -6.2, VIA_SIG, 'TXEN'), ('U31', 'RADIO_TXEN', 1.27, 6.15, VIA_SIG, 'TXEN')]

# The launch's eight GND vias at R7's built spots (R7's J31: the (+-1.45, 3.6) pair sits at y 3.58, where the 0.6 mm rings
# clear the (+-1.25, 4.15) pair; check_r9 R-4 holds them to LAUNCH within its 0.05 mm)
R7_LAUNCH_VIAS = ((-1.45, 1.0), (1.45, 1.0), (-1.45, 2.3), (1.45, 2.3), (-1.45, 3.58), (1.45, 3.58), (-1.25, 4.15),
                  (1.25, 4.15))
assert all(math.dist(a, c) <= C9.LAUNCH['via_tol'] for a, c in zip(R7_LAUNCH_VIAS, C9.LAUNCH['vias']))
# GND vias in the jack frames
GND_JACK = [
    # R7's strip grid outside the jack legs (x +-3.65, y 1.0 / 2.3 / 3.6)
    *[(j, dx, y, VIA_GND, 'grid') for j in ('J30', 'J31') for dx in (-3.65, 3.65) for y in (1.0, 2.3, 3.6)],
    # GNSS chain (D-S4-04): D30.2's via and the west stitch at the ESD row, the west stitch at the pi row between
    # R304.1 and V2, C303.2's via and the east stitch below it, the east stitch beyond C303 at the bias row, C305.2's
    # via and the east stitch at the module end
    ('J30', -1.3, 5.15, VIA_SIG, 'rf-ground D30.2 / stitch W'),
    ('J30', -0.79, 6.9, VIA_SIG, 'stitch W'),
    ('J30', 1.0, 4.8, VIA_SIG, 'rf-ground C303.2 / stitch E'),
    ('J30', 1.75, 6.18, VIA_SIG, 'stitch E'),
    ('J30', 2.66, 7.7, VIA_SIG, 'rf-ground C305.2 / stitch E'),
    # radio chain: R8's vias (R7's chain, translated with J31)
    ('J31', 1.25, 5.65, VIA_GND, 'rf-ground D31.2 / stitch E'),
    ('J31', -0.85, 5.65, VIA_GND, 'stitch W'),
    ('J31', -0.85, 6.75, VIA_GND, 'stitch W'),
    ('J31', 0.85, 6.75, VIA_GND, 'stitch E'),
    ('J31', 2.11, 6.6, VIA_GND, 'stitch E'),
    ('J31', -2.18, 6.9, VIA_GND, 'rf-ground C313.2'),
    ('J31', 3.04, 6.9, VIA_GND, 'rf-ground C314.2'),
    ('J31', -3.35, 7.2, VIA_GND, 'partner TXEN'),
    ('J31', 2.11, 8.45, VIA_GND, 'stitch E'),
]
GND_MODULE = [
    ('U30', -0.4, -7.25, VIA_SIG, 'partner V1 / V3'),
    ('U30', 2.46, 7.6, VIA_SIG, 'C301.2 decoupling via'),
    ('U31', 1.87, 6.55, VIA_GND, 'partner TXEN'),
    # R7's vias at the radio module's three ground pins (R7 pass 3 3.1: the joints of U31.2 / U31.7 / U31.16, the
    # E22's only grounds; R9P1-RF-01): R7's spots in U31's frame, 0.6 / 0.3 mm like R7's
    ('U31', 3.74, 1.27, VIA_GND, 'module ground U31.2'),
    ('U31', 1.27, -3.60, VIA_GND, 'module ground U31.7'),
    ('U31', -2.54, 3.60, VIA_GND, 'module ground U31.16'),
]
# The fence on y_f (check_r9 R-7: within 0.3 mm of y_f, <= 2.0 mm apart; step 7 opens lane gaps <= 2.7 mm) and the
# strip stitching grid (R-7 GND reach <= 4.0 mm on F.Cu and B.Cu), board frame; proposed by m3_design/r9_rf_aid.py
# (`2.5 3.6 3 rect 0.45`: a 2.5 mm grid snapped to legal spots, patched where the reach exceeded 3.6 mm; D-S4-04), frozen here
FENCE_Y = 22.2
# Step 7's family rf_if opens the lane gaps (<= 2.7 mm, each crossed by a lane) by moving fence vias of this table
# (r9_route_rf_if.FENCE_MOVES, D-S7-03); at this step every opening is <= 2.0 mm
FENCE_X = (1.95, 3.9, 5.85, 7.8, 9.75, 11.7, 13.6, 15.5, 17.45, 19.4, 21.3, 23.25, 25.2, 27.15, 29.05, 31.0, 32.95, 34.9,
           36.85, 38.8, 40.75, 42.7, 44.65)
GRID = (
    (1.0, 1.0), (3.5, 1.0), (6.0, 1.0), (8.5, 1.0), (18.5, 1.0), (21.0, 1.0), (23.5, 1.0), (26.0, 1.0),
    (38.5, 1.0), (41.0, 1.0), (43.5, 1.0), (1.0, 3.5), (6.4, 3.5), (8.5, 3.5), (18.5, 3.5), (21.0, 3.5),
    (23.5, 3.5), (26.0, 3.5), (38.5, 3.5), (1.0, 6.0), (6.0, 6.0), (8.5, 6.0), (16.0, 6.0), (18.5, 6.0),
    (21.0, 6.0), (23.5, 6.0), (26.0, 6.0), (28.5, 6.0), (36.0, 6.0), (38.5, 6.0), (43.5, 6.0), (30.95, 6.09),
    (40.96, 6.2), (33.68, 6.3), (3.57, 6.39), (5.95, 8.5), (16.35, 8.5), (18.5, 8.5), (26.0, 8.5), (36.0, 8.5),
    (38.5, 8.5), (41.0, 8.5), (43.5, 8.5), (20.59, 8.7), (24.65, 10.45), (25.9, 10.56), (35.9, 10.56), (11.3, 10.66),
    (6.0, 11.0), (8.95, 11.0), (13.5, 11.0), (16.0, 11.0), (18.5, 11.0), (28.5, 11.0), (31.0, 11.0), (33.5, 11.0),
    (38.5, 11.0), (41.0, 11.0), (43.5, 11.0), (3.85, 11.05), (20.59, 11.2), (11.18, 11.3), (38.42, 13.37), (40.92, 13.37),
    (1.0, 13.5), (3.5, 13.5), (6.0, 13.5), (16.0, 13.5), (18.5, 13.5), (28.5, 13.5), (31.0, 13.5),
    (33.5, 13.5), (43.5, 13.5), (8.5, 13.6), (11.0, 13.6), (20.59, 13.7), (13.61, 13.78), (38.47, 15.85),
    (1.0, 16.0), (3.5, 16.0), (6.0, 16.0), (8.5, 16.0), (11.0, 16.0), (13.5, 16.0), (16.0, 16.0), (18.5, 16.0),
    (28.5, 16.0), (31.0, 16.0), (33.5, 16.0), (41.4, 16.0), (43.5, 16.0), (20.59, 16.2), (1.0, 18.5),
    (3.5, 18.5), (16.35, 18.5), (18.5, 18.5), (26.0, 18.5), (36.0, 18.5), (38.5, 18.5), (41.4, 18.5), (43.5, 18.5),
    (5.97, 18.54), (20.59, 18.7), (1.0, 21.0), (3.5, 21.0), (6.0, 21.0), (18.5, 21.0), (26.0, 21.0), (28.5, 21.0),
    (31.0, 21.0), (38.5, 21.0), (41.4, 21.0), (43.5, 21.0), (20.59, 21.2),
)
# Fix pass 1 (R9P1-ROUTING-01): (24.65, 10.45) moved 0.05 mm west of the aid's (24.7, 10.45), so the TXEN loop at
# 0.2 mm keeps 0.2 mm from it.
# Step 7 (rf_if, D-S7-03): the three patches at U31's west pin entries are 0.5 mm vias, so the MOSI / NSS / SCK lanes keep
# 0.2 mm (they were 0.6 mm at (24.4, 13.45), (24.44, 14.71) and (24.55, 17.27)); the one between pins 13 and 14 sits midway
# (14.635), the one north of pin 15 moved east of SCK's lane and of the TXEN B.Cu loop (x 25.25), between pins 15 and 16;
# the grid via between DIO1's lane and FB31.1 (was 0.6 mm at (33.7, 21.0)) is 0.5 mm, midway between them (rf_if adds
# the via that stitches the GND strip between its MISO and MOSI lanes, R-7 reach)
GRID_SMALL = ((24.4, 13.45), (24.44, 14.635), (25.8, 17.6), (33.725, 21.0))
GND_BOARD = [(x, FENCE_Y, VIA_SIG, 'fence') for x in FENCE_X] + [(x, y, VIA_GND, 'grid') for x, y in GRID] + \
    [(x, y, VIA_SIG, 'grid') for x, y in GRID_SMALL]

# Lane corridors kept free of this step's vias for step 7's rf_if lanes (D-S4-05): (frame, x0, y0, x1, y1, lanes)
CORRIDORS = [
    ('U30', -4.55, 7.15, -1.65, 8.95, 'GNSS_TXD_MCU, GNSS_RXD, GNSS_TP_MCU north of the GNSS row'),
    ('U30', -3.02, 5.65, -2.34, 7.25, 'GNSS_RXD between R305 and R307 to U30.3'),
    ('U30', 4.15, 5.65, 7.05, 6.55, 'GNSS_RESET_N from U30.9 east under FB30'),
    ('U30', 6.15, 6.15, 7.05, 8.95, 'GNSS_RESET_N north'),
    ('U30', 5.25, 7.35, 5.8, 8.95, '3V3 into FB30.1'),
    ('U31', -9.71, -6.8, -7.71, 9.0, 'radio interface lanes west of R314 (RXEN, BUSY, MISO_MCU, MOSI, NSS, SCK)'),
    ('U31', -7.71, -0.7, -6.51, 9.0, 'RADIO_MOSI, RADIO_NSS, RADIO_SCK towards U31.13-15'),
    ('U31', -7.71, -6.8, -6.51, -1.9, 'RADIO_BUSY towards U31.11'),
    *[('U31', -6.51, dy - 0.25, -4.95, dy + 0.25, f'the entry into U31.{n} (a 0.2 mm lane and its 0.15 mm clearance)')
      for n, dy in ((11, -2.54), (13, 0.0), (14, 1.27), (15, 2.54))],
    ('U31', -9.71, -6.8, -3.81, -6.05, 'RADIO_RXEN to R312.1 / U31.10'),
    ('U31', 2.29, 5.7, 2.79, 9.0, 'RADIO_DIO1 north from U31.20'),
    ('U31', 3.59, 7.3, 4.19, 9.0, '3V3 into FB31.1'),
    ('U31', 6.89, -0.3, 10.49, 0.3, 'RADIO_NRST east from R311.1'),
    ('U31', 9.89, -0.3, 10.49, 9.0, 'RADIO_NRST north'),
]


def strip_nets(b, y_f=C9.Y_F):
    """The strip-internal nets: every pad in the strip (y < y_f), not GND (D-S4-05). This step completes them."""
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if n and n != 'GND' and not n.startswith('unconnected'):
                pads.setdefault(n, []).append(mm(p.GetBoundingBox().GetBottom()))
    return sorted(n for n, ys in pads.items() if max(ys) < y_f)


def corridor_boxes(frames):
    """CORRIDORS as board boxes (x0, y0, x1, y1, lanes)."""
    out = []
    for frame, x0, y0, x1, y1, lanes in CORRIDORS:
        a, c = frames.at(frame, x0, y0), frames.at(frame, x1, y1)
        out.append((min(a[0], c[0]), min(a[1], c[1]), max(a[0], c[0]), max(a[1], c[1]), lanes))
    return out


# ---------------------------------------------------------------------------------------------------------------------
def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def r4(v):
    return round(v, 4)


def octilinear(a, b):
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    return dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6


class Frames:
    """Frame origins read from the board (the frames' own parts), checked against each other and r9_place."""

    def __init__(self, b):
        self.b = b
        self.fps = {f.GetReference(): f for f in b.GetFootprints()}
        self.origin = {}
        for ref, rot in FRAME_ROT.items():
            f = self.fps[ref]
            assert not f.IsFlipped() and abs(((f.GetOrientationDegrees() - rot + 180) % 360) - 180) < 1e-6, \
                f'{ref}: rotation {f.GetOrientationDegrees()} (template {rot})'
            self.origin[ref] = (r4(mm(f.GetPosition().x)), r4(mm(f.GetPosition().y)))
        for jack in ('J30', 'J31'):
            assert abs(self.origin[jack][1]) < EPS, f'{jack} off the aft edge'
        for jack, mod, pad, dx in LINKS:
            p = self.fps[mod].FindPadByNumber(pad)
            assert abs(mm(p.GetPosition().x) - (self.origin[jack][0] + dx)) < EPS, \
                f'{mod}.{pad} must lie {dx} mm east of {jack}\'s axis (the chain template)'

    def at(self, frame, dx, dy):
        if frame == 'board':
            return (r4(dx), r4(dy))
        ox, oy = self.origin[frame]
        if frame in ('J30', 'J31'):
            return (r4(ox + dx), r4(dy))
        return (r4(ox + dx), r4(oy + dy))

    def check_parts(self):
        bad = []
        for ref, (frame, dx, dy, rot, side) in sorted(PARTS.items()):
            f = self.fps[ref]
            x, y = self.at(frame, dx, dy)
            px, py = mm(f.GetPosition().x), mm(f.GetPosition().y)
            if abs(px - x) > EPS or abs(py - y) > EPS or abs(((f.GetOrientationDegrees() - rot + 180) % 360) - 180) > \
                    1e-6 or f.IsFlipped() != (side == 'B'):
                bad.append(f'{ref} at ({px:.4f}, {py:.4f}) rot {f.GetOrientationDegrees()} '
                           f'{"B" if f.IsFlipped() else "F"}; template ({x}, {y}) rot {rot} {side} in {frame}')
        assert not bad, 'strip parts off their templates (r9_place.tsv and PARTS disagree):\n  ' + '\n  '.join(bad)


class Draw:
    def __init__(self, b, frames):
        self.b = b
        self.fr = frames
        self.vias = {}
        self.tracks = []

    def net(self, name):
        n = self.b.FindNet(name)
        assert n is not None and n.GetNetCode() > 0, f'no net {name}'
        return n

    def track(self, frame, net, layer, width, pts):
        n = self.net(net)
        pts = [self.fr.at(frame, x, y) for x, y in pts]
        for a, c in zip(pts, pts[1:]):
            assert a != c, f'{net}: zero-length segment at {a}'
            assert octilinear(a, c), f'{net}: segment {a}-{c} is not 0 / 45 / 90 degrees'
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(P(*a))
            t.SetEnd(P(*c))
            t.SetWidth(MM(width))
            t.SetLayer(LAYER[layer])
            t.SetNet(n)
            self.b.Add(t)
            self.tracks.append((net, layer, width, a, c))

    def via(self, frame, net, dx, dy, size, basis=''):
        key = self.fr.at(frame, dx, dy)
        assert key not in self.vias, f'two vias at {key}'
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(P(*key))
        v.SetWidth(MM(size[0]))
        v.SetDrill(MM(size[1]))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.net(net))
        self.b.Add(v)
        self.vias[key] = (net, basis)


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def zone(b, name, net, layers, pts, prio, clr, minw, conn, tgap, spoke):
    z = pcbnew.ZONE(b)
    ls = pcbnew.LSET()
    for lid in layers:
        ls.AddLayer(lid)
    z.SetLayerSet(ls)
    z.SetNet(b.FindNet(net))
    z.SetZoneName(name)
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(MM(clr))
    z.SetMinThickness(MM(minw))
    z.SetPadConnection(conn)
    z.SetThermalReliefGap(MM(tgap))
    z.SetThermalReliefSpokeWidth(MM(spoke))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(MM(x), MM(y))
    b.Add(z)
    return z


def rule_area(b, name, layers, pts, no_fill=False):
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    for lid in layers:
        ls.AddLayer(lid)
    z.SetLayerSet(ls)
    z.SetZoneName(name)
    z.SetDoNotAllowZoneFills(no_fill)
    z.SetDoNotAllowTracks(False)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(MM(x), MM(y))
    b.Add(z)
    return z


class _Ctx:
    """The slice of check_r9's context that module_regions needs."""

    def __init__(self, b):
        self.fps = {f.GetReference(): f for f in b.GetFootprints()}


def keepouts(b):
    """U30_KEEPOUT / U31_KEEPOUT: one rule area per distinct region, covering exactly the region check_r9 R-8 requires
    on each layer (R9_DECISIONS D-S1-22: the derivation reproduces R8's areas)."""
    ctx = _Ctx(b)
    out = {}
    for ref, name in (('U30', 'U30_KEEPOUT'), ('U31', 'U31_KEEPOUT')):
        groups = {}
        for lay, poly in C9.module_regions(ctx, ref).items():
            bb = poly.BBox()
            box = tuple(r4(mm(v)) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
            groups.setdefault(box, []).append(b.GetLayerID(lay))
        for box, layers in sorted(groups.items()):
            rule_area(b, name, layers, rect(*box))
            out[(name, tuple(sorted(b.GetLayerName(lid) for lid in layers)))] = box
    return out


def launches(b, frames):
    out = {}
    L = C9.LAUNCH
    for jack in ('J30', 'J31'):
        x, _ = frames.origin[jack]
        rule_area(b, f'R9_{jack}_launch_In1', (pcbnew.In1_Cu,), rect(r4(x - L['x']), L['y0'], r4(x + L['x']), L['y1']),
                  no_fill=True)
        out[jack] = x
    return out


def pours(b):
    """The strip's GND pours on all four layers, to STRIP_POUR_Y (R7 / R8's settings per layer); step 8 (ground)
    extends F.Cu, B.Cu and In1 over the board, step 6 (power) owns In2 forward of them (D-S4-07)."""
    T = pcbnew.ZONE_CONNECTION_THT_THERMAL
    box = rect(0.3, 0.3, 45.7, STRIP_POUR_Y)
    zone(b, 'R9_GND_F_strip', 'GND', (pcbnew.F_Cu,), box, 0, 0.15, 0.15, T, 0.5, 0.5)
    zone(b, 'R9_GND_B_strip', 'GND', (pcbnew.B_Cu,), box, 0, 0.15, 0.15, T, 0.5, 0.5)
    zone(b, 'R9_GND_In1_strip', 'GND', (pcbnew.In1_Cu,), box, 1, 0.25, 0.2, pcbnew.ZONE_CONNECTION_THERMAL, 0.25, 0.4)
    zone(b, 'R9_GND_In2_strip', 'GND', (pcbnew.In2_Cu,), box, 1, 0.25, 0.2, T, 0.25, 0.4)


def build(b, board_vias=True):
    frames = Frames(b)
    frames.check_parts()
    assert not [t for t in b.GetTracks()], 'the step-3 board carries no copper (r9_rf.py runs once, on r9_pcb.py\'s board)'
    assert not [z for z in b.Zones() if not z.GetIsRuleArea() or z.GetZoneName() in ('U30_KEEPOUT', 'U31_KEEPOUT')]
    ko = keepouts(b)
    la = launches(b, frames)
    pours(b)
    d = Draw(b, frames)
    for frame, net, layer, w, pts in GNSS_RF + RADIO_RF + U30_COPPER + LIMITER + U31_COPPER:
        d.track(frame, net, layer, w, pts)
    for frame, net, dx, dy, size, basis in LIMITER_VIAS + U31_VIAS:
        d.via(frame, net, dx, dy, size, basis)
    for jack in ('J30', 'J31'):
        for dx, dy in R7_LAUNCH_VIAS:
            d.via(jack, 'GND', dx, dy, VIA_GND, 'launch')
    for frame, dx, dy, size, basis in GND_JACK + GND_MODULE:
        d.via(frame, 'GND', dx, dy, size, basis)
    for x, y, size, basis in (GND_BOARD if board_vias else []):
        d.via('board', 'GND', x, y, size, basis)
    drawn = {net for net, *_ in d.tracks} - {'GND'}
    assert drawn == set(strip_nets(b)), (f'the step draws exactly the strip-internal nets (D-S4-05): extra '
                                         f'{sorted(drawn - set(strip_nets(b)))}, missing {sorted(set(strip_nets(b)) - drawn)}')
    return d, ko, la


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    ap.add_argument('--out', type=Path, help='design aid: save here instead of --board')
    ap.add_argument('--no-fill', action='store_true', help='design aid: save unfilled')
    ap.add_argument('--no-board-vias', action='store_true', help='design aid: leave out the fence and grid (GND_BOARD)')
    args = ap.parse_args()
    board = args.board.resolve()
    for ext in ('.kicad_pro', '.kicad_dru'):
        assert board.with_suffix(ext).is_file(), f'{board.with_suffix(ext).name} must sit beside the board'
    b = pcbnew.LoadBoard(str(board))
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    d, ko, la = build(b, board_vias=not args.no_board_vias)
    if not args.no_fill:
        b.BuildConnectivity()
        assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    b.BuildConnectivity()
    moved = []
    for v in b.GetTracks():
        if v.GetClass() == 'PCB_VIA':
            key = (r4(mm(v.GetPosition().x)), r4(mm(v.GetPosition().y)))
            if key in d.vias and d.vias[key][0] != v.GetNetname():
                moved.append((key, d.vias[key][0], v.GetNetname()))
    assert not moved, f'connectivity re-netted vias (a via sits on foreign copper): {moved}'
    out = (args.out or board).resolve()
    assert pcbnew.SaveBoard(str(out), b, True), 'save failed'
    length = sum(math.dist(a, c) for _, _, _, a, c in d.tracks)
    print(f'r9_rf: {len(d.tracks)} segments ({length:.1f} mm), {len(d.vias)} vias '
          f'({sum(1 for n, _ in d.vias.values() if n == "GND")} GND), keep-outs {len(ko)}, launches {sorted(la)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
