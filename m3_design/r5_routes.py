"""R5 scripted (hand-specified) critical copper: USB, crystal, QSPI, pyro exits and power (docs/M3_R5.md).

Imported by r5_pcb.py. Every segment is 0, 45 or 90 degrees (asserted); pads are looked up by
reference and number, and the script asserts that each route starts and ends on the pad it names.
Widths: signals 0.2 mm, USB 0.2 mm, power per IPC-2152 (see each function).
"""
import math

import pcbnew

from r5_maze import maze, maze_multi, via_spot

mm, MM = pcbnew.ToMM, pcbnew.FromMM
F, B, IN1, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def pad(b, ref, num):
    f = b.FindFootprintByReference(ref)
    assert f is not None, ref
    p = next(p for p in f.Pads() if p.GetNumber() == num)
    return round(mm(p.GetPosition().x), 4), round(mm(p.GetPosition().y), 4)


def _check_angle(a, c):
    dx, dy = abs(c[0] - a[0]), abs(c[1] - a[1])
    assert dx < 1e-4 or dy < 1e-4 or abs(dx - dy) < 1e-4, f'segment {a}->{c} is not 0/45/90 deg'


def route(b, netname, layer, pts, w=0.2):
    """Polyline of segments on one layer; consecutive points must be 0/45/90 apart."""
    n = b.FindNet(netname)
    assert n is not None, netname
    for a, c in zip(pts, pts[1:]):
        if abs(a[0] - c[0]) < 1e-6 and abs(a[1] - c[1]) < 1e-6:
            continue
        _check_angle(a, c)
        t = pcbnew.PCB_TRACK(b)
        t.SetLayer(layer)
        t.SetWidth(MM(w))
        t.SetStart(P(*a))
        t.SetEnd(P(*c))
        t.SetNet(n)
        b.Add(t)


def via(b, netname, xy, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(P(*xy))
    v.SetWidth(MM(d))
    v.SetDrill(MM(drill))
    v.SetNet(b.FindNet(netname))
    b.Add(v)


def usb(b):
    """USB 2.0 full speed, J3 -> D4 (USBLC6, flow-through) -> U1 PA11/PA12, and the CC pull-downs.

    J3's D- pads B7/A7 are joined on F.Cu by a loop under the receptacle (left of the A6 pad), so D-
    needs no via at the connector; the D+ pads A6/B6 each drop through a via and join on B.Cu. D- runs
    between those two vias. On B.Cu both lines enter D4 at pins 6/4 and leave from pins 1/3, then climb
    to U1's pins 70/71 through one via each. Lengths about 14 mm each; 0.2 mm traces over the In1 GND
    plane. CC1/CC2 reach their 5.1 k pull-downs (R7/R8, bottom) through one via each."""
    dm, dp = 'USB_DM', 'USB_DP'
    a5, b7, a6, a7, b6, b5 = (pad(b, 'J3', n) for n in ('A5', 'B7', 'A6', 'A7', 'B6', 'B5'))
    assert abs(a7[0] - 6.88) < 0.01 and abs(b7[1] - 56.55) < 0.01, 'J3 moved: re-derive the USB fan-out'
    x = a5[0]
    # D-: loop under the receptacle, then right between the D+ vias and down to D4.6
    route(b, dm, F, [b7, (5.7, b7[1]), (5.7, a7[1]), a7])
    d6, d1 = pad(b, 'D4', '6'), pad(b, 'D4', '1')
    d4, d3 = pad(b, 'D4', '4'), pad(b, 'D4', '3')
    vdm = (d6[0], 58.3)
    route(b, dm, F, [a7, (d6[0], a7[1]), vdm])
    via(b, dm, vdm)
    route(b, dm, B, [vdm, d6])
    # D+: a via behind each pad, joined on B.Cu, into D4.4
    v1, v2 = (8.9, a6[1] - 0.3), (8.9, b6[1] + 0.3)
    route(b, dp, F, [a6, (8.6, a6[1]), v1])
    route(b, dp, F, [b6, (8.6, b6[1]), v2])
    via(b, dp, v1)
    via(b, dp, v2)
    route(b, dp, B, [v1, v2, (9.6, 59.05), (d4[0], 59.05), d4])
    route(b, dm, B, [d6, d1])                         # flow-through under D4 (pins 6-1, 4-3)
    route(b, dp, B, [d4, d3])
    # out of D4 (pins 1 and 3) up to U1 PA11 (pin 70, D-) and PA12 (pin 71, D+)
    u70, u71 = pad(b, 'U1', '70'), pad(b, 'U1', '71')
    vm, vp = (11.2, u70[1] - 0.5), (12.5, u71[1] + 0.4)
    route(b, dm, B, [d1, (d1[0], vm[1] + (vm[0] - d1[0])), vm])
    route(b, dp, B, [d3, (d3[0], vp[1] + (vp[0] - d3[0])), vp])
    via(b, dm, vm)
    via(b, dp, vp)
    route(b, dm, F, [vm, (vm[0] + 0.5, u70[1]), u70])
    route(b, dp, F, [vp, (vp[0] + 0.4, u71[1]), u71])
    # CC1 -> R7, CC2 -> R8
    r7, r8 = pad(b, 'R7', '1'), pad(b, 'R8', '1')
    vc1, vc2 = (12.6, a5[1]), (8.2, b5[1])
    route(b, 'CC1', F, [a5, vc1])
    via(b, 'CC1', vc1)
    route(b, 'CC1', B, [vc1, r7])
    route(b, 'CC2', F, [b5, vc2])
    via(b, 'CC2', vc2)
    route(b, 'CC2', B, [vc2, (vc2[0], r8[1] - (r8[0] - vc2[0])), r8])


def crystal(b):
    """25 MHz HSE: Y1 on the bottom under U1's right edge, load capacitors C25/C26 beside its pads.

    PH0 (pin 12, OSC_IN) and PH1 (pin 13, OSC_OUT) leave their pads inward on F.Cu under the package
    body and drop through one via each; the In1 GND plane separates them from the MCU's own copper.
    OSC_IN: 3 mm to Y1.1, OSC_OUT: about 7 mm to Y1.3 (it passes Y1's GND pad on F.Cu). Y1's and the
    capacitors' GND pads each get a via to the In1 plane."""
    u12, u13 = pad(b, 'U1', '12'), pad(b, 'U1', '13')
    y1, y3, y2, y4 = (pad(b, 'Y1', n) for n in '1324')
    c25, c26 = pad(b, 'C25', '1'), pad(b, 'C26', '1')
    assert abs(c25[0] - y1[0]) < 0.01 and abs(c26[1] - 35.3) < 0.02, 'C25/C26 moved: re-derive the HSE routes'
    vi = (27.9, 36.4)
    route(b, 'HSE_IN', F, [u12, (vi[0] + 0.4, u12[1]), vi])
    via(b, 'HSE_IN', vi)
    route(b, 'HSE_IN', B, [vi, (vi[0] - 0.2, y1[1]), y1, c25])
    vo = (23.2, 35.9)
    route(b, 'HSE_OUT', F, [u13, (vo[0] + 0.4, u13[1]), vo])
    via(b, 'HSE_OUT', vo)
    route(b, 'HSE_OUT', B, [vo, (vo[0], 35.6), (vo[0] + 0.7, y3[1]), y3])
    route(b, 'HSE_OUT', B, [vo, (c26[0], c26[1])])
    for xy, g in ((y2, (y2[0], y2[1] + 1.3)), (y4, (y4[0], y4[1] - 1.3)),
                  (pad(b, 'C25', '2'), None), (pad(b, 'C26', '2'), None)):
        if g is None:
            continue
        route(b, 'GND', B, [xy, g])
        via(b, 'GND', g)


def track_end(b, netname, near):
    """Exact end point of an existing segment of netname nearest `near` (block copper moved from R4)."""
    best = None
    for t in b.GetTracks():
        if t.GetNetname() != netname or t.GetClass() == 'PCB_VIA':
            continue
        for e in (t.GetStart(), t.GetEnd()):
            d = math.hypot(mm(e.x) - near[0], mm(e.y) - near[1])
            if best is None or d < best[0]:
                best = (d, (mm(e.x), mm(e.y)))
    assert best and best[0] < 0.05, (netname, near, best)
    return best[1]


NECKS = []
SKIPPED = []


def _pad_at(b, xy):
    for f in b.GetFootprints():
        for p in f.Pads():
            if abs(mm(p.GetPosition().x) - xy[0]) < 1e-3 and abs(mm(p.GetPosition().y) - xy[1]) < 1e-3:
                return f, p
    return None, None


def escape(b, xy, extra=0.6):
    """Point straight out of the pad at xy, away from its footprint's centre along the pad's long axis."""
    f, p = _pad_at(b, xy)
    if p is None:
        return None
    bb = p.GetBoundingBox()
    w, h = mm(bb.GetWidth()), mm(bb.GetHeight())
    cx, cy = mm(f.GetPosition().x), mm(f.GetPosition().y)
    if w >= h:
        d = math.copysign(w / 2 + extra, xy[0] - cx)
        return round(xy[0] + d, 4), xy[1]
    d = math.copysign(h / 2 + extra, xy[1] - cy)
    return xy[0], round(xy[1] + d, 4)


def leg(b, netname, layer, a, c, w=0.2, **kw):
    """One scripted connection drawn by the grid router between points chosen here; returns its end.
    A wide leg that cannot leave a fine-pitch pin at full width necks down to 0.3 mm for a short stub
    straight out of that pin (logged in NECKS); a short leg may be drawn at 0.3 mm throughout."""
    try:
        pts = maze(b, netname, layer, a, c, w=w, **kw)
        route(b, netname, layer, pts, w)
        return pts[-1]
    except RuntimeError:
        if w <= 0.3:
            raise
    ea, ec = escape(b, a), escape(b, c)
    for sa, sc in ((ea, ec), (ea, None), (None, ec)):
        if sa is None and sc is None:
            continue
        a2, c2 = sa or a, sc or c
        try:
            pts = maze(b, netname, layer, a2, c2, w=w, **kw)
        except RuntimeError:
            continue
        if sa:
            route(b, netname, layer, [a, sa], 0.3)
        route(b, netname, layer, pts, w)
        if sc:
            route(b, netname, layer, [pts[-1], c] if pts[-1] == sc else [sc, c], 0.3)
        NECKS.append((netname, a, c))
        return c if sc else pts[-1]
    if math.hypot(a[0] - c[0], a[1] - c[1]) > 4.0:
        raise RuntimeError(f'leg: {netname} {a}->{c} does not fit at {w} mm')
    pts = maze(b, netname, layer, a, c, w=0.3, **kw)
    route(b, netname, layer, pts, 0.3)
    NECKS.append((netname, a, c))
    return pts[-1]


def pyro_exits(b):
    """Pyro control nets from the moved R4 block to the MCU side (docs/M3_R5.md section 1).

    Inside the block the R4 copper is kept; what R4 routed toward its forward MCU is replaced here. Each
    net leaves its block copper on F.Cu to a via, crosses on In2 (the layer between the In1 GND plane and
    the bottom; the BAT_IN, RAW_ACT and CAM_5V islands are avoided, the 3V3 pours fill afterwards) to a via
    beside its ADC series resistor (R168-R172, bottom) or, for the gate lines, beside U1 pins 3/4, and
    finishes on B.Cu or F.Cu. In2 is one layer, so the lanes follow a planar order: the gate and CONT lanes
    pass east of J122 (west to east PYRO2_GATE_N, PYRO1_GATE_N, PYRO2_CONT, PYRO1_CONT; the CONT lanes stay east of
    the via room in front of U1's right-hand pins and end at R169/R168 beside U1), the ARM and
    RAW_ACT sense lanes west of it under the buzzer. The router keeps the m3.kicad_dru pyro clearances
    (rule G: gate nets 0.3 mm from other live nets inside the block). PYRO1_COLD (R131 to D120) crosses the
    block on B.Cu, as in R4 (In2 is fenced by the lanes)."""
    def drop(net, a, v, layer=F):
        v = via_spot(b, net, v, a)
        e = leg(b, net, layer, a, v)
        via(b, net, e)
        return e

    def lane(net, vb, waypoints, ve):
        """In2 run from block via vb through waypoints to via ve (each waypoint on the previous segment's
        lattice, so only ve may need the sub-0.1 mm end adjustment)."""
        a = vb
        for w in waypoints:
            w = (a[0] + round((w[0] - a[0]) / 0.1) * 0.1, a[1] + round((w[1] - a[1]) / 0.1) * 0.1)
            a = leg(b, net, IN2, a, (round(w[0], 4), round(w[1], 4)), margin=10)
        leg(b, net, IN2, a, ve, margin=10)

    # block-side vias
    vb = {'PYRO1_GATE_N': drop('PYRO1_GATE_N', pad(b, 'R127', '1'), (23.0, 70.3)),
          'PYRO2_GATE_N': (19.4, 84.98)}
    via(b, 'PYRO2_GATE_N', vb['PYRO2_GATE_N'])        # R4's via point, where the block copper ends
    p1 = track_end(b, 'PYRO1_CONT', (25.22, 70.42))
    via(b, 'PYRO1_CONT', p1)
    vb['PYRO1_CONT'] = p1
    vb['PYRO2_CONT'] = (26.25, 89.85)                 # R4's via and stub north of R142 (south of it the drop had to
    via(b, 'PYRO2_CONT', vb['PYRO2_CONT'])            # wrap round PYRO2_COLD, which closed R142.2's GND pour in)
    route(b, 'PYRO2_CONT', F, [vb['PYRO2_CONT'], (26.25, 90.45)], 0.2)
    vb['ARM1_SENSE'] = drop('ARM1_SENSE', pad(b, 'R133', '1'), (18.4, 73.3))
    vb['ARM2_SENSE'] = (17.975, 80.825)               # existing block via (R4's In2 hop)
    vb['RAW_ACT_SENSE'] = drop('RAW_ACT_SENSE', pad(b, 'R182', '1'), (14.5, 90.4))
    # MCU-side vias: beside U1 pins 3/4 for the gates, beside each series resistor's block-side pad
    u3, u4 = pad(b, 'U1', '3'), pad(b, 'U1', '4')
    # gate vias staggered off U1's corner pins 3/4 (0.5 mm apart): pin 4's north-east, pin 3's south-east, so each
    # leg leaves its pin straight out and neither passes the other's via
    ends = {'PYRO1_GATE_N': (31.9, 41.2), 'PYRO2_GATE_N': (31.9, 39.3)}
    res = {'PYRO1_CONT': 'R168', 'PYRO2_CONT': 'R169', 'ARM1_SENSE': 'R170', 'ARM2_SENSE': 'R171',
           'RAW_ACT_SENSE': 'R172'}
    for net, d in (('PYRO1_CONT', (1.0, 0.0)), ('PYRO2_CONT', (0.9, 0.9)), ('ARM1_SENSE', (0.9, 0.9)),
                   ('ARM2_SENSE', (0.9, 0.9)), ('RAW_ACT_SENSE', (0.9, 0.9))):
        rp = pad(b, res[net], '1')
        ends[net] = (rp[0] + d[0], rp[1] + d[1])
    paths = [('PYRO1_CONT', [(32.4, 70.4), (32.4, 61.5)]),
             ('PYRO2_CONT', [(24.2, 74.0), (24.2, 68.8), (31.6, 68.8), (31.6, 61.5)]),
             ('PYRO1_GATE_N', [(23.0, 68.0), (30.2, 68.0), (30.2, 61.5)]),
             ('PYRO2_GATE_N', [(19.2, 74.0), (19.2, 67.3), (29.5, 67.3), (29.5, 61.5)]),
             ('RAW_ACT_SENSE', [(14.6, 60.0)]),
             ('ARM2_SENSE', [(15.4, 60.0)]),
             ('ARM1_SENSE', [(16.2, 60.0)])]
    for net, wps in paths:
        ve = via_spot(b, net, ends[net], vb[net])
        lane(net, vb[net], wps, ve)
        via(b, net, ve)
        if net == 'PYRO1_GATE_N':
            leg(b, net, F, ve, u3)                  # from the via: it is on the lane's lattice
        elif net == 'PYRO2_GATE_N':
            leg(b, net, F, ve, u4)
        else:
            leg(b, net, B, ve, pad(b, res[net], '1'))
    # R179 (PYRO2_CONT bottom half, B.Cu) from the PYRO2_CONT via
    leg(b, 'PYRO2_CONT', B, vb['PYRO2_CONT'], pad(b, 'R179', '1'))
    # PYRO1_COLD: R131 (drain side, aft) to D120 (forward)
    c1 = drop('PYRO1_COLD', pad(b, 'R131', '2'), (29.7, 66.9))
    c2 = drop('PYRO1_COLD', pad(b, 'D120', '1'), (19.0, 94.3))
    for layer in (B, F):
        try:
            leg(b, 'PYRO1_COLD', layer, c1, c2, margin=5)
            break
        except RuntimeError:
            if layer == F:
                raise


def tie(b, netname, a, near, layer, w=0.25, tries=12):
    """Pad (or point) a to a checked via near `near`, drawn by the router on `layer`; returns the via. A spot its
    stub cannot reach is skipped for the next nearest."""
    tried = []
    for _ in range(tries):
        v = via_spot(b, netname, near, a, exclude=tried)
        try:
            leg(b, netname, layer, a, v, w=w)
        except RuntimeError:
            tried.append(v)
            continue
        via(b, netname, v)
        return v
    raise RuntimeError(f'tie: no reachable via for {netname} at {a} near {near}')



def _layers_at(b, xy):
    """Copper layers present at xy: a pad's layers, or all four for a via."""
    for v in b.GetTracks():
        if v.GetClass() == 'PCB_VIA' and abs(mm(v.GetPosition().x) - xy[0]) < 1e-3 and \
                abs(mm(v.GetPosition().y) - xy[1]) < 1e-3:
            return {F, IN1, IN2, B}
    f, p = _pad_at(b, xy)
    if p is None:
        return {F, IN1, IN2, B}                      # a free point: the caller puts copper there
    return {lay for lay in (F, IN1, IN2, B) if p.IsOnLayer(lay)}


def _via_for(b, netname, p, own, w):
    """A via spot for pad p (on layer `own`) with a stub that fits: tried straight out of the pad at
    staggered distances, then anywhere near the pad."""
    tries = [escape(b, p, extra=e) for e in (0.9, 1.7, 2.5)] + [p]
    for e in tries:
        if e is None:
            continue
        try:
            v = via_spot(b, netname, e, p, r=0.8 if e is not p else 2.5)
            maze(b, netname, own, p, v, w=min(w, 0.25), margin=3)
            return v
        except RuntimeError:
            continue
    raise RuntimeError(f'no via for {netname} at {p}')


def connect(b, netname, a, c, w, layers, **kw):
    """Route a-c on the first of `layers` that works. An end that is a pad not on that layer first gets a
    via (checked spot, stub on the pad's own layer). Nothing is committed for a layer that fails."""
    errs = []
    for layer in layers:
        ends, stubs = [], []
        try:
            for p in (a, c):
                here = _layers_at(b, p)
                if layer in here:
                    ends.append(p)
                    continue
                own = F if F in here else B
                v = _via_for(b, netname, p, own, w)
                ends.append(v)
                stubs.append((own, p, v))
            pts = maze(b, netname, layer, ends[0], ends[1], w=w, **kw)
        except RuntimeError as e:
            errs.append(str(e))
            continue
        for own, p, v in stubs:
            leg(b, netname, own, p, v, w=min(w, 0.25), margin=3)
            via(b, netname, v)
        route(b, netname, layer, pts, w)
        return pts[-1]
    raise RuntimeError(f'connect: {netname} {a}->{c}: ' + ' | '.join(errs))


def multi(b, netname, a, c, w, layers, via_cost=15.0, **kw):
    """One connection over several layers with vias where the grid router chooses (maze_multi); a pad end
    starts or ends on its own layer. A wide connection that cannot leave a fine-pitch pin at full width necks
    down to 0.3 mm for a stub straight out of that pin (logged in NECKS), as leg() does."""
    def lays(p):
        f, pd = _pad_at(b, p)
        return None if pd is None else {lay for lay in layers if pd.IsOnLayer(lay)}

    def go(a2, c2, la, lc):
        runs, vias = maze_multi(b, netname, layers, a2, c2, w=w, a_layers=la, c_layers=lc, via_cost=via_cost, **kw)
        for layer, pts in runs:
            route(b, netname, layer, pts, w)
        for v in vias:
            via(b, netname, v)
        return runs
    try:
        return go(a, c, lays(a), lays(c))[-1][1][-1]
    except RuntimeError:
        if w <= 0.3:
            raise
    la, lc = lays(a), lays(c)
    ea, ec = (escape(b, a) if la else None), (escape(b, c) if lc else None)
    for sa, sc in ((ea, ec), (ea, None), (None, ec)):
        if sa is None and sc is None:
            continue
        try:
            runs = go(sa or a, sc or c, la, lc)
        except RuntimeError:
            continue
        if sa:
            route(b, netname, runs[0][0], [a, sa], 0.3)
        if sc:
            route(b, netname, runs[-1][0], [sc, c], 0.3)
        NECKS.append((netname, a, c))
        return c
    raise RuntimeError(f'multi: {netname} {a}->{c} does not fit at {w} mm')


def power_link(b, netname, a, c, w, layers=(B, IN2), wider=(B, IN2, F), margin=6, via_cost=20.0):
    """A power connection over several layers (maze_multi, checked vias): first on `layers`, then on `wider`."""
    try:
        return multi(b, netname, a, c, w, layers, margin=margin, via_cost=via_cost)
    except RuntimeError:
        return multi(b, netname, a, c, w, wider, margin=margin + 4, via_cost=via_cost)


def branch(b, netname, a, c, w, layers, **kw):
    """A low-current branch (pull-up, test pad, small capacitor): scripted if it fits, else left to the
    autorouter and listed in SKIPPED."""
    try:
        return any_layer(b, netname, a, c, w, layers, **kw)
    except RuntimeError:
        SKIPPED.append((netname, a))
        return None


def any_layer(b, netname, a, c, w, layers, **kw):
    if any(lay in (IN1, IN2) for lay in layers) or len(layers) > 1:
        return connect(b, netname, a, c, w, layers, **kw)
    for i, layer in enumerate(layers):
        try:
            return leg(b, netname, layer, a, c, w=w, **kw)
        except RuntimeError:
            if i == len(layers) - 1:
                raise


def power(b):
    """Power copper (REQUIREMENTS F4/F6/F9; IPC-2152 widths: 7.7 A servo path in pours and the In2/F.Cu RAW_ACT
    planes, 1 A camera path 0.8 mm, logic rails 0.5 mm, 0.4 mm for the USB and VBUS feeds, 0.25 mm sense taps).

    The pours themselves are made by r5_pcb.zones() before any route (BAT_IN on In2, B.Cu and F.Cu, the load
    switch's source pour, RAW_ACT on In2, B.Cu and F.Cu); here they get their stitching vias and branches."""
    # --- actuator gate. The FETs face each other, so their gates sit at opposite ends of the source pour (Q120's
    # upper left, Q121's lower right). C120 and R120 stand beside the pour's right end, source pins inward;
    # Q121's gate reaches their gate pins below them. Q120's gate drops through a via beside its pin, crosses
    # on In2 under the pour and comes up beside Q121's gate, so the 7.7 A source pour is not cut (as R4).
    g120, g121 = pad(b, 'Q120', '4'), pad(b, 'Q121', '4')
    leg(b, 'ACT_FET_S', B, pad(b, 'R120', '1'), pad(b, 'C120', '1'), w=0.4, margin=2)
    leg(b, 'ACT_GATE', B, pad(b, 'R120', '2'), g121, w=0.25, margin=3)
    leg(b, 'ACT_GATE', B, pad(b, 'C120', '2'), pad(b, 'R120', '2'), w=0.25, margin=2)
    try:                                              # B.Cu, or across the VLOGIC feed with a via pair
        leg(b, 'ACT_GATE', B, pad(b, 'R121', '1'), pad(b, 'R120', '2'), w=0.25, margin=4)
    except RuntimeError:
        try:
            multi(b, 'ACT_GATE', pad(b, 'R121', '1'), pad(b, 'R120', '2'), 0.25, (B, F), via_cost=8.0, margin=4)
        except RuntimeError:
            multi(b, 'ACT_GATE', pad(b, 'R121', '1'), pad(b, 'R120', '2'), 0.25, (B, F, IN2), via_cost=8.0, margin=6)
    vl = tie(b, 'ACT_GATE', g120, (g120[0] - 1.0, g120[1]), B, w=0.25)
    vr = via_spot(b, 'ACT_GATE', (g121[0] + 1.9, g121[1] + 1.1), vl)   # below BAT_IN_F, right of RAW_ACT_B
    leg(b, 'ACT_GATE', IN2, vl, vr, w=0.25, margin=3)
    via(b, 'ACT_GATE', vr)
    leg(b, 'ACT_GATE', B, vr, g121, w=0.25, margin=2)
    # the input TVS's GND pad sits inside the BAT_IN pours (B.Cu and In2): straight to the battery terminal's GND
    leg(b, 'GND', B, pad(b, 'D8', '2'), pad(b, 'J1', '2'), w=0.8, margin=4)
    for x in (2.1, 3.4, 4.6, 5.9):                    # Q120 drain row to the In2 island
        via(b, 'BAT_IN', via_spot(b, 'BAT_IN', (x, 8.6), (x, 8.6), r=0.6))
    leg(b, 'BAT_IN', F, pad(b, 'C88', '1'), U9_ESC['vin'], w=0.3, margin=2)   # U9's input capacitor onto its IN via
    r82 = pad(b, 'R82', '1')
    tie(b, 'BAT_IN', r82, (9.45, min(max(r82[1] + 0.9, 15.6), 36.0)), F if not b.FindFootprintByReference('R82').IsFlipped() else B)
    # --- input damper
    for p in (('C89', '2'), ('C95', '2')):
        leg(b, 'BAT_DAMP', F, pad(b, *p), pad(b, 'R166', '1'), w=0.8)
    # --- RAW_ACT: Q121 drains to the In2 strip, the F.Cu band to the strip, C121 to J122, the bulk caps
    for x in (1.6, 2.8, 4.0, 5.2, 6.4):
        via(b, 'RAW_ACT', via_spot(b, 'RAW_ACT', (x, 31.8), (x, 31.8), r=0.8))
    for y in (64.0, 65.3, 66.6, 67.9, 69.2):
        for x in (5.3, 6.6, 7.9):
            try:
                via(b, 'RAW_ACT', via_spot(b, 'RAW_ACT', (x, y), (x, y), r=0.3))
            except RuntimeError:
                pass
    for r in ('C150', 'C151'):
        tie(b, 'RAW_ACT', pad(b, r, '1'), (pad(b, r, '1')[0] - 1.0, pad(b, r, '1')[1]), B, w=0.5)
    tie(b, 'RAW_ACT', pad(b, 'TP120', '1'), (pad(b, 'TP120', '1')[0], pad(b, 'TP120', '1')[1] - 1.5), B, w=0.4)
    tie(b, 'RAW_ACT', pad(b, 'R177', '1'), (10.6, 91.7), F, w=0.3)


def power2(b):
    """Logic and camera supply paths (second part of the power copper)."""
    # --- RAW_PROTECTED: U9 OUT -> D9 -> U11 and C82 -> the camera eFuse U7 (up to about 1 A: 0.6 mm)
    out_end, vout, vd9 = U9_ESC['out_end'], U9_ESC['vout'], U9_ESC['vd9']
    c82 = pad(b, 'C82', '1')                          # U9's output capacitor: to the OUT bar's via
    try:
        power_link(b, 'RAW_PROTECTED', c82, out_end, 0.6, layers=(F,), wider=(F, B), margin=3)
    except RuntimeError:
        power_link(b, 'RAW_PROTECTED', c82, vout, 0.6, layers=(F, B), wider=(F, B, IN2))
    for r in ('R122', 'R92'):
        branch(b, 'RAW_PROTECTED', pad(b, r, '1'), vd9, 0.25, (B, IN2), margin=5)
    # --- camera buck (AP63301, 1 A out): input chain, switch node, bootstrap, output, feedback
    cin = 'CAM_INPUT_LIMITED'
    branch(b, cin, pad(b, 'TP71', '1'), pad(b, 'C73', '1'), 0.3, (B, F), margin=6)
    for near in ((39.5, 85.6), (39.5, 86.8)):         # into the In2 CAM_5V strip
        tie(b, 'CAM_5V', pad(b, 'C75', '1'), near, B, w=0.8)
    for r in ('R71', 'C77'):
        tie(b, 'CAM_5V', pad(b, r, '1'), (39.5, pad(b, r, '1')[1]), F, w=0.3)
    for r in ('U13', 'C91', 'R104'):
        rp = pad(b, r, '1')
        tie(b, 'CAM_5V', rp, (39.5, max(rp[1] + 0.9, 16.2)), B, w=0.4)
    for r in ('R78', 'TP72'):
        branch(b, 'CAM_5V', pad(b, r, '1'), pad(b, 'C75', '1'), 0.3, (B, IN2), margin=7)
    vfb = tie(b, 'CAM_FB', pad(b, 'U8', '1'), (pad(b, 'U8', '1')[0] - 1.2, pad(b, 'U8', '1')[1]), B)
    for r in (('R72', '1'), ('R71', '2'), ('C77', '2')):
        leg(b, 'CAM_FB', F, pad(b, *r), vfb, w=0.25, margin=3)
    # to the camera eFuse (0.4 mm: about 0.8 A): B.Cu and F.Cu first (keeps In2 free aft of U1), then In2 too
    power_link(b, 'RAW_PROTECTED', pad(b, 'U7', '3'), vd9, 0.4, layers=(B, F), wider=(B, F, IN2), margin=14)
    for r in ('C71', 'TP70'):
        branch(b, 'RAW_PROTECTED', pad(b, r, '1'), pad(b, 'U7', '4'), 0.4, (B, F), margin=5)
    # --- camera UART supply: U13 (LDO) -> U12 and its capacitors
    for r in (('U12', '7'), ('C93', '1'), ('C92', '1'), ('R103', '1'), ('TP90', '1')):
        branch(b, 'CAM_IO_3V3', pad(b, *r), pad(b, 'U13', '5'), 0.25, (B, F, IN2), margin=6)
    # --- 3V3 buck (AP63203): switch node, bootstrap
    # --- VBUS: the two receptacle VBUS pads -> D4 (clamp), the sense divider, the capacitors, U10's input
    vb1 = tie(b, 'VBUS', pad(b, 'J3', 'A4B9'), (8.2, 54.9), F, w=0.4)
    vb2 = tie(b, 'VBUS', pad(b, 'J3', 'B4A9'), (9.9, 60.0), F, w=0.4)
    vb3 = tie(b, 'VBUS', pad(b, 'D4', '5'), (11.0, 58.35), B, w=0.4)
    for v in (vb1, vb2):
        leg(b, 'VBUS', IN2, v, vb3, w=0.4, margin=4)
    for r in (('C28', '1'), ('C83', '1')):            # (to vb2 the legs looped round R8 and cut its GND pad off)
        leg(b, 'VBUS', B, pad(b, *r), vb1, w=0.4, margin=4)
    for r in (('U10', '3'), ('U10', '1'), ('R9', '1')):
        branch(b, 'VBUS', pad(b, *r), vb3, 0.4, (B, IN2), margin=5)
    # --- VLOGIC sense divider (after the main power paths, which it must not box in)
    if branch(b, 'VLOGIC', pad(b, 'R60', '1'), pad(b, 'U11', '8'), 0.25, (B, IN2, F), margin=5) is None and \
            _to_island(b, 'VLOGIC', pad(b, 'R60', '1'), pad(b, 'U11', '8'), 0.25):   # to any VLOGIC copper
        SKIPPED.pop()
    # --- USB_LIMITED branches (the main path is usb_limited(), before the signals)
    for r in (('C86', '1'), ('R87', '1'), ('TP82', '1')):
        try:                                          # (R87 is on the top, beside U11's OVLO via)
            multi(b, 'USB_LIMITED', pad(b, *r), pad(b, 'U11', '7'), 0.3, (B, IN2, F), margin=6, via_cost=20.0)
        except RuntimeError:
            SKIPPED.append(('USB_LIMITED', r))


# Pins the escape check (no escape on their layer, no via spot reachable) found boxed in by the scripted copper;
# each gets a fan-out via straight out of it right after placement, which the autorouter continues from.
EARLY_ESCAPES = [('U11', '5'), ('U11', '9'), ('U11', '10'), ('U11', '11'), ('D121', '4'), ('D121', '5'), ('D121', '6'),
                 ('U1', '37'), ('U1', '38'), ('U1', '29'), ('R11', '2'), ('U7', '2'), ('R142', '2'), ('R91', '2'),
                 ('U1', '94'),                         # (R5 just south of pin 94)
                 ('R87', '1'),                         # (the QSPI lines boxed in R87's USB_LIMITED pin)
                 ('U1', '7')]                          # (east, toward U12: its link took the west way, through
                                                       # the only gap C25's GND track has, and cut that off)


KEEP_VIAS = set()                                     # fan-out vias the autorouter continues from (kept as they are)


def early_escapes(b):
    done, failed = 0, []
    for ref, num in EARLY_ESCAPES:
        p = pad(b, ref, num)
        f = b.FindFootprintByReference(ref)
        lay = B if f.IsFlipped() else F
        net = next(q.GetNetname() for q in f.Pads() if q.GetNumber() == num)
        for extra in (0.9, 1.4, 2.0):
            e = escape(b, p, extra=extra)
            try:
                v = tie(b, net, p, e, lay, w=0.2, tries=6)
                KEEP_VIAS.add((round(v[0], 3), round(v[1], 3)))
                done += 1
                break
            except RuntimeError:
                continue
        else:
            failed.append(f'{ref}.{num}')
    print(f'  early escapes: {done} fan-out vias; none for {failed or "none"}')


def buck_loops(b):
    """The two buck converters' power loops, routed right after placement, before any other copper: input
    capacitor to VIN/GND, switch node to the inductor, bootstrap capacitor, output capacitors (AP63203/AP63301
    layout guidance: smallest loops first). Widths: 3V3 buck 0.5-0.6 mm, camera buck 0.8 mm (1 A), bootstrap 0.3 mm."""
    # 3V3 buck (U2, L1, C5 bootstrap, C7 input; C6 the second input capacitor)
    leg(b, 'VLOGIC', B, pad(b, 'C7', '1'), pad(b, 'U2', '3'), w=0.5, margin=2)
    leg(b, 'GND', B, pad(b, 'C7', '2'), pad(b, 'U2', '4'), w=0.5, margin=2)
    c72 = pad(b, 'C7', '2')                           # the loop's GND into the In1 plane at once: drawn later, the
    tie(b, 'GND', c72, (c72[0], c72[1] + 1.0), B, w=0.5)   # power links boxed it in and its pour island was cut off
    leg(b, 'VLOGIC', B, pad(b, 'U2', '2'), pad(b, 'U2', '3'), w=0.4, margin=2)
    leg(b, 'BST', B, pad(b, 'U2', '6'), pad(b, 'C5', '2'), w=0.3, margin=2)
    leg(b, 'SW_NODE', B, pad(b, 'U2', '5'), pad(b, 'C5', '1'), w=0.4, margin=2)
    leg(b, 'SW_NODE', B, pad(b, 'C5', '1'), pad(b, 'L1', '1'), w=0.6, margin=3)
    power_link(b, 'VLOGIC', pad(b, 'C6', '1'), pad(b, 'U2', '2'), 0.5, layers=(B,), wider=(B, F), margin=3)
    for r in (('C8', '1'), ('C9', '1')):              # the output capacitors on L1's 3V3 end
        power_link(b, '3V3', pad(b, *r), pad(b, 'L1', '2'), 0.6, layers=(B,), wider=(B, F), margin=4)
    # camera buck (U8, C72/C73 input, C74 bootstrap, L3, C75/C76 output)
    cin = 'CAM_INPUT_LIMITED'
    leg(b, cin, B, pad(b, 'U8', '3'), pad(b, 'U8', '2'), w=0.5, margin=1)
    leg(b, cin, B, pad(b, 'C72', '1'), pad(b, 'U8', '3'), w=0.8, margin=3)
    leg(b, cin, B, pad(b, 'C73', '1'), pad(b, 'C72', '1'), w=0.8, margin=3)
    leg(b, 'CAM_SW', B, pad(b, 'U8', '5'), pad(b, 'L3', '1'), w=0.8, margin=3)
    power_link(b, 'CAM_SW', pad(b, 'C74', '1'), pad(b, 'U8', '5'), 0.5, layers=(B,), wider=(B, F), margin=3)
    power_link(b, 'CAM_BST', pad(b, 'U8', '6'), pad(b, 'C74', '2'), 0.3, layers=(B,), wider=(B, F, IN2), margin=3)
    leg(b, 'CAM_5V', B, pad(b, 'L3', '2'), pad(b, 'C75', '1'), w=0.8, margin=3)
    leg(b, 'CAM_5V', B, pad(b, 'C75', '1'), pad(b, 'C76', '1'), w=0.8, margin=3)


U9_ESC = {}


def u9_escapes(b):
    """U9's IN and OUT are centre bars: each leaves straight out of its own end of the package (TI's layout; as R4)
    to a via. U9 sits turned 90 deg in the band: IN leaves west into the In2 BAT_IN strip, OUT east toward D9."""
    u5, u6 = pad(b, 'U9', '5'), pad(b, 'U9', '6')
    in_end, out_end = (u5[0] - 1.9, u5[1]), (u6[0] + 1.9, u6[1])
    route(b, 'BAT_IN', F, [u5, in_end], 0.3)
    route(b, 'RAW_PROTECTED', F, [u6, out_end], 0.3)
    U9_ESC['vin'] = tie(b, 'BAT_IN', in_end, (in_end[0], in_end[1] - 0.7), F, w=0.3)   # into the In2 strip
    U9_ESC['in_end'], U9_ESC['out_end'] = in_end, out_end
    U9_ESC['vout'] = tie(b, 'RAW_PROTECTED', out_end, (out_end[0] + 0.9, out_end[1] - 1.6), F, w=0.4)


def u9_network(b):
    """U9's control pins to their parts beside them, on F.Cu (TI's layout; as R4): U9's GND straight north to a GND via
    that R84 and C81 share; DVDT into C81; ILIM round R84's GND end (west) into its far end, where TP89 hangs; enable
    west to R81, C87 and R165; OVLO south-west to the divider R82/R83 under them; FLT south into R89. Then the vias:
    C88 and R81 to GND (R83 and C87 join R81's), R89 to the In2 3V3 plane. U9 sits turned 90 deg: ILIM/GND/DVDT face
    north, EN/OVLO/FLT south."""
    p = lambda r, n: pad(b, r, n)                    # noqa: E731
    vg = tie(b, 'GND', p('U9', '8'), (11.7, 17.5), F, w=0.2)             # straight north past R84's right side
    leg(b, 'BAT_DVDT', F, p('U9', '7'), p('C81', '1'), w=0.2, margin=2)     # 0.2 mm: the pins are 0.475 mm apart
    leg(b, 'BAT_ILIM', F, p('U9', '9'), p('R84', '1'), w=0.2, margin=2)     # west round R84's GND end
    leg(b, 'BAT_ILIM', F, p('TP89', '1'), p('R84', '1'), w=0.2, margin=2)
    for r in ('R84', 'C81'):
        leg(b, 'GND', F, p(r, '2'), vg, w=0.3, margin=3)
    tie(b, 'GND', p('C88', '2'), (8.35, 19.2), F, w=0.3)                   # west of the In2 BAT_IN strip
    leg(b, 'BAT_ENABLE', F, p('U9', '1'), p('R81', '1'), w=0.2, margin=3)
    leg(b, 'BAT_ENABLE', F, p('C87', '1'), p('R81', '1'), w=0.25, margin=2)
    leg(b, 'BAT_ENABLE', F, p('R165', '2'), p('C87', '1'), w=0.25, margin=2)
    leg(b, 'BAT_OVLO', F, p('U9', '2'), p('R82', '2'), w=0.2, margin=3)
    leg(b, 'BAT_OVLO', F, p('R83', '1'), p('R82', '2'), w=0.25, margin=2)
    leg(b, 'BAT_FAULT_N', F, p('U9', '4'), p('R89', '2'), w=0.2, margin=2)
    tie(b, 'GND', p('R81', '2'), (p('R81', '2')[0], p('R81', '2')[1] - 0.8), F, w=0.3)
    leg(b, 'GND', F, p('C87', '2'), p('R81', '2'), w=0.3, margin=2)      # (the load switch's gate run is below)
    leg(b, 'GND', F, p('R83', '2'), p('R81', '2'), w=0.3, margin=3)   # R83's corner: ACT_FET_S and RAW_ACT planes below
    tie(b, '3V3', p('R89', '1'), (p('R89', '1')[0] + 0.9, p('R89', '1')[1] + 0.3), F, w=0.25)


def power_main(b):
    """The main logic-supply paths, routed before the signals: RAW_PROTECTED from U9's OUT through D9 to U11's IN1,
    and VLOGIC from U11's OUT pins to the 3V3 buck's input and to the hold-up capacitor C84."""
    # RAW_PROTECTED (U9 OUT -> D9 -> U11 IN1): U11's west side carries it and VLOGIC
    out_end, vout = U9_ESC['out_end'], U9_ESC['vout']
    vd9 = tie(b, 'RAW_PROTECTED', pad(b, 'D9', '1'), (pad(b, 'D9', '1')[0] + 1.6, pad(b, 'D9', '1')[1] + 1.2), F, w=0.6)
    U9_ESC['vd9'] = vd9
    power_link(b, 'RAW_PROTECTED', vout, vd9, 0.6)
    power_link(b, 'RAW_PROTECTED', vd9, pad(b, 'U11', '2'), 0.6)
    # --- BAT_IN bulk capacitors, bleed resistor and test pad: into the In2 island's strip (before VLOGIC, which
    # would otherwise take their way across)
    # R80 (470 k, enable divider top) wherever the placer put it: to the battery terminal's BAT_IN pin
    power_link(b, 'BAT_IN', pad(b, 'R80', '1'), pad(b, 'J1', '1'), 0.25, layers=(B, F), wider=(B, F, IN2), margin=4)
    for r in ('C80', 'C96', 'R167', 'TP80'):
        rp = pad(b, r, '1')
        tie(b, 'BAT_IN', rp, (9.45, min(max(rp[1], 15.6), 36.0)), B, w=0.5)   # into the In2 island's strip
    # --- VLOGIC: U11 -> U2 (and its input capacitors) -> the hold-up capacitor C84 and the sense divider
    power_link(b, 'VLOGIC', pad(b, 'U11', '1'), pad(b, 'C7', '1'), 0.5, layers=(B,), wider=(B, IN2, F))   # west OUT pin
    # U11's two OUT pins sit on opposite sides: joined through the shortest way, vias allowed (a B.Cu loop round the
    # package would box in its other pins)
    multi(b, 'VLOGIC', pad(b, 'U11', '1'), pad(b, 'U11', '8'), 0.4, (B, IN2, F), via_cost=6.0, margin=3)
    v84 = tie(b, 'VLOGIC', pad(b, 'C84', '1'), (pad(b, 'C84', '1')[0] + 1.4, pad(b, 'C84', '1')[1] + 1.4), F, w=0.8)
    power_link(b, 'VLOGIC', v84, pad(b, 'U2', '2'), 0.5)
    # C84's GND pad to its own via (as R4): the In2 BAT_IN and RAW_ACT islands under it allow no via nearer, and the
    # pour alone was cut off from the plane in trial runs
    tie(b, 'GND', pad(b, 'C84', '2'), (11.0, 35.5), F, w=0.5)


def usb_limited(b):
    """USB_LIMITED (U10 -> U11, 0.5 A, 0.4 mm): routed before the signals, B.Cu and In2 with vias where the router
    finds room (the In2 area in front of U1 is fenced by the pyro lanes, and U11's surroundings on B.Cu are full)."""
    try:
        multi(b, 'USB_LIMITED', pad(b, 'U10', '6'), pad(b, 'U11', '7'), 0.4, (B, IN2), margin=6, via_cost=20.0)
    except RuntimeError:
        multi(b, 'USB_LIMITED', pad(b, 'U10', '6'), pad(b, 'U11', '7'), 0.4, (B, IN2, F), margin=9, via_cost=20.0)


def raw_act_link(b):
    """C121 (RAW_ACT bulk, top) to the J122 RAW pin column on F.Cu, between two signal pins (before the
    signal routes take the space in front of J122)."""
    leg(b, 'RAW_ACT', F, pad(b, 'C121', '1'), pad(b, 'J122', '8'), w=0.5)


def qspi_spi(b):
    """QSPI flash (U3, top, aft of U1) and the IMU's SPI1 (U4, bottom, forward-right of U1): 0.2 mm on F.Cu and
    B.Cu, the grid router choosing where to change layer (a via costs as much as 1.2 mm of track; In2 only if
    no path exists without it). QSPI runs at <= 80 MHz
    (docs/M3_R4.md section 3) over 8-25 mm, SPI1 at <= 10 MHz; both over the In1 GND plane."""
    # IMU end: a via fan under U4's pins on B.Cu (SCK straight out, CS and MOSI diagonally outward, MISO
    # sideways), so the four 0.5 mm-pitch escapes do not block each other
    fan = {}
    for net, pin, d in (('SPI1_SCK', '13', (0.0, 1.3)), ('IMU_CS', '12', (0.9, 1.7)),
                        ('SPI1_MOSI', '14', (-0.9, 1.7)), ('SPI1_MISO', '1', (-1.3, 0.0))):
        p = pad(b, 'U4', pin)
        fan[net] = tie(b, net, p, (p[0] + d[0], p[1] + d[1]), B, w=0.2)
    # QSPI first: its NCS pin (92) sits among SPI1's pins on U1's forward edge and must reach the flash aft
    # (IO3 before CLK: U3's west-facing column is IO0, CLK, IO3, VCC, and CLK turns south between IO0 and IO3, so
    # IO3 must leave its pin first; CLK then takes a via if it has to)
    q = [('QSPI_IO0', ('U1', '58'), ('U3', '5')), ('QSPI_IO3', ('U1', '60'), ('U3', '7')),
         ('QSPI_CLK', ('U1', '36'), ('U3', '6')), ('QSPI_IO1', ('U1', '59'), ('U3', '2')),
         ('QSPI_IO2', ('U1', '1'), ('U3', '3')), ('QSPI_NCS', ('U1', '92'), ('U3', '1'))]
    def sig(net, a, c):
        """F.Cu and B.Cu with vias where the grid router finds the shortest way (In2 only if that fails)."""
        try:
            multi(b, net, a, c, 0.2, (F, B), margin=8, via_cost=12.0)
        except RuntimeError:
            multi(b, net, a, c, 0.2, (F, B, IN2), margin=10, via_cost=12.0)
    for net, a, c in q:
        sig(net, pad(b, *a), pad(b, *c))
    for net, pin in (('IMU_CS', '93'), ('SPI1_MOSI', '91'), ('SPI1_MISO', '90'), ('SPI1_SCK', '89')):
        sig(net, pad(b, 'U1', pin), fan[net])                       # east-most pin first
    # the IMU's interrupt (U1 pin 40, on U1's aft row) with the SPI1 lines, before the decoupling and power copper
    # closes the IMU's corner: drawn later, no router found a way into it
    try:
        sig('IMU_INT1', pad(b, 'U1', '40'), pad(b, 'U4', '4'))
    except RuntimeError:
        SKIPPED.append(('IMU_INT1', ('U1', '40')))
    for net, a, c in (('QSPI_NCS', pad(b, 'R10', '1'), pad(b, 'U3', '1')), ('IMU_CS', pad(b, 'R11', '1'), fan['IMU_CS'])):
        try:                                          # pull-ups: scripted if they fit, else left to the autorouter
            multi(b, net, a, c, 0.2, (F, B, IN2), margin=6, via_cost=12.0)
        except RuntimeError:
            SKIPPED.append((net, a))


DECOUPLE_VIAS = {}


def sensor_links(b):
    """Before the signals: the IMU's second GND pin pair (6, 7) joined and taken north to a GND via clear of the
    no-via keep-out under the sensor; the I2C pull-ups straight into the barometer's pins (B.Cu, both parts on the
    bottom). Pins 2 and 3 reach GND through decoupling() as before."""
    leg(b, 'GND', B, pad(b, 'U4', '6'), pad(b, 'U4', '7'), w=0.2, margin=1)
    tie(b, 'GND', pad(b, 'U4', '7'), (pad(b, 'U4', '7')[0], pad(b, 'U4', '7')[1] - 1.1), B, w=0.2)
    for net, r, pin in (('I2C1_SCL', 'R12', '8'), ('I2C1_SDA', 'R13', '7')):
        try:
            leg(b, net, B, pad(b, r, '1'), pad(b, 'U5', pin), w=0.2, margin=3)
        except RuntimeError:
            print(f'  {net}: {r} to U5.{pin} left to the autorouter')
    try:                                              # the barometer's SDO to its resistor, before U5's GND ties
        leg(b, 'BARO_SDO', B, pad(b, 'U5', '6'), pad(b, 'R64', '1'), w=0.2, margin=3)
    except RuntimeError:
        print('  BARO_SDO: U5.6 to R64 left to the autorouter')


def slow_links(b):
    """Slow nets the autorouter left open in the trial runs, drawn before it: U7's fault output to R77, the pull-pin
    input (U1 pin 8 to its clamp D122 by J123, about 30 mm), U11's and U7's current-limit resistors (both pins boxed
    in by their neighbours), U11's soft-start capacitor and OVLO divider, the camera UART buffer's series
    resistors (U12's GND tie boxed in its RX pin), and
    plane vias for the 3V3 pull-ups R10 (flash chip select) and R91 (U11 status). Tolerant: what does not fit is
    left to the autorouter."""
    # U7's south pins, beside J121's igniter pin: OUT leaves east (it is the end pin) at 0.3 mm and widens to 0.8 mm
    # into the camera buck's input capacitor; then FLT straight out (south) to a via and on F.Cu up to its pull-up R77
    # on the top; ILIM (below) takes what is left, vias allowed
    u75 = pad(b, 'U7', '5')
    e75 = (round(u75[0] + 0.7, 4), u75[1])
    route(b, 'CAM_INPUT_LIMITED', B, [u75, e75], 0.3)
    power_link(b, 'CAM_INPUT_LIMITED', e75, pad(b, 'C73', '1'), 0.8, layers=(B,), wider=(B, IN2, F), margin=3)
    u76 = pad(b, 'U7', '6')
    vf = tie(b, 'CAM_FLT_RAW', u76, (u76[0], u76[1] + 0.9), B, w=0.2)
    leg(b, 'CAM_FLT_RAW', F, vf, pad(b, 'R77', '2'), w=0.2, margin=3)
    for net, a, c in (('PULLPIN', ('U1', '8'), ('D122', '3')), ('LOGIC_ILIM', ('U11', '10'), ('R86', '1')),
                      ('LOGIC_SS', ('U11', '11'), ('C85', '1')), ('USB_OVLO', ('R87', '2'), ('R88', '1')),
                      ('USB_OVLO', ('R88', '1'), ('U11', '5')), ('CAM_ILIM', ('U7', '7'), ('R70', '1')),
                      ('CAM_RX_BUFFER', ('U12', '1'), ('R100', '2')), ('CAM_TX_BUFFER', ('U12', '8'), ('R101', '1'))):
        try:
            multi(b, net, pad(b, *a), pad(b, *c), 0.2, (F, B, IN2), via_cost=10.0, margin=6)
        except RuntimeError:
            print(f'  {net} left to the autorouter')
    for r in ('R10', 'R91'):
        rp = next(q for q in b.FindFootprintByReference(r).Pads() if q.GetNetname() == '3V3')
        p = (round(mm(rp.GetPosition().x), 4), round(mm(rp.GetPosition().y), 4))
        try:
            tie(b, '3V3', p, escape(b, p, extra=0.6) or p, B if rp.IsOnLayer(B) else F, w=0.25, tries=8)
        except RuntimeError:
            print(f'  {r} 3V3 via left to the autorouter')


# the decoupling capacitors' returns (DECOUPLE_PAIRS), the eFuses' current-limit, soft-start and dV/dt parts, the
# USB CC pull-downs and the pyro sense divider whose pour corner gets boxed in; then the ICs (a pin with no room for
# a via joins its capacitor's GND pad, which by then has its own)
GND_PIN_EARLY = ('U1',)            # the MCU's VSS pins, with the decoupling vias, before the signals
GND_PIN_PARTS = ('C13', 'C14', 'C15', 'C16', 'C17', 'C18', 'C21', 'C22', 'C23', 'C29', 'C30', 'C31', 'C32',
                 'R86', 'C85', 'R70', 'C70', 'R84', 'C81', 'R7', 'R8', 'R142',
                 'U2', 'U3', 'U4', 'U5', 'U7', 'U8', 'U9', 'U10', 'U11', 'U12', 'U13', 'D121')   # after the power copper
GND_PIN_TRACK = ('C25',)          # a track to a GND via already placed, before the long links: after them the
                                   # servo and camera links boxed in the crystal's load capacitor
GND_PIN_LAST = ('R5',)            # after the long links: drawn before them, BOOT0's pull-down cut off the I2C pair


def _reaches_gnd_via(b, pad):
    """The pad's own GND copper (tracks end to end and the GND pads they reach; the pours left out) reaches a GND via
    or a through-hole GND pin."""
    tol = MM(0.01)
    segs = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'GND']
    vias = [v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND']
    pads = [q for f in b.GetFootprints() for q in f.Pads() if q.GetNetname() == 'GND']
    seen_pads, seen_segs = {pad.m_Uuid.AsString()}, set()
    todo = [pad]
    while todo:
        o = todo.pop()
        if isinstance(o, pcbnew.PAD):
            if o.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                return True
            hit = lambda q: o.HitTest(q)  # noqa: E731
        else:
            hit = lambda q, o=o: (q - o).EuclideanNorm() < tol  # noqa: E731
        if any(hit(v.GetPosition()) for v in vias):
            return True
        for s in segs:
            u = s.m_Uuid.AsString()
            if u in seen_segs:
                continue
            for e1, e2 in ((s.GetStart(), s.GetEnd()), (s.GetEnd(), s.GetStart())):
                if hit(e1):
                    seen_segs.add(u)
                    todo.append(e2)
                    break
        if not isinstance(o, pcbnew.PAD):
            for q in pads:
                if q.m_Uuid.AsString() not in seen_pads and q.HitTest(o):
                    seen_pads.add(q.m_Uuid.AsString())
                    todo.append(q)
    return False


def _gnd_via_near(b, p, own):
    """A GND via beside pad p (stub on its own layer), as _via_for, but never where an existing GND track ends inside
    the via off its centre (DRC: track not centred on via)."""
    ends = [(mm(q.x), mm(q.y)) for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'GND'
            for q in (t.GetStart(), t.GetEnd())]
    for e in [escape(b, p, extra=x) for x in (0.9, 1.7, 2.5)] + [p]:
        if e is None:
            continue
        tried = []
        for _ in range(6):
            try:
                v = via_spot(b, 'GND', e, p, r=0.8 if e is not p else 2.5, exclude=tried)
            except RuntimeError:
                break
            tried.append(v)
            if any(0.01 < math.hypot(v[0] - x, v[1] - y) < 0.45 for x, y in ends):
                continue
            before = {o.m_Uuid.AsString() for o in b.GetTracks()}
            try:
                leg(b, 'GND', own, p, v, w=0.25, margin=3)
            except RuntimeError:
                continue
            via(b, 'GND', v)
            new = [o for o in b.GetTracks() if o.m_Uuid.AsString() not in before]
            vias = [(mm(o.GetPosition().x), mm(o.GetPosition().y)) for o in b.GetTracks()
                    if o.GetClass() == 'PCB_VIA' and o.GetNetname() == 'GND']
            if any(0.01 < math.hypot(mm(q.x) - x, mm(q.y) - y) < 0.3 for o in new if o.GetClass() == 'PCB_TRACK'
                   for q in (o.GetStart(), o.GetEnd()) for x, y in vias):
                for o in new:                              # the stub ends inside another GND via, off its centre
                    b.Delete(o)
                continue
            return True
    return False


def gnd_pin_vias(b, parts=None, own_via=True):
    """Each GND pad of GND_PIN_PARTS whose own copper does not reach the In1 plane yet: its own via beside it (stub
    0.25 mm), or, with no room for one (or own_via False), a short track to a GND via or through-hole GND pin within 4 mm.
    Drawn after the critical and power routes and before the long slow links and the autorouter, which then route
    round them (power copper is hand-routed, AGENTS.md; drawn after the long links, 10 of these pads found no spot
    left). The outer GND pours alone may not reach a pad boxed in by traces: in the trial runs MCU VSS pins, U11's GND
    pins and several capacitors' returns were left on pour islands."""
    b.BuildConnectivity()
    done, failed = 0, []
    for ref in parts or GND_PIN_PARTS:
        for q in b.FindFootprintByReference(ref).Pads():
            if q.GetNetname() != 'GND' or q.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            if _reaches_gnd_via(b, q):                       # its own copper (not a pour) reaches the plane already
                continue
            p = (round(mm(q.GetPosition().x), 4), round(mm(q.GetPosition().y), 4))
            own = F if q.IsOnLayer(F) else B
            if own_via and _gnd_via_near(b, p, own):
                done += 1
                b.BuildConnectivity()
                continue
            # no room for a via: a track (F.Cu, B.Cu) to the nearest GND vias or through-hole GND pins within 4 mm
            tg = [(mm(v.GetPosition().x), mm(v.GetPosition().y), lay) for v in b.GetTracks()
                  if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND' for lay in (F, B)]
            tg += [(mm(c.GetPosition().x), mm(c.GetPosition().y), lay) for f in b.GetFootprints() for c in f.Pads()
                   if c.GetNetname() == 'GND' and c.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for lay in (F, B)]
            tg = [g for g in tg if math.hypot(g[0] - p[0], g[1] - p[1]) < 4.0]
            if tg:
                xs, ys = [p[0]] + [g[0] for g in tg], [p[1]] + [g[1] for g in tg]
                try:
                    runs, vs = maze_multi(b, 'GND', (F, B), p, tg[0][:2], w=0.25, a_layers={own},
                                          box=(min(xs) - 1.5, min(ys) - 1.5, max(xs) + 1.5, max(ys) + 1.5),
                                          via_cost=10.0, targets=tg)
                    for layer, pts in runs:
                        route(b, 'GND', layer, pts, 0.25)
                    for v in vs:
                        via(b, 'GND', v)
                    done += 1
                    b.BuildConnectivity()
                    continue
                except RuntimeError:
                    pass
            failed.append(f'{ref}.{q.GetNumber()}')
    print(f'  GND pin vias: {done}; none for {failed or "none"}')


def sense_mcu_links(b):
    """The pyro sense nets' MCU sides (pyro copper is hand-routed, AGENTS.md): each ADC series resistor's other pad
    (bottom, beside U1) to its MCU pin (top). Drawn after U1's supply pins have their decoupling vias
    (decoupling_vias), so a sense link never takes a decoupling via's spot, and before the signal fan-out."""
    for net, r, pin in (('PYRO1_CONT_MCU', 'R168', '15'), ('PYRO2_CONT_MCU', 'R169', '16'),
                        ('ARM1_SENSE_MCU', 'R170', '33'), ('ARM2_SENSE_MCU', 'R171', '32'),
                        ('RAW_ACT_SENSE_MCU', 'R172', '34')):
        for layers, m in (((F, B), 3), ((F, B), 6), ((F, B, IN2), 6)):
            try:
                multi(b, net, pad(b, 'U1', pin), pad(b, r, '2'), 0.2, layers, via_cost=10.0, margin=m)
                break
            except RuntimeError:
                continue
        else:
            print(f'  {net}: no scripted path from U1 pin {pin} to {r}')


# the long slow nets the autorouter left open in every trial run: SWD to J2 on the right edge, the servo lines from
# U1 to their clamp D121 (each about 30 mm across the board's busiest rows), the reset line to its capacitor and J2,
# the I2C pair to its pull-ups by the barometer (SCL first: the pair crosses on the way, and SDA then takes the outer
# path), the LED lines, the camera UART and its enable to the buffer U12, the logic-supply sense, the buzzer drive,
# and the power switch's return to J1
# SWCLK first, then the I2C pair, then SWDIO: drawn after SWDIO, SWCLK found no way to J2 in any trial (the router and
# the finisher then took it 80 mm round through the pyro block, or left it open), and SWDIO drawn before the I2C pair
# took I2C1_SDA's only way out of U1
LONG_LINKS = [('SWCLK', ('U1', '76'), ('J2', '2')),
              ('I2C1_SCL', ('U1', '95'), ('R12', '1')), ('I2C1_SDA', ('U1', '96'), ('R13', '1')),
              ('SWDIO', ('U1', '72'), ('J2', '3')),
              ('SERVO1_MCU', ('U1', '22'), ('D121', '1')), ('SERVO2_MCU', ('U1', '23'), ('D121', '3')),
              ('SERVO3_MCU', ('U1', '24'), ('D121', '4')), ('SERVO4_MCU', ('U1', '25'), ('D121', '6')),
              ('NRST', ('U1', '14'), ('C24', '1')), ('NRST', ('C24', '1'), ('J2', '4')),
              ('LED_YEL', ('U1', '37'), ('R33', '1')), ('LED_RED', ('U1', '38'), ('R32', '1')),
              ('CAM_MCU_TX', ('U1', '46'), ('U12', '5')), ('CAM_MCU_RX', ('U1', '47'), ('U12', '4')),
              ('CAM_UART_OE', ('U1', '7'), ('TP91', '1')),     # (to U12.6 it ran over R100.1 and cut off CAM_RX_WIRE;
                                                                # TP91 is on its way, U12.6 and R102 are left beside it)
              ('VLOGIC_SENSE', ('U1', '17'), ('R60', '2')),
              ('BUZZ_DRV', ('U1', '29'), ('R162', '1')),
              ('BAT_SW_RETURN', ('R165', '1'), ('J1', '4'))]


def long_links(b):
    """LONG_LINKS, after the decoupling and power copper (which they must not crowd out) and before the autorouter,
    0.15 mm like the autorouter's signals (the I2C pair leaves U1's pins between BOOT0's via and each other only at
    that width) and 0.02 mm over each clearance rule like the autorouter and r5_finish.py (DRC checks; at the
    scripted 0.05 mm, SWCLK, two servo lines and NRST found no way). Tolerant: what does not fit is left to the
    autorouter."""
    import r5_maze
    keep, r5_maze.MARGIN = r5_maze.MARGIN, 0.02
    try:
        _long_links(b)
    finally:
        r5_maze.MARGIN = keep


def _long_links(b):
    for net, a, c in LONG_LINKS:
        for margin in (6, 12):
            try:
                multi(b, net, pad(b, *a), pad(b, *c), 0.15, (F, B, IN2), via_cost=10.0, margin=margin)
                break
            except RuntimeError:
                continue
        else:
            if not _to_island(b, net, pad(b, *a), pad(b, *c), 0.15):
                print(f'  {net} left to the autorouter')


def _island_points(b, net, xy):
    """Grid targets (x, y, layer) on the copper already joined to the pad at xy: its pads, vias and track ends."""
    b.BuildConnectivity()
    f, q = _pad_at(b, xy)
    out = []
    for o in [q] + list(b.GetConnectivity().GetConnectedItems(q)):
        if o.GetNetname() != net:
            continue
        if o.GetClass() == 'PCB_TRACK':
            out += [(round(mm(e.x), 4), round(mm(e.y), 4), o.GetLayer()) for e in (o.GetStart(), o.GetEnd())]
        elif o.GetClass() in ('PCB_VIA', 'PAD'):
            p = o.GetPosition()
            out += [(round(mm(p.x), 4), round(mm(p.y), 4), lay) for lay in (F, B, IN2) if o.IsOnLayer(lay)]
    return out


def _to_island(b, net, a, c, w):
    """A long link that found no way to the pad itself: to any point of the copper already joined to it (a wider box),
    as the finisher does. True if drawn."""
    tg = _island_points(b, net, c)
    if not tg:
        return False
    xs, ys = [a[0]] + [q[0] for q in tg], [a[1]] + [q[1] for q in tg]
    f, pa = _pad_at(b, a)
    la = None if pa is None else {lay for lay in (F, B, IN2) if pa.IsOnLayer(lay)}
    for m in (6, 14):
        try:
            runs, vias = maze_multi(b, net, (F, B, IN2), a, c, w=w, a_layers=la, via_cost=10.0, targets=tg,
                                    box=(min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m))
        except RuntimeError:
            continue
        for layer, pts in runs:
            route(b, net, layer, pts, w)
        for v in vias:
            via(b, net, v)
        return True
    return False


def decoupling_vias(b):
    """Phase 1 of decoupling(), before the signals: each supply pin's own via beside it (stub 0.25 mm)."""
    for net, pin, caps in DECOUPLE_PAIRS:
        p = pad(b, *pin)
        own = F if F in _layers_at(b, p) else B
        v = _via_for(b, net, p, own, 0.25)
        leg(b, net, own, p, v, w=0.25, margin=3)
        via(b, net, v)
        DECOUPLE_VIAS[pin] = v


DECOUPLE_PAIRS = [('3V3', ('U1', '6'), [('C13', '1')]), ('3V3', ('U1', '11'), [('C14', '1'), ('C23', '1')]),
                  ('3V3', ('U1', '27'), [('C15', '1')]), ('3V3', ('U1', '50'), [('C16', '1')]),
                  ('3V3', ('U1', '75'), [('C17', '1')]), ('3V3', ('U1', '100'), [('C18', '1')]),
                  ('VCAP1', ('U1', '48'), [('C19', '1')]), ('VCAP2', ('U1', '73'), [('C20', '1')]),
                  ('3V3A', ('U1', '20'), [('C21', '1')]), ('3V3A', ('U1', '21'), [('C22', '1')]),
                  ('3V3', ('U3', '8'), [('C29', '1')]),
                  ('3V3A', ('U4', '5'), [('C30', '1')]), ('3V3A', ('U4', '8'), [('C31', '1')]),
                  ('3V3A', ('U5', '1'), [('C32', '1')])]


def decoupling(b):
    """Each MCU, flash and sensor supply pin: a via beside the pin (into the In2 3V3/3V3A fills) and a short
    stub to its own capacitor's supply pad on the bottom; VCAP1/2 to their capacitors. The capacitors' GND
    pads reach the In1 plane through the autorouter's fan-out vias."""
    pairs = DECOUPLE_PAIRS
    for net, pin, caps in pairs:
        v = DECOUPLE_VIAS[pin]
        for c in caps:
            cp = pad(b, *c)
            try:
                connect(b, net, cp, v, 0.3, (B, F, IN2), margin=4)
            except RuntimeError:
                SKIPPED.append((net, c))              # left to the autorouter, listed in the build log
    # 3V3 buck output (its capacitors joined in buck_loops): U2's sense pin and vias into the In2 3V3 fill
    # U2's FB pin (fixed 3.3 V version, an output sense) into the In2 3V3 plane through a via beside it, so its
    # line does not wrap round the buck's input loop
    u21 = pad(b, 'U2', '1')
    vfb = tie(b, '3V3', u21, (u21[0] - 0.8, u21[1] - 0.7), B, w=0.25)
    l2v = []
    for d in ((0.0, 2.3), (1.3, 1.8), (-1.3, 2.3)):     # south of the pad: the corridor north of L1 carries VLOGIC
        l2 = pad(b, 'L1', '2')
        l2v.append(tie(b, '3V3', l2, (l2[0] + d[0], l2[1] + d[1]), B, w=0.6))
    # ... and joined to L1's 3V3 end on copper as well: the autorouter's In2 traces can cut the 3V3 fill into
    # islands, and FB must see the output. A 3V3 track on In2 merges with the fill and no router copper crosses it
    # (F.Cu, over the In1 plane and away from the switch node below, if In2 has no way)
    try:
        connect(b, '3V3', vfb, l2v[0], 0.25, (IN2, F), margin=6)
    except RuntimeError:
        SKIPPED.append(('3V3', ('U2', '1')))
    # 3V3A: R164 (RC filter) and the bulk capacitors to the VDDA pins' via
    for net, r, to in (('3V3A', ('R164', '2'), ('C21', '1')), ('3V3A', ('C10', '1'), ('C21', '1')),
                       ('3V3A', ('C11', '1'), ('C21', '1')), ('3V3', ('R164', '1'), ('C14', '1'))):
        try:
            connect(b, net, pad(b, *r), pad(b, *to), 0.3, (B, F, IN2), margin=8)
        except RuntimeError:
            SKIPPED.append((net, r))


# 3V3 pads outside the In2 3V3 fill (it ends at x 34.5 and y 52.2): the I2C and IMU_CS pull-ups by the sensors, the
# servo clamp's reference, the camera UART buffer and SWD's VTref, and two pull-ups inside it with no room for a via
# of their own; each fed from the nearest plane via (power copper is hand-routed, AGENTS.md: left to the autorouter,
# these were cut off in trial runs)
FEED_3V3 = [('R12', '2'), ('R13', '2'), ('R11', '2'), ('D121', '5'), ('U12', '3'), ('J2', '5'),
            ('R91', '1'), ('R164', '1')]          # (inside the fill, but with no room for a via of their own)


def feed_3v3(b):
    """FEED_3V3, 0.25 mm on any layer to the nearest 3V3 via inside the In2 3V3 fill (tolerant)."""
    zone = next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == '3V3' and z.IsOnLayer(IN2))
    vias = [(round(mm(v.GetPosition().x), 4), round(mm(v.GetPosition().y), 4)) for v in b.GetTracks()
            if v.GetClass() == 'PCB_VIA' and v.GetNetname() == '3V3' and zone.Outline().Contains(v.GetPosition())]
    for r in FEED_3V3:
        p = pad(b, *r)
        for v in sorted(vias, key=lambda q: math.hypot(q[0] - p[0], q[1] - p[1]))[:4]:
            try:
                multi(b, '3V3', p, v, 0.25, (B, F, IN2), via_cost=10.0, margin=4)
                break
            except RuntimeError:
                continue
        else:
            SKIPPED.append(('3V3', r))


RETURN_NETS = ('USB_DP', 'USB_DM', 'HSE_IN', 'HSE_OUT', 'QSPI_CLK', 'QSPI_NCS', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2',
               'QSPI_IO3', 'SPI1_SCK', 'SPI1_MOSI', 'SPI1_MISO', 'IMU_CS')


def return_vias(b, reach=(1.5, 2.5)):
    """AGENTS.md: a ground via next to every layer change of the critical nets (USB, HSE, QSPI, SPI1): within
    1.5 mm of the signal via where one fits, else within 2.5 mm (one GND via may serve several); the rest are
    listed."""
    sig = [v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() in RETURN_NETS]
    tht = [(mm(q.GetPosition().x), mm(q.GetPosition().y)) for f in b.GetFootprints() for q in f.Pads()
           if q.GetNetname() == 'GND' and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    far, missing, by_pad = [], [], []
    for v in sig:
        p = (round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3))
        for k, r in enumerate(reach):
            gnd = [g for g in b.GetTracks() if g.GetClass() == 'PCB_VIA' and g.GetNetname() == 'GND']
            if any(math.hypot(mm(g.GetPosition().x) - p[0], mm(g.GetPosition().y) - p[1]) <= r for g in gnd):
                break
            try:
                via(b, 'GND', via_spot(b, 'GND', p, p, r=r))
                break
            except RuntimeError:
                continue
        else:
            # a through-hole GND pin (all four layers, In1 included) next to the via returns the current as well
            (by_pad if any(math.hypot(x - p[0], y - p[1]) <= reach[-1] for x, y in tht) else missing).append(
                (v.GetNetname(), p))
            continue
        if k:
            far.append((v.GetNetname(), p))
    print(f'  return vias: {len(sig)} critical vias; GND via 1.5-2.5 mm away: {far or "none"}; a through-hole GND '
          f'pin within 2.5 mm instead: {by_pad or "none"}; none: {missing or "none"}')

