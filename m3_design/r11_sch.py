#!/usr/bin/env python3
"""Generate the M3-ASSY-R11 schematic from R10's hash-pinned sheets (R11_DECISIONS D-R11-01, -04 ... -06).

R11 is R10's circuit with new packages and connectors: every R10 net and part value carries over. The input is R10's
final sheets and netlist (commit deb179e), copied into m3_design/r11/design/r10_input/ with a SHA-256 manifest that is
checked before every generation. The change list is m3_design/r11/design/circuit.json; the MCU ball map is BALL below,
written out as m3_design/r11/design/pin_table.tsv (--pin-table) and checked against it.

usage: python3 -B m3_design/r11_sch.py --out m3_design/r11        (after r11_parts.py --library-only)
       python3 -B m3_design/r11_sch.py --pin-inputs [--force]     (one time: copy and hash R10's inputs)
       python3 -B m3_design/r11_sch.py --pin-table                (write pin_table.tsv from BALL and R10's table)
No version-control operations; --out is required for a build. Deterministic: fixed UUID namespace NS (distinct from
R10's), no search, no timestamps.
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
R10 = HERE / 'assembly_review'                       # R10's frozen project (read only, pinned below)
PROJECT = HERE / 'r11'
DESIGN = PROJECT / 'design'
INPUT = DESIGN / 'r10_input'
NS = uuid.UUID('1fd39066-86bb-5f2e-aa5e-1984ab081457')    # uuid5(URL, 'm3-assy-r11/schematic'); R10's is 1af735a9-...
REV, R10_REV = 'M3-ASSY-R11', 'M3-ASSY-R10'
R10_COMMIT = 'deb179e'

SHEETS = ('m3.kicad_sch', 'actuator_power.kicad_sch', 'battery_entry.kicad_sch', 'camera_connector.kicad_sch',
          'camera_power.kicad_sch', 'camera_uart.kicad_sch', 'diagnostics.kicad_sch', 'logic_power_path.kicad_sch',
          'mcu.kicad_sch', 'pullpin_buzzer.kicad_sch', 'pyro.kicad_sch', 'sensors.kicad_sch', 'servos.kicad_sch',
          'telemetry.kicad_sch', 'usb_sense.kicad_sch')
# R10 inputs copied into r10_input/ (name there <- path in R10's project)
INPUT_FILES = {**{s: s for s in SHEETS},
               'schematic.net.xml': 'schematic.net.xml', 'm3.kicad_dru': 'm3.kicad_dru', 'm3.kicad_pro': 'm3.kicad_pro',
               'sym-lib-table': 'sym-lib-table', 'fp-lib-table': 'fp-lib-table',
               'm3.kicad_sym': 'kilib/m3.kicad_sym',
               'pin_table.tsv': 'sources/r10_design/pin_table.tsv', 'circuit.json': 'sources/r10_design/circuit.json'}

# ---------------------------------------------------------------------------------------------------------------------
# U1: STM32H743VIH6 TFBGA-100. R10 LQFP100 pin -> TFBGA100 ball.
# Source: ST DS12110 Rev 8 (April 2021), https://www.st.com/resource/en/datasheet/stm32h743vi.pdf: Table 9 "Pin/ball
# definition" pp. 64-88 (LQFP100 and TFBGA100 columns; every GPIO, VBAT, NRST, VSSA, VDDA, BOOT0, both VCAP and the
# VSS pairs 49/E4 and 74/E5 share one Table 9 row) and Figure 6 "TFBGA100 pinout" p. 56 (top view). The supply pins
# that Table 9 lists on separate rows (LQFP VSS 10/26/99 and VDD 11/27/50/75/100; ball VSS C2/E6/J1, VDD D2/F5/K1,
# VDDLDO F4, VDD33USB F6) are paired here by net only: every one keeps its R10 net (GND or 3V3). Cross-checked against
# KiCad 10's MCU_ST_STM32H7 symbol STM32H743V_G-I_Hx (ST's own pin data): every ball and name agrees.
BALL = {'1': 'A3', '2': 'B3', '3': 'C3', '4': 'D3', '5': 'E3', '6': 'B2', '7': 'A2', '8': 'A1', '9': 'B1', '10': 'C2',
        '11': 'D2', '12': 'C1', '13': 'D1', '14': 'E1', '15': 'F1', '16': 'F2', '17': 'E2', '18': 'F3', '19': 'G1',
        '21': 'H1', '22': 'G2', '23': 'H2', '24': 'J2', '25': 'K2', '26': 'J1', '27': 'K1', '28': 'G3', '29': 'H3',
        '30': 'J3', '31': 'K3', '32': 'G4', '33': 'H4', '34': 'J4', '35': 'K4', '36': 'G5', '37': 'H5', '38': 'J5',
        '39': 'K5', '40': 'G6', '41': 'H6', '42': 'J6', '43': 'K6', '44': 'G7', '45': 'H7', '46': 'J7', '47': 'K7',
        '48': 'F8', '49': 'E4', '50': 'F5', '51': 'K8', '52': 'J8', '53': 'H10', '54': 'G10', '55': 'K9', '56': 'J9',
        '57': 'H9', '58': 'G9', '59': 'K10', '60': 'J10', '61': 'H8', '62': 'G8', '63': 'F10', '64': 'E10', '65': 'F9',
        '66': 'E9', '67': 'D9', '68': 'C9', '69': 'D10', '70': 'C10', '71': 'B10', '72': 'A10', '73': 'E7', '74': 'E5',
        '75': 'F6', '76': 'A9', '77': 'A8', '78': 'B9', '79': 'B8', '80': 'C8', '81': 'D8', '82': 'E8', '83': 'B7',
        '84': 'C7', '85': 'D7', '86': 'B6', '87': 'C6', '88': 'D6', '89': 'A7', '90': 'A6', '91': 'C5', '92': 'B5',
        '93': 'A5', '94': 'D5', '95': 'B4', '96': 'A4', '97': 'D4', '98': 'C4', '99': 'E6', '100': 'F4'}
BALL_NAMES = {'F4': 'VDDLDO', 'F6': 'VDD33USB', 'F7': 'PDR_ON'}   # TFBGA100 supply balls with no LQFP100 equivalent
VREF_PIN = '20'          # LQFP100 VREF+: no TFBGA100 ball (Table 9 note 7 p. 88: double-bonded to VDDA in the package)
PDR_ON = 'F7'            # TFBGA100 PDR_ON: tied to VDD (3V3), as LQFP100 ties it internally (DS12110 Rev 8 p. 23 note 4)
PDR_ON_NET = '3V3'
BALL_SOURCE = ('DS12110 Rev 8 Table 9 pp. 64-88 (LQFP100 / TFBGA100 columns) and Figure 6 p. 56; '
               'KiCad 10 MCU_ST_STM32H7 STM32H743V_G-I_Hx agrees')
BALL_NOTES = {
    '10': 'supply pair by net (no shared Table 9 row): VSS, both GND', '26': 'supply pair by net: VSS, both GND',
    '99': 'supply pair by net: VSS, both GND', '11': 'supply pair by net: VDD, both 3V3',
    '27': 'supply pair by net: VDD, both 3V3', '50': 'supply pair by net: VDD, both 3V3',
    '75': ('ball F6 is VDD33USB (Table 9 p. 78): tied to 3V3 = VDD, the USB regulator bypassed as DS12110 Rev 8 '
           'p. 27 permits when VDD = 3.3 V; LQFP100 has no separate USB supply (p. 18)'),
    '100': ('ball F4 is VDDLDO (Table 9 p. 87): tied to 3V3 = VDD, as LQFP100 ties it internally (Table 9 note 8 p. 88)'),
}

# D-R11-41 / D-R11-49 (stageC1b.md): R11 re-pins for the BGA escape plan. {LQFP100 pin: (R11 net or 'NC', mode, note)};
# every other ball keeps R10's r10_net. The nets themselves are R10's (the net contract is unchanged); only the ball that
# carries them moves, to a ball whose alternate function DS12110 Rev 8 Tables 10-14 pp. 89-96 give (a GPIO needs no
# alternate function: Table 9). D-R11-49 re-pins every movable function to a ball in the outer two rings (or one row-C
# dog-bone) on its target's side; the firmware binding must follow these rows (stageC1b.md section 8 binding list).
NC_MODE = 'NC (firmware: analog, never driven)'
R11_REPIN = {
    # D-R11-49 (escape-first, stageC1b.md section 8): every movable function re-assigned by board side
    # aft (north) row A / B: camera UART on UART4 (PB9 / PB8, F.Cu lanes x 22.8 / 23.2), servos 1 / 2 on TIM4 / TIM2
    '96': ('CAM_MCU_TX', 'AF8 UART4_TX',
           'R11 D-R11-49: DS12110 Rev 8 Table 11 p. 91 (Port B alternate functions: PB9 AF8 UART4_TX); was PE8 '
           'UART7_TX (ball J5); a ROM-loader pin (I2C1_SDA), allowance case in stageC1b.md section 8'),
    '95': ('CAM_MCU_RX', 'AF8 UART4_RX',
           'R11 D-R11-49: DS12110 Rev 8 Table 11 p. 91 (Port B alternate functions: PB8 AF8 UART4_RX); was PE7 '
           'UART7_RX (ball H5)'),
    '93': ('SERVO1_MCU', 'AF2 TIM4_CH2 (servo PWM, 50-400 Hz)',
           'R11 D-R11-49: DS12110 Rev 8 Table 11 p. 91 (Port B alternate functions: PB7 AF2 TIM4_CH2); was PA0 '
           '(ball G2); R10 IMU_CS moved to PE3 (ball B3)'),
    '77': ('SERVO2_MCU', 'AF1 TIM2_CH1 (servo PWM, 50-400 Hz)',
           'R11 D-R11-49: DS12110 Rev 8 Table 10 p. 91 (Port A alternate functions: PA15 AF1 TIM2_CH1); was PA1 '
           '(ball H2); a ROM-loader pin (SPI3_NSS), allowance case in stageC1b.md section 8'),
    '2': ('IMU_CS', 'GPIO output push-pull; initialise high before output mode',
          'R11 D-R11-49: DS12110 Rev 8 Table 9 p. 64 (PE3, a general-purpose I/O); was PB7 (ball A5)'),
    # D-R11-81: IMU_INT1 on PD6 (ball C6, EXTI line 6), not PD5 (B6, EXTI line 5): SYSCFG_EXTICR selects one port per
    # EXTI line (RM0433), and line 5 is BAT_FAULT_N's (PA5, R10 firmware rule 7)
    '87': ('IMU_INT1', 'GPIO in, internal pull-down, EXTI6 data-ready interrupt (U4 INT1 push-pull, active high)',
           'R11 D-R11-81: DS12110 Rev 8 Table 9 p. 83 (PD6, a general-purpose I/O; EXTI line 6, used by no other '
           'interrupt net); was PD5 (ball B6, D-R11-49, EXTI line 5 shared with BAT_FAULT_N on PA5) and PE1 (ball C4, '
           'R10); R10 USB_FAULT_N moved to PD10 (ball H9)'),
    '86': ('NC', NC_MODE, 'R11 D-R11-81: PD5 freed (IMU_INT1 moved to PD6, ball C6; R10 LED_RED moved to PB1, ball K4)'),
    '98': ('NC', NC_MODE, 'R11 D-R11-49: PE1 freed (IMU_INT1 moved to PD5, ball B6; D-R11-81: then to PD6, ball C6)'),
    '24': ('NC', NC_MODE, 'R11 D-R11-49: PA2 freed (SERVO3_MCU moved to PA0, ball G2); a ROM-loader pin left unconnected'),
    '25': ('NC', NC_MODE, 'R11 D-R11-49: PA3 freed (SERVO4_MCU moved to PA1, ball H2); a ROM-loader pin left unconnected'),
    '22': ('SERVO3_MCU', 'AF2 TIM5_CH1 (servo PWM, 50-400 Hz)',
           'R11 D-R11-49: DS12110 Rev 8 Table 10 p. 89 (Port A alternate functions: PA0 AF2 TIM5_CH1); was PA2 '
           '(ball J2, a ROM-loader pin)'),
    '23': ('SERVO4_MCU', 'AF2 TIM5_CH2 (servo PWM, 50-400 Hz)',
           'R11 D-R11-49: DS12110 Rev 8 Table 10 p. 89 (Port A alternate functions: PA1 AF2 TIM5_CH2); was PA3 '
           '(ball K2, a ROM-loader pin)'),
    '39': ('NC', NC_MODE, 'R11 D-R11-49: PE9 freed (CAM_UART_OE moved to PC15, ball B1)'),
    '38': ('BUZZ_DRV', 'GPIO out (push-pull; initialise low before output mode)',
           'R11 D-R11-49: DS12110 Rev 8 Table 9 p. 71 (PE8, a general-purpose I/O); was PC14 (R10) and PB15 (ball '
           'G10, D-R11-42); R10 CAM_MCU_TX moved to PB9 (ball A4)'),
    # I2C (D-R11-41): the R10 nets I2C1_SCL / I2C1_SDA on peripheral I2C2, south row
    '46': ('I2C1_SCL', 'AF4 I2C2_SCL (the R10 net I2C1_SCL, now on peripheral I2C2)',
           'R11 D-R11-41: DS12110 Rev 8 Table 11 p. 91 (Port B alternate functions: PB10 AF4 I2C2_SCL); a ROM-loader '
           'pin (USART3_TX), allowance case in stageC1b.md section 7'),
    '47': ('I2C1_SDA', 'AF4 I2C2_SDA (the R10 net I2C1_SDA, now on peripheral I2C2)',
           'R11 D-R11-41: DS12110 Rev 8 Table 11 p. 91 (Port B alternate functions: PB11 AF4 I2C2_SDA); a ROM-loader '
           'pin (USART3_RX), allowance case in stageC1b.md section 7'),
    # camera control (D-R11-49): from the south rows to the north-west corner (PC13-PC15) and the west column (PC2_C);
    # camera control on PC13-PC15 (north-west corner), west to east in the order of their targets: OE (R102 / U12.6),
    # PWR_EN (U402.3 / R431), FAULT_N (U402.4 / R432)
    '9': ('CAM_UART_OE', 'GPIO out (push-pull, low speed; PC15 sources at most 3 mA and toggles at most 2 MHz)',
          'R11 D-R11-49: DS12110 Rev 8 Table 9 p. 65 (PC15), Table 62 p. 142 (PC13-PC15 output levels at 3 mA) and '
          'p. 143 note 2 (2 MHz); the load is U12 OE and R102 10k: at most 0.33 mA (Calculation); was PE9 (ball K5)'),
    '8': ('CAM_PWR_EN', 'GPIO out (push-pull, low speed; PC14 sources at most 3 mA and toggles at most 2 MHz)',
          'R11 D-R11-49: DS12110 Rev 8 Table 9 p. 65 (PC14, LSE off), Table 62 p. 142 and p. 143 note 2; the load is '
          'U402 EN and R431 100k: at most 0.04 mA (Calculation); was PE11 (ball H6, a ROM-loader pin)'),
    '7': ('CAM_FAULT_N', 'GPIO in (U402 FAULT open drain, R432 10k pull-up)',
          'R11 D-R11-49: DS12110 Rev 8 Table 9 p. 64 (PC13, a general-purpose I/O); was PE12 (ball J6, a ROM-loader '
          'pin)'),
    '17': ('CAM_5V_SENSE', 'ADC (ADC3_INP0, PC2_C analog pad)',
           'R11 D-R11-49: DS12110 Rev 8 Table 9 p. 67 (PC2_C: ANA pad, ADC3_INP0) and note 6 p. 88; was PB1 '
           '(ball K4, ADC12_INP5)'),
    '57': ('USB_FAULT_N', 'GPIO in',
           'R11 D-R11-49: DS12110 Rev 8 Table 9 p. 75 (PD10, a general-purpose I/O); was PD6 (ball C6, now IMU_INT1, '
           'D-R11-81)'),
    '35': ('LED_RED', 'GPIO out',
           'R11 D-R11-49: DS12110 Rev 8 Table 9 p. 70 (PB1, a general-purpose I/O); was PD5 (ball B6); LED1 / R32 '
           'moved forward beside the ports; R10 CAM_5V_SENSE moved to PC2_C (ball E2)'),
    '37': ('NC', NC_MODE, 'R11 D-R11-49: PE7 freed (CAM_MCU_RX moved to PB8, ball B4)'),
    '41': ('NC', NC_MODE, 'R11 D-R11-49: PE11 freed (CAM_PWR_EN moved to PC14, ball A1); a ROM-loader pin left unconnected'),
    '42': ('NC', NC_MODE, 'R11 D-R11-49: PE12 freed (CAM_FAULT_N moved to PC13, ball A2); a ROM-loader pin left '
                    'unconnected'),
    # status (D-R11-49)
    '83': ('LED_YEL', 'GPIO out',
           'R11 D-R11-49: DS12110 Rev 8 Table 9 p. 83 (PD2, a general-purpose I/O); was PD7 (ball D6)'),
    '88': ('NC', NC_MODE, 'R11 D-R11-49: PD7 freed (LED_YEL moved to PD2, ball B7)'),
}


def r11_net(pin, r10_net):
    return R11_REPIN[pin][0] if pin in R11_REPIN else r10_net


def uid(key):
    return str(uuid.uuid5(NS, key))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------------------------------------------
# pinned inputs

def r10_library_files():
    """R10 kilib files R11 may copy: every footprint the R10 netlist uses and the 3D models they name."""
    root = ET.parse(R10 / 'schematic.net.xml').getroot()
    names = sorted({c.findtext('footprint').split(':')[1] for c in root.findall('./components/comp')})
    files = []
    for name in names:
        fp = R10 / 'kilib/rocket.pretty' / (name + '.kicad_mod')
        files.append(fp)
        for model in re.findall(r'\(model "\$\{KIPRJMOD\}/([^"]+)"', fp.read_text()):
            files.append(R10 / model)
    return files


def pin_inputs(force=False):
    if (INPUT / 'manifest.json').exists() and not force:
        raise SystemExit('r10_input already pinned; use --force to re-pin (changes every downstream hash)')
    INPUT.mkdir(parents=True, exist_ok=True)
    for name, source in INPUT_FILES.items():
        shutil.copy2(R10 / source, INPUT / name)
    manifest = {
        'source': f'm3_design/assembly_review at commit {R10_COMMIT} (R10 board a0ec075e..., closing pair rounds 35 / 36)',
        'files': {name: sha(INPUT / name) for name in sorted(INPUT_FILES)},
        'library': {str(p.relative_to(ROOT_DIR)): sha(p) for p in r10_library_files()},
        'note': 'r11_sch.source_check() verifies every hash before each generation; library files stay in R10\'s kilib',
    }
    (INPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'pinned {len(manifest["files"])} R10 files and {len(manifest["library"])} R10 library files')


def source_check():
    data = json.loads((INPUT / 'manifest.json').read_text())
    assert set(data['files']) == set(INPUT_FILES), 'r10_input manifest lists other files'
    for name, digest in data['files'].items():
        assert sha(INPUT / name) == digest, f'R10 input changed: {name}'
    for rel, digest in data['library'].items():
        assert sha(ROOT_DIR / rel) == digest, f'R10 library file changed: {rel}'
    return data


def circuit():
    return json.loads((DESIGN / 'circuit.json').read_text())


def r10_netlist():
    root = ET.parse(INPUT / 'schematic.net.xml').getroot()
    parts = {c.get('ref'): c for c in root.findall('./components/comp')}
    pins = {(p.get('ref'), p.get('pin')): None if n.get('name').startswith('unconnected-') else n.get('name')
            for n in root.findall('./nets/net') for p in n.findall('node')}
    return parts, pins


def r10_pin_rows():
    return list(csv.DictReader((INPUT / 'pin_table.tsv').open(), delimiter='\t'))


# ---------------------------------------------------------------------------------------------------------------------
# pin table

PIN_TABLE_HEADER = ('# M3-ASSY-R11 U1 pin table: STM32H743VIH6 TFBGA-100 (JLC C964146). Columns as R10\'s '
                    'pin_table.tsv (r10_input/pin_table.tsv, the reviewed function map) plus r11_ball, r11_net and '
                    'r11_ball_source. Ball names: ST DS12110 Rev 8 (April 2021) Table 9 pp. 64-88 and Figure 6 p. 56; '
                    'VREF+ note 7 and VDDLDO note 8 p. 88; PDR_ON p. 23 note 4 and p. 29. R10\'s source column is kept '
                    'verbatim and still cites LQFP100 pin numbers; the ball is r11_ball. Lines starting with # are comments.\n')


def pin_rows():
    """R10's rows with the ball, the R11 net and the ball source; VREF+ has no ball, PDR_ON is added."""
    out = []
    for row in r10_pin_rows():
        pin = row['pin']
        new = dict(row)
        if pin == VREF_PIN:
            new.update(r11_ball='-', r11_net='-', r11_ball_source=(
                'no TFBGA100 ball: VREF+ is double-bonded to VDDA (3V3A) inside the package and the internal '
                'reference buffer must be kept disabled (DS12110 Rev 8 Table 9 note 7 p. 88); R10 tied VREF+ to VDDA '
                'on the board, so the circuit is the same'))
        else:
            new.update(r11_ball=BALL[pin], r11_net=r11_net(pin, row['r10_net']),
                       r11_ball_source=BALL_SOURCE + ('; ' + BALL_NOTES[pin] if pin in BALL_NOTES else '') +
                       ('; ' + R11_REPIN[pin][2] + '; R11 mode: ' + R11_REPIN[pin][1] if pin in R11_REPIN else ''))
        out.append(new)
    extra = {k: '-' for k in out[0]}
    extra.update(pin='-', port='PDR_ON', r9_net='-', r10_net='-', mode_af='input, tied high',
                 reset_contract='tied to 3V3 (VDD): power-down reset supervisor on, as on R10',
                 source='DS12110 Rev 8 Table 9 p. 87 (PDR_ON, TFBGA100 F7)',
                 an2606_t119_loader_role='not a GPIO', r11_ball=PDR_ON, r11_net=PDR_ON_NET,
                 r11_ball_source=('TFBGA100 only: LQFP100 has no PDR_ON pin and ties it to VDD internally (DS12110 Rev 8 '
                                  'p. 23 note 4); PDR_ON low disables the internal reset supervisor (p. 29) and VBAT '
                                  'operation (p. 37), so R11 ties it to 3V3'))
    out.append(extra)
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


def pin_map(ref, data):
    """{R10 pin: [R11 pins]} for a ref whose pin numbering changes; identity otherwise."""
    if ref == 'U1':
        return {p: [b] for p, b in BALL.items()}
    return data['pin_maps'].get(ref)


# ---------------------------------------------------------------------------------------------------------------------
# sheet editing

def instance(text, ref):
    read, _, _ = sch._reader()
    for node in read(text).children('symbol'):
        if any(p.items[1].atom == 'Reference' and p.items[2].atom == ref for p in node.children('property')):
            return node
    return None


def lib_name(node):
    return node.children('lib_id')[0].items[1].atom.split(':')[1]


def points(text, ref, library):
    node = instance(text, ref)
    x, y, angle = [float(v.atom) for v in node.children('at')[0].items[1:4]]
    assert angle == 0, f'{ref}: rotated symbol'
    return {p: (round(x + px, 2), round(y - py, 2), a) for p, (px, py, a) in sch._lib_pins(library, lib_name(node)).items()}


def rewire(text, ref, pin, net, library):
    """Replace the wire and label at one pin with a new 5.08 mm wire to a global label `net`."""
    x, y, angle = points(text, ref, library)[pin]
    text = sch.disconnect(text, {(x, y)})
    dx, dy = {0: (-5.08, 0), 180: (5.08, 0), 90: (0, 5.08), 270: (0, -5.08)}[int(angle)]
    bx, by = round(x + dx, 2), round(y + dy, 2)
    return sch.insert(text, sch.wire(x, y, bx, by, f'{ref}:r11:w{pin}') +
                      sch.glabel(net, bx, by, f'{ref}:r11:l{pin}', 180 if dx > 0 else 0, 'left' if dx > 0 else 'right'))


def repin(text, ball, net, library):
    """D-R11-41: give one U1 ball a new net (a 5.08 mm wire and global label, as rewire) or none (a no-connect
    flag), removing R10's wire, label or flag at that pin."""
    if net is not None:
        return rewire(text, 'U1', ball, net, library)
    x, y, _ = points(text, 'U1', library)[ball]
    text = sch.disconnect(text, {(x, y)})
    return sch.insert(text, f'\t(no_connect\n\t\t(at {x:g} {y:g})\n\t\t(uuid {uid("U1:r11:nc" + ball)}))\n')


def embed(text, library, name):
    read, patch, _ = sch._reader()
    libs = read(text).children('lib_symbols')[0]
    if f'(symbol "M3:{name}"\n' in text:
        return text
    return patch(text, [(libs.end - 1, libs.end - 1, sch._embed(library, name))])


def set_symbol(text, ref, spec, library):
    """Rewrite one placed symbol's lib_id, Value, Footprint, Datasheet and part fields, and its BOM / position flags."""
    read, patch, properties = sch._reader()
    node = instance(text, ref)
    props = properties(node)
    edits = []
    if spec.get('lib') and spec['lib'] != 'M3:' + lib_name(node):
        lid = node.children('lib_id')[0].items[1]
        edits.append((lid.start, lid.end, sch_quote(spec['lib'])))
    for name in ('Value', 'Footprint', 'Datasheet', 'LCSC', 'Manufacturer', 'Manufacturer Part', 'LCSC Part'):
        # D-R11-78: R10's redundant `LCSC Part` field follows the part's `LCSC` code (AGENTS section 3: redundant
        # identity fields may agree, never contradict); it is never added where R10 had none.
        want = spec['props'].get('LCSC' if name == 'LCSC Part' else name)
        if name == 'LCSC Part' and name not in props:
            continue
        if name in props and want is None:
            edits.append((text.rfind('\n', 0, props[name].start), props[name].end, ''))  # with its line break
        elif name in props:
            edits.append((props[name].items[2].start, props[name].items[2].end, sch_quote(want)))
        elif want is not None:
            x, y = sch._xy(node)
            inst = node.children('instances')[0]
            edits.append((inst.start, inst.start, sch.prop(name, want, x, y).lstrip('\t') + '\t\t'))
    for flag, value in (('in_bom', spec.get('in_bom', True)),):
        f = node.children(flag)[0].items[1]
        edits.append((f.start, f.end, 'yes' if value else 'no'))
    text = patch(text, edits)
    if spec.get('in_pos_files') is False and '(in_pos_files no)' not in sch_block(text, ref):
        node = instance(text, ref)
        board = node.children('on_board')[0]
        text = patch(text, [(board.end, board.end, '\n\t\t(in_pos_files no)')])
    return text


def sch_quote(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def sch_block(text, ref):
    node = instance(text, ref)
    return text[node.start:node.end]


def replace_symbol(text, ref, spec, nets, library, path):
    """Remove a symbol with its pin wires / labels and draw the new symbol at the same place with the given nets
    (sch._sym: one 5.08 mm wire and a global label per pin). The symbol UUID is kept."""
    node = instance(text, ref)
    x, y = sch._xy(node)
    old_uuid = node.children('uuid')[0].items[1].atom
    pts = points(text, ref, library)
    text = sch.disconnect(text, {v[:2] for v in pts.values()})
    node = instance(text, ref)
    text = text[:node.start] + text[node.end:]
    fields = {k: v for k, v in spec['props'].items() if k not in ('Value', 'Footprint') and v is not None}
    sch.RF_PARTS = {ref: (spec['lib'], spec['props']['Value'], spec['props']['Footprint'], fields, nets, 'fit')}
    sch.FLAGS = {}
    text = embed(text, library, spec['lib'].split(':')[1])
    text = sch.insert(text, sch._sym(library, ref, x, y, path))
    return text.replace('(uuid ' + uid(ref) + ')', '(uuid ' + old_uuid + ')')


def sheet_path(name):
    text = (INPUT / 'm3.kicad_sch').read_text()
    for m in re.finditer(r'\(sheet\n', text):
        block = text[m.start():sch.close_paren(text, m.start())]
        if f'(property "Sheetfile" "{name}"' in block:
            return '/' + sch.ROOT + '/' + re.search(r'\(uuid ([0-9a-f-]+)\)', block).group(1)
    raise AssertionError(f'no sheet symbol for {name}')


def replace_note(text, prefix, line):
    read, patch, _ = sch._reader()
    found = [n for n in read(text).children('text') if n.items[1].atom.startswith(prefix)]
    assert len(found) == 1, f'expected one note starting {prefix!r}, found {len(found)}'
    x, y = sch._xy(found[0])
    text = patch(text, [(found[0].start, found[0].end, '')])
    return sch.insert(text, sch.note(line, x, y, f'note:r11:{prefix}'))


def ball_text(text):
    """Re-key LQFP100 pin citations in notes: 'U1.<pin>' -> 'U1.<ball>'."""
    return re.sub(r'U1\.(\d{1,3})\b', lambda m: 'U1.' + BALL[m.group(1)], text)


# Sheet notes R10 wrote about the screw terminals, LQFP pin numbers or package-specific ties, rewritten for R11
# (matched by their opening words; every other R10 note is kept verbatim apart from the U1.<pin> re-key).
NOTES = {
    'camera_connector.kicad_sch': {
        'R10 owner screw terminals: J9': ('R11 (D-R11-05): J9 is a latching JST GH SM06B-GHS-TB 6-pin header: pins 1 and 2 '
                                          'CAM_5V, 3 and 4 GND, 5 CAM_RX_WIRE (board RX), 6 CAM_TX_WIRE (board TX); the '
                                          '1 A camera allowance is 0.5 A per contact (GH 1.0 A per contact, JST eGH p1). '
                                          'Camera U12/U13 isolation and the U402 switch retained.'),
        'No physical portkeying': ('GH is keyed and latching (JST eGH p1). Label all six pins, verify the harness '
                                   'end-to-end and polarity before power; GH crimps take AWG 30-26 only (JST eGH p2). '
                                   'Current and loop-resistance limits stay.')},
    'servos.kicad_sch': {
        'R10 owner screw terminals: J122': ('R11 (D-R11-05): J122 is a latching JST GH SM05B-GHS-TB: pins 1-4 '
                                            'SERVO1-4_OUT, pin 5 GND signal reference. No servo positive connection on board.'),
        'J122 DORABO': ('J122 JST SM05B-GHS-TB (C189896); signal only, AWG 30-26 GH crimps (JST eGH p2). Servo power '
                        'and motor return stay in the pack-star harness.')},
    'telemetry.kicad_sch': {
        'R10: always-on GPS J410': ('R11 (D-R11-05): always-on GPS J410, radio J420 and spare AUX J440 (D-R19-14), three '
                                    'electrically identical latching JST GH SM04B-GHS-TB ports: pin 1 PORT_4V8, 2 GND, '
                                    '3 board TX, 4 board RX; harness crosses TX to endpoint RX.'),
        'J410/J420/J440 are unkeyed': ('J410/J420/J440 are keyed latching JST SM04B-GHS-TB (C189895), 1.0 A per contact '
                                       '(JST eGH p1). Label power/GND/TX/RX per pin; verify polarity and harness '
                                       'crossing before power.')},
    'battery_entry.kicad_sch': {
        'J400.1 / J400.2': ('J400.1 / J400.2 (BAT_SW_SOURCE / BAT_SW_RETURN): external dry screw-switch contact on a '
                            'latching JST GH SM02B-GHS-TB (R11, D-R11-05). Closed = battery enabled; open/disconnected '
                            '= OFF. USB remains independent. J1 is a pair of plated AWG 20 wire pads (R11).')},
    'pyro.kicad_sch': {
        'R10 single screw switch: RAW_ACT': ('R10 single screw switch: RAW_ACT directly feeds R134.2 and R132.1 behind '
                                             'Q120/Q121; no separate ARM terminal or PYRO1_BUS net. J121.2 IGN, J121.1 '
                                             'OUT: plated AWG 20 wire pads on R11 (D-R11-05), with a permanent pigtail to '
                                             'the bay\'s field terminal.')},
    'mcu.kicad_sch': {
        'R10: camera enable CAM_PWR_EN': ('R10: camera enable CAM_PWR_EN on PE11 / ball H6, fault input CAM_FAULT_N '
                                          '(EXTI12) on PE12 / ball J6 (GPIO only, SPI4 never enabled); swapped from R8 '
                                          'for routing (D-R2-07); no actuation changes.'),
        'R10: PE3 (pin 2) and PE5': ('R10: PE3 (ball B3) and PE5 (ball D3) flank the PE4 fire ball (C3); PE3, PE5, PE6 '
                                     '(E3) and PC4 (G4) have no net and stay analog (their reset state), never driven '
                                     '(R5-MCU-03, R19-MCU-03). R8: LED_RED on PD5 (B6), LED_YEL on PD7 (D6).'),
        'R10 MCU map': None},     # filled from R10's text below (pin numbers -> balls)
    'camera_uart.kicad_sch': {
        'R8: PE8/pin38 UART7_TX': ('R8: PE8 (ball J5) UART7_TX and PE7 (ball H5) UART7_RX use AF7, no flow control (never '
                                   'AF7 on PE9 or PE10); off the ROM loader\'s USART3. R10: PE9 (ball K5) CAM_UART_OE '
                                   'drives OE as a GPIO; R102 10k holds it low (R19-MCU-03).')},
    'diagnostics.kicad_sch': {'CAM_5V_SENSE = CAM_5V x 1k/11k': None},
    'usb_sense.kicad_sch': {'PC8 / U1 pin65 (R8)': ('PC8 / U1 ball F9 (R8) is a regular FT_h GPIO input (EXTI8). PA9 '
                                                     'remains NC. D+/D- are unchanged.')},
}
R11_MCU_NOTE = ('R11 (D-R11-04): U1 is the STM32H743VIH6 TFBGA-100; pin_table.tsv r11_ball is the ball map. VREF+ has no '
                'ball and is double-bonded to VDDA in the package (DS12110 Rev 8 Table 9 note 7 p. 88): keep VREFBUF '
                'disabled. PDR_ON (F7), VDDLDO (F4) and VDD33USB (F6) are tied to 3V3, as LQFP100 ties them inside the '
                'package (p. 23 note 4, Table 9 note 8 p. 88; USB regulator bypassed, p. 27).')


def notes(text, name):
    for prefix, line in NOTES.get(name, {}).items():
        if line is None:
            read, _, _ = sch._reader()
            found = [n for n in read(text).children('text') if n.items[1].atom.startswith(prefix)]
            assert len(found) == 1, (name, prefix)
            line = found[0].items[1].atom
            line = re.sub(r'\(pin (\d+), ', lambda m: f'(ball {BALL[m.group(1)]}, ', line)
            line = line.replace('"', '\\"')
            if prefix == 'R10 MCU map':
                line = line.replace('R10 MCU map (pin_table.tsv r10_net is the sole authority)',
                                    'R10 MCU map, R11 balls in pin_table.tsv r11_ball (r10_net is the sole function authority)')
        text = replace_note(text, prefix, line)
    read, patch, _ = sch._reader()
    edits = []
    for n in read(text).children('text'):
        atom = n.items[1]
        new = ball_text(text[atom.start:atom.end])
        if new != text[atom.start:atom.end]:
            edits.append((atom.start, atom.end, new))
    text = patch(text, edits)
    if name == 'mcu.kicad_sch':
        text = sch.insert(text, sch.note(R11_MCU_NOTE, 20.32, 289.56, 'mcu:r11:package'))
    return text


def transform(text, name, library, data, nets):
    path = None if name == 'm3.kicad_sch' else sheet_path(name)
    for ref, spec in sorted(data['parts'].items()):
        if instance(text, ref) is None:
            continue
        old = lib_name(instance(text, ref))
        if ref in data['pin_maps'] and ref != 'U1':
            new_nets = {}
            for old_pin, new_pins in data['pin_maps'][ref].items():
                for p in new_pins:
                    new_nets[p] = nets[ref, old_pin]
            text = replace_symbol(text, ref, spec, new_nets, library, path)
            text = set_symbol(text, ref, spec, library)
            continue
        text = set_symbol(text, ref, spec, library)
        if spec.get('lib') and spec['lib'] != 'M3:' + old:
            text = embed(text, library, spec['lib'].split(':')[1])
        if ref == 'U1':
            text = rewire(text, 'U1', PDR_ON, PDR_ON_NET, library)
            for pin, (net, _, _) in sorted(R11_REPIN.items()):
                text = repin(text, BALL[pin], None if net == 'NC' else net, library)
    text = notes(text, name)
    for prefix in ('M3:',):
        for sym in sorted(set(re.findall(r'\t\t\(symbol "M3:([^"]+)"\n', text))):
            used = re.search(r'\(lib_id "M3:' + re.escape(sym) + r'"\)', text)
            if used:
                text = sch.refresh_embedded(text, library, sym)
            else:     # an embedded symbol no placed symbol uses any more (MCU, CameraTerminal)
                s = text.index(f'\t\t(symbol "M3:{sym}"\n')
                text = text[:s] + text[sch.close_paren(text, s + 2):].lstrip('\n')
    assert text.count(f'(rev "{R10_REV}")') == 1, name
    text = text.replace(f'(rev "{R10_REV}")', f'(rev "{REV}")')
    return re.sub(r'\n(?:\s*\n)+', '\n', text)


# ---------------------------------------------------------------------------------------------------------------------
# project settings and DRU

# JLCPCB PCB capabilities, https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-02 (multilayer, 1 oz):
# trace / space 0.09 / 0.09 mm; via 0.15 mm hole / 0.25 mm diameter; via hole-to-hole 0.2 mm; pad hole-to-hole 0.45 mm;
# PTH annular ring 0.15 mm minimum (0.20 recommended); PTH to track 0.28 mm (0.35 recommended); inner-layer PTH pad hole
# to copper 0.3 mm; SMD pad to pad 0.15 mm; BGA pad >= 0.2 mm, BGA pad to trace 0.09 mm; copper to routed edge 0.2 mm;
# filled and capped via-in-pad is the default from 6 layers.
R11_FLOOR = {'clearance': 0.1, 'track_width': 0.1, 'via_hole': 0.15, 'via_diameter': 0.25, 'via_hole_to_hole': 0.2,
             'pth_annular': 0.15}
KEEP_RULES = ('General copper to hole clearance', 'HRO M-12 internal SMD lands to locating holes',
              'Small GND pad thermal relief', 'Tag-Connect contact to foreign copper', 'R9 bare test pads to foreign copper',
              'JLC inner-layer PTH pad hole to copper', 'JLC outer-layer PTH hole to track', 'JLC pad hole to hole')
R11_RULES = (
    ('R11 board floor: copper clearance', None, None, f'clearance (min {R11_FLOOR["clearance"]}mm)',
     'JLC multilayer 0.09 mm, plus 0.01 mm'),
    ('R11 board floor: track width', None, None, f'track_width (min {R11_FLOOR["track_width"]}mm)',
     'JLC multilayer 0.09 mm, plus 0.01 mm'),
    ('R11 board floor: via drill', None, "A.Type == 'Via'", f'hole_size (min {R11_FLOOR["via_hole"]}mm)', 'JLC 0.15 mm'),
    ('R11 board floor: via diameter', None, "A.Type == 'Via'", f'via_diameter (min {R11_FLOOR["via_diameter"]}mm)',
     'JLC 0.25 mm'),
    ('R11 board floor: via hole to hole', None, "A.Type == 'Via' && B.Type == 'Via'",
     f'hole_to_hole (min {R11_FLOOR["via_hole_to_hole"]}mm)', 'JLC 0.2 mm'),
    ('R11 board floor: PTH pad annular ring', None, "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'",
     f'annular_width (min {R11_FLOOR["pth_annular"]}mm)', 'JLC 0.15 mm minimum, 0.20 recommended'),
)


def dru(text):
    """R10's DRU rules kept by name, then the R11 board floors (JLC 6-layer capability, cited above)."""
    rules = []
    for m in re.finditer(r'\(rule "([^"]+)"', text):
        if m.group(1) in KEEP_RULES:
            rules.append(text[m.start():sch.close_paren(text, m.start())])
    assert len(rules) == len(KEEP_RULES), 'R10 DRU rule set changed'
    for name, layer, condition, constraint, why in R11_RULES:
        rules.append(f'# {why} (https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-02)\n(rule "{name}"\n' +
                     (f'  (layer {layer})\n' if layer else '') + (f'  (condition "{condition}")\n' if condition else '') +
                     f'  (constraint {constraint}))')
    return ('(version 1)\n# M3-ASSY-R11 (D-R11-03): six layers at JLCPCB. R10\'s rules kept by name (the D-R21-01 0.55 mm '
            'inner PTH hole clearance included);\n# the R11 floors follow JLC\'s multilayer capability. Net classes and '
            'board setup are stage B\'s.\n' + '\n\n'.join(rules) + '\n')


def project_settings():
    """R10's m3.kicad_pro with the board-setup minimums lowered to the R11 floors (JLC multilayer)."""
    pro = json.loads((INPUT / 'm3.kicad_pro').read_text())
    rules = pro['board']['design_settings']['rules']
    rules.update(min_clearance=R11_FLOOR['clearance'], min_track_width=R11_FLOOR['track_width'],
                 min_via_diameter=R11_FLOOR['via_diameter'], min_through_hole_diameter=R11_FLOOR['via_hole'],
                 min_via_annular_width=0.05, min_hole_to_hole=R11_FLOOR['via_hole_to_hole'])
    pro['meta']['filename'] = 'm3.kicad_pro'
    # D-R11-15 (stage C1): net classes. Default = the BGA signal class: 0.1 mm track and clearance (JLC multilayer
    # 0.09 mm track / space plus 0.01, https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-02; the DRU floor
    # rule enforces it), 0.4 / 0.2 mm via (stageB.md section 10). Power = R10's rail widths start at 0.3 mm (the families
    # size each path per IPC-2152 for 0.5 oz inner / 1 oz outer copper), 0.45 / 0.25 mm via. DRC clearance comes from
    # m3.kicad_dru; the classes set the interactive defaults and record the intent.
    default = next(c for c in pro['net_settings']['classes'] if c['name'] == 'Default')
    default.update(track_width=0.1, clearance=0.1, via_diameter=0.4, via_drill=0.2)
    power = dict(default, name='Power', priority=0, track_width=0.3, clearance=0.1, via_diameter=0.45, via_drill=0.25)
    pro['net_settings']['classes'] = [default, power]
    pro['net_settings']['netclass_patterns'] = [
        {'netclass': 'Power', 'pattern': p} for p in R11_POWER_NETS]
    return json.dumps(pro, indent=2) + '\n'


# rails of the Power net class (stage C1, D-R11-15)
R11_POWER_NETS = ('GND', '3V3', '3V3A', 'VCAP1', 'VCAP2', 'VLOGIC', 'BAT_IN', 'BAT_DAMP', 'RAW_PROTECTED', 'RAW_ACT',
                  'ACT_FET_S', 'PORT_5V3', 'PORT_4V8', 'PORT_SW', 'CAM_5V', 'VBUS', 'USB_LIMITED', 'SW_NODE')


# ---------------------------------------------------------------------------------------------------------------------

def specs(data):
    """{ref: {'lib', 'props', 'in_bom', 'in_pos_files'}} from circuit.json's catalog and per-ref entries."""
    out = {}
    for ref, entry in data['parts'].items():
        code = entry.get('lcsc')
        if code:
            cat = data['catalog'][code]
            props = {'Value': entry['value'], 'Footprint': cat['footprint'], 'Datasheet': cat['Datasheet'],
                     'LCSC': code, 'Manufacturer': cat['Manufacturer'], 'Manufacturer Part': cat['Manufacturer Part']}
        else:
            props = {'Value': entry['value'], 'Footprint': entry['footprint'], 'Datasheet': entry.get('Datasheet', ''),
                     'LCSC': '', 'Manufacturer': None, 'Manufacturer Part': None}
        out[ref] = {'lib': entry.get('lib'), 'props': props, 'in_bom': entry.get('in_bom', True),
                    'in_pos_files': entry.get('in_pos_files', True)}
    return out


def build(out, netlist=True):
    source_check()
    data = circuit()
    assert data['status'] == 'frozen', 'circuit.json not frozen'
    assert (DESIGN / 'pin_table.tsv').read_text() == pin_table_text(), 'pin_table.tsv differs from BALL (run --pin-table)'
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if out != PROJECT.resolve():
        shutil.copytree(PROJECT / 'kilib', out / 'kilib', dirs_exist_ok=True)
    for name in ('sym-lib-table', 'fp-lib-table'):
        (out / name).write_text((INPUT / name).read_text())
    (out / 'm3.kicad_pro').write_text(project_settings())
    library = (out / 'kilib/m3.kicad_sym').read_text()
    sch.NS = NS
    _, nets = r10_netlist()
    work = dict(data, parts=specs(data))
    work['pin_maps'] = data['pin_maps']
    for name in SHEETS:
        text = transform((INPUT / name).read_text(), name, library, work, nets)
        (out / name).write_text(text)
    (out / 'm3.kicad_dru').write_text(dru((INPUT / 'm3.kicad_dru').read_text()))
    if netlist:
        sch.export_netlist(out)
    print(f'R11 schematic generated: {out}; {len(SHEETS)} sheets, {len(data["parts"])} changed parts')


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
