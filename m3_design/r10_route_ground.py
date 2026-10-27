"""R10 ground and plane fan-out: F.Cu / B.Cu GND pours and the frozen plane-via table (m3_design/r10_fanout.tsv).

The table was made by the design aid m3_design/r10_fanout_aid.py on the routed board (every rail pad whose island had
no via of its net gets one on the nearest legal octilinear spot) and is drawn here without search, as R9's
r9_ground.tsv was. Pours keep 0.25 mm from other nets and join GND pads by thermal spokes.

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


def draw(d):
    for layer in ('F', 'B'):
        d.zone(f'R10_GND_{layer}', 'GND', layer, POUR, 0, clr=0.25, minw=0.25, conn=pcbnew.ZONE_CONNECTION_THT_THERMAL)
    with TABLE.open() as fh:
        rows = csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t')
        for r in rows:
            at = (float(r['x']), float(r['y']))
            d.track(r['net'], r['layer'], 0.3, [d.pad(r['pad'], net=r['net']), at])
            d.via(r['net'], at)
    if not d.dry:
        for v in d.board.GetTracks():
            if v.GetClass() == 'PCB_VIA':
                ps = v.Padstack()
                assert ps.UnconnectedLayerMode() == pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL
                ps.SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_EXCEPT_START_AND_END)
