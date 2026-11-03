"""R9 step 7 family imu_baro: the IMU U4 (SPI1, CS, INT1), the barometer U5 (I2C1, SDO), their pull-ups and
decoupling, the QSPI flash's NCS and IO2 lanes, BOOT0, and the analog rail 3V3A (r9_route.py; R9_DECISIONS D-S7-05,
D-S7-06, D-S7-10).

U4 sits on the bottom under U1's west pins turned 180 degrees (D-S7-06): its south row (y 46.44) is CS, SCK, MOSI west
to east, its east column (x 13.21) MISO, GND, GND, INT1 south to north, its north row (y 48.36) GND, GND, 3V3A west to
east and its west column's north pad 3V3A. The rule areas keep vias off the body and tracks out of the interior. The
west face orders the pins aft to forward SCK, MISO, MOSI, NCS, CS, BOOT0, SCL, SDA, -, INT1 (0.5 mm pitch: a via on a
pin's own line just off the pad leaves the next pin's lane exactly 0.15 mm, so every escape below turns before its via).
  SPI      inward on F.Cu under U1's body: SCK one 45-degree step to (11.7, 44.6), MISO to (12.55, 45.0), MOSI to
           (12.55, 45.75), each into its pad from below on B.Cu (SCK one 45-degree step onto x 12.0 west of MOSI's via,
           MISO one 45-degree run east of it; MOSI ends 0.05 mm off its pad centre so SCK's lane keeps 0.2 mm)
  NCS      inward on F.Cu over the IMU to (14.57, 45.4); one B.Cu line U3.1 - via - R10.1 (R10 re-placed beside it)
  CS       west: one 45-degree step to (9.0, 46.4), B.Cu one 45-degree step onto y 46.2, east under U1's pad ends and
           U4.11 and one 45-degree run into pad 12; R11 (re-placed west of pins 89 / 90, rotation 90) on a branch
           straight south off the step's corner, so its pad also lengthens the net's MST (route_check's detour slack),
           its 3V3 pad strapped west to a via
  BOOT0    west: one 45-degree step to (8.8, 47.1), B.Cu into R5.1
  INT1     inward on F.Cu below the north-row pads' GND via to (13.21, 49.15), straight down into pad 4
  QSPI_IO2 F.Cu from inside U1.1's pad (12.0, 51.55: 1.64 mm from GATE_N outside U1's courtyard, r9_pyro_check's 1.5 mm
           neighbour rule), east on y 50.6 (0.55 mm inward of the gate pin U1.3's pad end: on y 50.9 it ran 0.25 mm from
           it, R9P1-PYRO-01; check_r9 P-7b holds 0.5 mm) and down x 13.9 between INT1's via and pin 6's 3V3 / C25.2's
           GND vias (the only
           F.Cu corridor: pin 6's inward 3V3 stub bars any path east of x 14.4 further north), one 45-degree step round
           NCS's via onto x 15.1, one 45-degree run to the via (12.5, 42.07) and B.Cu straight into U3.3
  I2C      F.Cu west from pins 95 / 96 over the buzzer LS120's interior (between its pads) to vias west and north of U5:
           SCL into U5.8 from the west with R12 beside the via, SDA into U5.7 from the north with R13 beyond the via
  SDO      U5.6 straight north into R64.1
  3V3A     one trunk R164.2 - C10.1 - C11.1 down x 11.5 (B.Cu): north of U4 a "U" round the GND pads 6 / 7 (pad 8 up x
           10.79 through C31.1, crossbar y 49.81 through C30.1, pad 5 up x 12.5), their GND via inside it; east on y 51.7
           under U1's forward pad row to the inward via (22.0, 50.75) of U1.20 / 21 (VDDA, VREF+) with C22.1 / C21.1 on
           it; west from pad 8 on y 48.15 below U5's south row into U5.2, U5.1 and C32.1
The critical vias (SPI, CS, NCS, IO2) each have a GND via within 1.5 mm (AGENTS section 3): G_B (SCK, MISO), G_A (MISO,
MOSI, NCS), G_CS (CS), U3.4's (12.5, 40.8) (IO2). GND vias wait for step 8's In1 pour (PENDING); the small parts' other
GND pads (R5.2, R64.2, C21.2, C22.2) are step 8's.
Neighbours left open (later families): LED_RED / LED_YEL west on F.Cu, USB_FAULT_N's west via near (9.25, 44.0) and its
B.Cu run south (R11's pads and vias keep >= 0.28 mm from that via; the LED lanes turn south-west at x <= 8.95 above
it), pins 17 / 18 north (servo family's y 53.3 band).
"""
from r9_route import W, VIA_SIG, VIA_PWR, u1_pin

NETS = ('SPI1_SCK', 'SPI1_MISO', 'SPI1_MOSI', 'IMU_CS', 'IMU_INT1', 'QSPI_NCS', 'QSPI_IO2', 'BOOT0', 'I2C1_SCL',
        'I2C1_SDA', 'BARO_SDO', '3V3A')
RAILS = ('GND', '3V3')
BUDGET = dict(length_mm=66.0, vias=10, critical_layer_changes=6, ratio=1.45)
W_A = 0.25                                   # 3V3A (the R8 rail width)

V = dict(SCK=(11.7, 44.6), MISO=(12.55, 45.0), MOSI=(12.55, 45.75), NCS=(14.57, 45.4), CS=(9.0, 46.4),
         BOOT0=(8.8, 47.1), INT1=(13.21, 49.15), IO2=(12.5, 42.07), SCL=(2.75, 51.3), SDA=(4.97, 53.0),
         A=(22.0, 50.75))
G = dict(A=(13.8, 45.4), B=(12.45, 44.0), CS=(8.35, 45.5), N67=(11.75, 49.1), E23=(14.6, 47.4), U5=(9.2, 49.5),
         U5N=(8.45, 51.7), C32=(0.85, 48.15))
V3 = dict(R10=(15.75, 45.3), R11=(8.45, 44.82), R12=(1.25, 50.44), R13=(4.2, 54.48), R164=(14.05, 57.4))
Y_BAR, Y_EAST, Y_WEST = 49.81, 51.7, 48.15   # 3V3A crossbar, east line, west line

TRACKS = [   # net, layer, width, polyline
    # SPI1, inward
    ('SPI1_SCK', 'F', W, [u1_pin(89), (11.3, 45.0), V['SCK']]),
    ('SPI1_SCK', 'B', W, [V['SCK'], (12.0, 44.9), (12.0, 46.44)]),                                     # U4.13
    ('SPI1_MISO', 'F', W, [u1_pin(90), (12.05, 45.5), V['MISO']]),
    ('SPI1_MISO', 'B', W, [V['MISO'], (13.21, 45.66), (13.21, 46.65)]),                                 # U4.1
    ('SPI1_MOSI', 'F', W, [u1_pin(91), (12.3, 46.0), V['MOSI']]),
    ('SPI1_MOSI', 'B', W, [V['MOSI'], (12.55, 46.44)]),                                                 # U4.14 (0.05 off)
    # QSPI_NCS, inward; U3.1 - via - R10.1 on one line
    ('QSPI_NCS', 'F', W, [u1_pin(92), (13.47, 46.5), V['NCS']]),
    ('QSPI_NCS', 'B', W, [(14.57, 44.6), V['NCS']]),                                                    # U3.1
    ('QSPI_NCS', 'B', W, [V['NCS'], (14.57, 46.19)]),                                                   # R10.1
    # IMU_CS, west
    ('IMU_CS', 'F', W, [u1_pin(93), (9.6, 47.0), V['CS']]),
    ('IMU_CS', 'B', W, [V['CS'], (9.2, 46.2)]),
    ('IMU_CS', 'B', W, [(9.2, 46.2), (11.26, 46.2), (11.5, 46.44)]),                                    # U4.12
    ('IMU_CS', 'B', W, [(9.2, 46.2), (9.2, 45.68)]),                                                    # R11.1
    # BOOT0, west
    ('BOOT0', 'F', W, [u1_pin(94), (9.2, 47.5), V['BOOT0']]),
    ('BOOT0', 'B', W, [V['BOOT0'], (8.0, 47.1)]),                                                      # R5.1
    # IMU_INT1, inward
    ('IMU_INT1', 'F', W, [u1_pin(98), (11.3, 49.5), (11.66, 49.86), (12.5, 49.86), V['INT1']]),
    ('IMU_INT1', 'B', W, [V['INT1'], (13.21, 48.15)]),                                                  # U4.4
    # QSPI_IO2
    ('QSPI_IO2', 'F', W, [(12.0, 51.55), (12.0, 50.6), (13.9, 50.6), (13.9, 47.1), (15.1, 45.9), (15.1, 44.67),
                          V['IO2']]),
    ('QSPI_IO2', 'B', W, [V['IO2'], (14.07, 42.07)]),                                                   # U3.3
    # I2C1 over LS120 to U5
    ('I2C1_SCL', 'F', W, [u1_pin(95), (6.55, 48.0), (3.25, 51.3), V['SCL']]),
    ('I2C1_SCL', 'B', W, [V['SCL'], (2.0, 51.3)]),                                                      # R12.1
    ('I2C1_SCL', 'B', W, [V['SCL'], (3.15, 51.7), (3.72, 51.7)]),                                       # U5.8
    ('I2C1_SDA', 'F', W, [u1_pin(96), (8.35, 48.5), (4.97, 51.88), V['SDA']]),
    ('I2C1_SDA', 'B', W, [V['SDA'], (4.97, 52.425)]),                                                   # U5.7
    ('I2C1_SDA', 'B', W, [V['SDA'], (4.97, 53.62)]),                                                    # R13.1
    ('BARO_SDO', 'B', W, [(6.23, 52.425), (6.23, 53.35)]),                                              # U5.6 -> R64.1
    # 3V3A: trunk, the U over U4's GND pads, east line to VDDA / VREF+, west line to U5
    ('3V3A', 'B', W_A, [(11.5, 57.4), (11.5, 55.6)]),                                                   # R164.2, C10.1
    ('3V3A', 'B', W_A, [(11.5, 55.6), (11.5, 53.6)]),                                                   # C11.1
    ('3V3A', 'B', W_A, [(11.5, 53.6), (11.5, Y_EAST)]),
    ('3V3A', 'B', W_A, [(11.5, Y_EAST), (11.5, Y_BAR)]),
    ('3V3A', 'B', W_A, [(10.79, 48.15), (10.79, Y_BAR), (11.5, Y_BAR)]),                                # U4.8
    ('3V3A', 'B', W_A, [(11.5, Y_BAR), (12.05, Y_BAR)]),                                                # C30.1
    ('3V3A', 'B', W_A, [(12.05, Y_BAR), (12.5, Y_BAR), (12.5, 48.36)]),                                 # U4.5
    ('3V3A', 'B', W_A, [(11.5, Y_EAST), (21.05, Y_EAST), V['A']]),
    ('3V3A', 'B', W_A, [V['A'], (22.68, 50.75)]),                                                        # C21.1
    ('3V3A', 'B', W_A, [V['A'], (22.0, 49.5)]),                                                         # C22.1
    ('3V3A', 'F', W_A, [u1_pin(20), (21.5, V['A'][1]), V['A']]),                                        # U1.20
    ('3V3A', 'F', W_A, [u1_pin(21), V['A']]),                                                           # U1.21
    ('3V3A', 'B', W_A, [(10.79, Y_WEST), (9.7, Y_WEST)]),                                               # C31.1
    ('3V3A', 'B', W_A, [(9.7, Y_WEST), (4.97, Y_WEST)]),
    ('3V3A', 'B', W_A, [(4.97, Y_WEST), (3.72, Y_WEST)]),
    ('3V3A', 'B', W_A, [(3.72, Y_WEST), (2.42, Y_WEST)]),                                               # C32.1
    ('3V3A', 'B', W_A, [(4.97, Y_WEST), (4.97, 48.775)]),                                               # U5.2
    ('3V3A', 'B', W_A, [(3.72, Y_WEST), (3.72, 48.775)]),                                               # U5.1
    # GND straps to their vias
    ('GND', 'B', W, [(11.5, 48.36), (11.75, 48.36), (12.0, 48.36)]),                                    # U4.7, U4.6
    ('GND', 'B', W, [(11.75, 48.36), G['N67']]),
    ('GND', 'B', W, [(13.21, 47.15), (13.21, 47.4), (13.21, 47.65)]),                                   # U4.2, U4.3
    ('GND', 'B', W, [(13.21, 47.4), G['E23']]),
    ('GND', 'B', W, [(6.23, 49.5), (7.48, 49.5)]),                                                      # U5.3, U5.4
    ('GND', 'B', W, [(7.48, 49.5), G['U5'], (9.7, 49.5), (9.7, 48.99)]),                                # C31.2
    ('GND', 'B', W, [(7.48, 51.7), G['U5N']]),                                                          # U5.5
    ('GND', 'B', W, [(1.58, Y_WEST), G['C32']]),                                                        # C32.2
    ('GND', 'B', W, [(12.05, 50.65), (12.88, 50.65)]),                                                  # C30.2 -> C18.2
    # 3V3 pull-up taps
    ('3V3', 'B', W, [(15.43, 46.19), (15.43, 45.62), V3['R10']]),
    ('3V3', 'B', W, [(9.2, 44.82), V3['R11']]),
    ('3V3', 'B', W, [(2.0, 50.44), V3['R12']]),
    ('3V3', 'B', W, [(4.97, 54.48), V3['R13']]),
    ('3V3', 'B', W, [(13.15, 57.4), V3['R164']]),
]
SIGNAL_VIAS = [(n, V[k]) for k, n in (('SCK', 'SPI1_SCK'), ('MISO', 'SPI1_MISO'), ('MOSI', 'SPI1_MOSI'),
                                      ('NCS', 'QSPI_NCS'), ('CS', 'IMU_CS'), ('BOOT0', 'BOOT0'), ('INT1', 'IMU_INT1'),
                                      ('IO2', 'QSPI_IO2'), ('SCL', 'I2C1_SCL'), ('SDA', 'I2C1_SDA'))]
PENDING = list(G.values())
PADS = [   # (U5's lands are two pads each; Draw.pad asserts the first, the tracks end on either)
    ('U1', '20', '3V3A', u1_pin(20)), ('U1', '21', '3V3A', u1_pin(21)), ('U1', '1', 'QSPI_IO2', u1_pin(1)),
    ('U4', '13', 'SPI1_SCK', (12.0, 46.44)), ('U4', '1', 'SPI1_MISO', (13.21, 46.65)),
    ('U4', '14', 'SPI1_MOSI', (12.5, 46.44)), ('U4', '12', 'IMU_CS', (11.5, 46.44)),
    ('U4', '4', 'IMU_INT1', (13.21, 48.15)), ('U4', '5', '3V3A', (12.5, 48.36)), ('U4', '8', '3V3A', (10.79, 48.15)),
    ('U4', '6', 'GND', (12.0, 48.36)), ('U4', '7', 'GND', (11.5, 48.36)), ('U4', '2', 'GND', (13.21, 47.15)),
    ('U4', '3', 'GND', (13.21, 47.65)),
    ('U3', '1', 'QSPI_NCS', (14.07, 44.6)), ('U3', '3', 'QSPI_IO2', (14.07, 42.07)),
    ('R10', '1', 'QSPI_NCS', (14.57, 46.19)), ('R10', '2', '3V3', (15.43, 46.19)),
    ('R11', '1', 'IMU_CS', (9.2, 45.68)), ('R11', '2', '3V3', (9.2, 44.82)),
    ('R5', '1', 'BOOT0', (8.0, 47.1)),
    ('U5', '8', 'I2C1_SCL', (3.72, 51.7)), ('U5', '7', 'I2C1_SDA', (4.97, 51.7)), ('U5', '6', 'BARO_SDO', (6.23, 51.7)),
    ('U5', '1', '3V3A', (3.72, 48.775)), ('U5', '2', '3V3A', (4.97, 48.775)), ('U5', '3', 'GND', (6.23, 48.775)),
    ('U5', '4', 'GND', (7.48, 48.775)), ('U5', '5', 'GND', (7.48, 51.7)),
    ('R12', '1', 'I2C1_SCL', (2.0, 51.3)), ('R12', '2', '3V3', (2.0, 50.44)),
    ('R13', '1', 'I2C1_SDA', (4.97, 53.62)), ('R13', '2', '3V3', (4.97, 54.48)), ('R64', '1', 'BARO_SDO', (6.23, 53.35)),
    ('R164', '2', '3V3A', (11.5, 57.4)), ('R164', '1', '3V3', (13.15, 57.4)),
    ('C10', '1', '3V3A', (11.5, 55.6)), ('C11', '1', '3V3A', (11.5, 53.6)),
    ('C30', '1', '3V3A', (12.05, Y_BAR)), ('C30', '2', 'GND', (12.05, 50.65)), ('C18', '2', 'GND', (12.88, 50.65)),
    ('C31', '1', '3V3A', (9.7, Y_WEST)), ('C31', '2', 'GND', (9.7, 48.99)),
    ('C32', '1', '3V3A', (2.42, Y_WEST)), ('C32', '2', 'GND', (1.58, Y_WEST)),
    ('C21', '1', '3V3A', (22.68, 50.75)), ('C22', '1', '3V3A', (22.0, 49.5)),
]


def draw(d):
    for net, layer, w, pts in TRACKS:
        d.track(net, layer, w, pts)
    for net, at in SIGNAL_VIAS:
        d.via(net, at, VIA_SIG)
    d.via('3V3A', V['A'], VIA_PWR)
    for at in G.values():
        d.via('GND', at, VIA_SIG)
    for at in V3.values():
        d.via('3V3', at, VIA_SIG)
