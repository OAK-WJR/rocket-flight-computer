#!/usr/bin/env python3
"""Geometric pyro spacing probe: m3.kicad_dru's pyro rules A-H and A2 plus R9's strict pad rules, measured on the
saved copper without KiCad's DRC engine (R9 gate P-0; r9_plan.md section 1, LC-1 graft).

usage: <KiCad python3> -I tools/pyro_probe.py BOARD.kicad_pcb [--json OUT]        exit 0 = every rule holds

Why it exists: in KiCad 10 a pad's or footprint's local clearance override replaces the custom rules for every pair
the pad is in, in DRC and in the zone filler alike (R8's 0.3 mm overrides on J124.2 and J122's RAW pads disabled
rules A, E and A2 there; r9_step1_progress.md shows a GND pad's override silencing rule D). This probe reads only
geometry, so an override cannot blind it. Each rule here restates its m3.kicad_dru text (nets, exempt parts, pads
only), checked on the same copper layer as DRC does, between pads, tracks, via rings or barrels and zone fills:

  A   RAW_ACT to gate, sense, COLD and midpoint copper                0.5 mm
  B   bus / igniter / drain to gate copper (Q124's own pads exempt)  0.5 mm
  C   bus / igniter / drain to sense, COLD and midpoint copper        0.3 mm (R173, R131, R132 own pads exempt)
  D   GND to bus / igniter / drain (Q124, C128 own pads exempt)       0.5 mm
  E   RAW_ACT to bus and igniter (the ARM break)                      1.0 mm
  F   bus / igniter / drain to every other live net (Q124 exempt)     0.5 mm
  G   gate copper to every other live net                             0.3 mm, R9 scope (P-1b): gate copper inside
      PYRO_BLOCK, and gate copper outside U1's courtyard (clipped to the outside), Q124's own pads exempt
  A2  RAW_ACT to RAW_ACT_SENSE                                        0.3 mm
  H   exposed live / RAW_ACT pads to sense and gate pads, midpoint pads to gate pads (pads only; Q120-Q122, Q124
      own pads exempt)                                                1.0 mm
R9 strict pad rules (r9_plan.md section 1, from plan C; owner decision 2):
  H+  rule H's pairs                                                   1.2 mm (H + 0.2)
  GS  pyro gate pads to sense, COLD and midpoint pads                  1.2 mm
  AG  actuator-switch gate pads (ACT_GATE, ACT_DRV) to GND pads        1.2 mm (Q120-Q122 own pads exempt)
Distances are edge to edge (bisection on SHAPE.Collide to 0.001 mm, tools/check_r8.min_gap). The report is
deterministic: among pairs at the same distance the closest is the first by its labels.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_r8 as C8                                           # noqa: E402 (net_items, min_gap, courtyard)

mm, MM = pcbnew.ToMM, pcbnew.FromMM
LIVE = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
GATES = ('PYRO1_GATE', 'PYRO1_GATE_N')
SENSE = ('ARM1_SENSE', 'PYRO1_CONT', 'PYRO1_COLD', 'PYRO1_CONT_MID', 'ARM1_SENSE_MID')
ACT_GATES = ('ACT_GATE', 'ACT_DRV')
H_LIVE = LIVE + ('RAW_ACT',)
H_SENSE_GATE = ('ARM1_SENSE', 'PYRO1_CONT', 'RAW_ACT_SENSE') + GATES + ACT_GATES
H_MID = ('PYRO1_CONT_MID', 'ARM1_SENSE_MID', 'RAW_ACT_SENSE_MID')
H_GATE = GATES + ACT_GATES
H_OWN = ('Q124', 'Q120', 'Q121', 'Q122')
GS_SENSE = SENSE + ('RAW_ACT_SENSE', 'RAW_ACT_SENSE_MID')
BLOCK_AREA = 'PYRO_BLOCK'
MCU = 'U1'
STRICT = 1.2


def _real(n):
    return bool(n)          # DRC's B.NetName != '' (KiCad names unconnected pads 'unconnected-(...)': they count)


# name: (minimum mm, predicate on (net of A, net of B), parts whose own A/B pads are exempt, pads only, kind)
RULES = {
    'A': (0.5, lambda a, b: a == 'RAW_ACT' and b in GATES + SENSE, (), False, 'dru'),
    'B': (0.5, lambda a, b: a in LIVE and b in GATES, ('Q124',), False, 'dru'),
    'C': (0.3, lambda a, b: a in LIVE and b in SENSE, ('R173', 'R131', 'R132'), False, 'dru'),
    'D': (0.5, lambda a, b: a == 'GND' and b in LIVE, ('Q124', 'C128'), False, 'dru'),
    'E': (1.0, lambda a, b: a == 'RAW_ACT' and b in ('PYRO1_BUS', 'PYRO1_IGN'), (), False, 'dru'),
    'F': (0.5, lambda a, b: a in LIVE and _real(b) and b not in ('GND',) + SENSE + GATES + LIVE
          and not (a in ('PYRO1_BUS', 'PYRO1_IGN') and b == 'RAW_ACT'), ('Q124',), False, 'dru'),
    'G': (0.3, lambda a, b: a in GATES and _real(b) and b not in ('GND', 'RAW_ACT') + LIVE + GATES, ('Q124',), False,
          'dru'),
    'A2': (0.3, lambda a, b: a == 'RAW_ACT' and b == 'RAW_ACT_SENSE', (), False, 'dru'),
    'H': (1.0, lambda a, b: (a in H_LIVE and b in H_SENSE_GATE) or (a in H_MID and b in H_GATE), H_OWN, True, 'dru'),
    'H+': (STRICT, lambda a, b: (a in H_LIVE and b in H_SENSE_GATE) or (a in H_MID and b in H_GATE), H_OWN, True,
           'strict'),
    'GS': (STRICT, lambda a, b: a in GATES and b in GS_SENSE, (), True, 'strict'),
    'AG': (STRICT, lambda a, b: a in ACT_GATES and b == 'GND', ('Q120', 'Q121', 'Q122'), True, 'strict'),
}
DESCRIPTION = {
    'A': 'RAW_ACT to pyro control', 'B': 'bus, igniter and drain to gate', 'C': 'bus, igniter and drain to sense',
    'D': 'GND to bus, igniter and drain', 'E': 'RAW_ACT to bus and igniter (ARM break)',
    'F': 'bus, igniter and drain to other live nets', 'G': 'gate nets (P-1b scope) to other live nets',
    'A2': 'RAW_ACT to RAW_ACT_SENSE', 'H': 'live pads to sense and gate pads (solder bridge)',
    'H+': 'rule H pairs, strict (H + 0.2 mm)', 'GS': 'pyro gate pads to sense, COLD and midpoint pads (strict)',
    'AG': 'actuator-switch gate pads to GND pads (strict)'}


def owner(it):
    obj = it[4]
    return obj.GetParentFootprint().GetReference() if isinstance(obj, pcbnew.PAD) else None


def _bbox_gap(a, b):
    A, B = a.BBox(), b.BBox()
    dx = max(B.GetLeft() - A.GetRight(), A.GetLeft() - B.GetRight(), 0)
    dy = max(B.GetTop() - A.GetBottom(), A.GetTop() - B.GetBottom(), 0)
    return mm(math.hypot(dx, dy))


def _poly(it):
    """The item's copper on its layer as a SHAPE_POLY_SET."""
    shape = it[3]
    if isinstance(shape, pcbnew.SHAPE_POLY_SET):
        return pcbnew.SHAPE_POLY_SET(shape)
    p = pcbnew.SHAPE_POLY_SET()
    obj = it[4]
    if isinstance(obj, pcbnew.PCB_VIA) or (isinstance(obj, pcbnew.PAD) and not obj.FlashLayer(it[2])):
        c = shape.GetCenter()
        r = shape.GetRadius()
        p.NewOutline()
        for k in range(32):
            a = 2 * math.pi * k / 32
            p.Append(int(c.x + r / math.cos(math.pi / 32) * math.cos(a)), int(c.y + r / math.cos(math.pi / 32) * math.sin(a)))
        return p
    obj.TransformShapeToPolygon(p, it[2], 0, MM(0.001), pcbnew.ERROR_OUTSIDE)
    return p


class Scope:
    """Rule G's R9 scope: PYRO_BLOCK's outline and U1's courtyard (P-1b)."""

    def __init__(self, board):
        self.block = [pcbnew.SHAPE_POLY_SET(z.Outline()) for z in board.Zones()
                      if z.GetIsRuleArea() and z.GetZoneName() == BLOCK_AREA]
        u1 = board.FindFootprintByReference(MCU)
        self.u1 = C8.courtyard(u1) if u1 else None

    def gate_shape(self, it):
        """The part of gate item `it` rule G governs: the whole item when it touches PYRO_BLOCK (the DRU's
        A.intersectsArea), else what lies outside U1's courtyard (None when nothing does)."""
        if any(pcbnew.SHAPE.Collide(area, it[3], 0) for area in self.block):
            return it[3]
        if self.u1 is None:
            return it[3]
        poly = _poly(it)
        poly.BooleanSubtract(self.u1)
        if poly.OutlineCount() == 0 or poly.Area() < 1e3:      # < 0.001 mm^2 left outside the courtyard
            return None
        return poly


def probe(board, rules=None, reach=1.0, limit_pairs=12):
    """{rule: dict(minimum, kind, closest (mm, a, b, layer) or None, margin, violations [(mm, a, b, layer)])}."""
    rules = RULES if rules is None else rules
    nets_needed = set()
    # sorted, and the closest pair below is the smallest (mm, labels): equal distances name the same pair in every
    # run (a set's order follows the per-process string hash; R9P1-INTEGRITY-01)
    names = sorted({str(n) for n in board.GetNetsByName()})
    for name, (mn, pred, _, _, _) in rules.items():
        for a in names:
            for b in names:
                if a != b and pred(a, b):
                    nets_needed.update((a, b))
    items = C8.net_items(board, lambda n: n in nets_needed)
    by = {}
    for it in items:
        by.setdefault((it[1], it[2]), []).append(it)
    scope = Scope(board)
    gate_cache = {}
    out = {}
    for name, (mn, pred, exempt, pads_only, kind) in rules.items():
        best, viol = None, []
        pairs = [(a, b) for a in names for b in names if a != b and pred(a, b)]
        for na, nb in pairs:
            for (net, lay), alist in by.items():
                if net != na:
                    continue
                blist = by.get((nb, lay), [])
                if not blist:
                    continue
                for a in alist:
                    if pads_only and not isinstance(a[4], pcbnew.PAD):
                        continue
                    sa = a[3]
                    if name == 'G':
                        key = id(a[4]), lay
                        if key not in gate_cache:
                            gate_cache[key] = scope.gate_shape(a)
                        sa = gate_cache[key]
                        if sa is None:
                            continue
                    for b in blist:
                        if pads_only and not isinstance(b[4], pcbnew.PAD):
                            continue
                        oa, ob = owner(a), owner(b)
                        if oa and oa == ob and oa in exempt:
                            continue
                        if pads_only and oa and oa == ob and name in ('GS', 'AG'):
                            continue                     # a part's own two pads (its own short is the part fault)
                        if _bbox_gap(sa if isinstance(sa, pcbnew.SHAPE_POLY_SET) else sa, b[3]) > mn + reach:
                            continue
                        g = C8.min_gap(sa, b[3], mn + reach)
                        if g is None:
                            continue
                        row = (g, f'{a[0]} ({na})', f'{b[0]} ({nb})', board.GetLayerName(lay))
                        if best is None or row < best:
                            best = row
                        if g < mn - 1e-3:
                            viol.append(row)
        viol.sort()
        uniq, seen = [], set()
        for v in viol:
            k = tuple(sorted((v[1], v[2]))) + (v[3],)
            if k not in seen:
                seen.add(k)
                uniq.append(v)
        out[name] = dict(minimum=mn, kind=kind, description=DESCRIPTION[name],
                         closest=None if best is None else dict(mm=best[0], a=best[1], b=best[2], layer=best[3]),
                         margin=None if best is None else round(best[0] - mn, 3),
                         violations=[dict(mm=v[0], a=v[1], b=v[2], layer=v[3]) for v in uniq[:limit_pairs]],
                         violation_count=len(uniq))
    return out


def issues_of(result):
    out = []
    for name, r in result.items():
        for v in r['violations']:
            out.append(f"pyro rule {name} ({r['description']}): {v['a']} to {v['b']} on {v['layer']} is {v['mm']:.3f} "
                       f"mm; minimum {r['minimum']} mm")
        if r['violation_count'] > len(r['violations']):
            out.append(f"pyro rule {name}: {r['violation_count'] - len(r['violations'])} more pairs under "
                       f"{r['minimum']} mm")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', type=Path)
    ap.add_argument('--json', type=Path)
    a = ap.parse_args()
    board = pcbnew.LoadBoard(str(a.board.resolve()))
    res = probe(board)
    for name, r in res.items():
        c = r['closest']
        print(f"{name:3s} min {r['minimum']:.1f}  " + (f"closest {c['mm']:.3f} margin {r['margin']:+.3f}  {c['a']} / "
                                                     f"{c['b']} {c['layer']}" if c else 'no pair within reach')
              + (f"  VIOLATIONS {r['violation_count']}" if r['violation_count'] else ''))
    issues = issues_of(res)
    for i in issues:
        print('FAIL', i)
    print('pyro probe:', 'OK' if not issues else f'FAIL ({len(issues)})')
    if a.json:
        a.json.write_text(json.dumps(res, indent=1) + '\n')
    return 0 if not issues else 1


if __name__ == '__main__':
    raise SystemExit(main())
