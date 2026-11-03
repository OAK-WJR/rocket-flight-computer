# Round 1 parts research — candidates, not a qualified BOM

No parts, lands or circuits have been frozen. These results support the plan review;
they do not constitute an R10 stock/cost gate or assembled-board qualification.

## Candidate stock

JLC public component API queried at 2026-10-27 00:46:08 UTC (2026-10-26 locally):
`https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`.
The temporary raw snapshot SHA-256 was
`42f926cc25c6884c13a19b464c58e6304009a3bf5731e8c046f2c8bbcf6ef06d`.
Stock is time-sensitive; rerun against the final BOM using `tools/jlc_stock.py` and
`tools/jlc_cost.py`. The raw snapshot is not a committed qualification artifact.

| LCSC | Part | Stock | Classification / minimum |
|---|---|---:|---|
| C2071056 | AP63205WU-7 | 48,394 | Extended / 1 |
| C161690 | BM02B-GHS-TBT(LF)(SN) | 71,734 | Extended / 1 |
| C20088623 | BM02B-GHS-TBT alternate listing | 0 | Extended / 85; not selected |
| C161692 | BM04B-GHS-TBT(LF)(SN) | 31,698 | Extended / 1 |
| C46550466 | MA25V470M8x10 | 121,382 | Extended / 1 |

The AP63205 candidate does not close the camera/radio input-voltage budgets;
see R10_DECISIONS D-R1-03. Stock availability does not make it an approved choice.

## C84 documentation correction

The parts reviewer located an [LCSC-hosted MA-series datasheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf)
linked to [C46550466](https://www.lcsc.com/product-detail/C46550466.html).
The root independently opened it: p.4 lists MA25V470M8X10, 470 µF, 25 V,
25 mΩ at 100 kHz and 4.1 A ripple at 105 °C/100 kHz. Page 1 specifies ±20%
initial capacitance, endurance capacitance change within ±20% of initial and
ESR at most 150% of initial. Page 2 supplies dimensions. This supersedes the
plan's assertion that no datasheet has been located. Manufacturer provenance,
assembled height, land and reflow compatibility still require final qualification;
the nominal 8 × 10 mm can is not proof of mounted height.

## Black 3.5 mm terminal candidate

Parts reviewer found DORABO DB125-3.5-2P-BK-S,
[C52993880](https://www.lcsc.com/product-detail/C52993880.html).
Sources: [maker family specification](https://www.nbdibo.com/product/plug-in-terminal-block/db2ekrm-3-81-through-the-wall-terminal.html),
[maker drawing](https://www.nbdibo.com/wp-content/uploads/2020/06/DB125-3.5-XXP-C-S.pdf),
[supplier-linked drawing](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf),
[supplier footprint](https://easyeda.com/api/products/C52993880/components).
Reviewer reports 10 A UL/CUL, 13.5 A IEC, 28–16 AWG, 4–5 mm strip, 0.2 N·m
maximum screw torque and Ø1.3 mm recommended holes; live JLC stock 675, Extended,
minimum 1 during the review. These are candidate research, not a final approved
terminal record. Root has opened the maker drawing but has not qualified the land.

Reviewer measured supplier footprint pitch 3.50012 mm and Ø1.8 mm copper pads:
nominal gap 1.70012 mm. Its Ø1.2 mm holes differ from the maker recommendation.
Do not import it blindly. A proposed Ø1.3 mm drill / Ø1.9 mm copper pad gives a
calculated 1.6 mm gap and 0.3 mm radial annulus; **Inference:** this is a feasible
land until manufacturing tolerances, mechanical drawing and actual R10 copper are
checked. J124's required ≥1.5 mm gap must be measured on the actual board including
adjoining copper. This supplier measurement is not that gate result.

## GH connector constraints

[JST GH specifications and drawings](https://www.jst-mfg.com/product/index.php?lang=2&series=105).
GH is rated 1 A with AWG26: qualify actual load and harness. Existing J9's GH4
land/model is a starting point; GH2 needs a new land/model and mated envelope.
`tools/jlc_orient.py` handles GH4 mechanical tabs; GH2 needs explicit mechanical-pad
mapping derived from the chosen local footprint, including tab left/right order.
Do not reuse R9 terminal pad aliases without checking physical wire entry.
