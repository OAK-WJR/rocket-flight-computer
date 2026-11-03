#!/usr/bin/env python3
"""Spike (d): the radio and GNSS interface buses of R8, from U1's strip-facing pins to the rigid RF strip.

usage: <KiCad python3> -I rf_route_r8.py base.kicad_pcb out.kicad_pcb [--report out.json]

The base board is spike_base.py's (R8 netlist, seed placement with d_rf_place.tsv, only the rigid R7 copper). This
script adds every track and via of the spike's nets from the tables below, re-cuts the strip fence row (D16), fills
the zones natively and saves. It is written as the real build's rf_iface / gnss module would be: explicit polylines
(octilinear, pad-centre ends, collinear runs merged by construction), no autorouter, nothing hand-patched.

Geometry (KiCad mm, y = 0 at the aft edge; U1 at (23, 45), rotation 0, so pins 51-75 face the strip):
  - One "river" leaves U1's aft face and south-east corner as parallel 45-degree lanes on F.Cu over In1 GND:
    GNSS (pins 64-61) on its north-west side, radio (pins 56-53 and the east-face pair 47/46) on its south-east side.
  - GNSS: straight down from the pins, one 45-degree run to a vertical section at 0.6 mm pitch (R306 inline on RXD),
    a mitered turn west into four rows, each lane turning down into the strip at its module pin / series resistor.
  - Radio: every lane leaves its pin, takes one 45-degree run and runs straight down to its module pin: the aft trio
    RXEN / BUSY / MISO at 0.5 mm pitch, MOSI (R315 inline) and NSS (R310 tapped) at 0.6 mm; SCK (R313 inline) steps once
    to pass the rigid GND via (23.8, 17.7) on its east side.
  - DIO1 runs down beside NRST, one 45-degree step to x 32.4, straight down to U31.20; NRST takes one 45-degree run
    east to x 40 and R7's own strip path.
  - TXEN keeps R7's B.Cu loop (inherent; its two vias keep their rigid GND partners).
  - The fence row at y 23.3 is re-cut: GND vias <= 2.0 mm apart, openings <= 2.7 mm, each crossed by its lanes.
"""
import argparse
import json
import math
import shutil
import sys
from pathlib import Path

import pcbnew

mm, MM = pcbnew.ToMM, pcbnew.FromMM
W = 0.20            # signal lane width (plan_partial section 4)
W_RAIL = 0.30       # module supply (3V3_GNSS) and FB30 feed, as R7
W_RAIL_R = 0.40     # 3V3_RADIO and FB31 feed, as R7
W_STRIP = 0.15      # R7's TXEN loop kept as it was
VIA = (0.5, 0.3)    # signal via (R7 strip vias)
VIA_PWR = (0.6, 0.3)
VIA_FENCE = (0.5, 0.3)
FENCE_Y = 23.3


def r(v):
    return round(v, 4)


# ---------------------------------------------------------------------------------------------------------------------
# GNSS bus. Pins on U1's aft face (y 37.45), west to east: TXD 64, RXD 63, TP 62, RESET_N 61 (0.5 mm pitch).
G_PIN_Y = 37.45
G = [  # net (MCU side), pin x, vertical-section x, row y, strip x (where the lane turns down into the strip)
    ('GNSS_TXD_MCU', 22.5, 18.2, 28.2, 7.11),
    ('GNSS_RXD_MCU', 23.0, 18.8, 27.6, 8.21),
    ('GNSS_TP_MCU', 23.5, 19.4, 27.0, 9.00),
    ('GNSS_RESET_N', 24.0, 20.0, 26.4, 14.81),
]
G_TOP0, G_TOP_STEP = 36.40, 0.25    # 45-degree run starts: TXD at y 36.40, each lane east 0.25 mm lower (mitered)
G_TURN = 0.60                       # 45-degree corner leg of the turns into the rows and into the strip
R306_PADS = (30.03, 29.17)          # R306 (18.8, 29.6) rot 90: GNSS_RXD_MCU pad, GNSS_RXD pad
G_ENDS = {'GNSS_TXD_MCU': (7.11, 22.75), 'GNSS_RXD_MCU': (8.21, 19.70), 'GNSS_TP_MCU': (9.00, 22.88),
          'GNSS_RESET_N': (14.81, 19.70)}   # R305.2, U30.3, R307.2, U30.9


def gnss_lanes():
    out = []
    for i, (net, px, vx, row, sx) in enumerate(G):
        top = G_TOP0 - G_TOP_STEP * i
        bot = top - (px - vx)
        pts = [(px, G_PIN_Y), (px, top), (vx, bot)]
        pts += [(vx, row + G_TURN), (vx - G_TURN, row), (sx + G_TURN, row), (sx, row - G_TURN), G_ENDS[net]]
        if net == 'GNSS_RXD_MCU':           # R306 inline on the vertical section: split at its pads
            k = 3
            out.append((net, pts[:k] + [(vx, R306_PADS[0])], 'F.Cu', W))
            out.append(('GNSS_RXD', [(vx, R306_PADS[1])] + pts[k:], 'F.Cu', W))
        else:
            out.append((net, pts, 'F.Cu', W))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Radio bus. Aft-face pins (y 37.45): MOSI 53 x 28.0, MISO 54 27.5, BUSY 55 27.0, RXEN 56 26.5. East-face pins
# (x 30.55): NSS 47 y 40.5, SCK 46 41.0, DIO1 45 41.5, NRST 39 44.5.
# Above the fence: RXEN 20.6, BUSY 21.1, MISO 21.6 (0.5 mm pitch), a 1.0 mm slot (the fence's GND via, D16 openings
# <= 2.7 mm), MOSI 22.6 and NSS 23.2 (0.6 mm). Inside the strip the trio steps 0.4 mm east (RXEN 21.0, BUSY 21.5,
# MISO 22.0) so no GND finger is left between MISO and MOSI where no new GND via may go (strip_gnd is rigid); SCK 25.1
# steps once to x 24.5 and passes the rigid GND via (23.8, 17.7) on its east side; the rigid via (20, 19) bounds RXEN.
R_PIN_Y = 37.45
E_PIN_X = 30.55
TRIO = [('RADIO_RXEN', 26.5, 36.400, 20.6, 22.400), ('RADIO_BUSY', 27.0, 36.193, 21.1, 22.607),
        ('RADIO_MISO_MCU', 27.5, 35.986, 21.6, 22.814)]   # net, pin x, 45-degree run start, x above the fence, step y
TRIO_STEP = 0.4
ROW_Y = 29.5                        # R315 / R310 / R313 centres
R_PADS = (ROW_Y + 0.43, ROW_Y - 0.43)


def peel(net, x, y_pin, x_end):
    """down the gap at x, 45-degree corner of 0.4 mm, east along the module pin's row to x_end"""
    return [(x, r(y_pin + 0.4)), (r(x + 0.4), y_pin), (x_end, y_pin)]


def radio_lanes():
    out = []
    # aft trio: one mitered 45-degree run (pitch 0.5 kept), down through the fence, one mitered 0.4 mm step east in the
    # strip mouth, then straight down to the peel-offs
    for net, px, top, fx, step_y in TRIO:
        gx = r(fx + TRIO_STEP)
        bot = r(top - (px - fx))
        pts = [(px, R_PIN_Y), (px, top), (fx, bot), (fx, step_y), (gx, r(step_y - TRIO_STEP))]
        # the stepped trio turns east with square corners: a 45-degree corner after the 45-degree step would make an
        # S, SE, S, SE run with two segments under 1 mm (route_check staircase)
        if net == 'RADIO_RXEN':          # round U31's south-west corner through R312.1 (inline) to U31.10
            pts += [(gx, 7.58), (25.8, 7.58)]
            out.append((net, pts, 'F.Cu', W))
            out.append((net, [(25.8, 7.58), (26.9, 7.58), (27.32, 8.0), (27.32, 9.05)], 'F.Cu', W))
        elif net == 'RADIO_BUSY':
            out.append((net, pts + [(gx, 11.46), (24.91, 11.46)], 'F.Cu', W))
        else:                             # MISO_MCU ends at R314.2; R314.1 -> U31.12 is RADIO_MISO
            out.append((net, pts + [(gx, 12.73), (22.57, 12.73)], 'F.Cu', W))
            out.append(('RADIO_MISO', [(23.43, 12.73), (24.91, 12.73)], 'F.Cu', W))
    # MOSI: pin 53 x 28.0, 45-degree run (0.5 mm from MISO's) to x 22.6 (R315), straight down to U31.13
    mosi_k = -7.779
    out.append(('RADIO_MOSI_MCU', [(28.0, R_PIN_Y), (28.0, r(28.0 - mosi_k)), (22.6, r(22.6 - mosi_k)),
                                   (22.6, R_PADS[0])], 'F.Cu', W))
    out.append(('RADIO_MOSI', [(22.6, R_PADS[1])] + peel('RADIO_MOSI', 22.6, 14.0, 24.91), 'F.Cu', W))
    # NSS: east face, down x 31.65 past pins 48-50, 45-degree run to x 23.3; R310 tapped at its NSS pad by a stub
    nss_k = -7.072                                 # 45-degree line x - y = k (0.5 mm from MOSI's)
    out.append(('RADIO_NSS', [(E_PIN_X, 40.5), (31.65, 40.5), (31.65, r(31.65 - nss_k)), (23.2, r(23.2 - nss_k)),
                              (23.2, R_PADS[0])] + peel('RADIO_NSS', 23.2, 15.27, 24.91), 'F.Cu', W))
    out.append(('RADIO_NSS', [(23.2, R_PADS[0]), (24.1, R_PADS[0])], 'F.Cu', W))   # stub to R310.2 (D4 pull-up)
    # SCK: east face, down x 32.25, 45-degree run to x 25.1 (R313), down through the fence, step to the gap x 23.1
    sck_k = -5.6
    out.append(('RADIO_SCK_MCU', [(E_PIN_X, 41.0), (32.25, 41.0), (32.25, r(32.25 - sck_k)), (25.1, r(25.1 - sck_k)),
                                  (25.1, R_PADS[0])], 'F.Cu', W))
    # SCK passes the rigid GND via (23.8, 17.7) on its east side (x 24.5: 0.3 mm from the via, 0.26 mm clear of U31's
    # body edge x 24.86) and enters U31.15 from the north; a west-side pass would turn back east (a local bump)
    out.append(('RADIO_SCK', [(25.1, R_PADS[1]), (25.1, 22.4), (24.5, 21.8), (24.5, 16.54), (24.91, 16.54)], 'F.Cu', W))
    # DIO1: east face, down x 32.85, one 45-degree step to x 32.4, straight down to U31.20 between the rigid GND vias
    # (the step to x 32.4 sits below NRST's turn east, so no GND finger is left between DIO1 and NRST)
    out.append(('RADIO_DIO1', [(E_PIN_X, 41.5), (32.85, 41.5), (32.85, 30.9), (32.4, 30.45), (32.4, 18.95)],
                'F.Cu', W))
    # NRST: east face, down x 33.4 (clear of U12's pads), one 45-degree run east to x 40, R7's strip path to U31.3
    out.append(('RADIO_NRST', [(E_PIN_X, 44.5), (33.4, 44.5), (33.4, 31.0), (40.0, 24.4), (40.0, 14.4), (39.6, 14.0),
                               (37.0, 14.0)], 'F.Cu', W))
    out.append(('RADIO_NRST', [(37.0, 14.0), (34.81, 14.0)], 'F.Cu', W))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Strip-internal leads and module supplies (D11: regenerated; geometry R7's where R7's was already clean)
def strip_lanes():
    out = [
        ('GNSS_TXD', [(7.11, 19.70), (7.11, 21.89)], 'F.Cu', W),                       # U30.2 -> R305.1
        ('GNSS_TIMEPULSE', [(9.31, 19.70), (9.31, 21.71), (9.00, 22.02)], 'F.Cu', W),  # U30.4 -> R307.1 (R7)
        ('GNSS_SAFEBOOT_N', [(6.01, 10.20), (2.60, 10.20), (2.00, 9.60)], 'F.Cu', W),  # U30.18 -> TP30
        # 3V3_GNSS: U30.7 / U30.8 joined at y 20.75, up to C301.1, on to C300.1 and FB30.2 (R7 geometry)
        ('3V3_GNSS', [(12.61, 19.70), (12.61, 20.75)], 'F.Cu', W_RAIL),
        ('3V3_GNSS', [(13.71, 19.70), (13.71, 20.75), (12.61, 20.75)], 'F.Cu', W_RAIL),
        ('3V3_GNSS', [(12.61, 20.75), (12.61, 21.75), (12.74, 21.88), (12.08, 22.54), (11.58, 22.54), (11.58, 23.85)],
         'F.Cu', W_RAIL),
        ('3V3', [(11.58, 25.15), (12.33, 24.40)], 'F.Cu', W_RAIL),                      # FB30.1 -> In2 3V3 via
        # 3V3_RADIO: FB31.2 -> C310.1 -> C312.1 -> C311.1 -> U31.1
        ('3V3_RADIO', [(35.10, 20.85), (36.35, 19.60), (36.78, 19.60), (36.78, 17.50), (36.78, 16.54), (34.81, 16.54)],
         'F.Cu', W_RAIL_R),
        ('3V3', [(35.10, 22.15), (35.10, 24.40)], 'F.Cu', W_RAIL_R),                    # FB31.1 -> In2 3V3 via
        ('3V3', [(24.10, 29.07), (24.10, 28.45)], 'F.Cu', W),                           # R310.1 -> In2 3V3 via
        # TXEN: R7's B.Cu loop round U31's west side (pins 9 and 19), unchanged
        ('RADIO_TXEN', [(28.59, 9.05), (28.59, 7.80)], 'F.Cu', W_STRIP),
        ('RADIO_TXEN', [(28.59, 7.80), (24.80, 7.80), (24.50, 8.10), (24.50, 19.85), (24.80, 20.15), (31.13, 20.15)],
         'B.Cu', W_STRIP),
        ('RADIO_TXEN', [(31.13, 20.15), (31.13, 18.95)], 'F.Cu', W_STRIP),
    ]
    return out


# The antenna-bias limiter's DC copper under U30 (D11 regenerates it; this spike keeps R7's verbatim, widths and vias
# included, because it is not an interface bus). Measured: without it the native fill drops three F.Cu GND islands
# beside GNSS_RF_ANT (their only link to the pour runs where the limiter's F.Cu leads sit) and strip_gcpw changes.
LIMITER_R7 = [
    ('GNSS_ANT_DC', [(11.45, 5.15), (5.85, 10.75), (4.75, 10.75)], 'B.Cu', 0.20),
    ('GNSS_ANT_GATE', [(5.70, 12.75), (6.18, 13.23), (6.18, 14.25), (7.32, 14.25), (8.75, 14.25)], 'B.Cu', 0.20),
    ('GNSS_ANT_GATE', [(7.32, 14.25), (7.32, 15.75), (7.32, 16.90)], 'B.Cu', 0.20),
    ('GNSS_ANT_PD', [(8.18, 15.75), (9.50, 15.75), (11.00, 14.25)], 'B.Cu', 0.20),
    ('GNSS_ANT_SRC', [(7.925, 12.25), (7.925, 10.75), (6.425, 10.75), (4.425, 12.75), (3.80, 12.75), (5.32, 14.27)],
     'B.Cu', 0.20),
    ('GNSS_LNA_EN', [(11.51, 10.20), (11.51, 8.30)], 'F.Cu', 0.20),
    ('GNSS_LNA_EN', [(11.51, 8.30), (11.51, 11.60), (12.09, 12.18)], 'B.Cu', 0.20),     # R7: joined to the next
    ('GNSS_LNA_EN', [(12.25, 12.18), (13.00, 12.93), (13.00, 13.30)], 'B.Cu', 0.20),    # run through R303's pad
    ('GNSS_VCC_RF', [(10.41, 10.20), (10.41, 8.30)], 'F.Cu', 0.25),
    ('GNSS_VCC_RF', [(10.41, 8.30), (9.575, 9.135), (9.575, 10.75), (9.575, 12.25)], 'B.Cu', 0.25),
]
LIMITER_VIAS = [('GNSS_LNA_EN', 11.51, 8.30, (0.6, 0.3)), ('GNSS_VCC_RF', 10.41, 8.30, (0.6, 0.3))]

# GND vias outside the strip that stitch the pour between bus groups (route_check pour_finger: <= 4 mm of copper to a
# GND via): the MISO-MOSI slot and the NSS-SCK gap above the fence
STITCH = [(22.10, 26.70), (24.15, 26.50)]

# Status LEDs (D3 primary): west face pins 86 (LED_RED, y 44.0) and 88 (LED_YEL, y 45.0) to R32 / R33 and LED1 / LED2
# in two rows at the west edge; LED_RED turns aft first, so the two lanes never cross (USB_FAULT_N, pin 87 between them,
# leaves inward under U1: its family's)
def status_lanes():
    return [
        ('LED_RED', [(15.45, 44.0), (14.3, 44.0), (12.1, 41.8)], 'F.Cu', W),        # U1.86 -> R32.1
        ('LED_RED_A', [(10.1, 41.8), (7.45, 41.8)], 'F.Cu', W),                     # R32.2 -> LED1.2
        ('LED_YEL', [(15.45, 45.0), (13.3, 45.0), (12.3, 44.0)], 'F.Cu', W),        # U1.88 -> R33.1
        ('LED_YEL_A', [(10.3, 44.0), (7.55, 44.0)], 'F.Cu', W),                     # R33.2 -> LED2.1
    ]


VIAS = [('RADIO_TXEN', 28.59, 7.80, VIA), ('RADIO_TXEN', 31.13, 20.15, VIA),
        ('3V3', 12.33, 24.40, VIA_PWR), ('3V3', 35.10, 24.40, VIA_PWR), ('3V3', 24.10, 28.45, VIA)]

# Fence row (D16) at y 23.3: GND vias, west to east. Openings and the lanes that cross them are checked by check_r8.
FENCE_X = [0.90, 2.90, 4.90, 6.40, 7.685, 9.70, 12.30, 14.20, 16.20, 18.20, 20.00, 22.10, 24.15, 26.00, 28.00, 30.00,
           31.80, 33.00, 34.40, 35.80, 37.80, 39.40, 40.60, 42.60, 44.60]


# ---------------------------------------------------------------------------------------------------------------------
# Designators of the parts this spike places (the real build's r8_post does this board-wide): the first free spot on a
# spiral round the part, top silkscreen first, text box 0.15 mm clear of every exposed copper item and every other silk
# item on that side and 0.3 mm inside the outline; else the bottom silkscreen under the part (AGENTS section 3).
REF_PARTS = ('R306', 'R315', 'R310', 'R313', 'R32', 'R33', 'LED1', 'LED2', 'J2')
REF_GAP = 0.15


def _box(item, grow=0.0):
    bb = item.GetBoundingBox()
    g = MM(grow)
    return (bb.GetLeft() - g, bb.GetTop() - g, bb.GetRight() + g, bb.GetBottom() + g)


def _hit(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def place_refs(b):
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    outline = b.GetBoardEdgesBoundingBox()
    inside = (outline.GetLeft() + MM(0.3), outline.GetTop() + MM(0.3), outline.GetRight() - MM(0.3),
              outline.GetBottom() - MM(0.3))
    placed = {}
    for side, cu, silk in (('F', pcbnew.F_Cu, pcbnew.F_SilkS), ('B', pcbnew.B_Cu, pcbnew.B_SilkS)):
        copper = [_box(p, REF_GAP) for f in fps.values() for p in f.Pads()
                  if p.IsOnLayer(cu) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
        copper += [_box(v, REF_GAP) for v in b.GetTracks() if v.GetClass() == 'PCB_VIA']
        placed[side] = (copper, [])
    for f in fps.values():                    # every other footprint's silk (graphics and visible texts)
        for item in list(f.GraphicalItems()) + [f.Reference(), f.Value()]:
            if f.GetReference() in REF_PARTS and item is f.Reference():
                continue
            if item.GetLayer() == pcbnew.F_SilkS and (not hasattr(item, 'IsVisible') or item.IsVisible()):
                placed['F'][1].append(_box(item, REF_GAP))
            elif item.GetLayer() == pcbnew.B_SilkS and (not hasattr(item, 'IsVisible') or item.IsVisible()):
                placed['B'][1].append(_box(item, REF_GAP))
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.F_SilkS:
            placed['F'][1].append(_box(d, REF_GAP))
        elif d.GetLayer() == pcbnew.B_SilkS:
            placed['B'][1].append(_box(d, REF_GAP))
    offsets = [(0.0, 0.0)] + [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
                              for r in (1.0, 1.4, 1.8, 2.2, 2.6, 3.0) for a in range(0, 360, 30)]
    result = {}
    for ref in REF_PARTS:
        f = fps[ref]
        t = f.Reference()
        c = f.GetPosition()
        done = False
        for side in ('F', 'B') if not f.IsFlipped() else ('B', 'F'):
            layer = pcbnew.F_SilkS if side == 'F' else pcbnew.B_SilkS
            copper, silk = placed[side]
            t.SetLayer(layer)
            t.SetMirrored(side == 'B')
            for angle in (0, 90):
                t.SetTextAngleDegrees(angle)
                for dx, dy in offsets:
                    t.SetPosition(pcbnew.VECTOR2I(c.x + MM(round(dx, 2)), c.y + MM(round(dy, 2))))
                    bx = _box(t)
                    if bx[0] < inside[0] or bx[1] < inside[1] or bx[2] > inside[2] or bx[3] > inside[3]:
                        continue
                    if any(_hit(bx, o) for o in copper) or any(_hit(bx, o) for o in silk):
                        continue
                    silk.append(_box(t, REF_GAP))
                    result[ref] = (side, angle, round(dx, 2), round(dy, 2))
                    done = True
                    break
                if done:
                    break
            if done:
                break
        if not done:
            t.SetVisible(False)
            result[ref] = 'hidden'
    return result


def add_track(b, net, pts, layer, w, added):
    lid = b.GetLayerID(layer)
    ni = b.FindNet(net)
    assert ni is not None, net
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if abs(x0 - x1) < 1e-9 and abs(y0 - y1) < 1e-9:
            continue
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        assert dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6, f'{net}: not octilinear {(x0, y0)}-{(x1, y1)}'
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
        t.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        t.SetWidth(MM(w))
        t.SetLayer(lid)
        t.SetNet(ni)
        b.Add(t)
        added.append(dict(net=net, layer=layer, a=[x0, y0], b=[x1, y1], w=w))


def add_via(b, net, x, y, size, added):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(size[0]))
    v.SetDrill(MM(size[1]))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(b.FindNet(net))
    b.Add(v)
    added.append(dict(net=net, via=[x, y], size=list(size)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('base')
    ap.add_argument('out')
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    assert Path(args.base).with_suffix('.kicad_dru').is_file(), 'project rules must sit beside the board'
    b = pcbnew.LoadBoard(args.base)
    pcbnew.KIID.SeedGenerator(8402)                 # deterministic UUIDs (as r7_pcb.py): byte-identical rebuilds
    added = []
    for net, pts, layer, w in gnss_lanes() + radio_lanes() + strip_lanes() + status_lanes():
        add_track(b, net, [(r(x), r(y)) for x, y in pts], layer, w, added)
    for net, pts, layer, w in LIMITER_R7:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):        # R7's segments as they were (no octilinear assert)
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
            t.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
            t.SetWidth(MM(w))
            t.SetLayer(b.GetLayerID(layer))
            t.SetNet(b.FindNet(net))
            b.Add(t)
    for net, x, y, size in LIMITER_VIAS + VIAS:
        add_via(b, net, x, y, size, added)
    for x in FENCE_X:
        add_via(b, 'GND', x, FENCE_Y, VIA_FENCE, added)
    for x, y in STITCH:
        add_via(b, 'GND', x, y, VIA_FENCE, added)
    refs = place_refs(b)
    b.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    # Save the board only (aSkipSettings): saving through the API rewrites the project file with KiCad's defaults
    # (netclass clearance 0.2 mm, no minimum clearance) when the output sits in another folder, and the next load then
    # fills and checks with the wrong rules (measured). The project files are copied from the input instead.
    out = Path(args.out)
    assert pcbnew.SaveBoard(str(out), b, True), 'save failed'
    for ext in ('.kicad_pro', '.kicad_dru'):
        if Path(args.base).with_suffix(ext).resolve() != out.with_suffix(ext).resolve():
            shutil.copyfile(Path(args.base).with_suffix(ext), out.with_suffix(ext))
    tracks = [a for a in added if 'a' in a]
    length = {}
    for a in tracks:
        length[a['net']] = length.get(a['net'], 0) + math.dist(a['a'], a['b'])
    print(f'added {len(tracks)} track segments ({sum(length.values()):.1f} mm), '
          f'{sum(1 for a in added if "via" in a)} vias ({len(FENCE_X)} fence)')
    if args.report:
        args.report.write_text(json.dumps(dict(added=added, refs=refs,
                                               length_mm={k: round(v, 2) for k, v in length.items()}), indent=1) + '\n')


if __name__ == '__main__':
    main()
