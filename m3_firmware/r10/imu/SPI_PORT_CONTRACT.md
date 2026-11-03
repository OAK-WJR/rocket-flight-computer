# Native SPI1 implementation contract

This contract is implemented by `spi_port.c` and `native_spi.c`, linked into
the sensor diagnostic image. It has source, cross-build and host register-model
verification, not a hardware pass. Pinned H743 headers/HAL are primary references.
No GPIOA/C/E, actuator outputs, DMA or interrupt-driven SPI are needed here.

| Item | Reviewed value |
|---|---|
| Pins | PB3/PB4/PB5 AF5; PB7 software CS, high before output mode |
| Clock | HSI ready, divider 1; CKPER=HSI; SPI123SEL=`100` (CKPER); SPI divisor 64, nominal 1 MHz |
| CFG1 | `0x50070007`: divider64, CRC size7, 8-bit data, one-frame FIFO threshold |
| CFG2 | `0x87400000`: master, software NSS, mode3, MSB first, keep IO control |
| CR1 idle | SSI=`0x1000`, SPE/CSTART off |
| CR2 | Finite TSIZE, TSER zero |
| IER / I2SMOD | Both off |
| Error bits | UDR/OVR/CRCE/TIFRE/MODF=`0x03e0`; unexpected SUSP also fails |
| IFCR clear | Direct write `0x0ff8`; no read-modify-write |

Set GPIOB's clock with readback. Raise CS before its output mode, preserve all
unrelated pin fields, configure clocks and pulse **only SPI1 reset**, then program
SPI while disabled. Set AF5 before the three MODER fields; no internal pulls.
Check configuration/CS readback. The shared CKPER/SPI123 clock selectors require
exclusive ownership or a reviewed agreement with other users.

For each transfer, use a single finite poll budget across all waits:

1. Clear flags, set TSIZE, enable SPE, assert CS, allow setup time, set CSTART.
2. For each byte: wait TXP, write TXDR with an **8-bit access**, wait RXP, read
   RXDR with an **8-bit access**. Reject error/suspension flags during waits.
3. Wait EOT, drain the expected receive data and reject residual RX data.
4. Apply a post-EOT/CS-hold guard, raise CS, clear EOT/TXTF, disable SPE and clear
   flags. TXTF alone is not wire completion; another TXC wait is not independent
   protection when TSIZE is nonzero.
5. On failure, preserve stage/status/counts, raise CS, request suspension and
   bound cleanup too. Reset only SPI1 if it does not stop. Mark the port
   uninitialized; require explicit reinitialization before another exchange.

No unbounded `HAL_GetTick` wait is permitted: a stalled SysTick must not turn a
nominal timeout into an infinite polling loop. A poll budget bounds software
iterations, not elapsed time or a stalled CPU/MMIO bus.

[ST ES0392](https://www.st.com/resource/en/errata_sheet/es0392-stm32h742x743xig-st32h750xb-and-stm32h753xi-device-errata-stmicroelectronics.pdf)
Rev16 §§2.22.2/.4/.5/.6 describe rapid-restart, disabled-interrupt, CRC-size and
post-EOT-disable constraints. Keep CRCSIZE=7 even with CRC off, IER=0 while
disabled, and disable/re-enable between transactions. ST gives no numeric minimum
for the post-EOT guard. The implemented 128-NOP guard at nominal 64 MHz is an
**engineering starting point**, not an ST-qualified guarantee; waveform tests
must establish sufficient sensor setup/hold/high times and absence of truncation.

Relevant pinned files: `stm32h7xx_hal_rcc_ex.h` clock selectors,
`stm32h743xx.h` SPI/RCC definitions, `stm32h7xx_hal_spi.c` finite TSIZE start,
byte FIFO accesses and EOT handling. See also [RM0433](https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)
§50.4.12 and DS15034 pp.25–26 (visually verified sensor mode3).
