#!/usr/bin/env python3
"""Verify R9 build step 2 (schematic, footprints, design rules) against R8 (commit 9c8179b): r9_plan.md section 4 step 2.

usage: <KiCad python3> -I m3_design/r9_sch_check.py [--project DIR] [--keep DIR] [--json OUT]
exit 0 = every check holds. Read-only on the worktree; all work happens in a temporary directory (--keep DIR keeps
it; --project checks another copy of the project, for seeded-defect tests). The R9 board does not exist yet (build
step 3 places it), so the board-side checks run on a scratch board: R8's board from git with r9_lib's footprint
exchange and override clearing applied, inside a copy of the R9 project.

1. ERC: kicad-cli sch erc, all severities: 0 violations, no ignored checks.
2. Library: r9_lib builds each variant from its base with no finding (same land, same body, same model) and the
   files in kilib equal the generated text.
3. Design rules: m3.kicad_dru is r9_dru.transform(R8's): R8's rules byte for byte but rule G (the P-1b scope only),
   the two LC-1 rules and the zone fill margins of rules A-G / A2 (step 5, D-S5-12); check_actuators' DRU pins (rule
   15) hold on it.
4. Netlist: a fresh export of the R9 sheets equals the committed schematic.net.xml, a fresh export of R8's sheets
   equals R8's committed netlist, and the semantic diff R8 -> R9 is exactly: J121 / J124 / J122's footprint (the
   <footprint> element and the Footprint field) and the sheets' rev; every part, field, value, library part, pin
   function, pin type and pin net identical. It is printed.
5. RF and safety on the R9 netlist (r8_sch_check.rf_safety, check_r7's definitions).
6. BOM: every part's LCSC code identical to R8's; R8's JLC BOM rows (fab/m3_bom_jlc.csv at 9c8179b) reproduce from
   the R9 netlist code by code and designator by designator; R8's supplier check (fab/cost_check.json, bound to that
   BOM by its SHA-256) classes 52 of those codes extended: still 52 <= 52 (REQUIREMENTS M3), no new code.
7. Scratch board (R8's board, SHA-256 checked):
   - parity of R8's board against the R9 schematic is exactly the three decided footprint changes (KiCad's view of
     the diff);
   - r9_lib.apply_variants + clear_overrides: parity 0, no lib_footprint_mismatch, each instance equal to its library
     footprint, no local clearance left (check_r9 LC-1), every pad still on its R8 net;
   - check_actuators in full with R9's DRU: only 15b may fail (the PYRO_BLOCK area against R8's placement: board
     geometry, step 3's); check_r8's pin table, U1 pin map and loader pins hold (R9 keeps R8's pin table);
   - pad roles at the planned orientations (plan_spine 2.1): J121 / J124 at rotation 90 enter from -x with pin 2
     (RAW / IGN) forward of pin 1 (BUS / OUT); J122 at rotation 180 has its SIG row aft and SERVO1-4 west to east;
     the base footprints at those orientations do not (control);
   - DRU liveness (zones unfilled, overrides cleared; a syntax error would drop every custom rule silently): a GATE_N
     track 0.25 mm from 3V3 outside PYRO_BLOCK and U1 (rule G, P-1b), a 3V3 track 0.6 mm from a test pad (test-pad
     rule) and a GND track 0.2 mm from a J122 RAW pin (RAW pin rule) are each reported under their rule, and none of
     them under R8's DRU;
   - fill equivalence: R8's board with its 29 overrides cleared, zones unfilled and refilled under R9's DRU with rule
     G's R8 text and without the fill margins (so only the two LC-1 rules differ from R8's DRU) gives R8's committed
     fills exactly, on every zone and layer: the rules replace the overrides in the filler (rule G's wider P-1b scope
     and the fill margins are separate tightenings);
   - tools/jlc_orient.py on the scratch board: both variants theta 0, status OK, equal to R8's base entries.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'tools'))
import pcbnew                                  # noqa: E402
import check_actuators                         # noqa: E402
import check_r8                                # noqa: E402
import check_r9                                # noqa: E402
import r8_sch_check as r8c                     # noqa: E402 (netlist parse, ERC, RF / safety)
import r9_dru                                  # noqa: E402
import r9_lib                                  # noqa: E402
import r9_sch                                  # noqa: E402

R8_COMMIT = '9c8179b'
R8_BOARD_SHA = 'cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7'
PROJECT = HERE / 'assembly_review'
REL = 'm3_design/assembly_review'
CLI = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
KICAD_PY = os.environ.get('KICAD_PY') or sys.executable
MAX_EXTENDED = 52                              # REQUIREMENTS M3 (tools/check_procurement.py)
BOARD_ONLY_ACTUATORS = 'one PYRO_BLOCK rule area'   # check_actuators 15b's message: board geometry (step 3)
PLANNED = {'J121': 90, 'J124': 90, 'J122': 180}      # plan_spine.md 2.1 / r9_plan section 1
MM, mm = pcbnew.FromMM, pcbnew.ToMM


def git(*args, binary=False):
    out = subprocess.run(['git', '-C', str(ROOT), *args], check=True, capture_output=True)
    return out.stdout if binary else out.stdout.decode()


def r8_file(name):
    return git('show', f'{R8_COMMIT}:{REL}/{name}', binary=True)


def drc(board):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(board)], check=True, capture_output=True)
        return json.loads(out.read_text())


# --- 4. netlist ---------------------------------------------------------------------------------------------------
def netlist_diff(r8, r9):
    """Issues and the list of differences R8 -> R9 (each a printable row)."""
    import xml.etree.ElementTree as ET
    issues, rows = [], []
    if set(r8['comps']) != set(r9['comps']):
        issues.append(f"components differ: -{sorted(set(r8['comps']) - set(r9['comps']))} "
                      f"+{sorted(set(r9['comps']) - set(r8['comps']))}")
    decided = {ref: (old, new) for ref, (_s, old, new) in r9_sch.FOOTPRINTS.items()}
    for ref in sorted(set(r8['comps']) & set(r9['comps'])):
        a, b = r8['comps'][ref], r9['comps'][ref]
        if ref in decided:
            old, new = decided[ref]
            want = a.replace(f'<footprint>{old}</footprint>'.encode(), f'<footprint>{new}</footprint>'.encode()) \
                    .replace(f'<field name="Footprint">{old}</field>'.encode(),
                             f'<field name="Footprint">{new}</field>'.encode())
            if a.count(old.encode()) != 2 or b != want:
                issues.append(f'component {ref}: differs beyond its footprint {old} -> {new}')
            else:
                rows.append(f'{ref:<5} footprint  {old} -> {new}  (<footprint> and the Footprint field)')
        elif a != b:
            issues.append(f'component {ref}: fields, footprint or sheet path changed')
    for key in ('libparts', 'libraries'):
        if r8[key] != r9[key]:
            issues.append(f'netlist <{key}> changed')
    d8 = ET.tostring(r8['root'].find('design')).replace(f'<rev>{r9_sch.REV_OLD}</rev>'.encode(),
                                                         f'<rev>{r9_sch.REV}</rev>'.encode())
    if d8 != ET.tostring(r9['root'].find('design')):
        issues.append(f'netlist <design> differs beyond rev {r9_sch.REV_OLD} -> {r9_sch.REV}')
    revs = [s.findtext('title_block/rev') for s in r9['root'].findall('design/sheet')]
    if len(revs) != r9_sch.SHEETS or set(revs) != {r9_sch.REV}:
        issues.append(f'sheet revs: {revs}')
    else:
        rows.append(f'{len(revs)} sheets  rev {r9_sch.REV_OLD} -> {r9_sch.REV}')
    if r8['pins'] != r9['pins']:
        diff = sorted(k for k in set(r8['pins']) | set(r9['pins']) if r8['pins'].get(k) != r9['pins'].get(k))
        issues.append(f'pin nets, functions or types changed: {diff[:8]}')
    return issues, rows


# --- 6. BOM -------------------------------------------------------------------------------------------------------
def bom_check(r8, r9):
    import xml.etree.ElementTree as ET
    issues, ev = [], {}

    def codes(n):
        out = {}
        for ref, blob in n['comps'].items():
            c = ET.fromstring(blob)
            f = {x.attrib['name']: x.text for x in c.findall('fields/field')}
            if f.get('LCSC'):
                out[ref] = f['LCSC']
        return out
    c8, c9 = codes(r8), codes(r9)
    if c8 != c9:
        issues.append(f'LCSC codes differ: {sorted(set(c8.items()) ^ set(c9.items()))[:6]}')
    bom = r8_file('fab/m3_bom_jlc.csv')
    rows = list(csv.DictReader(io.StringIO(bom.decode())))
    lines, seen = {}, set()
    for row in rows:
        refs = [r.strip() for r in row['Designator'].split(',')]
        code = row['LCSC Part #']
        for ref in refs:
            if c9.get(ref) != code:
                issues.append(f'R8 BOM row {code}: {ref} has {c9.get(ref)} in the R9 netlist')
            seen.add(ref)
        lines.setdefault(code, set()).update(refs)
    cost = json.loads(r8_file('fab/cost_check.json'))
    bom_sha = hashlib.sha256(bom).hexdigest()
    if cost.get('inputs_sha256', {}).get('m3_bom_jlc.csv') != bom_sha:
        issues.append('R8 cost_check.json is not bound to R8\'s BOM')
    extended = sorted(set(cost.get('extended_codes', [])))
    if not set(extended) <= set(lines):
        issues.append('R8 cost check names codes outside its BOM')
    r9codes = {c9[r] for r in seen}
    new = sorted(r9codes - set(lines))
    if new:
        issues.append(f'codes not in R8\'s BOM: {new}')
    if len(set(extended) & r9codes) > MAX_EXTENDED:
        issues.append(f'{len(set(extended) & r9codes)} extended codes > {MAX_EXTENDED}')
    ev.update(bom_lines=len(lines), bom_parts=len(seen), extended=len(set(extended) & r9codes),
              cost_checked_utc=cost.get('checked_utc'), bom_sha256=bom_sha[:16])
    return issues, ev


# --- 7. scratch board ---------------------------------------------------------------------------------------------
def scratch_project(project, work):
    d = work / 'r9'
    shutil.copytree(project, d, ignore=shutil.ignore_patterns('fab', 'sheets', 'sources', '*.png', '*.svg', '*.json',
                                                              '__pycache__', '*.lck', '*.kicad_prl', 'kilib'))
    (d / 'kilib').symlink_to(project / 'kilib')
    (d / 'm3.kicad_pcb').write_bytes(r8_file('m3.kicad_pcb'))
    sha = hashlib.sha256((d / 'm3.kicad_pcb').read_bytes()).hexdigest()
    assert sha == R8_BOARD_SHA, f'R8 board sha {sha[:16]}'
    return d


def pad_roles(b):
    """Findings on J121 / J124 / J122 turned to PLANNED (in memory), on a board with the variants (or with the bases,
    as a control)."""
    issues = []
    for ref, rot in PLANNED.items():
        b.FindFootprintByReference(ref).SetOrientationDegrees(rot)
    at = {(f.GetReference(), p.GetNumber()): (mm(p.GetPosition().x), mm(p.GetPosition().y), p.GetNetname())
          for f in b.GetFootprints() if f.GetReference() in PLANNED for p in f.Pads()}
    for ref in ('J121', 'J124'):
        f = b.FindFootprintByReference(ref)
        if check_r9.entry_dir(f) != '-x':
            issues.append(f'{ref} at rotation 90 enters from {check_r9.entry_dir(f)}')
        (x1, y1, n1), (x2, y2, n2) = at[(ref, '1')], at[(ref, '2')]
        if not (abs(x1 - x2) < 1e-3 and y2 > y1 + 5.0):
            issues.append(f'{ref}: pin 2 ({n2}) not forward of pin 1 ({n1}) at rotation 90')
    sig = [at[('J122', str(n))] for n in (1, 4, 7, 10)]
    raw = [at[('J122', str(n))] for n in (2, 5, 8, 11)]
    if [s[2] for s in sorted(sig)] != ['SERVO1_OUT', 'SERVO2_OUT', 'SERVO3_OUT', 'SERVO4_OUT']:
        issues.append('J122 at rotation 180: SERVO1-4 not west to east')
    if not all(s[1] < r[1] - 2.0 for s, r in zip(sig, raw)):
        issues.append('J122 at rotation 180: SIG row not aft of the RAW row')
    return issues


def seed_tracks(b):
    """The three DRU liveness seeds; returns the item labels to look for in DRC."""
    def trk(net, a, c, layer):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
        t.SetWidth(MM(0.2))
        t.SetLayer(layer)
        t.SetNet(b.FindNet(net))
        b.Add(t)
    for z in b.Zones():
        z.UnFill()
    # rule G (P-1b): open In1 at (30, 30) on R8's board, outside PYRO_BLOCK and U1's courtyard; 0.25 mm edge to edge
    trk('PYRO1_GATE_N', (30.0, 30.0), (33.0, 30.0), pcbnew.In1_Cu)
    trk('3V3', (30.0, 30.45), (33.0, 30.45), pcbnew.In1_Cu)
    tp = next(iter(b.FindFootprintByReference('TP74').Pads()))           # TP74 (GND, bottom): a 3V3 track 0.6 mm away
    c, r = tp.GetPosition(), mm(tp.GetSize(pcbnew.B_Cu).x) / 2
    x = mm(c.x) + r + 0.6 + 0.1
    trk('3V3', (x, mm(c.y) - 0.3), (x, mm(c.y) + 0.3), pcbnew.B_Cu)
    p2 = next(p for p in b.FindFootprintByReference('J122').Pads() if p.GetNumber() == '2')   # GND 0.2 mm from J122.2
    c2, r2 = p2.GetPosition(), mm(p2.GetSize(pcbnew.F_Cu).x) / 2
    y = mm(c2.y) + r2 + 0.2 + 0.1
    trk('GND', (mm(c2.x) - 0.3, y), (mm(c2.x) + 0.3, y), pcbnew.In1_Cu)
    return {'Pyro G: gate nets in the pyro block': 'PYRO1_GATE_N', 'R9 bare test pads to foreign copper': 'TP74',
            'R9 RAW_ACT pins to foreign copper': 'J122'}


def liveness(d, dru_text):
    """{rule name: [violation items]} of a DRC run on the seeded board s.kicad_pcb under the given rules."""
    (d / 's.kicad_dru').write_text(dru_text)
    rep = drc(d / 's.kicad_pcb')
    hits = {}
    for v in rep['violations']:
        m = re.search(r"rule '([^']+)'", v['description'])
        if m:
            hits.setdefault(m.group(1), []).append(' | '.join(i['description'] for i in v['items']))
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--project', type=Path, default=PROJECT, help='project folder (default: the worktree\'s)')
    ap.add_argument('--keep', type=Path, help='work in this (new) directory and keep it')
    ap.add_argument('--json', type=Path, help='write the findings and evidence here')
    args = ap.parse_args()
    project = args.project.resolve()
    if args.keep:
        args.keep.mkdir(parents=True)
        work = args.keep.resolve()
    else:
        tmp = tempfile.TemporaryDirectory(prefix='r9_sch_check_')
        work = Path(tmp.name)
    failures, evidence = [], {}

    def report(name, issues, detail=''):
        print(f"{'OK  ' if not issues else 'FAIL'} {name}{': ' + detail if detail else ''}")
        for i in issues:
            print('     -', i)
        failures.extend(f'{name}: {i}' for i in issues)
        evidence[name] = dict(issues=list(issues), detail=detail)

    # 1. ERC
    violations, ignored, severities = r8c.erc(project)
    report('ERC', [f"{v['type']}: {v['description']}" for v in violations] +
           ([f'ignored checks {ignored}'] if ignored else []) +
           ([] if {'error', 'warning'} <= set(severities) else [f'severities {severities}']),
           f'{len(violations)} violations, severities {"/".join(severities)}')

    # 2. library variants
    lib = project / 'kilib' / f'{r9_lib.LIB_NICK}.pretty'
    issues, aliases = [], {}
    for variant in r9_lib.VARIANTS:
        text, al, found = r9_lib.build(lib, variant)
        issues += found
        aliases[variant] = al
        path = lib / f'{variant}.kicad_mod'
        if not path.is_file() or path.read_text() != text:
            issues.append(f'{path.name} differs from r9_lib\'s generated text')
    report('footprint variants', issues, '; '.join(f'{v} (pad alias {" ".join(f"{k}:{x}" for k, x in al.items())})'
                                                    for v, al in aliases.items()))

    # 3. design rules
    dru8 = r8_file('m3.kicad_dru').decode()
    dru9 = (project / 'm3.kicad_dru').read_text()
    issues = r9_dru.verify(dru8, dru9)
    pins = [i for i in check_actuators.check('(kicad_pcb)', dru9) if 'rule "' in i or 'm3.kicad_dru' in i]
    report('m3.kicad_dru R8 -> R9', issues + pins,
           f'sha16 {hashlib.sha256(dru9.encode()).hexdigest()[:16]} (check_actuators DRU_SHA '
           f'{check_actuators.DRU_SHA}), rule G P-1b scope, RAW_ACT pin rule before the pyro rules, the fill margins '
           'after rule A2, test-pad rule last')

    # 4. netlists
    r9dir = scratch_project(project, work)
    committed9 = (project / 'schematic.net.xml').read_bytes()
    fresh9 = r8c.export(r9dir).read_bytes()
    report('R9 netlist current', [] if fresh9 == committed9 else ['schematic.net.xml is stale: run r9_sch.py --netlist'],
           f'sha256 {hashlib.sha256(committed9).hexdigest()[:16]}')
    r8dir = work / 'r8'
    r8dir.mkdir()
    for name in [Path(n).name for n in git('ls-tree', '--name-only', R8_COMMIT, f'{REL}/').split()]:
        if name.endswith('.kicad_sch') or name in ('m3.kicad_pro', 'sym-lib-table'):
            (r8dir / name).write_bytes(r8_file(name))
    committed8 = r8_file('schematic.net.xml')
    fresh8 = r8c.export(r8dir).read_bytes()
    report('R8 netlist reproduced', [] if fresh8 == committed8 else ['fresh R8 export differs from its netlist'],
           f'{R8_COMMIT} sheets exported again and compared with its committed netlist')
    n8, n9 = r8c.parse(r8dir / 'schematic.net.xml'), r8c.parse(r9dir / 'schematic.net.xml')
    issues, rows = netlist_diff(n8, n9)
    report('netlist diff R8 -> R9', issues, f'{len(n9["comps"])} parts, {len(n9["pins"])} pins, libparts, libraries '
           f'and sheets compared; {len(rows)} differences, all decided')
    for row in rows:
        print('     ', row)
    evidence['netlist diff rows'] = rows

    # 5. RF / safety
    issues, stats = r8c.rf_safety(n9)
    report('RF pins off safety nets', issues, f"{stats['rf_parts']} RF parts, {stats['rf_nets']} RF nets, RF nets on "
           f"U1 pins {', '.join(stats['u1_rf_pins'])} (none a contract pin)")

    # 6. BOM
    issues, ev = bom_check(n8, n9)
    report('BOM codes', issues, f"R8 BOM {ev.get('bom_lines')} lines / {ev.get('bom_parts')} parts reproduced code by "
           f"code; extended codes {ev.get('extended')} <= {MAX_EXTENDED} (R8 supplier check {ev.get('cost_checked_utc')}, "
           f"bound to BOM sha {ev.get('bom_sha256')})")

    # 7. scratch board
    board = r9dir / 'm3.kicad_pcb'
    want = {ref: new.split(':', 1)[1] for ref, (_s, _o, new) in r9_sch.FOOTPRINTS.items()}
    par = drc(board).get('schematic_parity', [])
    got = sorted({(p['type'], m.group(1)) for p in par for i in p['items']
                  for m in [re.match(r'Footprint (\S+)', i['description'])] if m})
    expect = sorted(('footprint_symbol_mismatch', ref) for ref in want)
    kinds = sorted({p['type'] for p in par})
    report('parity, R8 board vs R9 schematic', [] if (got == expect and len(par) == len(want)) else
           [f'{len(par)} items {kinds}: {got}'], f'{len(par)} items: the decided footprint changes of '
           f'{", ".join(sorted(want))}')
    b = pcbnew.LoadBoard(str(board))
    nets_before = {(f.GetReference(), p.GetNumber()): p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
    changed = r9_lib.apply_variants(b, project=project)
    cleared = r9_lib.clear_overrides(b)
    lib_issues = sum((r9_lib.compare_to_library(b.FindFootprintByReference(r), project) for r in want), [])
    nets_after = {(f.GetReference(), p.GetNumber()): p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
    lc1, _ = check_r9.lc1(b)
    report('variants applied', lib_issues + lc1 + [f'{k} net changed' for k in nets_before if nets_before[k] !=
                                                   nets_after.get(k)] +
           ([] if sorted(changed) == sorted(want) else [f'changed {changed}']),
           f'{", ".join(changed)} exchanged in place; {len(cleared)} local clearances cleared '
           f'({sum(1 for c in cleared if c[0].startswith("TP"))} test pads 1.0 mm, '
           f'{sum(1 for c in cleared if not c[0].startswith("TP"))} RAW_ACT pins 0.3 mm); LC-1 0; pad nets unchanged')
    pcbnew.SaveBoard(str(board), b)
    rep = drc(board)
    par = rep.get('schematic_parity', [])
    libmm = [v for v in rep['violations'] if v['type'] in ('lib_footprint_mismatch', 'lib_footprint_issues')]
    report('parity, variant board vs R9 schematic', [f"{p['type']}: {p['description']}" for p in par] +
           [f"{v['type']}: {v['items'][0]['description'] if v['items'] else v['description']}" for v in libmm],
           f'{len(par)} parity items, {len(libmm)} library-footprint findings (KiCad DRC)')
    text, dru = board.read_text(), (r9dir / 'm3.kicad_dru').read_text()
    ca = check_actuators.check(text, dru)
    report('check_actuators (schematic contracts)', [i for i in ca if not i.startswith(BOARD_ONLY_ACTUATORS)],
           f'rules 1-14, 16 and the DRU pins on the R9 netlist and DRU; board-only, for step 3: '
           f'{len(ca) - len([i for i in ca if not i.startswith(BOARD_ONLY_ACTUATORS)])} (15b, R8 placement)')
    rows_ = check_r8.load_pin_table()
    b = pcbnew.LoadBoard(str(board))
    loader, lev = check_r8.loader_pins(b, rows_)
    report('pin table and U1 map', check_r8.pin_table_issues(rows_) + check_r8.u1_pin_map(b, rows_) + loader,
           '100 pins against sources/r8_design/pin_table.tsv r8_net (R9 keeps it, D-S1-07); loader pins (D5)')
    r9fp = [f'{r}: {check_r9.fc.fp_name(b.FindFootprintByReference(r))}' for r, n in check_r9.R9_FOOTPRINTS.items()
            if check_r9.fc.fp_name(b.FindFootprintByReference(r)) != n]
    roles = pad_roles(b)
    report('pad roles at the planned orientations', roles + r9fp,
           'J121 / J124 rot 90: entry -x, pin 2 (RAW / IGN) forward of pin 1 (BUS / OUT); J122 rot 180: SIG row aft, '
           'SERVO1-4 west to east; check_r9 R9_FOOTPRINTS')
    (work / 'base').mkdir()
    (work / 'base' / 'm3.kicad_pcb').write_bytes(r8_file('m3.kicad_pcb'))
    ctrl = pad_roles(pcbnew.LoadBoard(str(work / 'base' / 'm3.kicad_pcb')))
    report('pad roles, control (base footprints)', [] if len(ctrl) == 3 else [f'control findings {ctrl}'],
           'the bases at the same orientations fail all three role checks: ' + '; '.join(ctrl))

    # DRU liveness
    s = pcbnew.LoadBoard(str(board))
    r9_lib.clear_overrides(s)
    want_hits = seed_tracks(s)
    pcbnew.SaveBoard(str(r9dir / 's.kicad_pcb'), s)
    shutil.copy(r9dir / 'm3.kicad_pro', r9dir / 's.kicad_pro')
    h9 = liveness(r9dir, dru)
    h8 = liveness(r9dir, dru8)
    issues = [f'R9 DRU: no "{rule}" violation at {key}' for rule, key in want_hits.items()
              if not any(key in i for i in h9.get(rule, []))]
    issues += [f'R8 DRU already reports {rule} at {key}' for rule, key in want_hits.items()
               if any(key in i for i in h8.get(rule, []))]
    report('DRU liveness (seeded)', issues, '; '.join(f'{r}: {len(h9.get(r, []))} hit(s) under R9, '
                                                      f'{len(h8.get(r, []))} under R8' for r in want_hits))
    for p in ('s.kicad_pcb', 's.kicad_pro', 's.kicad_dru'):
        (r9dir / p).unlink(missing_ok=True)

    # fill equivalence (the R8 board, no variants: only the override -> rule move differs)
    fdir = work / 'fill'
    fdir.mkdir()
    (fdir / 'm3.kicad_pcb').write_bytes(r8_file('m3.kicad_pcb'))
    shutil.copy(r9dir / 'm3.kicad_pro', fdir / 'm3.kicad_pro')
    g8, g9 = r9_dru.rule_block(dru8, r9_dru.RULE_G), r9_dru.rule_block(dru, r9_dru.RULE_G)
    lc1_only = r9_dru.without_fill(dru).replace(g9, g8)              # R8's rule G, no fill margins: the LC-1 rules only
    (fdir / 'm3.kicad_dru').write_text(lc1_only)
    ref, fb = pcbnew.LoadBoard(str(fdir / 'm3.kicad_pcb')), pcbnew.LoadBoard(str(fdir / 'm3.kicad_pcb'))
    n_cleared = len(r9_lib.clear_overrides(fb))
    for z in fb.Zones():
        z.UnFill()
    fb.BuildConnectivity()
    filled = pcbnew.ZONE_FILLER(fb).Fill(fb.Zones())
    zones = {z.m_Uuid.AsString(): z for z in ref.Zones() if not z.GetIsRuleArea()}
    issues, layers = [] if filled else ['native fill failed'], 0
    for z in fb.Zones():
        if z.GetIsRuleArea():
            continue
        r = zones[z.m_Uuid.AsString()]
        for lay in z.GetLayerSet().Seq():
            a, c = r.GetFilledPolysList(lay).CloneDropTriangulation(), z.GetFilledPolysList(lay).CloneDropTriangulation()
            x, y = a.CloneDropTriangulation(), c.CloneDropTriangulation()
            x.BooleanSubtract(c)
            y.BooleanSubtract(a)
            layers += 1
            if x.Area() or y.Area():                                   # exactly equal (nm^2)
                issues.append(f'{z.GetZoneName() or z.GetNetname()} {fb.GetLayerName(lay)}: R8-only {x.Area() / 1e12:.4f}'
                              f' mm2, R9-only {y.Area() / 1e12:.4f} mm2')
    extra = [n for n, _t in r9_dru.rules(lc1_only) if n not in dict(r9_dru.rules(dru8))]
    if extra != ['R9 RAW_ACT pins to foreign copper', 'R9 bare test pads to foreign copper'] or \
            any(t_ != dict(r9_dru.rules(dru8))[n] for n, t_ in r9_dru.rules(lc1_only) if n not in extra):
        issues.append('the LC-1-only rule set is not R8\'s plus the two LC-1 rules')
    report('fill equivalence (overrides -> rules)', issues + ([] if n_cleared == 29 else [f'{n_cleared} cleared']),
           f'{layers} zone-layer fills of R8\'s board refilled with its {n_cleared} overrides cleared under R8\'s rules + '
           'the two LC-1 rules equal R8\'s committed fills exactly (boolean difference both ways 0 nm2)')

    # jlc_orient
    out = work / 'jlc_corrections.json'
    run = subprocess.run([KICAD_PY, '-I', str(ROOT / 'tools/jlc_orient.py'), str(ROOT / 'tools/jlc_easyeda/pads.json'),
                          str(board), '--out', str(out)], capture_output=True, text=True)
    issues = []
    if not out.is_file():
        issues.append(f'jlc_orient did not run: {run.stderr[-300:]}')
    else:
        new = json.loads(out.read_text())['parts']
        old = json.loads(git('show', f'{R8_COMMIT}:tools/jlc_corrections.json'))['parts']
        for key in ('C430601|M3_DB128L_2P_BK_SW', 'C32713291|HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR'):
            base = key.replace('_SW', '').replace('_MIR', '')
            a = {k: v for k, v in new.get(key, {}).items() if k != 'footprint'}
            o = {k: v for k, v in old.get(base, {}).items() if k != 'footprint'}
            if not a or a.get('theta') != 0 or a.get('status') != 'OK' or a != o:
                issues.append(f'{key}: {new.get(key)} (R8 base {old.get(base)})')
    report('JLC placement of the variants', issues, 'tools/jlc_orient.py through PAD_ALIAS: theta 0, offset 0, OK, '
           'equal to R8\'s base entries (tools/jlc_corrections.json itself is regenerated on the final board, step 9)')

    if args.keep:
        print('kept', work)
    if args.json:
        args.json.write_text(json.dumps(dict(ok=not failures, failures=failures, evidence=evidence), indent=1) + '\n')
    print('r9_sch_check:', 'OK' if not failures else f'{len(failures)} failure(s)')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
