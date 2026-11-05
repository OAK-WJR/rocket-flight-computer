# R12 stage D: post stage, fab package, analyses and the fixes they needed (2026-11-05)

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
  0.155 mm silkscreen gap exceeds the pitch, so neighbours cannot share a face side by side. Each contact's legend sits
  on the bottom face (no parts there) in its own column, alternately outward (ink ends at the pad centre line) and
  inward (ink starts 0.2 mm past it); both alternations are tried per port and the one with fewer misses kept
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
| EN / chatter (Calculation / Inference) | single drop-out trip 8.13 ms at 5.7208 V; bench-rule worst-corner limit 7.56 ms; turn-on nominal 88 / 56 / 45 ms (R10's 30–130 ms window kept) |
| Hold-up (Calculation / Inference) | battery break 2.23–6.12 ms unshed, 6.68–11.43 ms shed; PA6 trip 0.47–1.72 ms |
| PA6 window (Calculation / Inference) | 4.62–4.95 V (4.54–5.04 V with 1 % resistors); a four-stall fire into a shorted match can reach it (firmware, O-R12-07) |
| U6 VCC (O-R12-22; Calculation) | ≥ 3.258 V initial / 3.227 V drift at U2's 1 A, margin 123 / 92 mV over 3.135 V: closed as a calculation |
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

All-in order totals (Calculation on the Live parts and feeder figures; setup / stencil $9.71 from the cost tool; SMT
joints $0.0016 each counted as the 577 pasted pads per board, manual THT joints $0.0164 × 2 for J121 plus $3.58
hand-soldering labour per order, and the bare PCB $25.10 for 5 pcs 4L 46 × 100 mm ENIG are cost_study.md's figures,
Live 2026-11-04; shipping, tax and attrition excluded):

| Order | JLC parts | Feeder | Setup + stencil | SMT joints | THT joints + labour | Bare PCB | **Total** | Per board |
|---|---|---|---|---|---|---|---|---|
| 2 boards | $65.44 | $58.33 | $9.71 | $1.85 | $3.65 | $25.10 | **$164.08** | $82.04 |
| 5 boards | $163.60 | $58.33 | $9.71 | $4.62 | $3.74 | $25.10 | **$265.10** | $53.02 |

Owner-fitted C84 + LS120 from LCSC add about $0.40 per board (cost tool's JLC prices as the LCSC estimate). Prices and
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
* O-R12-25 (U9 feed 0.4 mm IPC flag), O-R12-26 (PORT_4V8 at the ports under load), O-R12-27 (J122's note).
* Stage E records are written (`docs/M3_R12.md`, `docs/R12_VALIDATION.md`, `docs/R12_VEHICLE_HANDOFF.md`); no review
  round (stage F) has run; no firmware, physical, electrical or JLC DFM test.
* After any copper or placement change: rerun `m3_design/r12_legends_aid.py` on the routed board (r12_post fails closed
  when an applied item no longer matches), then `m3_design/r12_stageD.py` and `tools/r12_hotplug.py` on a filled copy.
