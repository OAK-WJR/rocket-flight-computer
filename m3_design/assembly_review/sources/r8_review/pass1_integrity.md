# R8 review pass 1: build integrity

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987`
(worktree `rocket-flight-computer-r8`, branch `m3-assy-r8`, uncommitted on R7 commit 431025d).
**Dimension:** build integrity. Does `r8_build.sh` reproduce the board byte for byte from R7? Is every gate and per-step
check real, with no tool, allowlist, threshold or exemption weakened or special-cased against the R7 versions at
431025d? Do the tests fire on seeded defects? Do the rigid-copy hashes cover what they claim? Do the records claim only
verification that happened?
**Reviewer rules kept:** read-only on the repository (this file is the only write). Every run used scratch copies under
the session scratchpad, which were deleted afterwards.

**Verdict: 0 Critical, 0 Major, 3 Minor.** The build reproduces the board exactly. No gate was weakened to let R8 pass.
Every new check fires on the real board when a defect is seeded, and the rigid digests are R7's own. The Minor items are
records that overstate what a few plan checks gave, a requirement limit (F4 necks) that the build does not hold, and an
R8 design state that exists only in an uncommitted worktree.

## 0. Previous pass

This is the first review pass on R8, so no earlier R8 integrity findings exist to close. R7's review history had no
build-integrity dimension. Its accepted lists are kept verbatim for the R7 record; see section 2.3.

## 1. Reproduction (the build, byte for byte)

Method:
1. Fresh `git clone` of the parent repository, checked out at 431025d.
2. The worktree's files rsync'd on top, without `.git`. This gives the same tree as the worktree: 86 modified or
   untracked paths.
3. SHA-256 of every sheet, `schematic.net.xml`, `m3.kicad_pcb` and `m3.kicad_pro`.
4. `bash m3_design/r8_build.sh`, then the same hashes again.

| Item | Result |
|---|---|
| Exit status | 0 after 8 min 47 s. Every step gate printed OK: place, power, 9 × route, ground, then `tools/check.sh`. |
| Sheets (15), netlist, board, project | **byte-identical** to the worktree. Board `429b6db4…`, netlist `0cc1ed69…`. |
| Whole tree after the build (`diff -rq`, `.git` and `__pycache__` excluded) | identical. The build leaves no stray or changed file. |
| `check.sh` inside the build | DRC 0 at every severity, unconnected 0, parity 0, ERC 0. Audit OK, silk OK, `R8 CAD contract: OK`. Routing: 0 failing, 3 allowlisted, 0 stale. Actuators OK, fit OK. |
| Fab package (`r8_fab.sh` on the rebuilt board) | exit 0. CHECK none. CPL 85 top / 126 bottom, no errors. Paste check OK. Manifest OK. All 14 Gerber / drill / job files equal the committed zip's apart from creation-date lines. BOM and CPL byte-identical. |
| External inputs | none. No absolute or scratchpad path in `r8_*.py`, `check_r8`, `route_check`, `run_*.sh` or `r8_build.sh`. The spikes the generators read are in `m3_design/r8_spikes/`. |

`r8_pcb.py` asserts the R7 source SHA (`c872a3d3…`) and the 28 decided netlist changes. Every stage asserts the 12 rigid
digests: `r8_pcb.py:221`, `r8_power.py:508`, `r8_route.py:188`, `r8_ground.py:157` and `r8_post.py:373/380`. `r8_post`
also asserts that no copper, zone, pad or footprint position changed. Every gate script returns 1 on failure, and the
build runs under `set -euo pipefail`.

Independent netlist diff, R7 against R8 (`schematic.net.xml`, parsed per pin):
- **exactly 28 pin-net changes:** R310.1 3V3_RADIO → 3V3, plus 27 U1 pins;
- no component added, removed or re-valued;
- none of the safety-contract pins changed (2–5, 15, 16, 22–25, 32–34, 40, 97, 98).

## 2. Gates against R7 (431025d)

### 2.1 Files unchanged
`git diff 431025d` is empty for these files:
- the rule and project files: `m3.kicad_dru` (pyro rules A–H) and `m3.kicad_pro`;
- the gate tools: `quality_audit/`, `tools/fit_check.py`, `tools/silk_check.py`, `tools/check_r7.py` and
  `tools/test_r7_check.py`;
- `m3_design/check_actuators.py` (SHA `5de1eb3c…`, asserted by `check_r8.actuators_unchanged`).

The board's `setup`, `layers` and `general` sections are identical to R7's; only the title block differs. DRC exclusions
are `[]`, and ERC has no ignored rule. Nine project rule severities are `warning`, but `check.sh` counts every severity.

### 2.2 `tools/check.sh` (9 lines changed)
- `check_r7` → `check_r8`, and `route_check` → `--profile r8`.
- The board path is made absolute, because the audit runs in `quality_audit/`.

Nothing was removed. The `pipefail` handling of route_check's exit status is unchanged.

### 2.3 `tools/route_check.py` (657 lines changed)
- **Thresholds and classes unchanged:** the constant block (DETOUR_MAX 1.6, DETOUR_SLACK 2, VIA_SLACK 2, GND_REACH 1.5,
  SHORT, MICRO, the angle limits, POUR_STUB, the CHAIN_DETOUR limits, the sliver and finger limits), CLASSES, CRITICAL,
  RULE, HYGIENE, POUR and INFO. The block differs from 431025d only in a comment line.
- **`evaluate`, `leftover_check`, `measured_check`, `nognd_audit`, `alt_audit` and `bump_audit` unchanged.** With
  `LEFTOVERS = []`, every non-critical hygiene instance now fails, which is stricter than R7.
- **R7's lists moved verbatim** to `route_lists_r7.py`. Compared object for object with R7's `route_check.py` lists:
  ALLOWLIST 45, LEFTOVERS 29 and ROUTE_FIGURES 38, all **EQUAL**. `--profile r7` on the R7 board: 0 failing, 45
  allowlisted, 29 leftovers recorded, **OK**. `check_r7` on R7: OK. The `check.sh` header claim holds.
- **Profile r8 ALLOWLIST:** A8, plus D51's GNSS_LNA_EN and GNSS_VCC_RF detours, with ROUTE_FIGURES (6.45, 1) and
  (5.0, 1). All three match the board (route.json: 6.45 / 3.72 mm and 5.00 / 2.61 mm). `nognd_audit` finds no GND-via
  spot for A8; its nearest GND via is 2.717 mm away.
- **D10 keep-out-aware detour baseline** (the one change in how the test judges a net):
  - It applies only where a straight MST edge crosses an all-layer track keep-out, the U31 body, an NPTH or Edge.Cuts
    hole, or the outline. Parts, pads and other copper are never obstacles.
  - On the board, 9 nets are judged on it. **It changes the verdict of exactly one net: RADIO_TXEN** (plain 10.95 mm,
    ratio 2.30; keep-out-aware 20.11 mm, ratio 1.25). RADIO_RXEN's ratio goes from 1.30 to 1.21; the other 7 are
    unchanged or move by ≤ 0.01.
  - Four seeded tests cover it: a loop round a body passes; a detour beside the keep-out still fails; a one-layer
    keep-out does not refine; parts and foreign copper are never obstacles.
  - TXEN stays visible to the owner as deviation C5. Not a hidden weakening (see R8P1-INTEGRITY-01(e) on its owner
    status).
- **Trim prefix** `R8_POUR_TRIM_` added beside `R7_POUR_TRIM_`. That keeps `pad_pour_cut` applying to R8's trims, so it
  widens the check, and a seeded test covers both prefixes.

### 2.4 `tools/check_r8.py` (new) against `check_r7.py`
- `check_board` calls every check that R7's `check_board` calls:
  - the R7 functions imported unchanged: `duplicate_ids`, `pin_legends`, `legend_subjects`, `foreign_clearances`,
    `vias_on_through_pads`, `vias_in_smd_pads`, `overlap_only_joints`, `thermal_policy`, `rf_grounds`,
    `launch_reference`, `module_ground` and `rf_gnd_reach`;
  - `check_contract` and `rf_strip`, copied constant for constant with the R8 pin map, pulls and strip regexes;
  - R7's `rf_stitching`, split into `rf_line_stitching` (R7's code without the fence) and `fence()`.
- **Fence (D16):** R7 allowed two named openings of 6.1 and 3.8 mm. R8 allows openings of at most 2.7 mm, each crossed
  by a lane. R7 fails the R8 rule, so this is tighter. On R8: 25 fence vias and 4 openings of 2.015 / 2.6 / 2.1 / 2.05 mm,
  each crossed by lanes.
- **The U1 map** comes from `pin_table.tsv` (all 100 pins), and the table's contract pins are asserted (D14). This
  replaces R7's subsets and covers more.
- **New checks:** F10 separation, D18, D19, D20 and loader pins. Each one is non-vacuous on the board:
  - F10: nearest part 5.94 mm (R306–U1), nearest fast line 5.075 mm;
  - D18: 175 items checked, nearest 2.65 mm;
  - D19: 19 gate and 84 servo items, nearest 5.89 mm;
  - D20: only the 3.4 mm RIGID_IN2 link, exempt by exact geometry;
  - loader pins: 13 checked.
- **Exemptions in check_r8, all named and narrow:**
  - J124's pads in D18;
  - RIGID_IN2 in D20 (net, end points in nm and width in nm);
  - D5's LOADER_ALLOWED; see R8P1-INTEGRITY-01(b).

### 2.5 Other tool changes
- **`dc_solve.py`:** additions only (`--necks`, `--max-rise`). `cuts()` equals the survey's `dc_neck.py` function line
  for line, plus a `return`.
  - Its "< 1 mm total cut" level filter could in principle hide a thin neck. On R8's 0.05 mm evidence and on my 0.1 mm
    rerun it excluded no level (no "not counted" line).
  - The limit fails closed: `--max-rise 15` on ACT_FET_S prints `NECK FAIL: 22.5 C exceeds 15 C` and returns 1.
- **`jlc_corrections.json`:** two `via` comment strings only.
- **`test_check_shell.py`:** stage names only.
- **`test_route_check.py`:** additive (+7 tests); one test now covers both trim prefixes.
- **`test_r5_repair.py`:** retargeted to read the R5 board from git (D73). It was failing on R6 and R7 because its subject
  is literal R5 geometry, and it was never part of `check.sh`. It still fails on R6, R7 and R8 boards (D73), so it is not
  a weakening.

### 2.6 Per-step gates
The step gates hold LATER lists, the WEAK_EXCEPT pocket, L10_EXCEPT and ratcheted P9 / P10 limits. These only defer
findings to a later step, or pin measured values. Each one that survives to the final board is on the deviation list:
- WEAK_EXCEPT pocket: C2;
- L10_EXCEPT: C7;
- the P9 / P10 limits (4.6 / 9.7 mm against measured 4.48 / 9.65 mm): C3.

The final `check.sh` runs `check_r8` and route_check with no LATER filter.

`r8_sch_check.py` is not in `r8_build.sh`. Its content is covered by:
- `r8_pcb.py`'s assertion of the 28 changes;
- `check.sh`'s ERC and parity;
- `check_r8`'s pin map, RF-part coverage and RF-on-safety-net checks;
- `check_actuators`.

## 3. Tests

Every suite was run in the scratch copy (KiCad Python): **17 suites, 269 tests, all OK.**

| Suite | Tests | Suite | Tests |
|---|---:|---|---:|
| test_check_shell | 2 | test_r8_check | 20 |
| test_dc_solve | 3 | test_r8_ground | 11 |
| test_fab_validation | 23 | test_r8_place | 13 |
| test_fit_check | 23 | test_r8_power | 7 |
| test_maze_clearances | 10 | test_r8_route | 12 |
| test_paste_check | 5 | test_reference_audit | 3 |
| test_procurement | 15 | test_route_check | 57 |
| test_r5_repair | 13 | test_r6_check | 17 |
| test_r7_check | 35 | | |

quality_audit `test_quality_tools`: 21 OK under both Pythons. These counts match STATUS / M3_R8 (269 in 17 suites).

**Seeded defects on the real R8 board.** These are my own seeds, saved to a scratch copy with the project's rules, not
the synthetic test boards:

| Seed | Gate result |
|---|---|
| strip GND via (43.0, 9.0) moved 0.05 mm | `rigid group strip_gnd differs from R7` |
| fence via (24.15, 23.3) deleted | `strip fence: opening x 22.10-26.00 is 3.90 mm wide` and strip GND reach 4.3 mm > 4.0 |
| PYRO1_COLD track widened 0.01 mm | `rigid group ch1_copper differs from R7` |
| 1 mm SERVO1_MCU track on In2 | `In2 track of SERVO1_MCU … In2 carries power and GND only (S15, D20)` |
| RAW_ACT In1 track 1.2 mm from a PYRO1_BUS track end | D18 FAIL 0.11 mm (plan view), and the S16 In1-track FAIL |
| SERVO1_MCU F.Cu stub 0.3 mm from PYRO1_GATE_N | D19 FAIL (4 instances, 0.012–0.310 mm) |
| 10° stub on RADIO_SCK_MCU (route_check r8) | `off_angle`, `acute_angle`, `dead_copper`: 3 failing, verdict FAIL |

Every seed fired, and each failure names its own gate. `check_r8` reported 11 findings on the combined board.

## 4. Rigid-copy hashes

`check_r8.py --print-hashes` on the R7 board (431025d, `c872a3d3…`) reproduces `RIGID_BASELINE` exactly, all 12 groups.
On R8, the build's `check.sh` report gives the same 12 digests: outline 4, m3_holes 5, j122_tie 3, j1 1,
pyro_block_area 1, ch1_parts 22, ch1_copper 60, strip_parts 22, strip_rf_copper 11, strip_gnd 176, strip_rule_areas 5 and
strip_gcpw 8 items. The baseline is not re-baselined anywhere.

**Coverage against D15:** it matches D15.
- `ch1_copper` takes every track and via of the block-internal nets. For the three exit nets it takes the copper
  graph-reached from the block pads up to the exit via, and new copper T-ing into block copper would be reached too.
  It also takes GND ties up to the first via.
- `strip_gnd` is every GND via with y < 23.5 off the fence row, plus the GND track.
- The strip pours are asserted only through the F.Cu GCPW profile, as D15 states.
- Neither board has a zone on a PYRO / ARM net, so no block pour falls outside the hash.

What is not rigid, measured R7 against R8 (geometry-canonical tracks and vias with bbox top < 23.5 mm):
- 219 of R7's 301 strip items are unchanged, and 82 are regenerated: module interface leads, limiter DC copper, the
  3V3 / 3V3_GNSS / 3V3_RADIO feeds, and the fence row (22 → 25 vias);
- 4 of the 35 strip parts moved: R310 out of the strip (D4), and C300, R305 and R312 by 0.08–0.20 mm;
- the strip GND fill area changes by +3 to +6 mm² per layer.

This is what D11 / D15 decided. Some summaries say more; see R8P1-INTEGRITY-01(d).

## 5. Records against what ran

These were verified as true:
- byte-identical rebuild;
- `check.sh` exit 0;
- 269 tests;
- check_r8 evidence figures (F10 5.94 / 5.08 mm, D18 2.65 mm, fence ≤ 2.7 mm);
- D10 changes only TXEN;
- check_r7, test_r7_check and route_check r7 reproduce R7's verdict;
- the quick scorecard: index 14.4, S1 1500.1, S4 55, S12 25, S17 1642.9, P9 / P10 4.48 / 9.65, R6b 0.1157, P6 1788.7,
  all equal to R8_VALIDATION;
- fit categories ≥ R7: C84 1.37 against 0.11 mm, worst bottom 2.36 against 2.34, support clearance 4.452 against
  4.150;
- the cost binding to the current BOM / CPL;
- the 0.1 mm DC necks: RAW_ACT 5.90 mm / 17.6 °C, BAT_IN 6.86 / 14.8, ACT_FET_S 4.77 / 22.5 (D49's 0.1 mm row within
  0.01 mm).

The overstatements are in R8P1-INTEGRITY-01.

## 6. Findings

### R8P1-INTEGRITY-01 (Minor, worth fixing): R8_VALIDATION and summaries present relaxed or skipped plan checks as passed

(a) **"each step's verification passed"** (`docs/R8_VALIDATION.md:3`, and the step table's "Verification (each
passed)" column) is not true of two steps:
- Step 1's plan verification includes "independent review" (`r8_plan.md:47`). Its handoff says this was not done
  (`r8_step1_handoff.md:172-173`, "no reviewer agent was available").
- Step 7's verification is "C6 = 0, P7 = 0, P9/P10" (`r8_plan.md:64`). The board has C6 = 1 and P7 = 1, and P9 / P10
  miss their targets. The coordinator's ruling D68 dispositioned these; they did not pass.

The table row for step 7 (`:31`) lists the misses, but under a "passed" heading.

(b) **The hard-gate row "Reset / loader pin table: only LEDs on loader-driven pins — met (D5)"** (`:48`). The plan gate
reads "allows only LEDs" (`r8_plan.md:17`). `check_r8.LOADER_ALLOWED` (`tools/check_r8.py:74`) admits six non-LED nets.
On the board, 7 of the 13 loader-driven pins carry them: PA2 SERVO3_MCU, PA11 / PA12 USB, PB6 QSPI_NCS, PB9 I2C1_SDA,
PB10 RADIO_SCK_MCU and PB14 RADIO_MOSI_MCU (r8.json `loader_pins`). D5's reasons look sound: the radio is held in reset
by R311 and deselected by R310. Even so, the gate as built is D5's rule, not the plan's.

(c) **The hard-gate row "route_check C1 / C3 / C4 / C6 = 0 except owner-accepted inherent items — 0 failing"**
(`:44`). The plan admits only TXEN and A8, owner-accepted (`r8_plan.md:16`). All three R8 allowlist entries await owner
acceptance; two of them (D51) are new to R8's allowlist. The scorecard tool itself marks C3 "hard gate: A8 only — no".
The gate passes because the entries are allowlisted, not because the plan's condition holds.

(d) **"The strip copper is R7's"** appears in three places: AGENTS.md:15 ("the strip copper is R7's, rigid and
hash-asserted"), REQUIREMENTS F10 ("holds the strip copper to R7's by hash") and M3_R8.md:282. M3_R8's "Kept rigid" list
and D15 are accurate. Measured (section 4): 82 of R7's 301 strip copper items were regenerated, including the whole
fence row, and 4 strip parts moved.

(e) **D10 (M2's detour test redefined in the REQUIREMENTS text)** and D5 are agent decisions that relax a plan gate or an
owner criterion. The owner summary asks the owner to accept the deviation list but does not name these two redefinitions
as decisions to accept.

**Fix (records only; no copper, gate or table change):**
- Reword R8_VALIDATION line 3 and the step table, e.g. "step 1's independent tool review: done by R8 review pass 1
  (build integrity)" and "step 7: C6 = 1 (A8), P7 = 1, P9 / P10 missed, dispositioned D68 for owner acceptance".
- Hard gates:
  - loader-pin row: "D5's rule (LEDs plus six reasoned nets) met; the plan's LEDs-only rule is not";
  - route_check row: "not met until the owner accepts A1–A3".
- Make AGENTS / REQUIREMENTS F10 / M3_R8 RF say "the RF lines, strip parts and strip GND field (D15 groups) are R7's".
- Add D5 and D10 to the owner summary's decision list.

### R8P1-INTEGRITY-02 (Minor, worth fixing): the F4 7.7 A neck limits are not held by the build or the gate

REQUIREMENTS F4 (R8 text) and R8_DECISIONS D12 set numeric limits: RAW_ACT and BAT_IN ≤ 20 °C, ACT_FET_S ≤ 30 °C, by
the IPC-2152 neck. `r8_build.sh` and `tools/check.sh` never run `tools/run_dc.sh`: "the 7.7 A DC solves run apart"
(`m3_design/r8_build.sh:22`, `m3_design/r8_power_check.py:22`).

The current board meets the limits:
- step 9's 0.05 mm evidence;
- my 0.1 mm rerun, exit 0: 17.6 / 14.8 / 22.5 °C.

r8_plan §4 sends every fix "into tables or generators, then rebuild and rescore", and only the soft scorecard re-runs
the DC solves. A fix to a power table could therefore narrow a neck past its limit with every gate green.

The step-9 DC evidence files (`step9/evidence/dc005_dc_*.txt`) also do not carry the board SHA-256 that F4 asks the
solve to be bound to. The binding is stated only in prose.

**Fix:**
- Add `tools/run_dc.sh "$D/m3.kicad_pcb" "$(mktemp -d)" 0.1` to `r8_build.sh` after `r8_ground_check.py` (copper
  final). It fails closed on `--max-rise`, and the three 0.1 mm solves took under two minutes here (ACT_FET_S 2 s).
- Have `dc_solve.py` print the board's SHA-256 in its header line.

### R8P1-INTEGRITY-03 (Minor, worth fixing): the R8 design exists only as an uncommitted worktree

All R8 inputs are untracked or modified in the worktree, with no commit on `m3-assy-r8` (`git status`: 37 modified and
49 untracked paths). That covers the generators (`m3_design/r8_*.py`), tables (`r8_place.tsv`, `r8_keepclear.tsv`,
`r8_ground.tsv`, `pin_table.tsv`), gate tools (`check_r8.py`, the new tests, the route_check changes), spikes,
decisions and records.

"Rebuilds byte for byte from the committed R7 (431025d)" is true only in the presence of this worktree:
- Losing the worktree (a worktree clean-up, a disk problem) loses R8 and its reproducibility.
- Review passes and fix passes have no commit to name as "the reviewed generator state". A finding's file:line can
  drift silently.

**Fix (owner action; AGENTS: commit only when asked):**
- Commit, or tag a snapshot of, the exact state reviewed here on `m3-assy-r8` before the fix pass. Record its hash in
  R8_VALIDATION beside the board SHA.
- Later fix passes then diff against it.

## 7. Notes (no finding)
- The D12 limits and D68 are described as "owner-delegated". They are agent rulings under R8_DECISIONS' standing
  delegation, and they stay on the owner's acceptance list. MARGIN P1-9's 10 mm is recorded as not met.
- The LATER entry for the ARM1_SENSE In2 link in `r8_route_check.py` / `r8_ground_check.py` is now dead, because D70's
  RIGID_IN2 suppresses that finding at the source. It is harmless.
- D5's text says PA10 must stay NC, but `LOADER_DRIVEN` omits PA10 (it is an input in AN2606 Table 135). The pin-table
  map still pins it NC.
