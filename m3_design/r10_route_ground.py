"""R10 ground and plane fan-out: F.Cu / B.Cu GND pours and the frozen plane-via table (m3_design/r10_fanout.tsv).

The table was made by the design aid m3_design/r10_fanout_aid.py on the routed board (every rail pad whose island had
no via of its net gets one on the nearest legal octilinear spot) and is drawn here without search, as R9's
r9_ground.tsv was. Pours keep 0.25 mm from other nets and join GND pads by thermal spokes.

STITCH retains the frozen 0.5 / 0.3 mm GND coverage vias from D-R3-09 / R3-RTE-05. The circuit pass removes or moves
only sites obstructed by changed footprints or routes; signal families draw their required GND partners explicitly.
Final DRC, reference, connectivity and routing checks use the resulting filled board. No search runs in the build.

Last, every via keeps its pads only on the copper layers it connects (KiCad: remove unconnected layers, keep the start
and end layers), as R9's ground stage (R9_DECISIONS D-S8-19): the In1 / In2 planes then clear a via by the board's
0.25 mm hole clearance (antipad r 0.40 mm) instead of an unconnected ring plus the zone clearance (r 0.50 mm), which is
what K-reference's own-antipad allowance measures (R10_DECISIONS D-R2-10).
"""
import csv
from pathlib import Path

import pcbnew

TABLE = Path(__file__).resolve().parent / 'r10_fanout.tsv'
POUR = [(0.3, 0.3), (45.7, 0.3), (45.7, 89.7), (0.3, 89.7)]
STITCH = (
    # west-edge row (x < 6); beside the terminals at x 0.9 (ring 0.65 mm from the edge), clear of the terminal legends'
    # spots (IGN / BAT on F.Cu at y 50.5-52.3, 70.5-72.3)
    # Circuit pass: (5,9.5) removed for J420.1's new terminal pad.
    (2.0, 9.0), (4.0, 12.0), (3.5, 18.0), (0.9, 48.0), (0.9, 54.5), (0.9, 57.5), (0.9, 64.0), (0.9, 67.0),
    (0.9, 74.5), (0.9, 77.5), (0.9, 80.5),
    # B.Cu void pair below J2's bottom pin-table spot (y >= 34.68).
    # Circuit pass: (25.6,28.85) removed for SD R461.2's new 3V3 pad.
    (13.0, 32.2), (11.45, 34.0),  # moved west of the new SPI3 B.Cu diagonal corridor and its reference margin
    # a second via in the larger outer-pour islands that hung on one (F.Cu at J2, F.Cu west of U12)
    (30.0, 34.8),  # J2 shares the SPI3 return vias; its former stitch occupied the legend band.
    # R8-RTE-03 (round 8): a GND partner 1.43 mm from I2C1_SCL's layer-change via (7.75, 49.8), 1.0 mm from U5's pads
    (7.4, 51.2),
    # coverage spots
    # The relocated R110 return now covers the former (15,20.5) stitch, which entered its SMD pad.
    (8.0, 3.0), (18.0, 3.0), (25.0, 2.5), (38.0, 3.0), (43.5, 8.0), (10.5, 9.0), (16.5, 12.5),
    # Circuit pass: (36,54.5)/(16.5,78.5)/(22,23) removed for moved R89.1/R80.2/C461.2 pads.
    (7.0, 22.0), (43.0, 65.0),
    (6.5, 83.0), (33.5, 88.0),  # D400's moved return replaces the former (34.9,44.5) stitch.
)


# Circuit pass: fill slivers that cannot hold a GND via (0.39-0.47 mm strips between neighbouring tracks, or between the
# outer-most copper and the board edge) are removed as R7 / R8 did: a pour-only keep-out the piece's own outline grown
# 0.02 mm (tracks, vias and pads stay allowed).  Name prefix R8_POUR_TRIM_ is the one route_check recognises.
TRIMS = (

    ('R8_POUR_TRIM_C4', 'F', [(16.0, 28.62), (20.3, 32.92), (20.3, 33.62), (16.0, 29.32)]),       # between USB_LIMITED / USB_DM
    ('R8_POUR_TRIM_C3', 'B', [(25.3, 19.69), (25.77, 19.69), (25.77, 23.34), (25.3, 23.34)]),     # between SD_MOSI / SD_CS
)


# R18-SAF-01 / R18-GATE-01 (D-R18-04): every plated barrel of the load-switch gate drive and of the arming-switch enable
# chain keeps >= 1.0 mm (check_r10.S-8) of inner-layer copper clearance, by a fill-only rule area around it on the inner
# layers where foreign copper is hazardous: In1 GND and In2 for the P-FET gate drive (a short to GND turns Q120 / Q121
# on), In2 only for the enable chain (In1 GND holds U9 / Q122 off). The areas follow the drawn barrels; no search.
BARREL_KEEPOUT = {'ACT_GATE': ('In1', 'In2'), 'ACT_DRV': ('In1', 'In2'), 'BAT_ENABLE': ('In2',),
                  'BAT_SW_RETURN': ('In2',), 'ACT_EN': ('In2',), 'ACT_EN_MCU': ('In2',), 'PYRO1_GATE_N': ('In2',)}
BARREL_KEEPOUT_GAP = 1.05          # mm: S-8's 1.0 mm plus 0.05 mm for the fill outline
BARREL_KEEPOUT_SIDES = 16


def barrel_keepouts(d):
    """[(name, layers, centre mm, radius mm)] of the R18 barrel keep-outs, from the board's drawn vias and plated pads."""
    out = []
    barrels = []
    for v in d.board.GetTracks():
        if v.GetClass() == 'PCB_VIA' and v.GetNetname() in BARREL_KEEPOUT:
            barrels.append((v.GetNetname(), v.GetPosition(), v.GetDrillValue() / 2))
    for f in d.board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() in BARREL_KEEPOUT:
                barrels.append((p.GetNetname(), p.GetPosition(), max(p.GetDrillSize().x, p.GetDrillSize().y) / 2))
    for i, (net, at, r) in enumerate(sorted(barrels, key=lambda b: (b[0], b[1].x, b[1].y))):
        out.append((f'R18_BARREL_KEEPOUT_{net}_{i}', BARREL_KEEPOUT[net], (pcbnew.ToMM(at.x), pcbnew.ToMM(at.y)),
                    pcbnew.ToMM(r) + BARREL_KEEPOUT_GAP))
    return out


def barrel_keepout(d, name, layers, centre, radius):
    import math
    z = pcbnew.ZONE(d.board)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    for layer in layers:
        ls.AddLayer({'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu}[layer])
    z.SetLayerSet(ls)
    z.SetZoneName(name)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(False)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    rr = radius / math.cos(math.pi / BARREL_KEEPOUT_SIDES)        # circumscribed: every edge >= radius from the centre
    for k in range(BARREL_KEEPOUT_SIDES):
        a = 2 * math.pi * (k + .5) / BARREL_KEEPOUT_SIDES
        o.Append(pcbnew.FromMM(round(centre[0] + rr * math.cos(a), 4)), pcbnew.FromMM(round(centre[1] + rr * math.sin(a), 4)))
    if not d.dry:
        d.board.Add(z)


def trim(d, name, layer, pts):
    z = pcbnew.ZONE(d.board)
    z.SetIsRuleArea(True)
    z.SetLayer(pcbnew.F_Cu if layer == 'F' else pcbnew.B_Cu)
    z.SetZoneName(name)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(False)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    if not d.dry:
        d.board.Add(z)


def draw(d):
    for name, layer, pts in TRIMS:
        trim(d, name, layer, pts)
    for layer in ('F', 'B'):
        d.zone(f'R10_GND_{layer}', 'GND', layer, POUR, 0, clr=0.25, minw=0.25, conn=pcbnew.ZONE_CONNECTION_THT_THERMAL)
    with TABLE.open() as fh:
        rows = csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t')
        for r in rows:
            at = (float(r['x']), float(r['y']))
            pts = [d.pad(r['pad'], net=r['net']), at]
            if r['pad'] == 'U1.49':
                # Exit the MCU pads before turning; C421's moved bottom land excludes the old via.
                pts.insert(1, (at[0], pts[0][1]))
            d.track(r['net'], r['layer'], 0.3, pts)
            d.via(r['net'], at)
    # R405 keeps its local return after the ESD clamp moves to the other legal pocket.
    d.track('GND','B',.3,[(35.475,16.1),(35.95,15.625)])
    d.via('GND',(35.95,15.625))
    # C60 and R103 share a local return; the moved C431 has its own return in the fanout table.
    d.track('GND','F',.3,[d.pad('C60.2'),(33.2,55.0)]);d.via('GND',(33.2,55.0))
    # The camera divider and filter each have a short local return, clear of the supply via.
    d.track('GND','F',.2,[d.pad('C94.2'),(34.45,50.3),(34.85,50.7)]);d.via('GND',(34.85,50.7))
    d.track('GND','F',.2,[d.pad('R105.2'),(33.63,47.5)]);d.via('GND',(33.63,47.5))
    # Adjacent core bypasses share C23's existing return, clear of the QSPI fan.
    d.track('GND','B',.2,[d.pad('C16.2'),(26.18,36.22),d.pad('C23.2')])
    d.track('GND','B',.3,[d.pad('C91.2'),(36.65,55.375)]);d.via('GND',(36.65,55.375))
    d.track('GND','B',.3,[(32.8,52.5),(32.8,53.3)]);d.via('GND',(32.8,53.3))
    # Explicit dogleg keeps the U402 return clear of the moved VLOGIC divider.
    d.track('GND','B',.3,[d.pad('U402.2'),(31.8,59.0),(32.3,59.5)]);d.via('GND',(32.3,59.5))
    for at in STITCH:
        d.via('GND', at)
    for name, layers, centre, radius in barrel_keepouts(d):
        barrel_keepout(d, name, layers, centre, radius)
    if not d.dry:
        for v in d.board.GetTracks():
            if v.GetClass() == 'PCB_VIA':
                ps = v.Padstack()
                assert ps.UnconnectedLayerMode() == pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL
                # Inner-track endpoints need their annular pads retained during zone filling.
                inner_end = any(t.GetClass() == 'PCB_TRACK' and t.GetLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu)
                                and t.GetNetCode() == v.GetNetCode() and v.GetPosition() in (t.GetStart(), t.GetEnd())
                                for t in d.board.GetTracks())
                if not inner_end:
                    ps.SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_EXCEPT_START_AND_END)
