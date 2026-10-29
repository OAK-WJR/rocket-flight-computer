# R8 review pass 2: DFM, fit and mechanical (independent review)

This is a read-only review, done 2026-10-19, of the R8 board after fix pass 1. The worktree is
`rocket-flight-computer-r8`, branch `m3-assy-r8`, uncommitted, on top of R7 `431025d`.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d`. I checked the hash before and after every run, and
  it did not change.
- **Coordinates:** KiCad mm, with y = 0 at the aft edge. In the Gerbers, Y = −y.
- **Repository changes:** none except this file. `git status --short` was the same before and after.
- **Experiments:** every experiment that changed copper ran on scratch copies in the session scratchpad, and those copies
  are now deleted.
- **Inference** marks anything not measured and not taken from a maker document (AGENTS §2.5).

## 1. Summary

**Critical 0, Major 0, Minor 3 (one worth fixing).**

The fab package is consistent and bound to `6600ef94…`:
- `tools/check.sh` exits 0.
- `export_fab.py` regenerated into scratch gives a byte-identical BOM and CPL.
- The Gerbers, drill files and job file are identical once the date lines are removed. The assembly PDFs differ only in
  3 bytes (their creation date).
- `fab_manifest.py`, `paste_check.py` and `jlc_orient.py --verify-cpl` all report OK.
- The five DFM-related test suites (89 tests) are OK.

All four pass-1 DFM findings are closed (§2), and fix pass 1 introduced no via-on-paste, edge, mask or silkscreen
regression. I re-ran the plate model on this board's `fit_check` report: it reproduces `plate_r8.json` exactly, every
value but the board SHA (§6).

The three Minor items:
1. **R8P2-DFM-01 (worth fixing):** J123.2 stays solid on F.Cu, In1 and B.Cu because "KiCad DRC reports `starved_thermal`
   on B.Cu" (D89, C17). That does not hold on the final board.
   - I gave J123.2 the standard THT relief on a scratch copy of `6600ef94…` and refilled natively.
   - The result: DRC 0 at every severity, `check_r8` OK and route_check OK. B.Cu has 2 resolved spokes, which meets
     `min_resolved_spokes` 2, and F.Cu and In1 have at least 4 each.
   - So REQUIREMENTS M2's relief rule applies to J123.2, and the recorded exception's reason is wrong.
   - C17's J122 wording ("starved on B.Cu") is also inexact: B.Cu has at least 4 spokes, and the thin layer is F.Cu. The
     current reason (the 7.7 A return) still keeps J122 solid.
2. **R8P2-DFM-02:** J1's `1:BAT+` legend sits aft of the 14.5 mm terminal body, while `2:GND`, `3:SW` and `4:SW` sit on the
   wire-entry strip. It fits there too. Cosmetic.
3. **R8P2-DFM-03:** documentation details.
   - ORDERING §3's tab table gives the right aft tab's nearest connector as J9 26.42 mm. It is J31, about 11.4 mm away:
     `tab_windows` skips J30 and J31 by design, and the table does not say so.
   - C83's new spot (1.51 mm from J3.1, the slot ORDERING asks to be hand-finished) is not named in the J3 rework steps.

## 2. Previous pass in this dimension: closure on `6600ef94…`

| Pass-1 ID | Fix-pass disposition | Measured on `6600ef94…` | Status |
|---|---|---|---|
| R8P1-DFM-01 (U30's T-paste and C7.1 over vias) | Vias at y 8.3; V_VLOGIC at (35.65, 66.6); gate `check_r8.via_paste` + seeded test (D87) | My scan of every via against every paste polygon finds no ring overlapping an aperture. The nearest rings: C90.1 0.025 mm (3V3 (34.8, 53.68), as in R7), C7.1 0.033 mm (VLOGIC (35.65, 66.6)), C60.2 / U10.3 0.050 mm. The limiter vias (11.51 / 10.41, 8.3) have rings 0.15 mm and hole edges 0.25 mm from U30's T apertures (y ≥ 8.70). No via hole edge lies within 0.15 mm of a pad opening except TP122's in-pad via (A8). The gate's evidence: 705 pairs, nearest 0.025 mm. `test_r8_check` 23 OK, including the seeded `ring overlaps` / `within 0.1 mm` / `C7.1's paste` cases (l. 283–290) | **Closed** |
| R8P1-DFM-02 (left forward tab on the 7.7 A band) | `TAB_PLAN` left (112.5, 117.5); ORDERING §3 table and remark (D93) | `tab_windows` (run read-only): left (0.5, 6.0), (48.5, 77.25), (86.25, 117.5); right (0.5, 23.0), (104.25, 117.5). The plan is inside them. The per-layer copper of the L 112.5–117.5 span is GND fill on all four layers at 0.5 mm, with no via or track within 1.5 mm. Polygon distances: Q121 8.15 mm, C120 12.70, J1 11.96, hole edge 2.40 mm (ORDERING's box figures 8.08 / 12.64 / 11.90 are conservative). The outline has square corners, so the span ends on straight edge | **Closed** |
| R8P1-DFM-03 (solid THT GND pins) | J3.1 / J3.4 thermal; J123.2 kept solid "(DRC `starved_thermal`, C17)" (D89) | J3.1 / J3.4 inherit THT_THERMAL (`GetLocalZoneConnection` −1); DRC passes, with ≥ 3 spokes on F.Cu and B.Cu and ≥ 4 on In1. **J123.2's recorded reason does not reproduce on the final board** (R8P2-DFM-01) | **J3 closed; J123.2 reopened as R8P2-DFM-01** |
| R8P1-DFM-04 (documentation) | ORDERING / D35 / D39 corrected | ORDERING §5: J2's locating hole 0.84 mm and pads 1.32 mm from the edge. §7: "C84 (12.8 mm, the tallest part at the bore wall; J1, 14.5 mm, sits on the axis)". §5 coating: U4 "west of U1". D35 and D39 carry "(step-4 values; final …)" | **Closed** |

The R7 pass-3 DFM and mechanical items pass 1 closed stay closed. Fix pass 1 touched none of their evidence: the order
mark, the J2 pads, the strip parts, the silkscreen rules, the SMA torque and saddle, and `fit_check`'s bottom pads. I
re-measured the order mark: ink to the nearest via ring 0.151 mm (GND (26.875, 97.875)), Q120.9's opening 1.49 mm, the
J124 note 0.275 mm, all as ORDERING §3 says.

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P2-DFM-01 | Minor (worth fixing) | REQUIREMENTS M2 ("Through-hole GND pins use thermal reliefs wherever their spokes are not starved"); AGENTS §3 (measured reasons) | **J123.2 is solid on a "starved" reason the final board does not reproduce.** D89 (R8_DECISIONS l. 1935–1941), R8_VALIDATION C17 (l. 228), the `r8_pcb.py` comment (l. 179–185) and ORDERING §4 (l. 97) keep J123.2 (pull-pin GND, (13.20, 75.40), 0.8 mm hole, Ø1.4 ring) solid on F.Cu, In1 and B.Cu. They say KiCad's DRC reports `starved_thermal` on B.Cu with the 0.5 mm / 45° relief. The progress log shows that DRC came from the **status-family stage gate** (step 6), before step 7's GND vias and refill. On `6600ef94…` the same relief is legal: B.Cu resolves 2 spokes (the two west diagonals, between J123.1 and the PULLPIN lane), and F.Cu and In1 resolve at least 4. A cold or open joint at this pin reads as the pull-pin being pulled, a false launch detect on the pad (Inference). Solid joints into three planes are the harder ones to hole-fill by hand or selective soldering, which is why ORDERING lists the pin for a hole-fill check. **J122 wording (same record):** C17 / D89 say J122's GND pins are "starved on B.Cu (1–2 of 8 directions)". That figure came from sampling the solid fill (pass 1's `spokes.py`), not a relief. With reliefs, J122.3 resolves 1 spoke on F.Cu (starved), and J122.6 / 9 / 12 resolve 2 on F.Cu and In2 and at least 4 on B.Cu. J122 rightly stays solid, but for the 7.7 A servo return, not for B.Cu starvation | Scratch copy of `6600ef94…` (with `.kicad_pro` / `.kicad_dru`): J123.2 `SetLocalZoneConnection(INHERITED)` (the GND zones give THT_THERMAL, 0.5 mm gap, 0.5 mm spokes), `ZONE_FILLER.Fill` on all zones, saved, then `kicad-cli pcb drc --severity-all`: **0 violations, 0 unconnected** (with `kilib` linked in; without it, only `lib_footprint_issues`). `check_r8`: OK. `route_check --profile r8`: 0 failing, 3 allowlisted. Same with 90° spokes (B 2, F 3, In1 3). **Control 1:** the same board with `min_resolved_spokes` raised to 3 gives `starved_thermal … PTH pad 2 [GND] of J123 … layer B.Cu; min spoke count 3; actual 2`, so the test runs and J123.2 has exactly 2 spokes on B.Cu. **Control 2:** reliefs on J122.3 / 6 / 9 / 12 with min 2 gives one violation: `J122 pad 3, layer F.Cu, actual 1`. With min 4: J122.6 / 9 / 12 F.Cu 2, In2 2; J3.1 / J3.4 F.Cu 3, B.Cu 3; no J122 B.Cu entry. Zone connections read with pcbnew: J123.2 local FULL (2); GND zones F / B / In2 THT_THERMAL (3), In1 THERMAL (1) | Give J123.2 the THT relief where the final GND copper exists, not in step 4: in `m3_design/r8_ground.py`, set it to INHERITED before the native refill (l. 146–149). That is exactly the configuration I tested. Then rebuild twice and rerun `check.sh` and `r8_fab.sh`. Then correct D89, C17, the `r8_pcb.py` comment and ORDERING §4 l. 97: drop J123.2 from the hole-fill list, and give J122's reason as "the 7.7 A servo return; J122.3 also starved on F.Cu". If the owner prefers J123.2 solid, record a true reason instead; the present one is not measured on this board |
| R8P2-DFM-02 | Minor (not worth fixing) | REQUIREMENTS F8 / M2 (terminal legends legible, a legend by its part) | **J1's battery-positive legend is the one J1 legend not on the wire-entry side.** D92 moved `2:GND`, `3:SW` and `4:SW` to the forward strip at y 116.8, in front of J1's wire entry. `1:BAT+` stays at (30.63, 104.2), aft of the terminal body (Fab y 104.83–116.17, 14.5 mm tall). So someone wiring the battery lead from the forward edge sees legends in front of pins 2–4 and none in front of pin 1. It is still legible from above and nearest its own pin (gate evidence 5.35 mm against J1.2's 5.83 mm), and U9 survives a reversed 2S. Cosmetic | Board silkscreen: `1:BAT+` box x 27.86–33.40, y 103.35–105.05; `2:GND` box x 23.19–27.91, y 115.95–117.65. Forward-strip occupancy at x 28.3–35.0, y 115.6–118.0: only the GND via rings (31.0, 115.3) and (35.0, 115.3), which reach y 115.6. No mask opening, no other silkscreen, and no courtyard but J1's (to y 116.09) | Optional: in `r8_post.py`, place `1:BAT+` in the strip at about x 28.5–34.0, y 116.8. That keeps 0.6 mm from `2:GND`'s ink (the run-on rule), clears the via rings and stays nearest J1.1 (box geometry: about 5.55 mm against about 6.3 mm to J1.2). `check_r8.terminal_legends` re-judges it |
| R8P2-DFM-03 | Minor | Record accuracy (AGENTS §3) | **Documentation details.** (a) ORDERING §3 table l. 71 gives the right aft tab (y 8–13) the nearest connector "J9, 26.42 mm". J31's courtyard (x 28.0–35.09, y −9.79–4.70) is about 11.4 mm away. `r8_place_check.tab_windows` skips J30 / J31 (l. 183–184), so the table never sees them. JLC's 2 mm rule still holds by a wide margin. (b) Fix pass 1 put C83 (bottom 0603, (9.55, 36.0)) 1.514 mm from J3.1's ring (6.31, 37.92), the board's second-closest R5 L10 pair after D8–J121.2's 1.502 mm. J3.1 is a slot that ORDERING §4 (l. 97) and §5 (l. 139) tell the bench to hand-finish "with extra solder" from both faces. The generic "bottom-side parts sit from 1.5 mm" covers it, but neither step names C83 | Polygon distances from my `tabd.py` (pads and courtyards of every footprint). `l10.py`: bottom courtyards to foreign THT rings | (a) Change the cell to "J31, 11.4 mm", or note under the table that the SMA jacks are left out of the window search (aft edge, overhanging). (b) Add "C83 (bottom, 1.5 mm from J3.1)" to the J3 hand-finish steps as the part to keep the iron off |

## 4. Fab package (regenerated and compared)

- **`tools/check.sh`** (rerun, exit 0, 60 s):
  - DRC 0, unconnected 0, parity 0, ERC 0;
  - audit OK; silkscreen outside the outline 0;
  - R8 CAD contract OK;
  - route_check r8: 0 failing, 3 allowlisted;
  - actuators OK; fit_check OK.
- **Export:** `python3 tools/export_fab.py --out <scratch>` reports:
  - 92 BOM lines, 219 placed parts;
  - no part without an LCSC code; no owner-fitted part;
  - DNP placeholders C303, C304, C305, C313, C314;
  - every CPL row corrected.

  The BOM (`be711876…`) and CPL (`c0ee08ae…`) are byte-identical to `fab/`. All 14 Gerber, drill and job files match
  `fab/m3_gerber.zip` once the date lines are removed. The assembly PDFs differ in 3 bytes, the creation date.
- **`fab_manifest.py`:** OK, 5 outputs bound to `6600ef94…`. `git diff --stat 431025d` on `kilib/`, `.kicad_pro`,
  `.kicad_dru` and `fp-lib-table` is empty, so the footprints, apertures and rules are R7's. `kilib/` holds no stray file
  (the accidental `kilib/kilib` link in fix pass 1's log is gone).
- **`paste_check.py`:** OK. F 348 flashes on 348 pasted pads, B 359 on 359, 20 dry pads (J30 / J31, C303 / C304 / C305 /
  C313 / C314).
- **`jlc_orient.py --verify-cpl`:** 85 top and 126 bottom rows rebuilt, worst residual 0.491 mm, 8 placement-only rows,
  no errors. C83's row `9.5500mm,-36.0000mm,Bottom,90` is among them.
- **Part counts** (pcbnew): 89 top and 130 bottom placed parts; test pads 5 top (TP30, TP75, TP76, TP84, TP121) and 19
  bottom, as ORDERING §4 says. C83 was already a bottom part, so the counts did not move.
- **Drill:**
  - PTH: 607 vias at 0.300 (equal to the board: 314 at Ø0.6, 293 at Ø0.5), 4 × 0.6 (J3 legs), 2 × 0.8, 12 × 1.1,
    8 × 1.6;
  - NPTH: J3's 2 × 0.600 and J2's 3 × 0.991.
- **Job file:** M3-ASSY-R8, 4 layers, 1.6 mm, ENIG; stackup 0.035 / 0.203 / 0.030 / 1.03 / 0.030 / 0.203 / 0.035.
- **Procurement:** `check_procurement.py --cost-only` now **fails** ("cost_check.json: BOM/CPL changed or report lacks
  input binding"), because fix pass 1 changed C83's CPL row.
  - ORDERING §1, M3_R8 and R8_VALIDATION all say so.
  - The BOM is R7's line for line ($106.00, 52 of 52 extended codes on 2026-10-19 23:51Z).
  - A `FAB_NET=1 m3_design/r8_fab.sh` run is due within 24 h of ordering anyway.

  This is properly dispositioned, not a finding. U4 stays short and consigned, and U30 is to be reserved.
- **Tests (KiCad Python):** `test_paste_check` 5, `test_fit_check` 23, `test_fab_validation` 23, `test_procurement`
  15, `test_r8_check` 23, all OK.

## 5. Footprints, paste, mask, vias, silkscreen

- **Via in pad / via to opening:**
  - Only TP122's via (A8) has its hole in an opening.
  - No other via hole edge lies within 0.15 mm of a pad opening.
  - 93 vias have their hole edge within 0.35 mm of an opening (pass 1: 95), all tented per ORDERING §4.
  - Fix pass 1's moved vias: HSE_OUT (24.69, 47.5) 0.24 mm from C26.1; its GND partner 0.52 mm; V_VLOGIC 0.18 mm from
    C7.1; CAM_MCU_RX hop (33.95, 44.0) 0.20 mm from U12.4.
- **Paste margins:** 33 pad-sides use ratio margins with x ≠ y (Q120 / Q121 drain fingers, U4, U9, U7.9).
  `check_r8.paste_polys` inflates by `margin.x` alone, so for U4.1–4 / 8–11 and U9's small pads it under-sizes the
  aperture by at most 0.007 mm on the short side; elsewhere it errs large. The nearest via to any such pad is far beyond
  that. Not a finding.
- **Mask webs:** the only zero webs are Q120's and Q121's same-net drain fingers. U4 keeps its 0.100 mm webs.
- **Pad gaps:** the minimum copper gap between pads of different parts is 0.324 mm (R175.1–R132.2, the rigid CH1 block).
- **R5 L10:** bottom courtyards to foreign THT rings are at least 1.502 mm (D8–J121.2). C83 is now second at 1.514 mm
  from J3.1 (R8P2-DFM-03(b)).
- **THT zone connections:**
  - FULL: J122.2 / 5 / 8 / 11 (RAW_ACT zones), J124.2 (RAW_ACT), J1.1 (BAT_IN), J122.3 / 6 / 9 / 12 and J123.2 (local
    FULL).
  - Thermal: J1.2 and J3.1–J3.4.

  ORDERING §4's hole-fill list matches the board; J123.2's reason does not (R8P2-DFM-01).
- **Silkscreen:**
  - 169 designators are shown and 80 hidden; the hidden set equals M3_R8's list (set difference empty).
  - 5 top-part designators are on the bottom: C95, Q124, R128, R133, TP30.
  - 35 board legends, every text 1.0 mm tall with a 0.15 mm stroke.
  - No ink lies within 0.1 mm of a mask opening, over a via ring, or within 0.15 mm of another text.
  - The closest ink to an edge is 0.176 mm (TP90's mark) and 0.216 mm (C72's designator), as in pass 1.
- **Terminal legends** (D92): each of the 10 is nearest its own pin (gate evidence). The tightest margins are `1:BAT+`
  (5.35 against 5.83 mm) and `2:RAW` (6.21 against J123.1's 6.69 mm).
  - J1's three forward legends (y 115.95–117.65) clear J1's body (Fab to y 116.17) except a 0.2 mm overlap of their
    boxes, and keep about 0.55 mm of ink from the forward edge.
  - J124 / J121 polarity legends are low-stakes: the ARM link and the igniter are not polarised.

## 6. Fit, supports, hardware, vibration, SMA

- **fit_check** (in `check.sh`): J9 mated 0.03 mm, J122 mated 0.71, J3 0.89, J121 / J124 1.15, C84 1.37 mm.
  - Worst bottom margin 2.36 mm (C91, L1, C81, D9); deepest part L1, z −4.62 (3.02 mm below the bottom face).
  - Nearest bottom item to a support: R12.1, 4.452 mm from (4, 64). Nearest top item: TP30.1, 5.008 mm.
  - Wire room 6.3–6.9 mm.
  - All equal to pass 1 and to ORDERING / M3_R8. C83 at x 9.55 on the bottom is far inside the bore.
- **Supports** (`supports.py`):

  | Support | Inner layers | Nearest items |
  |---|---|---|
  | (4, 4), (42.3, 4), (4, 114.4) | GND on every layer from 2.10 mm | U30's courtyard 4.58 mm and TP30.1 5.01 mm from (4, 4) |
  | (4, 64) | In2 3V3 | U5's courtyard 4.14 mm |
  | (42, 114.4) | In2 BAT_IN | — |

  - This matches ORDERING §7: nylon hardware, washers ≤ 7.0 mm OD, standoffs ≤ Ø6.4 and ≥ 3.5 mm tall.
  - The terminals' pin tails are not in the CAD models (J1 / J121 / J124 / J123 boxes start at z 0). From typical
    DB128 / PH lead lengths they protrude about 2 mm, inside L1's 3.02 mm (Inference, unchanged from R7).
- **Vibration (D75, C10):** I re-ran `step9/plate_model.py` (numpy 2.0.2 in a scratch virtual environment) on this run's
  `fit_check --report` of `6600ef94…`.
  - **69 of 69 values equal `step9/evidence/plate_r8.json`, all but `board_sha256`.**
  - f1 209 / 295 / 346 / 490 Hz (plugs on the sled), 173–379 Hz (plugs on the jacks).
  - So R8_VALIDATION's "not re-run, C83 not an input" is borne out: C83's 3 mg of distributed mass moves nothing at the
    recorded precision.
  - D75's disposition stands: no requirement sets an f1 floor, and C10 puts the sixth-support ruling to the owner, with
    C84's antinode position (−16.6 Hz) and the ~17 Hz gain from moving it recorded. This is properly dispositioned.
- **SMA retention:** J30 / J31 and the strip are rigid (12 / 12 digests, `check_r8` OK). ORDERING §4 / §5 / §7 and
  REQUIREMENTS P3 keep everything else as in R7:
  - counter-hold, with 0.8–1.13 N·m or the plug maker's lower value;
  - the saddle on the plug axis;
  - staking after the RF tests;
  - the leg-fillet and D30 / D31 / C302 inspection;
  - the 1.7 mm slot fit.

## 7. Panel and tabs

| Tab | Nearest part | Nearest 5 mm-class part | Nearest connector | Hole edge | Copper at the span (per layer) |
|---|---|---|---|---|---|
| L 63–68 | U5 7.87 | C32 8.34 | J123 10.46 | 2.40 | F / In1 / B GND, In2 3V3 at 0.5; GND vias 1.04 |
| L 112.5–117.5 | Q121 8.15 | C120 12.70 | J1 11.96 | 2.40 | GND on all four at 0.5; nothing else within 1.5 |
| R 8–13 | C310 8.45 | C310 8.45 | **J31 11.47** (ORDERING: J9 26.42) | 3.85 | GND on all four; GND vias 0.70 |
| R 18–23 | C73 5.20 | C73 5.20 | J9 16.48 | 12.88 | GND on all four; GND vias 0.70 |
| R 105–110 | TP88 2.44 | C96 5.97 | J121 8.00 | 4.35 | F / In1 / B GND, In2 BAT_IN at 0.5; GND vias 1.31 |

- All five spans are legal under ORDERING's rules: 1.5 mm to parts, 5 mm to the capacitor / R166 / LED2 / RF-module
  class, 2 mm to connectors, 1.5 mm to holes.
- The outline is a plain rectangle with square corners, with the five M3 and two tie holes as Edge.Cuts circles.
- Rail removal: the pads within 1.6 mm of a long edge are J9 0.50, TP90 0.50, TP74 / TP88 0.65, J2 0.84 (locating hole),
  C81 0.845, L1 0.90, C91 0.93, TP89 0.95, C8 / C9 0.995, TP72 1.05, R91 1.225, J3 1.23, TP30 1.25, C87 1.25, C72 / C73
  1.44 and R92 1.475 mm. ORDERING §5's list names the closest of them. No pad lies within 1.6 mm of the forward edge.

## 8. Sources

- JLCPCB mouse bites (tab count, width, 1.5 mm part and 2 mm connector clearance, ≥ 0.5 mm copper keep-out):
  https://jlcpcb.com/blog/pcb-mouse-bites, as cited in ORDERING §3 and pass 1.
- KiCad 10.0.6 DRC `starved_thermal` and `min_resolved_spokes` (the project's `m3.kicad_pro` l. 122 and l. 151;
  `thermal_relief_gap` 0.5 / `thermal_relief_spoke_width` 0.5, l. 68–69), exercised directly in the controls of
  R8P2-DFM-01.
- Project files:
  - `docs/ORDERING.md` l. 29, 59–79, 97, 100, 139–140, 206–207;
  - `docs/REQUIREMENTS.md` P2, P3, M1–M3;
  - `docs/R8_VALIDATION.md` l. 116–166 (review pass 1), l. 221 (C10), l. 228 (C17);
  - `R8_DECISIONS.md` D35, D39, D71, D75, D87, D89 (l. 1935–1941), D92, D93;
  - `m3_design/r8_pcb.py` l. 179–193; `m3_design/r8_ground.py` l. 129–149; `m3_design/r8_place_check.py` l. 59–65,
    178–221;
  - `tools/check_r8.py` l. 105–112, 697–760, 1120–1122; `tools/test_r8_check.py` l. 260–310;
  - `fix1_progress.md` ("status DRC starved_thermal J123.2 B.Cu").

## 9. Inferences

- That an open or cold J123.2 joint reads as a pulled pin, and that a relief eases hole fill (R8P2-DFM-01).
- The terminals' pin-tail protrusion (about 2 mm) from typical lead lengths.
- The plate model's inputs (as recorded in D75).
- Whether JLC accepts five tabs without a forward rail (ORDERING keeps it as a quote-time confirmation).

## 10. Method (reproducible, read-only)

**Scripts.** KiCad 10.0.6 Python (`pcbnew.LoadBoard`; the repository board was never saved). The scripts are in the
session scratchpad `r8p2dfm/`, copied from pass 1's `r8p1dfm/` and extended:
- `polys.py` and `geom.py`: pad copper, mask and paste polygons, vias, silk ink and courtyards;
- `dfm1.py`: via to mask and paste, mask webs, pad gaps;
- `silk1.py`, `silkedge.py`: silkscreen;
- `legends.py`, `desig.py`: legends and the hidden list;
- `tabcu.py`, `tabd.py`, `tw.py`: tab copper, tab clearances and `tab_windows`;
- `spokes.py`, `in2pin.py`, `thtzc.py`, `relief.py`: THT connections and relief spokes;
- `l10.py`: R5 L10;
- `supports.py`;
- `pm.py`: ratio paste margins;
- `inv2.py`: part counts;
- `outline.py`.

**Experiments** (scratch copies of `6600ef94…` with `m3.kicad_pro` / `m3.kicad_dru`, deleted after the run):
- `exp_j123.py` and `exp_multi.py`: set the pad's zone connection to INHERITED (and the spoke angle), then
  `pcbnew.ZONE_FILLER(b).Fill(b.Zones())`, save, and `kicad-cli pcb drc --severity-all`;
- then `tools/check_r8.py` (with `kilib` linked beside the copy) and `tools/route_check.py --profile r8` on the copy;
- controls with `min_resolved_spokes` 3 and 4.

**Tool runs:**
- `tools/check.sh`;
- `tools/export_fab.py --out <scratch>` and the Gerber, drill, job and PDF diffs;
- `tools/fab_manifest.py`;
- `tools/paste_check.py`;
- `tools/jlc_orient.py --verify-cpl`;
- `tools/check_procurement.py --cost-only`;
- `tools/fit_check.py --report <scratch>`;
- `step9/plate_model.py <scratch fit report>`;
- the five unit-test suites in §4.
