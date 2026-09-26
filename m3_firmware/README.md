# M3 bench diagnostic firmware

> **M3-ASSY-R2 (actuator merge, 2026-09-25): no firmware exists for R2 yet.** R2 moves LED_RED from PE3 to PE8 and turns PE3 / PE6 into no-net sentinels beside the pyro gates PE4 / PE5, so **v0.8.1 must not be run on an R2 board** (it drives PE3). `build.py` already refuses to build against the changed PCB hash; the reviewed R2 GPIO roles are in [`pins_r2.json`](pins_r2.json) and the rules in [`../docs/M3_ACTUATOR_MERGE.md`](../docs/M3_ACTUATOR_MERGE.md). A new binding must be written from `assembly_binding.py` together with the first R2 firmware, not by editing the R1 hash.

**Current version: v0.8.1 for M3-ASSY-R1.** Usage: [ASSEMBLY_DIAGNOSTICS.md](ASSEMBLY_DIAGNOSTICS.md). The host-side [triage entry point](../diagnostics/TRIAGE.md) ties USB snapshots, fault history and independent instrument readings to the current PCB's test points, keeping disconnections and partial evidence. **Nothing has been verified on a real board, and the complete M3 is not finished** (see [../STATUS.md](../STATUS.md)).

This is bench firmware: it acquires and logs diagnostic data and exposes it over SWD and USB. It contains **no flight-state estimation, attitude control, servo or pyro actuation**.

## What it does

| Subsystem | Implementation | Scope of the check |
|---|---|---|
| MCU start / liveness | ST startup code, HSI system clock, a heartbeat published every second | Reading back two records with consistent version / UID shows the program is running |
| Y1 crystal | Keeps running on HSI; enables the HSE briefly and records HSERDY; USB uses HSE → PLL3 48 MHz | Ready bits only; frequency, drive margin and drift are not measured |
| U4 IMU | ICM-45686 over SPI1: identity, raw accel / gyro / temperature at most once per second | See [IMU_DIAGNOSTICS.md](IMU_DIAGNOSTICS.md) |
| Rail voltages | ADC3: PC2_C / PC3_C dividers and VREFINT | Raw codes, reference calibration, VDDA / VLOGIC / 3V3; not yet compared with a meter. See [ACQUISITION.md](ACQUISITION.md) |
| U5 barometer | PROM / CRC at power-up; D1/D2 at OSR4096 with second-order compensation | Raw 24-bit codes, coefficients, Pa / 0.01 °C; accuracy not proven |
| U3 flash | Identity; append-only diagnostic log with single / quad-line write verification | See [STORAGE_DIAGNOSTICS.md](STORAGE_DIAGNOSTICS.md) |
| USB | TinyUSB 0.21.0 CDC: snapshot and read-only log download | See [USB_DIAGNOSTICS.md](USB_DIAGNOSTICS.md) |
| GNSS | USART6 read-only MON-VER / NAV-PVT polling, raw bytes and freshness | See [GNSS_DIAGNOSTICS.md](GNSS_DIAGNOSTICS.md) |
| Camera UART | One optional device-information query | See [UART_DIAGNOSTICS.md](UART_DIAGNOSTICS.md) |
| Power status | Battery / USB / camera FAULT and source-select ST inputs with history | See [POWER_STATUS_DIAGNOSTICS.md](POWER_STATUS_DIAGNOSTICS.md) |

The four prebuilt images for the current board are in `build_assembly_{inspect,inspect_query,record,record_query}/` (`.bin`, `.hex`, `.elf`, `manifest.json`, `binding.json`). The other `build*/` directories hold only the manifests of historical versions, used by the host tools' compatibility tests.

## Building

Uses the Arm GNU Toolchain 15.2.Rel1 and the ST CubeH7 v1.13.0 HAL/CMSIS. The vendor files in `vendor/` are pinned to fixed Git commits and verified by Git blob and SHA-256 at build time, with their licences kept; `fetch_vendor.py` can restore them from the official public repositories without any API key.

Get the toolchain from the [official Arm guide](https://learn.arm.com/install-guides/gcc/arm-gnu/) and unpack it into `m3_firmware/toolchain/` so that `TOOL` at the top of `build.py` resolves (`toolchain/arm-gnu-toolchain-15.2.rel1-darwin-arm64-arm-none-eabi/bin/`); on other hosts, adjust that path. Then:

```sh
python3 m3_firmware/build.py --board assembly --imu-samples --storage inspect
python3 m3_firmware/build.py --board assembly --imu-samples --storage record
# add --camera-query for the camera-query variants
```

The build checks the PCB hash and the native netlist against the firmware pin map, and refuses to build if the board has changed without a reviewed binding. It never touches a probe.

## Reading back a real board

Install the firmware separately with an ordinary debug tool and start from reset / power-up. J2 is wired by signal name: 1 = GND, 2 = SWCLK, 3 = SWDIO, 4 = NRST, 5 = 3V3 reference, 6 = BOOT0 — not the standard Arm 6-pin header. The readback tools never supply power, flash, halt, reset or erase.

Over USB (preferred), with a new output path each time:

```sh
diagnostics/.venv/bin/python -m diagnostics.usb capture \
  --port /dev/cu.YOUR_DEVICE --assembly BOARD_001 \
  --manifest m3_firmware/build_assembly_inspect/manifest.json \
  --out diagnostics/runs/board001_assembly.json
```

Over SWD:

```sh
diagnostics/.venv/bin/python -m diagnostics probes
diagnostics/.venv/bin/python -m diagnostics.mailbox capture \
  --probe-id EXACT_ID --assembly-id BOARD_001 \
  --binding m3_firmware/build_assembly_inspect/binding.json \
  --manifest m3_firmware/build_assembly_inspect/manifest.json \
  --samples 10 --interval 1.2 \
  --out diagnostics/runs/board001_mailbox
```

`EXACT_ID` must match the full enumerated probe ID. The readback checks sequence numbers, CRC32, version, PCB / firmware hashes and the UID read independently over SWD, taking 2–30 records at least 1.2 s apart to check heartbeats and sample counters. Stalled, old-firmware, corrupt or missing data never counts as a pass; hash / UID association is not anti-counterfeit authentication.

`PASS` applies only to that sub-check. The overall report is always `INCOMPLETE` or `ISSUES_FOUND`; no "board passed" is ever produced. If boot failed early or no firmware is installed, the result area may be empty or stale: check registers and external voltages first rather than declaring a sensor broken.

## Tests

```sh
pip install -r diagnostics/requirements-lock.txt
(cd m3_firmware && PYTHONPATH=.. python3 -m unittest test_firmware test_gnss test_usb test_imu test_storage test_camera test_power_status)
```

The tests compile the real production C functions for the host and drive them with scripted line levels / register models to check commands, error propagation and CRCs. **These are synthetic data, not electrical simulation or measurement.**

## Sources

- [ST CubeH7, pinned commit](https://github.com/STMicroelectronics/STM32CubeH7/tree/5abb9764b32e11a6557b90bf39531528019b5761): startup, LDO, HSI, GPIO/HAL and linker templates; per-file URLs in `vendor_manifest.json`.
- [TE MS5611 B3](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FMS5611-01BA03%7FB3%7Fpdf%7FEnglish%7FENG_DS_MS5611-01BA03_B3.pdf%7FCAT-BLPS0036): power-up reset, 2.8 ms reload, inverted CSB address bit and PROM commands.
- [MEAS AN520](https://www.amsys-sensor.eu/sheets/amsys.fr.an520_e.pdf): CRC low-byte handling and the public test vector giving 0xB.
- [Winbond Rev M](https://www.winbond.com/resource-files/W25Q128JV%20RevM%2012242024%20Plus.pdf): the W25Q128JV-IQ's EF4018 and the 9Fh transaction.
- TDK ICM-45686 DS-000577 Rev 1.0 §10.5 / §17.79: SPI read command and the 0xE9 identity.
