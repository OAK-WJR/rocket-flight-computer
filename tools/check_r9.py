#!/usr/bin/env python3
"""R9 native-CAD contract (M3-ASSY-R9): rule-based checks that replace check_r8's rigid hash groups and fixed
coordinates, each at least as strict (r9_plan.md section 4 step 1; survey_constraints.md sections 8.5, 9.5, 10).

usage: <KiCad python3> -I tools/check_r9.py [board.kicad_pcb] [--report out.json] [--fit FIT.json]
       [--plate PLATE.json] [--seed SEED.json] [--only P-3,R-7] [--strip-y Y]
exit 0 = every rule holds

Run with KiCad Python on a filled board. tools/check.sh runs it after fit_check (--fit), plate_model.py (--plate,
needs numpy) and rule_h_seed.py (--seed); without --fit the fit report is computed here, without --plate / --seed
the rules M-2 / P-4 fail as "not run". Decisions and their bases: m3_design/assembly_review/sources/r9_design/
R9_DECISIONS.md (D-S1-*). Every rule reports its evidence (closest pair, margin, measured value) in --report.

  LC-1  no pad or footprint carries a local clearance override, anywhere on the board (KiCad 10 lets an override
        replace the custom pyro rules for every pair the pad is in, in DRC and in the zone filler: D-S1-01)
  P-0   the pyro spacing rules measured geometrically, independent of DRC (tools/pyro_probe.py): m3.kicad_dru A-H,
        A2, rule G with the P-1b scope, and the strict pad rules H+ 1.2, GS 1.2, AG 1.2 mm
  P-1   one PYRO_BLOCK rule area, one outline, all four copper layers, restricting nothing, containing every CH1
        courtyard + 1.0 mm, all copper of the block's internal nets and the exit nets' copper within 3 mm of a CH1
        pad; P-1b: m3.kicad_dru's rule G also covers gate copper outside U1's courtyard (G_SCOPE)
  P-2   every bus, igniter and drain pad, track, via and fill lies inside PYRO_BLOCK
  P-3   inside the CH1 courtyards' convex hull + 1.0 mm: F.Cu only CH1 nets, GND, RAW_ACT and 3V3; In1 / In2 GND only
        (CH1 and GND vias and the CH1 parts' own barrels excepted); B.Cu foreign copper >= 1.0 mm from CH1 copper and
        foreign exposed pads >= 1.5 mm from the terminals' bottom pads
  P-4   rule H present, last among the pyro rules, minimum >= 1.0 mm, no later clearance rule able to govern its pad
        pairs; the seeded-fault suite (tools/rule_h_seed.py, --seed) ran on this board and every fault was caught
  P-5   the solder-bridge table (tools/bridge_table.py): no exposed pad pair in a forbidden consequence class
  P-6   bare pyro-gate and actuator-gate pads >= 1.0 mm from every bare always-live pad (armed-live included), same
        face, each part's own pads exempt
  P-7   gate copper (outside U1's courtyard) >= 0.5 mm, on the same layer and layers < 0.5 mm away, from every net whose
        hard short would put >= 0.2 V on the gate in reset (bridge_table.gate_voltage); the gate network's own pads
        exempt; the reset-voltage table of every neighbour within 3 mm is the evidence. P-7b (R9 review pass 1,
        R9P1-PYRO-01): U1's gate pin pad (PYRO1_GATE_N, inside the courtyard) >= 0.5 mm from every copper item that is
        not a U1 pad, GND or its own net (another net passing the pin: a short drives the gate with the MCU running)
  P-8   R168 / R170 / R172 at the MCU end: each *_MCU net <= 3.0 mm of track
  P-9   no test pad on bus / igniter / drain; TP122 on the bottom; bottom courtyards >= 2.0 mm from TP122; bare test
        pads 1.0 mm from foreign copper (check_r7.foreign_clearances); every PYRO / ARM via has a GND via within 1.5 mm
  P-10  the coat region (PYRO_BLOCK and J2's courtyard) >= 5.0 mm from U4 and clear of U5, U30, U31, LS120, the
        jacks, J3, J9, J122, J123 and every test pad but TP122
  P-11  J121 / J124 wires enter from the owner-set side (west) with >= R8's 6.25 mm to the bore wall at 5 mm height
  R-1   every strip part (RF parts but the four MCU-end interface resistors, D-S1-03) inside y < y_f; no non-RF pad
        below y_f
  R-2   the strip's per-layer net lists on y < y_f (In1 / In2 GND only; B.Cu GND, limiter nets and RADIO_TXEN up to
        R8's 22.72 mm), no non-GND pour, In1 / In2 GND across the strip, the keep-out areas on their layers
  R-3   two SMA jacks (by footprint) on the top, rotation 0, on the outline's aft edge, >= 12 mm apart, no paste,
        axes within x 3.6-42.4 (plug fit), GNSS / RADIO legends
  R-4   each jack's launch congruent with R7's in the jack's frame: the In1 cut-out x +-0.9, y 0-4.6 (no fill, In1
        only), In2 GND under it + 0.3 mm, eight GND vias at the qualified spots, F.Cu GND >= 0.30 mm from the pad
  R-5   every RF track 0.30 mm wide; F.Cu GND on both sides at 0.25-0.30 mm (one 0.01 mm scan step) except inside
        windows at the chain's own parts (launch, ESD, bias tap, pi parts, module pad entry), each <= 0.6 mm, and at
        bends, where the gap may reach R5_BEND_GAP (re-solved by tools/gcpw_solve.py: <= 52.3 ohm); In1 GND across
        +-0.70 mm under every RF track and + 0.3 mm round every RF pad outside the launch cut-outs
  R-6   jack pad end to module pad edge <= R7's 5.76 / 4.76 mm + 0.5 mm, <= 2 bends per line
  R-7   GND vias beside each RF line, gaps <= 2.5 mm on both sides, named by compass (east / west of a line run from
        the jack forward; no named ceilings); the fence on y_f (+-0.3 mm),
        pitch <= 2.0 mm, openings <= 2.7 mm crossed by a lane; strip GND reach <= 4.0 mm; RF ground pads solid with a
        GND via <= 0.6 mm
  R-8   U30 / U31 keep-outs cover the footprint-derived regions (U31 body on B.Cu / In2; the pad-ring interiors on
        F.Cu / In1); GND fill at every 0.2 mm under U31's whole body on In1 and In2 and under U30's keep-out on In1
        (survey 8.4 item 5, R8's module_ground; R9P1-INTEGRITY-02); no non-GND track or via inside a keep-out
  R-9   chain order jack -> ESD -> bias tap -> pi -> module; ESD <= 1.0 mm from the jack pad end; L30 on the line;
        C302 <= 1.0 mm from L30's cold pad; DNP shunt stubs <= 0.94 mm
  R-10  F10 / D17 separation: RF parts >= 5.94 mm (r9_plan hard X9) from the restricted parts and >= 5.0 mm from fast
        lines
  R-11  radio interface copper >= 5.0 mm from U30's body and >= 6.0 mm from GNSS RF copper; radio SPI >= 6.0 mm from
        U30's body; module courtyards >= 5.0 mm apart; GNSS RF to radio RF copper >= 15.0 mm
  R-12  FB30 / FB31 separate; decoupling within R7/R8's distances of the module VCC pins; GNSS VCC series <= 0.2 ohm
  R-13  U31, J31 and the radio RF copper >= 40 mm from J121 / J124 and from bus / igniter / drain copper
  M-2   plate model f1 (jacks only, pinned, D 5) >= 209 Hz, bound to this board
  M-3   two tie holes 1-4 mm beyond J122's ends, the tie line over all four plugs, a 4 mm bottom channel
  M-4   J1: C2915641, <= 25 mm from both terminals, entry +y with its face <= 2.0 mm from the forward edge
  M-5   fit_check clean, every category >= R8's figure or a recorded reason (FIT_FLOORS)
  M-6   bottom parts SMD only, >= 1.5 mm from foreign through-hole pads, >= 3.5 mm from an M3 centre, >= 1.0 mm from a
        PYRO / ARM via (TP122 excepted)
  M-7   U4 bottom at its revision's recorded rotation (IMU_ROTATION: R5-R8 0, the M3_R5 axis map; R9 180, D-S7-06,
        roll = -gyro_Y), lever arm |x - 23| <= 13.0 mm; no via or fill under U4 or U5 on their side, no track inside
        their pad-ring interiors
  F9-1  input protection (D8, C80, C96, C89, C95, R166, R167) <= 10.6 mm and U9 <= 27.0 mm from J1.1 (D76)
  T-1   a legal 5 mm tab on each long edge in the aft and the forward third (tools/tab_windows.py)
  K-*   kept from check_r8, unchanged or strengthened: the contract (pin table and U1 map, loader pins, connectors,
        module pins, series and pull resistors, DNP, modules on top, RF parts off safety nets, outline, C29, camera
        bypass, LS120; R9: J121 / J124 / J122 on the owner-decided footprint variants, R9_FOOTPRINTS), duplicate
        ids, legends, terminal legends, foreign clearances, vias in THT / SMD pads, overlap-only joints, thermal
        policy, via paste, D18 inner power to pyro >= 2.65 mm (r9 hard X9c), D85 battery-live to bus / igniter /
        drain >= 2.5 mm (r9 hard X2d), D19 gate to servo PWM >= 0.5 mm, D20 In1 / In2 with no signal track and no
        exemption, check_actuators.py pinned to its reviewed R9 version
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'm3_design'))
import check_r7 as r7                                           # noqa: E402
import check_r8 as r8                                           # noqa: E402
import fit_check as fc                                          # noqa: E402
import route_check as rc                                        # noqa: E402
import pyro_probe as PP                                         # noqa: E402
import bridge_table as BT                                       # noqa: E402
import tab_windows as TW                                        # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
ROOT = Path(__file__).resolve().parents[1]
PIN_TABLE = ROOT / 'm3_design/assembly_review/sources/r8_design/pin_table.tsv'   # R9 keeps R8's pin map (D-S1-07)
CHECK_ACTUATORS = ROOT / 'm3_design/check_actuators.py'
# the reviewed R9 check_actuators.py (15b rule-based, D-S1-02; DRU_SHA and rule G's PYRO_RULE_SHA re-pinned to R9's
# m3.kicad_dru, D-S2-11; DRU_SHA re-pinned for the zone fill margins, D-S5-12); a reviewed change re-pins this and
# records why
CHECK_ACTUATORS_SHA = '3f22b273b712418a0a16646d4af28e46ee3c1167a35547650076338c06725240'
EPS = 1e-3

# --- recorded geometry (owner decisions, R9_OWNER_DECISIONS.md) --------------------------------------------------------
Y_F = 22.0                       # RF strip boundary y_f (owner decision 3; F10 text "y 0-22.0")
FENCE_BAND = 0.3                 # fence vias within +-0.3 mm of y_f (survey 8.3)
ENTRY = {'J121': '-x', 'J124': '-x', 'J1': '+y'}       # owner decision 1: pyro leads west, battery leads forward/east

# --- P-rules ---------------------------------------------------------------------------------------------------------
CH1_PARTS = r8.CH1_PARTS
CH1_NET = re.compile(r'^(PYRO1_|ARM1_)')
BLOCK_NETS = ('PYRO1_GATE', 'PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT', 'PYRO1_COLD', 'PYRO1_CONT_MID', 'ARM1_SENSE_MID')
EXIT_NETS = ('PYRO1_GATE_N', 'PYRO1_CONT', 'ARM1_SENSE')
EXIT_REACH, COURTYARD_GROW, HULL_GROW = 3.0, 1.0, 1.0
ARMED = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
GATES = ('PYRO1_GATE', 'PYRO1_GATE_N')
ACT_GATES = ('ACT_GATE', 'ACT_DRV')
G_SCOPE = "(A.intersectsArea('PYRO_BLOCK') || !A.intersectsCourtyard('U1'))"     # P-1b (owner decision 2)
RULE_G = 'Pyro G: gate nets in the pyro block'
RULE_H = 'Pyro H: live pads to sense and gate pads (solder bridge)'
PURITY_F = ('GND', 'RAW_ACT', '3V3')
PURITY_B_GAP, PURITY_BARE_GAP = 1.0, 1.5
ALWAYS_LIVE = ('RAW_ACT', 'BAT_IN', 'RAW_PROTECTED', 'VLOGIC', '3V3', '3V3A', 'CAM_5V', 'CAM_INPUT_LIMITED',
               'USB_LIMITED', 'VBUS', 'BAT_ENABLE', 'BAT_SW_SOURCE', 'ACT_FET_S', '3V3_GNSS', '3V3_RADIO',
               'CAM_IO_3V3') + ARMED              # step9/requalify.ALWAYS_LIVE + the module and camera-IO rails
BARE_GATE = 1.0
GUARD, GUARD_REACH = 0.5, 3.0
GATE_PARTS = ('Q124', 'R126', 'R127', 'R128', 'C126', 'TP122')
MCU_REF, MCU_PIN_REACH = 'U1', 1.5     # P-7b: the gate pin's pad, its neighbours listed within 1.5 mm
SENSE_END = (('R168', 'PYRO1_CONT_MCU'), ('R170', 'ARM1_SENSE_MCU'), ('R172', 'RAW_ACT_SENSE_MCU'))
SENSE_END_MAX = 3.0
TP122_BOTTOM = 2.0
CRITICAL_VIA_GND = 1.5
COAT_U4 = 5.0                    # 3 mm coating-free zone (ORDERING 5, ST TN1383) + 2 mm brush margin (Inference)
COAT_KEEPOFF = ('U5', 'U30', 'U31', 'LS120', 'J30', 'J31', 'J3', 'J9', 'J122', 'J123')
BORE_WALL, WIRE_Z, SLED_TOL = 25.4, 5.0, 0.3
WIRE_ROOM = 6.25                 # R8: J121 / J124 6.253 mm (fit_check: 6.3-6.9)
AXIAL_FACE = 2.0                 # an axial entry's face within 2 mm of its edge (R8 J1 1.9 mm)

# --- R-rules ---------------------------------------------------------------------------------------------------------
JACK_FP = 'M3_SMA_KH_KE8_EDGE'
MCU_END = ('R306', 'R310', 'R313', 'R315')     # SERIES / D4: at the MCU end, not in the strip (D-S1-03)
STRIP_B_R9 = re.compile(r'^(GND|GNSS_VCC_RF|GNSS_LNA_EN|GNSS_ANT_(DC|SRC|GATE|PD)|RADIO_TXEN)$')
TXEN_B_MAX = 22.72               # mm of RADIO_TXEN on B.Cu in the strip on R8 (survey R-2: no more than R8's)
LAUNCH = dict(x=0.9, y0=0.0, y1=4.6, tol=0.01, in2_grow=0.3,
              vias=((-1.45, 1.0), (1.45, 1.0), (-1.45, 2.3), (1.45, 2.3), (-1.45, 3.6), (1.45, 3.6),
                    (-1.25, 4.15), (1.25, 4.15)), via_tol=0.05, gap=0.30)
RF_W = 0.30
GAP_LO, GAP_HI = 25, 31          # 0.01 mm scan steps: the qualified 0.25-0.30 mm gap within one step (R7 pass 2)
R5_BEND_GAP = 0.55               # mm: gcpw_solve Z0(0.58) = 52.3 ohm; 0.55 keeps margin (r9_step1_progress)
WINDOW_MAX, WINDOW_STEP = 0.6, 0.05
IN1_BAND = 0.70                  # +-(0.15 + 0.25 + 0.30) mm under each RF track
GCPW_STEP, GCPW_SCAN, GCPW_REACH = 0.05, 0.01, 1.5
CHAINS = {
    'GNSS': dict(jack_net='GNSS_RF_ANT', nets=('GNSS_RF_ANT', 'GNSS_RF_IN'), module='U30', pad='11', esd='D30',
                 bias='L30', bias_cap='C302', series='R304', shunts=('C303', 'C305'), length=5.76),
    'RADIO': dict(jack_net='RADIO_RF_ANT', nets=('RADIO_RF_ANT', 'RADIO_RF'), module='U31', pad='6', esd='D31',
                  bias=None, bias_cap=None, series='R316', shunts=('C313', 'C314'), length=4.76)}
LENGTH_SLACK, MAX_BENDS = 0.5, 2
ESD_MAX, BIAS_CAP_MAX, STUB_MAX = 1.0, 1.0, 0.94
STITCH_GAP, STITCH_NEAR, STITCH_FAR = 2.5, 0.4, 2.0
FENCE_PITCH, FENCE_OPENING_MAX = 2.0, 2.7
STRIP_GND_REACH = 4.0
# module bodies in the footprint's own frame (local x, local y), mm: EBYTE E22-900MM22S manual 10 x 10;
# u-blox MAX-F10S DS Table 21 10.1 (along the pad rows, local y) x 9.7
BODY = {'U31': (10.0, 10.0), 'U30': (9.7, 10.1)}
KEEPOUT_INSET = 0.15
KEEPOUT_LAYERS = {'U30': ('F.Cu', 'In1.Cu'), 'U31': ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')}
RF_SEP_PART, RF_SEP_LINE = 5.94, 5.0
COEX_BODY, COEX_GNSS, COEX_SPI, COEX_MODULES, COEX_RF = 5.0, 6.0, 6.0, 5.0, 15.0
RADIO_RF = ('RADIO_RF_ANT', 'RADIO_RF')
GNSS_RF = ('GNSS_RF_ANT', 'GNSS_RF_IN')
RADIO_SPI = re.compile(r'^RADIO_(SCK|MOSI|MISO)(_MCU)?$|^RADIO_NSS$')
# decoupling: (module, VCC pins, capacitor) -> limit mm, VCC pad centre to the capacitor's supply pad centre; the R7 /
# R8 geometry (rigid in R8) re-measured with this one metric (pass2_rf 3.11 quoted 1.8 / 2.0 / 3.6 mm from another point)
DECOUPLING = {('U31', ('1',), 'C311'): 1.97, ('U31', ('1',), 'C312'): 2.19, ('U31', ('1',), 'C310'): 3.64,
              ('U30', ('7', '8'), 'C301'): 2.18, ('U30', ('7', '8'), 'C300'): 3.02}
FB30_DCR = 0.050                 # ohm, BLM18KG221SN1D (Murata JENF243A-0003 section 3; pass2_electrical 4.5)
SHEET_R = 0.62e-3                # ohm / square, 1 oz copper at 85 C (0.49 mohm at 20 C, +0.393 %/K)
VIA_R, FEED_3V3 = 0.001, 0.020   # ohm per via; the 3V3 side of FB30 (pass 3 solved 5.06 mohm; 4x allowance)
GNSS_VCC_MAX = 0.2               # ohm (u-blox MAX-F10S IM 4.1.1)
RF_PYRO = 40.0                   # mm (owner decision 3: about 45 mm accepted; survey R-13 proposal 40)

# --- M-rules ---------------------------------------------------------------------------------------------------------
F1_MIN = 209.0                   # Hz, plate model jacks only, pinned, D 5 (r9_plan hard; R8 208.7)
TIE_PAST = (1.0, 4.0)
TIE_CHANNEL = 2.0
J1_LCSC, J1_GROUP = 'C2915641', 25.0
# owner decisions 2 and 5 (R9_OWNER_DECISIONS.md): the pad-renumbered terminals and the mirrored-numbering servo header,
# same parts and lands (m3_design/r9_lib.py; R9_DECISIONS D-S2-01, D-S2-12). KiCad DRC's lib_footprint_mismatch holds
# each instance to its library footprint, parity holds the board to the schematic's footprint fields.
R9_FOOTPRINTS = {'J121': 'M3_DB128L_2P_BK_SW', 'J124': 'M3_DB128L_2P_BK_SW',
                 'J122': 'HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR'}
FIT_FLOORS = {'J9 mated': (0.028, None), 'J3': (0.886, None), 'J121': (1.153, None), 'J124': (1.153, None),
              'C84': (1.366, None),
              'J122 mated': (0.49, 'owner decision 5 (r9_plan 3.4): J122 turned, plugs along x: 0.50 mm against R8 0.715')}
FIT_BOTTOM, FIT_SUPPORT_BOTTOM, FIT_SUPPORT_TOP = 2.356, 4.452, 5.008   # R8's figures, truncated to 0.001 mm
BOT_THT, BOT_M3, BOT_PYRO_VIA = 1.5, 3.5, 1.0
IMU_LEVER = 13.0                 # mm, R8's |x - 23|
# U4's recorded axis maps (M-7), keyed on the board's title-block revision. R5-R8: rotation 0, M3_R5 section 3 (+X_imu =
# +x_board, +Y_imu = +y_board, +Z_imu out of the bottom face; roll = +gyro_Y, thrust reads +a_Y). R9: rotation 180 on the
# bottom (R9_DECISIONS D-S7-06: +X_imu = -x_board, +Y_imu = -y_board, +Z_imu out of the bottom face; roll = -gyro_Y,
# thrust reads -a_Y; the binding note carries it and a bench sign check precedes flight). Any other revision is held to
# R9's map.
IMU_ROTATION = {'M3-ASSY-R8': 0.0, 'M3-ASSY-R7': 0.0}
IMU_ROTATION_R9 = 180.0
IMU_MAP = {0.0: 'M3_R5 axis map: roll = +gyro_Y', 180.0: 'R9 D-S7-06 axis map: roll = -gyro_Y'}
MEMS = ('U4', 'U5')
MEMS_INSET = 0.25                # the body: the courtyard less its 0.25 mm margin (R8's IMU_body_B / BARO_body_B)
PROTECTION = ('D8', 'C80', 'C96', 'C89', 'C95', 'R166', 'R167')
PROTECTION_MAX, U9_MAX = 10.6, 27.07   # R8 (D76): the geometry step9/hotplug_feed.py modelled
# --- K-rules ---------------------------------------------------------------------------------------------------------
INNER_POWER_PYRO = 2.65          # r9_plan hard X9c (D18 2.5)
BATTERY_PYRO = 2.5               # r9_plan hard X2d (D85 1.0)


# ======================================================================================================================
# geometry helpers
# ======================================================================================================================
def xy(p):
    return mm(p.x), mm(p.y)


def rect_poly(x0, y0, x1, y1):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        s.Append(MM(x), MM(y))
    return s


def poly_of_points(pts):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in pts:
        s.Append(MM(x), MM(y))
    return s


def poly_points(poly):
    out = []
    for i in range(poly.OutlineCount()):
        ch = poly.Outline(i)
        out += [xy(ch.CPoint(k)) for k in range(ch.PointCount())]
    return out


def area_mm2(poly):
    return poly.Area() / 1e12 if poly.OutlineCount() else 0.0


def residue(item_poly, container):
    r = pcbnew.SHAPE_POLY_SET(item_poly)
    r.BooleanSubtract(container)
    return area_mm2(r)


def inflate(poly, d):
    p = pcbnew.SHAPE_POLY_SET(poly)
    p.Inflate(MM(d), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MM(0.005))
    return p


def hull(points):
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def item_poly(it):
    return PP._poly(it)


def to_local(f, x, y):
    """Board mm -> footprint-local mm (KiCad rotation: board = pos + (x c + y s, -x s + y c))."""
    th = math.radians(f.GetOrientationDegrees())
    c, s = math.cos(th), math.sin(th)
    dx, dy = x - mm(f.GetPosition().x), y - mm(f.GetPosition().y)
    return dx * c - dy * s, dx * s + dy * c


def to_board(f, x, y):
    th = math.radians(f.GetOrientationDegrees())
    c, s = math.cos(th), math.sin(th)
    return mm(f.GetPosition().x) + x * c + y * s, mm(f.GetPosition().y) - x * s + y * c


def entry_dir(f):
    """Board direction of a terminal's wire entry: the DB128 footprints enter on local -y (their descr)."""
    th = math.radians(f.GetOrientationDegrees())
    dx, dy = -math.sin(th), -math.cos(th)
    if abs(dx) > abs(dy):
        return '+x' if dx > 0 else '-x'
    return '+y' if dy > 0 else '-y'


def seg_point_dist(p, a, b):
    return r7.distance_to_segment(p, a, b)


def pad_label(p):
    return f'{p.GetParentFootprint().GetReference()}.{p.GetNumber()}'


class Ctx:
    """Shared, lazily computed board data for the rules."""

    def __init__(self, board, folder=None, board_path=None, fit=None, plate=None, seed=None, y_f=Y_F, dru=None):
        self.board, self.folder, self.board_path = board, Path(folder) if folder else None, board_path
        self.fit_report, self.plate, self.seed, self.y_f = fit, plate, seed, y_f
        self.fps = {f.GetReference(): f for f in board.GetFootprints()}
        holes, self.outline = fc.board_geometry(board)
        self.holes = holes
        self._items = None
        if dru is None and self.folder is not None and board.GetFileName():
            p = self.folder / (Path(board.GetFileName()).stem + '.kicad_dru')
            dru = p.read_text() if p.is_file() else None
        self.dru = dru

    @property
    def items(self):
        if self._items is None:
            self._items = r8.net_items(self.board, lambda n: True)
        return self._items

    def net_items(self, pred, layers=None):
        return [it for it in self.items if pred(it[1]) and (layers is None or it[2] in layers)]

    def block_areas(self):
        return [z for z in self.board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK']

    def block_poly(self):
        a = self.block_areas()
        return pcbnew.SHAPE_POLY_SET(a[0].Outline()) if a else None

    def courtyard(self, ref):
        f = self.fps.get(ref)
        return r8.courtyard(f) if f else None

    def fit(self):
        if self.fit_report is None:
            self.fit_report = fc.check_board(self.board, self.folder or Path('.'))
        return self.fit_report

    def layer_pairs(self):
        if self.board_path and Path(self.board_path).is_file():
            return r8.close_layer_pairs(self.board_path)
        f, i1, i2, b = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
        same = {(x, x) for x in (f, i1, i2, b)}
        return same | {(f, i1), (i1, f), (i2, b), (b, i2)}


# ======================================================================================================================
# LC-1
# ======================================================================================================================
def lc1(board):
    """No pad or footprint carries a local clearance override (D-S1-01: board-wide)."""
    issues, found = [], []
    for f in board.GetFootprints():
        ref = f.GetReference()
        if f.GetLocalClearance() is not None:
            found.append(f'{ref} (footprint) {mm(f.GetLocalClearance()):g}')
            issues.append(f'LC-1: footprint {ref} carries a local clearance override of {mm(f.GetLocalClearance()):g} '
                          'mm (it replaces the pyro rules for every pad of the part)')
        for p in f.Pads():
            lc = p.GetLocalClearance()
            if lc is not None:
                found.append(f'{ref}.{p.GetNumber()} ({p.GetNetname()}) {mm(lc):g}')
                issues.append(f'LC-1: pad {ref}.{p.GetNumber()} ({p.GetNetname()}) carries a local clearance override '
                              f'of {mm(lc):g} mm (it replaces the DRU rules, pyro rules included, for every pair it is in)')
    zones = [f'{z.GetZoneName() or z.GetNetname()} {mm(z.GetLocalClearance()):g}' for z in board.Zones()
             if not z.GetIsRuleArea() and z.GetLocalClearance() is not None]
    return issues, dict(overrides=found, zone_clearances_floor_only=zones)


# ======================================================================================================================
# P-rules
# ======================================================================================================================
def p0(ctx):
    res = PP.probe(ctx.board)
    return PP.issues_of(res), {k: dict(minimum=v['minimum'], closest=v['closest'], margin=v['margin'],
                                       violations=v['violation_count']) for k, v in res.items()}


def p1(ctx):
    issues, ev = [], {}
    areas = ctx.block_areas()
    if len(areas) != 1:
        return [f'P-1: exactly one PYRO_BLOCK rule area required, found {len(areas)}'], ev
    z = areas[0]
    layers = {ctx.board.GetLayerName(l) for l in z.GetLayerSet().CuStack()}
    if layers != {'F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'}:
        issues.append(f'P-1: PYRO_BLOCK must be on F.Cu, In1, In2 and B.Cu (has {sorted(layers)})')
    out = z.Outline()
    if out.OutlineCount() != 1 or out.HoleCount(0):
        issues.append('P-1: PYRO_BLOCK must be one outline without holes')
    if any((z.GetDoNotAllowTracks(), z.GetDoNotAllowVias(), z.GetDoNotAllowPads(), z.GetDoNotAllowZoneFills(),
            z.GetDoNotAllowFootprints())):
        issues.append('P-1: PYRO_BLOCK must restrict nothing (it only scopes rule G)')
    area = pcbnew.SHAPE_POLY_SET(out)
    bb = area.BBox()
    ev['area_bbox'] = [round(mm(v), 3) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]
    for ref in CH1_PARTS:
        cy = ctx.courtyard(ref)
        if cy is None:
            issues.append(f'P-1: CH1 part {ref} missing')
            continue
        r = residue(inflate(cy, COURTYARD_GROW), area)
        if r > EPS:
            issues.append(f'P-1: {ref} courtyard + {COURTYARD_GROW} mm reaches {r:.3f} mm2 outside PYRO_BLOCK')
    for it in ctx.net_items(lambda n: n in BLOCK_NETS):
        r = residue(item_poly(it), area)
        if r > EPS:
            issues.append(f'P-1: {it[0]} ({it[1]}, {ctx.board.GetLayerName(it[2])}) reaches {r:.3f} mm2 outside '
                          'PYRO_BLOCK')
    for net in EXIT_NETS:
        reach = pcbnew.SHAPE_POLY_SET()
        for ref in CH1_PARTS:
            f = ctx.fps.get(ref)
            for p in (f.Pads() if f else []):
                if p.GetNetname() == net:
                    pp = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(pp, pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu, 0,
                                              MM(0.005), pcbnew.ERROR_OUTSIDE)
                    reach.BooleanAdd(inflate(pp, EXIT_REACH))
        if not reach.OutlineCount():
            issues.append(f'P-1: no CH1 pad on exit net {net}')
            continue
        for it in ctx.net_items(lambda n, net=net: n == net):
            if isinstance(it[4], pcbnew.PAD) and it[4].GetParentFootprint().GetReference() not in CH1_PARTS:
                continue
            part = item_poly(it)
            part.BooleanIntersection(reach)
            r = residue(part, area)
            if r > EPS:
                issues.append(f'P-1: {net} {it[0]} within {EXIT_REACH} mm of its CH1 pad lies {r:.3f} mm2 outside '
                              'PYRO_BLOCK')
    on_block = {f.GetReference() for f in ctx.board.GetFootprints() if any(p.GetNetname() in BLOCK_NETS for p in f.Pads())}
    for ref in sorted(on_block - set(CH1_PARTS)):
        issues.append(f'P-1: {ref} has a pad on a block-internal net but is not a CH1 part (netlist drift)')
    # P-1b: rule G's DRU scope
    g = rule_text(ctx.dru, RULE_G)
    ev['rule_g_scope'] = bool(g and G_SCOPE in g)
    if g is None:
        issues.append('P-1b: m3.kicad_dru has no rule G')
    elif G_SCOPE not in g:
        issues.append(f'P-1b: rule G must cover gate copper outside U1\'s courtyard: its condition must carry {G_SCOPE} '
                      "in place of A.intersectsArea('PYRO_BLOCK') (owner decision 2)")
    return issues, ev


def p2(ctx):
    issues, n = [], 0
    area = ctx.block_poly()
    if area is None:
        return ['P-2: no PYRO_BLOCK area'], {}
    for it in ctx.net_items(lambda x: x in ARMED):
        n += 1
        r = residue(item_poly(it), area)
        if r > EPS:
            issues.append(f'P-2: armed-live {it[0]} ({it[1]}, {ctx.board.GetLayerName(it[2])}) lies {r:.3f} mm2 outside '
                          'PYRO_BLOCK')
    return issues, dict(items=n)


def ch1_hull(ctx):
    pts = []
    for ref in CH1_PARTS:
        cy = ctx.courtyard(ref)
        if cy is not None:
            pts += poly_points(cy)
    return inflate(poly_of_points(hull(pts)), HULL_GROW) if len(pts) >= 3 else None


def p3(ctx):
    issues, foreign = [], defaultdict(set)
    h = ch1_hull(ctx)
    if h is None:
        return ['P-3: no CH1 parts'], {}
    bb = h.BBox()
    ev = dict(hull_bbox=[round(mm(v), 2) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())],
              hull_area_mm2=round(area_mm2(h), 1))

    def touches(it):
        s = it[3]
        return pcbnew.SHAPE.Collide(h, s, 0)

    def ch1_own(it):
        return isinstance(it[4], pcbnew.PAD) and it[4].GetParentFootprint().GetReference() in CH1_PARTS
    nc = lambda n: not n or n.startswith('unconnected-')          # noqa: E731
    ch1_b = [it for it in ctx.net_items(lambda n: bool(CH1_NET.match(n or '')), (pcbnew.B_Cu,))]
    term_b = [(pad_label(p), p.GetEffectiveShape(pcbnew.B_Cu)) for ref in ('J121', 'J124') if ref in ctx.fps
              for p in ctx.fps[ref].Pads() if p.IsOnLayer(pcbnew.B_Cu)]
    for it in ctx.items:
        net, lay = it[1], it[2]
        if nc(net) or CH1_NET.match(net or '') or net == 'GND':
            continue
        if lay == pcbnew.F_Cu:
            if net in PURITY_F or not touches(it):
                continue
            foreign['F.Cu'].add(net)
            issues.append(f'P-3: {it[0]} ({net}) on F.Cu inside the CH1 hull + {HULL_GROW} mm')
        elif lay in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            if ch1_own(it) or not touches(it):
                continue
            foreign[ctx.board.GetLayerName(lay)].add(net)
            issues.append(f'P-3: {it[0]} ({net}) on {ctx.board.GetLayerName(lay)} inside the CH1 hull (In1 / In2 GND only)')
        elif lay == pcbnew.B_Cu:
            if ch1_own(it) or not touches(it):
                continue
            for l2, n2, _, s2, _ in ch1_b:
                g = r8.min_gap(it[3], s2, PURITY_B_GAP)
                if g is not None and g < PURITY_B_GAP - EPS:
                    foreign['B.Cu'].add(net)
                    issues.append(f'P-3: {it[0]} ({net}) on B.Cu is {g:.3f} mm from CH1 copper {l2} ({n2}); minimum '
                                  f'{PURITY_B_GAP} mm inside the hull')
                    break
            obj = it[4]
            if isinstance(obj, pcbnew.PAD) and obj.IsOnLayer(pcbnew.B_Mask):
                for lab, s2 in term_b:
                    g = r8.min_gap(it[3], s2, PURITY_BARE_GAP)
                    if g is not None and g < PURITY_BARE_GAP - EPS:
                        issues.append(f'P-3: exposed {it[0]} ({net}) is {g:.3f} mm from terminal pad {lab} on B.Cu; '
                                      f'minimum {PURITY_BARE_GAP} mm')
    ev['foreign_nets'] = {k: sorted(v) for k, v in foreign.items()}
    return sorted(set(issues)), ev


def rule_text(dru, name):
    if not dru:
        return None
    i = dru.find(f'(rule "{name}"')
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(dru)):
        depth += {'(': 1, ')': -1}.get(dru[j], 0)
        if depth == 0:
            return dru[i:j + 1]
    return None


def rules_in_order(dru):
    out = []
    for m in re.finditer(r'\(rule "([^"]+)"', dru or ''):
        out.append((m.group(1), rule_text(dru, m.group(1))))
    return out


def p4(ctx, board_sha=None):
    issues, ev = [], {}
    order = rules_in_order(ctx.dru)
    names = [n for n, _ in order]
    if RULE_H not in names:
        return ['P-4: rule H missing from m3.kicad_dru'], ev
    h = rule_text(ctx.dru, RULE_H)
    m = re.search(r'\(min ([\d.]+)mm\)', h)
    if not m or float(m.group(1)) < 1.0:
        issues.append('P-4: rule H must keep a minimum >= 1.0 mm')
    ih = names.index(RULE_H)
    pyro = [i for i, n in enumerate(names) if n.startswith('Pyro ')]
    if max(pyro) != ih:
        issues.append('P-4: rule H must be the last pyro rule (KiCad applies the last matching rule)')
    for n, t in order[ih + 1:]:
        if '(constraint clearance' not in t:
            continue
        mm_ = re.search(r'\(constraint clearance \(min ([\d.]+)mm\)\)', t)
        if mm_ and float(mm_.group(1)) >= 1.0:
            continue
        # a later clearance rule may only match pairs rule H cannot hold: a zone on the B side, or J2's pads
        if "B.Type == 'Zone'" in t or "A.memberOfFootprint('J2')" in t:
            continue
        issues.append(f'P-4: rule "{n}" comes after rule H with a clearance under 1.0 mm and may govern its pad pairs')
    ev['rules_after_h'] = names[ih + 1:]
    import check_actuators as CA
    sha = hashlib.sha256(h.encode()).hexdigest()[:16]
    ev['rule_h_sha16'] = sha
    if sha != CA.PYRO_RULE_SHA.get(RULE_H):
        issues.append(f'P-4: rule H text differs from check_actuators PYRO_RULE_SHA ({sha})')
    s = ctx.seed
    if s is None:
        issues.append('P-4: the seeded rule-H suite (tools/rule_h_seed.py) was not run on this board (--seed)')
    else:
        ev['seed_pairs'] = [p.get('pair') for p in s.get('pairs', [])]
        if board_sha and s.get('board_sha256') != board_sha:
            issues.append('P-4: the seeded-suite report is not bound to this board (board_sha256)')
        if not s.get('pairs'):
            issues.append('P-4: the seeded suite seeded no pair')
        issues += [f'P-4: {i}' for i in s.get('issues', [])]
    return issues, ev


def p5(ctx):
    rows = BT.table(ctx.board)
    bad = BT.issues_of(rows)
    return bad, dict(pairs=len(rows), forbidden=sum(1 for r in rows if r['forbidden']),
                     under_1mm=[f"{r['gap']:.3f} {r['a']} -- {r['b']}: {r['consequence']}" for r in rows
                                if r['gap'] < BT.BRIDGE and not r['own_part']])


def exposed(board):
    return BT.exposed_pads(board)


def p6(ctx):
    issues, worst = [], {}
    pads = exposed(ctx.board)
    gates = [p for p in pads if p[2] in GATES + ACT_GATES]
    live = [p for p in pads if p[2] in ALWAYS_LIVE]
    for ra, na, neta, fa, sa, _ in gates:
        for rb, nb, netb, fb, sb, _ in live:
            if fa != fb or ra == rb or neta == netb:
                continue
            g = r8.min_gap(sa, sb, BARE_GATE + 1.0)
            if g is None:
                continue
            key = f'{ra}.{na} ({neta})'
            if key not in worst or g < worst[key][0]:
                worst[key] = (g, f'{rb}.{nb} ({netb})')
            if g < BARE_GATE - EPS:
                issues.append(f'P-6: bare gate pad {ra}.{na} ({neta}) is {g:.3f} mm from bare always-live pad {rb}.{nb} '
                              f'({netb}) on {fa}; minimum {BARE_GATE} mm')
    return issues, dict(nearest={k: list(v) for k, v in sorted(worst.items(), key=lambda kv: kv[1][0])[:8]})


def p7(ctx):
    issues, table = [], {}
    pairs = ctx.layer_pairs()
    scope = PP.Scope(ctx.board)
    u1 = scope.u1
    gate = ctx.net_items(lambda n: n in GATES)
    others = [it for it in ctx.items if it[1] not in GATES + ('GND',) and it[1]]
    for g in gate:
        shape = g[3]
        if u1 is not None:
            poly = item_poly(g)
            poly.BooleanSubtract(u1)
            if not poly.OutlineCount() or area_mm2(poly) < 1e-4:
                continue
            shape = poly
        for o in others:
            if (g[2], o[2]) not in pairs:
                continue
            if isinstance(o[4], pcbnew.PAD) and o[4].GetParentFootprint().GetReference() in GATE_PARTS:
                continue
            if PP._bbox_gap(shape, o[3]) > GUARD_REACH:
                continue
            d = r8.min_gap(shape, o[3], GUARD_REACH)
            if d is None:
                continue
            v = BT.gate_voltage(o[1], g[1])
            key = (o[1], g[1])
            if key not in table or d < table[key]['mm']:
                table[key] = dict(mm=d, gate=g[0], other=o[0], layers=[ctx.board.GetLayerName(g[2]),
                                                                   ctx.board.GetLayerName(o[2])], v_reset=round(v, 3))
            if v >= BT.GATE_RESET_MAX and d < GUARD - EPS:
                issues.append(f'P-7: {g[1]} {g[0]} ({ctx.board.GetLayerName(g[2])}) is {d:.3f} mm from {o[1]} {o[0]} '
                              f'({ctx.board.GetLayerName(o[2])}); a short puts {v:.2f} V on the gate in reset; minimum '
                              f'{GUARD} mm')
    rows = sorted(({'net': k[0], 'gate_net': k[1], **v} for k, v in table.items()), key=lambda r: (r['mm'], r['net']))
    # P-7b (R9P1-PYRO-01): the MCU's gate pin inside U1's courtyard, which the clipped measure above does not see.
    # Another net's copper passing the pin is a short that drives the gate with the MCU running (PE4 low against the
    # neighbour's driver): it keeps GUARD from the pin's pad; U1's own pads (the sentinels' pitch, R8's map), GND and
    # unconnected copper (no source) excepted
    pin_rows = []
    u1f = ctx.fps.get(MCU_REF)
    for pad in (u1f.Pads() if u1f else []):
        if pad.GetNetname() not in GATES:
            continue
        for lid in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not pad.IsOnLayer(lid):
                continue
            ps = pad.GetEffectiveShape(lid)
            near = {}
            for o in others:
                if (lid, o[2]) not in pairs or o[1].startswith('unconnected-'):
                    continue
                if isinstance(o[4], pcbnew.PAD) and o[4].GetParentFootprint().GetReference() == MCU_REF:
                    continue
                if PP._bbox_gap(ps, o[3]) > MCU_PIN_REACH:
                    continue
                d = r8.min_gap(ps, o[3], MCU_PIN_REACH)
                if d is None:
                    continue
                if o[1] not in near or (d, o[0]) < near[o[1]][:2]:
                    near[o[1]] = (d, o[0], ctx.board.GetLayerName(o[2]))
                if d < GUARD - EPS:
                    issues.append(f'P-7: {o[1]} {o[0]} ({ctx.board.GetLayerName(o[2])}) is {d:.3f} mm from the MCU gate '
                                  f'pin {pad_label(pad)} ({pad.GetNetname()}); minimum {GUARD} mm (P-7b)')
            pin_rows += [dict(pin=pad_label(pad), net=n, mm=v[0], item=v[1], layer=v[2])
                         for n, v in sorted(near.items(), key=lambda kv: (kv[1][0], kv[0]))]
    return sorted(set(issues)), dict(reset_voltage_table=rows, mcu_gate_pin=pin_rows)


def p8(ctx):
    issues, ev = [], {}
    for ref, net in SENSE_END:
        L = sum(mm(t.GetLength()) for t in ctx.board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net)
        ev[net] = round(L, 3)
        f = ctx.fps.get(ref)
        if f is None or not any(p.GetNetname() == net for p in f.Pads()):
            issues.append(f'P-8: {ref} must carry {net}')
        if L > SENSE_END_MAX + EPS:
            issues.append(f'P-8: {net} has {L:.2f} mm of track; {ref} must sit at the MCU end (<= {SENSE_END_MAX} mm)')
    return issues, ev


def p9(ctx):
    issues, ev = [], {}
    for f in ctx.board.GetFootprints():
        if re.fullmatch(r'TP\d+', f.GetReference()) and any(p.GetNetname() in ARMED for p in f.Pads()):
            issues.append(f'P-9: test pad {f.GetReference()} on armed-live copper')
    tp = ctx.fps.get('TP122')
    if tp is None:
        issues.append('P-9: TP122 missing')
    else:
        if not tp.IsFlipped():
            issues.append('P-9: TP122 (bare gate pad) must be on the bottom side')
        pad = next(iter(tp.Pads()))
        s = pad.GetEffectiveShape(pcbnew.B_Cu)
        near = None
        for f in ctx.board.GetFootprints():
            if f.GetReference() == 'TP122' or not f.IsFlipped():
                continue
            g = r8.min_gap(r8.courtyard(f), s, TP122_BOTTOM + 1)
            if g is not None and (near is None or g < near[0]):
                near = (g, f.GetReference())
            if g is not None and g < TP122_BOTTOM - EPS:
                issues.append(f'P-9: bottom part {f.GetReference()} is {g:.3f} mm from TP122; minimum {TP122_BOTTOM} mm')
        ev['tp122_nearest_bottom'] = near
    copper = r7.copper_shapes(ctx.board)
    found, ev['guarded_pads'] = r7.foreign_clearances(ctx.board, copper)
    issues += [f'P-9: {i}' for i in found]
    gnd = [xy(t.GetPosition()) for t in ctx.board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    vias = []
    for t in ctx.board.GetTracks():
        if t.GetClass() == 'PCB_VIA' and CH1_NET.match(t.GetNetname() or ''):
            c = xy(t.GetPosition())
            d = min((math.dist(c, g) for g in gnd), default=None)
            vias.append((t.GetNetname(), c, None if d is None else round(d, 3)))
            if d is None or d > CRITICAL_VIA_GND + EPS:
                issues.append(f'P-9: {t.GetNetname()} via at {c} has no GND via within {CRITICAL_VIA_GND} mm '
                              f'(nearest {d})')
    ev['pyro_vias'] = vias
    return issues, ev


def p10(ctx):
    issues, ev = [], {}
    area = ctx.block_poly()
    if area is None:
        return ['P-10: no PYRO_BLOCK area'], ev
    region = pcbnew.SHAPE_POLY_SET(area)
    if 'J2' in ctx.fps:
        region.BooleanAdd(ctx.courtyard('J2'))
    u4 = ctx.courtyard('U4')
    if u4 is None:
        issues.append('P-10: U4 missing')
    else:
        g = r8.min_gap(region, u4, COAT_U4 + 5)
        ev['u4_mm'] = g
        if g is not None and g < COAT_U4 - EPS:
            issues.append(f'P-10: the coat region is {g:.3f} mm from U4; minimum {COAT_U4} mm (3 mm zone + 2 mm brush)')
    for ref in COAT_KEEPOFF:
        cy = ctx.courtyard(ref)
        if cy is not None and pcbnew.SHAPE.Collide(region, cy, 0):
            issues.append(f'P-10: the coat region reaches {ref} (a coating keep-off, ORDERING 5)')
    for f in ctx.board.GetFootprints():
        ref = f.GetReference()
        if re.fullmatch(r'TP\d+', ref) and ref != 'TP122':
            for p in f.Pads():
                for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                    if p.IsOnLayer(lay) and pcbnew.SHAPE.Collide(region, p.GetEffectiveShape(lay), 0):
                        issues.append(f'P-10: test pad {ref} lies in the coat region (only TP122 may)')
                        break
    return sorted(set(issues)), ev


def wire_room(face_x):
    return math.sqrt(BORE_WALL ** 2 - WIRE_Z ** 2) - abs(face_x - 23.0) - SLED_TOL


def entry_face(ctx, f, d):
    box = fc.model_box(f, ctx.folder) if ctx.folder else None
    if box is None:
        cy = r8.courtyard(f).BBox()
        box = (mm(cy.GetLeft()), mm(cy.GetTop()), mm(cy.GetRight()), mm(cy.GetBottom()), 0, 0)
    return {'-x': box[0], '+x': box[2], '-y': box[1], '+y': box[3]}[d], box


def axial_ok(ctx, f, d, face, box):
    """An axial entry (+-y): the courtyard's entry face within AXIAL_FACE of its edge (R8 J1 1.86 mm) and no other
    top courtyard between it and the edge."""
    x0, y0, x1, y1 = ctx.outline
    edge = y1 if d == '+y' else y0
    cyb = r8.courtyard(f).BBox()
    face = mm(cyb.GetBottom()) if d == '+y' else mm(cyb.GetTop())
    issues = []
    if abs(edge - face) > AXIAL_FACE + EPS:
        issues.append(f'{f.GetReference()}: entry face {abs(edge - face):.2f} mm from its edge (maximum {AXIAL_FACE})')
    lo, hi = sorted((face, edge))
    corridor = rect_poly(box[0], lo, box[2], hi)
    for g in ctx.board.GetFootprints():
        if g.GetReference() == f.GetReference() or g.IsFlipped():
            continue
        cy = r8.courtyard(g)
        if hi - lo > 0.01 and pcbnew.SHAPE.Collide(corridor, cy, -MM(0.01)):
            issues.append(f'{f.GetReference()}: {g.GetReference()} stands in front of the wire entry')
    return issues


def p11(ctx):
    issues, ev = [], {}
    for ref in ('J121', 'J124'):
        f = ctx.fps.get(ref)
        if f is None:
            issues.append(f'P-11: {ref} missing')
            continue
        d = entry_dir(f)
        ev[ref] = dict(entry=d)
        if d != ENTRY[ref]:
            issues.append(f'P-11: {ref} wires enter from {d}; the owner set {ENTRY[ref]} (pyro leads west, decision 1)')
        face, box = entry_face(ctx, f, d)
        if d in ('-x', '+x'):
            room = wire_room(face)
            ev[ref]['wire_room_mm'] = round(room, 3)
            if room < WIRE_ROOM - EPS:
                issues.append(f'P-11: {ref} has {room:.2f} mm of wire room to the bore wall (minimum {WIRE_ROOM}, R8)')
        else:
            issues += [f'P-11: {i}' for i in axial_ok(ctx, f, d, face, box)]
    return issues, ev


# ======================================================================================================================
# R-rules
# ======================================================================================================================
def rf_parts(ctx):
    return sorted(r for r in ctx.fps if r7.RF_PART.fullmatch(r))


def r1(ctx):
    issues, ev = [], {}
    yf = ctx.y_f
    deepest = None
    for ref in rf_parts(ctx):
        if ref in MCU_END:
            continue
        b = r8.courtyard(ctx.fps[ref]).BBox()
        y = mm(b.GetBottom())
        if deepest is None or y > deepest[0]:
            deepest = (round(y, 3), ref)
        if y > yf + EPS:
            issues.append(f'R-1: strip part {ref} reaches y {y:.2f} (strip boundary y_f {yf})')
    ev['deepest_strip_courtyard'] = deepest
    for f in ctx.board.GetFootprints():
        ref = f.GetReference()
        if r7.RF_PART.fullmatch(ref):
            continue
        for p in f.Pads():
            if mm(p.GetBoundingBox().GetTop()) < yf - EPS:
                issues.append(f'R-1: non-RF pad {ref}.{p.GetNumber()} ({p.GetNetname()}) lies in the strip (y < {yf})')
                break
    return issues, ev


def r2(ctx):
    issues, counted = [], defaultdict(float)
    yf = ctx.y_f
    b = ctx.board
    for t in b.GetTracks():
        if mm(t.GetBoundingBox().GetTop()) >= yf - 1e-6:
            continue
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            if not r8.STRIP_VIA.match(net):
                issues.append(f'R-2: via of {net} at {xy(t.GetPosition())} in the RF strip')
            continue
        lay = t.GetLayer()
        if lay == pcbnew.F_Cu:
            ok = bool(r7.STRIP_F.match(net))
        elif lay == pcbnew.B_Cu:
            ok = bool(STRIP_B_R9.match(net))
            if net == 'RADIO_TXEN':
                counted['RADIO_TXEN_B'] += mm(t.GetLength())
        else:
            ok = net == 'GND'
        if not ok:
            issues.append(f'R-2: {b.GetLayerName(lay)} track of {net} at {xy(t.GetStart())} in the RF strip')
    if counted['RADIO_TXEN_B'] > TXEN_B_MAX + EPS:
        issues.append(f'R-2: RADIO_TXEN runs {counted["RADIO_TXEN_B"]:.2f} mm on B.Cu in the strip (R8 {TXEN_B_MAX})')
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() == 'GND':
            continue
        for lay in z.GetLayerSet().CuStack():
            if z.HasFilledPolysForLayer(lay):
                polys = z.GetFilledPolysList(lay)
                if polys.OutlineCount() and mm(polys.BBox().GetTop()) < yf:
                    issues.append(f'R-2: {z.GetNetname()} pour on {b.GetLayerName(lay)} reaches the RF strip')
    x0, _, x1, _ = ctx.outline
    for lay, name in ((pcbnew.In1_Cu, 'In1'), (pcbnew.In2_Cu, 'In2')):
        gnd = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(lay)]
        cover = [z for z in gnd if mm(z.GetBoundingBox().GetTop()) <= 0.5 and mm(z.GetBoundingBox().GetBottom()) >= yf
                 and mm(z.GetBoundingBox().GetLeft()) <= x0 + 0.5 and mm(z.GetBoundingBox().GetRight()) >= x1 - 0.5]
        if not cover:
            issues.append(f'R-2: {name}: no GND pour spans the RF strip (x {x0:g}-{x1:g}, y 0.5-{yf})')
    for name, layers in r7.KEEPOUTS.items():
        same = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == name]
        have = {b.GetLayerName(l) for z in same for l in z.GetLayerSet().CuStack()}
        if not same or have != set(layers):
            issues.append(f'R-2: {name}: rule area on {", ".join(layers)} required (m3.kicad_dru keep-out rules use it)')
    return issues, {k: round(v, 3) for k, v in counted.items()}


def jacks(ctx):
    return sorted((f for f in ctx.board.GetFootprints() if fc.fp_name(f) == JACK_FP), key=lambda f: f.GetReference())


def jack_pad(f):
    return next((p for p in f.Pads() if p.GetNetname() and p.GetNetname() != 'GND' and
                 not p.GetNetname().startswith('unconnected')), None)


def r3(ctx):
    issues, ev = [], {}
    js = jacks(ctx)
    want = {'J30': 'GNSS_RF_ANT', 'J31': 'RADIO_RF_ANT'}
    if sorted(f.GetReference() for f in js) != ['J30', 'J31']:
        issues.append(f'R-3: exactly J30 and J31 must use {JACK_FP} (found {[f.GetReference() for f in js]})')
    y_aft = ctx.outline[1]
    for f in js:
        ref = f.GetReference()
        x, y = xy(f.GetPosition())
        ev[ref] = dict(x=round(x, 3), y=round(y, 3), rot=f.GetOrientationDegrees())
        p = jack_pad(f)
        if ref in want and (p is None or p.GetNetname() != want[ref]):
            issues.append(f'R-3: {ref} centre pad must be {want[ref]}')
        if f.IsFlipped() or abs(f.GetOrientationDegrees()) > 0.01 or abs(y - y_aft) > 0.005:
            issues.append(f'R-3: {ref} must be top side, rotation 0, on the aft edge y {y_aft:g} (is ({x:.3f}, {y:.3f}) '
                          f'rot {f.GetOrientationDegrees():g})')
        if not 3.6 - EPS <= x <= 42.4 + EPS:
            issues.append(f'R-3: {ref} axis x {x:.2f} outside 3.6-42.4 (plug envelope, fit)')
        for q in f.Pads():
            if q.IsOnLayer(pcbnew.F_Paste) or q.IsOnLayer(pcbnew.B_Paste):
                issues.append(f'R-3: {ref}.{q.GetNumber()}: SMA pads carry no paste')
    if len(js) == 2:
        d = math.dist(xy(js[0].GetPosition()), xy(js[1].GetPosition()))
        ev['spacing_mm'] = round(d, 3)
        if d < 12 - EPS:
            issues.append(f'R-3: jacks {d:.2f} mm apart (F10 >= 12 mm)')
    return issues, ev


def launch_area(ctx, f):
    """The In1 cut-out rule areas whose outline is the qualified rectangle in the jack's frame."""
    jx, jy = xy(f.GetPosition())
    hits = []
    for z in ctx.board.Zones():
        if not z.GetIsRuleArea():
            continue
        layers = {ctx.board.GetLayerName(l) for l in z.GetLayerSet().CuStack()}
        if layers != {'In1.Cu'} or not z.GetDoNotAllowZoneFills():
            continue
        pts = poly_points(z.Outline())
        if len(pts) != 4:
            continue
        rel = sorted((round(x - jx, 3), round(y - jy, 3)) for x, y in pts)
        L = LAUNCH
        want = sorted([(-L['x'], L['y0']), (-L['x'], L['y1']), (L['x'], L['y0']), (L['x'], L['y1'])])
        if all(abs(a[0] - b[0]) <= L['tol'] and abs(a[1] - b[1]) <= L['tol'] for a, b in zip(rel, want)):
            hits.append(z)
    return hits


def r4(ctx):
    issues, ev = [], {}
    L = LAUNCH
    gnd_vias = [xy(t.GetPosition()) for t in ctx.board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    in2 = [z for z in ctx.board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.In2_Cu)]
    fgnd = gnd_copper(ctx.board, pcbnew.F_Cu)
    for f in jacks(ctx):
        ref = f.GetReference()
        jx, jy = xy(f.GetPosition())
        areas = launch_area(ctx, f)
        if len(areas) != 1:
            issues.append(f'R-4: {ref}: exactly one In1-only, no-fill cut-out at x +-{L["x"]}, y {L["y0"]}-{L["y1"]} in the '
                          f'jack frame required (found {len(areas)})')
        miss, n = [], 0
        x0, x1 = jx - L['x'] - L['in2_grow'], jx + L['x'] + L['in2_grow']
        y0, y1 = jy + 0.6, jy + L['y1']
        k = 0
        while y0 + 0.1 * k <= y1 + 1e-6:
            i = 0
            while x0 + 0.1 * i <= x1 + 1e-6:
                q = pcbnew.VECTOR2I(MM(x0 + 0.1 * i), MM(y0 + 0.1 * k))
                n += 1
                if not any(z.HitTestFilledArea(pcbnew.In2_Cu, q) for z in in2):
                    miss.append((round(x0 + 0.1 * i, 2), round(y0 + 0.1 * k, 2)))
                i += 1
            k += 1
        if miss:
            issues.append(f'R-4: {ref}: In2 GND missing under the launch cut-out at {len(miss)} of {n} samples, e.g. {miss[:3]}')
        found = []
        for dx, dy in L['vias']:
            d = min((math.dist((jx + dx, jy + dy), v) for v in gnd_vias), default=99)
            found.append(round(d, 3))
            if d > L['via_tol'] + EPS:
                issues.append(f'R-4: {ref}: no GND via at the qualified spot ({dx:+.2f}, {dy:.2f}) in the jack frame '
                              f'(nearest {d:.3f} mm)')
        p = jack_pad(f)
        g = r8.min_gap(p.GetEffectiveShape(pcbnew.F_Cu), fgnd, 2.0) if p else None
        ev[ref] = dict(cutouts=len(areas), in2_missing=len(miss), via_offsets=found, pad_to_gnd_mm=g)
        if g is not None and g < L['gap'] - EPS:
            issues.append(f'R-4: {ref}: F.Cu GND {g:.3f} mm from the centre pad (minimum {L["gap"]} mm)')
    return issues, ev


def gnd_copper(board, layer, window=None):
    gnd = pcbnew.SHAPE_POLY_SET()
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer):
            gnd.BooleanAdd(z.GetFilledPolysList(layer))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == 'GND' and p.IsOnLayer(layer) and (window is None or p.GetPosition().y < MM(window)):
                p.TransformShapeToPolygon(gnd, layer, 0, MM(0.001), pcbnew.ERROR_INSIDE)
    for t in board.GetTracks():
        if t.GetNetname() == 'GND' and t.IsOnLayer(layer) and (window is None or t.GetBoundingBox().GetTop() < MM(window)):
            t.TransformShapeToPolygon(gnd, layer, 0, MM(0.001), pcbnew.ERROR_INSIDE)
    gnd.Simplify()
    return gnd


def chain_parts(ch):
    out = {ch['esd'], ch['series']} | set(ch['shunts'])
    if ch['bias']:
        out.add(ch['bias'])
    return out


def rf_path(ctx, name):
    """The chain's centreline from the jack pad centre to the module RF pad centre: (points, s0, s1, pads) where
    s0 / s1 are the path coordinates where it leaves the jack pad and enters the module pad."""
    ch = CHAINS[name]
    b = ctx.board
    jack = next((f for f in jacks(ctx) if jack_pad(f) and jack_pad(f).GetNetname() == ch['jack_net']), None)
    mod = ctx.fps.get(ch['module'])
    if jack is None or mod is None:
        return None
    jp, mp = jack_pad(jack), mod.FindPadByNumber(ch['pad'])
    tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in ch['nets']]
    nodes, adj = {}, defaultdict(list)

    def node(p):
        k = (round(p[0], 4), round(p[1], 4))
        nodes[k] = p
        return k

    def link(a, b_, w=None):
        w = math.dist(nodes[a], nodes[b_]) if w is None else w
        adj[a].append((b_, w))
        adj[b_].append((a, w))
    ends = []
    for t in tracks:
        a, c = node(xy(t.GetStart())), node(xy(t.GetEnd()))
        link(a, c)
        ends += [(a, t.GetLayer()), (c, t.GetLayer())]
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() in ch['nets']]
    pad_node = {}
    for p in pads:
        k = node(xy(p.GetPosition()))
        pad_node[pad_label(p)] = k
        for e, lay in ends:
            if p.IsOnLayer(lay) and p.HitTest(pcbnew.VECTOR2I(MM(nodes[e][0]), MM(nodes[e][1]))):
                link(e, k)
    ser = ctx.fps.get(ch['series'])
    if ser:
        sp = [pad_label(p) for p in ser.Pads() if p.GetNetname() in ch['nets']]
        if len(sp) == 2:
            link(pad_node[sp[0]], pad_node[sp[1]])
    start, goal = pad_node.get(pad_label(jp)), pad_node.get(pad_label(mp))
    if start is None or goal is None:
        return None
    import heapq
    dist, prev, q = {start: 0.0}, {}, [(0.0, start)]
    while q:
        d, u = heapq.heappop(q)
        if u == goal:
            break
        if d > dist.get(u, 1e9):
            continue
        for v, w in adj[u]:
            if d + w < dist.get(v, 1e9) - 1e-12:
                dist[v], prev[v] = d + w, u
                heapq.heappush(q, (d + w, v))
    if goal not in dist:
        return None
    seq = [goal]
    while seq[-1] != start:
        seq.append(prev[seq[-1]])
    pts = [nodes[k] for k in reversed(seq)]
    clean = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, clean[-1]) > 1e-6:
            clean.append(p)
    # where the path leaves the jack pad and enters the module pad (0.005 mm walk)
    sh_j = jp.GetEffectiveShape(pcbnew.F_Cu)
    sh_m = mp.GetEffectiveShape(pcbnew.F_Cu)
    total, cum = 0.0, [0.0]
    for a, c in zip(clean, clean[1:]):
        total += math.dist(a, c)
        cum.append(total)

    def at(s):
        for i in range(len(clean) - 1):
            if cum[i] - 1e-9 <= s <= cum[i + 1] + 1e-9:
                a, c = clean[i], clean[i + 1]
                L = cum[i + 1] - cum[i] or 1.0
                f_ = (s - cum[i]) / L
                return a[0] + (c[0] - a[0]) * f_, a[1] + (c[1] - a[1]) * f_
        return clean[-1]

    def inside(sh, p):
        return sh.Collide(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])), 0)
    s0 = 0.0
    while s0 < total and inside(sh_j, at(s0)):
        s0 += 0.005
    s1 = total
    while s1 > s0 and inside(sh_m, at(s1)):
        s1 -= 0.005
    return dict(points=clean, cum=cum, s0=s0, s1=s1, total=total, at=at, jack=jack, module_pad=mp, jack_pad=jp)


def path_bends(path):
    pts = [p for p in path['points']]
    s0, s1 = path['s0'], path['s1']
    heads = []
    for i, (a, c) in enumerate(zip(pts, pts[1:])):
        if path['cum'][i + 1] <= s0 + 1e-6 or path['cum'][i] >= s1 - 1e-6:
            continue
        if math.dist(a, c) < 1e-6:
            continue
        heads.append(math.degrees(math.atan2(c[1] - a[1], c[0] - a[0])))
    bends, verts = 0, []
    for i in range(1, len(heads)):
        d = abs((heads[i] - heads[i - 1] + 180) % 360 - 180)
        if d > 0.5:
            bends += 1
    for i in range(1, len(pts) - 1):
        a, b_, c = pts[i - 1], pts[i], pts[i + 1]
        h1 = math.atan2(b_[1] - a[1], b_[0] - a[0])
        h2 = math.atan2(c[1] - b_[1], c[0] - b_[0])
        if abs((math.degrees(h2 - h1) + 180) % 360 - 180) > 0.5:
            verts.append(b_)
    return bends, verts


def project(path, p):
    """(path coordinate, signed offset: + left of the direction of travel) of point p on the path."""
    best = None
    pts, cum = path['points'], path['cum']
    for i, (a, c) in enumerate(zip(pts, pts[1:])):
        L = math.dist(a, c)
        if L < 1e-9:
            continue
        ux, uy = (c[0] - a[0]) / L, (c[1] - a[1]) / L
        t = max(0.0, min(L, (p[0] - a[0]) * ux + (p[1] - a[1]) * uy))
        q = (a[0] + ux * t, a[1] + uy * t)
        d = math.dist(p, q)
        side = (p[0] - a[0]) * uy - (p[1] - a[1]) * ux       # y down: positive = to the left of travel on screen
        if best is None or d < best[1]:
            best = (cum[i] + t, d, 1 if side >= 0 else -1)
    return (best[0], best[1] * best[2]) if best else (None, None)


def beside(path, p, reach=0.5):
    """[(path coordinate, signed offset)] for each line segment point p sits beside: its foot on the segment within
    `reach` of the segment's ends (R8's rf_line_stitching per segment, along the path instead of along y)."""
    out = []
    pts, cum = path['points'], path['cum']
    for i, (a, c) in enumerate(zip(pts, pts[1:])):
        L = math.dist(a, c)
        if L < 1e-9:
            continue
        ux, uy = (c[0] - a[0]) / L, (c[1] - a[1]) / L
        t = (p[0] - a[0]) * ux + (p[1] - a[1]) * uy
        if not (-reach <= t <= L + reach):
            continue
        d = (p[0] - a[0]) * uy - (p[1] - a[1]) * ux
        out.append((cum[i] + max(0.0, min(L, t)), d))
    return out


def r5(ctx):
    issues, ev = [], {}
    b = ctx.board
    window = ctx.y_f + 3
    gnd = gnd_copper(b, pcbnew.F_Cu, window)
    in1 = pcbnew.SHAPE_POLY_SET()
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.In1_Cu) and \
                z.HasFilledPolysForLayer(pcbnew.In1_Cu):
            in1.BooleanAdd(z.GetFilledPolysList(pcbnew.In1_Cu))
    cut = pcbnew.SHAPE_POLY_SET()
    for f in jacks(ctx):
        for z in launch_area(ctx, f):
            cut.BooleanAdd(z.Outline())
    rf_nets = {n for ch in CHAINS.values() for n in ch['nets']}
    feat_pads = {}                                  # pad label -> (feature name, chain)
    for name, ch in CHAINS.items():
        for ref in sorted(chain_parts(ch)):
            f = ctx.fps.get(ref)
            for p in (f.Pads() if f else []):
                feat_pads[pad_label(p)] = (ref, name)
    steps = int(round(GCPW_REACH / GCPW_SCAN))
    windows = defaultdict(list)                     # (chain, feature) -> [sample path coordinates]
    worst = dict(max_gap=0.0, min_gap=9.0, line_max=0.0, line_min=9.0)   # line_*: samples outside the windows
    paths = {n: rf_path(ctx, n) for n in CHAINS}
    bend_pts = {n: (path_bends(p)[1] if p else []) for n, p in paths.items()}
    for t in sorted((t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in rf_nets),
                    key=lambda t: (xy(t.GetStart()), xy(t.GetEnd()))):
        chain = next(n for n, ch in CHAINS.items() if t.GetNetname() in ch['nets'])
        if abs(mm(t.GetWidth()) - RF_W) > 0.001:
            issues.append(f'R-5: RF track {t.GetNetname()} at {xy(t.GetStart())} is {mm(t.GetWidth()):.3f} mm wide '
                          f'(GCPW {RF_W} mm)')
        (ax, ay), (bx, by) = xy(t.GetStart()), xy(t.GetEnd())
        L = math.hypot(bx - ax, by - ay)
        if L < 1e-6:
            continue
        ux, uy = (bx - ax) / L, (by - ay) / L
        half = mm(t.GetWidth()) / 2
        n = int(L // GCPW_STEP) + 1
        for k in range(n + 1):
            s = min(k * GCPW_STEP, L)
            cx, cy = ax + ux * s, ay + uy * s
            gaps = []
            for sx, sy in ((-uy, ux), (uy, -ux)):
                hit = None
                for j in range(1, steps + 1):
                    d = half + j * GCPW_SCAN
                    if gnd.Contains(pcbnew.VECTOR2I(MM(cx + sx * d), MM(cy + sy * d))):
                        hit = j
                        break
                gaps.append(hit)
            pt = (cx, cy)
            pv = pcbnew.VECTOR2I(MM(cx), MM(cy))
            in_cut = cut.OutlineCount() and cut.Contains(pv)
            # In1 band (outside the launch cut-outs)
            if not in_cut:
                for o in range(-int(round(IN1_BAND / 0.05)), int(round(IN1_BAND / 0.05)) + 1):
                    qx, qy = cx + (-uy) * o * 0.05, cy + ux * o * 0.05
                    q = pcbnew.VECTOR2I(MM(qx), MM(qy))
                    if cut.OutlineCount() and cut.Contains(q):
                        continue
                    if not in1.Contains(q):
                        issues.append(f'R-5: In1 GND missing {o * 0.05:+.2f} mm beside RF track {t.GetNetname()} at '
                                      f'({cx:.2f}, {cy:.2f})')
                        break
            ok = all(g is not None and GAP_LO <= g <= GAP_HI for g in gaps)
            if gaps[0] and gaps[1]:
                worst['max_gap'] = max(worst['max_gap'], max(gaps) * GCPW_SCAN)
                worst['min_gap'] = min(worst['min_gap'], min(gaps) * GCPW_SCAN)
            if ok:
                worst['line_max'] = max(worst['line_max'], max(gaps) * GCPW_SCAN)
                worst['line_min'] = min(worst['line_min'], min(gaps) * GCPW_SCAN)
                continue
            # explain the sample
            path = paths[chain]
            feature = None
            jp = path['jack_pad'] if path else None
            mp = path['module_pad'] if path else None
            if in_cut or (jp and r8.min_gap(jp.GetEffectiveShape(pcbnew.F_Cu), pcbnew.SHAPE_CIRCLE(pv, 1), 0.6) is not None):
                feature = 'launch'
            elif mp and r8.min_gap(mp.GetEffectiveShape(pcbnew.F_Cu), pcbnew.SHAPE_CIRCLE(pv, 1), WINDOW_MAX) is not None:
                feature = 'module'
            else:
                # the sample's window is the chain part whose pad is nearest (within 0.3 mm), ties to the lower
                # designator: deterministic, where the first part found in a set depended on the hash seed
                # (R9P1-RF-03 / R9P1-INTEGRITY-01)
                near = None
                for ref in sorted(chain_parts(CHAINS[chain])):
                    f = ctx.fps.get(ref)
                    for p in (f.Pads() if f else []):
                        if not p.IsOnLayer(pcbnew.F_Cu):
                            continue
                        g = r8.min_gap(p.GetEffectiveShape(pcbnew.F_Cu), pcbnew.SHAPE_CIRCLE(pv, 1), 0.3)
                        if g is not None and (near is None or (g, ref) < near):
                            near = (g, ref)
                feature = near[1] if near else None
            if feature is None and any(math.dist(pt, v) <= 0.5 for v in bend_pts[chain]):
                g_mm = [None if g is None else g * GCPW_SCAN for g in gaps]
                if all(g is not None and GAP_LO <= g / GCPW_SCAN and g <= R5_BEND_GAP + 1e-9 for g in g_mm):
                    worst['line_max'] = max(worst['line_max'], max(g_mm))
                    worst['line_min'] = min(worst['line_min'], min(g_mm))
                    continue
                issues.append(f'R-5: bend sample ({cx:.2f}, {cy:.2f}) on {t.GetNetname()} has gaps {g_mm} mm (0.25-'
                              f'{R5_BEND_GAP} at a bend, re-solved)')
                continue
            if feature is None:
                g_mm = [None if g is None else round(g * GCPW_SCAN, 2) for g in gaps]
                issues.append(f'R-5: {t.GetNetname()} at ({cx:.2f}, {cy:.2f}): GND gaps {g_mm} mm outside the qualified '
                              '0.25-0.30 mm and in no declared window')
                continue
            windows[(chain, feature)].append(pt)
    # each window is one of R7's chain elements; a part pad on the line may be at most WINDOW_MAX long along it
    # (R7's 0402 pads: 35-39 ohm over 0.5-0.6 mm, pass2_rf 3.2); the launch is R-4's, the module entry its own pad
    pad_len = {}
    for name, ch in CHAINS.items():
        path = paths[name]
        if path is None:
            continue
        for ref in sorted(chain_parts(ch)):
            f = ctx.fps.get(ref)
            for p in (f.Pads() if f else []):
                if p.GetNetname() not in ch['nets'] or abs(project(path, xy(p.GetPosition()))[1]) > 0.05:
                    continue
                poly = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(poly, pcbnew.F_Cu, 0, MM(0.005), pcbnew.ERROR_OUTSIDE)
                ss = [project(path, q)[0] for q in poly_points(poly)]
                L = max(ss) - min(ss)
                pad_len[f'{name} {pad_label(p)}'] = round(L, 3)
                if L > WINDOW_MAX + EPS:
                    issues.append(f'R-5: {name}: {pad_label(p)} on the line is {L:.2f} mm long (a window may be at most '
                                  f'{WINDOW_MAX} mm)')
    ev.update(window_samples={f'{c} {f}': len(s) for (c, f), s in sorted(windows.items())}, line_pad_lengths=pad_len,
              gap_range_mm=[round(worst['min_gap'], 2), round(worst['max_gap'], 2)],
              line_gap_range_mm=[round(worst['line_min'], 2), round(worst['line_max'], 2)])
    # In1 under RF pads + 0.3 (outside the launch cut-outs), as check_r8.rf_line_stitching
    fill = in1
    for f in ctx.board.GetFootprints():
        if fc.fp_name(f) == JACK_FP:
            continue
        for p in f.Pads():
            if p.GetNetname() not in rf_nets:
                continue
            poly = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(poly, pcbnew.F_Cu, MM(r7.IN1_MARGIN), MM(0.005), pcbnew.ERROR_OUTSIDE)
            poly.BooleanSubtract(fill)
            if cut.OutlineCount():
                poly.BooleanSubtract(cut)
            a = area_mm2(poly)
            if a > EPS:
                issues.append(f'R-5: In1 GND missing under {pad_label(p)} (+{r7.IN1_MARGIN} mm): {a:.3f} mm2')
    return sorted(set(issues)), ev


def r6(ctx):
    issues, ev = [], {}
    for name, ch in CHAINS.items():
        path = rf_path(ctx, name)
        if path is None:
            issues.append(f'R-6: {name}: no RF path from the jack to {ch["module"]}.{ch["pad"]}')
            continue
        length = path['s1'] - path['s0']
        bends, _ = path_bends(path)
        ev[name] = dict(length_mm=round(length, 3), bends=bends)
        if length > ch['length'] + LENGTH_SLACK + 0.01:
            issues.append(f'R-6: {name} line is {length:.2f} mm from the jack pad end to the module pad (R7 '
                          f'{ch["length"]} + {LENGTH_SLACK} mm)')
        if bends > MAX_BENDS:
            issues.append(f'R-6: {name} line has {bends} bends (maximum {MAX_BENDS})')
    return issues, ev


def fence_check(ctx):
    issues, ev = [], {}
    x0, _, x1, _ = ctx.outline
    yf = ctx.y_f
    vias = [xy(t.GetPosition()) for t in ctx.board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND'
            and abs(mm(t.GetPosition().y) - yf) <= FENCE_BAND + 1e-6]
    if not vias:
        return [f'R-7: no GND fence vias within {FENCE_BAND} mm of y_f {yf}'], dict(fence_vias=0)
    row_y = sorted(v[1] for v in vias)[len(vias) // 2]
    xs = sorted(v[0] for v in vias)
    pts = [x0] + xs + [x1]
    lanes = []
    y = MM(row_y)
    for t in ctx.board.GetTracks():
        if t.GetClass() == 'PCB_VIA' or t.GetNetname() == 'GND':
            continue
        a, b_ = t.GetStart(), t.GetEnd()
        if (a.y - y) * (b_.y - y) < 0 or ((a.y == y) != (b_.y == y)):
            if a.y == b_.y:
                continue
            x = a.x + (b_.x - a.x) * (y - a.y) / (b_.y - a.y)
            lanes.append((mm(x), t.GetNetname()))
    openings = []
    for a, b_ in zip(pts, pts[1:]):
        if b_ - a <= FENCE_PITCH + 1e-6:
            continue
        crossing = sorted({n for x, n in lanes if a < x < b_})
        openings.append(dict(x0=round(a, 3), x1=round(b_, 3), width=round(b_ - a, 3), lanes=crossing))
        if not crossing:
            issues.append(f'R-7: fence: GND vias {b_ - a:.2f} mm apart between x {a:.2f} and {b_:.2f} with no lane through '
                          f'the gap (maximum {FENCE_PITCH} mm)')
        elif b_ - a > FENCE_OPENING_MAX + 1e-6:
            issues.append(f'R-7: fence: opening x {a:.2f}-{b_:.2f} is {b_ - a:.2f} mm wide (maximum {FENCE_OPENING_MAX} mm)')
    ev.update(fence_vias=len(xs), row_y=round(row_y, 3), openings=openings)
    return issues, ev


def r7_rule(ctx):
    issues, ev = [], {}
    gnd = [xy(t.GetPosition()) for t in ctx.board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    for name in CHAINS:
        path = rf_path(ctx, name)
        if path is None:
            issues.append(f'R-7: {name}: no RF path')
            continue
        s0, s1 = path['s0'], path['s1']
        sides = {1: [s0, s1], -1: [s0, s1]}
        for v in gnd:
            for s, d in beside(path, v):
                if s0 - 1e-6 <= s <= s1 + 1e-6 and STITCH_NEAR < abs(d) <= STITCH_FAR:
                    sides[1 if d > 0 else -1].append(s)
        # beside()'s +d is the left of travel on KiCad's y-down canvas: east (+x) for a line run from the jack forward
        # (+y), as both R9 lines are; the sides are named by compass (R9P1-RF-02), left / right only for a line that
        # runs neither way
        pts = path['points']
        run = pts[-1][1] - pts[0][1]
        names = ('east', 'west') if run > 0 else (('west', 'east') if run < 0 else ('left', 'right'))
        for side, ss in sides.items():
            ss = sorted(set(round(x, 4) for x in ss))
            gap = max(b_ - a for a, b_ in zip(ss, ss[1:]))
            label = names[0] if side > 0 else names[1]
            ev[f'{name}_{label}_largest_gap_mm'] = round(gap, 3)
            if gap > STITCH_GAP + EPS:
                issues.append(f'R-7: {name} {label}: GND stitching gap {gap:.2f} mm beside the RF line (maximum '
                              f'{STITCH_GAP} mm, no named ceilings)')
    found, ev['fence'] = fence_check(ctx)
    issues += found
    x0, _, x1, _ = ctx.outline
    for lid in (pcbnew.F_Cu, pcbnew.B_Cu):
        pts = rc.gnd_reach(ctx.board, lid, (x0, -1.0, x1, ctx.y_f + 5.0), (x0, -1.0, x1, ctx.y_f),
                           limit=STRIP_GND_REACH + 30)
        far = [(d, x, y) for d, x, y in pts if d is None or d > STRIP_GND_REACH]
        ev[f'gnd_reach_{ctx.board.GetLayerName(lid)}'] = round(max((d for d, _, _ in pts if d is not None), default=0), 2)
        shown = []
        for d, x, y in sorted(far, key=lambda t: -(t[0] or 1e9)):
            if all(math.dist((x, y), q[1:]) > 1.5 for q in shown):
                shown.append((d, x, y))
        for d, x, y in shown:
            issues.append(f'R-7: {ctx.board.GetLayerName(lid)} GND copper at ({x:.2f}, {y:.2f}) in the strip is '
                          f'{"unreachable" if d is None else f"{d:.2f} mm"} of copper from a GND via (maximum '
                          f'{STRIP_GND_REACH} mm)')
    found, ev['rf_ground_via_mm'] = r7.rf_grounds(ctx.board, '')
    issues += [f'R-7: {i}' for i in found]
    cov = {}
    for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        zs = [z for z in ctx.board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(lay)]
        n = hit = 0
        y = 0.6
        while y < ctx.y_f - 0.1:
            x = x0 + 0.6
            while x < x1 - 0.6:
                n += 1
                q = pcbnew.VECTOR2I(MM(x), MM(y))
                hit += any(z.HitTestFilledArea(lay, q) for z in zs)
                x += 0.5
            y += 0.5
        cov[ctx.board.GetLayerName(lay)] = round(hit / n, 3) if n else None
    ev['strip_gnd_coverage'] = cov
    return issues, ev


def module_regions(ctx, ref):
    """{layer name: SHAPE_POLY_SET} the module's keep-outs must cover (R-8): U31 B.Cu / In2 its body; F.Cu / In1 (and
    U30's F.Cu / In1) the body clipped at each pad row's inner edge less KEEPOUT_INSET."""
    f = ctx.fps.get(ref)
    if f is None:
        return {}
    w, h = BODY[ref]
    corners = [to_board(f, x, y) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    xs, ys = [c[0] for c in corners], [c[1] for c in corners]
    body = [min(xs), min(ys), max(xs), max(ys)]
    cx, cy = xy(f.GetPosition())
    inner = list(body)
    for p in f.Pads():
        if not p.GetNumber() or not p.IsOnLayer(pcbnew.F_Cu):
            continue
        b = p.GetBoundingBox()
        l, t, r, bo = mm(b.GetLeft()), mm(b.GetTop()), mm(b.GetRight()), mm(b.GetBottom())
        px, py = xy(p.GetPosition())
        dx, dy = px - cx, py - cy
        if abs(dx) >= abs(dy):
            if dx > 0:
                inner[2] = min(inner[2], l - KEEPOUT_INSET)
            else:
                inner[0] = max(inner[0], r + KEEPOUT_INSET)
        else:
            if dy > 0:
                inner[3] = min(inner[3], t - KEEPOUT_INSET)
            else:
                inner[1] = max(inner[1], bo + KEEPOUT_INSET)
    out = {}
    for lay in KEEPOUT_LAYERS[ref]:
        box = body if (ref == 'U31' and lay in ('In2.Cu', 'B.Cu')) else inner
        out[lay] = rect_poly(*box)
    return out


def r8_rule(ctx):
    issues, ev = [], {}
    b = ctx.board
    for ref, name in (('U30', 'U30_KEEPOUT'), ('U31', 'U31_KEEPOUT')):
        regions = module_regions(ctx, ref)
        if not regions:
            issues.append(f'R-8: {ref} missing')
            continue
        areas = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == name]
        for lay, need in regions.items():
            lid = b.GetLayerID(lay)
            cover = pcbnew.SHAPE_POLY_SET()
            for z in areas:
                if z.IsOnLayer(lid):
                    cover.BooleanAdd(z.Outline())
            r = residue(need, cover)
            bb = need.BBox()
            ev[f'{ref} {lay}'] = dict(required=[round(mm(v), 3) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(),
                                                                         bb.GetBottom())], uncovered_mm2=round(r, 4))
            if r > EPS:
                issues.append(f'R-8: {name} leaves {r:.3f} mm2 of {ref}\'s required region uncovered on {lay}')
            gl = [lay] if lay in ('In1.Cu', 'In2.Cu') else []
            for gname in gl:
                gid = b.GetLayerID(gname)
                gnd = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(gid)]
                # GND is sampled under U31's whole body on In1 as on In2 (the keep-out itself covers the pad-ring
                # interior on In1; survey 8.4 item 5, R8's module_ground; R9P1-INTEGRITY-02), under U30's keep-out on In1
                body = regions.get('In2.Cu')
                sb = body.BBox() if (ref == 'U31' and body is not None) else bb
                x0, y0, x1, y1 = [mm(v) for v in (sb.GetLeft(), sb.GetTop(), sb.GetRight(), sb.GetBottom())]
                miss, n = [], 0
                j = 0
                while y0 + 0.2 * j <= y1 + 1e-6:
                    i = 0
                    while x0 + 0.2 * i <= x1 + 1e-6:
                        q = pcbnew.VECTOR2I(MM(x0 + 0.2 * i), MM(y0 + 0.2 * j))
                        n += 1
                        if not any(z.HitTestFilledArea(gid, q) for z in gnd):
                            miss.append((round(x0 + 0.2 * i, 2), round(y0 + 0.2 * j, 2)))
                        i += 1
                    j += 1
                ev[f'{ref} {gname}']['gnd_sampled'] = dict(box=[round(v, 3) for v in (x0, y0, x1, y1)], samples=n,
                                                          missing=len(miss))
                if miss:
                    issues.append(f'R-8: {ref} {gname}: GND missing at {len(miss)} of {n} samples, e.g. {miss[:3]}')
        for t in b.GetTracks():
            if t.GetNetname() == 'GND':
                continue
            for z in areas:
                for lid in z.GetLayerSet().CuStack():
                    if t.IsOnLayer(lid) and pcbnew.SHAPE.Collide(z.Outline(), t.GetEffectiveShape(lid), 0):
                        issues.append(f'R-8: {t.GetNetname()} {"via" if t.GetClass() == "PCB_VIA" else "track"} at '
                                      f'{xy(t.GetPosition())} inside {name} on {b.GetLayerName(lid)}')
                        break
    return sorted(set(issues)), ev


def r9(ctx):
    issues, ev = [], {}
    for name, ch in CHAINS.items():
        path = rf_path(ctx, name)
        if path is None:
            issues.append(f'R-9: {name}: no RF path')
            continue
        s0 = path['s0']

        def line_pad(ref):
            f = ctx.fps.get(ref)
            return [p for p in (f.Pads() if f else []) if p.GetNetname() in ch['nets']]
        pos = {}
        for ref in [ch['esd'], ch['bias'], ch['series']]:
            if ref is None:
                continue
            pads = line_pad(ref)
            if not pads:
                issues.append(f'R-9: {name}: {ref} has no pad on the RF line')
                continue
            ss = [project(path, xy(p.GetPosition())) for p in pads]
            pos[ref] = min(s for s, d in ss)
            if ref != ch['series'] and min(abs(d) for s, d in ss) > 0.05:
                issues.append(f'R-9: {name}: {ref}\'s line pad is {min(abs(d) for s, d in ss):.3f} mm off the line '
                              '(no stub)')
        order = [r for r in (ch['esd'], ch['bias'], ch['series']) if r in pos]
        if [pos[r] for r in order] != sorted(pos[r] for r in order):
            issues.append(f'R-9: {name}: chain order jack -> ESD -> bias tap -> pi -> module broken ({order} at '
                          f'{[round(pos[r], 2) for r in order]})')
        if ch['esd'] in pos:
            e = pos[ch['esd']] - s0
            ev[f'{name}_esd_from_jack_pad_mm'] = round(e, 3)
            if e > ESD_MAX + EPS:
                issues.append(f'R-9: {name}: {ch["esd"]} is {e:.2f} mm (path) from the jack pad end (maximum {ESD_MAX})')
        if ch['bias']:
            lf, cf = ctx.fps.get(ch['bias']), ctx.fps.get(ch['bias_cap'])
            cold = [p for p in (lf.Pads() if lf else []) if p.GetNetname() not in ch['nets']]
            if cold and cf:
                cp = [p for p in cf.Pads() if p.GetNetname() == cold[0].GetNetname()]
                d = math.dist(xy(cold[0].GetPosition()), xy(cp[0].GetPosition())) if cp else None
                ev[f'{name}_bias_cap_mm'] = None if d is None else round(d, 3)
                if d is None or d > BIAS_CAP_MAX + EPS:
                    issues.append(f'R-9: {name}: {ch["bias_cap"]} is {d} mm from {ch["bias"]}\'s cold pad (maximum '
                                  f'{BIAS_CAP_MAX})')
            else:
                issues.append(f'R-9: {name}: bias tap / decoupler pads missing')
        for ref in ch['shunts']:
            pads = line_pad(ref)
            if not pads:
                issues.append(f'R-9: {name}: shunt {ref} not on the line')
                continue
            d = min(abs(project(path, xy(p.GetPosition()))[1]) for p in pads)
            ev[f'{name}_{ref}_stub_mm'] = round(d, 3)
            if d > STUB_MAX + 0.005:
                issues.append(f'R-9: {name}: {ref}\'s stub is {d:.3f} mm (maximum {STUB_MAX})')
            if not (ctx.fps[ref].GetAttributes() & pcbnew.FP_DNP):
                issues.append(f'R-9: {name}: shunt {ref} must be DNP')
    return issues, ev


def r10(ctx):
    found, ev = r8.rf_separation(ctx.board, RF_SEP_LINE)
    issues = [f'R-10: {i}' for i in found]
    for ref, v in ev['per_part'].items():
        if v['part'] and v['part'][0] < RF_SEP_PART - EPS:
            issues.append(f'R-10: RF part {ref} is {v["part"][0]:.2f} mm from {v["part"][1]} (r9_plan hard X9 >= '
                          f'{RF_SEP_PART} mm)')
    return sorted(set(issues)), dict(nearest_part=ev['nearest_part'], nearest_line=ev['nearest_line'])


def u30_body(ctx):
    f = ctx.fps.get('U30')
    w, h = BODY['U30']
    pts = [to_board(f, x, y) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    return rect_poly(min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def r11(ctx):
    issues, ev = [], {}
    if 'U30' not in ctx.fps or 'U31' not in ctx.fps:
        return ['R-11: modules missing'], ev
    body = u30_body(ctx)
    gnss = [it for it in ctx.net_items(lambda n: n in GNSS_RF) if not isinstance(it[4], pcbnew.ZONE)]
    radio_rf = [it for it in ctx.net_items(lambda n: n in RADIO_RF) if not isinstance(it[4], pcbnew.ZONE)]
    near = {}
    for it in ctx.net_items(lambda n: (n or '').startswith('RADIO_') and n not in RADIO_RF):
        if isinstance(it[4], pcbnew.ZONE):
            continue
        g = r8.min_gap(body, it[3], 30)
        lim = COEX_SPI if RADIO_SPI.match(it[1]) else COEX_BODY
        if g is not None:
            if it[1] not in near or g < near[it[1]][0]:
                near[it[1]] = (g, it[0])
            if g < lim - EPS:
                issues.append(f'R-11: {it[1]} {it[0]} is {g:.2f} mm from U30\'s body (minimum {lim})')
        for q in gnss:
            h = r8.min_gap(it[3], q[3], COEX_GNSS + 1)
            if h is not None and h < COEX_GNSS - EPS:
                issues.append(f'R-11: {it[1]} {it[0]} is {h:.2f} mm from GNSS RF copper (minimum {COEX_GNSS})')
                break
    ev['radio_to_u30_body'] = {k: [round(v[0], 3), v[1]] for k, v in sorted(near.items())}
    m = r8.min_gap(ctx.courtyard('U30'), ctx.courtyard('U31'), 40)
    ev['module_courtyards_mm'] = m
    if m is not None and m < COEX_MODULES - EPS:
        issues.append(f'R-11: module courtyards {m:.2f} mm apart (minimum {COEX_MODULES})')
    best = None
    for a in gnss:
        for c in radio_rf:
            g = r8.min_gap(a[3], c[3], 40)
            if g is not None and (best is None or g < best):
                best = g
    ev['rf_to_rf_mm'] = best
    if best is not None and best < COEX_RF - EPS:
        issues.append(f'R-11: GNSS RF copper {best:.2f} mm from radio RF copper (minimum {COEX_RF})')
    return sorted(set(issues)), ev


def r12(ctx):
    issues, ev = [], {}
    fps = ctx.fps
    for fb, net in (('FB30', '3V3_GNSS'), ('FB31', '3V3_RADIO')):
        f = fps.get(fb)
        if f is None or {p.GetNetname() for p in f.Pads()} != {'3V3', net}:
            issues.append(f'R-12: {fb} must join 3V3 to {net} alone')
    for (mod, pins, cap), lim in DECOUPLING.items():
        m, c = fps.get(mod), fps.get(cap)
        if m is None or c is None:
            issues.append(f'R-12: {mod} / {cap} missing')
            continue
        vcc = [m.FindPadByNumber(p) for p in pins]
        net = vcc[0].GetNetname()
        cp = [p for p in c.Pads() if p.GetNetname() == net]
        if not cp:
            issues.append(f'R-12: {cap} is not on {net}')
            continue
        d = min(math.dist(xy(v.GetPosition()), xy(cp[0].GetPosition())) for v in vcc)
        ev[f'{cap}_to_{mod}'] = round(d, 3)
        if d > lim + 0.005:
            issues.append(f'R-12: {cap} is {d:.2f} mm from {mod}\'s VCC pin (R7/R8 {lim} mm)')
    tracks = [t for t in ctx.board.GetTracks() if t.GetNetname() == '3V3_GNSS']
    r_tr = sum(mm(t.GetLength()) / mm(t.GetWidth()) * SHEET_R for t in tracks if t.GetClass() == 'PCB_TRACK')
    n_via = sum(1 for t in tracks if t.GetClass() == 'PCB_VIA')
    total = FB30_DCR + r_tr + n_via * VIA_R + FEED_3V3
    ev['gnss_vcc_ohm'] = dict(total=round(total, 4), fb30=FB30_DCR, tracks=round(r_tr, 4), vias=n_via,
                              feed_3v3_allowance=FEED_3V3)
    if total > GNSS_VCC_MAX:
        issues.append(f'R-12: GNSS VCC series resistance {total:.3f} ohm (u-blox IM 4.1.1 <= {GNSS_VCC_MAX})')
    return issues, ev


def r13(ctx):
    issues, ev = [], {}
    src = [('U31', ctx.courtyard('U31')), ('J31', ctx.courtyard('J31'))]
    src += [(it[0], it[3]) for it in ctx.net_items(lambda n: n in RADIO_RF) if not isinstance(it[4], pcbnew.ZONE)]
    src = [s for s in src if s[1] is not None]
    dst = [(r, ctx.courtyard(r)) for r in ('J121', 'J124') if r in ctx.fps]
    dst += [(it[0] + f' ({it[1]})', it[3]) for it in ctx.net_items(lambda n: n in ARMED)]
    best = None
    for a, sa in src:
        for c, sc in dst:
            g = r8.min_gap(sa, sc, RF_PYRO + 40)
            if g is not None and (best is None or g < best[0]):
                best = (g, a, c)
    other = None
    for a, sa in src:
        for it in ctx.net_items(lambda n: bool(CH1_NET.match(n or '')) and n not in ARMED):
            if isinstance(it[4], pcbnew.ZONE):
                continue
            g = r8.min_gap(sa, it[3], 120)
            if g is not None and (other is None or g < other[0]):
                other = (g, a, f'{it[0]} ({it[1]})')
    ev.update(nearest=best and [round(best[0], 2), best[1], best[2]],
              nearest_other_pyro_copper=other and [round(other[0], 2), other[1], other[2]])
    if best is None or best[0] < RF_PYRO - EPS:
        issues.append(f'R-13: radio (U31 / J31 / RF line) to the pyro terminals and armed copper: '
                      f'{best and round(best[0], 2)} mm ({best and best[1]} to {best and best[2]}); minimum {RF_PYRO} mm')
    return issues, ev


# ======================================================================================================================
# M-rules, F9-1, T-1
# ======================================================================================================================
def m2(ctx, board_sha=None):
    p = ctx.plate
    if p is None:
        return ['M-2: plate model (tools/plate_model.py on this board\'s fit report, --plate) not run'], {}
    f1 = p.get('f1', {}).get('jacks_only', {}).get('pinned_D5')
    issues = []
    if board_sha and p.get('board_sha256') != board_sha:
        issues.append('M-2: the plate model report is not bound to this board (board_sha256 of its fit report)')
    if f1 is None or f1 < F1_MIN:
        issues.append(f'M-2: first plate mode {f1} Hz (jacks only, pinned, D 5); minimum {F1_MIN} Hz')
    return issues, dict(f1_hz=f1, supports=p.get('supports'))


def m3(ctx):
    issues, ev = [], {}
    f = ctx.fps.get('J122')
    if f is None:
        return ['M-3: J122 missing'], ev
    ties, problems, info = fc.retention_holes(ctx.board, with_info=True)
    ev.update(info)
    issues += [f'M-3: {p}' for p in problems]
    if len(ties) == 2:
        seg = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(ties[0][0]), MM(ties[0][1])),
                                   pcbnew.VECTOR2I(MM(ties[1][0]), MM(ties[1][1])), 0)
        near = None
        for g in ctx.board.GetFootprints():
            if not g.IsFlipped():
                continue
            d = r8.min_gap(r8.courtyard(g), seg, TIE_CHANNEL + 1)
            if d is not None and (near is None or d < near[0]):
                near = (d, g.GetReference())
            if d is not None and d < TIE_CHANNEL - EPS:
                issues.append(f'M-3: bottom part {g.GetReference()} is {d:.2f} mm from the tie path (4 mm channel)')
        ev['channel_nearest'] = near
    return issues, ev


def m4(ctx):
    issues, ev = [], {}
    f = ctx.fps.get('J1')
    if f is None:
        return ['M-4: J1 missing'], ev
    lcsc = next((fld.GetText() for fld in f.GetFields() if fld.GetName() == 'LCSC'), None)
    if lcsc != J1_LCSC:
        issues.append(f'M-4: J1 must be the green DB128V-4P {J1_LCSC} (is {lcsc})')
    for ref in ('J121', 'J124'):
        if ref in ctx.fps:
            d = math.dist(xy(f.GetPosition()), xy(ctx.fps[ref].GetPosition()))
            ev[f'J1_to_{ref}'] = round(d, 2)
            if d > J1_GROUP + EPS:
                issues.append(f'M-4: J1 is {d:.2f} mm from {ref} (grouped within {J1_GROUP} mm, M3_R6)')
    d = entry_dir(f)
    ev['entry'] = d
    if d != ENTRY['J1']:
        issues.append(f'M-4: J1 wires enter from {d}; the owner set {ENTRY["J1"]}')
    face, box = entry_face(ctx, f, d)
    if d in ('+y', '-y'):
        issues += [f'M-4: {i}' for i in axial_ok(ctx, f, d, face, box)]
    return issues, ev


def m5(ctx):
    rep = ctx.fit()
    issues = [f'M-5: fit_check: {i}' for i in rep['issues']]
    rows = {r[1]: r[0] for r in rep['rows']}
    ev = {}
    for cat, (floor, why) in FIT_FLOORS.items():
        v = rows.get(cat)
        ev[cat] = None if v is None else round(v, 3)
        if v is None:
            issues.append(f'M-5: fit category {cat} not measured')
        elif v < floor - 1e-6:
            issues.append(f'M-5: {cat} fit margin {v:.3f} mm below R8\'s {floor} mm' + (f' (recorded: {why})' if why else ''))
    bot = [r[0] for r in rep['rows'] if r[2] == 'B']
    worst = min(bot) if bot else None
    ev['worst_bottom'] = worst
    if worst is not None and worst < FIT_BOTTOM - 1e-6:
        issues.append(f'M-5: worst bottom fit margin {worst:.3f} mm below R8\'s {FIT_BOTTOM} mm')
    ns, nt = rep.get('nearest_support'), rep.get('nearest_top_support')
    ev['support_bottom'], ev['support_top'] = ns and ns[0], nt and nt[0]
    if ns and ns[0] < FIT_SUPPORT_BOTTOM - 1e-6:
        issues.append(f'M-5: bottom part / pin {ns[0]:.3f} mm from a support, below R8\'s {FIT_SUPPORT_BOTTOM} mm ({ns[1]})')
    if nt and nt[0] < FIT_SUPPORT_TOP - 1e-6:
        issues.append(f'M-5: top hardware clearance {nt[0]:.3f} mm, below R8\'s {FIT_SUPPORT_TOP} mm ({nt[1]})')
    return issues, ev


def m6(ctx):
    issues = []
    supports = ctx.fit().get('supports', [])
    pyro_vias = [(xy(t.GetPosition()), mm(t.GetWidth(pcbnew.F_Cu)) / 2) for t in ctx.board.GetTracks()
                 if t.GetClass() == 'PCB_VIA' and re.match(r'^(PYRO|ARM1)', t.GetNetname() or '')]
    tht = [(f.GetReference(), xy(p.GetPosition()), max(mm(p.GetSize().x), mm(p.GetSize().y)) / 2)
           for f in ctx.board.GetFootprints() for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for f in ctx.board.GetFootprints():
        if not f.IsFlipped():
            continue
        ref = f.GetReference()
        if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in f.Pads()):
            issues.append(f'M-6: bottom part {ref} has through-hole pads (bottom parts SMD only)')
        cy = r8.courtyard(f)
        for r2_, c, rr in tht:
            if r2_ == ref:
                continue
            d = r8.min_gap(cy, pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])), MM(rr)), BOT_THT + 1)
            if d is not None and d < BOT_THT - EPS:
                issues.append(f'M-6: bottom part {ref} is {d:.2f} mm from {r2_}\'s through-hole pad (minimum {BOT_THT})')
                break
        for c in supports:
            d = r8.min_gap(cy, pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])), 1), BOT_M3 + 1)
            if d is not None and d < BOT_M3 - EPS:
                issues.append(f'M-6: bottom part {ref} is {d:.2f} mm from the M3 centre {tuple(c)} (minimum {BOT_M3})')
        if ref != 'TP122':
            for c, rr in pyro_vias:
                d = r8.min_gap(cy, pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])), MM(rr)), BOT_PYRO_VIA + 1)
                if d is not None and d < BOT_PYRO_VIA - EPS:
                    issues.append(f'M-6: bottom part {ref} is {d:.2f} mm from the pyro via {c} (minimum {BOT_PYRO_VIA})')
                    break
    return sorted(set(issues)), dict(pyro_vias=len(pyro_vias))


def mems_regions(f):
    cy = r8.courtyard(f).BBox()
    body = [mm(cy.GetLeft()) + MEMS_INSET, mm(cy.GetTop()) + MEMS_INSET, mm(cy.GetRight()) - MEMS_INSET,
            mm(cy.GetBottom()) - MEMS_INSET]
    cx, cyy = xy(f.GetPosition())
    inner = list(body)
    for p in f.Pads():
        if not p.GetNumber():
            continue
        b = p.GetBoundingBox()
        l, t, r, bo = mm(b.GetLeft()), mm(b.GetTop()), mm(b.GetRight()), mm(b.GetBottom())
        dx, dy = xy(p.GetPosition())[0] - cx, xy(p.GetPosition())[1] - cyy
        if abs(dx) >= abs(dy):
            if dx > 0:
                inner[2] = min(inner[2], l)
            else:
                inner[0] = max(inner[0], r)
        else:
            if dy > 0:
                inner[3] = min(inner[3], t)
            else:
                inner[1] = max(inner[1], bo)
    return body, inner


def m7(ctx):
    issues, ev = [], {}
    u4 = ctx.fps.get('U4')
    if u4 is None:
        return ['M-7: U4 missing'], ev
    rev = ctx.board.GetTitleBlock().GetRevision()
    want = IMU_ROTATION.get(rev, IMU_ROTATION_R9)
    ev['imu_rotation'] = dict(revision=rev, required=want, axis_map=IMU_MAP[want])
    if not u4.IsFlipped() or abs((u4.GetOrientationDegrees() - want + 180.0) % 360.0 - 180.0) > 0.01:
        issues.append(f'M-7: U4 must be bottom side, rotation {want:g} (the {IMU_MAP[want]} recorded for {rev}; a new map '
                      f'needs a recorded decision); is {"bottom" if u4.IsFlipped() else "top"} rot '
                      f'{u4.GetOrientationDegrees():g}')
    lever = abs(xy(u4.GetPosition())[0] - 23.0)
    ev['imu_lever_arm_mm'] = round(lever, 3)
    if lever > IMU_LEVER + EPS:
        issues.append(f'M-7: IMU lever arm |x - 23| {lever:.2f} mm (maximum {IMU_LEVER}, R8)')
    for ref in MEMS:
        f = ctx.fps.get(ref)
        if f is None:
            issues.append(f'M-7: {ref} missing')
            continue
        lay = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
        body, inner = mems_regions(f)
        bp, ip = rect_poly(*body), rect_poly(*inner)
        ev[ref] = dict(body=[round(v, 3) for v in body], interior=[round(v, 3) for v in inner])
        own = {p.GetNetname() for p in f.Pads()}
        for t in ctx.board.GetTracks():
            if not t.IsOnLayer(lay):
                continue
            s = t.GetEffectiveShape(lay)
            if t.GetClass() == 'PCB_VIA':
                if pcbnew.SHAPE.Collide(bp, s, 0):
                    issues.append(f'M-7: via {xy(t.GetPosition())} ({t.GetNetname()}) under {ref} (P3)')
            elif pcbnew.SHAPE.Collide(ip, s, 0):
                issues.append(f'M-7: track of {t.GetNetname()} at {xy(t.GetStart())} inside {ref}\'s pad-ring interior')
        for z in ctx.board.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(lay) or not z.HasFilledPolysForLayer(lay):
                continue
            fill = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lay))
            fill.BooleanIntersection(bp)
            if area_mm2(fill) > EPS:
                issues.append(f'M-7: {z.GetNetname()} fill under {ref} on {ctx.board.GetLayerName(lay)} (P3)')
        _ = own
    return sorted(set(issues)), ev


def f9(ctx):
    issues, ev = [], {}
    j1 = ctx.fps.get('J1')
    if j1 is None:
        return ['F9-1: J1 missing'], ev
    q = xy(j1.FindPadByNumber('1').GetPosition())
    for ref in PROTECTION:
        f = ctx.fps.get(ref)
        if f is None:
            issues.append(f'F9-1: {ref} missing')
            continue
        d = min(math.dist(q, xy(p.GetPosition())) for p in f.Pads())
        ev[ref] = round(d, 2)
        if d > PROTECTION_MAX + 0.005:
            issues.append(f'F9-1: {ref} is {d:.2f} mm from J1.1 (the hot-plug premise lumps the harness at J1: <= '
                          f'{PROTECTION_MAX} mm, D76)')
    u9 = ctx.fps.get('U9')
    if u9 is not None:
        pads = [p for p in u9.Pads() if p.GetNetname() == 'BAT_IN'] or list(u9.Pads())
        d = min(math.dist(q, xy(p.GetPosition())) for p in pads)
        ev['U9'] = round(d, 2)
        if d > U9_MAX + 0.005:
            issues.append(f'F9-1: U9 is {d:.2f} mm from J1.1 (step9/hotplug_feed.py modelled {U9_MAX} mm)')
    return issues, ev


def t1(ctx):
    issues, ev = TW.check(ctx.board)
    return [f'T-1: {i}' for i in issues], ev


# ======================================================================================================================
# K-rules (kept from check_r8)
# ======================================================================================================================
def k_contract(ctx, rows):
    issues, ev = [], {}
    b, fps = ctx.board, ctx.fps
    issues += r8.pin_table_issues(rows)
    pads = r7.pads_by_ref(b)
    for ref in sorted(r8.REMOVED & fps.keys()):
        issues.append('removed part remains: ' + ref)
    nets = {str(n) for n in b.GetNetsByName()}
    for net in sorted(n for n in nets if re.search(r'PYRO2|ARM2', n) or n.startswith(r7.REMOVED_NETS)):
        issues.append('removed net remains: ' + net)
    for ref, expected in {**r7.FOOTPRINTS, **R9_FOOTPRINTS}.items():
        if ref not in fps or fc.fp_name(fps[ref]) != expected:
            issues.append(f'{ref}: requires {expected}')

    def expect(ref, pin, net):
        p = pads.get((ref, str(pin)))
        actual = p.GetNetname() if p else None
        ok = actual == net if net is not None else p is not None and r8._nc(actual)
        if not ok:
            issues.append(f'{ref}.{pin}: expected {net or "NC"}, found {actual}')
    for ref, nets_ in r7.CONNECTORS.items():
        for pin, net in enumerate(nets_, 1):
            expect(ref, pin, net)
    issues.extend(r8.u1_pin_map(b, rows))
    for (ref, pin), net in r7.MODULE_PINS.items():
        expect(ref, pin, net)
    expect('U4', '4', 'IMU_INT1')

    def value(ref):
        return fps[ref].GetValue().split()[0].lower() if ref in fps else None
    for ref, one, two, val, end, far in r7.SERIES:
        expect(ref, 1, one)
        expect(ref, 2, two)
        if value(ref) != val.lower():
            issues.append(f'{ref}: requires {val} series resistance')
        if ref in fps and end in fps and far in fps and \
                math.dist(xy(fps[ref].GetPosition()), xy(fps[end].GetPosition())) >= \
                math.dist(xy(fps[ref].GetPosition()), xy(fps[far].GetPosition())):
            issues.append(f'{ref}: series resistor must sit at its driving end ({end})')
    issues.extend(r8.pulls(b))
    for ref in r7.DNP:
        f = fps.get(ref)
        want = pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
        if not f or (f.GetAttributes() & want) != want:
            issues.append(f'{ref}: DNP placeholder needs dnp, exclude-from-BOM and exclude-from-position flags')
    issues.extend(r7.dnp_paste(b))
    for ref in ('U30', 'U31'):
        if ref in fps and fps[ref].IsFlipped():
            issues.append(f'{ref}: module must be on the top side (single final reflow)')
    issues.extend(r7.rf_part_coverage(b))
    for ref in sorted(r for r in fps if r7.RF_PART.fullmatch(r)):
        for p in fps[ref].Pads():
            if r7.SAFETY_NETS.match(p.GetNetname() or ''):
                issues.append(f'{ref}.{p.GetNumber()}: RF part on safety net {p.GetNetname()}')
    x0, y0, x1, y1 = ctx.outline
    ev['outline_mm'] = ctx.outline
    if abs((x1 - x0) - 46) > 0.01 or (y1 - y0) > 120.01:
        issues.append(f'outline {x1 - x0:g} x {y1 - y0:g} mm violates 46 mm width / 120 mm maximum (P1)')
    edges = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() != pcbnew.SHAPE_T_CIRCLE]
    rect = (len(edges) == 1 and edges[0].GetShape() == pcbnew.SHAPE_T_RECT) or \
        (len(edges) == 4 and all(d.GetShape() == pcbnew.SHAPE_T_SEGMENT for d in edges) and
         all(abs(mm(d.GetStart().x) - mm(d.GetEnd().x)) < 1e-4 or abs(mm(d.GetStart().y) - mm(d.GetEnd().y)) < 1e-4
             for d in edges))
    if not rect or abs(x0) > 0.005 or abs(y0) > 0.005:
        issues.append(f'outline must be one rectangle from (0, 0) (four axis-parallel Edge.Cuts segments or one '
                      f'rectangle; found {len(edges)} edges from ({x0:g}, {y0:g}))')
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE and abs(mm(d.GetRadius()) - 1.6) > 0.01:
            issues.append(f'Edge.Cuts circle at {xy(d.GetCenter())} is not a 3.2 mm hole')
    if 'LS120' in fps and ctx.folder is not None:
        box = fc.model_box(fps['LS120'], ctx.folder)
        if box is None or max(box[2] - box[0], box[3] - box[1]) >= 8.5:
            issues.append('LS120: readable model smaller than 8.5 x 8.5 mm required')
    flash, bypass = pads.get(('U3', '8')), pads.get(('C29', '1'))
    if flash and bypass:
        distance = math.dist(xy(flash.GetPosition()), xy(bypass.GetPosition()))
        route = r7.direct_route(b, flash, bypass)
        ev.update(c29_vcc_pad_distance_mm=distance, c29_direct_route_mm=route)
        if distance > 2:
            issues.append(f'C29 VCC pad is {distance:.3f} mm from U3.8; maximum 2 mm')
        if route is None or route > 3:
            issues.append(f'C29 requires a direct same-layer route <=3 mm to U3.8; found {route}')
    else:
        issues.append('C29.1 or U3.8 is absent')
    found, ev['camera_bypass'] = r7.camera_bypass(b)
    issues.extend(found)
    found, ev['loader_pins'] = r8.loader_pins(b, rows)
    issues.extend(found)
    return issues, ev


def k_legends(ctx):
    issues = list(r7.duplicate_ids(ctx.board)) + list(r7.pin_legends(ctx.board)) + list(r7.legend_subjects(ctx.board))
    found, ev = r8.terminal_legends(ctx.board)
    return issues + found, dict(terminal_legends=ev)


def k_copper(ctx):
    b = ctx.board
    issues, ev = [], {}
    copper = r7.copper_shapes(b)
    issues += r7.vias_on_through_pads(b)
    found, ev['smd_pads_checked_for_via_holes'] = r7.vias_in_smd_pads(b)
    issues += found
    found, ev['track_endpoints_checked'] = r7.overlap_only_joints(b, copper)
    issues += found
    found, ev['small_ground_pads'] = r7.thermal_policy(b, ctx.dru or '')
    issues += found
    found, ev['via_paste'] = r8.via_paste(b)
    issues += found
    return issues, dict(ev, small_ground_pads=len(ev['small_ground_pads']))


def k_power_pyro(ctx):
    issues, ev = [], {}
    found, ev['inner_power_pyro'] = r8.inner_power_pyro(ctx.board, INNER_POWER_PYRO)
    issues += found
    found, ev['battery_pyro'] = r8.battery_pyro(ctx.board, BATTERY_PYRO)
    issues += found
    found, ev['gate_servo'] = r8.gate_servo(ctx.board, ctx.layer_pairs())
    issues += found
    return issues, ev


def k_inner_signal(ctx):
    issues, length = [], defaultdict(float)
    for t in ctx.board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            continue
        lay, net = t.GetLayer(), t.GetNetname()
        if lay == pcbnew.In1_Cu:
            key = 'In1'
        elif lay == pcbnew.In2_Cu and rc.net_class(net) != 'power':
            key = 'In2_signal'
        else:
            continue
        length[key] += mm(t.GetLength())
        issues.append(f'{key.split("_")[0]} track of {net} at {xy(t.GetStart())}: In1 carries no track (S16) and In2 '
                      'power and GND only (S15, D20; no exemption in R9)')
    return issues, {k: round(v, 2) for k, v in length.items()}


def k_actuators(ctx):
    d = hashlib.sha256(CHECK_ACTUATORS.read_bytes()).hexdigest() if CHECK_ACTUATORS.is_file() else None
    if d != CHECK_ACTUATORS_SHA:
        return [f'm3_design/check_actuators.py differs from its reviewed R9 version (sha256 {d}); a reviewed change '
                're-pins CHECK_ACTUATORS_SHA and records why'], dict(sha256=d)
    return [], dict(sha256=d)


# ======================================================================================================================
RULES = [
    ('LC-1', 'local clearance overrides', lambda c, s: lc1(c.board)),
    ('P-0', 'pyro spacing rules, geometric', lambda c, s: p0(c)),
    ('P-1', 'PYRO_BLOCK area by content (+ P-1b rule G scope)', lambda c, s: p1(c)),
    ('P-2', 'armed-live copper confined', lambda c, s: p2(c)),
    ('P-3', 'block purity', lambda c, s: p3(c)),
    ('P-4', 'rule H live', lambda c, s: p4(c, s)),
    ('P-5', 'solder-bridge table', lambda c, s: p5(c)),
    ('P-6', 'bare gate pads', lambda c, s: p6(c)),
    ('P-7', 'gate guard (reset voltage)', lambda c, s: p7(c)),
    ('P-8', 'sense resistors at the MCU end', lambda c, s: p8(c)),
    ('P-9', 'test pads and pyro vias', lambda c, s: p9(c)),
    ('P-10', 'coat region', lambda c, s: p10(c)),
    ('P-11', 'terminal entry', lambda c, s: p11(c)),
    ('R-1', 'strip extent', lambda c, s: r1(c)),
    ('R-2', 'strip layers', lambda c, s: r2(c)),
    ('R-3', 'jacks', lambda c, s: r3(c)),
    ('R-4', 'launch congruent', lambda c, s: r4(c)),
    ('R-5', 'GCPW cross-section', lambda c, s: r5(c)),
    ('R-6', 'RF line length', lambda c, s: r6(c)),
    ('R-7', 'RF stitching and fence', lambda c, s: r7_rule(c)),
    ('R-8', 'module keep-outs', lambda c, s: r8_rule(c)),
    ('R-9', 'chain topology', lambda c, s: r9(c)),
    ('R-10', 'RF separation', lambda c, s: r10(c)),
    ('R-11', 'coexistence geometry', lambda c, s: r11(c)),
    ('R-12', 'RF supply', lambda c, s: r12(c)),
    ('R-13', 'radio to pyro', lambda c, s: r13(c)),
    ('M-2', 'vibration (plate model)', lambda c, s: m2(c, s)),
    ('M-3', 'J122 tie holes', lambda c, s: m3(c)),
    ('M-4', 'J1', lambda c, s: m4(c)),
    ('M-5', 'fit', lambda c, s: m5(c)),
    ('M-6', 'bottom keep-outs', lambda c, s: m6(c)),
    ('M-7', 'IMU and MEMS', lambda c, s: m7(c)),
    ('F9-1', 'input protection at J1', lambda c, s: f9(c)),
    ('T-1', 'panel-tab windows', lambda c, s: t1(c)),
    ('K-contract', 'contract (pin map, connectors, series, outline)', None),
    ('K-legends', 'legends and ids', lambda c, s: k_legends(c)),
    ('K-copper', 'copper hygiene (vias in pads, joints, thermals, paste)', lambda c, s: k_copper(c)),
    ('K-power-pyro', 'D18 / D85 / D19 (strengthened)', lambda c, s: k_power_pyro(c)),
    ('K-inner', 'D20 In1 / In2 signal tracks', lambda c, s: k_inner_signal(c)),
    ('K-actuators', 'check_actuators.py pinned', lambda c, s: k_actuators(c)),
]


def check_board(board, folder=None, board_path=None, rows=None, fit=None, plate=None, seed=None, y_f=Y_F, only=None,
                board_sha=None, dru=None):
    rows = r8.load_pin_table(PIN_TABLE) if rows is None else rows
    ctx = Ctx(board, folder, board_path, fit, plate, seed, y_f, dru)
    out, flat = {}, []
    for rid, title, fn in RULES:
        if only and rid not in only:
            continue
        try:
            if rid == 'K-contract':
                issues, ev = k_contract(ctx, rows)
            else:
                issues, ev = fn(ctx, board_sha)
        except Exception as e:                       # a rule that cannot run fails, it never passes
            issues, ev = [f'{rid}: could not run: {type(e).__name__}: {e}'], {}
        out[rid] = dict(title=title, ok=not issues, issues=issues, evidence=ev)
        flat += [i if i.startswith(rid) else f'{rid}: {i}' for i in issues]
    return dict(ok=not flat, rules=out, issues=flat, failing=[k for k, v in out.items() if not v['ok']])


def file_sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', nargs='?', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--report', type=Path)
    ap.add_argument('--fit', type=Path, help='tools/fit_check.py --report of this board')
    ap.add_argument('--plate', type=Path, help='tools/plate_model.py --json of this board\'s fit report')
    ap.add_argument('--seed', type=Path, help='tools/rule_h_seed.py --json of this board')
    ap.add_argument('--only', help='comma-separated rule ids')
    ap.add_argument('--strip-y', type=float, default=Y_F, help=f'strip boundary y_f (the R9 contract is {Y_F}; other '
                    'values only to evaluate another revision)')
    a = ap.parse_args()
    bp = a.board.resolve()
    load = lambda p: json.loads(p.read_text()) if p else None      # noqa: E731

    def inputs():
        r = fc.input_hashes(bp)
        for p in (bp.with_suffix('.kicad_dru'), bp.with_suffix('.kicad_pro'), PIN_TABLE):
            r[p.name] = file_sha(p)
        return r
    before = inputs()
    sha = before[bp.name]
    fit = load(a.fit)
    if fit is not None and fit.get('board_sha256') != sha:
        print('FAIL the fit report is not bound to this board (board_sha256)')
        return 1
    report = check_board(pcbnew.LoadBoard(str(bp)), bp.parent, bp, fit=fit, plate=load(a.plate), seed=load(a.seed),
                         y_f=a.strip_y, only=set(a.only.split(',')) if a.only else None, board_sha=sha)
    if a.strip_y != Y_F:
        report['issues'].append(f'strip boundary {a.strip_y} is not the R9 contract\'s {Y_F}')
        report['ok'] = False
    if before != inputs():
        report['issues'].append('board, model, rules or pin table changed during check')
        report['ok'] = False
    report.update(board_sha256=sha, inputs_sha256=before, checker_sha256=file_sha(__file__))
    for rid, r in report['rules'].items():
        print(f"{rid:12s} {'OK  ' if r['ok'] else 'FAIL'} {r['title']}" + (f" ({len(r['issues'])})" if r['issues'] else ''))
    for i in report['issues']:
        print('FAIL', i)
    print('R9 CAD contract:', 'OK' if report['ok'] else f"FAIL ({len(report['issues'])} findings in "
          f"{len(report['failing'])} rules: {', '.join(report['failing'])})")
    if a.report:
        a.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
