# freeze_signals.py routes.json board.kicad_pcb m3_design/r10_route_signals.py : write the AUTO table (KiCad python)
import json, sys, re, pcbnew
R = json.load(open(sys.argv[1])); b = pcbnew.LoadBoard(sys.argv[2]); mod = sys.argv[3]
mm = pcbnew.ToMM
centres = {}
import collections
for f in b.GetFootprints():
    cnt = collections.Counter(p.GetNumber() for p in f.Pads())
    for p in f.Pads():
        if cnt[p.GetNumber()] > 1:
            continue
        centres.setdefault((round(mm(p.GetPosition().x), 4), round(mm(p.GetPosition().y), 4), p.GetNetname()), f'{f.GetReference()}.{p.GetNumber()}')
def ref(net, pt):
    k = (round(pt[0], 4), round(pt[1], 4), net)
    for (x, y, n), r in centres.items():
        if n == net and abs(x - pt[0]) < 1e-3 and abs(y - pt[1]) < 1e-3:
            return repr(r)
    return f'({pt[0]:g}, {pt[1]:g})'
lines = ['AUTO_TRACKS = [']
for net in R:
    for l, pts, *_ in R[net]['polys']:
        lines.append(f"    ({net!r}, {l!r}, [{', '.join(ref(net, p) for p in pts)}]),")
lines.append(']')
lines.append('AUTO_VIAS = [')
for net in R:
    for v in R[net]['vias']:
        lines.append(f"    ({net!r}, ({v[0]:g}, {v[1]:g})),")
lines.append(']')
s = open(mod).read()
a = s.index('AUTO_TRACKS = ['); e = s.index('# ---- end AUTO ----')
s = s[:a] + '\n'.join(lines) + '\n' + s[e:]
open(mod, 'w').write(s)
print(sum(len(R[n]['polys']) for n in R), 'polylines', sum(len(R[n]['vias']) for n in R), 'vias')
