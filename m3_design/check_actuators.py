#!/usr/bin/env python3
"""Safety contract for the single-channel actuators (R6, kept in R7), read from the saved PCB (pad nets), not the schematic.

R7 removed the R6 telemetry port (J130/J131, U14-U16 and their parts), so its rules and pinned codes are gone; the
radio and GNSS now on the board are checked by tools/check_r7.py.

usage: python3 m3_design/check_actuators.py [board.kicad_pcb]      exit 0 = every rule holds

These rules restate AGENTS.md §2 and docs/M3_ACTUATOR_MERGE.md in machine-checkable form. They
qualify the CAD netlist only: no electrical, thermal or physical behaviour is proven here.
"""
import hashlib
import re
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'quality_audit'))
from sexpr import read, properties  # noqa: E402


def pad_nets(text, lcsc=None, side=None):
    pins, vals = {}, {}
    for fp in read(text).children('footprint'):
        ref = properties(fp)['Reference'].items[2].atom
        vals[ref] = properties(fp)['Value'].items[2].atom
        if lcsc is not None and 'LCSC' in properties(fp):
            lcsc[ref] = properties(fp)['LCSC'].items[2].atom
        if side is not None:
            side[ref] = fp.children('layer')[0].items[1].atom
        for p in fp.children('pad'):
            num = p.items[1].atom
            if num:
                n = p.children('net')
                pins[f'{ref}.{num}'] = n[0].items[-1].atom if n else None
    return pins, vals


def volts(value):
    """Voltage rating in a value string such as '100nF 50V X7R 10%' (0 when none is given)."""
    m = re.search(r'(\d+(?:\.\d+)?)V\b', value or '')
    return float(m.group(1)) if m else 0.0


POWER = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
SENSE = ('ARM1_SENSE', 'PYRO1_CONT', 'PYRO1_COLD')
MIDS = ('PYRO1_CONT_MID', 'ARM1_SENSE_MID')   # pass 11: split divider tops
GATES = ('PYRO1_GATE', 'PYRO1_GATE_N')
# m3.kicad_dru rule name -> (minimum clearance mm, nets its condition must name); pass 3 checks content, not only names
PYRO_RULES = {'Pyro A: RAW_ACT to pyro control': (0.5, ('RAW_ACT',) + GATES + SENSE + MIDS),
              'Pyro B: bus, igniter and drain to gate': (0.5, POWER + GATES),
              'Pyro C: bus, igniter and drain to sense': (0.3, POWER + SENSE + MIDS),
              'Pyro D: GND to bus, igniter and drain': (0.5, ('GND',) + POWER),
              'Pyro E: RAW_ACT to bus and igniter (ARM break)': (1.0, ('RAW_ACT',) + POWER[:2]),
              'Pyro F: bus, igniter and drain to other live nets': (0.5, POWER),
              'Pyro G: gate nets in the pyro block': (0.3, GATES + ('PYRO_BLOCK',)),
              'Pyro A2: RAW_ACT to RAW_ACT_SENSE': (0.3, ('RAW_ACT', 'RAW_ACT_SENSE')),
              # pass 13: exposed live and midpoint pads 1.0 mm from sense and gate pads (one solder bridge); pass 14 adds
              # the actuator switch's gate nets
              'Pyro H: live pads to sense and gate pads (solder bridge)':
                  (1.0, POWER + ('RAW_ACT', 'ARM1_SENSE', 'PYRO1_CONT', 'RAW_ACT_SENSE')
                   + GATES + ('ACT_GATE', 'ACT_DRV') + MIDS + ('RAW_ACT_SENSE_MID',))}
# pass 6: each pyro rule's full text is pinned (a narrowing condition such as A.Layer == 'In1.Cu' passed every other
# test); after a deliberate, reviewed rule change, update the hash printed by the failure message
PYRO_RULE_SHA = {
    'Pyro A: RAW_ACT to pyro control': '10e272f336d0be5f',
    'Pyro B: bus, igniter and drain to gate': '192931f194447748',
    'Pyro C: bus, igniter and drain to sense': 'ce5407466ab8bbb5',
    'Pyro D: GND to bus, igniter and drain': 'ad70c6cba4079ae0',
    'Pyro E: RAW_ACT to bus and igniter (ARM break)': '8bd3bd35c70a4107',
    'Pyro F: bus, igniter and drain to other live nets': '6149f1b365d67b31',
    'Pyro G: gate nets in the pyro block': 'df27324c1d4f54a6',
    'Pyro A2: RAW_ACT to RAW_ACT_SENSE': 'c7771c0291e02e3d',
    'Pyro H: live pads to sense and gate pads (solder bridge)': '2826f2e9f5038349',
}
# pass 7: the whole m3.kicad_dru is pinned too. KiCad applies the last matching rule, so a later or duplicate rule (or an
# unconditional low clearance) overrode the pinned blocks, and a syntax error makes kicad-cli drop every custom rule
# silently. After a deliberate, reviewed edit of the file, update this hash from the failure message.
DRU_SHA = '1674d58be79ae428'   # R7: the RF-strip rules added before the pyro rules (reviewed; pyro blocks unchanged)
# safety-relevant parts pinned by LCSC code (value text alone let a BAT54C, an AO3400A or a plain 1206 resistor pass)
PINNED = {'R134': 'C3013496',
 'Q124': 'C431195',
 'D120': 'C8591',
 'C126': 'C21120',
 'R126': 'C17557',
 'R127': 'C11702',
 'R128': 'C25744',
 'C128': 'C161115',
 'D121': 'C13612',
 'Q120': 'C2760089',
 'Q121': 'C2760089',
 'Q122': 'C20917',
 'D8': 'C83849',
 'U9': 'C3662793',
 'R80': 'C23178',
 'R165': 'C23178',
 'R81': 'C23024',
 'C87': 'C23630',
 'R82': 'C4241878',
 'R83': 'C705755',
 'R84': 'C861551',
 'C120': 'C23630',
 'C121': 'C46550466',
 'R120': 'C25741',
 'R121': 'C25744',
 'C80': 'C13585',
 'C96': 'C13585',
 'C89': 'C12891',
 'C95': 'C12891',
 'R166': 'C25468',
 'R167': 'C25804',
 'J124': 'C430601',
 'J121': 'C430601',
 'J1': 'C2915641',
 'J9': 'C161692',
 'R129': 'C25905',
 'R132': 'C25905',
 'R124': 'C25905',
 'R173': 'C25905',
 'R175': 'C25905',
 'R177': 'C25905',
 'R130': 'C4109',
 'R133': 'C4109',
 'R125': 'C4109',
 'R178': 'C4109',
 'R180': 'C4109',
 'R182': 'C4109',
 'R168': 'C25900',
 'R170': 'C25900',
 'R172': 'C25900',
 'R150': 'C17513',
 'R151': 'C17513',
 'R152': 'C17513',
 'R153': 'C17513',
 'R154': 'C25744',
 'R155': 'C25744',
 'R156': 'C25744',
 'R157': 'C25744',
 'R122': 'C25741',
 'R123': 'C25741'}
# pass 9 (actuators F3): the load switch's nets, pinned exactly; a GND short on ACT_GATE or ACT_DRV left Q120/Q121 on with
# the power switch open (the pyro bus straight from the battery) and passed every other rule
ACT_NETS = {'ACT_GATE': {'C120.2', 'Q120.4', 'Q121.4', 'R120.2', 'R121.1', 'TP121.1'},
            'ACT_DRV': {'Q122.3', 'R121.2'},
            'ACT_EN': {'Q122.1', 'R122.2', 'R123.1'},
            'ACT_FET_S': {'C120.1', 'Q120.1', 'Q120.2', 'Q120.3', 'Q121.1', 'Q121.2', 'Q121.3', 'R120.1'},
            'RAW_ACT': {'C121.1', 'C150.1', 'C151.1', 'J122.2', 'J122.5', 'J122.8', 'J122.11', 'J124.2',
                        'Q121.5', 'Q121.6', 'Q121.7', 'Q121.8', 'Q121.9', 'R177.1', 'TP120.1'}}


def rule_block(dru, name):
    i = dru.find(f'(rule "{name}"')
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(dru)):
        depth += {'(': 1, ')': -1}.get(dru[j], 0)
        if depth == 0:
            return dru[i:j + 1]
    return None


def check(text, dru=None):
    part, side = {}, {}
    pin, val = pad_nets(text, part, side)
    fpname = {properties(fp)['Reference'].items[2].atom: fp.items[1].atom for fp in read(text).children('footprint')}
    members = {}
    for p, n in pin.items():
        if n: members.setdefault(n, set()).add(p)
    issues = []
    def req(ok, msg):
        if not ok: issues.append(msg)
    removed = ['C138',
     'C139',
     'C140',
     'C141',
     'J120',
     'J125',
     'Q125',
     'R135',
     'R138',
     'R139',
     'R140',
     'R141',
     'R142',
     'R143',
     'R144',
     'R145',
     'R169',
     'R171',
     'R174',
     'R176',
     'R179',
     'R181',
     'TP123']
    req(not (set(removed) & set(val)), 'R6 must contain no removed CH2 components')
    req(not any(n.startswith(('PYRO2', 'ARM2')) for n in members), 'R6 must contain no CH2 net')
    # 1. arming break: each bus touches only its ARM pin, its arm-sense upper arm and its series
    #    resistor; the igniter side of that resistor touches only the igniter terminal
    req(members.get('PYRO1_BUS') == {'J124.1', 'R134.2', 'R132.1'}, 'PYRO1_BUS must be {J124.1, R134.2, R132.1}')
    req(members.get('PYRO1_IGN') == {'J121.2', 'R134.1'}, 'PYRO1_IGN must be {J121.2, R134.1}')
    # 1b. shorted-igniter current limit (sim_r2/FINDINGS.md 1): 2 ohm pulse-rated 2512 per channel
    for r in ('R134',):
        req(val.get(r) == '2R 1% 2W pulse', f'{r} must be the 2 ohm 2 W pulse resistor')
    # 1c. cold pull-up strength (sim_r2/FINDINGS.md 2): 10k keeps the plug-out states apart
    for r in ('R131',):
        req(val.get(r) == '10k', f'{r} cold pull-up must be 10k')
    req({'J124.2'} <= members.get('RAW_ACT', set()), 'ARM terminal outer pins must be RAW_ACT')
    req(not ({'J124.1'} & members.get('RAW_ACT', set())), 'no ARM bus pin may be RAW_ACT')
    # 2. no probe points on bus or igniter nets (DESIGN_ASSURANCE: never place TP on BUS/OUT)
    for n in POWER + ('RAW_ACT',):
        tps = sorted(p for p in members.get(n, ()) if p.startswith('TP') and n != 'RAW_ACT')
        req(not tps, f'test point on {n}: {tps}')
    # 3. pyro bus comes after the actuator load switch, never straight from the battery
    req('Q121.5' in members.get('RAW_ACT', set()) and 'Q120.5' in members.get('BAT_IN', set()),
        'RAW_ACT must be the Q121 drain; Q120 drain on BAT_IN')
    req(not (members.get('BAT_IN', set()) & {'J124.1', 'J124.2', 'J121.1', 'J121.2'}),
        'no pyro terminal pin on BAT_IN')
    # 4. gate networks: series R, pull-down on the MCU side, gate-source R and C, defined off in reset
    for ch, q, rs, rpd, rgs, cgs, mcu in ((1, 'Q124', 'R126', 'R127', 'R128', 'C126', 'U1.3'),):
        g, gn = f'PYRO{ch}_GATE', f'PYRO{ch}_GATE_N'
        req(pin.get(f'{q}.4') == g, f'{q} gate on {g}')
        req(pin.get(f'{q}.5') == f'PYRO{ch}_OUT', f'{q} drain on PYRO{ch}_OUT')
        req(all(pin.get(f'{q}.{k}') == 'GND' for k in '123'), f'{q} sources on GND')
        req({pin.get(f'{rs}.1'), pin.get(f'{rs}.2')} == {g, gn}, f'{rs} series between {gn} and {g}')
        req({pin.get(f'{rpd}.1'), pin.get(f'{rpd}.2')} == {gn, 'GND'}, f'{rpd} pull-down on {gn}')
        req({pin.get(f'{rgs}.1'), pin.get(f'{rgs}.2')} == {g, 'GND'}, f'{rgs} gate-source resistor')
        req({pin.get(f'{cgs}.1'), pin.get(f'{cgs}.2')} == {g, 'GND'}, f'{cgs} gate-source capacitor')
        req(members.get(gn) == {mcu, f'{rs}.1', f'{rpd}.1'}, f'{gn} must be only {mcu}, {rs}, {rpd}')
        # 4b. nothing else on the gate itself: FET, series R, gate-source R and C, the bottom-side test pad
        req(members.get(g) == {f'{q}.4', f'{rs}.2', f'{rgs}.1', f'{cgs}.1', f'TP{121 + ch}.1'},
            f'{g} must be only {q}.4, {rs}, {rgs}, {cgs}, TP{121 + ch}')
        req(val.get(q) == 'AON7524' and val.get(cgs, '').startswith('220nF'), f'{q}/{cgs} values')
        # 4c (validation pass 2, actuators F3): the gate network's values set the off-state hold, the turn-on
        # time and the Miller margin (M3_ACTUATOR_MERGE); a wrong value passed every rule above
        req(val.get(rs) == '220R' and val.get(rpd) == '1k' and val.get(rgs) == '10k', f'{rs}/{rpd}/{rgs} must be 220R / 1k / 10k')
        req(side.get(f'TP{121 + ch}') == 'B.Cu', f'TP{121 + ch} (bare gate pad) must stay on the bottom side')
    # 5. sentinel pins beside the pyro gates carry no net (firmware drives them low)
    for p in ('U1.2', 'U1.4', 'U1.5', 'U1.16', 'U1.32'):
        req(pin.get(p) is None or pin.get(p, '').startswith('unconnected-'), f'{p} must stay a no-net sentinel')
    # 6. CH1 drain contains only its terminal, FET, divider, cold pull-up and drain capacitor
    req(members.get('PYRO1_OUT') == {'J121.1', 'Q124.5', 'R173.1', 'R131.1', 'C128.1'}, 'PYRO1_OUT membership')
    # 6b (pass 2, actuators F3/F4): the sense dividers' lower leg is on GND, so every ADC pin reads at most 1.78 V at
    # the 19.9 V TVS clamp; each node is only its divider, filter cap and series resistor. Pass 9 (actuators F1): a 4.7k
    # series resistor between each node and its MCU pin (the *_MCU net). Pass 11: each top is two 5.1k in series
    # (a = source side, b = node side) through the *_MID net; pass 12: each bottom is two 2k in parallel. No single shorted
    # or open part lifts the node above 1.4 V (3.3 V at the clamp); ratio 1/11.2
    for ch, mcu_cont, mcu_arm in ((1, 'U1.15', 'U1.33'),):
        for node, ta, tb, bot, bot2, cap, ser, mcu, src in (
                (f'PYRO{ch}_CONT', 'R173', 'R129', 'R130',
                 'R178', 'C127', 'R168', mcu_cont, f'PYRO{ch}_OUT'),
                (f'ARM{ch}_SENSE', 'R132', 'R175', 'R133',
                 'R180', 'C129', 'R170', mcu_arm, f'PYRO{ch}_BUS')):
            req(members.get(node) == {f'{tb}.2', f'{bot}.1', f'{bot2}.1', f'{cap}.1', f'{ser}.1'},
                f'{node} must be only {tb}, {bot}, {bot2}, {cap} and {ser}')
            req(members.get(f'{node}_MID') == {f'{ta}.2', f'{tb}.1'} and pin.get(f'{ta}.1') == src,
                f'{node}_MID must be only {ta}.2 and {tb}.1, with {ta}.1 on {src} (split top, pass 11)')
            req(val.get(ta) == '5.1k' and val.get(tb) == '5.1k', f'{ta} and {tb} must be 5.1k')
            req(members.get(f'{node}_MCU') == {f'{ser}.2', mcu} and val.get(ser) == '4.7k',
                f'{ser} (4.7k) must be the only part between {node} and {mcu} ({node}_MCU)')
            for bt in (bot, bot2):
                req({pin.get(f'{bt}.1'), pin.get(f'{bt}.2')} == {node, 'GND'} and val.get(bt) == '2k', f'{bt} must be 2k from {node} to GND')
        # cold pull-up: R131 from the drain to the COLD node, which only D120 feeds
        cold, rc = f'PYRO{ch}_COLD', 'R131'
        req(members.get(cold) == {f'{rc}.2', f'D120.{ch}'}, f'{cold} must be only {rc}.2 and D120.{ch}')
        # Soft terminations reduce flex-crack risk; they do not guarantee fail-open behavior.
        # A drain-capacitor short bypasses the FET (docs/R5_VALIDATION.md, R5-V06).
        cd = 'C128'
        req(part.get(cd) == 'C161115' and volts(val.get(cd)) >= 25, f'{cd} must be the >= 25 V soft-termination C161115')
        # 6c (pass 5): every capacitor of the channel returns to GND (a drain capacitor on 3V3 or RAW_ACT passed)
        for c in (cd, 'C127', 'C129'):
            req(pin.get(f'{c}.2') == 'GND', f'{c}.2 must be GND')
    req(members.get('RAW_ACT_SENSE') == {'R124.2', 'R125.1', 'R182.1', 'C122.1', 'R172.1'} and val.get('R125') == '2k'
        and val.get('R182') == '2k' and pin.get('R125.2') == 'GND' and pin.get('R182.2') == 'GND',
        'RAW_ACT_SENSE must be R124 over R125 + R182 (2 x 2k) to GND, with C122 and R172')
    req(members.get('RAW_ACT_SENSE_MID') == {'R177.2', 'R124.1'} and pin.get('R177.1') == 'RAW_ACT'
        and val.get('R177') == '5.1k' and val.get('R124') == '5.1k', 'RAW_ACT_SENSE top must be R177 + R124, 2 x 5.1k (pass 11)')
    # pass 10: PB0 behind its own 4.7k too (a shorted R124 put stiff RAW_ACT on it, also armed under FMEA H-6(b))
    req(members.get('RAW_ACT_SENSE_MCU') == {'R172.2', 'U1.34'} and val.get('R172') == '4.7k',
        'R172 (4.7k) must be the only part between RAW_ACT_SENSE and U1.34 (RAW_ACT_SENSE_MCU)')
    # 7. servo chain order: MCU -> pull-down + clamp -> 1k series -> header
    for i, pa in enumerate(('22', '23', '24', '25'), start=1):
        m, o = f'SERVO{i}_MCU', f'SERVO{i}_OUT'
        req(f'U1.{pa}' in members.get(m, set()), f'{m} on U1.{pa}')
        req(members.get(o) == {f'J122.{1 + 3 * (i - 1)}', f'R{149 + i}.2'}, f'{o} only header + series R')
        req(pin.get(f'R{149 + i}.1') == m, f'R{149 + i}.1 must be on {m} (pass 9)')
        req(val.get(f'R{149 + i}') == '1k 0805', f'R{149 + i} must be 1k 0805')
        # 7b. each servo line has its own 10k pull-down to GND, so it is a defined low in reset (F6)
        req({pin.get(f'R{153 + i}.1'), pin.get(f'R{153 + i}.2')} == {m, 'GND'} and val.get(f'R{153 + i}') == '10k',
            f'R{153 + i} must be a 10k pull-down from {m} to GND')
    req(all(pin.get(f'J122.{k}') == 'RAW_ACT' for k in (2, 5, 8, 11)), 'servo + row on RAW_ACT')
    req(all(pin.get(f'J122.{k}') == 'GND' for k in (3, 6, 9, 12)), 'servo - row on GND')
    # 7c (pass 2): the SRV05-4 clamp's rails, so a servo-lead transient goes to 3V3/GND, not into a power rail
    req(pin.get('D121.2') == 'GND' and pin.get('D121.5') == '3V3', 'D121 SRV05-4: pin 2 GND, pin 5 3V3')
    req([pin.get(f'D121.{k}') for k in (1, 3, 4, 6)] == ['SERVO1_MCU', 'SERVO2_MCU', 'SERVO3_MCU', 'SERVO4_MCU'],
        'D121 SRV05-4 I/O pins 1/3/4/6 on SERVO1-4_MCU (pass 5)')
    # 8. actuator switch is gated by the logic path (single external switch)
    req({pin.get('R122.1'), pin.get('R122.2')} == {'RAW_PROTECTED', 'ACT_EN'}, 'ACT_EN divider from RAW_PROTECTED')
    req(pin.get('Q122.1') == 'ACT_EN' and pin.get('Q122.3') == 'ACT_DRV', 'Q122 drives the load-switch gate')
    # 8a (pass 9, actuators F3): every load-switch net exactly, Q122's source and the enable divider's foot on GND
    for n, want in ACT_NETS.items():
        req(members.get(n) == want, f'{n} must be exactly {sorted(want)} (is {sorted(members.get(n, ()))})')
    req(pin.get('Q122.2') == 'GND' and pin.get('R123.2') == 'GND', 'Q122 source and R123 foot on GND')
    # 8b (pass 2): C120 sits gate-to-source on Q120/Q121, so a shorted C120 turns the switch off (never on)
    req({pin.get('C120.1'), pin.get('C120.2')} == {'ACT_GATE', 'ACT_FET_S'}, 'C120 must be between ACT_GATE and ACT_FET_S')
    # 9. MLT-5020 coil polarity and isolated third solder tab (Huaneng 2021-05-27)
    req(pin.get('LS120.1') == '3V3' and pin.get('LS120.2') == 'BUZZ_OUT', 'LS120 + to 3V3, - to BUZZ_OUT')
    req(val.get('LS120') == 'MLT-5020' and part.get('LS120') == 'C94598', 'LS120 must use compact MLT-5020 C94598')
    req((pin.get('LS120.3') is None or pin.get('LS120.3', '').startswith('unconnected-')) and 'LS120.4' not in pin, 'LS120 has one isolated mechanical tab and no fourth pad')
    req(pin.get('D122.3') == 'PULLPIN' and pin.get('D122.2') == '3V3' and pin.get('D122.1') == 'GND', 'BAT54S clamp')
    # 10. FMEA H-1 cold pull-up: BAT54A common anode on 3V3, one cathode per channel
    req(pin.get('D120.3') == '3V3' and pin.get('D120.1') == 'PYRO1_COLD' and (pin.get('D120.2') is None or pin.get('D120.2', '').startswith('unconnected-')),
        'D120 BAT54A: anode 3V3, cathode 1 PYRO1_COLD, cathode 2 NC')
    # 11. Pyro terminals share a stocked black 2P body; PCB silk must distinguish ARM and IGN.
    arm_t, ign_t, other_t = ('J124',), ('J121',), ('J1', 'J9')
    req(all(part.get(j) == 'C430601' for j in arm_t), 'ARM terminal J124 must be black C430601')
    req(all(part.get(j) == 'C430601' for j in ign_t), 'igniter terminal J121 must be black C430601 with explicit IGN silk')
    groups = [{part.get(j) for j in g} for g in (arm_t, ign_t, other_t)]
    req(not (groups[0] & groups[2] or groups[1] & groups[2]),
        'pyro terminal part must remain distinct from battery/camera connectors')
    req(re.search(r'\(gr_text "ARM(?:1| CH1)?"', text) is not None
        and re.search(r'\(gr_text "IGN(?:1| CH1)?"', text) is not None,
        'shared black pyro terminals require explicit ARM and IGN silkscreen')
    # 12. external power contact: a 470k on each side, so no wire fault puts the pack on U9 EN (F8/F9)
    req(members.get('BAT_SW_SOURCE') == {'J1.3', 'R80.2'} and pin.get('R80.1') == 'BAT_IN', 'J1.3 only through R80 to BAT_IN')
    req(members.get('BAT_SW_RETURN') == {'J1.4', 'R165.1'} and pin.get('R165.2') == 'BAT_ENABLE', 'J1.4 only through R165 to EN')
    # 13. input TVS: bidirectional, VBR >= 13.3 V, so a wrong 3S pack (12.6 V) cannot drive it (F9)
    req(val.get('D8') in ('SMBJ12CA', 'SMBJ13CA') and {pin.get('D8.1'), pin.get('D8.2')} == {'BAT_IN', 'GND'},
        'D8 must be an SMBJ12CA/13CA across BAT_IN-GND')
    # 14 (pass 2/3, power P-1/F-1): nothing polarized ahead of U9; 2 x 10 uF at the input and the RC damper in place
    req(members.get('BAT_DAMP') == {'C89.2', 'C95.2', 'R166.1'} and pin.get('C89.1') == pin.get('C95.1') == 'BAT_IN'
        and pin.get('R166.2') == 'GND', 'input damper: C89 + C95 from BAT_IN to BAT_DAMP, R166 from BAT_DAMP to GND')
    req({pin.get('C80.1'), pin.get('C80.2')} == {pin.get('C96.1'), pin.get('C96.2')} == {'BAT_IN', 'GND'},
        'C80 and C96 (input capacitors) from BAT_IN to GND')
    # 14b (pass 4, power F-1/F-7): the 10k bleed empties the input after an unplug, so a reversed pack never starts
    # the harness ring from a charged input; R166 sits on UNI-ROYAL's own 2512 land
    req({pin.get('R167.1'), pin.get('R167.2')} == {'BAT_IN', 'GND'} and (val.get('R167') or '').startswith('10k'),
        'R167 (10k input bleed) from BAT_IN to GND')
    req(fpname.get('R166') == 'rocket:M3_R2512_UR', f"R166 must use UNI-ROYAL's land rocket:M3_R2512_UR (is {fpname.get('R166')})")
    # 15 (pass 2/3, actuators F2/F6/F3): the spacing rules live in m3.kicad_dru, where tools/check.sh's DRC enforces
    # them; each rule must keep its minimum and name every net it protects
    if dru is not None:
        sha = hashlib.sha256(dru.encode()).hexdigest()[:16]
        req(sha == DRU_SHA, f'm3.kicad_dru changed (sha {sha}): review the whole file, then update DRU_SHA')
        for name, (dmin, nets) in PYRO_RULES.items():
            blk = rule_block(dru, name)
            if blk is None:
                req(False, f'm3.kicad_dru must keep the rule "{name}"')
                continue
            m = re.search(r'\(min ([\d.]+)mm\)', blk)
            req(m is not None and float(m.group(1)) >= dmin, f'rule "{name}" must keep min >= {dmin} mm')
            missing = [n for n in nets if f"'{n}'" not in blk]
            req(not missing, f'rule "{name}" lost nets {missing}')
            # pass 5: a severity override or a layer clause silently narrows or mutes the rule
            req('(severity' not in blk and '(layer' not in blk, f'rule "{name}" must not carry a severity or layer clause')
            sha = hashlib.sha256(blk.encode()).hexdigest()[:16]
            req(sha == PYRO_RULE_SHA.get(name), f'rule "{name}" text changed (sha {sha}): review it, then update PYRO_RULE_SHA')
    # 15b (pass 5): rule G only works inside the PYRO_BLOCK rule area, so the area must exist on all four copper
    # layers, cover the block, and restrict nothing (renaming or deleting it made rule G check nothing). R5: the
    # block turned 180 deg and moved 24 mm forward; the area covers it whole. R7 moved the whole board 18 mm forward
    # (the RF strip at the aft end): x 4-42, y 84-114.4 (R5/R6: y 66-96.4; R4: x 12-42, y 42-72.4)
    areas = [z for z in read(text).children('zone') if z.children('name') and z.children('name')[0].items[1].atom == 'PYRO_BLOCK']
    ok = False
    for z in areas:
        layers = {a.atom for n in z.children('layers') for a in n.items[1:]}
        pts = [(float(xy.items[1].atom), float(xy.items[2].atom)) for pl in z.children('polygon') for pp in pl.children('pts')
               for xy in pp.children('xy')]
        keep = [a.atom for k in z.children('keepout') for n in k.items[1:] if hasattr(n, 'children') for a in n.items[1:2]]
        # pass 6: exactly the rectangle (a notch in a polygon with the same bounding box passed)
        rect = sorted(pts) == sorted([(4.0, 84.0), (42.0, 84.0), (42.0, 114.4), (4.0, 114.4)])
        if {'F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'} <= layers and rect and len(z.children('polygon')) == 1 and keep \
                and all(a == 'allowed' for a in keep):
            ok = True
    req(len(areas) == 1 and ok, 'one PYRO_BLOCK rule area on F.Cu/In1/In2/B.Cu covering x 4-42, y 84-114.4, restricting nothing')
    # IMU status on polled PE1; PE10 and PE0 stay no-connect (R6, kept)
    req(members.get('IMU_INT1') == {'U1.98', 'U4.4'}
        and pin.get('U1.40', '').startswith('unconnected-'),
        'IMU status must use polled PE1; PE10 must remain NC')
    req(pin.get('U1.97', '').startswith('unconnected-'), 'PE0 must remain NC')
    req(val.get('R84') == '750R 0.1%' and pin.get('R84.1') == 'BAT_ILIM' and pin.get('R84.2') == 'GND',
        'U9 R84 must be 750R 0.1%; revised copper and fault qualification are mandatory')
    req(tuple(pin.get(f'J9.{i}') for i in range(1, 5)) == ('CAM_5V', 'GND', 'CAM_RX_WIRE', 'CAM_TX_WIRE'),
        'J9 must retain all four camera nets')
    req(tuple(pin.get(f'J2.{i}') for i in range(1, 6)) == ('3V3', 'SWDIO', 'NRST', 'SWCLK', 'GND'),
        'J2 must match Tag-Connect ARM20-CTX SWD mapping')
    req(pin.get('J2.6') is None or pin.get('J2.6', '').startswith('unconnected-'), 'J2.6 SWO is NC; no BOOT0 harness')
    # 16 (pass 3, actuators F3 / system m7): pinned parts (protection values, pyro parts, terminals)
    for ref, code in PINNED.items():
        req(part.get(ref) == code, f'{ref} must be LCSC {code} (is {part.get(ref)})')
    return issues


def main():
    board = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'assembly_review' / 'm3.kicad_pcb'
    dru = board.with_suffix('.kicad_dru')
    issues = check(board.read_text(), dru.read_text() if dru.exists() else '')
    for i in issues: print('FAIL', i)
    print('actuator safety contract:', 'OK' if not issues else f'{len(issues)} issue(s)')
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
