# R10 round 31: parts lens

Target commit `3366287`, board SHA-256 before and after
`a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (unchanged). Reviewer: Claude. Strict real-error
rule (`.supervisor/r31_review_brief.md`).

**Totals: 0 Critical, 0 Major, 0 Minor.** No real error was found. 12 observations, none counted.

## What was checked

- **BOM / CPL / board agreement.** A read-only pcbnew script (`.supervisor/r31_parts/xcheck.py`) compared every
  footprint with `m3_bom_jlc.csv`, `m3_bom_owner.csv` and `m3_cpl_jlc.csv`. All 206 placed parts and C84 agree on LCSC
  code, maker part, footprint and side. CPL positions equal the footprint origins except J3 and J430, which are the JLC
  footprint-origin offsets that `jlc_orient --verify-cpl` rebuilds. All 82 codes' JLC model strings in `stock_check.json`
  (12:43:17Z) match the BOM's maker parts, designators and quantities. The cost arithmetic reproduces ($60.47 +
  $123.93 / 5 = $85.26; $83.96 / 5 = $16.79).
- **Value against maker part and land.** Every line's code was decoded: Samsung, Murata, Yageo and Fenghua capacitor
  codes; UNI-ROYAL J / K / L multipliers (0603WAF220KT5E = 2.2 Ω, 25121WF360LT4E = 0.36 Ω); CRM2512-FX (1 %, 100 ppm);
  MCT0603MD2004BP500 (2 MΩ, 0.1 %). Each agrees with its Comment and land size. The 19 `circuit.json` value overrides
  match the round 9 table.
- **Ratings at the operating points.** From the board's pad nets (`nets.py`):
  - capacitor voltage against each net's maximum (19.9 V SMBJ12CA clamp on BAT_IN, 10.18 V OVLO corner on
    RAW_PROTECTED);
  - resistor power and working voltage;
  - FET Vgs and Vds;
  - TPS25947 EN 4.81 V and OVLO 2.44 V at the clamp, against 6.5 V;
  - TPS7A91 and TPS2553 inputs at most 5.546 V, against 6.5 V.

  All are within rating.
- **Datasheet facts in `parts_qualification.md` (after audit A).** The cached maker PDFs were re-read for AONR21357,
  AO3400A, AON7524, BAT54, SRP5030T, CRM2512, TPS25947, TPS7A91, TPS2121, TPS709, AP6320x, ESD103, UNI-ROYAL, the MA
  series, NX3225GA, MLT-5020 and LSM6DSV320X. Every fact checked matches the record. The file's calculated figures
  were recomputed and all reproduce: R430 / R85 limits, rails and endpoint minima, U401 thermal, the D402 EN shift, the
  gate RCs, the watchdog guard, the CRM2512 chart figures, U9's limit and demand, the CONT / BUS bands, R166's corner and
  the USB attach charge.

## Fix verification

| Item | Measurement | Verdict |
|---|---|---|
| R30-TRI-01 (the BAT54 drop in the bridge figures) | Own solve: RAW_ACT 2.2049 / 2.1913 V and match current 0.1074 / 0.1087 mA at Vf 0.20 / 0.24 V. The JSCJ BAT54 VF maximum is 0.24 V at 0.1 mA, so the range is labelled Inference as written. 11.2 k ∥ (11.2 k + 4 Ω) = 5.6 kΩ. | confirmed |
| R30-TRI-02 at `parts_qualification.md`:40 | The pass criterion is now every 85 °C part ≤ 85 °C. LS120's rise is recorded and it is not a pass / fail gate; the best-effort limit is 70 °C minus the measured rise. MLT-5020 p2 item 6 gives −20…+70 °C. | confirmed |
| D-R29-01 (C126 tolerance in rule 3) | C126 code K = ±10 %. R = 238.56 Ω and C = C126 + 2.25 nF give 47.77 / 53.02 / 58.27 µs, as stated. | confirmed |

## Observations (not counted)

1. BOM, CPL and board fields agree. JLC's model strings match all 82 codes.
2. The J3 and J430 CPL offsets are JLC footprint-origin corrections; J430's +1.550 mm is recorded.
3. Every value and maker-part decode agrees with its land.
4. R134's 0.491 mm residual is within the two-pad 0.6 mm rule with zero offset, and LS120's 0.45 mm is under its
   recorded 0.451 mm tolerance.
5. Capacitor voltage ratings are adequate on every net.
6. Resistor power and working voltage are well inside rating. The largest 0402 load is about 16 mW at the clamp.
7. Semiconductor ratings hold at the clamp and OVLO corners. A floating TPS709 EN is the datasheet's permitted enable.
8. The datasheet facts re-read from the cached PDFs match the records.
9. The recomputed `parts_qualification` figures all reproduce.
10. L400 is 6.8 µH and L1 is 4.7 µH. DS41326 Tables 1–2 give 10 µH and 3.9 µH, but both are inside its 2.2–10 µH
    guidance, and no current record claims the table values.
11. Part positions quoted in the records match the board for 44 references.
12. M3_R10:1040's L1 / C88 / "J400 shell pad" figures sit under the historical mechanical record and are labelled to
    `877d0199…`; this is the mechanics lens's area.

## Coverage limits

- No live supplier or web lookup was made. LCSC identity rests on JLC's model field in the committed stock check.
- No cached text exists for SWPA4030S4R7MT, the TYPE-C-31-M-12 drawing, the DB125 drawing or DS15034 (ISM6HG256X), so
  their recorded facts were not re-read.
- Lands were not re-measured against maker drawings; the review relied on the committed `jlc_orient` match.
- Read-only lens: no `tools/check.sh`, build or seed run.
