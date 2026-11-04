#!/usr/bin/env python3
"""R11 reverse hot-plug model (stage D, D-R11-74): R10's distributed model (tools/r10_hotplug.py, unchanged) run on
R11's own BAT_IN / BAT_DAMP copper, six-layer stack-up and In2 BAT_IN pour.

What differs from R10. Everything else (the 2304 required corners, the limits, the nonlinear solver and its C source,
the maker C(V) curves, the convergence, sensitivity, no-clamp, retained-output, component and C88-topology checks) is
R10's code, called unchanged.
  * Stack-up: all six copper layers (F / In1 GND / In2 power / In3 signal / In4 GND / B, D-R11-03).
  * Microstrip height: 'near' = the nearest plane layer (In1 / In2 / In4; In3 is a signal layer), 'gnd' = the nearest
    GND plane (In1 / In4). R10 used In1 / In2 and In1, the same choices on a four-layer board (Inference: under a
    B.Cu track on R11 the plane is In4).
  * The In2 BAT_IN pour. R11 joins J1.1's B.Cu trunk to D8 and the C80 / C96 / C89 / C95 bank through an In2 pour
    (R10's model refused any BAT_IN pour). The board must be zone-filled first (R11's routing leaves zones unfilled;
    r11_post fills them). The filled pour is rasterised (GRID mm) with every BAT_IN via that lands on it and every
    BAT_IN plated pad on In2 as terminals; a conjugate-gradient solve of the sheet (rho / t of In2) gives the
    terminals' conductance matrix, and its Kron reduction is an exact DC resistor network between them, which becomes
    the model's plane edges. Each plane edge's inductance is its resistance times mu0 h t / rho: the parallel-plate
    sheet inductance mu0 h per square on the same current pattern, with h the distance to In1 alone ('gnd' corners) or
    In1 and In4 in parallel ('near' corners; In2 lies between the two GND planes) (Inference: plane-pair current
    pattern, ideal return planes, no antipad or slot correction).
  * Vias that land on the pour are split at In2 into two barrel edges (F-In2, In2-B), each with R10's barrel R and L.
  * R167 is R11's 0402 line (10k 1 %, C25744, 0402WGF1002TCE, D-R11-06): same value and net roles.
  * The inputs and results are R11's files in m3_design/r11/design/.

usage: <KiCad python3> -I tools/r11_hotplug.py --extract FILLED_BOARD.kicad_pcb [--inputs OUT.json]   (pcbnew)
       <python3 with numpy> -I tools/r11_hotplug.py [--inputs IN.json] [--output OUT.json]          (simulation)
Simulation needs a C compiler (cc) for tools/r10_hotplug_solver.c, as R10's.
"""
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r10_hotplug as base                                         # noqa: E402

ROOT = HERE.parent
DESIGN = ROOT / 'm3_design/r11/design'
CU_NAMES = ('F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu')
PLANES = ('In1.Cu', 'In2.Cu', 'In4.Cu')                           # D-R11-03: In3 is the inner signal layer
GND_PLANES = ('In1.Cu', 'In4.Cu')
POUR_LAYER = 'In2.Cu'
GRID = 0.1                                                         # mm, plane raster
RHO = 1.72e-8                                                      # ohm m, as R10 (20 C)
MU0 = 4e-7 * math.pi
MODEL_PARTS = dict(base.MODEL_PARTS, R167=('10k 1%', 'C25744', '0402WGF1002TCE', ('BAT_IN', 'GND')))
KEEP = ('J1.1', 'D8.1', 'C80.1', 'C96.1', 'C89.1', 'C89.2', 'C95.1', 'C95.2', 'C88.1', 'R166.1', 'R167.1', 'U9.5')


def stackup(path):
    """{copper layer: (thickness mm, mid-plane depth mm from the top of F.Cu)} for all six copper layers, from the
    board file's (stackup ...) block (tools/dc_solve.stackup's parse, extended from four to six copper layers)."""
    text = Path(path).read_text(encoding='utf-8')
    m = re.search(r'\(stackup\b', text)
    if not m:
        raise ValueError(f'{path}: no (stackup ...) block')
    level, j = 1, m.end()
    while level and j < len(text):
        level += {'(': 1, ')': -1}.get(text[j], 0)
        j += 1
    depth, out = 0.0, {}
    for lm in re.finditer(r'\(layer\s+"([^"]+)"(.*?)\n\t\t\t\)', text[m.end():j], re.S):
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


def model_sha():
    return base.digest([base.file_sha(p) for p in (Path(base.__file__), Path(__file__), base.SOLVER, base.CAPACITORS)])


def heights(stack, layer):
    z = stack[layer][1]
    return (min(abs(z - stack[q][1]) for q in PLANES if q != layer),
            min(abs(z - stack[q][1]) for q in GND_PLANES if q != layer))


def via_edge(stack, top, bottom, drill):
    h = abs(stack[top][1] - stack[bottom][1])
    inductance = .2 * h * (math.log(4 * h / drill) + 1)
    return h, 1.72e-5 * h / (math.pi * drill * .020), inductance


def solve_cg(n, nbr, fixed, tol=1e-11, max_it=200000):
    """Potentials of an n-node conductance graph (nbr[u] = [(v, g)]) with `fixed` {node: volts}: Jacobi-preconditioned
    conjugate gradient on the free nodes (pure Python)."""
    free = [u for u in range(n) if u not in fixed]
    pos = {u: k for k, u in enumerate(free)}
    m = len(free)
    diag, rhs, rows = [0.0] * m, [0.0] * m, [[] for _ in range(m)]
    for k, u in enumerate(free):
        for v, g in nbr[u]:
            diag[k] += g
            if v in fixed:
                rhs[k] += g * fixed[v]
            else:
                rows[k].append((pos[v], g))
    x = [0.0] * m
    r = rhs[:]
    z = [r[i] / diag[i] for i in range(m)]
    p = z[:]
    rz = sum(r[i] * z[i] for i in range(m))
    norm = math.sqrt(sum(v * v for v in rhs)) or 1.0
    for it in range(max_it):
        ap = [diag[i] * p[i] - sum(g * p[j] for j, g in rows[i]) for i in range(m)]
        alpha = rz / sum(p[i] * ap[i] for i in range(m))
        for i in range(m):
            x[i] += alpha * p[i]
            r[i] -= alpha * ap[i]
        if math.sqrt(sum(v * v for v in r)) < tol * norm:
            break
        z = [r[i] / diag[i] for i in range(m)]
        rz_new = sum(r[i] * z[i] for i in range(m))
        beta = rz_new / rz
        rz = rz_new
        p = [z[i] + beta * p[i] for i in range(m)]
    else:
        raise ValueError('plane solve did not converge')
    volts = dict(fixed)
    for k, u in enumerate(free):
        volts[u] = x[k]
    return volts, it + 1


def pour_network(board, net, stack, grid=GRID):
    """(terminal labels, conductance matrix S, cells, CG iterations): the net's filled pour on POUR_LAYER reduced to its
    terminals (each via of the net on the pour, each plated pad of the net on the layer), Kron reduction by unit-voltage
    solves (Calculation on the CAD copper; sheet resistance from the stack-up)."""
    import pcbnew
    mm, MM = pcbnew.ToMM, pcbnew.FromMM
    lay = board.GetLayerID(POUR_LAYER)
    polys = [z.GetFilledPolysList(lay) for z in board.Zones()
             if not z.GetIsRuleArea() and z.GetNetname() == net and z.IsOnLayer(lay) and z.HasFilledPolysForLayer(lay)]
    if not polys:
        return [], [], 0, 0
    pads = [(f'{f.GetReference()}.{p.GetNumber()}', p) for f in board.GetFootprints() for p in f.Pads()
            if p.GetNetname() == net and p.IsOnLayer(lay)]
    vias = [v for v in board.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == net]
    box = None
    for ps in polys:
        b = ps.BBox()
        r = (mm(b.GetX()), mm(b.GetY()), mm(b.GetRight()), mm(b.GetBottom()))
        box = r if box is None else (min(box[0], r[0]), min(box[1], r[1]), max(box[2], r[2]), max(box[3], r[3]))
    x0, y0 = box[0] - grid, box[1] - grid
    nx, ny = int((box[2] - box[0]) / grid) + 3, int((box[3] - box[1]) / grid) + 3
    centre = lambda i, j: pcbnew.VECTOR2I(MM(x0 + (i + .5) * grid), MM(y0 + (j + .5) * grid))   # noqa: E731
    cells = {}
    for j in range(ny):
        for i in range(nx):
            c = centre(i, j)
            if any(ps.Contains(c) for ps in polys):
                cells[(i, j)] = len(cells)
    groups = {}
    for label, p in pads:
        ps = pcbnew.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(ps, lay, 0, MM(.005), pcbnew.ERROR_INSIDE)
        hit = {k for (i, j), k in cells.items() if ps.Contains(centre(i, j))}
        if hit:
            groups[label] = hit
    for v in vias:
        vx, vy = mm(v.GetPosition().x), mm(v.GetPosition().y)
        rad = mm(v.GetWidth(v.TopLayer())) / 2
        hit = {k for (i, j), k in cells.items()
               if math.hypot(x0 + (i + .5) * grid - vx, y0 + (j + .5) * grid - vy) <= rad}
        if hit:
            groups[f'via({round(vx, 6)},{round(vy, 6)})'] = hit
    labels = sorted(groups)
    g_sheet = stack[POUR_LAYER][0] * 1e-3 / RHO                       # S per square
    nbr = [[] for _ in cells]
    for (i, j), u in cells.items():
        for di, dj in ((1, 0), (0, 1)):
            v = cells.get((i + di, j + dj))
            if v is not None:
                nbr[u].append((v, g_sheet))
                nbr[v].append((u, g_sheet))
    S, iterations = [], 0
    for a in labels:
        fixed = {u: (1.0 if lab == a else 0.0) for lab in labels for u in groups[lab]}
        volts, it = solve_cg(len(cells), nbr, fixed)
        iterations = max(iterations, it)
        row = []
        for b in labels:
            # current leaving terminal b's cells into the free copper (positive out of a at 1 V)
            row.append(sum(g * (volts[u] - volts[v]) for u in groups[b] for v, g in nbr[u] if v not in groups[b]))
        S.append(row)
    return labels, S, len(cells), iterations


def extract(board, board_path):
    """R10's extract (r10_hotplug.extract) on six layers, with the In2 BAT_IN pour reduced to plane edges."""
    import pcbnew
    mm = pcbnew.ToMM
    point = lambda p: (round(mm(p.x), 6), round(mm(p.y), 6))           # noqa: E731
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    missing = set(base.REFS) - set(fps)
    if missing:
        raise ValueError('missing hot-plug parts: ' + ', '.join(sorted(missing)))
    stack = stackup(board_path)
    pads, parts = {}, {}
    refs = sorted(set(base.REFS) | {r for r in fps if re.fullmatch(r'C\d+', r)})
    for ref in refs:
        f = fps[ref]
        parts[ref] = dict(value=f.GetValue(), footprint=str(f.GetFPID().GetLibItemName()),
                          fields={x.GetName(): x.GetText() for x in f.GetFields()
                                  if x.GetName() in ('LCSC', 'Manufacturer', 'Manufacturer Part')},
                          pads=[dict(number=p.GetNumber(), net=p.GetNetname(), xy=point(p.GetPosition()),
                                     size=point(p.GetSize()), layers=list(p.GetLayerSet().CuStack()))
                                for p in f.Pads() if p.GetNumber()])
        for p in f.Pads():
            if p.GetNumber() and p.GetNetname() in base.NETS:
                pads.setdefault((ref, p.GetNumber()), []).append(p)
    tracks, vias = [], []
    for t in board.GetTracks():
        if t.GetNetname() not in base.NETS:
            continue
        if t.GetClass() == 'PCB_VIA':
            vias.append(dict(net=t.GetNetname(), xy=point(t.GetPosition()),
                             diameter_mm=round(mm(t.GetWidth(t.TopLayer())), 6), drill_mm=round(mm(t.GetDrillValue()), 6),
                             top=board.GetLayerName(t.TopLayer()), bottom=board.GetLayerName(t.BottomLayer())))
            continue
        if t.GetClass() != 'PCB_TRACK':
            raise ValueError('hot-plug model needs straight tracks')
        tracks.append(dict(net=t.GetNetname(), layer=board.GetLayerName(t.GetLayer()),
                           a=point(t.GetStart()), b=point(t.GetEnd()), width=round(mm(t.GetWidth()), 6)))
    tracks.sort(key=lambda t: (t['net'], t['layer'], t['a'], t['b'], t['width']))
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() not in base.NETS:
            continue
        z.CalculateFilledArea()
        if z.GetFilledArea() > 0 and (z.GetNetname() != 'BAT_IN' or
                                      [board.GetLayerName(x) for x in z.GetLayerSet().Seq()] != [POUR_LAYER]):
            raise ValueError(f'unsupported pour {z.GetNetname()} {z.GetZoneName()}: only the In2 BAT_IN pour is modelled')
    unfilled = [z.GetZoneName() for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'BAT_IN'
                and not z.HasFilledPolysForLayer(board.GetLayerID(POUR_LAYER))]
    if unfilled:
        raise ValueError(f'BAT_IN pour not filled ({unfilled}): fill the zones first (r11_post / ZONE_FILLER)')
    labels, S, ncells, iterations = pour_network(board, 'BAT_IN', stack)
    pour_vias = {lab for lab in labels if lab.startswith('via(')}
    vertices = {(t['net'], t['layer'], *p) for t in tracks for p in (t['a'], t['b'])}
    for v in vias:
        layers = (v['top'], v['bottom']) + ((POUR_LAYER,) if f'via({v["xy"][0]},{v["xy"][1]})' in pour_vias and
                                             v['net'] == 'BAT_IN' else ())
        vertices.update((v['net'], layer, *v['xy']) for layer in layers)
    parent = {p: p for p in vertices}

    def find(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    def join(a, b):
        parent[find(b)] = find(a)

    terminals = {}
    for (ref, num), pp in pads.items():
        key = ('pad', ref, 'drain' if ref == 'Q120' else num)
        parent.setdefault(key, key)
        terminals[ref + '.' + num] = key
        for p in pp:
            for v in vertices:
                if v[0] == p.GetNetname() and p.IsOnLayer(board.GetLayerID(v[1])) and \
                        p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(v[2]), pcbnew.FromMM(v[3]))):
                    join(key, v)
    edges = []
    for t in tracks:
        a, b = t['a'], t['b']
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length <= 0:
            raise ValueError('zero-length hot-plug track')
        cuts = []
        for v in vertices:
            if v[:2] != (t['net'], t['layer']):
                continue
            along = ((v[2] - a[0]) * dx + (v[3] - a[1]) * dy) / length ** 2
            cross = abs((v[2] - a[0]) * dy - (v[3] - a[1]) * dx) / length
            if -1e-6 <= along <= 1 + 1e-6 and cross < 1e-6:
                cuts.append((along, v))
        cuts.sort()
        for (ta, va), (tb, vb) in zip(cuts, cuts[1:]):
            na, nb = find(va), find(vb)
            if na == nb or tb - ta < 1e-7:
                continue
            seg = length * (tb - ta)
            w, layer = t['width'], t['layer']
            h_near, h_gnd = heights(stack, layer)
            piece = dict(layer=layer, width_mm=w, length_mm=seg, start_mm=list(va[2:]), end_mm=list(vb[2:]))
            edges.append(dict(a=na, b=nb, R_ohm=1.72e-5 * seg / (w * stack[layer][0]),
                              L_near_nH=base.microstrip_nh(w, h_near, seg),
                              L_gnd_nH=base.microstrip_nh(w, h_gnd, seg), pieces=[piece]))
    for v in vias:
        stops = [v['top'], v['bottom']]
        if (v['net'], POUR_LAYER, *v['xy']) in parent:
            stops = [v['top'], POUR_LAYER, v['bottom']]
        for top, bottom in zip(stops, stops[1:]):
            h, r, ind = via_edge(stack, top, bottom, v['drill_mm'])
            edges.append(dict(a=find((v['net'], top, *v['xy'])), b=find((v['net'], bottom, *v['xy'])),
                              R_ohm=r, L_near_nH=ind, L_gnd_nH=ind,
                              pieces=[dict(layer='via', length_mm=h, drill_mm=v['drill_mm'], xy=v['xy'],
                                           span=[top, bottom])]))
    # The pour: Kron-reduced conductances between its terminals become plane edges (R = 1/g, L = R mu0 h t / rho).
    # 'gnd': the nearest GND plane (In1) alone; 'near': In2 lies between In1 and In4, both GND, so both return in
    # parallel (h1 h2 / (h1 + h2)). The two bracket the plane-pair inductance as R10's two references bracket a track's.
    z2 = stack[POUR_LAYER][1]
    h1, h4 = (abs(z2 - stack[q][1]) for q in GND_PLANES)
    h_ret = dict(near=h1 * h4 / (h1 + h4), gnd=min(h1, h4))
    l_per_r = {k: MU0 * h * 1e-3 * stack[POUR_LAYER][0] * 1e-3 / RHO * 1e9 for k, h in h_ret.items()}   # nH / ohm
    node_of = {}
    for lab in labels:
        if lab.startswith('via('):
            x, y = (float(s) for s in lab[4:-1].split(','))
            node_of[lab] = find(('BAT_IN', POUR_LAYER, x, y))
        else:
            node_of[lab] = find(terminals[lab])
    plane = []
    for i, a in enumerate(labels):
        for j in range(i + 1, len(labels)):
            g = -(S[i][j] + S[j][i]) / 2
            if g <= 0:
                continue
            res = 1 / g
            plane.append(dict(terminals=[a, labels[j]], R_ohm=res))
            edges.append(dict(a=node_of[a], b=node_of[labels[j]], R_ohm=res, L_near_nH=res * l_per_r['near'],
                              L_gnd_nH=res * l_per_r['gnd'],
                              pieces=[dict(layer=POUR_LAYER, kind='plane', length_mm=0.0, terminals=[a, labels[j]])]))
    terminals = {k: find(v) for k, v in terminals.items()}
    keep = {terminals[k] for k in KEEP}
    while True:
        incidence = {}
        for i, e in enumerate(edges):
            for k in ('a', 'b'):
                incidence.setdefault(e[k], []).append(i)
        candidate = next((n for n, ii in incidence.items() if n not in keep and len(ii) <= 2), None)
        if candidate is None:
            break
        ii = incidence[candidate]
        if len(ii) == 2:
            x, y = (edges[i] for i in ii)
            merged = dict(a=x['b'] if x['a'] == candidate else x['a'],
                          b=y['b'] if y['a'] == candidate else y['a'], pieces=x['pieces'] + y['pieces'])
            for k in ('R_ohm', 'L_near_nH', 'L_gnd_nH'):
                merged[k] = x[k] + y[k]
            edges.append(merged)
        edges = [e for i, e in enumerate(edges) if i not in ii]
    nodes = sorted({e[k] for e in edges for k in ('a', 'b')}, key=str)
    names = {n: next((k for k, v in sorted(terminals.items()) if v == n), 'junction_' + str(i))
             for i, n in enumerate(nodes)}
    for e in edges:
        e['a'], e['b'] = names[e['a']], names[e['b']]
        e['length_mm'] = sum(p['length_mm'] for p in e['pieces'])
    pin_nodes = {k: names[v] for k, v in terminals.items() if v in names}
    absent = [k for k in KEEP if k not in pin_nodes]
    if absent:
        raise ValueError(f'hot-plug terminals not on the BAT_IN / BAT_DAMP network: {absent}')
    signature = dict(parts=parts, tracks=tracks, vias=vias, stackup=stack, pour=dict(labels=labels, S=S))
    return dict(schema=base.SCHEMA, board_sha256=base.file_sha(board_path), electrical_sha256=base.digest(signature),
                parts=parts, stackup=stack, edges=edges, terminals=pin_nodes,
                pour=dict(layer=POUR_LAYER, grid_mm=GRID, cells=ncells, cg_iterations=iterations, terminals=labels,
                          conductance_S=S, edges=plane, return_plane_h_mm=h_ret, L_per_R_nH_per_ohm=l_per_r),
                note='Inference: trace R at 20 C; microstrip L to the nearest plane / nearest GND plane; the In2 BAT_IN '
                     'pour Kron-reduced from a DC sheet solve, its L scaled by mu0 h t / rho (plane-pair Inference); '
                     'ideal pad copper and ground (R11, tools/r11_hotplug.py).')


def install():
    base.DESIGN = DESIGN
    base.INPUTS = DESIGN / 'hotplug_inputs_r11.json'
    base.RESULTS = DESIGN / 'hotplug_results_r11.json'
    base.MODEL_PARTS = MODEL_PARTS
    base.model_sha = model_sha
    base.extract = extract


if __name__ == '__main__':
    install()
    sys.argv[0] = __file__
    raise SystemExit(base.main())
