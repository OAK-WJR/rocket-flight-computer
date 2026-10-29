# R8 review pass 2: build integrity

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d`
(worktree `rocket-flight-computer-r8`, branch `m3-assy-r8`, uncommitted on R7 commit 431025d).

**Dimension:** build integrity. The questions:
- Does `r8_build.sh` reproduce the board byte for byte from R7?
- Is every gate and per-step check real? Nothing may be weakened or special-cased against the R7 versions at 431025d,
  or since pass 1.
- Do the tests fire on seeded defects?
- Do the rigid-copy hashes cover what they claim?
- Do the records claim only verification that actually happened?

**Reviewer rules kept:** the repository was read-only; this file is the only write. Every run used scratch copies under
`…/scratchpad/p2int/`, which were deleted afterwards. Only the small measurement scripts in `p2int/scripts/` remain.

**Verdict: 0 Critical, 0 Major, 5 Minor.**
- The build reproduces the whole tree exactly from a fresh clone of 431025d.
- No gate, threshold, allowlist or exemption was weakened to let R8 pass. The fix pass made three changes of that
  kind, and each one is named and on the owner's list: the limiter figures, the rf budget ratio and the J123.2
  exception.
- The new gates (`battery_pyro`, `via_paste`, `terminal_legends`, the DC neck gate) fire on seeded defects on the real
  board. The 12 rigid digests are still R7's own.
- The Minor items:
  - J123.2's M2 exception rests on a DRC result from an intermediate build stage. It does not hold on the final copper.
  - `via_paste` is described as R7's rule but is looser than it.
  - The R8 state is still uncommitted, and pass 1's generator state is now lost.
  - The DC gate has no automated test.
  - A handful of small record inaccuracies.

## 0. Previous pass (R8P1-INTEGRITY-01…03)

| Pass-1 finding | Status on `6600ef94…` | Evidence |
|---|---|---|
| 01 Records present relaxed or skipped plan checks as passed | **Closed** | The R8_VALIDATION step table now reads "as run; misses and relaxed checks named": step 1's tool review is credited to pass 1, and step 7 names C6 = 1, P7 = 1 and P9 / P10 missed (D68). In the hard gates, the loader row reads "D5's rule met … the plan's LEDs-only rule is not" and the route_check row reads "not met until the owner accepts A1–A3". AGENTS:15, M3_R8:341 and F10 now say "the RF lines, strip parts and strip GND field (D15's groups)". The owner summary lists D5, D10, D12, D68, D87 and D89 as relaxations. |
| 02 F4 neck limits not held by the build; DC evidence not SHA-bound | **Closed** | `r8_build.sh` runs `tools/run_dc.sh … 0.1` after `r8_ground_check.py` and before `r8_post.py`, and `r8_post` asserts that the copper does not change. In my build it printed RAW_ACT 5.90 mm / 17.6 °C, BAT_IN 6.86 / 14.8 and ACT_FET_S 4.80 / 22.3 (D12: 20 / 20 / 30). It fails closed (§3). `fix1_dc_{raw,bat,fet,gnd}.txt` start with `sha256 6600ef94…`. |
| 03 R8 exists only as an uncommitted worktree | **Open** (owner action): still uncommitted, and pass 1's reviewed generator state is now unrecoverable | R8P2-INTEGRITY-03 |

## 1. Reproduction (the build, byte for byte)

Method:
1. Fresh `git clone` of the parent repository, checked out at 431025d.
2. The worktree rsync'd on top, without `.git` or `__pycache__`. That gives the same 88 status paths as the worktree.
3. SHA-256 of every file in the tree (1271 files).
4. `bash m3_design/r8_build.sh`, then the same 1271 hashes again.

| Item | Result |
|---|---|
| Exit status | 0 after 821 s. Every step gate printed OK: place, power, 9 × route, ground, the DC neck gate, `r8_post`, then `tools/check.sh`. |
| Whole tree after the build | **identical** (`diff` of the 1271 hashes is empty). Board `6600ef94…`, netlist `0cc1ed69…`, all 15 sheets unchanged. The build leaves no stray or changed file. |
| `check.sh` inside the build | DRC 0 at every severity, unconnected 0, parity 0, ERC 0. Metadata / 3D audit OK; silk 0 stroke points outside. `R8 CAD contract: OK`. Routing: 0 failing, 3 allowlisted, 0 leftovers, 0 out-of-date figures, 0 removable bumps (22 windows). Actuators OK; fit OK. |
| DC gate inside the build | The three solves ran at 0.1 mm, bound to the pre-`r8_post` board `278b952a…`. That board's copper is identical to the final one: `r8_post.py:407-416` asserts the rigid digests and a digest of every copper item, zone and pad. |
| Fab (`r8_fab.sh` on the rebuilt board) | Exit 0. CHECK none. CPL 85 top + 126 bottom, worst 0.491 mm, no errors. Paste check OK (348 / 359 flashes). Manifest OK. BOM `be711876…` and CPL `c0ee08ae…` are byte-identical to the worktree's. All 14 Gerber, drill and job files differ only in their `CreationDate` lines. |
| `r8_ground.tsv` | `step7/make_ground.py <final board> out.tsv --built` reproduces it byte for byte (199 rows). D90's "two-pass `--built`" claim holds. |

## 2. Gates against R7 (431025d) and against pass 1

### 2.1 Files unchanged since R7
`git diff 431025d` is still empty for these files:
- the rule and project files: `m3.kicad_dru` and `m3.kicad_pro`;
- `quality_audit/`;
- the gate tools: `tools/fit_check.py`, `tools/silk_check.py`, `tools/check_r7.py` and `tools/test_r7_check.py`;
- `m3_design/check_actuators.py`, whose SHA-256 `check_r8.actuators_unchanged` asserts.

`check.sh` is unchanged since pass 1 (the same 9-line diff from R7). The route_check exit status still reaches `set -e`
through `pipefail`.

### 2.2 What fix pass 1 changed in the gates

There is no commit of the pass-1 state, so I rebuilt the fix-pass gate edits from its edit scripts in the session
scratchpad: `fix1/e_rc.py`, `e_rfb.py`, `e_cr8.py`, `e_dc.py`, `e_t8.py`, `e_pcb*.py` and `e_post*.py`. I checked
each against the current files. The changes:

- **`tools/route_check.py`:** the limiter reason text, and ROUTE_FIGURES (6.45, 1) / (5.0, 1) → (7.65, 1) / (6.2, 1)
  (D87: the limiter vias returned to R7's y 8.3, clear of U30's paste).
  - The constant block, CLASSES, `evaluate`, `measured_check`, `nognd_audit`, `alt_audit` and `bump_audit` are
    unchanged.
  - The functional diff from R7 has the same hunks pass 1 reviewed: the profiles, the D10 baseline and TRIM_PREFIXES.
  - `--profile r7` on R7 (`c872a3d3…`) gives a report whose `allowed` (45), `instances` (326), `failures`, `stale`,
    `leftovers` (29), `measured_check`, `nognd_audit` and `alt_audit` are **object-equal** to R7's own `route_check.py`
    (run from an R7 tree). The summary line is identical too: OK.
  - D10 still changes the verdict of RADIO_TXEN only: 9 nets are judged on it, and the other 8 move by 0–0.09.
- **`m3_design/r8_route_rf.py` BUDGET:** ratio 1.95 → 2.40 (GNSS_VCC_RF 2.37). This loosens a step budget to the
  measured value. It is named in D87, in the comment and in the owner summary's list of relaxations.
- **`tools/check_r8.py`:** three new gates (`battery_pyro`, `via_paste`, `terminal_legends`), each called from
  `check_board`. No other change was made. The exemption set is still pass 1's: J124's pads in D18, `RIGID_IN2` and
  `LOADER_ALLOWED`.
- **`tools/dc_solve.py`:** additions only:
  - the board SHA as the first output line;
  - `--window` (only used by the opt-in DC_GND row);
  - `--via-currents`;
  - vias outside the grid skipped (a no-op without `--window`).
  The neck code is unchanged, and the docstring is corrected (R8P1-POWER-06).
- **`tools/run_dc.sh`:** via currents and the opt-in DC_GND row (reported, not gated, as documented).
- **Step gates:**
  - `LATER` entries for the terminal legends (`r8_route_check.py:69`, `r8_ground_check.py:76`). They defer the finding
    to `r8_post`, and the final `check.sh` runs `check_r8` with no filter.
  - `r8_place_check.TAB_PLAN` (D93).
  - `r8_pcb.THERMAL_PADS`, which asserts that each pad was R7's FULL before relieving it.
- **Tests:** +3 (`test_r8_check` 20 → 23).

### 2.3 Rigid digests
`check_r8.py --print-hashes` on the R7 board reproduces `RIGID_BASELINE` exactly, all 12 groups. The build asserts them
at every stage. Two measurements, R7 against R8:
- F.Cu GND under the U31 body: 79.771 mm² on both.
- F.Cu GND inside the U30 keep-out box: 74.625 mm² on both.

## 3. Tests and seeded defects

**Suites:** 17 suites, **272 tests, all OK** (KiCad Python, in a scratch copy). That matches STATUS, the handoff and
R8_VALIDATION. quality_audit: 21 OK under both Pythons.

**Mutation of the three new tests** (`test_r8_check.py`): each test fails when its gate is mutated.

| Mutation | Result |
|---|---|
| `battery_pyro` returns no issues | its test fails |
| `via_paste` returns no issues | its test fails |
| `terminal_legends` returns no issues | its test fails |
| `battery_pyro` limit lowered to 0.4 mm | its test fails |
| `via_paste` hole gap set to 0 | its test fails |

**Seeds on the real board** (`6600ef94…`, in memory, never saved):

| Seed | Result |
|---|---|
| none (baseline) | all three gates clean. battery_pyro nearest 1.089 mm (ACT_FET_S zone to J124.1, B.Cu); via_paste 705 pairs, nearest ring 0.025 mm (C90.1); 10 legends |
| C90.1's 3V3 via (34.8, 53.68) moved 0.05 mm toward the pad | `via ring overlaps the paste aperture (D87)` |
| that via shrunk to Ø0.35 mm and moved 0.15 mm toward the pad (ring clear, hole near) | `via hole is within 0.1 mm of the paste aperture` |
| ACT_FET_S 0.3 mm track 0.8 mm from J124.1 on B.Cu (then on In1) | `… 0.800 mm from PYRO1_BUS J124.1 …; minimum 1.0 mm (D85)`, on both layers |
| '4:SW' moved beside J124.1 | `nearest connector pin is J124.1` and `J1.4: 0 legends` |
| '1:BUS1' deleted | `J124.1: 0 legends "1:BUS1"` |
| `run_dc.sh` with ACT_FET_S `--max-rise 15` (scratch copy) | `NECK FAIL: 22.3 C exceeds 15 C`, `run_dc.sh` exit 1. Under `r8_build.sh`'s `set -e` that stops the build. |

## 4. Records against what ran

Each of these was verified:
- **Byte-identical rebuild:** "two builds identical, 17 files"; my independent build matches.
- **`check.sh` exit 0**, and the hard-gate figures: F10 5.94 / 5.075 mm, D18 2.65 mm, D19 none within 2 mm, battery_pyro
  1.089 mm, via_paste 705 pairs at 0.025 mm, 10 legends, fence openings 2.015 / 2.6 / 2.1 / 2.05 mm, and the loader map.
- **272 tests.**
- **The M2 sweep:** I ran `step9/m2_sweep.py` on the board, and every key is **equal** to `fix1_m2_sweep.json`. It
  gives 23 chain detours (17 critical), 32 net pairs under 0.2 mm (14 at 0.150), 12 nets over their via need (none over
  need + 2), 26 via folds and pad-edge 0.
- **The quick scorecard** (`NO_DC=1 NO_GATE=1 run_survey.sh`): every non-DC row equals R8_VALIDATION's. That covers
  S1 1498.8, S4 55, S6 / S7 1.176 / 288.8, S8 / S9 4 / 4, S10b 231, S12 25, S15 3.4, S17 1638.7, C1 / C2 / C3 / C6
  3 / 93 / 3 / 1, P1 0.9054, P3b 3, P4 5, P6 1782.9, P7 1, P9 / P10 4.48 / 9.65, R1 / R3 2.9 and R6b 0.1107. The quick
  index is 13.7; the record's 15.3 includes the 0.05 mm DC rows.
- **The DC figures:** the 0.05 mm evidence (17.5 / 14.5 / 21.4 °C; 0.86 / 0.67 A via maxima; GND return 0.72 mΩ with
  the 62.8 °C IPC figure explained in M3_R8:191-195) and the 0.1 mm build figures (17.6 / 14.8 / 22.3 °C).
- **The binding note** names `6600ef94…`.
- **`cost_check.json`** still binding the step-9 CPL is stated openly.

The inaccuracies are listed in §5.

## 5. Findings

### R8P2-INTEGRITY-01 (Minor, worth fixing): J123.2's solid-connection exception rests on an intermediate-stage DRC result that is false on the final copper

**What the records say.** D89, R8_VALIDATION C17 (`:228`), the DFM-03 disposition (`:162`), the owner summary (`:193`)
and the `r8_pcb.py:179-185` comment all say: "J123.2 stays solid: with the relief … KiCad's DRC reports starved_thermal
on B.Cu". The decision rests on that claim.

**Where the claim came from.** The fix pass's log `scratchpad/fix1/b3.log` shows `drc FAIL (1) starved_thermal … PTH
pad 2 [GND] of J123` at **"R8 route gate (status)"**. That is the step-6 board, before step 7's GND stitching.

**What the final copper does.** Method: a scratch copy of `6600ef94…` with J123.2 set to `ZONE_CONNECTION_INHERITED`
(THT thermal, 0.5 mm gap, 0.5 mm spokes), refilled by native `ZONE_FILLER`, with R8's `.kicad_pro` / `.kicad_dru` /
`fp-lib-table` / kilib beside it, then `kicad-cli pcb drc --severity-all`. Results:
- **0 violations.**
- With `min_resolved_spokes` raised to 4 as a probe, DRC reports `starved_thermal … layer B.Cu; zone min spoke count 4;
  actual 2`. So B.Cu has 2 spokes, exactly the project's minimum of 2, and F.Cu and In1 each have at least 4.
- **Negative control** (the same procedure on J122's four GND pins): `starved_thermal … F.Cu … actual 1` on J122.3. So
  the check is live on these copies.

**Consequence.**
- REQUIREMENTS M2 asks for reliefs "wherever their spokes are not starved". On the final copper they are not starved,
  so the recorded measured reason, and the C17 deviation that the owner is asked to accept, describe a board that is
  not the one built.
- A secondary point: C17 also says that J122's GND pins are "starved on B.Cu". DRC flags only J122.3, and on F.Cu.
  J122 stays solid on its other grounds (the rigid `j122_tie` digest includes its pads' zone connection, and it carries
  the 7.7 A return), so only the wording is off.

**Fix:** either one of these.
- Give J123.2 the relief on the final copper. Either:
  - put it back in `THERMAL_PADS` and add a step-gate `LATER` for exactly `starved_thermal` on J123.2 in
    `r8_route_check` / `r8_power_check` (the final `check.sh` holds it); or
  - set the connection in `r8_ground.py` before its fill.

  Then regenerate `r8_ground.tsv` with `make_ground.py`, rebuild, and drop J123.2 from C17.
- Or, if the owner prefers it solid, change the reason to: "starved only on the step-6 board; DRC-legal with the relief
  on the final copper (B.Cu 2 spokes); kept solid by choice". Keep it on the owner's list as a choice, and correct
  C17's J122 wording.

### R8P2-INTEGRITY-02 (Minor, worth fixing): `check_r8.via_paste` is described as R7's ViaCheck rule but is 0.1 mm looser on the via ring

**What the records say.**
- `tools/check_r8.py:36-37` says: "no via ring overlaps a solder-paste aperture and no via hole lies within 0.1 mm of
  one …: R7's r7_route.ViaCheck rule".
- `:108` comments `VIA_PASTE_HOLE = 0.1  # via hole to a paste aperture (r7_route.ViaCheck; step7/make_ground.py)`.
- D87 says "R7's rule (r7_route.ViaCheck: vias kept off the paste apertures)" and "nearest ring now 0.025 mm, C90.1, as
  R7's closest".

**What the cited rules do.** Both cited sources keep the whole ring **0.1 mm** from the aperture:
- `git show 431025d:m3_design/r7_route.py` lines 523-527:
  `o.GetEffectiveShape(lay).Collide(c, MM(0.1))` for the paste layers, where `c` is the via's full Ø circle.
- R8's own `step7/make_ground.py:271-273`: `TransformShapeToPolygon(forbid, paste, MM(0.1 + r + MARGIN))`.

The gate only keeps the ring off the aperture (0 mm) and the hole 0.1 mm away.

**Measured** with the gate's own `paste_polys` and `min_gap`:
- On `6600ef94…`, **14 vias** have their ring within 0.1 mm of a paste aperture: 0.025 C90.1 (3V3), 0.033 C7.1
  (VLOGIC), 0.050 C60.2 (GND) and U10.3 (VBUS), 0.064 D4.2 (GND), 0.070 C300.2 (fence via), 0.071 R71.2 / R72.1
  (CAM_FB), 0.075 C93.1, R165.2, R76.1 and R78.2, 0.087 R310.1, and 0.090 C76.2.
- All are own-net and tented.
- R7 (`c872a3d3…`) had **5** (worst 0.025, R81.2).

So "as R7's closest" is true of the minimum only. R8 has nearly three times R7's count against R7's rule.

No requirement is broken: M2's via rule concerns mask openings, and `vias_in_smd_pads` holds it. But the gate's
description misstates its strength, and the D87 record compares R8 with R7 on the minimum alone.

**Fix (records):**
- State the gate's real rule in the docstring, the `VIA_PASTE_HOLE` comment, D87 and R8_VALIDATION's hard-gate row: ring
  off the aperture, hole ≥ 0.1 mm, looser than ViaCheck and make_ground's 0.1 mm ring.
- Record the 14 against R7's 5.
- Whether to tighten the ring clause to 0.1 mm, and move the few vias that are not R7's, is DFM's call.

### R8P2-INTEGRITY-03 (Minor, worth fixing; owner action): R8 is still uncommitted, and pass 1's reviewed generator state is lost

`git log` still ends at 431025d, and `git status` shows 88 paths: 37 modified and 51 untracked, including every
`r8_*.py`, `check_r8.py`, the tables, the records and the reviews. R8_VALIDATION `:403-404` asks to "commit or tag the
generator state reviewed (pass 1, `429b6db4…`) and the fixed one". The pass-1 state can no longer be committed: fix
pass 1 overwrote it in place.

Two consequences:
- This review could reconstruct the fix pass's gate edits only from its temporary edit scripts in the session
  scratchpad (`fix1/e_*.py`, applied by `rep.py`). Edits made another way would not be visible.
- Pass 2's citations (file:line) are again tied to an uncommitted tree that the next fix pass will rewrite.

Nothing R8 needs is gitignored (`git ls-files --others --ignored` lists only `m3.kicad_prl`), so a plain `git add -A`
captures it all.

**Fix (owner):**
- Commit or tag the current state (`6600ef94…`) on `m3-assy-r8` before fix pass 2 starts, and record its hash beside
  the board SHA in R8_VALIDATION.
- Reword `:403-404`: the pass-1 state was not preserved; the fix-pass deltas are described in `fix1_handoff.md`.
- Have later fix passes diff against that commit.

### R8P2-INTEGRITY-04 (Minor, not worth fixing on its own): the build's DC neck gate has no automated test

R8P1-INTEGRITY-02 put `run_dc.sh … 0.1` into the build. The build's neck check therefore rests on two things:
- `dc_solve.py --max-rise` returning nonzero on a miss;
- `run_dc.sh` passing that on through `wait "$p" || rc=1`.

`tools/test_dc_solve.py` has three tests, and all three cover only the stack-up reader. None runs `--necks` or
`--max-rise` or checks the exit status. The behaviour is right today: pass 1 and this pass both seeded it, and
`run_dc.sh` exits 1 on `NECK FAIL: 22.3 C exceeds 15 C`. But a refactor could break it with every suite green.

**Fix:** add one synthetic-board test (a narrow strip between two pads). `--necks --max-rise` below the computed rise
must return 1, and above it must return 0. Optionally, also test that `run_dc.sh` exits 1 when one of its three solves
fails.

### R8P2-INTEGRITY-05 (Minor, worth fixing): small record inaccuracies

- **Wrong date.** `STATUS.md:10` dates fix pass 1 "2026-10-20". It ran on 2026-10-19: the fix-pass files were modified
  19:04–22:13 that day, and the Gerbers carry `CreationDate 2026-10-19T21:37:37`.
- **Self-contradiction on the module ground.**
  - R8_VALIDATION `:143` (the R8P1-RF-02 disposition) justifies not adding the F.Cu module-ground gate because
    "strip_gcpw and the rigid strip_gnd / strip_parts digests already fail on any change there".
  - The same file's note `:366-370` says "Still ungated: where a trim lands".
  - The note is the accurate one:
    - `strip_gcpw` samples only beside the RF lines;
    - `strip_rule_areas` hashes only the four named areas (`check_r8.py:1059-1060`);
    - `module_ground` checks In1 / In2, not F.Cu.

    So a new F.Cu pour trim, or a change to the zone settings, under a module body changes no digest. Today's copper
    is unaffected: F.Cu GND under the bodies is measured equal to R7's (§2.3).
- **Evidence not bound to the board.** R8_VALIDATION `:91` says fix pass 1 "re-measured on `6600ef94…`" with evidence
  in `step9/evidence/fix1_*`. Four of those files carry no board SHA: `fix1_pyro_neighbours_r8.json`,
  `fix1_refaudit_r8*.json`, `fix1_requalify_r8.json` and `fix1_route_check_report.json`. The DC, M2-sweep,
  measurements and check_r8 files do carry one.

**Fix:**
- Correct the date.
- Reword RF-02's reason to "the F.Cu GND under the bodies is measured equal to R7's; where a trim lands stays ungated".
- Add a `board_sha256` field to those four evidence files, or name the board in a header line.

## 6. Notes (no finding)

- **Dead entry.** The `LATER` entry for the ARM1_SENSE In2 link in `r8_route_check.py` / `r8_ground_check.py` is still
  dead, because RIGID_IN2 suppresses it at the source. It is harmless.
- **J3's relief.** J3.1 / J3.4's relief is DRC-clean on the final board. P3b's two new In1 "slots" are those relief
  rings.
- **Allowlist figures.** The A2 / A3 figures (7.65 / 6.20 mm) match the board: `measured_check` is 0 out-of-date in the
  build. A2 is 0.20 mm longer than R7's 7.45 mm for the same via spot, a routing matter.
- **Step budgets.** `r8_route_usb_swd.BUDGET` ratio 1.35 is unchanged; its worst ratio fell to 1.25. No other family
  budget moved.
- **Build order.** The build runs the DC gate before `r8_post`, so its SHA lines name the pre-post board. The final
  board is bound through `fix1_dc_*.txt` (0.05 mm) and through `r8_post`'s copper-unchanged assertion.
