"""R8 step 6 family rf (rf_iface / gnss): the radio and GNSS interface buses, the strip leads, the module supplies and
the antenna-bias limiter's DC copper (r8_route.py).

Port of spike (d) (m3_design/r8_spikes/d_rf/rf_route_r8.py, RESULT.md section 4), on the placement it proved
(r8_place.tsv basis spike-d / P1-P3), with the H0 pin map (R8_DECISIONS D2, D4; IOSWP) and the limiter redrawn (D11,
D51). Lanes are 0.2 mm on F.Cu over In1 GND with pad-centre ends.
  - One "river" leaves U1's aft face and south-east corner as parallel 45-degree lanes: GNSS (pins 64-61) on its
    north-west side, radio (pins 56-53 and the east-face pair 47 / 46) on its south-east side; mitred corners keep
    each group's pitch through the 45-degree runs.
  - GNSS: straight down from the pins, one 45-degree run to a vertical section at 0.6 mm pitch (R306 inline on RXD),
    a mitred turn west into four rows, each lane turning down into the strip at its module pin or series resistor.
  - Radio: the aft trio RXEN / BUSY / MISO at 0.5 mm pitch, one mitred 0.5 mm step east inside the strip mouth, then
    straight down to its module pins; MOSI (R315 inline) and NSS (R310 tapped at the MCU end, D4) at 0.6 mm; SCK
    (R313 inline) passes the rigid GND via (23.8, 17.7) on its east side; DIO1 straight down to U31.20; NRST one
    45-degree run east to x 40 and R7's strip path through R311 to U31.3.
  - TXEN keeps R7's B.Cu loop round U31's west side (inherent: pins 9 and 19, nothing may cross U31's pad field; it
    passes on route_check's keep-out-aware baseline, D10 / D21); its two vias keep their rigid GND partners.
  - The module supplies: 3V3_GNSS and 3V3_RADIO from FB30 / FB31, whose 3V3 sides drop to In2 3V3 by one via each, and
    R310's 3V3 via (D4).
  - The limiter (D11, D51): U30's LNA_EN / VCC_RF pads (F.Cu, aft row) drop through vias just outside their pad ends
    (U30_KEEPOUT closes F.Cu / In1 to non-GND vias and tracks under the module), then B.Cu under U30 to R303 / Q31 and
    R300 / Q32; ANT_DC, ANT_SRC, ANT_GATE and ANT_PD on B.Cu with R7's copper length on Q30's drain and source.
The strip fence row and stitching are step 7's (r8_ground.py, spike (d) FENCE_X / STITCH).
"""
from r8_route import W, VIA_SIG, VIA_PWR, u1_pin

NETS = ('GNSS_TXD_MCU', 'GNSS_TXD', 'GNSS_RXD_MCU', 'GNSS_RXD', 'GNSS_TP_MCU', 'GNSS_TIMEPULSE', 'GNSS_RESET_N',
        'GNSS_SAFEBOOT_N', 'RADIO_RXEN', 'RADIO_BUSY', 'RADIO_MISO_MCU', 'RADIO_MISO', 'RADIO_MOSI_MCU', 'RADIO_MOSI',
        'RADIO_NSS', 'RADIO_SCK_MCU', 'RADIO_SCK', 'RADIO_DIO1', 'RADIO_NRST', 'RADIO_TXEN', '3V3_GNSS', '3V3_RADIO',
        'GNSS_LNA_EN', 'GNSS_VCC_RF', 'GNSS_ANT_DC', 'GNSS_ANT_SRC', 'GNSS_ANT_GATE', 'GNSS_ANT_PD')
RAILS = ('3V3',)
# spike (d): interface 394.8 mm, 2 signal vias (TXEN); + limiter about 45 mm and its 2 vias (D51)
# ratio 2.40: GNSS_VCC_RF 2.37 since fix pass 1 (D87: the limiter vias at R7's y 8.3, clear of U30's paste; was 1.95
# for the step-6 spot y 8.9, whose paste defect R8P1-DFM-01 found); the other nets are unchanged
BUDGET = dict(length_mm=445.0, vias=4, critical_layer_changes=4, ratio=2.40)
W_RAIL, W_RAIL_R, W_STRIP = 0.30, 0.40, 0.15     # 3V3_GNSS / FB30 feed, 3V3_RADIO / FB31 feed, R7's TXEN loop


def r(v):
    return round(v, 4)


# ---------------------------------------------------------------------------------------------------------------------
# GNSS bus. Pins on U1's aft face (y 37.45), west to east: TXD 64, RXD 63, TP 62, RESET_N 61 (0.5 mm pitch).
G_PIN_Y = 37.45
G = [  # net (MCU side), pin, vertical-section x, row y, strip x (where the lane turns down into the strip)
    ('GNSS_TXD_MCU', 64, 18.2, 28.2, 7.11),
    ('GNSS_RXD_MCU', 63, 18.8, 27.6, 8.21),
    ('GNSS_TP_MCU', 62, 19.4, 27.0, 9.00),
    ('GNSS_RESET_N', 61, 20.0, 26.4, 14.81),
]
G_TOP0, G_TOP_STEP = 36.40, 0.25    # 45-degree run starts: TXD at y 36.40, each lane east 0.25 mm lower (mitred)
G_TURN = 0.60                       # 45-degree corner leg of the turns into the rows and into the strip
R306_PADS = (30.03, 29.17)          # R306 (18.8, 29.6) rot 90: GNSS_RXD_MCU pad, GNSS_RXD pad
G_ENDS = {'GNSS_TXD_MCU': (7.11, 22.75), 'GNSS_RXD_MCU': (8.21, 19.70), 'GNSS_TP_MCU': (9.00, 22.88),
          'GNSS_RESET_N': (14.81, 19.70)}   # R305.2, U30.3, R307.2, U30.9


def gnss_lanes():
    out = []
    for i, (net, pin, vx, row, sx) in enumerate(G):
        px = u1_pin(pin)[0]
        top = G_TOP0 - G_TOP_STEP * i
        bot = top - (px - vx)
        pts = [(px, G_PIN_Y), (px, top), (vx, bot)]
        pts += [(vx, row + G_TURN), (vx - G_TURN, row), (sx + G_TURN, row), (sx, row - G_TURN), G_ENDS[net]]
        if net == 'GNSS_RXD_MCU':           # R306 inline on the vertical section: split at its pads
            out.append((net, 'F', W, pts[:3] + [(vx, R306_PADS[0])]))
            out.append(('GNSS_RXD', 'F', W, [(vx, R306_PADS[1])] + pts[3:]))
        else:
            out.append((net, 'F', W, pts))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Radio bus. Aft-face pins (y 37.45): MOSI 53 x 28.0, MISO 54 27.5, BUSY 55 27.0, RXEN 56 26.5. East-face pins
# (x 30.55): NSS 47 y 40.5, SCK 46 41.0, DIO1 45 41.5, NRST 39 44.5. Above the fence: RXEN 20.5, BUSY 21.0, MISO 21.5
# (0.5 mm pitch), a 1.1 mm slot (the fence GND via (22.05, 23.3) and spike (d)'s stitch via (22.05, 26.7), D16), MOSI
# 22.6 and NSS 23.2 (0.6 mm). Inside the strip the trio steps 0.5 mm east (one lane pitch: RXEN 21.0, BUSY 21.5, MISO
# 22.0) so no GND finger is left between MISO and MOSI where no new GND via may go (strip_gnd is rigid); SCK 25.1 steps
# once to x 24.5 and passes the rigid GND via (23.8, 17.7) on its east side; the rigid via (20, 19) bounds RXEN.
# Fix pass 4 (R8P4-ROUTING-01, D110): the trio sat 0.1 mm east of centre in its fence opening (x 20.6 / 21.1 / 21.6,
# step 0.4 mm), so MISO and MOSI were 0.150 mm from the fence and stitch vias then at x 22.1; with the trio 0.1 mm west
# and those vias (and the west fence via) 0.05 mm west (step7/make_ground.py), RXEN, MISO and MOSI are each 0.200 mm
# from the vias. The in-strip lanes and the 45-degree runs to U1 stay on the same lines
R_PIN_Y = 37.45
E_PIN_X = 30.55
TRIO = [('RADIO_RXEN', 56, 36.400, 20.5, 22.500), ('RADIO_BUSY', 55, 36.193, 21.0, 22.707),
        ('RADIO_MISO_MCU', 54, 35.986, 21.5, 22.914)]   # net, pin, 45-degree run start, x above the fence, step y
TRIO_STEP = 0.5
ROW_Y = 29.5                        # R315 / R310 / R313 centres
R_PADS = (ROW_Y + 0.43, ROW_Y - 0.43)


def peel(x, y_pin, x_end):
    """down the gap at x, 45-degree corner of 0.4 mm, east along the module pin's row to x_end"""
    return [(x, r(y_pin + 0.4)), (r(x + 0.4), y_pin), (x_end, y_pin)]


def radio_lanes():
    out = []
    # aft trio: one mitred 45-degree run (pitch 0.5 kept), down through the fence, one mitred 0.5 mm step east in the
    # strip mouth, then straight down to the peel-offs; the trio's module-end corners are square (a 45-degree corner
    # after the 45-degree step would make an S, SE, S, SE run with two segments under 1 mm: a route_check staircase)
    for net, pin, top, fx, step_y in TRIO:
        px = u1_pin(pin)[0]
        gx = r(fx + TRIO_STEP)
        bot = r(top - (px - fx))
        pts = [(px, R_PIN_Y), (px, top), (fx, bot), (fx, step_y), (gx, r(step_y - TRIO_STEP))]
        if net == 'RADIO_RXEN':          # round U31's south-west corner through R312.1 (inline pull-down) to U31.10
            out.append((net, 'F', W, pts + [(gx, 7.58), (25.8, 7.58)]))
            out.append((net, 'F', W, [(25.8, 7.58), (26.9, 7.58), (27.32, 8.0), (27.32, 9.05)]))
        elif net == 'RADIO_BUSY':
            out.append((net, 'F', W, pts + [(gx, 11.46), (24.91, 11.46)]))
        else:                             # MISO_MCU ends at R314.2; R314.1 -> U31.12 is RADIO_MISO
            out.append((net, 'F', W, pts + [(gx, 12.73), (22.57, 12.73)]))
            out.append(('RADIO_MISO', 'F', W, [(23.43, 12.73), (24.91, 12.73)]))
    # MOSI: pin 53, 45-degree run (0.5 mm from MISO's) to x 22.6 (R315 inline), straight down to U31.13
    mosi_k = -7.779
    out.append(('RADIO_MOSI_MCU', 'F', W, [u1_pin(53), (28.0, r(28.0 - mosi_k)), (22.6, r(22.6 - mosi_k)),
                                           (22.6, R_PADS[0])]))
    out.append(('RADIO_MOSI', 'F', W, [(22.6, R_PADS[1])] + peel(22.6, 14.0, 24.91)))
    # NSS: east face, down x 31.65 past pins 48-50, 45-degree run to x 23.2; R310 tapped at its NSS pad by a stub
    nss_k = -7.072                                 # 45-degree line x - y = k (0.5 mm from MOSI's)
    out.append(('RADIO_NSS', 'F', W, [u1_pin(47), (31.65, 40.5), (31.65, r(31.65 - nss_k)), (23.2, r(23.2 - nss_k)),
                                      (23.2, R_PADS[0])] + peel(23.2, 15.27, 24.91)))
    out.append(('RADIO_NSS', 'F', W, [(23.2, R_PADS[0]), (24.1, R_PADS[0])]))   # stub to R310.2 (D4 pull-up)
    # SCK: east face, down x 32.25, 45-degree run to x 25.1 (R313 inline), down through the fence; past the rigid GND
    # via (23.8, 17.7) on its east side (x 24.5: 0.3 mm from the via, 0.26 mm clear of U31's body edge x 24.86) into
    # U31.15 from the north (a west-side pass would turn back east: a local bump)
    sck_k = -5.6
    out.append(('RADIO_SCK_MCU', 'F', W, [u1_pin(46), (32.25, 41.0), (32.25, r(32.25 - sck_k)),
                                          (25.1, r(25.1 - sck_k)), (25.1, R_PADS[0])]))
    out.append(('RADIO_SCK', 'F', W, [(25.1, R_PADS[1]), (25.1, 22.4), (24.5, 21.8), (24.5, 16.54), (24.91, 16.54)]))
    # DIO1: east face, down x 32.85, one 45-degree step to x 32.4 (below NRST's turn east, so no GND finger is left
    # between DIO1 and NRST), straight down to U31.20 between the rigid GND vias (31.73 / 33.0, 20.55)
    out.append(('RADIO_DIO1', 'F', W, [u1_pin(45), (32.85, 41.5), (32.85, 30.9), (32.4, 30.45), (32.4, 18.95)]))
    # NRST: east face, down x 33.4 (clear of U12's pads), one 45-degree run east to x 40, R7's strip path to U31.3
    out.append(('RADIO_NRST', 'F', W, [u1_pin(39), (33.4, 44.5), (33.4, 31.0), (40.0, 24.4), (40.0, 14.4),
                                       (39.6, 14.0), (37.0, 14.0)]))
    out.append(('RADIO_NRST', 'F', W, [(37.0, 14.0), (34.81, 14.0)]))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Strip-internal leads and module supplies (D11: regenerated; R7's geometry where it was already clean)
def strip_lanes():
    return [
        ('GNSS_TXD', 'F', W, [(7.11, 19.70), (7.11, 21.89)]),                       # U30.2 -> R305.1
        ('GNSS_TIMEPULSE', 'F', W, [(9.31, 19.70), (9.31, 21.71), (9.00, 22.02)]),  # U30.4 -> R307.1 (R7)
        ('GNSS_SAFEBOOT_N', 'F', W, [(6.01, 10.20), (2.60, 10.20), (2.00, 9.60)]),  # U30.18 -> TP30
        # 3V3_GNSS: U30.7 / U30.8 joined at y 20.75, up to C301.1, on to C300.1 and FB30.2 (R7 geometry)
        ('3V3_GNSS', 'F', W_RAIL, [(12.61, 19.70), (12.61, 20.75)]),
        ('3V3_GNSS', 'F', W_RAIL, [(13.71, 19.70), (13.71, 20.75), (12.61, 20.75)]),
        ('3V3_GNSS', 'F', W_RAIL, [(12.61, 20.75), (12.61, 21.75), (12.74, 21.88), (12.08, 22.54), (11.58, 22.54),
                                   (11.58, 23.85)]),
        ('3V3', 'F', W_RAIL, [(11.58, 25.15), (12.33, 24.40)]),                     # FB30.1 -> In2 3V3 via
        # 3V3_RADIO: FB31.2 -> C310.1 -> C312.1 -> C311.1 -> U31.1
        ('3V3_RADIO', 'F', W_RAIL_R, [(35.10, 20.85), (36.35, 19.60), (36.78, 19.60), (36.78, 17.50), (36.78, 16.54),
                                      (34.81, 16.54)]),
        ('3V3', 'F', W_RAIL_R, [(35.10, 22.15), (35.10, 24.40)]),                   # FB31.1 -> In2 3V3 via
        ('3V3', 'F', W, [(24.10, 29.07), (24.10, 28.45)]),                          # R310.1 -> In2 3V3 via
        # TXEN: R7's B.Cu loop round U31's west side (pins 9 and 19), unchanged
        ('RADIO_TXEN', 'F', W_STRIP, [(28.59, 9.05), (28.59, 7.80)]),
        ('RADIO_TXEN', 'B', W_STRIP, [(28.59, 7.80), (24.80, 7.80), (24.50, 8.10), (24.50, 19.85), (24.80, 20.15),
                                      (31.13, 20.15)]),
        ('RADIO_TXEN', 'F', W_STRIP, [(31.13, 20.15), (31.13, 18.95)]),
    ]


STRIP_VIAS = [('RADIO_TXEN', 28.59, 7.80, VIA_SIG), ('RADIO_TXEN', 31.13, 20.15, VIA_SIG),
              ('3V3', 12.33, 24.40, VIA_PWR), ('3V3', 35.10, 24.40, VIA_PWR), ('3V3', 24.10, 28.45, VIA_SIG)]


# ---------------------------------------------------------------------------------------------------------------------
# The antenna-bias limiter's DC copper (D11 regenerates it; D51). U30's aft-row pads 13 (LNA_EN) and 14 (VCC_RF) are
# F.Cu only, and U30_KEEPOUT (F.Cu / In1, y 11.25-18.65) bars non-GND vias under the module, so each drops through a
# via beyond its pad's end, then runs on B.Cu under U30. Fix pass 1 (R8P1-DFM-01, D87): the vias sit at R7's y 8.3,
# their rings 0.15 mm clear of the u-blox T-shaped paste extensions (paste-only pads, y 8.70-10.10) that reach 0.6 mm
# past the pads (y 8.9 printed paste over the tented holes: R7 pass 2 DFM-07's defect, now gated by check_r8
# via_paste). ANT_DC / ANT_SRC keep R7's lengths on Q30's drain and source (its thermal note: M3_R7 "Antenna bias
# limiter").
V_LNA_EN, V_VCC_RF = (11.51, 8.3), (10.41, 8.3)
LIMITER = [
    ('GNSS_LNA_EN', 'F', W, [(11.51, 10.20), V_LNA_EN]),
    ('GNSS_LNA_EN', 'B', W, [V_LNA_EN, (11.51, 11.66), (12.03, 12.18), (12.25, 12.18)]),   # R303.1 from the west
    ('GNSS_LNA_EN', 'B', W, [(12.25, 12.18), (12.25, 12.55), (13.00, 13.30)]),              # Q31.1 (gate)
    ('GNSS_VCC_RF', 'F', 0.25, [(10.41, 10.20), V_VCC_RF]),
    ('GNSS_VCC_RF', 'B', 0.25, [V_VCC_RF, (9.575, 9.135), (9.575, 10.75), (9.575, 12.25)]),  # R300.1, Q32.2 (sense)
    ('GNSS_ANT_DC', 'B', W, [(11.45, 5.15), (5.85, 10.75), (4.75, 10.75)]),                  # rigid via -> Q30.3
    ('GNSS_ANT_SRC', 'B', W, [(7.925, 10.75), (7.925, 12.25)]),                              # R300.2 -> Q32.1
    ('GNSS_ANT_SRC', 'B', W, [(7.925, 10.75), (6.425, 10.75), (4.425, 12.75), (3.80, 12.75)]),   # -> Q30.2
    ('GNSS_ANT_SRC', 'B', W, [(3.80, 12.75), (5.30, 14.25)]),                                # -> R301.1
    ('GNSS_ANT_GATE', 'B', W, [(5.70, 12.75), (6.18, 13.23), (6.18, 14.25), (7.32, 14.25), (8.75, 14.25)]),
    ('GNSS_ANT_GATE', 'B', W, [(7.32, 14.25), (7.32, 15.75), (7.32, 16.90)]),                # R302.1, C304.1 (DNP)
    ('GNSS_ANT_PD', 'B', W, [(8.18, 15.75), (9.50, 15.75), (11.00, 14.25)]),                 # R302.2 -> Q31.3
]
LIMITER_VIAS = [('GNSS_LNA_EN', *V_LNA_EN, VIA_SIG), ('GNSS_VCC_RF', *V_VCC_RF, VIA_SIG)]

PADS = [('R306', '1', 'GNSS_RXD_MCU', (18.8, 30.03)), ('R306', '2', 'GNSS_RXD', (18.8, 29.17)),
        ('R305', '2', 'GNSS_TXD_MCU', (7.11, 22.75)), ('R307', '2', 'GNSS_TP_MCU', (9.0, 22.88)),
        ('U30', '3', 'GNSS_RXD', (8.21, 19.7)), ('U30', '9', 'GNSS_RESET_N', (14.81, 19.7)),
        ('R315', '1', 'RADIO_MOSI_MCU', (22.6, 29.93)), ('R315', '2', 'RADIO_MOSI', (22.6, 29.07)),
        ('R310', '2', 'RADIO_NSS', (24.1, 29.93)), ('R310', '1', '3V3', (24.1, 29.07)),
        ('R313', '1', 'RADIO_SCK_MCU', (25.1, 29.93)), ('R313', '2', 'RADIO_SCK', (25.1, 29.07)),
        ('R312', '1', 'RADIO_RXEN', (25.8, 7.58)), ('U31', '10', 'RADIO_RXEN', (27.32, 9.05)),
        ('U31', '11', 'RADIO_BUSY', (24.91, 11.46)), ('R314', '2', 'RADIO_MISO_MCU', (22.57, 12.73)),
        ('U31', '13', 'RADIO_MOSI', (24.91, 14.0)), ('U31', '14', 'RADIO_NSS', (24.91, 15.27)),
        ('U31', '15', 'RADIO_SCK', (24.91, 16.54)), ('U31', '20', 'RADIO_DIO1', (32.4, 18.95)),
        ('R311', '1', 'RADIO_NRST', (37.0, 14.0)), ('U31', '3', 'RADIO_NRST', (34.81, 14.0)),
        ('FB30', '1', '3V3', (11.58, 25.15)), ('FB31', '1', '3V3', (35.1, 22.15)),
        ('U30', '13', 'GNSS_LNA_EN', (11.51, 10.2)), ('R303', '1', 'GNSS_LNA_EN', (12.25, 12.18)),
        ('Q31', '1', 'GNSS_LNA_EN', (13.0, 13.3)), ('U30', '14', 'GNSS_VCC_RF', (10.41, 10.2)),
        ('R300', '1', 'GNSS_VCC_RF', (9.575, 10.75)), ('Q32', '2', 'GNSS_VCC_RF', (9.7, 12.25)),
        ('Q30', '3', 'GNSS_ANT_DC', (4.75, 10.75)), ('Q30', '2', 'GNSS_ANT_SRC', (3.8, 12.75)),
        ('R300', '2', 'GNSS_ANT_SRC', (7.925, 10.75)), ('Q32', '1', 'GNSS_ANT_SRC', (7.8, 12.25)),
        ('R301', '1', 'GNSS_ANT_SRC', (5.32, 14.25)), ('Q30', '1', 'GNSS_ANT_GATE', (5.7, 12.75)),
        ('R301', '2', 'GNSS_ANT_GATE', (6.18, 14.25)), ('Q32', '3', 'GNSS_ANT_GATE', (8.75, 14.25)),
        ('R302', '1', 'GNSS_ANT_GATE', (7.32, 15.75)), ('C304', '1', 'GNSS_ANT_GATE', (7.32, 16.9)),
        ('R302', '2', 'GNSS_ANT_PD', (8.18, 15.75)), ('Q31', '3', 'GNSS_ANT_PD', (11.0, 14.25))]


def draw(d):
    for ref, num, net, at in PADS:
        d.pad(ref, num, net, at)
    for net, layer, w, pts in gnss_lanes() + radio_lanes() + strip_lanes() + LIMITER:
        d.track(net, layer, w, [(r(x), r(y)) for x, y in pts])
    for net, x, y, size in STRIP_VIAS + LIMITER_VIAS:
        d.via(net, x, y, size)
