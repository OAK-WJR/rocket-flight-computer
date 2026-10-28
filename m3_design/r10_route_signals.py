"""R10 signal copper, all hand-drawn: the external-port UARTs and IO rails, then every non-critical signal.

Hand-routed (AGENTS 3 critical nets, r10 route_check classes 'uart' and 'power'): GPS_*_MCU and RADIO_*_MCU from U1's
north edge to the port buffers U411 / U421, and the three port IO rails (*_IO_3V3: the TPS70933 output, its capacitors,
its bleed resistor and the buffer's VCCB). The radio pair crosses once (PB12 / PB13 order against U421's pin order):
RADIO_TX_MCU hops under RADIO_RX_MCU on B.Cu, a GND via within 1.5 mm of each layer change (AGENTS 3).
R3 (R10_DECISIONS D-R3-B2 / B3): every layer change of an external-port signal (the *_MCU / *_WIRE / *_BUFFER UART
nets and the *_PWR_EN / *_FAULT_N / *_UART_OE control nets) has a GND via centre within 1.5 mm, drawn here beside it
or, where named, a fan-out GND via of r10_fanout.tsv (C410.2 (32.959, 11.684), U401.11 (27.6, 14.95), U410.2
(29.35, 10.0), D411.2 / D421.2's ESD returns below); every remaining hop crosses other copper.

Every other signal is a deliberate hand-drawn polyline (R10_DECISIONS D-R2-08 / D-R2-09), grouped by cell; the design
aid's earlier frozen table (m3_design/r10_aid/ncroute.py) served only as a sketch of feasible paths.
"""
S, IO = 0.2, 0.3        # signal width; IO rail trunk width (bottom)
# GND return vias beside the port-control layer changes (R10_DECISIONS D-R3-B3; centre-to-centre distances measured on
# the built board): GPS_PWR_EN / GPS_FAULT_N south hop vias (24.5, 31.0) / (26.9, 31.0): 1.26 / 1.26; GPS_PWR_EN north
# hop via (24.5, 16.3): 1.14; RADIO_FAULT_N (32.3, 24.525): 0.68; RADIO_PWR_EN (31.25, 27.35): 1.06 (across RADIO_RX_MCU).
PORT_CONTROL_GND = ((25.7, 30.6), (23.6, 17.0), (32.6, 23.925), (32.0, 28.1))


def uarts(d):
    t, p, via = d.track, d.pad, d.via
    # GPS (USART6): two parallel lanes north from U1.64 / U1.63, one 45 deg diagonal each, into U411's west pins.
    t('GPS_RX_MCU', 'F', S, [p('U1.64'), (22.5, 28.1), (33.2, 17.4), (33.2, 15.05), p('U411.4')])
    t('GPS_TX_MCU', 'F', S, [p('U1.63'), (23.0, 28.35), p('U411.5')])
    # Radio (UART5): RX (PB12, U1.51, east pin) on F.Cu into U421.4 from the west; TX (PB13, U1.52) hops under it.
    t('RADIO_RX_MCU', 'F', S, [p('U1.51'), (29.0, 34.4), (30.0, 33.4), (30.0, 29.35), (33.55, 25.8), p('U421.4')])
    t('RADIO_TX_MCU', 'F', S, [p('U1.52'), (28.5, 32.4)])
    t('RADIO_TX_MCU', 'B', S, [(28.5, 32.4), (30.95, 32.4)])
    t('RADIO_TX_MCU', 'F', S, [(30.95, 32.4), p('U421.5')])
    for at in ((28.5, 32.4), (30.95, 32.4)):
        via('RADIO_TX_MCU', at)
    for at in ((28.5, 31.5), (31.85, 32.4)):          # 0.9 mm from each RADIO_TX_MCU layer change
        via('GND', at)


def io_rails(d):
    t, p, via = d.track, d.pad, d.via
    # GPS / radio (the radio cell is the GPS cell 12 mm forward): LDO output -> its capacitors on B.Cu, the buffer's VCCB
    # through a via under it, and over the port-rail track on F.Cu to the bleed resistor east of it.
    for net, dy in (('GPS_IO_3V3', 0.0), ('RADIO_IO_3V3', 12.0)):
        ldo, cin, cbulk, bleed, buf = (('U412', 'C443', 'C442', 'R443', 'U411') if dy == 0 else
                                        ('U422', 'C453', 'C452', 'R453', 'U421'))
        t(net, 'B', IO, [p(f'{ldo}.5'), p(f'{cin}.1')])
        t(net, 'B', IO, [p(f'{cin}.1'), (34.675, 22.525 + dy), p(f'{cbulk}.1')])
        # VCCB leaves its pad 0.05 mm east of centre on x 35.5 to the via, 0.55 mm from the *_UART_OE run at x 34.95,
        # so the via's In1 antipad (r 0.40) clears that run's copper edge by 0.05 mm (K-reference, D-R3-xx); the bleed
        # run continues straight south 0.1 mm inside the via's ring onto R9's 45 deg line under R441 / R451.
        p(f'{buf}.7', at=(35.45, 16.9 + dy))
        t(net, 'F', S, [(35.5, 16.9 + dy), (35.5, 17.7 + dy)])
        via(net, (35.5, 17.7 + dy))
        t(net, 'B', IO, [(35.5, 17.7 + dy), (35.5, 18.45 + dy)])
        t(net, 'F', S, [(35.5, 17.7 + dy), (35.5, 17.8 + dy), (36.9, 19.2 + dy), (40.0, 19.2 + dy), (42.0, 17.2 + dy)])
        via(net, (42.0, 17.2 + dy))
        t(net, 'B', IO, [(42.0, 17.2 + dy), p(f'{bleed}.1')])
    # Camera: U13 -> C93 -> C92 -> R103 on B.Cu, U12's VCCB through a via under it.
    net = 'CAM_IO_3V3'
    t(net, 'B', IO, [p('U13.5'), (35.6, 42.45), p('C93.1')])        # node at the VCCB via: C93 is U12.7's bypass (D-R2-11)
    t(net, 'B', IO, [p('C93.1'), (34.675, 45.245), p('C92.1')])
    t(net, 'B', IO, [p('C92.1'), (40.695, 46.02), p('R103.1')])
    t(net, 'F', S, [p('U12.7'), (35.45, 41.75), (35.6, 41.9)])
    via(net, (35.6, 41.9))
    t(net, 'B', IO, [(35.6, 41.9), (35.6, 42.45)])


def port_wires(d):
    """GPS / radio connector side: the buffer orders RX above TX, the connector TX above RX, so the wires cross once.
    RX runs under the cell on B.Cu (x 38.8) between two vias (under the TX wire's ESD diode D410 / D420 and its run to
    J410.3 / J420.3); TX stays on F.Cu west of the ESD diodes (x 38.25)."""
    t, p, via = d.track, d.pad, d.via
    for pre, r_rx, r_tx, d_tx, d_rx, j, dy in (('GPS', 'R440', 'R441', 'D410', 'D411', 'J410', 0.0),
                                               ('RADIO', 'R450', 'R451', 'D420', 'D421', 'J420', 12.0)):
        tx, rx = f'{pre}_TX_WIRE', f'{pre}_RX_WIRE'
        t(tx, 'F', S, [p(f'{r_tx}.2'), (38.25, 18.55 + dy), (38.25, 15.325 + dy), p(f'{d_tx}.1')])
        t(tx, 'F', S, [p(f'{d_tx}.1'), (40.6, 14.775 + dy), p(f'{j}.3')])
        t(rx, 'F', S, [p(f'{r_rx}.1'), (38.8, 12.15 + dy)])
        t(rx, 'B', S, [(38.8, 12.15 + dy), (38.8, 16.95 + dy)])
        t(rx, 'F', S, [(38.8, 16.95 + dy), p(f'{d_rx}.1')])
        t(rx, 'F', S, [p(f'{d_rx}.1'), (40.35, 16.275 + dy), p(f'{j}.4')])
        for at in ((38.8, 12.15 + dy), (38.8, 16.95 + dy)):
            via(rx, at)
        via('GND', (39.4, 12.45 + dy))       # 0.67 mm from the north hop via (the south one has D411.2's / D421.2's)


def camera_control(d):
    """U1's east pins to the camera buffer U12 and switch U402 (R10_DECISIONS D-R3-B2). U1 orders FAULT_N, PWR_EN, OE,
    TX, RX from the top; U12's west face orders RX (pin 4, top row), TX (pin 5, bottom row). OE enters U12.6 from
    between the pad rows (west of TX's pin 5 and under RX's pin 4), so OE and TX stay on F.Cu without crossing; only
    RX, the southern pin with the northern pad, crosses OE and TX: one B.Cu hop in the channel between USB_LIMITED
    (x 31.8) and R431 / C93. The enable drops to B.Cu once beside its pin (its pull-down R431 and U402.3 are bottom
    parts); GND vias G1 / G3 sit within 1.5 mm of the hop's and the enable's layer changes (AGENTS 3)."""
    t, p, via = d.track, d.pad, d.via
    t('CAM_MCU_RX', 'F', S, [p('U1.37'), (32.3, 43.5), (32.5, 43.7)])
    t('CAM_MCU_RX', 'B', S, [(32.5, 43.7), (32.5, 40.35), (33.65, 39.2)])
    t('CAM_MCU_RX', 'F', S, [(33.65, 39.2), (34.45, 38.4), p('U12.4')])
    for at in ((32.5, 43.7), (33.65, 39.2)):
        via('CAM_MCU_RX', at)
    t('CAM_MCU_TX', 'F', S, [p('U1.38'), (34.1, 43.0), (34.1, 41.25), p('U12.5')])
    t('CAM_UART_OE', 'F', S, [p('U12.6'), p('R102.1')])
    t('CAM_UART_OE', 'F', S, [p('U1.39'), (33.7, 42.5), (33.7, 40.2), (34.95, 40.2), p('U12.6')])
    t('CAM_PWR_EN', 'F', S, [p('U1.41'), (33.15, 41.5)])
    via('CAM_PWR_EN', (33.15, 41.5))
    t('CAM_PWR_EN', 'B', S, [(33.15, 41.5), (33.9, 40.75), (33.9, 40.1), (34.6, 40.1), p('R431.1')])
    t('CAM_PWR_EN', 'B', S, [p('R431.1'), (35.675, 38.15), p('U402.3')])
    for at in ((33.2, 43.85), (33.15, 40.55), (33.1, 35.825)):
        via('GND', at)          # RX south hop via 0.72 mm; PWR_EN 0.95 and RX north hop 1.44; FAULT_N's via 1.28
    t('CAM_FAULT_N', 'F', S, [p('U1.42'), (32.6, 41.0), p('R432.1')])
    t('CAM_FAULT_N', 'F', S, [p('R432.1'), (33.9, 37.525), (33.9, 36.825)])
    via('CAM_FAULT_N', (33.9, 36.825))
    t('CAM_FAULT_N', 'B', S, [(33.9, 36.825), (37.575, 36.825), p('U402.4')])


def gps_oe(d):
    """GPS_UART_OE (PD15, U1.62) in the strip south-east of the GPS UART lanes, under C420 to the pull-down R442."""
    t, p = d.track, d.pad
    t('GPS_UART_OE', 'F', S, [p('U1.62'), (23.5, 28.65), (28.1, 24.05), (31.6, 24.05), (32.8, 22.85), (32.8, 20.725),
                               p('R442.1')])
    t('GPS_UART_OE', 'F', S, [p('U411.6'), p('R442.1')])


def gnd_joins(d):
    """GND pads the signal copper boxes in, joined by hand (the fan-out aid runs after this family)."""
    t, p, via = d.track, d.pad, d.via
    t('GND', 'B', S, [(21.28, 53.65), (21.82, 53.65)])           # R63's GND pad onto C14's GND strap (core table)
    t('GND', 'F', S, [p('U1.49'), (28.75, 37.5)])                # west between pin 50's / 48's vias into the pour
    t('GND', 'F', S, [p('U12.2'), (35.45, 36.6)])                # into C100's GND pad (its own via)
    # C93 (U13's output capacitor) returns straight to U13's GND pin: a short strap between the two pads, east under
    # U12 and down the gap between U13's pin columns (its pad is boxed in on three sides, D-R2-09).
    t('GND', 'B', IO, [p('C93.2'), (37.0, 40.9), (37.6, 41.5), (37.6, 43.4), p('U13.2')])
    for d_gnd, y in (('D411.2', 15.625), ('D421.2', 27.625)):     # ESD returns boxed in by the port wires
        t('GND', 'F', S, [p(d_gnd), (39.4, y)])           # hole >= 0.1 mm off the pad's mask, ring off its paste (D-R2-11)
        via('GND', (39.4, y))


def servo_lanes(d):
    """SERVO1-4_MCU (U1.22-25, PA0-PA3) as one F.Cu bundle (R10_DECISIONS D-R2-09): straight south from the pins,
    one staggered 45 deg turn (0.6 / 0.7 / 0.6 mm between the diagonals), straight south again over the bottom sense
    rows to one via each at the head of the servo cell (SERVO1's lower, beside R122, so no bottom GND pour finger is
    left between it and TP120's 1 mm clearance). The diagonals run parallel to the two sense lanes east of them."""
    t, p, via = d.track, d.pad, d.via
    for net, pin, turn, x, end in (('SERVO1_MCU', 'U1.22', 54.8, 20.4, 68.6), ('SERVO2_MCU', 'U1.23', 55.15, 22.7, 66.2),
                                   ('SERVO3_MCU', 'U1.24', 55.65, 23.3, 66.7), ('SERVO4_MCU', 'U1.25', 56.0, 25.7, 66.4)):
        a = p(pin)
        t(net, 'F', S, [a, (a[0], turn), (x, turn + a[0] - x), (x, end)])
        via(net, (x, end))


def servo_cell(d):
    """Bottom servo cell: D121 (turned 90 deg) has S2 / S1 in its west column and S3 / S4 in its east column, so the
    inner lanes S2 and S3 run down the channel between the columns (tapping their pins and pull-downs from inside) and
    the outer lanes S1 and S4 pass outside and tap the south pins; each lane then ends in its 1 k resistor's MCU pad.
    Every lane enters from its via straight south (D-R2-09: R157 turned so its GND pad sits east of the S4 lane).
    The clamp's GND and 3V3 pins strap out sideways to one via each."""
    t, p, via = d.track, d.pad, d.via
    t('SERVO1_MCU', 'B', S, [(20.4, 68.6), p('R154.1')])
    # R150-R153 and D121 sit 1.15 / 0.6 mm aft of D-R2-07's spots (M-6: 1.5 mm from J122's pins, D-R2-12).
    t('SERVO1_MCU', 'B', S, [p('R154.1'), (20.4, 73.04), p('R150.1')])
    t('SERVO1_MCU', 'B', S, [(20.4, 72.55), p('D121.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 66.2), (22.7, 73.28), p('R151.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 69.03), p('R155.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 70.65), p('D121.3')])
    t('SERVO3_MCU', 'B', S, [(23.3, 66.7), (23.3, 73.28), p('R152.1')])
    t('SERVO3_MCU', 'B', S, [(23.3, 69.03), p('R156.1')])
    t('SERVO3_MCU', 'B', S, [(23.3, 70.65), p('D121.4')])
    t('SERVO4_MCU', 'B', S, [(25.7, 66.4), p('R157.1')])
    t('SERVO4_MCU', 'B', S, [p('R157.1'), (25.7, 73.14), p('R153.1')])
    t('SERVO4_MCU', 'B', S, [(25.7, 72.55), p('D121.6')])
    t('GND', 'B', IO, [p('D121.2'), (21.05, 71.6)])                # hole / ring clear of R123.2's mask / paste (top)
    via('GND', (21.05, 71.6))
    t('3V3', 'B', IO, [p('D121.5'), (25.05, 71.6)])
    via('3V3', (25.05, 71.6))


def east_lanes(d):
    """U1's east-side status and supply-sense lines (R10_DECISIONS D-R2-09). The pyro sense lanes (pyro family) leave
    U1.33 / U1.34 through R170 / R172 and run south at x 34.4 / 35.1. The three lines from U1.28-30 escape straight
    east inside them, drop through one via each east of the USB_LIMITED run and cross under the sense lanes on B.Cu:
    VLOGIC_SENSE (PA6) and BAT_FAULT_N (PA5) straight east under C92's body (between its pads), to the VLOGIC divider
    and to BAT_FAULT_N's F.Cu column x 37.0; LOGIC_SOURCE_ST (PA4) straight south to U11.9, taking its pull-up R91 and
    test pad TP87 by short stubs. BAT_FAULT_N's column takes its pull-up R89 and test pad TP85, passes C82 and runs
    under C84's body (between its pads) to a via, then straight south on B.Cu between C9 and the VLOGIC spine into
    U9.4."""
    t, p, via = d.track, d.pad, d.via
    # VLOGIC_SENSE (PA6): divider R61 / C60 / R60 hangs off a short lane x 38.66, R60's VLOGIC pad on the spine.
    t('VLOGIC_SENSE', 'F', S, [p('U1.30'), (33.5, 47.0)])
    via('VLOGIC_SENSE', (33.5, 47.0))
    t('VLOGIC_SENSE', 'B', S, [(33.5, 47.0), (38.66, 47.0), p('R61.1')])
    t('VLOGIC_SENSE', 'B', S, [p('R61.1'), p('C60.1')])
    t('VLOGIC_SENSE', 'B', S, [p('C60.1'), p('R60.2')])
    # BAT_FAULT_N (PA5)
    t('BAT_FAULT_N', 'F', S, [p('U1.29'), (33.2, 47.5), (33.6, 47.9)])
    via('BAT_FAULT_N', (33.6, 47.9))
    t('BAT_FAULT_N', 'B', S, [(33.6, 47.9), (37.0, 47.9)])
    via('BAT_FAULT_N', (37.0, 47.9))
    t('BAT_FAULT_N', 'F', S, [(37.0, 47.9), p('R89.2')])
    t('BAT_FAULT_N', 'F', S, [p('R89.2'), p('TP85.1')])
    t('BAT_FAULT_N', 'F', S, [p('TP85.1'), (37.0, 74.0)])
    via('BAT_FAULT_N', (37.0, 74.0))
    t('BAT_FAULT_N', 'B', S, [(37.0, 74.0), (37.0, 78.9), (38.1, 78.9)])
    # LOGIC_SOURCE_ST (PA4)
    t('LOGIC_SOURCE_ST', 'F', S, [p('U1.28'), (32.65, 48.0), (32.95, 48.3)])
    via('LOGIC_SOURCE_ST', (32.95, 48.3))
    t('LOGIC_SOURCE_ST', 'B', S, [(32.95, 48.3), (32.95, 57.0), (33.8, 57.85), p('U11.9')])
    t('LOGIC_SOURCE_ST', 'B', S, [(32.95, 54.85), p('R91.2')])
    t('LOGIC_SOURCE_ST', 'B', S, [(32.95, 56.6), p('TP87.1')])


def cam_sense(d):
    """CAM_5V_SENSE (PB1, U1.35): straight east from the pin above the sense resistors, one 45 deg rise between the
    camera UART hop vias, east under R102's body (between its pads) and straight south into the camera-supply
    divider column R104 / R105 / C94 (R10_DECISIONS D-R2-09)."""
    t, p = d.track, d.pad
    t('CAM_5V_SENSE', 'F', S, [p('U1.35'), (33.35, 44.5), (34.45, 43.4), (39.57, 43.4), p('R104.2')])
    t('CAM_5V_SENSE', 'F', S, [p('R104.2'), p('R105.1')])
    t('CAM_5V_SENSE', 'F', S, [p('R105.1'), p('C94.1')])


def south_sense(d):
    """V3V3_SENSE (PC3_C, U1.18): one via under the pin, one 45 deg run south-west on B.Cu and into the divider node
    R62.2 / R63.1 from the south."""
    t, p, via = d.track, d.pad, d.via
    t('V3V3_SENSE', 'F', S, [p('U1.18'), (25.5, 51.75)])
    via('V3V3_SENSE', (25.5, 51.75))                      # ring clear of U1.18's paste (D87)
    t('V3V3_SENSE', 'B', S, [(25.5, 51.75), (22.7, 54.55), (20.42, 54.55), p('R63.1')])
    t('V3V3_SENSE', 'B', S, [p('R62.2'), p('R63.1')])


def port_links(d):
    """Port buffer to series-resistor links (one straight pad-to-pad run each) and the camera wire side: the buffer
    orders RX above TX, J9 TX above RX, so CAM_RX_WIRE steps east above D401 and CAM_TX_WIRE runs west of D400."""
    t, p = d.track, d.pad
    for net, a, b in (('GPS_RX_BUFFER', 'R440.2', 'U411.1'), ('GPS_TX_BUFFER', 'R441.1', 'U411.8'),
                      ('RADIO_RX_BUFFER', 'U421.1', 'R450.2'), ('RADIO_TX_BUFFER', 'U421.8', 'R451.1'),
                      ('CAM_RX_BUFFER', 'U12.1', 'R100.2'), ('CAM_TX_BUFFER', 'R101.1', 'U12.8')):
        t(net, 'F', S, [p(a), p(b)])
    t('CAM_RX_WIRE', 'F', S, [p('R100.1'), (39.4, 36.15), (39.4, 38.775), (40.6, 38.775), p('J9.3')])
    t('CAM_RX_WIRE', 'F', S, [(39.4, 38.775), p('D401.1')])
    t('CAM_TX_WIRE', 'F', S, [p('R101.2'), (38.8, 42.55), p('D400.1')])
    t('CAM_TX_WIRE', 'F', S, [p('D400.1'), (40.35, 40.275), p('J9.4')])


def port_control(d):
    """GPS / radio power-switch enables and fault flags from U1's north edge (pins 55 / 56 / 57 / 61) and the radio
    UART OE from its east edge (R10_DECISIONS D-R3-B3). Each GND via named below sits within 1.5 mm (centre to centre)
    of the layer changes it serves (AGENTS 3; these nets are critical in route_check r10).
    Radio: RADIO_FAULT_N north through its pull-up R422 and one 45 deg run to a via over U420.4; RADIO_PWR_EN (U1.55
    is west of U1.56 while U420.3 is west of U420.4, so the pair crosses once) runs a parallel 45 deg F.Cu lane between
    RADIO_FAULT_N's and RADIO_RX_MCU's to one via between U420's pin columns and reaches U420.3 from the east on B.Cu,
    wholly over the In2 PORT_4V8 region (no In2 split crossed).
    GPS: the pair crosses under the GPS UART lanes (U1.62-64 are west of U1.57 / U1.61, U411 east of U410) on B.Cu
    lanes x 24.5 / 26.9 over In2 3V3, surfaces on F.Cu north of the lanes inside the 3V3 region (y >= 15.8), crosses
    over U401's bottom cell (U401.8-10, C408, PORT_5V3 / PORT_LDO_SS copper) on F.Cu and drops beside U410: three
    vias each, every hop crossing other copper (the lanes; U401's cell).
    K-reference (D-R3-xx): each F.Cu lane keeps >= 0.55 mm (centre) from other nets' vias, so their In1 antipads
    (r 0.40) clear its copper edge: RADIO_PWR_EN x 27.95 beside RADIO_TX_MCU's via (28.5, 32.4), RADIO_FAULT_N x 27.45
    (into R422.1 0.05 mm east of its centre) beside GPS_FAULT_N's via (26.9, 31.0); each B.Cu run lies wholly over one
    In2 region (r10_route_power)."""
    t, p, via = d.track, d.pad, d.via
    # radio
    p('R422.1', at=(27.4, 28.425))
    t('RADIO_FAULT_N', 'F', S, [p('U1.56'), (26.5, 34.15), (27.45, 33.2), (27.45, 28.425)])
    t('RADIO_FAULT_N', 'F', S, [p('R422.1'), (28.4, 28.425), (32.3, 24.525)])
    via('RADIO_FAULT_N', (32.3, 24.525))
    t('RADIO_FAULT_N', 'B', S, [(32.3, 24.525), p('U420.4')])
    t('RADIO_PWR_EN', 'F', S, [p('U1.55'), (27.0, 34.35), (27.95, 33.4), (27.95, 30.65), (31.25, 27.35)])
    via('RADIO_PWR_EN', (31.25, 27.35))
    t('RADIO_PWR_EN', 'B', S, [(31.25, 27.35), (31.25, 25.45), p('U420.3')])
    t('RADIO_UART_OE', 'F', S, [p('U421.6'), p('R452.1')])
    t('RADIO_UART_OE', 'F', S, [p('R452.1'), (31.75, 33.775), (31.75, 39.5), p('U1.45')])
    # GPS
    t('GPS_FAULT_N', 'F', S, [p('R412.1'), p('U1.57')])
    t('GPS_FAULT_N', 'F', S, [p('R412.1'), (26.9, 32.525), (26.9, 31.0)])
    via('GPS_FAULT_N', (26.9, 31.0))
    t('GPS_FAULT_N', 'B', S, [(26.9, 31.0), (26.9, 15.825)])
    via('GPS_FAULT_N', (26.9, 15.825))
    t('GPS_FAULT_N', 'F', S, [(26.9, 15.825), (26.9, 14.725), (30.2, 11.425), (31.6, 11.425)])
    via('GPS_FAULT_N', (31.6, 11.425))
    t('GPS_FAULT_N', 'B', S, [(31.6, 11.425), (31.6, 9.05), p('U410.4')])
    t('GPS_PWR_EN', 'F', S, [p('U1.61'), (24.0, 33.45), (24.5, 32.95), (24.5, 31.0)])
    via('GPS_PWR_EN', (24.5, 31.0))
    t('GPS_PWR_EN', 'B', S, [(24.5, 31.0), (24.5, 16.3)])
    via('GPS_PWR_EN', (24.5, 16.3))
    t('GPS_PWR_EN', 'F', S, [(24.5, 16.3), (24.5, 14.85), (28.1, 11.25), (28.1, 9.8)])
    via('GPS_PWR_EN', (28.1, 9.8))
    t('GPS_PWR_EN', 'B', S, [(28.1, 9.8), (28.85, 9.05), p('U410.3')])
    for at in PORT_CONTROL_GND:
        via('GND', at)


def leds(d):
    """Status LEDs west of U1: each series resistor straight to its LED, U1's pins to the resistors by one bend."""
    t, p = d.track, d.pad
    t('LED_RED_A', 'F', S, [p('R32.2'), (11.9, 39.65), p('LED1.2')])
    t('LED_YEL_A', 'F', S, [p('LED2.1'), p('R33.2')])
    t('LED_RED', 'F', S, [p('R32.1'), (14.0, 40.75), (14.0, 42.0), p('U1.86')])
    t('LED_YEL', 'F', S, [p('U1.88'), (14.3, 43.0), p('R33.1')])


def buzzer(d):
    """Buzzer: BUZZ_DRV (PC14, U1.8, south edge) north under U1 on F.Cu, across USB_LIMITED by one F.Cu run beside
    the USB pair, then straight north on B.Cu to the gate resistor R162. BUZZ_OUT (D-R2-09: Q123 shifted 0.25 mm east
    so its drain lines up under LS120.2) is one via under LS120.2 on Q123's drain column, the clamp D123 tapped by one
    45 deg run."""
    t, p, via = d.track, d.pad, d.via
    t('BUZZ_DRV', 'F', S, [p('U1.8'), (20.5, 48.75), (21.8, 47.45), (21.8, 37.95), (23.1, 36.65)])
    via('BUZZ_DRV', (23.1, 36.65))
    t('BUZZ_DRV', 'B', S, [(23.1, 36.65), (20.3, 33.85)])
    via('BUZZ_DRV', (20.3, 33.85))
    t('BUZZ_DRV', 'F', S, [(20.3, 33.85), (20.3, 33.05), (17.8, 30.55)])
    via('BUZZ_DRV', (17.8, 30.55))
    t('BUZZ_DRV', 'B', S, [(17.8, 30.55), (16.8, 29.55), (16.8, 18.85), p('R162.1')])
    # R163's pull-down lead enters R162.2 on its axis from the north and ends at its centre; Q123's gate lead runs
    # straight west on Q123.1's axis and tees onto it (R10_DECISIONS D-R3-B5).
    t('BUZZ_G', 'B', S, [p('R163.1'), (18.1, 17.23), p('R162.2')])
    t('BUZZ_G', 'B', S, [p('Q123.1'), (18.1, 17.95)])
    t('BUZZ_OUT', 'F', S, [p('LS120.2'), (21.85, 17.95)])
    via('BUZZ_OUT', (21.85, 17.95))
    t('BUZZ_OUT', 'B', S, [p('Q123.3'), (21.85, 17.95), (21.85, 18.78), p('D123.2')])


def pullpin(d):
    """Pull-pin: PULLPIN (PC13, U1.7) north under U1 on F.Cu beside BUZZ_DRV, one 45 deg run parallel to QSPI_IO2's
    and west between the QSPI_IO2 and GND vias at U3's north-west corner to one via west of U3's pad column
    (R10_DECISIONS D-R3-B4: no copper between U3's pads; 0.63 mm from U3.3, 0.19 mm from QSPI_IO2's via), then west on
    B.Cu south of USB_FAULT_N, up the board's west edge between J3's shell tabs (x 4.15: 1.01 mm from J3.4, 1.02 mm
    from J3.3) to the clamp D122 and the input filter C160 / R160 / R161 at J123; J123.1 reaches R160 by one via."""
    t, p, via = d.track, d.pad, d.via
    t('PULLPIN', 'F', S, [(20.05, 51.0), (20.05, 46.2), (21.4, 44.85), (21.4, 43.4), (17.93, 39.93), (17.25, 39.93)])
    via('PULLPIN', (17.25, 39.93))
    t('PULLPIN', 'B', S, [(17.25, 39.93), (11.8, 39.93), (10.8, 38.93), (10.8, 37.55), (4.15, 30.9), (4.15, 23.85),
                          p('D122.3')])
    t('PULLPIN', 'B', S, [p('D122.3'), (11.0, 13.58), p('C160.1')])
    t('PULLPIN', 'B', S, [p('C160.1'), p('R160.2')])
    t('PULLPIN', 'B', S, [p('R160.2'), (13.0, 11.43), p('R161.2')])
    t('PULLPIN_EXT', 'F', S, [p('J123.1'), (8.375, 14.45)])
    via('PULLPIN_EXT', (8.375, 14.45))
    t('PULLPIN_EXT', 'B', S, [(8.375, 14.45), (8.375, 10.57), p('R160.1')])


def servo_out(d):
    """Series resistors R150-R153 straight up into J122's signal row (2.54 mm pitch, one column each)."""
    for i, pin in ((1, 1), (2, 4), (3, 7), (4, 10)):
        d.track(f'SERVO{i}_OUT', 'B', S, [d.pad(f'J122.{pin}'), d.pad(f'R{149 + i}.2')])


def draw(d):
    uarts(d)
    io_rails(d)
    port_wires(d)
    camera_control(d)
    gps_oe(d)
    servo_lanes(d)
    servo_cell(d)
    east_lanes(d)
    south_sense(d)
    cam_sense(d)
    port_links(d)
    port_control(d)
    leds(d)
    buzzer(d)
    pullpin(d)
    servo_out(d)
    gnd_joins(d)
