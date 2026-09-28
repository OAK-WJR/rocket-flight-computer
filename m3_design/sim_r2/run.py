#!/usr/bin/env python3
"""M3-ASSY-R2 actuator-band SPICE suite (ngspice).

Builds one deck per case from the R2 netlist values (sheets 11-14), runs ngspice in
batch mode, evaluates each result against a stated limit and writes RESULTS.md and
results.json next to this file.  Decks and raw waveforms go to ./out (git-ignored).

    python3 m3_design/sim_r2/run.py

Component values are the ones in m3_design/assembly_review/*.kicad_sch (R2).  Off-board
values (battery, wiring, fuse resistance, igniter, servo) are assumptions and are
listed in ASSUMPTIONS below and in the report.
"""
import json, math, os, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'out'
MODELS = HERE / 'models.inc'
NGSPICE = shutil.which('ngspice') or sys.exit('ngspice not found (brew install ngspice)')

ASSUMPTIONS = [
    ('2S LiPo EMF', '6.0 / 7.4 / 8.4 V'),
    ('Pack internal resistance', '20 mOhm (fresh, hot) / 40 mOhm / 80 mOhm (cold, worn)'),
    ('Battery lead', '100 nH + 20 mOhm wiring + 5 mOhm in-line 15 A ATO fuse (MARGIN_PRESCRIPTION P0-3b)'),
    ('Logic load on BAT_IN through U9', '28 ohm (~0.3 A at 8.4 V); U9 itself not modelled, RAW_PROTECTED = BAT_IN x enable'),
    ('Arming-plug fuse', 'Littelfuse 217 series 5 A fast-acting 5x20 (0217005): cold R 13.7 mOhm, nominal melting I2t 42.8 A2s (datasheet table); modelled as opening when the integrated I2t reaches 42.8 A2s (arc time ignored)'),
    ('Logic brown-out', 'the R1 hold-up study (docs/SIMULATION.md) gives only ~3 ms of VLOGIC hold-up at 6.0 V / 0.5 A; any BAT_IN collapse longer than that resets the MCU'),
    ('Igniter', 'MJG bridgewire 1.2 ohm + 1 m 26 AWG (134 mOhm) + 1 uH lead (MARGIN_PRESCRIPTION fire row)'),
    ('Servo MKS HV6120 stalled', '4.385 ohm each, 1.096 ohm for all four (GEOMETRY_REV_G); cruise 1.5 A total'),
    ('Plug insertion', '10 ns contact edge, two bounces (on 10 us, off 12 us, on 14 us, off 15 us, on 17 us)'),
    ('ADC total error used for state separation', '+/-20 mV (budget, not a datasheet figure)'),
]

# thermal data (AOS datasheets): RthJA t<=10s max, RthJC max, single-pulse ZthJC read from Fig. 11
TH = {'AON6403': dict(rja10=17.0, rjc=1.5), 'AON7524': dict(rja10=40.0, rjc=3.9)}


def zth_jc_norm(t):
    """Normalised single-pulse ZthJC, read from Fig. 11 of both AOS datasheets (log interpolation)."""
    pts = [(1e-5, 0.03), (1e-4, 0.08), (1e-3, 0.3), (1e-2, 0.75), (1e-1, 0.97), (1.0, 1.0)]
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, z0), (t1, z1) in zip(pts, pts[1:]):
        if t <= t1:
            f = (math.log10(t) - math.log10(t0)) / (math.log10(t1) - math.log10(t0))
            return z0 + f * (z1 - z0)
    return 1.0


# ----------------------------------------------------------------------------- deck parts
def battery(vbat, rpack):
    return f"""
Vbat emf 0 DC {vbat}
Rpack emf b1 {rpack}
Llead b1 b2 100n
Rwire b2 BAT_IN 25m
* SMBJ9.0CA bidirectional at J1
Dt1 BAT_IN tvs TVS9
Dt2 0 tvs TVS9
Rlogic BAT_IN 0 28
"""


def act_switch(en_pwl, fet='AON6403'):
    """Sheet 11: Q120/Q121 back-to-back, C120 gate-source, Q122 driver from RAW_PROTECTED."""
    return f"""
Ven en 0 PWL({en_pwl})
Bprot RAW_PROT 0 V=max(v(BAT_IN),0)*v(en)
R122 RAW_PROT ACT_EN 100k
R123 ACT_EN 0 100k
Mq122 ACT_DRV ACT_EN 0 0 AO3400A_TYP
R121 ACT_GATE ACT_DRV 10k
R120 ACT_FET_S ACT_GATE 100k
C120 ACT_FET_S ACT_GATE 2.2u
Vi120 BAT_IN D120 0
Xq120 D120 ACT_GATE ACT_FET_S {fet}
Xq121 D121 ACT_GATE ACT_FET_S {fet}
Vi121 D121 RAW_ACT 0
C121 RAW_ACT c121 470u
Rc121 c121 0 25m
C150 RAW_ACT 0 44u
R124 RAW_ACT RAW_ACT_SENSE 10k
R125 RAW_ACT_SENSE 0 4.7k
C122 RAW_ACT_SENSE 0 10n
Bp120 p120 0 V=(v(D120)-v(ACT_FET_S))*i(Vi120)
Bp121 p121 0 V=(v(ACT_FET_S)-v(D121))*i(Vi121)
"""


def pin_driver(node, state, ctrl_pwl='0 3.3', strong=False):
    """STM32 FT pin. state: 'drive' (ctrl PWL: 3.3 = output low, 0 = output high), 'low', 'hiz'."""
    kp = "4" if strong else ""
    if state == 'hiz':   # MCU unpowered / in reset: FT pin has only a diode to VSS
        return f"Dpin 0 {node} DPINLO\n"
    if state == 'low':
        ctrl_pwl = '0 3.3'
    return f"""
Vdd vdd 0 3.3
Vctl pinctl 0 PWL({ctrl_pwl})
Mp {node} pinctl vdd vdd PDRV{kp}
Mn {node} pinctl 0 0 NDRV{kp}
Dpin 0 {node} DPINLO
"""


def pyro_channel(fet='AON7524', c126=True, bridge='1.2', lead_r='0.134', lead_l='1u', plug_pwl='0 1', rser='1u', fuse_i2t=42.8):
    """Sheet 12, channel 1, exactly as drawn: plug (J120 pins 4->3 through F1), igniter J121 1-2."""
    c = "C126 PYRO1_GATE 0 220n\n" if c126 else "* C126 omitted (fault case)\n"
    return f"""
V3v3 V3V3 0 3.3
Vplug plugc 0 PWL({plug_pwl})
Splug RAW_ACT f1 plugc 0 SWPLUG
.model SWPLUG SW(Ron=5m Roff=1e9 Vt=0.5 Vh=0)
Vif1 f1 f1a 0
Sfuse f1a f1b fctl 0 SWFUSE
.model SWFUSE SW(Ron=13.7m Roff=1e6 Vt=0.5 Vh=0.1)
Bi2t 0 i2t I=(time > 0) ? i(Vif1)*i(Vif1) : 0
Ci2t i2t 0 1
Ri2t i2t 0 1e12
Bfctl fctl 0 V=v(i2t) < {fuse_i2t} ? 1 : 0
Lf1 f1b PYRO1_BUS_R 20n
Rser PYRO1_BUS_R PYRO1_BUS {rser}
R132 PYRO1_BUS ARM1_SENSE 10k
R133 ARM1_SENSE 0 1k
C129 ARM1_SENSE 0 10n
Lig PYRO1_BUS ig1 {lead_l}
Rlead ig1 ig2 {lead_r}
Rbw ig2 ig3 {bridge}
Vibw ig3 PYRO1_OUT 0
C128 PYRO1_OUT 0 100n
R129 PYRO1_OUT PYRO1_CONT 10k
R130 PYRO1_CONT 0 1k
C127 PYRO1_CONT 0 10n
R131 PYRO1_OUT PYRO1_COLD 47k
D120 V3V3 PYRO1_COLD BAT54
R127 PYRO1_GATE_N 0 1k
R126 PYRO1_GATE_N PYRO1_GATE 220
R128 PYRO1_GATE 0 10k
{c}Vid PYRO1_OUT dq 0
Xq124 dq PYRO1_GATE 0 {fet}
Bp124 p124 0 V=v(PYRO1_OUT)*i(Vid)
"""


def deck(title, body, analysis, vecs):
    return f"""* {title}
.include {MODELS}
.model NDRV4 NMOS(LEVEL=1 VTO=1.15  KP=41m IS=1e-30)
.model PDRV4 PMOS(LEVEL=1 VTO=-1.15 KP=41m IS=1e-30)
{body}
.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
option numdgt=7
{analysis}
wrdata {{OUTFILE}} {' '.join(vecs)}
quit
.endc
.end
"""


def run(name, text):
    OUT.mkdir(exist_ok=True)
    dat = OUT / f'{name}.dat'
    cir = OUT / f'{name}.cir'
    cir.write_text(text.replace('{OUTFILE}', str(dat)))
    p = subprocess.run([NGSPICE, '-b', str(cir)], capture_output=True, text=True)
    (OUT / f'{name}.log').write_text(p.stdout + p.stderr)
    if not dat.exists():
        raise RuntimeError(f'{name}: ngspice produced no data\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}')
    lines = dat.read_text().split('\n')
    head = lines[0].split()
    cols = {h: [] for h in head}
    for ln in lines[1:]:
        if ln.strip():
            for h, v in zip(head, ln.split()):
                cols[h].append(float(v))
    return cols


def col(d, name):
    for k in d:
        if k.lower() == name.lower():
            return d[k]
    raise KeyError(f'{name} not in {list(d)}')


def integ(t, y, t0=None, t1=None):
    s = 0.0
    for i in range(1, len(t)):
        if (t0 is None or t[i] >= t0) and (t1 is None or t[i] <= t1):
            s += 0.5 * (y[i] + y[i - 1]) * (t[i] - t[i - 1])
    return s


def first_cross(t, y, level, rising=True, after=0.0):
    for i in range(1, len(t)):
        if t[i] < after:
            continue
        if (rising and y[i - 1] < level <= y[i]) or (not rising and y[i - 1] > level >= y[i]):
            return t[i]
    return None


def pulse_stats(t, p):
    """energy, peak power, equivalent width (E/Ppk) and the two junction-rise bounds."""
    e = integ(t, p)
    pk = max(p)
    w = e / pk if pk > 0 else 0.0
    return e, pk, w


def zth(part, t):
    """Junction-to-ambient step response used for the convolution: package ZthJC(t) from
    Fig. 11, plus the board copper heating linearly up to RthJA(t<=10 s) at 10 s."""
    th = TH[part]
    return zth_jc_norm(max(t, 1e-6)) * th['rjc'] + (th['rja10'] - th['rjc']) * min(t, 10.0) / 10.0


def tj_peak(part, t, p, nbin=600):
    """Peak junction rise by superposition of power steps through zth()."""
    t0, t1 = t[0], t[-1]
    dt = (t1 - t0) / nbin
    bins = [0.0] * nbin
    for i in range(1, len(t)):
        k = min(int((t[i] - t0) / dt), nbin - 1)
        bins[k] += 0.5 * (p[i] + p[i - 1]) * (t[i] - t[i - 1]) / dt
    steps = [bins[0]] + [bins[k] - bins[k - 1] for k in range(1, nbin)]
    zt = [zth(part, (j + 1) * dt) for j in range(nbin)]
    best = 0.0
    for i in range(nbin):
        tj = sum(steps[k] * zt[i - k] for k in range(i + 1) if steps[k])
        best = max(best, tj)
    return best


RESULTS = []


def res(case, item, value, limit, verdict, note=''):
    RESULTS.append(dict(case=case, item=item, value=value, limit=limit, verdict=verdict, note=note))


# ----------------------------------------------------------------------------- cases
def actuator_on_off():
    case = 'A. Actuator switch (sheet 11)'
    loads = [('no load', None), ('cruise 1.5 A', 5.6), ('4 servos stalled', 1.096)]
    for vbat, rpack in [(6.0, 0.08), (8.4, 0.02)]:
        for lname, rl in loads:
            for fet in ['AON6403', 'AON6403S']:
                load = f"Rservo RAW_ACT 0 {rl}\n" if rl else ''
                body = battery(vbat, rpack) + act_switch('0 0 10m 0 11m 1 700m 1 701m 0', fet=fet) + load
                name = f'act_{vbat}_{lname.split()[0]}_{fet}'.replace('.', 'v')
                d = run(name, deck(name, body, 'tran 20u 2.2 0 50u',
                                   ['v(RAW_ACT)', 'v(BAT_IN)', 'v(ACT_GATE)', 'v(ACT_FET_S)', 'v(p120)', 'v(p121)', 'i(Vi121)']))
                t = col(d, 'time')
                vr = col(d, 'v(RAW_ACT)')
                p121 = col(d, 'v(p121)')
                p120 = col(d, 'v(p120)')
                tag = f'{vbat} V, {lname}, {"slow-corner FET" if fet.endswith("S") else "typ FET"}'
                # turn-on window 10 ms .. 700 ms
                on_t = [x for x in t if 0.01 <= x <= 0.7]
                i0 = t.index(on_t[0]); i1 = t.index(on_t[-1])
                t_on, p_on = t[i0:i1], [a + b for a, b in zip(p121[i0:i1], p120[i0:i1])]
                v_final = vr[i1 - 1]
                t95 = first_cross(t, vr, 0.95 * v_final, True, 0.01)
                e, pk, w = pulse_stats(t_on, p121[i0:i1])
                dtj = tj_peak('AON6403', t_on, p121[i0:i1])
                res(case, f'turn-on {tag}: RAW_ACT 95 %', f'{(t95 - 0.011) * 1e3:.1f} ms after enable' if t95 else 'never',
                    '< 100 ms (bring-up)', 'PASS' if t95 and t95 - 0.011 < 0.1 else 'FAIL')
                res(case, f'turn-on {tag}: Q121 pulse', f'E {e * 1e3:.1f} mJ, Ppk {pk:.1f} W, peak dTj {dtj:.1f} K',
                    'Tj 150 C from 60 C ambient -> dTj < 90 K', 'PASS' if dtj < 90 else 'FAIL')
                # turn-off window 700 ms .. 2.2 s
                j0 = next(i for i, x in enumerate(t) if x >= 0.7)
                t_off, poff = t[j0:], p121[j0:]
                e, pk, w = pulse_stats(t_off, poff)
                dtj = tj_peak('AON6403', t_off, poff)
                t10 = first_cross(t, vr, 0.1 * v_final, False, 0.701)
                res(case, f'turn-off {tag}: Q121 pulse', f'E {e * 1e3:.0f} mJ, Ppk {pk:.1f} W, peak dTj {dtj:.1f} K; ' + (f'RAW_ACT < 10 % after {(t10 - 0.701) * 1e3:.0f} ms' if t10 else 'RAW_ACT bleeds down slowly (no load)'),
                    'dTj < 90 K', 'PASS' if dtj < 90 else 'FAIL')


def pyro_fire():
    case = 'B. Pyro channel fire (sheet 12)'
    for vbat, rpack, fet in [(6.0, 0.08, 'AON7524MAX'), (8.4, 0.02, 'AON7524')]:
        for strong in [False, True]:
            body = (battery(vbat, rpack) + act_switch('0 1 1 1') +
                    pyro_channel(fet=fet) + pin_driver('PYRO1_GATE_N', 'drive', '0 3.3 100u 3.3 100.01u 0', strong))
            name = f'fire_{vbat}_{fet}_{"strong" if strong else "weak"}'.replace('.', 'v')
            d = run(name, deck(name, body, 'tran 100n 3m 0 200n',
                               ['v(PYRO1_GATE)', 'v(PYRO1_GATE_N)', 'i(Vibw)', 'v(p124)', 'v(BAT_IN)', 'v(RAW_ACT)', 'i(Vdd)']))
            t = col(d, 'time'); vg = col(d, 'v(PYRO1_GATE)'); ib = col(d, 'i(Vibw)'); idd = col(d, 'i(Vdd)')
            tg = first_cross(t, vg, 2.5, True, 100e-6)
            tag = f'{vbat} V, {"max-RDS FET" if "MAX" in fet else "typ FET"}, {"strong" if strong else "weakest-legal"} GPIO'
            res(case, f'{tag}: gate reaches 2.5 V', f'{(tg - 100e-6) * 1e6:.0f} us' if tg else 'never', '< 1 ms', 'PASS' if tg and tg - 100e-6 < 1e-3 else 'FAIL')
            res(case, f'{tag}: final VGS', f'{vg[-1]:.2f} V', '>= 2.5 V (RDS(on) spec point) and <= 12 V', 'PASS' if 2.5 <= vg[-1] <= 12 else 'FAIL')
            res(case, f'{tag}: bridgewire current', f'{ib[-1]:.2f} A steady', '>= 1.0 A recommended all-fire (MJG), 0.6 A minimum',
                'PASS' if ib[-1] >= 1.0 else 'FAIL')
            res(case, f'{tag}: GPIO peak source current', f'{max(-x for x in idd) * 1e3:.1f} mA', '<= 20 mA (DS12110 IIO)',
                'PASS' if max(-x for x in idd) <= 0.020 else 'FAIL')
            p = col(d, 'v(p124)')
            res(case, f'{tag}: FET dissipation while firing', f'{p[-1]:.2f} W', f'< PDSM 3.1 W', 'PASS' if p[-1] < 3.1 else 'FAIL')


def pyro_short():
    case = 'C. Shorted igniter on channel 1 (fired into a short), fuse melting at its I2t'
    for where, br, lr, ll in [('short at J121 terminal', '1m', '5m', '50n'), ('short at the igniter end of 1 m lead', '1m', '0.134', '1u')]:
        for vbat, rpack in [(8.4, 0.02), (7.4, 0.04), (6.0, 0.08)]:
            for rser in ['1u', '1.0']:
                fix = rser != '1u'
                body = (battery(vbat, rpack) + act_switch('0 1 1 1') +
                        pyro_channel(fet='AON7524MAX', bridge=br, lead_r=lr, lead_l=ll, rser=rser) +
                        pin_driver('PYRO1_GATE_N', 'drive', '0 3.3 100u 3.3 100.01u 0'))
                name = f'short_{"term" if "J121" in where else "far"}_{vbat}_{"fix" if fix else "asdrawn"}'.replace('.', 'v')
                tend = '200m' if fix else '60m'
                d = run(name, deck(name, body, f'tran 1u {tend} 0 2u', ['i(Vibw)', 'v(p124)', 'v(BAT_IN)', 'v(i2t)', 'v(fctl)']))
                t = col(d, 'time'); ib = col(d, 'i(Vibw)'); p = col(d, 'v(p124)'); vb = col(d, 'v(BAT_IN)'); fc = col(d, 'v(fctl)')
                topen = first_cross(t, fc, 0.5, False, 0)
                dtj = tj_peak('AON7524', t, p)
                below = sum(t[i] - t[i - 1] for i in range(1, len(t)) if vb[i] < 5.0)
                tag = f'{where}, {vbat} V pack {int(rpack * 1e3)} mOhm' + (', PROPOSED 1.0 ohm series resistor' if fix else ', as drawn')
                res(case, f'{tag}: peak current / fuse', f'{max(ib):.1f} A; fuse opens at ' + (f'{(topen - 100e-6) * 1e3:.1f} ms' if topen else f'> {tend}s (does not open)'),
                    '< IDM 112 A', 'PASS' if max(ib) < 112 else 'FAIL')
                res(case, f'{tag}: AON7524 junction', f'peak dTj {dtj:.0f} K', 'dTj < 90 K (Tj 150 C from 60 C)', 'PASS' if dtj < 90 else 'FAIL')
                res(case, f'{tag}: BAT_IN', f'min {min(vb[5:]):.2f} V, below 5.0 V for {below * 1e3:.1f} ms',
                    'below 5.0 V for < 3 ms (R1 hold-up study, 6.0 V corner) so the MCU does not reset and channel 2 still fires', 'PASS' if below < 3e-3 else 'FAIL')
    # the proposed series resistor must not starve a good igniter
    for vbat, rpack in [(6.0, 0.08)]:
        body = (battery(vbat, rpack) + act_switch('0 1 1 1') + pyro_channel(fet='AON7524MAX', rser='1.0') +
                pin_driver('PYRO1_GATE_N', 'drive', '0 3.3 100u 3.3 100.01u 0'))
        d = run('fire_fix_6v0', deck('fire_fix', body, 'tran 1u 3m 0 2u', ['i(Vibw)']))
        i = col(d, 'i(Vibw)')[-1]
        res(case, 'PROPOSED 1.0 ohm: fire current at the worst corner (6.0 V, 80 mOhm, 1.2 ohm + 1 m 26 AWG)', f'{i:.2f} A',
            '>= 1.0 A recommended all-fire (MJG)', 'PASS' if i >= 1.0 else 'FAIL')
        res(case, 'PROPOSED 1.0 ohm: resistor pulse energy during a 20 ms fire at 8.4 V', f'{(8.4 / (1.2 + 0.134 + 1.0 + 0.1)) ** 2 * 1.0 * 0.02 * 1e3:.0f} mJ',
            'needs a pulse-rated 2512 (e.g. >= 1 J / 20 ms class); part not chosen', 'INFO')


def plug_insertion():
    case = 'D. ARM plug insertion, FET off (Miller self-turn-on)'
    bounce = '0 0 10u 0 10.01u 1 12u 1 12.01u 0 14u 0 14.01u 1 15u 1 15.01u 0 17u 0 17.01u 1'
    for c126 in [True, False]:
        for state in ['hiz', 'low']:
            body = (battery(8.4, 0.02) + act_switch('0 1 1 1') +
                    pyro_channel(fet='AON7524MIN', c126=c126, plug_pwl=bounce) + pin_driver('PYRO1_GATE_N', state))
            name = f'plug_{"c126" if c126 else "noc126"}_{state}'
            d = run(name, deck(name, body, 'tran 1n 200u 0 2n', ['v(PYRO1_GATE)', 'i(Vibw)', 'v(PYRO1_OUT)', 'i(Vid)']))
            t = col(d, 'time'); vg = col(d, 'v(PYRO1_GATE)'); ib = col(d, 'i(Vibw)'); idr = col(d, 'i(Vid)')
            i2t = integ(t, [x * x for x in ib])
            tag = f'{"C126 fitted" if c126 else "C126 MISSING (fault)"}, MCU {"unpowered/reset" if state == "hiz" else "driving low"}'
            vpk = max(vg)
            verdict = 'PASS' if vpk < 0.4 else 'FAIL'
            if not c126:
                verdict = 'DEMO'   # deliberate fault injection: shows why C126 is required
            res(case, f'{tag}: peak VGS', f'{vpk * 1e3:.0f} mV', '< VGS(th) min 0.4 V', verdict)
            res(case, f'{tag}: igniter transient', f'peak {max(abs(x) for x in ib):.2f} A, I2t {i2t * 1e6:.2f} uA2s; FET peak {max(idr):.3f} A',
                'no-fire 0.30 A continuous (MJG); I2t << 1 mA2s', 'PASS' if i2t < 1e-3 else 'FAIL')


def sense_table():
    case = 'E. Continuity / arm-sense states (split buses, cold pull-up)'
    states = [
        ('plug out, igniter OK, FET OK', False, True, False),
        ('plug out, igniter OPEN, FET OK', False, False, False),
        ('plug out, igniter OK, FET SHORTED', False, True, True),
        ('plug out, igniter OPEN, FET SHORTED', False, False, True),
        ('plug in, igniter OK, FET OK', True, True, False),
        ('plug in, igniter OPEN, FET OK', True, False, False),
    ]
    table = {}
    for label, plug, ig, short in states:
        vals = []
        for vbat in (6.0, 8.4):
            for v33 in (3.135, 3.465):
                body = (battery(vbat, 0.04) + act_switch('0 1 1 1') +
                        pyro_channel(bridge='1.2' if ig else '1e9', plug_pwl='0 1' if plug else '0 0').replace('V3v3 V3V3 0 3.3', f'V3v3 V3V3 0 {v33}') +
                        pin_driver('PYRO1_GATE_N', 'low') + ('Rshort PYRO1_OUT 0 10m\n' if short else ''))
                name = 'sense_' + re.sub(r'\W+', '_', label) + f'_{vbat}_{v33}'
                d = run(name, deck(name, body, 'tran 1m 20m', ['v(PYRO1_CONT)', 'v(ARM1_SENSE)']))
                vals.append((col(d, 'v(PYRO1_CONT)')[-1], col(d, 'v(ARM1_SENSE)')[-1]))
        c = [v[0] for v in vals]; a = [v[1] for v in vals]
        # +/-2 % for 1 % resistor pairs
        table[label] = dict(cont=(min(c) * 0.98, max(c) * 1.02), arm=(min(a) * 0.98, max(a) * 1.02))
        res(case, label, f'CONT {min(c) * 980:.1f}..{max(c) * 1020:.1f} mV, ARM {min(a) * 980:.1f}..{max(a) * 1020:.1f} mV', '', 'INFO')
    # ground checks the firmware must make with the plug OUT
    adc = 0.020
    def gap(x, y, k):
        return max(table[x][k][0], table[y][k][0]) - min(table[x][k][1], table[y][k][1])
    for x, y, k, why in [
            ('plug out, igniter OK, FET OK', 'plug out, igniter OK, FET SHORTED', 'cont', 'detect a shorted FET before the plug goes in (FMEA H-1)'),
            ('plug out, igniter OK, FET OK', 'plug out, igniter OPEN, FET OK', 'cont', 'igniter continuity with the plug out'),
            ('plug in, igniter OK, FET OK', 'plug out, igniter OK, FET OK', 'arm', 'bus armed vs not armed'),
            ('plug in, igniter OK, FET OK', 'plug in, igniter OPEN, FET OK', 'cont', 'igniter continuity with the plug in')]:
        g = gap(x, y, k)
        res(case, f'separation: {why}', f'{g * 1e3:.1f} mV gap between worst-case ranges', f'> 2 x {adc * 1e3:.0f} mV ADC error',
            'PASS' if g > 2 * adc else ('MARGINAL' if g > 0 else 'FAIL'))
    # ADC node limits at the TVS clamp
    for vclamp in (8.4, 15.4):
        ok = vclamp * 4.7 / 14.7 <= 3.3
        res(case, f'ADC node voltage at RAW_ACT = {vclamp} V', f'ARM/CONT {vclamp / 11:.2f} V, RAW_ACT_SENSE {vclamp * 4.7 / 14.7:.2f} V' + ('' if ok else ' (TVS-clamp transient only; < 0.2 mA through R124)'),
            'analog-mode pin <= VDDA 3.3 V', 'PASS' if ok else 'INFO')


def servo_chafe():
    case = 'F. Servo signal chafed onto RAW_ACT (sheet 13)'
    for vs in (8.4, 10.5):
        for state in ['low', 'high', 'hiz']:
            for strong in ([False, True] if state != 'hiz' else [False]):
                pin = pin_driver('SERVO1_MCU', 'drive', '0 3.3' if state == 'low' else '0 0', strong) if state != 'hiz' else pin_driver('SERVO1_MCU', 'hiz')
                body = f"""
V3v3 V3V3 0 3.3
Vchafe SERVO1_OUT 0 {vs}
R150 SERVO1_MCU SERVO1_OUT 1k
R154 SERVO1_MCU 0 10k
Dsu SERVO1_MCU vsrv DSTEER
Vsrv vsrv V3V3 0
Dsd 0 SERVO1_MCU DSTEER
Dtv 0 V3V3 DTVS6
""" + pin
                name = f'servo_{vs}_{state}_{"s" if strong else "w"}'.replace('.', 'v')
                d = run(name, deck(name, body, 'tran 1u 100u', ['v(SERVO1_MCU)', 'i(Vchafe)', 'i(Vsrv)'] + (['i(Vdd)'] if state != 'hiz' else [])))
                vm = col(d, 'v(SERVO1_MCU)')[-1]; ich = -col(d, 'i(Vchafe)')[-1]; isr = col(d, 'i(Vsrv)')[-1]
                ipin = ich - isr - vm / 10e3
                tag = f'{vs} V chafe, pin {state}{" (strong silicon)" if strong else ""}'
                pr = (vs - vm) ** 2 / 1e3
                res(case, f'{tag}: pin current', f'{ipin * 1e3:.1f} mA (node {vm:.2f} V, SRV05 {isr * 1e3:.1f} mA)',
                    '|IIO| <= 20 mA, node <= VDD+4 V', 'PASS' if abs(ipin) <= 0.020 and vm <= 7.3 else 'FAIL')
                res(case, f'{tag}: R150 dissipation', f'{pr * 1e3:.0f} mW', '<= 125 mW (0805)', 'PASS' if pr <= 0.125 else 'FAIL')


def pullpin_chafe():
    case = 'G. Pull-pin line chafed onto RAW_ACT (sheet 14)'
    for vs in (8.4, 10.5):
        body = f"""
V3v3 V3V3 0 3.3
Vchafe PULLPIN_EXT 0 {vs}
R160 PULLPIN_EXT PULLPIN 1k
R161 V3V3 PULLPIN 10k
C160 PULLPIN 0 100n
Dhi PULLPIN d3 BAT54
Vd3 d3 V3V3 0
Dlo 0 PULLPIN BAT54
Dpin 0 PULLPIN DPINLO
"""
        name = f'pullpin_{vs}'.replace('.', 'v')
        d = run(name, deck(name, body, 'tran 1u 2m', ['v(PULLPIN)', 'i(Vd3)']))
        vm = col(d, 'v(PULLPIN)')[-1]; i3 = col(d, 'i(Vd3)')[-1]
        res(case, f'{vs} V chafe: PC14 node', f'{vm:.2f} V, {i3 * 1e3:.1f} mA pushed into 3V3', 'FT pin <= VDD+4 = 7.3 V; 3V3 load must exceed the back-feed',
            'PASS' if vm <= 7.3 else 'FAIL')
        res(case, f'{vs} V chafe: R160 dissipation', f'{(vs - vm) ** 2:.0f} mW', '<= 62.5 mW (R160 is 0402)', 'PASS' if (vs - vm) ** 2 <= 62.5 else 'FAIL')


def write_report():
    ver = subprocess.run([NGSPICE, '-v'], capture_output=True, text=True).stdout
    ver = next((l.strip('* ').strip() for l in ver.splitlines() if 'ngspice-' in l), 'ngspice')
    counts = {}
    for r in RESULTS:
        counts[r['verdict']] = counts.get(r['verdict'], 0) + 1
    out = ['# M3-ASSY-R2 actuator band - SPICE results', '',
           f'Generated by `python3 m3_design/sim_r2/run.py` ({ver}). Do not edit by hand; edit `run.py` and re-run.', '',
           'These are **simulations of the schematic as drawn**, with datasheet-fitted level-1 models. They do not replace the',
           'bench tests listed in `docs/M3_ACTUATOR_MERGE.md` section 4. See `FINDINGS.md` for the interpretation.', '',
           '**Verdict counts:** ' + ', '.join(f'{k} {v}' for k, v in sorted(counts.items())), '',
           '`DEMO` rows are deliberate fault injections (a part removed) that show why the part is needed; they are expected to exceed the limit.', '',
           '## Assumptions (off-board values)', '', '| Item | Value |', '|---|---|']
    out += [f'| {a} | {b} |' for a, b in ASSUMPTIONS]
    case = None
    for r in RESULTS:
        if r['case'] != case:
            case = r['case']
            out += ['', f'## {case}', '', '| Item | Result | Limit | Verdict |', '|---|---|---|---|']
        out.append(f"| {r['item']} | {r['value']} | {r['limit']} | **{r['verdict']}** |")
    (HERE / 'RESULTS.md').write_text('\n'.join(out) + '\n')


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    for f in (actuator_on_off, pyro_fire, pyro_short, plug_insertion, sense_table, servo_chafe, pullpin_chafe):
        print('running', f.__name__, flush=True)
        f()
    (HERE / 'results.json').write_text(json.dumps(dict(assumptions=ASSUMPTIONS, results=RESULTS), indent=1))
    write_report()
    counts = {}
    for r in RESULTS:
        k = r['verdict'].split()[0]
        counts[k] = counts.get(k, 0) + 1
    print(counts)
    return counts


if __name__ == '__main__':
    main()
