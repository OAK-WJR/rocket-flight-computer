# Host diagnostics

**Current: M3-ASSY-R1 / firmware v0.8.1.** Start with the [unified triage entry point](TRIAGE.md):

```sh
python -m diagnostics.triage capture --port ACTUAL_PORT --assembly BOARD_001 --out NEW_DIRECTORY
```

It saves the raw exchange, fault branches, the 30 test-pad coordinates of the current PCB and an empty instrument template, and still produces a report on disconnection. The default firmware directory is `m3_firmware/build_assembly_inspect`. Nothing has been verified on a real board; the complete M3 is not finished.

Other entry points, each tied to the firmware version whose board binding it matches:

| Module | Purpose | Firmware notes |
|---|---|---|
| `diagnostics.usb capture` / `dump` | Read the 1024-byte status snapshot over USB CDC; download the flash log (inspect images only) | [USB](../m3_firmware/USB_DIAGNOSTICS.md), [GNSS](../m3_firmware/GNSS_DIAGNOSTICS.md), [power status](../m3_firmware/POWER_STATUS_DIAGNOSTICS.md) |
| `diagnostics.storage recover` | Parse a downloaded flash image into records, keeping corruption locations and raw records as JSONL | [Storage](../m3_firmware/STORAGE_DIAGNOSTICS.md) |
| `diagnostics.mailbox capture` | Read the firmware's fixed SRAM result area over SWD | [Firmware README](../m3_firmware/README.md) |
| `diagnostics capture` / `report` / `bench-template` | SWD register capture, raw evidence and interpretation of external DC measurements | Below |

The host never flashes, erases or writes target memory. Errors, no fix, stale data and unknown identities are reported separately; a receiver's self-reported accuracy is never treated as a measurement. `examples/` contains synthetic data only.

## SWD register capture

Run from the project root. Offline reports need only Python 3.9+; connecting a probe needs the pinned pyOCD.

```sh
python3 -m venv diagnostics/.venv
diagnostics/.venv/bin/python -m pip install -r diagnostics/requirements-lock.txt
diagnostics/.venv/bin/python -m diagnostics probes
diagnostics/.venv/bin/python -m diagnostics capture --probe-id EXACT_ID --assembly-id BOARD_001 --out diagnostics/runs/board001_first
```

`EXACT_ID` comes from the `probes` output and must match exactly; the first probe is never chosen by default. Use a new output directory every time. A capture stores each address, width, raw value or specific error, sample time, probe / driver version, assembly ID and the board file's SHA-256. Existing records are never overwritten; a driver call taking over 25 s is aborted with partial data kept. This recovers forensic data; it does not recover failed hardware.

J2 is not the standard Arm 6-pin header. Connect the probe by **signal name**:

| PCB J2 | Signal | Use |
|---|---|---|
| 1 | GND | Probe ground |
| 2 | SWCLK | Debug clock |
| 3 | SWDIO | Debug data |
| 4 | NRST | Not actively reset by this tool; may be left unconnected |
| 5 | 3V3 | Probe voltage reference, not a second supply input |
| 6 | BOOT0 | Not used by this tool; never connect it to reset or power |

This stage is for a bare board on a current-limited bench supply; attaching a debugger can change timing / low-power behaviour, so a debug session cannot prove reliability without the probe.

## Interpreting the output

- `snapshot.json` is the raw evidence, `analysis/report.md` gives findings and the next test point, `report.json` is for automated analysis.
- `PASS` applies only to the stated sub-check (e.g. "capacity register reads 2048 KiB"); it does not mean the flash reads and writes, or that the board passed.
- `INFO` is an observation or consistent with the model, `WARNING` needs further observation, `FAIL` clearly breaks that item's criterion, and `NOT_TESTED` / `INCONCLUSIVE` never count as a pass.
- The overall result is always `INCOMPLETE` or `ISSUES_FOUND`; `hardware_qualified` and `fabrication_release` are always false. Exit code 0 only means the capture/report command ran; 2 means the report found a FAIL; 3 means a capture, input or tool error.
- DEV_ID = 0x450 cannot distinguish every orderable part in the family, nor genuine from counterfeit chips / packages. CPUID decoding keeps variant/revision so a normal silicon revision is not misreported as the wrong chip.
- RCC_RSR holds history flags that may accumulate or be cleared by firmware, so no single "reset cause" is forced. With the HSE not enabled, the crystal is not judged broken; a changing clock configuration is reported as a non-atomic snapshot.
- Register capture never runs ADC, SPI, I2C or external QSPI transactions; sensor identity / samples, storage read/write, USB enumeration and real watchdog resets are not tested by it.

## External instrument measurements

```sh
python3 -m diagnostics bench-template diagnostics/runs/board001_first/snapshot.json --out diagnostics/runs/board001_first/bench.json
python3 -m diagnostics report diagnostics/runs/board001_first/snapshot.json --bench diagnostics/runs/board001_first/bench.json --out diagnostics/runs/board001_first/with_meter
```

The template contains the real pads and coordinates, with measurement fields initially null. Fill each real measurement in this structure (the values are only a format example and must never be copied as an acceptance record):

```json
{"value": 3.30, "unit": "V", "uncertainty_v": 0.01, "input_ohm": 10000000,
 "instrument": "actual instrument model / ID", "measured_at": "actual ISO date-time"}
```

`uncertainty_v` is an absolute error bound from the instrument specification, resolution and method; never enter 0 because it wasn't calibrated. Divider checks include 1 % resistors and the meter's input impedance loading the lower arm; the model has no dynamic ADC load. Paired voltages should be measured in the same stable supply configuration. The board file hash, assembly ID and capture_id must agree; this is provenance linking, **not an anti-counterfeit signature, and it cannot prove the physical board matches the PCB file**.

On a severe power-tree drop, check the USB / battery input path, then the U2/L1 regulator stage or the L2 sensor supply branch. Unknown versions never get guessed reference designators. The report keeps candidate causes such as "upstream open / downstream short" and never declares a chip broken from one voltage. 3.3 V ± 5 % is only a screening window.

## Connection behaviour and basis

pyOCD's normal connect, auto-unlock and disconnect can halt, erase or resume the core, so this tool does not use normal target initialisation ([pyOCD session options](https://pyocd.io/docs/options.html)). It is pinned to pyOCD 0.45.1: a session in an empty temporary directory with no configuration or user scripts; after `open(init_board=False)` it connects only the DP and AP0 and reads a whitelist through `MinimalMemAP`; a guard proxy only allows writes to the AP's CSW and to TAR for listed addresses, rejecting DRW/BD data writes. It never calls target.init, reset, halt, resume, unlock or flash algorithms, never reads the flash program area and never touches GPIO. **The SWD protocol itself must write debug-port configuration / addresses and request debug power; this is not a zero-disturbance measurement.** ([pyOCD API examples](https://pyocd.io/docs/api_examples.html), [H743 target source](https://github.com/pyocd/pyOCD/blob/v0.45.1/pyocd/target/builtin/target_STM32H743xx.py))

Register addresses / bit definitions come from the pinned [ST CMSIS H743 header](https://github.com/STMicroelectronics/cmsis-device-h7/blob/81db1ec63cdc191fae1565b772da3ea5aa29a683/Include/stm32h743xx.h) and [Arm CMSIS](https://github.com/ARM-software/CMSIS_6); `sources/manifest.json` keeps the exact URLs and SHA-256, with the original headers and licences.

## Regression tests

```sh
python3 -m unittest discover -s diagnostics -t . -p 'test_*.py'
```

The tests cover stopping chip-specific reads after a wrong family, capacity mismatches, chip revisions, timeouts / missing evidence, reset history, clock changes, fault-address VALID bits, L2 branch drops, swapped divider arms, meter loading, error bounds, wrong board / session / duplicate JSON data, and a real pyOCD MinimalMemAP rejecting memory writes through the guard proxy. API tests are not circuit simulation or a real-board connection.
