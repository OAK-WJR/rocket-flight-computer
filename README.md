# Rocket Flight Computer (M3 single board)

Flight computer for an amateur high-power rocket: 2S LiPo, STM32H743VIT6, IMU (LSM6DSV320X), barometer (MS5611), QSPI flight log, USB and a RunCam camera interface. The goal is **one 46 mm-wide, four-layer board that fits the main-section bay** (Ø54.6 mm bore; its aft ~70 mm sits inside the Ø50.8 mm coupler), including dual pyro channels and four-servo roll control.

> **Current status: M3-ASSY-R4 is the complete-function CAD candidate, not flight hardware.** Power / MCU / sensors / logging / USB / camera **plus** the actuator switch, four servos, two independently fused pyro channels with a complete arming break, pull-pin and buzzer are routed on one 46 × 193 mm four-layer board. R4 answers the R3 validation ([docs/R3_VALIDATION.md](docs/R3_VALIDATION.md)) and a first-principles evaluation against [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md): new IMU (ST LSM6DSV320X, ±320 g channel), 3S-proof input TVS, a reverse hot-plug damper and input bleed, black ARM / orange igniter terminals, pyro spacing rules enforced by DRC, continuous In2 servo feed, MEMS keep-outs, JLC placement corrections, single-fault-tolerant sense dividers with series resistors at the ADC pins ([docs/M3_R4.md](docs/M3_R4.md)); twelve independent evaluation passes. DRC, ERC and schematic parity are zero and the actuator safety contract passes. Nothing has been built or measured, and no firmware exists for R4 (the R1-bound v0.8.1 must not run on it). Full requirements and gaps: [STATUS.md](STATUS.md).

## Layout

| Path | Contents |
|---|---|
| `m3_design/assembly_review/` | **The current KiCad project (the single source of truth)**: `m3.kicad_pro`, fourteen schematic sheets, PCB, project-local footprints, symbols and 3D models, and the review notes `ASSEMBLY_REVIEW.md` |
| `m3_design/r4_*.py` | The scripts that generate R4 from the R3 files (footprints, schematic, board); every edit's reason is in their docstrings |
| `m3_design/sim_r2/` | ngspice suite for the R2 actuator band (`run.py`, `RESULTS.md`, `FINDINGS.md`) |
| `reference/` | `m1_power_actuator/`: the legacy M1 actuator board R2 was merged from; `m3_assy_r1/`: the R1 board the v0.8.1 firmware and `diagnostics/` are still bound to |
| `docs/` | Requirements (`REQUIREMENTS.md`), R4 design record (`M3_R4.md`), ordering guide (`ORDERING.md`), R3 validation (`R3_VALIDATION.md`), verification record (`R2_VERIFICATION.md`), actuator merge record (`M3_ACTUATOR_MERGE.md`), design rationale: frozen design and BOM, circuit review, FMEA, margin prescription, airframe geometry, automated test design, simulation, design history |
| `m3_firmware/` | Bench diagnostic firmware v0.8.1 source, binding / protocol definitions and tests; `build_assembly_*/` holds prebuilt images **for R1 only — do not run them on R2** |
| `diagnostics/` | Host-side diagnostic and fault-localisation tools (USB, SWD, log recovery, test-point map) |
| `quality_audit/` | Board-level audit: metadata conflicts, 3D model paths, DRC / ERC evidence |
| `tools/check.sh` | One-command board gate |

## Quick start

Requires **KiCad 10.0.x** (file format 20260206; older versions cannot open it) and Python 3.9+.

```bash
tools/check.sh                                     # DRC + ERC + parity + metadata/3D audit; passes only at zero
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
