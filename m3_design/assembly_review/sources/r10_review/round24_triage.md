# Round 24 triage (verifier, Claude)

Target commit `f2b8251`, board `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e` (SHA-256 identical before and after). Probe scripts and seed copies: `.supervisor/r24_triage/`.

**Totals: 0 Critical / 0 Major / 17 Minor real errors**, all text, record or check fixes (`board_change` false for every one). 24 lens findings were reproduced; 22 of them become 16 real errors after merging duplicates; R24-GATE-01 and R24-MCU-03 are observations. One root-flagged observation was promoted (gate obs 5, R24-TRI-17); MCU obs 6 is merged into R24-TRI-16. Not reproducible: none.

| ID | Merged | Kind | Sev. | Title | Board change |
|---|---|---|---|---|---|
| R24-TRI-01 | R24-SAFETY-01, R24-DOCS_BINDING-01 | doc | Minor | BAT_ENABLE via (17.1,82.8) to BAT_FAULT_N is 0.173 mm on 1407e850, not the 0.200 mm ("re-measured ... unchanged" / "not changed") the records state | no |
| R24-TRI-02 | R24-SAFETY-02, R24-POWER-01, R24-REQUIREMENTS-01 | calc | Minor | "The EN timing figures stand / are kept" is wrong: D402's 50 nA adds to U9's own +/-0.1 uA EN leakage (and drains C87 through R165 with J400 open) | no |
| R24-TRI-03 | R24-SAFETY-03, R24-POWER-02 | doc | Minor | The first-article / post-discharge bench-ramp window (turn-off 4.5-4.8 V, turn-on 4.9-5.2 V) rejects in-spec boards and contradicts the battery_entry sheet note | no |
| R24-TRI-04 | R24-SAFETY-04 (a)(b)(c), R24-MCU-01, R24-MCU-02 | doc | Minor | Single-via statements not carried to D-R24-02 / D-R24-08: Q120's gate, R91.1 and U1.28 still "on one via" | no |
| R24-TRI-05 | R24-SAFETY-04 (d)(e) | doc | Minor | D-R24-02 barrel records: Q121 barrel "0.342 mm from the nearest foreign copper" (GND fill is 0.2505 mm) and "eight" R18_BARREL_KEEPOUT areas (the board has ten) | no |
| R24-TRI-06 | R24-SAFETY-05 | doc | Minor | M3_R10 Power still says via (30.575,11.6) joins R402.1 to the In2 output plane; D-R24-09 removed it | no |
| R24-TRI-07 | R24-SAFETY-06, R24-REQUIREMENTS-02 | doc | Minor | REQUIREMENTS M1 quotes stock_check.json 2026-10-31T23:23Z with U9 40 / -69; the committed file is 2026-11-02T01:42:53Z with 28 / -83 | no |
| R24-TRI-08 | R24-REQUIREMENTS-03 | calc | Minor | P3 landing load: 8.0 m/s over 20 mm crush is 163 g, not 168 g | no |
| R24-TRI-09 | R24-REQUIREMENTS-04 | doc | Minor | J2 land distances to the (4,44.3) support are bounding-square figures (3.871 / 3.918 mm), not the round lands (3.880 / 3.987 mm) | no |
| R24-TRI-10 | R24-MCU-04 | doc | Minor | R10_VALIDATION section 5: QSPI lengths "4.110955-14.524012 mm"; on 1407e850 QSPI_IO2 is 14.102245 mm | no |
| R24-TRI-11 | R24-DOCS_BINDING-02 | doc | Minor | ORDERING 8.2 says 14 pin legends are on the bottom; its own list and the board have 13 | no |
| R24-TRI-12 | R24-DOCS_BINDING-03 | doc | Minor | R10_VALIDATION section 9 C84 row gives the superseded paste totals F 253 / B 375 | no |
| R24-TRI-13 | R24-DOCS_BINDING-04 | doc | Minor | round24_board_cad record calls the orientation-reconstruction counts (69 + 122 -> 67 + 125) CPL "rows per side" | no |
| R24-TRI-14 | R24-DOCS_BINDING-05 | doc | Minor | STATUS.md line 5 says the R10 section was last updated 2026-10-31; it carries 2026-11-01 entries | no |
| R24-TRI-15 | R24-GATE-02 | gate | Minor | No check holds the 2.5 mm short-edge component clearance D-R24-15 restored; R92 / TP88 moved back pass every gate | no |
| R24-TRI-16 | R24-GATE-03, R24-MCU observation 6 | doc | Minor | BOOT0's second via is cited as D-R24-05 (U9's EN kept single) in route_check's PARALLEL_VIAS reason and the generator; it is D-R24-03 | no |
| R24-TRI-17 | R24-GATE observation 5 | doc | Minor | check_actuators r10 failure message names the R9 pin J1.3 ("J1.3 only through R80 to BAT_IN"); on R10 the switch source is J400.1 and J1 has no pin 3 | no |

## Evidence and fixes

### R24-TRI-01: BAT_ENABLE via (17.1,82.8) to BAT_FAULT_N is 0.173 mm on 1407e850, not the 0.200 mm ("re-measured ... unchanged" / "not changed") the records state

- Evidence: pcbnew shape distance (SHAPE.Collide bisection, .supervisor/r24_triage/meas.py): F.Cu chamfer track (16.55,82.99)-(16.91,83.35) 0.2 mm wide is 0.173262 mm from the 0.5 mm via (17.1,82.8) on 1407e850; 0.200041 mm on 5516eeec (old corner run x=16.55). Closed form: (1.1 - c)/sqrt2 - 0.35 with c = 0.36 cut gives 0.1733 mm. No rule requires 0.200 mm: D-R19-02 records it as a consequence of U9 fan-out ("neither opens without moving U9's pins"), not a floor; owner row 24, ORDERING 8.3 coating worksheet and FMEA H-6 / V-18 select this via for coating by name, whatever the gap; the 0.58 Mohm latch-leak figure does not depend on the gap; D-R24-17 has no clearance-keeping constraint; 0.173 mm > the 0.15 mm board floor (DRC 0). The false statements: M3_R10 291-292 (BAT_FAULT_N clearances "re-measured on 1407e850 ... unchanged") and 306-307; ORDERING 570; FMEA_REDUNDANCY 36; R10_VALIDATION 2092 (owner row 24) and 2252 ("not changed"); also D-R24-11 "Kept" line ("no copper east of J400 moved").
- Fix: Text route (recommended): write 0.173 mm in M3_R10 (306-307; drop BAT_FAULT_N from "unchanged" at 291-292), ORDERING 8.3 line 570, FMEA H-6, R10_VALIDATION row 24 and the section 1 pair row (replace "not changed" with "0.200 -> 0.173 mm by the D-R24-17 chamfer"), and qualify D-R24-11's Kept line. Board route: a CHAMFER_CUTS entry (BAT_FAULT_N, F, 16.55, 83.35) <= 0.322 mm (0.32 gives 0.2015 mm, diagonal 0.453 mm >= the 0.2 mm floor) restores 0.200 mm, but changes copper and restarts the count.

### R24-TRI-02: "The EN timing figures stand / are kept" is wrong: D402's 50 nA adds to U9's own +/-0.1 uA EN leakage (and drains C87 through R165 with J400 open)

- Evidence: Own corner model (.supervisor/r24_triage/en_model.py: R80/R165/R81 +/-1 %, C87 0.72-1.27 x 220 nF, VUVLO(R) 1.183-1.223 V, VUVLO(F) 1.076-1.116 V, IENLKG +/-0.1 uA, TI SLVSFC9C p9) reproduces D-R20-11 exactly without D402: 6.579 / 8.496 / 10.651 / 20.473 / 26.414 ms at 5.5 / 5.73 / 6.0 / 7.4 / 8.4 V, pack floor 5.917 V, turn-on 30.31-128.56 ms (6.0-8.4 V), chatter trip 20.6 % / 25.0 % at 5.73 / 6.0 V, turn-off corner 4.778 V. With D402 at the record's 50 nA (Infineon ESD103 Rev 1.3 Table 3) at J400.2 (closed) and through R165 (open): 6.300 / 8.204 / 10.345 / 20.111 / 26.023 ms, pack floor 5.956 V (5.941 V counting only the closed-switch shift D-R24-11 computed), turn-on 30.44-130.27 ms, chatter trip 20.0 % / 24.4 %, turn-off corner 4.802 V, turn-on corner 5.251 V. At F4's 5.92 V pack the worst drop-out immunity is 9.83 ms < the 10 ms criterion. The 25 nA-equivalent argument in D-R24-11 is right as arithmetic (5.685 mV) but the conclusion is wrong because the two leakages add.
- Fix: Text only. Strike "stand / are kept" in D-R24-11, M3_R10 (Logic and switch, J400 ESD), ORDERING 8.3 J400 ESD (line 648), REQUIREMENTS F9 and parts_qualification; replace the D-R20-11 worst cases wherever quoted (REQUIREMENTS F4 / F6, AGENTS section 1 table, M3_R10, ORDERING 8.3 chatter row 617, R10_VALIDATION, STATUS, battery_entry sheet note, r10_sch_check obligations -> regenerated binding note): drop-out 10.3 / 20.1 / 26.0 ms at 6.0 / 7.4 / 8.4 V, 8.2 ms at 5.73 V, 6.3 ms at 5.5 V; 10 ms needs a pack >= 5.96 V; turn-on 30-130 ms; chatter "above about 20-24 %" (was 21-25 %); PA6 rule in F6 / M3_R10 / binding note: "above U9's 4.80 V BAT_IN turn-off corner" (was 4.78 V; PA6 lower edge 0.44 V x 11 = 4.84 V still above it). Or keep the old figures labelled "without D402" and give these shifts.

### R24-TRI-03: The first-article / post-discharge bench-ramp window (turn-off 4.5-4.8 V, turn-on 4.9-5.2 V) rejects in-spec boards and contradicts the battery_entry sheet note

- Evidence: Pack voltage at the EN threshold = VT x (R80+R165+R81)/R81 + IEN x (R80+R165) + ID402 x R80 over all 1 % / threshold / leakage corners (same model): healthy turn-off 4.288-4.778 V (4.802 V with D402 50 nA), nominal 4.505 V; turn-on 4.723-5.227 V (5.251 V), nominal 4.960 V. The ORDERING 8.3 (line 648), REQUIREMENTS F9 and M3_R10 347 window puts the nominal turn-off on its lower edge and excludes 4.29-4.50 V turn-off and 4.72-4.90 / 5.23-5.25 V turn-on. The sheet note (on 4.89-5.05 V, off 4.45-4.61 V) is thresholds x nominal ratio only (1.183 / 1.223 / 1.076 / 1.116 x 4.1333), so the two records also disagree. A healthy board can be taken for a damaged EN pin, so the required check cannot be carried out correctly as written.
- Fix: Text only, in ORDERING 8.3, REQUIREMENTS F9, M3_R10 (J400 ESD) and the battery_entry sheet note: expect turn-off 4.29-4.80 V and turn-on 4.72-5.25 V (TI SLVSFC9C p9, 1 % resistors, +/-0.1 uA, D402 <= 50 nA); a turn-off above 4.80 V means extra leakage to GND at EN or J400.2 (outcome (b) or a leaky D402), one below 4.29 V leakage from IN; or record each board's own first-article baseline and compare against it.

### R24-TRI-04: Single-via statements not carried to D-R24-02 / D-R24-08: Q120's gate, R91.1 and U1.28 still "on one via"

- Evidence: Board 1407e850 (.supervisor/r24_triage/meas2.py): ACT_GATE vias (16.2,73.3) + (15.4,72.85) and (11.14,71.7) + (11.74,72.3); LOGIC_SOURCE_ST (30.45,51.4) beside (30.85,51.8); 3V3 (28.1,59.4) beside (28.1,60.0); check_r10 single_via_opens (MCU, power, safety lenses) gives no single point for Q120.4, Q121.4, U1.28, R91.1. False text: M3_R10 Firmware rule 4 (963-964, "Respin: a second via at Q120's gate (16.2,73.3)"), rule 5 (965-967, "R91.1 and U1.28 each hang on one via (D-R22-02)"), r10_sch_check.py 318-319 and r10_binding_note.json obligations 39 / 40 (same text), R10_VALIDATION section 1 row 2250 ("Q120's gate via (16.2,73.3), the only link ... single via"). FMEA line 41 and M3_R10 348-351 already state the opposite, so the records also contradict each other.
- Fix: Re-word rule 4 (Q120-off now needs two opens; drop the respin line), rule 5 (each tap has a second via since D-R24-08; PC1 source rule stays an extra barrier) in M3_R10 and r10_sch_check.py, regenerate the binding note, and mark the R10_VALIDATION section 1 Q120 row as fixed by D-R24-02 (two barrels).

### R24-TRI-05: D-R24-02 barrel records: Q121 barrel "0.342 mm from the nearest foreign copper" (GND fill is 0.2505 mm) and "eight" R18_BARREL_KEEPOUT areas (the board has ten)

- Evidence: pcbnew (.supervisor/r24_triage/meas3.py): via (11.74,72.3) land to GND fill 0.2505 mm on both F.Cu and B.Cu (via (15.4,72.85): 0.2505 mm on F.Cu); R10_VALIDATION 1994 says "B.Cu 0.361 / 0.342 mm from the nearest foreign copper" (D-R24-02 itself correctly names the specific neighbours). Rule areas named R18_BARREL_KEEPOUT_*: ten (ACT_GATE_0..3 incl. the new (15.4,72.85) / (11.74,72.3), PYRO1_OUT_8/9, BAT_ENABLE_4/5/6, BAT_SW_RETURN_7); M3_R10 482 says "eight in all" and that the two new barrels are held off by other keep-outs.
- Fix: R10_VALIDATION 1994: "B.Cu 0.361 mm from Q120.9 (BAT_IN) / 0.342 mm from ACT_FET_S; both lands 0.2505 mm from the outer GND fill (accepted surface class)". M3_R10 482: "ten in all, including D-R24-02's two ACT_GATE barrels".

### R24-TRI-06: M3_R10 Power still says via (30.575,11.6) joins R402.1 to the In2 output plane; D-R24-09 removed it

- Evidence: No via at (30.575,11.6) on 1407e850 (present on 5516eeec; meas.py). M3_R10 614-618 (current Power section, present tense) also names the OUT via (29.75,12.6), now (29.75,11.65). R402 is on the B.Cu OUT run with no via (D-R24-09). The line-76 table row is under a round 20 history heading and is not counted.
- Fix: Rewrite the M3_R10 Power bullet: R402 / R403 sit beside U401 on B.Cu (D-R24-09), R402.1 is on the OUT run, U401 OUT keeps two In2 vias (29.75,11.65) / (29.75,9.95); no single via cuts the sense.

### R24-TRI-07: REQUIREMENTS M1 quotes stock_check.json 2026-10-31T23:23Z with U9 40 / -69; the committed file is 2026-11-02T01:42:53Z with 28 / -83

- Evidence: fab/stock_check.json checked_utc 2026-11-02T01:42:53Z, C3662793 jlc_stock 28, orderable -83, min_purchase 7; C51931514 9 / 2. AGENTS section 1, ORDERING 302 and M3_R10 already use the new run.
- Fix: Update M1 to 2026-11-02T01:42:53Z, U9 28 in stock / -83 orderable / minimum 7.

### R24-TRI-08: P3 landing load: 8.0 m/s over 20 mm crush is 163 g, not 168 g

- Evidence: a = v^2 / 2s: 8.0^2 / 0.04 = 1600 m/s^2 = 163.2 g; 6.2 m/s -> 98.0 g; 168 g needs 8.11 m/s. Quoted as 98-168 g in REQUIREMENTS P3 (74), ORDERING 699, R10_VALIDATION rows 12 (2090) and 32 (2112). The conclusions (above the 125 g plate figure; about 330 g for 2x) stand.
- Fix: Write 98-163 g in the four places (2x: about 330 g -> about 326 g, still "about 330 g").

### R24-TRI-09: J2 land distances to the (4,44.3) support are bounding-square figures (3.871 / 3.918 mm), not the round lands (3.880 / 3.987 mm)

- Evidence: pcbnew: J2.1 (3V3) round 0.7874 mm land at (3.73,40.035): centre 4.2735 mm, edge 3.8798 mm; J2.3 (NRST) at (5.0,40.035): edge 3.9870 mm. Its bounding square gives 3.871 / 3.918 mm exactly. tools/fit_check.py uses the true shape. Quoted in REQUIREMENTS P2 (3.808-3.918), M3_R10 817-818 (and 0.31-0.42 mm from the washer edge, now 0.31-0.49), R10_VALIDATION 2645, ORDERING 700, R10_VEHICLE_HANDOFF 75. Conservative; the nylon-hardware conclusion stands.
- Fix: J2.1 3.880 mm, J2.3 3.987 mm; range 3.808-3.987 mm; 0.31-0.49 mm from a 7.0 mm washer edge.

### R24-TRI-10: R10_VALIDATION section 5: QSPI lengths "4.110955-14.524012 mm"; on 1407e850 QSPI_IO2 is 14.102245 mm

- Evidence: pcbnew track sums (meas5.py): QSPI_IO2 14.524012 -> 14.102245, QSPI_CLK 7.85 -> 7.428234 mm (D-R24-17 chamfers), others unchanged, one via each. The row (line 2403) names no older board, so under "Inventory basis" it is a statement about 1407e850.
- Fix: "QSPI lengths span 4.110955-14.102245 mm, one via each".

### R24-TRI-11: ORDERING 8.2 says 14 pin legends are on the bottom; its own list and the board have 13

- Evidence: B.Silkscreen n:xxx texts on 1407e850: 13 (2:E1+, 2:SW, 4 x 2:GND, 2:S2, 3:RXI, 3 x 3:TXO, 4:RXI, 4:S4); F.Silkscreen 14; 27 in all (meas4.py). ORDERING line 416 list also counts 13.
- Fix: "13 pin legends are on the bottom".

### R24-TRI-12: R10_VALIDATION section 9 C84 row gives the superseded paste totals F 253 / B 375

- Evidence: fab/m3_gerber.zip F_Paste 249 and B_Paste 381 flashes (D03 count); 249 / 381 pasted pads on the board (meas4.py); line 2659.
- Fix: paste F 249 / B 381.

### R24-TRI-13: round24_board_cad record calls the orientation-reconstruction counts (69 + 122 -> 67 + 125) CPL "rows per side"

- Evidence: fab/m3_cpl_jlc.csv on f2b8251: 70 Top + 136 Bottom = 206 rows (5516eeec: 72 + 133); 67 + 125 (+ 14 placement-only) are jlc_orient's reconstructed parts. round24_board_cad.md line 56 and .json cpl.sides; the .json r10_fab_sh "67 top + 125 bottom, 206 rows" has the same confusion.
- Fix: "CPL rows 72 + 133 -> 70 + 136; orientation reconstructed 69 + 122 -> 67 + 125, plus 14 placement-only".

### R24-TRI-14: STATUS.md line 5 says the R10 section was last updated 2026-10-31; it carries 2026-11-01 entries

- Evidence: STATUS.md lines 9, 15, 21, 39 are dated 2026-11-01.
- Fix: "Last updated 2026-11-01 (R10 candidate section ...)".

### R24-TRI-15: No check holds the 2.5 mm short-edge component clearance D-R24-15 restored; R92 / TP88 moved back pass every gate

- Evidence: Board: R92 courtyard ymax 87.475 (2.525 mm from the y = 90 edge), TP88 87.445 (2.555 mm); the six accepted DFM queries C95 / R166 / R400 / R401 / R404 / C403 are the only parts closer (meas2.py). No check in tools/ or m3.kicad_dru tests courtyard / body to board-edge distance (grep: no short-edge rule; DRC edge clearance is copper only), so a generator edit returning R92 to F(31,87.5) / TP88 to F(35.5,87.0) (the 5516eeec poses) passes DRC, route_check, fit_check and check_r10 (gate lens seed F1). The limit is JLC assembly terms section 2.3 as cited in ORDERING 8.1 (M2: design rules within JLC's limits), with exactly six recorded exceptions.
- Fix: Checks only: add a body/courtyard-to-short-edge rule (2.5 mm) to check_r10 with an exact SHORT_EDGE_QUERIES list {C95, R166, R400, R401, R404, C403} in which a missing, stale or new part fails, plus a seeded test moving R92 back.

### R24-TRI-16: BOOT0's second via is cited as D-R24-05 (U9's EN kept single) in route_check's PARALLEL_VIAS reason and the generator; it is D-R24-03

- Evidence: tools/route_check.py:342 (the recorded reason of the named parallel via), m3_design/r10_route_core.py:108 docstring, tools/check_r10.py:3038 ("D-R24-04 / -05 give VCAP2 ... and BOOT0"), tools/test_r10_check.py 4466 / 4934 (lists "-05" among second-via decisions). R10_DECISIONS: D-R24-03 is BOOT0's second via, D-R24-05 keeps U9's EN on one via.
- Fix: Cite D-R24-03 in all five places (route_check reason, generator docstring, check_r10 comment, two test comments/docstrings).

### R24-TRI-17: check_actuators r10 failure message names the R9 pin J1.3 ("J1.3 only through R80 to BAT_IN"); on R10 the switch source is J400.1 and J1 has no pin 3

- Evidence: m3_design/check_actuators.py 575-576: switch_a is J400.1 for r10, but the req() message is the fixed R9 text. The check logic is correct; the message it prints on an R10 failure names a pin that does not exist on the board.
- Fix: Use the profile's pin in the message, e.g. f'{switch_a} only through R80 to BAT_IN'.

## Observations (not counted)

- **R24-GATE-01.** Reproduced (own seed: BAT_FAULT_N corner cut 0.05 mm, route_check exit 0, reported as an unrecorded noncritical short_segment leftover). Not a real error: every bend between two segments is 45 deg, M2 defines right_angle as two track ends meeting at 90 deg, and M2 assigns short segments on non-critical nets to review, where route_check counts them; the generator floor forbids such a cut.
- **R24-MCU-03.** The 1.662077 mm BOOT0 companion maximum sits in the "R14 manual routing receipt" paragraph, whose slow-companion measurements R10_VALIDATION section 6 explicitly scopes as historical; BOOT0 is not a critical net. (The second via is 2.000 mm from the nearest GND via, measured.)
- **routing obs: BUZZ_G T 0.02 mm before chamfer / VBUS 0.05 mm.** No segment under 0.05 mm; the T is a centre-line node in a 1.02 mm segment; D-R24-17's leg-piece floor is per segment (r10_route.chamfer_right_angles), and 0.15 mm is the largest cut its "removes copper another item joins" rule allows (a 0.17 cut ends on the T); non-critical net, review-only; CHAMFER_CUTS records the 0.15 cut.
- **routing obs: five chamfers start inside a pad land (D121.3, D121.4, U1.28, C31.2, R163.2; pad_end_offcentre 57->70, segment_inside_pad 22->27).** AUD-10 counted review items; no record (D-R24-17, round24_board_cad, M3_R10, R10_VALIDATION section 6, AVA_LAYOUT round 24 section) states their counts or that R402.1 is the only one; the final-board deviation list must count them (M2), which is not yet due.
- **routing obs: seven three-way forks with a bare 90 deg wedge.** Outside the rule: AGENTS section 3, M2 and route_check define right_angle on two track ends only; "a T or three or more ends is not a bend". Pre-existing.
- **routing obs: J440.3 / J440.4 tracks on both outer layers, GND via 3.9 mm away.** AUX_TX_WIRE / AUX_RX_WIRE are not critical signal nets in AGENTS section 3 (pyro and arming, crystal, USB data, SPI/QSPI/IMU CS; RADIO_* / GNSS_* only R7-R9), so the partner-via rule does not apply.
- **routing obs: leftover locations JSON bound to 632a9ad3.** AGENTS section 3 / M2 require counts and locations once in the final review report; section 6 gives the current count (5) and the JSON pointer sits in the labelled a3144b15 paragraph; not yet due.
- **R24 safety obs 2: leaky D402.** No record is false and the procedure is usable with TRI-03's corrected window: a D402 leak I raises turn-off by I x R80 (0.47 V/uA); the hazardous level (turn-off >= 5.73 V) needs 2.0-3.1 uA, which puts every board above the corrected 4.80 V top edge (any leak >= about 1.1 uA does).
- **manufacturing obs 10: stackup name JLC041611-7628.** Not shown wrong: JLC's impedance page (read 2026-11-01) lists only the 0.5 oz-inner JLC04161H-* templates; the name follows the same pattern for 1 oz inner (H = half oz), agrees with ORDERING 8.1 / M1 (1 oz inner, 0.030 mm = JLC's 1.2 mil for 1 oz) and has been used since R7 from the quote page; confirm on the quote page at order.
- **docs_binding obs 2: round24_board_cad.json "67 top + 125 bottom, 206 rows".** Folded into R24-TRI-13's fix.
- **other observations (safety 1, 3-11; power 1-13; routing 5, 6, 8; MCU 1-2, 4-5, 7-9; gate 1-4, 6-8; parts 1-8; mechanics 1-6; manufacturing 1-9, 11; requirements 1-10; docs_binding 1, 3-7).** Confirmations, labelled history, disclosed deviations, approximations or suggestions; none contradicts a current record or stated rule (checked against the cited lines where they touched one).

## Checks executed

- SHA-256 of the board before and after; probe copies of 1407e850 and 5516eeec (`git show 9b27268:`).
- pcbnew shape distances and inventories (meas*.py): BAT_ENABLE via gap, ACT_GATE / BOOT0 / monitor vias, Q121 barrel to fills, R18_BARREL_KEEPOUT areas, QSPI lengths, BUZZ_G geometry, J2 lands, short-edge courtyards, silkscreen pin legends, paste pads.
- Gerber paste flash count from fab/m3_gerber.zip; CPL side count; stock_check.json and cost_check.json fields.
- EN corner model with and without D402 (en_model.py): drop-out, pack floor, turn-on, chatter fraction, ramp window.
- Own GATE-01 seed (seed_g1.py) and route_check --profile r10 on it.
- Code reads: route_check right_angle / short_segment, r10_route.chamfer_right_angles and CHAMFER_CUTS, check_actuators 575-583, fit_check top_support_check.
- Web: JLC impedance page and help article (stackup names).
