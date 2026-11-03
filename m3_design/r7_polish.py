#!/usr/bin/env python3
"""R7 review pass 3, 4, 5, 6 and 7 fixes on the cleaned board (after r7_hygiene.py, before r7_post.py).

usage: <KiCad python3> -I m3_design/r7_polish.py [--board m3_design/assembly_review/m3.kicad_pcb] [--out PATH]
                                                  [--stop STAGE] [--start STAGE]

Fix passes 3 to 7 (sources/r7_review/pass3_*.md ... pass7_*.md and their verdicts; records: fix3_F4_handoff.md,
fix4_F5_handoff.md, fix5_F6_handoff.md, fix6_F7_handoff.md, fix7_F8_handoff.md). The board's
.kicad_pro / .kicad_dru must sit beside it (the pours are refilled with the board's own rules after every stage). As in
r7_hygiene.py, every stage keeps each net's pad groups with the pours joining exactly as they were, and by tracks and
vias alone they may only merge, never split (tools/route_check.pad_groups; the run stops on the first stage that breaks
this; fix pass 6's raw_act6 and fix pass 7's dup7 delete tracks that duplicate their pour and assert that split themselves, SPLIT_OK); hand edits delete asserted copper (exact end points or counted boxes, so a changed upstream board stops the build)
and draw asserted 0/45/90 polylines checked against every other net's copper (r7_hygiene.Clearance: m3.kicad_dru incl.
the pyro rules, bare test pads 1.0 mm, Tag-Connect 0.508 mm; fix pass 6: and 0.26 mm from every non-plated hole); new
or moved vias also pass r7_route.ViaCheck.
Deterministic (KIID seed 7601). Stages, in order (each one's docstring holds its measured reasons):
  dead          dead copper under tools/route_check.dead's pour-island rule (P3-ROUTING_GEOMETRY-03): copper floating in
                one pour island and stubs ending in a pour (40 tracks)
  neck          a width step the dead stage left at a former T
  swd           SWCLK and SWDIO rerouted off In1 and out of the pyro block (P3-REQUIREMENTS-01 option (a)); two vias move
  pyro_corners  PYRO1_GATE_N's 83 um hook, PYRO1_COLD's kink, the GND corner by C126.2
  pyro1_cont    PYRO1_CONT rerouted (fix pass 4: the 6-via plane-preserving route, off the SPI1 bundle and the In2 3V3
                island, >= 1 mm from PYRO1_GATE_N), GND return vias
  corners       short segments on 3V3 / RAW_PROTECTED / GND copper (C17.1, R164 branch, D9.1, J3, C8.2)
  l1_node       the L1.2 3V3 node (P3-ROUTING_GEOMETRY-04)
  gnd_moves     two GND vias nudged for RADIO_RXEN / GNSS_RXD_MCU, a GND via by C160.2 / D122.1 (P3-REGRESSION-02)
  dead2         dead copper the reroutes left (a 3V3 In2 link now inside one island)
  band          fix pass 4: two of the radio band's four fan-in staircases (RADIO_NRST, RADIO_SCK)
  debris        fix pass 4: non-critical short segments and tiny jogs a simpler drawing clears (10 nets)
  reroutes      fix pass 4: CAM_UART_OE and NRST's J2 branch on simpler routes (6 -> 4 vias each; NRST off In1)
  band5         fix pass 5: the RADIO_BUSY / RADIO_MISO_MCU band staircases (allowlist A1, A2) removed
  qspi5         fix pass 5: RADIO_RXEN on its via column, QSPI_CLK's tiny jog removed (A5, D12)
  jogs5         fix pass 5: CAM_EN, CAM_FAULT_N / SERVO4_MCU, LOGIC_ILIM, CAM_RX_WIRE, CAM_TX_WIRE off In1 (D16),
                LOGIC_SOURCE_ST, CAM_5V_SENSE, PULLPIN_EXT, LED_RED: jogs (incl. through T / via nodes), staircases,
                a via hop and two vias that a clean redraw removes
  tidy5         fix pass 5: deviation-list part D items D1-D4, D7, D9-D11
  arm_gnd       fix pass 5: GND vias beside ARM1_SENSE's two layer changes (A17, A18)
  band_end      fix pass 5: In2 GND over the band end of the BAT_IN arm (the band-end split crossings)
  rf_relief     fix pass 4: C302.2 back on the house thermal relief (P4-RF-03)
  qspi6         fix pass 6: QSPI_IO3's inherited square bump straightened (P6-ROUTING_QUALITY-01)
  sw6           fix pass 6: SW_NODE C5.1 -> L1.1 without the tiny jog and the two short segments (allowlist A3-A5)
  logic_ss6     fix pass 6: LOGIC_SS's two-segment knee (P6-ROUTING_GEOMETRY-02)
  servo_fault6  fix pass 6: CAM_FAULT_N and SERVO4_MCU apart again (P6-REGRESSION-02)
  v3v3_6        fix pass 6: the 3V3 F.Cu dip round R6's C179.1 (P6-DOCS-01)
  raw_act6      fix pass 6: RAW_ACT's B.Cu duplicate of its pour J124.2 -> Q121 deleted (P6-DOCS-01)
  ties6         fix pass 6: poured-net runs route_check's chain_detour test finds and a straight / one-bend drawing
                replaces (P6-DOCS-01)
  bat_in_f6     fix pass 6: BAT_IN_F's via connection into In2 BAT_IN restored (P6-REGRESSION-01)
  bumps7        fix pass 7: local bumps on 3V3A, CAM_5V, VLOGIC and A34's 3V3 feed (P7-ROUTING-01)
  v3pair7       fix pass 7: the redundant 3V3 via (30.4, 70.25), its stub and two overlap-only joints (P7-DOCS-01)
  acten7        fix pass 7: ACT_EN's In2 hop onto B.Cu (C26)
  arm1_7        fix pass 7: ARM1_SENSE's run split at R180.1 (C24: its pass through the pad and its chain detour)
  tidy7         fix pass 7: CAM_FAULT_N's In2 bump and I2C1_SDA's run (C25; LED_RED's bump keeps QSPI_NCS's reference)
  sense7        fix pass 7: CAM_5V_SENSE's and SERVO2_OUT's In2 runs (P7-ROUTING-02)
  bat_via7      fix pass 7: fix pass 6's BAT_IN via onto its track's line, the track split there (P7-ROUTING-03)
  v3a_hop7      fix pass 7: the 3V3A hop's fix-pass-5 drawing back (P7-ROUTING-04 / P7-REGRESSION-02)
  bat_in_b7     fix pass 7: BAT_IN_B's lobe fenced off again (P7-REGRESSION-01)
  dup7          fix pass 7: two 3V3 hops that duplicate the 3V3_In2 plane (P7-DOCS-02 (b), C23)
  review7       fix pass 7: non-critical bumps route_check --bumps-all finds (BUZZ_DRV, IMU_INT1)
  necks7        fix pass 7: the 7.7 A necks widened by local rework (C1)
  gnd_vias      fix pass 4: r7_hygiene.gnd_vias (+ its 0.025 mm fine pass) on the final signal copper: the GND via
                beside PYRO1_GATE_N's layer change (P4-ROUTING_GEOMETRY-01)
  pour_trim     zone-fill keep-out rule areas over every pour sliver (< 0.25 mm, > 3 mm) and unstitched GND finger
                (< 0.5 mm, > 3 mm, > 4 mm of copper from a GND via) left after all copper changes (P3-RF-01); a pad's
                relief ring is never kept out, and no pad loses its last pour contact (P4-REGRESSION-02, asserted)
  strip_stitch  GND vias until every F.Cu / B.Cu GND copper point of the RF strip is within 4 mm of copper of a via
  edge_stitch   fix pass 5: the same for the board's forward end (y >= 112; deviation D15)
  gnd_pieces    fix pass 5: a second GND via in the four pour pieces fix pass 4 left with one (P5-REGRESSION-02)
  gnd_vias2     the GND via search again after the last copper change (nothing to add, asserted)
  pour_trim2    the trim again (nothing left)
"""
import argparse
import math
from pathlib import Path
import sys
import time

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import r7_lib as lib  # noqa: E402
import r7_hygiene as hy  # noqa: E402
import route_check as rc  # noqa: E402

MM, mm = pcbnew.FromMM, pcbnew.ToMM
F, B, IN1, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu
LAYERS = {'F': F, 'In1': IN1, 'In2': IN2, 'B': B}
PROTECTED = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
TOL = rc.TOL


def V(p):
    return pcbnew.VECTOR2I(int(round(p[0])), int(round(p[1])))


def P(x, y):
    return MM(x), MM(y)


def near(p, q, tol=2000):
    return math.dist(p, q) <= tol


def tracks_of(b, net, layer=None):
    return [t for t in hy.tracks(b) if t.GetNetname() == net and (layer is None or t.GetLayer() == LAYERS[layer])]


def vias_of(b, net):
    return [t for t in hy.vias(b) if t.GetNetname() == net]


def find_track(b, net, layer, a, c):
    """The one track of net on layer with end points a, c (mm, either order, within 2 um)."""
    A, C = P(*a), P(*c)
    hit = [t for t in tracks_of(b, net, layer) if (near(hy.xy(t.GetStart()), A) and near(hy.xy(t.GetEnd()), C)) or
           (near(hy.xy(t.GetStart()), C) and near(hy.xy(t.GetEnd()), A))]
    assert len(hit) == 1, (net, layer, a, c, len(hit))
    return hit[0]


def find_via(b, net, p):
    hit = [v for v in vias_of(b, net) if near(hy.xy(v.GetPosition()), P(*p))]
    assert len(hit) == 1, (net, p, len(hit))
    return hit[0]


NPTH_GAP = 0.27             # mm: via copper to a non-plated hole (m3.kicad_dru copper to hole 0.25, + 0.02)


def npth_ok(b, p, d):
    """Whether a via at p (mm), diameter d, keeps NPTH_GAP from every non-plated hole (the JLC tooling holes):
    r7_route.ViaCheck tests hole to hole only, and a non-plated pad has no copper for the clearance tests."""
    for f in b.GetFootprints():
        for q in f.Pads():
            if q.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                r = mm(max(q.GetDrillSize().x, q.GetDrillSize().y)) / 2
                if math.dist(p, (mm(q.GetPosition().x), mm(q.GetPosition().y))) < r + d / 2 + NPTH_GAP:
                    return False
    return True


def check_via(b, net, p, d, clr=None, skip_hole=None):
    """Assert a via of net at p (mm), diameter d, keeps every clearance (Clearance on all four layers, hole clearance,
    copper to non-plated holes) and passes r7_route.ViaCheck (a via being moved is left out of the hole list:
    skip_hole)."""
    import r7_route as rt                       # noqa: E402 (heavy import, only here)
    clr = clr or hy.Clearance(b)
    q = P(*p)
    for l in hy.CU4:
        bad = clr.why(net, l, q, q, MM(d))
        assert bad is None, ('via clearance', net, p, b.GetLayerName(l), bad)
    chk = rt.ViaCheck(b, net)
    if skip_hole is not None:
        chk.holes = [h for h in chk.holes if math.dist((h[0], h[1]), skip_hole) > 1e-4]
    assert chk.ok(p, d), ('via keep-out / edge / paste / hole', net, p)
    assert npth_ok(b, p, d), ('via copper too near a non-plated hole', net, p)


def draw(b, net, layer, w, pts, clr):
    """Draw the polyline pts (mm) of net on layer, width w mm; every segment asserted 0/45/90 and clear."""
    lay = LAYERS[layer]
    q = [P(*p) for p in pts]
    holes = [(hy.xy(f_p.GetPosition()), max(f_p.GetDrillSize().x, f_p.GetDrillSize().y) / 2)
             for f in b.GetFootprints() for f_p in f.Pads() if f_p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
    for a, c in zip(q, q[1:]):
        assert hy.direction(a, c) is not None, (net, 'not 0/45/90', hy.loc(a), hy.loc(c))
        bad = clr.why(net, lay, a, c, MM(w))
        assert bad is None, (net, layer, 'clearance', hy.loc(a), hy.loc(c), w, bad)
        for h, r in holes:                     # fix pass 6: copper to a non-plated hole (Clearance sees no copper)
            assert rc.pt_seg(h, a, c)[0] - r - MM(w) / 2 >= MM(rc.NPTH_CLEAR), \
                (net, layer, 'copper to NPTH hole', hy.loc(a), hy.loc(c), hy.loc(h))
        hy.new_track(b, net, lay, a, c, MM(w))
        clr.add_segment(net, lay, a, c, MM(w))
    return len(q) - 1


def add_via(b, net, p, d, clr=None):
    check_via(b, net, p, d, clr)
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(P(*p)))
    v.SetWidth(MM(d))
    v.SetDrill(MM(0.3))
    v.SetNet(b.FindNet(net))
    b.Add(v)
    return v


def move_via(b, net, old, new, d=None, log=None, why=''):
    """Move net's via at old to new (mm), dragging the track ends that sat on its centre; d changes its diameter.
    The moved via and every dragged track are checked."""
    v = find_via(b, net, old)
    O, N = P(*old), P(*new)
    dragged = [(t, e) for t in tracks_of(b, net) for e, q in enumerate(hy.ends(t)) if near(q, O)]
    d = d if d is not None else mm(v.GetWidth(F))
    v.SetPosition(V(N))
    v.SetWidth(MM(d))
    for t, e in dragged:
        (t.SetStart if e == 0 else t.SetEnd)(V(N))
    clr = hy.Clearance(b)
    check_via(b, net, new, d, clr, skip_hole=new)
    for t, e in dragged:
        a, c = hy.ends(t)
        assert hy.direction(a, c) is not None, (net, 'dragged track off 0/45/90', hy.loc(a), hy.loc(c))
        clr.gone.add(t.m_Uuid.AsString())
        bad = clr.why(net, t.GetLayer(), a, c, t.GetWidth())
        assert bad is None, (net, 'dragged track clearance', hy.loc(a), hy.loc(c), bad)
    if log is not None:
        log.append(f'  {net}: via {old} -> {new} ({d} mm), {len(dragged)} track ends dragged{": " + why if why else ""}')


def move_end(b, net, layer, old, new):
    """Move every end of net's tracks on layer that sits at old (mm) to new; returns the moved tracks."""
    O, N = P(*old), P(*new)
    moved = []
    for t in tracks_of(b, net, layer):
        for e, q in enumerate(hy.ends(t)):
            if near(q, O):
                (t.SetStart if e == 0 else t.SetEnd)(V(N))
                moved.append(t)
    assert moved, (net, layer, old)
    return moved


def check_tracks(b, items):
    clr = hy.Clearance(b)
    for t in items:
        clr.gone.add(t.m_Uuid.AsString())
    for t in items:
        a, c = hy.ends(t)
        assert hy.direction(a, c) is not None, (t.GetNetname(), 'off 0/45/90', hy.loc(a), hy.loc(c))
        bad = clr.why(t.GetNetname(), t.GetLayer(), a, c, t.GetWidth())
        assert bad is None, (t.GetNetname(), 'clearance', hy.loc(a), hy.loc(c), bad)


def reroute(b, log, jobs, w=0.15, dv=0.5):
    """Replace all copper of each net in jobs = [(net, n_tracks, n_vias, route)] (counts asserted) by its route =
    [('F'|'B'|'In2', [(x, y), ...]) | ('via', (x, y))] (mm): every net's old copper goes first, then the routes are
    drawn in order (each later one checked against the earlier ones)."""
    old = {}
    for net, n_tracks, n_vias, route in jobs:
        ts, vs = tracks_of(b, net), vias_of(b, net)
        assert (len(ts), len(vs)) == (n_tracks, n_vias), (net, len(ts), len(vs), n_tracks, n_vias)
        old[net] = sum(hy.length(t) for t in ts) / 1e6
        for t in ts + vs:
            b.Delete(t)
    for net, n_tracks, n_vias, route in jobs:
        clr = hy.Clearance(b)
        n, nv, L = 0, 0, 0.0
        for kind, geo in route:
            if kind == 'via':
                add_via(b, net, geo, dv, clr)
                clr = hy.Clearance(b)
                nv += 1
            else:
                n += draw(b, net, kind, w, geo, clr)
                L += sum(math.dist(p, q) for p, q in zip(geo, geo[1:]))
        log.append(f'  {net}: {n_tracks} tracks ({old[net]:.2f} mm) and {n_vias} vias -> {n} tracks ({L:.2f} mm) '
                   f'and {nv} vias')


# --- stages --------------------------------------------------------------------------------------------------------

DEAD_EXPECTED = {'dead': 40, 'dead2': 1}   # tracks each dead stage removes (asserted: a changed upstream board stops)


def dead(b, log, name='dead'):
    """P3-ROUTING_GEOMETRY-03: tools/route_check.dead now treats each pour fill island as one terminal, so copper whose
    only contacts are one island is dead (3V3 In2 (18.7, 51.9) -> (19.6, 51.6), floating), and so is a stub ending in a
    pour: a run from a track end touching nothing but its own pour back to the first junction, pad or via, when removing
    it leaves the net's pad groups with the pours joining exactly as they are (the pour already makes the joint). Whole
    tracks only, repeated until none is left; every removal is logged. The six the review saw standing outside the fill
    are among them (GND F.Cu (11.75, 37.025)-(10.65, 38.125), GND B.Cu (12.43, 78.6)-(10.43, 78.6), (30.80, 27.38)-
    (32.09, 28.67), (33.03, 27.68)-(32.59, 28.12), 3V3 In2 (26.4, 36.6)-(26.4, 38.47), (16.25, 31.1)-(20.95, 31.1)).
    The 3V3 In2 runs at L1 ((20.95, 31.1) -> (24.2, 34.35) -> (24.2, 35.3)) lie in the 3V3 plane island their vias
    already join (the DC solve in the record shows what they carried)."""
    removed = []
    for _ in range(10):
        n = 0
        for net, nc in sorted(rc.collect(b).items()):
            pieces, dvias = rc.dead(nc)
            whole = [i for i, segs in pieces.items() if sum(s1 - s0 for s0, s1 in segs) >= 1 - 1e-9]
            assert len(whole) == len(pieces), (net, 'partly dead track', [hy.loc(nc.tracks[i]['a']) for i in pieces])
            assert not any(net in PROTECTED for _ in whole), (net, 'protected pyro copper is never removed here')
            for i in whole:
                t = nc.tracks[i]
                removed.append(f'{net} {b.GetLayerName(t["lid"])} {hy.loc(t["a"])}-{hy.loc(t["b"])}')
                b.Delete(t['obj'])
                n += 1
            for j in dvias:
                removed.append(f'{net} via {hy.loc(nc.vias[j]["pos"])}')
                b.Delete(nc.vias[j]['obj'])
                n += 1
        lib.fill(b)
        if not n:
            break
    assert len(removed) == DEAD_EXPECTED[name], (name, len(removed), removed)
    log.append(f'{name}: {len(removed)} tracks removed')
    log.extend(f'  {r}' for r in removed)


SWDIO_ROUTE = [
    ('F', [(14.3, 58.0), (17.1, 58.0), (19.55, 55.55)]), ('via', (19.55, 55.55)),
    ('B', [(19.55, 55.55), (20.8, 56.8), (20.8, 63.2), (18.55, 65.45), (18.55, 73.1)]), ('via', (18.55, 73.1)),
    ('In2', [(18.55, 73.1), (26.7, 73.1), (30.15, 69.65), (30.85, 69.65)]), ('via', (30.85, 69.65)),
    ('B', [(30.85, 69.65), (33.43, 69.65)]), ('via', (33.43, 69.65)),
    ('F', [(33.43, 69.65), (41.7, 77.92), (42.15, 77.92)])]
SWCLK_ROUTE = [
    ('F', [(15.85, 61.05), (15.85, 60.0), (20.5, 55.35), (20.5, 52.95)]), ('via', (20.5, 52.95)),
    ('B', [(20.5, 52.95), (22.5, 50.95), (24.7, 50.95)]), ('via', (24.7, 50.95)),
    ('F', [(24.7, 50.95), (24.7, 50.3), (29.4, 45.6), (31.8, 45.6), (33.25, 47.05), (33.25, 52.15)]),
    ('via', (33.25, 52.15)),
    ('B', [(33.25, 52.15), (35.75, 54.65)]), ('via', (35.75, 54.65)),
    ('F', [(35.75, 54.65), (35.75, 58.15), (33.3, 60.6), (33.3, 68.8), (41.15, 76.65), (42.15, 76.65)])]


def swd(b, log):
    """P3-REQUIREMENTS-01 option (a): SWCLK (U1.76 -> J2.4, R6: 117.2 mm, 14 vias, 19.5 mm on the In1 GND plane, down
    through the pyro block to y 100) and SWDIO (U1.72 -> J2.2, 70.8 mm, 11 vias, 7.8 mm on In1, through the pyro block)
    rerouted. A raster A* search (0.05 mm grid, every clearance of the board, the crystal Y1/C25/C26 kept clear) over
    F/B/In2 found two corridors out of U1's SW corner, each one track wide:
      north: under U1's body, out of its NE corner between pins 25 and 26, down its east side (x 33-36), then one
             diagonal into J2.4 from the west: SWCLK, F/B only, 62.9 mm, 4 vias;
      south: B.Cu down x 18.55 beside USB_LIMITED's trunk, In2 between J122's first two rows (y 73.1, 0.33 mm to the
             RAW_ACT pins against the 0.3 mm rule; on F.Cu that run would cut the RAW_ACT_F servo pour) and under the
             SPI1/I2C1 bundle to the IMU, then one diagonal into J2.2 from the west: SWDIO, 53.9 mm, 4 vias.
    No more direct route exists on F/B (the bundle, J122 and QSPI_NCS's under-body run close every other way); neither
    line touches In1 or the pyro block any more. Two vias move to let both lines enter J2 cleanly: the 3V3 via
    (41.135, 77.92) 0.135 mm west along its own run (now 0.5/0.3 mm, as the board's other small vias; it feeds only J2.1)
    and SERVO1_MCU's via (34.6, 58.7) 0.2 mm north along its In2 run (its F.Cu diagonal moves with it), which leaves
    SWCLK's diagonal 0.566 mm from it. Both lines end 0.215 mm west of their J2 pad centres, inside the pads, as R6's
    did: J2's footprint keep-out (no tracks between the Tag-Connect contacts) starts at the pad centres."""
    move_via(b, '3V3', (41.135, 77.92), (41.0, 77.92), d=0.5, log=log, why='SWDIO enters J2.2 from the west')
    t = find_track(b, 'SERVO1_MCU', 'F', (34.6, 58.7), (31.2, 62.1))
    u = find_track(b, 'SERVO1_MCU', 'F', (31.2, 62.1), (28.5, 62.1))
    move_end(b, 'SERVO1_MCU', 'F', (31.2, 62.1), (31.0, 62.1))
    move_via(b, 'SERVO1_MCU', (34.6, 58.7), (34.6, 58.5), log=log, why='SWCLK passes between it and CAM_UART_OE')
    check_tracks(b, [t, u])
    reroute(b, log, [('SWDIO', 32, 11, SWDIO_ROUTE), ('SWCLK', 46, 14, SWCLK_ROUTE)])


PYRO1_CONT_LOCAL = [((27.87, 87.9), (27.87, 86.75)), ((26.83, 87.9), (27.87, 87.9)), ((26.83, 87.9), (26.83, 88.4217)),
                    ((26.83, 88.4217), (25.22, 88.4217)), ((25.22, 88.4217), (24.6, 87.8017)),
                    ((24.6, 87.2), (24.6, 87.8017))]
PYRO1_CONT_ROUTE = [            # fix pass 4 (P4-ROUTING_QUALITY-01 / P4-REGRESSION-01): the plane-preserving route
    ('B', [(33.03, 52.9), (35.78, 55.65), (35.78, 58.85)]), ('via', (35.78, 58.85)),
    ('In2', [(35.78, 58.85), (35.78, 60.65)]), ('via', (35.78, 60.65)),
    ('F', [(35.78, 60.65), (35.78, 65.25), (40.88, 70.35), (40.88, 74.75)]), ('via', (40.88, 74.75)),
    ('In2', [(40.88, 74.75), (41.63, 75.5), (41.63, 78.85)]), ('via', (41.63, 78.85)),
    ('F', [(41.63, 78.85), (35.73, 84.75), (34.68, 84.75)]), ('via', (34.68, 84.75)),
    ('In2', [(34.68, 84.75), (30.82, 88.61), (28.4, 88.61)]), ('via', (28.4, 88.61)),
    ('F', [(28.4, 88.61), (27.87, 88.08)])]
PYRO1_CONT_GATE_GAP = 1.0       # mm: minimum copper gap to PYRO1_GATE_N on any shared layer (asserted)


def pyro1_cont(b, log):
    """PYRO1_CONT (continuity sense, divider C127/R129/R130/R178 in the pyro block -> R168.1 at U1) ran 59.9 mm with 7
    vias in R6 / fix pass 2: an In2 run inside the BAT_IN servo-current pour (y 88.4), up the board's east edge round J2
    (In2 x 40.5, F.Cu x 42.22) and a staircase between SWDIO's old run and R77.1. The divider's local F.Cu copper stays;
    every other track and via of the net (29 items) goes.
    Fix pass 3 drew a 4-via route through the SPI1/I2C1 bundle; pass 4 (P4-ROUTING_QUALITY-01, P4-REGRESSION-01) found
    that its In2 diagonal cut the In2 3V3 island under U1/U4 in two (72.15 mm2 with 4 vias -> 41.93 + a 22.69 mm2
    fragment on one via), ran 7.4 mm beside SPI1_SCK at 0.195 mm and passed a PYRO1_GATE_N via at 0.191 mm.
    Fix pass 4 draws the plane-preserving route instead (raster search fx4/rt/pc7: every board clearance incl. the pyro
    rules and the Tag-Connect NPTH 0.508 mm, every power pour on every layer kept whole (3V3/3V3A included), 1.0 mm to
    PYRO1_GATE_N copper; hand-tidied: the router's 0.1 mm In2 jog by J2 became one diagonal collinear through its via, the
    pyro-block via moved 0.53 mm east so a legal GND return via lies within 1.5 mm): B.Cu east of U4 under SWCLK's F.Cu
    run, a 1.8 mm In2 hop under SWCLK's corner and CAM_UART_OE, F.Cu east of the IMU, an In2 hop under SWCLK/SWDIO's J2
    diagonals, F.Cu down to the pyro block, In2 under it into R129.2 (the divider node, from the south): 47.5 mm, 6 vias.
    No In2 run in a 3V3 / 3V3A / BAT_IN / RAW_ACT pour (the search blocks them); the copper gap to PYRO1_GATE_N is
    asserted >= 1.0 mm on every shared layer. Each layer change gets a GND via within 1.5 mm (gnd_spot, 0.6 then
    0.5 mm, where none is there already)."""
    for a, c in PYRO1_CONT_LOCAL:
        find_track(b, 'PYRO1_CONT', 'F', a, c)
    keep = {find_track(b, 'PYRO1_CONT', 'F', a, c).m_Uuid.AsString() for a, c in PYRO1_CONT_LOCAL}
    old = [t for t in tracks_of(b, 'PYRO1_CONT') if t.m_Uuid.AsString() not in keep] + vias_of(b, 'PYRO1_CONT')
    assert len(old) == 29, len(old)
    L0 = sum(hy.length(t) for t in old if t.GetClass() == 'PCB_TRACK') / 1e6
    for t in old:
        b.Delete(t)
    clr = hy.Clearance(b)
    n = 0
    L1 = 0.0
    for kind, geo in PYRO1_CONT_ROUTE:
        if kind == 'via':
            add_via(b, 'PYRO1_CONT', geo, 0.5, clr)
            clr = hy.Clearance(b)
        else:
            n += draw(b, 'PYRO1_CONT', kind, 0.15, geo, clr)
            L1 += sum(math.dist(p, q) for p, q in zip(geo, geo[1:]))
    gv = []
    vias_pc = [g for k, g in PYRO1_CONT_ROUTE if k == 'via']
    for q in vias_pc:
        have = [hy.xy(v.GetPosition()) for v in vias_of(b, 'GND')]
        if min(math.dist(P(*q), h) for h in have) / 1e6 <= rc.GND_REACH:
            continue
        d = 0.6
        spot = gnd_spot(b, q, [q], r=1.45, d=0.6)
        if not spot:
            d, spot = 0.5, gnd_spot(b, q, [q], r=1.45, d=0.5)
        assert spot and spot[1] <= rc.GND_REACH, ('PYRO1_CONT layer change without a GND via spot', q, spot)
        add_via(b, 'GND', spot[0], d)
        gv.append((q, spot[0], d, spot[1]))
    gap = net_gap(b, 'PYRO1_CONT', 'PYRO1_GATE_N')
    assert gap >= PYRO1_CONT_GATE_GAP, ('PYRO1_CONT too near PYRO1_GATE_N', gap)
    log.append(f'  PYRO1_CONT: {len(old)} items ({L0:.2f} mm of track, 7 vias) -> {n} segments ({L1:.2f} mm) and '
               f'{len(vias_pc)} vias; GND return vias {gv}; copper gap to PYRO1_GATE_N {gap:.3f} mm')


def net_gap(b, net, other):
    """Smallest copper edge gap (mm, 0.001 resolution) between two nets' tracks, vias and pads on any shared layer."""
    def items(n):
        out = [(l, t) for t in b.GetTracks() if t.GetNetname() == n for l in hy.CU4 if t.IsOnLayer(l)]
        out += [(l, p) for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == n for l in hy.CU4
                if p.IsOnLayer(l)]
        return out
    best = 99.0
    others = items(other)
    for la, x in items(net):
        sa = x.GetEffectiveShape(la)
        for lb, y in others:
            if la != lb:
                continue
            sb = y.GetEffectiveShape(lb)
            if not sa.Collide(sb, MM(best)):
                continue
            lo, hi = 0, MM(best)
            while hi - lo > 1000:
                mid = (lo + hi) // 2
                if sa.Collide(sb, mid):
                    hi = mid
                else:
                    lo = mid
            best = min(best, mm(hi))
    return round(best, 3)


def redraw(b, log, label, net, layer, w, old, new, vias_gone=(), vias_new=(), dv=0.6):
    """Delete net's tracks on layer with the end points in `old` = [(a, c), ...] (each exactly once) and the vias at
    vias_gone, then place vias_new and draw `new` = [[(x, y), ...], ...] polylines (width w; all checked)."""
    for a, c in old:
        b.Delete(find_track(b, net, layer, a, c))
    for p in vias_gone:
        b.Delete(find_via(b, net, p))
    for p in vias_new:
        add_via(b, net, p, dv)
    clr = hy.Clearance(b)
    n = sum(draw(b, net, layer, w, pts, clr) for pts in new)
    log.append(f'  {label}: {net} {layer}: {len(old)} tracks and {len(vias_gone)} vias -> {n} segments and '
               f'{len(vias_new)} vias')


def gnd_spot(b, want, serve, r=1.0, d=0.6, step=0.05):
    """The GND via spot nearest `want` within r (0.05 mm grid) that passes r7_route.ViaCheck and r7_hygiene.Clearance
    on every layer (pyro rules, bare test pads 1.0 mm, Tag-Connect 0.508 mm), scored by its largest distance to the
    points in `serve`; (spot, score) or None."""
    import r7_route as rt                       # noqa: E402
    chk = rt.ViaCheck(b)
    clr = hy.Clearance(b)
    best = None
    n = int(r / step)
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            q = (round(want[0] + step * i, 3), round(want[1] + step * j, 3))
            if math.dist(q, want) > r or not chk.ok(q, d) or not npth_ok(b, q, d):
                continue
            Q = P(*q)
            if any(clr.why('GND', l, Q, Q, MM(d)) for l in hy.CU4):
                continue
            score = (round(max(math.dist(q, p) for p in serve), 4), round(math.dist(q, want), 4), q)
            if best is None or score < best:
                best = score
    return (best[2], best[0]) if best else None


def pyro_corners(b, log):
    """Short corners on the pyro block's gate and sense copper (P3-ROUTING_GEOMETRY-01 (b), P3-ROUTING_QUALITY-04):
    - PYRO1_GATE_N F.Cu R126.1 -> R127.1: an 83 um east hook (21.6, 89.5818) -> (21.6829, 89.5818) between the
      vertical and a 0.424 mm 45° step (R6 copper; the review's N / 45° / N redraw is still a tiny jog by
      route_check's rule): one straight run at x 21.9 from R127.1's centre into R126.1 (0.3 mm east of its centre,
      inside the 1.38 mm wide pad; every pyro rule kept, rule G 0.3 mm in the pyro block);
    - PYRO1_COLD F.Cu R131.2 -> D120.1: the kink where its deleted dead branch joined (it left R131.2 heading away from
      D120.1, then turned 90°) becomes one north run and one 45° run into D120.1's centre (0.48 mm to R131.1, PYRO1_OUT,
      against rule C's 0.3 mm);
    - GND F.Cu C126.2 -> R128.2: a 0.179 mm south stub between the T at (23.9677, 90.7) and the 45° step becomes one
      45° step from the T to y 91.07 and the run east into R128.2's centre."""
    redraw(b, log, 'gate_n corner', 'PYRO1_GATE_N', 'F', 0.2,
           [((21.6, 90.4), (21.6, 89.5818)), ((21.6, 89.5818), (21.6829, 89.5818)),
            ((21.6829, 89.5818), (21.9, 89.3647)), ((21.9, 88.83), (21.9, 89.3647))],
           [[(21.9, 88.83), (21.9, 90.4)]])
    redraw(b, log, 'cold kink', 'PYRO1_COLD', 'F', 0.2,
           [((29.72, 86.1), (29.335, 85.715)), ((29.335, 85.715), (31.05, 84.0))],
           [[(29.72, 86.1), (29.72, 85.33), (31.05, 84.0)]])
    redraw(b, log, 'gnd C126.2-R128.2', 'GND', 'F', 0.2,
           [((23.9677, 90.7), (23.9677, 90.8794)), ((23.9677, 90.8794), (24.1583, 91.07)),
            ((24.7, 91.07), (24.1583, 91.07))],
           [[(23.9677, 90.7), (24.3377, 91.07), (24.7, 91.07)]])


def corners(b, log):
    """Short segments and untidy nodes on power and GND copper (P3-ROUTING_GEOMETRY-01 (b) / -04, route_check
    short_segment):
    - 3V3 B.Cu into C17.1: 0.134 and 0.185 mm segments ending 0.1 mm off the pad centre: east along y 59.5, then
      south into the centre (0.40 mm to USB_DP, 0.44 mm to C17.2);
    - 3V3 B.Cu branch off the via (29.9, 43.625) -> R164.1 diagonal: F3's square T left a 0.25 mm stub, a north run
      and a short 45° step; the branch now leaves the diagonal square at (30.9, 44.625) and runs one 45° segment to
      y 43.725, then east as before;
    - RAW_PROTECTED F.Cu D9.1 -> via (15.7, 32.4): a 0.5 mm east piece of a 0.6 mm track after the 45° run: the run
      starts 0.5 mm east of D9.1's centre inside the 2.5 x 1.8 mm pad and reaches the via in one 45° segment;
    - GND F.Cu J3.1 -> J3.B1A12: a 0.127 mm 45° nick at (7.63, 79.63): one square corner at x 7.7217;
    - GND B.Cu via (28.13, 31.3) -> C8.2: a 0.147 mm east piece between a 45° and a south run: one 45° and one south
      run into C8.2's centre; C8.2 -> R86.2 now starts at the pad centre (it started 25 um off it)."""
    redraw(b, log, 'C17.1', '3V3', 'B', 0.3,
           [((12.6, 59.5), (14.505, 59.5)), ((14.505, 59.5), (14.6, 59.595)), ((14.6, 59.595), (14.6, 59.78))],
           [[(12.6, 59.5), (14.5, 59.5), (14.5, 59.88)]])
    redraw(b, log, 'R164 branch', '3V3', 'B', 0.25,
           [((31.3232, 45.0482), (31.5, 44.8714)), ((31.5, 44.8714), (31.5, 43.925)), ((31.5, 43.925), (31.7, 43.725)),
            ((31.7, 43.725), (33.8, 43.725))],
           [[(30.9, 44.625), (31.8, 43.725), (33.8, 43.725)]])
    redraw(b, log, 'D9.1', 'RAW_PROTECTED', 'F', 0.6,
           [((14.0, 31.2), (15.2, 32.4)), ((15.2, 32.4), (15.7, 32.4))],
           [[(14.5, 31.2), (15.7, 32.4)]])
    redraw(b, log, 'J3 GND', 'GND', 'F', 0.2,
           [((6.31, 79.625), (7.6317, 79.625)), ((7.6317, 79.625), (7.7217, 79.535)), ((7.7217, 79.535), (7.7217, 78.5))],
           [[(6.31, 79.625), (7.7217, 79.625), (7.7217, 78.5)]])
    redraw(b, log, 'C8.2', 'GND', 'B', 0.2,
           [((28.13, 31.3), (28.4533, 31.6233)), ((28.4533, 31.6233), (28.6, 31.6233)), ((28.6, 31.6233), (28.6, 32.6))],
           [[(28.13, 31.3), (28.6, 31.77), (28.6, 32.6)]])
    redraw(b, log, 'C8.2-R86.2', 'GND', 'B', 0.25,
           [((28.6, 32.625), (29.4, 32.625)), ((29.4, 32.625), (30.7, 33.925))],
           [[(28.6, 32.6), (29.375, 32.6), (30.7, 33.925)]])


def l1_node(b, log):
    """P3-ROUTING_GEOMETRY-04: F3's L1.2 (buck output, 3V3) node had four 0.6 mm tracks meeting the 1.6 x 3.5 mm pad at
    different points, C9.1's diagonal ending at the pad edge with its copper merging into the vertical's outside the
    pad without a node, and a via feeding a second via over a 1.25 mm B.Cu hop. Now: the 45° run from the pad centre to
    the plane via (24.8, 34.3) and C8.1's branch stay; the vertical to the plane via (26.4, 36.6) starts on C8.1's
    branch inside the pad, at (26.4, 33.3), as in R6 (the via cannot move under the centre line: USB_LIMITED's via
    (25.8, 37.15)); C9.1 joins that vertical square at (26.4, 36.1), past USB_LIMITED's via (east,
    one 45° step, east: a node on the vertical, no merged copper); the second
    via (24.2, 35.3) and its hop go (the dead stage already removed the In2 runs that tied it into the plane; the plane
    vias left are (24.8, 34.3) and (26.4, 36.6); the DC solve in the record gives L1.2 -> loads)."""
    for a, c in (((24.8, 34.3), (24.2, 34.9)), ((24.2, 34.9), (24.2, 35.3)), ((24.1, 36.6), (26.0, 34.7)),
                 ((26.4, 33.3), (26.4, 36.6))):
        b.Delete(find_track(b, '3V3', 'B', a, c))
    b.Delete(find_via(b, '3V3', (24.2, 35.3)))
    n = draw(b, '3V3', 'B', 0.6, [(26.4, 33.3), (26.4, 36.6)], hy.Clearance(b))
    n += draw(b, '3V3', 'B', 0.6, [(24.1, 36.6), (25.2, 36.6), (25.7, 36.1), (26.4, 36.1)], hy.Clearance(b))
    log.append(f'  L1.2 node: 4 tracks and via (24.2, 35.3) removed, {n} segments drawn')


def gnd_moves(b, log):
    """GND returns (P3-ROUTING_GEOMETRY-01 (c), P3-REGRESSION-02):
    - two GND vias move 0.06-0.07 mm so the critical layer changes beside them have a GND via within 1.5 mm (the
      allowlist reason "no DRC-legal spot" was wrong: the search only tried new vias): (19.65, 30.55) -> (19.71, 30.51)
      for RADIO_RXEN (21.2, 30.45) (1.553 -> 1.50 mm), (3.3, 50.4) -> (3.26, 50.44) for GNSS_RXD_MCU (2.2, 51.5)
      (1.556 -> 1.50 mm);
    - F2's PULLPIN redraw removed C160.2's trace to the GND via (32.75, 32.30), so the pull-pin clamp D122.1 and the
      filter capacitor C160.2 returned only through the F.Cu pour (5.62 / 4.22 mm of copper to a via); a GND via now
      sits 0.7 mm from C160.2, joined to it by one 45° track (D122.1 already joins C160.2 by track): D122.1 about
      2.5 mm and C160.2 0.7 mm of copper from a via (the spot search, ViaCheck and every clearance, finds nothing
      nearer D122.1)."""
    move_via(b, 'GND', (19.65, 30.55), (19.71, 30.51), log=log, why='RADIO_RXEN (21.2, 30.45)')
    move_via(b, 'GND', (3.3, 50.4), (3.26, 50.44), log=log, why='GNSS_RXD_MCU (2.2, 51.5)')
    pads = [(33.45, 28.6), (34.9, 28.92)]
    spot = gnd_spot(b, (34.2, 28.75), pads, r=2.5, d=0.5)
    assert spot and spot[0] == (35.5, 29.4), spot
    add_via(b, 'GND', spot[0], 0.5)
    n = draw(b, 'GND', 'F', 0.2, [(34.98, 28.88), (35.5, 29.4)], hy.Clearance(b))
    log.append(f'  GND via (0.5 mm) by C160.2 at {spot[0]}, joined to C160.2 by {n} 45° segment (D122.1 reaches it over '
               f'its existing link to C160.2); no legal spot lies nearer D122.1 (search radius 2.5 mm)')


def neck(b, log):
    """The dead stage left GND B.Cu (13.7, 80.6) -> (14.6, 80.6) (0.25 mm, U10.2's run) meeting the 0.2 mm rest of the
    run at a plain node, where a removed branch had made a T: the piece takes the run's 0.2 mm (route_check
    neck_down)."""
    t = find_track(b, 'GND', 'B', (13.7, 80.6), (14.6, 80.6))
    t.SetWidth(MM(0.2))
    log.append('  GND B.Cu (13.7, 80.6)-(14.6, 80.6): 0.25 -> 0.2 mm')


def dead2(b, log):
    """dead again after the reroutes: removing SWDIO's old In2 runs merged two 3V3 In2 fill islands, so the R6 link
    3V3 In2 (15.2, 62.3) -> (16.5, 61.0) that bridged them now lies in one island (the review had called it the one
    pour-only track with a function)."""
    dead(b, log, 'dead2')


def band(b, log):
    """P4-DOCS-01 (1): the radio band's fan-in (RADIO_* lanes from the via columns x 9.4 / 10.0 on 0.5 mm rows to the
    F.Cu lanes on 0.4 mm rows; tools/route_check staircase, gated on every net). Two of the four staircases go:
    - RADIO_NRST (column 10.0, lane 0.1 mm above its row): the step moves inside its via (a 0.141 mm diagonal from the
      via centre, wholly inside its 0.5 mm copper), so the lane leaves the via and runs straight on; its tiny jog and
      0.141 mm short segment go with it;
    - RADIO_SCK: the run before its step lengthens from 0.6 to 1.05 mm (and RADIO_NSS's, the lane outside it, from
      1.2 to 1.8 mm, keeping the chamfers 0.46 mm apart), so only one segment of the run is under 1 mm (extra bends,
      counted, not gated).
    RADIO_BUSY and RADIO_MISO_MCU keep theirs (measured reason in route_check.ALLOWLIST): a column-9.4 lane must stay on
    its row until it has passed the column-10.0 vias (0.475 mm needed at 0.5 mm rows), the lane rows are fixed at 0.4 mm
    by RADIO_DIO1 (y 27.2) and BAT_SW_RETURN (0.175 mm south of RADIO_NSS's lane), and the east chamfers into the strip
    columns (x 21.2 / 21.6) are fixed by the 0.4 mm column pitch, so each keeps two short 45° steps."""
    redraw(b, log, 'band NRST', 'RADIO_NRST', 'F', 0.15,
           [((10.0, 27.7), (10.6, 27.7)), ((10.6, 27.7), (10.7, 27.6)), ((10.7, 27.6), (18.5, 27.6))],
           [[(10.0, 27.7), (10.1, 27.6), (18.5, 27.6)]])
    redraw(b, log, 'band NSS', 'RADIO_NSS', 'F', 0.15,
           [((9.4, 30.2), (10.6, 30.2)), ((10.6, 30.2), (11.2, 29.6)), ((11.2, 29.6), (22.0, 29.6))],
           [[(9.4, 30.2), (11.2, 30.2), (11.8, 29.6), (22.0, 29.6)]])
    redraw(b, log, 'band SCK', 'RADIO_SCK', 'F', 0.15,
           [((10.0, 29.7), (10.6, 29.7)), ((10.6, 29.7), (11.1, 29.2)), ((11.1, 29.2), (21.398, 29.2))],
           [[(10.0, 29.7), (11.05, 29.7), (11.55, 29.2), (21.398, 29.2)]])


def debris(b, log):
    """P4-DOCS-01 (1): the non-critical short segments and tiny jogs a simpler drawing clears (route_check counts them;
    each redraw checked like every other one here):
    - LED_YEL_A F.Cu LED2.1 -> R33.2: 5 segments with a 99 um piece and a 0.516 mm jog -> south 0.55 mm and one 45° run
      into R33.2 (pass-4 docs review's route; >= 0.45 mm to R33.1, 0.65 mm to CAM_MCU_TX);
    - SERVO3_MCU B.Cu into D121.4: a 0.19 mm east piece and a stub inside the pad -> its 45° run continued into the pad
      (0.41 mm off the centre inside the 1.07 mm pad);
    - CAM_5V_SENSE F.Cu out of U1.35 round RAW_ACT_SENSE_MCU's via: a 0.2 mm west piece between two 45° runs (tiny jog)
      -> one 45° step, west 0.6 mm at y 47.05 (0.225 mm to U1.36's end and to the via), south;
    - SERVO4_OUT In2: a 0.3 mm west piece between two 45° runs -> one 45° run;
    - SERVO2_MCU In2 between the PYRO1_GATE_N via (23.0, 88.33) and the SERVO1_OUT via (24.4, 88.5): a 0.119 mm piece
      and three short bends (router debris) -> west, south on the line the two vias allow (x 23.775: 0.40 mm to the gate
      via against rule G's 0.31 mm, 0.25 mm to SERVO1_OUT's), one 45° run on;
    - CAM_EN B.Cu out of U7.2: a 61 um bevel -> a square corner (the 0.293 mm step between C71.1 and U7.1/CAM_DVDT
      stays: measured reason in route_check.LEFTOVERS);
    - LOGIC_ILIM B.Cu round LOGIC_SOURCE_ST's via (29.95, 30.55): a 0.2 mm offset step (tiny jog) -> a 0.36 mm offset
      step (0.51 mm long; 0.26 mm to LOGIC_SS);
    - I2C1_SCL F.Cu out of U1's bottom row between BOOT0's and IMU_INT1's vias: a 0.3 mm offset step (0.424 mm long,
      a tiny jog) -> a 0.36 mm step, the run 0.06 mm east (0.265 mm to the IMU_INT1 via);
    - SERVO4_MCU In2 beside CAM_FAULT_N's In2 run: a 0.276 mm offset step (0.391 mm, a tiny jog) -> a 0.36 mm step;
    - CAM_RX_WIRE In2 at its T by U12: a 58 um piece and two branches 0.04 / 0.16 mm off the trunk -> one vertical with a
      square T and one 0.228 mm 45° step into the southern branch."""
    redraw(b, log, 'LED_YEL_A', 'LED_YEL_A', 'F', 0.15,
           [((40.35, 26.5), (40.35, 27.4467)), ((40.35, 27.4467), (40.4492, 27.4467)),
            ((40.4492, 27.4467), (41.8868, 28.8843)), ((41.8868, 28.8843), (41.8868, 29.4)), ((42.7, 29.4), (41.8868, 29.4))],
           [[(40.35, 26.5), (40.35, 27.05), (42.7, 29.4)]])
    redraw(b, log, 'SERVO3_MCU', 'SERVO3_MCU', 'B', 0.15,
           [((33.0, 84.1), (33.0, 83.5)), ((32.8098, 84.1), (33.0, 84.1)), ((31.5313, 85.3785), (32.8098, 84.1))],
           [[(31.5313, 85.3785), (32.95, 83.9598)]])
    redraw(b, log, 'CAM_5V_SENSE', 'CAM_5V_SENSE', 'F', 0.15,
           [((23.35, 46.75), (23.05, 47.05)), ((22.85, 47.05), (23.05, 47.05)), ((22.45, 47.45), (22.85, 47.05)),
            ((22.45, 47.85), (22.45, 47.45))],
           [[(23.35, 46.75), (23.05, 47.05), (22.45, 47.05), (22.45, 47.85)]])
    redraw(b, log, 'SERVO4_OUT', 'SERVO4_OUT', 'In2', 0.15,
           [((26.9, 67.6), (26.1, 68.4)), ((26.1, 68.4), (25.8, 68.4)), ((25.8, 68.4), (25.0, 69.2)),
            ((25.0, 69.2), (25.0, 71.4))],
           [[(26.9, 67.6), (25.0, 69.5), (25.0, 71.4)]])
    redraw(b, log, 'SERVO2_MCU', 'SERVO2_MCU', 'In2', 0.15,
           [((29.0536, 87.871), (24.5847, 87.871)), ((24.5847, 87.871), (24.5004, 87.7867)),
            ((24.5004, 87.7867), (24.0475, 87.7867)), ((24.0475, 87.7867), (23.6831, 88.1511)),
            ((23.6831, 88.1511), (23.6831, 88.6747)), ((23.6831, 88.6747), (23.3055, 89.0523))],
           [[(29.0536, 87.871), (23.775, 87.871), (23.775, 88.5828), (23.3055, 89.0523)]])
    redraw(b, log, 'CAM_EN', 'CAM_EN', 'B', 0.15,
           [((37.95, 85.7), (37.95, 85.2033)), ((37.95, 85.2033), (37.9067, 85.16)), ((37.9067, 85.16), (37.1974, 85.16))],
           [[(37.95, 85.7), (37.95, 85.16), (37.1974, 85.16)]])
    redraw(b, log, 'LOGIC_ILIM', 'LOGIC_ILIM', 'B', 0.2,
           [((29.45, 29.35), (29.45, 30.15)), ((29.45, 30.15), (29.25, 30.35)), ((29.25, 30.35), (29.25, 30.85)),
            ((29.25, 30.85), (30.65, 32.25))],
           [[(29.45, 29.35), (29.45, 30.0), (29.09, 30.36), (29.09, 30.69), (30.65, 32.25)]])
    redraw(b, log, 'I2C1_SCL', 'I2C1_SCL', 'F', 0.15,
           [((25.35, 61.05), (25.35, 62.35)), ((25.35, 62.35), (25.65, 62.65)), ((25.65, 62.65), (25.65, 67.55)),
            ((25.65, 67.55), (32.15, 74.05))],
           [[(25.35, 61.05), (25.35, 62.25), (25.71, 62.61), (25.71, 67.61), (32.15, 74.05)]])
    redraw(b, log, 'SERVO4_MCU', 'SERVO4_MCU', 'In2', 0.15,
           [((15.7548, 91.1667), (15.4784, 90.8903)), ((15.7548, 101.3766), (15.7548, 91.1667)),
            ((15.4784, 90.8903), (15.4784, 67.1762)), ((18.005, 103.6268), (15.7548, 101.3766))],
           [[(15.4784, 67.1762), (15.4784, 90.85), (15.8384, 91.21), (15.8384, 101.4602), (18.005, 103.6268)]])
    redraw(b, log, 'CAM_RX_WIRE', 'CAM_RX_WIRE', 'In2', 0.15,
           [((42.859, 55.136), (44.0481, 55.136)), ((44.0481, 55.136), (44.0895, 55.0946)),
            ((44.251, 55.3389), (44.0481, 55.136)), ((44.251, 63.1084), (44.251, 55.3389)),
            ((44.0895, 55.0946), (44.0895, 44.9737))],
           [[(44.0895, 44.9737), (44.0895, 55.136), (44.251, 55.2975), (44.251, 63.1084)],
            [(42.859, 55.136), (44.0895, 55.136)]])


CAM_UART_OE_ROUTE = [
    ('B', [(42.175, 45.7), (41.5, 46.375), (41.5, 49.45)]), ('B', [(41.5, 49.45), (41.5, 50.45)]), ('via', (41.5, 50.45)),
    ('F', [(41.5, 50.45), (41.5, 56.65), (38.0, 60.15)]), ('via', (38.0, 60.15)),
    ('B', [(38.0, 60.15), (38.0, 62.5)]),
    ('F', [(38.0, 60.15), (34.55, 60.15), (34.0, 60.7)]), ('via', (34.0, 60.7)),
    ('In2', [(34.0, 60.7), (34.0, 58.0)]), ('via', (34.0, 58.0)),
    ('F', [(34.0, 58.0), (33.15, 58.0), (31.65, 56.5), (29.4, 56.5)])]
NRST_J2_OLD = [('In2', (30.824, 46.1947), (31.3687, 45.65)), ('In2', (31.3687, 45.65), (34.035, 45.65)),
               ('F', (34.035, 45.65), (36.135, 45.65)), ('F', (36.135, 45.65), (37.135, 46.65)),
               ('In2', (37.135, 46.65), (37.135, 50.35)), ('In2', (37.135, 50.35), (36.435, 51.05)),
               ('In2', (36.435, 51.05), (36.435, 65.05)), ('In1', (36.435, 65.05), (36.835, 65.05)),
               ('In1', (36.835, 65.05), (38.5, 66.715)), ('In1', (38.5, 66.715), (38.5, 67.2)),
               ('F', (38.5, 67.2), (39.785, 67.2)), ('F', (39.785, 67.2), (45.335, 72.75)),
               ('F', (45.335, 72.75), (45.335, 75.55)), ('F', (45.335, 75.55), (44.235, 76.65)),
               ('F', (44.235, 76.65), (43.85, 76.65))]
NRST_J2_VIAS = [(34.035, 45.65), (37.135, 46.65), (36.435, 65.05), (38.5, 67.2)]
NRST_J2_ROUTE = [
    ('B', [(30.8, 53.1), (30.8, 52.3), (31.5, 51.6), (33.45, 51.6), (35.8, 53.95)]), ('via', (35.8, 53.95)),
    ('In2', [(35.8, 53.95), (36.3, 54.45), (36.3, 64.8)]), ('via', (36.3, 64.8)),
    ('F', [(36.3, 64.8), (45.3, 73.8), (45.3, 75.6), (44.25, 76.65), (43.85, 76.65)])]


def reroutes(b, log):
    """P4-DOCS-01 (2): the non-critical over-via nets where the raster search (fx4/det/r3: F/B/In2 at 0.05 mm, every
    board clearance, every power pour on every layer kept whole) found a clearly simpler route; hand-tidied (the
    search's grid jogs gone) and checked like every other redraw here:
    - CAM_UART_OE (R102.1 / U12.6 / TP91 on B.Cu, U1.7 on F.Cu): R6's 44.1 mm / 6 vias (a loop along the east edge to
      x 45.09 and an F -> B -> F -> B hop under U1's SE corner that ran south to y 63.4 and back) -> 30.7 mm / 4 vias:
      U12.6 straight on south, F.Cu diagonal to TP91's via, west on F.Cu and a 2.7 mm In2 hop under SWCLK's diagonal
      (In2 GND, outside the 3V3 island) into U1.7;
    - NRST (C24.1, U1.14, J2.3): its branch to J2.3 ran 42 mm through In2, F.Cu, In2 and 3.2 mm on In1, the solid GND
      plane, with 4 vias -> from U1.14's via: B.Cu beside SWCLK's hop, In2 down x 36.3 (14 mm of In2 before), one F.Cu
      diagonal to J2.3: 6 -> 4 vias, 54.3 -> 47 mm, no copper on In1. J2.3 is entered from the east and the run ends
      0.215 mm east of the pad centre, as before (J2's keep-out between the contacts starts at the pad centres)."""
    reroute(b, log, [('CAM_UART_OE', 22, 6, CAM_UART_OE_ROUTE)])
    for lay, a, c in NRST_J2_OLD:
        b.Delete(find_track(b, 'NRST', lay, a, c))
    for q in NRST_J2_VIAS:
        b.Delete(find_via(b, 'NRST', q))
    clr = hy.Clearance(b)
    n = 0
    for kind, geo in NRST_J2_ROUTE:
        if kind == 'via':
            add_via(b, 'NRST', geo, 0.5, clr)
            clr = hy.Clearance(b)
        else:
            n += draw(b, 'NRST', kind, 0.15, geo, clr)
    log.append(f'  NRST J2 branch: {len(NRST_J2_OLD)} tracks (3 on In1) and {len(NRST_J2_VIAS)} vias -> {n} segments '
               f'and 2 vias')


# --- fix pass 5 (sources/r7_review/pass5_*.md, pass5_verdicts.json; record: fix5_F6_handoff.md) ---------------------

def band5(b, log):
    """P5-ROUTING_GEOMETRY-01 (allowlist A1, A2): the RADIO_BUSY and RADIO_MISO_MCU band staircases were not forced. The
    lanes are nested, so their east chamfers into the strip columns are free: each becomes 1.004 mm (BUSY from x 20.49,
    MISO_MCU from x 20.89), with the lane minimum clearance unchanged at 0.25 mm; MISO_MCU's fan-in step and
    RADIO_MOSI's (the lane outside it) move 0.35-0.4 mm east to keep 0.25 mm between the two steps (pass-5 review,
    v_band, measured again here). Each run then has one segment under 1 mm (extra bends, counted). The fan-in steps
    out of the via rows stay (tiny jogs A3/A4: a 0.2 / 0.3 mm row offset is a tiny step at any length)."""
    redraw(b, log, 'band BUSY', 'RADIO_BUSY', 'F', 0.15,
           [((10.8, 28.0), (20.9, 28.0)), ((20.9, 28.0), (21.2, 27.7)), ((21.2, 27.7), (21.2, 11.76))],
           [[(10.8, 28.0), (20.49, 28.0), (21.2, 27.29), (21.2, 11.76)]])
    redraw(b, log, 'band MOSI', 'RADIO_MOSI', 'F', 0.15,
           [((9.4, 29.2), (10.6, 29.2)), ((10.6, 29.2), (11.0, 28.8)), ((11.0, 28.8), (21.232, 28.8))],
           [[(9.4, 29.2), (10.95, 29.2), (11.35, 28.8), (21.232, 28.8)]])
    redraw(b, log, 'band MISO_MCU', 'RADIO_MISO_MCU', 'F', 0.15,
           [((10.0, 28.7), (10.6, 28.7)), ((10.6, 28.7), (10.9, 28.4)), ((10.9, 28.4), (21.066, 28.4)),
            ((21.066, 28.4), (21.6, 27.866)), ((21.6, 27.866), (21.6, 13.03))],
           [[(10.0, 28.7), (11.0, 28.7), (11.3, 28.4), (20.89, 28.4), (21.6, 27.69), (21.6, 13.03)]])


def qspi5(b, log):
    """P5-ROUTING_GEOMETRY-01 / P5-ROUTING_QUALITY-05 (allowlist A5) and deviation D12: RADIO_RXEN's lane ran at
    x 23.575 and stepped 0.225 mm across into its via (23.8, 39.45) (a tiny jog across a via); it now runs on the via's
    own column x 23.8 from one diagonal out of (22.575, 30.45) (0.329 mm to the GND via (23.92, 30.8), the nearest
    copper). That frees QSPI_CLK's escape from U1.36 to step 0.36 mm instead of 0.3 mm (a 0.509 mm 45 deg step, not a
    tiny jog; straight on at x 22.85 the clock would overlap QSPI_IO3's via (22.5, 40.3)); its NW diagonal keeps its line
    (x - y = -11.7), 0.24 mm from RXEN's via and 0.325 mm from LED_YEL."""
    redraw(b, log, 'RXEN column', 'RADIO_RXEN', 'F', 0.15,
           [((23.575, 31.45), (22.575, 30.45)), ((23.575, 39.225), (23.575, 31.45)), ((23.8, 39.45), (23.575, 39.225))],
           [[(22.575, 30.45), (23.8, 31.675), (23.8, 39.45)]])
    redraw(b, log, 'QSPI_CLK step', 'QSPI_CLK', 'F', 0.2,
           [((22.85, 44.65), (23.15, 44.35)), ((23.15, 44.35), (23.15, 34.85)), ((23.15, 34.85), (21.65, 33.35))],
           [[(22.85, 44.65), (23.21, 44.29), (23.21, 34.91), (21.65, 33.35)]])


CFN_IN2_OLD = [((14.0457, 77.0649), (14.0457, 78.2994)), ((14.0457, 78.2994), (14.6414, 78.8951)),
               ((14.6414, 78.8951), (14.6414, 90.8244)), ((14.6414, 90.8244), (15.2187, 91.4017)),
               ((15.2187, 91.4017), (15.2187, 101.3263)), ((15.2187, 101.3263), (17.8516, 103.9592)),
               ((17.8516, 103.9592), (20.4455, 103.9592)), ((20.4455, 103.9592), (20.6268, 103.7779)),
               ((20.6268, 103.7779), (31.0599, 103.7779)), ((31.0599, 103.7779), (37.8875, 96.9503))]
S4_IN2_OLD = [((17.825, 64.8296), (15.4784, 67.1762)), ((15.4784, 67.1762), (15.4784, 90.85)),
              ((15.4784, 90.85), (15.8384, 91.21)), ((15.8384, 91.21), (15.8384, 101.4602)),
              ((15.8384, 101.4602), (18.005, 103.6268))]


def jogs5(b, log):
    """P5-ROUTING_GEOMETRY-02 (leftovers B1, B2 not forced), P5-ROUTING_QUALITY-04 (three jogs only lengthened past
    route_check's threshold), deviations D6, D13, D16 and the tiny jogs across vias the pass-5 scan found (route_check
    now sees jogs through T, via and pad nodes). Each redraw is checked like every other one here:
    - CAM_EN B.Cu between C71.1 and U7.1: W, S, SW into the via instead of a 0.293 mm step (0.21 mm to RAW_PROTECTED);
    - CAM_FAULT_N In2 and SERVO4_MCU In2 (B2, D6, RQ-04): CAM_FAULT_N's tiny step between SERVO4_MCU and the GND via
      (24.55, 104.475) becomes one straight run at y 103.938 (0.162 mm to both); its staircase through the via
      (14.6414, 90.8244) goes: the In2 run leaves its F.Cu via (14.0457, 77.0649) in one 1.618 mm diagonal and runs
      straight down x 15.19 (0.165 mm to CAM_PWR_EN's via (14.65, 92.95)), the via joining it by a square 0.549 mm
      stub; SERVO4_MCU, beside it, runs straight down x 15.505 (0.165 mm to CAM_FAULT_N's via (16.0438, 67.4556) and
      to CAM_FAULT_N's run), so its 0.509 mm step (lengthened past the threshold in fix pass 4) is gone;
    - LOGIC_ILIM B.Cu U11.10 -> R86.1 (RQ-04): S, SW, SE (no jog) instead of S, SW, S, SE: 0.194 mm to the 3V3 via
      (30.63, 31.34), 0.272 mm to LOGIC_SOURCE_ST's via, into R86.1 0.025 mm off its centre;
    - CAM_RX_WIRE In2 (D13): one run at x 44.251 with the R100 branch squared onto it; its layer change to TP75 moves to
      the run's end (via (44.251, 64.0), B.Cu straight west into TP75.1): the 0.36 mm step across the old via goes;
    - CAM_TX_WIRE (D16): its three inherited R6 segments on In1 (the GND plane) go. CAM_RX_WIRE now leaves J9.3 east
      on F.Cu to a via at (43.75, 42.625) between BAT_SW_SOURCE and BAT_SW_RETURN's In2 runs and goes down In2, so
      CAM_TX_WIRE runs straight east from J9.4 on F.Cu (from its pad centre; it began 17 um off it) to one via at
      (45.1408, 43.875) and on down its B.Cu run: 2 vias -> 1, no In1 copper. The GND stitching via (43.7, 43.5), in
      the way of both, moves to (42.2, 43.25) between the two wires;
    - LOGIC_SOURCE_ST F.Cu: its SE run goes on to the via column x 30.725 and drops straight into the via (the 0.229 mm
      step across the via goes; 0.236 mm to USB_OVLO);
    - CAM_5V_SENSE: the 2.9 mm F.Cu hop (two vias, a V round the first one and a 0.3 mm step across the second) was not
      needed: In2 runs straight on down x 32.05 (0.175 mm to a GND via) and in one diagonal to its old line; the In2
      there is a void of 3V3_In2 (no fill to cut, zone check);
    - PULLPIN_EXT B.Cu: the lane between C94.1 and C94.2 (x 34.4) can take no via of its own (C160.2 on F.Cu, C60.2 and
      CAM_5V on B.Cu), so it reaches the via (34.15, 29.8) on the F.Cu column; it now runs straight on to the via's ring
      and steps 0.25 mm into its centre inside the via copper, instead of a 0.354 mm 45 deg step outside it (alt_audit's
      redraw; 0.175 mm to C60.2);
    - LED_RED: its 2.35 mm B.Cu hop over VLOGIC_SENSE's In2 run (between two vias) now runs on F.Cu, where the F.Cu
      hop of CAM_5V_SENSE (above) used to be: its F.Cu diagonal goes on west to the In2 via, one via fewer (3 -> 2;
      0.382 mm to LED_YEL's via);
    BOOT0's via, 0.2 mm off its U1.94 -> R5.1 line with a 45 deg piece in and out of it, stays: on the line (x 24.94,
    clear of every copper rule) its In1 antipad takes 0.5 mm of IMU_CS's In1 reference (51 samples, critical_reference),
    and I2C1_SCL's 0.36 mm step beside it is forced by that via (any BOOT0 via between IMU_CS at x 24.35 and SCL's pin
    column x 25.35 needs 1.095 mm of the 1.0 mm channel) and by the GND via (24.97, 64.4) (measured)."""
    redraw(b, log, 'CAM_EN', 'CAM_EN', 'B', 0.15,
           [((37.95, 85.16), (37.1974, 85.16)), ((37.1974, 85.16), (36.4333, 85.9241)),
            ((36.4333, 85.9241), (36.4333, 86.2167)), ((36.4333, 86.2167), (36.05, 86.6))],
           [[(37.95, 85.16), (36.9, 85.16), (36.9, 85.75), (36.05, 86.6)]])
    redraw(b, log, 'SERVO4_MCU', 'SERVO4_MCU', 'In2', 0.15, S4_IN2_OLD, [])
    redraw(b, log, 'CAM_FAULT_N', 'CAM_FAULT_N', 'In2', 0.15, CFN_IN2_OLD,
           [[(14.0457, 77.0649), (15.19, 78.2092), (15.19, 101.2976), (17.8304, 103.938), (30.8998, 103.938),
             (37.8875, 96.9503)], [(15.19, 90.8244), (14.6414, 90.8244)]])
    redraw(b, log, 'SERVO4_MCU', 'SERVO4_MCU', 'In2', 0.15, [],
           [[(17.825, 64.8296), (15.505, 67.1496), (15.505, 101.1268), (18.005, 103.6268)]])
    redraw(b, log, 'LOGIC_ILIM', 'LOGIC_ILIM', 'B', 0.2,
           [((29.45, 29.35), (29.45, 30.0)), ((29.45, 30.0), (29.09, 30.36)), ((29.09, 30.36), (29.09, 30.69)),
            ((29.09, 30.69), (30.65, 32.25))],
           [[(29.45, 29.35), (29.45, 29.95), (28.925, 30.475), (30.7, 32.25)]])
    # CAM_RX_WIRE In2 lane, then CAM_TX_WIRE off In1 (order: every old piece goes before the copper that needs its room)
    redraw(b, log, 'CAM_RX_WIRE lane', 'CAM_RX_WIRE', 'In2', 0.15,
           [((44.0895, 44.9737), (44.0895, 55.136)), ((44.0895, 44.9737), (43.6626, 44.5468)),
            ((44.0895, 55.136), (44.251, 55.2975)), ((44.251, 55.2975), (44.251, 63.1084)),
            ((42.859, 55.136), (44.0895, 55.136))],
           [[(43.6626, 44.5468), (44.251, 45.1352), (44.251, 64.0)], [(42.859, 55.136), (44.251, 55.136)]])
    redraw(b, log, 'CAM_RX_WIRE TP75', 'CAM_RX_WIRE', 'B', 0.15,
           [((43.0, 64.0), (43.9967, 64.0)), ((43.9967, 64.0), (43.9967, 63.3627)), ((43.9967, 63.3627), (44.251, 63.1084))],
           [[(44.251, 64.0), (43.0, 64.0)]], vias_gone=[(44.251, 63.1084)], vias_new=[(44.251, 64.0)])
    redraw(b, log, 'CAM_TX_WIRE In1', 'CAM_TX_WIRE', 'In1', 0.15,
           [((43.133, 42.8675), (42.133, 43.8675)), ((43.833, 42.8675), (43.133, 42.8675)),
            ((44.933, 43.9675), (43.833, 42.8675))], [])
    redraw(b, log, 'CAM_TX_WIRE B', 'CAM_TX_WIRE', 'B', 0.15,
           [((44.933, 43.9675), (45.1408, 44.1753)), ((45.1408, 44.1753), (45.1408, 51.3592))], [])
    redraw(b, log, 'CAM_TX_WIRE F', 'CAM_TX_WIRE', 'F', 0.15, [((42.133, 43.8675), (40.733, 43.8675))], [],
           vias_gone=[(42.133, 43.8675), (44.933, 43.9675)])
    redraw(b, log, 'CAM_RX_WIRE J9', 'CAM_RX_WIRE', 'F', 0.15,
           [((41.7408, 42.625), (40.75, 42.625)), ((43.6626, 44.5468), (41.7408, 42.625))],
           [[(40.75, 42.625), (43.75, 42.625)]])
    redraw(b, log, 'GND stitch J9', 'GND', 'F', 0.2, [], [], vias_gone=[(43.7, 43.5)], vias_new=[(42.2, 43.25)])
    redraw(b, log, 'CAM_RX_WIRE down', 'CAM_RX_WIRE', 'In2', 0.15, [((43.6626, 44.5468), (44.251, 45.1352))],
           [[(43.75, 42.625), (43.75, 44.6342), (44.251, 45.1352)]], vias_gone=[(43.6626, 44.5468)],
           vias_new=[(43.75, 42.625)])
    redraw(b, log, 'CAM_TX_WIRE J9', 'CAM_TX_WIRE', 'F', 0.15, [], [[(40.75, 43.875), (45.1408, 43.875)]],
           vias_new=[(45.1408, 43.875)])
    redraw(b, log, 'CAM_TX_WIRE down', 'CAM_TX_WIRE', 'B', 0.15, [], [[(45.1408, 43.875), (45.1408, 51.3592)]])
    redraw(b, log, 'LOGIC_SOURCE_ST', 'LOGIC_SOURCE_ST', 'F', 0.15,
           [((29.95, 35.6583), (30.9542, 36.6625)), ((30.9542, 36.6625), (30.9542, 37.2708)),
            ((30.9542, 37.2708), (30.725, 37.5))],
           [[(29.95, 35.6583), (30.725, 36.4333), (30.725, 37.5)]])
    redraw(b, log, 'CAM_5V_SENSE F', 'CAM_5V_SENSE', 'F', 0.15,
           [((31.85, 39.25), (32.05, 39.45)), ((32.05, 39.45), (32.05, 41.95)), ((32.05, 41.95), (31.75, 42.25))], [])
    redraw(b, log, 'CAM_5V_SENSE In2', 'CAM_5V_SENSE', 'In2', 0.15,
           [((32.05, 37.55), (32.05, 39.05)), ((32.05, 39.05), (31.85, 39.25)), ((31.75, 42.25), (31.75, 43.05)),
            ((31.75, 43.05), (28.05, 46.75))],
           [[(32.05, 37.55), (32.05, 42.75), (28.05, 46.75)]], vias_gone=[(31.85, 39.25), (31.75, 42.25)])
    redraw(b, log, 'PULLPIN_EXT', 'PULLPIN_EXT', 'B', 0.15, [((34.4, 27.925), (34.4, 29.55)), ((34.4, 29.55), (34.15, 29.8))],
           [[(34.4, 27.925), (34.4, 29.8), (34.15, 29.8)]])
    redraw(b, log, 'LED_RED B', 'LED_RED', 'B', 0.15, [((30.85, 41.7), (33.2, 41.7))], [], vias_gone=[(33.2, 41.7)])
    redraw(b, log, 'LED_RED F', 'LED_RED', 'F', 0.15, [((33.2, 41.7), (36.0, 38.9))],
           [[(36.0, 38.9), (33.2, 41.7), (30.85, 41.7)]])


LAUNCH_NUDGE = [((32.99, 3.6), (32.99, 3.58)), ((11.4, 3.6), (11.4, 3.58)), ((30.09, 3.6), (30.09, 3.58))]


def tidy5(b, log):
    """P5-DOCS-01 (b): the part-D items a clean redraw removes (deviation numbers of R7_VALIDATION's list):
    - D1 ACT_GATE B.Cu at Q121.4: TP121's vertical runs on to a square T on the E run instead of the 45 deg branch that
      met it at the pad (an acute wedge outside the pad);
    - D2 GND B.Cu C94.2 -> C92 (a staircase through R103.2's T, inside the GND pour): E, one 45 deg run, E, SE, with
      R103.2's branch meeting the diagonal square (0.218 mm to R103.1, CAM_IO_3V3);
    - D3 CAM_5V B.Cu R78.1 -> via (39.35, 104.55): one 45 deg run out of R78.1 and one run east into the via (square to
      the via's 0.8 mm runs) instead of NE, E, SE and a 0.425 mm piece, 99.9 % inside the 0.8 mm run beside it, that
      made a jog through the via (0.25 mm to R78.2);
    - D4 3V3_RADIO F.Cu FB31.2 -> C310.1: one 45 deg run on the line through FB31.2 into C310.1's 1.41 x 1.35 mm pad
      (0.304 mm off its centre) instead of a 0.43 mm step through FB31.2;
    - D7 RAW_ACT F.Cu: the 0.2 mm tail ran 3.19 mm inside its own fill to (5.3, 82.17); it now ends 0.5 mm inside the
      fill (the fill already covers the copper it drops: DC solve in the record);
    - D9 the three same-net GND via pairs at the SMA launches overlapped by 15 um of ring (centres 0.585 mm apart, 0.6 mm
      vias): each jack-leg via at y 3.6 moves 20 um aft, so the rings no longer overlap (0.604 mm);
    - D10 USB_LIMITED at U11.7: the 0.4 mm feed runs north to y 27.85 and square west into U11.7's centre, and C98.1's
      0.25 mm branch comes down the same line x 30.8 onto that corner (a straight run with a square side branch),
      instead of a T on the feed 0.1 mm short of its corner at U11.7's pad edge (0.2 mm to U11.8, 0.194 mm to
      BAT_SW_RETURN's via);
    - D11 VLOGIC at U2: the B.Cu run into U2.2 ends at the pad centre (it stopped 0.05 mm short), and C7.1's feed at
      U2.3's centre (it stopped 0.05 mm past it)."""
    redraw(b, log, 'D1 ACT_GATE', 'ACT_GATE', 'B', 0.25, [((7.08, 101.22), (5.9, 102.4)), ((7.08, 98.86), (7.08, 101.22))],
           [[(7.08, 98.86), (7.08, 102.4)]])
    redraw(b, log, 'D2 GND', 'GND', 'B', 0.2,
           [((35.1, 28.4), (35.7717, 28.4)), ((35.7717, 28.4), (36.1634, 28.0083)), ((36.1634, 28.0083), (36.3833, 28.0083)),
            ((36.3833, 28.0083), (37.3336, 27.058)), ((37.3336, 27.058), (38.2863, 27.058)),
            ((38.2863, 27.058), (38.9283, 27.7)), ((37.8, 29.425), (36.3833, 28.0083))],
           [[(35.1, 28.4), (35.8, 28.4), (37.142, 27.058), (38.2863, 27.058), (38.9283, 27.7)],
            [(37.8, 29.425), (36.2875, 27.9125)]])
    redraw(b, log, 'D3 CAM_5V', 'CAM_5V', 'B', 0.3,
           [((32.4, 105.325), (33.8, 103.925)), ((33.8, 103.925), (38.3, 103.925)), ((38.3, 103.925), (38.925, 104.55)),
            ((38.925, 104.55), (39.35, 104.55))],
           [[(32.4, 105.325), (33.175, 104.55), (39.35, 104.55)]])
    redraw(b, log, 'D4 3V3_RADIO', '3V3_RADIO', 'F', 0.4, [((35.1, 20.85), (35.53, 20.85)), ((35.53, 20.85), (36.78, 19.6))],
           [[(35.1, 20.85), (36.565, 19.385)]])
    redraw(b, log, 'D7 RAW_ACT', 'RAW_ACT', 'F', 0.2, [((9.8, 79.37), (7.0, 82.17)), ((7.0, 82.17), (5.3, 82.17))],
           [[(9.8, 79.37), (7.6, 81.57)]])
    for old, new in LAUNCH_NUDGE:
        move_via(b, 'GND', old, new, log=log, why='D9: ring overlap with the RF line fence via')
    redraw(b, log, 'D10 USB_LIMITED feed', 'USB_LIMITED', 'B', 0.4,
           [((30.8, 30.55), (30.8, 28.15)), ((30.8, 28.15), (30.5, 27.85)), ((30.5, 27.85), (29.875, 27.85))],
           [[(30.8, 30.55), (30.8, 27.85), (29.875, 27.85)]])
    redraw(b, log, 'D10 USB_LIMITED C98', 'USB_LIMITED', 'B', 0.25, [((31.9, 25.45), (30.4, 26.95)), ((30.4, 26.95), (30.4, 27.85))],
           [[(31.9, 25.45), (30.8, 26.55), (30.8, 27.85)]])
    redraw(b, log, 'D11 VLOGIC U2.2', 'VLOGIC', 'B', 0.5, [((18.0, 32.35), (18.0, 31.85))], [[(18.0, 32.35), (18.0, 31.8)]])
    redraw(b, log, 'D11 VLOGIC U2.3', 'VLOGIC', 'B', 0.5, [((20.6, 31.8), (19.0, 31.8))], [[(20.6, 31.8), (18.95, 31.8)]])


ARM_GND = [(13.95, 93.75), (13.95, 97.15)]    # 0.5/0.3 mm GND vias beside ARM1_SENSE's layer changes


def arm_gnd(b, log):
    """P5-ROUTING_GEOMETRY-03: ARM1_SENSE's two layer changes, (14.55, 94.15) and (14.55, 97.55), had no GND via within
    1.5 mm (allowlist A17/A18): every legal spot (GndFit's board rules and project margins) lies inside the J1 -> Q120
    BAT_IN servo-current corridor, which gnd_vias keeps out of by policy. The pass-5 review measured the cost on the
    board's own stack-up at +0.9 % (4.55 -> 4.59 mOhm at 7.7 A, 0.3 mV), so AGENTS.md's arming-net rule wins: the
    nearest legal spot of each (0.721 mm away, 0.5 mm vias) gets a GND via (DC solve in the record)."""
    for q in ARM_GND:
        add_via(b, 'GND', q, 0.5)
    log.append(f'  ARM1_SENSE layer changes: GND vias (0.5 mm) at {ARM_GND}')


def band_end(b, log):
    """P5-ROUTING_QUALITY-01: at the band end the seven radio lines crossed from the In2 GND corridor strip onto the In2
    BAT_IN arm (x 7.2-9.9 from y 26.0) about 1.6-1.9 mm before their band vias (12.1 mm of radio B.Cu over BAT_IN). That
    stretch of the arm serves only the BAT_IN_F stitch vias (7.6, 26.6) / (8.8, 26.6) (C89.1 and C95.1 reach BAT_IN
    through the F.Cu pour and via (9.2, 36.05)): R7_GND_In2_strip (priority 7, above BAT_IN's 6) now also covers
    x 6.9-9.9, y 25.0-31.3 and the two vias go, so the band-end crossings are gone (the U1-end ones stay: stitching there
    needs a BAT_IN-GND capacitor). J1 -> U9.5 resistance unchanged (DC solve in the record)."""
    named = {z.GetZoneName(): z for z in b.Zones()}
    z = named['R7_GND_In2_strip']
    old = [(round(mm(z.Outline().Outline(0).CPoint(k).x), 3), round(mm(z.Outline().Outline(0).CPoint(k).y), 3))
           for k in range(z.Outline().Outline(0).PointCount())]
    assert old == [(0.3, 0.3), (45.7, 0.3), (45.7, 23.5), (41.0, 23.5), (41.0, 24.75), (14.3, 24.75), (14.3, 25.0),
                   (9.6, 25.0), (9.6, 25.9), (6.9, 25.9), (6.9, 53.1), (0.3, 53.1)], old
    o = z.Outline()
    o.RemoveAllContours()
    o.NewOutline()
    for x, y in [(0.3, 0.3), (45.7, 0.3), (45.7, 23.5), (41.0, 23.5), (41.0, 24.75), (14.3, 24.75), (14.3, 25.0),
                 (9.9, 25.0), (9.9, 31.3), (6.9, 31.3), (6.9, 53.1), (0.3, 53.1)]:
        o.Append(MM(x), MM(y))
    for q in ((7.6, 26.6), (8.8, 26.6)):
        b.Delete(find_via(b, 'BAT_IN', q))
    log.append('  R7_GND_In2_strip over x 6.9-9.9, y 25.0-31.3 (band end of the BAT_IN arm); BAT_IN vias (7.6, 26.6), '
               '(8.8, 26.6) removed')


def rf_relief(b, log):
    """P4-RF-03 / P3-RF-02 / P3-DFM-05: C302.2 (the 10 nF bias-tee decoupler at L30's cold end; L30 is > 500 ohm at the
    GNSS bands, so a spoke's inductance in its ground is immaterial) goes back to the house thermal relief (m3.kicad_dru
    "Small GND pad thermal relief": 0.25 mm gap, 0.3 mm spokes), which evens the two pads' heating (tombstoning; pass-3
    DFM: 0.57 against 1.84 mm2 of copper within 0.5 mm when solid). Its GND via beside the pad (r7_route) stays.
    D30.2 / D31.2 stay solid: the ESD clamp's return inductance matters at the jack (RF review), and the parts are
    checked for tombstoning at first-article inspection instead (ORDERING §5, records)."""
    p = next(q for q in b.FindFootprintByReference('C302').Pads() if q.GetNumber() == '2')
    assert p.GetNetname() == 'GND' and p.GetLocalZoneConnection() == pcbnew.ZONE_CONNECTION_FULL
    p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    log.append('  C302.2: solid -> thermal relief')


# --- fix pass 6 (sources/r7_review/pass6_*.md, pass6_verdicts.json; record: fix6_F7_handoff.md) ---------------------

def qspi6(b, log):
    """P6-ROUTING_QUALITY-01: QSPI_IO3's inherited R6 square bump (N, W 1.2, N 1.0, E 1.2, N between its via
    (22.5, 40.3) and (22.5, 35.4); +2.4 mm, four 90 deg corners on a QSPI line) holds nothing: one straight F.Cu segment
    replaces it (0.205 mm to U3.8, the gap the run beside U3.8 already had; pass-6 review, re-checked here)."""
    redraw(b, log, 'QSPI_IO3', 'QSPI_IO3', 'F', 0.2,
           [((22.5, 40.3), (22.5, 37.7)), ((22.5, 37.7), (21.3, 37.7)), ((21.3, 37.7), (21.3, 36.7)),
            ((21.3, 36.7), (22.5, 36.7)), ((22.5, 36.7), (22.5, 35.4))],
           [[(22.5, 40.3), (22.5, 35.4)]])


def sw6(b, log):
    """P6-ROUTING_GEOMETRY-01 (allowlist A3-A5): SW_NODE's B.Cu run C5.1 -> L1.1 took a 0.566 mm drop out of C5.1 and a
    0.4 mm step through the C7.2 / C9.2 gap (a tiny jog and two short segments). The pass-6 review's redraw ends 0.2 mm
    further inside L1.1's 1.6 x 3.5 mm pad and needs neither: SE 0.849, E 1.70, NE 1.414, E 0.70 (the straight piece in
    the gap, 0.245 mm to C7.2), NE 1.697. Minimum gap 0.213 mm (3V3 via (18.7, 35.28); the present copper had 0.170);
    +0.37 mm of switching-node track (5.99 -> 6.36 mm, about +0.22 mm2 of the node's ~10.6 mm2). U2.5 -> C5.1 (0.4 mm),
    the input capacitors and the GND returns are untouched."""
    redraw(b, log, 'SW_NODE', 'SW_NODE', 'B', 0.6,
           [((17.92, 35.65), (18.32, 36.05)), ((18.32, 36.05), (20.52, 36.05)), ((20.52, 36.05), (21.32, 35.25)),
            ((21.32, 35.25), (21.72, 35.25)), ((21.72, 35.25), (22.92, 34.05))],
           [[(17.92, 35.65), (18.52, 36.25), (20.22, 36.25), (21.22, 35.25), (21.92, 35.25), (23.12, 34.05)]])


def logic_ss6(b, log):
    """P6-ROUTING_GEOMETRY-02: LOGIC_SS (B.Cu) left U11.11 with S 0.5, SW 0.707, then a knee S 0.35 / W 0.55 back onto
    a SW line 0.141 mm off the first (a jog with a two-segment middle, which route_check now counts). U11.11's pad
    edge (0.3 mm S, inside the pad) and one SW diagonal reach the S run at (27.55, 31.05): 0.183 mm to U11.12 (GND),
    0.187 mm to the GND via (28.13, 31.3) (the present minimum), 0.32 mm shorter."""
    redraw(b, log, 'LOGIC_SS', 'LOGIC_SS', 'B', 0.2,
           [((28.95, 29.35), (28.95, 29.85)), ((28.95, 29.85), (28.45, 30.35)), ((28.45, 30.35), (28.45, 30.7)),
            ((28.45, 30.7), (27.9, 30.7)), ((27.9, 30.7), (27.55, 31.05))],
           [[(28.95, 29.35), (28.95, 29.65), (27.55, 31.05)]])


def servo_fault6(b, log):
    """P6-REGRESSION-02: fix pass 5 straightened CAM_FAULT_N (x 15.19) and SERVO4_MCU (x 15.505) into side-by-side In2
    runs 0.165 mm apart over 22.9 mm (the base kept 0.47 mm). They part again without a jog or staircase:
    - CAM_FAULT_N leaves its F.Cu via (14.0457, 77.0649) in one SE diagonal onto x 14.6414, runs straight through its
      via (14.6414, 90.8244) (no stub) to y 91.85, steps SE 0.776 mm (offset 0.549) onto x 15.19 and runs on as before
      (the step ends 0.40 mm from CAM_PWR_EN's via (14.65, 92.95), which fixes x 15.19 below it);
    - SERVO4_MCU runs straight down x 15.505 (0.714 mm from CAM_FAULT_N) to y 91.3, past the 3V3 via (16.3, 90.525),
      steps SE 0.707 mm onto x 16.005 (0.665 mm from CAM_FAULT_N's x 15.19) and ends in its old diagonal into
      (18.005, 103.6268).
    The two steps are parallel 0.85 mm apart. The end pieces (the parallel diagonals into y 103.6 / 103.9 and the E
    runs) are the base's and stay: SERVO4's E run cannot move north (RAW_PROTECTED's via (18.05, 102.87)) nor
    CAM_FAULT_N's south (GND vias (24.55, 104.47) / (25.45, 104.47))."""
    redraw(b, log, 'CAM_FAULT_N', 'CAM_FAULT_N', 'In2', 0.15,
           [((14.0457, 77.0649), (15.19, 78.2092)), ((15.19, 78.2092), (15.19, 101.2976)),
            ((15.19, 90.8244), (14.6414, 90.8244))],
           [[(14.0457, 77.0649), (14.6414, 77.6606), (14.6414, 90.8244)],
            [(14.6414, 90.8244), (14.6414, 91.85), (15.19, 92.3986), (15.19, 101.2976)]])
    redraw(b, log, 'SERVO4_MCU', 'SERVO4_MCU', 'In2', 0.15,
           [((15.505, 67.1496), (15.505, 101.1268)), ((15.505, 101.1268), (18.005, 103.6268))],
           [[(15.505, 67.1496), (15.505, 91.3), (16.005, 91.8), (16.005, 101.6268), (18.005, 103.6268)]])


def v3v3_6(b, log):
    """P6-DOCS-01: the 3V3 F.Cu branch from the via (31.1, 54.5) to the T (36.5, 51.65) still dipped south to y 56.05,
    round R6's C179.1 that R7 removed (r7_redraw drew the dip from the trimmed corner): 9.44 mm for 6.58. It now runs
    E 2.55 and on the T's own NE line (x + y = 88.15) into it: 6.58 mm, minimum gap 0.47 mm (SERVO2_MCU's via
    (30.7, 55.3); the dip passed PULLPIN's via at 0.168 mm) (pass-6 review's probe, re-checked here)."""
    redraw(b, log, '3V3 C179 dip', '3V3', 'F', 0.25,
           [((31.1, 54.5), (32.65, 56.05)), ((32.65, 56.05), (34.7833, 56.05)), ((34.7833, 56.05), (35.0667, 55.7667)),
            ((35.0667, 55.7667), (35.0667, 53.0833)), ((35.0667, 53.0833), (36.5, 51.65))],
           [[(31.1, 54.5), (33.65, 54.5), (36.5, 51.65)]])


RAW_ACT_DUP = [(10.0, 90.78), (12.5, 93.28), (12.5, 100.18), (11.2, 101.48), (11.2, 106.78), (11.8, 107.38),
               (11.8, 110.38), (11.5, 110.68), (8.7, 110.68), (4.0, 105.98)]


def raw_act6(b, log):
    """P6-DOCS-01: RAW_ACT's 0.2 mm B.Cu run J124.2 -> Q121.9 (31.29 mm, 9 segments, 11.65 mm of it inside the BAT_IN
    B.Cu pour outline) duplicates the RAW_ACT F.Cu pour, which joins J124.2 (a plated hole in R6_RAW_ACT_F's one fill
    island) to Q121 already and carried 98 % of the current. Deleted (tools/dc_solve.py, 0.1 mm): RAW_ACT Q121:5-9 ->
    J124:2 1.47 -> 1.50 mOhm (pyro bus feed through the ARM plug); Q121:5-9 -> J122 (7.7 A) 3.95 -> 3.98 mOhm (+0.8 %,
    +1.8 mW), its peak current density (5.75 A/mm) and neck, which set the IPC-2152 estimate, unchanged."""
    lib.fill(b)
    before = hy.pad_groups(b, {'RAW_ACT'})['RAW_ACT']
    redraw(b, log, 'RAW_ACT duplicate', 'RAW_ACT', 'B', 0.2, list(zip(RAW_ACT_DUP, RAW_ACT_DUP[1:])), [])
    lib.fill(b)
    after = hy.pad_groups(b, {'RAW_ACT'})['RAW_ACT']
    # the run's whole point: J124.2 leaves Q121's group by tracks alone (run() lets exactly this split through,
    # SPLIT_OK); with the pours joining, every pad group stays the same
    assert after[1] == before[1], ('RAW_ACT connectivity with the pours changed', before[1], after[1])
    j = [g for g in after[0] if any(p.startswith('J124.2') for p in g)]
    q = [g for g in after[0] if any(p.startswith('Q121.9') for p in g)]
    assert j and q and j[0] != q[0], 'J124.2 should no longer share a track group with Q121.9'
    assert {p for g in before[0] for p in g} == {p for g in after[0] for p in g}
    assert all(any(g <= h for h in before[0]) for g in after[0]), 'only the J124.2 / Q121 track group splits'
    log.append(f'  RAW_ACT track-only groups {len(before[0])} -> {len(after[0])} (J124.2 now joins Q121 through the '
               f'F.Cu pour only); groups with the pours unchanged ({len(after[1])})')


def ties6(b, log):
    """P6-DOCS-01, route_check's new chain_detour test on poured nets: the runs a straight or one-bend drawing replaces
    (alt_audit's candidates, each checked here):
    - GND F.Cu J1.2 -> GND via (24.55, 108.05): W, SW, N, NE round nothing (3.07 mm): one N run from inside J1.2's
      2.6 mm round pad (1.18 mm from its centre) into the via (0.55 mm to BAT_SW_RETURN);
    - GND F.Cu J3.4 -> J3.A1B12 and J3.1 -> J3.B1A12 (USB-C shell legs to the GND contacts): E, S, SW and E, N, W round
      the outside of the contact row (2.76 / 3.38 mm): one 0.9 mm run each from inside the 2.1 mm shell pad straight
      into the contact (0.40 mm to the VBUS contacts J3.A4B9 / J3.B4A9);
    - GND B.Cu J3.1 -> R85.2: W, S, SE, S (4.95 mm): one 3.0 mm run from inside J3.1 down R85.2's centre line into its
      centre (0.82 mm to BUZZ_G);
    - GND B.Cu J3.1 -> C28.2: E, N, NW, N, NE, E, N (7.30 mm, a knee into C28.2), which J3.1's old west branch boxed in:
      with that branch gone (above) NW 1.65, N 1.90, NE 2.34 (5.90 mm; the shortest redraw that keeps the 0.25 mm
      copper-to-hole rule from J3's non-plated locating peg (5.81, 78.19): 0.267 mm; 0.29 mm to C28.1);
    - GND F.Cu R130.2 -> R178.2 (an L, 2.19 mm): the L with its corner chamfered (N 0.7, NE 0.64, E 0.59; 1.93 mm). The
      octilinear-shortest line (N 0.11, NE 1.47) passes R130.1 (PYRO1_CONT) at 0.170 mm; this keeps 0.30 mm;
    - 3V3A B.Cu via (35.5, 76.54) -> via (37.4, 76.52), round the GND via (36.5, 76.54) between them: the same NE / E /
      SE shape with the E piece 0.12 mm lower (2.505 -> 2.404 mm; 0.169 mm to that GND via, was 0.34: recorded);
    - ACT_FET_S B.Cu R120.1 -> Q120.1 (N, E, N, NW round nothing inside its own pour, 3.60 mm): N 1.36 and NE 1.05 into
      Q120.1 (0.377 mm to R120.2, ACT_GATE)."""
    redraw(b, log, 'GND J1.2', 'GND', 'F', 0.2,
           [((25.17, 109.8), (24.17, 109.8)), ((24.17, 109.8), (23.97, 109.6)), ((23.97, 109.6), (23.97, 108.63)),
            ((23.97, 108.63), (24.55, 108.05))],
           [[(24.55, 109.75), (24.55, 108.05)]])
    redraw(b, log, 'GND J3.4', 'GND', 'F', 0.2,
           [((6.31, 70.975), (7.6317, 70.975)), ((7.6317, 70.975), (7.6317, 71.3483)), ((7.6317, 71.3483), (6.88, 72.1))],
           [[(6.88, 71.2), (6.88, 72.1)]])
    redraw(b, log, 'GND J3.1 F', 'GND', 'F', 0.2,
           [((6.31, 79.625), (7.7217, 79.625)), ((7.7217, 79.625), (7.7217, 78.5)), ((6.88, 78.5), (7.7217, 78.5))],
           [[(6.88, 79.4), (6.88, 78.5)]])
    redraw(b, log, 'GND J3.1 B', 'GND', 'B', 0.2,
           [((6.31, 79.625), (4.9883, 79.625)), ((4.9883, 79.625), (4.9883, 79.9859)), ((4.9883, 79.9859), (6.0062, 81.0038)),
            ((6.0062, 81.0038), (6.0062, 82.8312))],
           [[(6.175, 80.0), (6.175, 83.0)]])
    redraw(b, log, 'GND J3.1 C28', 'GND', 'B', 0.2,
           [((6.31, 79.625), (7.6317, 79.625)), ((7.6317, 79.625), (7.6317, 78.7793)), ((7.6317, 78.7793), (6.0702, 77.2178)),
            ((6.0702, 77.2178), (6.0702, 75.7873)), ((6.0702, 75.7873), (6.2858, 75.5717)), ((6.2858, 75.5717), (6.8, 75.5717)),
            ((6.8, 74.9), (6.8, 75.5717))],
           [[(6.31, 79.625), (5.1433, 78.4583), (5.1433, 76.5567), (6.8, 74.9)]])
    redraw(b, log, 'GND R130.2', 'GND', 'F', 0.25, [((25.97, 87.9), (25.97, 86.75)), ((25.97, 86.75), (27.01, 86.75))],
           [[(25.97, 87.9), (25.97, 87.2), (26.42, 86.75), (27.01, 86.75)]])
    redraw(b, log, '3V3A hop', '3V3A', 'B', 0.3,
           [((35.5, 76.54), (36.24, 75.8)), ((36.24, 75.8), (36.68, 75.8)), ((36.68, 75.8), (37.4, 76.52))],
           [[(35.5, 76.54), (36.1187, 75.9213), (36.8013, 75.9213), (37.4, 76.52)]])
    redraw(b, log, 'ACT_FET_S R120.1', 'ACT_FET_S', 'B', 0.4,
           [((5.17, 96.0), (5.17, 95.0)), ((5.17, 95.0), (6.45, 95.0)), ((6.45, 95.0), (6.45, 94.44)),
            ((6.45, 94.44), (5.91, 93.9))],
           [[(5.17, 96.0), (5.17, 94.64), (5.91, 93.9)]])


BAT_IN_F_VIAS = [(9.7, 31.75), (9.7, 35.5)]       # 0.6/0.3 mm BAT_IN vias, BAT_IN_F -> In2 BAT_IN


def bat_in_f6(b, log):
    """P6-REGRESSION-01: band_end took the BAT_IN_F pour's two stitch vias (7.6, 26.6) / (8.8, 26.6) out with the band
    end of the In2 BAT_IN arm, so C89 / C95 (2 x 22 uF at U9's input, TI SLVSFC9C 8.3.1) reached BAT_IN only through
    C95.1's 0.2 mm track and a 0.03 mm2 touch of the via (9.2, 36.05) at the pour's edge. Inside BAT_IN_F the only spot
    for a via into In2 BAT_IN (which starts at y 31.61 now) is 0.60 mm from that via: TP89's 1.0 mm bare-pad keep-out
    and the radio corridor's B.Cu close the rest (fix pass 6, viaspot search). So BAT_IN_F grows east over GND F.Cu
    copper-free of signals to x 9.9 for y 31.4-36.9 (it now takes the via (9.2, 36.05) whole) and gets two BAT_IN vias
    there, (9.7, 31.75) and (9.7, 35.5), both inside the In2 BAT_IN fill and outside the band-end GND strip (y < 31.3),
    so no radio line crosses BAT_IN again. DC (tools/dc_solve.py, 0.1 mm): C89.1 -> U9.5 10.35 -> 7.05 mOhm (6.91 before
    band_end), C95.1 -> U9.5 7.37 -> 5.60 mOhm (6.57)."""
    z = [z for z in b.Zones() if z.GetZoneName() == 'BAT_IN_F']
    assert len(z) == 1
    o = z[0].Outline()
    old = [(round(mm(o.Outline(0).CPoint(k).x), 3), round(mm(o.Outline(0).CPoint(k).y), 3))
           for k in range(o.Outline(0).PointCount())]
    assert old == [(4.4, 25.7), (9.0, 25.7), (9.0, 36.9), (4.4, 36.9)], old
    o.RemoveAllContours()
    o.NewOutline()
    for x, y in [(4.4, 25.7), (9.0, 25.7), (9.0, 31.4), (9.9, 31.4), (9.9, 36.9), (4.4, 36.9)]:
        o.Append(MM(x), MM(y))
    for q in BAT_IN_F_VIAS:
        add_via(b, 'BAT_IN', q, 0.6)
    lib.fill(b)
    for q in BAT_IN_F_VIAS + [(9.2, 36.05)]:
        for lid in (F, IN2):
            assert any(zz.GetNetname() == 'BAT_IN' and zz.IsOnLayer(lid) and zz.HitTestFilledArea(lid, V(P(*q)), 0)
                       for zz in b.Zones() if not zz.GetIsRuleArea()), ('BAT_IN via not in its fill', q, lid)
    log.append(f'  BAT_IN_F to x 9.9 (y 31.4-36.9); BAT_IN vias {BAT_IN_F_VIAS} (F.Cu and In2 BAT_IN fills)')


# --- fix pass 7 (sources/r7_review/pass7_*.md, pass7_verdicts.json; record: fix7_F8_handoff.md) ---------------------

def bumps7(b, log):
    """P7-ROUTING-01: local bumps inside longer runs on power nets that the whole-run chain test cannot see (the pass-7
    review's sub-chain probe; route_check's local_bump test now gates them), each redrawn with the project's clearance
    machinery (gaps measured on the redraw, scratch f8/gap.py):
    - 3V3A B.Cu via (35.9632, 69.9393) -> (36.4, 60.86): the run bulged 1.83 mm east round NRST's via (36.3, 64.8)
      (R6 copper): NW, N on x 35.6096, NE back onto the x 36.4 run, 10.77 -> 9.55 mm (min gap 0.212 mm, PYRO1_CONT's
      via (35.78, 60.65); 0.315 mm to the NRST via it went round);
    - CAM_5V B.Cu U13.1 -> R104.1: a V dip south (37.0, 32.45) -> (36.0, 33.45) -> (35.48, 33.45) -> (34.23, 32.2)
      (R6): one west run at y 32.45 and a 45 deg step down x 34.23, 7.50 -> 6.62 mm (min gap 0.272 mm, C60.1);
    - VLOGIC F.Cu C99.1 -> (32.27, 29.2): a peak north to y 27.0 round D122.2 (R7 copper): NE, E at y 27.8, S,
      6.61 -> 6.02 mm (min gap 0.172 mm, C99.2, as before; 0.175 mm to D122.2);
    - 3V3 B.Cu (allowlist A34, the C100 feed round C11): from the via (36.94, 52.65) one SE diagonal and S down
      x 38.45 instead of S, SE, E, S, SW (0.175 mm to RAW_PROTECTED's via (37.85, 54.7)), and from (42.95, 57.15) N,
      NW, N into C100.1 instead of N, W, N (0.173 mm to CAM_RX_WIRE's via (42.175, 55.82)): 16.32 -> 14.37 mm.
    route_check's local-bump test also finds USB_LIMITED's C98.1 feed; its redraw would cut R105.2 off the GND copper
    (allowlisted with that reason)."""
    redraw(b, log, '3V3A bulge', '3V3A', 'B', 0.25,
           [((35.9632, 69.9393), (37.8632, 68.0393)), ((37.8632, 65.5392), (37.8632, 68.0393)),
            ((36.04, 63.716), (37.8632, 65.5392)), ((36.04, 61.22), (36.04, 63.716)), ((36.4, 60.86), (36.04, 61.22))],
           [[(35.9632, 69.9393), (35.6096, 69.5857), (35.6096, 61.6504), (36.4, 60.86)]])
    redraw(b, log, 'CAM_5V dip', 'CAM_5V', 'B', 0.2,
           [((34.23, 31.6), (34.23, 32.2)), ((34.23, 32.2), (35.48, 33.45)), ((35.48, 33.45), (36.0, 33.45)),
            ((37.0, 32.45), (36.0, 33.45)), ((40.2, 32.45), (37.0, 32.45))],
           [[(40.2, 32.45), (34.575, 32.45), (34.23, 32.105), (34.23, 31.6)]])
    redraw(b, log, 'VLOGIC peak', 'VLOGIC', 'F', 0.25,
           [((28.505, 29.85), (31.355, 27.0)), ((31.355, 27.0), (32.27, 27.915)), ((32.27, 27.915), (32.27, 29.2))],
           [[(28.505, 29.85), (30.555, 27.8), (32.27, 27.8), (32.27, 29.2)]])
    redraw(b, log, '3V3 C100 feed (west)', '3V3', 'B', 0.25,
           [((36.94, 52.65), (36.94, 53.0)), ((36.94, 53.0), (38.13, 54.19)), ((38.13, 54.19), (39.13, 54.19)),
            ((39.13, 54.19), (39.13, 56.07)), ((39.13, 56.07), (38.45, 56.75))],
           [[(36.94, 52.65), (38.45, 54.16), (38.45, 56.75)]])
    redraw(b, log, '3V3 C100 feed (east)', '3V3', 'B', 0.25,
           [((42.95, 57.15), (42.95, 54.5)), ((41.58, 54.5), (42.95, 54.5)), ((41.58, 53.9), (41.58, 54.5))],
           [[(42.95, 57.15), (42.95, 55.75), (41.58, 54.38), (41.58, 53.9)]])


def v3pair7(b, log):
    """P7-ROUTING-01 item 5 / P7-DOCS-01: the 3V3 via (30.4, 70.25) 0.95 mm from the via (30.17, 71.17), reached by a
    0.81 mm F.Cu stub T'd onto the latter's own F.Cu diagonal, started the 8.0 mm In2 run to the via (30.4, 78.25); the
    In2 run crossed the other via's ring (0.195 mm overlap, no node) and the B.Cu run (30.17, 65.1-71.17) crossed its
    ring the same way (R6 copper; r7_hygiene.v3v3 had moved the first via onto the B.Cu run). The second via and its stub
    go, and the In2 run starts at the via (30.17, 71.17): one 0.325 mm SE piece (0.025 mm of it outside the via's
    copper; the B.Cu run goes straight on through the via, so it is a fan-out, not a jog) onto x 30.4 and on to
    (30.4, 78.25). One via less, no overlap-only joint; In1 GND loses one antipad."""
    redraw(b, log, '3V3 via pair', '3V3', 'F', 0.25, [((30.4, 70.25), (29.825, 70.825))], [], vias_gone=[(30.4, 70.25)])
    redraw(b, log, '3V3 In2 run', '3V3', 'In2', 0.25, [((30.4, 78.25), (30.4, 70.25))],
           [[(30.17, 71.17), (30.4, 71.4), (30.4, 78.25)]])


def acten7(b, log):
    """Deviation C26 (removable, now removed): ACT_EN R122.2 -> Q122.1 ran B.Cu E, SE to a via (13.48, 106.06), an In2 run
    SW, W in a void of the R6_BAT_IN_In2 servo-current pour to a second via (11.15, 107.61), and B.Cu S into Q122.1
    0.05 mm off its centre (R6 copper; no reason for the hop was found). Now one B.Cu run from R122.2's centre S down
    x 11.75 and SW into Q122.1's centre (3.84 mm for 6.12 mm and two vias; 0.50 mm to R122.1, RAW_PROTECTED). The In2
    BAT_IN fill closes over the old run and its two antipads (J1 -> Q120 resistance in the record)."""
    redraw(b, log, 'ACT_EN In2 hop', 'ACT_EN', 'In2', 0.15,
           [((13.4814, 106.0636), (11.934, 107.611)), ((11.934, 107.611), (11.1483, 107.611))], [],
           vias_gone=[(13.4814, 106.0636), (11.1483, 107.611)])
    redraw(b, log, 'ACT_EN B.Cu', 'ACT_EN', 'B', 0.15,
           [((12.4478, 105.03), (11.75, 105.03)), ((13.4814, 106.0636), (12.4478, 105.03)),
            ((11.1483, 108.6), (11.1483, 107.611))],
           [[(11.75, 105.03), (11.75, 107.95), (11.1, 108.6)]])


def arm1_7(b, log):
    """Deviation C24 (ARM1_SENSE, removable): the F.Cu run from the via (14.55, 94.15) E and N into R133.1 passed through
    R180.1 (same net, the divider's other top resistor) without a node, so the via -> R133.1 run measured as one 4.48 mm
    chain for 3.46 and R180.1 hung on the track body. The vertical is split at R180.1's centre: via -> R180.1 (E 2.73,
    N 0.6) and R180.1 -> R133.1 (N 1.15) are pad-to-pad runs with a node in each pad. No copper moves (CH1 pyro
    geometry and every pyro clearance unchanged); the pass-through and the chain detour go."""
    redraw(b, log, 'ARM1_SENSE R180.1', 'ARM1_SENSE', 'F', 0.2, [((17.28, 94.15), (17.28, 92.4))],
           [[(17.28, 94.15), (17.28, 93.55)], [(17.28, 93.55), (17.28, 92.4)]])


def tidy7(b, log):
    """Deviation C25 (removable), each redraw clear of every other net's copper (scratch f8/gap.py):
    - CAM_FAULT_N In2 via (16.04, 67.46) -> via (19.82, 62.35): S, SE, E, NE, N, NE round nothing (10.52 mm; R6 copper)
      -> E 2.1, N 3.43, NE 2.37 (7.90 mm);
    - I2C1_SDA F.Cu U1.96 -> via (27.8, 59.3): N, NE up to y 59.05, E, SE back down into the via (3.47 mm) -> N 1.05,
      NE 0.99, E 1.25 into the via centre (3.29 mm; 0.275 mm to U1.95 / U1.97, the drawing E-then-NE keeps only 0.175).
    LED_RED's In2 bump north to y 39.15 between the vias (21.85, 41.85) and (30.85, 41.7), which the records called
    removable, stays: it goes round the part of the 3V3_In2 plane under QSPI_NCS's B.Cu run (25.0-26.4, 40.9-42.0).
    The straight run at y 41.85 cuts that reference: tools/critical_reference.py loses 465 QSPI_NCS samples (both
    methods; fix pass 7, a scratch build)."""
    redraw(b, log, 'CAM_FAULT_N bump', 'CAM_FAULT_N', 'In2', 0.15,
           [((16.0438, 67.4556), (15.9862, 67.5132)), ((15.9862, 67.5132), (15.9862, 68.8727)),
            ((15.9862, 68.8727), (16.3174, 69.204)), ((16.3174, 69.204), (16.8299, 69.204)),
            ((16.8299, 69.204), (18.137, 67.8968)), ((18.137, 67.8968), (18.137, 64.0306)),
            ((18.137, 64.0306), (19.8205, 62.3471))],
           [[(16.0438, 67.4556), (18.1438, 67.4556), (18.1438, 64.0238), (19.8205, 62.3471)]])
    redraw(b, log, 'I2C1_SDA', 'I2C1_SDA', 'F', 0.15,
           [((25.85, 61.05), (25.85, 60.05)), ((25.85, 60.05), (26.85, 59.05)), ((26.85, 59.05), (27.55, 59.05)),
            ((27.55, 59.05), (27.8, 59.3))],
           [[(25.85, 61.05), (25.85, 60.0), (26.55, 59.3), (27.8, 59.3)]])


def sense7(b, log):
    """P7-ROUTING-02: two non-critical In2 runs whose recorded reasons (LEFTOVERS CAM_5V_SENSE, SERVO2_OUT) a clean
    redraw contradicted (pass-7 review, variants c5s / s2o):
    - CAM_5V_SENSE In2 via (33.25, 29.85) -> via (32.05, 37.55): W 3.4, SW, S 4.5, SE (12.43 mm), which also fenced a
      17.6 mm2 piece of the 3V3_In2 plane off the main plane -> NW, NE, NW (10.89 mm; 0.18 mm to VLOGIC_SENSE's
      parallel In2 run); the piece rejoins the plane;
    - SERVO2_OUT In2 via (18.01, 93.1) -> (22.59, 96.21): S 3.6, E 4.09, NE -> SE 5.05, E 0.54, NE (37.07 -> 34.94 mm
      for the net; 0.17 mm, as before)."""
    redraw(b, log, 'CAM_5V_SENSE In2', 'CAM_5V_SENSE', 'In2', 0.15,
           [((33.25, 29.85), (29.85, 29.85)), ((29.85, 29.85), (29.35, 30.35)), ((29.35, 30.35), (29.35, 34.85)),
            ((29.35, 34.85), (32.05, 37.55))],
           [[(32.05, 37.55), (30.3353, 35.8353), (34.7853, 31.3853), (33.25, 29.85)]])
    redraw(b, log, 'SERVO2_OUT In2', 'SERVO2_OUT', 'In2', 0.15,
           [((18.0132, 93.1), (18.0132, 96.7)), ((22.0987, 96.7), (18.0132, 96.7)), ((22.5903, 96.2084), (22.0987, 96.7))],
           [[(18.0132, 93.1), (21.5841, 96.6709), (22.1278, 96.6709), (22.5903, 96.2084)]])


def bat_via7(b, log):
    """P7-ROUTING-03: fix pass 6's BAT_IN via (9.7, 35.5) sat on the body of the B.Cu BAT_IN run D8.1 -> via (9.2, 36.05),
    35 um off its centre line with no track end in it (a joint made by overlap only). No spot clear of the run is legal
    (TP89's 1.0 mm bare-pad keep-out west of the line, the via (9.2, 36.05) and BAT_ILIM's F.Cu run east of it), so
    the via moves 35 um onto the run's line, (9.725, 35.525), and the run is split there: the via is a node of the
    run. It stays inside the BAT_IN_F (F.Cu) and In2 BAT_IN fills (asserted)."""
    move_via(b, 'BAT_IN', (9.7, 35.5), (9.725, 35.525), log=log, why='onto the B.Cu run\'s centre line')
    redraw(b, log, 'BAT_IN run split', 'BAT_IN', 'B', 0.2, [((11.9, 33.35), (9.2, 36.05))],
           [[(11.9, 33.35), (9.725, 35.525)], [(9.725, 35.525), (9.2, 36.05)]])
    lib.fill(b)
    for lid in (F, IN2):
        assert any(z.GetNetname() == 'BAT_IN' and z.IsOnLayer(lid) and z.HitTestFilledArea(lid, V(P(9.725, 35.525)), 0)
                   for z in b.Zones() if not z.GetIsRuleArea()), ('BAT_IN via not in its fill', lid)


def v3a_hop7(b, log):
    """P7-ROUTING-04 / P7-REGRESSION-02: fix pass 6 lowered the E leg of the 3V3A B.Cu hop via (35.5, 76.54) -> via
    (37.4, 76.52) by 0.12 mm, which passed route_check's chain test by 4 um while the run still went round the GND via
    (36.5, 76.54) (U4.6 / U4.7's return via, on the straight line between the two vias), and cut its gap to that via
    from 0.200 to 0.169 mm. The fix-pass-5 drawing is restored (NE, E at y 75.8, SE; 2.505 mm; min gap 0.200 mm, set by
    the SE diagonal into the east via's centre, whose line the via positions fix) and allowlisted with that reason.
    The hop is kept although both vias also join the one 3V3A_In2 island: it is U4.5's (VDDIO) short path to C31 / C30
    at U4.8 (Inference: via-island-via adds about 1 nH)."""
    redraw(b, log, '3V3A hop', '3V3A', 'B', 0.3,
           [((35.5, 76.54), (36.1187, 75.9213)), ((36.1187, 75.9213), (36.8013, 75.9213)),
            ((36.8013, 75.9213), (37.4, 76.52))],
           [[(35.5, 76.54), (36.24, 75.8), (36.68, 75.8), (37.4, 76.52)]])


BAT_IN_B_OUTLINE = [(0.6, 80.9), (13.6, 80.9), (13.6, 94.4), (10.2, 94.4), (10.2, 92.9), (0.6, 92.9)]
# fix pass 7: a 0.1 mm notch from the outline's south edge up the line of the deleted RAW_ACT leg into J124.2's
# clearance void
BAT_IN_B_FENCED = [(0.6, 80.9), (13.6, 80.9), (13.6, 94.4), (12.55, 94.4), (12.55, 93.26), (10.95, 91.66),
                   (10.88, 91.73), (12.45, 93.3), (12.45, 94.4), (10.2, 94.4), (10.2, 92.9), (0.6, 92.9)]
BAT_IN_B_AREA = (69.8, 71.0)    # mm2: the fill before raw_act6 (69.84) plus the strip the deleted leg and its 0.3 mm
                                # clearance kept free west of the notch (70.85 measured; asserted)


def bat_in_b7(b, log):
    """P7-REGRESSION-01: raw_act6 deleted RAW_ACT's B.Cu duplicate, whose SE leg (10.0, 90.78) -> (12.5, 93.28) -> S had
    fenced the north-east part of the BAT_IN_B outline off its fill (an island, removed). With the leg gone BAT_IN_B
    filled a 24.2 mm2 lobe that holds no BAT_IN pad or via (joined only along the leg's line SE of J124.2) and took
    27.9 mm2 of GND B.Cu, putting battery voltage 0.3 mm from 3V3, RAW_ACT, USB_ILIM, BUZZ_* and ARM1_SENSE copper. A
    0.1 mm notch in the outline along the leg's line, from the south edge into J124.2's clearance void, fences the lobe
    off again: BAT_IN_B is back to its fix-pass-5 fill (asserted; +1.0 mm2 west of the notch where the leg and its clearance
    ran), GND B.Cu refills the lobe, the deletion stays."""
    z = [z for z in b.Zones() if z.GetZoneName() == 'BAT_IN_B']
    assert len(z) == 1
    o = z[0].Outline()
    old = [(round(mm(o.Outline(0).CPoint(k).x), 3), round(mm(o.Outline(0).CPoint(k).y), 3))
           for k in range(o.Outline(0).PointCount())]
    assert old == BAT_IN_B_OUTLINE, old
    o.RemoveAllContours()
    o.NewOutline()
    for x, y in BAT_IN_B_FENCED:
        o.Append(MM(x), MM(y))
    lib.fill(b)
    f = z[0].GetFilledPolysList(B)
    area = f.Area() / 1e12
    assert f.OutlineCount() == 1 and BAT_IN_B_AREA[0] <= area <= BAT_IN_B_AREA[1], (f.OutlineCount(), area)
    assert mm(f.BBox().GetRight()) <= 12.46, ('BAT_IN_B fill still east of the notch', mm(f.BBox().GetRight()))
    log.append(f'  BAT_IN_B outline notched along the deleted RAW_ACT leg; fill {area:.2f} mm2 (fix pass 5: 69.84)')


def dup7(b, log):
    """P7-DOCS-02 (b), deviation C23: two 3V3 hops duplicated the 3V3_In2 plane, both of whose vias already lie in its
    fill (measured on the fix-pass-7 copper; sense7 rejoined the 17.6 mm2 piece that held the second to the main plane):
    - F.Cu via (27.35, 44.25) -> via (29.9, 43.625) (S 0.21 mm, SE, E; 2.93 mm): U1.27's via to the R164 branch's via;
    - In2 via (30.63, 31.34) -> via (32.33, 33.04) (2.40 mm), lying wholly inside the plane's fill.
    Both go; each via keeps its own track ends and its plane contact. Like raw_act6, the stage splits 3V3's track-only
    pad groups by design (SPLIT_OK) and asserts itself that the groups with the pours joining are unchanged."""
    lib.fill(b)
    before = hy.pad_groups(b, {'3V3'})['3V3']
    redraw(b, log, '3V3 F.Cu hop', '3V3', 'F', 0.25,
           [((27.35, 44.25), (27.35, 44.0438)), ((27.35, 44.0438), (27.7688, 43.625)), ((27.7688, 43.625), (29.9, 43.625))],
           [])
    redraw(b, log, '3V3 In2 run', '3V3', 'In2', 0.25, [((30.63, 31.3417), (32.33, 33.0417))], [])
    lib.fill(b)
    for q in ((27.35, 44.25), (29.9, 43.625), (30.63, 31.3417), (32.33, 33.0417)):
        assert any(z.GetNetname() == '3V3' and z.IsOnLayer(IN2) and z.HitTestFilledArea(IN2, V(P(*q)), 0)
                   for z in b.Zones() if not z.GetIsRuleArea()), ('3V3 via not in the In2 plane', q)
    after = hy.pad_groups(b, {'3V3'})['3V3']
    assert after[1] == before[1], '3V3 connectivity with the pours changed'
    log.append(f'  3V3 track-only groups {len(before[0])} -> {len(after[0])}; groups with the pours unchanged '
               f'({len(after[1])})')


def review7(b, log):
    """route_check --bumps-all (fix pass 7: the local-bump search on the non-critical nets, information) finds removable
    bumps on non-critical nets too; the ones whose redraw keeps or widens the run's own minimum gap are redrawn (gaps
    from scratch f8/gap.py; DRC, the pours and critical_reference checked on the build):
    - BUZZ_DRV B.Cu (7.0, 56.15) -> (4.3, 71.25): W 4.45 to x 1.55, S past the west side of the M3 hole (4, 64), SE back
      (21.10 mm) -> S down x 7.0, SW past the hole's east side (0.517 mm from its edge against the 0.5 mm edge rule; the
      old run passed its west side at 0.775 mm), S on x 4.3, merged with the run below (16.22 mm; min gap 0.325 mm,
      C96.2);
    - IMU_INT1 B.Cu (26.3, 66.3) -> (26.55, 67.95): a SE / SW point to x 27.25 (2.33 mm) -> SE, S, SW (2.07 mm), the same
      0.191 mm to the SERVO1_MCU / SERVO2_MCU vias.
    Not redrawn (recorded): VLOGIC_SENSE In2 (0.33 mm shorter only 0.165 mm from a GND via, was 0.199), BAT_SW_SOURCE
    F.Cu (1.80 mm shorter with 0.187 mm on a harness line, was 0.725; pass-7 review's judgement) and SERVO2_MCU B.Cu
    below its via (30.7, 55.3) (SW, S, SE, S, SW -> SE, S, SW, 0.19 mm shorter: the redraw cuts the B.Cu GND that
    references QSPI_IO2's In2 run (30.6-31.7, y 56.3), 179 samples lost by critical_reference --extended)."""
    redraw(b, log, 'BUZZ_DRV', 'BUZZ_DRV', 'B', 0.15,
           [((7.0, 56.15), (7.0, 58.05)), ((7.0, 58.05), (6.45, 58.6)), ((6.45, 58.6), (2.0, 58.6)),
            ((2.0, 58.6), (1.55, 59.05)), ((1.55, 59.05), (1.55, 68.5)), ((1.55, 68.5), (4.3, 71.25)),
            ((4.3, 71.25), (4.3, 85.1))],
           [[(7.0, 56.15), (7.0, 64.1), (4.3, 66.8), (4.3, 85.1)]])
    redraw(b, log, 'IMU_INT1', 'IMU_INT1', 'B', 0.15,
           [((26.3, 66.3), (27.25, 67.25)), ((27.25, 67.25), (26.55, 67.95))],
           [[(26.3, 66.3), (26.9364, 66.9364), (26.9364, 67.5636), (26.55, 67.95)]])
    # the edge clearance at the M3 hole (r7_hygiene.Clearance holds no board edge): 0.5 mm from the hole's edge
    hole, r = P(4.0, 64.0), MM(1.6)
    t = find_track(b, 'BUZZ_DRV', 'B', (7.0, 64.1), (4.3, 66.8))
    assert rc.pt_seg(hole, hy.xy(t.GetStart()), hy.xy(t.GetEnd()))[0] - r - t.GetWidth() / 2 >= MM(rc.EDGE_CLEAR), \
        'BUZZ_DRV too near the M3 hole (4, 64)'


ACT_FET_S_B_OUTLINE = [(2.7, 93.3), (7.5, 93.3), (7.5, 94.9), (5.3, 94.9), (5.3, 103.0), (1.3, 103.0), (1.3, 94.8),
                       (2.7, 94.8)]
ACT_FET_S_B_WIDE = [(2.7, 93.3), (7.5, 93.3), (7.5, 94.9), (5.3, 94.9), (5.3, 103.0), (0.6, 103.0), (0.6, 94.8),
                    (2.7, 94.8)]
CROSSBAR_VIAS = [(9.45, 109.8), (9.45, 111.3), (9.45, 112.8), (9.45, 114.3), (9.95, 104.05), (10.2, 107.8)]


def necks7(b, log):
    """Deviation C1 (IPC-2152, bounded local rework, no part moved; neck widths from the equipotential cuts of the 7.7 A
    solve, scratch f8/dc_ipc.py at 0.1 mm, in the record):
    - RAW_ACT Q121 -> J122 (F.Cu): the neck (2.02 mm at 0.1 mm) ran between the zone notch corner (21.0, 85.8) and R6's
      GND via (18.975, 83.85), which with its 0.3 mm F.Cu track from C86.2 walled the band off from C86 down to
      y 84.45. C86 (USB_LIMITED's capacitor) keeps its GND through its thermal connection to GND_F (J122.3, a plated GND
      pin, 2.4 mm away); the via and track go. The neck moves to the arm under J122 (2.95 mm, the arm's own width
      between J122's GND and signal pin columns); the notch stays (it keeps RAW_ACT off the pyro block);
    - ACT_FET_S Q120 -> Q121 (B.Cu): the pour's west edge moves from x 1.3 to 0.6 (the board edge clearance holds the
      fill at 0.5 mm; only a GND B.Cu edge strip was there): the neck at C120.2 (2.10 mm) widens, the narrowest cut is now
      2.64 mm at Q120's source row, between Q120.4 (ACT_GATE) and R120 (ACT_GATE's resistor);
    - BAT_IN J1 -> Q120: R6's F.Cu crossbar pour (R6_BAT_IN_crossbar_F, 232 mm2 beside J1) joined the In2 pour only
      through J1.1's barrel, so it carried nothing; six 0.6/0.3 mm BAT_IN vias at its west end, each inside both fills
      (asserted), put it in parallel with the In2 band past J1.2: J1 -> Q120 3.90 -> 3.03 mOhm at 0.1 mm, the J1.2
      neck (3.61 mm) is relieved and the narrowest cut (3.66 mm) is now in the In2 arm where ACT_GATE's In2 run
      crosses it."""
    redraw(b, log, 'C86.2 GND via', 'GND', 'F', 0.3, [((18.275, 82.15), (18.975, 82.85)), ((18.975, 82.85), (18.975, 83.85))],
           [], vias_gone=[(18.975, 83.85)])
    z = [z for z in b.Zones() if z.GetZoneName() == 'ACT_FET_S_B']
    assert len(z) == 1
    o = z[0].Outline()
    old = [(round(mm(o.Outline(0).CPoint(k).x), 3), round(mm(o.Outline(0).CPoint(k).y), 3))
           for k in range(o.Outline(0).PointCount())]
    assert old == ACT_FET_S_B_OUTLINE, old
    o.RemoveAllContours()
    o.NewOutline()
    for x, y in ACT_FET_S_B_WIDE:
        o.Append(MM(x), MM(y))
    lib.fill(b)
    zf = [z for z in b.Zones() if z.GetZoneName() == 'R6_BAT_IN_crossbar_F'][0]
    zi = [z for z in b.Zones() if z.GetZoneName() == 'R6_BAT_IN_In2'][0]
    for q in CROSSBAR_VIAS:
        for zz, lid in ((zf, F), (zi, IN2)):         # the whole ring inside both fills
            assert all(zz.HitTestFilledArea(lid, V(P(q[0] + 0.3 * math.cos(k * math.pi / 4), q[1] + 0.3 * math.sin(
                k * math.pi / 4))), 0) for k in range(8)), ('crossbar via outside its fill', q, b.GetLayerName(lid))
        add_via(b, 'BAT_IN', q, 0.6)
    lib.fill(b)
    log.append(f'  ACT_FET_S_B west edge 1.3 -> 0.6 mm; BAT_IN crossbar vias {CROSSBAR_VIAS}')


GNDV_EXPECTED = {'gnd_vias': 1, 'gnd_vias2': 0}   # GND return vias each pass adds (asserted)


def gnd_vias(b, log, name='gnd_vias'):
    """P4-ROUTING_GEOMETRY-01: r7_hygiene.gnd_vias (the GND return via search: a GND via within 1.5 mm of every
    critical-signal layer change, where legal) again on the polished copper, then its fine pass (0.025 mm grid,
    r7_hygiene.gnd_spots: the search tools/route_check's allowlist audit runs). Fix pass 3's SWCLK reroute freed the
    spot beside PYRO1_GATE_N's layer change (23.0, 88.33): a 0.6/0.3 mm via at (22.85, 89.63), 1.31 mm away (pass-4
    review's projfit); the search finds it. Run again after the strip stitching (gnd_vias2, nothing to add)."""
    before = len(vias_of(b, 'GND'))
    hy.gnd_vias(b, log, fine=0.025)
    added = len(vias_of(b, 'GND')) - before
    assert added == GNDV_EXPECTED[name], (name, added)


def gnd_vias2(b, log):
    gnd_vias(b, log, 'gnd_vias2')


TRIM_EXPECTED = {'pour_trim': 23, 'pour_trim2': 0}   # rule areas each trim stage adds (asserted; fix pass 6: 23 -> 22,
                                                     # ties6's 3V3A redraw left no GND B.Cu finger at (35.8-38.7, 75-77);
                                                     # fix pass 7: 22 -> 23, v3a_hop7 restores that drawing and finger)
STITCH_EXPECTED = 3                                    # GND vias strip_stitch adds (asserted)


def touching(b):
    """{(pad key, layer)} of the pads with a thermal or solid pour connection that touch their pour's fill."""
    return {k for k, (net, conn, inside, touch) in rc.pad_contacts(b).items() if conn != 'none' and inside and touch}


def _trim_areas(b, pieces, rings, made):
    """Keep-out rule areas over pieces (minus rings, {(net, layer): poly}): the new zones."""
    import r5_pcb as base                        # noqa: E402 (rule_area helper)
    by_layer = {}
    for pc in pieces:                          # a sliver and the finger round it are one keep-out
        poly = pcbnew.SHAPE_POLY_SET(pc['poly'])
        poly.Inflate(MM(0.02), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 5000)
        ring = rings.get((pc['net'], pc['lid']))
        if ring is not None:
            poly.BooleanSubtract(ring)
        u = by_layer.setdefault(pc['lid'], pcbnew.SHAPE_POLY_SET())
        u.BooleanAdd(poly)
    new = []
    for lid, u in sorted(by_layer.items()):
        u.Simplify()
        for o in range(u.OutlineCount()):
            ch = u.Outline(o)
            one = pcbnew.SHAPE_POLY_SET()
            one.AddOutline(ch)
            if one.Area() < MM(0.05) * MM(0.05):
                continue                       # a crumb the ring cut leaves: nothing to keep out
            pts = [(mm(ch.CPoint(i).x), mm(ch.CPoint(i).y)) for i in range(ch.PointCount())]
            bb = ch.BBox()
            box = [round(mm(v), 2) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]
            kinds = sorted({pc['cat'] for pc in pieces if pc['lid'] == lid and
                            not (pc['box'][2] < bb.GetLeft() or pc['box'][0] > bb.GetRight() or
                                 pc['box'][3] < bb.GetTop() or pc['box'][1] > bb.GetBottom())})
            area = f'R7_POUR_TRIM_{len(made) + 1}'
            new.append(base.rule_area(b, area, (lid,), pts, fill=True))
            made.append((area, '+'.join(kinds), b.GetLayerName(lid), box))
    return new


def pour_trim(b, log, name='pour_trim'):
    """P3-RF-01 and the whole-board thin-pour scan (tools/route_check pour_sliver / pour_finger, gated): after every
    copper change, each pour piece narrower than 0.25 mm and longer than 3 mm (a sliver between two tracks, such as the
    15.2 mm F.Cu GND sliver between RADIO_RXEN and RADIO_BUSY that RQ-10's 0.15 mm lanes opened, and the 5.9 mm one
    between SPI1_MISO and SPI1_MOSI), and each GND finger narrower than 0.5 mm (too narrow for a via) and longer than
    3 mm with a point more than 4 mm of copper from a GND via or plated GND hole, gets a zone-fill keep-out rule area
    on its layer: the piece's own outline grown by 0.02 mm (tracks and vias stay allowed), named R7_POUR_TRIM_<n>; the
    pours are refilled and scanned again until none is left. Nothing else of any fill changes (the pad groups with the
    pours joining are checked after the stage, as after every stage).
    P4-REGRESSION-02 (fix pass 4): the keep-outs leave out the ring (outline + route_check.PAD_RING, 0.75 mm) of every
    pad of the piece's net with a thermal or solid connection to that pour (its relief: gap and spokes, which
    route_check no longer counts as a finger), so every pad that touched its pour before the stage still touches it
    after (asserted; route_check pad_pour_cut gates the same on the saved board)."""
    made = []
    lib.fill(b)
    before = touching(b)
    rings = rc.pad_rings(b)
    for _ in range(8):
        lib.fill(b)
        pieces = rc.pour_pieces(b)
        if not pieces or not _trim_areas(b, pieces, rings, made):
            break
    lib.fill(b)
    left = rc.pour_pieces(b)
    assert not left, [(p['cat'], p['net'], [round(mm(v), 2) for v in p['box']]) for p in left]
    lost = sorted(k[0].split('#')[0] + ' ' + b.GetLayerName(k[1]) for k in before - touching(b))
    assert not lost, ('pour trim took the last pour contact of', lost)
    assert TRIM_EXPECTED[name] is None or len(made) == TRIM_EXPECTED[name], (name, len(made), made)
    log.append(f'{name}: {len(made)} keep-out rule areas; every pad touching its pour before still touches it')
    log.extend(f'  {m}' for m in made)


STRIP_Y = 23.5
STRIP_REACH = 4.0           # tools/check_r7.STRIP_GND_REACH


def gnd_far(b, window, region, reach):
    """The F.Cu / B.Cu GND copper points in `region` (mm box) farther than `reach` (through copper, searched over
    `window`) from a GND via or plated hole, worst first: [(distance or None, layer, x, y)] (route_check.gnd_reach)."""
    out = []
    for lid in (F, B):
        for d, x, y in rc.gnd_reach(b, lid, window, region, limit=reach + 40):
            if d is None or d > reach:
                out.append((d, lid, x, y))
    return sorted(out, key=lambda t: -(t[0] or 1e9))


def strip_far(b):
    """The F.Cu / B.Cu GND copper points in the RF strip farther than STRIP_REACH (through copper) from a GND via or
    plated hole, worst first: [(distance or None, layer, x, y)] (tools/route_check.gnd_reach; check_r7 gates it)."""
    return gnd_far(b, (0.0, -1.0, 46.0, STRIP_Y + 5.0), (0.0, -1.0, 46.0, STRIP_Y), STRIP_REACH)


def stitch_region(b, far_fn, reach, rounds=40):
    """Worst point first (far_fn(b), as strip_far): the through-copper distance from that point is computed over its
    layer's GND copper, and a GND via (0.5/0.3 mm) goes at the legal spot (ViaCheck, every clearance incl. the RF nets'
    0.25 mm; fix pass 5: the whole r7_hygiene.GndFit test, so also bare test pads 1.02 mm, Tag-Connect 0.528 mm,
    Pyro D and no via inside a 7.7 A servo-current corridor's pour, as for every other GND via) on that copper nearest
    it through copper, within `reach`; repeated until no point is left. A point with no legal spot within reach is left
    (and every point within 1 mm of it): ([(via, layer, point, before, via's copper distance)], [(layer, point,
    distance)] left)."""
    added, left = [], []
    for _ in range(rounds):
        lib.fill(b)
        far = [f for f in far_fn(b) if not any(f[1] == l and math.dist(f[2:], q) < 1.0 for l, q, _ in left)]
        if not far:
            break
        d0, lid, x, y = far[0]
        cop, stitch = rc.net_copper(b, 'GND', lid)
        r = rc.Raster((MM(x - 5), MM(y - 5), MM(x + 5), MM(y + 5)), MM(rc.RASTER))
        copper = r.fill(cop)
        src = bytearray(r.nx * r.ny)
        k0 = min((k for k in range(r.nx * r.ny) if copper[k]),
                 key=lambda k: math.dist((mm(r.centre(k)[0]), mm(r.centre(k)[1])), (x, y)))
        src[k0] = 1
        d = rc.reach(r, copper, src, reach)
        fit = hy.GndFit(b, (x - 7.0, y - 7.0, x + 7.0, y + 7.0))
        clr = hy.Clearance(b)
        best = None
        for j in range(-80, 81):
            for i in range(-80, 81):
                q = (round(x + 0.05 * i, 3), round(y + 0.05 * j, 3))
                ci = int((MM(q[0]) - r.x0) / r.step)
                cj = int((MM(q[1]) - r.y0) / r.step)
                ks = [(cj + dj) * r.nx + ci + di for dj in range(-4, 5) for di in range(-4, 5)
                      if 0 <= ci + di < r.nx and 0 <= cj + dj < r.ny and (di * di + dj * dj) * 0.0025 <= 0.0625]
                ds = [d[k] for k in ks if d[k] >= 0]
                if not ds or (best is not None and min(ds) >= best[0]):
                    continue
                if fit.ok(q, 0.5) and npth_ok(b, q, 0.5) and \
                        not any(clr.why('GND', l, P(*q), P(*q), MM(0.5)) for l in hy.CU4):
                    best = (min(ds), q)
        if not best:
            left.append((lid, (x, y), d0))
            continue
        add_via(b, 'GND', best[1], 0.5)
        added.append((best[1], b.GetLayerName(lid), (x, y), d0, best[0]))
    lib.fill(b)
    return added, left


def strip_stitch(b, log):
    """P3-RF-01's check (tools/check_r7.rf_gnd_reach): after the sliver fix the farthest strip GND copper was still 4.99
    mm of copper from a via on F.Cu ((12.13, 20.73), among U30's forward escapes) and 4.87 / 4.09 mm on B.Cu ((6.58,
    10.43) in the bias limiter's pocket under U30, (24.78, 8.18) west of U31). Worst point first: the through-copper
    distance from that point is computed over its layer's GND copper, and a GND via (0.5/0.3 mm, the strip's stitching
    size) goes at the legal spot (ViaCheck, every clearance incl. the RF nets' 0.25 mm) on that copper nearest it through
    copper, within 4.0 mm; repeated until no point is left (stitch_region)."""
    added, left = stitch_region(b, strip_far, STRIP_REACH, rounds=12)
    assert not left, ('no GND via spot within', STRIP_REACH, 'mm of copper of', left)
    assert not strip_far(b), strip_far(b)[:3]
    assert len(added) == STITCH_EXPECTED, added
    log.append(f'strip_stitch: {len(added)} GND vias (0.5 mm)')
    log.extend(f'  {q} for {lay} ({p[0]:.2f}, {p[1]:.2f}) ({d:.2f} mm before; the via sits {dv:.2f} mm of copper away)'
               for q, lay, p, d, dv in added)


EDGE_WINDOW, EDGE_REGION = (0.0, 104.0, 46.0, 118.5), (0.0, 112.0, 46.0, 118.0)
EDGE_EXPECTED = 12


def edge_far(b):
    return gnd_far(b, EDGE_WINDOW, EDGE_REGION, STRIP_REACH)


def edge_stitch(b, log):
    """P5-DOCS-01 (b), deviation D15 (P4-RF-01): the forward end of the board (y >= 112, beyond the two forward supports)
    carried F.Cu GND copper up to 47 mm of copper from a GND via (the 1.7 mm strip along the forward edge, x 0.5-32) and
    B.Cu GND up to 15 mm. The strip's own rule now holds there too: every F.Cu / B.Cu GND point of that region within
    4.0 mm of copper of a GND via (stitch_region, 0.5/0.3 mm vias, every spot ViaCheck- and clearance-checked), i.e. a
    stitch about every 8 mm along the edge."""
    added, left = stitch_region(b, edge_far, STRIP_REACH)
    assert len(added) == EDGE_EXPECTED, added
    log.append(f'edge_stitch: {len(added)} GND vias (0.5 mm)')
    log.extend(f'  {q} for {lay} ({p[0]:.2f}, {p[1]:.2f}) ({"> 44" if d is None else f"{d:.2f}"} mm before)'
               for q, lay, p, d, dv in added)
    far = edge_far(b)
    log.append(f'  left: {len(far)} raster points farther than {STRIP_REACH} mm (no legal spot within reach: '
               f'{[(b.GetLayerName(l), (round(q[0], 2), round(q[1], 2)), None if d is None else round(d, 2)) for l, q, d in left]}); '
               f'worst {[(b.GetLayerName(l), round(x, 2), round(y, 2), None if d is None else round(d, 2)) for d, l, x, y in far[:3]]}')


# GND pour pieces fix pass 4's reroutes left with one stitching via (pass-5 regression review P5-REGRESSION-02):
# (layer, the piece's via)
SINGLE_VIA = [('F', (44.75, 75.38)), ('B', (35.75, 50.35)), ('B', (31.0, 80.15)), ('F', (35.17, 57.92))]


def gnd_pieces(b, log):
    """P5-REGRESSION-02: four GND pour pieces were stitched by one via each after fix pass 4's PYRO1_CONT, NRST and
    CAM_UART_OE reroutes (F.Cu beside J2 between NRST's diagonal and PYRO1_CONT's run, B.Cu east of U1 cut by NRST's
    B.Cu run, B.Cu by U4 whose second via left with the old PYRO1_CONT route, F.Cu beside CAM_UART_OE's run). Each gets a
    second GND via (0.5/0.3 mm) at the legal spot (GndFit, every clearance) inside the piece farthest through its copper
    from the via it has; a piece with no legal spot is logged."""
    lib.fill(b)
    for lay, v in SINGLE_VIA:
        lid = LAYERS[lay]
        piece = None
        for z in b.Zones():
            if z.GetNetname() == 'GND' and not z.GetIsRuleArea() and z.IsOnLayer(lid):
                f = z.GetFilledPolysList(lid)
                for o in range(f.OutlineCount()):
                    one = pcbnew.SHAPE_POLY_SET()
                    one.AddOutline(f.Outline(o))
                    for h in range(f.HoleCount(o)):
                        one.AddHole(f.Hole(o, h))
                    if one.Collide(V(P(*v)), 0):
                        piece = one
        assert piece is not None, (lay, v)
        bb = piece.BBox()
        r = rc.Raster((bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()), MM(rc.RASTER))
        copper = r.fill([piece])
        src = bytearray(r.nx * r.ny)
        k0 = min((k for k in range(r.nx * r.ny) if copper[k]),
                 key=lambda k: math.dist((mm(r.centre(k)[0]), mm(r.centre(k)[1])), v))
        src[k0] = 1
        d = rc.reach(r, copper, src, 60.0)
        n_vias = sum(1 for t in vias_of(b, 'GND') if piece.Collide(t.GetPosition(), 0))
        assert n_vias == 1, (lay, v, n_vias)
        fit = hy.GndFit(b, (mm(bb.GetLeft()) - 3, mm(bb.GetTop()) - 3, mm(bb.GetRight()) + 3, mm(bb.GetBottom()) + 3))
        clr = hy.Clearance(b)
        best = None
        for k in sorted((k for k in range(r.nx * r.ny) if d[k] >= 0), key=lambda k: (-d[k], k)):
            q = (round(round(mm(r.centre(k)[0]) / 0.025) * 0.025, 3), round(round(mm(r.centre(k)[1]) / 0.025) * 0.025, 3))
            if not piece.Contains(V(P(*q))):
                continue
            if fit.ok(q, 0.5) and npth_ok(b, q, 0.5) and \
                    not any(clr.why('GND', l, P(*q), P(*q), MM(0.5)) for l in hy.CU4):
                best = (d[k], q)
                break
        if best is None:
            log.append(f'  {lay}.Cu piece of via {v}: no legal second via spot')
            continue
        add_via(b, 'GND', best[1], 0.5)
        log.append(f'  {lay}.Cu piece of via {v} ({piece.Area() / 1e12:.2f} mm2): second GND via at {best[1]}, '
                   f'{best[0]:.2f} mm of copper from the first')
        lib.fill(b)
    assert sum('second GND via' in x for x in log) == len(SINGLE_VIA), log


def pour_trim2(b, log):
    """pour_trim after the strip stitching (asserted to add nothing)."""
    pour_trim(b, log, 'pour_trim2')


STAGES = [('dead', dead), ('neck', neck), ('swd', swd), ('pyro_corners', pyro_corners), ('pyro1_cont', pyro1_cont),
          ('corners', corners), ('l1_node', l1_node), ('gnd_moves', gnd_moves), ('dead2', dead2),
          ('band', band), ('debris', debris), ('reroutes', reroutes), ('band5', band5), ('qspi5', qspi5),
          ('jogs5', jogs5), ('tidy5', tidy5), ('arm_gnd', arm_gnd), ('band_end', band_end), ('rf_relief', rf_relief),
          ('qspi6', qspi6), ('sw6', sw6), ('logic_ss6', logic_ss6), ('servo_fault6', servo_fault6), ('v3v3_6', v3v3_6),
          ('raw_act6', raw_act6), ('ties6', ties6), ('bat_in_f6', bat_in_f6),
          ('bumps7', bumps7), ('v3pair7', v3pair7), ('acten7', acten7), ('arm1_7', arm1_7), ('tidy7', tidy7),
          ('sense7', sense7), ('bat_via7', bat_via7), ('v3a_hop7', v3a_hop7), ('bat_in_b7', bat_in_b7), ('dup7', dup7),
          ('review7', review7), ('necks7', necks7),
          ('gnd_vias', gnd_vias),
          ('pour_trim', pour_trim), ('strip_stitch', strip_stitch), ('edge_stitch', edge_stitch),
          ('gnd_pieces', gnd_pieces), ('gnd_vias2', gnd_vias2), ('pour_trim2', pour_trim2)]


SPLIT_OK = {'raw_act6': ('RAW_ACT',), 'dup7': ('3V3',)}   # a stage that deletes a track duplicating a pour asserts its own split


def run(b, stop=None, verbose=True, start=None):
    """The stages in order; after each one the pours are refilled and the pad groups compared (r7_hygiene)."""
    pcbnew.KIID.SeedGenerator(7601)
    lib.fill(b)
    base = hy.pad_groups(b)
    log = []
    names = [n for n, _ in STAGES]
    for name, fn in STAGES[names.index(start) if start else 0:]:
        t0 = time.time()
        fn(b, log)
        lib.fill(b)
        now = hy.pad_groups(b)
        bad = [n for n in hy.same_groups(base, now) if n not in SPLIT_OK.get(name, ())]
        if bad:
            raise RuntimeError(f'stage {name} changed the pad groups of {bad}')
        base = now
        if verbose:
            print(f'[{name}] ({time.time() - t0:.0f} s)', *log, sep='\n  ', flush=True)
        log.clear()
        if stop == name:
            break


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--board', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--out', type=Path, help='save here instead of over --board')
    ap.add_argument('--stop', help='stop after this stage (debugging)')
    ap.add_argument('--start', help='start at this stage (development only: the build runs every stage)')
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()
    if not args.board.with_suffix('.kicad_dru').exists():
        raise SystemExit(f'{args.board.with_suffix(".kicad_dru")} missing: the fills need the board\'s own rules')
    b = pcbnew.LoadBoard(str(args.board))
    run(b, args.stop, not args.quiet, args.start)
    lib.fill(b)
    out = args.out or args.board
    pcbnew.SaveBoard(str(out), b, True)
    print('saved', out)


if __name__ == '__main__':
    main()
