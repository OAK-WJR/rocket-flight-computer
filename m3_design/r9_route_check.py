#!/usr/bin/env python3
"""R9 build step 7 gate, run after each routing family (r9_plan.md section 4 step 7; R9_DECISIONS D-S7-*).

usage: <KiCad python3> -I m3_design/r9_route_check.py FAMILY [board] [--report OUT.json] [--seed SEED.json]
       exit 0 = every gate passes

The board is r9_route.py's output after FAMILY: steps 4-6 and every family up to FAMILY (r9_route.FAMILIES order).
"Done" below means those families. Gates (tools/check_r9.py, route_check.py, check_actuators.py and the step-5 gate's
pyro functions are called, never restated or weakened):
  template   each done family's copper (r9_route.build dry run: tracks and vias) is on the board, and the done
             families' NETS carry no other copper
  drc        kicad-cli DRC with schematic parity, every severity: no violation but step 8's silkscreen classes and the
             via_dangling of a pending GND via (steps 5 / 6 and the done families' PENDING, which wait for step 8's
             In1 pour); no parity item; no unconnected item on a done family's NETS, and every rail / continued pad a
             done family's PADS names joined (GND's are step 8's)
  route      tools/route_check.py, profile r9 (empty allowlist and leftover list): no failing instance and no
             unrecorded leftover but a pending GND via's dangling_via / dead_copper (and its strap's)
  budget     this family's figures within its BUDGET: signal track length, signal vias, critical layer changes, the
             worst copper / octilinear-MST ratio of a net more than route_check's slack longer than its MST
             (route_check's keep-out-aware baseline where it applies)
  totals     the board's signal vias (every via of a net that is neither GND nor route_check's power class) within
             the scorecard's S4 done row (<= 70, owner decision 4); the stretch row (<= 55) and the running length /
             layer-change totals are reported
  pyro       the step-5 gate's functions: the pyro margins (A-H, A2), the bridge table, GATE_N's neighbours (GND or
             <= 0.2 V in reset within 1.5 mm, outside U1's courtyard), the sense lanes' MCU sides, no foreign net within
             3 mm of armed copper (X2)
  contract   check_r9: every rule but M-2 (placement-bound, step 3's gate) and K-legends (step 8), P-4 with this board's
             seeded report; K-contract's route-only items of a family not yet done (ROUTE_ONLY) are reported, not
             failed. This holds P-7 (the gate guard), D19 / D18 / D85 (K-power-pyro), D20 (K-inner), R-1 ... R-13
  actuators  m3_design/check_actuators.py on the board and m3.kicad_dru: no finding
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
import r9_power_check as PW  # noqa: E402
import r9_pyro  # noqa: E402
import r9_pyro_check as PC  # noqa: E402
import r9_route as RT  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
DRC_DEFERRED = {'silk_over_copper', 'silk_overlap', 'silk_edge_clearance'}   # r9_post.py (step 8)
CONTRACT_SKIP = {'M-2', 'K-legends'}
# check_r9 findings that only a later family's copper settles: (pattern, family)
ROUTE_ONLY = [
    (re.compile(r'^K-contract: C(100|93): requires (local bypass within \d mm of U12\.\d+ and direct copper|'
                r'direct local GND return)'), 'camera'),
]
S4_DONE, S4_STRETCH = 70, 55                 # r9_scorecard S4_signal_layer_change_vias (owner decision 4)
PAD_RE = re.compile(r'Pad (\S+) \[([^\]]+)\] of (\S+)')


def r4(v):
    return round(v, 4)


def done_families(family):
    return RT.FAMILIES[:RT.FAMILIES.index(family) + 1]


def family_nets(done):
    return {n for f in done for n in RT.load_family(f).NETS}


def pending_vias(done):
    pend = [(r4(x), r4(y)) for x, y in PW.pending_vias()]
    for f in done:
        pend += [(r4(x), r4(y)) for x, y in getattr(RT.load_family(f), 'PENDING', ())]
    return pend


def seg_key(net, layer, w, a, c):
    return (net, layer, round(w, 3), tuple(sorted((a, c))))


LAYER_NAME = {pcbnew.F_Cu: 'F', pcbnew.B_Cu: 'B', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2'}


def board_copper(b):
    segs, vias = set(), {}
    for t in b.GetTracks():
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            vias[(r4(mm(t.GetPosition().x)), r4(mm(t.GetPosition().y)))] = net
        elif t.GetClass() == 'PCB_TRACK':
            a = (r4(mm(t.GetStart().x)), r4(mm(t.GetStart().y)))
            c = (r4(mm(t.GetEnd().x)), r4(mm(t.GetEnd().y)))
            segs.add(seg_key(net, LAYER_NAME.get(t.GetLayer(), '?'), mm(t.GetWidth()), a, c))
    return segs, vias


def gate_template(b, done):
    segs, vias = board_copper(b)
    issues, mine, ev = [], set(), {}
    for f in done:
        d = RT.build(b, f, dry=True)
        want = {seg_key(*t) for t in d.tracks}
        mine |= want
        miss = sorted(want - segs)
        issues += [f'template {f}: segment not on the board {m}' for m in miss[:10]]
        issues += [f'template {f}: via {at} ({net}) not on the board' for at, net in d.vias.items()
                   if vias.get(at) != net]
        issues += [f'template {f}: a via is still at {old}, which the family moved' for net, old in d.moved
                   if old in vias and old not in d.vias]
        ev[f] = dict(segments=len(want), vias=len(d.vias), moved=len(d.moved))
    own = family_nets(done)
    extra = sorted(s for s in segs if s[0] in own and s not in mine)
    issues += [f'template: copper on a family net that no family table draws {s}' for s in extra[:10]]
    return issues, ev


def joined_pads(done):
    """The rail / continued pads the done families' PADS say they join: {net: {REF.PAD}}. GND is not among them: a
    family's GND pads hang on its PENDING vias until step 8's In1 pour joins them (r9_ground_check gates GND)."""
    out = collections.defaultdict(set)
    for f in done:
        fam = RT.load_family(f)
        shared = (set(fam.RAILS) | set(getattr(fam, 'CONTINUES', ()))) - {'GND'}
        for ref, num, net, _ in getattr(fam, 'PADS', ()):
            if net in shared:
                out[net].add(f'{ref}.{num}')
    return out


def gate_drc(path, done):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(path)], capture_output=True)
        if not out.is_file():
            return ['drc: kicad-cli produced no report'], {}
        rep = json.loads(out.read_text())
    return judge_drc(rep, done)


def judge_drc(rep, done):
    pend = pending_vias(done)
    nets, joined = family_nets(done), joined_pads(done)
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
    open_nets = collections.Counter()
    for u in rep.get('unconnected_items', []):
        un = {i['description'].split('[')[1].split(']')[0] for i in u['items'] if '[' in i['description']}
        for n in un:
            open_nets[n] += 1
        if un & nets:
            bad.append('drc: unconnected ' + ' | '.join(i['description'] for i in u['items']))
            continue
        pads = {f'{m.group(3)}.{m.group(1)}' for i in u['items'] for m in [PAD_RE.search(i['description'])] if m}
        for n in un & set(joined):
            hit = sorted(pads & joined[n])
            if hit:
                bad.append(f'drc: {n} pad(s) {hit} a done family joins are unconnected: ' +
                           ' | '.join(i['description'] for i in u['items']))
    return bad, dict(unconnected_total=len(rep['unconnected_items']), deferred=dict(deferred), pending_vias=pending,
                     open_elsewhere=dict(sorted(open_nets.items())))


def gnd_straps(b, done, pend):
    """GND track chains joined to a pending via (their dead_copper waits for the same pour)."""
    segs = [(a, c) for net, layer, w, a, c in RP.build(b, dry=True).tracks if net == 'GND']
    segs += [(a, c) for net, _, _, pts in r9_pyro.copper(r9_pyro.Pads(b))[0] if net == 'GND'
             for a, c in zip(pts, pts[1:])]
    for f in done:
        segs += [(a, c) for net, layer, w, a, c in RT.build(b, f, dry=True).tracks if net == 'GND']
    return PW.chains(segs, pend)


def gate_route(b, done):
    pend = pending_vias(done)
    straps = gnd_straps(b, done, pend)

    def on_pending(x):
        p = (round(x['x'], 4), round(x['y'], 4))
        if x['net'] != 'GND' or x['cat'] not in ('dangling_via', 'dead_copper'):
            return False
        return any(math.dist(p, v) < 2e-3 for v in pend) or \
            any(C9.seg_point_dist(p, a, c) < 2e-3 for a, c in straps)
    rc.set_profile('r9')
    baseline = []
    inst = rc.scan(b, baseline)
    bumps, searched = rc.bump_audit(b)
    inst += bumps
    failures, allowed, stale = rc.evaluate(inst)
    _, missing, _ = rc.leftover_check(inst)
    pending = [x for x in failures if on_pending(x)]
    issues = [f"route: {x['cat']} {x['net']} {x['layer']} ({x['x']}, {x['y']})" for x in failures if x not in pending]
    issues += [f"route: unrecorded leftover {x['cat']} {x['net']} {x['layer']} ({x['x']}, {x['y']})" for x in missing]
    issues += [f'route: allowlist entry {e[:4]}' for e in allowed + stale]
    own = family_nets(done)
    info = collections.Counter(x['cat'] for x in inst if x['net'] in own and x['cat'] in rc.INFO)
    return issues, dict(instances=len(inst), pending=[f"{x['cat']} {x['net']} ({x['x']}, {x['y']})" for x in pending],
                        information_on_family_nets=dict(info), bump_windows=searched), baseline


def bends(tracks):
    """Direction changes at nodes where exactly two segments of one net and layer meet."""
    ends = collections.defaultdict(list)
    for t in tracks:
        a = (round(mm(t.GetStart().x), 3), round(mm(t.GetStart().y), 3))
        c = (round(mm(t.GetEnd().x), 3), round(mm(t.GetEnd().y), 3))
        if a == c:
            continue
        ends[(t.GetLayer(), a)].append(math.atan2(c[1] - a[1], c[0] - a[0]))
        ends[(t.GetLayer(), c)].append(math.atan2(a[1] - c[1], a[0] - c[0]))
    n = 0
    for dirs in ends.values():
        if len(dirs) == 2:
            d = abs(dirs[0] - dirs[1]) % (2 * math.pi)
            if abs(d - math.pi) > 1e-3:
                n += 1
    return n


def record(b, nets, baseline):
    """Per-net and family figures of a family's NETS (all their copper is the family's: template gate)."""
    keepout = {x['net']: x['keepout_mst_mm'] for x in baseline}
    nc = rc.collect(b, set(nets))
    per = {}
    for net in sorted(nets):
        tr = [t for t in b.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_TRACK']
        vias = [t for t in b.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_VIA']
        r = rc.net_route(nc[net]) if net in nc else None
        mst = keepout.get(net, r['mst']) if r else None
        per[net] = dict(len_mm=round(sum(mm(t.GetLength()) for t in tr), 2), vias=len(vias), bends=bends(tr),
                        ratio=round(r['len'] / mst, 3) if r and mst else None,
                        excess_mm=round(r['len'] - mst, 2) if r and mst else None,
                        critical=rc.net_class(net) in rc.SIGNAL_CRITICAL, signal=rc.net_class(net) != 'power')
    fam = dict(signal_track_mm=round(sum(v['len_mm'] for v in per.values() if v['signal']), 1),
               signal_vias=sum(v['vias'] for v in per.values() if v['signal']),
               critical_layer_changes=sum(v['vias'] for v in per.values() if v['critical']),
               bends=sum(v['bends'] for v in per.values() if v['signal']),
               worst_ratio=max((v['ratio'] if (v['excess_mm'] or 0) > rc.DETOUR_SLACK else min(v['ratio'], 1.0)
                                for v in per.values() if v['ratio']), default=None))
    return fam, per


def gate_budget(b, family, baseline):
    fam = RT.load_family(family)
    fig, per = record(b, set(fam.NETS), baseline)
    issues = []
    for key, got in (('length_mm', fig['signal_track_mm']), ('vias', fig['signal_vias']),
                     ('critical_layer_changes', fig['critical_layer_changes']), ('ratio', fig['worst_ratio'])):
        lim = fam.BUDGET.get(key)
        if lim is not None and got is not None and got > lim + 1e-9:
            issues.append(f'budget: {key} {got} over the family budget {lim}')
    return issues, dict(family=fig, budget=fam.BUDGET, nets=per)


def gate_totals(b, done, baseline):
    sig = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() != 'GND' and
           rc.net_class(t.GetNetname()) != 'power']
    issues = [] if len(sig) <= S4_DONE else [f'totals: {len(sig)} signal vias over the S4 done row ({S4_DONE})']
    run = collections.Counter()
    for f in done:
        fig, _ = record(b, set(RT.load_family(f).NETS), baseline)
        for k in ('signal_track_mm', 'signal_vias', 'critical_layer_changes', 'bends'):
            run[k] += fig[k]
    return issues, dict(board_signal_vias=len(sig), s4_done=S4_DONE, s4_stretch=S4_STRETCH,
                        stretch_met=len(sig) <= S4_STRETCH, by_net=dict(collections.Counter(t.GetNetname() for t in sig)),
                        families_so_far={k: round(v, 1) for k, v in run.items()})


def gate_contract(b, path, seed, done):
    only = {rid for rid, _, _ in C9.RULES} - CONTRACT_SKIP
    res = C9.check_board(b, path.parent, path, only=only, seed=seed,
                         board_sha=hashlib.sha256(path.read_bytes()).hexdigest())
    issues, deferred = [], []
    for i in res['issues']:
        later = [f for rx, f in ROUTE_ONLY if rx.match(i) and f not in done]
        (deferred if later else issues).append(i)
    ev = {k: v['evidence'] for k, v in res['rules'].items()}
    ev['deferred_to_later_family'] = deferred
    return issues, ev


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('family', choices=RT.FAMILIES)
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--report', type=Path)
    ap.add_argument('--seed', type=Path, help='a rule_h_seed.py report of this board')
    args = ap.parse_args()
    path = args.board.resolve()
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    done = done_families(args.family)
    seed = PC.run_seed(path, args.seed)
    board = pcbnew.LoadBoard(str(path))
    ctx = C9.Ctx(board, path.parent, path)
    report, fails = {}, {}

    def gate(name, result):
        issues, ev = result
        report[name] = dict(ok=not issues, issues=issues, evidence=ev)
        fails[name] = len(issues)
    gate('template', gate_template(board, done))
    gate('drc', gate_drc(path, done))
    issues, ev, baseline = gate_route(board, done)
    gate('route', (issues, ev))
    gate('budget', gate_budget(board, args.family, baseline))
    gate('totals', gate_totals(board, done, baseline))
    gate('pyro', PW.gate_pyro(board, ctx))
    gate('contract', gate_contract(board, path, seed, done))
    gate('actuators', PW.gate_actuators(path))
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name   # no local absolute paths (AGENTS.md)
    report.update(family=args.family, done=list(done), board=str(shown), board_sha256=sha,
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  family_sha256=hashlib.sha256((ROOT / f'm3_design/r9_route_{args.family}.py').read_bytes()).hexdigest())
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:25]:
            print('    ', i)
    print('family', args.family, report['budget']['evidence']['family'], 'budget', report['budget']['evidence']['budget'])
    tot = report['totals']['evidence']
    print('board signal vias', tot['board_signal_vias'], f'(S4 done <= {S4_DONE}, stretch <= {S4_STRETCH});',
          'families so far', tot['families_so_far'])
    print('route pending', report['route']['evidence'].get('pending'))
    ok = not any(fails.values())
    print(f'R9 route gate ({args.family}):', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
