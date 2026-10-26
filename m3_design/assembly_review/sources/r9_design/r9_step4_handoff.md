# R9 step 4 (RF strip): handoff

Step 4 of `r9_plan.md` §4. The RF strip copper is built by `m3_design/r9_rf.py` on the step-3 placement and gated by
`m3_design/r9_rf_check.py`; both run in `m3_design/r9_build.sh`. The built board (`m3_design/assembly_review/
m3.kicad_pcb`, SHA-256 `50a5af67…`, `step4_evidence/build_sha256.txt`) reproduces byte for byte. The step gate passes
in full. Nothing committed or pushed. Decisions: `R9_DECISIONS.md` D-S4-01 … D-S4-08. Log: `r9_step4_progress.md`.
Evidence: `step4_evidence/`.

## 1. What was produced

| File | What it is |
|---|---|
| `m3_design/r9_rf.py` | The builder. Tables in part frames: `PARTS` (every strip part's position in its jack's or module's frame, asserted against the board), the RF chains and launches in J30's / J31's frames (R7's geometry, `R7_LAUNCH_VIAS`), U30's and U31's own copper and the limiter in the module frames, GND vias (`GND_JACK`, `GND_MODULE`, the fence `FENCE_X` at `FENCE_Y` 22.2 and the grid `GRID`), the U30 / U31 keep-outs derived with `check_r9.module_regions`, the In1 launch cut-outs, the strip pours on four layers to y 23.0. `R7_DEVIATIONS`, `CORRIDORS`, `strip_nets()`, `corridor_boxes()`. `--no-board-vias` (design aid) |
| `m3_design/r9_rf_check.py` | The step gate: frames, r7, launch, contract (check_r9 R-1 … R-13, LC-1, K-copper), gcpw, route, drc, corridors (§2) |
| `m3_design/r9_place.tsv` | 28 strip rows changed (each basis names its D-S4 decision): J30, D30, L30, C302, C303, R304, C305; the limiter R300-R303, Q30-Q32, C304; the radio group U31, J31, D31, R316, C313, C314, C310-C312, R311, R312, R314, FB31 (+0.75 mm east) |
| `m3_design/r9_build.sh` | Step-4 stages appended: `r9_rf.py`, `r9_rf_check.py` |
| `m3_design/r9_rf_aid.py` | Design aid, not in the build: proposes the fence and the stitching grid on a board built with `r9_rf.py --no-board-vias`; with `2.5 3.6 3 rect 0.45` it reproduces the frozen `FENCE_X` / `GRID` exactly (checked) |
| `tools/test_r9_rf.py` | 16 tests: frames hold; a moved chain part, a jack off its module pin, an undeclared chain change, a stale deviation, an extra launch via, foreign copper in a launch, a corridor via, a missing stitch are each caught; GCPW judging; line samples on both chains; B.Cu may cross a corridor; drawn nets = strip nets; contract rules hold |
| `step4_evidence/` | `r9_rf_check.{txt,json}` (gate on the built board), `check_r9_full.{txt,json}` (the whole contract: what remains for later steps), `tests.txt`, `build_sha256.txt` |

## 2. Verification (r9_plan §4 step 4)

| Item | Result on the built board (`step4_evidence/r9_rf_check.json`) |
|---|---|
| R-1 … R-13 of check_r9 | all OK (plus LC-1, K-copper). R-1 deepest strip courtyard 21.955 (C300); R-2 TXEN B.Cu 22.719 mm (R8 22.72); R-6 GNSS 4.85 mm / 2 bends, radio 4.75 / 2; R-7 side gaps GNSS 2.38 / 1.75, radio 1.70 / 2.41 mm (<= 2.5), fence 23 vias, reach F.Cu 3.10 / B.Cu 3.57 mm (<= 4.0), RF ground vias <= 0.23 mm; R-9 ESD 0.795 mm, C302 0.925, stubs 0.94; R-10 6.24 / 5.197 mm; R-11 RF-RF 15.46 mm (R7 15.45), radio SPI 6.84 mm from U30's body, courtyards 7.67; R-12 C311 1.97, C312 2.191, C310 3.639, C301 2.13, C300 2.556 mm, GNSS VCC 0.088 ohm; R-13 46.13 mm |
| Launch congruent with R7 in each jack's frame | R-4 OK (via offsets <= 0.02 mm: R7's built 3.58); gate `launch`: the eight vias, R7's 0.6 / 0.3 size, no foreign copper, In1 cut-out, F.Cu GND copper in the window = R7's J31 to 0.0008 mm2 for both jacks, J30 = J31 exactly |
| GCPW 50 +- 2.5 ohm at every sample (gcpw_solve) | 79 R-5 line samples (GNSS 30, radio 49), gap pairs 0.26-0.32 mm, Z0 50.16-51.08 ohm (coated, over In1) |
| No allowlist entry (no A2 / A3 detours) | route_check profile r9: 0 failing, 0 unrecorded leftovers, 13 information instances (in-pad final segments at C300.1, C310.1, TP30; lines through D30.1 / D31.1; the TXEN u-turn; one width change at a T: R7 / R8 precedents) |
| Chains congruent with R7 | gate `r7`: every chain part at R7's position in its jack frame but D30 (turned) and C303 (moved), the recorded deviations (D-S4-02); the radio chain exactly R7's |
| DRC + parity | 0 violations but step 8's silkscreen classes, 0 parity, no unconnected item on a strip net or between strip GND items (482 unconnected elsewhere: nothing else routed) |
| Corridors | no F.Cu copper or via of this step in a step-7 lane corridor (the fence row excepted, D-S4-05) |
| Step-3 gate on the edited placement | OK in the build (legaliser, DRC, fit, plate f1 252.3 Hz, F9, F10, pyro pads, J1, tabs, MST 1465.1 mm, contract, actuators, areas) |
| Reproducible | `r9_build.sh` twice: board, sheets, netlist, DRU and variant files byte-identical |
| Tool tests | 21 suites, 378 tests, all OK (`step4_evidence/tests.txt`; test_r9_rf 16, the rest unchanged) |

## 3. Reproduce

```bash
R=rocket-pcb/rocket-flight-computer-r9                                   # this worktree
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
NUMPY_PY=/path/to/python3-with-numpy $R/m3_design/r9_build.sh            # steps 2-4 and their gates (about 1 min)
(cd $R && PYTHONUNBUFFERED=1 $KP -I -B m3_design/r9_rf_check.py --report out.json)                 # about 35 s
(cd $R/tools && $KP -B -m unittest test_r9_rf)                                                     # about 17 s
(cd $R && PYTHONUNBUFFERED=1 $KP -I -B tools/check_r9.py m3_design/assembly_review/m3.kicad_pcb --only R-1,R-2,R-3,R-4,R-5,R-6,R-7,R-8,R-9,R-10,R-11,R-12,R-13)
```
(The parent project's `cfd/venv/bin/python3` has numpy.)

## 4. What the next steps must know

- **Placement changed in the strip** (D-S4-01 … 03): J30 is at x 13.59, J31 at 32.29; U31 at (30.61, 14.0); the
  limiter is re-placed under U30's aft half. Everything else is step 3's.
- **Ownership** (D-S4-05): step 4 drew only the strip-internal nets (`r9_rf.strip_nets`, asserted). Step 7 (rf_if)
  draws the nets that cross y_f: GNSS_TXD_MCU (from R305.2), GNSS_RXD (to U30.3 between R305.1 and R307.2: the gap is
  x 8.13-8.81 at the row, so the lane jogs 0.48 mm to U30.3 below the row), GNSS_TP_MCU (from R307.2), GNSS_RESET_N
  (U30.9, east under FB30 at y ~20.46, then north), the 3V3 feeds of FB30.1 (16.66, 21.06) and FB31.1 (34.5, 20.95),
  and the radio lanes (R312.1 / U31.10 for RXEN, U31.11 BUSY, R314.2 MISO_MCU, U31.13-15 MOSI / NSS / SCK, U31.20
  DIO1, R311.1 / U31.3 NRST). `r9_rf.CORRIDORS` are kept free for those lanes (Inference: R8's radio lanes translated
  +0.75 mm lie inside them; not drawn here). The radio interface copper must stay >= 5.0 mm (SPI 6.0) from U30's body box x 6.1-16.2 (R-11).
- **The fence** (`r9_rf.FENCE_X`, y 22.2) is complete now (R-7 needs it without lanes). Step 7 opens a gap where its
  lanes cross: each opening <= 2.7 mm and crossed by a lane, the rest <= 2.0 mm (R-7). Edit `FENCE_X` in r9_rf.py
  and re-run r9_rf_check (the gate re-measures).
- **Grid vias** (`r9_rf.GRID`) avoid the corridors. If a lane needs a grid via moved, move it in the table and re-run
  the gate (R-7 reach <= 4.0 mm, corridors); `m3_design/r9_rf_aid.py` can re-propose the grid around new copper (the
  frozen table stays the source).
- **Pours** (D-S4-07): R9_GND_F_strip / _B_ / _In1_ / _In2_strip end at y 23.0. Step 8 extends F.Cu, B.Cu and In1
  over the board (replace or add board-wide GND pours with the same settings); step 6 owns In2 forward of y 23.0 and
  must keep In2 GND-only below y_f (R-2).
- **Silkscreen** (step 8): "GNSS" beside J30 and "RADIO" beside J31 (K-legends fails them now).
- **Records** (step 10): F10's strip text (y 0-22.0; the quoted stitching gaps 2.38 / 1.75 GNSS, 1.70 / 2.41 radio
  along the path), ORDERING §4's bench-tuning note (C303 now sits at the bias node, before R304; the stubs are still
  0.94 mm), §5's RF coordinates (jacks x 13.59 / 32.29), M3_R7's limiter thermal note (Q30 drain lead 0.40 mm, D-S4-03).
- **SWIG** (step 1's note) still applies: the gate keeps R7's board alive next to the checked one.

## 5. Open

- No question for the owner arises from step 4. Not unsafe; no requirement's intent changes (F10's limiter stays on
  B.Cu under U30; y_f is the owner's 22.0).
- The R-7 margins are thin: GNSS east 2.38 mm and radio west 2.41 mm against 2.5 (corrected by R9 review pass 1, R9P1-RF-02: the radio's 2.405 mm gap is on the west side, ending at U31.7; check_r9 R-7 now names the sides) (the chain rows are courtyard-packed
  under U30's aft pads, D-S4-02). A later move of U30, the jacks or the chain parts must re-run the gate.
- Inference items, not re-solved here: Q30's junction temperature with the new copper (R7's bound kept, D-S4-03); the
  return-loss cascade of pass2_rf §3.12 for the GNSS chain with C303 at the bias node (same elements and stubs,
  about 3 degrees of line moved, D-S4-02). Both are for the RF / power review of r9_plan §5.
- Minor: a GND via under Q30's body (11.3, 10.66) closes the limiter's B.Cu pocket (tented, between pads); the
  scratch boards were deleted.
