#!/usr/bin/env python3
"""Compare the offline probe catalog to actual R10 native pads; no hardware access."""
import argparse
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnostics.r10_offline import Profile
from diagnostics.r10_swd import binding as swd_binding


def check(board_path):
    profile = Profile(board=board_path)
    debug = swd_binding(board_path)
    points = dict(profile.points)
    points.update({p['point_id']: dict(p, frame=debug['coordinate_frame'])
                   for p in debug['connector'].values()})
    board = pcbnew.LoadBoard(str(board_path))
    footprints = list(board.GetFootprints())
    pads = [pad for fp in footprints for pad in fp.Pads()]
    if (len(footprints), len(pads)) != (profile.data['native_footprints'], profile.data['native_pads']):
        raise ValueError('Native footprint/pad inventory differs from the diagnostic profile')
    for key, point in points.items():
        found = [pad for fp in footprints if fp.GetReference() == point['reference']
                 for pad in fp.Pads() if pad.GetNumber() == point['pad']]
        if len(found) != 1:
            raise ValueError('Missing or ambiguous native pad: ' + key)
        pad = found[0]
        xy = [pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)]
        side = board.GetLayerName(pad.GetParentFootprint().GetLayer())
        if (point['point_id'] != key or point['net'] != pad.GetNetname() or
                point['side'] != side or
                any(abs(a - b) > 1e-6 for a, b in zip(point['xy_mm'], xy)) or
                point['frame'] != profile.data['coordinate_frame']):
            raise ValueError('Native diagnostic pad/net/side/XY/frame mismatch: ' + key)
    print('R10 diagnostic profile: %d native points match; board bytes verified; no hardware tested' %
          len(points))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    try:
        check(parser.parse_args().board)
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')
