"""R9 step 7 family status: the two status LEDs, the buzzer and its driver, the pull-pin input and the two supply sense
dividers (VLOGIC_SENSE, V3V3_SENSE) (r9_route.py; R9_DECISIONS D-S7-14).

Parts re-placed (r9_place.tsv, D-S7-14): the LEDs west of U1 clear of the SWD lanes, the buzzer LS120 to the
south-centre with its driver Q123 / R162 / R163 / D123 on B.Cu under it (the west spot is crossed by imu_baro's I2C),
the pull-pin parts on a B.Cu column x 27.0, the VLOGIC divider beside its interior exit, the V3V3 divider into the
VLOGIC divider's old spots (R62 turned).
  LEDs         U1.86 / 88 west on F.Cu into R32.1 / R33.1 (LED_RED round R33's east end), the anode lanes north
               between the resistors' and LED1's pads into LED1.2 / LED2.1; cathodes to GND (LED1 by a via, LED2 to
               imu_baro's GND via (8.35, 45.5))
  BUZZ_DRV     U1.7 inward on F.Cu to a via (17.3, 43.0) under U3's north-east half, B.Cu east by the interior exit
               E41.44 and south on x 25.1 into R162.1; BUZZ_G R162.2 / R163.1 into Q123.1; BUZZ_OUT Q123.3 by one via
               (31.42, 25.82) to LS120.2 (F.Cu) and D123.2 (B.Cu); 3V3 to LS120.1 and D123.1 by one In2 via (D123
               and the two vias moved for footprint silk, D-S9-01: each lead one straight run)
  PULLPIN      U1.8 inward on F.Cu to a via (16.85, 44.6), B.Cu east by E43.97 (y 43.97, north of camera RX's y 44.5)
               to D122.3 and south on x 27.0 through C160.1, R161.2, R160.2; PULLPIN_EXT R160.1 to J123.1 (y 29.1 /
               27.0, 1.05 mm from TP70)
  VLOGIC_SENSE U1.17 inward on F.Cu to the via (21.0, 45.6), B.Cu by the interior exit E46.4 (y 46.375), under R172
               (y 45.55) into the divider's sense pads R61.1, C60.1, R60.2 (C60 at the ADC end); VLOGIC (step 6's
               PARTIAL rail) from the hold-up via (38.5, 69.6) on F.Cu (x 37.6, y 56.4, x 30.4) to a via into R60.1:
               2.1 mm from ARM1_SENSE_MCU (no HIGH net within 1.5 mm of an MCU-side sense lane, r9_pyro_check)
  V3V3_SENSE   U1.18 north to a via (20.5, 53.3) (the servo family's band), B.Cu y 52.75 west under the servo
               pull-downs, x 14.6 north round C14's 3V3 via into the pocket's divider R62.2 / R63.1 (R62 / R63 in R60 /
               R61's old spots); R62.1 straight onto C14.1 (3V3), R63.2 onto C14.2's GND via (16.82, 55.3); ratio 1.49:
               the pocket's only way in is round the servo pull-downs
The driver's GND strap runs on y 23.9 through R163.2 and Q123.2, so B.Cu below y ~23.5 stays free between the RF
strip's fence and the driver (a USB_LIMITED corridor for power_ctl). None of these nets is a critical class. The GND
vias of LED1, the buzzer driver and the VLOGIC divider wait for step 8 (PENDING); the small parts' other GND pads
(C160.2, D122.1) are step 8's.
"""
from r9_route import W, VIA_SIG, VIA_PWR, u1_pin

NETS = ('LED_RED', 'LED_RED_A', 'LED_YEL', 'LED_YEL_A', 'BUZZ_DRV', 'BUZZ_G', 'BUZZ_OUT', 'PULLPIN', 'PULLPIN_EXT',
        'VLOGIC_SENSE', 'V3V3_SENSE')
CONTINUES = ('VLOGIC',)            # step 6's PARTIAL rail, open at R60.1 (r9_power.PARTIAL)
RAILS = ('GND', '3V3')
BUDGET = dict(length_mm=140.0, vias=5, critical_layer_changes=0, ratio=1.50)
W_VL = 0.25                        # VLOGIC to the divider top (a 100 k tap)

V_BUZ, V_PP, V_VS, V_V3 = (17.3, 43.0), (16.85, 44.6), (21.0, 45.6), (20.5, 53.3)
V_BO = (31.42, 25.82)              # BUZZ_OUT: on Q123.3's 45-degree line and D123.2's axis (D-S9-01)
V_VL = (30.4, 47.3)                # VLOGIC into R60.1
V_HOLDUP = (38.5, 69.6)            # step 6's VLOGIC via to the hold-up C84 (r9_power.V_HOLDUP; x 38.5: D-S8-10)
V3 = dict(BUZ=(29.08, 28.4), PP=(28.6, 33.5), D122=(30.0, 42.45))
G = dict(LED1=(4.4, 45.9), BUZ=(29.6, 23.9), VS=(29.2, 47.75))
G_IMU = (8.35, 45.5)               # imu_baro's GND via (G_CS)
G_C14 = (16.82, 55.3)              # C14.2's GND via (step 6)

TRACKS = [   # net, layer, width, polyline
    # LEDs
    ('LED_RED', 'F', W, [u1_pin(86), (9.3, 43.5), (9.0, 43.2), (9.0, 41.45), (8.7, 41.15), (7.9, 41.15)]),  # R32.1
    ('LED_YEL', 'F', W, [u1_pin(88), (8.9, 44.5), (8.1, 43.7)]),                                        # R33.1
    ('LED_RED_A', 'F', W, [(5.9, 41.15), (6.9, 42.15), (6.9, 45.1)]),                                   # R32.2 -> LED1.2
    ('LED_YEL_A', 'F', W, [(5.9, 43.1), (5.9, 47.0)]),                                                  # R33.2 -> LED2.1
    ('GND', 'F', W, [(5.2, 45.1), G['LED1']]),                                                          # LED1.1
    ('GND', 'F', W, [(7.8, 47.0), (7.8, 46.05), G_IMU]),                                                # LED2.2
    # buzzer
    ('BUZZ_DRV', 'F', W, [u1_pin(7), (15.0, 50.14), (16.3, 48.84), (16.3, 44.0), V_BUZ]),
    ('BUZZ_DRV', 'B', W, [V_BUZ, (18.86, 41.44), (24.75, 41.44), (25.1, 41.09), (25.1, 26.15)]),        # R162.1
    ('BUZZ_G', 'B', W, [(27.1, 25.95), (28.6, 25.95)]),                                                 # R162.2 -> Q123.1
    ('BUZZ_G', 'B', W, [(26.6, 24.73), (26.6, 25.6)]),                                                  # R163.1
    ('BUZZ_OUT', 'B', W, [(30.6, 25.0), V_BO]),                                                         # Q123.3
    ('BUZZ_OUT', 'F', W, [V_BO, (31.42, 26.7)]),                                                        # LS120.2
    ('BUZZ_OUT', 'B', W, [V_BO, (31.42, 27.6)]),                                                        # D123.2
    ('3V3', 'F', W, [V3['BUZ'], (28.08, 27.4)]),                                                        # LS120.1
    ('3V3', 'B', W, [V3['BUZ'], (29.08, 27.6)]),                                                        # D123.1
    ('GND', 'B', W, [(26.6, 23.9), G['BUZ']]),                                                          # R163.2, Q123.2
    # pull-pin
    ('PULLPIN', 'F', W, [u1_pin(8), (15.5, 50.35), (16.85, 49.0), V_PP]),
    ('PULLPIN', 'B', W, [V_PP, (17.48, 43.97), (26.5, 43.97), (27.0, 43.47), (27.0, 42.5)]),            # D122.3
    ('PULLPIN', 'B', W, [(27.0, 42.5), (27.0, 35.6), (27.0, 33.5), (27.0, 30.93)]),                     # C160, R161, R160
    ('PULLPIN_EXT', 'B', W, [(27.0, 30.07), (27.0, 29.1), (32.5, 29.1), (34.6, 27.0), (37.6, 27.0), (39.0, 28.4),
                             (39.0, 29.6)]),                                                            # J123.1
    ('3V3', 'B', W, [(27.86, 33.5), V3['PP']]),                                                         # R161.1
    ('3V3', 'B', W, [(29.0, 43.45), V3['D122']]),                                                       # D122.2
    # VLOGIC_SENSE and its divider
    ('VLOGIC_SENSE', 'F', W, [u1_pin(17), (20.0, 50.85), (21.0, 49.85), V_VS]),
    ('VLOGIC_SENSE', 'B', W, [V_VS, (21.775, 46.375), (24.8, 46.375), (24.8, 45.55), (28.0, 45.55), (29.2, 45.55),
                              (30.4, 45.55)]),                                                          # R61.1, C60.1, R60.2
    ('VLOGIC', 'F', W_VL, [V_HOLDUP, (37.6, 68.7), (37.6, 59.0), (35.0, 56.4), (30.8, 56.4), (30.4, 56.0), V_VL]),
    ('VLOGIC', 'B', W_VL, [V_VL, (30.4, 46.43)]),                                                       # R60.1
    ('GND', 'B', W, [(29.2, 46.95), G['VS']]),                                                          # C60.2
    ('GND', 'B', W, [(28.0, 46.41), (28.54, 46.95), (29.2, 46.95)]),                                    # R61.2
    # V3V3_SENSE in the pocket
    ('V3V3_SENSE', 'F', W, [u1_pin(18), V_V3]),
    ('V3V3_SENSE', 'B', W, [V_V3, (19.95, 52.75), (15.3, 52.75), (14.6, 53.45), (14.6, 54.5), (15.42, 54.5)]),
    ('V3V3_SENSE', 'B', W, [(15.42, 54.5), (15.42, 55.38)]),                                            # R62.2 -> R63.1
    ('3V3', 'B', W, [(16.1, 54.5), (16.1, 53.6)]),                                                      # R62.1 -> C14.1
    ('GND', 'B', W, [(16.28, 55.3), G_C14]),                                                            # R63.2
]
SIGNAL_VIAS = [('BUZZ_DRV', V_BUZ), ('PULLPIN', V_PP), ('VLOGIC_SENSE', V_VS), ('V3V3_SENSE', V_V3),
               ('BUZZ_OUT', V_BO)]
PENDING = list(G.values())
PADS = [
    ('C60', '1', 'VLOGIC_SENSE', (29.2, 45.55)), ('C60', '2', 'GND', (29.2, 46.95)),
    ('C160', '1', 'PULLPIN', (27.0, 35.6)), ('D122', '2', '3V3', (29.0, 43.45)),
    ('D122', '3', 'PULLPIN', (27.0, 42.5)), ('D123', '1', '3V3', (29.08, 27.6)),
    ('D123', '2', 'BUZZ_OUT', (31.42, 27.6)), ('J123', '1', 'PULLPIN_EXT', (39.0, 29.6)),
    ('LED1', '1', 'GND', (5.2, 45.1)), ('LED1', '2', 'LED_RED_A', (6.9, 45.1)),
    ('LED2', '1', 'LED_YEL_A', (5.9, 47.0)), ('LED2', '2', 'GND', (7.8, 47.0)),
    ('LS120', '1', '3V3', (27.15, 27.25)), ('LS120', '2', 'BUZZ_OUT', (30.85, 27.25)),
    ('Q123', '1', 'BUZZ_G', (28.6, 25.95)), ('Q123', '2', 'GND', (28.6, 24.05)), ('Q123', '3', 'BUZZ_OUT', (30.6, 25.0)),
    ('R32', '1', 'LED_RED', (7.9, 41.15)), ('R32', '2', 'LED_RED_A', (5.9, 41.15)),
    ('R33', '1', 'LED_YEL', (7.9, 43.1)), ('R33', '2', 'LED_YEL_A', (5.9, 43.1)),
    ('R60', '1', 'VLOGIC', (30.4, 46.43)), ('R60', '2', 'VLOGIC_SENSE', (30.4, 45.57)),
    ('R61', '1', 'VLOGIC_SENSE', (28.0, 45.55)), ('R61', '2', 'GND', (28.0, 46.41)),
    ('R62', '1', '3V3', (16.28, 54.5)), ('R62', '2', 'V3V3_SENSE', (15.42, 54.5)),
    ('R63', '1', 'V3V3_SENSE', (15.42, 55.38)), ('R63', '2', 'GND', (16.28, 55.38)), ('C14', '1', '3V3', (15.98, 53.6)),
    ('R160', '1', 'PULLPIN_EXT', (27.0, 30.07)),
    ('R160', '2', 'PULLPIN', (27.0, 30.93)), ('R161', '1', '3V3', (27.86, 33.5)),
    ('R161', '2', 'PULLPIN', (27.0, 33.5)), ('R162', '1', 'BUZZ_DRV', (25.1, 26.15)),
    ('R162', '2', 'BUZZ_G', (27.1, 26.15)), ('R163', '1', 'BUZZ_G', (26.6, 24.73)),
    ('R163', '2', 'GND', (26.6, 23.87)), ('U1', '7', 'BUZZ_DRV', u1_pin(7)),
    ('U1', '8', 'PULLPIN', u1_pin(8)), ('U1', '17', 'VLOGIC_SENSE', u1_pin(17)),
    ('U1', '18', 'V3V3_SENSE', u1_pin(18)), ('U1', '86', 'LED_RED', u1_pin(86)),
    ('U1', '88', 'LED_YEL', u1_pin(88)),
]


def draw(d):
    for net, layer, w, pts in TRACKS:
        d.track(net, layer, w, pts)
    for net, at in SIGNAL_VIAS:
        d.via(net, at, VIA_SIG)
    d.via('VLOGIC', V_VL, VIA_PWR)
    for at in V3.values():
        d.via('3V3', at, VIA_SIG)
    for at in PENDING:
        d.via('GND', at, VIA_SIG)
