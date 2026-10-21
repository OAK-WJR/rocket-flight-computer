"""Dump U1's pad nets of a board to JSON (pin -> net, '' for no net). Usage: KICAD_PY dump_r7_u1.py BOARD OUT.json"""
import json, sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
u = b.FindFootprintByReference('U1')
d = {int(p.GetNumber()): ('' if p.GetNetname().startswith('unconnected-') else p.GetNetname()) for p in u.Pads()}
json.dump(d, open(sys.argv[2], 'w'), indent=0)
print(len(d), 'pins')
