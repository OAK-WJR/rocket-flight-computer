#!/usr/bin/env python3
"""R9 build step 3 gate: the frozen placement (r9_plan.md section 4 step 3; R9_DECISIONS D-S3-*).

usage: <KiCad python3> -I m3_design/r9_place_check.py [board] [--report OUT.json] [--numpy-py PYTHON3]
       exit 0 = every gate passes

The board is r9_pcb.py's output (placement only: no track, via or pour). Gates (each from the R9 contract, never a
weaker copy of it; tools/check_r9.py's rules are called, not restated):
  legaliser  r9_legalise.check over every part: no violation (courtyards, outline, holes, the R9 DRU and strict pad
             rules between pads, M-6 bottom keep-outs, M-5 support and fit floors, R-1, R-10, P-3 pads, P-10, M-4)
  drc        kicad-cli DRC with schematic parity, every severity: no violation and no parity item. Allowed at this stage
             only: unconnected items (nothing is routed) and the silkscreen violations r9_post.py (step 9) settles,
             those with a text among their items (a designator or a board legend). A silkscreen violation between
             footprint graphics and another footprint's graphics, pad or the edge depends on the placement alone and
             fails here (R9_DECISIONS D-S9-01: several library outlines and pin-1 marks reach past their courtyards,
             so the legaliser's courtyard model cannot see them)
  fit        tools/fit_check.py clean and check_r9 M-5 (every category at or above R8's floor or its recorded reason)
  plate      tools/plate_model.py on this board's fit report: f1 (jacks only, pinned, D 5) >= 209 Hz (M-2, hard);
             r9_plan's done row (>= 241 Hz) is reported
  f9         check_r9 F9-1: the input protection <= 10.6 mm and U9 <= 27.07 mm from J1.1
  f10        check_r9 R-10: RF parts >= 5.94 mm from the restricted parts, >= 5.0 mm from fast-net pads
  pyro_pads  tools/pyro_probe.py (rules A-H / A2 and the strict pad rules H+, GS, AG on the pads; copper follows in
             steps 5-7), tools/bridge_table.py (P-5) and check_r9 P-6: no violation
  j1         check_r9 M-4: J1 is C2915641, <= 25 mm from both CH1 terminals, enters +y with its face <= 2.0 mm from the
             forward edge and nothing in front
  tabs       check_r9 T-1: a legal 5 mm tab in the aft and the forward third of each long edge
  mst        octilinear MST of pad centres over the nets without a planned pour (r8_place_check.mst, R8's measure)
             <= 1638.9 mm (r9_plan S17 done row: no worse than R8)
  contract   check_r9's placement-bound rules: LC-1, P-1 (PYRO_BLOCK by content, P-1b), P-2, P-3, P-10, P-11, R-1,
             R-3, R-11, R-12, R-13, M-3, M-6, M-7, K-contract (its two route-only items, C29's direct route and the
             camera bypass routes, wait for copper; their pad distances are gated here) and K-actuators
  actuators  m3_design/check_actuators.py on the board: every rule holds
  areas      the IMU / barometer rule areas and Y1's In2 keep-out keep R8's offsets from U4 / U5 / Y1
"""
import argparse
import collections
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r9 as C9  # noqa: E402
import fit_check  # noqa: E402
import pyro_probe as PP  # noqa: E402
import bridge_table as BT  # noqa: E402
import r8_place_check  # noqa: E402  (mst: R8's S17 measure, unchanged)
import r9_legalise  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
MST_LIMIT = 1638.9                     # r9_plan section 2: S17 <= R8 (1638.9 mm)
F1_DONE = 241.0                        # r9_plan section 2 done row (reported); the hard floor is C9.F1_MIN
DRC_DEFERRED = {'silk_over_copper', 'silk_overlap', 'silk_edge_clearance'}   # r9_post.py (step 9), texts only
CONTRACT_RULES = ('LC-1', 'P-1', 'P-2', 'P-3', 'P-10', 'P-11', 'R-1', 'R-3', 'R-11', 'R-12', 'R-13', 'M-3', 'M-6', 'M-7',
                  'K-contract', 'K-actuators')
ROUTE_ONLY = re.compile(r'^(C29 requires a direct same-layer route|C100: requires direct local GND return|'
                        r'C(100|93): requires local bypass within 3 mm of U12\.\d+ and direct copper)')
# R8's sensor / Y1 rule areas relative to their parts: (part, area bbox top-left - part centre), measured on R8 cc044ea0
AREA_OFFSETS = {'IMU_body_B': 'U4', 'IMU_no_internal_tracks': 'U4', 'BARO_body_B': 'U5',
                'BARO_no_inter_row_tracks': 'U5', 'Y1_In2_keepout': 'Y1'}


TEXT_ITEM = re.compile(r'^(reference field|value field|footprint field|field|pcb text|text|footprint text|user)\b',
                       re.IGNORECASE)          # kicad-cli 10: "Reference field of C1", "PCB text 'ARM' on F.Silkscreen"


def silk_text(v):
    """A silkscreen violation r9_post.py settles: one of its items is a text (a designator, a value or a board legend).
    One made of footprint graphics, pads and the edge alone is the placement's (D-S9-01)."""
    return any(TEXT_ITEM.match(i['description']) for i in v['items'])


def judge_drc(rep):
    """A kicad-cli DRC report (JSON) -> (issues, evidence): every violation fails but the deferred silkscreen ones
    with a text item; every parity item fails."""
    bad, deferred = [], collections.Counter()
    for v in rep['violations']:
        if v['type'] in DRC_DEFERRED and silk_text(v):
            deferred[v['type']] += 1
            continue
        bad.append(f"{v['type']}: " + ' | '.join(i['description'] for i in v['items']))
    for p in rep.get('schematic_parity', []):
        bad.append(f"parity {p['type']}: " + ' | '.join(i['description'] for i in p.get('items', [])))
    return bad, dict(unconnected=len(rep['unconnected_items']), deferred=dict(deferred))


def drc(board_path):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(board_path)], capture_output=True)
        rep = json.loads(out.read_text())
    return judge_drc(rep)


def plate(fit_report, numpy_py):
    with tempfile.TemporaryDirectory() as tmp:
        fp, pp = Path(tmp) / 'fit.json', Path(tmp) / 'plate.json'
        fp.write_text(json.dumps(fit_report, default=str))
        r = subprocess.run([numpy_py, '-I', str(ROOT / 'tools/plate_model.py'), str(fp), '--json', str(pp)],
                           capture_output=True, text=True)
        if r.returncode != 0 or not pp.is_file():
            return None, r.stdout + r.stderr
        return json.loads(pp.read_text()), r.stdout


def areas(board, r8_offsets):
    issues, ev = [], {}
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for z in board.Zones():
        ref = AREA_OFFSETS.get(z.GetZoneName())
        if not ref:
            continue
        bb = z.GetBoundingBox()
        f = fps[ref]
        got = (round(mm(bb.GetLeft()) - mm(f.GetPosition().x), 3), round(mm(bb.GetTop()) - mm(f.GetPosition().y), 3))
        ev[z.GetZoneName()] = got
        want = r8_offsets.get(z.GetZoneName())
        if want is None or any(abs(a - b) > 0.002 for a, b in zip(got, want)):
            issues.append(f'{z.GetZoneName()}: offset {got} from {ref}, R8 {want}')
    if set(ev) != set(AREA_OFFSETS):
        issues.append(f'rule areas present: {sorted(ev)}; required {sorted(AREA_OFFSETS)}')
    return issues, ev


def r8_area_offsets():
    """R8's offsets, measured on R8's committed board (git 9c8179b): the build keeps them by translation."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / 'r8.kicad_pcb'
        p.write_bytes(subprocess.run(['git', '-C', str(ROOT), 'show', '9c8179b:m3_design/assembly_review/m3.kicad_pcb'],
                                     capture_output=True, check=True).stdout)
        b = pcbnew.LoadBoard(str(p))
        fps = {f.GetReference(): f for f in b.GetFootprints()}
        out = {}
        for z in b.Zones():
            ref = AREA_OFFSETS.get(z.GetZoneName())
            if ref:
                bb = z.GetBoundingBox()
                f = fps[ref]
                out[z.GetZoneName()] = (round(mm(bb.GetLeft()) - mm(f.GetPosition().x), 3),
                                        round(mm(bb.GetTop()) - mm(f.GetPosition().y), 3))
        return out, b          # the board is returned so it is not freed before the caller's boards (SWIG, step 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--report', type=Path)
    ap.add_argument('--numpy-py', default='python3', help='a python3 with numpy for tools/plate_model.py')
    args = ap.parse_args()
    path = args.board.resolve()
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    r8_offsets, _keep = r8_area_offsets()
    board = pcbnew.LoadBoard(str(path))
    report, fails = {}, {}

    def gate(name, issues, evidence):
        report[name] = dict(ok=not issues, issues=issues, evidence=evidence)
        fails[name] = len(issues)
    refs = [f.GetReference() for f in board.GetFootprints()]
    leg = r9_legalise.check(board, refs)
    gate('legaliser', [f'{r}: {"; ".join(v)}' for r, v in sorted(leg.items())], dict(parts=len(refs)))
    issues, ev = drc(path)
    gate('drc', issues, ev)
    fit = fit_check.check_board(board, path.parent)
    fit.update(board_sha256=sha)
    ctx = C9.Ctx(board, path.parent, path, fit=fit)
    issues, ev = C9.m5(ctx)
    gate('fit', issues, dict(ev, minimum=round(min(r[0] for r in fit['rows']), 3)))
    pl, out = plate(fit, args.numpy_py)
    if pl is None:
        gate('plate', [f'plate model did not run: {out.strip()[-300:]}'], {})
    else:
        pl['board_sha256'] = sha
        f1 = pl.get('f1', {}).get('jacks_only', {}).get('pinned_D5')
        gate('plate', [] if f1 is not None and f1 >= C9.F1_MIN else [f'f1 {f1} Hz < {C9.F1_MIN} Hz (M-2)'],
             dict(f1_hz=f1, done_241=f1 is not None and f1 >= F1_DONE, supports=pl.get('supports')))
    for name, rid in (('f9', 'F9-1'), ('f10', 'R-10'), ('j1', 'M-4'), ('tabs', 'T-1')):
        r = C9.check_board(board, path.parent, path, fit=fit, only={rid}, board_sha=sha)['rules'][rid]
        gate(name, r['issues'], r['evidence'])
    probe = PP.probe(board)
    issues = PP.issues_of(probe)
    rows = BT.table(board)
    issues += BT.issues_of(rows)
    p6, ev6 = C9.p6(ctx)
    issues += p6
    gate('pyro_pads', issues, dict(margins={k: v['margin'] for k, v in probe.items()},
                                   bridge_pairs=len(rows), p6=ev6))
    total, per, fam = r8_place_check.mst(board)
    gate('mst', [] if total <= MST_LIMIT else [f'MST {total:.1f} mm > {MST_LIMIT} mm (S17)'],
         dict(total_mm=round(total, 1), nets=len(per), by_family={k: round(v) for k, v in sorted(fam.items())}))
    res = C9.check_board(board, path.parent, path, fit=fit, only=set(CONTRACT_RULES), board_sha=sha)
    issues, ev = [], {}
    for rid, r in res['rules'].items():
        ev[rid] = r['evidence']
        for i in r['issues']:
            body = i.split(': ', 1)[1] if i.startswith('K-contract') else i
            if rid == 'K-contract' and ROUTE_ONLY.match(body):
                m = re.search(r'distance ([\d.]+)', body)
                if m and float(m.group(1)) > 3:
                    issues.append(f'{rid}: {i} (distance, not only the route)')
                continue
            issues.append(i if i.startswith(rid) else f'{rid}: {i}')
    gate('contract', issues, ev)
    act = subprocess.run(['python3', str(ROOT / 'm3_design/check_actuators.py'), str(path)], capture_output=True,
                         text=True)
    gate('actuators', [] if act.returncode == 0 else act.stdout.strip().splitlines(), act.stdout.strip().splitlines()[-1:])
    issues, ev = areas(board, r8_offsets)
    gate('areas', issues, ev)
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
    report.update(board=str(shown), board_sha256=sha, checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:25]:
            print('    ', i)
    print('mst', report['mst']['evidence']['total_mm'], 'mm;', 'f1', report.get('plate', {}).get('evidence', {}).get('f1_hz'),
          'Hz;', 'tabs', report['tabs']['evidence'].get('windows'))
    ok = not any(fails.values())
    print('R9 placement gate:', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
