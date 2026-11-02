# R10 round 28 — power lens (Claude)

Target commit `19dd0b5`; board SHA-256 `a0ec075e…` before and after (unchanged). Read-only; probes in
`.supervisor/r28_power/`.

**Totals (real errors only): 0 Critical / 0 Major / 3 Minor.**

## Findings

### R28-POWER-01 (doc, Minor): GAP-1 quotes the pre-AUX 12.370807 W as the budget's converter load
- **Where:** `parts_qualification.md` line 458 ("GAP-1, requirements audit 2 (current Calc / Inference)"):
  "`parts_budget.json` now includes 12.370807 W normal converter allocation with SD writes and always-on GPS/radio."
- **Contradicts:** `parts_budget.json` `fire_current_GAP1.other_converter_load_W` = `battery_break_load_W.c_camera_radio_gps_on[1]`
  = 13.064091 W, and the same paragraph's later "(other converter load 13.064 W with the 100 mA AUX allowance)".
- **Evidence:** 5.546269 V × 1.461 A / 0.80 + 1.4 + 0.825 + 0.016933 W = 12.370807 W (no AUX); with aux_A 0.1 A,
  × 1.561 A gives 13.064091 W. The regenerated budget (byte-identical to the committed one) holds no 12.370807. The line
  dates from round 18 (acba196), before the AUX port.
- **Fix:** "13.064091 W (12.370807 W before D-R19-14's 100 mA AUX allowance)".

### R28-POWER-02 (calc, Minor): D-R27-01's `loaded_pack` uses 1.46 A, not the 1.461 A its comment and record claim
- **Where:** `m3_design/r10_parts.py` line 448: `5.456 * (1.46 + aux_A)`. The comment above it (lines 444–446) says
  "camera 1 A + radio .3 + GPS .15 + 11 mA + the AUX allowance …, as ports_w does". D-R27-01 says "the way ports_w does".
  `ports_w` (line 415) uses `1.461 + aux_A`.
- **Evidence:** solving the generator's own equation:
  - with 1.56 A: 5.881014 / 4.388745 V (the budget values);
  - with the stated 1.561 A: 5.880831 / 4.388491 V.

  So the 6 V figure quoted as 4.389 V (STATUS, parts_qualification, D-R27-01) is 4.388 V on the stated basis. The
  difference is 0.25 mV; no limit moves.
- **Fix:** use `1.461 + aux_A` and regenerate, or state 1.46 A (10 mA) in the comment and D-R27-01.

### R28-POWER-03 (doc, Minor): "four on PORT_4V8" on the current board; there are five
- **Where:** `parts_qualification.md` lines 584–586: "on the current board: … four on PORT_4V8 (C406, C407, C411, C421,
  plus C410 and C420 as local bypasses) …".
- **Evidence:**
  - The netlist's PORT_4V8 carries C445 (22 µF, C21397) and C444 (100 nF) as well.
  - The JLC BOM's C21397 line lists C445.
  - The file's own round 19 table names C444 / C445 as the AUX cell.

  The sentence is from round 18. The header's round 19 supersession does not make the present-tense count true.
- **Fix:** "five on PORT_4V8 (C406, C407, C411, C421, C445, plus C410, C420 and C444 as local bypasses)".

## Fix verification
| Change | Measurement | Verdict |
|---|---|---|
| D-R27-01 | The budget SHA is `ecc45417…`, and the in-memory regeneration on the board is identical. The diff against `816038c` changes only the two pack lines, 5.899191 → 5.881014 V and 4.414002 → 4.388745 V. | Partly: the AUX allowance is counted, but the 11 mA it claims to mirror is not (POWER-02). |
| GAP-3 U401 docs (round 27 docs lane) | 0.489653 W; 109.17–123.86 °C at 70 °C and 124.17–138.86 °C at 85 °C; 112.32 °C/W; AUX limit 112.4 mA | Confirmed |
| Stall-input paragraph | Matches the generator as coded | Confirmed (as coded) |
| D-R26-03 | Four-stall point: 5.713190 V and 1.278747 A. Single drop-out: 8.066 ms at 5.713 V; 10.345 / 20.111 / 26.023 ms at 6.0 / 7.4 / 8.4 V; 6.300 ms at 5.5 V; 10 ms at 5.956 V. Late-block window limits: 7.501 / 7.629 / 5.871 / 9.594 ms. EN at 7 ms: 1.1295 / 1.1330 V. Rule 8 corners: 5.7132 / 5.5576 / 5.5555 / 5.5085 V. Turn-on: 30.3–129.8 ms. U9 turn-off: 4.802 / 4.835 / 4.875 V. | Confirmed |
| D-R26-02 / -04 hot-plug inputs | `--extract` on the board gives inputs byte-identical to the committed file; the digest equals the results' `inputs_sha256` | Confirmed |

Other budget-derived figures recomputed and found correct:
- **Hold-up:** 0.464–0.539 / 1.304–1.412 ms, and 0.103–0.164 / 0.291–0.430 ms from the PA6 trip.
- **USB-only:** 0.4596 / 0.4856 / 0.281–0.296 A, 1.61 W; U10 limit 0.3477–0.4530 A.
- **U9 bound:** 3.743861 A and 3.946188 A, a 0.202327 A margin.
- **Buck:** 2.911 / 3.160 / 1.810 A; ripple 0.74–0.76 A.
- **Load-switch gate:** 4.744 V and 31.9 ms.
- **R134:** 35.80 W and 61.2 / 44.1 W.
- **Watchdog:** 34.853 ms.
- **Pack row:** 4.802 / 4.835 / 4.875 V.
- **Body-diode fire currents:** 1.128 / 1.063 A.
- **Endpoint minima:** 4.642 V (AUX module) and 5.031682 V (camera).

K-power (run read-only) passes with every floor at or above its IPC-2152 width.

## Observations (not counted)
1. The parts_qualification ride-through table and OQ-5 paragraph cite the budget but carry a pre-microSD, pre-AUX model: 8.7 / 8.2, 0.55–0.65 / 0.53–0.62, 4.6 / 7.2 and 2.3 / 3.7 ms. The budget gives 7.43–7.49 / 7.05–7.11, 0.49–0.57 / 0.46–0.54, 3.84 / 6.00 and 1.57 / 2.46 ms. The file header supersedes the "ride-through records", as in R25 obs 9.
2. The Q122 gate is "at most 0.218 V" with nominal resistors and 0.2203 V with 1 % parts (budget); it is far below 0.65 V either way.
3. The pad-energy worksheet (sealed D-R17-01) has no AUX allowance (about +0.69 W), and owner row 17 is open.
4. The U400 input feed is 0.4 mm. That is enough at the normal load even at 5.71 V; only the firmware-cleared camera-short fault needs 0.43 mm.
5. K-power's 2.9 A U9 design current covers every continuous budget case: the most is 2.59 A, in the camera-short case at 5.71 V.
6. The 1.2 W low end of "U400 and L400 lose 1.2–2.2 W" implies about 87.5 % efficiency; the budget's 80–85 % gives 1.48–2.16 W. The upper end, which drives the conclusion, agrees.
7. "Upstream coordination" (2.92 A asserted) is still port-switch-era text, as already recorded in R25 obs 9.
8. All K-power paths pass on `a0ec075e…`; only the six named POWER_NARROW entries are narrower.
9. The regulator FB taps are all in SINGLE_OPEN_TAPS:
   - U400 at C403.1;
   - U401 at R402.1 on the OUT run before the vias;
   - U2.1 through two vias.
10. U401 meets TPS7A91's recommended operating conditions: COUT ≥ 10 µF and VIN ≤ 6.5 V. The 4 mA IGND is the p5 maximum.
11. U9's VOVLO recommended range of 0.5–1.5 V holds for BAT_IN of about 4.07–12.2 V; the 12.2 V edge is already disclosed.
12. The EN and OVLO pull-ups (940 kΩ, 2 MΩ) meet TI's "≥ 350 kΩ" reverse-polarity note, and R84 is within the RILM range.

## Coverage limits
- The hot-plug simulation was not re-run; only its inputs were re-extracted.
- No thermal or DC copper solve was done.
- The 5.6465 V and TCR window limits were not recomputed.
- No other round 28 lens output was read.
