# R10 firmware readback

`diagnostics.r10_firmware` separately compares the installed internal image with
the reviewed [R10 sensor diagnostic build](../m3_firmware/r10/README.md) and acquires two
1024-byte ABI v4 CRC-protected RAM records. Original register-only SWD and legacy R1
permissions remain unchanged. Development tests use synthetic DP/MCU data only;
no probe was opened or image flashed, and no physical R10 test has passed.

## Capture prerequisites

Provide the current PCB and a fresh R10 `manifest.json` / `r10_bench.bin`. Board,
J2 binding, firmware source inventory, netlist, pin table, vendor inputs, build ID
and image hash are checked before opening a probe. Changed source requires a
rebuild; changed PCB requires a reviewed binding, never an automatic refresh.

The operator must independently install the image and reset-boot into user flash,
with external loads isolated. Both CLI flags below record declarations, not
measurements. Native J2 wiring is in [R10_SWD.md](R10_SWD.md); its 3V3 pin is probe
voltage reference, not another supply. No hot plugging is part of this workflow.

Reset boot matters: the bootstrap initializes AXI SRAM before setting VTOR to
user flash. Chip identity, power readiness and VTOR are checked before reading
the image; power/VTOR are checked again before RAM. Image equality alone does not
prove execution. Debug reads of uninitialized SRAM can affect ECC status, and
SWD requests debug/system power; zero disturbance is not guaranteed.

Use pinned pyOCD 0.45.1 and a new output directory:

```sh
diagnostics/.venv/bin/python -m diagnostics.r10_firmware capture \
  --board m3_design/assembly_review/m3.kicad_pcb \
  --manifest m3_firmware/r10/build_local/manifest.json \
  --image m3_firmware/r10/build_local/r10_bench.bin \
  --probe-id EXACT_PROBE_ID --assembly-id BOARD_001 \
  --bench-isolated --reset-boot-confirmed --out NEW_CAPTURE_DIRECTORY
```

The tool never resets, halts, resumes, erases or programs as a fallback. A child
has a 30-second deadline and bounded terminate/kill grace periods. There is no
automatic reconnect loop. An unreaped worker's PID is retained; confirm that it
has ended before another connection.

## Record integrity and evidence

The firmware publishes once per nominal second while internal tick/main counters
continue at millisecond cadence. Each sample gets at most three attempts, with
sequence reads before/after, CRC and board/build/MCU-UID checks. The host waits
1.1 seconds between samples. This provides a longer window at 100 kHz SWD; real
probe timing remains unmeasured and a record may still change during a read.

The request saves assembly/probe/build IDs, declarations, expected image,
manifest and acquisition source hashes. `observed_image.bin` keeps partial image
bytes; `snapshot.json` atomically preserves partial registers, failed attempts,
words, errors and AP trace. Execution and supervisor receipts are separate.
Timeout supervision never replaces the raw snapshot. Replay checks its hash,
cross-attempt/sample chronology and receipts; changed evidence is refused.

```sh
python3 -m diagnostics.r10_firmware report \
  --board m3_design/assembly_review/m3.kicad_pcb \
  --run EXISTING_CAPTURE_DIRECTORY --out NEW_ANALYSIS_DIRECTORY
```

Replay needs no pyOCD or probe. New JSON/Markdown reports distinguish:

| State | Supported conclusion |
|---|---|
| `PROGRESS_OBSERVED` | Matching image and two coherent records show advancing nominal ticks, main count and generation |
| `FAULT_RECORDED` | A firmware exception/fault record is present; inspect exception number and CFSR/HFSR/address validity bits |
| `NO_PROGRESS_OBSERVED` | No main-loop progress in these records; this alone does not identify a dead MCU |
| `INCOMPLETE` | Image/readback, chronology, receipt, timeout or cleanup evidence is incomplete |

Reports retain capture errors, cleanup failures, PID/exit/timeout details and
unreaped-worker instructions. Any incomplete capture has `progress: null`,
including cleanup failures, missing receipts, timeouts and clock inconsistency.
Decoded records and their reported sensor states/counters remain visible as
saved observations; they are not a capture-level progress verdict. Paired
identity validation still applies. Transport failure is never automatically a
PCB defect.

The retained IMU fields from v2 add U4 sensor state, current/history errors, sample count and
nominal age, raw native-axis values, endpoint/validity masks, configuration
readback and bus/retry details. Stale raw values remain visible with effective
validity zero. Main-loop progress is separate from reported sensor acquisition
progress. Core FAULT records withhold interrupted IMU state. Historical ABI v1
reports explicitly say that no IMU fields exist; it cannot be paired with v2.
ABI v3 also reports U5 PROM CRC4, candidate/last-good D1/D2, their calibration
banks, compensated pressure/temperature, acquisition age and message/retry
history. The host independently recomputes compensation and suppresses expired
data. Record size and ABI must match the image; adjacent words remain blocked.
ABI4 adds full raw/last-good voltage observations, per-channel times,
configuration and calibration, nominal conversions, state/error/cleanup history
and last native ADC register observations. Current errors or expired data keep
history visible without reporting acquisition progress. Freshness is at record
publication, not at replay time. The host independently checks the nominal math;
it does not assess electrical rail health or establish measurement accuracy.
Historical capture requests retain their original source-set shape for replay;
new capture requests bind the voltage decoder too.
A successful decode or a reported fresh sample is not physical calibration,
sensor identity authentication or a sensor/board qualification.

Hardware qualification, physical board identity, reset continuity and fabrication
release remain false. UID identifies the MCU, not its assembly; unsigned local
manifests/receipts are not cryptographic attestation. Sensors, rails, power loads,
connectors, actuators, environmental endurance and flight behaviour are untested.

## Address boundary

The dedicated guard allows fixed AP configuration, identity/status registers,
the exact internal-image window (at most64KiB), then only its image/ABI-bound
mailbox:1024 bytes for v4,512 for historical v3,256 for v1/v2. The default grant
remains v1/256 bytes. A size from a different ABI is rejected and revokes RAM
access. For v4,0x240003FC is the last permitted word;0x24000400 remains blocked.
The larger grant is explicit after matching the image and its validated
version/size contract; it does not enable the legacy generic RAM or mapped QSPI
permissions. Startup ECC initialization covers the exact linked record range. Target-memory data writes,
GPIO/reset/debug-control addresses, unaligned addresses and adjacent words are
blocked. Each DRW read consumes its validated TAR so auto-increment cannot fetch
an unchecked second word. Failed revalidation revokes previous grants.

The pinned pyOCD `MinimalMemAP.read32` source writes TAR then reads one word.
CSW/TAR/DRW behaviour follows the [Arm Debug Interface specification](https://documentation-service.arm.com/static/5f900a61f86e16515cdc0610).
ST supply/SRAM references are in the bootstrap README. Fake-AP and scripted C
tests are software evidence, not real-probe qualification.
