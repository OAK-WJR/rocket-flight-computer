# R8 step 4 handoff: placement freeze

**Status:** done, and the step's verification passes in full (below). Nothing is committed (the brief forbids commits).
- Branch `m3-assy-r8`, worktree `rocket-flight-computer-r8`.
- The worktree board `m3_design/assembly_review/m3.kicad_pcb` is now the R8 placement board, SHA-256 `40e516fa…`
  (`40e516fac14f310f5e5cacfab6c373e088f55caa607d331ef8acdc88b0f91acd`). It holds parts and the rigid R7 copy only; no
  other copper.
- The sheets and `schematic.net.xml` are step 2's, byte for byte (netlist `0cc1ed69…`).
- Decisions taken in this step: R8_DECISIONS **D29–D39** (read them first; summary below).

## What this step produced

| File | Content |
|---|---|
| `m3_design/r8_place.tsv` (new) | **The frozen placement.** All 203 non-rigid parts: x, y, rot, side and basis (seed, spike-a/b/c/d, legalised, or a D-number), grouped by block with a comment per block |
| `m3_design/r8_build.sh` (new) | Build start. The schematic stage (R7's sheets restored, then `r8_sch.py --netlist`), then R7's board restored, then `r8_pcb.py`, then the step gate `r8_place_check.py`. Steps 5-8 append their stages; step 8 swaps the gate for `tools/check.sh` |
| `m3_design/r8_pcb.py` (new) | Board stage (D29) |
| `m3_design/r8_legalise.py` (new) | The placement rules (D29-D31); details below |
| `m3_design/r8_keepclear.tsv` (new) | 510 routing reservations: spike copper and step-4 lanes, with net, layer and width (D31) |
| `m3_design/r8_place_check.py` (new) | Step-4 gate: 11 gates, listed under verification |
| `tools/test_r8_place.py` (new) | 13 tests: seeded defects for every legaliser rule, the pyro clearance table, and the reserved-route gate |
| `sources/r8_design/step4/make_keepclear.py` (new) | Generates `r8_keepclear.tsv` from the spike scripts plus the step-4 lanes |
| `sources/r8_design/step4/place_report.json` | The gate report on `40e516fa…` |
| `R8_DECISIONS.md` | D29–D39 appended |
| `r8_step4_progress.md` | Running log |

**`r8_pcb.py` does, in order:**
1. checks the R7 SHA;
2. sets the R8 pad nets: exactly D28's 28 pads, asserted;
3. keeps the rigid copper (check_r8 D15 selection) and removes every other track and via;
4. keeps the GND_F / GND_B / GND_In1 pours, the strip, pyro and sensor rule areas, and the placeholder F.Cu pour
   `R6_BAT_IN_crossbar_F`, and removes every other zone;
5. removes TH1–TH3 and the R7 silk of moved parts;
6. places from the table, moving the IMU / BARO rule areas with U4 / U5;
7. runs the legaliser, strictly;
8. sets the title block to M3-ASSY-R8;
9. fills natively in place, saves (board only) and asserts the 12 rigid digests.

`--propose OUT.tsv` and `--draft` are design aids.

**`r8_legalise.py` checks:**
- courtyards, outline and holes;
- pad clearances: netclass, local (bare test pads 1.0 mm, RAW_ACT pins 0.3 mm), J2 0.508 mm, pyro A–G / A2 and, between
  pads, rule H;
- R5 L10 bottom keep-outs (1.5 mm from through-hole pads, 3.5 mm from M3, 1.0 mm from pyro vias, 2.0 mm from TP122) and
  the J122 tie path;
- top washers 3.8 mm;
- the strip's per-layer nets;
- F10's 5 mm separation;
- the reservations of `r8_keepclear.tsv`, each pad against them with the project's clearance rules.

**`r8_keepclear.tsv` contents:**
- spike (a): under U1, ARM1_SENSE;
- spike (b): servo;
- spike (c): band tracks and vias, minus its divider and corridor lanes, with the moved switch legs and BAT_ENABLE;
- spike (d): RF buses, strip leads, fence row, LED lanes;
- step 4: the pyro exit lanes GATE_N / CONT to U1, RAW_ACT_SENSE, the east-face escapes 34 / 35 / 41 / 42, the pin 15 /
  17 / 18 escapes, VLOGIC's via, the CAM_PWR_EN loop round U7, the CAM_5V gap, the BAT_IN / BAT_ENABLE / RAW_PROTECTED
  routes to the moved U9 and U7.

## Decisions in one screen (details in R8_DECISIONS)

- **D29 freeze mechanism.**
  - The table is the truth; the legaliser checks it and never moves anything in the build.
  - In2 is empty until step 5.
  - One R7 F.Cu power pour stays as a placeholder. With no non-GND F.Cu pour, the native fill shifts GND_F by µm and
    strip_gcpw fails: 15 of 744 samples. This was measured again here, as spikes a/b/d found.
  - Silk: the ARM / IGN and other rigid-part legends stay (check_actuators 11); the rest goes to r8_post.
- **D30 R5 L10 strictly (1.5 mm).**
  - R7 had six exceptions, down to 0.94 mm; R8 has none.
  - Spike (c)'s R80 / R165 / R120 / D8 were nudged.
- **D31 reservations.** The DRC overlay found two inter-spike conflicts:
  - spike (a)'s C21 / C22 GND via on spike (b)'s SERVO1 lane;
  - spike (c)'s GND via on the moved BAT_IN feed.

  Both are fixed in the generator.
- **D32 RAW_ACT_SENSE divider at J122's aft end, not in spike (c)'s notch.**
  - A lane from the notch would have to cross ARM1_SENSE, the westmost corridor lane (spike a).
  - The new lane is crossing-free: B.Cu x 25.92, then y 58.1 under the servo lanes, then x 30.6, to R172 under U1's
    east pad row.
- **D33 escapes and dividers.**
  - VLOGIC divider on the top at pin 17, with VLOGIC by one via. This is the one inherent VLOGIC × RAW_ACT_SENSE
    crossing.
  - V3V3 divider at pin 18's via.
  - Pins 34 / 35 / 41 / 42 leave outward to vias.
  - CAM_5V sense divider at pin 35.
- **D34.** C100 / C93 at their own U12 pins (the seed had them crossed, 4.7 mm). LS120 nudged.
- **D35 tabs.** Five tabs, left 63–68 / 100–105 and right 8–13 / 18–23 / 105–110. **A forward window exists on both long
  edges, so the forward-rail request can be dropped.** That 5 tabs suffice is an Inference to confirm at quote.
- **D36 eFuse U9 aft of J121's L10 zone,** at (41.5, 85.5).
  - BAT_IN lane x 41.25; EN spine x 40.42.
  - C87 and TP84 on the top on the EN lane.
  - RAW_PROTECTED down the east side on F.Cu (x 45.3, then x 42.15 between J9's pads), dropping to B.Cu south of L3.
- **D37 camera eFuse U7.**
  - FLT north, OUT east.
  - CAM_PWR_EN round U7's west end, ratio about 1.3.
  - ILIM / DVDT inside that loop.
  - IN from the south-east.
  - Test pads re-homed.
- **D38.** IMU stays at D13's default; the "free" test fails.
- **D39 fit gated per category.** Six east-edge bottom parts moved 0.07–0.65 mm inward so the worst bottom-part margin
  is not below R7's.

## How it was verified

`m3_design/r8_build.sh` runs in about 10 s, ends with `R8 placement gate: OK` and exits 0. All 11 gates of
`r8_place_check.py` pass on `40e516fa…`:

| Gate | Result |
|---|---|
| rigid | 12/12 check_r8 digests equal R7, strip_gcpw included |
| legaliser | 0 violations over 203 parts |
| drc | kicad-cli DRC with `--schematic-parity`, every severity: 0 violations, 0 parity items. Allowed only: 339 unconnected items (nothing routed yet); 4 `via_dangling` on the rigid copy's open vias (exits GATE_N / CONT / ARM1_SENSE and GNSS_ANT_DC; step 6 connects them, D11 / D15); the silk classes deferred to r8_post (121 silk_over_copper, 58 silk_overlap, 5 silk_edge_clearance) |
| f10 | 0 issues. Nearest RF part to a restricted part: FB31–L3 5.28 mm. Nearest fast copper: R306–USB_DP pad 6.01 mm |
| fit | fit_check OK, every category ≥ R7 (table below) |
| tabs | the 5-tab plan is legal (windows below) |
| mst | 1632.5 mm (≤ 1850; R7 2727; plan_partial prototype 1785) |
| contract | check_r8 contract on the placed board, distances included. Only route measures wait for copper: C29's direct route, the U12 bypass routes and GND return |
| actuators | `check_actuators.py`: OK |
| sensors | IMU / BARO rule areas at R7's offsets from U4 / U5 |
| reserved | the 510 reservations drawn as copper on a copy: 0 DRC copper-rule violations (clearance, shorts, holes, edge, crossings) |

**Fit against R7** (fit_check on c872a3d3, measured this step):

| Category | R7 | R8 |
|---|---:|---:|
| Overall bore minimum (J9 mated) | 0.028 mm | 0.028 mm |
| J122 mated | 0.71 mm | 0.71 mm |
| J3 | 0.89 mm | 0.89 mm |
| C84 | 0.11 mm | 1.37 mm |
| Worst bottom part | 2.34 mm (C74) | 2.36 mm (C91) |
| Nearest bottom item to a support | 4.150 mm | 4.701 mm (U5) |
| Nearest top item to a support | 5.008 mm | 5.008 mm (TP30) |
| J121 / J124 wire room | 6.3–6.9 mm | unchanged (rigid) |

**Tab windows:**
- left y 0.5–6.0, 48.5–77.25, 86.25–117.5;
- right y 0.5–25.5, 104.25–117.5;
- R7: none forward of y 71.5.

**Other checks:**
- **Byte-identical rebuild:** two consecutive `r8_build.sh` runs give the same board SHA (`40e516fa…`) and the same
  netlist SHA (`0cc1ed69…`). The sheets equal step 2's outputs byte for byte (`shasum` diff empty).
- **Tests** (KiCad Python): `test_r8_place` 13 OK. Each legaliser rule fires on a seeded move:
  - courtyard, L10, the TP 1.0 mm clearance, rule H (C122.1 beside R177.1), a reservation, F10, strip content, tie
    path, washer;
  - the pyro clearance table;
  - the reserved gate on a conflicting reservation.

  `test_r8_check`, `test_route_check`, `test_fit_check`, `test_check_shell`, `test_dc_solve` and `test_r7_check` are
  all OK.
- **Full `check_r8`** on the placed board: 26 findings, every one for a later step:
  - strip fence row and strip GND reach (steps 6/7);
  - In2 GND under the strip, launches and U31 (step 5);
  - J2 / J9 pin legends (r8_post);
  - C29 / U12 bypass routes (step 6);
  - the rigid ARM1_SENSE In2 link (open item 1).

  It reports no pin-map, pull, loader, F10, rigid, inner-power, gate-servo or TH finding.

## Reproduce

```bash
cd rocket-pcb/rocket-flight-computer-r8
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
m3_design/r8_build.sh                                         # schematic + board + gate, ~10 s; ends "R8 placement gate: OK"
shasum -a 256 m3_design/assembly_review/m3.kicad_pcb          # 40e516fac14f310f...
(cd tools && PYTHONUNBUFFERED=1 $KPY -m unittest test_r8_place)
PYTHONUNBUFFERED=1 $KPY -I m3_design/r8_place_check.py --report /tmp/place.json
PYTHONUNBUFFERED=1 $KPY -I tools/check_r8.py m3_design/assembly_review/m3.kicad_pcb   # 26 later-step findings
# regenerate the reservations (only when spike / step-4 lane geometry changes), on a placed board:
PYTHONUNBUFFERED=1 $KPY -I m3_design/assembly_review/sources/r8_design/step4/make_keepclear.py \
    m3_design/assembly_review/m3.kicad_pcb m3_design/r8_keepclear.tsv
```

**Design workflow for a table edit.** Edit `r8_place.tsv`, then run
`PYTHONUNBUFFERED=1 $KPY -I m3_design/r8_pcb.py --board <copy of R7 board with m3.kicad_pro/.dru beside it> --draft`.
`--propose OUT.tsv` lists legal nudges. Then run the gate. The scratch tools used in this step (viewer, overlay, table
builder) are in the session scratchpad `r8_step4/`; they are not needed to rebuild.

## What the next steps must know

1. **Steps 5–7 route against `r8_keepclear.tsv`.** It is the copper the spikes proved plus the step-4 lanes, and it
   fits the frozen parts (gate `reserved`).
   - Port it rather than re-inventing it: `spike_geom.copper()`, `servo_route.route()`, `battery.copper()`,
     `rf_route_r8` lanes, `make_keepclear.MANUAL_*` / `C_MOVED_*`.
   - Where a route changes, change the table generator and rerun the gate.
   - Once real copper exists, the reservation rows it replaces can go.
2. **Step 5 (power).**
   - Replace `R6_BAT_IN_crossbar_F` (the D29 placeholder) with the band's F.Cu pours and re-assert strip_gcpw. Spike
     (c) passed 12/12 with its pours.
   - Spike (c)'s RAW_ACT west region no longer needs the divider notch (D32). The RAW_ACT tap to R177 comes from
     J122.11.
   - The BAT_IN B.Cu feed is the lane x 41.25 down to U9 at y 86.6 (D36), no longer x 40.75.
   - RAW_PROTECTED is a long net. Step 5 or 6 can carry it on the reserved F.Cu east lanes, or as an In2 island along
     the east edge (D20 allows power tracks on In2).
3. **Step 6 (signals).** The arrangements below are placement-backed and the routes are reserved. Remaining inherent
   items, each within route_check's VIA_SLACK (one under-and-back crossing per net) or solvable on In2:
   - **USB_LIMITED, U10 (west) to U11 (east).** It crosses the middle band: pyro corridor, servo lanes, CAM_PWR_EN
     loop. Use a 2-via hop or an In2 island.
   - **Camera UART.** RX / TX swap order between U1 (RX north) and J9 (RX south). Cross under R100's or R101's 0603
     body, between its pads (0.85 mm gap), or with one 2-via hop.
   - **BAT_FAULT_N, U9 to pin 28.** A clear path: F.Cu down x 43.0 to y 52, then west, staying north of RAW_PROTECTED's
     jog at y 49.8–51.5. Not reserved.
   - **LOGIC_SOURCE_ST (pin 29).** Use its via at once; U11 is on the bottom.
   - **NRST's tail to J2.3.** J2.3 is reachable only from the board-edge side (x ≈ 0.8), because J2's 0.508 mm contact
     rule closes the other sides. Spike (a)'s tail to R7's J2 position was dropped from the reservations.
   - **SWD.**
     - SWCLK leaves pin 76 north along x 14.4 to y 40.1, then west through the corridor between J3's pads (top
       38.97) and the LED rows (41.2).
     - SWDIO leaves pin 72 aft, then west south of SWCLK, then north on the western vertical (x 4.3) to J2.2.
     - SWCLK takes x 4.9 to J2.4.
     - Checked by hand: no crossing.
   - **CAM_PWR_EN's loop round U7 (x 28.0)** is reserved; keep its ratio below 1.6.
4. **Step 8 / 9.**
   - r8_post redraws the silkscreen, including the J2 / J9 pin legends that check_r8 now flags.
   - TP84 and C87 are on the top side: coating mask, ORDERING probe list.
   - ORDERING tabs: D35, with no forward rail.
   - The fit and F10 figures change from R7's; see above.

## Left open (not escalated; none is unsafe or changes a requirement's intent)

1. **D15 against D20** (spikes a, c, d). check_r8 `inner_signal` flags the rigid CH1 block's ARM1_SENSE In2 link,
   3.4 mm at (14.55, 94.15–97.55), which D9 / D15 make rigid. The full check_r8 can never pass until the orchestrator
   decides: a named D20 exemption for that rigid segment, or a decision. This is not a step-4 gate.
2. **strip_gcpw fragility (D29).** The digest depends on a non-GND F.Cu pour existing, because of fill-path noise.
   Tolerance or quantisation is a check_r8 question for the orchestrator. This step changed no check.
3. **JLC acceptance of 5 tabs on a 118 mm board** without the forward rail is an Inference, to confirm at quote.
4. **No independent review** of the step-4 tools and table was possible inside this step (r8_plan §4). The
   orchestrator schedules it.
