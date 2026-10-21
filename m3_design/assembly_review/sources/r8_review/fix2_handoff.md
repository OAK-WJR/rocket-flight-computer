# R8 fix pass 2: handoff

Fix pass 2 implements R8 review pass 2 (`pass2_*.md`, board `6600ef94…`: 0 Critical, 0 Major, 31 Minor) through the R8
generators, tables and tools only; `m3_design/r8_build.sh` reproduces the result. Nothing is committed (AGENTS: the owner
asks for commits). Log: `fix2_progress.md`. Decisions: `sources/r8_design/R8_DECISIONS.md` D97–D105 (and corrections to
D6.8, D85, D87, D89). Dispositions of all 31 findings: `docs/R8_VALIDATION.md` "Review pass 2". Every file this pass
changed is listed below; `fix2_baseline_sha256.txt` holds the SHA-256 of the 222 changed / untracked files it started
from, and `fix2_generators.diff` is its diff of the 13 code / table files against that state (R8P2-INTEGRITY-03: no
commit exists to diff against).

- **Final board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18`; netlist `0cc1ed69…` (unchanged). Two consecutive
  `r8_build.sh` runs (612 / 609 s) gave identical boards, netlists and all 15 sheets (17 files).
- **Gate:** `tools/check.sh` exit 0 in both builds and standalone: DRC 0 at every severity, unconnected 0, parity 0, ERC 0;
  audit OK; silk OK; `check_r8` OK; route_check r8 0 failing, 3 allowlisted, 0 leftovers; `check_actuators` OK; fit OK.
  Build DC gate (0.1 mm): RAW_ACT 5.90 mm / 17.6 °C, BAT_IN 6.85 / 14.8, ACT_FET_S 4.80 / 22.3. `make_ground.py --built`
  reproduces `r8_ground.tsv` (201 rows) byte for byte.
- **Tests:** 272 in 17 suites (KiCad Python) OK; quality_audit 21 under both Pythons OK. The new drain case kills the
  old-ARM_SIDE mutant.
- **Fab:** `m3_design/r8_fab.sh` exit 0: CHECK none; BOM `be711876…` (R7's); CPL `25cfed69…` (only R81's row changed);
  verify 85 + 126, worst 0.491 mm; paste check OK; manifest bound to `990c8040…`; renders regenerated. Cost / stock not
  re-run (no network): `cost_check.json` still binds the step-9 CPL; `FAB_NET=1 m3_design/r8_fab.sh` within 24 h of
  ordering.

## What changed, per item

| Item | Change | Result on `990c8040…` |
|---|---|---|
| PYRO-01 | `check_r8.ARM_SIDE` += PYRO1_OUT, docstring; `test_r8_check` drain case (D103) | nearest 1.089 mm; drain 3.562 mm |
| PYRO-02 | records: M3_R8 GND/drain text, pyro observations GND row; `make_ground` 1.0 mm option not applied (no gain: pour edge stays at rule D 0.5 mm) | GND vias 0.528 / 0.537 mm from drain copper (unchanged) |
| PYRO-03 | `binding_note.py` constraint (PE4 low / GPIOE reset first), note regenerated; D6.8; REQUIREMENTS F10 | — |
| REQUIREMENTS-01, ROUTING-03 | `m2_sweep.py` `adjacency_pad` (D104); C12 / C12b, part F, scope sentence; Q120.9 in the BAT_ENABLE row | 36 pad pairs (4 fine-pitch counted, 32 listed; R7 C15 #1 / #6 restored) |
| REQUIREMENTS-02 / -03 / -05 / -06 | R8_VALIDATION head and history row; D5 wording, D70 in the owner list; README coupler; MARGIN (4 over 0.5 A), AGENTS (24 h run), M2 pointer (C17), F8 battery_pyro, ORDERING 21.4 °C, STATUS dates / R7 ORDERING branch | — |
| REQUIREMENTS-04 | C19: per-category reasons; part-E search (`fix2_part_e.json`): no end centrable by a one-segment change | C2 93 → 90 |
| POWER-01 | ORDERING §5 stall test rewritten (D105); F4, M3_R8, MARGIN | — |
| POWER-02 | `r8_power.py` IN2_BAT_IN x ≤ 33.5, y ≤ 112.6 (D97); ORDERING §3 / §7 | In2 BAT_IN 505.6 → 229.6 mm²; right fwd tab and (42, 114.4) GND on 4 layers; BAT_IN 0.42 → 0.45 mΩ, neck 6.99 mm 14.5 °C |
| ROUTING-01 | `r8_power.py` SMALL_VIA for C75.2 / R78.2 / R72.2 GND vias and V_IN1 (same drill) (D98) [fix pass 3, R8P3-INTEGRITY-01: first written "C76.2"; C76.2's via stays 0.6 mm] | 0.150 mm pairs 14 → 10; pairs 32 → 29 |
| ROUTING-02 | **fixed differently**: the reviewer's r81w fails R5 L10 (J121.1); `r8_place.tsv` R81 (39.6, 91.275, 90, B), `r8_route_status.py` spine split + 0.82 mm stub (D100) | feed threads no part, ≥ 0.20 mm to other nets; R81.1–J121.1 1.825 mm bare |
| ROUTING-04 | **fixed differently**: C83 +0.175 fails L10 (J3.1), east overlaps U10, U10 aft hits V_D; `r8_route_usb_swd.py` link split into two straight tracks (D99) | C83.2 instances 3 → 1 (0.175 mm), no micro-segment |
| PLANES-01 | `make_ground.py` pad stage (IC GND pad > 4 mm copper → nearest legal spot) (D102); table regenerated | via (44.65, 86.775): U9.8 14.06 → 2.54 mm, R84.2 0.64, C81.2 3.51; U13.2 no spot |
| PLANES-02 | M3_R8 Ground | In1 90.50 %, 4 slots, 21 outer islands |
| DFM-01, INTEGRITY-01 | `r8_ground.py` `RELIEF_PADS` J123.2 before the fill; `make_ground` models it; `r8_pcb.py` comment; D89, C17, ORDERING §4 (D101) | B.Cu 2 spokes, F / In1 4; one new island via (13.5455, 74.2255); P3b 3 → 4 (≤ 4) |
| INTEGRITY-02 | `check_r8` docstring / comment, D87, hard-gate row | ViaCheck-rule pairs 13 (fix 1: 14; R7: 5) |
| INTEGRITY-05 | STATUS date; R8P1-RF-02 row; four fix1 evidence files re-run on `6600ef94…` (identical) and given `board_sha256` | — |
| Also (records) | RF-01 (1.22 mm partner, M3_R8 and route_check A3 reason text), POWER-05 (b) / (c), DFM-03 (a) / (b), POWER-03 line, PYRO-04 recorded | — |

## Scorecard (against fix pass 1; `fix2_scorecard.md`)

Index 15.3 (unchanged; quick 13.7). Targets 20 met / 11 missed (unchanged). Moved: C2 93 → 90; S1 1498.8 → 1499.6 mm;
S6 / S7 1.176 / 288.8 → 1.177 / 289.4 mm; S17 1638.7 → 1638.9; S18 794 → 795; P1 0.9054 → 0.905; P3 15 → 16; P3b 3 → 4;
P6 1782.9 → 1752.5 mm; P8 8.12 → 8.15; P9 4.48 → 4.47 mm; D_bat 0.42 → 0.45 mΩ (neck 7.00 → 6.99 mm). GND return
0.72 → 0.69 mΩ.

## Not done, and why

- **INTEGRITY-03 (commit / tag):** owner action; the brief said not to commit.
- **PYRO-02's optional 1.0 mm drain clearance for step-7 vias:** no gain while the pour edge stays at rule D's 0.5 mm.
- **Not fixed (reviewers: not worth fixing), recorded:** PYRO-04, POWER-03, POWER-04 / INTEGRITY-04 (DC-gate test), DFM-02.
- **Found while listing pads, recorded not fixed:** step 7 keeps 0.5 mm only from pyro / arming nets, so a GND via sits
  0.180 mm from bare R120.2 (ACT_GATE; a bridge turns the actuator switch on with the power switch open; ORDERING's
  "RAW_ACT dead with the switch open" step screens it); candidate for pass 3: give `make_ground.clearance` the actuator
  gate nets. [Fix pass 3, R8P3-PYRO-01 / PLANES-01 / DFM-01 / INTEGRITY-03 / REQUIREMENTS-02 / POWER-03: closed, no
  copper change. The GND pours stand at 0.150 mm from all five bare ACT_GATE / ACT_DRV pads (R120.2, C120.2 on B.Cu;
  R121.1, R121.2, Q122.3 on F.Cu), as on R7 (four pads); the tented via at 0.180 mm adds no closer approach, so the
  candidate would gain nothing. Screened by ORDERING §5's 20 power-switch cycles and the hot RAW_ACT check.] Other R8-new lane pairs in C12b (Q123.3 / PULLPIN, R166 / RAW_PROTECTED, R172 / USB_LIMITED, Q120.9 /
  BAT_ENABLE via) are "not removed yet".
- **Not re-run:** plate model and hot-plug script (numpy; only an 0603 moved); route_check `--profile r7` on R7 (only an r8
  allowlist reason string changed); live cost / stock (network).
- **Open:** review pass 3 on `990c8040…`, owner acceptance of the deviation list and its decisions, C10, U4 consignment,
  JLC tab acceptance, firmware binding, bench items.

## Reproduce

```
m3_design/r8_build.sh                       # twice; compare SHA-256 (990c8040…)
KICAD_PY=<KiCad python3> tools/check.sh
PY=<KiCad python3>; D=m3_design/assembly_review/sources/r8_design
$PY -I $D/step9/m2_sweep.py m3_design/assembly_review/m3.kicad_pcb --json /tmp/m2.json
$PY -I $D/step7/make_ground.py m3_design/assembly_review/m3.kicad_pcb /tmp/g.tsv --built   # = r8_ground.tsv
DC_GND=0.1 tools/run_dc.sh m3_design/assembly_review/m3.kicad_pcb /tmp/dc 0.05             # ~60 min with GND
NO_GATE=1 NO_DC=1 tools/run_survey.sh m3_design/assembly_review/m3.kicad_pcb /tmp/survey   # add dc_*.txt, then scorecard.py
m3_design/r8_fab.sh                         # before the tests: test_fab_validation judges the package against the board
(cd tools && for t in test_*.py; do $PY -m unittest ${t%.py}; done)
```

[Fix pass 3, R8P3-INTEGRITY-02: this block first listed the tests before `r8_fab.sh`; after a copper change that order
makes `test_fab_validation.test_current_package` fail on the stale CPL (fix pass 2's only test log shows that failure; a
run after the fab step passes).]

## Files changed by fix pass 2

Generators / tables / tools: `m3_design/r8_power.py`, `r8_place.tsv`, `r8_route_status.py`, `r8_route_usb_swd.py`,
`r8_ground.py`, `r8_ground.tsv`, `r8_pcb.py` (comment), `sources/r8_design/step7/make_ground.py`,
`step9/m2_sweep.py`, `step9/binding_note.py`, `tools/check_r8.py`, `tools/test_r8_check.py`, `tools/route_check.py`
(A3 reason text). Outputs: `m3.kicad_pcb`, `fab/` (CPL, Gerbers, PDFs, manifest), `r8_top.png`, `r8_bottom.png`,
`step9/r8_binding_note.json`, `step9/evidence/fix2_*` (15 files) and the four `fix1_*` files given `board_sha256`.
Records: `docs/R8_VALIDATION.md`, `docs/M3_R8.md`, `R8_DECISIONS.md`, `docs/ORDERING.md`, `docs/REQUIREMENTS.md`,
`docs/MARGIN_PRESCRIPTION.md`, `STATUS.md`, `AGENTS.md`, `README.md`; this folder's `fix2_*`.
