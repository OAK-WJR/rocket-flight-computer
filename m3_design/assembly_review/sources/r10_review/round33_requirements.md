# R10 round 33: requirements lens

Target commit `feed21f`, board `a0ec075e…733c` (SHA-256 the same before and after). Read-only; probes in `.supervisor/r33_requirements/`.

**Totals: 0 Critical / 0 Major / 0 Minor.** No real errors found.

## Mapping performed
- F4: J122 pins 1–4 SERVO1–4 / 5 GND; 1 kΩ series (R150–R153), 10 kΩ pull-downs (R154–R157), D121 SRV05-4 on the MCU side. Hinge range: 77 % nominal / 84 % high at 15° for L1000W, from the round 23 script, as F4 states. EN-train figures re-derived: 1.088 V at 5.96 V, 1.095 V at 6.0 V.
- F5: J430 at B(24,24.3), SPI3 PC10/11/12 plus PD0, 10 kΩ pulls R460–R464, C460 100 nF / C461 22 µF.
- F6: R80 / R165 470 k, R81 300 k, C87 220 nF. Re-derived figures: single drop-out worst 6.30 / 8.07 / 10.35 / 20.11 / 26.02 ms, nominal turn-on 88 / 56 / 45 ms, hold-up scalings and the PA6 ×11 divider; all match.
- F7 / F8: Q120's drain on BAT_IN through a 1.0 mm track. ACT_FET_S is exactly seven 0.4 mm source bridges. RAW_ACT, IGN and OUT are 0.5 mm. The dividers are two 5.1 k tops, two 2 k bottoms and 10 nF on PC0 / PC5. Q122's gate is at 0.218 V; healthy CONT 99.37 mV and open CONT 146.23 mV. J121.1 is OUT and J121.2 is IGN, and all 23 pin legends are present.
- F9: D402 sits at B(4.45,65.9) on a 4.114 mm tap, with its GND via 0.700 mm away. BAT_IN bleed: about 1.5 s to 1 V, within 2 s. The ESD figures (7.5 / 9.6 V) and the 3V3 delay (21–26 ms) both reproduce.
- F10 / F11: every assigned U1 pin matches `pin_table.tsv`, including the EXTI pins, PC14 buzzer, PB1, PC3_C / PC13 NC, VBAT = 3V3 and VREF+ / VDDA = 3V3A. Port pin order matches on all three ports and on J9. PORT_4V8 = 4.792 V and PORT_5V3 = 5.456 V from the feedback resistors.
- P1 / P2: outline 46 × 90 mm with the five Edge.Cuts supports. The lands nearest the (4,44.3) support measure 3.808–3.989 mm (polygon figures, which bound the round lands).
- VEHICLE.md: motor and booster sizes, bulkplate −44.6, battery bay top +35.4, aft edge +79.4…+83.4, shroud +4…+47 and the 32 mm margin all match.
- Storage, landing, apogee-temperature, barometer-altitude and M3 arithmetic: all reproduce.

## Fix verification (round 32)
- R32-TRI-01 confirmed (0.56 mm remains only in the historical row title, which now carries the correction).
- R32-TRI-02 confirmed.
- R32-TRI-03 confirmed.

## Observations (7, not counted)
1. The Pack row's 0.23 A recomputes as 0.224 A, an "about" Inference figure.
2. The log-size wording differs: "about 3 MB" in one place, 2–3.5 MB in F5.
3. F1's 30 s versus 35 s window is a disclosed recompute item.
4. Flight 1's low-Mach hinge case is 77 %; F4 speaks of flight 2 only.
5. The cost-table basis was already ruled on in round 29.
6. The Ø50.8 mm fit requirement is conservative beyond the end of the coupler.
7. VEHICLE.md's R10 row is stale, as the brief already notes.

## Coverage limits
- Datasheet limits are taken as the records quote them; none was re-read.
- No DRC or route_check run.
- The schematic was not opened; the mapping uses board nets.
