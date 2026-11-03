"""Native zone fill without the CLI's macOS GUI tool-manager mouse query.

Called only on an isolated project by verify_board.py. A failed fill fails the gate.
"""
import sys

import pcbnew


board = pcbnew.LoadBoard(sys.argv[1])
if board is None:
    raise RuntimeError('Cannot load board for native zone fill')
board.BuildConnectivity()
if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):
    raise RuntimeError('Native zone fill did not complete')
pcbnew.SaveBoard(sys.argv[1], board)
print('Native zone fill complete')
