"""R8 step 6 family status: the LEDs, the buzzer and the pull-pin, the logic-supply status and sense lines, and the
battery switch's enable (r8_route.py). R8_DECISIONS D57 (placement), D58 (topology).

  - LEDs (spike (d), D3): pins 86 / 88 run west on F.Cu to R32 / R33 and on to LED1 / LED2 on the west edge, LED_RED
    aft of LED_YEL as the pins are.
  - Buzzer and pull-pin (pins 7 and 8 on U1's forward face): both lanes run forward on F.Cu beside each other, then
    west across the pyro corridor (B.Cu lanes x 18.18 - 19.25; the F.Cu lanes stay aft of the 3V3A F.Cu hop on y 62.2,
    D44) and drop to B.Cu. BUZZ_DRV (pin 7, the west lane) turns first, into R162 stood with its drive pad aft (D57);
    BUZZ_G runs from R162's far pad to Q123's gate, R163 (pull-down) under Q123's body between its pin columns.
    BUZZ_OUT leaves Q123's drain through a via to the buzzer LS120 and the clamp D123 on the top. PULLPIN (pin 8)
    continues west to x 14.23 and runs forward on B.Cu down the gap between the barometer's GND vias and Q123: R161
    (pull-up) on the lane, R160 (series to J123) tapped west of R161, C160 (turned, D57) and the clamp D122 at the end.
  - 3V3 for LS120, D123, R161 and D122: one via each into the In2 3V3 west tongue.
  - VLOGIC_SENSE (pin 17) straight forward to the divider R60 / R61 (on its line) and C60; V3V3_SENSE (pin 18)
    dives beside it (the step-4 escape, D33) to R63 / R62 on the bottom, passing between R63 and the 3V3A via.
  - BAT_FAULT_N (pin 28) and LOGIC_SOURCE_ST (pin 29), the reserved lanes of D50: east then forward on F.Cu, BAT_FAULT_N
    turning first (x 33.6, to a via beside the 3V3 F.Cu line on y 82.0, then B.Cu through TP85 and R89 to U9.4),
    LOGIC_SOURCE_ST west of R102 (D55) and diagonally clear of TP76 to a via, then B.Cu to U11.9, TP87 and R91.
  - BAT_ENABLE (D36, spike (c)'s lane): R165 through its via (D30), forward on F.Cu x 16.6 under Q122, east on the top
    strip between the CH1 block and RAW_PROTECTED to x 42.9, aft through TP84 and C87, a via, and the B.Cu spine
    x 40.42 between R82's pads to U9.1, with R81 (EN to GND) west of it on a stub (fix pass 2, D100: R81 used to
    straddle the BAT_IN feed x 41.25 with its pad 1 on the spine). The lane runs on y 98.45, not spike (c)'s 99.25 beside
    RAW_PROTECTED: with both lanes, Q122's GND pocket (Q122.2, R123.2; Q120's drain under it on B.Cu) had no way to
    GND. The 1.3 mm strip between the lanes now carries the pocket's pour east to a GND via (D58).
"""
from r8_route import W, VIA_PWR, u1_pin

NETS = ('LED_RED', 'LED_RED_A', 'LED_YEL', 'LED_YEL_A', 'BUZZ_DRV', 'BUZZ_G', 'BUZZ_OUT', 'PULLPIN', 'PULLPIN_EXT',
        'VLOGIC_SENSE', 'V3V3_SENSE', 'BAT_FAULT_N', 'LOGIC_SOURCE_ST', 'BAT_ENABLE')
RAILS = ('GND', '3V3')
BUDGET = dict(length_mm=215.0, vias=8, critical_layer_changes=0, ratio=1.3)

# BUZZ_DRV's lane runs 0.55 mm beside PULLPIN's (y 60.45 / 61.0): no GND pour finger between them, and BUZZ_DRV's via
# keeps 0.20 mm from PULLPIN's lane over it (fix pass 1, D91; at 0.5 mm it was the 0.15 mm DRC minimum)
V_BD, V_PP, V_BO = (16.4, 60.45), (14.23, 61.0), (15.0, 67.5)         # BUZZ_DRV, PULLPIN, BUZZ_OUT
V_V3 = (25.9, 54.0)                                                    # V3V3_SENSE
V_BF, V_LG = (33.6, 81.2), (38.6, 57.27)                               # BAT_FAULT_N, LOGIC_SOURCE_ST
V_BE1, V_BE2 = (16.6, 104.5), (40.42, 93.5)                            # BAT_ENABLE
Y_BE = 98.45                     # BAT_ENABLE's strip lane, 1.3 mm north of RAW_PROTECTED's (D58)
V_STRIP_GND = (30.6, 99.1)       # the GND strip between the two lanes, with Q122's pocket, to In1
V_3V3 = [(10.05, 71.25), (15.28, 72.65), (13.37, 73.1), (16.75, 80.95)]  # LS120.1, D123.1, R161.1, D122.2

TRACKS = [   # net, layer, width, polyline
    # LEDs (spike (d))
    ('LED_RED', 'F', W, [u1_pin(86), (14.3, 44.0), (12.1, 41.8)]),
    ('LED_RED_A', 'F', W, [(10.1, 41.8), (7.45, 41.8)]),
    ('LED_YEL', 'F', W, [u1_pin(88), (13.3, 45.0), (12.3, 44.0)]),
    ('LED_YEL_A', 'F', W, [(10.3, 44.0), (7.55, 44.0)]),
    # buzzer drive and pull-pin: forward on F.Cu, west across the pyro corridor, down to B.Cu
    ('BUZZ_DRV', 'F', W, [u1_pin(7), (20.0, 59.95), (19.5, 60.45), V_BD]),
    ('BUZZ_DRV', 'B', W, [V_BD, (16.4, 61.95)]),                                      # R162.1
    ('PULLPIN', 'F', W, [u1_pin(8), (20.5, 60.5), (20.0, 61.0), V_PP]),
    ('PULLPIN', 'B', W, [V_PP, (14.23, 71.4), (14.23, 72.2), (14.23, 78.4), (14.23, 80.0)]),  # R161.2, D122.3
    ('PULLPIN', 'B', W, [(14.23, 71.4), (11.03, 71.4), (11.03, 72.2)]),              # R160.2
    ('PULLPIN', 'B', W, [(14.23, 78.4), (11.02, 78.4)]),                              # C160.1
    ('PULLPIN_EXT', 'B', W, [(10.17, 72.2), (10.17, 74.37), (11.2, 75.4)]),           # R160.1 -> J123.1
    ('BUZZ_G', 'B', W, [(16.4, 63.95), (16.4, 64.85), (17.0, 65.45)]),               # R162.2 -> Q123.1
    ('BUZZ_G', 'B', W, [(16.4, 64.85), (16.0, 65.25), (16.0, 68.8)]),                # R163.1, under Q123
    ('BUZZ_OUT', 'B', W, [(15.0, 66.4), V_BO]),                                       # Q123.3
    ('BUZZ_OUT', 'F', W, [V_BO, (13.75, 68.75), (13.75, 69.75)]),                     # LS120.2
    ('BUZZ_OUT', 'F', W, [V_BO, (16.0, 67.5), (17.62, 69.12), (17.62, 71.7)]),        # D123.2
    ('3V3', 'F', W, [(10.05, 69.75), V_3V3[0]]),
    ('3V3', 'F', W, [(15.28, 71.7), V_3V3[1]]),
    ('3V3', 'B', W, [(13.37, 72.2), V_3V3[2]]),
    ('3V3', 'B', W, [(15.8, 80.95), V_3V3[3]]),
    # logic-supply sense dividers at U1's forward face
    ('VLOGIC_SENSE', 'F', W, [u1_pin(17), (25.0, 55.3)]),
    ('VLOGIC_SENSE', 'F', W, [(24.43, 55.3), (25.0, 55.3), (25.67, 55.3)]),          # R61.1, R60.2
    ('VLOGIC_SENSE', 'F', W, [(24.43, 55.3), (24.43, 56.75)]),                        # C60.1
    ('V3V3_SENSE', 'F', W, [u1_pin(18), (25.5, 53.6), V_V3]),
    ('V3V3_SENSE', 'B', W, [V_V3, (25.9, 55.88), (25.3, 55.88), (25.3, 56.87)]),     # R63.1, R62.2
    # status lanes (D50)
    ('BAT_FAULT_N', 'F', W, [u1_pin(28), (32.6, 50.0), (33.6, 51.0), V_BF]),
    ('BAT_FAULT_N', 'B', W, [V_BF, (36.0, 83.6), (37.675, 83.6), (37.675, 84.8), (40.6, 84.8)]),  # TP85, R89.2, U9.4
    ('LOGIC_SOURCE_ST', 'F', W, [u1_pin(29), (34.0, 49.5), (34.0, 51.5), (38.6, 56.1), V_LG]),
    ('LOGIC_SOURCE_ST', 'B', W, [(36.75, 57.85), (36.75, 57.27), V_LG, (42.0, 57.27), (43.595, 57.27),
                                 (44.3, 57.975)]),                                   # U11.9 -> R91.2
    ('LOGIC_SOURCE_ST', 'B', W, [(42.0, 57.27), (42.0, 58.5)]),                       # TP87
    # battery switch enable (D36)
    ('BAT_ENABLE', 'B', W, [(16.6, 105.275), V_BE1]),                                 # R165.2 (D30's via)
    # (the 45-degree step clears R175.2, ARM1_SENSE, at the lane's west end)
    ('BAT_ENABLE', 'F', W, [V_BE1, (16.6, 99.25), (17.4, Y_BE), (42.9, Y_BE), (42.9, 93.5), V_BE2]),  # TP84, C87.1
    # the spine x 40.42 to U9.1; R81 (EN to GND) stands west of it since fix pass 2 (R8P2-ROUTING-02, D100), its pad 1
    # on a stub: the 0.5 mm BAT_IN feed (x 41.25) no longer runs between R81's pads
    ('BAT_ENABLE', 'B', W, [V_BE2, (40.42, 92.1), (40.42, 86.2)]),                     # U9.1
    ('BAT_ENABLE', 'B', W, [(40.42, 92.1), (39.6, 92.1)]),                            # R81.1
]
SIGNAL_VIAS = [('BUZZ_DRV', V_BD), ('PULLPIN', V_PP), ('BUZZ_OUT', V_BO), ('V3V3_SENSE', V_V3),
               ('BAT_FAULT_N', V_BF), ('LOGIC_SOURCE_ST', V_LG)]
# BAT_ENABLE (U9's EN divider, uA) takes the board's 0.5 / 0.3 mm signal via at both ends. Fix pass 3 (R8P3-ROUTING-02,
# D108): V_BE1 was spike (c)'s 0.6 mm power via, 0.180 mm from Q120.9 (the bare BAT_IN drain pad); same drill and
# barrel, now 0.23 mm
SIGNAL_VIAS += [('BAT_ENABLE', V_BE2), ('BAT_ENABLE', V_BE1)]
POWER_VIAS = [('3V3', xy) for xy in V_3V3] + [('GND', V_STRIP_GND)]
PADS = [('R32', '1', 'LED_RED', (12.1, 41.8)), ('R32', '2', 'LED_RED_A', (10.1, 41.8)),
        ('LED1', '2', 'LED_RED_A', (7.45, 41.8)), ('R33', '1', 'LED_YEL', (12.3, 44.0)),
        ('R33', '2', 'LED_YEL_A', (10.3, 44.0)), ('LED2', '1', 'LED_YEL_A', (7.55, 44.0)),
        ('R162', '1', 'BUZZ_DRV', (16.4, 61.95)), ('R162', '2', 'BUZZ_G', (16.4, 63.95)),
        ('Q123', '1', 'BUZZ_G', (17.0, 65.45)), ('R163', '1', 'BUZZ_G', (15.97, 68.8)),
        ('Q123', '3', 'BUZZ_OUT', (15.0, 66.4)), ('LS120', '2', 'BUZZ_OUT', (13.75, 69.75)),
        ('D123', '2', 'BUZZ_OUT', (17.62, 71.7)), ('LS120', '1', '3V3', (10.05, 69.75)),
        ('D123', '1', '3V3', (15.28, 71.7)), ('R161', '1', '3V3', (13.37, 72.2)),
        ('R161', '2', 'PULLPIN', (14.23, 72.2)), ('R160', '2', 'PULLPIN', (11.03, 72.2)),
        ('R160', '1', 'PULLPIN_EXT', (10.17, 72.2)), ('J123', '1', 'PULLPIN_EXT', (11.2, 75.4)),
        ('C160', '1', 'PULLPIN', (11.02, 78.4)), ('D122', '3', 'PULLPIN', (13.8, 80.0)),
        ('D122', '2', '3V3', (15.8, 80.95)),
        ('R61', '1', 'VLOGIC_SENSE', (24.43, 55.3)), ('R60', '2', 'VLOGIC_SENSE', (25.67, 55.3)),
        ('C60', '1', 'VLOGIC_SENSE', (24.2, 56.75)), ('R63', '1', 'V3V3_SENSE', (25.3, 55.88)),
        ('R62', '2', 'V3V3_SENSE', (25.3, 56.87)),
        ('TP85', '1', 'BAT_FAULT_N', (35.4, 83.0)), ('R89', '2', 'BAT_FAULT_N', (37.675, 83.6)),
        ('U9', '4', 'BAT_FAULT_N', (40.6, 84.8)), ('U11', '9', 'LOGIC_SOURCE_ST', (36.75, 57.85)),
        ('TP87', '1', 'LOGIC_SOURCE_ST', (42.0, 58.5)), ('R91', '2', 'LOGIC_SOURCE_ST', (44.3, 57.975)),
        ('R165', '2', 'BAT_ENABLE', (16.6, 105.275)), ('TP84', '1', 'BAT_ENABLE', (42.9, 96.5)),
        ('C87', '1', 'BAT_ENABLE', (42.95, 94.1)), ('R81', '1', 'BAT_ENABLE', (39.6, 92.1)),
        ('U9', '1', 'BAT_ENABLE', (40.6, 86.2))]


def draw(d):
    for ref, num, net, at in PADS:
        d.pad(ref, num, net, at)
    for net, layer, w, pts in TRACKS:
        d.track(net, layer, w, pts)
    for net, xy in SIGNAL_VIAS:
        d.via(net, *xy)
    for net, xy in POWER_VIAS:
        d.via(net, *xy, VIA_PWR)
