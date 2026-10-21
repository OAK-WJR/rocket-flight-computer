# R8 review pass 4: DFM, fit and mechanical (independent review)

This is a read-only review, done 2026-10-20, of the R8 board after fix pass 3. The worktree is
`rocket-flight-computer-r8`, branch `m3-assy-r8`, uncommitted, on top of R7 `431025d`.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54`. I checked the hash before and after the runs; it
  did not change.
- **Coordinates:** KiCad mm, with y = 0 at the aft edge. In the Gerbers, Y = −y.
- **Repository changes:** none except this file. `git status --short` was the same before and after every tool run. The
  fab outputs keep their 14:10 timestamps, and `cost_check.json` / `stock_check.json` keep 2026-10-19.
- **Comparison board** (read only): fix pass 2's `990c8040…`, the board pass 3 reviewed. I rebuilt it in the scratchpad
  from R7's board (`git show 431025d:…`) and the coordinator's `r8_backup_990c8040/tracked.diff` (`git apply --include`
  on the board only). Its SHA-256 matched `990c8040…` exactly.
- **Inference** marks anything not measured and not taken from a maker document (AGENTS §2.5).

## 1. Summary

**Critical 0, Major 0, Minor 2 (one worth fixing, records only).**

Fix pass 3's copper is exactly what its handoff describes, and it opens no DFM regression.
- **What `bdiff.py` (`990c8040…` → `c84f00b8…`) finds changed:**
  - one footprint moved: R172 (30.6 → 30.65, 48.1, rot 90, B);
  - USB_LIMITED's trunk (y 37.25 → 37.3);
  - CAM_PWR_EN's lower leg (x 28.0 L → x 28.25 and one 45° run into R74.1);
  - RAW_ACT_SENSE's lane and R172.2's stub (x 30.65);
  - one via resized: BAT_ENABLE (16.6, 104.5), 0.6 → 0.5 mm;
  - one GND cover via moved: (28.875, 32.875) → (29.125, 32.625).
- **What did not change:** pad zone connections and zone outlines.
- **Silkscreen:** the only change is R70's designator, which the build re-placed (R8P4-DFM-02).

The fab package is consistent and bound to `c84f00b8…`:
- `tools/check.sh` exits 0: DRC 0 at every severity, unconnected 0, parity 0, ERC 0; audit OK; silk OK; `check_r8` OK;
  route_check r8 0 failing / 3 allowlisted; actuators OK; fit OK.
- `export_fab.py --out <scratch>` gives a BOM (`be711876…`) and CPL (`ef90bfa1…`) byte-identical to `fab/`.
- All 14 Gerber, drill and job files equal `fab/m3_gerber.zip` once the `TF.CreationDate` line is removed. The
  assembly PDFs differ in 4 bytes each, inside `/CreationDate`.
- `fab_manifest.py`, `paste_check.py` and `jlc_orient.py --verify-cpl` report OK.
- The five DFM test suites (89 tests) pass.
- A live JLC cost and stock run (scratch `--fab` copy, 2026-10-20 21:47Z) on this BOM and CPL gives the recorded
  figures: $106.00 per board, 52 of 52 Extended codes, U4 the only short line, none thin.
- The plate model re-run on this board's `fit_check` report reproduces `step9/evidence/plate_r8.json` exactly, every
  value but the board SHA.

All three pass-3 DFM findings are closed or properly dispositioned (§2).

The two Minor items:
1. **R8P4-DFM-01 (worth fixing, records only):** R8_VALIDATION calls R172 "an 0603" twice; it is `rocket:R0402`.
   - The two places are l. 120, the fix-pass-3 evidence paragraph, and l. 128, the vibration row. `fix3_handoff.md`
     ("only an 0603 moved 0.05 mm") does the same.
   - The vibration row also says the plate model "was not re-run" because the moved parts are 0603s "that the plate
     model's lumped heavy parts do not include". In fact the model carries every part as a model-box-volume mass. The
     reason it does not matter is the mass: about 0.5 mg moved 0.05 mm.
   - The row cites only pass 2's re-run, but passes 3 and 4 also re-ran it, on `990c8040…` and `c84f00b8…`, and every
     value was equal.
2. **R8P4-DFM-02 (not worth fixing):** the rebuild moved R70's designator by (+0.104, −0.173) mm, an unrecorded change
   to the silkscreen output.
   - Its ink is now 0.175 mm from its own courtyard (was 0.003) and 0.376 mm from C70's (was 0.549).
   - It is still nearer its own part, and every silkscreen rule holds.
   - The fix-pass-3 records describe the output change as "only R172's CPL row". The bottom silkscreen Gerber changed
     too.

## 2. Previous pass in this dimension: closure on `c84f00b8…`

| Pass-3 ID | Fix-pass disposition | Measured on `c84f00b8…` | Status |
|---|---|---|---|
| R8P3-DFM-01 (records named a GND via as ACT_GATE's nearest GND copper; the pour is closer) | Records (D109): C12b #18 (R120.2) and #23 (J1.4), the note under C12b (J123.1), the pyro-observations ACT_GATE row, M3_R8, open items, `fix2_handoff.md`; candidate dropped; a GND-to-gate zone rule offered as an owner option | `nearfill.py`, distance from each pad to the nearest GND fill vertex: R120.2 0.150 and C120.2 0.150 (B); R121.1, R121.2 and Q122.3 0.151 (F); J1.4 0.151 (F and B); J123.1 0.150 (F and B). Via rings (`dfm2.py`): R120.2 0.180 mm from GND (15.0, 107.3). R8_VALIDATION C12b #18 (l. 437), #23 (l. 443), the note (l. 450) and the ACT_GATE observations row (l. 552) give these figures and drop the via-only candidate | **Closed** |
| R8P3-DFM-02 (`via_paste` ring clause looser than R7's ViaCheck) | Accepted, recorded (hard-gate row, D87, open items); ratchet not added | `vp.py`: via rings < 0.1 mm from a paste aperture: **12 pairs at 11 vias** (CAM_FB's via serves R71.2 and R72.1), all own-net. Worst: C90.1 0.025 mm (3V3 (34.8, 53.68)). Pass 3's board had 13 at 12: R165.2's BAT_ENABLE via, 0.075 mm then, left the list when D108 made it a 0.5 mm via. A further 4 sit at exactly 0.1 mm: U12.4, C84.1, and the two U30 T-pad vias (R7's). The gate evidence (`fix3_check_r8_report.json`) shows 709 pairs, nearest 0.025 mm. R8_VALIDATION l. 63 / l. 265 / l. 580 and M3_R8 l. 543 carry "12 at 11" | **Dispositioned** (recorded) |
| R8P3-DFM-03 (Q123's pin-1 dot on R162.2's opening) | Accepted, recorded as C20 | `q123.py`: dot box x 16.801–17.199, y 64.451–64.849; R162.2 B.Mask box x 15.711–17.088, y 63.383–64.516; overlap 0.01198 mm², unchanged. C20 (l. 352) and the open-items line (l. 581) carry it. M3_R8 §"Silkscreen" has no pointer to C20 (pass 3 offered either place; optional) | **Dispositioned** (recorded) |

**Fix pass 3's copper, in this dimension** (`dfm2.py`, `vp.py`, `r172.py`, `trkpad.py`; both boards):

| Item | `990c8040…` | `c84f00b8…` |
|---|---|---|
| BAT_ENABLE via (16.6, 104.5): ring to Q120.9's opening (BAT_IN) | 0.180 mm (Ø0.6) | **0.230 mm** (Ø0.5) |
| BAT_ENABLE via: ring to R165.2's paste (own net) | 0.075 mm | 0.125 mm (off the ViaCheck list) |
| BAT_ENABLE via: hole edge to R165.2's opening | 0.225 mm | 0.225 mm (within 0.35 mm, so tented per ORDERING §4) |
| GND cover via, moved to (29.125, 32.625): ring to nearest foreign opening | 1.050 mm (R70.1) | 0.810 mm (R70.1); hole 0.910 mm (pluggable) |
| R172 courtyard: nearest bottom courtyard | 0.570 mm (C15) | 0.620 mm (C15) |
| R172 pads: nearest foreign pad copper | 0.860 mm (C15.2) | 0.910 mm (C15.2) |
| R172 openings: nearest via ring | 0.711 mm (RAW_ACT_SENSE_MCU, own net) | 0.666 mm (own net); the ARM1_SENSE_MCU pyro via 0.830 mm |
| R172 courtyard to ARM1_SENSE_MCU via (29.3, 47.5) (L10_EXCEPT) | 0.635 mm | 0.685 mm (= `r8_route_check.L10_EXCEPT`) |
| USB_LIMITED to R172.1 / R172.2 | 0.180 / 0.180 mm | 0.230 / 0.230 mm |

- **R172's paste and CPL:** the paste apertures follow the pads (`paste_check` OK). The CPL row
  `R172,30.6500mm,-48.1000mm,Bottom,90` is rebuilt by `--verify-cpl` against JLC's footprint.
- **R172's silkscreen:** its designator is hidden, as M3_R8's list says.
- **New tracks:**
  - The 45° corners of the new tracks are all 135° (USB_LIMITED (16.35, 37.3), CAM_PWR_EN (28.25, 30.025),
    RAW_ACT_SENSE (30.65, 57.45)).
  - There is no acid-trap angle.
  - No new track or via comes within 0.2 mm of a foreign pad: the nearest new pad gap is Q120.9–BAT_ENABLE via
    0.231 mm.

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P4-DFM-01 | Minor (worth fixing: records only) | AGENTS §2.5 / §3 (measured, correct records); REQUIREMENTS P2 (vibration estimate's basis) | **The fix-pass-3 records call R172 an 0603 and justify not re-running the plate model on a wrong premise.** R8_VALIDATION l. 120 ("its placement change is R172 (an 0603, 0.05 mm, D106)") and l. 128 (vibration row: "fix pass 3 only R172 (0.05 mm), 0603s that the plate model's lumped heavy parts do not include, so it was not re-run (R8 pass 2 DFM re-ran it on `6600ef94…`: 69 of 69 values equal)"), and `fix3_handoff.md` §"Not done" ("only an 0603 moved 0.05 mm"). (a) R172 is an 0402: footprint `rocket:R0402`; C83 and R81 are 0603s. (b) `plate_model.py` does include every small part: "every other part at 3 g/cm³ of its model-box volume" (l. 10–11). So small parts are not left out. Their mass, about 0.5 mg for R172's box, is what makes a 0.05 mm move immaterial. (c) The row cites only pass 2's re-run. R8 pass 3 DFM re-ran the model on `990c8040…`, and this pass re-ran it on `c84f00b8…`. Both give every value equal to `plate_r8.json` except `board_sha256`, so the row can state a measured result instead of an argument | `pcbnew`: R172 `(footprint "rocket:R0402"`; R81 `R_0603_1608Metric`; C83 `C_0603_1608Metric`. `fit_check --report` diff between the two boards: only R172's row (box x 30.35–30.85 → 30.40–30.90). `step9/plate_model.py` (numpy 2.0.2, scratch venv) on the `c84f00b8…` report against `step9/evidence/plate_r8.json`: no difference but `board_sha256` (`429b6db4…` → `c84f00b8…`). f1 209 / 295 / 346 / 490 Hz (plugs on the sled), 173–379 Hz (plugs on the jacks); 100 g no jacks D5 pinned: 1.01 mm at (46, 62.5); U1 609, U4 509, C84 588 µε | R8_VALIDATION l. 120: "R172 (an 0402, 0.05 mm, D106)". l. 128: "fix pass 1 moved only C83, fix pass 2 only R81 (0603s) and fix pass 3 only R172 (0402, 0.05 mm); re-run by R8 pass 3 DFM on `990c8040…` and pass 4 DFM on `c84f00b8…`: every value equal to `plate_r8.json` but the board SHA". `fix3_handoff.md`: "an 0402". Optionally, regenerate `plate_r8.json` on `c84f00b8…` (the same values; binds the evidence to the final board). No copper |
| R8P4-DFM-02 | Minor (not worth fixing) | AGENTS §3 silkscreen (designator nearer its own part); record accuracy | **The rebuild re-placed R70's designator, and the fix-pass-3 records do not mention it.** R70 (bottom, (31.4, 33.05)): its reference moved from (29.124, 31.794) to (29.228, 31.621). Ink box x 27.787–30.413, y 31.174–32.324 → x 27.891–30.517, y 31.001–32.151. Ink to R70's courtyard 0.003 → 0.175 mm; to C70's 0.549 → 0.376 mm. Still nearer its own part: `r7_post.courtyard_offenders` is empty, and AGENTS' rule holds. Nearest via rings: GND (31.0, 31.3) 0.233 mm and the moved cover via (29.125, 32.625) 0.252 mm (was 0.337 / 0.379). Nearest opening R70.1 0.425 mm (was 0.254). The designator now reads slightly less clearly as R70's: the gap to its own courtyard is half the gap to C70's, where it was almost nil. The fix-pass-3 records (handoff "What changed", M3_R8 l. 560, R8_VALIDATION l. 139) describe the output change as "only R172's CPL row". The bottom silkscreen Gerber also changed here. Likely cause: `r8_post.py`'s designator spot search reacting to the moved cover via or CAM_PWR_EN's new diagonal (Inference; I did not trace the placer) | Silkscreen diff (`polys.py` on both boards, every silkscreen item): the only changed item is R70's `PCB_FIELD`. `r70.py` (reference position), `silk1.py` (no text ink within 0.1 mm of an opening, none over a via ring, no text overlap), `co.py` (`r7_post.courtyard_offenders` → `{}`). Designators: 168 shown, 81 hidden, equal to M3_R8's list (`desig.py`, the same on both boards) | None needed (cosmetic; every gate holds). If the fix pass touches the records again, add one line: "R70's designator re-placed by `r8_post.py` (0.2 mm), bottom silkscreen only". |

## 4. Fab package (regenerated and compared)

- **`tools/check.sh`** (KiCad Python, exit 0):
  - DRC 0 / unconnected 0 / parity 0 / ERC 0;
  - metadata / 3D model audit OK; silkscreen outside the outline 0;
  - R8 CAD contract OK; route_check r8 0 failing, 3 allowlisted, 0 stale, 0 leftovers, 0 removable (22 bump windows);
  - actuators OK; fit OK.
- **Export:** `python3 tools/export_fab.py --out <scratch>` reports:
  - 92 BOM lines, 219 placed parts;
  - no part without an LCSC code; no owner-fitted part;
  - DNP C303, C304, C305, C313, C314;
  - every CPL row corrected.

  BOM `be711876…` and CPL `ef90bfa1…` are byte-identical to `fab/`. The 14 Gerber, drill and job files match once the
  `TF.CreationDate` line is removed (the raw files differ only there). Each PDF differs in 4 bytes, the `/CreationDate`
  time (14:10:46 against 14:42:38).
- **CPL:** 89 Top and 130 Bottom rows, matching ORDERING §4. The only change since pass 3 is R172's row, which matches
  `r8_place.tsv` (30.65, 48.1, 90, B). `--verify-cpl` rebuilds 85 top and 126 bottom rows (worst 0.491 mm) and checks 8
  by placement only (J1, R72, R74, R77, R100, R101, R103, R110), with no errors.
- **`fab_manifest.py`:** OK, 5 outputs; `inputs_sha256["cad/m3.kicad_pcb"]` = `c84f00b8…`. The library, `.kicad_pro`,
  `.kicad_dru`, `fp-lib-table` and `sym-lib-table` are unchanged from `431025d` (`git diff --stat` empty).
- **`paste_check.py`:** OK. F 348 / 348, B 359 / 359, 20 dry pads (J30 / J31 and the DNP lands).
- **Drill:**
  - PTH T1 0.300 × 609 vias: 309 Ø0.6 and 300 Ø0.5 (pass 3: 310 / 299; D108 resized one);
  - the moved via is written as `X29.125Y-32.625` and the resized one as `X16.6Y-104.5`;
  - the other tools are unchanged (4 × 0.600 J3 slots, 2 × 0.8, 12 × 1.1, 8 × 1.6; NPTH 2 × 0.600, 3 × 0.991).
- **Procurement:** `check_procurement.py --cost-only` fails with "cost_check.json: BOM/CPL changed or report lacks input
  binding".
  - This is the recorded staleness: `cost_check.json` binds the step-9 CPL `d26572d3…` (ORDERING §1 l. 29, REQUIREMENTS
    M3, R8_VALIDATION open items; due within 24 h of ordering).
  - **Live run (this review, read-only):** I copied the BOM and CPL to the scratchpad and ran `jlc_stock.py --fab
    <scratch>` and `jlc_cost.py --fab <scratch>` (2026-10-20 21:46–21:47Z, 5 boards, bound to `be711876…` /
    `ef90bfa1…`):
    - 92 unique codes, 52 Extended / 40 Basic;
    - parts $77.85 per board; $106.00 per board with Standard's $1.53 per-code fee (cap $126.41);
    - extended codes 52 (limit 52); cost targets met;
    - short: U4 (C26633007, stock 0, consigned); thin: none.

    These are the recorded figures, so REQUIREMENTS M3 still holds on the final package. The repository's reports were
    not touched. The handoff's "no network" did not hold in this session (Inference about the fix session).
- **Tests (KiCad Python):** `test_paste_check` 5, `test_fit_check` 23, `test_fab_validation` 23, `test_procurement`
  15, `test_r8_check` 23, all OK (89).

## 5. Footprints, paste, mask, vias, silkscreen

- **Via to pad opening (foreign net, ring):** the smallest are LS120.2 0.124 mm (GND (15.2, 70.9)), R305.2 0.155 and
  R129.1 0.170. All are unchanged from pass 3 (`dfm2.py`), and every gap is above JLC's 0.10 mm soldermask bridge.
  - 93 vias have their hole edge within 0.35 mm of an opening (pass 3: 93), so ORDERING §4's "tent them" applies to
    them.
  - Only TP122's via (A8) has its hole in an opening.
- **Paste and mask:** no via ring overlaps a paste aperture. The 12 own-net pairs under 0.1 mm are R8P3-DFM-02's class
  (§2). Mask webs and pad-to-pad gaps are unchanged: R172 moved away from its nearest neighbour (C15, 0.57 → 0.62 mm
  courtyard).
- **R5 L10** (bottom courtyards to foreign THT rings, ≥ 1.5 mm gated), the same as pass 3:
  - D8–J121.2 1.502;
  - C83–J3.1 1.514;
  - R80–J1.3 1.527;
  - R165–J1.4 1.569;
  - R81–J121.1 1.575;
  - R120–J1.4 1.583 mm.
- **THT zone connections** (`thtzc.py`): identical on both boards, and ORDERING §4's hole-fill list matches.
- **Silkscreen:**
  - 168 designators shown, 81 hidden, 35 board legends, the same set as M3_R8.
  - No text ink within 0.1 mm of an opening, none over a via ring, no text overlap (`silk1.py`).
  - `r7_post.courtyard_offenders` is empty.
  - Footprint graphics against foreign openings (`silkforeign.py`): Q123's dot (C20), then 0.125 mm (J124 against
    R132 / R175), as in pass 3.
  - The only changed silkscreen item is R70's designator (R8P4-DFM-02).
- **Order mark:** no via or silkscreen moved near `JLCJLCJLCJLC` (16.13–26.67, 96.55–98.25); ORDERING §3's figures stand.

## 6. Fit, supports, hardware, vibration, SMA

- **fit_check** (in `check.sh`, and `--report` on both boards):
  - J9 mated 0.03, J122 mated 0.71, J3 0.89, J121 / J124 1.15, C84 1.37 mm;
  - worst bottom margin 2.36 mm (C91); deepest L1 at z −4.62;
  - nearest bottom item to a support R12.1 4.452 mm; nearest top item TP30.1 5.008 mm;
  - wire room 6.3–6.9 mm.

  The reports differ only in R172's box and the board SHA, and they equal ORDERING §7 and M3_R8 "Mechanical".
- **Supports, hardware and the tie path:** `supports.py` gives identical output on both boards. The copper is GND on all
  four layers at (4, 4), (42.3, 4), (4, 114.4) and (42, 114.4); at (4, 64) it is GND on F / In1 / B with In2 3V3. ORDERING
  §7 (nylon hardware, washers ≤ 7.0 mm OD, standoffs ≤ Ø6.4 mm and ≥ 3.5 mm tall) and the tie channel are unchanged.
- **Vibration (D75, C10):** the plate model re-run on `c84f00b8…` reproduces `plate_r8.json` (§3, R8P4-DFM-01).
  - f1 is 209 / 295 / 346 / 490 Hz with the plugs on the sled.
  - D75 / C10 stays properly dispositioned to the owner: C84 on the mode-1 antinode (−16.6 Hz), about +17 Hz if moved,
    no sixth-support ruling for R8.
- **SMA retention:**
  - J30 / J31 and the strip are rigid (`check_r8` OK, 12 / 12 digests).
  - ORDERING §4 / §5 / §7 and REQUIREMENTS P3 are unchanged: counter-hold, torque, saddle on the plug axis, staking after
    the RF tests, D30 / D31 inspection, no paste on the jack pads (`paste_check`).

## 7. Panel and tabs

| Tab | Nearest part | 5 mm class | Connector | Hole edge | Copper at the span (per layer, `tabcu.py`) |
|---|---|---|---|---|---|
| L 63–68 | U5 7.87 | C32 8.34 | J123 10.46 | 2.40 | F / In1 / B GND, In2 3V3 at 0.5; GND vias 1.04 |
| L 112.5–117.5 | Q121 8.15 | C120 12.70 | J1 11.96 | 2.40 | GND on all four at 0.5 |
| R 8–13 | C310 8.45 | C310 8.45 | J31 11.47 | 3.85 | GND on all four; GND vias 0.70 |
| R 18–23 | C73 5.20 | C73 5.20 | J9 16.48 | 12.88 | GND on all four; GND vias 0.70 |
| R 105–110 | TP88 2.44 | C96 5.97 | J121 8.00 | 4.35 | GND on all four at 0.5; GND vias 1.31 |

- Every figure equals pass 3's, and `tabcu3.py` gives identical output on both boards. ORDERING §3's table (box figures)
  and its rules hold: 1.5 mm to parts, 5 mm to the capacitor / R166 / LED2 / RF-module class, 2 mm to connectors,
  1.5 mm to holes.
- JLC's acceptance of five tabs without a forward rail remains a quote-time confirmation (ORDERING §3, Inference).

## 8. Sources

- JLCPCB PCB capabilities, https://jlcpcb.com/capabilities/pcb-capabilities (as cited in pass 3, read 2026-10-20):
  - Soldermask Bridge 0.10 mm (green, 1 oz);
  - multilayer via 0.15 mm hole / 0.25 mm diameter; via hole-to-hole 0.2 mm;
  - plugged vias "keep at least 0.35 mm from other mask openings";
  - silkscreen line ≥ 0.15 mm, text ≥ 1.0 mm, pad to silkscreen 0.15 mm;
  - mouse-bite tab ≥ 5 mm.
- JLCPCB public component search (`jlc_stock.py` / `jlc_cost.py`; live data 2026-10-20 21:46–21:47Z).
- Project files:
  - `docs/R8_VALIDATION.md` l. 63, 120, 128, 139, 265–266, 342, 352, 437, 443, 450, 552, 575–582;
  - `docs/M3_R8.md` §"Silkscreen" (l. 172–187), §"Mechanical" (l. 443–478), l. 543, 560;
  - `docs/ORDERING.md` l. 29, 46–79, 84–104, 208;
  - `docs/REQUIREMENTS.md` M2, M3, P2, P3;
  - `R8_DECISIONS.md` D75, D87, D106–D109;
  - `sources/r8_review/fix3_handoff.md`, `fix3_generators.diff`, `pass3_dfm.md`;
  - `step9/plate_model.py` l. 1–20;
  - `step9/evidence/plate_r8.json`, `fix3_check_r8_report.json`;
  - `m3_design/r8_route_check.py` (`L10_EXCEPT`), `m3_design/r7_post.py` l. 120–146.

## 9. Inferences

- The cause of R70's designator move (`r8_post.py`'s spot search reacting to the moved cover via or CAM_PWR_EN's
  diagonal; not traced).
- That the fix session lacked network access (its handoff says so; this session had it).
- The plate model's inputs (as recorded in D75).
- Whether JLC accepts five tabs without a forward rail.

## 10. Method (reproducible, read-only)

**Scripts.** KiCad 10.0.6 Python (`pcbnew.LoadBoard`; no board was saved). The scripts are in the session scratchpad
`r8p4dfm/`.
- Reused from pass 3: `bdiff.py`, `polys.py`, `geom.py`, `dfm2.py`, `nearfill.py`, `q123.py`, `silk1.py`, `silkpad.py`,
  `silkforeign.py`, `desig.py`, `co.py`, `l10.py`, `tabd.py`, `tabcu.py`, `tabcu3.py`, `supports.py`, `thtzc.py`.
- New in this pass:
  - `vp.py`: via ring to paste aperture, pairs under 0.1 mm;
  - `r172.py`: R172's courtyard, pad and via neighbours;
  - `r70.py`: the designator position;
  - `trkpad.py`: the changed nets' copper to foreign pads;
  - `c21.py`: a cross-check of a scratch-script false positive against `r7_post._poly_gap`.

  `desnear2.py` flags C21, but `r7_post` gives an own gap of 0.249 mm against C22's 0.433 mm, so it is not an offender.

**Tool runs:**
- `tools/check.sh`;
- `tools/export_fab.py --out <scratch>`, then diffs of the BOM, CPL, Gerbers, drills, job file and PDFs;
- `tools/fab_manifest.py`; `tools/paste_check.py`; `tools/jlc_orient.py --verify-cpl`;
- `tools/check_procurement.py --cost-only`;
- `tools/jlc_stock.py --fab <scratch>` and `tools/jlc_cost.py --fab <scratch>`;
- `tools/fit_check.py --report <scratch>` on both boards (the `990c8040…` copy with symlinks to the repository's
  `kilib`, `.kicad_pro`, `.kicad_dru` and lib tables), then `step9/plate_model.py` on the `c84f00b8…` report;
- the five unit-test suites in §4.

The scratch copies (the rebuilt `990c8040…` board, the regenerated package, the Gerber extracts, the live-run reports and
the virtual environment) were deleted after the run.
