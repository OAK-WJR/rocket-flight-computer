# R8 fix pass 3: handoff

Fix pass 3 implements R8 review pass 3 (`pass3_*.md`, board `990c8040…`: 0 Critical, 0 Major, 26 Minor) through the R8
generators, tables and tools only; `m3_design/r8_build.sh` reproduces the result. Nothing is committed (AGENTS: the owner
asks for commits; R8P3-INTEGRITY-04). Log: `fix3_progress.md`. Decisions: `sources/r8_design/R8_DECISIONS.md` D106–D109
(and corrections to D6.8, D76, D87, D97, D98, D105). Dispositions of all 26 findings: `docs/R8_VALIDATION.md` "Review
pass 3". `fix3_baseline_sha256.txt` holds the SHA-256 of the 248 changed / untracked files fix pass 3 started from (the
coordinator also kept a backup of the `990c8040…` state in the session scratchpad, `r8_backup_990c8040/`), and
`fix3_generators.diff` is the diff of the 11 code / table files fix pass 3 changed.

**Passes 2 and 3 are two consecutive review passes with no Critical or Major** (r8_plan §4, REQUIREMENTS "R8
acceptance"). Fix pass 3's three copper edits are the pass-3 routing reviewer's own trialled variants; the final board has
not itself been reviewed, so a re-check (review pass 4 on `c84f00b8…`) is offered as the owner's call.

- **Final board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54`; netlist `0cc1ed69…` (unchanged). Two consecutive
  `r8_build.sh` runs (611 / 769 s, the second sharing the CPU with the DC solves) gave identical boards, netlists and all
  15 sheets (17 files); a third run (609 s) on the final generator state (after a comment-only edit: R172's basis column
  in `r8_place.tsv`, which no stage reads) gave the same 17 files, and the fab manifest still verifies.
- **Gate:** `tools/check.sh` exit 0 in both builds and standalone: DRC 0 at every severity, unconnected 0, parity 0, ERC 0;
  audit OK; silk OK; `check_r8` OK (report equal to fix pass 2's but the board SHA); route_check r8 0 failing, 3
  allowlisted, 0 leftovers, 0 removable (22 bump windows); `check_actuators` OK; fit OK. Every step gate OK (the camera
  family's ratio budget tightened 1.55 → 1.40, worst 1.375; `L10_EXCEPT` R172 re-measured 0.635 → 0.685 mm). Build DC gate
  (0.1 mm): RAW_ACT 5.90 mm / 17.6 °C, BAT_IN 6.85 / 14.8, ACT_FET_S 4.80 / 22.3. `make_ground.py --built` reproduces the
  regenerated `r8_ground.tsv` (201 rows) byte for byte. route_check `--profile r7` on R7 (with its project files) OK.
- **Tests:** 272 in 17 suites (KiCad Python) OK, run after `r8_fab.sh` (`step9/evidence/fix3_tests.txt`);
  quality_audit 21 under both Pythons OK.
- **Fab:** `m3_design/r8_fab.sh` exit 0: CHECK none; BOM `be711876…` (R7's); CPL `ef90bfa1…` (only R172's row changed
  from `25cfed69…`; the bottom silkscreen changed too: `r8_post.py` re-placed R70's designator by (+0.104, −0.173) mm,
  still nearer its own part, every silkscreen gate holding; recorded after review pass 4, R8P4-DFM-02); verify 85 + 126, worst 0.491 mm; paste check OK (`tools/paste_check.py` standalone too); manifest
  bound to `c84f00b8…`; renders regenerated. Cost / stock not re-run (no network): `cost_check.json` still binds the
  step-9 CPL; `FAB_NET=1 m3_design/r8_fab.sh` within 24 h of ordering.
- **DC (0.05 mm, `step9/evidence/fix3_dc_*.txt`):** RAW_ACT 1.45 mΩ, 5.94 mm, 17.5 °C; BAT_IN 0.45 mΩ, 6.99 mm, 14.5 °C;
  ACT_FET_S 0.18 mΩ, 4.97 mm, 21.4 °C; vias 0.86 / 0.65 A: all equal to fix pass 2's. Servo GND return (DC_GND 0.1):
  0.69 mΩ, its largest vias 0.26 / 0.24 A: equal to fix pass 2's. Supply paths (0.1 mm): USB_LIMITED 52.61 → 52.62 mΩ; the four BAT_IN rows equal; the rest untouched.
- **reference_audit:** 11.07 % / 5.81 %, sample for sample equal to fix pass 2's. requalify and pyro_neighbours equal
  (one exit's nearest-net coordinate moved with USB_LIMITED).

## What changed, per item

| Item | Change | Result on `c84f00b8…` |
|---|---|---|
| ROUTING-01 | `r8_power.py` USB_LIMITED trunk y 37.25 → 37.3 (corner, TP82 tap); `r8_place.tsv` R172 x 30.65; `r8_route_pyro.py` lane / stub / pad table; `r8_route_check.L10_EXCEPT` R172 0.685 (D106) | CAM_PWR_EN–USB_LIMITED 0.150 → 0.200 mm; R172.1 / .2–USB_LIMITED 0.180 → 0.230 mm; no new pair under 0.2 mm |
| ROUTING-02 | `r8_route_status.py`: R165's BAT_ENABLE via in `SIGNAL_VIAS` (0.5 / 0.3 mm) (D108) | Q120.9–BAT_ENABLE 0.180 → 0.23 mm; BAT_ENABLE–BAT_IN minimum 0.200 mm at U9.1 (pin pitch); ViaCheck list 13 → 12 pairs (11 vias) |
| ROUTING-03 | `r8_route_camera.py` CAM_PWR_EN (28.25, 36.8) → (28.25, 30.025) → R74.1; budget ratio 1.40; `m2_sweep.py margin_free` (bump / redraw search at DRC's threshold) (D107) | C11 run 22.12 → 20.15 mm (excess 6.18 → 4.20), route ratio 1.50 → 1.38; margin_free finds only part F's BAT_ENABLE false positive and C11's four "found"; step 7 moved one cover via |
| PYRO-01, PLANES-01, DFM-01, INTEGRITY-03, REQUIREMENTS-02, POWER-03 | records (D109): C12b R120.2 / J1.4 rows, the note under C12b, pyro observations ACT_GATE row, M3_R8, open items, `fix2_handoff.md`; no copper | pour 0.151 mm from R120.2, C120.2, R121.1, R121.2, Q122.3, J1.4, J123.1 (measured); candidate closed; GND-to-gate zone rule left as an owner option |
| PYRO-02 | GND row and closing sentence of the pyro observations, M3_R8 | R81.2–J121.1 1.825 mm (measured) |
| PLANES-02 | P3b row names the four In1 slots | — |
| RF-01 | `binding_note.py` (note regenerated on `c84f00b8…`), D6.8, F10, M3_R8, ORDERING §5: PE4 low; SX1262 asleep and PE9 low; GPIOE reset last | — |
| RF-02 | ORDERING §5 coexistence: 1175.000 MHz near L5, C/N0 per signal (UBX-NAV-SIG); M3_R8 RF | — |
| RF-03, INTEGRITY-01 | C76.2 → R78.2 in D98, D87's correction, `r8_power.py` comments, `fix2_handoff.md`, `fix2_progress.md` | — |
| DFM-02 | recorded (hard-gate row, D87, part of open items); gate unchanged, ratchet not added | 12 own-net tented pairs, worst 0.025 mm |
| DFM-03 | recorded as C20 (M2 silkscreen deviation) | dot overlap 0.012 mm² (measured) |
| INTEGRITY-02 | reproduce order (`r8_fab.sh` before the tests) in `fix2_handoff.md` and below; `test_fab_validation` docstring; `fix3_tests.txt` | — |
| REQUIREMENTS-01 | ORDERING §5: TP122 below 0.1 V and the static gate in the bootloader; CAM_5V at J9.1 under a 0.1 → 1 A step; IMU / lever-arm signs | — |
| REQUIREMENTS-03 / -04 | D51 in the owner summary; C12 #13 wording; REQUIREMENTS M3 names the step-9 CPL binding | — |
| POWER-01 | ORDERING §5 stall test: neck read at y 83.35–86.25 (≥ 3 mm from J122's pads, measured y ≤ 80.31), J122 recorded, the load wired by crimped plugs; D105 correction; M3_R8 | — |
| POWER-02 | M3_R8 single points: U11's IN1 via (35.25, 60.5) and the 3V3A hop pair | — |
| POWER-04 | F9 pad edges 1.9–7.8 mm (re-measured: R167 1.905 … C96 7.817) in M3_R8, D76, R8_VALIDATION, STATUS; `hotplug_feed.py` docstring | — |
| POWER-05 | ORDERING §3: In2 3V3 under the left middle tab | — |
| Also | D97 wording (B.Cu BAT_IN pour reaches x 41.3), C12b reasons for #3 / #11 / #12, an owner-summary count of "not removed yet" items | — |
| (rebuild side effect) | R70's designator re-placed by `r8_post.py` (0.2 mm), bottom silkscreen only (noted after review pass 4, R8P4-DFM-02) | ink 0.175 mm from R70's courtyard (was 0.003), 0.376 mm from C70's (was 0.549); every silkscreen gate holds |

## Scorecard (against fix pass 2; `step9/evidence/fix3_scorecard.md`)

Index 15.3 (unchanged; quick 13.7). Targets 20 met / 11 missed (unchanged). Moved: S1 1499.6 → 1497.6 mm; S2 2090.8 →
2088.8 mm; S6 / S7 1.177 / 289.4 → 1.175 / 287.4 mm; S10 1.540 → 1.542 bends / 10 mm; P1 0.905 → 0.9051; P6 1752.5 →
1752.2 mm. Every other row (C, R, D, Q, the rest of S and P) equal. M2 sweep: chain detours 23; track / via pairs under
0.2 mm 29 → 28 (0.150 mm 10 → 9); pad rows 36 → 33 (32 → 29 listed); routes 28; folds 26.

## Not done, and why

- **INTEGRITY-04 (commit / tag):** owner action; the brief said not to commit.
- **Not applied (reviewers: not worth fixing):** DFM-02's optional `via_paste` ratchet; DFM-03's R162 move (re-opens the
  buzzer group's routing and step 7 for a clipped cosmetic dot; recorded as C20); the routing reviewer's R166 0.025 mm
  move (clean, but the GND pour stays 0.151 mm from R166.1) and the R120.2 via move (no gain, D109).
- **Not re-run:** plate model and hot-plug script (numpy; only an 0402, R172, moved 0.05 mm and a docstring changed; "an 0603" corrected after review pass 4, R8P4-DFM-01: the plate model carries every part as a model-box-volume mass, and R172's 0.5 mg is what makes the move immaterial; R8 pass 3 DFM on `990c8040…` and pass 4 DFM on `c84f00b8…` re-ran it, every value equal to `plate_r8.json` but the board SHA); the 3V3 /
  RAW_ACT / RAW_PROTECTED / VLOGIC / CAM_5V supply rows (copper untouched); live cost / stock (network).
- **Open:** the owner's acceptance of the deviation list and its decisions, an optional review pass 4 on `c84f00b8…`,
  C10, U4 consignment, JLC tab acceptance, firmware binding, bench items.

## Reproduce

```
m3_design/r8_build.sh                       # twice; compare SHA-256 (c84f00b8…)
KICAD_PY=<KiCad python3> tools/check.sh
m3_design/r8_fab.sh                         # before the tests: test_fab_validation judges the package against the board
PY=<KiCad python3>; (cd tools && for t in test_*.py; do $PY -m unittest ${t%.py}; done)
$PY -m unittest quality_audit.test_quality_tools; python3 -m unittest quality_audit.test_quality_tools
D=m3_design/assembly_review/sources/r8_design
$PY -I $D/step9/m2_sweep.py m3_design/assembly_review/m3.kicad_pcb --json /tmp/m2.json       # incl. margin_free
$PY -I $D/step7/make_ground.py m3_design/assembly_review/m3.kicad_pcb /tmp/g.tsv --built   # = r8_ground.tsv
DC_GND=0.1 tools/run_dc.sh m3_design/assembly_review/m3.kicad_pcb /tmp/dc 0.05             # ~60 min with GND
NO_GATE=1 NO_DC=1 tools/run_survey.sh m3_design/assembly_review/m3.kicad_pcb /tmp/survey   # add dc_*.txt, then
python3 tools/scorecard.py /tmp/survey --baseline tools/scorecard_r7.json --md /tmp/survey/scorecard.md
$PY -I tools/reference_audit.py m3_design/assembly_review/m3.kicad_pcb [--extended]
$PY -I $D/step9/requalify.py <board> /tmp/req.json; $PY -I $D/step9/pyro_neighbours.py <board> /tmp/nb.json
$PY -I $D/step9/binding_note.py m3_design/assembly_review/m3.kicad_pcb $D/step9/r8_binding_note.json
```

A table change made after step 6 must be regenerated first: build to step 6 (the `r8_build.sh` stages up to `r8_route.py
links`), run `step7/make_ground.py` on that board into `r8_ground.tsv`, then build again (fix pass 3 did so; scratch
`fix3/stageA.sh`).

## Files changed by fix pass 3

Generators / tables / tools: `m3_design/r8_power.py`, `r8_place.tsv`, `r8_route_pyro.py`, `r8_route_camera.py`,
`r8_route_status.py`, `r8_route_check.py`, `r8_ground.tsv`, `sources/r8_design/step9/m2_sweep.py`,
`step9/binding_note.py`, `step9/hotplug_feed.py` (docstring), `tools/test_fab_validation.py` (docstring). Outputs:
`m3.kicad_pcb`, `fab/` (CPL, Gerbers, PDFs, manifest), `r8_top.png`, `r8_bottom.png`, `step9/r8_binding_note.json`,
`step9/evidence/fix3_*` (15 files). Records: `docs/R8_VALIDATION.md`, `docs/M3_R8.md`, `R8_DECISIONS.md`,
`docs/ORDERING.md`, `docs/REQUIREMENTS.md`, `docs/MARGIN_PRESCRIPTION.md`, `STATUS.md`, `AGENTS.md`, `README.md`,
`fix2_handoff.md` / `fix2_progress.md` (marked corrections); this folder's `fix3_*`.
