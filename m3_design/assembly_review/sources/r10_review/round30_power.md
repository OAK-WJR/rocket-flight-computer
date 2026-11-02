# R10 round 30 review: power lens

Target commit `0afaed3`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (the same before and after). Read-only. Probes are in `.supervisor/r30_power/`.

## Totals

Critical 0 / Major 0 / Minor 0. No real errors found.

## Findings

None.

## Fix verification (round 29, power-relevant)

- **D-R29-01 rule 3 time constant 47-58 us over C126 +/-10 %**: confirmed. Binding note c5cd0fa3... carries the new phrase; 47.8/53.0/58.3 us is the triage's model (not a power figure, read only)
- **D-R29-02 pin (c) rule 8: loads are the budget's allocations, C84 has no cold-capacitance factor**: confirmed. Phrase present in binding note; hold-up 0.103-0.164 / 0.291-0.430 ms recomputed from the budget's 13.064/11.249 and 4.650/4.295 W at 300.8 uF, VLOGIC 4.84-5.17 V to 3.8 V
- **D-R29-02 pin (d) obligation 15 port lead Calculation / Inference**: confirmed. Phrase present; 470 nF scaled from SLVSEA3F Table 9-1 gives 166-196 V/s; 3.3/196+4 = 20.8 ms, 3.7/166+4 = 26.3 ms; DS41326 p5 UVLO rising 3.30-3.70 V, tSS 4 ms
- **D-R29-02 pin (f) port map U401 junction <= 125 C at 70 C with inferred 110 C/W**: confirmed. Phrase present; budget loss 0.48965 W, 70 + 110 x 0.48965 = 123.86 C; AUX ceiling 0.1118 A
- **Round 29 docs: pack-sag figures relabelled Calculation / Inference (STATUS, R10_VALIDATION)**: confirmed. STATUS round 28 entry now reads 'Calculations / Inferences on the budget model'; values 5.880831 / 4.388491 V re-solved

## Observations (not counted)

- Pad-energy worksheet (ORDERING 8.1.1): the sealed 0.461 A table and the 1.7 W physics basis both leave out the 100 mA AUX allowance (about +0.69 W at the buck input). Already a round 28 observation; the table states its inputs and its larger margins cover this; owner row 17 is open.
- Binding note rule 8: '0.22-0.31 of the break-to-3.8 V hold-up'. The exact ratios are 0.2229 and 0.3048, so 0.31 is an outward-rounded bound, not the nearest rounding (0.30). Not counted, because outward rounding of a range is conservative.
- r10_parts.py OQ-5 comment says 'VON 6.49-6.94 V'. The computed lower edge is 6.4845 V (1.15 V x 5.7 - 1.5 uA x 47 k), and parts_qualification correctly prints 6.48 V. This is a comment on a hypothetical option that was not adopted.
- check_r10.py line 2737 cites 'Diodes DS41271' for AP63203's 2.0 A rating. The cached AP63203 datasheet is DS41326 Rev 3-2, which gives the 2 A on p1. I could not identify DS41271 offline or through web search, so I cannot show the citation is wrong.
- K-power's U400 OUT design current (1.81 A, camera short) is below the camera-off GPS/radio/AUX port-short case (1.9 A LDO limit + 11 mA = 1.911 A). Even so, 1.911 A needs only 0.329 mm (F.Cu, 30 C) against the 0.4 mm floor, so no width rule is violated.
- AP63201 is used with no feedforward capacitor (DS41326 Table 1 C4) and 6.8 uH (Table 1 lists 10 uH at 5 V). No record claims the design follows Table 1. Ripple is 0.74-0.76 A, inside the 30-50 % guidance (Eq. 7).
- U400 input feed (RAW_PROTECTED, two parallel 0.4 mm F.Cu legs) is not a K-power path. Already observed in rounds 27-29.
- GAP-3's 123.9 C counts only U401's own heating. ORDERING 8.3 already discloses this and makes the AUX allowance provisional until the power-knot temperature test.
- Every power figure I re-derived matched the records; see checks_actually_executed.

## Checks actually executed

- Board SHA-256 before/after: a0ec075e... both; HEAD 0afaed3; git status clean
- Re-ran r10_parts.power_budget() on the committed board (KiCad Python, read-only import): its JSON is byte-identical to the committed parts_budget.json
- Hand re-derivation: buck/LDO bands, camera/radio/GPS/AUX endpoint minima, LDO loss 0.4897 W and junction 109.2-123.9 C / 124.2-138.9 C, AUX ceiling 112 mA, theta ceiling 112.3 C/W
- loaded_pack 5.880831 / 4.388491 V; fire loop 4.617803 ohm, 0-stall 1.540851 A; four-stall-plus-fire BAT_IN 5.713 V, shorted match 5.551-5.558 V, match+leads 5.503-5.511 V
- Ride-through table (a)-(d) at 300.8 / 470 uF to 3.5 / 3.8 V matches parts_qualification; PA6-trip hold-up and 0.22-0.31 ratio; OQ-5 VOFF/VON against DS41326 eq. 1-2 and p5; OQ-5 0.25/0.40 ms and 3.8/6.0, 1.6/2.5 ms
- USB-only: R85 66.5k +/-2 % gives 347.7-453.0 mA (SLVS841 eq. 1); 514.1 / 516.1 uF inventory checked against the board (C84 470, C6/C7 22, C99 0.1, C86/C98 1 uF); 2.416 / 2.426 mC, 5.33-6.95 / 5.35-6.98 ms; 2.225 W at 0.3462 ohm gives 0.4596 / 0.4856 A, 1.61 W, 0.281-0.296 A
- C120 off tau 64.52 / 129.03 ms, on-tau 10.7525 ms, 31.89 ms to 4.5 V; GAP-5 C126 RC 0.6782 ms + 0.061 ms, 34.853 ms; R134 35.7975 W, 85 C 36.345 vs 35.851 W
- EN network: turn-on 88/56/45 ms nominal, drop-out 19/33/41 ms nominal, worst 10.34 ms at 6.0 V; turn-on/off ramp nominal 4.96 / 4.51 V; EN 2.03/2.063 V; chafe 1.87/1.28 V
- Hot-plug results: 2304 rows, min -14.807373 V, falling 8.994764, rising 5.087664 V/us, R166 579.049 W / 2.979359 mJ, retained 5.9145 V at 1643.90 uF; capacitor inventory equals board's capacitor set
- Board copper (pcbnew read-only): PORT_5V3, PORT_4V8, RAW_PROTECTED, VLOGIC, 3V3 tracks/vias; U400 FB tap at C403.1, U401 FB at R402.1 on OUT run with R403.2 to U401.4 on B.Cu (no via), U401 EN two vias, thermal vias (27.3/27.9,13.6) 0.5/0.3 mm; zone fills one piece each (3V3 1430.05 mm2, RAW 1218.99, PORT_5V3 218.62, PORT_4V8 324.8)
- IPC-2152 (tools/ipc2152.py): K-power design currents vs floors (0.4 mm >= 0.343 mm at 1.9 A In2, 0.68 <= 0.7 at 2.9 A); U400 input legs 0.4 mm; POWER_NARROW entries and K-width 0.3 mm runs <= 2 mm
- Datasheet text (cached PDFs): TPS7A91 ROC/EC (VIN 6.5 V, IOUT 1 A, ILIM 1.5-1.9 A, IGND 3.5/4 mA, RthetaJA 62.5), AP6320x (UVLO, IPEAK 2.5-3.1 A, EN thresholds/currents, VFB, tSS, Table 1/2), TPS2121 pins and Table 9-1 and OV thresholds (OV1 trip 5.76-6.27 V), TPS25947 EN/OVLO/ILIM tables and ITIMER open allowed

## Coverage limits

- No physical tests; no full check.sh; no gate seeds run (no realistic power-gate miss identified to seed)
- EN chatter-train (7.50 ms) and hot-plug solver not re-run; only spot re-derivations and result-file reads
- DS41271 identity unverified (offline / search returned nothing)
