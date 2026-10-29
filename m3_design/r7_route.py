#!/usr/bin/env python3
"""Route the R7 board after r7_pcb.py: local surgery at U1's left side, the RF strip, the interface, the fence.

usage: <KiCad python3> -I m3_design/r7_route.py [--board m3_design/assembly_review/m3.kicad_pcb] [--stop STAGE]

Stages run in order on the board in memory (each is deterministic); the board is saved where a stage needs KiCad's
DRC and once at the end. Decisions and their basis: sources/r7_review/stepB_progress.md.
  surgery    make room at U1's left side and in the freed aft area: QSPI_IO0 leaves pin 58 inward and runs on B.Cu
             (the IO1/IO3 pattern), VBUS_SENSE escapes inward, C84's GND trace becomes vias beside its pad, C80's
             BAT_IN via joins C96's, and R6 vias that sit where the new copper goes are removed or moved
  rf         both 50 ohm GCPW lines and their chain parts (W 0.30 mm on F.Cu; the GND pour keeps 0.25 mm)
  limiter    the GNSS antenna-feed limiter on B.Cu under U30's west half (explicit geometry)
  gnss       U30's own F.Cu: SAFEBOOT_N to TP30, the 3V3_GNSS bar and FB30 feed, UART/TIMEPULSE/RESET_N leads
  radio      U31's own copper: supply filter and feed, NRST, DIO1, the TXEN loop, RXEN, the NSS pull-up link
  interface  U1 pins 51-57 and 61/63-65 to the modules: escape vias beside U1, B.Cu corridor along the left edge,
             an F.Cu band forward of the strip, the SPI lane at x 20.6-23.2 (>= 5 mm from U30)
  stitch     the strip fence (y 23.3), GND vias along the RF lines, at the jack legs and module GND pins
  clean      R6 copper of 13 non-critical nets in the strip, in FB30's In2 lobe or in conflict with new copper goes
  redraw     their open connections are drawn again from explicit geometry (r7_redraw.py, which also removes the R6
             copper the removed port parts left behind)
  finish     checks that no R6 copper of those nets hangs; GND pour islands without a via get one
Every route is explicit geometry. (Until review pass 2 the displaced connections were drawn by the house grid router
and replayed from a recorded session file; fix2_F2_handoff.md records why that was retired.)
"""
import argparse
import math
from pathlib import Path
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
import r5_maze as maze  # noqa: E402
import r5_routes as rr  # noqa: E402
import r7_lib as lib  # noqa: E402
import r7_redraw  # noqa: E402

maze.BLOCK = (4.0, 84.0, 42.0, 114.4)          # the PYRO_BLOCK rule area after the +18 mm translation
MM, mm = pcbnew.FromMM, pcbnew.ToMM
F, B, IN1, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu
RF_W = 0.30
RF_NETS = ('GNSS_RF_ANT', 'GNSS_RF_IN', 'RADIO_RF_ANT', 'RADIO_RF')
SIG_W = 0.15                                    # interface tracks (house practice: R6 has 1551 tracks at 0.15 mm)
SIG_VIA = 0.5                                   # interface vias 0.5/0.3 (R6 has 129)
FENCE_Y = 23.3                                  # strip-boundary fence (pass1_layout 3.3: y ~ 23.5)
# Non-critical nets whose R6 copper the new layout may displace (the R6 port area, J123's new place, U1's left side).
# Only their copper that lies in the strip, in FB30's In2 3V3 lobe or in conflict with new copper is removed (clean).
REROUTE = ('BUZZ_DRV', 'BAT_FAULT_N', 'LOGIC_SOURCE_ST', 'BAT_SW_SOURCE', 'BAT_SW_RETURN', 'LED_RED', 'LED_YEL',
           'CAM_MCU_TX', 'CAM_MCU_RX', 'PULLPIN', 'PULLPIN_EXT', 'VLOGIC_SENSE', 'BAT_ILIM')


def r3(p):
    return round(mm(p.x), 3), round(mm(p.y), 3)


def ends(t):
    return [r3(t.GetPosition())] if t.GetClass() == 'PCB_VIA' else [r3(t.GetStart()), r3(t.GetEnd())]


def near(a, c, tol=0.006):
    return abs(a[0] - c[0]) <= tol and abs(a[1] - c[1]) <= tol


def find(b, net, *pts, cls=None, layer=None):
    """Tracks/vias of net whose end points match pts (any order; a via matches one point)."""
    out = []
    for t in b.GetTracks():
        if t.GetNetname() != net or (cls and t.GetClass() != cls) or (layer is not None and t.GetLayer() != layer
                                                                       and t.GetClass() != 'PCB_VIA'):
            continue
        e = ends(t)
        if len(e) == len(pts) and all(any(near(q, p) for q in e) for p in pts):
            out.append(t)
    return out


def delete(b, items, why, log):
    for t in items:
        b.Delete(t)
    log.append(f'{why}: {len(items)} item(s)')


def pad(b, ref, num):
    return rr.pad(b, ref, num)


def T(b, net, layer, pts, w=SIG_W):
    rr.route(b, net, layer, [tuple(round(v, 4) for v in p) for p in pts], w)


def V(b, net, p, d=SIG_VIA):
    rr.via(b, net, (round(p[0], 4), round(p[1], 4)), d=d)


# --- surgery -----------------------------------------------------------------------------------------------

def surgery(b, log):
    # BAT_ILIM: keep U9-R84; the TP89 branch (In2 under U9, via (10.49, 46.89), F.Cu under C84) is redrawn (reroute).
    tp89 = [t for t in b.GetTracks() if t.GetNetname() == 'BAT_ILIM' and
            (t.GetLayer() == IN2 and t.GetClass() == 'PCB_TRACK' or any(y > 43.0 for _, y in ends(t)))]
    delete(b, tp89, 'BAT_ILIM test-pad branch removed (redrawn by reroute)', log)
    # QSPI_IO0: drop the F.Cu run along U1's left pin tips (x 12.9, y 44.4-51.0 and the loop at x 11.15).
    io0 = []
    for t in b.GetTracks():
        if t.GetNetname() != 'QSPI_IO0' or t.GetClass() != 'PCB_TRACK':
            continue
        a, c = ends(t)
        if {a, c} == {(12.9, 42.5), (12.9, 48.4)}:
            t.SetEnd(rr.P(12.9, 44.4)) if near(c, (12.9, 48.4)) else t.SetStart(rr.P(12.9, 44.4))
        elif min(a[1], c[1]) > 44.39:
            io0.append(t)
    delete(b, io0, 'QSPI_IO0 F.Cu along the pin tips removed', log)
    rr.route(b, 'QSPI_IO0', F, [(14.3, 51.0), (15.4, 51.0), (15.55, 50.85)], 0.2)
    rr.via(b, 'QSPI_IO0', (15.55, 50.85))
    rr.route(b, 'QSPI_IO0', B, [(15.55, 50.85), (12.9, 50.85), (12.9, 44.4)], 0.2)
    rr.via(b, 'QSPI_IO0', (12.9, 44.4))
    log.append('QSPI_IO0: inward stub, via (15.55, 50.85), B.Cu y 50.85 / x 12.9, via (12.9, 44.4)')
    # VBUS_SENSE: inward escape and an In2 link into its existing In2 run at (13.61, 53.58).
    vb = find(b, 'VBUS_SENSE', (13.0, 52.97), cls='PCB_VIA') + \
        find(b, 'VBUS_SENSE', (13.0, 52.97), (13.03, 53.0)) + find(b, 'VBUS_SENSE', (13.03, 53.0), (14.3, 53.0)) + \
        find(b, 'VBUS_SENSE', (13.61, 53.58), (13.0, 52.97))
    assert len(vb) == 4, vb
    delete(b, vb, 'VBUS_SENSE west escape removed', log)
    rr.route(b, 'VBUS_SENSE', F, [(14.3, 53.0), (15.65, 53.0)], 0.15)
    rr.via(b, 'VBUS_SENSE', (15.65, 53.0))
    run = [t for t in b.GetTracks() if t.GetNetname() == 'VBUS_SENSE' and t.GetClass() == 'PCB_TRACK' and
           t.GetLayer() == IN2 and any(near(e, (13.61, 53.58)) for e in ends(t))]
    assert len(run) == 1, [ends(t) for t in run]
    e = min((run[0].GetStart(), run[0].GetEnd()), key=lambda q: math.dist(r3(q), (13.61, 53.58)))
    ex, ey = mm(e.x), mm(e.y)                     # its exact end (13.6118, 53.5831): join it end to end, 45 deg
    rr.route(b, 'VBUS_SENSE', IN2, [(15.65, 53.0), (15.65, 53.2), (ex + ey - 53.2, 53.2), (ex, ey)], 0.15)
    # C84's GND trace from its pad to the via (11, 53.55), the via, and its B.Cu tail to C80's pour.
    gnd = (find(b, 'GND', (7.5, 46.95), (11.0, 50.45)) + find(b, 'GND', (11.0, 50.45), (11.0, 53.55)) +
           find(b, 'GND', (11.0, 53.55), cls='PCB_VIA') + find(b, 'GND', (11.0, 53.55), (10.322, 53.55)) +
           find(b, 'GND', (10.322, 53.55), (9.45, 52.678)) + find(b, 'GND', (9.45, 52.678), (9.191, 52.678)) +
           find(b, 'GND', (12.7, 53.7), cls='PCB_VIA') +
           find(b, 'GND', (9.8, 48.6), (9.8, 49.13)) + find(b, 'GND', (9.8, 49.13), (10.22, 49.56)) +
           find(b, 'GND', (9.2, 50.58), (7.67, 52.1)))
    assert len(gnd) == 10, [ends(t) for t in gnd]
    delete(b, gnd, 'C84 GND trace, via (11, 53.55), GND via (12.7, 53.7) and GND stubs near C80 removed', log)
    for y in (45.0, 45.8, 46.6):                 # C84's GND pad (x 6.55-8.45) to In1 through vias east of it
        rr.route(b, 'GND', F, [(7.5, y), (9.0, y)], 0.5)
        rr.via(b, 'GND', (9.0, y))
    log.append('C84 GND: three vias at x 9.0 beside its pad (F.Cu 0.5 mm stubs)')
    # C80's BAT_IN via (9.43, 52.1) joins C96's via (9.3, 53.38).
    c80 = find(b, 'BAT_IN', (9.43, 52.1), cls='PCB_VIA') + find(b, 'BAT_IN', (10.62, 52.1), (9.43, 52.1))
    assert len(c80) == 2, c80
    delete(b, c80, "C80's BAT_IN via moved", log)
    rr.route(b, 'BAT_IN', B, [(10.62, 52.1), (10.62, 52.6), (9.84, 53.38), (9.3, 53.38)], 0.5)
    # Dead RAW_PROTECTED branch that fed R6's U16 (now removed): via (15.7, 25.8), In2 to via (9.35, 26.45), F stub.
    dead = (find(b, 'RAW_PROTECTED', (14.5, 27.0), (15.7, 25.8)) + find(b, 'RAW_PROTECTED', (15.7, 25.8), cls='PCB_VIA')
            + [t for t in b.GetTracks() if t.GetNetname() == 'RAW_PROTECTED' and t.GetLayer() == IN2
               and t.GetClass() == 'PCB_TRACK' and all(y < 27 for _, y in ends(t))]
            + find(b, 'RAW_PROTECTED', (9.35, 26.45), cls='PCB_VIA')
            + find(b, 'RAW_PROTECTED', (9.5, 26.2), (9.35, 26.35)) + find(b, 'RAW_PROTECTED', (9.35, 26.35), (9.35, 26.45)))
    assert len(dead) == 10, [ends(t) for t in dead]
    delete(b, dead, 'dead RAW_PROTECTED branch of the removed U16 deleted', log)
    # R6 GND stitching vias inside the strip (the fence and strip stitching replace them) and the ones forward of it
    # that sit on the new GNSS leads (9.875, 23.7), (6.85, 24.425) or the new RADIO_NRST/SCK columns (19.3, 25.4),
    # (22.5, 25.4). The R6 via at (14.8, 18.85) lies inside U30's pin 9 pad (it took that pad's net on import).
    stray = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND' and
             (r3(t.GetPosition())[1] < FENCE_Y + 0.2 or
              any(near(r3(t.GetPosition()), q) for q in ((9.875, 23.7), (6.85, 24.425), (19.3, 25.4), (22.5, 25.4))))]
    stray += find(b, 'GNSS_RESET_N', (14.8, 18.85), cls='PCB_VIA')
    delete(b, stray, 'R6 GND vias in the strip or on the new leads deleted', log)
    # ...and that via's 0.4 mm R6 lead (C172.2's GND stub), which took pin 9's net too: it overlapped U30.9 and the
    # RESET_N lead and reached U30's keep-out edge (pass 2 RQ-05)
    delete(b, find(b, 'GNSS_RESET_N', (14.8, 19.8), (14.8, 18.85), cls='PCB_TRACK'),
           'R6 0.4 mm stub left on U30.9 (GNSS_RESET_N) deleted', log)
    # GND via (5.975, 40.6) of R81/C87/R83 sits on the corridor (B.Cu x 1.2-6.2): moved onto their GND track at x 6.75.
    g = find(b, 'GND', (5.975, 40.6), cls='PCB_VIA') + find(b, 'GND', (6.775, 41.3), (6.075, 40.6)) + \
        find(b, 'GND', (6.075, 40.6), (5.975, 40.6))
    assert len(g) == 3, [ends(t) for t in g]
    delete(b, g, 'GND via (5.975, 40.6) on the corridor removed', log)
    rr.via(b, 'GND', (6.85, 40.5))
    # D9/C6 GND via (19.85, 28.246) and C97's (22.7, 28.8) sit in the new F.Cu band: C6 and C97 get vias beside them.
    g = (find(b, 'GND', (19.85, 28.246), cls='PCB_VIA') + find(b, 'GND', (19.85, 28.246), (18.0, 30.096)) +
         find(b, 'GND', (18.0, 30.096), (18.0, 31.2)) + find(b, 'GND', (19.85, 28.246), (20.057, 28.453)) +
         find(b, 'GND', (20.057, 28.453), (20.2, 28.453)) + find(b, 'GND', (20.2, 29.4), (20.2, 28.453)) +
         find(b, 'GND', (22.7, 28.8), cls='PCB_VIA') + find(b, 'GND', (24.15, 27.25), (22.75, 28.65)) +
         find(b, 'GND', (22.75, 28.65), (22.75, 28.85)) + find(b, 'GND', (22.75, 28.85), (22.7, 28.8)))
    assert len(g) == 10, [ends(t) for t in g]
    delete(b, g, 'GND vias (19.85, 28.246) and (22.7, 28.8) in the new F.Cu band removed', log)
    # (C6's GND pad keeps the B.Cu GND pour; the space north of the band is RXEN's way through)
    rr.route(b, 'GND', B, [(24.15, 27.25), (24.15, 28.25)], 0.25)
    rr.via(b, 'GND', (24.15, 28.25))
    # R6 GND leadouts of the removed port parts that stage 1 kept (their free ends lie in the F.Cu GND pour) where new
    # copper goes: the stubs of the vias deleted above at (6.85, 24.425) and (9.875, 23.7), and a chain at x 10.4-11.3,
    # y 28.5-31.3 under the new F.Cu band.
    left = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetLayer() == F and t.GetNetname() == 'GND'
            and (any(near(e, q) for e in ends(t) for q in ((6.85, 24.425), (9.875, 23.7))) or
                 all(10.3 <= x <= 11.4 and 28.4 <= y <= 31.4 for x, y in ends(t)))]
    assert len(left) == 7, [ends(t) for t in left]
    delete(b, left, 'R6 GND leadouts of removed parts under the new GNSS leads and F.Cu band deleted', log)
    # A dead-end In2 3V3 stub inside the 3V3 plane, (21.78, 29.8)-(17.58, 34.0), crosses RXEN's way north of the band.
    stub = find(b, '3V3', (21.78, 29.8), (17.58, 34.0), layer=IN2)
    assert len(stub) == 1
    delete(b, stub, 'dead-end In2 3V3 stub (21.78, 29.8)-(17.58, 34.0) inside the 3V3 plane deleted', log)
    # J123 at its new place: the R6 GND via (37.7, 34.7) is 0.25 mm from its pin 2 hole.
    delete(b, find(b, 'GND', (37.7, 34.7), cls='PCB_VIA'), 'GND via (37.7, 34.7) at J123 pin 2 removed', log)
    # R105.2 (B.Cu) reached the GND pour through R6 B.Cu stubs; the redrawn links that now pass it can cut that pour
    # patch off, so the stub end (32.2, 27.033) gets a GND via (0.5 mm: the room beside R160.2).
    assert len(find(b, 'GND', (32.2, 27.033), (32.2, 28.115), layer=B)) == 1
    rr.via(b, 'GND', (32.2, 27.033), d=0.5)
    log.append('GND via (32.2, 27.033) at the end of R105.2\'s GND stub')


# --- RF strip ----------------------------------------------------------------------------------------------

def rf(b, log):
    """Straight GCPW lines: jack centre pad -> ESD pad -> (bias tap) -> pi network row -> module RF pin."""
    gx, rx = lib.GNSS_X, lib.RADIO_X
    P = lambda ref, n: pad(b, ref, n)  # noqa: E731
    j30, d30, l30, r304a, r304b, c303, c305, u30 = (P('J30', '5'), P('D30', '1'), P('L30', '2'), P('R304', '1'),
                                                     P('R304', '2'), P('C303', '1'), P('C305', '1'), P('U30', '11'))
    assert j30[0] == d30[0] == l30[0] == r304a[0] == gx and r304b[0] == u30[0]
    rr.route(b, 'GNSS_RF_ANT', F, [j30, r304a], RF_W)
    rr.route(b, 'GNSS_RF_ANT', F, [c303, r304a], RF_W)
    rr.route(b, 'GNSS_RF_IN', F, [r304b, u30], RF_W)
    rr.route(b, 'GNSS_RF_IN', F, [r304b, c305], RF_W)
    # bias tap cold end: L30.1 - C302.1, then a via to the B.Cu limiter
    l30a, c302 = P('L30', '1'), P('C302', '1')
    rr.route(b, 'GNSS_ANT_DC', F, [c302, l30a], 0.25)
    rr.route(b, 'GNSS_ANT_DC', F, [(11.45, c302[1]), (11.45, 5.15)], 0.25)
    rr.via(b, 'GNSS_ANT_DC', (11.45, 5.15))
    j31, d31, r316a, r316b, c313, c314, u31 = (P('J31', '5'), P('D31', '1'), P('R316', '1'), P('R316', '2'),
                                               P('C313', '1'), P('C314', '1'), P('U31', '6'))
    assert j31[0] == d31[0] == r316a[0] == rx and r316b[0] == u31[0]
    rr.route(b, 'RADIO_RF_ANT', F, [j31, r316a], RF_W)
    rr.route(b, 'RADIO_RF_ANT', F, [c313, r316a], RF_W)
    rr.route(b, 'RADIO_RF', F, [r316b, u31], RF_W)
    rr.route(b, 'RADIO_RF', F, [r316b, c314], RF_W)
    lg = math.dist(j30, r304a) + math.dist(r304b, u30)
    lr = math.dist(j31, r316a) + math.dist(r316b, u31)
    log.append(f'RF lines W {RF_W} mm: GNSS {lg:.2f} mm (+0.86 mm inside R304), radio {lr:.2f} mm (+0.86 inside R316)')


# --- GNSS antenna-feed limiter (B.Cu) ----------------------------------------------------------------------

def limiter(b, log):
    """Pins 14 (VCC_RF) and 13 (LNA_EN) drop through vias just aft of U30's pad row (clear of its paste apertures);
    the bias tap's cold end arrives by the via the rf stage placed (ANT_DC). The B.Cu copper is the grid router's
    path for the placement in r7_lib.LIMITER (pass 2 search), written out pad centre to pad centre: R300 across x with
    Q32 under it, so the sense pair (R300.1 -> emitter, R300.2 -> base) runs straight and nothing loops round Q32
    (RQ-15/RG-13). Where R300's 1.65 mm pad pitch meets Q32's 1.9 mm pin pitch the two sense legs end 0.125 mm off
    the pin centres, inside the pins."""
    rr.route(b, 'GNSS_VCC_RF', F, [pad(b, 'U30', '14'), (10.41, 8.3)], 0.25)
    rr.via(b, 'GNSS_VCC_RF', (10.41, 8.3))
    rr.route(b, 'GNSS_LNA_EN', F, [pad(b, 'U30', '13'), (11.51, 8.3)], 0.2)
    rr.via(b, 'GNSS_LNA_EN', (11.51, 8.3))
    P = lambda r, n: pad(b, r, n)  # noqa: E731
    r300a, r300b = P('R300', '1'), P('R300', '2')            # VCC_RF (east), ANT_SRC (west)
    q32b, q32e, q32c = P('Q32', '1'), P('Q32', '2'), P('Q32', '3')
    q30g, q30s, q30d = P('Q30', '1'), P('Q30', '2'), P('Q30', '3')
    r301a, r301b, r302a, r302b = P('R301', '1'), P('R301', '2'), P('R302', '1'), P('R302', '2')
    q31g, q31d, r303a, c304a = P('Q31', '1'), P('Q31', '3'), P('R303', '1'), P('C304', '1')
    assert abs(r300a[1] - r300b[1]) < 1e-6 and abs(q32b[1] - q32e[1]) < 1e-6 and abs(q30g[1] - q30s[1]) < 1e-6
    gx = r302a[0]                                             # R302.1 and C304.1 share this column
    assert abs(c304a[0] - gx) < 0.011
    d = 10.41 - r300a[0]
    runs = {
        'GNSS_VCC_RF': ([(10.41, 8.3), (r300a[0], 8.3 + d), r300a],                       # via -> R300.1
                        [r300a, (r300a[0], q32e[1])]),                                    # -> Q32 emitter
        'GNSS_ANT_SRC': ([(r300b[0], q32b[1]), r300b],                                     # Q32 base -> R300.2
                         [r300b, (q30s[0] + 2.0 + 0.625, r300b[1]), (q30s[0] + 0.625, q30s[1]), q30s],  # -> Q30 source
                         [q30s, (r301a[0], q30s[1] + r301a[0] - q30s[0])]),               # -> R301.1
        'GNSS_ANT_GATE': ([q30g, (r301b[0], q30g[1] + r301b[0] - q30g[0]), r301b],         # Q30 gate -> R301.2
                          [r301b, (gx, r301b[1])], [(gx, r301b[1]), q32c],                 # -> Q32 collector
                          [(gx, r301b[1]), r302a],                                         # -> R302.1
                          [r302a, (gx, c304a[1])]),                                        # -> C304.1 (DNP)
        'GNSS_ANT_PD': ([r302b, (q31d[0] - (r302b[1] - q31d[1]), r302b[1]), q31d],),       # R302.2 -> Q31 drain
        'GNSS_LNA_EN': ([(11.51, 8.3), (11.51, r303a[1] - 0.58), (11.51 + 0.58, r303a[1]), r303a],  # via -> R303.1
                                                                                  # (its 45 deg leg clears R303.2)
                        [r303a, (q31g[0], r303a[1] + q31g[0] - r303a[0]), q31g]),           # -> Q31 gate
        'GNSS_ANT_DC': ([(11.45, 5.15), (q30d[0] + 1.1, 5.15 + 11.45 - q30d[0] - 1.1), q30d],),  # bias via -> Q30 drain
    }
    total = 0.0
    for net, polylines in runs.items():
        w = 0.25 if net in ('GNSS_VCC_RF',) else 0.2
        for pts in polylines:
            rr.route(b, net, B, pts, w)
            total += sum(math.dist(a, c) for a, c in zip(pts, pts[1:]))
    log.append(f'limiter B.Cu: {total:.1f} mm; vias VCC_RF (10.41, 8.3), LNA_EN (11.51, 8.3), ANT_DC (11.45, 5.15)')


# --- U30 local (F.Cu) --------------------------------------------------------------------------------------

def gnss(b, log):
    P = lambda r, n: pad(b, r, n)  # noqa: E731
    rr.route(b, 'GNSS_SAFEBOOT_N', F, [P('U30', '18'), (2.6, 10.2), P('TP30', '1')], 0.2)
    # 3V3_GNSS: pins 7/8 bar (just outside the module outline) -> C301 (100 nF) -> C300 (10 uF) -> FB30; FB30's 3V3
    # side drops into the In2 3V3 lobe (r7_lib.zones)
    # (the bar runs just beyond the pads' outer ends, y 20.75, so no segment lies wholly inside a pad, RG-14)
    rr.route(b, '3V3_GNSS', F, [P('U30', '7'), (12.61, 20.75)], 0.3)
    rr.route(b, '3V3_GNSS', F, [P('U30', '8'), (13.71, 20.75), (12.61, 20.75)], 0.3)
    rr.route(b, '3V3_GNSS', F, [(12.61, 20.75), (12.61, 21.75), P('C301', '1')], 0.3)
    rr.route(b, '3V3_GNSS', F, [P('C301', '1'), (12.0, 22.62), P('C300', '1')], 0.3)
    rr.route(b, '3V3_GNSS', F, [P('C300', '1'), P('FB30', '2')], 0.3)
    rr.route(b, '3V3', F, [P('FB30', '1'), (11.58, 26.2)], 0.3)
    rr.via(b, '3V3', (11.58, 26.2))
    # UART, TIMEPULSE (series resistors at the module, the driving end) and RESET_N to the interface vias
    T(b, 'GNSS_TXD', F, [P('U30', '2'), P('R305', '1')], 0.2)
    T(b, 'GNSS_TXD_MCU', F, [P('R305', '2'), (7.11, 24.65)], 0.2)
    V(b, 'GNSS_TXD_MCU', (7.11, 24.65))
    T(b, 'GNSS_RXD', F, [P('U30', '3'), (8.21, 25.2)], 0.2)
    V(b, 'GNSS_RXD', (8.21, 25.2))
    T(b, 'GNSS_TIMEPULSE', F, [P('U30', '4'), (9.31, 21.71), P('R307', '1')], 0.2)
    T(b, 'GNSS_TP_MCU', F, [P('R307', '2'), (9.0, 25.44), (9.31, 25.75)], 0.2)
    V(b, 'GNSS_TP_MCU', (9.31, 25.75))
    T(b, 'GNSS_RESET_N', F, [P('U30', '9'), (14.81, 23.59), (14.3, 24.1)], 0.2)
    V(b, 'GNSS_RESET_N', (14.3, 24.1))
    log.append('U30: SAFEBOOT_N -> TP30, 3V3_GNSS bar/C301/C300/FB30, 3V3 via (11.58, 26.2), UART/TP/RESET_N leads')


# --- U31 local -----------------------------------------------------------------------------------------------

def radio(b, log):
    P = lambda r, n: pad(b, r, n)  # noqa: E731
    # supply: pin 1 -> C311 (100 nF) -> C312 (10 nF) -> C310 (22 uF) <- FB31; FB31's 3V3 side takes R161.1's 3V3 pad on F.Cu
    # (C311/C312's pad 1 on C310.1's axis: pin 1 -> C311 -> C312 -> C310 runs straight, pad centre to pad centre; FB31
    # enters C310.1 on one 45 degree leg, RG-14)
    c310, fb31 = P('C310', '1'), P('FB31', '2')
    assert abs(P('C311', '1')[0] - c310[0]) < 1e-6 and abs(P('C312', '1')[0] - c310[0]) < 1e-6
    rr.route(b, '3V3_RADIO', F, [P('U31', '1'), P('C311', '1'), P('C312', '1'), c310], 0.4)
    rr.route(b, '3V3_RADIO', F, [fb31, (c310[0] - (fb31[1] - c310[1]), fb31[1]), c310], 0.4)
    rr.route(b, '3V3', F, [P('FB31', '1'), (35.1, 25.1), (35.1, 26.6)], 0.4)   # to R161.1's 3V3 pad and its via
    # NSS pull-up R310 (east of the NSS lead): a 3V3_RADIO link along the module's forward side, into R310.1 on 45
    r310 = P('R310', '1')
    rr.route(b, '3V3_RADIO', F, [fb31, (34.35, 21.6), (round(r310[0] + 21.6 - r310[1], 4), 21.6), r310], 0.4)
    # NRST: pin 3 -> R311 (pull-down) -> east of the supply filter -> forward to the interface via
    T(b, 'RADIO_NRST', F, [P('U31', '3'), P('R311', '1'), (39.6, 14.0), (40.0, 14.4), (40.0, 24.5)], 0.2)
    V(b, 'RADIO_NRST', (40.0, 24.5))
    # DIO1 arrives on B.Cu (interface) at a via just forward of pin 20
    V(b, 'RADIO_DIO1', (32.4, 20.15))
    T(b, 'RADIO_DIO1', F, [(32.4, 20.15), P('U31', '20')], 0.2)
    # TXEN: pins 19 (DIO2) and 9 (TXEN) joined round the module's west side on B.Cu (nothing may cross under U31,
    # the SPI leads hold F.Cu on the west and the RF line the aft-east side)
    T(b, 'RADIO_TXEN', F, [P('U31', '19'), (31.13, 20.15)], 0.2)
    V(b, 'RADIO_TXEN', (31.13, 20.15))
    T(b, 'RADIO_TXEN', B, [(31.13, 20.15), (24.8, 20.15), (24.5, 19.85), (24.5, 8.1), (24.8, 7.8), (28.59, 7.8)], 0.2)
    V(b, 'RADIO_TXEN', (28.59, 7.8))
    T(b, 'RADIO_TXEN', F, [(28.59, 7.8), P('U31', '9')], 0.2)
    # RXEN: pin 10's outer end, aft of the module along y 8.0 (clear of its body, RQ-12) with R312 (pull-down) tapped on
    # the way, then forward along x 20.6 under the SPI leads to the band
    u31_10, r312 = P('U31', '10'), P('R312', '1')
    T(b, 'RADIO_RXEN', F, [u31_10, (u31_10[0], 8.2), (u31_10[0] - 0.2, 8.0), (r312[0], 8.0)], 0.2)
    T(b, 'RADIO_RXEN', F, [(r312[0], 8.0), r312], 0.2)
    T(b, 'RADIO_RXEN', F, [(r312[0], 8.0), (20.9, 8.0), (20.6, 8.3), (20.6, 25.4)], 0.2)
    log.append('U31: supply filter, 3V3 from R161.1 (F.Cu 0.4 mm), 3V3_RADIO link to R310, NRST via (40.0, 24.5), DIO1 via, '
               'TXEN B.Cu loop (x 24.5), RXEN to (20.6, 25.4)')


# --- interface: U1 -> modules --------------------------------------------------------------------------------
# (line, U1 pin, net at U1, escape via, B.Cu row y, corridor column x, bottom row y, bottom via x, band y, lane x)
# MISO and MOSI swap rows at the escape vias so that the lane order at U31 (west to east BUSY, MISO, MOSI, SCK, NSS)
# needs no further crossing except NSS's one B.Cu hop under SCK; NSS stays the outermost lead, open to R310.
RADIO_IF = [
    ('NSS', '51', 'RADIO_NSS', (9.3, 47.5), 47.5, 6.2, 30.2, 9.4, 29.6, 23.2),
    ('SCK', '52', 'RADIO_SCK_MCU', (10.0, 48.0), 48.0, 5.7, 29.7, 10.0, 29.2, 22.4),
    ('MOSI', '54', 'RADIO_MOSI_MCU', (9.4, 48.5), 48.5, 5.2, 29.2, 9.4, 28.8, 22.0),
    ('MISO', '53', 'RADIO_MISO_MCU', (10.7, 48.5), 49.0, 4.7, 28.7, 10.0, 28.4, 21.6),
    ('BUSY', '55', 'RADIO_BUSY', (10.0, 49.5), 49.5, 4.2, 28.2, 9.4, 28.0, 21.2),
    ('NRST', '56', 'RADIO_NRST', (9.3, 50.0), 50.0, 3.7, 27.7, 10.0, 27.6, 19.0),
    ('DIO1', '57', 'RADIO_DIO1', (10.0, 50.5), 50.5, 3.2, 27.2, 9.4, 27.2, 18.4),
]
LANE_CHAMFER = {'DIO1': 0.3, 'NRST': 0.5, 'BUSY': 0.3, 'MISO': 0.534, 'MOSI': 0.768, 'SCK': 1.002, 'NSS': 1.2}
# series resistors inline on the corridor columns (B.Cu): (ref, net above, net below)
INLINE = {'SCK': ('R313', 'RADIO_SCK_MCU', 'RADIO_SCK'), 'MOSI': ('R315', 'RADIO_MOSI_MCU', 'RADIO_MOSI')}
# GNSS: (line, U1 pin, net at U1, jog start, row y, via x, bottom row y, bottom chamfer, end via)
GNSS_IF = [
    ('TP', '61', 'GNSS_TP_MCU', (12.4, 52.5), 51.0, 2.7, 25.75, 0.3, (9.31, 25.75)),
    ('RXD', '63', 'GNSS_RXD_MCU', (11.5, 53.5), 51.5, 2.2, 25.2, 0.6, (8.21, 25.2)),
    ('TXD', '64', 'GNSS_TXD_MCU', (11.3, 54.0), 52.0, 1.7, 24.65, 0.9, (7.11, 24.65)),
    ('RESET', '65', 'GNSS_RESET_N', (11.2, 54.5), 52.5, 1.2, 24.1, 1.2, (14.3, 24.1)),
]


def interface(b, log):
    P = lambda r, n: pad(b, r, n)  # noqa: E731
    for k, (name, pin, net, via, row, col, bot, bvx, band, lane) in enumerate(RADIO_IF):
        u1 = P('U1', pin)
        c = round(0.3 + 0.293 * k, 3)                  # nested 45 deg corners keep the 0.5 mm pitch on the diagonals
        # F.Cu from the pin to the escape via (MOSI jogs aft into the row MISO left; MISO jogs forward on B.Cu)
        if name == 'MOSI':
            T(b, net, F, [u1, (via[0] + 0.5, u1[1]), via])
        else:
            T(b, net, F, [u1, via])
        V(b, net, via)
        start = [via, (via[0] - 0.5, row)] if name == 'MISO' else [via]
        # B.Cu: row west, corner, column down to the corridor bottom, corner, row east to the bottom via
        path = start + [(col + c, row), (col, row - c), (col, bot + c), (col + c, bot), (bvx, bot)]
        if name in INLINE:
            ref, up, down = INLINE[name]
            p1, p2 = P(ref, '1'), P(ref, '2')
            assert abs(p1[0] - col) < 1e-6 and abs(p2[0] - col) < 1e-6 and p1[1] > p2[1]
            T(b, up, B, start + [(col + c, row), (col, row - c), p1])
            T(b, down, B, [p2, (col, bot + c), (col + c, bot), (bvx, bot)])
            net = down
        else:
            T(b, net, B, path)
        V(b, net, (bvx, bot))
        # F.Cu: from the bottom via east, jog to the 0.4 mm band pitch, east to the lane, corner, down
        x0 = 10.6
        cl = LANE_CHAMFER[name]
        f = [(bvx, bot), (x0, bot), (x0 + (bot - band), band), (lane - cl, band), (lane, band - cl)]
        if name == 'DIO1':
            T(b, net, F, f + [(lane, 24.0)])
            V(b, net, (lane, 24.0))
            T(b, net, B, [(lane, 24.0), (32.1, 24.0), (32.4, 23.7), (32.4, 20.15)])
        elif name == 'NRST':
            T(b, net, F, f + [(lane, 24.5)])
            V(b, net, (lane, 24.5))
            T(b, net, B, [(lane, 24.5), (40.0, 24.5)])
        elif name == 'BUSY':
            T(b, net, F, f + [(lane, 11.76), (lane + 0.3, 11.46), P('U31', '11')])
        elif name == 'MISO':
            T(b, net, F, f + [(lane, 13.03), (lane + 0.3, 12.73), P('R314', '2')])
            T(b, 'RADIO_MISO', F, [P('R314', '1'), P('U31', '12')])
        elif name == 'MOSI':
            T(b, net, F, f + [(lane, 14.3), (lane + 0.3, 14.0), P('U31', '13')])
        elif name == 'SCK':
            T(b, net, F, f + [(lane, 16.84), (lane + 0.3, 16.54), P('U31', '15')])
        elif name == 'NSS':
            T(b, net, F, f + [(lane, 17.3)])
            V(b, net, (lane, 17.3))
            T(b, net, B, [(lane, 17.3), (lane, 15.67), (lane + 0.4, 15.27)])
            V(b, net, (lane + 0.4, 15.27))
            T(b, net, F, [(lane + 0.4, 15.27), P('U31', '14')])
            T(b, net, F, [(lane, P('R310', '2')[1]), P('R310', '2')])
    # GNSS: F.Cu rows west under C84's body to vias at the board edge, B.Cu columns aft, rows east to U30's leads
    for name, pin, net, jog, row, vx, bot, c, end in GNSS_IF:
        u1 = P('U1', pin)
        T(b, net, F, [u1, jog, (jog[0] - (jog[1] - row), row), (vx, row)])
        V(b, net, (vx, row))
        if name == 'RXD':                               # R306 (series, MCU end) inline on the column
            p1, p2 = P('R306', '1'), P('R306', '2')
            T(b, net, B, [(vx, row), p1])
            net = 'GNSS_RXD'
            T(b, net, B, [p2, (vx, bot + c), (vx + c, bot), end])
        else:
            T(b, net, B, [(vx, row), (vx, bot + c), (vx + c, bot), end])
    log.append('radio: escape vias x 9.3-10.7 (MISO/MOSI swapped), corridor columns x 3.2-6.2, band y 27.2-29.6, '
               'lanes x 18.4 (DIO1), 19.0 (NRST), 21.2-22.4 (SPI), 23.2 (NSS, B.Cu hop under SCK)')
    log.append('GNSS: F.Cu rows y 51.0-52.5 under C84, columns x 1.2-2.7, rows y 24.1-25.75 to U30')


# --- U1 pins 45-47: RXEN beside the camera UART fan-outs ------------------------------------------------------

def u1fan(b, log):
    """RXEN (U1.45, PE15) leaves its pad on F.Cu straight aft and east under the no-connect pins 44-41 to a via; the
    camera UART fan-outs of pins 46/47 (R6, diagonal under pin 45) turn 0.4 mm sooner to make room. The grid router
    (reroute) takes RXEN on from that via to its strip lead."""
    old = (find(b, 'CAM_MCU_TX', (17.85, 45.95), (17.85, 45.15)) + find(b, 'CAM_MCU_TX', (17.85, 45.15), (18.75, 44.25)) +
           find(b, 'CAM_MCU_TX', (18.75, 44.25), (20.75, 44.25)) + find(b, 'CAM_MCU_RX', (17.35, 45.95), (17.35, 45.15)) +
           find(b, 'CAM_MCU_RX', (17.35, 45.15), (19.95, 42.55)) + find(b, 'CAM_MCU_RX', (19.95, 42.55), (21.15, 42.55)))
    assert len(old) == 6, [ends(t) for t in old]
    delete(b, old, 'R6 camera UART fan-outs of U1.46/47 replaced', log)
    T(b, 'CAM_MCU_TX', F, [pad(b, 'U1', '46'), (17.85, 44.75), (18.35, 44.25), (20.55, 44.25)])
    T(b, 'CAM_MCU_RX', F, [pad(b, 'U1', '47'), (17.35, 44.75), (19.55, 42.55), (21.15, 42.55)])
    # RXEN from U1.45 to its strip lead (20.6, 25.4): under U1's no-connect pins 44-41, down past QSPI's U3 on B.Cu
    # and under U3's body on F.Cu (x 23.5), over RAW_PROTECTED and under the F.Cu band on B.Cu (x 21.2)
    T(b, 'RADIO_RXEN', F, [pad(b, 'U1', '45'), (18.35, 44.75), (20.9, 44.75), (21.2, 44.45)])
    V(b, 'RADIO_RXEN', (21.2, 44.45))
    T(b, 'RADIO_RXEN', B, [(21.2, 44.45), (21.2, 43.65), (23.8, 41.05), (23.8, 39.45)])
    V(b, 'RADIO_RXEN', (23.8, 39.45))                     # (QSPI_CLK runs on F.Cu at x 23.15)
    T(b, 'RADIO_RXEN', F, [(23.8, 39.45), (23.5, 39.15), (23.5, 32.75), (21.2, 30.45)])
    V(b, 'RADIO_RXEN', (21.2, 30.45))
    T(b, 'RADIO_RXEN', B, [(21.2, 30.45), (21.2, 27.65), (20.6, 27.05)])
    V(b, 'RADIO_RXEN', (20.6, 27.05))
    T(b, 'RADIO_RXEN', F, [(20.6, 27.05), (20.6, 25.4)])
    log.append('U1.45 RXEN: F.Cu under pins 44-41, vias (21.2, 44.45), (23.8, 39.45), (21.2, 30.45), (20.6, 27.05) to '
               'its strip lead; U1.46/47 fan-outs turn at y 44.75')


# --- GND stitching ----------------------------------------------------------------------------------------

class ViaCheck:
    """Whether a new GND through via fits: the board rules against every other net's copper on every layer (0.15 mm,
    0.25 mm to the RF nets, 0.30 mm to the SMA centre pads), hole to hole 0.25 mm, 0.5 mm to the board edge and the
    support holes, no via in or within 0.15 mm of a GND solder pad, none in a via keep-out or an In1 launch cut-out.
    Each check adds 0.02 mm to the rule."""
    CU4 = (F, IN1, IN2, B)

    def __init__(self, b, net='GND'):
        self.b, self.net = b, net
        self.objs = [t for t in b.GetTracks()] + [q for f in b.GetFootprints() for q in f.Pads()]
        self.holes = []
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_VIA':
                self.holes.append((mm(t.GetPosition().x), mm(t.GetPosition().y), mm(t.GetDrillValue()) / 2))
        for f in b.GetFootprints():
            for q in f.Pads():
                if q.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                    self.holes.append((mm(q.GetPosition().x), mm(q.GetPosition().y),
                                       mm(max(q.GetDrillSize().x, q.GetDrillSize().y)) / 2))
        self.circles = [(mm(d.GetCenter().x), mm(d.GetCenter().y), mm(d.GetRadius())) for d in b.GetDrawings()
                        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
        self.keep = [z.Outline() for z in maze.zones(b) if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
        self.launch = [(x - 1.2, -1.0, x + 1.2, 4.9) for x in lib.IN1_LAUNCH.values()]

    def ok(self, p, d=0.6):
        x, y = p
        r = d / 2
        if x - r < 0.52 or x + r > 46.0 - 0.52 or y - r < 0.52 or y + r > 118.0 - 0.52:
            return False
        if any(math.hypot(x - cx, y - cy) < cr + 0.52 + r for cx, cy, cr in self.circles):
            return False
        if any(math.hypot(x - hx, y - hy) < hr + 0.15 + 0.27 for hx, hy, hr in self.holes):
            return False
        if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in self.launch):
            return False
        c = pcbnew.SHAPE_CIRCLE(rr.P(x, y), MM(r))
        for o in self.objs:
            bb = o.GetBoundingBox()
            if mm(bb.GetLeft()) > x + 1.0 or mm(bb.GetRight()) < x - 1.0 or mm(bb.GetTop()) > y + 1.0 or \
                    mm(bb.GetBottom()) < y - 1.0:
                continue
            n = o.GetNetname()
            if o.GetClass() == 'PAD':
                if o.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                # paste apertures (U30's T-shaped extensions are paste-only pads): no via under a stencil opening, so
                # the print never lands on a plugged via (pass 2 DFM-07)
                if any(o.IsOnLayer(lay) and o.GetEffectiveShape(lay).Collide(c, MM(0.1))
                       for lay in (pcbnew.F_Paste, pcbnew.B_Paste)):
                    return False
                layers = [lay for lay in self.CU4 if o.IsOnLayer(lay)]
                if n == self.net:
                    if any(o.GetEffectiveShape(lay).Collide(c, MM(0.15)) for lay in layers):
                        return False                  # no via in or touching its own solder pad
                    continue
                clr = 0.32 if o.GetParentFootprint().GetReference() in ('J30', 'J31') else 0.17
                clr = max(clr, mm(o.GetLocalClearance() or 0) + 0.02)
            else:
                if n == self.net:
                    continue
                layers = list(self.CU4) if o.GetClass() == 'PCB_VIA' else [o.GetLayer()]
                clr = 0.17
            if n in RF_NETS:
                clr = max(clr, 0.27)
            if any(o.GetEffectiveShape(lay).Collide(c, MM(clr)) for lay in layers):
                return False
        q = rr.P(x, y)
        return not any(o.Contains(q) or o.SquaredDistance(q) < MM(r) ** 2 for o in self.keep)

    def add(self, p, d=0.6):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(rr.P(round(p[0], 4), round(p[1], 4)))
        v.SetWidth(MM(d))
        v.SetDrill(MM(0.3))
        v.SetNet(self.b.FindNet(self.net))
        self.b.Add(v)
        self.objs.append(v)
        self.holes.append((p[0], p[1], 0.15))
        return v.m_Uuid.AsString()


def _nearest_spot(chk, target, r, d=0.6):
    """The ViaCheck spot (0.05 mm grid) nearest `target` within r: target is a point, or a pad (distance to its edge).
    Returns (spot, distance) or None."""
    if isinstance(target, tuple):
        cx, cy = target
        dist = lambda q: math.dist(q, target)  # noqa: E731
    else:
        cx, cy = mm(target.GetPosition().x), mm(target.GetPosition().y)
        lay = F if target.IsOnLayer(F) else B
        shape = target.GetEffectiveShape(lay)

        def dist(q):
            ring = pcbnew.SHAPE_CIRCLE(rr.P(*q), MM(d / 2))
            k = 0
            while not shape.Collide(ring, MM(0.01 * k)) and k < 300:
                k += 1
            return 0.01 * k
    best = None
    n = int(r / 0.05)
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            q = (round(cx + 0.05 * i, 3), round(cy + 0.05 * j, 3))
            if math.hypot(q[0] - cx, q[1] - cy) > r or not chk.ok(q, d):
                continue
            dq = dist(q)
            if best is None or dq < best[1] - 1e-9:
                best = (q, dq)
    return best


def _gnd_vias(b):
    return [(mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in b.GetTracks()
            if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']


def _greedy(chk, cands, lo, hi):
    """Place vias along an ordered candidate list (position along the line, point): each next via the farthest valid
    one within [last+lo, last+hi], else the first valid one beyond (an opening). Returns the positions used."""
    used, last = [], None
    i = 0
    while i < len(cands):
        if last is None:
            nxt = next((c for c in cands if chk.ok(c[1])), None)
        else:
            window = [c for c in cands if last + lo - 1e-9 <= c[0] <= last + hi + 1e-9 and chk.ok(c[1])]
            nxt = window[-1] if window else next((c for c in cands if c[0] > last + hi and chk.ok(c[1])), None)
        if nxt is None:
            break
        chk.add(nxt[1])
        used.append(nxt[0])
        last = nxt[0]
        i = cands.index(nxt) + 1
    return used


def _gaps(used, a, b_):
    pts = [a] + used + [b_]
    return max(q - p for p, q in zip(pts, pts[1:])) if used else b_ - a


# The TP30 SAFEBOOT legend (r7_post.py) runs up the left edge beside TP30, F.Cu side, where the strip lattice
# would otherwise leave no 1 mm x 12 mm spot: its window gets no lattice vias.
TP30_LEGEND = (0.85, 10.75, 2.05, 22.65)


def inside(q, r, margin=0.0):
    return r[0] - margin <= q[0] <= r[2] + margin and r[1] - margin <= q[1] <= r[3] + margin


def stitch(b, log):
    P = lambda r, n: pad(b, r, n)  # noqa: E731
    # vias beside every module GND castellation (pass1_layout 5.4), clear of U30's paste apertures (y 8.70 / 21.2)
    for ref, num, q, w in (('U30', '1', (6.01, 21.7), 0.3), ('U30', '10', (14.81, 8.3), 0.3),
                           ('U30', '12', (12.61, 8.3), 0.3), ('U31', '2', (33.6, 15.27), 0.3),
                           ('U31', '7', (31.13, 10.4), 0.3), ('U31', '16', (27.32, 17.6), 0.3)):
        rr.route(b, 'GND', F, [P(ref, num), q], w)
        rr.via(b, 'GND', q)
    # the decoupling capacitors' GND pads beside the modules' supply pins
    for q in ((38.78, 20.85),):
        rr.route(b, 'GND', F, [P('C310', '2'), q], 0.4)
        rr.via(b, 'GND', q)
    chk = ViaCheck(b)
    # pass 2 RF-02: a GND via beside each RF ground pad (ESD diodes, bias-tee capacitor, pi-network shunt lands; their
    # pads connect solidly, r7_pcb), the spot nearest the pad edge within 1.2 mm
    rf_gnd = []
    for ref in lib.RF_SOLID_GND:
        q = next(p for p in b.FindFootprintByReference(ref).Pads() if p.GetNetname() == 'GND')
        spot = _nearest_spot(chk, q, 1.2)
        if spot:
            chk.add(spot[0])
            rf_gnd.append(f'{ref}.{q.GetNumber()} {spot[0]} edge {spot[1]:.2f} mm')
        else:
            rf_gnd.append(f'{ref}.{q.GetNumber()} none')
    # pass 2 RG-05: a GND via beside the radio layer changes in the strip (NSS's hop, TXEN's loop, DIO1's lead)
    ret = []
    for net, q in (('RADIO_NSS', (23.2, 17.3)), ('RADIO_NSS', (23.6, 15.27)), ('RADIO_TXEN', (31.13, 20.15)),
                   ('RADIO_TXEN', (28.59, 7.8)), ('RADIO_DIO1', (32.4, 20.15))):
        assert find(b, net, q, cls='PCB_VIA'), (net, q)
        spot = _nearest_spot(chk, q, 1.0)
        if spot:
            chk.add(spot[0])
        ret.append(f'{net} {q}: ' + (f'{spot[0]} at {spot[1]:.2f} mm' if spot else 'none'))
    log.append('RF ground pad vias: ' + '; '.join(rf_gnd))
    log.append('strip layer-change GND vias: ' + '; '.join(ret))
    # jack legs: three vias beside each leg pad pair (F.Cu and B.Cu legs), outside the pads
    jack = 0
    for ref in ('J30', 'J31'):
        legs = sorted({round(mm(q.GetPosition().x), 3) for q in b.FindFootprintByReference(ref).Pads()
                       if q.GetNetname() == 'GND'})
        for lx in legs:
            for dx in (-1.1, 1.1):
                for y in (1.0, 2.3, 3.6):
                    q = (round(lx + dx, 3), y)
                    if chk.ok(q):
                        chk.add(q)
                        jack += 1
    # RF lines: GND vias 0.85 mm from the line centre on both sides, <= 1.5 mm pitch where the chain parts allow
    rf_report = []
    segs = [('GNSS_RF_ANT', lib.GNSS_X, 4.4, 7.13), ('GNSS_RF_IN', P('U30', '11')[0], 7.13, 9.3),
            ('RADIO_RF_ANT', lib.RADIO_X, 4.4, 7.6), ('RADIO_RF', P('U31', '6')[0], 7.6, 8.3)]
    for net, x, y0, y1 in segs:
        for sign in (-1, 1):
            cands = []
            for k in range(int(round((y1 - y0 + 2.0) / 0.05)) + 1):
                y = round(y0 - 1.0 + 0.05 * k, 2)
                for off in (1.25, 1.15, 1.05, 0.95, 0.85):          # nearest offset last: the window keeps it
                    cands.append((y, (round(x + sign * off, 3), y)))
            used = _greedy(chk, cands, 0.9, 1.5)
            rf_report.append(f'{net} {"west" if sign < 0 else "east"}: {len(used)} via(s) at y '
                             f'{", ".join(f"{u:.2f}" for u in used)}')
    # strip fence along y = FENCE_Y, 2 mm pitch, open where the interface and supply leads cross
    fx = [(round(0.8 + 0.1 * k, 1), (round(0.8 + 0.1 * k, 1), FENCE_Y)) for k in range(445)]
    used = _greedy(chk, fx, 1.2, 2.0)
    pts = [0.0] + used + [46.0]
    openings = [(round(p, 1), round(q, 1)) for p, q in zip(pts, pts[1:]) if q - p > 2.05]
    # strip stitching: a 2 mm lattice over the strip, every via >= 1.6 mm from the GND vias already there
    have = _gnd_vias(b)
    lattice = 0
    for j in range(12):
        for i in range(23):
            q = (round(1.0 + 2.0 * i + (1.0 if j % 2 else 0.0), 2), round(1.0 + 2.0 * j, 2))
            if q[1] > FENCE_Y - 0.9 or q[0] > 45.2:
                continue
            if any(math.hypot(q[0] - hx, q[1] - hy) < 1.6 for hx, hy in have):
                continue
            if inside(q, TP30_LEGEND, 0.45):     # via ring + silkscreen gap: keep the legend's window clear
                continue
            if chk.ok(q):
                chk.add(q)
                have.append(q)
                lattice += 1
    log.append(f'module GND pins: 6 vias; jack legs: {jack} vias; fence y {FENCE_Y}: {len(used)} vias, '
               f'openings (x) {openings}; strip lattice: {lattice} vias')
    log.extend(rf_report)


# --- the displaced non-critical connections ----------------------------------------------------------------

STATE = {}          # the R6 copper of the REROUTE nets, by uuid (KiCad may re-net a stub that touches new copper)


def _r6_items(b):
    return [t for t in b.GetTracks() if t.m_Uuid.AsString() in STATE['r6']]


def clean(b, log, board_path):
    """R6 copper of the REROUTE nets that lies in the strip, in FB30's In2 3V3 lobe, or that DRC finds in conflict with
    the new copper, and what that leaves hanging, is removed (the redraw stage draws the connections again)."""
    pcbnew.SaveBoard(str(board_path), b, True)
    report = lib.drc(board_path)
    bad = set()
    kinds = ('clearance', 'shorting_items', 'tracks_crossing', 'hole_clearance', 'hole_to_hole', 'solder_mask_bridge',
             'copper_edge_clearance', 'items_not_allowed', 'via_dangling', 'track_dangling')
    for v in report['violations']:
        if v['type'] in kinds:
            bad |= {it['uuid'] for it in v['items']}
    def in_band(t):                     # the In2 3V3 lobe forward of the strip (x 9.9-14, y 23.9-27.0)
        return t.GetLayer() == IN2 and t.GetClass() == 'PCB_TRACK' and \
            any(9.5 <= x <= 14.4 and y < 27.3 for x, y in ends(t))
    gone = [t for t in _r6_items(b) if t.m_Uuid.AsString() in bad or any(y < FENCE_Y + 0.4 for _, y in ends(t)) or
            in_band(t)]
    for t in gone:
        b.Delete(t)
    n = 0
    for _ in range(8):           # DRC lists only some of the items where two nets overlap: look again until none
        lib.fill(b)
        pcbnew.SaveBoard(str(board_path), b, True)
        report = lib.drc(board_path)
        bad = {it['uuid'] for v in report['violations'] if v['type'] in kinds for it in v['items']}
        # a piece left touching only new copper takes that copper's net on the refill (KiCad's net propagation) and
        # then never shows in a DRC conflict (pass 2: an R6 LED_RED piece became RADIO_DIO1 under DIO1's B.Cu run):
        # an R6 piece of a displaced net that is now on another net goes too
        more = [t for t in _r6_items(b) if t.m_Uuid.AsString() in bad or t.GetNetname() not in REROUTE]
        if not more:
            break
        for t in more:
            b.Delete(t)
        gone += more
    log.append(f'R6 copper of the displaced nets removed: {len(gone)} in conflict, in the strip or in the In2 3V3 lobe '
               '(the redraw stage removes or joins what is left)')


def _drc_prune_r6(b, board_path):
    """R6 copper of the displaced nets that KiCad's DRC still calls dangling (by uuid), until none: a via is
    deleted, a track is shortened to the last joint on its body (a new route may end on it mid-segment) or deleted
    (r7_lib._trim_or_delete)."""
    n = 0
    for _ in range(16):
        lib.fill(b)
        pcbnew.SaveBoard(str(board_path), b, True)
        report = lib.drc(board_path)
        dead = {it['uuid'] for v in report['violations'] if v['type'] in ('track_dangling', 'via_dangling')
                for it in v['items']}
        items = [t for t in b.GetTracks() if t.m_Uuid.AsString() in dead and t.m_Uuid.AsString() in STATE['r6']]
        if not items:
            return n
        b.BuildConnectivity()
        for t in items:
            if t.GetClass() == 'PCB_TRACK':
                net, uid = t.GetNetname(), t.m_Uuid.AsString()
                joints = [o.GetPosition() for o in b.GetTracks() if o.GetNetname() == net and
                          o.GetClass() == 'PCB_VIA']
                joints += [q for o in b.GetTracks() if o.GetNetname() == net and o.GetClass() == 'PCB_TRACK' and
                           o.GetLayer() == t.GetLayer() and o.m_Uuid.AsString() != uid for q in (o.GetStart(), o.GetEnd())]
                joints += [p.GetPosition() for f in b.GetFootprints() for p in f.Pads()
                           if p.GetNetname() == net and p.IsOnLayer(t.GetLayer())]
                if lib._trim_or_delete(b, t, joints) == 'trim':
                    n += 1
                    continue
            b.Delete(t)
            n += 1
    return n


def _island_vias(b, log=None, fill=True):
    """Every GND pour island (F.Cu, B.Cu, the In2 strip) without a via or through-hole GND pin gets a GND via
    (ViaCheck rules, 0.6 mm, else 0.5 mm) where one fits. Returns the added vias' uuids and spots."""
    added, spots = [], []
    for zname, lay in (('GND_F', F), ('GND_B', B), ('R7_GND_In2_strip', IN2)):
        if fill:
            lib.fill(b)
        z = next(z for z in b.Zones() if z.GetZoneName() == zname)
        polys = z.GetFilledPolysList(lay)
        anchors = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
        anchors += [q.GetPosition() for f in b.GetFootprints() for q in f.Pads()
                    if q.GetNetname() == 'GND' and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
        chk = ViaCheck(b)
        for k in range(polys.OutlineCount()):
            if any(polys.Contains(q, k) for q in anchors):
                continue
            bb = polys.Outline(k).BBox()
            x0, y0, x1, y1 = mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())
            spot = None
            for d in (0.6, 0.5):
                for j in range(int((y1 - y0) / 0.1) + 1):
                    for i in range(int((x1 - x0) / 0.1) + 1):
                        q = (round(x0 + 0.1 * i, 2), round(y0 + 0.1 * j, 2))
                        if polys.Contains(rr.P(*q), k) and chk.ok(q, d):
                            spot = (q, d)
                            break
                    if spot:
                        break
                if spot:
                    break
            if spot:
                added.append(chk.add(*spot))
                spots.append((zname, spot))
            elif log is not None:
                log.append(f'{zname} island at ({x0:.1f}, {y0:.1f})-({x1:.1f}, {y1:.1f}) has no via spot')
    return added, spots


def redraw(b, log):
    """The open connections of the REROUTE nets are drawn from explicit geometry (r7_redraw.py), together with the
    removal of the R6 copper they replace and of the copper the removed port parts left behind."""
    r7_redraw.redraw(b, log)


def finish(b, log, board_path):
    """Check that no R6 copper of the displaced nets hangs (the redraw removes what it replaces by name, so anything
    KiCad's DRC still calls dangling here is a defect: it stops the build); every GND pour island without a via or
    through-hole pin gets a via (ViaCheck rules) where one fits."""
    n = _drc_prune_r6(b, board_path)
    assert n == 0, f'{n} R6 item(s) of the displaced nets left dangling by the redraw'
    log.append('R6 leftovers DRC calls dangling: none')
    _, spots = _island_vias(b, log)
    log.append(f'GND islands given a via: {spots}')


STAGES = [('surgery', surgery), ('rf', rf), ('limiter', limiter), ('gnss', gnss), ('radio', radio),
          ('interface', interface), ('u1fan', u1fan), ('clean', clean), ('stitch', stitch), ('redraw', redraw),
          ('finish', finish)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--stop', help='stop after this stage (debugging)')
    args = ap.parse_args()
    pcbnew.KIID.SeedGenerator(7201)
    b = pcbnew.LoadBoard(str(args.board))
    STATE['r6'] = {t.m_Uuid.AsString() for t in b.GetTracks() if t.GetNetname() in REROUTE}
    log = []
    for name, fn in STAGES:
        fn(b, log, args.board) if name in ('clean', 'finish') else fn(b, log)
        print(f'[{name}]', *log, sep='\n  ')
        log.clear()
        if args.stop == name:
            break
    lib.fill(b)
    pcbnew.SaveBoard(str(args.board), b, True)
    print('saved', args.board)


if __name__ == '__main__':
    main()
