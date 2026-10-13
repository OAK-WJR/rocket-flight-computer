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
    ref, nums = spec.split(':')
    f = b.FindFootprintByReference(ref)
    assert f is not None, ref
    want = set(nums.split(','))
    pads = [p for p in f.Pads() if p.GetNumber() in want]
    assert len(pads) == len(want), (spec, [p.GetNumber() for p in pads])
    return pads


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
    b = pcbnew.LoadBoard(a.board)
    h = a.grid
    net = a.net
    # --- copper cells per layer
    zones = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == net]
    tracks = [t for t in b.GetTracks() if t.GetNetname() == net and t.GetClass() != 'PCB_VIA']
    vias = [t for t in b.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_VIA']
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
    ext = []
    for it in zones + tracks + vias + pads:
        r = it.GetBoundingBox()
        ext.append((mm(r.GetX()), mm(r.GetY()), mm(r.GetRight()), mm(r.GetBottom())))
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
    for spec, val in ((a.source, 1.0), (a.sink, 0.0)):
        for p in parse_pads(b, spec):
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
                                fixed[u] = val
    assert any(v == 1.0 for v in fixed.values()) and any(v == 0.0 for v in fixed.values()), 'pads not on the copper'
    # --- connected part only (copper islands that touch neither end are dropped)
    seen = set(fixed)
    stack = list(fixed)
    while stack:
        u = stack.pop()
        for v, _ in nbr[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
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
    # A x = rhs, A = diag - offdiag (symmetric positive definite); Jacobi-preconditioned CG
    x = [0.5] * m

    def mat(vec):
        return [diag[k] * vec[k] - sum(g * vec[q] for q, g in rows[k]) for k in range(m)]
    r = [rhs[k] - y for k, y in enumerate(mat(x))]
    z = [r[k] / diag[k] for k in range(m)]
    p = z[:]
    rz = sum(r[k] * z[k] for k in range(m))
    r0 = math.sqrt(sum(v * v for v in rhs)) or 1.0
    for it in range(20000):
        Ap = mat(p)
        alpha = rz / sum(p[k] * Ap[k] for k in range(m))
        for k in range(m):
            x[k] += alpha * p[k]
            r[k] -= alpha * Ap[k]
        res = math.sqrt(sum(v * v for v in r))
        if res < 1e-10 * r0:
            break
        z = [r[k] / diag[k] for k in range(m)]
        rz2 = sum(r[k] * z[k] for k in range(m))
        beta = rz2 / rz
        rz = rz2
        p = [z[k] + beta * p[k] for k in range(m)]
    V = dict(fixed)
    for k, u in enumerate(free):
        V[u] = x[k]
    # current out of the source
    I = sum(g * (V[u] - V[v]) for u in fixed if fixed[u] == 1.0 for v, g in nbr[u] if v in V and not (v in fixed and fixed[v] == 1.0))
    R = 1.0 / I
    scale = a.amps * R                               # volts at the source for a.amps
    print(f'{net}: {a.source} -> {a.sink}, grid {h} mm, {m} free cells, CG {it + 1} iterations')
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
    sys.exit(main())
