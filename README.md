# Rocket Flight Computer (M3, design only)

> **This checkout contains the latest M3-ASSY-R10 CAD candidate, merged with the local MIT review history. No board has been built, powered or flown.** R10 has not been accepted for ordering. R9 remains the previously accepted candidate on `m3-assy-r9`; its package must be obtained from that branch.

The current project is one **46 × 90 mm, four-layer PCB**. It uses an STM32H743, an ISM6HG256X IMU, an MS5611 barometer, QSPI flash and microSD, USB, camera power/UART and external GPS/radio/AUX ports. Read the current requirements and limitations in [STATUS.md](STATUS.md), the R10 design record in [docs/M3_R10.md](docs/M3_R10.md), and the unresolved acceptance items in [docs/R10_VALIDATION.md](docs/R10_VALIDATION.md).

R10's board and fabrication files are in `m3_design/assembly_review/`. R8/R9 used on-board RF; **R10 uses external GPS and radio modules**. The R2 portfolio images in `docs/images/` show the historical board, not R10. Current visual review files are in `m3_design/assembly_review/`.

**Firmware and diagnostics:** the existing v0.8.1 images and host tools remain bound to the archived R1 board. No R10 firmware is implemented or validated. Do not flash R1 images onto R10 or treat old tests as R10 hardware results.

The local `mit-review` commits, tool-specific credits, third-party notices and removal of three copied datasheet-page images are preserved. The Git merge changes project documentation and repository history; it does not edit R10 copper, components, schematics, fabrication files or firmware. See [docs/INTEGRATION_2026-11-02.md](docs/INTEGRATION_2026-11-02.md) for the merge inputs and checks.

## Open and check

Requires KiCad 10.0.x and Python 3.9+. For the numerical tests, set `NUMPY_PY` to a Python environment where `python -I -c "import numpy"` works. A NumPy installation only in the user site is ignored by isolated mode. Open `m3_design/assembly_review/m3.kicad_pro` in KiCad, or open the adjacent `m3.kicad_pcb` in PCB Editor.

```bash
tools/check.sh
```

This runs native DRC/ERC and schematic parity, schematic regeneration, model/metadata and fit checks, routing checks, fabrication-package binding/content checks, and the gates' negative tests. The integration also checks that KiCad 10.0.6 and 10.0.7 exporter metadata does not cause a false mismatch. All other netlist bytes and all schematic/DRU bytes remain checked.

## Project files

| Path | Contents |
|---|---|
| `m3_design/assembly_review/` | Current R10 PCB, schematic sheets, libraries, 3D models and bound `fab/` package |
| `m3_design/assembly_review/sources/r10_design/` | R10 decisions, pin table, binding note and review evidence |
| `m3_design/r10_build.sh`, `m3_design/r10_fab.sh` | R10 rebuild and package-export entry points |
| `docs/M3_R10.md`, `docs/R10_VALIDATION.md` | Design record, qualification limits and owner acceptance items |
| `docs/ORDERING.md`, `docs/R10_VEHICLE_HANDOFF.md` | R10 assembly and vehicle handoff records |
| `m3_firmware/`, `diagnostics/` | Historical R1-bound bench firmware and host tools, not R10 firmware |
| `reference/` | Historical M1 and M3-ASSY-R1 boards |
| `STATUS.md`, `AGENTS.md` | Requirements, evidence boundaries and collaboration rules |
| `THIRD_PARTY_NOTICES.md` | Retained local third-party licence and attribution notices |

## Collaboration

Work on a separate branch and review the result before updating a shared branch. The R9 and R8 branches remain historical candidates with their own packages. R2 images, simulations and test counts apply only to that historical revision. See [AGENTS.md](AGENTS.md) for the repository rules.

## Credits

**Jerry Wu (Jiarui Wu):** the project and its requirements: one board that fits the 54.66 mm airframe, built-in USB diagnostics, at most three PCB iterations. I chose to merge the two earlier boards into one, set the system constraints, made the design decisions recorded as "owner rulings" (for example two independently fused parachute channels, and keeping the backup altimeter fully separate), and reviewed the layout, flagging routing problems such as unwanted zigzag traces.

**AI coding assistants:** they produced most of the schematics, PCB layout, simulations, firmware and scripts from my requirements and decisions.
- **Claude Code** wrote the design documents, drew the first schematics through the EasyEDA API, wrote the KiCad board, routing and check scripts, and ran the ngspice simulations. It proposed and chose the 2 Ω per-channel pulse resistors used in R2; I approved them. It also merged pull requests #1–#5 on my account, so those merge commits show my name.
- **Codex** did the quality audit, the single-board versions up to M3-ASSY-R1, the bench firmware v0.1–v0.8.1 and the USB diagnostic tools.
- Commits made with Claude Code carry a `Co-Authored-By: Claude` line. `AGENTS.md` (read by Codex, and by Claude Code through `CLAUDE.md`) holds the safety and routing rules they had to follow.

**Collaborator and existing work:**
- **Ethan Huang** (collaborator) merged the four servo outputs, the two fused parachute channels with the arming break, the pull-pin and the buzzer into the board (pull request #1, 26 Sep 2026), also with Claude Code. He committed the later R3–R10 branches.
- **Open-source code and models:** TinyUSB (MIT), STM32CubeH7 HAL (BSD-3-Clause) and CMSIS headers (Apache-2.0) in `m3_firmware/vendor/`; KiCad library 3D models (CC-BY-SA 4.0 with exception); footprints and 3D models converted from the EasyEDA/LCSC library with easyeda2kicad. Details and licences: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- **Tools:** KiCad 10, ngspice, Python, Arm GNU Toolchain; part data from maker datasheets and LCSC/JLCPCB pages (linked in the review notes, not copied).
