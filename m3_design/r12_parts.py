#!/usr/bin/env python3
"""Generate and check the M3-ASSY-R12 project library (m3_design/r12/kilib); price the stage A BOM at JLC.

usage: KiCad python3 -I -B m3_design/r12_parts.py --library-only   write kilib/ (symbols, footprints, 3D models)
       KiCad python3 -I -B m3_design/r12_parts.py --check          fail if kilib/ is stale; parse every land with pcbnew
       python3 -I -B m3_design/r12_parts.py --stock                query JLC for every R12 BOM code (network): stock,
                                                                    price, library; writes design/jlc_r12_stock.json and
                                                                    design/r12_cost.json (Economic PCBA, 2 and 5 boards)
The library is R11's (hash-pinned in r11_input/manifest.json: symbols copied from r11_input/m3.kicad_sym, footprints
and models from R11's kilib, only those R12 uses) plus the R12 parts (R12_DECISIONS D-R12-06 ... -16). New lands, each
from the maker's drawing or the LCSC / JLCEDA official land (https://easyeda.com/api/products/<code>/components, the
library JLC's own CPL uses), with the URL noted below. Every R12 land is a top-side land (D-R12-01, one assembled side):
SMD pads on F.Cu / F.Paste / F.Mask only, or plated through-holes.
Symbols: R11's library with the R12 symbols added (LMR50410, TPS563208, FXLS9xxxx, Buzzer_THT2, BAT54C, ServoGH6,
SwitchGH4) and every used symbol's ki_fp_filters set to exactly the R12 footprints it carries (ERC footprint_filter).
"""
import argparse
import datetime
import json
import math
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r7_parts
from r7_parts import _box, _circle, _line, _rect, g, module_symbol
import r12_sch as r12

LIB = r12.PROJECT / 'kilib'
PRETTY = LIB / 'rocket.pretty'
SHAPES = LIB / 'rocket.3dshapes'
SYMLIB = LIB / 'm3.kicad_sym'
STOCK = r12.DESIGN / 'jlc_r12_stock.json'
COST = r12.DESIGN / 'r12_cost.json'
GEN = 'm3_r12_parts'
EASYEDA = 'https://easyeda.com/api/products/{}/components'


def make_fp(name, descr, body, ref_y, model, attr='smd'):
    text = r7_parts.footprint(name, descr, body, ref_y, -ref_y, model or 'none').replace('m3_r7_parts', GEN)
    if model is None:
        text = text[:text.index('\t(model ')] + ')\n'
    return text.replace('(attr smd)', f'(attr {attr})')


def _rpad(num, x, y, w, h, layers=('F.Cu', 'F.Mask', 'F.Paste'), shape='rect'):
    lay = ' '.join(f'"{l}"' for l in layers)
    return f'\t(pad "{num}" smd {shape}\n\t\t(at {g(x)} {g(y)})\n\t\t(size {g(w)} {g(h)})\n\t\t(layers {lay}))\n'


def _courtyard(points, pad=0.25):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return _rect((min(xs) - pad, min(ys) - pad), (max(xs) + pad, max(ys) + pad), 'F.CrtYd', .05)


def _pad_extents(pads):
    pts = []
    for _, x, y, w, h in pads:
        pts += [(x - w / 2, y - h / 2), (x + w / 2, y + h / 2)]
    return pts


# ---------------------------------------------------------------------------------------------------------------------
# SH-1.0 clone headers (D-R12-31, owner 2026-11-03: the MicoAir H743's port family, so one module lead fits both boards;
# R11's D-R11-05 rejected SH for its friction-only retention, which the owner now accepts with a retention step per flight).
# Megastar ZX-SH1.0-4PWT (C7430446) and ZX-SH1.0-6PWT (C7430448), side entry, 1 A per contact (JLC listing, Live
# 2026-11-04). JLCEDA's land could not be fetched (HTTP 403, 2026-11-04), so the land is JST's own SMnnB-SRSS-TB land as
# KiCad's library draws it from JST eSH.pdf (Connector_JST JST_SH_SM0nB-SRSS-TB_1x0n-1MP_P1.00mm_Horizontal): contacts
# 0.6 x 1.55 at 1.0 mm, y -2.0; two fixing tabs 1.2 x 1.8 at x +-(n / 2 + 0.8), y +1.875 (Datasheet via KiCad; that the
# clone takes the JST land is an Inference, as for the GH clones). Body from the JLC listing: width 6.35 / 8.35 mm,
# depth 4.3 mm, height 3.15 mm; contacts behind the rear wall, mouth to +y. Mating with JST SH housings: O-R12-04.
GHC = {
    4: dict(code='C7430446', name='M3_SHC_4P', y_sig=-2.0, tab=(2.8, 1.875, 1.2, 1.8), width=6.35),
    6: dict(code='C7430448', name='M3_SHC_6P', y_sig=-2.0, tab=(3.8, 1.875, 1.2, 1.8), width=8.35),
}
GHC_PITCH, GHC_W, GHC_L, GHC_DEPTH, GHC_HEIGHT = 1.0, 0.6, 1.55, 4.3, 3.15


def ghc_pads(n):
    c = GHC[n]
    x1 = -(n - 1) * GHC_PITCH / 2
    pads = [(str(i + 1), round(x1 + i * GHC_PITCH, 4), c['y_sig'], GHC_W, GHC_L) for i in range(n)]
    tx, ty, tw, th = c['tab']
    tabs = [('', -tx, ty, tw, th), ('', tx, ty, tw, th)]
    return pads, tabs


def ghc_body_y(n):
    rear = GHC[n]['y_sig'] + 0.25         # R11's JST land: body rear wall 0.25 mm in front of the contact pad centre
    return rear, rear + GHC_DEPTH


def ghc(n):
    c = GHC[n]
    pads, tabs = ghc_pads(n)
    y0, y1 = ghc_body_y(n)
    b = c['width'] / 2
    body = _rect((-b, y0), (b, y1), 'F.Fab', .1)
    body += _courtyard(_pad_extents(pads + tabs) + [(-b, y0), (b, y1)])
    body += _circle((pads[0][1], c['y_sig'] - GHC_L / 2 - .45), .12, 'F.SilkS', .15)
    for num, x, y, w, h in pads + tabs:
        body += _rpad(num, x, y, w, h)
    return c['name'], make_fp(c['name'], f'Megastar ZX-SH1.0-{n}PWT side-entry SH-1.0 clone ({c["code"]}); JST '
                              f'SM0{n}B-SRSS-TB land (contacts 0.6 x 1.55 at 1.0, two fixing tabs); top side only',
                              body, c['y_sig'] - GHC_L / 2 - 1.4, c['name'] + '.wrl')


# NXP FXLS90322AESR2 HLQFN-16 4 x 4 x 1.45 mm, 0.8 mm pitch (D-R12-51). Land: NXP FXLS9xxx0 Rev 6 (8 February 2021; the
# LCSC copy for C5190712, https://www.lcsc.com/datasheet/lcsc_datasheet_2405281435_NXP-Semicon-FXLS90322AESR2_C5190712.pdf)
# Figure 111 (drawing 98ASA00761D rev F, SOT1688-1(SC)): I/O pads 0.5 x 0.85 at 0.8 mm pitch centred 1.975 mm from the
# package centre, die attach pad 2.6 x 2.6; Figure 110 mask openings 0.6 x 0.95 and 2.7 x 2.7 (mask margin 0.05). Pins:
# Figure 9 transparent top view: 1-4 down the west side from the pin-1 corner, 5-8 along the south side, 9-12 up the east
# side, 13-16 along the north side; 17 the die attach pad (to VSS, Table 9). JLCEDA C5190712 places its I/O pads 0.1 mm
# further out (0.5 x 0.95 at 2.075); NXP's drawing is used. That the dual-channel FXLS9xxxx (FXLS90322) has the same
# package and SPI pin-out as this single-channel sheet is an Inference (the figure itself is labelled FXLS9xxxx; JLCEDA's
# C5190712 symbol gives the same pin names). Paste on the die pad 2.0 x 2.0 (paste margin -0.3, about 59 %, Inference).
FX_C, FX_W, FX_L, FX_EP, FX_BODY, FX_H = 1.975, 0.5, 0.85, 2.6, 4.0, 1.45


def fx_pads():
    pads = []
    for i, o in enumerate((-1.2, -0.4, 0.4, 1.2)):
        pads += [(str(1 + i), -FX_C, o, FX_L, FX_W), (str(5 + i), o, FX_C, FX_W, FX_L),
                 (str(9 + i), FX_C, -o, FX_L, FX_W), (str(13 + i), -o, -FX_C, FX_W, FX_L)]
    return tuple(sorted(pads, key=lambda p: int(p[0]))) + (('17', 0.0, 0.0, FX_EP, FX_EP),)


FX_PADS = fx_pads()


def fxls():
    name = 'M3_FXLS_HLQFN16'
    h = FX_BODY / 2
    body = _rect((-h, -h), (h, h), 'F.Fab', .1) + _line((-h, -1.2), (-1.2, -h), 'F.Fab', .1)
    body += _courtyard(_pad_extents(FX_PADS) + [(-h, -h), (h, h)])
    body += _circle((-h - .45, -h - .1), .12, 'F.SilkS', .15)
    for num, x, y, w, hh in FX_PADS:
        pad = _rpad(num, x, y, w, hh)
        extra = '\t\t(solder_mask_margin 0.05)\n' + ('\t\t(solder_paste_margin -0.3)\n' if num == '17' else '')
        body += pad[:-2] + '\n' + extra.rstrip('\n') + ')\n'
    return name, make_fp(name, 'NXP FXLS90322 HLQFN-16 4 x 4 mm, 0.8 mm pitch (SOT1688-1(SC)); land FXLS9xxx0 Rev 6 '
                         'Figure 110 / 111; pins Figure 9; top side only', body, -h - 1.0, name + '.wrl')


# QMB-09B-03 9 mm passive magnetic buzzer, THT (D-R12-16): Huawha product specification QMB-09B-03 (2019-12-3, LCSC
# C96256 PDF) item 4 dimension drawing: body 9.0 x 5.5 mm, two 0.6 +/- 0.05 mm pins at 4.0 mm, (+) and (-) marked. Land
# JLCEDA C96256 "BUZ-TH_BD9.0-P4.00-D0.6-FD": 1.0 mm finished hole, 1.8 mm pad, 4.0 mm pitch; pin 1 (+) (Inference:
# JLCEDA's numbering, check the (+) mark when fitting). Owner-fitted by hand after reflow: no paste.
BUZ_PITCH, BUZ_HOLE, BUZ_PAD, BUZ_D, BUZ_H = 4.0, 1.0, 1.8, 9.0, 5.5


def buzzer():
    name = 'M3_BUZ_TH_D9_P4'
    body = _circle((0, 0), BUZ_D / 2, 'F.Fab', .1) + _circle((0, 0), BUZ_D / 2 + .25, 'F.CrtYd', .05)
    body += _line((-2.0, -2.2), (-2.0, -1.4), 'F.SilkS', .15) + _line((-2.4, -1.8), (-1.6, -1.8), 'F.SilkS', .15)
    # D-R12-82: the polarity on F.Fab as R10's LS120 land carries it (check_r10.FAB_TEXT_ALLOWED: '+' / '-'), so the
    # owner's fitting drawing shows which hole takes the (+) lead (pin 1 = (+) remains an Inference, D-R12-16)
    body += ''.join(f'\t(fp_text user "{t}" (at {g(x)} 1.6) (layer "F.Fab") (effects (font (size 0.8 0.8) '
                    f'(thickness 0.10))))\n' for t, x in (('+', -BUZ_PITCH / 2), ('-', BUZ_PITCH / 2)))
    for num, x in (('1', -BUZ_PITCH / 2), ('2', BUZ_PITCH / 2)):
        body += (f'\t(pad "{num}" thru_hole {"rect" if num == "1" else "circle"}\n\t\t(at {g(x)} 0)\n'
                 f'\t\t(size {g(BUZ_PAD)} {g(BUZ_PAD)})\n\t\t(drill {g(BUZ_HOLE)})\n\t\t(layers "*.Cu" "*.Mask")\n'
                 '\t\t(remove_unused_layers yes)\n\t\t(keep_end_layers yes))\n')
    return name, make_fp(name, 'Huawha QMB-09B-03 9 mm THT buzzer, pins 4.0 mm, hole 1.0 mm, pad 1.8 mm; land JLCEDA '
                         'C96256; owner-fitted (no paste)', body, -5.6, name + '.wrl', attr='through_hole')


# TPS563208DDCR SOT-23-THIN-6 (DDC) (D-R12-07 / -08): JLCEDA C468250 "TSOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL", read
# 2026-11-04: pads 0.55 x 1.2 at 0.95 pitch, rows at y = +/-1.2, pin 1 bottom left (R11's TSOT-26 land has 1.1 mm pads).
DDC_PADS = tuple((str(n), x, y, 0.55, 1.2) for n, x, y in
                 ((1, -.95, 1.2), (2, 0, 1.2), (3, .95, 1.2), (4, .95, -1.2), (5, 0, -1.2), (6, -.95, -1.2)))


def ddc6():
    name = 'M3_TSOT23_6_DDC'
    body = _rect((-1.45, -.8), (1.45, .8), 'F.Fab', .1)
    body += _courtyard(_pad_extents(DDC_PADS) + [(-1.45, -.8), (1.45, .8)])
    body += _circle((-.95, 2.15), .12, 'F.SilkS', .15)
    for num, x, y, w, h in DDC_PADS:
        body += _rpad(num, x, y, w, h)
    return name, make_fp(name, 'TI DDC (SOT-23-THIN-6) for TPS563208; land JLCEDA C468250 '
                         '(https://easyeda.com/api/products/C468250/components); top side only', body, -2.4, name + '.wrl')


# D-R12-30 (owner, 2026-11-03): J1 stays soldered pack wire pads, drawn as two plated holes at 5.0 mm pitch so a 5.0 mm
# two-position screw terminal fits later with no board change. Hole 1.40 mm finished: a tinned 16-20 AWG conductor
# (about 1.3-0.8 mm, Inference: typical bundle sizes) and a 5.0 mm terminal pin (about 1.0-1.2 mm, Inference) both go in;
# land 2.6 mm (0.6 mm ring against JLC's 0.15 mm minimum; 2.4 mm copper gap). The courtyard is the 10 x 8.2 mm keep-clear
# for a future terminal body, its wire side at -y (the board edge after rotation 90).
BAT_HOLE, BAT_PAD, BAT_PITCH = 1.40, 2.60, 5.00
BAT_KEEP = (-5.0, -3.2, 5.0, 5.0)


def batpads():
    name = 'M3_WIREPAD_2P_P5'
    x = BAT_PITCH / 2
    body = _circle((-x, 0), BAT_HOLE / 2 + .25, 'F.Fab', .1) + _circle((x, 0), BAT_HOLE / 2 + .25, 'F.Fab', .1)
    body += _rect(BAT_KEEP[:2], BAT_KEEP[2:], 'F.Fab', .1)
    body += _rect(BAT_KEEP[:2], BAT_KEEP[2:], 'F.CrtYd', .05)
    for num, px in (('1', -x), ('2', x)):
        body += (f'\t(pad "{num}" thru_hole circle\n\t\t(at {g(px)} 0)\n\t\t(size {g(BAT_PAD)} {g(BAT_PAD)})\n'
                 f'\t\t(drill {g(BAT_HOLE)})\n\t\t(layers "*.Cu" "*.Mask")\n'
                 '\t\t(remove_unused_layers yes)\n\t\t(keep_end_layers yes))\n')
    return name, make_fp(name, 'Battery pigtail pads: two plated 1.40 mm holes, 2.60 mm land, 5.00 mm pitch (a later 5.0 mm '
                         'screw terminal fits); hand-soldered, no paste, not in the JLC BOM or CPL (D-R12-30)',
                         body, -3.8, None, attr='through_hole exclude_from_pos_files exclude_from_bom')


R10_REUSE = ('M3_DB125_2P_BK',)       # D-R12-29: R10's verified DB125-2 (black) land and model, copied verbatim


def footprints():
    out = {}
    for maker in (lambda: ghc(4), lambda: ghc(6), fxls, buzzer, ddc6, batpads):
        name, text = maker()
        out[name] = text
    return out


PCB, BLACK, IVORY, GREY = '.06 .25 .10', '.12 .12 .12', '.92 .89 .78', '.6 .6 .6'
MODELS = {
    **{GHC[n]['name'] + '.wrl': (
        f'# Megastar ZX-SH1.0-{n}PWT envelope: {GHC[n]["width"]} x {GHC_DEPTH} x {GHC_HEIGHT} mm (JLC listing). NOT a maker '
        'model.\n', [(0, sum(ghc_body_y(n)) / 2, 0, GHC[n]['width'], GHC_DEPTH, GHC_HEIGHT, IVORY)]) for n in GHC},
    'M3_FXLS_HLQFN16.wrl': ('# FXLS90322 HLQFN-16 envelope 4.0 x 4.0 x 1.45 mm (FXLS9xxx0 Rev 6 Table 1). NOT a maker '
                            'model.\n', [(0, 0, 0, FX_BODY, FX_BODY, FX_H, GREY)]),
    'M3_BUZ_TH_D9_P4.wrl': ('# QMB-09B-03 envelope 9.3 x 9.3 x 5.7 mm (spec item 4, +0.3 tolerance). NOT a maker model.\n',
                            [(0, 0, 0, 9.3, 9.3, 5.7, BLACK)]),
    'M3_TSOT23_6_DDC.wrl': ('# TI DDC envelope 2.9 x 1.6 x 1.1 mm. NOT a maker model.\n', [(0, 0, 0, 2.9, 1.6, 1.1, BLACK)]),
}


def model_text(name):
    note, boxes = MODELS[name]
    return '#VRML V2.0 utf8\n' + note + ''.join(_box(*b) for b in boxes)


# ---------------------------------------------------------------------------------------------------------------------
# symbols

def block(text, name):
    i = text.index(f'\t(symbol "{name}"\n')
    return i, r7_parts._close(text, i + 1)


def P(y, num, name, kind='passive'):
    return (y, num, name, kind)


NEW_SYMBOLS = (
    ('LMR50410', 'U', 'TI LMR50410 4-36 V 1 A buck, SOT-23-6 DBV (SLUSDW3A Table 6-1): 1 CB, 2 GND, 3 FB, 4 EN, 5 VIN, '
     '6 SW', 'buck regulator', 7.62, 5.08,
     [P(2.54, '5', 'VIN', 'power_in'), P(0, '4', 'EN', 'input'), P(-2.54, '2', 'GND', 'power_in')],
     [P(2.54, '6', 'SW', 'output'), P(0, '1', 'CB'), P(-2.54, '3', 'FB', 'input')]),
    ('TPS563208', 'U', 'TI TPS563208 4.5-17 V 3 A FCCM buck, SOT-23-THIN-6 DDC (SLVSD90B Table 4-1): 1 GND, 2 SW, '
     '3 VIN, 4 VFB, 5 EN, 6 VBST', 'buck regulator', 7.62, 5.08,
     [P(2.54, '3', 'VIN', 'power_in'), P(0, '5', 'EN', 'input'), P(-2.54, '1', 'GND', 'power_in')],
     [P(2.54, '2', 'SW', 'output'), P(0, '6', 'VBST'), P(-2.54, '4', 'VFB', 'input')]),
    ('FXLS9xxxx', 'U', 'NXP FXLS9xxxx inertial sensor, HLQFN-16, SPI mode (FXLS9xxx0 Rev 6 Figure 9 / Table 9): 1 13 15 16 '
     'VCC, 2 n.c., 3-6 TEST0-3, 7 14 VSS, 8 SS_B, 9 SCLK, 10 MOSI, 11 MISO, 12 PCM0/ARM0, 17 die pad (VSS)',
     'accelerometer high-g SPI', 7.62, 12.7,
     [P(10.16, '1', 'VCC', 'power_in'), P(7.62, '13', 'VCC', 'power_in'), P(5.08, '15', 'VCC', 'power_in'),
      P(2.54, '16', 'VCC', 'power_in'), P(0, '7', 'VSS', 'power_in'), P(-2.54, '14', 'VSS', 'power_in'),
      P(-5.08, '17', 'PAD', 'power_in'), P(-7.62, '2', 'n.c.'), P(-10.16, '12', 'PCM0/ARM0', 'output')],
     [P(10.16, '8', 'SS_B', 'input'), P(7.62, '9', 'SCLK', 'input'), P(5.08, '10', 'MOSI', 'input'),
      P(2.54, '11', 'MISO', 'passive'), P(-2.54, '3', 'TEST0'), P(-5.08, '4', 'TEST1'), P(-7.62, '5', 'TEST2'),
      P(-10.16, '6', 'TEST3')]),
    ('Buzzer_THT2', 'LS', 'Two-pin THT magnetic buzzer (QMB-09B-03): 1 (+), 2 (-)', 'buzzer transducer', 5.08, 2.54,
     [P(0, '1', '+')], [P(0, '2', '-')]),
    ('BAT54C', 'D', 'Nexperia BAT54C dual Schottky, common cathode (pinning Table 2): 1 A1, 2 A2, 3 K', 'diode schottky',
     5.08, 2.54, [P(1.27, '1', 'A1'), P(-1.27, '2', 'A2')], [P(0, '3', 'K')]),
    ('ServoGH6', 'J', 'GH-1.25 clone 6-pin servo port (D-R12-15): 1-4 SERVO1-4, 5 GND, 6 unused', 'connector servo',
     7.62, 7.62, [P(6.35, '1', 'SERVO1'), P(3.81, '2', 'SERVO2'), P(1.27, '3', 'SERVO3'), P(-1.27, '4', 'SERVO4'),
                  P(-3.81, '5', 'GND'), P(-6.35, '6', 'NC')], []),
    ('SwitchGH4', 'J', 'GH-1.25 clone 4-pin external switch port (D-R12-15): 1 SW SOURCE, 2 SW RETURN, 3-4 unused',
     'connector switch', 7.62, 5.08, [P(3.81, '1', 'SW SOURCE'), P(1.27, '2', 'SW RETURN'), P(-1.27, '3', 'NC'),
                                      P(-3.81, '4', 'NC')], []),
)
TEXTS = {   # symbol: (R11 Description, R12 Description)
    'PortTerminal': ('JST SM04B-GHS-TB always-on port (D-R19-14, D-R11-05): 1 PORT_4V8, 2 GND, 3 board TXO, 4 board RXI',
                     'GH-1.25 clone 4-pin always-on port (D-R19-14, D-R12-15): 1 PORT_4V8, 2 GND, 3 board TXO, '
                     '4 board RXI'),
}


def r12_footprints_by_symbol():
    parts, _ = r12.model()
    out = {}
    for p in parts.values():
        out.setdefault(p['lib'].split(':')[1], set()).add(p['footprint'].split(':')[1])
    return out


def set_filter(library, name, fps):
    s, e = block(library, name)
    b = library[s:e]
    new = f'(property "ki_fp_filters" "{" ".join(sorted(fps))}"'
    if '(property "ki_fp_filters" "' not in b:       # no filter: ERC footprint_filter has nothing to check
        return library
    b = re.sub(r'\(property "ki_fp_filters" "[^"]*"', new, b, count=1)
    return library[:s] + b + library[e:]


def symbol_library():
    library = (r12.INPUT / 'm3.kicad_sym').read_text()
    for name, (d0, d1) in TEXTS.items():
        s, e = block(library, name)
        b = library[s:e]
        assert b.count(f'"{d0}"') == 1, name
        library = library[:s] + b.replace(f'"{d0}"', f'"{d1}"') + library[e:]
    extra = ''
    for name, ref, descr, kw, hw, hh, left, right in NEW_SYMBOLS:
        assert f'\t(symbol "{name}"\n' not in library, name
        extra += module_symbol(name, ref, descr, kw, 'X', hw, hh, left, right)
    library = library.rstrip()[:-1].rstrip('\n') + '\n' + extra.rstrip('\n') + '\n)\n'
    for name, fps in sorted(r12_footprints_by_symbol().items()):
        library = set_filter(library, name, fps)
    return library


# ---------------------------------------------------------------------------------------------------------------------

def r12_footprints():
    parts, _ = r12.model()
    return {ref: p['footprint'].split(':')[1] for ref, p in parts.items()}


def generated():
    r12.source_check()
    new = footprints()
    files = {SYMLIB: symbol_library()}
    for name, text in new.items():
        files[PRETTY / (name + '.kicad_mod')] = text
    for name in MODELS:
        files[SHAPES / name] = model_text(name)
    copied = {}
    pinned = json.loads((r12.INPUT / 'manifest.json').read_text())['library']
    r10 = HERE / 'assembly_review/kilib'
    for name in R10_REUSE:
        src = r10 / 'rocket.pretty' / (name + '.kicad_mod')
        copied[PRETTY / src.name] = src
        for model in re.findall(r'\(model "\$\{KIPRJMOD\}/kilib/([^"]+)"', src.read_text()):
            copied[LIB / model] = r10 / model
    for name in sorted(set(r12_footprints().values()) - set(new) - set(R10_REUSE)):
        src = r12.R11 / 'kilib/rocket.pretty' / (name + '.kicad_mod')
        assert str(src.relative_to(r12.ROOT_DIR)) in pinned, f'{name}: not a pinned R11 land'
        copied[PRETTY / src.name] = src
        for model in re.findall(r'\(model "\$\{KIPRJMOD\}/kilib/([^"]+)"', src.read_text()):
            copied[LIB / model] = r12.R11 / 'kilib' / model
    return files, copied


def stale(files, copied):
    out = [p for p, t in files.items() if not p.exists() or p.read_text() != t]
    out += [p for p, s in copied.items() if not p.exists() or p.read_bytes() != s.read_bytes()]
    wanted = set(files) | set(copied)
    out += [p for p in LIB.rglob('*') if p.is_file() and p not in wanted]
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


def single_side_issues(fp, pcbnew):
    """D-R12-01: a top-side land: SMD pads on F.Cu (no B.* layer), or plated / non-plated holes."""
    issues = []
    if fp.GetLayer() != pcbnew.F_Cu:
        issues.append('footprint not on F.Cu')
    for p in fp.Pads():
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            continue
        aperture = not p.IsOnLayer(pcbnew.F_Cu) and p.IsOnLayer(pcbnew.F_Paste)      # a paste-only aperture (no copper)
        if any(p.IsOnLayer(l) for l in (pcbnew.B_Cu, pcbnew.B_Paste, pcbnew.B_Mask)) or not (p.IsOnLayer(pcbnew.F_Cu)
                                                                                           or aperture):
            issues.append(f'pad {p.GetNumber() or "(unnumbered)"} not a top-side SMD pad')
    return issues


def geometry_checks():
    """Parse every R12 land with pcbnew, assert the new lands' source dimensions and the one-side rule."""
    import pcbnew
    mm = pcbnew.ToMM
    result, issues = {}, []
    for name in sorted(set(r12_footprints().values())):
        fp = pcbnew.FootprintLoad(str(PRETTY), name)
        assert fp is not None, name
        issues += [f'{name}: {i}' for i in single_side_issues(fp, pcbnew)]
        result[name] = {p.GetNumber() or f'tab{i}': [round(mm(p.GetFPRelativePosition().x), 4),
                                                     round(mm(p.GetFPRelativePosition().y), 4),
                                                     round(mm(p.GetSize().x), 4), round(mm(p.GetSize().y), 4)]
                        for i, p in enumerate(fp.Pads())}
        for model in fp.Models():
            assert model.m_Filename.startswith('${KIPRJMOD}/kilib/'), (name, model.m_Filename)
            assert (LIB / model.m_Filename.split('/kilib/', 1)[1]).exists(), (name, model.m_Filename)
    assert not issues, issues
    for n, c in GHC.items():
        pads = result[c['name']]
        sig = [pads[str(i)] for i in range(1, n + 1)]
        tabs = [v for k, v in pads.items() if k.startswith('tab')]
        assert len(pads) == n + 2 and len(tabs) == 2
        assert all(round(b[0] - a[0], 4) == GHC_PITCH and a[2:] == [GHC_W, GHC_L] and a[1] == c['y_sig']
                   for a, b in zip(sig, sig[1:]))
        assert sorted(abs(t[0]) for t in tabs) == [c['tab'][0]] * 2 and all(t[2:] == list(c['tab'][2:]) for t in tabs)
    fx = result['M3_FXLS_HLQFN16']
    assert fx == {n: [x, y, w, h] for n, x, y, w, h in FX_PADS}
    assert len(fx) == 17 and fx['1'] == [-1.975, -1.2, .85, .5] and fx['17'] == [0, 0, 2.6, 2.6]
    buz = result['M3_BUZ_TH_D9_P4']
    assert buz == {'1': [-2.0, 0, 1.8, 1.8], '2': [2.0, 0, 1.8, 1.8]}
    ddc = result['M3_TSOT23_6_DDC']
    assert ddc == {n: [x, y, w, h] for n, x, y, w, h in DDC_PADS}
    sot6 = result['SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL']       # LMR50410 DBV: JLCEDA C2841056 0.532 x 1.072 at +/-1.149
    assert all(abs(abs(v[1]) - 1.149) < .002 and v[2:] == [.532, 1.072] for v in sot6.values())
    xtal = result['CRYSTAL-SMD_4P-L3.2-W2.5-BL']             # YXC YSX321SL suggested layout: 1.4 x 1.2, 0.8 / 0.5 gaps
    assert all(abs(abs(v[0]) - 1.1) < 1e-6 and abs(abs(v[1]) - .85) < 1e-6 and v[2:] == [1.4, 1.2] for v in xtal.values())
    bga = result['M3_TFBGA100_8x8_P0.8']
    assert len(bga) == 100 and bga['A1'] == [-3.6, -3.6, .4, .4]
    return result


# ---------------------------------------------------------------------------------------------------------------------
# JLC stock and cost (network)

BOARDS = (2, 5)
# JLC fees, https://jlcpcb.com/help/article/pcb-assembly-price ("updated Oct 22, 2026", read by the cost study
# 2026-11-04): Economic setup $8.18 + stencil $1.53 per order, $3.07 feeder fee per unique Extended code (Basic free;
# Preferred Extended free on Economic is an Inference from https://jlcpcb.com/solutions/pcb-prototype-assembly, so both
# counts are reported), $0.0016 per SMT joint. Bare board: 4L 46 x 100 mm ENIG 0.5 oz inner, 5 pcs $25.10 (cost study
# section 2.1, live quote 2026-11-04; the 2-board order still buys JLC's 5-board minimum).
ECON_FIXED, FEEDER, JOINT, PCB_5 = 8.18 + 1.53, 3.07, 0.0016, 25.10


def bom_lines():
    """[(code, refs, owner_fit, joints per board)] of the R12 model (parts with an LCSC code)."""
    import pcbnew  # noqa: F401  (pad counts come from the lands)
    data = r12.circuit()
    parts, _ = r12.model(data)
    pads = {}
    for name in set(p['footprint'].split(':')[1] for p in parts.values()):
        fp = pcbnew.FootprintLoad(str(PRETTY), name)
        pads[name] = sum(1 for p in fp.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH)
    lines = {}
    for ref, p in parts.items():
        code = p['fields'].get('LCSC')
        if not code or 'exclude_from_bom' in p['flags']:
            continue
        line = lines.setdefault(code, dict(refs=[], owner=False, joints=0))
        line['refs'].append(ref)
        line['owner'] = ref in data['owner_fit']
        line['joints'] += pads[p['footprint'].split(':')[1]]
    return lines


def stock():
    sys.path.insert(0, str(r12.ROOT_DIR / 'tools'))
    import jlc_stock
    import jlc_cost
    lines = bom_lines()
    rows, failures = {}, []
    for code in sorted(lines):
        item = jlc_stock.lookup(code)
        s, presale, available = jlc_stock.orderable(item)
        need = len(lines[code]['refs']) * max(BOARDS)
        minimum, purchase = jlc_stock.purchase_quantity(item, need) if item else (None, need)
        rows[code] = dict(refs=sorted(lines[code]['refs'], key=r12.natural), qty_per_board=len(lines[code]['refs']),
                          owner_fit=lines[code]['owner'], joints_per_board=lines[code]['joints'],
                          stockCount=s, canPresaleNumber=presale, orderable=available, min_purchase=minimum,
                          library_type=item.get('componentLibraryType'), preferred=item.get('preferredComponentFlag'),
                          jlc_model=item.get('componentModelEn'), jlc_brand=item.get('componentBrandEn'),
                          prices=item.get('componentPrices'))
        if not item or available is None or available < purchase:
            failures.append(f'{code} ({",".join(rows[code]["refs"])}): orderable {available} < {purchase} for '
                            f'{max(BOARDS)} boards')
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    STOCK.write_text(json.dumps(dict(checked_utc=now, source=jlc_stock.API, boards=max(BOARDS),
                                     rule='orderable = min(stockCount, canPresaleNumber) (R20-BOM-01, Inference)',
                                     parts=rows, failures=failures), indent=1, ensure_ascii=False) + '\n')
    cost = dict(checked_utc=now, tier='JLC Economic PCBA, one side', basis=dict(
        fixed_usd=ECON_FIXED, feeder_usd_per_extended_code=FEEDER, joint_usd=JOINT, pcb_5pcs_usd=PCB_5,
        source='https://jlcpcb.com/help/article/pcb-assembly-price (cost study 2026-11-04); PCB quote: cost_study.md 2.1',
        excluded='shipping, tax, attrition, owner hand-fit (C84, LS120), C84 / LS120 bought from LCSC by the owner'),
        orders={})
    for boards in BOARDS:
        parts_usd = owner_usd = 0.0
        ext, pref, joints = [], [], 0
        for code, r in rows.items():
            qty = r['qty_per_board'] * boards
            order_qty = max(qty, r['min_purchase'] or 1)
            price = jlc_cost.unit_price({'componentPrices': r['prices']}, order_qty) or 0.0
            if r['owner_fit']:
                owner_usd += price * order_qty
                continue
            parts_usd += price * order_qty
            joints += r['joints_per_board'] * boards
            if r['library_type'] == 'expand':
                (pref if r['preferred'] else ext).append(code)
        feeder_strict = FEEDER * (len(ext) + len(pref))
        feeder_pref_free = FEEDER * len(ext)
        total = parts_usd + feeder_strict + ECON_FIXED + joints * JOINT + PCB_5
        cost['orders'][str(boards)] = dict(
            jlc_parts_usd=round(parts_usd, 2), extended_codes=len(ext), preferred_extended_codes=len(pref),
            feeder_usd=round(feeder_strict, 2), feeder_usd_if_preferred_free=round(feeder_pref_free, 2),
            fixed_usd=ECON_FIXED, smt_joints=joints, joints_usd=round(joints * JOINT, 2), pcb_usd=PCB_5,
            owner_parts_usd=round(owner_usd, 2), total_usd=round(total, 2),
            total_usd_if_preferred_free=round(total - feeder_strict + feeder_pref_free, 2),
            per_board_usd=round(total / boards, 2),
            m3_metric_per_board_usd=round((parts_usd + feeder_strict) / boards, 2))
    COST.write_text(json.dumps(cost, indent=1) + '\n')
    print(f'JLC: {len(rows)} codes, {len(failures)} stock failures -> {STOCK.name}; cost -> {COST.name}')
    for f in failures:
        print('  ', f)
    for b, o in cost['orders'].items():
        print(f'  {b} boards: total ${o["total_usd"]} (${o["total_usd_if_preferred_free"]} if preferred is free), '
              f'parts ${o["jlc_parts_usd"]}, {o["extended_codes"]}+{o["preferred_extended_codes"]} extended codes')
    return 0


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
        print('r12_parts: stale:', ', '.join(str(p.relative_to(LIB)) for p in old))
        return 1
    if args.library_only:
        write(files, copied)
    rows = geometry_checks()
    print(f'r12_parts: {len(rows)} footprints parsed (all top-side), {len(files) + len(copied)} library files current')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
