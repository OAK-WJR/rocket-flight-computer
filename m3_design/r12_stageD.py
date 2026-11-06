#!/usr/bin/env python3
"""R12 stage D electrical analyses on R12's own copper (D-R12-78 ... ; m3_design/r12/design/stageD_analysis.md).

R11's m3_design/r11_stageD.py adapted to R12's four-layer, one-sided board and R12's parts (R12_DECISIONS D-R12-04 ...
-21, -49 ... -52). No CAD is changed. Writes m3_design/r12/design/stageD_budget.json:
  * fire budget: the five fire paths read from the board (check_r10.fire_path with check_r12's terminals by net),
    series copper per segment at the board's own copper thickness (R12 mixes widths on one path, so R10's
    one-width formula in r10_parts.native_fire_copper is not used), R10's GAP-1 pack model (r10_parts.power_budget's
    fire_case, re-stated here) with R12's FETs and converter load (m3_design/r12_budget.py), the GND fire return by
    DC solve against R10's 5 mOhm allowance, shorted-match currents and FET dissipation, gate drive, adiabatic rise;
  * J400 / U9 EN timing and chatter (R10's EN model, r11_stageD.en_model, unchanged values), turn-on window;
  * hold-up (C84 on VLOGIC behind D5, D-R12-04) from the battery break and from the PA6 trip; PA6 trip-window corners
    with the match / leads shorted (O-R12-07);
  * rail paths (check_r10.path_graph between R12's terminals): series R, IPC-2152 rise per drawn width at R10's
    design currents (tools/ipc2152.py with th_mm); DC solves of the feeds (tools/r11_dc_net.py's method on R12's four
    layers);
  * U6 (FXLS90322) supply drop from the 3V3 regulation point (O-R12-22);
  * Q124 gate copper, U4 / U6 axis placement and lever arm.

usage: <KiCad python3> -I -B m3_design/r12_stageD.py FILLED_BOARD [--source-board UNFILLED_BOARD] [--out JSON]
       [--skip-gnd]  (the GND and 3V3 plane solves take a few minutes in pure Python)
The board must be zone-filled; a scratch copy filled with pcbnew.ZONE_FILLER is enough, and --source-board records
the board whose copper it is. Labels (AGENTS section 2.5): Calculation on CAD copper and datasheet values; Inference
where an input is unmeasured (FET hot factors, pack / harness / match, diode drops, load allocations, X7R bias).
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'tools'))
import ipc2152                                                    # noqa: E402
import r12_budget                                                 # noqa: E402
from r11_stageD import adiabatic, en_model                        # noqa: E402

OUT = HERE / 'r12/design/stageD_budget.json'
RHO = 1.72e-8
TCR = .00393
CU_NAMES = ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')
OUTER = ('F.Cu', 'B.Cu')
# R10 GAP-1 fire model constants (r10_parts.power_budget): pack 0.15 ohm at 7.4 V open, 1.92 A per stalled servo,
# MJG J-Tek match <= 2 ohm, external leads <= 0.3 ohm, terminal allowance 0.010 ohm, GND return allowance 0.005 ohm.
PACK_R, PACK_V, STALL_A = .15, 7.4, 1.92
MATCH, LEADS, TERMINALS, GND_ALLOWANCE = 2.0, .3, .010, .005
FLOOR_A = .75 * 1.5                                               # MJG J-Tek all-fire 0.75 A x 1.5 (REQUIREMENTS F7)
R134_HOT = 2 * 1.01 * (1 + 100e-6 * (70 - 25))
# D-R12-10 (r12_budget.fire): AO3401A <= 60 mOhm at VGS -4.5 V, 25 C, x 1.225 at 70 C; AO3400A <= 48 mOhm at 2.5 V, x 1.195
PFET_HOT, Q124_HOT = .060 * 1.225, .048 * 1.195
# Design currents (R10's K-power basis by function, REQUIREMENTS F4 / F9): U9 path 2.9 A, port rail 1.9 A per port,
# camera 1.249 A, VLOGIC 1.294 A, 3V3 2.0 A; the shorted-igniter bound 4.2 A (8.4 V / R134 2 ohm, R10 FIRE_NARROW basis)
SHORT_A = 4.2
FOUR_STALL_VIN = 5.71                                             # buck input at the four-stall point (checked below)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stackup(path):
    from dc_solve import stackup as four_layer                    # R10's four-layer stack-up parse (F / In1 / In2 / B)
    return four_layer(path)


def seg_r(length_mm, width_mm, th_mm):
    return RHO * length_mm * 1e-3 / (width_mm * 1e-3 * th_mm * 1e-3)


def fps(board):
    return {f.GetReference(): f for f in board.GetFootprints()}


def pads_on(board, ref, net):
    f = fps(board)[ref]
    return tuple(sorted({p.GetNumber() for p in f.Pads() if p.GetNetname() == net and p.GetNumber()}))


def fire_terminals(board):
    """check_r12.fire_terminals: each current-path terminal by its net on its reference (D-R12-10)."""
    refs = {'PYRO1_IGN': ('R134', 'J121'), 'PYRO1_OUT': ('J121', 'Q124'),
            'RAW_ACT': ('Q121', 'R134'), 'ACT_FET_S': ('Q120', 'Q121'), 'BAT_IN': ('J1', 'Q120')}
    return {net: tuple({ref: pads_on(board, ref, net)} for ref in ends) for net, ends in refs.items()}


def fire_copper(board, stack):
    """Per fire net: the series tracks between its terminals (check_r10.fire_path) plus routed entries into the
    terminal pads (r10_parts.native_fire_copper's rule), each at its own width and layer thickness; vias on the path."""
    import pcbnew
    import check_r10
    mm = pcbnew.ToMM
    out = {}
    for net, groups in fire_terminals(board).items():
        tracks, joined, term = check_r10.fire_path(board, net, groups)
        if not joined or not tracks:
            raise ValueError(f'{net}: no fire path')
        chosen = {t.m_Uuid.AsString(): t for t in tracks}
        ends = {(t.GetLayer(), q.x, q.y) for t in tracks for q in (t.GetStart(), t.GetEnd())}
        f = fps(board)
        pads = [f[ref].FindPadByNumber(n) for g in groups for ref, nums in g.items() for n in nums]
        entries = {}
        for t in board.GetTracks():
            if t.GetClass() != 'PCB_TRACK' or t.GetNetname() != net:
                continue
            for pad in pads:
                if pad is None or not pad.IsOnLayer(t.GetLayer()):
                    continue
                anchor, a, b = pad.GetPosition(), t.GetStart(), t.GetEnd()
                if pad.HitTest(a) and pad.HitTest(b) and ((a == anchor and (t.GetLayer(), b.x, b.y) in ends)
                                                          or (b == anchor and (t.GetLayer(), a.x, a.y) in ends)):
                    if t.m_Uuid.AsString() not in chosen:
                        entries[t.m_Uuid.AsString()] = t
        chosen.update(entries)
        segs, vias = [], [t for t in chosen.values() if t.GetClass() == 'PCB_VIA']
        for t in sorted((t for t in chosen.values() if t.GetClass() == 'PCB_TRACK'),
                        key=lambda t: (t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y)):
            lay = board.GetLayerName(t.GetLayer())
            w, L = mm(t.GetWidth()), mm(t.GetLength())
            segs.append(dict(layer=lay, width_mm=round(w, 4), length_mm=round(L, 4), th_mm=stack[lay][0],
                             R_20C_ohm=seg_r(L, w, stack[lay][0]), pad_entry=t.m_Uuid.AsString() in entries))
        layers = sorted({s['layer'] for s in segs})
        if vias or len(layers) != 1:
            raise ValueError(f'{net}: fire path changes layer ({layers}, {len(vias)} vias): needs a via model')
        out[net] = dict(terminals=term, layers=layers, segments=segs,
                        length_mm=sum(s['length_mm'] for s in segs),
                        widths_mm=sorted({s['width_mm'] for s in segs}),
                        R_20C_ohm=sum(s['R_20C_ohm'] for s in segs))
    return out


def other_load_w():
    """Converter load during the fire (r12_budget.fire's 'other', from the R12 rail windows): camera 1 A and ports
    0.561 A at their bucks' initial maximum output / 0.80, logic 1.4 W + microSD write 3.3 V x 0.2 A / 0.80, D5
    0.45 V x 0.3 A, R92 bleed at 7.4 V (Inference: allocations, efficiency, diode drop)."""
    rails = r12_budget.rails()
    cam = rails['CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)']['initial']['max_V']
    port = rails['PORT_4V8 (U400 TPS563208, R400 47k + R404 5.1k / R401 10k 0.1 %)']['initial']['max_V']
    parts = dict(camera_W=cam * 1.0 / .80, ports_W=port * .561 / .80, logic_W=1.4, microsd_write_W=3.3 * .2 / .80,
                 d5_W=.45 * .3, r92_W=PACK_V ** 2 / (3300 * .98))
    return sum(parts.values()), dict(parts, camera_V=cam, port_V=port)


def loaded(rest, other, stalls, open_v=PACK_V):
    a, b = 1 + PACK_R / rest, open_v - PACK_R * STALL_A * stalls
    v = (b + math.sqrt(b * b - 4 * a * PACK_R * other)) / (2 * a)
    return v, v / rest


def fire_budget(copper, gnd_return):
    other, other_parts = other_load_w()
    cu20 = sum(c['R_20C_ohm'] for c in copper.values())
    cu70 = cu20 * (1 + TCR * (70 - 20))
    ground = max(GND_ALLOWANCE, gnd_return or 0.0)
    rest = R134_HOT + MATCH + LEADS + cu70 + ground + TERMINALS + 2 * PFET_HOT + Q124_HOT
    stalls = {}
    for n in range(5):
        v, i = loaded(rest, other, n)
        stalls[str(n)] = dict(BAT_IN_V=v, fire_A=i, margin_pct=(i / FLOOR_A - 1) * 100)
    shorts = {}
    for label, drop in (('match_shorted', MATCH), ('match_and_leads_shorted', MATCH + LEADS)):
        for n in (0, 4):
            v, i = loaded(rest - drop, other, n)
            shorts[f'{label}_{n}_stalls'] = dict(BAT_IN_V=v, fire_A=i, Q120_I2R_W=i * i * PFET_HOT,
                                                 Q121_I2R_W=i * i * PFET_HOT, Q124_I2R_W=i * i * Q124_HOT,
                                                 R134_W=i * i * R134_HOT)
    # Q120 / Q121 gate: VGS = -(V_BAT - Q122 drop 0.1 V) x Rgs / (Rgs + R121), Rgs = R119 || R120 = 50k (1 %), R121 10k
    r_gs_min = 50e3 * .98
    ratio = r_gs_min / (r_gs_min + 10e3 * 1.02)
    tau = (50e3 * 10e3 / 60e3) * 1.02 * (1e-6 * 1.10 * 1.15)      # C120 1 uF +10 % tolerance, +15 % temperature
    # D-R12-91 (R12F1-TRI-19): the pack voltage above which |VGS| can exceed 12 V uses the largest ratio, 51k / 60.8k
    # (Rgs +2 %, R121 -2 %), not the smallest one the drive-strength figures above use
    r_gs_max = 50e3 * 1.02
    ratio_max = r_gs_max / (r_gs_max + 10e3 * .98)
    def vgs(v):
        return (v - .1) * ratio
    gate = dict(q120_q121_vgs_V={f'{v:g}V': -vgs(v) for v in (stalls['4']['BAT_IN_V'], 6.0, 7.4, 8.4, 12.6, 19.9)},
                q120_q121_time_to_minus_4V5_ms={f'{v:g}V': (-tau * math.log(1 - 4.5 / vgs(v)) * 1e3 if vgs(v) > 4.5
                                                            else None) for v in (6.0, 7.4, 8.4)},
                q120_rds_row='AO3401A RDS(on) <= 60 mOhm at VGS -4.5 V (25 C)', q120_vgs_abs_max_V=12.0,
                q120_vgs_exceeds_12V_above_pack_V=12.0 / ratio_max + .1, q120_vgs_ratio_min_max=[ratio, ratio_max],
                q124_vgs_min_V=3.240 * 10e3 / (10e3 + 220), q124_vgs_row_V=2.5, q124_vgs_th_max_V=1.45,
                q124_gate_tau_us=220 * 220e-9 * 1e6,
                basis='R119 / R120 100k, R121 10k, C120 1 uF 50 V X5R (C15849), R126 220R / R127 1k / R128 10k / C126 '
                      '220 nF (values unchanged from R10 / R11); AO3401A / AO3400A datasheet rows (D-R12-10); C120 '
                      'tolerance and temperature factors as R10 (no bias credit), Inference')
    return dict(
        status='Calculation on R12 CAD copper with R10 GAP-1 pack model; Inference: FET hot factors, pack, harness, '
               'match, converter load allocations',
        copper_by_net={k: dict(length_mm=v['length_mm'], widths_mm=v['widths_mm'], layers=v['layers'],
                               R_20C_mohm=v['R_20C_ohm'] * 1e3) for k, v in copper.items()},
        copper_20C_ohm=cu20, copper_70C_ohm=cu70, gnd_return_dc_ohm=gnd_return, gnd_return_used_ohm=ground,
        R134_hot_ohm=R134_HOT, pfet_hot_ohm=PFET_HOT, q124_hot_ohm=Q124_HOT, match_ohm=MATCH, leads_ohm=LEADS,
        terminal_allowance_ohm=TERMINALS, fire_branch_without_pack_ohm=rest, total_loop_ohm=rest + PACK_R,
        other_converter_load_W=other, other_load_parts=other_parts, floor_A=FLOOR_A, stalls=stalls,
        four_stall_A=stalls['4']['fire_A'], four_stall_BAT_IN_V=stalls['4']['BAT_IN_V'],
        four_stall_ok=stalls['4']['fire_A'] >= FLOOR_A, shorted=shorts, gate=gate,
        r12_budget_placeholder_four_stall_A=r12_budget.fire()['four_stall_A'],
        shorted_igniter_guard=dict(
            watchdog_ms=[960 / 33600 * 1e3, 960 / 29400 * 1e3], allocations_ms=[.2, .5, 1.5],
            guard_ms=960 / 29400 * 1e3 + .2 + .5 + 1.5, limit_ms=36.0,
            R134_min_70C_ohm=2 * .99 * (1 - 100e-6 * 45), fault_W=8.4 ** 2 / (2 * .99 * (1 - 100e-6 * 45)),
            note='R10 GAP-5 inputs unchanged on R12 (IWDG 960 LSI cycles, R126 / R127 / R128 / C126, R134 part): '
                 'carried by identity of inputs (Calculation on allocations / Inference)'))


def holdup(four_stall_bat):
    """C84 (470 uF polymer, 300.8 uF allowance as R10) holds VLOGIC only; D5 blocks RAW_PROTECTED (D-R12-04), so the
    port and camera bucks and R92 are not on it. Constant-power loads to 3.8 V (R10 / R11's end point, Inference for
    the LMR50410): unshed logic 0.6-1.4 W + microSD write 3.3 V x 0.2 A / 0.85-0.80; shed logic 0.62 W + microSD idle
    3.3 V x 0.03 A / 0.85-0.80. Start points: battery break at the 7.4 V launch floor less U9 and D5 (D5 VF 0.25-0.45 V,
    U9 0.04 ohm x 1.5 A, Inference); PA6 trip at the window below. No credit for C6 / C99 (Inference)."""
    loads = dict(unshed=(.6 + 3.3 * .2 / .85, 1.4 + 3.3 * .2 / .80), shed=(.62 + 3.3 * .03 / .85, .62 + 3.3 * .03 / .80))
    def ms(c, v0, w, v_end=3.8):
        return .5 * c * (v0 ** 2 - v_end ** 2) / w * 1e3
    win = pa6_window()
    out = {}
    for case, (wmin, wmax) in loads.items():
        out[case] = dict(
            load_W=[wmin, wmax],
            battery_break_ms=[ms(300.8e-6, PACK_V - .45 - .06, wmax), ms(470e-6, PACK_V - .25 - .06, wmin)],
            pa6_trip_nominal_ratio_ms=[ms(300.8e-6, win['nominal_ratio_V'][0], wmax),
                                       ms(470e-6, win['nominal_ratio_V'][1], wmin)],
            pa6_trip_with_divider_tolerance_ms=[ms(300.8e-6, win['with_divider_tolerance_V'][0], wmax),
                                                ms(470e-6, win['with_divider_tolerance_V'][1], wmin)],
            battery_break_to_3V5_ms=[ms(300.8e-6, PACK_V - .45 - .06, wmax, 3.5), ms(470e-6, PACK_V - .25 - .06, wmin, 3.5)])
    out['r11_case_c_ms'] = [.464, .539]
    out['label'] = 'Calculation / Inference (constant-power allocations, D5 drop, C84 allowance, 3.8 V end point)'
    return out


def pa6_window():
    """PA6 = VLOGIC x R61 / (R60 + R61), R60 100k / R61 10k; firmware threshold 0.42-0.45 V (D-R12-21, O-R12-17).
    'nominal_ratio' is R10 / R11's method (x 11); 'with_divider_tolerance' adds the two 1 % resistors (Calculation)."""
    lo_ratio, hi_ratio = 10e3 * .99 / (10e3 * .99 + 100e3 * 1.01), 10e3 * 1.01 / (10e3 * 1.01 + 100e3 * .99)
    return dict(threshold_V=[.42, .45], nominal_ratio_V=[.42 * 11, .45 * 11],
                with_divider_tolerance_V=[.42 / hi_ratio, .45 / lo_ratio], ratio=[lo_ratio, hi_ratio])


def pa6_corners(fire, u9_feed_ohm, raw_d5_ohm):
    """VLOGIC during the fire at the healthy / match-shorted / match-and-leads-shorted four-stall points: BAT_IN less
    U9 (0.04 ohm, Inference) and its copper (DC solves J1 -> U9.5 and U9.6 -> D5.2) at the converter current, less D5
    (SS34 VF 0.25-0.45 V, Inference); against the PA6 trip window (O-R12-07)."""
    other = fire['other_converter_load_W']
    win = pa6_window()
    out = {}
    cases = {'healthy': fire['stalls']['4'], 'match_shorted': fire['shorted']['match_shorted_4_stalls'],
             'match_and_leads_shorted': fire['shorted']['match_and_leads_shorted_4_stalls']}
    for name, c in cases.items():
        v = c['BAT_IN_V']
        i = other / v
        drop = i * (.04 + u9_feed_ohm + raw_d5_ohm)
        vl = [v - drop - .45, v - drop - .25]
        out[name] = dict(BAT_IN_V=v, converter_A=i, U9_and_copper_drop_V=drop, VLOGIC_V=vl,
                         margin_to_nominal_trip_top_V=vl[0] - win['nominal_ratio_V'][1],
                         margin_to_tolerance_trip_top_V=vl[0] - win['with_divider_tolerance_V'][1])
    out['window'] = win
    out['u9_turn_off_through_d5_V'] = 4.80 - .25
    out['label'] = 'Calculation / Inference (U9 RON, SS34 VF and the load allocations are Inference)'
    return out


def en_figures(four):
    """R10's EN model (r11_stageD.en_model: R80 / R165 470k, R81 300k, C87 220 nF x 0.72, U9 0.1 uA, D402 50 nA;
    values unchanged on R12, D-R12-09), at R12's four-stall BAT_IN; the lowest pack voltage at which the J400 7 ms
    bench line holds; the single-drop-out 10 ms pack floor; the turn-on window (EN rising 1.183-1.223 V, TI SLVSFC9C
    section 6.5) over a 6.0-8.4 V unloaded pack, C87 220 nF x 0.72 x 0.9 ... 220 nF x 1.1 (Inference: X7R bias)."""
    out = {f'{v:.4g}V': en_model(v) for v in (8.4, 7.4, 6.0, four, 5.73, 5.71, 5.65, 5.5)}

    def bisect(f, lo, hi):
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if f(mid) else (mid, hi)
        return hi
    seven = bisect(lambda v: en_model(v)['periodic_100ms_trip_open_ms'] >= 7.0, 5.0, 7.0)
    ten = bisect(lambda v: en_model(v)['single_dropout_trip_ms'] >= 10.0, 5.0, 7.0)

    def turn_on(v, c, r_hi):
        r_top, r81 = 2 * 470e3 * (1.01 if r_hi else .99), 300e3 * (.99 if r_hi else 1.01)
        r_th = r_top * r81 / (r_top + r81)
        vc = v * r81 / (r_top + r81) - (.1e-6 if r_hi else -.1e-6) * r_th - (50e-9 if r_hi else 0) * r_th
        vth = 1.223 if r_hi else 1.183
        return r_th * c * math.log(vc / (vc - vth)) * 1e3
    nominal = {f'{v:g}V': 2 * 470e3 * 300e3 / (2 * 470e3 + 300e3) * 220e-9 * 1e3 *
               math.log((v * 300 / 1240) / (v * 300 / 1240 - 1.2)) for v in (6.0, 7.4, 8.4)}
    on = dict(nominal_ms=nominal, fastest_ms=turn_on(8.4, 220e-9 * .72 * .9, False),
              slowest_ms=turn_on(6.0, 220e-9 * 1.1, True))
    return dict(by_pack=out, four_stall_BAT_IN_V=four, seven_ms_line_holds_down_to_V=seven,
                single_10ms_dropout_needs_pack_V=ten, turn_on=on,
                bench_rule='J400 chatter (D-R25-01): total open time < 7 ms in every sliding 100 ms window, U9 on for '
                           'the whole run at the four-stall BAT_IN',
                label='Calculation / Inference (C87 X7R bias allowance, leakages at their datasheet bounds)')


def dc(board_path, net, src, snk, margin=4.0, full_width=True):
    """tools/r11_dc_net.solve on R12's four copper layers. Window: the terminals' box plus `margin` along y and, for a
    track-routed net, the full board width (a feed may detour sideways); for the plane nets (GND, 3V3) the box plus
    `margin` both ways. Copper outside the window is dropped, so R is an upper bound (Calculation)."""
    import pcbnew
    import r11_hotplug
    import r11_dc_net
    r11_hotplug.CU_NAMES = CU_NAMES
    r11_dc_net.CU_NAMES = CU_NAMES
    board = pcbnew.LoadBoard(str(board_path))
    xs, ys = [], []
    for s in (src, snk):
        for p in r11_dc_net.pad_spec(board, s):
            xs.append(pcbnew.ToMM(p.GetPosition().x))
            ys.append(pcbnew.ToMM(p.GetPosition().y))
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = (pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY()), pcbnew.ToMM(bb.GetRight()),
                      pcbnew.ToMM(bb.GetBottom()))
    window = (x0 if full_width else max(x0, min(xs) - margin), max(y0, min(ys) - margin),
              x1 if full_width else min(x1, max(xs) + margin), min(y1, max(ys) + margin))
    window = tuple(round(v, 1) for v in window)
    r = r11_dc_net.solve(board_path, net, src, snk, grid=0.1, window=window)
    r.pop('board_sha256', None)
    if not math.isfinite(r['resistance_ohm']) or r['resistance_ohm'] > 1.0:
        raise ValueError(f'{net} {src} -> {snk}: not joined inside the window {window}')
    return r


def spec(board, ref, net):
    return f'{ref}:' + ','.join(pads_on(board, ref, net))


def power_paths(board):
    """R12's rail paths by function (R10 K-power basis): (name, net, start pads, end pads or None = the path's vias,
    design current A, basis)."""
    p = lambda ref, net: {ref: pads_on(board, ref, net)}         # noqa: E731
    port_v = r12_budget.rails()['PORT_4V8 (U400 TPS563208, R400 47k + R404 5.1k / R401 10k 0.1 %)']['initial']['max_V']
    port_in = 1.9 * port_v / (.80 * FOUR_STALL_VIN)
    cam_in = 1.249 * 5.691 / (.80 * FOUR_STALL_VIN)
    rows = [
        ('U9 IN', 'BAT_IN', p('J1', 'BAT_IN'), p('U9', 'BAT_IN'), 2.9, 'R10 U9 IN'),
        ('U9 OUT', 'RAW_PROTECTED', p('U9', 'RAW_PROTECTED'), None, 2.9, 'R10 U9 OUT'),
        ('U400 IN', 'RAW_PROTECTED', p('U400', 'RAW_PROTECTED'), None, port_in,
         f'port 1.9 A at {port_v:.3f} V / 0.80 from 5.71 V (Inference)'),
        ('U403 IN', 'RAW_PROTECTED', p('U403', 'RAW_PROTECTED'), None, cam_in,
         'camera 1.249 A at 5.691 V / 0.80 from 5.71 V (Inference)'),
        ('D5 IN', 'RAW_PROTECTED', p('D5', 'RAW_PROTECTED'), None, 1.294, 'R10 VLOGIC 1.294 A'),
        ('VLOGIC D5 to U2', 'VLOGIC', p('D5', 'VLOGIC'), p('U2', 'VLOGIC'), 1.294, 'R10 VLOGIC trunk'),
        ('C84 hold-up', 'VLOGIC', p('C84', 'VLOGIC'), p('U2', 'VLOGIC'), 1.294, 'R10 C84 hold-up'),
        ('U400 OUT', 'PORT_4V8', p('L400', 'PORT_4V8'), None, 1.9, 'R10 port rail'),
        ('J410 feed', 'PORT_4V8', p('J410', 'PORT_4V8'), None, 1.9, 'R10 port feed'),
        ('J420 feed', 'PORT_4V8', p('J420', 'PORT_4V8'), None, 1.9, 'R10 port feed'),
        ('J440 feed', 'PORT_4V8', p('J440', 'PORT_4V8'), None, 1.9, 'R10 port feed'),
        ('CAM_5V out', 'CAM_5V', p('L401', 'CAM_5V'), p('J9', 'CAM_5V'), 1.249, 'R10 camera'),
        ('U2 OUT', '3V3', p('L1', '3V3'), None, 2.0, 'R10 3V3 (U2 LMR50410 is a 1 A part)'),
    ]
    return rows


def rail_paths(board, stack):
    import pcbnew
    import check_r10
    mm = pcbnew.ToMM
    out = {}
    for name, net, start, end, amps, basis in power_paths(board):
        segs, joined, vias, on = check_r10.path_graph(board, net, start, end)
        key = lambda t: (t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth())  # noqa: E731
        segs = sorted(segs, key=key)
        vias = sorted(vias, key=lambda v: (v.GetPosition().x, v.GetPosition().y))
        per = {}
        for t in segs:
            lay = board.GetLayerName(t.GetLayer())
            th = stack[lay][0]
            w, L = round(mm(t.GetWidth()), 4), mm(t.GetLength())
            q = per.setdefault(lay, dict(length_mm=0.0, R_series_ohm=0.0, th_mm=th, by_width_mm={}))
            q['length_mm'] += L
            q['R_series_ohm'] += seg_r(L, w, th)
            q['by_width_mm'].setdefault(f'{w:.3f}', dict(length_mm=0.0))['length_mm'] += L
        for lay, q in per.items():
            for key, item in q['by_width_mm'].items():
                item['ipc_rise_C'] = ipc2152.ipc_dt(float(key), lay, amps, th_mm=q['th_mm'])
            q['min_width_mm'] = min(float(k) for k in q['by_width_mm'])
            q['ipc_width_for_30C_mm'] = ipc2152.ipc_width(30.0, lay, amps, th_mm=q['th_mm'])
        over = [dict(layer=lay, width_mm=float(k), length_mm=v['length_mm'], rise_C=v['ipc_rise_C'])
                for lay, q in per.items() for k, v in q['by_width_mm'].items() if v['ipc_rise_C'] > 30.0]
        out[name] = dict(net=net, amps=amps, basis=basis, joined=joined, pads=on, layers=per,
                         vias=[[round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3),
                                round(mm(v.GetDrillValue()), 3)] for v in vias],
                         R_tracks_series_ohm=sum(q['R_series_ohm'] for q in per.values()),
                         over_30C=over, over_30C_all_short_entries=all(o['length_mm'] <= 2.0 for o in over))
    return out


def fire_return(board, stack):
    """Q124's source (GND) copper: tracks and vias touching Q124's GND pad; adiabatic rise of each width at 4.2 A."""
    import pcbnew
    mm = pcbnew.ToMM
    pad = fps(board)['Q124'].FindPadByNumber(pads_on(board, 'Q124', 'GND')[0])
    tracks = [t for t in board.GetTracks() if t.GetNetname() == 'GND' and t.GetClass() == 'PCB_TRACK'
              and (pad.HitTest(t.GetStart()) or pad.HitTest(t.GetEnd()))]
    vias = [v for v in board.GetTracks() if v.GetNetname() == 'GND' and v.GetClass() == 'PCB_VIA'
            and math.dist((mm(v.GetPosition().x), mm(v.GetPosition().y)),
                          (mm(pad.GetPosition().x), mm(pad.GetPosition().y))) < 2.0]
    return dict(pad=[mm(pad.GetPosition().x), mm(pad.GetPosition().y)],
                tracks=[dict(layer=board.GetLayerName(t.GetLayer()), width_mm=round(mm(t.GetWidth()), 3),
                             length_mm=round(mm(t.GetLength()), 3),
                             adiabatic_4A2_20ms_K=adiabatic(SHORT_A, mm(t.GetWidth()), stack[board.GetLayerName(t.GetLayer())][0], .020))
                        for t in tracks],
                vias_within_2mm=[[round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3)] for v in vias])


def gate_copper(board, stack):
    import pcbnew
    import r10_hotplug
    mm = pcbnew.ToMM
    out = {}
    for net in ('PYRO1_GATE_N', 'PYRO1_GATE', 'ACT_GATE', 'ACT_EN'):
        L, ind, nv = {}, 0.0, 0
        for t in board.GetTracks():
            if t.GetNetname() != net:
                continue
            if t.GetClass() == 'PCB_VIA':
                nv += 1
                continue
            lay = board.GetLayerName(t.GetLayer())
            L[lay] = L.get(lay, 0.0) + mm(t.GetLength())
            h = min(abs(stack[lay][1] - stack[q][1]) for q in ('In1.Cu', 'In2.Cu') if q != lay)
            ind += r10_hotplug.microstrip_nh(mm(t.GetWidth()), h, mm(t.GetLength()))
        out[net] = dict(length_mm_by_layer=L, vias=nv, microstrip_L_nH_upper=ind)
    return out


def imu(board):
    import pcbnew
    mm = pcbnew.ToMM
    out = {}
    for ref in ('U4', 'U6'):
        f = fps(board)[ref]
        xs = [mm(p.GetPosition().x) for p in f.Pads()]
        ys = [mm(p.GetPosition().y) for p in f.Pads()]
        out[ref] = dict(part=f.GetValue(), side='bottom' if f.IsFlipped() else 'top',
                        rotation_deg=f.GetOrientationDegrees(), x_mm=round(mm(f.GetPosition().x), 4),
                        y_mm=round(mm(f.GetPosition().y), 4),
                        pad_centre_mm=[round((min(xs) + max(xs)) / 2, 4), round((min(ys) + max(ys)) / 2, 4)],
                        lever_arm_x_mm=round(mm(f.GetPosition().x) - 23.0, 4))
    out['U4']['axis_map'] = ('D-R12-54: +X_imu -> +x_board, +Y_imu -> -y_board, +Z_imu out of the top face; roll about '
                             '+y_board reads -gyro_Y; forward thrust reads -a_Y (Calculation; LSM6DSVE frame Inference)')
    out['U6']['axis_map'] = ('D-R12-54: channel 0 (X) -> +x_board, channel 1 (Y) -> +y_board (rocket axis); forward '
                             'thrust reads +a on channel 1 (Inference: single-channel sheet figure)')
    out['roll_axis_x_mm'] = 23.0
    return out


def u6_supply(solves):
    """O-R12-22: U6 VCC_BUF >= 3.135 V (NXP FXLS9xxx0 Rev 6 item 10502), <= 6.0 mA (item 10510). The regulation point
    is R14.1 (U2's feedback divider top). Bound: every 3V3 load current flows from L1.2, so the potential difference
    between R14.1 and U6's VCC pins is at most (R(L1.2 -> U6) + R(L1.2 -> R14.1)) x I_3V3 (the triangle bound on the
    DC network; Calculation). I_3V3: U2's 1 A rating (an upper bound) and a 0.5 A allocation (Inference)."""
    r_u6 = solves['3V3_L1_to_U6']['resistance_ohm']
    r_fb = solves['3V3_L1_to_R14']['resistance_ohm']
    rails = r12_budget.rails()['3V3 (U2 LMR50410, R14 47k / R15 20k)']
    out = dict(R_L1_to_U6_ohm=r_u6, R_L1_to_R14_ohm=r_fb, R_R14_to_U6_direct_ohm=solves['3V3_R14_to_U6']['resistance_ohm'],
               floor_V=3.135, u6_max_A=.006)
    for label, amps in (('1A_rating_bound', 1.0), ('0V5_allocation', .5), ('u6_only_6mA', .006)):
        drop = (r_u6 + r_fb) * amps if amps > .006 else solves['3V3_R14_to_U6']['resistance_ohm'] * amps
        out[label] = dict(I_A=amps, drop_V=drop,
                          min_VCC_initial_V=rails['initial']['min_V'] - drop, margin_initial_V=rails['initial']['min_V'] - drop - 3.135,
                          min_VCC_drift_V=rails['drift']['min_V'] - drop, margin_drift_V=rails['drift']['min_V'] - drop - 3.135)
    out['label'] = 'Calculation on CAD copper (DC solves, 20 C) and the r12_windows 3V3 window; load currents Inference'
    return out


def port_supply(solves):
    """PORT_4V8 at each port's pin 2. U400 regulates at R400.1 (its feedback divider top), whose 0.3 mm B.Cu sense stub
    joins the east-edge trunk at (45.2, 21.5), 5 mm from L400; the ports sit on the forward edge. Every node potential
    of a resistive network lies between the source's and the sinks' (maximum principle), and a mutual resistance from
    L400.2 is at most either driving-point resistance, so with the three ports drawing I in all the drop from the
    regulation point to port k is at most R(L400.2 -> port k) x I (Calculation on CAD copper at 20 C; an upper bound:
    the trunk from L400 to the sense tap, about 8 mOhm, is counted). I: the always-on budget 0.561 A (GPS 0.15 + radio
    0.30 + AUX 0.10 + 0.011 A, R10 D-R28-01) and R10's 1.9 A design current. Port window (r12_windows, D-R12-21):
    r12_windows' rows (D-R12-83: 4.603-4.938 V initial, 4.571-4.972 V drift); module floor 4.5 V (MicoAir LR900-F, project
    records; MicoAir's page gives '5V DC' with no range, so the floor is an Inference)."""
    rails = r12_budget.rails()['PORT_4V8 (U400 TPS563208, R400 47k + R404 5.1k / R401 10k 0.1 %)']
    out = dict(R_L400_to_R400_ohm=solves['PORT_4V8_L400_to_R400']['resistance_ohm'], floor_V=4.5,
               window_initial_V=[rails['initial']['min_V'], rails['initial']['max_V']],
               window_drift_V=[rails['drift']['min_V'], rails['drift']['max_V']])
    for port in ('J410', 'J420', 'J440'):
        r = solves[f'PORT_4V8_L400_to_{port}']['resistance_ohm']
        row = dict(R_L400_to_port_ohm=r)
        for label, amps in (('budget_0A561', .561), ('design_1A9', 1.9)):
            drop = r * amps
            row[label] = dict(I_A=amps, drop_bound_V=drop, min_initial_V=rails['initial']['min_V'] - drop,
                              min_drift_V=rails['drift']['min_V'] - drop,
                              margin_initial_V=rails['initial']['min_V'] - drop - 4.5,
                              margin_drift_V=rails['drift']['min_V'] - drop - 4.5)
        out[port] = row
    # D-R12-83: the ceiling side. With no port load there is no copper drop, so each port can sit at the regulator's
    # maximum; it must stay at or under the 5.0 V top (HGLRC M100 Mini 3.3-5 V, hglrc.com; the LR900-F's 5.0 V top is
    # the project record, an Inference).
    out['ceiling_V'] = 5.0
    out['max_no_load_initial_V'] = rails['initial']['max_V']
    out['max_no_load_drift_V'] = rails['drift']['max_V']
    out['all_ports_inside_4V5_5V0_at_0A561'] = all(
        min(out[p]['budget_0A561']['min_initial_V'], out[p]['budget_0A561']['min_drift_V']) >= 4.5
        for p in ('J410', 'J420', 'J440')) and rails['drift']['max_V'] <= 5.0 and rails['initial']['max_V'] <= 5.0
    out['label'] = ('Calculation on CAD copper and the r12_windows PORT_4V8 window (upper bound on the drop); the 4.5 V '
                    'module floor, the LR900-F 5.0 V top and the load allocation are Inference; harness drop not '
                    'included')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board')
    ap.add_argument('--source-board', default=None)
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--skip-gnd', action='store_true')
    a = ap.parse_args()
    import pcbnew
    board_path = Path(a.board)
    before = sha(board_path)
    stack = stackup(board_path)
    board = pcbnew.LoadBoard(str(board_path))
    unfilled = [z.GetZoneName() for z in board.Zones() if not z.GetIsRuleArea()
                and any(not z.HasFilledPolysForLayer(l) for l in z.GetLayerSet().Seq())]
    if unfilled:
        raise SystemExit(f'zones not filled: {unfilled} (fill a scratch copy first)')
    copper = fire_copper(board, stack)
    S = {}
    jobs = [('BAT_IN_J1_to_U9', 'BAT_IN', spec(board, 'J1', 'BAT_IN'), spec(board, 'U9', 'BAT_IN')),
            ('BAT_IN_J1_to_Q120', 'BAT_IN', spec(board, 'J1', 'BAT_IN'), spec(board, 'Q120', 'BAT_IN')),
            ('RAW_PROTECTED_U9_to_U400', 'RAW_PROTECTED', spec(board, 'U9', 'RAW_PROTECTED'), spec(board, 'U400', 'RAW_PROTECTED')),
            ('RAW_PROTECTED_U9_to_U403', 'RAW_PROTECTED', spec(board, 'U9', 'RAW_PROTECTED'), spec(board, 'U403', 'RAW_PROTECTED')),
            ('RAW_PROTECTED_U9_to_D5', 'RAW_PROTECTED', spec(board, 'U9', 'RAW_PROTECTED'), spec(board, 'D5', 'RAW_PROTECTED')),
            ('VLOGIC_D5_to_U2', 'VLOGIC', spec(board, 'D5', 'VLOGIC'), spec(board, 'U2', 'VLOGIC')),
            ('VLOGIC_C84_to_U2', 'VLOGIC', spec(board, 'C84', 'VLOGIC'), spec(board, 'U2', 'VLOGIC')),
            ('VLOGIC_D6_to_U2', 'VLOGIC', spec(board, 'D6', 'VLOGIC'), spec(board, 'U2', 'VLOGIC')),
            ('PORT_4V8_L400_to_J410', 'PORT_4V8', spec(board, 'L400', 'PORT_4V8'), spec(board, 'J410', 'PORT_4V8')),
            ('PORT_4V8_L400_to_J420', 'PORT_4V8', spec(board, 'L400', 'PORT_4V8'), spec(board, 'J420', 'PORT_4V8')),
            ('PORT_4V8_L400_to_J440', 'PORT_4V8', spec(board, 'L400', 'PORT_4V8'), spec(board, 'J440', 'PORT_4V8')),
            ('PORT_4V8_L400_to_R400', 'PORT_4V8', spec(board, 'L400', 'PORT_4V8'), spec(board, 'R400', 'PORT_4V8')),
            ('CAM_5V_L401_to_J9', 'CAM_5V', spec(board, 'L401', 'CAM_5V'), spec(board, 'J9', 'CAM_5V'))]
    if not a.skip_gnd:
        jobs += [('3V3_L1_to_U6', '3V3', spec(board, 'L1', '3V3'), spec(board, 'U6', '3V3')),
                 ('3V3_L1_to_R14', '3V3', spec(board, 'L1', '3V3'), spec(board, 'R14', '3V3')),
                 ('3V3_R14_to_U6', '3V3', spec(board, 'R14', '3V3'), spec(board, 'U6', '3V3')),
                 ('GND_Q124_to_J1', 'GND', spec(board, 'Q124', 'GND'), spec(board, 'J1', 'GND'))]
    for key, net, src, snk in jobs:
        S[key] = dc(board_path, net, src, snk, margin=6.0 if net in ('GND', '3V3') else 4.0,
                    full_width=net not in ('GND', '3V3'))
        print(f'{key}: {S[key]["resistance_ohm"] * 1e3:.3f} mOhm ({S[key]["cells"]} cells)', flush=True)
    gnd = S['GND_Q124_to_J1']['resistance_ohm'] if 'GND_Q124_to_J1' in S else None
    fire = fire_budget(copper, gnd)
    four = fire['four_stall_BAT_IN_V']
    out = dict(
        status='Calculation on R12 CAD copper with R10 component tolerances; Inference where labelled; no physical test',
        board_sha256=before, source_board_sha256=sha(a.source_board) if a.source_board else None,
        stackup={k: dict(thickness_mm=v[0], depth_mm=v[1]) for k, v in stack.items()},
        fire_copper=copper, fire=fire,
        fire_adiabatic={f'{w}mm_{int(th * 1e3)}um_{int(t * 1e3)}ms': adiabatic(SHORT_A, w, th, t)
                        for w in sorted({w for c in copper.values() for w in c['widths_mm']})
                        for th in (stack['F.Cu'][0],) for t in (.020, .036)},
        fire_return=fire_return(board, stack),
        en=en_figures(four),
        holdup=holdup(four),
        pa6_corners=pa6_corners(fire, S['BAT_IN_J1_to_U9']['resistance_ohm'],
                                S['RAW_PROTECTED_U9_to_D5']['resistance_ohm']),
        rails=rail_paths(board, stack),
        dc_solves=S,
        u6_supply=u6_supply(S) if '3V3_L1_to_U6' in S else None,
        port_supply=port_supply(S),
        gate=gate_copper(board, stack),
        imu=imu(board))
    if sha(board_path) != before:
        raise ValueError('board changed during the analysis')
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    print(json.dumps(dict(loop_ohm=fire['total_loop_ohm'], four_stall_A=fire['four_stall_A'],
                          four_stall_BAT_IN_V=four, gnd_return_ohm=gnd), indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
