# R10 round 30 — parts lens (Claude)

Target commit `0afaed3`, board SHA-256 `a0ec075e…2e733c` before and after (identical). Read-only; probes in
`.supervisor/r30_parts/`.

## Totals

| Critical | Major | Minor |
|---|---|---|
| 0 | 0 | 0 |

No real errors found.

## What was checked

- **BOM / CPL vs board:** all 206 CPL rows and 82 codes (81 JLC + C84 on the owner BOM) agree with the board's LCSC,
  Manufacturer Part and footprint fields. Side and position also agree, apart from the two recorded JLC centroid
  offsets (J3 and J430).
- **Schematic vs board:** every footprint matches its symbol's Value, LCSC, Manufacturer, Manufacturer Part and
  Footprint. The 130 duplicate `LCSC Part` fields repeat the same code.
- **Value vs part number:** every line decodes to its Comment. UNI-ROYAL `220K` is 2.2 Ω and `360L` is 0.36 Ω. The
  Vishay MCT0603 2 MΩ is a 0.1 % / 25 ppm/K part inside its range.
- **Rotation:** `jlc_orient --verify-cpl` passes: 67 top + 125 bottom rows, worst residual 0.491 mm, no errors, and
  14 placement-only rows.
- **Pinouts:** checked against the maker pin maps for BAT54A, SRV05-4, USBLC6-2SC6, D9 / D123 polarity and LS120
  polarity (MLT-5020 p4). All agree.
- **Ratings vs operating points:**
  - Capacitor voltage ratings hold against the 10.18 V OVLO corner.
  - The TVS, ESD and MOSFET gate limits are not exceeded.
  - Resistor dissipation is within rating. R134's pulse reproduces 35.80 W against the 61.2 W chart read, a 1.23×
    margin.
- **parts_qualification calculations:** these reproduce: R430 at 1.041–1.249 A, R405 at ≥ 5.63 mA, GAP-3 at 0.490 W /
  109.2–123.9 °C, the 5.880831 V pack sag, the continuity table, the 3.342 V fault value, the C126 and IWDG timings,
  the DB125 diagonal, the VCAP envelope, and D402's 5.7 mV / 14 mV.
- **Datasheet facts:** these agree with the cached maker PDFs: AONR21357, AON7524, AO3400A, TPS7A91, TPS2553 rev G,
  TPS2121, AP6320x, SRP5030T, ESD103, BAT54, Yageo RT and the DORABO T0-1 drawing.
- **Supplier figures:** the figures in AGENTS, M3_R10, ORDERING §8.1, R10_VALIDATION and parts_qualification match
  `cost_check.json` / `stock_check.json`. Both files bind the committed BOM hashes.

## Fix verification

- **R29-TRI-04 (LS120 rated to +70 °C):** confirmed. The MLT-5020 sheet (p2 item 6) gives −20…+70 °C. The note
  appears in parts_qualification, REQUIREMENTS, M3_R10 (the chamber pass needs LS120 ≤ 70 °C) and owner row 36. The
  48 °C figure reproduces as 70 − 22.
- **D-R29-01 / -02:** no parts impact. The BOM and CPL are unchanged and still bound.

## Observations

There are 11, listed in the JSON. None is counted.

The one open point is LED polarity. LED1 and LED2 depend on JLC's library pad numbering, and the records already
send that to JLC's placement preview.

## Coverage limits

- No live supplier queries were made.
- The historical sections of parts_qualification were not re-audited.
- Lands were checked only through the EasyEDA residuals and the existing records.
