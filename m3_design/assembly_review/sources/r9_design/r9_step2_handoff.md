# R9 step 2 (schematic, footprints, design rules): handoff

Step 2 of `r9_plan.md` §4. The R9 schematic, the two footprint variants, the R9 design rules and the board-side
footprint rules (for step 3's builder) are in place and verified. No board was built: the worktree's `m3.kicad_pcb` is
still R8 (`cc044ea0…`). Nothing committed or pushed. Decisions: `R9_DECISIONS.md` D-S2-01 … D-S2-13. Log:
`r9_step2_progress.md`. Evidence: `step2_evidence/`.

## 1. What was produced

| File | What it is |
|---|---|
| `m3_design/r9_lib.py` | Generates `M3_DB128L_2P_BK_SW` (J121, J124) and `HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR` (J122) from their base footprints: the base mirrored about local y, so the same part on the same land with the numbering reversed along x; the square pin-1 pad and the header's pin-1 silk move with pin 1 (D-S2-01); asserts same land, symmetric body, same model. `--check`. Board side: `apply_variants(board)` (in-place exchange, idempotent, checked against the library), `clear_overrides(board)` (LC-1), `compare_to_library(f)` |
| `kilib/rocket.pretty/M3_DB128L_2P_BK_SW.kicad_mod`, `…/HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR.kicad_mod` | The generated variants (3D models: the bases') |
| `m3_design/r9_dru.py` | R8's `m3.kicad_dru` (sha256 pinned) → R9's: rule G's P-1b scope; "R9 RAW_ACT pins to foreign copper" (0.3 mm, before the pyro rules); "R9 bare test pads to foreign copper" (1.0 mm, last). Every other rule byte for byte (`verify`). `--check` |
| `m3_design/assembly_review/m3.kicad_dru` | The R9 rules (sha16 `5aa63b0aeabb43eb`, rule G `740c8388e07e6197`) |
| `m3_design/r9_sch.py` | R8's sheets → R9's: J121 / J124 / J122 footprint fields, the pyro pin-order note and the servo D121 note rewritten, a J122 numbering note, rev M3-ASSY-R9 on 15 sheets; `--netlist` |
| `m3_design/assembly_review/*.kicad_sch`, `schematic.net.xml` | The R9 schematic and netlist |
| `m3_design/r9_sch_check.py` | The step gate (below), on the worktree and on a scratch R8 board with the variants; `--project`, `--keep`, `--json` |
| `m3_design/r9_build.sh` | The build so far: restore R8's sheets / netlist / DRU from 9c8179b, r9_lib, r9_dru, r9_sch --netlist, r9_sch_check. Later steps append their stages |
| `m3_design/check_actuators.py` | `DRU_SHA` and rule G's `PYRO_RULE_SHA` re-pinned to the R9 DRU (nothing else); file sha256 `0a4269ca…` |
| `tools/check_r9.py` | `CHECK_ACTUATORS_SHA` re-pinned; K-contract pins `R9_FOOTPRINTS` (J121 / J124 / J122 on the variants, D-S2-12) |
| `tools/jlc_orient.py` | `PAD_ALIAS` (our pad number → the maker's, D-S2-08) in generator and `--verify-cpl`; `--out FILE` |
| `tools/fit_check.py` | `MATED` entry for the J122 variant (same envelope) |
| `tools/test_r9_sch.py` | 20 tests: library (variants = committed files, same land, alias = jlc_orient's table, asymmetric body / rotated item / tampered file caught), rules (transform = committed, only G changes, edits caught, check_actuators pins), sheets (R8 → committed, idempotent, wrong field / note refused), board (in place, idempotent, pad nets and J122 GND zone connections kept, square pad on pin 1, moved pad caught, wrong base refused, LC-1 clean, check_r9 pin, netlist / BOM diffs caught) |
| `tools/test_r9_check.py` | `R8_FAILING` + K-contract (18 rules); the K-contract test applies the variants first and shows D92 (K-legends) catching R8's terminal legends beside the swapped pins |
| `tools/test_r8_place.py` | Its reservation test runs on R8's own board / pro / DRU from git (R9's rule G also reports R8's known GATE_N via) |
| `sources/r9_design/step2_evidence/` | `r9_sch_check.txt` / `.json`, `netlist_r8_r9.diff`, `dru_r8_r9.diff`, `tests.txt` |

## 2. Verification

| Item (r9_plan §4 step 2) | Result |
|---|---|
| ERC 0 | kicad-cli, all severities: 0 violations, no ignored checks. ERC also reports a footprint field naming a missing library footprint (`footprint_link_issues`, tried), so 0 means the variants resolve |
| Netlist diff footprint-field / pad-numbering only (listed) | Fresh exports equal the committed R9 and R8 netlists. Diff R8 → R9 (249 parts, 749 pins compared): **J121** `rocket:M3_DB128L_2P_BK` → `rocket:M3_DB128L_2P_BK_SW`; **J124** the same; **J122** `rocket:HDR-TH_12P-P2.54-V-M-R3-C4-S2.54` → `…_MIR` (each in `<footprint>` and the Footprint field); the 15 sheets' rev M3-ASSY-R8 → R9. Every other field, value, library part, pin function, pin type and pin net identical (the pad renumbering lives in the footprints: each pad number keeps its net) |
| Parity | The R9 board does not exist yet (step 3). On a scratch R8 board: parity against the R9 schematic is exactly the three decided `footprint_symbol_mismatch` items; after `apply_variants` + `clear_overrides` parity is 0 and KiCad reports no `lib_footprint_mismatch` (negative control: pads mirrored with the FPID left at the base → DRC reports it) |
| Still 52 / 52 extended codes | Every part's LCSC code is R8's; R8's JLC BOM (92 lines, 219 parts) reproduces from the R9 netlist code by code; R8's supplier check (2026-10-19, bound to that BOM by sha256 `be711876…`) classes 52 of them extended: 52 ≤ 52. No fresh supplier query (REQUIREMENTS M3's 24 h re-run is step 9's) |
| check_actuators' schematic contracts hold | On the scratch variant board with R9's DRU: rules 1–14, 16 and the DRU / rule pins hold; the only finding is 15b (the PYRO_BLOCK area against R8's placement: board geometry, step 3). check_r8's pin table, U1 map and loader pins hold (R9 keeps R8's pin table) |
| LC-1 | All 29 overrides (J124.2, J122.2/5/8/11 at 0.3 mm; 24 test pads at 1.0 mm) cleared; check_r9 LC-1 clean |
| Test-pad clearance in the DRU, pyro rules unchanged or stricter | Pyro A–F, A2, H byte-identical; G only the P-1b scope (stricter). Seeded DRC (scratch, zones unfilled, overrides cleared): R9's DRU reports GATE_N 0.25 mm from 3V3 outside PYRO_BLOCK and U1 (rule G), 3V3 0.6 mm from TP74 (test-pad rule), GND 0.2 mm from J122.2 (RAW pin rule); R8's DRU reports none. Fill: R8's board, overrides cleared, refilled under R8's rules + the two LC-1 rules: all 14 zone-layer fills equal R8's committed fills exactly (0 nm²); rule G's wider scope alone moves R8_3V3_In2 by sub-µm² slivers (no copper change, D-S2-06) |
| Pad roles | At the planned rotations (J121 / J124 90, J122 180) the variants put J124's RAW and J121's IGN pin forward of BUS / OUT with wires entering −x, J122's SIG row aft with SERVO1–4 west to east; the bases at the same rotations fail all three (control) |
| JLC placement | jlc_orient on the scratch board: both variants theta 0, offset 0, residual 0, OK, equal to R8's base entries; without the alias the DB128L comes out theta 180 "OK" (a silent body turn) |
| Reproducible | `r9_build.sh` twice: sheets, netlist, DRU and variant files byte-identical |
| Tool tests | 19 suites, 344 tests, every one OK (`step2_evidence/tests.txt`), quality_audit 21 OK under both pythons; `r9_sch_check.py`: OK; end-to-end negative (a project copy with J122's field reverted and the DRU edited): 6 failures |
| tools/check.sh on the worktree | Stops at stage 1, as expected until step 3: DRC 1 (R8's GATE_N via 0.22 mm from ARM1_SENSE, now reported by rule G's P-1b scope: the known R8P1-PYRO-04 pair), parity 3 (the decided footprint changes), ERC 0 |

## 3. Reproduce

```bash
R=rocket-pcb/rocket-flight-computer-r9            # this worktree
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
$R/m3_design/r9_build.sh                                       # step 2 stages + r9_sch_check (about 30 s)
PYTHONUNBUFFERED=1 $KP -I -B $R/m3_design/r9_sch_check.py --json out.json        # the step gate alone (about 15 s)
python3 -B $R/m3_design/r9_lib.py --check && python3 -B $R/m3_design/r9_dru.py --check
cd $R/tools && for t in test_*.py; do $KP -B -m unittest "${t%.py}"; done        # 19 suites, 344 tests (about 4 min)
```

## 4. What the next steps must know

**Step 3 (placement, `r9_pcb.py`).**
- After loading R8's board: `r9_lib.apply_variants(board)` then `r9_lib.clear_overrides(board)` (both assert and are
  idempotent). No pad changes net: R9's netlist is R8's pin for pin, so a netlist-apply step should change 0 pads
  (assert it). Parity then needs nothing else from the schematic.
- Rotations: J121 / J124 at 90 (entry −x, P-11) give pin 2 (RAW / IGN) forward of pin 1 (BUS / OUT), the plan's
  arrangement; J122 at 180 gives plug 1 (SERVO1) west and the SIG row aft. The square pad is on pin 1 (BUS, OUT,
  SERVO1's signal): plan_spine's prototype measured with the square on the other pin (it swapped nets), so P-0 / DRC
  margins are re-measured on the real geometry; the prototype's (RAW branch to BUS 3.0 mm against E 1.0) leave room.
- The legaliser's clearance model (R8's `r8_legalise.rule_clearance`) must follow R9's DRU: rule G applies outside
  U1's courtyard too (not only `at_block`), every RAW_ACT through-hole pad (J124.2, J122.2/5/8/11) 0.3 mm from all
  copper, every TP* pad 1.0 mm from all copper; there are no local clearances left to read.
- check_actuators 15b still fails on R8's PYRO_BLOCK rectangle: step 3 derives the area (P-1).

**Step 8 (silkscreen).** Terminal legends are drawn by pin, not copied: R8's "1:BUS1" / "2:RAW" / "1:E1-" / "2:E1+"
end up beside the wrong pins once the pads swap, and check_r9 D92 (K-legends) fails them (shown in test_r9_check). The
J122 SERVO 1–4 legend runs west to east.

**Step 9 (fab).** Regenerate `tools/jlc_corrections.json` with `tools/jlc_orient.py` on the final board (PAD_ALIAS is in
place; until then the file has no variant entries and `export_fab.py` refuses the R9 board). The BOM's Footprint
column names the variants for J121 / J124 / J122. Cost and stock re-run within 24 h of ordering (M3).

**Step 10 (records).** Harness / FMEA / ORDERING text: J124's RAW pin forward and BUS aft, J121's IGN pin forward and
OUT aft, both wires from −x; J122 plug 1 = SERVO1 at the west end; the P-1b rule retires REQUIREMENTS' accepted risk
"gate-net spacing outside the pyro block is the board's 0.15 mm default"; the R8 record note on J124.2 / J122's 0.3 mm
overrides (plan_spine §13 item 7).

**Gate state.** check_r9 on R8 now fails 18 rules (K-contract added: base footprints). Tools that run DRC with the
worktree's project files on an R8-era board now see R9's rules (test_r8_place adjusted; R8's own contract stays
checkable in `../rocket-flight-computer-r8`, untouched).

## 5. Open

- Nothing blocks step 3; no question for the owner arises from step 2.
- Parity, DRC and the full gate on the real R9 board: step 3 on.
- Rule G keeps its name ("gate nets in the pyro block") though its scope now also covers everything outside U1's
  courtyard; the DRU comment says so (renaming would touch the step-1 gate's keys for no safety gain, D-S2-05).
- Minor: a few new code lines run to 121–125 characters (the repo has no linter gate).
