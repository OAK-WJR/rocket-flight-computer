#!/usr/bin/env python3
"""Reproducible R6 -> R7 schematic transform: on-board GNSS and telemetry radio (REQUIREMENTS F10).

usage: python3 m3_design/r7_sch.py [project_dir] [--netlist]
Run after m3_design/r7_parts.py (it adds the symbols and footprints this script uses). The input is the
committed R6 project (3b215ba); a second run changes nothing. --netlist also regenerates
schematic.net.xml with kicad-cli (local path made relative and the date blanked, as r4_build.sh does).

Design basis: m3_design/assembly_review/sources/r7_review/pass1_electrical.md (section 5.2 pin map,
6.1 GNSS and 6.2 radio netlists and parts, 6.3 removals) with the step-A adjudication: ESD103-B1-02EL
on both antenna ports, R300 = 15 ohm, a DNP pi network on the radio line too, no L31, Kinghelm
KH-SMA-KE8-G jacks, 3xx designators. docs/M3_R7.md records the result.

1. Sheet 15 (telemetry.kicad_sch, same sheet UUID) is regenerated from RF_PARTS: R6's port parts J130,
   J131, U14, U15, U16, L4, TP130, D130, D131, C170-C180 and R190-R206 and their TLM_*/RADIO_*/GPS_*
   nets disappear with the old file (every one of the 37 parts on it; 3V3, GND and RAW_PROTECTED keep
   all their other connections). Every pin reaches a global label through a short wire (the R6 sheet
   style); unused module pins carry a no-connect flag. 3V3_GNSS and 3V3_RADIO (fed through ferrites)
   get local PWR_FLAGs.
2. Root sheet: the sheet-15 name changes; #FLG07 and its TLM_5V_REG label go.
3. MCU sheet: U1 re-pinned (RF_MCU_PINS). PA7, PC9, PA8, PA9 and PA10 lose their old nets and become
   no-connect; the pyro sentinels PE3, PE5, PE6, PC1, PC4 stay without a net (asserted).
4. Every sheet: rev M3-ASSY-R7; the embedded copy of M3:L follows the library (r7_parts.py added
   M3_LQG15_0402 to its footprint filter).
RF_PARTS / RF_MCU_PINS are the board builder's input (step B); DNP parts carry dnp, in_bom no and
in_pos_files no, which the KiCad netlist passes on as dnp / exclude_from_bom / exclude_from_pos_files.
"""
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = '6007a7db-6a58-5660-8beb-956dea045ff8'
NS = uuid.UUID('9a3e2c71-4f0b-5d18-b6a2-7c0e5d8f1a37')    # fixed namespace -> stable R7 UUIDs
GRID = 2.54
TLM_SHEET = 'telemetry.kicad_sch'
TLM_SHEET_UUID = '05a85211-bc24-59d4-a8a4-ff7347ee84fc'   # R6's sheet-15 UUID, kept
OLD_TITLE = '15 | Telemetry radio and GPS port'
TITLE = '15 | GNSS and telemetry radio (R7)'
REV = 'M3-ASSY-R7'
D = None


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
    s = text.rfind('\n\t(symbol\n', 0, i) + 2
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


def nc(x, y, key):
    return f'\t(no_connect\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(uuid {uid(key)}))\n'


def insert(text, chunk):
    i = text.rfind('\t(sheet_instances')
    return text[:i] + chunk + text[i:]


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


def _lib_block(lt, name):
    i = lt.index(f'\t(symbol "{name}"\n')
    return lt[i:close_paren(lt, i + 1)]


def _lib_pins(lt, name):
    """{pin number: (x, y, angle)} of a library symbol (y up, as stored)."""
    out = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)[\s\S]*?\(number "([^"]+)"',
                         _lib_block(lt, name)):
        out[m.group(4)] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
    return out


def _embed(lt, name):
    blk = _lib_block(lt, name).replace(f'(symbol "{name}"', f'(symbol "M3:{name}"', 1)
    return ''.join('\t' + line for line in blk.splitlines(True)) + '\n'


# ---------------------------------------------------------------------------------------------------------
# sheet 15 content

DS = {   # maker documents (URLs only); the LCSC copies are the ones checked on 2026-10-15
    'maxf10s': 'https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf',
    'e22': 'https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2212192008_Chengdu-Ebyte-Elec-Tech-E22-900MM22S_C5333985.pdf',
    'sma': 'https://datasheet.lcsc.com/datasheet/pdf/35ad22a9bea57e53d493009a20c931ef.pdf?productCode=C530661',
    'esd': 'https://datasheet.lcsc.com/datasheet/pdf/9f837311bec7e3ead15a9d62fb0575b0.pdf?productCode=C535146',
    'ao3401a': 'https://www.aosmd.com/res/datasheets/AO3401A.pdf',
    'ao3400a': 'https://www.aosmd.com/res/datasheets/AO3400A.pdf',
    's8550': 'https://datasheet.lcsc.com/datasheet/pdf/e048f602aee74d95b954be40ef1dcefb.pdf?productCode=C105432',
    'blm18': 'https://datasheet.lcsc.com/datasheet/pdf/2d503a4b167da9bb5d0eb4a3fa711314.pdf?productCode=C88980',
    'lqg15': 'https://datasheet.lcsc.com/datasheet/pdf/4fdc9bb2296ffef8346418b98de47ce9.pdf?productCode=C97998',
}
PARTS = {   # LCSC -> (Manufacturer, Manufacturer Part, Datasheet) exactly as JLC lists them (2026-10-15)
    'C30005563': ('U-BLOX', 'MAX-F10S-00B', DS['maxf10s']),
    'C5333985': ('Chengdu Ebyte Elec Tech', 'E22-900MM22S', DS['e22']),
    'C530661': ('Shenzhen Kinghelm Elec', 'KH-SMA-KE8-G', DS['sma']),
    'C535146': ('Infineon Technologies', 'ESD103-B1-02EL E6327', DS['esd']),
    'C15127': ('Alpha & Omega Semicon', 'AO3401A', DS['ao3401a']),
    'C20917': ('Alpha & Omega Semicon', 'AO3400A', DS['ao3400a']),
    'C105432': ('Jiangsu Changjing Electronics Technology Co., Ltd.', 'S8550(RANGE:120-200)', DS['s8550']),
    'C88980': ('Murata Electronics', 'BLM18KG221SN1D', DS['blm18']),
    'C97998': ('Murata Electronics', 'LQG15HS47NJ02D', DS['lqg15']),
    'C19702': ('Samsung Electro-Mechanics', 'CL10A106KP8NNNC', 'https://datasheet.lcsc.com/datasheet/pdf/02336ea48ea44ca18c72517dd3cb7b47.pdf?productCode=C19702'),
    'C307331': ('Samsung Electro-Mechanics', 'CL05B104KB54PNC', ''),
    'C15195': ('Samsung Electro-Mechanics', 'CL05B103KB5NNNC', 'https://datasheet.lcsc.com/datasheet/pdf/02336ea48ea44ca18c72517dd3cb7b47.pdf?productCode=C15195'),
    'C45783': ('Samsung Electro-Mechanics', 'CL21A226MAQNNNE', ''),
    'C22810': ('UNI-ROYAL(Uniroyal Elec)', '0603WAF150JT5E', 'https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C22810'),
    'C25741': ('UNI-ROYAL(Uniroyal Elec)', '0402WGF1003TCE', ''),
    'C25744': ('UNI-ROYAL(Uniroyal Elec)', '0402WGF1002TCE', ''),
    'C11702': ('UNI-ROYAL(Uniroyal Elec)', '0402WGF1001TCE', ''),
    'C4109': ('UNI-ROYAL(Uniroyal Elec)', '0402WGF2001TCE', ''),
    'C25091': ('UNI-ROYAL(Uniroyal Elec)', '0402WGF2200TCE', 'https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25091'),
    'C25105': ('UNI-ROYAL(Uniroyal Elec)', '0402WGF330JTCE', 'https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25105'),
    'C17168': ('UNI-ROYAL(Uniroyal Elec)', '0402WGF0000TCE', 'https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C17168'),
}
SMA_ASSEMBLY = 'THT (JLC through-hole step, hand-soldered after reflow; no paste; body overhangs the aft edge)'


def part(lib, value, fp, code, nets, kind='fit'):
    """kind: fit | dnp (placeholder: dnp, in_bom no, in_pos_files no, no part number) | tp (bare test pad)."""
    if kind == 'fit':
        maker, mpn, ds = PARTS[code]
        fields = {'Datasheet': ds, 'LCSC': code, 'Manufacturer': maker, 'Manufacturer Part': mpn}
        if fp == 'rocket:M3_SMA_KH_KE8_EDGE':
            fields['JLC_Assembly'] = SMA_ASSEMBLY
    else:
        fields = {'Datasheet': '', 'LCSC': ''}
    return (lib, value, fp, fields, nets, kind)


R0402, C0402 = 'rocket:R0402', 'rocket:C0402'
C0402_DNP = 'rocket:C0402_DNP'      # C0402 land without paste: unfitted placeholders print no solder (pass 2 RF-01)
SOT23 = 'rocket:SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR'
SMA_GND = {'1': 'GND', '2': 'GND', '3': 'GND', '4': 'GND'}
RF_PARTS = {
    # GNSS (pass1_electrical 6.1)
    'U30': part('M3:MAX_F10S', 'MAX-F10S-00B', 'rocket:M3_MAX_F10S_LCC18', 'C30005563', {
        '1': 'GND', '2': 'GNSS_TXD', '3': 'GNSS_RXD', '4': 'GNSS_TIMEPULSE', '5': None, '6': None,
        '7': '3V3_GNSS', '8': '3V3_GNSS', '9': 'GNSS_RESET_N', '10': 'GND', '11': 'GNSS_RF_IN', '12': 'GND',
        '13': 'GNSS_LNA_EN', '14': 'GNSS_VCC_RF', '15': None, '16': None, '17': None, '18': 'GNSS_SAFEBOOT_N'}),
    'FB30': part('M3:FerriteBead', 'BLM18KG221SN1D', 'rocket:M3_BLM18K_0603', 'C88980', {'1': '3V3', '2': '3V3_GNSS'}),
    'C300': part('M3:C', '10uF 10V X5R 10%', 'rocket:C0603', 'C19702', {'1': '3V3_GNSS', '2': 'GND'}),
    'C301': part('M3:C', '100nF 50V X7R 10%', C0402, 'C307331', {'1': '3V3_GNSS', '2': 'GND'}),
    'R300': part('M3:R', '15R 1%', 'rocket:R_0603_1608Metric', 'C22810', {'1': 'GNSS_VCC_RF', '2': 'GNSS_ANT_SRC'}),
    'Q32': part('M3:PNP_SOT23', 'S8550', SOT23, 'C105432', {'1': 'GNSS_ANT_SRC', '2': 'GNSS_VCC_RF', '3': 'GNSS_ANT_GATE'}),
    'Q30': part('M3:PMOS_SOT23', 'AO3401A', SOT23, 'C15127', {'1': 'GNSS_ANT_GATE', '2': 'GNSS_ANT_SRC', '3': 'GNSS_ANT_DC'}),
    'R301': part('M3:R', '100k', R0402, 'C25741', {'1': 'GNSS_ANT_SRC', '2': 'GNSS_ANT_GATE'}),
    'R302': part('M3:R', '10k', R0402, 'C25744', {'1': 'GNSS_ANT_GATE', '2': 'GNSS_ANT_PD'}),
    # limiter loop compensation placeholder (pass 2 ELECTRICAL-01): fit 1-2.2 nF only if the bench short test shows
    # oscillation at GNSS_ANT_GATE / VCC_RF
    'C304': part('M3:C', 'DNP', C0402_DNP, '', {'1': 'GNSS_ANT_GATE', '2': 'GND'}, 'dnp'),
    'Q31': part('M3:NMOS_SOT23', 'AO3400A', SOT23, 'C20917', {'1': 'GNSS_LNA_EN', '2': 'GND', '3': 'GNSS_ANT_PD'}),
    'R303': part('M3:R', '100k', R0402, 'C25741', {'1': 'GNSS_LNA_EN', '2': 'GND'}),
    'C302': part('M3:C', '10nF 50V X7R 10%', C0402, 'C15195', {'1': 'GNSS_ANT_DC', '2': 'GND'}),
    'L30': part('M3:L', '47nH 5% 300mA', 'rocket:M3_LQG15_0402', 'C97998', {'1': 'GNSS_ANT_DC', '2': 'GNSS_RF_ANT'}),
    'J30': part('M3:SMA_Edge', 'GNSS ANT SMA', 'rocket:M3_SMA_KH_KE8_EDGE', 'C530661', {'5': 'GNSS_RF_ANT', **SMA_GND}),
    'D30': part('M3:ESD_Bidir', 'ESD103-B1-02EL', 'rocket:M3_TSLP_2_20', 'C535146', {'1': 'GNSS_RF_ANT', '2': 'GND'}),
    'C303': part('M3:C', 'DNP', C0402_DNP, '', {'1': 'GNSS_RF_ANT', '2': 'GND'}, 'dnp'),
    'R304': part('M3:R', '0R', R0402, 'C17168', {'1': 'GNSS_RF_ANT', '2': 'GNSS_RF_IN'}),
    'C305': part('M3:C', 'DNP', C0402_DNP, '', {'1': 'GNSS_RF_IN', '2': 'GND'}, 'dnp'),
    'R305': part('M3:R', '220R', R0402, 'C25091', {'1': 'GNSS_TXD', '2': 'GNSS_TXD_MCU'}),
    'R306': part('M3:R', '220R', R0402, 'C25091', {'1': 'GNSS_RXD_MCU', '2': 'GNSS_RXD'}),
    'R307': part('M3:R', '1k', R0402, 'C11702', {'1': 'GNSS_TIMEPULSE', '2': 'GNSS_TP_MCU'}),
    'TP30': part('M3:TestPoint', 'GNSS_SAFEBOOT_N', 'rocket:M3_TestPad_1.5', '', {'1': 'GNSS_SAFEBOOT_N'}, 'tp'),
    # radio (pass1_electrical 6.2; pi network added in step A, no L31)
    'U31': part('M3:E22_900MM22S', 'E22-900MM22S', 'rocket:M3_E22_900MM22S', 'C5333985', {
        '1': '3V3_RADIO', '2': 'GND', '3': 'RADIO_NRST', '4': None, '5': None, '6': 'RADIO_RF', '7': 'GND',
        '8': None, '9': 'RADIO_TXEN', '10': 'RADIO_RXEN', '11': 'RADIO_BUSY', '12': 'RADIO_MISO',
        '13': 'RADIO_MOSI', '14': 'RADIO_NSS', '15': 'RADIO_SCK', '16': 'GND', '17': None, '18': None,
        '19': 'RADIO_TXEN', '20': 'RADIO_DIO1'}),
    'FB31': part('M3:FerriteBead', 'BLM18KG221SN1D', 'rocket:M3_BLM18K_0603', 'C88980', {'1': '3V3', '2': '3V3_RADIO'}),
    'C310': part('M3:C', '22uF', 'rocket:C0805', 'C45783', {'1': '3V3_RADIO', '2': 'GND'}),
    'C311': part('M3:C', '100nF 50V X7R 10%', C0402, 'C307331', {'1': '3V3_RADIO', '2': 'GND'}),
    'C312': part('M3:C', '10nF 50V X7R 10%', C0402, 'C15195', {'1': '3V3_RADIO', '2': 'GND'}),
    'R310': part('M3:R', '100k', R0402, 'C25741', {'1': '3V3_RADIO', '2': 'RADIO_NSS'}),
    'R311': part('M3:R', '2k', R0402, 'C4109', {'1': 'RADIO_NRST', '2': 'GND'}),
    'R312': part('M3:R', '100k', R0402, 'C25741', {'1': 'RADIO_RXEN', '2': 'GND'}),
    'R313': part('M3:R', '33R', R0402, 'C25105', {'1': 'RADIO_SCK_MCU', '2': 'RADIO_SCK'}),
    'R314': part('M3:R', '33R', R0402, 'C25105', {'1': 'RADIO_MISO', '2': 'RADIO_MISO_MCU'}),
    'R315': part('M3:R', '33R', R0402, 'C25105', {'1': 'RADIO_MOSI_MCU', '2': 'RADIO_MOSI'}),
    'J31': part('M3:SMA_Edge', 'RADIO ANT SMA', 'rocket:M3_SMA_KH_KE8_EDGE', 'C530661', {'5': 'RADIO_RF_ANT', **SMA_GND}),
    'D31': part('M3:ESD_Bidir', 'ESD103-B1-02EL', 'rocket:M3_TSLP_2_20', 'C535146', {'1': 'RADIO_RF_ANT', '2': 'GND'}),
    'C313': part('M3:C', 'DNP', C0402_DNP, '', {'1': 'RADIO_RF_ANT', '2': 'GND'}, 'dnp'),
    'R316': part('M3:R', '0R', R0402, 'C17168', {'1': 'RADIO_RF_ANT', '2': 'RADIO_RF'}),
    'C314': part('M3:C', 'DNP', C0402_DNP, '', {'1': 'RADIO_RF', '2': 'GND'}, 'dnp'),
}
FLAGS = {'#FLG08': '3V3_GNSS', '#FLG09': '3V3_RADIO'}     # supplies behind ferrites (passive drivers only)

RF_MCU_PINS = {'45': 'RADIO_RXEN', '51': 'RADIO_NSS', '52': 'RADIO_SCK_MCU', '53': 'RADIO_MISO_MCU',
               '54': 'RADIO_MOSI_MCU', '55': 'RADIO_BUSY', '56': 'RADIO_NRST', '57': 'RADIO_DIO1',
               '61': 'GNSS_TP_MCU', '63': 'GNSS_RXD_MCU', '64': 'GNSS_TXD_MCU', '65': 'GNSS_RESET_N'}
FREED_NC = ('31', '66', '67', '68', '69')                  # PA7, PC9, PA8, PA9, PA10
R6_PIN_STATE = {'31': 'TLM_FAULT_N', '51': 'TLM_PWR_EN', '63': 'RADIO_TX_MCU', '64': 'RADIO_RX_MCU',
                '65': 'RADIO_M0_MCU', '66': 'RADIO_M1_MCU', '67': 'RADIO_AUX_MCU', '68': 'GPS_TX_MCU',
                '69': 'GPS_RX_MCU', '45': None, '52': None, '53': None, '54': None, '55': None, '56': None,
                '57': None, '61': None}                     # None = R6 no-connect flag
PYRO_SENTINELS = ('2', '4', '5', '16', '32')               # PE3, PE5, PE6, PC1, PC4 (check_actuators.py)

RF_LAYOUT = {
    'FB30': (45.72, 88.9), 'C300': (76.2, 88.9), 'C301': (106.68, 88.9), '#FLG08': (142.24, 83.82),
    'R300': (167.64, 88.9), 'R301': (198.12, 88.9), 'R302': (228.6, 88.9), 'R303': (259.08, 88.9),
    'C302': (289.56, 88.9), 'L30': (320.04, 88.9), 'C304': (350.52, 88.9),
    'U30': (76.2, 139.7), 'Q32': (167.64, 139.7), 'Q30': (213.36, 139.7), 'Q31': (259.08, 139.7),
    'J30': (45.72, 190.5), 'D30': (96.52, 190.5), 'C303': (127.0, 190.5), 'R304': (157.48, 190.5),
    'C305': (187.96, 190.5), 'R305': (218.44, 190.5), 'R306': (248.92, 190.5), 'R307': (279.4, 190.5),
    'TP30': (309.88, 186.69),
    'U31': (76.2, 266.7), 'FB31': (137.16, 254.0), 'C310': (167.64, 254.0), 'C311': (198.12, 254.0),
    'C312': (228.6, 254.0), '#FLG09': (266.7, 248.92), 'R310': (289.56, 254.0), 'R311': (320.04, 254.0),
    'R312': (350.52, 254.0),
    'R313': (137.16, 304.8), 'R314': (167.64, 304.8), 'R315': (198.12, 304.8), 'J31': (243.84, 304.8),
    'D31': (281.94, 304.8), 'C313': (312.42, 304.8), 'R316': (342.9, 304.8), 'C314': (373.38, 304.8),
}
NOTES = [
    '15 | GNSS and telemetry radio (R7): u-blox MAX-F10S U30 and EBYTE E22-900MM22S U31 on main 3V3 through FB30/FB31; aft RF strip, one edge SMA each (REQUIREMENTS F10).',
    'GNSS on USART6: PC6 TX -> R306 220R -> RXD; TXD -> R305 220R -> PC7 RX. PC8 drives RESET_N open-drain (no pull, no capacitor). TIMEPULSE -> R307 1k -> PD14, never pulled down (SAFEBOOT_N shares it).',
    'Radio on SPI2: PB12 NSS (R310 100k to 3V3_RADIO), PB13 SCK / PB15 MOSI / PB14 MISO through R313 / R315 / R314 33R. PD8 BUSY, PD9 NRST (R311 2.0k to GND), PD10 DIO1 (EXTI10), PE15 RXEN (R312 100k to GND), TXEN = DIO2.',
    'MCU in reset or ROM bootloader: R311 holds the radio in reset (it cannot transmit), NSS high, RXEN low, TXEN low (DIO2 pulled down in reset); the GNSS keeps tracking. PA7, PC9, PA8, PA9, PA10 NC; pyro sentinels unchanged.',
    'Radio commands can never arm or fire: no GNSS or radio net reaches pyro, ARM or actuator copper, and arming is the physical J124 link.',
    'Antenna bias: VCC_RF -> R300 15R sense -> Q30 (on while LNA_EN drives Q31). Q32 limits a shorted antenna or coax to about 37-48 mA at -20 C and 25-38 mA at +85 C (Inference, bench check); about 2.93 V at the antenna at 15 mA. C304 (DNP, gate to GND): fit 1-2.2 nF if the short test shows oscillation.',
    'RF chains: J30 -> D30 ESD103 -> L30 47nH bias tap -> C303 DNP / R304 0R / C305 DNP -> RF_IN; J31 -> D31 ESD103 -> C313 DNP / R316 0R / C314 DNP -> ANT. DNP shunts are tuning placeholders: C303 and C305 capacitive only while R304 is 0R; C313/C314 C or L. C304 capacitor only, 1.0-2.2 nF.',
    'E22: passive 32 MHz crystal, never enable DIO3 TCXO control; never transmit without an antenna or 50R load. The MAX-M10S fits U30 unchanged (fit L30 = 27nH for L1-only).',
]


# Reference / Value offsets clear of pin names and labels (default: right of a two-pin part)
TEXT_AT = {'MAX_F10S': ((-12.7, -16.51), (-12.7, 16.51)), 'E22_900MM22S': ((-12.7, -17.78), (-12.7, 17.78)),
           'SMA_Edge': ((-2.54, -7.62), (-2.54, 7.62)), 'ESD_Bidir': ((-2.54, -3.81), (-2.54, 3.81)),
           'PMOS_SOT23': ((6.35, -1.27), (6.35, 1.27)), 'PNP_SOT23': ((6.35, -1.27), (6.35, 1.27)),
           'NMOS_SOT23': ((6.35, -1.27), (6.35, 1.27))}


def _sym(lt, ref, x, y, path):
    """One sheet-15 symbol at (x, y): every pin reaches a global label through a 5.08 mm wire;
    pins mapped to None get a no-connect flag at the pin end."""
    if ref in FLAGS:
        lib_id, value, fp, fields, nets, kind = 'M3:PWR_FLAG', 'PWR_FLAG', '', {'LCSC': ''}, {'1': FLAGS[ref]}, 'flag'
    else:
        lib_id, value, fp, fields, nets, kind = RF_PARTS[ref]
    name = lib_id.split(':')[1]
    flags = {'fit': ('yes', 'yes', None, 'no'), 'dnp': ('no', 'yes', 'no', 'yes'),
             'tp': ('no', 'yes', 'no', 'no'), 'flag': ('no', 'no', None, 'no')}[kind]
    body = (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {fmt(x)} {fmt(y)} 0)\n\t\t(unit 1)\n'
            f'\t\t(in_bom {flags[0]})\n\t\t(on_board {flags[1]})\n')
    if flags[2]:
        body += f'\t\t(in_pos_files {flags[2]})\n'
    body += f'\t\t(dnp {flags[3]})\n\t\t(uuid {uid(ref)})\n'
    hidden = kind == 'flag'
    (rx, ry), (vx, vy) = TEXT_AT.get(name, ((GRID, -1.27), (GRID, 1.27)))
    body += prop('Reference', ref, x + rx, y + ry, hide=hidden)
    body += prop('Value', value, x + vx, y + vy, hide=hidden)
    body += prop('Footprint', fp, x, y)
    body += prop('Datasheet', fields.get('Datasheet', ''), x, y)
    for k, v in fields.items():
        if k != 'Datasheet':
            body += prop(k, v, x, y)
    body += (f'\t\t(instances\n\t\t\t(project "m3"\n\t\t\t\t(path "{path}"\n'
             f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)))))\n')
    pins = _lib_pins(lt, name)
    if set(pins) != set(nets):
        raise SystemExit(f'{ref}: pins {sorted(pins)} differ from the net map {sorted(nets)}')
    for num, (px, py, ang) in sorted(pins.items(), key=lambda kv: (len(kv[0]), kv[0])):
        ax, ay = round(x + px, 2), round(y - py, 2)
        if nets[num] is None:
            body += nc(ax, ay, f'{ref}:nc{num}')
            continue
        dx, dy = {0: (-5.08, 0), 180: (5.08, 0), 90: (0, 5.08), 270: (0, -5.08)}[int(ang) % 360]
        bx, by = round(ax + dx, 2), round(ay + dy, 2)
        body += wire(ax, ay, bx, by, f'{ref}:w{num}')
        body += glabel(nets[num], bx, by, f'{ref}:l{num}', angle=0 if dx <= 0 else 180,
                       justify='right' if dx <= 0 else 'left')
    return body


def t_rf_sheet(lt):
    """Section 1: sheet 15 regenerated from RF_PARTS (the board builder reads the same table)."""
    path = f'/{ROOT}/{TLM_SHEET_UUID}'
    libs = sorted({v[0].split(':')[1] for v in RF_PARTS.values()} | {'PWR_FLAG'})
    out = (f'(kicad_sch\n\t(version 20250114)\n\t(generator "m3_r7_rf")\n\t(uuid {TLM_SHEET_UUID})\n\t(paper "A2")\n'
           f'\t(title_block\n\t\t(title "{TITLE}")\n\t\t(date "2026-10-15")\n\t\t(rev "{REV}")\n'
           f'\t\t(company "Single-board M3 candidate; on-board GNSS and radio, not bench-verified"))\n\t(lib_symbols\n')
    out += ''.join(_embed(lt, n) for n in libs) + '\t)\n'
    for k, line in enumerate(NOTES):
        out += note(line, 20.32, 15.24 + 5.08 * k, f'rf:note{k}')
    for ref in list(RF_PARTS) + list(FLAGS):
        out += _sym(lt, ref, *RF_LAYOUT[ref], path)
    out += '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "15"))))\n'
    return out


# ---------------------------------------------------------------------------------------------------------
# root and MCU sheets


def t_root(t):
    """Section 2: sheet-15 block renamed; #FLG07 (PWR_FLAG on the removed TLM_5V_REG) and its label removed."""
    assert f'(uuid {TLM_SHEET_UUID})' in t and f'(property "Sheetfile" "{TLM_SHEET}"' in t
    t = t.replace(f'(property "Sheetname" "{OLD_TITLE}"', f'(property "Sheetname" "{TITLE}"')
    assert f'(property "Sheetname" "{TITLE}"' in t
    blk = symbol_block(t, '#FLG07')
    if blk:
        s, e = blk
        m = re.search(r'\(at ([\d.]+) ([\d.]+) 0\)', t[s:e])
        point = (round(float(m.group(1)), 2), round(float(m.group(2)), 2))
        t = t[:s] + t[e:]
        t = disconnect(t, {point})
    assert 'TLM_5V_REG' not in t and '#FLG07' not in t
    return t


def _mcu_points(t, lt):
    pins = _lib_pins(lt, 'MCU')
    m = re.search(r'\(lib_id "M3:MCU"\)\n\t\t\(at ([\d.]+) ([\d.]+) 0\)', t)
    X, Y = float(m.group(1)), float(m.group(2))
    assert (X, Y) == (91.44, 132.08), (X, Y)
    return {n: (round(X + px, 2), round(Y - py, 2), int(a)) for n, (px, py, a) in pins.items()}


def t_mcu(t, lt):
    """Section 3: U1 re-pinned for the GNSS (USART6, PC8, PD14) and the radio (SPI2, PD8-PD10, PE15)."""
    read, _, _ = _reader()
    pts = _mcu_points(t, lt)

    def state(num):
        x, y, a = pts[num]
        root = read(t)
        if any(_xy(n) == (x, y) for n in root.children('no_connect')):
            return 'NC'
        end = (round(x + (5.08 if a == 180 else -5.08), 2), y)
        labels = [n.items[1].atom for n in root.children('global_label') if _xy(n) == end]
        return labels[0] if len(labels) == 1 else None

    def connect(num, net):
        nonlocal t
        x, y, a = pts[num]
        bx = round(x + (5.08 if a == 180 else -5.08), 2)
        t = insert(t, wire(x, y, bx, y, f'U1:r7:w{num}') +
                   glabel(net, bx, y, f'U1:r7:l{num}', angle=180 if a == 180 else 0,
                          justify='left' if a == 180 else 'right'))

    for num, net in RF_MCU_PINS.items():
        now = state(num)
        if now == net:
            continue
        r6 = R6_PIN_STATE[num]
        assert now == (r6 or 'NC'), f'U1.{num}: unexpected state {now!r} (R6: {r6 or "NC"})'
        t = disconnect(t, {pts[num][:2]})
        connect(num, net)
    for num in FREED_NC:
        now = state(num)
        if now == 'NC':
            continue
        assert now == R6_PIN_STATE[num], f'U1.{num}: unexpected state {now!r}'
        t = disconnect(t, {pts[num][:2]})
        t = insert(t, nc(*pts[num][:2], f'U1:r7:nc{num}'))
    for num in PYRO_SENTINELS:
        assert state(num) == 'NC', f'pyro sentinel U1.{num} must stay without a net'
    line = ('R7 (sheet 15): radio SPI2 PB12 NSS, PB13 SCK, PB14 MISO, PB15 MOSI; PD8 BUSY, PD9 NRST, PD10 DIO1, '
            'PE15 RXEN. GNSS USART6 PC6/PC7, PC8 RESET_N (open drain), PD14 TIMEPULSE. PA7, PC9, PA8, PA9, PA10 NC.')
    if f'(text "{line}"' not in t:
        t = insert(t, note(line, 20.32, 259.08, 'U1:r7:note'))
    return t


def refresh_embedded(t, lt, name):
    """Replace the sheet's embedded copy of M3:<name> with the library's (ERC lib_symbol_mismatch)."""
    marker = f'\t\t(symbol "M3:{name}"\n'
    if marker not in t:
        return t
    s = t.index(marker)
    e = close_paren(t, s + 2)
    return t[:s] + _embed(lt, name).rstrip('\n') + t[e:]


def export_netlist(project):
    cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
    out = project / 'schematic.net.xml'
    subprocess.run([cli, 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(out),
                    str(project / 'm3.kicad_sch')], check=True, capture_output=True, text=True)
    text = out.read_text().replace(str(project.resolve()) + '/', '').replace(str(project) + '/', '')
    out.write_text(re.sub(r'<date>[^<]*</date>', '<date></date>', text))
    print('wrote', out.name)


def main():
    global D
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    D = Path(args[0]) if args else Path(__file__).resolve().parent / 'assembly_review'
    lt = (D / 'kilib' / 'm3.kicad_sym').read_text()
    for name in ('MAX_F10S', 'E22_900MM22S', 'SMA_Edge', 'ESD_Bidir', 'PMOS_SOT23', 'PNP_SOT23', 'FerriteBead'):
        if f'\t(symbol "{name}"\n' not in lt:
            raise SystemExit(f'M3:{name} missing: run m3_design/r7_parts.py first')
    rf = t_rf_sheet(lt)
    edits = {'m3.kicad_sch': t_root, 'mcu.kicad_sch': lambda t: t_mcu(t, lt), TLM_SHEET: lambda _t: rf}
    for f in sorted(D.glob('*.kicad_sch')):
        original = f.read_text()
        text = edits.get(f.name, lambda t: t)(original)
        text = refresh_embedded(text, lt, 'L')
        text = refresh_embedded(text, lt, 'C')
        text = re.sub(r'\(rev "M3-ASSY-R[3456]"\)', f'(rev "{REV}")', text)
        text = re.sub(r'\n(?:\s*\n)+', '\n', text)     # removed blocks otherwise leave blank lines
        if text != original:
            f.write_text(text)
            print('edited', f.name)
    if '--netlist' in sys.argv:
        export_netlist(D)
    fitted = sum(1 for v in RF_PARTS.values() if v[5] == 'fit')
    print(f'R7 schematic: {len(RF_PARTS)} sheet-15 parts ({fitted} fitted, '
          f'{sum(v[5] == "dnp" for v in RF_PARTS.values())} DNP, 1 test pad), {len(RF_MCU_PINS)} U1 pins assigned, '
          f'{len(FREED_NC)} freed to NC')


if __name__ == '__main__':
    main()
