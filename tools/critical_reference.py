#!/usr/bin/env python3
"""Critical-net reference coverage, the R6 acceptance method (docs/M3_R6.md "104,241 critical reference samples";
sources/r6-independent-routing-reference-review-20261013.json "method"), between a base and a candidate board.

usage: <KiCad python3> tools/critical_reference.py BASE.kicad_pcb CANDIDATE.kicad_pcb [--dy 18] [--extended] [--json OUT]

Both boards must carry their saved zone fills. Every track of the critical nets is sampled along its centre line and
both copper edges every 0.01 mm; a sample is referenced when it lies inside the adjacent reference fill:
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

import pcbnew

mm, MM = pcbnew.ToMM, pcbnew.FromMM
R6_NETS = ('USB_DP', 'USB_DM', 'HSE_IN', 'HSE_OUT', 'QSPI_CLK', 'QSPI_NCS', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2',
           'QSPI_IO3', 'SPI1_SCK', 'SPI1_MOSI', 'SPI1_MISO', 'IMU_CS')
EXTENDED = ('SWDIO', 'SWCLK', 'NRST', 'RADIO_NSS', 'RADIO_SCK', 'RADIO_SCK_MCU', 'RADIO_MOSI', 'RADIO_MOSI_MCU',
            'RADIO_MISO', 'RADIO_MISO_MCU')
R10_PORT_NETS = ('CAM_MCU_TX', 'CAM_MCU_RX') + tuple(f'{port}_{signal}_{side}' for port in ('GPS', 'RADIO', 'CAM')
                      for signal in ('TX', 'RX') for side in ('MCU', 'WIRE', 'BUFFER'))
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


def samples(b, nets, refs, dy=0.0):
    """(net, layer, x, y) samples (mm) of the nets' tracks on the reference-mapped layers, moved by dy."""
    out = []
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetNetname() not in nets or t.GetLayer() not in refs:
            continue
        ax, ay, cx, cy = mm(t.GetStart().x), mm(t.GetStart().y) + dy, mm(t.GetEnd().x), mm(t.GetEnd().y) + dy
        length = math.hypot(cx - ax, cy - ay)
        if length == 0:
            continue
        ux, uy = (cx - ax) / length, (cy - ay) / length
        hw = mm(t.GetWidth()) / 2
        n = int(math.ceil(length / STEP))
        for k in range(n + 1):
            s = min(length, k * STEP)
            px, py = ax + ux * s, ay + uy * s
            for off in (0.0, hw, -hw):
                out.append((t.GetNetname(), t.GetLayer(), round(px - uy * off, 4), round(py + ux * off, 4)))
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
