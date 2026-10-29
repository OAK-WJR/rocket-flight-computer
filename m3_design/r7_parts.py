#!/usr/bin/env python3
"""M3-ASSY-R7 part library for the on-board GNSS and telemetry radio (REQUIREMENTS F10).

usage: <KiCad python3> m3_design/r7_parts.py          build (idempotent) and check
       <KiCad python3> m3_design/r7_parts.py --check  check only; exit 1 when a file would change

Run before m3_design/r7_sch.py. Never edits the board or a schematic. It writes:
  kilib/rocket.pretty/   M3_MAX_F10S_LCC18, M3_E22_900MM22S, M3_SMA_KH_KE8_EDGE, M3_TSLP_2_20,
                         M3_LQG15_0402, M3_BLM18K_0603, C0402_DNP (C0402 without paste, for DNP placeholders)
  kilib/rocket.3dshapes/ one envelope model (VRML boxes, maker maximum dimensions) per footprint;
                         these are fit envelopes, NOT maker STEP models
  kilib/m3.kicad_sym     MAX_F10S, E22_900MM22S, SMA_Edge, ESD_Bidir, PMOS_SOT23, PNP_SOT23, FerriteBead,
                         and M3_LQG15_0402 added to M3:L's footprint filter, C0402_DNP to M3:C's (r7_sch.py
                         refreshes the embedded copies of M3:L and M3:C so ERC's library check stays clean)
  assembly_review/sources/r7_review/r7_parts_check.json
                         every R7 code's land matched against its JLC/EasyEDA footprint in
                         tools/jlc_easyeda/pads.json, the same way tools/jlc_orient.py matches them
                         (pad numbers, rotation 0/90/180/270, bounding-box offset, worst residual)

Land sources (maker drawings; URLs, never PDFs, are recorded):
  MAX-F10S / MAX-M10S  u-blox MAX-F10S integration manual UBXDOC-963802114-12892 R01, Fig. 25 (copper = mask,
                       1.8 mm pads: 1.0 under the module + 0.8 outside, 0.8 mm wide, the four corner pads 0.7 mm,
                       1.1 mm pitch, 9.7 x 10.1 mm outline) and Fig. 26 (T-shaped paste for a 150 um stencil:
                       0.9 mm inside the outline at pad width - 0.2 mm, 1.4 mm outside at pad width; inner span
                       7.9 mm, outer 12.5 mm); MAX-M10S integration manual UBX-20053088 R05 Tables 44-45 give
                       the same numbers. Pinout: MAX-F10S data sheet UBXDOC-963802114-12732 R03 Table 10 and
                       Fig. 2 (pins 1-9 down one side, 10-18 back up the other, counter-clockwise from the top);
                       outline Table 21 (A 10.1 typ / 10.7 max with the 0.6 mm de-paneling tab P, B 9.7 / 9.8,
                       C 2.5 / 2.7 high).
  E22-900MM22S         EBYTE user manual v1.3 ch. 3: 10.0 x 10.0 x 2.5 mm (X.X +/-0.2), 1.27 mm pitch, pin 1
                       2.46 mm from the edge, module pad 0.80 wide x 0.75 deep with a 0.40 mm half hole; no
                       maker land. Land: 0.90 x 1.50 mm (pad + 0.05 per side; 0.80 under the module = pad depth +
                       0.05, 0.70 toe outside for the castellation fillet), identical to JLC/EasyEDA
                       WIRELM-SMD_20P-L10.0-W10.0-P1.27-TL (C5333985). Paste 1:1 (no maker stencil guidance).
  KH-SMA-KE8-G         Kinghelm drawing 2019-08-10 (LCSC C530661): 6.5 mm square flange, 1.5 thick, 8 mm
                       1/4-36UNEF thread (13.5 overall, 9.5 beyond the board edge), four 0.9 mm square legs 4 mm
                       long at 4.2 / 6.0 mm inner / outer spacing (centres +/-2.55), 1.7 mm board slot,
                       centre pin 0.95 mm on the axis 0.45 mm above the top face. Land: 1.2 x 4.2 mm pads from
                       0.2 to 4.4 mm inside the board edge (centre pin top; legs top and bottom), NO paste
                       (hand-fitted in JLC's through-hole step after reflow; pre-tinned bumps would eat the
                       slot play). The BAT WIRELESS BWSMA-KE-P001 (C496550) drawing has the same 6.5 / 4.2 / 6 /
                       2.8 / 1.7 / 4 / 13.5 mm family and fits this land.
  ESD103-B1-02EL       Infineon ESD103-B1-02 series data sheet rev 1.3 (2014-06-12) Fig. 14 TSLP-2-19/-20-FP
                       V01: copper 0.35 x 0.60 mm at 0.65 mm pitch (0.30 mm gap), stencil 0.28 x 0.45 mm (0.38 mm
                       gap). Infineon draws one mask opening round both pads; here each pad has its own opening
                       (0.30 mm web, inside JLC's capability) because the board forbids bridged apertures in
                       footprints (solder_mask_bridge is a DRC error). Package 1.0 x 0.6 x 0.31 mm (v2.0 Fig. 9).
  LQG15HS47NJ02D       Murata JELF243B-0010 sec. 11.1: a 0.4 mm gap, b 1.4-1.5 mm, c 0.5-0.6 mm -> 0.525 x 0.55 mm
                       pads at +/-0.4625 mm; body 1.0 x 0.5 x 0.5 mm (+/-0.05).
  BLM18KG221SN1D       Murata JENF243A-0003 sec. 10-1 (BLM18K, reflow): a 0.7, b 1.8-2.0, c 0.7 mm ->
                       0.6 x 0.7 mm pads at +/-0.65 mm; body 1.6 x 0.8 x 0.8 mm (+/-0.15).
Reused library footprints (land checked here against each new code's EasyEDA footprint): R0402, C0402,
C0603, C0805, R_0603_1608Metric, SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR (AO3401A per AOS; S8550 per the JSCJ
SOT-23 suggested pad layout: 0.6 x 0.8 mm pads, 1.9 mm pitch, 2.02 mm row spacing), M3_TestPad_1.5.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROJECT = HERE / 'assembly_review'
LIB = PROJECT / 'kilib'
PRETTY = LIB / 'rocket.pretty'
SHAPES = LIB / 'rocket.3dshapes'
SYMLIB = LIB / 'm3.kicad_sym'
PADS = ROOT / 'tools/jlc_easyeda/pads.json'
REPORT = PROJECT / 'sources/r7_review/r7_parts_check.json'
GEN = 'm3_r7_parts'


def g(v):
    """Compact millimetre text: 4.75, -0.325, 2 (never 1e-05 or -0)."""
    v = round(v, 6)
    s = f'{v:.6f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


# ---------------------------------------------------------------------------------------------------------
# footprints


def _line(a, b, layer, width):
    return (f'\t(fp_line\n\t\t(start {g(a[0])} {g(a[1])})\n\t\t(end {g(b[0])} {g(b[1])})\n'
            f'\t\t(stroke\n\t\t\t(width {g(width)})\n\t\t\t(type solid))\n\t\t(layer "{layer}"))\n')


def _rect(a, b, layer, width):
    return (f'\t(fp_rect\n\t\t(start {g(a[0])} {g(a[1])})\n\t\t(end {g(b[0])} {g(b[1])})\n'
            f'\t\t(stroke\n\t\t\t(width {g(width)})\n\t\t\t(type solid))\n\t\t(fill none)\n\t\t(layer "{layer}"))\n')


def _circle(c, r, layer, width, fill=False):
    return (f'\t(fp_circle\n\t\t(center {g(c[0])} {g(c[1])})\n\t\t(end {g(c[0] + r)} {g(c[1])})\n'
            f'\t\t(stroke\n\t\t\t(width {g(width)})\n\t\t\t(type solid))\n\t\t(fill {"yes" if fill else "no"})\n'
            f'\t\t(layer "{layer}"))\n')


def _pad(num, x, y, w, h, layers):
    lay = ' '.join(f'"{l}"' for l in layers)
    return f'\t(pad "{num}" smd rect\n\t\t(at {g(x)} {g(y)})\n\t\t(size {g(w)} {g(h)})\n\t\t(layers {lay}))\n'


def _paste(x, y, w, h):
    """Paste-only aperture: no copper, no number (tools/jlc_orient.py and the BOM ignore it)."""
    return _pad('', x, y, w, h, ('F.Paste',))


def footprint(name, descr, body, ref_y, val_y, model):
    head = (f'(footprint "{name}"\n\t(version 20260206)\n\t(generator "{GEN}")\n\t(layer "F.Cu")\n'
            f'\t(descr "{descr}")\n\t(attr smd)\n'
            f'\t(property "Reference" "REF**"\n\t\t(at 0 {g(ref_y)} 0)\n\t\t(layer "F.SilkS")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15))))\n'
            f'\t(property "Value" "{name}"\n\t\t(at 0 {g(val_y)} 0)\n\t\t(layer "F.Fab")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15))))\n')
    tail = (f'\t(model "${{KIPRJMOD}}/kilib/rocket.3dshapes/{model}"\n\t\t(offset\n\t\t\t(xyz 0 0 0))\n'
            f'\t\t(scale\n\t\t\t(xyz 1 1 1))\n\t\t(rotate\n\t\t\t(xyz 0 0 0))))\n')
    return head + body + tail


# u-blox MAX-F10S / MAX-M10S LCC-18 (IM R01 Fig. 25-26; M10S IM R05 Tables 44-45)
MAX_HALF_X, MAX_HALF_Y = 9.7 / 2, 10.1 / 2       # module outline
MAX_PAD_IN, MAX_PAD_OUT = 1.0, 0.8               # pad length under / outside the outline
MAX_PITCH = 1.1
MAX_TAB = 0.6                                     # de-paneling residual tab P, max (DS Table 21)


def max_pad_positions():
    """{pin: (x, y, width)}; pin 1 top left, 1-9 down the left side, 10-18 up the right side (top view)."""
    x = MAX_HALF_X - MAX_PAD_IN + (MAX_PAD_IN + MAX_PAD_OUT) / 2        # 4.75
    out = {}
    for n in range(1, 19):
        k = n - 1 if n <= 9 else 18 - n
        y = -4 * MAX_PITCH + k * MAX_PITCH
        out[str(n)] = (-x if n <= 9 else x, y, 0.7 if n in (1, 9, 10, 18) else 0.8)
    return out


def max_f10s():
    body = ''
    for n, (x, y, w) in max_pad_positions().items():
        body += _pad(n, x, y, MAX_PAD_IN + MAX_PAD_OUT, w, ('F.Cu', 'F.Mask'))
    for n, (x, y, w) in max_pad_positions().items():
        s = math.copysign(1, x)
        body += _paste(s * (MAX_HALF_X + 0.7), y, 1.4, w)              # outside the module: 4.85 .. 6.25
        body += _paste(s * (MAX_HALF_X - 0.45), y, 0.9, w - 0.2)       # under the module: 3.95 .. 4.85
    tab_y = MAX_HALF_Y + MAX_TAB
    body += _rect((-MAX_HALF_X, -MAX_HALF_Y), (MAX_HALF_X, MAX_HALF_Y), 'F.Fab', 0.1)
    body += _line((-MAX_HALF_X, -3.9), (-3.7, -MAX_HALF_Y), 'F.Fab', 0.1)      # pin-1 chamfer
    for sy in (-1, 1):                                                      # tab allowance, either edge
        body += _line((-2.0, sy * tab_y), (2.0, sy * tab_y), 'F.Fab', 0.1)
    body += _rect((-6.4, -(tab_y + 0.3)), (6.4, tab_y + 0.3), 'F.CrtYd', 0.05)
    for sy in (-1, 1):
        body += _line((-MAX_HALF_X, sy * (tab_y + 0.15)), (MAX_HALF_X, sy * (tab_y + 0.15)), 'F.SilkS', 0.15)
    body += _line((-5.35, -(tab_y + 0.15)), (-5.35, -5.2), 'F.SilkS', 0.15)   # pin-1 tick, clear of pad 1
    descr = ('u-blox MAX-F10S-00B / MAX-M10S-00B LCC-18, 9.7 x 10.1 mm, 1.1 mm pitch. Land: MAX-F10S IM '
             'UBXDOC-963802114-12892 R01 Fig. 25 (copper = mask) and MAX-M10S IM UBX-20053088 R05 Table 44; '
             'T-shaped paste per Fig. 26 / Table 45 (150 um stencil). Courtyard covers the 12.5 mm paste '
             'span and the 0.6 mm de-paneling tab on either 9.7 mm edge (DS Table 21: 10.7 x 9.8 x 2.7 max)')
    return footprint('M3_MAX_F10S_LCC18', descr, body, -7.0, 7.0, 'M3_MAX_F10S_ENVELOPE.wrl')


# EBYTE E22-900MM22S, 20 stamp-hole pads (manual v1.3 ch. 3)
E22_HALF = 5.0
E22_PITCH = 1.27
E22_LAND = (1.5, 0.9)       # length across the edge, width along it
E22_CX = E22_HALF - 0.8 + E22_LAND[0] / 2         # 4.95: 0.80 under the module, 0.70 outside


def e22_pad_positions():
    """{pin: (x, y, w, h)}; counter-clockwise from the top: 1-5 left (down), 6-10 bottom (right),
    11-15 right (up), 16-20 top (left), as the EBYTE top view."""
    out = {}
    offs = [(k - 2) * E22_PITCH for k in range(5)]                 # -2.54 .. 2.54
    for k in range(5):
        out[str(1 + k)] = (-E22_CX, offs[k], E22_LAND[0], E22_LAND[1])
        out[str(6 + k)] = (offs[k], E22_CX, E22_LAND[1], E22_LAND[0])
        out[str(11 + k)] = (E22_CX, -offs[k], E22_LAND[0], E22_LAND[1])
        out[str(16 + k)] = (-offs[k], -E22_CX, E22_LAND[1], E22_LAND[0])
    return out


def e22():
    body = ''
    for n, (x, y, w, h) in e22_pad_positions().items():
        body += _pad(n, x, y, w, h, ('F.Cu', 'F.Paste', 'F.Mask'))
    body += _rect((-E22_HALF, -E22_HALF), (E22_HALF, E22_HALF), 'F.Fab', 0.1)
    body += _circle((-3.6, -3.6), 0.4, 'F.Fab', 0.1)
    body += _rect((-5.85, -5.85), (5.85, 5.85), 'F.CrtYd', 0.05)
    c = 5.35
    for sx in (-1, 1):
        for sy in (-1, 1):
            body += _line((sx * c, sy * 3.6), (sx * c, sy * c), 'F.SilkS', 0.15)
            body += _line((sx * c, sy * c), (sx * 3.6, sy * c), 'F.SilkS', 0.15)
    body += _circle((-6.2, -2.54), 0.2, 'F.SilkS', 0.15, fill=True)       # pin 1 beside its pad
    descr = ('EBYTE E22-900MM22S (SX1262) 10.0 x 10.0 x 2.5 mm, 20 stamp-hole pads at 1.27 mm (manual v1.3 '
             'ch. 3, X.X +/-0.2). Land 0.9 x 1.5 mm: module pad 0.80 x 0.75 + 0.05 heel, 0.70 toe; same as '
             'JLC/EasyEDA WIRELM-SMD_20P-L10.0-W10.0-P1.27-TL (C5333985). EBYTE: no tracks under the module')
    return footprint('M3_E22_900MM22S', descr, body, -7.0, 7.0, 'M3_E22_900MM22S_ENVELOPE.wrl')


# Kinghelm KH-SMA-KE8-G edge-launch jack (drawing 2019-08-10). Board edge = local y 0, board on +y.
SMA_LEG_X = 2.55
SMA_PAD = (1.2, 4.2)
SMA_PAD_Y = 0.2 + SMA_PAD[1] / 2                   # 2.3: pads span 0.2 .. 4.4 from the edge


def sma():
    body = ''
    for num, x, layers in (('1', -SMA_LEG_X, ('F.Cu', 'F.Mask')), ('2', SMA_LEG_X, ('F.Cu', 'F.Mask')),
                           ('3', -SMA_LEG_X, ('B.Cu', 'B.Mask')), ('4', SMA_LEG_X, ('B.Cu', 'B.Mask')),
                           ('5', 0, ('F.Cu', 'F.Mask'))):
        body += _pad(num, x, SMA_PAD_Y, SMA_PAD[0], SMA_PAD[1], layers)
    # body beyond the edge (fab only; silkscreen must stay on the board)
    body += _rect((-3.25, -1.5), (3.25, 0), 'F.Fab', 0.1)
    body += _rect((-3.175, -9.5), (3.175, -1.5), 'F.Fab', 0.1)
    body += _line((-4.0, 0), (4.0, 0), 'F.Fab', 0.1)                        # board edge reference
    for x in (-SMA_LEG_X, 0, SMA_LEG_X):
        body += _rect((x - 0.45, 0), (x + 0.45, 4.0), 'F.Fab', 0.05)
    for layer in ('F.CrtYd', 'B.CrtYd'):
        body += _rect((-3.5, -9.75), (3.5, 4.65), layer, 0.05)
    descr = ('Kinghelm KH-SMA-KE8-G (C530661) 50 ohm edge-launch SMA jack for a 1.6 mm board; same land: BAT '
             'WIRELESS BWSMA-KE-P001 (C496550). Centre pad 5 and legs 1/2 on F.Cu, legs 3/4 on B.Cu, '
             '1.2 x 4.2 mm from 0.2 to 4.4 mm inside the edge (local y = 0). NO paste: fitted by hand in '
             'JLC through-hole step after reflow. Body overhangs the edge 9.5 mm (flange 1.5 + thread 8)')
    return footprint('M3_SMA_KH_KE8_EDGE', descr, body, 6.2, 7.5, 'M3_SMA_KH_KE8_EDGE.wrl')


def tslp():
    body = ''
    for num, x in (('1', -0.325), ('2', 0.325)):
        body += _pad(num, x, 0, 0.35, 0.6, ('F.Cu', 'F.Mask'))
    for x in (-0.33, 0.33):
        body += _paste(x, 0, 0.28, 0.45)
    body += _rect((-0.5, -0.3), (0.5, 0.3), 'F.Fab', 0.05)
    body += _rect((-0.65, -0.45), (0.65, 0.45), 'F.CrtYd', 0.05)
    descr = ('Infineon TSLP-2-20 (ESD103-B1-02EL, C535146), 1.0 x 0.6 x 0.31 mm, bidirectional. Land: ESD103-B1-02 '
             'data sheet rev 1.3 Fig. 14 TSLP-2-19/-20-FP V01: copper 0.35 x 0.6 at 0.65 pitch, paste 0.28 x 0.45; '
             'per-pad mask openings (Infineon: one common opening)')
    return footprint('M3_TSLP_2_20', descr, body, -1.4, 1.4, 'M3_TSLP_2_20.wrl')


def lqg15():
    body = ''.join(_pad(n, x, 0, 0.525, 0.55, ('F.Cu', 'F.Paste', 'F.Mask')) for n, x in (('1', -0.4625), ('2', 0.4625)))
    body += _rect((-0.5, -0.25), (0.5, 0.25), 'F.Fab', 0.05)
    body += _rect((-0.88, -0.43), (0.88, 0.43), 'F.CrtYd', 0.05)
    descr = ('Murata LQG15HS 0402 chip inductor (LQG15HS47NJ02D, C97998), 1.0 x 0.5 x 0.5 mm. Land: Murata '
             'JELF243B-0010 sec. 11.1 (a 0.4, b 1.45, c 0.55 mm)')
    return footprint('M3_LQG15_0402', descr, body, -1.3, 1.3, 'M3_LQG15_0402.wrl')


def blm18k():
    body = ''.join(_pad(n, x, 0, 0.6, 0.7, ('F.Cu', 'F.Paste', 'F.Mask')) for n, x in (('1', -0.65), ('2', 0.65)))
    body += _rect((-0.8, -0.4), (0.8, 0.4), 'F.Fab', 0.05)
    body += _rect((-1.1, -0.55), (1.1, 0.55), 'F.CrtYd', 0.05)
    descr = ('Murata BLM18KG 0603 ferrite bead (BLM18KG221SN1D, C88980), 1.6 x 0.8 x 0.8 mm. Land: Murata '
             'JENF243A-0003 sec. 10-1, BLM18K reflow (a 0.7, b 1.9, c 0.7 mm)')
    return footprint('M3_BLM18K_0603', descr, body, -1.4, 1.4, 'M3_BLM18K_0603.wrl')


def c0402_dnp():
    """rocket:C0402 without paste, for unfitted (DNP) placeholders: the stencil prints nothing on their empty lands
    (R7 pass 2 RF-01/DFM-02). Copied from C0402 (same copper, mask, courtyard and model) with fixed UUIDs."""
    import uuid
    text = (PRETTY / 'C0402.kicad_mod').read_text()
    text = text.replace('(footprint "C0402"', '(footprint "C0402_DNP"', 1)
    text = text.replace('\t(layer "F.Cu")\n', '\t(layer "F.Cu")\n\t(descr "C0402 land with no solder paste: an unfitted (DNP) '
                        'placeholder, so the stencil prints nothing on its empty pads (R7 pass 2 RF-01/DFM-02)")\n', 1)
    text = text.replace('(property "Value" "C0402"', '(property "Value" "C0402_DNP"')
    n = text.count('(layers "F.Cu" "F.Mask" "F.Paste")')
    assert n == 2, n
    text = text.replace('(layers "F.Cu" "F.Mask" "F.Paste")', '(layers "F.Cu" "F.Mask")')
    ns = uuid.UUID('5b1c7e2a-0d4f-4e2b-9a61-3f0c2d7e9b14')
    k = iter(range(1, 1000))
    return re.sub(r'\(uuid "[0-9a-f-]+"\)', lambda m: '(uuid "%s")' % uuid.uuid5(ns, 'C0402_DNP:%d' % next(k)), text)


FOOTPRINTS = {'M3_MAX_F10S_LCC18': max_f10s, 'M3_E22_900MM22S': e22, 'M3_SMA_KH_KE8_EDGE': sma,
              'M3_TSLP_2_20': tslp, 'M3_LQG15_0402': lqg15, 'M3_BLM18K_0603': blm18k, 'C0402_DNP': c0402_dnp}


# ---------------------------------------------------------------------------------------------------------
# 3D envelopes: VRML boxes (1 unit = 2.54 mm; KiCad model y is up, so footprint y = -model y)


def _box(cx, cy, z0, sx, sy, sz, color):
    """Box centred on footprint (cx, cy), from z0 up by sz (mm)."""
    t = [cx / 2.54, -cy / 2.54, (z0 + sz / 2) / 2.54]
    s = [sx / 2.54, sy / 2.54, sz / 2.54]
    return ('Transform { translation ' + ' '.join(f'{v:.6f}' for v in t) + ' children [ Shape { appearance '
            f'Appearance {{ material Material {{ diffuseColor {color} }} }} geometry Box {{ size '
            + ' '.join(f'{v:.6f}' for v in s) + ' } } ] }\n')


PCB, CAN, BRASS, GOLD, BLACK = '.06 .25 .10', '.75 .75 .78', '.80 .62 .25', '.85 .70 .30', '.12 .12 .12'
MODELS = {
    'M3_MAX_F10S_ENVELOPE.wrl': (
        '# MAX-F10S/M10S envelope from u-blox DS Table 21 maxima: 9.8 x 10.7 mm incl. the 0.6 mm tab (modelled\n'
        '# on both 9.7 mm edges), 2.7 mm high. NOT a maker model.\n',
        [(0, 0, 0, 9.8, 10.1 + 2 * 0.6, 0.8, PCB), (0, 0, 0, 9.4, 9.8, 2.7, CAN)]),
    'M3_E22_900MM22S_ENVELOPE.wrl': (
        '# E22-900MM22S envelope from the EBYTE manual v1.3 drawing: 10.0 +/-0.2 square, 2.5 +/-0.2 high.\n'
        '# NOT a maker model.\n',
        [(0, 0, 0, 10.2, 10.2, 0.8, PCB), (0, 0, 0, 8.6, 8.6, 2.7, CAN)]),
    'M3_SMA_KH_KE8_EDGE.wrl': (
        '# KH-SMA-KE8-G envelope from the Kinghelm drawing (+0.2 general tolerance on the body): flange 6.7 sq x\n'
        '# 1.7, thread 6.4 dia x 8.2 to 9.7 mm beyond the board edge, axis 0.45 mm above the top face; legs 0.9 sq\n'
        '# x 4.0 on both faces (1.7 mm slot), centre pin 0.95. Board edge at footprint y = 0. NOT a maker model.\n',
        [(0, -0.85, 0.45 - 3.35, 6.7, 1.7, 6.7, GOLD), (0, -5.6, 0.45 - 3.2, 6.4, 8.2, 6.4, GOLD),
         (-SMA_LEG_X, 2.0, 0, 0.9, 4.0, 0.9, BRASS), (SMA_LEG_X, 2.0, 0, 0.9, 4.0, 0.9, BRASS),
         (-SMA_LEG_X, 2.0, -1.7 - 0.9, 0.9, 4.0, 0.9, BRASS), (SMA_LEG_X, 2.0, -1.7 - 0.9, 0.9, 4.0, 0.9, BRASS),
         (0, 2.0, 0.45 - 0.475, 0.95, 4.0, 0.95, GOLD)]),
    'M3_TSLP_2_20.wrl': (
        '# TSLP-2-20 envelope, Infineon ESD103-B1-02EL DS v2.0 Fig. 9 maxima: 1.05 x 0.65 x 0.32 mm. NOT a maker model.\n',
        [(0, 0, 0, 1.05, 0.65, 0.32, BLACK)]),
    'M3_LQG15_0402.wrl': (
        '# LQG15HS envelope, Murata JELF243B-0010 sec. 5 maxima: 1.05 x 0.55 x 0.55 mm. NOT a maker model.\n',
        [(0, 0, 0, 1.05, 0.55, 0.55, '.85 .85 .85')]),
    'M3_BLM18K_0603.wrl': (
        '# BLM18KG envelope, Murata JENF243A-0003 sec. 4 maxima: 1.75 x 0.95 x 0.95 mm. NOT a maker model.\n',
        [(0, 0, 0, 1.75, 0.95, 0.95, '.20 .20 .22')]),
}


def model_text(name):
    note, boxes = MODELS[name]
    return '#VRML V2.0 utf8\n' + note + ''.join(_box(*b) for b in boxes)


# ---------------------------------------------------------------------------------------------------------
# symbols


def _close(text, start):
    """Index just past the parenthesis that closes the one opening at text[start] (skips strings)."""
    depth, i, in_str = 0, start, False
    while i < len(text):
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


def lib_block(lt, name):
    i = lt.index(f'\t(symbol "{name}"\n')
    return lt[i:_close(lt, i + 1)]


def _prop(name, value, at, hide=False, size=1.27):
    h = '\t\t\t(hide yes)\n' if hide else ''
    return (f'\t\t(property "{name}" "{value}"\n\t\t\t(at {g(at[0])} {g(at[1])} 0)\n{h}'
            f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size {g(size)} {g(size)}))))\n')


def _pin(kind, x, y, angle, length, name, number):
    return (f'\t\t\t(pin {kind} line\n\t\t\t\t(at {g(x)} {g(y)} {angle})\n\t\t\t\t(length {g(length)})\n'
            f'\t\t\t\t(name "{name}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.05 1.05))))\n'
            f'\t\t\t\t(number "{number}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.05 1.05)))))\n')


def module_symbol(name, ref, descr, keywords, filt, half_w, half_h, left, right):
    """Box symbol; left/right: [(y, number, name, type)], pins 5.08 long ending at x = -/+ (half_w + 5.08)."""
    s = (f'\t(symbol "{name}"\n\t\t(pin_names\n\t\t\t(offset 1.016))\n\t\t(exclude_from_sim no)\n'
         f'\t\t(in_bom yes)\n\t\t(on_board yes)\n')
    s += _prop('Reference', ref, (0, half_h + 2.54))
    s += _prop('Value', name, (0, -half_h - 2.54))
    s += _prop('Footprint', '', (0, 0), hide=True)
    s += _prop('Datasheet', '', (0, 0), hide=True)
    s += _prop('Description', descr, (0, 0), hide=True)
    s += _prop('ki_keywords', keywords, (0, 0), hide=True)
    s += _prop('ki_fp_filters', filt, (0, 0), hide=True)
    s += (f'\t\t(symbol "{name}_0_1"\n\t\t\t(rectangle\n\t\t\t\t(start {g(-half_w)} {g(half_h)})\n'
          f'\t\t\t\t(end {g(half_w)} {g(-half_h)})\n\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n'
          f'\t\t\t\t\t(type default))\n\t\t\t\t(fill\n\t\t\t\t\t(type background))))\n')
    s += f'\t\t(symbol "{name}_1_1"\n'
    for y, num, pname, kind in left:
        s += _pin(kind, -half_w - 5.08, y, 0, 5.08, pname, num)
    for y, num, pname, kind in right:
        s += _pin(kind, half_w + 5.08, y, 180, 5.08, pname, num)
    s = s.rstrip('\n') + ')\n\t\t(embedded_fonts no))\n'
    return s


def sym_max_f10s():
    left = [(11.43, '8', 'VCC', 'power_in'), (8.89, '7', 'V_IO', 'power_in'), (6.35, '6', 'V_BCKP', 'power_in'),
            (3.81, '14', 'VCC_RF', 'power_out'), (1.27, '13', 'LNA_EN', 'output'), (-1.27, '11', 'RF_IN', 'passive'),
            (-3.81, '15', 'VIO_SEL', 'input'), (-6.35, '1', 'GND', 'power_in'), (-8.89, '10', 'GND', 'power_in'),
            (-11.43, '12', 'GND', 'power_in')]
    right = [(11.43, '2', 'TXD', 'output'), (8.89, '3', 'RXD', 'input'), (6.35, '4', 'TIMEPULSE', 'output'),
             (3.81, '5', 'EXTINT', 'input'), (1.27, '9', 'RESET_N', 'input'),
             (-1.27, '18', 'SAFEBOOT_N', 'bidirectional'), (-3.81, '16', 'SDA', 'bidirectional'),
             (-6.35, '17', 'SCL', 'input')]
    return module_symbol('MAX_F10S', 'U', 'u-blox MAX-F10S (L1/L5) GNSS module, LCC-18; MAX-M10S has the same pins '
                         '(DS UBXDOC-963802114-12732 R03 Table 10)', 'GNSS GPS u-blox module',
                         'M3_MAX_F10S_LCC18', 12.7, 13.97, left, right)


def sym_e22():
    left = [(12.7, '1', 'VCC', 'power_in'), (10.16, '6', 'ANT', 'passive'), (7.62, '9', 'TXEN', 'input'),
            (5.08, '10', 'RXEN', 'input'), (2.54, '19', 'DIO2', 'bidirectional'), (0, '18', 'DIO3', 'bidirectional'),
            (-2.54, '2', 'GND', 'power_in'), (-5.08, '7', 'GND', 'power_in'), (-7.62, '16', 'GND', 'power_in')]
    right = [(12.7, '14', 'NSS', 'input'), (10.16, '15', 'SCK', 'input'), (7.62, '13', 'MOSI', 'input'),
             (5.08, '12', 'MISO', 'tri_state'), (2.54, '11', 'BUSY', 'output'), (0, '3', 'NRST', 'input'),
             (-2.54, '20', 'DIO1', 'bidirectional'), (-5.08, '4', 'NC', 'no_connect'),
             (-7.62, '5', 'NC', 'no_connect'), (-10.16, '8', 'NC', 'no_connect'), (-12.7, '17', 'NC', 'no_connect')]
    return module_symbol('E22_900MM22S', 'U', 'EBYTE E22-900MM22S SX1262 LoRa module, 20 stamp holes '
                         '(user manual v1.3 ch. 3)', 'LoRa SX1262 radio module EBYTE',
                         'M3_E22_900MM22S', 12.7, 15.24, left, right)


def sym_sma():
    s = (f'\t(symbol "SMA_Edge"\n\t\t(pin_names\n\t\t\t(offset 0.508)\n\t\t\t(hide yes))\n\t\t(exclude_from_sim no)\n'
         f'\t\t(in_bom yes)\n\t\t(on_board yes)\n')
    s += _prop('Reference', 'J', (0, 7.62))
    s += _prop('Value', 'SMA_Edge', (0, -7.62))
    s += _prop('Footprint', '', (0, 0), hide=True)
    s += _prop('Datasheet', '', (0, 0), hide=True)
    s += _prop('Description', '50 ohm edge-launch SMA jack: 5 = centre contact, 1-4 = ground legs', (0, 0), hide=True)
    s += _prop('ki_keywords', 'SMA coax RF connector antenna', (0, 0), hide=True)
    s += _prop('ki_fp_filters', 'M3_SMA_KH_KE8_EDGE', (0, 0), hide=True)
    s += ('\t\t(symbol "SMA_Edge_0_1"\n\t\t\t(rectangle\n\t\t\t\t(start -3.81 5.08)\n\t\t\t\t(end 3.81 -5.08)\n'
          '\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default))\n\t\t\t\t(fill\n\t\t\t\t\t(type background)))\n'
          '\t\t\t(circle\n\t\t\t\t(center 0 0)\n\t\t\t\t(radius 2.032)\n\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n'
          '\t\t\t\t\t(type default))\n\t\t\t\t(fill\n\t\t\t\t\t(type none)))\n'
          '\t\t\t(circle\n\t\t\t\t(center 0 0)\n\t\t\t\t(radius 0.508)\n\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n'
          '\t\t\t\t\t(type default))\n\t\t\t\t(fill\n\t\t\t\t\t(type outline))))\n')
    s += '\t\t(symbol "SMA_Edge_1_1"\n'
    s += _pin('passive', -8.89, 0, 0, 5.08, 'SIG', '5')
    for y, num in ((3.81, '1'), (1.27, '2'), (-1.27, '3'), (-3.81, '4')):
        s += _pin('passive', 8.89, y, 180, 5.08, 'SH', num)
    return s.rstrip('\n') + ')\n\t\t(embedded_fonts no))\n'


def derived(lt, base, name, replace):
    """Copy an existing library symbol under a new name with text replacements (all must apply)."""
    blk = lib_block(lt, base).replace(f'(symbol "{base}"', f'(symbol "{name}"', 1)
    blk = blk.replace(f'(symbol "{base}_', f'(symbol "{name}_')
    for old, new in replace:
        if old not in blk:
            raise SystemExit(f'{name}: {old!r} not in {base}')
        blk = blk.replace(old, new)
    return blk + '\n'


def sym_pmos(lt):
    return derived(lt, 'NMOS_SOT23', 'PMOS_SOT23', [
        ('"NMOS_SOT23"', '"PMOS_SOT23"'),
        ('N-MOSFET SOT-23 (1 G, 2 S, 3 D)', 'P-MOSFET SOT-23 (1 G, 2 S, 3 D)'),
        ('(at 0 -10.16 90)\n\t\t\t\t(length 5.08)\n\t\t\t\t(name "S"', '(at 0 10.16 270)\n\t\t\t\t(length 5.08)\n\t\t\t\t(name "S"'),
        ('(at 0 10.16 270)\n\t\t\t\t(length 5.08)\n\t\t\t\t(name "D"', '(at 0 -10.16 90)\n\t\t\t\t(length 5.08)\n\t\t\t\t(name "D"')])


def sym_pnp(lt):
    return derived(lt, 'NMOS_SOT23', 'PNP_SOT23', [
        ('"NMOS_SOT23"', '"PNP_SOT23"'),
        ('N-MOSFET SOT-23 (1 G, 2 S, 3 D)', 'PNP BJT SOT-23 (1 B, 2 E, 3 C)'),
        ('(name "G"', '(name "B"'),
        ('(at 0 -10.16 90)\n\t\t\t\t(length 5.08)\n\t\t\t\t(name "S"', '(at 0 10.16 270)\n\t\t\t\t(length 5.08)\n\t\t\t\t(name "E"'),
        ('(at 0 10.16 270)\n\t\t\t\t(length 5.08)\n\t\t\t\t(name "D"', '(at 0 -10.16 90)\n\t\t\t\t(length 5.08)\n\t\t\t\t(name "C"')])


def sym_esd(lt):
    return derived(lt, 'TVS_Bidir', 'ESD_Bidir', [
        ('"Bidirectional transient-voltage-suppression diode"',
         '"Bidirectional low-capacitance ESD protection diode (RF line)"'),
        ('(property "Value" "D_TVS"', '(property "Value" "ESD_Bidir"'),
        ('"ki_fp_filters" "D_SMB"', '"ki_fp_filters" "M3_TSLP_2_20"')])


def sym_ferrite(lt):
    blk = lib_block(lt, 'L')
    graphics = blk[blk.index('\t\t(symbol "L_0_1"'):blk.index('\t\t(symbol "L_1_1"')]
    bead = ('\t\t(symbol "FerriteBead_0_1"\n\t\t\t(rectangle\n\t\t\t\t(start -1.016 2.286)\n\t\t\t\t(end 1.016 -2.286)\n'
            '\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default))\n\t\t\t\t(fill\n\t\t\t\t\t(type none)))\n'
            '\t\t\t(polyline\n\t\t\t\t(pts\n\t\t\t\t\t(xy 0 2.54)\n\t\t\t\t\t(xy 0 2.286))\n\t\t\t\t(stroke\n'
            '\t\t\t\t\t(width 0)\n\t\t\t\t\t(type default))\n\t\t\t\t(fill\n\t\t\t\t\t(type none)))\n'
            '\t\t\t(polyline\n\t\t\t\t(pts\n\t\t\t\t\t(xy 0 -2.286)\n\t\t\t\t\t(xy 0 -2.54))\n\t\t\t\t(stroke\n'
            '\t\t\t\t\t(width 0)\n\t\t\t\t\t(type default))\n\t\t\t\t(fill\n\t\t\t\t\t(type none))))\n')
    blk = blk.replace(graphics, bead)
    blk = re.sub(r'"ki_fp_filters" "[^"]*"', '"ki_fp_filters" "M3_BLM18K_0603"', blk)
    return derived(lt.replace(lib_block(lt, 'L'), blk), 'L', 'FerriteBead', [
        ('(property "Reference" "L"', '(property "Reference" "FB"'),
        ('(property "Value" "L"', '(property "Value" "FerriteBead"'),
        ('(property "Description" "Inductor"', '(property "Description" "Ferrite bead"'),
        ('"inductor choke coil reactor magnetic"', '"ferrite bead emi filter"')])


L_FILTER_OLD = '"ki_fp_filters" "IND-SMD_L4.0-W4.0 M3_SRP5030TA"'
L_FILTER_NEW = '"ki_fp_filters" "IND-SMD_L4.0-W4.0 M3_SRP5030TA M3_LQG15_0402"'
C_FILTER_OLD = '"ki_fp_filters" "C0402 C0603 C0805 C_0603_1608Metric C_1206_3216Metric M3_GRM32_1210"'
C_FILTER_NEW = '"ki_fp_filters" "C0402 C0402_DNP C0603 C0805 C_0603_1608Metric C_1206_3216Metric M3_GRM32_1210"'


def symbol_library(lt):
    """New symbols appended before the library's final parenthesis; M3:L's filter gains M3_LQG15_0402."""
    if L_FILTER_OLD in lt:
        lt = lt.replace(L_FILTER_OLD, L_FILTER_NEW)
    assert lib_block(lt, 'L').count(L_FILTER_NEW) == 1
    if C_FILTER_OLD in lt:                         # M3:C gains the DNP placeholder land (pass 2 RF-01)
        lt = lt.replace(C_FILTER_OLD, C_FILTER_NEW)
    assert lib_block(lt, 'C').count(C_FILTER_NEW) == 1
    makers = {'MAX_F10S': lambda _: sym_max_f10s(), 'E22_900MM22S': lambda _: sym_e22(),
              'SMA_Edge': lambda _: sym_sma(), 'ESD_Bidir': sym_esd, 'PMOS_SOT23': sym_pmos,
              'PNP_SOT23': sym_pnp, 'FerriteBead': sym_ferrite}
    for name, make in makers.items():
        blk = make(lt)
        if f'\t(symbol "{name}"\n' in lt:          # owned by this script: keep it in step with the code
            old = lib_block(lt, name)
            if old + '\n' != blk:
                lt = lt.replace(old + '\n', blk, 1)
            continue
        k = lt.rstrip().rindex(')')
        lt = lt[:k] + blk + lt[k:]
    return lt


# ---------------------------------------------------------------------------------------------------------
# checks against JLC/EasyEDA footprints (same method as tools/jlc_orient.py)

# code -> (footprint, EasyEDA pad numbers to compare, maker-land note)
CODES = {
    'C30005563': 'M3_MAX_F10S_LCC18', 'C4153167': 'M3_MAX_F10S_LCC18', 'C5333985': 'M3_E22_900MM22S',
    'C530661': 'M3_SMA_KH_KE8_EDGE', 'C496550': 'M3_SMA_KH_KE8_EDGE', 'C535146': 'M3_TSLP_2_20',
    'C97998': 'M3_LQG15_0402', 'C88980': 'M3_BLM18K_0603', 'C15127': 'SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR',
    'C105432': 'SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR', 'C20917': 'SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR',
    'C19702': 'C0603', 'C22810': 'R_0603_1608Metric', 'C15195': 'C0402', 'C307331': 'C0402', 'C45783': 'C0805',
    'C17168': 'R0402', 'C25091': 'R0402', 'C25105': 'R0402', 'C25741': 'R0402', 'C25744': 'R0402',
    'C11702': 'R0402', 'C4109': 'R0402'}
TOL, MARGIN = 0.35, 0.4          # tools/jlc_orient.py: residual limit and next-best separation


def rot(v, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c + v[1] * s, -v[0] * s + v[1] * c)


def ez_pads(rec):
    hx, hy = rec['head']
    out = {}
    for p in rec['pads']:
        f = p.split('~')
        out.setdefault(f[8], []).append(((float(f[2]) - hx) * 0.254, (float(f[3]) - hy) * 0.254))
    return out


def our_pads(name):
    import pcbnew
    f = pcbnew.FootprintLoad(str(PRETTY), name)
    if f is None:
        raise SystemExit(f'KiCad cannot load {name}')
    out = {}
    for p in f.Pads():
        if not p.GetNumber() or not (p.IsOnLayer(pcbnew.F_Mask) or p.IsOnLayer(pcbnew.B_Mask)):
            continue
        r = p.GetFPRelativePosition()
        out.setdefault(p.GetNumber(), []).append((pcbnew.ToMM(r.x), pcbnew.ToMM(r.y)))
    return f, out


def match(ours, ez):
    common = sorted(set(ours) & set(ez))
    tried, best = [], None
    for th in (0, 90, 180, 270):
        a = [rot(v, th) for n in common for v in ours[n]]
        b = [q for n in common for q in ez[n]]
        ta = ((min(x for x, _ in a) + max(x for x, _ in a)) / 2, (min(y for _, y in a) + max(y for _, y in a)) / 2)
        tb = ((min(x for x, _ in b) + max(x for x, _ in b)) / 2, (min(y for _, y in b) + max(y for _, y in b)) / 2)
        t = (tb[0] - ta[0], tb[1] - ta[1])
        worst = max(min(math.hypot(rot(v, th)[0] + t[0] - e[0], rot(v, th)[1] + t[1] - e[1]) for e in ez[n])
                    for n in common for v in ours[n])
        tried.append(worst)
        if best is None or worst < best[0]:
            best = (worst, th, t)
    worst, th, t = best
    second = sorted(tried)[1]
    full = len(common) == len(ours) == len(ez)
    ok = full and ((worst <= TOL + 1e-4 and second - worst >= MARGIN) or
                   (len(common) == 2 and worst <= 0.6 and second - worst >= 2.0))
    return dict(theta=th, offset=[round(t[0], 4), round(t[1], 4)], residual_mm=round(worst, 3),
                next_best_mm=round(second, 3), pads_ours=len(ours), pads_easyeda=len(ez),
                pads_matched=len(common), status='OK' if ok else 'CHECK')


def geometry_asserts():
    """Re-read the generated lands through pcbnew and assert the maker numbers (guards against typos)."""
    import pcbnew
    mm = pcbnew.ToMM
    f, pads = our_pads('M3_MAX_F10S_LCC18')
    assert len(pads) == 18
    sizes = {p.GetNumber(): (round(mm(p.GetSize().x), 3), round(mm(p.GetSize().y), 3)) for p in f.Pads() if p.GetNumber()}
    assert all(sizes[n] == (1.8, 0.7 if n in ('1', '9', '10', '18') else 0.8) for n in sizes), sizes
    assert abs(pads['1'][0][0] + 4.75) < 1e-6 and abs(pads['1'][0][1] + 4.4) < 1e-6
    assert abs(pads['10'][0][1] - 4.4) < 1e-6 and abs(pads['18'][0][1] + 4.4) < 1e-6
    assert abs(pads['2'][0][1] - pads['1'][0][1] - 1.1) < 1e-6
    paste = [p for p in f.Pads() if not p.GetNumber()]
    assert len(paste) == 36 and not any(p.IsOnLayer(pcbnew.F_Paste) for p in f.Pads() if p.GetNumber())
    span = max(mm(p.GetFPRelativePosition().x) + mm(p.GetSize().x) / 2 for p in paste)
    inner = min(abs(mm(p.GetFPRelativePosition().x)) - mm(p.GetSize().x) / 2 for p in paste)
    assert abs(span - 6.25) < 1e-6 and abs(inner - 3.95) < 1e-6, (span, inner)       # 12.5 / 7.9 mm spans
    f, pads = our_pads('M3_E22_900MM22S')
    assert len(pads) == 20 and abs(pads['1'][0][1] + 2.54) < 1e-6 and abs(pads['1'][0][0] + 4.95) < 1e-6
    assert abs(pads['6'][0][0] + 2.54) < 1e-6 and abs(pads['11'][0][1] - 2.54) < 1e-6
    assert abs(pads['16'][0][0] - 2.54) < 1e-6 and abs(pads['20'][0][0] + 2.54) < 1e-6
    f, pads = our_pads('M3_SMA_KH_KE8_EDGE')
    layers = {p.GetNumber(): ('B' if p.IsOnLayer(pcbnew.B_Cu) else 'F') for p in f.Pads()}
    assert layers == {'1': 'F', '2': 'F', '3': 'B', '4': 'B', '5': 'F'}, layers
    assert not any(p.IsOnLayer(pcbnew.F_Paste) or p.IsOnLayer(pcbnew.B_Paste) for p in f.Pads())
    assert all(abs(min(y for _, y in v) - 2.3) < 1e-6 for v in pads.values())
    f, pads = our_pads('M3_TSLP_2_20')
    assert abs(pads['2'][0][0] - pads['1'][0][0] - 0.65) < 1e-6


def check_against_easyeda():
    data = json.loads(PADS.read_text())
    rows = {}
    for code, fp in CODES.items():
        rec = data.get(code)
        if not rec or 'pads' not in rec:
            raise SystemExit(f'{code}: no EasyEDA pad record in {PADS}')
        _, ours = our_pads(fp)
        rows[f'{code}|{fp}'] = dict(match(ours, ez_pads(rec)), footprint=fp, easyeda=rec['title'],
                                     retrieved_utc=rec.get('retrieved_utc'))
    return rows


# ---------------------------------------------------------------------------------------------------------


def planned():
    files = {PRETTY / f'{name}.kicad_mod': make() for name, make in FOOTPRINTS.items()}
    files.update({SHAPES / name: model_text(name) for name in MODELS})
    files[SYMLIB] = symbol_library(SYMLIB.read_text())
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true', help='change nothing; exit 1 if a file would change')
    a = ap.parse_args()
    changed = [p for p, text in planned().items() if not p.exists() or p.read_text() != text]
    if a.check:
        print('r7_parts: up to date' if not changed else 'r7_parts: would change ' + ', '.join(p.name for p in changed))
        if changed:
            return 1
    else:
        for p, text in planned().items():
            if not p.exists() or p.read_text() != text:
                p.write_text(text)
                print('wrote', p.relative_to(ROOT))
    geometry_asserts()
    rows = check_against_easyeda()
    bad = sorted(k for k, v in rows.items() if v['status'] != 'OK' and not k.startswith('C496550|'))
    report = {'scope': 'R7 lands matched to JLC/EasyEDA footprints by pad number (tools/jlc_orient.py method); '
                       'expected tools/jlc_corrections.json entries once the parts are on the board',
              'tolerance_mm': TOL, 'margin_mm': MARGIN,
              'note': 'C496550 (BAT WIRELESS, second source) is listed for reference only: its EasyEDA numbering '
                      'swaps legs 1 and 2 against C530661, so a substitution needs its own reviewed correction',
              'parts': rows}
    text = json.dumps(report, indent=1) + '\n'
    if not a.check and (not REPORT.exists() or REPORT.read_text() != text):
        REPORT.write_text(text)
        print('wrote', REPORT.relative_to(ROOT))
    for k, v in rows.items():
        print(f"{k:45s} {v['status']:5s} theta {v['theta']:>3} off {v['offset'][0]:+.3f},{v['offset'][1]:+.3f} "
              f"res {v['residual_mm']:.3f}/{v['next_best_mm']:.2f} pads {v['pads_ours']}/{v['pads_easyeda']}/{v['pads_matched']} | {v['easyeda']}")
    print('CHECK:', bad or 'none')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
