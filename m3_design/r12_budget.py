#!/usr/bin/env python3
"""M3-ASSY-R12 stage A windows and budgets (R12_DECISIONS D-R12-05 ... -14): every figure the re-sourcing changes,
recomputed from datasheet limits and 1 % resistor values, written to m3_design/r12/design/r12_windows.json.

usage: python3 -I -B m3_design/r12_budget.py [--check]      (--check: fail if the JSON differs from a fresh run)

Labels (AGENTS section 2.5): every figure is a Calculation on the cited Datasheet limits; inputs that are not maker
limits (resistor temperature drift, diode forward drop at the operating current, copper, harness, loads, efficiency)
are Inference and named in the figure's 'basis'. Two resistor cases: 'initial' = 1 % initial tolerance, each resistor
at its own worst end; 'drift' = 1 % + 100 ppm/K over 67 K (the bay's -42 ... +70 C span from 25 C, REQUIREMENTS F1),
also independent (a bound: two thick-film parts of one series largely track, Inference). No board exists: the fire
budget takes R11's CAD copper (stageD_budget.json, 0b26da5) as a placeholder until stage D re-runs it on R12 copper.
"""
import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'r12/design/r12_windows.json'
R11_BUDGET = HERE / 'r11/design/stageD_budget.json'
TOL = {'initial': 0.01, 'drift': 0.01 + 100e-6 * 67}


def divider(vref, top, bot, tol, leak=0.0):
    """(min, max) of vref x (1 + top / bot) with each resistor at its worst end; leak = FB pin current bound (A)."""
    lo = vref[0] * (1 + top * (1 - tol) / (bot * (1 + tol))) - leak * top * (1 + tol)
    hi = vref[1] * (1 + top * (1 + tol) / (bot * (1 - tol))) + leak * top * (1 + tol)
    return round(lo, 4), round(hi, 4)


def rails():
    out = {}
    specs = {
        '3V3 (U2 LMR50410, R14 47k / R15 20k)': dict(
            vref=(0.99, 1.01), top=47e3, bot=20e3, leak=0.0,
            src='TI SLUSDW3A section 7.5 VFB 0.99-1.01 V; ILKG-FB 0.2 nA typ (neglected)',
            limits=(3.0, 3.6), why='STM32H743 VDD33USB 3.0-3.6 V (USB regulator bypassed, R11) and VDD <= 3.6 V; '
                                  'W25Q128 / microSD 2.7-3.6 V; ISM6HG256X / LPS28DFW <= 3.6 V'),
        'PORT_4V8 (U400 TPS563208, R400 47k + R404 4.7k / R401 10k)': dict(
            vref=(0.749, 0.787), top=51.7e3, bot=10e3, leak=0.1e-6,
            src='TI SLVSD90B section 5.5 VFB 0.749-0.787 V continuous mode (TPS563208 is FCCM), TJ -40 to 125 C; '
                'IVFB +/-0.1 uA',
            limits=(4.5, 5.0), why='project module ranges: MicoAir LR900 4.5-5 V, HGLRC M100 Mini 3.3-5 V '
                                  '(r10_plan O5, parts_qualification R8-MCU-02); Inference until bench-confirmed'),
        'CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)': dict(
            vref=(0.749, 0.787), top=61e3, bot=10e3, leak=0.1e-6, src='TI SLVSD90B section 5.5',
            limits=(5.0, 20.0), why='RunCam Split 4 manual "DC 5-20V" (as quoted in the R10 records); harness drop at '
                                    '1 A comes off the lower end'),
    }
    for name, s in specs.items():
        row = dict(source=s['src'], limits_V=s['limits'], limits_basis=s['why'])
        for case, tol in TOL.items():
            lo, hi = divider(s['vref'], s['top'], s['bot'], tol, s['leak'])
            row[case] = dict(min_V=lo, max_V=hi, inside_limits=lo >= s['limits'][0] and hi <= s['limits'][1],
                             margin_low_V=round(lo - s['limits'][0], 4), margin_high_V=round(s['limits'][1] - hi, 4))
        row['nominal_V'] = round((s['vref'][0] + s['vref'][1]) / 2 * (1 + s['top'] / s['bot']), 4)
        row['label'] = 'Calculation (Datasheet VFB, 1 % resistors); drift case Inference'
        out[name] = row
    return out


def u9():
    """U9 TPS259470A: OVLO (R82 1M / R83 100k + R93 33k), ILIM (R84 || R94, 2 x 1.5k), EN chain (R80 / R165 470k,
    R81 300k, unchanged values). TI SLVSFC9C section 6.5: VOV(R) 1.183-1.223 V, VOV(F) 1.076-1.116 V, IOVLKG +/-0.1 uA,
    VUVLO(R) 1.183-1.223 V, VUVLO(F) 1.076-1.116 V, IENLKG +/-0.1 uA, ILIM 3.960-4.840 A at RILM = 750 ohm, tRST 110 ms
    (A variant); the A and L variants share the EC table (device comparison table: only the fault response differs)."""
    out = {}
    top, bot = 1e6, 133e3
    for case, tol in TOL.items():
        t_lo, t_hi, b_lo, b_hi = top * (1 - tol), top * (1 + tol), bot * (1 - tol), bot * (1 + tol)
        def trip(v, t, b, i):
            return (v + i * t * b / (t + b)) * (t + b) / b
        out[case] = dict(
            ovlo_rising_V=[round(trip(1.183, t_lo, b_hi, -0.1e-6), 3), round(trip(1.223, t_hi, b_lo, 0.1e-6), 3)],
            ovlo_falling_V=[round(trip(1.076, t_lo, b_hi, -0.1e-6), 3), round(trip(1.116, t_hi, b_lo, 0.1e-6), 3)],
            ilim_A=[round(3.960 * 750 / (750 * (1 + tol)), 3), round(4.840 * 750 / (750 * (1 - tol)), 3)])
    out['ovlo_nominal_V'] = round(1.2 * (1 + top / bot), 3)
    out['ovlo_check'] = ('2S full charge 8.4 V stays below the lowest falling threshold (no OVLO hysteresis on a full '
                         'pack); a 3S pack above the highest rising threshold is cut off (F9 "wrong 3S")')
    out['ovlo_check_ok'] = all(out[c]['ovlo_falling_V'][0] > 8.4 for c in TOL)
    out['ovlo_pin_V_at_8V4'] = round(8.4 * bot / (top + bot), 3)
    out['ovlo_pin_roc'] = 'VOVLO 0.5-1.5 V recommended (SLVSFC9C section 6.3): 0.676 V at the 5.71 V four-stall point'
    out['ilim_basis'] = ('Datasheet ILIM at exactly 750 ohm, scaled 1/R for the 1 % pair (Inference: TI gives no '
                         'RILM sensitivity formula in section 6.5)')
    en = 300e3 / (470e3 + 470e3 + 300e3)
    out['en_chain'] = dict(
        closed_en_at_8V4_V=round(8.4 * en, 3), turn_on_min_bat_V=round(1.223 / en, 3),
        en_abs_max_ok_at_19V9=round(19.9 * en, 3) < 6.5,
        carried='R80 / R165 470k, R81 300k, C87 220 nF, D402 unchanged in value (0603 basic cases); U9 A and L share the '
                'EN / UVLO limits, so R11 / R10 F6 figures (turn-on 30-130 ms; single drop-out 10.3 ms at 6.0 V, 8.1 ms '
                'at 5.71 V; D-R24-19) carry over as Calculation / Inference; stage D re-runs them with R12 tolerances')
    out['label'] = 'Calculation on Datasheet limits; ILIM scaling and drift case Inference'
    return out


def sense():
    """ADC / GPIO sense dividers (1 % resistors)."""
    out = {}
    for case, tol in TOL.items():
        r = {}
        # PA4 PORT_SENSE = PORT_4V8 x R112 / (R111 + R112), R111 4.7k, R112 10k
        p = rails()['PORT_4V8 (U400 TPS563208, R400 47k + R404 4.7k / R401 10k)'][case]
        lo = p['min_V'] * 10e3 * (1 - tol) / (10e3 * (1 - tol) + 4.7e3 * (1 + tol))
        hi = p['max_V'] * 10e3 * (1 + tol) / (10e3 * (1 + tol) + 4.7e3 * (1 - tol))
        r['PORT_SENSE_V'] = [round(lo, 3), round(hi, 3)]
        # PA6 VLOGIC_SENSE = VLOGIC x 10k / 110k
        r['VLOGIC_SENSE_ratio'] = [round(10e3 * (1 - tol) / (10e3 * (1 - tol) + 100e3 * (1 + tol)), 5),
                                   round(10e3 * (1 + tol) / (10e3 * (1 + tol) + 100e3 * (1 - tol)), 5)]
        # PC2_C CAM_5V_SENSE = CAM_5V x 1k / 11.2k (R104 + R107 over R105 || R106, D-R11-86)
        c = rails()['CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)'][case]
        r['CAM_5V_SENSE_V'] = [round(c['min_V'] / 11.2 * (1 - 2 * tol), 3), round(c['max_V'] / 11.2 * (1 + 2 * tol), 3)]
        out[case] = r
    out['PORT_SENSE_limits'] = ('PA4 (TT_a): VIH 0.7 x VDD = 2.39 V at the 3V3 maximum 3.43 V; at most VDD + 0.3 = '
                                '3.52 V at the 3V3 minimum 3.22 V (DS12110 I/O limits as R10 used them)')
    out['PORT_SENSE_ok'] = all(out[c]['PORT_SENSE_V'][0] > 0.7 * 3.43 and out[c]['PORT_SENSE_V'][1] < 3.22 + 0.3
                               for c in TOL)
    out['label'] = 'Calculation (1 % resistors, rail windows above)'
    return out


def vlogic():
    """D-R12-04: VLOGIC = RAW_PROTECTED - D5 or VBUS - D6 (SS34). SS34 (MDD) VF 0.55 V max at 3 A (JLC listing);
    at 0.1-0.4 A it is taken as 0.25-0.45 V (Inference: typical curve, no maximum at that current)."""
    vf = (0.25, 0.45)
    usb = dict(host_V=(4.75, 5.25), low_power_port_V=4.40)
    out = dict(
        battery_four_stall_V=round(5.713 - 0.04 * 1.5 - vf[1], 3),
        battery_2s_min_6V_V=round(6.0 - 0.04 * 1.5 - vf[1], 3),
        usb_only_V=[round(usb['host_V'][0] - vf[1], 3), round(usb['host_V'][1] - vf[0], 3)],
        usb_low_power_port_V=round(usb['low_power_port_V'] - vf[1], 3),
        lmr50410_uvlo_rising_max_V=4.0, lmr50410_roc_min_V=4.0,
        pa6_trip_window_V=[4.84, 5.17],
        basis='U9 RON 0.04 ohm at 1.5 A (Inference); SS34 VF Inference; LMR50410 VIN_UVLO rising 3.55-4.0 V, VIN 4-36 V '
              '(SLUSDW3A 7.3 / 7.5); PA6 window as R10 / R11 (firmware). USB host port 4.75-5.25 V at the connector '
              '(USB 2.0); a bus-powered hub\'s low-power port may give 4.40 V, below the LMR50410 floor through D6 '
              '(bench rule: a host or powered-hub port, O-R12-03)')
    out['usb_only_ok'] = out['usb_only_V'][0] >= 4.0
    out['pa6_below_battery_min'] = out['battery_four_stall_V'] > out['pa6_trip_window_V'][1]
    out['pa6_margin_V'] = round(out['battery_four_stall_V'] - out['pa6_trip_window_V'][1], 3)
    # D-R12-21 (O-R12-07): no E24 pair moves R60 / R61's 1 / 11 toward the needed 0.092-0.097 (every E24 ratio near it
    # is 1 / 11 or >= 0.0979), so the divider stays and the firmware PA6 threshold moves down by about the D5 drop:
    # PA6 0.42-0.45 V gives VLOGIC 4.62-4.95 V, above the U9 turn-off corner seen through D5 (BAT_IN 4.80 V less VF
    # 0.25 V = 4.55 V) and below the four-stall VLOGIC (Calculation / Inference, firmware rule)
    out['pa6_retuned_threshold_V'] = [0.42, 0.45]
    out['pa6_retuned_window_V'] = [round(0.42 * 11, 3), round(0.45 * 11, 3)]
    out['pa6_retuned_margins_V'] = dict(
        above_u9_turn_off_through_d5=round(0.42 * 11 - (4.80 - vf[0]), 3),
        below_four_stall=round(out['battery_four_stall_V'] - 0.45 * 11, 3))
    out['label'] = 'Calculation / Inference (diode drop)'
    return out


def holdup():
    """C84 (470 uF, 300.8 uF low case as R11) feeds VLOGIC only (D5 blocks RAW_PROTECTED): logic 0.6-1.4 W plus the
    microSD write 3.3 V x 0.2 A / 0.80-0.85 (R10 / R11 load cases), to 3.8 V (R11's end point)."""
    loads = (0.6 + 3.3 * .2 / .85, 1.4 + 3.3 * .2 / .80)
    def ms(c, v1, w):
        return round(.5 * c * (v1 ** 2 - 3.8 ** 2) / w * 1000, 3)
    return dict(
        from_pa6_trip_ms=[ms(300.8e-6, 4.84, loads[1]), ms(470e-6, 5.17, loads[0])],
        from_battery_break_ms=[ms(300.8e-6, 7.4 - .45, loads[1]), ms(470e-6, 7.4 - .25, loads[0])],
        r11_case_c_ms=[0.464, 0.539],
        note='R11 back-fed the port and camera bucks from C84 through U11 (case c 0.46-0.54 ms); R12 does not, so the '
             'ports and camera drop with RAW_PROTECTED and the logic keeps C84 (Calculation / Inference: constant-power '
             'loads, no credit for C6 / C99)',
        label='Calculation / Inference')


def fire():
    """REQUIREMENTS F7 / R10 GAP-1 fire model (r10_parts.power_budget fire_case) with the R12 FETs. R11's loop
    (stageD_budget.json four_stall: 1.278004 A at 5.7133 V, i.e. 4.4705 ohm branch, other load 13.07 W) is the base;
    R12 swaps the FET resistances and the other-converter load. Q120 / Q121 AO3401A: RDS(on) <= 60 mOhm at VGS -4.5 V,
    25 C; 50 -> 75 mOhm (x 1.5) from 25 to 125 C at -10 V (AOS datasheet) -> x 1.225 at 70 C (linear, Inference).
    Q124 AO3400A: <= 48 mOhm at VGS 2.5 V, 25 C; 26.5 -> 38 mOhm (x 1.434) at 125 C -> x 1.195 at 70 C (Inference)."""
    r11 = json.loads(R11_BUDGET.read_text())
    base_v, base_a = r11['four_stall']['BAT_IN_V'], r11['four_stall']['fire_A']
    rest11 = base_v / base_a
    a11 = 1 + .15 / rest11
    b11 = 7.4 - .15 * 1.92 * 4
    other11 = (b11 * base_v - a11 * base_v ** 2) / .15
    pfet_r11, q124_r11 = .040, .0058 * 1.42
    pfet, q124 = .060 * 1.225, .048 * 1.195
    rest = rest11 - 2 * pfet_r11 - q124_r11 + 2 * pfet + q124
    # other converter load (R11 'c' case max): camera 1 A and ports 0.561 A at the R12 bucks' maximum outputs / 0.80,
    # logic 1.4 W + microSD write 0.825 W, D5 0.45 V x 0.3 A, R92 bleed (R11 value)
    cam = 5.684 * 1.0 / .80
    ports = 4.962 * .561 / .80
    other = cam + ports + 1.4 + 3.3 * .2 / .80 + .45 * .3 + 7.4 ** 2 / (3300 * .98)
    cases = {}
    for stalls in range(5):
        a, b = 1 + .15 / rest, 7.4 - .15 * 1.92 * stalls
        v = (b + math.sqrt(b * b - 4 * a * .15 * other)) / (2 * a)
        cases[str(stalls)] = dict(BAT_IN_V=round(v, 4), fire_A=round(v / rest, 4))
    shorts = {}
    for label, drop in (('match_shorted', 2.0), ('match_and_leads_shorted', 2.3)):
        r = rest - drop
        a, b = 1 + .15 / r, 7.4 - .15 * 1.92 * 4
        v = (b + math.sqrt(b * b - 4 * a * .15 * other)) / (2 * a)
        shorts[label] = dict(BAT_IN_V=round(v, 4), fire_A=round(v / r, 4),
                             Q120_I2R_W=round((v / r) ** 2 * pfet, 3), Q124_I2R_W=round((v / r) ** 2 * q124, 3))
    vgs_p = lambda vbat: round(-vbat * 50e3 / (50e3 + 10e3), 2)
    return dict(
        r11_branch_ohm=round(rest11, 4), r11_other_W=round(other11, 3), r12_branch_ohm=round(rest, 4),
        r12_other_W=round(other, 3), pfet_hot_ohm=round(pfet, 4), q124_hot_ohm=round(q124, 4),
        stalls=cases, four_stall_A=cases['4']['fire_A'], floor_A=1.125, four_stall_ok=cases['4']['fire_A'] >= 1.125,
        four_stall_margin_pct=round((cases['4']['fire_A'] / 1.125 - 1) * 100, 1), shorted=shorts,
        gate=dict(
            q120_q121_vgs_V={'5.72V_four_stall': vgs_p(5.72), '8.4V': vgs_p(8.4), '12.6V_3S': vgs_p(12.6),
                             '19.9V_TVS_clamp': vgs_p(19.9)},
            q120_vgs_abs_max_V=12, q120_rds_row='VGS -4.5 V (|VGS| >= 4.5 V down to a 5.4 V pack)',
            q124_vgs_min_V=round(3.222 * 10e3 / (10e3 + 220), 3), q124_vgs_th_max_V=1.45,
            q124_tau_us=round(220 * 220e-9 * 1e6, 1),
            note='Q120 / Q121 VGS = -V_BAT x (R119 || R120) / ((R119 || R120) + R121) (R11 network). |VGS| exceeds the '
                 'AO3401A +/-12 V only above 14.4 V pack-side with the bus enabled (a transient up to the SMAJ12CA '
                 'clamp); the bus is only enabled in flight (Inference that no such transient occurs there)'),
        basis='R11 CAD copper (placeholder until stage D), R10 pack model (0.15 ohm, 7.4 V open, 1.92 A per stall), '
              'R134 hot, match 2 ohm, leads 0.3 ohm; FET hot factors Inference',
        label='Calculation on Datasheet limits; copper, pack, loads and hot factors Inference')


def crystal():
    """ST AN2867: gm_crit = 4 ESR (2 pi f)^2 (C0 + CL)^2 against Gm_critmax 1.5 mA/V (DS12110 Rev 8 Table 141 p. 234,
    as the R10 records cite it). YXC YSX321SL sheet (LCSC's PDF for C9006): ESR <= 50 ohm (16-31 MHz), C0 <= 3 pF,
    CL 12 pF specified; the circuit's load with C25 / C26 18 pF is 9 pF + stray 2-5 pF (Inference) = 11-14 pF."""
    f, esr, c0 = 25e6, 50.0, 3e-12
    g = lambda cl: 4 * esr * (2 * math.pi * f) ** 2 * (c0 + cl) ** 2 * 1e3
    return dict(gm_crit_mA_per_V_at_CL12=round(g(12e-12), 3), gm_crit_range_mA_per_V=[round(g(11e-12), 3),
                round(g(14e-12), 3)], limit_mA_per_V=1.5, ok=g(14e-12) < 1.5,
                label='Calculation (Datasheet ESR / C0 maxima); stray capacitance Inference')


def compute():
    return dict(
        status='R12 stage A (no board): Calculation / Inference as labelled; no measurement',
        resistor_cases={k: f'+/-{v * 100:.2f} % independent' for k, v in TOL.items()},
        rails=rails(), u9=u9(), sense=sense(), vlogic=vlogic(), holdup=holdup(), fire=fire(), crystal=crystal())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(compute(), indent=1, sort_keys=True) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            print('r12_budget: r12_windows.json is stale')
            return 1
        print('r12_budget: r12_windows.json current')
        return 0
    OUT.write_text(text)
    print(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
