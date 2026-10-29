# Rocket Flight Computer (M3 single board)

Flight computer for an amateur high-power rocket: 2S LiPo, STM32H743VIT6, IMU (LSM6DSV320X), barometer (MS5611), QSPI flight log, USB, a RunCam camera interface, an on-board GNSS (u-blox MAX-F10S) and LoRa radio (EBYTE E22-900MM22S), four roll-control servos and one recovery pyro channel with a complete arming break (the backup is an isolated commercial altimeter). The goal is **one 46 mm-wide, four-layer board that fits the main-section bay** (it fits the Ø50.8 mm coupler bore along its whole length; REQUIREMENTS P1/P2).

> **Current status: M3-ASSY-R9 (owner-accepted 2026-10-25) is the current CAD candidate and the board to order; M3-ASSY-R8 (owner-accepted 2026-10-20) is the fallback.** R9 is R8's circuit (one pyro channel, fifteen schematic sheets, the BOM R8's line for line but three footprint fields) laid out again from a clean sheet at 46 × 102 mm (the B-spine: RF strip aft, the CH1 pyro column as a dead end on the west edge, all power in the east column), built reproducibly by `m3_design/r9_build.sh` from R8's committed sources and judged by a rule-based gate (`tools/check_r9.py`) in place of R8's hash-asserted copper; every safety and RF qualification was re-derived on the current board (`4f841a0e…`, made by review pass 1's fix pass; step 10's board was `fc3d5b34…`). Two consecutive independent review passes found no confirmed Critical or Major (pass 1's one Major was confirmed as Minor; pass 2: 0 Critical, 0 Major, 32 Minor, recorded), and the owner accepted R9's deviation list on 2026-10-25 with the board kept at 102 mm; before an order, U4 must be in JLC stock or consigned, JLC must accept the four panel tabs and the cost and stock run must be fresh ([docs/ORDERING.md](docs/ORDERING.md)). Neither board has been built or measured, and no firmware exists for R2–R9 (the R1-bound v0.8.1 must not run on them). Status, what was verified and the open items: [STATUS.md](STATUS.md); the R9 design record: [docs/M3_R9.md](docs/M3_R9.md); validation, requalification and the deviation list: [docs/R9_VALIDATION.md](docs/R9_VALIDATION.md); R8's: [docs/M3_R8.md](docs/M3_R8.md), [docs/R8_VALIDATION.md](docs/R8_VALIDATION.md).

> **On branch `m3-assy-r10` the project holds M3-ASSY-R10, a CAD candidate (review rounds in progress, see docs/R10_VALIDATION.md) that has not been accepted.** Here `m3_design/assembly_review/` and its `fab/` package (bound to the R10 board by `fab/m3_fab_manifest.json`) are R10's, not R9's: 46 × 90 mm, external GPS (J410) and radio (J420) ports in place of the on-board RF, servo power and return off the board (owner decisions O1–O6; [docs/M3_R10.md](docs/M3_R10.md), [docs/R10_VALIDATION.md](docs/R10_VALIDATION.md)). **Do not order the R10 package**: R9 stays the accepted board to order, with its package and records on `m3-assy-r9`. On this branch `tools/check.sh` runs the R10 gate (`tools/check_r10.py`, `route_check --profile r10`, `check_actuators --profile r10`, fit and plate model with profile r10), `m3_design/r10_build.sh` rebuilds R10 byte for byte (about 2.5 min), and `m3_design/r10_fab.sh` makes its package. No R10 firmware exists; its binding evidence is `m3_design/assembly_review/sources/r10_design/r10_binding_note.json` (never an approval).

## Layout

| Path | Contents |
|---|---|
| `m3_design/assembly_review/` | **The current KiCad project (the single source of truth)**: `m3.kicad_pro`, fifteen schematic sheets, PCB, project-local footprints, symbols and 3D models, the fab package (`fab/`, R9's; R10's on `m3-assy-r10`) and the design sources (`sources/r9_design/`: R9's plan, owner and agent decisions, step handoffs and evidence; `sources/r8_design/`: R8's, with the pin table R9 keeps) |
| `m3_design/r9_*.py`, `r9_*.tsv`, `r9_build.sh`, `r9_fab.sh` | The R9 build: schematic and footprint variants, design rules, placement table and legaliser, RF strip, pyro column, power, ten routing-family modules, ground table, silkscreen, each with its gate, then `tools/check.sh`; `r9_fab.sh` makes and checks the fab package. The `r8_` scripts are R8's build (its sources are R9's input) and the older `r4_`–`r7_` scripts the earlier revisions' |
| `m3_design/sim_r2/` | ngspice suite for the R2 actuator band (`run.py`, `RESULTS.md`, `FINDINGS.md`) |
| `reference/` | `m1_power_actuator/`: the legacy M1 actuator board R2 was merged from; `m3_assy_r1/`: the R1 board the v0.8.1 firmware and `diagnostics/` are still bound to |
| `docs/` | Requirements (`REQUIREMENTS.md`), R9 design record (`M3_R9.md`) and validation (`R9_VALIDATION.md`), ordering guide (`ORDERING.md`, R9's (R10's on `m3-assy-r10`); R8's is on `m3-assy-r8`), the earlier revisions' records (`M3_R4.md` … `M3_R8.md`, `R7_VALIDATION.md`, `R8_VALIDATION.md`), design rationale: frozen design and BOM, circuit review, FMEA, margin prescription, airframe geometry, simulation, design history |
| `m3_firmware/` | Bench diagnostic firmware v0.8.1 source, binding / protocol definitions and tests; `build_assembly_*/` holds prebuilt images **for R1 only — do not run them on R2–R9** |
| `diagnostics/` | Host-side diagnostic and fault-localisation tools (USB, SWD, log recovery, test-point map) |
| `quality_audit/` | Board-level audit: metadata conflicts, 3D model paths, DRC / ERC evidence |
| `tools/check.sh` | One-command board gate (DRC, ERC, parity, audit, fit, plate model, seeded rule-H suite, `check_r9`, `route_check` profile r9, actuator contract; set `NUMPY_PY` to a Python 3 with numpy for the plate model). **On `m3-assy-r10`:** the R10 gate instead (`check_r10`, `route_check` profile r10, `check_actuators --profile r10`; no rule-H suite) |

## Quick start

Requires **KiCad 10.0.x** (file format 20260206; older versions cannot open it) and Python 3.9+.

```bash
tools/check.sh                                     # the board gate; passes only at zero
NUMPY_PY=<python3 with numpy> m3_design/r9_build.sh # rebuild R9 from R8's committed sources, byte for byte (about 40 min)
NUMPY_PY=<python3 with numpy> m3_design/r10_build.sh # on m3-assy-r10: rebuild R10 from R9's pinned inputs, byte for byte (about 2.5 min)
python3 m3_design/check_actuators.py               # pyro / arming / servo safety contract
python3 m3_design/sim_r2/run.py                    # SPICE suite (needs ngspice)
open m3_design/assembly_review/m3.kicad_pro        # open in KiCad
pip install -r diagnostics/requirements-lock.txt   # host diagnostic dependencies (pyocd etc.)
python3 -m unittest discover -s diagnostics -t . -p 'test_*.py'
(cd m3_firmware && PYTHONPATH=.. python3 -m unittest test_firmware test_gnss test_usb)
```

Building the firmware needs the ARM GNU Toolchain 15.2.rel1 unpacked into `m3_firmware/toolchain/` (see the `TOOL` path at the top of `m3_firmware/build.py`). **After any PCB change, `build.py` refuses to build until the pin binding has been reviewed again** — this is intentional. No firmware exists for R2–R10; an R10 binding must be created from `m3_firmware/assembly_binding.py` with R10's pin table (`sources/r10_design/pin_table.tsv`) and binding note (AGENTS.md §3).

## Collaboration

See [AGENTS.md](AGENTS.md): development rules, safety constraints, what remains for the complete PCB, and the contribution workflow.
