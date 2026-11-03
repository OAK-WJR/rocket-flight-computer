#!/usr/bin/env python3
"""Absolute critical-net reference audit of one board: every unreferenced sample, listed with its cause.

usage: <KiCad python3> tools/reference_audit.py BOARD.kicad_pcb [--extended] [--json OUT] [--list N]

R8 step 9 (r8_plan section 3; survey_constraints section 13 "critical-reference sampling"): tools/critical_reference.py
compares a candidate with a base board (R6 moved +18 mm for R7), which means nothing after a re-placement. This tool
needs no base. It samples the board's own critical tracks exactly as critical_reference.py does (centre line and both
copper edges every 0.01 mm; F.Cu against In1 GND, B.Cu against In2 GND / 3V3 / 3V3A; --extended adds In1 -> F.Cu GND,
In2 -> B.Cu GND and the SWD, NRST and radio SPI nets), so its unreferenced count equals critical_reference.py BOARD BOARD
(candidate_unreferenced; the scorecard's R6b share is that count over the samples), and names the cause of every
unreferenced sample from what lies at that point on the reference layer:
  keepout     inside a rule area that keeps zone fill out of the reference layer (named)
  over_fill   inside another net's fill on the reference layer (named net)
  own_via     within 0.7 mm of a via or plated pad of the track's own net (its own antipad at a layer change; the
              survey's OWN_VIA radius)
  other_via   within 0.5 mm of another net's via or plated pad copper (its antipad)
  track       otherwise, the nearest copper item is another net's track on the reference layer
  fill_gap    otherwise, the nearest copper item is a fill edge: the track crosses or runs along a split or pour edge
  void        no copper item within 1.0 mm (a cut-out)
Consecutive unreferenced samples of one track line with one cause make a run; the runs of a track's three lines with
the same cause are merged into one listed entry (net, layer, cause, causing item, box, samples, centre-line length).
Read-only. Prints the summary and the --list longest entries; --json writes every entry.
"""
import argparse
from collections import Counter, defaultdict
import json
import math
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import critical_reference as CR  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
REACH = 1.0          # mm: a copper item farther than this from an unreferenced sample is not its cause
OWN_VIA = 0.7        # mm from the centre of a same-net via / plated pad (tools/survey_metrics.py OWN_VIA)
ANTIPAD = 0.5        # mm beyond another net's via / plated pad copper
CELL = 1.0           # mm: spatial bucket size


def track_samples(b, nets, refs):
    """Yield (track index, net, layer, line, k, x, y) with critical_reference.samples' arithmetic (line 0 = centre,
    1 = +half width, 2 = -half width)."""
    for ti, t in enumerate(b.GetTracks()):
        if t.GetClass() != 'PCB_TRACK' or t.GetNetname() not in nets or t.GetLayer() not in refs:
            continue
        ax, ay, cx, cy = mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y)
        length = math.hypot(cx - ax, cy - ay)
        if length == 0:
            continue
        ux, uy = (cx - ax) / length, (cy - ay) / length
        hw = mm(t.GetWidth()) / 2
        n = int(math.ceil(length / CR.STEP))
        for k in range(n + 1):
            s = min(length, k * CR.STEP)
            px, py = ax + ux * s, ay + uy * s
            for line, off in enumerate((0.0, hw, -hw)):
                yield ti, t.GetNetname(), t.GetLayer(), line, k, round(px - uy * off, 4), round(py + ux * off, 4)


class Scene:
    """What lies on each reference layer: rule areas, every net's fill, vias, plated pads and tracks, bucketed."""

    def __init__(self, b, layers):
        self.keepouts = defaultdict(list)
        self.fills = defaultdict(list)
        self.items = {lay: defaultdict(list) for lay in layers}
        for z in b.Zones():
            for lay in layers:
                if not z.IsOnLayer(lay):
                    continue
                if z.GetIsRuleArea():
                    if z.GetDoNotAllowZoneFills():
                        self.keepouts[lay].append((z.GetZoneName() or '(unnamed)', z.Outline()))
                elif z.HasFilledPolysForLayer(lay):
                    self.fills[lay].append((z.GetNetname(), z.GetFilledPolysList(lay)))
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_VIA':
                for lay in layers:
                    if t.IsOnLayer(lay):
                        r = max(mm(t.GetWidth(lay)) if t.FlashLayer(lay) else 0.0, mm(t.GetDrillValue())) / 2
                        self._add(lay, ('via', t.GetNetname(), (mm(t.GetPosition().x), mm(t.GetPosition().y)), r))
            elif t.GetClass() == 'PCB_TRACK':
                if t.GetLayer() in self.items:
                    self._add(t.GetLayer(), ('track', t.GetNetname(), (mm(t.GetStart().x), mm(t.GetStart().y),
                                             mm(t.GetEnd().x), mm(t.GetEnd().y)), mm(t.GetWidth()) / 2))
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetAttribute() not in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                    continue
                for lay in layers:
                    if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or p.IsOnLayer(lay):
                        r = max(mm(p.GetDrillSize().x), mm(max(p.GetSize(lay).x, p.GetSize(lay).y))
                                if p.FlashLayer(lay) else 0.0) / 2
                        self._add(lay, ('pad', p.GetNetname() or 'NPTH', (mm(p.GetPosition().x), mm(p.GetPosition().y)),
                                        r, f'{f.GetReference()}.{p.GetNumber()}'))

    def _add(self, lay, item):
        if item[0] == 'track':
            x0, y0, x1, y1 = item[2]
            cells = {(int(math.floor(min(x0, x1) / CELL)) + i, int(math.floor(min(y0, y1) / CELL)) + j)
                     for i in range(int(abs(x1 - x0) / CELL) + 2) for j in range(int(abs(y1 - y0) / CELL) + 2)}
        else:
            x, y = item[2]
            cells = {(int(math.floor(x / CELL)), int(math.floor(y / CELL)))}
        for c in cells:
            self.items[lay][c].append(item)

    def hole(self, lay, x, y, own_net):
        """('own_via' | 'other_via', label) when the point lies in a via's or plated pad's antipad, else None."""
        cx, cy = int(math.floor(x / CELL)), int(math.floor(y / CELL))
        best = None
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for it in self.items[lay].get((cx + i, cy + j), ()):
                    if it[0] == 'track':
                        continue
                    d = math.hypot(x - it[2][0], y - it[2][1])
                    own = it[1] == own_net
                    if (own and d <= OWN_VIA) or (not own and d - it[3] <= ANTIPAD):
                        label = f'{it[1]} {"via" if it[0] == "via" else "pad " + it[4]} ({it[2][0]:.2f}, {it[2][1]:.2f})'
                        rank = (0 if own else 1, d)
                        if best is None or rank < best[0]:
                            best = (rank, 'own_via' if own else 'other_via', label)
        return None if best is None else best[1:]

    def nearest(self, lay, x, y, own_net):
        cx, cy = int(math.floor(x / CELL)), int(math.floor(y / CELL))
        best = None
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for it in self.items[lay].get((cx + i, cy + j), ()):
                    if it[0] == 'track':
                        x0, y0, x1, y1 = it[2]
                        dx, dy = x1 - x0, y1 - y0
                        L2 = dx * dx + dy * dy
                        u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / L2))
                        d = math.hypot(x - x0 - u * dx, y - y0 - u * dy) - it[3]
                        label = f'{it[1]} track'
                    else:
                        d = math.hypot(x - it[2][0], y - it[2][1]) - it[3]
                        label = f'{it[1]} {"via" if it[0] == "via" else "pad " + it[4]} ({it[2][0]:.2f}, {it[2][1]:.2f})'
                    kind = 'track' if it[0] == 'track' else ('own_via' if it[1] == own_net else 'other_via')
                    if best is None or d < best[0]:
                        best = (d, kind, label)
        for net, ps in self.fills.get(lay, ()):
            if ps.Collide(pcbnew.VECTOR2I(MM(x), MM(y)), MM(REACH)):
                lo, hi = 0, MM(REACH)
                while hi - lo > MM(0.005):
                    m = (lo + hi) // 2
                    if ps.Collide(pcbnew.VECTOR2I(MM(x), MM(y)), m):
                        hi = m
                    else:
                        lo = m
                d = mm(hi)
                if best is None or d < best[0]:
                    best = (d, 'fill_gap', f'{net} fill edge')
        return best

    def cause(self, lay, x, y, own_net):
        p = pcbnew.VECTOR2I(MM(x), MM(y))
        for name, outline in self.keepouts.get(lay, ()):
            if outline.Contains(p):
                return 'keepout', name
        for net, ps in self.fills.get(lay, ()):
            if ps.Contains(p, -1, 0, True):
                return 'over_fill', f'{net} fill'
        h = self.hole(lay, x, y, own_net)
        if h:
            return h
        best = self.nearest(lay, x, y, own_net)
        if best is None or best[0] > REACH:
            return 'void', 'no copper within 1 mm'
        return best[1], best[2]


def audit(b, extended=False):
    refs = CR.references(extended)
    nets = CR.R6_NETS + (CR.EXTENDED if extended else ())
    ref_fill = CR.fills(b, refs)
    scene = Scene(b, sorted({v[0] for v in refs.values()}))
    total, per_net = 0, defaultdict(lambda: [0, 0])
    runs = {}                                     # (ti, cause, item) -> entry
    prev = {}                                     # (ti, line) -> (k, cause key)
    by_cause = Counter()
    for ti, net, lay, line, k, x, y in track_samples(b, nets, refs):
        total += 1
        per_net[(net, pcbnew.LayerName(lay))][0] += 1
        if CR.inside(ref_fill[lay], x, y):
            continue
        per_net[(net, pcbnew.LayerName(lay))][1] += 1
        rlay = refs[lay][0]
        kind, item = scene.cause(rlay, x, y, net)
        by_cause[kind] += 1
        key = (ti, kind, item)
        e = runs.setdefault(key, dict(net=net, layer=pcbnew.LayerName(lay), ref_layer=pcbnew.LayerName(rlay),
                                      cause=kind, item=item, samples=0, centre_samples=0, runs=0,
                                      box=[x, y, x, y]))
        e['samples'] += 1
        e['centre_samples'] += line == 0
        e['box'] = [min(e['box'][0], x), min(e['box'][1], y), max(e['box'][2], x), max(e['box'][3], y)]
        last = prev.get((ti, line))
        if last is None or last[0] != k - 1 or last[1] != key:
            e['runs'] += 1
        prev[(ti, line)] = (k, key)
    entries = []
    merged = defaultdict(lambda: dict(samples=0, centre_samples=0, runs=0, tracks=0, box=None))
    for (ti, kind, item), e in runs.items():          # merge the tracks of one net / layer / cause / item
        m = merged[(e['net'], e['layer'], kind, item)]
        m.update(net=e['net'], layer=e['layer'], ref_layer=e['ref_layer'], cause=kind, item=item)
        m['samples'] += e['samples']
        m['centre_samples'] += e['centre_samples']
        m['runs'] += e['runs']
        m['tracks'] += 1
        bx = e['box']
        m['box'] = bx if m['box'] is None else [min(m['box'][0], bx[0]), min(m['box'][1], bx[1]),
                                                 max(m['box'][2], bx[2]), max(m['box'][3], bx[3])]
    for m in merged.values():
        m['centre_mm'] = round(m['centre_samples'] * CR.STEP, 2)
        m['box'] = [round(v, 2) for v in m['box']]
        entries.append(m)
    entries.sort(key=lambda m: (-m['samples'], m['net']))
    unref = sum(v[1] for v in per_net.values())
    return dict(nets=list(nets), samples=total, unreferenced=unref,
                unreferenced_share=round(unref / total, 4) if total else None,
                share_without_own_via=round((unref - by_cause['own_via']) / total, 4) if total else None,
                by_cause=dict(by_cause.most_common()),
                by_net_layer={f'{n} {l}': dict(samples=v[0], unreferenced=v[1]) for (n, l), v in sorted(per_net.items())},
                entries=entries)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board')
    ap.add_argument('--extended', action='store_true')
    ap.add_argument('--json')
    ap.add_argument('--list', type=int, default=40, help='print this many of the largest entries')
    a = ap.parse_args()
    b = pcbnew.LoadBoard(a.board)
    rep = audit(b, a.extended)
    rep['board'] = a.board
    print(f"{'extended' if a.extended else 'R6'} net set: {rep['samples']} samples, {rep['unreferenced']} unreferenced "
          f"({rep['unreferenced_share']:.2%}; {rep['share_without_own_via']:.2%} without the nets' own via antipads)")
    print('  by cause: ' + ', '.join(f'{k} {v}' for k, v in rep['by_cause'].items()))
    for e in rep['entries'][:a.list]:
        print(f"  {e['samples']:6d}  {e['net']:15s} {e['layer']:5s} {e['cause']:9s} {e['item']:38s} centre {e['centre_mm']:5.2f} mm"
              f"  box {e['box']}")
    if len(rep['entries']) > a.list:
        print(f"  ... {len(rep['entries']) - a.list} more entries (--json for all)")
    if a.json:
        with open(a.json, 'w') as f:
            json.dump(rep, f, indent=1)


if __name__ == '__main__':
    main()
