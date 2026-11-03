#!/usr/bin/env python3
"""R8 firmware board-binding note (AGENTS.md section 3): the facts a future m3_firmware binding for R8 must carry.

usage: <KiCad python3> binding_note.py BOARD.kicad_pcb OUT.json

This is a record, not a binding: m3_firmware/assembly_binding.py and build.py are bound to the archived R1 board and
their build chain cannot run in this repository (AGENTS section 1). It writes, for the board given:
  - the board, netlist and pin-table SHA-256 a binding must be generated against;
  - U1's full pin map read from the board's pads, checked equal to pin_table.tsv's r8_net column (it fails otherwise);
  - every U1 pin whose net differs from R7 (pin_table 'change'), with its mode / AF and EXTI line;
  - the binding constraints of R8_DECISIONS D6 and D27, the radio start order (pass1_electrical section 5.4, M3_R7),
    the IMU axis map and lever arm (U4 measured on the board: face, rotation, pad-1 offset, position).
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PIN_TABLE = HERE.parent / 'pin_table.tsv'
NETLIST = ROOT / 'm3_design/assembly_review/schematic.net.xml'
mm = pcbnew.ToMM

CONSTRAINTS = [
    'SPI2 (radio): set SPI_CFG2.IOSWP = 1 while SPE = 0, before PB14 / PB15 take AF5, and never assert NSS before that; '
    'NSS (PB11) is a software GPIO with R310 (100 k) to 3V3 (D2, D4, D6.1; RM0433 Rev 9 section 50.11.4).',
    'Radio start order: NSS high, RXEN (PD9) low, then release NRST (PE9 high) and wait for BUSY (PD8) low; call '
    'SetDio2AsRfSwitchCtrl, keep RXEN low while transmitting, RampTime >= 200 us, <= +14 dBm on USB power '
    '(pass1_electrical section 5.4; M3_R7 pin contract; D6.2).',
    'BUSY (PD8) is polled: EXTI line 8 belongs to VBUS_SENSE (PC8) (D6; RM0433 section 12.3).',
    'EXTI: 4 BAT_FAULT_N (PA4), 5 LOGIC_SOURCE_ST (PA5), 6 USB_FAULT_N (PD6), 8 VBUS_SENSE (PC8), 11 CAM_FAULT_N (PE11), '
    '14 PULLPIN (PC14), 15 RADIO_DIO1 (PE15); the EXTI9_5 and EXTI15_10 handlers check each pending bit (D6).',
    'GNSS TIMEPULSE (PD15) is read by TIM4_CH4 input capture (AF2), never EXTI15 (DIO1\'s line); GNSS RESET_N is PD14, '
    'open drain (D2, D6).',
    'Camera UART is UART7: TX PE8, RX PE7 (AF7), no flow control; never AF7 on PE9 (UART7_RTS/DE) or PE10 (CTS); PE10 '
    'stays NC; keep CAM_UART_OE (PA7) low until the camera is powered and UART7 is set up (D2, D6.3, D6.7).',
    'Lock PE4 (GPIOE_LCKR) before any other GPIOE set-up; SPI4 is never enabled; PE11 / PE12 are GPIO only (D6.4).',
    'BUZZ_DRV is PC13: drive the buzzer (MLT-5020, 4.0 +- 0.2 kHz, Huaneng datasheet item 5) by GPIO toggling (a timer '
    'interrupt, or timer-triggered DMA to BSRR), never a DC level on the coil, never RTC_OUT / ALARM / CALIB / TAMP / TS on '
    'PC13; the pin is limited to 2 MHz (D27; DS12110 Rev 11 Table 53 note 2).',
    'PA4 / PA5 / PA7 are GPIO with internal pulls off (external pulls exist) and are not ADC inputs (D6.6).',
    'Pins the ROM bootloader drives carry only the D5 allow-list (PA2 SERVO3_MCU, PB10 RADIO_SCK_MCU, PB14 RADIO_MOSI_MCU, '
    'PA11 / PA12 USB, PB6 QSPI_NCS, PB9 I2C1_SDA) and LEDs; PA6, PA8, PA9, PA10, PC9, PC11 and PE13 are NC (D5).',
    'Unchanged from R7: the pyro gate and sense pins, the servo pins and the sentinels (check_actuators); fire pulses end '
    'at 20 ms; neutral is the first servo output after any reset (REQUIREMENTS F6, F7).',
    'Before any jump to the ROM bootloader (the only way in: BOOT0 is tied low by R5 and is not on J2, so AN2606 Table 2 '
    'pattern 10 needs BOOT0 = 1 and cannot be selected), in this order: (1) drive PE4 (PYRO1_GATE_N) low (GPIOE_LCKR '
    'freezes PE4\'s configuration registers, not its output data, RM0433 section 11.4.8); (2) put the SX1262 to sleep '
    '(the radio is still out of reset, so BUSY can go low) and drive RADIO_NRST (PE9) low; (3) last, reset GPIOE through '
    'RCC_AHB4RSTR, which clears the lock and returns PE4 and PE9 to analog, so R127 holds the gate off and R311 holds NRST '
    'low in the bootloader (without that reset, keep PE4 driven low and return PE9 to analog mode). Never reset GPIOE '
    'before step 2: it returns PE9 to analog, R311 asserts NRST, the SX1262 holds BUSY high in reset, and a driver that '
    'waits for BUSY low before SetSleep hangs, so the jump is never made (fail-safe, but the order matters; fix pass 3, '
    'R8P3-RF-01). AN2606 Rev 70 Table 135 configures only the bootloader\'s own interface pins, so PE4 and PE9 would '
    'otherwise keep their last application state: a jump made with PE4 high would hold an armed gate on for as long as '
    'the bootloader runs, outside the application\'s 20 ms fire limit (Inference). NSS stays high through R310, so the '
    'loader-capture safety of D2 / D5 holds either way; the "radio cannot transmit in the bootloader" property of F10 and '
    'the gate held off there rest on this step (D6.8; fix pass 1, R8P1-REQUIREMENTS-02; fix pass 2, R8P2-PYRO-03; bench: '
    'ORDERING section 5, the bootloader repeat of the radio-reset step).',
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(board_path, out):
    b = pcbnew.LoadBoard(board_path)
    rows = list(csv.DictReader(open(PIN_TABLE, encoding='utf-8'), delimiter='\t'))
    u1 = next(f for f in b.GetFootprints() if f.GetReference() == 'U1')
    pads = {p.GetNumber(): p.GetNetname() for p in u1.Pads()}
    mism = []
    for r in rows:
        net = pads.get(r['pin'], '')
        want = r['r8_net']
        if want in ('NC', '-', ''):
            if net and not net.startswith('unconnected-'):
                mism.append((r['pin'], want, net))
        elif net != want:
            mism.append((r['pin'], want, net))
    if mism:
        raise SystemExit(f'U1 pads differ from pin_table.tsv: {mism}')
    u4 = next(f for f in b.GetFootprints() if f.GetReference() == 'U4')
    p1 = next(p for p in u4.Pads() if p.GetNumber() == '1')
    c = (mm(u4.GetPosition().x), mm(u4.GetPosition().y))
    note = dict(
        profile='M3-ASSY-R8', status='record only: no binding generated (the R1 binding chain cannot run here)',
        board_sha256=sha(board_path), netlist_sha256=sha(NETLIST), pin_table_sha256=sha(PIN_TABLE),
        u1_pins={r['pin']: dict(port=r['port'], net=r['r8_net'], mode=r['r8_mode_af']) for r in rows},
        changed_from_r7={r['pin']: dict(port=r['port'], r7=r['r7_net'], r8=r['r8_net'], mode=r['r8_mode_af'],
                                        exti=r['exti_r8']) for r in rows if r['change'] != 'unchanged'},
        constraints=CONSTRAINTS,
        imu=dict(part='U4 LSM6DSV320X', face='B' if u4.IsFlipped() else 'F', rotation=u4.GetOrientationDegrees(),
                 at_mm=[round(c[0], 3), round(c[1], 3)],
                 pad1_offset_mm=[round(mm(p1.GetPosition().x) - c[0], 3), round(mm(p1.GetPosition().y) - c[1], 3)],
                 axes='+X_imu = +x_board, +Y_imu = +y_board (forward), +Z_imu out of the bottom face (M3_R5 section 3; '
                      'unchanged: bottom face, rotation 0, pad 1 at (-1.21, +0.75) mm as in R5 and R7)',
                 roll='+gyro_Y (right-handed about +y_board as M3_R5 section 3); thrust reads +a_Y',
                 lever_arm_mm=dict(x=round(c[0] - 23.0, 2), z='about -2.06 (model-box centre, bottom face)',
                                   note='R7 +13.0 / -2.06: the centripetal term on a_X changes sign '
                                        '(R8: +omega^2 x 13.0 mm toward +x_board, 1.38 g at 1850 deg/s)')),
    )
    json.dump(note, open(out, 'w'), indent=1)
    print(f'binding note for {note["board_sha256"][:12]}: {len(note["changed_from_r7"])} changed pins, U1 map = pin table')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
