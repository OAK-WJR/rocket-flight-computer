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
# D-R12-83: R401 is a 0.1 % 25 ppm/K thin-film part (YAGEO RT0402BRD0710KL, C190095: JLC listing / YAGEO RT datasheet)
TOL_PRECISE = {'initial': 0.001, 'drift': 0.001 + 25e-6 * 67}
# D-R12-86 (R12F1-TRI-01): PA4's divider at ten times D-R12-05's impedance; PA4 TT_xx input leakage (DS12110 Rev 8
# Table 60 p. 139: +/-250 nA, 0 < VIN <= VDD). D-R12-93 moves PORT_SENSE from PA4 (TT_a) to PD10 (H9, FT_h; DS12110 Rev 8
# Table 9 p. 75). R12F5-TRI-16: FT_h is an FT_xx pin (Table 60 note 5: all FT_xx except FT_lu, FT_u and PC3), whose input
# leakage is +/-250 nA for 0 < VIN <= VDD, the same as PA4's TT_xx (Table 60 p. 139; the +/-350 nA row is FT_u only);
# above VDD an FT_xx pin may sink up to 1.5 uA, which only lowers the reading (Inference)
PORT_SENSE_TOP, PORT_SENSE_BOT, PD10_LEAK = 47e3, 100e3, 250e-9
# R12F5-TRI-02: TPS563208 (U400 PORT_4V8, U403 CAM_5V) headroom. TI SLVSD90B section 7.3: maximum recommended duty 75 %,
# minimum recommended input VO / 0.75; section 5.5: tOFF(MIN) 220 typ / 310 max ns, RDS(on)h 95 mOhm typ (25 C), Fsw
# 580 kHz (VIN 12 V); section 6.4.1: below VIN 7 V (with VFB under the reference) the frequency may drop smoothly to a
# minimum of about 200 kHz to extend TON
BUCK_DUTY_REC, BUCK_TOFF_S, BUCK_RDSH, BUCK_FSW, BUCK_FSW_FOLDBACK = 0.75, (220e-9, 310e-9), 0.095, 580e3, 200e3
PORT_RAIL = 'PORT_4V8 (U400 TPS563208, R400 47k + R404 5.1k / R401 10k 0.1 %)'
PORT_BUDGET_A = 0.561                                         # always-on port budget (R10 D-R28-01; Inference)


def divider(vref, top, bot, tol, leak=0.0, tol_bot=None):
    """(min, max) of vref x (1 + top / bot) with each resistor at its worst end; leak = FB pin current bound (A);
    tol_bot = the bottom resistor's own tolerance when it differs from the top's (D-R12-83)."""
    tb = tol if tol_bot is None else tol_bot
    lo = vref[0] * (1 + top * (1 - tol) / (bot * (1 + tb))) - leak * top * (1 + tol)
    hi = vref[1] * (1 + top * (1 + tol) / (bot * (1 - tb))) + leak * top * (1 + tol)
    return round(lo, 4), round(hi, 4)


def rails():
    out = {}
    specs = {
        '3V3 (U2 LMR50410, R14 47k / R15 20k)': dict(
            vref=(0.99, 1.01), top=47e3, bot=20e3, leak=0.0,
            src='TI SLUSDW3A section 7.5 VFB 0.99-1.01 V; ILKG-FB 0.2 nA typ (neglected)',
            limits=(3.135, 3.6), why='U6 FXLS90322 VCC_BUF >= 3.135 V (NXP FXLS9xxx0 Rev 6 item 10502, D-R12-51; the '
                                    'tightest low end); STM32H743 VDD33USB 3.0-3.6 V (USB regulator bypassed, R11) '
                                    'and VDD <= 3.6 V; W25Q128 / microSD 2.7-3.6 V; LSM6DSVE 1.71-3.6 V (JLC / LCSC '
                                    'listing, D-R12-50); MS5607 1.8-3.6 V (TE MS5607-02BA03, D-R12-52)'),
        'PORT_4V8 (U400 TPS563208, R400 47k + R404 5.1k / R401 10k 0.1 %)': dict(
            vref=(0.749, 0.787), top=52.1e3, bot=10e3, leak=0.1e-6, precise_bot=True,
            src='TI SLVSD90B section 5.5 VFB 0.749-0.787 V continuous mode (TPS563208 is FCCM), TJ -40 to 125 C; '
                'IVFB +/-0.1 uA; R401 0.1 % 25 ppm/K (D-R12-83)',
            limits=(4.5, 5.0), why='HGLRC M100 Mini 3.3-5 V (hglrc.com product page, read 2026-11-05: the 5.0 V top); '
                                  'MicoAir LR900-F "5V DC (from USB or JST-GH)" with no range (micoair.com product '
                                  'page, read 2026-11-05), so its 4.5 V floor and 5.0 V top stay the project records\' '
                                  'Inference (r10_plan O5, parts_qualification R8-MCU-02) until bench-confirmed. The '
                                  'floor applies at the port pins after the copper drop (r12_stageD port_supply). '
                                  'The window holds only while U400 VIN >= VO / 0.75 (R12F5-TRI-02; port_input)'),
        'CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)': dict(
            vref=(0.749, 0.787), top=61e3, bot=10e3, leak=0.1e-6, src='TI SLVSD90B section 5.5',
            limits=(5.0, 20.0), why='RunCam Split 4 manual "DC 5-20V" (as quoted in the R10 records); harness drop at '
                                    '1 A comes off the lower end'),
    }
    for name, s in specs.items():
        row = dict(source=s['src'], limits_V=s['limits'], limits_basis=s['why'])
        for case, tol in TOL.items():
            lo, hi = divider(s['vref'], s['top'], s['bot'], tol, s['leak'],
                             TOL_PRECISE[case] if s.get('precise_bot') else None)
            row[case] = dict(min_V=lo, max_V=hi, inside_limits=lo >= s['limits'][0] and hi <= s['limits'][1],
                             margin_low_V=round(lo - s['limits'][0], 4), margin_high_V=round(s['limits'][1] - hi, 4))
        row['nominal_V'] = round((s['vref'][0] + s['vref'][1]) / 2 * (1 + s['top'] / s['bot']), 4)
        row['label'] = ('Calculation (Datasheet VFB, ' + ('1 % top, 0.1 % bottom' if s.get('precise_bot') else '1 %')
                        + ' resistors); drift case Inference')
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
        # PD10 PORT_SENSE = PORT_4V8 x R112 / (R111 + R112), R111 47k, R112 100k (D-R12-86: ten times D-R12-05's 4.7k /
        # 10k, same ratio), less PD10's FT_xx input leakage +/-250 nA through the divider's 32 kohm Thevenin resistance
        # (DS12110 Rev 8 Table 60 p. 139; R12F5-TRI-16)
        p = rails()['PORT_4V8 (U400 TPS563208, R400 47k + R404 5.1k / R401 10k 0.1 %)'][case]
        top, bot = PORT_SENSE_TOP, PORT_SENSE_BOT
        rth = top * bot / (top + bot)
        lo = p['min_V'] * bot * (1 - tol) / (bot * (1 - tol) + top * (1 + tol)) - PD10_LEAK * rth * (1 + tol)
        hi = p['max_V'] * bot * (1 + tol) / (bot * (1 + tol) + top * (1 - tol)) + PD10_LEAK * rth * (1 + tol)
        r['PORT_SENSE_V'] = [round(lo, 3), round(hi, 3)]
        # PA6 VLOGIC_SENSE = VLOGIC x 10k / 110k
        r['VLOGIC_SENSE_ratio'] = [round(10e3 * (1 - tol) / (10e3 * (1 - tol) + 100e3 * (1 + tol)), 5),
                                   round(10e3 * (1 + tol) / (10e3 * (1 + tol) + 100e3 * (1 - tol)), 5)]
        # PC2_C CAM_5V_SENSE = CAM_5V x 1k / 11.2k (R104 + R107 over R105 || R106, D-R11-86)
        c = rails()['CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)'][case]
        r['CAM_5V_SENSE_V'] = [round(c['min_V'] / 11.2 * (1 - 2 * tol), 3), round(c['max_V'] / 11.2 * (1 + 2 * tol), 3)]
        out[case] = r
    out['PORT_SENSE_divider'] = dict(R111_ohm=PORT_SENSE_TOP, R112_ohm=PORT_SENSE_BOT, pd10_leak_A=PD10_LEAK,
                                     thevenin_ohm=round(PORT_SENSE_TOP * PORT_SENSE_BOT / (PORT_SENSE_TOP + PORT_SENSE_BOT), 1),
                                     low_when_off_V=round(PD10_LEAK * PORT_SENSE_BOT * (1 + TOL['drift']), 3))
    # R12F5-TRI-17: the VIH / VIL / ceiling checks use this file's own 3V3 window in each resistor case (VDD at its
    # maximum for VIH, at its minimum for the ceiling and VIL), not hard-coded 3.43 / 3.22 V
    v33 = rails()['3V3 (U2 LMR50410, R14 47k / R15 20k)']
    lim = {c: dict(vdd_V=[v33[c]['min_V'], v33[c]['max_V']], vih_V=round(0.7 * v33[c]['max_V'], 4),
                   ceiling_V=round(v33[c]['min_V'] + 0.3, 4), vil_V=round(0.3 * v33[c]['min_V'], 4)) for c in TOL}
    out['PORT_SENSE_thresholds'] = lim
    out['PORT_SENSE_limits'] = (
        'PD10 (FT_h, D-R12-93): VIH 0.7 x VDD at the 3V3 maximum = '
        + ' / '.join(f"{lim[c]['vih_V']:.3f} V ({c}, VDD {lim[c]['vdd_V'][1]:.4f} V)" for c in TOL)
        + "; R10's TT_a ceiling VDD + 0.3 at the 3V3 minimum = "
        + ' / '.join(f"{lim[c]['ceiling_V']:.3f} V ({c})" for c in TOL)
        + ' kept as a margin (FT_h tolerates 5.5 V, DS12110 Table 60); with PORT_4V8 off, R112 holds PD10 at or below '
          'the leakage figure, under VIL 0.3 x VDD at the 3V3 minimum')
    out['PORT_SENSE_ok'] = all(out[c]['PORT_SENSE_V'][0] > lim[c]['vih_V'] and out[c]['PORT_SENSE_V'][1] < lim[c]['ceiling_V']
                               and out['PORT_SENSE_divider']['low_when_off_V'] < lim[c]['vil_V'] for c in TOL)
    out['label'] = 'Calculation (1 % resistors, rail windows above; DS12110 leakage); drift Inference'
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
    # R12F5-TRI-04 (D-R12-10): the R119 || R120 / R121 divider hangs on ACT_FET_S, which sits I_fire x RDS(Q120 hot)
    # below BAT_IN during a fire (R12F2-TRI-08), less Q122's 0.1 V drop (Inference); drive strength at the smallest
    # ratio 49k / 59.2k (Rgs -2 %, R121 +2 %), the +/-12 V corner at the largest 51k / 60.8k (D-R12-91). Stage A has no
    # board copper; r12_stageD adds the J1 -> Q120 and Q120 -> Q121 copper drops (R12F5-TRI-03)
    r_min, r_max = 49e3 / 59.2e3, 51e3 / 60.8e3
    def vgs_p(vbat, amps=0.0, ratio=r_min):
        return round(-(vbat - amps * pfet - .1) * ratio, 3)
    four = cases['4']
    # |VGS| >= 4.5 V down to this BAT_IN: with the bus on (no fire current) and during a fire at the four-stall current
    pack_bus_on = 4.5 / r_min + .1
    pack_fire = pack_bus_on + four['fire_A'] * pfet
    # R12F5-TRI-05: Q124 VGS from the 3V3 drift minimum less PE4's VOH allowance, R126 / R128 at their drift ends
    v33_min = rails()['3V3 (U2 LMR50410, R14 47k / R15 20k)']['drift']['min_V']
    td = TOL['drift']
    return dict(
        r11_branch_ohm=round(rest11, 4), r11_other_W=round(other11, 3), r12_branch_ohm=round(rest, 4),
        r12_other_W=round(other, 3), pfet_hot_ohm=round(pfet, 4), q124_hot_ohm=round(q124, 4),
        stalls=cases, four_stall_A=cases['4']['fire_A'], floor_A=1.125, four_stall_ok=cases['4']['fire_A'] >= 1.125,
        four_stall_margin_pct=round((cases['4']['fire_A'] / 1.125 - 1) * 100, 1), shorted=shorts,
        gate=dict(
            q120_q121_vgs_V={'four_stall_fire': vgs_p(four['BAT_IN_V'], four['fire_A']),
                             '8.4V_bus_on': vgs_p(8.4), '12.6V_3S_bus_on_max_ratio': vgs_p(12.6, ratio=r_max),
                             '19.9V_TVS_clamp_bus_on_max_ratio': vgs_p(19.9, ratio=r_max)},
            q120_q121_vgs_basis=('stage A (no board copper): VGS = -(BAT_IN - I_fire x RDS(Q120 hot) - 0.1 V) x Rgs / '
                                 '(Rgs + R121), ACT_FET_S basis (R12F2-TRI-08, R12F5-TRI-04); the four-stall point is '
                                 'this file\'s stage A fire model; r12_stageD (stageD_budget.json fire.gate) gives the '
                                 'board figures with the copper drops, per FET'),
            q120_vgs_abs_max_V=12,
            q120_rds_row=(f'VGS -4.5 V (|VGS| >= 4.5 V down to BAT_IN {pack_bus_on:.2f} V with the bus on and '
                          f'{pack_fire:.2f} V during a {four["fire_A"]:.2f} A fire; stage A, no copper)'),
            q120_vgs_4V5_min_bat_V=dict(bus_on=round(pack_bus_on, 3), four_stall_fire=round(pack_fire, 3)),
            q124_vgs_min_V=round((v33_min - .4) * 10e3 * (1 - td) / (10e3 * (1 - td) + 220 * (1 + td)), 3),
            q124_vgs_th_max_V=1.45,
            q124_tau_us=round(220 * 220e-9 * 1e6, 1),
            note='Q120 / Q121 VGS = -(V_ACT_FET_S - 0.1 V) x (R119 || R120) / ((R119 || R120) + R121), V_ACT_FET_S = BAT_IN '
                 'less Q120\'s drop during a fire (Q122 drop 0.1 V and the Q120 hot factor Inference). |VGS| exceeds the '
                 'AO3401A +/-12 V only above 14.4 V pack-side with the bus enabled (a transient up to the SMAJ12CA '
                 'clamp); the bus is enabled from the on-rail check until switch-off (Inference that no transient '
                 'above 14.4 V occurs while it is on, pad or flight; R12F4-TRI-03). Q124 VGS: PE4 VOH >= VDD - 0.4 V '
                 '(DS12110 Rev 8 Table 158, |IIO| 4 / 8 mA; PE4\'s steady load, R127 1k plus R126 220R + R128 10k, is '
                 'about 3.6 mA (<= 3.9 mA with drift), within the 4 mA row; R12F3-TRI-06, R12F4-TRI-02) through R126 '
                 '220R / R128 10k, at the 3V3 drift minimum with R126 / R128 at their drift ends (R12F5-TRI-05)'),
        basis='R11 CAD copper (placeholder until stage D), R10 pack model (0.15 ohm, 7.4 V open, 1.92 A per stall), '
              'R134 hot, match 2 ohm, leads 0.3 ohm; FET hot factors Inference',
        label='Calculation on Datasheet limits; copper, pack, loads and hot factors Inference')


def crystal():
    """ST AN2867: gm_crit = 4 ESR (2 pi f)^2 (C0 + CL)^2 must stay below Gm_critmax 1.5 mA/V (DS12110 Rev 8 Table 141
    p. 234: 'Maximum critical crystal gm', startup, max). YXC YSX321SL sheet (LCSC's PDF for C9006, Datasheet): ESR <=
    50 ohm (16-31 MHz), C0 <= 3 pF, CL 12 pF (the C9006 listing: 12PF +/-10PPM, +/-20PPM over -40...85 C), drive level
    10-200 uW max; no motional capacitance C1 is given. The circuit's load CL = C25 x C26 / (C25 + C26) + Cs, with C25 /
    C26 read from circuit.json (value and tolerance, each at its own worst end) and Cs the stray (pin + board)
    capacitance 2-5 pF (AN2867's typical range; Inference). R12F3-TRI-05: the range now includes the capacitors'
    tolerance; with 18 pF +/-5 % the +5 % / 5 pF corner gave 1.5027 mA/V, above 1.5, so C25 / C26 became 15 pF.
    The frequency offset from CL 12 pF is the pulling estimate (C1 / 2) (1 / (C0 + CL) - 1 / (C0 + 12 pF)) with C1 <=
    10 fF and C0 0.5-3 pF (Inference: C1 and the C0 minimum are not on the sheet), added to the sheet's +/-10 ppm
    tolerance, +/-20 ppm over temperature and 5 years of +/-3 ppm / year ageing, against USB full speed's +/-2500 ppm
    (USB 2.0 section 7.1.11, 12 Mb/s +/-0.25 %)."""
    import re
    parts = json.loads((HERE / 'r12/design/circuit.json').read_text())['parts']
    caps = []
    for ref in ('C25', 'C26'):
        m = re.fullmatch(r'([\d.]+)pF \S+ C0G (\d+)%', parts[ref]['value'])
        caps.append((float(m[1]) * 1e-12, float(m[2]) / 100))
    f, esr, c0, cl_spec = 25e6, 50.0, 3e-12, 12e-12
    g = lambda cl: 4 * esr * (2 * math.pi * f) ** 2 * (c0 + cl) ** 2 * 1e3
    series = lambda a, b: a * b / (a + b)
    cl_lo = series(*(c * (1 - t) for c, t in caps)) + 2e-12
    cl_hi = series(*(c * (1 + t) for c, t in caps)) + 5e-12
    cl_nom = series(*(c for c, _ in caps)) + 3.5e-12
    pull = lambda cl, c0x: 10e-15 / 2 * (1 / (c0x + cl) - 1 / (c0x + cl_spec)) * 1e6
    pulls = [pull(cl, c0x) for cl in (cl_lo, cl_hi) for c0x in (0.5e-12, 3e-12)]
    total = max(abs(p) for p in pulls) + 10 + 20 + 5 * 3
    gm = [g(cl_lo), g(cl_hi)]
    return dict(C25_C26_pF=[round(c * 1e12, 3) for c, _ in caps], C25_C26_tolerance=[t for _, t in caps],
                stray_pF=[2.0, 5.0], circuit_CL_pF=[round(cl_lo * 1e12, 3), round(cl_nom * 1e12, 3),
                                                    round(cl_hi * 1e12, 3)],
                gm_crit_mA_per_V_at_CL12=round(g(12e-12), 3), gm_crit_range_mA_per_V=[round(v, 4) for v in gm],
                limit_mA_per_V=1.5, ok=gm[1] < 1.5, margin_pct=round((1 - gm[1] / 1.5) * 100, 1),
                gm_crit_18pF_5pct_corner_mA_per_V=round(g(series(18.9e-12, 18.9e-12) + 5e-12), 4),
                pulling_ppm_range=[round(min(pulls), 1), round(max(pulls), 1)], total_offset_ppm_bound=round(total, 1),
                usb_fs_limit_ppm=2500,
                label='Calculation (Datasheet ESR / C0 maxima, C25 / C26 tolerance); stray capacitance Inference; '
                      'pulling: Inference (C1 <= 10 fF and C0 0.5-3 pF assumed, not on the YSX321SL sheet)')


def cam_input():
    """D-R12-87 (R12F1-TRI-17): the CAM_5V window above is the feedback window, valid only while U403 can regulate.
    TI SLVSD90B section 7.3: maximum recommended duty 75 %, so the minimum recommended input is VO / 0.75; section 6.4.1:
    below VIN 7 V the switching frequency may fall to about 200 kHz; section 5.5: tOFF(MIN) 220 typ / 310 max ns and
    RDS(on)h 95 mOhm typ (25 C). Below VO / 0.75 the window is not claimed. At the four-stall fire point U403's input is
    taken as the fire model's BAT_IN less U9's RON 0.04 ohm (Inference, as vlogic) at the converters' fire-time current
    (fire 'other' / BAT_IN); the highest output U403 can then hold is D_max x (VIN - 1 A x RDS(on)h) with
    D_max = 1 - tOFF(MIN) x 200 kHz (inductor DCR, board copper and hot RDS(on) not included: Inference)."""
    cam = rails()['CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)']
    f = fire()
    bat = f['stalls']['4']['BAT_IN_V']
    vin = bat - 0.04 * f['r12_other_W'] / bat
    rh, i_out, fsw = 0.095, 1.0, 200e3
    dmax = {k: 1 - t * fsw for k, t in (('tOFF_typ_220ns', 220e-9), ('tOFF_max_310ns', 310e-9))}
    held = {k: round(d * (vin - i_out * rh), 3) for k, d in dmax.items()}
    return dict(
        min_recommended_VIN_V={case: [round(cam[case]['min_V'] / 0.75, 3), round(cam[case]['max_V'] / 0.75, 3)]
                               for case in TOL},
        window_holds_for='U403 VIN >= VO / 0.75 (6.96-7.59 V initial); below it the CAM_5V window is not claimed',
        four_stall_BAT_IN_V=bat, four_stall_U403_VIN_V=round(vin, 3),
        four_stall_duty_needed_lossless=round(cam['initial']['min_V'] / vin, 4),
        dmax_at_200kHz={k: round(d, 4) for k, d in dmax.items()}, four_stall_max_held_V=held,
        four_stall_note=('at the four-stall point U403 runs past its 75 % recommended duty, at or near its minimum '
                         'off-time limit: CAM_5V may fall below the 5.221 V window low end to about '
                         f'{min(held.values()):.2f} V (above the camera 5.0 V minimum before harness drop); the '
                         'camera is not shown to fail'),
        label='Calculation / Inference (Datasheet duty, tOFF(MIN) and RDS(on)h; U9 RON, currents, DCR and copper '
              'Inference)')


def buck_headroom(vin, row, i_out):
    """R12F5-TRI-02: can a TPS563208 hold the rail window `row` (r12_budget.rails row) from input `vin` at output current
    `i_out`? Duty needed = VO / (VIN - i_out x RDS(on)h) at each window end; the off-time duty ceiling is
    1 - tOFF(MIN) x f at the nominal 580 kHz and at the about 200 kHz foldback floor below 7 V; the highest output the
    buck can then hold is D_max x (VIN - i_out x RDS(on)h). Inductor DCR, the low-side switch, hot RDS(on) and the exact
    foldback frequency are not modelled (Inference): an estimate, not a guaranteed window."""
    v = vin - i_out * BUCK_RDSH
    dmax = {f'{f / 1e3:.0f}kHz_tOFF_{"typ" if t < 300e-9 else "max"}_{t * 1e9:.0f}ns': 1 - t * f
            for f in (BUCK_FSW, BUCK_FSW_FOLDBACK) for t in BUCK_TOFF_S}
    held = {k: round(d * v, 3) for k, d in dmax.items()}
    top = max(row[c]['max_V'] for c in TOL)
    return dict(
        VIN_V=round(vin, 4), I_out_A=i_out,
        duty_needed={c: [round(row[c]['min_V'] / v, 4), round(row[c]['max_V'] / v, 4)] for c in TOL},
        duty_needed_lossless={c: [round(row[c]['min_V'] / vin, 4), round(row[c]['max_V'] / vin, 4)] for c in TOL},
        below_recommended_duty=all(row[c]['max_V'] / vin <= BUCK_DUTY_REC for c in TOL),
        dmax={k: round(d, 4) for k, d in dmax.items()}, max_held_V=held,
        window_top_V=top, holds_window_top_at_580kHz=min(held[k] for k in held if k.startswith('580')) >= top,
        holds_window_top_with_foldback=min(held[k] for k in held if k.startswith('200')) >= top)


def port_input():
    """R12F5-TRI-02: the PORT_4V8 window is the feedback window, valid only while U400 can regulate (as D-R12-87 for
    U403): U400 VIN >= VO / 0.75 (TI SLVSD90B section 7.3). Stage A (no board): U400's input is BAT_IN less U9's RON
    0.04 ohm at the converter current (Inference, as vlogic / cam_input), at the four-stall fire point of fire() and on a
    6.0 V open-circuit pack (R10 pack model 0.15 ohm, no fire, no stall, the same converter load); the ports draw the
    0.561 A budget (Inference). r12_stageD (stageD_budget.json port_supply.u400_input) repeats it with the board copper."""
    port = rails()[PORT_RAIL]
    f = fire()
    other = f['r12_other_W']
    pack6 = (6.0 + math.sqrt(36.0 - 4 * .15 * other)) / 2
    pts = {'four_stall_fire': f['stalls']['4']['BAT_IN_V'], '6V0_pack_converters_only': pack6}
    out = dict(
        min_recommended_VIN_V={c: [round(port[c]['min_V'] / BUCK_DUTY_REC, 3), round(port[c]['max_V'] / BUCK_DUTY_REC, 3)]
                               for c in TOL},
        window_holds_for=('U400 VIN >= VO / 0.75 ('
                          + ', '.join(f"{port[c]['min_V'] / BUCK_DUTY_REC:.2f}-{port[c]['max_V'] / BUCK_DUTY_REC:.2f} V {c}"
                                      for c in TOL)
                          + '); below it the PORT_4V8 window is not claimed, and the headroom estimate below applies'))
    for name, bat in pts.items():
        vin = bat - 0.04 * other / bat
        out[name] = dict(BAT_IN_V=round(bat, 4), **buck_headroom(vin, port, PORT_BUDGET_A))
    out['note'] = ('below about 6.1-6.6 V U400 runs past its 75 % recommended duty; at the nominal 580 kHz its minimum '
                   'off-time would cap the output under the window, but below VIN 7 V the frequency may fold back to '
                   'about 200 kHz (SLVSD90B 6.4.1), which leaves room for the window top: regulation should hold '
                   '(Inference; bench item)')
    out['label'] = ('Calculation / Inference (Datasheet duty, tOFF(MIN), RDS(on)h and foldback floor; U9 RON, pack model, '
                    'converter load, DCR and copper Inference)')
    return out


def compute():
    return dict(
        status='R12 stage A (no board): Calculation / Inference as labelled; no measurement',
        resistor_cases={k: f'+/-{v * 100:.2f} % independent' for k, v in TOL.items()},
        rails=rails(), cam_input=cam_input(), port_input=port_input(), u9=u9(), sense=sense(), vlogic=vlogic(), holdup=holdup(), fire=fire(), crystal=crystal())


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
