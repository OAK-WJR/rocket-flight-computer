# M3 bench triage entry point

The current PCB is **M3-ASSY-R1**, with firmware `build_assembly_*` / v0.8.1. This entry point links the USB snapshot, fault history and external DC measurements to the current PCB's test points and gives a troubleshooting order from power to communication. It cannot uniquely identify a broken chip, and it does not represent full rocket function, real-board reliability or manufacturing release.

Board SHA-256: `e432d3436d5029de0a74a4b0ebcd02ec092dedf6d4252ce310f7be301558627f`. This tool changed none of the CAD, copper or the four firmware binaries.

## One capture

First install the reviewed diagnostic image on the board separately. The command below only reads snapshots; it never installs firmware or controls power. (No real board has been connected yet.)

From the project root, with the real serial port, the physical board ID and a new output directory:

```sh
diagnostics/.venv/bin/python -m diagnostics.triage capture \
  --port /dev/cu.REPLACE_WITH_ACTUAL_PORT \
  --assembly BOARD_001 \
  --out diagnostics/runs/BOARD_001_first
```

By default it binds to `m3_firmware/build_assembly_inspect/manifest.json` and `m3_design/assembly_review/m3.kicad_pcb`, taking two snapshots 1.2 s apart. `--manifest` selects another exactly matching assembly image; `--samples 2..30` and `--interval 1.2..10` adjust acquisition. Each request has a bounded deadline with no automatic retry. Uses the pinned `pyserial==3.5`; offline `report` needs no serial driver.

Outputs:

| File | Purpose |
|---|---|
| `report.html` | Browsable report: branch troubleshooting order, test-point map, evidence for every judgement |
| `capture.json` | Raw sent / received bytes, accepted records, errors, partially received bytes and identities |
| `report.json` | Automated results, on-board measurements and fault history, external instrument records, input hashes |
| `probe_map.json` / `board.svg` | The 30 pad positions and nets read back from the saved PCB |
| `bench_template.json` | An instrument record template for the 25 non-ground nets of this capture; every measurement starts `null` |

A report is still saved with no serial port, no image installed or an interrupted connection. **Reading no data never counts as a pass.** Exit code 0 means a complete liveness snapshot report was produced, 2 means the report contains an explicit FAIL, 3 means incomplete capture / input or tool error; no exit code means the board passed.

## Reading the test-point map

The map shows the component side (TOP), x to the right, y down, in mm — not a mirrored bottom view. The 20 dedicated test pads and 10 power / reset / reference pads are all parsed from the saved board and cross-checked one by one against KiCad's native `PAD.GetPosition()` and net names. Numbers match the coordinate table in the report; click a number to jump to its row, hover to see the net.

The map draws only pads and part centres, not footprint outlines or routing. Prefer the dedicated test pads; component pads need a suitable fine probe without bridging. Each row gives its reference ground and coordinates. Independent instrument readings and on-board ADC readings are stored separately: the ADC's own reference cannot prove its own supply is accurate.

If USB will not connect, look first at USB input / current limit, source selection, 3V3, reset and the data branch. Fault history showing a FAULT on a protection branch does not mean that protection chip is broken. An input pin that is currently normal does not clear an earlier abnormality. ST high can mean USB input or a high-impedance output, and cannot alone be taken as healthy power.

## Adding measurements

Copy `bench_template.json` to `meter.json`, keep the board ID, assembly ID, capture_id, TOP coordinates and reference grounds unchanged, and fill `measurement` only after actually measuring. Also fill `supply_configuration` (actual supply / switch / camera state), confirm paired readings were taken in the same stable configuration, and set `same_supply_configuration: true`. Leave unmeasured items empty.

Measurement fields are `value`, `unit: "V"`, `uncertainty_v`, `input_ohm`, `instrument` and a time-zoned `measured_at`. The uncertainty must include instrument specification, resolution and method; never use 0 for an unknown error. Every non-empty value in the example reports is explicitly marked synthetic and must not be copied as physical acceptance.

```sh
diagnostics/.venv/bin/python -m diagnostics.triage report \
  diagnostics/runs/BOARD_001_first/capture.json \
  --bench diagnostics/runs/BOARD_001_first/meter.json \
  --out diagnostics/runs/BOARD_001_with_meter
```

The new report keeps a byte-for-byte copy of the original `capture.json` and `bench_input.json`, and checks nets, pads, coordinates, reference grounds, versions and sessions. Synthetic and physical sources must never be mixed. The automatic DC criteria only reuse the existing 3V3 / 3V3A screening, the three-level severe-drop check and the two divider checks; new test points are observation positions only and add no PASS thresholds. Transients, ripple, temperature rise and pressure / inertial accuracy cannot be inferred from DC readings.

## Verification and boundaries

`test_triage.py` covers wrong nets, native coordinates, old bindings, wrong binaries, disconnection / partial frames / CRC, stale heartbeats, FAULTs after recovery, upstream-power-first troubleshooting, instrument error bounds, mixing versions / sessions / sources, wrong reference grounds, HTML escaping and overwrite protection.

This entry point only sends the existing snapshot operation (op 1, address 0, length 1024). It never erases flash, clears history, resets, or switches the camera or power; logging or camera-query behaviour depends on the image installed beforehand. For log export keep using the verified `diagnostics.usb dump`; erasing is never a troubleshooting step. Full list of missing functions: [STATUS.md](../STATUS.md).
