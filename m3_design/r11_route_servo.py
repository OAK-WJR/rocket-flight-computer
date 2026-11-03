"""R11 family `servo` (stage C3): J122's servo outputs from the 1 kOhm series resistors R150-R153 (D-R11-38).

Explicit tables only (D-R11-07). Board mm (x east, y forward from the aft edge, KiCad's y). R150-R153 (B.Cu) sit in
J122's pin order (SERVO1 east, D-R11-43), so each output goes up to F.Cu by one via east of its resistor and runs under
J122's housing straight into its pin; no two outputs cross.

The MCU side (U1.G2 / H2 / J2 / K2 to R150-R157.1 and D121) is not drawn: stageC3.md O-C3-1.
"""

NETS = ('SERVO1_OUT', 'SERVO2_OUT', 'SERVO3_OUT', 'SERVO4_OUT', 'SERVO2_MCU')

SIG, SV = 0.1, (0.4, 0.2)
RUNS = (
    # D-R11-43: R150-R153 in J122's pin order (SERVO1 east): each output leaves its resistor's OUT pad east on B.Cu
    # to one via and runs on F.Cu under J122's housing straight into its pin; no output crosses another
    ('SERVO1_OUT', 'B', [('R150', '2'), (23.9, 2.175)]),
    ('SERVO1_OUT', 'F', [(23.9, 2.175), ('J122', '1')]),
    ('SERVO2_OUT', 'B', [('R151', '2'), (21.85, 2.175)]),
    ('SERVO2_OUT', 'F', [(21.85, 2.175), (21.85, 4.6), ('J122', '2')]),
    ('SERVO3_OUT', 'B', [('R152', '2'), (20.05, 2.175)]),
    ('SERVO3_OUT', 'F', [(20.05, 2.175), (20.05, 3.65), (21.4, 5.0)]),                    # ends inside J122.3
    ('SERVO4_OUT', 'B', [('R153', '2'), (18.25, 2.175)]),
    ('SERVO4_OUT', 'F', [(18.25, 2.175), (18.25, 3.3), (20.15, 5.2)]),                  # ends inside J122.4
)
VIAS = (('SERVO1_OUT', (23.9, 2.175)), ('SERVO2_OUT', (21.85, 2.175)), ('SERVO3_OUT', (20.05, 2.175)),
        ('SERVO4_OUT', (18.25, 2.175)))
ENDS = (('J122', '1', 'SERVO1_OUT'), ('J122', '2', 'SERVO2_OUT'), ('J122', '3', 'SERVO3_OUT'), ('J122', '4', 'SERVO4_OUT'))


def draw(d):
    import r11_escape
    r11_escape.draw(d, 'servo')
    for net, layer, pts in RUNS:
        d.track(net, layer, SIG, [d.pad(p[0], p[1], net=net) if isinstance(p[0], str) else p for p in pts])
    for net, at in VIAS:
        d.via(net, at, SV)
    for ref, num, net in ENDS:
        d.pad(ref, num, net=net)
