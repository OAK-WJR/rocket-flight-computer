# R9 step 1 (gate first): handoff

Step 1 of `r9_plan.md` §4: the rule-based gate R9 is built against. Nothing on the board changed: the worktree's
`m3.kicad_pcb` is still R8 (`cc044ea0…`), so `tools/check.sh` now fails on it by design (R8 does not meet the R9
contract). Nothing committed or pushed. Decisions: `R9_DECISIONS.md` D-S1-01 … D-S1-25. Log: `r9_step1_progress.md`.

## 1. What was produced

| File | What it is |
|---|---|
| `tools/check_r9.py` | The R9 CAD contract: LC-1, P-0 … P-11 (+ P-1b), R-1 … R-13, M-2 … M-7, F9-1, T-1 and the kept K-rules (contract, legends, copper hygiene, D18 / D85 / D19 strengthened, D20 with no exemption, check_actuators pin). No rigid hash, no fixed coordinate. Every rule reports its evidence in `--report`. Reads the fit report (`--fit`), the plate model (`--plate`) and the seeded-suite report (`--seed`), each bound to the board's SHA-256 |
| `tools/pyro_probe.py` | P-0: the DRU pyro rules A–H / A2 measured from geometry (an override cannot blind it), rule G with the P-1b scope (gate copper clipped to outside U1's courtyard), and the strict pad rules H+ 1.2, GS 1.2, AG 1.2 mm |
| `tools/bridge_table.py` | P-5: the R4-style solder-bridge table (exposed pairs, consequence, cold-test signature, tolerated / forbidden) and the reset-voltage model of the gate used by P-7 |
| `tools/rule_h_seed.py` | P-4: on scratch copies, seeds the three closest rule-H pairs to 0.95 mm and runs DRC on eight variants (seed, rule lowered / deleted / moved first / narrowed / RAW_ACT dropped / ACT_GATE dropped, and an armed-pad 0.3 mm override); each must be caught by DRC, check_actuators, LC-1 or pyro_probe |
| `tools/gcpw_solve.py` | The 2-D finite-volume GCPW solver of pass2_rf §7 (half domain, lid 3 mm, SOR 1e-8), plain python3; `--validate`, `--gmax` |
| `tools/tab_windows.py` | T-1: legal 5 mm tab windows per long edge by ORDERING §3's clearances; a tab in each end third of each long edge |
| `tools/plate_model.py` | Verbatim copy of R8 step 9's plate model (needs numpy), so the gate's M-2 does not depend on R8's record folder |
| `tools/r9_scorecard.py`, `tools/r9_extra_metrics.py`, `tools/run_r9_survey.sh` | The R9 scorecard (r9_plan §2's hard / done / stretch rows) and its survey runner, from the survey's scratch tools, repo-relative; new rows LC-1, f1, the R-5 GCPW bound, whole-net exit lanes |
| `tools/scorecard_r8_r9.json`, `tools/scorecard_r8_r9_quick.json` | R8's baseline for the R9 scorecard (0.05 / 0.1 mm DC grids) |
| `tools/test_r9_check.py` | 52 tests: every rule passes on a clean base and fails on a seeded defect; the tool tests; the R8 failing set |
| `tools/route_check.py` | Profile `r9`: empty ALLOWLIST / LEFTOVERS / ROUTE_FIGURES, D10 keep-out baseline |
| `tools/fit_check.py` | `retention_holes()`: J122's tie holes derived from J122 (R8: the old constants); `check_board` uses it |
| `tools/check.sh` | Switched: DRC / parity / ERC, audit, silk, fit → plate model (`NUMPY_PY`) → rule_h_seed → check_r9 → route_check r9 → check_actuators |
| `m3_design/check_actuators.py` | 15b only: the PYRO_BLOCK rectangle replaced by a rule-based, strictly stronger containment check (D-S1-02); sha 6fa58a41… pinned in check_r9 |
| `tools/test_check_shell.py`, `tools/test_r8_check.py` | The gate's stage list; R8's D14 pin now reads R8's check_actuators from commit 9c8179b |
| `sources/r9_design/R9_DECISIONS.md` | Step-1 decisions with their bases |
| `sources/r9_design/step1_evidence/` | `r8_check_r9.json` (the R8 gate report), `r8_rule_h_seed.json`, `r8_plate.json`, `gcpw_validate.txt`, `tests.txt` |

## 2. Verification

| Item (r9_plan §4 step 1) | Result |
|---|---|
| Every rule fails on a seeded defect | `test_r9_check`: 52 tests OK. Each rule id (LC-1, P-0 rule by rule, P-1 / P-1b … P-11, R-1 … R-13, M-2 … M-7, F9-1, T-1, every K-rule) passes on a clean base (synthetic, R8, or R8 repaired in memory where R8 itself fails) and fails on its seed |
| … including an armed-pad override | LC-1 test (J124.1 BUS given 0.3 mm), and rule_h_seed's `pad_override` variant on R8: DRC goes silent (the override blinds it), LC-1 and pyro_probe catch it |
| R8 fails exactly P-3, P-7 and LC-1 | R8 fails 17 rules (§3). P-3, P-7 and LC-1 fail as predicted; the other 14 each fail for an owner-adopted strictness or a real R8 fact, none for a checker fault |
| gcpw_solve reproduces pass 2's 50.3 Ω within 1 Ω | 49.959 Ω coated (−0.34), 51.995 bare (52.2, −0.21), 48.790 launch (49.0, −0.21); mesh refinement 0.004 → 0.002 mm moves Z0 +0.09 Ω |
| All tool tests pass | 18 suites, 324 tests OK (`step1_evidence/tests.txt`), quality_audit 21 OK under both pythons |
| check.sh switched | On R8: DRC 0, ERC 0, parity 0, audit OK, silk OK, fit OK, plate 208.7 Hz, rule-H suite OK (3 pairs × 8 variants), check_r9 FAIL (the 17 rules) → exit 1, 2 min 47 s. route_check r9 on R8 fails exactly R8's three former allowlist items (A8, A2, A3) |
| Scorecard | `run_r9_survey.sh` geometry-only on R8 gives index_r8 = index_r9 = 100, GCPW bound 50.17–50.96 Ω (R8 hard 13 / 17, done 15 / 53 with DC) |

## 3. R8 against check_r9: why it fails 17 rules, not 3

| Rule | R8 finding | Why it differs from the plan's prediction |
|---|---|---|
| LC-1 | 29 overrides: J124.2 and J122's RAW pads 0.3 mm, 24 test pads 1.0 mm | predicted; board-wide by D-S1-01 |
| P-3 | BAT_ENABLE, RAW_PROTECTED, ACT_GATE, BAT_FAULT_N on F.Cu in the hull; RAW_ACT vias and In2 RAW_ACT regions under the block; B.Cu ACT_FET_S pour 0.301 mm from an ARM1_SENSE via | predicted |
| P-7 | GATE_N 0.219 mm from ARM1_SENSE (0.37 V in reset), 0.300 / 0.329 mm from PYRO1_CONT, its via 0.449 mm from In2 3V3 | predicted |
| P-0 | rule G with the P-1b scope (the same ARM1_SENSE pair outside the block); strict H+ (Q124.5–R129.2 1.025 … R134.2–R180.1 1.161) | owner decision 2 (P-1b, strict pad rules) |
| P-1 | R4's rectangle misses J121 / J124 courtyards + 1 mm (x 3.46 < 4.0) and D120 (courtyard, its COLD pad, a COLD track at y < 84); no P-1b scope in R8's DRU | survey P-1 asks for content, which the rectangle covered for gate copper only; P-1b |
| P-5 | 10 forbidden pairs, among them Q124.5 drain–C128.2 GND 0.970 mm and C128.2–R134.1 0.621 mm, 3V3 / 3V3A beside sense nodes at the MCU end, and the strict 1.2 mm class | survey P-5's classes beyond rule H; the strict pad rules |
| P-6 | Q121.4 ACT_GATE–C120.1 ACT_FET_S 0.634 mm | strict "bare gate ≥ 1.0 mm from always-live" (Z5b) |
| P-9 | A8: TP122's gate via in its pad, nearest GND via 2.72 mm | survey P-9 removes R8's allowlisted A8 |
| P-10 | TP121 inside R8's oversized rectangle | ORDERING §5 keep-offs as a rule |
| P-11 | J121 enters from +x | owner decision 1 (pyro leads west) |
| R-1 | C300, C301, FB30, FB31, R305, R307 beyond y 22.0 | owner decision 3 (y_f 22.0; R8's strip is 23.5 deep) |
| R-4 | J30's (+1.25, 4.15) launch via sits at (+1.20, 4.65) (J31 matches) | a real R7 / R8 deviation from pass 2's qualified launch |
| R-7 | GNSS west stitching 2.73 mm along the path (3.90 along y) > 2.5; the fence at y 23.3, not 22.0 ± 0.3 | survey R-7 drops the named ceilings; owner decision 3 |
| M-2 | f1 208.7 Hz < 209 | the plan's 209 Hz is R8's figure rounded up |
| M-6 | C15, R168, R170, R172 within 1.0 mm of the MCU-side pyro vias | D61's exceptions not carried (D-S1-17) |
| K-power-pyro | ACT_FET_S pour 1.089 mm from J124.1 (D85 now 2.5) | r9_plan hard X2d ≥ 2.5 |
| K-inner | R8's rigid In2 ARM1_SENSE link | r9_plan hard S15 = 0 |

R8 passes P-2, P-4 (its seeded suite), P-8, R-2, R-3, R-5, R-6, R-8 … R-13, M-3, M-4, M-5, M-7, F9-1, T-1 and the
K-rules but these two. Report: `step1_evidence/r8_check_r9.json`.

**R8 observations for the owner** (R8 is the orderable fallback and stays untouched; not acted on here):
1. Q124.5 (drain) and C128.2 (GND) are exposed pads 0.970 mm apart: one solder bridge there fires the igniter whenever
   the board is armed (rule D's 0.5 mm holds; rule H does not name GND). C128.2 is also 0.621 mm from R134.1 (igniter):
   a bridge puts R134 across the armed bus (about 4.1 A, below the 5 A link fuse). Post-assembly inspection should look
   at both gaps.
2. The 0.3 mm local overrides on J124.2 and J122's RAW pads disable rules A, E and A2 at those pads (plan_spine §0.5).
3. J30's launch has one stitching via 0.5 mm off pass 2's qualified spot.
4. The B.Cu ACT_FET_S pour sits 0.301 mm from an ARM1_SENSE via (no DRU rule names ACT_FET_S against sense nets).

## 4. What the next steps must know

**Running the gate.** `NUMPY_PY=<python3 with numpy> tools/check.sh [board]` (the parent project's `cfd/venv` has
numpy 2.0.2). About 3 minutes; `rule_h_seed` is 2–3 of them. The gate stops at the first failing stage (`set -e`), so
route_check r9 and check_actuators run only once check_r9 passes. Standalone:
`<KiCad python3> -I tools/check_r9.py BOARD --fit F --plate P --seed S --report OUT [--only P-3,R-7]`.

**R8's own contract in this worktree.** `tools/check_r8.py` on the R8 board now fails only its D14 pin, because
`check_actuators.py` is R9's reviewed version; R8 stays checkable on its own worktree (`../rocket-flight-computer-r8`),
which this step did not touch.

**Step 2 (schematic, footprints, DRU) must:**
- write rule G's condition with `(A.intersectsArea('PYRO_BLOCK') || !A.intersectsCourtyard('U1'))` in place of
  `A.intersectsArea('PYRO_BLOCK')` (P-1b, exact text: `check_r9.G_SCOPE`);
- move the test pads' 1.0 mm clearance into the DRU and clear every pad and footprint override (LC-1 is board-wide;
  the RAW_ACT pins' 0.3 mm to GND pours is already the DRU's last rule);
- after review, re-pin `DRU_SHA` and the changed `PYRO_RULE_SHA` entries in `check_actuators.py`, then
  `CHECK_ACTUATORS_SHA` in `check_r9.py`, and record it (rule H's text must stay as pinned: P-4 cross-checks it);
- keep pad numbers' nets for the renumbered J121 / J124 and the mirrored J122 (check_actuators rules 1 and 7, the
  terminal legends) unchanged.

**Placement (step 3) is bound by:** R-1 every RF part but R306 / R310 / R313 / R315 inside y ≤ 22.0 (FB30 / FB31,
C300 / C301, R305 / R307 included); R-3 jack axes x 3.6–42.4, ≥ 12 mm apart; P-11 J121 / J124 entering −x with
≥ 6.25 mm wire room; M-4 J1 entering +y, courtyard face ≤ 2.0 mm from the forward edge, ≤ 25 mm from both terminals;
F9-1 (≤ 10.6 mm / U9 ≤ 27.07 mm from J1.1); M-3 (tie holes 1–4 mm past J122's courtyard ends, the line within
±3.81 mm at each plug, a 4 mm bottom channel); M-5 floors (J9 mated 0.028, J3 0.886, terminals 1.153, C84 1.366,
J122 0.49 (turned), worst bottom 2.356, support bottom 4.452 and **top 5.008 mm**: the corner holes must keep exposed
top pads ≥ 5.008 mm away, or an owner-backed reason added to `FIT_FLOORS`); M-6 (no bottom part within 1.0 mm of any
PYRO / ARM via, MCU side included); M-7 lever arm ≤ 13.0 (done ≤ 11); P-10 (PYRO_BLOCK and J2 ≥ 5 mm from U4, clear of
U5, the modules, LS120, the jacks, J3, J9, J122, J123 and all test pads but TP122); R-13 radio ≥ 40 mm from the
terminals and armed copper; R-11 / R-12 coexistence and decoupling distances; T-1 a tab in both end thirds of each long
edge; K-contract the outline a rectangle from (0, 0) (four segments or one rectangle).

**RF (step 4):** R-4 the eight launch vias at (±1.45, 1.0 / 2.3 / 3.6), (±1.25, 4.15) and the In1-only no-fill cut-out
x ±0.9, y 0–4.6 in each jack's frame; R-5 W 0.30, gaps 0.25–0.30 (bends ≤ 0.55), part pads on the line ≤ 0.6 mm long,
In1 ±0.70 mm; R-6 ≤ 6.26 / 5.26 mm and ≤ 2 bends; R-7 stitching ≤ 2.5 mm along the path, fence within ±0.3 mm of
y 22.0 (pitch ≤ 2.0, openings ≤ 2.7 with a lane); R-8 keep-outs covering the derived regions (named U30_KEEPOUT /
U31_KEEPOUT); R-9 order and distances (ESD ≤ 1.0, C302 ≤ 1.0, stubs ≤ 0.94).

**Pyro (step 5):** P-0 strict pad rules; P-5 table; P-6; P-7 every GATE / GATE_N neighbour GND or under 0.2 V in reset
(MCU-side sense lanes are 0.10 V and pass); P-8 *_MCU ≤ 3 mm; P-9 no via in TP122, a GND via within 1.5 mm of every
PYRO / ARM via; P-3 no RAW_ACT vias in the CH1 hull, B.Cu foreign copper ≥ 1.0 mm from CH1 copper; P-1 the area must
also pass check_actuators 15b's conservative bounding-box test (make it generous: a larger area only widens rule G).

**Scripts beware:** in KiCad 10, `BOARD.Remove()` of a footprint, drawing, track or zone from a board read by
`LoadBoard`, followed by freeing that board, corrupts SWIG's type table for every later board in the same process
(they come back as bare `SwigPyObject`s). The tests move items off the board instead; any builder that loads several
boards in one process should do the same or keep the edited board alive.

**Scorecard:** `NUMPY_PY=… tools/run_r9_survey.sh BOARD OUTDIR` (full, about 20 min with the 0.05 mm DC; `DC_GRID=0.1`
about 5 min; `NO_DC=1 NO_GATE=1` about 1 min); report `OUTDIR/r9_scorecard.md`.

## 5. Reproduce

```bash
R=rocket-pcb/rocket-flight-computer-r9            # this worktree
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
cd $R/tools && python3 -B gcpw_solve.py --validate && python3 -B gcpw_solve.py --gmax 52.3
for t in test_*.py; do $KP -m unittest "${t%.py}"; done                     # 18 suites, 324 tests
cd $R && NUMPY_PY=<python3 with numpy> tools/check.sh                       # on R8: check_r9 fails 17 rules, exit 1
$KP -I tools/pyro_probe.py m3_design/assembly_review/m3.kicad_pcb
$KP -I tools/bridge_table.py m3_design/assembly_review/m3.kicad_pcb
$KP -I tools/tab_windows.py m3_design/assembly_review/m3.kicad_pcb
$KP -I tools/rule_h_seed.py m3_design/assembly_review/m3.kicad_pcb --json seed.json
```

## 6. Open

- Nothing blocks step 2. No question for the owner arises from step 1.
- The four R8 observations in §3 are for the owner's record of the fallback board.
- M-5's top-hardware floor (5.008 mm) and terminal floor (1.153 mm) are R8's figures; if R9's placement cannot meet one,
  the miss needs an owner-backed reason in `FIT_FLOORS`, never a silent change.
- The D12 rise limits stay in the build's power check (step 6, `run_dc.sh`), not in check.sh, as in R8.
- R-5 treats a bend by its 2-D cross-section (the survey's method; Inference for the bend's true field); R-12's GNSS
  supply figure is a conservative series sum, not a DC solve (0.085 Ω on R8 against 0.2 Ω).
