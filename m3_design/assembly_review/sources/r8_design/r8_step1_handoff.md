# R8 step 1 handoff: gate tools

**Status:** done; verification passed (below). Nothing is committed (the brief forbids commits). Branch `m3-assy-r8`,
worktree `rocket-flight-computer-r8`; the board is untouched (`m3.kicad_pcb` is still R7's `c872a3d3…`).
Decisions taken in this step: R8_DECISIONS **D15–D23** (read them first; summary below).

## What this step produced

| File | Content |
|---|---|
| `tools/check_r8.py` (new) | The R8 CAD contract, in `check.sh` in place of check_r7. R7's contract with the R8 pin map (whole U1 map from `pin_table.tsv`), R310 on 3V3 at the MCU end, STRIP_B / STRIP_VIA without NSS / DIO1, TH1–TH3 removed, plus the new checks: F10 5 mm separation, inner RAW_ACT / BAT_IN 2.5 mm from pyro live copper, PYRO1_GATE_N 0.5 mm from servo PWM, the D5 loader-pin rule, S15 = S16 = 0, the fence rule, 12 rigid hash groups pinned to R7, check_actuators byte-identical. `--print-hashes` prints the digests |
| `tools/test_r8_check.py` (new) | 19 tests; every R8 change and new check fires on a seeded defect |
| `tools/route_check.py` | Profiles: `--profile r8` (default; ALLOWLIST = A8 only, LEFTOVERS / ROUTE_FIGURES empty, D10 keep-out-aware detour baseline, every net so judged printed with both ratios and in the report's `detour_baseline`) and `--profile r7` (the R7 record) |
| `tools/route_lists_r7.py` (new) | R7's ALLOWLIST (45), LEFTOVERS (29), ROUTE_FIGURES, moved verbatim (diff-checked against 431025d) |
| `tools/test_route_check.py` | +7 tests (57): profiles, the TXEN-type loop passing on the D10 baseline, a detour beside the keep-out still failing, a one-layer keep-out not refining, parts / other copper never obstacles, NPTH holes, the R7 lists' reasons |
| `tools/check.sh`, `tools/test_check_shell.py` | check_r8 and `route_check --profile r8` replace check_r7. The board path is made absolute first: R7's script failed its metadata audit on a relative path, because the audit runs in `quality_audit/` |
| `tools/dc_solve.py` | `--necks [--max-rise C]`: the survey's equipotential-cut neck analysis (`cuts()` verbatim from `baseline/dc_neck.py`) with the IPC-2152 rise; fails above the limit |
| `tools/ipc2152.py` (new) | The Brooks & Adam IPC-2152 fit, and D12's limits |
| `tools/run_dc.sh` (new) | The three 7.7 A solves with D12 limits (RAW_ACT 20 °C, BAT_IN 20 °C, ACT_FET_S 30 °C) |
| `tools/survey_metrics.py`, `tools/scorecard.py`, `tools/run_survey.sh` (new) | The scorecard, from the survey scratchpad. survey_metrics unchanged but for its default `--tools`. scorecard takes a JSON baseline and reports r8_plan §2's targets (soft). run_survey has `ROUTE_PROFILE` |
| `tools/scorecard_r7.json`, `tools/scorecard_r7_quick.json` (new) | R7 baselines made by the new tools (DC at 0.05 / 0.1 mm), `ROUTE_PROFILE=r7` |
| `R8_DECISIONS.md` | D15–D23 appended |
| `r8_step1_progress.md` | Running log |

Not changed: `tools/check_r7.py`, `tools/test_r7_check.py` (byte-identical to 431025d; check_r7 still passes on R7),
`m3_design/check_actuators.py` (D14; now hash-asserted by check_r8), every board / schematic / rules file.

## Decisions in one screen (details in R8_DECISIONS)

- **D15 rigid groups.** The pinned R7 digests (`check_r8.RIGID_BASELINE`) cover:
  - the outline, the 5 M3 holes, J122 with its 2 tie holes, J1 and PYRO_BLOCK;
  - the 22 CH1 parts and the CH1 copper (internal pyro nets whole; exit nets up to the exit vias (23.0, 88.33),
    (28.4, 88.61), (18.18, 91.30); GND ties to the first via);
  - the 22 RF-chain and limiter parts and the RF-line copper (8 tracks, GNSS_ANT_DC's via and F.Cu);
  - the strip GND vias and track (175 + 1), the fence row excepted;
  - the strip rule areas (U30 / U31 keep-outs, launch cut-outs);
  - the GCPW ground profile: the F.Cu GND gap along each RF line, every 0.05 mm, to 1.5 mm, which asserts the
    strip "pours" where the field solve used them.

  Regenerated limiter copper and strip interface leads do not disturb the profile; this was measured.
- **D16 fence.** GND vias on y 23.3 at most 2.0 mm apart, except openings of at most 2.7 mm that a lane crosses.
  R7's openings (6.10 / 3.80 mm) fail.
- **D17 F10 separation.** Measured as the R7 RF review did (pass2_rf §3.9), and it reproduces those numbers.
- **D18.** Inner RAW_ACT / BAT_IN must keep 2.5 mm in plan view from PYRO1_BUS / IGN / OUT copper on any layer.
  J124's own pads are exempt.
- **D19.** PYRO1_GATE_N must keep 0.5 mm from SERVO*_MCU / SERVO*_OUT on the same layer and on F/In1 and In2/B
  (layer pairs taken from the stack-up).
- **D20.** S15 = S16 = 0 is a check_r8 gate.
- **D21 profiles.** TXEN needs no entry: on R7, D10 turns 10.95 mm (ratio 2.30) into 20.11 mm (1.25).
- **D22.** R7 history is kept.
- **D23.** The tools moved into `tools/`.

## How it was verified

1. **Unit tests (KiCad Python), all pass:**

   | Suite | Tests |
   |---|---:|
   | test_check_shell | 2 |
   | test_dc_solve | 3 |
   | test_fab_validation | 23 |
   | test_fit_check | 23 |
   | test_maze_clearances | 10 |
   | test_procurement | 15 |
   | test_r6_check | 17 |
   | test_r7_check | 35 |
   | test_r8_check | 19 (new) |
   | test_route_check | 57 (was 50) |

   - quality_audit/test_quality_tools passes under both Pythons.
   - `test_r5_repair` fails its one known subtest, unchanged; STATUS.md records it as failing on R6 and R7 too.
2. **Each new check fires on a seeded defect** (test_r8_check, test_route_check):
   - pin table: a contract pin, a loader marker, a duplicate net, a missing row;
   - U1 pin map and sentinel; R310 rail and MCU-end placement; NSS / DIO1 in the strip;
   - fence: no lane, and an opening wider than 2.7 mm;
   - PB10 carrying the camera UART; an LED net passes and the same net without its LED fails;
   - RF part near U1, near a fast line, near a switching part;
   - inner RAW_ACT and BAT_IN near pyro copper (J124 exempt); gate and servo on the same layer and through a
     thin prepreg (but not through the core); layer pairs from the stack-up;
   - In1 / In2 tracks; every one of the 12 rigid groups (and order / UUID invariance); the GCPW profile;
   - an edited check_actuators;
   - D10: the loop round a module body passes, a wider detour beside it still fails, a one-layer keep-out does not
     refine.
3. **The tools on the R7 board report its known values:**
   - **check_r8:**
     - Rigid hashes match by construction. They are stable across a native refill and save / reload, and
       `strip_gcpw` is unchanged after deleting far copper, the limiter DC copper or the strip interface leads and
       refilling.
     - Separation: FB30–C6 5.875 mm (pass2_rf 5.87), C301–C6 6.992 (6.99), U30–C6 7.185 (7.19), C300–C6 7.199
       (7.20), U31–C6 9.092 (9.09), FB31–U3 9.896 (9.90).
     - Fence: 21 vias, openings 6.3–12.4 and 20.0–23.8 (pass4_rf).
     - Line stitching gaps 3.90 / 2.65 / 1.55 / 1.55 mm (pass4_rf).
     - S15 = 901.0 mm (survey S15); 27 pin-map mismatches, which are step 0's 27 changed pins.
     - The expected R8 findings: 92 in all. Pin map 27, TH1–3, R310 rail and its MCU-end placement 2, NSS / DIO1 in the strip 6, fence 2, loader
       PB10 / PB14 2, BAT_IN In2 under PYRO1_BUS 1, GATE_N / servo 14, In2 signal nets 35.
   - **check_r7** on R7: OK. **`route_check --profile r7`** on R7: the baseline survey's `route.txt` line for line
     (0 failing, 45 allowlisted, 29 leftovers, OK). **`--profile r8`** on R7: 43 failing + A8 + 29 unrecorded
     leftovers (73 = R7's 74 minus TXEN); 15 nets listed on the D10 baseline.
   - **Full `check.sh`** on R7: DRC / parity / ERC 0, metadata audit OK, silk OK, check_r8 FAIL (as expected),
     exit 1. Run with an absolute path, then again with a relative one after the path fix; same result.
   - **Scorecard:**
     - `run_survey.sh` with the new tools on R7 (`ROUTE_PROFILE=r7`): `survey.json` equals the baseline survey's
       field for field, and `cref_self*.json` and `route.txt` are identical.
     - DC at 0.05 mm, the same output as the baseline survey line for line plus the new IPC lines:

       | Path | R | Neck | Rise |
       |---|---:|---|---:|
       | RAW_ACT | 3.71 mΩ | 3.00 mm on F.Cu | 38.3 °C |
       | BAT_IN | 3.03 mΩ | 3.82 mm on In2 | 30.2 °C |
       | ACT_FET_S | 1.16 mΩ | 2.65 mm on B.Cu | 44.3 °C |

       At 0.1 mm the three give 3.74 / 3.03 / 1.19 mΩ, the same as r7_quick.
     - The scorecards equal the baseline survey's in every row. The exceptions are the G rows (the runs used
       NO_GATE, since the R8 gate fails R7 by design) and the new R6b row (0.2791, R7's 27.9 % critical-reference
       loss).
     - They are installed as `tools/scorecard_r7.json` / `scorecard_r7_quick.json`: R7 against itself gives index
       100.0, and R6 against R7 gives 142.9 (the survey: 143).
     - `dc_solve --necks` prints the IPC-2152 rise and the D12 verdict (R7: FET 44.3 °C > 30, NECK FAIL).

## Reproduce

```bash
cd rocket-pcb/rocket-flight-computer-r8
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
B=$PWD/m3_design/assembly_review/m3.kicad_pcb           # still R7 c872a3d3... until step 4 writes R8
(cd tools && for t in test_r8_check test_route_check test_r7_check test_check_shell test_dc_solve; do $KPY -m unittest $t; done)
PYTHONUNBUFFERED=1 $KPY -I tools/check_r8.py "$B" --report /tmp/r8.json     # R7: 92 findings, hashes OK
PYTHONUNBUFFERED=1 $KPY -I tools/check_r8.py "$B" --print-hashes            # equals check_r8.RIGID_BASELINE on R7
PYTHONUNBUFFERED=1 $KPY -I tools/check_r7.py "$B"                           # R7 CAD contract: OK
PYTHONUNBUFFERED=1 $KPY -I tools/route_check.py "$B" --profile r7           # OK, 45 allowlisted, 29 leftovers
PYTHONUNBUFFERED=1 $KPY -I tools/route_check.py "$B"                        # r8: TXEN on the D10 baseline
bash tools/check.sh m3_design/assembly_review/m3.kicad_pcb                  # R7 fails at check_r8 (exit 1)
T=$(mktemp -d); ROUTE_PROFILE=r7 NO_GATE=1 DC_GRID=0.1 tools/run_survey.sh "$B" $T/r7q   # ~8 min
diff <(python3 -c "import json;print(json.dumps(json.load(open('$T/r7q/scorecard.json'))['scorecard'],sort_keys=True,indent=0))") \
     <(python3 -c "import json;print(json.dumps(json.load(open('tools/scorecard_r7_quick.json'))['scorecard'],sort_keys=True,indent=0))")
```

On an R8 board: `tools/run_survey.sh BOARD OUTDIR` (r8 profile; DC at 0.05 mm, ~45 min), `DC_GRID=0.1` for the quick
grid, `NO_DC=1 NO_GATE=1` for a one-minute geometry + route_check pass.

## What the next steps must know

- **check.sh now gates R8:** check_r8 + route_check r8. On the worktree board (still R7) it fails at check_r8, as
  expected. When step 4 or later writes the R8 board, every check_r8 finding above must go.
- **Rigid copy:** steps 4–8 must leave the 12 groups' digests unchanged. `check_r8.py --print-hashes` shows which
  group drifted.
  - Copy rigid items with their exact geometry (nets, pad properties, footprint attributes included; UUIDs may be
    new).
  - The GND zone settings near the RF lines must reproduce R7's F.Cu fill there (`strip_gcpw`): zone clearance and
    minimum width as R7's GND_F, and no new copper within about 1.5 mm of an RF line.
  - Re-baselining is a recorded R8 decision naming the group; never the RF-line or CH1 groups (D9; r8_plan §5).
- **Fence (D16):** the fence row at y 23.3 is regenerated. Each lane group goes through an opening of at most
  2.7 mm, crossed by its lanes; other gaps are at most 2.0 mm. Strip field vias are rigid: if a regenerated lead
  cannot pass one, that is a D11 amendment re-baselining `strip_gnd` only.
- **Placement (step 4):**
  - R306 / R310 / R313 / R315 ≥ 5 mm (courtyard) from U1, U3, Y1 and the bucks' parts, and ≥ 5 mm from QSPI / SPI1 /
    IMU_CS / SWD / USB / HSE / switch-node copper (D17).
  - R310 nearer U1 than U31 (D4).
  - No LED or other net on PA6 / PA8 / PA9 / PA10 / PC9 / PC11 / PE13 (D5).
- **Power (step 5):** In1 / In2 RAW_ACT and BAT_IN at least 2.5 mm, in plan view, from PYRO1_BUS / IGN / OUT copper
  on any layer (In2 GND under the block, D18). `run_dc.sh` gives the D12 verdicts; `dc_solve --necks --max-rise`
  for one net.
- **Signal routing (step 6):**
  - PYRO1_GATE_N 0.5 mm from servo copper on its layer and the prepreg-adjacent layer (D19);
  - no signal track on In2 and no track on In1 (D20);
  - route_check r8 has no leftovers list, so every non-critical hygiene instance fails too;
  - the only allowlist entry is A8.
- **Scorecard:** `tools/run_survey.sh`; baseline `tools/scorecard_r7.json`; targets in its output.

## Left open (not escalated; none is unsafe or changes a requirement's intent)

- **Independent review of the step-1 tools** (r8_plan §3 step 1 "independent review") is for the orchestrator; no
  reviewer agent was available inside this step.
- **Docs that still name check_r7 for R8:** AGENTS §3 (legend rule), REQUIREMENTS M2 / F10 "`tools/check_r7.py`
  enforces …" (F10 already names check_r8), STATUS. Step 9 regenerates them (R8_DECISIONS "Not changed here").
  check_r8 runs the same R7 functions those texts cite.
- **"Fit margins ≥ R7's"** (r8_plan §2 hard gate) has no automated check in this step. fit_check is unchanged and
  in check.sh; step 4 compares its report with R7's.
