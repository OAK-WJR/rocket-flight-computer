"""R9 step 7 family rf_if: the GNSS and radio interface buses from U1 into the RF strip, and the strip's 3V3 feeds
(r9_route.py; R9_DECISIONS D-S7-02 .. D-S7-04).

Every lane is 0.2 mm on F.Cu over In1 GND (no layer change), pad centre to pad centre; the strip-internal copper is
step 4's (r9_rf.py), the lanes cross the fence on y_f through the openings this family moves its vias to make (R-7:
each opening <= 2.7 mm and crossed by a lane), and inside the strip they keep R-11's 5.0 / 6.0 mm from U30's body and 6.0 mm
from GNSS RF copper.

GNSS (pins 64-61 on U1's aft face, west to east TXD_MCU, RXD_MCU, TP_MCU, RESET_N, 0.5 mm pitch): four parallel lanes
straight down from the pins, peeling off west as nested 45-degree L's in pin order, outermost first:
  TXD_MCU   one 45-degree run from x 17.5 to x 6.99, straight down into R305.2 (fence opening 5.85 / 7.8);
  RXD_MCU   down to R306 (220R, at the MCU end) and into its east pad; GNSS_RXD leaves its west pad, one 45-degree run
            parallel to TXD's to x 8.47, down between R305.1 and R307.2, one 0.48 mm 45-degree step onto U30.3's axis
            below the row (fence opening 7.8 / 9.75);
  TP_MCU    down under R306, west on y 28.1, one 45-degree run parallel inside RXD's to x 9.09, down into R307.2;
  RESET_N   down x 19.0, one 45-degree run to x 17.85, through the fence (opening 17.25 / 19.4), east of FB30, west
            under FB30 on y 20.25 and into U30.9 from the north (D-S4-04's corridor).
Radio (aft-face pins 56-53 RXEN, BUSY, MISO_MCU, MOSI_MCU; east-face pins 47 / 46 / 45 / 39 NSS, SCK_MCU, DIO1, NRST):
  the series and pull resistors R315 (MOSI), R310 (NSS pull-up) and R313 (SCK) sit in one row at the MCU end inside the
  window F10 (5.94 mm from U1's courtyard, R-10) and SERIES / PULL_END (nearer U1 than U31) leave (D-S7-02); the aft
  four lanes leave the pins as a parallel bus, step 1.1 mm west together (mitred 45-degree runs, 0.5 mm apart) to pass
  west of the row (MOSI through R315), and step back east together to their strip positions RXEN 21.5, BUSY 22.0,
  MISO 22.5 (fence opening 20.95 / 23.05), MOSI 23.6; NSS (tapped by R310) and SCK (through R313) come from the east
  face as two parallel 45-degree runs and step east to 24.05 / 24.65 (fence opening 23.05 / 25.2). In the strip each
  lane runs straight down and turns into its U31 pin in pin order (the deepest pin westmost: BUSY 11, MISO via R314,
  MOSI 13, NSS 14, SCK 15); RXEN continues to y 9.6 and one 45-degree run east (R-11: 6.0 mm from C305) into R312.1
  and U31.10. DIO1 runs east, down x 27.75, one 45-degree run to x 33.15 and straight down into U31.20 (fence opening
  32.5 / 33.8); NRST runs east on y 44.0, down x 33.65, one 45-degree run to x 40.6 (east of C310), down through the
  fence (opening 38.8 / 41.3) and west on y 14.0 through R311.1 into U31.3.
3V3 feeds: FB30.1 and FB31.1 from In2 3V3 by one via each north of the fence (0.3 mm), R310.1 by one via.
The fence: step 4 closes it (every opening <= 2.0 mm); this family opens its lanes' gaps by moving six of step 4's fence
vias and adding one (FENCE_MOVES / FENCE_ADD; R-7: an opening <= 2.7 mm crossed by a lane), and stitches the GND strip
between the MISO and MOSI lanes with one grid via (R-7 reach <= 4.0 mm; D-S7-03).
"""
from r9_route import W, VIA_SIG, VIA_PWR, u1_pin
from r9_rf import FENCE_Y

NETS = ('GNSS_TXD_MCU', 'GNSS_RXD_MCU', 'GNSS_RXD', 'GNSS_TP_MCU', 'GNSS_RESET_N', 'RADIO_RXEN', 'RADIO_BUSY',
        'RADIO_MISO_MCU', 'RADIO_MOSI_MCU', 'RADIO_MOSI', 'RADIO_NSS', 'RADIO_SCK_MCU', 'RADIO_SCK', 'RADIO_DIO1',
        'RADIO_NRST')
RAILS = ('3V3',)
BUDGET = dict(length_mm=420.0, vias=0, critical_layer_changes=0, ratio=1.45)
W_FEED = 0.3                          # the module supply feeds (R8 W_RAIL)

V_FB30, V_FB31, V_R310 = (16.2, 24.2), (34.5, 24.3), (22.88, 27.55)

TRACKS = [   # net, polyline (F.Cu, 0.2 mm)
    # GNSS
    ('GNSS_TXD_MCU', [u1_pin(64), (17.5, 33.31), (6.99, 22.8), (6.99, 20.93)]),                     # R305.2
    ('GNSS_RXD_MCU', [u1_pin(63), (18.0, 29.67), (17.53, 29.2), (16.93, 29.2)]),                    # R306.1
    ('GNSS_RXD', [(16.07, 29.2), (15.0, 29.2), (8.47, 22.67), (8.47, 20.53), (8.95, 20.05), (8.95, 18.8)]),
    ('GNSS_TP_MCU', [u1_pin(62), (18.5, 28.6), (18.0, 28.1), (14.54, 28.1), (9.09, 22.65), (9.09, 20.93)]),
    ('GNSS_RESET_N', [u1_pin(61), (19.0, 24.0), (17.85, 22.85), (17.85, 20.7), (17.4, 20.25), (16.0, 20.25),
                      (15.55, 19.8), (15.55, 18.8)]),
    # radio, aft face: the bus steps west past the resistor row and back east (mitred, 0.5 mm apart)
    ('RADIO_RXEN', [u1_pin(56), (21.5, 35.6), (20.4, 34.5), (20.4, 25.6), (21.5, 24.5), (21.5, 9.6), (23.52, 7.58),
                    (26.55, 7.58)]),                                                                   # R312.1
    ('RADIO_RXEN', [(26.55, 7.58), (27.65, 7.58), (28.07, 8.0), (28.07, 9.05)]),                       # U31.10
    ('RADIO_BUSY', [u1_pin(55), (22.0, 35.4), (20.9, 34.3), (20.9, 25.8), (22.0, 24.7), (22.0, 11.46), (25.66, 11.46)]),
    ('RADIO_MISO_MCU', [u1_pin(54), (22.5, 35.2), (21.4, 34.1), (21.4, 26.0), (22.5, 24.9), (22.5, 12.73),
                        (23.32, 12.73)]),                                                              # R314.2
    ('RADIO_MOSI_MCU', [u1_pin(53), (23.0, 35.0), (22.0, 34.0), (22.0, 29.23)]),                       # R315.1
    ('RADIO_MOSI', [(22.0, 28.37), (22.0, 26.1), (23.6, 24.5), (23.6, 14.0), (25.66, 14.0)]),         # U31.13
    # radio, east face
    ('RADIO_NSS', [u1_pin(47), (26.75, 40.0), (26.75, 33.5), (23.45, 30.2), (23.45, 25.35), (24.05, 24.75),
                   (24.05, 15.27), (25.66, 15.27)]),                                                   # U31.14
    ('RADIO_NSS', [(22.88, 29.23), (23.45, 29.23)]),                                                   # R310.2 tap
    ('RADIO_SCK_MCU', [u1_pin(46), (27.25, 40.5), (27.25, 33.3), (24.895, 30.945), (24.895, 29.45)]),  # R313.1
    ('RADIO_SCK', [(24.035, 29.45), (24.035, 25.465), (24.65, 24.85), (24.65, 16.54), (25.66, 16.54)]),  # U31.15
    ('RADIO_DIO1', [u1_pin(45), (27.75, 41.0), (27.75, 33.0), (33.15, 27.6), (33.15, 18.95)]),         # U31.20
    ('RADIO_NRST', [u1_pin(39), (33.65, 44.0), (33.65, 31.0), (40.6, 24.05), (40.6, 14.45), (40.15, 14.0),
                    (37.75, 14.0)]),                                                                   # R311.1
    ('RADIO_NRST', [(37.75, 14.0), (35.56, 14.0)]),                                                    # U31.3
]
FEEDS = [   # 3V3: In2 via -> pad
    ('3V3', W_FEED, [V_FB30, (16.2, 21.52), (16.66, 21.06)]),                                          # FB30.1
    ('3V3', W_FEED, [V_FB31, (34.5, 20.95)]),                                                          # FB31.1
    ('3V3', W, [(22.88, 28.37), V_R310]),                                                              # R310.1
]
VIAS = [('3V3', V_FB30, VIA_PWR), ('3V3', V_FB31, VIA_PWR), ('3V3', V_R310, VIA_SIG)]
# fence vias (x on y_f) moved off the lanes: GNSS_RESET_N (opening 17.25 / 19.4), the radio aft bus RXEN / BUSY / MISO
# (20.95 / 23.05), MOSI / NSS / SCK (23.05 / 25.2), DIO1 (32.5 / 33.8) and FB31's 3V3 feed (33.8 / 35.2), NRST (38.8 / 41.3)
FENCE_MOVES = [(17.45, 17.25), (21.3, 20.95), (23.25, 23.05), (32.95, 32.5), (34.9, 35.2), (40.75, 41.3)]
FENCE_ADD = [33.8]
GRID_ADD = [(23.05, 17.4)]          # the GND strip between the MISO (x 22.5) and MOSI (x 23.6) lanes

PADS = [
    ('R305', '2', 'GNSS_TXD_MCU', (6.99, 20.93)), ('R306', '1', 'GNSS_RXD_MCU', (16.93, 29.2)),
    ('R306', '2', 'GNSS_RXD', (16.07, 29.2)), ('U30', '3', 'GNSS_RXD', (8.95, 18.8)),
    ('R307', '2', 'GNSS_TP_MCU', (9.09, 20.93)), ('U30', '9', 'GNSS_RESET_N', (15.55, 18.8)),
    ('R312', '1', 'RADIO_RXEN', (26.55, 7.58)), ('U31', '10', 'RADIO_RXEN', (28.07, 9.05)),
    ('U31', '11', 'RADIO_BUSY', (25.66, 11.46)), ('R314', '2', 'RADIO_MISO_MCU', (23.32, 12.73)),
    ('R315', '1', 'RADIO_MOSI_MCU', (22.0, 29.23)), ('R315', '2', 'RADIO_MOSI', (22.0, 28.37)),
    ('U31', '13', 'RADIO_MOSI', (25.66, 14.0)), ('R310', '2', 'RADIO_NSS', (22.88, 29.23)),
    ('R310', '1', '3V3', (22.88, 28.37)), ('U31', '14', 'RADIO_NSS', (25.66, 15.27)),
    ('R313', '1', 'RADIO_SCK_MCU', (24.895, 29.45)), ('R313', '2', 'RADIO_SCK', (24.035, 29.45)),
    ('U31', '15', 'RADIO_SCK', (25.66, 16.54)), ('U31', '20', 'RADIO_DIO1', (33.15, 18.95)),
    ('R311', '1', 'RADIO_NRST', (37.75, 14.0)), ('U31', '3', 'RADIO_NRST', (35.56, 14.0)),
    ('FB30', '1', '3V3', (16.66, 21.06)), ('FB31', '1', '3V3', (34.5, 20.95)),
]


def draw(d):
    for net, pts in TRACKS:
        d.track(net, 'F', W, pts)
    for net, w, pts in FEEDS:
        d.track(net, 'F', w, pts)
    for net, at, size in VIAS:
        d.via(net, at, size)
    for x0, x1 in FENCE_MOVES:
        d.move_via('GND', (x0, FENCE_Y), (x1, FENCE_Y), VIA_SIG)
    for x in FENCE_ADD:
        d.via('GND', (x, FENCE_Y), VIA_SIG)
    for at in GRID_ADD:
        d.via('GND', at, VIA_SIG)
