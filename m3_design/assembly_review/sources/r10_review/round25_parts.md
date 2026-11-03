# R10 round 25 — parts lens (Claude)

Target `c4bb56b`; board SHA-256 `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` before and after.

**Totals: 0 Critical / 0 Major / 0 Minor.** No real errors found.

## Checks
- Every BOM and owner-BOM designator's LCSC, maker part and footprint fields agree with the board. Each CPL row's side, position and rotation matches the board, except J3 and J430, whose JLC centroid offsets are deliberate. All 216 footprints are in the BOM, the owner BOM or the excluded set.
- CPL has 206 rows (70 top / 136 bottom). Paste flashes are 249 / 381. There are 81 JLC lines (45 Extended / 36 Basic), and C84 is on the owner BOM.
- Capacitor ratings hold against their nets: the 16 V parts sit only on 3V3, VCAP, VBUS and CAM_IO_3V3. Diode and FET pin functions match their nets, and the resistor dissipation spot checks pass. L400's Isat is 4.3 A against a 3.645 A prospective peak.
- The cost and stock files recompute: $60.81 + $24.79 = $85.60, with C535146 at 9 × $0.2306.

## Fix verification
| Change | Measurement | Verdict |
|---|---|---|
| D-R24-11 D402 identity / pose | C535146 ESD103-B1-02EL E6327 ×9; CPL B(4.45, 65.9) rot 90, the same as the board | confirmed |
| D-R24-11 D402 land | 0.35 × 0.60 copper at ±0.325 mm, 0.28 × 0.45 paste at ±0.33 mm, the same as Infineon Rev 1.3 Fig. 14 | confirmed |
| D-R24-11 rating | VRWM ±15 V against J400.2 at 5.22 V (8.4 V pack) and 12.4 V (19.9 V clamp corner); the part is bidirectional | confirmed |
| D-R24-11 / -19 leakage | 5.69 mV at EN, the same as 25.0 nA; C87 rises 14.3 mV | confirmed |
| D-R24-11 geometry | 3.405 mm to J400.2; tap 4.114 mm; return 0.70 mm | confirmed |
| D-R24-11 / -23 counts | 206 CPL rows (70 / 136); paste 249 / 381 | confirmed |
| D-R24-11 cost / stock | $85.60; C535146 194 orderable against 45; U9 −83; U4 2 against 5 | confirmed |

## Observations (not counted)
1. J3 / J430 CPL centroid offsets are deliberate.
2. The round 19 J440 row in parts_qualification still says "ESD code 8". It sits in the dated section, which is superseded by the round 24 amendment.
3. The "$85.36 before D402" figure comes from a separate run. At today's prices it would be $85.37, so it cannot be shown false.
4. The Sunlord L1 PDF has no text layer, so its ratings were not re-read. L1 is inherited and unchanged.
