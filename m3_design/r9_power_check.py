#!/usr/bin/env python3
"""R9 build step 6 gate: the power copper (r9_plan.md section 4 step 6; R9_DECISIONS D-S6-*).

usage: <KiCad python3> -I m3_design/r9_power_check.py [board] [--report OUT.json] [--seed SEED.json]
                                                     [--numpy-py PYTHON3-WITH-NUMPY] [--dc-dir DIR]
       exit 0 = every gate passes
       --seed: reuse a rule_h_seed.py report of this board (bound by its board_sha256); without it the suite runs here
       --dc-dir: keep the DC solves' outputs there (each output's first line is the board's SHA-256)

The board is r9_power.py's output. Gates (tools/check_r9.py, run_dc.sh / dc_solve.py, route_check.py, the step-5 gate's
pyro functions and R8's hot-plug model are called, never restated or weakened; the step's own floors are stricter):
  template   the copper r9_power.py draws (a dry run on this board: tracks, vias, zone outlines) is on the board, and
             the board has no other copper on the nets the step owns (r9_power.NETS and PARTIAL)
  in2        In2 holds the four regions (GND, RAW_ACT, BAT_IN, 3V3) and the RF strip's GND pour only (from step 8 also
             the crystal's GND plane, IN2_LATER: optional here, required by r9_ground_check), each power region
             filled as one piece, and no track (r9_plan section 3, S15 / S16)
  dc         tools/run_dc.sh at 0.1 mm (the three 7.7 A paths): R8_DECISIONS D12's limits (RAW_ACT / BAT_IN 20 C,
             ACT_FET_S 30 C), and the stricter r9_plan section 2 rows: every rise <= R8's at the same grid (RAW_ACT
             17.6, BAT_IN 14.8, ACT_FET_S 22.3 C), D_raw <= 1.0 mOhm, no via barrel over 1.0 A (MARGIN P1-9)
  supply     dc_solve on the supply paths the step draws: RAW_PROTECTED U9 -> U7 (1 A) / U11 (0.5 A) and CAM_5V L3 -> J9
             (1 A) each no via barrel over 1.0 A; BAT_IN J1.1 -> U9.5 (the hot-plug feed's R_b) reported for f9
  f9         REQUIREMENTS F9's hot-plug premise (R8 D76): R8's model (hotplug_feed_r9.py, numpy) with this board's R_b
             and the feed's estimate, and at R8's 5 nH bound: U9 IN departs from the protected input node by <= 0.01 V
             and <= 5 % in slew (the R4 figures -14.6 V / 9.2 V/us then stay inside the TPS25947's -15 V / 10 V/us)
  pyro       the step-5 gate's functions on the powered board: pyro margins (A-H, A2 + max(R8, 0.2 mm), the recorded
             U1.3 entry exception), the bridge table (no fires-class pair under 1.5 mm), GATE_N's neighbours, the sense
             lanes' MCU sides, no foreign net within 3 mm of armed copper (X2)
  contract   check_r9: every rule but M-2 (placement-bound, step 3's gate runs the plate model), K-legends (step 8)
             and K-contract's route-only camera-bypass items (step 7); P-4 with this board's seeded report. This holds
             D18 (K-power-pyro, X9c >= 2.65 mm), D85 (X2d >= 2.5 mm), P-3, P-6, F9-1, M-5, R-2 and LC-1 on the copper
  actuators  m3_design/check_actuators.py on the board and m3.kicad_dru: no finding
  drc        kicad-cli DRC with schematic parity, every severity: no violation but step 8's silkscreen classes and the
             PENDING vias' via_dangling, no parity item, no unconnected item on a net the step completes, and on the
             partial nets only the pads PARTIAL names
  route      tools/route_check.py, profile r9: no failing instance and no unrecorded leftover but the PENDING vias'
             dangling_via and the dead_copper of those vias and their straps (and step 5's GATE_N guard via, which waits
             for the same In1 GND pour)
"""
import argparse
import collections
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_actuators as CA  # noqa: E402
import check_r9 as C9  # noqa: E402
import route_check as rc  # noqa: E402
import r9_power as RP  # noqa: E402
import r9_pyro  # noqa: E402
import r9_pyro_check as PC  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
HOTPLUG = ROOT / 'm3_design/assembly_review/sources/r9_design/step6_evidence/hotplug_feed_r9.py'
DRC_DEFERRED = {'silk_over_copper', 'silk_overlap', 'silk_edge_clearance'}   # r9_post.py (step 8)
GRID = 0.1
D12 = {'raw': 20.0, 'bat': 20.0, 'fet': 30.0}                 # R8_DECISIONS D12 (run_dc.sh)
R8_RISE = {'raw': 17.6, 'bat': 14.8, 'fet': 22.3}             # R8 at the 0.1 mm grid (tools/r9_scorecard.QUICK)
D_RAW_MAX = 1.0                                               # mOhm, r9_plan section 2 power row
VIA_MAX = 1.0                                                 # A per via barrel (MARGIN P1-9)
SUPPLY = [('rp_u7', 'RAW_PROTECTED', 'U9:6', 'U7:3,4', 1.0), ('rp_u11', 'RAW_PROTECTED', 'U9:6', 'U11:2', 0.5),
          ('cam_j9', 'CAM_5V', 'L3:2', 'J9:1', 1.0), ('bat_u9', 'BAT_IN', 'J1:1', 'U9:5', 1.0)]
F9_EXTRA_V, F9_SLEW = 0.01, 1.05                              # U9 IN against the input node (f9)
F9_BOUND_NH = 5.0                                             # R8 D76's lowest modelled feed
IN2_ZONES = {'R9_GND_In2': 'GND', 'R9_RAW_ACT_In2': 'RAW_ACT', 'R9_BAT_IN_In2': 'BAT_IN', 'R9_3V3_In2': '3V3',
             'R9_GND_In2_strip': 'GND'}
# zones a later step adds on In2: step 8's local ground plane under the crystal (r9_ground.XTAL_ZONE; R9_DECISIONS D-S8-20).
# GND only; accepted when present, never required here (r9_ground_check's table gate requires it on the step-8 board).
IN2_LATER = {'R9_GND_In2_Y1': 'GND'}
CONTRACT_SKIP = {'M-2', 'K-legends'}
ROUTE_ONLY = re.compile(r'^K-contract: C(100|93): requires (local bypass within \d mm of U12\.\d+ and direct copper|'
                        r'direct local GND return)')
# step 5's GATE_N guard via waits for the same In1 GND pour (r9_step5_handoff section 4)
STEP5_PENDING = [(13.5, 54.6)]


def r4(v):
    return round(v, 4)


LAYER_NAME = {pcbnew.F_Cu: 'F', pcbnew.B_Cu: 'B', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2'}


def lay(b, t):
    return LAYER_NAME.get(t.GetLayer(), b.GetLayerName(t.GetLayer()))


def seg_key(net, layer, w, a, c):
    return (net, layer, round(w, 3), tuple(sorted((a, c))))


def gate_template(b):
    d = RP.build(b, dry=True)
    want_t = collections.Counter(seg_key(*t) for t in d.tracks)
    want_v = {(net, at, d.via_size[at]) for at, net in d.vias.items()}
    own = set(RP.NETS) | set(RP.PARTIAL)
    have_t, have_v = collections.Counter(), set()
    for t in b.GetTracks():
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            key = (net, (r4(mm(t.GetPosition().x)), r4(mm(t.GetPosition().y))),
                   (round(mm(t.GetWidth(pcbnew.F_Cu)), 3), round(mm(t.GetDrillValue()), 3)))
            if net in own or key in want_v:
                have_v.add(key)
            continue
        a = (r4(mm(t.GetStart().x)), r4(mm(t.GetStart().y)))
        c = (r4(mm(t.GetEnd().x)), r4(mm(t.GetEnd().y)))
        key = seg_key(net, lay(b, t), mm(t.GetWidth()), a, c)
        if net in own or key in want_t:
            have_t[key] += 1
    issues = [f'template: missing {k[0]} {k[1]} w{k[2]} {k[3]}' for k in sorted(want_t - have_t)]
    issues += [f'template: extra {k[0]} {k[1]} w{k[2]} {k[3]}' for k in sorted(have_t - want_t)]
    issues += [f'template: missing via {k}' for k in sorted(want_v - have_v)]
    issues += [f'template: extra via {k}' for k in sorted(have_v - want_v)]
    zones = {z.GetZoneName(): z for z in b.Zones() if not z.GetIsRuleArea()}
    for name, net, layer, z in d.zones:
        bz = zones.get(name)
        if bz is None:
            issues.append(f'template: zone {name} missing')
            continue
        if bz.GetNetname() != net or not bz.IsOnLayer(RP.LAYER[layer]) or \
                bz.GetAssignedPriority() != z.GetAssignedPriority():
            issues.append(f'template: zone {name} differs (net / layer / priority)')
        x1 = bz.Outline().CloneDropTriangulation()
        x1.BooleanSubtract(z.Outline())
        x2 = z.Outline().CloneDropTriangulation()
        x2.BooleanSubtract(bz.Outline())
        err = (x1.Area() + x2.Area()) / 1e12
        if err > 1e-6:
            issues.append(f'template: zone {name} outline differs by {err:.6f} mm2')
    for name, z in zones.items():
        if z.GetNetname() in own and name not in {n for n, *_ in d.zones}:
            issues.append(f'template: extra zone {name} ({z.GetNetname()})')
    return issues, dict(segments=sum(want_t.values()), vias=len(want_v), zones=len(d.zones),
                        length_mm=round(sum(math.dist(*k[3]) for k in want_t.elements()), 2))


def gate_in2(b):
    issues, ev = [], {}
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA' and t.GetLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            issues.append(f'in2: {b.GetLayerName(t.GetLayer())} track of {t.GetNetname()} at '
                          f'({mm(t.GetStart().x):.2f}, {mm(t.GetStart().y):.2f})')
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.In2_Cu):
            continue
        name = z.GetZoneName()
        if IN2_ZONES.get(name, IN2_LATER.get(name)) != z.GetNetname():
            issues.append(f'in2: zone {name} ({z.GetNetname()}) is not one of the four regions / the strip pour')
            continue
        fill = z.GetFilledPolysList(pcbnew.In2_Cu)
        ev[name] = dict(pieces=fill.OutlineCount(), area_mm2=round(fill.Area() / 1e12, 1))
        if name in ('R9_RAW_ACT_In2', 'R9_BAT_IN_In2', 'R9_3V3_In2') and fill.OutlineCount() != 1:
            issues.append(f'in2: {name} fills as {fill.OutlineCount()} pieces (one region, one piece)')
    missing = set(IN2_ZONES) - set(ev)
    if missing:
        issues.append(f'in2: regions missing: {sorted(missing)}')
    return issues, ev


NUM = r'([0-9.]+)'


def parse_dc(text):
    """dc_solve output -> R (mOhm), neck rise (C), largest via current (A), vias over 1 A."""
    r = re.search(rf'R = {NUM} mOhm', text)
    rise = re.search(rf'rises {NUM} C at', text)
    via = re.search(rf'largest barrel currents at {NUM} A: {NUM} A', text)
    over = re.search(r'over 1\.0 A: (\d+)', text)
    sha = re.search(r'^board .* sha256 ([0-9a-f]{64})$', text, re.M)
    return dict(mohm=float(r.group(1)) if r else None, rise_c=float(rise.group(1)) if rise else None,
                via_max_a=float(via.group(2)) if via else None, vias_over_1a=int(over.group(1)) if over else None,
                sha=sha.group(1) if sha else None)


def judge_dc(rows, sha):
    """rows: {'raw' / 'bat' / 'fet': parse_dc(...)} -> issues (D12, R8 rises, D_raw, vias)."""
    issues = []
    for k in ('raw', 'bat', 'fet'):
        r = rows.get(k)
        if not r or r['mohm'] is None or r['rise_c'] is None:
            issues.append(f'dc: {k} solve failed')
            continue
        if r['sha'] != sha:
            issues.append(f'dc: {k} solve is not bound to this board')
        if r['rise_c'] > D12[k]:
            issues.append(f"dc: {k} neck rises {r['rise_c']} C > D12 {D12[k]} C")
        if r['rise_c'] > R8_RISE[k]:
            issues.append(f"dc: {k} neck rises {r['rise_c']} C > R8's {R8_RISE[k]} C (every rise <= R8)")
        if r['via_max_a'] is not None and r['via_max_a'] > VIA_MAX:
            issues.append(f"dc: {k} via barrel {r['via_max_a']} A > {VIA_MAX} A")
        if r['vias_over_1a']:
            issues.append(f"dc: {k} {r['vias_over_1a']} vias over 1.0 A")
    if rows.get('raw') and rows['raw']['mohm'] is not None and rows['raw']['mohm'] > D_RAW_MAX:
        issues.append(f"dc: D_raw {rows['raw']['mohm']} mOhm > {D_RAW_MAX}")
    return issues


def gate_dc(path, keep):
    out = Path(keep) if keep else Path(tempfile.mkdtemp())
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(['bash', str(ROOT / 'tools/run_dc.sh'), str(path), str(out), str(GRID)], capture_output=True)
    rows = {k: parse_dc((out / f'dc_{k}.txt').read_text()) if (out / f'dc_{k}.txt').is_file() else None
            for k in ('raw', 'bat', 'fet')}
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return judge_dc(rows, sha), dict(grid_mm=GRID, rows=rows, limits=dict(D12=D12, R8=R8_RISE, D_raw=D_RAW_MAX,
                                                                         via=VIA_MAX))


def gate_supply(path, keep):
    out = Path(keep) if keep else Path(tempfile.mkdtemp())
    out.mkdir(parents=True, exist_ok=True)
    procs = {}
    for name, net, src, snk, amps in SUPPLY:
        f = open(out / f'{name}.txt', 'w')
        procs[name] = (subprocess.Popen([sys.executable, '-I', str(ROOT / 'tools/dc_solve.py'), str(path), '--grid',
                                         str(GRID), '--net', net, '--source', src, '--sink', snk, '--amps',
                                         str(amps), '--via-currents', '3'], stdout=f, stderr=subprocess.STDOUT), f)
    rows, issues = {}, []
    for name, (p, f) in procs.items():
        p.wait()
        f.close()
        rows[name] = parse_dc((out / f'{name}.txt').read_text())
        if rows[name]['mohm'] is None:
            issues.append(f'supply: {name} solve failed')
        elif name != 'bat_u9' and (rows[name]['via_max_a'] or 0) > VIA_MAX:
            issues.append(f"supply: {name} via barrel {rows[name]['via_max_a']} A > {VIA_MAX} A")
    return issues, dict(paths={n: dict(net=net, source=s, sink=k, amps=a, **rows[n]) for n, net, s, k, a in SUPPLY})


def gate_f9(rb_mohm, numpy_py):
    if rb_mohm is None:
        return ['f9: no R_b (BAT_IN J1:1 -> U9:5 solve failed)'], {}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'f9.json'
        r = subprocess.run([numpy_py, '-I', str(HOTPLUG), '--rb', str(rb_mohm), '--json', str(out)],
                           capture_output=True, text=True)
        if r.returncode or not out.is_file():
            return [f'f9: hotplug_feed_r9.py failed: {(r.stdout + r.stderr)[-300:]}'], {}
        res = json.loads(out.read_text())
    return judge_f9(res), res


def judge_f9(res):
    """hotplug_feed_r9.py's result -> issues (every modelled feed up to F9_BOUND_NH, and the estimate itself)."""
    issues = []
    est = res['feed_estimate_nH']
    for lb, v in res['by_feed_nH'].items():
        if float(lb) > F9_BOUND_NH + 1e-9:
            continue
        if v['extra_negative_V'] > F9_EXTRA_V or v['slew_ratio'] > F9_SLEW:
            issues.append(f"f9: at {lb} nH U9 IN departs {v['extra_negative_V']} V / slew x{v['slew_ratio']} from the "
                          f"input node (<= {F9_EXTRA_V} V, x{F9_SLEW})")
    if est > F9_BOUND_NH:
        issues.append(f'f9: feed estimate {est} nH > {F9_BOUND_NH} nH')
    return issues


def gate_pyro(b, ctx):
    issues, ev = [], {}
    for name, fn in (('margins', lambda: PC.gate_margins(b)), ('bridges', lambda: PC.gate_bridges(b)),
                     ('gate_n', lambda: PC.gate_neighbours(b, ctx)), ('sense', lambda: PC.gate_sense(b, ctx)),
                     ('armed', lambda: PC.gate_armed(b, ctx))):
        i, e = fn()
        issues += [f'pyro {name}: {x}' for x in i]
        ev[name] = e
    return issues, ev


def gate_contract(b, path, seed):
    only = {rid for rid, _, _ in C9.RULES} - CONTRACT_SKIP
    res = C9.check_board(b, path.parent, path, only=only, seed=seed,
                         board_sha=hashlib.sha256(path.read_bytes()).hexdigest())
    issues = [i for i in res['issues'] if not ROUTE_ONLY.match(i)]
    deferred = [i for i in res['issues'] if ROUTE_ONLY.match(i)]
    ev = {k: v['evidence'] for k, v in res['rules'].items()}
    ev['deferred_to_step7'] = deferred
    return issues, ev


def gate_actuators(path):
    found = CA.check(path.read_text(), path.with_suffix('.kicad_dru').read_text())
    return [f'actuators: {i}' for i in found], dict(findings=len(found))


def pending_vias():
    return [(r4(x), r4(y)) for x, y in RP.PENDING + STEP5_PENDING]


def gate_drc(path):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(path)], capture_output=True)
        if not out.is_file():
            return ['drc: kicad-cli produced no report'], {}
        rep = json.loads(out.read_text())
    return judge_drc(rep)


def judge_drc(rep):
    """A kicad-cli DRC report (JSON) -> (issues, evidence)."""
    pend = pending_vias()
    bad, deferred, pending = [], collections.Counter(), []
    for v in rep['violations']:
        if v['type'] in DRC_DEFERRED:
            deferred[v['type']] += 1
            continue
        if v['type'] == 'via_dangling' and len(v['items']) == 1 and '[GND]' in v['items'][0]['description'] and \
                any(math.dist((v['items'][0]['pos']['x'], v['items'][0]['pos']['y']), at) < 2e-3 for at in pend):
            pending.append((v['items'][0]['pos']['x'], v['items'][0]['pos']['y']))
            continue
        bad.append(f"drc: {v['type']}: " + ' | '.join(i['description'] for i in v['items']))
    for p in rep.get('schematic_parity', []):
        bad.append(f"drc: parity {p['type']}: " + ' | '.join(i['description'] for i in p.get('items', [])))
    pad_re = re.compile(r'Pad (\S+) \[([^\]]+)\] of (\S+)')
    partial_left = collections.defaultdict(set)
    for u in rep.get('unconnected_items', []):
        nets = {i['description'].split('[')[1].split(']')[0] for i in u['items'] if '[' in i['description']}
        if nets & set(RP.NETS):
            bad.append('drc: unconnected ' + ' | '.join(i['description'] for i in u['items']))
        for net in nets & set(RP.PARTIAL):
            pads = [f'{m.group(3)}.{m.group(1)}' for i in u['items'] for m in [pad_re.search(i['description'])] if m]
            allowed = set(RP.PARTIAL[net])
            if not any(p in allowed for p in pads):
                bad.append(f'drc: unconnected {net} beyond the deferred pads: ' +
                           ' | '.join(i['description'] for i in u['items']))
            partial_left[net].update(p for p in pads if p in allowed)
    return bad, dict(unconnected_total=len(rep['unconnected_items']), deferred=dict(deferred),
                     pending_vias=pending, partial_left={k: sorted(v) for k, v in partial_left.items()})


def chains(segs, starts):
    """The segments joined end to end (through track ends) to any of the start points."""
    pts, out, todo = set(starts), [], list(segs)
    grew = True
    while grew:
        grew = False
        for sg in list(todo):
            if any(math.dist(q, p) < 2e-3 for q in sg for p in pts):
                out.append(sg)
                todo.remove(sg)
                pts.update(sg)
                grew = True
    return out


def gate_route(b):
    pend = pending_vias()
    d = RP.build(b, dry=True)
    segs = [(a, c) for net, layer, w, a, c in d.tracks if net == 'GND']
    segs += [(a, c) for net, _, _, pts in r9_pyro.copper(r9_pyro.Pads(b))[0] if net == 'GND'
             for a, c in zip(pts, pts[1:])]
    gnd_t = chains(segs, pend)

    def on_pending(x):
        p = (round(x['x'], 4), round(x['y'], 4))
        if x['net'] != 'GND' or x['cat'] not in ('dangling_via', 'dead_copper'):
            return False
        return any(math.dist(p, v) < 2e-3 for v in pend) or \
            any(C9.seg_point_dist(p, a, c) < 2e-3 for a, c in gnd_t)
    rc.set_profile('r9')
    inst = rc.scan(b, [])
    bumps, searched = rc.bump_audit(b)
    inst += bumps
    failures, allowed, stale = rc.evaluate(inst)
    _, missing, _ = rc.leftover_check(inst)
    pending = [x for x in failures if on_pending(x)]
    issues = [f"route: {x['cat']} {x['net']} {x['layer']} ({x['x']}, {x['y']})" for x in failures if x not in pending]
    issues += [f"route: unrecorded leftover {x['cat']} {x['net']} {x['layer']} ({x['x']}, {x['y']})" for x in missing]
    issues += [f'route: allowlist entry {e[:4]}' for e in allowed + stale]
    own = set(RP.NETS) | set(RP.PARTIAL)
    mine = [x for x in inst if x['net'] in own]
    return issues, dict(instances=len(inst), pending=[f"{x['cat']} {x['net']} ({x['x']}, {x['y']})" for x in pending],
                        step_nets=dict(collections.Counter(x['cat'] for x in mine)), bump_windows=searched)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--report', type=Path)
    ap.add_argument('--seed', type=Path, help='a rule_h_seed.py report of this board')
    ap.add_argument('--numpy-py', default='python3', help='a python3 with numpy (the hot-plug model, f9)')
    ap.add_argument('--dc-dir', type=Path, help='keep the DC solves here')
    args = ap.parse_args()
    path = args.board.resolve()
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    seed = PC.run_seed(path, args.seed)
    board = pcbnew.LoadBoard(str(path))
    ctx = C9.Ctx(board, path.parent, path)
    report, fails = {}, {}

    def gate(name, result):
        issues, ev = result
        report[name] = dict(ok=not issues, issues=issues, evidence=ev)
        fails[name] = len(issues)
    gate('template', gate_template(board))
    gate('in2', gate_in2(board))
    gate('dc', gate_dc(path, args.dc_dir))
    gate('supply', gate_supply(path, args.dc_dir))
    gate('f9', gate_f9(report['supply']['evidence'].get('paths', {}).get('bat_u9', {}).get('mohm'), args.numpy_py))
    gate('pyro', gate_pyro(board, ctx))
    gate('contract', gate_contract(board, path, seed))
    gate('actuators', gate_actuators(path))
    gate('drc', gate_drc(path))
    gate('route', gate_route(board))
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
    report.update(board=str(shown), board_sha256=sha,
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  builder_sha256=hashlib.sha256((ROOT / 'm3_design/r9_power.py').read_bytes()).hexdigest())
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:25]:
            print('    ', i)
    dc = report['dc']['evidence'].get('rows') or {}
    print('dc', {k: (v or {}).get('mohm') for k, v in dc.items()}, 'mOhm;',
          {k: (v or {}).get('rise_c') for k, v in dc.items()}, 'C;',
          'via max', max([(v or {}).get('via_max_a') or 0 for v in dc.values()] or [0]), 'A')
    sp = report['supply']['evidence'].get('paths', {})
    print('supply', {k: v.get('mohm') for k, v in sp.items()}, 'mOhm')
    f9 = report['f9']['evidence']
    print('f9', f9.get('rb_mohm'), 'mOhm,', f9.get('feed_estimate_nH'), 'nH,', f9.get('by_feed_nH'))
    print('route pending', report['route']['evidence'].get('pending'))
    ok = not any(fails.values())
    print('R9 power gate:', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
