# M3-USB-R1 diagnostic software v0.6

> Historical version note: this document describes a firmware version bound to an earlier board candidate that is not included in this repository. Its subsystem behaviour, record formats and error codes carry forward into v0.8.1 on the current M3-ASSY-R1 board (see `ASSEMBLY_DIAGNOSTICS.md`); build directories and archives named below existed only in the original working tree.

This version connects the board's USB data interface to the diagnostic firmware: a computer can read a 1024-byte status snapshot and download the U3 log in 1024-byte blocks. It was bound to the single board M3-USB-R1, keeping voltage, pressure/temperature, raw IMU observations and the camera query option. **It is a compiled, software-fault-tested bench candidate; no flashing, real USB enumeration or whole-board acceptance.**

PCB SHA-256: `e920cb93616475bd0a8cba37461bd292404b0695fadf94cf4cbae266bc28ba40`.

## Which image to use

| Directory | Log operation | Camera |
|---|---|---|
| `build_usb_inspect` | Default; read-only scan/download, never writes flash | Off |
| `build_usb_record` | Appends diagnostic records at most once per second, read-back verified, no erase | Off |
| `build_usb_inspect_query` | Read-only | Queries device information once at boot, then disables UART OE and leaves camera power on |
| `build_usb_record_query` | Append | Same |

record is for collecting bench logs; the download tool requires inspect so the data being downloaded stays still. Replacing the MCU firmware and powering the bench board are separate steps; this tool never flashes or switches images. Old flash contents are never deleted automatically, and unknown / interrupted pages are kept. U6 was still DNP; no GNSS or control / actuation functions were added.

## Build and test

Run from the project root with the pinned Arm GNU toolchain; the sources never download dependencies during a build.

```sh
python3 m3_firmware/build.py --board usb --imu-samples --storage inspect
python3 m3_firmware/build.py --board usb --imu-samples --storage record
diagnostics/.venv/bin/python m3_firmware/verify_usb_firmware.py
```

`--camera-query` is an explicit option. Each image records its PCB and source / option hashes; `manifest.json`, ELF/BIN/HEX, the symbol table and `binding.json` are kept as a set. A new USB build never overwrites old build directories.

The host USB dependency is pinned to pySerial 3.5 in `diagnostics/requirements-lock.txt`. Port opening, bounded timeouts and DTR control follow the [official pySerial API](https://pyserial.readthedocs.io/en/latest/pyserial_api.html).

## Reading back once a real board is connected

Replace `PORT` with that board's explicit device name, e.g. `/dev/cu.usbmodem...` on macOS or `COM...` on Windows. The program never picks the first device automatically. First complete that board's power-up / USB current acceptance and wait for the boot scan to finish; no real hardware was available for this verification.

```sh
diagnostics/.venv/bin/python -m diagnostics.usb capture --port PORT --assembly BOARD001 --manifest m3_firmware/build_assembly_inspect/manifest.json --out diagnostics/runs/board001_usb.json
diagnostics/.venv/bin/python -m diagnostics.usb dump --port PORT --manifest m3_firmware/build_assembly_inspect/manifest.json --out diagnostics/runs/board001_flash
diagnostics/.venv/bin/python -m diagnostics.storage recover diagnostics/runs/board001_flash/flash.bin --out diagnostics/runs/board001_recovered
```

capture defaults to 2 samples 1.2 s apart (`--samples 2..30`). dump defaults to 16 MiB; `--sectors 1..4096` limits it to the first N 4 KiB sectors. Output paths must be new. The USB requests include no erase, target-memory write, reset or firmware-update commands; the CDC descriptors expose no MSC or DFU interface.

capture outputs the raw requests/responses, frame bytes/words, sequence numbers, times, PCB / firmware / UID and an `.analysis.json`. Over USB the chip identity is self-reported by the firmware — **not an independent SWD check and not cryptographic authentication**. If the identity changes within one connection, data is stale or a CRC fails, the result does not pass as a valid measurement.

dump outputs `flash.bin`, `chunks.jsonl` and `capture.json`. Each block's request ID, offset, length and CRC are checked independently, and identity and uptime are checked at the end. If interrupted, only the verified prefix is kept; failed blocks are never zero-filled and there are no automatic retries. Offline recovery needs whole sectors; a tail shorter than 4 KiB must be kept separately, never padded. The storage format keeps the first 127 words of v5/v6; live USB status is not in the log prefix, and recovery marks it explicitly `NOT_RECORDED`.

## Localising problems

| Evidence | Narrows it to | Next step |
|---|---|---|
| No serial port / connection failed | Host port, firmware not running, USB clock / power / data path; no chip readings in this case | Keep the failure JSON; read the result area over SWD, check power and TP92 |
| `USB_E_HSE` / `PLL_CONFIG` / `FREQUENCY` / `CLOCK_LOST` | HSE/PLL readiness and derived frequency | Check Y1 and the RCC evidence, measure with instruments; abnormal frequency values are kept as-is |
| `WAIT_VBUS` with the cable plugged in | PD15 detection or USB input voltage | Compare the actual voltage at TP92 / C28.1 with the GPIO reading |
| CRC / request ID / offset error | Stream misalignment, a stale transaction, an interrupted transfer or corrupt data | Keep the raw bytes, check the cable / driver; do not conclude that a chip is broken |
| `BUSY` or flash read failure | Initialisation, QSPI state, read-back error | Look at the STORE state / error history; never treat failed data as samples |
| Heartbeat / time not advancing | Stale record, stall or reset | Check the reset flags and SWD; a stable old value does not prove the board is healthy |

The v6 extension, words 160..183, records USB state, errors, clock, plug / enumerate / suspend counts, bytes sent and received, bad requests, timeouts, read errors, longest service interval and the relevant RCC/GPIO/USB registers. The host keeps USB error counts as evidence and never clears them. Full encoding in `protocol_usb.json`.

## Electrical and timing boundaries

The CPU and acquisition peripherals keep the original HSI scheme; USB alone uses the 25 MHz HSE → PLL3 (25, 192, Q = 4) to make 48 MHz. PD15 detects VBUS as an ordinary GPIO; PA9 is unused; PA11/PA12 are D−/D+. DWC2 is initialised and connected only after a stable high for 20 ms, and disconnected when unplugged. TinyUSB initialisation connects internally, so the call timing was checked separately. Rationale and pinned sources: [USB integration notes](research/usb/USB_INTEGRATION.md).

USB events are processed in the main loop / idle waits; the ISR only hands events over and never reads sensors or flash. The USB controller uses FIFO mode with DMA off, data in DTCM, and the D-cache currently disabled. USB flash reads use bounded indirect QSPI transactions; leaving / restoring memory-mapped mode uses a 20 ms handle timeout. Initialisation still depends on the ST HAL and a valid SysTick; firmware hangs, the watchdog and worst-case scheduling latency have not been measured.

The descriptors use TinyUSB's example development VID/PID **CAFE:4001**, not an identifier allocated to this product. The configuration declares 500 mA with no remote wakeup; **a descriptor cannot guarantee the board's actual current**. Hardware-load USB suspend power reduction is not implemented; input inrush, pre-enumeration / suspend current, HSE accuracy, hot back-feed / unplug detection, D+/D− signal integrity and cross-platform driver compatibility are all still to be measured.

The software evidence covered compiling the real sources, parsing the actual CDC descriptor bytes, scripted HAL faults, 192 request bit flips, fragmentation / back-pressure, production C ↔ host interoperation, old-protocol compatibility and the real pySerial no-device error path. None of it proves the real USB PHY, power stability, power-loss retention, sensor accuracy or full rocket function. Remaining items are listed in `../STATUS.md`.
