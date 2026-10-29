import pcbnew, sys, csv
board, table, basis = sys.argv[1], sys.argv[2], sys.argv[3]
b = pcbnew.LoadBoard(board); mm = pcbnew.ToMM
pos = {f.GetReference(): (round(mm(f.GetPosition().x), 3), round(mm(f.GetPosition().y), 3),
                          round(f.GetOrientationDegrees(), 3), 'B' if f.IsFlipped() else 'F') for f in b.GetFootprints()}
lines = open(table).read().split('\n'); out = []; n = 0
for line in lines:
    t = line.split('\t')
    if len(t) >= 6 and t[0] in pos:
        x, y, r, s = pos[t[0]]
        ox, oy, orr = float(t[1]), float(t[2]), float(t[3])
        if abs(ox - x) > 1e-3 or abs(oy - y) > 1e-3 or abs(((orr - r + 180) % 360) - 180) > 1e-3 or t[4] != s:
            t = [t[0], f'{x:g}', f'{y:g}', f'{r:g}', s, basis]; n += 1
        line = '\t'.join(t)
    out.append(line)
open(table, 'w').write('\n'.join(out)); print(n, 'rows updated')
