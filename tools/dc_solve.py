#!/usr/bin/env python3
"""DC resistance of one net's copper between two sets of pads (REQUIREMENTS F4: the servo feed at 7.7 A).

usage: <KiCad python3> tools/dc_solve.py [board] [--net RAW_ACT] [--source Q121:5,6,7,8,9] [--sink J122:2,5,8,11]
                                         [--amps 7.7] [--grid 0.1] [--png out.svg] [--necks [--max-rise C]]
                                         [--window X0,Y0,X1,Y1] [--via-currents N]

The first output line names the board file and its SHA-256, so a recorded solve is bound to the copper it solved
(REQUIREMENTS F4; fix pass 1, R8P1-INTEGRITY-02).

The board must be filled. The net's copper (zone fills, tracks and pads) on each copper layer is cut into
square cells (--grid); neighbouring cells on a layer conduct with the sheet conductance of that layer's copper,
read from the board's own stack-up (the (stackup ...) block of the .kicad_pcb: each copper layer's thickness and the
dielectrics between them; the ordered JLC041611-7628 stack is 35 µm outer, 30 µm inner copper, M1; resistivity
1.72e-8 Ohm m, copper at 20 °C). Each via of the net joins the cells it sits in on the layers where the net has
copper, through its barrel (0.3 mm hole, 20 µm plating; barrel length = the stack-up distance between the two copper
layers' mid-planes). Only vias join layers: a through-hole pad that is not a terminal is rasterised on each layer but
not linked across them (pessimistic; terminal pads are held at their potential on every layer). The source pads are held
at one potential and the sink pads at another; the solve (conjugate gradient, Jacobi preconditioner) gives
the resistance, then the drop and the copper loss at --amps, the share each layer carries across the half-way
equipotential, and the highest current per mm of width on each layer (where the copper is the neck).
Assumptions, not measurements: plating thickness, room-temperature resistivity, no pad-to-component
resistance (the FET's and the connector's own resistance are not included).
--necks (R8 step 1; the R8 survey's dc_neck.py, the fix-pass-7 equipotential-cut analysis, now here) also cuts the
solved potential at 377 equipotentials between 3 and 97 % of the drop (marching squares on each layer) and reports
the narrowest cut, the neck: its length on the layer that carries most of the current, scaled by the whole current
over that layer's share (an equivalent single-layer width), where it is, and its IPC-2152 rise at --amps (ipc2152.py:
no plane credit, an upper bound). --max-rise fails the run when that rise exceeds it (R8_DECISIONS D12: 20 C for
RAW_ACT and BAT_IN, 30 C for ACT_FET_S; tools/run_dc.sh passes them).
--window (fix pass 1, R8P1-POWER-01) keeps only the net's copper inside the box (board mm): a large net such as GND is
solved over the region its current crosses (the servo return, J122's GND pins to J1.2: tools/run_dc.sh), the copper
outside it treated as absent (an upper bound on R). --via-currents N prints the N largest via barrel currents at --amps
(each via link's g x dV), the per-via figure MARGIN_PRESCRIPTION P1-9 asks for.
The grid must be no larger than half the narrowest track on the net. Disconnected sampled terminals,
invalid numerical quantities or an unconverged solve return nonzero; refine the grid to check accuracy.
"""
import argparse
import hashlib
import math
import re
import sys

import pcbnew

mm, MM = pcbnew.ToMM, pcbnew.FromMM
RHO = 1.72e-8                        # Ohm m
LAYERS = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
CU_NAMES = ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')
VIA_HOLE, VIA_PLATE = 0.3e-3, 20e-6


def stackup(path):
    """The board's copper stack from its file: {copper layer name: (thickness mm, mid-plane depth mm from the top of
    F.Cu)}, from the (stackup ...) block (pcbnew's Python API does not expose the stack-up). Every layer of the block
    with a thickness counts toward the depth except the solder masks (outside the copper). Raises ValueError when the
    block or a copper thickness is missing: no default stack is assumed."""
    text = open(path, encoding='utf-8').read()
    m = re.search(r'\(stackup\b', text)
    if not m:
        raise ValueError(f'{path}: no (stackup ...) block; set the board stack-up first')
    depth, i, out = 0.0, m.end(), {}
    level, j = 1, m.end()
    while level and j < len(text):                 # the block's extent: balanced parentheses
        level += {'(': 1, ')': -1}.get(text[j], 0)
        j += 1
    for lm in re.finditer(r'\(layer\s+"([^"]+)"(.*?)\n\t\t\t\)', text[i:j], re.S):
        name, body = lm.group(1), lm.group(2)
        t = re.search(r'\(thickness\s+([\d.]+)\)', body)
        kind = re.search(r'\(type\s+"([^"]+)"\)', body)
        if not t or (kind and 'Mask' in kind.group(1)):
            continue
        th = float(t.group(1))
        if name in CU_NAMES:
            out[name] = (th, depth + th / 2)
        depth += th
    missing = [n for n in CU_NAMES if n not in out]
    if missing:
        raise ValueError(f'{path}: stack-up has no thickness for {missing}')
    return out


def pad_poly(p, lay):
    """The pad's copper on a layer as a polygon set (PAD.HitTest can abort outside the KiCad GUI)."""
    ps = pcbnew.SHAPE_POLY_SET()
    p.TransformShapeToPolygon(ps, lay, 0, MM(0.005), pcbnew.ERROR_INSIDE)
    return ps


def parse_pads(b, spec):
    try:
        ref, nums = spec.split(':')
    except ValueError:
        raise ValueError(f'invalid pad specification {spec!r}; expected REF:pin,pin')
    f = b.FindFootprintByReference(ref)
    if f is None:
        raise ValueError(f'footprint {ref} is absent')
    want = set(nums.split(','))
    pads = [p for p in f.Pads() if p.GetNumber() in want]
    if not all(want) or len(pads) != len(want):
        raise ValueError(f'{spec}: requested pads do not match {[p.GetNumber() for p in pads]}')
    return pads


def positive(value, name):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be finite and positive (got {value!r})')
    return value


def check_grid(grid, widths):
    positive(grid, 'grid spacing')
    if widths:
        narrowest = min(positive(w, 'track width') for w in widths)
        if grid > narrowest / 2 + 1e-9:
            raise ValueError(f'grid {grid:g} mm cannot resolve {narrowest:g} mm tracks; '
                             f'use --grid {narrowest / 2:g} or finer')


def connected_nodes(neighbours, fixed):
    """Require a copper path between the equipotential source and sink terminals."""
    sources = {u for u, voltage in fixed.items() if voltage == 1.0}
    sinks = {u for u, voltage in fixed.items() if voltage == 0.0}
    if not sources or not sinks:
        raise ValueError('source and sink must both have sampled copper cells')
    seen, stack = set(sources), list(sources)
    while stack:
        u = stack.pop()
        for v, conductance in neighbours[u]:
            positive(conductance, 'edge conductance')
            if v not in seen:
                seen.add(v)
                stack.append(v)
    if not sinks.intersection(seen):
        raise ValueError('source and sink are disconnected in the sampled copper; '
                         'check routing and refine the grid')
    # Retain the original boundary-attached domain, including zero-current
    # branches; islands touching neither terminal do not enter the matrix.
    stack = list(set(fixed) - seen)
    seen.update(fixed)
    while stack:
        u = stack.pop()
        for v, conductance in neighbours[u]:
            positive(conductance, 'edge conductance')
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def solve_cg(diag, rows, rhs, tolerance=1e-10, max_iterations=20000):
    """Jacobi-preconditioned CG, with explicit true-residual convergence evidence."""
    m = len(diag)
    if len(rows) != m or len(rhs) != m:
        raise ValueError('inconsistent matrix dimensions')
    positive(tolerance, 'CG tolerance')
    if max_iterations <= 0:
        raise ValueError('CG iteration limit must be positive')
    for value in diag:
        positive(value, 'matrix diagonal')
    if any(not math.isfinite(value) for value in rhs):
        raise ValueError('nonfinite matrix right-hand side')
    for row in rows:
        for q, conductance in row:
            if not 0 <= q < m:
                raise ValueError('matrix column outside its domain')
            positive(conductance, 'matrix conductance')
    if not m:
        return [], 0, 0.0

    def mat(vec):
        return [diag[k] * vec[k] - sum(g * vec[q] for q, g in rows[k]) for k in range(m)]

    def norm(vec):
        result = math.sqrt(sum(v * v for v in vec))
        if not math.isfinite(result):
            raise ValueError('nonfinite CG residual')
        return result

    x = [0.5] * m
    r = [rhs[k] - y for k, y in enumerate(mat(x))]
    r0 = norm(rhs) or 1.0
    if norm(r) <= tolerance * r0:
        return x, 0, norm(r) / r0
    z = [r[k] / diag[k] for k in range(m)]
    p = z[:]
    rz = positive(sum(r[k] * z[k] for k in range(m)), 'CG residual product')
    for it in range(max_iterations):
        Ap = mat(p)
        denominator = positive(sum(p[k] * Ap[k] for k in range(m)), 'CG curvature')
        alpha = positive(rz / denominator, 'CG step')
        for k in range(m):
            x[k] += alpha * p[k]
            r[k] -= alpha * Ap[k]
        if any(not math.isfinite(v) for v in x):
            raise ValueError('nonfinite CG potential')
        if norm(r) <= tolerance * r0:
            # A recurrence can accumulate roundoff; certify against A*x itself.
            r = [rhs[k] - y for k, y in enumerate(mat(x))]
            residual = norm(r) / r0
            if residual <= tolerance:
                return x, it + 1, residual
            z = [r[k] / diag[k] for k in range(m)]
            p = z[:]
            rz = positive(sum(r[k] * z[k] for k in range(m)), 'CG residual product')
            continue
        z = [r[k] / diag[k] for k in range(m)]
        rz2 = positive(sum(r[k] * z[k] for k in range(m)), 'CG residual product')
        beta = positive(rz2 / rz, 'CG direction update')
        rz = rz2
        p = [z[k] + beta * p[k] for k in range(m)]
    residual = norm([rhs[k] - y for k, y in enumerate(mat(x))]) / r0
    raise ValueError(f'CG did not converge after {max_iterations} iterations '
                     f'(relative residual {residual:.3g}, limit {tolerance:g})')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board', nargs='?', default='m3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--net', default='RAW_ACT')
    ap.add_argument('--source', default='Q121:5,6,7,8,9')
    ap.add_argument('--sink', default='J122:2,5,8,11')
    ap.add_argument('--amps', type=float, default=7.7)
    ap.add_argument('--grid', type=float, default=0.1)
    ap.add_argument('--png', default=None, help='SVG map of current density (A/mm), all layers')
    ap.add_argument('--necks', action='store_true', help='equipotential-cut neck analysis with its IPC-2152 rise')
    ap.add_argument('--max-rise', type=float, default=None, help='with --necks: fail when the neck rises more (C)')
    ap.add_argument('--window', default=None, help='X0,Y0,X1,Y1 (mm): solve only the copper inside this box')
    ap.add_argument('--via-currents', type=int, default=0, help='print the N largest via barrel currents at --amps')
    a = ap.parse_args()
    positive(a.amps, 'load current')
    positive(a.grid, 'grid spacing')
    with open(a.board, 'rb') as fh:
        print(f'board {a.board} sha256 {hashlib.sha256(fh.read()).hexdigest()}')
    win = None
    if a.window:
        win = tuple(float(v) for v in a.window.split(','))
        if len(win) != 4 or not (win[0] < win[2] and win[1] < win[3]):
            raise ValueError(f'invalid --window {a.window!r}; expected X0,Y0,X1,Y1 with X0 < X1, Y0 < Y1')
    b = pcbnew.LoadBoard(a.board)
    stack = stackup(a.board)
    T_CU = {lay: stack[n][0] * 1e-3 for lay, n in zip(LAYERS, CU_NAMES)}        # m
    Z = {lay: stack[n][1] for lay, n in zip(LAYERS, CU_NAMES)}                  # mm
    h = a.grid
    net = a.net
    # --- copper cells per layer
    zones = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == net]
    tracks = [t for t in b.GetTracks() if t.GetNetname() == net and t.GetClass() != 'PCB_VIA']
    vias = [t for t in b.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_VIA']
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
    check_grid(h, [mm(t.GetWidth()) for t in tracks])
    terminals = [(parse_pads(b, spec), value) for spec, value in ((a.source, 1.0), (a.sink, 0.0))]
    if any(p.GetNetname() != net for group, _ in terminals for p in group):
        raise ValueError(f'all source and sink pads must belong to {net}')
    ext = []
    for it in zones + tracks + vias + pads:
        r = it.GetBoundingBox()
        ext.append((mm(r.GetX()), mm(r.GetY()), mm(r.GetRight()), mm(r.GetBottom())))
    if not ext:
        raise ValueError(f'net {net!r} has no copper')
    bx = (min(e[0] for e in ext), min(e[1] for e in ext), max(e[2] for e in ext), max(e[3] for e in ext))
    if win:
        bx = (max(bx[0], win[0]), max(bx[1], win[1]), min(bx[2], win[2]), min(bx[3], win[3]))
        positive(bx[2] - bx[0], 'window width on the net')
        positive(bx[3] - bx[1], 'window height on the net')
    x0, y0 = bx[0] - h, bx[1] - h
    nx, ny = int((bx[2] - bx[0]) / h) + 3, int((bx[3] - bx[1]) / h) + 3
    cu = {}
    for lay in LAYERS:
        g = bytearray(nx * ny)
        polys = [z.GetFilledPolysList(lay) for z in zones if z.IsOnLayer(lay)]
        for ps in polys:
            pb = ps.BBox()
            i0, i1 = max(0, int((mm(pb.GetX()) - x0) / h)), min(nx - 1, int((mm(pb.GetRight()) - x0) / h) + 1)
            j0, j1 = max(0, int((mm(pb.GetY()) - y0) / h)), min(ny - 1, int((mm(pb.GetBottom()) - y0) / h) + 1)
            for j in range(j0, j1 + 1):
                y = y0 + (j + 0.5) * h
                for i in range(i0, i1 + 1):
                    if not g[j * nx + i] and ps.Contains(pcbnew.VECTOR2I(MM(x0 + (i + 0.5) * h), MM(y))):
                        g[j * nx + i] = 1
        for t in tracks:
            if t.GetLayer() != lay:
                continue
            ax, ay, cx, cy = mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y)
            r = mm(t.GetWidth()) / 2
            for j in range(max(0, int((min(ay, cy) - r - y0) / h)), min(ny, int((max(ay, cy) + r - y0) / h) + 1)):
                for i in range(max(0, int((min(ax, cx) - r - x0) / h)), min(nx, int((max(ax, cx) + r - x0) / h) + 1)):
                    px, py = x0 + (i + 0.5) * h, y0 + (j + 0.5) * h
                    dx, dy = cx - ax, cy - ay
                    L = dx * dx + dy * dy
                    s = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
                    if math.hypot(px - ax - s * dx, py - ay - s * dy) <= r:
                        g[j * nx + i] = 1
        for p in pads:
            if not p.IsOnLayer(lay):
                continue
            pb, pp = p.GetBoundingBox(), pad_poly(p, lay)
            for j in range(max(0, int((mm(pb.GetY()) - y0) / h)), min(ny, int((mm(pb.GetBottom()) - y0) / h) + 1)):
                for i in range(max(0, int((mm(pb.GetX()) - x0) / h)), min(nx, int((mm(pb.GetRight()) - x0) / h) + 1)):
                    if pp.Contains(pcbnew.VECTOR2I(MM(x0 + (i + 0.5) * h), MM(y0 + (j + 0.5) * h))):
                        g[j * nx + i] = 1
        cu[lay] = g
    if win:                                       # cells whose centre lies outside the window carry no copper
        for lay in LAYERS:
            g = cu[lay]
            for j in range(ny):
                y = y0 + (j + 0.5) * h
                for i in range(nx):
                    x = x0 + (i + 0.5) * h
                    if g[j * nx + i] and not (win[0] <= x <= win[2] and win[1] <= y <= win[3]):
                        g[j * nx + i] = 0
    # --- nodes
    idx, node_xy = {}, []
    for li, lay in enumerate(LAYERS):
        g = cu[lay]
        for k in range(nx * ny):
            if g[k]:
                idx[(li, k)] = len(node_xy)
                node_xy.append((li, k))
    n = len(node_xy)
    nbr = [[] for _ in range(n)]
    gs = [T_CU[lay] / RHO for lay in LAYERS]         # S per square, per layer
    for (li, k), u in idx.items():
        i, j = k % nx, k // nx
        for di, dj in ((1, 0), (0, 1)):
            if i + di < nx and j + dj < ny:
                v = idx.get((li, k + di + dj * nx))
                if v is not None:
                    nbr[u].append((v, gs[li]))
                    nbr[v].append((u, gs[li]))
    area = math.pi * (VIA_HOLE + VIA_PLATE) * VIA_PLATE

    def cell(x, y):
        return int((x - x0) / h) + int((y - y0) / h) * nx

    via_links = []                                # (via position, upper node, lower node, conductance)
    for v in vias:
        vx, vy = mm(v.GetPosition().x), mm(v.GetPosition().y)
        if not (x0 <= vx < x0 + nx * h and y0 <= vy < y0 + ny * h):
            continue                              # outside the (windowed) grid
        k = cell(vx, vy)
        on = [(li, idx[(li, k)]) for li in range(4) if (li, k) in idx]
        for (la, ua), (lb, ub) in zip(on, on[1:]):
            gv = area / (RHO * abs(Z[LAYERS[lb]] - Z[LAYERS[la]]) * 1e-3)
            nbr[ua].append((ub, gv))
            nbr[ub].append((ua, gv))
            via_links.append(((round(vx, 3), round(vy, 3)), ua, ub, gv, f'{CU_NAMES[la]}-{CU_NAMES[lb]}'))
    # --- boundary: every cell of the source pads (all their layers) at 1 V, sink pads at 0 V
    fixed = {}
    for group, val in terminals:
        for p in group:
            sampled = False
            pb = p.GetBoundingBox()
            for li, lay in enumerate(LAYERS):
                if not p.IsOnLayer(lay):
                    continue
                pp = pad_poly(p, lay)
                for j in range(max(0, int((mm(pb.GetY()) - y0) / h)), min(ny, int((mm(pb.GetBottom()) - y0) / h) + 1)):
                    for i in range(max(0, int((mm(pb.GetX()) - x0) / h)), min(nx, int((mm(pb.GetRight()) - x0) / h) + 1)):
                        if pp.Contains(pcbnew.VECTOR2I(MM(x0 + (i + 0.5) * h), MM(y0 + (j + 0.5) * h))):
                            u = idx.get((li, j * nx + i))
                            if u is not None:
                                if u in fixed and fixed[u] != val:
                                    raise ValueError('source and sink overlap in the sampled copper')
                                fixed[u] = val
                                sampled = True
            if not sampled:
                raise ValueError(f'terminal pad {p.GetNumber()} has no sampled copper; refine the grid')
    seen = connected_nodes(nbr, fixed)
    free = [u for u in range(n) if u in seen and u not in fixed]
    pos = {u: k for k, u in enumerate(free)}
    m = len(free)
    diag = [0.0] * m
    rhs = [0.0] * m
    rows = [[] for _ in range(m)]
    for k, u in enumerate(free):
        for v, g in nbr[u]:
            diag[k] += g
            if v in fixed:
                rhs[k] += g * fixed[v]
            elif v in pos:
                rows[k].append((pos[v], g))
    # A x = rhs, A = diag - offdiag; preserve the existing copper network.
    x, iterations, residual = solve_cg(diag, rows, rhs)
    V = dict(fixed)
    for k, u in enumerate(free):
        V[u] = x[k]
    if any(not math.isfinite(v) or v < -1e-6 or v > 1 + 1e-6 for v in V.values()):
        raise ValueError('solved potentials violate the passive 0..1 V boundary')
    # current out of the source
    I = sum(g * (V[u] - V[v]) for u in fixed if fixed[u] == 1.0 for v, g in nbr[u] if v in V and not (v in fixed and fixed[v] == 1.0))
    positive(I, 'source current')
    sink_current = sum(g * (V[v] - V[u]) for u in fixed if fixed[u] == 0.0
                       for v, g in nbr[u] if v in V and not (v in fixed and fixed[v] == 0.0))
    positive(sink_current, 'sink current')
    if abs(I - sink_current) > 1e-6 * max(I, sink_current):
        raise ValueError(f'source/sink current imbalance: {I:g} A vs {sink_current:g} A')
    R = positive(1.0 / I, 'resistance')
    scale = positive(a.amps * R, 'voltage drop')        # volts at the source for a.amps
    positive(a.amps ** 2 * R, 'copper loss')
    print(f'{net}: {a.source} -> {a.sink}, grid {h} mm, {m} free cells, CG {iterations} iterations, residual {residual:.2g}')
    print('  stack-up: ' + ', '.join(f'{n} {stack[n][0] * 1000:.0f} um at {stack[n][1]:.4f} mm' for n in CU_NAMES))
    print(f'  R = {R * 1e3:.2f} mOhm; at {a.amps} A: drop {a.amps * R * 1e3:.1f} mV, copper loss {a.amps ** 2 * R:.3f} W')
    # layer share across the half-way equipotential (current crossing V = 0.5)
    share = [0.0] * 4
    jmax = [(0.0, None)] * 4
    for u in V:
        li, k = node_xy[u]
        for v, g in nbr[u]:
            if v <= u or v not in V:
                continue
            lv, kv = node_xy[v]
            if lv != li:
                continue
            cur = g * (V[u] - V[v]) * scale           # amps through this cell edge
            if (V[u] - 0.5) * (V[v] - 0.5) < 0:
                share[li] += abs(cur)
            dens = abs(cur) / h
            if dens > jmax[li][0]:
                i, j = k % nx, k // nx
                jmax[li] = (dens, (round(x0 + (i + 0.5) * h, 2), round(y0 + (j + 0.5) * h, 2)))
    tot = sum(share) or 1.0
    for li, lay in enumerate(LAYERS):
        if jmax[li][1] is None:
            continue
        print(f'  {pcbnew.LayerName(lay):6s} carries {100 * share[li] / tot:4.0f} % at mid-path; '
              f'peak {jmax[li][0]:.2f} A/mm at {jmax[li][1]}')
    if a.via_currents:
        per_via = {}
        for p, ua, ub, gv, span in via_links:
            if ua in V and ub in V:
                cur = abs(gv * (V[ua] - V[ub]) * scale)
                if cur > per_via.get(p, (0.0, ''))[0]:
                    per_via[p] = (cur, span)
        top = sorted(((c, p, s) for p, (c, s) in per_via.items()), reverse=True)
        print(f'  vias: {len(per_via)} carry current; largest barrel currents at {a.amps} A: '
              + ', '.join(f'{c:.2f} A at {p} ({s})' for c, p, s in top[:a.via_currents]))
        print(f'  vias over 0.5 A: {sum(1 for c, _, _ in top if c > 0.5)}; over 1.0 A: {sum(1 for c, _, _ in top if c > 1.0)}')
    if a.png:
        _svg(a.png, V, node_xy, nbr, nx, ny, x0, y0, h, scale)
    if a.necks:
        neck = cuts(V, node_xy, nbr, nx, ny, x0, y0, h, scale, a.amps, idx)
        sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
        import ipc2152                                          # noqa: E402 (beside this file; run with -I)
        dt = ipc2152.ipc_dt(neck[0], neck[2], a.amps)
        w20 = ipc2152.ipc_width(20.0, neck[2], a.amps)
        print(f'  IPC-2152 (no plane credit): neck {neck[0]:.2f} mm on {neck[2]} rises {dt:.1f} C at {a.amps} A; '
              f'20 C needs {w20:.2f} mm there')
        if a.max_rise is not None:
            if dt > a.max_rise:
                print(f'  NECK FAIL: {dt:.1f} C exceeds {a.max_rise:g} C (R8_DECISIONS D12)')
                return 1
            print(f'  neck OK: {dt:.1f} C <= {a.max_rise:g} C (R8_DECISIONS D12)')
    return 0


def _svg(path, V, node_xy, nbr, nx, ny, x0, y0, h, scale):
    """Current density per cell (A/mm), one panel per layer, red = high."""
    dens = {}
    for u in V:
        li, k = node_xy[u]
        s = 0.0
        for v, g in nbr[u]:
            if v in V and node_xy[v][0] == li:
                s = max(s, abs(g * (V[u] - V[v]) * scale) / h)
        dens[u] = s
    top = max(dens.values()) or 1.0
    px = 4
    W = nx * px
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{4 * W + 30}" height="{ny * px + 20}" style="background:white">']
    for u, d in dens.items():
        li, k = node_xy[u]
        i, j = k % nx, k // nx
        c = min(1.0, d / top)
        col = f'rgb({int(255 * c)},{int(200 * (1 - c))},{int(255 * (1 - c))})'
        out.append(f'<rect x="{li * (W + 10) + i * px}" y="{j * px + 20}" width="{px}" height="{px}" fill="{col}"/>')
    for li, nm in enumerate(('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')):
        out.append(f'<text x="{li * (W + 10) + 4}" y="14" font-size="14">{nm} (peak {top:.1f} A/mm red)</text>')
    out.append('</svg>')
    open(path, 'w').write('\n'.join(out))


def cuts(V, node_xy, nbr, nx, ny, x0, y0, h, scale, amps, idx, nlev=377):
    """Equipotential cuts (marching squares per layer) between 3 and 97 % of the drop: at each level the copper cut
    length on each layer and the current crossing it; the equivalent width = the main layer's length scaled by the
    whole current over that layer's share. Prints the neck (narrowest cut), where, and the median cut."""
    import statistics
    names = ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')
    val = {}
    for u, v in V.items():
        val[node_xy[u]] = v
    levels = [0.03 + 0.94 * k / (nlev - 1) for k in range(nlev)]
    res = []
    # current crossing per layer per level: edges whose ends straddle the level
    edges = []
    for u in V:
        li, k = node_xy[u]
        for v, g in nbr[u]:
            if v <= u or v not in V or node_xy[v][0] != li:
                continue
            edges.append((li, V[u], V[v], abs(g * (V[u] - V[v]) * scale)))
    squares = []
    for (li, k), v00 in val.items():
        i, j = k % nx, k // nx
        if i + 1 >= nx or j + 1 >= ny:
            continue
        v10 = val.get((li, k + 1)); v01 = val.get((li, k + nx)); v11 = val.get((li, k + nx + 1))
        if v10 is None or v01 is None or v11 is None:
            continue
        squares.append((li, i, j, v00, v10, v11, v01))
    for t in levels:
        L = [0.0] * 4
        I = [0.0] * 4
        mid = [[] for _ in range(4)]
        for li, a, b, c in edges:
            if (a - t) * (b - t) < 0:
                I[li] += c
        for li, i, j, a, b, c, d in squares:
            # corners (0,0)=a (1,0)=b (1,1)=c (0,1)=d
            pts = []
            for (p, q, P0, P1) in ((a, b, (0, 0), (1, 0)), (b, c, (1, 0), (1, 1)), (c, d, (1, 1), (0, 1)), (d, a, (0, 1), (0, 0))):
                if (p - t) * (q - t) < 0:
                    f = (t - p) / (q - p)
                    pts.append((P0[0] + f * (P1[0] - P0[0]), P0[1] + f * (P1[1] - P0[1])))
            if len(pts) == 2:
                L[li] += h * math.dist(pts[0], pts[1])
                mid[li].append((x0 + (i + 1) * h, y0 + (j + 1) * h))
            elif len(pts) == 4:
                L[li] += h * (math.dist(pts[0], pts[1]) + math.dist(pts[2], pts[3]))
        tot = sum(I) or 1.0
        main = max(range(4), key=lambda q: I[q])
        W = L[main] * tot / I[main] if I[main] else 0.0
        box = None
        if mid[main]:
            xs = [p[0] for p in mid[main]]; ys = [p[1] for p in mid[main]]
            box = (round(min(xs), 2), round(max(xs), 2), round(min(ys), 2), round(max(ys), 2))
        res.append((W, t, names[main], round(100 * I[main] / tot), box, [round(x, 2) for x in L]))
    tiny = [r for r in res if sum(r[5]) < 1.0]          # a contour round a via field next to a terminal, not a section
    if tiny:
        print(f'  cuts: {len(tiny)} levels with < 1 mm of cut on every layer together (via-field contours by a terminal, '
              f'not counted): {[(round(r[0], 2), round(r[1], 3), r[4]) for r in sorted(tiny)[:3]]}')
    res = [r for r in res if sum(r[5]) >= 1.0]
    ws = sorted(r[0] for r in res)
    neck = min(res)
    print(f'  cuts: neck {neck[0]:.2f} mm at level {neck[1]:.3f} on {neck[2]} ({neck[3]} % of the current), cut box {neck[4]}, '
          f'per-layer length {neck[5]}')
    print(f'  cuts: median {statistics.median(ws):.2f} mm; below 1.1x neck: {sum(1 for w in ws if w < 1.1 * neck[0])} of {len(ws)} levels; '
          f'5 narrowest: {[(round(r[0], 2), round(r[1], 3), r[4]) for r in sorted(res)[:5]]}')
    return neck


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, OverflowError) as error:
        print(f'DC solve: FAIL: {error}', file=sys.stderr)
        sys.exit(1)
