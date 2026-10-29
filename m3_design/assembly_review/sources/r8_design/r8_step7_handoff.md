# R8 build step 7 handoff: ground

Step 7 of `r8_plan.md` section 3 (Strategy B): the GND stitching, built by `m3_design/r8_ground.py` from one table,
`m3_design/r8_ground.tsv`, after the links gate, and gated by `m3_design/r8_ground_check.py`. Decisions D62-D67 in
`R8_DECISIONS.md`; the running log is `r8_step7_progress.md`. Nothing was committed or pushed.

## Result

- `m3_design/r8_build.sh` now builds R8 from R7 (431025d) through steps 2, 4, 5, 6 and 7 in about 6.5 min. Every gate
  passes: placement, power, the nine route gates and the new ground gate. Final board
  `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `52c643d679e54a6281aa89f6c21110d34ee1c92b61208fba03b2a79e8afb0dde`,
  reproduced byte for byte by three consecutive full builds; netlist `0cc1ed69…` unchanged (step 2's).
- **The GND copper** (200 table rows):

  | Basis | Items | What |
  |---|---:|---|
  | fence | 25 vias | spike (d)'s fence row on y 23.3 (D16) |
  | stitch | 2 vias | spike (d)'s stitches above the fence |
  | c24 | 1 via, 1 track | spike (a)'s C24.2 GND stub under U1 |
  | trim | 6 rule areas | R8_POUR_TRIM_G1-G6: GND pieces no second via can reach (D65) |
  | return | 17 vias | a GND via within 1.5 mm of power-net layer changes that had none |
  | grid | 88 vias | the 4 mm stitching grid (x 3 + 4k, y 27.3 + 4k), snapped to the nearest legal spot within 1 mm |
  | cover | 57 vias | greedy cover of the outer GND pours to 3.0 mm |
  | island | 3 vias | second vias for weak islands |

  All vias are 0.5 / 0.3 mm GND; 193 in all (the board's GND vias: 234 → 427, plus 10 plated GND holes).
- **Every critical layer change has its GND via** (route_check critical_via_no_gnd: A8 only, D9; S13 = 0).
- **Pour cleanup:** route_check has no pour finger, sliver or pad pour cut (step 6's last failure, the I2C finger over
  U5, is trimmed). C6 (AGENTS 3 rule instances) = 1 = A8, the plan's "0 except A8".
- **Fence:** 25 vias, four openings 2.015 / 2.60 / 2.10 / 2.05 mm, each crossed by its lanes; other gaps <= 2.0 mm (D16,
  D67). Strip GND reach F.Cu 3.04 / B.Cu 3.49 mm (limit 4.0).
- **check_r8:** only later-step findings remain: the J2 / J9 pin legends (step 8) and the rigid ARM1_SENSE In2 link
  (step-4 open item 1, the orchestrator's).

**Scorecard** (`NO_DC=1 NO_GATE=1 tools/run_survey.sh`, R7 → step 6 → step 7):

| Row | R7 | Step 6 | Step 7 | Target |
|---|---:|---:|---:|---|
| C6 rule instances | 9 | 2 | **1 (A8)** | 0 but A8: met |
| C2 information | 252 | 109 | 93 | <= 80 (power_via_no_gnd 22 → 6) |
| P7 outer GND islands <= 1 via | 32 | 11 | **1** | 0: missed by the D4.2 pocket (D63) |
| P9 GND via distance p95 | 6.12 | 11.55 | **4.48** | <= 3.5: infeasible, floor 4.32 (D64) |
| P10 max | 13.78 | 23.51 | **9.65** | <= 7: infeasible, floor 8.67 for any placement (D64) |
| P11 p95 inside the outer GND pours | 5.09 | 10.03 | **2.90** | <= 3.5: met (max 5.89) |
| P6 In2 perimeter | 1581 | 1495 | 1789 | <= 900: missed since step 5; +294 mm of GND-via antipads |
| R1 / R3 / critical_reference | 60.3 / 115.9 / 0.279 | 4.7 / 4.7 / 0.116 | unchanged | |
| Simplicity index | 100 | 19.1 | 14.4 | <= 35 |

**7.7 A DC** (`tools/run_dc.sh`, 0.1 mm, on a board byte-identical to the final one): RAW_ACT 5.90 mm F.Cu 17.6 °C
1.45 mΩ; BAT_IN 6.86 mm B.Cu 14.8 °C 0.42 mΩ (step 6: 0.41); ACT_FET_S 4.77 mm B.Cu 22.5 °C 0.19 mΩ. Necks and rises equal
step 6's. At the 0.05 mm qualification grid on the final board: RAW_ACT 5.94 mm 17.5 °C 1.45 mΩ, BAT_IN 7.00 mm 14.5 °C
0.42 mΩ, ACT_FET_S 4.97 mm 21.5 °C 0.18 mΩ (step 5's D49: 5.93 / 7.00 / 4.97 mm, the same rises). D12 holds.

## Files

New:
- `m3_design/r8_ground.tsv`: the GND copper table (item, net, layer, size, x0, y0, x1, y1, basis, points).
- `m3_design/r8_ground.py`: the build stage. It draws the table once (refuses a second run), with KIID seed 8815, a native
  fill, a re-net check of every new via and the 12 rigid digests asserted.
- `m3_design/r8_ground_check.py`: the step-7 gate, 14 gates: rigid, table, drc, route, islands, reach, power, trims,
  pyro, inner, in2, contract, l10, reserved (its docstring defines each).
- `m3_design/assembly_review/sources/r8_design/step7/make_ground.py`: the design-time generator (legality model,
  order and parameters in its docstring). Deterministic; `--built` regenerates from the built board.
- `m3_design/assembly_review/sources/r8_design/step7/bounds.py`: design aid, the P9 / P10 floors of D64.
- `m3_design/assembly_review/sources/r8_design/step7/ground_report.json`: the gate report on the final board.
- `tools/test_r8_ground.py`: 11 seeded-defect tests of the stage, the gate and the legality model.
- `r8_step7_progress.md` and this handoff.

Changed:
- `m3_design/r8_build.sh`: the ground stage and gate after the links gate.
- `m3_design/r8_keepclear.tsv`: regenerated empty; step 7 builds the last 29 reservations (D66).
- `sources/r8_design/step4/make_keepclear.py`: header and message name step 7 when the built board carries it (D66).
- `tools/route_check.py`: `TRIM_PREFIXES` adds `R8_POUR_TRIM_`, so pad_pour_cut covers R8's trims, step 5's L1 included
  (D65; a strengthening). `tools/test_route_check.py`: the trim test runs both prefixes.
- `tools/test_r8_place.py`: test_reserved_route reads its reservation from a temporary table (the real one is empty, D66).
- `R8_DECISIONS.md`: D62-D67.

## How it was verified

- **Three full builds** (`r8_build.sh`): every gate OK each time; identical board SHA-256 `52c643d6…`.
- **Ground gate** (`r8_ground_check.py`, all 14 OK):

  | Gate | Result |
  |---|---|
  | rigid | 12/12 digests equal R7 (strip_gnd 176 items: no new GND via aft of y 23.5 but the fence row) |
  | table | all 200 rows on the board (vias, the C24 track, the six trims with outline, layer and fill-only flags) |
  | drc | kicad-cli DRC with parity, every severity: no violation outside the silkscreen classes (step 8); 0 unconnected (every net whole, GND included); 0 parity |
  | route | route_check r8: 0 failures, no stale / audit finding, no leftover; allowlisted exactly A8 + D51's two |
  | islands | 18 outer GND islands; all >= 2 GND vias / plated holes but the D4.2 pocket (WEAK_EXCEPT: 2.89 mm2, its one via) |
  | reach | pours p95 2.90 / max 5.89 mm (<= 3.5 / 7.0); board p95 4.48 / max 9.65 mm (<= 4.6 / 9.7 ceilings, D64) |
  | power | no step-7 via in an outer power pour, in a 7.7 A corridor's In2 island, or within 0.5 mm of pyro / arming copper |
  | trims | each R8_POUR_TRIM_G* covers GND fill only (board refilled without the trims) |
  | pyro | D18 inner_power_pyro and D19 gate_servo: 0 issues |
  | inner | no In1 / In2 track besides the rigid CH1 link |
  | in2 | D47's islands; no other net's In2 fill under CH1 pads or pyro / servo lanes |
  | contract | check_r8: only the J2 / J9 legends and the ARM1_SENSE In2 open item; fence, strip GND reach, line stitching pass; check_actuators OK |
  | l10 | D61's two exceptions only |
  | reserved | r8_keepclear.tsv empty |

- **Two-pass regeneration:** `make_ground.py BUILT --built` (removes the table's items in memory, refills) reproduces
  `r8_ground.tsv` byte for byte; so does a run on the step-6 board (b7a4d34d).
- **Unit tests** (KiCad Python): test_r8_ground 11, test_r8_route 12, test_route_check 57, test_r8_power 7,
  test_r8_place 13, test_r8_check 19, test_check_shell 2, test_dc_solve 3, test_fit_check 23, test_r7_check 35: 182 OK.
  test_fab_validation fails 2 (the R7 fab package against the moved parts; unchanged by step 7, step 8 regenerates it).
- **tools/check.sh** stops at DRC: 163 violations, all silkscreen (104 silk_over_copper, 55 silk_overlap, 4
  silk_edge_clearance: step 8); unconnected 0, parity 0, ERC 0. Its later stages, run one by one: metadata audit fails
  on the same silk DRC findings only; silk_check: silk outside the outline (step 8); check_r8: the 10 legends + the
  ARM1_SENSE In2 item; route_check OK; check_actuators OK; fit_check OK.
- **Visual review** of the via field (F / B, whole board) with a scratch viewer and a distance heat map.

## Reproduce

```bash
cd rocket-pcb/rocket-flight-computer-r8
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
m3_design/r8_build.sh                                          # ~6.5 min; ends "R8 ground gate: OK"
shasum -a 256 m3_design/assembly_review/m3.kicad_pcb           # 52c643d679e54a62...
PYTHONUNBUFFERED=1 $KPY -I m3_design/r8_ground_check.py --report /tmp/ground.json
(cd tools && for t in test_r8_ground test_r8_route test_route_check test_r8_power test_r8_place test_r8_check; do
   PYTHONUNBUFFERED=1 $KPY -m unittest $t; done)
# regenerate the table from the built board (must equal the committed one), and the P9 / P10 floors (D64)
D=m3_design/assembly_review/sources/r8_design/step7
PYTHONUNBUFFERED=1 $KPY -I $D/make_ground.py m3_design/assembly_review/m3.kicad_pcb /tmp/g.tsv --built
cmp /tmp/g.tsv m3_design/r8_ground.tsv
PYTHONUNBUFFERED=1 $KPY -I $D/bounds.py m3_design/assembly_review/m3.kicad_pcb --built      # any 3.30 / 8.67, rules 4.32 / 9.42
NO_DC=1 NO_GATE=1 tools/run_survey.sh m3_design/assembly_review/m3.kicad_pcb /tmp/survey
tools/run_dc.sh m3_design/assembly_review/m3.kicad_pcb /tmp/dc 0.1                          # ~5 min (0.05: ~40 min)
```

**After a change upstream** (placement, power or a family): the table's vias may land on new copper, and the ground
stage or gate fails loudly (re-net check, DRC). Rebuild through links (or run `make_ground.py --built` on a built
board), regenerate `r8_ground.tsv` with `make_ground.py`, rebuild, and confirm the two-pass check. A new GND piece no via
can reach shows as an island line in the generator's output: add a trim (TRIMS) or a decision.

## What the next steps must know

1. **Step 8 (post and fab):**
   - check.sh's remaining failures are all step 8's: the silkscreen DRC classes and silk outside the outline, the J2 / J9
     pin legends, the fab package (test_fab_validation), plus the ARM1_SENSE In2 open item (orchestrator).
   - r8_post's silkscreen must keep off the 193 new vias' pads (DRC silk_over_copper) like any via.
   - When the full gate (check.sh) replaces the step gates, keep r8_ground_check's checks that check.sh lacks:
     islands (P7 exception), reach ceilings, power, trims, table.
2. **Step 9 (requalify):**
   - DC: step 7's figures at 0.05 mm are above (D67); requalify on the step-8 board (step 7 adds In2 antipads in the
     BAT_IN band outside the corridor: BAT_IN 0.41 → 0.42 mΩ).
   - 28 new GND vias lie inside the PYRO_BLOCK rule area, all in GND fill and >= 0.5 mm from every pyro / arming net's
     copper: include them in the coating / leakage review.
   - RF: the fence row and its four openings, the two stitches above it, trim G5 in the strip (7 mm from both RF lines;
     strip_gcpw unchanged): the stitching review's figures (D67).
   - The scorecard misses for the owner's list: P7 = 1 (D63), P9 4.48 / P10 9.65 against floors 4.32 / 8.67 (D64), P6
     1789 mm (In2 antipads), C2 93 (> 80).
3. **Code contracts.**
   - `r8_ground.py` refuses to run if any table item is already on the board: run it once, on the links output.
   - Remove KiCad items with `board.Delete(item)`, not `board.Remove(item)`: a removed item's proxy freed by Python breaks
     SWIG's type table (GetTracks fails, or a segfault).
   - `make_ground.py` refills the board in memory (twice per legal() for the dormant-island check); it needs the project's
     .kicad_pro / .kicad_dru beside the board, or the fill changes and it stops ("a refill changed the outer GND fill").

## Left open

Every step-7 gate passes; these plan targets do not:
1. **P7 = 1, not 0 (D63).** The D4.2 pocket: D4's GND pin between the USB DM / DP flow-through lanes (D52) is enclosed
   with its one via (shared with U10.2); no second via fits, and a trim would take the pad's pour contact. A usb_swd edit
   splitting that via into two at about (9.0, 33.35) / (9.05, 34.2) is possible at marginal clearances (0.15-0.22 mm
   to DP, ring about 0.07 mm from D4.2's pad); not taken. Owner or review: accept the pocket, or take that edit.
2. **P9 / P10 targets (3.5 / 7 mm) are infeasible on step 5's 7.7 A copper (D64).** Any placement keeping the 7.7 A
   corridors whole has P10 >= 8.67 mm (the RAW_ACT west pour is RAW_ACT on three layers); under D62's rules the floors
   are 4.32 / 9.42 mm, and the board reaches 4.48 / 9.65. The gate holds the stitchable area (the outer GND pours) to the
   plan's numbers: p95 2.90 / max 5.89 mm. For the owner's list of measured misses (r8_plan section 4).
3. **Six power-net layer changes** still have no GND via within 1.5 mm (no legal spot; route_check information only):
   3V3 (29.25, 39.0), CAM_IO_3V3 (35.45, 48.5), 3V3A (26.5, 54.4), VBUS (11.1, 33.8), CAM_5V (40.75, 41.4), VLOGIC
   (35.5, 66.6).
4. **Inference** (D62): a tented via under a part's body is acceptable to JLC; the body rule keeps them clear anyway.
5. No independent review of the step-7 generator, gate and table was possible inside this step (r8_plan section 4).
