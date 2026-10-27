#!/usr/bin/env python3
"""Generate R10 local lands/envelope models; never edit a board or schematic.

Maker sources and qualification limits: sources/r10_design/parts_qualification.md.
Run with KiCad Python; --check verifies deterministic files and actual parsed pads.
The PortLDO symbol is exposed for the schematic generator, not written here.
"""
import argparse
import json
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


def terminal(color):
    name = 'M3_DB125_2P_' + color
    body = _rect((-3.5, -3.9), (3.5, 3.5), 'F.Fab', .1)
    body += _rect((-3.9, -4.3), (3.9, 3.9), 'F.CrtYd', .05)
    body += _rect((-3.65, -4.05), (3.65, 3.65), 'F.SilkS', .15)
    # Positive-y face is the wire-entry face in this local frame. A fabrication
    # arrow under the housing prevents silently inheriting the old pad aliases.
    body += _line((0, 1.5), (0, 3), 'F.Fab', .15)
    body += _line((0, 3), (-.5, 2.5), 'F.Fab', .15)
    body += _line((0, 3), (.5, 2.5), 'F.Fab', .15)
    for n, x in [('1', -1.75), ('2', 1.75)]:
        body += (f'(pad "{n}" thru_hole circle (at {x} 0) (size 1.9 1.9) '
                 '(drill 1.3) (layers "*.Cu" "*.Mask"))\n')
    return make_fp(name, body, -5,
                   'DORABO DB125-3.5-2P; drawing T0-1; 1.3mm finished drill, 1.9mm copper; wire entry +y', True)


def ldo():
    name = 'M3_TPS7A91_DSK10'
    body = _rect((-1.25, -1.25), (1.25, 1.25), 'F.Fab', .1)
    body += _rect((-1.7, -1.55), (1.7, 1.55), 'F.CrtYd', .05)
    body += _line((-.85, -1.4), (.85, -1.4), 'F.SilkS', .15)
    body += _circle((-1.65, -1.3), .1, 'F.SilkS', .15)
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
    for n, x in [('1', -3.25), ('2', 3.25)]:
        body += _pad(n, x, 0, 3.5, 1.7, ('F.Cu', 'F.Paste', 'F.Mask'))
    body += _line((-4.5, -2.2), (-4.5, -1.2), 'F.SilkS', .15)
    body += _line((-5, -1.7), (-4, -1.7), 'F.SilkS', .15)
    return make_fp(name, body, -5.4, 'jieerrui MA25V470M8x10; positive pad1 left; derived land, reflow qualification open')


FOOTPRINTS = {'M3_GH_BM02B_GHS_TBT': gh2, 'M3_DB125_2P_BK': lambda: terminal('BK'),
              'M3_DB125_2P_GN': lambda: terminal('GN'), 'M3_TPS7A91_DSK10': ldo,
              'M3_MA_8x10': polymer}
# Boxes use millimetres, KiCad VRML scale .1in handled by r7_parts._box.
MODELS = {
    'M3_GH_BM02B_GHS_TBT': (0, -.375, 0, 5.75, 4.25, 7.3, '.85 .85 .8'),
    'M3_DB125_2P_BK': (0, -.2, 0, 7.3, 7.7, 8.9, '.12 .12 .12'),
    'M3_DB125_2P_GN': (0, -.2, 0, 7.3, 7.7, 8.9, '.1 .55 .2'),
    'M3_TPS7A91_DSK10': (0, 0, 0, 2.6, 2.6, .8, '.12 .12 .12'),
    'M3_MA_8x10': (0, 0, 0, 8.5, 8.5, 10.8, '.65 .65 .68'),
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
    for name in ('M3_DB125_2P_BK', 'M3_DB125_2P_GN'):
        p = result[name]
        assert p['2'][0] - p['1'][0] - (p['1'][2] + p['2'][2]) / 2 >= 1.5
        assert p['1'] == [-1.75, 0, 1.9, 1.9]
    assert result['M3_GH_BM02B_GHS_TBT']['1'] == [-.625, 1.95, .6, 1.7]
    assert result['M3_TPS7A91_DSK10']['11'] == [0, 0, 1.2, 2]
    assert len(result['M3_TPS7A91_DSK10']) == 11
    assert result['M3_MA_8x10']['1'] == [-3.25, 0, 3.5, 1.7]
    return result


def power_budget():
    """Worst component tolerances plus explicit, unmeasured harness/thermal limits."""
    thin = .001 + 25e-6 * 100
    thick = .01 + 100e-6 * 100
    buck_min = .792 * (1 + (56200 * (1-thin) + 2000 * (1-thick)) / (10000 * (1+thin)))
    buck_max = .808 * (1 + (56200 * (1+thin) + 2000 * (1+thick)) / (10000 * (1-thin)))
    ldo_min = .792 * (1 + 49900 * (1-thin) / (10000 * (1+thin))) - 100e-9 * 49900 * (1+thin)
    ldo_max = .808 * (1 + 49900 * (1+thin) / (10000 * (1-thin))) + 100e-9 * 49900 * (1+thin)
    limits = {port: [25230 / (r * (1+thick)) ** 1.016 / 1000,
                     22980 / (r * (1-thick)) ** .94 / 1000]
              for port, r in [('camera', 22.6), ('radio', 66.5), ('gps', 120)]}
    # Equation roots include input power as constant power, not a guessed current.
    def loaded_pack(open_v, servos):
        r, logic, power, efficiency = .15, .5, 5.456 * 1.46, .8
        a = open_v - r * (servos + logic)
        return (a + (a*a - 4*r*power/efficiency)**.5) / 2
    results = dict(
        status='Calculated conditional bounds; no physical or transient tests performed',
        temperature_excursion_from_25C=100,
        buck_V=[buck_min, buck_max], ldo_V=[ldo_min, ldo_max],
        switch_Rmax_ohm=.135, camera_harness_copper_loop_max_ohm=.15,
        radio_gps_harness_copper_loop_max_ohm=.2,
        transient_allowance_V=.05,
        camera_module_min_V=buck_min-.135-.15-.05,
        radio_module_min_V=ldo_min-.3*(.135+.2)-.05,
        gps_module_min_V=ldo_min-.15*(.135+.2)-.05,
        radio_gps_module_max_V=ldo_max+.05,
        ldo_headroom_min_V=buck_min-.05-ldo_max,
        switch_limit_A=limits,
        buck_all_shorts_A=sum(v[1] for v in limits.values())+.011,
        buck_camera_short_radio_gps_normal_A=limits['camera'][1]+.3+.15+.011,
        ldo_bleeder_min_A=ldo_min/(820*(1+thick)),
        ldo_full_load_loss_W=(buck_max-ldo_min)*.46+buck_max*.004,
        ldo_ambient_85C_junction_inference_C=85+62.5*((buck_max-ldo_min)*.46+buck_max*.004),
        pack_7V4_four_stall_loaded_V=loaded_pack(7.4,7.68),
        pack_6V0_four_stall_loaded_V=loaded_pack(6,7.68),
        servo_star_board_return_max_A=4*7.68*.001/.05,
        u9_input_at_all_port_shorts_inference_A=(buck_max*(sum(v[1] for v in limits.values())+.011)/(.8*5.8))+.5)
    assert results['camera_module_min_V'] >= 5
    assert results['radio_module_min_V'] >= 4.5
    assert results['gps_module_min_V'] >= 3.3
    assert results['radio_gps_module_max_V'] < 5
    assert results['ldo_headroom_min_V'] > .2
    assert results['ldo_bleeder_min_A'] > .005
    assert results['buck_camera_short_radio_gps_normal_A'] < 2
    assert results['buck_all_shorts_A'] < 2
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    files = generated()
    files[NOTES / 'parts_budget.json'] = json.dumps(power_budget(), indent=2) + '\n'
    changed = [p for p, t in files.items() if not p.exists() or p.read_text() != t]
    if args.check and changed:
        print('r10_parts: stale:', ', '.join(p.name for p in changed))
        return 1
    if not args.check:
        for p in changed:
            p.write_text(files[p])
    rows = geometry_checks()
    print(f'r10_parts: {len(rows)} footprints parsed; terminal copper gap 1.600mm; generated files current')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
