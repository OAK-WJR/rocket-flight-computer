# R10 round 28: safety lens

- **Target:** commit `19dd0b5`, board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before
  and after (unchanged). Read-only; probes in `.supervisor/r28_safety/`. Machine-readable copy: `round28_safety.json`.
- **Rule:** the round 28 brief's strict definition (real errors only).

## Totals

**0 Critical / 0 Major / 1 Minor.**

## Finding

### R28-SAFETY-01 (doc, Minor): the FMEA's current R10 row claims "ADC series protection" that R10 removed

- **What is wrong.** `docs/FMEA_REDUNDANCY.md:39`, the "I-1 / I-2 / I-5; H-1 / H-2; T-3 / T-4" row of the
  "R10 applicability" table (column "Current R10 disposition"), reads: "Keep R134 2 Ω, Q124's pull-down / series
  resistor / gate-source capacitor, reset-safe gate, cold pull-up and bus / continuity dividers **with ADC series
  protection**." R10 has no ADC series protection.
- **What it contradicts.**
  - The board. On `a0ec075e…` PYRO1_CONT = {C127.1, R129.2, R130.1, R178.1, U1.15} and
    ARM1_SENSE = {C129.1, R133.1, R175.2, R180.1, U1.33}, so both divider nodes end directly on PC0 / PC5. R168, R170 and
    R172 are absent from the 216 footprints.
  - REQUIREMENTS F8: "...directly read filtered 10.2 kΩ/1 kΩ dividers ... Delete ... R168 / R170 4.7 kΩ tails ...
    Double faults can damage the MCU; no double-fault current guarantee."
  - The FMEA's own R10 amendment (lines 3–8): "R168 / R170 and the duplicate bank are removed ... The historical
    double-fault 9.4 mA limit is withdrawn."
  - M3_R10:585 ("audit 2 removes R168 / R170").
  - check_r10 S-1 (`mcu_side_issues`), which fails any MCU-side sense tail.
  - The FMEA's own terms. Line 80 lists "split sense dividers" and "ADC series protection" as separate items, and I-9
    (line 115) defines the latter as "R168–R171, 4.7 kΩ between each divider node and its ADC pin".
- **History.** The phrase dates from `73af96b` (2026-10-28), when R168 / R170 were still fitted. Audit 2 (`ff15523`,
  2026-10-29) removed them. Round 19 (`6628488`) amended the FMEA header but not this row. No round 24–27 triage
  observation mentions it.
- **Impact.** The current disposition credits PC0 / PC5 with the I-9 double-fault current limit that R10 withdrew. No
  board change and no new fire path: the single-resistor rule (≤ 3.342171 V at 19.9 V) still holds.
- **Fix (text only).** Replace "and bus / continuity dividers with ADC series protection" with "and the bus / continuity
  dividers (two 5.1 kΩ tops, two 2 kΩ bottoms, 10 nF) read directly by PC0 / PC5: audit 2 removed the 4.7 kΩ ADC
  series resistors R168 / R170, so one resistor fault stays within the pin ratings (≤ 3.342171 V at 19.9 V) but there
  is no double-fault current limit (REQUIREMENTS F8)".
- **Evidence:** `.supervisor/r28_safety/f01_evidence.txt`.

## What was checked and held

- **AGENTS §2 on the board.**
  - J400 drives U9 EN, and RAW_ACT is reached only through Q120 / Q121.
  - Q124: R128 10 k gate-source, R126 220 Ω series, C126 220 nF gate-source, R127 1 k at PE4.
  - Q120 / Q121: R119 ∥ R120 50 k, R121 10 k, C120 1 µF.
  - Q122: R123 2 k, R122 1 k, C123 10 nF.
  - All of them are defined off with U1 in reset or unpowered. The firmware and per-flight texts keep ground refusals
    and the in-flight never-veto rule. No violation found.
- **Fire-chain adjacencies (D-R26-02 / -04), §1's pair table, owner rows 1 / 2 and FMEA I-5.** Every figure re-measured
  on `a0ec075e…` reproduces:
  - PYRO1_OUT: to GND 0.1768 / 0.1800 mm, R173.1 to Q124's source via 0.500 mm, to BUZZ_DRV 0.7935 mm, to 3V3A
    1.0400 mm, to 3V3 1.0500 / 1.0511 mm.
  - Q124's gate nets: 1.065 / 1.0585 / 1.145 mm.
  - PYRO1_CONT_MID: to Q123.1 0.175 mm (diagonal 0.2005 mm), to R134.2 0.250 mm (diagonal 0.3862 mm).
  - R173.2: to D120.3 0.4154 mm, to R162.1 1.1328 mm.
  - EN-node pairs 0.200 / 0.200 / 0.330 / 0.500 / 0.1732 mm.
  - The J440.1 / J9.1 In2 rings 0.2505 mm, and the In2 3V3 fill edges 0.300 mm.
  - The barrel figures behind S-8.
- **Calculations reproduce:**
  - the cold-screen readings (99.370 / 99.339 mV healthy, 146.226 / 0 mV open, 0.295 V for an OUT–3V3 bridge,
    102.0 / 55.5 mV for a CONT_MID–RAW_ACT bridge with an open match at Vf 0.30 V);
  - the latch thresholds;
  - turn-off within 1 s after the closed-switch check.
- **D-R26-04's audit** reproduces exactly (seven rows without fills, six with) in the regions the round 26 pass changed.
- **Single-fault sweep.** It found no undisclosed path that fires, energises the bus or turns the board on with J400
  open. The bus-energising single faults (Q121 gate–drain or source–drain, ACT_DRV / ACT_GATE to GND, a Q122
  gate–drain short) are in owner row 2's class. Per-flight step 2 screens them, and firing still needs Q124.

## Fix verification

| Item | Verdict | Measurement |
|---|---|---|
| D-R26-01 | confirmed | GND vias (7.4,16.5) / (7.4,20.0) on F / In1 / B. Pins 3–4 of J410 / J420 / J440 / J9 have no inner rings; pins 1–2 keep them |
| D-R26-02 | confirmed | PYRO1_OUT is 1.0500 / 1.0511 mm from 3V3 and 1.0400 mm from 3V3A. Inner: J121.1 barrel 1.0612 mm from In2 3V3 |
| D-R26-04 | confirmed | Gate nets 1.065 / 1.0585 / 1.145 mm. The regional audit gives exactly the recorded rows |
| D-R26-03 | partly | The rule 8 and 5.71 V texts are consistent across documents; not re-computed (power lens) |
| R27-TRI-05 fix | confirmed | The H-9 wording is fixed in FMEA:37, FMEA:111, §1 (a) and the round 26 triage erratum; no other mislabel |
| D-R27-01 / -02 / -03 | not checked | Out of lens |

## Observations

There are 12, none counted; the JSON gives one line each. The main ones:
- **VLOGIC onto 3V3, not named in the I-5 route lists.** U2.1–U2.2 is 0.400 mm, and C84.1 is 0.531 mm from a 3V3 via.
  Round 27's precedent applies: the lists are not claimed complete.
- **Owner row 24 figures.** It quotes 0.5205 / 0.5008 mm against exact values of 0.5197 / 0.5000 mm.
- **Step 2's diagnosis list is incomplete.** It omits U9 IN–OUT, a switch that is not actually open, and the J1.1 In2
  ring. The required action is unchanged.
- **Rule 3's 1.19–1.98 V / 0.55 ms.** M3_R10 and the binding note state these figures without the Inference label
  that §1 and the FMEA carry.

## Coverage limits

- No DRC, route_check or check.sh run.
- The old-versus-new comparison covered the changed regions only.
- Harness, ESD, leakage and MCU-pin behaviour are Calculation or Inference.
- There are no bench or firmware results.
