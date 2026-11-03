# R10 round 32 review: requirements lens

Target commit `3366287`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256 identical before and after). Strict real-error rule (`.supervisor/r32_review_brief.md`).

**Totals:** 0 Critical, 0 Major, 0 Minor real errors.

## Findings

None. Each requirement in docs/REQUIREMENTS.md (F1-F12, P1-P3, M1-M3, operating assumptions) was mapped to the board, the fab evidence and ../../docs/VEHICLE.md; no requirement fails, none contradicts another, and no number is wrong against VEHICLE.md.

## Fix verification

- **R30-TRI-02 (REQUIREMENTS Temperature row and its siblings):** REQUIREMENTS:94 pass criterion is 'every 85 C part <= 85 C' alone; LS120's measured rise is recorded, not a gate, limit 70 C minus that rise, 48 C marked the pre-test estimate; same in ORDERING:608, M3_R10:503-504, owner rows 33 / 36, parts_qualification:40; remaining 'LS120 <= 70 C' hits are history (STATUS round 29 / 30 entries, R29-TRI-04 / R30-TRI-02 record rows). Verdict: confirmed.
- **R30-TRI-01 (R10_VALIDATION section 1, outside this lens; read only):** R10_VALIDATION:2637 gives about 2.19-2.21 V / 0.107-0.109 mA with the D120 / R131 pull-up (Calculation / Inference); :2670 gives EN 5.6 kOhm with the e-match or dummy. Verdict: confirmed.

## Observations (not counted)

1. F4: J122 pins 1-4 SERVO1..4_OUT, pin 5 GND; R150-R153 1 k series, R154-R157 10 k pull-downs, D121 SRV05-4 on SERVO*_MCU (U1.22-25): matches F4.
2. F4 hinge range: own linear-theory recompute over the 18 L1000W cases of the round 23 derived envelope (8 x 26.5 mm tab from VEHICLE.md, 15 deg, hinge arm c/2, 5.4 kg.cm HV6120 at 8.4 V): 63.9-84.3 %; nominal M1.82 / 212 kPa 77.4 %, high 84.5 % (simple form): F4's 'about 64-84 % (77-84 % nominal to high)' reproduces.
3. Flight envelope table: every range in REQUIREMENTS line 32 (specific force, burnout deceleration, Mmax, q_max, apogee, t_apogee, flight duration 449-877 / 592-1183 s) reproduces from flight1d_results.json; landing 6.2-8.0 m/s flat 36 in; ISA apogee ambient -7.8..-27.3 / -16.1..-42.2 C matches F1.
4. F2 37 g margin basis = L1000W 36.6 g max; F3 8.8 km MSL = 7.6 km AGL + 1.2 km site, ISA 316.7 hPa >= 300 hPa; the 10 km capability vs 300 hPa bench floor was already ruled no contradiction (round 26 triage).
5. F1 budget: 0.015 x 10 x 30 = 4.5 deg; ARW 5.5 mdps/rtHz x sqrt(30 s) = 0.030 deg; (5 - 0.9 - 0.03)/0.45 = 9.04 C: reproduces.
6. F6 / F4 EN model (own worst-corner solve: R80 / R165 +1 %, R81 -1 %, 0.1 uA EN + 50 nA D402 sinks, C87 0.72 x 220 nF, 1.116 V): EN0 1.4014 V at 6.0 V; single drop-out 10.35 / 20.11 / 26.02 / 8.07 (5.713 V) / 6.30 ms; 8 ms per 50 ms: 1.0953 V at 6.0 V, 1.0878 V at 5.96 V; 7 ms per 100 ms: 1.1295 V at 5.713 V, 1.1330 V at 5.73 V; trip block 7.50 (5.713 V) / 7.63 / 9.59 / 5.87 ms, 7.03 ms at 5.65 V; trip fractions 19.6 / 14.8 / 4.5 % (5.713 V) and 24.3 / 8.3 % (6.0 V); 3 x 4 ms burst 1.028 V (5.73 V). All reproduce.
7. The '5.71 V' figures in F4 / F6 (7.50 ms, 1.1295 V, 4.5 %) are computed at the budget's 5.713 V; at exactly 5.710 V they are 7.48 ms, 1.1289 V, 4.1 %. 5.71 is the stated rounding of 5.713 V (F6 says so), so this is the rounding class, not counted.
8. F6 turn-on 88 / 56 / 45 ms at 6.0 / 7.4 / 8.4 V reproduce with tau = (940 k || 300 k) x 220 nF = 50.0 ms to 1.20 V.
9. F7 widths: BAT_IN J1.1 -> Q120 EP 1.0 mm B.Cu (7.4,74.1)-(13.0,74.1)-(13.5,73.6); seven 0.4 mm ACT_FET_S source-pin bridges (x 12.525 / 13.175 / 13.825 / 14.475); 0.3 mm ACT_FET_S segments go only to R119 / R120 / C120 (bias); RAW_ACT 0.5 mm Q121.8 -> R134.2; the 0.4 mm RAW_ACT segment (13.5,68.6)-(18.0,68.6) goes only to TP120 (test branch); PYRO1_IGN 0.5 mm; PYRO1_OUT fire copper 0.5 mm F.Cu, 0.2 mm B.Cu sense only. Matches F7.
10. F8: sense banks R132 + R175 / R173 + R129 5.1 k tops, R133 || R180 / R130 || R178 2 k bottoms, C129 / C127 10 nF on PC5 (U1.33) / PC0 (U1.15); D120 BAT54A + R131 10 k cold pull-up; healthy CONT 99.36 mV, open CONT 146.23 mV reproduce (3V3 3.3 V, 0.20 V drop).
11. F8 / F9: BAT_SW_RETURN = {J400.2, R165.1, D402.1} exactly; Q122 R122 1 k / R123 2 k / C123 10 nF; D402 at B(4.45,65.9) with the tap J400.2 -> D402.1 4.114 mm (2.59 + 0.509 + 1.015) and its GND via (5.15,65.575) 0.700 mm from D402.2: matches F9.
12. F8 connectors: J121 black DB125 2P (C52993880), J1 / J400 green 2P (C466970), J122 green 5P, J9 / J410 / J420 / J440 green 4P (C2757925) at the stated positions; port pin order 4V8 / GND / TXO / RXI and J9 CAM_5V / GND / RX / TX match F10.
13. F5: J430 (C164170) CS / MOSI / MISO / DAT1 / DAT2 pulled up by R460-R464 10 k; C460 100 nF, C461 22 uF on 3V3 at J430: matches F5.
14. F11: LED1 / LED2 with R32 / R33 220 R; LS120 driven by Q123 from BUZZ_DRV (U1.8, PC14) via R162 1 k / R163 10 k, D123; U1.7 (PC13) and U1.18 (PC3_C) unconnected: matches F11.
15. F10 EXTI pins: IMU_INT1 U1.98 (PE1), BAT_FAULT_N U1.29 (PA5), USB_FAULT_N U1.87 (PD6), VBUS_SENSE U1.65 (PC8), CAM_FAULT_N U1.42 (PE12) as in the LQFP100 map; LR900-F 890 + 12 .. 25 = 902-915 MHz.
16. P1 / P2: outline 46.05 x 90.05 mm edge-line bounding box (0.05 mm line width) = 46 x 90; exposed lands to the (4,44.3) support: LED2.2 GND 3.808, LED1.1 GND 3.860, J2.1 3V3 3.881, J2.3 NRST 3.989 mm (polygon approximation; record 3.987 mm).
17. P3 sled pocket box x 31.5-41, y 20-60 matches C411 / C421 / C431 bodies (x 31.475-40.975, y 20.425-60.075).
18. Board position: -44.6 + 80 + 44..48 = joint + 79.4..83.4 mm (VEHICLE.md bulkplate top joint - 44.6, shroud +4..+47); board forward edge at about joint + 169-173 runs past the coupler end (joint + 120) into the Ø54.6 bore, so P1's Ø50.8 mm fit check is conservative there.
19. Pack row: radio 1 W + GPS 0.05 A at 4.792 V through the LDO at 5.456 V and an 85 % buck: 1.66 W, 0.225 A at 7.4 V (record about 1.7 W, 0.23 A). Storage: 8.4 V / 10 k R167 = 0.84 mA, 1 Ah in 7.1 weeks (R82 2 M and U9 off-state add a few uA).
20. M1 / M3: stock_check.json 2026-11-02T12:43:17Z (U4 9 / presale 2; U9 30 / -81, minimum 7) and cost_check.json 2026-11-02T12:44:13Z ($85.26, $61.01 vs $60.47 with minimum purchases, fixed $83.96, handling $14.93) match REQUIREMENTS M1 / M3; 'about $102-$105' spans 102.05-105.58, an approximate range.
21. No requirement in REQUIREMENTS F1-F12, P1-P3, M1-M3 or the operating assumptions was found to contradict another or the board.

## Checks actually executed

- sha256 of m3.kicad_pcb before and after (a0ec075e...); git HEAD 3366287; tracked tree unchanged
- pcbnew read-only dump of every footprint, pad net, via (dump.py -> board.json) and net queries (q.py, nets.py)
- pcbnew track / via / zone listing of BAT_IN, ACT_FET_S, RAW_ACT, PYRO1_IGN, PYRO1_OUT, BAT_SW_RETURN (geo.py, geo2.py)
- pcbnew bounding boxes of C411 / C421 / C431 / C84 (geo3.py); land-to-support distances by effective pad polygon (geo4.py)
- NumPy worst-corner EN chatter model (en.py, en2.py): steady EN, single drop-out, periodic trains, trip block, trip fractions, burst
- Derived envelope ranges and linear-theory hinge ratio from .supervisor/r23_requirements/flight1d_results.json
- Read stock_check.json and cost_check.json; grep of committed docs for the R30-TRI-02 / R30-TRI-01 fix text

## Sources

- docs/REQUIREMENTS.md
- ../../docs/VEHICLE.md (lines 36-45)
- AGENTS.md (committed 3366287)
- m3_design/assembly_review/m3.kicad_pcb
- m3_design/assembly_review/fab/stock_check.json
- m3_design/assembly_review/fab/cost_check.json
- m3_design/r10_sch_check.py (chatter text)
- round30_triage.md, round30_fix_docs.md, round28_triage.md (R28-TRI-07)
- research_notes (HV6120 5.4 kg.cm at 8.4 V, Aloft Hobbies listing)
- TI SLVSFC9C p9 thresholds as quoted in the records (PDF not re-read)

## Coverage limits

- No datasheet PDF re-read this round; EN thresholds and leakages taken from the records' citations
- HV6120 stall torque taken from the project's research notes (retailer listing), not a maker datasheet
- No kicad-cli DRC or tools/check.sh run (read-only brief); other lenses cover routing, DRC and fab
- Derived envelope and hinge figures are the records' Inference model, reproduced, not independently validated against OpenRocket
