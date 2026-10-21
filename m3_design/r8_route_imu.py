"""R8 step 6 family imu (imu_i2c): the IMU U4 (SPI1, CS, INT1) and the barometer U5 (I2C1, SDO), their pull-ups and
decoupling, and the sensors' 3V3A from step 5's trunk end (r8_route.py). R8_DECISIONS D52 (placement), D54 (topology).

Both sensors are bottom parts west of U1 at fixed positions and rotations (D13, D38). U4's SPI pads face forward
(pads 14 / 13 / 12 = MOSI, SCK, CS, west to east), MISO and INT1 sit on its west column, its supplies on the aft row
and east column; U5's I2C pads face forward. U1's west face orders the pins aft to forward SCK, MISO, MOSI, CS, SCL,
SDA, INT1, so no single-layer order reaches the pads (D54). The routing is one F.Cu fan over the sensors (the top
layer carries nothing else there) and short B.Cu stubs into the pads, one via per net:
  - The SPI lanes leave the west face, run 45 degrees south-west as a bus and drop straight down over U4 to vias just
    below its forward pad row (MISO below pad 1, MOSI below pad 14, CS below pad 12). SCK, the outermost lane, passes
    under MISO's and MOSI's vias and turns east to its via below pad 13: the one crossing the pin order forces, made
    without a second via. One GND via within 1.5 mm of each SPI via (AGENTS section 3).
  - CS's pull-up R11 sits on the top beside CS's via (D52): CS's lane drops on R11's x into R11.1 and steps west
    to its via, which leaves the room between MOSI's and CS's lanes over U4's aft row for pads 6 / 7's GND via.
  - SCL and SDA run down U4's east side and across U5 to vias below pads 8 / 7; their pull-ups R12 / R13 and SDO's R64
    sit in line beyond (D52).
  - INT1 drops beside U1 (NRST's B.Cu diagonal bounds that spot) and runs on B.Cu north of U4 into pad 4.
  - 3V3A: step 5's trunk via (15.0, 62.2) on B.Cu to a tee between the sensors: west along the gap to U5's supply pads
    and C32, north through C30.1 (the cap in series with the feed) and up U4's east side past C31 (D52) to pad 8, and
    round the aft row to pad 5 (a U over pads 6 / 7, whose GND via sits inside it). No new 3V3A via: the net already has the one layer change it needs plus route_check's
    two slack (extra_vias).
The IMU / BARO rule areas (no via or fill under the parts, no track between their pad rows) hold: every via sits
outside them, every track enters its pad from outside the inner areas.
"""
from r8_route import W, u1_pin

NETS = ('SPI1_SCK', 'SPI1_MISO', 'SPI1_MOSI', 'IMU_CS', 'IMU_INT1', 'I2C1_SCL', 'I2C1_SDA', 'BARO_SDO', '3V3A')
RAILS = ('GND', '3V3')
CONTINUES = ('3V3A',)          # step 5's trunk (D44) ends at the via (15.0, 62.2)
# 105.6 mm of signal copper, one via per signal net; SCK's 1.56 is the pin-order crossing (D54)
BUDGET = dict(length_mm=110.0, vias=7, critical_layer_changes=4, ratio=1.6)
W_3V3A = 0.25

V_MISO, V_MOSI, V_SCK, V_CS = (8.79, 55.75), (9.5, 55.65), (10.0, 56.35), (10.5, 55.65)
V_INT1, V_SCL, V_SDA = (13.3, 51.0), (8.72, 62.85), (9.97, 62.85)
T_3V3A = (12.95, 57.85)


def fan(pin, x_exit, x_v, y_end):
    """A lane of the SPI / I2C fan: west out of the pin to x_exit, 45 degrees south-west to x_v, south to y_end."""
    px, py = u1_pin(pin)
    c = x_exit + py                                       # the 45-degree line x + y = c
    return [(px, py), (x_exit, py), (x_v, round(c - x_v, 4)), (x_v, y_end)]


TRACKS = [   # net, layer, width, polyline
    # SPI1: the fan down over U4; SCK round MISO's and MOSI's vias to its own below pad 13
    ('SPI1_SCK', 'F', W, fan(89, 14.2, 8.2, V_SCK[1]) + [V_SCK]),
    ('SPI1_SCK', 'B', W, [V_SCK, (10.0, 54.76)]),                                                       # pad 13
    ('SPI1_MISO', 'F', W, fan(90, 14.45, 8.79, V_MISO[1])),
    ('SPI1_MISO', 'B', W, [V_MISO, (8.79, 54.55)]),                                                     # pad 1
    ('SPI1_MOSI', 'F', W, fan(91, 14.6, 9.5, V_MOSI[1])),
    ('SPI1_MOSI', 'B', W, [V_MOSI, (9.5, 54.76)]),                                                      # pad 14
    ('IMU_CS', 'F', W, fan(93, 14.45, 11.25, 55.65) + [V_CS]),                                           # R11.1 (top)
    ('IMU_CS', 'B', W, [V_CS, (10.5, 54.76)]),                                                          # pad 12
    # I2C1: down U4's east side, across U5 to vias below pads 8 / 7; pull-ups R12 / R13 beyond
    # SCL leaves pin 95 to x 14.243 so its 45-degree run is 0.5 mm (perpendicular) from SDA's, not 0.354 mm (fix pass 1,
    # D91: the pair was 0.154 mm apart edge to edge over 2.8 mm)
    ('I2C1_SCL', 'F', W, fan(95, 14.243, 12.0, 59.57) + [V_SCL]),
    ('I2C1_SCL', 'B', W, [(8.72, 62.025), V_SCL, (8.72, 63.57)]),                                      # U5.8, R12.1
    ('I2C1_SDA', 'F', W, fan(96, 14.45, 12.5, 60.32) + [V_SDA]),
    ('I2C1_SDA', 'B', W, [(9.97, 62.025), V_SDA, (9.97, 63.57)]),                                      # U5.7, R13.1
    ('BARO_SDO', 'B', W, [(11.23, 62.025), (11.23, 63.57)]),                                           # U5.6 -> R64.1
    # INT1: drops beside U1, B.Cu north of U4 into pad 4 from the aft side
    ('IMU_INT1', 'F', W, [u1_pin(98), (14.3, 50.0), V_INT1]),
    ('IMU_INT1', 'B', W, [V_INT1, (8.79, 51.0), (8.79, 53.05)]),
    # 3V3A: trunk via -> tee between the sensors -> U5 / C32 west; north through C30.1, past C31 to pad 8, round to pad 5
    ('3V3A', 'B', W_3V3A, [(15.0, 62.2), (15.0, 58.25), (14.6, 57.85), T_3V3A]),
    ('3V3A', 'B', W_3V3A, [T_3V3A, (9.97, 57.85), (8.72, 57.85), (7.3, 57.85)]),                       # C32.1
    ('3V3A', 'B', W_3V3A, [(9.97, 57.85), (9.97, 58.375)]),                                            # U5.2
    ('3V3A', 'B', W_3V3A, [(8.72, 57.85), (8.72, 58.375)]),                                            # U5.1
    # U4's branch passes through C30.1 (the cap in series with the feed, not on a stub)
    ('3V3A', 'B', W_3V3A, [T_3V3A, (12.95, 55.92), (12.3, 55.92), (12.3, 53.05)]),                    # C30.1
    ('3V3A', 'B', W_3V3A, [(12.95, 53.05), (12.3, 53.05), (11.21, 53.05)]),                           # C31.1, pad 8
    ('3V3A', 'B', W, [(11.21, 53.05), (11.21, 51.5), (9.5, 51.5), (9.5, 52.84)]),                      # pad 5
    # 3V3 pull-ups to In2 3V3: R11 (top), R12 / R13
    ('3V3', 'F', W, [(11.25, 56.51), (11.25, 57.2)]),
    ('3V3', 'B', W, [(9.97, 64.43), (8.72, 64.43), (8.0, 64.43)]),
    # GND: U4 pads 2 / 3 west, 6 / 7 inside the 3V3A U; U5 pads 3 / 4 and 5 east; C30 / C31; R64.2
    ('GND', 'B', W, [(8.79, 53.55), (8.79, 53.8), (8.79, 54.05)]),
    ('GND', 'B', W, [(8.79, 53.8), (7.5, 53.8)]),
    ('GND', 'B', W, [(10.0, 52.84), (10.5, 52.84), (10.5, 52.1)]),      # via just aft of IMU_body_B
    ('GND', 'B', W, [(11.23, 59.1), (12.48, 59.1), (13.45, 59.1)]),
    ('GND', 'B', W, [(12.48, 61.3), (13.6, 61.3)]),
    ('GND', 'B', W, [(12.95, 53.89), (13.545, 54.485), (12.95, 55.08)]),                               # C31.2, C30.2
    ('GND', 'B', W, [(7.3, 57.06), (6.6, 57.06)]),                                                     # C32.2
    ('GND', 'B', W, [(11.23, 64.43), (11.9, 64.43)]),                                                  # R64.2
]
SIGNAL_VIAS = [('SPI1_MOSI', V_MOSI), ('SPI1_MISO', V_MISO), ('SPI1_SCK', V_SCK), ('IMU_CS', V_CS),
               ('IMU_INT1', V_INT1), ('I2C1_SCL', V_SCL), ('I2C1_SDA', V_SDA)]
GND_VIAS = [(9.25, 57.1),      # partner of V_MISO / V_MOSI / V_SCK (1.43 / 1.47 / 1.06 mm)
            (10.6, 57.0),      # partner of V_CS (1.35 mm)
            (7.5, 53.8), (10.5, 52.1), (13.45, 59.1), (13.6, 61.3), (13.545, 54.485), (6.6, 57.06), (11.9, 64.43)]
RAIL_VIAS = [('3V3', (11.25, 57.2)), ('3V3', (8.0, 64.43))]
PADS = [('U4', '14', 'SPI1_MOSI', (9.5, 54.76)), ('U4', '1', 'SPI1_MISO', (8.79, 54.55)),
        ('U4', '13', 'SPI1_SCK', (10.0, 54.76)), ('U4', '12', 'IMU_CS', (10.5, 54.76)),
        ('U4', '4', 'IMU_INT1', (8.79, 53.05)), ('U4', '5', '3V3A', (9.5, 52.84)), ('U4', '8', '3V3A', (11.21, 53.05)),
        ('U4', '2', 'GND', (8.79, 54.05)), ('U4', '3', 'GND', (8.79, 53.55)), ('U4', '6', 'GND', (10.0, 52.84)),
        ('U4', '7', 'GND', (10.5, 52.84)), ('R11', '1', 'IMU_CS', (11.25, 55.65)), ('R11', '2', '3V3', (11.25, 56.51)),
        ('R12', '1', 'I2C1_SCL', (8.72, 63.57)), ('R12', '2', '3V3', (8.72, 64.43)),
        ('R13', '1', 'I2C1_SDA', (9.97, 63.57)), ('R13', '2', '3V3', (9.97, 64.43)),
        ('R64', '1', 'BARO_SDO', (11.23, 63.57)), ('R64', '2', 'GND', (11.23, 64.43)),
        # U5's pads are two rectangles each; pad() reports the first (forward pads: the inner one at y 61.3)
        ('U5', '8', 'I2C1_SCL', (8.72, 61.3)), ('U5', '7', 'I2C1_SDA', (9.97, 61.3)),
        ('U5', '6', 'BARO_SDO', (11.23, 61.3)), ('U5', '1', '3V3A', (8.72, 58.375)), ('U5', '2', '3V3A', (9.97, 58.375)),
        ('U5', '3', 'GND', (11.23, 58.375)), ('U5', '4', 'GND', (12.48, 58.375)), ('U5', '5', 'GND', (12.48, 61.3)),
        ('C30', '1', '3V3A', (12.95, 55.92)), ('C30', '2', 'GND', (12.95, 55.08)),
        ('C31', '1', '3V3A', (12.95, 53.05)), ('C31', '2', 'GND', (12.95, 53.89)),
        ('C32', '1', '3V3A', (7.3, 57.9)), ('C32', '2', 'GND', (7.3, 57.06))]


def draw(d):
    for ref, num, net, at in PADS:
        d.pad(ref, num, net, at)
    for net, layer, w, pts in TRACKS:
        d.track(net, layer, w, pts)
    for net, xy in SIGNAL_VIAS:
        d.via(net, *xy)
    for xy in GND_VIAS:
        d.via('GND', *xy)
    for net, xy in RAIL_VIAS:
        d.via(net, *xy)
