# R11 plan: R10's circuit on a compact six-layer board

Branch `m3-assy-r11`, cut from `m3-assy-r10` at `deb179e` (R10 board `a0ec075e…`, 46 × 90 mm, closing pair rounds
35 / 36 clean). Started 2026-11-02 on the owner's standing instruction: a much more compact board laid out the way the
MicoAir H743 is, with pyro, using the open-source LEVIA-H7 as the reference. Decisions are in `R11_DECISIONS.md`
(D-R11-xx); this file is the plan and the reading guide.

## 1. What R11 is

R11 is R10's circuit with a new physical implementation. The netlist's nets, part values and every AGENTS §2 rule
carry over unchanged (D-R11-01). What changes: the MCU package, passive case sizes, the wired connections, the
stackup, the outline, the placement and all the copper. Every calculation that depends on copper, placement or a
package (fire budget, hot-plug feed, hold-up, IPC-2152 widths, S-8 spacing, plate modes, fit) is re-run on the R11
board; a figure that is not re-run is not quoted for R11.

## 2. Reference designs

| Reference | What R11 takes from it | What R11 does not take |
|---|---|---|
| LEVIA-H7 (`github.com/piecol/LEVIA-H7`, CERN-OHL-S-2.0, cloned read-only to `~/dev/LEVIA-H7`; nothing in it was run) | 39.6 × 39.6 mm, six layers F / GND / PWR / SIG / GND / B (0.1 / 0.535 / 0.1 / 0.535 / 0.1 mm cores and prepregs), STM32H743VIH6 TFBGA-100, 0402 passives, 0.4 / 0.25 mm vias, 0.127 mm rules, parts on both faces (81 top / 92 bottom), connectors on the edges with wires leaving outward, MCU and IMUs central, regulators on one side. Measured density: 1407 mm² of courtyard on 3137 mm² of two faces (45 %). | Its circuit, footprints, firmware and scripts; its non-latching JST-SH 1.0 connectors; the 30.5 mm drone stack pattern |
| MicoAir H743 (closed; public photos and dimensions only) | Edge-mounted latching JST-GH ports, battery on solder pads | Its circuit |
| BPS.space AVA (R10's layout reference, `AVA_LAYOUT.md` in R10) | Pyro cell kept compact and separate, probes at part pads | Screw terminals |

## 3. Size (D-R11-02)

R10's courtyards cover 2986 mm²; without the eight DB125 terminals (945 mm²) the parts need about 2040 mm², and
about 1800–1900 mm² after the TFBGA-100 and 0402 changes (estimate; the placement stage measures it). A 36 × 36 mm
board has 2592 mm² over both faces, about 72 % fill before connectors and mounting holes, beyond the 45 % that
LEVIA-H7 routes on six layers. The bay's limit is the Ø50.8 mm coupler bore, which allows R10's 46 mm width, and the
board's cost to the vehicle is its length in the stack. So R11 keeps 46 mm and is as short as the parts allow, with
a target of 50 mm and a ceiling of 56 mm.

## 4. Stages

| Stage | Output | Gate |
|---|---|---|
| A. Parts and schematic | `m3_design/r11_parts.py`, `r11_sch.py`, `r11_sch_check.py`; R10's netlist pinned in `m3_design/r11/design/r10_input/` by SHA-256; `circuit.json` (the R11 package / connector changes); `pin_table.tsv` (TFBGA-100 balls) | strict ERC, every pin against the pin table, R10's net contract carried over, seeded faults |
| B. Board and placement | `r11_pcb.py`, `r11_place.tsv`: outline, six-layer stackup, holes, every part placed, no copper | DRC courtyards, fit, placement report (density, edge clearances) |
| C. Copper, by families | `r11_route*.py`: core (MCU / BGA fan-out / HSE / QSPI / IMU / baro), usb, pyro, power, ports, servo, sd, signals, ground | `r11_stage_check.py` after each family |
| D. Post and fab | `r11_post.py` (silkscreen, designators, title block, zone fill), `r11_fab.sh` (Gerber / BOM / CPL / manifest) | `tools/check.sh` with the R11 profile |
| E. Records | `docs/M3_R11.md`, AGENTS / STATUS / REQUIREMENTS R11 rows, the binding note | review rounds |
| F. Review | ten lenses plus a triage verifier per round, until two consecutive full rounds have zero verified real errors | |

Layout in the repository: the R11 KiCad project is `m3_design/r11/` (R10's `m3_design/assembly_review/` stays as the
frozen record); design data in `m3_design/r11/design/`, reviews in `m3_design/r11/review/`, the fab package in
`m3_design/r11/fab/`. `tools/check.sh` runs R10's gate and, once `m3_design/r11/m3.kicad_pcb` is tracked, R11's.
Until the R11 board passes its full gate it is not committed; generators and records may be.
