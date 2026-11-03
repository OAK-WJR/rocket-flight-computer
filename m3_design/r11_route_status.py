"""R11 family `status` (stage C3): the status LEDs and the buzzer driver (D-R11-39).

Explicit tables only (D-R11-07). Board mm (x east, y forward from the aft edge, KiCad's y).

LED_RED_A / LED_YEL_A: R32.2 / R33.2 to the LEDs' anodes on F.Cu. Buzzer: BUZZ_G (Q123.1 to R162.2 and R163.1) and
BUZZ_OUT (Q123.3, D123.2 on B.Cu, LS120.2 on F.Cu by one via) on B.Cu beside the parts. The MCU lines LED_RED (U1.B6),
LED_YEL (U1.D6) and BUZZ_DRV (U1.A1 to R162.1) are not drawn: stageC3.md O-C3-3 (LED_RED's only via site, the dog-bone
(24.8, 24.8), closes the In2 3V3 neck beside C6's via under QSPI_NCS's In3 run: check_r11 K-region, Measured).
"""

NETS = ('LED_RED_A', 'LED_YEL_A', 'BUZZ_G', 'BUZZ_OUT')

SIG, SV = 0.1, (0.4, 0.2)
RUNS = (
    ('LED_RED_A', 'F', [('R32', '2'), (22.03, 21.35), (22.23, 21.15)]),                 # ends inside LED1.2
    ('LED_YEL_A', 'F', [('R33', '2'), (26.43, 21.55), (26.13, 21.25)]),                 # ends inside LED2.1
    ('BUZZ_G', 'B', [('Q123', '1'), (43.75, 38.05)]),
    ('BUZZ_G', 'B', [(43.75, 38.05), (44.15, 38.05)]),                                  # ends inside R162.2
    ('BUZZ_G', 'B', [(43.75, 38.05), (43.75, 40.6), (44.25, 41.1)]),                    # ends inside R163.1
    ('BUZZ_OUT', 'B', [('Q123', '3'), (39.6, 39.9), (40.15, 40.45), (42.15, 40.45), (42.45, 40.15)]),
    ('BUZZ_OUT', 'B', [(42.15, 40.45), (42.15, 41.5)]),                                 # ends inside D123.2
    ('BUZZ_OUT', 'F', [(42.45, 40.15), (42.0, 40.6)]),                                  # ends inside LS120.2
)
VIAS = (('BUZZ_OUT', (42.45, 40.15)),)
ENDS = (('LED1', '2', 'LED_RED_A'), ('LED2', '1', 'LED_YEL_A'), ('R162', '2', 'BUZZ_G'),
        ('R163', '1', 'BUZZ_G'), ('D123', '2', 'BUZZ_OUT'), ('LS120', '2', 'BUZZ_OUT'))


def draw(d):
    for net, layer, pts in RUNS:
        d.track(net, layer, SIG, [d.pad(p[0], p[1], net=net) if isinstance(p[0], str) else p for p in pts])
    for net, at in VIAS:
        d.via(net, at, SV)
    for ref, num, net in ENDS:
        d.pad(ref, num, net=net)
