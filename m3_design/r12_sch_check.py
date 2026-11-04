#!/usr/bin/env python3
"""Check the M3-ASSY-R12 schematic against R11's pinned netlist, circuit.json and pin_table.tsv.

usage: KiCad python3 -I -B m3_design/r12_sch_check.py --project m3_design/r12 [--json FILE]
Checks (D-R12-01: R11's circuit pruned and re-sourced, every AGENTS section 2 rule kept):
  * every part and pin exactly as r12_sch.model() derives them from R11's netlist and circuit.json (deleted parts
    gone, re-sourced parts on their catalog code, added parts and net changes present), no other part or pin;
  * U1's balls against pin_table.tsv r12_net, the package supply balls and R11's PDR_ON / VDDLDO / VDD33USB ties;
  * the AGENTS section 2 contracts by net: the pyro bus behind the Q120 / Q121 load switch, every pyro gate network
    (series resistor, pull-down, gate-source capacitor), PE4 / PC1 on their balls, the single J400 switch chain with
    D402, the pyro wire pads, servo pull-downs and clamp, the ports, the camera switch default off;
  * part identity: LCSC / Manufacturer / Manufacturer Part agree with circuit.json's catalog (or R11's line), one
    footprint and one part number per code, every BOM part has a code, every footprint in the project kilib and a
    top-side land (D-R12-01, one assembled side);
  * strict ERC (zero violations of any severity), the DRU, a deterministic regeneration from the pinned inputs and a
    fresh netlist export of the supplied sheets; seeded contract faults (in memory) must all be caught.
Schematic gate only: no PCB, routing, thermal or bench claim.
"""
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r12_sch as gen

R10_REMOVED = {'J123', 'R160', 'R161', 'C160', 'D122', 'TP84', 'TP85', 'TP86', 'TP87', 'TP89', 'TP92', 'U412', 'U422',
               'R443', 'R453', 'C441', 'C442', 'C451', 'C452', 'U410', 'U420', 'U411', 'U421', 'R410', 'R411', 'R412',
               'R420', 'R421', 'R422', 'R442', 'R452', 'C440', 'C443', 'C450', 'C453', 'R177', 'R124', 'R125', 'R182',
               'R172', 'C122', 'R168', 'R170', 'J124'}

# AGENTS section 2 / REQUIREMENTS F4, F7-F10 contracts, by (ref, pin) -> net (None = no connection)
SAFETY = {
    # 2.2: the pyro bus RAW_ACT is taken after the load switch Q120 / Q121 (back-to-back AO3401A), never from the pack
    ('Q120', '3'): 'BAT_IN', ('Q120', '2'): 'ACT_FET_S', ('Q121', '2'): 'ACT_FET_S', ('Q121', '3'): 'RAW_ACT',
    ('Q120', '1'): 'ACT_GATE', ('Q121', '1'): 'ACT_GATE',
    ('R134', '1'): 'PYRO1_IGN', ('R134', '2'): 'RAW_ACT', ('R132', '1'): 'RAW_ACT',
    ('J121', '1'): 'PYRO1_OUT', ('J121', '2'): 'PYRO1_IGN',
    # 2.4: gate networks (series resistor, pull-down, gate-source capacitor), defined off in reset
    ('R119', '1'): 'ACT_GATE', ('R119', '2'): 'ACT_FET_S', ('R120', '1'): 'ACT_FET_S', ('R120', '2'): 'ACT_GATE',
    ('C120', '1'): 'ACT_FET_S', ('C120', '2'): 'ACT_GATE', ('R121', '1'): 'ACT_GATE', ('R121', '2'): 'ACT_DRV',
    ('Q122', '1'): 'ACT_EN', ('Q122', '2'): 'GND', ('Q122', '3'): 'ACT_DRV',
    ('R122', '1'): 'ACT_EN_MCU', ('R122', '2'): 'ACT_EN', ('R123', '1'): 'ACT_EN', ('R123', '2'): 'GND',
    ('C123', '1'): 'ACT_EN', ('C123', '2'): 'GND',
    ('Q124', '1'): 'PYRO1_GATE', ('Q124', '2'): 'GND', ('Q124', '3'): 'PYRO1_OUT',
    ('R126', '1'): 'PYRO1_GATE_N', ('R126', '2'): 'PYRO1_GATE', ('R127', '1'): 'PYRO1_GATE_N', ('R127', '2'): 'GND',
    ('R128', '1'): 'PYRO1_GATE', ('R128', '2'): 'GND', ('C126', '1'): 'PYRO1_GATE', ('C126', '2'): 'GND',
    ('U1', 'C3'): 'PYRO1_GATE_N', ('U1', 'F2'): 'ACT_EN_MCU',
    # continuity / bus sense (F8; never in the fire path)
    ('R173', '1'): 'PYRO1_OUT', ('R131', '1'): 'PYRO1_OUT', ('R131', '2'): 'PYRO1_COLD',
    ('D120', '1'): '3V3', ('D120', '2'): None, ('D120', '3'): 'PYRO1_COLD',
    # 2.1 / F8 / F9: one external switch J400 drives U9 EN; D402 clamps J400.2 ahead of R165
    ('J400', '1'): 'BAT_SW_SOURCE', ('J400', '2'): 'BAT_SW_RETURN', ('J400', '3'): None, ('J400', '4'): None,
    ('R80', '1'): 'BAT_IN', ('R80', '2'): 'BAT_SW_SOURCE', ('R165', '1'): 'BAT_SW_RETURN', ('R165', '2'): 'BAT_ENABLE',
    ('D402', '1'): 'BAT_SW_RETURN', ('D402', '2'): 'GND', ('R81', '1'): 'BAT_ENABLE', ('R81', '2'): 'GND',
    ('C87', '1'): 'BAT_ENABLE', ('C87', '2'): 'GND', ('U9', '1'): 'BAT_ENABLE', ('U9', '5'): 'BAT_IN',
    ('U9', '6'): 'RAW_PROTECTED', ('U9', '2'): 'BAT_OVLO', ('U9', '9'): 'BAT_ILIM', ('U9', '7'): 'BAT_DVDT',
    ('J1', '1'): 'BAT_IN', ('J1', '2'): 'GND',
    # F4 / F6: servo signals, 1 k series, pull-downs, SRV05-4 clamp; J122 pin 6 unused
    ('J122', '1'): 'SERVO1_OUT', ('J122', '2'): 'SERVO2_OUT', ('J122', '3'): 'SERVO3_OUT', ('J122', '4'): 'SERVO4_OUT',
    ('J122', '5'): 'GND', ('J122', '6'): None,
    ('R154', '2'): 'GND', ('R155', '2'): 'GND', ('R156', '2'): 'GND', ('R157', '2'): 'GND',
    # F10 ports: identical, 1 PORT_4V8, 2 GND, 3 board TXO, 4 board RXI, 1 kOhm series
    ('J410', '1'): 'PORT_4V8', ('J410', '2'): 'GND', ('J410', '3'): 'GPS_TX_WIRE', ('J410', '4'): 'GPS_RX_WIRE',
    ('J420', '1'): 'PORT_4V8', ('J420', '2'): 'GND', ('J420', '3'): 'RADIO_TX_WIRE', ('J420', '4'): 'RADIO_RX_WIRE',
    ('J440', '1'): 'PORT_4V8', ('J440', '2'): 'GND', ('J440', '3'): 'AUX_TX_WIRE', ('J440', '4'): 'AUX_RX_WIRE',
    ('R440', '2'): 'GPS_RX_MCU', ('R441', '1'): 'GPS_TX_MCU', ('R450', '2'): 'RADIO_RX_MCU', ('R451', '1'): 'RADIO_TX_MCU',
    ('R470', '2'): 'AUX_RX_MCU', ('R471', '1'): 'AUX_TX_MCU',
    # camera: J9 1-2 CAM_5V, 3-4 GND, 5 board RX, 6 board TX; the buck EN is the MCU switch with its pull-down
    ('J9', '1'): 'CAM_5V', ('J9', '2'): 'CAM_5V', ('J9', '3'): 'GND', ('J9', '4'): 'GND', ('J9', '5'): 'CAM_RX_WIRE',
    ('J9', '6'): 'CAM_TX_WIRE', ('U403', '5'): 'CAM_PWR_EN', ('R431', '1'): 'CAM_PWR_EN', ('R431', '2'): 'GND',
    ('R100', '1'): 'CAM_RX_WIRE', ('R100', '2'): 'CAM_MCU_RX', ('R101', '1'): 'CAM_MCU_TX', ('R101', '2'): 'CAM_TX_WIRE',
    # D-R12-04: the VLOGIC diode-OR; D-R12-05: PA4 port sense
    ('D5', '1'): 'VLOGIC', ('D5', '2'): 'RAW_PROTECTED', ('D6', '1'): 'VLOGIC', ('D6', '2'): 'VBUS',
    ('R111', '1'): 'PORT_4V8', ('R111', '2'): 'PORT_SENSE', ('R112', '1'): 'PORT_SENSE', ('R112', '2'): 'GND',
    # R11 package ties
    ('U1', 'F7'): '3V3', ('U1', 'F4'): '3V3', ('U1', 'F6'): '3V3', ('U1', 'H1'): '3V3A', ('U1', 'G1'): 'GND',
    ('U1', 'E1'): 'NRST', ('U1', 'D5'): 'BOOT0', ('U1', 'E7'): 'VCAP2', ('U1', 'F8'): 'VCAP1',
}
REQUIRED_PARTS = ('Q120', 'Q121', 'Q122', 'Q124', 'R119', 'R120', 'C120', 'R121', 'R122', 'R123', 'C123', 'R126', 'R127',
                  'R128', 'C126', 'R134', 'D402', 'U9', 'D121', 'R150', 'R151', 'R152', 'R153', 'R154', 'R155', 'R156',
                  'R157', 'U3', 'J430', 'R460', 'R461', 'R462', 'R463', 'R464', 'C84', 'LS120', 'U4', 'U5', 'D5', 'D6')
WIRE_PADS = ('J1', 'J121')


def read_netlist(path):
    return gen.read_netlist(path)


def footprint_side_issues(project, name):
    """D-R12-01 top-side land, read from the footprint file: footprint on F.Cu, no SMD pad on a B.* layer, SMD pads
    with copper on F.Cu (paste-only apertures allowed)."""
    path = project / 'kilib/rocket.pretty' / (name + '.kicad_mod')
    if not path.exists():
        return [f'footprint {name} missing from the project kilib']
    text = path.read_text()
    issues = []
    if not re.search(r'^\t\(layer "F\.Cu"\)', text, re.M):
        issues.append(f'{name}: footprint not on F.Cu')
    for m in re.finditer(r'\(pad "[^"]*" (smd|thru_hole|np_thru_hole) [\s\S]*?\(layers ([^)]*)\)', text):
        layers = set(re.findall(r'"([^"]+)"', m.group(2)))
        if m.group(1) == 'smd' and (any(l.startswith('B.') for l in layers) or
                                    not ({'F.Cu'} & layers or layers == {'F.Paste'})):
            issues.append(f'{name}: SMD pad on layers {sorted(layers)} (one assembled side, D-R12-01)')
    return issues


def contract(parts, pins, project=None):
    data = gen.circuit()
    want_parts, want_pins = gen.model(data)
    issues = []
    for (ref, pin), net in SAFETY.items():
        if pins.get((ref, pin), 'missing') != net:
            issues.append(f'AGENTS 2 / F-contract: {ref}.{pin} is {pins.get((ref, pin), "missing")!r}, must be {net!r}')
    for ref in REQUIRED_PARTS:
        if ref not in parts:
            issues.append(f'required part {ref} missing')
    if R10_REMOVED & parts.keys():
        issues.append(f'R10 removed parts present: {sorted(R10_REMOVED & parts.keys())}')
    if set(data['deleted']) & parts.keys():
        issues.append(f'D-R12 deleted parts present: {sorted(set(data["deleted"]) & parts.keys())}')
    if 'PYRO1_BUS' in pins.values() or any(str(n).startswith('RAW_ACT_SENSE') for n in pins.values()):
        issues.append('single screw switch: no PYRO1_BUS or RAW_ACT_SENSE net')
    for ref in ('C126', 'R127', 'R128', 'R123', 'C123', 'R119', 'R120', 'C120', 'R134', 'R431'):
        if ref in parts and set(parts[ref]['flags']) & {'dnp', 'exclude_from_bom'}:
            issues.append(f'{ref}: a safety network part must be fitted (no DNP / BOM exclusion)')
    for ref in WIRE_PADS:
        if ref in parts and not {'exclude_from_bom', 'exclude_from_pos_files'} <= set(parts[ref]['flags']):
            issues.append(f'{ref}: wire pads stay out of the BOM and CPL (D-R11-05)')
    # U1 against the pin table
    for row in gen.read_pin_table():
        if row['r11_ball'] == '-':
            continue
        want = None if row['r12_net'] == 'NC' else row['r12_net']
        if pins.get(('U1', row['r11_ball']), 'missing') != want:
            issues.append(f'U1.{row["r11_ball"]} ({row["port"]}): {pins.get(("U1", row["r11_ball"]), "missing")!r}, '
                          f'pin_table r12_net {want!r}')
    for ball in ('C2', 'E4', 'E5', 'E6', 'J1'):
        if pins.get(('U1', ball)) != 'GND':
            issues.append(f'U1.{ball} (VSS) must be GND')
    for ball in ('D2', 'F5', 'K1'):
        if pins.get(('U1', ball)) != '3V3':
            issues.append(f'U1.{ball} (VDD) must be 3V3')
    # exact parts and pins
    if set(parts) != set(want_parts):
        issues.append(f'component set: missing {sorted(set(want_parts) - set(parts))}; extra {sorted(set(parts) - set(want_parts))}')
    for key in sorted(set(want_pins) | set(pins)):
        if pins.get(key, 'missing') != want_pins.get(key, 'missing'):
            issues.append(f'{key[0]}.{key[1]}: {pins.get(key, "missing")!r}, expected {want_pins.get(key, "missing")!r}')
    for ref in sorted(set(parts) & set(want_parts)):
        a, w = parts[ref], want_parts[ref]
        for key in ('lib', 'value', 'footprint', 'fields', 'flags'):
            if a[key] != w[key]:
                issues.append(f'{ref}: {key} {a[key]!r}, expected {w[key]!r}')
    # part identity (AGENTS 3)
    groups = {}
    for ref, p in parts.items():
        if 'exclude_from_bom' in p['flags']:
            continue
        code = p['fields'].get('LCSC')
        if not code:
            issues.append(f'{ref}: in the BOM without an LCSC code')
            continue
        groups.setdefault(code, set()).add((p['footprint'], p['fields'].get('Manufacturer'),
                                            p['fields'].get('Manufacturer Part')))
        cat = data['catalog'].get(code)
        if cat and (cat['Manufacturer'], cat['Manufacturer Part']) != (p['fields'].get('Manufacturer'),
                                                                       p['fields'].get('Manufacturer Part')):
            issues.append(f'{ref}: {code} fields disagree with circuit.json catalog')
    for code, ids in sorted(groups.items()):
        if len(ids) > 1:
            issues.append(f'LCSC {code} on several footprints or part numbers: {sorted(ids)}')
    for ref in data['owner_fit']:
        if ref not in parts or not parts[ref]['fields'].get('LCSC'):
            issues.append(f'owner-fitted {ref} missing or without an LCSC code')
    if project is not None:
        for name in sorted({p['footprint'].split(':')[1] for p in parts.values()}):
            issues += footprint_side_issues(project, name)
    return issues


def seeds(parts, pins):
    def pop(ref):
        return lambda p, n: p.pop(ref)

    def field(ref, name, value):
        return lambda p, n: p[ref]['fields'].__setitem__(name, value)
    mutations = {
        'pyro bus fed straight from the pack': lambda p, n: n.update({('R134', '2'): 'BAT_IN'}),
        'load switch removed': pop('Q120'),
        'load switch bypassed (Q121 drain on BAT_IN)': lambda p, n: n.update({('Q121', '3'): 'BAT_IN'}),
        'fire gate pull-down removed': pop('R128'),
        'fire gate series resistor shorted': lambda p, n: n.update({('U1', 'C3'): 'PYRO1_GATE'}),
        'fire gate capacitor DNP': lambda p, n: p['C126']['flags'].append('dnp'),
        'bus enable pull-down removed': pop('R123'),
        'bus-enable gate capacitor removed': pop('C123'),
        'load-switch gate capacitor removed': pop('C120'),
        'fire command on the wrong ball': lambda p, n: n.update({('U1', 'C3'): None, ('U1', 'D3'): 'PYRO1_GATE_N'}),
        'bus enable on the wrong ball': lambda p, n: n.update({('U1', 'F2'): None}),
        'J400 clamp removed': pop('D402'),
        'J400 switch shorted to EN': lambda p, n: n.update({('J400', '2'): 'BAT_ENABLE'}),
        'second arming terminal restored': lambda p, n: p.update({'J124': copy.deepcopy(p['J400'])}),
        'separate pyro bus restored': lambda p, n: n.update({('R134', '2'): 'PYRO1_BUS'}),
        'shorted-igniter limiter removed': pop('R134'),
        'servo pull-down removed': pop('R156'),
        'servo pin 6 connected': lambda p, n: n.update({('J122', '6'): 'SERVO4_OUT'}),
        'port TX / RX swapped': lambda p, n: n.update({('J420', '3'): 'RADIO_RX_WIRE', ('J420', '4'): 'RADIO_TX_WIRE'}),
        'port series resistor bypassed': lambda p, n: n.update({k: 'GPS_TX_WIRE' for k, v in list(n.items())
                                                                if k[0] == 'U1' and v == 'GPS_TX_MCU'}),
        'camera switch pull-down removed': pop('R431'),
        'camera buck always on': lambda p, n: n.update({('U403', '5'): 'RAW_PROTECTED'}),
        'USB leg of the diode-OR missing': pop('D6'),
        'diode-OR reversed': lambda p, n: n.update({('D5', '1'): 'RAW_PROTECTED', ('D5', '2'): 'VLOGIC'}),
        'deleted USB mux restored': lambda p, n: p.update({'U11': copy.deepcopy(p['U9'])}),
        'deleted port ESD restored': lambda p, n: p.update({'D410': copy.deepcopy(p['D402'])}),
        'PDR_ON tied low': lambda p, n: n.update({('U1', 'F7'): 'GND'}),
        'VCAP balls on one cap': lambda p, n: n.update({('U1', 'E7'): 'VCAP1'}),
        'PA4 left on the deleted mux net': lambda p, n: n.update({('U1', 'G3'): 'LOGIC_SOURCE_ST'}),
        'LCSC code and part number disagree': field('R81', 'Manufacturer Part', '0402WGF4703TCE'),
        'part without an LCSC code': field('C8', 'LCSC', ''),
        'code on two footprints': lambda p, n: p['C10'].__setitem__('footprint', 'rocket:C0805'),
        'value changed': lambda p, n: p['R82'].__setitem__('value', '2M 0.1%'),
        'wire pads in the BOM': lambda p, n: p['J1']['flags'].remove('exclude_from_bom'),
        'owner-fitted buzzer removed': pop('LS120'),
        'barometer SA0 floating': lambda p, n: n.update({('U5', '2'): None}),
    }
    out = {}
    for label, mutate in mutations.items():
        p, n = copy.deepcopy(parts), dict(pins)
        mutate(p, n)
        out[label] = bool(contract(p, n))
    return out


def side_seed(project):
    """A bottom-side SMD land in a copy of the kilib must be caught."""
    with tempfile.TemporaryDirectory(prefix='r12-side-') as d:
        work = Path(d)
        shutil.copytree(project / 'kilib', work / 'kilib')
        f = work / 'kilib/rocket.pretty/R0402.kicad_mod'
        text = f.read_text()
        f.write_text(text.replace('"F.Cu"', '"B.Cu"', 1))
        return bool(footprint_side_issues(work, 'R0402'))


def _stamp_free(path):
    data = path.read_bytes()
    return re.sub(rb'<tool>[^<]*</tool>', b'<tool/>', data) if path.name.endswith('.net.xml') else data


def check(project):
    gen.source_check()
    issues = []
    if (gen.DESIGN / 'pin_table.tsv').read_text() != gen.pin_table_text():
        issues.append('pin_table.tsv differs from r12_sch.pin_table_text()')
    parts, pins = read_netlist(project / 'schematic.net.xml')
    issues += contract(parts, pins, project)
    seeded = seeds(parts, pins)
    seeded['bottom-side SMD land'] = side_seed(project)
    issues += [f'seed survived: {name}' for name, caught in seeded.items() if not caught]
    if (project / 'm3.kicad_dru').read_text() != gen.dru((gen.INPUT / 'm3.kicad_dru').read_text()):
        issues.append('DRU differs from the generator')
    for path in [project / n for n in gen.SHEET_FILES] + [project / 'm3.kicad_pro', project / 'schematic.net.xml']:
        if re.search(r'/Users/|/home/|/private/|[A-Z]:\\\\', path.read_text()):
            issues.append(f'absolute path in {path.name}')
    cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
    with tempfile.TemporaryDirectory(prefix='r12-sch-check-') as directory:
        work = Path(directory)
        erc = work / 'erc.json'
        subprocess.run([cli, 'sch', 'erc', '--severity-all', '--format', 'json', '-o', str(erc),
                        str(project / 'm3.kicad_sch')], check=True, capture_output=True, text=True)
        violations = [v for sheet in json.loads(erc.read_text())['sheets'] for v in sheet['violations']]
        issues += [f'ERC {v["type"]}: {v.get("description", "")}' for v in violations]
        replay = work / 'replay'
        gen.build(replay)
        for file in [replay / n for n in gen.SHEET_FILES] + [replay / 'schematic.net.xml', replay / 'm3.kicad_dru',
                                                             replay / 'm3.kicad_pro', replay / 'sym-lib-table',
                                                             replay / 'fp-lib-table']:
            if _stamp_free(file) != _stamp_free(project / file.name):
                issues.append(f'nonreproducible generated artifact: {file.name}')
        fresh = work / 'fresh'
        fresh.mkdir()
        for file in project.glob('*.kicad_sch'):
            shutil.copy2(file, fresh / file.name)
        shutil.copytree(project / 'kilib', fresh / 'kilib')
        for name in ('sym-lib-table', 'fp-lib-table', 'm3.kicad_pro'):
            shutil.copy2(project / name, fresh / name)
        gen.sch.export_netlist(fresh)
        p2, n2 = read_netlist(fresh / 'schematic.net.xml')
        issues += ['fresh schematic export: ' + i for i in contract(p2, n2)]
    return {'ok': not issues, 'issues': issues, 'components': len(parts), 'pins': len(pins),
            'erc_violations': len(violations), 'seeded_faults': seeded,
            'netlist_sha256': hashlib.sha256((project / 'schematic.net.xml').read_bytes()).hexdigest(),
            'scope': 'schematic, parts, exact pin nets, ball map, one-side lands and DRU; no PCB / physical qualification'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--project', required=True, type=Path)
    ap.add_argument('--json', type=Path)
    args = ap.parse_args()
    report = check(args.project.resolve())
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'seeded_faults'}, indent=2))
    print(f'seeded faults caught: {sum(report["seeded_faults"].values())} / {len(report["seeded_faults"])}')
    raise SystemExit(0 if report['ok'] else 1)


if __name__ == '__main__':
    main()
