#!/usr/bin/env python3
"""DC resistance of one net's copper between two sets of pads (REQUIREMENTS F4: the servo feed at 7.7 A).

usage: <KiCad python3> tools/dc_solve.py [board] [--net RAW_ACT] [--source Q121:5,6,7,8,9] [--sink J122:2,5,8,11]
                                         [--amps 7.7] [--grid 0.1] [--png out.svg]

The board must be filled. The net's copper (zone fills, tracks and pads) on each copper layer is cut into
square cells (--grid); neighbouring cells on a layer conduct with the sheet conductance of the layer's copper
(1 oz = 35 µm on every layer, M1; resistivity 1.72e-8 Ohm m, copper at 20 °C). Each via of the net joins the
cells it sits in on the layers where the net has copper, through its barrel (0.3 mm hole, 20 µm plating,
barrel length from the stack-up below). Through-hole pads join their layers outright. The source pads are held
at one potential and the sink pads at another; the solve (conjugate gradient, Jacobi preconditioner) gives
the resistance, then the drop and the copper loss at --amps, the share each layer carries across the half-way
equipotential, and the highest current per mm of width on each layer (where the copper is the neck).
Assumptions, not measurements: plating thickness, room-temperature resistivity, no pad-to-component
resistance (the FET's and the connector's own resistance are not included).
The grid must be no larger than half the narrowest track on the net. Disconnected sampled terminals,
invalid numerical quantities or an unconverged solve return nonzero; refine the grid to check accuracy.
"""
import argparse
import math
import re
import sys

import pcbnew

mm, MM = pcbnew.ToMM, pcbnew.FromMM
RHO = 1.72e-8                        # Ohm m
T_CU = 35e-6                         # 1 oz, every layer (M1)
LAYERS = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
Z = {pcbnew.F_Cu: 0.0, pcbnew.In1_Cu: 0.245, pcbnew.In2_Cu: 1.345, pcbnew.B_Cu: 1.59}   # mm, JLC04161H-7628
VIA_HOLE, VIA_PLATE = 0.3e-3, 20e-6


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
    a = ap.parse_args()
    positive(a.amps, 'load current')
    positive(a.grid, 'grid spacing')
    b = pcbnew.LoadBoard(a.board)
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
    gs = T_CU / RHO                                  # S per square
    for (li, k), u in idx.items():
        i, j = k % nx, k // nx
        for di, dj in ((1, 0), (0, 1)):
            if i + di < nx and j + dj < ny:
                v = idx.get((li, k + di + dj * nx))
                if v is not None:
                    nbr[u].append((v, gs))
                    nbr[v].append((u, gs))
    area = math.pi * (VIA_HOLE + VIA_PLATE) * VIA_PLATE

    def cell(x, y):
        return int((x - x0) / h) + int((y - y0) / h) * nx

    for v in vias:
        k = cell(mm(v.GetPosition().x), mm(v.GetPosition().y))
        on = [(li, idx[(li, k)]) for li in range(4) if (li, k) in idx]
        for (la, ua), (lb, ub) in zip(on, on[1:]):
            gv = area / (RHO * abs(Z[LAYERS[lb]] - Z[LAYERS[la]]) * 1e-3)
            nbr[ua].append((ub, gv))
            nbr[ub].append((ua, gv))
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
    if a.png:
        _svg(a.png, V, node_xy, nbr, nx, ny, x0, y0, h, scale)
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


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, OverflowError) as error:
        print(f'DC solve: FAIL: {error}', file=sys.stderr)
        sys.exit(1)
