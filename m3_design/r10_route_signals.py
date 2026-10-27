"""R10 signal copper: the external-port UARTs and IO rails by hand, the other signals from a frozen table.

Hand-routed (AGENTS 3 critical nets, r10 route_check classes 'uart' and 'power'): GPS_*_MCU and RADIO_*_MCU from U1's
north edge to the port buffers U411 / U421, and the three port IO rails (*_IO_3V3: the TPS70933 output, its capacitors,
its bleed resistor and the buffer's VCCB). The radio pair crosses once (PB12 / PB13 order against U421's pin order):
RADIO_TX_MCU hops under RADIO_RX_MCU on B.Cu, a GND via within 1.5 mm of each layer change (AGENTS 3).

AUTO (below the marker) is the non-critical signal table frozen from the design aid m3_design/r10_signal_aid.py
(R10_DECISIONS D-R2-04, D-R2-07): explicit polylines and vias, drawn without search.
"""
S, IO = 0.2, 0.3        # signal width; IO rail trunk width (bottom)


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
        t(net, 'F', S, [p(f'{buf}.7'), (35.45, 17.75 + dy)])
        via(net, (35.45, 17.75 + dy))
        t(net, 'B', IO, [(35.45, 17.75 + dy), (35.45, 18.45 + dy)])
        t(net, 'F', S, [(35.45, 17.75 + dy), (35.95, 18.25 + dy), (35.95, 19.4 + dy), (41.6, 19.4 + dy), (42.0, 19.0 + dy),
                        (42.0, 17.2 + dy)])
        via(net, (42.0, 17.2 + dy))
        t(net, 'B', IO, [(42.0, 17.2 + dy), p(f'{bleed}.1')])
    # Camera: U13 -> C93 -> C92 -> R103 on B.Cu, U12's VCCB through a via under it.
    net = 'CAM_IO_3V3'
    t(net, 'B', IO, [p('U13.5'), p('C93.1')])
    t(net, 'B', IO, [p('C93.1'), (34.675, 45.245), p('C92.1')])
    t(net, 'B', IO, [p('C92.1'), (40.695, 46.02), p('R103.1')])
    t(net, 'F', S, [p('U12.7'), (35.45, 41.75), (35.6, 41.9)])
    via(net, (35.6, 41.9))
    t(net, 'B', IO, [(35.6, 41.9), (35.6, 42.45)])


def port_wires(d):
    """GPS / radio connector side: the buffer orders RX above TX, the connector TX above RX, so the wires cross once.
    RX runs under the cell on B.Cu (x 38.8) between two vias; TX stays on F.Cu west of the ESD diodes (x 38.25)."""
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


def camera_control(d):
    """U1's east pins to the camera buffer U12 and switch U402. The buffer orders RX above TX and OE below both while
    U1 orders OE, TX, RX from the top, so RX and TX each take one short B.Cu hop east of USB_LIMITED; the switch enable
    reaches its pull-down R431 on B.Cu through one via between R431 and C93."""
    t, p, via = d.track, d.pad, d.via
    t('CAM_MCU_RX', 'F', S, [p('U1.37'), (32.55, 43.5), (32.95, 43.9)])
    t('CAM_MCU_RX', 'B', S, [(32.95, 43.9), (32.95, 39.8), (33.55, 39.2)])
    t('CAM_MCU_RX', 'F', S, [(33.55, 39.2), (34.45, 38.3), p('U12.4')])
    t('CAM_MCU_TX', 'F', S, [p('U1.38'), (33.25, 43.0), (33.55, 43.3)])
    t('CAM_MCU_TX', 'B', S, [(33.55, 43.3), (33.55, 41.55), (33.75, 41.35)])
    t('CAM_MCU_TX', 'F', S, [(33.75, 41.35), (34.2, 40.9), p('U12.5')])
    for net, at in (('CAM_MCU_RX', (32.95, 43.9)), ('CAM_MCU_RX', (33.55, 39.2)),
                    ('CAM_MCU_TX', (33.55, 43.3)), ('CAM_MCU_TX', (33.75, 41.35))):
        via(net, at)
    t('CAM_UART_OE', 'F', S, [p('U12.6'), p('R102.1')])
    t('CAM_UART_OE', 'F', S, [p('U1.39'), (34.95, 42.5)])                    # square T onto U12.6 -> R102.1
    t('CAM_PWR_EN', 'F', S, [p('U1.41'), (32.75, 41.5), (34.25, 40.0)])
    via('CAM_PWR_EN', (34.25, 40.0))
    t('CAM_PWR_EN', 'B', S, [(34.25, 40.0), (34.6, 40.0), p('R431.1')])
    t('CAM_PWR_EN', 'B', S, [p('R431.1'), (35.675, 38.15), p('U402.3')])
    t('CAM_FAULT_N', 'F', S, [p('U1.42'), (32.6, 41.0), p('R432.1')])
    t('CAM_FAULT_N', 'F', S, [p('R432.1'), (33.9, 37.525), (33.9, 36.825)])
    via('CAM_FAULT_N', (33.9, 36.825))
    t('CAM_FAULT_N', 'B', S, [(33.9, 36.825), (37.575, 36.825), p('U402.4')])


# ---- AUTO: generated by m3_design/r10_signal_aid.py; do not edit by hand below this line ----
AUTO_TRACKS = []
AUTO_VIAS = []
# ---- end AUTO ----


def draw(d):
    uarts(d)
    io_rails(d)
    port_wires(d)
    camera_control(d)
    for net, layer, pts in AUTO_TRACKS:
        d.track(net, layer, S, [d.pad(p) if isinstance(p, str) else p for p in pts])
    for net, at in AUTO_VIAS:
        d.via(net, at)
