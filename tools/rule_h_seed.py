#!/usr/bin/env python3
"""Seeded-fault suite for pyro rule H (R9 gate P-4; survey_constraints.md section 9.4 item 2, R4 pass 14's method).

usage: <KiCad python3> -I tools/rule_h_seed.py BOARD.kicad_pcb [--pairs 3] [--json OUT] [--keep DIR]
       exit 0 = every seeded fault is caught by at least one gate component, and the controls behave

Works on scratch copies only (the board, its .kicad_pro and .kicad_dru in a temporary folder; the board is never
written). For each of the board's closest rule-H pad pairs (tools/pyro_probe.py), one part is moved so the pair sits
SEED_GAP (0.95 mm, 0.05 mm inside rule H's 1.0 mm), and kicad-cli DRC runs on these variants:

  seed            the DRU as it is: DRC must report rule H on the pair
  min_lowered     rule H's minimum 1.0 -> 0.9 mm: DRC passes it; check_actuators must fail (minimum, text pin)
  deleted         rule H removed: check_actuators must fail (rule missing)
  moved_first     rule H moved to the top of the file: an earlier, smaller rule governs the pads; check_actuators must
                  fail (whole-file pin)
  narrowed        rule H restricted to In1.Cu: check_actuators must fail (text pin)
  raw_dropped     RAW_ACT removed from rule H: check_actuators must fail (lost nets)
  act_gate_dropped ACT_GATE removed from rule H: check_actuators must fail (lost nets)
  pad_override    the seeded live pad given a 0.30 mm local clearance (the R8 J124.2 / J122 defect): DRC goes silent,
                  check_r9 LC-1 must fail

tools/pyro_probe.py (geometry only) must catch the seed in every variant, and DRC must not report rule H on the pair
before seeding (control). A variant counts as caught when DRC, check_actuators, check_r9 LC-1 or pyro_probe fails on
it; the suite fails when any variant is caught by nothing, or when the DRC-only variant ("seed") is not caught by DRC.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import pcbnew

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'm3_design'))
import check_r8 as C8                                           # noqa: E402
import pyro_probe as PP                                         # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
SEED_GAP = 0.95
RULE_H = 'Pyro H: live pads to sense and gate pads (solder bridge)'


def kicad_cli():
    cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli')
    for c in (cli, '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'):
        if c and Path(c).exists():
            return c
    raise SystemExit('kicad-cli not found; set KICAD_CLI')


def rule_block(dru, name):
    i = dru.find(f'(rule "{name}"')
    if i < 0:
        return None, -1, -1
    depth = 0
    for j in range(i, len(dru)):
        depth += {'(': 1, ')': -1}.get(dru[j], 0)
        if depth == 0:
            return dru[i:j + 1], i, j + 1
    return None, -1, -1


def dru_variants(dru):
    """{variant: DRU text} for the rule-H edits."""
    blk, i, j = rule_block(dru, RULE_H)
    if blk is None:
        raise ValueError('rule H missing from the DRU')
    out = {'seed': dru, 'pad_override': dru}
    out['min_lowered'] = dru[:i] + blk.replace('(min 1.0mm)', '(min 0.9mm)') + dru[j:]
    out['deleted'] = dru[:i] + dru[j:]
    first = dru.find('(rule ')
    out['moved_first'] = dru[:first] + blk + '\n' + (dru[first:i] + dru[j:])[0:]
    out['narrowed'] = dru[:i] + blk.replace('(condition "A.Type', "(condition \"A.Layer == 'In1.Cu' && A.Type", 1) + dru[j:]
    out['raw_dropped'] = dru[:i] + blk.replace(" || A.NetName == 'RAW_ACT'", '') + dru[j:]
    out['act_gate_dropped'] = dru[:i] + blk.replace(" || B.NetName == 'ACT_GATE'", '') + dru[j:]
    for k, v in out.items():
        if k not in ('seed', 'pad_override') and v == dru:
            raise ValueError(f'variant {k} did not change the DRU text (rule H wording changed?)')
    return out


def closest_pairs(board, n):
    """The n closest distinct rule-H pad pairs: [(gap, pad_a, pad_b)] (pad_a the live / midpoint side)."""
    rows = []
    items = C8.net_items(board, lambda x: True)
    pads = [it for it in items if isinstance(it[4], pcbnew.PAD)]
    pred, exempt = PP.RULES['H'][1], PP.RULES['H'][2]
    for a in pads:
        for b in pads:
            if a[2] != b[2] or not pred(a[1], b[1]):
                continue
            oa, ob = PP.owner(a), PP.owner(b)
            if oa == ob and oa in exempt:
                continue
            g = C8.min_gap(a[3], b[3], 3.0)
            if g is not None:
                rows.append((g, a[4], b[4], a[2]))
    rows.sort(key=lambda r: r[0])
    out, seen = [], set()
    for g, pa, pb, lay in rows:
        key = (pa.GetParentFootprint().GetReference(), pa.GetNumber(), pb.GetParentFootprint().GetReference(),
               pb.GetNumber())
        if key in seen:
            continue
        seen.add(key)
        out.append((g, pa, pb, lay))
        if len(out) >= n:
            break
    return out


def pad_id(p):
    return f'{p.GetParentFootprint().GetReference()}.{p.GetNumber()}'


def seed(board, ref_a, num_a, ref_b, num_b, layer, gap=SEED_GAP):
    """Move the part with fewer pads of the pair so the pads' edge gap is `gap` mm; returns (moved ref, offset mm)."""
    fa, fb = board.FindFootprintByReference(ref_a), board.FindFootprintByReference(ref_b)
    pa, pb = fa.FindPadByNumber(num_a), fb.FindPadByNumber(num_b)
    move, fixed, pm, pf = (fb, fa, pb, pa) if len(list(fb.Pads())) <= len(list(fa.Pads())) else (fa, fb, pa, pb)
    for _ in range(40):
        g = C8.min_gap(pm.GetEffectiveShape(layer), pf.GetEffectiveShape(layer), 5.0)
        if g is None:
            raise ValueError('pair out of reach')
        if abs(g - gap) <= 0.003:
            break
        cm, cf = pm.GetPosition(), pf.GetPosition()
        dx, dy = cf.x - cm.x, cf.y - cm.y
        d = math.hypot(dx, dy) or 1.0
        step = MM(g - gap)
        move.SetPosition(pcbnew.VECTOR2I(int(move.GetPosition().x + dx / d * step),
                                         int(move.GetPosition().y + dy / d * step)))
    g = C8.min_gap(pm.GetEffectiveShape(layer), pf.GetEffectiveShape(layer), 5.0)
    return move.GetReference(), g


def drc_reports_h(cli, pcb, ref_a, ref_b):
    out = pcb.with_suffix('.json')
    subprocess.run([cli, 'pcb', 'drc', '--format', 'json', '--severity-all', '--units', 'mm', '-o', str(out), str(pcb)],
                   capture_output=True)
    d = json.loads(out.read_text())
    hits = []
    for v in d['violations']:
        if "rule 'Pyro H" not in v.get('description', ''):
            continue
        refs = [re.search(r' of (\S+) on ', i['description']) for i in v['items']]
        refs = {m.group(1) for m in refs if m}
        if {ref_a, ref_b} <= refs:
            hits.append(v['description'])
    return hits


def actuators_fail(board_text, dru_text):
    import check_actuators as CA
    return CA.check(board_text, dru_text)


def lc1_fail(board):
    import check_r9 as C9
    return C9.lc1(board)[0]


def run(board_path, pairs=3, keep=None):
    board_path = Path(board_path).resolve()
    cli = kicad_cli()
    dru0 = board_path.with_suffix('.kicad_dru').read_text()
    variants = dru_variants(dru0)
    work = Path(keep) if keep else Path(tempfile.mkdtemp(prefix='rule_h_seed_'))
    work.mkdir(parents=True, exist_ok=True)
    import hashlib
    report = dict(board=board_path.name, board_sha256=hashlib.sha256(board_path.read_bytes()).hexdigest(),
                  seed_gap=SEED_GAP, pairs=[])
    try:
        shutil.copy(board_path.with_suffix('.kicad_pro'), work / 'm3.kicad_pro')
        base = pcbnew.LoadBoard(str(board_path))
        targets = closest_pairs(base, pairs)
        if not targets:
            report['error'] = 'no rule-H pad pair on the board'
            return report, ['rule H seed: no rule-H pad pair found']
        issues = []
        base_text = board_path.read_text()
        base_actuators = set(actuators_fail(base_text, dru0))
        base_lc1 = set(lc1_fail(base))
        report['baseline'] = dict(check_actuators=sorted(base_actuators), lc1=sorted(base_lc1))
        for gap0, pa, pb, lay in targets:
            ra, na, rb, nb = pa.GetParentFootprint().GetReference(), pa.GetNumber(), \
                pb.GetParentFootprint().GetReference(), pb.GetNumber()
            row = dict(pair=f'{ra}.{na} -- {rb}.{nb}', layer=base.GetLayerName(lay), gap_before=gap0, variants={})
            # control: the unseeded board must not report rule H on this pair
            (work / 'm3.kicad_dru').write_text(dru0)
            ctrl = work / 'm3.kicad_pcb'
            shutil.copy(board_path, ctrl)
            row['control_drc_hits'] = len(drc_reports_h(cli, ctrl, ra, rb)) if gap0 >= 1.0 else None
            for name, dru in variants.items():
                b = pcbnew.LoadBoard(str(board_path))
                moved, g = seed(b, ra, na, rb, nb, lay)
                if name == 'pad_override':
                    b.FindFootprintByReference(ra).FindPadByNumber(na).SetLocalClearance(MM(0.30))
                pcb = work / 'm3.kicad_pcb'
                b.Save(str(pcb))
                (work / 'm3.kicad_dru').write_text(dru)
                caught = []
                if drc_reports_h(cli, pcb, ra, rb):
                    caught.append('DRC')
                if set(actuators_fail(pcb.read_text(), dru)) - base_actuators:
                    caught.append('check_actuators')
                if set(lc1_fail(b)) - base_lc1:
                    caught.append('check_r9 LC-1')
                probe = PP.probe(b, rules={'H': PP.RULES['H']}, limit_pairs=1000)
                if any(ra in v['a'] + v['b'] and rb in v['a'] + v['b'] for v in probe['H']['violations']):
                    caught.append('pyro_probe')
                row['variants'][name] = dict(moved=moved, seeded_gap=g, caught_by=caught)
                if not caught:
                    issues.append(f'rule H seed {row["pair"]} variant {name}: caught by nothing')
                if 'pyro_probe' not in caught:
                    issues.append(f'rule H seed {row["pair"]} variant {name}: pyro_probe missed the seeded pair')
                if name == 'seed' and 'DRC' not in caught:
                    issues.append(f'rule H seed {row["pair"]}: DRC did not report the seeded pair (rule H not live)')
                if name == 'pad_override' and 'check_r9 LC-1' not in caught:
                    issues.append(f'rule H seed {row["pair"]}: LC-1 missed the seeded pad override')
            if row['control_drc_hits']:
                issues.append(f'rule H seed {row["pair"]}: DRC reports rule H before seeding (control)')
            report['pairs'].append(row)
        return report, issues
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', type=Path)
    ap.add_argument('--pairs', type=int, default=3)
    ap.add_argument('--json', type=Path)
    ap.add_argument('--keep', type=Path, help='keep the scratch folder here')
    a = ap.parse_args()
    report, issues = run(a.board, a.pairs, a.keep)
    for row in report.get('pairs', []):
        print(f"pair {row['pair']} ({row['layer']}, {row['gap_before']:.3f} mm before)")
        for name, v in row['variants'].items():
            print(f"   {name:17s} seeded {v['seeded_gap']:.3f} mm (moved {v['moved']}): caught by "
                  f"{', '.join(v['caught_by']) or 'NOTHING'}")
    for i in issues:
        print('FAIL', i)
    print('rule H seeded-fault suite:', 'OK' if not issues else f'FAIL ({len(issues)})')
    if a.json:
        a.json.write_text(json.dumps(dict(report, issues=issues), indent=1, default=str) + '\n')
    return 0 if not issues else 1


if __name__ == '__main__':
    raise SystemExit(main())
