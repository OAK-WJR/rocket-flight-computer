#!/usr/bin/env python3
"""Spike 3(c) battery band: placement and copper of the 7.7 A servo feed, the actuator switch and the input
protection at J1, on the scratch base board (base.py). Scratch only; the real build ports this into r8_power.py /
r8_place.tsv (step 4-5).

usage: <KiCad python3> -I battery.py BASE_DIR OUT_DIR [--no-fill]

Topology ("west chain", RESULT.md):
  J1.1 -> BAT_IN (B.Cu pour + In2 band + F.Cu under J1) -> Q120 (rot 90, drain east) -> ACT_FET_S bridge between the
  facing, aligned source rows -> Q121 (rot 270, drain west) -> RAW_ACT down the west strip past J124 (F/In2/B) ->
  west region (J124.2, C121) -> F.Cu-only bridge over the pyro-lane corridor (B.Cu, In2 GND under it) -> the J122 box
  (F.Cu + B.Cu + In2 finger) -> J122's RAW_ACT middle column.
Every number is board mm (y forward). Zones: power pours FULL connection, 0.3 mm clearance, 0.3 mm minimum width
(R7's power-zone settings); In2 GND is the background of the band.
"""
import shutil
import sys
from pathlib import Path

import pcbnew

MM, mm = pcbnew.FromMM, pcbnew.ToMM
F, In1, In2, B = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu

# --- placement: ref -> (x, y, rotation, side) ---------------------------------------------------------------------
FET_XA, FET_YC = 8.0, 103.0                  # Q121 centre; Q120 = Q121 + (8.38, -1.28): source rows aligned, 1.5 mm gap
PLACE = {
    'Q121': (FET_XA, FET_YC, 270, 'B'),                       # drain (RAW_ACT) west, sources east, gate fwd end
    'Q120': (FET_XA + 8.38, FET_YC - 1.28, 90, 'B'),          # sources west, drain (BAT_IN) east, gate aft end
    # gate-source network on the bridge's forward end (B); ACT_GATE bus y 107.3
    'C120': (12.5, 106.6, 270, 'B'),
    'R120': (14.3, 106.87, 270, 'B'),
    # gate drive on the top side, east of the F.Cu ACT_GATE hop at x 13.48 (RAW_PROTECTED reaches R122 from the east)
    'TP121': (13.48, 103.2, 0, 'F'),
    'R121': (13.91, 100.85, 0, 'F'),
    'Q122': (16.6, 100.85, 0, 'F'),
    'R122': (17.6, 103.36, 90, 'F'),
    'R123': (18.9, 102.5, 90, 'F'),
    # switch legs at J1.3 / J1.4 (bottom, under J1's body)
    'R80': (20.46, 107.9, 270, 'B'),
    'R165': (16.6, 107.9, 90, 'B'),
    # input protection at J1.1: TVS and input caps (bottom), damper (top strip aft of J1's body)
    'D8': (32.3, 101.6, 90, 'B'),
    'C80': (35.8, 102.3, 90, 'B'),
    'C96': (38.9, 102.3, 90, 'B'),
    'R167': (34.3, 108.4, 270, 'B'),
    'C89': (24.0, 102.15, 90, 'F'),
    'C95': (26.5, 102.15, 90, 'F'),
    'R166': (32.2, 101.7, 0, 'F'),
    # RAW_ACT bulk and test pad (west region), bulk ceramics straddling the B.Cu pour's aft edge
    'C121': (12.0, 83.8, 180, 'F'),
    'TP120': (3.0, 88.0, 0, 'B'),
    'C150': (8.0, 81.8, 90, 'B'),
    'C151': (5.4, 81.8, 90, 'B'),
    # RAW_ACT_SENSE divider in a notch at the west region's aft-east corner; its lane joins the pyro corridor
    'R177': (13.2, 85.61, 90, 'B'),
    'R124': (14.6, 85.18, 0, 'B'),
    'R125': (13.6, 83.23, 90, 'B'),
    'R182': (14.6, 83.23, 90, 'B'),
    'C122': (15.85, 82.96, 90, 'B'),
    # eFuse input side: BAT_IN feed on x 40.75 into U9.5 (U9 itself at the seed position)
    'C88': (41.17, 93.6, 0, 'B'),
    'R82': (39.93, 95.2, 180, 'B'),
    'TP80': (40.75, 97.8, 0, 'B'),
    'R81': (38.6, 92.8, 90, 'B'),
    'C87': (38.6, 89.6, 90, 'B'),
    'C81': (37.9, 86.0, 0, 'B'),
    'R83': (43.0, 96.1, 90, 'B'),
    # eFuse output parts moved aft of U9 (RAW_PROTECTED leaves U9.6 southward); GND test pads moved east
    'D9': (43.6, 79.5, 90, 'B'),
    'C82': (39.6, 78.6, 0, 'B'),
    'R92': (39.6, 81.6, 0, 'B'),
    'TP74': (44.6, 99.0, 0, 'B'),
    'TP88': (44.6, 101.6, 0, 'B'),
}

POUR = dict(clr=0.3, minw=0.3)


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


class Band:
    def __init__(self, board):
        self.b = board
        self.zones = []

    def net(self, name):
        n = self.b.FindNet(name)
        assert n is not None, name
        return n

    def place(self):
        for ref, (x, y, rot, side) in PLACE.items():
            f = self.b.FindFootprintByReference(ref)
            assert f is not None, ref
            if (side == 'B') != f.IsFlipped():
                f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            f.SetOrientationDegrees(rot)
            f.SetPosition(P(x, y))

    def zone(self, name, net, layer, pts, prio, clr=0.3, minw=0.3, conn=pcbnew.ZONE_CONNECTION_FULL):
        z = pcbnew.ZONE(self.b)
        z.SetLayer(layer)
        z.SetNet(self.net(net))
        z.SetZoneName(name)
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(MM(clr))
        z.SetMinThickness(MM(minw))
        z.SetPadConnection(conn)
        z.SetThermalReliefGap(MM(0.25))
        z.SetThermalReliefSpokeWidth(MM(0.4))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(MM(x), MM(y))
        assert not ol.IsSelfIntersecting(), name
        self.b.Add(z)
        self.zones.append(z)
        return z

    def track(self, net, layer, width, pts):
        n = self.net(net)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(P(x0, y0))
            t.SetEnd(P(x1, y1))
            t.SetWidth(MM(width))
            t.SetLayer(layer)
            t.SetNet(n)
            self.b.Add(t)

    def via(self, net, x, y, d=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(P(x, y))
        v.SetWidth(MM(d))
        v.SetDrill(MM(drill))
        v.SetNet(self.net(net))
        self.b.Add(v)

    def vias(self, net, pts):
        for x, y in pts:
            self.via(net, x, y)


def grid(x0, x1, y0, y1, pitch):
    """Via field points on a pitch (>= 0.9 mm, plan A's via-column rule), inclusive ends."""
    out = []
    nx, ny = int(round((x1 - x0) / pitch)), int(round((y1 - y0) / pitch))
    for i in range(nx + 1):
        for j in range(ny + 1):
            out.append((round(x0 + i * pitch, 3), round(y0 + j * pitch, 3)))
    return out


def copper(bd):
    """Every zone, track and via of the band."""
    # ---- In2: GND background of the band, RAW_ACT islands, BAT_IN band (D18: >= 2.5 mm plan view from live pyro
    # copper; the islands stop at y 91.6 / x 6.0 near J124.1 and at y 100.3 under R134 and J121.2)
    bd.zone('C_GND_In2_band', 'GND', In2, [(0.5, 66.8), (45.5, 66.8), (45.5, 117.5), (0.5, 117.5)], 8,
            clr=0.25, minw=0.2)
    bd.zone('C_RAW_ACT_In2_west', 'RAW_ACT', In2, [(0.5, 79.0), (16.4, 79.0), (16.4, 91.6), (6.0, 91.6), (6.0, 100.3),
                                                   (11.0, 100.3), (11.0, 108.0), (0.5, 108.0)], 12)
    bd.zone('C_RAW_ACT_In2_j122', 'RAW_ACT', In2, [(20.2, 70.5), (24.6, 70.5), (24.6, 86.4), (20.2, 86.4)], 12)
    bd.zone('C_BAT_IN_In2', 'BAT_IN', In2, [(12.4, 100.3), (45.5, 100.3), (45.5, 117.5), (12.4, 117.5)], 12)
    # ---- B.Cu
    bd.zone('C_ACT_FET_S_B', 'ACT_FET_S', B, [(9.6, 98.6), (11.4, 98.6), (11.4, 97.6), (14.78, 97.6), (14.78, 106.9), (11.9, 106.9),
                                               (11.9, 105.8), (9.6, 105.8)], 40)
    # west region with the divider notch (x 12.6-16.5, y 81.8-84.7) open to the GND fill aft of it
    bd.zone('C_RAW_ACT_B_west', 'RAW_ACT', B, [(0.5, 81.8), (12.6, 81.8), (12.6, 85.3), (16.5, 85.3), (16.5, 93.2),
                                               (7.4, 93.2), (7.4, 97.7), (9.6, 99.9), (9.6, 108.0), (0.5, 108.0)], 36)
    bd.zone('C_RAW_ACT_B_box', 'RAW_ACT', B, [(21.3, 70.9), (24.7, 70.9), (24.7, 80.35), (25.1, 80.35), (25.1, 86.9),
                                              (19.65, 86.9), (19.65, 80.35), (21.3, 80.35)], 36)
    bd.zone('C_BAT_IN_B', 'BAT_IN', B, [(15.0, 98.6), (31.0, 98.6), (31.0, 101.9), (41.3, 101.9), (41.3, 105.6),
                                        (35.2, 105.6), (35.2, 108.2), (33.4, 108.2), (33.4, 112.6), (27.8, 112.6),
                                        (27.8, 108.6), (17.0, 108.6), (17.0, 104.6), (15.0, 104.6)], 34)
    # ---- F.Cu: RAW_ACT west strip / region / bridge / J122 box, with a GND bay at C121's GND pad
    bd.zone('C_RAW_ACT_F', 'RAW_ACT', F, [(0.5, 79.6), (6.6, 79.6), (6.6, 84.8), (10.8, 84.8), (10.8, 79.6),
                                          (19.6, 79.6), (19.6, 80.35), (21.3, 80.35), (21.3, 70.9), (24.7, 70.9),
                                          (24.7, 80.35), (25.1, 80.35), (25.1, 86.3), (21.3, 86.3), (21.3, 88.0),
                                          (15.8, 88.0), (15.8, 93.1), (7.4, 93.1), (7.4, 97.7), (9.6, 99.9),
                                          (12.8, 99.9), (12.8, 108.0), (7.4, 108.0), (7.4, 109.5), (0.5, 109.5)], 36)
    bd.zone('C_BAT_IN_F', 'BAT_IN', F, [(17.0, 104.9), (22.5, 104.9), (22.5, 103.0), (27.3, 103.0), (27.3, 104.9),
                                        (33.5, 104.9), (33.5, 112.6), (27.8, 112.6), (27.8, 108.6), (17.0, 108.6)], 34)

    # ---- ACT_GATE: B.Cu bus y 107.3 (Q121.4 stub, C120.2, R120.2), via A, F.Cu hop x 13.48 (R121.1, TP121), via B,
    # Q120.4. The gates sit at opposite corners of the facing-row bridge, and In2 carries power only (D20).
    gx = PLACE['Q120'][0] - 2.9                      # 13.48: Q120's source / gate column
    q121_gate = (PLACE['Q121'][0] + 2.9, PLACE['Q121'][1] + 1.9)          # (10.9, 104.9)
    q120_gate = (gx, PLACE['Q120'][1] - 1.9)                             # (13.48, 99.82)
    bd.track('ACT_GATE', B, 0.25, [q121_gate, (q121_gate[0], 107.3), (12.5, 107.3), (gx, 107.3)])
    bd.track('ACT_GATE', B, 0.25, [(gx, 107.3), (14.3, 107.3)])
    bd.via('ACT_GATE', gx, 107.3)
    bd.track('ACT_GATE', B, 0.25, [q120_gate, (gx, 98.95)])
    bd.via('ACT_GATE', gx, 98.95)
    bd.track('ACT_GATE', F, 0.25, [(gx, 98.95), (gx, 100.85)])
    bd.track('ACT_GATE', F, 0.25, [(gx, 100.85), (gx, 103.2)])
    bd.track('ACT_GATE', F, 0.25, [(gx, 103.2), (gx, 107.3)])

    # ---- BAT_IN feed to the eFuse: TP80, R82.1, C88.1 on x 40.75, into U9.5's north end
    bd.track('BAT_IN', B, 0.5, [(40.75, 102.4), (40.75, 97.8)])
    bd.track('BAT_IN', B, 0.5, [(40.75, 97.8), (40.75, 95.2)])
    bd.track('BAT_IN', B, 0.5, [(40.75, 95.2), (40.75, 93.6)])
    bd.track('BAT_IN', B, 0.3, [(40.75, 93.6), (40.75, 91.4)])
    # switch legs
    bd.track('BAT_SW_SOURCE', B, 0.25, [(20.46, 108.725), (20.46, 110.4)])
    bd.track('BAT_SW_RETURN', B, 0.25, [(16.6, 108.725), (16.6, 109.18), (15.38, 110.4)])

    # ---- RAW_ACT_SENSE divider: MID R177.2 -> R124.1; SENSE bus y 83.66 (R125.1, R182.1, C122.1) with R124.2
    bd.track('RAW_ACT_SENSE_MID', B, 0.2, [(13.2, 85.18), (14.17, 85.18)])
    bd.track('RAW_ACT_SENSE', B, 0.2, [(13.6, 83.66), (14.6, 83.66)])
    bd.track('RAW_ACT_SENSE', B, 0.2, [(14.6, 83.66), (15.03, 83.66)])
    bd.track('RAW_ACT_SENSE', B, 0.2, [(15.03, 83.66), (15.85, 83.66)])
    bd.track('RAW_ACT_SENSE', B, 0.2, [(15.03, 85.18), (15.03, 83.66)])
    # ---- gate drive on F: ACT_DRV Q122.3 -> R121.2; ACT_EN Q122.1 -> R123.1 -> R122.2
    bd.track('ACT_DRV', F, 0.25, [(14.34, 100.85), (15.6, 100.85)])
    bd.track('ACT_EN', F, 0.25, [(17.6, 101.8), (17.6, 102.93)])
    bd.track('ACT_EN', F, 0.25, [(17.6, 102.93), (18.9, 102.93)])
    # ---- damper: BAT_DAMP C89.2 -> C95.2 -> R166.1 on y 100.675 (F)
    bd.track('BAT_DAMP', F, 0.5, [(24.0, 100.675), (26.5, 100.675)])
    bd.track('BAT_DAMP', F, 0.5, [(26.5, 100.675), (27.875, 100.675), (28.9, 101.7)])

    # ---- reservation lanes (not spike copper): the pyro exits and the RAW_ACT_SENSE lane down the B.Cu corridor
    # west of J122 (plan_partial 5.5), to y 70, so DRC measures the band against them
    bd.track('PYRO1_GATE_N', B, 0.2, [(23.0, 88.33), (18.9, 88.33), (18.4, 87.83), (18.4, 70.0)])
    bd.track('PYRO1_CONT', B, 0.2, [(28.4, 88.61), (27.39, 87.6), (19.6, 87.6), (19.0, 87.0), (19.0, 70.0)])
    bd.track('ARM1_SENSE', B, 0.2, [(18.18, 91.3), (18.18, 89.5), (17.8, 89.12), (17.8, 70.0)])
    bd.track('RAW_ACT_SENSE', B, 0.2, [(15.85, 83.66), (17.2, 83.66), (17.2, 70.0)])

    # ---- via fields (0.6 / 0.3 mm, pitch >= 1.0 mm): RAW_ACT joins F.Cu, In2 and B.Cu along the strip, at Q121's
    # drain, across the west region and in the J122 box; BAT_IN joins In2 / F.Cu to the B.Cu pour at Q120's drain
    raw = grid(1.3, 5.5, 92.8, 99.8, 1.4) + grid(1.3, 2.7, 101.2, 106.8, 1.4) + grid(4.1, 8.3, 106.8, 106.8, 1.4)
    raw += [(1.3, 85.6), (3.3, 85.6), (5.3, 85.6), (11.3, 85.6)]
    raw += [(x, 87.6) for x in (5.3, 7.3, 9.3, 11.3)]
    raw += [(x, 89.6) for x in (1.3, 3.3, 5.3, 7.3, 12.7, 14.7)]
    raw += [(x, 91.0) for x in (12.7, 14.7)]
    raw += grid(20.6, 23.4, 81.4, 85.6, 1.4)
    bd.vias('RAW_ACT', raw)
    bat = grid(17.7, 19.1, 105.6, 107.0, 1.4) + grid(22.0, 26.2, 105.6, 107.0, 1.4) + grid(21.25, 21.25, 100.9, 103.7, 1.4)
    bd.vias('BAT_IN', bat)
    # GND vias: gate-drive GND pocket on F, the damper / input-cap GND pads, the GND test pads
    bd.vias('GND', [(19.6, 104.4), (37.35, 100.6), (41.6, 100.0), (37.4, 107.6), (44.6, 104.2)])
    # reservation lanes (not spike copper) for the eFuse's low-current nets across the band, on the top-side strip
    # between the CH1 block and the damper row: BAT_ENABLE from R165.2 (via) and RAW_PROTECTED from R122.1, east to
    # x 38.5 where the eFuse network (step 6) takes them
    bd.track('BAT_ENABLE', B, 0.25, [(16.6, 107.075), (16.6, 106.0)])
    bd.via('BAT_ENABLE', 16.6, 106.0)
    bd.track('BAT_ENABLE', F, 0.25, [(16.6, 106.0), (16.6, 99.25), (38.5, 99.25)])
    bd.track('RAW_PROTECTED', F, 0.25, [(17.6, 103.79), (20.3, 103.79), (20.3, 99.75), (38.5, 99.75)])
    return bd


def main(base_dir, out_dir, fill=True):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ('m3.kicad_pro', 'm3.kicad_dru'):
        shutil.copyfile(Path(base_dir) / name, out_dir / name)
    pcbnew.KIID.SeedGenerator(8301)      # deterministic KIIDs for the new items (as the R7 stages do)
    b = pcbnew.LoadBoard(str(Path(base_dir) / 'm3.kicad_pcb'))
    for z in b.Zones():          # the base keeps R7's stale fills; connectivity would re-net new vias from them
        if not z.GetIsRuleArea():
            z.UnFill()
    bd = Band(b)
    bd.place()
    copper(bd)
    want = {(v.GetPosition().x, v.GetPosition().y): v.GetNetname() for v in b.GetTracks() if v.GetClass() == 'PCB_VIA'}
    if fill:
        b.BuildConnectivity()
        assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'fill failed'
    b.BuildConnectivity()
    moved = [(mm(v.GetPosition().x), mm(v.GetPosition().y), want[(v.GetPosition().x, v.GetPosition().y)], v.GetNetname())
             for v in b.GetTracks() if v.GetClass() == 'PCB_VIA'
             and want.get((v.GetPosition().x, v.GetPosition().y)) not in (None, v.GetNetname())]
    assert not moved, f'connectivity re-netted vias (a via sits on foreign copper): {moved}'
    pcbnew.SaveBoard(str(out_dir / 'm3.kicad_pcb'), b)
    print('saved', out_dir / 'm3.kicad_pcb')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], '--no-fill' not in sys.argv)
