# Collaboration and AI development guide

This file is for anyone — person or AI coding assistant — picking up this repository on any account. (Claude Code reads `CLAUDE.md`, which points here; Codex and others read this file directly.)

## 1. Goal: one complete PCB

The deliverable is **one** board (the M1/M2 two-board scheme was abandoned; see `docs/HISTORY.md`) with every function in the original requirements:

| Block | Current M3-ASSY-R1 | Reference |
|---|---|---|
| 2S battery input, switch, reverse / over-voltage / current limit, logic hold-up | ✅ Routed (U9 / U10 / U11) | `STATUS.md` |
| STM32H743, 25 MHz HSE, SWD, USB-C | ✅ | `docs/ROCKET_FC_FROZEN_DESIGN.md` |
| IMU, barometer, QSPI log, GNSS | ✅ | Same |
| Camera 4-position terminal (power / GND / UART × 2) | ✅ | `STATUS.md` |
| **Four servos (3×4 header, series resistors, pull-downs, SRV05-4 clamp)** | ❌ Not merged | `reference/m1_power_actuator/m1.py`, `docs/MARGIN_PRESCRIPTION.md` §8.2 |
| **Dual pyro + complete arming break + continuity sensing** | ❌ Not merged | Same + `docs/FMEA_REDUNDANCY.md`, `docs/CIRCUIT_REVIEW.md` |
| **Pull-pin (launch detect), buzzer** | ❌ Not merged | Same |
| Interface and common-cause isolation for the independent backup altimeter | ❌ Undecided | `STATUS.md` |
| Mounting holes / sled / zip-tie holes, final board length | ❌ Not frozen (186 mm is provisional) | `docs/GEOMETRY_REV_G.md` |
| Manufacturing package (BOM / CPL / Gerber) and quote | ❌ | — |

## 2. Safety constraints that must never be violated

1. **The arming (ARM) plug must be a complete electrical break in the pyro bus.** No copper, part or test point may bypass it.
2. The ARM plug goes in last and comes out first; the pyro bus is taken after the load switch (RAW), never straight from the battery.
3. In flight, continuity / ARM_SENSE readings are only logged and annunciated and **never veto a fire**; on the ground they are hard refusals (`docs/FMEA_REDUNDANCY.md` F-10).
4. Pyro FET gates must have a pull-down, a series resistor and a gate-source capacitor, and must be defined off while the MCU is in reset or unpowered.
5. An inference that has not been measured or checked against the original datasheet must be labelled as an inference, never written as fact.

## 3. Development rules

- **The KiCad project is the single source of truth**: edit the schematic and PCB directly in `m3_design/assembly_review/`, keeping them in sync ("Update PCB from Schematic").
- **Verify, don't guess**: package dimensions, lands, pinouts and electrical parameters always come from the maker's datasheet or the LCSC / JLCPCB page, with the source URL written into the review notes.
- New footprints go in `kilib/rocket.pretty`, 3D models in `kilib/rocket.3dshapes`, referenced as `${KIPRJMOD}/kilib/...`; **absolute paths are forbidden**.
- Every part's `LCSC` / `Manufacturer` / `Manufacturer Part` fields must agree, with no second, contradictory part-number field (`quality_audit` rejects it).
- Routing: hand-route critical nets (power, pyro, crystal, USB, SPI/QSPI); use only 0° / 45° / 90° straight segments with no staircases, acute angles or stubs; add ground vias next to layer changes; size high-current copper per IPC-2152.
- Silkscreen: reference designators legible (≥ 0.8 mm text), never over pads or off the board edge; only designators on silkscreen, part numbers hidden on F.Fab.
- **`tools/check.sh` must pass at zero before every commit**; put its output in the pull-request description.
- After a board change, update the matching row of `STATUS.md`, stating clearly what was verified and what was not (software tests, DRC, simulation and physical tests must be reported separately).
- A PCB change invalidates the board hash binding in `m3_firmware/build.py`; create a new binding for the new revision based on `m3_firmware/assembly_binding.py` and review the pin table, rather than editing the hash to get around it.

## 4. Workflow and communication

- One branch per piece of work → pull request → reviewed by the other side before merging. Do not push directly to `main`.
- Discussions, questions and decisions go in **GitHub Issues / PR comments** so both sides always get notified; once merged, decisions are also written into the relevant document.
- Large files (datasheet PDFs, build intermediates, toolchains, render history) stay out of the repository; see `.gitignore`. Review notes link to datasheets instead.
- Never commit personal information, accounts, tokens or local absolute paths.

## 5. Common commands

```bash
tools/check.sh                                   # board gate
KICAD_CLI=/path/to/kicad-cli tools/check.sh      # specify kicad-cli on non-macOS systems
kicad-cli pcb render --side top -o top.png m3_design/assembly_review/m3.kicad_pcb
kicad-cli pcb export gerbers -o gerber/ m3_design/assembly_review/m3.kicad_pcb
```
