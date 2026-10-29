# R8 review pass 4: build integrity

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54`
(worktree `rocket-flight-computer-r8`, branch `m3-assy-r8`, uncommitted on R7 commit 431025d).

**Dimension:** build integrity. The questions:
- Does `r8_build.sh` reproduce the board byte for byte from R7?
- Is every gate and per-step check real? Was anything weakened or special-cased, against the R7 versions at 431025d
  or since pass 3?
- Do the tests fire on seeded defects?
- Do the rigid-copy hashes cover what they claim?
- Do the records claim only verification that actually happened?

**Reviewer rules kept:**
- The repository was read-only, and this file is my only write.
- Builds, the fab run, the tests and the step-6 rebuild ran in a fresh clone under `…/scratchpad/p4int/`. Board copies
  and clones were deleted afterwards. Only logs, small result files and the scripts in `p4int/scripts/` remain.
- Read-only scripts (`m2_sweep`, `reference_audit`, `check_r8 --print-hashes`, `route_check`, `check_r7`, my
  `measure.py`) read scratch copies of the boards. Seeds were applied in memory, and no board was saved.
- `git status` is the same 89 paths at the end as at the start: 38 modified and 51 untracked. Pass 3 had 88;
  `tools/test_fab_validation.py` is now modified.

**Verdict: 0 Critical, 0 Major, 2 Minor.**
- **Reproduction:** the build reproduces the whole tree byte for byte from a fresh clone of 431025d. The step-7 table
  regenerates byte for byte from the real step-6 board and from the final board (`--built`).
- **Fix pass 3's record:** its recorded baseline (248 hashes) and its 11-file generator diff are exact and complete.
- **Gate changes:** fix pass 3 made two, and both tighten a gate:
  - the camera family's ratio budget, 1.55 → 1.40;
  - L10's R172 figure, 0.635 → 0.685 mm.

  No tool, allowlist, threshold or exemption was loosened. `route_check.py`, `check_r8.py`, `check.sh` and every other
  gate file are byte-identical to the pass-3 state.
- **Seeded defects:** each change fires on a seeded defect. The new review-only `m2_sweep.margin_free` search finds, on
  the pass-3 board, exactly the CAM_PWR_EN redraw that the gate-margin search misses.
- **Rigid digests:** the 12 digests are still R7's.
- **Pass-3 findings:** all four are closed except the commit, which is the owner's action and carried here as 01.
- **The Minor items:**
  - **01:** still uncommitted. This is an owner action, carried.
  - **02:** a stale "six pour trims" in `r8_build.sh`'s stage description. It has been seven since fix pass 1.

## 0. Previous pass (R8P3-INTEGRITY-01…04)

| Pass-3 finding | Status on `c84f00b8…` | Evidence |
|---|---|---|
| 01 R78.2's GND via recorded as C76.2's; D87's correction misnamed the via that left the ViaCheck list | **Closed** | See "Evidence for 01" below the table. |
| 02 "272 tests OK" rested on a log that showed `test_fab_validation` failing; the reproduce block ran the tests before `r8_fab.sh` | **Closed** | See "Evidence for 02" below the table. |
| 03 ACT_GATE exposure recorded as a step-7 via, but the GND pour sits closer; the recorded remedy would not remove it | **Closed** (records; D109) | See "Evidence for 03" below the table. |
| 04 R8 uncommitted | **Open** (owner action), carried as R8P4-INTEGRITY-01 | `git log` still ends at 431025d. |

**Evidence for 01:**
- D98 (`R8_DECISIONS.md` "D98") and the D87 correction now name R78.2. The D87 correction reads "D98's 0.5 mm R78.2 via
  left the list; C76.2's 0.6 mm via is still on it at 0.090 mm". `fix2_handoff.md:37` and `fix2_progress.md:10` carry
  marked corrections, and the comment at `r8_power.py` `CAMERA_GND` reads "R78.2 (CAM_5V bleed)".
- Remeasured with the gate's own `check_r8.paste_polys` / `min_gap` (ring within 0.1 mm of an aperture, on
  `c84f00b8…`): **12 pairs at 11 vias**, as the records and D108 now state:
  - 0.025 C90.1, 0.033 C7.1, 0.050 C60.2 and U10.3, 0.064 D4.2, 0.070 C300.2;
  - 0.071 R71.2 and R72.1 (one via), 0.075 C93.1 and R76.1, 0.087 R310.1;
  - 0.090 C76.2 (via (34.4, 38.27), 0.6 mm).
- R165.2's pair, which pass 3 measured at 0.075 mm, is gone. That is fix pass 3's D108.

**Evidence for 02:**
- `fix2_handoff.md` and `fix3_handoff.md` list `r8_fab.sh` before the test loop, with a marked correction.
- `test_fab_validation`'s docstring now says to run it after the fab step.
- `step9/evidence/fix3_tests.txt` names `c84f00b8…` and "each suite run after `m3_design/r8_fab.sh`". The scratch logs
  bear this out: `fix3/fab.log` was written at 14:11:08, the first suite log at 14:11:10 and the last at 14:11:58, and
  all 17 suites passed. The board was `c84f00b8…`: builds 1, 2 and 3 have identical `sha.txt`.
- I re-ran the suites after my own fab run: 17 suites, 272 tests, all OK (§3).

**Evidence for 03:**
- The ACT_GATE row, C12b and the note under it, the pyro observations and M3_R8 now give the pour gap (0.151 mm at the
  five bare ACT_GATE / ACT_DRV pads) and name the class as R7's.
- The `make_ground.clearance` remedy is dropped (D109, and the marked correction in `fix2_handoff.md:59-64`).
- The DRU rule is left as an owner option. D109's claim that a DRU change trips `check_actuators` is true:
  `check_actuators.py:78` pins `DRU_SHA = '1674d58be79ae428'`, the current file's prefix.

## 1. Reproduction (the build, byte for byte)

**Method:**
1. Fresh `git clone` of the parent repository, checked out at 431025d.
2. The worktree rsync'd on top, without `.git`, `__pycache__` or the gitignored `m3.kicad_prl`. The result has the same
   89 status paths.
3. SHA-256 of every file (1324 files).
4. `bash m3_design/r8_build.sh`.
5. The hashes again.
6. The post-build checks: `p4int/scripts/post.sh`.

| Item | Result |
|---|---|
| Exit status | **0** after 843 s (the CPU was shared with the other pass-4 reviewers) |
| Whole tree after the build | **All 1324 files identical.** The only additions are the gitignored `m3.kicad_prl`, which KiCad writes and I had left out of the overlay, and `__pycache__` files. The board is `c84f00b8…`, the netlist `0cc1ed69…`, and all 15 sheets are unchanged |
| Step gates in the build | placement OK; power OK; the 9 route families OK; ground OK (reach p95 4.47 / max 9.65 mm, 21 islands); `r8_post` (rigid 12/12, "copper, zones and pads unchanged"). The camera family prints `signal_track_mm 89.9, signal_vias 6, worst_ratio 1.375` against the new 1.40 budget |
| DC neck gate (0.1 mm) in the build | RAW_ACT 5.90 mm / 17.6 °C, BAT_IN 6.85 / 14.8, ACT_FET_S 4.80 / 22.3, all "neck OK" against D12. These equal the handoff's figures |
| `tools/check.sh` in the build | See the breakdown below the table |
| Step-7 table from the **real** step-6 board | See the breakdown below the table |
| Fab (`r8_fab.sh` on the rebuilt board) | Exit 0. CHECK none. CPL 85 + 126 rows rebuilt, worst 0.491 mm, no errors. Paste check OK (348 / 359 flashes). Manifest OK (5 outputs) |
| Fab outputs against the worktree | See the breakdown below the table |
| Fab against fix pass 2 | Only R172's CPL row changed: `R172,30.6000mm` → `R172,30.6500mm` (`25cfed69…` → `ef90bfa1…`). The BOM is unchanged (`be711876…`, R7's) |

**`tools/check.sh` in the build:**
- DRC 0, unconnected 0, parity 0, ERC 0;
- audit OK; silk 0 stroke points outside;
- `R8 CAD contract: OK`;
- routing: 0 failing, 3 allowlisted, 0 stale, 0 leftovers, 0 out-of-date figures, 0 removable exceptions, 0 removable
  bumps (22 windows);
- actuators OK; fit OK.

**Step-7 table from the real step-6 board:**
- I rebuilt the step-6 board in the clone: R7's board, then `r8_pcb`, `r8_power` and the nine families. Its SHA-256 is
  `c6a03c55…`, and every stage printed "rigid digests 12/12 equal R7".
- `make_ground.py` in its normal (non-`--built`) mode gives `e2250409…`, which is **`r8_ground.tsv` byte for byte**:
  201 rows (fence 25, stitch 2, c24 2, trim 7, return 16, grid 89, cover 54, island 5, pad 1).
- `--built` on the final board gives the same file.
- So the regenerated table is a fixed point of the final generators. This matters because `r8_route_camera.py` (14:03)
  and `r8_route_check.py` (13:56) were edited after fix pass 3's stage A regenerated the table (13:45). The first edit
  was the budget only, the second the L10 figure only, and neither touches copper.

**Fab outputs against the worktree:**
- `m3_bom_jlc.csv`, `m3_cpl_jlc.csv`, `cost_check.json` and `stock_check.json` are byte-identical.
- The 13 Gerber and drill files differ only in their date lines, and the job file only in `CreationDate`.
- Both PDFs are equal, length for length, once `/CreationDate`, `/ModDate` and `/ID` are masked.
- The manifest differs only in those three outputs' hashes.

Five more outputs regenerate exactly:
- `binding_note.py` on the rebuilt board gives `r8_binding_note.json` byte for byte. The new RF-01 order text is in it.
- `m2_sweep.py` on the final board matches `fix3_m2_sweep.json` in **every key**. That includes the new `margin_free`
  key: 29 windows, the BAT_ENABLE candidate and the four C11 redraws. The pairs are 53 rows / 28 pairs (9 at 0.150 mm)
  against fix pass 2's 54 / 29 / 10, and the pad rows 33 against 36. These are the handoff's figures.
- `reference_audit.py` equals `fix3_refaudit_r8.json` in every non-path key.
- The quick survey (`NO_GATE=1 NO_DC=1 run_survey.sh`) plus the recorded `fix3_dc_*.txt`, run through `scorecard.py`
  against `scorecard_r7.json`, reproduces `fix3_scorecard.md` row for row: index 15.3, S1 1497.6, S6 / S7
  1.175 / 287.4, P1 0.9051, P6 1752.2, 20 met / 11 missed. Only the header differs.
- `route_check --profile r7` and `check_r7.py` on R7's own board and project files (431025d): exit 0, "R7 CAD contract:
  OK".

## 2. Gates against R7 (431025d) and against pass 3

### 2.1 What fix pass 3 changed, measured independently

**Rebuilding the pass-3 state:**
- I rebuilt the pass-3 state (`990c8040…`) from 431025d plus the coordinator's backup (`r8_backup_990c8040/`: the
  tracked diff and the untracked tarball). Its board hashes to `990c8040…`.
- All **248** hashes in `fix3_baseline_sha256.txt` verify against it.
- Its header claim also holds: every tracked file it does not list equals 431025d. Those files come from the commit
  unchanged.

**What changed against that state:**
- **31 files changed and 19 were added**:
  - the 15 `step9/evidence/fix3_*` files;
  - `fix3_baseline_sha256.txt`, `fix3_generators.diff`, `fix3_handoff.md` and `fix3_progress.md`.
- None were removed, and no `pass3_*.md` was touched.
- The changed set is exactly the handoff's "Files changed by fix pass 3".
- I recomputed the diff of the 11 code and table files. Its +/− lines (124) are **identical** to `fix3_generators.diff`.

**Every gate file keeps its pass-3 hash.** That covers:
- `tools/check.sh`, `check_r8.py`, `route_check.py`, `check_r7.py`, `fit_check.py`, `silk_check.py`, `dc_solve.py`,
  `run_dc.sh`, `paste_check.py`, `reference_audit.py` and `scorecard*`;
- every `m3_design/r8_*_check.py` except `r8_route_check.py`;
- `r8_legalise.py`, `r8_keepclear.tsv` (header only, as in pass 3), `check_actuators.py`, `m3.kicad_dru`,
  `m3.kicad_pro` and `quality_audit/`;
- every test file except `test_fab_validation.py`, whose change is a docstring only.

The gate edits in fix pass 3, with seeds on the real board (`p4int/scripts/measure.py`, in memory):

| Edit | Direction | Seed result |
|---|---|---|
| `r8_route_check.L10_EXCEPT` R172 0.635 → 0.685 mm (`:262`; the test at `:282` is `gap >= ok - 0.005`) | **Tighter**: the exception now needs R172's measured gap after D106 (0.685 mm, measured; `l10` lists it as allowed) | R172 moved 0.05 mm west (its pass-3 spot) **fails** with the new figure ("R172 bottom courtyard 0.635 mm from the pyro via ARM1_SENSE_MCU (29.3, 47.5)"). The same seed passes with the old 0.635. |
| `r8_route_camera.BUDGET` ratio 1.55 → 1.40 (`:40`) | **Tighter** (worst 1.375) | `budget()` flags 1.41 and 1.50 ("ratio … over the family budget 1.4"). The old CAM_PWR_EN route (1.50) would now fail its own family gate. |
| `step9/m2_sweep.py margin_free` (`:335-347`) | Review code, not a gate | See the breakdown below the table. |

**Why `margin_free` is review code only:**
- No gate, test or build stage imports `m2_sweep`. `grep` finds it only in its own file.
- The patch of `r7_hygiene.rule_clearance` is restored in `finally`.
- `Clearance.why` looks the name up at call time (`r7_hygiene.py:699`), so the patch takes effect.

**`margin_free` on the pass-3 board (`990c8040…`):**
- It gives the bumps CAM_PWR_EN and BAT_ENABLE. The CAM_PWR_EN candidate is (31.85, 36.8) → (28.25, 36.8) →
  (28.25, 30.025) → (30.775, 27.5), exactly the copper fix pass 3 drew.
- The gate-margin `bumps_all` (BAT_ENABLE only) and the C11 row (CAM_PWR_EN "no redraw") miss it.
- So the new search fires on the defect it was written for. On `c84f00b8…` it finds only the known items (§1).

**Generators** (no gate effect):
- `r8_power.py` (trunk y 37.3, comments), `r8_place.tsv` (R172 x 30.65, and its basis column);
- `r8_route_pyro.py` (lane x 30.65, pad table), `r8_route_camera.py` (one path), `r8_route_status.py` (V_BE1 into
  `SIGNAL_VIAS`; `ENABLE_VIA` is referenced nowhere else);
- `r8_ground.tsv` (one cover via, one row reordered).

The basis column of `r8_place.tsv` changed after build 2. `r8_pcb.read_place` reads only `ref`, `x`, `y`, `rot` and
`side`, and no other stage reads that file, so "no stage reads it" holds.

### 2.2 Against R7

`git diff 431025d` is still empty for:
- `m3.kicad_dru`, `m3.kicad_pro` and `quality_audit/`;
- `tools/fit_check.py`, `silk_check.py`, `check_r7.py` and `test_r7_check.py`;
- `m3_design/check_actuators.py` (SHA-256 `5de1eb3c…`, asserted by `check_r8.CHECK_ACTUATORS_SHA`).

The `check.sh`, `test_check_shell.py`, `test_r5_repair.py` and `jlc_corrections.json` diffs are the ones passes 1–3
reviewed: the R7 → R8 contract swap, the absolute board path, the R5 test retargeted to 580d358, and two "via" provenance
strings. `route_check.py` is unchanged since pass 3, and `--profile r7` on R7 still exits 0 (§1).

### 2.3 Rigid digests

- `check_r8.py --print-hashes` on R7's board (`c872a3d3…`, from 431025d) prints the 12 values of `RIGID_BASELINE` exactly
  (each checked against `check_r8.py:136-149`).
- The final board prints identical output, which is also identical to pass 3's `r7_hashes.txt`.
- None of fix pass 3's copper touches a rigid group:
  - the moved cover via (29.125, 32.625) lies forward of the strip_gnd limit (y 23.25);
  - R172, the USB_LIMITED trunk, CAM_PWR_EN and R165's via are not R7-rigid copper.
- Every build stage and `r8_post` printed "rigid digests 12/12 equal R7".

## 3. Tests and seeded defects

**Suites** (rebuilt clone, after `r8_fab.sh`, KiCad Python, no bytecode written):
- **17 suites, 272 tests, all OK**, including `test_fab_validation` (23) on the regenerated package;
- quality_audit **21 OK** under both KiCad's Python and the system `python3`.

**Seeds this pass:**
- L10 and the camera budget (§2.1).
- `margin_free` on the pass-3 board (§2.1).

**Seeds carried, still valid because the code is unchanged since pass 3:**
- pass 3's five `battery_pyro` drain mutants and its real-board drain seed;
- the DC gate's hand-seeded fail path (passes 1 and 2).

**Untested** (not a finding, and no record claims otherwise):
- `margin_free` has no unit test. It is review code, and its output is checked above.
- The L10 exception path (an excepted part nearer than its figure) has no unit test. `test_r8_route` seeds a non-excepted
  part (R163) only. My seed shows the path works.

## 4. Records against what ran

Verified against logs, evidence and my own runs:

**Builds:**
- "Three builds gave the same board, the third on the final generator state": `fix3/build1|2|3/sha.txt` are identical
  (17 files). Their durations are 10:11.61, 12:49.12 and 10:09.39, which matches the recorded 611 / 769 / 609 s.
- My independent build gives the same result.

**Gate:**
- "`check.sh` exit 0" holds in all three logs and in mine.
- "camera budget 1.40 holds at 1.375" and "L10 R172 0.685 measured" both hold.

**Table:** "`make_ground --built` reproduces `r8_ground.tsv` (201 rows)" holds, and so does the stronger claim that it
regenerates from the real step-6 board.

**Tests:** "272 tests after the fab step": §0, item 02.

**Fab:**
- "only R172's CPL row changed; BOM unchanged" holds.
- "cost / stock not re-run; `cost_check.json` still binds the step-9 CPL `d26572d3…`" holds: the `m3_cpl_jlc.csv` input
  hash in `cost_check.json` is `d26572d3…`.

**Evidence binding:**
- All 15 `fix3_*` evidence files name `c84f00b8…`.
- They are the scratch outputs (`fix3/ev/`, run on `fix3/build1`, which is `c84f00b8…`), with the absolute path replaced
  by `<board folder>` and a `board_sha256` key added. Their content is otherwise equal.

**Claimed equal to fix pass 2:**
- The `check_r8` report: equal but the SHA.
- The `route_check` report: equal but one T, (29.95, 37.25 → 37.3), as D106 says.
- `refaudit` and `pyro_neighbours`: equal but the SHA.
- `requalify`: two "other" coordinates move with USB_LIMITED.
- The DC files: the headline figures are equal, as claimed. At 0.05 mm BAT_IN's free-cell count and peak density move
  slightly (204261 → 204350 cells, 3.96 → 3.95 A/mm) because the B.Cu pour refills round R165's smaller via. The
  neck stays 6.99 mm / 14.5 °C.

**ViaCheck:** "12 pairs at 11 vias" (§0, item 01).

**Honest "not re-run" list:**
- the plate model and the hot-plug script (numpy; one 0603 moved 0.05 mm and a docstring changed);
- the untouched supply rows;
- the live cost and stock run.

## 5. Findings

### R8P4-INTEGRITY-01 (Minor, worth fixing; owner action; carried from R8P1/R8P2/R8P3-INTEGRITY): R8 is still uncommitted at pass 4

**State:**
- `git log` ends at 431025d.
- `git status` shows 89 paths: 38 modified and 51 untracked. They include every `r8_*.py`, `check_r8.py`, the tables,
  the records and all four review passes.
- R8_VALIDATION "Open after fix pass 3" and STATUS still ask for a commit or tag. None was made.

**What survives of the pass-3 state:**
- `fix3_baseline_sha256.txt` (verified, §2.1).
- The exact 11-file `fix3_generators.diff`. With it, the pass-3 code and tables can be recovered by reverse patch from
  the current tree.
- The full pass-3 state exists only in the session scratchpad (`r8_backup_990c8040/`). The pass-3 records (docs) are
  recoverable only from that backup.

**Consequence:** this review's file:line citations are tied to an uncommitted tree. The next edit will rewrite it, and
the only full copy of the reviewed state before it lives in a temporary directory. Nothing R8 needs is gitignored: the
ignored set is `m3.kicad_prl` and `__pycache__`.

**Fix (owner):**
- Commit or tag `m3-assy-r8` at this state (`git add -A`).
- Record the commit beside `c84f00b8…` in R8_VALIDATION and STATUS.
- Have any further fix pass diff against it.

### R8P4-INTEGRITY-02 (Minor, not worth fixing on its own): `r8_build.sh`'s stage description still says "six pour trims"; there are seven

**What the file says:** `m3_design/r8_build.sh:30-31` describes `r8_ground.py` as drawing "… island and reach vias, six
pour trims".

**What the build does:**
- `r8_ground.tsv` has 7 `trim` rows (`R8_POUR_TRIM_G1` … `G7`).
- The build prints "r8_ground: 193 GND vias, 1 GND track(s), **7 pour trims**".
- `make_ground` prints `trim: 7`.
- G7 was added in fix pass 1 (D90; M3_R8:164 says "seven pour trims").
- D62's "six pour trims" (`R8_DECISIONS.md:1468`) and D65 are step-7 history, superseded by D90, and are fine as
  history.

**Fix:** "seven pour trims (D65, D90)" in the build header, at the next edit of `r8_build.sh`. It is a comment only:
nothing reads it and the board is unchanged.

## 6. Notes (no finding)

- **Table regeneration is a manual step.** It is documented in `make_ground.py`'s docstring and the handoff: build to
  step 6, regenerate, rebuild. The build itself does not check that `r8_ground.tsv` is current for the generators;
  `r8_ground_check` gates every row's presence and the functional properties (reach, islands, DRC).
  - Fix passes 2 and 3 both edited generators after regenerating the table. Pass 3 and this pass each checked the fixed
    point by hand, and it held both times.
  - A stale table would still have to pass every gate, so this is a reproducibility nicety, not a correctness risk.
  - The repository's own check is `make_ground.py --built` on the final board, which is in the reproduce block.
- **Pour gap rounding.** The pour-to-ACT_GATE gap is written 0.151 mm in D109 and R8_VALIDATION, and 0.150 mm in the
  `fix2_handoff.md` correction and pass 3. The rule is 0.15 mm and the fill sits a few µm outside it (the pass-3 routing
  reviewer measured 0.1505 mm), so both are the same copper at different rounding.
- **Renders.** `r8_top.png` and `r8_bottom.png` are still not byte-reproducible (pass 3's note). They are not fab
  outputs, and no record calls them reproducible.
- **Concurrent edits.** `r8_route_camera.py` was saved at 14:03, during fix pass 3's build 2 (13:56–14:09). Build 3 ran
  on the final files and matches builds 1 and 2, and my build matches all three. Nothing depends on which version
  build 2 read.
