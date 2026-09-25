# ICM-45686 bench raw sampling: rationale

Checked 2026-09-08 UTC. Maker documents and a reference driver at a pinned commit were used. This document supports diagnostic sampling; it contains no attitude estimation or actuation control.

| Primary source | Local evidence |
|---|---|
| [TDK ICM-45686 product page](https://www.invensense.tdk.com/en-us/products/6-axis/icm-45686), listing DS-000577 v1.0 | The 200-page datasheet was cached locally, SHA256 `1fc7e54bcb03126e2094745a29440b97cd1ff8aff679f8a31e4ac121c415f274` |
| [TDK public reference driver](https://github.com/tdk-invn-oss/motion.mcu.icm45686.driver/tree/0a5bed6975b5cdeecb98f95db420f3058dd88547) | Pinned URLs, Git blobs and SHA256 of 10 files were recorded; licence kept; the reference code is not linked into the firmware |
| [ST SPI HAL, pinned](https://github.com/STMicroelectronics/stm32h7xx-hal-driver/blob/a1996eed9172b59887bafaaa0ea1816ea14d48b5/Src/stm32h7xx_hal_spi.c) | `vendor_manifest.json` pins 55 HAL/CMSIS files including the added SPI/SPIEx |

Decisions checked:

- DS §10.5: SPI mode 0/3, 7-bit address, read flag 0x80, burst reads supported. The bench uses HSI → CLKP → SPI1 ÷64 for a nominal 1 MHz; PB3/PB4/PB5 AF5, PB7 software chip select. The ST HAL source provides `HAL_SPI_TransmitReceive` with an 8-bit FIFO threshold of 1 and a 10 ms timeout, releasing chip select on return. ADC3 also uses HSI/CLKP, and SPI initialisation does not change its clock source.
- DS §15 p. 58: little-endian by default, but the maker requires explicitly setting SREG_CTRL / 0xA267 bit 1, and the data-register tables are described big-endian. The field is read back on every observation rather than assumed on the host.
- DS pp. 66–70: the 14 bytes from 0x00 are accel XYZ, gyro XYZ and temperature, all 16-bit signed. Nominal temperature conversion is raw/128 + 25 °C. No rule makes 0x8000 a universal invalid value, so signed extremes are kept and a range hint is reported separately.
- DS pp. 79–80 (rendered and checked visually): ACCEL_CONFIG0 / 0x1B and GYRO_CONFIG0 / 0x1C set to 0x0A = 50 Hz, range fields left at the reset ±32 g / ±4000 °/s; PWR_MGMT0 / 0x10 = 0x0F, both sensors in low-noise mode. The host decodes at nominal full scale and claims no sensitivity calibration.
- DS INT1 configuration / status tables: disable interrupts first, then INT1_CONFIG2 = 1 (push-pull, pulsed, active high), CONFIG0 = 4 to enable only UI DRDY. SPI polls bit 2 of 0x19 without using the EXTI; this **does not prove the PE10 interrupt line is connected correctly**. Reading 0x19 clears it, so old flags are cleared before waiting for a new DRDY, and after reading the code checks whether DRDY or RESET_DONE appeared again.
- DS pp. 109–110 and TDK `inv_imu_soft_reset`: save 0x2D/0x32, write 2 to 0x7F, wait, restore interface / driver configuration, and check the reset self-clears and RESET_DONE. Only once at initialisation; failure is never masked by endless reset retries.
- DS §14 pp. 56–57: IREG address 0x7C/0x7D, data 0x7E; a write must send address + data in the same burst to avoid a spurious prefetch; a read also prefetches the next address. Indirect accesses need at least 4 µs between them; the bench waits 1 ms and polls IREG_DONE (0x7F bit 0), at most 10 times.
- DS pp. 27–30 and TDK `inv_imu_regmap_le.h`: 0xA03A..0xA03D clear 0x48 / 0x92 / 0x24 / 0x49 respectively, removing the internal pulls of used or grounded pins; other bits are read-modify-write preserved. U4.9 is NC in the actual netlist, so 0xA03E bit 1 is kept; the build checks this assumption pin by pin.
- Accel / gyro start-up tables give 10 ms / 35 ms. Using 100 ms is a bench choice, **not a maker-guaranteed worst-case start-up time or a measurement**; a new DRDY must still be seen.

Diagnostic boundaries:

1. At most one observation per second, actively discarding accumulated DRDYs; not all 50 Hz samples, no FIFO, no log storage. Timestamps are the MCU's millisecond start / end of the read, not the sensor's internal sampling instant.
2. After a new DRDY, 14 bytes are read and checked for a further update; a read taking over 5 ms or updated during the read is rejected. This conservative check reduces the risk of straddling an update, but the documentation does not give every internal shadow-latch / synchronisation guarantee this implementation would need, so strict synchronisation or signal integrity cannot be claimed.
3. SPI timeouts and waits depend on a working SysTick; a stalled CPU / SysTick is still judged indeterminate by the host heartbeat. This firmware has not completed independent watchdog verification. Portable-driver loops also have bounded counts, with no endless automatic retries.
4. The scripted register model checks flow and error propagation; it cannot model real levels, traces, MEMS response, temperature drift, noise or assembly. There is no connected real board or measured data.
