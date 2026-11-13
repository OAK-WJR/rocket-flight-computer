#!/usr/bin/env python3
"""R12 stage D electrical analyses on R12's own copper (D-R12-78 ... ; m3_design/r12/design/stageD_analysis.md).

R11's m3_design/r11_stageD.py adapted to R12's four-layer, one-sided board and R12's parts (R12_DECISIONS D-R12-04 ...
-21, -49 ... -52). No CAD is changed. Writes m3_design/r12/design/stageD_budget.json:
  * fire budget: the five fire paths read from the board (check_r10.fire_path with check_r12's terminals by net),
    series copper per segment at the board's own copper thickness (R12 mixes widths on one path, so R10's
    one-width formula in r10_parts.native_fire_copper is not used), R10's GAP-1 pack model (r10_parts.power_budget's
    fire_case, re-stated here) with R12's FETs and converter load (m3_design/r12_budget.py), the GND fire return by
    DC solve against R10's 5 mOhm allowance, shorted-match currents and FET dissipation, gate drive, adiabatic rise;
  * J400 / U9 EN timing and chatter (R10's EN model, r12_budget.en_model, unchanged values) in both of R12's resistor
    cases (1 % and the drift bound, R12F8-TRI-06), turn-on window over R10's C87 range 0.72-1.265 x 220 nF (D-R19-10;
    R12F7-TRI-17);
  * hold-up (C84 on VLOGIC behind D5, D-R12-04) from the battery break and from the PA6 trip; PA6 trip-window corners
    with the match / leads shorted (O-R12-07), U9 RON at SLVSFC9C's 45 mOhm maximum (R12F8-TRI-07), the PA6 divider in
    both resistor cases;
  * U403 (camera buck) input and the camera-pin estimate at the four-stall point (R12F8-TRI-09);
  * rail paths (check_r10.path_graph between R12's terminals): series R, IPC-2152 rise per drawn width at R10's
    design currents (tools/ipc2152.py with th_mm); DC solves of the feeds (tools/r11_dc_net.py's method on R12's four
    layers);
  * U6 (FXLS90322) supply drop from the 3V3 regulation point (O-R12-22);
  * Q124 gate copper, U4 / U6 axis placement and lever arm;
  * R12F12 round 12: BAT_IN as one network (J1.1; U9.5, Q120.3, R80.1) with the fire and converter currents solved
    together and EN taken at R80.1 (TRI-30), the J400 chatter bench rule as a number below the worst limit over both
    load conventions (TRI-23), 70 C copper in the drift minima and PA6's upper end at its own VF current (TRI-31), the
    3V3 load budget against U2 with L1 4.7 uH (TRI-11), VBUS_SENSE with R110 1.5k (TRI-06), Q122's gate with R118
    (TRI-04), D8's GND return (TRI-16), and a walk that cuts a track at a pad it crosses, failing on an unjoined path
    (TRI-24). main refuses to write a record that record_issues rejects.

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
from r11_stageD import adiabatic                                  # noqa: E402
from r12_budget import en_model                                   # noqa: E402

OUT = HERE / 'r12/design/stageD_budget.json'
RHO = 1.72e-8
TCR = .00393
# R12F9-TRI-04: copper at the 70 C hot end (the fire loop's own corner) in every bound that pairs the four-stall BAT_IN
# with board copper: pa6_corners, u400_input, u403_input (1 + 0.00393 x 50 = 1.1965)
HOT_CU = 1 + TCR * (70 - 20)
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
# D-R12-95 (90 mm re-layout), still so on the current board (R12F12-TRI-40: items named, not coordinates): the In2
# RAW_PROTECTED island's west piece (U9 / C82 / D9) and east piece (camera buck, trunk vias) join only in the aft band
# under J122 / J9, aft of every RAW_PROTECTED terminal box; the port buck's VIN (U400.3 / C400.1) is reached by the
# 0.6 mm B.Cu trunk along the east edge, a 0.6 mm diagonal (B and F, D-R12-162) and the 1.0 mm F.Cu run west across the
# board to C400.1. Solve RAW_PROTECTED on the whole board.
# The In2 3V3 plane is one filled outline, but inside the L1 / U6 box (+ 6 mm, and + 12 mm) the RAW island, the 3V3A
# sensor copper and the In2 signal lanes leave L1's and U6's copper in separate pieces (Measured: the box solve finds two
# components), so 3V3 is solved on the whole board too.
FULL_BOARD_NETS = ('RAW_PROTECTED', '3V3')
FOUR_STALL_VIN = 5.71                                             # buck input at the four-stall point (checked below)
U9_RON = r12_budget.U9_RON                                        # SLVSFC9C 6.5 maximum, 45 mOhm (R12F8-TRI-07)
TOL = r12_budget.TOL                                              # 'initial' 1 %, 'drift' 1 % + 100 ppm/K x 67 K


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
    0.561 A at their bucks' initial maximum output / 0.80, logic 1.4 W + microSD write 3.3 V x 0.2 A / 0.80 (U2's input
    power), R92 3.3 kOhm -2 % (Inference: allocations, efficiency). R12F10-TRI-09: the stage A allocations 'D5 0.45 V x
    0.3 A' allocation is gone: fire_budget charges D5's loss as SS34's 0.45 V x U2's own input current from
    raw_point's self-consistent solve at each BAT_IN. The returned total is the converters' input power plus R92's
    bleed at 7.4 V (the R10 GAP-1 constant-power convention), without D5's loss."""
    rails = r12_budget.rails()
    cam = rails['CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)']['initial']['max_V']
    port = rails['PORT_4V8 (U400 TPS563208, R400 47k + R404 5.1k / R401 10k 0.1 %)']['initial']['max_V']
    parts = dict(camera_W=cam * 1.0 / .80, ports_W=port * .561 / .80, logic_W=1.4, microsd_write_W=3.3 * .2 / .80,
                 r92_W=PACK_V ** 2 / R92_MIN)
    return sum(parts.values()), dict(parts, camera_V=cam, port_V=port)


# R92 (RAW_PROTECTED bleed, 3.3 kOhm 1 %) at its -2 % end; SS34 (D5) VF at the logic current, its high end (Inference,
# r12_budget.D5_VF): the current-maximising corners of raw_point
R92_MIN, D5_VF_MAX = 3300 * .98, r12_budget.D5_VF[1]
RAW_SINKS = ('U400', 'U403', 'D5')


class NoPoint(ValueError):
    """raw_point has no operating point at that BAT_IN (the constant-power loads collapse it)."""


def raw_point(bat, parts, u9_feed_ohm, raw_ohm, r_u2_ohm, vf=D5_VF_MAX, i_fire=0.0, z_fire_ohm=0.0):
    """R12F10-TRI-09: the self-consistent RAW_PROTECTED operating point at BAT_IN bat (J1's terminal). Unknowns: the
    U400 (ports) and U403 (camera) input currents, D5's current (= U2's input current: with D6 off it is the only path
    into VLOGIC in steady state) and R92's bleed. U9's output is bat - I_total x (U9 RON + the J1 -> U9.5 copper); each
    sink's node is that less sum_j I_j x min(R_k, R_j) (the mutual-resistance bound from U9.6 of pa6_corners, an upper
    bound on each drop), R92 at D5's node. U400 / U403 draw their constant input power at their own node; U2 draws the
    logic + microSD write power at its VIN = D5's node - vf - I_D5 x R(D5 -> U2) (the quadratic's lower root); R92
    draws its node voltage / R92_MIN. R12F12-TRI-30: bat is J1's terminal and U9.5 sits on the shared BAT_IN copper, so
    U9's input is also lowered by the fire current i_fire x z_fire_ohm (the J1 -> U9.5 / J1 -> Q120.3 transfer resistance
    of bat_in_network; 0 with no fire); u9_feed_ohm is then the network's own J1 -> U9.5 term. Lower nodes mean larger currents, so the fixed-point iteration from the BAT_IN
    currents rises monotonically to the solution; D5's loss is vf x I_D5, the model's own current x drop (Calculation on
    the DC solves; the allocations, SS34 VF and R92's corner Inference). Resistances are as given (callers pass 70 C)."""
    p_u2 = parts['logic_W'] + parts['microsd_write_W']
    power = dict(U400=parts['ports_W'], U403=parts['camera_W'])
    at = dict(U400='U400', U403='U403', D5='D5', R92='D5')
    cur = dict(U400=power['U400'] / bat, U403=power['U403'] / bat, D5=p_u2 / bat, R92=bat / R92_MIN)
    for _ in range(2000):
        tot = sum(cur.values())
        u9_out = bat - tot * (U9_RON + u9_feed_ohm) - i_fire * z_fire_ohm
        node = {k: u9_out - sum(cur[j] * min(raw_ohm[k], raw_ohm[at[j]]) for j in cur) for k in RAW_SINKS}
        va = node['D5'] - vf
        if min(node.values()) <= 0 or va * va < 4 * r_u2_ohm * p_u2 or va <= 0:
            raise NoPoint(f'no RAW_PROTECTED operating point at BAT_IN {bat} V')
        i_d5 = 2 * p_u2 / (va + math.sqrt(va * va - 4 * r_u2_ohm * p_u2))   # the lower root, cancellation-free
        new = dict(U400=power['U400'] / node['U400'], U403=power['U403'] / node['U403'], D5=i_d5,
                   R92=node['D5'] / R92_MIN)
        done = max(abs(new[k] - cur[k]) for k in cur) < 1e-13
        cur = new
        if done:
            break
    else:
        raise NoPoint(f'raw_point did not converge at BAT_IN {bat} V')
    tot = sum(cur.values())
    u9_out = bat - tot * (U9_RON + u9_feed_ohm) - i_fire * z_fire_ohm
    node = {k: u9_out - sum(cur[j] * min(raw_ohm[k], raw_ohm[at[j]]) for j in cur) for k in RAW_SINKS}
    v_u2 = node['D5'] - vf - cur['D5'] * r_u2_ohm
    return dict(BAT_IN_V=bat, currents_A=cur, I_total_A=tot, U9_out_V=u9_out, node_V=node, D5_VF_V=vf,
                fire_A=i_fire, fire_drop_at_U9_V=i_fire * z_fire_ohm,
                U2_VIN_V=v_u2, U2_input_A=p_u2 / v_u2, D5_loss_W=vf * cur['D5'], R92_W=node['D5'] * cur['R92'],
                power_at_BAT_IN_W=bat * tot)


# R12F3-TRI-06: Q124's gate drive from PE4 (DS12110 Rev 8 Table 158 VOH allowance; 3V3 drift minimum)
VOH_DROP = 0.4
Q124_VDD_MIN = r12_budget.rails()['3V3 (U2 LMR50410, R14 47k / R15 20k)']['drift']['min_V']
# R12F4-TRI-02: PE4 (PYRO1_GATE_N) sources R127 1k to GND as well as R126 220R + R128 10k (netlist: PYRO1_GATE_N = U1.C3,
# R126.1, R127.1). Steady high load at the 3V3 drift minimum with nominal resistors, and its bound at the 3V3 drift
# maximum with every resistor at its -1.67 % drift end (r12_budget TOL['drift']); both must stay within Table 158's 4 mA
# row, the current at which VOH >= VDD - 0.4 V is guaranteed.
Q124_VDD_MAX = r12_budget.rails()['3V3 (U2 LMR50410, R14 47k / R15 20k)']['drift']['max_V']
VOH_ROW_MA = 4.0
TD = r12_budget.TOL['drift']


def pe4_load_mA(vdd, low=0.0):
    """PE4's steady high load (mA) at vdd: R127 1k plus R126 220R + R128 10k, each resistor (1 - low) of nominal."""
    return (vdd / (1e3 * (1 - low)) + vdd / (10.22e3 * (1 - low))) * 1e3


# R12F12-TRI-30: BAT_IN is one copper network from J1.1 to U9.5 (the converters), Q120.3 (the fire) and R80.1 (U9's EN
# divider top), solved as a multiport (r11_dc_net.solve_ports; bat_in_network). Z[a][b] is the drop from J1.1 at port a
# per ampere drawn at port b (20 C; HOT_CU applied where the four-stall points use it).
BAT_PORTS = ('U9', 'Q120', 'R80')


def split(v, rest, conv_amps, zq_u=0.0):
    """At J1 voltage v: the fire current and the converter current solved together. rest is the fire branch from J1.1
    (its BAT_IN term the network's J1 -> Q120.3 resistance), conv_amps(v, i_fire) the converter current drawn at U9.5
    with the fire current's drop on the shared copper, and zq_u the transfer resistance J1 -> Q120.3 per ampere at U9.5,
    so i_fire = (v - zq_u x i_conv) / rest. The coupling is milliohms against ohms: a fixed-point iteration converges in
    a few steps. rest = inf: no fire."""
    if math.isinf(rest):
        return 0.0, conv_amps(v, 0.0)
    i_fire = v / rest
    i_conv = conv_amps(v, i_fire)
    for _ in range(200):
        i_new = (v - zq_u * i_conv) / rest
        c_new = conv_amps(v, i_new)
        done = abs(i_new - i_fire) < 1e-15 and abs(c_new - i_conv) < 1e-15
        i_fire, i_conv = i_new, c_new
        if done:
            break
    else:
        raise NoPoint(f'fire / converter split did not converge at J1 {v} V')
    return i_fire, i_conv


def loaded(rest, other, stalls, open_v=PACK_V, z=None):
    """J1's terminal voltage (BAT_IN_V), the fire current and the converter current with the pack model.
    other: the converter load, either a constant power (W) at BAT_IN (the quadratic; no network) or a function
    (J1 voltage, fire current) -> converter current (A) (R12F10-TRI-09; R12F12-TRI-30: bisection of
    v = open - PACK_R x (i_fire + i_conv + stalls x STALL_A), both from split(); they fall as v falls, so the root is
    unique). z: the hot BAT_IN network (bat_in_network's Z x HOT_CU; None = no shared copper), which also gives the
    voltage at U9.5 and at R80.1. Returns a dict."""
    if not callable(other):
        a, b = 1 + PACK_R / rest, open_v - PACK_R * STALL_A * stalls
        v = (b + math.sqrt(b * b - 4 * a * PACK_R * other)) / (2 * a)
        return dict(BAT_IN_V=v, fire_A=v / rest, converter_A=other / v)
    zq_u = z['Q120']['U9'] if z else 0.0

    def f(v):
        try:
            i_fire, i_conv = split(v, rest, other, zq_u)
        except NoPoint:                                           # below the collapse: the pack cannot sit here
            return -1.0
        return open_v - PACK_R * (i_fire + i_conv + STALL_A * stalls) - v
    lo, hi = open_v / 2, open_v
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    v = (lo + hi) / 2
    i_fire, i_conv = split(v, rest, other, zq_u)
    out = dict(BAT_IN_V=v, fire_A=i_fire, converter_A=i_conv)
    if z:
        out.update({f'{p}_V': v - z[p]['U9'] * i_conv - z[p]['Q120'] * i_fire for p in BAT_PORTS})
    return out


def fire_budget(copper, gnd_return, conv, z20):
    """conv(v, i_fire): raw_point at J1 voltage v with the fire current i_fire on the shared BAT_IN copper. z20: the
    BAT_IN network (bat_in_network's Z_ohm, 20 C). R12F10-TRI-09: the pack's converter load keeps R10 GAP-1's
    convention (the converters' input power and R92's bleed as a constant power at BAT_IN, other_load_w), but D5's loss
    is 0.45 V x U2's own input current from raw_point's self-consistent solve at that BAT_IN. The convention leaves U9's
    and the copper's own loss (and the bucks drawing their power at their lower input nodes) off the pack;
    pack_load_sensitivity gives the four-stall point with the pack carrying raw_point's whole current instead.
    R12F12-TRI-30: BAT_IN is one network (J1.1, U9.5, Q120.3, R80.1). The fire branch's BAT_IN term is the network's
    J1 -> Q120.3 resistance (fire_copper's BAT_IN track sum stays in copper_by_net as the record of the copper), the
    converter current lowers Q120's drain by Z[Q120][U9] x i_conv, the fire current lowers U9.5 by Z[U9][Q120] x i_fire,
    and both currents are solved together at every point (split, loaded); each point also gives R80.1, U9's EN divider
    top, for the chatter figures (Calculation on CAD copper at 70 C / Inference: allocations, efficiency, SS34 VF)."""
    base, other_parts = other_load_w()
    z = {a: {b: r * HOT_CU for b, r in row.items()} for a, row in z20.items()}
    zq_u = z['Q120']['U9']
    main_amps = lambda v, i_f: (base + conv(v, i_f)['D5_loss_W']) / v        # noqa: E731
    whole_amps = lambda v, i_f: conv(v, i_f)['I_total_A']                     # noqa: E731
    cu20 = sum(c['R_20C_ohm'] for c in copper.values())
    cu20_tracks_other = sum(c['R_20C_ohm'] for k, c in copper.items() if k != 'BAT_IN')
    r_batin = z['Q120']['Q120']
    cu70 = cu20_tracks_other * HOT_CU + r_batin
    ground = max(GND_ALLOWANCE, gnd_return or 0.0)
    rest = R134_HOT + MATCH + LEADS + cu70 + ground + TERMINALS + 2 * PFET_HOT + Q124_HOT
    stalls = {}
    for n in range(5):
        op = loaded(rest, main_amps, n, z=z)
        stalls[str(n)] = dict(op, margin_pct=(op['fire_A'] / FLOOR_A - 1) * 100)
    dummy = dummy_fire(rest, main_amps, cu70, z)
    shorts = {}
    for label, drop in (('match_shorted', MATCH), ('match_and_leads_shorted', MATCH + LEADS)):
        for n in (0, 4):
            op = loaded(rest - drop, main_amps, n, z=z)
            i = op['fire_A']
            shorts[f'{label}_{n}_stalls'] = dict(op, Q120_I2R_W=i * i * PFET_HOT, Q121_I2R_W=i * i * PFET_HOT,
                                                 Q124_I2R_W=i * i * Q124_HOT, R134_W=i * i * R134_HOT)
    # Q120 / Q121 gate: the R119 || R120 / R121 divider hangs on ACT_FET_S (the common sources of Q120 / Q121; Q120's
    # drain is BAT_IN, R119 / R120 / C120 sit between ACT_FET_S and ACT_GATE, netlist), so
    # VGS = -(V_ACT_FET_S - Q122 drop 0.1 V) x Rgs / (Rgs + R121), Rgs = R119 || R120 = 50k (1 %), R121 10k.
    # During a fire V_ACT_FET_S = Q120's drain - I_fire x RDS(Q120) (R12F2-TRI-08); R12F5-TRI-03 / R12F12-TRI-30:
    # Q120's drain is J1 less the BAT_IN network's drop at Q120.3 (the fire current x Z[Q120][Q120] and the converter
    # current x Z[Q120][U9]); R119 / R120 tap ACT_FET_S at Q120's source pad through a stub that carries no current,
    # while the fire current runs the ACT_FET_S copper on to Q121's source. With the bus on and no fire, Q120 carries
    # only the sense banks' sub-mA current, so V_ACT_FET_S = Q120's drain.
    r_fets = copper['ACT_FET_S']['R_20C_ohm'] * HOT_CU
    r_gs_min = 50e3 * .98
    ratio = r_gs_min / (r_gs_min + 10e3 * 1.02)
    tau = (50e3 * 10e3 / 60e3) * 1.02 * (1e-6 * 1.10 * 1.15)      # C120 1 uF +10 % tolerance, +15 % temperature
    # D-R12-91 (R12F1-TRI-19): the pack voltage above which |VGS| can exceed 12 V uses the largest ratio, 51k / 60.8k
    # (Rgs +2 %, R121 -2 %), not the smallest one the drive-strength figures above use
    r_gs_max = 50e3 * 1.02
    ratio_max = r_gs_max / (r_gs_max + 10e3 * .98)

    def vgs(v, amps=0.0, i_conv=0.0):
        """|VGS| of Q120 (the divider's own FET); Q121's is smaller by amps x r_fets."""
        return (v - zq_u * i_conv - amps * (r_batin + PFET_HOT) - .1) * ratio

    def during_fire(v, amps, i_conv):
        drain = v - zq_u * i_conv - amps * r_batin
        s120 = drain - amps * PFET_HOT
        q120, q121 = vgs(v, amps, i_conv), vgs(v, amps, i_conv) - amps * r_fets
        return dict(BAT_IN_V=v, fire_A=amps, converter_A=i_conv, BAT_IN_copper_drop_V=v - drain,
                    BAT_IN_copper_drop_parts_V=dict(fire=amps * r_batin, converter=zq_u * i_conv),
                    Q120_drain_V=drain, Q120_drop_V=amps * PFET_HOT, Q120_source_V=s120,
                    ACT_FET_S_copper_drop_V=amps * r_fets, Q121_source_V=s120 - amps * r_fets,
                    vgs_Q120_V=-q120, vgs_Q121_V=-q121,
                    margin_to_minus_4V5_row_V=dict(Q120=q120 - 4.5, Q121=q121 - 4.5))
    four = stalls['4']
    point = conv(four['BAT_IN_V'], four['fire_A'])
    other_parts = dict(other_parts, d5_W=point['D5_loss_W'])
    whole = loaded(rest, whole_amps, 4, z=z)
    sensitivity = dict(
        four_stall_BAT_IN_V=whole['BAT_IN_V'], four_stall_A=whole['fire_A'], converter_A=whole['converter_A'],
        four_stall_R80_V=whole['R80_V'], four_stall_U9_V=whole['U9_V'], four_stall_Q120_V=whole['Q120_V'],
        delta_BAT_IN_V=whole['BAT_IN_V'] - four['BAT_IN_V'], delta_fire_A=whole['fire_A'] - four['fire_A'],
        basis=('the pack carries raw_point\'s whole converter current (U9 RON maximum and the J1 -> U9 / RAW copper '
               'at 70 C, U400 / U403 at their own input nodes, D5 = U2\'s input current) instead of GAP-1\'s constant '
               'power at BAT_IN, solved together with the fire current on the BAT_IN network (R12F12-TRI-30); not '
               'used by the figures above (Calculation / Inference: allocations, efficiency, SS34 VF)'))

    def at_j1(v):
        i_f, i_c = split(v, rest, main_amps, zq_u)
        return i_f, i_c
    during = {}
    for v in (6.0, 7.4, 8.4):
        i_f, i_c = at_j1(v)
        during[f'{v:g}V'] = dict(Q120=-vgs(v, i_f, i_c), Q121=-vgs(v, i_f, i_c) + i_f * r_fets)
    gate = dict(q120_q121_vgs_four_stall_fire=during_fire(four['BAT_IN_V'], four['fire_A'], four['converter_A']),
                # at a given J1 voltage v the fire and converter currents are split()'s (the main convention)
                q120_q121_vgs_during_fire_V=during,
                q120_q121_vgs_shorted_four_stall={k: during_fire(shorts[f'{k}_4_stalls']['BAT_IN_V'],
                                                                 shorts[f'{k}_4_stalls']['fire_A'],
                                                                 shorts[f'{k}_4_stalls']['converter_A'])
                                                  for k in ('match_shorted', 'match_and_leads_shorted')},
                q120_q121_vgs_bus_on_no_fire_V={f'{v:g}V': -vgs(v) for v in (6.0, 7.4, 8.4, 12.6, 19.9)},
                q120_q121_time_to_minus_4V5_ms={f'{v:g}V': (-tau * math.log(1 - 4.5 / vgs(v)) * 1e3 if vgs(v) > 4.5
                                                            else None) for v in (6.0, 7.4, 8.4)},
                q120_vgs_note=('during a fire Q120\'s drain = J1 - I_fire x Z[Q120][Q120] - I_conv x Z[Q120][U9] (the '
                               'BAT_IN network at 70 C, R12F12-TRI-30) and its source a further I_fire x 73.5 mOhm '
                               'lower (Q120 hot, the -4.5 V row x 1.225; R12F2-TRI-08), and Q121\'s source sits a '
                               'further I_fire x the ACT_FET_S copper lower (copper at 70 C; R12F5-TRI-03); the enable '
                               'time and the 12 V corner have no fire or converter current (bus on, before the fire). '
                               'A shorted match takes |VGS| below the -4.5 V row, where RDS(on) is above the row value '
                               'used here (Inference; a fault case, not the fire budget)'),
                q120_rds_row='AO3401A RDS(on) <= 60 mOhm at VGS -4.5 V (25 C)', q120_vgs_abs_max_V=12.0,
                q120_vgs_exceeds_12V_above_pack_V=12.0 / ratio_max + .1, q120_vgs_ratio_min_max=[ratio, ratio_max],
                # R12F3-TRI-06: PE4 drives Q124's gate through R126 220R into R128 10k; DS12110 Rev 8 Table 158
                # guarantees only VOH >= VDD - 0.4 V (|IIO| 4 mA, 1.62-3.6 V; 8 mA, 2.7-3.6 V). R12F4-TRI-02: PE4's
                # steady load includes R127 1k (about 3.54 mA at the 3V3 drift minimum, <= 3.93 mA at the drift maximum
                # with every resistor at its drift low end; R12F6-TRI-03's PFM window), within the 4 mA row; VDD = the 3V3
                # drift minimum, R126 / R128 at their drift ends (+/-1.67 %, r12_budget TOL['drift']; R12F5-TRI-05)
                q124_vgs_min_V=(Q124_VDD_MIN - VOH_DROP) * 10e3 * (1 - TD) / (10e3 * (1 - TD) + 220 * (1 + TD)),
                q124_vgs_min_basis=dict(vdd_min_V=Q124_VDD_MIN, voh_drop_V=VOH_DROP,
                                        pe4_load_mA=pe4_load_mA(Q124_VDD_MIN),
                                        pe4_load_max_mA=pe4_load_mA(Q124_VDD_MAX, r12_budget.TOL['drift']),
                                        pe4_load_vdd_max_V=Q124_VDD_MAX, voh_row_mA=VOH_ROW_MA,
                                        pe4_load_within_voh_row=pe4_load_mA(Q124_VDD_MAX,
                                                                            r12_budget.TOL['drift']) <= VOH_ROW_MA,
                                        pe4_load_parts='R127 1k to GND, and R126 220R + R128 10k (10.22 kOhm) to GND',
                                        resistor_tolerance=TD,
                                        source='DS12110 Rev 8 Table 158 p. 247 (VOH VDD - 0.4 V at 4 / 8 mA); 3V3 '
                                               'drift minimum and maximum (r12_windows.json: the SLUSDW3A section 7.8 '
                                               'PFM band, R12F6-TRI-03); R126 220R / R127 1k / R128 10k 1 % + 100 '
                                               'ppm/K over 67 K (the drift case)',
                                        label=(f'Calculation / Inference (3V3 window, D-R12-139) (PE4 load about '
                                               f'{pe4_load_mA(Q124_VDD_MIN):.2f} mA, <= {pe4_load_mA(Q124_VDD_MAX, TD):.2f} '
                                               'mA with drift, within the 4 mA VOH row; the 3V3 PFM band at R12\'s VIN '
                                               'and resistor drift)')),
                q124_vgs_row_V=2.5, q124_vgs_th_max_V=1.45,
                q124_gate_tau_us=220 * 220e-9 * 1e6,
                basis='R119 / R120 100k, R121 10k, C120 1 uF 50 V X5R (C15849), R126 220R / R127 1k / R128 10k / C126 '
                      '220 nF (values unchanged from R10 / R11); AO3401A / AO3400A datasheet rows (D-R12-10); C120 '
                      'tolerance and temperature factors as R10 (no bias credit); Q122 drop 0.1 V and the Q120 hot '
                      'factor, Inference')
    return dict(
        status='Calculation on R12 CAD copper with R10 GAP-1 pack model; Inference: FET hot factors, pack, harness, '
               'match, converter load allocations',
        copper_by_net={k: dict(length_mm=v['length_mm'], widths_mm=v['widths_mm'], layers=v['layers'],
                               R_20C_mohm=v['R_20C_ohm'] * 1e3) for k, v in copper.items()},
        copper_20C_ohm=cu20, copper_70C_ohm=cu70,
        copper_basis=('copper_20C_ohm: the five fire nets\' series tracks (fire_copper); copper_70C_ohm, the loop\'s: '
                      'the four nets other than BAT_IN at 70 C plus the BAT_IN network\'s J1 -> Q120.3 resistance at '
                      '70 C (R12F12-TRI-30; it replaces the BAT_IN track sum)'),
        bat_in_network_70C_ohm=z, bat_in_fire_term_70C_ohm=r_batin,
        gnd_return_dc_ohm=gnd_return, gnd_return_used_ohm=ground,
        R134_hot_ohm=R134_HOT, pfet_hot_ohm=PFET_HOT, q124_hot_ohm=Q124_HOT, match_ohm=MATCH, leads_ohm=LEADS,
        terminal_allowance_ohm=TERMINALS, fire_branch_without_pack_ohm=rest, total_loop_ohm=rest + PACK_R,
        other_converter_load_W=base + point['D5_loss_W'], other_load_parts=other_parts,
        converter_point_four_stall=point, pack_load_sensitivity=sensitivity,
        converter_load_basis=('R10 GAP-1 constant power at BAT_IN: the converters\' input power and R92 at 7.4 V '
                              '(other_load_w), plus D5\'s loss 0.45 V x U2\'s input current from raw_point at that '
                              'BAT_IN (R12F10-TRI-09; it was 0.45 V x 0.3 A); other_converter_load_W and d5_W at the '
                              'four-stall point; the converter current (power / J1) is drawn at U9.5 of the BAT_IN '
                              'network (R12F12-TRI-30) (Calculation / Inference: allocations, efficiency, SS34 VF)'),
        floor_A=FLOOR_A, stalls=stalls,
        four_stall_A=stalls['4']['fire_A'], four_stall_BAT_IN_V=stalls['4']['BAT_IN_V'],
        four_stall_R80_V=stalls['4']['R80_V'], four_stall_converter_A=stalls['4']['converter_A'],
        four_stall_ok=stalls['4']['fire_A'] >= FLOOR_A, shorted=shorts, gate=gate, dummy_fire=dummy,
        r12_budget_placeholder_four_stall_A=r12_budget.fire()['four_stall_A'],
        shorted_igniter_guard=dict(
            watchdog_ms=[960 / 33600 * 1e3, 960 / 29400 * 1e3], allocations_ms=[.2, .5, 1.5],
            guard_ms=960 / 29400 * 1e3 + .2 + .5 + 1.5, limit_ms=36.0,
            R134_min_70C_ohm=2 * .99 * (1 - 100e-6 * 45), fault_W=8.4 ** 2 / (2 * .99 * (1 - 100e-6 * 45)),
            note='R10 GAP-5 inputs unchanged on R12 (IWDG 960 LSI cycles, R126 / R127 / R128 / C126, R134 part): '
                 'carried by identity of inputs (Calculation on allocations / Inference)'))


def dummy_fire(rest, other, cu70, z):
    """D-R12-109's first-article dummy fire (R12F9-TRI-05): a 2 ohm dummy plus 0.3 ohm leads, the 7.4 V / 0.15 ohm source,
    no stall, the budget converter loads. Reject line: BAT_IN - RAW_ACT above 0.4 V. The drop bound is I x (two AO3401A at
    their 70 C 73.5 mOhm + all the fire copper at 70 C, its BAT_IN term the network's J1 -> Q120.3) plus the converter
    current's share of the J1 -> Q120.3 copper (R12F12-TRI-30). The fire budget's R134 is at its hot high end (the current
    minimising corner), so its idle current is not an upper bound; the bound takes R134 at its low end at 70 C, in each
    resistor case: 1 % (2 x 0.99 x (1 - 100 ppm/K x 45 K)) and the drift case (2 x (1 - TOL['drift']), r12_budget's
    bound convention), and the drift case is the bound (Calculation / Inference: hot factors, pack, converter loads,
    copper model)."""
    fets = 2 * PFET_HOT
    r134 = dict(budget_hot_high=R134_HOT, initial_70C_low=2 * .99 * (1 - 100e-6 * 45), drift_low=2 * (1 - TOL['drift']))
    out = {}
    for k, r in r134.items():
        op = loaded(rest - R134_HOT + r, other, 0, z=z)
        v, i, ic = op['BAT_IN_V'], op['fire_A'], op['converter_A']
        out[k] = dict(R134_ohm=r, BAT_IN_V=v, fire_A=i, converter_A=ic, fets_drop_V=i * fets,
                      converter_drop_at_Q120_V=ic * z['Q120']['U9'],
                      drop_bound_V=i * (fets + cu70) + ic * z['Q120']['U9'])
    bound = max(out[k]['drop_bound_V'] for k in out)
    return dict(by_R134=out, fets_hot_ohm=fets, copper_70C_ohm=cu70, drop_bound_V=bound,
                drop_bound_case=max(out, key=lambda k: out[k]['drop_bound_V']), reject_above_V=0.4,
                bound_below_reject=bound < 0.4,
                label='Calculation / Inference (FET hot factors, pack model, converter loads, copper model; the R134 '
                      'drift case Inference): the drop bound takes R134 at its current-maximising low end')


def holdup(four_stall_bat):
    """C84 (470 uF polymer, 300.8 uF allowance as R10) holds VLOGIC only; D5 blocks RAW_PROTECTED (D-R12-04), so the
    port and camera bucks and R92 are not on it. Constant-power loads to 3.8 V (R10 / R11's end point, Inference for
    the LMR50410): unshed logic 0.6-1.4 W + microSD write 3.3 V x 0.2 A / 0.85-0.80; shed logic 0.62 W + microSD idle
    3.3 V x 0.03 A / 0.85-0.80. Start points: battery break at the 7.4 V launch floor less U9 and D5 (D5 VF 0.25-0.45 V,
    Inference; U9 at SLVSFC9C's 0.045 ohm maximum x 1.5 A, the current Inference); PA6 trip at the window below, at the
    nominal ratio and with the divider in each resistor case (R12F8-TRI-08), the window carrying PA6's +/-250 nA input
    leakage through R60 || R61 (R12F10-TRI-08, r12_budget.pa6_trip_window). No credit for C6 / C99 (Inference)."""
    loads = dict(unshed=(.6 + 3.3 * .2 / .85, 1.4 + 3.3 * .2 / .80), shed=(.62 + 3.3 * .03 / .85, .62 + 3.3 * .03 / .80))
    def ms(c, v0, w, v_end=3.8):
        return .5 * c * (v0 ** 2 - v_end ** 2) / w * 1e3
    win = pa6_window()
    u9 = U9_RON * 1.5
    out = {}
    for case, (wmin, wmax) in loads.items():
        out[case] = dict(
            load_W=[wmin, wmax],
            battery_break_ms=[ms(300.8e-6, PACK_V - .45 - u9, wmax), ms(470e-6, PACK_V - .25 - u9, wmin)],
            pa6_trip_ms={k: [ms(300.8e-6, w[0], wmax), ms(470e-6, w[1], wmin)] for k, w in win['trip_V'].items()},
            battery_break_to_3V5_ms=[ms(300.8e-6, PACK_V - .45 - u9, wmax, 3.5), ms(470e-6, PACK_V - .25 - u9, wmin, 3.5)])
        out[case]['pa6_trip_range_ms'] = {k: [min(out[case]['pa6_trip_ms'][j][0] for j in ('nominal_ratio', k)),
                                              max(out[case]['pa6_trip_ms'][j][1] for j in ('nominal_ratio', k))]
                                          for k in TOL}
    out['r11_case_c_ms'] = [.464, .539]
    out['label'] = ('Calculation / Inference (constant-power allocations, D5 drop, C84 allowance, 3.8 V end point, PA6\'s '
                    'input leakage row in analog mode; the drift case Inference); pa6_trip_range_ms is the range over '
                    'the divider tolerance of that case')
    return out


def pa6_window():
    """PA6 = VLOGIC x R61 / (R60 + R61), R60 100k / R61 10k, both 0.1 % 25 ppm/K thin film since R12F9-TRI-04 (round 9
    lane B, owner option (b)); firmware threshold 0.425-0.455 V (D-R12-21's 0.42-0.45 V moved, O-R12-17).
    trip_V: 'nominal_ratio' is R10 / R11's method (x 11); 'initial' / 'drift' put R60 / R61 at their own worst ends of
    R12's two resistor cases for these parts (r12_budget.PA6_TOL: 0.1 %; 0.1 % + 25 ppm/K over 67 K); every window
    carries PA6's +/-250 nA input leakage through R60 || R61 (R12F10-TRI-08) (Calculation / Inference: drift, the
    leakage row in analog mode)."""
    return dict(threshold_V=list(r12_budget.PA6_THRESHOLD),
                divider_tolerance=dict(r12_budget.PA6_TOL),
                trip_V=dict(nominal_ratio=r12_budget.pa6_trip_window(),
                            **{case: r12_budget.pa6_trip_window(tol) for case, tol in r12_budget.PA6_TOL.items()}),
                ratio={case: list(r12_budget.pa6_ratio(tol)) for case, tol in r12_budget.PA6_TOL.items()},
                leakage_A=r12_budget.PA6_LEAK,
                leakage_offset_V=dict(nominal_ratio=r12_budget.pa6_leak_V(),
                                      **{case: r12_budget.pa6_leak_V(tol) for case, tol in r12_budget.PA6_TOL.items()}))


def pa6_corners(fire, u9_feed_ohm, raw_ohm, vlogic_ohm=None, z_fire_ohm=0.0):
    """VLOGIC during the fire at the healthy / match-shorted / match-and-leads-shorted four-stall points, against the
    PA6 trip window (O-R12-07): BAT_IN less U9's RON (SLVSFC9C's 0.045 ohm maximum, R12F8-TRI-07) and the J1 -> U9.5
    copper at the whole
    converter current, less the RAW_PROTECTED drop at D5.2, less D5 (SS34 VF 0.25-0.45 V, Inference).
    R12F3-TRI-09: each RAW_PROTECTED branch is charged at its own share of the U9.6 -> D5.2 resistance, not all at
    U9 -> D5's: in a resistive network fed from U9.6, the drop a current into sink b causes at sink a (the mutual
    resistance) is at most the smaller of the two sinks' own resistances to U9.6 (maximum principle and reciprocity),
    so U403 (camera) is charged at min(R(U9 -> U403), R(U9 -> D5)), U400 (ports) at min(R(U9 -> U400), R(U9 -> D5)),
    and D5's own load and R92's bleed at R(U9 -> D5) (dc_solves, each an upper bound). The drop is therefore an upper
    bound, and the margins lower bounds (Calculation on the DC solves; the allocations Inference). Margins are given to
    the trip top at the nominal ratio and in both resistor cases (R12F8-TRI-06); D-R12-21's margin of the trip bottom over
    U9's turn-off corner seen through D5 (r12_budget.vlogic) is given in each case too.
    R12F9-TRI-04: all copper at 70 C (HOT_CU), and the VLOGIC copper from D5's cathode to R60's tap (the PA6 divider top)
    is charged too: U2's input current (logic + microSD write, constant power, at the lowest VLOGIC of the case) times
    min(R(D5 -> R60), R(D5 -> U2)) (vlogic_ohm; the same mutual-resistance bound).
    R12F10-TRI-09: the currents are raw_point's self-consistent solve at each case's BAT_IN: D5's current is U2's input
    current (it was the branch's allocated power / BAT_IN, 24 mA short at the healthy four-stall point), D5's loss is
    0.45 V x that current, and U400 / U403 draw their input power at their own nodes, not at BAT_IN.
    R12F10-TRI-08: the trip window carries PA6's own input leakage (r12_budget.pa6_trip_window).
    R12F12-TRI-30: u9_feed_ohm is the BAT_IN network's J1 -> U9.5 term and z_fire_ohm its J1 -> U9.5 / Q120.3 transfer
    resistance (20 C, taken at 70 C here): each case's own fire current lowers U9.5 too.
    R12F12-TRI-31: the upper end of VLOGIC_V (D5 at 0.25 V) is its own raw_point solve at that VF (U2's input current
    and the branch currents at the higher VLOGIC), not the 0.45 V point's currents."""
    parts = fire['other_load_parts']
    # R12F9-TRI-04: the DC solves are 20 C copper; the four-stall BAT_IN is the fire loop's 70 C corner, so the branch
    # copper is taken at 70 C too (HOT_CU), or the drop is not an upper bound at the model's own temperature
    raw20, feed20 = dict(raw_ohm), u9_feed_ohm
    raw_ohm = {k: r * HOT_CU for k, r in raw20.items()}
    u9_feed_ohm = feed20 * HOT_CU
    z_fire = z_fire_ohm * HOT_CU
    vl20 = dict(vlogic_ohm or {})
    r_vl = min(vl20.values()) * HOT_CU if vl20 else 0.0
    r_d5 = raw_ohm['D5']
    r_u2 = vl20['U2'] * HOT_CU if 'U2' in vl20 else 0.0
    shared = {'U403 (camera)': min(raw_ohm['U403'], r_d5), 'U400 (ports)': min(raw_ohm['U400'], r_d5),
              'D5 (logic, microSD) and R92': r_d5}
    win = pa6_window()
    out = {}
    cases = {'healthy': fire['stalls']['4'], 'match_shorted': fire['shorted']['match_shorted_4_stalls'],
             'match_and_leads_shorted': fire['shorted']['match_and_leads_shorted_4_stalls']}
    for name, c in cases.items():
        v, i_fire = c['BAT_IN_V'], c.get('fire_A', 0.0)
        pt = raw_point(v, parts, u9_feed_ohm, raw_ohm, r_u2, i_fire=i_fire, z_fire_ohm=z_fire)
        hi = raw_point(v, parts, u9_feed_ohm, raw_ohm, r_u2, vf=r12_budget.D5_VF[0], i_fire=i_fire, z_fire_ohm=z_fire)
        i = pt['I_total_A']
        drop = v - pt['node_V']['D5']
        raw_drop = pt['U9_out_V'] - pt['node_V']['D5']
        lumped = i * (U9_RON + u9_feed_ohm + r_d5) + i_fire * z_fire
        i_vl = pt['currents_A']['D5']
        vl_drop = i_vl * r_vl
        drop_hi, vl_drop_hi = v - hi['node_V']['D5'], hi['currents_A']['D5'] * r_vl
        vl = [v - drop - .45 - vl_drop, v - drop_hi - hi['D5_VF_V'] - vl_drop_hi]
        out[name] = dict(BAT_IN_V=v, fire_A=i_fire, converter_A=i, branch_A=pt['currents_A'],
                         U9_and_copper_drop_V=drop, fire_drop_at_U9_V=pt['fire_drop_at_U9_V'],
                         RAW_PROTECTED_drop_at_D5_V=raw_drop, D5_A=i_vl, D5_loss_W=pt['D5_loss_W'],
                         U2_VIN_V=pt['U2_VIN_V'], VLOGIC_A=i_vl, VLOGIC_copper_drop_at_R60_V=vl_drop,
                         lumped_drop_V_superseded=lumped, VLOGIC_V=vl,
                         upper_end_VF_0V25=dict(converter_A=hi['I_total_A'], branch_A=hi['currents_A'],
                                                U9_and_copper_drop_V=drop_hi, D5_A=hi['currents_A']['D5'],
                                                VLOGIC_copper_drop_at_R60_V=vl_drop_hi, U2_VIN_V=hi['U2_VIN_V']),
                         margin_to_trip_top_V={k: vl[0] - w[1] for k, w in win['trip_V'].items()})
    out['branch_shared_ohm'] = dict(shared)
    out['raw_point_ohm'] = dict(raw_ohm)
    out['raw_point_ohm_20C'] = raw20
    out['J1_to_U9_ohm_20C'], out['J1_to_U9_ohm'] = feed20, u9_feed_ohm
    out['fire_coupling_at_U9_ohm_20C'], out['fire_coupling_at_U9_ohm'] = z_fire_ohm, z_fire
    out['copper_factor_70C'] = HOT_CU
    out['vlogic_ohm_20C'], out['vlogic_shared_ohm'] = vl20, r_vl
    out['window'] = win
    out['u9_ron_ohm'] = U9_RON
    vlog = r12_budget.vlogic()
    out['u9_turn_off_through_d5_V'] = vlog['u9_turn_off_through_d5_V']
    out['trip_bottom_above_u9_turn_off_V'] = {k: m['above_u9_turn_off_through_d5']
                                              for k, m in vlog['pa6_retuned_margins_V'].items()}
    out['trip_bottom_basis'] = vlog['pa6_retuned_margins_basis']
    out['owner_options'] = pa6_options(out, vlog['u9_turn_off_through_d5_V'])
    out['label'] = ('Calculation / Inference (DC-solve upper bounds with the copper at 70 C, the fire loop\'s corner '
                    '(R12F9-TRI-04), mutual resistance bounded by the smaller point resistance, the VLOGIC copper to R60 '
                    'included; the branch currents solved self-consistently, D5\'s current = U2\'s input current '
                    '(R12F10-TRI-09); the BAT_IN network with each case\'s fire current (R12F12-TRI-30); the upper end '
                    'at D5 0.25 V with its own currents (R12F12-TRI-31); PA6\'s +/-250 nA input leakage through R60 || '
                    'R61 in the window (R12F10-TRI-08); '
                    'U9 RON at the SLVSFC9C maximum; SS34 VF, the load allocations, the 70 C copper temperature, the '
                    'leakage row in analog mode and the resistor drift case are Inference); the drop is an upper '
                    'bound, the margins lower bounds')
    return out


# R12F9-TRI-04 owner option (b), adopted in round 9 lane B: R60 / R61 as 0.1 % 25 ppm/K thin film (YAGEO
# RT0402BRD07100KL C852472, RT0402BRD0710KL C190095, already R401's line; JLC listing 2026-11-08, Extended; circuit.json)
PA6_PRECISE = dict(R60='YAGEO RT0402BRD07100KL (C852472), 100k 0.1 % 25 ppm/K, Extended, $0.0256 (1-499)',
                   R61='YAGEO RT0402BRD0710KL (C190095, R401\'s BOM line), 10k 0.1 % 25 ppm/K, Extended, $0.0246 (1-499)')


def pa6_options(corners, u9_off_d5):
    """R12F9-TRI-04: what each owner-level change gives the PA6 margins. Option (b) is adopted (round 9 lane B): the
    0.1 % divider with the band the drift case's room centred in round 9 (band_derivation; r12_budget.PA6_THRESHOLD),
    so the rows below now evaluate the adopted band 0.425-0.455 V, not D-R12-21's 0.42-0.45 V. R12F10-TRI-08: each
    limit carries PA6's input leakage offset (r12_budget.pa6_leak_V), which narrows the room at both ends. Two limits:
    the trip top below the lowest four-stall VLOGIC (healthy / shorted cases, VLOGIC at SS34's 0.45 V) and the trip
    bottom above U9's highest turn-off VLOGIC through D5 at 0.25 V (D-R12-21; the EN chain stays 1 % in each case).
    (a) 0.1 % 25 ppm/K divider (r12_budget.TOL_PRECISE, 0.1 %; 0.1 % + 25 ppm/K x 67 K); (b) the firmware threshold
    alone, with the 1 % divider: the highest threshold top that clears the healthy four-stall point and the lowest
    bottom that clears U9's turn-off, and the room between them against the present 30 mV band; (c) the same room
    with the 0.1 % divider (Calculation / Inference: SS34 VF, allocations, 70 C copper, drift)."""
    thr = r12_budget.PA6_THRESHOLD
    vmin = {k: corners[k]['VLOGIC_V'][0] for k in ('healthy', 'match_shorted', 'match_and_leads_shorted')}
    out = {}
    for name, tols in (('divider_1pct', r12_budget.TOL), ('divider_0p1pct', r12_budget.TOL_PRECISE)):
        row = {}
        for case, tol in tols.items():
            lo, hi = r12_budget.pa6_ratio(tol)
            win = r12_budget.pa6_trip_window(tol)
            e = r12_budget.pa6_leak_V(tol)                         # R12F10-TRI-08: PA6's own input leakage
            top_max = vmin['healthy'] * lo - e
            bottom_min = u9_off_d5[case] * hi + e
            row[case] = dict(tolerance=tol, trip_V=win,
                             margin_to_trip_top_V={k: v - win[1] for k, v in vmin.items()},
                             trip_bottom_above_u9_turn_off_V=win[0] - u9_off_d5[case],
                             threshold_top_max_for_healthy_V=top_max, threshold_bottom_min_for_u9_V=bottom_min,
                             threshold_room_V=top_max - bottom_min, present_band_V=thr[1] - thr[0],
                             present_band_fits=top_max - bottom_min >= thr[1] - thr[0])
            # the present 30 mV band centred in that room, and the margins it gives (both limits at once)
            mid = (top_max + bottom_min) / 2
            band = [mid - (thr[1] - thr[0]) / 2, mid + (thr[1] - thr[0]) / 2]
            row[case]['centred_band_V'] = band
            row[case]['centred_band_margins_V'] = dict(healthy_to_trip_top=vmin['healthy'] - (band[1] + e) / lo,
                                                       trip_bottom_above_u9_turn_off=(band[0] - e) / hi
                                                       - u9_off_d5[case])
        out[name] = row
    # the band the 0.1 % drift case's room centres (its 30 mV band, rounded to the millivolt; round 9 lane B adopted
    # 0.425-0.455 V from it as r12_budget.PA6_THRESHOLD). R12F10-TRI-08 / -09 narrow the room and move its centre, so
    # the derived band is recorded beside the adopted one; the gate is that the adopted band lies inside the room and
    # clears both limits in every case at the adopted divider (margins_V)
    d = out['divider_0p1pct']['drift']
    centre = round((d['threshold_top_max_for_healthy_V'] + d['threshold_bottom_min_for_u9_V']) / 2, 3)
    width = thr[1] - thr[0]
    band = [round(centre - width / 2, 4), round(centre + width / 2, 4)]

    def band_margins(b):
        m = {}
        for case, tol in r12_budget.PA6_TOL.items():
            lo, hi = r12_budget.pa6_ratio(tol)
            e = r12_budget.pa6_leak_V(tol)
            m[case] = dict(healthy_to_trip_top=vmin['healthy'] - (b[1] + e) / lo,
                           trip_bottom_above_u9_turn_off=(b[0] - e) / hi - u9_off_d5[case])
        return m
    margins = band_margins(list(thr))
    room = [d['threshold_bottom_min_for_u9_V'], d['threshold_top_max_for_healthy_V']]
    out['band_derivation'] = dict(
        room_drift_V=room,
        room_width_drift_V=d['threshold_room_V'], band_width_V=width, centre_V=centre, band_V=band,
        equals_threshold=[round(x, 4) for x in thr] == band, adopted_band_V=list(thr),
        adopted_inside_room=room[0] <= thr[0] and thr[1] <= room[1], derived_band_margins_V=band_margins(band),
        margins_V=margins, both_limits_clear=all(v > 0 for m in margins.values() for v in m.values()),
        margins_basis='margins_V and both_limits_clear: the adopted band (r12_budget.PA6_THRESHOLD); '
                      'derived_band_margins_V: band_V',
        basis='the 0.1 % drift case: highest top = healthy four-stall VLOGIC minimum x lowest ratio less PA6\'s '
              'leakage offset; lowest bottom = U9 turn-off VLOGIC through D5 (drift EN chain) x highest ratio plus '
              'that offset (+/-250 nA x R60 || R61 at +tol, R12F10-TRI-08); the 30 mV band centred in that room, '
              'centre rounded to 1 mV (Calculation / Inference as pa6_corners)')
    out['adopted'] = 'divider_0p1pct with the band_derivation band (owner option (b), round 9 lane B; R12F9-TRI-04)'
    out['parts_0p1pct'] = PA6_PRECISE
    out['label'] = ('Calculation / Inference (as pa6_corners; the 0.1 % parts\' 25 ppm/K drift case Inference); options '
                    'for the owner; option (b) adopted (round 9 lane B, O-R12-17)')
    return out


C87_LOW, C87_HIGH = .72, 1.10 * 1.15                               # R10 D-R19-10 / r11_stageD.en_model (R12F7-TRI-17)


def en_figures(four, j1_v=None):
    """R10's EN model (r12_budget.en_model: R80 / R165 470k, R81 300k, C87 220 nF x 0.72, U9 0.1 uA, D402 50 nA;
    values unchanged on R12, D-R12-09) in each of R12's resistor cases (R12F8-TRI-06: 'initial' 1 %, 'drift' 1 % +
    100 ppm/K over 67 K, the bound; 'bound' takes the worse of the two), at R12's four-stall BAT_IN; the lowest pack
    voltage at which the J400 7 ms
    bench line holds; the single-drop-out 10 ms pack floor; the turn-on window (EN rising 1.183-1.223 V, TI SLVSFC9C
    section 6.5) over a 6.0-8.4 V unloaded pack, C87 220 nF x 0.72 ... 220 nF x 1.265 (R12F7-TRI-17: R10 D-R19-10's
    range; 0.72 = -10 % tolerance, X7R -15 % over temperature and <= 6 % bias loss, 1.265 = +10 % x +15 %; the bias and
    temperature allowances are Inference). Before round 7 the range was 0.648-1.10 x, which counted -10 % twice at the
    fast end and left out the +15 % temperature end. R12F12-TRI-30: `four` is R80.1's voltage at the four-stall point
    (U9's EN divider top, fed from the BAT_IN network about 19 mV below J1), j1_v J1's."""
    def bisect(f, lo, hi):
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if f(mid) else (mid, hi)
        return hi

    def turn_on(v, c, r_hi, tol):
        r_top, r81 = 2 * 470e3 * ((1 + tol) if r_hi else (1 - tol)), 300e3 * ((1 - tol) if r_hi else (1 + tol))
        r_th = r_top * r81 / (r_top + r81)
        vc = v * r81 / (r_top + r81) - (.1e-6 if r_hi else -.1e-6) * r_th - (50e-9 if r_hi else 0) * r_th
        vth = 1.223 if r_hi else 1.183
        return r_th * c * math.log(vc / (vc - vth)) * 1e3
    nominal = {f'{v:g}V': 2 * 470e3 * 300e3 / (2 * 470e3 + 300e3) * 220e-9 * 1e3 *
               math.log((v * 300 / 1240) / (v * 300 / 1240 - 1.2)) for v in (6.0, 7.4, 8.4)}
    cases = {}
    for case, tol in TOL.items():
        m = lambda v: en_model(v, tol)                              # noqa: E731
        at_four = m(four)
        cases[case] = dict(
            resistor_tolerance=tol,
            by_pack={f'{v:.4g}V': m(v) for v in (8.4, 7.4, 6.0, four, 5.73, 5.71, 5.65, 5.5)},
            four_stall_single_dropout_ms=at_four['single_dropout_trip_ms'],
            four_stall_periodic_limit_ms=at_four['periodic_100ms_trip_open_ms'],
            margin_over_7ms_line_ms=at_four['periodic_100ms_trip_open_ms'] - 7.0,
            seven_ms_line_holds_down_to_V=bisect(lambda v: m(v)['periodic_100ms_trip_open_ms'] >= 7.0, 5.0, 7.0),
            single_10ms_dropout_needs_pack_V=bisect(lambda v: m(v)['single_dropout_trip_ms'] >= 10.0, 5.0, 7.0),
            turn_on=dict(nominal_ms=nominal, fastest_ms=turn_on(8.4, 220e-9 * C87_LOW, False, tol),
                         slowest_ms=turn_on(6.0, 220e-9 * C87_HIGH, True, tol), c87_factor=[C87_LOW, C87_HIGH],
                         label=('Calculation / Inference (C87 0.72-1.265 x, R10 D-R19-10: X7R tolerance, temperature '
                                f'and bias allowances; resistors +/-{tol * 100:.2f} %, SLVSFC9C EN thresholds and '
                                'leakages at their datasheet bounds)')))
    i, d = cases['initial'], cases['drift']
    bound = dict(
        four_stall_single_dropout_ms=min(i['four_stall_single_dropout_ms'], d['four_stall_single_dropout_ms']),
        four_stall_periodic_limit_ms=min(i['four_stall_periodic_limit_ms'], d['four_stall_periodic_limit_ms']),
        margin_over_7ms_line_ms=min(i['margin_over_7ms_line_ms'], d['margin_over_7ms_line_ms']),
        seven_ms_line_holds_down_to_V=max(i['seven_ms_line_holds_down_to_V'], d['seven_ms_line_holds_down_to_V']),
        single_10ms_dropout_needs_pack_V=max(i['single_10ms_dropout_needs_pack_V'], d['single_10ms_dropout_needs_pack_V']),
        single_dropout_at_6V0_ms=min(i['by_pack']['6V']['single_dropout_trip_ms'], d['by_pack']['6V']['single_dropout_trip_ms']),
        turn_on_ms=[min(i['turn_on']['fastest_ms'], d['turn_on']['fastest_ms']),
                    max(i['turn_on']['slowest_ms'], d['turn_on']['slowest_ms'])],
        seven_ms_line_holds_at_four_stall=min(i['four_stall_periodic_limit_ms'], d['four_stall_periodic_limit_ms']) > 7.0,
        note='the worse of the 1 % and drift cases (the drift case in every figure): R12\'s bound convention '
             '(r12_budget.TOL, R12F8-TRI-06)')
    return dict(by_case=cases, bound=bound, four_stall_R80_V=four,
                four_stall_BAT_IN_V=four if j1_v is None else j1_v,
                voltage_basis=('every voltage the EN model takes (by_pack, seven_ms_line_holds_down_to_V, '
                               'single_10ms_dropout_needs_pack_V, the turn-on pack range) is R80.1\'s, the EN divider '
                               'top (R12F12-TRI-30); with no load current it equals J1\'s'),
                label='Calculation / Inference (C87 X7R bias allowance, leakages at their datasheet bounds; the resistor '
                      'drift case Inference)')


# R12F12-TRI-23 / -30: the J400 chatter bench rule is a number derived from the model, not a fixed line: the largest
# 0.1 ms step at least 0.10 ms below the worst-corner periodic limit over both load conventions (GAP-1's and the
# whole-current sensitivity), each with EN fed from R80.1 on the BAT_IN network
BENCH_STEP_MS, BENCH_MARGIN_MS = 0.1, 0.10


def bench_rule_ms(worst_ms):
    """The largest multiple of BENCH_STEP_MS that is at most worst_ms - BENCH_MARGIN_MS."""
    return round(math.floor(round((worst_ms - BENCH_MARGIN_MS) / BENCH_STEP_MS, 9)) * BENCH_STEP_MS, 10)


def chatter_rule(en_main, en_sens):
    """The bench rule from the two conventions' drift-bound limits (Calculation / Inference as en_figures)."""
    limits = dict(gap1_constant_power=en_main['bound']['four_stall_periodic_limit_ms'],
                  whole_current_sensitivity=en_sens['bound']['four_stall_periodic_limit_ms'])
    worst = min(limits.values())
    rule = bench_rule_ms(worst)
    return dict(limits_ms=limits, worst_limit_ms=worst, worst_convention=min(limits, key=limits.get),
                R80_V=dict(gap1_constant_power=en_main['four_stall_R80_V'],
                           whole_current_sensitivity=en_sens['four_stall_R80_V']),
                bench_rule_ms=rule, margin_ms=worst - rule, step_ms=BENCH_STEP_MS, min_margin_ms=BENCH_MARGIN_MS,
                bench_rule=(f'J400 chatter, R12 pass rule: total open time < {rule:.1f} ms in every sliding 100 ms '
                            'window, U9 on for the whole run (R12F12-TRI-30: the largest 0.1 ms step at least 0.10 ms '
                            f'below the worst-corner limit {worst:.3f} ms, the lower of the two load conventions with '
                            'EN fed from R80.1)'),
                label='Calculation / Inference (as en_figures; the load allocations and both pack-load conventions)')


def record_issues(d):
    """R12F12-TRI-23 / -24: what makes a stage D record fail, on the record itself (main refuses to write one; the
    stage D self-test runs it on the committed file and on seeded copies)."""
    issues = []
    try:
        ch = d['en']['chatter_rule']
        sens = d['fire']['pack_load_sensitivity']['en_at_that_BAT_IN']['four_stall_periodic_limit_ms']
        worst = min(d['en']['bound']['four_stall_periodic_limit_ms'], sens)
        rule = ch['bench_rule_ms']
        if not isinstance(rule, (int, float)) or isinstance(rule, bool) or not math.isfinite(rule):
            issues.append('chatter bench rule is not a number')
        else:
            if rule > worst - BENCH_MARGIN_MS + 1e-9:
                issues.append(f'chatter bench rule {rule} ms is not {BENCH_MARGIN_MS} ms below the worst limit '
                              f'{worst:.4f} ms over both load conventions')
            if abs(rule - bench_rule_ms(worst)) > 1e-9:
                issues.append(f'chatter bench rule {rule} ms is not the largest 0.1 ms step below {worst:.4f} ms')
        if abs(ch['worst_limit_ms'] - worst) > 1e-9:
            issues.append('chatter worst limit does not match the two conventions')
    except (KeyError, TypeError) as exc:
        issues.append(f'chatter bench rule missing: {exc}')
    for name, r in d.get('rails', {}).items():
        if r.get('joined') is not True:
            issues.append(f'rail path {name} is not joined')
    for block in ('vbus_sense', 'q122_gate'):
        if d.get(block, {}).get('topology_ok') is not True:
            issues.append(f'{block}: the parts are not on the nets the block models')
    return issues


def dc(board_path, net, src, snk, margin=4.0, full_width=True):
    """tools/r11_dc_net.solve on R12's four copper layers. Window: the terminals' box plus `margin` along y and, for a
    track-routed net, the full board width (a feed may detour sideways); for the plane nets (GND, 3V3) the box plus
    `margin` both ways; for FULL_BOARD_NETS the whole board. Copper outside the window is dropped, so R is an upper
    bound (Calculation)."""
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
    if net in FULL_BOARD_NETS:
        window = (x0, y0, x1, y1)
    window = tuple(round(v, 1) for v in window)
    r = r11_dc_net.solve(board_path, net, src, snk, grid=0.1, window=window)
    r.pop('board_sha256', None)
    if not math.isfinite(r['resistance_ohm']) or r['resistance_ohm'] > 1.0:
        raise ValueError(f'{net} {src} -> {snk}: not joined inside the window {window}')
    return r


def spec(board, ref, net):
    return f'{ref}:' + ','.join(pads_on(board, ref, net))


# TI TPS563208 SOT-23-6 (DDC) pinout: 1 GND, 2 SW, 3 VIN, 4 VFB, 5 EN, 6 VBST. On R12 U400's EN is tied to VIN (both
# RAW_PROTECTED): the 0.25 mm F.Cu stub U400.5 -> U400.3 carries only EN's input current (uA), so the load-current paths
# start at VIN alone (R12F2-TRI-06; U403's EN is CAM_EN, another net, driven from PC12 through R436 since R12F8).
BUCK_VIN = ('3',)
# R12F2-TRI-07: RAW_PROTECTED's load branches end where their copper joins the In2 RAW_PROTECTED island (a via whose In2
# pad touches that fill): the current enters there. Ending at every via instead (check_r10.path_graph's end=None) made
# each branch take the whole B.Cu trunk, including copper that carries only the other branch's current.
PLANE_END = {'RAW_PROTECTED': 'In2.Cu'}


def power_paths(board):
    """R12's rail paths by function (R10 K-power basis): (name, net, start pads, end pads or None = the path's vias
    (on a PLANE_END net: the vias joined to that net's inner fill), design current A, basis). rail_paths adds the
    RAW_PROTECTED loads' budget currents (raw_budget_currents)."""
    p = lambda ref, net: {ref: pads_on(board, ref, net)}         # noqa: E731
    port_v = r12_budget.rails()['PORT_4V8 (U400 TPS563208, R400 47k + R404 5.1k / R401 10k 0.1 %)']['initial']['max_V']
    port_in = 1.9 * port_v / (.80 * FOUR_STALL_VIN)
    cam_in = 1.249 * 5.691 / (.80 * FOUR_STALL_VIN)
    for ref in ('U400', 'U403'):
        if not set(BUCK_VIN) <= set(pads_on(board, ref, 'RAW_PROTECTED')):
            raise ValueError(f'{ref} VIN (pin 3) is not on RAW_PROTECTED')
    rows = [
        ('U9 IN', 'BAT_IN', p('J1', 'BAT_IN'), p('U9', 'BAT_IN'), 2.9, 'R10 U9 IN'),
        ('U9 OUT', 'RAW_PROTECTED', p('U9', 'RAW_PROTECTED'), None, 2.9, 'R10 U9 OUT'),
        ('U400 IN', 'RAW_PROTECTED', {'U400': BUCK_VIN}, None, port_in,
         f'port 1.9 A at {port_v:.3f} V / 0.80 from 5.71 V (Inference); VIN pin 3 only, the EN stub excluded '
         '(R12F2-TRI-06)'),
        ('U403 IN', 'RAW_PROTECTED', {'U403': BUCK_VIN}, None, cam_in,
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


def track_graph(board, net, layers=None):
    """check_r10.track_graph with one addition (R12F12-TRI-24): a track that crosses a pad of its net on its layer
    without ending in it (C84.1's VLOGIC run) is cut at the pad, so the pad is a node of the walk. check_r10's own
    walk is unchanged (R10's gate)."""
    import pcbnew
    import check_r10
    pads, vias, edges = check_r10.track_graph(board, net, layers)
    crossing = []
    for key, (a, b, t) in list(edges.items()):
        s, e = t.GetStart(), t.GetEnd()
        length = (e - s).EuclideanNorm()
        if length == 0:
            continue
        for lab, _, _, p in pads:
            if not p.IsOnLayer(t.GetLayer()) or ('P' + lab) in (a, b):
                continue
            c = p.GetPosition()
            k = ((c.x - s.x) * (e.x - s.x) + (c.y - s.y) * (e.y - s.y)) / length ** 2
            q = pcbnew.VECTOR2I(int(round(s.x + k * (e.x - s.x))), int(round(s.y + k * (e.y - s.y))))
            if 0 < k < 1 and p.HitTest(q):
                crossing.append((key, a, b, t, k, 'P' + lab))
    for key, a, b, t, k, node in crossing:
        if key not in edges:
            continue
        del edges[key]
        # the piece's own ends: split it at the pad; pieces that fall inside the pad are not edges
        s, e = t.GetStart(), t.GetEnd()
        if a != node:
            edges[f'{key}/a'] = (a, node, t)
        if b != node:
            edges[f'{key}/b'] = (node, b, t)
    return pads, vias, edges


def path_graph(board, net, start, end=None, layers=None):
    """check_r10.path_graph on track_graph above (R12F12-TRI-24)."""
    import check_r10
    pads, vias, edges = track_graph(board, net, layers)
    first = {'P' + lab for lab, ref, num, _ in pads if num in start.get(ref, ())}
    last = ({'V' + v.m_Uuid.AsString() for v in vias} if end is None else
            {'P' + lab for lab, ref, num, _ in pads if num in end.get(ref, ())})
    kept, joined = check_r10.simple_path_edges(edges, first, last)
    on = {x for a, b, _ in kept.values() for x in (a, b) if isinstance(x, str)}
    tracks = {e[2].m_Uuid.AsString(): e[2] for e in kept.values()}
    return (list(tracks.values()), joined, [v for v in vias if 'V' + v.m_Uuid.AsString() in on],
            sorted(n[1:] for n in on if n.startswith('P')))


def plane_path_graph(board, net, start, layer):
    """check_r10.path_graph with the path's end at the vias of `net` whose `layer` pad touches the net's fill on that
    layer (check_r10.plane_via): the copper on simple paths from the start pads to the inner island. Returns
    (segments, joined, vias on the path, pad labels on the path)."""
    import check_r10
    pads, vias, edges = track_graph(board, net)
    first = {'P' + lab for lab, ref, num, _ in pads if num in start.get(ref, ())}
    lid = board.GetLayerID(layer)
    last = {'V' + v.m_Uuid.AsString() for v in vias if check_r10.plane_via(board, v, lid, net)}
    kept, joined = check_r10.simple_path_edges(edges, first, last)
    on = {x for a, b, _ in kept.values() for x in (a, b) if isinstance(x, str)}
    tracks = {e[2].m_Uuid.AsString(): e[2] for e in kept.values()}
    return (list(tracks.values()), joined, [v for v in vias if 'V' + v.m_Uuid.AsString() in on],
            sorted(n[1:] for n in on if n.startswith('P')))


def raw_budget_currents(fire):
    """RAW_PROTECTED branch currents at the board's own budget during the fire: raw_point's self-consistent solve at the
    four-stall BAT_IN (R12F10-TRI-09; it was each branch's allocated power / BAT_IN): U400 and U403 their input power at
    their own nodes, D5 U2's input current (Calculation / Inference: the allocations, the 80 % efficiency and D5's drop
    are Inference)."""
    c = fire['converter_point_four_stall']['currents_A']
    return {'U400 IN': c['U400'], 'U403 IN': c['U403'], 'D5 IN': c['D5']}


# the net's source path current: on RAW_PROTECTED every load current comes through U9's path (R10's 2.9 A)
SOURCE_A = {'RAW_PROTECTED': 2.9}


def shared_copper(found, raw_budget):
    """R12F2-TRI-07: a track on more than one load path of a net carries the sum of their currents. For each group of
    such tracks (same paths, layer and width): length, the summed design current and its IPC-2152 rise, the same capped
    at the net's source current (SOURCE_A: the summed design inputs exceed U9's own 2.9 A path rating), and the summed
    budget current and its rise. U9 OUT (the source path) shares no track with the load paths: they meet only through
    the In2 island. IPC rise: long-conductor fit, no plane credit, an upper bound (Calculation on CAD widths /
    Inference)."""
    import pcbnew
    mm = pcbnew.ToMM
    owners = {}
    for name, (net, amps, segs, board, stack) in found.items():
        for t in segs:
            owners.setdefault(t.m_Uuid.AsString(), (t, net, board, stack, []))[4].append(name)
    groups = {}
    for t, net, board, stack, names in owners.values():
        if len(names) < 2:
            continue
        lay = board.GetLayerName(t.GetLayer())
        w = round(mm(t.GetWidth()), 4)
        key = (net, tuple(sorted(names)), lay, w)
        g = groups.setdefault(key, dict(net=net, paths=list(key[1]), layer=lay, width_mm=w, th_mm=stack[lay][0],
                                        length_mm=0.0, R_series_ohm=0.0, tracks=[]))
        g['length_mm'] += mm(t.GetLength())
        g['R_series_ohm'] += seg_r(mm(t.GetLength()), w, stack[lay][0])
        g['tracks'].append([[round(mm(t.GetStart().x), 3), round(mm(t.GetStart().y), 3)],
                            [round(mm(t.GetEnd().x), 3), round(mm(t.GetEnd().y), 3)]])
    out = []
    for key in sorted(groups):
        g = groups[key]
        g['tracks'].sort()
        design = sum(found[n][1] for n in g['paths'])
        g['design_A_sum'] = design
        g['ipc_rise_design_sum_C'] = ipc2152.ipc_dt(g['width_mm'], g['layer'], design, th_mm=g['th_mm'])
        g['ipc_width_for_30C_at_design_sum_mm'] = ipc2152.ipc_width(30.0, g['layer'], design, th_mm=g['th_mm'])
        cap = SOURCE_A.get(g['net'])
        if cap is not None and design > cap:
            g['design_A_capped_at_source'] = cap
            g['ipc_rise_capped_C'] = ipc2152.ipc_dt(g['width_mm'], g['layer'], cap, th_mm=g['th_mm'])
        if all(n in raw_budget for n in g['paths']):
            g['budget_A_sum'] = sum(raw_budget[n] for n in g['paths'])
            g['ipc_rise_budget_C'] = ipc2152.ipc_dt(g['width_mm'], g['layer'], g['budget_A_sum'], th_mm=g['th_mm'])
        g['label'] = ('Calculation on CAD widths; the rise is the IPC-2152 long-conductor fit with no plane credit, an '
                      'upper bound (Inference); design currents R10 K-power basis, budget currents Inference')
        out.append(g)
    return out


def rail_paths(board, stack, fire=None):
    import pcbnew
    import check_r10
    mm = pcbnew.ToMM
    out, found = {}, {}
    raw_budget = raw_budget_currents(fire) if fire else {}
    for name, net, start, end, amps, basis in power_paths(board):
        if end is None and net in PLANE_END:
            segs, joined, vias, on = plane_path_graph(board, net, start, PLANE_END[net])
        else:
            segs, joined, vias, on = path_graph(board, net, start, end)
        found[name] = (net, amps, segs, board, stack)
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
                         end=(f'vias joined to the {PLANE_END[net]} fill' if end is None and net in PLANE_END
                              else 'the path vias' if end is None else 'named pads'),
                         vias=[[round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3),
                                round(mm(v.GetDrillValue()), 3)] for v in vias],
                         R_tracks_series_ohm=sum(q['R_series_ohm'] for q in per.values()),
                         over_30C=over, over_30C_all_short_entries=all(o['length_mm'] <= 2.0 for o in over))
        if name in raw_budget:
            out[name]['budget_A'] = raw_budget[name]
    shared = shared_copper(found, raw_budget)
    for g in shared:
        for name in g['paths']:
            r = out[name]
            r.setdefault('shared_tracks', []).append(
                dict(layer=g['layer'], width_mm=g['width_mm'], length_mm=g['length_mm'], with_paths=g['paths'],
                     design_A_sum=g['design_A_sum'], rise_design_sum_C=g['ipc_rise_design_sum_C']))
            if g['ipc_rise_design_sum_C'] > 30.0:
                r['over_30C'].append(dict(layer=g['layer'], width_mm=g['width_mm'], length_mm=g['length_mm'],
                                          rise_C=g['ipc_rise_design_sum_C'], amps=g['design_A_sum'],
                                          shared_with=g['paths']))
                r['over_30C_all_short_entries'] = all(o['length_mm'] <= 2.0 for o in r['over_30C'])
    return out, shared


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
        hot = drop * HOT_CU                                        # R12F12-TRI-31: the drift case at 70 C copper
        out[label] = dict(I_A=amps, drop_V=drop, drop_drift_V=hot,
                          min_VCC_initial_V=rails['initial']['min_V'] - drop, margin_initial_V=rails['initial']['min_V'] - drop - 3.135,
                          min_VCC_drift_V=rails['drift']['min_V'] - hot, margin_drift_V=rails['drift']['min_V'] - hot - 3.135)
    out['copper_factor_drift'] = HOT_CU
    out['window_basis'] = rails['source']
    out['label'] = ('Calculation / Inference (3V3 window, D-R12-139): Calculation on CAD copper (DC solves, 20 C; the '
                    'drift rows at 70 C, R12F12-TRI-31) and '
                    'the r12_windows 3V3 window (SLUSDW3A section 7.8 PFM band, R12F6-TRI-03); the band at R12\'s VIN, '
                    'the drift case and load currents Inference')
    return out


def port_supply(solves, fire=None):
    """PORT_4V8 at each port's pin 2. U400 regulates at R400.1 (its feedback divider top), whose 0.15 mm F.Cu sense run
    ends at C406's corner of the 1.0 mm feed (R12F12-TRI-40: items named, not coordinates). The feed runs from C406.1 to
    L400.2; a 0.8 mm trunk off the feed drops through two vias into the forward In2 PORT_4V8 island under the port row
    (C407's via joins it too), and each port's pin 2 rises through its own via. Every node potential
    of a resistive network lies between the source's and the sinks' (maximum principle), and a mutual resistance from
    L400.2 is at most either driving-point resistance, so with the three ports drawing I in all the drop from the
    regulation point to port k is at most R(L400.2 -> port k) x I (Calculation on CAD copper at 20 C; an upper bound:
    the feed from L400.2 to the sense tap is counted). I: the always-on budget 0.561 A (GPS 0.15 + radio
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
            hot = drop * HOT_CU                                    # R12F12-TRI-31: the drift case at 70 C copper
            row[label] = dict(I_A=amps, drop_bound_V=drop, drop_bound_drift_V=hot,
                              min_initial_V=rails['initial']['min_V'] - drop,
                              min_drift_V=rails['drift']['min_V'] - hot,
                              margin_initial_V=rails['initial']['min_V'] - drop - 4.5,
                              margin_drift_V=rails['drift']['min_V'] - hot - 4.5)
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
    out['window_holds_for'] = ('U400 VIN >= VO / 0.75 (TI SLVSD90B 7.3; R12F5-TRI-02): every window figure above '
                               'assumes U400 regulates; u400_input gives its input and headroom at the four-stall point '
                               'and on a 6.0 V pack')
    if fire is not None:
        out['u400_input'] = u400_input(fire, solves)
    out['copper_factor_drift'] = HOT_CU
    out['label'] = ('Calculation on CAD copper (20 C; the drift rows at 70 C, R12F12-TRI-31) and the r12_windows PORT_4V8 '
                    'window (upper bound on the drop); the 4.5 V '
                    'module floor, the LR900-F 5.0 V top and the load allocation are Inference; harness drop not '
                    'included; valid while U400 VIN >= VO / 0.75')
    return out


def u400_input(fire, solves):
    """R12F5-TRI-02: U400's input (VIN, pin 3) against the TPS563208's VO / 0.75 condition, and its duty headroom
    (r12_budget.buck_headroom: tOFF(MIN) at 580 kHz and at the about 200 kHz foldback floor below VIN 7 V). U400 VIN =
    BAT_IN less U9's RON (SLVSFC9C's 0.045 ohm maximum, R12F8-TRI-07) and the J1 -> U9.5 copper at the whole converter
    current, less the
    RAW_PROTECTED drop at U400.3, each branch charged at min(its own, U400's) resistance from U9.6 (the mutual-resistance
    bound of pa6_corners; an upper bound on the drop). Points: the four-stall fire point (healthy match) and a 6.0 V
    open-circuit pack under the converter load alone (R10 pack model 0.15 ohm; no fire, no stall). Ports at the 0.561 A
    budget (Inference). R12F10-TRI-09: the currents are raw_point's self-consistent solve (U400 / U403 at their own
    nodes, D5 = U2's input current), and the 6.0 V point's BAT_IN is solved with that current. Calculation / Inference."""
    port = r12_budget.rails()[r12_budget.PORT_RAIL]
    parts = fire['other_load_parts']
    hot = lambda key: solves[key]['resistance_ohm'] * HOT_CU                # noqa: E731  (70 C copper, R12F9-TRI-04)
    z = fire['bat_in_network_70C_ohm']                                     # R12F12-TRI-30 (already at 70 C)
    r_u9, z_fire = z['U9']['U9'], z['U9']['Q120']
    r_u400 = hot('RAW_PROTECTED_U9_to_U400')
    raw = {k: hot(f'RAW_PROTECTED_U9_to_{k}') for k in RAW_SINKS}
    r_u2 = hot('VLOGIC_D5_to_U2')
    conv = lambda v, i_f=0.0: raw_point(v, parts, r_u9, raw, r_u2, i_fire=i_f, z_fire_ohm=z_fire)  # noqa: E731
    shares = {'U400 (ports)': r_u400, 'U403 (camera)': min(raw['U403'], r_u400),
              'D5 (logic, microSD) and R92': min(raw['D5'], r_u400)}
    pack6 = loaded(math.inf, lambda v, i_f: conv(v)['I_total_A'], 0, open_v=6.0)['BAT_IN_V']
    out = dict(min_recommended_VIN_V={c: [port[c]['min_V'] / .75, port[c]['max_V'] / .75] for c in r12_budget.TOL},
               branch_shared_ohm=shares, J1_to_U9_ohm=r_u9, fire_coupling_at_U9_ohm=z_fire, u9_ron_ohm=U9_RON,
               copper_factor_70C=HOT_CU)
    for name, bat, i_f in (('four_stall_fire', fire['four_stall_BAT_IN_V'], fire['four_stall_A']),
                           ('6V0_pack_converters_only', pack6, 0.0)):
        pt = conv(bat, i_f)
        i = pt['I_total_A']
        drop = bat - pt['node_V']['U400']
        vin = bat - drop
        out[name] = dict(BAT_IN_V=bat, fire_A=i_f, converter_A=i, branch_A=pt['currents_A'], drop_to_U400_VIN_V=drop,
                         below_VO_over_0V75=vin < min(port[c]['min_V'] for c in r12_budget.TOL) / .75,
                         **r12_budget.buck_headroom(vin, port, r12_budget.PORT_BUDGET_A))
    out['label'] = ('Calculation / Inference (DC-solve upper bounds on the drop, copper at 70 C (R12F9-TRI-04); U9 RON '
                    'at the SLVSFC9C maximum; the pack model, converter allocations, the 70 C copper temperature, the '
                    'foldback frequency, DCR and hot RDS(on) Inference): an estimate, not a guaranteed window')
    return out


# R10's camera harness and transient allowances (stageD_analysis section 6 "R10's allowances"; Inference)
CAM_HARNESS_OHM, CAM_TRANSIENT_V, CAM_I_A = 0.15, 0.05, 1.0


def u403_input(fire, solves):
    """R12F8-TRI-09: U403 (camera buck) input at the four-stall fire point (healthy match) on the current copper, as
    u400_input does for U400: BAT_IN less U9's RON (0.045 ohm maximum) and the J1 -> U9.5 copper at the whole converter
    current, less the RAW_PROTECTED drop at U403.3 with each branch charged at min(its own, U403's) resistance from U9.6
    (the mutual-resistance bound; an upper bound on the drop). Then r12_budget.buck_headroom at the camera's 1 A, and the
    optimistic camera-pin estimate of stageD_analysis section 6: the held output less 1 A x the L401 -> J9 copper, R10's
    0.15 ohm harness and 0.05 V transient allowance (Calculation / Inference: low-side, inductor and contact losses, the
    foldback frequency and typical RDS(on)h are not modelled; not a guaranteed window or proof of camera failure)."""
    cam = r12_budget.rails()['CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)']
    parts = fire['other_load_parts']
    hot = lambda key: solves[key]['resistance_ohm'] * HOT_CU                # noqa: E731  (70 C copper, R12F9-TRI-04)
    z = fire['bat_in_network_70C_ohm']                                     # R12F12-TRI-30 (already at 70 C)
    r_u9, z_fire = z['U9']['U9'], z['U9']['Q120']
    r_u403 = hot('RAW_PROTECTED_U9_to_U403')
    raw = {k: hot(f'RAW_PROTECTED_U9_to_{k}') for k in RAW_SINKS}
    shares = {'U403 (camera)': r_u403, 'U400 (ports)': min(raw['U400'], r_u403),
              'D5 (logic, microSD) and R92': min(raw['D5'], r_u403)}
    bat = fire['four_stall_BAT_IN_V']
    # R12F10-TRI-09: raw_point's self-consistent currents (U400 / U403 at their own nodes, D5 = U2's input current)
    pt = raw_point(bat, parts, r_u9, raw, hot('VLOGIC_D5_to_U2'), i_fire=fire['four_stall_A'], z_fire_ohm=z_fire)
    i = pt['I_total_A']
    drop = bat - pt['node_V']['U403']
    vin = bat - drop
    head = r12_budget.buck_headroom(vin, cam, CAM_I_A)
    r_cam = hot('CAM_5V_L401_to_J9')
    pins = {k: v - CAM_I_A * (r_cam + CAM_HARNESS_OHM) - CAM_TRANSIENT_V for k, v in head['max_held_V'].items()
            if k.startswith('200kHz')}
    return dict(BAT_IN_V=bat, fire_A=fire['four_stall_A'], converter_A=i, branch_A=pt['currents_A'],
                drop_to_U403_VIN_V=drop, VIN_V=vin, u9_ron_ohm=U9_RON, J1_to_U9_ohm=r_u9,
                fire_coupling_at_U9_ohm=z_fire, branch_shared_ohm=shares,
                min_recommended_VIN_V={c: [cam[c]['min_V'] / .75, cam[c]['max_V'] / .75] for c in TOL},
                below_VO_over_0V75=vin < min(cam[c]['min_V'] for c in TOL) / .75, headroom=head,
                camera_pin_estimate_V=pins, camera_pin_basis=dict(L401_to_J9_ohm=r_cam, harness_ohm=CAM_HARNESS_OHM,
                                                                  transient_V=CAM_TRANSIENT_V, I_A=CAM_I_A),
                copper_factor_70C=HOT_CU,
                label=('Calculation / Inference (DC-solve upper bounds on the drop, copper at 70 C (R12F9-TRI-04); U9 RON '
                       'at the SLVSFC9C maximum; the 70 C copper temperature, the pack model, converter allocations, the foldback frequency, typical RDS(on)h, harness and '
                       'transient allowances Inference): an optimistic estimate, not a guaranteed window'))


def u400_feed_drop(rails, shared):
    """R12F8-TRI-09: the drop along U400 IN's series copper (In2 landing -> VIN), at its own current, plus the other
    paths' current on the tracks it shares (rails_shared): at the design inputs and at the budget (Calculation on CAD
    copper at 20 C; the currents Inference)."""
    r = rails['U400 IN']
    out = {}
    for key, cur in (('design', lambda n: rails[n]['amps']), ('budget', lambda n: rails[n].get('budget_A'))):
        extra = [(g['R_series_ohm'], sum(cur(n) for n in g['paths'] if n != 'U400 IN')) for g in shared
                 if 'U400 IN' in g['paths']]
        own = cur('U400 IN')
        out[f'{key}_V'] = own * r['R_tracks_series_ohm'] + sum(rr * a for rr, a in extra)
        out[f'{key}_terms'] = dict(own_A=own, R_series_ohm=r['R_tracks_series_ohm'],
                                   shared=[dict(R_ohm=rr, other_A=a) for rr, a in extra])
    out['label'] = 'Calculation on CAD copper (20 C); design and budget currents Inference'
    return out


def bat_in_network(board_path, board):
    """R12F12-TRI-30: BAT_IN as one copper network, J1.1 the reference, ports U9.5 (converters), Q120.3 (fire) and R80.1
    (U9's EN divider top): r11_dc_net.solve_ports on the whole board (Calculation on CAD copper, 20 C)."""
    import r11_hotplug
    import r11_dc_net
    r11_hotplug.CU_NAMES = CU_NAMES
    r11_dc_net.CU_NAMES = CU_NAMES
    ports = {p: spec(board, p, 'BAT_IN') for p in BAT_PORTS}
    out = r11_dc_net.solve_ports(board_path, 'BAT_IN', spec(board, 'J1', 'BAT_IN'), ports)
    if out['reciprocity_max_rel_asymmetry'] > 1e-6:
        raise ValueError(f"BAT_IN network not reciprocal: {out['reciprocity_max_rel_asymmetry']}")
    out['label'] = ('Calculation on CAD copper (20 C; the four-stall points take it at 70 C): Z[a][b] is the drop from '
                    'J1.1 at port a per ampere drawn at port b, every terminal pad equipotential')
    return out


# R12F12-TRI-11: U2 (LMR50410XDBVR) output capability with L1 = 4.7 uH, and the 3V3 load budget
U2_ISC_MIN, U2_FSW = 1.25, (600e3, 700e3, 800e3)                   # SLUSDW3A 7.5: ISC 1.25 / 1.6 / 1.9 A; FOSC
U2_L, U2_L_TOL, U2_VIN_FRESH = 4.7e-6, 0.20, 8.15
# DS12110 Rev 8, IDD in Run mode, all peripherals enabled, VOS3 at 200 MHz (rev Y Tables 30-32 / rev V Tables 129-131)
# and the 480 MHz VOS0 rows (rev V Tables 129 / 130); maximum columns by junction temperature (mA). Guaranteed by
# characterization (table notes), CoreMark, I/Os in analog mode, AHB = CPU / 2, APB = AHB / 2.
MCU_IDD_MAX_MA = {
    '200MHz_VOS3': {'rev_Y_T30_ITCM': {25: 110, 85: 220, 105: 300}, 'rev_Y_T31_flash_cache_on': {25: 110, 85: 220, 105: 300},
                    'rev_Y_T32_flash_cache_off': {25: 100, 85: 210, 105: 300},
                    'rev_V_T129_ITCM': {25: 116, 85: 174, 105: 233}, 'rev_V_T130_flash_cache_on': {25: 114, 85: 173, 105: 232},
                    'rev_V_T131_flash_cache_off': {25: 103, 85: 167, 105: 226}},
    '480MHz_VOS0': {'rev_V_T129_ITCM': {25: 348, 85: 439, 105: 550}, 'rev_V_T130_flash_cache_on': {25: 342, 85: 436, 105: 546},
                    'rev_V_T131_flash_cache_off': {25: 276, 85: 390, 105: 504}}}
MCU_TJ_BUDGET = 85
# the other 3V3 loads (A): microSD write (REQUIREMENTS F5), U3 QSPI flash program / erase, U4 + U5 + U6, the LEDs, the
# pull-ups, the buzzer (QMB-09B-03 16 +/- 5 ohm coil, D-R12-16 / Huawha 2019-12-3: 3V3 maximum / 11 ohm in its on-phase,
# half of it on average with the <= 50 % square wave of firmware rule (a); TRI-13)
BUDGET_3V3_A = dict(microsd_write=0.200, U3_qspi_flash=0.025, U4_U5_U6_sensors=0.008, LEDs=0.012, pull_ups=0.004)
BUZZER_COIL_MIN_OHM = 11.0


def u2_limit(vin=U2_VIN_FRESH, l=U2_L * (1 - U2_L_TOL), fsw=U2_FSW[1], vout=3.35, isc=U2_ISC_MIN):
    """IOUT max = ISC - dI / 2 with dI = VOUT (VIN - VOUT) / (VIN L fSW) when dI exceeds ISC - ILS (SLUSDW3A 8.3.5:
    eq. 6 needs the valley limit to engage; with 4.7 uH it does not at 8.15 V)."""
    di = vout * (vin - vout) / (vin * l * fsw)
    return dict(VIN_V=vin, L_H=l, fsw_Hz=fsw, VOUT_V=vout, ISC_min_A=isc, ripple_A=di, IOUT_max_A=isc - di / 2)


def u3v3_budget():
    """R12F12-TRI-11: the 3V3 load budget against U2's limit with L1 4.7 uH (TI SLUSDW3A 7.5 ISC minimum 1.25 A, FOSC
    600 / 700 / 800 kHz; the 4.7 uH part at -20 %; VIN 8.15 V = an 8.4 V pack less D5 at 0.25 V, the largest ripple).
    MCU: DS12110 Rev 8's run-mode maxima at the firmware's 200 MHz (VOS3, all peripherals enabled), the larger of
    silicon revisions Y and V, at Tj 85 C (a 70 C bay plus self-heating; the Tj is an Inference), and at 480 MHz (VOS0,
    revision V) for comparison; the 105 C column as a sensitivity. Average = buzzer at half its on-phase current; peak =
    every load at once with the buzzer in its on-phase (Calculation on the maker's tables / Inference: the allocations,
    Tj, the closed-loop current limit (SLUSDW3A note 3: open-loop production values) and I/O switching currents, which
    the maker's rows exclude)."""
    v33_max = r12_budget.rails()[r12_budget.V33_RAIL]['drift']['max_V']
    buzz_on = v33_max / BUZZER_COIL_MIN_OHM
    limits = {f'{int(f / 1e3)}kHz': u2_limit(fsw=f) for f in U2_FSW[:2]}
    limit_typ, limit_min = limits['700kHz']['IOUT_max_A'], limits['600kHz']['IOUT_max_A']
    other = sum(BUDGET_3V3_A.values())
    out = dict(u2_limit=limits, u2_limit_A=limit_typ, u2_limit_fsw_min_A=limit_min,
               u2_limit_basis=('ISC minimum 1.25 A less half the ripple at 8.15 V in, L 4.7 uH -20 %, fSW 700 kHz '
                               '(typical) and 600 kHz (FOSC minimum), VOUT 3.35 V (R14 47k / R15 20k)'),
               loads_A=dict(BUDGET_3V3_A), buzzer_on_phase_A=buzz_on, buzzer_average_A=buzz_on / 2,
               buzzer_basis=f'3V3 drift maximum {v33_max} V / 11 ohm (16 +/- 5 ohm coil), <= 50 % square wave',
               mcu_source='DS12110 Rev 8 Tables 30-32 (rev Y) and 129-131 (rev V): IDD max, Run mode, all peripherals '
                          'enabled, CoreMark, I/Os analog; guaranteed by characterization',
               mcu_idd_max_mA=MCU_IDD_MAX_MA, tj_budget_C=MCU_TJ_BUDGET, cases={})
    for clock, rows in MCU_IDD_MAX_MA.items():
        for tj in (85, 105):
            mcu = max(r[tj] for r in rows.values()) / 1e3
            avg, peak = mcu + other + buzz_on / 2, mcu + other + buzz_on
            out['cases'][f'{clock}_Tj{tj}'] = dict(
                MCU_A=mcu, MCU_row=max(rows, key=lambda k: rows[k][tj]), average_A=avg, peak_A=peak,
                margin_average_A=limit_typ - avg, margin_peak_A=limit_typ - peak,
                margin_peak_fsw_min_A=limit_min - peak, peak_without_buzzer_A=mcu + other,
                fits=peak <= limit_typ, fits_fsw_min=peak <= limit_min)
    c200, c480 = out['cases'][f'200MHz_VOS3_Tj{MCU_TJ_BUDGET}'], out['cases'][f'480MHz_VOS0_Tj{MCU_TJ_BUDGET}']
    out['fits_200MHz'] = c200['fits'] and c200['fits_fsw_min']
    out['fits_480MHz'] = c480['fits']
    out['verdict'] = (f"200 MHz: peak {c200['peak_A']:.3f} A against {limit_typ:.3f} A ({limit_min:.3f} A at FOSC "
                      f"minimum), average {c200['average_A']:.3f} A, at Tj {MCU_TJ_BUDGET} C; 480 MHz: peak "
                      f"{c480['peak_A']:.3f} A, {'fits' if c480['fits'] else 'does not fit'}")
    out['label'] = ('Calculation / Inference (maker maxima for U2 and the MCU; Tj, load allocations, closed-loop current '
                    'limit and I/O switching currents Inference)')
    return out


def vbus_sense(nets):
    """R12F12-TRI-06: PC9 (VBUS_SENSE, FT_fh, DS12110 Rev 8 Table 9) reads VBUS x R110 / (R9 + R110), R9 1k / R110
    1.5k (lane P), over VBUS 4.45-5.5 V and both resistor cases, with PC9's +/-250 nA input leakage through R9 || R110
    (Table 60). High needs V_IH = 0.7 x VDD (Table 60) at the 3V3 window's maximum; the absolute maximum on an FT pin is
    min(VDD, VDDA, VDD33USB, VBAT) + 4.0 V (Table 21), 4.0 V with VDD at 0 (USB plugged in before 3V3 rises), and above
    4 V the pin's pull-up / pull-down must be off (Table 21 note 4) (Calculation / Inference: the VBUS range, drift)."""
    r9, r110, leak = 1e3, 1.5e3, 250e-9
    v33 = r12_budget.rails()[r12_budget.V33_RAIL]
    want = {'R9': {'1': 'VBUS', '2': 'VBUS_SENSE'}, 'R110': {'1': 'VBUS_SENSE', '2': 'GND'}}
    out = dict(topology=nets, topology_ok=nets == want, R9_ohm=r9, R110_ohm=r110, ratio_nominal=r110 / (r9 + r110),
               vbus_V=[4.45, 5.5], pc9_leak_A=leak, cases={})
    for case, tol in TOL.items():
        lo = r110 * (1 - tol) / (r110 * (1 - tol) + r9 * (1 + tol))
        hi = r110 * (1 + tol) / (r110 * (1 + tol) + r9 * (1 - tol))
        rth = r9 * r110 / (r9 + r110) * (1 + tol)
        vih = 0.7 * v33[case]['max_V']
        vmin, vmax = 4.45 * lo - leak * rth, 5.5 * hi + leak * rth
        out['cases'][case] = dict(ratio=[lo, hi], VBUS_SENSE_V=[vmin, vmax], vih_V=vih,
                                  margin_over_vih_V=vmin - vih, reads_high_from_VBUS_V=(vih + leak * rth) / lo,
                                  abs_max_V=min(4.0, v33[case]['min_V'] + 4.0), margin_to_abs_max_V=4.0 - vmax,
                                  ok=vmin > vih and vmax < 4.0)
    out['ok'] = out['topology_ok'] and all(c['ok'] for c in out['cases'].values())
    out['source'] = ('DS12110 Rev 8 Table 21 (FT_xxx VIN max min(VDD, VDDA, VDD33USB, VBAT) + 4.0 V; note 4), Table 60 '
                     '(VIH 0.7 VDD; FT_xx leakage +/-250 nA), Table 9 (PC9 FT_fh); 3V3 window r12_windows.json')
    out['label'] = 'Calculation / Inference (3V3 window, D-R12-139; the VBUS range and resistor drift)'
    return out


def q122_gate(nets):
    """R12F12-TRI-04: Q122 (AO3400A) gate from PC1 through R122 1k into R123 2k || R118 10k (lane P's R118, the
    triage's R124). VGS = VOH x Rp / (Rp + R122): at 3.30 V ideal, and at the 3V3 drift minimum with VOH = VDD - 0.4 V
    (DS12110 Rev 8 Table 158 at 4 mA) and every resistor at its worse drift end; the single-open cases (one pull-down
    open); PC1's source current. AO3400A VGS(th) <= 1.45 V, RDS(on) row at 2.5 V (D-R12-10) (Calculation / Inference:
    3V3 window, drift)."""
    td = TOL['drift']
    v33 = r12_budget.rails()[r12_budget.V33_RAIL]

    def par(*rs):
        return 1 / sum(1 / r for r in rs)
    rp = par(2e3, 10e3)
    want = {'R122': {'1': 'ACT_EN_MCU', '2': 'ACT_EN'}, 'R123': {'1': 'ACT_EN', '2': 'GND'},
            'R118': {'1': 'ACT_EN', '2': 'GND'}, 'Q122': {'1': 'ACT_EN', '2': 'GND', '3': 'ACT_DRV'}}
    out = dict(topology=nets, topology_ok=nets == want, R122_ohm=1e3, R123_ohm=2e3, R118_ohm=10e3, pulldown_ohm=rp, vgs_th_max_V=1.45,
               rds_row_V=2.5)
    out['vgs_nominal_3V30_V'] = 3.30 * rp / (rp + 1e3)
    out['vgs_3V224_V'] = 3.224 * rp / (rp + 1e3)
    rp_lo, r122_hi = par(2e3 * (1 - td), 10e3 * (1 - td)), 1e3 * (1 + td)
    vdd = v33['drift']['min_V']
    out['vgs_min_V'] = (vdd - VOH_DROP) * rp_lo / (rp_lo + r122_hi)
    out['vgs_min_basis'] = dict(vdd_min_V=vdd, voh_drop_V=VOH_DROP, resistor_tolerance=td)
    out['single_open_V'] = dict(R118_open=(vdd - VOH_DROP) * 2e3 * (1 - td) / (2e3 * (1 - td) + r122_hi),
                                R123_open=(vdd - VOH_DROP) * 10e3 * (1 - td) / (10e3 * (1 - td) + r122_hi))
    vmax = v33['drift']['max_V']
    out['pc1_source_mA_max'] = vmax / (rp_lo + 1e3 * (1 - td)) * 1e3
    out['pc1_within_voh_row'] = out['pc1_source_mA_max'] <= VOH_ROW_MA
    out['margin_over_vgs_th_V'] = out['vgs_min_V'] - 1.45
    out['off_hold'] = 'PC1 high-Z or low: two DC holds on ACT_EN (R123 2k, R118 10k), each alone holds Q122 off'
    out['label'] = ('Calculation / Inference (3V3 window, D-R12-139; resistor drift; Q122 conducts the PFET gate '
                    'divider\'s sub-mA current at VGS above VGS(th), Inference on the transfer curve)')
    return out


def d8_return(board, stack):
    """R12F12-TRI-16: D8's GND return (D8.2 to the In1 GND plane): the F.Cu tracks ending in D8.2 and their vias.
    Series R at 20 C (centreline length, so the copper inside the pad is counted: an upper bound) and the microstrip L
    over In1 (r10_hotplug.microstrip_nh), the runs in parallel; the via barrels F -> In1 at R10's 20 um plating. The
    hot-plug model takes D8.2 as ideal ground; this is the return it leaves out (Calculation / Inference: the
    inductance formula, plane spreading not modelled)."""
    import pcbnew
    import r10_hotplug
    mm = pcbnew.ToMM
    pad = fps(board)['D8'].FindPadByNumber(pads_on(board, 'D8', 'GND')[0])
    runs, vias = [], []
    h = stack['In1.Cu'][1] - stack['F.Cu'][1]
    for t in board.GetTracks():
        if t.GetNetname() != 'GND' or t.GetClass() != 'PCB_TRACK' or t.GetLayer() != pcbnew.F_Cu:
            continue
        if not (pad.HitTest(t.GetStart()) or pad.HitTest(t.GetEnd())):
            continue
        w, L = mm(t.GetWidth()), mm(t.GetLength())
        far = t.GetEnd() if pad.HitTest(t.GetStart()) else t.GetStart()
        via = next((v for v in board.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND'
                    and (v.GetPosition() - far).EuclideanNorm() <= v.GetWidth(pcbnew.F_Cu) // 2), None)
        inside = 0.0
        n = 200
        for i in range(n):
            q = pcbnew.VECTOR2I(int(t.GetStart().x + (t.GetEnd().x - t.GetStart().x) * (i + .5) / n),
                                int(t.GetStart().y + (t.GetEnd().y - t.GetStart().y) * (i + .5) / n))
            inside += pad.HitTest(q) / n
        runs.append(dict(width_mm=round(w, 3), length_mm=round(L, 4), outside_pad_mm=round(L * (1 - inside), 4),
                         R_20C_ohm=seg_r(L, w, stack['F.Cu'][0]), L_nH=r10_hotplug.microstrip_nh(w, h, L),
                         via=None if via is None else [round(mm(via.GetPosition().x), 3),
                                                       round(mm(via.GetPosition().y), 3), round(mm(via.GetDrillValue()), 3)]))
    if len(runs) < 1 or any(r['via'] is None for r in runs):
        raise ValueError('D8.2: a GND run does not end in a via')
    barrel = RHO * h * 1e-3 / (math.pi * (runs[0]['via'][2] + .020) * .020 * 1e-6)
    r_par = 1 / sum(1 / (r['R_20C_ohm'] + barrel) for r in runs)
    l_par = 1 / sum(1 / r['L_nH'] for r in runs)
    return dict(pad=[round(mm(pad.GetPosition().x), 3), round(mm(pad.GetPosition().y), 3)], runs=runs,
                via_barrel_F_to_In1_ohm=barrel, R_20C_ohm=r_par, R_70C_ohm=r_par * HOT_CU, L_nH=l_par,
                label=('Calculation / Inference: centreline track R at 20 C (the part inside D8.2 counted, an upper '
                       'bound), 20 um barrels, microstrip L over In1 (Inference), runs in parallel; the hot-plug model '
                       'takes D8.2 as ideal ground and leaves this out'))


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
            ('RAW_PROTECTED_U9_to_U400', 'RAW_PROTECTED', spec(board, 'U9', 'RAW_PROTECTED'),
             'U400:' + ','.join(BUCK_VIN)),                       # VIN only (R12F2-TRI-06)
            ('RAW_PROTECTED_U9_to_U403', 'RAW_PROTECTED', spec(board, 'U9', 'RAW_PROTECTED'), spec(board, 'U403', 'RAW_PROTECTED')),
            ('RAW_PROTECTED_U9_to_D5', 'RAW_PROTECTED', spec(board, 'U9', 'RAW_PROTECTED'), spec(board, 'D5', 'RAW_PROTECTED')),
            ('VLOGIC_D5_to_U2', 'VLOGIC', spec(board, 'D5', 'VLOGIC'), spec(board, 'U2', 'VLOGIC')),
            ('VLOGIC_C84_to_U2', 'VLOGIC', spec(board, 'C84', 'VLOGIC'), spec(board, 'U2', 'VLOGIC')),
            ('VLOGIC_D6_to_U2', 'VLOGIC', spec(board, 'D6', 'VLOGIC'), spec(board, 'U2', 'VLOGIC')),
            ('VLOGIC_D5_to_R60', 'VLOGIC', spec(board, 'D5', 'VLOGIC'), spec(board, 'R60', 'VLOGIC')),
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
    # R12F12-TRI-30: BAT_IN as one network (J1.1; U9.5, Q120.3, R80.1)
    net = bat_in_network(board_path, board)
    print('BAT_IN network (mOhm): ' + json.dumps({a: {b: round(r * 1e3, 4) for b, r in row.items()}
                                                 for a, row in net['Z_ohm'].items()}), flush=True)
    z20 = net['Z_ohm']
    # R12F10-TRI-09: the pack's converter load is raw_point's self-consistent current on the board's copper at 70 C
    raw_hot = {k: S[f'RAW_PROTECTED_U9_to_{k}']['resistance_ohm'] * HOT_CU for k in RAW_SINKS}
    feed_hot, fire_hot = z20['U9']['U9'] * HOT_CU, z20['U9']['Q120'] * HOT_CU
    u2_hot = S['VLOGIC_D5_to_U2']['resistance_ohm'] * HOT_CU
    parts = other_load_w()[1]
    fire = fire_budget(copper, gnd, lambda v, i_f: raw_point(v, parts, feed_hot, raw_hot, u2_hot, i_fire=i_f,
                                                             z_fire_ohm=fire_hot), z20)
    four = fire['four_stall_BAT_IN_V']
    sens = fire['pack_load_sensitivity']
    en_sens = en_figures(sens['four_stall_R80_V'], sens['four_stall_BAT_IN_V'])
    eb = en_sens['bound']
    sens['en_at_that_BAT_IN'] = {k: eb[k] for k in ('four_stall_periodic_limit_ms', 'margin_over_7ms_line_ms',
                                                    'seven_ms_line_holds_at_four_stall', 'seven_ms_line_holds_down_to_V')}
    sens['en_at_that_BAT_IN']['R80_V'] = sens['four_stall_R80_V']
    en = en_figures(fire['four_stall_R80_V'], four)
    en['chatter_rule'] = chatter_rule(en, en_sens)
    rails, shared = rail_paths(board, stack, fire)
    out = dict(
        status='Calculation on R12 CAD copper with R10 component tolerances; Inference where labelled; no physical test',
        board_sha256=before, source_board_sha256=sha(a.source_board) if a.source_board else None,
        stackup={k: dict(thickness_mm=v[0], depth_mm=v[1]) for k, v in stack.items()},
        fire_copper=copper, fire=fire,
        fire_adiabatic={f'{w}mm_{int(th * 1e3)}um_{int(t * 1e3)}ms': adiabatic(SHORT_A, w, th, t)
                        for w in sorted({w for c in copper.values() for w in c['widths_mm']})
                        for th in (stack['F.Cu'][0],) for t in (.020, .036)},
        fire_return=fire_return(board, stack),
        bat_in_network=net,
        en=en,
        holdup=holdup(four),
        pa6_corners=pa6_corners(fire, z20['U9']['U9'],
                                {k: S[f'RAW_PROTECTED_U9_to_{k}']['resistance_ohm'] for k in ('D5', 'U400', 'U403')},
                                {k: S[f'VLOGIC_D5_to_{k}']['resistance_ohm'] for k in ('R60', 'U2')},
                                z_fire_ohm=z20['U9']['Q120']),
        u403_input=u403_input(fire, S),
        u400_feed_drop=u400_feed_drop(rails, shared),
        rails=rails,
        rails_shared=dict(groups=shared, raw_budget_A=raw_budget_currents(fire), source_A=SOURCE_A,
                          note=('tracks on more than one load path, rated at the summed current (R12F2-TRI-07); each '
                                "path's own by_width_mm figures are at its own current")),
        dc_solves=S,
        u6_supply=u6_supply(S) if '3V3_L1_to_U6' in S else None,
        port_supply=port_supply(S, fire),
        gate=gate_copper(board, stack),
        imu=imu(board),
        u3v3_budget=u3v3_budget(),
        vbus_sense=vbus_sense({r: {p.GetNumber(): p.GetNetname() for p in fps(board)[r].Pads()} for r in ('R9', 'R110')}),
        q122_gate=q122_gate({r: {p.GetNumber(): p.GetNetname() for p in fps(board)[r].Pads()}
                             for r in ('R122', 'R123', 'R118', 'Q122')}),
        d8_return=d8_return(board, stack))
    if sha(board_path) != before:
        raise ValueError('board changed during the analysis')
    issues = record_issues(out)
    if out['source_board_sha256'] not in (None, before):
        issues.append('the analysed board is not a byte copy of the source board')
    if issues:
        raise SystemExit('stage D record refused: ' + '; '.join(issues))
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    print(json.dumps(dict(loop_ohm=fire['total_loop_ohm'], four_stall_A=fire['four_stall_A'],
                          four_stall_BAT_IN_V=four, four_stall_R80_V=fire['four_stall_R80_V'], gnd_return_ohm=gnd,
                          chatter=en['chatter_rule']), indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
