# M3 bench logging v0.5

> Historical version note: this document describes a firmware version bound to an earlier board candidate that is not included in this repository. Its subsystem behaviour, record formats and error codes carry forward into v0.8.1 on the current M3-ASSY-R1 board (see `ASSEMBLY_DIAGNOSTICS.md`); build directories and archives named below existed only in the original working tree.

Bound to the M3-UART-R1 board: `f8004cbb274808b1d334667d5331c1980cb69a16672b8c0284907862370e8e88`.
This package adds an on-board raw diagnostic log, file recovery after power loss and read-only SWD download; it does not change the PCB and is not a complete flight computer or a fab release.
Compilation and fault tests are not real-board verification.

Software evidence: 172 regression tests, nine build combinations, and a check that a wrong probe produces no data.

## Choosing an image

| Directory | Behaviour |
|---|---|
| `build_storage_inspect` | Default read-only; scans, reports old data, allows read-only download; camera off |
| `build_storage_record` | Explicitly appends records at most once per second; camera off; no automatic erase |
| `build_storage_inspect_query` | Read-only plus the existing one-time camera information query; camera power stays on afterwards |
| `build_storage_record_query` | Record mode plus the same camera query |

Each record keeps raw voltage / pressure / IMU data, nominal conversions, configuration, errors and sample times, plus board, firmware, MCU and flash identity.
Error states are logged as usual; an abnormal sample is never quietly replaced with zero or the last good sample.
A full flash, a write-back mismatch or a transfer error stops logging and increments a drop counter; the rest of the bench acquisition continues.
Detailed format, primary sources and power-loss limits: [sources and implementation notes](research/STORAGE_ACQUISITION.md).

## Build (no flashing)

```sh
python3 m3_firmware/build.py --board uart --imu-samples --storage inspect
python3 m3_firmware/build.py --board uart --imu-samples --storage record
```

Add `--camera-query` explicitly if the camera information query is wanted. Existing v2/v3/v4 images and protocols stay compatible.
v5 uses 1024 B of initialised SRAM; the tool checks the 16 B header before reading the new area, so old firmware cannot cause reads of uninitialised ECC memory.
The first full-flash scan takes time. `SCANNING` does not mean a sensor is broken; watch for the state to change before accepting.

## Reading back once the matching firmware is installed

No probe was connected and no firmware installed for this work. The following is tool usage only; take the probe ID from the actual probe list.

```sh
diagnostics/.venv/bin/python -m diagnostics probes
diagnostics/.venv/bin/python -m diagnostics.mailbox capture --probe-id PROBE_ID --assembly-id BOARD_SERIAL --binding m3_firmware/build_storage_inspect/binding.json --manifest m3_firmware/build_storage_inspect/manifest.json --out captures/inspect-001
diagnostics/.venv/bin/python -m diagnostics.storage dump --probe-id PROBE_ID --manifest m3_firmware/build_storage_inspect/manifest.json --out captures/log-001
diagnostics/.venv/bin/python -m diagnostics.storage recover captures/log-001/flash.bin --out captures/log-001-recovered
```

Download only works against an exactly matching inspect image. The host has no reset / halt / erase / write commands; the flash read range is fixed at 16 MiB, downloading only up to the highest non-empty sector. SWD is slow for large logs (USB came in v0.6).
An interrupted download keeps the complete sectors read so far in `flash.bin` plus the error in `capture.json`; a partial download is never marked complete.
The software never overwrites an existing output directory.

Recovery output: `records.jsonl` with every raw record and its diagnostics; `recovery.json` with CRC errors, unknown pages, orphan fragments, sequence gaps and bad-record addresses.
Offline files default to source `FILE_UNVERIFIED`; a file name is never taken as proof of physical data. Recovery never writes back to flash.

## Localising problems

| Error | Meaning and next check |
|---|---|
| ID/SFDP | U3 did not answer with the expected identity or interface bytes; check supply, NCS/CLK/IO0/IO1, package soldering and part number |
| CLOCK/IO | QSPI initialisation or transfer failed, HAL error kept; this alone does not prove the chip is broken |
| BUSY/TIMEOUT | The chip is busy/suspended or a write did not finish within budget; the chip is not reset and writes are not blindly retried |
| PROTECTED/QE | Status configuration does not allow logging; the tool never unlocks or changes status registers automatically |
| VERIFY | 03h or 6Bh readback differs from the page to be written; check supply / quad lines / timing / part; the success counter is not incremented |
| FULL | No new unused sector; old data kept; download it and follow an explicit maintenance procedure |
| INVALID_PAGE/INCOMPLETE_RECORD | Offline recovery found an unknown / corrupt / incomplete page; address and raw file kept; not a valid measurement |

Still missing (at v0.5): USB, real 500 Hz logging, real sensor accuracy / interrupts, physical power-loss tests, continuous running without a probe, whole-board acceptance.
Full requirements remain in [the status table](../STATUS.md); this addition does not declare the whole version complete.
