#!/usr/bin/env python3
"""M3-ASSY-R4 footprint-library edits (docs/M3_R4.md). Run before m3_design/r4_pcb.py.

usage: <KiCad python3> m3_design/r4_lib.py

Courtyards: five EasyEDA-derived footprints drew F.CrtYd round the body only, so pads stuck out
0.5-0.9 mm and DRC's courtyard-overlap check could not see two pad-to-pad contacts (R123/C121,
Q123/LS120; docs/R3_VALIDATION.md section 4). Each gets one rectangle round its pads and body plus
0.15 mm (dense-board excess). Idempotent: a footprint whose courtyard already encloses its pads + 0.15 mm is left alone.
r4_pcb.py then reloads the board instances from the library so they stay identical to it.
"""
import math
import re
import sys
from pathlib import Path

import pcbnew

LIB = Path(__file__).resolve().parent / 'assembly_review' / 'kilib' / 'rocket.pretty'
MARGIN = 0.15            # IPC-7351 dense-board courtyard excess; pads always inside
COURTYARD_FIX = ['SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR', 'PDFN-8_L5.6-W5.2-P1.27-LS6.1-BL',
                 'BUZ-SMD_4P-L8.5-W8.5-P8.50-BR', 'CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD_H10.5',
                 'SOD-323_L1.8-W1.3-LS2.5-RD']
mm = pcbnew.ToMM
CROSS = {'CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD_H10.5': 4.15}   # 8.3 mm square base


def up(v):
    """Round outward to 0.05 mm."""
    return math.copysign(math.ceil(abs(v) / 0.05 - 1e-9) * 0.05, v)


def extents(name):
    f = pcbnew.FootprintLoad(str(LIB), name)
    assert f is not None, name
    pads = None
    for p in f.Pads():
        bb = p.GetBoundingBox()
        r = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))
        pads = r if pads is None else (min(pads[0], r[0]), min(pads[1], r[1]), max(pads[2], r[2]), max(pads[3], r[3]))
    cb = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
    crt = (mm(cb.GetX()), mm(cb.GetY()), mm(cb.GetRight()), mm(cb.GetBottom()))
    return pads, crt


def cross_courtyard(name, body_half):
    """Courtyard = union of a centred square body (half-size body_half) and the pad band, + MARGIN.
    For C121's can: its pads stick out of the 8.3 mm base in a thin band, and a plain rectangle
    round both would falsely swallow the parts beside the pads."""
    pads, crt = extents(name)
    b = up(body_half + MARGIN)
    px0, py0, px1, py1 = up(pads[0] - MARGIN), up(pads[1] - MARGIN), up(pads[2] + MARGIN), up(pads[3] + MARGIN)
    path = LIB / f'{name}.kicad_mod'
    text = path.read_text()
    if f'(start {px0:.2f} {py1:.2f})' in text:
        return False
    lines = text.split('\n')
    first = next(ln for ln in lines if '(fp_line' in ln and 'F.CrtYd' in ln)
    indent = first[:-len(first.lstrip())]
    kept = [ln for ln in lines if not ('(fp_line' in ln and 'F.CrtYd' in ln)]
    poly = [(-b, -b), (b, -b), (b, py0), (px1, py0), (px1, py1), (b, py1), (b, b), (-b, b), (-b, py1), (px0, py1), (px0, py0), (-b, py0)]
    new = [f'{indent}(fp_line (start {a[0]:.2f} {a[1]:.2f}) (end {c[0]:.2f} {c[1]:.2f}) (layer F.CrtYd) (width 0.05))'
           for a, c in zip(poly, poly[1:] + poly[:1])]
    at = next(i for i, ln in enumerate(kept) if '(pad ' in ln)
    kept[at:at] = new
    path.write_text('\n'.join(kept))
    print(f'{name}: courtyard -> body +/-{b:.2f} union pads ({px0:.2f}, {py0:.2f}, {px1:.2f}, {py1:.2f})')
    return True


def fix_courtyard(name):
    if name in CROSS:
        return cross_courtyard(name, CROSS[name])
    pads, crt = extents(name)
    need = (pads[0] - MARGIN, pads[1] - MARGIN, pads[2] + MARGIN, pads[3] + MARGIN)
    if crt[0] <= need[0] + 1e-6 and crt[1] <= need[1] + 1e-6 and crt[2] >= need[2] - 1e-6 and crt[3] >= need[3] - 1e-6:
        return False
    x0, y0 = up(min(crt[0], need[0])), up(min(crt[1], need[1]))
    x1, y1 = up(max(crt[2], need[2])), up(max(crt[3], need[3]))
    path = LIB / f'{name}.kicad_mod'
    lines = path.read_text().split('\n')
    kept = [ln for ln in lines if not ('(fp_line' in ln and 'F.CrtYd' in ln)]
    assert len(kept) == len(lines) - 4 or len(kept) < len(lines), name
    indent = next(ln for ln in lines if '(fp_line' in ln and 'F.CrtYd' in ln)[:-len(next(ln for ln in lines if '(fp_line' in ln and 'F.CrtYd' in ln).lstrip())]
    rect = [(x0, y1, x0, y0), (x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1)]
    new = [f'{indent}(fp_line (start {a:.2f} {b:.2f}) (end {c:.2f} {d:.2f}) (layer F.CrtYd) (width 0.05))' for a, b, c, d in rect]
    at = next(i for i, ln in enumerate(kept) if '(pad ' in ln)          # courtyard goes just before the pads
    kept[at:at] = new
    path.write_text('\n'.join(kept))
    print(f'{name}: courtyard {tuple(round(v, 2) for v in crt)} -> ({x0:.2f}, {y0:.2f}, {x1:.2f}, {y1:.2f})')
    return True


# Paste apertures (R3 report 4). KiCad paste size per axis = pad + 2 * ratio * pad, so area = (1 + 2r)^2.
PASTE = {
    'M3_TPS25947_RPW': {'5': -0.047, '6': -0.047,           # IN/OUT bars: 82 % area (TI RPW0010A stencil example)
                        '1': -0.018, '4': -0.018, '7': -0.018, '10': -0.018},   # corner pads: 93 % (same drawing)
    'M3_TPS2595_DSG': {'9': -0.034},                         # exposed pad: 87 % area (TI TPS2595 stencil)
    # AON6403 gate/source: 81 %. AOS publishes no stencil guidance; these are engineering choices, and the
    # paddle gets a windowpane in aon6403_windowpane() (validation pass 2)
    'PDFN-8_L5.6-W5.2-P1.27-LS6.1-BL': {'1': -0.05, '2': -0.05, '3': -0.05, '4': -0.05},
}


def set_paste(name, ratios):
    path = LIB / f'{name}.kicad_mod'
    t = path.read_text()
    if 'solder_paste_margin_ratio' in t:
        return False
    for num, r in ratios.items():
        # KiCad 10 multi-line pads: (pad "N" ...\n\t\t(at ..)\n\t\t(size ..)
        pat = re.compile(r'(\t\(pad "' + num + r'" [^\n]*\n\t\t\(at [^\n]*\n\t\t\(size [^\n]*\n)')
        t, n = pat.subn(lambda m: m.group(1) + f'\t\t(solder_paste_margin_ratio {r})\n', t)
        if n == 0:   # KiCad 5 one-line pads: (pad N smd rect (at ..) (size ..) (layers ..))
            pat = re.compile(r'(\(pad ' + num + r' smd [^\n]*\(layers [^)]*\))\)')
            t, n = pat.subn(lambda m: m.group(1) + f' (solder_paste_margin_ratio {r}))', t)
        assert n >= 1, (name, num)
    path.write_text(t)
    print(f'{name}: paste ratios {ratios}')
    return True


def lga14_land():
    """U4 land (now ST LSM6DSV320X; package pads 0.475 x 0.25, DS14623 fig. 32). Length per ST TN0018
    (quoted in TN1383 3.1): package pad + 0.1 mm, ending at the package edge (inner end unchanged; was
    +0.2 mm, 0.1 mm past the edge). Width deliberately stays 0.28, not TN0018's 0.35: with a 0.04 mm
    NSMD mask relief that leaves a 0.14 mm mask web at 0.5 mm pitch (TN0018's land + 0.1 mm opening
    would leave 0.05 mm, below JLC's 0.1 mm). Paste 88 % of the land (TN0018: 70-90 %), which is
    0.142 mm2, ~70 % of a TN0018-sized land, so the joint volume also stays inside ST's range."""
    path = LIB / 'LGA-14_L3.0-W2.5-P0.50-TL.kicad_mod'
    t = path.read_text()
    if 'solder_mask_margin 0.04' in t:
        return False
    t = t.replace('(at -1.26 ', '(at -1.21 ').replace('(at 1.26 ', '(at 1.21 ')
    t = re.sub(r'\(at ([-\d.]+) 1\.01\)', r'(at \1 0.96)', t)
    t = re.sub(r'\(at ([-\d.]+) -1\.01\)', r'(at \1 -0.96)', t)
    extra = '\n\t\t(solder_mask_margin 0.04)\n\t\t(solder_paste_margin_ratio -0.03)'
    t = t.replace('(size 0.675 0.28)', '(size 0.575 0.28)' + extra)
    t = t.replace('(size 0.28 0.675)', '(size 0.28 0.575)' + extra)
    assert t.count('solder_mask_margin 0.04') == 14, t.count('solder_mask_margin 0.04')
    path.write_text(t)
    print('LGA-14 land: 0.575 x 0.28, NSMD +0.04, paste 88 %')
    return True


# Silkscreen marks JLC cannot print (validation pass 1, E5-F7): EasyEDA pin-1 dots are r 0.03 mm circles
# drawn 0.06 wide (a 0.09 mm dot), and some outlines are 0.12 mm; JLC's minimum line is 0.15 mm.
# Dots become 0.4 mm filled dots (r 0.1, 0.2 wide), moved where the old spot sat on or against a pad.
SILK_DOTS = {
    'SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR': (1.0, 1.75),       # old spot touched pad 1 once enlarged
    'PDFN-8_L5.6-W5.2-P1.27-LS6.1-BL': None,                # None: keep the old centre
    'CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD_H10.5': None,
    'BUZ-SMD_4P-L8.5-W8.5-P8.50-BR': (-5.3, 5.3),            # old spot was inside pad 1
    'HDR-TH_12P-P2.54-V-M-R3-C4-S2.54': None,
    'SOD-323_L1.8-W1.3-LS2.5-RD': (-1.23, 0.75),
    'TSOT-26_L2.9-W1.6-P0.95-LS2.8-BL': (-1.6, 1.5),         # replaces a zero-height polygon (printed nothing)
}
SILK_WIDEN = list(SILK_DOTS) + ['D_SMB', 'D_SMA', 'M3_AON7524_DFN3x3A']


def _dot(f, xy):
    s = pcbnew.PCB_SHAPE(f)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetLayer(pcbnew.F_SilkS)
    s.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(xy[0]), pcbnew.FromMM(xy[1])))
    s.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(xy[0] + 0.1), pcbnew.FromMM(xy[1])))
    s.SetWidth(pcbnew.FromMM(0.2))
    s.SetFilled(True)
    f.Add(s)


def silk_marks():
    changed = []
    for name in SILK_WIDEN:
        f = pcbnew.FootprintLoad(str(LIB), name)
        dots, dead, widened = [], [], 0
        for g in f.GraphicalItems():
            if g.GetLayer() != pcbnew.F_SilkS or g.GetClass() != 'PCB_SHAPE':
                continue
            bb = g.GetBoundingBox()
            if g.GetShape() == pcbnew.SHAPE_T_CIRCLE and mm(g.GetRadius()) < 0.075:
                dead.append(g)
                dots.append(SILK_DOTS.get(name) or (mm(g.GetCenter().x), mm(g.GetCenter().y)))
            elif g.GetShape() == pcbnew.SHAPE_T_POLY and min(mm(bb.GetWidth()), mm(bb.GetHeight())) < 0.01:
                dead.append(g)
                dots.append(SILK_DOTS[name])
            elif g.GetShape() != pcbnew.SHAPE_T_POLY and mm(g.GetWidth()) < 0.15 - 1e-6:
                g.SetWidth(pcbnew.FromMM(0.15))
                widened += 1
        for g in dead:
            f.Delete(g)
        for xy in dots:
            _dot(f, xy)
        if dead or widened:
            pcbnew.FootprintSave(str(LIB), f)
            changed.append(f'{name} ({len(dots)} dot, {widened} widened)')
    print('silk marks:', changed or 'none (already done)')


DB128L = """(footprint "M3_DB128L_2P"
\t(version 20260206)
\t(generator "m3_review")
\t(layer "F.Cu")
\t(descr "DORABO DB128L-5.08-2P (LCSC C430603, orange): 5.08 pitch; 1.6 finished hole; hole 5.00 from body face; body 10.16 wide (end-stackable, two make the 4P envelope) x 10.1 deep x 14.1 high")
\t(attr through_hole)
\t(property "Reference" "REF**"
\t\t(at 0 -6.6 0)
\t\t(layer "F.SilkS")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1 1)
\t\t\t\t(thickness .15))))
\t(property "Value" "M3_DB128L_2P"
\t\t(at 0 6.8 0)
\t\t(layer "F.Fab")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1 1)
\t\t\t\t(thickness .15))))
\t(fp_rect
\t\t(start -5.07 -5.25)
\t\t(end 5.07 5.45)
\t\t(stroke
\t\t\t(width .1)
\t\t\t(type solid))
\t\t(fill none)
\t\t(layer "F.Fab"))
\t(fp_rect
\t\t(start -5.07 -5.5)
\t\t(end 5.07 5.7)
\t\t(stroke
\t\t\t(width .05)
\t\t\t(type solid))
\t\t(fill none)
\t\t(layer "F.CrtYd"))
\t(fp_line
\t\t(start -4.8 -5.5)
\t\t(end 4.8 -5.5)
\t\t(stroke
\t\t\t(width .15)
\t\t\t(type solid))
\t\t(layer "F.SilkS"))
\t(fp_line
\t\t(start -4.8 5.7)
\t\t(end 4.8 5.7)
\t\t(stroke
\t\t\t(width .15)
\t\t\t(type solid))
\t\t(layer "F.SilkS"))
\t(pad "1" thru_hole rect
\t\t(at -2.54 0)
\t\t(size 2.6 2.6)
\t\t(drill 1.6)
\t\t(layers "*.Cu" "*.Mask"))
\t(pad "2" thru_hole circle
\t\t(at 2.54 0)
\t\t(size 2.6 2.6)
\t\t(drill 1.6)
\t\t(layers "*.Cu" "*.Mask"))
\t(model "${KIPRJMOD}/kilib/rocket.3dshapes/M3_DB128L_2P.wrl"
\t\t(offset
\t\t\t(xyz 0 0 0))
\t\t(scale
\t\t\t(xyz 1 1 1))
\t\t(rotate
\t\t\t(xyz 0 0 0))))
"""
DB128L_WRL = ('#VRML V2.0 utf8\n# M3 nominal/envelope visualization; not vendor model. DB128L-5.08-2P orange: 10.16 x 10.7 '
              '(incl tolerance/tongue) x 14.4 (14.1 + tolerance) mm\nTransform { translation 0 0 2.83464567 children [ Shape '
              '{ appearance Appearance { material Material { diffuseColor 0.95 0.5 0.1 } } geometry Box { size 4.0 '
              '4.21259842519685 5.669291338582677 } } ] }\n')


def db128l_footprint():
    """A3 (first R4 cut): the orange 2-position terminal that replaces the green 4-position ARM and
    igniter terminals did not exist in the R3 library. Written here (base outline; terminal_marks()
    then adds the wire-entry arrows), so the whole of R4 regenerates from the R3 files.
    Validation pass 2 (actuators F1): the ARM terminals become the black part (DB128L-5.08-2P-BK-S,
    C430601), so an ARM link and an igniter cannot swap terminals unnoticed. Same DORABO body and land;
    EasyEDA's black and orange 3D models are the same geometry at the same rotation."""
    (LIB / 'M3_DB128L_2P.kicad_mod').write_text(DB128L)
    (LIB.parent / 'rocket.3dshapes' / 'M3_DB128L_2P.wrl').write_text(DB128L_WRL)
    bk = (DB128L.replace('(footprint "M3_DB128L_2P"', '(footprint "M3_DB128L_2P_BK"')
          .replace('DB128L-5.08-2P (LCSC C430603, orange)', 'DB128L-5.08-2P-BK-S (LCSC C430601, black; ARM terminals)')
          .replace('(property "Value" "M3_DB128L_2P"', '(property "Value" "M3_DB128L_2P_BK"')
          .replace('M3_DB128L_2P.wrl', 'M3_DB128L_2P_BK.wrl'))
    assert bk.count('M3_DB128L_2P_BK') == 3 and 'C430601' in bk
    (LIB / 'M3_DB128L_2P_BK.kicad_mod').write_text(bk)
    (LIB.parent / 'rocket.3dshapes' / 'M3_DB128L_2P_BK.wrl').write_text(
        DB128L_WRL.replace('orange', 'black').replace('diffuseColor 0.95 0.5 0.1', 'diffuseColor 0.12 0.12 0.12'))


TERMINALS = {'M3_DB128V_4P': (-7.62, -2.54, 2.54, 7.62), 'M3_DB128V_4P_Entry': (-7.62, -2.54, 2.54, 7.62),
             'M3_DB128L_2P': (-2.54, 2.54), 'M3_DB128L_2P_BK': (-2.54, 2.54)}


def terminal_marks():
    """Wire-entry arrows (validation pass 1, E4-F5/E5-F1) on local -y, where every placement puts the
    board edge. JLC fits through-hole parts from EasyEDA's model, and a symmetric pin row cannot show a
    180 deg error; the arrows sit under the body so the operator sees them at insertion. DB128V body
    asymmetry corrected: the DORABO DB128V drawing (third-angle side view and PCB layout) puts the pin
    row 5.00 mm from the BACK face and 5.20 mm from the wire-entry face (GEOMETRY_REV_G 3 had it
    reversed), so the entry side is now 5.20 + 0.25 (fab) / + 0.5 (courtyard)."""
    done = []
    for name, pins in TERMINALS.items():
        f = pcbnew.FootprintLoad(str(LIB), name)
        if 'wire entry on local -y' in f.GetLibDescription():
            continue
        if name.startswith('M3_DB128V'):
            for g in f.GraphicalItems():
                if g.GetClass() != 'PCB_SHAPE':
                    continue
                flip = {-5.25: -5.45, 5.45: 5.25, -5.5: -5.7, 5.7: 5.5}
                for get, put in (('GetStart', 'SetStart'), ('GetEnd', 'SetEnd')):
                    p = getattr(g, get)()
                    y = round(mm(p.y), 3)
                    if y in flip:
                        getattr(g, put)(pcbnew.VECTOR2I(p.x, pcbnew.FromMM(flip[y])))
        for layer in (pcbnew.F_SilkS, pcbnew.F_Fab):
            for x in pins:
                for (x1, y1), (x2, y2) in (((x - 0.5, -2.6), (x, -3.4)), ((x, -3.4), (x + 0.5, -2.6))):
                    s = pcbnew.PCB_SHAPE(f)
                    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
                    s.SetLayer(layer)
                    s.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
                    s.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
                    s.SetWidth(pcbnew.FromMM(0.15 if layer == pcbnew.F_SilkS else 0.1))
                    f.Add(s)
        d = f.GetLibDescription()
        if name.startswith('M3_DB128V'):
            d = d.replace('envelope incl tolerance/tongue', 'pin row 5.00 from the back face, 5.20 from the wire-entry '
                          'face (DORABO drawing); envelope incl tolerance/tongue')
        f.SetLibDescription(d + '; wire entry on local -y (arrows)')
        pcbnew.FootprintSave(str(LIB), f)
        done.append(name)
    print('terminal entry marks:', done or 'none (already done)')


JST_PH = '''(footprint "M3_JST_PH_B2B_2P"
\t(version 20260206)
\t(generator "m3_review")
\t(layer "F.Cu")
\t(descr "JST B2B-PH-K-S(LF)(SN) (LCSC C131337): PH 2.00 mm pitch, top entry, friction lock; body 6.0 x 4.5, 6.0 high; pin row 1.7 mm from the back face (local -y) and 2.8 mm from the front (JST PH drawing; EasyEDA CONN-TH_B2B-PH-K-S agrees on the side). Drill 0.8 for the 0.5 mm square post")
\t(attr through_hole)
\t(property "Reference" "REF**"
\t\t(at 0 -3.0 0)
\t\t(layer "F.SilkS")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1 1)
\t\t\t\t(thickness .15))))
\t(property "Value" "M3_JST_PH_B2B_2P"
\t\t(at 0 4.2 0)
\t\t(layer "F.Fab")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1 1)
\t\t\t\t(thickness .15))))
\t(fp_rect
\t\t(start -3 -1.75)
\t\t(end 3 2.85)
\t\t(stroke
\t\t\t(width .1)
\t\t\t(type solid))
\t\t(fill none)
\t\t(layer "F.Fab"))
\t(fp_rect
\t\t(start -3.25 -2)
\t\t(end 3.25 3.1)
\t\t(stroke
\t\t\t(width .05)
\t\t\t(type solid))
\t\t(fill none)
\t\t(layer "F.CrtYd"))
\t(fp_poly
\t\t(pts
\t\t\t(xy -3.11 -1.86)
\t\t\t(xy 3.11 -1.86)
\t\t\t(xy 3.11 2.96)
\t\t\t(xy -3.11 2.96))
\t\t(stroke
\t\t\t(width .15)
\t\t\t(type solid))
\t\t(fill none)
\t\t(layer "F.SilkS"))
\t(fp_circle
\t\t(center -1 -2.4)
\t\t(end -0.9 -2.4)
\t\t(stroke
\t\t\t(width .2)
\t\t\t(type solid))
\t\t(fill solid)
\t\t(layer "F.SilkS"))
\t(pad "1" thru_hole rect
\t\t(at -1 0)
\t\t(size 1.4 1.4)
\t\t(drill 0.8)
\t\t(layers "*.Cu" "*.Mask"))
\t(pad "2" thru_hole circle
\t\t(at 1 0)
\t\t(size 1.4 1.4)
\t\t(drill 0.8)
\t\t(layers "*.Cu" "*.Mask"))
\t(model "${KIPRJMOD}/kilib/rocket.3dshapes/M3_JST_PH_B2B_2P.wrl"
\t\t(offset
\t\t\t(xyz 0 0 0))
\t\t(scale
\t\t\t(xyz 1 1 1))
\t\t(rotate
\t\t\t(xyz 0 0 0))))
'''
# VRML units are 2.54 mm; model +y is footprint -y. Body 6.0 x 4.6 x 6.0 centred at footprint y +0.55.
JST_PH_WRL = ('#VRML V2.0 utf8\n# M3 envelope, not a vendor model. JST B2B-PH-K-S: 6.0 x 4.6 x 6.0 mm, centre 0.55 mm toward the front.\n'
              'Transform { translation 0 -0.2165354 1.1811024 children [ Shape { appearance Appearance { material Material '
              '{ diffuseColor 0.92 0.90 0.84 } } geometry Box { size 2.3622047 1.8110236 2.3622047 } } ] }\n')


def jst_ph_footprint():
    """J123 pull-pin header -> JST PH 2-pin top entry (validation pass 1, E5-F5/E6): the PZ254 2.54 mm
    plug stood 16.75 mm with its wires leaving the top, 19 mm off the bore axis, so the wire bend left
    the bore envelope and a 3 mm aft shift of the board put the housing inside the coupler. PH is
    about 6 mm tall and latches."""
    fp = LIB / 'M3_JST_PH_B2B_2P.kicad_mod'
    wrl = LIB.parent / 'rocket.3dshapes' / 'M3_JST_PH_B2B_2P.wrl'
    if fp.exists() and fp.read_text() == JST_PH and wrl.exists():
        return False
    fp.write_text(JST_PH)
    wrl.write_text(JST_PH_WRL)
    print('M3_JST_PH_B2B_2P footprint + envelope model written')
    return True


def usb_shell_paste():
    """J3 (USB-C, an SMT part with four through-hole shell legs): the legs had no paste, so JLC's reflow
    left them unsoldered and the SMD pads alone would take every plug and unplug (validation pass 1,
    E5-F3/E6). Pin-in-paste: each leg gets an F.Paste aperture 0.1 mm larger than its pad."""
    path = LIB / 'USB-C_SMD-TYPE-C-31-M-12_1.kicad_mod'
    t = path.read_text()
    if '(solder_paste_margin 0.1)' in t:
        return False
    n = 0
    for num in ('1', '2', '3', '4'):
        # KiCad 10 multi-line pad: (pad "N" thru_hole oval / (at ..) / (size ..) / (drill ..) / (property ..) / (layers ..)
        pat = re.compile(r'(\t\(pad "' + num + r'" thru_hole oval\n(?:\t\t[^\n]*\n)*?\t\t\(layers "\*\.Cu" "\*\.Mask")\)')
        t, k = pat.subn(lambda m: m.group(1) + ' "F.Paste")\n\t\t(solder_paste_margin 0.1)', t)
        n += k
    assert n == 4, n
    path.write_text(t)
    print('USB-C shell legs: pin-in-paste')
    return True


# --- validation pass 2 (docs/M3_R4.md section 1c) ----------------------------------------------

def paste_only(x, y, w, h, rot=0):
    """A paste-only aperture (no copper, no number: tools/jlc_orient.py and the BOM ignore it)."""
    r = f' {rot}' if rot else ''
    return f'\t(pad "" smd rect\n\t\t(at {x:g} {y:g}{r})\n\t\t(size {w:g} {h:g})\n\t\t(layers "F.Paste")\n\t)\n'


def _add_before_tail(t, chunk):
    k = t.index('\t(embedded_fonts')
    return t[:k] + chunk + t[k:]


def ms5611_land():
    """U5 (sensors F-5 in pass 2, Minor 2 in pass 3): the R3 lands are 1.50 x 0.60 mm at 2.60 mm row pitch, 0.4 mm
    longer than TE's recommended 1.1 x 0.6 mm land at 2.2 mm (MS5611-01BA03 datasheet, PCB layout), so solder spread
    over 36 % more copper. Each land becomes TE's (inner 1.1 mm, mask opening and 100 % paste), and a copper-only
    tab under the mask keeps the outer 0.45 mm, where the tracks and vias join outside the body: same pad number,
    no mask, no paste, so the joint is TE-sized and no routing moves. tools/jlc_orient.py ignores mask-less pads."""
    path = LIB / 'SENSORS-SMD_MS5611-01BA03.kicad_mod'
    t = path.read_text()
    if '(size 1.1 0.6)' in t:
        return False
    pads = re.findall(r'\t\(pad "([1-8])" smd rect\n\t\t\(at ([-\d.]+) ([-\d.]+) 90\)\n\t\t\(size 1\.5 0\.6\)\n'
                      r'\t\t\(layers "F\.Cu" "F\.Mask" "F\.Paste"\)', t)
    assert len(pads) == 8 and all(abs(abs(float(y)) - 1.3) < 1e-6 for _, _, y in pads), pads
    for num, x, y in pads:
        old = f'\t(pad "{num}" smd rect\n\t\t(at {x} {y} 90)\n\t\t(size 1.5 0.6)'
        new = f'\t(pad "{num}" smd rect\n\t\t(at {x} {math.copysign(1.1, float(y)):g} 90)\n\t\t(size 1.1 0.6)'
        assert t.count(old) == 1, old
        t = t.replace(old, new)
    tabs = ''.join(f'\t(pad "{num}" smd rect\n\t\t(at {x} {math.copysign(1.825, float(y)):g} 90)\n\t\t(size 0.45 0.6)\n'
                   f'\t\t(layers "F.Cu")\n\t)\n' for num, x, y in pads)
    t = _add_before_tail(t, tabs)
    path.write_text(t)
    print('MS5611: TE 1.1 x 0.6 mm lands (mask + paste) plus copper-only tabs under the mask')
    return True


def aon6403_windowpane():
    """Q120/Q121 AON6403 paddle (DFM note): one 3.6 x 3.2 mm aperture (61 %) becomes a 2 x 2 windowpane,
    1.875 x 1.46 mm each with 0.35 mm webs (58 % of the 4.6 x 4.1 land, about 70 % of the package's
    exposed pad), which vents flux gas and keeps the part from floating. The upper pair stops 0.2 mm short
    of the drain pins' paste. AOS gives no stencil guidance; this is IPC-7525 large-pad practice."""
    path = LIB / 'PDFN-8_L5.6-W5.2-P1.27-LS6.1-BL.kicad_mod'
    t = path.read_text()
    if '(pad "" smd rect' in t:
        return False
    t, n = re.subn(r'(\t\(pad "9" smd rect\n\t\t\(at 0 -0\.69\)\n\t\t\(size 4\.6 4\.1\)\n\t\t\(layers "F\.Cu" "F\.Mask") "F\.Paste"\)',
                   r'\1)', t)
    assert n == 1, n
    t = _add_before_tail(t, ''.join(paste_only(x, y, 1.875, 1.46) for x in (-1.1125, 1.1125) for y in (-1.43, 0.38)))
    path.write_text(t)
    print('AON6403: paddle paste as a 2 x 2 windowpane (58 %)')
    return True


def j3_silk_trim():
    """J3 (DFM note, AGENTS.md silkscreen rule): the EasyEDA outline draws the receptacle's front face 0.49 mm
    beyond the board edge (J3 sits at x 4.6, turned -90 deg, so the edge is local y 4.6) and two stubs to
    within 0.07 mm of it; JLC clips both. The front-face line goes and the stubs stop 0.5 mm inside the edge."""
    f = pcbnew.FootprintLoad(str(LIB), 'USB-C_SMD-TYPE-C-31-M-12_1')
    edge, keep = 4.6, 4.6 - 0.5 - 0.125            # line centre 0.5 mm + half its width inside the edge
    dead, trimmed = [], 0
    for g in f.GraphicalItems():
        if g.GetLayer() != pcbnew.F_SilkS or g.GetClass() != 'PCB_SHAPE' or g.GetShape() != pcbnew.SHAPE_T_SEGMENT:
            continue
        ys = [mm(g.GetStart().y), mm(g.GetEnd().y)]
        if min(ys) > keep:
            dead.append(g)
        elif max(ys) > keep:
            for get, put in (('GetStart', 'SetStart'), ('GetEnd', 'SetEnd')):
                p = getattr(g, get)()
                if mm(p.y) > keep:
                    getattr(g, put)(pcbnew.VECTOR2I(p.x, pcbnew.FromMM(keep)))
            trimmed += 1
    if not dead and not trimmed:
        return False
    assert edge - keep > 0.6 and len(dead) == 1 and trimmed == 2, (len(dead), trimmed)
    for g in dead:
        f.Delete(g)
    pcbnew.FootprintSave(str(LIB), f)
    print('J3 silkscreen: front-face line removed, 2 stubs trimmed 0.5 mm inside the board edge')
    return True


# --- validation pass 4 (docs/M3_R4.md section 1e) ----------------------------------------------

R2512_UR = '''(footprint "M3_R2512_UR"
\t(version 20260206)
\t(generator "pcbnew")
\t(layer "F.Cu")
\t(descr "UNI-ROYAL 2512 thick-film chip resistor, maker's recommended land (Thick Film Chip Resistors data sheet V.3, land table: A 5.0, B 1.6, C 3.3, D 8.2 mm): pads 1.6 x 3.3 mm, 5.0 mm gap. Body 6.35 x 3.20 mm, bottom electrodes 0.50 +/- 0.20 mm. R166 (25121WF330LT4E, LCSC C25468)")
\t(tags "resistor 2512")
\t(property "Reference" "REF**"
\t\t(at 0 -2.9 0)
\t\t(layer "F.SilkS")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1 1)
\t\t\t\t(thickness 0.15)
\t\t\t)
\t\t)
\t)
\t(property "Value" "M3_R2512_UR"
\t\t(at 0 2.9 0)
\t\t(layer "F.Fab")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1 1)
\t\t\t\t(thickness 0.15)
\t\t\t)
\t\t)
\t)
\t(attr smd)
\t(duplicate_pad_numbers_are_jumpers no)
\t(fp_rect
\t\t(start -4.35 -1.9)
\t\t(end 4.35 1.9)
\t\t(stroke
\t\t\t(width 0.05)
\t\t\t(type solid)
\t\t)
\t\t(fill no)
\t\t(layer "F.CrtYd")
\t)
\t(fp_rect
\t\t(start -3.175 -1.6)
\t\t(end 3.175 1.6)
\t\t(stroke
\t\t\t(width 0.1)
\t\t\t(type solid)
\t\t)
\t\t(fill no)
\t\t(layer "F.Fab")
\t)
\t(fp_text user "${REFERENCE}"
\t\t(at 0 0 0)
\t\t(layer "F.Fab")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1 1)
\t\t\t\t(thickness 0.15)
\t\t\t)
\t\t)
\t)
\t(pad "1" smd roundrect
\t\t(at -3.3 0)
\t\t(size 1.6 3.3)
\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t(roundrect_rratio 0.15625)
\t)
\t(pad "2" smd roundrect
\t\t(at 3.3 0)
\t\t(size 1.6 3.3)
\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t(roundrect_rratio 0.15625)
\t)
\t(embedded_fonts no)
\t(model "${KIPRJMOD}/kilib/generic.3dshapes/R_2512_6332Metric.step"
\t\t(offset
\t\t\t(xyz 0 0 0)
\t\t)
\t\t(scale
\t\t\t(xyz 1 1 1)
\t\t)
\t\t(rotate
\t\t\t(xyz 0 0 0)
\t\t)
\t)
)
'''


def r2512_uniroyal():
    """R166 (pass 4, power F-7): the damper resistor sat on the Bourns CRM2512 land (2.45 x 3.7 mm pads, 2.7 mm
    gap) that R134/R135 need. UNI-ROYAL's 2512 has 0.5 mm bottom electrodes, so about 1.2 mm of each pad lay under
    bare alumina: excess paste there balls or beads under the body. R166 gets UNI-ROYAL's own land; R134/R135
    keep the Bourns one."""
    path = LIB / 'M3_R2512_UR.kicad_mod'
    if path.exists() and path.read_text() == R2512_UR:
        return False
    path.write_text(R2512_UR)
    print('M3_R2512_UR footprint written (UNI-ROYAL land)')
    return True


TOOLING_HOLE = '''(footprint "M3_ToolingHole_JLC"
\t(version 20260206)
\t(generator "pcbnew")
\t(layer "F.Cu")
\t(descr "JLCPCB assembly tooling hole: 1.152 mm round NPTH with 0.148 mm solder mask expansion, in opposite corners (jlcpcb.com/help/article/how-to-add-tooling-holes-for-pcb-assembly-order). Economic PCBA requires them; without them JLC adds its own")
\t(tags "tooling hole NPTH JLC")
\t(property "Reference" "REF**"
\t\t(at 0 -1.5 0)
\t\t(layer "F.Fab")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 0.6 0.6)
\t\t\t\t(thickness 0.1)
\t\t\t)
\t\t)
\t)
\t(property "Value" "M3_ToolingHole_JLC"
\t\t(at 0 1.5 0)
\t\t(layer "F.Fab")
\t\t(hide yes)
\t\t(effects
\t\t\t(font
\t\t\t\t(size 0.6 0.6)
\t\t\t\t(thickness 0.1)
\t\t\t)
\t\t)
\t)
\t(attr board_only exclude_from_pos_files exclude_from_bom)
\t(duplicate_pad_numbers_are_jumpers no)
\t(fp_circle
\t\t(center 0 0)
\t\t(end 0.95 0)
\t\t(stroke
\t\t\t(width 0.05)
\t\t\t(type solid)
\t\t)
\t\t(fill no)
\t\t(layer "F.CrtYd")
\t)
\t(fp_circle
\t\t(center 0 0)
\t\t(end 0.576 0)
\t\t(stroke
\t\t\t(width 0.1)
\t\t\t(type solid)
\t\t)
\t\t(fill no)
\t\t(layer "F.Fab")
\t)
\t(pad "" np_thru_hole circle
\t\t(at 0 0)
\t\t(size 1.152 1.152)
\t\t(drill 1.152)
\t\t(layers "*.Cu" "*.Mask")
\t\t(solder_mask_margin 0.148)
\t)
\t(embedded_fonts no)
)
'''


def tooling_hole():
    """DFM (pass 4): JLC's Economic PCBA requires tooling holes and, when the board has none, adds its own where
    it chooses. The board now carries three, at positions checked clear of copper and parts."""
    path = LIB / 'M3_ToolingHole_JLC.kicad_mod'
    if path.exists() and path.read_text() == TOOLING_HOLE:
        return False
    path.write_text(TOOLING_HOLE)
    print('M3_ToolingHole_JLC footprint written')
    return True


def usb_model_offset():
    """J3 (pass 4, DFM note): the 3D model sat 2.2 mm inboard of the real receptacle (its mouth 2.58 mm ahead of
    the front legs, per EasyEDA's footprint and model), so renders and STEP exports hid the 0.45 mm overhang past
    the board edge that a sled rail must clear. Offset y -2.2 mm in the model frame (local +y, toward the edge)."""
    path = LIB / 'USB-C_SMD-TYPE-C-31-M-12_1.kicad_mod'
    t = path.read_text()
    if '(xyz 0 -2.2 0)' in t:
        return False
    t, n = re.subn(r'(\(model "\$\{KIPRJMOD\}/kilib/rocket\.3dshapes/USB-C_SMD-TYPE-C-31-M-12_1\.wrl"\n\t\t\(offset\n\t\t\t)\(xyz 0 0 0\)',
                   r'\1(xyz 0 -2.2 0)', t)
    assert n == 1, n
    path.write_text(t)
    print('J3 3D model: offset y -2.2 mm')
    return True


def main():
    changed = [n for n in COURTYARD_FIX if fix_courtyard(n)]
    print('courtyards fixed:', changed or 'none (already done)')
    pasted = [n for n, r in PASTE.items() if set_paste(n, r)]
    print('paste apertures set:', pasted or 'none (already done)')
    lga14_land()
    silk_marks()
    db128l_footprint()
    terminal_marks()
    jst_ph_footprint()
    usb_shell_paste()
    ms5611_land()
    aon6403_windowpane()
    j3_silk_trim()
    r2512_uniroyal()
    tooling_hole()
    usb_model_offset()


if __name__ == '__main__':
    main()
