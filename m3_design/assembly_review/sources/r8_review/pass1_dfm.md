# R8 review pass 1: DFM, fit and mechanical (independent review)

This is a read-only review, done 2026-10-19, of the R8 board as built by steps 0–9. The worktree is
`rocket-flight-computer-r8` on branch `m3-assy-r8`, uncommitted, on top of R7 `431025d`.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987`. The hash was checked before and after every run
  and did not change.
- **Comparison board:** R7, `git show 431025d:…/m3.kicad_pcb` (`c872a3d3…`), as a scratch copy.
- **Coordinates:** KiCad mm, with y = 0 at the aft edge. In the Gerbers, Y = −y.
- **Repository changes:** none except this file. `git status` was the same before and after, apart from the other
  reviewers' reports that appeared in this folder.
- **Inference** marks anything not measured and not taken from a maker document (AGENTS §2.5).

## 1. Summary

**Critical 0, Major 0, Minor 4.**

The R8 fab package is consistent and bound to the board:
- `tools/check.sh` exits 0.
- `export_fab.py` regenerated into scratch gives a byte-identical BOM and CPL, and Gerbers, drill and job files that
  are identical apart from their dates.
- `fab_manifest.py` OK; `paste_check.py` OK; `jlc_orient.py --verify-cpl` OK.
- `check_procurement.py --cost-only` OK.
- The BOM is byte-identical to R7's: $106.00 per board, 52 extended codes.
- The five tab windows are legal, and I reproduced each one independently.
- `fit_check` passes, and every category is at or above R7's.
- The vibration estimate reproduces exactly (§6).
- All ten R7 pass-3 DFM and mechanical findings stay closed on R8 (§2).
- R8 also clears several R7 compromises:
  - no via in any J2 pad;
  - R5 L10 met everywhere (R7 had 8 violations, closest 0.66 mm);
  - no text over a via;
  - the order mark is placed by the build.

The four Minor items:
1. **R8P1-DFM-01:** a regression of R7's DFM-07 fix. U30's T-shaped paste apertures for pins 13 and 14 now print
   directly over the GNSS_LNA_EN and GNSS_VCC_RF vias. Separately, the VLOGIC via's ring overlaps C7.1's pasted pad. No
   gate checks vias against paste: R7's rule lived only in `r7_route.ViaCheck`.
2. **R8P1-DFM-02:** the left forward tab (y 100–105) sits on the 7.7 A RAW_ACT pours of three layers and is 4.4 mm from
   Q121. A legal GND-only window exists at y 112.5–117.5. Moving the tab changes only ORDERING and TAB_PLAN.
3. **R8P1-DFM-03:** full (solid) zone connections inherited from R5 on THT GND pins that R8 moved (J123.2, J3 legs 1
   and 4). R5's "starved spokes" reason no longer holds, so REQUIREMENTS M2 asks for thermal reliefs there. ORDERING's
   "GND pins on all four layers" holds for J122 only.
4. **R8P1-DFM-04:** documentation details in ORDERING and two step-4 records.

## 2. Previous pass in this dimension: closure on R8

R8 had no previous review. The previous pass in this dimension is R7's pass 3 (`pass3_dfm.md`, `pass3_mechanical.md`),
dispositioned in `R7_VALIDATION.md` l. 343–359.

| R7 ID | R7 disposition | On R8 `429b6db4…` | Status |
|---|---|---|---|
| P3-DFM-01 (DNP list, test-pad counts) | Fixed | ORDERING §1 lists C303, C304, C305, C313 and C314, which is exactly what `export_fab.py` reports (rerun). §4 gives 5 top TPs (TP30, TP75, TP76, TP84, TP121) and 19 bottom, as on the board. The paste remark names the five pasteless lands. `paste_check`: 20 dry pads | Closed |
| P3-DFM-02 (stale cost and stock) | Fixed | ORDERING §1 is consistent with the bound reports. `cost_check.json` (23:51:04Z, bound to the BOM/CPL SHA-256s `be71…`/`d265…`, equal to the files): $106.00 per board, $77.85 parts, 52 extended codes. `stock_check.json` (23:50:07Z): U4 short, none thin | Closed |
| P3-DFM-03 (order mark, tab table) | Fixed | `JLCJLCJLCJLC` is at B (21.4, 97.4), placed `required` by `r8_post`. Measured: ink to the nearest via ring 0.151 mm (GND (26.875, 97.875)), 1.490 mm to Q120.9's opening, 0.275 mm to the J124 note, all as ORDERING says. The tab table matches my polygon measurements within 0.07 mm (ORDERING uses boxes, so it is conservative) | Closed |
| P3-DFM-04 (via in J2.1) | Documented | Gone. No via hole lies in or within 0.35 mm of any J2 pad. The nearest are the same-net feed vias (0.8, 42.75) NRST and (0.8, 44.02) GND: ring 0.271 mm from the pad, hole 0.42 mm. REQUIREMENTS M2 says the exception lapses | Closed |
| P3-DFM-05 (D30/D31/C302 tombstoning) | Done (records) | The strip is rigid (check_r8 digests). ORDERING §5 keeps the first-article inspection | Closed |
| P3-DFM-06 (silkscreen nits) | Fixed | R8 redrew the silkscreen (§5). No text ink lies over a via ring or within 0.1 mm of a mask opening, and no two texts come within 0.15 mm. GNSS (8.15, 3.0) and RADIO (35.74, 6.2) are present. The BOM comment reads "GNSS ANT SMA; RADIO ANT SMA". The hidden list equals M3_R8's 81 refs (set difference empty) | Closed |
| P3-MECHANICAL-01 (SMA torque) | Fixed | REQUIREMENTS P3 and ORDERING §5/§7 give 0.8–1.13 N·m (Kinghelm p. 1) or the plug maker's lower value | Closed |
| P3-MECHANICAL-02 (tie share, saddle) | Fixed | ORDERING §7 sets the saddle on the plug axis. P3 keeps "relieves most, not all" | Closed |
| P3-MECHANICAL-03 (VEHICLE row) | Proposed | The parent row still says M3-ASSY-R7, without J1's entry or the standoff height. `r8_step9_handoff.md` §"Proposed parent VEHICLE.md" carries both (D84). It stays a parent-repository item | Properly dispositioned |
| P3-MECHANICAL-04 (fit_check skipped bare bottom pads) | Fixed | `tools/fit_check.py` l. 300–303 add exposed bottom pads of board features and DNP footprints. `test_fit_check`: 23 OK | Closed |

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P1-DFM-01 | Minor (worth fixing) | REQUIREMENTS M2 (paste per maker guidance); R7 pass-2 DFM-07, fixed in R7 (`R7_VALIDATION` l. 214: "ViaCheck keeps vias 0.1 mm from paste apertures; the two vias under U30's paste extensions are gone"); ORDERING §4 via remark | **U30's T-paste prints over two vias again: a regression from R7.** R8's limiter (`r8_route_rf.py` l. 170–189, D51) drops pins 13 and 14 through vias at (11.51, 8.9) and (10.41, 8.9), "just outside" the pads, which end at y 9.3. That is inside u-blox's T-shaped paste extensions, the paste-only pads 0.8 × 1.4 mm at (11.51 / 10.41, 9.4), y 8.70–10.10. Each 0.3 mm hole (y 8.75–9.05) lies entirely inside its stencil opening. The hole edge is 0.25 mm from the pad opening, so ORDERING §4's own rule ("within 0.35 mm of a pad: tent them") makes these tented, not ink-plugged, vias. So paste is printed onto a tented hole on the module's VCC_RF (antenna-bias supply) and LNA_EN castellations. Solder can be pulled into the via, leaving a starved castellation joint or solder balls. Same net, so no short; the cost is GNSS antenna bias or LNA enable (tracking only, not safety). R7 had these two vias at (x, 8.3), 0.10 mm outside the apertures. **Second instance:** V_VLOGIC (35.5, 66.6) (`r8_power.py` l. 311, 0.6 mm via). Its ring overlaps C7.1's pasted pad corner by 0.044 mm, and its hole edge is only 0.106 mm from the opening (M2's 0.1 mm is met by 6 µm). **Cause:** R7's paste rule lived only in `r7_route.ViaCheck` (l. 523), a routing helper. No R8 generator or gate checks it: `paste_check.py` matches flashes to pads only, and check_r8 has no via–paste rule | Gerbers in `fab/m3_gerber.zip`: `m3-F_Paste.gbr` l. 551–552 flash D42 (`R,0.8×1.4`) at X11.51/X10.41 Y−9.4; `m3-PTH.drl` l. 159 X10.41Y−8.9 and l. 179 X11.51Y−8.9 (T1 0.300). pcbnew: U30 at (10.41, 14.95) rot 90; U30.13 / U30.14 copper y 9.30–11.10; via ring Ø0.5. My scan of every via against every paste polygon: R8 has three overlaps (−0.45, −0.45, −0.044 mm), R7 has none (closest +0.025 mm). R7 `r7_route.py` l. 242–248 put the vias at (10.41 / 11.51, 8.3). C7: 0805 at (34.75, 64.65) B, pad 1 corner (35.425, 66.355); via centre to corner 0.256 mm against a 0.300 mm ring radius | (1) In `r8_route_rf.py` set `V_LNA_EN, V_VCC_RF = (11.51, 8.3), (10.41, 8.3)`, R7's spots. The ring is then 0.15 mm from the apertures. Only own-net copper lies within 0.8 mm of either spot, and the GND stitches (12.61, 8.3) and (9.025, 8.325) are R7's. Update `route_check` ROUTE_FIGURES for A2 and A3: about +1.2 mm each, so roughly 7.65 / 6.20 mm (Inference), against R7's 7.45 / 6.2 mm. (2) Move V_VLOGIC about 0.05 mm north, to (35.5, 66.65), where only VLOGIC copper lies within 0.8 mm. (3) Port the rule to a gate: in check_r8 (or `paste_check`), no via hole within 0.1 mm of a paste aperture and no via ring overlapping one, with a seeded test. Rebuild and rerun the strip digests |
| R8P1-DFM-02 | Minor (worth fixing) | ORDERING §3 tab rules; JLC mouse-bite guidance ("critical traces and components at least 1.5 mm from the nearest tab edge"; copper keep-out ≥ 0.5 mm) | **The left forward tab sits on the 7.7 A battery band.** For y 100–105 at x = 0, RAW_ACT fills run on F.Cu, B.Cu and In2 to 0.5 mm from the edge, RAW_ACT vias are 1.0 mm away (column x 1.3), and Q121 (AON6403 DFN 5×6, the actuator switch carrying 7.7 A) is 4.41 mm away. That is above JLC's 1.5 mm part rule but below the 5 mm house margin ORDERING applies to capacitors, and it is the same flex-cracking mechanism. JLC's 0.5 mm copper keep-out is met, and rails are nibbled, not snapped, so this is margin, not a defect. The same window has a legal span at **y 112.5–117.5**: GND on all four layers, Q121 8.15 mm, J1 11.96 mm, C120 12.70 mm, hole (4, 114.4) edge 2.4 mm (the rule is 1.5). The right forward tab (y 105–110) sits over the In2 BAT_IN island at 0.5 mm. Every right-edge window forward of y 104 does, so that one stays, inner layer only | `r8_place_check.tab_windows(board)` (run read-only): left (0.5, 6.0), (48.5, 77.25), (86.25, 117.5); right (0.5, 23.0), (104.25, 117.5). My per-layer copper scan of each tab span (`tabcu.py`, filled polygons, tracks, vias): L 100–105: F/B/In2 RAW_ACT fill 0.5, RAW_ACT vias 1.0, In1 GND 0.5. L 112.5–117.5: F/In1/In2/B GND only, 0.5. R 105–110 and every right forward span: In2 BAT_IN 0.5. Courtyard polygons: Q121 4.41 mm (ORDERING's box figure 4.36 mm). `r8_place_check.py` l. 59–63 (TAB_PLAN, TAB_SOFT_REFS has no FETs) | Change TAB_PLAN left (100, 105) to (112.5, 117.5) and regenerate the ORDERING §3 table, the remark l. 100 (Gerber Y −117.5…−112.5) and §5. No copper change, so the board hash stays. Optionally add the power DFNs (Q120/Q121) to the 5 mm class |
| R8P1-DFM-03 | Minor (worth fixing) | REQUIREMENTS M2 ("Through-hole GND pins use thermal reliefs wherever their spokes are not starved (exceptions listed in M3_R4 §2)"); ORDERING §4 hole-fill remark | **Solid connections kept on moved THT GND pins whose spokes are no longer starved.** R5 set `FULL_PADS` (`r5_pcb.py` l. 773–785) because, in R5's layout, J123.2 sat "between J1's body and the hole" and J3 leg 1 "between the board edge, its own locating hole and the USB fan-out". (M3_R4 V16 had J3 leg 4 full for the same reason.) R8 moved J123 to (12.2, 75.4) and J3 to y 29–38, but the pads keep `zc = FULL`. Measured in R8: GND fill reaches 5–7 of 8 spoke directions on F.Cu and B.Cu at all three pins, so they are not starved. J123.2 (pull-pin GND, 0.8 mm hole) is hand- or selective-soldered solid to F/In1/B planes. A cold joint there reads as "pin pulled" (Inference). ORDERING already lists it for a hole-fill check. Also, ORDERING l. 97 says "the GND pins on all four layers". That is true for J122's GND pins (In2 GND reaches the ring), but J123.2 and J3 legs 1/4 are solid on F/In1/B only: In2 is the 3V3 region there, 0.95 / 0.85 mm away. J122.3/6/9/12 stay starved on B.Cu (1–2 of 8) and carry the servo return, so full is right for them | pcbnew `GetLocalZoneConnection`: J122.3/6/9/12, J123.2, J3.1, J3.4 = FULL (2); J1.2, J3.2, J3.3 inherit THT_THERMAL. `spokes.py` (fill sampled at ring + gap + 0.3 mm, 8 directions): J123.2 F 7/8, In1 7/8, B 5/8; J3.1 F 5/8, B 7/8; J3.4 F 6/8, B 7/8. `in2pin.py`: nearest In2 fill to J123.2 is 3V3 at 0.95 mm, to J3.1/J3.4 3V3 at 0.851 mm; J122 GND pins have In2 GND within 0.26 mm of the centre. R7 has the same overrides with spokes free too (J123.2 F 5/8, B 7/8), so this is inherited, but R8 re-placed both parts and never re-evaluated it (no R8 decision mentions it) | In the R8 build, clear the FULL override on J123.2, J3.1 and J3.4 so they inherit the THT thermal reliefs, then refill and rerun the gates. No 7.7 A copper is involved. Or record a measured reason for each in M3_R8. Either way, correct ORDERING l. 97 to "J122's GND pins on all four layers; J123.2 and J3 legs 1/4 on F.Cu, In1 and B.Cu" (or drop them if they become thermal) |
| R8P1-DFM-04 | Minor | Record accuracy (AGENTS §3) | **Documentation details.** (a) ORDERING §5 rail removal: "J2's contact pads sit 0.84 mm … from the left edge". The 0.84 mm is J2's NPTH locating hole (X1.334, Ø0.991). The contact pads are 1.32 mm from the edge. (b) ORDERING §7 Sled row: "C84, the tallest part" (carried from R7, pass3_mechanical §5). J1 (14.5 mm) and J121/J124 (14.4 mm) are taller; C84 (12.8 mm) is the tallest part *near the wall* (fit margin 1.37 mm). (c) ORDERING §5 coating: U4 "under U1's west edge". U4 (10.0, 53.8, bottom; body x ≈ 8.5–11.5) is about 3.5 mm west of U1's lead tips (U1 spans x ≈ 15–31), not under U1. M3_R8 says "west of U1". (d) R8_DECISIONS D35's window table (right y 0.5–25.5) and D39's "nearest bottom item 4.701 mm" are step-4 values. The final board gives 0.5–23.0 and 4.452 mm (R12.1), which ORDERING and M3_R8 already carry | pcbnew pads: J2 NPTH (1.334, 45.29) bbox x 0.839; contact pads x ≥ 1.321. fit_check rows: J1 z 14.5, J121/J124 14.4, C84 12.8. U4 position from the board. `tab_windows` output (R8P1-DFM-02 evidence); fit_check `nearest_support` 4.452 mm R12.1 | Fix the three ORDERING phrases. Mark D35's and D39's tables "(step 4; final values in ORDERING §3 / M3_R8)" |

## 4. Fab package (regenerated and compared)

- **`tools/check.sh`** (rerun, exit 0, 48 s):
  - DRC 0 at every severity, unconnected 0, parity 0, ERC 0;
  - metadata / 3D audit OK; silkscreen outside the outline 0;
  - check_r8 OK; route_check r8: 0 failing, 3 allowlisted;
  - check_actuators OK; fit_check OK.
- **Export:** `python3 tools/export_fab.py --out <scratch>` reports:
  - 92 BOM lines, 219 placed parts;
  - no LCSC code missing, no owner-fitted part, no uncorrected CPL row;
  - DNP placeholders C303, C304, C305, C313, C314.

  The BOM and CPL are byte-identical to `fab/`. All 11 Gerbers, both drill files and the job file are identical once
  the date lines are removed.
- **`fab_manifest.py`:** OK, 5 outputs, bound to `429b6db4…` and its library, rules and tool inputs. The library,
  `.kicad_pro` and `.kicad_dru` are unchanged since 431025d (`git diff --stat` empty), so every footprint, paste
  aperture and rule is R7's.
- **`paste_check.py`:** OK; F 348 flashes on 348 pasted pads, B 359 on 359, 20 dry pads. It does not look at vias
  (R8P1-DFM-01).
- **`jlc_orient.py --verify-cpl`:** 85 top and 126 bottom rows rebuilt, worst residual 0.491 mm, 8 placement-only rows,
  no errors. The CPL layer column holds 89 Top and 130 Bottom rows, matching the board.
- **Drill:**
  - PTH: 608 vias at 0.300 (equal to the board's via count), 4 × 0.6, 2 × 0.8, 12 × 1.1, 8 × 1.6;
  - NPTH: J3's 2 × 0.600 and J2's 3 × 0.991 only (TH1–TH3 are gone, as ORDERING §4 says).
- **Job file:** revision M3-ASSY-R8, 4 layers, 1.6 mm, ENIG; stackup 0.035 / 0.203 / 0.030 / 1.03 / 0.030 / 0.203 /
  0.035 (JLC041611-7628).
- **Assembly PDFs:** they carry R8's side changes (bottom: U3, U9, D9, C304; top: U12, D4, Q122, TP121).
- **Procurement:** `check_procurement.py --cost-only` OK ($106.00 per board; $77.85 with minimum purchases). The live
  supplier data is from today, so I did not query the API again. REQUIREMENTS M3 is met with no extended-code margin
  (52 of 52). U4 stays consigned.
- **Tests (KiCad Python):** `test_paste_check` 5, `test_fit_check` 23, `test_fab_validation` 23, `test_procurement`
  15, all OK.

## 5. Footprints, paste, mask, vias, silkscreen

- **Side changes:** 58 parts changed side (R7 → R8). To the bottom: U3, U9, D9, D122 and 27 passives. To the top: U12,
  D4, Q122, TP75, TP76, TP121 and 21 passives.
  - Heavy bottom parts by weight over pad area (masses from the plate model's lumped table, Inference): L3 21.5 g/in²
    (bottom in R7 too), U3 8.5, L1 8.6, D8 5.2, D9 4.6, Q120/Q121 1.9. All are under the usual 30 g/in² limit for a
    second, inverted reflow (Inference: industry rule of thumb, no JLC figure).
  - U3 (SOIC-8) is the only new IC on the bottom.
- **Via in pad (M2):**
  - Only TP122.1 (A8) has a via hole inside an opening.
  - The next closest is C7.1 at 0.106 mm (R8P1-DFM-01).
  - 95 vias have their hole edge within 0.35 mm of a pad opening (R7: 83). These are tented per ORDERING. JLC's 4-layer
    drill-to-pad minimum is 0 mm (as R7 pass 3 cited).
- **Via to paste:**
  - Three overlaps (R8P1-DFM-01).
  - Otherwise the closest via rings are C90.1 0.025, C60.2 0.050, U10.3 0.050, D4.2 0.064 and C300.2 0.070 mm, all
    outside the aperture.
- **Mask webs:**
  - None under 0.1 mm between different pads.
  - The only zero webs are the same-net drain fingers of Q120 and Q121.
  - U4 keeps its 0.100 mm webs.
- **Pad gaps:** the minimum copper gap between pads of different parts is 0.324 mm (R175.1–R132.2, the rigid CH1
  block).
- **R5 L10:**
  - Bottom courtyards to THT pad rings are at least 1.5 mm everywhere. The closest are D8–J121.2 1.502, R80–J1.3 1.527
    and R165–J1.4 1.569 mm.
  - R7 had eight violations, the closest R61–J123.1 at 0.659 mm. This is a real improvement for hand or selective THT
    soldering.
- **Small GND pads:** `check_r7.thermal_policy` (run by check_r8) passes, so the 0402/0603 GND pads have explicit
  thermal reliefs.
- **Silkscreen:**
  - 168 designators are shown and 81 hidden (equal to M3_R8's list); 35 board legends.
  - Every text is 1.0 mm tall with a 0.15 mm stroke. The thin silk lines are filled pin-1 marks only (0 width).
  - No ink lies within 0.1 mm of a mask opening, over a via ring, or within 0.15 mm of another text.
  - The closest ink to a board edge is 0.176 mm (TP90's footprint mark) and 0.216 mm (C72's designator); none lies
    outside the outline.
  - The terminal entry arrows are in the rigid J1/J121/J124 footprints.
- **TC2030 J2 on the west edge:**
  - From Tag-Connect's TC2030-IDC-NL drawing (sheet 2), the plug's nose is 7.24 × 3.81 mm and 6.0 mm long, and the
    9.9 × 6.1 mm body starts above it. J2's courtyard (4.09 × 7.09 mm) encloses the nose's footprint, and LED1/LED2
    (bodies from x 5.55, ≤ 0.95 mm tall) and J3 (3.25 mm) lie under the body's height, so the probe can seat
    (Inference from the drawing).
  - No track or via of another net lies within 0.508 mm of a contact pad, or in the keep-out between the pads (sheet 1,
    notes 1–2).

## 6. Fit, supports, hardware, vibration, SMA

- **fit_check:** radius 24.9 mm, sled tolerance 0.3 mm.
  - J9 mated 0.03 mm (= R7), J122 mated 0.71, J3 0.89, J121/J124 1.15, C84 1.37 mm (R7 0.11).
  - Worst bottom margin 2.36 mm (C91, L1, C81, D9); deepest part L1, 3.02 mm below the bottom face.
  - Nearest bottom item to a support: R12.1, 4.452 mm from (4, 64). Nearest top item: TP30.1, 5.008 mm from (4, 4).
  - Every category is at or above R7's (D39). I checked C84 by hand: corner (42.25 + 0.3, 12.8 + 0.3) lies 23.53 mm from
    the axis, a margin of 1.37 mm.
- **Supports** (`supports.py`, filled zones, tracks, vias, pads, courtyards):

  | Support | Copper within 4.5 mm | Nearest pads and courtyards |
  |---|---|---|
  | (4, 4), (42.3, 4), (4, 114.4) | GND on all layers from 2.100 mm | TP30.1 5.008 mm from (4, 4); nothing within 6.5 mm of the other two |
  | (4, 64) | In2 is **3V3** | U5 courtyard 4.138 mm (bottom), R12.1/.2 4.452 mm, LS120.3 5.096 mm |
  | (42, 114.4) | In2 is **BAT_IN** | nothing within 6.5 mm |

  - This matches ORDERING §7 "Mounting hardware": nylon, washers ≤ 7.0 mm OD, standoffs ≤ Ø6.4 mm and ≥ 3.5 mm tall.
  - Observation: U5 (MS5611) now sits 7.6 mm from the mid-span support's centre (R7: far from every support). Its
    courtyard clears the standoff and washer radius by 0.64 mm. Any shift from clamping stress is for the
    7-day barometer comparison to show (Inference; no TE figure found).
- **Tie path:** the J122 tie line (21.5, 68.6)–(27.0, 82.6) clears bottom courtyards by 2.263 mm (R150) and bottom pads
  by 2.585 mm. The 4 mm channel holds.
- **Sled data:** ORDERING §7's bottom-pour boxes match the R8 fills:
  - RAW_ACT 0.5–16.5 × 81.8–108.0 and 19.85–25.1 × 70.9–86.9;
  - ACT_FET_S 9.6–14.78 × 97.6–106.63;
  - BAT_IN 15.02–41.3 × 98.6–112.6.

  The probe points C24.1 (NRST, (25.33, 51.1)) and C15.1 (3V3, (29.2, 49.82)) are 4.08 mm apart. TP74 and TP88 are GND.
- **Vibration (D75, C10):** I re-ran `step9/plate_model.py` on this run's `fit_check` report, using numpy 2.5.4 in a
  scratch virtual environment.
  - It reproduces `step9/evidence/plate_r8.json` exactly: 57 values, 0 differences.
  - f1 with the plugs on the sled is 208.7 / 295.1 / 346.3 / 489.7 Hz; with the plugs on the jacks 173.2–379.4 Hz.
  - The 100 g deflection is 1.01 mm at (46, 62.5).
  - Miles' equation at 209 Hz, Q 10 gives 11.5 / 22.9 g rms at 0.04 / 0.16 g²/Hz, as the record says.
  - I agree with D75's disposition. No requirement sets an f1 floor, and C10 correctly puts the sixth-support
    rationale, which is now further from R6's level (13 % below), to the owner. Moving C84 toward a support (about
    +17 Hz) is a placement change, not a DFM item.
- **SMA retention:** J30, J31 and the strip are rigid (12/12 digests). ORDERING keeps all of these as in R7:
  - the counter-hold and torque (0.8–1.13 N·m);
  - the saddle on the plug axis;
  - staking after the RF tests;
  - the inspection of the leg fillets and of D30/D31/C302;
  - the 1.7 mm slot fit.

  U31's 100 g strain is 579 µε (R7 556); with the plugs on the jacks it is 893 µε (R7 872).

## 7. Panel and tabs

- **Windows:** `r8_place_check.tab_windows` gives left (0.5, 6.0), (48.5, 77.25), (86.25, 117.5) and right (0.5, 23.0),
  (104.25, 117.5), as in ORDERING. My polygon distances for each planned tab:

  | Tab | Nearest part | Nearest 5 mm-class part | Nearest connector | Hole edge |
  |---|---|---|---|---|
  | L 63–68 | U5 7.87 | C32 8.34 | J123 10.46 | 2.40 |
  | L 100–105 | Q121 4.41 | C120 11.81 | J124 4.79 | 8.62 |
  | R 8–13 | C310 8.45 | C310 8.45 | J9 26.48 | 3.85 |
  | R 18–23 | C73 5.20 | C73 5.20 | J9 16.48 | 12.88 |
  | R 105–110 | TP88 2.44 | C96 5.97 | J121 8.00 | 4.35 |

  All are legal. ORDERING's box figures are 0.05–0.07 mm smaller (conservative).
- **JLC's mouse-bite guidance** (https://jlcpcb.com/blog/pcb-mouse-bites) gives 4–6 tabs for a board over 100 mm,
  4–5 mm wide, 1.5 mm to components, 2 mm to connectors, and a copper keep-out of at least 0.5 mm. Five 5 mm tabs fit
  it. Whether five tabs suffice without a forward rail is JLC's call, and ORDERING keeps it as a pre-order confirmation
  (D35). The aft 63 mm of the left edge has no tab, as in R7. JLC's assembly fixture supports the board (Inference).
- **Edges:**
  - J3 overhangs the left edge by 0.45 mm (body) and 0.985 mm (courtyard); J9's courtyard ends at the right edge;
    V-cut is forbidden.
  - Copper near the long edges: J9's mounting pads and TP90 0.50 mm; TP74 and TP88 0.65; C81 0.845; L1 0.90; C91 0.93;
    TP89 0.95; C8/C9 0.995 mm. ORDERING §5's rail-removal list matches, except the J2 figure (R8P1-DFM-04(a)).

## 8. Sources

- JLCPCB mouse bites (tab count, width, 1.5 mm part and critical-trace clearance, 2 mm connector, ≥ 0.5 mm copper
  keep-out): https://jlcpcb.com/blog/pcb-mouse-bites
- Tag-Connect TC2030 No-Legs footprint drawing, rev B (pads, alignment holes, keep-out, notes 1–3):
  https://www.tag-connect.com/wp-content/uploads/bsk-pdf-manager/2026/07/NL-TC2030-Footprint.pdf
- Tag-Connect TC2030-IDC-NL cable drawing, sheet 2 (nose 0.285 × 0.150 in, 0.236 in long; body 0.39 × 0.240 in):
  https://cdn.hackaday.io/files/293411255325344/TC2030-IDC-NL.pdf
- JLC drill-to-pad on 4-layer boards and the via-plugging table: as cited in `r7_review/pass3_dfm.md` §5 (not
  re-read).
- Project files:
  - `docs/ORDERING.md` l. 29, 59–79, 83–122, 139–152, 205–206;
  - `docs/REQUIREMENTS.md` P2, P3, M1–M3;
  - `R8_DECISIONS.md` D8, D11, D35, D39, D51, D71, D72, D75, D81, D84;
  - `m3_design/r8_route_rf.py` l. 170–189; `m3_design/r8_power.py` l. 311; `m3_design/r8_place_check.py` l. 59–63,
    178–221;
  - `m3_design/r7_route.py` l. 242–248, 515–530; `m3_design/r5_pcb.py` l. 773–785;
  - `tools/paste_check.py`, `tools/check_r7.py` l. 748–773, `tools/fit_check.py` l. 296–320;
  - `docs/R7_VALIDATION.md` l. 208–236, 343–359; `docs/M3_R4.md` V16.

## 9. Inferences

- The solder-wicking and joint-starvation mechanism, and its likelihood, at a tented via under a stencil opening
  (R8P1-DFM-01).
- The A2/A3 length increase when the vias move to y 8.3.
- Flex-cracking risk at a nibbled tab 4.4 mm from a DFN (R8P1-DFM-02).
- That a cold J123.2 joint reads as "pin pulled", and the hole-fill benefit of thermal reliefs (R8P1-DFM-03).
- Bottom-part masses and the 30 g/in² rule.
- TC2030 probe seating, from the cable drawing.
- U5's sensitivity to clamping stress.
- The plate model's inputs (as recorded in D75).

## 10. Method (reproducible, read-only)

**Scripts.** KiCad 10.0.6 Python (`pcbnew.LoadBoard`, never saved); scripts in the session scratchpad `r8p1dfm/`,
deleted after the run except the small `.py` files:
- `inv.py`: footprint, pad, via, track, text and zone inventory, for R8 and R7;
- `polys.py` and `geom.py`: pad copper, mask and paste polygons, vias, silk ink and courtyards;
- `dfm1.py`: via to mask and paste, mask webs, pad gaps;
- `silk1.py`: silkscreen;
- `supports.py`: copper, pads and courtyards at the supports;
- `tabcu.py` (and its variants): per-layer copper at each tab span;
- `spokes.py`, `in2pin.py`: THT GND pin connections;
- `zfill.py`: zone fill boxes.

**Tool runs:**
- `tools/check.sh`;
- `tools/export_fab.py --out <scratch>` and the Gerber, drill and job diff;
- `tools/fab_manifest.py`;
- `tools/paste_check.py`;
- `tools/jlc_orient.py --verify-cpl`;
- `tools/check_procurement.py --cost-only`;
- `r8_place_check.tab_windows`;
- `step9/plate_model.py`;
- the four unit tests in §4.
