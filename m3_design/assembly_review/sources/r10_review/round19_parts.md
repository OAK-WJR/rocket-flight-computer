# R19 parts / BOM / CPL / lands / ratings / stock (Claude)

Target commit `1e604412015002be941f7056d0788d23f508e6ac`. PCB SHA-256 before and after:
`a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918` (unchanged; no tracked file edited).
Evidence, sources and limits: [round19_parts.json](round19_parts.json). Probe scripts, raw supplier and EasyEDA
responses, renders and DRC output: `.supervisor/r19_parts/` (ignored).

**Totals: 0 Critical, 0 Major, 5 Minor (2 new, 3 carried).**

## Findings

| ID | Sev. | Status | Finding and key number | Fix |
|---|---|---|---|---|
| R19-BOM-01 | Minor | carried R18-BOM-01 | U4 still blocks release: C26633007 has 0 at JLC and LCSC (2026-10-31T01:41Z). New: **ISM6HG256XTR C51931514** has 9 at JLC (minimum 1, $14.33, 01:54Z). Its datasheet (DS15034 Rev 1) uses the same LGA-14L drawing DM01021587_2 (p187), the same pin functions (Table 2: our grounded SDx/SCx and open OCS_aux/SDO_aux/INT2 are allowed) and the same axis figure (p9) as the LSM6DSV320X (DS14623 Rev 1), with ±16 g low-g, ±256 g high-g, ±4000 dps and −40…+105 °C, so it meets F1 and F2. Swapping raises cost to $84.17 against the $84.41 cap. R10_VALIDATION R18-m14 ("no JLC-stocked IMU meets both") is out of date. Watch list unchanged since 23:50Z: U9 45, D400–D421 201 for 30, J121 186, U1 812. | Owner decision, no copper change: consign LSM6DSV320XTR (ORDERING §1), or substitute C51931514 by fields only (fresh EasyEDA correction, rebind, firmware driver note) and buy the 9 at once. Correct the R18-m14 sentence. |
| R19-BOM-02 | Minor | new | C84 left the JLC BOM/CPL (D-R18-09), but F.Paste still flashes both its lands at 100 % (1.7 × 3.5 mm at (27.5, 81.75) and (27.5, 75.25)); ORDERING 8.2 says to use the paste layer exactly, so JLC prints and reflows 0.60–0.71 mm³ per bare land (Calculation). Neither the manual-fit step nor the first-article seating/height check mentions the tinned lands. No electrical effect. | Docs now: say so in ORDERING 8.2 and the order remark (or ask JLC to block the two apertures); the manual operation reflows both lands fully and checks standoff. If the board is rebuilt anyway, drop F.Paste from M3_MA_8x10 and exempt it in paste_check. |
| R19-BOM-03 | Minor | new | REQUIREMENTS line 89 says LS120 is the only part rated above −40 °C at the cold end. Not so: LED1 NCD0805R1 −30…+85 °C (Nationstar p1), J3 TYPE-C-31-M-12 −30…+80 °C (HRO note 5), J430 472192001 −20…+85 °C (JLC/LCSC/Arrow listings; Molex spec not reached). J430 may have zero margin at the −20 °C bay floor; J3's +80 °C is below the 85 °C unshaded case (bench-only, unmated in flight). | Rewrite the sentence with the four parts and their ratings; confirm J430 from the Molex specification. |
| R19-BOM-04 | Minor | carried R18-BOM-02 | DB125: 1.30 mm holes / 1.90 mm lands on all 23 contacts against DORABO T0-1 Ø1.20 (pin 0.50 × 0.85). Unchanged. Wire entry re-checked: DORABO entry face 3.50 mm from the pin row (back 3.90); fresh EasyEDA outlines/arrows put the entry on local +y like ours, so J1/J400/J121 face west and J9/J410/J420/J122 east. | No CAD change; keep R18-m11's first-article fill and preview checks. |
| R19-BOM-05 | Minor | carried R18-BOM-04 | VCAP C19/C20 (Samsung C23630, 2.2 µF X5R ±10 %) still have no maker-bounded worst case against ST's 2.2 µF ±20 %. Unchanged. | As R18-m10: bench-qualify, or an X7R part with maker curves ≥ 1.76 µF. |

## Round 18 fix verification (parts lens)

| D-ID | Verdict | Measured |
|---|---|---|
| D-R18-08 L400 | confirmed | Pads 2.0 × 1.8 mm at ±2.25 mm about F(24.2, 5.55); copper, mask and paste all 2.0 × 1.8. This matches Bourns SRP5030T p1 (6.50 / 2.50 / 1.8). Fresh EasyEDA residual 0.050 mm (EasyEDA now has a direct C1329837 record). Isat 4.3 A exceeds the AP6320x peak limit (3.1 A max). |
| D-R18-08 U4 mask | confirmed | B.Mask openings equal the 0.575 × 0.35 lands, so webs are 0.150 mm. Paste 0.5405 × 0.329 (88.4 %, TN1383 70–90 %). Land is the ST pad + 0.1 mm (TN1383 Rev 1 p6). DRC lib_footprint_mismatch 0. |
| D-R18-09 R430 | confirmed | C2999509: 84,923 at JLC, minimum 1, $0.0021. FOJAN: 1/10 W, 75 V, ±100 ppm/°C, −55…+155 °C, 240–260 °C reflow. Land 0.85 gap / 2.45 overall / 0.95 width, inside FOJAN p12's 0.80–1.10 / 2.00–2.50 / 0.80–1.00. Reconstruction 0.072 mm. |
| D-R18-09 C84 | confirmed (residual R19-BOM-02) | JLC BOM 81 lines / 197 parts; CPL 197 rows (66 top + 131 bottom), no C84; owner BOM has C84. |
| D-R18-02 R119 | confirmed | C25741 line qty 3; CPL Bottom 180; residual 0.003 mm. Stress ≤ 7.0 V / 0.49 mW (16.6 V / 2.7 mW at the 19.9 V clamp) against 50 V / 62.5 mW. |
| D-R18-01 R123, R62/R63 | confirmed | 2 k C4109 on the same land, ≤ 2.4 mW. R62/R63 are gone from every file (C25744 qty 17 → 15). 649 pin nodes agree. |
| D-R18-05 R173 | confirmed | CPL (16.87, −59.7) Bottom 270; residual 0.003 mm. |
| D-R18-09 supplier refresh | confirmed | Live 01:41–01:44Z: only U4 is short. Recomputed $54.334 + $24.786 = $79.12, with no unit-price change since the cost check. 36 Basic / 45 Extended. |
| D-R18-11 K-lands | confirmed | 37 SHA-256 pins equal the library files; the 9 unpinned footprints are the generated ones (46 in use). |

## Closed independently (no finding)

- **Identity.** kicad-cli 10.0.7 netlist, native board, JLC BOM/CPL and owner BOM agree: 208/208 parts, 198 fitted, 0 mismatches. 132 duplicate "LCSC Part" fields all equal "LCSC". All 81 MPNs, packages, values and ratings equal the supplier records.
- **Orientation.** All 197 CPL rows were rebuilt from fresh EasyEDA records (82/82 codes). Every pad lands on our same-numbered pad. Worst residuals: R134 0.491 and LS120 0.45 (land size); Q120/Q121 paddle anchor 0.35. Q124's EasyEDA drain pads 5–9 lie inside our merged pad 5. The 12 C21190 "placement-only" rows now reconstruct directly (0.072 mm).
- **Polarity.** LED1, LED2, D9, D123 and LS120 pin labels match our nets. C8591's EasyEDA label is wrong, but the JCET BAT54A sheet (pin 3 common anode) matches our wiring.
- **R0402 land** (R119, R123 and 33 others). It is JLC/EasyEDA's own R0402. Its 0.294 mm gap departs from UNI-ROYAL's 0.50 ± 0.05; width and outer extent conform. Round 14 assessed it; not raised.
- **Ratings.** Capacitor voltage ratings are all ≥ 2 × steady state, and above the 19.9 V TVS clamp wherever a capacitor is exposed to it (C89/C95 25 V, C120 25 V against 16.6 V). Steady resistor loads peak at about 29 mW of 100 mW. L1 Isat 3.2 A (supplier) against the 3.1 A peak limit. Bottom-side UNI-ROYAL resistors see 2 reflows, which is their rated limit.
- **Lifecycle.** LCSC reports "normal" for 81/82 codes; L1 C57269 has no LCSC record (JLC stock 40,726).
- **DRC.** 0 violations (all severities), 0 unconnected, 0 parity.

## Fix now

No CAD change. Any board edit restarts the clean-review pair, and the U4 choice belongs to the owner. Docs only:

1. **R19-BOM-02:** add the C84 paste note to ORDERING 8.2 and the order remark.
2. **R19-BOM-03:** correct REQUIREMENTS line 89.

## Limits

- The JLC bottom-side rotation convention is still an Inference; the placement preview remains the release check.
- ISM6HG256X registers and noise were not compared, and its stock of 9 is a snapshot.
- J430's temperature range comes from listings only.
- Stock and prices are 2026-10-31T01:41–01:54Z snapshots.
- No physical or firmware qualification is claimed.
