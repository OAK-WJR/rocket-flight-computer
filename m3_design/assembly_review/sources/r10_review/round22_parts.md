# R22 parts / BOM / CPL / lands / ratings / stock (Claude)

- **Target commit:** `ec8cb98`.
- **PCB SHA-256, before and after:** `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` (unchanged; no tracked file was edited).
- **Evidence:** [round22_parts.json](round22_parts.json).
- **Probes:** `.supervisor/r22_parts/` (ignored).

**Totals: 0 Critical, 0 Major, 3 Minor (all carried; R22-PARTS-01 now also covers U9).**

## Findings

| ID | Sev. | Status | Finding and key number | Fix |
|---|---|---|---|---|
| R22-PARTS-01 | Minor | carried R21-BOM-02, now also U9 | The records' fallback for short U4 and U9 is "consign franchised parts". The franchised channels I checked cannot supply either part today. **U9 TPS259470LRPWR:** the TI store is out of stock. DigiKey has 0, with 3000 expected on 14 Dec 2026 (6-week lead time). Only brokers list stock (Win Source, Vyrian). **U4 ISM6HG256XTR:** the ST eStore is out of stock. DigiKey has 0, with 5000 expected on 22 Mar 2027 (20-week lead time). Avnet and Newark have 0. The second fallback, LSM6DSV320XTR, has 0 at DigiKey (24-week lead time). Live JLC at 01:07Z: U9 40 in stock / −69 orderable / minimum 7; U4 9 / 2. M3_R10.md line 85 still says U4 is "in JLC stock". | Text only. Record the dated franchised status. Allow franchised or JLC sources only, never brokers. Add an owner choice: fit U4 / U9 later (DNP), or order only as many boards as JLC can fill. Fix line 85. |
| R22-PARTS-02 | Minor | carried R21-BOM-03 | DB125 holes are 1.30 mm with 1.90 mm lands, against DORABO's recommended 1.20 mm. The library is unchanged. | Check the through-hole fill on the first article. |
| R22-PARTS-03 | Minor | carried R21-BOM-04 | VCAP C19 / C20 (C23630) have no maker-bounded worst case. | As R18-m10. |

## Fix verification

| D-ID | Verdict | Measured |
|---|---|---|
| D-R21-05 R81 / C87 | confirmed | Only R81 and C87 moved among the 215 footprints. Their CPL rows are Top 0. The EasyEDA rebuild is off by 0.072 mm (R0603 pitch) and 0.000 mm (C0603). Paste is at the new pads and none is left at the old spots; totals are 253 / 375. Live parts: C23024 is 300 kΩ, 0.1 W; C21120 is 220 nF 25 V X7R. EN stays at or below 2.03 V. |
| D-R21-01 0.55 mm PTH rule | confirmed | Every PTH pad wall is at least 0.5505 mm from foreign copper on the inner layers. The measurement uses the true slot shape (native), and the shipped Gerber agrees: J1.2 In2, J400.2 In1 and J3.1–J3.4 In2 are all 0.5505. DRC: 0 / 0 / 0. |
| D-R21-05 vias | confirmed | Vias went from 302 to 300, removing exactly the two GND vias, with none added. The only vias in pads are the two U401.11 VIPPO vias. |
| D-R20-05 / D-R19-11 / D-R19-07 | confirmed | No inner rings remain at J400.2 / J1.2. U4 at Bottom 180 is off by 0.040 mm. C84 has no paste and is on the owner BOM only. |

## Closed independently

- **U9 consigned land and rotation.** Our land matches TI's RPW0010A drawing (SLVSFC9C p72): columns ±0.9, pads 2/3/8/9 0.25 at ±0.225, legs at ±0.725, pads 5/6 0.3 × 2.4 at ±0.25. EasyEDA at Bottom 180 matches pads 2/3/8/9 within 0.005 mm, so pin 1 is correct. A consigned part has the same MPN, so it uses the same land and the same CPL rotation. Whether JLC maps the consigned part to the same footprint is an Inference: check it in the placement preview.
- **Identity.** 215 / 206 / 205 parts and 666 nodes match with 0 issues. All 82 codes match their MPNs live (36 Basic / 46 Extended, C84 included). The fab, stock and cost hashes all match the manifest.
- **Small discrepancy in the D-R21-01 table.** It gives J3.1 / J3.4 on In1 as 1.375 / 1.345 mm. Measured with the true slot shape they are 1.225 / 1.194 mm. Both are far above the limit.
- **Cost.** $85.37 against the $84.41 cap is an open owner decision; noted only.

## Fix now

R22-PARTS-01 (text only): record the dated franchised status, ban broker parts, and add the DNP or partial-order choice for the owner; correct M3_R10.md line 85.

## Limits

- I could not verify Mouser (the page timed out) or RS (it returned 403).
- How JLC uses `canPresaleNumber`, and how it maps consigned parts to footprints, are Inferences.
- No physical qualification.
