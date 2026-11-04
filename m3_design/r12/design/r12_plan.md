# R12 plan: R11's circuit, pruned and re-sourced, on a one-sided four-layer board for JLC Economic PCBA

Branch `m3-assy-r12`, cut from `m3-assy-r11` at `0b26da5` (R11 tip, D-R11-85 … -88 included). Started 2026-11-04 on
the owner's instruction (verbatim): "without sacrificing functionality, make the price as low as it can reasonably go.
two potential levers include safety margin (absolutely minimal safety margin) and size (you can increase it up to
200mm) finding alternatives to parts and ruthlessly deleting unecessary partws" and "remember to use BPS.space AVA as
an example for great layout and for like how little safety margin you need". Decisions are in `R12_DECISIONS.md`
(D-R12-xx); the cost study that chose the architecture is `cost_study.md`. This file is the plan and the reading guide.

Evidence labels (AGENTS §2.5): Datasheet, Calculation, Simulation, Inference, Measured; live JLC data is labelled
Live with its UTC timestamp. Nothing in R12 is measured on hardware.

## 1. What R12 is

R12 is R11's circuit (net names, the R10 safety networks and R11's TFBGA ball map kept) with every part that no
requirement needs deleted, every part with a cheaper equivalent re-sourced, and laid out new on:

| Item | R12 | R11 | Basis |
|---|---|---|---|
| Assembly | JLC **Economic** PCBA, **one side** (every footprint on F) | Standard, two sides | D-R12-01; cost_study §1 |
| Reflow | 255 ± 5 °C (Economic, not adjustable) | 240 ± 5 °C | JLC capabilities page (cost_study §1.1) |
| Stack | 4 layers, 1.6 mm, 0.5 oz inner, ENIG | 6 layers | D-R12-03; cost_study §2.1 |
| Outline | 46 × ≤ 100 mm (JLC's 4-layer price step: 46 × 105 costs $20 more) | 46 × 50 mm | D-R12-01; cost_study §1.4, §2.1 |
| Vias | 0.3 mm drill / 0.45 mm pad through vias only, no via in pad | 0.25 / 0.2 mm, two VIPPO | D-R12-03 |
| MCU | STM32H743VIH6 TFBGA-100 kept (escape count, D-R12-02) | same | D-R12-02 |
| Parts | 184 (50 deleted, 16 added), 55 codes: 36 Basic, 16 Extended, 1 Preferred Extended, 2 owner-fitted | 218, 75 codes | D-R12-04 … -19 |

The owner's 200 mm allowance is not used: R12's courtyards cover 1995 mm² (Calculation: the sum of the R12 lands'
courtyard boxes), 43 % of one 46 × 100 mm face, near LEVIA-H7's 45 % two-face density (R11 records) and inside AVA's
47.4 × 98.5 mm footprint (`reports/AVA board layout images.md` in the parent repository). A longer board adds JLC's
$25 engineering fee (cost_study §2.1, Live).

## 2. Reference designs

| Reference | What R12 takes | What R12 does not take |
|---|---|---|
| BPS.space AVA (cost_study §4; every "AVA has / lacks" is an Inference from photos and talks: no AVA schematic or BOM is public) | four layers at about 47 × 99 mm; one connector family per job; no USB limiter, no port ESD, a bare transistor for the camera, a plain bulk cap: the minimal-margin pattern R12 follows wherever no requirement or AGENTS §2 rule needs more | parts on both faces (hand assembly; at JLC that forces Standard two-sided, +$33.77 per order and no Economic tier), screw terminals |
| R11 / LEVIA-H7 | the circuit, the TFBGA ball map, 0402 passives, GH-style latching ports on the edges | six layers, both faces, 0.2 mm vias, VIPPO |

## 3. Cost target

REQUIREMENTS M3 cap: $84.41 per board at 5 boards (parts + feeder fees). R12's target is the lowest order total that
keeps every requirement's function: **≤ $170 for 2 boards and ≤ $295 for 5 boards all-in (JLC parts, feeder, fixed and
joint fees, bare PCB; shipping and tax excluded)**, against R11's $376.55 / $531.81 (cost_study §0, Live 2026-11-04).

Stage A run (Live, `jlc_r12_stock.json` / `r12_cost.json`, 2026-11-04T02:42:47Z): **2 boards $169.15, 5 boards
$292.38** ($166.08 / $289.31 if JLC waives the Preferred Extended feeder fee, an Inference); M3 metric $50.63 per board
at 5 boards against the $84.41 cap.

## 4. Stages and gate

| Stage | Output | Gate |
|---|---|---|
| A. Parts and schematic (this stage) | `m3_design/r12_parts.py`, `r12_sch.py`, `r12_sch_check.py`, `r12_budget.py`; R11's netlist pinned in `design/r11_input/` by SHA-256; `design/circuit.json` (the R12 change list); `design/pin_table.tsv` (r12_net); `design/r12_windows.json`; `design/jlc_r12_stock.json`, `design/r12_cost.json`; `tools/check_r12.py` skeleton, `fit_check` / `route_check` profile r12, `check.sh` R12 section, `tools/test_r12_check.py` | strict ERC, exact netlist contract, AGENTS §2 net contracts, one-side lands, 37 seeded faults, deterministic replay; `tools/check.sh` exit 0 |
| B. Board and placement | `r12_pcb.py`, `r12_place.tsv`: outline, four-layer stack-up, holes, every part on F, no copper | check_r12 `--stage placement`, fit_check r12, DRC courtyards |
| C. Copper by families | `r12_route*.py` (BGA escape per D-R12-02, pyro, power, ports, USB, SD, servo, signals, ground) | route_check r12 after each family; check_r12 `--stage copper` |
| D. Post, fab and analyses | `r12_post.py`, `r12_fab.sh` (Economic BOM / CPL, owner BOM for C84 and LS120), fire budget, hot-plug and hold-up re-runs on R12 copper (keep or drop R166, D-R12-09), the R10 / R11 rules ported into check_r12 (its PENDING list) | `tools/check.sh` with the R12 section (runs once `m3_design/r12/m3.kicad_pcb` is tracked) |
| E. Records | `docs/M3_R12.md`, REQUIREMENTS / ORDERING / AGENTS R12 rows, binding note, owner acceptance list (`R12_DECISIONS.md` §3) | review rounds |
| F. Review | ten lenses plus triage per round until two consecutive rounds have zero verified real errors | |

Layout: the R12 KiCad project is `m3_design/r12/`; design data in `m3_design/r12/design/`. `tools/check.sh` runs R10's
gate, R11's (its board is tracked) and, once `m3_design/r12/m3.kicad_pcb` is tracked, R12's; until then only
`tools/test_r12_check.py` runs for R12. R10's and R11's gates are unchanged.

## 5. Stage A status (2026-11-04)

Done: everything in the stage A row. Not done: any board, placement, copper, fab package, hot-plug or fire re-run on
R12 copper, firmware. Open items: `R12_DECISIONS.md` §4.
