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


def symbol(library, ref, x, y, path):
    """Draw one lead per stacked pin position, keeping every electrical pin."""
    body = sch._sym(library, ref, x, y, path)
    lib, _, _, _, nets, _ = sch.RF_PARTS[ref]
    shared, redundant = {}, set()
    for num, (px, py, _) in sorted(sch._lib_pins(library, lib.split(':')[1]).items(),
                                  key=lambda item: (len(item[0]), item[0])):
        position = (px, py)
        if position in shared:
            assert nets[num] == nets[shared[position]], f'{ref}: stacked pins have different nets'
            redundant.update(uid(f'{ref}:{kind}{num}') for kind in ('w', 'l', 'nc'))
        else:
            shared[position] = num
    if not redundant:
        return body
    # PMOS_PDFN8 stacks S1-3 and D5-9. Separate identical wires/labels at
    # those points create four-way ERC junctions when a part is replaced.
    read, patch, _ = sch._reader()
    prefix = '(kicad_sch\n'
    text = prefix + body + ')'
    root = read(text)
    edits = [(n.start, n.end, '') for kind in ('wire', 'global_label', 'no_connect')
             for n in root.children(kind) if n.children('uuid')[0].items[1].atom in redundant]
    return patch(text, edits)[len(prefix):-1]


def add(text, library, ref, spec, x, y):
    sch.RF_PARTS = {ref: part_tuple(spec)}
    sch.FLAGS = {}
    sch.NS = NS
    text = embed(text, library, {spec['lib'].split(':')[1]})
    path = SHEET['path']
    return sch.insert(text, symbol(library, ref, x, y, path))


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


def replace_note(text, prefix, line, key):
    """R18: replace exactly one retained sheet note (matched by its opening words) in place, at its own position."""
    read, patch, _ = sch._reader()
    found = [n for n in read(text).children('text') if n.items[1].atom.startswith(prefix)]
    assert len(found) == 1, f'expected one note starting {prefix!r}, found {len(found)}'
    x, y = sch._xy(found[0])
    text = patch(text, [(found[0].start, found[0].end, '')])
    return sch.insert(text, sch.note(line, x, y, key))


def replace_once(text, old, new):
    assert text.count(old) == 1, f'expected one {old!r}'
    return text.replace(old, new)


# R18-REQ-01 / R18-MCU-03: the retained R8 MCU-sheet notes, rewritten from the R10 pin table (asserted below).
R10_MCU_NOTES = {
    'R8: camera enable': ('R10: camera enable CAM_PWR_EN on PE11 / pin41, fault input CAM_FAULT_N (EXTI12) on PE12 / '
                          'pin42 (GPIO only, SPI4 never enabled); swapped from R8 for routing (D-R2-07); no actuation '
                          'changes.'),
    'R8 follow-on moves': ('R10 MCU map (pin_table.tsv r10_net is the sole authority): BUZZ_DRV PC14; LOGIC_SOURCE_ST '
                           'PA4, BAT_FAULT_N PA5 (D-R2-09); camera UART7 PE7 RX / PE8 TX, CAM_UART_OE PE9; radio UART5 '
                           'PB12 RX / PB13 TX (J420); GPS USART3 PD8 TX / PD9 RX (J410) and AUX USART6 PC6 TX / PC7 RX (J440, D-R19-14); '
                           'SD SPI3 PC10 / PC11 / PC12, PD0 CS; '
                           'ACT_EN_MCU PC1; PE4 fire, ACTIVE HIGH (PYRO1_GATE_N is a historical name); VBUS_SENSE '
                           'PC8; LEDs PD5 / PD7. NC: PC13, PB0, PC3_C (R18-REQ-08), PB10, PB14, PD10, PD14, PD15, '
                           'PE15.'),
    'Pins the ROM bootloader drives': ('R10 pins the ROM bootloader drives (AN2606 Rev64 Table119 / Rev70 Table135; '
                                       'K-loader): SERVO3 PA2 (USART2_TX), VLOGIC_SENSE PA6 (SPI1_MISO into the '
                                       'divider), SD_MISO PC11 (SPI3_MISO; R460 keeps the card deselected), USB '
                                       'PA11/PA12 (DFU), QSPI_NCS PB6 and I2C1_SDA PB9 (open drain); PA8, PA9, PB10, '
                                       'PB14, PC9 and PE13 stay NC. UART5 PB12/PB13, USART6 PC6/PC7 and USART3 on PD8/PD9 '
                                       '(the loader\'s USART3 is PB10/PB11) are not loader interfaces.'),
}
# Each claim above, checked against the reviewed pin table (pin: r10_net).
R10_MCU_NOTE_PINS = {'8': 'BUZZ_DRV', '28': 'LOGIC_SOURCE_ST', '29': 'BAT_FAULT_N', '37': 'CAM_MCU_RX',
                     '38': 'CAM_MCU_TX', '39': 'CAM_UART_OE', '41': 'CAM_PWR_EN', '42': 'CAM_FAULT_N',
                     '51': 'RADIO_RX_MCU', '52': 'RADIO_TX_MCU', '55': 'GPS_TX_MCU', '56': 'GPS_RX_MCU',
                     '63': 'AUX_TX_MCU', '64': 'AUX_RX_MCU',
                     '78': 'SD_SCK', '79': 'SD_MISO', '80': 'SD_MOSI', '81': 'SD_CS', '16': 'ACT_EN_MCU',
                     '3': 'PYRO1_GATE_N', '65': 'VBUS_SENSE', '86': 'LED_RED', '88': 'LED_YEL', '24': 'SERVO3_MCU',
                     '30': 'VLOGIC_SENSE', '70': 'USB_DM', '71': 'USB_DP', '92': 'QSPI_NCS', '96': 'I2C1_SDA',
                     '7': 'NC', '34': 'NC', '18': 'NC', '46': 'NC', '53': 'NC', '67': 'NC', '68': 'NC', '66': 'NC',
                     '43': 'NC', '2': 'NC', '4': 'NC', '5': 'NC', '32': 'NC'}  # R19-MCU-03 sentinels PE3 / PE5 / PE6 / PC4


# R19-MCU-03 / R19-REQ-02 / R19-MCU-02: retained R8 / R9 sheet notes that contradicted the R10 pin map, part values or
# the single DS12110 revision, each replaced in place (matched by its opening words).
R19_SHEET_NOTES = {
    'mcu.kicad_sch': {
        'R2: PE3 (pin 2) and PE6 (pin 5)': ('R10: PE3 (pin 2) and PE5 (pin 4) flank the PE4 fire pin (pin 3); PE3, PE5, PE6 (pin 5) '
                                          'and PC4 (pin 32) have no net and stay analog (their reset state), never driven '
                                          '(R5-MCU-03, R19-MCU-03). R8: LED_RED on PD5 (pin 86), LED_YEL on PD7 (pin 88).')},
    'camera_uart.kicad_sch': {
        'R8: PE8/pin38 UART7_TX': ('R8: PE8/pin38 UART7_TX and PE7/pin37 UART7_RX use AF7, no flow control (never AF7 on PE9 or '
                                   'PE10); off the ROM loader\'s USART3. R10: PE9/pin39 CAM_UART_OE drives OE as a GPIO; R102 '
                                   '10k holds it low (R19-MCU-03).')},
    'battery_entry.kicad_sch': {
        'C87: EN/UVLO ride-through.': ('C87: EN/UVLO ride-through, 220 nF 25 V X7R (R19-REQ-02). (R80+R165)||R81 = 227k charges it '
                                       '(tau 50 ms; turn-on 88/56/45 ms at 6.0/7.4/8.4 V, 30-129 ms worst case); R81 alone '
                                       'discharges it (tau 66 ms), so J400 drop-outs shorter than 19/33/41 ms (worst case '
                                       '10.6/20.5/26.4 ms with 0.1 uA EN leakage, D-R20-11) cannot trip U9 (25-64 us t_D,OFF). '
                                       'EN thresholds 1.183-1.223 V rising, 1.076-1.116 V falling (TI SLVSFC9C p9): UVLO on '
                                       '4.89-5.05 V, off 4.45-4.61 V.')},
    'usb_sense.kicad_sch': {
        'Input range and tolerance calculation uses DS12110': ('Input range and tolerance calculation uses DS12110 Rev 8, rev V '
                                                              'chapter: Table 122 pp214-215 and Table 157 pp246-247 '
                                                              '(R19-MCU-02).')},
}


def override_values(text, values):
    """Expand retained-part labels without replacing symbols or their metadata."""
    read, patch, properties = sch._reader()
    edits = []
    for node in read(text).children('symbol'):
        props = properties(node)
        ref = props['Reference'].items[2].atom
        if ref in values:
            value = props['Value'].items[2]
            edits.append((value.start, value.end, json.dumps(values[ref])))
    return patch(text, edits)


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
        text += symbol(library, ref, 86.36 + 139.7 * (i % 5), 88.9 + 48.26 * (i // 5), SHEET['path'])
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
            '# The external power switch arms the board; load-switch, reset and gate safety remain checked.\n' +
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
    if '(symbol "MicroSD_Hinge"' not in library:
        library = library.rstrip()[:-1] + r10_parts.microsd_symbol() + '\n)\n'
    if '(symbol "ServoTerminal"' not in library:
        library = library.rstrip()[:-1] + r10_parts.servo_terminal_symbol() + '\n)\n'
    library = library.replace('(property "ki_fp_filters" "M3_GH_BM04B_GHS_TBT"', '(property "ki_fp_filters" "M3_GH_BM04B_GHS_TBT M3_DB125_4P_GN"')
    # R18-REQ-01: no GH 4-pin header remains on R10; the 4-position terminal symbol filters the DB125 land only.
    library = library.replace('(property "ki_fp_filters" "M3_GH_BM04B_GHS_TBT M3_DB125_4P_GN"',
                              '(property "ki_fp_filters" "M3_DB125_4P_GN"')
    library_path.write_text(library)
    sch.NS = NS
    pins.NS = NS
    originals, nets = baseline()
    changed = data['parts']
    replacements = data['replacements']
    removed = set(data['removed_refs'])
    values = data['value_overrides']
    assert set(values) <= originals.keys() - removed, 'value override must name a retained R9 part'
    assert not set(values) & (changed.keys() | replacements.keys()), 'value override conflicts with part specification'
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
                # R8's translator holds PC1 as an NC sentinel; R10 now uses it for the independent load-switch enable.
                legacy_map = {**pinmap, '16': ('NC', 'NC')}
                t = pins.t_mcu(t, library, legacy_map, {p: ns for p, ns in mcuchanges.items() if p != '16'})
                t = change_pin(t, 'U1', '16', pinmap['16'][1], library)
                # Remove obsolete RF, pull-pin and EXTI narrative; preserve every safety note.
                read, patch, _ = sch._reader()
                t = patch(t, [(n.start, n.end, '') for n in read(t).children('text')
                              if 'radio SPI2' in n.items[1].atom or 'R8 EXTI:' in n.items[1].atom
                              or 'pull-pin' in n.items[1].atom.lower() or 'PULLPIN' in n.items[1].atom
                              or 'CH1 sense:' in n.items[1].atom])
                t = sch.insert(t, sch.note('R10: three identical always-on ports, direct1k UARTs on PORT_4V8 (D-R19-14): USART3 PD8/PD9 AF7 J410 (GPS by default); UART5 PB13/PB12 AF14 J420 (radio); USART6 PC6/PC7 AF7 J440 (AUX spare); firmware maps devices to ports. Camera EN/OE default low; EXTI12 CAM_FAULT_N; EXTI4 LOGIC_SOURCE_ST (PA4), EXTI5 BAT_FAULT_N (PA5); VLOGIC_SENSE ADC on PA6. EXTI1 PE1 IMU_INT1 data-ready. SPI3 PC10/11/12 AF6 SD_SCK/MISO/MOSI; PD0 SD_CS high at reset via10k. No SD card-detect.', 20.32, 259.08, 'mcu:r10:ports'))
                t = sch.insert(t, sch.note('Single screw switch: PC1 U1.16 ACT_EN_MCU drives R122 1k and Q122; initialise PC1 and PE4 low before output mode. R123 2k holds the load switch off at reset and against a 30k internal pull-up (R18-MCU-01); never enable a PC1 or PE4 pull-up. PE4 U1.3 is ACTIVE HIGH: PE4 high turns Q124 on (PYRO1_GATE_N is a historical name). Both low for passive cold screening; after prior enable wait >=1 s and verify bus discharge. Refuse ground faults BEFORE PC1 enable; then PC1 high, PE4 low >=100 ms before powered-bus checks (D-SS-04). Disable synchronous trace; lock/read back both gate GPIO configurations. AUD-4: PC13 U1.7 is NC/analog; no pull-pin.', 20.32, 269.24, 'mcu:r10:load-switch'))
                for row in R10_MCU_NOTE_PINS.items():
                    assert pinmap[row[0]][1] == row[1], f'R10 MCU note claim U1.{row[0]} {row[1]} differs from the pin table'
                for prefix, line in R10_MCU_NOTES.items():
                    t = replace_note(t, prefix, line, f'mcu:r18:{prefix}')
                t = sch.insert(t, sch.note('CH1 sense: filtered PYRO1_CONT -> PC0 ADC123_INP10; filtered ARM1_SENSE -> PC5 ADC12_INP8, the sole RAW_ACT bus reading (historical ARM1_SENSE name). Split divider safety retained; audit2 removes R168/R170 and _MCU tails (single-resistor fault maximum3.342V at19.9V clamp). AVA follow-up removes the duplicate six-part RAW_ACT_SENSE chain; PB0 U1.34 is NC/analog, never driven. Ground bus/continuity readings are hard refusals; in flight they never veto fire.', 20.32, 279.4, 'mcu:r10:sense'))
            if file.name == 'battery_entry.kicad_sch':
                t = add(t, library, 'J400', changed['J400'], 330.2, 238.76)
                # R18-REQ-02 / R18-SAF-05: the arming contact is J400.1 / J400.2 and the damper R166 is 0.36 ohm.
                t = replace_once(t, '"J1.3--4: external dry contact. Closed = battery enabled;',
                                 '"J400.1 / J400.2 (BAT_SW_SOURCE / BAT_SW_RETURN): external dry screw-switch contact. '
                                 'Closed = battery enabled;')
                t = replace_once(t, 'a battery lead in J1.3/J1.4 puts', 'a battery lead in J400.1/J400.2 puts')
                t = replace_once(t, 'R166 (0.33 ohm 2512)', 'R166 (0.36 ohm 2512)')
            if file.name == 'actuator_power.kicad_sch':
                # R18-SAF-02: Q121's own gate-source resistor (circuit.json sheets: actuator_power).
                t = add(t, library, 'R119', changed['R119'], 157.48, 114.3)
                # R19-SAF-06: Q122's gate-source capacitor completes the AGENTS 2.4 network.
                t = add(t, library, 'C123', changed['C123'], 215.9, 114.3)
            if file.name == 'diagnostics.kicad_sch':
                # R18-REQ-08: the 3V3 / 2 divider (R62 / R63, V3V3_SENSE) is removed; 3V3 is read internally.
                t = replace_once(t, '"Measure VLOGIC and 3V3 directly, then compare divider outputs: VLOGIC/11 and 3V3/2."',
                                 '"Measure VLOGIC directly, then compare VLOGIC/11 (PA6). R18-REQ-08 removes R62/R63: read '
                                 'VDDA (3V3A) from VREFINT and 3V3 from the internal VBAT/4 channel (VBAT tied to 3V3); '
                                 'PC3_C is NC."')
            if file.name == 'camera_uart.kicad_sch':
                for ref, y in (('D400', 228.6), ('D401', 251.46)):
                    t = add(t, library, ref, changed[ref], 330.2, y)
            if file.name == 'usb_sense.kicad_sch':
                t = t.replace('TP92 measures their junction.', 'Probe R9.2 / R110.1; TP92 removed (AUD-5).')
            for prefix, line in R19_SHEET_NOTES.get(file.name, {}).items():
                t = replace_note(t, prefix, line, f'{file.stem}:r19:{prefix}')
            if file.stem in data['notes']:
                t = replace_notes(t, data['notes'][file.stem])
        t = override_values(t, values)
        t = t.replace('(rev "M3-ASSY-R9")', f'(rev "{REV}")')
        t = t.replace('14 | Launch pull-pin and buzzer', data['titles']['pullpin_buzzer'])
        # Root hierarchy names follow new sheet titles; their UUID/path never changes.
        if file.name == 'm3.kicad_sch':
            t = change_pin(t, '#FLG06', '1', 'PORT_5V3', library)
            t = t.replace('05 | Camera branch protection and regulator', data['titles']['power'])
            t = t.replace('15 | GNSS and telemetry radio (R7)', data['titles']['telemetry'])
        t = sch.refresh_embedded(t, library, 'PolarCap')
        t = sch.refresh_embedded(t, library, 'CameraTerminal')
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
