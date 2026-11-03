# R9 step 2 (schematic and footprints): progress log

Brief: r9_plan.md §4 step 2. Build m3_design/r9_sch.py (R8 -> R9: J121/J124 pad-renumbered footprint, J122 mirrored
numbering, same part and land; rev M3-ASSY-R9; notes), the footprint variants, removal of every local clearance override
(LC-1), test-pad clearance moved into the DRU (pyro rules A-H unchanged or stricter; P-1b rule G scope). Verify: ERC 0;
parity on a scratch board (the R9 board does not exist yet); the netlist diff is footprint-field / pad-numbering only
(listed); still 52/52 extended codes; check_actuators' schematic contracts hold.

Step 1 handoff read (r9_step1_handoff.md). No step-2 log existed at start: fresh start.

## Plan

1. [x] Inspect R8's J121/J124/J122 board footprints, the library, overrides, DRU, KiCad DRU semantics (wildcards).
2. [x] m3_design/r9_lib.py: the two variant footprints (generated from the base files), the board-side footprint
       exchange and override clearing (used by step 3's builder), the pad maps.
3. [x] m3_design/r9_dru.py (or section): DRU R8 -> R9 (P-1b rule G scope, test-pad 1.0 mm rule, RAW_ACT PTH rule).
4. [x] m3_design/r9_sch.py: sheets R8 -> R9 (footprint fields, rev, notes), netlist.
5. [x] Re-pin check_actuators DRU_SHA / PYRO_RULE_SHA (G), check_r9 CHECK_ACTUATORS_SHA; tools that key on footprint
       names (fit_check MATED, jlc_orient pad maps).
6. [x] m3_design/r9_sch_check.py: ERC, netlist diff, RF/safety, scratch-board parity, check_actuators, LC-1, BOM codes.
7. [x] Seeded tests; full tool suites; R9_DECISIONS; handoff.

## Log
- R8 overrides (KiCad python on the worktree board): 29 local clearances, all on pads: J124.2 and J122.2/5/8/11
  (RAW_ACT) 0.3 mm, 24 test pads 1.0 mm. No footprint-level override; the library carries none (M3_AON7524's
  "(clearance outline)" is a custom-pad shape option; TC2030's is its keep-out zone's connect_pads clearance). J122's
  GND pads carry ZONE_CONNECTION_FULL (instance data, kept by the in-place variant exchange).
- KiCad 10 DRU facts measured on a scratch R8 copy (step2/drutest): memberOfFootprint('TP*') wildcards work (a 3V3
  track 0.6 mm from TP74: flagged by a 'TP*' rule and a 'TP74' rule, not by a 'TQ*' rule, not without a rule).
- Footprint variants: m3_design/r9_lib.py writes M3_DB128L_2P_BK_SW and HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR from
  their bases (mirror about local y; asserts: same pads by number at mirrored positions, same land set, courtyard
  and fab outline symmetric and unchanged, same single 3D model, texts on x = 0). Pad alias variant -> base: DB128L
  1:2 2:1; header 1:10 2:11 3:12 4:7 5:8 6:9 7:4 8:5 9:6 10:1 11:2 12:3. Header model (EasyEDA): bbox symmetric
  (+-2.0 x +-1.49 VRML units = +-5.08 x +-3.79 mm); asymmetric vertices are a white top-face glyph (shapes 4-5) and
  the mesh triangulation.
- Board side: apply_variants() on a scratch R8 copy mirrors J121/J124/J122 in place; compare_to_library() clean and
  KiCad DRC reports no lib_footprint_mismatch; negative control (J124 pads mirrored, FPID left at the base): DRC
  reports lib_footprint_mismatch and compare_to_library() flags pads 1, 2. Idempotent (second call changes nothing).
- m3_design/r9_dru.py: R8 DRU (sha256 1674d58b...) -> R9 (sha16 5aa63b0aeabb43eb; rule G sha16 740c8388e07e6197):
  rule G P-1b scope, "R9 RAW_ACT pins to foreign copper" 0.3 mm before the pyro rules, "R9 bare test pads to foreign
  copper" 1.0 mm last. Seeded DRC (scratch, zones unfilled, overrides cleared): R9 DRU flags all three seeds (GATE_N
  0.25 mm from 3V3 outside block and U1 -> Pyro G; 3V3 0.6 mm from TP74 -> test-pad rule; GND 0.2 mm from J122.2 ->
  RAW rule); R8's DRU flags none.
- Fill equivalence: R8 board refilled under R8's DRU equals the committed board byte for byte; R8 board with all 29
  overrides cleared, zones unfilled, refilled under R9's DRU: all 14 zone-layer fills identical (boolean XOR area 0).
  So the rules replace the overrides exactly in the filler, and DRC is stricter at J124.2 / J122 RAW (pyro rules
  A, E, A2 apply there again).
- m3_design/r9_sch.py: R8 sheets (9c8179b) -> R9: footprint fields J121/J124 M3_DB128L_2P_BK_SW, J122 ..._MIR; pyro
  pin-order note and servo D121 note rewritten in place (the D121 note named R8's lane reversal); servo J122 note added
  at (20.32, 237.38) (first tried y 283.1: rendered on the frame line, moved; SVG render checked); rev M3-ASSY-R9 on 15
  sheets. Idempotent. ERC (kicad-cli, all severities): 0, no ignored checks. Netlist diff R8 -> R9 (git diff of
  schematic.net.xml): the 15 sheet revs and J121 / J124 / J122's <footprint> and Footprint field only.
- check_actuators re-pinned: DRU_SHA 5aa63b0aeabb43eb, PYRO_RULE_SHA G 740c8388e07e6197 (file sha256 0a4269ca...);
  check_r9 CHECK_ACTUATORS_SHA re-pinned. On the worktree (R8) board with R9's DRU check_actuators fails only 15b
  (R8's rectangle, known from step 1).
- fit_check MATED: the J122 variant entry (same envelope, symmetric).
- jlc_orient: PAD_ALIAS (ours -> maker's numbers) and --out. On a scratch board with the variants: both variant
  entries theta 0 / offset 0 / residual 0 / OK, equal to R8's base entries apart from the footprint name. Control with
  the alias disabled: DB128L theta 180 status OK (a silent 180 deg body turn: wire entry into the board, pads still on
  pads), header CHECK (no fit). tools/jlc_corrections.json NOT regenerated (it is generated from the final board in
  step 9; it has no entries for the variants yet, so export_fab refuses until then).
- CORRECTION to the fill-equivalence entry above: that comparison used a 1e-6 mm2 threshold. At zero threshold the
  full R9 DRU gives R8_3V3_In2 sub-um2 slivers (R8-only 515064 nm2, R9-only 298008 nm2 in all; 10 / 5 slivers
  <= 0.13 mm long, nm-thin, along y ~ 54). Isolated (scratch step2/drutest, separate processes): R8 DRU + G edit only,
  overrides kept -> the same slivers; R8 DRU + the two LC-1 rules only, overrides kept -> identical; same with the 29
  overrides cleared -> identical (0 nm2); R8 DRU with overrides cleared -> GND_F, GND_B, R8_RAW_ACT_F gain 34, 116, 2.6 mm2. So the
  LC-1 rules replace the overrides exactly; rule G's wider scope causes the slivers (polygon arithmetic, no copper
  change). r9_sch_check now gates the exact LC-1 equivalence (R9 DRU with R8's rule G text, 0 nm2).
- r9_sch_check.py written (ERC, variants, DRU, netlists, diff, RF/safety, BOM 52/52, scratch-board parity / library /
  LC-1 / check_actuators / pin map / pad roles + control / DRU liveness / fill equivalence / JLC): OK, ~15 s.
  End-to-end negative (project copy with J122's field reverted and the DRU edited): 6 failures, as expected.
- ERC catches a missing footprint (footprint_link_issues on a field naming 'rocket:HDR-NOPE'), so ERC 0 also means the
  variant footprints resolve in the library.
- check_r9 K-contract pins R9_FOOTPRINTS (D-S2-12); test_r9_check updated: R8_FAILING + K-contract; the K-contract test
  applies the variants first and shows D92 (K-legends) catching R8's terminal legends beside the swapped pins.
- test_r8_place's reservation test now runs on R8's own board / pro / DRU from git (R9's rule G also reports R8's
  GATE_N via beside ARM1_SENSE, a recorded R8 fact the test is not about).
- tools/test_r9_sch.py: 20 tests (library, rules, sheets, board), OK under KiCad python (plain python3: 14 run, 6 skip).
- m3_design/r9_build.sh (step-2 stages): two runs byte-identical (sheets, netlist, DRU, variants).
- Final: tools/check.sh on the worktree stops at stage 1 as expected (DRC 1: rule G P-1b reports R8's GATE_N via
  0.22 mm from ARM1_SENSE; parity 3: the decided footprint changes; ERC 0). All 19 tool suites (344 tests) OK,
  quality_audit 21 OK under both pythons (step2_evidence/tests.txt); r9_sch_check OK (step2_evidence/). Scratch
  boards and test temp folders deleted. R9_DECISIONS D-S2-01 ... D-S2-13 written. Handoff: r9_step2_handoff.md.
  Step 2 complete.
