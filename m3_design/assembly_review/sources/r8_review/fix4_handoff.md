# R8 fix pass 4: handoff

Fix pass 4 implements the open items of R8 review pass 4 (`pass4_*.md`, board `c84f00b8…`: 0 Critical, 0 Major,
16 Minor; the records pass after it had already fixed nine): the two copper Minors (R8P4-ROUTING-01 / -02) and the four
text items marked not worth fixing but trivial (R8P4-RF-02, -POWER-02, -DFM-02, -INTEGRITY-02). Everything went through
the R8 generators and tables; `m3_design/r8_build.sh` reproduces the result. Nothing is committed (AGENTS: the owner asks
for commits; R8P4-INTEGRITY-01). Log: `fix4_progress.md`. Decisions: `sources/r8_design/R8_DECISIONS.md` D110, D111
(and pointers added to D16, D33, D37, D42). Dispositions of all 16 pass-4 findings: `docs/R8_VALIDATION.md` "Review
pass 4". `fix4_baseline_sha256.txt` holds the SHA-256 of the 276 changed / untracked files fix pass 4 started from (the
coordinator also kept a backup of the `c84f00b8…` state in the session scratchpad, `r8_backup_c84f00b8/`), and
`fix4_generators.diff` is the diff of the 5 code / table files fix pass 4 changed.

Fix pass 4's board has not itself been reviewed. Its copper diff against `c84f00b8…` is exactly the pass-4 routing
reviewer's trialled variant `rec4` (= `fence2` + `r87`), so a re-check is the owner's call.

- **Final board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7`; netlist `0cc1ed69…` (unchanged). Two consecutive
  `r8_build.sh` runs (609 / 769 s, the second sharing the CPU with the DC solves) gave identical boards, netlists and all
  15 sheets (17 files).
- **Gate:** `tools/check.sh` exit 0 in both builds and standalone twice (before the fab step, and after every record edit):
  DRC 0 at every severity, unconnected 0, parity 0, ERC 0; audit OK; silk OK; `check_r8` OK (report equal to fix pass
  3's but the fence openings and the track-end count); route_check r8 0 failing, 3 allowlisted, 0 leftovers, 0 removable
  (22 bump windows), 94 instances (+1: width_change_junction at the new T); `check_actuators` OK; fit OK. Every step gate
  OK (the rf family 436.6 → 436.9 mm of its 445 mm budget). Build DC gate (0.1 mm): RAW_ACT 5.90 mm / 17.6 °C, BAT_IN
  6.85 / 14.8, ACT_FET_S 4.80 / 22.3 (unchanged). `make_ground.py --built` reproduces the regenerated `r8_ground.tsv`
  byte for byte. route_check `--profile r7` on R7 (with its project files) OK.
- **Tests:** 272 in 17 suites (KiCad Python) OK, run after `r8_fab.sh` (`step9/evidence/fix4_tests.txt`);
  quality_audit 21 under both Pythons OK.
- **Fab:** `m3_design/r8_fab.sh` exit 0: CHECK none; BOM `be711876…` and CPL `ef90bfa1…` unchanged (no part moved);
  verify 85 + 126, worst 0.491 mm; paste check OK (`tools/paste_check.py` standalone too); manifest bound to
  `cc044ea0…`; renders regenerated. The copper and drill Gerbers changed; the silkscreen did not (571 of 571 items equal
  to `c84f00b8…`). Cost / stock not re-run (no network): `FAB_NET=1 m3_design/r8_fab.sh` within 24 h of ordering.
- **DC (0.05 mm, `step9/evidence/fix4_dc_*.txt`):** RAW_ACT 1.45 mΩ, 5.94 mm, 17.5 °C; BAT_IN 0.45 mΩ, 6.99 mm, 14.5 °C;
  ACT_FET_S 0.18 mΩ, 4.97 mm, 21.4 °C; servo GND return (DC_GND 0.1) 0.69 mΩ: every output line identical to fix pass
  3's. Supply paths (0.1 mm, every row re-solved, `fix4_dc_supply_summary.txt`): all equal but USB_LIMITED
  52.62 → 52.66 mΩ (D111; 26 mV at 0.5 A either way).
- **reference_audit:** R6 set 11.07 % (equal); extended 5.81 → 5.80 % (24 more samples on RADIO_MISO_MCU's longer lane,
  none unreferenced). requalify and pyro_neighbours equal to fix pass 3's but the board SHA. Binding note regenerated
  (only its board SHA changed).

## What changed, per item

| Item | Change | Result on `cc044ea0…` |
|---|---|---|
| R8P4-ROUTING-01 | `r8_route_rf.py`: TRIO below-fence x 20.6 / 21.1 / 21.6 → 20.5 / 21.0 / 21.5, step y 22.400 / 22.607 / 22.814 → 22.500 / 22.707 / 22.914, TRIO_STEP 0.4 → 0.5 (in-strip lanes and 45° lines unchanged; comments). `step7/make_ground.py`: FENCE_X 20.00 / 22.10 → 19.95 / 22.05, STRIP_STITCH (22.10, 26.70) → (22.05, 26.70). `r8_ground.tsv` regenerated from the step-6 board (those three rows; one cover row reordered, same coordinates) (D110) | RXEN–(19.95, 23.3), MISO_MCU and MOSI to (22.05, 23.3) / (22.05, 26.7) all 0.200 mm (were 0.250 / 0.150 / 0.150); fence openings 1.75 (no lane) / 2.10 / 2.10 mm; M2 sweep adjacency 53 → 51 rows, net pairs under 0.2 mm 28 → 26, 0.150 mm pairs 9 → 7; C12 #5 / #6 removed (table renumbered) |
| R8P4-ROUTING-02 | `r8_power.py`: USB_LIMITED trunk through (32.2, 55.3); R87.1's branch the T drop (32.2, 55.3) → (32.2, 57.775) (D111) | B.Cu −1.86 mm (51.44 → 49.59 mm), route ratio 1.28 → 1.23; acute pairs 3 → 2 (the two left rigid R7); the 1.65 mm parallel run gone; USB_LIMITED clearances within 0.6 mm unchanged; +1 width_change_junction (C2 90 → 91); step 7 added no via; C21 removed |
| R8P4-RF-02 | ORDERING §5: the camera buck U8 / L3 13.5 / 17.5 mm from U31 and 24.8 / 26.1 mm from U30, courtyard to courtyard; U7 (eFuse, not a switcher) 9.4 / 18.0 mm | records only |
| R8P4-POWER-02 | M3_R8 "Ground": the relief rule as built (R6's R / C GND pads ≤ 2.0 mm), the twelve 0805 / 1206 pads named, the DRU comment left (SHA-pinned) | the same twelve pads with a local thermal connection (measured) |
| R8P4-DFM-02 | `fix3_handoff.md`, M3_R8 manufacturing outputs, R8_VALIDATION fab row: R70's designator re-placed in fix pass 3 by `r8_post.py` (0.2 mm), bottom silkscreen only | fix pass 4 moved no silkscreen item |
| R8P4-INTEGRITY-02 | `r8_build.sh` stage note: "seven pour trims (D65, D90)" | comment only |
| Also | D16 note; D33 / D37 / D42 fix-pass-3 coordinate pointers (pass-4 routing §9); C14 heading "unchanged by fix passes 2–4"; every record's board SHA, counts and review status | — |

## Scorecard (against fix pass 3; `step9/evidence/fix4_scorecard.md`)

Index 15.3 (unchanged; quick 13.7). Targets 20 met / 11 missed (unchanged). Moved: C2 90 → 91; S1 1497.6 → 1497.9 mm;
S2 2088.8 → 2087.2 mm; S6 / S7 1.175 / 287.4 → 1.174 / 285.8 mm; S18 795 → 794; R7 extended samples 102384 → 102408.
No P or D row moved, and of the R rows only R7's sample count (+24 on RADIO_MISO_MCU's longer lane, none
unreferenced; corrected after review pass 5, R8P5-PLANES-01). M2 sweep: chain detours 23; track / via pairs under 0.2 mm 28 → 26 (0.150 mm 9 → 7); pad rows
33; routes 28; folds 26; bumps_all 1; margin_free 1 + 4 (all equal but the adjacency rows).

## Not done, and why

- **R8P4-INTEGRITY-01 (commit / tag):** owner action; the brief said not to commit.
- **Not re-run:** plate model and hot-plug script (no part moved; the hot-plug premise's parts and copper untouched);
  live cost / stock (network). A review of `cc044ea0…` itself (the owner's call).
- **Open:** the owner's acceptance of the deviation list and its decisions, C10, U4 consignment, JLC tab acceptance,
  firmware binding, bench items.

## Reproduce

```
m3_design/r8_build.sh                       # twice; compare SHA-256 (cc044ea0…)
KICAD_PY=<KiCad python3> tools/check.sh
m3_design/r8_fab.sh                         # before the tests: test_fab_validation judges the package against the board
PY=<KiCad python3>; (cd tools && for t in test_*.py; do $PY -m unittest ${t%.py}; done)
$PY -m unittest quality_audit.test_quality_tools; python3 -m unittest quality_audit.test_quality_tools
D=m3_design/assembly_review/sources/r8_design
$PY -I $D/step9/m2_sweep.py m3_design/assembly_review/m3.kicad_pcb --json /tmp/m2.json
$PY -I $D/step7/make_ground.py m3_design/assembly_review/m3.kicad_pcb /tmp/g.tsv --built   # = r8_ground.tsv
DC_GND=0.1 tools/run_dc.sh m3_design/assembly_review/m3.kicad_pcb /tmp/dc 0.05
$D/step9/run_supply_dc.sh m3_design/assembly_review/m3.kicad_pcb /tmp/sup 0.1
NO_GATE=1 NO_DC=1 tools/run_survey.sh m3_design/assembly_review/m3.kicad_pcb /tmp/survey   # add dc_*.txt, then
python3 tools/scorecard.py /tmp/survey --baseline tools/scorecard_r7.json --md /tmp/survey/scorecard.md
$PY -I tools/reference_audit.py m3_design/assembly_review/m3.kicad_pcb [--extended]
$PY -I $D/step9/requalify.py <board> /tmp/req.json; $PY -I $D/step9/pyro_neighbours.py <board> /tmp/nb.json
$PY -I $D/step9/binding_note.py m3_design/assembly_review/m3.kicad_pcb $D/step9/r8_binding_note.json
```

A table change made after step 6 must be regenerated first: build to step 6 (the `r8_build.sh` stages up to `r8_route.py
links`), run `step7/make_ground.py` on that board into `r8_ground.tsv`, then build again (fix pass 4 did so; scratch
`fix4/stageA.sh`).

## Files changed by fix pass 4

Generators / tables: `m3_design/r8_route_rf.py`, `m3_design/r8_power.py`, `m3_design/r8_ground.tsv`,
`m3_design/r8_build.sh` (comment), `sources/r8_design/step7/make_ground.py`. Outputs: `m3.kicad_pcb`, `fab/` (Gerbers,
PDFs, manifest; BOM and CPL unchanged), `r8_top.png`, `r8_bottom.png`, `step9/r8_binding_note.json`,
`step9/evidence/fix4_*` (15 files). Records: `docs/R8_VALIDATION.md`, `docs/M3_R8.md`, `R8_DECISIONS.md`,
`docs/ORDERING.md`, `docs/REQUIREMENTS.md`, `docs/MARGIN_PRESCRIPTION.md`, `STATUS.md`, `AGENTS.md`, `README.md`,
`fix3_handoff.md` (R70 note); this folder's `fix4_*`.
