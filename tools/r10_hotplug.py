#!/usr/bin/env python3
"""R10 distributed reverse hot-plug model with original maker C(V) data.

Extract with KiCad Python; simulate with Python + numpy. No CAD is changed. See
sources/r10_design/hotplug.md for the circuit, limits and model limitations.
"""
import argparse
import hashlib
import itertools
import json
import math
import re
from pathlib import Path
import sys
import ctypes
import subprocess
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / 'm3_design/assembly_review/sources/r10_design'
INPUTS = DESIGN / 'hotplug_inputs.json'
RESULTS = DESIGN / 'hotplug_results.json'
CAPACITORS = DESIGN / 'hotplug_capacitors.json'
SOLVER = Path(__file__).with_name('r10_hotplug_solver.c')
REFS = ('J1', 'D8', 'C80', 'C96', 'C89', 'C95', 'C88', 'R166', 'R167', 'U9', 'Q120', 'R92')
NETS = ('BAT_IN', 'BAT_DAMP')
LIMITS = {'minimum_V': -15.0, 'maximum_V': 28.0, 'falling_V_per_us': 10.0, 'rising_V_per_us': 100.0}
CONVERGENCE_LIMITS = {'minimum_V': .002, 'maximum_V': .002, 'falling_V_per_us': .01, 'rising_V_per_us': .01}
SCHEMA = 3
SENSITIVITY_STEP = .025
SENSITIVITY_US = .5
# The numerical model cannot silently qualify a substituted capacitor/resistor after re-extraction.
MODEL_PARTS = {
    'C80': ('10uF 50V X5R 10%', 'C13585', 'CL31A106KBHNNNE', ('BAT_IN', 'GND')),
    'C96': ('10uF 50V X5R 10%', 'C13585', 'CL31A106KBHNNNE', ('BAT_IN', 'GND')),
    'C89': ('22uF 25V X5R 10%', 'C12891', 'CL31A226KAHNNNE', ('BAT_IN', 'BAT_DAMP')),
    'C95': ('22uF 25V X5R 10%', 'C12891', 'CL31A226KAHNNNE', ('BAT_IN', 'BAT_DAMP')),
    'C88': ('100nF 50V', 'C307331', 'CL05B104KB54PNC', ('BAT_IN', 'GND')),
    'D8': ('SMBJ12CA', 'C83849', 'SMBJ12CA', ('BAT_IN', 'GND')),
    'R166': ('0.36R 1% 2512', 'C168925', '25121WF360LT4E', ('BAT_DAMP', 'GND')),
    'R167': ('10k 1%', 'C25804', '0603WAF1002T5E', ('BAT_IN', 'GND')),
    'R92': ('3.3k 1%', 'C22978', '0603WAF3301T5E', ('RAW_PROTECTED', 'GND')),
}
# Known BOM inventory: nominal microfarads and order code. The discharge envelope below deliberately
# uses +20% for every MLCC, including the +/-5% and +/-10% parts, and +15% for X5R/X7R/C0G alike.
DISCHARGE_PARTS = {
    '0603B103K500NT': (.01, 'C57112'), 'CC0603KRX7R9BB104': (.1, 'C14663'),
    'CL05B103KB5NNNC': (.01, 'C15195'), 'CL05B104KB54PNC': (.1, 'C307331'),
    'CL05C100JB5NNNC': (.00001, 'C32949'), 'CL10A105KB8NNNC': (1., 'C15849'),
    'CL10A225KO8NNNC': (2.2, 'C23630'), 'CL10A475KO8NNNC': (4.7, 'C19666'),
    'CL10B105KA8NNNC': (1., 'C29936'), 'CL10B224KA8NNNC': (.22, 'C21120'),
    'CL10B474KA8NNNC': (.47, 'C1623'), 'CL21A226MAQNNNE': (22., 'C45783'),
    'CL31A106KBHNNNE': (10., 'C13585'), 'CL31A226KAHNNNE': (22., 'C12891'),
    'CL31B105KBHNNNE': (1., 'C1848'), 'GCJ188R71H104KA12D': (.1, 'C161115'),
    'GRM1885C1H472JA01D': (.0047, 'C85980'), 'GRM32ER71E226KE15L': (22., 'C21397'),
    'MA25V470M8x10': (470., 'C46550466'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def model_sha():
    return digest([file_sha(p) for p in (Path(__file__), SOLVER, CAPACITORS)])


def microstrip_nh(w, h, length):
    """R8's microstrip estimate, extended to w/h < 1; dimensions mm, result nH (Inference)."""
    u = w / h
    # Z0 sqrt(eps_eff) / c; the effective permittivity cancels in L per unit length.
    z = 60 * math.log(8 / u + u / 4) if u < 1 else 120 * math.pi / (u + 1.393 + .667 * math.log(u + 1.444))
    return z / 299792458.0 * length * 1e6


def extract(board, board_path):
    """Read actual tracks/pads; join through the physical pads and collapse degree-two track nodes."""
    import pcbnew
    from dc_solve import stackup
    mm = pcbnew.ToMM
    point = lambda p: (round(mm(p.x), 6), round(mm(p.y), 6))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    missing = set(REFS) - set(fps)
    if missing:
        raise ValueError('missing hot-plug parts: ' + ', '.join(sorted(missing)))
    stack = stackup(board_path)
    pads, parts = {}, {}
    # All capacitor identities, values and net roles bind the conservative retained-output inventory.
    refs = sorted(set(REFS) | {r for r in fps if re.fullmatch(r'C\d+', r)})
    for ref in refs:
        f = fps[ref]
        parts[ref] = dict(value=f.GetValue(), footprint=str(f.GetFPID().GetLibItemName()),
                          fields={x.GetName(): x.GetText() for x in f.GetFields()
                                  if x.GetName() in ('LCSC', 'Manufacturer', 'Manufacturer Part')},
                          pads=[dict(number=p.GetNumber(), net=p.GetNetname(), xy=point(p.GetPosition()),
                                     size=point(p.GetSize()), layers=list(p.GetLayerSet().CuStack()))
                                for p in f.Pads() if p.GetNumber()])
        for p in f.Pads():
            if p.GetNumber() and p.GetNetname() in NETS:
                pads.setdefault((ref, p.GetNumber()), []).append(p)
    tracks, vias = [], []
    for t in board.GetTracks():
        if t.GetNetname() not in NETS:
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
    if any(z.GetNetname() in NETS and z.GetFilledArea() > 0 for z in board.Zones()):
        raise ValueError('hot-plug track extraction does not model BAT_IN/BAT_DAMP pours')
    # Endpoint union through pads. Q120's BAT_IN drain pads overlap on the PCB; pad copper is ideal here.
    vertices = {(t['net'], t['layer'], *p) for t in tracks for p in (t['a'], t['b'])}
    for v in vias:
        vertices.update((v['net'], layer, *v['xy']) for layer in (v['top'], v['bottom']))
    parent = {p: p for p in vertices}

    def find(p):
        if parent[p] != p:
            parent[p] = find(parent[p])
        return parent[p]

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
            l = length * (tb - ta)
            w, layer = t['width'], t['layer']
            h_gnd = abs(stack[layer][1] - stack['In1.Cu'][1])
            h_near = min(abs(stack[layer][1] - stack[inner][1]) for inner in ('In1.Cu', 'In2.Cu'))
            piece = dict(layer=layer, width_mm=w, length_mm=l,
                         start_mm=list(va[2:]), end_mm=list(vb[2:]))
            edges.append(dict(a=na, b=nb, R_ohm=1.72e-5 * l / (w * stack[layer][0]),
                              L_near_nH=microstrip_nh(w, h_near, l),
                              L_gnd_nH=microstrip_nh(w, h_gnd, l), pieces=[piece]))
    for v in vias:
        h = abs(stack[v['top']][1] - stack[v['bottom']][1])
        drill = v['drill_mm']
        inductance = .2 * h * (math.log(4 * h / drill) + 1)
        edges.append(dict(a=find((v['net'], v['top'], *v['xy'])),
                          b=find((v['net'], v['bottom'], *v['xy'])),
                          R_ohm=1.72e-5 * h / (math.pi * drill * .020),
                          L_near_nH=inductance, L_gnd_nH=inductance,
                          pieces=[dict(layer='via', length_mm=h, drill_mm=drill, xy=v['xy'])]))
    terminals = {k: find(v) for k, v in terminals.items()}
    keep = {terminals[k] for k in ('J1.1', 'D8.1', 'C80.1', 'C96.1', 'C89.1', 'C89.2',
                                  'C95.1', 'C95.2', 'C88.1', 'R166.1', 'R167.1', 'U9.5')}
    # Remove open-ended measurement/control branches, then combine only series copper (never component terminals).
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
    signature = dict(parts=parts, tracks=tracks, vias=vias, stackup=stack)
    return dict(schema=SCHEMA, board_sha256=file_sha(board_path), electrical_sha256=digest(signature),
                parts=parts, stackup=stack, edges=edges, terminals=pin_nodes,
                note='Inference: trace R at 20 C; microstrip L with nearest plane / In1 GND brackets; ideal pad copper and ground.')


def linear_cases():
    keys = ('lh_uH', 'rh_ohm', 'cap_scale', 'cb_nF', 'vbr_V', 'reference')
    values = ((.1, .5, 1., 2.), (0., .01, .03, .1), ('derated', 'nominal'), (50., 100.),
              (12.65, 13.3, 14.7), ('near', 'gnd'))
    return [dict(zip(keys, row)) for row in itertools.product(*values)]


def cases():
    keys = ('lh_uH', 'rh_ohm', 'bulk', 'damper', 'bypass', 'vbr_V', 'reference', 'rdamp_ohm', 'copper_r_scale')
    # UNI-ROYAL SMD-SP-001 V10: +/-1%, +/-800 ppm/C below 1 ohm; 65 C from 25 to -40 C.
    rdamp = tuple(round(.36 * tolerance * (1 + temperature), 10)
                  for tolerance, temperature in ((.99, -.0008 * 65), (1.01, .0008 * 65)))
    values = ((.1, .5, 1., 2.), (.03, .1), ('low', 'high'), ('low', 'high'), ('low', 'high'),
              (12.4, 14.7, 15.6), ('near', 'gnd'), rdamp, (.75, 1., 1.3))
    return [dict(zip(keys, row)) for row in itertools.product(*values)]


def component_issues(inputs):
    issues = []
    for ref, (value, code, part, nets) in MODEL_PARTS.items():
        item = inputs.get('parts', {}).get(ref, {})
        fields = item.get('fields', {})
        roles = {p['number']: p['net'] for p in item.get('pads', [])}
        if item.get('value') != value or fields.get('LCSC') != code or fields.get('Manufacturer Part') != part or \
                any(roles.get(str(i)) != net for i, net in enumerate(nets, 1)):
            issues.append('unsupported model component or net role: ' + ref)
    u9 = inputs.get('parts', {}).get('U9', {})
    if u9.get('fields', {}).get('Manufacturer Part') != 'TPS259470LRPWR' or \
            {p['number']: p['net'] for p in u9.get('pads', [])}.get('6') != 'RAW_PROTECTED':
        issues.append('unsupported U9 or OUT net role')
    return issues


def retained_output(inputs):
    """Conservative common-node discharge sensitivity, not a manufacturer capacitance guarantee."""
    inventory = {}
    for ref, item in inputs['parts'].items():
        if not re.fullmatch(r'C\d+', ref):
            continue
        match = re.match(r'([\d.]+)([pnu])F(?:\s|$)', item['value'])
        if not match:
            raise ValueError('unsupported discharge capacitor value: ' + ref)
        nominal = float(match[1]) * {'p': 1e-12, 'n': 1e-9, 'u': 1e-6}[match[2]]
        fields = item.get('fields', {})
        expected = DISCHARGE_PARTS.get(fields.get('Manufacturer Part'))
        if expected is None or fields.get('LCSC') != expected[1] or not math.isclose(nominal, expected[0] * 1e-6):
            raise ValueError('unsupported discharge capacitor identity/value: ' + ref)
        inventory[ref] = nominal * (2. if fields['Manufacturer Part'] == 'MA25V470M8x10' else 1.2 * 1.15)
    c84 = inputs['parts'].get('C84', {})
    if c84.get('value') != '470uF 25V polymer' or \
            c84.get('fields', {}).get('Manufacturer Part') != 'MA25V470M8x10' or \
            {p['number']: p['net'] for p in c84.get('pads', [])} != {'1': 'VLOGIC', '2': 'GND'}:
        raise ValueError('unsupported C84 discharge model')
    capacitance = sum(inventory.values())
    resistance = 3300 * 1.01 * (1 + 100e-6 * 65)
    voltage = 8.5 * math.exp(-2 / (resistance * capacitance))
    return dict(capacitance_F=capacitance, inventory_F=inventory, R92_max_ohm=resistance,
                initial_V=8.5, time_s=2., output_bound_V=voltage,
                cold_input_minimum_V=max(-15., voltage - 21.),
                inference='All board capacitors share one 8.5V node: C84 twice nominal, others +20% tolerance and +15% temperature. '
                          'No operating-load or divider-discharge credit; no U11 reverse-blocking credit. '
                          'Capacitor sharing and the doubled C84 envelope are inference, requiring bench verification.')


def curves():
    """Recover the maker's numerical graph data; charge is the integral of differential C(V)."""
    import numpy as np
    data = json.loads(CAPACITORS.read_text())
    ns = np.zeros(3, dtype=np.int32)
    xs, cs, qs = (np.zeros((3, 160), dtype=np.float64) for _ in range(3))
    factors = []
    for i, part in enumerate(('CL31A106KBHNNN', 'CL31A226KAHNNN', 'CL05B104KB54PN')):
        item = data[part]
        temperature = []
        for graph in item['graphs']:
            p = graph['selectPartsList'][0]
            curve = p['chartList'][0]
            x, y = np.array([(float(d['x']), float(d['y'])) for d in curve['data']]).T
            order = np.argsort(x); x, y = x[order], y[order]
            if graph['graphType'] == 'DCBias':
                n = len(x); ns[i] = n; xs[i, :n] = x; cs[i, :n] = 1 + y / 100
                qs[i, 1:n] = np.cumsum(np.diff(x) * (cs[i, 1:n] + cs[i, :n-1]) / 2)
            else:
                ratio = (1 + y / 100) / (1 + np.interp(25, x, y) / 100)
                temperatures = np.r_[[-40, 85], x[(x >= -40) & (x <= 85)]]
                temperature.extend(np.interp(temperatures, x, ratio))
        factors.append(dict(part=part, low=.9 * min(temperature), high=1.1 * max(temperature),
                            basis='Independent +/-10% tolerance and envelope of normalized biased/unbiased TCC, -40..85C; Inference'))
    return ns, xs, cs, qs, factors


def run_nonlinear(inputs, corners, step_scale=1., end_us=150.):
    import numpy as np
    if not math.isfinite(step_scale) or step_scale <= 0 or not math.isfinite(end_us) or end_us <= 0:
        raise ValueError('invalid integration step or duration')
    frozen = model_sha()
    pins, model_edges, nodes, index = network(inputs)
    branches = [(e['a'], e['b'], e) for e in model_edges] + [('PACK', pins['J1.1'], None)]
    n, m = len(nodes), len(branches)
    E = np.zeros((m, n)); CE = np.zeros((6, n))
    for j, (a, b, _) in enumerate(branches):
        if a != 'PACK': E[j, index[a]] = 1
        E[j, index[b]] -= 1
    for j, (a, b) in enumerate((('C80.1', None), ('C96.1', None), ('C89.1', 'C89.2'),
                                ('C95.1', 'C95.2'), ('C88.1', None))):
        CE[j, index[pins[a]]] = 1
        if b: CE[j, index[pins[b]]] -= 1
    CE[5, index[pins['U9.5']]] = 1
    ns, xs, cs, qs, factors = curves()
    # Optional U9 input-capacitance sensitivity, not a TI-specified capacitance or guaranteed bound.
    ns = np.r_[ns, np.int32(2)].astype(np.int32)
    constant_x = np.zeros((1, 160)); constant_x[0, 1] = 1000.
    xs, cs, qs = np.vstack((xs, constant_x)), np.vstack((cs, np.ones((1, 160)))), np.vstack((qs, constant_x))
    ptr = lambda a: a.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    rows = []
    with tempfile.TemporaryDirectory(prefix='r10_hotplug_') as tmp:
        library = Path(tmp) / 'solver.so'
        subprocess.run(['cc', '-O2', '-shared', '-fPIC', str(SOLVER), '-o', str(library)], check=True,
                       capture_output=True, text=True)
        lib = ctypes.CDLL(str(library))
        for corner in corners:
            R, L = np.zeros(m), np.zeros(m)
            for j, (_, _, e) in enumerate(branches):
                if e:
                    R[j], L[j] = e['R_ohm'] * corner.get('copper_r_scale', 1.), e['L_' + corner['reference'] + '_nH'] * 1e-9
                else:
                    R[j], L[j] = corner['rh_ohm'], corner['lh_uH'] * 1e-6
            scale = np.array([factors[0][corner['bulk']] * 10e-6] * 2 +
                             [factors[1][corner['damper']] * 22e-6] * 2 +
                             [factors[2][corner['bypass']] * 100e-9, corner.get('input_cap_pF', 0.) * 1e-12])
            edge = corner.get('contact_edge_ns', 0.)
            if not all(np.isfinite(x).all() for x in (R, L, scale)) or (R < 0).any() or (L <= 0).any():
                raise ValueError('non-finite or invalid circuit parameters')
            if (scale < 0).any() or not isinstance(edge, (int, float)) or not math.isfinite(edge) or edge < 0:
                raise ValueError('invalid input-capacitance or contact-edge sensitivity')
            V = np.full(n, 2.); out = np.zeros(8)
            for pin in ('C89.2', 'C95.2', 'R166.1'): V[index[pins[pin]]] = 0.
            code = lib.hotplug(n, m, ptr(E), ptr(CE), ptr(R), ptr(L),
                               ns.ctypes.data_as(ctypes.POINTER(ctypes.c_int)), ptr(xs), ptr(cs), ptr(qs), ptr(scale),
                               ptr(V), index[pins['D8.1']], index[pins['U9.5']], index[pins['R166.1']],
                               index[pins['R167.1']], ctypes.c_double(corner['vbr_V']),
                               ctypes.c_double(corner['rdamp_ohm']), ctypes.c_double(edge), ctypes.c_double(step_scale),
                               ctypes.c_double(end_us), ptr(out))
            if code: raise ValueError('nonlinear solver failure ' + str(code) + ': ' + str(corner))
            rows.append(dict(corner=corner, **dict(zip(('minimum_V', 'maximum_V', 'falling_V_per_us',
                                                       'rising_V_per_us', 'falling_peak_us',
                                                       'falling_peak_voltage_V', 'damper_peak_W',
                                                       'damper_energy_J'), map(float, out)))))
    if frozen != model_sha():
        raise ValueError('model sources changed during simulation')
    return rows


def network(inputs):
    pins = dict(inputs['terminals'])
    model_edges = [dict(e) for e in inputs['edges']]
    nodes = sorted({e[k] for e in model_edges for k in ('a', 'b')})
    index = {n: i for i, n in enumerate(nodes)}
    return pins, model_edges, nodes, index


def topology_issues(inputs):
    """C88 must intercept the feed before U9; retain every local trace rather than shorting the bypass path."""
    try:
        pins, edges, _, _ = network(inputs)
        cap, u9 = pins['C88.1'], pins['U9.5']
    except (KeyError, TypeError, ValueError):
        return ['missing input-feed topology']
    adjacency = {}
    for e in edges:
        adjacency.setdefault(e['a'], []).append(e['b'])
        adjacency.setdefault(e['b'], []).append(e['a'])
    # Removing C88's node must leave only U9 and the intervening local trace, with no upstream drive.
    todo, reached = [u9], set()
    while todo:
        node = todo.pop()
        if node in reached or node == cap:
            continue
        reached.add(node)
        todo.extend(adjacency.get(node, ()))
    if cap != u9 and not any(cap in adjacency.get(node, ()) for node in reached):
        return ['C88 disconnected from U9']
    if any(node in reached for pin, node in pins.items() if pin not in ('C88.1', 'U9.5')):
        return ['U9 has an input feed that bypasses C88']
    local = [e for e in edges if e['a'] in reached or e['b'] in reached]
    issues = []
    # Centreline bounds include trace inside ideal pad copper; no such inductance is dropped or contracted.
    for key, bound in (('length_mm', 4.), ('R_ohm', .005), ('L_near_nH', 2.6), ('L_gnd_nH', 2.6)):
        values = [e.get(key) for e in local]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0
               for v in values) or sum(values) > bound:
            issues.append('C88 local bypass path exceeds qualified ' + key)
    return issues


def run(inputs, corners, dt_ns=1., end_us=150., topology='board'):
    """Trapezoidal MNA with scalar implicit solution of R8's soft-knee TVS; all cases together."""
    import numpy as np
    ncase = len(corners)
    pins, model_edges, nodes, index = network(inputs)
    nn, dt = len(nodes), dt_ns * 1e-9
    # Positive element current flows a -> b. None is GND; PACK is the imposed -8.4 V source.
    branches = [(e['a'], e['b'], e) for e in model_edges]
    branches.append(('PACK', pins['J1.1'], None))
    # Recovery control only: feed U9/C88 from the C80 input node with the existing long feed's R/L.
    # A lumped control collapses all BAT_IN protection terminals; it is a diagnostic, never gate evidence.
    if topology != 'board':
        if topology not in ('lumped',):
            raise ValueError(topology)
        # Very low parasitics in the F.Cu protection cluster reconstruct R8's node-A premise.
    E = np.zeros((len(branches), nn))
    R, L = np.zeros((ncase, len(branches))), np.zeros((ncase, len(branches)))
    for j, (a, b, e) in enumerate(branches):
        if a != 'PACK': E[j, index[a]] = 1
        E[j, index[b]] -= 1
        for c, corner in enumerate(corners):
            if e is None:
                R[c, j], L[c, j] = corner['rh_ohm'], corner['lh_uH'] * 1e-6
            else:
                R[c, j], L[c, j] = e['R_ohm'], e['L_' + corner['reference'] + '_nH'] * 1e-9
                if topology == 'lumped' and all(p['layer'] == 'F.Cu' for p in e['pieces']):
                    R[c, j], L[c, j] = 1e-6, 1e-12
    caps = [('C80.1', None, 4.7, 10.), ('C96.1', None, 4.7, 10.),
            ('C89.1', 'C89.2', 8.35, 22.), ('C95.1', 'C95.2', 8.35, 22.), ('C88.1', None, 0., 0.)]
    CE = np.zeros((len(caps), nn)); CV = np.zeros((ncase, len(caps)))
    for j, (a, b, low, high) in enumerate(caps):
        CE[j, index[pins[a]]] = 1
        if b: CE[j, index[pins[b]]] -= 1
        for c, corner in enumerate(corners):
            CV[c, j] = (corner['cb_nF'] * 1e-3 if a == 'C88.1' else
                         low if corner['cap_scale'] == 'derated' else high) * 1e-6
    CG = 2 * CV / dt
    G = dt / (2 * L + R * dt)
    q = (2 * L - R * dt) / (2 * L + R * dt)
    A = np.einsum('ei,ce,ej->cij', E, G, E) + np.einsum('ei,ce,ej->cij', CE, CG, CE)
    for pin, resistance in (('R166.1', .33), ('R167.1', 1e4)):
        A[:, index[pins[pin]], index[pins[pin]]] += 1 / resistance
    inverse = np.linalg.inv(A)
    d = index[pins['D8.1']]; u = index[pins['U9.5']]
    response = inverse[:, :, d]; z = inverse[:, d, d]
    vbr = np.array([c['vbr_V'] for c in corners])
    V = np.full((ncase, nn), 2.)
    for pin in ('C89.2', 'C95.2', 'R166.1'):
        V[:, index[pins[pin]]] = 0.
    I = np.zeros_like(G); IC = np.zeros_like(CG)
    offset = np.zeros_like(G); offset[:, -1] = -8.4
    # Backward-Euler first step establishes the algebraic (uncapacitated) node voltages after the source step.
    # Starting trapezoidal directly from the pre-plug voltages produces an artificial alternating algebraic mode.
    G0, CG0 = dt / (L + R * dt), CV / dt
    A0 = np.einsum('ei,ce,ej->cij', E, G0, E) + np.einsum('ei,ce,ej->cij', CE, CG0, CE)
    for pin, resistance in (('R166.1', .33), ('R167.1', 1e4)):
        A0[:, index[pins[pin]], index[pins[pin]]] += 1 / resistance
    inverse0 = np.linalg.inv(A0)
    vmin, vmax = V[:, u].copy(), V[:, u].copy()
    falling = np.zeros(ncase); rising = np.zeros(ncase); peak_t = np.zeros(ncase); peak_v = np.full(ncase, 2.)
    for step in range(int(round(end_us * 1e-6 / dt))):
        old_drop = np.einsum('ci,ei->ce', V, E) + offset
        old_cap = np.einsum('ci,ei->ce', V, CE)
        gg, cg, inv = (G0, CG0, inverse0) if step == 0 else (G, CG, inverse)
        history = L / (L + R * dt) * I if step == 0 else q * I + G * old_drop
        cap_history = cg * old_cap if step == 0 else cg * old_cap + IC
        rhs = -np.einsum('ce,ei->ci', history + gg * offset, E) + np.einsum('ce,ei->ci', cap_history, CE)
        free = np.einsum('cij,cj->ci', inv, rhs)
        response, z = inv[:, :, d], inv[:, d, d]
        # v + Z I_tvs(v) = free_d. Newton is scalar and monotone, including the R8 soft knee.
        vd = free[:, d].copy()
        for _ in range(12):
            x = (np.abs(vd) - vbr) / .1
            tvs = np.sign(vd) * .5 * np.logaddexp(0., x)
            slope = 5. / (1 + np.exp(-np.clip(x, -700, 700)))
            change = (vd + z * tvs - free[:, d]) / (1 + z * slope)
            vd -= change
            if np.max(np.abs(change)) < 1e-10: break
        tvs = np.sign(vd) * .5 * np.logaddexp(0., (np.abs(vd) - vbr) / .1)
        new = free - response * tvs[:, None]
        slew = (new[:, u] - V[:, u]) / dt / 1e6
        changed = -slew > falling
        peak_t[changed] = (step + .5) * dt * 1e6
        peak_v[changed] = (new[changed, u] + V[changed, u]) / 2
        falling = np.maximum(falling, -slew); rising = np.maximum(rising, slew)
        vmin = np.minimum(vmin, new[:, u]); vmax = np.maximum(vmax, new[:, u])
        I = gg * (np.einsum('ci,ei->ce', new, E) + offset) + history
        IC = cg * np.einsum('ci,ei->ce', new, CE) - cap_history
        V = new
    if not np.isfinite(V).all(): raise ValueError('non-finite hot-plug state')
    return [dict(corner=c, minimum_V=float(vmin[i]), maximum_V=float(vmax[i]),
                 falling_V_per_us=float(falling[i]), rising_V_per_us=float(rising[i]),
                 falling_peak_us=float(peak_t[i]), falling_peak_voltage_V=float(peak_v[i]))
            for i, c in enumerate(corners)]


def assess(rows):
    failures = []
    for i, row in enumerate(rows):
        for k, limit in LIMITS.items():
            value = row.get(k)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or \
                    (value < limit if k == 'minimum_V' else value > limit):
                failures.append(dict(case=i, metric=k, value=value, limit=limit))
            elif (k == 'minimum_V' and value > 2.) or (k == 'maximum_V' and value < 2.) or \
                    (k in ('falling_V_per_us', 'rising_V_per_us') and value < 0):
                failures.append(dict(case=i, metric=k, value=value,
                                     limit='minimum <= initial 2V <= maximum; slew extrema >= 0'))
    return failures


def extreme_corners(rows):
    selected = []
    for key in LIMITS:
        row = (min if key == 'minimum_V' else max)(rows, key=lambda r: r[key])
        if row['corner'] not in selected: selected.append(row['corner'])
    return selected


def local_sensitivity_corners(rows):
    # These are deliberately assumed values, not TI/connector limits. The checked feed-first topology is primary.
    return [dict(c, input_cap_pF=cap, contact_edge_ns=edge) for c in extreme_corners(rows)
            for cap in (0., 10., 100., 1000., 10000.) for edge in (.1, 1., 10.)]


def report(inputs, rows, step_scale=1., end_us=150.):
    selected = extreme_corners(rows)
    refined = run_nonlinear(inputs, selected, step_scale=step_scale / 2, end_us=end_us)
    by_corner = {digest(r['corner']): r for r in rows}
    deltas = {k: max(abs(r[k] - by_corner[digest(r['corner'])][k]) for r in refined) for k in LIMITS}
    failed = assess(rows) + assess(refined)
    convergence = dict(step_scale=step_scale / 2, rows=refined, max_abs_delta=deltas, limits=CONVERGENCE_LIMITS)
    converged = all(deltas[k] <= CONVERGENCE_LIMITS[k] for k in LIMITS)
    # No fuse-derived minimum resistance: retain F9's >=0.03 ohm required domain; separately test lower R.
    sensitivity_corners = [dict(c, rh_ohm=rh) for c in selected for rh in (0., .01)]
    sensitivity = run_nonlinear(inputs, sensitivity_corners, step_scale=step_scale, end_us=end_us)
    unclamped = run_nonlinear(inputs, [dict(c, vbr_V=1000.) for c in selected], step_scale=step_scale, end_us=end_us)
    discharge = retained_output(inputs)
    components = component_issues(inputs)
    topology = topology_issues(inputs)
    local = run_nonlinear(inputs, local_sensitivity_corners(rows), step_scale=SENSITIVITY_STEP, end_us=SENSITIVITY_US)
    local_fine = run_nonlinear(inputs, extreme_corners(local), step_scale=SENSITIVITY_STEP / 2, end_us=SENSITIVITY_US)
    local_by_corner = {digest(r['corner']): r for r in local}
    local_deltas = {k: max(abs(r[k] - local_by_corner[digest(r['corner'])][k]) for r in local_fine) for k in LIMITS}
    local_passed = not assess(local + local_fine) and all(local_deltas[k] <= CONVERGENCE_LIMITS[k] for k in LIMITS)
    cold_ok = min(r['minimum_V'] for r in rows + refined + unclamped) >= discharge['cold_input_minimum_V']
    passed = not failed and converged and not components and not topology and cold_ok and not assess(unclamped) and local_passed
    return dict(schema=SCHEMA, inputs_sha256=digest(inputs), model_sha256=model_sha(), limits=LIMITS,
                topology='board', method='nonlinear charge, maker C(V), trapezoidal with backward-Euler start',
                initial_input_V=2., pack_V=-8.4, step_scale=step_scale, end_us=end_us,
                steps_ns=[.5 * step_scale, 2 * step_scale, 10 * step_scale],
                temperature_and_tolerance=curves()[-1], rows=rows, failures=failed, convergence=convergence,
                convergence_passed=converged, passed=passed,
                qualification='pass' if passed else 'failed',
                component_issues=components, topology_issues=topology, retained_output=discharge, cold_limit_passed=cold_ok,
                local_path_sensitivity=dict(rows=local, step_scale=SENSITIVITY_STEP, end_us=SENSITIVITY_US,
                    refined_rows=local_fine, refined_step_scale=SENSITIVITY_STEP / 2,
                    max_abs_delta=local_deltas, passed=local_passed,
                    note='First 0.5us only: assumed U9 input capacitance 0..10nF and contact edges 0.1/1/10ns. '
                         'No manufacturer capacitance/edge bounds or package ESL/ESR guarantee. '
                         'All local copper remains in the model; C88 must separate U9 from the incoming feed.'),
                no_clamp_control=dict(rows=unclamped, failures=assess(unclamped)),
                lower_resistance_sensitivity=dict(rows=sensitivity, failures=assess(sensitivity),
                    note='Outside F9 required >=0.03 ohm envelope; no battery-lead fuse assumed. Measure pack+harness resistance.'),
                inference='Maker curves are typical; temperature/bias combination and PCB parasitics estimated. Bench qualification outstanding.')


def validate(inputs, report, live_signature):
    """Fail closed; a forged summary cannot hide a failing, missing, stale or non-finite corner."""
    issues = []
    if inputs.get('schema') != SCHEMA or report.get('schema') != SCHEMA:
        issues.append('unsupported model schema')
    if inputs.get('electrical_sha256') != live_signature:
        issues.append('stale electrical inputs (BAT_IN/protection geometry or parts changed)')
    if report.get('inputs_sha256') != digest(inputs):
        issues.append('stale model inputs')
    if report.get('model_sha256') != model_sha():
        issues.append('stale model source')
    issues += component_issues(inputs)
    issues += topology_issues(inputs)
    if report.get('limits') != LIMITS:
        issues.append('model limits changed')
    if report.get('topology') != 'board':
        issues.append('model is a topology control, not this board')
    if report.get('initial_input_V') != 2. or report.get('pack_V') != -8.4:
        issues.append('model initial/source voltages changed')
    step, duration = report.get('step_scale'), report.get('end_us')
    if isinstance(step, bool) or not isinstance(step, (int, float)) or not math.isfinite(step) or not 0 < step <= 1:
        issues.append('model timestep is not qualified')
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration < 150:
        issues.append('model duration is too short')
    rows = report.get('rows', [])
    if [r.get('corner') for r in rows] != cases():
        issues.append('missing or changed model corners')
    failed = assess(rows)
    if failed:
        worst = max(failed, key=lambda x: abs(x['value']) if isinstance(x['value'], (int, float)) else math.inf)
        issues.append('model fails: ' + str(worst))
    if report.get('passed') is not True or report.get('qualification') != 'pass':
        issues.append('model does not establish F9 compliance')
    conv = report.get('convergence', {})
    fine = conv.get('rows', [])
    if not rows or [r.get('corner') for r in fine] != extreme_corners(rows) or \
            not isinstance(step, (int, float)) or conv.get('step_scale') != step / 2:
        issues.append('model convergence corners/steps missing or changed')
    else:
        by_corner = {digest(r['corner']): r for r in rows}
        for key, tolerance in CONVERGENCE_LIMITS.items():
            for row in fine:
                val = row.get(key)
                if not isinstance(val, (int, float)) or not math.isfinite(val) or \
                        abs(val - by_corner[digest(row['corner'])][key]) > tolerance:
                    issues.append('model convergence fails: ' + key)
        if assess(fine): issues.append('refined model fails limits')
    unclamped = report.get('no_clamp_control', {}).get('rows', [])
    if not rows or [r.get('corner') for r in unclamped] != [dict(c, vbr_V=1000.) for c in extreme_corners(rows)] or \
            assess(unclamped):
        issues.append('missing or failing no-clamp control')
    local = report.get('local_path_sensitivity', {})
    local_rows, local_fine = local.get('rows', []), local.get('refined_rows', [])
    if not rows or [r.get('corner') for r in local_rows] != local_sensitivity_corners(rows) or \
            local.get('step_scale') != SENSITIVITY_STEP or local.get('end_us') != SENSITIVITY_US or \
            local.get('refined_step_scale') != SENSITIVITY_STEP / 2 or not local_rows or \
            [r.get('corner') for r in local_fine] != extreme_corners(local_rows) or assess(local_rows + local_fine):
        issues.append('missing, changed or failing local-path sensitivity')
    else:
        local_by_corner = {digest(r['corner']): r for r in local_rows}
        if any(abs(row[k] - local_by_corner[digest(row['corner'])][k]) > tolerance
               for row in local_fine for k, tolerance in CONVERGENCE_LIMITS.items()):
            issues.append('local-path sensitivity does not converge')
    try:
        discharge = retained_output(inputs)
        if report.get('retained_output') != discharge:
            issues.append('stale retained-output calculation')
        if any(not isinstance(r.get('minimum_V'), (int, float)) or not math.isfinite(r['minimum_V']) or
               r['minimum_V'] < discharge['cold_input_minimum_V'] for r in rows + fine + unclamped):
            issues.append('cold IN-to-OUT absolute limit fails')
    except (KeyError, ValueError, TypeError) as exc:
        issues.append('invalid retained-output calculation: ' + str(exc))
    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--extract', type=Path)
    ap.add_argument('--inputs', type=Path, default=INPUTS)
    ap.add_argument('--output', type=Path, default=RESULTS)
    ap.add_argument('--dt-ns', type=float, default=1.)
    ap.add_argument('--linear', action='store_true', help='legacy R8 constant-C diagnostic only')
    ap.add_argument('--step-scale', type=float, default=1.)
    ap.add_argument('--end-us', type=float, default=150.)
    ap.add_argument('--control', choices=('board', 'lumped'), default='board')
    a = ap.parse_args()
    if a.extract:
        import pcbnew
        result = extract(pcbnew.LoadBoard(str(a.extract)), a.extract)
        a.inputs.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({k: result[k] for k in ('board_sha256', 'electrical_sha256')}, indent=2))
        print('edges:', len(result['edges']))
        return 0
    inp = json.loads(a.inputs.read_text())
    frozen = model_sha()
    if a.linear:
        rows = run(inp, linear_cases(), a.dt_ns, a.end_us, a.control)
        out = dict(rows=rows, failures=assess(rows), qualification='unqualified', topology=a.control,
                   note='Legacy constant-capacitance control; not gate evidence')
    else:
        rows = run_nonlinear(inp, cases(), a.step_scale, a.end_us)
        out = report(inp, rows, a.step_scale, a.end_us)
    failed = out['failures']
    if frozen != model_sha():
        raise ValueError('model sources changed during simulation')
    a.output.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(dict(cases=len(rows), failures=len(failed), minimum=min(rows, key=lambda r: r['minimum_V']),
                         fastest=max(rows, key=lambda r: r['falling_V_per_us'])), indent=2))
    return 1 if failed or (not a.linear and out['qualification'] != 'pass') else 0


if __name__ == '__main__':
    raise SystemExit(main())
