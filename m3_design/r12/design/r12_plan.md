# R12 plan: R11's circuit, pruned and re-sourced, on a one-sided four-layer board for JLC PCBA (Economic until D-R12-211, Standard since)

## Current snapshot (round 12, 2026-11-13; D-R12-192 and D-R12-195, 2026-11-14; round 13 fix pass, 2026-11-14; round 14 fix pass, 2026-11-15; Standard rebuild and its review fixes, 2026-11-24)

PCB `0c681ad6af502e12a285aa1fbc5cbfba81d7131e18d698ab9199c8462cdde5a5` since the Standard PCBA rebuild (D-R12-211 … -220, 2026-11-24: JLC Standard, 240 ± 5 °C; U4 ISM6HG256X, U5 MS5611, U6 / C33 not fitted; 179 JLC parts, 59 codes, all charged; copper identical); before it `c8b0412d…`, since the round 14 fix pass (D-R12-205 … -209: round 14 reviewed `5af58097…` with seven lenses plus a
second opinion, 0 Critical / 0 Major / 12 Minor, R12F14-TRI-01 … -12; rounds 13 and 14 are the clean pair under
D-R12-167 and the review loop stops; a second GND via for R110 / C83 / C28 and an F.Cu 3V3 strap along U1's F row;
K-power validates its exceptions and pins their cut sets; one unshed load envelope in the hold-up and fire models,
so the J400 chatter bench rule is **under 6.6 ms** (was 6.7); two identical builds; stage D / hot-plug re-bound;
1114 tracks / 386 vias, K-power 128 taps / 20 exceptions, 148 single points = 18 exception vias + 130
`LONG_TAIL_R12` entries; legends, designators, paste, BOM and CPL unchanged). Before it, PCB `5af58097…` since the
round 13 fix pass (D-R12-199 … -204:
round 13 reviewed `96207d2e…` with seven lenses plus a second opinion, 0 Critical / 0 Major / 12 Minor, R12F13-TRI-01
… -12; SERVO1_OUT's hop removed, C60.1 / C94.1 second barrels and the C16–C18 / C60.2 / C94.2 GND row's link, K-power
gating every single point; two identical builds; stage D / hot-plug re-bound; 1111 tracks / 385 vias, K-power 124 taps
/ 20 exceptions, 153 single points = 18 exception vias + 135 `LONG_TAIL_R12` entries; legends, designators, paste,
BOM and CPL unchanged). Before it, PCB `96207d2e…` since D-R12-195 (single-servo SH-4 J122 in the MicoAir H743 UART order; SERVO3 / SERVO4 deleted;
SERVO1_MCU / SERVO2_MCU trunks re-laned; two identical builds, gate steps and stage D / hot-plug re-bound by its fix
lane; 189 footprints, 181 JLC parts, 1107 tracks / 385 vias, 50 legends, 105 shown / 84 hidden designators, 585 paste
flashes, 60 BOM lines, four recorded route leftovers, K-power 121 taps / 19 exceptions, S-10's exception table
unchanged), 46 × 86.85 × 1.6 mm. `876733fe…` (D-R12-192, SH-8 J122) differed from round 12's `c9b9f0fa…` only at
J122. The figures below for `c9b9f0fa…` describe its copper; away from J122 and the servo cells they still hold.
Round 12's `c9b9f0fa…`: lane P (`6d945ce`) reported two identical builds,
full gate exit 0, 193 footprints, 185 assembled parts, 1147 tracks / 394 vias, 52 legends, 106 shown / 87 hidden
designators (R13 and R118 newly hidden), 595 paste flashes, 60 BOM lines (on `876733fe…`: 54 legends, 597 paste
flashes, 61 BOM lines; tracks / vias, S-10 and K-power counts unchanged). S-10 has 203 exceptions;
K-power 123 taps / 19 exceptions. Routing: zero failing, two allowlisted, eight recorded leftovers, no stale
or unrecorded leftovers. Lane A (`a04a513`): 60 stage-D tests pass; analysis and hot-plug inputs bind to this hash.
The verification review of the fix pass found 0 Critical / 0 Major / 7 Minor, all text (R12F12-VER-01 … -07);
the full gate on the final tree is the commit condition.

Fire loop 4.72843 Ω; four-stall fire 1.24705 A at J1 5.71364 V; EN at R80.1 5.69476 V (D-R12-219's unshed load, 0.551 A;
1.24711 A / 5.71390 / 5.69504 V under D-R12-207, 1.24833 A / 5.71941 / 5.70082 V before). Chatter limits 6.890 / 6.794 ms;
bench rule under 6.6 ms per sliding 100 ms (6.892 / 6.796 ms before D-R12-219, 6.935 / 6.843 ms and 6.7 ms before D-R12-207). U6 drift minimum 3.20400 V on the current board and `5af58097…` (3.20406 V on `96207d2e…`: the C60.1 / C94.1 barrels open the In2 3V3 sheet, D-R12-200)
in the 1 A calculation; O-R12-22 remains open. U2 requires ≤ 200 MHz and no microSD write burst overlapping a beep (rule (g); limit 0.870 / 0.807 A at 700 / 600 kHz at the 3V3 drift maximum, D-R12-202).
All these electrical bounds are Calculation / Inference. Hot-plug 2304 / 2304 pass, minimum −14.077 V
(Simulation / Inference). No firmware, physical, electrical or JLC DFM test has been done on this board.
Current electrical detail: [M3_R12.md](../../../docs/M3_R12.md); full numbers: `stageD_budget.json` and
`hotplug_results_r12.json`. Earlier named-board figures below are historical and cannot qualify this board.

Parts + feeder **$62.44 / $43.10 per board at 2 / 5 boards**, against the $84.41 cap (Live
2026-11-15T02:20:48Z / 02:22:13Z, after D-R12-195's SH-4 J122 and the SERVO3 / SERVO4 deletion): 60 BOM lines
(24 Extended / 36 Basic), 181 JLC parts, 21 charged codes, $30.20 parts per board and $64.47 feeder fees per order
(was $64.03 / $43.77 with 22 codes on `876733fe…`). There are 585 paste flashes and no owner BOM. Stock
2026-11-15T02:20:03Z / 02:21:31Z: **U9 (TPS259470ARPWR, C3662799) reads short at both quantities** (stock 175,
orderable 0 by JLC's `canPresaleNumber`, minimum purchase 7: a supplier change since 2026-11-14, not D-R12-195); no
other line short or thin. Orderable quantity is an Inference about JLC's field: confirm U9 in the JLC cart on order
day. The 2026-11-11 all-in quote of $165.33 for two assembled boards before shipping was for historical `1d7562d5…`;
re-quote the current board, including X-ray, DFM and reflow acceptance. Nothing ordered.


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
| Assembly | JLC **Standard** PCBA, **one side** (every footprint on F; Economic until D-R12-211) | Standard, two sides | D-R12-01, -211; cost_study §1 |
| Reflow | 240 ± 5 °C (Standard; Economic's 255 ± 5 °C until D-R12-211) | 240 ± 5 °C | JLC capabilities page (cost_study §1.1) |
| Stack | 4 layers, 1.6 mm, 0.5 oz inner, ENIG | 6 layers | D-R12-03; cost_study §2.1 |
| Outline | 46 × ≤ 100 mm (JLC's 4-layer price step: 46 × 105 costs $20 more) | 46 × 50 mm | D-R12-01; cost_study §1.4, §2.1 |
| Vias | 0.3 mm drill / 0.45 mm pad through vias only, no via in pad | 0.25 / 0.2 mm, two VIPPO | D-R12-03 |
| MCU | STM32H743VIH6 TFBGA-100 kept (escape count, D-R12-02) | same | D-R12-02 |
| Parts | 189 footprints, 179 JLC-assembled parts, 59 codes: 36 Basic / 23 Extended, all 59 charged on Standard (D-R12-211, -213: U6 / C33 not fitted; 181 / 60 / 21 charged on Economic before); no owner-fitted parts (D-R12-195: J122 an SH-4 on C7430446, SERVO3 / SERVO4 cells deleted; D-R12-192's 8P had added C7430450; 193 / 185 / 60 in round 12) | 218, 75 codes | D-R12-04 … -19 |

The owner's 200 mm allowance is not used. The historical stage-A density estimate was 1995 mm² (Calculation: the sum of the R12 lands'
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
| D. Post, fab and analyses | `r12_post.py`, `r12_fab.sh` (Economic BOM / CPL; every part JLC-assembled, no owner BOM), fire budget, hot-plug and hold-up re-runs on R12 copper (keep or drop R166, D-R12-09), the R10 / R11 rules ported into check_r12 (its PENDING list) | `tools/check.sh` with the R12 section (runs once `m3_design/r12/m3.kicad_pcb` is tracked) |
| E. Records | `docs/M3_R12.md`, REQUIREMENTS / ORDERING / AGENTS R12 rows, binding note, owner acceptance list (`R12_DECISIONS.md` §3) | review rounds |
| F. Review | full review rounds plus triage until two consecutive rounds have zero Critical and zero Major real errors; fix Minors each round without resetting the count (D-R12-167). Rounds 10 and 11 were clean; the owner stopped the loop on 2026-11-09. Round 12 is the final pass (D-R12-175) | |

Layout: the R12 KiCad project is `m3_design/r12/`; design data in `m3_design/r12/design/`. `tools/check.sh` runs R10's
gate, R11's (its board is tracked) and, once `m3_design/r12/m3.kicad_pcb` is tracked, R12's; until then only
`tools/test_r12_check.py` runs for R12. R10's and R11's gates are unchanged.

## 5. Stage A status (2026-11-04)

Done: everything in the stage A row. Not done: any board, placement, copper, fab package, hot-plug or fire re-run on
R12 copper, firmware. Open items: `R12_DECISIONS.md` §4.

## 6. Stage B / C status (2026-11-04)

Stage B done: `r12_pcb.py`, `r12_place.tsv` (46 × 100 mm, D-R12-24), `r12_build.sh`; fit_check r12, placed DRC with
parity (0 violations) and check_r12 placement pass; the placed board builds byte-identically (`9881aaa3…`). Stage C in
progress: infrastructure (`r12_route.py`, `r12_planes.tsv`, the drafting aid `r12_aid/`) written, routing not complete
and no copper table frozen (stageC.md). Stage A margin items D-R12-21 applied (port divider, PA6 threshold).

## 7. Historical Economic parts pass (2026-11-04, D-R12-49 … -54)

Owner: "go fully Economic" (every JLC-placed part allowed on Economic PCBA); parts rated to a 250 °C peak are accepted on
Economic's 255 ± 5 °C (D-R12-49, owner acceptance A-9). U4 ISM6HG256X (Standard Only) → LSM6DSVE on the same land
(D-R12-50); new U6 FXLS90322 XY medium-g accelerometer for F2 on the IMU SPI1 bus with chip select HG_CS on PD2 (B7; PA10 → PC11 D-R12-64A → PD2 D-R12-93), plus
C33 (D-R12-51); U5 LPS28DFW (Standard Only) → MS5607-02BA03 on R11's MS5611 land (D-R12-52); placement D-R12-53; axis maps
D-R12-54. SS34, SRV05-4 and the microSD socket stay. 186 parts, 57 codes (stock run 2026-11-04T23:25:09Z):
**2 boards $159.92 ($79.96 per board), 5 boards $260.08 ($52.02 per board)**, M3 metric $44.12 per board at 5 boards
(`r12_cost.json`). Stage B rebuilt and passes (placed DRC, fit_check r12, check_r12 placement); routing restarts on the
new placement: new net HG_CS (U1.D10 to U6.8), U6 on SPI1 and 3V3, U5 rotated 180 with its inter-row no-track band, R12 / R13 0.2 mm east, U6 / C33 at x 25–31, y 38–43.

## 8. Stage C pass 1 (2026-11-05, D-R12-61A … -66A)

Nine U1 nets re-pinned to balls facing their pads (QSPI_NCS PB10; barometer I2C3 on PA8 / PC9; microSD SPI4 on PE12-14
with SD_CS on PA7; HG_CS PD2 (B7; PA10 → PC11 D-R12-64A → PD2 D-R12-93); VBUS_SENSE PA10), two U1 escapes changed in the aid (QSPI_IO2 by a dog-bone, IMU_INT1
without a B lane), and the copper frozen in `m3_design/r12_routes.tsv`: board `da48bb99…` (two builds, same hash), DRC
0 / unconnected 0 / parity 0, check_r12 copper OK, route_check r12 83 failing (reported, not fatal, until pass 2 sets
`R12_ROUTE_HYGIENE=strict`). Pass 2 (routing hygiene) is next (stageC.md §5).

## 9. Historical stage D (2026-11-05, D-R12-78 … -82)

Stage C pass 2 was frozen as D-R12-77A. On that copper, R10's hot-plug model failed 8 of 2304 cases, and R10's C88
topology check failed. Stage D fixed both and finished the board.

**Fixes.**
- C79, a third 22 µF damper capacitor (D-R12-78).
- C88 moved onto the U9 feed (D-R12-79).
- Second vias on Q124's fire return and on U9 OUT.

**Post stage, gate and parts.**
- The build now runs a post stage: `r12_post.py` applies the frozen `r12_legends.tsv`, which `r12_legends_aid.py`
  drafts (D-R12-80). Every SH contact carries a legend on the bottom face, and five copper items moved to make room.
- J122's harness note is optional (D-R12-81, owner acceptance pending).
- The buzzer land carries '+' / '-' on F.Fab (D-R12-82).

**Build and gate (Measured).**
- `r12_fab.sh` produces the package; the manifest is bound.
- Board `d776c5d7…`: two builds gave the same hash.
- The board and `fab/` are tracked, so `tools/check.sh` runs its R12 section: exit 0.

**Analyses.** `r12_stageD.py` and `tools/r12_hotplug.py` were re-run on the final board (`stageD_analysis.md`):
- hot-plug passes 2304 / 2304 (Simulation / Inference);
- four-stall fire current is 1.249978 A (Calculation / Inference);
- U6's supply closes O-R12-22 (Calculation).

**Cost (Live).** Parts plus feeder: $61.88 per board at 2 boards and $44.38 at 5. All-in order totals are about $164 and
$265 (Calculation, below the §3 targets). No part is short.

**Next.** Stage E records are written (`docs/M3_R12.md`, `docs/R12_VALIDATION.md`, `docs/R12_VEHICLE_HANDOFF.md`).
At that historical checkpoint stage F was pending. It later completed; rounds 10 / 11 stopped the loop,
and round 12 is the final pass (D-R12-175). Record: `stageD.md`.
