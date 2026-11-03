#!/usr/bin/env python3
"""The REQUIREMENTS M2 review sweep on a built R8 board: every review category the gate does not hold, measured, so the
R8 deviation list (docs/R8_VALIDATION.md part C) can name each instance or say "swept, none" (fix pass 1,
R8P1-REQUIREMENTS-01; R8_DECISIONS D96). Re-run it after any copper change and update part C from its output.

usage: <KiCad python3> -I m3_design/assembly_review/sources/r8_design/step9/m2_sweep.py [BOARD] [--json OUT]

Categories (M2 "What review checks"; R7's deviation list C3 / C4 / C15 / C24 / C25 and its part F):
  chain_detour      every run of a net WITHOUT a pour (route_check.topology chains: between pads, vias, T nodes and
                    ends) longer than route_check.CHAIN_DETOUR_MAX (1.25) x the octilinear distance of its ends and
                    more than CHAIN_DETOUR_SLACK (0.5 mm) longer: route_check's own poured-net chain test, applied to the
                    nets it does not gate (their net-level detour test is gated instead). Each run is also given to
                    route_check.alt_audit, the gate's redraw search (1-3 segment polylines through RedrawCheck: other
                    nets' copper, keep-outs, holes, the edge; pads and vias stay put): "redraw found" means a DRC-clean
                    redraw that ends the detour exists, "no redraw" that none of its candidates does
  adjacency         every pair of different-net tracks, or track and via, or via and via, on one copper layer, whose
                    edges are closer than 0.2 mm (R7 C15's bar; the board's DRC minimum is 0.15 mm), with rigid R7
                    copper (r8_power_check.rigid_items) marked
  adjacency_pad     every pad against every different-net track or via on one copper layer (each copper layer the
                    pad is flashed on: a through-hole pad's unflashed inner layers are skipped), edges closer than
                    0.2 mm, one row per (pad, foreign net) at its smallest gap (fix pass 2, R8P2-REQUIREMENTS-01 /
                    R8P2-ROUTING-03: pass 1's sweep compared tracks and vias only). Each row is classed: 'own_part'
                    when the foreign net also has a pad on the pad's footprint (a track leaving its own pad beside a
                    neighbour of the same part, or the part's own via beside its other pad), with the footprint's pad
                    pitch (smallest pad-centre spacing); 'fine' = own_part on a part of pitch <= FINE_PITCH (the
                    footprint's geometry, counted, not listed one by one in part C); every other row is listed
  via_step          a track with both ends inside one same-net via's ring, off its centre (a step inside via copper)
  poured_hop        a via-to-via track shorter than 4 mm on a net with a pour (a hop under other copper and back)
  routes            route_check --routes on every net without a pour: copper / octilinear MST ratio and vias against
                    the layer changes the pads need; listed when the ratio is >= 1.25 (with > 0.5 mm excess) or the
                    vias exceed the need (route_check gates ratio 1.6 / 2 mm and need + 2 on every net)
  bumps_all         route_check.bump_audit on the non-critical nets (the gate runs it on the critical ones)
  pad_edge          a track end inside a same-net pad of any size but within 0.03 mm of its edge (route_check's
                    pad_end_offcentre sees only pads up to 2 mm)
  via_fold          a non-GND via two of whose arms, on different layers, leave it within 45 degrees of each other (a
                    run that passes its target on one layer and comes back on the other; R8 pass 1 routing's viaturn)
  short_hop         route_check's short_layer_hop and power_via_no_gnd information instances (listed for part E / C8)
  margin_free       the gate's bump and redraw searches once more at DRC's own threshold (fix pass 3, R8P3-ROUTING-03,
                    R8_DECISIONS D107): RedrawCheck tests every candidate at the rule + 0.01 mm
                    (r7_hygiene.rule_clearance), so a window whose present copper already sits at the DRC minimum
                    fails every candidate that keeps that copper, and chain_detour / bumps_all report nothing there.
                    Here the margin is taken off (rule - 0.0005 mm): route_check.bump_audit on every net and alt_audit
                    on every chain_detour row. A candidate found here is for review, not a defect by itself: one that
                    adds a new pair at the DRC minimum, or is a known false positive, is not a clean redraw. The gate
                    keeps its margin (its own bump search, on the critical nets, is unchanged)
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
import route_check as rc  # noqa: E402
import check_r8  # noqa: E402
import r8_power_check  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
CU = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
ADJ = 0.2
HOP = 4.0
FINE_PITCH = 0.65             # mm: a part's pad pitch at or below this is fine pitch (QFN / LGA / QFP / SOT-563 class)
RIGID_REFS = set(check_r8.STRIP_PARTS) | set(check_r8.CH1_PARTS) | {'J1', 'J122'}   # the rigid R7 parts (D11, D15)
STRIP_GND_Y = 23.25           # mm: GND vias aft of the fence row (y 23.3) are the rigid strip_gnd group (D15)
DRC_EPS = 0.0105              # mm: rule_clearance adds 0.01; less this is just under DRC's own threshold (margin_free)


def r3(v):
    return round(v, 3)


def chain_detours(board, cu):
    _, _, _, chains = rc.topology(board, cu)
    poured = {n for (n, _) in cu.zones}
    rows = []
    for chain, n0, n1 in chains:
        s0 = chain[0][0]
        if s0['net'] in poured or s0['net'] == 'GND':
            continue
        pa, pb = chain[0][1], chain[-1][2]
        dx, dy = abs(mm(pb[0] - pa[0])), abs(mm(pb[1] - pa[1]))
        octile = max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
        L = sum(s['len'] for s, _, _ in chain)
        if L - octile > rc.CHAIN_DETOUR_SLACK and L > rc.CHAIN_DETOUR_MAX * octile:
            rows.append(dict(cat='chain_detour', net=s0['net'], cls=rc.net_class(s0['net']), layer=s0['layer'],
                             x=round(mm(pa[0]), 4), y=round(mm(pa[1]), 4), end=(round(mm(pb[0]), 4), round(mm(pb[1]), 4)),
                             path_mm=r3(L), octile_mm=r3(octile), excess_mm=r3(L - octile), nseg=len(chain)))
    found = {(d['net'], d['layer'], d['x'], d['y']): pts for d, pts in rc.alt_audit(board, rows)}
    for d in rows:
        pts = found.get((d['net'], d['layer'], d['x'], d['y']), 'none')
        d['redraw'] = 'window not found' if pts is None else ('no redraw' if pts == 'none' else pts)
    return sorted(rows, key=lambda d: -d['excess_mm'])


def items(board):
    rigid = {t.m_Uuid.AsString() for t in r8_power_check.rigid_items(board)}
    out = []
    for t in board.GetTracks():
        for lid in CU:
            if t.IsOnLayer(lid):
                kind = 'via' if t.GetClass() == 'PCB_VIA' else 'trk'
                where = (r3(mm(t.GetPosition().x)), r3(mm(t.GetPosition().y))) if kind == 'via' else \
                    ((r3(mm(t.GetStart().x)), r3(mm(t.GetStart().y))), (r3(mm(t.GetEnd().x)), r3(mm(t.GetEnd().y))))
                out.append(dict(t=t, lid=lid, net=t.GetNetname(), kind=kind, where=where,
                                shape=t.GetEffectiveShape(lid), box=t.GetBoundingBox(),
                                rigid=t.m_Uuid.AsString() in rigid))
    return out


def adjacency(board, its):
    M = MM(ADJ)
    by = defaultdict(list)
    for it in its:
        by[it['lid']].append(it)
    rows = []
    for lid, group in by.items():
        group.sort(key=lambda it: it['box'].GetLeft())
        for i, a in enumerate(group):
            for c in group[i + 1:]:
                if c['box'].GetLeft() > a['box'].GetRight() + M:
                    break
                if a['net'] == c['net'] or not a['net'] or not c['net']:
                    continue
                ba, bc = a['box'], c['box']
                if ba.GetBottom() + M < bc.GetTop() or bc.GetBottom() + M < ba.GetTop():
                    continue
                if not a['shape'].Collide(c['shape'], M - 1):
                    continue
                lo, hi = 0, M
                while hi - lo > 500:
                    m = (lo + hi) // 2
                    if a['shape'].Collide(c['shape'], m):
                        hi = m
                    else:
                        lo = m
                rows.append(dict(gap_mm=r3(mm(hi)), layer=board.GetLayerName(lid), nets=sorted((a['net'], c['net'])),
                                 a=(a['net'], a['kind'], a['where']), b=(c['net'], c['kind'], c['where']),
                                 rigid=[a['rigid'], c['rigid']]))
    pairs = {}
    for r in sorted(rows, key=lambda r: r['gap_mm']):
        key = (r['layer'],) + tuple(r['nets'])
        pairs.setdefault(key, r)
    return sorted(pairs.values(), key=lambda r: (r['gap_mm'], r['layer'], r['nets']))


def bisect_gap(a, c, M):
    """Edge gap (nm, to 0.5 um) between two shapes known to collide within M."""
    lo, hi = 0, M
    while hi - lo > 500:
        m = (lo + hi) // 2
        if a.Collide(c, m):
            hi = m
        else:
            lo = m
    return hi


def pad_pitch(f):
    """Smallest centre-to-centre spacing (mm) of a footprint's copper pads (inf for one pad)."""
    cs = [p.GetPosition() for p in f.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
    best = math.inf
    for i, a in enumerate(cs):
        for c in cs[i + 1:]:
            d = math.hypot(a.x - c.x, a.y - c.y)
            if d > 0:
                best = min(best, d)
    return best if best == math.inf else mm(best)


def adjacency_pads(board, its):
    """Pad against different-net track / via on one copper layer, edges < ADJ (the adjacency_pad category)."""
    M = MM(ADJ)
    by = defaultdict(list)
    for it in its:
        by[it['lid']].append(it)
    for group in by.values():
        group.sort(key=lambda it: it['box'].GetLeft())
    lefts = {lid: [it['box'].GetLeft() for it in group] for lid, group in by.items()}
    best = {}
    for f in board.GetFootprints():
        ref = f.GetReference()
        part_nets = {p.GetNetname() for p in f.Pads() if p.GetNetname()}
        pitch = pad_pitch(f)
        for p in f.Pads():
            net = p.GetNetname()
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or not net:
                continue
            for lid in CU:
                if not p.IsOnLayer(lid) or not p.FlashLayer(lid):
                    continue
                shape = p.GetEffectiveShape(lid)
                pb = p.GetBoundingBox()
                group = by.get(lid, [])
                hi_left = pb.GetRight() + M
                for it in group:
                    if it['box'].GetLeft() > hi_left:
                        break
                    if it['box'].GetRight() + M < pb.GetLeft():
                        continue
                    if it['net'] == net or not it['net']:
                        continue
                    ib = it['box']
                    if ib.GetBottom() + M < pb.GetTop() or pb.GetBottom() + M < ib.GetTop():
                        continue
                    if not shape.Collide(it['shape'], M - 1):
                        continue
                    g = r3(mm(bisect_gap(shape, it['shape'], M)))
                    own = it['net'] in part_nets
                    key = (f'{ref}.{p.GetNumber()}', it['net'])
                    row = dict(gap_mm=g, layer=board.GetLayerName(lid), pad=key[0], pad_net=net, net=it['net'],
                               item=(it['kind'], it['where']), cls='own_part' if own else 'foreign_part',
                               pitch_mm=r3(pitch) if pitch != math.inf else None,
                               fine=own and pitch <= FINE_PITCH + 1e-6,
                               bare=bool(p.IsOnLayer(pcbnew.F_Mask) if lid == pcbnew.F_Cu else
                                         p.IsOnLayer(pcbnew.B_Mask) if lid == pcbnew.B_Cu else False),
                               rigid=[ref in RIGID_REFS, it['rigid'] or (it['net'] == 'GND' and it['kind'] == 'via'
                                                                         and it['where'][1] < STRIP_GND_Y)])
                    if key not in best or g < best[key]['gap_mm']:
                        best[key] = row
    return sorted(best.values(), key=lambda r: (r['gap_mm'], r['pad'], r['net']))


def via_steps_and_hops(board, cu):
    poured = {n for (n, _) in cu.zones}
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    steps, hops = [], []
    for t in board.GetTracks():
        if t.GetClass() != 'PCB_TRACK':
            continue
        a, b = t.GetStart(), t.GetEnd()
        at = []
        for v in vias:
            if v.GetNetname() != t.GetNetname():
                continue
            r = v.GetWidth(t.GetLayer()) / 2
            p = v.GetPosition()
            ia = math.hypot(a.x - p.x, a.y - p.y) <= r
            ib = math.hypot(b.x - p.x, b.y - p.y) <= r
            if ia and ib and t.GetLength() > 0:
                steps.append(dict(net=t.GetNetname(), layer=board.GetLayerName(t.GetLayer()),
                                  via=(r3(mm(p.x)), r3(mm(p.y))), len_mm=r3(mm(t.GetLength()))))
            if ia or ib:
                at.append(v)
        if t.GetNetname() in poured and len({id(v) for v in at}) >= 2 and mm(t.GetLength()) < HOP:
            hops.append(dict(net=t.GetNetname(), layer=board.GetLayerName(t.GetLayer()),
                             a=(r3(mm(a.x)), r3(mm(a.y))), b=(r3(mm(b.x)), r3(mm(b.y))), len_mm=r3(mm(t.GetLength()))))
    return steps, hops


def routes(board):
    out = []
    for net, nc in sorted(rc.collect(board).items()):
        if nc.zones:
            continue
        r = rc.net_route(nc)
        if r['pads'] < 2:
            continue
        ratio = r['len'] / r['mst'] if r['mst'] else 0.0
        if (ratio >= rc.CHAIN_DETOUR_MAX and r['len'] - r['mst'] > rc.CHAIN_DETOUR_SLACK) or r['vias'] > r['need']:
            out.append(dict(net=net, cls=rc.net_class(net), pads=r['pads'], len_mm=r3(r['len']), mst_mm=r3(r['mst']),
                            ratio=round(ratio, 2), vias=r['vias'], need=r['need']))
    return out


def pad_edges(board):
    pads = defaultdict(list)
    for f in board.GetFootprints():
        for p in f.Pads():
            pads[p.GetNetname()].append((f, p))
    rows = []
    for t in board.GetTracks():
        if t.GetClass() != 'PCB_TRACK':
            continue
        for e in (t.GetStart(), t.GetEnd()):
            for f, p in pads[t.GetNetname()]:
                if not p.IsOnLayer(t.GetLayer()):
                    continue
                ps = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(ps, t.GetLayer(), 0, MM(0.001), pcbnew.ERROR_INSIDE)
                if not ps.Contains(e):
                    continue
                best = float('inf')
                for k in range(ps.OutlineCount()):
                    ol = ps.Outline(k)
                    for i in range(ol.PointCount()):
                        a, c = ol.CPoint(i), ol.CPoint((i + 1) % ol.PointCount())
                        dx, dy = c.x - a.x, c.y - a.y
                        L2 = dx * dx + dy * dy
                        u = 0 if L2 == 0 else max(0, min(1, ((e.x - a.x) * dx + (e.y - a.y) * dy) / L2))
                        best = min(best, math.hypot(e.x - a.x - u * dx, e.y - a.y - u * dy))
                deeper = any(q is not p and q.GetNumber() == p.GetNumber() and q.IsOnLayer(t.GetLayer()) and
                             q.GetEffectiveShape(t.GetLayer()).Collide(e, -MM(0.03)) for g, q in pads[t.GetNetname()]
                             if g is f)
                if mm(best) < 0.03 and not deeper:
                    rows.append(dict(pad=f'{f.GetReference()}.{p.GetNumber()}', net=t.GetNetname(),
                                     layer=board.GetLayerName(t.GetLayer()), end=(r3(mm(e.x)), r3(mm(e.y))),
                                     depth_mm=r3(mm(best))))
    return rows


def via_folds(board):
    T = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK']
    rows = []
    for v in board.GetTracks():
        if v.GetClass() != 'PCB_VIA' or v.GetNetname() == 'GND':
            continue
        p, r = v.GetPosition(), v.GetWidth(pcbnew.F_Cu) / 2
        arms = []
        for t in T:
            if t.GetNetname() != v.GetNetname():
                continue
            a, e = t.GetStart(), t.GetEnd()
            for near, far in ((a, e), (e, a)):
                if math.hypot(near.x - p.x, near.y - p.y) <= r < math.hypot(far.x - p.x, far.y - p.y):
                    arms.append((board.GetLayerName(t.GetLayer()), (far.x - p.x, far.y - p.y), mm(t.GetLength())))
        for i, (la, ua, La) in enumerate(arms):
            for lb, ub, Lb in arms[i + 1:]:
                if la == lb:
                    continue
                c = (ua[0] * ub[0] + ua[1] * ub[1]) / (math.hypot(*ua) * math.hypot(*ub))
                ang = math.degrees(math.acos(max(-1.0, min(1.0, c))))
                if ang < 46:
                    rows.append(dict(net=v.GetNetname(), cls=rc.net_class(v.GetNetname()),
                                     via=(r3(mm(p.x)), r3(mm(p.y))), arms=(la, r3(La), lb, r3(Lb)),
                                     angle=round(ang, 1), fold_mm=r3(min(La, Lb) * math.cos(math.radians(ang)))))
    return sorted(rows, key=lambda d: -d['fold_mm'])


def margin_free(board, chain_rows):
    """bump_audit (every net) and alt_audit (the chain_detour rows) with RedrawCheck at DRC's threshold (see the module
    docstring): {windows, bumps, redraws}."""
    import r7_hygiene as hy
    orig = hy.rule_clearance
    hy.rule_clearance = lambda a, c, gate_in_block=True: orig(a, c, gate_in_block) - DRC_EPS
    try:
        bumps, searched = rc.bump_audit(board, nets=lambda n: True)
        redraws = [dict(net=d['net'], layer=d['layer'], x=d['x'], y=d['y'], end=d['end'], candidate=pts)
                   for d, pts in rc.alt_audit(board, chain_rows) if pts is not None]
    finally:
        hy.rule_clearance = orig
    return dict(windows=searched, bumps=bumps, redraws=redraws)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--json', type=Path)
    a = ap.parse_args()
    rc.set_profile('r8')
    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(a.board))
    cu = rc.Copper(board)
    out = dict(board_sha256=sha)
    out['chain_detour'] = chain_detours(board, cu)
    its = items(board)
    out['adjacency'] = adjacency(board, its)
    out['adjacency_pad'] = adjacency_pads(board, its)
    out['via_step'], out['poured_hop'] = via_steps_and_hops(board, cu)
    out['routes'] = routes(board)
    bumps, searched = rc.bump_audit(board, nets=lambda n: rc.net_class(n) not in rc.CRITICAL)
    out['bumps_all'] = dict(windows=searched, candidates=bumps)
    out['pad_edge'] = pad_edges(board)
    out['via_fold'] = via_folds(board)
    inst = rc.scan(board)
    out['short_hop'] = [d for d in inst if d['cat'] in ('short_layer_hop', 'power_via_no_gnd')]
    out['margin_free'] = margin_free(board, out['chain_detour'])
    print(f'M2 review sweep on {a.board.name} ({sha[:12]}...)')
    for key in ('chain_detour', 'adjacency', 'adjacency_pad', 'via_step', 'poured_hop', 'routes', 'pad_edge',
                'via_fold', 'short_hop'):
        print(f'{key}: {len(out[key])}')
        for d in out[key]:
            print('   ', json.dumps(d, default=str))
    print(f"bumps_all: {len(bumps)} candidates in {searched} windows")
    for d in bumps:
        print('   ', json.dumps(d, default=str))
    mf = out['margin_free']
    print(f"margin_free: {len(mf['bumps'])} bump candidates in {mf['windows']} windows (every net), "
          f"{len(mf['redraws'])} chain-detour redraws (at DRC's threshold; review each)")
    for d in mf['bumps'] + mf['redraws']:
        print('   ', json.dumps(d, default=str))
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=str) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
