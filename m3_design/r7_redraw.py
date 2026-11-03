#!/usr/bin/env python3
"""R7 redraw of the R6 connections the new copper displaced, from explicit geometry (r7_route.py stage 'redraw').

Imported by r7_route.py; runs on the board as the 'stitch' stage leaves it, after 'clean' has removed the R6 copper of
the displaced nets that conflicted with the new copper. It replaces the grid router's recorded result (the former
r7_reroute_session.json): every segment and via below is drawn deliberately (fix agent F2, review pass 2 RG-01..04,
RQ-04..06, REGRESSION-05; record in sources/r7_review/fix2_F2_handoff.md).

Rules followed throughout: 0/45/90 degree segments on exact nm coordinates (round, not truncate), one width per net
(0.15 mm signals, 0.2 mm BAT_ILIM as R6 drew it, power nets their R6 width), pad entries straight and centred where
the pad allows, branches from existing copper instead of copies of it, no route under U1's body that R6 did not
already have, and every deletion matched by exact end points (0.6 um, one to one) and asserted, so a changed
upstream board stops the build instead of being patched silently.

  orphans      RG-04: R6 copper left by the removed port parts (D130/D131/C171/C179/C180/R205): floating GND chain,
               GND stubs held only by the pour, the dead In2 3V3 branch, the D130.5 and C179.1 junctions, the R205.1
               star (C90's 3V3 via reaches the FB31 lobe of the In2 plane directly instead)
  bat_ilim     RG-02 / REGRESSION-08: U9.9-R84.1 link square into R84.1; the TP89 branch tees off it beside R84 (no
               copy of the link); TP89 on the bottom side next to it (fix2_F1)
  buzz_drv     BUZZ_DRV as fix2_F1 drew it (>= 1 mm from QSPI_IO1, off USB_DP's In2), without R6's single-layer via
               and In2 stub at U1.29 and the doubled stub at R162.1
  bat_fault_n  BAT_FAULT_N as fix2_F1 drew it (In2 west of QSPI_IO0), R6's second In2 branch removed
  cam_uart     RQ-06: RX one In2 lane (no duplicated branch, no loop) over R6's QSPI_NCS crossing and R6's F.Cu hop; TX
               across QSPI_IO3 on R6's line, R6's In2 west of the lanes, round U3 and along the band as before, into
               U12.5 from the north (no weave under C10)
  leds         RQ-06 / RG-03: U1.38/U1.37 straight out of their toes into In2 lanes round the north of QSPI_NCS's via
               (no In2 under QSPI B.Cu where R6 had plane), B.Cu under CAM_5V_SENSE, F.Cu into R32.1 (through J123's
               gap) and R33.1 from the south (62.7 mm with a U-turn under U1 -> about 33 mm)
  pullpin      RG-01 / RQ-04: one route U1.8 -> D122.3 that joins R6's D122/R160/R161/C160 tree, 2 vias (was 6)
  pullpin_ext  REGRESSION-05: R160.1 -> J123.1 with >= 0.5 mm to CAM_5V and VLOGIC_SENSE copper on every layer
  vlogic_sense RG-03 / RQ-06: no hairpin, no U-turn; R6's In2 trunk to R60.2 (entered from the south) and C60.1
  bat_sw       RG-03: BAT_SW_RETURN without the hairpin or its east F.Cu hop, BAT_SW_SOURCE without the loop east
"""
import math

import pcbnew

F, B, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
LAYER = {'F': F, 'B': B, 'I': IN2}
W = 0.15                       # signal width (house practice; the displaced nets' R6 width)
V5 = 0.5                       # 0.5/0.3 vias where a 0.6 via does not keep the rules (R6 has 129 of them)


def nm(v):
    return int(round(v * 1e6))


class Edit:
    """Strict editing helpers on one board; `log` collects one line per stage."""

    def __init__(self, b, log):
        self.b, self.log = b, log
        self.removed = self.added = 0

    def _ends(self, t):
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            return [(p.x / 1e6, p.y / 1e6)]
        return [(t.GetStart().x / 1e6, t.GetStart().y / 1e6), (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6)]

    def rm(self, net, layer, *pts, n=1):
        """Delete the n tracks (layer 'F'/'B'/'I') or vias (layer 'V') of net with exactly these end points."""
        tol = 0.0006
        hit = []
        for t in self.b.GetTracks():
            if t.GetNetname() != net:
                continue
            if layer == 'V':
                if t.GetClass() != 'PCB_VIA':
                    continue
            elif t.GetClass() != 'PCB_TRACK' or t.GetLayer() != LAYER[layer]:
                continue
            e = self._ends(t)
            if len(e) != len(pts):
                continue
            if len(e) == 1:
                ok = math.dist(e[0], pts[0]) <= tol
            else:
                ok = (math.dist(e[0], pts[0]) <= tol and math.dist(e[1], pts[1]) <= tol) or \
                     (math.dist(e[0], pts[1]) <= tol and math.dist(e[1], pts[0]) <= tol)
            if ok:
                hit.append(t)
        assert len(hit) == n, (net, layer, pts, len(hit))
        for t in hit:
            self.b.Delete(t)
        self.removed += n

    def rm_all(self, net, layer, segs):
        for a, c in segs:
            self.rm(net, layer, a, c)

    def track(self, net, layer, pts, w=W):
        ni = self.b.FindNet(net)
        assert ni is not None, net
        for a, c in zip(pts, pts[1:]):
            dx, dy = abs(c[0] - a[0]), abs(c[1] - a[1])
            assert dx > 1e-6 or dy > 1e-6, (net, a, c)
            assert dx < 1e-4 or dy < 1e-4 or abs(dx - dy) < 1e-4, f'{net} {a}->{c} is not 0/45/90 deg'
            t = pcbnew.PCB_TRACK(self.b)
            t.SetLayer(LAYER[layer])
            t.SetWidth(nm(w))
            t.SetStart(pcbnew.VECTOR2I(nm(a[0]), nm(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(nm(c[0]), nm(c[1])))
            t.SetNet(ni)
            self.b.Add(t)
            self.added += 1

    def via(self, net, p, d=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pcbnew.VECTOR2I(nm(p[0]), nm(p[1])))
        v.SetWidth(nm(d))
        v.SetDrill(nm(drill))
        v.SetNet(self.b.FindNet(net))
        self.b.Add(v)
        self.added += 1

    def pad(self, ref, num):
        p = self.b.FindFootprintByReference(ref).FindPadByNumber(num).GetPosition()
        return round(p.x / 1e6, 4), round(p.y / 1e6, 4)


# --- RG-04: R6 copper the removed port parts left behind ---------------------------------------------------------

def orphans(e):
    # GND F.Cu chain from the removed D131.2 to the removed C180.2: touched no pad or via, held only by the pour
    e.rm_all('GND', 'F', [((36.5, 63.65), (36.5, 64.3)), ((36.5, 64.3), (37.25, 65.05)),
                          ((37.25, 65.05), (37.275, 65.075)), ((37.275, 65.075), (37.275, 66.0))])
    # GND stubs of the removed C171.2, D131.6 and D130.2/C179.2 into the pour (their stitching vias stay)
    e.rm_all('GND', 'F', [((25.5, 27.5), (26.4, 28.4)), ((26.4, 28.4), (26.5, 28.4)),
                          ((35.55, 61.35), (35.55, 61.66)), ((35.55, 61.66), (35.01, 62.2)),
                          ((36.5, 53.65), (36.5, 54.8)), ((36.5, 54.8), (37.275, 55.575)),
                          ((37.275, 55.575), (37.275, 56.0)), ((37.275, 56.0), (37.275, 56.615)),
                          ((37.275, 56.615), (36.99, 56.9))])
    # dead In2 3V3 branch (r7_route.surgery removed its continuation), and the In2 link it left between two vias that
    # both sit in the 3V3 plane
    e.rm_all('3V3', 'I', [((15.0, 43.4), (17.57, 40.83)), ((17.57, 40.83), (17.57, 36.5)),
                          ((17.58, 36.5), (17.57, 36.5)), ((17.58, 34.0), (17.58, 36.5)),
                          ((14.525, 43.4), (15.0, 43.4)), ((15.0, 43.4), (15.85, 44.25))])
    # D130.5 junction (8-30 um pieces, an acute T, unmerged joints) -> one Y
    e.rm_all('3V3', 'F', [((36.5, 51.35), (36.5, 50.15)), ((36.5, 51.35), (36.5, 51.65)),
                          ((36.429, 51.729), (36.429, 51.721)), ((36.45, 51.75), (36.429, 51.729)),
                          ((36.45, 51.75), (36.94, 52.24)), ((36.94, 52.24), (36.94, 52.65))])
    e.track('3V3', 'F', [(36.5, 50.15), (36.5, 51.65)], 0.25)
    e.track('3V3', 'F', [(36.5, 51.65), (36.94, 52.09), (36.94, 52.65)], 0.25)
    # the same branch at the trimmed C179.1 corner (25/35 um jog) and at U1.11's via (a 25-50 um triangle round it)
    e.rm_all('3V3', 'F', [((34.9, 53.05), (34.9, 55.95)), ((34.9, 55.95), (34.925, 55.975)),
                          ((34.925, 55.975), (34.925, 56.0)), ((34.925, 56.0), (32.625, 56.0)),
                          ((32.625, 56.0), (31.125, 54.5)), ((31.125, 54.5), (31.15, 54.525)),
                          ((31.15, 54.525), (31.15, 54.55)), ((31.15, 54.55), (31.1, 54.5))])
    e.track('3V3', 'F', [(31.1, 54.5), (32.6, 56.0), (34.65, 56.0), (34.9, 55.75), (34.9, 53.05)], 0.25)
    # R205.1 star (acute angle, 2-8 um pieces) and its F.Cu path from two plane vias to C90's 3V3 via (34.663,
    # 36.105): C90's via (38.172, 37.819) reaches the FB31 lobe of the In2 3V3 plane instead, through the In2 free
    # east of J123 (the space west of J123 goes to PULLPIN and VLOGIC_SENSE)
    e.rm_all('3V3', 'F', [((33.57, 35.0), (32.57, 35.0)), ((33.57, 35.0), (32.87, 34.3)),
                          ((33.57, 35.0), (33.17, 35.4)), ((33.17, 35.4), (33.17, 36.4)),
                          ((33.17, 36.4), (33.47, 36.7)), ((33.47, 36.7), (34.07, 36.7)),
                          ((34.07, 36.7), (34.67, 36.1)), ((34.67, 36.1), (34.6647, 36.1053)),
                          ((34.65, 36.1), (34.6553, 36.1053)), ((34.6553, 36.1053), (34.6631, 36.1053)),
                          ((34.6647, 36.1053), (34.6631, 36.1053))])
    for p in ((32.57, 35.0), (32.87, 34.3), (34.6631, 36.1053)):
        e.rm('3V3', 'V', p)
    e.rm_all('3V3', 'I', [((36.3769, 37.8191), (34.6631, 36.1053)), ((38.1719, 37.8191), (36.3769, 37.8191))])
    e.track('3V3', 'I', [(38.1719, 37.8191), (38.0, 37.6472), (38.0, 29.6117), (35.73, 27.3417)], 0.2)
    e.log.append('RG-04: floating GND chain, 3 GND stubs, dead In2 3V3 branch removed; D130.5 / C179.1 / U1.11 '
                 'joints redrawn; R205.1 star replaced by an In2 link from C90\'s via to the FB31 lobe')


# --- RG-02 / REGRESSION-08: BAT_ILIM ----------------------------------------------------------------------------
TP89_AT = (8.1, 33.6)          # bottom side beside R84 (fix2_F1): its 1.0 mm bare-pad clearance is clear of the
                               # corridor (x <= 6.275), BAT_IN's via (9.2, 36.05) and D8


def bat_ilim(e):
    # R6's 0.2 mm link from U9.9 round R84.2 entered R84.1 through 25 um pieces at 45 degrees: one vertical down the
    # link's x 9.875 column and a square entry at R84.1's centre
    e.rm_all('BAT_ILIM', 'F', [((9.875, 37.3), (10.675, 36.5)), ((10.675, 36.5), (10.65, 36.475)),
                               ((10.6, 36.5), (10.625, 36.475)), ((10.625, 36.475), (10.65, 36.475)),
                               ((9.875, 38.7), (9.875, 37.3))])
    e.track('BAT_ILIM', 'F', [(9.875, 38.7), (9.875, 37.05), (9.875, 36.475), (10.65, 36.475)], 0.2)
    # the test-pad branch tees off that link west of R84 (no copy of it), drops through a via south-west of BAT_IN's
    # via and runs straight into TP89 from the south
    tp = e.b.FindFootprintByReference('TP89')
    if not tp.IsFlipped():
        tp.Flip(tp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    tp.SetOrientationDegrees(0)
    tp.SetPosition(pcbnew.VECTOR2I(nm(TP89_AT[0]), nm(TP89_AT[1])))
    e.track('BAT_ILIM', 'F', [(9.875, 37.05), (9.3, 37.05)], 0.2)
    e.via('BAT_ILIM', (9.3, 37.05))
    e.track('BAT_ILIM', 'B', [(9.3, 37.05), (8.1, 35.85), TP89_AT], 0.2)
    e.log.append(f'BAT_ILIM: U9.9-R84.1 link square into R84.1; TP89 (bottom, {TP89_AT}) branch from the link, 4.5 mm, '
                 '1 via; net 9.3 mm, 1 via (pass 2: the branch a 0.15 mm copy of the link, net 36.8 mm, 4 vias)')


# --- BUZZ_DRV (fix2_F1 geometry) -----------------------------------------------------------------------------------

def buzz_drv(e):
    # R6's escape from U1.29 ran through a via that carried only F.Cu tracks and a dangling In2 stub
    e.rm('BUZZ_DRV', 'I', (26.85, 47.55), (27.05, 47.75))
    e.rm('BUZZ_DRV', 'B', (19.65, 50.25), (19.25, 50.65))         # R6's via west of the new path, and its stub
    e.rm('BUZZ_DRV', 'V', (19.25, 50.65))
    e.rm('BUZZ_DRV', 'V', (26.85, 47.55))
    e.rm_all('BUZZ_DRV', 'F', [((26.35, 45.95), (26.35, 47.05)), ((26.35, 47.05), (26.85, 47.55)),
                               ((26.85, 47.55), (24.15, 50.25))])
    e.track('BUZZ_DRV', 'F', [(26.35, 45.95), (26.35, 48.05), (24.15, 50.25)])
    # R6's B.Cu (24.15, 50.25)-(19.65, 50.25) stays; F1's path >= 1 mm from QSPI_IO1, over VLOGIC on F.Cu under C84's
    # body and round C96 to the left edge (R167.2's GND link to C96.2 gives way to its own via)
    e.rm_all('GND', 'B', [((6.0, 56.125), (6.95, 56.125)), ((6.95, 56.125), (8.3, 57.475))])
    e.track('GND', 'B', [e.pad('R167', '2'), (6.0, 57.2)], 0.25)
    e.via('GND', (6.0, 57.2))
    e.track('BUZZ_DRV', 'B', [(19.65, 50.25), (14.3, 55.6), (13.0, 55.6)])
    e.via('BUZZ_DRV', (13.0, 55.6))
    e.track('BUZZ_DRV', 'F', [(13.0, 55.6), (9.0, 55.6)])
    e.via('BUZZ_DRV', (9.0, 55.6))
    e.track('BUZZ_DRV', 'B', [(9.0, 55.6), (7.55, 55.6), (7.0, 56.15), (7.0, 58.05), (6.45, 58.6), (2.0, 58.6),
                              (1.55, 59.05), (1.55, 68.5), (4.3, 71.25), (4.3, 85.1)])
    e.rm('BUZZ_DRV', 'B', (4.25, 85.05), (4.3, 85.1), n=2)          # R6's doubled stub inside R162.1
    e.log.append('BUZZ_DRV: fix2_F1 route, U1.29 escape without the single-layer via and In2 stub, straight into '
                 'R162.1\'s centre')


# --- BAT_FAULT_N (fix2_F1 geometry) ---------------------------------------------------------------------------------

def bat_fault_n(e):
    e.rm_all('BAT_FAULT_N', 'F', [((11.9, 43.0), (12.0, 43.1)), ((12.0, 43.1), (11.975, 43.1)),
                                  ((11.9, 41.5), (11.9, 43.0))])
    e.track('BAT_FAULT_N', 'F', [(11.9, 41.5), (11.9, 42.1), (11.9, 43.1)])
    e.track('BAT_FAULT_N', 'F', [(11.9, 42.1), (12.3, 42.1)])
    e.via('BAT_FAULT_N', (12.3, 42.1))
    e.track('BAT_FAULT_N', 'I', [(12.3, 42.1), (12.3, 56.2)])
    e.via('BAT_FAULT_N', (12.3, 56.2))
    e.rm_all('BAT_FAULT_N', 'B', [((15.6, 54.8), (15.6, 55.1)), ((15.5994, 55.9008), (15.5994, 56.2027)),
                                  ((15.5994, 56.2027), (16.4, 57.0033)), ((16.4, 57.0033), (16.4, 58.0))])
    # R6's second In2 branch to the via (15.6, 55.1) (the B.Cu beyond that via went with the clean stage)
    e.rm_all('BAT_FAULT_N', 'I', [((14.3, 56.4), (15.6, 55.1)), ((14.3, 56.4), (14.3, 57.2)),
                                  ((14.2833, 57.2167), (14.3, 57.2)), ((14.2833, 57.2167), (14.2833, 57.2169))])
    e.rm('BAT_FAULT_N', 'V', (15.6, 55.1))
    e.track('BAT_FAULT_N', 'B', [(12.3, 56.2), (15.5994, 56.2), (16.4, 57.0006), (16.4, 58.0)])
    e.track('BAT_FAULT_N', 'B', [(15.5994, 55.9008), (15.5994, 56.2)])
    e.log.append('BAT_FAULT_N: fix2_F1 route (In2 x 12.3 west of QSPI_IO0), R6\'s second In2 branch removed')


# --- RQ-06: camera UART -----------------------------------------------------------------------------------------------

def cam_uart(e):
    # The In2 3V3 plane is QSPI_IO3's and QSPI_NCS's B.Cu reference here (critical-reference method, R6 gate). Each In2
    # lane under them crosses where R6 already crossed, at 90 degrees or on R6's own line, and the plane each side
    # stays joined (fix2_F2 handoff, critical reference).
    # RX: R6's In2 run between the vias (21.15, 42.55) and (31.15, 42.85) (a duplicated branch and a loop round the
    # RAW_PROTECTED via) becomes one lane: its via moves to (21.35, 42.35) (0.6 mm off QSPI_IO3, 0.48 mm under the
    # LED_RED via), the lane crosses QSPI_NCS on R6's LED_YEL crossing and hops over to F.Cu on R6's LED_YEL hop
    # (25.85-28.25), which leaves the plane under QSPI_NCS open to the south between the LED lanes and RX
    e.rm_all('CAM_MCU_RX', 'I', [((21.15, 42.55), (21.95, 42.55)), ((21.15, 42.55), (22.75, 42.55)),
                                 ((21.95, 42.55), (22.85, 41.65)), ((22.75, 42.55), (23.65, 41.65)),
                                 ((22.85, 41.65), (24.15, 41.65)), ((24.15, 41.65), (24.55, 41.25)),
                                 ((24.55, 40.15), (24.55, 41.25)), ((24.55, 40.15), (25.75, 38.95)),
                                 ((25.75, 38.95), (26.25, 38.95)), ((26.25, 38.95), (27.65, 40.35)),
                                 ((27.65, 40.35), (27.65, 42.55)), ((27.65, 42.85), (27.65, 42.55)),
                                 ((27.65, 42.85), (31.15, 42.85))])
    e.rm_all('CAM_MCU_RX', 'F', [((17.35, 44.75), (19.55, 42.55)), ((19.55, 42.55), (21.15, 42.55))])
    e.rm('CAM_MCU_RX', 'V', (21.15, 42.55))
    e.track('CAM_MCU_RX', 'F', [(17.35, 44.75), (19.75, 42.35), (21.35, 42.35)])
    e.via('CAM_MCU_RX', (21.35, 42.35), V5)
    e.track('CAM_MCU_RX', 'I', [(21.35, 42.35), (25.85, 42.35)])
    e.via('CAM_MCU_RX', (25.85, 42.35), V5)
    e.track('CAM_MCU_RX', 'F', [(25.85, 42.35), (28.25, 42.35)])
    e.via('CAM_MCU_RX', (28.25, 42.35), V5)
    e.track('CAM_MCU_RX', 'I', [(28.25, 42.35), (30.65, 42.35), (31.15, 42.85)])
    # the bottom-side GND via at the end of R6's B.Cu GND run (27.425, 41.349)-(26.45, 42.324) goes 0.05 mm south,
    # clear of the RX hop
    e.rm('GND', 'V', (26.45, 42.85))
    e.rm('GND', 'B', (26.45, 42.3244), (26.45, 42.85))
    e.track('GND', 'B', [(26.45, 42.3244), (26.45, 42.9)], 0.2)
    e.via('GND', (26.45, 42.9))
    # TX: the u1fan fan-out ends at a via south-east of QSPI_IO3; In2 crosses QSPI_IO3 at 90 degrees where R6's TX
    # did, then R6's In2 north (clear of the LED and RX lanes) and round U3, the F.Cu column under U3 and the In2 band
    # run of the redraw before, F.Cu down the east, B.Cu into U12.5 from the north (R6's tail weaved between C10's
    # pads). The via sits where RXEN's GND via (rework iface_returns) still fits within 1 mm of RXEN's.
    e.rm('CAM_MCU_TX', 'F', (18.35, 44.25), (20.55, 44.25))
    e.rm_all('CAM_MCU_TX', 'B', [((36.5533, 46.8562), (36.9533, 47.2562)), ((36.9533, 47.2562), (38.4533, 47.2562)),
                                 ((38.4533, 47.2562), (39.3533, 46.3562)), ((39.3533, 46.3562), (40.8533, 46.3562)),
                                 ((40.8533, 46.3562), (41.0533, 46.5562)), ((41.05, 49.4529), (41.05, 49.45)),
                                 ((41.0533, 46.5562), (41.0533, 49.4562)), ((41.0533, 49.4562), (41.05, 49.4529))])
    e.track('CAM_MCU_TX', 'F', [(18.35, 44.25), (19.6, 44.25), (20.45, 43.4)])
    e.via('CAM_MCU_TX', (20.45, 43.4), V5)
    e.track('CAM_MCU_TX', 'I', [(20.45, 43.4), (20.45, 42.95), (19.95, 42.45), (19.95, 39.15), (20.34, 38.76),
                                (21.94, 38.76), (25.45, 35.25), (25.45, 33.95), (24.75, 33.25)])
    e.via('CAM_MCU_TX', (24.75, 33.25))
    e.track('CAM_MCU_TX', 'F', [(24.75, 33.25), (24.75, 28.35), (24.95, 28.15)])
    e.via('CAM_MCU_TX', (24.95, 28.15))
    e.track('CAM_MCU_TX', 'I', [(24.95, 28.15), (28.55, 24.55), (38.75, 24.55), (39.55, 25.35)])
    e.via('CAM_MCU_TX', (39.55, 25.35))
    e.track('CAM_MCU_TX', 'F', [(39.55, 25.35), (39.55, 37.15), (37.95, 38.75)])
    e.via('CAM_MCU_TX', (37.95, 38.75))
    e.track('CAM_MCU_TX', 'B', [(37.95, 38.75), (38.25, 39.05), (38.25, 40.85), (41.05, 43.65), (41.05, 49.45)])
    e.log.append('CAM_MCU_RX: one In2 lane over R6\'s QSPI_NCS crossing and R6\'s F.Cu hop (duplicate branch and loop '
                 'removed); CAM_MCU_TX: across QSPI_IO3 on R6\'s line, R6\'s In2 north, into U12.5 from the north')


# --- RQ-06 / RG-03: LED_RED and LED_YEL -------------------------------------------------------------------------------

def leds(e):
    e.rm('LED_RED', 'F', (21.85, 45.95), (21.75, 45.85))           # R6 stubs inside the pads
    e.rm('LED_RED', 'F', (36.55, 29.65), (36.6, 29.7))
    e.rm('LED_RED', 'F', (36.65, 29.75), (36.6, 29.7))
    e.rm('LED_YEL', 'F', (40.75, 29.45), (40.7, 29.4))
    # what clean left of R6's LED_YEL ladder (F -> B -> In2 -> F at U1.37; its continuation conflicted with new copper)
    e.rm_all('LED_YEL', 'F', [((22.35, 45.95), (22.35, 43.45)), ((25.85, 42.25), (28.25, 42.25))])
    e.rm_all('LED_YEL', 'B', [((22.35, 43.45), (23.55, 42.25)), ((23.55, 42.25), (23.95, 42.25))])
    e.rm('LED_YEL', 'I', (23.95, 42.25), (25.85, 42.25))
    for p in ((22.35, 43.45), (23.95, 42.25), (25.85, 42.25)):
        e.rm('LED_YEL', 'V', p)
    # straight out of the pin toes to vias between QSPI_IO3's and RXEN's B.Cu diagonals (0.6 mm off QSPI_IO3, so their
    # In2 openings stay off it), two In2 lanes 0.3 mm apart round the north of QSPI_NCS's via (no In2 under QSPI_NCS or
    # QSPI_IO3 where R6 had plane; the plane inside the bend stays joined through the gap of RX's F.Cu hop), B.Cu under
    # CAM_5V_SENSE and VLOGIC_SENSE, F.Cu into each resistor
    e.track('LED_YEL', 'F', [(22.35, 45.95), (22.35, 41.35)])
    e.via('LED_YEL', (22.35, 41.35), V5)
    e.track('LED_YEL', 'I', [(22.35, 41.35), (24.25, 41.35), (24.45, 41.15), (24.45, 39.8), (25.4, 38.85),
                             (26.8, 38.85), (27.65, 39.7), (27.65, 41.0), (27.85, 41.2), (30.35, 41.2)])
    e.via('LED_YEL', (30.35, 41.2), V5)
    e.track('LED_YEL', 'B', [(30.35, 41.2), (37.2, 41.2)])
    e.via('LED_YEL', (37.2, 41.2), V5)
    e.track('LED_YEL', 'F', [(37.2, 41.2), (40.7, 37.7), (40.7, 29.4)])
    e.track('LED_RED', 'F', [(21.85, 45.95), (21.85, 41.85)])
    e.via('LED_RED', (21.85, 41.85), V5)
    e.track('LED_RED', 'I', [(21.85, 41.85), (24.25, 41.85), (24.75, 41.35), (24.75, 40.0), (25.6, 39.15),
                             (26.6, 39.15), (27.35, 39.9), (27.35, 41.2), (27.85, 41.7), (30.85, 41.7)])
    e.via('LED_RED', (30.85, 41.7), V5)
    e.track('LED_RED', 'B', [(30.85, 41.7), (33.2, 41.7)])
    e.via('LED_RED', (33.2, 41.7), V5)
    e.track('LED_RED', 'F', [(33.2, 41.7), (36.0, 38.9), (36.0, 33.6), (36.6, 33.0), (36.6, 29.7)])
    e.log.append('LED_RED: U1.38 -> R32.1 32.6 mm, 3 vias (pass 2: 62.7 mm, U-turn, under U1); LED_YEL: U1.37 -> R33.1 '
                 '36.3 mm, 3 vias (pass 2: 33.2 mm, 6 vias and a hook); both round the north of QSPI_NCS\'s via')


# --- RG-01 / RQ-04: PULLPIN -------------------------------------------------------------------------------------------

def pullpin(e):
    # R6's escape from U1.8 (a V-jog and a hook to a via south-east of the pin) and its In2 run: one F.Cu escape, In2
    # north beside SERVO1_MCU and through the 3V3 plane past NRST's via, F.Cu into D122.3 from the south; R6's
    # D122.3 / R160.2 / R161.2 / C160.1 tree stays as drawn (the session's copy of it beside it is gone)
    e.rm_all('PULLPIN', 'F', [((29.4, 56.0), (31.1, 56.0)), ((31.1, 56.0), (31.4, 55.7)), ((32.2, 56.5), (31.4, 55.7)),
                              ((34.1953, 56.5), (32.2, 56.5)), ((35.4377, 57.7424), (34.1953, 56.5))])
    e.rm('PULLPIN', 'V', (35.4377, 57.7424))
    e.rm_all('PULLPIN', 'I', [((35.4377, 57.7424), (34.9411, 57.2458)), ((34.9411, 57.2458), (34.9411, 46.7668)),
                              ((34.9411, 46.7668), (35.0675, 46.6404))])
    e.rm('PULLPIN', 'F', (32.2, 30.9), (32.5, 30.6))               # R6 dead end inside D122.3
    e.track('PULLPIN', 'F', [(29.4, 56.0), (32.0, 56.0), (32.5, 56.5), (35.17, 56.5)])
    e.via('PULLPIN', (35.17, 56.5))
    e.track('PULLPIN', 'I', [(35.17, 56.5), (35.17, 45.98), (33.93, 44.74), (33.93, 35.85)])
    e.via('PULLPIN', (33.93, 35.85))
    e.track('PULLPIN', 'F', [(33.93, 35.85), (33.93, 32.6), (32.5, 31.17), (32.5, 30.6)])
    # C160.2's GND trace to the via (32.75, 32.3) crossed the way into D122.3 (the pad keeps its pour connection, the
    # via stays as a stitch)
    e.rm_all('GND', 'F', [((34.9, 28.92), (34.9, 30.1533)), ((34.9, 30.1533), (32.7532, 32.3001))])
    e.log.append('PULLPIN: U1.8 -> D122.3 33.0 mm, 2 vias (pass 2: 46.5 mm, a second F.Cu copy of the tree, 6 vias)')


def pullpin_ext(e):
    # R160.1 -> via north of R160 -> B.Cu between C98's and C94's pads -> via west of C60 -> F.Cu into J123.1 from the
    # north. CAM_5V and VLOGIC_SENSE copper stay >= 0.5 mm away on every layer (REGRESSION-05)
    e.track('PULLPIN_EXT', 'F', [(32.9, 26.17), (32.9, 25.8), (33.1, 25.6), (33.875, 25.6)])
    e.via('PULLPIN_EXT', (33.875, 25.6))
    e.track('PULLPIN_EXT', 'B', [(33.875, 25.6), (33.875, 27.4), (34.4, 27.925), (34.4, 29.55), (34.15, 29.8)])
    e.via('PULLPIN_EXT', (34.15, 29.8))
    e.track('PULLPIN_EXT', 'F', [(34.15, 29.8), (34.15, 31.2), (35.0, 32.05), (35.0, 34.6)])
    e.log.append('PULLPIN_EXT: R160.1 -> J123.1 11.1 mm, 2 vias, >= 0.72 mm to CAM_5V and VLOGIC_SENSE copper (pass 2: '
                 '13.7 mm, jogs, 0.40 mm to CAM_5V)')


def vlogic_sense(e):
    # the orphan via and stubs at C60.1, and the doubled joint at R60.2
    for (a, c), lay in ((((35.5769, 32.8066), (35.8044, 32.8066)), 'I'),
                        (((35.8044, 32.8066), (35.8234, 32.8066)), 'F'),
                        (((35.8234, 32.8066), (35.83, 32.8)), 'F'), (((35.8044, 32.8066), (35.6599, 32.8066)), 'B'),
                        (((35.6599, 32.8066), (35.1, 32.2467)), 'B'), (((35.1, 31.6), (35.1, 32.2467)), 'B'),
                        (((32.5, 37.0), (32.53, 37.0)), 'B'), (((32.53, 36.5), (32.53, 37.0)), 'B'),
                        (((32.53, 37.0), (32.53, 36.4833)), 'B'), (((32.53, 36.4833), (33.5, 35.5133)), 'B'),
                        (((33.5, 35.5133), (33.5, 32.93)), 'B')):
        e.rm('VLOGIC_SENSE', lay, a, c)
    e.rm('VLOGIC_SENSE', 'V', (35.8044, 32.8066))
    # R6's In2 3V3 U-turn from FB31's via (35.73, 27.34) to the plane (and its run inside the plane), where C60.1's link
    # goes: FB31's new feed reaches that via through the In2 lobe r7_rework.planes adds (r7_rework.fb31)
    e.rm_all('3V3', 'I', [((35.73, 27.3417), (36.73, 28.3417)), ((36.73, 28.3417), (36.73, 31.5417)),
                          ((36.73, 31.5417), (36.23, 32.0417)), ((36.23, 32.0417), (35.23, 32.0417)),
                          ((35.23, 32.0417), (34.53, 31.3417)), ((34.53, 31.3417), (30.63, 31.3417))])
    e.track('VLOGIC_SENSE', 'B', [(32.53, 37.0), (32.53, 36.47), (33.5, 35.5), (33.5, 32.93)])
    # U1.17: F.Cu to a via, R6's In2 route under the pin row and up the east of the U1/U3 group to a via south of
    # R60.2 (entered from the south), on through the In2 east of the plane into C60.1 from the east
    e.track('VLOGIC_SENSE', 'F', [(29.4, 51.5), (30.7, 51.5)])
    e.via('VLOGIC_SENSE', (30.7, 51.5))
    e.track('VLOGIC_SENSE', 'I', [(30.7, 51.5), (30.2, 51.5), (29.2, 50.5), (29.2, 46.1), (32.44, 42.86), (32.44, 38.0),
                                  (32.44, 34.2), (35.04, 31.6), (36.0, 31.6)])
    e.track('VLOGIC_SENSE', 'I', [(32.44, 38.0), (33.0, 38.0)])
    e.via('VLOGIC_SENSE', (33.0, 38.0))
    e.track('VLOGIC_SENSE', 'B', [(33.0, 38.0), (32.53, 37.53), (32.53, 37.0)])
    e.via('VLOGIC_SENSE', (36.0, 31.6))
    e.track('VLOGIC_SENSE', 'B', [(36.0, 31.6), (35.1, 31.6)])
    e.log.append('VLOGIC_SENSE: 3 vias, U1.17 -> R60.2 18.8 mm, no hairpin or U-turn (pass 2: 6 vias, 31.7 mm, a '
                 'hairpin, a U-turn to y 55.3)')


# --- RG-03: BAT_SW_SOURCE / BAT_SW_RETURN -----------------------------------------------------------------------------

def bat_sw(e):
    # SOURCE: R6's In2 up the east edge and its via (41.36, 39.0); B.Cu under RETURN's In2 (the crossing the redraw
    # before had, without its loop east); the band's north lane round the USB_OVLO via; B.Cu at y 25.0 into R80.2
    e.rm_all('BAT_SW_SOURCE', 'B', [((17.125, 24.435), (17.125, 24.45)), ((17.16, 24.4), (17.125, 24.435))])
    e.track('BAT_SW_SOURCE', 'B', [(40.16, 37.8), (40.16, 36.8), (40.56, 36.4), (43.36, 36.4)])
    e.via('BAT_SW_SOURCE', (43.36, 36.4))
    e.track('BAT_SW_SOURCE', 'I', [(43.36, 36.4), (43.16, 36.4), (42.26, 35.5), (42.26, 32.1), (35.16, 25.0),
                                   (30.16, 25.0), (28.76, 26.4), (27.96, 26.4), (27.76, 26.2)])
    e.via('BAT_SW_SOURCE', (27.76, 26.2))
    e.track('BAT_SW_SOURCE', 'B', [(27.76, 26.2), (26.56, 25.0), (17.125, 25.0), (17.125, 24.45)])
    # RETURN: In2 from J1 up the east edge without the F.Cu hop (R6's via (44.4, 44.525) goes), the band's south lane,
    # F.Cu west and down to R165 as before, without the hairpin at the R6 via R7 removed (11.9, 44.125)
    e.rm('BAT_SW_RETURN', 'F', (44.3, 44.425), (44.4, 44.525))
    e.rm('BAT_SW_RETURN', 'V', (44.4, 44.525))
    e.track('BAT_SW_RETURN', 'I', [(44.4, 44.525), (44.4, 39.725), (41.9, 37.225), (41.9, 32.225), (36.0, 26.325),
                                   (31.9, 26.325)])
    e.via('BAT_SW_RETURN', (31.9, 26.325))
    e.track('BAT_SW_RETURN', 'F', [(31.9, 26.325), (30.5, 26.325), (30.0, 26.825), (24.8, 26.825), (23.6, 28.025),
                                   (23.6, 28.525), (22.2, 29.925), (21.0, 29.925), (19.5, 31.425), (19.5, 32.425),
                                   (15.0, 36.925), (15.0, 37.725)])
    e.via('BAT_SW_RETURN', (15.0, 37.725))
    e.track('BAT_SW_RETURN', 'I', [(15.0, 37.725), (16.3, 37.725)])
    e.via('BAT_SW_RETURN', (16.3, 37.725))
    e.track('BAT_SW_RETURN', 'B', [(16.3, 37.725), (16.3, 42.825), (14.1, 45.025), (14.1, 46.425)])
    e.via('BAT_SW_RETURN', (14.1, 46.425))
    e.rm_all('BAT_SW_RETURN', 'F', [((9.7, 44.825), (11.2, 44.825)), ((11.2, 44.825), (11.9, 44.125))])
    e.track('BAT_SW_RETURN', 'F', [(14.1, 46.425), (12.5, 44.825), (9.7, 44.825)])
    e.rm('GND', 'B', (29.05, 25.15), (30.317, 25.15))               # R6 GND stub from that via into the pour
    e.log.append('BAT_SW_RETURN: no hairpin, In2 continuous up the east edge; BAT_SW_SOURCE: no loop east of its '
                 'crossing')


STAGES = (orphans, bat_ilim, buzz_drv, bat_fault_n, cam_uart, leds, pullpin, pullpin_ext, vlogic_sense, bat_sw)


def redraw(b, log):
    e = Edit(b, log)
    for fn in STAGES:
        fn(e)
    log.append(f'redraw: {e.removed} R6 items removed, {e.added} tracks and vias drawn')
