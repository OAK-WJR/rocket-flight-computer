# R9 review pass 2: gate and build integrity

Reviewer dimension: gate and build integrity. The questions were:
- Does `m3_design/r9_build.sh` reproduce the board byte for byte?
- Is every gate and per-step check real? Nothing may be weakened or special-cased to make R9 pass, judged against the
  R8 versions at `9c8179b`, and the replacements for R8's rigid hashes must be at least as strict as claimed.
- Do the seeded tests fire?
- Does the no-GUI shim leave results unchanged?
- Do the records claim only verification that happened?

Board under review: `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14` (review pass 1's fix pass). It was hashed at the
start and at the end of this review and is unchanged.
- The worktree's whole-tree manifest at the end equals the one at the start, apart from the other pass-2 reviewers'
  reports.
- This review modified no repository file except this report.
- Every run used scratch clones under `<scratchpad>/r9review/integrity2/`, deleted afterwards.

## Verdict

**0 Critical, 0 Major, 3 Minor (1 worth fixing).**

- **The build reproduces.** `r9_build.sh`, run whole in a clean clone with no shim, exits 0 in 43 min 17 s, and every
  file it writes is byte-identical to the worktree. This is the third independent build of `4f841a0e…`.
- **The gate holds.** `tools/check.sh` exits 0, and its output and every report equal the bound
  `step10_evidence/gate/` files.
- **check_r9 is deterministic now.** Three hash seeds give byte-identical reports, equal to the bound evidence.
- **Pass 1's findings in this dimension:** INTEGRITY-01, -02 and -05 are closed; -03, -04 and -06 stay open as
  recorded.
- **Tests:** 478 tests in 26 suites pass, none skipped. The gate's seeded rule-H suite catches all 24 variants.
- **The aid's frozen table checks out.** `r9_ground_aid.py --check` reproduces the frozen ground table from the step-7
  board.
- **The new gate rules are real.** P-7b, R-8 over U31's body and the copper gate are real, stricter and seeded. The
  other tool changes are deterministic or labels only. No gate file shared with R8 changed in the fix pass.

The three Minors:
- **01, worth fixing.** The step-8 stitch gate's outer-pour clause cannot fail on a filled board.
  - It replaced R8's outline test with a fill test, so it is weaker than R8's `r8_ground_check.power`.
  - Its seeded test passes only for a via position where no via is drawn.
  - D-F1-07's "the stitch gate allows the cut inside that box only" leans on this clause.
- **02.** The fix pass added an exemption to that stitch gate: C121.2's corridor box, recorded in D-F1-07 and part D.
  Four record summaries still say no check was weakened.
- **03.** Five fix-pass record statements do not match what happened. One is an owner-acceptance figure (C21) whose
  evidence was deleted.

On this board none of them hides a defect: measured, no table via lies in an outer power pour, and the one corridor
cut is the recorded one.

## 1. What was run (independent of the fix pass's records)

Each clone is a `git clone --shared` of the main repository at `9c8179b` with the R9 worktree's files rsynced over it.
Before any run, each clone's `git status` (113 entries) and whole-tree SHA-256 manifest (1660 files) equalled the
worktree's. A GUI session was logged in (`who`: console since 2026-10-24 19:10), so kicad-cli ran directly. No shim
or wrapper was used anywhere.

| Check | Result |
|---|---|
| `NUMPY_PY=<cfd venv> bash m3_design/r9_build.sh`, run whole (clone `build1`) | **rc 0 in 2597 s.** Every stage gate printed OK: `r9_sch_check`, placement, RF strip, pyro block, power, the ten route families, ground (12 gates; P9 3.37 mm, P10 7.32 mm, P7 9, unreferenced 3206 = `REF_UNREF_MAX`), post, the final `tools/check.sh`. **The clone's whole-tree manifest after the build equals the one before it, which equals the worktree's.** So the 15 sheets, `schematic.net.xml`, `m3.kicad_dru` and the board `4f841a0e…` came out byte-identical. `r9_lib.py` writes a variant footprint only when its generated text differs, and it wrote none, so both variants equal their generated text. The only new files are git-ignored `__pycache__/` folders from the steps that run without `-B`; `git status` is unchanged |
| Generator-only replay (clone `gen3`: `r9_pcb`, `r9_rf`, `r9_pyro`, `r9_power`, the ten `r9_route` families, `r9_ground`, `r9_post`; no gates) | The step-7 board is `7274f29cf553…`, the SHA that the aid's log names for stage 34. The final board is `4f841a0e…` byte for byte, so the step gates write nothing the board depends on |
| `r9_ground_aid.py STEP7.kicad_pcb out.tsv --check` on that step-7 board, beside the project's `.kicad_pro` / `.kicad_dru` | **"frozen table reproduced", rc 0.** `out.tsv` equals `m3_design/r9_ground.tsv` byte for byte (187 rows). Its island, reach and copper-stage log lines equal `sources/r9_review/fix1/aid_copper.txt` line for line |
| `tools/check.sh` on the unmodified board (clone `gate2`) | **rc 0 in 6 min 44 s.** Stdout equals `step10_evidence/gate/check_sh.txt` line for line, apart from that file's header and its closing "exit 0". Compared field by field with the bound reports: `fit`, `plate`, `seed` and `r9` differ only by the added `bound_by` field; `route` by that and `board_sha256`; `drc` and `erc` by those and the run date |
| `tools/check_r9.py` run three times without `-I`, at `PYTHONHASHSEED` 1, 2 and 3, on the bound fit / plate / seed reports | **Three byte-identical reports** (`fd5a11ea…`). They are byte-identical to my `check.sh` run's `r9.json`, and equal to the bound `gate/r9.json` but for its `bound_by` field |
| The 26 suites in `tools/`, every `tools/test_*.py`: KiCad python3 `-B -m unittest -v`, the real kicad-cli, `KICAD_PY` and `NUMPY_PY` set | **478 tests, all OK, none skipped** (no "skipped" in any log). `test_r9_check` 53, `test_r9_ground` 21. The clone's manifest was unchanged afterwards |
| `quality_audit` tests | 21 OK under python3 and under KiCad python3 with `KICAD_PY` / `KICAD_CLI` unset. With `KICAD_PY` exported: 3 failures and 1 error (INTEGRITY-06, unchanged) |
| `step10/check_records.py` | OK. The report equals `step10_evidence/check_records.txt`: 69 evidence files, 151 hashed inputs, 87 figures |
| Fab manifest | All 180 SHA-256 entries (inputs and outputs) of `fab/m3_fab_manifest.json` match the files on disk; the board entry is `4f841a0e…` |
| Scorecard Z4 (`tools/r9_extra_metrics.py`) | fc3d5b34: 2, TP120's RAW_ACT vias at (29.6, 78.2) and (31.0, 78.2). 4f841a0e: 0. R8 `cc044ea0…`: 1 (TP122), so the R8 column stays like for like. X5 6 → 5 |
| R8 / R7 / R6 worktrees | R8 and R7 are clean at `9c8179b` / `431025d`; R8's board is `cc044ea0…`. No R6 file changed after 2026-10-20 |

## 2. Pass 1's findings in this dimension

| Finding | Disposition in the records | On `4f841a0e…` |
|---|---|---|
| R9P1-INTEGRITY-01 check_r9's report not reproducible | Fixed (D-F1-03) | **Closed.** R-5 credits each sample to the nearest pad over sorted designators. pyro_probe sorts net names and keeps the smallest (mm, labels) pair. Three hash seeds give byte-identical reports, and my gate run reproduces the bound `r9.json`, `seed.json` and `route.json`. The attribution change moves evidence only: the set of samples excused as windows (any chain pad within 0.3 mm) is unchanged, so no verdict can move. D-S10-18 is corrected |
| R9P1-INTEGRITY-02 R-8 sampled In1 only inside U31's pad ring | Fixed (D-F1-03) | **Closed.** In1 is sampled over U31's body box [25.61, 9.0, 35.61, 19.0]: 2601 of 2601 samples are GND (the new `gnd_sampled` evidence). The test first asserts that R8 passes R-8, then cuts a 0.5 mm notch in the pad-ring band, which fails |
| R9P1-INTEGRITY-03 the test-pad rule's "never lowers a pyro rule" comment | Open, recorded | Still true, and still harmless. No zone is on PYRO1_BUS / IGN / OUT (the outer non-GND zones are BAT_IN, RAW_ACT, ACT_FET_S and RAW_PROTECTED), and TP120 is the only RAW_ACT test pad. The stated reason for leaving it is weak: "the DRU text is pinned by check_actuators' DRU_SHA", but R9 already re-pinned DRU_SHA once (D-S1-02), so a comment edit costs one reviewed re-pin |
| R9P1-INTEGRITY-04 rule_h_seed cannot fail on a check_actuators regression | Open, recorded | The code is unchanged. In my run `check_actuators` caught all six text edits on all three pairs, DRC every plain seed and LC-1 every pad override; the controls showed 0 hits |
| R9P1-INTEGRITY-05 stale docstring and via count | Fixed | **Closed.** The M-7 docstring names the rotation per revision. M3_R9's 183 GND vias and 4 straps are the regenerated table's, and the build prints the same |
| R9P1-INTEGRITY-06 quality_audit's tests depend on KICAD_PY | Open (pre-existing) | Unchanged; reconfirmed |

## 3. The fix pass's gate and tool changes

I diffed the worktree against the backup the fix pass took before it started
(`<scratchpad>/r9review/orig/worktree_before_fix1.tgz`, fc3d5b34's state; 325 files).
- **Unchanged since pass 1:** the gate files shared with R8 (`tools/check.sh`, `m3_design/check_actuators.py`,
  `fit_check.py`, `route_check.py`, `jlc_orient.py`, the `test_r8_*` suites) and every step-gate script except
  `r9_ground_check.py`. Pass 1 compared these with `9c8179b`.
- **Changed:** the tools in the table below and the generators.
- **Hashes:** the DRU `ea77b791…` and the netlist `8b0e04ea…` are unchanged.

| File | Change | Judgement |
|---|---|---|
| `tools/check_r9.py` P-7b | U1's gate-pin pad ≥ 0.5 mm from every copper item that is not a U1 pad, GND, its own net or unconnected | New and stricter. Seeded: fails at 0.25 mm, passes at 0.55 mm; GND and U1's own pins are exempt. Board: QSPI_IO2 0.55, 3V3 1.25, IMU_INT1 1.369 mm |
| `tools/check_r9.py` R-5 / R-7 / R-8 / docstring | Nearest-pad attribution and sorted iteration; compass labels; In1 sampled over U31's body | Deterministic; labels only; stricter |
| `tools/pyro_probe.py` | Sorted net names; ties broken on (mm, labels) | Deterministic; no threshold change |
| `tools/r9_extra_metrics.py`, `r9_scorecard.py` | Z4 over every TP* pad, preferred to the R8 survey's A8 (x_metrics is merged first, so it wins) | Stricter (a scorecard row, not a gate) |
| `m3_design/r9_ground_check.py` copper gate | GND SMD pads of C / U / Q / J parts ≤ 5 mm, and outer GND copper ≤ 8 mm, of copper from a via; 1 pad and 6 cluster exceptions | New. Each exception is held at its measured reach + 0.1 mm and fails when stale. The board's clusters (9.50 / 9.37 / 8.95 / 8.61 / 8.48 / 8.05 mm) and J9.2 (6.99 mm) equal the recorded values, and each exception has its "no legal spot" line in the aid's log. Seeded: a stale exception fails, and so does a lost pad via |
| `m3_design/r9_ground_check.py` stitch gate | A table via inside `r9_ground_aid.CORRIDOR_EXCEPT`'s box (34.55–35.75 × 61.3–64.85) may cut the In2 RAW_ACT region inside its 7.7 A corridor | **A relaxation of an existing step-8 gate** (finding 02). Exactly one via uses it, (35.6, 64.8) (measured `corridor_exceptions`). Recorded in D-F1-07 and part D |
| `m3_design/r9_ground_aid.py` | `legal(relax=BOX)` lifts the outer RAW_ACT pours' 0.3 mm and the RAW_ACT In2 corridor inside the box; the copper stage; `place_safe` | A design aid, not a gate. Its frozen output reproduces (§1) |
| `step10/check_records.py` | Reads the 0.05 mm solves from `step10_evidence/dc/`; the TP120 claim is now built from the data | Adapted to the new evidence; not weakened |
| Generators and tables (`r9_rf.py`, `r9_route.py`, `r9_route_imu_baro.py`, `r9_route_power_ctl.py`, `r9_power.py`, `r9_place.tsv`, `r9_ground.tsv`) | Design changes | No assertion or draw-primitive check removed |

**The step-8 gates against R8's step-7 ground gate.** R8's `r8_ground_check.power` (`m3_design/r8_ground_check.py:298-341`
at `9c8179b`) refused a stitching via inside any non-GND F.Cu / B.Cu zone's outline (`:328`,
`z.Outline().Contains`), and one inside an In2 power island within its 7.7 A corridor.
- **In2:** R9's stitch gate keeps this half in a working form. It tests the via's circle (r + 0.3 = 0.55 mm) against
  the region's fill. That circle reaches past the 0.40 mm antipad round the hole, because the vias keep no In2 pad
  (D-S8-19). It also catches an antipad reaching into the corridor from just outside it.
- **Outer layers:** R9 replaced the outline test with a test of the via's centre against the fill. That test can never
  fire on a refilled board (finding 01).

**Rigid-hash replacements.** Pass 1 traced every R8 rigid group to its R9 rule. The fix pass changed none of those
rules except R-8, which it made stricter.
- **The gap that remains.** No R9 rule holds the RF modules' ground-pin vias, which R8's hashed RF copper held. So
  check_r9's header claim ("each at least as strict") still overstates there. Pass 2's RF reviewer reports this as
  R9P2-RF-01; I concur.
- **My measurement**, by `check_r7.rf_grounds`' own method (pad edge to the nearest GND via ring):

  | Pins | fc3d5b34 | 4f841a0e | R8 |
  |---|---|---|---|
  | U31.2 / U31.7 / U31.16 | 1.04 / 0.98 / 1.01 mm | 0.17 / 0.31 / 0.31 mm | 0.17 / 0.31 / 0.31 mm |
  | U30.1 / U30.10 / U30.12 | 0.14 / 0.16 / 0.51 mm | 0.14 / 0.16 / 0.51 mm | 0.81 / 0.55 / 0.71 mm |

  A row at R-7's existing 0.6 mm for U31's pins, and at R8's figures for U30's, separates the cases with margin. The
  fix pass's reason for not adding the row ("a gate at exactly 0.35 mm on a 0.05 mm raster would sit at its limit")
  applies only to that raster metric.

## 4. Seeded tests

- **The gate's seeded rule-H suite** (my run, equal to the bound `seed.json`). The pairs are Q124.5–R129.2 (1.225 mm),
  R132.1–C129.1 (1.758 mm) and R177.1–R124.2 (2.054 mm), with 0 DRC hits before seeding. Every variant is caught as the
  suite's docstring requires:
  - DRC catches `seed`;
  - LC-1 catches `pad_override`;
  - `check_actuators` catches the six text edits.

  The suite's own pass criterion is still the loose one (INTEGRITY-04).
- **The fix pass's new tests** fire on their seeds: `test_p7b_mcu_gate_pin`, the R-8 body notch, 'GNSS west',
  `test_copper_gate_holds_and_stale_exception_caught`, `test_copper_gate_catches_a_lost_pad_via` and
  `test_corridor_exception_only_inside_its_box`.
- **One older seeded test proves less than its name says:** `test_via_in_a_power_pour_caught` (finding 01).

## 5. The no-GUI shim

- The fix pass ran with a GUI session logged in (R9_VALIDATION "Environment"; `who`), and so did this review. Neither
  used a shim or a wrapper.
- No repository script references the shim: "DYLD_INSERT", "wxGetMousePosition" and "shim" appear nowhere in `tools/`,
  `m3_design/` or `quality_audit/`.
- Pass 1 showed that the shim-built fc3d5b34 equalled a build without it. Nothing in this pass depends on it.

## 6. Records against what happened

Confirmed:
- the board, netlist and DRU hashes;
- the two byte-identical builds, with my own as a third;
- `check.sh` exit 0 and its figures: DRC, unconnected, parity and ERC 0; check_r9 40 / 40; route_check 0 failing, 0
  allowlisted, 0 leftovers; check_actuators OK;
- "two separate gate runs on 4f841a0e give identical check_r9 reports";
- 478 tests in 26 suites, none skipped;
- quality_audit 21 under both Pythons with `KICAD_PY` unset;
- `check_records` OK;
- the fab manifest's binding;
- Z4 = 2 on fc3d5b34 and 0 now;
- the aid's `--check` and its copper-stage log;
- the six clusters and J9.2 at their recorded reaches;
- the corridor exception's one via;
- the step-7 board SHA in `aid_copper.txt`.

Not as stated: findings 02 and 03.

## Findings

### R9P2-INTEGRITY-01: Minor, worth fixing. The step-8 stitch gate's outer-pour clause cannot fail on a filled board (weaker than R8's)

- **What it claims.** `r9_ground_check.py:20` says "every table via: inside no non-GND F.Cu / B.Cu fill", and
  `r9_ground.py:279` says "a stitching via must not cut a power pour". Together they are the outer half of D-S8-02's
  rule that the "outer power pours and the 7.7 A In2 corridors" stay uncut.
- **What it does.** `foreign_fill` (`r9_ground.py:278-288`) asks whether the via's centre lies inside a non-GND F.Cu
  / B.Cu fill (`f.Contains(P(*q))`). Both callers run it after the native refill:
  - `build()` (`r9_ground.py:299-307`);
  - `gate_stitch` (`r9_ground_check.py:341-342`), on the saved board.

  A refill always clears a GND via out of a foreign fill, so the centre is never inside one.
- **R8's version worked.** R8's step-7 gate (`r8_ground_check.py:328` at `9c8179b`) tested the zone's outline,
  `z.Outline().Contains(P(*q))`, which needs no fill.
- **Measured.** I added, in memory with nothing saved, a 0.5 / 0.3 mm GND via at (20.6, 97.25). It lies 1.0 mm inside
  the BAT_IN B.Cu fill and outside every 7.7 A corridor box.
  - Before the refill, `foreign_fill` names it.
  - After the native refill, `foreign_fill` returns [] and `gate_stitch(b, [(20.6, 97.25)])` returns no issue.
  - The BAT_IN zone's outline contains the point; its fill no longer does.
- **Reproduce** (KiCad python3 `-B -I`, on a copy of the board beside the project's `.kicad_pro` / `.kicad_dru`, with
  `m3_design` and `tools` on `sys.path`):

  ```python
  import pcbnew, r9_ground as G, r9_ground_check as GC
  b = pcbnew.LoadBoard('copy/m3.kicad_pcb'); q = (20.6, 97.25)
  print(G.foreign_fill(b, [q]))                     # [((20.6, 97.25), 'BAT_IN', 'B.Cu')]
  v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(q[0]), pcbnew.FromMM(q[1])))
  v.SetWidth(pcbnew.FromMM(0.5)); v.SetDrill(pcbnew.FromMM(0.3)); v.SetNet(b.FindNet('GND')); b.Add(v)
  b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
  print(G.foreign_fill(b, [q]), GC.gate_stitch(b, [q])[0])     # [] []
  ```
- **The seeded test proves less than its name says.** `test_via_in_a_power_pour_caught`
  (`tools/test_r9_ground.py:102-105`) passes (32.6, 70.5) to `gate_stitch`. No via is drawn there, so the fill there
  is still whole.
- **Why it matters.**
  - The ground table is frozen and the build does not run the aid. This clause is therefore the build's only guard
    against a table via that lands in an outer power pour after a pour edit, and the fix pass made exactly such an edit
    (`RAW_ACT_F`'s west edge).
  - D-F1-07's "the stitch gate allows the cut inside that box only" holds for In2 alone: an outer RAW_ACT cut outside
    the box would pass as well.
  - The In2 half does fire. It tests the via circle at r + 0.3 = 0.55 mm, wider than the 0.40 mm antipad round the
    0.3 mm hole.
- **This board.** None of the 183 table vias lies inside any non-GND F.Cu / B.Cu zone outline.
  - Only In2 outlines hold table vias: 52 in 3V3, and 6 in RAW_ACT.
  - Of the six in RAW_ACT, five lie south of the corridor box (y < 60.0) and the sixth is the excepted (35.6, 64.8).
  - Nothing is hidden today.
- **Fix:**
  - restore R8's test: refuse a table via whose circle meets any non-GND F.Cu / B.Cu zone's outline
    (`z.Outline().Collide(P(*q), r)`), with C121.2's box as an explicit RAW_ACT exception if D-F1-07 means it to cover
    the outer pours;
  - make the test draw a real via, refill, and expect the failure (the seed above);
  - the board passes unchanged.

### R9P2-INTEGRITY-02: Minor. The fix pass added an exemption to the step-8 stitch gate, but four summaries say no check was weakened

- **The exemption.** `r9_ground_check.py:354-358` now skips "via … cuts the In2 RAW_ACT region inside its 7.7 A
  corridor" for any table via whose centre lies in the box of `r9_ground_aid.CORRIDOR_EXCEPT['C121.2']`
  (x 34.55–35.75, y 61.3–64.85; `r9_ground_aid.py:155`).
  - One via uses it: (35.6, 64.8). Measured, `corridor_exceptions` = [((35.6, 64.8), 'RAW_ACT', 'C121.2')].
  - That via's antipad cuts the In2 RAW_ACT region inside the RAW_ACT corridor box [17.19, 60.0, 36.63, 83.51].
- **It is recorded and reasoned**, so it is a disposition, not a hidden weakening:
  - D-F1-07 calls it "the one recorded exception to D-S8-02's '7.7 A corridors uncut'";
  - part D, M3_R9 "Ground" and STATUS list it;
  - the recorded DC solves back it: RAW_ACT 0.80 mΩ at 0.05 mm (0.79 before), and C121.2's return 11.98 → 1.38 mΩ
    (`fix1/dc_c121_gnd.txt`; I did not re-run that solve).
- **The summaries contradict it:**
  - `fix1_handoff.md:5`: "no check was weakened";
  - `R9_DECISIONS.md:2146`: "no check is weakened";
  - `R9_VALIDATION.md:273`: "weakened no check";
  - the hard-gates row "No rule weaker than R8" (`R9_VALIDATION.md:77`) lists D-F1-07 only as an addition.

  The owner summary's bold "No gate exception" (`R9_VALIDATION.md:174`) speaks of the final gate only. The step-8 gate
  holds the exceptions of C9, C11, C22 and D-F1-07.
- **The exemption is looser than the copper gate's exceptions in the same file:**
  - its box lives in the design aid, so editing the aid silently widens the gate;
  - it admits any number of vias in the box. The aid's cluster stage applies the relax to any cluster whose copper
    reaches C121.2's pad, and all 60 of its tries for the (28.85, 59.95) cluster were box spots;
  - it has no stale-entry check, while `COPPER_EXCEPT` has one;
  - the build runs the gate without `--report` (`r9_build.sh:127`), so D-F1-07's "and reports it" leaves no trace in a
    build.
- **Fix:**
  - reword the four places, e.g. "one recorded exception added to the step-8 stitch gate (D-F1-07)";
  - optionally, move the box into `r9_ground_check.py` with the one via it admits, and fail when the exception is unused
    or a second via uses it.

### R9P2-INTEGRITY-03: Minor. Five fix-pass record statements do not match what happened

- **(a) The evidence count.** `fix1_handoff.md:44` says "70 evidence files bound". `step10_evidence/check_records.txt`
  and my re-run say 69, and the folder holds 69 files.
- **(b) A decision that does not exist.** `step10/check_records.py:235` cites "D-F1-12". The decisions end at D-F1-11,
  which is the one that moved the solves.
- **(c) "The RAW_ACT solve is unchanged."** `r9_ground_aid.py:41`, `r9_ground_aid.py:153-154` ("the RAW_ACT solve is
  unchanged (0.79 mOhm, the neck at Q121)") and `M3_R9.md:256` say so.
  - The final solve is 0.80 mΩ, neck 7.89 mm (`step10_evidence/dc/dc005_raw.txt`); fc3d5b34 gave 0.79 mΩ, 7.81 mm.
  - D-F1-04 credits the change to TP120's dropped via. The box via's own effect was never solved separately.
- **(d) C21's evidence was deleted.** The J122 relief trial (D-F1-06, C21) measured a 0.86 mm² single-spoke F.Cu
  piece at x 18.15–19.13, y 62.61–64.31, and an islands-gate failure. No file holds that result.
  - D-F1-06 says the RELIEVE variant was not kept. It sat in the scratch folder (`fix1_progress.md:59`), which was
    then deleted (`fix1_progress.md:85-87`).
  - Yet `fix1_progress.md:87` says "Every result the records cite is in `fix1/` or `step10_evidence/`".
  - C21 is an owner-acceptance item.
- **(e) "No legal spot" sometimes means "60 spots tried".** The aid prints "no legal spot" whenever `place_safe`
  uses up `COPPER_TRIES` (60) (`r9_ground_aid.py:884`, `:936`). I re-ran its candidate search on the board for the
  (28.85, 59.95) cluster:
  - 0 legal spots under the normal rules, so C22's conclusion holds;
  - 388 legal spots under the C121.2 relax that the aid applied, all inside the box, of which it tried 60.

  C22's "each a cluster the aid's copper stage found no legal via in" is therefore true only under the normal rules.
  C121.2's own pad stage also stopped at the cap (its 60 rejections in `aid_copper.txt`).
- **Fix:**
  - correct (a)–(c);
  - re-run the RELIEVE trial's islands gate into `fix1/`, or say in C21 that its figures were not kept;
  - have the aid log "cap reached" separately from "no legal spot".

## Not findings (checked)

- **The copper gate's exceptions.** All six clusters and J9.2 have a "no legal spot" line in the aid's log. Five of
  the clusters and J9.2 had no candidate at all: no `place_safe` rejections precede their lines. The sixth is (e)
  above, and it is still justified under the normal rules.
- **The other In2 cuts.** Five table vias inside the In2 RAW_ACT outline lie south of the corridor box (y < 60.0),
  outside the corridor rule's scope, as D-S8-02 session 2 recorded.
- **P-7b's exemptions** are each needed:
  - U1's own pads, because the 0.5 mm LQFP pitch puts U1.2 / U1.4 inside 0.5 mm, and they are no-net sentinels
    (D-S5-13);
  - GND;
  - unconnected copper, which has no source.
- **The ground gate's reference ceiling.** It still equals the built board's count: unreferenced 3206 =
  `REF_UNREF_MAX`. P9 3.37 ≤ 3.5 and P10 7.32 ≤ 7.35 mm; P7 9 with `WEAK_EXCEPT` unchanged.
- **The stage replay ran in the worktree itself** (the fix pass's `stage_runner.sh` changes into it). The whole-build
  clones (the fix pass's and mine) reproduce its result, so no stray worktree state entered the board.
- **Build 1's sheets.** The fix pass's build 1 did not re-run lines 1–5 (the sheets, netlist, DRU and variants);
  `build_sha256.txt` says so. Build 2 and my build re-ran them and match.
- **The post gate's DC rows.** They are at 0.1 mm (RAW_ACT 0.80, BAT_IN 0.17, ACT_FET_S 0.27 mΩ; 12.6 / 12.1 /
  20.8 °C). The records' figures are the 0.05 mm solves (0.80 / 0.16 / 0.26 mΩ; 12.6 / 12.1 / 20.4 °C), and both are
  labelled with their grid.
