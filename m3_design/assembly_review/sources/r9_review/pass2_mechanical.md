# R9 pass 2: mechanical fit and robustness review

Independent, read-only review (2026-10-25) of the uncommitted M3-ASSY-R9 board after review pass 1's fix pass
(worktree `rocket-flight-computer-r9`, branch `m3-assy-r9`). The board file `m3_design/assembly_review/m3.kicad_pcb` had
SHA-256 `4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14` at the start, after every tool run and at the
end. `m3.kicad_sch` (`5672d00a…`), `m3.kicad_dru` (`ea77b791…`) and `git status` were also unchanged. No repository file
was changed apart from this report. The pre-fix board `fc3d5b34…` was read from the fix pass's backup
(`scratchpad/r9review/orig/worktree_before_fix1.tgz`), and R8 `cc044ea0…` from git (`git show 9c8179b:…`). The sibling
worktrees were not touched.

Scope (the brief's mechanical dimension):
- the outline and P1; the bore envelope (fit_check, J122 turned on the axis);
- the five supports, including the mid support at (42, 59.5);
- the plate model (f1 against the 209 Hz gate and the 241 Hz target);
- the SMA jacks and their retention and staking;
- lead directions (pyro west, battery east) and wire room;
- the IMU lever arm and the 180° rotation; tall-part staking;
- the bay stack (the proposed parent VEHICLE.md row).

Vehicle-level choices and firmware are out of scope. Coordinates are KiCad mm (x = 0 west edge, y = 0 aft edge).
**Inference** marks anything not measured and not taken from a requirement or a maker document (AGENTS §2.5).

What was run:
- `tools/check.sh` on the worktree board: a GUI session was logged in, so no shim was needed; `NUMPY_PY` was the cfd
  venv and `TMPDIR` the scratchpad. **Exit 0**:
  - DRC 0, unconnected 0, parity 0, ERC 0;
  - metadata / 3D audit OK; silkscreen 0 points outside the outline; fit OK; plate model; seeded rule-H suite OK;
  - check_r9 OK on every rule (M-2…M-7, P-10, P-11, T-1 and R-3 evidence read from `r9.json`);
  - route_check r9: 0 failing / 0 allowlisted / 0 leftovers; check_actuators OK.
- `tools/fit_check.py` and `tools/plate_model.py` on a scratch copy of the board give the same figures as
  `step10_evidence/gate/check_sh.txt` and `gate/plate.json`. Both tools are byte-identical to the pre-fix backup, so the
  fix pass did not touch them.
- The same two tools on R8 `cc044ea0…` (f1 208.7 Hz, as recorded).
- Tests (KiCad Python): `test_fit_check` (23 tests) and `test_r9_check.MechanicalAndKept` (13 tests, M-2…M-7 and the
  kept rules): OK.
- A diff of `check_r9.py` against the pre-fix backup: no M-rule changed (only the M-7 docstring). A diff of
  `r9_place.tsv`: only C98 moved.
- My own read-only pcbnew and numpy scripts (core code in the Appendix):
  - footprints moved and vias added or removed between `fc3d5b34…` and `4f841a0e…`;
  - courtyards, pads and non-GND copper round every hole on every layer;
  - the jack-leg neighbours;
  - pass 1's modal code on the new fit report;
  - terminal-torquing point loads (signed surface strain along each capacitor's length) on R9 and R8;
  - a mid standoff out of plane;
  - exposed pads within reach of the staking fillets.
- Maker documents:
  - **DORABO DB128L-5.08-XXP-C-S customer drawing** (LCSC C430601): fetched and rendered, title block and views read.
  - **Samsung CL31 reference sheet with the MLCC product manual** (CL31B473KBCNNNC, the same series and template as
    C80/C96's CL31A106KBHNNNE): bending-strength line and handling cautions.
  - **Murata GCJ series page**: the resin termination and the cracked-MLCC failure mode.
  - **AEC-Q200 Rev D**, Table 2C: board flex is ">= x mm", a supplier value.

## 1. Summary

**Critical 0, Major 0, Minor 5.**

R9 `4f841a0e…` meets every mechanical requirement and gate I checked. The fix pass's only placement change, C98, and its
twelve new vias leave every mechanical figure at or above its rule:
- **P1:** the board is 46.00 × 102.00 mm (Edge.Cuts: four lines, square corners), against 120 mm.
- **P2, bore fit:** the fit report is identical to pass 1's apart from the support row. J9 mated is 0.028 mm (R6/R8's
  floor), J122 mated 0.50 mm (turned, owner decision 5), J121 and J124 1.232 mm, C84 1.367 mm and the worst bottom part
  2.366 mm.
- **P2, supports:** five M3 supports at (4, 4), (42, 4), (4, 98), (42, 98) and (42, 59.5).
  - Bottom clearance is now **4.483 mm (C98.1 at (42, 59.5))**: the fix pass moved C98 next to the mid support. Top
    clearance is 5.008 mm (TP30.1). The rules are 3.5 / 3.8 mm, and M-5's R8 floors are 4.452 / 5.008 mm.
  - The mid support is effective: f1 is 128.7 Hz with the corners only and 256.6 Hz with it.
- **P2, vibration:** f1 is 256.6 / 362.9 Hz pinned and 434.8 / 614.9 Hz clamped, against the 209 Hz gate and the 241 Hz
  target. The 100 g deflection is 0.66 mm at (0, 54), and the strains equal pass 1's.
  - The modal exposure of U4 and U5 reproduces on this board: 0.76 / 0.89 of the mode-1 peak, 18.1 g rms in mode 1 and
    18.8 over modes 1–6 (Inference).
  - It is listed for the owner (part D).
- **Wire entries:**
  - J121 and J124 enter from −x with 6.353 mm to the bore wall (P-11).
  - J1 enters from +y, its courtyard face 1.855 mm from the forward edge (M-4), 23.33 / 14.72 mm from the terminals.
- **IMU:**
  - U4 is on the bottom at (12.0, 47.4), rotation 180, pad 1 (SPI1_MISO) at (+1.21, −0.75) mm: R8's map turned 180°,
    so roll = −gyro_Y.
  - M-7 keys the rotation on the revision. The lever arm is 11.000 mm.
- **Pass 1:** every pass-1 mechanical finding is closed or dispositioned, except R9P1-MECHANICAL-05. It stays open; this
  pass re-reads the maker drawing and reverses pass 1's inference.

The five findings:
1. **R9P2-MECHANICAL-01: the DB128L stacking nubs face J1** (R9P1-MECHANICAL-05, still open).
   - The DORABO drawing is third-angle. Its front (wire-entry) view shows the 0.57 mm nubs on the right-hand end.
   - On R9 that end is J121's and J124's **forward** end, not the aft end pass 1 inferred.
   - J121's nubs engage J124's grooves, but J124's free-end nubs sit **0.25 mm** (nominal) from J1's back face. The
     J124-side tolerances alone (±0.20 + ±0.20 + 0.275 mm of pin play) can close that.
   - Modelled, J124's courtyard would overlap J1's by about 0.33 mm.
2. **R9P2-MECHANICAL-02: torquing J1 bends the board at the battery-input MLCCs, and nothing says to back the board.**
   - C80 and C96 (10 µF 1206 X5R, BAT_IN to GND, bottom) lie along the line between the forward supports, directly
     under J1, with their length along that line.
   - A 40 N push on a J1 screw puts about +1.2…+2.3 × 10⁻³ tension along their length (plate model, D 10…5; Inference).
     That is up to about twice the strain of the maker's 1 mm bend test.
   - R8's worst on the same parts was 0.93…1.86 × 10⁻³, from its J121; torquing R8's J1 gave ≤ 0.57 × 10⁻³.
3. **R9P2-MECHANICAL-03: the staking text does not keep the fillets off R9's new neighbours.**
   - C84's "all sides" fillet reaches TP120 (RAW_ACT, 0.80 mm) and the east test-pad column, including TP88, the
     designated GND probe point for the post-staking gates (1.70 mm).
   - J1's fillet reaches C89 / C95 (BAT_IN 1206, 0.55 mm).
   - J121's reaches R131 / R173 / R134 / D120 (0.26–0.95 mm), and J122's reaches R150–R153 (0.74 mm).
4. **R9P2-MECHANICAL-04: two records keep the pre-fix support figure.** M3_R9 l. 310 and ORDERING §7 Sled still say
   "4.600 mm, R300.2 at (4, 4)". The board says 4.483 mm, C98.1 at (42, 59.5).
5. **R9P2-MECHANICAL-05: the proposed VEHICLE row uses lateral words VEHICLE.md avoids, and omits J1's switch pair.**
   - "Left (x = 0)", "east side" and "west side" read the opposite way round for someone facing the top face with the
     nose up. VEHICLE.md defines no lateral convention.
   - J1 takes four wires through its forward face, not two.

All five fixes are text and a first-article check. The optional layout items are left to the next placement change, as
the plan's §5 asks of Minors.

## 2. Pass-1 findings in this dimension

| Pass-1 finding | Fix-pass disposition | Status on `4f841a0e…` |
|---|---|---|
| R9P1-MECHANICAL-01: IMU and barometer on mode 1's antinode | Fixed (records), listed (part D) | **Properly dispositioned.** M3_R9 l. 314–326 carries the mode position, the R7 / R8 / R9 comparison and the alternatives. R9_VALIDATION l. 154 and part D (l. 235) list it for the owner, and Open item 2 names it. ORDERING §5 l. 171 adds the tap check with the accelerometer at U4 or (0, 52) and U4 logged. Re-measured here (pass 1's code on `4f841a0e…`): U4 0.76, U5 0.89, mode 1 at 256.6 Hz with 54.2 % effective mass, U4 18.1 / 18.8 g rms. C98's move changed nothing |
| R9P1-MECHANICAL-02: bay stack and harness records | Fixed (records) | **Closed.** M3_R9 l. 328–344 has the bay paragraph: the harness sides, the battery leads below the board and sled, the forward U-turn clear of (42, 98), standoffs ≥ 3.5 mm. ORDERING §7 covers the battery lead (l. 204), the sled's open forward end (l. 211) and the servo-lead dress over the turned header (l. 209). The VEHICLE proposal (`fix1_handoff.md` §5) adds the standoff height, the U-turn and the harness sides. Its wording is R9P2-MECHANICAL-05 |
| R9P1-MECHANICAL-03: P2's stale R8 clause | Fixed | **Closed.** REQUIREMENTS l. 67: "R8: f1 is 13 % below R6's; accepted with R8's deviation list (C10) on 2026-10-20" |
| R9P1-MECHANICAL-04: hardware, staking and foam neighbours | Fixed (records) | **Closed as raised.** ORDERING §7 l. 212 names the masked RAW_PROTECTED / BAT_ENABLE / BAT_FAULT_N / LOGIC_SOURCE_ST tracks under the hardware; I re-measured them unchanged (§4.3). §5 l. 150 adds the J30 leg limits and C121's tie-hole limit (1.328 mm, confirmed), and §7 l. 213 keeps the foam off U4. The same staking paragraph misses the neighbours of C84, J1, J121, J124 and J122: R9P2-MECHANICAL-03 |
| R9P1-MECHANICAL-05: DB128L stacking nubs not modelled | Open (not in the fix brief) | **Open, and worse than pass 1 inferred.** The drawing puts the nubs on the end that is forward on R9, so J124's nubs face J1 at 0.25 mm: R9P2-MECHANICAL-01 |
| D-S10-18: check_r9's M-7 docstring | Fixed (INTEGRITY-05) | **Closed** (`check_r9.py` l. 75–77 now gives "R5-R8 0 … R9 180") |

The fix pass changed the mechanics in one place. **C98** (0603, 1 µF, USB_LIMITED to GND, bottom) moved from (37.0, 62.8)
rotation 0 to (39.275, 64.2) rotation 180 (`r9_place.tsv`; D-F1-05):
- C98.1 is the nearest bottom pad to the mid support: 4.548 mm of copper, 4.483 mm by fit_check's pad box, courtyard
  4.167 mm. It was C98.2 at 4.805 / courtyard 4.365.
- That is above the 3.5 mm rule and M-5's floor of 4.452. ORDERING §7's standoff (≤ 5.5 mm across flats, r 3.175 across
  corners) clears the courtyard by 0.99 mm.

Twelve vias were added and eight removed (§4.3). None changes a hole's non-GND copper, a fit figure or a tab window.

## 3. Findings

| ID | Sev. | Req. | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R9P2-MECHANICAL-01 | Minor (worth fixing: one remark and a first-article check) | P2 (fit of fitted parts); AGENTS §3 (dimensions from the maker's drawing); M3_R4 AG5's precedent ("clear of a tongue on either end"); R9P1-MECHANICAL-05 | **The DB128L stacking nubs are on the forward end of J121 and J124, so J124's free-end nubs face J1's back face at 0.25 mm.** The drawing's title block carries the third-angle symbol. Its front view is the wire-entry face (the three openings drawn solid), and the 0.57 mm nub shows on its right-hand end. The top view shows the two nubs on the same end. They sit near the back and near the entry face; the top-view bands (back 2.17 mm, entry 1.94 mm) match the side view's (2.16 / 1.9 mm), so the entry face is the top view's lower edge. On R9 the terminals are at rotation 90 with the entry facing −x. The right-hand end seen from the entry face is then the footprint's local −x, which is board **+y** (forward). So J121's nubs go into J124's grooves (the pair interlocks as the footprint intends), and J124's nubs face J1. Pass 1 took the entry face to be the top view's upper edge, which put the nubs aft (its Inference). The views above reverse that. **Stack-up:** J124's forward end is at y 88.58 (pin 2 at 86.04 plus 2.54) and the nub tip at 89.15. J1's back face is at 94.40 − 5.00 = 89.40 (J1's footprint description, from the DORABO drawing): **0.25 mm nominal**. The nub near J124's back face (x ≈ 12.9–14.2; the back face at x 15.10) lies inside J1's span (x ≈ 9.8–30.2). The drawing's own tolerances alone can close the gap on J124's side: ±0.20 on 2.54, ±0.20 on 0.57, and ±0.275 mm of play for the 1.05 mm-wide pin in a Ø1.6 hole along the row, 0.675 mm in all. If the nubs were in the footprint, J124's courtyard (now to 88.615) would reach about 89.19 and overlap J1's, which starts at 88.855. The current DRC-clean gap exists only because the nubs are left out. **Consequence (Inference):** J124 or J1 is seated proud or tilted. A proud screw terminal takes the screwdriver push on its solder joints, and J124 is the ARM terminal, torqued in the field. Plastic to plastic, no electrical path | DORABO DB128L-5.08-XXP-C-S drawing (LCSC C430601; https://datasheet.lcsc.com/datasheet/pdf/774f77501d8e260538e3ee59c3ecee93.pdf?productCode=C430601): third-angle projection symbol (title block); front view N × 5.08 with the 0.57 nub at the right end; top view; side view 10.10 / 14.10 with the pin 5.00 from the back face; pins 0.80 × 1.05, 3.50 ± 0.30; GB/T 14486-2008 table (±0.20 to 6 mm). Board (pcbnew): J121 (10.1, 73.27) and J124 (10.1, 83.5), rotation 90, `M3_DB128L_2P_BK_SW`; J124.1 (10.1, 80.96), J124.2 (10.1, 86.04); J1 (20.0, 94.4), rotation 180, courtyard y from 88.855; J124 courtyard to 88.615; fit boxes J124 y 78.42–88.58, J1 from 89.05 (0.35 mm of tolerance). `M3_DB128V_4P_Entry` description: "pin row 5.00 from the back face, 5.20 from the wire-entry face (DORABO drawing)". R9_VALIDATION l. 317 (open); ORDERING l. 103 (no nub remark) | (1) ORDERING §4 THT remark: "J121 and J124 (C430601) form one end-stacked pair. J121's two 0.57 mm stacking nubs (its forward end) go into J124's grooves. J124's own nubs (its forward end) face J1's back face 0.25 mm away (nominal). Seat J124 and J1 flat; do not force J124 against J1." (2) First article, before staking: J124 and J1 sit flat, with no gap under either end, and J124 does not bear on J1. If it bears, trim J124's two forward nubs (they serve only for stacking) and reseat. (3) Optional, at the next footprint or placement change: add the nubs to the DB128L model and courtyard at local −x. DRC then needs J1 ≥ 0.35 mm further forward; M-4's face distance would be about 1.5 mm, still ≤ 2.0 |
| R9P2-MECHANICAL-02 | Minor (worth fixing: one procedure line) | P3 (robustness; "two-terminal tall parts are staked", the board survives handling and integration); FMEA_REDUNDANCY l. 459 (terminate the J1 and pyro wires outside the airframe at 0.4 N·m); Samsung MLCC manual §4-10-4 / §4-10-5 | **Torquing J1 bends the board at the battery-input MLCCs C80 and C96, and no record tells the integrator to back the board.** C80 and C96 (10 µF 50 V X5R 1206, Samsung CL31A106KBHNNNE, BAT_IN to GND, upstream of U9's eFuse) sit on the bottom at (19.0, 99.7) and (24.0, 99.7), rotation 180. That is under J1's entry side, on the line between the forward supports (4, 98) and (42, 98), with their length along it. A screwdriver push on a J1 screw sags that 38 mm span, so the bottom face, where they sit, is in **tension along their length**. Plate model (R7 pass 2's code, D 5–10 N·m; Inference), 40 N on one J1 screw: up to **+2.33 × 10⁻³ (D 5) / +1.17 × 10⁻³ (D 10)**, worst on the GND screw. The same model on R8 gives ≤ +1.86 / +0.93 × 10⁻³ on R8's C80/C96, from its J121 (east-edge) push; torquing R8's own J1 gave ≤ +0.57 / +0.29 × 10⁻³. So R9 moves the worst case onto the battery terminal itself and raises it 1.25×. Samsung rates the series by "Bending to the limit (1 mm) with 1.0 mm/sec" on a 1.6 mm test board, about 1.2 × 10⁻³ on the usual 90 mm span (6tδ/L², Inference). A realistic D of about 10 (laminate plus outer copper, Inference) puts the 40 N push at that test strain, and a firmer push or D 5 at up to twice it. Murata: a cracked MLCC "may cause a drop in insulation resistance, which could lead to a short circuit". A BAT_IN short sits upstream of every on-board protection but the in-line 15 A fuse. It either blows the fuse (board dead, primary channel lost; the isolated Blue Jay remains) or, if resistive, heats in the bay (Inference, improbable). Pass 1 compared only the deflection (J1 0.32 mm, "no regression"). **Context:** R9 also turned C128 (GCJ soft termination, PYRO1_OUT to GND; a short bypasses Q124) so that its length runs along the J121 strain. Under a downward push it is in compression (−1.0…−1.9 × 10⁻³), which is far less damaging, and the pre-arm continuity reading sees an existing short (R5-V06). Noted, not raised | Board (pcbnew): C80 (19.0, 99.7) B, rotation 180, pads (20.475 BAT_IN / 17.525 GND, 99.7); C96 (24.0, 99.7) B, rotation 180; J1 pins at y 94.4, x 27.62 / 22.54 / 17.46 / 12.38. Signed strain, 40 N, D 5 / D 10 (`signed.py`, Appendix): J1 GND screw (22.54, 94.4): C80 +1460…+2258 / +730…+1129, **C96 +1889…+2330 / +944…+1165**; J1 BAT+ screw (27.62, 94.4): C96 +2189 / +1094 peak. R8 (C80 (35.8, 102.3), C96 (38.9, 102.3) B, rotation 90): J121 IGN screw (36.0, 95.86): C96 +907…+1860 / +453…+930; R8 J1 screws ≤ +569 / +285. Turned to run along y, R9's C80/C96 would see about 0.3 × 10⁻³: the along-y strain at their spots is 309 / 269 µε at D 5 for 40 N at J1's centre (20.0, 94.4), against 2286 / 2202 µε along x (`pointload.py`). Samsung CL31 reference sheet (CL31B473KBCNNNC, https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7483/cl31b473kbcnnn_specsheet.pdf), "Bending Strength … Bending to the limit (1㎜) with 1.0mm/sec", T = 1.6 mm substrate; manual §4-10-4 ("insertion or removal from sockets and connectors may cause the board to bent"), §4-10-5 ("Plan the work to prevent the board from bending"; torque driver), "Support the bottom side of the board to avoid bending the board". Murata GCJ page (https://www.murata.com/en-sg/products/capacitor/ceramiccapacitor/overview/lineup/smd/gcj). ORDERING §5 / §7 and FMEA l. 459: no word on backing the board | ORDERING §5 (with the termination step of FMEA l. 459, and §7 Sled): "Torque J1, J121 and J124 only with the board backed directly under the terminal: a non-conductive block against the bottom face beside the terminal's pin tails, clear of the bottom parts (C80 / C96 lie under J1's entry side). Or terminate before the board goes on its standoffs. Use a torque driver at 0.4 N·m (FMEA). Never push on a terminal with the board held only on its five standoffs. After terminating, inspect C80 / C96 and repeat the pre-arm continuity reading." Optional at the next power-entry change: turn C80 / C96 so their length runs along y (about 7× less strain) |
| R9P2-MECHANICAL-03 | Minor (worth fixing: text only) | P3 (staking); R9P1-MECHANICAL-04's precedent (J30, C121) | **ORDERING's staking paragraph says "on all sides" and "the three screw terminals, J122 and J123" without naming R9's close neighbours of those bodies.** Model box edge to the neighbour's exposed pad: **C84 →** TP120.1 (RAW_ACT test pad) **0.80 mm**; TP83.1 (VLOGIC), TP85.1 (BAT_FAULT_N) and TP89.1 (BAT_ILIM) 1.60 mm; **TP88.1 (GND) 1.70 mm**, one of the two GND probe points ORDERING names for the armed and leakage gates, which run again after staking (§5 l. 141, 151, 155); TP74, the other, is 2.2 mm away. **J1 →** C89.1 / C89.2 / C95.1 / C95.2 (22 µF 1206, BAT_IN / BAT_DAMP) **0.55 mm**. **J121 →** R131 (the cold pull-up) **0.26 mm**, R173 (CONT top) 0.48 mm, R134 (the 2 Ω pulse resistor) 0.80 mm, D120 0.95 mm. **J124 →** R134 0.80 mm. **J122 →** R150–R153 (servo series resistors) 0.74 mm. **C121 →** R103 1.08 mm, C97 1.27 mm. A base fillet runs about 1–2 mm out from the body (Inference). So these fillets would cover test points the later gates need, and bond small parts, MLCCs among them, to large terminal bodies that the screwdriver moves (R9P2-MECHANICAL-02) | `stake_nb.py` (Appendix) on `4f841a0e…`: C84 box x 31.75–42.25, y 75.25–85.75; J1 box x 9.2–30.8, y 89.05–99.75; J121 box x 4.75–15.45, y 68.19–78.35; J122 box x 17.92–28.08, y 58.21–65.79. ORDERING l. 150 (the staking text), l. 151 (TP74 / TP88 as GND points), l. 141 (staking precedes the repeated pyro gates), l. 147 (coating already kept off every other test pad) | ORDERING §5 Staking. "C84: fillet on its north, south and east faces only, off TP120 (0.8 mm west of the can) and the east test-pad column TP83 / TP85 / TP88 / TP89 (1.6–1.7 mm). J1: along its back face and west end, off C89 / C95 at its east end. J121 / J124: along the west (entry) face below the wire openings and the outer ends, off R131, R173, R134 and D120 on the east side. J122: at its two end faces, off R150–R153. C121: off R103 and C97 as well as the tie hole. Never bridge a fillet onto another part's body or pad." |
| R9P2-MECHANICAL-04 | Minor (worth fixing: two figures) | P2 (support clearance); REQUIREMENTS M2's records | **Two records still give the pre-fix bottom support clearance.** The fix pass moved C98 next to the mid support (D-F1-05). The nearest bottom part to a support is now C98.1 at (42, 59.5): **4.483 mm** by fit_check, 4.548 mm of pad copper, courtyard 4.167 mm. M3_R9's fit sentence and ORDERING §7's sled row still name R300.2 at (4, 4) at 4.600 mm. R9_VALIDATION, the scorecard and ORDERING's hardware row carry the new figure, so ORDERING now contradicts itself between two adjacent rows. The sled row is the one a sled or standoff designer reads | `docs/M3_R9.md` l. 310: "support clearances 4.600 mm bottom (R300.2 at (4, 4))". `docs/ORDERING.md` l. 211 (Sled): "no bottom part within 3.5 mm of a hole centre: nearest 4.60 mm, R300.2 at (4, 4)". Against: `step10_evidence/gate/check_sh.txt` l. 24 ("C98.1, 4.483 mm from support (42.0, 59.5)"); `r9_scorecard.md` F3 4.483; R9_VALIDATION l. 76 / 155; ORDERING l. 212 ("C98.1 … at 4.55 mm from (42, 59.5)"); this review's fit_check run | M3_R9 l. 310: "support clearances 4.483 mm bottom (C98.1 at (42, 59.5), since the fix pass moved C98; fc3d5b34: 4.600 mm, R300.2) and 5.008 mm top (TP30.1)". ORDERING l. 211: "(no bottom part within 3.5 mm of a hole centre: nearest 4.48 mm, C98.1 at (42, 59.5))" |
| R9P2-MECHANICAL-05 | Minor (worth fixing: one clause) | P1 (record the orientation and bay stack in the parent VEHICLE); parent VEHICLE.md "Conventions"; R9P1-MECHANICAL-02 | **The proposed VEHICLE stack row names lateral sides in the board's KiCad view, and leaves out J1's switch pair.** (a) It says "both pyro terminals take their wires from the left (x = 0) edge", "the battery leads run … along the east side" and "the igniter and ARM leads run along the west side". VEHICLE.md defines no lateral convention ("No fixed x/y axes or lateral sign convention are defined. Keep it that way unless a task truly needs one"). For someone facing the top face with the nose up, the board's x = 0 edge is on the **right**: KiCad's view has the aft edge at the top. The words read the wrong way round exactly where the bay layout is still open (the board's angular position waits on the camera shroud). (b) J1 takes four wires through its forward face: BAT_IN (J1.1), GND (J1.2) and the power-switch pair BAT_SW_SOURCE / BAT_SW_RETURN (J1.3 / J1.4, its west half). The row's "battery-wire entry" and "allow that bend" cover two | `fix1_handoff.md` §5 l. 74–84 (the proposed row); parent `docs/VEHICLE.md` l. 48–52 (Conventions), l. 39 (the current R8 row); board: J1 pads 1 BAT_IN (27.62, 94.4), 2 GND (22.54), 3 BAT_SW_SOURCE (17.46), 4 BAT_SW_RETURN (12.38); ORDERING l. 5 defines "left" for the JLC / KiCad view only | In the proposed row: "both pyro terminals take their wires from the board's x = 0 edge (the pyro-terminal side); … the battery leads run aft to forward along the board's x = 46 side (J9's), below the board and sled …; J1's four wires (the battery pair and the power-switch pair) enter its forward face and turn back beyond the forward edge, so allow that bend forward of the board; the igniter and ARM leads run along the x = 0 side". The same "four wires" in M3_R9's bay paragraph and ORDERING §7 Battery lead |

## 4. Measurements (board `4f841a0e…`)

### 4.1 Outline (P1)

- **Edge.Cuts:** (0, 0)–(46, 0)–(46, 102)–(0, 102), 0.05 mm strokes.
- **Holes:** seven Ø3.2 circles. Supports at (4, 4), (42, 4), (4, 98), (42, 98) and (42, 59.5); tie holes at (15.6, 62)
  and (30.8, 59).
- **Board:** thickness 1.6 mm; title-block revision "M3-ASSY-R9".
- **Unchanged by the fix pass:** the outline, the holes and every footprint but C98.

### 4.2 Bore fit (P2, `fit_check`; radius 24.9 mm, axis x 23.0, ±0.3 mm, top face on the axis)

| Item | Box x; z (mm) | Margin |
|---|---|---|
| J9 mated | 40.95–45.20; 0–10.30 | 0.028 (R6/R8 floor) |
| J122 mated (turned) | 17.92–28.08; 0–23.50 | 0.500 |
| J3 | −0.45–7.45; −0.85–3.25 | 0.886 |
| J121 / J124 | 4.75–15.45; 0–14.40 | 1.232 |
| C84 | 31.75–42.25; 0–12.80 | 1.367 |
| J123 mated | 37.00–43.00; 0–9.50 | 2.358 |
| Worst bottom: C72 / C73 | 42.06–44.76; −4.30…−1.60 | 2.366 |
| Deepest bottom: L1 | z −4.62 (3.02 mm below the bottom face) | — |

The wire entries at 5 mm height are J121 6.4–7.0 mm and J124 6.4–7.0 mm (P-11: 6.353 mm). fit_check has no issues.

### 4.3 Supports and hardware (P2)

Distances are from each hole centre (r 1.6). Top uses the 3.8 mm rule, bottom 3.5 mm.

| Support | Nearest top courtyard / exposed pad | Nearest bottom courtyard / exposed pad | Non-GND copper within r 3.5 (F) / 3.2 (B) |
|---|---|---|---|
| (4, 4) | U30 3.849 / TP30.1 5.008 | R300 4.248 / R300.2 4.681 | none |
| (42, 4) | J31 6.215 / J31 pads 6.56 | none within 6.5 | none |
| (4, 98) | J1 4.955 / none within 6.5 | none | none |
| (42, 98) | R166 4.785 / R166.1 5.030 | R83 4.375, R82 4.452 / R83.1 4.625 | F.Cu BAT_ENABLE 3.10; B.Cu BAT_FAULT_N 2.90 |
| (42, 59.5) | TP76 4.887 / TP76.1 5.233 | **C98 4.167 / C98.1 4.548** (USB_LIMITED; was C98.2 4.805) | F.Cu RAW_PROTECTED 2.15 (0.40 mm track); B.Cu BAT_FAULT_N 2.37, LOGIC_SOURCE_ST 3.13 |

- **Unchanged by the fix pass:** every hole has GND fill on all four layers to 2.10 mm (0.5 mm from the edge) and no other
  net's fill within the washer radius.
- **The tie holes:** unchanged from fc3d5b34 (east tie hole: B.Cu USB_LIMITED track 2.12 mm, RAW_ACT pour 2.10 mm on
  B.Cu and In2; nylon tie).
- **Fix-pass vias** (12 added, 8 removed):
  - near the mid support, (38.55, 58.95) GND is 3.49 mm from (42, 59.5), inside the top washer's 3.5 mm and outside the
    standoff's 3.2 mm, plugged;
  - (32.9, 99.85) GND is 2.15 mm from the forward edge, away from both forward tabs;
  - (41.4, 41.1) GND is 4.6 mm from the east edge;
  - R7's three U31 module vias lie under U31.
  - None is in a tab span or a hole web.
- **Over-constraint (Inference).** With the mid standoff 0.3 mm out of the corners' plane (forced displacement, four
  corners pinned), the strain is modest at the nearest parts:
  - C98: 0.03 × 10⁻³ along its length (0.35 principal);
  - C92 (1210): 0.33 × 10⁻³;
  - C91: 0.04 along its length (0.35 principal);
  - U11: 0.33 principal.
  - Displacement-controlled, so independent of D.
  - A sled tolerance of ±0.3 mm does not crack them; no finding.

### 4.4 Plate model and modes (P2; gate M-2)

| Case (jacks only) | R9 `4f841a0e…` | R8 `cc044ea0…` |
|---|---|---|
| Pinned D 5 / D 10 | **256.6** / 362.9 Hz | 208.7 / 295.1 Hz |
| Clamped D 5 / D 10 | 434.8 / 614.9 Hz | 346.3 / 489.7 Hz |
| Plugs on the jacks (P3 forbids), pinned D 5 | 183.7 Hz | 173.2 Hz |
| Corners only, pinned D 5 | 128.7 Hz | 97.7 Hz |
| 100 g static, largest deflection | 0.66 mm at (0, 54) | 0.98 mm at (46, 63.5) |

**Strains:** 100 g peak strain, unchanged from pass 1 (µε): U31 434, U30 484, U4 405, U1 488, J121 780, J124 840,
C121 557, C84 596, U5 480, J1 888, J122 519.

**Modes:** pass 1's code (Appendix) on this board.

| Mode | f | Antinode | Effective mass | U4 | U5 | U4 response |
|---|---|---|---|---|---|---|
| 1 | 256.6 Hz | (0.0, 52.5) | 54.2 % | 0.76 | 0.89 | 18.1 g rms |
| 2 | 473.9 Hz | (46.0, 30.5) | 5.2 % | — | — | 3.4 g rms |
| 4 | 709.9 Hz | (22.0, 102.0) | 26.3 % | — | — | 2.4 g rms |

- Over modes 1–6, U4 sees 18.8 g rms (Miles, Q 10, 0.04 g²/Hz; Inference).
- These are pass 1's figures: C98's move made no difference. They are listed in part D.

### 4.5 Terminal torquing (P3; new in this pass)

**Method (Inference: R7 pass 2's plate and inputs):**
- 40 N point load on each screw position.
- Five supports, pinned, D 5 and D 10 N·m.
- Surface strain along each capacitor's length, signed (tension +) for the face it sits on.
- The same script on R8's fit report.

**Deflection at the pushed terminal** (as pass 1 found):

| Terminal | R9 | R8 |
|---|---|---|
| J121 | 1.04 mm | 1.03 mm |
| J124 | 0.57 mm | 0.53 mm |
| J1 | 0.32 mm | 0.35 mm |

**Strain along each part's length, worst screw** (×10⁻³, D 5 / D 10):

| Part (face, length axis) | Role | R9 | R8 |
|---|---|---|---|
| C96 (B, x on R9 / y on R8) | BAT_IN–GND 1206 | **+2.33 / +1.17** (J1 GND screw) | +1.86 / +0.93 (R8's J121 IGN screw); R8's J1 ≤ +0.57 / +0.29 |
| C80 (B, same) | BAT_IN–GND 1206 | +2.26 / +1.13 (J1 GND screw) | +1.82 / +0.91 (R8's J121) |
| C88 (B) | BAT_IN–GND 0402 (U9 IN) | +0.45 / +0.23 | +0.13 / +0.07 |
| C89 / C95 (F) | BAT_IN–damper 1206 | compression, ≤ 0.64 / 0.32 | compression, ≤ 1.33 / 0.67 |
| C128 (F, y on R9 / x on R8) | PYRO1_OUT–GND 0603 (GCJ) | **−1.94 / −0.97, compression** (J121 OUT screw) | −0.78 / −0.39 (R8's J1) |

**References:**
- Samsung's series rating: "Bending to the limit (1 mm)", about 1.2 × 10⁻³ on a 90 mm span (Inference).
- Murata's GCJ page claims only "suppressed" cracking, with no figure.
- AEC-Q200 Rev D Table 2C leaves the board-flex deflection to the supplier (">= x mm").

**Conclusions:**
- C80 and C96 are the parts in tension, right under the battery terminal: R9P2-MECHANICAL-02.
- C128 is in compression under the common (downward) push, and its soft termination and the pre-arm continuity reading
  remain the barriers.

### 4.6 SMA jacks (F10, P2, P3)

- **Placement:** J30 (13.59, 0) and J31 (32.29, 0), rotation 0, 18.70 mm apart (R-3). They overhang the aft edge by
  9.5 mm (courtyard to −9.795).
- **Leg-pad neighbours:** identical to pass 1, so the fix pass changed nothing here (courtyard to leg pad, mm):
  - J30.1 (F): D30 1.04, C302 1.37, L30 1.49;
  - J30.2 (F): C303 0.81, D30 1.67;
  - J30.3 (B): R300 2.28, R303 3.18;
  - J30.4 (B): R303 3.44;
  - J31: D31 1.04 / 1.67, nothing on the bottom.
- **Retention chain:** present (REQUIREMENTS P3; ORDERING §5 counter-hold, torque and staking order; §7 sled tongue and
  saddle).
- **Clearances under the bottom face:** the plug nut reaches 2.535 mm below the bottom face. A 5/16 in nut (9.17 mm
  across corners) about the axis 0.45 mm above the top face clears ≥ 3.5 mm standoffs by about 1 mm (Calc). The 6.5 mm
  flange reaches 1.2 mm below.
- **Nit:** ORDERING l. 150 gives "L30 (1.37–1.49 mm from the west leg)". The 1.37 is C302's and the 1.49 is L30's.

### 4.7 Terminals, lead directions, wire room, and the DB128L drawing

- **Entries:** J121 (10.1, 73.27) and J124 (10.1, 83.5), rotation 90, enter from −x. J1 (20.0, 94.4), rotation 180,
  enters from +y (M-4 and P-11 hold).
- **Wire room:** J121 / J124 have 6.353 mm (P-11) and 6.4–7.0 mm at 5 mm height. The model's entry face is 0.25–0.35 mm
  conservative (the pin is 5.00 mm from the back face of a 10.10 mm body).
- **Drawing reading** (R9P2-MECHANICAL-01; rendered at 600 dpi from the LCSC PDF):
  - the projection symbol, circles on the left with the frustum's small end toward them, is third-angle;
  - the front view shows three solid wire openings (the entry face) and a 0.57 mm strip on the right-hand end at the
    opening level;
  - the top view shows two 0.57 mm tabs on the right-hand end: one 0.93–2.17 mm from the back face, one 0.55–1.79 mm
    from the entry face (scaled from the 10.10 mm depth);
  - the band widths confirm the views (top view 2.17 / 1.94 mm, side view 2.16 / 1.9 mm, back / entry).
- **Mapping to R9:** for a viewer facing the entry face (local −y) with up out of the top face, the right-hand end is
  local −x. Rotation 90 maps local (−1, 0) to board (0, +1) (fit_check's transform), so the forward end.
- **Harness sides:** owner decision 1 says battery east and pyro west. plan_spine (approved through r9_plan) has J1 on
  the forward edge with the battery leads "along the EAST wall". On the top side, J9's mated plug closes that wall
  (0.028 mm); the fix pass routed the leads below the sled (recorded).

### 4.8 J122 and its tie (P2, P3)

- **Position:** J122 (23.0, 62.0), rotation 180, on the roll axis. M-3 holds:
  - the tie holes are 2.3 / 2.7 mm past the courtyard ends;
  - the tie line crosses the plugs at 2.213 / 1.711 / 1.21 / 0.709 mm off their centre lines (half plug 3.81);
  - the nearest bottom part to the line is R124 at 2.007 mm (thin, C13).
- **Servo-lead dress over the turned header:** an ORDERING §7 bench item.
- **Staking neighbours:** R150–R153 at 0.74 mm (R9P2-MECHANICAL-03).

### 4.9 IMU (F1, F5; M-7)

- **Placement:** U4 on the bottom at (12.0, 47.4), rotation 180. Pad 1 (SPI1_MISO) is at (13.21, 46.65), an offset of
  (+1.21, −0.75). R5–R8 had (−1.21, +0.75) at rotation 0.
- **Axis map:** +X_imu = −x_board, +Y_imu = −y_board, +Z_imu out of the bottom face, right-handed in KiCad's frame.
  Roll = −gyro_Y; thrust reads −a_Y.
- **M-7 evidence:** the revision "M3-ASSY-R9" requires 180; lever arm 11.0 mm (≤ 13; the done row ≤ 11 is met at its
  limit); bodies clear of vias and fill on their face.
- **P-10:** the coat region is 5.526 mm from U4.
- **U4–U5:** courtyards about 1.8 mm apart; the foam is trimmed to U5 (ORDERING l. 213).

### 4.10 Tall parts and staking (P3)

- **Staked:** C84 (12.8 mm), C121 (10.5), J1 (14.5), J121 / J124 (14.1, 14.4 envelope), J122 (23.5 mated), J123
  (9.5 mated), and J30 / J31 after the RF tests.
- **Not staked:** J9, J3, L1 / L3 (bottom), LS120 and U30 / U31 (as pass 1).
- **No staking site near U4 or U5.**
- **Fillet reach:** the reach of each fillet to its R9 neighbours is R9P2-MECHANICAL-03 (table there).

### 4.11 Bay stack and the VEHICLE proposal (P1)

- **The proposed row** (`fix1_handoff.md` §5) carries everything pass 1 asked for:
  - length 102 and the five holes;
  - the 9.5 mm jack overhang and J1's forward entry;
  - pyro entries from x = 0 and 3.0 mm bottom parts;
  - standoffs ≥ 3.5 mm;
  - the battery leads below the board and sled with the U-turn;
  - the harness sides.
- **Slack arithmetic checks out** (Calc): 595 − (80 + 44…48 + 102 + 25 + 260) = 80–84 mm with the loops beside the
  shroud. With the aft edge at joint +91…95 it is 68–72 mm, so "~68–84 mm" stands; R8's "~52–68" also checks.
- **Its wording is R9P2-MECHANICAL-05.**
- **The parent VEHICLE.md** still shows R8's row. It has unrelated uncommitted edits (K850DM) that are not this
  review's concern.

## 5. Checked, no finding

- **fit_check and plate_model:** both unchanged since 2026-10-20 (byte-identical to the pre-fix backup). Their outputs on
  `4f841a0e…` equal the bound evidence (`gate/fit.json`, `gate/plate.json`, `board_sha256` = `4f841a0e…`).
- **check_r9's M-rules:** unchanged by the fix pass (diff); M-2…M-7, P-10, P-11, T-1 and R-3 pass, and their tests pass.
- **T-1 and the four tabs:** unchanged.
  - Windows: west 0.5–7.25, 12.0–20.5, 53.5–101.5; east 0.5–27.0, 92.75–101.5.
  - Three tabs sit beside the corner holes' 2.4 mm webs, as R8's forward tab did. ORDERING's "nibble, never snap"
    covers them.
- **Mid support web:** 2.4 mm to the east edge, no tab beside it.
- **Hole neighbourhoods:** every hole's courtyards, pads and copper are identical to `fc3d5b34…` except C98 at
  (42, 59.5).
- **The 9 mm washer remark** in ORDERING l. 212 ("clear every pad, by 0.05 mm") is right for C98.1 (4.548 − 4.5).
- **Nylon hardware:** remains mandatory for the masked tracks under the hardware.
- **Battery-lead path:** under the sled on the east side it meets no board feature. The (42, 98) standoff's clearance at
  the forward-edge turn is recorded.
- **Coupler and bore:** fit_check uses Ø50.8 mm along the whole board, which is conservative where the board's forward
  part enters the Ø54.6 mm tube above joint +120.

## 6. Outside this dimension (for the coordinator)

- ORDERING l. 3 still says "no independent review pass has run on it". Pass 1 ran, and its fix pass made this board.

## 7. Sources

- **DORABO DB128L-5.08-XXP-C-S customer drawing** (LCSC C430601):
  https://datasheet.lcsc.com/datasheet/pdf/774f77501d8e260538e3ee59c3ecee93.pdf?productCode=C430601
  - title block: third-angle symbol, GB/T 14486-2008 tolerances;
  - front, top and side views: 0.57 mm nubs, 10.10 / 14.10, pin 5.00 from the back face, pins 0.80 × 1.05, 3.50 ± 0.30.
- **Samsung Electro-Mechanics CL31B473KBCNNNC reference sheet** with the MLCC product manual (the CL31 series template
  that C80/C96's CL31A106KBHNNNE shares; that part's own sheet was not fetched):
  https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7483/cl31b473kbcnnn_specsheet.pdf
  - "Bending Strength … Bending to the limit (1㎜) with 1.0mm/sec" (T = 1.6 mm substrate);
  - §4-1-1 (mounting position), §4-1-3 (near screws), §4-10-4 (connector attach / detach), §4-10-5 (fastening screw),
    and "Support the bottom side of the board".
- **Murata GCJ series page:** https://www.murata.com/en-sg/products/capacitor/ceramiccapacitor/overview/lineup/smd/gcj
  ("Cracking … suppressed by the resin of the external electrodes"; "cracks … could lead to a short circuit").
- **AEC-Q200 Rev D** (2010-06-01), Table 2C "21. Board Flex: >= x mm":
  http://www.aecouncil.com/Documents/AEC_Q200_Rev_D_Base_Document.pdf
- **Project files:**
  - tools: `tools/fit_check.py`, `tools/plate_model.py`, `tools/check_r9.py` (M-2…M-7, P-10, P-11, T-1, R-3),
    `tools/test_fit_check.py`, `tools/test_r9_check.py`;
  - `m3_design/r9_place.tsv` (C98);
  - `docs/M3_R9.md` l. 306–344, 353–360;
  - `docs/ORDERING.md` l. 3, 5, 103, 141, 147, 150–151, 155, 171, 204, 209, 211–213;
  - `docs/R9_VALIDATION.md` l. 76, 154–157, 235, 313–317, 355–372;
  - `docs/REQUIREMENTS.md` l. 66–68;
  - `docs/FMEA_REDUNDANCY.md` l. 459;
  - `docs/M3_R4.md` l. 78 (W3, GCJ for C128), l. 291 (AG5, the tongue);
  - `docs/R5_VALIDATION.md` l. 33 (R5-V06);
  - `kilib/rocket.pretty/M3_DB128L_2P_BK_SW.kicad_mod`, `M3_DB128V_4P_Entry.kicad_mod`;
  - `sources/r9_review/pass1_mechanical.md`, `fix1_handoff.md`, `fix1_progress.md`;
  - `step10_evidence/gate/` (check_sh, fit, plate, r9), `requalify_r9.json` (`mech.*`, `imu`), `r9_scorecard.md`;
  - parent `docs/VEHICLE.md` l. 36–41, 48–52.

## 8. Inferences (not measured, not from a maker document)

- **Plate inputs.** The plate model's inputs (D 5–10 N·m, laminate mass, lumped masses, point supports) are R7 pass 2's.
  - The R8 / R9 ratios are the robust result.
  - A realistic D of about 10 counts the outer copper.
  - The 40 N screwdriver push is assumed (pass 1's value).
  - A point load and point supports smooth the local field.
- **Strain conversion.** Converting Samsung's 1 mm bend rating into about 1.2 × 10⁻³ assumes the usual 90 mm span
  (6tδ/L²).
- **Fillet and short behaviour.** A fillet's reach of about 1–2 mm is an assumption. So are a cracked BAT_IN MLCC's
  consequences (a blown fuse or a resistive short).
- **DB128L drawing reading.** The reading of the DB128L drawing (nub end forward on R9) still needs the first article.
  - The interference consequence (seated proud, load on the joints) is assumed.
- **Mode exposure.** The modal response at U4 (Miles, Q 10, 0.04 g²/Hz) is a trend, as in pass 1.

## Appendix: core code (numpy, `tools/plate_model.py` unchanged; pcbnew scripts read-only)

```python
# modes and U4 response (pass 1's method), FIT = tools/fit_check.py --report of the board
p, masses, _ = PM.build(fit, 5.0, False, 'jacks_only'); Z = p.basis()
Kr, Mr = Z.T @ p.K @ Z, Z.T @ p.M @ Z; Li = np.linalg.inv(np.linalg.cholesky(Mr))
w2, V = np.linalg.eigh((Li @ Kr @ Li.T + (Li @ Kr @ Li.T).T) / 2); one = np.zeros(p.K.shape[0]); one[0] = 1
for i in range(6):
    f = math.sqrt(w2[i]) / (2 * math.pi); c = Z @ (Li.T @ V[:, i]); gam = float(c @ (p.M @ one))
    phi = float(p.field(c, np.array([masses['U4'][1]]), np.array([masses['U4'][2]]))[0, 0])
    grms = abs(gam * phi) * math.sqrt(math.pi / 2 * f * 10 * 0.04)

# terminal push: 40 N at (x, y) mm, signed strain along a part's length (tension +; top face +t/2 w'', bottom -t/2 w'')
c = Z @ np.linalg.solve(Z.T @ p.K @ Z, Z.T @ (40.0 * p.phi((x - x0) / 1e3, (y - y0) / 1e3)))
k = p.field(c, px, py, 2, 0) if axis == 'x' else p.field(c, px, py, 0, 2)
eps = (1 if face == 'F' else -1) * k * PM.T / 2

# mid standoff out of plane by delta: C c = d (delta at (42, 59.5)), energy minimised on the null space
cp = np.linalg.pinv(np.array(p.C)) @ d; y = -np.linalg.solve(Z.T @ p.K @ Z, Z.T @ p.K @ cp); c = cp + Z @ y
```

The pcbnew scripts did the following:
- listed Edge.Cuts and the holes;
- measured each hole's courtyard and pad distances (`SHAPE.Collide` bisection) and non-GND tracks, vias and fills on
  every copper layer within 5 mm;
- measured courtyard to leg-pad distances for J30 / J31;
- found exposed top pads within 2 mm of the staked parts' fit_check model boxes;
- diffed footprints and vias between `fc3d5b34…` (the fix pass's backup) and `4f841a0e…`.

Scratch copies lived under `scratchpad/r9review/mech2/` and were deleted after this report.
