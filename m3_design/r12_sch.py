#!/usr/bin/env python3
"""Generate the M3-ASSY-R12 schematic: R11's circuit pruned and re-sourced for one-sided JLC Economic PCBA (D-R12-01).

R12 starts from R11's final netlist (commit 0b26da5, D-R11-85 ... -88 included), copied into
m3_design/r12/design/r11_input/ with a SHA-256 manifest that is checked before every generation. The change list is
m3_design/r12/design/circuit.json (deleted parts, re-sourced parts, added parts, pin net changes, U1 re-pins); its
decisions are R12_DECISIONS.md D-R12-xx. Unlike R11, the sheets are drawn fresh from the netlist model: every part is a
symbol whose pins each reach a global label through a 5.08 mm wire (or carry a no-connect flag), laid out on a grid,
one sheet per R11 sheet file. The board is laid out new (stage B), so no R11 drawing is reused.

usage: python3 -B m3_design/r12_sch.py --out m3_design/r12        (after r12_parts.py --library-only)
       python3 -B m3_design/r12_sch.py --pin-inputs [--force]     (one time: copy and hash R11's inputs)
       python3 -B m3_design/r12_sch.py --pin-table                (write design/pin_table.tsv)
No version-control operations; deterministic (fixed UUID namespace NS, no timestamps).
"""
import argparse
import csv
import hashlib
import io
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

ROOT_DIR = HERE.parent
R11 = HERE / 'r11'                                   # R11's project (read only; the used files are pinned below)
PROJECT = HERE / 'r12'
DESIGN = PROJECT / 'design'
INPUT = DESIGN / 'r11_input'
NS = uuid.UUID(str(uuid.uuid5(uuid.NAMESPACE_URL, 'm3-assy-r12/schematic')))
ROOT_UUID = str(uuid.uuid5(NS, 'root'))
REV, R11_REV = 'M3-ASSY-R12', 'M3-ASSY-R11'
R11_COMMIT = '0b26da5'
DATE = '2026-11-04'

INPUT_FILES = {'schematic.net.xml': 'schematic.net.xml', 'pin_table.tsv': 'design/pin_table.tsv',
               'circuit.json': 'design/circuit.json', 'm3.kicad_sym': 'kilib/m3.kicad_sym',
               'm3.kicad_dru': 'm3.kicad_dru', 'm3.kicad_pro': 'm3.kicad_pro', 'sym-lib-table': 'sym-lib-table',
               'fp-lib-table': 'fp-lib-table'}

# file, page title (page numbers follow this order; the root is page 1)
SHEETS = (
    ('m3.kicad_sch', '01 | USB input, 3V3 buck (LMR50410) and analog rail'),
    ('mcu.kicad_sch', '02 | MCU, clock and debug'),
    ('sensors.kicad_sch', '03 | QSPI log, IMU and barometer'),
    ('diagnostics.kicad_sch', '04 | Voltage diagnosis, port sense and indicators'),
    ('camera_power.kicad_sch', '05 | Port buck and camera buck (TPS563208)'),
    ('camera_connector.kicad_sch', '06 | Camera terminal'),
    ('battery_entry.kicad_sch', '07 | Battery input, contact and protection'),
    ('logic_power_path.kicad_sch', '08 | Logic diode-OR and hold-up'),
    ('camera_uart.kicad_sch', '09 | Camera UART series resistors'),
    ('usb_sense.kicad_sch', '10 | USB cable presence'),
    ('actuator_power.kicad_sch', '11 | Pyro bus load switch'),
    ('pyro.kicad_sch', '12 | Pyro channel'),
    ('servos.kicad_sch', '13 | Servo outputs'),
    ('pullpin_buzzer.kicad_sch', '14 | Buzzer'),
    ('telemetry.kicad_sch', '15 | GPS / radio / AUX ports and microSD'),
)
SHEET_FILES = tuple(s for s, _ in SHEETS)

# D-R12-12: U1 functions R12 deletes or replaces, keyed by their R11 net (each appears on exactly one U1 ball)
R12_REPIN = {
    'USB_FAULT_N': ('NC', 'NC (firmware: analog, never driven)', 'D-R12-04: U10 deleted (USB diode-OR)'),
    'CAM_FAULT_N': ('NC', 'NC (firmware: analog, never driven)', 'D-R12-07: U402 deleted (camera buck EN is the switch)'),
    'CAM_UART_OE': ('NC', 'NC (firmware: analog, never driven)', 'D-R12-07: U12 deleted (1 kOhm series only)'),
    'LOGIC_SOURCE_ST': ('PORT_SENSE', 'GPIO in, no pull (high = PORT_4V8 present: the battery path is on)',
                        'D-R12-05 / -86: U11 deleted; PA4 now reads PORT_4V8 through R111 47k / R112 100k (3.10-3.39 V '
                        'high initial, 3.07-3.43 V drift, with PA4 leakage; Calculation; drift Inference); the R10 rule '
                        '"port UARTs only while PA4 reads low" becomes "only while PA4 reads high" (D-R12-93: PD10 reads high; '
                        'PORT_SENSE moves to H9 through R12_MOVES)'),
}

# D-R12-51: U1 balls R12 gives a function that R11 left NC, keyed by ball (each NC in R11)
R12_NEW_PINS = {
    'D10': ('HG_CS', 'GPIO out (push-pull, initialise high before output mode); analog at reset: U6 SS_B internal '
                     'pull-up (NXP FXLS9xxx0 Rev 6 Table 9) holds the high-g accelerometer deselected',
            'D-R12-51: PA10 (outer ring, east column) is U6 FXLS90322 SS_B on the IMU SPI1 bus; not a PE4 (C3) or '
            'PC1 (F2) neighbour; loader USART1_RX input with pull-up (AN2606), which leaves U6 deselected'),
}


# D-R12-61A ... (stage C pass 1): nets moved to another U1 ball so that each leaves the ball field on the side facing its
# pads; net -> (new ball, R12 mode, source). Balls: DS12110 Rev 8 Table 9; alternate functions: its Tables 10-14 (Port
# A-E). Each function was read from KiCad 10's MCU_ST_STM32H7 symbol STM32H743V_G-I_Hx (pin alternates built from ST's
# open pin data); the AF numbers are not in that symbol and st.com refused scripted access in this pass, so the
# datasheet rows and AF numbers were an Inference until D-R12-93 read them from the DS12110 Rev 8 PDF text (Tables 9-14).
_DS = 'DS12110 Rev 8'
R12_MOVES = {
    'QSPI_NCS': ('J7', 'AF9 QUADSPI_BK1_NCS',
                 f'D-R12-61A: PB6 (B5, aft) -> PB10 (J7, forward, toward U3); {_DS} Table 11 pp. 90-91 (Port B alternate functions: PB10 AF9 '
                 'QUADSPI_BK1_NCS; AF number confirmed from the Rev 8 PDF text in D-R12-93)'),
    'SD_SCK': ('J6', 'AF5 SPI4_SCK', f'D-R12-63A: PC10 (B9, aft) -> PE12 (J6, forward, toward J430); peripheral '
               f'SPI4; {_DS} Table 14 pp. 95-96 (Port E alternate functions: PE12 AF5 SPI4_SCK; AF number confirmed from the Rev 8 PDF text in D-R12-93)'),
    'SD_MISO': ('K6', 'AF5 SPI4_MISO', f'D-R12-63A: PC11 (B8, aft) -> PE13 (K6, forward, toward J430); peripheral '
                f'SPI4; {_DS} Table 14 pp. 95-96 (Port E alternate functions: PE13 AF5 SPI4_MISO; AF number confirmed from the Rev 8 PDF text in D-R12-93)'),
    'SD_MOSI': ('G7', 'AF5 SPI4_MOSI', f'D-R12-63A: PC12 (C8) -> PE14 (G7, dog-bone, forward B lane); peripheral '
                f'SPI4; {_DS} Table 14 pp. 95-96 (Port E alternate functions: PE14 AF5 SPI4_MOSI; AF number confirmed from the Rev 8 PDF text in D-R12-93)'),
    'SD_CS': ('K3', 'GPIO output push-pull; initialise high before output mode',
              f'D-R12-63A: PD0 (D8, dog-bone) -> PA7 (K3, forward ring 1, toward J430.2); plain GPIO; {_DS} Table 9 '
              'pp. 64-88 (PA7, TFBGA100 ball K3)'),
    # D-R12-93 (AVA re-layout): every function below read from DS12110 Rev 8 Tables 9-14 (pdftotext of the Rev 8 PDF);
    # ROM-loader roles from the pin table's AN2606 Rev 64 Table 119 column (read in R11, not re-read here).
    'I2C1_SCL': ('B5', 'AF4 I2C1_SCL (open drain, R12 pull-up)',
                 f'D-R12-62A: PB10 (J7) -> PA8 (D9, I2C3); D-R12-93: PA8 (D9) -> PB6 (B5, aft, straight to U5 on the axis); '
                 f'peripheral I2C3 -> I2C1; {_DS} Table 11 pp. 90-91 (Port B alternate functions: PB6 AF4 I2C1_SCL); '
                 f'ball B5 = PB6, {_DS} Table 9 p. 86'),
    'I2C1_SDA': ('A5', 'AF4 I2C1_SDA (open drain, R13 pull-up)',
                 f'D-R12-62A: PB11 (K7) -> PC9 (E9, I2C3); D-R12-93: PC9 (E9) -> PB7 (A5, aft); peripheral I2C3 -> I2C1; '
                 f'{_DS} Table 11 pp. 90-91 (PB7 AF4 I2C1_SDA); ball A5 = PB7, {_DS} Table 9 p. 86'),
    'HG_CS': ('B7', 'GPIO out (push-pull, initialise high before output mode); analog at reset: U6 SS_B internal '
              'pull-up (NXP FXLS9xxx0 Rev 6 Table 9) holds the high-g accelerometer deselected',
              f'D-R12-64A: PA10 (D10) -> PC11 (B8); D-R12-93: PC11 (B8) -> PD2 (B7, aft sensor group, toward U6); plain '
              f'GPIO; {_DS} Table 9 p. 83 (PD2, TFBGA100 ball B7); not a PE4 (C3) or PC1 (F2) neighbour; PD2 is not an H74x '
              'loader pin (AN2606 Rev 64 Table 119)'),
    'VBUS_SENSE': ('E9', 'GPIO in',
                   f'D-R12-64A: PC8 (F9) -> PA10 (D10); D-R12-93: PA10 (D10) -> PC9 (E9, east, toward R9 / R110); plain '
                   f'GPIO input; {_DS} Table 9 p. 79 (PC9, TFBGA100 ball E9); loader I2C3_SDA open drain, not driven (AN2606 '
                   'Rev 64 Table 119 p. 278): the divider sets the level'),
    'SERVO1_MCU': ('A8', 'AF1 TIM2_CH1 (333 Hz PWM, REQUIREMENTS F4); reset: JTDI with the internal pull-up (RM0433 debug pins)',
                   f'D-R12-93: PB7 (A5) -> PA15 (A8, aft-east, toward the CA bus and D121.1); {_DS} Table 10 p. 90 '
                   '(PA15 AF1 TIM2_CH1 / TIM2_ETR, AF0 JTDI; Table 9 p. 82: ball A8 = PA15 (JTDI)); loader SPI3_NSS slave input, no pull (AN2606 Rev 64 Table 119 '
                   'p. 279); at reset the JTDI pull-up (30-50 kohm, DS12110 RPU) against the servo-cell 10 kohm 1 % '
                   'pull-down (R154-R157) holds a steady level of at most 0.864 V at the 3V3 initial maximum 3.4314 V '
                   '(3.4314 x 10.1k / 40.1k) and 0.873 V at the drift maximum 3.4641 V (r12_windows.json), no pulse '
                   '(Calculation; drift case Inference; as R12 accepted for SERVO2 on this ball)'),
    'SERVO2_MCU': ('D10', 'AF1 TIM1_CH3 (333 Hz PWM, REQUIREMENTS F4; TIM1 is an advanced timer: set BDTR.MOE)',
                   f'D-R12-93: PA15 (A8) -> PA10 (D10, east ring 1); {_DS} Table 10 p. 89 (PA10 AF1 TIM1_CH3); loader '
                   'USART1_RX input with pull-up (AN2606 Rev 64 Table 119 p. 277): the 30-50 kohm pull-up (DS12110 RPU) '
                   'against the servo-cell 10 kohm 1 % pull-down holds at most 0.864 V at the 3V3 initial maximum 3.4314 V '
                   '(3.4314 x 10.1k / 40.1k) and 0.873 V at the drift maximum 3.4641 V (r12_windows.json), no pulse '
                   '(Calculation; drift case Inference; R11 PA3 method)'),
    'SERVO3_MCU': ('D9', 'AF1 TIM1_CH1 (333 Hz PWM, REQUIREMENTS F4; TIM1: set BDTR.MOE)',
                   f'D-R12-93: PA1 (H2, west face) -> PA8 (D9, east ring 2); {_DS} Table 10 p. 89 (PA8 AF1 TIM1_CH1, AF0 '
                   'MCO1: keep MCO1 off); loader I2C3_SCL open drain, not driven (AN2606 Rev 64 Table 119 p. 278)'),
    'SERVO4_MCU': ('C9', 'AF1 TIM1_CH2 (333 Hz PWM, REQUIREMENTS F4; TIM1: set BDTR.MOE)',
                   f'D-R12-93: PA2 (J2, west face) -> PA9 (C9, aft-east ring 2); {_DS} Table 10 p. 89 (PA9 AF1 '
                   'TIM1_CH2); loader USART1_TX may drive a steady high (AN2606 Rev 64 Table 119 p. 277) [LOADER-DRIVEN]: '
                   'it reaches the servo through the 1 kohm series resistor as a level, not a pulse train; the same '
                   'allowance R11 accepted for SERVO4 on PA2 (USART2_TX), which this map frees'),
    'CAM_MCU_TX': ('B9', 'AF8 UART4_TX',
                   f'D-R12-93: PD5 (B6, USART2) -> PC10 (B9, aft-east, toward R101); peripheral USART2 -> UART4; {_DS} '
                   'Table 12 p. 92 (Port C alternate functions: PC10 AF8 UART4_TX); loader SPI3_SCK slave input, not '
                   'driven (AN2606 Rev 64 Table 119 p. 279)'),
    'CAM_MCU_RX': ('B8', 'AF8 UART4_RX',
                   f'D-R12-93: PD6 (C6, USART2) -> PC11 (B8, aft-east, toward R100); peripheral USART2 -> UART4; {_DS} '
                   'Table 12 p. 92 (PC11 AF8 UART4_RX); loader SPI3_MISO slave output push-pull (AN2606 Rev 64 Table 119 '
                   'p. 279) [LOADER-DRIVEN]: the camera is unpowered in the loader (PC12 CAM_PWR_EN is an undriven input '
                   'and R431 holds the buck EN low) and R100 1 kohm 1 % limits any fight to at most 3.47 mA (resistor-only bound, '
                   '3.4314 V / 990 ohm at the 3V3 initial maximum; 3.50 mA at the drift maximum 3.4641 V, r12_windows.json; '
                   'Calculation; drift case Inference)'),
    'CAM_PWR_EN': ('C8', 'GPIO out (push-pull; R431 pull-down holds the camera buck off in reset)',
                   f'D-R12-93: PC14 (A1, aft-west corner) -> PC12 (C8, aft-east, toward U403.5); plain GPIO; {_DS} Table '
                   '9 p. 82 (PC12, TFBGA100 ball C8); loader SPI3_MOSI slave input, no pull (AN2606 Rev 64 Table 119 p. 279): '
                   'not driven, so R431 keeps the camera off'),
    'LED_YEL': ('H2', 'GPIO out',
                f'D-R12-93: PD2 (B7) -> PA1 (H2, west face, straight to R33 in the west bay); plain GPIO; {_DS} Table 9 '
                '(PA1, TFBGA100 ball H2); not an H74x loader pin (AN2606 Rev 64 Table 119)'),
    'BAT_FAULT_N': ('A2', 'GPIO in, EXTI13 (open drain U9 FLT with R89 pull-up)',
                    f'D-R12-93: PA5 (H3, forward-west) -> PC13 (A2, aft-west, toward R89 / U9); plain GPIO input; '
                    f'{_DS} Table 9 p. 64 (PC13, TFBGA100 ball A2, FT; a VBAT-domain pin whose 2 MHz / 3 mA output '
                    'limits do not apply to an input, DS12110 Table 9 note); not an H74x loader pin (AN2606 Rev 64 '
                    'Table 119)'),
    'PORT_SENSE': ('H9', 'GPIO in, no pull (high = PORT_4V8 present: the battery path is on)',
                   f'D-R12-93: PA4 (G3, a PC1 F2 neighbour) -> PD10 (H9, forward-east, beside the port UART balls); plain '
                   f'GPIO input; {_DS} Table 9 p. 75 (PD10, TFBGA100 ball H9, FT_h); not an H74x loader pin (AN2606 Rev 64 '
                   'Table 119); G3 is now NC, so K-neighbours no longer needs an inert argument for it'),
}


def uid(key):
    return str(uuid.uuid5(NS, key))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------------------------------------------
# pinned inputs

def r11_library_files():
    """R11 kilib files R12 may copy: every footprint of R11's netlist and the models they name."""
    root = ET.parse(R11 / 'schematic.net.xml').getroot()
    names = sorted({c.findtext('footprint').split(':')[1] for c in root.findall('./components/comp')})
    files = []
    for name in names:
        fp = R11 / 'kilib/rocket.pretty' / (name + '.kicad_mod')
        files.append(fp)
        for model in re.findall(r'\(model "\$\{KIPRJMOD\}/([^"]+)"', fp.read_text()):
            files.append(R11 / model)
    return files


def pin_inputs(force=False):
    if (INPUT / 'manifest.json').exists() and not force:
        raise SystemExit('r11_input already pinned; use --force to re-pin (changes every downstream hash)')
    INPUT.mkdir(parents=True, exist_ok=True)
    for name, source in INPUT_FILES.items():
        shutil.copy2(R11 / source, INPUT / name)
    manifest = {
        'source': f'm3_design/r11 at commit {R11_COMMIT} (R11 tip, D-R11-85 ... -88 included)',
        'files': {name: sha(INPUT / name) for name in sorted(INPUT_FILES)},
        'library': {str(p.relative_to(ROOT_DIR)): sha(p) for p in r11_library_files()},
        'note': 'r12_sch.source_check() verifies every hash before each generation; library files stay in R11\'s kilib',
    }
    (INPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'pinned {len(manifest["files"])} R11 files and {len(manifest["library"])} R11 library files')


def source_check():
    data = json.loads((INPUT / 'manifest.json').read_text())
    assert set(data['files']) == set(INPUT_FILES), 'r11_input manifest lists other files'
    for name, digest in data['files'].items():
        assert sha(INPUT / name) == digest, f'R11 input changed: {name}'
    for rel, digest in data['library'].items():
        assert sha(ROOT_DIR / rel) == digest, f'R11 library file changed: {rel}'
    return data


def circuit():
    return json.loads((DESIGN / 'circuit.json').read_text())


FIELDS = ('LCSC', 'Manufacturer', 'Manufacturer Part', 'Datasheet')
FLAG_NAMES = ('dnp', 'exclude_from_bom', 'exclude_from_pos_files', 'exclude_from_board')


def read_netlist(path):
    """({ref: part}, {(ref, pin): net or None}) of a KiCad XML netlist; part = lib, value, footprint, fields, flags,
    sheet (its Sheetfile)."""
    root = ET.parse(path).getroot()
    parts = {}
    for c in root.findall('./components/comp'):
        f = {e.get('name'): e.text or '' for e in c.findall('./fields/field')}
        props = {e.get('name'): e.get('value') for e in c.findall('property')}
        parts[c.get('ref')] = dict(lib='M3:' + c.find('libsource').get('part'), value=c.findtext('value'),
                                   footprint=c.findtext('footprint'),
                                   fields={k: f.get(k, '') for k in FIELDS if k in f},
                                   flags=sorted(k for k in props if k in FLAG_NAMES),
                                   sheet=props.get('Sheetfile', 'm3.kicad_sch'))
    pins = {(p.get('ref'), p.get('pin')): None if n.get('name').startswith('unconnected-') else n.get('name')
            for n in root.findall('./nets/net') for p in n.findall('node')}
    return parts, pins


def r11_netlist():
    return read_netlist(INPUT / 'schematic.net.xml')


def catalog_fields(data, code):
    cat = data['catalog'][code]
    return {'LCSC': code, 'Manufacturer': cat['Manufacturer'], 'Manufacturer Part': cat['Manufacturer Part'],
            'Datasheet': cat['Datasheet']}


def model(data=None):
    """R12's parts and pins: R11's netlist with circuit.json applied. Parts keep R11's symbol, value, footprint and
    part fields unless circuit.json re-sources them; 'nets' in a re-sourced entry replaces every pin of the part."""
    data = data or circuit()
    parts, pins = r11_netlist()
    for ref in data['deleted']:
        assert ref in parts, f'deleted part {ref} is not an R11 part'
        del parts[ref]
    pins = {k: v for k, v in pins.items() if k[0] in parts}
    for ref, e in data['parts'].items():
        assert ref in parts, f'circuit.json parts names {ref}, not a kept R11 part'
        p = parts[ref]
        if e.get('lcsc'):
            p['fields'] = catalog_fields(data, e['lcsc'])
            p['footprint'] = data['catalog'][e['lcsc']]['footprint']
        p['value'] = e.get('value', p['value'])
        p['lib'] = e.get('lib', p['lib'])
        p['footprint'] = e.get('footprint', p['footprint'])          # D-R12-30: a land change with no BOM code
        if 'flags' in e:
            p['flags'] = list(e['flags'])
        if 'nets' in e:
            pins = {k: v for k, v in pins.items() if k[0] != ref}
            pins.update({(ref, n): net for n, net in e['nets'].items()})
    for ref, changes in data['net_changes'].items():
        for pin, net in changes.items():
            assert (ref, pin) in pins, f'net_changes names {ref}.{pin}, not a pin'
            pins[ref, pin] = net
    for ref, e in data['added_parts'].items():
        assert ref not in parts, f'added part {ref} already exists'
        parts[ref] = dict(lib=e['lib'], value=e['value'], footprint=data['catalog'][e['lcsc']]['footprint'],
                          fields=catalog_fields(data, e['lcsc']), flags=[], sheet=e['sheet'])
        pins.update({(ref, n): net for n, net in e['nets'].items()})
    seen = {}
    for (ref, pin), net in list(pins.items()):
        if ref == 'U1' and net in R12_REPIN:
            assert net not in seen, f'{net} on two U1 balls'
            seen[net] = pin
            new = R12_REPIN[net][0]
            pins[ref, pin] = None if new == 'NC' else new
    assert set(seen) == set(R12_REPIN), f'U1 re-pin nets not found: {sorted(set(R12_REPIN) - set(seen))}'
    for ball, (net, _, _) in R12_NEW_PINS.items():
        assert pins.get(('U1', ball), 'missing') is None, f'U1.{ball} is not an R11 NC ball'
        pins['U1', ball] = net
    # D-R12-61A ...: stage C re-pins (every moved net leaves its ball first, then takes its new one)
    old = {}
    for net in R12_MOVES:
        balls = [k[1] for k, v in pins.items() if k[0] == 'U1' and v == net]
        assert len(balls) == 1, f'{net} on U1 balls {balls}'
        old[net] = balls[0]
        pins['U1', balls[0]] = None
    for net, (ball, _, _) in R12_MOVES.items():
        assert pins.get(('U1', ball), 'missing') is None, f'U1.{ball} is not free for {net}'
        pins['U1', ball] = net
    for p in parts.values():
        p['flags'] = sorted(p['flags'])
    return parts, pins


# ---------------------------------------------------------------------------------------------------------------------
# pin table

PIN_TABLE_HEADER = ('# M3-ASSY-R12 U1 pin table: STM32H743VIH6 TFBGA-100 (JLC C964146), kept from R11 (D-R12-02). '
                    'Columns as R11\'s pin_table.tsv (r11_input/pin_table.tsv, verbatim) plus r12_net, r12_mode and '
                    'r12_source; r12_net is the R12 function map (R11\'s r11_net with the D-R12 changes in r12_source). '
                    'Lines starting with # are comments.\n')


def r11_pin_rows():
    lines = [l for l in (INPUT / 'pin_table.tsv').read_text().splitlines(True) if not l.startswith('#')]
    return list(csv.DictReader(lines, delimiter='\t'))


def pin_rows():
    out = []
    rows = r11_pin_rows()
    moved_to = {ball: net for net, (ball, _, _) in R12_MOVES.items()}
    for row in rows:
        new = dict(row)
        net = row['r11_net']
        if net in R12_REPIN:
            r12, mode, why = R12_REPIN[net]
            new.update(r12_net=r12, r12_mode=mode, r12_source=why)
        elif row['r11_ball'] in R12_NEW_PINS:
            assert net == 'NC', row
            r12, mode, why = R12_NEW_PINS[row['r11_ball']]
            new.update(r12_net=r12, r12_mode=mode, r12_source=why)
        else:
            new.update(r12_net=net, r12_mode='as R11', r12_source='R11 (unchanged)')
        if new['r12_net'] in R12_MOVES and row['r11_ball'] != R12_MOVES[new['r12_net']][0]:
            ball, _, why = R12_MOVES[new['r12_net']]
            new.update(r12_net='NC', r12_mode='NC (firmware: analog, never driven)',
                       r12_source=f"{why.split(':')[0]}: {new['r12_net']} moved to ball {ball}")
        if row['r11_ball'] in moved_to:
            net_ = moved_to[row['r11_ball']]
            _, mode, why = R12_MOVES[net_]
            new.update(r12_net=net_, r12_mode=mode, r12_source=why)
        out.append(new)
    nets = [r['r12_net'] for r in out if r['r12_net'] not in ('NC', 'GND', '3V3', '-')]
    dup = {n for n in nets if nets.count(n) > 1 and n not in ('3V3A',)}
    assert not dup, f'pin table: nets on two balls {sorted(dup)}'
    return out


def pin_table_text():
    rows = pin_rows()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return PIN_TABLE_HEADER + buf.getvalue()


def read_pin_table(path=DESIGN / 'pin_table.tsv'):
    lines = [l for l in Path(path).read_text().splitlines(True) if not l.startswith('#')]
    return list(csv.DictReader(lines, delimiter='\t'))


# ---------------------------------------------------------------------------------------------------------------------
# sheet drawing

GRID = 2.54
PAPERS = (('A3', 420, 297), ('A2', 594, 420), ('A1', 841, 594), ('A0', 1189, 841))
MARGIN = 25.4


def snap(v, step=GRID):
    return round(round(v / step) * step, 2)


def natural(ref):
    m = re.match(r'([A-Z#]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def lib_pins(lt, name):
    return sch._lib_pins(lt, name)


def cell(lt, name, nets):
    """Extents of one symbol with its wires and labels around its origin (sheet coordinates, y down)."""
    pins = lib_pins(lt, name)
    xs = [x for x, _, _ in pins.values()]
    ys = [-y for _, y, _ in pins.values()]
    label = max([len(n or '') for n in nets.values()] + [4]) * 1.0 + 4.0
    return (min(xs) - 5.08 - label, min(ys) - 10.16, max(xs) + 5.08 + label, max(ys) + 10.16)


def symbol_text(lt, ref, part, nets, x, y, path):
    name = part['lib'].split(':')[1]
    flags = set(part['flags'])
    body = (f'\t(symbol\n\t\t(lib_id "{part["lib"]}")\n\t\t(at {sch.fmt(x)} {sch.fmt(y)} 0)\n\t\t(unit 1)\n'
            f'\t\t(in_bom {"no" if "exclude_from_bom" in flags else "yes"})\n\t\t(on_board yes)\n')
    if 'exclude_from_pos_files' in flags:
        body += '\t\t(in_pos_files no)\n'
    body += f'\t\t(dnp {"yes" if "dnp" in flags else "no"})\n\t\t(uuid {uid("sym:" + ref)})\n'
    pins = lib_pins(lt, name)
    top = min(-py for _, py, _ in pins.values())
    body += sch.prop('Reference', ref, x, y + top - 3.81, hide=False)
    body += sch.prop('Value', part['value'].replace('"', "'"), x, y + top - 1.27, hide=False)
    body += sch.prop('Footprint', part['footprint'], x, y)
    for k in FIELDS:
        if k in part['fields']:
            body += sch.prop(k, part['fields'][k], x, y)
    body += (f'\t\t(instances\n\t\t\t(project "m3"\n\t\t\t\t(path "{path}"\n'
             f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)))))\n')
    if set(pins) != set(nets):
        raise SystemExit(f'{ref}: symbol pins {sorted(pins)} differ from the net map {sorted(nets)}')
    for num, (px, py, ang) in sorted(pins.items(), key=lambda kv: (len(kv[0]), kv[0])):
        ax, ay = round(x + px, 2), round(y - py, 2)
        if nets[num] is None:
            body += sch.nc(ax, ay, f'{ref}:nc{num}').replace(sch.uid(f'{ref}:nc{num}'), uid(f'{ref}:nc{num}'))
            continue
        dx, dy = {0: (-5.08, 0), 180: (5.08, 0), 90: (0, 5.08), 270: (0, -5.08)}[int(ang) % 360]
        bx, by = round(ax + dx, 2), round(ay + dy, 2)
        w = sch.wire(ax, ay, bx, by, 'x').replace(sch.uid('x'), uid(f'{ref}:w{num}'))
        lab = sch.glabel(nets[num], bx, by, 'x', angle=0 if dx <= 0 else 180,
                         justify='right' if dx <= 0 else 'left').replace(sch.uid('x'), uid(f'{ref}:l{num}'))
        body += w + lab
    return body


def flag_text(ref, net, x, y, path):
    """A PWR_FLAG (#FLGnn, out of BOM and board) wired to a global label: ERC's driver for a power-input net."""
    body = (f'\t(symbol\n\t\t(lib_id "M3:PWR_FLAG")\n\t\t(at {sch.fmt(x)} {sch.fmt(y)} 0)\n\t\t(unit 1)\n'
            f'\t\t(in_bom no)\n\t\t(on_board no)\n\t\t(dnp no)\n\t\t(uuid {uid("flag:" + net)})\n')
    body += sch.prop('Reference', ref, x, y - 7.62)
    body += sch.prop('Value', 'PWR_FLAG', x, y - 3.81)
    body += sch.prop('Footprint', '', x, y)
    body += sch.prop('Datasheet', '', x, y)
    body += (f'\t\t(instances\n\t\t\t(project "m3"\n\t\t\t\t(path "{path}"\n'
             f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)))))\n')
    body += sch.wire(x, y, x - 7.62, y, 'x').replace(sch.uid('x'), uid(f'flag:{net}:w'))
    body += sch.glabel(net, x - 7.62, y, 'x').replace(sch.uid('x'), uid(f'flag:{net}:l'))
    return body


def layout(lt, items, width):
    """Grid positions {ref: (x, y)} for (ref, symbol name, nets) items, rows filled left to right; returns the
    positions and the used height."""
    out, x0, y0, row_h = {}, MARGIN, MARGIN + 30.48, 0.0
    for ref, name, nets in items:
        a, b, c, d = cell(lt, name, nets)
        w, h = c - a, d - b
        if x0 + w > width - MARGIN and x0 > MARGIN:
            x0, y0, row_h = MARGIN, y0 + row_h + 5.08, 0.0
        out[ref] = (snap(x0 - a + GRID), snap(y0 - b + GRID))
        x0 += w + 5.08
        row_h = max(row_h, h)
    return out, y0 + row_h


def paper(lt, items):
    for name, w, h in PAPERS:
        pos, used = layout(lt, items, w)
        if used <= h - MARGIN:
            return name, w, h, pos
    raise SystemExit('sheet does not fit A0')


def power_nets(lt, parts, pins):
    """Nets that need a PWR_FLAG for ERC: a power-input pin and no power-output pin."""
    kinds = {}
    for name in {p['lib'].split(':')[1] for p in parts.values()}:
        block = sch._lib_block(lt, name)
        kinds[name] = {num: kind for kind, num in
                       re.findall(r'\(pin (\w+) \w+\s*\(at [^)]*\)[\s\S]*?\(number "([^"]+)"', block)}
    has_in, has_out = set(), set()
    for (ref, pin), net in pins.items():
        if net is None:
            continue
        kind = kinds[parts[ref]['lib'].split(':')[1]].get(pin)
        (has_in if kind == 'power_in' else has_out if kind == 'power_out' else set()).add(net)
    return sorted(has_in - has_out)


def sheet_uuid(name):
    return uid('sheet:' + name)


def sheet_text(lt, name, title, page, parts, pins, flags=()):
    path = f'/{ROOT_UUID}' if name == 'm3.kicad_sch' else f'/{ROOT_UUID}/{sheet_uuid(name)}'
    refs = sorted((r for r, p in parts.items() if p['sheet'] == name), key=natural)
    items = [(r, parts[r]['lib'].split(':')[1], {pin: net for (rr, pin), net in pins.items() if rr == r}) for r in refs]
    if name == 'm3.kicad_sch':
        items += [(f'#FLG{i + 1:02d}', 'PWR_FLAG', {'1': net}) for i, net in enumerate(flags)]
    pname, w, h, pos = paper(lt, items)
    libs = sorted({p['lib'].split(':')[1] for r, p in parts.items() if p['sheet'] == name} |
                  ({'PWR_FLAG'} if name == 'm3.kicad_sch' and flags else set()))
    out = (f'(kicad_sch\n\t(version 20250114)\n\t(generator "m3_r12_sch")\n\t(uuid {ROOT_UUID if name == "m3.kicad_sch" else sheet_uuid(name)})\n'
           f'\t(paper "{pname}")\n\t(title_block\n\t\t(title "{title}")\n\t\t(date "{DATE}")\n\t\t(rev "{REV}")\n'
           f'\t\t(company "M3-ASSY-R12 stage A schematic; not reviewed, not ordered"))\n\t(lib_symbols\n')
    out += ''.join(sch._embed(lt, n) for n in libs) + '\t)\n'
    out += sch.note(f'{REV} ({title}): drawn from R11 {R11_COMMIT} with circuit.json (R12_DECISIONS.md); every pin '
                    f'reaches a global label.', MARGIN, MARGIN, 'x').replace(sch.uid('x'), uid('note:' + name))
    for ref, sym, nets in items:
        x, y = pos[ref]
        if sym == 'PWR_FLAG':
            out += flag_text(ref, nets['1'], x + 7.62, y, path)
        else:
            out += symbol_text(lt, ref, parts[ref], nets, x, y, path)
    if name == 'm3.kicad_sch':
        y = h - MARGIN - 15.24
        for i, (fname, ftitle) in enumerate(SHEETS[1:]):
            x = MARGIN + (i % 4) * 96.52
            yy = y - (i // 4) * 15.24 - 30.48
            u = sheet_uuid(fname)
            out += (f'\t(sheet\n\t\t(at {sch.fmt(x)} {sch.fmt(yy)})\n\t\t(size 86.36 7.62)\n\t\t(stroke\n\t\t\t(width .254)\n'
                    f'\t\t\t(type default))\n\t\t(fill\n\t\t\t(color 0 0 0 0))\n\t\t(uuid {u})\n'
                    f'\t\t(property "Sheetname" "{ftitle}"\n\t\t\t(at {sch.fmt(x)} {sch.fmt(yy - 1.27)} 0)\n'
                    f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.05 1.05))\n\t\t\t\t(justify left)))\n'
                    f'\t\t(property "Sheetfile" "{fname}"\n\t\t\t(at {sch.fmt(x)} {sch.fmt(yy + 8.89)} 0)\n'
                    f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.05 1.05))\n\t\t\t\t(justify left)))\n'
                    f'\t\t(instances\n\t\t\t(project "m3"\n\t\t\t\t(path "/{ROOT_UUID}"\n\t\t\t\t\t(page "{i + 2}")))))\n')
    out += f'\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "{page}"))))\n'
    return out


# ---------------------------------------------------------------------------------------------------------------------
# project settings and DRU

# JLCPCB PCB capabilities, https://jlcpcb.com/capabilities/pcb-capabilities (multilayer): trace / space 0.09 mm. The
# cost study's live quote (cost_study.md section 2.1) found no surcharge at a 0.3 mm via drill and a 0.45 mm pad and a
# surcharge below 0.3 mm (+$16.88 at 0.25 mm on 4 layers): R12's via floor is 0.3 / 0.45 mm (D-R12-03), no via in pad.
R12_FLOOR = {'clearance': 0.1, 'track_width': 0.1, 'via_hole': 0.3, 'via_diameter': 0.45, 'via_hole_to_hole': 0.25,
             'pth_annular': 0.15, 'via_hole_clearance': 0.2}
KEEP_RULES = ('General copper to hole clearance', 'HRO M-12 internal SMD lands to locating holes',
              'Small GND pad thermal relief', 'Tag-Connect contact to foreign copper', 'R9 bare test pads to foreign copper',
              'JLC inner-layer PTH pad hole to copper', 'JLC outer-layer PTH hole to track', 'JLC pad hole to hole')
R12_RULES = (
    ('R12 board floor: copper clearance', f'clearance (min {R12_FLOOR["clearance"]}mm)', None,
     'JLC multilayer 0.09 mm, plus 0.01 mm'),
    ('R12 board floor: track width', f'track_width (min {R12_FLOOR["track_width"]}mm)', None,
     'JLC multilayer 0.09 mm, plus 0.01 mm'),
    ('R12 board floor: via drill', f'hole_size (min {R12_FLOOR["via_hole"]}mm)', "A.Type == 'Via'",
     'D-R12-03: 0.3 mm drill, no small-hole surcharge (cost_study.md section 2.1)'),
    ('R12 board floor: via diameter', f'via_diameter (min {R12_FLOOR["via_diameter"]}mm)', "A.Type == 'Via'",
     'D-R12-03: 0.45 mm via pad'),
    ('R12 board floor: via hole to hole', f'hole_to_hole (min {R12_FLOOR["via_hole_to_hole"]}mm)',
     "A.Type == 'Via' && B.Type == 'Via'", 'JLC 0.2 mm, plus 0.05 mm'),
    # D-R12-23: JLC lists 'via hole to track 0.2 mm' (capabilities page, read 2026-11-04); with R10's general 0.25 mm a
    # 0.3 mm via at a TFBGA-100 interstitial site (0.566 mm from four 0.40 mm balls) keeps only 0.216 mm, so the via hole
    # takes JLC's figure against tracks, SMD pads, vias and pours; plated pad holes keep the PTH rules above
    ('R12 via hole to copper', f'hole_clearance (min {R12_FLOOR["via_hole_clearance"]}mm)',
     "(A.Type == 'Via' && (B.Type != 'Pad' || B.Pad_Type == 'SMD')) || "
     "(B.Type == 'Via' && (A.Type != 'Pad' || A.Pad_Type == 'SMD'))", 'JLC via hole to track 0.2 mm'),
    ('R12 board floor: PTH pad annular ring', f'annular_width (min {R12_FLOOR["pth_annular"]}mm)',
     "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'", 'JLC 0.15 mm minimum, 0.20 recommended'),
)


def dru_conditional(rule_text):
    """True when a DRU rule is scoped by a condition or a layer clause (KiCad applies the last matching rule, so an
    unconditional floor written after a scoped rule of the same constraint silently replaces it: R12F1-TRI-11)."""
    return '(condition ' in rule_text or re.search(r'^\s*\(layer ', rule_text, re.M) is not None


def dru(text):
    """R11's (R10's) DRU rules kept by name and the R12 floors; every unconditional rule first (D-R12-88), then the
    scoped ones, each group in its listed order, so no unconditional floor follows (and overrides) a scoped rule."""
    rules = []
    for m in re.finditer(r'\(rule "([^"]+)"', text):
        if m.group(1) in KEEP_RULES:
            rules.append(text[m.start():sch.close_paren(text, m.start())])
    assert len(rules) == len(KEEP_RULES), 'R11 DRU rule set changed'
    for name, constraint, condition, why in R12_RULES:
        rules.append(f'# {why} (https://jlcpcb.com/capabilities/pcb-capabilities)\n(rule "{name}"\n' +
                     (f'  (condition "{condition}")\n' if condition else '') + f'  (constraint {constraint}))')
    rules = [r for r in rules if not dru_conditional(r)] + [r for r in rules if dru_conditional(r)]
    return ('(version 1)\n# M3-ASSY-R12 (D-R12-03): four layers at JLCPCB, one assembled side, 0.3 / 0.45 mm vias only. '
            'R10 / R11 rules kept by name;\n# the R12 floors follow JLC\'s multilayer capability and the cost study\'s '
            'no-surcharge via. Net classes and board setup are stage B\'s.\n' + '\n\n'.join(rules) + '\n')


R12_POWER_NETS = ('GND', '3V3', '3V3A', 'VCAP1', 'VCAP2', 'VLOGIC', 'BAT_IN', 'BAT_DAMP', 'RAW_PROTECTED', 'RAW_ACT',
                  'ACT_FET_S', 'PORT_4V8', 'PORT_SW', 'CAM_5V', 'CAM_SW', 'VBUS', 'SW_NODE')


def project_settings():
    pro = json.loads((INPUT / 'm3.kicad_pro').read_text())
    rules = pro['board']['design_settings']['rules']
    rules.update(min_clearance=R12_FLOOR['clearance'], min_track_width=R12_FLOOR['track_width'],
                 min_via_diameter=R12_FLOOR['via_diameter'], min_through_hole_diameter=R12_FLOOR['via_hole'],
                 min_via_annular_width=0.075, min_hole_to_hole=R12_FLOOR['via_hole_to_hole'])
    pro['meta']['filename'] = 'm3.kicad_pro'
    default = next(c for c in pro['net_settings']['classes'] if c['name'] == 'Default')
    default.update(track_width=0.1, clearance=0.1, via_diameter=0.45, via_drill=0.3)
    power = dict(default, name='Power', priority=0, track_width=0.3, clearance=0.1, via_diameter=0.45, via_drill=0.3)
    pro['net_settings']['classes'] = [default, power]
    pro['net_settings']['netclass_patterns'] = [{'netclass': 'Power', 'pattern': p} for p in R12_POWER_NETS]
    pro['sheets'] = [[ROOT_UUID, 'Root']] + [[sheet_uuid(f), t] for f, t in SHEETS[1:]]
    return json.dumps(pro, indent=2) + '\n'


# ---------------------------------------------------------------------------------------------------------------------

def build(out, netlist=True):
    source_check()
    data = circuit()
    assert data['status'] == 'frozen', 'circuit.json not frozen'
    assert (DESIGN / 'pin_table.tsv').read_text() == pin_table_text(), 'pin_table.tsv stale (run --pin-table)'
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if out != PROJECT.resolve():
        shutil.copytree(PROJECT / 'kilib', out / 'kilib', dirs_exist_ok=True)
    for name in ('sym-lib-table', 'fp-lib-table'):
        (out / name).write_text((INPUT / name).read_text())
    (out / 'm3.kicad_pro').write_text(project_settings())
    lt = (out / 'kilib/m3.kicad_sym').read_text()
    parts, pins = model(data)
    flags = power_nets(lt, parts, pins)
    for page, (name, title) in enumerate(SHEETS, 1):
        (out / name).write_text(sheet_text(lt, name, title, page, parts, pins, flags))
    for stale in set(p.name for p in out.glob('*.kicad_sch')) - set(SHEET_FILES):
        (out / stale).unlink()
    (out / 'm3.kicad_dru').write_text(dru((INPUT / 'm3.kicad_dru').read_text()))
    if netlist:
        sch.export_netlist(out)
    print(f'R12 schematic generated: {out}; {len(SHEETS)} sheets, {len(parts)} parts, {len(flags)} power flags')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--no-netlist', action='store_true')
    ap.add_argument('--pin-inputs', action='store_true')
    ap.add_argument('--pin-table', action='store_true')
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    if args.pin_inputs:
        pin_inputs(args.force)
    elif args.pin_table:
        source_check()
        (DESIGN / 'pin_table.tsv').write_text(pin_table_text())
        print('wrote', DESIGN / 'pin_table.tsv')
    elif args.out:
        build(args.out, not args.no_netlist)
    else:
        ap.error('--out, --pin-inputs or --pin-table')


if __name__ == '__main__':
    main()
