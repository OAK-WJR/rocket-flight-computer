# R20 parts / BOM / CPL / lands / ratings / stock (Claude)

Target commit `6628488cf34bf33bdf104cb4383fcbe447c5da65`. PCB SHA-256 before and after:
`50a39de5b76dec3cb58bbb1b0ab528fd4d65098de9dfe8f89f49e2e7adcbd976` (unchanged; no tracked file edited).
Evidence, sources and limits: [round20_parts.json](round20_parts.json). Probe scripts, raw supplier and EasyEDA
responses, renders and DRC output: `.supervisor/r20_parts/` (ignored).

**Totals: 0 Critical, 0 Major, 3 Minor (1 new, 2 carried).**

## Findings

| ID | Sev. | Status | Finding and key number | Fix |
|---|---|---|---|---|
| R20-BOM-01 | Minor | new | U4 ISM6HG256XTR C51931514: JLC shows stockCount 9 but canPresaleNumber **2** for 5 needed (09:54Z; the round 19 probe at 01:54Z also had 2). LCSC stock is 0. Every other line has canPresaleNumber at least twice its need. `jlc_stock.py` reads stockCount only. The project has read canPresale as the orderable quantity before (ORDERING line 34 "available −33"; ROCKET_FC_FROZEN_DESIGN "oversold"). On that reading U4 is 3 short, not thin. This is an Inference: JLC's field meaning is not documented. | Gate on min(stockCount, canPresaleNumber). Restate ORDERING 8.1 and REQUIREMENTS M1 as "9 in stock, 2 orderable". On order day, put U4 in the cart first or pre-buy it, else start the LSM6DSV320X consignment path (already in 8.1). |
| R20-BOM-02 | Minor | carried R19-BOM-04 | DB125 holes 1.30 mm / lands 1.90 mm against DORABO's 1.20 mm on every contact, now including J440. J440 reconstructs with a 0.000 mm residual at Top 270, like J1 / J400. | No CAD change; first-article fill check, add J440. |
| R20-BOM-03 | Minor | carried R19-BOM-05 | VCAP C19 / C20 (C23630 X5R) still have no maker-bounded worst case. | As R18-m10. |

## Round 19 fix verification (parts lens)

| D-ID | Verdict | Measured |
|---|---|---|
| D-R19-04 C123 | confirmed | F(18.22, 71.85) 0°, ACT_EN / GND; C15195 10 nF X7R 50 V ±10 % (LCSC live), on line C123,C408 (qty 2); residual 0.000 mm; F.Paste 0.50 × 0.54 on both pads. |
| D-R19-07 C84 paste | confirmed | M3_MA_8x10 pads F.Cu and F.Mask only. No F_Paste flash within 0.3 mm of (27.5, 81.75) or (27.5, 75.25); mask openings 1.7 × 3.5 remain. Paste F 257 / B 371. |
| D-R19-10 C87 | confirmed | C21120 220 nF X7R 25 V on the same 0603 land at F(17, 65), BAT_ENABLE / GND; residual 0.000 mm. EN ≤ 2.06 V. |
| D-R19-11 U4 | confirmed (residual R20-BOM-01) | DS15034 p9 Fig. 5 is identical to DS14623 p9 when rendered side by side. Table 2 allows our GND on SDx / SCx and NC on OCS_aux / SDO_aux. p187 gives 0.475 × 0.25 mm pads. The board's B.Cu pads, seen from the top, equal ST's bottom view. The EasyEDA footprint changes from TL (LSM) to BR (ISM), exactly 180° apart; the CPL at Bottom 180 rebuilds 0.040 mm on all 14 pads. The B.SilkS pin-1 dot is 0.70 mm from pad 1. −40…+105 °C (p14). |
| D-R19-14 J440 cell | confirmed | Same codes and topology as J410 / J420 (nets checked pin by pin). Residuals: J440 0.000, C444 0.075, C445 0.017, D440 / D441 0.005, R470 / R471 0.072 mm. Ratings fit (C21397 25 V, C535146 Vrwm 15 V bidirectional, C2757925 300 V / 10 A). Stock: C2757925 37,802 for 20, C535146 201 (194 orderable) for 40. |

## Closed independently

- **Identity.** kicad-cli 10.0.7 netlist, native board, JLC BOM / CPL and owner BOM agree: 215 / 215, 206 fitted, 205 CPL rows (AGENTS' 205 is correct), 666 pin nodes, 0 mismatches.
- **DRC** (kicad-cli 10.0.7, all severities, schematic parity): 0 / 0 / 0, including lib_footprint_mismatch.
- **Orientation.** All 205 rows were rebuilt from EasyEDA footprints: fresh records for the 9 changed codes, the round 19 same-day cache for the rest. Each pad lands nearest its own number. The outliers are known land-size or merged-pad cases: Q124 1.789 (merged drain), R134 0.491, LS120 0.45 and Q120 / Q121 0.35 mm.
- **Values, MPNs, packages.** All 82 codes match JLC's model and LCSC's parameters. 36 Basic / 45 Extended confirmed live.
- **Consigned-LSM rotation trap.** ORDERING 8.1 (R10) already says the LSM6DSV320X needs its own 0° CPL row. The R9 sections that omit this are history.
- **Cost (note only).** Live parts $60.57 (incl. C84) + feeder $24.79 = **$85.35** per board against $84.41. This is the open owner decision.

## Fix now

None in CAD. R20-BOM-01 is a gate and docs change (`jlc_stock.py`, ORDERING 8.1, REQUIREMENTS M1) plus an order-day cart check.

## Limits

- The JLC bottom-side rotation convention and the meaning of canPresaleNumber are Inferences. JLC's placement preview and the cart quantity are the release checks.
- I checked the unchanged usual-set lands (DB125, microSD, U9, U1, U5, Q120 / Q121 / Q124, USB-C, crystal) only by EasyEDA rebuild and DRC library parity. Their maker-drawing comparisons are carried from round 19; the library is unchanged except M3_MA_8x10.
- Stock and prices are a 2026-10-31T09:54–09:57Z snapshot. No physical or firmware qualification is claimed.
