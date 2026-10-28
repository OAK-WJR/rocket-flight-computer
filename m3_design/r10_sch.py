#!/usr/bin/env python3
"""Generate the R10 sheets, netlist and DRU from hash-pinned R9 inputs.

No version-control operations. --out is required; the checked-in CAD is never an
implicit output. Part selection/net maps live in sources/r10_design/circuit.json.
The source manifest is checked before every generation, including build replays.
"""
import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r7_sch as sch
import r8_sch as pins

PROJECT = HERE / 'assembly_review'
SOURCE = PROJECT / 'sources/r10_design'
BASE = SOURCE / 'r9_input'
NS = uuid.UUID('1af735a9-7221-5413-9d5c-c1284216d384')
REV = 'M3-ASSY-R10'
SILK_CLEARANCE = 0.15           # mm: m3.kicad_pro min_silk_clearance (JLC silkscreen clearance; R9 had 0)
KEEP_RULES = ('General copper to hole clearance', 'HRO M-12 internal SMD lands to locating holes',
              'Small GND pad thermal relief', 'Tag-Connect contact to foreign copper',
              'R9 bare test pads to foreign copper')


def source_check():
    data = json.loads((BASE / 'manifest.json').read_text())
    for name, digest in data['files'].items():
        assert hashlib.sha256((BASE / name).read_bytes()).hexdigest() == digest, f'R9 source changed: {name}'


def circuit():
    return json.loads((SOURCE / 'circuit.json').read_text())


def uid(key):
    return str(uuid.uuid5(NS, key))


def baseline():
    root = ET.parse(BASE / 'schematic.net.xml').getroot()
    parts = {c.get('ref'): c for c in root.findall('./components/comp')}
    nets = {(p.get('ref'), p.get('pin')): None if n.get('name').startswith('unconnected-') else n.get('name')
            for n in root.findall('./nets/net') for p in n.findall('node')}
    return parts, nets


def specification(component, nets):
    fields = {f.get('name'): f.text or '' for f in component.findall('./fields/field')
              if f.get('name') not in ('Footprint', 'Description', 'LCSC Part')}
    return dict(lib='M3:' + component.find('libsource').get('part'), value=component.findtext('value'),
                footprint=component.findtext('footprint'), fields=fields, nets=nets, kind='fit')


def part_tuple(spec):
    return spec['lib'], spec['value'], spec['footprint'], spec['fields'], spec['nets'], spec.get('kind', 'fit')


def sheet_id(text):
    read, _, _ = sch._reader()
    return read(text).children('uuid')[0].items[1].atom


def instance(text, ref):
    read, _, _ = sch._reader()
    for node in read(text).children('symbol'):
        if any(p.items[1].atom == 'Reference' and p.items[2].atom == ref for p in node.children('property')):
            return node
    raise AssertionError(f'missing symbol {ref}')


def points(text, ref, library):
    n = instance(text, ref)
    at = n.children('at')[0].items
    x, y, angle = [float(v.atom) for v in at[1:4]]
    assert angle == 0, f'{ref}: nonzero schematic angle not supported'
    lib = n.children('lib_id')[0].items[1].atom.split(':')[1]
    return {p: (round(x + px, 2), round(y - py, 2), a)
            for p, (px, py, a) in sch._lib_pins(library, lib).items()}


def remove(text, ref, library):
    pts = points(text, ref, library)
    text = sch.disconnect(text, {v[:2] for v in pts.values()})
    node = instance(text, ref)
    return text[:node.start] + text[node.end:]


def embed(text, library, names):
    read, patch, _ = sch._reader()
    root = read(text)
    libs = root.children('lib_symbols')[0]
    known = {n.items[1].atom for n in libs.children('symbol')}
    extra = ''.join(sch._embed(library, n) for n in sorted(names) if 'M3:' + n not in known)
    if extra:
        text = patch(text, [(libs.end - 1, libs.end - 1, extra)])
    return text


def sheet_path(name):
    """The hierarchical instance path of sheet file `name`: the root uuid, then the root's sheet-symbol uuid for that
    file (not the sub-sheet file's own uuid; they differ for camera_power, battery_entry and camera_uart, and a symbol
    instance on the wrong path breaks the board's schematic parity)."""
    text = (BASE / 'm3.kicad_sch').read_text()
    for m in re.finditer(r'\(sheet\n', text):
        block = text[m.start():sch.close_paren(text, m.start())]
        if f'(property "Sheetfile" "{name}"' in block:
            return '/' + sch.ROOT + '/' + re.search(r'\(uuid ([0-9a-f-]+)\)', block).group(1)
    raise AssertionError(f'no sheet symbol for {name}')


SHEET = {}


def add(text, library, ref, spec, x, y):
    sch.RF_PARTS = {ref: part_tuple(spec)}
    sch.FLAGS = {}
    sch.NS = NS
    text = embed(text, library, {spec['lib'].split(':')[1]})
    path = SHEET['path']
    return sch.insert(text, sch._sym(library, ref, x, y, path))


def replace(text, library, ref, spec):
    node = instance(text, ref)
    x, y = sch._xy(node)
    old_uuid = node.children('uuid')[0].items[1].atom
    text = add(remove(text, ref, library), library, ref, spec, x, y)
    # Existing board/schematic identity remains stable even if the symbol changes.
    return text.replace('(uuid ' + uid(ref) + ')', '(uuid ' + old_uuid + ')')


def change_pin(text, ref, pin, net, library):
    x, y, angle = points(text, ref, library)[pin]
    text = sch.disconnect(text, {(x, y)})
    if net is None:
        return sch.insert(text, sch.nc(x, y, f'{ref}:r10:nc{pin}'))
    dx, dy = {0: (-5.08, 0), 180: (5.08, 0), 90: (0, 5.08), 270: (0, -5.08)}[int(angle)]
    bx, by = round(x + dx, 2), round(y + dy, 2)
    return sch.insert(text, sch.wire(x, y, bx, by, f'{ref}:r10:w{pin}') +
                      sch.glabel(net, bx, by, f'{ref}:r10:l{pin}', 180 if dx > 0 else 0,
                                 'left' if dx > 0 else 'right'))


def replace_notes(text, lines):
    read, patch, _ = sch._reader()
    text = patch(text, [(n.start, n.end, '') for n in read(text).children('text')])
    return sch.insert(text, ''.join(sch.note(line, 20.32, 15.24 + i * 5.08, f'note:{sheet_id(text)}:{i}')
                                   for i, line in enumerate(lines)))


def generated_sheet(old, library, specs, title, page, notes):
    sid = sheet_id(old)
    names = sorted({v['lib'].split(':')[1] for v in specs.values()})
    text = (f'(kicad_sch\n\t(version 20250114)\n\t(generator "m3_r10")\n\t(uuid {sid})\n\t(paper "A1")\n'
            f'\t(title_block (title "{title}") (date "2026-10-26") (rev "{REV}"))\n\t(lib_symbols\n' +
            ''.join(sch._embed(library, n) for n in names) + '\t)\n')
    sch.RF_PARTS = {ref: part_tuple(spec) for ref, spec in specs.items()}
    sch.FLAGS = {}
    # A regular, deliberately generous schematic grid; no symbol/label collisions.
    for i, (ref, spec) in enumerate(specs.items()):
        text += sch._sym(library, ref, 86.36 + 139.7 * (i % 5), 88.9 + 48.26 * (i // 5), SHEET['path'])
    for i, line in enumerate(notes):
        text += sch.note(line, 20.32, 15.24 + i * 5.08, f'note:{sid}:{i}')
    return text + f'\t(sheet_instances (path "/" (page "{page}"))))\n'


def dru(text):
    rules = []
    for m in re.finditer(r'\(rule "([^"]+)"', text):
        if m.group(1) in KEEP_RULES:
            rules.append(text[m.start():sch.close_paren(text, m.start())])
    assert len(rules) == len(KEEP_RULES)
    return ('(version 1)\n# R10 plan section 2 item 1: board-default copper clearance, no pyro/RF spacing overrides.\n'
            '# Functional ARM break, reset safety and J124 physical pad gap remain independently checked.\n' +
            '\n\n'.join(rules) + '\n')


def build(out, netlist=True):
    source_check()
    data = circuit()
    assert data['status'] == 'frozen', 'circuit.json not frozen; do not generate incomplete hardware'
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if out != PROJECT.resolve():
        shutil.copytree(PROJECT / 'kilib', out / 'kilib', dirs_exist_ok=True)
        for name in ('sym-lib-table', 'fp-lib-table'):
            shutil.copy2(PROJECT / name, out / name)
    # R9's project settings with one change (R10_DECISIONS D-R3, R3-MFG-02): the board-setup silkscreen clearance is
    # JLC's 0.15 mm instead of 0, so DRC's silk_overlap test holds every silkscreen item 0.15 mm from every other one
    # (silkscreen to pad openings is r10_post.py's polygon assertion: KiCad's silk_over_copper tests overlap only)
    pro = (BASE / 'm3.kicad_pro').read_text()
    assert pro.count('"min_silk_clearance": 0.0,') == 1, 'R9 project settings changed: min_silk_clearance'
    pro = pro.replace('"min_silk_clearance": 0.0,', f'"min_silk_clearance": {SILK_CLEARANCE},')
    (out / 'm3.kicad_pro').write_text(pro)
    library_path = out / 'kilib/m3.kicad_sym'
    library = library_path.read_text()
    import r10_parts
    if '(symbol \"PortLDO\"' not in library:
        library = library.rstrip()[:-1] + r10_parts.port_ldo_symbol() + '\n)\n'
        library = library.replace('M3_OSCON_F12 CAP-SMD_BD8.0*', 'M3_OSCON_F12 CAP-SMD_BD8.0* M3_MA_8x10')
    library_path.write_text(library)
    sch.NS = NS
    pins.NS = NS
    originals, nets = baseline()
    changed = data['parts']
    replacements = data['replacements']
    removed = set(data['removed_refs'])
    rows = list(csv.DictReader((SOURCE / 'pin_table.tsv').open(), delimiter='\t'))
    pinmap = {r['pin']: (r['r9_net'], r['r10_net']) for r in rows}
    mcuchanges = {p: ns for p, ns in pinmap.items() if ns[0] != ns[1]}
    for file in sorted(BASE.glob('*.kicad_sch')):
        t = file.read_text()
        SHEET['path'] = None if file.name == 'm3.kicad_sch' else sheet_path(file.name)
        if file.name in ('telemetry.kicad_sch', 'camera_power.kicad_sch'):
            group = 'telemetry' if file.stem == 'telemetry' else 'power'
            specs = {ref: spec for ref, spec in changed.items() if data['sheets'][ref] == group}
            notes = data['notes'][group]
            t = generated_sheet(t, library, specs, data['titles'][group], '15' if group == 'telemetry' else '05', notes)
        else:
            for ref in sorted(removed):
                if sch.symbol_block(t, ref):
                    t = remove(t, ref, library)
            for ref, spec in replacements.items():
                if sch.symbol_block(t, ref):
                    t = replace(t, library, ref, spec)
            if file.name == 'mcu.kicad_sch':
                t = pins.t_mcu(t, library, pinmap, mcuchanges)
                # Remove obsolete RF and EXTI narrative; preserve every safety note.
                read, patch, _ = sch._reader()
                t = patch(t, [(n.start, n.end, '') for n in read(t).children('text')
                              if 'radio SPI2' in n.items[1].atom or 'R8 EXTI:' in n.items[1].atom])
                t = sch.insert(t, sch.note('R10: USART6 PC6/PC7 AF7 GPS; UART5 PB13/PB12 AF14 radio. Port EN and OE default low. EXTI10 GPS_FAULT_N; EXTI9 RADIO_FAULT_N; EXTI12 CAM_FAULT_N; EXTI4 LOGIC_SOURCE_ST (PA4), EXTI5 BAT_FAULT_N (PA5); VLOGIC_SENSE ADC on PA6 (D-R2-09). EXTI1 PE1 IMU_INT1 data-ready (R6-MCU-01).', 20.32, 259.08, 'mcu:r10:ports'))
            if file.name == 'servos.kicad_sch':
                for pin in ('2', '5', '8', '11'):
                    t = change_pin(t, 'J122', pin, None, library)
            if file.name == 'battery_entry.kicad_sch':
                t = add(t, library, 'J400', changed['J400'], 330.2, 238.76)
            if file.name == 'camera_uart.kicad_sch':
                for ref, y in (('D400', 228.6), ('D401', 251.46)):
                    t = add(t, library, ref, changed[ref], 330.2, y)
            if file.stem in data['notes']:
                t = replace_notes(t, data['notes'][file.stem])
        t = t.replace('(rev "M3-ASSY-R9")', f'(rev "{REV}")')
        # Root hierarchy names follow new sheet titles; their UUID/path never changes.
        if file.name == 'm3.kicad_sch':
            t = change_pin(t, '#FLG06', '1', 'PORT_5V3', library)
            t = t.replace('05 | Camera branch protection and regulator', data['titles']['power'])
            t = t.replace('15 | GNSS and telemetry radio (R7)', data['titles']['telemetry'])
        t = sch.refresh_embedded(t, library, 'PolarCap')
        t = re.sub(r'\n(?:\s*\n)+', '\n', t)
        assert t.count(f'(rev "{REV}")') == 1, file.name
        (out / file.name).write_text(t)
    (out / 'm3.kicad_dru').write_text(dru((BASE / 'm3.kicad_dru').read_text()))
    if netlist:
        sch.export_netlist(out)
    print(f'R10 schematic generated: {out}; 15 sheets, {len(changed)} new parts, {len(removed)} removals')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--no-netlist', action='store_true')
    args = parser.parse_args()
    build(args.out, not args.no_netlist)


if __name__ == '__main__':
    main()
