#!/usr/bin/env python3
"""M3-ASSY-R12 stage A windows and budgets (R12_DECISIONS D-R12-05 ... -14): every figure the re-sourcing changes,
recomputed from datasheet limits and 1 % resistor values, written to m3_design/r12/design/r12_windows.json.

usage: python3 -I -B m3_design/r12_budget.py [--check]      (--check: fail if the JSON differs from a fresh run)

Labels (AGENTS section 2.5): every figure is a Calculation on the cited Datasheet limits; inputs that are not maker
limits (resistor temperature drift, diode forward drop at the operating current, copper, harness, loads, efficiency)
are Inference and named in the figure's 'basis'. Two resistor cases: 'initial' = 1 % initial tolerance, each resistor
at its own worst end; 'drift' = 1 % + 100 ppm/K over 67 K (the bay's -42 ... +70 C span from 25 C, REQUIREMENTS F1),
also independent (a bound: two thick-film parts of one series largely track, Inference). The 0.1 % 25 ppm/K thin-film
parts (R401, D-R12-83; R60 / R61, R12F9-TRI-04) take TOL_PRECISE instead: 0.1 %, and 0.1 % + 25 ppm/K over 67 K. No board exists: the fire
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
V33_RAIL = '3V3 (U2 LMR50410, R14 47k / R15 20k)'
# R12F6-TRI-03: U2 is LMR50410XDBVR, the PFM variant (TI SLUSDW3A section 5 orderable table: XDBVR PFM, XFDBVR FPWM).
# SLUSDW3A section 7.8 (System Characteristics) gives the adjustable output's regulation as -1.5 % ... +2.5 % in PFM
# operation (+/-1.5 % FPWM): deviation from the nominal output at VIN 24 V, IOUT 0 A to full load, with typical (nominal)
# components over TJ -40 ... 150 C, not production tested. It contains section 7.5's VFB 0.99-1.01 V, so the window
# takes it as an effective reference band about the 1.000 V nominal (0.985-1.025 V) with the 1 % divider on top. The
# band is the maker's typical-component system figure (Datasheet); its use at R12's VIN (about 5 V, not 24 V) and its
# stacking with the resistor tolerance are Inference.
V33_PFM_BAND = (-0.015, 0.025)
V33_VREF_NOM = 1.0
# R12F8-TRI-07: U9 TPS259470A RON, TI SLVSFC9C section 6.5: 28.2 mOhm typ (25 C), 45 mOhm max over 2.7 <= VIN <= 23 V,
# IOUT 3 A, -40 <= TJ <= 125 C (Datasheet). Every bound below takes the maximum (it was 40 mOhm, an Inference under it).
U9_RON = 0.045
# R12 U9 EN chain (unchanged values): R80 / R165 470k in series from the switch, R81 300k to GND, C87 220 nF; TI SLVSFC9C
# section 6.5: EN / UVLO rising 1.183-1.223 V, falling 1.076-1.116 V, IENLKG +/-0.1 uA; D402 (ESD103-B1-02EL) <= 50 nA
# reverse leakage (Infineon ESD103 Rev 1.3) at J400.2. C87 x 0.72 is R10's X7R bias / temperature / tolerance allowance at
# the fast-discharge end (Inference)
EN_TOP, EN_R81, EN_C87, EN_C87_LOW = 2 * 470e3, 300e3, 220e-9, 0.72
EN_I_U9, EN_I_D402, EN_OFF_MAX = 0.1e-6, 50e-9, 1.116
# R60 100k / R61 10k (PA6 = VLOGIC x R61 / (R60 + R61)). R12F9-TRI-04 (round 9 lane B, owner option (b)): R60 / R61
# are 0.1 % 25 ppm/K thin film (YAGEO RT0402BRD07100KL C852472, RT0402BRD0710KL C190095: JLC listing 2026-11-08 / YAGEO
# RT datasheet), so the PA6 divider takes TOL_PRECISE in each resistor case (PA6_TOL), and the firmware PA6 threshold
# band moves from D-R12-21's 0.42-0.45 V to 0.425-0.455 V: r12_stageD.pa6_options centres the 30 mV band in the drift
# case's room between the healthy four-stall VLOGIC (trip top below it) and U9's turn-off through D5 (trip bottom above
# it), 0.4253-0.4553 V on the board's DC solves, rounded to the millivolt (pa6_band_derivation). R12F10-TRI-08 / -09
# (PA6's input leakage; the self-consistent stage D currents) narrow that room and move its centre to about 0.439 V;
# the adopted band stays, inside the room, and stage D's band_derivation records both (adopted_inside_room)
PA6_TOP, PA6_BOT, PA6_THRESHOLD = 100e3, 10e3, (0.425, 0.455)
PA6_TOL = TOL_PRECISE
# R12F10-TRI-08: PA6's own input leakage, as PD10_LEAK. PA6 is FT_a (DS12110 Rev 8 Table 9 p. 69), an FT_xx pin (Table 60
# note 5), so +/-250 nA for 0 < VIN <= VDD (Table 60 p. 139), through the divider's Thevenin resistance R60 || R61 at
# its high end (pa6_leak_V). Applying the digital-input leakage row to the pin in analog mode is an Inference.
PA6_LEAK = 250e-9
# SS34 (D5) VF at the logic current 0.25-0.45 V (Inference: typical curve, no maximum at that current; vlogic())
D5_VF = (0.25, 0.45)


def en_model(v_bat, tol=0.01):
    """R10's U9 EN model (D-R24-19, D-R26-03; r11_stageD.en_model) with the resistor tolerance as a parameter
    (R12F8-TRI-06): R80 / R165 at +tol, R81 at -tol (the slow-trip corner: lowest closed EN, fastest open decay), C87
    220 nF x 0.72, U9 EN leakage 0.1 uA out of the node, D402 50 nA at J400.2. tol = 0.01 reproduces r11_stageD.en_model
    exactly. Returns the closed EN voltage, the single drop-out that trips U9 at 1.116 V, and the periodic
    one-block-per-100-ms open time that trips it (the late-block worst train)."""
    r_top, r81, c = EN_TOP * (1 + tol), EN_R81 * (1 - tol), EN_C87 * EN_C87_LOW
    i_u9, i_d402, v_off = EN_I_U9, EN_I_D402, EN_OFF_MAX
    r_th = r_top * r81 / (r_top + r81)
    v_closed = v_bat * r81 / (r_top + r81) - i_u9 * r_th
    r80, r_low = EN_TOP / 2 * (1 + tol), EN_TOP / 2 * (1 + tol) + r81
    v_closed -= i_d402 * (r80 * r_low / (r80 + r_low)) * (r81 / r_low)
    tau_o, tau_c = r81 * c, r_th * c
    a = (i_u9 + i_d402) * r81
    single = tau_o * math.log((v_closed + a) / (v_off + a)) if v_closed > v_off else 0.0

    def bottom(t_open, period=.1):
        x, y = math.exp(-t_open / tau_o), math.exp(-(period - t_open) / tau_c)
        return ((v_closed * (1 - y) + a) * x - a) / (1 - x * y)
    lo, hi = 0.0, single
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if bottom(mid) > v_off else (lo, mid)
    return dict(v_bat=v_bat, en_closed_V=v_closed, single_dropout_trip_ms=single * 1e3,
                periodic_100ms_trip_open_ms=lo * 1e3, en_at_7ms_open_per_100ms_V=bottom(.007),
                tau_open_ms=tau_o * 1e3, tau_closed_ms=tau_c * 1e3)


def u9_turn_off_bat_V(tol):
    """The highest BAT_IN at which U9 turns off (closed EN falls to EN falling's 1.116 V maximum) at the slow corner of
    en_model: the closed EN is linear in BAT_IN (Calculation on SLVSFC9C limits and the resistor case)."""
    e0, e1 = en_model(0.0, tol)['en_closed_V'], en_model(1.0, tol)['en_closed_V']
    return (EN_OFF_MAX - e0) / (e1 - e0)


def pa6_ratio(tol):
    """(lowest, highest) PA6 / VLOGIC ratio with R60 / R61 each at its own worst end of tol."""
    lo = PA6_BOT * (1 - tol) / (PA6_BOT * (1 - tol) + PA6_TOP * (1 + tol))
    hi = PA6_BOT * (1 + tol) / (PA6_BOT * (1 + tol) + PA6_TOP * (1 - tol))
    return lo, hi


def pa6_leak_V(tol=None):
    """R12F10-TRI-08: the bound on PA6's offset from its own input leakage, PA6_LEAK x R60 || R61 (tol None: nominal
    resistors; else both at +tol, the highest Thevenin resistance; the sign is either way)."""
    rth = PA6_TOP * PA6_BOT / (PA6_TOP + PA6_BOT)
    return PA6_LEAK * rth * (1 + (tol or 0.0))


def pa6_trip_window(tol=None):
    """VLOGIC trip window [lowest, highest] for the PA6_THRESHOLD band (0.425-0.455 V): tol None = the nominal ratio
    (x 11), else the divider at that tolerance (lowest = band bottom / highest ratio, highest = band top / lowest
    ratio); R60 / R61 take PA6_TOL (0.1 %) in R12's resistor cases. R12F10-TRI-08: PA6 = VLOGIC x ratio +/- pa6_leak_V,
    so the band widens by the leakage offset at each end (lowest = (bottom - e) / highest ratio, highest = (top + e) /
    lowest ratio), in every case including the nominal ratio."""
    if tol is None:
        k, e = (PA6_TOP + PA6_BOT) / PA6_BOT, pa6_leak_V()
        return [(PA6_THRESHOLD[0] - e) * k, (PA6_THRESHOLD[1] + e) * k]
    lo, hi = pa6_ratio(tol)
    e = pa6_leak_V(tol)
    return [(PA6_THRESHOLD[0] - e) / hi, (PA6_THRESHOLD[1] + e) / lo]


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
        V33_RAIL: dict(
            vref=(round(V33_VREF_NOM * (1 + V33_PFM_BAND[0]), 4), round(V33_VREF_NOM * (1 + V33_PFM_BAND[1]), 4)),
            top=47e3, bot=20e3, leak=0.0, pfm_band=True,
            src='TI SLUSDW3A section 7.8 PFM output regulation -1.5 % ... +2.5 % (U2 LMR50410XDBVR is the PFM variant; '
                'typical components over TJ -40 ... 150 C, VIN 24 V, IOUT 0 A to full load, not production tested), '
                'taken as an effective VFB 0.985-1.025 V about the 1.000 V nominal; it contains section 7.5\'s VFB '
                '0.99-1.01 V (R12F6-TRI-03); ILKG-FB 0.2 nA typ (neglected)',
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
        if s.get('pfm_band'):
            row['nominal_V'] = round(V33_VREF_NOM * (1 + s['top'] / s['bot']), 4)
            row['vfb_section_7_5_V'] = [0.99, 1.01]
            row['pfm_regulation_band'] = list(V33_PFM_BAND)
            row['label'] = ('Calculation / Inference (3V3 window, D-R12-139): Calculation on SLUSDW3A section 7.8\'s '
                            'PFM regulation band, the maker\'s typical-component system figure, as the reference band, '
                            'with 1 % resistors; the band at R12\'s VIN and its stacking with the resistor tolerance '
                            'Inference; drift case Inference')
        else:
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
    # R12F8-TRI-10: OVLO pin = BAT_IN x (R83 100k + R93 33k) / (R82 1M + 133k), at the 5.71 V four-stall point; the range
    # takes each side of the divider at its own worst end (leakage neglected)
    v4 = 5.71
    out['ovlo_pin_V_at_5V71'] = dict(
        nominal=round(v4 * bot / (top + bot), 4),
        **{case: [round(v4 * bot * (1 - tol) / (top * (1 + tol) + bot * (1 - tol)), 4),
                  round(v4 * bot * (1 + tol) / (top * (1 - tol) + bot * (1 + tol)), 4)] for case, tol in TOL.items()})
    out['ovlo_pin_roc'] = ('VOVLO 0.5-1.5 V recommended (SLVSFC9C section 6.3): '
                           f"{out['ovlo_pin_V_at_5V71']['nominal']:.3f} V at the 5.71 V four-stall point "
                           f"({out['ovlo_pin_V_at_5V71']['initial'][0]:.4f}-{out['ovlo_pin_V_at_5V71']['initial'][1]:.4f} V "
                           'with 1 % resistors), inside the range')
    out['ovlo_pin_roc_ok'] = all(0.5 <= x <= 1.5 for case in TOL for x in out['ovlo_pin_V_at_5V71'][case])
    out['ilim_basis'] = ('Datasheet ILIM at exactly 750 ohm, scaled 1/R for the 1 % pair (Inference: TI gives no '
                         'RILM sensitivity formula in section 6.5)')
    en = 300e3 / (470e3 + 470e3 + 300e3)
    out['en_chain'] = dict(
        closed_en_at_8V4_V=round(8.4 * en, 3), turn_on_min_bat_V=round(1.223 / en, 3),
        en_abs_max_ok_at_19V9=round(19.9 * en, 3) < 6.5,
        carried='R80 / R165 470k, R81 300k, C87 220 nF, D402 unchanged in value (0603 basic cases); U9 A and L share the '
                'EN / UVLO limits, so R11 / R10 F6 figures (turn-on 30-130 ms; single drop-out 10.3 ms at 6.0 V, 8.1 ms '
                'at 5.71 V; D-R24-19) carry over as Calculation / Inference; stage D re-runs them over both resistor cases '
                '(R12F8-TRI-06)')
    out['turn_off_max_bat_V'] = {case: round(u9_turn_off_bat_V(tol), 4) for case, tol in TOL.items()}
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
        # PA6 VLOGIC_SENSE = VLOGIC x 10k / 110k (R60 / R61 0.1 % 25 ppm/K, PA6_TOL; R12F9-TRI-04)
        r['VLOGIC_SENSE_ratio'] = [round(v, 5) for v in pa6_ratio(PA6_TOL[case])]
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
    out['label'] = ('Calculation (1 % resistors, R60 / R61 0.1 % (PA6_TOL, R12F9-TRI-04), rail windows above; DS12110 '
                    'leakage); drift Inference; the PORT_SENSE '
                    'thresholds: Calculation / Inference (3V3 window, D-R12-139)')
    return out


def vlogic():
    """D-R12-04: VLOGIC = RAW_PROTECTED - D5 or VBUS - D6 (SS34). SS34 (MDD) VF 0.55 V max at 3 A (JLC listing);
    at 0.1-0.4 A it is taken as 0.25-0.45 V (Inference: typical curve, no maximum at that current)."""
    vf = D5_VF
    usb = dict(host_V=(4.75, 5.25), low_power_port_V=4.40)
    out = dict(
        battery_four_stall_V=round(5.713 - U9_RON * 1.5 - vf[1], 3),
        battery_2s_min_6V_V=round(6.0 - U9_RON * 1.5 - vf[1], 3),
        usb_only_V=[round(usb['host_V'][0] - vf[1], 3), round(usb['host_V'][1] - vf[0], 3)],
        usb_low_power_port_V=round(usb['low_power_port_V'] - vf[1], 3),
        lmr50410_uvlo_rising_max_V=4.0, lmr50410_roc_min_V=4.0,
        basis='U9 RON 0.045 ohm (SLVSFC9C 6.5 maximum, R12F8-TRI-07) at 1.5 A (the current Inference); SS34 VF '
              'Inference; LMR50410 VIN_UVLO rising 3.55-4.0 V, VIN 4-36 V (SLUSDW3A 7.3 / 7.5); PA6 window R12\'s '
              '(D-R12-21, below). USB host port 4.75-5.25 V at the connector '
              '(USB 2.0); a bus-powered hub\'s low-power port may give 4.40 V, below the LMR50410 floor through D6 '
              '(bench rule: a host or powered-hub port, O-R12-03)')
    out['usb_only_ok'] = out['usb_only_V'][0] >= 4.0
    # D-R12-21 (O-R12-07): no E24 pair moves R60 / R61's 1 / 11 toward the needed 0.092-0.097 (every E24 ratio near it
    # is 1 / 11 or >= 0.0979), so the divider stays and the firmware PA6 threshold moves down by about the D5 drop.
    # R12F9-TRI-04 (round 9 lane B): R60 / R61 are 0.1 % 25 ppm/K (PA6_TOL) and the band is 0.425-0.455 V, VLOGIC
    # 4.650-5.030 V at the nominal ratio with PA6's input leakage (R12F10-TRI-08; 4.675-5.005 V without). R12F8-TRI-06: the window and both margins are given at the nominal ratio and
    # over both resistor cases (R60 / R61 at their own worst ends of PA6_TOL). The U9 turn-off corner is the highest
    # BAT_IN at which U9 turns off (u9_turn_off_bat_V, the EN chain, still 1 % thick film, in the same resistor case;
    # 4.80 V at 1 %), seen through D5 at its lowest VF 0.25 V (no load drop: the highest VLOGIC at turn-off); the trip
    # bottom must lie above it for firmware to see PA6 trip before U9 turns off (Calculation / Inference: D5 VF, the
    # drift case)
    out['pa6_retuned_threshold_V'] = list(PA6_THRESHOLD)
    out['pa6_retuned_window_V'] = [round(v, 3) for v in pa6_trip_window()]
    out['pa6_trip_window_V'] = dict(nominal_ratio=out['pa6_retuned_window_V'],
                                    **{case: [round(v, 4) for v in pa6_trip_window(tol)] for case, tol in PA6_TOL.items()})
    turn_off = dict(nominal_ratio=u9_turn_off_bat_V(TOL['initial']), initial=u9_turn_off_bat_V(TOL['initial']),
                    drift=u9_turn_off_bat_V(TOL['drift']))
    out['u9_turn_off_through_d5_V'] = {k: round(v - vf[0], 4) for k, v in turn_off.items()}
    out['pa6_retuned_margins_V'] = {
        k: dict(above_u9_turn_off_through_d5=round(out['pa6_trip_window_V'][k][0] - out['u9_turn_off_through_d5_V'][k], 4),
                below_four_stall=round(out['battery_four_stall_V'] - out['pa6_trip_window_V'][k][1], 4))
        for k in ('nominal_ratio', 'initial', 'drift')}
    out['pa6_retuned_margins_basis'] = ('nominal_ratio: the x 11 window against the 1 % EN corner (D-R12-21\'s original '
                                        'comparison); initial / drift: the divider (0.1 %, PA6_TOL) and the EN '
                                        'chain (1 %) both in that resistor case. Negative above_u9_turn_off_through_d5 = the trip bottom lies '
                                        'below the highest VLOGIC at which U9 can turn off (R12F8-TRI-06)')
    out['pa6_threshold_bottom_needed_V'] = {case: round(out['u9_turn_off_through_d5_V'][case] * pa6_ratio(PA6_TOL[case])[1]
                                                        + pa6_leak_V(PA6_TOL[case]), 4)
                                            for case in TOL}
    # R12F10-TRI-08: PA6's FT_xx input leakage through R60 || R61 is in every window and margin above
    out['pa6_leakage'] = dict(leak_A=PA6_LEAK, thevenin_ohm=round(PA6_TOP * PA6_BOT / (PA6_TOP + PA6_BOT), 1),
                              offset_V={k: round(pa6_leak_V(t), 7) for k, t in
                                        (('nominal_ratio', None), *PA6_TOL.items())},
                              source='DS12110 Rev 8 Table 60 p. 139 (FT_xx +/-250 nA, 0 < VIN <= VDD); PA6 FT_a, Table 9 '
                                     'p. 69', label='Calculation / Inference (the digital-input leakage row applied to '
                                                    'PA6 in analog mode)')
    out['label'] = ('Calculation / Inference (diode drop; resistor drift case; PA6 input leakage in analog mode, '
                    'R12F10-TRI-08)')
    return out


def holdup():
    """C84 (470 uF, 300.8 uF low case as R11) feeds VLOGIC only (D5 blocks RAW_PROTECTED): logic 0.6-1.4 W plus the
    microSD write 3.3 V x 0.2 A / 0.80-0.85 (R10 / R11 load cases), to 3.8 V (R11's end point). R12F8-TRI-08: the PA6-trip
    start points are R12's window (R12F9-TRI-04: 0.425-0.455 V, VLOGIC 4.650-5.030 V at the nominal ratio with PA6's
    input leakage (R12F10-TRI-08), the divider
    0.1 %), not R10 / R11's 4.84-5.17 V, at the nominal ratio and over both resistor cases; the battery break starts at 7.4 V less U9 (RON
    0.045 ohm at 1.5 A) and D5, as stage D does."""
    loads = (0.6 + 3.3 * .2 / .85, 1.4 + 3.3 * .2 / .80)
    def ms(c, v1, w):
        return round(.5 * c * (v1 ** 2 - 3.8 ** 2) / w * 1000, 3)
    wins = dict(nominal_ratio=pa6_trip_window(), **{case: pa6_trip_window(tol) for case, tol in PA6_TOL.items()})
    u9 = U9_RON * 1.5
    return dict(
        from_pa6_trip_ms={k: [ms(300.8e-6, w[0], loads[1]), ms(470e-6, w[1], loads[0])] for k, w in wins.items()},
        from_battery_break_ms=[ms(300.8e-6, 7.4 - u9 - D5_VF[1], loads[1]), ms(470e-6, 7.4 - u9 - D5_VF[0], loads[0])],
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
                 'about 3.5 mA (<= 3.93 mA with drift at the 3V3 PFM-band maximum), within the 4 mA row; R12F3-TRI-06, '
                 'R12F4-TRI-02, R12F6-TRI-03) through R126 220R / R128 10k, at the 3V3 drift minimum (SLUSDW3A section '
                 '7.8 PFM band) with R126 / R128 at their drift ends (R12F5-TRI-05); the Q124 VGS and PE4 load figures: '
                 'Calculation / Inference (3V3 window, D-R12-139)'),
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
    taken as the fire model's BAT_IN less U9's RON 0.045 ohm (SLVSFC9C maximum, R12F8-TRI-07) at the converters' fire-time
    current
    (fire 'other' / BAT_IN); the highest output U403 can then hold is D_max x (VIN - 1 A x RDS(on)h) with
    D_max = 1 - tOFF(MIN) x 200 kHz (inductor DCR, board copper and hot RDS(on) not included: Inference)."""
    cam = rails()['CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)']
    f = fire()
    bat = f['stalls']['4']['BAT_IN_V']
    vin = bat - U9_RON * f['r12_other_W'] / bat
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
        label='Calculation / Inference (Datasheet duty, tOFF(MIN), RDS(on)h and U9 RON maximum; currents, DCR and copper '
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
    0.045 ohm (SLVSFC9C maximum, R12F8-TRI-07) at the converter current, at the four-stall fire point of fire() and on a
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
        vin = bat - U9_RON * other / bat
        out[name] = dict(BAT_IN_V=round(bat, 4), **buck_headroom(vin, port, PORT_BUDGET_A))
    out['note'] = ('below about 6.1-6.6 V U400 runs past its 75 % recommended duty; at the nominal 580 kHz its minimum '
                   'off-time would cap the output under the window, but below VIN 7 V the frequency may fold back to '
                   'about 200 kHz (SLVSD90B 6.4.1), which leaves room for the window top: regulation should hold '
                   '(Inference; bench item)')
    out['label'] = ('Calculation / Inference (Datasheet duty, tOFF(MIN), RDS(on)h, foldback floor and U9 RON maximum; '
                    'pack model, converter load, DCR and copper Inference)')
    return out


# R12F6-TRI-01: the cold pull-up is 3V3 -> R136 5.1k -> PYRO1_COLD_PU -> D120 (BAT54C A1 -> K) -> PYRO1_COLD -> R131 5.1k
# -> PYRO1_OUT (10.2 kohm, was D120 + R131 10k); the netlist values (schematic.net.xml): PYRO1_OUT -> R173 5.1k ->
# PYRO1_CONT_MID -> R129 5.1k -> PYRO1_CONT (PC0) with R130 / R178 2k each to GND; RAW_ACT -> R132 5.1k -> ARM1_SENSE_MID
# -> R175 5.1k -> ARM1_SENSE (PC5) with R133 / R180 2k each to GND; a fitted match joins PYRO1_OUT to RAW_ACT through
# J121 and R134 2R.
COLD_PULL = (('R136', 5.1e3), ('R131', 5.1e3))
COLD_CONT_TOP, COLD_CONT_BOT = (('R173', 5.1e3), ('R129', 5.1e3)), (('R130', 2e3), ('R178', 2e3))
COLD_BUS_TOP, COLD_BUS_BOT = (('R132', 5.1e3), ('R175', 5.1e3)), (('R133', 2e3), ('R180', 2e3))
COLD_R134 = 2.0
# D120 BAT54C VF (Nexperia BAT54 series, 1 July 2022, Table 7, 25 C, pulsed): <= 240 mV at 0.1 mA, <= 320 mV at 1 mA; no
# minimum and no temperature curve. At the screen's 0.13-0.23 mA the 25 C maximum is about 0.26 V (log interpolation)
# and the -42 C end adds about 2 mV/K x 67 K: VF 0-0.40 V (Inference; the zero end is a bound)
COLD_VF = (0.0, 0.40)
# MJG J-Tek match 1-2 ohm and leads 0-0.3 ohm (R10's cold-screen and fire models; Inference)
COLD_MATCH, COLD_LEADS = (1.0, 2.0), (0.0, 0.3)


def cold_screen():
    """R12F6-TRI-01 / -03: the passive cold screen at 10.2 kohm (R10 r10_parts.passive_cold_screen's network with R12's
    parts). State: bus off (PC1 low, Q120 / Q121 off), PE4 low (Q124 off), so PYRO1_OUT is fed only by the cold pull-up
    and RAW_ACT only through a fitted match. Readings: PC0 = PYRO1_CONT, PC5 = ARM1_SENSE, in mV and as a fraction of
    VDDA (VREF+ = VDDA = 3V3A, fed from 3V3 through R164 2.2R, whose drop is neglected: Inference). Bands: every corner
    of the 3V3 window (rails(), per resistor case), D120 VF 0-0.40 V, each series pair and parallel pair at its own
    worst end (resistor case tolerance; the readings are monotonic in each element, so the corners bound them), R134
    2R at the same tolerance, match 1-2 ohm, leads 0-0.3 ohm. Cases: open (no match), healthy match, shorted match
    (0 ohm), J121 to GND, R131 bridged (the same DC network as R136 bridged: one 5.1k pull), R173 bridged (the same as R129
    bridged: one 5.1k divider top), each with and without a match. Zero leakage, ADC offset and reference error.
    Calculation on the netlist values; VF, the match and the R164 drop Inference."""
    import itertools

    def node(v, vf, rp, rct, rcb, rbt, rbb, link):
        gc, gb, src = 1 / (rct + rcb), 1 / (rbt + rbb), (v - vf) / rp
        if link is None:
            vp, va = src / (1 / rp + gc), 0.0
        else:
            gl = 1 / link
            det = (1 / rp + gc + gl) * (gb + gl) - gl * gl
            vp, va = src * (gb + gl) / det, src * gl / det
        return vp * rcb / (rct + rcb), va * rbb / (rbt + rbb), vp, (v - vf - vp) / rp

    def series(pairs):
        return sum(r for _, r in pairs)

    def parallel(pairs):
        return 1 / sum(1 / r for _, r in pairs)
    v33 = rails()[V33_RAIL]
    faults = {'open': dict(match=None), 'healthy': dict(match=COLD_MATCH), 'shorted_match': dict(match=(0.0, 0.0)),
              'R131_bridged_no_match': dict(match=None, pull=COLD_PULL[:1]),
              'R131_bridged_healthy': dict(match=COLD_MATCH, pull=COLD_PULL[:1]),
              'R173_bridged_no_match': dict(match=None, cont_top=COLD_CONT_TOP[1:]),
              'R173_bridged_healthy': dict(match=COLD_MATCH, cont_top=COLD_CONT_TOP[1:])}
    out = {}
    for case, tol in TOL.items():
        vwin = (v33[case]['min_V'], v33[case]['max_V'])
        rows = {}
        for name, f in faults.items():
            nom = (series(f.get('pull', COLD_PULL)), series(f.get('cont_top', COLD_CONT_TOP)), parallel(COLD_CONT_BOT),
                   series(COLD_BUS_TOP), parallel(COLD_BUS_BOT))
            vals = []
            for v, vf, *k in itertools.product(vwin, COLD_VF, *[(1 - tol, 1 + tol)] * 6):
                links = [None] if f['match'] is None else [
                    COLD_R134 * k[5] + m + lead for m in sorted(set(f['match'])) for lead in COLD_LEADS]
                for link in links:
                    pc0, pc5, vp, i = node(v, vf, *(r * x for r, x in zip(nom, k[:5])), link)
                    vals.append((pc0, pc5, vp, i, pc0 / v, pc5 / v))
            rng = lambda j, scale, nd: [round(min(x[j] for x in vals) * scale, nd), round(max(x[j] for x in vals) * scale, nd)]
            rows[name] = dict(PC0_mV=rng(0, 1e3, 2), PC5_mV=rng(1, 1e3, 2), PYRO1_OUT_mV=rng(2, 1e3, 1),
                              pull_up_mA=rng(3, 1e3, 4), PC0_of_VDDA=rng(4, 1, 5), PC5_of_VDDA=rng(5, 1, 5))
        rows['J121_to_GND'] = dict(PC0_mV=[0.0, 0.0], PC5_mV=[0.0, 0.0],
                                   note='either terminal to GND holds PYRO1_OUT (directly, or through the match and '
                                        'R134 from RAW_ACT) and both readings at 0')
        h, o = rows['healthy'], rows['open']
        m = dict(
            open_PC0_above_healthy_mV=round(o['PC0_mV'][0] - h['PC0_mV'][1], 2),
            healthy_PC5_above_open_mV=round(h['PC5_mV'][0] - o['PC5_mV'][1], 2),
            R131_bridged_healthy_PC0_above_healthy_mV=round(rows['R131_bridged_healthy']['PC0_mV'][0] - h['PC0_mV'][1], 2),
            R131_bridged_healthy_PC5_above_healthy_mV=round(rows['R131_bridged_healthy']['PC5_mV'][0] - h['PC5_mV'][1], 2),
            R131_bridged_no_match_PC0_above_open_mV=round(rows['R131_bridged_no_match']['PC0_mV'][0] - o['PC0_mV'][1], 2),
            R173_bridged_healthy_PC0_above_healthy_mV=round(rows['R173_bridged_healthy']['PC0_mV'][0] - h['PC0_mV'][1], 2),
            R173_bridged_no_match_PC0_above_open_mV=round(rows['R173_bridged_no_match']['PC0_mV'][0] - o['PC0_mV'][1], 2),
            shorted_vs_healthy_band_edges_mV=round(max(abs(rows['shorted_match'][c][j] - h[c][j])
                                                       for c in ('PC0_mV', 'PC5_mV') for j in (0, 1)), 2))
        out[case] = dict(vdd_V=list(vwin), cases=rows, margins_mV=m)
    nominal = node(3.35, 0.25, series(COLD_PULL), series(COLD_CONT_TOP), parallel(COLD_CONT_BOT), series(COLD_BUS_TOP),
                   parallel(COLD_BUS_BOT), None)
    nominal_h = node(3.35, 0.25, series(COLD_PULL), series(COLD_CONT_TOP), parallel(COLD_CONT_BOT),
                     series(COLD_BUS_TOP), parallel(COLD_BUS_BOT), COLD_R134 + 1.5)
    out['nominal_3V35_VF_0V25'] = dict(open_PC0_mV=round(nominal[0] * 1e3, 2), healthy_PC0_mV=round(nominal_h[0] * 1e3, 2),
                                       healthy_PC5_mV=round(nominal_h[1] * 1e3, 2))
    out['topology'] = ('3V3 -> R136 5.1k -> D120 (BAT54C A1 -> K) -> R131 5.1k -> PYRO1_OUT (10.2 kohm, R12F6-TRI-01); '
                       'PYRO1_OUT -> R173 5.1k + R129 5.1k -> PC0 over R130 || R178 (2k || 2k); RAW_ACT -> R132 5.1k + '
                       'R175 5.1k -> PC5 over R133 || R180; a match joins PYRO1_OUT to RAW_ACT through R134 2R')
    out['reading'] = ('healthy needs PC5 well above 0 and PC0 inside the healthy band; open reads PC5 0; a bridge across '
                      'R131 (or R136) or R173 (or R129) with a match fitted reads above the healthy PC0 band in every '
                      'corner (margins above), so the screen refuses it; without a match every case reads PC5 0 and is '
                      'refused as open. A shorted match reads as a healthy one (band edges differ by about 0.01 mV): the '
                      'screen cannot see it, and R134 limits that case in a fire. A J121 terminal to GND reads 0 / 0. '
                      'Firmware thresholds are not set here: bench the bands (zero leakage, ADC offset and reference '
                      'error assumed)')
    out['inputs'] = dict(vf_V=list(COLD_VF), match_ohm=list(COLD_MATCH), leads_ohm=list(COLD_LEADS), R134_ohm=COLD_R134,
                         resistor_cases={k: v for k, v in TOL.items()})
    out['label'] = ('Calculation / Inference (3V3 window, D-R12-139): Calculation on the netlist values and the 3V3 '
                    'window (R12F6-TRI-03); D120 VF (BAT54C 25 C maxima extended to -42 C), the match and leads, the '
                    'R164 drop and zero leakage are Inference')
    return out


def compute():
    return dict(
        status='R12 stage A (no board): Calculation / Inference as labelled; no measurement',
        resistor_cases={k: f'+/-{v * 100:.2f} % independent' for k, v in TOL.items()},
        resistor_cases_precise={'parts': 'R401 (D-R12-83); R60 / R61 (R12F9-TRI-04, PA6_TOL)',
                                **{k: f'+/-{v * 100:.3f} % independent' for k, v in TOL_PRECISE.items()}},
        rails=rails(), cam_input=cam_input(), port_input=port_input(), u9=u9(), sense=sense(), vlogic=vlogic(), holdup=holdup(), fire=fire(), crystal=crystal(),
        cold_screen=cold_screen())


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
