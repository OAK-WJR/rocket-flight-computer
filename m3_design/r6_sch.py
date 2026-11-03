#!/usr/bin/env python3
"""Reproducible R5 -> R6 schematic transform. Run before r6 PCB construction.

New parts/pins are exported as TLM_PARTS/TLM_MCU_PINS for the board builder.
The existing R5 files are the input; repeat runs make no changes.
"""
import re
import sys
import uuid
from pathlib import Path

D = Path(sys.argv[1] if len(sys.argv) > 1 else 'm3_design/assembly_review')
ROOT = '6007a7db-6a58-5660-8beb-956dea045ff8'
NS = uuid.UUID('5f1c0e3a-8d64-4c1b-9a52-4d334f525236')   # fixed namespace -> stable R6 UUIDs
GRID = 2.54


def uid(*key):
    return str(uuid.uuid5(NS, ':'.join(key)))


def fmt(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.') if abs(v - round(v, 2)) < 1e-9 else repr(v)


def effects(size, justify=None, hide=False):
    j = f'\n\t\t\t\t(justify {justify})' if justify else ''
    h = '\n\t\t\t(hide yes)' if hide else ''
    return f'{h}\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size {size} {size})){j})'


def prop(name, value, x, y, hide=True, justify='left'):
    return f'\t\t(property "{name}" "{value}"\n\t\t\t(at {fmt(x)} {fmt(y)} 0){effects(1.27, justify, hide)})\n'


def sheet_path(text):
    """Instance path of the sheet (root uuid / sheet uuid), read from an existing symbol."""
    m = re.search(r'\(path "(/' + ROOT + r'/[0-9a-f-]+)"', text)
    if not m:
        raise SystemExit('no instance path found in sheet')
    return m.group(1)


def close_paren(text, start):
    """Index just past the parenthesis that closes the one opening at text[start] (skips strings)."""
    depth, i, n, in_str = 0, start, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            if c == '\\':
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise SystemExit('unbalanced parentheses')


def symbol_block(text, ref):
    """(start, end) of the top-level symbol whose Reference is ref, or None."""
    i = text.find(f'(property "Reference" "{ref}"')
    if i < 0:
        return None
    s = text.rfind('\n\t(symbol\n', 0, i) + 2          # at the '('
    return s, close_paren(text, s)


def wire(x1, y1, x2, y2, key):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {fmt(x1)} {fmt(y1)})\n\t\t\t(xy {fmt(x2)} {fmt(y2)}))\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default))\n\t\t(uuid {uid(key)}))\n')


def glabel(net, x, y, key, angle=0, justify='right'):
    return (f'\t(global_label "{net}"\n\t\t(shape passive)\n\t\t(at {fmt(x)} {fmt(y)} {angle})'
            f'\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.05 1.05))\n\t\t\t(justify {justify}))\n\t\t(uuid {uid(key)}))\n')


def note(textline, x, y, key):
    return (f'\t(text "{textline}"\n\t\t(at {fmt(x)} {fmt(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.05 1.05))'
            f'\n\t\t\t(justify left))\n\t\t(uuid {uid(key)}))\n')


def two_pin(ref, lib_id, value, footprint, fields, x, y, net1, net2, path):
    """Vertical 2-pin M3:R / M3:C symbol at (x, y): pin 1 at y - 3.81 (top), pin 2 at y + 3.81.
    Each pin gets a 7.62 mm wire to the left ending in a global label (the sheet's style)."""
    body = (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {fmt(x)} {fmt(y)} 0)\n\t\t(unit 1)\n'
            f'\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(uuid {uid(ref)})\n')
    body += prop('Reference', ref, x + GRID, y - 1.27, hide=False)
    body += prop('Value', value, x + GRID, y + 1.27, hide=False)
    body += prop('Footprint', footprint, x, y)
    body += prop('Datasheet', '', x, y)
    for k, v in fields.items():
        body += prop(k, v, x, y)
    body += (f'\t\t(instances\n\t\t\t(project "m3"\n\t\t\t\t(path "{path}"\n'
             f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)))))\n')
    out = body
    for pin, (py, net) in enumerate(((y - 3.81, net1), (y + 3.81, net2)), 1):
        out += wire(x, py, x - 3 * GRID, py, f'{ref}:w{pin}')
        out += glabel(net, x - 3 * GRID, py, f'{ref}:l{pin}')
    return out


def insert(text, chunk):
    i = text.rfind('\t(sheet_instances')
    return text[:i] + chunk + text[i:]


def set_props(text, ref, updates, optional=()):
    """Set existing properties of a symbol; names in `optional` are skipped when the symbol lacks them."""
    s, e = symbol_block(text, ref)
    blk = text[s:e]
    for k, v in updates.items():
        blk, n = re.subn(r'(\(property "' + re.escape(k) + r'" )"[^"]*"', r'\g<1>"' + v + '"', blk)
        if n == 0 and k in ('LCSC Part', 'Manufacturer', 'Manufacturer Part'):
            blk = blk[:-1] + prop(k, v, 0, 0) + ')'
            n = 1
        if n != 1 and not (n == 0 and k in optional):
            raise SystemExit(f'{ref}: property {k} found {n} times')
    return text[:s] + blk + text[e:]


def replace_note(text, old_prefix, new_text):
    """Replace the (text "...") note that starts with old_prefix by new_text (no-op when already done)."""
    if f'(text "{new_text}"' in text:
        return text
    pat = r'\(text "' + re.escape(old_prefix) + r'[^"]*"'
    text, n = re.subn(pat, lambda _m: f'(text "{new_text}"', text)
    if n != 1:
        raise SystemExit(f'note {old_prefix!r} found {n} times')
    return text



TLM_SHEET = 'telemetry.kicad_sch'
TLM_SHEET_UUID = uid('sheet', 'telemetry')
TLM_TITLE = '15 | Telemetry radio and GPS port'
TLM_PARTS = {'U14': ('M3:CameraBuck',
         'AP63301WU-7',
         'rocket:M3_AP63200_TSOT26',
         {'LCSC': 'C2158003', 'Manufacturer': 'Diodes Incorporated', 'Manufacturer Part': 'AP63301WU-7'},
         {'1': 'TLM_FB', '2': 'TLM_EN', '3': 'TLM_INPUT_LIMITED', '4': 'GND', '5': 'TLM_SW', '6': 'TLM_BST'}),
 'L4': ('M3:L',
        '6.8uH',
        'rocket:M3_SRP5030TA',
        {'LCSC': 'C1329837',
         'Manufacturer': 'Bourns',
         'Manufacturer Part': 'SRP5030T-6R8M',
         'LCSC Part': 'C1329837'},
        {'1': 'TLM_SW', '2': 'TLM_5V_REG'}),
 'C170': ('M3:C',
          '22uF 25V X7R 10%',
          'rocket:M3_GRM32_1210',
          {'LCSC': 'C21397',
           'Manufacturer': 'Murata',
           'Manufacturer Part': 'GRM32ER71E226KE15L',
           'LCSC Part': 'C21397'},
          {'1': 'TLM_INPUT_LIMITED', '2': 'GND'}),
 'C171': ('M3:C',
          '22uF 25V X7R 10%',
          'rocket:M3_GRM32_1210',
          {'LCSC': 'C21397',
           'Manufacturer': 'Murata',
           'Manufacturer Part': 'GRM32ER71E226KE15L',
           'LCSC Part': 'C21397'},
          {'1': 'TLM_5V_REG', '2': 'GND'}),
 'C172': ('M3:C',
          '22uF 25V X7R 10%',
          'rocket:M3_GRM32_1210',
          {'LCSC': 'C21397',
           'Manufacturer': 'Murata',
           'Manufacturer Part': 'GRM32ER71E226KE15L',
           'LCSC Part': 'C21397'},
          {'1': 'TLM_5V_REG', '2': 'GND'}),
 'C173': ('M3:C',
          '100nF 50V X7R 10%',
          'rocket:C_0603_1608Metric',
          {'LCSC': 'C14663',
           'Manufacturer': 'YAGEO',
           'Manufacturer Part': 'CC0603KRX7R9BB104',
           'LCSC Part': 'C14663'},
          {'1': 'TLM_SW', '2': 'TLM_BST'}),
 'C174': ('M3:C',
          '47pF 50V C0G 5%',
          'rocket:C_0603_1608Metric',
          {'LCSC': 'C1671',
           'Manufacturer': 'Samsung Electro-Mechanics',
           'Manufacturer Part': 'CL10C470JB8NNNC',
           'LCSC Part': 'C1671'},
          {'1': 'TLM_5V_REG', '2': 'TLM_FB'}),
 'R190': ('M3:R',
          '300k 1%',
          'rocket:R_0603_1608Metric',
          {'LCSC': 'C23024',
           'LCSC Part': 'C23024',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)',
           'Manufacturer Part': '0603WAF3003T5E'},
          {'1': 'TLM_5V_REG', '2': 'TLM_FB'}),
 'R206': ('M3:R',
          '300k 1%',
          'rocket:R_0603_1608Metric',
          {'LCSC': 'C23024',
           'LCSC Part': 'C23024',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)',
           'Manufacturer Part': '0603WAF3003T5E'},
          {'1': 'TLM_5V_REG', '2': 'TLM_FB'}),
 'R191': ('M3:R',
          '30k 1%',
          'rocket:R_0603_1608Metric',
          {'LCSC': 'C22984',
           'LCSC Part': 'C22984',
           'Manufacturer': 'UNI-ROYAL',
           'Manufacturer Part': '0603WAF3002T5E'},
          {'1': 'TLM_FB', '2': 'GND'}),
 'R192': ('M3:R',
          '1k',
          'rocket:R0402',
          {'LCSC': 'C11702', 'LCSC Part': 'C11702',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1001TCE'},
          {'1': 'TLM_PWR_EN', '2': 'TLM_EN'}),
 'R193': ('M3:R', '10k', 'rocket:R0402', {'LCSC': 'C25744', 'LCSC Part': 'C25744',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1002TCE'}, {'1': 'TLM_EN', '2': 'GND'}),
 'U15': ('M3:USBCurrentLimit',
         'TPS2553DBVR',
         'rocket:M3_TPS2553_DBV',
         {'LCSC': 'C55266',
          'LCSC Part': 'C55266',
          'Manufacturer': 'Texas Instruments',
          'Manufacturer Part': 'TPS2553DBVR'},
         {'1': 'TLM_5V_REG',
          '2': 'GND',
          '3': 'TLM_5V_REG',
          '4': 'TLM_FAULT_N',
          '5': 'TLM_ILIM',
          '6': 'TLM_5V'}),
 'R194': ('M3:R', '66.5k 1%', 'rocket:R_0603_1608Metric',
          {'LCSC': 'C137691', 'LCSC Part': 'C137691', 'Manufacturer': 'Yageo',
           'Manufacturer Part': 'RC0603FR-0766K5L'}, {'1': 'TLM_ILIM', '2': 'GND'}),
 'TP130': ('M3:TestPoint', 'TLM_5V', 'rocket:M3_TestPad_1.5', {'LCSC': ''}, {'1': 'TLM_5V'}),
 'J130': ('M3:Conn_1x7',
          'RADIO M0/M1/RXD/TXD/AUX/VCC/GND',
          'rocket:M3_SH_BM07B_SRSS_TB',
          {'LCSC': 'C160393',
           'LCSC Part': 'C160393',
           'Manufacturer': 'JST',
           'Manufacturer Part': 'BM07B-SRSS-TB(LF)(SN)'},
          {'1': 'RADIO_M0',
           '2': 'RADIO_M1',
           '3': 'RADIO_RXD',
           '4': 'RADIO_TXD',
           '5': 'RADIO_AUX',
           '6': 'TLM_5V',
           '7': 'GND'}),
 'J131': ('M3:Conn_1x4',
          'GPS 5V/GND/TX/RX',
          'rocket:M3_SH_BM04B_SRSS_TB',
          {'LCSC': 'C160390',
           'LCSC Part': 'C160390',
           'Manufacturer': 'JST',
           'Manufacturer Part': 'BM04B-SRSS-TB(LF)(SN)'},
          {'1': 'TLM_5V', '2': 'GND', '3': 'GPS_TXD', '4': 'GPS_RXD'}),
 'R196': ('M3:R',
          '1k',
          'rocket:R0402',
          {'LCSC': 'C11702', 'LCSC Part': 'C11702',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1001TCE'},
          {'1': 'RADIO_M0_MCU', '2': 'RADIO_M0'}),
 'R197': ('M3:R',
          '1k',
          'rocket:R0402',
          {'LCSC': 'C11702', 'LCSC Part': 'C11702',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1001TCE'},
          {'1': 'RADIO_M1_MCU', '2': 'RADIO_M1'}),
 'R198': ('M3:R',
          '1k',
          'rocket:R0402',
          {'LCSC': 'C11702', 'LCSC Part': 'C11702',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1001TCE'},
          {'1': 'RADIO_TX_MCU', '2': 'RADIO_RXD'}),
 'R199': ('M3:R',
          '1k',
          'rocket:R0402',
          {'LCSC': 'C11702', 'LCSC Part': 'C11702',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1001TCE'},
          {'1': 'RADIO_RX_MCU', '2': 'RADIO_TXD'}),
 'R200': ('M3:R',
          '1k',
          'rocket:R0402',
          {'LCSC': 'C11702', 'LCSC Part': 'C11702',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1001TCE'},
          {'1': 'RADIO_AUX_MCU', '2': 'RADIO_AUX'}),
 'R201': ('M3:R',
          '1k',
          'rocket:R0402',
          {'LCSC': 'C11702', 'LCSC Part': 'C11702',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1001TCE'},
          {'1': 'GPS_TX_MCU', '2': 'GPS_RXD'}),
 'R202': ('M3:R',
          '1k',
          'rocket:R0402',
          {'LCSC': 'C11702', 'LCSC Part': 'C11702',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1001TCE'},
          {'1': 'GPS_RX_MCU', '2': 'GPS_TXD'}),
 'U16': ('M3:CameraEFuse',
         'TPS259570DSGR',
         'rocket:M3_TPS2595_DSG',
         {'LCSC': 'C1849463',
          'LCSC Part': 'C1849463',
          'Manufacturer': 'Texas Instruments',
          'Manufacturer Part': 'TPS259570DSGR'},
         {'1': 'TLM_DVDT',
          '2': 'TLM_EN',
          '3': 'RAW_PROTECTED',
          '4': 'RAW_PROTECTED',
          '5': 'TLM_INPUT_LIMITED',
          '6': 'TLM_FAULT_N',
          '7': 'TLM_INPUT_ILIM',
          '8': 'GND',
          '9': 'GND'}),
 'R195': ('M3:R',
          '4.42k 0.5%',
          'rocket:R_0603_1608Metric',
          {'LCSC': 'C728617',
           'LCSC Part': 'C728617',
           'Manufacturer': 'YAGEO',
           'Manufacturer Part': 'RT0603DRD074K42L'},
          {'1': 'TLM_INPUT_ILIM', '2': 'GND'}),
 'C175': ('M3:C',
          '100nF 50V X7R 10%',
          'rocket:C_0603_1608Metric',
          {'LCSC': 'C14663',
           'LCSC Part': 'C14663',
           'Manufacturer': 'YAGEO',
           'Manufacturer Part': 'CC0603KRX7R9BB104'},
          {'1': 'TLM_5V_REG', '2': 'GND'}),
 'C177': ('M3:C',
          '100nF 50V X7R 10%',
          'rocket:C_0603_1608Metric',
          {'LCSC': 'C14663',
           'LCSC Part': 'C14663',
           'Manufacturer': 'YAGEO',
           'Manufacturer Part': 'CC0603KRX7R9BB104'},
          {'1': 'RAW_PROTECTED', '2': 'GND'}),
 'C179': ('M3:C',
          '100nF 50V X7R 10%',
          'rocket:C_0603_1608Metric',
          {'LCSC': 'C14663',
           'LCSC Part': 'C14663',
           'Manufacturer': 'YAGEO',
           'Manufacturer Part': 'CC0603KRX7R9BB104'},
          {'1': '3V3', '2': 'GND'}),
 'C180': ('M3:C',
          '100nF 50V X7R 10%',
          'rocket:C_0603_1608Metric',
          {'LCSC': 'C14663',
           'LCSC Part': 'C14663',
           'Manufacturer': 'YAGEO',
           'Manufacturer Part': 'CC0603KRX7R9BB104'},
          {'1': '3V3', '2': 'GND'}),
 'C176': ('M3:C',
          '1uF',
          'rocket:C0603',
          {'LCSC': 'C29936', 'LCSC Part': 'C29936',
           'Manufacturer': 'Samsung Electro-Mechanics', 'Manufacturer Part': 'CL10B105KA8NNNC'},
          {'1': 'TLM_5V', '2': 'GND'}),
 'C178': ('M3:C',
          '4.7nF 50V C0G 5%',
          'rocket:C_0603_1608Metric',
          {'LCSC': 'C85980',
           'LCSC Part': 'C85980',
           'Manufacturer': 'Murata',
           'Manufacturer Part': 'GRM1885C1H472JA01D'},
          {'1': 'TLM_DVDT', '2': 'GND'}),
 'R203': ('M3:R',
          '10k',
          'rocket:R0402',
          {'LCSC': 'C25744', 'LCSC Part': 'C25744',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1002TCE'},
          {'1': 'RADIO_M0_MCU', '2': 'GND'}),
 'R204': ('M3:R',
          '10k',
          'rocket:R0402',
          {'LCSC': 'C25744', 'LCSC Part': 'C25744',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1002TCE'},
          {'1': 'RADIO_M1_MCU', '2': 'GND'}),
 'R205': ('M3:R',
          '10k',
          'rocket:R0402',
          {'LCSC': 'C25744', 'LCSC Part': 'C25744',
           'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0402WGF1002TCE'},
          {'1': '3V3', '2': 'TLM_FAULT_N'}),
 'D130': ('M3:SRV05_4',
          'SRV05-4.TCT',
          'rocket:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL',
          {'LCSC': 'C13612',
           'LCSC Part': 'C13612',
           'Manufacturer': 'SEMTECH',
           'Manufacturer Part': 'SRV05-4.TCT'},
          {'1': 'RADIO_M0_MCU',
           '2': 'GND',
           '3': 'RADIO_M1_MCU',
           '4': 'RADIO_TX_MCU',
           '5': '3V3',
           '6': 'RADIO_RX_MCU'}),
 'D131': ('M3:SRV05_4',
          'SRV05-4.TCT',
          'rocket:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL',
          {'LCSC': 'C13612',
           'LCSC Part': 'C13612',
           'Manufacturer': 'SEMTECH',
           'Manufacturer Part': 'SRV05-4.TCT'},
          {'1': 'RADIO_AUX_MCU', '2': 'GND', '3': 'GPS_TX_MCU', '4': 'GPS_RX_MCU', '5': '3V3', '6': 'GND'})}

TLM_MCU_PINS = {'63': 'RADIO_TX_MCU',
 '64': 'RADIO_RX_MCU',
 '65': 'RADIO_M0_MCU',
 '66': 'RADIO_M1_MCU',
 '67': 'RADIO_AUX_MCU',
 '68': 'GPS_TX_MCU',
 '69': 'GPS_RX_MCU',
 '31': 'TLM_FAULT_N',
 '51': 'TLM_PWR_EN'}

def _lib_block(lt, name):
    i = lt.index(f'\t(symbol "{name}"\n')
    return lt[i:close_paren(lt, i + 1)]


def _lib_pins(lt, name):
    """{pin number: (x, y, angle)} of a library symbol (y up, as stored)."""
    out = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)[\s\S]*?\(number "([^"]+)"', _lib_block(lt, name)):
        out[m.group(4)] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
    return out


CONN_1X7 = None                                  # built from Conn_1x4 by t_conn_1x7()


def t_conn_1x7(lt):
    """M3:Conn_1x7 for J130 (the Conn_1x4 symbol with seven pins on the same 2.54 mm pitch)."""
    if '\t(symbol "Conn_1x7"\n' in lt:
        return lt
    blk = _lib_block(lt, 'Conn_1x4').replace('Conn_1x4', 'Conn_1x7').replace('4-position connector', '7-position connector')
    blk = blk.replace('(at 0 7.62 0)', '(at 0 11.43 0)').replace('(at 0 -7.62 0)', '(at 0 -11.43 0)')
    blk = blk.replace('(start -2.54 5.08)', '(start -2.54 8.89)').replace('(end 2.54 -5.08)', '(end 2.54 -8.89)')
    i = blk.index('\t\t\t(pin passive line')
    pin = blk[i:blk.index('\t\t\t(pin passive line', i + 10)]      # pin 1, complete, with its newline
    pins = ''.join(pin.replace('(at -7.62 3.81 0)', f'(at -7.62 {7.62 - 2.54 * k:g} 0)')
                      .replace('"1"', f'"{k + 1}"') for k in range(7))
    unit_end = blk.index('))\n\t\t(embedded_fonts') + 1              # skip pin 4's closing paren, keep the unit's
    blk = blk[:i] + pins.rstrip('\n') + blk[unit_end:]
    k = lt.rindex(')')
    return lt[:k] + blk + '\n' + lt[k:]


def _embed(lt, name):
    blk = _lib_block(lt, name).replace(f'(symbol "{name}"', f'(symbol "M3:{name}"', 1)
    return ''.join('\t' + line for line in blk.splitlines(True)) + '\n'


def _sym(lt, ref, x, y, path):
    """One TLM_PARTS symbol at (x, y) in the house style: every pin reaches a global label through a 5.08 mm wire."""
    lib_id, value, fp, fields, nets = TLM_PARTS[ref]
    name = lib_id.split(':')[1]
    body = (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {fmt(x)} {fmt(y)} 0)\n\t\t(unit 1)\n'
            f'\t\t(in_bom {"no" if name == "TestPoint" else "yes"})\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(uuid {uid(ref)})\n')
    body += prop('Reference', ref, x + GRID, y - 1.27, hide=False)
    body += prop('Value', value, x + GRID, y + 1.27, hide=False)
    body += prop('Footprint', fp, x, y)
    body += prop('Datasheet', '', x, y)
    for k, v in fields.items():
        body += prop(k, v, x, y)
    body += (f'\t\t(instances\n\t\t\t(project "m3"\n\t\t\t\t(path "{path}"\n'
             f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)))))\n')
    for num, (px, py, ang) in sorted(_lib_pins(lt, name).items()):
        if num not in nets:
            continue
        ax, ay = x + px, y - py
        dx, dy = {0: (-5.08, 0), 180: (5.08, 0), 90: (0, 5.08), 270: (0, -5.08)}[int(ang) % 360]
        bx, by = ax + dx, ay + dy
        body += wire(ax, ay, bx, by, f'{ref}:w{num}')
        body += glabel(nets[num], bx, by, f'{ref}:l{num}', angle=0 if dx <= 0 else 180, justify='right' if dx <= 0 else 'left')
    return body



TLM_LAYOUT = {'U16': (55.88, 83.82),
 'R195': (114.3, 83.82),
 'C178': (139.7, 83.82),
 'C177': (165.1, 83.82),
 'R192': (200.66, 83.82),
 'R193': (231.14, 83.82),
 'R205': (261.62, 83.82),
 'C170': (40.64, 132.08),
 'U14': (91.44, 132.08),
 'C173': (149.86, 132.08),
 'L4': (175.26, 132.08),
 'C171': (205.74, 132.08),
 'C172': (236.22, 132.08),
 'R190': (266.7, 132.08),
 'R206': (266.7, 157.48),
 'C174': (297.18, 132.08),
 'R191': (327.66, 132.08),
 'U15': (55.88, 180.34),
 'R194': (114.3, 180.34),
 'C175': (139.7, 180.34),
 'C176': (165.1, 180.34),
 'TP130': (200.66, 180.34),
 'J130': (55.88, 233.68),
 'J131': (55.88, 279.4),
 'R196': (114.3, 226.06),
 'R197': (144.78, 226.06),
 'R198': (175.26, 226.06),
 'R199': (205.74, 226.06),
 'R200': (236.22, 226.06),
 'R203': (114.3, 256.54),
 'R204': (144.78, 256.54),
 'R201': (175.26, 279.4),
 'R202': (205.74, 279.4),
 'D130': (299.72, 226.06),
 'D131': (299.72, 279.4),
 'C179': (360.68, 226.06),
 'C180': (360.68, 279.4)}
TLM_NOTES = ['15 | Telemetry radio and GPS (R6); 5 V power, 3.3 V UART logic',
 'U16 limits branch input to 0.458-0.523 A; U15 R194=66.5k limits harness output to 351-449 mA including resistor tolerance. U9 R84 = 750R, '
 '3.956-4.845 A.',
 'U14 AP63301: (R190||R206)=150k over R191=30k, 4.8 V nominal; DC 4.674-4.930 V before ripple. GPS max5.0V: '
 'verify startup and TX peaks.',
 'R193 holds U16/U14 off in reset; R205 pulls wired open-drain fault to 3V3. M0/M1 have external reset '
 'pull-downs.',
 'E22-900T22D 2026 manual: 100-140 mA TX at 22 dBm; >=3.3 V for rated RF power. GPS current and '
 'simultaneous startup require measurement.',
 'PC6/PC7 USART6; PC8 M0, PC9 M1, PA8 AUX. PA9/PA10 USART1 GPS; disconnect GPS for ROM bootloader use.',
 '1k and SRV05-4 on all seven harness signals. J131 pins: 1=5V, 2=GND, 3=module TX, 4=module RX. '
 'Match harness pin numbers.',
 'At 6 V input, 4.93 V output and assumed 85% efficiency, 449 mA output requires 434 mA < U16 458 mA minimum.',
 'Radio commands cannot arm or fire. ARM is the physical J124 link; fire remains the local flight-control '
 'decision.']

def t_telemetry_sheet():
    """Section 1p: new sheet 15, generated from TLM_PARTS (the PCB side reads the same table)."""
    f = D / TLM_SHEET
    lt = (D / 'kilib' / 'm3.kicad_sym').read_text()
    path = f'/{ROOT}/{TLM_SHEET_UUID}'
    libs = sorted({v[0].split(':')[1] for v in TLM_PARTS.values()})
    out = (f'(kicad_sch\n\t(version 20250114)\n\t(generator "m3_r6_telemetry")\n\t(uuid {TLM_SHEET_UUID})\n\t(paper "A2")\n'
           f'\t(title_block\n\t\t(title "{TLM_TITLE}")\n\t\t(date "2026-10-13")\n\t\t(rev "M3-ASSY-R6")\n'
           f'\t\t(company "Single-board M3 candidate; telemetry port, not bench-verified"))\n\t(lib_symbols\n')
    out += ''.join(_embed(lt, n) for n in libs) + '\t)\n'
    for k, line in enumerate(TLM_NOTES):
        out += note(line, 20.32, 20.32 + 5.08 * k if k else 15.24, f'tlm:note{k}')
    for ref in TLM_PARTS:
        out += _sym(lt, ref, *TLM_LAYOUT[ref], path)
    out += '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "15"))))\n'
    if f.exists() and f.read_text() == out:
        return False
    f.write_text(out)
    return True


def t_root_sheet(t):
    """Root: sheet 15's block and a PWR_FLAG on TLM_5V_REG (its only drivers are passive: L4 and the caps)."""
    if TLM_SHEET in t:
        return t
    blk = (f'\t(sheet\n\t\t(at 294.64 231.14)\n\t\t(size 83.82 10.16)\n\t\t(stroke\n\t\t\t(width .254)\n\t\t\t(type default))\n'
           f'\t\t(fill\n\t\t\t(color 0 0 0 0))\n\t\t(uuid {TLM_SHEET_UUID})\n'
           f'\t\t(property "Sheetname" "{TLM_TITLE}"\n\t\t\t(at 294.64 229.87 0)\n\t\t\t(effects\n\t\t\t\t(font\n'
           f'\t\t\t\t\t(size 1.05 1.05))\n\t\t\t\t(justify left)))\n'
           f'\t\t(property "Sheetfile" "{TLM_SHEET}"\n\t\t\t(at 294.64 243.84 0)\n\t\t\t(effects\n\t\t\t\t(font\n'
           f'\t\t\t\t\t(size 1.05 1.05))\n\t\t\t\t(justify left)))\n'
           f'\t\t(instances\n\t\t\t(project "m3"\n\t\t\t\t(path "/{ROOT}"\n\t\t\t\t\t(page "15")))))\n')
    i = t.index('\t(sheet_instances')
    t = t[:i] + blk + t[i:]
    # PWR_FLAG: same shape as #FLG01..06 (x 35.56 .. 302.26 on y 218.44), next slot x 355.6
    s = t.index('\t(symbol\n\t\t(lib_id "M3:PWR_FLAG")')
    flag = t[s:close_paren(t, s + 1)] + '\n'
    flag = re.sub(r'\(uuid [0-9a-f-]+\)', f'(uuid {uid("FLG07")})', flag, count=1)
    flag = flag.replace('#FLG01', '#FLG07').replace('35.56', '355.6')
    flag += wire(355.6, 218.44, 347.98, 218.44, 'FLG07:w') + glabel('TLM_5V_REG', 347.98, 218.44, 'FLG07:l')
    i = t.index('\t(sheet\n')
    return t[:i] + flag + t[i:]


def t_mcu_pins(t):
    """Sheet 02: U1's nine telemetry pins lose their no-connect flags and get a wire and a global label each."""
    lt = (D / 'kilib' / 'm3.kicad_sym').read_text()
    pins = _lib_pins(lt, 'MCU')
    X, Y = 91.44, 132.08                         # U1's position on the sheet (asserted below)
    assert '(lib_id "M3:MCU")\n\t\t(at 91.44 132.08 0)' in t
    # Guard both known R6 assignment migrations; other pins are untouched.
    read, _, _ = _reader()
    def endpoint(num):
        px, py, ang = pins[num]
        return (round(X + px + (5.08 if int(ang) == 180 else -5.08), 2),
                round(Y - py, 2))
    for netname, old_pin, new_pin, key in (
            ('TLM_PWR_EN', '98', '51', 'port-enable-reassigned'),
            ('TLM_FAULT_N', '97', '31', 'port-fault-reassigned')):
        labels = [n for n in read(t).children('global_label') if n.items[1].atom == netname]
        if not labels:
            continue
        assert len(labels) == 1, f'duplicate {netname} labels'
        if _xy(labels[0]) != endpoint(new_pin):
            assert _xy(labels[0]) == endpoint(old_pin), f'unexpected {netname} assignment'
            px, py, _ = pins[old_pin]
            ax, ay = round(X + px, 2), round(Y - py, 2)
            t = disconnect(t, {(ax, ay)})
            t = insert(t, nc(ax, ay, f'U1:{key}:{old_pin}'))
    for num, netname in TLM_MCU_PINS.items():
        px, py, ang = pins[num]
        ax, ay = round(X + px, 2), round(Y - py, 2)
        lab = f'(global_label "{netname}"'
        if lab in t:
            continue
        pat = re.compile(r'\t\(no_connect\n\t\t\(at ' + re.escape(fmt(ax)) + ' ' + re.escape(fmt(ay)) + r'\)\n\t\t\(uuid [0-9a-f-]+\)\)\n')
        t, n = pat.subn('', t)
        assert n == 1, f'no-connect at U1 pin {num} ({ax}, {ay}) found {n} times'
        bx = ax + (5.08 if int(ang) == 180 else -5.08)
        t = insert(t, wire(ax, ay, bx, ay, f'U1:tlm:w{num}') +
                   glabel(netname, bx, ay, f'U1:tlm:l{num}', angle=180 if int(ang) == 180 else 0,
                          justify='left' if int(ang) == 180 else 'right'))
    return t


# CH1's electrical values, split dividers, ARM break and gate geometry are retained.
REMOVE_REFS = frozenset(('J120', 'J125', 'Q125', 'R135', 'R138', 'R139', 'R140', 'R141',
    'R142', 'R143', 'R144', 'R145', 'R169', 'R171', 'R174', 'R176', 'R179', 'R181',
    'C138', 'C139', 'C140', 'C141', 'TP123'))
SWD_PINS = {'1': '3V3', '2': 'SWDIO', '3': 'NRST', '4': 'SWCLK', '5': 'GND', '6': None}
UPDATED_PARTS = {
    'J9': {'Value': 'CAMERA 5V/GND/RX/TX', 'Footprint': 'rocket:M3_GH_BM04B_GHS_TBT',
           'LCSC': 'C161692', 'LCSC Part': 'C161692', 'Manufacturer': 'JST',
           'Manufacturer Part': 'BM04B-GHS-TBT(LF)(SN)'},
    'J2': {'Value': 'TC2030-IDC-NL SWD', 'Footprint': 'rocket:M3_TC2030_IDC_NL',
           'LCSC': '', 'LCSC Part': '', 'Manufacturer': 'Tag-Connect', 'Manufacturer Part': 'TC2030-IDC-NL'},
    'J121': {'Footprint': 'rocket:M3_DB128L_2P_BK', 'LCSC': 'C430601', 'LCSC Part': 'C430601',
             'Manufacturer': 'DORABO', 'Manufacturer Part': 'DB128L-5.08-2P-BK-S'},
    'R165': {'Footprint': 'rocket:R_0603_1608Metric', 'LCSC': 'C23178', 'LCSC Part': 'C23178',
             'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0603WAF4703T5E'},
    'LS120': {'Value': 'MLT-5020', 'Footprint': 'rocket:M3_MLT5020_3pad',
              'LCSC': 'C94598', 'LCSC Part': 'C94598', 'Manufacturer': 'Jiangsu Huaneng Elec',
              'Manufacturer Part': 'MLT-5020',
              'Datasheet': 'https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf'},
    'R84': {'Value': '750R 0.1%', 'LCSC': 'C861551', 'LCSC Part': 'C861551',
            'Manufacturer': 'YAGEO', 'Manufacturer Part': 'RT0603BRD07750RL'},
}


def nc(x, y, key):
    return f'\t(no_connect\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(uuid {uid(key)}))\n'


def _reader():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'quality_audit'))
    from sexpr import read, patch, properties
    return read, patch, properties


def _xy(node, child='at'):
    v = node.children(child)[0].items
    return tuple(round(float(a.atom), 2) for a in v[1:3])


def disconnect(t, points):
    """Remove only each pin's short wire, end label and/or no-connect marker."""
    read, patch, _ = _reader()
    root, edits, ends = read(t), [], set(points)
    for n in root.children('wire'):
        xy = {tuple(round(float(a.atom), 2) for a in p.items[1:3])
              for p in n.children('pts')[0].children('xy')}
        if xy & points:
            assert len(xy) == 2, 'unexpected branched connection'
            ends |= xy
            edits.append((n.start, n.end, ''))
    for key in ('global_label', 'no_connect'):
        for n in root.children(key):
            if _xy(n) in ends:
                edits.append((n.start, n.end, ''))
    return patch(t, edits)


def symbol_points(t, ref, lt):
    read, _, properties = _reader()
    syms = [s for s in read(t).children('symbol') if properties(s)['Reference'].items[2].atom == ref]
    if not syms:
        return {}
    sym = syms[0]
    x, y = _xy(sym)
    assert float(sym.children('at')[0].items[3].atom) == 0, ref
    name = sym.children('lib_id')[0].items[1].atom.split(':')[1]
    return {num: (round(x + px, 2), round(y - py, 2), ang)
            for num, (px, py, ang) in _lib_pins(lt, name).items()}


def remove_channel2(t, lt):
    for ref in sorted(REMOVE_REFS):
        if not symbol_block(t, ref):
            continue
        t = disconnect(t, {xy[:2] for xy in symbol_points(t, ref, lt).values()})
        s, e = symbol_block(t, ref)
        t = t[:s] + t[e:]
    return t


def r6_pyro(t, lt):
    t = set_props(t, 'J121', UPDATED_PARTS['J121'])
    t = t.replace('Black ARM; orange J121 igniter.', 'Black J124 ARM / J121 IGN; identify by silk and pin legends.')
    # The unused second cathode is left open; no source can reach removed CH2 copper.
    x, y, _ = symbol_points(t, 'D120', lt)['2']
    t = disconnect(t, {(x, y)})
    t = insert(t, nc(x, y, 'D120:unused-k2'))
    replacements = {
        'R134/R135:': 'R134: 2 ohm 2 W pulse-rated Bourns CRM2512; shorted-igniter current about 4 A. Firmware fire pulse <= 20 ms.',
        '12 | Pyro channels,': '12 | Single pyro CH1, arming and continuity',
        'Two independent channels': 'One pyro channel. J124.2 RAW -> external F1 5A FAST -> J124.1 BUS1. Black J124 ARM / J121 IGN; identify by silk and pin legends.',
        'With the plug out': 'With the ARM plug out NOTHING connects RAW_ACT to PYRO1_BUS. No test point on BUS, IGN or OUT.',
        'Igniter 1 across': 'Igniter across J121.1 OUT and J121.2 IGN. J124 and J121 pin ordering is retained from the reviewed CH1.',
        'CONT =': 'CONT: R173 + R129 over R130 || R178 from drain. ARM: R132 + R175 over R133 || R180 from fused bus.',
        'D120 + R131/R143': 'D120 cathode 1 + R131 10k: cold pull-up for plug-out FET-short detection. Cathode 2 NC. In flight: log only, never veto.',
        'Pass 11: each divider top': 'Split divider tops: R173 + R129 and R132 + R175 (2 x 5.1k). Bottoms: R130 || R178 and R133 || R180 (2 x 2k). Ratio 1/11.2. R168/R170 4.7k at MCU. CH1 coating and safety rules A-H/A2 remain mandatory.',
    }
    for prefix, new in replacements.items():
        t = replace_note(t, prefix, new)
    return t.replace('(title "12 | Pyro channels, arming and continuity")', '(title "12 | Single pyro CH1, arming and continuity")')


def t_imu_pin(t, lt):
    """Move the polled IMU status input from PE10 to PE1, preserving EXTI1 on PD1."""
    points = symbol_points(t, 'U1', lt)
    read, _, _ = _reader()
    labels = [n for n in read(t).children('global_label') if n.items[1].atom == 'IMU_INT1']
    assert len(labels) == 1, 'expected one IMU status label'
    def endpoint(pin):
        x, y, angle = points[pin]
        return (round(x + (5.08 if int(angle) == 180 else -5.08), 2), y)
    if _xy(labels[0]) == endpoint('98'):
        return t
    assert _xy(labels[0]) == endpoint('40'), 'unexpected IMU status assignment'
    x, y, angle = points['98']
    assert any(_xy(n) == (x, y) for n in read(t).children('no_connect')), 'PE1 must be unused'
    t = disconnect(t, {points['40'][:2], points['98'][:2]})
    bx, by = endpoint('98')
    return insert(t, nc(*points['40'][:2], 'U1:imu-old-pe10') +
                  wire(x, y, bx, by, 'U1:imu-pe1:wire') +
                  glabel('IMU_INT1', bx, by, 'U1:imu-pe1:label',
                         angle=180 if int(angle) == 180 else 0,
                         justify='left' if int(angle) == 180 else 'right') +
                  note('IMU INT1: PE1 polled input only. EXTI1 remains PD1 power status. PE10 NC; pyro sentinels unchanged.',
                       40.64, 248.92, 'U1:imu-pe1:mode'))


def r6_mcu(t, lt):
    t = t_mcu_pins(t)
    t = t_imu_pin(t, lt)
    points = symbol_points(t, 'U1', lt)
    for p in ('4', '16', '32'):
        x, y, _ = points[p]
        t = disconnect(t, {(x, y)})
        t = insert(t, nc(x, y, f'U1:removed-ch2:{p}'))
    points = symbol_points(t, 'J2', lt)
    t = disconnect(t, {xy[:2] for xy in points.values()})
    for p, net in SWD_PINS.items():
        x, y, _ = points[p]
        chunk = nc(x, y, 'J2:nc6') if net is None else (
            wire(x, y, x - 5.08, y, f'J2:r6:w{p}') + glabel(net, x - 5.08, y, f'J2:r6:l{p}'))
        t = insert(t, chunk)
    t = set_props(t, 'J2', UPDATED_PARTS['J2'])
    s, e = symbol_block(t, 'J2')
    t = t[:s] + t[s:e].replace('(in_bom yes)', '(in_bom no)') + t[e:]
    t = replace_note(t, 'J2:', 'J2 TC2030-IDC-NL: 1 VTref/3V3 | 2 SWDIO | 3 NRST | 4 SWCLK | 5 GND | 6 NC. BOOT0 remains at R5; use SWD or firmware jump for ROM boot.')
    t = replace_note(t, 'J2.5 is', 'J2.1 is probe voltage reference only. Tag-Connect ARM20-CTX standard SWD mapping; pin 6 SWO is unused.')
    t = replace_note(t, 'R168-R172 (R4):', 'CH1 sense: R168 4.7k -> PC0 continuity; R170 4.7k -> PC5 ARM; R172 4.7k -> PB0 RAW_ACT. Split divider safety retained. PE5/PC1/PC4 are now NC; PE3/PE6 remain sentinels. Never enable TRACE on PE2-PE6.')
    return t


def buzzer_symbol(lt):
    """MLT-5020 has two coil leads plus one isolated mechanical solder tab."""
    if '\t(symbol "Buzzer_3pad"\n' in lt:
        return lt
    block = _lib_block(lt, 'Buzzer_4pad')
    start = block.rfind('\t\t\t(pin passive line')
    end = close_paren(block, start + 3)
    block = (block[:start] + block[end:]).replace('Buzzer_4pad', 'Buzzer_3pad')
    block = block.replace('3/4 = dummy pads', '3 = isolated mechanical tab')
    k = lt.rindex(')')
    return lt[:k] + block + '\n' + lt[k:]


def r6_buzzer(t, lt):
    if '(lib_id "M3:Buzzer_4pad")' in t:
        x, y, _ = symbol_points(t, 'LS120', lt)['4']
        t = disconnect(t, {(x, y)})
        t = t.replace('(lib_id "M3:Buzzer_4pad")', '(lib_id "M3:Buzzer_3pad")')
    marker = '\t\t(symbol "M3:Buzzer_4pad"\n'
    if marker in t:
        start = t.index(marker)
        end = close_paren(t, start + 2)
        t = t[:start] + _embed(lt, 'Buzzer_3pad').rstrip('\n') + t[end:]
    t = set_props(t, 'LS120', UPDATED_PARTS['LS120'])
    t = replace_note(t, 'LS120 ', 'LS120 MLT-5020: pad 1 = +, pad 2 = -, pad 3 = isolated mechanical tab. Huaneng 2021-05-27 drawing; body 5.0 +/-0.3 mm, height 2.0 +/-0.2 mm.')
    t = replace_note(t, 'BUZZ_DRV =', 'BUZZ_DRV = PA5 (pin 29). MLT-5020: 4 kHz, 50% duty; software toggle or TIM8_CH1N (AF3). Never leave the coil driven with DC.')
    return t


def camera_filter(t):
    for name in ('CameraTerminal', 'M3:CameraTerminal'):
        marker = f'(symbol "{name}"\n'
        if marker in t:
            s = t.index(marker)
            e = close_paren(t, s)
            t = t[:s] + t[s:e].replace('M3_DB128V_4P', 'M3_GH_BM04B_GHS_TBT') + t[e:]
    return t


def stocked_parts(t):
    # Same 0402 package, capacitance, X7R dielectric and tolerance; higher voltage rating.
    read, _, properties = _reader()
    for symbol in read(t).children('symbol'):
        fields = properties(symbol)
        if 'LCSC' in fields and fields['LCSC'].items[2].atom == 'C1525':
            ref = fields['Reference'].items[2].atom
            t = set_props(t, ref, {'Value': '100nF 50V X7R 10%', 'LCSC': 'C307331',
                'LCSC Part': 'C307331', 'Manufacturer': 'Samsung Electro-Mechanics',
                'Manufacturer Part': 'CL05B104KB54PNC'})
    return t


def main():
    global D
    D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / 'assembly_review'
    lib = D / 'kilib' / 'm3.kicad_sym'
    lt = camera_filter(buzzer_symbol(t_conn_1x7(lib.read_text()))).replace('"HDR-TH_6P-P2.54-V-M-1x6"', '"M3_TC2030_IDC_NL"')
    if lt != lib.read_text():
        lib.write_text(lt)
    t_telemetry_sheet()
    edits = {
        'pullpin_buzzer.kicad_sch': lambda t: r6_buzzer(t, lt),
        'pyro.kicad_sch': lambda t: r6_pyro(t, lt),
        'mcu.kicad_sch': lambda t: r6_mcu(t, lt),
        'camera_connector.kicad_sch': lambda t: set_props(t, 'J9', UPDATED_PARTS['J9']),
        'battery_entry.kicad_sch': lambda t: set_props(set_props(t, 'R84', UPDATED_PARTS['R84']), 'R165', UPDATED_PARTS['R165']),
        'm3.kicad_sch': t_root_sheet,
    }
    for f in sorted(D.glob('*.kicad_sch')):
        original = f.read_text()
        text = remove_channel2(original, lt)
        text = stocked_parts(camera_filter(edits.get(f.name, lambda t: t)(text)))
        text = text.replace('"HDR-TH_6P-P2.54-V-M-1x6"', '"M3_TC2030_IDC_NL"')
        text = re.sub(r'\(rev "M3-ASSY-R[345]"\)', '(rev "M3-ASSY-R6")', text)
        # Removing a block otherwise leaves whitespace growing on repeated runs.
        text = re.sub(r'\n(?:\s*\n)+', '\n', text)
        if text != original:
            f.write_text(text)
            print('edited', f.name)
    print(f'R6 schematic: {len(TLM_PARTS)} telemetry parts, {len(REMOVE_REFS)} CH2 parts removed')


if __name__ == '__main__':
    main()
