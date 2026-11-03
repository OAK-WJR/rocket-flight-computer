# R8 review pass 3: DFM, fit and mechanical (independent review)

This is a read-only review, done 2026-10-20, of the R8 board after fix pass 2. The worktree is
`rocket-flight-computer-r8`, branch `m3-assy-r8`, uncommitted, on top of R7 `431025d`.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18`. I checked the hash before and after the runs; it
  did not change.
- **Coordinates:** KiCad mm, with y = 0 at the aft edge. In the Gerbers, Y = −y.
- **Repository changes:** none except this file. `git status --short` was the same before and after every tool run.
- **Comparison boards** (read only): fix pass 1's `6600ef94…`, extracted from fix pass 2's own snapshot
  (`scratch fix2/pre_fix2_state.tgz`, SHA-256 checked), and R7's `c872a3d3…` in `../rocket-flight-computer-r7` (opened
  with `pcbnew.LoadBoard` only; nothing written there).
- **Inference** marks anything not measured and not taken from a maker document (AGENTS §2.5).

## 1. Summary

**Critical 0, Major 0, Minor 3 (one worth fixing, records only).**

The fab package is consistent and bound to `990c8040…`:
- `tools/check.sh` exits 0: DRC 0 at every severity, unconnected 0, parity 0, ERC 0; audit OK; silk OK; `check_r8`
  OK; route_check r8 0 failing / 3 allowlisted; actuators OK; fit OK.
- `export_fab.py --out <scratch>` gives a BOM (`be711876…`) and CPL (`25cfed69…`) byte-identical to `fab/`.
- All 14 Gerber, drill and job files equal `fab/m3_gerber.zip` once the date lines are removed. The assembly PDFs
  differ in 3 bytes each, the creation date.
- `fab_manifest.py`, `paste_check.py` and `jlc_orient.py --verify-cpl` report OK.
- The five DFM test suites (89 tests) pass.

All three pass-2 DFM findings are closed or properly dispositioned (§2). Fix pass 2 introduced no DFM regression:
- The only placement change is R81, whose CPL row is the only changed row. It passes R5 L10 at 1.575 mm from J121.1.
- The eight new or moved vias have no ring on a paste aperture and no hole near an opening.
- J123.2's relief resolves 2 / 4 / 4 spokes, and DRC passes.
- The right forward tab and the hole at (42, 114.4) now carry GND on all four layers, as ORDERING says.
- I re-ran the plate model on this board's `fit_check` report: it reproduces `plate_r8.json` exactly, every value but
  the board SHA.

The three Minor items:
1. **R8P3-DFM-01 (worth fixing, records only):** the records name a GND via as ACT_GATE's nearest GND copper, but the
   GND pour is closer.
   - R8_VALIDATION C12b #19, its "Pyro review observations" row and its open-items line, and `fix2_handoff.md`'s
     candidate for pass 3, all treat step 7's GND via (15.0, 107.3), 0.180 mm from bare R120.2, as the nearest GND
     copper.
   - On the final copper the B.Cu GND pour is 0.150 mm from R120.2 and C120.2, and the F.Cu pour 0.151 mm from R121.1.
   - So the proposed fix, step 7's 0.5 mm via clearance for the actuator gate nets, would not change this exposure at
     all.
   - The class is R7's: there R121.1 and Q121.4 sit 0.150 mm from the pour, and the owner accepted it.
   - J1.4's row (C12b #26: 0.189 mm GND via) is the same: the pour is 0.151 mm from J1.4 on both faces.
2. **R8P3-DFM-02 (not worth fixing):** the `via_paste` ring clause, which R8P2-INTEGRITY-02 handed to this review.
   - 13 via–aperture pairs (12 vias) have a ring within 0.1 mm of a paste aperture, against R7's 5.
   - With mask expansion 0, the mask web between such a via and its pad is below JLC's 0.10 mm soldermask bridge.
   - Every pair is on the via's own net, and every such via is tented. The worst pair (0.025 mm) is the same as R7's
     worst. A lost web wets a same-net ring; it cannot short anything.
   - Verdict: keep the gate as it is and record the class. Tightening to R7's rule would move 12 vias for no electrical
     gain.
3. **R8P3-DFM-03 (not worth fixing):** Q123's pin-1 dot sits on R162.2's mask opening.
   - The dot is a footprint silkscreen circle (bottom), and it overlaps R162.2's opening by 0.065 mm (0.012 mm²).
   - The Gerber export clips it, so no ink reaches the pad. In CAD, though, it is silkscreen on a pad (REQUIREMENTS M2).
   - It is R8-new (since R162 moved, D57). KiCad's `silk_over_copper` does not report it, and the project's silkscreen
     gates measure text only.

## 2. Previous pass in this dimension: closure on `990c8040…`

| Pass-2 ID | Fix-pass disposition | Measured on `990c8040…` | Status |
|---|---|---|---|
| R8P2-DFM-01 (J123.2 solid on a non-reproducible `starved_thermal`) | Relieved in `r8_ground.py` `RELIEF_PADS` before the native fill; `make_ground` models it; D89 / C17 / `r8_pcb.py` comment / ORDERING §4 corrected (D101) | J123.2 local zone connection −1 (INHERITED: GND zones THT_THERMAL on F / B / In2, THERMAL on In1). Spokes sampled at r + 0.2 mm: F.Cu 45/135/225/315°, In1 the same, B.Cu 135/225° (2, the project's `min_resolved_spokes`); In2 is the 3V3 region (antipad). DRC 0 at every severity. ORDERING §4's hole-fill list (J122.2/3/5/6/8/9/11/12, J1.1, J124.2) equals the board's FULL set (`thtzc.py`); J1.2, J3.1–J3.4 and J123.2 relieved. D89, C17, D101, the `r8_pcb.py` comment and REQUIREMENTS M2's pointer agree | **Closed** |
| R8P2-DFM-02 (J1's `1:BAT+` legend aft of the body) | Accepted, not changed (R8_VALIDATION) | Legend unchanged at (27.86–33.40, 103.35–105.05); `terminal_legends` passes | **Dispositioned** (recorded) |
| R8P2-DFM-03 (tab table names J9; C83 not named for J3) | ORDERING §3 note; §4 and §5 J3 steps name C83 | ORDERING l. 75 explains the window search leaves out J30 / J31 and gives J31 at about 11.4 mm (measured 11.47 mm). §4 l. 97 and §5 l. 139 say "keep the iron off C83, the bottom-side 0603 1.5 mm from J3.1's slot" (C83–J3.1 1.514 mm) | **Closed** |

**Other pass-2 items touching this dimension:**
- **R8P2-POWER-02 (In2 BAT_IN trim):** the In2 BAT_IN fill is now x 12.40–33.50, y 100.30–112.60, 229.6 mm².
  - The right forward tab span (y 105–110) is GND fill on all four layers at 0.5 mm.
  - The hole at (42, 114.4) is GND on all four layers from 2.10 mm.
  - ORDERING §3 and §7 say so.
- **R8P2-ROUTING-01 (0.5 mm vias):** the board now has 310 vias at Ø0.6 / 0.3 and 299 at Ø0.5 / 0.3.
  - The ring is 0.1 mm, inside JLC's multilayer via minimum (0.15 / 0.25 mm hole / diameter, below).
  - Via hole to hole is at least 0.30 mm (JLC 0.2 mm).
- **R8P2-INTEGRITY-02:** handed to this review; see R8P3-DFM-02.

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P3-DFM-01 | Minor (worth fixing: records only) | AGENTS §3 / §2.5 (measured reasons); REQUIREMENTS M2 (deviation list accuracy) | **The records name a GND via as the nearest GND copper to the actuator gate, but the GND pour is closer, so the pass-3 candidate fix would not reduce the exposure.** The via in question is step 7's grid via (15.0, 107.3), Ø0.5, `r8_ground.tsv` l. 125, basis `grid`, 0.180 mm from bare R120.2 (ACT_GATE). These records treat it as ACT_GATE's nearest GND copper: R8_VALIDATION C12b #19 (l. 379), the pyro-observations ACT_GATE row (l. 492), the open-items line (l. 519) and `fix2_handoff.md` l. 60 ("candidate for pass 3: give `make_ground.clearance` the actuator gate nets"). On the final copper, **the outer GND pour already sits at the board's 0.150 mm clearance from three bare ACT_GATE pads**: R120.2 and C120.2 on B.Cu, and R121.1 on F.Cu. A GND bridge there turns the actuator switch on with the power switch open (R8_VALIDATION's own consequence). Moving or dropping the via therefore changes nothing; closing the class needs a pour rule. The class is R7's, owner-accepted: R121.1 and Q121.4 at 0.150 mm on R7's copper. The same holds for J1.4 (BAT_SW_RETURN): C12b #26 gives the GND via (14.7, 112.0) at 0.189 mm, while the pour is 0.151 mm from J1.4 on F.Cu and B.Cu (R7 B.Cu 0.151 mm). J123.1 (PULLPIN_EXT) is the same: via (10.05, 75.3) 0.20 mm, pour 0.150 mm. These two vias are the closest foreign vias to any through-hole pad on the board (R7's closest 0.275 mm), but not the closest GND copper. The mask web at each pad is the gap itself (mask expansion 0), above JLC's 0.10 mm soldermask bridge, so a bridge needs a mask breach (Inference: the general basis of the board's 0.15 mm default) | `nearfill.py` (zone filled polygons, distance from pad outline): R120.2 0.150 mm to GND_B fill vertex (14.720, 106.926); C120.2 0.150 to (11.899, 106.994); R121.1 0.151 to GND_F (13.837, 100.448); J1.4 0.151 on F and B; J123.1 0.150 on F and B. On R7: R121.1 0.151, Q121.4 0.150; R120.2 2.582, C120.2 2.806. Via ring to pad: `dfm2.py` R120.2 0.180, J1.4 0.190, J123.1 0.200 (THT list, `polys*.json`: R7 nearest foreign via to a THT pad 0.275 mm, J122.10–SERVO1_MCU). `make_ground.clearance` (l. 152–171) gives THT pads more than 0.15 mm only for RAW_ACT (as the dru's "RAW_ACT pins to pours" rule, R5 pass 4: "hand-soldered … a bridge there shorts the servo feed to GND") | Records only: in C12b #19 / #26, the pyro-observations ACT_GATE row and the open-items line, give the nearest GND copper as the pour at 0.150 mm (R120.2, C120.2, R121.1; R7: R121.1, Q121.4), and drop the via-only candidate (it is not the nearest copper). If the owner wants the class closed, it takes a pour rule like "RAW_ACT pins to pours", say ACT_GATE pads to GND zones ≥ 0.3 mm, plus the same net in `make_ground.clearance`. That is an owner choice; R7 accepted the class, and ORDERING §5's "RAW_ACT dead with the switch open, link out and in" step screens it |
| R8P3-DFM-02 | Minor (not worth fixing) | REQUIREMENTS M2 (paste per IPC-7525 practice; design rules within JLC's limits); R8P2-INTEGRITY-02 hand-over | **The `via_paste` ring clause: verdict.** `check_r8.via_paste` fails a ring on an aperture (0 mm) and a hole within 0.1 mm; R7's `ViaCheck` kept the whole ring 0.1 mm clear. On `990c8040…`, 13 via–aperture pairs at 12 vias are closer than 0.1 mm (R7: 5 strictly under, 4 more at exactly 0.1 at U30's T-pads). With the board's 0 mm mask expansion, the mask web between each via ring and its pad's opening equals that gap, 0.025–0.09 mm, below JLC's 0.10 mm soldermask bridge (green, 1 oz). JLC can therefore lose the web, leaving a sliver of the via ring beside the pad opening. Every pair is on the via's own net (no short is possible), and every one of these vias is within 0.35 mm of an opening, so it is tented, not ink-plugged (ORDERING §4; JLC's plugged-via rule). The effect is at most solder wetting onto a same-net ring, a smaller fillet on a 0402 / 0603 passive or U10.3 / U12.4 (Inference). The worst (C90.1, 0.025 mm) equals R7's worst (R81.2 / R125.2, 0.025 / 0.030 mm). Tightening the gate to R7's rule would move 12 vias, most of them pitch- or pour-bound (D87, C12), for no electrical gain | `vp.py` (ring to paste aperture) and the mask-web scan: C90.1 0.025 (3V3 (34.8, 53.68), B), C7.1 0.033 (VLOGIC (35.65, 66.6), B), C60.2 0.050, U10.3 0.050, D4.2 0.064, C300.2 0.070, R71.2 / R72.1 0.073 (one CAM_FB via), C93.1 0.075, R165.2 0.075, R76.1 0.075, R310.1 0.087, C76.2 0.090; R7: R81.2 0.025, R125.2 0.030, C87.2 0.050, R100.1 0.055, R130.2 0.062 (U9.4 0.091 by the mask scan). Vias with the ring within 0.35 mm of any opening: R8 201, R7 258. JLC capabilities: "Soldermask Bridge 0.10 mm (green, 1 oz)"; plugged vias "keep at least 0.35 mm from other mask openings" | Keep the gate as it is. Record the class in R8_VALIDATION (the INTEGRITY-02 row and the open-items line): 13 own-net tented pairs with a sub-0.10 mm mask web, worst 0.025 mm as R7; JLC may remove the web; no short. Optional, cheap: ratchet `via_paste` to fail any new pair under 0.1 mm beyond these 13 |
| R8P3-DFM-03 | Minor (not worth fixing) | REQUIREMENTS M2 ("Silkscreen … never on pads"); AGENTS §3 silkscreen | **Q123's pin-1 dot lies on R162.2's mask opening.** Q123 (SOT-23, bottom, (16.0, 66.4)) carries a filled Ø0.4 mm silkscreen circle at (17.0, 64.65), outside its own courtyard (y ≥ 64.905). R162 (bottom, (16.4, 62.95), rot 270, D57) puts pad 2's opening at y ≤ 64.516, so the dot overlaps it by 0.065 mm (0.012 mm² by pcbnew `BooleanIntersection`). The Gerber export subtracts the mask (`--subtract-soldermask`, ORDERING §2), so no ink reaches the pad, but the remaining dot butts against R162.2's edge, inside JLC's 0.15 mm pad-to-silkscreen distance, and JLC's CAM may trim it further. R8-new (R7's nearest foreign footprint silk was 0.125 mm, J124 at R132 / R175); unchanged since step 4. Not reported by KiCad 10.0.6 DRC (`silk_over_copper` is enabled at warning; the run reports 0), nor by `silk_check` / `check_r8` / pass 1–2's text-ink scans | `q123.py`: R162.2 B.Mask box x 15.711–17.088, y 63.383–64.516; dot box x 16.801–17.199, y 64.451–64.849; overlap 0.01198 mm². `silkforeign.py` (every silkscreen polygon against other parts' openings): R8 one overlap (this), next 0.125 mm; R7 none under 0.125 mm; fix pass 1 board `6600ef94…` the same overlap. Bottom silkscreen Gerber draws the dot (X 16.9–17.1, Y −64.65) | Record it as an M2 silkscreen deviation in M3_R8 §"Silkscreen" / R8_VALIDATION part C (cosmetic; the output is clipped). At the next placement change in the buzzer group, move R162 at least 0.2 mm aft (dot 0.15 mm clear). Optionally extend `silk_check` to footprint graphics against other parts' openings |

## 4. Fab package (regenerated and compared)

- **`tools/check.sh`** (KiCad Python, exit 0):
  - DRC 0 / unconnected 0 / parity 0 / ERC 0;
  - audit OK; silkscreen outside the outline 0;
  - R8 CAD contract OK; route_check r8 0 failing, 3 allowlisted, 0 leftovers;
  - actuators OK; fit OK.
- **Export:** `python3 tools/export_fab.py --out <scratch>` reports:
  - 92 BOM lines, 219 placed parts;
  - no part without an LCSC code; no owner-fitted part;
  - DNP C303, C304, C305, C313, C314;
  - every CPL row corrected.

  BOM `be711876…` and CPL `25cfed69…` are byte-identical to `fab/`. The 14 Gerber, drill and job files match once the
  date lines are removed; the PDFs differ in 3 bytes (the date).
- **CPL change since pass 2:** one row, `R81,41.2450mm,-91.0000mm,Bottom,180` → `R81,39.6000mm,-91.2750mm,Bottom,90`.
  It matches `r8_place.tsv` (39.6, 91.275, 90, B), and `--verify-cpl` rebuilds it (85 top / 126 bottom, worst 0.491 mm,
  8 placement-only, no errors).
- **`fab_manifest.py`:** OK, 5 outputs. The library, `.kicad_pro`, `.kicad_dru` and `fp-lib-table` are unchanged from
  `431025d` (`git diff --stat` empty).
- **`paste_check.py`:** OK. F 348 / 348, B 359 / 359, 20 dry pads (J30 / J31 and the DNP lands).
- **Drill:**
  - PTH: 609 × 0.300 (vias; 310 Ø0.6, 299 Ø0.5), 4 × 0.600 (J3's slots, G85), 2 × 0.8, 12 × 1.1, 8 × 1.6;
  - NPTH: 2 × 0.600 and 3 × 0.991;
  - the board outline is a rectangle plus seven Ø3.2 circles (5 M3, 2 tie).
  - The new island via (13.5455, 74.2255) is written as X13.545 Y−74.225 (decimal format, 3 places): 0.5 µm per axis,
    immaterial.
- **Procurement:** `check_procurement.py --cost-only` fails with "cost_check.json: BOM/CPL changed or report lacks
  input binding".
  - The BOM is unchanged, so this is the expected binding staleness: the CPL moved for C83 (fix pass 1) and R81 (fix
    pass 2). ORDERING §1 l. 29, M3_R8 and R8_VALIDATION say so and require `FAB_NET=1 m3_design/r8_fab.sh` within 24 h
    of ordering.
  - The recorded figures are $106.00 per board and 52 of 52 Extended codes (the M3 limit, no margin).
  - U4 is consigned and U30 is to be reserved.

  This is properly dispositioned (network run not repeated, read-only review).
- **Tests (KiCad Python):** `test_paste_check` 5, `test_fit_check` 23, `test_fab_validation` 23, `test_procurement`
  15, `test_r8_check` 23, all OK.

## 5. Footprints, paste, mask, vias, silkscreen

- **Via in pad / via to opening:** only TP122's via (A8) has its hole in an opening (−0.90 mm). No other via hole edge
  lies within 0.15 mm of a pad opening. 93 vias have their hole edge within 0.35 mm of an opening (pass 2: 93).
- **Fix pass 2's new and moved vias** (`bdiff.py` against `6600ef94…`):

  | Via | Nearest foreign pad (ring) | Nearest opening (hole) |
  |---|---|---|
  | GND (13.5455, 74.2255), island | J123.1 1.463 mm | own-net J123.2 0.375 mm |
  | GND (44.65, 86.775), U9.8 pad stage | R84.1 0.497 mm | own-net R84.2 0.413 mm |
  | GND (38.85, 91.3), moved | R81.1 0.317 mm | 0.417 mm |
  | GND (42.9, 91.45), moved | TP89.1 1.028 mm | 1.128 mm |
  | Ø0.6 → Ø0.5 at (33.9, 45.2), (41.4, 47.8), (41.45, 32.6), (35.25, 60.5) | 0.320 mm or more | 0.225 mm or more |

  None has a ring on a paste aperture.
- **Plated-hole clearances** (`pthclr.py`, every layer, tracks, vias, pads and fills):
  - every component hole edge is ≥ 0.40 mm from foreign copper (J122's signal pins to F.Cu GND), against JLC's "PTH to
    track 0.28 mm";
  - NPTH: J3's locating holes 0.201 mm (HRO's layout; ORDERING's expected query) and J2's 0.251 mm, both ≥ JLC's
    "NPTH to track 0.2 mm".
- **Hole to hole:** via to via ≥ 0.300 mm (JLC 0.2 mm). Via to plated hole: the nearest is the island via to J123.2,
  0.674 mm edge to edge (JLC pad hole-to-hole 0.45 mm).
- **Paste and mask:**
  - The only zero mask webs are Q120's and Q121's same-net drain fingers; U4 keeps its 0.100 mm webs.
  - The minimum copper gap between pads of different parts is 0.324 mm (R175.1–R132.2, rigid CH1).
  - Paste margins: as pass 2 (33 ratio-margin pad sides, no effect on any via).
- **R5 L10** (bottom courtyards to foreign THT rings, ≥ 1.5 mm gated): D8–J121.2 1.502, C83–J3.1 1.514, R80–J1.3
  1.527, R165–J1.4 1.569, **R81–J121.1 1.575** (new with D100; R8_VALIDATION records R81.1–J121.1 1.825 mm bare to bare,
  in the pyro observations), R120–J1.4 1.583 mm. ORDERING §4's generic "bottom-side parts sit from 1.5 mm" covers R81.
- **THT zone connections:**
  - FULL: J122.2 / 5 / 8 / 11, J124.2 (RAW_ACT), J1.1 (BAT_IN), J122.3 / 6 / 9 / 12 (local FULL).
  - Relieved: J1.2, J3.1–J3.4, J123.2.
  - ORDERING §4 matches.
- **Silkscreen:**
  - 168 designators shown, 81 hidden. The hidden set equals M3_R8's list, including R84 (D102).
  - 5 top-part designators sit on the bottom (C95, Q124, R128, R133, TP30).
  - 35 board legends, every text 1.0 mm tall with a 0.15 mm stroke (JLC: ≥ 1.0 mm, ≥ 0.15 mm).
  - Text ink: none within 0.1 mm of an opening, none over a via ring, no text–text overlap.
  - `r7_post.courtyard_offenders` is empty. R81's designator (B) is 0.055 mm from its own courtyard and 0.361 mm from
    R82's.
  - The closest ink to an edge is 0.176 mm (TP90's mark), as in passes 1 and 2.
  - Footprint graphics against foreign openings: R8P3-DFM-03.
- **Order mark and legends:** no via or silkscreen moved near `JLCJLCJLCJLC` (16.13–26.67, 96.55–98.25). The legends
  list equals pass 2's.
- **MEMS (P3):** `IMU_body_B` and `BARO_body_B` (B.Cu, no via, no fill) are in place; no via under U4 or U5.

## 6. Fit, supports, hardware, vibration, SMA

- **fit_check** (in `check.sh`): J9 mated 0.03 mm, J122 mated 0.71, J3 0.89, J121 / J124 1.15, C84 1.37 mm.
  - Worst bottom margin 2.36 mm (C91); deepest part L1, z −4.62 mm.
  - Nearest bottom item to a support: R12.1, 4.452 mm from (4, 64). Nearest top item: TP30.1, 5.008 mm.
  - Wire room 6.3–6.9 mm.
  - All equal to pass 2 and to ORDERING §7 / M3_R8 "Mechanical". R81 (0603, bottom, x 39.6) is far inside the bore
    envelope.
- **Supports** (`supports.py`):

  | Support | Copper and nearest items |
  |---|---|
  | (4, 4) | GND on all four layers from 2.10 mm; nearest U30's courtyard 4.58 mm and TP30.1 5.01 mm |
  | (42.3, 4) | GND on all four layers; no pad or courtyard within 6 mm |
  | (4, 64) | F / In1 / B GND, In2 3V3; nearest U5's courtyard 4.14 mm, R12.1 / R12.2 4.45 mm, LS120.3 5.10 mm |
  | (4, 114.4) | GND on all four layers; no pad or courtyard within 6 mm |
  | (42, 114.4) | **GND on all four layers since D97** (pass 2: In2 BAT_IN); no pad or courtyard within 6 mm |

  This matches ORDERING §7: nylon hardware, washers ≤ 7.0 mm OD, standoffs ≤ Ø6.4 mm and ≥ 3.5 mm tall.
- **Bottom power pours** (ORDERING §7 Sled row; per-layer fill extents) all match:
  - RAW_ACT x 0.50–16.50, y 81.80–108.00 and x 19.85–25.10, y 70.90–86.90;
  - ACT_FET_S x 9.60–14.78, y 97.60–106.63;
  - BAT_IN x 15.02–41.30, y 98.60–112.60.
- **Vibration (D75, C10):** I re-ran `step9/plate_model.py` (numpy 2.0.2 in a scratch virtual environment) on this
  run's `fit_check --report` of `990c8040…`.
  - Every value equals `step9/evidence/plate_r8.json` except `board_sha256`.
  - f1 209 / 295 / 346 / 490 Hz (plugs on the sled), 173–379 Hz (plugs on the jacks).
  - So R8_VALIDATION's "not re-run, only R81 moved" is borne out.
  - D75 / C10 stays properly dispositioned to the owner: C84 on the mode-1 antinode (−16.6 Hz), about +17 Hz if moved,
    no sixth support ruling for R8.
- **SMA retention:** J30 / J31 and the strip are rigid (12 / 12 digests, `check_r8` OK). ORDERING §4 / §5 / §7 and
  REQUIREMENTS P3 are unchanged: counter-hold, torque, saddle on the plug axis, staking after the RF tests, the
  leg-fillet and D30 / D31 / C302 inspection, and the 1.7 mm slot fit.

## 7. Panel and tabs

| Tab | Nearest part | 5 mm class | Connector | Hole edge | Copper at the span (per layer) |
|---|---|---|---|---|---|
| L 63–68 | U5 7.87 | C32 8.34 | J123 10.46 | 2.40 | F / In1 / B GND, In2 3V3 at 0.5; GND vias 1.04 |
| L 112.5–117.5 | Q121 8.15 | C120 12.70 | J1 11.96 | 2.40 | GND on all four at 0.5 |
| R 8–13 | C310 8.45 | C310 8.45 | J31 11.47 (J9 in the window search) | 3.85 | GND on all four; GND vias 0.70 |
| R 18–23 | C73 5.20 | C73 5.20 | J9 16.48 | 12.88 | GND on all four; GND vias 0.70 |
| R 105–110 | TP88 2.44 | C96 5.97 | J121 8.00 | 4.35 | **GND on all four at 0.5 (since D97)**; GND vias 1.31 |

- `r8_place_check.tab_windows` gives left (0.5, 6.0), (48.5, 77.25), (86.25, 117.5) and right (0.5, 23.0),
  (104.25, 117.5). That equals ORDERING §3, and every planned tab lies inside a window.
- All five spans keep ORDERING's rules: 1.5 mm to parts, 5 mm to the capacitor / R166 / LED2 / RF-module class, 2 mm to
  connectors, 1.5 mm to holes.
- JLC's mouse-bite tab minimum is 5 mm (capabilities page, below). Five tabs without a forward rail remain a quote-time
  confirmation (ORDERING §3, Inference).

## 8. Sources

- JLCPCB PCB capabilities, https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-10-20):
  - Soldermask Bridge 0.10 mm (green, 1 oz); Soldermask Expansion 1:1, ≥ 0.09 mm opening-to-trace;
  - multilayer via 0.15 mm hole / 0.25 mm diameter; via hole-to-hole 0.2 mm, pad hole-to-hole 0.45 mm;
  - via hole to track 0.2 mm; pad to track 0.1 mm; PTH to track 0.28 mm (0.35 recommended); NPTH to track 0.2 mm;
  - routed edge ≥ 0.2 mm;
  - plugged vias: no mask opening, ≤ 0.5 mm, "keep at least 0.35 mm from other mask openings";
  - silkscreen line ≥ 0.15 mm, text ≥ 1.0 mm, pad to silkscreen 0.15 mm;
  - breakaway tab with mouse bites ≥ 5 mm.
- KiCad 10.0.6 DRC (`--severity-all`; `silk_over_copper` at warning in `m3.kicad_pro`); project rules `m3.kicad_dru`
  l. 5–9 (hole clearance 0.25 mm), l. 96–99 ("RAW_ACT pins to pours", 0.3 mm, R5 pass 4).
- Project files:
  - `docs/ORDERING.md` l. 29, 52–79, 97, 139–140, 206–207;
  - `docs/REQUIREMENTS.md` M1–M3, P2, P3;
  - `docs/R8_VALIDATION.md` l. 118, 129, 220–224, 379, 394, 492, 519;
  - `docs/M3_R8.md` l. 161–177, 352, 412–448, 500–527;
  - `R8_DECISIONS.md` D57, D75, D87, D97–D102;
  - `m3_design/r8_ground.tsv` l. 95, 102, 125, 131; `step7/make_ground.py` l. 74, 152–171;
  - `tools/check_r8.py` l. 702–743;
  - `fix2_handoff.md` l. 58–62; `fix2_generators.diff`.

## 9. Inferences

- That a lost sub-0.10 mm mask web only wets a same-net via ring and slightly reduces the fillet (R8P3-DFM-02).
- That a bridge from a bare pad to masked copper 0.150–0.200 mm away needs a mask breach (R8P3-DFM-01): this is the
  basis of the board-wide 0.15 mm default.
- Whether JLC accepts five tabs without a forward rail (ORDERING's quote-time confirmation).
- The plate model's inputs (as recorded in D75).

## 10. Method (reproducible, read-only)

**Scripts.** KiCad 10.0.6 Python (`pcbnew.LoadBoard`; no board was saved). The scripts are in the session scratchpad
`r8p3dfm/`. Pass 2's set is reused: `polys.py`, `geom.py`, `dfm1.py`, `silk1.py`, `silkedge.py`, `legends.py`,
`desig.py`, `inv2.py`, `tabd.py`, `tabcu.py`, `tw.py`, `supports.py`, `thtzc.py`, `relief.py`, `l10.py`, `outline.py`.
New in this pass:
- `bdiff.py`: vias, tracks, footprints, pad zone connections and zone outlines, `6600ef94…` against `990c8040…`;
- `dfm2.py`: via ring and hole against foreign pad copper and openings;
- `vp.py`: ring to paste and the tenting count, R7 against R8;
- `pthclr.py`: plated and NPTH hole edges to foreign copper on every layer;
- `silkpad.py`, `silkforeign.py`, `q123.py`: silkscreen against openings;
- `desnear2.py`, `co.py`: designator subjects (`r7_post.courtyard_offenders`);
- `padfill.py`, `nearfill.py`, `netpads.py`: GND fill and via distance from named pads, R7 against R8;
- `vctx.py`: zone context of a via;
- `bpours.py`: pour extents;
- `mems.py`.

**Tool runs:**
- `tools/check.sh`;
- `tools/export_fab.py --out <scratch>`, then diffs of the BOM, CPL, Gerbers, drills, job file and PDFs;
- `tools/fab_manifest.py`; `tools/paste_check.py`; `tools/jlc_orient.py --verify-cpl`;
- `tools/check_procurement.py --cost-only`;
- `tools/fit_check.py --report <scratch>`, then `step9/plate_model.py` on it;
- the five unit-test suites in §4.

The scratch copies (the extracted pass-2 board, the regenerated package, the virtual environment) were deleted after the
run.
