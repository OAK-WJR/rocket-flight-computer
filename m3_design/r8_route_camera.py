"""R8 step 6 family camera: the camera UART through the translator U12 to J9, the camera supply's control and sense
(eFuse U7 network, CAM_5V sense divider), and the camera I/O rail from U13 (r8_route.py). R8_DECISIONS D55
(placement), D56 (topology).

UART (D56). U1's east face carries TX (pin 38, y 45.0) aft of RX (pin 37, y 45.5); J9 carries RX_WIRE (pin 3) aft of
TX_WIRE (pin 4). U12 (TXU0202, on the top) is turned with its A port (MCU side, pins 4 / 5) west toward U1 and its B
port (pins 1 / 8) east toward R100 / R101 and J9 (D55), so the wire side runs straight: pin 1 -> R100 -> J9.3 and
pin 8 -> R101 -> J9.4, the series resistors stood on end in line with their pins. On the top side the A port's pin 4
(RX) is in the aft row and pin 5 (TX) in the forward row, the reverse of U1's order: one crossing that no placement
of a top-side part removes. TX stays on F.Cu (lifted to y 45.75 past R78's GND via, then under U12's body into pin
5's inner end); RX takes the one under-and-back hop: a via beside pin 37, B.Cu under the radio lanes' ends, a via
beside pin 4 (the aft side of U12 is the only side with room: NRST's F.Cu lane x 33.4 bounds it on the west, C76 on
B.Cu on the south).
  - The wire pads: R100's aft (TP75 straight aft of it; J9.2's pocket stays open to the F.Cu pour aft), R101's
    forward (TP76 straight forward of it).
  - OE (pin 31) runs east on y 48.5 to a T on pin 6's line: pin 6 aft, the pull-down R102 forward (stood on end on
    that line, D55); a via on the lane drops to the test pad TP91 on B.Cu.
  - U12's supplies: C100 (3V3 / GND) under pins 3 / 2 in the aft row, straight; its 3V3 via west of it. Pin 7
    (CAM_IO_3V3) drops through a via to C93 on the bottom (D55) and on to U13's output network.
Supply sense and control:
  - CAM_5V_SENSE (pin 35) runs east on y 46.5 and drops to the divider R104 / R105 / C94, stood in a column x 33.3 on
    B.Cu (D55); CAM_5V reaches R104 on y 47.4 from C75 (the buck's output capacitor), which also feeds U13 down the
    gap between U13's pad columns (pin 1, and C91 between pins 4 and 5).
  - CAM_IO_3V3 on B.Cu: C93 -> forward on x 36.225 -> east on y 51.2 under U13's forward edge to TP90, with R103, C92
    and U13.5 tapped off it.
  - CAM_FAULT_N / CAM_PWR_EN (pins 41 / 42): the step-4 escapes (D33) to vias and B.Cu aft; FAULT_N to R76 (its
    pull-up, 3V3 via) and R77 (to U7's FLT); PWR_EN round U7's west end (x 28.25) and one 45-degree run
    into R74.1 (D37, D107).
  - U7's local network (EN, DVDT, ILIM, FLT_RAW) on B.Cu beside the part.
"""
from r8_route import W, VIA_PWR, VIA_SIG, u1_pin

NETS = ('CAM_MCU_RX', 'CAM_MCU_TX', 'CAM_RX_BUFFER', 'CAM_TX_BUFFER', 'CAM_RX_WIRE', 'CAM_TX_WIRE', 'CAM_UART_OE',
        'CAM_IO_3V3', 'CAM_5V_SENSE', 'CAM_FAULT_N', 'CAM_PWR_EN', 'CAM_EN', 'CAM_DVDT', 'CAM_FLT_RAW', 'CAM_ILIM',
        'CAM_5V')
CONTINUES = ('CAM_5V',)        # step 5 drew the buck output (L3 / C75 / C76 / TP72) and J9.1's feed
RAILS = ('GND', '3V3')
# 89.9 mm; worst ratio 1.375, CAM_PWR_EN (D37's loop), since fix pass 3's one-diagonal entry into R74.1 (D107; it was
# 91.9 mm and 1.50 against a 1.55 budget, tightened to 1.40)
BUDGET = dict(length_mm=95.0, vias=6, critical_layer_changes=0, ratio=1.40)
W_PWR = 0.3

# U12 (rotation 270): aft row y 44.0 (pins 4, 3, 2, 1 west to east), forward row y 47.1 (pins 5, 6, 7, 8)
X4, X3, X2, X1 = 34.45, 34.95, 35.45, 35.95
YA, YF = 44.0, 47.1
V_RX1, V_RX2 = (31.85, 45.5), (33.95, 44.0)     # RX's hop (V_RX2 0.20 mm from RADIO_NRST's lane x 33.4: fix pass 1, D91)
V_3V3 = (34.0, 43.1)                            # U12.3 / C100.1 to In2 3V3
V_SENSE = (33.3, 46.5)                          # CAM_5V_SENSE to the divider column x 33.3
V_OE = (32.5, 48.5)                             # OE to TP91
V_IO = (35.45, 48.5)                            # U12.7 to C93 (bottom)
# FAULT_N's B.Cu lane runs 0.5 mm beside PWR_EN's (x 32.35 / 31.85): no GND pour finger between them
V_FAULT, V_PWR_EN = (32.35, 43.5), (31.85, 43.0)
V_R76 = (34.425, 37.4)                          # R76.1 (FAULT_N pull-up) to In2 3V3
V_C92G = (43.9, 55.0)                           # C92.2 (U13's output capacitor) to In1 GND

TRACKS = [   # net, layer, width, polyline
    # UART, MCU side
    # TX lifts to y 45.75 past R78's GND via (33.9, 45.2), then under U12 into pin 5's inner end
    ('CAM_MCU_TX', 'F', W, [u1_pin(38), (32.3, 45.0), (33.05, 45.75), (X4, 45.75), (X4, YF)]),
    ('CAM_MCU_RX', 'F', W, [u1_pin(37), V_RX1]),
    ('CAM_MCU_RX', 'B', W, [V_RX1, (33.35, YA), V_RX2]),
    ('CAM_MCU_RX', 'F', W, [V_RX2, (X4, YA)]),                                        # pin 4 from the west
    # UART, wire side: straight through the series resistors; test pads off the wire pads
    ('CAM_RX_BUFFER', 'F', W, [(X1, YA), (37.5, YA)]),                                # R100.2
    ('CAM_TX_BUFFER', 'F', W, [(X1, YF), (37.5, YF)]),                                # R101.1
    # R100 stands with its wire pad aft, so TP75 hangs straight off it and J9.2's pocket stays open to the pour aft
    ('CAM_RX_WIRE', 'F', W, [(37.5, 42.35), (38.3, 42.35), (38.3, YA), (39.125, 44.825), (40.75, 44.825)]),
    ('CAM_RX_WIRE', 'F', W, [(37.5, 42.35), (37.5, 40.3)]),                           # TP75
    ('CAM_TX_WIRE', 'F', W, [(37.5, 48.75), (38.075, 48.75), (40.75, 46.075)]),       # J9.4
    ('CAM_TX_WIRE', 'F', W, [(37.5, 48.75), (37.5, 51.1)]),                           # TP76
    # OE: U1.31 -> T on pin 6's line (pin 6 aft, R102 forward); TP91 on the bottom
    ('CAM_UART_OE', 'F', W, [u1_pin(31), V_OE, (34.95, 48.5)]),
    ('CAM_UART_OE', 'F', W, [(34.95, YF), (34.95, 48.5), (34.95, 49.325)]),
    ('CAM_UART_OE', 'B', W, [V_OE, (32.5, 52.3)]),
    # U12 supplies
    ('3V3', 'F', W, [(X3, YA), (X3, 42.8)]),                                          # pin 3 -> C100.1
    ('3V3', 'F', W, [(34.78, 42.8), (34.3, 42.8), V_3V3]),
    ('GND', 'F', W, [(X2, YA), (X2, 42.8)]),                                          # pin 2 -> C100.2
    ('GND', 'B', W, [(34.16, 48.7), (34.7, 48.7), (34.7, 49.95)]),                    # R105.2 -> C94.2
    ('CAM_IO_3V3', 'F', W_PWR, [(35.45, YF), V_IO]),
    # CAM_IO_3V3 on the bottom: C93 -> TP90, U13.5, R103, C92
    ('CAM_IO_3V3', 'B', W_PWR, [V_IO, (36.225, 48.5), (36.225, 51.2), (37.375, 51.2), (39.8, 51.2), (42.1, 51.2),
                                (44.75, 51.2), (44.75, 52.35)]),
    ('CAM_IO_3V3', 'B', W_PWR, [(37.375, 51.2), (37.375, 52.6)]),                    # R103.1
    ('CAM_IO_3V3', 'B', W_PWR, [(39.8, 51.2), (39.8, 55.0)]),                        # C92.1
    ('CAM_IO_3V3', 'B', W_PWR, [(42.1, 51.2), (42.1, 50.55)]),                       # U13.5
    ('GND', 'B', W_PWR, [(42.8, 55.0), V_C92G]),                                      # C92.2's return
    # CAM_5V: C75.1 -> R104 west; -> U13.1 and C91 down U13's middle
    ('CAM_5V', 'B', W_PWR, [(38.5, 46.07), (38.5, 47.4), (34.16, 47.4)]),
    # (U13.1 entered along its axis to its centre: a 45-degree chamfer here would end in a 0.35 mm segment inside the pad,
    # off its centre; fix pass 1 tried it and kept this, R8_VALIDATION C11)
    ('CAM_5V', 'B', W_PWR, [(38.5, 47.4), (40.4, 47.4), (40.8, 47.8), (40.8, 49.6), (40.8, 50.55), (39.5, 50.55)]),
    ('CAM_5V', 'B', W_PWR, [(40.8, 49.6), (44.17, 49.6)]),                            # C91.1
    # CAM_5V_SENSE: pin 35 -> the divider column x 33.3 (R104.2, R105.1, C94.1)
    ('CAM_5V_SENSE', 'F', W, [u1_pin(35), V_SENSE]),
    ('CAM_5V_SENSE', 'B', W, [V_SENSE, (33.3, 47.4), (33.3, 48.7), (33.3, 49.95)]),
    # CAM_FAULT_N: pin 41 -> via -> B.Cu south to R76.2 (pull-up) -> R77.1
    ('CAM_FAULT_N', 'F', W, [u1_pin(41), V_FAULT]),
    # one 45-degree run through R76.2 (pull-up) to above R77.1
    ('CAM_FAULT_N', 'B', W, [V_FAULT, (32.35, 36.975), (34.05, 35.275), (34.05, 34.575)]),
    ('3V3', 'B', W, [(34.425, 36.55), V_R76]),                                        # R76.1
    # CAM_PWR_EN: pin 42 -> via -> B.Cu south, round U7's west end (x 28.25) and one 45-degree run into R74.1 (D37;
    # fix pass 3, R8P3-ROUTING-03, D107: was x 28.0 with an L and a 2.78 mm stub into R74.1, 1.98 mm longer)
    ('CAM_PWR_EN', 'F', W, [u1_pin(42), V_PWR_EN]),
    ('CAM_PWR_EN', 'B', W, [V_PWR_EN, (31.85, 36.8), (28.25, 36.8), (28.25, 30.025), (30.775, 27.5)]),
    # U7's network (B.Cu)
    ('CAM_EN', 'B', W, [(32.425, 25.9), (32.425, 27.5), (32.425, 28.0), (33.55, 29.125), (33.55, 29.75)]),
    ('CAM_DVDT', 'B', W, [(31.655, 29.9), (33.05, 29.9)]),
    ('CAM_FLT_RAW', 'B', W, [(34.05, 31.65), (34.05, 32.925)]),
    ('CAM_ILIM', 'B', W, [(33.55, 31.65), (33.55, 32.15), (30.575, 32.15), (30.575, 33.05), (30.575, 34.9)]),
]
SIGNAL_VIAS = [('CAM_MCU_RX', V_RX1), ('CAM_MCU_RX', V_RX2), ('CAM_5V_SENSE', V_SENSE), ('CAM_UART_OE', V_OE),
               ('CAM_FAULT_N', V_FAULT), ('CAM_PWR_EN', V_PWR_EN)]
# rail vias: R76's in the open at the board's default size; U12's two at the signal size (a few mA each), which the
# NRST lane, C76 and the OE corner leave room for
POWER_VIAS = [('3V3', V_3V3, VIA_SIG), ('3V3', V_R76, VIA_PWR), ('CAM_IO_3V3', V_IO, VIA_SIG), ('GND', V_C92G, VIA_PWR)]
PADS = [('U12', '4', 'CAM_MCU_RX', (X4, YA)), ('U12', '3', '3V3', (X3, YA)), ('U12', '2', 'GND', (X2, YA)),
        ('U12', '1', 'CAM_RX_BUFFER', (X1, YA)), ('U12', '5', 'CAM_MCU_TX', (X4, YF)),
        ('U12', '6', 'CAM_UART_OE', (34.95, YF)), ('U12', '7', 'CAM_IO_3V3', (35.45, YF)),
        ('U12', '8', 'CAM_TX_BUFFER', (X1, YF)),
        ('C100', '1', '3V3', (34.78, 42.8)), ('C100', '2', 'GND', (35.62, 42.8)),
        ('R100', '2', 'CAM_RX_BUFFER', (37.5, 44.0)), ('R100', '1', 'CAM_RX_WIRE', (37.5, 42.35)),
        ('R101', '1', 'CAM_TX_BUFFER', (37.5, 47.1)), ('R101', '2', 'CAM_TX_WIRE', (37.5, 48.75)),
        ('J9', '3', 'CAM_RX_WIRE', (40.75, 44.825)), ('J9', '4', 'CAM_TX_WIRE', (40.75, 46.075)),
        ('TP75', '1', 'CAM_RX_WIRE', (37.65, 40.3)), ('TP76', '1', 'CAM_TX_WIRE', (37.5, 51.1)),
        ('R102', '1', 'CAM_UART_OE', (34.95, 49.325)), ('R102', '2', 'GND', (34.95, 50.975)),
        ('TP91', '1', 'CAM_UART_OE', (32.5, 52.3)),
        ('C93', '1', 'CAM_IO_3V3', (36.225, 48.5)), ('C93', '2', 'GND', (37.775, 48.5)),
        ('TP90', '1', 'CAM_IO_3V3', (44.75, 52.35)), ('R103', '1', 'CAM_IO_3V3', (37.375, 52.6)),
        ('C92', '1', 'CAM_IO_3V3', (39.8, 55.0)), ('C92', '2', 'GND', (42.8, 55.0)), ('U13', '5', 'CAM_IO_3V3', (42.1, 50.55)),
        ('C75', '1', 'CAM_5V', (38.5, 46.07)), ('U13', '1', 'CAM_5V', (39.5, 50.55)),
        ('C91', '1', 'CAM_5V', (44.17, 49.975)), ('R104', '1', 'CAM_5V', (34.16, 47.4)),
        ('R104', '2', 'CAM_5V_SENSE', (33.3, 47.4)), ('R105', '1', 'CAM_5V_SENSE', (33.3, 48.7)),
        ('C94', '1', 'CAM_5V_SENSE', (33.3, 49.95)),
        ('R76', '2', 'CAM_FAULT_N', (32.775, 36.55)), ('R76', '1', '3V3', (34.425, 36.55)),
        ('R77', '1', 'CAM_FAULT_N', (34.05, 34.575)), ('R77', '2', 'CAM_FLT_RAW', (34.05, 32.925)),
        ('R74', '1', 'CAM_PWR_EN', (30.775, 27.5)), ('R74', '2', 'CAM_EN', (32.425, 27.5)),
        ('R75', '1', 'CAM_EN', (32.425, 25.9)), ('U7', '2', 'CAM_EN', (33.55, 29.75)),
        ('U7', '1', 'CAM_DVDT', (33.05, 29.75)), ('C70', '1', 'CAM_DVDT', (31.655, 29.9)),
        ('U7', '6', 'CAM_FLT_RAW', (34.05, 31.65)), ('U7', '7', 'CAM_ILIM', (33.55, 31.65)),
        ('R70', '1', 'CAM_ILIM', (30.575, 33.05)), ('TP73', '1', 'CAM_ILIM', (30.1, 34.9))]


def draw(d):
    for ref, num, net, at in PADS:
        d.pad(ref, num, net, at)
    for net, layer, w, pts in TRACKS:
        d.track(net, layer, w, pts)
    for net, xy in SIGNAL_VIAS:
        d.via(net, *xy)
    for net, xy, size in POWER_VIAS:
        d.via(net, *xy, size)
