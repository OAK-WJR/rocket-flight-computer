# R10 round 34 — requirements lens

Target `c2a11fd`, board SHA-256 before and after: `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`.

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

Each requirement in `docs/REQUIREMENTS.md` was mapped to the board, the fab package and `../../docs/VEHICLE.md`.
No requirement fails on the board, no two requirements contradict, and no number is wrong against VEHICLE.md.

## Observations (not counted)
1. Outline and the five Ø3.2 support holes match P1 / P2.
2. Terminal positions and pin nets (J1, J400, J121 black, J122, J9, J410 / J420 / J440) match F4 / F8 / F9 / F10.
3. F4 servo chain (R150–R153 1 k, R154–R157 10 k, D121) and TIM5 on PA0–PA3; hinge moment 0.447 N·m at M2.13 / 286 kPa / 15° = 84 % of 0.53 N·m.
4. Pin map (SPI3, USARTs, EXTI lines), VBAT on 3V3, VREF+ / VDDA on 3V3A, PC3_C NC.
5. F6 EN model reproduced: 88 / 56 / 45 ms turn-on; 10.35 / 8.04 / 6.30 ms single drop-out; 1.088 V (5.96 V) and 1.095 V (6.0 V) for 8 ms per 50 ms; 7 ms line to 5.65 V.
6. F7 fire-path widths (BAT_IN 1.0 mm, seven 0.4 mm ACT_FET_S bridges, 0.5 mm elsewhere; narrower copper only on sense / test branches); fire 1.279 / 1.476 / 1.541 A.
7. F8: 0.218 V Q122 gate; 99.36 / 146.2 mV cold readings; gate networks present.
8. F9: D402 tap 4.114 mm, GND via 0.700 mm; ESD 7.5 / 9.6 V.
9. Port rails 5.456 / 4.792 V; PA6 ×11; R167 0.84 mA, 7.1 weeks.
10. P2 exposed lands 3.808–3.989 mm from (4, 44.3) (polygon approximation).
11. VEHICLE derivations (joint + 79–83 mm, 316 hPa at 8.8 km, apogee ambients, 3906 dps, 98–163 g) reproduce.
12. M1 / M3 cost and stock figures match `cost_check.json` / `stock_check.json` (12:44:13Z / 12:43:17Z), input hashes match the BOM / CPL.
13. The session-context AGENTS.md copy is stale; the committed one is current (round 29 ruling).

## Fix verification
- R33-TRI-01 (docs_binding; checked): U9 pads 5 / 6 expose 0.15–0.25 × 0.30 mm, pad 9 0.15–0.25 × 0.25 mm; ORDERING 8.3 lines 552 / 555 agree. **Confirmed.**

## Checks executed
pcbnew read-only probes (`.supervisor/r34_requirements/probe1–9.py`), pin_table, parts_budget, cost / stock JSON and hashes, an independent EN RC model, and hand arithmetic. Coverage limits: datasheets not re-downloaded, worksheet and plate model not re-derived, no full `tools/check.sh`.
