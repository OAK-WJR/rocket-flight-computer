# R10 round 32 — safety lens

Target `3366287`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256 before and after identical). Strict real-errors rule.

**Totals:** 0 Critical, 0 Major, 0 Minor real errors.

## Findings

None.

## Fix verification

- **R30-TRI-01 (§1 ARM1_SENSE-to-CAM_IO_3V3 bridge figures)** — confirmed: R10_VALIDATION §1 now gives about 2.19-2.21 V on RAW_ACT and about 0.107-0.109 mA at a BAT54 drop of 0.20-0.24 V, labelled Calculation / Inference; pair re-measured 0.1501 mm (B.Cu (29.75,49.4)-(29.75,45.85) to U13.5); figures match the triage solve (2.2052 / 2.1913 V, 0.1073 / 0.1087 mA).
- **R30-TRI-01 sibling (EN load 5.6 kOhm with the e-match or the step-3 dummy)** — confirmed: R10_VALIDATION §1 EN-threshold paragraph reads '10 kOhm, 11.2 kOhm (5.6 kOhm with the e-match or the step-3 dummy fitted, R30-TRI-01) or 2 kOhm'; 11.2k || (11.2k + ~4 Ohm) = 5.6 kOhm.
- **R30-TRI-02 (chamber-test pass criterion; LS120 not a gate)** — confirmed: REQUIREMENTS Temperature row, M3_R10 hot-end, ORDERING 8.3, owner rows 33 / 36, AGENTS buzzer row and STATUS all pass on 'every 85 °C part <= 85 °C' and record LS120's rise as non-gating; 48 °C kept as the labelled pre-test Inference.
- **D-R29-01 / R29-TRI-02 (rule 3 gate time constant)** — confirmed: 'about 47-58 us over C126's ±10 % (53 us nominal; Calculation, driver resistances Inference)' in M3_R10 rule 3, FMEA I-2 / H-2, binding note obligation 38 and §1; 238.6 Ohm x 198-242 nF = 47.2-57.7 us.
- **R29-TRI-01 (§2.5 labels on safety figures)** — confirmed: AGENTS shorted-igniter row (34.853 ms, Calculation on allocations / Inference), pyro row (1.279 A, conditional; Calculation / Inference), M3_R10 residuals (0.9-1.8 A, Calculation / Inference), FMEA I-5 (991 microstrain, Calculation / Inference), I-2 / H-2 (3.23 V, Calculation / Inference).

## Observations (not counted)

1. PYRO1_OUT to GND residuals reproduce: B.Cu track (15.5,56.6)-(16.87,57.97) to GND via (15.85,57.695) 0.1768 mm; F.Cu Q124.5 to GND via (12.775,59.025) 0.180 mm; R173.1 to Q124 source via (15.85,58.345) 0.5000 mm (owner rows 1 / 2, FMEA I-5, M3_R10 residuals).
2. Fire-chain clearances to 3V3 / 3V3A reproduce on every layer: PYRO1_OUT min 1.0400 mm (B.Cu run to R164.2, 3V3A), 1.0501 mm F.Cu (to 3V3 via (9.2,52.55)), 1.0512 mm (R173.1-D120.3), In2 J121.1 wall to 3V3 fill 1.0613 mm; PYRO1_GATE min 1.0585 mm (R128.1 to via (19.55,55.825)), PYRO1_GATE_N 1.0651 / 1.0809 mm (R127.1 / R126.1), 3V3A to PYRO1_GATE via 1.1450 mm; PYRO1_GATE via to In2 3V3 fill 2.7506 mm.
3. PYRO1_OUT to BUZZ_DRV R173.1-R162.1 0.7935 mm, R173.2-R162.1 1.1329 mm, R173.2-D120.3 0.4154 mm, CONT_MID diagonal 0.2006 mm from Q123.1 and 0.3862 mm from R134.2: all as recorded.
4. PYRO1_OUT to BUZZ_G (R173.1 to the B.Cu BUZZ_G track (17.92,58.70)-(17.75,58.87)) is 0.510 mm, inside the 0.6 mm scan band but not a §1 table row; recorded in D-R18-05; a bridge feeds PC14 / R163 a few mA through R162 1 kOhm (no fire). The §1 table is not claimed complete (round 27 ruling).
5. Q124 gate-to-own-drain (Q124.4-Q124.5) 0.520 mm: a bridge with the bus enabled holds Q124 in linear conduction and can fire an enabled match; §1 records the geometry only. Same class as the disclosed failed-short Q124 / OUT-to-GND routes; the lists say 'include' (round 27 ruling).
6. Q121.4 (ACT_GATE) to Q121.9 (RAW_ACT) 0.520 mm inside the FET land: a gate-to-drain bridge biases the pair on (RAW_ACT about BAT_IN minus |Vth|) even with J400 open; owner row 2's load-switch-gate class; per-flight step 2 (J121.2 < 0.1 V) screens it before the e-match goes in.
7. BAT_ENABLE-BAT_OVLO (U9.1-U9.2, 0.200 mm): OVLO node is BAT_IN x 280k / 2.28M = 1.03 V at 8.4 V (R82 2 MOhm, R83 280 kOhm), below VUVLO(R) min 1.183 V, so a bridge holds U9 off: fail-safe, as round 30 obs 1-2 ruled.
8. BAT_SW_SOURCE In2 via (10.8,69.2) 0.2508 mm from In2 RAW_PROTECTED: a short only pulls the J400.1 node to the U9 output (0 V with J400 open); fail-safe, shows at power-up.
9. RAW_ACT-USB_OVLO measures 0.1772 mm on a0ec075e (chamfer (22.8,63.535)-(22.46,63.875) to (22.0,64.75)-(22.5,64.25)) against the table's 0.175 mm, which the table heads 'on a3144b15 unless noted'; consequence unchanged.
10. Owner row 24's 0.5205 / 0.5008 mm (ACT_EN_MCU / RAW_ACT to BAT_ENABLE) measure 0.5199 / 0.5001 mm here: sub-micron shape-approximation difference, not an error.
11. ACT_EN_MCU-BUZZ_OUT 0.520 mm (F.Cu, LS120.2, 3V3 through the coil) can raise the bus with PC1 low or undriven; disclosed in R18-m03 and owner row 2's PC1 enable-chain class; cold screen refuses a pre-existing bridge.
12. The 3V3 bridge via (26.4,79.26) barrel 0.2506 mm from In2 RAW_PROTECTED is the I-5 member already ruled (round 27 / 30 triage: lists not exhaustive).
13. Rule 4 '0.93-1.01x' against 1.128 / 1.063 A: the round 23 case-table envelope, ruled an observation in round 27 (R27-MCU obs 5).
14. EN latch thresholds reproduce: BAT_FAULT_N 3.3 x 300 / 310 = 3.19 V, leak <= 577 kOhm; RAW_ACT leak 1.69-1.96 MOhm; ACT_EN (2.2 V via 667 Ohm) leak <= 0.29 MOhm; J400.2 chafe 2.88 / 1.87 / 1.28 V; EN divider 2.032 / 2.063 V; dry-contact current 6.8 uA.
15. Cold-screen and bridge readings reproduce: healthy 99.36 / open 146.2 mV at Vf 0.20 V; OUT-3V3 bridge 0.2946 V; CONT_MID-RAW_ACT open-match 102.0 / 55.5 mV at Vf 0.30 V; powered 1.213 V (7.4 V) / 1.377 V (8.4 V) vs 0.75 V intact; R173.2-3V3 0.54 V.
16. Rule 3 figures reproduce: 0.91 kOhm = 1 k || 10.22 k (910.9 Ohm); 238.6 Ohm x 220 nF = 52.5 us, +-10 % 47.2-57.7 us; hard-bridge gate 3.229 V; U3.3 is QSPI_IO2 and R127.1 is PYRO1_GATE_N on the board; U1.1-U1.3 pad gap 0.700 mm; QSPI_IO2 track 0.5500 mm from U1.3.
17. Rule 4 / ORDERING Q120 test is executable on the board: Q120.4, C120.2 and R120.2 share one B.Cu island joined to R121 only through vias (16.2,73.3) and (15.4,72.85), so with both open the probe point reads Q120's own gate at its source; AONR21357 RDS(on) <= 12.3 mOhm at -4.5 V (Rev 2.1 p1) keeps a healthy two-FET drop well under the 0.2 V fail line at dummy-load current.
18. AGENTS §2.4 gate networks present on the board: Q124 (R126 220 Ohm series, R128 10 k + R127 1 k pull-downs, C126 220 nF), Q122 (R122 1 k, R123 2 k, C123 10 nF), Q120 / Q121 (R121 10 k, R119 / R120 100 k to ACT_FET_S, C120 1 uF); R127 holds PE4's node at <= 0.12 V against a 30 kOhm pull-up at 3.6 V.
19. AGENTS §2.2: RAW_ACT is fed only from Q121's drain behind Q120 (BAT_IN); no RAW_ACT barrel; S-8 inventory 12 barrels on 6 nets reproduces (PYRO1_OUT via, J121.1, J121.2, PYRO1_GATE via, four ACT_GATE vias, three BAT_ENABLE vias, J400.2).
20. In2 rings: J440.1 and J9.1 0.2507 mm from the In2 3V3 fill; J121.1 has no In2 ring (1.0613 mm wall); J121.2 ring 0.2507 mm to GND (exempt), as recorded.
21. §2.5 label sweep of current safety figures (AGENTS table, M3_R10 Firmware / CH1 pyro / residuals, ORDERING 8.3, FMEA I-2 / H-2 / I-5 (R10), R10_VALIDATION §1 and owner rows 1 / 2 / 7 / 24 / 36, the handoff): every figure resting on an inferred input carries an Inference label (the 34.853 ms guard, 1.279 A, the gate-fight figures, the BAT54 drop, the bridge figures, the 991 microstrain); pure arithmetic on stated values is labelled Calculation.

## Checks actually executed

- SHA-256 of m3.kicad_pcb before and after (shasum): a0ec075e…, unchanged; target commit 3366287 = HEAD; tracked docs equal to the commit.
- pcbnew read-only pad / net dump of every footprint (.supervisor/r32_safety/pads.py -> allpads.txt).
- pcbnew shape-distance adjacency scan, all four copper layers incl. zone fills: PYRO1_OUT / PYRO1_GATE / PYRO1_GATE_N to 1.2 mm; BAT_ENABLE, BAT_SW_*, ACT_*, RAW_ACT, ACT_FET_S to 0.6 mm; sense nets (PYRO1_CONT*, PYRO1_COLD, ARM1_*, PYRO1_IGN) to 0.6 mm; 3V3 / 3V3A items to 0.32 mm (adj.py).
- Targeted pair distances for every §1 / owner-row 1 / 2 / 24 figure (pair.py), pad-ring-to-fill (padzone.py) and via-to-fill (viazone.py) measurements.
- Net routing dumps of ACT_GATE, PYRO1_GATE, PYRO1_GATE_N, BAT_ENABLE, BAT_SW_RETURN and via inventory of protected nets (nettracks.py).
- Hand calculations: cold-screen bands, bridge readings, EN latch leak thresholds, EN divider, OVLO node, gate time constants, meter-check 0.91 kOhm, Q124 / Q122 off-state against pull-ups, body-diode ratio consistency.
- Text reads: AGENTS §1 table and §2, M3_R10 Firmware / CH1 pyro / retained residuals, ORDERING 8.3 (probe worksheet, coating, Q120 / QSPI first-article checks, per-flight steps 1-7), FMEA I-5 / I-2 / H-2 (R10), R10_VALIDATION owner rows 1 / 2 / 7 / 24 / 36 and §1, binding note obligations 6 / 30 / 38 / 39, R10_VEHICLE_HANDOFF safety paragraph.

## Coverage limits

- No live datasheet re-read beyond AONR21357; DS12110 PC14 / FT figures and TPS25947 thresholds taken as quoted in the records.
- Adjacency scan reports the per-layer minimum for each net pair; non-minimal pairs were checked only where a document states a figure.
- No firmware exists; firmware rules were checked for consistency with the circuit, not executed.
- No gate seeding was run (no gate claim in this lens's findings).
