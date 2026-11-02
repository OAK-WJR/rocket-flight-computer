# R10 round 29 triage (fresh verifier)

Target: commit `09a564e`, board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, the same before and
after. Read-only: no tracked file was edited, nothing was built, and git state did not change. Probe files are in
`.supervisor/r29_triage/`. The JSON (`round29_triage.json`) holds the full evidence, every `all_places` entry and all
139 observation reasons.

## Totals

| Critical | Major | Minor | Real errors | Raw findings (confirmed) | Observations | Not reproducible | Board changes |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 4 | 5 | 5 (5) | 139 | 0 | 0 |

## Real errors

| ID | From | Kind / severity | What | Board change |
|---|---|---|---|---|
| R29-TRI-01 | SAFETY-01 | rule / **Major** | AGENTS §2.5. Current safety statements still give figures that rest on inferred inputs as "Calculation" or bare model output. Four round 28 status lines claim that every such figure is labelled. | No |
| R29-TRI-02 | MCU-01, safety obs 12 | calc / Minor | Rule 3 gives Q124's gate time constant as 47–53 µs. That range covers C126 only from −10 % to nominal; C126 at +10 % gives 58.3 µs. | No |
| R29-TRI-03 | MECHANICS-01 | doc / Minor | R10_VALIDATION §8 says 23 tails on seven terminals, with J440 "not re-run". fit_check allocates all 27 tails on every gate run. | No |
| R29-TRI-04 | REQUIREMENTS-01 | rule / Minor | LS120 (MLT-5020) is rated −20…+70 °C, so it is out of rating at the stated 70 °C bay. The hot-end disposition and the chamber test cover only the 85 °C parts. | No |
| R29-TRI-05 | GATE-01 (+ gate obs 3–5) | gate / Minor | D-R28-03 says the test "pins each new label", but the turn-on label is not pinned. Reverting it to the round 27 text passes every check. | No |

### R29-TRI-01: the §2.5 sweep (the whole class)

I reproduced the 9.6 V figure: 1.2 µC / (0.72 × 220 nF) + 2.063 V = 9.65 V. The 0.72× factor carries the X7R DC-bias
allowance, which D-R19-10 labels as an Inference.

The scanner `labelscan.py` (448 figure hits; paragraph-, row- and heading-aware) and a hand reading of every hit found
these unlabelled places, all to be fixed together:
- FMEA:37 H-6 (c): 9.6 V marked "(Calculation, …)".
- REQUIREMENTS:64 F9, twice: the unlabelled 9.6 V sentence, and "(R23-SAFETY-06, Calculation)".
- FMEA:38 I-5: "991 microstrain at 100 g, plate model".
- R10_VALIDATION:2642–2647 §2: the fire currents 1.540851 … 1.278747 A, which rest on "stated assumptions"; Q124's hot
  factor is an Inference.
- R10_VALIDATION:2712–2714 §5: "calculated 34.853 ms". Owner row 7 (2369) also calls the guard and the 20 ms firing
  "calculations".
- Owner row 32 (2404): the plate model's 125 / 133 g.
- M3_R10:415–418: "about 3.23 V … Calculation". Its premise, that a hard 3V3 bridge holds PE4's net against its low
  driver, is labelled Inference at FMEA:39 and R10_VALIDATION:2569.
- STATUS:26 (and :19) and R10_VALIDATION:2346: "the pack-sag figures are Calculations on the budget model". The owning
  record (parts_qualification:693) heads them "Inference, stall input", and the round 27 records say "Calculations /
  Inferences".
- The false status claims: AGENTS:32, M3_R10:32–34, M3_R10:182 and STATUS:18.

Everything else in AGENTS outside §2, STATUS, M3_R10, ORDERING §8, the handoff, R10_VALIDATION's current sections and owner
rows, FMEA's current R10 rows, REQUIREMENTS and parts_qualification is labelled in its sentence, row, bullet or section
heading. That covers the EN timing and chatter, hold-up, cold-screen, Q122 drive, fire budget, plate model, thermal, ESD,
gate fight and port lead.

Three borderline places are optional:
- the change-record quotes at M3_R10:66 and STATUS:44;
- FMEA:52–53, the conditional "within 36 ms";
- M3_R10:407, the explicit hypothetical "0.9–1.8 A if the rail held 3.3 V".

**Status claims.** Narrowing them alone is not enough, because the figures still violate §2.5. Labelling the figures alone
does not make them true either, because the round 28 pass did not label these places. Do both: label every place, and
reword the four claims to say that the round 29 pass finished the sweep.

### R29-TRI-02: the partial-tolerance sweep

Recomputed with the source model (238.6 Ω, Ciss 2.25 nF): 47.8 / 53.0 / 58.3 µs at C126 −10 % / nominal / +10 %. The places
are `r10_sch_check.py:366` (the binding note), M3_R10:1095, FMEA:39 and R10_VALIDATION:2561.

Fix: "about 47–58 µs over C126's ±10 % (53 µs nominal; Calculation, driver resistances Inference)". Then regenerate the
note and pin the new phrase.

No other partial-tolerance range turned up:
- C87 0.72–1.27×, C120's maximum, the LSI range, the PA6 window and R84 each cover their full range.
- The 0.218 / 0.104 V pull-up bounds are nominal-resistor figures, already ruled (R28-POWER obs 2, R19-DOC-05).

### R29-TRI-03: tail allocation

Reproduced with fit_check on a copy of the board with the project kilib: 27 tails, J440.1–.4 included, minimum 7.558359 mm.

Fix: rewrite R10_VALIDATION:2923–2924 and delete the sentence at :2928.

The "plate model not re-run" lines are true: the plate model is optional and outside check.sh.

### R29-TRI-04: LS120 hot end

MLT-5020 p2 item 6 gives operating −20…+70 °C (storage +85 °C). With the records' own +10–22 K board rise (an Inference),
LS120 sits at:
- 80–92 °C in a 70 °C bay;
- 65–77 °C at the 55 °C interim limit.

Two parts are rated below 85 °C at the hot end:
- LS120 (+70 °C);
- J3 (+80 °C), which is disclosed as unmated in flight and not counted.

Places: REQUIREMENTS:94, M3_R10:471–475, ORDERING:608, owner row 33 (R10_VALIDATION:2405) and parts_qualification:40 / :43.

Fix:
- name LS120 as a +70 °C part;
- add "LS120 ≤ 70 °C" to the chamber-test pass criterion;
- either an interim limit of about 48 °C bay air for the buzzer, or an owner row accepting the buzzer as best-effort.

### R29-TRI-05: unpinned D-R28-02 … -04 qualifiers

The pin at `test_r10_check.py:452` stops before the label, and no rejected form covers the unlabelled text. I checked this
with an in-memory seed against the 55 pinned and 38 rejected phrases.

Other D-R28 additions with no pin; the fix pins them all:
- (a) GAP-5's gate-discharge Inference clause;
- (b) chatter's "5.71 V point … inferred";
- (c) rule 8's "loads are the budget's allocations, and C84 has no cold-capacitance factor";
- (d) obligation 15's reason text;
- (e) rule 4's "before coating, with PC1 high and a dummy load in J121", "against Q120's source at R120.1", the
  R23-SAFETY-05 criterion and the VSD citation;
- (f) the port map's "junction ≤ 125 C at the 70 C bay".

## Root-flagged observations

- **Power: 6 V open pack, four stalls, 4.39 V.** Observation. The 6 V pack is below the REQUIREMENTS Pack-row floor
  (≥ 7.4 V resting at launch). That row's four-stall requirement is met at 5.881 V. The stall-input sentence states a
  shedding policy, and its own paragraph says that no all-load guarantee exists at that corner.
- **Parts: "$102.05 plus fixed fees".** Observation. The row is built on the target basis ($85.26 + $16.79), as
  R10_VALIDATION:2994 says. On the minimum-purchase basis the figure would be $102.59, which "about" covers. This is table
  composition, not a false figure.

## Other observations

All 139 observations stay observations; the reasons are in the JSON. Four are merged into real errors: safety obs 12 into
TRI-02, and gate obs 3–5 into TRI-05 as siblings.

Power obs 2 (1.128 against a re-solved 1.12747 A) cannot be shown to be the records' error. The triage's own
reconstruction of that model does not reproduce the budget's normal four-stall current either, and both values clear
1.125 A.
