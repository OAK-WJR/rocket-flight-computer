#!/usr/bin/env python3
"""R11 stage D electrical analyses on R11's own copper (D-R11-73 ... ; m3_design/r11/design/stageD_analysis.md).

Re-runs R10's native-board power budget (m3_design/r10_parts.power_budget, unchanged, with the fire copper read from
the R11 board and checked against R11's six-layer stack-up), and adds what R10 computed outside that function:
  * K-power rail paths (tools/check_r11.POWER_PATHS_R11): series copper resistance per layer at R11's thicknesses and
    the IPC-2152 rise of each path's narrowest track at its design current (tools/ipc2152.py with th_mm);
  * DC solves of the feed, logic, USB and fire-return copper (tools/r11_dc_net.py, all six layers, zones filled);
  * the J400 / U9 EN timing and chatter figures at the R11 four-stall BAT_IN (R10's EN model, D-R24-19 / D-R26-03);
  * hold-up from the battery break and from the PA6 trip (R10's constant-power model, D-R25-02);
  * the PA6 trip-window corners with the match / leads shorted (R10's fire_current_GAP1 model, R26-TRI-04);
  * the fire-path adiabatic rise at the 4.2 A shorted-igniter current (R10's FIRE_NARROW basis);
  * U4's axis map and lever arm.
No CAD is changed. Writes m3_design/r11/design/stageD_budget.json.

usage: <KiCad python3> -I -B m3_design/r11_stageD.py FILLED_BOARD [--source-board UNFILLED_BOARD] [--out JSON]
       [--skip-gnd]  (the GND fire-return solve takes a few minutes in pure Python)
The board must be zone-filled (R11's routing leaves zones unfilled; r11_post fills them): a scratch copy filled with
pcbnew.ZONE_FILLER is enough, and --source-board records the unfilled board whose copper it is.
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
import r10_parts                                                  # noqa: E402
import ipc2152                                                    # noqa: E402
from r11_hotplug import stackup                                    # noqa: E402

OUT = HERE / 'r11/design/stageD_budget.json'
RHO = 1.72e-8
OUTER = ('F.Cu', 'B.Cu')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fire_copper_r11(board_path):
    """r10_parts.native_fire_copper on the R11 board, with the R11 conditions R10's formula assumes checked: every fire
    path on one outer layer whose stack-up copper is 35 um (R10's formula uses 1.72e-8 / 35e-6)."""
    import pcbnew
    import check_r10
    stack = stackup(board_path)
    board = pcbnew.LoadBoard(str(board_path))
    paths, entries = r10_parts.native_fire_copper(board)
    layers = {}
    terminals = {**check_r10.FIRE_TERMINALS, 'ACT_FET_S': ({'Q120': ('2',)}, {'Q121': ('3',)})}
    for net, groups in terminals.items():
        tracks, joined, _ = check_r10.fire_path(board, net, groups)
        layers[net] = sorted({board.GetLayerName(t.GetLayer()) for t in tracks})
        if len(layers[net]) != 1 or layers[net][0] not in OUTER or abs(stack[layers[net][0]][0] - 0.035) > 1e-9:
            raise ValueError(f'{net}: fire path on {layers[net]}; R10 formula needs one 35 um outer layer')
    return paths, entries, layers


def budget(board_path):
    paths, entries, layers = fire_copper_r11(board_path)
    original = r10_parts.native_fire_copper
    r10_parts.native_fire_copper = lambda board: (paths, entries)
    try:
        res = r10_parts.power_budget(board_path)
    finally:
        r10_parts.native_fire_copper = original
    res['fire_current_GAP1']['CAD_fire_path_layers'] = layers
    res['ldo_thermal_vias'] = 'R10 record (two VIPPO vias at R10 coordinates): not an R11 figure; see stageD r11_u401'
    return res


def seg_r(length_mm, width_mm, th_mm):
    return RHO * length_mm * 1e-3 / (width_mm * 1e-3 * th_mm * 1e-3)


def rail_paths(board):
    """Per K-power path: tracks per layer (length, narrowest width, series R at R11 copper), vias, IPC-2152 rise of the
    narrowest track at the path's design current (no plane credit, long-conductor fit: an upper bound, Inference)."""
    import pcbnew
    import check_r10
    import check_r11
    mm = pcbnew.ToMM
    out = {}
    for spec in check_r11.POWER_PATHS_R11:
        segs, joined, vias, on = check_r10.path_graph(board, spec['net'], spec['start'], spec['end'])
        per = {}
        for t in segs:
            lay = board.GetLayerName(t.GetLayer())
            th = check_r11.CU_MM_R11[lay]
            w, L = mm(t.GetWidth()), mm(t.GetLength())
            p = per.setdefault(lay, dict(length_mm=0.0, R_series_ohm=0.0, min_width_mm=w, th_mm=th))
            p['length_mm'] += L
            p['R_series_ohm'] += seg_r(L, w, th)
            p['min_width_mm'] = min(p['min_width_mm'], w)
            key = f'{w:.3f}'
            p.setdefault('by_width_mm', {}).setdefault(key, dict(length_mm=0.0))['length_mm'] += L
        amps = spec.get('amps')
        for lay, p in per.items():
            if amps:
                p['ipc_rise_at_min_width_C'] = ipc2152.ipc_dt(p['min_width_mm'], lay, amps, th_mm=p['th_mm'])
                p['ipc_width_for_30C_mm'] = ipc2152.ipc_width(30.0, lay, amps, th_mm=p['th_mm'])
                for key, item in p['by_width_mm'].items():
                    item['ipc_rise_C'] = ipc2152.ipc_dt(float(key), lay, amps, th_mm=p['th_mm'])
        out[spec['name']] = dict(net=spec['net'], amps=amps, joined=joined, pads=on, layers=per,
                                 vias=[[round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3),
                                        round(mm(v.GetDrillValue()), 3)] for v in vias],
                                 R_tracks_series_ohm=sum(p['R_series_ohm'] for p in per.values()))
    return out


def gate_copper(board):
    """Copper of Q124's gate drive (PYRO1_GATE_N: PE4 -> R126; PYRO1_GATE: R126 -> Q124.4, R128, C126): length per
    net and layer, vias, and a microstrip inductance bound against the gate RC time constant."""
    import pcbnew
    import r10_hotplug
    mm = pcbnew.ToMM
    stack = stackup(board.GetFileName())
    out = {}
    for net in ('PYRO1_GATE_N', 'PYRO1_GATE'):
        L, ind, nv = {}, 0.0, 0
        for t in board.GetTracks():
            if t.GetNetname() != net:
                continue
            if t.GetClass() == 'PCB_VIA':
                nv += 1
                continue
            lay = board.GetLayerName(t.GetLayer())
            L[lay] = L.get(lay, 0.0) + mm(t.GetLength())
            z = stack[lay][1]
            h = min(abs(z - stack[q][1]) for q in ('In1.Cu', 'In4.Cu') if q != lay)
            ind += r10_hotplug.microstrip_nh(mm(t.GetWidth()), h, mm(t.GetLength()))
        out[net] = dict(length_mm_by_layer=L, vias=nv, microstrip_L_nH_upper=ind)
    return out


def en_model(v_bat):
    """R10's U9 EN model (D-R24-19, D-R26-03; TPS25947 SLVSFC9C p9 thresholds and leakage, Infineon ESD103 Rev 1.3):
    R80 / R165 470 k (1 %, high), R81 300 k (1 %, low), C87 220 nF x 0.72 (X7R bias allowance, Inference), U9 EN
    leakage 0.1 uA out of the node, D402 50 nA at J400.2. Returns the closed EN voltage, the single drop-out that
    trips U9 at 1.116 V, and the periodic one-block-per-100-ms open time that trips it (the late-block worst train)."""
    r_top, r81, c = 2 * 470e3 * 1.01, 300e3 * .99, 220e-9 * .72
    i_u9, i_d402, v_off = .1e-6, 50e-9, 1.116
    r_th = r_top * r81 / (r_top + r81)
    v_closed = v_bat * r81 / (r_top + r81) - i_u9 * r_th
    r80, r_low = 470e3 * 1.01, 470e3 * 1.01 + r81
    v_closed -= i_d402 * (r80 * r_low / (r80 + r_low)) * (r81 / r_low)
    tau_o, tau_c = r81 * c, r_th * c
    a = (i_u9 + i_d402) * r81                                        # open: both leakages leave EN through R81 / R165
    single = tau_o * math.log((v_closed + a) / (v_off + a))

    def bottom(t_open, period=.1):
        x, y = math.exp(-t_open / tau_o), math.exp(-(period - t_open) / tau_c)
        return ((v_closed * (1 - y) + a) * x - a) / (1 - x * y)
    lo, hi = 0.0, single
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if bottom(mid) > v_off else (lo, mid)
    return dict(v_bat=v_bat, en_closed_V=v_closed, single_dropout_trip_ms=single * 1e3,
                periodic_100ms_trip_open_ms=lo * 1e3, en_at_7ms_open_per_100ms_V=bottom(.007),
                tau_open_ms=tau_o * 1e3, tau_closed_ms=tau_c * 1e3)


def holdup(loads_w):
    """R10's hold-up (D-R25-02): constant power from 300.8 uF; break-to-3.8 V from 7.4 V and PA6-trip-to-3.8 V from
    VLOGIC 4.84-5.17 V (the PA6 0.44-0.47 V window x 11). [shortest, longest] ms."""
    c = 300.8e-6

    def ms(v0, w):
        return .5 * c * (v0 ** 2 - 3.8 ** 2) / w * 1e3
    out = {}
    for case, (wmin, wmax) in loads_w.items():
        out[case] = dict(break_to_3V8_ms=[ms(7.4, wmax), ms(7.4, wmin)],
                         pa6_trip_to_3V8_ms=[ms(4.84, wmax), ms(5.17, wmin)])
    return out


def pa6_corners(res):
    """R10's fire_current_GAP1 pack model with the match (2 ohm) and the match plus external leads (0.3 ohm) shorted,
    four stalls, both FET cases (R26-TRI-04)."""
    f = res['fire_current_GAP1']
    other_w = f['other_converter_load_W']
    out = {}
    for name, case in (('primary_40mohm', f['primary_40mohm_FETs']), ('typical_hot', f['secondary_typical_hot_curve_FETs'])):
        rest = case['fire_branch_without_pack_ohm']
        for label, drop in (('healthy', 0.0), ('match_shorted', 2.0), ('match_and_leads_shorted', 2.3)):
            r = rest - drop
            a, b = 1 + .15 / r, 7.4 - .15 * 1.92 * 4
            v = (b + math.sqrt(b * b - 4 * a * .15 * other_w)) / (2 * a)
            out[f'{name}_{label}'] = dict(BAT_IN_V=v, fire_A=v / r)
    return out


def adiabatic(amps, width_mm, th_mm, seconds):
    j = amps / (width_mm * 1e-3 * th_mm * 1e-3)
    return j * j * RHO * seconds / (8960 * 385)


def u401_thermal(board):
    """U401's thermal pad (pin 11, GND) and the GND vias in it or near it: R10's GAP-3 junction figure rested on two
    filled and capped vias in that pad (Inference: 80-110 C/W)."""
    import pcbnew
    mm = pcbnew.ToMM
    f = next(f for f in board.GetFootprints() if f.GetReference() == 'U401')
    pad = f.FindPadByNumber('11')
    px, py = mm(pad.GetPosition().x), mm(pad.GetPosition().y)
    vias = []
    for v in board.GetTracks():
        if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND':
            vx, vy = mm(v.GetPosition().x), mm(v.GetPosition().y)
            d = math.hypot(vx - px, vy - py)
            if d < 3.0:
                vias.append(dict(xy=[round(vx, 3), round(vy, 3)], centre_distance_mm=round(d, 3),
                                 in_pad=bool(pad.HitTest(v.GetPosition()))))
    return dict(side='bottom' if f.IsFlipped() else 'top', pad_xy=[px, py],
                pad_size_mm=[mm(pad.GetSize().x), mm(pad.GetSize().y)], gnd_vias_within_3mm=vias,
                vias_in_pad=sum(v['in_pad'] for v in vias))


def imu(board):
    import pcbnew
    mm = pcbnew.ToMM
    u4 = next(f for f in board.GetFootprints() if f.GetReference() == 'U4')
    xs = [mm(p.GetPosition().x) for p in u4.Pads()]
    ys = [mm(p.GetPosition().y) for p in u4.Pads()]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return dict(ref='U4', part=u4.GetValue(), side='bottom' if u4.IsFlipped() else 'top',
                rotation_deg=u4.GetOrientationDegrees(), x_mm=round(mm(u4.GetPosition().x), 4),
                y_mm=round(mm(u4.GetPosition().y), 4), pad_centre_mm=[round(cx, 4), round(cy, 4)],
                lever_arm_x_mm=round(mm(u4.GetPosition().x) - 23.0, 4))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board')
    ap.add_argument('--source-board', default=None)
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--skip-gnd', action='store_true')
    a = ap.parse_args()
    import pcbnew
    import r11_dc_net
    board_path = Path(a.board)
    before = sha(board_path)
    res = budget(board_path)
    board = pcbnew.LoadBoard(str(board_path))
    f = res['fire_current_GAP1']
    four = f['primary_40mohm_FETs']['pack_7V4_by_stall_count']['4']
    solves = {}
    for key, net, src, snk, win in (
            ('BAT_IN_J1_to_U9', 'BAT_IN', 'J1:1', 'U9:5', None),
            ('BAT_IN_J1_to_Q120', 'BAT_IN', 'J1:1', 'Q120:5,6,7,8,9', None),
            ('RAW_PROTECTED_U9_to_U11', 'RAW_PROTECTED', 'U9:6', 'U11:2', None),
            ('RAW_PROTECTED_U9_to_U400', 'RAW_PROTECTED', 'U9:6', 'U400:2,3', None),
            ('PORT_5V3_L400_to_U401', 'PORT_5V3', 'L400:2', 'U401:9,10', None),
            ('PORT_5V3_L400_to_U402', 'PORT_5V3', 'L400:2', 'U402:1', None),
            ('PORT_4V8_U401_to_J410', 'PORT_4V8', 'U401:1,2', 'J410:1', None),
            ('PORT_4V8_U401_to_J420', 'PORT_4V8', 'U401:1,2', 'J420:1', None),
            ('PORT_4V8_U401_to_J440', 'PORT_4V8', 'U401:1,2', 'J440:1', None),
            ('VLOGIC_U11_to_U2', 'VLOGIC', 'U11:1,8', 'U2:2,3', None),
            ('USB_LIMITED_U10_to_U11', 'USB_LIMITED', 'U10:6', 'U11:7', None),
            ('GND_Q124_to_J1', 'GND', 'Q124:1,2,3', 'J1:2', (0.0, 8.0, 16.0, 33.0))):
        if key.startswith('GND') and a.skip_gnd:
            continue
        solves[key] = r11_dc_net.solve(board_path, net, src, snk, grid=0.1, window=win)
    usb = {}
    r_usb = .135 + .100 + solves['USB_LIMITED_U10_to_U11']['resistance_ohm'] + .02
    for vbus in (5.0, 4.75):
        for p_w, label in ((1.4 + .825, 'unshed_plus_sd'), (.6 + .776, 'low_allocation')):
            i = (vbus - math.sqrt(vbus * vbus - 4 * r_usb * p_w)) / (2 * r_usb)
            usb[f'{label}_{vbus:g}V'] = dict(A=i, VLOGIC_V=vbus - i * r_usb)
    out = dict(
        status='Calculation on R11 CAD copper with R10 component tolerances; Inference where labelled; no physical test',
        board_sha256=before, source_board_sha256=sha(a.source_board) if a.source_board else None,
        stackup={k: dict(thickness_mm=v[0], depth_mm=v[1]) for k, v in stackup(board_path).items()},
        power_budget=res,
        four_stall=dict(BAT_IN_V=four['loaded_pack_V'], fire_A=four['fire_A']),
        en=dict((f'{v:g}V', en_model(v)) for v in (8.4, 7.4, 6.0, four['loaded_pack_V'], 5.73, 5.71, 5.65, 5.5)),
        holdup=holdup(res['battery_break_load_W']),
        pa6_corners=pa6_corners(res),
        rails=rail_paths(board),
        dc_solves=solves,
        usb_only=dict(path_ohm=r_usb, basis='U10 <= 0.135 + U11 <= 0.100 + R11 USB_LIMITED copper (solve) + 0.02 allowance; '
                      'R10: 0.0912 ohm In2 track', cases=usb, u10_limit_A=[.3477, .4530]),
        fire_adiabatic=dict((f'{w}mm_{th}um_{int(t * 1e3)}ms', adiabatic(4.2, w, th / 1000, t))
                            for w, th in ((0.5, 35), (0.3, 35), (1.0, 35)) for t in (.020, .036)),
        gate=gate_copper(board),
        r11_u401=u401_thermal(board),
        imu=imu(board))
    if sha(board_path) != before:
        raise ValueError('board changed during the analysis')
    Path(a.out).write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(four_stall=out['four_stall'], loop=f['primary_40mohm_FETs']['total_loop_ohm'],
                          dc={k: v['resistance_ohm'] for k, v in solves.items()}), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
