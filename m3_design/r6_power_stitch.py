#!/usr/bin/env python3
"""Join the relocated actuator switches to their broad power pours.

Vias remain outside component pads. Native DRC and the filled-copper DC solve
must follow; connectivity alone does not establish current capacity.
"""
import pcbnew
import r5_maze
from r5_routes import via


def repair(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    banks = [
        ('RAW_ACT', ('RAW_ACT_B', 'R6_RAW_ACT_F'),
         [(x, y) for x in (1.1, 6.8) for y in (86.5, 87.5, 88.5, 89.5, 90.5, 91.5)]),
        ('BAT_IN', ('BAT_IN_B', 'R6_BAT_IN_In2'),
         [(x, y) for x in (1.1, 6.8) for y in (66.5, 67.5, 68.5, 69.5, 71, 72, 73)]),
    ]
    added = []
    for net, names, candidates in banks:
        zones = [z for z in board.Zones() if z.GetZoneName() in names]
        assert len(zones) == len(names), names
        count = 0
        for point in candidates:
            # These broad pours are deliberately stitched across one another's
            # layers. Refill creates antipads; final DRC and DC solving check them.
            previous = r5_maze.PLANES_AFTER
            try:
                r5_maze.PLANES_AFTER = previous | {'BAT_IN', 'RAW_ACT'}
                position = r5_maze.via_spot(board, net, point, (0, 0), r=.45)
            except RuntimeError:
                continue
            finally:
                r5_maze.PLANES_AFTER = previous
            p = pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in position))
            # A pour with no pad or via yet may be removed as an island.
            # Place inside both outlines, then check the resulting filled copper.
            if not all(z.Outline().Contains(p) for z in zones):
                continue
            via(board, net, position)
            count += 1
            added.append((net, position))
        if count < 8:
            raise RuntimeError(f'{net}: only {count} safe stitching vias; review bank placement')
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print('Actuator power stitching:', added)
    return added
