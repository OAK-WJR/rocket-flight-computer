#!/usr/bin/env python3
"""DC resistance of one net's copper between two pad sets on R11's six-layer board (stage D, D-R11-73).

tools/dc_solve.py's method (square cells per copper layer at the layer's sheet conductance from the board's own
stack-up; vias and plated pads join the layers through their barrels; source pads at 1 V, sink pads at 0 V; resistance
= 1 / source current), written for all six R11 copper layers. dc_solve.py itself is R10's four-layer tool and stays
unchanged.

usage: <KiCad python3> -I tools/r11_dc_net.py FILLED_BOARD --net GND --source Q124:1,2,3 --sink J1:2
                                              [--grid 0.1] [--window X0,Y0,X1,Y1] [--plating 0.020]
The board must be zone-filled (R11's routing leaves zones unfilled; r11_post fills them). Output: the board SHA-256,
the cell count, CG iterations and the resistance (Calculation on CAD copper: resistivity 1.72e-8 ohm m at 20 C, the
stack-up's nominal copper, a 20 um barrel plating; Inference for the as-built board). The window drops copper outside
it (an upper bound on R).
"""
import argparse
import hashlib
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from r11_hotplug import CU_NAMES, RHO, solve_cg, stackup          # noqa: E402


def pad_spec(board, spec):
    ref, nums = spec.split(':')
    f = next((f for f in board.GetFootprints() if f.GetReference() == ref), None)
    if f is None:
        raise ValueError(f'no footprint {ref}')
    want = set(nums.split(','))
    pads = [p for p in f.Pads() if p.GetNumber() in want]
    if {p.GetNumber() for p in pads} != want:
        raise ValueError(f'{spec}: missing pads')
    return pads


def solve(board_path, net, source, sink, grid=0.1, window=None, plating=0.020):
    import pcbnew
    mm, MM = pcbnew.ToMM, pcbnew.FromMM
    board = pcbnew.LoadBoard(str(board_path))
    stack = stackup(board_path)
    layers = [(name, board.GetLayerID(name)) for name in CU_NAMES]
    zones = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == net]
    if any(not z.HasFilledPolysForLayer(lid) for z in zones for _, lid in layers if z.IsOnLayer(lid)):
        raise ValueError('unfilled zone on the net: fill the board first')
    tracks = [t for t in board.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_TRACK']
    if any(t.GetClass() == 'PCB_ARC' for t in board.GetTracks() if t.GetNetname() == net):
        raise ValueError('arcs are not modelled')
    vias = [t for t in board.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_VIA']
    pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
    src, snk = pad_spec(board, source), pad_spec(board, sink)
    if any(p.GetNetname() != net for p in src + snk):
        raise ValueError('terminal pads must be on the net')
    if window is None:
        bb = board.GetBoardEdgesBoundingBox()
        window = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))
    x0, y0, x1, y1 = window
    nx, ny = int((x1 - x0) / grid) + 1, int((y1 - y0) / grid) + 1
    centre = lambda i, j: (x0 + (i + .5) * grid, y0 + (j + .5) * grid)          # noqa: E731
    vec = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))                            # noqa: E731
    idx, nodes = {}, []

    def span(lo, hi, origin, count):
        return range(max(0, int((lo - origin) / grid)), min(count, int((hi - origin) / grid) + 1))
    for li, (name, lid) in enumerate(layers):
        hit = set()
        for t in tracks:
            if t.GetLayer() != lid:
                continue
            ax, ay, bx, by = mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y)
            r = mm(t.GetWidth()) / 2
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            for j in span(min(ay, by) - r, max(ay, by) + r, y0, ny):
                for i in span(min(ax, bx) - r, max(ax, bx) + r, x0, nx):
                    x, y = centre(i, j)
                    u = 0.0 if L == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L))
                    if math.hypot(x - ax - u * dx, y - ay - u * dy) <= r:
                        hit.add((i, j))
        for v in vias:
            if not v.IsOnLayer(lid):
                continue
            vx, vy, r = mm(v.GetPosition().x), mm(v.GetPosition().y), mm(v.GetWidth(lid)) / 2
            for j in span(vy - r, vy + r, y0, ny):
                for i in span(vx - r, vx + r, x0, nx):
                    if math.hypot(centre(i, j)[0] - vx, centre(i, j)[1] - vy) <= r:
                        hit.add((i, j))
        polys = [z.GetFilledPolysList(lid) for z in zones if z.IsOnLayer(lid)]
        for p in pads:
            if p.IsOnLayer(lid):
                ps = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(ps, lid, 0, MM(.005), pcbnew.ERROR_INSIDE)
                polys.append(ps)
        for ps in polys:
            if ps.OutlineCount() == 0:
                continue
            b = ps.BBox()
            for j in span(mm(b.GetY()), mm(b.GetBottom()), y0, ny):
                for i in span(mm(b.GetX()), mm(b.GetRight()), x0, nx):
                    if (i, j) not in hit and ps.Contains(vec(*centre(i, j))):
                        hit.add((i, j))
        for i, j in sorted(hit):
            idx[(li, i, j)] = len(nodes)
            nodes.append((li, i, j))
    nbr = [[] for _ in nodes]
    gs = [stack[name][0] * 1e-3 / RHO for name, _ in layers]
    for (li, i, j), u in idx.items():
        for di, dj in ((1, 0), (0, 1)):
            v = idx.get((li, i + di, j + dj))
            if v is not None:
                nbr[u].append((v, gs[li]))
                nbr[v].append((u, gs[li]))

    def cell(x, y):
        return int((x - x0) / grid), int((y - y0) / grid)

    def barrel(x, y, drill, name):
        i, j = cell(x, y)
        on = [(li, idx[(li, i, j)]) for li in range(len(layers)) if (li, i, j) in idx]
        area = math.pi * (drill + plating) * plating * 1e-6
        for (la, ua), (lb, ub) in zip(on, on[1:]):
            g = area / (RHO * abs(stack[layers[lb][0]][1] - stack[layers[la][0]][1]) * 1e-3)
            nbr[ua].append((ub, g))
            nbr[ub].append((ua, g))
        return len(on)
    for v in vias:
        barrel(mm(v.GetPosition().x), mm(v.GetPosition().y), mm(v.GetDrillValue()), 'via')
    for p in pads:
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            barrel(mm(p.GetPosition().x), mm(p.GetPosition().y), mm(p.GetDrillSize().x), 'pad')
    fixed = {}
    for group, val in ((src, 1.0), (snk, 0.0)):
        for p in group:
            sampled = False
            for li, (name, lid) in enumerate(layers):
                if not p.IsOnLayer(lid):
                    continue
                ps = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(ps, lid, 0, MM(.005), pcbnew.ERROR_INSIDE)
                for (lj, i, j), u in idx.items():
                    if lj == li and ps.Contains(vec(*centre(i, j))):
                        if fixed.get(u, val) != val:
                            raise ValueError('source and sink overlap')
                        fixed[u] = val
                        sampled = True
            if not sampled:
                raise ValueError(f'terminal pad {p.GetParentFootprint().GetReference()}.{p.GetNumber()} not sampled')
    # keep only the component joined to both terminals
    seen, todo = set(), [u for u in fixed]
    while todo:
        u = todo.pop()
        if u in seen:
            continue
        seen.add(u)
        todo.extend(v for v, _ in nbr[u])
    keep = sorted(seen)
    remap = {u: k for k, u in enumerate(keep)}
    sub = [[(remap[v], g) for v, g in nbr[u] if v in remap] for u in keep]
    fixed2 = {remap[u]: val for u, val in fixed.items()}
    if not any(v == 0.0 for v in fixed2.values()) or not any(v == 1.0 for v in fixed2.values()):
        raise ValueError('terminals not connected')
    volts, iterations = solve_cg(len(sub), sub, fixed2, tol=1e-9)
    current = sum(g * (volts[u] - volts[v]) for u, val in fixed2.items() if val == 1.0 for v, g in sub[u]
                  if fixed2.get(v) != 1.0)
    return dict(board_sha256=hashlib.sha256(Path(board_path).read_bytes()).hexdigest(), net=net, source=source,
                sink=sink, grid_mm=grid, window_mm=list(window), cells=len(sub), cg_iterations=iterations,
                resistance_ohm=1.0 / current)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board')
    ap.add_argument('--net', required=True)
    ap.add_argument('--source', required=True)
    ap.add_argument('--sink', required=True)
    ap.add_argument('--grid', type=float, default=0.1)
    ap.add_argument('--window', default=None)
    ap.add_argument('--plating', type=float, default=0.020)
    a = ap.parse_args()
    win = tuple(float(v) for v in a.window.split(',')) if a.window else None
    import json
    print(json.dumps(solve(a.board, a.net, a.source, a.sink, a.grid, win, a.plating), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
