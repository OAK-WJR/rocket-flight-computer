# R10 round 29 fix pass: docs lane (2026-11-02)

Brief: `.supervisor/r29_fix_docs_brief.md`. Base commit `09a564e`, board `a0ec075e…` (unchanged). Inputs: the triage
`round29_triage.md` / `.json` (R29-TRI-01 … -05, `all_places`, wording, borderline places), the CAD lane's decisions
D-R29-01 / -02 in `R10_DECISIONS.md` its hand-back `round29_fix_cad.md` / `.json`, and the MLT-5020 sheet (cached
`.supervisor/r14_parts_pdf/buzzer.pdf`: p2 item 6, operating −20…+70 °C; item 7, storage −30…+85 °C).

**Files edited (docs lane only):** AGENTS.md (outside §2), STATUS.md, docs/M3_R10.md, docs/FMEA_REDUNDANCY.md,
docs/REQUIREMENTS.md, docs/ORDERING.md, docs/R10_VEHICLE_HANDOFF.md, docs/R10_VALIDATION.md and
`parts_qualification.md`. AVA_LAYOUT.md needed no change.

**Constraints kept:**
- AGENTS §2 byte-identical to HEAD (md5 `e3bdcdaa37e08ca027ab2f80fad0f2e7` before and after);
- no generator, test, decision-record, CAD or git change;
- no local absolute paths added (0 in the diff);
- links: 172 relative links and anchors in the nine edited files, 0 bad (new anchors `#round-29-ten-lenses-on-committed-09a564e`, `#round-29-fix-pass` resolve).

## Items

### R29-TRI-01 (Major): AGENTS §2.5

Every `all_places` entry, with the triage's wording:

| Place | Before → after |
|---|---|
| FMEA:37 H-6 (c) | "about 9.6 V (Calculation, against EN's 6.5 V …)" → "about 9.6 V, against EN's 6.5 V absolute maximum (Calculation / Inference: a full transfer of the 150 pF / 8 kV charge into C87 is assumed, and the 9.6 V uses C87's 0.72 × minimum, whose ≤ 6 % X7R DC-bias part is an Inference, D-R19-10)" |
| REQUIREMENTS:64 F9 | The unclamped sentence gains the same label; "(R23-SAFETY-06, Calculation)" → "(R23-SAFETY-06, Calculation / Inference)"; outcome (c) gains "(Calculation / Inference, as above)" |
| FMEA:38 I-5 | "991 microstrain at 100 g, plate model" + ", Calculation / Inference" |
| R10_VALIDATION §2 | After the fire currents: "Calculation / Inference: Q124's inherited hot factor is an Inference, and the FET, hot R134, harness, contact and converter-load figures are unmeasured allowances" |
| R10_VALIDATION §5 | "calculated 34.853 ms" → "34.853 ms (Calculation on allocations / Inference: the 0.2 / 0.5 / 1.5 ms allocations need bench tests, and the gate-discharge model's 0.4 V off criterion and hot gate charge are inferred)" |
| Owner row 7 | Title "… are calculations on allocations and inferred models"; the 34.853 ms guard allocation carries the same label |
| Owner row 32 | "(C421 at 133 g; plate model, Calculation / Inference; R25-TRI-10)" |
| M3_R10 gate nets (was :418) | "or 3.3 V directly; Calculation / Inference: that a hard bridge holds PE4's net at 3.3 V against its low driver is an Inference" |
| STATUS round 28 entry (:19, :26) and R10_VALIDATION round 28 fix pass | "Calculations on the budget model" → "Calculations / Inferences on the budget model (stall input, parts_qualification)"; the four-stall bullet gains "Calculation / Inference on the budget model's stall input" |
| Rule 3 time constant | Under TRI-02 (below), with "driver resistances Inference" |

**The four status claims**, each reworded to claim only what is true:
- AGENTS:32: round 28 "labelled the inferred-input figures it found"; a round 29 sentence says its fix pass labelled every place the triage listed and those its own sweep found.
- M3_R10:32–34 (summary): the same, with the round 29 paragraph.
- M3_R10:182 (review-status row): "the inferred-input figures it found labelled (round 29 found more, R29-TRI-01)".
- STATUS:18 (round 28 entry): "It labelled the … figures it found …; round 29 found more such places, and four status lines (this one among them) that claimed all were labelled (R29-TRI-01), which the round 29 fix pass labelled and corrected."
- Also annotated, same class: R10_VALIDATION's R28-TRI-09 row ("Class sweep … are now labelled"): "Round 29 found further places that this sweep had missed (R29-TRI-01); the round 29 fix pass labelled them".

**Borderline places (all done):**
- M3_R10:66 (round 26 change row): the chatter figures and rule 8's corner labelled Calculation / Inference (C87's X7R bias allowance and the fire budget's hot Q124 factor).
- STATUS round 26 entry (was :44): the same label on 5.71 V / 8.1 ms / 7.50 ms / 19.7 %.
- FMEA:52–53 (GAP-5): "fault current ends within 36 ms … (34.853 ms; Calculation on allocations / Inference: …)".
- M3_R10:407: "(about 0.9–1.8 A if the rail held 3.3 V; Calculation / Inference, as FMEA I-5)".

**Own sweep.** A label scanner over the current text of AGENTS, STATUS (current block), M3_R10, FMEA, REQUIREMENTS,
ORDERING, the handoff, R10_VALIDATION (owner rows and §1–§13) and `parts_qualification.md` (every "Calculation" not
followed by "/ Inference" and with no Inference word in its sentence), then each hit read in context; plus targeted greps
for "calculated", the plate model, 34.853 ms / 36 ms, 9.6 V, 1.279 / 1.278747 / 1.540851 A, 123.9 °C, the hold-up
figures, 4.74 V / 31.9 ms and 5.881 / 4.388 V. Three more places labelled:
1. M3_R10 Power, EN switch-network paragraph: "Calculation with TPS25947 EN thresholds" → "Calculation / Inference (C87's X7R bias loss, below) with …" (the paragraph's figures use C87's 0.72–1.27×).
2. FMEA I-2 / H-2, gate nets to 3V3: "one to PYRO1_GATE puts 3.3 V on the gate directly (Calculation)" → "(Calculation / Inference: the 3.23 V rests on the hard-bridge Inference above)".
3. R10_VALIDATION §1, the same row: "fires an enabled match by itself (Calculation)" → the same label.

**Checked and left as Calculation** (pure arithmetic on component values, datasheet figures or stated hypotheticals, as
round 28 ruled): the EN divider 2.03 / 2.06 V; the J440 chafe EN 1.87 / 1.28 V; D402's 5.7 mV; the bench-ramp window;
the EN-leakage hypotheticals 5.55 / 6.49 / 7.43 V and 4.08 µA; Q122's 7.1 µs; R134's 22–29 W; the off-state 0.218 V;
the C84 capacitance pass value; the USB-only allocations; the U401 FB-open 5.2–5.55 V; the bridge cold readings in §1;
the leak thresholds 0.20–0.52 / 1.8–2.0 MΩ; the 1.810 A camera-short sum; the 2.7 mA idle-TX figure (its sentence
names the unmeasured input); geometry figures. Not changed: R10_VALIDATION §1's "time constant about 47 µs with C126"
for a hard 3V3 bridge is the nominal for that case (Thevenin 220 Ω ∥ 10 kΩ = 215.3 Ω, 222.25 nF → 47.8 µs), a
different source resistance from rule 3's 238.6 Ω, so it is not the TRI-02 error. Historical sections (R10_VALIDATION
"Historical round10 …", round records, change tables of earlier rounds other than the borderline ones) were not relabelled.

### R29-TRI-02 (docs places)

M3_R10 rule 3 (was :1095), FMEA I-2 / H-2 (:39) and R10_VALIDATION §1 (was :2561): "the gate time constant is 47–53
µs" → "about 47–58 µs over C126's ±10 % (53 µs nominal; Calculation, driver resistances Inference)", the CAD lane's
generated wording (D-R29-01).

### R29-TRI-03

R10_VALIDATION §8: "all 23 tails of the seven earlier terminals" → "all 27 tails of the eight terminals (J440's since
its addition)"; "Minimum tail/bore clearance 7.558359 mm (unchanged on `a0ec075e…`)"; the sentence "J440's four tails
were not added to that tail allocation (not re-run)." deleted. The plate-model "not re-run" lines are true and stay.

### R29-TRI-04: LS120 hot end

LS120 named as a +70 °C part (MLT-5020 p2 item 6) and "LS120 ≤ 70 °C (thermocouple on LS120)" added to the chamber-test
pass criterion in: REQUIREMENTS Temperature row; M3_R10 "Hot-end temperature"; ORDERING 8.3 "Board temperature at the
pad load"; owner row 33; `parts_qualification.md` (round 23 notes, a "Round 29" sentence, and the LS120 cold-end
bullet). Root's decision recorded: at a 70 °C bay LS120 is out of rating (about 80–92 °C at the pad load; 65–77 °C at
the 55 °C interim limit; Inference); buzzer annunciation is best-effort when bay air is above about 48 °C (70 °C − 22 K;
Inference); recovery and logging do not depend on the buzzer. **New owner row 36** (Accept table, after row 23), with
the respin option of a +85 °C buzzer on the same land. AGENTS §1 buzzer row (outside §2) points to it.

### Round 29 records

- **STATUS:** status line (round 29 sentence; closing pair rounds 30 and 31); new "Round 29 review and fix pass" entry
  (raw 0 / 1 / 4 by lens, triage 5 real errors (1 Major, 4 Minor), 139 observations, 0 not reproducible, none on the
  board; the five fixes; software tests, DRC / CAD gate, simulation and physical tests reported separately); the round
  28 entry's physical-tests line now says round 29 reviewed the board.
- **R10_VALIDATION:** "Where R10 stands" and "Latest review"; the round table (row 29 filled, rows 30 / 31 planned);
  new sections "Round 29: ten lenses on committed `09a564e`" (index, five dispositions, observations) and "Round 29 fix
  pass"; owner-table intro; owner row 20 (229 decisions, 103 after the ledger, rounds 30 and 31); "Decisions after the
  ledger" heading and rows D-R29-01 / -02; inventory basis (103 IDs); §12 (229 through D-R29-02); owner rows 33 and 36.
- **M3_R10:** summary; review-status rows 29, 29 fix pass, 30 and 31; the closing-pair paragraph; decision counts (two
  places, 229 through D-R29-02); the "Current state" rounds sentence; a "Round 29 fix pass" checks bullet.
- **AGENTS, ORDERING 8, the handoff, REQUIREMENTS (R10 status), `parts_qualification.md`:** round 29 sentence; closing
  pair rounds 30 and 31.

## Binding

Bound to the CAD lane's hand-back (`round29_fix_cad.md` / `.json`), as root relayed it:
- PCB `a0ec075e…` unchanged; one complete build (1668 s) reproduced it and ended in `tools/check.sh` exit 0 (the CAD
  lane's run; this lane claims no check result of its own);
- binding note `c5cd0fa313d3e973bf0542e806f82ae1bfea357943ec49d3c84e522449836cca` (was `30796f5e…`), current in
  R10_VALIDATION's round 29 fix pass, STATUS's round 29 entry and the M3_R10 checks bullet. In STATUS's and M3_R10's
  round 28 records and R10_VALIDATION's round 27 and 28 fix passes, `30796f5e…` stays as round 28 history, marked
  "`c5cd0fa3…` since the round 29 fix pass";
- decisions D-R29-01 / -02; 229 unique D IDs through D-R29-02, 103 after the ledger;
- tests: R10 268 (6 NumPy skips), route 72, fab_validation 34, fit 33, paste 16, shell 11, r10_parts 5, NumPy 6;
- fab outputs changed only in their creation dates (BOM, owner BOM, CPL and paste byte-identical);
- the placeholders in STATUS's round 29 entry and R10_VALIDATION's round 29 fix pass are filled, and a "Round 29 fix
  pass" checks bullet is added to M3_R10 "Software and CAD checks".

## Completeness sweep

`git grep -n` over docs/, STATUS.md, AGENTS.md and `m3_design/assembly_review/sources/` for the replaced phrases
(`47–53`, `47-53`, `calculated 34.853`, `23 tails`, `four tails were not added`, `Calculations on the budget`,
`labelled every model figure`, `every model figure resting`, `85 °C part ≤ 85 °C`, `85 °C-rated part ≤ 85 °C`,
`9.6 V (Calculation,`, `R23-SAFETY-06, Calculation)`, `directly; Calculation)`, `are now labelled Calculation /
Inference`, `guard are calculations |`, `29 and 30`):

| Residual | Why it stays |
|---|---|
| `47–53` in STATUS's and R10_VALIDATION's round 29 records, R10_DECISIONS D-R29-01 / -02, `round28_fix_cad.*` | Quotes of the error, the rejected test form, or immutable review records |
| `47–53` in ORDERING:152 | Unrelated: U4 / U5 at y 47–53 mm (R9 section) |
| `47-53` in `round23_safety_severity_check.json` | Immutable source record |
| `23 tails` in R10_VALIDATION's R13-m08 row and R29-TRI-03 row, R10_DECISIONS:2073, round 13–17 review records | History (seven terminals then) or the error quoted |
| `85 °C part ≤ 85 °C` / `85 °C-rated part ≤ 85 °C` in REQUIREMENTS, M3_R10, ORDERING, owner row 33 | Each now continues "and LS120 ≤ 70 °C (thermocouple on LS120)" |
| `are now labelled Calculation / Inference` in the R28-TRI-09 row | Annotated with round 29's finding |
| Others | 0 hits |

## Not done or not verified

- No board, generator, test, decision-record or git change by this lane. The relabelled figures keep their values; this
  lane re-ran no model (the 47.8 / 53.0 / 58.3 µs and LS120 figures are the triage's and D-R29-01's, checked by hand).
- No physical test. Rounds 30 and 31 are planned on `a0ec075e…`.
