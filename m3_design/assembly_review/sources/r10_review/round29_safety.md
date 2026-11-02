# R10 round 29: safety lens

Target commit `09a564e`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256 the same before
and after). Read-only. Probes and scripts are in `.supervisor/r29_safety/`. The JSON twin is `round29_safety.json`.

## Totals

| Critical | Major | Minor | Observations |
|---|---|---|---|
| 0 | 1 | 0 | 19 |

## Finding

### R29-SAFETY-01 (rule, Major): AGENTS §2.5 labels still missing on five safety figures

Round 28 ruled (R28-TRI-09) that an inference-based figure must carry its Inference label where it is stated, and that
"Calculation" alone is not enough. The round 28 status lines (AGENTS.md:32, M3_R10.md:33 and :182, STATUS.md:18) say the
fix pass labelled every model figure that rests on an inferred input. These five current statements do not:

| Place | Statement | Same figure labelled elsewhere |
|---|---|---|
| FMEA_REDUNDANCY.md:37 (H-6, ESD outcome (c)) | "the worst case is about 9.6 V (Calculation, against EN's 6.5 V absolute maximum)" | M3_R10:456-457 "(Inference)"; ORDERING:651 "p7; Inference" |
| REQUIREMENTS.md:64 (F9) | "... would give about 7.5 V nominal on EN, about 9.6 V worst case ..." (no label); outcomes "(R23-SAFETY-06, Calculation)" | as above |
| FMEA_REDUNDANCY.md:38 (I-5) | "991 microstrain at 100 g, plate model" | R10_VALIDATION:2534 "(Calculation/Inference)"; owner row 1 "(R21-SAF-03, Inference; §1)" |
| R10_VALIDATION.md:2646 (§2) | fire budget "1.540851 A idle and 1.475765 / ... / 1.278747 A", no label | M3_R10:322 "Fire budget (Calculation / Inference)"; REQUIREMENTS F7; AGENTS:20 |
| R10_VALIDATION.md:2714 (§5) | "calculated 34.853 ms against 36 ms" | AGENTS:25 and binding-note obligation 7: "Calculation on allocations / Inference" (round 28 replaced AGENTS's own "(calculated)") |

Why the ESD figure is an inference: 1.2 µC / (0.72 × 220 nF) + 2.063 V = 9.648 V; C87's 0.72× minimum carries a ≤ 6 %
X7R DC-bias allowance that D-R19-10 labels an Inference (without it, 9.193 V), and the figure assumes the whole charge
reaches C87 (`esd_calc.py`). The fire budget rests on Q124's inherited hot factor (parts_qualification.md:490,
`r10_parts.py:460`). Outside this lens, owner row 32's plate-model 125 / 133 g (R10_VALIDATION:2404) is unlabelled too,
while ORDERING:702 and the handoff label it.

**Fix (text only):** add the Calculation / Inference labels with the inferred inputs named (C87's bias allowance and the
full-transfer assumption; the plate model; Q124's hot factor and the unmeasured allowances; the gate-discharge model's
0.4 V criterion and hot gate charge), label owner row 32, and either sweep the rest of R10_VALIDATION §2-§13 for model
figures or narrow the status claims to what was swept. No board change.

## Fix verification (round 28, this lens)

| Item | Verdict | Basis |
|---|---|---|
| D-R28-02 / R28-TRI-05: rule 3 meter check | confirmed | QSPI_IO2 = {U1.1, U3.3}; PYRO1_GATE_N = {U1.3, R126.1, R127.1}; 910.9 Ω (901.8 Ω at −1 %) plus a clamp diode one way, open or rising the other; identical text in the binding note, M3_R10:1094-1103, ORDERING:652, FMEA:39, R10_VALIDATION:2561 |
| D-R28-03 / R28-TRI-09: rule 3 labels | confirmed | label present in all five places; figures match the R23 severity check |
| D-R28-03 / docs lane: the §2.5 sweep | partly | R29-SAFETY-01 |
| D-R28-04: rule 4 Q120 criterion, rule 3 "before first power" | confirmed | Q120.4, C120.2 and R120.2 share one B.Cu island that reaches R121 only through (16.2,73.3) / (15.4,72.85); \|VGS\| = 0.833 V_S (4.742 V at 5.71 V); intact drop ≤ 2 × 12.3 mΩ × 2.7 A plus copper, under 0.2 V; body diode 0.7–1.0 V |
| R28-TRI-01: FMEA divider row | confirmed | R168 / R170 / R172 absent; dividers go straight to U1.15 / U1.33 |
| Audit B #4, #6, #10, #11, #12, #13 | confirmed | C84 window 411–617 µF; cold-screen values reproduced; ESD ramp 4.288 / 4.802 and 4.723 / 5.250 V; probe points match; CONT = BUS through the dummy; the no-USB precondition matches AGENTS |

## Checks of the lens focus

- **AGENTS §2.1–§2.4 on the board: hold.** RAW_ACT is fed only through Q121, which does the forward blocking because
  Q120's body diode conducts from BAT_IN to ACT_FET_S. Every gate has its full network:
  - Q124: R126 220 Ω, R128 10 k / R127 1 k, C126 220 nF;
  - Q120 / Q121: R121 10 k, R119 / R120 100 k, C120 1 µF;
  - Q122: R122 1 k, R123 2 k, C123 10 nF.

  Every part is in the JLC BOM and CPL. Firmware rules 1 and 3–6 keep the launch, ground-refusal and never-veto rules.
- **§1 pair table, owner rows 1, 2 and 24: every gap matches its stated board.** Re-measured on `a0ec075e…`: the
  0.150 mm minimum; 0.1772 / 0.1804 / 0.5004 mm PYRO1_OUT to GND; 0.7935 mm to BUZZ_DRV; ≥ 1.0406 mm to 3V3 / 3V3A; the
  gate nets 1.0585 / 1.0654 / 1.0808 / 1.1454 mm; the EN pairs 0.200 / 0.2004 / 0.330 / 0.5004 / 0.5201 mm; and the rest
  listed in the JSON.
- **Per-flight checks: consistent with the circuit.** Step 3 is the only screen of the three PC1 / bus latch pairs: no
  other BAT_ENABLE neighbour within 1.25 mm is energised only with the bus enabled.
- **Single-fault scan (bus energised, fire, board on with J400 open): every new pair is benign or in a disclosed
  class.** It covers every foreign item within 1.25 mm of the 21 protected nets on four layers. The new pairs are in the
  observations.

## Observations (not counted)

- **Rule 3's ground refusal:** it says "a known pattern"; the source specified all-ones at the default 25 % DRV.
- **Q124 gate to drain, 0.520 mm:** a bridge is in the OUT-to-lower-potential class; R25 already considered it.
- **More PYRO1_OUT-to-GND gaps:** 0.237, 0.325, 0.414 and 0.467 mm; the class is disclosed and the records name its minima.
- **PYRO1_OUT to BUZZ_G, 0.510 mm:** benign (≤ 8.4 mA through 1 kΩ).
- **ACT_GATE to BAT_IN, 0.2177 mm:** fail-safe.
- **U9 bypass pairs:** unchanged on this board; ruled in R25.
- **I-5 routes through via barrels:** two more via-barrel I-5 routes at 0.2505 mm; the lists are not complete by ruling.
- **FMEA I-5 fill-edge lengths:** they are the `0dc84776…` figures; this board gives 138.3 / 35.8 / 34.8 mm by sampling.
- **J440.1 chafe onto J121.1:** "fires by itself" is a conservative overstatement.
- **Rule 4's 0.96 band:** it depends on the load; it is to be qualified.
- **Ratio 0.93–1.01×:** it spans the full R23 case set; ruled in R27.
- **Rule 3's 47–53 µs:** it is the source's range.
- **F6 / owner row 21 chatter trains:** covered by the labels on their cell and row.
- **The S-8 table's J400.2 In1 figure:** labelled history.
- **Rule 3 meter criterion:** no verdict for 100–900 Ω.
- **AGENTS §2.1–§2.4, the gap re-measurements, the per-flight consistency and rule 4's via islands:** confirmed (details
  in the JSON).

## Coverage limits

- No physical or firmware tests, and no re-runs of the QSPI fight, plate, fire, EN or hot-plug models.
- Zone fills are as saved; distances are upper bounds within 0.5 µm.
- Non-safety model figures were only sampled, and parts_qualification.md was not swept for labels.
- Historical sections were not judged.
- check.sh was not run on the canonical tree.
- Other lenses' round 29 reports were not opened.
