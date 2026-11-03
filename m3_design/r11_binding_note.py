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
# number (RM0433 SYSCFG_EXTICRx selects one port per line; RM0433 not re-read here: Inference).
R11_DELTAS = (
    (3, 'Camera UART is UART4 AF8: CAM_MCU_TX PB9 (ball A4), CAM_MCU_RX PB8 (ball B4), no flow control (D-R11-49), not '
        'UART7 PE8 / PE7. PB9 is a ROM-loader pin (I2C1_SDA, open drain): stageC1b.md section 8.4 case; drive PB9 '
        'push-pull only after the UART4 binding.'),
    (4, 'PE11 / PE12 (loader SPI4) are NC on R11. Camera EN is PC14 (CAM_PWR_EN, ball A1), held low by R431 100 k while '
        'PC14 is an input; camera OE is PC15 (ball B1), held low by R102 10 k. New loader members: PA15 (SPI3_NSS) '
        'carries SERVO2_MCU (R155 holds it low) and PB9 carries CAM_MCU_TX (stageC1b.md section 8.4).'),
    (5, 'EXTI map on R11: CAM_FAULT_N PC13 (EXTI13, EXTI15_10), USB_FAULT_N PD10 (EXTI10, EXTI15_10), LOGIC_SOURCE_ST PA4 '
        '(EXTI4), BAT_FAULT_N PA5 (EXTI5), VBUS_SENSE PC8 (EXTI8), IMU_INT1 PD5 (EXTI5). CONFLICT: PA5 and PD5 are both '
        'line 5, and SYSCFG_EXTICR2 routes one port to a line, so BAT_FAULT_N and IMU_INT1 cannot both interrupt '
        '(Inference: RM0433 not re-read). Open design item D-R11-77: one of them must be polled or re-mapped. PC13 is '
        'used on R11 (it was NC).'),
    (6, 'PE3 carries IMU_CS on R11 (ball B3), so it is no longer an analog sentinel; the sentinels are PE5 / PE6 / PC4. '
        'PA15 carries SERVO2_MCU (TIM2_CH1 AF1): it resets as JTDI with its internal pull-up, which against R155 '
        '10 k gives at most 0.83 V on the line until firmware selects TIM2 (stageC1b.md section 8.4, Calculation with '
        'a 30 k minimum pull-up, Inference); configure PA15 early, as R10 required for the no-net PA15.'),
    (8, 'Servo timers on R11: SERVO1 PB7 TIM4_CH2 AF2 (ball A5), SERVO2 PA15 TIM2_CH1 AF1 (A8), SERVO3 PA0 TIM5_CH1 AF2 '
        '(G2), SERVO4 PA1 TIM5_CH2 AF2 (H2): three timers, so the neutral-first-pulse and 50 ms rules apply to each '
        'timer start.'),
    (10, 'R11 connectors (D-R11-05): J122 / J400 / J410 / J420 / J440 / J9 are latching JST GH (J9 six-pin: 1-2 CAM_5V, '
         '3-4 GND, 5 RXI, 6 TXO); J1 (battery) and J121 (igniter) are hand-soldered AWG 20 wire pads. The DB125 text '
         'is R10 only.'),
    (16, 'The buzzer gate is driven by PE8 (BUZZ_DRV, ball J5) through R162, initialised low; PC14 now drives '
         'CAM_PWR_EN (U402 EN, R431 100 k; at most 0.04 mA, Calculation in pin_table.tsv), still a VBAT-domain pin at '
         '3 mA / 2 MHz.'),
    (19, 'Buzzer on PE8, not PC14. PC13 carries CAM_FAULT_N (input). PE0 and PE10 stay NC.'),
    (20, 'Camera start-up: RX PB8 pull-up and TX PB9 idle high before OE (PC15) goes high.'),
    (21, 'CAM_5V_SENSE is PC2_C (ball E2), ADC3_INP0 (the analog-only _C pad), not PB1 ADC12_INP5; ADC3 also carries the '
         'VBAT/4 bridge reading. PB1 carries LED_RED.'),
    (24, 'LEDs: LED_RED PB1 (ball K4), LED_YEL PD2 (ball B7).'),
    (27, 'LSE: PC14 (OSC32_IN) now drives CAM_PWR_EN; keep RCC_BDCR.LSEON = 0 as on R10.'),
    (29, 'CAM_5V_SENSE moved to PC2_C, an analog-only switch pad: the R10 TT_u 4.0 V single-fault limit for an open R105 '
         'does not carry over; the PC2_C limit is to be read from DS12110 (not re-read here: open item).'),
    (30, 'PE3 is IMU_CS: synchronous trace (TRACED0 on PE3) would also drive the IMU chip select; the trace prohibition '
         'stands. The lock list is unchanged (PC1, PE4).'),
    (38, 'Rule 3 on R11: QSPI_IO2 is PE2 (ball A3) and PE4 is ball C3, with PE3 / IMU_CS (B3) between them; a BGA '
         'bridge cannot be seen, so the visual "U1 pins 1-5" inspection becomes X-ray of U1, and the U3.3-to-R127.1 '
         'meter check stays. The cold-screen toggle list is the buzzer PE8 (not PC14) and the servo PWM.'),
    (39, 'The R10 second-barrel coordinates are R10 records; R11 gate barrels are in the R11 board and S-8 data.'),
    (40, 'The R91.1 / U1.28 second vias are R10 records. On R11 PA4 (LOGIC_SOURCE_ST, ball G3) has two single-via '
         'points, its dog-bone (21.60, 28.80) and its In3-to-B.Cu via (14.65, 39.90) (D-R11-45, D-R11-48, '
         'single_open_exceptions): an open leaves PA4 floating, so rule 5 (PC1 only while PA4 reads low) stays an '
         'extra barrier, not a guarantee.'),
    (42, 'EXTI5 is shared with IMU_INT1 on R11 (see the delta for obligation 5).'),
    (46, 'U5 (MS5611) is on I2C2, PB10 SCL (ball J7) / PB11 SDA (ball K7), AF4 (D-R11-41; the nets keep the names '
         'I2C1_SCL / I2C1_SDA); PB10 / PB11 are loader USART3 pins (stageC1b.md section 7). IMU_CS is PE3 (ball B3). '
         'CAM_5V scale: PC2_C = CAM_5V / 11.'),
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
            'EXTI line 5 is claimed by both BAT_FAULT_N (PA5) and IMU_INT1 (PD5): firmware must poll one of them until '
            'the open design item D-R11-77 is decided (Inference on RM0433 SYSCFG_EXTICR, not re-read).'],
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
