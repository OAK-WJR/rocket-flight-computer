"""R11 family `servo` (stage C3): J122's servo outputs from the 1 kOhm series resistors R150-R153 (D-R11-38).

Explicit tables only (D-R11-07). Board mm (x east, y forward from the aft edge, KiCad's y). R150-R153 (B.Cu, SERVO1-4
west to east) feed J122.1-.4 (F.Cu, SERVO1 east to SERVO4 west): the order reverses, so each net changes layer once and
the four cross on different layers: SERVO1 and SERVO2 go up to F.Cu beside their resistors and cross under J122's housing
on F.Cu; SERVO3 and SERVO4 run on B.Cu east of R152 / R153 and come up south of the pin row.

The MCU side (U1.G2 / H2 / J2 / K2 to R150-R157.1 and D121) is not drawn: stageC3.md O-C3-1.
"""

NETS = ('SERVO1_OUT', 'SERVO2_OUT', 'SERVO3_OUT', 'SERVO4_OUT')

SIG, SV = 0.1, (0.4, 0.2)
RUNS = (
    ('SERVO1_OUT', 'B', [('R150', '2'), (18.25, 2.175)]),
    ('SERVO1_OUT', 'F', [(18.25, 2.175), (20.7, 2.175), (23.65, 5.125)]),                  # ends inside J122.1
    ('SERVO2_OUT', 'B', [('R151', '2'), (19.55, 2.175), (20.45, 3.075)]),
    ('SERVO2_OUT', 'F', [(20.45, 3.075), (22.4, 5.025)]),                                 # ends inside J122.2
    ('SERVO3_OUT', 'B', [('R152', '2'), (21.35, 2.175), (22.0, 2.825), (22.0, 6.325)]),
    ('SERVO3_OUT', 'F', [(22.0, 6.325), (21.65, 5.975)]),                               # ends inside J122.3
    ('SERVO4_OUT', 'B', [('R153', '2'), (23.15, 2.175), (23.45, 2.475), (23.45, 5.675), (22.5, 6.625)]),
    ('SERVO4_OUT', 'F', [(22.5, 6.625), (22.4, 6.725), (21.45, 6.725), (20.4, 5.675)]),                # ends inside J122.4
)
VIAS = (('SERVO1_OUT', (18.25, 2.175)), ('SERVO2_OUT', (20.45, 3.075)), ('SERVO3_OUT', (22.0, 6.325)),
        ('SERVO4_OUT', (22.5, 6.625)))
ENDS = (('J122', '1', 'SERVO1_OUT'), ('J122', '2', 'SERVO2_OUT'), ('J122', '3', 'SERVO3_OUT'), ('J122', '4', 'SERVO4_OUT'))


def draw(d):
    for net, layer, pts in RUNS:
        d.track(net, layer, SIG, [d.pad(p[0], p[1], net=net) if isinstance(p[0], str) else p for p in pts])
    for net, at in VIAS:
        d.via(net, at, SV)
    for ref, num, net in ENDS:
        d.pad(ref, num, net=net)
