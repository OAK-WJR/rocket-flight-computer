#!/usr/bin/env python3
"""Check the M3-ASSY-R11 schematic against R10's pinned netlist, circuit.json and pin_table.tsv.

usage: KiCad python3 -I -B m3_design/r11_sch_check.py --project m3_design/r11 [--json FILE]
Checks (D-R11-01: R10's circuit unchanged in nets and values):
  * every R10 (ref, pin) net carried to R11 through the declared pin maps (U1 LQFP100 -> TFBGA100 balls, J9 4 -> 6
    contacts), the only other pin changes being U1's VREF+ (no ball) and PDR_ON (F7, 3V3);
  * every U1 ball against pin_table.tsv (r11_ball / r11_net) and the package supply balls;
  * every part's symbol, value, footprint, LCSC / Manufacturer / Manufacturer Part and assembly flags against R10 or
    circuit.json; one footprint and one part number per LCSC code; every footprint present in the project's kilib;
  * R10's safety, single-switch, always-on port, SD and camera-isolation contracts with R11's ball keys, the R11
    connector pin contracts and terminal pin names;
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
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r11_sch as gen

B = gen.BALL


def read_netlist(path):
    root = ET.parse(path).getroot()
    parts = {c.get('ref'): c for c in root.findall('./components/comp')}
    pins = {(p.get('ref'), p.get('pin')): None if n.get('name').startswith('unconnected-') else n.get('name')
            for n in root.findall('./nets/net') for p in n.findall('node')}
    return parts, pins


def read_pin_names(path):
    names = {}
    for net in ET.parse(path).getroot().findall('./nets/net'):
        for node in net.findall('node'):
            function, suffix = node.get('pinfunction') or '', '_' + node.get('pin')
            names[node.get('ref'), node.get('pin')] = function[:-len(suffix)] if function.endswith(suffix) else function
    return names


PORT_PIN_NAMES = {'1': '4V8', '2': 'GND', '3': 'TXO', '4': 'RXI'}
CAMERA_PIN_NAMES = {'1': '5V_OUT', '2': '5V_OUT', '3': 'GND', '4': 'GND', '5': 'RX_FROM_CAMERA_TX', '6': 'TX_TO_CAMERA_RX'}
TERMINAL_PIN_NAMES = {'J410': PORT_PIN_NAMES, 'J420': PORT_PIN_NAMES, 'J440': PORT_PIN_NAMES, 'J9': CAMERA_PIN_NAMES}


def terminal_pin_issues(names):
    issues = []
    for ref, want in TERMINAL_PIN_NAMES.items():
        got = {pin: names.get((ref, pin)) for pin in want}
        if got != want or any(k[0] == ref and k[1] not in want for k in names):
            issues.append(f'{ref}: pin names {got}, expected {want} (REQUIREMENTS F10, D-R27-03, D-R11-05)')
    return issues


def name_seeds(names):
    mutations = {
        'port pins named as the camera terminal': lambda m: m.update({('J410', p): v for p, v in CAMERA_PIN_NAMES.items()}),
        'port TXO / RXI swapped': lambda m: m.update({('J440', '3'): 'RXI', ('J440', '4'): 'TXO'}),
        'port supply named 5V OUT': lambda m: m.update({('J420', '1'): '5V_OUT'}),
        'camera GH RX / TX names swapped': lambda m: m.update({('J9', '5'): 'TX_TO_CAMERA_RX', ('J9', '6'): 'RX_FROM_CAMERA_TX'}),
    }
    results = {}
    for label, mutate in mutations.items():
        mutant = dict(names)
        mutate(mutant)
        results[label] = bool(terminal_pin_issues(mutant))
    return results


def flags(part):
    return {p.get('name') for p in part.findall('property')} & {'dnp', 'exclude_from_bom', 'exclude_from_pos_files',
                                                                 'exclude_from_board'}


def fields(part):
    return {f.get('name'): f.text or '' for f in part.findall('./fields/field')}


def expected():
    """R10's parts and pins carried to R11: {ref: spec}, {(ref, pin): net}."""
    data = gen.circuit()
    r10_parts, r10_pins = gen.r10_netlist()
    specs = gen.specs(data)
    parts = {}
    for ref, comp in r10_parts.items():
        f = fields(comp)
        spec = {'lib': 'M3:' + comp.find('libsource').get('part'), 'value': comp.findtext('value'),
                'footprint': comp.findtext('footprint'), 'flags': flags(comp),
                'fields': {k: f.get(k, '') for k in ('LCSC', 'Manufacturer', 'Manufacturer Part')}}
        if ref in specs:
            s = specs[ref]
            spec.update(lib=s['lib'] or spec['lib'], value=s['props']['Value'], footprint=s['props']['Footprint'],
                        fields={k: s['props'][k] or '' for k in ('LCSC', 'Manufacturer', 'Manufacturer Part')})
            spec['flags'] = set(spec['flags'])
            if not s['in_bom']:
                spec['flags'].add('exclude_from_bom')
            if not s['in_pos_files']:
                spec['flags'].add('exclude_from_pos_files')
        parts[ref] = spec
    pins = {}
    for (ref, pin), net in r10_pins.items():
        if ref == 'U1':
            if pin == gen.VREF_PIN:
                continue
            pins[ref, B[pin]] = net
            if pin in gen.R11_REPIN:                                  # D-R11-41 / -42: the net moves ball, not name
                new = gen.R11_REPIN[pin][0]
                pins[ref, B[pin]] = None if new == 'NC' else new
        elif ref in data['pin_maps'] and isinstance(data['pin_maps'][ref], dict):
            for new in data['pin_maps'][ref][pin]:
                pins[ref, new] = net
        else:
            pins[ref, pin] = net
    pins['U1', gen.PDR_ON] = gen.PDR_ON_NET
    # D-R11-86: R11's only netlist additions (circuit.json added_parts / net_changes)
    for ref, changes in data.get('net_changes', {}).items():
        for pin, net in changes.items():
            assert (ref, pin) in pins, f'net_changes names {ref}.{pin}, not an R10 pin'
            pins[ref, pin] = net
    for ref, entry in data.get('added_parts', {}).items():
        assert ref not in parts, f'added part {ref} is an R10 reference'
        s = gen.added_spec(data, entry)
        parts[ref] = {'lib': s['lib'], 'value': s['props']['Value'], 'footprint': s['props']['Footprint'],
                      'flags': set(), 'fields': {k: s['props'][k] or '' for k in ('LCSC', 'Manufacturer', 'Manufacturer Part')}}
        for pin, net in entry['nets'].items():
            pins[ref, pin] = net
    return parts, pins


def assembly_groups(parts):
    groups, issues = {}, []
    for ref, part in parts.items():
        if not ref or ref.startswith('#') or 'exclude_from_bom' in flags(part):
            continue
        f = fields(part)
        if f.get('LCSC'):
            key = ('owner' if 'dnp' in flags(part) else 'JLC', f['LCSC'])
            groups.setdefault(key, []).append((ref, (part.findtext('footprint') or '').split(':')[-1], f.get('Manufacturer Part', '')))
        elif 'exclude_from_bom' not in flags(part):
            issues.append(f'{ref}: in the BOM without an LCSC code')
    for (bom, code), members in sorted(groups.items()):
        fps, mpns = {m[1] for m in members}, {m[2] for m in members}
        if len(fps) > 1 or len(mpns) > 1:
            issues.append(f'BOM contract: LCSC {code} on several footprints {sorted(fps)} or part numbers {sorted(mpns)} '
                          f'({",".join(sorted(m[0] for m in members))}; {bom} BOM)')
    return issues


def ball(pin):
    return B[pin]


def contract(actual_parts, actual_pins, project=None):
    want_parts, want_pins = expected()
    data = gen.circuit()
    issues = assembly_groups(actual_parts)
    # R10 contracts (r10_sch_check.contract), U1 keys re-keyed to balls.
    removed = {'J123', 'R160', 'R161', 'C160', 'D122', 'TP84', 'TP85', 'TP86', 'TP87', 'TP89', 'TP92',
               'U412', 'U422', 'R443', 'R453', 'C441', 'C442', 'C451', 'C452',
               'U410', 'U420', 'U411', 'U421', 'R410', 'R411', 'R412', 'R420', 'R421', 'R422',
               'R442', 'R452', 'C440', 'C443', 'C450', 'C453', 'R177', 'R124', 'R125', 'R182', 'R172', 'C122', 'R168',
               'R170', 'J124'}
    if removed & actual_parts.keys():
        issues.append(f'AUD-4 / AUD-5 / AUD-8: obsolete parts remain: {sorted(removed & actual_parts.keys())}')
    if 'PYRO1_BUS' in actual_pins.values():
        issues.append('single screw switch: PYRO1_BUS must be merged into RAW_ACT')
    if any(str(net).startswith('RAW_ACT_SENSE') for net in actual_pins.values()):
        issues.append('AVA: ARM1_SENSE is the sole RAW_ACT bus divider; duplicate RAW_ACT_SENSE remains')
    safety_pins = {('R134', '2'): 'RAW_ACT', ('R132', '1'): 'RAW_ACT', ('U1', ball('16')): 'ACT_EN_MCU',
                   ('R122', '1'): 'ACT_EN_MCU', ('R122', '2'): 'ACT_EN', ('R123', '1'): 'ACT_EN',
                   ('R123', '2'): 'GND', ('Q122', '1'): 'ACT_EN', ('Q122', '2'): 'GND',
                   ('U1', ball('3')): 'PYRO1_GATE_N', ('R127', '1'): 'PYRO1_GATE_N', ('R126', '1'): 'PYRO1_GATE_N',
                   ('R126', '2'): 'PYRO1_GATE', ('R128', '1'): 'PYRO1_GATE', ('C126', '1'): 'PYRO1_GATE'}
    for key, net in safety_pins.items():
        if actual_pins.get(key) != net:
            issues.append(f'safety (AGENTS 2.4, single screw switch): {key[0]}.{key[1]} must be {net}')
    interface_pins = {('J410', '1'): 'PORT_4V8', ('J420', '1'): 'PORT_4V8', ('J440', '1'): 'PORT_4V8',
                      ('R440', '2'): 'GPS_RX_MCU', ('R441', '1'): 'GPS_TX_MCU',
                      ('R450', '2'): 'RADIO_RX_MCU', ('R451', '1'): 'RADIO_TX_MCU',
                      ('R470', '2'): 'AUX_RX_MCU', ('R471', '1'): 'AUX_TX_MCU',
                      ('U1', ball('55')): 'GPS_TX_MCU', ('U1', ball('56')): 'GPS_RX_MCU',
                      ('U1', ball('63')): 'AUX_TX_MCU', ('U1', ball('64')): 'AUX_RX_MCU',
                      ('U1', ball('33')): 'ARM1_SENSE', ('U1', ball('34')): None,
                      ('U1', ball('78')): 'SD_SCK', ('U1', ball('79')): 'SD_MISO',
                      ('U1', ball('80')): 'SD_MOSI', ('U1', ball('81')): 'SD_CS'}
    for key, net in interface_pins.items():
        if actual_pins.get(key) != net:
            issues.append(f'AVA port / SD contract: {key[0]}.{key[1]} must be {net}')
    # R11 connector and package contracts (D-R11-04 / -05).
    r11_pins = {('J9', '1'): 'CAM_5V', ('J9', '2'): 'CAM_5V', ('J9', '3'): 'GND', ('J9', '4'): 'GND',
                ('J9', '5'): 'CAM_RX_WIRE', ('J9', '6'): 'CAM_TX_WIRE',
                ('J122', '1'): 'SERVO1_OUT', ('J122', '2'): 'SERVO2_OUT', ('J122', '3'): 'SERVO3_OUT',
                ('J122', '4'): 'SERVO4_OUT', ('J122', '5'): 'GND',
                ('J400', '1'): 'BAT_SW_SOURCE', ('J400', '2'): 'BAT_SW_RETURN',
                ('J1', '1'): 'BAT_IN', ('J1', '2'): 'GND', ('J121', '1'): 'PYRO1_OUT', ('J121', '2'): 'PYRO1_IGN',
                ('U1', 'F7'): '3V3', ('U1', 'F4'): '3V3', ('U1', 'F6'): '3V3', ('U1', 'H1'): '3V3A', ('U1', 'G1'): 'GND',
                ('U1', 'B2'): '3V3', ('U1', 'E1'): 'NRST', ('U1', 'D5'): 'BOOT0', ('U1', 'E7'): 'VCAP2',
                ('U1', 'F8'): 'VCAP1'}
    for ref in ('J410', 'J420', 'J440'):
        r11_pins[ref, '2'] = 'GND'
    for key, net in r11_pins.items():
        if actual_pins.get(key) != net:
            issues.append(f'R11 connector / package contract: {key[0]}.{key[1]} must be {net}')
    for ball_name in ('C2', 'E4', 'E5', 'E6', 'J1'):
        if actual_pins.get(('U1', ball_name)) != 'GND':
            issues.append(f'U1.{ball_name} (VSS) must be GND')
    for ball_name in ('D2', 'F5', 'K1'):
        if actual_pins.get(('U1', ball_name)) != '3V3':
            issues.append(f'U1.{ball_name} (VDD) must be 3V3')
    u1 = {k[1] for k in actual_pins if k[0] == 'U1'}
    if u1 != set(B.values()) | {gen.PDR_ON}:
        issues.append(f'U1 balls: missing {sorted(set(B.values()) | {gen.PDR_ON} - u1)}, extra {sorted(u1 - set(B.values()) - {gen.PDR_ON})}')
    for row in gen.read_pin_table():
        if row['r11_ball'] == '-':
            continue
        want = None if row['r11_net'] == 'NC' else row['r11_net']
        if actual_pins.get(('U1', row['r11_ball'])) != want:
            issues.append(f'U1.{row["r11_ball"]} ({row["port"]}): {actual_pins.get(("U1", row["r11_ball"]))!r}, '
                          f'pin_table.tsv {want!r}')
    for ref in ('J1', 'J121'):
        if ref in actual_parts and not {'exclude_from_bom', 'exclude_from_pos_files'} <= flags(actual_parts[ref]):
            issues.append(f'{ref}: wire pads must be out of the BOM and CPL (D-R11-05)')
    # Exact parts and pins.
    if set(actual_parts) != set(want_parts):
        issues.append(f'component set: missing {sorted(set(want_parts) - set(actual_parts))}; '
                      f'extra {sorted(set(actual_parts) - set(want_parts))}')
    for key in sorted(set(want_pins) | set(actual_pins)):
        if key not in actual_pins or key not in want_pins or actual_pins.get(key) != want_pins.get(key):
            issues.append(f'{key[0]}.{key[1]}: {actual_pins.get(key)!r}, expected {want_pins.get(key)!r}')
    for ref in sorted(set(want_parts) & set(actual_parts)):
        a, want = actual_parts[ref], want_parts[ref]
        for key in ('value', 'footprint'):
            if a.findtext(key) != want[key]:
                issues.append(f'{ref}: {key} {a.findtext(key)!r}, expected {want[key]!r}')
        if 'M3:' + a.find('libsource').get('part') != want['lib']:
            issues.append(f'{ref}: symbol differs')
        f = fields(a)
        for key in ('LCSC', 'Manufacturer', 'Manufacturer Part'):
            if f.get(key, '') != want['fields'][key]:
                issues.append(f'{ref}: {key} {f.get(key, "")!r}, expected {want["fields"][key]!r}')
        if 'LCSC Part' in f and f['LCSC Part'] != f.get('LCSC', ''):           # D-R11-78, AGENTS 3
            issues.append(f'{ref}: LCSC Part {f["LCSC Part"]!r} contradicts LCSC {f.get("LCSC", "")!r}')
        if flags(a) != want['flags']:
            issues.append(f'{ref}: assembly flags {sorted(flags(a))}, expected {sorted(want["flags"])}')
        if project is not None:
            name = (a.findtext('footprint') or '').split(':')[-1]
            if not (project / 'kilib/rocket.pretty' / (name + '.kicad_mod')).exists():
                issues.append(f'{ref}: footprint {name} missing from the project kilib')
    # circuit.json internal agreement (AGENTS 3: LCSC / Manufacturer / Manufacturer Part agree, one per code).
    for ref, entry in data['parts'].items():
        code = entry.get('lcsc')
        if code and code not in data['catalog']:
            issues.append(f'circuit.json {ref}: LCSC {code} not in the catalog')
    return issues


def seeds(parts, pins):
    def drop_flag(ref, name):
        return lambda p, n: [p[ref].remove(e) for e in p[ref].findall('property') if e.get('name') == name]

    def set_field(ref, name, value):
        def f(p, n):
            for e in p[ref].findall('./fields/field'):
                if e.get('name') == name:
                    e.text = value
        return f
    mutations = {
        'C92 split assembly footprint': lambda p, n: setattr(p['C92'].find('footprint'), 'text', 'rocket:C_0603_1608Metric'),
        '0402 part on its R10 0603 land': lambda p, n: setattr(p['R80'].find('footprint'), 'text', 'rocket:R_0603_1608Metric'),
        'AUD-4 pull-pin restored': lambda p, n: p.update({'J123': copy.deepcopy(p['J400'])}),
        'AUD-4 pull-pin MCU net restored': lambda p, n: n.update({('U1', ball('7')): 'PULLPIN'}),
        'AUD-5 removed test pad restored': lambda p, n: p.update({'TP92': copy.deepcopy(p['TP74'])}),
        'AVA obsolete GPS translator restored': lambda p, n: p.update({'U411': copy.deepcopy(p['U12'])}),
        'AVA duplicate bus divider restored': lambda p, n: p.update({'R124': copy.deepcopy(p['R132'])}),
        'audit2 bus ADC tail restored': lambda p, n: n.update({('U1', ball('33')): 'ARM1_SENSE_MCU'}),
        'AVA duplicate bus ADC restored': lambda p, n: n.update({('U1', ball('34')): 'RAW_ACT_SENSE_MCU'}),
        'obsolete ARM terminal restored': lambda p, n: p.update({'J124': copy.deepcopy(p['J400'])}),
        'obsolete separate pyro bus': lambda p, n: n.update({('R134', '2'): 'PYRO1_BUS'}),
        'pyro feed directly from pack': lambda p, n: n.update({('R134', '2'): 'BAT_IN'}),
        'bus sense directly from pack': lambda p, n: n.update({('R132', '1'): 'BAT_IN'}),
        'load switch follows logic rail': lambda p, n: n.update({('R122', '1'): 'RAW_PROTECTED'}),
        'load switch enable pull-down missing': lambda p, n: p.pop('R123'),
        'independent load switch MCU ball missing': lambda p, n: n.update({('U1', 'F2'): None}),
        'fire command on the wrong ball': lambda p, n: n.update({('U1', 'C3'): None, ('U1', 'D3'): 'PYRO1_GATE_N'}),
        'fire gate pull-down removed': lambda p, n: p.pop('R127'),
        'servo signal terminal powered': lambda p, n: n.update({('J122', '2'): 'RAW_ACT'}),
        'radio USB injection bypass': lambda p, n: n.update({('U1', ball('51')): 'RADIO_RX_WIRE'}),
        'GPS always-on feed split': lambda p, n: n.update({('J410', '1'): 'GPS_4V8'}),
        'AUX TX series bypass': lambda p, n: n.update({('U1', ball('63')): 'AUX_TX_WIRE'}),
        'AUX port ESD clamp removed': lambda p, n: p.pop('D441'),
        'J400 contact clamp removed': lambda p, n: p.pop('D402'),
        'J400 contact clamp return off GND': lambda p, n: n.update({('D402', '2'): 'BAT_ENABLE'}),
        'retained camera isolation removed': lambda p, n: p.pop('U12'),
        'pyro load switch removed': lambda p, n: p.pop('Q120'),
        'pyro gate capacitor excluded': lambda p, n: ET.SubElement(p['C126'], 'property', name='exclude_from_bom'),
        'shorted igniter limiter DNP': lambda p, n: ET.SubElement(p['R134'], 'property', name='dnp'),
        'microSD MOSI MISO swapped': lambda p, n: n.update({('J430', '3'): 'SD_MISO', ('J430', '7'): 'SD_MOSI'}),
        'microSD unused DAT2 floating': lambda p, n: p.pop('R464'),
        'QSPI primary logger removed': lambda p, n: p.pop('U3'),
        'LCSC Part contradicts LCSC': set_field('R85', 'LCSC Part', 'C137691'),   # D-R11-78
        # R11 (D-R11-04 / -05)
        'PDR_ON tied low': lambda p, n: n.update({('U1', 'F7'): 'GND'}),
        'PDR_ON floating': lambda p, n: n.pop(('U1', 'F7')),
        'VDDLDO floating': lambda p, n: n.update({('U1', 'F4'): None}),
        'VDD33USB on VBUS': lambda p, n: n.update({('U1', 'F6'): 'VBUS'}),
        'VDDA ball on 3V3': lambda p, n: n.update({('U1', 'H1'): '3V3'}),
        'LQFP pin number left on U1': lambda p, n: n.update({('U1', '20'): '3V3A'}),
        'VCAP balls swapped onto one cap': lambda p, n: n.update({('U1', 'E7'): 'VCAP1'}),
        'camera supply on one contact': lambda p, n: n.update({('J9', '2'): None}),
        'camera RX / TX swapped': lambda p, n: n.update({('J9', '5'): 'CAM_TX_WIRE', ('J9', '6'): 'CAM_RX_WIRE'}),
        'camera GND on one contact': lambda p, n: n.update({('J9', '4'): 'CAM_5V'}),
        'port TXO / RXI swapped': lambda p, n: n.update({('J420', '3'): 'RADIO_RX_WIRE', ('J420', '4'): 'RADIO_TX_WIRE'}),
        'pyro pads OUT / IGN swapped': lambda p, n: n.update({('J121', '1'): 'PYRO1_IGN', ('J121', '2'): 'PYRO1_OUT'}),
        'battery pads in the JLC BOM': drop_flag('J1', 'exclude_from_bom'),
        'pyro pads in the CPL': drop_flag('J121', 'exclude_from_pos_files'),
        'port back on a DB125 land': lambda p, n: setattr(p['J410'].find('footprint'), 'text', 'rocket:M3_DB125_4P_GN'),
        'MCU on the LQFP land': lambda p, n: setattr(p['U1'].find('footprint'), 'text', 'rocket:LQFP-100_L14.0-W14.0-P0.50-LS16.0-BL'),
        'LCSC code and part number disagree': set_field('R81', 'Manufacturer Part', '0402WGF4703TCE'),
        'R10 LCSC code left on a 0402 part': set_field('C90', 'LCSC', 'C14663'),
        'value changed': lambda p, n: setattr(p['R86'].find('value'), 'text', '80.6k 1%'),
    }
    results = {}
    for label, mutate in mutations.items():
        p, n = copy.deepcopy(parts), dict(pins)
        mutate(p, n)
        results[label] = bool(contract(p, n))
    return results


def _stamp_free(path):
    data = path.read_bytes()
    return re.sub(rb'<tool>[^<]*</tool>', b'<tool/>', data) if path.name.endswith('.net.xml') else data


def check(project):
    gen.source_check()
    issues = []
    if (gen.DESIGN / 'pin_table.tsv').read_text() != gen.pin_table_text():
        issues.append('pin_table.tsv differs from r11_sch.BALL / R10 pin table')
    parts, pins = read_netlist(project / 'schematic.net.xml')
    issues += contract(parts, pins, project)
    seeded = seeds(parts, pins)
    names = read_pin_names(project / 'schematic.net.xml')
    issues += terminal_pin_issues(names)
    seeded.update(name_seeds(names))
    issues += [f'seed survived: {name}' for name, caught in seeded.items() if not caught]
    if (project / 'm3.kicad_dru').read_text() != gen.dru((gen.INPUT / 'm3.kicad_dru').read_text()):
        issues.append('DRU differs from the generator')
    for path in [project / n for n in gen.SHEETS] + [project / 'm3.kicad_pro', project / 'schematic.net.xml']:
        if re.search(r'/Users/|/home/|[A-Z]:\\\\', path.read_text()):
            issues.append(f'absolute path in {path.name}')
    cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
    with tempfile.TemporaryDirectory(prefix='r11-sch-check-') as directory:
        work = Path(directory)
        erc = work / 'erc.json'
        subprocess.run([cli, 'sch', 'erc', '--severity-all', '--format', 'json', '-o', str(erc),
                        str(project / 'm3.kicad_sch')], check=True, capture_output=True, text=True)
        violations = [v for sheet in json.loads(erc.read_text())['sheets'] for v in sheet['violations']]
        issues += [f'ERC {v["type"]}: {v.get("description", "")}' for v in violations]
        replay = work / 'replay'
        gen.build(replay)
        for file in [replay / n for n in gen.SHEETS] + [replay / 'schematic.net.xml', replay / 'm3.kicad_dru',
                                                         replay / 'm3.kicad_pro', replay / 'sym-lib-table',
                                                         replay / 'fp-lib-table']:
            if _stamp_free(file) != _stamp_free(project / file.name):
                issues.append(f'nonreproducible generated artifact: {file.name}')
        fresh = work / 'fresh'
        fresh.mkdir()
        for file in project.glob('*.kicad_sch'):
            shutil.copy2(file, fresh / file.name)
        for name in ('kilib', ):
            shutil.copytree(project / name, fresh / name)
        for name in ('sym-lib-table', 'fp-lib-table', 'm3.kicad_pro'):
            shutil.copy2(project / name, fresh / name)
        gen.sch.export_netlist(fresh)
        p2, n2 = read_netlist(fresh / 'schematic.net.xml')
        issues += ['fresh schematic export: ' + i for i in contract(p2, n2)]
        issues += ['fresh schematic export: ' + i for i in terminal_pin_issues(read_pin_names(fresh / 'schematic.net.xml'))]
    return {'ok': not issues, 'issues': issues, 'components': len(parts), 'pins': len(pins),
            'erc_violations': len(violations), 'seeded_faults': seeded,
            'netlist_sha256': hashlib.sha256((project / 'schematic.net.xml').read_bytes()).hexdigest(),
            'scope': 'schematic, parts, exact pin nets, ball map and DRU; no PCB / physical qualification'}


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
