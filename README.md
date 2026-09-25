# Rocket Flight Computer (M3 single board)

Flight computer for an amateur high-power rocket: 2S LiPo, STM32H743VIT6, IMU (ICM-45686), barometer (MS5611), GNSS (SAM-M10Q), QSPI flight log, USB and a RunCam camera interface. The goal is **one 46 mm-wide, four-layer board that fits a 54.66 mm ID airframe**, including dual pyro channels and four-servo roll control.

> **Current status: M3-ASSY-R1 is a bench candidate, not flight hardware.** Power / MCU / sensors / logging / USB / GNSS / camera are routed on one 46 × 186 mm four-layer board with DRC, ERC and schematic parity all at zero. **The servo drive, pyro channels + arming break, pull-pin and buzzer are not merged yet**, and nothing has been measured on real hardware. Full requirements and gaps: [STATUS.md](STATUS.md).

## Layout

| Path | Contents |
|---|---|
| `m3_design/assembly_review/` | **The current KiCad project (the single source of truth)**: `m3.kicad_pro`, ten schematic sheets, PCB, project-local footprints, symbols and 3D models, and the review notes `ASSEMBLY_REVIEW.md` |
| `reference/m1_power_actuator/` | The legacy M1 power + actuator board (pyro, arming, servos, buzzer) — **the reference design still to be merged into M3**; the `PARTS` table and `build_nets()` in `m1.py` are its netlist |
| `docs/` | Design rationale: frozen design and BOM, circuit review, FMEA, margin prescription, airframe geometry, automated test design, simulation, design history |
| `m3_firmware/` | Bench diagnostic firmware v0.8.1 source, binding / protocol definitions and tests; `build_assembly_*/` holds prebuilt images for the current board |
| `diagnostics/` | Host-side diagnostic and fault-localisation tools (USB, SWD, log recovery, test-point map) |
| `quality_audit/` | Board-level audit: metadata conflicts, 3D model paths, DRC / ERC evidence |
| `tools/check.sh` | One-command board gate |

## Quick start

Requires **KiCad 10.0.x** (file format 20260206; older versions cannot open it) and Python 3.9+.

```bash
tools/check.sh                                     # DRC + ERC + parity + metadata/3D audit; passes only at zero
open m3_design/assembly_review/m3.kicad_pro        # open in KiCad
pip install -r diagnostics/requirements-lock.txt   # host diagnostic dependencies (pyocd etc.)
python3 -m unittest discover -s diagnostics -t . -p 'test_*.py'
(cd m3_firmware && PYTHONPATH=.. python3 -m unittest test_firmware test_gnss test_usb)
```

Building the firmware needs the ARM GNU Toolchain 15.2.rel1 unpacked into `m3_firmware/toolchain/` (see the `TOOL` path at the top of `m3_firmware/build.py`). **After any PCB change, `build.py` refuses to build until the pin binding has been reviewed again** — this is intentional.

## Collaboration

See [AGENTS.md](AGENTS.md): development rules, safety constraints, what remains for the complete PCB, and the contribution workflow.
