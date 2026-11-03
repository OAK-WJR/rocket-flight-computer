#!/usr/bin/env python3
"""R4-style solder-bridge table (R9 gate P-5) and the reset-voltage model of the pyro gate (R9 gate P-7).

usage: <KiCad python3> -I tools/bridge_table.py BOARD.kicad_pcb [--json OUT] [--all]     exit 0 = no forbidden pair

The table (survey_constraints.md section 9.4 item 3; docs/M3_R4.md sections 1n, 1o, 2 and 3): every pair of exposed
pads (both pads open in the solder mask on the same face, different nets, different parts) closer than REPORT where
the pair can change a pyro or actuator-switch state: one net is a pyro gate, an actuator-switch gate, armed-live
(bus, igniter, drain), a sense node, a divider midpoint, the cold node or a sense line's MCU side, or both nets are
among RAW_ACT and the battery-live nets. Each pair gets the consequence of one solder bridge and the cold-test
signature (M3_R4 section 3) and is either tolerated or forbidden:

  tolerated  (R4's classes) a drain against its own divider's midpoint or its own COLD pad, COLD against its own
             midpoint; a midpoint against its own sense node or against the other pyro midpoint (nearly equal
             voltages); a live net against a divider midpoint (one 5.1 k top half shorted: F8's single-fault bound,
             node <= 1.4 V, 3.3 V at the 19.9 V clamp); and the fail-safe equivalents of one analysed part fault: a
             pyro gate to GND or GATE to GATE_N (R126 / R127 / R128 / C126 shorted: the gate held off), a sense node or
             midpoint or MCU-side sense line to GND (reads no continuity / disarmed: the ground refusal), a sense node
             to its own MCU side (R168 / R170 / R172 shorted: still within F8's single-fault bound), the actuator gate
             to its own source or the battery input (switch held off), ACT_GATE to ACT_DRV (R121 shorted), and a gate
             to a passive source whose reset voltage (below) stays under GATE_RESET_MAX; a pad with no net
  forbidden  everything else in scope, at BRIDGE mm (STRICT for the pairs R9's strict pad rules name: a live net or
             RAW_ACT against a sense node or a gate, a midpoint against a gate, a gate against a sense node, midpoint
             or COLD, an actuator-switch gate against GND)

A part's own pads (its own short is the part's own fault, analysed in F8 / FMEA) are listed apart and not gated.

Reset model (survey_constraints.md section 9.4 item 6): with the MCU in reset U1.3 is high impedance, R127 (1 k)
holds PYRO1_GATE_N, R126 (220 R) feeds the gate and R128 (10 k) ties it to its source (check_actuators 4 / 4c pin these
values). A hard short from a source of open-circuit voltage Vth and resistance Rth puts on the gate
  to GATE_N: Vth * Rn / (Rth + Rn) * R128 / (R126 + R128),   Rn = R127 || (R126 + R128)
  to GATE:   Vth * Rg / (Rth + Rg),                          Rg = R128 || (R126 + R127)
Sources, with the board armed at the 2S pack's 8.4 V maximum (REQUIREMENTS F9): a sense node is its divider's
Thevenin (8.4 V / 11.2 through 10.2 k || 1 k); a sense line's MCU side the same plus the 4.7 k series resistor; a
midpoint 8.4 V * 6.1 / 11.2 through 5.1 k || 6.1 k; GND and pads with no net 0 V; COLD (BAT54A from 3V3), every rail,
armed-live net and driven logic net is stiff (>= 3.3 V through 0 ohm). The AON7524's minimum threshold is 0.4 V at
25 C (Alpha & Omega AON7524 data sheet, lower hot); GATE_RESET_MAX = 0.2 V keeps a factor of two (survey P-7).
ARM1_SENSE through its divider gives 0.37 V (the R8P1-PYRO-04 figure); an MCU-side sense line gives 0.10 V.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_r8 as C8                                           # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
BRIDGE, STRICT, REPORT = 1.0, 1.2, 1.5
ARMED = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
GATES = ('PYRO1_GATE', 'PYRO1_GATE_N')
ACT_GATES = ('ACT_GATE', 'ACT_DRV')
NODES = ('ARM1_SENSE', 'PYRO1_CONT', 'RAW_ACT_SENSE')
MIDS = ('PYRO1_CONT_MID', 'ARM1_SENSE_MID', 'RAW_ACT_SENSE_MID')
COLD = 'PYRO1_COLD'
MCU_SIDE = ('ARM1_SENSE_MCU', 'PYRO1_CONT_MCU', 'RAW_ACT_SENSE_MCU')
OWN_NODE = {'PYRO1_CONT_MID': 'PYRO1_CONT', 'ARM1_SENSE_MID': 'ARM1_SENSE', 'RAW_ACT_SENSE_MID': 'RAW_ACT_SENSE',
            'PYRO1_CONT_MCU': 'PYRO1_CONT', 'ARM1_SENSE_MCU': 'ARM1_SENSE', 'RAW_ACT_SENSE_MCU': 'RAW_ACT_SENSE'}
MID_SOURCE = {'PYRO1_CONT_MID': 'PYRO1_OUT', 'ARM1_SENSE_MID': 'PYRO1_BUS', 'RAW_ACT_SENSE_MID': 'RAW_ACT'}
BATTERY = ('RAW_ACT', 'BAT_IN', 'ACT_FET_S', 'RAW_PROTECTED')
PYRO_SCOPE = set(ARMED + GATES + ACT_GATES + NODES + MIDS + MCU_SIDE + (COLD,))
# gate network (check_actuators 4 / 4c) and the divider (F8): ohm
R126, R127, R128 = 220.0, 1000.0, 10000.0
TOP, BOTTOM, SERIES = 10200.0, 1000.0, 4700.0
V_PACK = 8.4
GATE_RESET_MAX = 0.2
STIFF = (3.3, 0.0)


def source_of(net):
    """(Vth V, Rth ohm) of a hard short from `net` with the MCU in reset and the board armed, or None for GND / no
    net (0 V); STIFF for rails, armed-live, COLD and driven logic."""
    if not net or net.startswith('unconnected-') or net == 'GND':
        return None
    node_v, node_r = V_PACK * BOTTOM / (TOP + BOTTOM), TOP * BOTTOM / (TOP + BOTTOM)
    if net in NODES:
        return node_v, node_r
    if net in MCU_SIDE:
        return node_v, node_r + SERIES
    if net in MIDS:
        below = TOP / 2 + BOTTOM
        return V_PACK * below / (TOP / 2 + below), (TOP / 2) * below / (TOP / 2 + below)
    return STIFF


def gate_voltage(net, at):
    """Gate voltage (V) in reset when `net` is shorted to `at` (PYRO1_GATE or PYRO1_GATE_N)."""
    s = source_of(net)
    if s is None:
        return 0.0
    vth, rth = s
    if at == 'PYRO1_GATE_N':
        rn = R127 * (R126 + R128) / (R127 + R126 + R128)
        return vth * rn / (rth + rn) * R128 / (R126 + R128)
    rg = R128 * (R126 + R127) / (R128 + R126 + R127)
    return vth * rg / (rth + rg)


def classify(n1, n2):
    """(class, tolerated, threshold mm, cold-test signature) of one bridge between nets n1 and n2, or None when the
    pair cannot change a pyro or actuator-switch state."""
    s = {n1, n2}
    if not (s & PYRO_SCOPE) and not (len(s & set(BATTERY + ('ACT_EN',))) == 2):
        return None
    nc = [n for n in (n1, n2) if not n or n.startswith('unconnected-')]
    if nc:
        return 'pad with no net: no consequence', True, BRIDGE, 'none'

    def other(x):
        return n2 if x == n1 else n1
    # pyro gates
    g = [n for n in (n1, n2) if n in GATES]
    if len(g) == 2:
        return 'GATE to GATE_N: R126 shorted, the gate follows GATE_N (R127 holds it in reset)', True, BRIDGE, 'none'
    if g:
        o = other(g[0])
        if o == 'GND':
            return 'gate to GND: holds the FET off (R127 / R128 / C126 short)', True, BRIDGE, 'refuses fire (bench)'
        v = gate_voltage(o, g[0])
        strict = o in ARMED + ('RAW_ACT',) + NODES + MIDS + (COLD,)
        thr = STRICT if strict else BRIDGE
        if v < GATE_RESET_MAX:
            return (f'gate to {o}: {v:.2f} V on the gate in reset (< {GATE_RESET_MAX} V)', True, thr,
                    'none in reset; firmware drives GATE_N low when running')
        return f'FIRES: {o} on the pyro gate ({v:.2f} V in reset)', False, thr, 'shorted-FET signature (0 / 0 V)'
    # actuator-switch gates (P-channel AON6403 pair: gate low = on)
    a = [n for n in (n1, n2) if n in ACT_GATES]
    if a:
        o = other(a[0])
        if len(a) == 2:
            return 'ACT_GATE to ACT_DRV: R121 shorted', True, BRIDGE, 'none'
        if o in ('ACT_FET_S', 'BAT_IN'):
            return f'{a[0]} to {o}: gate at source, switch held off', True, BRIDGE, 'actuators dead (bench)'
        thr = STRICT if o == 'GND' else BRIDGE
        return f'actuator switch on: {o} pulls {a[0]} (RAW_ACT live with the power switch open)', False, thr, \
            'RAW_ACT present with the switch open'
    # armed-live copper
    live = [n for n in (n1, n2) if n in ARMED]
    if live:
        x = live[0]
        o = other(x)
        if o in ARMED:
            what = {frozenset(('PYRO1_BUS', 'PYRO1_IGN')): 'R134 shorted: shorted-igniter current limit lost',
                    frozenset(('PYRO1_BUS', 'PYRO1_OUT')): 'bus on the drain: igniter and R134 bypassed',
                    frozenset(('PYRO1_IGN', 'PYRO1_OUT')): 'igniter shorted: no deployment'}[frozenset((x, o))]
            return what, False, BRIDGE, 'continuity reads short'
        if o == 'GND':
            what = {'PYRO1_OUT': 'FIRES when armed: drain to GND bypasses Q124',
                    'PYRO1_IGN': 'R134 across the armed bus (4.1 A, below the 5 A fuse)',
                    'PYRO1_BUS': 'armed bus to GND (the 5 A link fuse clears)'}[x]
            return what, False, BRIDGE, 'arm sense 0 V'
        if o in MIDS:
            if MID_SOURCE[o] == x:
                return f'{x} to its own midpoint: one 5.1 k half shorted (R4 tolerated)', True, BRIDGE, \
                    'one half shorted: 0.142 / 0.077 V (M3_R4 section 3)'
            return f'{x} on {o}: one 5.1 k top half shorted (F8 single fault, node <= 1.4 V)', True, BRIDGE, \
                'one half shorted signature'
        if o == COLD:
            if x == 'PYRO1_OUT':
                return 'drain to its own COLD pad: R131 shorted (R4 tolerated)', True, BRIDGE, 'outside the healthy band'
            return f'{x} on COLD (D120 to the armed bus)', False, BRIDGE, 'cold test'
        if o in NODES + MCU_SIDE:
            return f'live past the divider top: {x} on {o} (ADC overstress)', False, STRICT, 'hard fault (> 0.2 V)'
        if o == 'RAW_ACT':
            return ('BYPASSES the ARM break' if x != 'PYRO1_OUT' else 'RAW_ACT on the drain'), False, BRIDGE, \
                'arm sense high with the link out'
        return f'{o} on armed copper {x}', False, BRIDGE, 'cold test'
    # RAW_ACT / battery-live with each other
    b = [n for n in (n1, n2) if n in BATTERY + ('ACT_EN',)]
    if len(b) == 2 and 'RAW_ACT' in s:
        return f'actuator switch bypassed: {other("RAW_ACT")} on RAW_ACT', False, BRIDGE, \
            'RAW_ACT present with the switch open'
    # midpoints, nodes, COLD, MCU sides
    m = [n for n in (n1, n2) if n in MIDS]
    if m:
        o = other(m[0])
        if o == OWN_NODE[m[0]]:
            return f'{m[0]} to its own node: one 5.1 k half shorted (R4 pass 11)', True, BRIDGE, 'one half shorted'
        if o in MIDS and {m[0], o} == {'PYRO1_CONT_MID', 'ARM1_SENSE_MID'}:
            return 'the two pyro midpoints (nearly equal voltage, R4)', True, BRIDGE, 'none armed'
        if o == 'GND':
            return f'{m[0]} to GND: reads no continuity / disarmed (ground refusal)', True, BRIDGE, 'node 0 V'
        if o == COLD and m[0] == 'PYRO1_CONT_MID':
            return 'COLD to its own midpoint (R4 tolerated)', True, BRIDGE, 'CONT 0.49 V cold, 0.89 V armed'
        if o in NODES or o in MCU_SIDE:
            return f'{m[0]} on another node {o} through one 5.1 k half', True, BRIDGE, 'node <= 1.4 V'
        return f'{o} drives midpoint {m[0]}', False, BRIDGE, 'cold test'
    nd = [n for n in (n1, n2) if n in NODES]
    if nd:
        o = other(nd[0])
        if o == 'GND':
            return f'{nd[0]} to GND: reads no continuity / disarmed (ground refusal)', True, BRIDGE, 'node 0 V'
        if o in MCU_SIDE and OWN_NODE[o] == nd[0]:
            return f'{nd[0]} to its MCU side: the 4.7 k series resistor shorted (F8 single fault)', True, BRIDGE, 'none'
        return f'{o} drives sense node {nd[0]}', False, STRICT if o in ARMED + ('RAW_ACT',) else BRIDGE, 'cold test'
    if COLD in s:
        o = other(COLD)
        return f'COLD to {o} (D120 / R131 cold bias)', False, BRIDGE, 'cold test'
    sm = [n for n in (n1, n2) if n in MCU_SIDE]
    if sm:
        o = other(sm[0])
        if o == 'GND':
            return f'{sm[0]} to GND: the ADC reads 0 (ground refusal)', True, BRIDGE, 'node reads 0 V'
        return f'{o} on the ADC pin of {sm[0]} (past its 4.7 k)', False, BRIDGE, 'hard fault'
    return None


def exposed_pads(board):
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            for face, cu, mask in (('F', pcbnew.F_Cu, pcbnew.F_Mask), ('B', pcbnew.B_Cu, pcbnew.B_Mask)):
                if p.IsOnLayer(cu) and p.IsOnLayer(mask):
                    out.append((f.GetReference(), p.GetNumber(), p.GetNetname() or '', face, p.GetEffectiveShape(cu), p))
    return out


def table(board, report=REPORT):
    """[dict(gap, a, b, face, class, tolerated, threshold, signature, own_part, forbidden)] sorted by gap."""
    pads = exposed_pads(board)
    rows = []
    for i, (ra, na_, nna, fa, sa, pa) in enumerate(pads):
        ca = pa.GetPosition()
        for rb, nb_, nnb, fb, sb, pb in pads[i + 1:]:
            if fa != fb or nna == nnb:
                continue
            cb = pb.GetPosition()
            if abs(mm(ca.x - cb.x)) > 12 or abs(mm(ca.y - cb.y)) > 12:
                continue
            cls = classify(nna, nnb)
            if cls is None:
                continue
            g = C8.min_gap(sa, sb, report)
            if g is None:
                continue
            what, ok, thr, sig = cls
            own = ra == rb
            rows.append(dict(gap=g, a=f'{ra}.{na_} ({nna})', b=f'{rb}.{nb_} ({nnb})', face=fa, consequence=what,
                             tolerated=ok, threshold=thr, signature=sig, own_part=own,
                             forbidden=(not own and not ok and g < thr - 1e-3)))
    rows.sort(key=lambda r: (r['gap'], r['a'], r['b']))
    return rows


def issues_of(rows):
    return [f"bridge table (P-5): {r['a']} to {r['b']} ({r['face']}) is {r['gap']:.3f} mm < {r['threshold']} mm: "
            f"{r['consequence']}" for r in rows if r['forbidden']]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', type=Path)
    ap.add_argument('--json', type=Path)
    ap.add_argument('--all', action='store_true', help='print own-part pairs too')
    a = ap.parse_args()
    rows = table(pcbnew.LoadBoard(str(a.board.resolve())))
    for r in rows:
        if r['own_part'] and not a.all:
            continue
        tag = 'FORBIDDEN' if r['forbidden'] else ('own part ' if r['own_part'] else
                                                  ('tolerated' if r['tolerated'] else 'listed   '))
        print(f"{r['gap']:6.3f} {r['face']} {tag} {r['a']} -- {r['b']}: {r['consequence']} [{r['signature']}]")
    bad = issues_of(rows)
    print(f'bridge table: {len(rows)} pairs < {REPORT} mm ({sum(1 for r in rows if r["own_part"])} own-part), '
          f'{len(bad)} forbidden:', 'OK' if not bad else 'FAIL')
    if a.json:
        a.json.write_text(json.dumps(rows, indent=1) + '\n')
    return 0 if not bad else 1


if __name__ == '__main__':
    raise SystemExit(main())
