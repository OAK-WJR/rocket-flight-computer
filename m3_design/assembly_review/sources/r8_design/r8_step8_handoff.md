# R8 build step 8 handoff: post and fab

Step 8 of `r8_plan.md` section 3 (Strategy B): the silkscreen (`m3_design/r8_post.py`), the full board gate at the end
of the build, the fab package and its checks (`m3_design/r8_fab.sh`), the renders, and the closing of step 7's
check.sh items. Decisions D68-D73 in `R8_DECISIONS.md`; the running log is `r8_step8_progress.md`. Nothing was
committed or pushed.

## Result

- `m3_design/r8_build.sh` builds R8 from R7 (431025d) through steps 2-8 in about 8 min and now ends with
  `r8_post.py` and `tools/check.sh`; every step gate before them stays. Final board
  `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987`,
  reproduced byte for byte by two consecutive full builds with the final scripts (builds 3 and 4; and by r8_post run on
  a copy of the ground-stage board elsewhere); netlist `0cc1ed69…` unchanged (step 2's).
- **tools/check.sh exit 0** inside every build: DRC 0 (every severity), unconnected 0, parity 0, ERC 0; metadata / 3D
  audit OK; silkscreen inside the outline; check_r8 OK; route_check r8 OK (0 failing, 3 allowlisted: A8 and D51's two;
  0 leftovers); check_actuators OK; fit_check OK.
- **Step 7's open check.sh items, closed:**
  - the silkscreen DRC classes (163 on the step-7 board): r8_post redraws all board silkscreen; one finding was a
    footprint graphic (Q122's pin-1 dot on R122.2's pad) that silkscreen cannot fix: **D69** moves R122 / R123 east
    (placement amendment, ACT_EN gets one 45 deg), every gate re-run;
  - the J2 / J9 pin legends: drawn beside their connectors (check_r7.pin_legends passes);
  - the ARM1_SENSE In2 item: **D70**, the rigid CH1 link is D20's one named exemption, exact R7 segment only;
  - the fab package: regenerated and checked (below);
  - D63 / D64 recorded as owner-delegated acceptances (**D68**).
- **Silkscreen** (D71): 35 legends (GNSS / RADIO, TP30 SAFEBOOT, ARM / IGN / BAT / CAM / SWD / SERVO / PULL, the J9, J2
  and J122 pin tables, the J124 / J1 notes, terminal pin legends, J122 row numbers, M3-ASSY-R8 at B (22.9, 108.4),
  JLCJLCJLCJLC at B (21.4, 97.4)), each legend about a part within 6 mm of it with no fallback; 168 designators shown
  (6 top parts' under them on the bottom: C89, C95, Q124, R128, R133, TP30), 81 hidden and kept on Fab (R7: 90). New
  rule: no run-on text (no text ends within 0.6 mm of another on its line). Hidden: C8 C9 C18 C23 C24 C26 C31 C74 C75
  C85 C88 C91 C92 C94 C97 C99 C126 C129 C300 C302 C303 C305 C311 C312 C313 C314 D30 D31 D123 L3 L30 Q32 R13 R63 R78 R85
  R86 R91 R100 R103 R104 R105 R120 R121 R122 R123 R124 R129 R130 R132 R151 R152 R154 R155 R156 R165 R170 R172 R173 R175
  R178 R180 R182 R301 R302 R303 R304 R310 R311 R312 R316 TP83 TP87 TP89 TP90 TP91 TP121 U7 U11 U12 U13.
- **Fab package** (`m3_design/r8_fab.sh`, D72), on the final board: jlc_orient CHECK none; BOM 92 lines, byte-identical
  to R7's (`be711876…`); CPL 219 rows (`d26572d3…`); `--verify-cpl` 85 top + 126 bottom rows rebuilt from JLC's
  footprints, worst residual 0.491 mm, 8 placement-only, no errors; paste check OK (F 348 flashes on 348 pasted pads,
  B 359 on 359, no flash in the 20 dry pads of J30 / J31 and C303 / C304 / C305 / C313 / C314); manifest OK (5
  outputs); Gerber job M3-ASSY-R8, 4 layers, 1.6 mm, ENIG; renders `m3_design/assembly_review/r8_top.png` /
  `r8_bottom.png` (984 x 2184, as R7's).
- **Cost** (live JLC data, 2026-10-19 23:51Z, 5 boards): **$106.00 per board, 52 extended codes: REQUIREMENTS M3 met**
  ($126.41, 52; no code to spare). Stock: U4 (C26633007) 0 < 5, consigned as in R7; nothing else short or thin.
  check_procurement `--cost-only` OK; the full procurement gate fails on U4 until it is consigned, as in R7.
- **7.7 A DC at 0.05 mm** (in the survey, the final copper): RAW_ACT 5.94 mm F.Cu 17.5 C 1.45 mOhm; BAT_IN 7.00 mm B.Cu
  14.5 C 0.42 mOhm; ACT_FET_S 4.97 mm B.Cu 21.5 C 0.18 mOhm: equal to step 7's (D12 holds; D69 touches no 7.7 A copper).

## Scorecard (`NO_GATE=1 DC_GRID=0.05 tools/run_survey.sh`, against r8_plan section 2)

Run on build 1's board (`6e949873…`, the same copper: r8_post changes silkscreen only, asserted); a quick survey
(`NO_DC=1`) on the final board `429b6db4…` gives every non-DC row identical.

Simplicity index **16.0** (R7 = 100; target <= 35). 20 targets met, 11 missed; all 11 were already missed at step 7
(step 8 changed copper only by D69); S15's 3.4 mm is now a named exemption by decision (D70).

| Metric | R7 | R8 final | Target | Met | Cause of a miss |
|---|---:|---:|---|---|---|
| C1 gated category instances | 74 | 3 | <= 1 (A8) | no | the 3 allowlisted: A8 + D51's two GNSS limiter detours (D11's agreed fallback); 0 failures |
| C2 information instances | 252 | 93 | <= 80 | no | step 7's figure: pad_end_offcentre 42, width_change_junction 15, passes_through_pad 9, segment_inside_pad 8, u_turn 7, power_via_no_gnd 6 (no legal spot, D67), extra_bends 4, short_layer_hop 2 |
| C3 allowlisted | 45 | 3 | <= 1 | no | A8 + D51 x 2, as C1 |
| C4 leftovers | 29 | 0 | 0 | yes | |
| C5 failures | 0 | 0 | 0 | yes | |
| C6 AGENTS 3 rule instances | 9 | 1 | <= 1 (A8) | yes | |
| S1 signal track | 3355 mm | 1500.1 mm | <= 2300 | yes | |
| S4 signal layer-change vias | 217 | 55 | <= 75 | yes | |
| S6 / S7 detour | 1.396 / 1081 mm | 1.18 / 295.5 mm | <= 1.18 / <= 350 | yes | |
| S8 / S9 nets over 1.6x / 2x | 23 / 12 | 4 / 2 | 0 except keep-out-forced | no | RADIO_TXEN (2.30, U31 keep-out, D10: 1.25 on its baseline), GNSS_VCC_RF 1.91 / GNSS_LNA_EN 1.73 (U30 keep-out, D51); left: RAW_ACT_SENSE_MCU 3.80 (2.63 mm against 0.69, D33's crossover, 1.94 mm excess under the 2 mm slack) |
| S10b bends | 648 | 234 | <= 400 | yes | |
| S12 critical layer changes | 73 | 25 (0 without a GND via) | <= 32 | yes | |
| S15 In2 signal track | 901 mm | 3.4 mm | 0 | no | D70: the rigid CH1 ARM1_SENSE link, exempt in check_r8 |
| S16 In1 track | 0 | 0 | 0 | yes | |
| S17 placement MST | 2727 mm | 1642.9 mm | <= 1850 | yes | |
| P1 In1 GND coverage | 0.880 | 0.9065 | >= 0.90 | yes | |
| P3b In1 slots | 16 | 1 | <= 4 | yes | |
| P4 In2 regions | 8 | 5 | <= 5 | yes | |
| P6 In2 perimeter | 1581 mm | 1788.7 mm | <= 900 | no | missed since step 5; step 7's GND-via antipads +294 mm (D67) |
| P7 outer GND islands <= 1 via | 32 | 1 | 0 | no | D63, accepted (D68) |
| P9 / P10 GND via distance | 6.12 / 13.78 mm | 4.48 / 9.65 mm | <= 3.5 / <= 7 | no | D64 floors 4.32 / 9.42 mm, accepted (D68); P11 in the pours 2.90 |
| R1 / R3 unreferenced | 60.3 / 115.9 mm | 4.7 / 4.7 mm | <= 5 / <= 15 | yes | |
| R6b critical_reference share | 0.279 | 0.1157 | <= 0.08 | no | unchanged since step 6; no cause measured yet (step 9's absolute critical-reference item) |
| 7.7 A RAW / BAT / FET | 38.3 / 30.2 / 44.2 C | 17.5 / 14.5 / 21.5 C (5.94 / 7.00 / 4.97 mm) | <= 20 / 20 / 30 C (D12) | yes | |

## Files

New:
- `m3_design/r8_post.py`: the silkscreen stage (KIID seed 8816; runs once, refuses a board that already has the pin
  tables); asserts the 12 rigid digests and a digest of every track, via, zone (outline and fill), pad and footprint
  position; fails on an essential legend that does not fit, a legend beyond 6 mm of its part, a designator left nearer
  another courtyard or in a run-on pair, or a legend-contract issue.
- `m3_design/r8_fab.sh`: the fab package and checks; `FAB_NET=1` adds live stock, cost and the cost-only procurement
  check.
- `tools/paste_check.py` and `tools/test_paste_check.py` (5 seeded-defect tests).
- `m3_design/assembly_review/r8_top.png`, `r8_bottom.png`.
- `sources/r8_design/step8/post_report.json` (r8_post's placement evidence), `step8/paste_report.json`.
- `r8_step8_progress.md` and this handoff.

Changed:
- `m3_design/r8_build.sh`: r8_post.py and tools/check.sh at the end; header.
- `m3_design/r8_place.tsv`: R122 (18.2, 103.36) and R123 (19.15, 102.5), basis D69.
- `m3_design/r8_power.py`: ACT_EN (17.6, 101.8) -> (18.2, 102.4) -> (18.2, 102.93) -> (19.15, 102.93); RAW_PROTECTED
  starts at (18.2, 103.79) (D69).
- `tools/check_r8.py`: `RIGID_IN2` and the inner_signal exemption (D70); `tools/test_r8_check.py` +1 test (20).
- `tools/test_r5_repair.py`: the scoped-repair check reads the R5 board from git (D73).
- `tools/jlc_corrections.json`: regenerated; two "via" comments changed (proxy footprint name; same corrections).
- `m3_design/assembly_review/m3.kicad_pcb`, `fab/*` (BOM unchanged), `fab/cost_check.json`, `fab/stock_check.json`.
- `R8_DECISIONS.md`: D68-D73.

## How it was verified

- **Four full builds** from R7 (`r8_build.sh`, logs `$SCRATCH/r8_step8/build1.log` … `build4.log`), every gate OK each
  time (placement, power, nine route gates, ground, check.sh exit 0). Builds 1 and 2 gave `6e949873…`; review then
  found r8_post's re-placement holding a bottom part's designator inside its own courtyard box (from r7_post) and the
  fix showed C32; builds 3 and 4, with the final scripts, both gave `429b6db4…`. The ground table regenerates byte for
  byte from the D69 board (`make_ground.py BUILT --built`).
- **check_r8** on the final copper: OK; inner_signal `In2_rigid_exempt` 3.4 mm, nothing else on In1 / In2 signal; fence
  25 vias, openings 2.015 / 2.60 / 2.10 / 2.05 mm; strip GND reach F 3.04 / B 3.49 mm; D18 nearest 2.65 mm; D19 none;
  loader pins per D5; F10 nearest part 5.94 mm (R306-U1), line 6.08 mm; rigid 12/12; check_actuators R7's.
- **Tests** (KiCad Python): test_check_shell 2, test_dc_solve 3, test_fab_validation 23, test_fit_check 23,
  test_maze_clearances 10, test_paste_check 5, test_procurement 15, test_r5_repair 13, test_r6_check 17, test_r7_check 35,
  test_r8_check 20, test_r8_ground 11, test_r8_place 13, test_r8_power 7, test_r8_route 12, test_route_check 57: 266 tests
  in 16 suites, all OK. quality_audit/test_quality_tools 21 OK under KiCad's Python and python3.
- **Fab** (`FAB_NET=1 m3_design/r8_fab.sh`, `$SCRATCH/r8_step8/fab_final2.log`): exit 0, figures above.
- **Visual review** of the top and bottom renders after each silkscreen iteration (run-on text found and fixed).

## Reproduce

```bash
cd rocket-pcb/rocket-flight-computer-r8
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
m3_design/r8_build.sh                                          # ~8 min; ends with check.sh ("fit check: OK"), exit 0
shasum -a 256 m3_design/assembly_review/m3.kicad_pcb           # 429b6db4dc95c1a0...
FAB_NET=1 m3_design/r8_fab.sh                                  # ~2.5 min; fab package, checks, renders, cost / stock
(cd tools && for t in test_*.py; do PYTHONUNBUFFERED=1 $KPY -m unittest ${t%.py}; done)
(cd quality_audit && $KPY -m unittest test_quality_tools && python3 -m unittest test_quality_tools)
NO_GATE=1 DC_GRID=0.05 tools/run_survey.sh m3_design/assembly_review/m3.kicad_pcb /tmp/survey   # ~20 min (DC 0.05)
```

r8_post can be re-run on a copy of the ground-stage board (`--board`, with the project files beside it) and reproduces
the final board. A second pass over its own output does not reproduce it (measured on build 1's board: 6c7f5716…
instead of 6e949873…), so r8_post refuses a board that already carries the J9 / J2 pin tables; rebuild from R7
instead.

## What the next steps must know

1. **Step 9 (requalify):**
   - Bind every record to board `429b6db4…`; the fab package is bound to it by the manifest (173 inputs).
   - D69 moved R122 / R123 and redrew ACT_EN / RAW_PROTECTED's first segment (gate drive of the actuator switch, not
     pyro): include it in the power and hot-plug review; DC unaffected (figures above).
   - ORDERING section 3: the order-number mark is JLCJLCJLCJLC at B.SilkS (21.4, 97.4); the tabs (D35); U4 consigned;
     the paste checklist can cite `tools/paste_check.py`.
   - M3_R8: the hidden-designator list (81, above), the run-on rule, D70's exemption.
   - R8_VALIDATION deviation list: D68 (P7, P9 / P10), D70 (S15 3.4 mm), D51's two allowlist entries and A8 (C1 / C3),
     S8 / S9's RAW_ACT_SENSE_MCU, P6, C2, R6b, and REQUIREMENTS M2's owner acceptance for the new board.
   - AGENTS section 3 still points the silkscreen record at M3_R7 and `check_r7.legend_subjects`; STATUS.md is R7's.
2. **Code contracts.**
   - Compare KiCad footprints by reference, never with `is`: SWIG returns a new proxy per call (r7_post's
     `g is not f` is always true; harmless there, fatal in a run-on check).
   - r8_post's run-on rule lives in `RunOnSilk`: a text box added without an explicit gap is a text; pads, vias,
     bodies and graphics pass their gap.
3. **check.sh in the build** writes its reports to a fresh mktemp folder each run (`reports: …` at the end).

## Left open

1. **Scorecard misses** (soft report; table above): C1 / C3 3 (A8 + D51), C2 93, S8 / S9 4 / 2 (one not keep-out
   forced: RAW_ACT_SENSE_MCU), S15 3.4 mm (D70), P6 1788.7 mm, P7 1 (D68), P9 / P10 4.48 / 9.65 mm (D68), R6b 0.1157.
   None is new in this step; S15 is now exempt by decision (D70); the others carry the earlier steps' measured causes,
   except R6b, whose cause was not measured here (step 9's absolute critical-reference item).
2. **D70 is a judgement** between two plan rules (rigid CH1 copper over S15 = 0); the owner may prefer to re-open the
   CH1 block instead, at the cost of its R4 qualification.
3. Fab-layer designators C80 and D8 overlap at 0.3 mm on the bottom assembly drawing (information only).
4. No independent review of r8_post, r8_fab.sh, paste_check or D69-D73 was possible inside this step (r8_plan section 4).
5. JLC prices and stock change daily: re-run `FAB_NET=1 m3_design/r8_fab.sh` within 24 h of ordering.
