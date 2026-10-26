#!/usr/bin/env python3
"""R9 build step 5 gate: the CH1 pyro column (r9_plan.md section 4 step 5; R9_DECISIONS D-S5-*).

usage: <KiCad python3> -I m3_design/r9_pyro_check.py [board] [--report OUT.json] [--seed SEED.json]
       exit 0 = every gate passes
       --seed: reuse a rule_h_seed.py report of this board (bound by its board_sha256); without it the suite runs here

The board is r9_pyro.py's output. Gates (tools/check_r9.py, pyro_probe.py, bridge_table.py and rule_h_seed.py are
called, never restated or weakened; the step's own floors below are stricter than those tools):
  template    the board's copper on the step's nets, its GND and 3V3 copper drawn by r9_pyro equal the template
              regenerated from the pads (r9_pyro.copper): nothing missing, nothing extra, every via in place
  margins     pyro_probe passes (A-H, A2, the strict pad rules H+ / GS / AG) and every pair of rules A-H and A2 keeps
              the rule's minimum plus FLOOR (max(R8's margin, 0.2 mm): r9_plan section 2, Z1), the one recorded
              exception being GATE_N's entry into U1.3 between its no-net sentinel pins (U1.2 / U1.4: the LQFP's
              0.5 mm pitch and the courtyard 0.3 mm past the pad ends cap that gap at 0.41 mm; rule G holds there;
              D-S5-13)
  bridges     bridge_table: no forbidden pair, and no fires-class pair (a bridge that fires the igniter or bypasses
              the ARM break) between two parts closer than FIRES_MIN (1.5 mm)
  rule_h      tools/rule_h_seed.py on this board: three closest rule-H pairs x eight variants, every one caught
  gate_n      every copper item of another net within NEIGHBOUR (1.5 mm, the bridge table's reach) of PYRO1_GATE_N's
              copper, on its layer or one < 0.5 mm away through the stack, outside U1's courtyard and other than the
              gate network's and U1's own pads, is GND, has no net, or puts < 0.2 V on the gate in reset
              (bridge_table.gate_voltage); the P-7 reset-voltage table of the gate nets is the evidence
  sense       the divider-fault analysis' layout preconditions (survey 9.4 item 4): every sense lane's neighbours
              within NEIGHBOUR listed; the MCU sides (past the 4.7 k) have no battery-live, RAW_ACT, armed or other
              above-logic copper within NEIGHBOUR
  armed       r9_plan section 2 done rows X2 / X2b / X2c: no foreign net (not a CH1 net, GND or RAW_ACT) within 3 mm
              of bus, igniter or drain copper, on its layer or in plan view (tools/r9_extra_metrics.py's method)
  contract    check_r9 LC-1, P-0 ... P-11 (P-4 with this board's seeded report), M-6, R-13, K-power-pyro, K-copper,
              K-inner, K-actuators: every rule holds
  actuators   m3_design/check_actuators.py on the board and m3.kicad_dru: no finding
  drc         kicad-cli DRC with schematic parity, every severity: no violation but step 8's silkscreen classes, no
              parity item, no unconnected item on a net this step completes (r9_pyro.NETS)
  route       tools/route_check.py, profile r9: no failing instance and no unrecorded leftover, but the pending
              items of the step's own GND and 3V3 copper (dangling_via / dead_copper) that wait for step 8's In1 GND
              pour and step 6's In2 3V3 region: each one is a via or a track of the template, nothing else
"""
import argparse
import collections
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import bridge_table as BT  # noqa: E402
import check_actuators as CA  # noqa: E402
import check_r8 as r8  # noqa: E402
import check_r9 as C9  # noqa: E402
import pyro_probe as PP  # noqa: E402
import route_check as rc  # noqa: E402
import r9_pyro  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
DRC_DEFERRED = {'silk_over_copper', 'silk_overlap', 'silk_edge_clearance'}   # r9_post.py (step 8)
CONTRACT_RULES = ('LC-1',) + tuple(f'P-{k}' for k in range(0, 12)) + ('M-6', 'R-13', 'K-power-pyro', 'K-copper',
                                                                        'K-inner', 'K-actuators')
# margin floors: max(R8's margin, 0.2 mm) per rule (r9_plan section 2 Z1; R8: A .001 B .17 C .077 D .001 E .30 F .20
# G .000 H .025; A2 had no R8 pair)
FLOOR = {'A': 0.2, 'B': 0.2, 'C': 0.2, 'D': 0.2, 'E': 0.30, 'F': 0.2, 'G': 0.2, 'H': 0.2, 'A2': 0.2}
FIRES_MIN = 1.5
NEIGHBOUR = 1.5
PENDING = {'dangling_via', 'dead_copper'}        # the step's GND / 3V3 copper before steps 6 and 8 (route gate)


def r4(v):
    return round(v, 4)


def gate_template(b):
    P = r9_pyro.Pads(b)
    tracks, vias = r9_pyro.copper(P)
    want_t = collections.Counter()
    for net, layer, w, pts in tracks:
        for a, c in zip(pts, pts[1:]):
            want_t[(net, layer, round(w, 3), tuple(sorted((a, c))))] += 1
    want_v = {(net, at, size) for net, at, size, _ in vias}
    have_t, have_v = collections.Counter(), set()
    own = set(r9_pyro.NETS)
    template_pts = {k[3] for k in want_t}
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
        key = (net, 'F' if t.GetLayer() == pcbnew.F_Cu else 'B' if t.GetLayer() == pcbnew.B_Cu else
               b.GetLayerName(t.GetLayer()), round(mm(t.GetWidth()), 3), tuple(sorted((a, c))))
        if net in own or (net in ('GND', '3V3') and key[3] in template_pts):
            have_t[key] += 1
    issues = [f'template: missing {k[0]} {k[1]} w{k[2]} {k[3]}' for k in sorted(want_t - have_t)]
    issues += [f'template: extra {k[0]} {k[1]} w{k[2]} {k[3]}' for k in sorted(have_t - want_t)]
    issues += [f'template: missing via {k}' for k in sorted(want_v - have_v)]
    issues += [f'template: extra via {k}' for k in sorted(have_v - want_v)]
    return issues, dict(segments=sum(want_t.values()), vias=len(want_v),
                        length_mm=round(sum(math.dist(*k[3]) for k in want_t.elements()), 2))


def sentinel_entry(row, b):
    """The recorded G exception: GATE_N copper against U1's no-net pins flanking U1.3 (D-S5-13)."""
    a, c = row['a'], row['b']
    gate, other = (a, c) if 'PYRO1_GATE_N' in a else (c, a)
    if 'PYRO1_GATE_N' not in gate or not other.startswith('U1.'):
        return False
    num = other.split()[0].split('.')[1]
    p = b.FindFootprintByReference('U1').FindPadByNumber(num)
    return num in ('2', '4') and p.GetNetname().startswith('unconnected-')


def gate_margins(b):
    res = PP.probe(b)
    issues = PP.issues_of(res)
    raised = {k: (v[0] + FLOOR[k],) + tuple(v[1:]) for k, v in PP.RULES.items() if k in FLOOR}
    rows = PP.probe(b, rules=raised, limit_pairs=10 ** 6)
    excepted = []
    for k, r in rows.items():
        for v in r['violations']:
            if k == 'G' and sentinel_entry(v, b):
                excepted.append(dict(rule=k, **v))
                continue
            issues.append(f"margin {k}: {v['a']} to {v['b']} on {v['layer']} is {v['mm']:.3f} mm < "
                          f"{PP.RULES[k][0]} + {FLOOR[k]} mm")
    ev = {k: dict(minimum=v['minimum'], closest=v['closest'], margin=v['margin']) for k, v in res.items()}
    return issues, dict(rules=ev, floors=FLOOR, excepted=excepted)


def fires_class(cons):
    return cons.startswith('FIRES') or 'BYPASSES' in cons


def gate_bridges(b):
    rows = BT.table(b)
    issues = BT.issues_of(rows)
    for r in rows:
        if not r['own_part'] and fires_class(r['consequence']) and r['gap'] < FIRES_MIN - 1e-3:
            issues.append(f"bridges: fires-class {r['a']} -- {r['b']} {r['gap']:.3f} mm < {FIRES_MIN}: "
                          f"{r['consequence']}")
    fires = [f"{r['gap']:.3f} {r['a']} -- {r['b']}: {r['consequence']}" for r in rows if fires_class(r['consequence'])]
    return issues, dict(pairs=len(rows), forbidden=sum(1 for r in rows if r['forbidden']),
                        fires_class=fires,
                        under_1mm=[f"{r['gap']:.3f} {r['a']} -- {r['b']}: {r['consequence']}" for r in rows
                                   if r['gap'] < BT.BRIDGE and not r['own_part']])


def run_seed(path, report):
    if report is None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'seed.json'
            subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'tools/rule_h_seed.py'), str(path), '--json',
                            str(out)], capture_output=True)
            return json.loads(out.read_text()) if out.is_file() else None
    return json.loads(Path(report).read_text())


def gate_rule_h(seed, sha):
    if seed is None:
        return ['rule_h: tools/rule_h_seed.py produced no report'], {}
    issues = [f'rule_h: {i}' for i in seed.get('issues', [])]
    if seed.get('board_sha256') != sha:
        issues.append('rule_h: the seeded report is not bound to this board')
    if not seed.get('pairs'):
        issues.append('rule_h: no pair seeded')
    return issues, dict(pairs=[p.get('pair') for p in seed.get('pairs', [])],
                        variants=sorted({v for p in seed.get('pairs', []) for v in p.get('variants', {})}))


def gate_neighbours(b, ctx):
    """PYRO1_GATE_N's neighbours within NEIGHBOUR mm (outside U1's courtyard; the gate network's and U1's own pads
    excepted): GND, no net, or < 0.2 V on the gate in reset."""
    pairs = ctx.layer_pairs()
    scope = PP.Scope(b)
    issues, table = [], {}
    gate = [it for it in ctx.items if it[1] == 'PYRO1_GATE_N']
    others = [it for it in ctx.items if it[1] not in C9.GATES and it[1]]
    for g in gate:
        poly = C9.item_poly(g)
        if scope.u1 is not None:
            poly.BooleanSubtract(scope.u1)
        if not poly.OutlineCount() or C9.area_mm2(poly) < 1e-4:
            continue
        for o in others:
            if (g[2], o[2]) not in pairs:
                continue
            if isinstance(o[4], pcbnew.PAD) and o[4].GetParentFootprint().GetReference() in C9.GATE_PARTS + ('U1',):
                continue
            if PP._bbox_gap(poly, o[3]) > NEIGHBOUR:
                continue
            d = r8.min_gap(poly, o[3], NEIGHBOUR)
            if d is None:
                continue
            v = BT.gate_voltage(o[1], 'PYRO1_GATE_N')
            key = o[1]
            if key not in table or d < table[key]['mm']:
                table[key] = dict(mm=round(d, 3), item=o[0], v_reset=round(v, 3))
            if o[1] != 'GND' and not o[1].startswith('unconnected-') and v >= BT.GATE_RESET_MAX:
                issues.append(f'gate_n: {o[1]} {o[0]} ({b.GetLayerName(o[2])}) is {d:.3f} mm from PYRO1_GATE_N '
                              f'{g[0]}: {v:.2f} V on the gate in reset (neighbours must be GND or < '
                              f'{BT.GATE_RESET_MAX} V within {NEIGHBOUR} mm)')
    p7 = C9.p7(ctx)[1]['reset_voltage_table']
    return sorted(set(issues)), dict(neighbours=table, p7_table=p7[:12])


SENSE_NETS = ('ARM1_SENSE', 'PYRO1_CONT', 'ARM1_SENSE_MID', 'PYRO1_CONT_MID', 'PYRO1_COLD', 'ARM1_SENSE_MCU',
              'PYRO1_CONT_MCU')
HIGH = set(BT.BATTERY) | set(BT.ARMED) | {'BAT_IN', 'ACT_FET_S', 'RAW_PROTECTED', 'VLOGIC', 'CAM_5V', 'VBUS'}


def gate_sense(b, ctx):
    """Survey 9.4 item 4's layout preconditions of the divider-fault analysis: each sense lane's neighbours within
    NEIGHBOUR mm (same layer or < 0.5 mm away) listed (a bridge there sees the divider's Thevenin source and the 4.7 k);
    the MCU sides (past the 4.7 k, nothing limits a short) have none above the 3.3 V logic rail."""
    pairs = ctx.layer_pairs()
    issues, table = [], {}
    lanes = [it for it in ctx.items if it[1] in SENSE_NETS]
    others = [it for it in ctx.items if it[1] and it[1] not in SENSE_NETS]
    for s_ in lanes:
        for o in others:
            if (s_[2], o[2]) not in pairs or PP._bbox_gap(s_[3], o[3]) > NEIGHBOUR:
                continue
            if isinstance(s_[4], pcbnew.PAD) and isinstance(o[4], pcbnew.PAD) and \
                    s_[4].GetParentFootprint().GetReference() == o[4].GetParentFootprint().GetReference():
                continue                                  # a part's own pads (the part fault, F8)
            d = r8.min_gap(s_[3], o[3], NEIGHBOUR)
            if d is None:
                continue
            key = f'{s_[1]} / {o[1]}'
            if key not in table or d < table[key][0]:
                table[key] = (round(d, 3), s_[0], o[0])
            if s_[1].endswith('_MCU') and o[1] in HIGH:
                issues.append(f'sense: {s_[1]} {s_[0]} is {d:.3f} mm from {o[1]} {o[0]} (an MCU side next to copper '
                              f'above the logic rail, within {NEIGHBOUR} mm)')
    return sorted(set(issues)), dict(neighbours=dict(sorted(table.items(), key=lambda kv: kv[1][0])))


ARMED_REACH = 3.0
OWN = ('PYRO', 'ARM')


def gate_armed(b, ctx):
    """r9_plan section 2 done rows X2 / X2b / X2c (tools/r9_extra_metrics.py's X2, the same method): no net but the
    CH1 nets, GND and RAW_ACT (the ARM break's source side) has copper within ARMED_REACH of armed-live copper, on its
    layer or in plan view on any layer; a no-net pad is listed, not gated (R8 counted them apart)."""
    live = [it for it in ctx.items if it[1] in BT.ARMED]
    issues, near, nc = [], {}, {}
    for it in ctx.items:
        n = it[1]
        if not n or n in BT.ARMED or n.startswith(OWN) or n in ('GND', 'RAW_ACT'):
            continue
        for lv in live:
            if PP._bbox_gap(lv[3], it[3]) > ARMED_REACH:
                continue
            g = r8.min_gap(lv[3], it[3], ARMED_REACH)
            if g is None:
                continue
            row = (round(g, 3), lv[0], it[0], 'same layer' if lv[2] == it[2] else 'plan view')
            tgt = nc if n.startswith('unconnected-') else near
            if n not in tgt or g < tgt[n][0]:
                tgt[n] = row
    issues = [f'armed: {n} {v[2]} is {v[0]:.3f} mm from armed-live {v[1]} ({v[3]}); none within {ARMED_REACH} mm '
              f'(X2 / X2b)' for n, v in sorted(near.items())]
    return issues, dict(foreign=near, no_net_pads=nc)


def gate_contract(b, path, seed):
    res = C9.check_board(b, path.parent, path, only=set(CONTRACT_RULES), seed=seed,
                         board_sha=hashlib.sha256(path.read_bytes()).hexdigest())
    return res['issues'], {k: v['evidence'] for k, v in res['rules'].items()}


def gate_actuators(path):
    found = CA.check(path.read_text(), path.with_suffix('.kicad_dru').read_text())
    return [f'actuators: {i}' for i in found], dict(findings=len(found))


def gate_drc(path, pending_vias):
    """pending_vias: [(net, (x, y))] the step's GND / 3V3 vias that wait for steps 6 and 8 (via_dangling until then)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(path)], capture_output=True)
        rep = json.loads(out.read_text())
    bad, deferred, pending = [], collections.Counter(), []
    for v in rep['violations']:
        if v['type'] in DRC_DEFERRED:
            deferred[v['type']] += 1
            continue
        if v['type'] == 'via_dangling' and len(v['items']) == 1 and \
                any(math.dist((v['items'][0]['pos']['x'], v['items'][0]['pos']['y']), at) < 2e-3 and
                    f'[{net}]' in v['items'][0]['description'] for net, at in pending_vias):
            pending.append(f"{v['items'][0]['description']} at ({v['items'][0]['pos']['x']}, {v['items'][0]['pos']['y']})")
            continue
        bad.append(f"drc: {v['type']}: " + ' | '.join(i['description'] for i in v['items']))
    for p in rep.get('schematic_parity', []):
        bad.append(f"drc: parity {p['type']}: " + ' | '.join(i['description'] for i in p.get('items', [])))
    own = 0
    for u in rep.get('unconnected_items', []):
        nets = {i['description'].split('[')[1].split(']')[0] for i in u['items'] if '[' in i['description']}
        if nets & set(r9_pyro.NETS):
            own += 1
            bad.append('drc: unconnected ' + ' | '.join(i['description'] for i in u['items']))
    return bad, dict(unconnected_total=len(rep['unconnected_items']), unconnected_step=own, deferred=dict(deferred),
                     pending=pending)


def gate_route(b):
    P = r9_pyro.Pads(b)
    tracks, vias = r9_pyro.copper(P)
    pend_v = {at for net, at, _, _ in vias if net in ('GND', '3V3')}
    pend_t = [(net, pts) for net, _, _, pts in tracks if net in ('GND', '3V3')]

    def on_pending(d):
        p = (round(d['x'], 3), round(d['y'], 3))
        if d['net'] not in ('GND', '3V3'):
            return False
        if any(math.dist(p, v) < 2e-3 for v in pend_v):
            return True
        return any(d['net'] == net and C9.seg_point_dist(p, a, c) < 2e-3 for net, pts in pend_t
                   for a, c in zip(pts, pts[1:]))
    rc.set_profile('r9')
    inst = rc.scan(b, [])
    bumps, searched = rc.bump_audit(b)
    inst += bumps
    failures, allowed, stale = rc.evaluate(inst)
    _, missing, _ = rc.leftover_check(inst)
    pending = [d for d in failures if d['cat'] in PENDING and on_pending(d)]
    issues = [f"route: {d['cat']} {d['net']} {d['layer']} ({d['x']}, {d['y']})" for d in failures if d not in pending]
    issues += [f"route: unrecorded leftover {d['cat']} {d['net']} {d['layer']} ({d['x']}, {d['y']})" for d in missing]
    issues += [f'route: allowlist entry {e[:4]}' for e in allowed + stale]
    mine = [d for d in inst if d['net'] in r9_pyro.NETS]
    return issues, dict(instances=len(inst), pending=[f"{d['cat']} {d['net']} ({d['x']}, {d['y']})" for d in pending],
                        step_nets=dict(collections.Counter(d['cat'] for d in mine)), bump_windows=searched)


def evidence(b):
    """Record figures: the exit lanes' track (Z2r9), the fire loop's board copper resistance (Calc: 1 oz copper at
    85 C, check_r9.SHEET_R per square, the bars only)."""
    L = collections.Counter()
    sq = collections.Counter()
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            continue
        n = t.GetNetname()
        L[n] += mm(t.GetLength())
        if n in ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT') and abs(mm(t.GetWidth()) - r9_pyro.W_ARMED) < 1e-6:
            sq[n] += mm(t.GetLength()) / r9_pyro.W_ARMED
    return dict(exit_track_mm=round(sum(L[n] for n in C9.EXIT_NETS), 2),
                track_mm={n: round(L[n], 2) for n in sorted(L) if n in r9_pyro.NETS},
                fire_bar_mohm={n: round(1000 * C9.SHEET_R * s, 2) for n, s in sq.items()},
                block_bbox=[round(mm(v), 2) for v in (lambda bb: (bb.GetLeft(), bb.GetTop(), bb.GetRight(),
                                                                  bb.GetBottom()))(
                    [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK'][0]
                    .Outline().BBox())])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--report', type=Path)
    ap.add_argument('--seed', type=Path, help='a rule_h_seed.py report of this board')
    args = ap.parse_args()
    path = args.board.resolve()
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    seed = run_seed(path, args.seed)
    board = pcbnew.LoadBoard(str(path))
    ctx = C9.Ctx(board, path.parent, path)
    report, fails = {}, {}

    def gate(name, result):
        issues, ev = result
        report[name] = dict(ok=not issues, issues=issues, evidence=ev)
        fails[name] = len(issues)
    gate('template', gate_template(board))
    gate('margins', gate_margins(board))
    gate('bridges', gate_bridges(board))
    gate('rule_h', gate_rule_h(seed, sha))
    gate('gate_n', gate_neighbours(board, ctx))
    gate('sense', gate_sense(board, ctx))
    gate('armed', gate_armed(board, ctx))
    gate('contract', gate_contract(board, path, seed))
    gate('actuators', gate_actuators(path))
    pend = [(net, at) for net, at, _, _ in r9_pyro.copper(r9_pyro.Pads(board))[1] if net in ('GND', '3V3')]
    gate('drc', gate_drc(path, pend))
    gate('route', gate_route(board))
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
    report.update(board=str(shown), board_sha256=sha, figures=evidence(board),
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  builder_sha256=hashlib.sha256((ROOT / 'm3_design/r9_pyro.py').read_bytes()).hexdigest())
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:25]:
            print('    ', i)
    m = report['margins']['evidence']['rules']
    print('margins', {k: v['margin'] for k, v in m.items()}, 'excepted',
          [f"{e['a']} / {e['b']} {e['mm']:.3f}" for e in report['margins']['evidence']['excepted']])
    print('route pending', report['route']['evidence'].get('pending'))
    ok = not any(fails.values())
    print('R9 pyro block gate:', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
