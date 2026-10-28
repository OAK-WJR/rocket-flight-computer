#!/usr/bin/env python3
"""Critical-net reference coverage, the R6 acceptance method (docs/M3_R6.md "104,241 critical reference samples";
sources/r6-independent-routing-reference-review-20261013.json "method"), between a base and a candidate board.

usage: <KiCad python3> tools/critical_reference.py BASE.kicad_pcb CANDIDATE.kicad_pcb [--dy 18] [--extended] [--json OUT]

Both boards must carry their saved zone fills. Every track of the critical nets is sampled along its centre line and
both copper edges every 0.01 mm (an arc track along its curve: centre radius and radius +- half width, R3-GATE-01);
a sample is referenced when it lies inside the adjacent reference fill:
  F.Cu track -> In1.Cu GND;  B.Cu track -> In2.Cu GND, 3V3 or 3V3A  (R6 method)
  --extended also samples In1 tracks (reference F.Cu GND) and In2 tracks (reference B.Cu GND) and adds SWDIO, SWCLK,
  NRST and the radio SPI nets (the R7 pass-2 regression review's extension).
Reported, R6 style: the base's referenced samples (R6 final board: 104,241) and how many of them lose their reference
on the candidate (base tracks sampled against the candidate's fills, after moving the base by --dy in y); then the
candidate's own critical tracks: samples unreferenced on the candidate whose position was referenced on the base
(new losses on new or moved copper). Read-only.
"""
import argparse
from collections import defaultdict
import json
import math
import re

import pcbnew

mm, MM = pcbnew.ToMM, pcbnew.FromMM
R6_NETS = ('USB_DP', 'USB_DM', 'HSE_IN', 'HSE_OUT', 'QSPI_CLK', 'QSPI_NCS', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2',
           'QSPI_IO3', 'SPI1_SCK', 'SPI1_MOSI', 'SPI1_MISO', 'IMU_CS')
EXTENDED = ('SWDIO', 'SWCLK', 'NRST', 'RADIO_NSS', 'RADIO_SCK', 'RADIO_SCK_MCU', 'RADIO_MOSI', 'RADIO_MOSI_MCU',
            'RADIO_MISO', 'RADIO_MISO_MCU')
# R10 external-port signal nets: the ONE definition both gates use (R3-RTE-01 / R3-GATE-04): route_check profile r10
# classes them critical (GND via within 1.5 mm of every layer change, the critical hygiene rules) and check_r10
# K-reference samples them. UART data on all three segments (MCU side, translator buffer side, wire side after the
# 1 kOhm), the camera's MCU-side pair (CAM_MCU_TX / _RX: the R9 names kept for U12), and the port control lines
# (load-switch enable, fault flag, translator output enable).
R10_PORT_UART = re.compile(r'^((GPS|RADIO|CAM)_(TX|RX)_(MCU|WIRE|BUFFER)|CAM_MCU_(TX|RX))$')
R10_PORT_CONTROL = re.compile(r'^(GPS|RADIO|CAM)_(PWR_EN|FAULT_N|UART_OE)$')
R10_PORT_NETS = ('CAM_MCU_TX', 'CAM_MCU_RX') + tuple(f'{port}_{signal}_{side}' for port in ('GPS', 'RADIO', 'CAM')
                      for signal in ('TX', 'RX') for side in ('MCU', 'WIRE', 'BUFFER')) + tuple(
    f'{port}_{signal}' for port in ('GPS', 'RADIO', 'CAM') for signal in ('PWR_EN', 'FAULT_N', 'UART_OE'))
assert all(R10_PORT_UART.match(n) or R10_PORT_CONTROL.match(n) for n in R10_PORT_NETS)


def r10_port_net(name):
    """Whether `name` is an R10 external-port signal net (R10_PORT_UART or R10_PORT_CONTROL)."""
    return bool(R10_PORT_UART.match(name or '') or R10_PORT_CONTROL.match(name or ''))


STEP = 0.01


def references(extended):
    ref = {pcbnew.F_Cu: (pcbnew.In1_Cu, ('GND',)), pcbnew.B_Cu: (pcbnew.In2_Cu, ('GND', '3V3', '3V3A'))}
    if extended:
        ref[pcbnew.In1_Cu] = (pcbnew.F_Cu, ('GND',))
        ref[pcbnew.In2_Cu] = (pcbnew.B_Cu, ('GND',))
    return ref


def fills(b, refs):
    out = {}
    for layer, (rlay, nets) in refs.items():
        ps = pcbnew.SHAPE_POLY_SET()
        for z in b.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() in nets and z.IsOnLayer(rlay) and z.HasFilledPolysForLayer(rlay):
                ps.BooleanAdd(z.GetFilledPolysList(rlay))
        out[layer] = ps
    return out


def track_samples(t, dy=0.0, step=STEP, margin=0.0):
    """(net, layer, x, y) samples (mm) of one straight track (centre line and both copper edges pushed `margin`
    outward, every `step` mm) or arc track, moved by dy."""
    if t.GetClass() == 'PCB_ARC':
        return arc_samples(t, dy, step, margin)
    out = []
    ax, ay, cx, cy = mm(t.GetStart().x), mm(t.GetStart().y) + dy, mm(t.GetEnd().x), mm(t.GetEnd().y) + dy
    length = math.hypot(cx - ax, cy - ay)
    if length == 0:
        return out
    ux, uy = (cx - ax) / length, (cy - ay) / length
    hw = mm(t.GetWidth()) / 2 + margin
    n = int(math.ceil(length / step))
    for k in range(n + 1):
        s = min(length, k * step)
        px, py = ax + ux * s, ay + uy * s
        for off in (0.0, hw, -hw):
            out.append((t.GetNetname(), t.GetLayer(), round(px - uy * off, 4), round(py + ux * off, 4)))
    return out


def samples(b, nets, refs, dy=0.0):
    """(net, layer, x, y) samples (mm) of the nets' tracks on the reference-mapped layers, moved by dy."""
    out = []
    for t in b.GetTracks():
        if t.GetClass() not in ('PCB_TRACK', 'PCB_ARC') or t.GetNetname() not in nets or t.GetLayer() not in refs:
            continue
        out += track_samples(t, dy)
    return out


def arc_samples(t, dy=0.0, step=STEP, margin=0.0):
    """(net, layer, x, y) samples of an arc track along its curve (start -> mid -> end), every STEP mm of the centre
    radius, on the centre line and both copper edges (radius +- half width); a degenerate arc (collinear points) is
    sampled as its chord."""
    pts = [(mm(p.x), mm(p.y) + dy) for p in (t.GetStart(), t.GetMid(), t.GetEnd())]
    (x1, y1), (x2, y2), (x3, y3) = pts
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    hw = mm(t.GetWidth()) / 2 + margin
    net, lay = t.GetNetname(), t.GetLayer()
    if abs(d) < 1e-12:
        out = []
        for (ax, ay), (cx, cy) in ((pts[0], pts[1]), (pts[1], pts[2])):
            length = math.hypot(cx - ax, cy - ay)
            if length == 0:
                continue
            ux, uy = (cx - ax) / length, (cy - ay) / length
            for k in range(int(math.ceil(length / step)) + 1):
                s = min(length, k * step)
                for off in (0.0, hw, -hw):
                    out.append((net, lay, round(ax + ux * s - uy * off, 4), round(ay + uy * s + ux * off, 4)))
        return out
    s1, s2, s3 = x1 * x1 + y1 * y1, x2 * x2 + y2 * y2, x3 * x3 + y3 * y3
    ux = (s1 * (y2 - y3) + s2 * (y3 - y1) + s3 * (y1 - y2)) / d
    uy = (s1 * (x3 - x2) + s2 * (x1 - x3) + s3 * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1, a2, a3 = (math.atan2(y - uy, x - ux) for x, y in pts)
    sweep = (a3 - a1) % (2 * math.pi)               # counter-clockwise from start to end ...
    if (a2 - a1) % (2 * math.pi) > sweep:           # ... unless the mid point lies on the other way round
        sweep -= 2 * math.pi
    n = max(1, int(math.ceil(abs(sweep) * r / step)))
    out = []
    for k in range(n + 1):
        a = a1 + sweep * k / n
        for rr in (r, r + hw, max(0.0, r - hw)):
            out.append((net, lay, round(ux + rr * math.cos(a), 4), round(uy + rr * math.sin(a), 4)))
    return out


def inside(polys, x, y):
    return polys.Contains(pcbnew.VECTOR2I(MM(x), MM(y)), -1, 0, True)


def compare(base, cand, dy, extended, profile="r9"):
    refs = references(extended)
    if profile not in ('r9', 'r10'):
        raise ValueError(f'unknown reference profile {profile!r}')
    nets = R6_NETS + (EXTENDED if extended else ()) + (R10_PORT_NETS if profile == 'r10' else ())
    fb, fc = fills(base, refs), fills(cand, refs)
    rep = {'nets': list(nets), 'layers': {pcbnew.LayerName(k): [pcbnew.LayerName(v[0]), list(v[1])]
                                          for k, v in refs.items()}}
    # R6 method: the base's tracks, referenced on the base, lose it on the candidate
    base_s = samples(base, nets, refs, dy)
    ref_base = [s for s in base_s if inside(fb[s[1]], s[2], s[3] - dy)]
    lost = [s for s in ref_base if not inside(fc[s[1]], s[2], s[3])]
    rep['base_samples'] = len(base_s)
    rep['base_referenced_samples'] = len(ref_base)
    rep['lost_on_candidate'] = len(lost)
    rep['lost_by_net_layer'] = _group(lost)
    # the candidate's own tracks: unreferenced where the base was referenced at the same place
    cand_s = samples(cand, nets, refs)
    unref = [s for s in cand_s if not inside(fc[s[1]], s[2], s[3])]
    new = [s for s in unref if inside(fb[s[1]], s[2], s[3] - dy)]
    rep['candidate_samples'] = len(cand_s)
    rep['candidate_unreferenced'] = len(unref)
    rep['candidate_new_losses'] = len(new)
    rep['candidate_new_losses_by_net_layer'] = _group(new)
    return rep


def _group(items):
    g = defaultdict(list)
    for net, layer, x, y in items:
        g[f'{net} {pcbnew.LayerName(layer)}'].append((x, y))
    out = {}
    for k, pts in sorted(g.items()):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        out[k] = {'samples': len(pts), 'box': [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('base')
    ap.add_argument('candidate')
    ap.add_argument('--dy', type=float, default=0.0, help='move the base by this much in y (R6 -> R7: 18)')
    ap.add_argument('--extended', action='store_true')
    ap.add_argument('--json')
    ap.add_argument('--profile', choices=('r9', 'r10'), default='r9')
    a = ap.parse_args()
    rep = compare(pcbnew.LoadBoard(a.base), pcbnew.LoadBoard(a.candidate), a.dy, a.extended, a.profile)
    print(f"base referenced samples {rep['base_referenced_samples']} of {rep['base_samples']}; lost on the candidate "
          f"{rep['lost_on_candidate']}")
    for k, v in rep['lost_by_net_layer'].items():
        print(f'  lost  {k:22s} {v["samples"]:6d}  box {v["box"]}')
    print(f"candidate samples {rep['candidate_samples']}, unreferenced {rep['candidate_unreferenced']}, of which "
          f"referenced on the base at the same place {rep['candidate_new_losses']}")
    for k, v in rep['candidate_new_losses_by_net_layer'].items():
        print(f'  new   {k:22s} {v["samples"]:6d}  box {v["box"]}')
    if a.json:
        with open(a.json, 'w') as f:
            json.dump(rep, f, indent=1)


if __name__ == '__main__':
    main()
