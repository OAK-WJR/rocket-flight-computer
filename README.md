# Rocket Flight Computer (M3 single board)

Flight computer for an amateur high-power rocket: 2S LiPo, STM32H743VIT6, IMU (LSM6DSV320X), barometer (MS5611), QSPI flight log, USB, a RunCam camera interface, an on-board GNSS (u-blox MAX-F10S) and LoRa radio (EBYTE E22-900MM22S), four roll-control servos and one recovery pyro channel with a complete arming break (the backup is an isolated commercial altimeter). The goal is **one 46 mm-wide, four-layer board that fits the main-section bay** (it fits the Ø50.8 mm coupler bore along its whole length; REQUIREMENTS P1/P2).

> **Current status: M3-ASSY-R8 is the current CAD candidate; M3-ASSY-R7 (owner-accepted 2026-10-18) is the orderable fallback.** R8 is R7's circuit (one pyro channel, 46 × 118 mm, fifteen schematic sheets, BOM identical to R7's) re-placed and re-routed around R7's rigid RF strip and pyro block, built reproducibly by `m3_design/r8_build.sh` from the committed R7; independent review passes 2, 3 and 4 found no Critical or Major (its plan's review loop; pass 4 on fix pass 3's board `c84f00b8…`: 0 Critical, 0 Major, 16 Minor); fix pass 4 applied pass 4's two copper Minors, and review pass 5 re-checked its board `cc044ea0…` in build integrity, planes and routing (0 Critical, 0 Major, 3 Minor; the other five dimensions not re-run on it); the owner accepted R8's deviation list on 2026-10-20; still open: U4 consigned, JLC's tab acceptance and a cost and stock run within 24 h. Neither board has been built or measured, and no firmware exists for R2–R8 (the R1-bound v0.8.1 must not run on them). Status, what was verified and the open items: [STATUS.md](STATUS.md); the R8 design record: [docs/M3_R8.md](docs/M3_R8.md); validation and the deviation list: [docs/R8_VALIDATION.md](docs/R8_VALIDATION.md).

## Layout

| Path | Contents |
|---|---|
| `m3_design/assembly_review/` | **The current KiCad project (the single source of truth)**: `m3.kicad_pro`, fifteen schematic sheets, PCB, project-local footprints, symbols and 3D models, the fab package (`fab/`) and the R8 design sources (`sources/r8_design/`: plan, decisions, pin table, step handoffs) |
| `m3_design/r8_*.py`, `r8_*.tsv`, `r8_build.sh`, `r8_fab.sh` | The R8 build: schematic pin map, placement table and legaliser, power, nine signal-family modules, ground table, silkscreen, each with its gate; `r8_fab.sh` makes and checks the fab package. Older `r4_`–`r7_` scripts are the earlier revisions' builds |
| `m3_design/sim_r2/` | ngspice suite for the R2 actuator band (`run.py`, `RESULTS.md`, `FINDINGS.md`) |
| `reference/` | `m1_power_actuator/`: the legacy M1 actuator board R2 was merged from; `m3_assy_r1/`: the R1 board the v0.8.1 firmware and `diagnostics/` are still bound to |
| `docs/` | Requirements (`REQUIREMENTS.md`), R8 design record (`M3_R8.md`) and validation (`R8_VALIDATION.md`), ordering guide (`ORDERING.md`, R8's), the earlier revisions' records (`M3_R4.md` … `M3_R7.md`, `R7_VALIDATION.md`), design rationale: frozen design and BOM, circuit review, FMEA, margin prescription, airframe geometry, simulation, design history |
| `m3_firmware/` | Bench diagnostic firmware v0.8.1 source, binding / protocol definitions and tests; `build_assembly_*/` holds prebuilt images **for R1 only — do not run them on R2–R8** |
| `diagnostics/` | Host-side diagnostic and fault-localisation tools (USB, SWD, log recovery, test-point map) |
| `quality_audit/` | Board-level audit: metadata conflicts, 3D model paths, DRC / ERC evidence |
| `tools/check.sh` | One-command board gate (DRC, ERC, parity, audit, `check_r8`, `route_check`, actuator contract, fit) |

## Quick start

Requires **KiCad 10.0.x** (file format 20260206; older versions cannot open it) and Python 3.9+.

```bash
tools/check.sh                                     # the board gate; passes only at zero
m3_design/r8_build.sh                              # rebuild R8 from the committed R7, byte for byte (about 10 min)
python3 m3_design/check_actuators.py               # pyro / arming / servo safety contract
python3 m3_design/sim_r2/run.py                    # SPICE suite (needs ngspice)
open m3_design/assembly_review/m3.kicad_pro        # open in KiCad
pip install -r diagnostics/requirements-lock.txt   # host diagnostic dependencies (pyocd etc.)
python3 -m unittest discover -s diagnostics -t . -p 'test_*.py'
(cd m3_firmware && PYTHONPATH=.. python3 -m unittest test_firmware test_gnss test_usb)
```

Building the firmware needs the ARM GNU Toolchain 15.2.rel1 unpacked into `m3_firmware/toolchain/` (see the `TOOL` path at the top of `m3_firmware/build.py`). **After any PCB change, `build.py` refuses to build until the pin binding has been reviewed again** — this is intentional.

## Collaboration

See [AGENTS.md](AGENTS.md): development rules, safety constraints, what remains for the complete PCB, and the contribution workflow.
