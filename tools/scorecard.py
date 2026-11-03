#!/usr/bin/env python3
"""Simplicity scorecard of one surveyed board, optionally against a baseline survey (plain python3, no pcbnew).

usage: python3 tools/scorecard.py OUTDIR [--baseline BASE_OUTDIR | BASE.json] [--md OUT.md] [--json OUT.json]

Moved into tools/ in R8 build step 1 (from the R8 baseline survey, sources/r8_design/survey_baseline.md section 5).
--baseline takes a survey OUTDIR or a scorecard JSON this tool wrote (tools/scorecard_r7.json: the accepted R7 board
c872a3d3..., DC at 0.05 mm; tools/scorecard_r7_quick.json: the same with DC at 0.1 mm). The R8 targets of
r8_plan.md section 2 are reported beside each row (TARGETS): a soft report, never a gate; tools/check.sh is the gate.

OUTDIR is what run_survey.sh wrote for one board:
  survey.json                 survey_metrics.py
  route.json, route.txt       route_check.py --report (--routes)
  cref_self.json              critical_reference.py BOARD BOARD          (R6 net set and layer mapping)
  cref_self_ext.json          critical_reference.py BOARD BOARD --extended
  cref_vs_base*.json          critical_reference.py BASE BOARD [--extended]   (optional)
  dc_raw.txt, dc_bat.txt, dc_fet.txt   run_dc.sh (dc_solve.py --necks: resistance and equipotential-cut neck)
  gate.txt                    tools/check.sh BOARD                        (optional)
Every metric is defined in survey_baseline.md. With --baseline, each row gets the baseline value and the ratio, and
the simplicity index (100 = baseline, lower = simpler) is the geometric mean of the INDEX rows' ratios.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ipc2152 import ipc_dt, ipc_width  # noqa: E402,F401 (IPC-2152 fit shared with dc_solve --necks)


def load(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def dc(path):
    p = Path(path)
    if not p.exists():
        return None
    t = p.read_text()
    out = {}
    m = re.search(r'R = ([\d.]+) mOhm', t)
    out['mohm'] = float(m.group(1)) if m else None
    m = re.search(r'cuts: neck ([\d.]+) mm at level [\d.]+ on (\S+) \((\d+) %', t)
    if m:
        out['neck_mm'], out['neck_layer'], out['neck_share'] = float(m.group(1)), m.group(2), int(m.group(3))
        out['neck_dT'] = round(ipc_dt(out['neck_mm'], out['neck_layer']), 1)
        out['w20'] = round(ipc_width(20, out['neck_layer']), 2)
    m = re.search(r'cuts: median ([\d.]+) mm', t)
    out['median_mm'] = float(m.group(1)) if m else None
    m = re.search(r'cut box \(([^)]*)\)', t)
    out['neck_box'] = m.group(1) if m else None
    out['fail'] = 'FAIL' in t
    return out


def gate(path):
    p = Path(path)
    if not p.exists():
        return None
    t = p.read_text()
    m = re.search(r'DRC violations (\d+)\s+unconnected (\d+)\s+schematic parity (\d+)\s+ERC (\d+)', t)
    ex = re.search(r'exit (\d+)', t)
    rh = re.search(r'routing hygiene: (\d+) failing, (\d+) allowlisted', t)
    return dict(drc=int(m.group(1)) if m else None, unconnected=int(m.group(2)) if m else None,
                parity=int(m.group(3)) if m else None, erc=int(m.group(4)) if m else None,
                route_failing=int(rh.group(1)) if rh else None, route_allowlisted=int(rh.group(2)) if rh else None,
                exit=int(ex.group(1)) if ex else None)


def route(rep):
    if rep is None:
        return None
    inst = rep['instances']
    gated = len(rep['failures']) + len(rep['allowed']) + len(rep['leftovers']) + len(rep['leftovers_missing'])
    by = {}
    for d in inst:
        by[d['cat']] = by.get(d['cat'], 0) + 1
    rule_cats = ('off_angle', 'staircase', 'acute_angle', 'fold_back', 'dead_copper', 'pour_stub', 'dangling_via',
                 'critical_via_no_gnd', 'pour_sliver', 'pour_finger', 'pad_pour_cut')
    return dict(instances=len(inst), gated_category=gated, info=len(inst) - gated, failures=len(rep['failures']),
                allowlisted=len(rep['allowed']), leftovers=len(rep['leftovers']),
                leftovers_missing=len(rep['leftovers_missing']), stale=len(rep['stale']),
                agents3_rule_instances=sum(v for k, v in by.items() if k in rule_cats), by_category=dict(sorted(by.items())))


def build(d):
    s = load(d / 'survey.json')
    rc = route(load(d / 'route.json'))
    cr, ce = load(d / 'cref_self.json'), load(d / 'cref_self_ext.json')
    dcs = {k: dc(d / f'dc_{k}.txt') for k in ('raw', 'bat', 'fet')}
    g = gate(d / 'gate.txt')
    sc = dict(s['scorecard']) if s else {}
    sc['S10b_signal_bends_total'] = sum(s['bends']['signal'].get(k, 0) for k in ('b45', 'b90', 'acute', 'other')) if s else None
    if rc:
        sc.update(C1_route_gated_category_instances=rc['gated_category'], C2_route_info_instances=rc['info'],
                  C3_route_allowlisted=rc['allowlisted'], C4_route_leftovers=rc['leftovers'],
                  C5_route_failures=rc['failures'] + rc['leftovers_missing'] + rc['stale'],
                  C6_agents3_rule_instances=rc['agents3_rule_instances'])
    if cr:
        sc.update(R5_cref_r6_samples=cr['candidate_samples'], R6_cref_r6_unreferenced=cr['candidate_unreferenced'])
        if cr['candidate_samples']:
            sc['R6b_cref_r6_unreferenced_share'] = round(cr['candidate_unreferenced'] / cr['candidate_samples'], 4)
    if ce:
        sc.update(R7_cref_ext_samples=ce['candidate_samples'], R8_cref_ext_unreferenced=ce['candidate_unreferenced'])
    for k, v in dcs.items():
        if v:
            sc[f'D_{k}_mohm'] = v['mohm']
            sc[f'D_{k}_neck_mm'] = v.get('neck_mm')
            sc[f'D_{k}_neck_dT_C'] = v.get('neck_dT')
    necks = [v['neck_mm'] / v['w20'] for v in dcs.values() if v and v.get('neck_mm')]
    if necks:
        sc['D_min_neck_fraction_of_20C_width'] = round(min(necks), 3)
    if g:
        sc.update(G_gate_exit=g['exit'], G_drc=g['drc'], G_unconnected=g['unconnected'], G_parity=g['parity'], G_erc=g['erc'])
    return dict(scorecard=sc, route=rc, dc=dcs, gate=g)


# rows of the simplicity index: (key, 'lower' | 'higher' is better). Counts get +1 so a zero stays finite.
INDEX = [('S1_signal_track_mm', 'lower'), ('S4_signal_layer_change_vias', 'lower'), ('S7_detour_excess_mm', 'lower'),
         ('S10b_signal_bends_total', 'lower'), ('S12_critical_layer_changes', 'lower'),
         ('S15_in2_signal_track_mm', 'lower'), ('C1_route_gated_category_instances', 'lower'),
         ('C2_route_info_instances', 'lower'), ('R3_ref_ext_unreferenced_mm', 'lower'),
         ('P7_outer_gnd_islands_le1_via', 'lower'), ('P9_gnd_dist_p95_mm', 'lower'),
         ('D_min_neck_fraction_of_20C_width', 'higher')]


# r8_plan.md section 2 (R8 definition of done): (key, '<=' | '>=' | '==', target, note). C1/C3/C6 allow the one
# owner-accepted inherent item A8 (R8_DECISIONS D9); S8/S9 0 except nets forced round a keep-out (route_check lists
# those on the D10 baseline). Soft report only.
TARGETS = [
    ('C1_route_gated_category_instances', '<=', 1, 'hard gate: 0 but A8'),
    ('C2_route_info_instances', '<=', 80, ''),
    ('C3_route_allowlisted', '<=', 1, 'hard gate: A8 only'),
    ('C4_route_leftovers', '==', 0, 'hard gate'),
    ('C5_route_failures', '==', 0, 'hard gate'),
    ('C6_agents3_rule_instances', '<=', 1, 'hard gate: A8 only'),
    ('S1_signal_track_mm', '<=', 2300, ''),
    ('S4_signal_layer_change_vias', '<=', 75, ''),
    ('S6_detour_weighted', '<=', 1.18, ''),
    ('S7_detour_excess_mm', '<=', 350, ''),
    ('S8_nets_ratio_over_1_6', '==', 0, 'except keep-out-forced nets'),
    ('S9_nets_ratio_over_2', '==', 0, 'except keep-out-forced nets'),
    ('S10b_signal_bends_total', '<=', 400, ''),
    ('S12_critical_layer_changes', '<=', 32, ''),
    ('S15_in2_signal_track_mm', '==', 0, 'hard gate (check_r8 D20)'),
    ('S16_in1_track_mm', '==', 0, 'hard gate (check_r8 D20)'),
    ('S17_route_mst_total_mm', '<=', 1850, ''),
    ('P1_in1_gnd_coverage', '>=', 0.90, ''),
    ('P3b_in1_slots', '<=', 4, ''),
    ('P4_in2_regions', '<=', 5, ''),
    ('P6_in2_perimeter_mm', '<=', 900, ''),
    ('P7_outer_gnd_islands_le1_via', '==', 0, ''),
    ('P9_gnd_dist_p95_mm', '<=', 3.5, ''),
    ('P10_gnd_dist_max_mm', '<=', 7, ''),
    ('R1_ref_r6_unreferenced_mm', '<=', 5, ''),
    ('R3_ref_ext_unreferenced_mm', '<=', 15, ''),
    ('R6b_cref_r6_unreferenced_share', '<=', 0.08, 'critical_reference'),
    ('D_raw_neck_dT_C', '<=', 20, 'D12: >= 5.3 mm outer / 5.6 mm inner'),
    ('D_bat_neck_dT_C', '<=', 20, 'D12: >= 5.3 mm outer / 5.6 mm inner'),
    ('D_fet_neck_dT_C', '<=', 30, 'D12: >= 3.71 mm on B.Cu'),
    ('index_vs_baseline', '<=', 35, 'simplicity index'),
]


def target_rows(sc):
    """[(key, value, op, target, met (True / False / None when not measured), note)] for TARGETS."""
    out = []
    for key, op, want, note in TARGETS:
        v = sc.get(key)
        met = None if not isinstance(v, (int, float)) else (v <= want if op == '<=' else v >= want if op == '>=' else
                                                            v == want)
        out.append((key, v, op, want, met, note))
    return out


GROUP = 'GCSRPDQ'


def order(k):
    m = re.match(r'([A-Z])_?(\d*)([a-z]?)', k)
    g = GROUP.index(k[0]) if k[0] in GROUP else 9
    return (g, int(m.group(2)) if m and m.group(2) else 0, m.group(3) if m else '', k)


def compare(new, base):
    rows, logs = [], []
    for k in sorted(set(new) | set(base), key=order):
        a, b = new.get(k), base.get(k)
        ratio = None
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and b:
            ratio = round(a / b, 3)
        rows.append((k, a, b, ratio))
    for k, better in INDEX:
        a, b = new.get(k), base.get(k)
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            continue
        if isinstance(a, int) and isinstance(b, int):
            a, b = a + 1, b + 1
        if a <= 0 or b <= 0:
            continue
        logs.append(math.log(a / b) if better == 'lower' else math.log(b / a))
    idx = round(100 * math.exp(sum(logs) / len(logs)), 1) if logs else None
    return rows, idx


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('outdir')
    ap.add_argument('--baseline')
    ap.add_argument('--md')
    ap.add_argument('--json')
    a = ap.parse_args()
    d = Path(a.outdir)
    res = build(d)
    lines = [f'# Scorecard: {d}', '']
    if a.baseline:
        bp = Path(a.baseline)
        base = json.loads(bp.read_text()) if bp.is_file() else build(bp)
        rows, idx = compare(res['scorecard'], base['scorecard'])
        res['index_vs_baseline'] = idx
        lines += [f'Simplicity index vs baseline ({a.baseline}): **{idx}** (100 = baseline, lower = simpler)', '',
                  '| Metric | Board | Baseline | Ratio |', '|---|---:|---:|---:|']
        lines += [f'| {k} | {v} | {b} | {q if q is not None else ""} |' for k, v, b, q in rows]
    else:
        lines += ['| Metric | Value |', '|---|---:|'] + [f'| {k} | {v} |' for k, v in sorted(res['scorecard'].items(), key=lambda kv: order(kv[0]))]
    sc = dict(res['scorecard'], index_vs_baseline=res.get('index_vs_baseline'))
    rows = target_rows(sc)
    res['targets'] = [dict(key=k, value=v, op=op, target=t, met=m, note=n) for k, v, op, t, m, n in rows]
    lines += ['', f"R8 targets (r8_plan.md section 2; soft report): {sum(1 for r in rows if r[4])} met, "
              f"{sum(1 for r in rows if r[4] is False)} missed, {sum(1 for r in rows if r[4] is None)} not measured", '',
              '| Target | Board | Goal | Met | Note |', '|---|---:|---|---|---|']
    lines += [f"| {k} | {v} | {op} {t} | {'yes' if m else 'no' if m is False else '-'} | {n} |" for k, v, op, t, m, n in rows]
    txt = '\n'.join(lines) + '\n'
    if a.md:
        Path(a.md).write_text(txt)
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + '\n')
    print(txt)


if __name__ == '__main__':
    main()
