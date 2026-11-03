"""Write r8_design/pin_table.tsv: the R8 U1 pin contract, every pin, cited.

Sources (all read for R8 step 0):
  DS12110 Rev 11 (Jan 2026) https://www.st.com/resource/en/datasheet/stm32h743vi.pdf
  RM0433 Rev 9 (Oct 2026)   https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf
  AN2606 Rev 70 (Feb 2026)  https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf
R7 nets: m3_design/assembly_review/m3.kicad_pcb at 431025d (SHA-256 c872a3d3...), U1 pads.
"""
import json, sys

r7 = {int(k): v for k, v in json.load(open(sys.argv[1])).items()}
out = sys.argv[2]

PORT = {1: 'PE2', 2: 'PE3', 3: 'PE4', 4: 'PE5', 5: 'PE6', 6: 'VBAT', 7: 'PC13', 8: 'PC14', 9: 'PC15', 10: 'VSS',
        11: 'VDD', 12: 'PH0', 13: 'PH1', 14: 'NRST', 15: 'PC0', 16: 'PC1', 17: 'PC2_C', 18: 'PC3_C', 19: 'VSSA',
        20: 'VREF+', 21: 'VDDA', 22: 'PA0', 23: 'PA1', 24: 'PA2', 25: 'PA3', 26: 'VSS', 27: 'VDD', 28: 'PA4',
        29: 'PA5', 30: 'PA6', 31: 'PA7', 32: 'PC4', 33: 'PC5', 34: 'PB0', 35: 'PB1', 36: 'PB2', 37: 'PE7', 38: 'PE8',
        39: 'PE9', 40: 'PE10', 41: 'PE11', 42: 'PE12', 43: 'PE13', 44: 'PE14', 45: 'PE15', 46: 'PB10', 47: 'PB11',
        48: 'VCAP', 49: 'VSS', 50: 'VDD', 51: 'PB12', 52: 'PB13', 53: 'PB14', 54: 'PB15', 55: 'PD8', 56: 'PD9',
        57: 'PD10', 58: 'PD11', 59: 'PD12', 60: 'PD13', 61: 'PD14', 62: 'PD15', 63: 'PC6', 64: 'PC7', 65: 'PC8',
        66: 'PC9', 67: 'PA8', 68: 'PA9', 69: 'PA10', 70: 'PA11', 71: 'PA12', 72: 'PA13', 73: 'VCAP', 74: 'VSS',
        75: 'VDD', 76: 'PA14', 77: 'PA15', 78: 'PC10', 79: 'PC11', 80: 'PC12', 81: 'PD0', 82: 'PD1', 83: 'PD2',
        84: 'PD3', 85: 'PD4', 86: 'PD5', 87: 'PD6', 88: 'PD7', 89: 'PB3', 90: 'PB4', 91: 'PB5', 92: 'PB6', 93: 'PB7',
        94: 'BOOT0', 95: 'PB8', 96: 'PB9', 97: 'PE0', 98: 'PE1', 99: 'VSS', 100: 'VDD'}
# DS12110 Table 9 (pin/ball definition): I/O structure and page (read 1: text extraction; read 2: page images)
T9 = {1: ('FT_h', 64), 2: ('FT_h', 64), 3: ('FT_h', 64), 4: ('FT_h', 64), 5: ('FT_h', 64), 6: ('S', 64), 7: ('FT', 64),
      8: ('FT', 65), 9: ('FT', 65), 10: ('S', 66), 11: ('S', 66), 12: ('FT', 65), 13: ('FT', 65), 14: ('RST', 66),
      15: ('FT_a', 67), 16: ('FT_ha', 67), 17: ('ANA TT_a', 67), 18: ('ANA TT_a', 67), 19: ('S', 67), 20: ('S', 67),
      21: ('S', 67), 22: ('FT_a', 68), 23: ('FT_ha', 68), 24: ('FT_a', 68), 25: ('FT_ha', 69), 26: ('S', 69),
      27: ('S', 69), 28: ('TT_a', 69), 29: ('TT_ha', 69), 30: ('FT_a', 69), 31: ('TT_a', 70), 32: ('TT_a', 70),
      33: ('TT_a', 70), 34: ('FT_a', 70), 35: ('TT_a', 70), 36: ('FT_ha', 71), 37: ('TT_ha', 72), 38: ('TT_ha', 72),
      39: ('TT_ha', 72), 40: ('FT_ha', 72), 41: ('FT_ha', 72), 42: ('FT_h', 72), 43: ('FT_h', 72), 44: ('FT_h', 73),
      45: ('FT_h', 73), 46: ('FT_f', 73), 47: ('FT_f', 73), 48: ('S', 73), 49: ('S', 73), 50: ('S', 73),
      51: ('FT_u', 74), 52: ('FT_u', 75), 53: ('FT_u', 75), 54: ('FT_u', 75), 55: ('FT_h', 75), 56: ('FT_h', 75),
      57: ('FT_h', 76), 58: ('FT_h', 76), 59: ('FT_fh', 76), 60: ('FT_fh', 76), 61: ('FT_h', 76), 62: ('FT_h', 76),
      63: ('FT_h', 79), 64: ('FT_h', 79), 65: ('FT_h', 79), 66: ('FT_fh', 79), 67: ('FT_fha', 80), 68: ('FT_u', 80),
      69: ('FT_u', 80), 70: ('FT_u', 80), 71: ('FT_u', 80), 72: ('FT', 80), 73: ('S', 81), 74: ('S', 81),
      75: ('S', 81), 76: ('FT', 81), 77: ('FT', 82), 78: ('FT_ha', 82), 79: ('FT_h', 82), 80: ('FT_h', 82),
      81: ('FT_h', 82), 82: ('FT_h', 82), 83: ('FT_h', 83), 84: ('FT_h', 83), 85: ('FT_h', 83), 86: ('FT_h', 83),
      87: ('FT_h', 83), 88: ('FT_h', 83), 89: ('FT', 85), 90: ('FT', 85), 91: ('FT', 86), 92: ('FT_f', 86),
      93: ('FT_fa', 86), 94: ('B', 86), 95: ('FT_fh', 86), 96: ('FT_fh', 87), 97: ('FT_h', 87), 98: ('FT_h', 87),
      99: ('S', 87), 100: ('S', 87)}
# DS12110 Table 10 page by port
def T10P(p):
    if p[:2] not in ('PA', 'PB', 'PC', 'PD', 'PE'):
        return '-'
    k = int(p[2:].split('_')[0])
    return {'PA': '89' if k <= 11 else '90', 'PB': '90' if k <= 9 else '91', 'PC': '91' if k <= 5 else '92',
            'PD': '92' if k <= 4 else '93', 'PE': '94'}[p[:2]]
# AN2606 Rev 70 Table 135 (STM32H74xxx/75xxx, pp. 320-323): pins the ROM bootloader configures
LOADER = {
    'PA9': 'USART1_TX: output (AF push-pull, pull-up); input until USART1 detected on V9.1 (0x91) (p. 320)',
    'PA10': 'USART1_RX: input (AF, pull-up) (p. 320)',
    'PB14': 'USART1_TX (PB14/PB15 map): output, AF push-pull pull-up; no "input until detected" note (p. 320); V9.1 also echoes PA9 data on PB14 (Table 136, p. 326)',
    'PB15': 'USART1_RX (PB14/PB15 map): input pull-up (p. 320); V13.3/V9.1 limitation: PB15 at GND blocks every interface except USB (Table 136, pp. 325-326)',
    'PA2': 'USART2_TX: output; input until detected on V9.1 (p. 321)',
    'PA3': 'USART2_RX: input (p. 321)',
    'PB10': 'USART3_TX: output (AF push-pull, pull-up); input until USART3 detected on V9.1 (p. 321)',
    'PB11': 'USART3_RX: input (AF, pull-up) (p. 321)',
    'PB6': 'I2C1_SCL: open drain, no pull (p. 321)', 'PB9': 'I2C1_SDA: open drain, no pull (p. 321)',
    'PA8': 'I2C3_SCL: open drain, no pull (p. 321)', 'PC9': 'I2C3_SDA: open drain, no pull (p. 321)',
    'PA4': 'SPI1_NSS: slave input, no pull (p. 322)', 'PA5': 'SPI1_SCK: slave input, no pull (p. 322)',
    'PA6': 'SPI1_MISO: slave OUTPUT, push-pull (p. 322)', 'PA7': 'SPI1_MOSI: slave input, no pull (p. 322)',
    'PA15': 'SPI3_NSS: slave input (p. 322)', 'PC10': 'SPI3_SCK: slave input (p. 322)',
    'PC11': 'SPI3_MISO: slave OUTPUT, push-pull (p. 322)', 'PC12': 'SPI3_MOSI: slave input (p. 322)',
    'PE11': 'SPI4_NSS: slave input, no pull (p. 323)', 'PE12': 'SPI4_SCK: slave input, no pull (p. 323)',
    'PE13': 'SPI4_MISO: slave OUTPUT, push-pull (p. 323)', 'PE14': 'SPI4_MOSI: slave input, no pull (p. 323)',
    'PA11': 'USB DFU DM: AF push-pull (p. 323)', 'PA12': 'USB DFU DP: AF push-pull (p. 323)',
}
LOADER_DRIVEN = {'PA9', 'PB14', 'PA2', 'PB10', 'PB6', 'PB9', 'PA8', 'PC9', 'PA6', 'PC11', 'PE13', 'PA11', 'PA12'}
FROZEN = {  # docs/ROCKET_FC_FROZEN_DESIGN.md 3.10
    'PC8': 'reserved (SDMMC1); R7 already uses it', 'PC9': 'reserved (SDMMC1)', 'PC10': 'reserved (SDMMC1)',
    'PC11': 'reserved (SDMMC1)', 'PC12': 'reserved (SDMMC1)', 'PD2': 'reserved (SDMMC1)',
    'PA4': 'no signal that matters at reset', 'PA5': 'no signal that matters at reset',
    'PA6': 'no signal that matters at reset', 'PA7': 'no signal that matters at reset',
    'PE11': 'avoid (loader SPI4): R8 exception D3', 'PE12': 'avoid (loader SPI4): R8 exception D3', 'PE13': 'avoid (loader SPI4)', 'PE14': 'avoid (loader SPI4)',
    'PB1': 'forbidden off-board (TT)', 'PE9': 'forbidden (TT_ha 4.0 V; rationale was off-board/servo use): R8 exception D2',
    'PA9': 'avoid (loader USART1)', 'PA10': 'avoid (loader USART1)', 'PB10': 'avoid (loader USART3): R8 exception D2',
    'PB11': 'avoid (loader USART3): R8 exception D2', 'PA15': 'avoid (JTDI pull-up, loader SPI3)',
    'PD0': 'keep free (H723 FDCAN; voided in R7 pass 1)', 'PD1': 'keep free (H723 FDCAN; voided in R7 pass 1)',
    'PD8': 'keep free (H723 FDCAN; voided in R7 pass 1)', 'PD9': 'keep free (H723 FDCAN; voided in R7 pass 1)',
}
# D5: the only nets allowed on a pin the ROM bootloader drives (output or open drain), with the reason
LOADER_ALLOW = {
    'PA2': 'SERVO3: frozen 3.2 (TX input until detected on V9.1; a servo never sends 0x7F; R7 pass3_electrical 4.4)',
    'PB10': 'RADIO_SCK into the SX1262 held in reset by R311; USART3 never detected (PB11 held high by R310) (D2)',
    'PB14': 'RADIO_MOSI into the SX1262 held in reset by R311; no contention (D2; R7 had MISO here)',
    'PA11': 'USB_DM: DFU is the loader interface itself', 'PA12': 'USB_DP: DFU is the loader interface itself',
    'PB6': 'QSPI_NCS: open drain only, 10k pull-up keeps the flash deselected (frozen 3.5)',
    'PB9': 'I2C1_SDA: open drain only, 4.7k pull-up (frozen 3.6)',
}
VIEWED = {64, 69, 70, 72, 73, 75, 76, 79, 82, 83}   # Table 9 pages read as page images in step 0
POWER = {'VBAT', 'VSS', 'VDD', 'VSSA', 'VREF+', 'VDDA', 'VCAP'}

# R8 assignment: net, mode/AF, AF cite, external part that sets reset/loader line state, EXTI, decision ref, note
R8 = {
    7: ('BUZZ_DRV', 'GPIO out', '-', 'R163 10k to GND (via R162 220R): Q123 off', '-', 'D3 move',
        'backup-domain pin: VOH >= VDD-0.4 V at 3 mA (DS Table 52 p. 140), <= 2 MHz; firmware never routes RTC_OUT/TAMP/TS to PC13'),
    28: ('BAT_FAULT_N', 'GPIO in', '-', 'R89 10k to 3V3: high (no fault)', 'EXTI4', 'D3 move',
         'TT_a, IINJ 0/0 (DS Table 49): input only, pulled to 3V3; holds loader SPI1 NSS deselected'),
    29: ('LOGIC_SOURCE_ST', 'GPIO in', '-', 'R91 10k to 3V3: high', 'EXTI5', 'D3 move',
         'TT_ha, IINJ 0/0 (DS Table 49): input only, pulled to 3V3'),
    31: ('CAM_UART_OE', 'GPIO out', '-', 'R102 10k to GND: U12 disabled', '-', 'D3 move',
         'TT_a on-board; low in reset and in the loader (SPI1_MOSI input), so the SPI1 slave can never see the 0x5A sync byte'),
    37: ('CAM_MCU_RX', 'AF7 UART7_RX', 'PE7 AF7 UART7_RX', 'U12 A2Y output, Hi-Z while OE low', '-', 'D2 camera',
         'TT_ha on-board: U12 (TXU0202) VCCA = 3V3 (netlist), so the line stays <= 3V3 (Inference: A-port referenced to VCCA)'),
    38: ('CAM_MCU_TX', 'AF7 UART7_TX', 'PE8 AF7 UART7_TX', 'U12 A1 input (CMOS)', '-', 'D2 camera', 'TT_ha on-board, MCU output'),
    39: ('RADIO_NRST', 'GPIO out (push-pull)', '-', 'R311 2.0k to GND: radio held in reset', '-', 'D2 radio',
         'TT_ha on-board 3V3 line; sources 1.65 mA into R311 to release; firmware never selects AF7 (UART7_RTS/DE) on PE9'),
    41: ('CAM_FAULT_N', 'GPIO in', '-', 'R76 10k to 3V3: high', 'EXTI11', 'D3 move',
         'high level holds loader SPI4 NSS deselected'),
    42: ('CAM_PWR_EN', 'GPIO out', '-', 'R75 10k to GND (via R74 1k): camera eFuse U7 off', '-', 'D3 move',
         'static low on loader SPI4_SCK input'),
    45: ('RADIO_DIO1', 'GPIO in, EXTI15', '-', 'SX1262 DIO1 pulled down in reset (pass2_electrical 3.2)', 'EXTI15', 'D2 radio', '-'),
    46: ('RADIO_SCK_MCU', 'AF5 SPI2_SCK', 'PB10 AF5 SPI2_SCK/I2S2_CK', 'radio held in reset by R311; SCK is an SX1262 input', '-', 'D2 radio',
         'PB10/PB11 exception (D2): loader USART3 never detected because PB11 (NSS) is held high'),
    47: ('RADIO_NSS', 'GPIO out (software NSS)', '-', 'R310 100k to 3V3 at the MCU end: high, SX1262 MISO Hi-Z', '-', 'D2 radio, D4 R310',
         'no SPI2 AF on PB11 (DS Table 10 p. 91): software NSS (SPI_CFG1/CR SSM) by design'),
    53: ('RADIO_MOSI_MCU', 'AF5 SPI2_MISO pin, MOSI function with SPI_CFG2.IOSWP=1', 'PB14 AF5 SPI2_MISO/I2S2_SDI', 'drives into the SX1262 MOSI input (radio in reset)', '-', 'D2 radio',
         'IOSWP: RM0433 50.11.4 p. 2222 (bit 15, reset 0, writable only with SPI disabled), 50.4.2 p. 2159, note in 50.4.4 p. 2161; Table 422 p. 2157 sets no per-instance limit'),
    54: ('RADIO_MISO_MCU', 'AF5 SPI2_MOSI pin, MISO function with SPI_CFG2.IOSWP=1', 'PB15 AF5 SPI2_MOSI/I2S2_SDO', 'SX1262 MISO Hi-Z (NSS high, in reset); loader pull-up keeps PB15 high', '-', 'D2 radio',
         'IOSWP as pin 53; PB15 is never pulled to GND (AN2606 Table 136 limitation)'),
    56: ('RADIO_RXEN', 'GPIO out', '-', 'R312 100k to GND: low', '-', 'D2 radio', '-'),
    61: ('GNSS_RESET_N', 'GPIO out, open drain', '-', 'no pull, no capacitor: released (module pull-up)', '-', 'D2 GNSS', '-'),
    62: ('GNSS_TP_MCU', 'AF2 TIM4_CH4 input capture', 'PD15 AF2 TIM4_CH4', 'R307 1k from TIMEPULSE, never pulled down', '- (capture, never EXTI15)', 'D2 GNSS', '-'),
    65: ('VBUS_SENSE', 'GPIO in', '-', 'R9/R110 1k:1k divider from VBUS: 0 V without USB', 'EXTI8 (BUSY PD8 polled)', 'D3 forced', 'FT_h (VBUS divider)'),
    86: ('LED_RED', 'GPIO out', '-', 'R32 220R + LED1 to GND: off', '-', 'D3 forced', 'LEDs move to the west edge (placement, D3)'),
    88: ('LED_YEL', 'GPIO out', '-', 'R33 220R + LED2 to GND: off', '-', 'D3 forced', 'PD7 carries SPI1_MOSI as AF5 (unused)'),
}
FREED = {51, 52, 57, 81, 82, 84, 85}           # lose their R7 net, stay NC
# unchanged signal pins: (AF/mode, AF cite)
KEEP = {1: ('AF9 QUADSPI_BK1_IO2', 'PE2 AF9'), 3: ('GPIO out', '-'), 8: ('GPIO in', '-'), 12: ('HSE', '-'), 13: ('HSE', '-'),
        14: ('NRST', '-'), 15: ('ADC', '-'), 17: ('ADC', '-'), 18: ('ADC', '-'), 22: ('AF2 TIM5_CH1', 'PA0 AF2'),
        23: ('AF2 TIM5_CH2', 'PA1 AF2'), 24: ('AF2 TIM5_CH3', 'PA2 AF2'), 25: ('AF2 TIM5_CH4', 'PA3 AF2'), 33: ('ADC', '-'),
        34: ('ADC', '-'), 35: ('ADC', '-'), 36: ('AF9 QUADSPI_CLK', 'PB2 AF9'), 55: ('GPIO in (polled)', '-'),
        58: ('AF9 QUADSPI_BK1_IO0', 'PD11 AF9'), 59: ('AF9 QUADSPI_BK1_IO1', 'PD12 AF9'), 60: ('AF9 QUADSPI_BK1_IO3', 'PD13 AF9'),
        63: ('AF7 USART6_TX', 'PC6 AF7'), 64: ('AF7 USART6_RX', 'PC7 AF7'), 70: ('AF10 OTG_FS_DM', 'PA11 AF10'),
        71: ('AF10 OTG_FS_DP', 'PA12 AF10'), 72: ('AF0 SWDIO', 'PA13 AF0'), 76: ('AF0 SWCLK', 'PA14 AF0'),
        87: ('GPIO in', '-'), 89: ('AF5 SPI1_SCK', 'PB3 AF5'), 90: ('AF5 SPI1_MISO', 'PB4 AF5'), 91: ('AF5 SPI1_MOSI', 'PB5 AF5'),
        92: ('AF10 QUADSPI_BK1_NCS', 'PB6 AF10'), 93: ('GPIO out', '-'), 94: ('BOOT0', '-'), 95: ('AF4 I2C1_SCL', 'PB8 AF4'),
        96: ('AF4 I2C1_SDA', 'PB9 AF4'), 98: ('GPIO in (polled)', '-')}
CONTRACT = {2: 'pyro sentinel NC (check_actuators 5)', 3: 'pyro gate U1.3 (check_actuators 4)', 4: 'pyro sentinel NC',
            5: 'pyro sentinel NC', 15: 'continuity ADC U1.15 (check_actuators 6b)', 16: 'pyro sentinel NC',
            22: 'servo U1.22 (check_actuators 7)', 23: 'servo U1.23', 24: 'servo U1.24', 25: 'servo U1.25',
            32: 'pyro sentinel NC', 33: 'arm-sense ADC U1.33 (check_actuators 6b)', 34: 'RAW_ACT_SENSE U1.34 (check_actuators)',
            40: 'PE10 NC (check_actuators, check_r7 OTHER_NC)', 97: 'PE0 NC (check_actuators, check_r7 OTHER_NC)',
            98: 'IMU_INT1 on PE1 (check_actuators)'}

cols = ['pin', 'port', 'r7_net', 'r8_net', 'change', 'r8_mode_af', 'ds12110_t9_io_structure', 'ds12110_t10_af',
        'rm0433', 'an2606_t135_loader_role', 'mcu_reset_state', 'reset_and_loader_line_state', 'exti_r8',
        'frozen_3_10', 'loader_driven_allowance', 'contract', 'decision', 'notes', 'read1_source', 'read2_check']
rows = []
for n in range(1, 101):
    port = PORT[n]; was = r7[n]
    t9s, t9p = T9[n]
    t9 = f'{t9s} (Table 9 p. {t9p})'
    if port in POWER or port in ('NRST', 'BOOT0'):
        rows.append([n, port, was or 'NC', was or 'NC', 'unchanged', port, t9, '-', '-', '-', '-', '-', '-', '-', '-',
                     CONTRACT.get(n, '-'), '-', 'supply/dedicated pin; R7 net kept', '-', '-'])
        continue
    loader = LOADER.get(port, 'not used by the H74x bootloader (Table 135, pp. 320-323)')
    if port in LOADER_DRIVEN:
        loader += ' [LOADER-DRIVEN]'
    reset = 'analog, Hi-Z (DS 3.8 p. 32; Table 8 p. 63)'
    if port in ('PA13', 'PA14'):
        reset = 'debug pin: SWD with internal pull (DS 3.8 p. 32)'
    t10p = T10P(port)
    if n in R8:
        net, mode, afc, line, exti, dec, note = R8[n]
        change = 'moved in' if not was else 'reassigned'
        af = f'{afc} (Table 10 p. {t10p})' if afc != '-' else f'GPIO: no AF selected (Table 10 p. {t10p} read)'
        rm = 'SPI_CFG2.IOSWP = 1 (RM0433 50.11.4 p. 2222)' if n in (53, 54) else (
            'SYSCFG_EXTICR selects one port per EXTI line (RM0433 12.3.2-12.3.5 pp. 552-555); vectors Table 147 pp. 754-755'
            if exti.startswith('EXTI') else '-')
        assert t9p in VIEWED, n
        rows.append([n, port, was or 'NC', net, change, mode, t9, af, rm, loader, reset, line, exti,
                     FROZEN.get(port, '-'), LOADER_ALLOW.get(port, '-') if port in LOADER_DRIVEN else '-', CONTRACT.get(n, '-'), dec, note, f'DS12110 Table 10 pp. 89-94 images, Table 9 p. {t9p} image',
                     'pdftotext layout row re-read, agrees'])
    elif n in FREED:
        rows.append([n, port, was, 'NC', 'freed', 'NC (firmware: analog)', t9, f'- (Table 10 p. {t10p})', '-', loader, reset,
                     'no net', '-', FROZEN.get(port, '-'), '-', '-', 'D2/D3', 'R7 net moved away; stays unconnected in R8',
                     f'Table 9 p. {t9p}' + (' image' if t9p in VIEWED else ' text'), 'n/a: no net'])
    elif was:
        mode, afc = KEEP[n]
        af = f'{afc} (Table 10 p. {t10p})' if afc != '-' else '-'
        rows.append([n, port, was, was, 'unchanged', mode, t9, af, '-', loader, reset,
                     'as R7 (pass1/2/3_electrical, M3_R7 pin contract)', '-', FROZEN.get(port, '-'), LOADER_ALLOW.get(port, '-') if port in LOADER_DRIVEN else '-', CONTRACT.get(n, '-'),
                     '-', 'R7 net kept', f'Table 9 p. {t9p}' + (f'; Table 10 p. {t10p} image' if afc != '-' else ''), 'not required (unchanged)'])
    else:
        rows.append([n, port, 'NC', 'NC', 'unchanged', 'NC (firmware: analog or driven low for sentinels)', t9, '-', '-',
                     loader, reset, 'no net', '-', FROZEN.get(port, '-'), '-', CONTRACT.get(n, '-'), '-', 'stays unconnected',
                     f'Table 9 p. {t9p}', 'not required (unchanged)'])
with open(out, 'w') as f:
    f.write('\t'.join(cols) + '\n')
    for r in rows:
        f.write('\t'.join(str(x) for x in r) + '\n')
# self-checks
r8 = {r[0]: r[3] for r in rows}
for p in (2, 3, 4, 5, 15, 16, 22, 23, 24, 25, 32, 33, 34, 40, 97, 98):
    assert (r8[p] or 'NC') == (r7[p] or 'NC'), (p, r7[p], r8[p])
nets = [v for v in r8.values() if v not in ('NC', 'GND', '3V3', '3V3A', 'VCAP1', 'VCAP2')]
assert len(nets) == len(set(nets)), 'duplicate net'
lost = {v for v in r7.values() if v} - set(r8.values())
assert not lost, lost
for r in rows:
    if '[LOADER-DRIVEN]' in r[9] and r[3] != 'NC':
        assert r[14] != '-' and not r[3].startswith('LED') or r[3].startswith('LED'), r
        print('loader-driven pin with a net:', r[0], r[1], r[3], '|', r[14])
assert all(len(r) == len(cols) for r in rows)
print('rows', len(rows), 'changed', sum(1 for r in rows if r[4] != 'unchanged'))
