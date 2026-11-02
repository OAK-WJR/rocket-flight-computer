# R10 round 31 triage

Target: commit `3366287`, board `a0ec075e…` (SHA-256 verified before and after: unchanged). Ten lenses reported 0 findings and 151 observations.

## Totals

**0 real errors (0 Critical / 0 Major / 0 Minor). 0 not reproducible. 151 lens observations re-examined plus 1 triage observation; none meets the review brief's definition. Round 31 is clean** (first of the closing pair; no board change, so the count stands).

## Root-flagged observations

- **R31-SAFETY obs 3 (J440.1 / J440.2 onto J121.1 filed under the OUT-to-GND class; R10_VALIDATION:2668, ORDERING:694, handoff:62)**: Root flag. R10_VALIDATION:2639 defines the class as PYRO1_OUT onto a lower-potential net, which PORT_4V8 (4.79 V) is; J440.2 is GND outright. If PORT_4V8 held, the loop carries (7.4-8.4 - 4.79) V / 2.8-4.5 ohm = 0.58-1.29 A (triage Calculation) against the 0.30 A no-fire, and TPS7A91 not sinking only moves the outcome to an over-voltage on the port modules; 'fires by itself' cannot be shown false, it errs to the hazard side and the mitigation (separate leads) is the same. Not a real error.
- **R31-SAFETY obs 5 (S-8 tables: J400.2 In1 GND '0.250 since D-R20-05')**: Root flag. Triage pcbnew on a0ec075e: J400.2 wall to In1 GND 0.5505 mm, In2 GND / RAW_PROTECTED 1.0501 mm. The M3_R10:657 table heading labels the J400.2 row 'updated for D-R20-05, round20_fix_cad.md', and round20_fix_cad.md:121 gives exactly 'In1 GND wall 0.550 -> 0.250 (exempt)'; R10_VALIDATION:2681 labels the table to 50a39de5 and its next paragraph records D-R21-01's 0.55 mm PTH rule; M3_R10:121 records J400.2 In1 0.251 -> 0.550 mm (D-R21-01). GND is exempt at J400.2, the current sentences (1.050 mm) are right. Same class as R25-SAFETY obs 6 / R29 safety obs (labelled history); nothing new.
- **R31-MECHANICS obs 6 (ORDERING 8.4 / handoff / R10_VALIDATION row 32 sled-contact lists vs J9.3 / J420.1 tails at 161.8 / 167.5 g)**: Root flag. ORDERING:702 lists C431 125 g, C421 133 g, C411 175 g, L1 214 g; it makes no completeness or 'first contact' claim beyond C431, which stays first (125 g < 161.8 g). M3_R10 and the handoff state only C431 at 125 g and the 100 g gaps. Both vehicle remedies cover the tails (pocket x 31.5-41 contains them; 4.5 mm standoffs first contact 172.6 g > 163 g). Ruled in R25 (mechanics obs 2); nothing new.
- **R31-POWER obs 18 (USB_LIMITED 63.605 mm, M3_R10:759; U400 / L400 1.2-2.2 W, M3_R10:354, ORDERING:607, R10_VALIDATION row 26)**: Root flag. M3_R10:754 heads the USB paragraph 'Calculation, Round 18'; 63.115 mm now changes the 0.0912 ohm term by <1 % and 0.4596 A still reproduces (R27 / R30 triage). U400 + L400 1.2-2.2 W: triage recomputed 5.456-5.546 V x 1.567 A = 8.55-8.69 W out at 88-80 % = 1.17-2.17 W, a correct rounding from the stated budget efficiency (ORDERING:607 names that input; R10_VALIDATION / M3_R10 label it Inference); the separate 'about 0.46 W' U400 figure (x 89 C/W = 41 C) is a labelled datasheet estimate. R28 / R29 ruling; nothing new.
- **R31-PARTS obs 12 (M3_R10:1040 L1 (33.0,71.6), C88.1 3.844 mm, J400 shell figures)**: Root flag. They sit under '## Historical mechanical record' (M3_R10:1023) and the paragraph is labelled 'native audit-board inventory on 877d0199'; the current section (M3_R10:973) and ORDERING:702 give L1 B(25,74.6), 3.015825 mm. Labelled history.

## Other observations (grouped)

- **R31-DOCS_BINDING obs 1-7**: R101 / R173 old positions are dated history (R173 B(16.87,59.05) on the board, triage pcbnew: pads 58.62 / 59.48); U4 coating outline is the silkscreen extent, conservative; R150-R157 present, R62 / R63 absent; legend hyphen typography; untracked probe-file mentions (ruled class); polygon approximation.
- **R31-GATE obs 1-12**: Seed and reproduction results showing the gates catch the realistic defects (budget staleness, generator text, right_angle, partner vias, D-R26-02 / -04 spacing, PortTerminal names) and the binding note / budget hashes reproduce; obs 1 is the ruled 'no rule binds a budget figure to a check' class (R26 / R28 / R29). No gate miss shown.
- **R31-MANUFACTURING obs 1-10**: DRC 0, fab export identity, manifest / CPL / paste checks reproduce; obs 4 (1.955 vs 1.96 mm) is rounding; obs 5, 6, 10 are measurement-basis differences within stated ranges; obs 9 ruled in rounds 18 / 19.
- **R31-MCU obs 1-18**: Pin map, AF, trace pins, citations, IWDG, gate thresholds, camera UART, LED polarity and binding-note regeneration all reproduce; obs 5 (PA4 / PA5 0 mA injection) has no design case that injects (pulled only to 3V3 by open-drain sources); obs 8 / 9 are round 26 / 27 triage observations.
- **R31-MECHANICS obs 1-5, 7-16**: fit_check, exposed lands, tenting, plate model, gaps, hardware bounds, wire room, compass, stack arithmetic and legends reproduce; obs 15 (1.73 vs 1.67 / 0.575 mm) is a measurement-basis difference already raised in round 29; obs 16 positions unchanged.
- **R31-PARTS obs 1-11**: BOM / CPL / board agreement, MPN decoding, ratings, datasheet facts and recomputed parts_qualification figures reproduce; obs 2 and 4 are recorded JLC origin / residual allowances; obs 10 (inductors inside DS41326's 2.2-10 uH guidance, table values not claimed in a current record).
- **R31-POWER obs 1-17, 19**: Budget currency, pack sag, USB attach, C120, GAP-1 / -3 / -5, ride-through, OQ-5, post-trip hold-up, EN / J400 figures, four-stall-plus-fire corner, regulator rails and taps, IPC widths, hot-plug binding and probe worksheet reproduce; obs 19 (about 1.7 W / 0.23 A) is a correct 'about' figure.
- **R31-REQUIREMENTS obs 1-21**: Outline, pin map, F4 / F6 / F7 / F8 / F9 / F10 / F11 parts and figures, temperature, F1, VEHICLE derivations, P2 / P3, stock / cost (committed stock_check 12:43:17Z and cost_check 12:44:13Z match AGENTS / STATUS / M3_R10 $85.26, $0.85 over), storage and fee range reproduce; obs 15 (HV6120 not re-sourced) and obs 20 are coverage notes / prior rulings.
- **R31-ROUTING obs 1-20**: route_check counts, independent angle / partner-via / reference / adjacency scans reproduce; obs 10's unnamed ACT_FET_S / RADIO_TX_MCU +3.1 mm: R10_VALIDATION:2941 'Below +3.5 mm: QSPI_IO2 +3.3 and USB_DM +3.1 mm' names examples and also names 3V3A +2.6 in the next sentence, with no claim of a complete sub-line list; obs 19 (ledger bound to an older board) is the round 24 ruling; obs 20 is a recorded M2 detour row.
- **R31-SAFETY obs 1, 2, 4, 6-16**: I-5 route lists (round 27 ruling), U9 bypass (R25 / R29), body-diode ratios bounded outward (round 27 ruling), PYRO1_OUT-BUZZ_G / Q124 self-pairs (table not claimed complete), BAT_FAULT_N 0.175 mm diagnostic class, sub-micron method difference (round 28 ruling), AGENTS 2.4 networks, rule 3 / 4 topology, pair table, arithmetic, S-8 and procedure coordinates reproduce.
- **Triage obs T-1 (R10_VALIDATION:2695 ring paragraph: J121.1-to-3V3 'roughly 0.3-0.8 A in the match')**: Own check. The paragraph is the R19-SAF-05 ring record for 50a39de5 / a3144b15 (resolved by D-R20-05) and states the rail-rising case with an Inference label (AP63203 does not sink); R10_VALIDATION:2639 / 2655 give 0.9-1.8 A only 'if the rail held 3.3 V' and otherwise the I-5 rise. The two describe different assumptions; neither claims 'does not fire' (R26-TRI-01's false sentence is gone). Not shown false.

## Independent spot checks (triage's own, pcbnew 10 on a copy and Python)

- PYRO1_OUT-3V3 1.050109 mm (F.Cu track (7.4,54.1) to via), PYRO1_OUT-3V3A 1.040038 mm (B.Cu track to R164.2): match D-R26-02 >= 1.040 mm
- PYRO1_GATE-3V3 1.0585 mm (R128.1), PYRO1_GATE_N-3V3 1.0651 mm (R127.1), PYRO1_GATE-3V3A 1.1450 mm (via (14.4,53.3)-C10.1), PYRO1_GATE_N-3V3A 1.6000 mm: match D-R26-04
- PYRO1_OUT-BUZZ_DRV 0.7936 mm (R173.1-R162.1, B.Cu): matches 0.794 mm
- PYRO1_OUT-GND 0.1768 mm (B.Cu): matches 0.177 mm
- BAT_ENABLE via (17.1,82.8)-BAT_FAULT_N 0.2000 mm; BAT_ENABLE-RAW_ACT 0.5000 mm; BAT_ENABLE-ACT_EN_MCU 0.5199 mm (records 0.200 / 0.5008 / 0.5205: sub-micron method difference, round 28 ruling)
- J400.2 hole wall: In1 GND 0.5505, In2 GND 1.0501, In2 RAW_PROTECTED 1.0501 mm (drill 1.3)
- Probe nets / positions: TP80 BAT_IN F(9.8,83.8), TP81 RAW_PROTECTED B(31,84.8), TP120 RAW_ACT B(18,68.6), TP122 PYRO1_GATE B(13.3,53.3), C15.1 3V3, C24.1 NRST, R119.1 / R120.2 ACT_GATE, R120.1 B(18.5,72.17), J410.1 / J420.1 / J440.1 PORT_4V8, J121.1 PYRO1_OUT / J121.2 PYRO1_IGN, R60 / R61 VLOGIC / 11: match ORDERING 8.3 and AGENTS
- Doc coordinate sweep (regex F/B(x,y) after a designator) over ORDERING, handoff, M3_R10, AGENTS, REQUIREMENTS, STATUS: 31 hits, 3 mismatches all in M3_R10 before/after history rows (R81 / C87 old F(20.5,65) / F(17,65); 'J440 at B(4.45,19.45)' is D440 under J440)
- EN model (R80+R165 949.4 k, R81 297 k, C87 0.72 x 220 nF, 0.1 uA EN + 50 nA D402, 1.116 V): single drop-out 10.345 / 8.066 / 8.204 / 6.300 ms at 6.0 / 5.713 / 5.73 / 5.5 V; late-block window limit 9.594 / 7.501 / 7.629 / 5.871 ms, 7.026 ms at 5.65 V; EN at 7 ms 1.1295 / 1.1330 V: all match AGENTS / M3_R10 / ORDERING 8.3 / REQUIREMENTS F6
- Turn-on 87.7 / 55.5 / 44.7 ms at 6.0 / 7.4 / 8.4 V (rounded 88 / 56 / 45): match F6
- Pack sag 5.880831 / 4.388491 V (r 0.15 ohm, 8.3175 A + 10.646 W): match D-R28-01
- Fire budget: 6.884219 / 4.467803 ohm = 1.5409 A; 5.713190 V four-stall, 1.2787 A: match AGENTS (1.279 A, 5.71 V)
- Harness EN 4.79 x 300 / 770 = 1.866 V, 3.3 x 300 / 770 = 1.286 V; nominal EN 8.4 x 300 / 1240 = 2.032 V: match
- Post-trip hold-up 0.5 x 300.8 uF x (4.84^2 - 3.8^2) / 13.064 W = 0.1034 ms; C120 off tau 50 k x 1.02 x 1.265 uF = 64.5 ms; IWDG 28.571-32.653 ms; U401 0.48965 W, 123.86 C: match
- PORT_4V8 4.792 V nominal, 4.71-4.87 V window in per-flight step 3 matches ldo 4.711504-4.873250 V; per-flight step 2 J121.2 < 0.1 V with 11.2 k x 5 uA = 56 mV
- Decision count: 126 ledger (r10_final_deviations.json agent_decisions) + 103 later (11+15+11+9+7+11+23+3+4+3+4+2) = 229, as R10_VALIDATION row 20 / M3_R10:199 state
- Committed stock_check.json 2026-11-02T12:43:17Z and cost_check.json 12:44:13Z ($85.26, $0.85 over) match AGENTS:24/32, STATUS:12, M3_R10:372-385

## Sibling sweep

No real error, so no sibling sweep was needed. The root-flagged classes were grepped: `0.250 since D-R20-05` (M3_R10:662, R10_VALIDATION:2691, both under labelled headings), `63.605` (M3_R10:759 only, labelled Round 18), `1.2–2.2 W` (M3_R10:354, ORDERING:607, R10_VALIDATION:2487, all labelled), `J440.1 or J440.2` (R10_VALIDATION:2668, ORDERING:694, handoff:62, consistent with the class definition at R10_VALIDATION:2639).

## Coverage limits

No full `tools/check.sh` (read-only rule); gate behaviour taken from the gate lens's seeds plus the triage's measurements. Datasheet facts not re-read beyond those the lenses cite; the HV6120 stall figure has no cached maker sheet.
