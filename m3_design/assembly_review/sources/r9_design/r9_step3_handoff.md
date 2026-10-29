# R9 step 3 (placement freeze): handoff

Step 3 of `r9_plan.md` §4. The R9 placement is frozen in `m3_design/r9_place.tsv` and built by `m3_design/r9_build.sh`
into `m3_design/assembly_review/m3.kicad_pcb` (placement only: no track, via or pour; SHA-256 `349c1477…`). The step
gate passes in full. The board is **46 × 102 mm**: 98 mm could not legalise the four MCU-end interface resistors, so
the plan's kill path (100, then 102 mm; owner decision 1) applies (D-S3-03). (Corrected by R9 review pass 1,
R9P1-REQUIREMENTS-01: the kill path held the resistors to r9_plan §2's hard row X9 ≥ 5.94 mm from U1 / U3 / Y1, R8's
measured R306–U1 distance, not to F10's 5 mm; with F10's 5.0 mm it holds at 100 mm, total detour 6.96 mm, and 98 mm
still fails. The owner's options are in R9_VALIDATION C1.) Nothing committed or pushed. Decisions:
`R9_DECISIONS.md` D-S3-01 … D-S3-11. Log: `r9_step3_progress.md`. Evidence: `step3_evidence/`.

## 1. What was produced

| File | What it is |
|---|---|
| `m3_design/r9_legalise.py` | The R9 placement legaliser (R8's generalised to the R9 contract, D-S3-01) and `block_area` (PYRO_BLOCK by content, D-S3-02); `check`, `propose` |
| `m3_design/r9_pcb.py` | The builder: R8's board (SHA asserted) → variants in place, overrides cleared, netlist assert (761 pads, 0 changed), clean sheet (sensor / Y1 rule areas, PYRO_BLOCK and ARM / IGN legends kept), outline / supports / tie holes from the '@' rows, every part from the table, PYRO_BLOCK derived, title, native fill, save. Refuses any legaliser violation (`--propose OUT.tsv`, `--draft`, `--out` are design aids) |
| `m3_design/r9_place.tsv` | The frozen placement: '@' rows (46 × 102 outline; supports (4, 4), (42, 4), (4, 98), (42, 98), (42, 59.5); tie holes (16, 62), (29.9, 59)) and all 249 parts, each with its basis |
| `m3_design/r9_place_check.py` | The step gate (D-S3-09) |
| `m3_design/r9_kill_path.py` | Kill-path record (not in the build): rebuilds the table at other lengths and searches clean spots for R306 / R315 / R310 / R313 |
| `m3_design/r9_build.sh` | Step-3 stages appended: R8's board restored from git, `r9_pcb.py`, `r9_place_check.py --numpy-py "$NUMPY_PY"` |
| `tools/test_r9_place.py` | 18 tests: table = board, outline / supports / ties from the table, built board legal, PYRO_BLOCK = `block_area`, bad tables refused, and one seeded defect per rule (courtyard, outline, R-1 both clauses, R-10, GS strict pad rule, M-5 support floor, M-3 tie path, M-6 THT keep-out, P-10 coat region, M-4 J1 corridor, rule clearances incl. G's scope, RAW_ACT PTH 0.3, test pads 1.0) |
| `tools/r8_record.py` + six R8-era suites | `board()` gives R8's committed project when the worktree board is R9's (D-S3-11): test_r8_place, test_r8_power, test_r8_ground, test_r8_route, test_reference_audit, test_fab_validation |
| `step3_evidence/` | `r9_place_check.{txt,json}` (gate on the built board), `check_r9_placement.{txt,json}` (full check_r9: what remains for later steps), `kill_path.{txt,json}`, `option_98mm_f10.txt`, `gate_negative.txt`, `tests.txt` |

## 2. Verification (r9_plan §4 step 3)

| Item | Result on the built board (`step3_evidence/r9_place_check.json`) |
|---|---|
| 0 legaliser violations, 249 parts | 0 (gate legaliser, y_f 22.0, F10 as written) |
| DRC + parity | 0 violations, 0 parity items; 499 unconnected (nothing routed) and step 8's silkscreen classes (5 / 78 / 128) deferred |
| fit | clean; M-5 floors held (minimum J9 mated 0.028 = R8's floor; bottom 2.357; supports 4.465 bottom / 5.008 top) |
| plate model | f1 252.1 Hz (hard ≥ 209; done ≥ 241) |
| F9 input protection | D8 5.22, C96 5.72, C80 8.90, C89 4.79, C95 4.69, R166 8.38, R167 5.59 mm (≤ 10.6); U9 12.8 mm (≤ 27.07) |
| F10 5 mm separations | nearest RF part 6.24 mm (R310–U1, ≥ 5.94); nearest fast-net pad 5.197 mm (R306–USB_DM, ≥ 5.0) |
| strict pad rules | margins H 0.225, H+ 0.025, GS 0.151, AG 0.162, A 0.767, C 0.609 mm; P-5 135 pairs, none forbidden; P-6 nearest 1.019 mm |
| J1 ≤ 25 mm from both CH1 terminals | 23.33 (J121), 14.72 (J124) mm; entry +y |
| tab windows | west 0.5–7.25, 12.0–26.75, 55.75–101.5; east 0.5–27.0, 95.5–101.5 (both end thirds of both edges) |
| MST ≤ 1639 mm | 1468.0 mm |
| check_r9 placement rules, check_actuators, rule areas | OK (R-1 deepest strip courtyard 21.955 mm; R-11; R-12 C301 2.13 / C300 2.556 mm; P-10 U4 5.526 mm; P-11 wire room 6.353 mm; 15b passes on the derived block) |
| Kill path | 98 mm none, 100 mm none, 101 mm holds, 102 mm holds (`kill_path.txt`; D-S3-03) |
| Gate fires | a copy with C301 at y 22.4 and R310 beside U1 fails legaliser, f10 and contract (R-1, R-12) (`gate_negative.txt`) |
| Reproducible | `r9_build.sh` twice: board, sheets, netlist, DRU and variant files byte-identical |
| Tool tests | 20 tool suites, 362 tests, all OK; quality_audit 21 OK under both pythons (`tests.txt`); the six R8-era suites run on R8's committed board |

Full check_r9 on the board (`check_r9_placement.txt`) fails only later-step rules: R-2, R-4…R-9 (RF pours, launches,
lines, fences, keep-out areas: step 4), K-contract's three route-only items (C29, C100, C93 direct routes), K-legends
(step 8), P-4 / M-2 (seeded suite and plate report not passed to that run; the step gate runs the plate model).

## 3. Reproduce

```bash
R=rocket-pcb/rocket-flight-computer-r9                         # this worktree
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
NUMPY_PY=/path/to/python3-with-numpy $R/m3_design/r9_build.sh  # steps 2 + 3, gates included (about 30 s)
(cd $R && PYTHONUNBUFFERED=1 $KP -I -B m3_design/r9_place_check.py --numpy-py /path/to/python3-with-numpy --report out.json)
(cd $R && PYTHONUNBUFFERED=1 $KP -I -B m3_design/r9_kill_path.py --lengths 98 100 101 102)   # about 1 min
cd $R/tools && for t in test_*.py; do $KP -B -m unittest "${t%.py}"; done                    # about 5 min
```

## 4. What the next steps must know

- **Length 102 mm.** Everything forward of the RF strip is the 98 mm design moved 4 mm forward; the gap band between
  the strip and the forward block (y ≈ 22–28) is wider than planned and holds the four MCU-end resistors. Done row
  X1 ≤ 100 is missed; the owner may take back 98 mm by reclassifying R306 / R310 / R313 / R315 out of F10's RF-part
  list (measured: the only 98 mm violations are R-10 between them and U1 / U3 / U7 / C76; `option_98mm_f10.txt`).
- **Step 4 (RF).** U30 is at (11.15, 14.05), 0.74 mm east and 0.9 mm aft of R8; J30, the GNSS chain and limiter stay
  R8's, so the module segment R304.2 → U30.11 needs a 0.74 mm jog (moving J30 / chain east breaks R-11, 14.71 mm).
  The GNSS row forward of U30 is planar in pin order: TXD through R305, RXD between R305 and R307, TIMEPULSE through
  R307, 3V3_GNSS (C300 → U30.7, C301 ↔ U30.8, FB30 → C301.1), RESET_N east under FB30 then forward. The LNA_EN /
  VCC_RF escape vias go in the 1.0 mm between U30's aft pads (y 8.4) and C303's pads (y 7.4) (Inference: 0.45 mm vias
  with 0.275 mm clearances). FB31 is rot 0 at (34.4, 20.95); DIO1 / TXEN leave U31's forward pins west of it. The
  U30_KEEPOUT / U31_KEEPOUT rule areas are gone (clean sheet): step 4 regenerates them (R-2 / R-8 require them).
- **Interface lanes (step 7).** R306 (16.5, 29.2), R315 (20.7, 28.8), R310 (21.7, 28.8), R313 (23.3, 29.2), all top,
  pad 1 toward U1: lanes in pin order west to east (GNSS RXD, MOSI, NSS, SCK) need no crossing.
- **Supports.** The mid support (42, 59.5) is owner decision 5's (42, 55.5) moved with the forward block; the DC solve
  that decision depends on is step 6's (else (4, 49.5) + 4 mm, re-run the plate model).
- **Thin margins to keep.** H+ 0.025 mm (pyro strict pad rule), fit J9 mated 0.028 mm (R8's floor), R-12 C301
  2.13 / 2.18 mm, R-1 C300 21.955 / 22.0 mm, U30.18 5.012 / 5.008 mm, SERIES R313 0.36 mm.
- **Tests.** R8-era suites now run on R8's committed project (`tools/r8_record.py`); `test_r9_place` needs the built
  R9 board (skips otherwise). `tools/check.sh` on the worktree fails at stage 1 (unrouted) until the board is routed.

## 5. Open

- Owner option, not a blocker: F10 reclassification of the four MCU-end resistors → 98 mm (D-S3-03); review pass 1
  added the second, 100 mm with the four at 5.0–5.94 mm from U1 (a relaxed hard row X9, F10 still met;
  R9_VALIDATION C1).
- STATUS.md and the R9 records are step 10's.
- Minor: the mid-support position assumes step 6's DC solve holds (owner decision 5's fallback re-runs the plate
  model).
