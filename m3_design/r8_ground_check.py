#!/usr/bin/env python3
"""R8 build step 7 gate: the GND stitching (r8_plan.md section 3 step 7; R8_DECISIONS D62-D67).

usage: <KiCad python3> -I m3_design/r8_ground_check.py [board] [--report OUT.json]     exit 0 = every gate passes

The board is r8_ground.py's output: every net routed (step 6) plus the GND copper of m3_design/r8_ground.tsv. Gates:
  rigid     the 12 check_r8 digests equal R7's (D15)
  table     every row of r8_ground.tsv is on the board: a GND via of its size at its point, the C24 track, each trim
            as a fill-only rule area with its layer and outline
  drc       kicad-cli DRC with schematic parity, every severity (pyro rules A-H of m3.kicad_dru included): no violation
            outside the silkscreen classes r8_post.py settles (step 8), no unconnected item (every net whole, GND
            included), no parity item
  route     tools/route_check.py, profile r8: no failure (GND pour fingers, slivers and pad pour cuts included), no
            stale or audited entry, no leftover; the allowlist holds exactly A8 and D51's two limiter entries, so the
            only critical layer change without a GND via within 1.5 mm is A8's (AGENTS 3; scorecard C6 = A8)
  islands   every F.Cu / B.Cu GND pour island holds two or more GND vias or plated GND holes (survey P7), except the
            pockets of WEAK_EXCEPT at no more than their measured area and with their measured via (D63)
  reach     GND via distance (survey P9-P11 definitions, 0.5 mm raster): inside the outer GND pours p95 <= POUR_P95
            and max <= POUR_MAX; over the whole board p95 <= BOARD_P95 and max <= BOARD_MAX, the ceilings the 7.7 A
            pours set (D64)
  power     no step-7 via inside a non-GND F.Cu / B.Cu zone, or inside an In2 RAW_ACT / BAT_IN / ACT_FET_S zone within
            its 7.7 A corridor (tools/run_dc.sh terminals + 2 mm), or within Pyro D (0.5 mm) of any pyro or arming
            net's copper: the stitching cuts no power pour and no 7.7 A path (D62)
  trims     each R8_POUR_TRIM_G* area covers GND fill only, on the board refilled without the trims (D65)
  pyro      check_r8 inner_power_pyro (D18) and gate_servo (D19)
  inner     no In1 or In2 track besides the rigid CH1 block's (D20)
  in2       r8_power_check's In2 gate (D47 islands; no other net's In2 fill under a CH1 pad or a pyro / servo lane)
  contract  tools/check_r8.py on the board: only findings a later step or an open item owns (LATER) and
            check_actuators.py passes; the strip fence (D16), strip GND reach and line stitching pass
  l10       r8_route_check's R5 L10 gate (D61)
  reserved  r8_keepclear.tsv holds no reservation: step 7 builds the last ones (fence row, strip stitches, C24's GND
            stub; D66)
"""
import argparse
import collections
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r8  # noqa: E402
import r8_ground  # noqa: E402
import r8_power_check  # noqa: E402
import r8_place_check  # noqa: E402
import r8_route_check  # noqa: E402
import route_check as rc  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
F, IN1, IN2, B = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
CU4 = (F, IN1, IN2, B)
CLI = r8_place_check.CLI
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
RASTER = 0.5                  # mm (survey_metrics stitching)
POUR_P95, POUR_MAX = 3.5, 7.0
# D64: measured 4.48 / 9.65 mm; floors 4.32 / 9.42 (every legal spot of D62), P10 8.67 (any placement)
BOARD_P95, BOARD_MAX = 4.6, 9.7
# D63: outer GND pour islands allowed fewer than two GND vias: (layer, pad the island holds, measured area mm2, vias)
WEAK_EXCEPT = [('F', 'D4.2', 2.90, 1)]
ALLOWLIST = {('critical_via_no_gnd', 'PYRO1_GATE'), ('detour', 'GNSS_LNA_EN'), ('detour', 'GNSS_VCC_RF')}   # A8, D51
CORRIDORS = {'BAT_IN': [('J1', {'1'}), ('Q120', {'5', '6', '7', '8', '9'})],          # tools/run_dc.sh terminals
             'RAW_ACT': [('Q121', {'5', '6', '7', '8', '9'}), ('J122', {'2', '5', '8', '11'})],
             'ACT_FET_S': [('Q120', {'1', '2', '3'}), ('Q121', {'1', '2', '3'})]}
PYRO = re.compile(r'^(PYRO1_|ARM1_)')
PYRO_D = 0.5
LATER = [
    (r'^J[29]\.\d: silkscreen must identify', 'r8_post (step 8): the J2 / J9 pin legends'),
    (r'^terminal pin legend |^J\d+\.\d+: \d+ legends "', 'r8_post (step 8): the terminal pin legends (D92)'),
    (r'^In2 track of ARM1_SENSE: 3\.4 mm in 1 segments, first at \(14\.55, 94\.15\)',
     'step-4 open item 1 (D15 against D20): the rigid CH1 ARM1_SENSE In2 link, for the orchestrator'),
]


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def r4(v):
    return round(v, 4)


def fill(z, lid):
    f = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid))
    f.Unfracture()
    return f


def table(board, rows):
    issues = []
    vias = {(r4(mm(t.GetPosition().x)), r4(mm(t.GetPosition().y))): t for t in board.GetTracks()
            if t.GetClass() == 'PCB_VIA'}
    tracks = {(r4(mm(t.GetStart().x)), r4(mm(t.GetStart().y)), r4(mm(t.GetEnd().x)), r4(mm(t.GetEnd().y))): t
              for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK'}
    areas = {z.GetZoneName(): z for z in board.Zones() if z.GetIsRuleArea()}
    for r in rows:
        if r['item'] == 'via':
            q = (float(r['x0']), float(r['y0']))
            d, drill = (float(v) for v in r['size'].split('/'))
            v = vias.get(q)
            if v is None or v.GetNetname() != 'GND' or abs(mm(v.GetWidth(F)) - d) > 1e-6 or \
                    abs(mm(v.GetDrillValue()) - drill) > 1e-6:
                issues.append(f'table via {q} ({r["basis"]}) missing or not a {r["size"]} GND via')
        elif r['item'] == 'track':
            t = tracks.get((float(r['x0']), float(r['y0']), float(r['x1']), float(r['y1'])))
            if t is None or t.GetNetname() != 'GND' or board.GetLayerName(t.GetLayer())[0] != r['layer'] or \
                    abs(mm(t.GetWidth()) - float(r['size'])) > 1e-6:
                issues.append(f'table track {r["x0"]},{r["y0"]}-{r["x1"]},{r["y1"]} ({r["basis"]}) missing')
        elif r['item'] == 'trim':
            name = r['basis'].split()[1]
            z = areas.get(name)
            pts = [tuple(float(v) for v in p.split(',')) for p in r['points'].split()]
            if z is None:
                issues.append(f'trim {name} missing')
                continue
            o = z.Outline().Outline(0)
            got = [(r4(mm(o.CPoint(k).x)), r4(mm(o.CPoint(k).y))) for k in range(o.PointCount())]
            if got != pts or [board.GetLayerName(lay)[0] for lay in z.GetLayerSet().CuStack()] != [r['layer']] or \
                    not z.GetDoNotAllowZoneFills() or z.GetDoNotAllowTracks() or z.GetDoNotAllowVias() or \
                    z.GetDoNotAllowPads() or z.GetDoNotAllowFootprints():
                issues.append(f'trim {name}: outline, layer or flags differ from the table')
    return issues, dict(rows=len(rows), vias=sum(1 for r in rows if r['item'] == 'via'),
                        trims=sum(1 for r in rows if r['item'] == 'trim'))


def drc(board_path):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(board_path)], capture_output=True)
        rep = json.loads(out.read_text())
    bad, deferred = [], collections.Counter()
    for v in rep['violations']:
        if v['type'] in r8_place_check.DRC_DEFERRED:
            deferred[v['type']] += 1
        else:
            bad.append(f"{v['type']}: " + ' | '.join(i['description'] for i in v['items']))
    for u in rep['unconnected_items']:
        bad.append('unconnected: ' + ' | '.join(i['description'] for i in u['items']))
    for p in rep.get('schematic_parity', []):
        bad.append(f"parity {p['type']}: " + ' | '.join(i['description'] for i in p.get('items', [])))
    return bad, dict(deferred=dict(deferred), unconnected=len(rep['unconnected_items']))


def route(board_path):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'route.json'
        subprocess.run([sys.executable, '-I', str(ROOT / 'tools/route_check.py'), str(board_path), '--profile', 'r8',
                        '--report', str(out)], capture_output=True)
        rep = json.loads(out.read_text())
    bad = [f"{f['cat']} {f['net']} {f['layer']} ({f['x']}, {f['y']})" for f in rep['failures']]
    for key in ('stale', 'leftovers', 'leftovers_missing', 'nognd_audit', 'leftovers_stale', 'measured_check',
                'alt_audit'):
        bad += [f'route_check {key}: {e}' for e in rep.get(key, [])]
    allowed = {(a['cat'], a['net']) for a in rep['allowed']}
    if allowed != ALLOWLIST:
        bad.append(f'route_check allowlisted {sorted(allowed)}, expected {sorted(ALLOWLIST)}')
    cats = collections.Counter(i['cat'] for i in rep['instances'])
    rule = sum(v for k, v in cats.items() if k in ('off_angle', 'staircase', 'acute_angle', 'fold_back', 'dead_copper',
                                                     'pour_stub', 'dangling_via', 'critical_via_no_gnd', 'pour_sliver',
                                                     'pour_finger', 'pad_pour_cut'))
    return bad, dict(agents3_rule_instances=rule, information={k: v for k, v in cats.items() if k in rc.INFO})


def gnd_points(board):
    pts = [(mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in board.GetTracks()
           if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    pts += [(mm(p.GetPosition().x), mm(p.GetPosition().y)) for f in board.GetFootprints() for p in f.Pads()
            if p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    return pts


def outer_gnd(board):
    out = {}
    for lid in (F, B):
        ps = pcbnew.SHAPE_POLY_SET()
        for z in board.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                ps.BooleanAdd(fill(z, lid))
        out[lid] = ps
    return out


def islands(board):
    """[dict(layer, area mm2, vias: GND vias / plated holes inside, pads: GND pads inside, box)] of the F / B GND pour
    islands (survey P7)."""
    pts = gnd_points(board)
    out = []
    for lid, pours in outer_gnd(board).items():
        for i in range(pours.OutlineCount()):
            one = pcbnew.SHAPE_POLY_SET()
            one.AddOutline(pours.Outline(i))
            for j in range(pours.HoleCount(i)):
                one.AddHole(pours.Hole(i, j))
            n = sum(1 for q in pts if one.Collide(P(*q), MM(0.15)))
            pads = sorted(f'{f.GetReference()}.{p.GetNumber()}' for f in board.GetFootprints() for p in f.Pads()
                          if p.GetNetname() == 'GND' and p.IsOnLayer(lid) and one.Collide(p.GetPosition(), 0))
            bb = one.BBox()
            out.append(dict(layer=board.GetLayerName(lid)[0], area=round(one.Area() / 1e12, 3), vias=n, pads=pads,
                            box=[round(mm(v), 2) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]))
    return out


def island_gate(board):
    found = islands(board)
    issues, allowed = [], []
    for isl in found:
        if isl['vias'] >= 2:
            continue
        ok = [e for e in WEAK_EXCEPT if e[0] == isl['layer'] and e[1] in isl['pads'] and isl['area'] <= e[2] + 1e-6
              and isl['vias'] == e[3]]
        if ok:
            allowed.append(dict(isl, why=ok[0]))
        else:
            issues.append(f"{isl['layer']}.Cu GND island {isl['box']} ({isl['area']} mm2, pads {isl['pads'][:4]}) "
                          f"holds {isl['vias']} GND via(s); two needed (P7)")
    return issues, dict(islands=len(found), weak_allowed=allowed)


class Near:
    def __init__(self, pts, cell=2.0):
        self.cell = cell
        self.bk = collections.defaultdict(list)
        for p in pts:
            self.bk[(int(p[0] // cell), int(p[1] // cell))].append(p)

    def dist(self, q):
        ci, cj = int(q[0] // self.cell), int(q[1] // self.cell)
        best, ring = math.inf, 0
        while ring < 80:
            for di in range(-ring, ring + 1):
                for dj in range(-ring, ring + 1):
                    if max(abs(di), abs(dj)) == ring:
                        for p in self.bk.get((ci + di, cj + dj), ()):
                            best = min(best, math.dist(p, q))
            if best <= ring * self.cell:
                return best
            ring += 1
        return best


def pctl(vals, q):
    s = sorted(vals)
    return s[int(q * (len(s) - 1))] if s else None


def reach(board):
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    bb = outline.BBox()
    pours = outer_gnd(board)
    near = Near(gnd_points(board))
    allpts, pour = [], []
    worst = (0.0, None)
    y = mm(bb.GetTop()) + RASTER / 2
    while y < mm(bb.GetBottom()):
        x = mm(bb.GetLeft()) + RASTER / 2
        while x < mm(bb.GetRight()):
            if outline.Contains(P(x, y)):
                d = near.dist((x, y))
                allpts.append(d)
                if d > worst[0]:
                    worst = (d, (round(x, 2), round(y, 2)))
                if pours[F].Contains(P(x, y)) or pours[B].Contains(P(x, y)):
                    pour.append(d)
            x += RASTER
        y += RASTER
    ev = dict(board_p95=round(pctl(allpts, 0.95), 2), board_max=round(worst[0], 2), board_max_at=worst[1],
              pour_p95=round(pctl(pour, 0.95), 2), pour_max=round(max(pour), 2), pour_points=len(pour))
    issues = []
    for key, lim in (('pour_p95', POUR_P95), ('pour_max', POUR_MAX), ('board_p95', BOARD_P95),
                     ('board_max', BOARD_MAX)):
        if ev[key] > lim + 1e-9:
            issues.append(f'GND via distance {key} {ev[key]} mm over {lim} mm')
    return issues, ev


def corridor_boxes(board):
    out = {}
    for net, ends in CORRIDORS.items():
        xs, ys = [], []
        for ref, pins in ends:
            for p in board.FindFootprintByReference(ref).Pads():
                if p.GetNumber() in pins:
                    xs.append(mm(p.GetPosition().x))
                    ys.append(mm(p.GetPosition().y))
        out[net] = (min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2)
    return out


def power(board, rows):
    """Step-7 vias: none in a non-GND outer zone, in a 7.7 A In2 island inside its corridor, or within Pyro D of pyro
    or arming copper."""
    issues = []
    boxes = corridor_boxes(board)
    zones = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() != 'GND']
    pyro = []
    for t in board.GetTracks():
        if PYRO.match(t.GetNetname()):
            for lid in CU4:
                if t.IsOnLayer(lid):
                    pyro.append(t.GetEffectiveShape(lid))
    for f in board.GetFootprints():
        for p in f.Pads():
            if PYRO.match(p.GetNetname()):
                for lid in CU4:
                    if p.IsOnLayer(lid):
                        pyro.append(p.GetEffectiveShape(lid))
    for z in zones:
        if PYRO.match(z.GetNetname()):
            for lid in CU4:
                if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                    pyro.append(fill(z, lid))
    vias = [r for r in rows if r['item'] == 'via']
    for r in vias:
        q = (float(r['x0']), float(r['y0']))
        rad = float(r['size'].split('/')[0]) / 2
        for z in zones:
            n = z.GetNetname()
            outer = [lid for lid in (F, B) if z.IsOnLayer(lid)]
            if outer and z.Outline().Contains(P(*q)):
                issues.append(f'GND via {q} inside the {n} zone on {board.GetLayerName(outer[0])}')
            if n in boxes and z.IsOnLayer(IN2) and z.Outline().Contains(P(*q)):
                x0, y0, x1, y1 = boxes[n]
                if x0 <= q[0] <= x1 and y0 <= q[1] <= y1:
                    issues.append(f'GND via {q} in the In2 {n} island inside its 7.7 A corridor')
        ring = pcbnew.SHAPE_CIRCLE(P(*q), MM(rad))
        for sh in pyro:
            hit = sh.Collide(P(*q), MM(rad + PYRO_D)) if isinstance(sh, pcbnew.SHAPE_POLY_SET) else \
                sh.Collide(ring, MM(PYRO_D))
            if hit:
                issues.append(f'GND via {q} within {PYRO_D} mm of pyro / arming copper')
                break
    return issues, dict(vias=len(vias), corridors={k: [round(v, 2) for v in b] for k, b in boxes.items()})


def trims(board_path, board):
    """Each step-7 trim covers GND fill only: on the board refilled without the trims, no other net's fill on its layer
    reaches inside its outline."""
    names = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('R8_POUR_TRIM_G')]
    if not names:
        return [], dict(trims=0)
    free = rc.unkept_copy(board)
    issues = []
    for t in names:
        lid = t.GetLayer()
        o = pcbnew.SHAPE_POLY_SET(t.Outline())
        for z in free.Zones():
            if z.GetIsRuleArea() or z.GetNetname() == 'GND' or not z.IsOnLayer(lid) or \
                    not z.HasFilledPolysForLayer(lid):
                continue
            inter = pcbnew.SHAPE_POLY_SET(o)
            inter.BooleanIntersection(fill(z, lid))
            if inter.Area() > 0:
                issues.append(f'{t.GetZoneName()} covers {z.GetNetname()} fill ({inter.Area() / 1e12:.3f} mm2)')
    return issues, dict(trims=len(names))


def contract(board, path):
    rep = check_r8.check_board(board, path.parent, str(path))
    bad, later = [], collections.Counter()
    for i in rep['issues']:
        for pat, owner in LATER:
            if re.search(pat, i):
                later[owner] += 1
                break
        else:
            bad.append(i)
    ev = rep['evidence']
    return bad, dict(later=dict(later), fence=ev.get('fence'), strip_gnd_reach_mm=ev.get('strip_gnd_reach_mm'),
                     rf_stitching=ev.get('rf_stitching'))


def reserved():
    rows = r8_power_check.keepclear_rows()
    return [f'reservation left: {r}' for r in rows], dict(rows=len(rows))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--table', type=Path, default=r8_ground.TABLE)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    path = args.board.resolve()
    board = pcbnew.LoadBoard(str(path))
    rows = r8_ground.read(args.table)
    report, fails = {}, {}

    def gate(name, issues, evidence):
        report[name] = dict(ok=not issues, issues=issues, evidence=evidence)
        fails[name] = len(issues)
    issues, ev = check_r8.rigid(board)
    gate('rigid', issues, {k: v['sha256'][:16] for k, v in ev.items()})
    gate('table', *table(board, rows))
    gate('drc', *drc(path))
    gate('route', *route(path))
    gate('islands', *island_gate(board))
    gate('reach', *reach(board))
    gate('power', *power(board, rows))
    gate('trims', *trims(path, board))
    issues, ev = check_r8.inner_power_pyro(board)
    found, ev2 = check_r8.gate_servo(board, check_r8.close_layer_pairs(str(path)))
    gate('pyro', issues + found, dict(inner_power_pyro=ev, gate_servo=ev2))
    gate('inner', *r8_power_check.inner(board, r8_power_check.rigid_items(board)))
    gate('in2', *r8_power_check.in2(board, []))
    issues, ev = contract(board, path)
    found, ev2 = r8_route_check.actuators(path)
    gate('contract', issues + found, dict(check_r8=ev, check_actuators=ev2))
    gate('l10', *r8_route_check.l10(board))
    gate('reserved', *reserved())
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name   # no local absolute paths (AGENTS.md)
    report.update(board=str(shown), board_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:25]:
            print('    ', i)
    print('reach', report['reach']['evidence'])
    print('islands', report['islands']['evidence'])
    ok = not any(fails.values())
    print('R8 ground gate:', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
