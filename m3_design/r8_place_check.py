#!/usr/bin/env python3
"""R8 build step 4 gate: the frozen placement (r8_plan.md section 3 step 4; R8_DECISIONS D29-D36).

usage: <KiCad python3> -I m3_design/r8_place_check.py [board] [--report OUT.json]      exit 0 = every gate passes

The board is r8_pcb.py's output (placement only: rigid R7 copper, no other track). Gates:
  rigid      the 12 check_r8 digests equal R7's (D15)
  legaliser  r8_legalise.check: courtyards, edges, R5 L10 bottom keep-outs, washers, tie path, routing reservations,
             test-pad and pyro clearances, F10 separation (D29-D31)
  drc        kicad-cli DRC with schematic parity, every severity: no violation and no parity item. Allowed at this
             stage only: unconnected items (nothing is routed), the dangling ends of the rigid copper (its four vias
             whose lanes are routed in step 6, D11 / D15) and the silkscreen classes that r8_post.py (step 8) settles
  f10        check_r8.rf_separation: RF parts >= 5 mm from restricted parts and fast-net copper (D17)
  fit        tools/fit_check.py OK, and no margin below R7's (FIT_R7: the bore margin of every part R7 bound below 1 mm,
             the overall minimum, the worst bottom-part margin, the nearest support clearances on both faces)
  tabs       5 mm long-edge windows by ORDERING's rules; TAB_PLAN's spans must be legal, including one forward of
             y 71.5 on each long edge (the forward-rail dependency, survey_constraints section 4)
  mst        octilinear MST of pad centres over the nets without a planned pour (plan_partial's measure) <= 1850 mm
  contract   check_r8's contract on the placed board (pin map, pulls with R310 at the MCU end, series driving ends,
             TH1-TH3 gone, J1 grouping, CH1 spacing, LS120, C29 distance, camera bypass distances); only its route
             measures wait for copper (C29's direct route, the camera bypass routes), their distances are gated here
  actuators  m3_design/check_actuators.py on the board: every rule holds
  sensors    the IMU / barometer rule areas sit on U4 / U5 exactly as in R7
  reserved   a copy of the board with every r8_keepclear.tsv reservation drawn as copper passes DRC's copper rules
             (clearance, shorts, hole clearances, edge, crossings): the reserved routes fit together and fit the parts
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
import check_r7 as r7  # noqa: E402
import check_r8  # noqa: E402
import fit_check  # noqa: E402
import r8_legalise  # noqa: E402
import shutil  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
MST_LIMIT = 1850.0
POUR_NETS = {'GND', '3V3', '3V3A', 'BAT_IN', 'RAW_ACT', 'CAM_5V', 'ACT_FET_S'}   # plan_partial / b0_check.py measure
# fit_check on R7 (c872a3d3..., this step): bore margins below 1 mm, the overall minimum and the support clearances
FIT_R7 = dict(parts={'J9 mated': 0.0281, 'C84': 0.1066, 'J122 mated': 0.7147, 'J3': 0.8861}, minimum=0.0281,
              bottom_worst=2.3378, bottom_support=4.150, top_support=5.0085)
DRC_DEFERRED = {'silk_over_copper', 'silk_overlap', 'silk_edge_clearance'}   # r8_post.py (step 8)
RIGID_DANGLING = {'via_dangling'}          # only on the rigid copper's open ends, checked by position below
TAB_LEN, TAB_PART, TAB_SOFT, TAB_CONN, TAB_HOLE = 5.0, 1.5, 5.0, 2.0, 1.5
TAB_SOFT_REFS = re.compile(r'^(C\d+|R166|LED2|TH\d|U30|U31)$')   # ORDERING section 3 (+ the RF modules, survey 4)
# D35: five 5 mm tabs (JLC suggests 4-6 above 100 mm): R7's left (63-68) and right aft (8-13) spans, a second right aft
# span, and one forward span on each long edge, which drops R7's forward-rail request (ORDERING section 3)
# fix pass 1 (R8P1-DFM-02, D93): the left forward tab at y 112.5-117.5, GND on all four layers, 8.15 mm from Q121, not
# y 100-105 on the 7.7 A battery band (RAW_ACT pours on three layers 0.5 mm from the edge, Q121 4.41 mm away)
TAB_PLAN = {'left': [(63.0, 68.0), (112.5, 117.5)], 'right': [(8.0, 13.0), (18.0, 23.0), (105.0, 110.0)]}


def rigid_ends(board):
    """Positions of the rigid copper's vias (their lanes are step 6's)."""
    return {(round(mm(t.GetPosition().x), 2), round(mm(t.GetPosition().y), 2))
            for t in board.GetTracks() if t.GetClass() == 'PCB_VIA'}


def drc(board_path, board):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(board_path)], capture_output=True)
        rep = json.loads(out.read_text())
    ends = rigid_ends(board)
    bad, deferred, allowed = [], collections.Counter(), collections.Counter()
    for v in rep['violations']:
        if v['type'] in DRC_DEFERRED:
            deferred[v['type']] += 1
            continue
        if v['type'] in RIGID_DANGLING and all((round(i['pos']['x'], 2), round(i['pos']['y'], 2)) in ends
                                               for i in v['items']):
            allowed['rigid via dangling (step 6 connects it)'] += 1
            continue
        bad.append(f"{v['type']}: " + ' | '.join(i['description'] for i in v['items']))
    for p in rep.get('schematic_parity', []):
        bad.append(f"parity {p['type']}: " + ' | '.join(i['description'] for i in p.get('items', [])))
    return bad, dict(unconnected=len(rep['unconnected_items']), deferred=dict(deferred), allowed=dict(allowed))


RESERVED_RULES = {'clearance', 'shorting_items', 'hole_clearance', 'hole_to_hole', 'copper_edge_clearance',
                  'tracks_crossing', 'solder_mask_bridge', 'items_not_allowed'}


def reserved(board_path):
    """DRC of a copy with the reservations drawn as tracks and vias (0.3 mm drill), zones refilled."""
    import csv
    b = pcbnew.LoadBoard(str(board_path))
    with open(r8_legalise.KEEPCLEAR) as fh:
        rows = list(csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t'))
    for r in rows:
        x0, y0, x1, y1, w = (float(r[k]) for k in ('x0', 'y0', 'x1', 'y1', 'w'))
        net = b.FindNet(r['net'])
        if (x0, y0) == (x1, y1):
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(MM(x0), MM(y0)))
            v.SetWidth(MM(w))
            v.SetDrill(MM(0.3))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNet(net)
            b.Add(v)
        else:
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
            t.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
            t.SetWidth(MM(w))
            t.SetLayer(pcbnew.F_Cu if r['layer'] == 'F' else pcbnew.B_Cu)
            t.SetNet(net)
            b.Add(t)
    for z in b.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / board_path.name
        pcbnew.SaveBoard(str(out), b, True)
        for ext in ('.kicad_pro', '.kicad_dru'):
            shutil.copyfile(board_path.with_suffix(ext), out.with_suffix(ext))
        rep_path = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', str(rep_path), str(out)],
                       capture_output=True)
        rep = json.loads(rep_path.read_text())
    bad = [f"{v['type']}: " + ' | '.join(i['description'] for i in v['items'])
           for v in rep['violations'] if v['type'] in RESERVED_RULES]
    return bad, dict(reservations=len(rows), copper_rules=sorted(RESERVED_RULES))


def octile(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


FAMILY = [('RF', r'^(RADIO|GNSS)'), ('SERVO', r'^SERVO'), ('PYRO', r'^(PYRO|ARM1|RAW_ACT_S)'), ('QSPI', r'^QSPI'),
          ('CAM', r'^CAM'), ('IMU', r'^(SPI1|IMU|I2C|BARO)'), ('USB/SWD', r'^(USB|SW|NRST|CC|VBUS)')]


def mst(board):
    nets = collections.defaultdict(set)
    for f in board.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if n and not n.startswith('unconnected') and n not in POUR_NETS:
                q = p.GetPosition()
                nets[n].add((round(mm(q.x), 2), round(mm(q.y), 2)))
    per = {}
    for n, pts in nets.items():
        pts = list(pts)
        if len(pts) < 2:
            continue
        best = {j: octile(pts[0], pts[j]) for j in range(1, len(pts))}
        total = 0.0
        while best:
            j = min(best, key=best.get)
            total += best.pop(j)
            for k in best:
                best[k] = min(best[k], octile(pts[j], pts[k]))
        per[n] = total
    fam = collections.defaultdict(float)
    for n, v in per.items():
        fam[next((k for k, rx in FAMILY if re.match(rx, n)), 'other')] += v
    return sum(per.values()), per, dict(fam)


def tab_windows(board):
    """Legal 5 mm windows on each long edge (ORDERING section 3 rules, courtyard and pad boxes), as (start, end)."""
    boxes = []
    for f in board.GetFootprints():
        ref = f.GetReference()
        if ref in ('J30', 'J31'):
            continue
        need = TAB_SOFT if TAB_SOFT_REFS.match(ref) else TAB_CONN if ref.startswith('J') else TAB_PART
        boxes.append((ref, r8_legalise._box(check_r8.courtyard(f)), need))
        for p in f.Pads():
            b = p.GetBoundingBox()
            boxes.append((ref, (mm(b.GetLeft()), mm(b.GetTop()), mm(b.GetRight()), mm(b.GetBottom())), need))
    holes = [(c, r) for c, r in r8_legalise.Model.edge_holes_of(board)]
    out = {}
    for edge, x in (('left', 0.0), ('right', r8_legalise.W)):
        ok = []
        y = 0.5
        while y + TAB_LEN <= r8_legalise.L - 0.5 + 1e-9:
            y0, y1 = y, y + TAB_LEN
            good = True
            for ref, b, need in boxes:
                dx = max(b[0] - x, x - b[2], 0)
                dy = max(b[1] - y1, y0 - b[3], 0)
                if math.hypot(dx, dy) < need - 1e-6:
                    good = False
                    break
            if good:
                for (cx, cy), r in holes:
                    dx = max(abs(cx - x) - r, 0)
                    dy = max(cy - r - y1, y0 - (cy + r), 0)
                    if math.hypot(dx, dy) < TAB_HOLE - 1e-6:
                        good = False
                        break
            if good:
                ok.append(round(y, 2))
            y = round(y + 0.25, 2)
        spans = []
        for s in ok:
            if spans and s - spans[-1][1] <= 0.26:
                spans[-1][1] = s
            else:
                spans.append([s, s])
        out[edge] = [(a, round(b + TAB_LEN, 2)) for a, b in spans]
    return out


def sensor_areas(board):
    """Offsets of the IMU / BARO rule areas from U4 / U5: must equal R7's (they move with the parts, D29)."""
    issues, ev = [], {}
    want = {'IMU_body_B': ('U4', (36.0, 78.3), (34.4, 76.9)), 'IMU_no_internal_tracks': ('U4', (36.0, 78.3), (35.1, 77.6)),
            'BARO_body_B': ('U5', (36.3, 73.0), (33.8, 70.9)), 'BARO_no_inter_row_tracks': ('U5', (36.3, 73.0), (33.8, 72.2))}
    for z in board.Zones():
        if z.GetZoneName() in want:
            ref, r7_part, r7_corner = want[z.GetZoneName()]
            f = board.FindFootprintByReference(ref)
            bb = z.GetBoundingBox()
            got = (round(mm(bb.GetLeft()) - mm(f.GetPosition().x), 1), round(mm(bb.GetTop()) - mm(f.GetPosition().y), 1))
            exp = (round(r7_corner[0] - r7_part[0], 1), round(r7_corner[1] - r7_part[1], 1))
            ev[z.GetZoneName()] = got
            if got != exp:
                issues.append(f'{z.GetZoneName()} offset {got} from {ref}, R7 {exp}')
    if len(ev) != 4:
        issues.append(f'sensor rule areas: {sorted(ev)}')
    return issues, ev


def fit(board, board_path):
    rep = fit_check.check_board(board, board_path.parent)
    issues = list(rep['issues'])
    margins = {ref: mgn for mgn, ref, _, _ in rep['rows']}
    for ref, r7m in FIT_R7['parts'].items():
        if margins.get(ref, -1) < r7m - 1e-3:
            issues.append(f'fit: {ref} bore margin {margins.get(ref)} mm below R7 {r7m}')
    bottom = min((mgn, ref) for mgn, ref, side, _ in rep['rows'] if side == 'B')
    if bottom[0] < FIT_R7['bottom_worst'] - 1e-3:
        issues.append(f'fit: worst bottom-part bore margin {bottom[0]:.3f} mm ({bottom[1]}) below R7 '
                      f'{FIT_R7["bottom_worst"]} (C74)')
    low = min(margins.values())
    if low < FIT_R7['minimum'] - 1e-3:
        issues.append(f'fit: minimum bore margin {low:.3f} mm below R7 {FIT_R7["minimum"]}')
    if rep['nearest_support'][0] < FIT_R7['bottom_support'] - 1e-3:
        issues.append(f'fit: nearest bottom support clearance {rep["nearest_support"]} below R7 {FIT_R7["bottom_support"]}')
    if rep['nearest_top_support'][0] < FIT_R7['top_support'] - 1e-3:
        issues.append(f'fit: nearest top support clearance {rep["nearest_top_support"]} below R7 {FIT_R7["top_support"]}')
    return issues, dict(minimum=round(low, 3), bottom_worst=(round(bottom[0], 3), bottom[1]), binding=sorted((round(m, 3), r) for r, m in margins.items())[:8],
                        bottom_support=rep['nearest_support'], top_support=rep['nearest_top_support'])


ROUTE_ONLY = re.compile(r'^(C29 requires a direct same-layer route|C100: requires direct local GND return|'
                        r'C(100|93): requires local bypass within 3 mm of U12\.\d+ and direct copper)')


def contract(board, board_path):
    rows = check_r8.load_pin_table()
    issues, _, ev = check_r8.check_contract(board, board_path.parent, rows)
    issues += check_r8.pin_table_issues(rows)
    out = []
    for i in issues:
        if ROUTE_ONLY.match(i):
            m = re.search(r'distance ([\d.]+)', i)
            if m and float(m.group(1)) > 3:
                out.append(i + ' (distance, not only the route)')
            continue
        out.append(i)
    return out, {k: ev[k] for k in ('c29_vcc_pad_distance_mm', 'camera_bypass') if k in ev}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    path = args.board.resolve()
    board = pcbnew.LoadBoard(str(path))
    report, fails = {}, {}

    def gate(name, issues, evidence):
        report[name] = dict(ok=not issues, issues=issues, evidence=evidence)
        fails[name] = len(issues)
    issues, ev = check_r8.rigid(board)
    gate('rigid', issues, {k: v['sha256'][:16] for k, v in ev.items()})
    movable = {f.GetReference() for f in board.GetFootprints()} - set(check_r8.STRIP_PARTS) - set(check_r8.CH1_PARTS) \
        - {'J1', 'J122'}
    leg = r8_legalise.check(board, movable)
    gate('legaliser', [f'{r}: {"; ".join(v)}' for r, v in sorted(leg.items())], dict(parts=len(movable)))
    issues, ev = drc(path, board)
    gate('drc', issues, ev)
    issues, ev = check_r8.rf_separation(board)
    gate('f10', issues, dict(nearest_part=ev['nearest_part'], nearest_line=ev['nearest_line']))
    issues, ev = fit(board, path)
    gate('fit', issues, ev)
    wins = tab_windows(board)
    issues = []
    for edge, spans in TAB_PLAN.items():
        for a, b in spans:
            if not any(s <= a + 1e-6 and b <= e + 1e-6 for s, e in wins[edge]):
                issues.append(f'tab plan {edge} {a}-{b} is not a legal window')
    for edge in ('left', 'right'):
        if not any(e - TAB_LEN >= 71.5 for s, e in wins[edge]):
            issues.append(f'no {edge}-edge window forward of y 71.5')
    gate('tabs', issues, dict(windows=wins, plan=TAB_PLAN))
    total, per, fam = mst(board)
    gate('mst', [] if total <= MST_LIMIT else [f'MST {total:.0f} mm > {MST_LIMIT:.0f}'],
         dict(total_mm=round(total, 1), nets=len(per), by_family={k: round(v) for k, v in sorted(fam.items())},
              longest=sorted(((round(v, 1), n) for n, v in per.items()), reverse=True)[:12]))
    issues, ev = contract(board, path)
    gate('contract', issues, ev)
    act = subprocess.run(['python3', str(ROOT / 'm3_design/check_actuators.py'), str(path)],
                         capture_output=True, text=True)
    gate('actuators', [] if act.returncode == 0 else act.stdout.strip().splitlines(), act.stdout.strip().splitlines()[-1:])
    issues, ev = sensor_areas(board)
    gate('sensors', issues, ev)
    issues, ev = reserved(path)
    gate('reserved', issues, ev)
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name   # no local absolute paths (AGENTS.md)
    report.update(board=str(shown), board_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:20]:
            print('    ', i)
    print('mst', report['mst']['evidence']['total_mm'], 'mm', report['mst']['evidence']['by_family'])
    print('tabs', report['tabs']['evidence']['windows'])
    print('fit', report['fit']['evidence']['minimum'], report['fit']['evidence']['bottom_support'],
          report['fit']['evidence']['top_support'])
    print('f10', report['f10']['evidence'])
    ok = not any(fails.values())
    print('R8 placement gate:', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
