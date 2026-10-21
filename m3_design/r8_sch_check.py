#!/usr/bin/env python3
"""Verify the R8 schematic (m3_design/r8_sch.py) against R7 (commit 431025d): R8 build step 2.

usage: <KiCad python3> -I m3_design/r8_sch_check.py [--project DIR] [--keep DIR]
exit 0 = every check holds. Read-only on the worktree; all work happens in a temporary directory (--keep DIR keeps
it, for inspection; --project checks another copy of the project, for seeded-defect tests). KiCad Python is needed
for the contract checks on the netlist-applied board.

1. ERC: kicad-cli sch erc, all severities, on the worktree schematic: 0 violations, no ignored checks.
2. Netlist: a fresh export of the worktree schematic equals the committed schematic.net.xml, and a fresh export of
   R7's sheets equals R7's committed netlist (both normalised as r7_sch.export_netlist does). The semantic diff of the
   two exports must be exactly the decided changes: every component, library part and library identical; each
   sheet's title block identical apart from rev M3-ASSY-R7 -> M3-ASSY-R8; every pin's pin function and type
   identical; and the pin-to-net changes exactly pin_table.tsv's changed rows (D2, D3) plus R310.1 3V3_RADIO -> 3V3
   (D4). It is printed.
3. RF and safety, on the R8 netlist, with check_r7's own definitions (RF_PART, RF_NET, SAFETY_NETS): no RF-part pin
   on a safety net; every RF net joins only RF parts and U1; no RF net on a safety-contract pin of U1 (D14).
4. Contract on the R8 netlist: a scratch board, R7's board with every pad's net taken from the R8 netlist, saved in
   a copy of the project:
   - m3_design/check_actuators.py (the safety contract, read from pad nets) holds in full;
   - check_r8's netlist checks hold: pin table, U1's whole pin map, the loader-pin rule (D5), and check_contract
     with only the board-only findings step 4 removes (TH1-TH3 present, R310 not yet at the MCU end) left over;
   - KiCad schematic parity of that board against the R8 schematic is 0, and parity of R7's own board against it
     is exactly the decided pad changes (net_conflict items), KiCad's native view of the same diff.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'tools'))
import pcbnew                                  # noqa: E402
import check_actuators                         # noqa: E402
import check_r7                                # noqa: E402
import check_r8                                # noqa: E402
import r7_sch                                  # noqa: E402
import r8_sch                                  # noqa: E402

R7_COMMIT = '431025d'
R7_BOARD_SHA = 'c872a3d3'
PROJECT = HERE / 'assembly_review'
REL = 'm3_design/assembly_review'
CLI = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
# check_r8.check_contract findings that are board geometry, not netlist: the scratch board keeps R7's footprints and
# placement, and step 4 removes the tooling holes (D8) and puts R310 at the MCU end of the NSS lane (D4)
BOARD_ONLY = {'removed part remains: TH1', 'removed part remains: TH2', 'removed part remains: TH3',
              'R310: must sit at the U1 end of its lane (D4)'}


def git(*args, binary=False):
    out = subprocess.run(['git', '-C', str(ROOT), *args], check=True, capture_output=True)
    return out.stdout if binary else out.stdout.decode()


def r7_file(name, dest):
    dest.write_bytes(git('show', f'{R7_COMMIT}:{REL}/{name}', binary=True))
    return dest


def export(project):
    """kicad-cli netlist export, normalised exactly as r7_sch.export_netlist (relative path, blank date)."""
    r7_sch.export_netlist(project)
    return project / 'schematic.net.xml'


def erc(project):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'erc.json'
        subprocess.run([CLI, 'sch', 'erc', '--severity-all', '--format', 'json', '-o', str(out),
                        str(project / 'm3.kicad_sch')], check=True, capture_output=True)
        report = json.loads(out.read_text())
    violations = [v for s in report['sheets'] for v in s['violations']]
    return violations, report.get('ignored_checks', []), report.get('included_severities', [])


def parity(board):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(board)], check=True, capture_output=True)
        return json.loads(out.read_text()).get('schematic_parity', [])


# --- netlist ------------------------------------------------------------------------------------------------------
def nc(net):
    return 'NC' if net.startswith('unconnected-') else net


def parse(path):
    root = ET.parse(path).getroot()
    comps = {c.attrib['ref']: ET.tostring(c) for c in root.findall('./components/comp')}
    pins = {}
    for net in root.findall('./nets/net'):
        for node in net.findall('node'):
            key = (node.attrib['ref'], node.attrib['pin'])
            assert key not in pins, f'{key} on two nets'
            pins[key] = (net.attrib['name'], node.attrib.get('pinfunction', ''), node.attrib.get('pintype', ''))
    return {'root': root, 'comps': comps, 'pins': pins,
            'libparts': ET.tostring(root.find('libparts')), 'libraries': ET.tostring(root.find('libraries'))}


def expected_changes():
    pins, changed = r8_sch.load_changes()
    want = {('U1', p): (o, n) for p, (o, n) in changed.items()}
    ref, pin, old, new = r8_sch.R310
    want[(ref, pin)] = (old, new)
    return want


def netlist_diff(r7, r8):
    """Issues and the pin-to-net change list {(ref, pin): (R7 net, R8 net)} ('NC' = no-connect)."""
    issues = []
    if set(r7['comps']) != set(r8['comps']):
        issues.append(f"components differ: -{sorted(set(r7['comps']) - set(r8['comps']))} "
                      f"+{sorted(set(r8['comps']) - set(r7['comps']))}")
    for ref in sorted(set(r7['comps']) & set(r8['comps'])):
        if r7['comps'][ref] != r8['comps'][ref]:
            issues.append(f'component {ref}: fields, footprint or sheet path changed')
    for key in ('libparts', 'libraries'):
        if r7[key] != r8[key]:
            issues.append(f'netlist <{key}> changed')
    d7 = ET.tostring(r7['root'].find('design')).replace(b'<rev>M3-ASSY-R7</rev>', b'<rev>M3-ASSY-R8</rev>')
    d8 = ET.tostring(r8['root'].find('design'))
    if d7 != d8:
        issues.append('netlist <design> differs beyond rev M3-ASSY-R7 -> M3-ASSY-R8')
    revs = [s.findtext('title_block/rev') for s in r8['root'].findall('design/sheet')]
    if len(revs) != 15 or set(revs) != {'M3-ASSY-R8'}:
        issues.append(f'sheet revs: {revs}')
    if set(r7['pins']) != set(r8['pins']):
        issues.append(f"pin sets differ: {sorted(set(r7['pins']) ^ set(r8['pins']))}")
    changes = {}
    flag = '+no_connect'           # KiCad appends it to the pin type of a pin with a no-connect flag
    for key in sorted(set(r7['pins']) & set(r8['pins'])):
        (n7, f7, t7), (n8, f8, t8) = r7['pins'][key], r8['pins'][key]
        if (f7, t7.removesuffix(flag)) != (f8, t8.removesuffix(flag)):
            issues.append(f'{key[0]}.{key[1]}: pin function/type {f7}/{t7} -> {f8}/{t8}')
        for n, t, rev in ((n7, t7, 'R7'), (n8, t8, 'R8')):
            if t.endswith(flag) and nc(n) != 'NC':
                issues.append(f'{rev} {key[0]}.{key[1]}: no-connect flag on net {n}')
        if nc(n7) != nc(n8):
            changes[key] = (nc(n7), nc(n8))
    want = expected_changes()
    for key in sorted(set(changes) | set(want)):
        if changes.get(key) != want.get(key):
            issues.append(f'{key[0]}.{key[1]}: netlist change {changes.get(key)} but decided {want.get(key)}')
    return issues, changes


def rf_safety(r8):
    """F10 / D2: no RF pin on a safety net, RF nets only between RF parts and U1, no RF net on a contract pin."""
    issues, members = [], {}
    for (ref, pin), (net, _, _) in r8['pins'].items():
        members.setdefault(net, set()).add((ref, pin))
    rf_parts = {ref for ref in r8['comps'] if check_r7.RF_PART.fullmatch(ref)}
    for (ref, pin), (net, _, _) in sorted(r8['pins'].items()):
        if ref in rf_parts and check_r7.SAFETY_NETS.match(net):
            issues.append(f'{ref}.{pin}: RF part on safety net {net}')
    rf_nets = sorted(n for n in members if check_r7.RF_NET.match(n))
    for net in rf_nets:
        foreign = sorted(f'{r}.{p}' for r, p in members[net] if r not in rf_parts and r != 'U1')
        if foreign:
            issues.append(f'RF net {net} reaches non-RF parts {foreign}')
        for r, p in members[net]:
            if r == 'U1' and p in check_r8.CONTRACT_PINS:
                issues.append(f'RF net {net} on safety-contract pin U1.{p}')
        if check_r7.SAFETY_NETS.match(net):
            issues.append(f'RF net {net} matches the safety-net pattern')
    stats = {'rf_parts': len(rf_parts), 'rf_nets': len(rf_nets),
             'u1_rf_pins': sorted((p for n in rf_nets for r, p in members[n] if r == 'U1'), key=int)}
    return issues, stats


# --- scratch board ------------------------------------------------------------------------------------------------
def apply_netlist(board_path, r8):
    """Every pad of every netlist part takes its net from the R8 netlist; returns the pads that changed."""
    b = pcbnew.LoadBoard(str(board_path))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    missing = sorted(set(r8['comps']) - set(fps))
    assert not missing, f'netlist parts missing from the R7 board: {missing}'
    changed = []
    for ref, f in fps.items():
        if ref not in r8['comps']:
            continue
        for p in f.Pads():
            key = (ref, p.GetNumber())
            if not p.GetNumber() or key not in r8['pins']:
                continue
            name = r8['pins'][key][0]
            net = b.FindNet(name)
            if net is None:
                net = pcbnew.NETINFO_ITEM(b, name)
                b.Add(net)
            if p.GetNetname() != name:
                changed.append((ref, p.GetNumber(), nc(p.GetNetname()), nc(name)))
                p.SetNet(net)
    pcbnew.SaveBoard(str(board_path), b)
    return sorted(changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--project', type=Path, default=PROJECT, help='project folder (default: the worktree\'s)')
    parser.add_argument('--keep', type=Path, help='work in this (new) directory and keep it')
    args = parser.parse_args()
    project = args.project.resolve()
    if args.keep:
        args.keep.mkdir(parents=True)
        work = args.keep
    else:
        tmp = tempfile.TemporaryDirectory(prefix='r8_sch_check_')
        work = Path(tmp.name)
    failures = []

    def report(name, issues, detail=''):
        print(f"{'OK  ' if not issues else 'FAIL'} {name}{': ' + detail if detail else ''}")
        for i in issues:
            print('     -', i)
        failures.extend(f'{name}: {i}' for i in issues)

    # 1. ERC
    violations, ignored, severities = erc(project)
    report('ERC', [f"{v['type']}: {v['description']}" for v in violations] +
           ([f'ignored checks {ignored}'] if ignored else []) +
           ([] if {'error', 'warning'} <= set(severities) else [f'severities {severities}']),
           f'{len(violations)} violations, severities {"/".join(severities)}')
    report('schematic parts', [f'{f.name}: TH part' for f in project.glob('*.kicad_sch')
                               if re.search(r'\(property "Reference" "TH\d+"', f.read_text())],
           'no TH1-TH3 symbols (board-only tooling holes, D8)')

    # 2. netlists
    r8dir, r7dir = work / 'r8', work / 'r7'
    shutil.copytree(project, r8dir, ignore=shutil.ignore_patterns('fab', 'sheets', 'sources', '*.png', '*.svg',
                                                                   '__pycache__', '*.lck', '*.kicad_prl'))
    committed8 = (project / 'schematic.net.xml').read_bytes()
    fresh8 = export(r8dir).read_bytes()
    report('R8 netlist current', [] if fresh8 == committed8 else ['schematic.net.xml is stale: run r8_sch.py --netlist'],
           f'sha256 {hashlib.sha256(committed8).hexdigest()[:16]}')
    r7dir.mkdir()
    names = [Path(n).name for n in git('ls-tree', '--name-only', R7_COMMIT, f'{REL}/').split()]
    for name in names:
        if name.endswith('.kicad_sch') or name in ('m3.kicad_pro', 'sym-lib-table'):
            r7_file(name, r7dir / name)
    committed7 = git('show', f'{R7_COMMIT}:{REL}/schematic.net.xml', binary=True)
    fresh7 = export(r7dir).read_bytes()
    report('R7 netlist reproduced', [] if fresh7 == committed7 else ['fresh R7 export differs from its netlist'],
           f'{R7_COMMIT} sheets exported again and compared with its committed netlist')
    r7, r8 = parse(r7dir / 'schematic.net.xml'), parse(r8dir / 'schematic.net.xml')
    issues, changes = netlist_diff(r7, r8)
    report('netlist diff R7 -> R8', issues, f'{len(r8["comps"])} parts, libparts, libraries and sheets compared; '
           f'{len(changes)} pin-net changes, {len(expected_changes())} decided')
    print('     pin            R7 net               R8 net')
    for (ref, pin), (old, new) in sorted(changes.items(), key=lambda kv: (kv[0][0] != 'U1', kv[0][0], int(kv[0][1]))):
        fn = r8['pins'][(ref, pin)][1]
        print(f'     {ref}.{pin:<4} {fn:<9} {old:<20} {new}')

    # 3. RF / safety
    issues, stats = rf_safety(r8)
    report('RF pins off safety nets', issues, f"{stats['rf_parts']} RF parts, {stats['rf_nets']} RF nets, RF nets on "
           f"U1 pins {', '.join(stats['u1_rf_pins'])} (none a contract pin)")

    # 4. contract on the netlist-applied board
    board7 = r8dir / 'm3.kicad_pcb'
    r7_file('m3.kicad_pcb', board7)
    sha = hashlib.sha256(board7.read_bytes()).hexdigest()
    assert sha.startswith(R7_BOARD_SHA), f'R7 board sha {sha[:16]}'
    want = expected_changes()
    found = parity(board7)
    got = set()
    for item in found:
        m = re.match(r'Pad (\S+) \[[^\]]*\] of (\S+)', item['items'][0]['description']) if item['items'] else None
        got.add((item['type'], (m.group(2), m.group(1)) if m else item['description']))
    report('parity, R7 board vs R8 schematic', sorted(str(g) for g in got ^ {('net_conflict', k) for k in want}),
           f'{len(found)} net_conflict items, {len(want)} decided pads')
    pad_changes = apply_netlist(board7, r8)
    report('netlist applied to the R7 board', [f'{c}' for c in pad_changes
                                              if want.get((c[0], c[1])) != (c[2], c[3])] +
           ([f'{len(pad_changes)} pads changed, {len(want)} decided'] if len(pad_changes) != len(want) else []),
           f'{len(pad_changes)} pads re-netted')
    found = parity(board7)
    report('parity, netlist-applied board vs R8 schematic', [f"{p['type']}: {p['description']}" for p in found],
           f'{len(found)} items')
    text, dru = board7.read_text(), (r8dir / 'm3.kicad_dru').read_text()
    report('check_actuators (schematic-side safety contract)', check_actuators.check(text, dru),
           'every rule on the R8 netlist, D121 7c included')
    b = pcbnew.LoadBoard(str(board7))
    rows = check_r8.load_pin_table()
    report('check_r8 pin table', check_r8.pin_table_issues(rows))
    report('check_r8 U1 pin map', check_r8.u1_pin_map(b, rows), '100 pins against pin_table.tsv r8_net')
    loader, evidence = check_r8.loader_pins(b, rows)
    report('check_r8 loader pins (D5)', loader, ', '.join(f'{k} {v}' for k, v in evidence.items()))
    contract, _, _ = check_r8.check_contract(b, r8dir, rows)
    left = sorted(set(contract) & BOARD_ONLY)
    report('check_r8 contract', sorted(set(contract) - BOARD_ONLY),
           f'R310 on 3V3, MODULE_PINS, SERIES, connectors, RF parts off safety nets; board-only, for step 4: '
           f'{"; ".join(left) or "none"}')
    if args.keep:
        print('kept', work)
    print('r8_sch_check:', 'OK' if not failures else f'{len(failures)} failure(s)')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
