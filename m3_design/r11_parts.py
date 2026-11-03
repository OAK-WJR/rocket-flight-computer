#!/usr/bin/env python3
"""Generate and check the M3-ASSY-R11 project library (m3_design/r11/kilib); never edits a board or a schematic.

usage: KiCad python3 -I -B m3_design/r11_parts.py --library-only   write kilib/ (symbols, footprints, 3D models)
       KiCad python3 -I -B m3_design/r11_parts.py --check          fail if kilib/ is stale; parse every land with pcbnew
       python3 -I -B m3_design/r11_parts.py --stock                query JLCPCB for every catalog code (network) and
                                                                    write m3_design/r11/design/jlc_r11_stock.json
The library is R10's (hash-pinned in r10_input/manifest.json: symbols copied from r10_input/m3.kicad_sym, footprints
and models from R10's kilib, only those R11 uses) plus the R11 parts (D-R11-04 / -05):
  M3_TFBGA100_8x8_P0.8     STM32H743VIH6, ST DS12110 Rev 8 Table 218 p. 324 and Table 219 p. 325
  M3_GH_SM0nB_GHS_TB       JST GH side-entry SMT header, JST eGH.pdf p. 2 "PC board layout" (side entry)
  M3_WIREPAD_2P_AWG20      two plated through-holes for AWG 20 stranded wire (J1 battery, J121 pyro); no paste, no BOM
Symbols: MCU_TFBGA100 (R10's MCU symbol, pins re-numbered to balls), CameraGH6 (J9), and GH texts on PortTerminal /
ServoTerminal (same pins and geometry). Sources and rating checks: m3_design/r11/design/parts_r11.md.
"""
import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r7_parts
from r7_parts import _box, _circle, _line, _rect, g, module_symbol
import r11_sch as r11

LIB = r11.PROJECT / 'kilib'
PRETTY = LIB / 'rocket.pretty'
SHAPES = LIB / 'rocket.3dshapes'
SYMLIB = LIB / 'm3.kicad_sym'
STOCK = r11.DESIGN / 'jlc_r11_stock.json'
GEN = 'm3_r11_parts'
BOARDS = 5

# ---------------------------------------------------------------------------------------------------------------------
# footprints


def make_fp(name, descr, body, ref_y, model, attr='smd'):
    text = r7_parts.footprint(name, descr, body, ref_y, -ref_y, model or 'none').replace('m3_r7_parts', GEN)
    if model is None:
        text = text[:text.index('\t(model ')] + ')\n'
    return text.replace('(attr smd)', f'(attr {attr})')


def _round_pad(num, x, y, w, h, layers, extra=''):
    lay = ' '.join(f'"{l}"' for l in layers)
    return (f'\t(pad "{num}" smd roundrect\n\t\t(at {g(x)} {g(y)})\n\t\t(size {g(w)} {g(h)})\n\t\t(layers {lay})\n'
            f'\t\t(roundrect_rratio 0.25){extra})\n')


# ST DS12110 Rev 8 Table 218 p. 324: D = E = 8.000 (7.850-8.150), A max 1.100, ball b 0.350-0.450, e 0.800, D1 = E1
# 7.200. Table 219 p. 325 (0.8 mm pitch BGA): Dpad 0.400 mm, Dsm 0.470 mm typical, stencil opening 0.400 mm, stencil
# 0.100-0.125 mm, pad trace width 0.120 mm. Ball A1 top left (Figure 6 p. 56, top view); rows A-K without I.
BGA_ROWS = 'ABCDEFGHJK'
BGA_PITCH, BGA_PAD, BGA_SM = 0.8, 0.4, 0.47
BGA_BODY, BGA_HEIGHT = 8.15, 1.10


def bga_pad_positions():
    return {f'{r}{c}': ((c - 5.5) * BGA_PITCH, (i - 4.5) * BGA_PITCH)
            for i, r in enumerate(BGA_ROWS) for c in range(1, 11)}


def bga100():
    h = BGA_BODY / 2
    body = _rect((-4, -4), (4, 4), 'F.Fab', .1)
    body += _line((-4, -3), (-3, -4), 'F.Fab', .1)
    body += _rect((-h - .5, -h - .5), (h + .5, h + .5), 'F.CrtYd', .05)
    body += _line((-4.2, -2.6), (-4.2, -4.2), 'F.SilkS', .15) + _line((-4.2, -4.2), (-2.6, -4.2), 'F.SilkS', .15)
    margin = f'\n\t\t(solder_mask_margin {g((BGA_SM - BGA_PAD) / 2)})\n\t\t(property pad_prop_bga)'
    for num, (x, y) in sorted(bga_pad_positions().items()):
        body += (f'\t(pad "{num}" smd circle\n\t\t(at {g(x)} {g(y)})\n\t\t(size {g(BGA_PAD)} {g(BGA_PAD)})\n'
                 f'\t\t(layers "F.Cu" "F.Paste" "F.Mask"){margin})\n')
    return make_fp('M3_TFBGA100_8x8_P0.8', 'STM32H743VIH6 TFBGA-100 8 x 8 mm, 0.8 mm pitch; ST DS12110 Rev 8 Table 218 '
                   'p. 324 (body, balls) and Table 219 p. 325 (Dpad 0.40, Dsm 0.47, stencil 0.40 mm); A1 top left',
                   body, -5.6, 'M3_TFBGA100_8x8_P0.8.wrl')


# JST eGH.pdf (https://www.jst-mfg.com/product/pdf/eng/eGH.pdf, read 2026-11-02) p. 2, "PC board layout", side entry
# type, viewed from the mounting surface: contact lands 0.6 +/-0.05 wide at 1.25 +/-0.05 pitch; 5.4 +/-0.1 from the
# contact land's far end to the far end of the solder-tab lands; 3.7 +/-0.1 from the contact land's near end to that
# far end (contact land length 1.7); solder-tab lands 2.7 +/-0.1 long and 1 +/-0.1 wide, their inner edge 1.35 +/-0.1
# from the No. 1 contact centre. p. 3: header width B = 5.75 / 8.25 / 9.50 / 10.75 mm (2 / 4 / 5 / 6 circuits),
# assembled height (4.35), mated length (7.15). Frame: contacts at y < 0, tabs at y > 0, the mouth (wire entry) to +y.
GH_PITCH, GH_W, GH_L, GH_TAB_W, GH_TAB_L, GH_GAP, GH_TAB_IN = 1.25, 0.6, 1.7, 1.0, 2.7, 1.0, 1.35
GH_B = {2: 5.75, 4: 8.25, 5: 9.50, 6: 10.75}
GH_BODY_Y = (-1.6, 2.45)        # header body depth, as KiCad's generator draws it from the same drawing (Inference)
GH_PARTS = {2: ('SM02B-GHS-TB', 'C189893'), 4: ('SM04B-GHS-TB', 'C189895'), 5: ('SM05B-GHS-TB', 'C189896'),
            6: ('SM06B-GHS-TB', 'C133065')}


def gh_pad_positions(n):
    y = -(GH_GAP + GH_L / 2)
    x1 = -(n - 1) * GH_PITCH / 2
    pads = {str(i + 1): (x1 + i * GH_PITCH, y, GH_W, GH_L) for i in range(n)}
    tab_x = -x1 + GH_TAB_IN + GH_TAB_W / 2
    tabs = [(-tab_x, GH_TAB_L / 2, GH_TAB_W, GH_TAB_L), (tab_x, GH_TAB_L / 2, GH_TAB_W, GH_TAB_L)]
    return pads, tabs


def gh(n):
    model, _ = GH_PARTS[n]
    name = 'M3_GH_' + model.replace('-', '_')
    b = GH_B[n] / 2
    pads, tabs = gh_pad_positions(n)
    tab_x = tabs[1][0] + GH_TAB_W / 2
    body = _rect((-b, GH_BODY_Y[0]), (b, GH_BODY_Y[1]), 'F.Fab', .1)
    body += _rect((-max(b, tab_x) - .25, -(GH_GAP + GH_L) - .25), (max(b, tab_x) + .25, GH_TAB_L + .25), 'F.CrtYd', .05)
    body += _circle((pads['1'][0], -(GH_GAP + GH_L) - .45), .12, 'F.SilkS', .15)
    for num, (x, y, w, h) in pads.items():
        body += _round_pad(num, x, y, w, h, ('F.Cu', 'F.Mask', 'F.Paste'))
    for x, y, w, h in tabs:          # unnumbered solder tabs (mechanical, no net), as R10's GH lands
        body += _round_pad('', x, y, w, h, ('F.Cu', 'F.Mask', 'F.Paste'))
    return name, make_fp(name, f'JST {model} side-entry latching GH header; JST eGH.pdf p. 2 side-entry PC board '
                         'layout (contacts 0.6 x 1.7 at 1.25, tabs 1.0 x 2.7, 1.0 gap); unnumbered solder tabs',
                         body, -(GH_GAP + GH_L) - 1.4, name + '.wrl')


# AWG 20 stranded wire pads (D-R11-05): conductor bundle about 0.97 mm (7 x 0.32 mm) to 1.02 mm (19 x 0.203 mm)
# (Inference: typical maker values, not a specific wire's datasheet). Finished hole 1.30 mm: 0.28-0.33 mm diametral
# clearance for the bundle, inside the 0.2-0.7 mm lead-to-hole range commonly quoted from IPC-2222 Level B (Inference:
# IPC-2222 not re-read). Land 2.5 mm: >= IPC-2222's minimum land a + 2b + c = 1.43 (1.30 hole + 0.13 JLC hole
# tolerance) + 2 x 0.05 (external annular ring) + 0.6 (fabrication allowance) = 2.13 mm (Inference, as above), and a
# 0.60 mm nominal ring against JLC's 0.15 mm minimum / 0.20 mm recommended. Pitch 3.8 mm: a 1.3 mm copper gap.
WIRE_HOLE, WIRE_PAD, WIRE_PITCH = 1.30, 2.50, 3.80


def wirepads():
    name = 'M3_WIREPAD_2P_AWG20'
    x = WIRE_PITCH / 2
    body = _circle((-x, 0), WIRE_HOLE / 2 + .25, 'F.Fab', .1) + _circle((x, 0), WIRE_HOLE / 2 + .25, 'F.Fab', .1)
    body += _rect((-x - WIRE_PAD / 2 - .25, -WIRE_PAD / 2 - .25), (x + WIRE_PAD / 2 + .25, WIRE_PAD / 2 + .25),
                  'F.CrtYd', .05)
    for num, px in (('1', -x), ('2', x)):
        body += (f'\t(pad "{num}" thru_hole circle\n\t\t(at {g(px)} 0)\n\t\t(size {g(WIRE_PAD)} {g(WIRE_PAD)})\n'
                 f'\t\t(drill {g(WIRE_HOLE)})\n\t\t(layers "*.Cu" "*.Mask"))\n')
    return name, make_fp(name, 'Two plated AWG 20 stranded wire pads, 1.30 mm finished hole, 2.50 mm land, 3.80 mm '
                         'pitch; hand-soldered, no paste, not in the JLC BOM or CPL (parts_r11.md)',
                         body, -2.6, None, attr='through_hole exclude_from_pos_files exclude_from_bom')


def footprints():
    out = {'M3_TFBGA100_8x8_P0.8': bga100()}
    for n in GH_B:
        name, text = gh(n)
        out[name] = text
    name, text = wirepads()
    out[name] = text
    return out


PCB, BLACK, IVORY = '.06 .25 .10', '.12 .12 .12', '.92 .89 .78'
MODELS = {
    'M3_TFBGA100_8x8_P0.8.wrl': ('# TFBGA-100 envelope, DS12110 Rev 8 Table 218 maxima: 8.15 x 8.15 x 1.10 mm. NOT a maker '
                                 'model.\n', [(0, 0, 0, BGA_BODY, BGA_BODY, BGA_HEIGHT, BLACK)]),
    **{f'M3_GH_{GH_PARTS[n][0].replace("-", "_")}.wrl': (
        f'# JST {GH_PARTS[n][0]} header envelope: {GH_B[n]} mm wide (eGH p. 3 B), {GH_BODY_Y[1] - GH_BODY_Y[0]:.2f} mm '
        'deep, 4.35 mm high (eGH p. 2, assembled). NOT a maker model.\n',
        [(0, sum(GH_BODY_Y) / 2, 0, GH_B[n], GH_BODY_Y[1] - GH_BODY_Y[0], 4.35, IVORY)]) for n in GH_B},
}


def model_text(name):
    note, boxes = MODELS[name]
    return '#VRML V2.0 utf8\n' + note + ''.join(_box(*b) for b in boxes)


# ---------------------------------------------------------------------------------------------------------------------
# symbols

def block(text, name):
    i = text.index(f'\t(symbol "{name}"\n')
    return i, r7_parts._close(text, i + 1)


def mcu_tfbga100(library):
    """R10's MCU symbol with every pin re-numbered LQFP100 -> TFBGA100 at the same position; the VREF+ position
    becomes PDR_ON (F7), and the VDD pins on balls F4 / F6 are named VDDLDO / VDD33USB."""
    s, e = block(library, 'MCU')
    text = library[s:e].replace('(symbol "MCU"', '(symbol "MCU_TFBGA100"', 1)
    text = text.replace('(symbol "MCU_0_1"', '(symbol "MCU_TFBGA100_0_1"').replace('(symbol "MCU_1_1"',
                                                                                     '(symbol "MCU_TFBGA100_1_1"')

    def pin(m):
        body = m.group(0)
        num = re.search(r'\(number "([^"]+)"', body).group(1)
        if num == r11.VREF_PIN:
            body = body.replace('(pin power_in ', '(pin input ').replace('(name "VREF+"', '(name "PDR_ON"')
            return body.replace(f'(number "{num}"', f'(number "{r11.PDR_ON}"')
        ball = r11.BALL[num]
        if ball in r11.BALL_NAMES:
            body = re.sub(r'\(name "[^"]+"', f'(name "{r11.BALL_NAMES[ball]}"', body)
        return body.replace(f'(number "{num}"', f'(number "{ball}"')

    filt = '(property "ki_fp_filters" "LQFP-100_L14.0-W14.0-P0.50-LS16.0-BL"'
    assert text.count(filt) == 1
    text = text.replace(filt, '(property "ki_fp_filters" "M3_TFBGA100_8x8_P0.8"')
    text = re.sub(r'\(pin \w+ line\n.*?\(number "[^"]+"', pin, text, flags=re.S)
    numbers = re.findall(r'\(number "([^"]+)"', text)
    assert sorted(numbers) == sorted(set(r11.BALL.values()) | {r11.PDR_ON}) and len(numbers) == 100
    return text


CAMERA_PINS = (('1', '5V OUT'), ('2', '5V OUT'), ('3', 'GND'), ('4', 'GND'), ('5', 'RX FROM CAMERA TX'),
               ('6', 'TX TO CAMERA RX'))


def camera_gh6():
    return module_symbol('CameraGH6', 'J', 'JST SM06B-GHS-TB camera port (D-R11-05): 1-2 CAM_5V, 3-4 GND, 5 board RX '
                         '(camera TX), 6 board TX (camera RX)', 'camera port UART', 'M3_GH_SM06B_GHS_TB', 10.16, 8.89,
                         [(y, n, name, 'passive') for y, (n, name) in zip((6.35, 3.81, 1.27, -1.27, -3.81, -6.35),
                                                                         CAMERA_PINS)], [])


TEXTS = {   # symbol: (R10 Description, R11 Description, R10 filter, R11 filter)
    'PortTerminal': ('DORABO DB125-3.5-4P-GN-S always-on port (D-R19-14): 1 PORT_4V8, 2 GND, 3 board TXO, 4 board RXI',
                     'JST SM04B-GHS-TB always-on port (D-R19-14, D-R11-05): 1 PORT_4V8, 2 GND, 3 board TXO, 4 board RXI',
                     'M3_DB125_4P_GN', 'M3_GH_SM04B_GHS_TB'),
    'ServoTerminal': ('DORABO DB1253.5mm5pos; four servo signals and GND only',
                      'JST SM05B-GHS-TB (D-R11-05); four servo signals and GND only', 'M3_DB125_5P_GN',
                      'M3_GH_SM05B_GHS_TB'),
}


def symbol_library():
    library = (r11.INPUT / 'm3.kicad_sym').read_text()
    for name, (d0, d1, f0, f1) in TEXTS.items():
        s, e = block(library, name)
        b = library[s:e]
        assert b.count(f'"{d0}"') == 1 and b.count(f'(property "ki_fp_filters" "{f0}"') == 1, name
        b = b.replace(f'"{d0}"', f'"{d1}"').replace(f'(property "ki_fp_filters" "{f0}"', f'(property "ki_fp_filters" "{f1}"')
        library = library[:s] + b + library[e:]
    extra = mcu_tfbga100(library) + '\n' + camera_gh6()
    return library.rstrip()[:-1].rstrip('\n') + '\n' + extra.rstrip('\n') + '\n)\n'


# ---------------------------------------------------------------------------------------------------------------------

def r11_footprints():
    """{footprint name} of every R11 part: R10's netlist with circuit.json's footprint changes."""
    data = r11.circuit()
    parts, _ = r11.r10_netlist()
    fps = {ref: c.findtext('footprint').split(':')[1] for ref, c in parts.items()}
    for ref, entry in data['parts'].items():
        fps[ref] = (data['catalog'][entry['lcsc']]['footprint'] if entry.get('lcsc') else entry['footprint']).split(':')[1]
    return fps


def generated():
    r11.source_check()
    new = footprints()
    files = {SYMLIB: symbol_library()}
    for name, text in new.items():
        files[PRETTY / (name + '.kicad_mod')] = text
    for name in MODELS:
        files[SHAPES / name] = model_text(name)
    copied = {}
    for name in sorted(set(r11_footprints().values()) - set(new)):
        src = r11.R10 / 'kilib/rocket.pretty' / (name + '.kicad_mod')
        copied[PRETTY / src.name] = src
        for model in re.findall(r'\(model "\$\{KIPRJMOD\}/kilib/([^"]+)"', src.read_text()):
            copied[LIB / model] = r11.R10 / 'kilib' / model
    return files, copied


def stale(files, copied):
    out = [p for p, t in files.items() if not p.exists() or p.read_text() != t]
    out += [p for p, s in copied.items() if not p.exists() or p.read_bytes() != s.read_bytes()]
    wanted = set(files) | set(copied)
    out += [p for p in LIB.rglob('*') if p.is_file() and p not in wanted]       # nothing unlisted in kilib
    return out


def write(files, copied):
    for p in [p for p in LIB.rglob('*') if p.is_file() and p not in set(files) | set(copied)]:
        p.unlink()
    for p, t in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_text() != t:
            p.write_text(t)
    for p, s in copied.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_bytes() != s.read_bytes():
            shutil.copyfile(s, p)


def geometry_checks():
    """Parse every R11 land with pcbnew and assert the maker dimensions above."""
    import pcbnew
    mm = pcbnew.ToMM
    result = {}
    for name in sorted(set(r11_footprints().values())):
        fp = pcbnew.FootprintLoad(str(PRETTY), name)
        assert fp is not None, name
        result[name] = {p.GetNumber() or f'tab{i}': [round(mm(p.GetFPRelativePosition().x), 4),
                                                     round(mm(p.GetFPRelativePosition().y), 4),
                                                     round(mm(p.GetSize().x), 4), round(mm(p.GetSize().y), 4)]
                        for i, p in enumerate(fp.Pads())}
        for model in fp.Models():
            assert model.m_Filename.startswith('${KIPRJMOD}/kilib/'), (name, model.m_Filename)
            assert (LIB / model.m_Filename.split('/kilib/', 1)[1]).exists(), (name, model.m_Filename)
    bga = result['M3_TFBGA100_8x8_P0.8']
    assert len(bga) == 100 and bga['A1'] == [-3.6, -3.6, .4, .4] and bga['K10'] == [3.6, 3.6, .4, .4]
    assert bga['F7'] == [1.2, .4, .4, .4]
    fp = pcbnew.FootprintLoad(str(PRETTY), 'M3_TFBGA100_8x8_P0.8')
    assert all(abs(mm(p.GetLocalSolderMaskMargin() or 0) - .035) < 1e-6 for p in fp.Pads())
    for n, (model, _) in GH_PARTS.items():
        pads = result['M3_GH_' + model.replace('-', '_')]
        sig = [pads[str(i)] for i in range(1, n + 1)]
        tabs = [v for k, v in pads.items() if k.startswith('tab')]
        assert len(sig) == n and len(tabs) == 2 and len(pads) == n + 2
        assert all(round(b[0] - a[0], 4) == 1.25 and a[2:] == [.6, 1.7] for a, b in zip(sig, sig[1:]))
        far_contact, near_contact = sig[0][1] - .85, sig[0][1] + .85
        far_tab = tabs[0][1] + 1.35
        assert round(far_tab - far_contact, 4) == 5.4 and round(far_tab - near_contact, 4) == 3.7
        assert all(t[2:] == [1.0, 2.7] for t in tabs)
        assert round(abs(tabs[0][0]) - .5 - abs(sig[0][0]), 4) == 1.35
    wire = result['M3_WIREPAD_2P_AWG20']
    assert wire == {'1': [-1.9, 0, 2.5, 2.5], '2': [1.9, 0, 2.5, 2.5]}
    fp = pcbnew.FootprintLoad(str(PRETTY), 'M3_WIREPAD_2P_AWG20')
    for p in fp.Pads():
        assert round(mm(p.GetDrillSize().x), 4) == 1.3 and not p.IsOnLayer(pcbnew.F_Paste) and not p.IsOnLayer(pcbnew.B_Paste)
    assert fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM and fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES
    return result


# ---------------------------------------------------------------------------------------------------------------------
# JLC stock (network)

def stock():
    sys.path.insert(0, str(r11.ROOT_DIR / 'tools'))
    import jlc_stock
    data = r11.circuit()
    demand = {}
    for ref, entry in data['parts'].items():
        if entry.get('lcsc'):
            demand.setdefault(entry['lcsc'], []).append(ref)
    parts, _ = r11.r10_netlist()        # R10 parts R11 keeps that share a changed code also count
    for ref, comp in parts.items():
        if ref in data['parts']:
            continue
        code = {f.get('name'): f.text for f in comp.findall('./fields/field')}.get('LCSC')
        if code in data['catalog']:
            demand[code].append(ref)
    rows, failures = {}, []
    for code in sorted(data['catalog']):
        item = jlc_stock.lookup(code)
        stock_count, presale, available = jlc_stock.orderable(item)
        need = len(demand.get(code, [])) * BOARDS
        minimum, purchase = jlc_stock.purchase_quantity(item, need) if item else (None, need)
        cat = data['catalog'][code]
        row = {'refs': sorted(demand.get(code, [])), 'qty_per_board': len(demand.get(code, [])), 'need_5_boards': purchase,
               'stockCount': stock_count, 'canPresaleNumber': presale, 'orderable': available,
               'library_type': item.get('componentLibraryType'), 'preferred': item.get('preferredComponentFlag'),
               'jlc_model': item.get('componentModelEn'), 'jlc_brand': item.get('componentBrandEn'),
               'package': item.get('componentSpecificationEn'), 'describe': item.get('describe'),
               'datasheet': item.get('dataManualUrl'),
               'unit_price_usd': (item.get('componentPrices') or [{}])[0].get('productPrice')}
        if not item or available is None or available < purchase:
            failures.append(f'{code}: orderable {available} < {purchase}')
        if item and (item.get('componentModelEn') != cat['Manufacturer Part'] or item.get('componentBrandEn') != cat['Manufacturer']):
            failures.append(f'{code}: JLC lists {item.get("componentBrandEn")} {item.get("componentModelEn")}, '
                            f'circuit.json {cat["Manufacturer"]} {cat["Manufacturer Part"]}')
        rows[code] = row
    report = {'checked_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
              'source': jlc_stock.API, 'boards': BOARDS,
              'rule': 'orderable = min(stockCount, canPresaleNumber) as tools/jlc_stock.py (R20-BOM-01, Inference about JLC fields)',
              'parts': rows, 'failures': failures}
    STOCK.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f'JLC: {len(rows)} codes, {len(failures)} failures -> {STOCK}')
    for f in failures:
        print('  ', f)
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--library-only', action='store_true')
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--stock', action='store_true')
    args = ap.parse_args()
    if args.stock:
        return stock()
    files, copied = generated()
    old = stale(files, copied)
    if args.check and old:
        print('r11_parts: stale:', ', '.join(str(p.relative_to(LIB)) for p in old))
        return 1
    if args.library_only:
        write(files, copied)
    rows = geometry_checks()
    print(f'r11_parts: {len(rows)} footprints parsed, {len(files) + len(copied)} library files current')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
