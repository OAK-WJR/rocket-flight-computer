"""R9 step 7 family links: the constrained short-link stage, the remaining single-layer pad-to-pad connections with
no via (r9_route.py; r9_plan section 4 step 7; R9_DECISIONS D-S7-17).

Each link is one layer, no via, copper <= RATIO_MAX x its octilinear pad-to-pad distance, or the build fails (R8 D59's
constraint, kept). After power_ctl these are U9's and U11's divider and timing pins, each on its part's own line:
  - U9 (bottom, rot 90): BAT_OVLO U9.2 straight north into R82.2, R82.2 east into R83.1 (the OVLO divider north of U9);
    BAT_DVDT U9.7 straight south into C81.1.
  - U11 (bottom, rot 90): LOGIC_ILIM U11.10 straight east into R86.1; LOGIC_SS U11.11 east and one 45-degree run into
    C85.1 (clear of U11.12's pad and R86.1); USB_OVLO U11.5 straight west into R87.2, R87.2 north into R88.1.
"""
import math

from r9_route import W, mm, octile

NETS = ('BAT_OVLO', 'BAT_DVDT', 'LOGIC_ILIM', 'LOGIC_SS', 'USB_OVLO')
RAILS = ()
RATIO_MAX = 1.3
BUDGET = dict(length_mm=12.0, vias=0, critical_layer_changes=0, ratio=RATIO_MAX)

LINKS = [   # net, layer, (ref, pad) from, (ref, pad) to, polyline (pad centre to pad centre)
    ('BAT_OVLO', 'B', ('U9', '2'), ('R82', '2'), [(40.525, 91.3), (40.525, 92.9)]),
    ('BAT_OVLO', 'B', ('R82', '2'), ('R83', '1'), [(40.525, 92.9), (41.935, 92.9)]),
    ('BAT_DVDT', 'B', ('U9', '7'), ('C81', '1'), [(39.6, 89.5), (39.6, 87.525)]),
    ('LOGIC_ILIM', 'B', ('U11', '10'), ('R86', '1'), [(40.8, 66.25), (42.075, 66.25)]),
    ('LOGIC_SS', 'B', ('U11', '11'), ('C85', '1'), [(40.8, 66.75), (41.15, 66.75), (42.125, 67.725)]),
    ('USB_OVLO', 'B', ('U11', '5'), ('R87', '2'), [(38.5, 66.25), (37.0, 66.25)]),
    ('USB_OVLO', 'B', ('R87', '2'), ('R88', '1'), [(37.0, 66.25), (37.0, 67.675)]),
]


def pad_at(d, ref, num, net, at):
    """The centre of the pad shape of REF.NUM (on NET) at AT: U9's corner pins are two rectangles each (an L), and a
    link ends on the centre of one of them."""
    f = d.b.FindFootprintByReference(ref)
    shapes = [p for p in f.Pads() if p.GetNumber() == num]
    assert shapes and all(p.GetNetname() == net for p in shapes), f'{ref}.{num} is not on {net}'
    xy = [(round(mm(p.GetPosition().x), 4), round(mm(p.GetPosition().y), 4)) for p in shapes]
    assert any(math.dist(q, at) < 1e-3 for q in xy), f'{ref}.{num} has no pad centre at {at} ({xy})'
    return at


def draw(d):
    for net, layer, (r1, p1), (r2, p2), pts in LINKS:
        a, c = pad_at(d, r1, p1, net, pts[0]), pad_at(d, r2, p2, net, pts[-1])
        length = sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))
        ratio = length / octile(a, c)
        assert ratio <= RATIO_MAX + 1e-6, f'{net} {r1}.{p1}-{r2}.{p2}: copper {length:.2f} mm is {ratio:.2f} x its ' \
                                          f'octilinear distance (> {RATIO_MAX})'
        d.track(net, layer, W, pts)
