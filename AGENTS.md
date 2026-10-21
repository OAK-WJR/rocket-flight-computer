# Collaboration and AI development guide

This file is for anyone — person or AI coding assistant — picking up this repository on any account. (Claude Code reads `CLAUDE.md`, which points here; Codex and others read this file directly.)

## 1. Goal: one complete PCB

The deliverable is **one** board (the M1/M2 two-board scheme was abandoned; see `docs/HISTORY.md`) with every function in the original requirements:

| Block | Current M3-ASSY-R8 (R7, owner-accepted, is the fallback) | Reference |
|---|---|---|
| 2S battery input, switch, reverse / over-voltage / current limit, logic hold-up | ✅ Routed (U9 / U10 / U11). R8: the input protection (D8, C80 / C96, the damper, R167) sits at J1, U9 27 mm away aft of J121 | `STATUS.md`; `docs/M3_R8.md` |
| STM32H743, 25 MHz HSE, SWD, USB-C | ✅ R8: U1 at rotation 0 with the QSPI flash and crystal under it; 27 pins re-assigned, each cited in `m3_design/assembly_review/sources/r8_design/pin_table.tsv`; SWD (TC2030 J2) and USB-C on the west edge | `docs/ROCKET_FC_FROZEN_DESIGN.md`; `docs/M3_R8.md` |
| IMU, barometer, QSPI log | ✅ R4: IMU is the ST LSM6DSV320X (±16 g + ±320 g, ±4000 dps; out of JLC stock in R7, consigned). R5: IMU and barometer on the bottom side (the IMU's Y and Z axes flip: roll is +gyro_Y, the opposite sign to R4; M3_R5 §3). R8: still bottom, rotation 0, so the axis map holds; U4 now sits 13 mm west of the roll axis, so the lever-arm sign flips (M3_R8) | `docs/M3_R5.md`; `docs/M3_R8.md`; `docs/M3_R4.md` |
| Camera connector (power / GND / UART × 2) | ✅ R6: keyed JST GH 4-pin J9. R8: the MCU side moves from the loader port USART3 to UART7 (PE8 TX, PE7 RX) | `docs/M3_R6.md`; `docs/M3_R8.md` |
| GNSS and telemetry radio on the board | ✅ R7, CAD only: u-blox MAX-F10S (U30) and EBYTE E22-900MM22S SX1262 radio (U31) on 3V3 in an aft RF strip, edge SMA jacks J30/J31, antenna-bias current limiter; the radio is held in reset by hardware while the MCU is in reset, and no radio or GNSS net touches pyro, arming or actuator copper. R8: the RF lines, strip parts and strip GND field (R8_DECISIONS D15's groups) are R7's, rigid and hash-asserted (`check_r8`; the interface leads, limiter DC copper, feeds and fence row are regenerated, D11); the radio on SPI2 (PB10 / PB11 / PB14 / PB15 with IOSWP), NRST PE9, DIO1 PE15, RXEN PD9; GNSS RESET_N PD14, TIMEPULSE PD15. RF bench tests not done; firmware binding open | `docs/M3_R7.md`; `docs/M3_R8.md`; REQUIREMENTS F10 |
| Actuator power switch (second, high-current battery path) | ✅ Routed in R2 (Q120/Q121 AON6403, gated by the logic path). R8: the FETs face each other beside J1; the 7.7 A necks are 5.94 / 6.99 / 4.97 mm, within R8_DECISIONS D12's rise limits, which the build now holds (D95) | `docs/M3_ACTUATOR_MERGE.md`; `docs/M3_R8.md` |
| Four servos (3×4 header, 1 k series, pull-downs, SRV05-4 clamp) | ✅ Routed in R2. R8: J122 unmoved; D121 on the bottom at J122, on the U1-ordered lanes | Same |
| Pyro + complete arming break + continuity sensing | ✅ R6: one recovery channel (J124 ARM, J121 IGNITER 1, both black 2-position terminals with ARM / IGN legends; the backup is the isolated Blue Jay). From R2/R4: AON7524, arm sense, cold pull-up (H-1); pyro spacing rules in `m3.kicad_dru`; sense dividers of 2 × 5.1 kΩ in series over 2 × 2 kΩ in parallel, plus 4.7 kΩ at each ADC pin (R168, R170, R172). R8: the CH1 block (parts and copper) and PYRO_BLOCK are R7's, rigid and hash-asserted | `docs/M3_R6.md`; `docs/M3_ACTUATOR_MERGE.md`; `docs/M3_R4.md`; `docs/M3_R8.md` |
| Pull-pin (advisory pad witness, F9), buzzer | ✅ Routed in R2; R4: JST PH pull-pin connector; R6: MLT-5020 buzzer (4.0 ± 0.2 kHz, Huaneng datasheet). R8: the buzzer on PC13, GPIO-toggled (no timer output on PC13) | `docs/M3_ACTUATOR_MERGE.md`; `docs/M3_R8.md` |
| Interface to the independent backup altimeter | ✅ Ruled 2026-09-25: none — fully isolated, no shared copper | Same, §1 |
| Mounting holes / zip-tie holes, board length | ✅ R7 and R8 (the same outline and holes, rigid in R8): 46 × 118 mm with parts on both sides (P1 maximum 120 mm); the SMA jacks overhang the aft edge (y = 0) by 9.5 mm; 5 M3 holes at (4, 4), (42.3, 4), (4, 64), (4, 114.4), (42, 114.4); 2 Ø3.2 tie holes beyond J122's ends for the servo-plug tie; R7 also had 3 JLC tooling holes (Ø1.152 NPTH), removed in R8. Sled, coax and camera-shroud fit not physically verified | `docs/M3_R7.md`; `docs/M3_R8.md`; `docs/M3_R3.md` §2 |
| Manufacturing package (BOM / CPL / Gerber) | ✅ R8 package made and checked by `m3_design/r8_fab.sh` on the final board (SHA-256 `cc044ea0…`, fix pass 4) and bound to it (`tools/fab_manifest.py`); BOM identical to R7's. Before ordering R8: two consecutive independent review passes with no open Critical or Major (REQUIREMENTS "R8 acceptance"; r8_plan §4; pass 1 found 1 Major, fixed in fix pass 1): passes 2, 3 and 4 found no Critical or Major (pass 4 on fix pass 3's board `c84f00b8…`: 0 Critical, 0 Major, 16 Minor; `docs/R8_VALIDATION.md` "Review pass 4"); fix pass 4 applied pass 4's two copper Minors, and its board `cc044ea0…` has not itself been reviewed; still open: the owner's dated acceptance of the R8 deviation list (REQUIREMENTS M2; `docs/R8_VALIDATION.md`), U4 consigned, JLC's acceptance of the five long-edge tabs (ORDERING §3) and a cost and stock run within 24 h (REQUIREMENTS M3); no quote accepted, nothing ordered. R7's accepted package stays on branch `m3-assy-r7` (431025d) as the fallback | `m3_design/assembly_review/fab/`; `docs/ORDERING.md` |
| Shorted-igniter current limit (a shorted igniter must not brown out the logic) | ✅ Hardware: R134 2 Ω pulse resistor, simulated at all corners. Firmware must end every fire pulse at 20 ms and resume flight state after a reset | `docs/M3_ACTUATOR_MERGE.md` §2.6, `m3_design/sim_r2/FINDINGS.md` |
| ARM plug physical form / reachability in flight configuration (FMEA H-6, V-18) | ❌ Owner decision open (harness / mechanics, not the board) | `docs/R2_VERIFICATION.md` §4 |
| External power switch type (contact carries ~7 µA; 470 kΩ on each side of it since R4) | ⚠ Requirement: sealed reed / magnetic switch or a dry-circuit-rated gold-contact switch | `docs/R2_VERIFICATION.md` §4 |
| R8 bench firmware and diagnostics | ❌ Not started (R8 needs a new board binding; `docs/M3_R8.md` §"Firmware" and its binding note `m3_design/assembly_review/sources/r8_design/step9/r8_binding_note.json`): v0.8.1 and `diagnostics` are bound to the archived R1 board (`reference/m3_assy_r1/`); the R1 build chain cannot run in this repo | `docs/superpowers/plans/2026-10-05-m3-assy-r3-bench-firmware.md` |

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
- Routing: hand-route critical nets (power, pyro, crystal, USB, SPI/QSPI); use only 0° / 45° / 90° straight segments with no staircases, acute angles or stubs; put a GND via within 1.5 mm (centre to centre) of every layer change of a critical signal net (RF, pyro and arming, crystal, USB data, SPI/QSPI/IMU chip select and the other RADIO_* / GNSS_* nets); size high-current copper per IPC-2152. The owner's full clean-routing list (no needless detours, extra vias or layer hops, tiny jogs, duplicate or overlap-only copper, untidy pad entries or neck-downs, over the whole board, inherited copper included) is REQUIREMENTS M2. `tools/route_check.py` (run by `tools/check.sh`) gates the part of it that M2 names (on nets with a pour this includes chain detours and layer hops in series; on every critical net, removable local bumps and vias joined to a track only by overlap); every exception is an allowlist entry in that tool with a measured reason, every counted non-critical leftover (any hygiene category) carries a recorded measured reason there too, and the rest is checked in review and listed with a measured reason in the revision's validation record. All of them stay deviations until the owner accepts that list (M2).
- Silkscreen: reference designators legible (≥ 1.0 mm text, REQUIREMENTS M2), never over pads or off the board edge; on silkscreen only designators, the terminal, arming and connector legends (REQUIREMENTS F8; also UART, SERVO and battery), the revision legend and JLC's order-number placeholder; a legend about a part sits within 6 mm of that part's courtyard (`tools/check_r7.py` `legend_subjects`, which `tools/check_r8.py` runs); part numbers hidden on F.Fab. Crowded designators go on the bottom side under their part, never next to another part; one with no spot nearer its own part than any other (clear of pads and vias) on either side is hidden, kept on F.Fab and listed in the current revision's record (`docs/M3_R8.md` §"Silkscreen").
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
python3 tools/export_fab.py                      # Gerber zip + JLC BOM/CPL into m3_design/assembly_review/fab/
KICAD_CLI=/path/to/kicad-cli tools/check.sh      # specify kicad-cli on non-macOS systems
kicad-cli pcb render --side top -o top.png m3_design/assembly_review/m3.kicad_pcb
kicad-cli pcb export gerbers -o gerber/ m3_design/assembly_review/m3.kicad_pcb
```
