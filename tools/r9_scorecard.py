#!/usr/bin/env python3
"""R9 scorecard of one surveyed board against the R8 baseline (plain python3, no pcbnew).

usage: python3 r9_scorecard.py OUTDIR [--baseline R8_OUTDIR | R8_scorecard.json] [--md OUT.md] [--json OUT.json]
       [--tools REPO/tools]

OUTDIR is what tools/run_r9_survey.sh wrote: the repo survey (run_survey.sh: survey.json, route.json/.txt,
cref_self*.json, dc_*.txt, gate.txt) plus x_metrics.json (r9_extra_metrics.py), m2_sweep.json, requalify.json, fit.json,
plate.json (plate_model.py) and r9_check.json (check_r9.py: LC-1 overrides, the R-5 gap range whose Z0 bound
gcpw_solve.py gives). The baseline is R8: tools/scorecard_r8_r9.json (0.05 mm DC) or scorecard_r8_r9_quick.json. The repo
rows (G, C, S, P, R, D) come from tools/scorecard.py's own build(), so they equal the R8 record's definitions
(survey_baseline.md of R8); the X / Y / Z / F rows are this survey's additions (survey_baseline.md of R9, section 3).
Indexes: 'index_r8' = the repo's 12-row simplicity index with R8 = 100; 'index_r9' = that plus the clean-sheet rows
of R9_INDEX (board length, pyro foreign nets, through traffic, track widths, mean segment, P6, P9, close pairs).
Targets: TARGETS, r9_plan.md section 2 (kind 'hard' = the build fails, 'done' = R9's definition of done, 'stretch' =
ambition). The gate itself is tools/check.sh; this is the report the review loop reads.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path


def load(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def extra_rows(d):
    sc = {}
    x = load(d / 'x_metrics.json')
    if x:
        sc.update(x['scorecard'])
        sc['X2h_ch1_through_items'] = x['X2']['through_items']
        sc['X1e_aft_overhang_mm'] = x['X1']['aft_overhang']
        sc['X8c_pour_trim_areas'] = sum(1 for n in x['X8']['rule_area_names'] if 'TRIM' in n.upper())
    m = load(d / 'm2_sweep.json')
    if m:
        u = {}
        for a in m.get('adjacency', []):
            k = (json.dumps(a['a']), json.dumps(a['b']))
            u[k] = min(u.get(k, 9.0), a['gap_mm'])
        ap = m.get('adjacency_pad', [])
        sc.update(Y1_close_pairs_lt_0p2=len(u), Y1b_close_pairs_at_drc_min=sum(1 for v in u.values() if v <= 0.151),
                  Y2_pad_close_lt_0p2=len(ap), Y2b_pad_close_foreign=sum(1 for a in ap if a.get('cls') != 'own_part'),
                  Y2c_pad_close_at_drc_min=sum(1 for a in ap if a['gap_mm'] <= 0.151),
                  Y3_m2_chain_detours=len(m.get('chain_detour', [])), Y4_m2_routes_over_1_25=len(m.get('routes', [])),
                  Y5_m2_via_folds=len(m.get('via_fold', [])), Y6_m2_poured_hops=len(m.get('poured_hop', [])),
                  Y7_m2_via_steps=len(m.get('via_step', [])), Y8_m2_short_hops=len(m.get('short_hop', [])))
    q = load(d / 'requalify.json')
    if q:
        tag = {'A': 'Z1a', 'B': 'Z1b', 'C': 'Z1c', 'D': 'Z1d', 'E': 'Z1e', 'F': 'Z1f', 'G': 'Z1g', 'H': 'Z1h'}
        for name, v in q['pyro_rules'].items():
            key = name.split()[0]
            if key in tag and v.get('closest'):
                sc[f'{tag[key]}_pyro_rule_{key}_margin_mm'] = v['closest']['margin']
        ex = q.get('exits', {})
        sc['Z2_pyro_exit_lanes_mm'] = round(sum(ex[n]['new_copper_mm'] for n in ('PYRO1_GATE_N', 'PYRO1_CONT',
                                                                                 'ARM1_SENSE') if n in ex), 1)
        sc['Z2b_pyro_exit_vias'] = sum(len(ex[n]['vias']) for n in ex)
        if q.get('imu'):
            sc['Z3_imu_lever_arm_abs_mm'] = abs(q['imu']['lever_arm_x_mm'])
        if q.get('a8') and 'Z4_vias_in_test_pads' not in sc:     # the R8 survey's A8 (TP122 only) when x_metrics has
            sc['Z4_vias_in_test_pads'] = len(q['a8'].get('vias', []))   # no Z4 (r9_extra_metrics: every TP* pad)
        bare = q.get('bare', {})
        pyro_gate = [v for k, v in bare.items() if '(PYRO1_GATE' in k]
        arm = [v['armed live (bus/ign/drain)']['mm'] for v in pyro_gate if v.get('armed live (bus/ign/drain)')]
        live = [v['other always-live']['mm'] for v in bare.values() if v.get('other always-live')]
        sc['Z5_bare_pyro_gate_to_armed_live_mm'] = min(arm) if arm else None
        sc['Z5b_bare_gate_to_always_live_mm'] = min(live) if live else None
    c9 = load(d / 'r9_check.json')
    if c9:
        rules = c9.get('rules', {})
        lc = rules.get('LC-1', {}).get('evidence', {})
        sc['LC1_local_clearance_overrides'] = len(lc.get('overrides', [])) if lc else None
        r5 = rules.get('R-5', {}).get('evidence', {})
        rng = r5.get('line_gap_range_mm')
        if rng and rng[1] > 0:
            import gcpw_solve as G                     # the GCPW Z0 bound of the widest and narrowest gaps on the lines
            sc['R5_gcpw_gap_min_mm'], sc['R5_gcpw_gap_max_mm'] = rng
            sc['R5_gcpw_z_min_ohm'] = G.z0(0.30, max(rng[0], 0.01))['z0_ohm']
            sc['R5_gcpw_z_max_ohm'] = G.z0(0.30, rng[1])['z0_ohm']
        sc['check_r9_failing_rules'] = len(c9.get('failing', []))
    pl = load(d / 'plate.json')
    if pl:
        sc['M2_f1_hz'] = pl.get('f1', {}).get('jacks_only', {}).get('pinned_D5')
    f = load(d / 'fit.json')
    if f:
        top = [r for r in f['rows'] if r[2] == 'F']
        bot = [r for r in f['rows'] if r[2] == 'B']
        sc.update(F1_fit_worst_top_margin_mm=round(min(r[0] for r in top), 3) if top else None,
                  F2_fit_worst_bottom_margin_mm=round(min(r[0] for r in bot), 3) if bot else None,
                  F3_support_bottom_clear_mm=round(f['nearest_support'][0], 3),
                  F4_support_top_clear_mm=round(f['nearest_top_support'][0], 3))
    return sc


# R9 targets: r9_plan.md section 2 (hard = the build fails; done = R9's definition of done; stretch = ambition).
# (key, op, value, kind, note). R8 values in the notes are board cc044ea0... (tools/scorecard_r8_r9.json).
Z1_DONE = {'a': ('A', 0.2), 'b': ('B', 0.2), 'c': ('C', 0.2), 'd': ('D', 0.2), 'e': ('E', 0.30), 'f': ('F', 0.2),
           'g': ('G', 0.2), 'h': ('H', 0.2)}         # every Z1 margin >= max(R8, 0.2): R8 A .001 B .17 C .077 D .001
                                                    # E .30 F .20 G .000 H .025
TARGETS = [
    # --- hard (r9_plan 2 "Hard (build fails)") ---------------------------------------------------------------------
    ('G_gate_exit', '==', 0, 'hard', 'R9 check.sh: DRC incl. pyro A-H / A2, ERC, parity, check_r9, route_check r9, fit'),
    ('D_raw_neck_dT_C', '<=', 20, 'hard', 'D12'),
    ('D_bat_neck_dT_C', '<=', 20, 'hard', 'D12'),
    ('D_fet_neck_dT_C', '<=', 30, 'hard', 'D12'),
    ('LC1_local_clearance_overrides', '==', 0, 'hard', 'R8 29 (J124.2, J122 RAW pads, 24 test pads)'),
    ('X2d_pyro_nearest_battery_live_mm', '>=', 2.5, 'hard', 'R8 1.089 (ACT_FET_S pour to J124.1, B.Cu)'),
    ('X9_rf_sep_nearest_part_mm', '>=', 5.94, 'hard', 'R8 5.94 (R306 to U1)'),
    ('X9c_inner_power_pyro_mm', '>=', 2.65, 'hard', 'R8 2.65'),
    ('S15_in2_signal_track_mm', '==', 0, 'hard', 'R8 3.4 (rigid CH1 link): no exemption in R9'),
    ('S16_in1_track_mm', '==', 0, 'hard', 'R8 0'),
    ('F1_fit_worst_top_margin_mm', '>=', 0.0, 'hard', 'P2 (fit_check)'),
    ('M2_f1_hz', '>=', 209, 'hard', 'plate model, jacks only, pinned, D 5; R8 208.7'),
    ('X1b_board_width_mm', '==', 46, 'hard', 'P1'),
    ('X3d_non_rf_parts_in_strip', '==', 0, 'hard', 'F10 strip contents'),
    ('S13_critical_layer_changes_no_gnd_via', '==', 0, 'hard', 'AGENTS 3; R8 0'),
    ('F3_support_bottom_clear_mm', '>=', 3.5, 'hard', 'P2'),
    ('F4_support_top_clear_mm', '>=', 3.8, 'hard', 'P2'),
    # --- done: length, pyro -----------------------------------------------------------------------------------------
    ('X1_board_length_mm', '<=', 100, 'done', 'r9_plan: plan 98 mm; R8 118'),
    ('X2_pyro_foreign_nets_3mm_same_layer', '==', 0, 'done', 'R8 6'),
    ('X2b_pyro_foreign_nets_3mm_plan', '==', 0, 'done', 'R8 7'),
    ('X2g_ch1_through_nets', '==', 0, 'done', 'R8 6'),
    ('X2c_pyro_nearest_foreign_mm', '>=', 3.0, 'done', 'R8 0.70'),
] + [(f'Z1{k}_pyro_rule_{v[0]}_margin_mm', '>=', v[1], 'done', 'every Z1 margin >= max(R8, 0.2)')
     for k, v in Z1_DONE.items()] + [
    ('Z2r9_exit_net_track_mm', '<=', 80, 'done', 'GATE_N + CONT + ARM1_SENSE track (whole nets: R9 has no rigid block)'),
    ('Z4_vias_in_test_pads', '==', 0, 'done', 'R8 1 (A8)'),
    ('C6_agents3_rule_instances', '==', 0, 'done', 'R8 1 (A8)'),
    ('Z5_bare_pyro_gate_to_armed_live_mm', '>=', 2.0, 'done', 'R8 1.027'),
    ('Z5b_bare_gate_to_always_live_mm', '>=', 1.0, 'done', 'R8 0.634'),
    # --- done: routing ----------------------------------------------------------------------------------------------
    ('C1_route_gated_category_instances', '==', 0, 'done', 'empty allowlist; R8 3'),
    ('C3_route_allowlisted', '==', 0, 'done', 'R8 3'),
    ('S8_nets_ratio_over_1_6', '<=', 1, 'done', 'RADIO_TXEN only (keep-out-forced); R8 4'),
    ('S9_nets_ratio_over_2', '<=', 1, 'done', 'as S8; R8 4'),
    ('S1_signal_track_mm', '<=', 1497.9, 'done', '<= R8'),
    ('S6_detour_weighted', '<=', 1.174, 'done', '<= R8'),
    ('S7_detour_excess_mm', '<=', 285.8, 'done', '<= R8'),
    ('S10b_signal_bends_total', '<=', 231, 'done', '<= R8'),
    ('S12_critical_layer_changes', '<=', 25, 'done', '<= R8'),
    ('S17_route_mst_total_mm', '<=', 1638.9, 'done', '<= R8'),
    ('S4_signal_layer_change_vias', '<=', 70, 'done', 'owner decision 4 (per-family budgets); R8 55'),
    ('X5_track_widths', '<=', 6, 'done', 'R8 11 (flowline graft: six widths)'),
    ('X8c_pour_trim_areas', '==', 0, 'done', 'R8 8'),
    ('Y1_close_pairs_lt_0p2', '<=', 10, 'done', 'R8 27'),
    ('Y1b_close_pairs_at_drc_min', '==', 0, 'done', 'R8 8'),
    ('Y2c_pad_close_at_drc_min', '==', 0, 'done', 'R8 4'),
    ('Y6_m2_poured_hops', '==', 0, 'done', 'R8 2'),
    ('Y7_m2_via_steps', '==', 0, 'done', 'R8 1'),
    ('Y5_m2_via_folds', '<=', 10, 'done', 'R8 26'),
    # --- done: planes, power, RF, mechanical ------------------------------------------------------------------------
    ('P6_in2_perimeter_mm', '<=', 900, 'done', 'R8 1752.2'),
    ('P7_outer_gnd_islands_le1_via', '==', 0, 'done', 'R8 1'),
    ('P9_gnd_dist_p95_mm', '<=', 3.5, 'done', 'R8 4.47'),
    ('P10_gnd_dist_max_mm', '<=', 7.0, 'done', 'R8 9.65'),
    ('R6b_cref_r6_unreferenced_share', '<=', 0.08, 'done', 'R8 0.1107'),
    ('D_raw_mohm', '<=', 1.0, 'done', 'r9_plan; R8 1.45'),
    ('D_raw_neck_dT_C', '<=', 17.5, 'done', 'every rise <= R8 (17.5)'),
    ('D_bat_neck_dT_C', '<=', 14.5, 'done', 'every rise <= R8 (14.5)'),
    ('D_fet_neck_dT_C', '<=', 21.5, 'done', 'every rise <= R8 (21.4-21.5)'),
    ('X3_rf_strip_depth_mm', '<=', 21.4, 'done', 'R8 21.39'),
    ('X3f_rfif_track_mm', '<=', 250, 'done', 'R8 321.3'),
    ('R5_gcpw_z_min_ohm', '>=', 47.5, 'done', 'GCPW 50 +- 2.5 ohm at every sample (tools/gcpw_solve.py)'),
    ('R5_gcpw_z_max_ohm', '<=', 52.5, 'done', 'GCPW 50 +- 2.5 ohm at every sample (tools/gcpw_solve.py)'),
    ('M2_f1_hz', '>=', 241, 'done', 'R6 target; R8 208.7'),
    ('Z3_imu_lever_arm_abs_mm', '<=', 11.0, 'done', 'R8 13.0'),
    ('index_r9', '<=', 73, 'done', 'R8 = 100'),
    # --- stretch ----------------------------------------------------------------------------------------------------
    ('S4_signal_layer_change_vias', '<=', 55, 'stretch', 'owner decision 4 stretch'),
    ('X1_board_length_mm', '<=', 96, 'stretch', 'plan_spine: 95-96 with a tighter cluster (Inference)'),
    ('X2e_ch1_bbox_area_mm2', '<=', 500, 'stretch', 'R8 662.4'),
    ('Y1_close_pairs_lt_0p2', '==', 0, 'stretch', ''),
    ('D_fet_neck_dT_C', '<=', 20, 'stretch', 'all three paths inside 20 C'),
    ('X6c_mean_segment_mm', '>=', 3.5, 'stretch', 'R8 2.629'),
    ('Z3_imu_lever_arm_abs_mm', '<=', 5.0, 'stretch', ''),
    ('F1_fit_worst_top_margin_mm', '>=', 0.5, 'stretch', 'R8 0.028 (J9 mated)'),
    ('index_r9', '<=', 50, 'stretch', ''),
]

R9_INDEX = [('X1_board_length_mm', 'lower'), ('X2_pyro_foreign_nets_3mm_same_layer', 'lower'),
            ('X2g_ch1_through_nets', 'lower'), ('X5_track_widths', 'lower'), ('X6c_mean_segment_mm', 'higher'),
            ('P6_in2_perimeter_mm', 'lower'), ('Y1_close_pairs_lt_0p2', 'lower')]


# 'done' DC rows are R8's 0.05 mm (qualification grid) values; on a 0.1 mm quick survey compare with R8's quick values
QUICK = {'D_raw_neck_dT_C': 17.6, 'D_bat_neck_dT_C': 14.8, 'D_fet_neck_dT_C': 22.3}


def dc_grid(d):
    p = d / 'dc_raw.txt'
    if not p.exists():
        return None
    m = re.search(r'grid ([\d.]+) mm', p.read_text())
    return float(m.group(1)) if m else None


def met(v, op, want):
    if not isinstance(v, (int, float)):
        return None
    return v <= want if op == '<=' else v >= want if op == '>=' else v == want


def index(new, base, rows):
    logs = []
    for k, better in rows:
        a, b = new.get(k), base.get(k)
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            continue
        if isinstance(a, int) and isinstance(b, int):
            a, b = a + 1, b + 1
        if a <= 0 or b <= 0:
            continue
        logs.append(math.log(a / b) if better == 'lower' else math.log(b / a))
    return round(100 * math.exp(sum(logs) / len(logs)), 1) if logs else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('outdir')
    ap.add_argument('--baseline')
    ap.add_argument('--md')
    ap.add_argument('--json')
    ap.add_argument('--tools', default=str(Path(__file__).resolve().parent))
    a = ap.parse_args()
    sys.path.insert(0, str(Path(a.tools).resolve()))
    import scorecard as S  # repo tools/scorecard.py: build(), compare(), INDEX
    d = Path(a.outdir)
    res = S.build(d)
    sc = res['scorecard']
    sc.update(extra_rows(d))
    base = None
    if a.baseline:
        bp = Path(a.baseline)
        if bp.is_file():
            base = json.loads(bp.read_text())['scorecard']
        else:
            base = S.build(bp)['scorecard']
            base.update(extra_rows(bp))
        sc['index_r8'] = index(sc, base, S.INDEX)
        sc['index_r9'] = index(sc, base, S.INDEX + R9_INDEX)
    grid = sc['D_grid_mm'] = dc_grid(d)
    rows = []
    for k, op, t, kind, n in TARGETS:
        if kind == 'done' and grid and grid > 0.075 and k in QUICK:
            t, n = QUICK[k], f'R8 at the 0.1 mm quick grid ({n})'
        rows.append(dict(key=k, value=sc.get(k), op=op, target=t, kind=kind, met=met(sc.get(k), op, t), note=n))
    out = dict(scorecard=sc, targets=rows, baseline=base)
    lines = [f'# R9 scorecard: {d}', '']
    if base:
        lines += [f"index_r8 (repo 12-row index, R8 = 100): **{sc['index_r8']}**; index_r9 (+ clean-sheet rows): "
                  f"**{sc['index_r9']}**", '']
    for kind in ('hard', 'done', 'stretch'):
        rr = [r for r in rows if r['kind'] == kind]
        lines += [f"## {kind}: {sum(1 for r in rr if r['met'])} met, {sum(1 for r in rr if r['met'] is False)} "
                  f"missed, {sum(1 for r in rr if r['met'] is None)} not measured", '',
                  '| Row | Board | Goal | Met | Note |', '|---|---:|---|---|---|']
        lines += [f"| {r['key']} | {r['value']} | {r['op']} {r['target']} | "
                  f"{'yes' if r['met'] else 'no' if r['met'] is False else '-'} | {r['note']} |" for r in rr]
        lines.append('')
    keys = sorted(sc, key=lambda k: (S.order(k) if k[0] in S.GROUP else (8, k)))
    lines += ['## All rows', '', '| Row | Board | Baseline |', '|---|---:|---:|']
    lines += [f"| {k} | {sc[k]} | {base.get(k) if base else ''} |" for k in keys]
    txt = '\n'.join(lines) + '\n'
    if a.md:
        Path(a.md).write_text(txt)
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1, default=str) + '\n')
    print(txt)


if __name__ == '__main__':
    main()
