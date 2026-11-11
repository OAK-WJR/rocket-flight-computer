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
SwitchGH4, PortSH4, PortSH6) and every used symbol's ki_fp_filters set to exactly the R12 footprints it carries (ERC
footprint_filter).
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
# R12F5-TRI-06: drawn as plain rectangles, the corner lands of two sides meet corner to corner at sqrt(0.1^2 + 0.1^2) =
# 0.141 mm (U6.4 / .5, .8 / .9, .12 / .13, .16 / .1), under JLC's 0.15 mm SMD pad-to-pad (different nets), with a 0.041 mm
# mask web at the 0.05 mm margin (JLC soldermask bridge 0.10 mm; https://jlcpcb.com/capabilities/pcb-capabilities, read
# 2026-11-06 by the round 5 mfg lens). NXP's own land is not plain: Figures 110 / 111 (same sheet) draw those eight lands
# and their mask openings with the corner that faces the other side cut at 45 degrees; Figure 104 (98ASA00761D rev F,
# package outline) marks "(8X 0.143)" at the eight corner terminals, read here as their own corner cut (Inference). The
# land cut is not dimensioned; it scales to about 0.14 mm on Figure 111 (Inference), so R12 cuts 0.143 mm. Size and position stay NXP's
# (0.5 x 0.85 at 1.975). Corner gap 0.141 + 2 x 0.143 / sqrt(2) = 0.344 mm, mask web 0.344 - 2 x 0.05 = 0.244 mm
# (Calculation); the cut removes 0.0102 mm2 (2.4 %) of each 0.425 mm2 land, where the terminal is cut too (Figure 104:
# terminals 0.35-0.45 x 0.40-0.50 mm).
FX_CHAMFER = 0.143
FX_CHAMFER_AT = {'1': 'top_right', '4': 'bottom_right', '5': 'top_left', '8': 'top_right', '9': 'bottom_left',
                 '12': 'top_left', '13': 'bottom_right', '16': 'bottom_left'}


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
        pad = _rpad(num, x, y, w, hh, shape='roundrect' if num in FX_CHAMFER_AT else 'rect')
        extra = '\t\t(solder_mask_margin 0.05)\n' + ('\t\t(solder_paste_margin -0.3)\n' if num == '17' else '')
        if num in FX_CHAMFER_AT:
            extra += (f'\t\t(roundrect_rratio 0)\n\t\t(chamfer_ratio {g(FX_CHAMFER / min(w, hh))})\n'
                      f'\t\t(chamfer {FX_CHAMFER_AT[num]})\n')
        body += pad[:-2] + '\n' + extra.rstrip('\n') + ')\n'
    return name, make_fp(name, 'NXP FXLS90322 HLQFN-16 4 x 4 mm, 0.8 mm pitch (SOT1688-1(SC)); land FXLS9xxx0 Rev 6 '
                         'Figure 110 / 111; pins Figure 9; top side only', body, -h - 1.0, name + '.wrl')


# QMB-09B-03 9 mm passive magnetic buzzer, THT (D-R12-16): Huawha product specification QMB-09B-03 (2019-12-3, LCSC
# C96256 PDF) item 4 dimension drawing: body 9.0 x 5.5 mm, two 0.6 +/- 0.05 mm pins at 4.0 mm, (+) and (-) marked. Land
# JLCEDA C96256 "BUZ-TH_BD9.0-P4.00-D0.6-FD": 1.0 mm finished hole, 1.8 mm pad, 4.0 mm pitch; pin 1 (+): JLCEDA's
# footprint prints its '+' beside pad 1 (read 2026-11-05) and the maker drawing marks the (+) lead. JLC THT assembly
# (hand-soldered after reflow, D-R12-85): no paste; the CPL puts JLCEDA's pad 1 on ours (jlc_orient_r12).
BUZ_PITCH, BUZ_HOLE, BUZ_PAD, BUZ_D, BUZ_H = 4.0, 1.0, 1.8, 9.0, 5.5


def buzzer():
    name = 'M3_BUZ_TH_D9_P4'
    body = _circle((0, 0), BUZ_D / 2, 'F.Fab', .1) + _circle((0, 0), BUZ_D / 2 + .25, 'F.CrtYd', .05)
    body += _line((-2.0, -2.2), (-2.0, -1.4), 'F.SilkS', .15) + _line((-2.4, -1.8), (-1.6, -1.8), 'F.SilkS', .15)
    # D-R12-82: the polarity on F.Fab as R10's LS120 land carries it (check_r10.FAB_TEXT_ALLOWED: '+' / '-'), so the
    # assembly drawing shows which hole takes the (+) lead (pin 1 = (+), JLCEDA's '+' at pad 1, D-R12-85)
    body += ''.join(f'\t(fp_text user "{t}" (at {g(x)} 1.6) (layer "F.Fab") (effects (font (size 0.8 0.8) '
                    f'(thickness 0.10))))\n' for t, x in (('+', -BUZ_PITCH / 2), ('-', BUZ_PITCH / 2)))
    for num, x in (('1', -BUZ_PITCH / 2), ('2', BUZ_PITCH / 2)):
        body += (f'\t(pad "{num}" thru_hole {"rect" if num == "1" else "circle"}\n\t\t(at {g(x)} 0)\n'
                 f'\t\t(size {g(BUZ_PAD)} {g(BUZ_PAD)})\n\t\t(drill {g(BUZ_HOLE)})\n\t\t(layers "*.Cu" "*.Mask")\n'
                 '\t\t(remove_unused_layers yes)\n\t\t(keep_end_layers yes))\n')
    return name, make_fp(name, 'Huawha QMB-09B-03 9 mm THT buzzer, pins 4.0 mm, hole 1.0 mm, pad 1.8 mm; land JLCEDA '
                         'C96256; JLC THT assembly (no paste)', body, -5.6, name + '.wrl', attr='through_hole')


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


# D-R12-174 (owner, 2026-11-10: "replace the battery solder pads with screw terminals"; supersedes D-R12-30's wire
# pads): J1 is a Cixi Kefa KF301-5.0-2P (LCSC C474881, blue), a 5.0 mm two-position rising-cage screw terminal, JLC THT
# assembly (hand-soldered, as J121 and LS120, D-R12-85). Kefa drawing KF301-5.0 rev A (2021-03-13; LCSC C474881 PDF,
# https://datasheet.lcsc.com/datasheet/pdf/dbe48a1bef5e997cc12dba31bc0ac67e.pdf?productCode=C474881): pitch 5.0, body
# P x 5.0 = 10.0 wide, 7.60 deep, 10.0 tall; pins dia 1.00, 3.60 +/- 0.30 below the seating plane, 4.0 from the rear
# face (3.60 from the wire face: 7.60 - 4.0); PCB hole dia 1.20 +0.10 / -0 ("PCB LAYOUT"; "PCB Hole Diameter 1.2");
# a 0.67 mm interlock key on one end, 0.6-1.6 mm from the rear face (scaled from the top view: Inference); UL 16 A /
# 300 V, IEC 17 A; wire 22-14 AWG, 1.5 mm2; strip 4-5 mm; M2.5 screw, 0.4 N m maximum; -30 to +120 C (Datasheet).
# Wire face: the front view (wire cages) and the right side view in third-angle projection put the wire face 3.60 mm
# from the pin row (Inference from the projection, the pin's 4.0 mm being dimensioned to the opposite face); the wire
# hole is centred about 2.9 mm above the seating plane (scaled from the front view: Inference).
# Land: finished hole 1.30 mm (the maker's 1.20 +0.10 maximum; the pin is 1.00), land 2.60 mm (0.65 mm ring), 5.00 mm
# pitch. Local frame: pin 1 at -x, the wire face at -y (rotation 90 puts it at the board's west edge), so the key
# (the right end seen from the wire face) is at -x. Envelopes are maximum-tolerance unions (the drawing's GB/T 14486
# table: +/-0.20 to 6 mm, +/-0.30 over 6 to 10 mm), as R10's DB125 (T0-1 p1): wire face -3.80, rear +4.20, ends
# +/-5.15, key to -6.02 over local y 2.2-3.8, height 10.30 (key 6.95), pin tail 3.90 below the seating plane.
KF_PITCH, KF_HOLE, KF_PAD = 5.00, 1.30, 2.60
KF_FRONT, KF_REAR, KF_END, KF_H = -3.80, 4.20, 5.15, 10.30
KF_KEY = (-6.02, 2.2, -KF_END, 3.8, 6.95)        # x0, y0, x1, y1, height of the interlock key
KF_TAIL = 3.90


def kf301():
    name = 'M3_KF301_5P0_2P_BU'
    x = KF_PITCH / 2
    body = _rect((-5.0, -3.6), (5.0, 4.0), 'F.Fab', .1)                            # nominal body
    body += _line((-1.0, -3.6), (-1.0, -5.0), 'F.Fab', .1) + _line((1.0, -3.6), (1.0, -5.0), 'F.Fab', .1)  # wire face
    k0, ky0, k1, ky1, _ = KF_KEY
    pts = ((-KF_END, KF_FRONT), (KF_END, KF_FRONT), (KF_END, KF_REAR), (-KF_END, KF_REAR), (-KF_END, ky1), (k0, ky1),
           (k0, ky0), (-KF_END, ky0))
    body += ('\t(fp_poly\n\t\t(pts\n' + ''.join(f'\t\t\t(xy {g(a)} {g(b)})\n' for a, b in pts) +
             '\t\t)\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type solid))\n\t\t(fill no)\n\t\t(layer "F.CrtYd"))\n')
    body += _rect((-5.15, -3.75), (5.15, 4.15), 'F.SilkS', .15)
    for num, px in (('1', -x), ('2', x)):
        body += (f'\t(pad "{num}" thru_hole circle\n\t\t(at {g(px)} 0)\n\t\t(size {g(KF_PAD)} {g(KF_PAD)})\n'
                 f'\t\t(drill {g(KF_HOLE)})\n\t\t(layers "*.Cu" "*.Mask")\n'
                 '\t\t(remove_unused_layers yes)\n\t\t(keep_end_layers yes))\n')
    return name, make_fp(name, 'Cixi Kefa KF301-5.0-2P (C474881) 5.0 mm 2P screw terminal, blue; hole 1.30 mm (maker 1.20 '
                         '+0.10), land 2.60 mm; pin 1 at -x; wire face -y; JLC THT assembly (no paste) (D-R12-174)',
                         body, 5.3, name + '.wrl', attr='through_hole')


R10_REUSE = ('M3_DB125_2P_BK',)       # D-R12-29: R10's verified DB125-2 (black) land and model, copied verbatim

# R12-only text overrides of copied R11 lands (R12F4-TRI-06): the copy is pinned byte for byte to R11's kilib, so a
# correction that belongs to R12 alone is a (old, new) substitution applied to the pinned source text. R10's and R11's
# copies are not touched. M3_R2512_UR: R11's descr names 25121WF330LT4E / C25468 (0.33 ohm); R12's R166 is
# 25121WF360LT4E / C168925, 0.36 ohm 1 % 2512 (its Value, LCSC and Manufacturer Part fields and the JLC BOM). Copper,
# courtyard and model are unchanged.
R11_TEXT_OVERRIDES = {
    'M3_R2512_UR': (' R166 (25121WF330LT4E, LCSC C25468)")',
                    ' R166 (25121WF360LT4E, LCSC C168925, 0.36 ohm 1 %; R12 override of the R11 land text)")'),
}


# C84 hold-up capacitor, JLC-placed (D-R12-85, owner 2026-11-05: every part JLC-assembled): Honor Elec HV1E477M0810PZ
# (C5246546), 470 uF 25 V conductive polymer, D8 x L10.5 mm. Honor CDHV specification (LCSC C5246546 PDF): dimension
# table 8 x 10.5: A = B 8.3, C 2.9, P 3.1, W 0.8-1.1 mm, L 10.5; item 14 lead-free reflow: peak 255 C for 5 s, 230-255 C
# <= 30 s (Datasheet). The copper is R11's M3_MA_8x10 land unchanged (3.5 x 1.7 mm pads at +/-3.25 mm: the same 8.3 mm
# base and 3.1 mm terminal gap, Datasheet for both makers), so C84's copper and routing do not move; JLCEDA's land for
# C5246546 ("CAP-SMD_BD8.0-L8.3-W8.3-LS9.3-FD-2", 4.0 x 1.6 mm at +/-3.5 mm, read 2026-11-05) matches it within
# jlc_orient's two-pad tolerance. Pad 1 is the anode (+), as JLCEDA's pad 1. Paste on both pads (JLC reflow).
CAP_D8_PAD, CAP_D8_X, CAP_D8_BASE = (3.5, 1.7), 3.25, 8.3


def cap_d8():
    name = 'M3_CAP_D8_SMD'
    h = CAP_D8_BASE / 2
    body = _rect((-h, -h), (h, h), 'F.Fab', .1) + _circle((0, 0), 4.0, 'F.Fab', .1)
    body += _rect((-5.25, -4.5), (5.25, 4.5), 'F.CrtYd', .05)
    body += _line((-4.5, -2.2), (-4.5, -1.2), 'F.SilkS', .15) + _line((-5.0, -1.7), (-4.0, -1.7), 'F.SilkS', .15)
    body += _rpad('1', -CAP_D8_X, 0, *CAP_D8_PAD) + _rpad('2', CAP_D8_X, 0, *CAP_D8_PAD)
    return name, make_fp(name, 'Honor Elec HV1E477M0810PZ 470 uF 25 V polymer, D8 x 10.5 mm; pad 1 (+) left; R11 M3_MA_8x10 '
                         'copper with paste (JLC-placed, D-R12-85)', body, -5.4, name + '.wrl')


# J430 push-pull microSD (round 9 lane L, owner decision 2026-11-07: replaces the Molex 472192001 hinge): Molex
# 104031-0811 (LCSC C585350), 1.42 mm, shielded push-pull, 8 contacts at 1.10 mm, card-detect switch. Land, outline and
# card from Molex sales drawing SD-104031-001 rev B2 sheet 1 (the LCSC copy for C585350,
# https://datasheet.lcsc.com/datasheet/pdf/541e9f28cb856b9ee4390625509ae3af.pdf?productCode=C585350; series brief
# https://static.chipdip.ru/lib/615/DOC034615058.pdf), "RECOMMENDED PCB LAYOUT" (tolerance +/-0.05), read at 600 dpi:
# x from the socket centre, D from the product line (the card mouth, where the contact tails are) into the body.
#   contacts 1-7: 0.85 x 1.1 mm, pin 1 centre x +3.105, pitch 1.10 ("7-1.1"), D -0.30 ... +0.80 ("8-1.1", "0.3");
#   contact 8: 0.75 wide, x -4.92 ... -4.17 ("0.75", "4.17"), 0.25 mm from contact 7 and from G2;
#   G1 x 4.79 ... 6.34 (1.55), D -0.30 ... 1.05 (1.35); G2 x -6.34 ... -5.17 ("1.17", "5.17"), D -0.30 ... 1.50 ("1.8");
#   G3 / G4 1.90 x 1.35 at x -4.68 ... -2.78 / 1.29 ... 3.19 ("2-1.9", "2.78", "1.29"), D 10.40 ... 11.75 ("10.4",
#   "2-1.35"); card-detect switch pads 1.20 x 1.00 at x 5.14 ... 6.34 ("2-5.14", "2-1.2"), D 5.90 ... 6.90 and
#   9.60 ... 10.60 ("5.9", "9.6", "2-1.0"). G1 ... G4 are the ground (shell) pattern.
# Body 11.95 x 11.40 mm, 1.42 mm high (sheet 1 top / front views); the inserted card (11.0 mm wide, centred 0.095 mm
# toward contact 8) reaches 4.0 +/- 0.2 mm beyond the product line, its underside 0.62 +/- 0.20 mm and its top
# 1.57 +/- 0.20 mm above the board (side view). Pin map (sheet 1 table): 1 DAT2, 2 CD/DAT3, 3 CMD, 4 VDD, 5 CLK, 6 VSS,
# 7 DAT0, 8 DAT1. JLCEDA's C585350 land (read 2026-11-08) has the same shell and switch pads and 0.7 x 1.2 mm contacts
# at a uniform 1.1 mm pitch (its contacts 1-7 sit 0.05 mm from the maker's); the maker's land is used.
# KiCad frame: footprint origin at the socket centre, the product line (mouth) at local y = +5.70, so local
# y = 5.70 - D; pads numbered as JLCEDA's C585350 land "SIM-SMD_8P-1040310811" (read 2026-11-08), so JLC's CPL
# matches pad for pad: 1-8 the contacts, 9 G2, 10 G1, 11 the D 5.9-6.9 switch pad, 12 the D 9.6-10.6 switch pad,
# 13 G4, 14 G3; the switch (11-12) is not connected (round 9 lane L). Reflow rating: not on the drawing or the brief
# (UNVERIFIED; that it takes JLC's 255 C profile is an Inference, as for 472192001).
SD_MOUTH = 5.70


def _sd_y(d0, d1):
    return round(SD_MOUTH - (d0 + d1) / 2, 4), round(d1 - d0, 4)


SD_PADS = tuple((str(n), round(3.105 - 1.1 * (n - 1), 4), *_sd_y(-0.30, 0.80), 0.85) for n in range(1, 8)) + (
    ('8', -4.545, *_sd_y(-0.30, 0.80), 0.75),
    ('9', -5.755, *_sd_y(-0.30, 1.50), 1.17),       # G2
    ('10', 5.565, *_sd_y(-0.30, 1.05), 1.55),       # G1
    ('11', 5.74, *_sd_y(5.90, 6.90), 1.20),         # card-detect switch
    ('12', 5.74, *_sd_y(9.60, 10.60), 1.20),
    ('13', 2.24, *_sd_y(10.40, 11.75), 1.90),       # G4
    ('14', -3.73, *_sd_y(10.40, 11.75), 1.90),      # G3
)
SD_BODY = (-5.975, -5.70, 5.975, 5.70)
SD_CARD = (-5.595, SD_MOUTH, 5.405, SD_MOUTH + 4.0)       # card beyond the mouth, nominal
SD_CARD_TOL, SD_CARD_TOP, SD_BODY_H = 0.2, 1.57 + 0.20, 1.42


def sd_pads():
    """[(num, x, y, w, h)] in the footprint frame."""
    return [(n, x, y, w, h) for n, x, y, h, w in SD_PADS]


def microsd():
    name = 'M3_MICROSD_MOLEX_104031'
    pads = sd_pads()
    body = _rect(SD_BODY[:2], SD_BODY[2:], 'F.Fab', .1)
    cx0, cy0, cx1, cy1 = SD_CARD
    body += (_line((cx0, cy0), (cx0, cy1), 'F.Fab', .1) + _line((cx0, cy1), (cx1, cy1), 'F.Fab', .1)
             + _line((cx1, cy1), (cx1, cy0), 'F.Fab', .1))
    # courtyard 0.25 mm round the body and lands, following the body's back edge (y -5.95) except where G3 / G4 reach
    # 0.35 mm past it (y -6.30), so the VCAP caps west of the socket keep their places (round 9 lane L)
    ext = _pad_extents(pads)
    x0, x1 = min(p[0] for p in ext) - .25, max(p[0] for p in ext) + .25
    y1 = max(max(p[1] for p in ext), SD_BODY[3]) + .25
    yb, yg = SD_BODY[1] - .25, min(p[1] for p in ext) - .25
    g3 = [p for n, *p in pads if n == '14'][0]
    g4 = [p for n, *p in pads if n == '13'][0]
    poly = [(x0, yb)]
    for x, _, w, _ in (g3, g4):
        poly += [(x - w / 2 - .25, yb), (x - w / 2 - .25, yg), (x + w / 2 + .25, yg), (x + w / 2 + .25, yb)]
    poly += [(x1, yb), (x1, y1), (x0, y1)]
    poly = [(round(x, 4), round(y, 4)) for x, y in poly]
    body += ''.join(_line(a, b, 'F.CrtYd', .05) for a, b in zip(poly, poly[1:] + poly[:1]))
    body += _circle((3.105, 6.55), .12, 'F.SilkS', .15)        # contact 1, outside the land, on the card side
    for num, x, y, w, h in pads:
        body += _rpad(num, x, y, w, h)
    return name, make_fp(name, 'Molex 104031-0811 push-pull microSD, 1.42 mm, card-detect switch (C585350); land, body '
                         'and card from Molex SD-104031-001 sheet 1; contacts 1-8, shell 9 G2 / 10 G1 / 13 G4 / 14 G3, '
                         'switch 11-12 (JLCEDA numbering); mouth (product line) at local +y; top side only', body, -6.9,
                         name + '.wrl')


def footprints():
    out = {}
    for maker in (lambda: ghc(4), lambda: ghc(6), fxls, buzzer, ddc6, kf301, cap_d8, microsd):
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
    # D-R12-174: KF301-5.0-2P maximum-tolerance union (body 10.30 x 8.00 x 10.30 mm about local y 0.2, key 0.87 x 1.6 x
    # 6.95 mm at -x); fit_check reads the box (R12-GATE-01 envelope KF301_BOX)
    'M3_KF301_5P0_2P_BU.wrl': ('# KF301-5.0-2P envelope, Kefa KF301-5.0 drawing rev A maxima (D-R12-174). NOT a maker '
                               'model.\n',
                               [(0, (KF_FRONT + KF_REAR) / 2, 0, 2 * KF_END, KF_REAR - KF_FRONT, KF_H, '.15 .35 .75'),
                                ((KF_KEY[0] + KF_KEY[2]) / 2, (KF_KEY[1] + KF_KEY[3]) / 2, 0, KF_KEY[2] - KF_KEY[0],
                                 KF_KEY[3] - KF_KEY[1], KF_KEY[4], '.15 .35 .75')]),
    # base 8.3 + 0.2, height 10.5 + 0.5 + 0.3 mm (R10's M3_MA_8x10 allowances applied to the Honor L 10.5; Inference)
    'M3_CAP_D8_SMD.wrl': ('# HV1E477M0810PZ envelope 8.5 x 8.5 x 11.3 mm (Honor CDHV dimension table, R10 allowances). NOT a '
                          'maker model.\n', [(0, 0, 0, 8.5, 8.5, 11.3, GREY)]),
    # body 11.95 x 11.40 x 1.42 mm (Molex SD-104031-001 sheet 1); the inserted card is fit_check's mated envelope
    'M3_MICROSD_MOLEX_104031.wrl': ('# Molex 104031-0811 envelope 11.95 x 11.40 x 1.42 mm (SD-104031-001). NOT a maker '
                                    'model.\n', [(0, 0, 0, SD_BODY[2] - SD_BODY[0], SD_BODY[3] - SD_BODY[1], SD_BODY_H,
                                                  GREY)]),
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
    ('ServoGH6', 'J', 'Megastar ZX-SH1.0-6PWT SH-1.0 clone (C7430448) 6-pin servo port (D-R12-31): 1-4 SERVO1-4, 5 GND, '
     '6 unused', 'connector servo',
     7.62, 7.62, [P(6.35, '1', 'SERVO1'), P(3.81, '2', 'SERVO2'), P(1.27, '3', 'SERVO3'), P(-1.27, '4', 'SERVO4'),
                  P(-3.81, '5', 'GND'), P(-6.35, '6', 'NC')], []),
    ('SwitchGH4', 'J', 'Megastar ZX-SH1.0-4PWT SH-1.0 clone (C7430446) 4-pin external switch port (D-R12-31): '
     '1 SW SOURCE, 2 SW RETURN, 3-4 unused',
     'connector switch', 7.62, 5.08, [P(3.81, '1', 'SW SOURCE'), P(1.27, '2', 'SW RETURN'), P(-1.27, '3', 'NC'),
                                      P(-3.81, '4', 'NC')], []),
    # R12F6-TRI-09: the GPS / radio / AUX ports in D-R12-31's MicoAir H743 order. R11's PortTerminal names pin 1 4V8 and
    # pin 2 GND (R10 / R11's JST order); on R12 pin 1 is GND and pin 2 PORT_4V8, so the ports take their own symbols
    # (r12_sch_check PORT_PIN_NAMES: every pin name agrees with its net).
    ('PortSH4', 'J', 'Megastar ZX-SH1.0-4PWT SH-1.0 clone (C7430446) always-on port (D-R19-14, D-R12-31, MicoAir H743 '
     'order): 1 GND, 2 PORT_4V8, 3 board TXO, 4 board RXI', 'connector port uart', 7.62, 5.08,
     [P(3.81, '1', 'GND'), P(1.27, '2', '4V8'), P(-1.27, '3', 'TXO'), P(-3.81, '4', 'RXI')], []),
    # round 9 lane L: the Molex 104031-0811 push-pull microSD (pins: SD-104031-001 sheet 1 pin map; pad numbers as
    # JLCEDA's C585350 land: shell 9 G2, 10 G1, 13 G4, 14 G3; 11-12 the card-detect switch, not connected)
    ('MicroSD_PushPull', 'J', 'Molex 104031-0811 push-pull microSD with card-detect switch (C585350): 1 DAT2, 2 CD/DAT3 '
     '(CS), 3 CMD (DI), 4 VDD, 5 CLK, 6 VSS, 7 DAT0 (DO), 8 DAT1, shell 9 G2 10 G1 13 G4 14 G3, 11-12 card-detect '
     'switch', 'connector microsd card', 10.16, 10.16,
     [P(8.89, '1', 'DAT2'), P(6.35, '2', 'CD_DAT3_CS'), P(3.81, '3', 'CMD_DI'), P(1.27, '4', 'VDD', 'power_in'),
      P(-1.27, '5', 'CLK'), P(-3.81, '6', 'VSS', 'power_in'), P(-6.35, '7', 'DAT0_DO'), P(-8.89, '8', 'DAT1')],
     [P(8.89, '9', 'G2'), P(6.35, '10', 'G1'), P(3.81, '13', 'G4'), P(1.27, '14', 'G3'), P(-3.81, '11', 'CD_A'),
      P(-6.35, '12', 'CD_B')]),
    ('PortSH6', 'J', 'Megastar ZX-SH1.0-6PWT SH-1.0 clone (C7430448) always-on GPS port (D-R19-14, D-R12-31, MicoAir H743 '
     'GPS order): 1 GND, 2 PORT_4V8, 3 board TXO, 4 board RXI, 5-6 unused (the H743\'s I2C pins, NC on R12)',
     'connector port uart gps', 7.62, 7.62,
     [P(6.35, '1', 'GND'), P(3.81, '2', '4V8'), P(1.27, '3', 'TXO'), P(-1.27, '4', 'RXI'), P(-3.81, '5', 'NC'),
      P(-6.35, '6', 'NC')], []),
)
TEXTS = {   # symbol: (R11 Description, R12 Description); R11's PortTerminal is no longer used (R12F6-TRI-09)
    'CameraGH6': ('JST SM06B-GHS-TB camera port (D-R11-05): 1-2 CAM_5V, 3-4 GND, 5 board RX (camera TX), 6 board TX '
                  '(camera RX)',
                  'Megastar ZX-SH1.0-6PWT SH-1.0 clone (C7430448) camera port (D-R12-31): 1-2 CAM_5V, 3-4 GND, 5 board '
                  'RX (camera TX), 6 board TX (camera RX)'),
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
        if name in R11_TEXT_OVERRIDES:
            before, after = R11_TEXT_OVERRIDES[name]
            text = src.read_text()
            assert text.count(before) == 1, f'{name}: override text not found once in the pinned R11 land'
            files[PRETTY / src.name] = text.replace(before, after)
        else:
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
    # R12F5-TRI-06: chamfered corner lands keep >= 0.2 mm corner to corner (JLC 0.15 mm pad to pad, 0.10 mm mask web)
    fx_text = (LIB / 'rocket.pretty/M3_FXLS_HLQFN16.kicad_mod').read_text()
    assert len(re.findall(r'\(chamfer (top|bottom)_(left|right)\)', fx_text)) == len(FX_CHAMFER_AT) == 8
    assert math.sqrt(2) * (FX_C - FX_L / 2 - 1.2 - FX_W / 2 + FX_CHAMFER) >= 0.2
    kf = result['M3_KF301_5P0_2P_BU']                  # D-R12-174: KF301 pins at 5.0 mm, 1.30 mm hole (maker 1.20 +0.10)
    assert kf == {'1': [-2.5, 0, KF_PAD, KF_PAD], '2': [2.5, 0, KF_PAD, KF_PAD]}
    kf_fp = pcbnew.FootprintLoad(str(PRETTY), 'M3_KF301_5P0_2P_BU')
    assert all(abs(mm(p.GetDrillSize().x) - KF_HOLE) < 1e-6 and 1.20 <= KF_HOLE <= 1.30 for p in kf_fp.Pads())
    buz = result['M3_BUZ_TH_D9_P4']
    assert buz == {'1': [-2.0, 0, 1.8, 1.8], '2': [2.0, 0, 1.8, 1.8]}
    ddc = result['M3_TSOT23_6_DDC']
    assert ddc == {n: [x, y, w, h] for n, x, y, w, h in DDC_PADS}
    sot6 = result['SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL']       # LMR50410 DBV: JLCEDA C2841056 0.532 x 1.072 at +/-1.149
    assert all(abs(abs(v[1]) - 1.149) < .002 and v[2:] == [.532, 1.072] for v in sot6.values())
    xtal = result['CRYSTAL-SMD_4P-L3.2-W2.5-BL']             # YXC YSX321SL suggested layout: 1.4 x 1.2, 0.8 / 0.5 gaps
    assert all(abs(abs(v[0]) - 1.1) < 1e-6 and abs(abs(v[1]) - .85) < 1e-6 and v[2:] == [1.4, 1.2] for v in xtal.values())
    sd = result['M3_MICROSD_MOLEX_104031']             # round 9 lane L: Molex SD-104031-001 land
    assert sd == {n: [x, y, w, h] for n, x, y, w, h in sd_pads()} and len(sd) == 14
    assert sd['1'][:2] == [3.105, 5.45] and sd['8'] == [-4.545, 5.45, .75, 1.1] and sd['10'][2:] == [1.55, 1.35]
    assert all(round(sd[str(n)][0] - sd[str(n + 1)][0], 4) == 1.1 for n in range(1, 7))
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
        excluded='shipping, tax, attrition; THT hand-soldering ($0.0164 per joint + $3.58 per order, J121 and LS120) is '
                 'counted in stageD.md, not here; no owner-fitted parts since D-R12-85'),
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
