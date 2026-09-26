#!/usr/bin/env python3
"""Safety contract for the R2 actuator merge, read from the saved PCB (pad nets), not the schematic.

usage: python3 m3_design/check_actuators.py [board.kicad_pcb]      exit 0 = every rule holds

These rules restate AGENTS.md §2 and docs/M3_ACTUATOR_MERGE.md in machine-checkable form. They
qualify the CAD netlist only: no electrical, thermal or physical behaviour is proven here.
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'quality_audit'))
from sexpr import read, properties  # noqa: E402


def pad_nets(text):
    pins, vals = {}, {}
    for fp in read(text).children('footprint'):
        ref = properties(fp)['Reference'].items[2].atom
        vals[ref] = properties(fp)['Value'].items[2].atom
        for p in fp.children('pad'):
            num = p.items[1].atom
            if num:
                n = p.children('net')
                pins[f'{ref}.{num}'] = n[0].items[-1].atom if n else None
    return pins, vals


def check(text):
    pin, val = pad_nets(text)
    members = {}
    for p, n in pin.items():
        if n: members.setdefault(n, set()).add(p)
    issues = []
    def req(ok, msg):
        if not ok: issues.append(msg)
    # 1. arming break: each bus touches only its terminal positions and its arm-sense upper arm
    req(members.get('PYRO1_BUS') == {'J120.3', 'J121.2', 'R132.1'}, 'PYRO1_BUS must be {J120.3, J121.2, R132.1}')
    req(members.get('PYRO2_BUS') == {'J120.2', 'J121.3', 'R144.1'}, 'PYRO2_BUS must be {J120.2, J121.3, R144.1}')
    req({'J120.1', 'J120.4'} <= members.get('RAW_ACT', set()), 'ARM terminal outer pins must be RAW_ACT')
    req(not ({'J120.2', 'J120.3'} & members.get('RAW_ACT', set())), 'no ARM bus pin may be RAW_ACT')
    # 2. no probe points on bus or igniter nets (DESIGN_ASSURANCE: never place TP on BUS/OUT)
    for n in ('PYRO1_BUS', 'PYRO2_BUS', 'PYRO1_OUT', 'PYRO2_OUT', 'RAW_ACT'):
        tps = sorted(p for p in members.get(n, ()) if p.startswith('TP') and n != 'RAW_ACT')
        req(not tps, f'test point on {n}: {tps}')
    # 3. pyro bus comes after the actuator load switch, never straight from the battery
    req('Q121.5' in members.get('RAW_ACT', set()) and 'Q120.5' in members.get('BAT_IN', set()),
        'RAW_ACT must be the Q121 drain; Q120 drain on BAT_IN')
    req(not (members.get('BAT_IN', set()) & {'J120.1', 'J120.4', 'J121.1', 'J121.2', 'J121.3', 'J121.4'}),
        'no pyro terminal pin on BAT_IN')
    # 4. gate networks: series R, pull-down on the MCU side, gate-source R and C, defined off in reset
    for ch, q, rs, rpd, rgs, cgs, mcu in ((1, 'Q124', 'R126', 'R127', 'R128', 'C126', 'U1.3'),
                                         (2, 'Q125', 'R138', 'R139', 'R140', 'C138', 'U1.4')):
        g, gn = f'PYRO{ch}_GATE', f'PYRO{ch}_GATE_N'
        req(pin.get(f'{q}.4') == g, f'{q} gate on {g}')
        req(pin.get(f'{q}.5') == f'PYRO{ch}_OUT', f'{q} drain on PYRO{ch}_OUT')
        req(all(pin.get(f'{q}.{k}') == 'GND' for k in '123'), f'{q} sources on GND')
        req({pin.get(f'{rs}.1'), pin.get(f'{rs}.2')} == {g, gn}, f'{rs} series between {gn} and {g}')
        req({pin.get(f'{rpd}.1'), pin.get(f'{rpd}.2')} == {gn, 'GND'}, f'{rpd} pull-down on {gn}')
        req({pin.get(f'{rgs}.1'), pin.get(f'{rgs}.2')} == {g, 'GND'}, f'{rgs} gate-source resistor')
        req({pin.get(f'{cgs}.1'), pin.get(f'{cgs}.2')} == {g, 'GND'}, f'{cgs} gate-source capacitor')
        req(members.get(gn) == {mcu, f'{rs}.1', f'{rpd}.1'}, f'{gn} must be only {mcu}, {rs}, {rpd}')
        req(val.get(q) == 'AON7524' and val.get(cgs, '').startswith('220nF'), f'{q}/{cgs} values')
    # 5. sentinel pins beside the pyro gates carry no net (firmware drives them low)
    for p in ('U1.2', 'U1.5'):
        req(pin.get(p) is None or pin.get(p, '').startswith('unconnected-'), f'{p} must stay a no-net sentinel')
    # 6. two independent channels: nothing but the terminals and dividers on the drains
    req(members.get('PYRO1_OUT') == {'J121.1', 'Q124.5', 'R129.1', 'R131.1', 'C128.1'}, 'PYRO1_OUT membership')
    req(members.get('PYRO2_OUT') == {'J121.4', 'Q125.5', 'R141.1', 'R143.1', 'C140.1'}, 'PYRO2_OUT membership')
    # 7. servo chain order: MCU -> pull-down + clamp -> 1k series -> header
    for i, pa in enumerate(('22', '23', '24', '25'), start=1):
        m, o = f'SERVO{i}_MCU', f'SERVO{i}_OUT'
        req(f'U1.{pa}' in members.get(m, set()), f'{m} on U1.{pa}')
        req(members.get(o) == {f'J122.{1 + 3 * (i - 1)}', f'R{149 + i}.2'}, f'{o} only header + series R')
        req(val.get(f'R{149 + i}') == '1k 0805', f'R{149 + i} must be 1k 0805')
    req(all(pin.get(f'J122.{k}') == 'RAW_ACT' for k in (2, 5, 8, 11)), 'servo + row on RAW_ACT')
    req(all(pin.get(f'J122.{k}') == 'GND' for k in (3, 6, 9, 12)), 'servo - row on GND')
    # 8. actuator switch is gated by the logic path (single external switch)
    req({pin.get('R122.1'), pin.get('R122.2')} == {'RAW_PROTECTED', 'ACT_EN'}, 'ACT_EN divider from RAW_PROTECTED')
    req(pin.get('Q122.1') == 'ACT_EN' and pin.get('Q122.3') == 'ACT_DRV', 'Q122 drives the load-switch gate')
    # 9. buzzer pad mapping (Huaneng spec 5.2) and pull-pin clamp
    req(pin.get('LS120.1') == '3V3' and pin.get('LS120.2') == 'BUZZ_OUT', 'LS120 + to 3V3, - to BUZZ_OUT')
    req(pin.get('D122.3') == 'PULLPIN' and pin.get('D122.2') == '3V3' and pin.get('D122.1') == 'GND', 'BAT54S clamp')
    return issues


def main():
    board = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'assembly_review' / 'm3.kicad_pcb'
    issues = check(board.read_text())
    for i in issues: print('FAIL', i)
    print('actuator safety contract:', 'OK' if not issues else f'{len(issues)} issue(s)')
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
