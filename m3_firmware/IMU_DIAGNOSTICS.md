# M3-UART-R1 bench diagnostics v0.4

> Historical version note: this document describes a firmware version bound to an earlier board candidate that is not included in this repository. Its subsystem behaviour, record formats and error codes carry forward into v0.8.1 on the current M3-ASSY-R1 board (see `ASSEMBLY_DIAGNOSTICS.md`); build directories and archives named below existed only in the original working tree.

Adds **raw acceleration, angular rate and temperature samples from U4, with fault evidence**. Voltage, pressure and camera diagnostics are kept. The complete M3 still has missing functions; these programs were never flashed to a real board, and neither sensor accuracy nor whole-board reliability was verified.

Bound board: M3-UART-R1, PCB SHA256 `f8004cbb274808b1d334667d5331c1980cb69a16672b8c0284907862370e8e88`. It is a diagnostic software addition, not a new fab package.

## Images and readback

| Build directory | Build command | Behaviour |
|---|---|---|
| `build_imu_idle`, the default | `python3 m3_firmware/build.py --board uart --imu-samples` | IMU / voltage / pressure sampling; camera power and OE stay off |
| `build_imu_query` | The same plus `--camera-query` | Turns the camera on and reads device information once; disables OE, leaves camera power on; then samples |

Sources restore 55 ST HAL/CMSIS files at a fixed commit; compiler version / download hash in `toolchain/manifest.json`. The build checks the PCB, the native netlist, each of U4's ground/NC pins and GPIOs, maker source files and source hashes. It never touches a probe or flashes. The package does not carry the ~140 MB compiler or the Python virtual environment; see [the README](README.md) for restoring dependencies.

After installing the matching firmware separately and resetting, read back from the project root (no real board yet):

```sh
diagnostics/.venv/bin/python -m diagnostics probes
diagnostics/.venv/bin/python -m diagnostics.mailbox capture \
  --probe-id EXACT_ID --assembly-id BOARD_001 \
  --binding m3_firmware/build_imu_idle/binding.json \
  --manifest m3_firmware/build_imu_idle/manifest.json \
  --samples 10 --interval 1.2 \
  --out diagnostics/runs/board001_imu
```

For the query version change both `build_imu_idle` to `build_imu_query`. Never mix bindings or firmware from different boards / versions. J2 is still 1 = GND, 2 = SWCLK, 3 = SWDIO, 4 = NRST, 5 = 3V3 reference, 6 = BOOT0 — not the standard Arm 6-pin header. The readback program never writes target memory, halts, resets or programs.

Protocol v4 still uses only the 512 bytes at `0x24000000..0x240001ff`. Boot, version, identity and CRC semantics are unchanged, with IMU records added in words 112–126; the exact v2/v3/v4 version is checked before reading the whole result area. Any mismatch in CRC / before-after sequence / UID / board and firmware hash, heartbeat or sample count produces no valid sample.

## What each record means

Each line of `analysis/measurements.jsonl` gains an `imu` object: 14 raw bytes, 7 signed raw values, nominal unit conversions, SPI rate, configuration readback, DRDY/reset bits before and after, start / finish times, an error code and a cumulative error bitmap. Failed data keeps its raw bytes but `nominal_units` is empty; later successes never erase earlier anomalies.

The IMU is configured internally at 50 Hz, and the program **observes at most once per second**, skipping the samples in between. It is not a 50 Hz logger. The start / end times are the MCU's millisecond timestamps of the register reads, not the sensor's exact sampling instants. Voltage, pressure and IMU are not sampled synchronously either.

| Error | Check first |
|---|---|
| CLOCK / SPI_INIT | Core / peripheral clock readback, SPI configuration, chip-select level; `io_error` stores the HAL status or adapter check code |
| TRANSFER | U4 supply, pins / soldering, PB3/4/5/7 continuity and waveforms; one failure does not trigger endless reset retries |
| IDENTITY | The WHO_AM_I actually read; all 0s / all 1s can come from an open line, supply or chip select — do not conclude the chip is broken |
| RESET / CONFIG | Reset-done bit, reset / configuration drift while running, byte order / range / ODR; units are interpreted only with readback evidence |
| IREG_TIMEOUT | The indirect register interface is busy; fails after a bounded wait, keeping context |
| READY_TIMEOUT | No new DRDY after 100 polls since clearing old flags; check configuration, supply and the device's real state |
| UPDATE_DURING_READ / READ_TOO_SLOW | Data updated again during the raw read, or the read window exceeded 5 ms; bytes kept and this sample rejected |
| TICK_STALLED | The delay callback did not advance the timebase; a fully stalled CPU / SysTick still relies on the host's liveness check |

`io_error`: high byte = HAL return status, low bits = HAL SPI error; `0x40000001` = chip select read back low, `...02` = kernel clock mismatch, `...03` = SPI register configuration mismatch, `...04` = wrong transfer length. Software pin readback is not an actual voltage or waveform measurement.

## Software verification and what is missing

```sh
python3 m3_firmware/verify_imu_firmware.py
```

The regression evidence recorded the final test count, five images and input hashes. The tests run the real C driver, covering communication failures at every initialisation / sampling transaction point, readback mismatches, wrong byte order, stale DRDY, updates during reads, timeouts, millisecond wraparound and error-recovery history; the real STM32 adapter was also tested against a scripted HAL with UBSan. C result bytes feed straight into the host parser as an ABI cross-check.

All of this is **software and synthetic fault testing**. No real IMU data, electrical simulation or accuracy proof exists. Still needed: real supply / bus waveforms, the PE10 interrupt line, built-in self-test, independent motion / temperature references, noise and real running tests; the internal synchronisation guarantee of direct register burst reads was not fully verified by this tool either. Other whole-board functions: [the requirement status table](../STATUS.md).

Maker documents, register / wait rationale and explicit limits: [acquisition notes](research/IMU_ACQUISITION.md). All report statuses stay `INCOMPLETE` or `ISSUES_FOUND`; no "board passed" is ever produced.
