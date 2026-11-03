"""R11 family `ports` (stage C3): the wire side of the three identical GH ports J410 (GPS) / J420 (radio) / J440 (AUX)
and of the camera port J9: pin -> 1 kOhm series resistor (wire side) and the ESD clamp (check_r11 K-ports: the clamp on
the wire side of its resistor within 4.5 mm of track from the pin, its GND pad within 1.0 mm of a GND via), D-R11-37.

Explicit tables only (D-R11-07). Board mm (x east, y forward from the aft edge, KiCad's y).

The three GH ports are one cell translated by the port's centre x0 (J420 12.4, J410 23.0, J440 33.6; pins on F.Cu at
y 44.6, resistors / clamps / caps on B.Cu at the same offsets). Per cell, TX (pin 3, x0 + 0.625) and RX (pin 4,
x0 + 1.875) each leave the pin south on F.Cu to one via, then on B.Cu north to the resistor's wire pad and south to the
clamp's wire pad; TX's via sits west of the cell (x0 + 0.1, the B.Cu run west of R / D), RX's between the two columns
(x0 + 1.25), which leaves the R441-R440 gap north of y 44.6 for the MCU-side TX (stageC3.md O-C3-2). Each clamp's GND pad
has its own GND via 0.625 mm north of it; these are the wire vias' GND partners too (AGENTS section 3, critical UART
nets, <= 1.5 mm).

The MCU sides (U1 -> the resistors' MCU pads) are not drawn: stageC3.md O-C3-1 / O-C3-2.
"""

NETS = ('GPS_TX_WIRE', 'GPS_RX_WIRE', 'RADIO_TX_WIRE', 'RADIO_RX_WIRE', 'AUX_TX_WIRE', 'AUX_RX_WIRE', 'CAM_TX_WIRE',
        'CAM_RX_WIRE')

SIG = 0.1
SV, PV = (0.4, 0.2), (0.45, 0.25)
GH = (('J420', 12.4, 'RADIO', 'R451', 'R450', 'D420', 'D421'),
      ('J410', 23.0, 'GPS', 'R441', 'R440', 'D410', 'D411'),
      ('J440', 33.6, 'AUX', 'R471', 'R470', 'D440', 'D441'))


def gh_cell(d, ref, x0, port, r_tx, r_rx, d_tx, d_rx):
    t, p, v = d.track, d.pad, d.via
    tx, rx = f'{port}_TX_WIRE', f'{port}_RX_WIRE'
    xt, xr = round(x0 + 0.625, 4), round(x0 + 1.875, 4)
    vt, vr = (round(x0 + 0.1, 4), 45.9), (round(x0 + 1.25, 4), 45.9)
    # TX: pin 3 -> via west of the cell; B.Cu north into the resistor's wire pad, south and east into the clamp
    t(tx, 'F', SIG, [p(ref, '3', net=tx), (xt, 45.375), vt])
    v(tx, vt, SV)
    t(tx, 'B', SIG, [vt, (vt[0], 44.5), (round(x0 + 0.57, 4), 44.03)])                 # ends inside the R's wire pad
    p(r_tx, '2', net=tx)
    t(tx, 'B', SIG, [vt, (vt[0], 47.4), (round(x0 + 0.425, 4), 47.725)])             # ends inside the clamp's wire pad
    p(d_tx, '1', net=tx)
    # RX: pin 4 -> via between the columns; B.Cu north-east into the resistor's wire pad, south and east into the clamp
    t(rx, 'F', SIG, [p(ref, '4', net=rx), (xr, 45.275), vr])
    v(rx, vr, SV)
    t(rx, 'B', SIG, [vr, (vr[0], 45.3), (round(x0 + 1.73, 4), 44.82)])                 # ends inside the R's wire pad
    p(r_rx, '1', net=rx)
    t(rx, 'B', SIG, [vr, (vr[0], 47.35), (round(x0 + 1.625, 4), 47.725)])            # ends inside the clamp's wire pad
    p(d_rx, '1', net=rx)
    # the clamps' GND pads, each to its own GND via (K-ports: <= 1.0 mm of track)
    for dref, x in ((d_tx, xt), (d_rx, xr)):
        t('GND', 'B', 0.2, [p(dref, '2', net='GND'), (x, 46.45)])
        v('GND', (x, 46.45), PV)


def draw(d):
    for cell in GH:
        gh_cell(d, *cell)
    cam(d)


# J9 (camera, aft edge, rotation 180: pins on F.Cu at y 5.4, housing toward the edge). CAM_RX_WIRE: J9.5 -> via under
# the housing -> B.Cu to D401.1 (clamp, west) and R100.1 (east). CAM_TX_WIRE: J9.6 -> via -> D400.1 (west) and, north of
# the clamps and R100 along y 0.6, into R101.2 from the south-west (R101's MCU-side pad is north of it). Four GND
# vias: the two clamps' (K-ports) and the two wire vias' partners (<= 1.5 mm).
V_CTX, V_CRX = (29.675, 3.6), (30.925, 3.6)
CAM_GND = ((28.75, 1.05), (30.2, 1.05), (29.0, 4.5), (31.55, 3.6))


def cam(d):
    t, p, v = d.track, d.pad, d.via
    t('CAM_RX_WIRE', 'F', SIG, [p('J9', '5', net='CAM_RX_WIRE'), V_CRX])
    v('CAM_RX_WIRE', V_CRX, SV)
    t('CAM_RX_WIRE', 'B', SIG, [V_CRX, (30.2, 2.875), p('D401', '1', net='CAM_RX_WIRE')])
    t('CAM_RX_WIRE', 'B', SIG, [V_CRX, (31.6, 2.925), p('R100', '1', net='CAM_RX_WIRE')])
    t('CAM_TX_WIRE', 'F', SIG, [p('J9', '6', net='CAM_TX_WIRE'), V_CTX])
    v('CAM_TX_WIRE', V_CTX, SV)
    t('CAM_TX_WIRE', 'B', SIG, [V_CTX, (29.0, 3.6), (28.6, 3.2), p('D400', '1', net='CAM_TX_WIRE')])
    t('CAM_TX_WIRE', 'B', SIG, [V_CTX, (29.675, 0.95), (30.025, 0.6), (32.0, 0.6), (32.97, 1.57)])     # south of the clamps; ends inside R101.2
    p('R101', '2', net='CAM_TX_WIRE')
    t('GND', 'B', 0.2, [p('D400', '2', net='GND'), (28.6, 1.2), (28.75, 1.05)])
    t('GND', 'B', 0.2, [p('D401', '2', net='GND'), (30.2, 1.05)])
    for at in CAM_GND:
        v('GND', at, PV)
