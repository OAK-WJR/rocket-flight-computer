"""R10 ground and plane fan-out: F.Cu / B.Cu GND pours and the frozen plane-via table (m3_design/r10_fanout.tsv).

The table was made by the design aid m3_design/r10_fanout_aid.py on the routed board (every rail pad whose island had
no via of its net gets one on the nearest legal octilinear spot) and is drawn here without search, as R9's
r9_ground.tsv was. Pours keep 0.25 mm from other nets and join GND pads by thermal spokes.

STITCH (R10_DECISIONS D-R3-09, R3-RTE-05) adds GND stitching vias (0.5 / 0.3 mm, no track), frozen: a west-edge row
(x 0.9-5.0, between the supports' 4.05 mm via keep-outs, clear of J3's / J2's / the terminals' courtyards and of the
terminal legends' spots); two vias in each pour void the review found (F.Cu x 23.6-27.2, y 27.1-32.3; B.Cu x 11.3-21.3,
y 31.8-37.5, there clear of TP82's designator spot); a second via in the two larger F.Cu islands that hung on one GND
via (beside J2, west of U12); and the spots a greedy design-aid pass chose to cut the outer GND fill farther than 4 mm
(straight line) from any GND via or plated GND hole (raster 0.4 mm; a legal spot: the via ring inside the F.Cu and B.Cu
GND fill or 0.3 mm clear of other copper, 0.25 mm from pads (0.15 mm GND), its hole 0.3 mm from other holes, the ring
0.5 mm inside the edge, 4.05 mm from every M3 support, outside every courtyard, >= 2.0 mm from any signal via (room for
the signal family's GND partners), on In2 a rail plane >= 1.2 mm wide round it and 0.45 mm + half a width from every
critical B.Cu track (K-reference)). No search runs in the build.

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
    # spots (ARM / IGN / BAT on F.Cu at y 50.5-52.3, 60.5-62.3, 70.5-72.3; the J124 / J1 notes on B.Cu from x 1.18)
    (2.0, 9.0), (5.0, 9.5), (4.0, 12.0), (3.5, 18.0), (0.9, 48.0), (0.9, 54.5), (0.9, 57.5), (0.9, 64.0), (0.9, 67.0),
    (0.9, 74.5), (0.9, 77.5), (0.9, 80.5),
    # the two pour voids of the review (F.Cu, B.Cu), and a second via in the B.Cu one (the F.Cu void's second via is the
    # signal family's GPS control GND partner at (25.7, 30.6))
    (25.6, 28.85), (13.5, 33.0), (12.4, 34.0),       # B.Cu void pair below J2's bottom pin-table spot (y >= 34.68)
    # a second via in the larger outer-pour islands that hung on one (F.Cu at J2, F.Cu west of U12)
    (9.05, 37.75), (30.0, 34.4),
    # coverage spots
    (8.0, 3.0), (18.0, 3.0), (25.0, 2.5), (38.0, 3.0), (43.5, 8.0), (10.5, 9.0), (16.5, 12.5), (15.0, 20.5),
    (7.0, 22.0), (22.0, 23.0), (30.0, 55.0), (36.0, 54.5), (42.5, 59.0), (43.0, 65.0), (29.5, 74.0),
    (16.5, 78.5), (9.0, 82.0), (6.5, 83.0), (33.5, 88.0),
)


def draw(d):
    for layer in ('F', 'B'):
        d.zone(f'R10_GND_{layer}', 'GND', layer, POUR, 0, clr=0.25, minw=0.25, conn=pcbnew.ZONE_CONNECTION_THT_THERMAL)
    with TABLE.open() as fh:
        rows = csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t')
        for r in rows:
            at = (float(r['x']), float(r['y']))
            d.track(r['net'], r['layer'], 0.3, [d.pad(r['pad'], net=r['net']), at])
            d.via(r['net'], at)
    for at in STITCH:
        d.via('GND', at)
    if not d.dry:
        for v in d.board.GetTracks():
            if v.GetClass() == 'PCB_VIA':
                ps = v.Padstack()
                assert ps.UnconnectedLayerMode() == pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL
                ps.SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_EXCEPT_START_AND_END)
