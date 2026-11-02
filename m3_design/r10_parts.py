#!/usr/bin/env python3
"""Generate R10 local lands/envelope models; never edit a board or schematic.

Maker sources and qualification limits: sources/r10_design/parts_qualification.md.
Run with KiCad Python; --check verifies deterministic files and actual parsed pads.
The PortLDO symbol is exposed for the schematic generator, not written here.
"""
import argparse
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from r7_parts import _box, _circle, _line, _pad, _rect, footprint, module_symbol

PROJECT = HERE / 'assembly_review'
PRETTY = PROJECT / 'kilib/rocket.pretty'
SHAPES = PROJECT / 'kilib/rocket.3dshapes'
NOTES = PROJECT / 'sources/r10_design'


def make_fp(name, body, reference_y, description, through=False):
    text = footprint(name, description, body, reference_y, -reference_y,
                     name + '.wrl').replace('m3_r7_parts', 'm3_r10_parts')
    return text.replace('(attr smd)', '(attr through_hole)') if through else text


def gh2():
    name = 'M3_GH_BM02B_GHS_TBT'
    # JST eGH p2 rotated 180 degrees, same frame as existing GH4: pin1 left,
    # signal pads toward +y; mated height 7.3mm (not the bare header height).
    body = _rect((-2.875, -2.5), (2.875, 1.75), 'F.Fab', .1)
    body += _rect((-3.25, -3.05), (3.25, 3.05), 'F.CrtYd', .05)
    body += _line((-1.6, -2.65), (1.6, -2.65), 'F.SilkS', .15)
    body += _circle((-.625, 3.25), .12, 'F.SilkS', .15)
    for n, x in [('1', -.625), ('2', .625)]:
        body += _pad(n, x, 1.95, .6, 1.7, ('F.Cu', 'F.Paste', 'F.Mask'))
    for x in (-2.475, 2.475):
        body += _pad('', x, -1.4, 1, 2.8, ('F.Cu', 'F.Paste', 'F.Mask'))
    return make_fp(name, body, -4, 'JST BM02B-GHS-TBT; eGH p2 top-entry maker land; unnamed mechanical tabs')


def terminal(color, positions=2, bare=()):
    """`bare`: pad numbers that keep copper only on the layers they connect (the outer lands always; KiCad 'remove
    unconnected layers, keep start and end', as every via since D-S8-19)."""
    name = f'M3_DB125_{positions}P_' + color
    half = positions * 3.5 / 2
    body = _rect((-half, -3.9), (half, 3.5), 'F.Fab', .1)
    # T0-1 p1: tolerance union includes the asymmetric interlock and end datum.
    # A 0.20 mm courtyard margin preserves the 16 mm port pitch (D-R11-01).
    x0, x1 = TERMINAL_X[positions]
    body += _rect((x0-.2, -4.3), (x1+.2, 4.2), 'F.CrtYd', .05)
    body += _rect((-half-.15, -4.05), (half+.15, 3.65), 'F.SilkS', .15)
    # Positive-y face is the wire-entry face in this local frame. A fabrication
    # arrow under the housing prevents silently inheriting the old pad aliases.
    body += _line((0, 1.5), (0, 3), 'F.Fab', .15)
    body += _line((0, 3), (-.5, 2.5), 'F.Fab', .15)
    body += _line((0, 3), (.5, 2.5), 'F.Fab', .15)
    for number in range(1, positions+1):
        n, x = str(number), (number-(positions+1)/2)*3.5
        body += (f'(pad "{n}" thru_hole circle (at {x} 0) (size 1.9 1.9) '
                 '(drill 1.3) (layers "*.Cu" "*.Mask")' +
                 (' (remove_unused_layers yes) (keep_end_layers yes)' if n in bare else '') + ')\n')
    return make_fp(name, body, -5,
                   f'DORABO DB125-3.5-{positions}P; drawing T0-1; 1.3mm finished drill, 1.9mm copper; wire entry +y', True)


def ldo():
    name = 'M3_TPS7A91_DSK10'
    body = _rect((-1.25, -1.25), (1.25, 1.25), 'F.Fab', .1)
    body += _rect((-1.7, -1.55), (1.7, 1.55), 'F.CrtYd', .05)
    body += _line((-.85, -1.4), (.85, -1.4), 'F.SilkS', .15)
    body += _circle((-1.65, -1.42), .1, 'F.SilkS', .15)
    for n in range(1, 11):
        x, y = (-1.15, (n - 3) * .5) if n <= 5 else (1.15, (8 - n) * .5)
        body += _pad(str(n), x, y, .6, .25, ('F.Cu', 'F.Paste', 'F.Mask'))
    body += _pad('11', 0, 0, 1.2, 2, ('F.Cu', 'F.Mask'))
    # TI DSK0010A stencil: two 1.13 x .89 apertures at y +/- .555 (84%).
    for y in (-.555, .555):
        body += _pad('', 0, y, 1.13, .89, ('F.Paste',))
    return make_fp(name, body, -2.3, 'TI TPS7A9101 DSK0010A, drawing 4218903/C; thermal pad 11 GND; vias in board')


def polymer():
    name = 'M3_MA_8x10'
    # MA drawing has no recommended land: derived from P3.1+/-.2 gap,
    # lead width .8..1.1 and base8.3+/-.2. Explicit inference in qualification.
    body = _rect((-4.15, -4.15), (4.15, 4.15), 'F.Fab', .1)
    body += _circle((0, 0), 4, 'F.Fab', .1)
    body += _rect((-5.25, -4.5), (5.25, 4.5), 'F.CrtYd', .05)
    # D-R19-07 (R19-MFG-02 / R19-BOM-02): C84 is soldered by hand after both reflow passes (export_fab.MANUAL_FIT), so its
    # lands carry no stencil aperture; the copper and mask openings are unchanged.
    for n, x in [('1', -3.25), ('2', 3.25)]:
        body += _pad(n, x, 0, 3.5, 1.7, ('F.Cu', 'F.Mask'))
    body += _line((-4.5, -2.2), (-4.5, -1.2), 'F.SilkS', .15)
    body += _line((-5, -1.7), (-4, -1.7), 'F.SilkS', .15)
    return make_fp(name, body, -5.4, 'jieerrui MA25V470M8x10; positive pad1 left; derived land; hand-fitted after reflow, '
                   'no paste aperture')


def srp5030t():
    name = 'M3_SRP5030TA'
    # D-R18-08 (R18-BOM-03): Bourns SRP5030T datasheet p1 "Recommended Layout" (6.50 mm over both lands, 2.50 mm
    # between them, 1.8 mm land height): two 2.0 x 1.8 mm lands at x = +/-2.25 mm. Body 5.7 +/-0.3 x 5.2 +/-0.2 x
    # 2.8 +/-0.2 mm, terminals 1.1 +/-0.3 x 1.5 +/-0.2 mm (same page). Replaces R7's 1.8 x 2.5 mm proxy at +/-2.35 mm.
    body = _rect((-3, -2.75), (3, 2.75), 'F.Fab', .1)
    body += _rect((-3.5, -3.0), (3.5, 3.0), 'F.CrtYd', .05)
    body += _line((-3.5, -3.0), (3.5, -3.0), 'F.SilkS', .15)
    body += _line((-3.5, 3.0), (3.5, 3.0), 'F.SilkS', .15)
    for n, x in (('1', -2.25), ('2', 2.25)):
        body += _pad(n, x, 0, 2.0, 1.8, ('F.Cu', 'F.Paste', 'F.Mask'))
    return make_fp(name, body, -4.1, 'Bourns SRP5030T p1 recommended layout: 6.50 mm over both lands, 2.50 mm gap, '
                   '2.0 x 1.8 mm lands')


def load_switch():
    name = 'M3_AONR21357_DFN3x3A_EP1'
    # AOS PO-00047 rev I: recommended top-side copper land, in a frame
    # with source pins 1-3 / gate 4 south and the drain fingers north.
    body = _rect((-1.5, -1.5), (1.5, 1.5), 'F.Fab', .1)
    body += _rect((-1.9, -1.9), (1.9, 1.9), 'F.CrtYd', .05)
    body += _circle((-1.7, 1.4), .1, 'F.SilkS', .15)
    for n in range(1, 5):
        body += _pad(str(n), (n - 2.5) * .65, 1.4, .35, .5, ('F.Cu', 'F.Paste', 'F.Mask'))
    for n in range(5, 9):
        # 0.01 mm overlaps the common drain pad. The copper union is
        # exactly the maker's .40 x .30 fingers plus the main polygon.
        body += _pad(str(n), (6.5 - n) * .65, -1.495, .4, .31, ('F.Cu', 'F.Paste', 'F.Mask'))
    outline = ((-1.225, -1.35), (1.225, -1.35), (1.225, -.215),
               (1.605, -.215), (1.605, .215), (1.225, .215),
               (1.225, .63), (-1.225, .63), (-1.225, .215),
               (-1.605, .215), (-1.605, -.215), (-1.225, -.215))
    points = ' '.join(f'(xy {x} {y})' for x, y in outline)
    body += ('(pad "9" smd custom (at 0 0) (size .43 .43) (layers "F.Cu" "F.Paste" "F.Mask") '
             '(options (clearance outline) (anchor rect)) '
             f'(primitives (gr_poly (pts {points}) (width 0) (fill yes))))\n')
    return make_fp(name, body, -2.5,
                   'AOS AONR21357; PO-00047 rev I maker land; S1-3 G4 D5-8 and common exposed drain9')


def microsd():
    name = 'M3_MICROSD_MOLEX_472192001'
    # Molex SD-47219-001 rev G, recommended PCB layout, top view. Origin:
    # midpoint of the two shell-pad columns, on the eight signal-pad centres.
    # G1..G4 use numeric aliases12/9/10/11 (supplier numbering) in the electrical symbol/assembly table.
    body = _rect((-6.8, -9.35), (6.8, 5.15), 'F.Fab', .1)
    body += _rect((-7.85, -9.85), (7.85, 5.65), 'F.CrtYd', .05)
    body += _line((-6.8, -9.5), (6.8, -9.5), 'F.SilkS', .15)
    body += _circle((3.205, 1.12), .12, 'F.SilkS', .15)
    for number in range(1, 9):
        body += _pad(str(number), round(3.205 - (number - 1) * 1.1, 5), 0,
                     .8, 1.5, ('F.Cu', 'F.Paste', 'F.Mask'))
    for number, x, y in ((12, 6.875, 2.6), (9, 6.875, -5.7),
                         (10, -6.875, -5.7), (11, -6.875, 2.6)):
        body += _pad(str(number), x, y, 1.45, 2., ('F.Cu', 'F.Paste', 'F.Mask'))
    return make_fp(name, body, 6.5,
                   'Molex 472192001 hinged microSD; SD-47219-001 revG maker land; shell G1-G4=12/9/10/11; 0.10/0.12mm stencil, 100% aperture')


TERMINAL_X = {2: (-4.62, 3.70), 4: (-8.32, 7.20), 5: (-10.07, 8.95)}

# D-R20-05 (R20-SAF-05): the S-8-protected terminal barrels J121.1 (PYRO1_OUT, BK pad 1) and J400.2 (BAT_SW_RETURN, GN
# pad 2) carry no unconnected inner rings, so ring-to-copper equals their barrel walls' >= 1.0 mm. GN pad 2 is also J1.2
# (GND: In1 thermal kept, its unconnected In2 ring goes). J121.2 (PYRO1_IGN, GND exempt) keeps its rings.
FOOTPRINTS = {'M3_GH_BM02B_GHS_TBT': gh2, 'M3_DB125_2P_BK': lambda: terminal('BK', bare=('1',)),
              'M3_DB125_2P_GN': lambda: terminal('GN', bare=('2',)), 'M3_TPS7A91_DSK10': ldo,
              'M3_MA_8x10': polymer, 'M3_AONR21357_DFN3x3A_EP1': load_switch,
              'M3_MICROSD_MOLEX_472192001': microsd,
              'M3_DB125_4P_GN': lambda: terminal('GN', 4),
              'M3_DB125_5P_GN': lambda: terminal('GN', 5), 'M3_SRP5030TA': srp5030t}
# Boxes use millimetres, KiCad VRML scale .1in handled by r7_parts._box.
MODELS = {
    'M3_GH_BM02B_GHS_TBT': (0, -.375, 0, 5.75, 4.25, 7.3, '.85 .85 .8'),
    # Maximum-tolerance unions, not individual body dimensions (T0-1 p1).
    # Wire face: 7.70 total depth - 3.70 rear datum = +4.00 mm.
    'M3_DB125_2P_BK': (-.46, -.05, 0, 8.32, 8.10, 8.9, '.12 .12 .12'),
    'M3_DB125_2P_GN': (-.46, -.05, 0, 8.32, 8.10, 8.9, '.1 .55 .2'),
    'M3_DB125_4P_GN': (-.56, -.05, 0, 15.52, 8.10, 8.9, '.1 .55 .2'),
    'M3_DB125_5P_GN': (-.56, -.05, 0, 19.02, 8.10, 8.9, '.1 .55 .2'),
    'M3_TPS7A91_DSK10': (0, 0, 0, 2.6, 2.6, .8, '.12 .12 .12'),
    'M3_MA_8x10': (0, 0, 0, 8.5, 8.5, 10.8, '.65 .65 .68'),
    'M3_AONR21357_DFN3x3A_EP1': (0, 0, 0, 3.3, 3.3, .9, '.12 .12 .12'),
    'M3_SRP5030TA': (0, 0, 0, 6.0, 5.4, 3.0, '.35 .38 .42'),     # SRP5030T p1 maxima (5.7+.3, 5.2+.2, 2.8+.2)
    # SD-47219-001G sheet1: include fitting nails and independent dimension
    # tolerances; centred seating/card-front allocation remains an inference.
    # Local union x +/-7.525, y -9.70..6.00, z0..2.10 (R13-BOM-02).
    'M3_MICROSD_MOLEX_472192001': (0, -1.85, 0, 15.05, 15.7, 2.1, '.45 .45 .48'),
}


def port_ldo_symbol():
    return module_symbol('PortLDO', 'U', 'TPS7A9101DSKR adjustable LDO; DSK thermal pad 11 to GND',
                         'LDO regulator', 'M3_TPS7A91_DSK10', 10.16, 10.16,
                         [(7.62, '9', 'IN', 'power_in'), (5.08, '10', 'IN', 'power_in'),
                          (2.54, '7', 'EN', 'input'), (0, '6', 'SS_CTRL', 'input'),
                          (-2.54, '4', 'GND', 'power_in'), (-5.08, '11', 'PAD', 'power_in')],
                         [(7.62, '1', 'OUT', 'power_out'), (5.08, '2', 'OUT', 'passive'),
                          (2.54, '3', 'FB', 'input'), (0, '8', 'NR_SS', 'passive'),
                          (-2.54, '5', 'PG', 'open_collector')])


def microsd_symbol():
    return module_symbol('MicroSD_Hinge', 'J', 'Molex 472192001 locking hinged microSD; no card detect; G1-G4=12/9/10/11',
                         'microSD socket', 'M3_MICROSD_MOLEX_472192001', 10.16, 12.7,
                         [(10.16, '1', 'DAT2', 'passive'), (7.62, '2', 'CD_DAT3_CS', 'passive'),
                          (5.08, '3', 'CMD_DI', 'passive'), (2.54, '4', 'VDD', 'power_in'),
                          (0, '5', 'CLK', 'passive'), (-2.54, '6', 'VSS', 'power_in')],
                         [(10.16, '7', 'DAT0_DO', 'passive'), (7.62, '8', 'DAT1', 'passive'),
                          (5.08, '9', 'G2', 'passive'), (2.54, '10', 'G3', 'passive'),
                          (0, '11', 'G4', 'passive'), (-2.54, '12', 'G1', 'passive')])


def servo_terminal_symbol():
    return module_symbol('ServoTerminal', 'J', 'DORABO DB1253.5mm5pos; four servo signals and GND only',
                         'servo terminal', 'M3_DB125_5P_GN', 10.16, 10.16,
                         [(5.08, '1', 'SERVO1', 'passive'), (2.54, '2', 'SERVO2', 'passive'),
                          (0, '3', 'SERVO3', 'passive'), (-2.54, '4', 'SERVO4', 'passive'),
                          (-5.08, '5', 'GND', 'passive')], [])


def generated():
    files = {PRETTY / (n + '.kicad_mod'): f() for n, f in FOOTPRINTS.items()}
    for name, box in MODELS.items():
        files[SHAPES / (name + '.wrl')] = ('#VRML V2.0 utf8\n# R10 fit envelope, not maker model. '
                                         'See parts_qualification.md.\n' + _box(*box))
    return files


def geometry_checks():
    import pcbnew
    mm = pcbnew.ToMM
    result = {}
    for name in FOOTPRINTS:
        fp = pcbnew.FootprintLoad(str(PRETTY), name)
        assert fp is not None, name
        rows = {p.GetNumber(): [round(mm(p.GetFPRelativePosition().x), 5),
                              round(mm(p.GetFPRelativePosition().y), 5),
                              round(mm(p.GetSize().x), 5), round(mm(p.GetSize().y), 5)]
                for p in fp.Pads() if p.GetNumber()}
        assert all(p.GetLocalClearance() in (None, 0) for p in fp.Pads()), name
        result[name] = rows
        if name.startswith('M3_DB125_'):            # D-R20-05: only the protected barrels drop unconnected rings
            bare = {'M3_DB125_2P_BK': {'1'}, 'M3_DB125_2P_GN': {'2'}}.get(name, set())
            assert {p.GetNumber() for p in fp.Pads() if p.Padstack().UnconnectedLayerMode()
                    == pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_EXCEPT_START_AND_END} == bare, name
            assert all(p.Padstack().UnconnectedLayerMode() == pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL
                       for p in fp.Pads() if p.GetNumber() not in bare), name
        if name == 'M3_AONR21357_DFN3x3A_EP1':
            drain = next(p for p in fp.Pads() if p.GetNumber() == '9')
            box = drain.GetBoundingBox()
            assert [round(mm(v),5) for v in (box.GetX(),box.GetY(),box.GetWidth(),box.GetHeight())] == [-1.605,-1.35,3.21,1.98]
    for name in ('M3_DB125_2P_BK', 'M3_DB125_2P_GN'):
        p = result[name]
        assert p['2'][0] - p['1'][0] - (p['1'][2] + p['2'][2]) / 2 >= 1.5
        assert p['1'] == [-1.75, 0, 1.9, 1.9]
    for positions in (4, 5):
        p = result[f'M3_DB125_{positions}P_GN']
        assert len(p) == positions
        assert p['1'] == [-(positions-1)*1.75, 0, 1.9, 1.9]
        assert p[str(positions)] == [(positions-1)*1.75, 0, 1.9, 1.9]
    assert result['M3_GH_BM02B_GHS_TBT']['1'] == [-.625, 1.95, .6, 1.7]
    assert result['M3_TPS7A91_DSK10']['11'] == [0, 0, 1.2, 2]
    assert len(result['M3_TPS7A91_DSK10']) == 11
    assert result['M3_MA_8x10']['1'] == [-3.25, 0, 3.5, 1.7]
    assert result['M3_SRP5030TA'] == {'1': [-2.25, 0, 2.0, 1.8], '2': [2.25, 0, 2.0, 1.8]}
    fet = result['M3_AONR21357_DFN3x3A_EP1']
    assert len(fet) == 9 and fet['1'] == [-.975, 1.4, .35, .5]
    assert fet['4'] == [.975, 1.4, .35, .5] and fet['8'] == [-.975, -1.495, .4, .31]
    sd = result['M3_MICROSD_MOLEX_472192001']
    assert len(sd) == 12 and sd['1'] == [3.205, 0, .8, 1.5]
    assert sd['8'] == [-4.495, 0, .8, 1.5]
    assert sd['12'] == [6.875, 2.6, 1.45, 2.] and sd['10'] == [-6.875, -5.7, 1.45, 2.]
    return result


def passive_cold_screen():
    """Two retained dividers, PC1/PE4 low; illustrative zero-leakage bands only."""
    def sense(v, vf, pull, cont_top, cont_bottom, bus_top, bus_bottom, match):
        cont, bus, link = cont_top + cont_bottom, bus_top + bus_bottom, match + 2.
        g11, g22, g12 = 1/pull + 1/cont + 1/link, 1/bus + 1/link, -1/link
        determinant = g11*g22-g12*g12
        out = (v-vf)/pull*g22/determinant
        raw = -(v-vf)/pull*g12/determinant
        return out*cont_bottom/cont, raw*bus_bottom/bus
    nominal = sense(3.3, .2, 10000, 10200, 1000, 10200, 1000, 1.5)
    tolerance = .0145
    bands = [sense(v, vf, 10000*p, 10200*ct, 1000*cb, 10200*bt, 1000*bb, m)
             for v, vf, p, ct, cb, bt, bb, m in itertools.product(
                 (3.135, 3.465), (0., .32), *([(1-tolerance, 1+tolerance)]*5), (1., 2.))]
    open_cont = [(v-vf)*1000*bottom/(10000*pull+10200*top+1000*bottom)
                 for v,vf,pull,top,bottom in itertools.product(
                     (3.135,3.465),(0.,.32),*([(1-tolerance,1+tolerance)]*3))]
    common_r = 1/(1/10000+2/11200)
    return dict(status='Calc / Inference; no firmware thresholds or measured fault discrimination',
                topology='R13110k pull-up; one11.2k OUT divider and one11.2k RAW_ACT divider, linked by2R R134 and1-2R ematch',
                healthy_cont_bus_nominal_mV=[x*1000 for x in nominal],
                healthy_cont_bus_band_mV=[[min(row[n] for row in bands)*1000,
                                           max(row[n] for row in bands)*1000] for n in (0,1)],
                open_cont_nominal_mV=(3.3-.2)*1000/(10000+11200)*1000,
                open_cont_band_mV=[min(open_cont)*1000,max(open_cont)*1000],
                open_bus_nominal_mV=0,
                correlated_10uA_leak_each_node_healthy_shift_mV=common_r*20e-6/11.2*1000,
                open_10uA_leak_cont_shift_mV=(1/(1/10000+1/11200))*10e-6/11.2*1000,
                open_10uA_leak_bus_shift_mV=11200*10e-6/11.2*1000,
                assumptions='3V3 +/-5%, Vf0..0.32V inference from25C BAT54A table, resistor+/-1.45%; zero leakage/ADC offset/reference error; bench all ground refusal bands before firmware')


def native_fire_copper(board):
    """Series fire tracks, including routed terminal-pad entries (D-R11-03)."""
    import pcbnew
    sys.path.insert(0, str(HERE.parent / 'tools'))
    from check_r10 import FIRE_TERMINALS, fire_path
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    terminals = {**FIRE_TERMINALS, 'ACT_FET_S': ({'Q120': ('2',)}, {'Q121': ('3',)})}
    paths, pad_entries = {}, {}
    for net, groups in terminals.items():
        tracks, joined, _ = fire_path(board, net, groups)
        if not joined or not tracks:
            raise ValueError(f'{net}: no native fire path')
        chosen = {t.m_Uuid.AsString(): t for t in tracks}
        ends = {(t.GetLayer(), q.x, q.y) for t in tracks for q in (t.GetStart(), t.GetEnd())}
        pads = [fps[ref].FindPadByNumber(num) for group in groups for ref, nums in group.items() for num in nums]
        entries = {}
        for t in board.GetTracks():
            if t.GetClass() != 'PCB_TRACK' or t.GetNetname() != net:
                continue
            for pad in pads:
                if pad is None or not pad.IsOnLayer(t.GetLayer()):
                    continue
                anchor, a, b = pad.GetPosition(), t.GetStart(), t.GetEnd()
                # fire_path collapses copper inside a pad. Count only an entry from a retained current
                # endpoint to that pad's anchor, not another branch leaving the anchor for a sense tap.
                if pad.HitTest(a) and pad.HitTest(b) and ((a == anchor and (t.GetLayer(), b.x, b.y) in ends)
                        or (b == anchor and (t.GetLayer(), a.x, a.y) in ends)):
                    key = t.m_Uuid.AsString()
                    if key not in chosen:
                        entries[key] = t
        chosen.update(entries)
        if len({t.GetLayer() for t in chosen.values()}) != 1:
            raise ValueError(f'{net}: series layer change requires a via-resistance model')
        widths = {t.GetWidth() for t in chosen.values()}
        if len(widths) != 1:
            raise ValueError(f'{net}: mixed fire widths require a series-resistance model')
        paths[net] = [sum(pcbnew.ToMM(t.GetLength()) for t in chosen.values()), pcbnew.ToMM(widths.pop())]
        pad_entries[net] = sum(pcbnew.ToMM(t.GetLength()) for t in entries.values())
    return paths, pad_entries


def power_budget(board_path=PROJECT / 'm3.kicad_pcb'):
    """Worst component tolerances plus explicit, unmeasured harness/thermal limits."""
    import pcbnew
    board_path = Path(board_path)
    board_bytes = board_path.read_bytes()
    copper_paths, pad_entries = native_fire_copper(pcbnew.LoadBoard(str(board_path)))
    if board_path.read_bytes() != board_bytes:
        raise ValueError('board changed during native fire-path extraction')
    thin = .001 + 25e-6 * 100
    thick = .01 + 100e-6 * 100
    buck_min = .792 * (1 + (56200 * (1-thin) + 2000 * (1-thick)) / (10000 * (1+thin)))
    buck_max = .808 * (1 + (56200 * (1+thin) + 2000 * (1+thick)) / (10000 * (1-thin)))
    ldo_min = .792 * (1 + 49900 * (1-thin) / (10000 * (1+thin))) - 100e-9 * 49900 * (1+thin)
    ldo_max = .808 * (1 + 49900 * (1+thin) / (10000 * (1-thin))) + 100e-9 * 49900 * (1+thin)
    # TI SLVS841F eq. 1 p. 15 (IOSmin / IOSmax, RILIM in kOhm, mA); R +/-2 % (1 % initial + 100 ppm/K x 100 K).
    # GPS/radio limiters are removed by the always-on ports owner decision; only camera R430 remains.
    limits = {port: [25230 / (r * (1+thick)) ** 1.016 / 1000,
                     22980 / (r * (1-thick)) ** .94 / 1000]
              for port, r in [('camera', 22.6)]}
    # TPS7A91 SBVS282A p5 current limit1.5..1.9A; hard-short foldback1.45A is typical only.
    # Shared shorts are a prospective demand, not a continuous operating point of the2A buck.
    ldo_short_max = 1.9
    all_shorts = limits['camera'][1] + ldo_short_max + .011
    # AP63201 (Diodes DS41326 Rev 3-2): 2 A continuous (p. 1), HS peak current limit 2.5 A min (p. 5), fSW 500 kHz
    # typ with +/-6 % spread spectrum (p. 5: 470 kHz taken as the low edge, Inference), ripple dI = Vo (Vi - Vo) /
    # (Vi L fSW) (p. 13); L400 6.8 uH -20 % (Bourns SRP5030T). Inputs: 8.4 V (2S full, F9) and U9's OVLO trip corner
    # ovlo_max (below); Vo over the buck tolerance band.
    # D-R25-03 (R25-TRI-04): U9's OVLO trip corner includes the OVLO pin leakage (TI SLVSFC9C section 6.5: VOV(R)
    # 1.183-1.223 V, IOVLKG -0.1 to 0.1 uA): (VOV(R) + I x R82 || R83) x (R82 + R83) / R83 at R82 2 M / R83 280 k at their
    # 0.1 % tolerance (their temperature drift is not included) gives 10.18 V; without the leakage it is 9.98 V (M3_R4 A2's
    # 9.63-9.96 V trip range was the no-leakage figure).
    r82_max, r83_min = 2e6 * 1.001, 280e3 * .999
    ovlo_max = (1.223 + .1e-6 * r82_max * r83_min / (r82_max + r83_min)) * (r82_max + r83_min) / r83_min
    assert round(ovlo_max, 2) == 10.18, ovlo_max            # the budget keys below name it
    def peak(vin, f, lmin=6.8e-6 * .8):
        return max(all_shorts + vo * (vin - vo) / (vin * lmin * f) / 2 for vo in (buck_min, buck_max))
    # Battery-lead-break ride-through (REQUIREMENTS F6, R3-PWR-02): C84 on VLOGIC back-feeds RAW_PROTECTED through
    # U11 (TPS2121 reverse blocking only above IRCB 0.2 / 1 / 2 A, SLVSEA3F section 7.5 p. 8), so it also carries the
    # port buck U400 (EN tied to VIN; GPS/radio always on, camera turn-off up to3ms). Constant-power
    # loads from 7.4 V; no credit for RAW_PROTECTED / C6 / C7 capacitance or for U11 blocking (Calc / Inference).
    # D-R19-14 (owner, 2026-10-30): the spare AUX port J440 shares PORT_4V8. Its allowance is set by U401's thermal floor
    # (GAP-3: junction <= 125 C at the 70 C bay limit with the 80-110 C/W inferred theta-JA): the LDO loss
    # (buck_max - ldo_min) x (0.46 A + AUX) + buck_max x 4 mA ground current stays <= 0.5 W for AUX <= 0.112 A, so the
    # documented limit is 100 mA at 4.8 V. U401's 1 A rating (TI SBVS282A p. 1) and 1.5-1.9 A limit (p. 5) are not binding.
    aux_A = .1
    ports_w = [buck_min * (1.461 + aux_A) / .85, buck_max * (1.461 + aux_A) / .80]  # camera 1 A + radio .3 + GPS .15 + AUX .1 + 11 mA
    # D-OA-05: account explicitly for R92 (3.3 kohm) while C84 can feed RAW_PROTECTED through U11.
    # Hold its worst loss at the 7.4 V launch floor constant as voltage falls; no credit for any old envelope allowance.
    r92_bleed_w = 7.4 ** 2 / (3300 * (1-thick))
    sd_write_w = [3.3*.2/.85, 3.3*.2/.80]
    sd_idle_w = [3.3*.03/.85, 3.3*.03/.80]
    loads_w = dict(a_ports_off_logic_shed=[.62 + .1 + sd_idle_w[0], .62 + .1 + sd_idle_w[1]],
                   b_ports_off_no_shed=[.6 + .1 + sd_write_w[0], 1.4 + .1 + sd_write_w[1]],
                   c_camera_radio_gps_on=[ports_w[0] + .6 + sd_write_w[0], ports_w[1] + 1.4 + sd_write_w[1]],
                   d_gps_radio_on_camera_off_logic_shed=[buck_min*(.461+aux_A)/.85+.62+sd_idle_w[0],
                                                        buck_max*(.461+aux_A)/.80+.62+sd_idle_w[1]])
    loads_w = {case: [w + r92_bleed_w for w in watts] for case, watts in loads_w.items()}
    def ride(c, v_end, w):
        return .5 * c * (7.4 ** 2 - v_end ** 2) / w * 1000
    ride_through = {f'{case}_C{int(round(c * 1e7)) / 10:g}uF_to_{v}V': [ride(c, v, w[1]), ride(c, v, w[0])]
                    for case, w in loads_w.items() for c in (300.8e-6, 470e-6) for v in (3.5, 3.8)}
    # Owner option OQ-5 (not implemented): an AP63201 EN divider from RAW_PROTECTED on existing BOM values, R5 47 k
    # 1 % (C25819) / R6 10 k (DS41326 p. 10 eq. 1-2; VEN_L 1.05-1.15 V, VEN_H 1.15-1.23 V; 1.5 / 5.5 uA EN currents
    # typical): the port buck stops at VOFF 5.73-6.30 V (6.01 V typ) and restarts at VON 6.49-6.94 V; then C84
    # carries only the logic below VOFF.
    en_r5, en_r6 = 47e3, 10e3
    voff = [v * (1 + en_r5 / en_r6) - 5.5e-6 * en_r5 for v in (1.05, 1.10, 1.15)]
    von = [v * (1 + en_r5 / en_r6) - 1.5e-6 * en_r5 for v in (1.15, 1.18, 1.23)]
    def ride_en(c, v_end, w_all, w_logic, v_off=voff[0]):  # lowest VOFF: ports drain C84 longest
        return (.5 * c * (7.4 ** 2 - v_off ** 2) / w_all + .5 * c * (v_off ** 2 - v_end ** 2) / w_logic) * 1000
    ride_through_en = {f'{case}_C{int(round(c * 1e7)) / 10:g}uF_to_{v}V': ride_en(c, v, wa, wl)
                       for case, wa, wl in (('ports_on_then_logic_shed', loads_w['c_camera_radio_gps_on'][1], .72+sd_idle_w[1]+r92_bleed_w),
                                            ('ports_on_then_logic_no_shed', loads_w['c_camera_radio_gps_on'][1], 1.5+sd_write_w[1]+r92_bleed_w))
                       for c in (300.8e-6, 470e-6) for v in (3.5, 3.8)}
    # Equation roots include input power as constant power, not a guessed current.
    def loaded_pack(open_v, servos):
        r, logic, power, efficiency = .15, .5+3.3*.2/(.8*6), 5.456 * 1.46, .8
        a = open_v - r * (servos + logic)
        return (a + (a*a - 4*r*power/efficiency)**.5) / 2
    # GAP-1 / D-R11-03: current native paths; rho=1.72e-8 ohm m, nominal 35 um outer copper at 20 C.
    # One aligned source path takes no parallel-leg credit. Routed pad entries are included conservatively;
    # actual copper thickness, pad resistance and device/harness limits still need physical qualification.
    copper_by_net = {net: length/width * (1.72e-8/35e-6) for net,(length,width) in copper_paths.items()}
    copper_20c = sum(copper_by_net.values())
    copper_70c = copper_20c * (1 + .00393 * (70 - 20))
    r134_hot = 2 * 1.01 * (1 + 100e-6 * (70 - 25))
    q124_hot = .0058 * 1.42       # inherited hot-factor inference; bench qualification remains open
    other_w = loads_w['c_camera_radio_gps_on'][1]
    def fire_case(pfet_r):
        rest = r134_hot + 2 + .3 + copper_70c + .005 + .010 + 2 * pfet_r + q124_hot
        def current(open_v, stalls):
            # Pack feeds the firing branch, servo current and the other constant-power loads simultaneously.
            a, b = 1 + .15 / rest, open_v - .15 * 1.92 * stalls
            voltage = (b + math.sqrt(b*b - 4*a*.15*other_w)) / (2*a)
            return dict(loaded_pack_V=voltage, fire_A=voltage/rest,
                        other_A=other_w/voltage + 1.92*stalls)
        cases = {str(n): current(7.4, n) for n in range(5)}
        target_v = 1.5 * rest
        return dict(fire_branch_without_pack_ohm=rest, total_loop_ohm=rest+.15,
                    pack_7V4_by_stall_count=cases,
                    two_stall_compatible_all_fire_A=cases['2']['fire_A']/1.5,
                    two_stall_open_equivalent_V_for_1A_all_fire=target_v+.15*(1.5+3.84+other_w/target_v))
    fire_primary, fire_typical = fire_case(.040), fire_case(.0123*1.4)
    # GAP-5: 960 LSI cycles, including Rev V's 29.4 kHz minimum through Tj=125 C (DS12110 Rev 8 Table 146 p. 238).
    watchdog_ms = [960/33600*1000, 960/29400*1000]
    c126_max = 220e-9*1.10*1.15
    r_discharge_max = (1/(1/10000 + 1/(220+1000))) * 1.02
    rc_tail_ms = r_discharge_max*c126_max*math.log(3.6/.4)*1000
    charge_tail_ms = r_discharge_max*22e-9/.4*1000
    r134_min = 2*.99*(1-100e-6*(70-25))
    fault_power = 8.4**2/r134_min
    def pulse_curve(ms):
        return 90*(ms/10)**(math.log(25/90)/math.log(10))
    # D-R18-02: R119 (Q121) and R120 (Q120), both 100k 1%, now bias the shared ACT_GATE node in parallel (50k).
    r_gs_min, r_gs_nom = 50000*.98, 50000
    enable_ratio = r_gs_min/(r_gs_min+10000*1.02)
    enable_tau = (r_gs_nom*10000/(r_gs_nom+10000))*1.02*(1e-6*1.10*1.15)
    # D-R18-01 (R18-MCU-01): Q122 gate drive through R122 1k / R123 2k (1 %). AO3400A Rev3.1 p2: VGS(th) 0.65 / 1.05 /
    # 1.45 V; RDS(on) <= 48 mohm at VGS 2.5 V. STM32H743 DS12110 Table157 p246: internal pull-up 30 / 40 / 50 kohm.
    q122_on_V = [3.3*2000*.99/(1000*1.01+2000*.99), (3.3-.4)*2000*.99/(1000*1.01+2000*.99)]
    q122_pullup_off_V = 3.6*2000*1.01/(2000*1.01+1000*.99+30000)
    q122_drain_load_A = 8.4/(r_gs_min+10000*.98)
    enable_vgs = (6-4.2*.040-.1)*enable_ratio
    # Linear interpolation of the maker's typical bias curve at 4.5 V, then tolerance / temperature / aging factors.
    c120_bias_delta_pct = -14.594404761904764 + (4.5-4.471875)/(5.2344-4.471875)*(-18.78912+14.594404761904764)
    c120_effective = (1+c120_bias_delta_pct/100)*.9*.85*.9
    results = dict(
        status='Calculated conditional bounds; no physical or transient tests performed',
        temperature_excursion_from_25C=100,
        buck_V=[buck_min, buck_max], ldo_V=[ldo_min, ldo_max],
        switch_Rmax_ohm=.135, camera_harness_copper_loop_max_ohm=.15,
        radio_gps_harness_copper_loop_max_ohm=.2,
        transient_allowance_V=.05,
        camera_module_min_V=buck_min-.135-.15-.05,
        radio_module_min_V=ldo_min-.3*.2-.05,
        gps_module_min_V=ldo_min-.15*.2-.05,
        aux_module_min_V=ldo_min-aux_A*.2-.05,
        port_aux_allowance_A=aux_A,
        port_aux_allowance_basis=('D-R19-14: the spare port (J440 AUX by default; the three ports are identical, so it is whichever '
                                  'port carries neither the GPS nor the radio) may draw up to 100 mA at 4.8 V beyond GPS 150 mA '
                                  'and radio 300 mA; set by U401 GAP-3 junction <= 125 C at 70 C bay (theta-JA 110 C/W '
                                  'Inference), which allows 112 mA; TI SBVS282A 1 A rating p1 and 1.5-1.9 A limit p5 not binding'),
        radio_gps_module_max_V=ldo_max+.05,
        ldo_headroom_min_V=buck_min-.05-ldo_max,
        switch_limit_A=limits,
        gps_radio_always_on=True,
        ldo_shared_current_limit_A=[1.5,1.9],
        ldo_hard_short_foldback_typical_A=1.45,
        gps_or_radio_short_camera_normal_prospective_buck_A=ldo_short_max+1+.011,
        port_short_note='GPS/radio/AUX share the LDO current/thermal limit; one cable short may remove all three and cause U400 current limit/hiccup with camera on. No guarantee of continuous fault operation; bench logic/flight retention.',
        microsd_current_allocation_A=dict(write=.2,idle=.03,status='selected card qualification required; allocations, not measured maxima'),
        microsd_input_write_W=sd_write_w, microsd_input_idle_W=sd_idle_w,
        buck_all_shorts_A=all_shorts,
        buck_all_shorts_over_2A_continuous_pct=(all_shorts / 2 - 1) * 100,
        buck_prospective_all_shorts_peak_inductor_without_limiting_A={'8V4_470kHz': peak(8.4, 470e3), '8V4_500kHz': peak(8.4, 500e3),
                                         '10V18_470kHz': peak(ovlo_max, 470e3), '10V18_500kHz': peak(ovlo_max, 500e3)},
        buck_peak_current_limit_min_A=2.5,
        buck_camera_short_radio_gps_normal_A=limits['camera'][1]+.3+.15+aux_A+.011,
        ldo_bleeder_min_A=ldo_min/(820*(1+thick)),
        ldo_full_load_loss_W=(buck_max-ldo_min)*(.46+aux_A)+buck_max*.004,
        # GAP-3 adds two filled/capped vias; retain the conservative, unmeasured layout estimate.
        ldo_theta_ja_inference_C_per_W=[80, 110],
        ldo_thermal_vias=dict(count=2, at_mm=[[27.3,13.6],[27.9,13.6]], ring_mm=.5, drill_mm=.3,
                             process='Resin-filled, copper-capped planar VIPPO; maker paste unchanged'),
        ldo_ambient_70C_junction_inference_C=[70+r*((buck_max-ldo_min)*(.46+aux_A)+buck_max*.004)
                                             for r in (80, 110)],
        ldo_ambient_85C_junction_inference_C=[85+r*((buck_max-ldo_min)*(.46+aux_A)+buck_max*.004)
                                             for r in (80, 110)],
        pack_7V4_four_stall_loaded_V=loaded_pack(7.4,7.68),
        pack_6V0_four_stall_loaded_V=loaded_pack(6,7.68),
        servo_star_board_return_max_A=4*7.68*.001/.05,
        u9_prospective_input_without_buck_limiting_A=(buck_max*all_shorts/(.8*5.8))+.5+sd_write_w[1]/5.8,
        # DS41326 p5 high-side peak limit max3.1A bounds the instantaneous
        # gated input demand; use the whole pulse, no duty/hiccup reduction.
        u9_port_fault_peak_bound_inference_A=3.1+(1.4+sd_write_w[1])/3.5+ovlo_max/(3300*(1-thick))+.005,
        u9_port_fault_peak_bound_basis='AP63201 max3.1A HS peak current plus(1.4W logic+0.825W SDwrite)/3.5V, R92 at10.18V (U9 OVLO trip corner with its pin leakage, D-R25-03) and5mA allowance; excludes threshold overshoot/parasitic dips; bench required',
        # TI TPS25947 RevC p9/eq7 p32 at exact750ohm, scaled inversely
        # for R84 RT0603BRD07750RL0.1%/25ppm/K over the stated100K excursion.
        u9_current_limit_min_A=3.96/(1+thin),
        u9_current_limit_max_A=4.84/(1-thin),
        u9_current_limit_basis='Calc/Inference: exact750ohm TI table3.96..4.84A scaled inversely with R84 +/-0.35% (0.1% initial +25ppm/K x100K); not a new TI characterization or transient guarantee',
        r92_ohm=3300,
        battery_break_r92_bleed_bound_W=r92_bleed_w,
        battery_break_load_W=loads_w,
        battery_break_ride_through_ms=ride_through,
        battery_break_ride_through_note=('[shortest, longest] ms; Calc / Inference: constant-power loads at the '
                                         'AP63203 / AP63201 inputs from7.4V; microSD additional3.3V*0.2A write or0.03A idle divided by80-85% efficiency; a:0.62W retained logic+0.1W idle '
                                         'port chain; b: 0.6-1.4 W unshed logic (pass1_electrical 4.4, no RF) + 0.1 W; '
                                         'c:ports at1.561A (incl. the 0.1A AUX allowance)+unshed logic+SDwrite; d:GPS/radio/AUX always on at0.561A,camera off,logic shed+SDidle; a/b require physically absent port loads, not software switches. No credit for '
                                         'RAW_PROTECTED capacitance or U11 reverse blocking; each case additionally '
                                         'includes the 3.3 kohm R92 loss at 7.4 V and minimum resistance'),
        passive_cold_screen_sole_bus=passive_cold_screen(),
        divider_audit2=dict(top_series_ohm=[5100,5100], bottom_parallel_ohm=[2000,2000],
                           direct_ADC_filtered_nodes=['PYRO1_CONT','ARM1_SENSE'],
                           extra_pin_series_resistors='R168/R170 removed; no _MCU tails',
                           normal_8V4_pin_V=8.4/11.2,
                           clamp_19V9_one_top_short_or_bottom_open_pin_max_V=19.9*1014.5/(5026.05+1014.5),
                           one_top_short_8V4_divider_max_A=8.4/(5026.05+985.5),
                           nominal_source_ohm=1/(1/10200+1/1000),
                           nominal_filter_RC_us=(1/(1/10200+1/1000))*10e-9*1e6,
                           basis='1% plus100ppm/K to70C; ST DS12110 Table109 4V analog absolute max; double-fault pin damage remains possible; bench transitions/ADC classification'),
        camera_io_C92=dict(code='C19666', nominal_uF=4.7, max_bias_V=3.4,
                           typical_bias_retained=.6832757,
                           effective_uF_inference=4.7*.6832757*.9*.85*.9,
                           tps709_required_effective_uF=1.5,
                           note='Typical bias curve and 10% aging allowance are inferences; bench stability required'),
        load_switch_AUD3=dict(code='C431196', part='AONR21357', gate_abs_max_V=25,
                             gate_event_inference_V=18, hot_R_acceptance_ceiling_ohm=.040,
                             hot_R_typical_curve_inference_ohm=.0123*1.4,
                             minimum_loaded_BAT_IN_V=6, Q122_drain_allowance_V=.1,
                             gate_source_ohm_nominal=r_gs_nom, Q122_gate_on_V_nominal_and_VOH_floor=q122_on_V,
                             Q122_gate_with_30k_pullup_PC1_unconfigured_V=q122_pullup_off_V,
                             Q122_VGS_th_V=[.65, 1.05, 1.45], Q122_drain_load_max_A=q122_drain_load_A,
                             settled_min_Vgs_magnitude_V=enable_vgs,
                             C120_code='C29936', C120_max_uF=1.265,
                             C120_effective_at_4V5_uF_inference=c120_effective,
                             two_FET_140nC_gate_step_V_inference=.14/c120_effective,
                             tau_max_ms=enable_tau*1000,
                             time_to_4V5_max_ms=-enable_tau*math.log(1-4.5/enable_vgs)*1000,
                             enable_settle_min_ms=100,
                             note='Hot R, effective C, Miller and actual board SOA are conditional inferences; bench required'),
        fire_current_GAP1=dict(status='Native-board CAD path calculation; material, hot FET, source and harness conditions unmeasured',
                              board_sha256=hashlib.sha256(board_bytes).hexdigest(),
                              selected_ematch='MJG J-Tek LEAD-FREE standard24AWG',
                              maker_all_fire_A=.75, current_margin=1.5, required_fire_current_A=1.125,
                              maker_source='https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF',
                              maker_all_fire_test_s=.5, physical_pulse_qualification='<=20ms including tail; lot bench qualification pending',
                              pack_R_ohm=.15, open_equivalent_at_fire_V=7.4,
                              other_converter_load_W=other_w, servo_stall_A=1.92,
                              R134_hot_max_ohm=r134_hot, ematch_max_ohm=2,
                              external_leads_harness_max_ohm=.3,
                              CAD_track_length_width_mm=copper_paths,
                              CAD_inside_pad_entry_length_mm=pad_entries,
                              CAD_path_basis='Native fire_path pruning; ACT_FET_S uses Q120.2 to Q121.3 without parallel credit; '
                                             'routed current entries to terminal-pad anchors included, dead sense branches excluded; no series firing via',
                              copper_20C_by_net_ohm=copper_by_net,
                              copper_20C_ohm=copper_20c, copper_TCR_per_K=.00393,
                              copper_70C_ohm=copper_70c,
                              ground_return_allowance_ohm=.005, terminal_allowance_ohm=.010,
                              Q124_hot_R_inference_ohm=q124_hot,
                              primary_40mohm_FETs=fire_primary, secondary_typical_hot_curve_FETs=fire_typical,
                              historical_4R533_fixed_other_1p5A_fire_A=(7.4-.15*1.5)/4.533,
                              historical_4R533_fixed_other_5p34A_fire_A=(7.4-.15*(1.5+3.84))/4.533,
                              note='7.4V equivalent must remain at fire after pad/flight drain; neutral does not unload a jam. '
                                   'Selected MJG J-Tek all-fire0.75A times1.5=1.125A; <=20ms lot firing test still required.'),
        pyro_fault_GAP5=dict(watchdog_prescaler=4, watchdog_reload=239, watchdog_LSI_cycles=960,
                            watchdog_nominal_ms=30, LSI_qualified_Hz=[29400,33600],
                            watchdog_actual_ms=watchdog_ms, prefire_sync_max_ms=.2,
                            reset_to_HiZ_max_ms=.5, actual_current_tail_max_ms=1.5,
                            physical_fault_bound_ms=watchdog_ms[1]+.2+.5+1.5,
                            guarded_fault_max_ms=36, normal_physical_current_max_ms=20,
                            postfire_SAFETY_refresh_max_ms=5, C126_max_F=c126_max,
                            floating_MCU_Rdis_max_ohm=r_discharge_max,
                            RC_to_0V4_ms=rc_tail_ms, gate_charge_tail_ms_inference=charge_tail_ms,
                            combined_tail_model_ms_inference=rc_tail_ms+charge_tail_ms,
                            R134_min_70C_ohm=r134_min, R134_fault_max_W=fault_power,
                            R134_20ms_energy_J=fault_power*.020, R134_36ms_energy_J=fault_power*.036,
                            R134_curve_20ms_W_inference=pulse_curve(20),
                            R134_curve_36ms_W_inference=pulse_curve(36),
                            R134_85C_curve_36ms_W_sensitivity_inference=pulse_curve(36)*(155-85)/(155-70),
                            note='Refresh immediately before PE4 rises; no refresh during fire; normal abort includes gate tail. '
                                 'All timing/actual-current and hot pulse limits need bench tests; no firmware implemented. '
                                 '0.4V off criterion and hot gate-charge extrapolation are inferences, not a hot off guarantee.'),
        option_oq5_status='Historical alternative, not adopted: hardware U400 cutoff absent; GPS/radio now always on. Hypothetical cutoff values do not qualify the board',
        option_oq5_en_divider_ohm=[en_r5, en_r6],
        option_oq5_voff_V=voff, option_oq5_von_V=von,
        option_oq5_ride_through_ms=ride_through_en)
    assert results['camera_module_min_V'] >= 5
    assert results['radio_module_min_V'] >= 4.5
    assert results['gps_module_min_V'] >= 3.3
    assert results['radio_gps_module_max_V'] < 5
    assert results['ldo_headroom_min_V'] > .2
    assert results['ldo_bleeder_min_A'] > .005
    assert results['buck_camera_short_radio_gps_normal_A'] < 2
    # GAP-3 / D-R19-14: U401's inferred junction stays <= 125 C at the 70 C bay limit with the AUX allowance included.
    assert max(results['ldo_ambient_70C_junction_inference_C']) <= 125 and .46 + results['port_aux_allowance_A'] <= 1
    # Removing individual GPS/radio limiters raises prospective short demand above
    # the buck's2A continuous rating. Current limit/hiccup/thermal response is the
    # intended fault state, not qualification of this prospective current as safe.
    assert all_shorts > 3.1 and results['gps_or_radio_short_camera_normal_prospective_buck_A'] > 2
    assert results['u9_port_fault_peak_bound_inference_A'] < results['u9_current_limit_min_A']
    assert all(case['fire_A'] >= results['fire_current_GAP1']['required_fire_current_A']
               for case in fire_primary['pack_7V4_by_stall_count'].values())
    assert results['camera_io_C92']['effective_uF_inference'] > 1.5
    assert results['pyro_fault_GAP5']['physical_fault_bound_ms'] < 36
    assert .2+20+5 < watchdog_ms[0] and enable_vgs > 4.5
    assert q122_pullup_off_V < .65 and min(q122_on_V) > 1.45
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    scope = ap.add_mutually_exclusive_group()
    scope.add_argument('--library-only', action='store_true', help='generate local lands/models before schematic generation')
    scope.add_argument('--budget-only', action='store_true', help='bind the power budget after the final PCB is generated')
    args = ap.parse_args()
    files = {} if args.budget_only else generated()
    if not args.library_only:
        files[NOTES / 'parts_budget.json'] = json.dumps(power_budget(args.board), indent=2) + '\n'
    changed = [p for p, t in files.items() if not p.exists() or p.read_text() != t]
    if args.check and changed:
        print('r10_parts: stale:', ', '.join(p.name for p in changed))
        return 1
    if not args.check:
        for p in changed:
            p.write_text(files[p])
    if not args.budget_only:
        rows = geometry_checks()
        print(f'r10_parts: {len(rows)} footprints parsed; terminal copper gap 1.600mm; generated files current')
    if not args.library_only:
        print('r10_parts: native-board power budget current')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
