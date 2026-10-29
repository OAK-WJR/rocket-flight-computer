# R7 pass 3: mechanical fit and robustness review

Independent, read-only review (2026-10-17) of the final R7 board on branch `m3-assy-r7`.

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c`. This matches the "final R7 board" in
  `docs/R7_VALIDATION.md`. The hash was checked before and after every tool run.
- **Comparison board:** the pass-2 board `03fe7572…6d54`, a byte-identical copy in the session scratchpad
  (`scratchpad/r7.kicad_pcb`).
- **Scope:** bore envelope and `fit_check`; supports and the vibration record; SMA retention, staking,
  counter-hold and sled requirements; mounting hardware; module and jack heights; the bay stack (M3_R7,
  REQUIREMENTS "Board position", and the parent `docs/VEHICLE.md` row against the proposal in
  `fix2_docs_handoff.md` §2).
- **Changes:** none to any repository file apart from this report.

What was run:
- `tools/check.sh`, exit 0:
  - DRC 0, unconnected 0, parity 0, ERC 0;
  - audit, silk, R7 contract, routing hygiene (0 failing, 20 allowlisted), actuator contract and fit all OK.
- `fit_check.check_board()` called directly for the J30/J31/U30/U31 rows and the excluded-reference list.
- My own read-only pcbnew scripts (`scratchpad/p3mech/`):
  - `fpdiff.py`: every footprint and Edge.Cuts circle, pass-2 board against final board;
  - `supports.py`: pads (exposed or not, any side, DNP included), courtyards, tracks, vias and in-memory
    zone fills around each support;
  - `parts.py`: model boxes and courtyards of the tall parts, the RF parts and the moved parts.
- **Kinghelm KH-SMA-KE8-G datasheet**, re-downloaded from the LCSC URL and its text extracted (§4).
- **Parent repository:** `git log` / `git show 43af048` / `git diff` of `docs/VEHICLE.md` and `CLAUDE.md`.

## 1. Summary

**Critical 0, Major 0, Minor 4.**

Every pass-2 mechanical finding is closed or properly dispositioned. The fix pass caused no mechanical
regression:
- Supports, J30/J31, U30/U31 and every tall part are exactly where they were on the pass-2 board.
- The only parts that moved are the small limiter parts on B.Cu (Q30–Q32, R300–R303), C311/C312 (0.2 mm), and
  TP89 (to the bottom at (8.1, 33.6)). C304 (DNP 0402, bottom) is new.
- All of these are ≥ 6 mm from any support.
- Bore-fit margins are unchanged: J9 mated 0.03 mm, C84 0.11 mm, U30 6.12 mm, J30 mated 8.91 mm, U31
  12.28 mm.

The four Minor items are about how the new procedures and records are worded. None needs a board change:
1. **P3-MECHANICAL-01:** the SMA mating torque written into five documents ("about 0.45 N·m") contradicts
   Kinghelm's recommended 0.8–1.13 N·m and has no source.
2. **P3-MECHANICAL-02:** the R14 (R7) "≫ 5×" and the M3_R7 retention line assume the ferrule tie carries the
   whole plug. The plug is screwed to the jack, so the jack still carries part of it, and a mis-set saddle
   can preload it. f1 hardly changes; the jack moment does.
3. **P3-MECHANICAL-03:** the records are stale about the parent VEHICLE.md row, which has been committed. That
   row also leaves out J1's forward-facing battery entry, which P1 asks to be recorded.
4. **P3-MECHANICAL-04:** `fit_check`'s 3.5 mm bottom-standoff rule skips bare bottom test pads and DNP lands,
   although P2 covers pads. The board passes today: TP92 is at 4.60 mm.

## 2. Pass-2 findings in this dimension: closure check

| Pass-2 ID (skeptic majority) | R7_VALIDATION disposition | Verified on the final board / documents | Verdict |
|---|---|---|---|
| MECHANICAL-01 (Major → Minor) | Documented. Counter-hold, torque, witness marks, staking after the RF tests, the sled carries the plugs; physical work open | REQUIREMENTS P3 (l. 68), ORDERING §4 table (l. 122), §5 counter-hold (l. 145), staking list incl. J30/J31 (l. 143), step order (l. 134), §7 "Antennas and coax" and "Sled" (l. 195, 198), MARGIN_PRESCRIPTION R14 (R7) (l. 271). The contradictory "2 cm tie" and "end at the aft edge" wording is gone (grep: none) | **Closed**, with the residual wording issues P3-MECHANICAL-01/02 |
| MECHANICAL-02 (Major) | Fixed (record): M3_R7 §"Mechanical", owner decision "no sixth support", bench tap/modal check | M3_R7 l. 430–455 records method, inputs, results, decision and bench check. It was computed on the pass-2 board. `fpdiff.py` shows supports, outline, every heavy or tall part, J30/J31 and U30/U31 unchanged; only SOT-23/0402/0603 parts (≈ 1–10 mg each, Inference) and a test pad moved, so the record carries over to `7660620c…`. That replaces R7_VALIDATION l. 277's "Inference that it carries over" with a measured placement diff | **Closed** |
| MECHANICAL-03 (Major → Minor) | Documented: REQUIREMENTS "Board position" replaced; bay-stack paragraph in M3_R7. Open: parent VEHICLE.md row and shroud measurement | REQUIREMENTS l. 86 and M3_R7 l. 267–280 are consistent with my arithmetic (§3.6). The parent row **was committed** in `43af048` (2026-10-16 10:41), so the "open" entries are stale, and the committed row leaves out J1's orientation | **Closed in substance**; records issue P3-MECHANICAL-03 |
| MECHANICAL-04 (Minor) | Documented: 44–48 mm zone with staggered loops or right-angle plugs. Open: choose the plug and cite its drawing | REQUIREMENTS l. 86, ORDERING l. 195, VEHICLE row. `fit_check` MATED basis still "Inference" (tools/fit_check.py l. 42–50), tracked as open | **Properly dispositioned** (open, tracked) |
| MECHANICAL-05 (Minor) | Documented: ORDERING §7 hardware sizes | ORDERING l. 199: M3 nylon, washer ≤ 7.0 mm OD, standoff ≤ 5.5 AF (≤ Ø6.4) and ≥ 3.5 mm tall. Measured on the final board: C76.2 4.423 mm from (42, 114.4), TP92.1 4.596 mm from (4, 64), TP30.1 5.009 mm from (4, 4); copper ≥ 2.100 mm from every support centre (0.5 mm from the hole edge); BUZZ_DRV B.Cu 2.375 mm from (4, 64); In2 BAT_IN at (4, 64) and (4, 114.4); F.Cu RAW_ACT at (4, 114.4) 2.400 mm. All match the row | **Closed** |

The related requirements findings agree with these dispositions: REQUIREMENTS-02 is closed with MECHANICAL-02,
REQUIREMENTS-12 is closed by the R14 (R7) row, and REQUIREMENTS-06 is the VEHICLE row (now done, see
P3-MECHANICAL-03).

## 3. Findings

| ID | Sev. | Req. | Finding | Evidence | Recommended fix |
|---|---|---|---|---|---|
| P3-MECHANICAL-01 | Minor | P3 (SMA torque); AGENTS.md §3 "Verify, don't guess" (parameters from the maker's datasheet, with source) | The pass-2 fix wrote "mating torque about 0.45 N·m, never above Kinghelm's 1.13 N·m" into five documents. 0.45 N·m is about 55 % of the bottom of the jack maker's recommended range, and no document gives its source. The plug that sets the other half of the interface has not been chosen. An under-torqued SMA coupling is the usual way for a nut to back off under vibration. Here that means an intermittent GNSS antenna bias or RF path. Tracking and telemetry are not safety functions; the witness marks show it after the flight; the bench RF tests run at the same torque | Kinghelm KH-SMA-KE8-G datasheet p. 1, 机械性能 item 2: "Recommended mating torque 建议适配扭矩：0.8～1.13N·m" (https://datasheet.lcsc.com/datasheet/pdf/35ad22a9bea57e53d493009a20c931ef.pdf?productCode=C530661). Amphenol's SMA cut sheet gives 7–10 in-lb (0.80–1.10 N·m) recommended (https://www.tti.com/content/dam/ttiinc/manufacturers/amphenol/RF/Products/pdf/SMA-Cutsheet.pdf). The 0.45 value is at REQUIREMENTS.md l. 68, ORDERING.md l. 145 and l. 195, MARGIN_PRESCRIPTION.md l. 271, M3_R7.md l. 453 and R7_VALIDATION.md l. 213. `grep "0.45 N"` finds no source in docs/ or the review folder; fix2_docs_handoff §1 gives none. pass2_mechanical asked for "the plug maker's [value], ≤ Kinghelm's 1.13 N·m" | Use the jack maker's range with the counter-hold already required: "0.8–1.13 N·m (Kinghelm p. 1), or the chosen plug maker's value if lower, cited". If a lower value is kept on purpose (to spare the legs should a counter-hold slip), state that reason and cite a brass-SMA torque source. Either way, record the value with the plug choice (MECHANICAL-04) |
| P3-MECHANICAL-02 | Minor | P3 (≥ 5× at 100 g; "the board's pads never carry cable loads"); P2 (vibration record) | The new R14 (R7) "✅ ≫ 5× (Inference)" and M3_R7's "each jack carries only its own ≈ 1.8 g" assume the tie or saddle at the crimp ferrule carries the whole plug. But the plug is screwed and torqued onto the jack, and the ferrule is 25–30 mm aft of the edge. The jack and the tie therefore share the plug in proportion to their stiffness, and a zip tie is the compliant member. The documents also do not require the saddle to sit on the plug axis. A saddle set too low or too high, once tied, bends the jack statically: the very pad load the sled was meant to remove. The f1 record is barely affected; the jack-load claim is | **Jack moment at the edge at 5 × 100 g** (Inference; pass2_mechanical §3.4 masses: jack 1.8 g, centre of mass ≈ 5 mm; plug 3.5 g, ≈ 17.5 mm): 45 N·mm with the tie taking all of the plug (the R14 (R7) figure); ≈ 190 N·mm if the tie takes half; 373 N·mm with no tie (the R14 (R7) "❌ not shown" case). **f1 for the half-share case**: about the pass-2 sensitivity row "3.5 g at 11.5 mm", i.e. 208 / 294 / 361 / 510 Hz, against 221 / 313 / 377 / 533 Hz recorded (pass2_mechanical §3.3), so the vibration record holds within ≈ 6 %. **Documents**: ORDERING l. 198 "with a tie or saddle at each plug's crimp ferrule" (no height or preload rule); REQUIREMENTS l. 68; MARGIN_PRESCRIPTION l. 271; M3_R7 l. 441–453. The M3_R7 table row label "plugs mated on the jacks (not allowed in flight)" is misleading: the plugs are mated in flight; what is excluded is the jack carrying them unaided. **Jack axis** (Kinghelm drawing, pass2_mechanical §3.1): 0.45 mm above the top face | (1) ORDERING "Sled": the saddle is set to the plug axis so the plug rests on it unloaded before it is tied, with no visible jack or plug deflection when the tie is closed; the tongue is stiff enough not to drive the plugs (the tap check already looks for plug-driven rocking). (2) R14 (R7) and M3_R7: say the tie relieves most, not all, of the plug, so the jack moment is 45 to about 190 N·mm at 5 × 100 g depending on the tie, and the ≥ 5× rests on the structural-epoxy staking (Inference). (3) Relabel the M3_R7 row "plug carried by the jack alone (not allowed in flight)" |
| P3-MECHANICAL-03 | Minor | P1 ("Record final outline, orientation and bay stack in … M3_R7.md and parent VEHICLE") | **Stale records.** The coordinator committed the R7 VEHICLE stack row (and the CLAUDE.md E22 wording) in parent commit `43af048` on 2026-10-16. Four R7 records still call them open or say the row "still describes R5". **Omission in the committed row.** It records the jacks on the aft edge but not that J1's battery entry faces forward at the forward edge, which the fix2_docs_handoff proposal included. The battery leads therefore run the whole board length and U-turn into J1 beyond the forward edge. That U-turn shares the "eyebolt nut and charge wiring ~25" zone, which does not allocate room for it. The row also gives no standoff height: it says only that the sled clears parts hanging 3.0 mm. Yet the sled tongue must also pass under the SMA plug nuts (2.6 mm below the bottom face), which needs ≥ 3.5 mm standoffs (ORDERING l. 199) | `git -C <parent repo> show 43af048 -- docs/VEHICLE.md`: the row now reads "flight computer board 118 (M3-ASSY-R7 …) … Leaves ~52–68 mm of slack". Stale text: M3_R7.md l. 280 "the parent docs/VEHICLE.md stack row still describes R5"; R7_VALIDATION.md l. 205 (REQUIREMENTS-06 "Open (parent repository)"), l. 215 (MECHANICAL-03 "Open: parent VEHICLE.md row"), l. 279; STATUS.md l. 108. Parent CLAUDE.md l. 46 already reads "the E22-900M22S is a layout alternate that needs a respin". **J1**: footprint `M3_DB128V_4P_Entry` ("wire entry on local −y") at (23.0, 110.4), rotation 180°, so the entry faces +y. Courtyard y 104.86–116.14, so the entry face is 1.9 mm inside the forward edge (pcbnew). M3_R7 l. 271–273 records this; VEHICLE does not | Update M3_R7 l. 280, R7_VALIDATION (REQUIREMENTS-06 and MECHANICAL-03 rows, "Parent repository" line) and STATUS l. 108 to "recorded in parent `43af048`". Ask the coordinator to add to the VEHICLE row: "J1's battery entry faces forward at the board's forward edge (leads run the board's length and turn back into J1 beyond it); standoffs ≥ 3.5 mm". Optionally also state the aft-edge position range (joint ≥ +80…83 / +91…95) |
| P3-MECHANICAL-04 | Minor | P2 ("≥ 3.5 mm bottom part/pad clearance around each support"); gate integrity | `fit_check.check_board()` puts bare board features (TP\*, J2, TH\*) and DNP footprints on the excluded list before it builds the bottom-obstacle list. So the 3.5 mm standoff rule never sees their bottom pads. The top check does collect exposed top pads of the same footprints, before the `continue`. The rule passes on this board, but the gate does not prove it. This matters more now that the fix pass moved TP89 to the bottom and added the bottom DNP land C304 | tools/fit_check.py l. 296–311: `top_pads.extend(...)`, then `if board_feature(f) or f.GetAttributes() & pcbnew.FP_DNP: excluded.append(ref); continue`; `bottom` is filled only after that. Excluded on this board: C303–C305, C313, C314, J2, TH1–3, 20 TPs. Measured with `supports.py`: the nearest bottom bare pad is TP92.1, 4.596 mm from (4, 64) (courtyard 4.250); TP89 is at (8.1, 33.6), ≥ 25 mm from any support; C304 is 13.4 mm from (4, 4). So no violation today | In `check_board`, before the `continue`, add the B.Cu pads of board features and DNP footprints that are exposed (on B.Mask) to `bottom`, as is already done for top pads. Add a `test_fit_check` case with a bottom TP inside 3.5 mm. Keep the TH tooling holes out (NPTH, no pad) |

## 4. Measurements and checks (final board `7660620c…`)

### 4.1 Bore envelope (`fit_check`, P2)

`tools/check.sh` fit section: radius 24.9 mm, axis x 23.0, sled tolerance ±0.3 mm, top face on the axis.

| Item | Box (x; z), mm | Margin |
|---|---|---|
| J9 mated (R6) | 40.95–45.20; 0–10.30 | 0.03 |
| C84 (R6) | 2.25–12.75; 0–12.80 | 0.11 |
| J122 mated | 19.00–27.00; 0–23.50 | 0.71 |
| U30 MAX-F10S | 4.76–16.06; 0–2.70 | 6.12 |
| J30 mated (plug box x ±4.6, z −4.1…+5.1) | 8.25–17.45; −4.10–5.10 | 8.91 |
| J30 jack body | 9.50–16.20; −2.90–3.80 | 10.50 |
| J31 mated / body | 26.94–36.14 / 28.19–34.89 | 10.42 / 12.04 |
| U31 E22-900MM22S | 24.76–34.96; 0–2.70 | 12.28 |

Other results:
- **Deepest bottom parts:** L1 (z −4.62, 3.02 mm below the bottom face) and L3 (−4.60). A 3.5 mm standoff
  leaves 0.48 mm under them.
- **Heights:**
  - U30's 2.70 mm envelope equals the MAX-F10S maximum (u-blox DS R03 Table 21, as cited in pass 2).
  - U31's 2.70 mm envelope is the E22 2.5 ± 0.2 mm maximum.
  - The J30/J31 body box is the Kinghelm 6.5 mm flange plus 0.2 mm tolerance about the jack axis, which sits
    0.45 mm above the top face.
  - The mated-plug box bottom (−4.10) is 0.07 mm above an 8 mm AF nut's corner (−4.17). That is immaterial
    against an 8.9 mm margin.
- **No mated envelope intersects a model box.**

### 4.2 Supports (P2, MECHANICAL-05)

Edge.Cuts Ø3.2 circles on both boards: supports (4, 4), (42.3, 4), (4, 64), (4, 114.4) and (42, 114.4); J122
tie holes (21.5, 68.6) and (27.0, 82.6). They are unchanged.

| Support | Top (rule 3.8) | Bottom (rule 3.5) | Copper ≤ 3.5 mm from the centre |
|---|---|---|---|
| (4, 4) | U30 courtyard 4.579, TP30.1 pad 5.009 | none within 5.2 (Q30 courtyard ≈ 6.0) | GND fills on all layers at 2.100; GND vias from 2.700 |
| (42.3, 4) | none within 5.2 | none within 5.2 | GND fills 2.100; GND vias from 2.208 |
| (4, 64) | none within 5.2 (TP89 has gone to the bottom) | TP92 courtyard 4.250, pad 4.596 | F/In1/B GND 2.100; In2 BAT_IN 2.100; B.Cu BUZZ_DRV 2.375 |
| (4, 114.4) | TH3 NPTH 2.962 (R6, known) | — | F/In1/B GND 2.100; F.Cu RAW_ACT 2.400; In2 BAT_IN 2.400 |
| (42, 114.4) | none within 5.2 | C76 courtyard 3.905, model 4.150, C76.2 pad 4.423 | GND fills 2.100; GND via 2.121 |

The standoff (≤ Ø6.4, radius 3.2) and the washer (≤ 7.0 mm OD, radius 3.5) clear everything listed. The
copper near the holes is under mask and 0.5–0.9 mm from the hole edge, so nylon hardware stays required, as
ORDERING says.

### 4.3 Fix-pass placement diff (pass-2 `03fe7572…` → final `7660620c…`)

`fpdiff.py`: no change to the outline, the holes, J30/J31, U30/U31 or any part heavier than about 0.02 g.

| Part | Change |
|---|---|
| Q30 | (10.75, 13.0) → (4.75, 11.75), bottom |
| Q31 | (10.75, 17.25) → (12.0, 14.25), bottom |
| Q32 | (5.0, 12.0) → (8.75, 13.25), bottom |
| R300–R303 | within 1.75 mm, bottom |
| C311, C312 | +0.2 mm in x |
| TP89 | (5.0, 59.4) top → (8.1, 33.6) bottom |
| C303/C305/C313/C314 | footprint now `C0402_DNP` |
| C304 | new, DNP, (7.74, 16.9) bottom |

All moved bottom parts are ≥ 6.0 mm (courtyard) from (4, 4) and inside the bore (worst bottom margin 2.34 mm,
C74, R6).

### 4.4 SMA retention chain (P3)

- **Datasheet text, re-extracted.** Recommended mating torque 0.8–1.13 N·m. Assembly torque ≥ 0.5 N·m. Centre
  contact withdrawal ≥ 0.28 N. Brass HPb59-1, gold-plated. Wave solder 240–250 °C for 5 s.
- **Counter-hold.** The instruction (ORDERING l. 145: thin flat-jaw pliers, jaw ≤ 1.5 mm, off the thread) is
  feasible.
  - The 6.5 mm flange flats stand about 0.075 mm proud of a 1/4-36 thread (Ø6.35), so parallel jaws on the
    flats clear the thread.
  - Jaws on the top and bottom flats (z +3.7 and −2.8) clear the jack legs (to z +0.9 and −2.47).
  - This is geometry from the Kinghelm drawing; the hand operation itself is an Inference.
- **Staking.** Structural epoxy from the flange back face along the legs, off the centre pad, the RF line,
  D30/D31, the threads and the mating face. The sequence is right: RF tests → coating → staking → tap check
  (ORDERING l. 134).
  - With ≥ 3.5 mm standoffs, a bottom fillet of up to about 2 mm along the bottom legs stays above the plate.
    This is a planning note, not a finding.
- **Sled tongue.** The flanges hang 1.23–1.33 mm and the plug nuts 2.6 mm below the bottom face. A plate
  ≥ 3.5 mm below keeps ≥ 0.9 mm under the nuts. The "relieved for the flanges" wording is harmless but not
  needed at that standoff height.

### 4.5 Vibration record (P2)

- **The record is complete.** M3_R7 §"Mechanical" gives the method (Ritz plate, pinned and clamped bounds,
  D 5–10 N·m), the cross-check against the R5 record, and the table:
  - flight configuration 221 / 313 / 377 / 533 Hz;
  - R6 241 / 341 / 396 / 559 Hz;
  - plug carried by the jack alone 176 / 249 / 269 / 380 Hz.
- **It also records** the 100 g strains, the owner decision and the bench check (ORDERING l. 159).
- **The placement diff (§4.3) confirms** that it applies to the final board.
- **Tie stiffness matters little for f1.** With the plug half carried, the pass-2 sensitivity case gives
  208 Hz pinned at D 5 (P3-MECHANICAL-02).

### 4.6 Bay stack (P1; REQUIREMENTS "Board position"; parent VEHICLE.md)

Joint coordinates from VEHICLE:
- bulkplate top −44.6;
- battery bay 80 mm, to +35.4;
- shroud +4…+47, within 18.4 mm of the axis;
- coupler bore Ø50.8 to +120;
- nose-shoulder base +550.

Checks:
- **Aft edge, loops off the shroud side:** −44.6 + 80 + 44…48 = +79.4…83.4. REQUIREMENTS, M3_R7 and the
  handoff give "≥ +80…83" ✓.
- **Aft edge, loops forward of the shroud:** +47 + 44…48 = +91…95 ✓.
- **Slack:** 595 − (80 + 44…48 + 118 + 25 + 260) = 64–68 mm, and 550 − (91…95 + 118 + 25 + 260) = 52–56 mm.
  VEHICLE's "~52–68" ✓.
- **Plug ends:** from aft edge +80, at +50.5…54.5. That is clear of the battery bay (+35.4) and axially clear
  of the shroud top (+47). Only the loops overlap the shroud's axial range, on the side away from it, as
  required.
- **Coax bend radius:** the 13 mm static RG316 radius used for the loop zone agrees with L-com (0.51 in) and
  ULTECH (12.7 mm). HUBER+SUHNER lists 15 mm static and 25 mm repeated
  (https://www.hubersuhner.com/en/shop/product/cables/coaxial-cables/flexible/22510079/rg316-50-ohm-3-ghz-200-c-2-5-mm-fep-jacket).
  When the coax is chosen, check its static radius against the 44–48 mm allocation; it is already listed open
  with the plug choice.
- **Committed VEHICLE row:** consistent with the board (118 mm, five holes, jacks 9.5 mm aft, sled carries
  the plugs 25–30 mm aft). The omissions are in P3-MECHANICAL-03.

## 5. Other observations (no finding)

- **ORDERING "Sled" row (l. 198), inherited from R6 unchanged.** It calls C84 "the tallest part" and says it
  keeps 0.11 mm. J1 (14.5 mm) is the tallest part, and the binding envelope is the J9 mated plug at 0.03 mm.
  The "Camera harness" row (l. 194) states that correctly. Cosmetic.
- **TH3 (Ø1.152 NPTH) sits under the (4, 114.4) washer**, 2.96 mm from the centre. This is known since R6, with
  a 1.36 mm web between the hole edges.
- **The J122 tie channel under the board** (ORDERING l. 198) must also clear the tie head within the ≥ 3.5 mm
  standoff gap. This is inherited and already stated ("with room for the tie head").

## 6. Sources

- Kinghelm KH-SMA-KE8-G datasheet (LCSC C530661), p. 1 mechanical items 1–4, materials, wave-solder rating:
  https://datasheet.lcsc.com/datasheet/pdf/35ad22a9bea57e53d493009a20c931ef.pdf?productCode=C530661
- Amphenol RF SMA cut sheet (coupling torque 7–10 in-lb recommended, 15 in-lb max):
  https://www.tti.com/content/dam/ttiinc/manufacturers/amphenol/RF/Products/pdf/SMA-Cutsheet.pdf
- HUBER+SUHNER RG316 22510079 (static bend radius 15 mm, repeated 25 mm):
  https://www.hubersuhner.com/en/shop/product/cables/coaxial-cables/flexible/22510079/rg316-50-ohm-3-ghz-200-c-2-5-mm-fep-jacket
- L-com RG316 2D drawing: https://l-com.com/Images/Downloadables/2D/RG316-1K_2D.pdf
- Project files:
  - `tools/fit_check.py` (l. 36–66, 290–346);
  - `docs/REQUIREMENTS.md` l. 66–68 and 86;
  - `docs/ORDERING.md` l. 89, 122, 132–145, 159, 194–199;
  - `docs/MARGIN_PRESCRIPTION.md` l. 270–271;
  - `docs/M3_R7.md` l. 267–280 and 430–482;
  - `docs/R7_VALIDATION.md` l. 205–217 and 270–290;
  - `STATUS.md` l. 60–110;
  - parent `docs/VEHICLE.md` l. 39 (commit `43af048`) and parent `CLAUDE.md` l. 46;
  - `sources/r7_review/pass2_mechanical.md` §3.1–3.6;
  - `pass2_main_verdicts.json` (mechanical);
  - `fix2_docs_handoff.md` §1–3;
  - `fix2_F1_handoff.md` (TP89, C304, limiter).

## 7. Inferences (not measured, not from a primary source)

- Part masses other than U30/U31 (jack 1.8 g, plug 3.5 g, small parts 1–10 mg), the plug centre of mass, the
  tie's load share, and the resulting jack moments (P3-MECHANICAL-02).
- f1 for a half-carried plug, taken from pass 2's sensitivity row rather than a new model run.
- The practicality of a hand counter-hold on a 1.5 mm flange, and SMA loosening behaviour at low coupling
  torque (P3-MECHANICAL-01).
- RG316 bend radius for the cable eventually chosen.
