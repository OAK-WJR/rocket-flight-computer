# R23 parts: lifecycle, derating and logistics (Claude)

- **Target commit:** `c70d261`.
- **PCB SHA-256, before and after:** `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` (unchanged; no tracked file was edited).
- **Evidence:** [round23_parts.json](round23_parts.json). Probes: `.supervisor/r23_parts/` (ignored).
- **Angle:** lifecycle, derating at a 70 °C bay and consignment logistics, plus the CPL rotation for the U9 / U4 alternates. Round 22 did the BOM-to-land match.

**Totals: 0 Critical, 0 Major, 3 Minor (all new).**

## Findings

| ID | Sev. | Finding and key number | Fix (text only) |
|---|---|---|---|
| R23-PARTS-01 | Minor | The hot-end derating compares the 85 °C ratings with the 70 °C bay air. The records' own heating Inference (2.6–4.4 W at 10–15 °C/W) puts the board **26–66 °C above the bay** at full camera and port load. That affects the X5R parts on the power paths (C6/C7 VLOGIC, C8–C11, C80/C96 and C89/C95 BAT_IN, C19/C20) and U2 / U400 (AP6320x, TA ≤ 85 °C, "function not guaranteed outside", DS41326 p4). The first-article run thermocouples only U401 / U400 / L400. | State the board-temperature basis. Add C6/C7, U2, C89, Y1 and U3 to the owner row 26 / ORDERING 8.3 measurement, with the pass criterion ≤ 85 °C. |
| R23-PARTS-02 | Minor | "Consign U4 / U9 to JLC" leaves out JLC's actual process: a Hong Kong warehouse, a price review of up to 2 business days with purchase records, a refundable duty + 13 % VAT deposit, and a 2 % handling fee (minimum USD 10 per shipment). It also leaves out moisture handling (U9 is MSL 2 / 1 year per SLVSFC9C p68; U4's MSL is not stated in DS15034 p185), the carrier, and the quantity to buy. | Add a dated consignment paragraph to ORDERING 8.1: buy 7–10 of each, ship them in a sealed moisture-barrier bag, and confirm the carrier and bake. |
| R23-PARTS-03 | Minor | round22_alternates §2.2 calls the LSM6DSV320X swap "BOM fields only". It also needs U4's CPL rotation changed from Bottom 180 to **Bottom 0**. Kept at 180 with the LSM footprint, the pads are off by **2.892 mm**. | Add the rotation, regenerate and `--verify-cpl` steps to §2.2 / §2.3 and to ORDERING option (d). Add C46898862 to `pads.json`. |

## Alternates (brief items)

- **U9 C3662799 (TPS259470ARPWR).** EasyEDA (lceda.cn, 04:53Z) gives the same footprint as C3662793: `VQFN-10_L2.0-W2.0-P0.45-TL`, all 10 pad strings identical. `jlc_orient` gives θ 0 with a 0.200 mm residual, the same as the fitted part. `--verify-cpl` with the shipped Bottom 180 passes all 205 rows. **No CPL correction is needed.** TI lists it Active, MSL 2. JLC had 2547 in stock and 2349 orderable at 04:57Z.
- **U4 C26633007 / C46898862 (LSM6DSV320X / 80X).** Both use the same EasyEDA TL footprint: θ 0, 0.052 mm residual. Bottom 0 passes verification. **The records' 0° claim holds** for both parts. The fitted ISM part (BR footprint) is θ 180, 0.040 mm, so it stays at Bottom 180.

## Lifecycle

- **Maker status read and none flagged:** the TI parts U9, U10/U402, U11, U12, U13 and U401, and the alternate TPS259470A, are ACTIVE (ti.com, 04:55Z). AONR21357 is Full Production, ESD103 is Active, and SRP5030T carries no NRND mark.
- **Diodes B340A / AP6320x:** no EOL PCN covers these part numbers. PCN-2623 lists only the B340A "-2477" variants.
- **SRV05-4:** Semtech's page sells it and shows no NRND mark. One aggregator says "Not For New Designs" (unresolved).
- **ST and TE:** ISM6HG256X shows Active (search snippet). st.com itself was not reachable. TE parts are Active per distributors.
- **Brands:** all 82 JLC codes carry the original maker's brand. The AONR21357 code is AOS's own part, not one of the clone listings.

## Derating at 70 °C (summary; full table in the JSON)

Every rating has its datasheet page in the JSON.

- **Voltage:** every power-path part is at 85 % or less of its recommended maximum. The tightest are:
  - PORT_5V3, at 5.52 V static, against the 6.5 V recommended maximum of TPS7A91 / TPS2553 (7 V absolute maximum);
  - D8, standing off 8.4 V against its 12 V V_RWM.
- **Q120 / Q121:** VDS, VGS and current are each about 28 % or less of rating, the current against IDSM 17 A at 70 °C.
- **R134 pulse:** 35.3 W into a shorted match. The interpolated chart allows 62.6 W at 20 ms (56 % used) and 46.9 W at the 34.853 ms watchdog bound (75 % used).
- **Resistors:** 30 % or less of their 70 °C rating.
- **L400:** at 39 % of its rms rating and 43 % of Isat.
- **Temperature:** see R23-PARTS-01.

## Fix verification

| D-ID | Verdict | Measured |
|---|---|---|
| D-R22 (all) | confirmed | Board hash identical at `ec8cb98` / `c70d261`. BOM, CPL and owner-BOM hashes are unchanged. The Gerbers differ only in timestamps. |
| D-R22-03 | confirmed | R104 / R105 are 10 k / 1 k at 1 %: 19.9 V reads 1.81 V. R104 dissipates 33 mW (transient). |
| D-R22-04 | partly | Text confirmed; the J3 geometry was not re-measured. |
| D-R21-05 | confirmed | C87 is C21120, 25 V X7R: 2.06 V is 8.2 % of its rating. R81 dissipates 14 µW. |
| D-R19-11 | confirmed | The EasyEDA BR footprint is unchanged: θ 180, 0.040 mm, and the shipped CPL verifies. |
| D-R19-10 / D-R19-14 | confirmed | C87 is C21120. C2757925 × 4 and C535146 × 8 per board are in stock for 5 boards. |

## Fix now

All three are text only, with no board change: R23-PARTS-03, then R23-PARTS-02, then R23-PARTS-01.

## Comparison with round 22

Round 22's report was opened only after these findings were written.

- R22-PARTS-01 covered franchised availability. R23-PARTS-02 adds the JLC-side process.
- R23-PARTS-01 and R23-PARTS-03 are new.
- R22-PARTS-02 and R22-PARTS-03 are outside this round's angle and are not re-filed.

## Limits

- st.com timed out, so there is no ST lifecycle or MSL from the maker.
- easyeda.com returned 403, so the lceda.cn mirror was used. It matches the cached data.
- AOS (AO3400A, AON7524), Murata, Molex, Winbond, NDK and the passive makers were not read at the maker.
- JLC's consigned-part packaging, MSL and attrition rules are not published.
- The CRM2512 chart points are the records' reading.
- The board self-heating figures are the records' Inference.
