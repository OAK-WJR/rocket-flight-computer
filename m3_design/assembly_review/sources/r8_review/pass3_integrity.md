# R8 review pass 3: build integrity

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18`
(worktree `rocket-flight-computer-r8`, branch `m3-assy-r8`, uncommitted on R7 commit 431025d).

**Dimension:** build integrity. The questions:
- Does `r8_build.sh` reproduce the board byte for byte from R7?
- Is every gate and per-step check real? Was anything weakened or special-cased, against the R7 versions at 431025d
  or since pass 2?
- Do the tests fire on seeded defects?
- Do the rigid-copy hashes cover what they claim?
- Do the records claim only verification that actually happened?

**Reviewer rules kept:** the repository was read-only; this file is the only write. Builds, gate runs, DRC probes, tests
and the fab run used scratch copies under `…/scratchpad/p3int/`, deleted afterwards. Only logs, small result files and
the measurement scripts in `p3int/scripts/` remain. Read-only scripts (`check_r8 --print-hashes`, `make_ground`,
`m2_sweep`, `binding_note`, `run_survey`) read a scratch copy of the board. They were run from the worktree's tools, and
each wrote its output only to scratch. `git status` is the same 88 paths as at the start of pass 3.

**Verdict: 0 Critical, 0 Major, 4 Minor.**
- The build reproduces the whole tree byte for byte from a fresh clone of 431025d. The step-7 table also regenerates
  byte for byte from the real step-6 board, not only from the stripped final board (`--built`).
- Fix pass 2 changed the gates in two ways only:
  - it tightened `check_r8.battery_pyro`, which now also measures from the drain;
  - it edited text: docstrings, a comment and one allowlist reason string.

  No threshold, allowlist entry, exemption or `LATER` entry moved. The 13-file generator diff it recorded is exact and
  complete.
- The new drain test kills five mutants. The gate catches a seeded drain defect on the real board, which the pass-2
  gate misses.
- The 12 rigid digests are still R7's.
- All five pass-2 integrity findings are closed or properly dispositioned.
- The Minor items:
  - **01:** R78.2's GND via is named as C76.2's in D98, in the D87 correction, in the handoff and in a generator
    comment. As a result, D87 claims a via left the ViaCheck list when it is still on it.
  - **02:** "272 tests OK" is backed only by a log that shows one failure: the tests ran before `r8_fab.sh`. My re-run
    passes. The documented reproduce order sets this trap again.
  - **03:** the ACT_GATE exposure is recorded as a GND via at 0.180 mm. The GND pour itself is at 0.150 mm, and the
    remedy the records propose would not remove it.
  - **04:** the state is still uncommitted. This is an owner action, carried from pass 2.

## 0. Previous pass (R8P2-INTEGRITY-01…05)

| Pass-2 finding | Status on `990c8040…` | Evidence |
|---|---|---|
| 01 J123.2's solid-connection exception rested on a step-6 DRC result | **Closed** | See the evidence below the table. |
| 02 `via_paste` described as R7's ViaCheck rule but looser on the ring | **Closed** (one slip: R8P3-INTEGRITY-01) | `check_r8.py:38-41` docstring and the `:112-113` comment, D87's correction and R8_VALIDATION's hard-gate row now give the real rule (ring off the aperture, hole ≥ 0.1 mm) and the ViaCheck count. Measured with the gate's own `paste_polys` / `min_gap`: **13 pairs at 12 vias** (0.025 C90.1 … 0.090 C76.2), as recorded. The record says the via that left the list is C76.2's; it is R78.2's (finding 01). |
| 03 R8 uncommitted; the pass-1 state lost | **Open** (owner action), carried as R8P3-INTEGRITY-04 | Still no commit: `git log` ends at 431025d, 88 status paths. Fix pass 2 left a stand-in: the hashes of the 222 changed or untracked files and an exact diff of the 13 code files (§2.1). |
| 04 The build's DC neck gate has no automated test | **Accepted** (R8P2-POWER-04 / INTEGRITY-04); recorded in R8_VALIDATION "Open after fix pass 2" | `tools/test_dc_solve.py` is unchanged: 3 tests, all on the stack-up reader. `dc_solve.py` and `run_dc.sh` are unchanged since pass 2, so pass 2's seeded fail path (`NECK FAIL`, exit 1) still applies. Not re-raised. |
| 05 Record slips: date, RF-02 wording, unbound evidence | **Closed** | `STATUS.md:10` dates fix pass 1 2026-10-19. The R8P1-RF-02 row (`R8_VALIDATION:162`) now says "where a trim lands stays ungated". The five `fix1_*` files that lacked a board SHA (`fix1_pyro_neighbours_r8`, `fix1_refaudit_r8`, `fix1_refaudit_r8_ext`, `fix1_requalify_r8`, `fix1_route_check_report`) now carry `board_sha256` `6600ef94…` with a note. I compared each with its pre-fix-2 version from the snapshot: the content is identical apart from the new keys (the pyro list now sits under `neighbours`). The handoff calls them "four" files; they are five. |

Evidence for finding 01 (closed):
- `r8_ground.py` sets `RELIEF_PADS` J123.2 to INHERITED before its fill, after asserting that the pad was FULL.
- On the final board J123.2 is INHERITED. J122.3 / 6 / 9 / 12 stay FULL. J3.1–4 and J1.2 are INHERITED.
- DRC on scratch copies with `min_resolved_spokes` raised gives J123.2 **B.Cu 2 spokes**, F.Cu 4 and In1 4:
  - at 3, the only through-hole pad flagged is J123.2 on B.Cu ("actual 2");
  - at 5, F.Cu and In1 report "actual 4" and B.Cu "actual 2".
- The build's own `check.sh` DRC is 0 at every severity.
- D101, C17, the `r8_pcb.py` comment and ORDERING §4 now describe the final copper.

## 1. Reproduction (the build, byte for byte)

Method:
1. Fresh `git clone` of the parent repository, checked out at 431025d.
2. The worktree rsync'd on top, without `.git` or `__pycache__`: the same 88 status paths.
3. SHA-256 of every file (1298 files).
4. `bash m3_design/r8_build.sh`.
5. The hashes again.

| Item | Result |
|---|---|
| Exit status | **0** after 768 s. Every step gate printed OK: place, power, 9 × route, ground, the DC neck gate, `r8_post`, then `tools/check.sh`. |
| Whole tree after the build | **All 1298 files identical.** The only additions are 35 gitignored `__pycache__/*.pyc` files. Board `990c8040…`, netlist `0cc1ed69…`, all 15 sheets unchanged. |
| `check.sh` inside the build | DRC 0 at every severity, unconnected 0, parity 0, ERC 0. Metadata / 3D OK; silk 0 stroke points outside. `R8 CAD contract: OK`. Routing: 0 failing, 3 allowlisted, 0 stale, 0 leftovers, 0 out-of-date figures, 0 removable bumps. Actuators OK; fit OK. |
| `check_r8` report (the build's `r8.json`) | `checker_sha256` `93715601…` is the current `check_r8.py`. battery_pyro nearest 1.089 mm (ACT_FET_S zone to J124.1, B.Cu); via_paste 709 pairs, nearest ring 0.025 mm (C90.1); 10 legends; D18 2.65 mm (BAT_IN In2 to R134.1); `gate_servo` none under 0.5 mm; `In2_rigid_exempt` 3.4 mm. All as recorded. |
| DC gate inside the build (0.1 mm) | RAW_ACT 5.90 mm / 17.6 °C, BAT_IN 6.85 / 14.8, ACT_FET_S 4.80 / 22.3, all OK against D12. These are the handoff's figures. The solves are bound to the pre-`r8_post` board `7c1b5b21…`; `r8_post`'s copper-unchanged assertion carries the result to the final board. |
| Step-7 table from the **real** step-6 board | I rebuilt the step-6 board in the scratch clone: R7's board, then `r8_pcb`, `r8_power` and the nine `r8_route` families (`8b71a9b1…`; every stage printed "rigid digests 12/12 equal R7"). `make_ground.py` in its normal (non-`--built`) mode on it gives `fe686731…`, which is **`r8_ground.tsv` byte for byte**: 201 rows, with the pad stage's U9.8 → (44.65, 86.775) and U13.2 printed as having no spot. `--built` on the final board gives the same file. The table is therefore a fixed point of the current generator from its documented input, not only from the stripped final board. This matters because the fix pass changed `r8_route_usb_swd.py` (11:48) after it regenerated the table (11:45). |
| Fab (`r8_fab.sh` on the rebuilt board) | Exit 0. CHECK none. CPL verify 85 + 126 rows, worst 0.491 mm, no errors. Paste check OK (348 / 359 flashes). Manifest OK. |
| Fab outputs against the worktree | `m3_bom_jlc.csv` (`be711876…`, R7's), `m3_cpl_jlc.csv` (`25cfed69…`), `cost_check.json` and `stock_check.json` are byte-identical. The 13 Gerber and drill files differ only in their two date lines, and the job file only in date fields. Both PDFs are equal once their date and ID fields are masked. The manifest differs only in those outputs' hashes. |
| Fab against fix pass 1 | Only R81's CPL row changed: (41.245, −91, 180) → (39.6, −91.275, 90). Its rotation follows the board's bottom-side mapping: all 12 other bottom resistors at rotation 90 are also 90 in the CPL. |

Three more outputs regenerate exactly:
- `binding_note.py` on the final board gives `r8_binding_note.json` byte for byte (27 changed pins, U1 map = pin table,
  the PE4 constraint present).
- `m2_sweep.py` matches `fix2_m2_sweep.json` in every key: adjacency, adjacency_pad (36 rows, 4 fine), chain_detour,
  via_fold, pad_edge, routes, bumps_all, short_hop, via_step and poured_hop.
- The quick scorecard (`NO_DC=1 NO_GATE=1 run_survey.sh`) equals `fix2_scorecard.md` in every non-DC row: S1 1499.6,
  S6 / S7 1.177 / 289.4, S17 1638.9, C2 90, P1 0.905, P3b 4, P6 1752.5, P9 / P10 4.47 / 9.65 mm, and the rest. The quick
  index is 13.7; the record's 15.3 includes the 0.05 mm DC rows.

## 2. Gates against R7 (431025d) and against pass 2

### 2.1 What fix pass 2 changed, measured independently

The fix pass's pre-change snapshot still exists in the session scratchpad (`fix2/pre_fix2_state.tgz`).
- Its 222 files hash exactly to `fix2_baseline_sha256.txt`, and the recorded and scratch hash lists are identical.
- Against it, **37 files changed and 18 were added**: 15 `fix2_*` evidence files, `fix2_baseline_sha256.txt`,
  `fix2_generators.diff` and `fix2_handoff.md`. None were removed.
- I recomputed the diff of the 13 code and table files. Its +/− lines are **identical** to `fix2_generators.diff`.
- Every gate and check file keeps its baseline (pass-2-reviewed) hash: `tools/check.sh`, every `r8_*_check.py`,
  `r8_legalise.py`, `r8_keepclear.tsv`, `dc_solve.py`, `run_dc.sh`, `scorecard*.py/json`, `m3.kicad_dru` and
  `m3.kicad_pro`.

The gate edits in that diff:
- **`tools/check_r8.py`:**
  - `ARM_SIDE` adds `PYRO1_OUT`. This only tightens the gate: more copper is measured, and the 1.0 mm limit is unchanged.
  - The `battery_pyro` and `via_paste` docstrings and the `VIA_PASTE_HOLE` comment now state the real rule. The values
    are unchanged.
- **`tools/route_check.py`:** A3's reason string only. `evaluate()` matches an allowlist entry on category, net, layer and
  location; the reason is carried, never compared (`route_check.py:2088-2097`). So the r7 profile and every verdict are
  unchanged.
- **`tools/test_r8_check.py`:** one assertion block added (the drain case). No test was removed or loosened.
- **Generators:**
  - `r8_power.py`: the In2 BAT_IN outline and four via sizes.
  - `r8_place.tsv`: R81.
  - `r8_route_status.py`, `r8_route_usb_swd.py`: two tracks each.
  - `r8_ground.py`: `RELIEF_PADS` / `relieve()`.
  - `step7/make_ground.py`: the relief model and the pad stage. Its legality rules are untouched: the pad stage uses
    the same `Spots.ok`.
  - `r8_pcb.py`: a comment.
  - `binding_note.py`: text.
  - `m2_sweep.py`: the `adjacency_pad` category.

  No family `BUDGET` changed.

### 2.2 Against R7

`git diff 431025d` is still empty for these files:
- `m3.kicad_dru` and `m3.kicad_pro`;
- `quality_audit/`;
- `tools/fit_check.py`, `tools/silk_check.py`, `tools/check_r7.py` and `tools/test_r7_check.py`;
- `m3_design/check_actuators.py`, whose SHA-256 `5de1eb3c…` `check_r8` asserts.

`check.sh` keeps the same 9-line diff from R7 that passes 1 and 2 reviewed. Since `route_check.py` changed only by a
reason string, pass 2's object-equal comparison of `--profile r7` on R7 still holds.

### 2.3 Rigid digests

`check_r8.py --print-hashes` on the R7 board (`c872a3d3…`, from 431025d) reproduces `RIGID_BASELINE` exactly, all 12
groups. The final board prints identical output. No R8 net has a pyro-net pour, so `ch1_copper`'s tracks-and-vias
scope misses no pyro copper. J123 is in no rigid group, so its new relief changes no digest. That is consistent with
J123 not being R7-rigid copper.

## 3. Tests and seeded defects

**Suites** (run on the rebuilt scratch tree, KiCad Python, no bytecode written): **17 suites, 272 tests, all OK**. That
includes `test_fab_validation` 23 OK on the final package. quality_audit: **21 OK** under both Pythons.

**Mutation of the new drain assertion** (`test_battery_live_copper_keeps_1_mm_from_the_bus_igniter_and_drain`):

| Mutant | Test result |
|---|---|
| none | pass |
| `ARM_SIDE` without `PYRO1_OUT` (the pass-2 gate) | **fails** |
| `ARM_SIDE` without `PYRO1_IGN` | fails |
| `ARM_SIDE` without `PYRO1_BUS` | fails |
| `battery_pyro` limit 0.45 mm | fails |
| `BATTERY_LIVE` without `BAT_IN` | fails |

**Seed on the real board** (`990c8040…`, in memory, never saved): a 0.3 mm BAT_IN track whose edge is 0.800 mm from
J121.1 (PYRO1_OUT).
- On B.Cu: `BAT_IN track (34.0, 93.03) is 0.800 mm from PYRO1_OUT J121.1 on B.Cu; minimum 1.0 mm (D85 …)`.
- On In2: the same message.
- With the pass-2 `ARM_SIDE`, neither seed is caught.

Baseline: the gate is clean on the real board. The nearest battery copper to the drain is 3.563 mm (BAT_IN R82.1 to
J121.1, B.Cu), against the recorded 3.562 mm (bisection resolution).

**Untested new code** (not a finding; nothing claims otherwise):
- `r8_ground.relieve()`, `make_ground`'s pad stage and `m2_sweep.adjacency_pad` are generator and review code with no
  unit test.
- The relief is held on the final copper by DRC's `starved_thermal`, an error in `m3.kicad_pro`.
- The pad stage's output is held by the table: `r8_ground_check` asserts every table row on the board. No gate
  re-measures pad copper reach, and the records say "at generation" (R8_VALIDATION PLANES-03), which is accurate.

## 4. Records against what ran

Verified:
- **Builds:** "two consecutive builds identical" (fix-2 `full.sum`: 612 / 609 s, the same 17 hashes) and my independent
  build.
- **Gate:** "`check.sh` exit 0 standalone" (fix-2 `check_final.txt`).
- **Table:** "`make_ground --built` reproduces `r8_ground.tsv` (201 rows)", and, beyond the claim, the same from the real
  step-6 board.
- **Mutant:** "the new drain case kills the old-ARM_SIDE mutant".
- **ViaCheck count:** 13 pairs at 12 vias.
- **J123.2's spokes:** 2 / 4 / 4.
- **Evidence binding:** all 15 `fix2_*` evidence files name `990c8040…`.
- **Binding note:** names `990c8040…`.
- **Manifest:** bound to `990c8040…` (5 outputs).
- **CPL:** only R81's row changed.
- **Hidden designators:** the board's 81 equal M3_R8's list, R84 included.
- **Scorecard, M2 sweep and DC gate figures** (§1).
- **Honest "not re-run" list:** the plate model, the hot-plug script, `--profile r7` on R7 (justified by §2.1) and the
  live cost and stock run. `cost_check.json` still binds the step-9 CPL, and this is stated.

The exceptions are findings 01–03.

## 5. Findings

### R8P3-INTEGRITY-01 (Minor, worth fixing): R78.2's GND via is recorded as C76.2's, so D87's correction misstates the ViaCheck list

**What the records say:**
- D98 (`R8_DECISIONS.md:2048`): "C75.2's and C76.2's GND vias (CAMERA_GND), R72.2's GND via and … `V_IN1` … all four
  take `SMALL_VIA`".
- The D87 correction (`:1934`): "The final board has 13 pairs at 12 vias (**D98's 0.5 mm C76.2 via left the list**)".
- `fix2_handoff.md:37` and `fix2_progress.md:10`: "SMALL_VIA for C75.2 / C76.2 / R72.2 … and V_IN1".
- `m3_design/r8_power.py:469` and `:475`. The comment on the entry `('B', (34.675, 45.2), (33.9, 45.2), SMALL_VIA)` reads
  "C76.2 north-west of the radio lanes". In the pre-fix-2 file, that comment followed two entries on one line, and it
  described the first of them.

**What the board has (`990c8040…`, pcbnew):**
- Pad (34.675, 45.2) is **R78.2** (GND). Its via (33.9, 45.2) is **0.5 mm**.
- C76.2 is pad (35.29, 39.16). Its via (34.4, 38.27) is **0.6 mm** (`VIA`), as `R8_DECISIONS.md:1036` itself says ("C76.2's
  via is at (34.4, 38.27)").
- The copper change is the right one. `fix1_m2_sweep.json` puts the 0.150 mm CAM_MCU_TX / GND pair at via (33.9, 45.2),
  and `fix2_m2_sweep.json` no longer has it.

**The ViaCheck list** (the gate's `paste_polys` / `min_gap`, ring within 0.1 mm of an aperture, on `990c8040…`):
- 0.025 C90.1, 0.033 C7.1, 0.050 C60.2 and U10.3, 0.064 D4.2, 0.070 C300.2, 0.071 R71.2 / R72.1, 0.075 C93.1, R165.2 and
  R76.1, 0.087 R310.1, and **0.090 C76.2** (via (34.4, 38.27), 0.6 mm).
- The entry that left since pass 2's list is **R78.2** (0.075 mm on `6600ef94…`).
- So "D98's 0.5 mm C76.2 via left the list" is false: C76.2's via is still 0.6 mm and still on the list. The count, 13
  pairs at 12 vias, is right.

**Fix (records and a comment; no copper change, board SHA unchanged):**
- Say "R78.2's" for "C76.2's" in D98, the D87 correction, `fix2_handoff.md:37` and the `r8_power.py:469` / `:475`
  comments.
- In the D87 correction write "R78.2's 0.5 mm via left the list; C76.2's 0.6 mm via is still on it at 0.090 mm".

### R8P3-INTEGRITY-02 (Minor, worth fixing): "272 tests OK" rests on a run that shows a failure, and the documented reproduce order sets it up again

**What the records say:** fix pass 2's records state that the 272 tests in 17 suites pass:
- `fix2_handoff.md:20`: "272 in 17 suites (KiCad Python) OK";
- `fix2_progress.md:15`;
- `STATUS.md:58`;
- R8_VALIDATION's fix-pass-2 step row (`:51`).

**What the only test log shows** (scratch `fix2/tests.txt`, 12:22):
- `test_fab_validation.py 23 FAILED (failures=1)`.
- The failing test is `test_current_package`, with the error `[('R81', 'position differs from board and reviewed
  correction')]`.
- The tests ran on the new board, and the CPL still had fix pass 1's R81 row. `r8_fab.sh` regenerated the CPL only at
  12:23 (`fix2/fab.log`).
- No log of a passing run after the fab step exists.

**My result:** on the rebuilt tree, with the final package, all 17 suites (272 tests) pass. So the claim is true of the
final state, but the run it cites did not show it.

**The trap:** the handoff's "Reproduce" block (`fix2_handoff.md:79-80`) lists the test loop before
`m3_design/r8_fab.sh`. After any copper change, following that order makes `test_fab_validation` fail, because it checks
the current package against the current board.

**Fix:**
- Put `r8_fab.sh` before the test loop in the Reproduce block, and in the fix-pass checklist if one is kept.
- Keep the post-fab test log (`tests.txt`) beside the evidence.
- Optionally add one sentence to `test_fab_validation`'s docstring: it judges the package, so run it after `r8_fab.sh`.

### R8P3-INTEGRITY-03 (Minor, worth fixing; records; for the pyro and planes reviewers): the ACT_GATE exposure is recorded as a step-7 via, but the GND pour sits closer, so the recorded remedy would not remove it

**What the records say:**
- R8_VALIDATION's pyro observations, the ACT_GATE row (`:492`), name "step 7's GND via (15.0, 107.3) 0.180 mm from bare
  R120.2".
- C12b #19 (`:379`) gives the reason: "D62's model keeps 0.5 mm from pyro and arming nets only, not from the actuator
  gate".
- The open item (`:518-519`) and `fix2_handoff.md:59-61` propose the remedy: "give `make_ground.clearance` the actuator
  gate nets".
- M3_R8 (`:352-357`) lists ACT_GATE's live neighbours but no GND gap.

**Measured** (pad polygon grown against the GND fills and vias, 1 µm bisection):

| Board | Pad (layer, mask open) | GND pour fill | GND via |
|---|---|---|---|
| R8 (`990c8040…`) | R120.2 (ACT_GATE, B.Cu) | **0.150 mm** (GND_B) | 0.180 mm, (15.0, 107.3) |
| R8 | C120.2 (ACT_GATE, B.Cu) | 0.150 mm | — |
| R8 | R121.1 (ACT_GATE, F.Cu) | 0.150 mm | — |
| R8 | R121.2 and Q122.3 (ACT_DRV, F.Cu) | 0.150 mm | — |
| R8 | Q121.4 (ACT_GATE) | 0.667 mm | — |
| R8 | TP121.1 | 1.0 mm (guarded) | — |
| R8 | Q120.4 | none within 1 mm | none within 1 mm |
| R7 (`c872a3d3…`) | R121.1 (ACT_GATE, B.Cu) | 0.150 mm | — |
| R7 | Q121.4 (ACT_GATE, B.Cu) | 0.150 mm | — |
| R7 | R121.2 and Q122.3 (ACT_DRV, B.Cu) | 0.150 mm | Q122.3: 0.425 mm |
| R7 | R120.2, C120.2, Q120.4 | none within 1 mm | none within 1 mm |

**Consequence:**
- The closest GND to bare R120.2 is the pour, at the board's 0.150 mm minimum, not the via.
- Keeping step-7 vias 0.5 mm from the actuator gate nets would leave that exposure unchanged. It would need a DRC rule
  (GND to ACT_GATE / ACT_DRV) or a pour clearance.
- The class is R7's accepted geometry: a bare actuator-gate pad at 0.150 mm from GND pour, at R121.1 and Q121.4. So this
  is not a new kind of exposure. R8 adds two pads to it (R120.2 and C120.2), and the record understates it.
- What a bridge does is already recorded (rule H's reason: the switch turns on with the power switch open; no fire
  alone), and ORDERING §5's "RAW_ACT dead with the switch open" step screens it.

**Fix (records):**
- The ACT_GATE row, C12b #19 and the open item give the GND pour gap (0.150 mm at R120.2 / C120.2 / R121.1 and at the
  ACT_DRV pads), name the class as R7's (R121.1, Q121.4), and drop "give make_ground.clearance the actuator gate nets"
  as a remedy. Either replace it with the effective one (a `m3.kicad_dru` GND to ACT_GATE / ACT_DRV clearance), if the
  pyro review wants it, or state that the bench screen is the control.
- Whether to add such a rule is the pyro reviewers' call, not this dimension's.

### R8P3-INTEGRITY-04 (Minor, worth fixing; owner action; carried from R8P1/R8P2-INTEGRITY-03): R8 is still uncommitted at pass 3

**State:**
- `git log` still ends at 431025d.
- `git status` shows 88 paths: 37 modified and 51 untracked. They include every `r8_*.py`, `check_r8.py`, the tables,
  the records and the reviews.
- R8_VALIDATION (`:30-36`, `:509-511`) asked for a commit or tag "before review pass 3". None was made.

**What survives of the pass-2 state:**
- The hash list `fix2_baseline_sha256.txt`, which I verified.
- The 13-file `fix2_generators.diff`, which I verified exact. With it, the pass-2 code can be recovered by reverse patch.
- The full snapshot `fix2/pre_fix2_state.tgz`, but only in the session scratchpad, outside the repository. The pass-2
  records survive only as hashes.

**Consequence:** this review's file:line citations are again tied to an uncommitted tree that the next fix pass will
rewrite. Nothing R8 needs is gitignored: the ignored set is `m3.kicad_prl` and `__pycache__`.

**Fix (owner):** commit or tag `m3-assy-r8` at this state (`git add -A`), record the commit beside `990c8040…` in
R8_VALIDATION, and have fix pass 3 diff against it.

## 6. Notes (no finding)

- **Renders.** `r8_top.png` and `r8_bottom.png` are not byte-reproducible: 586 k of 8.6 M decoded pixel bytes differ
  between my fab run and the worktree's. They are not fab outputs, are not in the manifest, and no record calls them
  reproducible.
- **Pad stage figures.** `make_ground`'s pad stage reports U9.8 at 2.81 mm of copper on its 0.1 mm raster. The records'
  2.54 mm is the 0.05 mm measurement (`fix2_measurements.json`). Both describe the same via.
- **Fine-pitch rows.** `m2_sweep.adjacency_pad` counts the 4 fine-pitch own-part rows without listing them. This is a
  stated review convention (C12), not a gate.
- **Local bump.** The M2 sweep's `bumps_all` lists a non-critical BAT_ENABLE local bump: 32.93 mm against a 25.73 mm
  redraw. That is for the routing reviewers. The gate searches bumps on critical nets only, as in R7.
- **Bytecode file.** `step7/__pycache__/make_ground.cpython-39.pyc` (gitignored) appeared in the worktree at 13:04 during
  pass 3. My `make_ground` run had ended at 12:59 and ran it as a script, which writes no bytecode for itself, so it is
  probably another reviewer's import (Inference).
