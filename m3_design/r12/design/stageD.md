# R12 stage D: post stage, fab package, analyses and the fixes they needed (2026-11-05)

**Superseded by §7 (branch `r12-port-fix`, D-R12-83 … -85): board `d6e4f7ee…`; and since the AVA re-layout by
`stageE_relayout.md` (D-R12-93 … -99, 46 × 90 mm, and 46 × 88 mm since D-R12-144; current board `82eddc69…` since
round 7, D-R12-144 … -151; `f26dfef1…` after round 6, D-R12-134 … -143; `6e874d4e…` after round 5, D-R12-125 …
-133).** §1–§6
record the stage D board `d776c5d7…` as it was.

Follows stageC.md (pass 2 frozen, D-R12-77A, board `e2b005b5…`). Decisions D-R12-78 … D-R12-82 are in
`R12_DECISIONS.md`. Branch `r12-stage-d`; nothing is ordered. Labels (AGENTS §2.5): **Measured** = read from the CAD or
a tool run on it; **Calculation** = arithmetic on CAD copper and datasheet values; **Simulation** = the numerical
hot-plug model; **Inference** = anything resting on an unmeasured or estimated input; **Live** = JLC's public component
API with its UTC timestamp. No physical test was run. Coordinates are board mm (x east, y forward from the aft edge).

## 1. Result

`m3_design/r12_build.sh` now ends with the post stage (`m3_design/r12_post.py` from the frozen table
`m3_design/r12_legends.tsv`) and the fab package (`m3_design/r12_fab.sh`). Board `m3_design/r12/m3.kicad_pcb` SHA-256
`d776c5d7181e10f0ea3d16960050b63b5c5e7d61bb26074c4ea3b204b71b7161`, built twice from the final tree with the same hash,
exit 0 (Measured). On it (Measured): KiCad DRC 0 violations, 0 unconnected, 0 parity; r12_sch_check OK (187 parts,
37 / 37 seeded faults caught); fit_check r12 OK; check_r12 every rule OK, K-legends and K-fill included; route_check r12
0 failing, 2 allowlisted (D-R12-75A), 13 non-critical leftovers (informational); the R12 fab manifest bound, its content
checks OK. The board and `m3_design/r12/fab/` are tracked in git, so `tools/check.sh` runs its R12 section:
exit 0 (Measured, 2026-11-05). `tools/test_r12_check.py`: 49 tests OK (one skipped without the board; Measured).

| Stage D finding | Fix | Decision |
|---|---|---|
| Hot-plug on the stage C copper: 8 / 2304 required cases at −15.05 … −15.10 V (limit −15.0 V), all at the 2 µH corner | C79, a third 22 µF damper capacitor (C12891, already on the BOM) | D-R12-78 |
| R10's C88 topology: the U9 feed bypassed C88 (stub off C96.1) | C88 on the feed, C96.1 → C88.1 → U9.5; C95.1 → C96.1 widened to 0.8 mm | D-R12-79 |
| Fire return Q124.2 on one via; U9 OUT on one via; a duplicate RAW_PROTECTED track | second GND via (9.2, 42.6); second RAW_PROTECTED via (20.6, 15.0); duplicate removed | D-R12-78 (fix pass) |
| No room for the SH contact legends | bottom-face columns, alternately inward / outward; five copper items moved | D-R12-80 |
| J122's harness note: no free strip within 6 mm of J122 | optional on R12 (absence waived only); owner acceptance pending | D-R12-81 |
| R10's Fab-text rule on LS120 ('+' / '-' required) | polarity marks added to the QMB-09B-03 land on F.Fab | D-R12-82 |
| J400's footprint pin-1 mark nearer D402's pad 1 | D402 1.0 mm west to (10.6, 7.8) | D-R12-80 |

## 2. Post stage (D-R12-80 … -82)

* **No search in the build.** `m3_design/r12_legends_aid.py` (not run by the build) drafts the table once on the routed
  board with R11's search helpers (`r11_legends_aid`) in R12's order: every contact legend first, J122's note, the
  revision, the SHOWN_REFS designators, the connector words, J2's SWD rows, pin-1 dots, the other designators and the
  Fab references. Two aid runs on the final routed board wrote the same file byte for byte (Measured, `cmp`).
* **SH contacts.** At 1.0 mm pitch a 1.0 mm legend's ink (about 1.15 mm wide at 90°, Measured from the font) plus the
  0.155 mm silkscreen gap exceeds the pitch, so neighbours cannot share a face side by side. The contact legends sit
  on the bottom face (no parts there), except J400's `1:SW` and `4:NC` on the top face. Each follows its own column,
  alternately outward (ink ends at the pad centre line) and inward (ink starts 0.2 mm past it); both alternations are tried per port and the one with fewer misses kept
  (J122 alternation 1, the others 0; no misses). The aid's ownership margin is 0.05 mm (gate 0.01 mm).
* **`m3_design/r12_post.py`** is `r11_post`'s apply and contract with R12's revision, KIID seed 12120, table and gate
  data, gated by `check_r12 --only K-legends,K-fill`; it refuses a table with an open row.
* **Placed (Measured on `d776c5d7…`).** 50 legends: every contact of J1 (BAT+ / GND), J121 (E1− / E1+), J400, J122, J9,
  J410, J420 and J440 (NC contacts included), the words IGN, BAT, CAM, SWD, SERVO, GPS, RADIO, AUX, SWITCH, J2's SWD
  rows, the revision M3-ASSY-R12 on B.Silkscreen and the pin-1 dots. 111 designators shown at 1.0 / 0.15 mm (35 on the
  bottom under their part), 76 hidden and kept on F.Fab:
  C120 C123 C14 C21 C24 C28 C30 C32 C400 C402 C410 C420 C432 C433 C444 C461 C60 C81 C88 D402 R100 R101 R104 R105 R106
  R107 R110 R112 R119 R120 R122 R123 R126 R127 R128 R129 R13 R130 R133 R14 R15 R151 R153 R154 R155 R156 R157 R162 R163
  R164 R165 R167 R175 R178 R180 R400 R401 R404 R431 R433 R434 R435 R440 R451 R460 R462 R471 R60 R61 R81 R83 R84 R9 R92
  R93 R94.
* **Not drawn: J122's note `SERVO + FROM HARNESS`** (D-R12-81). Its 18.9 mm ink has no free position within 6 mm of
  J122 with J122 the nearest subject on either face, at 0° or 90° (Measured: a probe of every 0.2 mm position on the
  drafted board found 0). check_r12 waives only its absence; the rule it states is in `docs/R12_VEHICLE_HANDOFF.md`.
* **Copper moved for the legend columns (D-R12-80; each step DRC 0, route_check r12 0 failing, check_r12 copper 0,
  Measured):** J410 / J420 pin 2 reach PORT_4V8 through C410.1 / C420.1 and their via (outward vias at (21.6, 95.5) /
  (11.1, 95.5) removed); J122.5's GND via to (19.9, 7.0); J122's SERVO3_OUT hop to x 22.05; J9's CAM_5V via to
  (33.0, 8.8); D402 to (10.6, 7.8) (J400's library pin-1 mark is now nearest J400.1 by more than r10_post's 0.5 mm).
* **Notes (footprint library graphics, not drawn by the post stage; printed by r12_post, as R11's).** Silkscreen circle
  of D120 0.10 mm from R130.1's mask opening; U403's and U400's pin-1 circles 0.092 mm from C433.2 / C400.2; U5's
  outline 0.13 mm from C30.1 and C30.2 (all under JLC's 0.15 mm pad-to-silkscreen; KiCad DRC does not flag them, and
  JLC clips silkscreen at openings, Inference).

## 3. Analyses (`stageD_analysis.md`, `stageD_budget.json`; re-run on the final board)

`m3_design/r12_stageD.py` (R11's stage D script on R12's four layers and parts) and `tools/r12_hotplug.py` (R10's model
and C solver run with asserted string replacements, so C79 is modelled as C89 / C95 are; neither R10 file is edited).
Headline figures (labels as given; details and inputs in `stageD_analysis.md`):

| Figure | Value |
|---|---|
| Fire loop / four-stall current (Calculation / Inference) | 4.726699 Ω; 1.249978 A at BAT_IN 5.7208 V, +11.1 % over the MJG J-Tek 1.125 A floor; idle 1.505915 A |
| Shorted match (Calculation / Inference) | 2.164 A at four stalls, 2.608 A idle; match and leads shorted 2.430 / 2.929 A; Q120 / Q121 ≤ 0.631 W, Q124 ≤ 0.492 W for ≤ 36 ms |
| GND fire return Q124 → J1.2 (Calculation, DC solve) | 2.575 mΩ, two vias, inside the 5 mΩ allowance |
| Hot-plug (Simulation / Inference) | 0 / 2304 required cases fail; minimum U9 IN −14.255 V (≥ −15.0); steepest fall 9.251 V/µs (≤ 10); C88 topology, cold limit, convergence, no-clamp and local-path checks pass; electrical SHA `db6dfd75…` |
| D-R12-09 keep or drop R166 (Simulation / Inference) | keep: R166 shorted fails 1164 / 2304, no damper 1920 / 2304, the pre-C79 44 µF 8 / 2304 |
| EN / chatter (Calculation / Inference) | single drop-out trip 8.13 ms at 5.7208 V; bench-rule worst-corner limit 7.56 ms; turn-on nominal 88 / 56 / 45 ms (R12 bound 27–114 ms) |
| Hold-up (Calculation / Inference) | battery break 2.23–6.12 ms unshed, 6.68–11.43 ms shed; PA6 trip 0.47–1.72 ms |
| PA6 window (Calculation / Inference) | 4.62–4.95 V (4.54–5.04 V with 1 % resistors); a four-stall fire into a shorted match can reach it (firmware, O-R12-07) |
| U6 VCC (O-R12-22; Calculation / Inference: drift case and load currents Inference) | ≥ 3.258 V initial / 3.227 V drift at U2's 1 A, margin 123 / 92 mV over 3.135 V: closed as a calculation |
| PORT_4V8 at the ports, 0.561 A (Calculation / Inference) | 4.497–4.500 V initial, 4.447–4.450 V drift (J420 lowest) against the LR900's 4.5 V: owner item (O-R12-26) |
| IPC-2152 worst (Inference, upper bound) | U9.6 pin entry 0.3 mm 76.8 °C at 2.9 A (pin-entry class, two vias now); the 0.4 mm C96.1 → C88.1 → U9.5 run, 4.13 mm, 55.2 °C at 2.9 A, about 36 °C at 2.34 A (O-R12-25) |

## 4. Fab package, cost and stock

`FAB_NET=1 m3_design/r12_fab.sh` on `d776c5d7…` (Measured): JLC BOM 55 lines, 176 JLC parts = 176 CPL rows (all Top)
rebuilt from JLC footprints, every correction verified (`CHECK: none`); owner BOM C84 and LS120 (hand-fitted after
delivery); Gerber zip 13 files (four copper layers); F paste 577 flashes on 577 pasted pads of 175 parts (J121 the one
THT part); manifest bound after the content checks.

Cost (Live 2026-11-05T17:26:00Z / 17:27:57Z, `fab/cost_check_2.json` / `_5.json`, Economic one-sided): parts **$32.72
per board**, feeder 19 charged codes × $3.07 = $58.33 per order. REQUIREMENTS M3 metric (parts + feeder per board):
**$61.88 at 2 boards, $44.38 at 5 boards** against the $84.41 cap. Stock (Live 17:25:13Z / 17:27:19Z,
`fab/stock_check_2.json` / `_5.json`): 57 unique codes (21 Extended / 36 Basic), **none short and none thin** at 2 or 5
boards (orderable = min(stock, canPresaleNumber), an Inference about JLC's field).

All-in order totals (Calculation / Inference: U1-only X-ray count; Live parts and feeder figures; setup / stencil $9.71 from the cost tool; SMT
joints $0.0016 each counted as the 577 pasted pads per board, manual THT joints $0.0164 × 2 for J121 plus $3.58
hand-soldering labour per order, and the bare PCB $25.10 for 5 pcs 4L 46 × 100 mm ENIG are cost_study.md's figures,
Live 2026-11-04; shipping, tax and attrition excluded). Round-2 correction D-R12-105 adds minimum U1-only
X-ray $3.28 / $8.20 at 2 / 5 boards using JLC's 2026-11-06 fee schedule; the dated parts / feeder inputs stay:

| Order | JLC parts | Feeder | Setup + stencil | SMT joints | THT joints + labour | Bare PCB | X-ray (U1 only) | **Total** | Per board |
|---|---|---|---|---|---|---|---|---|---|
| 2 boards | $65.44 | $58.33 | $9.71 | $1.85 | $3.65 | $25.10 | $3.28 | **$167.36** | $83.68 |
| 5 boards | $163.60 | $58.33 | $9.71 | $4.62 | $3.74 | $25.10 | $8.20 | **$273.30** | $54.66 |

Counting U1 / U4 / U5 / U6 / U9 gives $180.48 / $285.60–293.80 with these dated inputs
(Calculation / Inference: qualifying count and tier); confirm the quote, including possible D402 / Y1 fees.
Owner-fitted C84 + LS120 from LCSC add about $0.40 per board (cost tool's JLC prices as the LCSC estimate, Inference). Prices and
stock move daily; re-run `FAB_NET=1 m3_design/r12_fab.sh` before ordering.

## 5. Hashes (Measured, SHA-256)

| File | SHA-256 |
|---|---|
| m3_design/r12/m3.kicad_pcb | d776c5d7181e10f0ea3d16960050b63b5c5e7d61bb26074c4ea3b204b71b7161 |
| m3_design/r12_legends.tsv | 4ea8b5f14094a5252b0e435633df9d6c91946ecaa4d8f0cd62c3f9a5a8f10c31 |
| m3_design/r12_routes.tsv | 3ca7d13e7b8ab7eb3256442b66024dfac4542fddeca64777c12d512e58cb7f43 |
| m3_design/r12_place.tsv | 78584417a5314d379595e6515eced93ae4362e569ecc936260bc4a5e851b6a5f |
| m3_design/r12/fab/m3_bom_jlc.csv | ee5cade81d08f7ff78694856c44baea9ee5db67d72b84fa12540e3b96e8edc85 |
| m3_design/r12/fab/m3_bom_owner.csv | 7e6da01d29e917091f692e01dc8a4a6040ab4abfe5c942b208272017cd82af36 |
| m3_design/r12/fab/m3_cpl_jlc.csv | f21f90a6cb4d5698c13afc1c280a4a0f23da920a436e02f4474c236fae9b2e6b |
| m3_design/r12/fab/m3_fab_manifest.json | 40e79688adef129bbe86d0eb7256022ef33fd11c536724c7b80ae2899e4879b2 |
| m3_design/r12/fab/m3_gerber.zip | 3652072127a863ecfc6289e5ae8bbb75e231bc0ba07c85528d7687360d8bce47 |
| m3_design/r12/fab/m3_assembly_top.pdf | 58bc68aefe91f11c71e854b2ff8158066de567c859a32a94e2f2db12c5fb801b |
| m3_design/r12/fab/m3_assembly_bottom.pdf | d0be0c0b6fa66ed00950031555e5a8bb575b83f650efda010c101c1892ea5a2a |
| m3_design/r12/fab/cost_check_2.json | 3d8058bc0448de52237c9135d03e499874597de969f6b6e60399cdf0c37d7b81 |
| m3_design/r12/fab/cost_check_5.json | 1b22e1c8054501d7916e449b1830c92ddb5be6ff43cb34902dd08534cc40ee87 |
| m3_design/r12/fab/stock_check_2.json | f6667b466583d3dfa5fca1c1829a14a36a8fb1f292a5f4f47b29a2abc954a9d0 |
| m3_design/r12/fab/stock_check_5.json | af8994e1f1b8b431e717f0ea3169ff2895e50e9555825febb050f3cfd333d6a1 |

The Gerbers carry their creation date, so the zip, PDFs and manifest change on every export; the manifest binds them
to the board instead.

## 6. Open

* Owner acceptance: `docs/R12_VALIDATION.md` (A-1 … A-10, the allowlist, D-R12-81, SH retention, the port voltage,
  the U9 feed width).
* ~~O-R12-25 (U9 feed 0.4 mm IPC flag), O-R12-26 (PORT_4V8 at the ports under load)~~ closed in §7; O-R12-27 (J122's
  note).
* Stage E records are written (`docs/M3_R12.md`, `docs/R12_VALIDATION.md`, `docs/R12_VEHICLE_HANDOFF.md`); no review
  round (stage F) has run; no firmware, physical, electrical or JLC DFM test.
* After any copper or placement change: rerun `m3_design/r12_legends_aid.py` on the routed board (r12_post fails closed
  when an applied item no longer matches), then `m3_design/r12_stageD.py` and `tools/r12_hotplug.py` on a filled copy.

## 7. Port-fix pass (branch `r12-port-fix`, D-R12-83 … -85, 2026-11-05)

Three changes, each recorded in `R12_DECISIONS.md`:

* **D-R12-83, PORT_4V8 setpoint (O-R12-16, -26).** R401 → 10k 0.1 % 25 ppm/K (YAGEO RT0402BRD0710KL, C190095, the one
  new Extended code), R404 4.7k → 5.1k (C25905, already on the BOM). No 1 % pair and no feed width could hold
  4.5–5.0 V at the drift corner. Window 4.603–4.938 V initial, 4.571–4.972 V drift; ports ≥ 4.561 / 4.529 V under
  0.561 A (Calculation / Inference: drift and load budget; the LR900-F's limits also an Inference).
* **D-R12-84, U9 feed and output (O-R12-25).** U9 0.3 mm east, C88 on the bar line between C96 and U9; the feed is
  0.8 mm except U9.5's 1.3 mm 0.4 mm pin entry; U9 OUT 0.8 mm into C82.1, 0.45 mm via stubs. U9's EN, OVLO, FAULT_N,
  DVDT, GND and ILIM copper redrawn 0.3 mm east on the same topology. The legend aid was re-run on the routed board:
  only U9's designator, pin-1 dot and Fab text and C88's Fab text moved (Measured, `diff`).
* **D-R12-85, everything JLC-assembled (owner).** C84 → Honor HV1E477M0810PZ (C5246546, reflow-rated 255 °C peak,
  new land `M3_CAP_D8_SMD` = R11's copper plus paste); LS120 to the JLC BOM / CPL as THT; circuit.json owner_fit empty,
  check_r12 S-4 refuses any owner-fitted part, no owner BOM is written.

**Result (Measured).** `m3_design/r12_build.sh` twice: PCB `d6e4f7ee0fc3c5d72176493717eb692316e84a21ac892437b56f649e8e76fc64`
both times, exit 0. KiCad DRC 0 violations, 0 unconnected, 0 parity; r12_sch_check OK (187 parts); fit_check r12 OK;
check_r12 every rule OK in the strict tier (S-1 … S-9, K-legends, K-reference, K-region, K-plane, K-fill); route_check
r12 0 failing, 2 allowlisted, 13 non-critical leftovers (the same 13); 1208 tracks, 414 vias. Fab: JLC BOM 58 lines,
178 JLC parts = 178 CPL rows (176 SMT, 2 THT: J121, LS120), all Top: 174 rebuilt from JLC footprints,
4 placement-only (R150–R153); worst residual 0.491 mm, LS120 0.0 mm, C84 0.25 mm; no owner BOM;
F paste 579 flashes on 579 pasted pads of 176 parts;
manifest bound. `tools/test_r12_check.py` 50 OK (`R12_BOARD_REQUIRED=1`), `tools/test_r12_fab.py` 15 OK,
`tools/test_r12_stageD.py` 4 OK. Analyses re-run: `stageD_analysis.md` §10.

**Historical cost and stock (current cost: [stageE_relayout.md §5](stageE_relayout.md),
D-R12-110; Preferred Extended waiver now applied).**

**Cost and stock (Live, `fab/cost_check_2.json` / `_5.json` 2026-11-05T19:19:44Z / 19:21:01Z, stock 19:19:05Z /
19:20:23Z, Economic one-sided).** 58 codes (22 Extended / 36 Basic), **none short and none thin** at 2 or 5 boards
(orderable = min(stock, canPresaleNumber), an Inference about JLC's field). Parts $32.74 per board (C84 and LS120 now
included in the JLC order; they were priced before too), feeder 22 charged codes × $3.07 = $67.54 per order (+3 codes:
C190095, C5246546, C96256). REQUIREMENTS M3 metric (parts + feeder per board): **$66.51 at 2 boards, $46.25 at 5
boards** against the $84.41 cap (was $61.88 / $44.38).

All-in (Calculation / Inference: U1-only X-ray count; Live figures; setup / stencil $9.71; SMT joints $0.0016 × 579 pasted pads per board; THT
joints $0.0164 × 4 per board (J121, LS120) plus $3.58 hand-soldering labour per order; bare PCB $25.10 for 5 pcs;
cost_study.md's figures, Live 2026-11-04; shipping, tax and attrition excluded). Round-2 correction D-R12-105 adds minimum U1-only
X-ray $3.28 / $8.20 at 2 / 5 boards using JLC's 2026-11-06 fee schedule; the dated parts / feeder inputs stay:

| Order | JLC parts | Feeder | Setup + stencil | SMT joints | THT joints + labour | Bare PCB | X-ray (U1 only) | **Total** | Per board |
|---|---|---|---|---|---|---|---|---|---|
| 2 boards | $65.48 | $67.54 | $9.71 | $1.85 | $3.71 | $25.10 | $3.28 | **$176.67** | $88.34 |
| 5 boards | $163.70 | $67.54 | $9.71 | $4.63 | $3.91 | $25.10 | $8.20 | **$282.79** | $56.56 |

Before X-ray, the preceding stage's subtotals were $164.08 / $265.10 plus about $0.40 per board of owner-bought parts.
The r12_plan targets were ≤ $170 / ≤ $295: with U1-only X-ray, this dated 2-board order is $6.67 over.
Counting U1 / U4 / U5 / U6 / U9 gives $189.79 / $295.09–303.29, above both targets (Calculation / Inference:
qualifying count and fee tier); confirm JLC's quote, including possible D402 / Y1 fees.

**Current board cost (D-R12-110, -151; R12F7-TRI-12: this paragraph quoted round 5's run until round 7).** See
[stageE_relayout.md §5](stageE_relayout.md) and [M3_R12 "Cost and stock"](../../../docs/M3_R12.md#cost-and-stock): the
Live run of 2026-11-07T14:15:13Z / 14:16:33Z on the 88 mm `82eddc69…` (`fab/cost_check_2.json` / `_5.json`, with the
Preferred Extended waiver). Parts + feeder **$64.86 / $45.52** per board at 2 / 5 boards; minimum all-in
**$173.39 / $279.19** with U1-only X-ray, $3.39 over the two-board target. Five X-ray parts give **$186.51 /
$291.49–299.69**, straddling $295 at five boards (Calculation / Inference: qualifying X-ray count and tier; the bare PCB
is cost_study.md §2.1's Live 46 × 90 ENIG 0.5 oz quote, $25.10, R12F5-TRI-22, taken for the 88 mm board without a
re-quote, an Inference). Round 5's run (2026-11-06T17:55–17:56Z) gave $65.02 / $45.68, $173.69 / $279.93 and $186.81 /
$292.23–300.43. Confirm JLC's count and tier, including D402 / Y1, before ordering.

**Hashes (Measured, SHA-256).**

| File | SHA-256 |
|---|---|
| m3_design/r12/m3.kicad_pcb | d6e4f7ee0fc3c5d72176493717eb692316e84a21ac892437b56f649e8e76fc64 |
| m3_design/r12_legends.tsv | b0dbc38a39f7d79657907d5efce884b8441fc2208a922cbd145aa1dd9630d4d4 |
| m3_design/r12_routes.tsv | 98d767faa2b4b1ae5c38ee651b28ee73607bfea470aa1ad12590f25e446fe3d9 |
| m3_design/r12_place.tsv | ef911fe28e8ad4518d1dffb9e4c0feca745c29fd73b65b36a9432acf6614df51 |
| m3_design/r12/fab/m3_bom_jlc.csv | c884fbd7092a1a0dd5a5de12c1351aa6f5dbb543efd94797198455d1c1562493 |
| m3_design/r12/fab/m3_cpl_jlc.csv | f3b98fe7a4db0d1a0b59d6e336ca9b2c78be88a8b21aafed747af03b0f953239 |
| m3_design/r12/fab/m3_fab_manifest.json | 41e7bbd141a6af39c1532515e1cc2c4e37a86cd9c010102e3fd856f35ad43c6c |
| m3_design/r12/fab/m3_gerber.zip | 4f5c58cb975bd5a613124e2dc9b0ff0700ef345d47659ed143a1d4bfa2d9cfea |
| m3_design/r12/fab/m3_assembly_top.pdf | 952374b5eaa7133c99532c5b08bfc7bc90173a55bd8e248346b52edf4a675500 |
| m3_design/r12/fab/m3_assembly_bottom.pdf | fd6fd6d394f36c2611441a56701d4af5e6a8d20184841c7994bbe0429341a450 |
| m3_design/r12/fab/cost_check_2.json | 89cb7e8555bb9f3730799eb15ad3c2dabebfff78c57fd1fa974eb73ca15b4566 |
| m3_design/r12/fab/cost_check_5.json | ba43e8d90448f94633c7e0c9f1c6c1df1648fcfc1987879654f4fcbc5db749da |
| m3_design/r12/fab/stock_check_2.json | bb7595ee6bc6052a8c707e79fcd5252a440e529fdb9e8570c8ecee131121c16f |
| m3_design/r12/fab/stock_check_5.json | 57d8e580236ca2e772f861743cb9e05d67b566b9d8700a5ae8d9c85c1e35d94d |

`m3_design/r12/fab/m3_bom_owner.csv` is deleted (no owner-fitted parts). The cost and stock files bind the BOM / CPL
hashes above (their `inputs_sha256`).
