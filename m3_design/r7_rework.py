#!/usr/bin/env python3
"""R7 review pass 2 rework of the routed board (after r7_route.py, before r7_post.py).

usage: <KiCad python3> -I m3_design/r7_rework.py [--board m3_design/assembly_review/m3.kicad_pcb] [--stop STAGE]

Fixes from the pass-2 reviews (sources/r7_review/pass2_*.md) to copper r7_route.py drew, made on the routed board item
by item: each stage deletes named copper (by exact end points, asserted) and draws its replacement from explicit
geometry, or places GND vias by a deterministic search. Every stage is deterministic (KIID seed 7401). Finding ids
refer to pass2_*.md; the records are sources/r7_review/fix2_F1_handoff.md and fix2_F2_handoff.md. (F1's stages for
the displaced nets themselves, TP89 / BAT_ILIM, BAT_FAULT_N and BUZZ_DRV, moved into r7_redraw.py when the router
replay was retired: their geometry is unchanged there.)
  returns  REGRESSION-01/03, RQ-01: GND vias beside QSPI_IO0's layer changes, D9.2, C80.2 and in the NRST-area
           B.Cu GND pour
  ...      cam_rx, rxen, tidy, widths, fb31, planes, iface_returns: see each stage
"""
import argparse
import math
from pathlib import Path
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
import r5_routes as rr  # noqa: E402
import r7_lib as lib  # noqa: E402
import r7_route as rt  # noqa: E402

MM, mm = pcbnew.FromMM, pcbnew.ToMM
F, B, IN1, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu
W = 0.15


def exact_ends(t):
    return [(mm(q.x), mm(q.y)) for q in (t.GetStart(), t.GetEnd())]


def gone(b, net, segs, vias=(), layer=None, why='', log=None):
    """Delete the tracks of net with these exact end points and the vias at these points (each must exist once)."""
    items = []
    for a, c in segs:
        hit = rt.find(b, net, a, c, cls='PCB_TRACK', layer=layer)
        if len(hit) > 1:                       # micro-segments: match both end points, in either order, to 10 nm
            def same(t):
                s, e = exact_ends(t)
                return (math.dist(s, a) < 1e-5 and math.dist(e, c) < 1e-5) or \
                    (math.dist(s, c) < 1e-5 and math.dist(e, a) < 1e-5)
            hit = [t for t in hit if same(t)]
        assert len(hit) == 1, (net, a, c, len(hit))
        items += hit
    for p in vias:
        hit = rt.find(b, net, p, cls='PCB_VIA')
        assert len(hit) == 1, (net, p, len(hit))
        items += hit
    rt.delete(b, items, why or f'{net}: old copper removed', log)


def gnd_via(b, want, near, r=1.2, d=0.6, log=None, label=''):
    """The GND via spot (ViaCheck rules, 0.05 mm grid) nearest `want` within r, scored by its largest distance to
    the points in `near` (the layer changes it serves); returns (spot, worst distance) or None."""
    chk = rt.ViaCheck(b)
    bare = [(p, lay) for f in b.GetFootprints() if f.GetReference().startswith('TP') for p in f.Pads()
            for lay in (F, B) if p.IsOnLayer(lay)]           # bare test pads keep 1.0 mm to foreign copper (check_r7)
    best = None
    n = int(r / 0.05)
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            q = (round(want[0] + 0.05 * i, 3), round(want[1] + 0.05 * j, 3))
            if math.dist(q, want) > r or not chk.ok(q, d):
                continue
            ring = pcbnew.SHAPE_CIRCLE(rr.P(*q), MM(d / 2))
            if any(p.GetNetname() != 'GND' and p.GetEffectiveShape(lay).Collide(ring, MM(1.02)) for p, lay in bare):
                continue
            score = max(math.dist(q, p) for p in near)
            if best is None or score < best[1] - 1e-9 or (abs(score - best[1]) < 1e-9 and math.dist(q, want) <
                                                          math.dist(best[0], want)):
                best = (q, score)
    if best:
        chk.add(best[0], d)
        if log is not None:
            log.append(f'GND via {label} at {best[0]} (d {d}): {best[1]:.2f} mm from {near}')
    elif log is not None:
        log.append(f'GND via {label}: no spot within {r} mm of {want}')
    return best


# --- GND returns ------------------------------------------------------------------------------------------------

def returns(b, log):
    io0 = [(12.9, 44.4), (15.55, 50.85)]
    for want, serve in (((13.7, 44.55), [io0[0]]), ((15.85, 50.1), [io0[1]])):
        spot = gnd_via(b, want, serve, r=0.6, log=log, label='QSPI_IO0')
        assert spot and spot[1] <= 1.0, spot
    # REGRESSION-03: D9.2 (U9 output Schottky anode, F.Cu) and C80.2 (BAT_IN input cap, B.Cu) lost their R6 vias.
    # D9.2: the only spot is the F.Cu pour between the pad's east end and BAT_SW_RETURN (0.5 mm via; the band holds
    # the north side, U2/VLOGIC/3V3 the copper under it); it also serves C6.2 on B.Cu
    # C80.2: R6's leftover stub from the pad into the pour (it led to a via R7 removed) goes; a via south-west of the pad
    gone(b, 'GND', [((7.675, 52.1), (7.675, 52.4612)), ((7.675, 52.4612), (8.2755, 53.0617)),
                    ((8.2755, 53.0617), (8.4255, 53.2117))], layer=B, why='GND: R6 stub at C80.2 removed', log=log)
    for label, want, pad_, d in (('D9.2', (19.65, 30.55), ('D9', '2'), 0.5), ('C80.2', (6.3, 53.05), ('C80', '2'), 0.6)):
        spot = gnd_via(b, want, [rr.pad(b, *pad_)], r=0.4, d=d, log=log, label=label)
        assert spot, label
    # REGRESSION-02: the B.Cu GND pour over NRST's In2 run (x 36.4-37.1, y 46.6-51) lost its only via (the island was
    # dropped by the filler); a via inside the pocket keeps it
    spot = gnd_via(b, (35.8, 50.6), [(37.135, 49.0), (36.435, 51.6)], r=0.8, log=log, label='NRST pour')
    assert spot, 'NRST pour'


# --- DFM-01 / REQUIREMENTS-03: CAM_RX_WIRE via out of R100.1 ---------------------------------------------------------

def cam_rx(b, log):
    gone(b, 'CAM_RX_WIRE', [((42.175, 56.65), (42.175, 56.2731)), ((43.3121, 55.136), (42.175, 56.2731)),
                            ((44.0481, 55.136), (43.3121, 55.136))], vias=[(42.175, 56.2731)],
         why='CAM_RX_WIRE: via in R100.1 removed', log=log)
    rr.route(b, 'CAM_RX_WIRE', B, [rr.pad(b, 'R100', '1'), (42.175, 55.82)], W)
    rr.via(b, 'CAM_RX_WIRE', (42.175, 55.82))
    rr.route(b, 'CAM_RX_WIRE', IN2, [(42.175, 55.82), (42.859, 55.136), (44.0481, 55.136)], W)
    log.append('CAM_RX_WIRE: via (42.175, 55.82), hole edge 0.205 mm outside R100.1\'s opening (was 0.248 mm inside)')


# --- RQ-12 / RG-11: RXEN off U3.5 and QSPI_CLK ------------------------------------------------------------------

def rxen(b, log):
    """RXEN's F.Cu leg under U3 ran at x 23.5, 0.175 mm beside QSPI_CLK for 4.3 mm, and its 45 degree leg passed U3.5
    at 0.165 mm: it now runs midway between QSPI_CLK and a 3V3 via and turns to its via (21.2, 30.45) aft of U3."""
    gone(b, 'RADIO_RXEN', [((23.8, 39.45), (23.5, 39.15)), ((23.5, 39.15), (23.5, 32.75)), ((23.5, 32.75), (21.2, 30.45))],
         layer=F, why='RADIO_RXEN: F.Cu beside QSPI_CLK and U3.5 removed', log=log)
    x = 23.575                  # midway between QSPI_CLK (x 23.15) and the 3V3 via (24.2, 35.3): 0.25 mm each
    rr.route(b, 'RADIO_RXEN', F, [(23.8, 39.45), (x, 39.45 - (23.8 - x)), (x, 31.45), (x - 1.0, 30.45), (21.2, 30.45)], W)
    log.append(f'RADIO_RXEN: F.Cu x {x} (0.25 mm from QSPI_CLK, was 0.175), aft of U3 along y 30.45 (1.2 mm from U3.5, '
               'was 0.165)')


# --- RG-11 / RQ-11: QSPI_IO0 corner, VBUS_SENSE jog -----------------------------------------------------------------

def tidy(b, log):
    gone(b, 'QSPI_IO0', [((15.55, 50.85), (12.9, 50.85)), ((12.9, 50.85), (12.9, 44.4))], layer=B,
         why='QSPI_IO0: B.Cu 90 degree corner', log=log)
    rr.route(b, 'QSPI_IO0', B, [(15.55, 50.85), (13.3, 50.85), (12.9, 50.45), (12.9, 44.4)], 0.2)
    gone(b, 'VBUS_SENSE', [((15.65, 53.0), (15.65, 53.2)), ((15.65, 53.2), (13.9949, 53.2)),
                           ((13.9949, 53.2), (13.6118, 53.5831))], layer=IN2,
         why='VBUS_SENSE: In2 0.2 mm jog and 90 degree corner', log=log)
    rr.route(b, 'VBUS_SENSE', IN2, [(15.65, 53.0), (14.1949, 53.0), (13.6118, 53.5831)], W)
    log.append('QSPI_IO0 corner chamfered (0.4 mm); VBUS_SENSE In2 straight from its via, one 45 degree leg')


# --- RQ-10: one width for the interface nets, collinear joints merged ------------------------------------------------
IFACE = ('RADIO_RXEN', 'RADIO_NRST', 'RADIO_DIO1', 'RADIO_TXEN', 'RADIO_NSS', 'RADIO_SCK', 'RADIO_SCK_MCU', 'RADIO_MOSI',
         'RADIO_MOSI_MCU', 'RADIO_MISO', 'RADIO_MISO_MCU', 'RADIO_BUSY', 'GNSS_TXD', 'GNSS_TXD_MCU', 'GNSS_RXD',
         'GNSS_RXD_MCU', 'GNSS_TIMEPULSE', 'GNSS_TP_MCU', 'GNSS_RESET_N')


def merge_collinear(b, nets):
    """Join two segments of a net that meet end to end in a straight line, with the same width and layer, where
    nothing else (another segment, a via or a pad) meets them. Returns the joints merged."""
    merged = 0
    while True:
        tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in nets]
        ends = {}
        for t in tracks:
            for q in (t.GetStart(), t.GetEnd()):
                ends.setdefault((t.GetLayer(), t.GetNetname(), q.x, q.y), []).append(t)
        vias = {(v.GetNetname(), v.GetPosition().x, v.GetPosition().y) for v in b.GetTracks()
                if v.GetClass() == 'PCB_VIA'}
        done = False
        for (lay, net, x, y), ts in ends.items():
            if len(ts) != 2 or ts[0].GetWidth() != ts[1].GetWidth() or (net, x, y) in vias:
                continue
            q = pcbnew.VECTOR2I(x, y)
            if any(p.GetNetname() == net and p.IsOnLayer(lay) and p.GetEffectiveShape(lay).Collide(q, 0)
                   for f in b.GetFootprints() for p in f.Pads()):
                continue
            a, c = ts
            pa = a.GetEnd() if a.GetStart() == q else a.GetStart()
            pc = c.GetEnd() if c.GetStart() == q else c.GetStart()
            cross = (q.x - pa.x) * (pc.y - q.y) - (q.y - pa.y) * (pc.x - q.x)
            dot = (q.x - pa.x) * (pc.x - q.x) + (q.y - pa.y) * (pc.y - q.y)
            if abs(cross) > 10 or dot <= 0:
                continue
            a.SetStart(pa)
            a.SetEnd(pc)
            b.Delete(c)
            merged += 1
            done = True
            break
        if not done:
            return merged


def widths(b, log):
    n = 0
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in IFACE and t.GetWidth() > MM(W) + 10:
            t.SetWidth(MM(W))
            n += 1
    m = merge_collinear(b, set(IFACE))
    log.append(f'interface nets: {n} segments 0.2 -> {W} mm (one width, pads included); {m} collinear joints merged')


# --- RQ-03: FB31's 3V3 feed ---------------------------------------------------------------------------------------

def fb31(b, log):
    """FB31 took 3V3 through R161.1's pad (a 10 k pull-up), a 0.2 mm neck and a 7.3 mm In2 U-turn to a plane 1.2 mm
    from its via. Now: one 0.4 mm F.Cu feed from FB31.1 to that via, which a small lobe of the In2 3V3 plane reaches
    (planes stage), and R161.1 tapped off the feed."""
    gone(b, '3V3', [((35.1, 22.15), (35.1, 25.1)), ((35.1, 25.1), (35.1, 26.6)), ((35.03, 26.8), (35.03, 27.3417)),
                    ((35.03, 27.3417), (35.73, 27.3417))], layer=F, why='3V3: FB31 feed through R161.1 removed', log=log)
    # (R6's In2 U-turn from that via to the plane goes in r7_redraw.vlogic_sense: C60.1's link takes its place)
    rr.route(b, '3V3', F, [rr.pad(b, 'FB31', '1'), (35.1, 24.6), (35.73, 25.23), (35.73, 26.8), (35.73, 27.3417)], 0.4)
    rr.route(b, '3V3', F, [rr.pad(b, 'R161', '1'), (35.73, 26.8)], 0.4)
    log.append('3V3: FB31.1 -> F.Cu 0.4 mm 5.2 mm -> via (35.73, 27.34) in the In2 3V3 lobe; R161.1 tapped')


# --- RQ-02 / RQ-13: In2 GND under the radio/GNSS B.Cu runs forward of the strip -------------------------------------

def outline(z, pts):
    o = z.Outline()
    o.RemoveAllContours()
    o.NewOutline()
    for x, y in pts:
        o.Append(MM(x), MM(y))


def planes(b, log):
    named = {z.GetZoneName(): z for z in b.Zones()}
    # In2 GND (R7_GND_In2_strip) grows forward of the strip: under NRST's and DIO1's B.Cu runs at y 24.0-24.5 (x 14.3-41;
    # RQ-02), under the GNSS rows at y 24.1-25.75 (x 0.3-14.3; RQ-13), up to BAT_IN and the 3V3 lobe, and on along the
    # left-edge B.Cu corridor (x 0.3-6.9 to y 53.1; RQ-14), whose 11 lanes referenced the In2 BAT_IN plane
    outline(named['R7_GND_In2_strip'], [(0.3, 0.3), (45.7, 0.3), (45.7, lib.STRIP_Y), (41.0, lib.STRIP_Y), (41.0, 24.75),
                                        (14.3, 24.75), (14.3, 25.0), (9.6, 25.0), (9.6, 25.9), (6.9, 25.9),
                                        (6.9, 53.1), (0.3, 53.1)])
    # BAT_IN In2 keeps its arm along x 7.2-9.9 past the corridor (J1 -> U9.5: 10.6 -> about 13.3 mOhm, DC solve; the
    # 7.7 A J1 -> Q120 path is elsewhere and unchanged); the BAT_IN_F pour's two stitch vias move onto it
    outline(named['R6_BAT_IN_In2'], [(7.2, 26.0), (9.9, 26.0), (9.9, 80.0), (14.0, 84.1), (14.0, 106.6), (32.2, 106.6),
                                     (32.2, 115.5), (8.9, 115.5), (8.9, 112.0), (0.3, 112.0), (0.3, 53.4), (7.2, 53.4)])
    gone(b, 'BAT_IN', [], vias=[(4.6, 26.6), (5.9, 26.6)], why='BAT_IN: BAT_IN_F stitch vias over the corridor', log=log)
    for q in ((7.6, 26.6), (8.8, 26.6)):
        rr.via(b, 'BAT_IN', q)
    # 3V3 In2: FB30's lobe starts at y 25.4 (was 23.9: RESET_N's row now has GND under it), and a lobe reaches FB31's
    # feed via at (35.73, 27.34) (RQ-03)
    outline(named['3V3_In2'], [(9.9, 25.4), (14.0, 25.4), (14.0, 27.0), (35.9, 27.0), (36.4, 27.5), (36.4, 27.9),
                               (34.5, 27.9), (34.5, 70.2), (14.0, 70.2), (14.0, 79.5), (8.9, 79.5), (8.9, 70.2),
                               (9.2, 70.2), (9.2, 27.0), (9.9, 27.0)])
    log.append('In2 GND strip grown to y 24.75 (x 14.3-41), 25.0 (x 9.6-14.3), 25.9 (x 0.3-9.6) and along the corridor '
               '(x 0.3-6.9, to y 53.1); BAT_IN In2 from x 7.2 there, BAT_IN_F stitch vias at (7.6, 26.6), (8.8, 26.6); '
               '3V3 lobes: FB30 from y 25.4, FB31 feed via (34.5-36.4, 27.0-27.9)')


# --- RG-05 / RQ-01: GND vias beside the interface layer changes --------------------------------------------------
# (group, [(net, via)]): each group's vias share the GND vias placed for it
IFACE_VIAS = [
    ('U1 escape column', [('RADIO_NSS', (9.3, 47.5)), ('RADIO_SCK_MCU', (10.0, 48.0)), ('RADIO_MOSI_MCU', (9.4, 48.5)),
                          ('RADIO_MISO_MCU', (10.7, 48.5)), ('RADIO_BUSY', (10.0, 49.5)), ('RADIO_NRST', (9.3, 50.0)),
                          ('RADIO_DIO1', (10.0, 50.5))]),
    ('band column', [('RADIO_DIO1', (9.4, 27.2)), ('RADIO_NRST', (10.0, 27.7)), ('RADIO_BUSY', (9.4, 28.2)),
                     ('RADIO_MISO_MCU', (10.0, 28.7)), ('RADIO_MOSI', (9.4, 29.2)), ('RADIO_SCK', (10.0, 29.7)),
                     ('RADIO_NSS', (9.4, 30.2))]),
    ('GNSS corridor head', [('GNSS_TP_MCU', (2.7, 51.0)), ('GNSS_RXD_MCU', (2.2, 51.5)), ('GNSS_TXD_MCU', (1.7, 52.0)),
                            ('GNSS_RESET_N', (1.2, 52.5))]),
    ('GNSS strip entry', [('GNSS_TXD_MCU', (7.11, 24.65)), ('GNSS_RXD', (8.21, 25.2)), ('GNSS_TP_MCU', (9.31, 25.75)),
                          ('GNSS_RESET_N', (14.3, 24.1))]),
    ('radio band turns', [('RADIO_DIO1', (18.4, 24.0)), ('RADIO_NRST', (19.0, 24.5)), ('RADIO_NRST', (40.0, 24.5))]),
    ('RXEN', [('RADIO_RXEN', (20.6, 27.05)), ('RADIO_RXEN', (21.2, 30.45)), ('RADIO_RXEN', (23.8, 39.45)),
              ('RADIO_RXEN', (21.2, 44.45))]),
]


def iface_returns(b, log, limit=1.0, step=0.1):
    """Greedy: the GND via spot (ViaCheck rules, bare-pad clearance) within `limit` of the most layer changes that have
    none yet, until no spot serves another; then every layer change's nearest GND via is logged (the record lists
    the ones left beyond `limit`)."""
    chk = rt.ViaCheck(b)
    bare = [(p, lay) for f in b.GetFootprints() if f.GetReference().startswith('TP') for p in f.Pads()
            for lay in (F, B) if p.IsOnLayer(lay)]

    def fits(q):
        if not chk.ok(q, 0.6):
            return False
        ring = pcbnew.SHAPE_CIRCLE(rr.P(*q), MM(0.3))
        return not any(p.GetNetname() != 'GND' and p.GetEffectiveShape(lay).Collide(ring, MM(1.02)) for p, lay in bare)

    def gnd():
        return [(mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in b.GetTracks()
                if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    for group, items in IFACE_VIAS:
        for net, q in items:
            assert rt.find(b, net, q, cls='PCB_VIA'), (net, q)
        pts = [q for _, q in items]
        added = []
        for lim in (limit, 1.5):        # within 1.0 mm where a spot exists, else within M3_R5's 1.5 mm criterion
          while True:
            have = gnd()
            open_ = [q for q in pts if min(math.dist(q, g) for g in have) > lim]
            if not open_:
                break
            cands = {}
            n = int(lim / step)
            for q in open_:
                for j in range(-n, n + 1):
                    for i in range(-n, n + 1):
                        c = (round(q[0] + step * i, 2), round(q[1] + step * j, 2))
                        if c not in cands and math.dist(c, q) <= lim:
                            cands[c] = None
            best = None
            for c in cands:
                served = [q for q in open_ if math.dist(c, q) <= lim]
                if not served:
                    continue
                key = (len(served), -sum(math.dist(c, q) for q in served))
                if best is None or key > best[0]:
                    if fits(c):
                        best = (key, c)
            if best is None:
                break
            chk.add(best[1], 0.6)
            added.append(best[1])
        have = gnd()
        far = {f'{net}{q}': round(min(math.dist(q, g) for g in have), 2) for net, q in items}
        log.append(f'{group}: GND vias {added}; nearest GND via per layer change (mm): {far}')


STAGES = [('returns', returns), ('cam_rx', cam_rx), ('rxen', rxen),
          ('tidy', tidy), ('widths', widths), ('fb31', fb31), ('planes', planes), ('iface_returns', iface_returns)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--stop', help='stop after this stage (debugging)')
    args = ap.parse_args()
    pcbnew.KIID.SeedGenerator(7401)
    b = pcbnew.LoadBoard(str(args.board))
    log = []
    for name, fn in STAGES:
        fn(b, log)
        print(f'[{name}]', *log, sep='\n  ')
        log.clear()
        if args.stop == name:
            break
    lib.fill(b)
    pcbnew.SaveBoard(str(args.board), b, True)
    print('saved', args.board)


if __name__ == '__main__':
    main()
