# Round 23 manufacturing review: JLC order forms, field by field

Target commit `c70d261`, board `5516eeec…`. The SHA-256 was the same before and after the review.

**Totals: 0 Critical, 0 Major, 5 Minor.** The machine-readable twin is `round23_manufacturing.json`.

JLC's live pages were read on 2026-11-01 (UTC):
- the PCB capabilities and assembly capabilities pages;
- the assembly terms, updated 2026-09-09;
- the help articles on via covering, via-in-pad, PCB marks (updated 2026-05-22), production-file confirmation and stackups;
- the quote form text.

## Findings

### R23-MANUFACTURING-01 (Minor): the Electrical Test field is not set, and the free option tests only a sample

- **What the docs say.** ORDERING 8.1 says "Keep JLC's bare-board electrical test". It also states as an Inference that JLC tests every four-layer board by default.
- **What JLC's form offers.** Two flying-probe options:
  - "Full Test: 100% pass rate … incurs a fee";
  - "Random Test: Free of charge, ensuring a minimum pass rate of 99%".
- **Why it matters.** Owner row 29 and M3_R10's "Mitigations" rely on this test to catch an open EN via at (17.10, 82.80) (R21-SAF-01). The per-flight off-with-J400-open check is still the second screen.
- **Fix (text only).** Specify **Flying Probe Full Test** and include its fee in the quote. Update ORDERING 8.1, M3_R10 and owner row 29 to name it.

### R23-MANUFACTURING-02 (Minor): JLC no longer offers the order-number mark

- **On the board.** The bottom silkscreen carries `JLCJLCJLCJLC` at (20.35, 35.6). The ink spans x 15.323–25.425 and y 34.980–36.130, as recorded. `r10_post` and `check_r10` require this text.
- **What the docs say.** ORDERING 8.1 says to choose "Specify a location".
- **What JLC says now** (help article updated 2026-05-22):
  - "Order Number is not available since May 2026";
  - "Please DO NOT add JLCJLCJLCJLC";
  - no mark is added by default;
  - "Specify Position" now needs a solid silkscreen square.
- **Impact.** The text will be printed as written, or JLC will raise a query. There is no functional effect.
- **Fix (text now).** Set Mark on PCB to "none / Remove Mark" and add a remark about the legacy text. At the next board change, delete the placeholder and its check.

### R23-MANUFACTURING-03 (Minor): section 8 does not give one value for every form field

Section 8 tells the reader to use sections 1–7 "only where restated". It does not restate these fields:
- Delivery Format. The form's "Panel by JLCPCB" means V-cut, which J3's overhang forbids.
- Which edges get rails, and how wide they must be. Standard PCBA needs at least 70 × 70 mm; this board is 46 mm wide, so each rail plus its gap needs about 12 mm.
- Via Covering. The form takes a single choice. "Plugged where permitted" is not one of its options: 179 of 300 vias are within 0.35 mm of a mask opening and cannot be ink-plugged.
- Tooling holes and fiducials. The board has none of either; JLC adds both by default (terms §5.5).
- Silkscreen colour.
- Product Type. Choosing Aerospace forces a 4-wire Kelvin test and FR4 Tg155.
- JLC's panel-removal option. Section 8.3 requires the owner to nibble the tabs, never snap them.

**Fix (text only).** Add an "R10 order form" table with one value per field. The proposed values are in the JSON.

### R23-MANUFACTURING-04 (Minor): the VIPPO evidence and paste overlap

- **What JLC says.** The via-covering article lets filled vias be named "with a note or image, or fill all vias of a given diameter". The docs base their refusal risk only on the capabilities page.
- **Filling by diameter means filling the whole board.** The two U401 vias are in the 0.300 mm drill group with 297 other vias.
- **Paste overlap.** U401's two paste windows leave a 0.22 mm gap over the via row. Each window overlaps the 0.30 mm drill outline by 0.04 mm and the via land by 0.14 mm. If the fill is missed, paste sits over open barrels.
- **Fix (text only).**
  - Cite the via-covering article.
  - Attach an image or the coordinates of the two vias.
  - State that filling by diameter is fallback (1).
  - Add a first-article X-ray of U401.11.

### R23-MANUFACTURING-05 (Minor): JLC's 2.5 mm body-to-edge rule is not listed as an expected query

JLC's assembly terms (§2.3) require component bodies to sit at least 2.5 mm from the board edge. The short edges carry no rails, and several parts are closer than that (courtyard to edge):
- aft edge: R400, R401 and R404 at 1.02 mm, C403 at 1.96 mm;
- forward edge: C95 1.50 mm, R92 1.72 mm, R166 1.75 mm, TP88 1.95 mm.

**Fix (text only).** List these parts in "Expected DFM queries". If JLC insists on rails on all four sides, re-run T-1 before accepting.

## Fix verification

| Item | Verdict | Measurement |
|---|---|---|
| D-R22 (all) | confirmed | Same PCB hash; BOM and CPL unchanged. All 14 Gerber and drill files are identical to ec8cb98 once their date lines are stripped. |
| D-R22-01 / -05 (board rows) | confirmed | NPTH holes are ≥ 0.6 mm and ≥ 0.200 mm from copper. Via walls are ≥ 0.25 mm and PTH walls on F/B ≥ 0.55 mm from foreign copper (independent Gerber parse). |
| D-R21-01 | confirmed | All 31 plated pad holes are ≥ 0.550 mm from foreign inner copper: J1.2, J400.2 and the J3 slots are each 0.55 mm; J121.1 is 1.05 mm. |
| D-R19-07 | confirmed | C84's lands have no paste flash. All 253 + 375 paste flashes map onto pads. |
| D-GAP-03 / R18-MFG-03 | confirmed | Only the two U401 vias have the fill and cap flags. Both sit in the ordinary 0.300 mm drill group. |
| R20-MFG-04 | partly | The placeholder's position is correct, but the JLC process it relies on is gone (finding 02). |
| Via mask (R18 / R3) | confirmed | Only the two VIPPO vias lie inside a mask opening. No via's drill wall is within 0.10 mm of an opening. |

## Closed

These match JLC's rules:
- Board: 4 layers, 1.6 mm, ENIG. The stackup equals JLC041611-7628 (third-party mirror; Inference). Inner 1 oz is stated, which the form needs because it defaults to 0.5 oz.
- Vias: 0.3 / 0.5 mm, below the form's surcharge threshold.
- Outline: 46 × 90 mm. Copper is at least 0.500 mm from the edges and from the M3 holes.
- Drill counts equal the board's. J3's 0.6 mm plated slots exceed JLC's 0.35 mm minimum.
- The 81-line BOM covers exactly the 205 CPL rows (72 top / 133 bottom).
- DRC with kicad-cli 10.0.7, all severities, with parity: 0 / 0 / 0.

Not filed:
- 29 same-net vias have mask slivers under 0.10 mm. The existing "tent" disposition covers them.
- The tab plan and cost are owner decisions.
- U4 / U9 consignment is an ordering item.

## Comparison with round 22

I read round 22's report only after writing the findings above. It had none of findings 01–05. It mentioned fiducials (part of 03) as an optional one-line addition.

## Fix now

All five are text only: 01, 02, 03, 04, 05.

## Coverage limits

- Nothing was uploaded to JLC: no DFM check, quote or rail preview. The quote page was read as text.
- The stackup values come from a third-party mirror.
- Inner via barrels without rings are not in the Gerbers.
- The D-R22 check-code changes were not seeded.
- Supplier data was not re-queried.
- Probe outputs are in `.supervisor/r23_manufacturing/`.
