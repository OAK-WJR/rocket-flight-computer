# R18 parts / BOM / footprints / orientation / stock (Claude)

Target commit `dcbb6c8f040b7012f78934e1caf1b401db84d356`. PCB SHA-256 before and after:
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982` (unchanged; tracked tree unchanged).
Detailed evidence, sources and limits: [round18_parts.json](round18_parts.json). Probe scripts and raw supplier
responses: `.supervisor/r18_parts/` (ignored).

**Totals: 0 Critical, 0 Major, 4 Minor (all carried, with new evidence).**

## Findings

| ID | Sev. | Status | Finding and key number | Fix |
|---|---|---|---|---|
| R18-BOM-01 | Minor | carried R17-BOM-04 | Stock still blocks release. Live JLC query, 2026-10-30 19:24–19:45Z: R430/C185349 has 17 in stock against a 3,610 minimum purchase; U4/C26633007 has 0. U9/C3662793 fell from 83 (17:15Z) to 78, has a minimum purchase of 7 and no LCSC presale stock. **R430 drop-ins** (same 22.6 kΩ ±1% ±100 ppm/°C, 0.1 W, 75 V, 0603, same land, nonpolar): **C2999509 FOJAN FRC0603F2262TS** (84,923, min 1) or **C403080 Panasonic ERJ-3EKF2262V** (5,007). **U4:** no JLC-stocked part meets both F1 (±4000 dps) and F2 (≥±64 g). LSM6DSV80XTR C46898862 (±80 g) has 0 in stock. LSM6DSV32XTR C22461202 (5,295) and LSM6DSV16XTR C5267406 (15,397) fit the land but fail F2. **U9:** TPS259470ARPWR C3662799 (2,591) has the same package and pins, but its fault response is auto-retry instead of latch-off (TI Device Comparison Table p4), so it is not a pure drop-in. Live cost is $79.43/board placed plus feeder, or $81.77 with minimum purchases; swapping R430 brings that to $79.97. | Change R430's fields to C2999509, or to C403080, and add its jlc_corrections key. Consign U4. Reserve the seven-piece U9 minimum now, or decide on the auto-retry variant. |
| R18-BOM-02 | Minor | carried R17-BOM-02 | DB125: the 23 contacts use 1.30 mm holes with 1.90 mm lands; DORABO T0-1 recommends Ø1.20. The maker's pin is 0.50×0.85 mm (0.986 mm diagonal), which leaves ≥0.234 mm clearance at JLC's 1.22 mm minimum finished hole; the annular ring is ≥0.235 mm against JLC's 0.20 mm minimum. The carried 0.70×1.05 mm corner case would not even fit the maker's own 1.20 mm hole, so it is not a credible insertion failure. The S-8 fabrication allocation at J121.1 (1.102502 mm nominal) and the hand/selective-solder fill remain open. | No CAD change. Close the insertion sub-item. Keep the fabricator S-8 allocation and first-article seating/fill checks. |
| R18-BOM-03 | Minor | carried R17-BOM-01 | L400 has a proxy land: 1.8×2.5 mm pads at ±2.35 mm. Bourns SRP5030T p1 recommends 2.0×1.8 mm at ±2.25 mm. The outer extent (6.50 mm) is equal; at worst tolerance about 0.15 mm of the terminal heel lies off the pad. | Use Bourns' land only if the board changes for another reason; otherwise inspect heel wetting on first articles. |
| R18-BOM-04 | Minor | carried R17-BOM-03 | C19/C20 (VCAP) are Samsung C23630, 2.2 µF X5R ±10%. ST allows 2.2 µF ±20% with ESR <100 mΩ (DS12110 Rev 8 Table 25 p109). With generic X5R tolerance, temperature, bias and aging allowances the worst case is about 1.52 µF, below 1.76 µF (Inference, not maker curves). | Bench-qualify, or adopt a reviewed X7R part whose maker curves bound ≥1.76 µF. |

## Closed independently (no finding)

- **Identity:** the kicad-cli 10.0.7 schematic netlist, the native PCB and the BOM/CPL agree. That covers 209 symbols, 199 fitted parts, 82 rows and 651 pin-net nodes, with 0 mismatches in LCSC/MPN/maker/value/footprint/net/quantity. All passive package sizes match their codes.
- **Orientation:** my own y-up reconstruction of all 199 CPL rows against fresh EasyEDA footprints puts every pad on our pad of the same number. R134 (0.491 mm) and LS120 (0.45 mm) differ only by land size; every other residual is ≤0.25 mm (MOSFET pins 0.100 mm). Polarity marks map correctly for LED1, LED2, D9, D123, C84, LS120 and D120. All four DB125 EasyEDA footprints mark the wire entry on local +y, the same side as ours, so no body correction is needed. The T0-1 third-angle views place the entry face 3.50 mm from the pins, also matching ours. The EasyEDA 5P outline is mirrored in depth; that affects the library only, not placement.
- **Lands checked against the makers:** Molex SD-47219-001G; TI RPW (U9 paste at 93%/82%, as TI's stencil), RUX, DCU and DSK; U4 meets the TN1383 +0.1 mm rule with 88% paste; U1 has equal outer extent to ST; MS5611 has no foreign copper in TE's reserved area; AOS PO-00047; HRO; NDK; Infineon TSLP; Bourns CRM2512; UniOhm 2512; Diodes TSOT26; Littelfuse SMB.
- **Ratings:** all within limits. R134 sees 35.8 W for 36 ms against about 46 W on the Bourns pulse curve (an interpolation, so Inference). C128 is a soft-termination GCJ part, the only MLCC across the fire path: keep it unmerged.

## Fix now

1. Swap R430's metadata to C2999509 (or C403080). No copper changes, but the board hash does, so it needs the usual rebind.
2. Reserve the U9 minimum or consign it.
3. Optional: give C22 the C29936 code to drop one feeder code. Do not merge C128.
