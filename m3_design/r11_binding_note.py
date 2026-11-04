#!/usr/bin/env python3
"""Write the R11 binding note, m3_design/r11/design/r11_binding_note.json (stage D, D-R11-76): a record of the D-R11-49
pin map, U4's axis map and the firmware obligations, in the form of R10's r10_binding_note.json. Record only: it is
not an executable firmware binding, approves nothing, and m3_firmware is not touched.

usage: <KiCad python3> -I -B m3_design/r11_binding_note.py BOARD [--stage-d stageD_budget.json] [--out JSON] [--check]
BOARD is the R11 board (filled or not: only U1's and U4's pads are read). --check compares the saved note with a fresh
generation and exits 1 on any difference.

Sources: pin_table.tsv (columns r11_ball, r11_net and the 'R11 mode:' text of r11_ball_source, generated from
r11_sch.R11_REPIN), R10's binding note (sources, port states, arming policy, fire timing and the 49 firmware
obligations, carried verbatim and marked as R10 text), and the R11 deltas listed here (R11_DELTAS), each naming the R10
obligation it changes.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESIGN = HERE / 'r11/design'
R10_NOTE = HERE / 'assembly_review/sources/r10_design/r10_binding_note.json'
OUT = DESIGN / 'r11_binding_note.json'

# (R10 obligation index, what changes on R11). Pin facts from pin_table.tsv / D-R11-41 / D-R11-49; EXTI line = pin
# number (SYSCFG_EXTICRx selects one port per line: the field layout is checked against ST's CMSIS header stm32h743xx.h,
# cmsis-device-h7 commit 8f922cdc; RM0433 itself not read: Inference). Every interrupt net has its own line number.
R11_DELTAS = (
    (3, 'Camera UART is USART2 AF7: CAM_MCU_TX PD5 (ball B6), CAM_MCU_RX PD6 (ball C6), no flow control (D-R11-85; was '
        'UART4 PB9 / PB8, D-R11-49, and UART7 PE8 / PE7 on R10). PD5 / PD6 are not ROM-loader pins.'),
    (4, 'PE11 / PE12 (loader SPI4) are NC on R11. Camera EN is PC14 (CAM_PWR_EN, ball A1), held low by R431 100 k while '
        'PC14 is an input; camera OE is PC15 (ball B1), held low by R102 10 k. New loader members: PA15 (SPI3_NSS) '
        'carries SERVO2_MCU (R155 holds it low), PB9 (I2C1_SDA) carries IMU_CS (R11 holds it high) and PA2 (USART2_TX) '
        'carries SERVO4_MCU (stageC1b.md sections 8.4 and 9).'),
    (5, 'EXTI map on R11: CAM_FAULT_N PC13 (EXTI13, EXTI15_10), USB_FAULT_N PD10 (EXTI10, EXTI15_10), LOGIC_SOURCE_ST PA4 '
        '(EXTI4), BAT_FAULT_N PA5 (EXTI5), IMU_INT1 PD3 (EXTI3, ball C7; D-R11-85), VBUS_SENSE PC8 (EXTI8). Every '
        'interrupt net has its own line number (3, 4, 5, 8, 10, 13), so each SYSCFG_EXTICR field selects one port '
        '(PD for 3 / 10, PA for 4 / 5, PC for 8 / 13; the EXTICR field layout checked against ST\'s CMSIS header '
        'stm32h743xx.h, cmsis-device-h7 commit 8f922cdc; RM0433 not read: Inference); EXTI3 has its own vector, 5 / 8 '
        'share EXTI9_5 and 10 / 13 EXTI15_10, so each shared handler checks its pending bit. IMU_INT1 was PE1 / EXTI1 on '
        'R10, PD5 (D-R11-49, line 5 shared with PA5) and PD6 (D-R11-81). PC13 is used on R11 (it was NC); PD5 / PD6 '
        'carry the camera UART.'),
    (6, 'PE3 is NC again on R11 (ball B3, PE4\'s neighbour, D-R11-85), so it is again an analog sentinel with PE5 / PE6 / '
        'PC4; never drive it. PA15 carries SERVO2_MCU (TIM2_CH1 AF1): it resets as JTDI with its internal pull-up, which '
        'against R155 10 k gives at most 0.83 V on the line until firmware selects TIM2 (stageC1b.md section 8.4, '
        'Calculation with a 30 k minimum pull-up, Inference); configure PA15 early, as R10 required for the no-net PA15.'),
    (8, 'Servo timers on R11: SERVO1 PB7 TIM4_CH2 AF2 (ball A5), SERVO2 PA15 TIM2_CH1 AF1 (A8), SERVO3 PA1 TIM5_CH2 AF2 '
        '(H2), SERVO4 PA2 TIM5_CH3 AF2 (J2) (D-R11-85; PA0 / G2, PC1\'s neighbour, is NC): three timers, so the '
        'neutral-first-pulse and 50 ms rules apply to each timer start.'),
    (10, 'R11 connectors (D-R11-05): J122 / J400 / J410 / J420 / J440 / J9 are latching JST GH (J9 six-pin: 1-2 CAM_5V, '
         '3-4 GND, 5 RXI, 6 TXO); J1 (battery) and J121 (igniter) are hand-soldered AWG 20 wire pads. The DB125 text '
         'is R10 only.'),
    (16, 'The buzzer gate is driven by PE8 (BUZZ_DRV, ball J5) through R162, initialised low; PC14 now drives '
         'CAM_PWR_EN (U402 EN, R431 100 k; at most 0.04 mA, Calculation in pin_table.tsv), still a VBAT-domain pin at '
         '3 mA / 2 MHz.'),
    (19, 'Buzzer on PE8, not PC14. PC13 carries CAM_FAULT_N (input). PE0 and PE10 stay NC.'),
    (20, 'Camera start-up: RX PD6 pull-up and TX PD5 idle high before OE (PC15) goes high.'),
    (21, 'CAM_5V_SENSE is PC2_C (ball E2), ADC3_INP0, a TT_a pad (DS12110 Rev 8 Table 9 p. 67), not PB1 ADC12_INP5; ADC3 '
         'also carries the VBAT/4 bridge reading. PB1 carries LED_RED.'),
    (24, 'LEDs: LED_RED PB1 (ball K4), LED_YEL PD2 (ball B7).'),
    (27, 'LSE: PC14 (OSC32_IN) now drives CAM_PWR_EN; keep RCC_BDCR.LSEON = 0 as on R10.'),
    (29, 'CAM_5V_SENSE on PC2_C, a TT_a pad: absolute maximum 4.0 V (DS12110 Rev 8 Table 119 p. 211) and 0 mA injection '
         '(Table 156 p. 244). D-R11-86 makes the divider single-fault tolerant: R104 + R107 (5.1k + 5.1k) in series on '
         'top, R105 || R106 (2k || 2k) below, so one open or shorted resistor leaves the pin at most CAM_5V x 2k / 12.2k '
         '= 0.94 V at 5.6 V (Calculation); a shorted R105 / R106 / C94 or an open R104 / R107 reads 0 V. Firmware: the '
         'scale is CAM_5V = PC2_C x 11.2 (ratio 1k / 11.2k = 0.08929), not x 11; R10\'s camera thresholds stay in volts '
         'of CAM_5V and convert with the new ratio; a reading near 2x the expected value (one bottom resistor open) or '
         'near 0 V with the camera on (one top resistor open) is a sense fault, not a supply fault.'),
    (30, 'PE3 is NC on R11 (D-R11-85); IMU_CS is PB9 (ball A4). The trace prohibition stands (TRACED0 on PE3 would only '
         'drive an NC pin). The lock list is unchanged (PC1, PE4).'),
    (38, 'Rule 3 on R11: QSPI_IO2 is PE2 (ball A3) and PE4 is ball C3; B3 (PE3), B4, C4, D3, D4 are NC, C2 GND and B2 / '
         'D2 3V3 (D-R11-23), so no driven signal can bridge to PE4 (check_r11 K-neighbours, D-R11-85). A BGA bridge cannot '
         'be seen, so the visual "U1 pins 1-5" inspection becomes X-ray of U1, and the U3.3-to-R127.1 meter check stays. '
         'The cold-screen toggle list is the buzzer PE8 (not PC14) and the servo PWM.'),
    (39, 'The R10 second-barrel coordinates are R10 records; R11 gate barrels are in the R11 board and S-8 data.'),
    (40, 'The R91.1 / U1.28 second vias are R10 records. On R11 PA4 (LOGIC_SOURCE_ST, ball G3) has two single-via '
         'points, its dog-bone (21.60, 28.80) and its In3-to-B.Cu via (14.65, 39.90) (D-R11-45, D-R11-48, '
         'single_open_exceptions): an open leaves PA4 floating, so rule 5 (PC1 only while PA4 reads low) stays an '
         'extra barrier, not a guarantee.'),
    (42, 'EXTI5 is BAT_FAULT_N\'s alone on R11 (IMU_INT1 is on EXTI3, D-R11-85); rule 7 stands as R10.'),
    (46, 'U5 (MS5611) is on I2C2, PB10 SCL (ball J7) / PB11 SDA (ball K7), AF4 (D-R11-41; the nets keep the names '
         'I2C1_SCL / I2C1_SDA); PB10 / PB11 are loader USART3 pins (stageC1b.md section 7). IMU_CS is PB9 (ball A4). '
         'CAM_5V scale: PC2_C = CAM_5V / 11.2 (D-R11-86).'),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows():
    with (DESIGN / 'pin_table.tsv').open() as fh:
        return list(csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t'))


def mode_of(row):
    src = row['r11_ball_source']
    k = src.find('R11 mode: ')
    return src[k + len('R11 mode: '):].strip() if k >= 0 else row['mode_af']


def board_facts(board_path):
    import pcbnew
    mm = pcbnew.ToMM
    b = pcbnew.LoadBoard(str(board_path))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    u1 = {p.GetNumber(): p.GetNetname() for p in fps['U1'].Pads()}
    u4 = fps['U4']
    return u1, dict(x_mm=round(mm(u4.GetPosition().x), 4), y_mm=round(mm(u4.GetPosition().y), 4),
                    rotation_deg=u4.GetOrientationDegrees(), side='bottom' if u4.IsFlipped() else 'top',
                    part=u4.GetValue())


def generate(board_path, stage_d=None):
    r10 = json.loads(R10_NOTE.read_text())
    u1_pads, u4 = board_facts(board_path)
    pins, mismatch = {}, []
    for r in rows():
        ball = r['r11_ball']
        if ball in ('', '-'):
            continue
        net = r['r11_net']
        entry = dict(port=r['port'], net=net, mode=mode_of(r), r10_lqfp_pin=r['pin'])
        if r['r10_net'] != net:
            entry['r10_net'] = r['r10_net']
        pins[ball] = entry
        board_net = u1_pads.get(ball, '')
        if (net in ('NC', '-') and board_net and not board_net.startswith('unconnected')) or \
                (net not in ('NC', '-') and board_net != net):
            mismatch.append(f'{ball}: table {net}, board {board_net or "none"}')
    signals = {e['net']: dict(ball=ball, port=e['port'], mode=e['mode'])
               for ball, e in sorted(pins.items()) if re.fullmatch(r'P[A-K]\d+(_C)?', e['port']) and e['net'] not in ('NC', '-')}
    lever_x = round(u4['x_mm'] - 23.0, 4)
    note = {
        'profile': 'M3-ASSY-R11',
        'status': ('record only; not an executable binding; the R1 and R10 bindings are invalid for R11; no R11 firmware '
                   'or flight approval'),
        'board_sha256': sha(board_path),
        'board_note': 'the board file this note was generated from (U1 / U4 pads only; zone fill does not change them)',
        'netlist_sha256': sha(HERE / 'r11/schematic.net.xml'),
        'pin_table_sha256': sha(DESIGN / 'pin_table.tsv'),
        'circuit_sha256': sha(DESIGN / 'circuit.json'),
        'u1_package': 'STM32H743VIH6 TFBGA-100 (D-R11-04); keys are balls, r10_lqfp_pin is the R10 LQFP100 pin',
        'u1_balls': pins,
        'u1_signal_nets': signals,
        'u1_board_map_checked': not mismatch,
        'u1_board_map_mismatches': mismatch,
        'imu': {
            **u4, 'lever_arm_x_mm': lever_x, 'lever_arm_z_mm': -2.06,
            'lever_arm_z_basis': ('Inference: centre of the U4 3D model box on a 1.6 mm board, as R10 (same footprint, '
                                  'model and board thickness); not measured'),
            'lever_arm_frame': ('board frame: x east (+x toward the x = 46 edge), y forward, z up from the top face, the '
                                'roll axis at x 23 on the top face as R10 (Inference: same sled datum); in the IMU frame '
                                f'(+X_imu = -x, +Y_imu = -y, +Z_imu = -z) the lever arm is ({0.0 - lever_x + 0.0:+.1f}, ., +2.06) mm'),
            'bench_sign_check': 'required',
            'axis_basis': 'same signed frame as R9 / R10: bottom, rotation 180 (D-R11-11)',
            'roll_about_forward_axis': '-gyro_Y',
            'forward_thrust': '-a_Y',
            'centripetal_note': ('x lever arm 0: the roll centripetal term on a_X is nominally zero; the 2.06 mm z offset '
                                 'puts it on a_Z (Inference)')},
        'sources': r10['sources'],
        'port_states': r10['port_states'],
        'arming_policy': r10['arming_policy'],
        'fire_timing': r10['fire_timing'],
        'r10_firmware_obligations': r10['firmware_obligations'],
        'r10_firmware_obligations_note': ('R10 text, carried verbatim (R10 pin names, LQFP pin numbers and DB125 '
                                          'terminals); r11_obligation_deltas overrides each obligation it names'),
        'r11_obligation_deltas': [dict(r10_obligation=i, r11=text) for i, text in R11_DELTAS],
        'r11_firmware_rules': [
            'An R11 binding changes the TIM, UART, ADC and EXTI assignments together (stageC1b.md section 8.2); R10 '
            'firmware cannot run on R11.',
            'EXTI lines on R11 (D-R11-85): 3 PD3 IMU_INT1, 4 PA4 LOGIC_SOURCE_ST, 5 PA5 BAT_FAULT_N, 8 PC8 VBUS_SENSE, '
            '10 PD10 USB_FAULT_N, 13 PC13 CAM_FAULT_N; one port per line in SYSCFG_EXTICR (field layout from ST\'s CMSIS '
            'stm32h743xx.h, cmsis-device-h7 commit 8f922cdc; RM0433 not read: Inference).',
            'Gate-drive neighbours (D-R11-85): every ball round PE4 is NC, GND or the D-R11-23 3V3 pair; round PC1 they are '
            'NC, GND or NRST / PC0 / PC2_C / PA4, none of which can drive ACT_EN above about 0.5 V if bridged; never drive '
            'an NC ball next to PE4 or PC1 (PE3, PB8, PE1, PE5, PE0, PE6, PC3_C, PA0).'],
        'physical_tests': 'not performed',
    }
    if stage_d:
        d = json.loads(Path(stage_d).read_text())
        g = d['power_budget']['pyro_fault_GAP5']
        note['stage_d'] = dict(
            budget_board_sha256=d['board_sha256'], source_board_sha256=d.get('source_board_sha256'),
            four_stall_BAT_IN_V=d['four_stall']['BAT_IN_V'], four_stall_fire_A=d['four_stall']['fire_A'],
            physical_fault_bound_ms=g['physical_fault_bound_ms'], combined_tail_model_ms_inference=g['combined_tail_model_ms_inference'],
            basis='m3_design/r11_stageD.py; stageD_analysis.md (Calculation / Inference labels there)')
    return note


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board')
    ap.add_argument('--stage-d', default=None)
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(generate(Path(a.board), a.stage_d), indent=2) + '\n'
    if a.check:
        same = Path(a.out).is_file() and Path(a.out).read_text() == text
        print('r11_binding_note: ' + ('current' if same else 'STALE'))
        return 0 if same else 1
    Path(a.out).write_text(text)
    note = json.loads(text)
    print(f'wrote {a.out}: {len(note["u1_balls"])} balls, {len(note["u1_signal_nets"])} signal nets, '
          f'board map checked {note["u1_board_map_checked"]} {note["u1_board_map_mismatches"][:5]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
