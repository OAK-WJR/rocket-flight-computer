# M3-UART-R1 bench diagnostics v0.3

> Historical version note: this document describes a firmware version bound to an earlier board candidate that is not included in this repository. Its subsystem behaviour, record formats and error codes carry forward into v0.8.1 on the current M3-ASSY-R1 board (see `ASSEMBLY_DIAGNOSTICS.md`); build directories and archives named below existed only in the original working tree.

This version added **one device-information query and fault logging** for the routed camera UART, keeping voltage, pressure, temperature and device-identity diagnostics. Both ARM firmware builds compiled, but no real board or camera was connected and nothing was flashed; the complete M3 is not finished.

Bound PCB: `M3-UART-R1`, SHA-256 `f8004cbb274808b1d334667d5331c1980cb69a16672b8c0284907862370e8e88`. Protocol version 3 still occupies 512 bytes; the old PWR-R3 v2 protocol cannot be mixed with the new hardware.

## Choosing an image

| Directory / build | Power-up behaviour | At the end |
|---|---|---|
| `build_uart_idle`: `python3 m3_firmware/build.py --board uart` | Default; OE and camera power stay off, UART not initialised | Camera state `NOT_TESTED` |
| `build_uart_query`: the same command plus `--camera-query` | Turns the camera on; waits 3000 ms; reads GET_DEVICE_INFO once at 115200 8N1 | Disables UART OE, **camera power stays on** |
| `build`: `python3 m3_firmware/build.py` | Old PWR-R3 compatible build; does not drive the new UART | For old hardware and v2 compatibility checks only |

Each directory has its own `.elf/.hex/.bin`, `manifest.json`, `binding.json` and source hashes. Never choose by the file name `m3_bench.hex` alone; check the directory, board ID and manifest together. The build command never touches a probe or flashes.

The query version sends only the fixed request `CC 00 60`; never start/stop recording, simulated key presses or settings commands. The camera may start recording on its own and the firmware cannot know the SD-card write state, so it never cuts camera power once on, whether the query succeeded or failed. GPIO readback shows only the control-pin state, not the actual voltage at J9.

The 3000 ms start-up, 100 ms transmit / stale-data drain and 1000 ms response window are initial bench settings, not maker-guaranteed maximum timings. An unknown protocol version, incomplete reception, CRC mismatch or a PE/FE/NE/ORE error never counts as success. Only the protocol 1.0 information response verified here is supported; other modes are not silently downgraded.

## Wiring and evidence

J9: 1 = camera 5 V-class supply, 2 = GND, 3 = from camera TX, 4 = to camera RX. J2 SWD signals as in the [bench notes](README.md): 1 = GND, 2 = SWCLK, 3 = SWDIO, 4 = NRST, 5 = 3V3 reference, 6 = BOOT0.

The compiler is the Arm GNU Toolchain pinned in `toolchain/manifest.json`; ST dependencies are restored at a fixed commit by `fetch_vendor.py` (also in `vendor/`). Create `diagnostics/.venv` from `diagnostics/requirements-lock.txt`; no external API key is needed.

After separately installing the image that matches the PCB, read back from the project root (usage only; nothing was flashed or connected):

```sh
diagnostics/.venv/bin/python -m diagnostics probes
diagnostics/.venv/bin/python -m diagnostics.mailbox capture \
  --probe-id EXACT_ID --assembly-id BOARD_001 \
  --binding m3_firmware/build_uart_query/binding.json \
  --manifest m3_firmware/build_uart_query/manifest.json \
  --samples 10 --interval 1.2 \
  --out diagnostics/runs/board001_uart
```

For the default camera-off version, change both paths to `build_uart_idle`. Readback never resets, halts, flashes or writes target data; after the version header checks out, SRAM is still read only in `0x24000000..0x240001ff`. Use a new output directory each time so evidence is never overwritten.

Outputs include the raw `mailbox.json`, the driver log and `analysis/report.md/json`, `measurements.jsonl`. Records keep the raw response bytes, CRC error count, stale / discarded counts, protocol version, capability bits, GPIO readback, UART status, error bits, start / finish times and board / program identity. A valid response is stored separately and cannot be pushed out of the record by earlier garbage. The single boot-time query is republished with every heartbeat and **does not count as several independent UART tests**.

| Observation | Narrows it to | Next evidence |
|---|---|---|
| No / incomplete response | Supply, TX/RX wiring, camera not yet started, unsupported protocol / mode, etc. | Measure J9 supply, the TP90 logic supply and the TP91 enable first, then look at TX/RX; do not conclude the camera is broken |
| CRC error or noise / framing errors | Received bytes untrustworthy; raw bytes and PE/FE/NE/ORE kept | Check levels, cable, common ground, actual baud rate and supply disturbances |
| Init / clock / transmit timeout | The firmware or MCU peripheral path did not pass | Compare with status registers and the 64 MHz / BRR 556 readback; this does not identify a solder fault |
| Information query succeeded | This recorded device-information transaction succeeded | Camera electrical compatibility, recording and power-down isolation are still not accepted |
| No probe / version mismatch | No usable diagnostic evidence | Check the probe ID and image binding; never output a chip-failure conclusion |

## Software verification

The regression evidence pinned the sources, options and binary hashes of the three builds and recorded 96 regression tests: timeout / CRC / out-of-order / stale-data tests of the real C transaction function, and 12 cases of the real STM32 adapter against scripted registers; the 13 ADC and 14 bus cases were kept. Sub-cases are included in the 96, not added to inflate the count.

```sh
python3 m3_firmware/verify_uart_firmware.py
```

All three directories must be built before verifying; any change in sources / options / board refuses the old build. The bench "no probe" path is also exercised, keeping empty evidence rather than fabricating measurements.

Levels / bytes in the tests and the example reports are all marked `SYNTHETIC_FIXTURE`: not SPICE, not real-board data, not reliability statistics. Report status stays `INCOMPLETE` or `ISSUES_FOUND`, camera electrical qualification is always `NOT_TESTED`, and no whole-board pass is produced.

Rationale and limits: [CAMERA_UART.md](research/CAMERA_UART.md). Camera electrical thresholds, real start-up time, U12/U13 power-down behaviour, cable immunity, and whole-board IMU samples, flash logging, USB export and real-board dynamic verification remain. Full requirements: [STATUS.md](../STATUS.md).
