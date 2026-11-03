"""R9 step 7 family camera: the camera UART through the translator U12, its OE, the translator's camera-side supply
(LDO U13), the camera-5V sense divider and the camera eFuse U7's control nets (r9_route.py; R9_DECISIONS D-S7-13).

U1's east face, south to north: 41 CAM_FAULT_N, 42 CAM_PWR_EN (south of RADIO_NRST's F.Cu lane y 44.0), 38 TX, 37 RX,
35 CAM_5V_SENSE, 31 OE (inside the pin-28..31 box closed on F.Cu by ARM1_SENSE_MCU, R170 and the ARM1_SENSE lane).
U12's MCU pins are its west end: 4 (RX) on the south row, 5 (TX) on the north row, so RX and TX must cross once.
  RX           U1.37 to a via beside the pin (26.75, 45.0), B.Cu y 44.5 under TX and the other F.Cu lanes to a via
               (33.15, 44.5) west of RADIO_NRST's corner, F.Cu north and one 45-degree run into U12.4
  TX           F.Cu y 44.5 east, x 31.8 north, y 51.1 east into U12.5
  OE           U1.31 to a via in the box (26.75, 48.0), B.Cu one 45-degree step onto y 48.4 (south of the box's exit
               band, which power_ctl's BAT_FAULT_N / LOGIC_SOURCE_ST use), x 33.9 north to a via west of R102, F.Cu
               into R102.1 / U12.6 and to TP91 (F.Cu)
  5V_SENSE     U1.35 straight east on F.Cu y 46.0 (under pyro's MCU-side via at 0.15 mm, D-S7-12) to a via (31.2, 46.25),
               B.Cu to the divider R104 / R105 / C94 beside C76.1 (R104.1's CAM_5V tap)
  BUFFER/WIRE  U12.1 / 8 straight east into R100 / R101; R100.1 / R101.2 down / up into TP75 / TP76 and round J9's
               power pins into J9.3 / J9.4
  CAM_IO_3V3   U12.7 north to a via (35.45, 51.95); B.Cu trunk north: C93 (U12.7's bypass, west) and U13.5 (OUT, east)
               at one cross, C92 (bulk) at its north end; one via under C92's body to TP90 and R103 (bleed) on F.Cu
               (the (42, 59.5) support's M-5 disk keeps parts off the space east of C92)
  CAM_5V       step 6's PARTIAL rail finished: C75.1 north into U13.1 (IN) and C91.1, C76.1 west into R104.1
  3V3          U12.3 and C100.1 joined straight (camera_bypass); C100.1 F.Cu x 34.975 south to a via (35.225, 40.83)
               between R76 and C74, into R76.1 (CAM_FAULT_N's pull-up) and one In2 3V3 via (33.1, 42.65): In2's 3V3
               region ends at x ~33.4 here, so U12's VCCA reaches it through R76's pad
  GND          C100.2 straight into U12.2, U12.2 north under U12's body to R78's GND via (moved north, step 6 table,
               D-S7-13), C93.2 into the same via; R70.2 to a via
  eFuse        CAM_FAULT_N F.Cu y 43.0, 45 degrees beside CAM_PWR_EN and y 41.6 to a via (32.775, 41.6) (D-S8-07), B.Cu into R76.2 and R77.1; CAM_PWR_EN F.Cu y 42.5 and
               x 30.775 south (east of the radio lanes, west of RADIO_NRST) to a via into R74.1; CAM_EN R75.1 - R74.2 -
               U7.2, CAM_DVDT C70.1 - U7.1, CAM_FLT_RAW U7.6 - R77.2, CAM_ILIM U7.7 - R70.1 - TP73 on B.Cu
No camera net is a critical class: its vias need no GND partner. R70.2's GND via waits for step 8 (PENDING).
"""
from r9_route import W, VIA_SIG, u1_pin

NETS = ('CAM_MCU_RX', 'CAM_MCU_TX', 'CAM_RX_BUFFER', 'CAM_TX_BUFFER', 'CAM_RX_WIRE', 'CAM_TX_WIRE', 'CAM_UART_OE',
        'CAM_IO_3V3', 'CAM_5V_SENSE', 'CAM_FAULT_N', 'CAM_PWR_EN', 'CAM_EN', 'CAM_DVDT', 'CAM_FLT_RAW', 'CAM_ILIM')
CONTINUES = ('CAM_5V',)            # step 6's PARTIAL rail, open at U13.1, R104.1, C91.1 (r9_power.PARTIAL)
RAILS = ('GND', '3V3')
BUDGET = dict(length_mm=110.0, vias=7, critical_layer_changes=0, ratio=1.40)
W_IN = 0.4                         # CAM_5V into U13 / C91 (the step-6 feed width)

V_RX1, V_RX2 = (26.75, 45.0), (33.15, 44.5)
V_BOX, V_OE = (26.75, 48.0), (33.9, 53.4)
V_5V = (31.2, 46.25)
V_IO, V_IO2 = (35.45, 51.95), (34.6, 57.4)
V_FLT, V_PEN = (32.775, 41.6), (30.775, 32.6)
V3 = dict(C100=(35.225, 40.83), IN2=(33.1, 42.65))
G_U12 = (34.675, 50.15)            # R78's GND via (step 6, r9_power.CAMERA_GND)
G_R70 = (30.0, 36.9)

TRACKS = [   # net, layer, width, polyline
    # UART, MCU side: RX hops under TX
    ('CAM_MCU_RX', 'F', W, [u1_pin(37), V_RX1]),
    ('CAM_MCU_RX', 'B', W, [V_RX1, (26.75, 44.5), V_RX2]),
    ('CAM_MCU_RX', 'F', W, [V_RX2, (33.15, 46.6), (34.4, 47.85)]),                                      # U12.4
    ('CAM_MCU_TX', 'F', W, [u1_pin(38), (31.8, 44.5), (31.8, 51.1), (34.45, 51.1)]),                    # U12.5
    # UART, camera side
    ('CAM_RX_BUFFER', 'F', W, [(35.95, 48.0), (37.5, 48.0)]),                                           # U12.1 -> R100.2
    ('CAM_TX_BUFFER', 'F', W, [(35.95, 51.1), (37.5, 51.1)]),                                           # U12.8 -> R101.1
    ('CAM_RX_WIRE', 'F', W, [(37.5, 46.35), (37.5, 44.9)]),                                             # TP75
    ('CAM_RX_WIRE', 'F', W, [(37.5, 46.35), (38.3, 46.35), (39.0, 47.05), (39.0, 48.225), (39.6, 48.825),
                             (40.75, 48.825)]),                                                         # J9.3
    ('CAM_TX_WIRE', 'F', W, [(37.5, 52.75), (37.5, 54.6)]),                                             # TP76
    ('CAM_TX_WIRE', 'F', W, [(37.5, 52.75), (38.4, 52.75), (39.4, 51.75), (39.4, 50.475), (39.8, 50.075),
                             (40.75, 50.075)]),                                                         # J9.4
    # OE
    ('CAM_UART_OE', 'F', W, [u1_pin(31), V_BOX]),
    ('CAM_UART_OE', 'B', W, [V_BOX, (27.15, 48.4), (33.9, 48.4), V_OE]),
    ('CAM_UART_OE', 'F', W, [V_OE, (34.5, 52.8)]),                                                      # R102.1
    ('CAM_UART_OE', 'F', W, [(34.95, 52.775), (34.95, 51.1)]),                                          # U12.6
    ('CAM_UART_OE', 'F', W, [V_OE, (32.9, 54.4)]),                                                      # TP91
    # CAM_5V_SENSE and its divider
    ('CAM_5V_SENSE', 'F', W, [u1_pin(35), (30.95, 46.0), V_5V]),
    ('CAM_5V_SENSE', 'B', W, [V_5V, (31.65, 45.8)]),                                                    # C94.1
    ('CAM_5V_SENSE', 'B', W, [V_5V, (31.5, 46.55), (32.37, 46.55), (32.37, 47.55)]),                    # R104.2, R105.1
    ('CAM_5V', 'B', W, [(33.23, 46.55), (34.6, 46.55)]),                                                # R104.1 -> C76.1
    # 3V3: U12.3 / C100, R76.1, one In2 via
    ('3V3', 'F', W, [(34.92, 46.9), (34.92, 47.8)]),                                                    # C100.1 - U12.3
    ('3V3', 'F', W, [(34.975, 46.8), (34.975, 41.08), V3['C100']]),
    ('3V3', 'B', W, [V3['C100'], (34.425, 40.83)]),                                                     # R76.1
    ('3V3', 'B', W, [(34.425, 40.55), (34.425, 41.325), V3['IN2']]),
    # GND
    ('GND', 'F', W, [(35.48, 46.9), (35.48, 47.8)]),                                                    # C100.2 - U12.2
    ('GND', 'F', W, [(35.45, 48.0), (35.45, 49.375), G_U12]),
    ('GND', 'B', W, [(34.675, 51.1), G_U12]),                                                           # C93.2
    ('GND', 'B', W, [(30.775, 36.9), G_R70]),                                                           # R70.2
    # camera eFuse control
    ('CAM_FAULT_N', 'F', W, [u1_pin(41), (28.669, 43.0), (30.069, 41.6), V_FLT]),                       # D-S8-07
    ('CAM_FAULT_N', 'B', W, [V_FLT, (32.775, 40.55)]),                                                  # R76.2
    ('CAM_FAULT_N', 'B', W, [(32.775, 40.55), (32.775, 39.85), (33.75, 38.875)]),                       # R77.1
    ('CAM_PWR_EN', 'F', W, [u1_pin(42), (28.6, 42.5), (30.775, 40.325), V_PEN]),
    ('CAM_PWR_EN', 'B', W, [V_PEN, (30.775, 31.5)]),                                                    # R74.1
    ('CAM_EN', 'B', W, [(32.425, 29.9), (32.425, 31.5)]),                                               # R75.1 - R74.2
    ('CAM_EN', 'B', W, [(32.425, 31.5), (32.425, 31.875), (33.55, 33.0), (33.55, 33.75)]),              # U7.2
    ('CAM_DVDT', 'B', W, [(31.655, 33.9), (33.05, 33.9)]),                                              # C70.1 -> U7.1
    ('CAM_FLT_RAW', 'B', W, [(34.05, 35.65), (34.05, 36.925)]),                                         # U7.6 -> R77.2
    ('CAM_ILIM', 'B', W, [(33.55, 35.65), (33.55, 36.0), (32.65, 36.9)]),                               # U7.7 -> R70.1
    ('CAM_ILIM', 'B', W, [(32.425, 36.9), (32.425, 37.45), (31.0, 38.875)]),                            # TP73
    # the translator's camera-side supply
    ('CAM_5V', 'B', W_IN, [(38.85, 50.07), (38.85, 52.65)]),                                            # C75.1 -> U13.1
    ('CAM_5V', 'B', W_IN, [(38.85, 52.65), (40.2, 52.65)]),                                             # C91.1
    ('CAM_IO_3V3', 'F', W, [(35.45, 51.1), V_IO]),                                                      # U12.7
    ('CAM_IO_3V3', 'B', W, [V_IO, (35.45, 52.65), (35.45, 56.22)]),                                     # C92.1
    ('CAM_IO_3V3', 'B', W, [(35.45, 52.65), (34.675, 52.65)]),                                          # C93.1
    ('CAM_IO_3V3', 'B', W, [(35.45, 52.65), (36.3, 52.65)]),                                            # U13.5
    ('CAM_IO_3V3', 'B', W, [(35.45, 56.22), (35.45, 56.55), V_IO2]),
    ('CAM_IO_3V3', 'F', W, [V_IO2, (34.6, 57.9), (33.85, 58.65)]),                                      # TP90 (D-S8-12)
    ('CAM_IO_3V3', 'F', W, [(33.85, 58.65), (33.85, 60.075), (34.275, 60.5)]),                          # R103.1
]
SIGNAL_VIAS = [('CAM_MCU_RX', V_RX1), ('CAM_MCU_RX', V_RX2), ('CAM_UART_OE', V_BOX), ('CAM_UART_OE', V_OE),
               ('CAM_5V_SENSE', V_5V), ('CAM_IO_3V3', V_IO), ('CAM_IO_3V3', V_IO2), ('CAM_FAULT_N', V_FLT),
               ('CAM_PWR_EN', V_PEN)]
PENDING = [G_R70]
PADS = [
    ('C70', '1', 'CAM_DVDT', (31.655, 33.9)), ('C75', '1', 'CAM_5V', (38.5, 50.07)),
    ('C76', '1', 'CAM_5V', (35.29, 46.16)), ('C91', '1', 'CAM_5V', (40.675, 53.3)),
    ('C92', '1', 'CAM_IO_3V3', (35.45, 56.22)), ('C93', '1', 'CAM_IO_3V3', (34.675, 52.65)),
    ('C93', '2', 'GND', (34.675, 51.1)), ('C94', '1', 'CAM_5V_SENSE', (31.6, 45.4)),
    ('C100', '1', '3V3', (34.78, 46.8)), ('C100', '2', 'GND', (35.62, 46.8)),
    ('J9', '3', 'CAM_RX_WIRE', (40.75, 48.825)), ('J9', '4', 'CAM_TX_WIRE', (40.75, 50.075)),
    ('R70', '1', 'CAM_ILIM', (32.425, 36.9)), ('R70', '2', 'GND', (30.775, 36.9)),
    ('R74', '1', 'CAM_PWR_EN', (30.775, 31.5)), ('R74', '2', 'CAM_EN', (32.425, 31.5)),
    ('R75', '1', 'CAM_EN', (32.425, 29.9)), ('R76', '1', '3V3', (34.425, 40.55)),
    ('R76', '2', 'CAM_FAULT_N', (32.775, 40.55)), ('R77', '1', 'CAM_FAULT_N', (34.05, 38.575)),
    ('R77', '2', 'CAM_FLT_RAW', (34.05, 36.925)), ('R78', '2', 'GND', (34.675, 49.2)),
    ('R100', '1', 'CAM_RX_WIRE', (37.5, 46.35)), ('R100', '2', 'CAM_RX_BUFFER', (37.5, 48.0)),
    ('R101', '1', 'CAM_TX_BUFFER', (37.5, 51.1)), ('R101', '2', 'CAM_TX_WIRE', (37.5, 52.75)),
    ('R102', '1', 'CAM_UART_OE', (34.95, 52.775)), ('R103', '1', 'CAM_IO_3V3', (34.275, 60.5)),
    ('R104', '1', 'CAM_5V', (33.23, 46.55)), ('R104', '2', 'CAM_5V_SENSE', (32.37, 46.55)),
    ('R105', '1', 'CAM_5V_SENSE', (32.37, 47.55)),
    ('TP73', '1', 'CAM_ILIM', (30.4, 39.3)), ('TP75', '1', 'CAM_RX_WIRE', (37.65, 44.3)),
    ('TP76', '1', 'CAM_TX_WIRE', (37.5, 55.1)), ('TP90', '1', 'CAM_IO_3V3', (33.85, 58.65)),
    ('TP91', '1', 'CAM_UART_OE', (32.4, 54.4)), ('U1', '31', 'CAM_UART_OE', u1_pin(31)),
    ('U1', '35', 'CAM_5V_SENSE', u1_pin(35)), ('U1', '37', 'CAM_MCU_RX', u1_pin(37)),
    ('U1', '38', 'CAM_MCU_TX', u1_pin(38)), ('U1', '41', 'CAM_FAULT_N', u1_pin(41)),
    ('U1', '42', 'CAM_PWR_EN', u1_pin(42)),
    ('U7', '1', 'CAM_DVDT', (33.05, 33.75)), ('U7', '2', 'CAM_EN', (33.55, 33.75)),
    ('U7', '6', 'CAM_FLT_RAW', (34.05, 35.65)), ('U7', '7', 'CAM_ILIM', (33.55, 35.65)),
    ('U12', '1', 'CAM_RX_BUFFER', (35.95, 48.0)), ('U12', '2', 'GND', (35.45, 48.0)),
    ('U12', '3', '3V3', (34.95, 48.0)), ('U12', '4', 'CAM_MCU_RX', (34.45, 48.0)),
    ('U12', '5', 'CAM_MCU_TX', (34.45, 51.1)), ('U12', '6', 'CAM_UART_OE', (34.95, 51.1)),
    ('U12', '7', 'CAM_IO_3V3', (35.45, 51.1)), ('U12', '8', 'CAM_TX_BUFFER', (35.95, 51.1)),
    ('U13', '1', 'CAM_5V', (38.9, 52.65)), ('U13', '5', 'CAM_IO_3V3', (36.3, 52.65)),
]


def draw(d):
    for net, layer, w, pts in TRACKS:
        d.track(net, layer, w, pts)
    for net, at in SIGNAL_VIAS:
        d.via(net, at, VIA_SIG)
    for at in V3.values():
        d.via('3V3', at, VIA_SIG)
    for at in PENDING:
        d.via('GND', at, VIA_SIG)
