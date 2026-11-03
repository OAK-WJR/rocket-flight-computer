# R7 pass 3: DFM, assembly and fabrication package (independent review)

Read-only review, 2026-10-17, of the uncommitted R7 worktree (`m3-assy-r7`, base `3b215ba`) after the pass-2 fixes
(F1, F2, F3, docs, records). Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c` (checked before and after; unchanged), schematic
`47057f7d…`. Comparison board: the pass-2 board `03fe7572…6d54` (scratchpad copy `rg/r7.kicad_pcb`, hash checked).
Coordinates are KiCad mm (y = 0 aft edge); Gerber Y = −y.

## 1. Summary

The fab package is consistent with the final board and the board itself is DFM-clean. `tools/check.sh` exits 0 (rerun
here, including the new `route_check` stage). `export_fab.py` regenerated into scratch gives a byte-identical BOM and
CPL and identical Gerbers, drill and job files apart from creation dates. `fab_manifest.py` is OK, and
`jlc_orient.py --verify-cpl` passes. A native in-memory refill changes no zone area. The live JLC API (21:25Z) gives
52 Extended and 40 Basic codes, only U4 short, and `jlc_cost.py` gives $105.96 per board. No via hole lies in a
soldered pad opening and no via sits under paste. The DNP lands and SMA pads carry no paste. No two soldered pads of
different parts are closer than 0.3 mm, no mask web is under 0.1 mm, and no silkscreen ink is clipped by a pad
opening.

All eleven pass-2 DFM findings are closed or properly dispositioned (§2). The fix pass introduced no manufacturing
defect. What remains is documentation drift in ORDERING (C304, TP89, cost and stock, order-number mark), one
undispositioned sub-item of DFM-01 (J2.1), a thermal-balance trade-off from RF-02's solid grounds, and silkscreen
nits.

Findings: Critical 0, Major 0, Minor 6 (P3-DFM-01 … 06).

## 2. Pass-2 DFM findings: closure check

| Pass-2 ID | Disposition in R7_VALIDATION | Verified on the final board | Status |
|---|---|---|---|
| DFM-01 (Major, via in R100.1) | Fixed; `check_r7.vias_in_smd_pads` | Via now at (42.175, 55.82): hole edge **0.205 mm** outside R100.1's opening (`m3-PTH.drl` X42.175Y−55.82). A full scan of every via hole against every pad mask opening (both sides) finds only TP122.1 (bare test pad, allowed) and J2.1 inside an opening. The gate check exists and `test_r7_check` passes (28 tests) | **Closed.** The fix's third item ("list J2.1 next to TP122 among ORDERING's expected DFM queries") was neither done nor dispositioned: P3-DFM-04 |
| DFM-02 (DNP paste) | Fixed | `rocket:C0402_DNP` has no F.Paste. There are no paste flashes at C303 (11.07/11.91, 7.13), C305, C313, C314 or C304 (B, 7.74, 16.9). R304/R316 keep two flashes each | Closed |
| DFM-03 (forward 50 mm) | Documented; pre-order gate | ORDERING §3 (table, forward rail request, written-confirmation gate) and the §4 order remark. Forward windows rescanned: x 6–11 and 35–40 are 2.06 mm from J1; the nearest 5 mm-rule item is TH3 at 6.17 mm (x 6–11) and C76 at 7.45 mm (x 35–40) | Closed as dispositioned (one table value is wrong, in P3-DFM-03) |
| DFM-04 (left tab beside J3) | Accepted with procedure | The window is unchanged: J3 courtyard 1.83 mm, C84 5.23 mm | Closed |
| DFM-05 (ESD diodes beside the SMA centre pads) | Documented | D30.1/D30.2 and D31.1/D31.2 are still 0.50 mm from pad 5. ORDERING §4 remark and the §5 ohmmeter check are present | Closed |
| DFM-06 (heat-sunk SMA legs) | Documented | 41 vias (J30) and 40 vias (J31) within 1 mm, up from 37–39 (RF-02's D30.2/D31.2 vias); the nearest are unchanged at a 0.20 mm gap. ORDERING §5 leg-fillet inspection is present | Closed |
| DFM-07 (U30 T-paste over vias) | Fixed | No via copper is within 0.1 mm of any paste aperture. The stitching vias (12.61, 8.3) and (14.81, 8.3) are 0.10 mm from U30's outer apertures (y 8.70–10.10) | Closed |
| DFM-08 (LS120 reflow) | Fixed in documents; catalog open | REQUIREMENTS M1 and ORDERING §4/§6 carry it. `procurement_catalog.json` still has dimensions only, recorded as an open Minor | Closed as dispositioned |
| DFM-09 (U30 245 °C) | Documented | M1 and the ORDERING §4 remark ("peak ≤ 245 °C, 40–60 s above 217 °C") are present | Closed |
| DFM-10 (legends) | Fixed | GNSS (8.05, 8.1) and RADIO (35.74, 6.2) are both on F.SilkS. FB31 is hidden (F.Fab keeps it). ORDERING §7 says "GNSS and RADIO" | Closed. Nits in P3-DFM-06 (BOM comment, J31/RADIO stacking) |
| DFM-11 (duplicate BOM codes) | Fixed | `m3_bom_jlc.csv` has 92 lines and 92 codes, with Qty equal to the designator count on every line. BOM and CPL both hold the same 219 refs | Closed |

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| P3-DFM-01 | Minor | ORDERING §1 export check; §4 assembly description and remarks | **ORDERING was not updated for C304 (new DNP land) and TP89 (moved to the bottom).** §1 says `export_fab.py` "must report … not fitted (DNP placeholders …): C303, C305, C313, C314", but the export now reports **C303, C304, C305, C313, C314**, so an operator following the checklist sees a mismatch. §4's "DNP placeholders" bullet lists four lands. §4 says "plus 3 test pads [top] … 21 test pads [bottom]"; the board has 2 top (TP30, TP84) and 22 bottom. The paste remark says only "J30/J31 have none on purpose" and does not name the five pasteless DNP lands. Those lands are bare 0402 pads with no BOM line, which a CAM engineer may "repair". | `docs/ORDERING.md` l.25, l.80, l.84, l.95. `export_fab.py --out <scratch>`: "not fitted (DNP placeholders, in no BOM or CPL): C303, C304, C305, C313, C314". pcbnew: TP top {TP30, TP84}, bottom 22 (pass-2 board: TP89 on top, 3/21). M3_R7 already says "24 test pads" | Update §1 l.25 and §4 l.84 to add C304 (bottom, GNSS_ANT_GATE–GND compensation placeholder). Change l.80 to "2 test pads … 22 test pads". Extend the l.95 remark: "C303, C304, C305, C313 and C314 are unfitted lands with no paste on purpose; do not add apertures". |
| P3-DFM-02 | Minor | ORDERING §1 (procurement), M3 record | **ORDERING §1's cost and stock figures are from the superseded 2026-10-16 05:14Z snapshot and disagree with the bound reports.** It gives $110.93 per board, $82.78 of parts and $84.20 with minimum purchases. `fab/cost_check.json` (2026-10-17T21:01Z, bound to the current BOM/CPL hashes) gives **$105.96, $77.81 and $79.23**. §1 also says U30 "has thin stock: 18 in stock, about 10 available". `stock_check.json` and the live API give **161 in stock (152 available), not thin**. The l.3 summary ("about $106–111") and R7_VALIDATION ($105.96) are current. REQUIREMENTS M3 quotes the 05:14Z snapshot as such, which is acceptable as a historical record. M3 is met either way. | `docs/ORDERING.md` l.28, l.32. `fab/cost_check.json` total 105.96, parts 77.81, order 79.23, 52 extended. Live (my run, 2026-10-17T21:25Z, 92 codes): C30005563 stock 161 / pre-order 152; only C26633007 short (0, −33); 52 `expand`, 40 `base`. `jlc_cost.py --fab <scratch>` gives $105.96, 52 extended. `jlc_stock.py` reports thin: none | Rewrite l.28 from the bound `cost_check.json` (or say "see `fab/cost_check.json`"). Rewrite l.32: U30 is not thin now, but reserve it anyway (its stock fell to 18 two days ago). Re-run before ordering, as §1 already requires. |
| P3-DFM-03 | Minor | ORDERING §3 (order-number mark, tab table) | **ORDERING §3 gives a stale order-number placeholder location and one wrong tab-table value.** The F2/F3 copper changes moved the `JLCJLCJLCJLC` placeholder: `r7_post` searches from (23, 94) and now lands it at **(23.65, 103.15)**, ink box x 18.38–28.92, y 102.30–104.00 on B.SilkS. ORDERING still says "(22.9, 85.4) (Gerber Y −85.4), clear of every label, pad and via". The new spot is clear (no ink within 0.1 mm of any mask opening) but sits on two tented vias. Separately, the forward-tab row x 6–11 lists "nearest capacitor C76, 7.45 mm". Measured: nearest capacitor C120 at 17.29 mm, and the binding item of the 5 mm rule is TH3 at 6.17 mm (C76 at 7.45 mm is the x 35–40 window's). Both still meet the rule. | pcbnew `PCB_TEXT` 'JLCJLCJLCJLC' B.Silkscreen pos (23.65, 103.15) (pass-2 board (22.9, 85.4)). `docs/ORDERING.md` l.60, l.69. Window scan: (6,11) → J1 2.06, TH3 6.17, C120 17.29; (35,40) → J1 2.06, C76 7.45 | Update l.60 to (23.65, 103.15) / Gerber Y −103.15, or pin the placeholder in `r7_post.py` (for example `required=True` near (22.9, 85.4)) so documents and board cannot drift. Fix l.69's capacitor column (TH3 6.17 mm). |
| P3-DFM-04 | Minor | M2 (via in pad; bare test pads exempt), ORDERING §3/§4 (via covering, expected DFM queries); pass-2 DFM-01 fix item 3 | **J2.1's in-pad via is not documented, and pass 2 asked for it.** The 3V3 via at (44.035, 77.92) has its 0.3 mm hole **0.142 mm inside J2.1's Ø0.787 mask opening**. J2 is the bare TC2030 contact pattern. `check_r7.vias_in_smd_pads` exempts J2, but M2 exempts only "bare test pads", and ORDERING's via-covering row (l.58) and expected DFM queries (l.112) name only TP122. With "Plugged" ordered, JLC either plugs a via that is partly in an open pad, leaving ink on a pogo-pin contact, or queries it. Either way the order stalls or the contact is degraded (Inference: impact on TC2030 contact not measured). Pass-2 DFM-01's fix said to list J2.1 next to TP122; R7_VALIDATION's DFM-01 row does not mention it. | Via scan: (−0.142 mm, J2.1, 3V3, via (44.035, 77.92), F). `m3-PTH.drl` T1 at X44.035Y−77.92. `tools/check_r7.py` exempt set `TP\d+`, J2 (F1 handoff §2). `docs/ORDERING.md` l.58, l.112. REQUIREMENTS M2 l.75 | Add J2.1 to ORDERING l.58 ("the vias inside TP122 and J2.1 … stay open") and l.112. Either word M2's exemption as "bare test or programming contacts (TP*, J2)" to match the gate, or move the via ≥ 0.1 mm off J2.1 in a later respin. |
| P3-DFM-05 | Minor | M1/M2 assembly yield (tombstoning), ORDERING §5 inspection; trade-off of RF-02 | **RF-02's solid RF grounds raise the thermal imbalance of three small fitted two-terminal parts.** D30 and D31 (TSLP-2-20, 1.0 × 0.6 mm) and C302 (0402, 10 nF bias decoupling) now have pad 2 solid into the F.Cu GND pour, each with a GND via 0.15 mm from the pad edge. Pad 1 sits on a 0.3 mm RF line or a thin trace. Copper of each pad's net within 0.5 mm of the pad (F.Cu): D30 0.53 vs **1.19 mm²** (pass 2 0.89, thermal relief), D31 0.51 vs 1.21, C302 0.57 vs **1.84 mm²** (pass 2 1.31). Unequal heating of the two terminals is a known tombstoning driver for parts this small (Inference: no maker statement for these parts; JLC's convection reflow and nominal paste may well absorb it). ORDERING §5 inspects D30/D31 for "bridges or shift" only after jack soldering, and does not inspect C302. A tombstoned D30/D31 only loses ESD protection silently. A lifted C302 removes the bias-tap RF decoupling. | pcbnew: D30.2/D31.2/C302.2 `ZONE_CONNECTION_FULL` (zc 2; pass 2 zc 1). Vias (14.05, 4.65), (32.79, 4.75), (9.76, 5.48), copper gap 0.151–0.155 mm. Copper-within-0.5 mm figures from a same-net polygon intersection (fills, tracks, pads). `docs/ORDERING.md` l.89, l.132 | Keep the RF choice. Add to the §4 order remark and §5 inspection: "check D30, D31 and C302 for tombstoning or lifted ends (AOI/visual) before the jacks are fitted". Optionally request a ≥ 30 s soak in the profile remark. |
| P3-DFM-06 | Minor | AGENTS §3 / M2 (silkscreen), F8 (labels), DFM-10 residue | **Silkscreen and label nits.** (a) J31's designator (90°, ink y 1.48–3.96) and the RADIO legend (90°, ink y 4.12–8.23) are stacked end to end, **0.095 mm apart**, offset only 0.7 mm in x, so they read as one string. (b) GNSS is printed over four tented vias, including the new RF-ground via (10.37, 7.08), and RADIO over two, (35.19, 3.6) and (34.58, 6.9). Plugged-via dimples can break characters (cosmetic). (c) The BOM comment for C530661 still reads "GNSS ANT SMA; 915MHZ ANT SMA", and ORDERING §4 l.105 says "J31 (915 MHz radio)", while the board and §7 say RADIO (DFM-10 asked for one name). (d) By `r7_post`'s own ink-box courtyard test, which runs only for FB31, R80's designator is 0.08 mm from D8's courtyard against 0.51 mm from its own. R172 (0.51 to Y1, 0.68 own) and TP84 (0.01 to C84, 0.17 own) also fail it. All three were on the pass-2 board too (7 there), so this is not a regression, but they break the AGENTS "never next to another part" rule. | Ink polygons via `TransformTextToPolySet`: J31 ref vs RADIO minimum gap 0.095 mm. Legend boxes vs vias (§6). `fab/m3_bom_jlc.csv` C530661 line. Ink-box-to-courtyard scan (final 3, pass-2 7, R6 3) | Move RADIO to x ≥ 36.6 or start it at y ≥ 4.6 (or put J31's designator on the other side of the jack). Keep legends off vias where a spot exists. Set J31's Value to "RADIO ANT SMA" (or accept). Add R80, R172 and TP84 to `COURTYARD_REFS` (hide them if no spot). |

## 4. Fabrication package (regenerated and compared)

- **`tools/check.sh`** (rerun, exit 0): DRC 0 (`--severity-all`, no exclusions in `m3.kicad_pro`), unconnected 0,
  parity 0, ERC 0; audit OK; silkscreen outside the outline 0; R7 contract OK; routing hygiene 0 failing, 20
  allowlisted, 0 stale; actuator contract OK; fit OK.
- **Tests** (KiCad Python, from `tools/`): `test_fab_validation` 23 OK, `test_r7_check` 28 OK, `test_procurement` 15 OK.
- **Regeneration:** `python3 tools/export_fab.py --out <scratch>` reports 92 BOM lines, 219 placed parts, no part
  missing an LCSC code, no owner-fitted part, DNP placeholders C303/C304/C305/C313/C314, no uncorrected CPL row.
  The BOM and CPL are byte-identical to `fab/`. All 11 Gerbers, both drill files and the job file are identical once
  the creation-date lines are removed.
- **`tools/fab_manifest.py`:** OK, 5 outputs bound to the current CAD.
- **Zone fills:** a native `ZONE_FILLER` refill (a scratch copy with `.kicad_pro`/`.kicad_dru`) changes no zone area
  (15 zones, max 0 mm²).
- **Drill:**
  - PTH T1 0.300 ×709 (vias: 603 at 0.6/0.3, 106 at 0.5/0.3; pass 2 699), T2 0.6 ×4, T3 0.8 ×2, T4 1.1 ×12, T5 1.6 ×8;
  - NPTH 0.600 ×2 (J3), 0.991 ×3 (TC2030), 1.152 ×3 (TH1–TH3).
  - The mask Gerbers have no via openings (the only 0.6 mm round openings are J3's NPTH).
- **Job file:** M3-ASSY-R7, 4 layers, 1.6 mm, ENIG, stackup 0.035/0.203/0.030/1.03/0.030/0.203/0.035 (JLC041611-7628).
- **CPL:** `jlc_orient.py --verify-cpl` rebuilds 92 top and 119 bottom rows from JLC footprints (worst residual
  0.491 mm, no errors) and checks 8 rows by placement only (J1 R72 R74 R77 R100 R101 R103 R110). Rows changed since
  pass 2: the re-placed limiter (Q30 270°, Q31 180°, Q32 90°, R300 0°, R301 180°, R302 180°, R303 90°, all bottom)
  and C311/C312 (x 37.2). All are verified. The bottom-side rotation convention remains the documented Inference.
  Confirm it in JLC's preview.
- **BOM merged lines:** one per code. The comments are joined with "; " (C307331: "100nF 50V X7R 10%; 100nF 50V",
  two schematic spellings of one part). No code maps to two footprints or MPNs. J30/J31 Assembly column: "THT (JLC
  through-hole step, hand-soldered after reflow; no paste; body overhangs the aft edge)".
- **Assembly PDFs:** the top PDF contains C303, D30, D31, FB31, J30, J31, U30, U31. The bottom PDF contains C304,
  Q30, Q32, R100, TP89.

## 5. Footprints, paste, mask, vias

- **Library:** the only footprint changes are the new `C0402_DNP` (identical to `C0402` apart from the missing
  F.Paste and the description) and the LS120 silk at 0.15 mm. DRC reports no `lib_footprint_mismatch`.
- **Via in pad (M2):**
  - no via hole is within 0.1 mm of a soldered pad opening;
  - closest: R125.2 0.13 mm, R81.2 0.175, TP120.1 0.20, R100.1 0.205, R130.2 0.212, U9.4 0.241 (BAT_FAULT_N, new);
  - only TP122.1 (allowed) and J2.1 (P3-DFM-04) are inside an opening.
- **Vias near pads:**
  - vias whose hole edge is within 0.35 mm of a pad opening: 70 (pass 2) → 80 (final);
  - the new ones are the seven RF-ground vias (0.30 mm), D9.2's (0.25), C80/C84 (0.32), R305/R302 (0.33), C60, C75,
    C30 and the two moved signal vias;
  - JLC's BGA via-plugging table gives a **0 mm** minimum drill-to-pad spacing for 4-layer boards (0.35 mm applies to
    2-layer), so these vias are not a fabrication limit (https://jlcpcb.com/help/article/bga-design-guidelines---pcb-layout-recommendations-for-bga-packages,
    4-layer table, row D).
- **Paste:**
  - no via copper lies under or within 0.1 mm of any paste aperture (minimum 0.025 mm at R81.2, outside);
  - no paste on J30/J31 pads (the F_Paste flashes in the strip are only R304, R316, C302, L30, D30, D31 and R312);
  - no paste on any DNP land.
- **Mask:** no web under 0.1 mm between openings of different pads. The only overlaps are same-net drain fingers
  (Q120/Q121) and U9's duplicate pad numbers.
- **Pad entries:** 13 tracks are wider than the SMD pad they enter (pass 2: 17). All are inherited (Q124.5, U7, U8,
  U11, C5), and none is new.
- **Component spacing:** no soldered pads of different parts are closer than 0.3 mm (final and pass-2 boards).
- **Through-hole GND pins:**
  - the zone connections and attached tracks are unchanged from pass 2 (J122 GND zc full, J123.2, J1.2, J3 legs);
  - the hygiene pass removed only duplicate track ends on signal THT pads (J124.1, J122.1/4/8/10, J121.1/2, J123.1,
    J1.4).
- **One 3V3 via under L1** (24.8, 34.3): between L1's terminals on the bottom, hole 0.35 mm from L1.2's opening, under
  the body and tented/plugged. Acceptable.

## 6. Silkscreen

- **Text and lines:** 163 visible designators, every one ≥ 1.0 mm tall with a 0.15 mm stroke. All silk line widths
  are ≥ 0.15 mm (LS120 now 0.15).
- **Hidden designators:** 89, equal to the `docs/M3_R7.md` list (set difference empty).
- **Overlaps:** no text ink is clipped by, or within 0.1 mm of, a pad mask opening, except TH2's own designator at
  0.08 mm from its NPTH. No ink of two texts overlaps.
- **Legends:**
  - GNSS (F, 8.05, 8.1) sits over vias (6.0, 7.0), (8.0, 7.0), (10.37, 7.08) and (10.41, 8.3);
  - RADIO (F, 35.74, 6.2) sits over (35.19, 3.6) and (34.58, 6.9);
  - the J2 pin rows are on the bottom at (30.0, 66.4), (40.0, 68.15) and (25.0, 85.15), 8–20 mm from J2 (top). They
    moved with the F2/F3 changes and are still self-identified by "J2";
  - `JLCJLCJLCJLC` is at (23.65, 103.15) (P3-DFM-03).
- **Designator placement:**
  - by the pass-2 text-centre metric, 16 designators are nearer another courtyard than their own on both boards. The
    set changed: C150, R126, R131 and R60 are newly flagged; C129, C14, FB31, R12 and R312 cleared;
  - by `r7_post`'s ink-box metric, 3 are (pass 2: 7). See P3-DFM-06(d).

## 7. Panel, rails, tabs

- **Long-edge windows:** unchanged from pass 2 (rescanned): left y 63–68 (J3 1.83 mm, C84 5.23 mm); right y 62–67
  (TP75 1.95, C11 6.6) and 8–13 (C310 8.38). Compliant starts are the same as pass 2.
- **Forward edge:** x 6–11 and 35–40 are compliant (J1 2.06 mm). J1's courtyard ends short of the forward edge, so
  a forward rail does not collide with its body.
- **Parts at the edges:**
  - J3 (courtyard to x −1.03) and J9 (courtyard to x 46.05, body to 46.02) reach the long edges, as on R6;
  - J30/J31 overhang the aft edge, where ORDERING forbids a rail.
- **Documentation:** ORDERING §3/§4 carry the forward-rail request and the written-confirmation gate (DFM-03) and
  the J3 procedure (DFM-04).

## 8. Procurement and cost

- **Live JLC parts API** (`selectSmtComponentList`, `searchType` 2, all 92 codes, 2026-10-17T21:25Z):
  - 52 `expand` and 40 `base`;
  - every line in stock for 5 boards except U4 (C26633007: stock 0, pre-order −33), which is documented as consigned.
- **Key lines:**

  | Line | Stock | Pre-order |
  |---|---:|---:|
  | U30 C30005563 | 161 | 152 |
  | U31 C5333985 | 462 | 420 |
  | J30/J31 C530661 | 3,299 | |
  | D30/D31 C535146 | 218 | (needs 10, minimum 5) |
  | J9 C161692 | 719 | −2,750 (pass 2's Inference: private-library allowance) |
- **`jlc_cost.py --fab <scratch>`:** parts $77.81 + 92 × $1.53 / 5 = **$105.96 per board** (cap $126.41). 52
  Extended codes (cap 52, no margin). With minimum purchases: $79.23. This matches `fab/cost_check.json`.
- **`jlc_stock.py`:** short U4 only; thin none.
- **M1 and M3** are met (U4 consignment pending). ORDERING §1's figures are stale (P3-DFM-02).

## 9. Sources

- JLC BGA design guidelines (via plugging, drill-to-pad spacing, 2-layer 0.35 mm / 4-layer 0 mm):
  https://jlcpcb.com/help/article/bga-design-guidelines---pcb-layout-recommendations-for-bga-packages
- JLC mouse-bite guidance (tab count, 1.5 mm part clearance, 2 mm connector keep-out): https://jlcpcb.com/blog/pcb-mouse-bites
- JLC parts API: POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
- Maker data for the footprints and reflow limits: as cited in `pass2_dfm.md` §9 (unchanged parts, not re-read).

## 10. Inferences

- That the thermal imbalance in P3-DFM-05 raises tombstoning risk materially. There is no maker statement for these
  parts, and the size of the effect under JLC's profile is unknown.
- That JLC's CAM would plug or query the via partly inside J2.1's opening, and the effect on the TC2030 contact.
- The meaning of `canPresaleNumber` (carried from pass 2).
- The JLC bottom-side CPL rotation convention (`jlc_orient.py` docstring).

## 11. Method (reproducible, read-only)

KiCad 10.0.6 Python (`pcbnew.LoadBoard`, never saved) scripts in `scratchpad/p3dfm/`:
- `counts.py`: placed parts, test pads and DNP by side;
- `viapad.py`, `viapad2.py`: via hole and ring to pad mask openings, final vs pass 2;
- `pastevia.py`: vias near paste, and DNP paste;
- `padinfo.py`: pad layers and zone connection;
- `silk.py`, `refnear2.py`, `inkd.py`, `txtpad.py`, `txtclear.py`, `silkw.py`, `inkover.py`: silkscreen;
- `tht.py`: THT pad connections;
- `padentry.py`: wide pad entries;
- `padpad.py`: inter-part pad gaps;
- `maskweb.py`: mask webs;
- `padcu.py`: copper near the D30/D31/C302 pads;
- `edgeparts.py`, `fwd.py`: edges and tabs.

Pass-2 helper scripts reused read-only (`dfm_p2/work/refnear.py`, `tabs.py`, `tabs2.py`, `smanear.py`, `gflash.py`,
`refill.py`, `live.py`).

Other runs:
- `tools/check.sh`;
- `tools/export_fab.py --out <scratch>` and a Gerber/drill/job diff;
- `tools/fab_manifest.py`;
- `tools/jlc_orient.py --verify-cpl`;
- `tools/jlc_cost.py` and `tools/jlc_stock.py` with `--fab <scratch>`;
- the unit tests listed in §4.

No repository file other than this report was written. The board and fab hashes are unchanged.
