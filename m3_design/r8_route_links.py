"""R8 step 6 family links: the remaining short links, each a single-layer pad-to-pad connection with no via
(r8_route.py; r8_plan section 3 step 6; R8_DECISIONS D59).

The plan routes these through a constrained r5_maze (copper <= 1.3 x the octilinear distance, no via, or the build
fails). r5_maze draws on a 0.1 mm lattice anchored at one pad and ends at the other with a sub-0.1 mm dog-leg (a tiny
jog / short segment under route_check, REQUIREMENTS M2), and its 0.05 mm margin closes U9.9's exit (the corridor
between U9.10 and R84.2 sits exactly at the margin), so its output would need hand edits. D59: the links are drawn as
explicit octilinear polylines, as every other family, and held here to the plan's constraint: one layer, no via, copper
<= RATIO_MAX x the pad-to-pad octilinear distance, or the build fails.

  - U11's network (LOGIC_ILIM, LOGIC_SS east to R86 / C85; USB_OVLO west to the R87 / R88 divider).
  - U9's network (BAT_OVLO to R83 and R82, west of the BAT_ENABLE spine; BAT_DVDT east to C81; BAT_ILIM east round
    R84's GND pad to R84 and TP89).
"""
import math

from r8_route import W, octile

NETS = ('LOGIC_ILIM', 'LOGIC_SS', 'USB_OVLO', 'BAT_OVLO', 'BAT_DVDT', 'BAT_ILIM')
RAILS = ()
RATIO_MAX = 1.3
BUDGET = dict(length_mm=20.0, vias=0, critical_layer_changes=0, ratio=RATIO_MAX)

LINKS = [   # net, layer, (ref, pad) from, (ref, pad) to, polyline (pad centre to pad centre or into the pad)
    ('LOGIC_ILIM', 'B', ('U11', '10'), ('R86', '1'), [(36.75, 58.35), (38.125, 58.35)]),
    ('LOGIC_SS', 'B', ('U11', '11'), ('C85', '1'), [(36.75, 58.85), (37.075, 58.85), (38.175, 59.95)]),
    ('USB_OVLO', 'B', ('U11', '5'), ('R87', '2'), [(34.45, 58.35), (33.275, 58.35), (32.2, 59.425)]),
    ('USB_OVLO', 'B', ('R87', '2'), ('R88', '1'), [(32.2, 59.425), (32.2, 60.835)]),
    ('BAT_OVLO', 'B', ('U9', '2'), ('R83', '1'), [(40.6, 85.725), (40.0, 85.725), (38.925, 86.8)]),
    ('BAT_OVLO', 'B', ('R83', '1'), ('R82', '2'), [(38.925, 86.8), (39.6, 87.475), (39.6, 88.9)]),
    # from U9.7's inner rectangle (centre column x 42.225, 0.05 mm off its centre), on C81.1's row (fix pass 1,
    # R8P1-ROUTING-02, D94: the link began 0.025 mm inside the outer rectangle's edge; C81 cannot move onto the outer
    # rectangle's row y 84.8: its courtyard would meet R84's)
    ('BAT_DVDT', 'B', ('U9', '7'), ('C81', '1'), [(42.225, 84.675), (44.68, 84.675)]),
    ('BAT_ILIM', 'B', ('U9', '9'), ('R84', '1'), [(42.4, 85.725), (43.0, 85.725), (43.0, 86.925), (43.8, 87.725)]),
    ('BAT_ILIM', 'B', ('R84', '1'), ('TP89', '1'), [(43.8, 87.725), (44.3, 88.225), (44.3, 89.6)]),
]


def draw(d):
    for net, layer, (r1, p1), (r2, p2), pts in LINKS:
        a, c = d.pad(r1, p1, net), d.pad(r2, p2, net)
        length = sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))
        ratio = length / octile(a, c)
        assert ratio <= RATIO_MAX + 1e-6, f'{net} {r1}.{p1}-{r2}.{p2}: copper {length:.2f} mm is {ratio:.2f} x its ' \
                                          f'octilinear distance (> {RATIO_MAX})'
        d.track(net, layer, W, pts)
