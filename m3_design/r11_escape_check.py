#!/usr/bin/env python3
"""R11 U1 escape plan checker (stage C1b, D-R11-41; stageC1b.md): proves from the pinned escape table
m3_design/r11_fanout.tsv that every used ball of U1 (TFBGA-100) has an exit, that no two exits share a channel slot on
one layer, and that each exit heads to its target's side; with --board it also checks the table against the copper.

usage: <python3> -I -B m3_design/r11_escape_check.py [--board m3_design/r11/m3.kicad_pcb] [--json OUT]
       (the table-only checks need no KiCad; --board needs KiCad's python, pcbnew)

The field box is U1's courtyard, x 19.38 ... 28.62, y 23.38 ... 32.62 (board mm, x east, y forward). A row's `exit` is
the side of that box its escape crosses (N: y = 23.38, S: y = 32.62, W: x = 19.38, E: x = 28.62), `layer` the copper
layer it crosses on and `slot` the crossing coordinate along the side (x for N / S, y for E / W). Rails (exit P) leave
by their dog-bone via to their plane or bottom capacitor; exit U is a net whose other pads lie under the field (BOOT0's
R5). A row's state is `routed` (its escape copper is on the board) or `open` (no escape copper yet: an open item of
stageC1b.md, listed in the output and the JSON, never counted as an exit). Checks:
  T1  every used ball (pin_table.tsv r11_net, not NC) has exactly one row, with the same net;
  T2  every signal row names its exit, layer and slot, and the exit side faces its target: N when the target lies north
      of the box (y < 23.38), S south, W west, E east (a target beyond a corner may use either side); U only for a
      target inside the box; rails use P with a via;
  T3  channel slots: on one layer and side no two exits are closer than 0.2 mm (one 0.1 mm track and its 0.1 mm
      clearance per slot), so no slot carries two tracks;
  T4  via sites: a dog-bone site is used by one net only, and sites of different nets are >= 0.55 mm apart (the DRU's
      0.25 mm hole-to-hole and copper-to-hole rules on 0.4 / 0.2 mm vias, D-R11-15);
  B1  (--board) each row's via exists on the board on its net, and each target pad exists at (tx, ty) on the row's net;
  B2  (--board) each signal row's net has copper on `layer` crossing its `exit` side within 0.05 mm of `slot`, and every
      crossing of the box by that net's tracks, on any layer, lies on a side that faces one of the net's own pads
      outside the box (the escape heads to its target, no detour out and back).
Exit 0 when every check holds.
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / 'm3_design/r11_fanout.tsv'
PIN_TABLE = ROOT / 'm3_design/r11/design/pin_table.tsv'
BOX = (19.38, 23.38, 28.62, 32.62)          # U1 courtyard (x0, y0, x1, y1)
SIDES = ('N', 'S', 'W', 'E')
LAYERS = ('F', 'In3', 'B')
PITCH = 0.2                                  # one 0.1 mm track + 0.1 mm clearance
VIA_SPACING = 0.55                           # 0.4 / 0.2 vias: 0.25 hole-to-hole and copper-to-hole (D-R11-15)
TOL = 0.05


def read_table(path=TABLE):
    with path.open() as fh:
        return list(csv.DictReader((ln for ln in fh if not ln.startswith('#')), delimiter='\t'))


def used_balls(path=PIN_TABLE):
    out = {}
    with path.open() as fh:
        rows = csv.DictReader((ln for ln in fh if not ln.startswith('#')), delimiter='\t')
        for r in rows:
            ball, net = r.get('r11_ball', '-'), r.get('r11_net', '-')
            if ball and ball != '-' and net and net not in ('NC', '-'):
                out[ball] = net
    return out


def num(v):
    return None if v in (None, '', '-') else float(v)


def facing(tx, ty, box=BOX):
    """The box sides that face the point (tx, ty); empty when it lies inside the box."""
    x0, y0, x1, y1 = box
    out = set()
    if ty < y0:
        out.add('N')
    if ty > y1:
        out.add('S')
    if tx < x0:
        out.add('W')
    if tx > x1:
        out.add('E')
    return out


def table_checks(rows, balls):
    issues = []
    seen = {}
    for r in rows:
        b = r['ball']
        if b in seen:
            issues.append(f'T1 ball {b} listed twice')
        seen[b] = r
        if b not in balls:
            issues.append(f'T1 ball {b} ({r["net"]}) is not a used ball of the pin table')
        elif balls[b] != r['net']:
            issues.append(f'T1 ball {b}: table net {r["net"]}, pin table {balls[b]}')
    for b in sorted(set(balls) - set(seen)):
        issues.append(f'T1 used ball {b} ({balls[b]}) has no escape row')
    slots = {}
    for r in rows:
        b, ex, lay = r['ball'], r['exit'], r['layer']
        if r.get('state') not in ('routed', 'open'):
            issues.append(f'T2 ball {b}: state {r.get("state")!r} is neither routed nor open')
            continue
        if r['state'] == 'open':
            continue
        if ex == 'P':
            if num(r['via_x']) is None:
                issues.append(f'T2 rail ball {b} has no via')
            continue
        if ex == 'U':
            if facing(float(r['tx']), float(r['ty'])):
                issues.append(f'T2 ball {b}: exit U but its target {r["target"]} lies outside the field')
            continue
        if ex not in SIDES or lay not in LAYERS or num(r['slot']) is None:
            issues.append(f'T2 ball {b}: exit {ex!r} / layer {lay!r} / slot {r["slot"]!r} incomplete')
            continue
        want = facing(float(r['tx']), float(r['ty']))
        if ex not in want:
            issues.append(f'T2 ball {b} ({r["net"]}): exit {ex} does not face its target {r["target"]} '
                          f'({r["tx"]}, {r["ty"]}; sides {sorted(want) or "inside"})')
        slots.setdefault((lay, ex), []).append((float(r['slot']), b))
    for (lay, ex), lst in sorted(slots.items()):
        lst.sort()
        for (s1, b1), (s2, b2) in zip(lst, lst[1:]):
            if s2 - s1 < PITCH - 1e-6:
                issues.append(f'T3 {lay} {ex}: balls {b1} ({s1}) and {b2} ({s2}) share a channel slot '
                              f'({s2 - s1:.3f} mm < {PITCH})')
    sites = {}
    for r in rows:
        x, y = num(r['via_x']), num(r['via_y'])
        if x is None:
            continue
        sites.setdefault((x, y), set()).add(r['net'])
    for s, nets in sites.items():
        if len(nets) > 1:
            issues.append(f'T4 via site {s} used by {sorted(nets)}')
    keys = sorted(sites)
    for i, a in enumerate(keys):
        for c in keys[i + 1:]:
            if sites[a] != sites[c] and math.dist(a, c) < VIA_SPACING - 1e-6:
                issues.append(f'T4 via sites {a} {sorted(sites[a])} and {c} {sorted(sites[c])} are '
                              f'{math.dist(a, c):.3f} mm apart (< {VIA_SPACING})')
    return issues, dict(rows=len(rows), used_balls=len(balls),
                        open=[f"{r['ball']} {r['net']}" for r in rows if r.get('state') == 'open'],
                        exits={f'{k[0]} {k[1]}': len(v) for k, v in sorted(slots.items())})


def crossings(seg, box=BOX):
    """[(side, coordinate)] where the segment crosses the box outline (proper crossings, ends excluded)."""
    (ax, ay), (bx, by) = seg
    x0, y0, x1, y1 = box
    out = []
    for side, horiz, c, lo, hi in (('N', True, y0, x0, x1), ('S', True, y1, x0, x1),
                                    ('W', False, x0, y0, y1), ('E', False, x1, y0, y1)):
        a, b = (ay, by) if horiz else (ax, bx)
        if (a - c) * (b - c) >= 0:
            continue
        t = (c - a) / (b - a)
        u = (ax + t * (bx - ax)) if horiz else (ay + t * (by - ay))
        if lo - 1e-9 <= u <= hi + 1e-9:
            out.append((side, round(u, 4)))
    return out


def board_checks(rows, board_path):
    import pcbnew
    mm = pcbnew.ToMM
    lay_name = {pcbnew.F_Cu: 'F', pcbnew.In3_Cu: 'In3', pcbnew.B_Cu: 'B', pcbnew.In1_Cu: 'In1',
                pcbnew.In2_Cu: 'In2', pcbnew.In4_Cu: 'In4'}
    b = pcbnew.LoadBoard(str(board_path))
    vias, tracks, pads = {}, {}, {}
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            vias.setdefault((round(mm(t.GetPosition().x), 3), round(mm(t.GetPosition().y), 3)), set()).add(n)
        else:
            s, e = t.GetStart(), t.GetEnd()
            tracks.setdefault(n, []).append((lay_name.get(t.GetLayer(), '?'),
                                             ((mm(s.x), mm(s.y)), (mm(e.x), mm(e.y)))))
    for f in b.Footprints():
        for p in f.Pads():
            pads.setdefault(p.GetNetname(), []).append((f'{f.GetReference()}.{p.GetNumber()}',
                                                        (mm(p.GetPosition().x), mm(p.GetPosition().y))))
    issues = []
    cross_ev = {}
    for r in rows:
        bl, net = r['ball'], r['net']
        if r.get('state') == 'open':
            continue
        x, y = num(r['via_x']), num(r['via_y'])
        if x is not None:
            hit = [k for k in vias if math.dist(k, (x, y)) < 0.005]
            if not hit or net not in vias[hit[0]]:
                issues.append(f'B1 ball {bl} ({net}): no via of the net at ({x}, {y})')
        if r['exit'] in ('P',):
            continue
        tgt = [q for ref, q in pads.get(net, []) if ref == r['target']]
        if not any(math.dist(q, (float(r['tx']), float(r['ty']))) <= 0.01 for q in tgt):
            issues.append(f'B1 ball {bl} ({net}): target {r["target"]} not at ({r["tx"]}, {r["ty"]}) on the net')
        if r['exit'] == 'U':
            continue
        found = [(lay, side, u) for lay, seg in tracks.get(net, []) for side, u in crossings(seg)]
        cross_ev[bl] = found
        if not any(lay == r['layer'] and side == r['exit'] and abs(u - float(r['slot'])) <= TOL
                   for lay, side, u in found):
            issues.append(f'B2 ball {bl} ({net}): no {r["layer"]} copper crosses side {r["exit"]} at slot {r["slot"]} '
                          f'(crossings {found})')
        own = set()
        for ref, q in pads.get(net, []):
            if not ref.startswith('U1.'):
                own |= facing(*q)
        for lay, side, u in found:
            if side not in own:
                issues.append(f'B2 ball {bl} ({net}): {lay} copper crosses side {side} at {u}, which faces none of '
                              f'the net\'s pads (sides {sorted(own)})')
    return issues, dict(crossings={k: v for k, v in cross_ev.items()})


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', type=Path)
    ap.add_argument('--json', type=Path)
    a = ap.parse_args()
    rows = read_table()
    issues, ev = table_checks(rows, used_balls())
    if a.board:
        bi, bev = board_checks(rows, a.board)
        issues += bi
        ev.update(bev)
    if a.json:
        a.json.write_text(json.dumps(dict(issues=issues, evidence=ev), indent=1) + '\n')
    print(f'r11_escape_check: {ev["rows"]} rows, {ev["used_balls"]} used balls, exits {ev["exits"]}'
          f'{", board checked" if a.board else ""}: {"OK" if not issues else "FAIL"}; open (no escape copper): '
          f'{len(ev["open"])} {ev["open"]}')
    for i in issues:
        print('  FAIL', i)
    return 1 if issues else 0


if __name__ == '__main__':
    sys.exit(main())
