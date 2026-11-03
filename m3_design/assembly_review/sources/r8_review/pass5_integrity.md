# R8 review pass 5: build integrity

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7`
(fix pass 4; worktree `rocket-flight-computer-r8`, branch `m3-assy-r8`, uncommitted on R7 commit 431025d).

**Dimension:** build integrity, as a focused confirming pass after fix pass 4. The questions:
- Does `r8_build.sh` still reproduce the board byte for byte from R7?
- Is every gate and per-step check real? Was anything weakened or special-cased, against R7 (431025d) or since pass 4?
- Do the tests and gates fire on seeded defects, in particular round fix pass 4's copper?
- Do the rigid-copy hashes cover what they claim?
- Do fix pass 4's records claim only verification that happened?
- Against the pass-4 board `c84f00b8…`, did anything change besides the two items' copper and the regenerated GND
  fill and vias?

**Reviewer rules kept:**
- The repository was read-only, and this file is my only write. `git status` was the same 89 paths at the end as at the
  start (38 modified, 51 untracked; `p5int/gitstatus_before.txt` = `gitstatus_after.txt`), and the board still hashes to
  `cc044ea0…`.
- Builds, the fab run, the tests and the step-6 rebuild ran in a fresh clone under `…/scratchpad/p5int/clone`. The pass-4
  state was rebuilt in a second clone (`p5int/c84`). Read-only scripts ran on scratch copies of the boards, and the seeds
  were applied in memory with no board saved. The clones, board copies and Gerber extracts were deleted afterwards;
  logs, small result files and my scripts (`p5int/scripts/`) remain (1.3 MB).

**Verdict: 0 Critical, 0 Major, 2 Minor.**
- **Reproduction:** the build reproduces the whole tree byte for byte from a fresh clone of 431025d (1351 files; the only
  addition is the gitignored `m3.kicad_prl`). The step-7 table regenerates byte for byte from the real step-6 board, and
  from the final board with `--built`.
- **Fix pass 4's record:** its 276-hash baseline and its five-file generator diff are exact and complete, and the set of
  files it changed is exactly the handoff's list.
- **Gates:** fix pass 4 changed no gate, test, allowlist, threshold or exemption file; every one is byte-identical to the
  pass-4 state. The R7 diffs are the ones passes 1–4 reviewed. No code keys on a board SHA.
- **Board diff against `c84f00b8…`:** only D110's three radio lanes (9 segments) and three GND vias, D111's USB_LIMITED
  segments (−4 +3) and the zone fills differ. The fills are F / B GND plus, as a direct consequence of the moved stitch
  via, the In2 3V3 pour's clearance ring round it (02). Footprints, text, drawings, zone outlines and setup are equal.
- **Seeds:** check_r8's fence check, the step-7 table gate and the strip_gnd digest each fire on a seeded defect at fix
  pass 4's moved vias and lanes. The fence row is not rigid, as D16 says.
- **Rigid digests:** the 12 digests are still R7's: R7's board and the final board print identical values, equal to
  `RIGID_BASELINE`.
- **Records:** every fix-pass-4 claim I checked holds, and the records say plainly that `cc044ea0…` was not itself
  reviewed.
- **The Minor items:**
  - **01:** still uncommitted (owner action, carried).
  - **02:** fix pass 4's notes list the zone changes as F / B GND only; the In2 3V3 antipad shift round (22.05, 26.7) is
    unrecorded. It is area-neutral and documentation only.

## 0. Previous pass (R8P4-INTEGRITY-01, -02)

| Pass-4 finding | Status on `cc044ea0…` | Evidence |
|---|---|---|
| 01 R8 uncommitted | **Open** (owner action), carried as R8P5-INTEGRITY-01 | `git log` still ends at 431025d; 89 status paths |
| 02 `r8_build.sh` stage note said "six pour trims" | **Closed** | `m3_design/r8_build.sh:31` reads "seven pour trims (D65, D90)". The build prints "r8_ground: 193 GND vias, 1 GND track(s), 7 pour trims", and the regenerated table has `trim: 7`. The change is a comment only: the build output is byte-identical (§1) |

The pass-4 records pass also changed `step9/requalify.py` (rule G added: gate nets in the block, 0.3 mm) and regenerated
`fix3_requalify_r8.json`, as R8_VALIDATION:43–45 says. I diffed the records-pass state against the tree pass 4 hashed
(`p4int/tree_before.txt`). Besides the eight `pass4_*.md` files it added, it changed exactly AGENTS, README, STATUS,
M3_R8, ORDERING, R8_VALIDATION, REQUIREMENTS, R8_DECISIONS, `fix3_handoff.md`, `requalify.py` and that one evidence file.
`requalify.py` is review code: no gate, test or build stage references it (`grep` over `tools/` and `m3_design/*.{py,sh}`
is empty), and its change adds a rule rather than removing one.

## 1. Reproduction (the build, byte for byte)

**Method:**
1. Fresh `git clone` of the parent repository, checked out at 431025d.
2. The worktree rsync'd on top, without `.git`, `__pycache__` or the gitignored `m3.kicad_prl`. The clone's
   `git status` is the worktree's 89 paths, line for line.
3. SHA-256 of every file (1351 files, `p5int/tree_before.txt`).
4. `bash m3_design/r8_build.sh` (`p5int/build1.log`).
5. The hashes again (`tree_after.txt`), then the post-build checks (`p5int/scripts/post.sh`).

| Item | Result |
|---|---|
| Exit status | **0** after 631 s |
| Whole tree after the build | **All 1351 files identical**; the only addition is `m3_design/assembly_review/m3.kicad_prl` (gitignored, written by KiCad). Board `cc044ea0…`, netlist `0cc1ed692fb99dd2…`, all 15 sheets unchanged |
| Step gates in the build | placement OK; power OK; the 9 route families OK (rf `signal_track_mm 436.9`, budget 445; every stage "rigid digests 12/12 equal R7"); ground OK; `r8_post` "rigid digests 12/12 equal R7; copper, zones and pads unchanged" |
| DC neck gate (0.1 mm) in the build | RAW_ACT 5.90 mm / 17.6 °C, BAT_IN 6.85 / 14.8, ACT_FET_S 4.80 / 22.3, all "neck OK" against D12, as the handoff says |
| `tools/check.sh` in the build | DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silk 0 stroke points outside; `R8 CAD contract: OK`; routing 0 failing, 3 allowlisted, 0 stale, 0 leftovers, 0 out-of-date figures, 0 removable exceptions, 0 removable bumps (22 windows); actuators OK; fit OK |
| Step-7 table from the **real** step-6 board | Built in the clone (R7's board, `r8_pcb`, `r8_power`, the nine families; board `b8b73b56…`, every stage 12/12 rigid). `make_ground.py` in normal mode gives `6b6e91d2…`, **`r8_ground.tsv` byte for byte**: 201 rows (fence 25, stitch 2, c24 2, trim 7, return 16, grid 89, cover 54, island 5, pad 1). `--built` on the final board gives the same file (`GROUND_BUILT_IDENTICAL`). The regenerated table is a fixed point of the final generators |
| Fab (`r8_fab.sh` on the rebuilt board) | Exit 0. CHECK none. CPL 85 + 126 rows rebuilt, worst 0.491 mm, no errors. Paste check OK (348 / 359 flashes). Manifest OK (5 outputs). `tools/paste_check.py` standalone OK |
| Fab outputs against the worktree | See the breakdown below the table |

**Fab outputs against the worktree:**
- `m3_bom_jlc.csv`, `m3_cpl_jlc.csv`, `cost_check.json` and `stock_check.json` are byte-identical.
- The 13 Gerber and drill files differ only in their date lines (0 non-date lines each), and the job file only in
  `CreationDate`.
- Both PDFs are equal, length for length, once `/CreationDate`, `/ModDate` and `/ID` are masked.
- The manifest differs only in those three outputs' hashes.

**Against the pass-4 package** (`c84f00b8…`, Gerbers unzipped and compared with date lines masked):
- F_Cu, B_Cu, In1_Cu and In2_Cu changed (299 / 510 / 96 / 238 lines), and so did PTH.drl (6 lines: the three via hits).
- Both masks, both pastes, both silkscreens, Edge_Cuts and NPTH are equal. This bears out "the copper and drill Gerbers
  changed; the silkscreen did not".

**Other outputs regenerate exactly** (on a scratch copy of the worktree board, with the clone's identical code):
- `binding_note.py` gives `r8_binding_note.json` byte for byte.
- `check_r8 --report` equals `fix4_check_r8_report.json` in every key.
- `route_check --profile r8 --report` equals `fix4_route_check_report.json` but the `board_sha256` key the evidence adds.
  It has 94 instances, 0 failures, 3 allowed and 0 stale.
- `reference_audit` (R6 set and `--extended`), `requalify` and `pyro_neighbours` equal their `fix4_*` files but the
  normalised board path and the added SHA. The extended run gives 102408 samples, 5944 unreferenced (5.80 %).
- `m2_sweep.py` equals `fix4_m2_sweep.json` in **every key**: adjacency, adjacency_pad, bumps_all, chain_detour,
  margin_free, pad_edge, poured_hop, routes, short_hop, via_fold, via_step and board_sha256.
- The quick survey (`NO_GATE=1 NO_DC=1 run_survey.sh`) plus the recorded `fix4_dc_*.txt`, run through `scorecard.py`
  against `scorecard_r7.json`, reproduces `fix4_scorecard.md` row for row: index 15.3, C2 91, S1 1497.9, S6 / S7
  1.174 / 285.8, 20 met / 11 missed. Only the header differs.
- On R7's own board and project files (431025d, board `c872a3d3…`): `route_check --profile r7` exit 0 (0 failing,
  45 allowlisted, 29 leftovers recorded, 1 removable local bump, which is R7's allowlisted USB_LIMITED bump), and
  `check_r7.py` gives "R7 CAD contract: OK". **R7's own `route_check.py`** (from `git archive 431025d`) prints the
  identical summary line on the same board, so the R8 tool's r7 profile still reproduces R7's result.

## 2. What fix pass 4 changed, measured independently

### 2.1 Its recorded starting state and diff

**Rebuilding the pass-4 state:**
- I rebuilt the pass-4 state from 431025d plus the coordinator's backup `r8_backup_c84f00b8/` (`git apply --binary
  tracked.diff`, untar `untracked.tgz`). The board hashes to `c84f00b8…` and the status is the same 89 paths.
- All **276** hashes in `fix4_baseline_sha256.txt` verify against it (`shasum -c`, 0 failures).
- The expanded changed / untracked file list of that state is exactly the baseline's 276 paths. So the header's "every
  tracked file not listed equalled commit 431025d" holds.

**What changed against that state** (`diff -rq`, excluding `.git`, `__pycache__` and `m3.kicad_prl`;
`p5int/c84_vs_wt.txt`):
- **23 files changed and 19 were added**:
  - generators / tables (5): `r8_route_rf.py`, `r8_power.py`, `r8_build.sh`, `r8_ground.tsv`, `step7/make_ground.py`;
  - outputs (8): `m3.kicad_pcb`, `fab/` (Gerber zip, two PDFs, manifest), `r8_top.png`, `r8_bottom.png`,
    `r8_binding_note.json`;
  - records (10): AGENTS, README, STATUS, M3_R8, MARGIN_PRESCRIPTION, ORDERING, R8_VALIDATION, REQUIREMENTS,
    R8_DECISIONS, `fix3_handoff.md`;
  - added: the 15 `step9/evidence/fix4_*` files and the four `fix4_*` files in this folder.
- The changed set is exactly the handoff's "Files changed by fix pass 4". Nothing was removed, and no `pass4_*.md` was
  touched.
- The netlist and all 15 sheets are unchanged.
- I recomputed the diff of the five code and table files. Its 51 +/− lines are **identical** to `fix4_generators.diff`.

**Every gate file is byte-identical to the pass-4 state.** None of these appears in the diff:
- `tools/` (every file, `check.sh`, `check_r8.py`, `route_check.py`, `check_r7.py`, `fit_check.py`, `dc_solve.py`,
  `run_dc.sh`, `paste_check.py`, `reference_audit.py`, `scorecard*` and every `test_*.py` included);
- every `m3_design/r8_*_check.py`, `r8_legalise.py`, `r8_keepclear.tsv` (header only), `check_actuators.py` (SHA-256
  `5de1eb3c…` = `check_r8.CHECK_ACTUATORS_SHA`);
- `m3.kicad_dru` (`1674d58b…`, `check_actuators.DRU_SHA`), `m3.kicad_pro` and `quality_audit/`.

**The generator edits carry no gate content:**
- `r8_route_rf.py`: only the TRIO table, TRIO_STEP and comments. Its family budget (445 mm) is unchanged.
- `r8_power.py`: only the USB_LIMITED track list and a comment.
- `make_ground.py`: only FENCE_X, STRIP_STITCH and a comment.
- `r8_ground.tsv`: three rows and one reordered row.
- `r8_build.sh`: one comment line.

**Timing:** all five were saved before the stage-A regeneration and build 1 (generators 15:34–15:35, table 15:42:38).
Both builds therefore ran on the final state, and my build matches them.

**Where the fence geometry is judged:**
- The fence is judged independently of `make_ground.py` by `check_r8.fence`. It requires consecutive fence vias at most
  `FENCE_PITCH` 2.0 mm apart, except openings of at most 2.7 mm (D16) that a lane crosses.
- The new openings are 2.015 / 2.60 / 2.10 / 2.10 mm, each with its lanes. The 18.2–19.95 gap is 1.75 mm, so it is not
  an opening.
- No code keys on a board SHA: `grep` for `cc044ea0`, `c84f00b8` or `990c8040` over `*.py`, `*.sh`, `*.tsv` and
  `*.json` finds only the fab manifest, the binding note and evidence and review files.

### 2.2 Against R7

**Unchanged since 431025d:** `git diff --stat 431025d` over `tools/`, `check_actuators.py`, the DRU, the project file
and `quality_audit/` lists the same eight tracked files as passes 1–4:
- `check.sh`, `dc_solve.py`, `jlc_corrections.json` and `route_check.py`;
- `test_check_shell.py`, `test_fab_validation.py`, `test_r5_repair.py` and `test_route_check.py`.

`check_actuators.py`, the DRU, `m3.kicad_pro`, `quality_audit/`, `fit_check.py`, `silk_check.py`, `check_r7.py` and
`test_r7_check.py` have an empty diff.

**Spot check of route_check:** the acute-angle rule's pad / via exemption, through which C21's wedge passed (D111), is in
R7's own `route_check.py` with the same wording (R7 l. 17, R8 l. 21). It is not an R8 relaxation.

### 2.3 Board diff against `c84f00b8…`

**Method:** `p5int/scripts/sdiff.py` compares every top-level item of the two `.kicad_pcb` files as multisets, after
dropping `uuid` and with zone fills set aside. `filldiff.py` takes each zone's filled-polygon difference with pcbnew.

| Item class | `c84f00b8…` → `cc044ea0…` |
|---|---|
| footprints (249), gr_text (35), gr_line, gr_circle, zones (33 definitions), setup, title block, layers, general | **identical** |
| segments 795 → 794 | −13 / +12: RADIO_RXEN, RADIO_BUSY, RADIO_MISO_MCU 3 each (x 20.6 / 21.1 / 21.6 → 20.5 / 21.0 / 21.5, steps at y 22.500 / 22.707 / 22.914); USB_LIMITED −4 +3 (trunk split at (32.2, 55.3), branch (32.2, 55.3) → (32.2, 57.775)) |
| vias 609 → 609 | GND (20, 23.3) → (19.95, 23.3); (22.1, 23.3) → (22.05, 23.3); (22.1, 26.7) → (22.05, 26.7) |
| fill GND_F (F.Cu) | 3353.816 → 3354.052 mm² (−0.460 at x 20.11–20.75, y 21.85–26.88; +0.696 at x 21.75–22.13, y 22.64–30.01: the trio's move) |
| fill GND_B (B.Cu) | 3430.171 → 3431.047 mm² (−0.369 at x 31.84–32.56, y 55.65–56.65; +1.245 at x 32.48–34.67, y 55.79–56.86: D111's freed copper) |
| fill R8_3V3_In2 (In2.Cu) | 1513.828 → 1513.828 mm²: 0.050 mm² removed at x 21.55–22.03 and added at x 22.12–22.60, y 26.20–27.20: the 3V3 pour's clearance ring round the stitch via (22.05, 26.7), 0.05 mm west with the via (02) |
| every other fill | identical |

This is exactly the two items' copper, the three moved GND vias and the fills that follow from them. The edge gaps
(pcbnew, edge to edge, F.Cu):

| Via | Nearest lanes (mm) |
|---|---|
| (19.95, 23.3) | RXEN 0.200 |
| (22.05, 23.3) | MISO_MCU 0.200, MOSI 0.200 |
| (22.05, 26.7) | MISO_MCU 0.200, MOSI 0.200 |

These are the handoff's figures (the via positions do not exist on `c84f00b8…`).

## 3. Rigid digests

- `check_r8.py --print-hashes` on R7's board (`c872a3d3…`, from 431025d) and on the final board print **identical** values
  for all 12 groups. They equal `RIGID_BASELINE` (`check_r8.py:136-148`) and pass 4's `r7_hashes.txt`.
- Every build stage, the step-6 rebuild and `r8_post` printed "rigid digests 12/12 equal R7".

**What the digests cover round fix pass 4's copper** (`check_r8.rigid_groups`, l. 1042–1068):
- `strip_gnd` holds the GND vias with y < `STRIP_Y` (23.5) **off the fence row** (|y − 23.3| ≥ 0.06) and the GND tracks
  starting in the strip.
  - The three moved vias are outside it: two are fence-row vias, and the stitch via sits at y 26.7.
  - That is D16's and D11's design: the fence row and the interface leads are regenerated, not rigid.
- The trio's in-strip step segments (y 22.0–22.9) are radio interface leads, in no group (D11).
- The GCPW profile digest samples the F.Cu GND within 1.5 mm of the RF lines. It is unchanged, so the trio's fill change
  does not reach them.
- The seeds in §4 confirm each of these boundaries.

## 4. Tests and seeded defects

**Suites** (rebuilt clone, after `r8_fab.sh`, KiCad Python, no bytecode written):
- **17 suites, 272 tests, all OK**, including `test_fab_validation` (23) on the regenerated package;
- quality_audit **21 OK** under both KiCad's Python and the system `python3`.

**Seeds this pass** (`p5int/scripts/seeds.py` on a copy of `cc044ea0…`, in memory; output `p5int/seeds.json`):

| Seed | Expected | Result |
|---|---|---|
| As built | fence, table, rigid clean | fence 0 issues (25 vias, openings 2.015 / 2.60 / 2.10 / 2.10 with their lanes); table 0; rigid 0 |
| Fence via (22.05, 23.3) deleted | fence fails (4.20 mm opening > 2.7); table misses the row; rigid unaffected | "strip fence: opening x 19.95-24.15 is 4.20 mm wide (maximum 2.7 mm, D16 …)"; "table via (22.05, 23.3) (fence) missing …"; rigid [] |
| Stitch via back at (22.1, 26.7) | table fails; fence and rigid unaffected | "table via (22.05, 26.7) (stitch) missing or not a 0.5/0.3 GND via"; fence []; rigid [] |
| The trio's three fence crossings removed | fence fails "no lane" (the 2.10 mm gap > 2.0 needs a lane) | "strip fence: GND vias 2.10 mm apart between x 19.95 and 22.05 with no lane through the gap (maximum 2.0 mm)" |
| Strip GND via (1.0, 1.0) moved 0.05 mm | strip_gnd digest fails | "rigid group strip_gnd differs from R7 (176 items, sha256 bbd6aca4…, R7 bfcbe417…)" |
| Fence via (19.95, 23.3) moved 0.05 mm | no digest change (fence row not rigid, D16) | rigid [] |
| RXEN's six in-strip segments shifted 0.01 mm | no digest change (interface leads regenerated, D11) | rigid []; restored, rigid [] |

**Seeds carried**, still valid because the code is byte-identical since pass 4 (and pass 3):
- pass 4's L10 and camera-budget seeds;
- pass 4's `margin_free` seed on the pass-3 board;
- pass 3's `battery_pyro` drain mutants;
- the DC gate's hand-seeded fail path (passes 1 and 2).

## 5. Records against what ran

| Claim (fix4_handoff / R8_VALIDATION / M3_R8 / STATUS) | Check |
|---|---|
| Two consecutive builds, 609 / 769 s, identical board, netlist and 15 sheets | `fix4/build1/sha256.txt` = `build2/sha256.txt` (17 files, board `cc044ea0…`); the logs end "build1 exit 0 in 609 s", "build2 exit 0 in 769 s". My independent build gives the same tree |
| `check.sh` exit 0 in both builds and standalone twice | Both build logs, `fix4/check_sh.log` (16:07:21) and `check_final.log` (16:34:38) end in the OK summary; mine as well |
| Every step gate OK; rf 436.6 → 436.9 of 445 mm | My build log |
| Build DC gate figures | My build log, identical |
| `make_ground --built` reproduces `r8_ground.tsv` | Holds, and so does the stronger fixed point from the real step-6 board (§1) |
| 272 tests after `r8_fab.sh` | `fix4/fab.log` written 16:07:45; the first suite log 16:07:46 and the last 16:08:38; `fix4_tests.txt` lists all 17 OK. My re-run: 272 OK |
| Fab: CHECK none, BOM `be711876…` and CPL `ef90bfa1…` unchanged, manifest bound, silkscreen unchanged | §1: BOM and CPL byte-equal to the pass-4 package; silkscreen, mask and paste Gerbers equal; copper and drill changed |
| `check_r8` report equal to fix pass 3's but the fence openings and the track-end count | `fix3_` vs `fix4_check_r8_report.json`: only the SHA (×2), openings[2] / [3] x0 / x1 / width and `track_endpoints_checked` 1590 → 1588 differ |
| route_check 94 instances (+1 width_change_junction at the T) | fix3 → fix4 report: exactly that one instance added, none removed. Also two informational `detour_baseline` lengths, RADIO_BUSY 32.01 → 32.09 and RADIO_RXEN 40.02 → 40.11 mm, the trio's +0.3 mm (S1) |
| requalify, pyro_neighbours and refaudit (R6 set) equal but the SHA; extended +24 samples on RADIO_MISO_MCU | The fix3 → fix4 JSON diffs show exactly that |
| DC 0.05 mm and the GND return identical to fix pass 3's; supply rows equal but USB_LIMITED 52.62 → 52.66 | `fix3_dc_*` vs `fix4_dc_*`: only the header line differs. The scratch solves (`fix4/dc/*.txt`) are genuine runs on `fix4/build1` (`cc044ea0…` in the solver's own header). The GND solve is windowed (`--window`), which explains its unchanged cell count. The supply summary differs only in the header and the usb row |
| Evidence binding | All 15 `fix4_*` evidence files name `cc044ea0…` |
| Board not itself reviewed | Stated in R8_VALIDATION:9, :161 and "Open after fix pass 4", STATUS:14 / :98, AGENTS §1 and M3_R8. No record claims a review of `cc044ea0…` |
| Records pass "changed records, `step9/requalify.py` and one evidence file only" (R8_VALIDATION:43–45) | Holds (§0) |
| Not re-run: plate model, hot-plug script, live cost / stock | Stated honestly; `cost_check.json` still binds the step-9 CPL (ORDERING:29, R8_VALIDATION "Open after fix pass 4") |

## 6. Findings

### R8P5-INTEGRITY-01 (Minor, worth fixing; owner action; carried from R8P1–R8P4-INTEGRITY): R8 is still uncommitted at pass 5

**State:**
- `git log` ends at 431025d.
- `git status` shows 89 paths: 38 modified and 51 untracked. They include every `r8_*.py`, `check_r8.py`, the tables,
  the records and all four review passes plus pass 5's reports.
- R8_VALIDATION "Open after fix pass 4" and STATUS:26 still ask for a commit or tag. None was made.

**What survives of the reviewed state:**
- The pass-4 state (`c84f00b8…`) survives only as the coordinator's scratchpad backup `r8_backup_c84f00b8/`. I verified
  that it rebuilds `c84f00b8…` and all 276 baseline hashes (§2.1).
- Beside it there are `fix4_baseline_sha256.txt` and the exact five-file `fix4_generators.diff`.
- `cc044ea0…`, the state this pass reviews, exists only in the worktree.

**Consequence:** this pass's file:line citations are tied to an uncommitted tree, and the next edit rewrites it.

**Fix (owner):**
- Commit or tag `m3-assy-r8` at this state (`git add -A`; nothing R8 needs is gitignored).
- Record the commit beside `cc044ea0…` in R8_VALIDATION and STATUS.
- Have any further fix pass diff against it.

### R8P5-INTEGRITY-02 (Minor, not worth fixing on its own): fix pass 4's notes give the zone changes as F / B GND only; the In2 3V3 pour also changed, round the moved stitch via

**What is recorded:**
- `fix4_progress.md:32` lists the build-1 diff's zone changes as "zones F GND +0.24, B GND +0.88 mm2" (measured:
  +0.236 / +0.876 mm²).
- The handoff and records describe the board diff as the reviewer's `rec4` copper. No record mentions In2.

**What the board shows:**
- The `R8_3V3_In2` fill also differs. Its clearance ring round the GND stitch via moved 0.05 mm west with the via,
  (22.10, 26.70) → (22.05, 26.70).
- 0.050 mm² was removed at x 21.55–22.03 and the same area added at x 22.12–22.60, y 26.20–27.20. The pour's area is
  unchanged (1513.828 mm²).
- The In1_Cu and In2_Cu Gerbers changed accordingly (96 / 238 lines; In1 by the three via flashes).

**Impact:** none on function. It is the necessary consequence of moving a through via in a 3V3 pour: DRC 0, and the
scorecard's P rows (P6 In2 perimeter 1752.2) are equal. It is not a forbidden change under this pass's brief either,
being the antipad of a regenerated GND via. Only the description of "what changed" is incomplete.

**Fix:** none needed. If the fix-4 notes are edited again, add "and the In2 3V3 antipad round (22.05, 26.7), area
unchanged".

## 7. Notes (no finding)

- **Table regeneration is still a manual step** (pass 4's note). Fix pass 4 did it correctly: build to step 6,
  `make_ground.py`, rebuild. My independent step-6 rebuild regenerates `r8_ground.tsv` byte for byte. A stale table would
  still have to pass every gate (`check_r8.fence`, DRC, reach, islands), as the seeds show.
- **Stale wording.** R8_VALIDATION:37 says "neither fix-pass brief allowed one" (a commit). There have now been four fix
  passes, and none allowed one.
- **Renders.** `r8_top.png` and `r8_bottom.png` are regenerated but not byte-reproducible (passes 3 and 4). They are not
  fab outputs, and no record calls them reproducible.
- **Worktree activity during this pass.** Other pass-5 reviewers wrote `pass5_planes.md` and `pass5_routing.md`. The
  `assembly_review/` directory's mtime moved at 16:44 (a transient file from another reviewer's KiCad session,
  Inference). The board still hashes to `cc044ea0…`, and the status paths are unchanged.
- **Scratch kept:** `…/scratchpad/p5int/` holds the logs, `seeds.json`, `sdiff.txt`, the evidence regenerations
  (`ev/`), `scorecard_p5.md` and the scripts `run_build.sh`, `post.sh`, `run_tests.sh`, `step6.sh`, `ev.sh`, `seeds.py`,
  `sdiff.py`, `filldiff.py` and `gaps.py`.
