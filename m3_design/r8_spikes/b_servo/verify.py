#!/usr/bin/env python3
"""R8 spike 3(b) verification on the scratch board (KiCad Python).

usage: <KiCad python3> -I verify.py BOARD [--report out.json]

Gate (the brief): DRC 0 and route_check 0 on the spike's nets, rigid copper present with its hashes unchanged.
  - rigid: check_r8.rigid (all 12 D15 groups equal R7's digests);
  - DRC: kicad-cli pcb drc --severity-all; a violation or unconnected item counts when one of its items is spike copper
    (SERVO1-4_MCU / _OUT tracks, vias and pads, D121 and R150-R157 and their pads, the spike's GND / 3V3 vias and
    tracks, the In2 3V3 tongue); the other violations inside the servo region are listed as information;
  - route_check (profile r8): every failing or unrecorded instance on a SERVO net, and every one on GND / 3V3 inside
    the servo region (the spike's vias and pour pockets);
  - D121 / pull-down power pins reach their plane (pcbnew connectivity), since the board's other 3V3 / GND pads are
    unrouted and make unconnected items of their own.
Also measured: route figures, layer lengths, bends, clearances to other nets, D19 (gate vs servo), D20, the tie channel,
check_actuators. Exit 0 when the gate passes.
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(HERE))
import check_r8                    # noqa: E402
import route_check                 # noqa: E402
import servo_route as G            # noqa: E402

MM, mm = pcbnew.FromMM, pcbnew.ToMM
CLI = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
SERVO = re.compile(r'^SERVO[1-4]_(MCU|OUT)$')
PARTS = ('D121',) + tuple(f'R{n}' for n in range(150, 158))
MOVED = ('R177', 'R124', 'R125', 'R182', 'C122')      # the RAW_ACT_SENSE divider, moved out of the way here
REGION = (24.0, 52.0, 38.0, 82.0)                   # servo interface, x0 y0 x1 y1
SPIKE_POWER_VIAS = [G.D121_GND_VIA, G.D121_3V3_VIA] + G.POCKET_GND_VIAS
TIE = ((21.5, 68.6), (27.0, 82.6))                  # fit_check.RETENTION_HOLES; tie path ~4 mm wide (P2, ORDERING)
TIE_HALF = 2.0


def in_region(x, y, box=REGION):
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def seg_dist(p, a, b):
    ax, ay, bx, by = *a, *b
    L2 = (bx - ax) ** 2 + (by - ay) ** 2
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / L2))
    return math.hypot(p[0] - ax - t * (bx - ax), p[1] - ay - t * (by - ay))


def spike_items(b):
    """uuid -> label of every spike item."""
    out = {}
    for t in b.GetTracks():
        p = t.GetPosition() if t.GetClass() == 'PCB_VIA' else t.GetStart()
        xy = (round(mm(p.x), 3), round(mm(p.y), 3))
        if SERVO.match(t.GetNetname()):
            out[t.m_Uuid.AsString()] = f'{t.GetClass()} {t.GetNetname()} {xy}'
        elif t.GetNetname() in ('GND', '3V3') and t.GetClass() == 'PCB_VIA' and \
                any(math.dist(xy, q) < 0.01 for q in SPIKE_POWER_VIAS):
            out[t.m_Uuid.AsString()] = f'via {t.GetNetname()} {xy}'
        elif t.GetNetname() in ('GND', '3V3') and t.GetClass() == 'PCB_TRACK' and \
                any(math.dist(xy, q) < 0.01 for q in (G.D121_GND_VIA, G.D121_3V3_VIA)) or \
                (t.GetClass() == 'PCB_TRACK' and t.GetNetname() in ('GND', '3V3') and in_region(*xy, (33, 72, 36.5, 80))):
            out[t.m_Uuid.AsString()] = f'track {t.GetNetname()} {xy}'
    for f in b.GetFootprints():
        if f.GetReference() in PARTS + MOVED:
            out[f.m_Uuid.AsString()] = f.GetReference()
        for p in f.Pads():
            if f.GetReference() in PARTS + MOVED or SERVO.match(p.GetNetname()):
                out[p.m_Uuid.AsString()] = f'{f.GetReference()}.{p.GetNumber()} {p.GetNetname()}'
    for z in b.Zones():
        if z.GetZoneName() == 'SPIKE_3V3_In2_servo_tongue':
            out[z.m_Uuid.AsString()] = 'zone In2 3V3 tongue'
    return out


def drc(board_path, mine):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', str(out), str(board_path)],
                       check=True, capture_output=True)
        rep = json.loads(out.read_text())
    res = dict(spike=[], spike_silk=[], spike_unconnected=[], spike_power_ratsnest=[], region_other=[], totals=dict(violations=len(rep['violations']),
               unconnected=len(rep['unconnected_items'])))
    for key, lst in (('violations', rep['violations']), ('unconnected_items', rep['unconnected_items'])):
        for v in lst:
            items = v.get('items', [])
            row = dict(type=v['type'], severity=v.get('severity'), description=v.get('description'),
                       items=[(i.get('description'), i.get('pos', {}).get('x'), i.get('pos', {}).get('y'))
                              for i in items])
            hit = [mine[i['uuid']] for i in items if i.get('uuid') in mine]
            if hit and key == 'violations':
                res['spike_silk' if v['type'].startswith('silk') else 'spike'].append(row)
            elif hit and any('SERVO' in h for h in hit):
                res['spike_unconnected'].append(row)
            elif hit:                 # a spike power pin / via as the near end of another unrouted part's ratsnest
                res['spike_power_ratsnest'].append(row)
            elif key == 'violations' and any(in_region(i.get('pos', {}).get('x', -1), i.get('pos', {}).get('y', -1))
                                             for i in items):
                res['region_other'].append(row)
    return res


def plane_reach(b):
    """Each spike power pin / via is joined to a pour of its net (connectivity), and to which pours."""
    b.BuildConnectivity()
    c = b.GetConnectivity()
    out = {}
    pads = [(f'D121.{n}', next(p for p in b.FindFootprintByReference('D121').Pads() if p.GetNumber() == n))
            for n in ('2', '5')]
    pads += [(f'R{153 + i}.2', next(p for p in b.FindFootprintByReference(f'R{153 + i}').Pads() if p.GetNumber() == '2'))
             for i in G.CH]
    vias = [(f'via {t.GetNetname()} {round(mm(t.GetPosition().x), 2), round(mm(t.GetPosition().y), 2)}', t)
            for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and
            any(math.dist((mm(t.GetPosition().x), mm(t.GetPosition().y)), q) < 0.01 for q in SPIKE_POWER_VIAS)]
    for label, item in pads + vias:
        zones = sorted({z.GetZoneName() for z in c.GetConnectedItems(item) if isinstance(z, pcbnew.ZONE)})
        if not zones:     # pad joined through a track / via: follow one more hop
            for o in c.GetConnectedItems(item):
                zones += [z.GetZoneName() for z in c.GetConnectedItems(o) if isinstance(z, pcbnew.ZONE)]
        out[label] = sorted(set(zones))
    return out


def route_figures(b):
    nets = sorted({p.GetNetname() for f in b.GetFootprints() for p in f.Pads() if SERVO.match(p.GetNetname())})
    nc = route_check.collect(b, set(nets))
    out = {}
    for n in nets:
        r = route_check.net_route(nc[n])
        lay = defaultdict(float)
        segs = [t for t in b.GetTracks() if t.GetNetname() == n and t.GetClass() == 'PCB_TRACK']
        for t in segs:
            lay[b.GetLayerName(t.GetLayer())] += mm(t.GetLength())
        heads = defaultdict(set)              # direction changes: count nodes where two segments meet at an angle
        ends = defaultdict(list)
        for t in segs:
            a, c = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
            ang = round(math.degrees(math.atan2(c[1] - a[1], c[0] - a[0])) % 180, 1)
            ends[(t.GetLayer(), a)].append(ang)
            ends[(t.GetLayer(), c)].append(ang)
        bends = sum(1 for k, angs in ends.items() if len(angs) == 2 and angs[0] != angs[1])
        out[n] = dict(pads=r['pads'], len_mm=round(r['len'], 3), octile_mst_mm=round(r['mst'], 3),
                      ratio=round(r['len'] / r['mst'], 3) if r['mst'] else None, vias=r['vias'], vias_needed=r['need'],
                      by_layer={k: round(v, 3) for k, v in sorted(lay.items())}, segments=len(segs), bends=bends)
    return out


def clearances(b, limit=1.0):
    """Nearest other-net copper (pads, tracks, vias; same layer) to each servo net, within `limit` mm."""
    layers = list(b.GetEnabledLayers().CuStack())
    servo = check_r8.net_items(b, lambda n: bool(SERVO.match(n or '')), layers)
    other = [it for it in check_r8.net_items(b, lambda n: bool(n) and not SERVO.match(n), layers)
             if not isinstance(it[4], pcbnew.ZONE)]
    box = pcbnew.BOX2I(pcbnew.VECTOR2I(MM(REGION[0] - 2), MM(REGION[1] - 2)),
                       pcbnew.VECTOR2L(MM(REGION[2] - REGION[0] + 4), MM(REGION[3] - REGION[1] + 4)))
    other = [it for it in other if it[4].GetBoundingBox().Intersects(box)]
    best = {}
    for l1, n1, lay1, s1, _ in servo:
        for l2, n2, lay2, s2, _ in other:
            if lay1 != lay2:
                continue
            g = check_r8.min_gap(s1, s2, limit)
            if g is not None and (n1 not in best or g < best[n1][0]):
                best[n1] = (round(g, 3), f'{l1} to {n2} {l2} on {pcbnew.LayerName(lay1)}')
    pair = {}
    for l1, n1, lay1, s1, _ in servo:          # servo to servo (different nets)
        for l2, n2, lay2, s2, _ in servo:
            if n1 < n2 and lay1 == lay2:
                g = check_r8.min_gap(s1, s2, limit)
                if g is not None and ('min' not in pair or g < pair['min'][0]):
                    pair['min'] = (round(g, 3), f'{n1} {l1} to {n2} {l2} on {pcbnew.LayerName(lay1)}')
    return dict(to_other_nets=best, between_servo_nets=pair.get('min'))


def tie_channel(b):
    out = {}
    for ref in PARTS:
        f = b.FindFootprintByReference(ref)
        if not f.IsFlipped():
            continue
        bb = f.GetCourtyard(pcbnew.B_CrtYd).BBox()
        x0, y0, x1, y1 = mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        d = min(min(seg_dist(c, *TIE) for c in corners),
                min(seg_dist(e, c1, c2) for e in TIE for c1, c2 in zip(corners, corners[1:] + corners[:1])))
        out[ref] = round(d, 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board', type=Path)
    ap.add_argument('--report', type=Path)
    a = ap.parse_args()
    path = a.board.resolve()
    b = pcbnew.LoadBoard(str(path))
    rep = {}
    issues, ev = check_r8.rigid(b)
    rep['rigid'] = dict(issues=issues, groups=ev)
    mine = spike_items(b)
    rep['drc'] = drc(path, mine)
    route_check.set_profile('r8')
    log = []
    inst = route_check.scan(b, log)
    failures, allowed, stale = route_check.evaluate(inst)
    recorded, missing, _ = route_check.leftover_check(inst)

    def ours(d):
        return bool(SERVO.match(d['net'])) or (d['net'] in ('GND', '3V3') and in_region(d['x'], d['y']))
    rep['route_check'] = dict(
        gated=[d for d in failures + missing if ours(d)],
        info=[d for d in inst if ours(d) and d['cat'] in route_check.INFO],
        local_bump_review=route_check.bump_audit(b, nets=lambda n: bool(SERVO.match(n)))[0],
        board_failing=len(failures), board_unrecorded=len(missing))
    rep['plane_reach'] = plane_reach(b)
    rep['routes'] = route_figures(b)
    rep['clearances'] = clearances(b)
    found, ev = check_r8.gate_servo(b, check_r8.close_layer_pairs(str(path)))
    rep['d19_gate_servo'] = dict(issues=found, evidence=ev)
    found, ev = check_r8.inner_signal(b)
    rep['d20_inner_signal'] = dict(issues=[i for i in found if 'SERVO' in i], evidence=ev)
    rep['tie_channel_courtyard_to_centreline_mm'] = tie_channel(b)
    ca = subprocess.run([sys.executable.replace('python3', 'python3'), str(ROOT / 'm3_design/check_actuators.py'),
                         str(path)], capture_output=True, text=True)
    rep['check_actuators'] = dict(rc=ca.returncode, out=(ca.stdout + ca.stderr).strip().splitlines()[-12:])
    unreached = [k for k, z in rep['plane_reach'].items() if not z]
    tie_short = {k: d for k, d in rep['tie_channel_courtyard_to_centreline_mm'].items() if d < TIE_HALF}
    gate = dict(rigid=not issues, drc_spike=not rep['drc']['spike'], drc_spike_unconnected=not rep['drc']['spike_unconnected'],
                route_check_spike=not rep['route_check']['gated'], plane_reach=not unreached,
                d19=not rep['d19_gate_servo']['issues'], d20=not rep['d20_inner_signal']['issues'],
                tie_channel=not tie_short, check_actuators=ca.returncode == 0)
    rep['gate'] = gate
    rep['ok'] = all(gate.values())
    print(json.dumps(dict(gate=gate, rigid_issues=issues, drc_spike=rep['drc']['spike'],
                          drc_spike_unconnected=rep['drc']['spike_unconnected'],
                          drc_totals=rep['drc']['totals'], region_other=len(rep['drc']['region_other']),
                          route_gated=rep['route_check']['gated'], unreached=unreached, tie_short=tie_short,
                          check_actuators=rep['check_actuators']), indent=1, default=str))
    if a.report:
        a.report.write_text(json.dumps(rep, indent=1, default=str) + '\n')
    print('spike 3(b) verify:', 'OK' if rep['ok'] else 'FAIL')
    return 0 if rep['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
