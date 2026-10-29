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
    (8.7, 37.75), (30.0, 34.8),  # moved off new USB_FAULT_N / USB_LIMITED trunks
    # R8-RTE-03 (round 8): a GND partner 1.43 mm from I2C1_SCL's layer-change via (7.75, 49.8), 1.0 mm from U5's pads
    (7.4, 51.2),
    # coverage spots
    # The relocated R110 return now covers the former (15,20.5) stitch, which entered its SMD pad.
    (8.0, 3.0), (18.0, 3.0), (25.0, 2.5), (38.0, 3.0), (43.5, 8.0), (10.5, 9.0), (16.5, 12.5),
    # Circuit pass: (36,54.5)/(16.5,78.5)/(22,23) removed for moved R89.1/R80.2/C461.2 pads.
    (7.0, 22.0), (30.2, 53.6), (42.5, 59.0), (43.0, 65.0), (29.5, 74.0),
    (9.0, 82.0), (6.5, 83.0), (33.5, 88.0),
)


# Circuit pass: fill slivers that cannot hold a GND via (0.39-0.47 mm strips between neighbouring tracks, or between the
# outer-most copper and the board edge) are removed as R7 / R8 did: a pour-only keep-out the piece's own outline grown
# 0.02 mm (tracks, vias and pads stay allowed).  Name prefix R8_POUR_TRIM_ is the one route_check recognises.
TRIMS = (
    ('R8_POUR_TRIM_C1', 'F', [(42.24, 39.86), (42.67, 39.86), (42.67, 53.55), (42.24, 53.55)]),   # between CAM_TX / RX_WIRE
    ('R8_POUR_TRIM_C2', 'B', [(45.0, 41.5), (45.53, 41.5), (45.53, 61.9), (45.0, 61.9)]),         # east edge strip
    ('R8_POUR_TRIM_C4', 'F', [(16.0, 28.62), (20.3, 32.92), (20.3, 33.62), (16.0, 29.32)]),       # between USB_LIMITED / USB_DM
    ('R8_POUR_TRIM_C3', 'B', [(25.3, 19.69), (25.77, 19.69), (25.77, 23.34), (25.3, 23.34)]),     # between SD_MOSI / SD_CS
)


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
            d.track(r['net'], r['layer'], 0.3, [d.pad(r['pad'], net=r['net']), at])
            d.via(r['net'], at)
    # R128.2's GND joins C127.2's via (21.3, 57.55) on F.Cu (R4-RTE-01): its own via at (18.933, 57.835) would block the
    # 3V3 tongue's corridor on In2 to D120's via
    d.track('GND', 'F', 0.3, [d.pad('R128.2', net='GND'), (21.815, 57.835), (22.1, 57.55)])
    for at in STITCH:
        d.via('GND', at)
    if not d.dry:
        for v in d.board.GetTracks():
            if v.GetClass() == 'PCB_VIA':
                ps = v.Padstack()
                assert ps.UnconnectedLayerMode() == pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL
                ps.SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_EXCEPT_START_AND_END)
