# R10 read-only register diagnostics

For the separate installed-image and RAM-record path, see
[R10 firmware readback](R10_FIRMWARE.md). This command's register-only permissions
remain unchanged.

This host workflow reads a fixed set of STM32H743 identity, reset-history,
clock-state and CPU fault registers over SWD. It needs no R10 application image.
It does not install firmware, halt/reset the core, initialize GPIO/peripherals,
or perform sensor, memory, communications or output tests. The R1 firmware and
its USB/mailbox bindings remain incompatible with R10.

**Development verification uses fake readers only. No physical R10 connection
has been tested.** Register reads cannot qualify a board or verify firmware.
SWD itself writes debug-port/AP configuration and requests debug/system power,
so this is not a zero-disturbance observation of a running system.

## R10 connection identity

`--board` is mandatory and must match the saved R10 PCB bytes. The separately
pinned SWD binding is checked against all six native J2 pads by the project
gate, alongside the 33 offline diagnostic points. Coordinates use PCB top
projection in millimetres; bottom pads are not mirrored.

| R10 J2 pad | Signal | Use |
|---|---|---|
| 1 | 3V3 | Target voltage reference to the probe; not a second supply input |
| 2 | SWDIO | Debug data |
| 3 | NRST | Not commanded by this workflow |
| 4 | SWCLK | Debug clock |
| 5 | GND | Probe ground |
| 6 | NC | Not connected on this PCB; do not assume an SWO connection |

The R10 J2 map differs from the old R1 header. The native board is authoritative;
the [Tag-Connect ARM20-CTX sheet](https://www.tag-connect.com/wp-content/uploads/bsk-pdf-manager/ARM20-CTX_19.pdf)
provides the corresponding standard SWD contact roles, with pad 6 deliberately
unused here. Verify the actual probe/adapter by signal name. The tool does not
supply power or test the physical wiring.

## Capture and saved reports

Use Python 3.9+ on macOS/Linux. Capture requires the project's pinned pyOCD
0.45.1 environment; saved reports and wiring output use the standard library.
Run from the project root:

```sh
python3 -m venv diagnostics/.venv
diagnostics/.venv/bin/python -m pip install -r diagnostics/requirements-lock.txt
diagnostics/.venv/bin/python -m diagnostics probes

# Read the native R10 connection map without opening a probe:
python3 -m diagnostics.r10_swd wiring --board m3_design/assembly_review/m3.kicad_pcb

# Replace EXACT_ID and BOARD_001 with the actual probe and assembly identifiers.
diagnostics/.venv/bin/python -m diagnostics.r10_swd capture \
  --board m3_design/assembly_review/m3.kicad_pcb --probe-id EXACT_ID \
  --assembly-id BOARD_001 --bench-isolated --out diagnostics/runs/board001_swd
```

Capture is for an isolated bench setup with deployment and actuator loads
disconnected. `--bench-isolated` records the operator's declaration; software
cannot verify disconnection. There is no automatic probe selection, erase,
unlock, reset, halt or recovery fallback. The transport uses the existing
DP/AP-only guard, not normal target initialization. Its connection policy is
based on the pinned implementation and [pyOCD session options](https://pyocd.io/docs/options.html).

Each run gets a new directory containing:

- `request.json`: assembly, exact probe ID, PCB/binding identity and acquisition
  source-file hashes. Source drift before worker startup is rejected.
- `snapshot.json`: original register values and individual read errors, saved
  incrementally. Wrong chip identity stops family-specific reads.
- `execution.json`: worker completion and snapshot byte hash, if it finished.
- `supervision.json` and `driver.log`: process outcome and timeout evidence.
- `analysis/report.json` and `report.md`: findings, missing evidence and correct
  R10 connector locations. A complete register capture is not a board PASS.

Driver work is bounded to 25 seconds, then a 3-second terminate grace and a
3-second kill grace. Partial snapshots are never rewritten as empty data or
successful completion. If the OS still cannot reap the worker, its PID and
unknown exit are recorded explicitly; capture is incomplete.

Repeat analysis into a **new** output directory:

```sh
python3 -m diagnostics.r10_swd report --run diagnostics/runs/board001_swd \
  --board m3_design/assembly_review/m3.kicad_pcb --out diagnostics/runs/board001_report2
```

Exit 0 means the capture/report operation completed, not that the board passed;
2 indicates a reported issue and can still include partial evidence; 3 indicates
incomplete capture or an input/tool error. Inspect `complete_register_capture`
and individual checks. Raw evidence and old report directories are never
overwritten. Keep assembly UIDs/probe IDs in private run directories.

A successful terminal snapshot requires a known finish time, no capture error,
all allowlisted reads, matching driver/source metadata and its address trace.
Contradictory synthetic/live labels are rejected. Inconsistent or future host
timestamps make the capture incomplete, retaining the raw observations; they
do not imply a power or MCU fault.

## Pair instrument measurements with the same capture

```sh
python3 -m diagnostics.r10_swd bench-template --run diagnostics/runs/board001_swd \
  --board m3_design/assembly_review/m3.kicad_pcb --out diagnostics/runs/board001_meter.json
# Fill the template with actual instrument records and the actual steady window.
python3 -m diagnostics.r10_swd report --run diagnostics/runs/board001_swd \
  --board m3_design/assembly_review/m3.kicad_pcb \
  --manual diagnostics/runs/board001_meter.json --out diagnostics/runs/board001_combined
```

The template fills provenance only, including the capture's assembly/session
and epoch; measurements remain empty and source state remains unknown. Follow
the [offline record format](R10_OFFLINE.md). The declared steady window must
cover both the capture and the individual voltage readings. A known coherent
capture end is required; interrupted captures with no end can be inspected as
raw data but cannot establish a paired instrument window. Pairing rejects
different assemblies, sessions, epochs or windows. The declaration does not
prove the physical configuration stayed unchanged. The report keeps instrument
records, uncertainty and their source byte hash separate from SWD observations.

Software tests exercise disconnection, wrong identity, partial/timeout/cleanup
failures, immutable evidence, wrong bindings, source drift, process isolation,
forbidden addresses and cross-session pairing. They do not prove electrical
behaviour, physical probe clearance, exact part authenticity or flight reliability.
