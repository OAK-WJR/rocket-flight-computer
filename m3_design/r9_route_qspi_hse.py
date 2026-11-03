"""R9 step 7 family qspi_hse: the QSPI flash U3 and the crystal Y1 under U1 (r9_route.py; R9_DECISIONS D-S7-05).

U1, U3, Y1, C25 and C26 keep R8's relative placement (r9_place.tsv: R8's spot (a) cluster moved by (-5, -0.5); R10, the
NCS pull-up, is re-placed with the NCS lane by imu_baro, D-S7-10), so the dives are R8's qspi_hse tables
(r8_route_qspi_hse.py, spike (a)) moved by the same (-5, -0.5), except where R9's own copper or rules differ (each noted
below). U3 sits under U1 (bottom, rotation 90): its west row is pins 1-4 forward to aft (NCS, IO1, IO2, GND), its east
row 5-8 aft to forward (IO0, CLK, IO3, VCC). Each QSPI signal is one inward dive: the U1 pad, F.Cu under U1's body, one
via, B.Cu into the flash pad, with a GND via within 1.5 mm of every via (AGENTS section 3).
Y1 (rotation 90) sits under pins 12 / 13: HSE_IN and HSE_OUT dive straight to it, and their load caps C25 / C26 sit on
the crystal pads' rows. In2 under Y1 is the Y1_In2_keepout (step 6).
R9 differences:
  QSPI_NCS / QSPI_IO2  leave U1's west face and north-west corner through the IMU's corner (U4 under the west pins), so
            they are routed with the IMU family, imu_baro (R9_DECISIONS D-S7-05); R8's BOOT0 member too (R5 sits in the
            IMU's west column)
  C25.2     R8's GND via spot (13.75, 49.2) moved lies on the IMU body's no-via area (M-7): the via sits north of the pad
            (14.53, 49.95)
Built elsewhere: U3.8 / U3.4 3V3 and GND (step 6, U1 decoupling); NRST (usb_swd); QSPI_NCS, QSPI_IO2, BOOT0 (imu_baro).
"""
from r9_route import W, VIA_SIG, u1_pin

NETS = ('QSPI_IO0', 'QSPI_IO1', 'QSPI_IO3', 'QSPI_CLK', 'HSE_IN', 'HSE_OUT')
RAILS = ('GND',)
# R8 spike (a): QSPI 49.5 mm with 6 vias (NCS and IO2 about 14 mm and 2 of them), HSE 14.0 mm with 2 vias
BUDGET = dict(length_mm=50.0, vias=6, critical_layer_changes=6, ratio=1.40)

# (net, [(layer, polyline)...], via): F.Cu from the U1 pad to the via, B.Cu to the flash / crystal pad
DIVES = [
    ('QSPI_IO1', [('F', [u1_pin(59), (20.0, 38.9)]),
                  ('B', [(20.0, 38.9), (15.57, 43.33), (14.07, 43.33)])], (20.0, 38.9)),     # under the flash body
    ('QSPI_IO0', [('F', [u1_pin(58), (20.5, 38.05), (21.13, 38.68), (21.13, 40.05)]),
                  ('B', [(21.13, 40.05), (21.13, 40.8)])], (21.13, 40.05)),
    ('QSPI_IO3', [('F', [u1_pin(60), (19.5, 37.95), (19.0, 38.45), (19.0, 39.58), (22.75, 43.33)]),
                  ('B', [(22.75, 43.33), (21.13, 43.33)])], (22.75, 43.33)),                 # over the flash diagonally
    ('QSPI_CLK', [('F', [u1_pin(36), (24.3, 45.5), (24.3, 42.07), (22.75, 42.07)]),
                  ('B', [(22.75, 42.07), (21.13, 42.07)])], (22.75, 42.07)),                 # x 24.3: 0.4 mm off the pads
    ('HSE_IN', [('F', [u1_pin(12), (17.5, 51.1), (17.0, 50.6)]),
                ('B', [(17.0, 50.6), (17.0, 49.2), (15.37, 49.2)])], (17.0, 50.6)),           # Y1.1, then C25.1
    ('HSE_OUT', [('F', [u1_pin(13), (18.0, 48.69), (19.69, 47.0)]),
                 ('B', [(18.7, 47.0), (19.69, 47.0), (20.33, 47.0)])], (19.69, 47.0)),        # Y1.3, C26.1
]
# pads the tables end on (ref, pad, net, centre): a placement change refuses to draw
PADS = [('U3', '2', 'QSPI_IO1', (14.07, 43.33)), ('U3', '5', 'QSPI_IO0', (21.13, 40.8)),
        ('U3', '6', 'QSPI_CLK', (21.13, 42.07)), ('U3', '7', 'QSPI_IO3', (21.13, 43.33)),
        ('Y1', '1', 'HSE_IN', (17.0, 49.2)), ('C25', '1', 'HSE_IN', (15.37, 49.2)),
        ('Y1', '3', 'HSE_OUT', (18.7, 47.0)), ('C26', '1', 'HSE_OUT', (20.33, 47.0)),
        ('C25', '2', 'GND', (14.53, 49.2)), ('C26', '2', 'GND', (21.17, 47.0))]
# GND vias: one within 1.5 mm of each critical dive, and the crystal load caps' GND pads (R8's, moved)
GND_VIAS = [(23.6, 42.7),     # IO3 / CLK vias
            (20.5, 39.5),     # IO0 / IO1 vias
            (16.0, 50.6),     # HSE_IN via
            (19.69, 45.75),   # HSE_OUT via (1.25 mm)
            (17.65, 45.85),   # crystal guard (Y1's B.Cu GND guard, R8 D86)
            (14.53, 49.95),   # C25.2 (R8's (13.75, 49.2) spot is under the IMU body)
            (21.95, 47.0)]    # C26.2
GND_TRACKS = [[(14.53, 49.2), (14.53, 49.95)], [(21.17, 47.0), (21.95, 47.0)]]
PENDING = GND_VIAS            # every GND via waits for step 8's In1 pour (dangling until then)


def draw(d):
    for net, runs, via in DIVES:
        for layer, pts in runs:
            d.track(net, layer, W, pts)
        d.via(net, via, VIA_SIG)
    for xy in GND_VIAS:
        d.via('GND', xy, VIA_SIG)
    for pts in GND_TRACKS:
        d.track('GND', 'B', W, pts)
