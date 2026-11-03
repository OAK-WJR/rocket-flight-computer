#!/usr/bin/env python3
"""Remove conflicting copper after placement changes, for explicit rerouting.

Consumes a fresh native DRC report. Never edits rules, pads or exclusions.
The resulting board is intentionally unconnected until the routing pass.
"""
import argparse
import json
from pathlib import Path

import pcbnew

COPPER = {'clearance', 'shorting_items', 'tracks_crossing', 'hole_clearance',
          'hole_to_hole', 'solder_mask_bridge', 'copper_edge_clearance'}


def remove_conflicts(board, report):
    tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    remove = set()
    for violation in report['violations']:
        if violation['type'] not in COPPER:
            continue
        candidates = [tracks[i['uuid']] for i in violation['items'] if i['uuid'] in tracks]
        if not candidates or any(t.m_Uuid.AsString() in remove for t in candidates):
            continue
        # Stitching vias are replaceable; preserve signal conductors where possible.
        candidates.sort(key=lambda t: (t.GetNetname() != 'GND', t.IsLocked(),
                                       t.GetClass() != 'PCB_VIA'))
        remove.add(candidates[0].m_Uuid.AsString())
    removed = []
    for key in sorted(remove):
        item = tracks[key]
        removed.append({'uuid': key, 'net': item.GetNetname(), 'type': item.GetClass()})
        board.Delete(item)
    board.BuildConnectivity()
    return removed


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board', type=Path)
    ap.add_argument('drc', type=Path)
    args = ap.parse_args()
    board = pcbnew.LoadBoard(str(args.board))
    changes = remove_conflicts(board, json.loads(args.drc.read_text()))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(args.board), board, True)
    print(f'Removed {len(changes)} conflicting tracks/vias; rerouting required')
