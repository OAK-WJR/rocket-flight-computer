# R9 review pass 1: gate and build integrity

Reviewer dimension: gate and build integrity. The questions were:
- Does `m3_design/r9_build.sh` reproduce the board byte for byte?
- Is every gate and per-step check real? Nothing may be weakened or special-cased to make R9 pass, judged against the
  R8 versions at `9c8179b`, and the replacements for R8's rigid hashes must be at least as strict as claimed.
- Do the seeded tests fire?
- Does the no-GUI shim leave results unchanged?
- Do the records claim only verification that happened?

Board under review: `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51`. It was hashed at the start and the end of this
review and is unchanged. This review modified no repository file except this report.

## Verdict

**0 Critical, 0 Major, 6 Minor.**

- The build reproduces byte for byte. This is the first time `r9_build.sh` itself has been run, with no shim. Steps 6–9
  had only replayed its lines through a scratch runner with the shim.
- `tools/check.sh` exits 0, and its output equals the step-10 evidence.
- The 474 tests pass, and the seeded suites fire.
- Against R8, no gate, allowlist, threshold or exemption is weakened to let R9 pass. The changes are strictly
  stricter, or owner-decided and recorded.

The Minors are four kinds of gap:
- two places where a replacement check is not as strict, or not as deterministic, as claimed (01, 02);
- one latent rule-order hole that a design-rules comment hides (03);
- one seeded suite whose pass criterion is looser than its text (04);
- stale text, and one pre-existing test-hermeticity issue (05, 06).

None of them changes the verdict of any check on this board.

## 1. What was run (independent of the step records)

All runs used scratch clones under `<scratchpad>/r9review/integrity/`. Each clone is a `git clone --shared` of the main
repository at `9c8179b`, with the R9 worktree's files rsynced over it. Clone 1's `git status` was diffed against the
worktree's and is identical (112 entries); clone 2 also shows 112 entries. Apart from reports the other reviewers
wrote in the meantime, clone 2's files hash-equal clone 1's. A GUI session was logged in (`who`: console), so
kicad-cli ran directly.

| Check | Result |
|---|---|
| `NUMPY_PY=<cfd venv> bash m3_design/r9_build.sh`, run directly (clone 1) | **rc 0 in 40 min 12 s.** Every stage gate OK: schematic, placement, RF strip (79 GCPW samples, 50.16–51.08 Ω, launch XOR 0.0008 mm²), pyro, power, the ten routing families, ground, post. The final `tools/check.sh` exited 0. **Every built file is byte-identical to the worktree:** the board `fc3d5b34…`, the 15 sheets, `schematic.net.xml`, `m3.kicad_dru` and both variant footprints. A whole-tree hash diff before and after the build shows only new git-ignored `__pycache__/*.pyc` files. `git status` is unchanged |
| `tools/check.sh` on the unmodified board (clone 2) | **rc 0 in 266 s.** Its stdout is identical, line for line, to `step10_evidence/gate/check_sh.txt`, ignoring wx debug lines, the temp-path line and the timing. Compared field by field with the bound evidence: `seed.json`, `fit.json` and `plate.json` are equal. `drc.json`, `erc.json` and `route.json` differ only by the added binding field, and `audit.json` only by paths and dated report hashes. `r9.json` differs only in nondeterministic evidence fields (finding 01) |
| Test suites (clone 2, KiCad python3, real kicad-cli) | **26 suites, 474 tests, all OK, 0 skipped.** `quality_audit`, with `KICAD_PY` and `KICAD_CLI` unset, passed 21/21 under python3 and under KiCad python3; with `KICAD_PY` exported it gave 3 failures and 1 error (finding 06). `audit_artifacts` exit 0. A whole-tree hash diff shows the clone unchanged by the runs |
| `step10/check_records.py` (clone 2) | OK. Its report is identical to `step10_evidence/check_records.txt`: 56 files bound, 151 inputs equal, 39 requalification rows, 87 figures |
| DC spot checks with `tools/dc_solve.py`, the `run_dc_r9.sh` arguments | `fire_bus` 2.41, `fire_out` 1.58 and `fire_raw` 10.06 mΩ: equal to `step10_evidence/dc/`. The `fire_loop.txt` arithmetic checks: 17.70 + 14.40 = 32.10 mΩ, and 7.4 V / 4.4821 Ω = 1.651 A |
| Determinism probe: `check_r9.py --only R-5` with `PYTHONHASHSEED` 1, 2 and 3 | The verdict is OK every time, but the window split changes from run to run (finding 01) |
| R8 / R7 / R6 worktrees | R8 and R7 are clean at `9c8179b` / `431025d`; R8's board is `cc044ea0…`. R6's local modifications all date from 2026-10-13, before R9 began (2026-10-20) |

## 2. Gate changes against R8 (`git diff 9c8179b`)

| File | Change | Judgement |
|---|---|---|
| `tools/check.sh` | `check_r8` is replaced by `fit_check` → `plate_model` → `rule_h_seed` → `check_r9`. Then `route_check --profile r9` and `check_actuators` run, with `set -euo pipefail` kept | Nothing is dropped. `test_check_shell` proves the stage order, and that each stage's failure stops the stages after it |
| `tools/route_check.py` | Adds profile `r9`: `ALLOWLIST`, `LEFTOVERS` and `ROUTE_FIGURES` are all empty, with R8's D10 keep-out baseline. No other code reads the profile name | Stricter than r8 (R8's A8, A2 and A3 entries are gone) |
| `tools/fit_check.py` | The J122 tie holes are derived from J122 (`retention_holes`). It falls back to R7's constants if the derivation fails | That fallback is silent inside `fit_check`, but `check_r9` M-3 reports the same derivation's problems as failures. Acceptable |
| `m3_design/check_actuators.py` | `DRU_SHA` and rule G's `PYRO_RULE_SHA` are re-pinned. Check 15b goes from "exactly R4's rectangle" to "one area, all four layers, restricting nothing, containing every CH1 courtyard + 1 mm, all block-net copper, and the exit copper within 3 mm" | A larger area only widens rule G, and `check_r9` P-10 bounds the area from above. The re-pins follow the reviewed DRU edits. `test_check_actuators_15b_is_rule_based` seeds a notch and a restriction, and both are caught |
| `m3.kicad_dru` | Rule G's scope is widened to everything outside U1's courtyard (P-1b). Two LC-1 rules replace R8's 29 pad overrides. Eight zone fill-margin rules are added after A2, each repeating its base rule's condition on zones at +0.25 mm (E +0.35) | Every R8 rule is otherwise byte-identical, in R8's order (`r9_dru.verify`, run in build stage 4). The three new rule types are live, shown by seeded DRC hits in `r9_sch_check` stage 4 (G 2, TP 1, RAW_ACT 1, against 0 under R8's rules). This includes `memberOfFootprint('TP*')`. One latent order hole: finding 03 |
| `tools/test_r8_*.py`, `test_reference_audit.py`, `test_fab_validation.py` | These now judge R8's committed board through `r8_record.py`, which SHA-checks `cc044ea0…` from git. The D14 test now hashes R8's own `check_actuators` from git | The R8 record keeps its meaning. No assertion is weakened |
| `tools/jlc_orient.py`, `jlc_corrections.json` | Adds `PAD_ALIAS` for the renumbered variants | Necessary. Without it, `--verify-cpl` cannot see a two-pin part turned 180°. `test_jlc_pad_alias_matches_the_library` holds the map to the library files |

## 3. `check_r8` → `check_r9`: is each replacement at least as strict?

Each R8 check was traced to the R9 rule that replaces it.

**Kept or strengthened:**
- pin table and U1 map, loader pins, connectors, module pins, series and pull resistors, DNP, modules on top, RF parts
  off safety nets (K-contract);
- outline: now also a rectangle at (0, 0);
- legends and terminal legends (K-legends); foreign clearances (P-9);
- vias in pads, overlap joints, thermals, via paste (K-copper);
- `rf_separation`: parts must now be 5.94 mm apart, up from 5.0 (R-10);
- `inner_power_pyro` 2.65 mm, up from 2.5; `battery_pyro` 2.5 mm, up from 1.0; `gate_servo` (K-power-pyro);
- `inner_signal`: R8's rigid In2 exemption is gone (K-inner);
- fence (R-7), stitching (R-7 drops R7's 4.0 / 2.7 mm ceilings), `rf_grounds` (R-7), `rf_gnd_reach` (R-7, 4.0 mm);
- `launch_reference` (R-4, the same grid);
- `u31_body_keepout` (R-8).

**Replaced by rules, by owner decision.** These rigid groups are the outline, the M3 holes, J122 with its tie holes,
J1, PYRO_BLOCK, CH1 parts and copper, strip parts, RF copper, strip GND, rule areas and the GCPW profile. They are
replaced by:
- M-2…M-7 and fit;
- P-0…P-11;
- R-1…R-13;
- the build-time step gates. These include the R7 congruence of every chain part, and the launch GND XOR against R7
  (0.0008 mm² in the build). Step 10's `requalify_r9.json` records `gnd_xor_r7_mm2` 0.0 for both launches on the
  final board.

The build re-runs the pyro margin floors (Z1) after every later step, in the route and ground gates, through
`r9_power_check.gate_pyro`. So the Z1 floors hold on the final copper even though `check.sh` checks rule minima only.

**Owner-decided relaxations, each recorded:**
- M-5's J122 mated floor of 0.49 mm (R8 0.715; owner decision 4/5);
- R-13's 40 mm radio-to-pyro limit (R8 68.4; owner decision 3);
- the jack axis held to a range instead of R7's fixed positions (a clean-sheet layout).

**Not as strict, and not recorded:** R-8's In1 ground sampling under U31 (finding 02).

## 4. Seeded tests

- **`rule_h_seed.py` evidence** (`gate/seed.json`, reproduced exactly by my gate run): 3 pairs × 8 variants.
  - DRC catches every plain seed, and LC-1 catches every pad override (DRC is blind to it).
  - `check_actuators` catches all six rule-H text edits on all three pairs.
  - The control pairs show no hit before seeding.
  - The suite's own pass criterion is looser than its text, though (finding 04).
- **`test_r9_check.py`, 52 tests:**
  - every rule passes on a clean or repaired base and fails on its seed;
  - LC-1 catches an armed-pad override;
  - the GCPW solver is within 1 Ω of pass 2;
  - R8 fails the 18 rules recorded for it.
- **Step-gate suites** (`test_r9_sch`, `_place`, `_rf`, `_pyro`, `_power`, `_route`, `_ground`, `_post`): every seeded
  case fires. My run: 474/474.

## 5. The no-GUI shim (D-S6-14 / D-S9-06)

The shim makes `wxGetMousePosition` return (0, 0). Three comparisons show that it changes nothing:
- Step 9's shim-built board is byte-identical to my build without the shim (section 1).
- The stdout of step 9's shim run of `check.sh` (`step9_evidence/check_sh.txt`) equals step 10's run without the shim,
  line for line. The only differences are the temp path and the timing.
- My own run without the shim equals step 10's.

## 6. Records against what happened

These record claims were checked and confirmed:
- the 474 tests, 26 suites and none skipped;
- `quality_audit` 21 under both Pythons with `KICAD_PY` unset;
- `audit_artifacts` exit 0;
- `check.sh` exit 0, all 40 `check_r9` rules OK, and route_check with 0 failing, 0 allowlisted and 0 leftovers;
- the DC rows and the F7 arithmetic;
- the `check_records` figures;
- the M3_R9 26-row supply table, compared row by row with `dc_summary.txt`;
- the disclosure in R9_VALIDATION §"Environment" that steps 6–9 ran through the shim;
- the claim in M3_R9 and STATUS that `r9_build.sh` rebuilds the board byte for byte, which is now true of the script
  itself.

Two statements are wrong. Both are folded into the findings below:
- D-S10-18 says the radio window split was unchanged across runs (finding 01);
- M3_R9 §"Ground" gives 183 GND vias (finding 05).

## Findings

### R9P1-INTEGRITY-01: Minor, worth fixing. `check_r9`'s report is not reproducible from run to run, more broadly than D-S10-18 records

- **The mechanism.** `check.sh` runs the checker with `python -I`, which ignores `PYTHONHASHSEED`, so string hashing is
  randomised in every run. Two pieces of evidence depend on set iteration order:
  - **R-5 window attribution.** A sample lying within 0.3 mm of two chain parts goes to whichever part the set
    `chain_parts()` yields first (`tools/check_r9.py:1024-1028`, `:1267`).
  - **P-0 closest pair.** Among pairs at exactly equal distance, pyro_probe keeps the first one found. Its pairs are
    built from a set of net names (`tools/pyro_probe.py:146`, `:161`, `:194`).
- **What varies (measured).**
  - **R-5, under seeds 1/2/3:** GNSS L30 30/24/24, R304 32/36/36, D30 0/2/2; radio C314 12/12/8, R316 30/30/34. The
    totals (155 / 131) and the verdict never change.
  - **R-5, my gate run against the bound `gate/r9.json`:** RADIO C313 12/8, C314 12/8, R316 30/38.
  - **P-0, my gate run against the bound `gate/r9.json`:** rule C names R173.1–CONT_MID versus R132.1–ARM1_SENSE_MID,
    both 0.577 mm. Rule D names R131.1 versus J124.1, both 0.751 mm. Rule G names U1.4 versus U1.2, both 0.412 mm.
- **The record is wrong.** D-S10-18 (`R9_DECISIONS.md:2099`) says "the radio's split unchanged" and names only R-5.
- **The cost.** Gate reports can never be compared byte for byte, and every comparison needs this kind of special-casing.
  The plan's §5 lists determinism as a gate-integrity criterion.
- **Fix:**
  - iterate `sorted(chain_parts(...))`, or attribute each sample to its nearest pad;
  - in pyro_probe, sort `names` and the pair list, or break ties on the label;
  - then re-run `requalify_r9.py` (its provenance hashes both tools) and the gate.

  No verdict changes.

### R9P1-INTEGRITY-02: Minor, worth fixing. R-8 samples In1 ground only inside U31's pad ring, not under the whole body

- **What R-8 does.** It samples In1 GND every 0.2 mm only over U31's pad-ring interior. The region is
  [26.56, 9.95, 34.66, 18.05], 8.1 × 8.1 mm (`tools/check_r9.py:1478` uses `inner` for F.Cu and In1, and `:1504-1521`
  samples those regions). In2 is sampled over the body.
- **What it should do.** The specification it implements (`survey_constraints.md:329`, item 5) samples GND "under U31's
  body on In1 and In2". So does R8's gate, through `check_r7.module_ground` (`tools/check_r7.py:528-550`), over the
  whole 10 × 10 mm body.
- **The gap.** A no-fill rule area or notch on In1 under U31's 0.95 mm pad-ring band would pass the final gate.
  - R-2 checks only the pour's bounding box.
  - The step-8 table gate checks pour outlines, not rule areas.
  - R-5 covers only the RF pad.
- **Why it matters.** EBYTE's manual §4.1 asks for nothing but ground under the module.
- **The record is wrong.** This contradicts check_r9's header claim, "each at least as strict". The relaxation appears
  in no decision; D-S1-22 covers the keep-out areas only.
- **The board is fine.** Measured on fc3d5b34: In1 and In2 GND at all 2601 of 2601 samples under the body
  (25.61–35.61 × 9.0–19.0).
- **Fix:** sample In1 GND over the U31 body box, as In2 already is. Keep the keep-out coverage on F.Cu and In1 at the
  interior. This board still passes.

### R9P1-INTEGRITY-03: Minor. The test-pad rule's "never lowers a pyro rule" has been false since step 5

- **The claim.** `m3.kicad_dru:147-152`, and `r9_dru.py:19-22` and `:100-106`, put "R9 bare test pads to foreign
  copper" (1.0 mm) last because "no rule above asks more than 1.0 mm" (rules E and H, none larger).
- **What changed.** Step 5 added "R9 fill margin E" at 1.35 mm (`m3.kicad_dru:105-107`). KiCad applies the last
  matching rule; `rule_h_seed`'s `moved_first` variant shows this. So for a test pad on RAW_ACT facing a PYRO1_BUS or
  PYRO1_IGN zone, the governing clearance drops from 1.35 to 1.0 mm.
- **Nothing is affected today:**
  - TP120 is on RAW_ACT, but no zone is on BUS, IGN or OUT;
  - P-9 bars test pads from armed nets.
- **Nothing guards the property:**
  - `check_r9` P-4 polices only rules after H that ask less than 1.0 mm;
  - `r9_dru.verify` checks the rule order, not this property.
- **Fix:** correct both comments. Optionally, have `r9_dru.verify` assert that no later rule asks less than an earlier
  fill-margin rule whose condition it overlaps.

### R9P1-INTEGRITY-04: Minor. The seeded rule-H suite cannot fail on a `check_actuators` regression

- **The criterion.** `tools/rule_h_seed.py:209-227` counts `pyro_probe` as a catcher for every variant. pyro_probe
  reads geometry only, so it always catches the 0.95 mm seed.
- **The consequence.** The "caught by nothing" check is vacuous for the six rule-H text edits. The per-variant
  requirement "check_actuators must fail" (`:12-18`) is not enforced by the suite that `check.sh` runs on every gate.
- **Partial cover.** The unit test `test_rule_h_seeded_suite_end_to_end` (`tools/test_r9_check.py:274-284`) asserts it
  for 4 of the 6 edits, on R8's board, with one pair.
- **This board.** The bound evidence shows `check_actuators` caught all six on all three pairs, so the gate itself
  holds.
- **Fix:** require `check_actuators` in `caught_by` for the six text-edit variants.

### R9P1-INTEGRITY-05: Minor. Stale statements in the tool docstring and the design record

- **`tools/check_r9.py:71`:** the docstring still calls M-7 "U4 bottom, rotation 0 (the M3_R5 axis map)". The rule
  requires 180° for M3-ASSY-R9 (`IMU_ROTATION`, `:209-216`, `:1867-1873`; roll = −gyro_Y, D-S7-06). D-S10-18 records
  this observation.
- **`docs/M3_R9.md:184`:** it gives "183 GND vias from a frozen table". The final `m3_design/r9_ground.tsv` holds 181
  via rows and 4 track rows; step 9 regenerated it under D-S9-01. My build prints "181 GND vias, 4 GND track(s)". The 183
  belongs to step 8's board `89ddea8d`. R9_VALIDATION's step-8 row is correct for that board.
- **Fix:** correct both texts. Fold the docstring edit into finding 01's change to `check_r9.py`.

### R9P1-INTEGRITY-06: Minor (pre-existing, not R9). `quality_audit` tests depend on the environment

- With `KICAD_PY` exported, `test_quality_tools` gives 3 failures and 1 error.
  `verify_board.native_refill_python` (`quality_audit/verify_board.py:61-71`) prefers the environment's interpreter to
  the tests' fakes.
- With the variable unset, all 21 pass. I confirmed both cases.
- The failures are false failures (no fault is masked). `check.sh` runs ERC and DRC itself before the audit.
- The code is unchanged since R6 (`3b215ba`), and D-S10-18 records it.
- **Fix:** have the test fixture clear `KICAD_PY` and `KICAD_CLI`.

## Not findings (checked)

- **The step gates' silkscreen deferral.** Steps 4–8 defer all silkscreen DRC classes; only step 3's judge requires a
  text item. The final `check.sh` DRC, which is inside the build, defers nothing.
- **The step-8 ground gate ceilings.** It raises `P10_MAX` to 7.35 and pins `REF_UNREF_MAX` at 3206, which are step-gate
  ceilings. R9_VALIDATION reports the done-row misses honestly (P10 7.32 > 7.0, R6b 0.1022 > 0.08).
- **The pyro margin exception.** The one exception, GATE_N against U1's no-net sentinels at 0.412 mm (D-S5-13), is
  tested to cover only those pins (`test_the_g_exception_covers_only_the_sentinel_pins`). R9_VALIDATION C12 discloses
  it.
- **Rule G's scope in DRC.** `A.intersectsCourtyard('U1')` exempts a whole gate segment that touches the courtyard.
  pyro_probe (P-0) clips such a segment to its outside part instead, so the geometric gate is the stricter one.
- **Zone clearances.** LC-1 reports the zones' local clearances as floors only. The 0.751 mm GND fill to R131.1
  confirms that the custom rules govern the fills.
- **Evidence binding.** "Binding" names the board's SHA-256 inside each evidence file. For reports that do not carry
  it, `bind_report.py` adds it, an assertion by the caller rather than a proof. My re-runs reproduce the bound gate and
  DC evidence, so the bindings hold.
- **The placeholder generator.** The generator that filled step 10's DC placeholders was not kept. `check_records.py`
  re-derives the 87 figures from the evidence, and my re-run agrees.
