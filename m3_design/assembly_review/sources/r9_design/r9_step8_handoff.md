# R9 step 8 (ground): handoff

Status: **built and gated; R6b reworked to 0.1022 (better than R8's 0.1107); the 0.08 done row and P7 = 0 stay recorded
misses for the owner.** The ground is built by `m3_design/r9_ground.py` (the board-wide GND pours, the frozen stitching
table `m3_design/r9_ground.tsv`, the crystal's In2 GND plane, every via's unconnected inner pads removed) and gated by
`m3_design/r9_ground_check.py`; both run in `r9_build.sh` after the step-7 stages. Two full builds (stages 0-35, every
gate OK) reproduce every built file byte for byte: board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`89ddea8d7c396dc4e9825c25ad9fa7da2de84d8da971a0736d9db7f4d26fb001`. Nothing committed or pushed. Decisions:
`R9_DECISIONS.md` D-S8-01 ... D-S8-20 (session 2: D-S8-17 replaced, D-S8-19 and D-S8-20 new, D-S8-02 and D-S8-18
extended). Log: `r9_step8_progress.md` (sessions 1 and 2). Evidence: `step8_evidence/`.

**Coordinator decisions applied (session 2).** (1) P7 = 9 single-via GND pockets (D-S8-15): accepted as recorded items
for the owner's deviation list; no pour trims added. (2) R6b 0.1732 not accepted: reworked (section 5).

**Environment.** Still no logged-in GUI session: kicad-cli DRC runs through step 6's scratch shim and `r9_build.sh` is
replayed stage by stage by its runner (D-S6-14; `r9_step6_handoff.md` section 6). Both are in `<scratch>/s6/`
(`inj/nomouse.dylib`, `tools/build.py`). The scratch `inj/bash` copy no longer runs (killed on launch); run the survey
with `/bin/bash` (its DRC-free parts) and the DRC users from KiCad's python with the shim in the environment.

## 1. Produced

| File | What |
|---|---|
| `m3_design/r9_ground.py` | The builder: grows step 4's F.Cu / B.Cu / In1 strip GND pours over the board (D-S8-01), draws the table (GND vias 0.5 / 0.3 and GND straps only; no trims, D-S8-03), then (session 2) `xtal_plane`: the rule area Y1_In2_keepout becomes an In2 track keep-out that no longer bars fills, and R9_GND_In2_Y1 (GND, priority 11, R9_GND_In2's settings) fills it, its outline the area less `xtal_outline`'s notches (one, under NRST's B.Cu run to C24.1) (D-S8-20); `strip_via_pads`: every via REMOVE_EXCEPT_START_AND_END (D-S8-19); fills, asserts no via re-netted and no table via in a non-GND outer fill. KIID seed 9908 |
| `m3_design/r9_ground.tsv` | 187 rows: 183 GND vias (return 11, pad 3, grid 89, cover 36, island 14, patch 27, strap 1, reach 2), 4 strap tracks (C17.2, C24.2). Session 2: regenerated after the aid's corridor fix (5 rows differ, all round the dropped cover via (25.65, 59.95)) |
| `m3_design/r9_ground_aid.py` | Design aid (not in the build) generating the table from the step-7 board; `--check` regenerates and compares (reproduced from the build's own stage-33 board). Session 2: no antipad may reach into a 7.7 A corridor from just outside it (D-S8-02) |
| `m3_design/r9_ground_check.py` | The step gate: table (+ the crystal plane's settings / outline, the rule area's flags, every via's pad mode), drc, route, stitch, in2, **xtal** (new: In2 under the crystal GND only, the plane one piece >= 90 % of the area with >= 2 GND vias), islands (WEAK_EXCEPT, D-S8-15), reach (P9 <= 3.5, P10 <= 7.35, D-S8-16), reference (count <= 3,206 and no unreferenced sample outside its own via antipad in the R6 or the extended set but REF_STRAY's one, D-S8-17), pyro, contract (check_r9 but M-2 / K-legends), actuators |
| `m3_design/r9_power_check.py` | `gate_in2` accepts IN2_LATER (R9_GND_In2_Y1, GND only; optional at steps 6-7) |
| `m3_design/r9_build.sh` | step-8 header text (no command changed) |
| `tools/test_r9_ground.py` | 18 tests (session 2 +6: a via keeping its inner pads, the rule area barring fills again, the plane's priority, the plane's notch and outline, the plane on a foreign net, a stale REF_STRAY entry) |
| `tools/test_r9_power.py` | +1 test: the IN2_LATER zone must stay GND |
| `step8_evidence/` | session 2: `r9_ground_check.{json,txt}`, `check_r9_full.{json,txt}`, `rule_h_seed.{json,txt}`, `r9_scorecard.{md,json}`, `x_metrics.json`, `refaudit*.txt`, `build_sha256.txt`, `build.txt`, `tests.txt`, `aid_check.txt`, `step8_deltas.txt`, `reference_causes.{py,txt}` (per via side, one- / multi-branch), `unground.py` (also undoes the crystal plane and the via pads); `reach_floor.{py,txt}` from session 1 |

## 2. Verification (board `89ddea8d…`)

| Item | Result |
|---|---|
| Build | two full replays, every stage rc 0 (steps 2-7's gates included), byte-identical sheets, netlist, DRU, variants and board |
| Step gate | `r9_ground_check.py`: all 12 gates OK |
| DRC + parity | 0 violations but the silkscreen classes (step 9), 0 unconnected (GND included), 0 parity |
| route_check r9 | 0 failing, 0 allowlisted; S13 (critical layer changes without a GND via) 0 |
| check_r9 | fit OK, plate f1 256.6 Hz, seeded rule-H suite OK; 39 rules OK, including P-0 ... P-11, R-1 ... R-13 (R-5 GCPW cross-section, R-7 fence and strip stitching), M-2, M-5, M-6, M-7, LC-1, K-copper, K-power-pyro, K-inner; K-legends FAIL: 22 legends, step 9's r9_post.py (D-S8-18) |
| Pyro | step-5 functions on the built board OK; stitching vias >= 0.75 mm from bus / igniter / drain copper, >= 0.5 mm from the other pyro / arming nets; via-pad removal only widens clearances on In1 / In2 |
| Power | no stitching via in a power pour or reaching a 7.7 A In2 corridor (now tested with the true antipad); In2's regions one piece each; DC (survey, 0.1 mm): RAW_ACT / BAT_IN / ACT_FET_S neck rises 12.8 / 12.1 / 20.8 C (D12 20 / 20 / 30) |
| **R6b** | **0.1022** (3,206 / 31,359; R8 0.1107, session 1 0.1732). Done row 0.08 missed; floor with the 12 unavoidable critical vias 0.091 (D-S8-17) |
| Extended reference set | 3,931 / 83,715 unreferenced, all own via antipads but USB_DM's one edge sample; R3 (centre-line unreferenced, own antipads excluded) 0.0 (session 1 2.8) mm; R8 5,944 |
| P7 | 9 recorded pockets (D-S8-15; coordinator: accepted as recorded items) |
| P9 / P10 | 3.45 mm (met) / 7.32 mm at (31.25, 91.25), the BAT_IN battery entry (recorded cause, D-S8-16) |
| X8c pour trims | 0 (met) |
| Crystal plane | R9_GND_In2_Y1 covers 0.961 of the area in one piece, 6 GND vias, no foreign fill (U1.6's 3V3 via ring 0.05 mm across the edge, as before) |
| Scorecard (0.1 mm DC) | step-8 rows: P9 3.45 (met), P10 7.32 (recorded cause), P7 9 (recorded pockets), R6b 0.1022 (0.08 missed; better than R8's 0.1107), X8c 0 (met); P6 1484.0 mm (session 1 1533.3; D-S6-13's miss), P1 In1 coverage 0.9094, P3b In1 slots 4 (8), M2 adjacency 33 (39), index_r9 84.8 (85.6). The other misses are steps 3-7's, unchanged (step8_deltas.txt) |
| Tests | 25 suites, 458 tests OK, none skipped (run on build 4's board, byte-identical to build 5's); quality_audit 21 OK under both pythons; audit_artifacts exit 0 |

## 3. Reproduce

```bash
R=rocket-pcb/rocket-flight-computer-r9
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
NP=<python3 with numpy>                                       # the parent project's cfd/venv/bin/python3
NUMPY_PY=$NP $R/m3_design/r9_build.sh                         # with a GUI session (kicad-cli DRC), ~25 min
# without a GUI session (D-S6-14): the scratch runner replays the script's own lines with the shim
$KP <scratch>/s6/tools/build.py --from 0 --to 35              # 34 / 35 are r9_ground.py / r9_ground_check.py
(cd $R && DYLD_INSERT_LIBRARIES=<scratch>/s6/inj/nomouse.dylib $KP -I -B m3_design/r9_ground_check.py --report out.json)
# the table from the step-7 board (the build's state after stage 33, or step8_evidence/unground.py BUILT OUT)
(cd $R && $KP -I -B m3_design/r9_ground_aid.py STEP7.kicad_pcb out.tsv --check)
(cd $R && $KP -I m3_design/assembly_review/sources/r9_design/step8_evidence/reference_causes.py m3_design/assembly_review/m3.kicad_pcb)
(cd $R/tools && DYLD_INSERT_LIBRARIES=<scratch>/s6/inj/nomouse.dylib $KP -B -m unittest test_r9_ground test_r9_power \
    test_r9_route test_r9_rf test_r9_place test_r9_pyro test_r9_sch test_r9_check)
(cd $R && NO_GATE=1 DC_GRID=0.1 NUMPY_PY=$NP bash tools/run_r9_survey.sh m3_design/assembly_review/m3.kicad_pcb survey)
```
A changed table is regenerated with the aid and frozen again (the aid's output must equal the table: `--check`).

## 4. What step 9 (post and fab) must know

- **Silkscreen is step 9's** (D-S8-18): K-legends lists 22 legends and DRC shows the silk classes; r9_post.py places
  legends off the 183 GND vias too (they are tented).
- **Planes:** the GND pours are R9_GND_F / _B / _In1 (the step-4 strip zones, grown) and, on In2, R9_GND_In2,
  R9_GND_In2_strip and the crystal plane R9_GND_In2_Y1 (D-S8-20). Every via carries pads only on the layers it connects
  (D-S8-19): any via step 9 adds must get the same mode (the table gate fails a via with pads on every layer), and any
  copper change after step 8 must re-run `r9_ground_check.py` (islands, reach, reference and the crystal plane are
  measured on the copper; xtal_outline's notches follow the reference-set B.Cu tracks).
- **Fabrication:** inner layers now show bare via holes (no ring) where a via does not connect; the planes keep the DRU's
  0.25 mm hole clearance (JLC inner-layer via hole to copper >= 0.2 mm). The Gerber review in step 9 should expect it.
- **Moved parts and test pads** from session 1 (bench and BOM text, step 10): the east column TP87 LOGIC_SOURCE_ST 67.8,
  TP81 RAW_PROTECTED 70.4, TP74 GND 73.0, TP88 GND 75.6, TP83 VLOGIC 78.2, TP85 80.8, TP89 83.4 (x 44.6, top); TP90
  (33.85, 58.65); R105 turned 180 at (31.94, 47.55); R182 at (30.5, 54.6).
- **Step 10 records:** the crystal's local ground plane (AN2867 section 5.1) adds about 0.37 pF per HSE node (Inference),
  CL about +0.19 pF: carry docs/CIRCUIT_REVIEW.md's HSE bench check (frequency error by MCO, a cold start; C25 / C26 a
  bench variable) into ORDERING's bench list with the plane named.
- The scorecard's other misses are steps 3-7's and unchanged by step 8 (step8_deltas.txt).

## 5. Open (for the owner)

- **R6b 0.1022 against <= 0.08** (D-S8-17): better than R8's 0.1107 (the coordinator's floor), the 0.08 row missed.
  Every remaining sample is inside an own antipad of the 12 critical layer-change vias (one per QSPI / HSE / SPI1 /
  IMU_CS net, the minimum with U3 / Y1 / U4 under U1): 21 one-branch sides 2,550 samples, three two-branch sides 655
  (HSE_OUT's in-line via, R8 D86; QSPI_NCS's R10 branch; IMU_CS's T to R11, both boxed in the IMU knot), plus USB_DM's one
  edge sample at CC1's via. The floor at the board's via rules is 0.091; 0.08 would need fewer critical vias (parts off
  the bottom) or smaller vias / hole clearance than R8's rules (0.45 / 0.2 vias measured 0.0888, not adopted).
- **Crystal plane (D-S8-20)** changes R5 V1's void into AN2867's local ground plane (the In2 track keep-out stays). It is
  the one lever past R8 (without it 0.1396). The owner may restore the void (XTAL_ZONE and the rule area's flags in
  r9_ground.py) at that cost.
- **P7 = 9 against 0** (D-S8-15): accepted by the coordinator as recorded pockets for the owner's deviation list.
- **P10 7.32 mm** is the brief's recorded-cause case (BAT_IN battery entry, D-S8-16).
- **Minor:** the 7 power layer changes without a GND via within 1.5 mm (information; AGENTS 3 asks it of critical nets
  only). RAW_PROTECTED -> U7 77.1 mOhm, 0.8 mOhm above R8 D49 (D-S8-09; no limit). CAM_FAULT_N one bend more (D-S8-07).
- **Scratch:** the shim and runner in `<scratch>/s6` stay needed without a GUI session; `<scratch>/s8b` holds session
  2's throwaway scripts and `<scratch>/r9/s7` the step-7 snapshots (delete when the step is accepted).
