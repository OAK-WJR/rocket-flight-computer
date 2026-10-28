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
    # TI SLVS841F eq. 1 p. 15 (IOSmin / IOSmax, RILIM in kOhm, mA); R +/-2 % (1 % initial + 100 ppm/K x 100 K).
    # R410 is 100 kOhm (R10_DECISIONS D-R3-01: the board's value, sharing the 100 kOhm BOM line, C14675).
    limits = {port: [25230 / (r * (1+thick)) ** 1.016 / 1000,
                     22980 / (r * (1-thick)) ** .94 / 1000]
              for port, r in [('camera', 22.6), ('radio', 66.5), ('gps', 100)]}
    all_shorts = sum(v[1] for v in limits.values()) + .011
    # AP63201 (Diodes DS41326 Rev 3-2): 2 A continuous (p. 1), HS peak current limit 2.5 A min (p. 5), fSW 500 kHz
    # typ with +/-6 % spread spectrum (p. 5: 470 kHz taken as the low edge, Inference), ripple dI = Vo (Vi - Vo) /
    # (Vi L fSW) (p. 13); L400 6.8 uH -20 % (Bourns SRP5030T). Inputs: 8.4 V (2S full, F9) and 9.97 V (U9's OVLO trip,
    # 9.63-9.96 V, M3_R4 A2: the highest RAW_PROTECTED can reach); Vo over the buck tolerance band.
    def peak(vin, f, lmin=6.8e-6 * .8):
        return max(all_shorts + vo * (vin - vo) / (vin * lmin * f) / 2 for vo in (buck_min, buck_max))
    # Battery-lead-break ride-through (REQUIREMENTS F6, R3-PWR-02): C84 on VLOGIC back-feeds RAW_PROTECTED through
    # U11 (TPS2121 reverse blocking only above IRCB 0.2 / 1 / 2 A, SLVSEA3F section 7.5 p. 8), so it also carries the
    # port buck U400 (EN tied to VIN; port switch turn-off up to 3 ms, SLVS841F section 7.5 p. 7). Constant-power
    # loads from 7.4 V; no credit for RAW_PROTECTED / C6 / C7 capacitance or for U11 blocking (Calc / Inference).
    ports_w = [buck_min * 1.461 / .85, buck_max * 1.461 / .80]     # camera 1 A + radio .3 A + GPS .15 A + 11 mA
    # D-OA-05: account explicitly for R92 (3.3 kohm) while C84 can feed RAW_PROTECTED through U11.
    # Hold its worst loss at the 7.4 V launch floor constant as voltage falls; no credit for any old envelope allowance.
    r92_bleed_w = 7.4 ** 2 / (3300 * (1-thick))
    loads_w = dict(a_ports_off_logic_shed=[.62 + .1] * 2, b_ports_off_no_shed=[.6 + .1, 1.4 + .1],
                   c_camera_radio_gps_on=[ports_w[0] + .6, ports_w[1] + 1.4])
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
                       for case, wa, wl in (('ports_on_then_logic_shed', loads_w['c_camera_radio_gps_on'][1], .72+r92_bleed_w),
                                            ('ports_on_then_logic_no_shed', loads_w['c_camera_radio_gps_on'][1], 1.5+r92_bleed_w))
                       for c in (300.8e-6, 470e-6) for v in (3.5, 3.8)}
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
        buck_all_shorts_A=all_shorts,
        buck_all_shorts_over_2A_continuous_pct=(all_shorts / 2 - 1) * 100,
        buck_all_shorts_peak_inductor_A={'8V4_470kHz': peak(8.4, 470e3), '8V4_500kHz': peak(8.4, 500e3),
                                         '9V97_470kHz': peak(9.97, 470e3), '9V97_500kHz': peak(9.97, 500e3)},
        buck_peak_current_limit_min_A=2.5,
        buck_camera_short_radio_gps_normal_A=limits['camera'][1]+.3+.15+.011,
        ldo_bleeder_min_A=ldo_min/(820*(1+thick)),
        ldo_full_load_loss_W=(buck_max-ldo_min)*.46+buck_max*.004,
        # U401 has no thermal vias: use the layout inference in parts_qualification,
        # not the datasheet reference-board thermal resistance (partial round 9).
        ldo_theta_ja_inference_C_per_W=[80, 110],
        ldo_ambient_85C_junction_inference_C=[85+r*((buck_max-ldo_min)*.46+buck_max*.004)
                                             for r in (80, 110)],
        pack_7V4_four_stall_loaded_V=loaded_pack(7.4,7.68),
        pack_6V0_four_stall_loaded_V=loaded_pack(6,7.68),
        servo_star_board_return_max_A=4*7.68*.001/.05,
        u9_input_at_all_port_shorts_inference_A=(buck_max*all_shorts/(.8*5.8))+.5,
        u9_current_limit_min_A=3.96,
        r92_ohm=3300,
        battery_break_r92_bleed_bound_W=r92_bleed_w,
        battery_break_load_W=loads_w,
        battery_break_ride_through_ms=ride_through,
        battery_break_ride_through_note=('[shortest, longest] ms; Calc / Inference: constant-power loads at the '
                                         'AP63203 / AP63201 inputs from 7.4 V; a: 0.62 W retained logic + 0.1 W idle '
                                         'port chain; b: 0.6-1.4 W unshed logic (pass1_electrical 4.4, no RF) + 0.1 W; '
                                         'c: ports at 1.461 A, 80-85 % buck efficiency, + unshed logic; no credit for '
                                         'RAW_PROTECTED capacitance or U11 reverse blocking; each case additionally '
                                         'includes the 3.3 kohm R92 loss at 7.4 V and minimum resistance'),
        option_oq5_status='Not adopted: owner 2026-10-28 retained firmware shedding without a hardware cutoff',
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
    # All three ports shorted (three faults) exceed AP63201's 2 A continuous rating by about 1 %. The criterion is
    # that the inductor's peak current stays below the 2.5 A minimum cycle-by-cycle limit (else the buck hiccups,
    # DS41326 p. 11: ports lose supply, VLOGIC / 3V3 are a separate path): met at 8.4 V; at the 9.97 V OVLO corner it
    # holds at the 500 kHz nominal frequency and misses by <= 0.01 A at the -6 % spread-spectrum edge (recorded).
    pk = results['buck_all_shorts_peak_inductor_A']
    assert 2 < all_shorts < 2.03
    assert pk['8V4_470kHz'] < 2.41 < 2.5 and pk['9V97_500kHz'] < 2.5
    assert pk['9V97_470kHz'] < 2.51
    assert results['u9_input_at_all_port_shorts_inference_A'] < 2.95 < results['u9_current_limit_min_A']
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
