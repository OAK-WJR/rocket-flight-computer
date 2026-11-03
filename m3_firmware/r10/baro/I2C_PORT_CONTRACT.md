# Native I2C1 barometer port contract

`i2c_port.c` implements the bounded register adapter; `native_i2c.c` exposes
`r10_native_baro_io()` using the parent-owned `baro_io.h`. These five files have
host register-model and ARM compilation verification only. They do not establish
hardware operation, measured frequency, oscillator accuracy or timing qualification.
Integration, the sensor state machine, conversion scheduling and build manifests
belong to the parent lane.

| Item | Contract |
|---|---|
| Fitted sensor | U5 MS561101BA03-50; PS high selects I2C; CSB tied to GND gives seven-bit address `0x77` (CSB is complemented) |
| SCL | U1.95 PB8 AF4 to U5.8; open drain, low GPIO speed, no internal pull |
| SDA | U1.96 PB9 AF4 to U5.7; open drain, low GPIO speed, no internal pull |
| External pull-ups | R12/R13 4.7 kOhm, **R12.2/R13.2 to 3V3**; U5 VDD and PS are on **3V3A**. These are distinct rails. This reflects the authoritative native-netlist correction. |
| Shared GPIO | Only PB8/9 fields in MODER, OTYPER, OSPEEDR, PUPDR and AFRH are changed. PB3/4/5/7 SPI1 fields and every other bit are preserved. No ODR/BSRR, GPIOA/C/E or actuator access. |
| Peripheral | I2C1 only; seven-bit, AUTOEND, no RELOAD; OAR1/OAR2 and TIMEOUTR zero; CR1=`PE` (analog filter on, DNF=0, DMA/IRQ/SMBus off) |
| Accepted messages | Exactly one TX command byte **or** two/three RX bytes, at `0x77`. Each callback is one START/address/STOP message; there is no repeated-START combined API. |
| Timing | TIMINGR=`0x70b44f4f`; PRESC=7, SCLDEL=11, SDADEL=4, SCLH=SCLL=79. `nominal_hz=50000` reports the design target, not measured SCL. |
| Budget | Native `poll_limit=65536`; adapter permits 1..1000000. One shared ISR-read budget covers idle, every byte, STOP, BUSY release and the final status check. |

The caller must serialize the port and shared RCC/GPIO read-modify-writes. It
must own I2C1/PB8/PB9 exclusively, keep the clock tree stable throughout each
callback, and avoid Stop mode while the port is enabled. No interrupt masking,
DMA, IRQ setup, SysTick/HAL_GetTick timeout, probe operation or
bit-banged bus recovery is used. Poll counts bound software iterations and
cleanup; they do not bound elapsed time under interrupts, stalled CPU or MMIO.

Clock registers are **read only**. Initialization and each transfer require:

| Register fields | Required value |
|---|---|
| RCC_CR HSION / HSIRDY / HSIDIV | 1 / 1 / 0 (nominal HSI 64 MHz) |
| RCC_CFGR SW / SWS | 0 / 0 (HSI requested and selected) |
| RCC_D1CFGR D1CPRE / HPRE | 0 / 0 (core and AHB undivided) |
| RCC_D2CFGR D2PPRE1 | 0 (APB1 undivided) |
| RCC_D2CCIP2R I2C123SEL | `00` (D2PCLK1, the reset path) or `10` (HSI) |

Both accepted paths make APB1/kernel/core nominally 64 MHz and APB1/kernel
ratio 1. Other encodings, even equivalent divider aliases, fail without silently
changing a shared selector. No new parent clock write is needed for the pinned
SystemInit reset path. Only GPIOBEN and I2C1EN are enabled with readback; only
I2C1RST is pulsed. D1CCIPR and D2CCIP1R, used by SPI1, are never accessed.

The timing calculation below is an engineering design, conditional on
`0 <= tr <= 1000 ns`, `0 <= tf <= 300 ns`, analog filter delay 50..260 ns and
kernel/core frequency 60..68 MHz. The last interval is a deliberately stated
design envelope, **not** a claim about an HSI production tolerance. The actual
pull-up tolerance, bus capacitance, fall slope, sensor setup/hold, supply
sequencing between 3V3 and 3V3A, and installed waveforms remain unmeasured.

Using the RM0433 timing counters and AN4235 method, let `t=1/fkernel` and
`p=(PRESC+1)*t`. At nominal 64 MHz, `t=15.625 ns`, `p=125 ns`:

| Check | Calculation at nominal 64 MHz |
|---|---|
| Low/high counters | `(79+1)*p = 10000 ns` each |
| Minimum low/high including synchronization | `10000 + 50 + 2*t = 10081.25 ns`; exceeds Standard-mode 4700/4000 ns |
| Data setup | `(11+1)*p = 1500 ns >= tr_max + tSU:DAT_min = 1250 ns` |
| SDADEL lower bound | `tf_max + tHD:DAT_min - tAF_min - (DNF+3)*t = 203.125 ns <= 4*p = 500 ns` |
| SDADEL upper bound | `4*p = 500 ns <= tVD:DAT_max - tr_max - tAF_max - (DNF+4)*t = 2127.5 ns` |
| Total SCL period, no additional stretching | `tr + tf + 80*p + 80*p + 2*tAF + (4..6)*t` |

RM0433's setup/hold discussion includes the extra kernel cycle in
`tSDADEL = SDADEL*p + t`; the above `(DNF+3/4)*t` bounds already include it.
SCLL also generates bus-free/START-setup timing; SCLH generates START-hold and
STOP-setup timing. Their 10 us nominal counters exceed the respective 4.7/4 us
minima. The 512-NOP guard before checking idle adds at least 7.53 us within the
stated core-frequency envelope; it is not a frequency measurement.

Across 60..68 MHz, the shortest low/high lower bound is about 9.491 us,
the shortest setup counter 1.412 us, and the hold counter is 0.471..0.533 us,
inside the calculated bounds. With the stated rise/fall/filter envelope,
unstretched SCL computes to approximately 45.63..49.60 kHz at 64 MHz and
43.00..52.68 kHz across 60..68 MHz, below 100 kHz. Clock stretching and software
service delay can only lengthen these modeled periods. For a nominal 4.7 kOhm
pull-up, `tr=0.8473*R*C` makes the 1 us assumption correspond to about 251 pF;
that is a conditional load estimate, not a measured board capacitance.

Initialization resets I2C1, configures it with PE clear, parks only PB8/9 in
analog mode while setting open drain/AF4, then enables it. Configuration and
pin readback must match; both lines must read high with BUSY clear within the
budget. A blocked SCL or SDA is a failure, including a bus whose peripheral
BUSY flag is misleadingly clear.

Each message checks clocks/configuration, waits for a clean idle bus, and writes
all CR2 transfer fields plus START together. TXDR/RXDR CPU accesses are 32-bit words with byte-valued payloads, matching
RM0433 §47.7 and ST LL register access. This differs from SPI FIFO access width.
TXIS or RXNE alone cannot finish a callback: it must also observe STOPF,
BUSY clear and high SCL/SDA. The expected final receive byte may coexist with
STOPF and must still be read. STOPCF is written directly, followed by another
error/status check. ICR is never read or modified through RMW.

Every status check rejects NACKF/BERR/ARLO/OVR/TIMEOUT before any ready flag.
Unexpected PECERR/ALERT/ADDR/TC/TCR also fail. The receiver's normal final
outgoing NACK is not NACKF; an observed NACKF always fails. Partial RX output
must be discarded on any nonzero return. Invalid arguments do no MMIO and do
not disturb a usable port.

On a transport failure, `detail = 0x80000000 | stage<<16 | (last_ISR & 0xffff)`
is saved before cleanup; `transmitted`/`received` preserve software byte counts.
Stages are CLOCK=2, CONFIG=3, INIT_IDLE=4, ARGUMENT=5, IDLE=6, TX=7, RX=8,
STOP=9, BUSY=10, FINAL=11; invalid adapters report stage 1. A budget exhaustion
retains the last observed ISR and is not falsely presented as hardware TIMEOUT.
If this callback requested START and still owns a busy transfer, cleanup
requests STOP with START masked out and allows at most 128 further ISR polls.
No STOP is requested after observed ARLO or for a bus busy before our START.
Cleanup clears PE, reads it back, and pulses only I2C1RST even when STOP/disable
did not complete. At most `poll_limit+129` ISR reads occur including cleanup.
The port remains uninitialized until an explicit successful initialize; removing
the injected fault alone cannot enable another transaction.

TE's OSR4096 conversion table is min 7.40 / typ 8.22 / max 9.04 ms. As specified
by the parent, its 12 nominal ms conversion guard starts on the first subsequent
poll **after the command callback returns**. This transport does not schedule
conversion waits or incorporate the callback's own latency into that guard.

Primary sources checked before implementation (2026-11-03):

- [ST RM0433 Rev 8](https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), chapter 47: setup/hold pp.1956-1957, PE reset p.1959, master transmit/receive, CR2 p.2007, TIMINGR and W1C register semantics. Full-PDF fetch exceeded the browser limit and direct download failed; the relevant ST-hosted indexed passages were read explicitly.
- [ST ES0392 Rev 16, October 2026](https://www.st.com/resource/en/errata_sheet/es0392-stm32h742x743xig-st32h750xb-and-stm32h753xi-device-errata-stmicroelectronics.pdf), §§2.19.1-.10. Seven-bit/no-RELOAD/no-target/no-SMBus operation avoids the corresponding modes. The 60 MHz minimum design kernel is above the 4 MHz Standard-mode sampling workaround threshold. APB1/kernel=1 avoids the first-byte stall ratio. Spurious BERR is possible; this diagnostic port intentionally reports it as failure as required by its scope, accepting possible false negatives.
- [ST AN4235 Rev 2](https://www.st.com/resource/en/application_note/an4235-i2c-timing-configuration-tool-for-stm32f3xxxx-and-stm32f0xxxx-microcontrollers-stmicroelectronics.pdf), §§2.2.2-.4, timing method and rise/fall/filter effects. This F0/F3 note supplies the method; H743 register behavior comes from RM0433.
- [ST DS12110](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf), I2C analog-filter characteristics (50..260 ns); [ST-hosted manufacturer PDF](https://community.st.com/ysqtg83639/attachments/ysqtg83639/stm32-mcu-products-forum/283157/1/stm32h743vi.pdf). Pin AF4 assignments also match the reviewed native pin table.
- [TE MS5611-01BA03 B3, June 2017](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FMS5611-01BA03%7FB3%7Fpdf%7FEnglish%7FENG_DS_MS5611-01BA03_B3.pdf%7FCAT-BLPS0036), pp.3, 7, 12-13: conversion limits, complemented CSB, STOP-delimited command/PROM/ADC transactions.

The brief's `AN4779` could not be verified as an ST I2C timing reference. The
primary [NXP AN4779](https://www.nxp.com/docs/en/application-note/AN4779.pdf) is
an EMC note for Kinetis E and is not used for this driver. `hyperresearch search`
was attempted first and reported no vault; no external search API key was used.
No third-party driver source was copied.

The pinned local `vendor/device/Include/stm32h743xx.h` was SHA-256 checked against
`vendor_manifest.json`: `9a4ea0860707868a1cc562140ba214d535fb5a64fde91b451b2767276eef7e03`
(CMSIS device commit `8f922cdc7cc6de2344e75ddd657889f4ff761790`). The pinned
`vendor/hal/Inc/stm32h7xx_hal_rcc_ex.h` clock selectors and SystemInit were also
hash-checked. No HAL I2C module is present or required. ARM static assertions
cover every accessed MMIO offset, base and register-field mask used by the port.

Validation from `m3_firmware/r10`:

```sh
clang -O1 -g -Wall -Wextra -Werror -std=c11 -fsanitize=undefined \
  -fno-sanitize-recover=undefined -Ibaro baro/test_i2c.c baro/i2c_port.c \
  -o /private/tmp/r10-test-i2c
/private/tmp/r10-test-i2c
```

The scripted model verifies W1C and START auto-clear, distinct wire/RX/software
completion, early/late STOP, back-to-back commands and reads, final NACK+ready,
every polling-stage fault, budget exhaustion, stuck SCL/SDA, missing STOP/BUSY
release, residual RX, cleanup failure and explicit recovery. Every shared-register
write checks preservation, including SPI1 pin fields. Clock selectors cannot be
written and addresses outside the I2C1/RCC/GPIOB allowlist fail the test.
The model is a software oracle with scripted timing, not STM32 silicon emulation.
Both production C files also compile with pinned Arm GNU 15.2.1 for Cortex-M7,
`-std=c11 -ffreestanding -Wall -Wextra -Werror`, using the pinned CMSIS headers.
Full-image integration and physical timing validation are outside this lane.
