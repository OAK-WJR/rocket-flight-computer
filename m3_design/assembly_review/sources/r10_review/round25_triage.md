# R10 round 25 triage (verifier)

Target: commit `c4bb56b`, board SHA-256 `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f`
(checked before and after; unchanged). Read-only; probes in `.supervisor/r25_triage/`. The definition of a real error is
the one in the round 25 review brief.

**Totals.** I reproduced all 14 raw lens findings, from safety 3, power 4, MCU 1, mechanics 2, requirements 3 and docs
binding 1; routing, gate, parts and manufacturing had none. They merge into 9 real errors. I promoted one observation
(mechanics observation 1, now R25-TRI-10), which makes **10 real errors: 0 Critical, 0 Major, 10 Minor**. None of them
changes the board copper or placement. 72 lens observations stay observations, and 0 findings were not reproducible.

## Real errors

| ID | Merged | Kind | Title (key number) | Board change |
|---|---|---|---|---|
| R25-TRI-01 | POWER-03, REQUIREMENTS-01, safety obs 9 | calc | The J400 chatter rule (< 10 ms per drop-out, < 18 % open in any 100 ms window) passes trains that turn a worst-case U9 off: 8 ms every 50 ms at 6.0 V (16 %) gives EN 1.095 V; 3 × 4 ms with 0.2 ms closures (12 %) gives EN 1.028 V at 5.73 V | no |
| R25-TRI-02 | SAFETY-02, POWER-02, MCU-01, REQUIREMENTS-02 | calc | The post-trip hold-up is computed from 5.3 V, outside the stated trip window of 4.84–5.17 V. Over the window it is 0.103–0.164 ms (all ports on) and 0.291–0.430 ms (camera off / shed), not 0.157–0.182 / 0.44–0.48 ms; the fraction is 0.22–0.31, not "about a third" | no |
| R25-TRI-03 | POWER-01 | doc | REQUIREMENTS F6 still says "100–220 µF would do", although the records say it was struck. From the trip, 100–220 µF gives 0.03–0.12 ms | no |
| R25-TRI-04 | POWER-04 | calc | The OVLO corner of 9.97 V omits IOVLKG ±0.1 µA. The highest trip is 10.18 V | no (generator re-run) |
| R25-TRI-05 | SAFETY-01 | doc | FMEA H-6 keeps the old bench-ramp window (4.5–4.8 / 4.9–5.2 V); the correct window is 4.29–4.80 / 4.72–5.25 V | no |
| R25-TRI-06 | SAFETY-03, DOCS_BINDING-01, safety obs 7 | doc | FMEA line 86 and R10_VALIDATION line 2329 name `1407e850…` as the current board | no |
| R25-TRI-07 | REQUIREMENTS-03 | doc | The REQUIREMENTS Pack row gives the U9 turn-off corner as 4.778 / 4.811 / 4.851 V, without D402. With D402 it is 4.802 / 4.835 / 4.875 V | no |
| R25-TRI-08 | MECHANICS-01 | doc | M3_R10 line 874 and R10_VALIDATION line 2709 say R150–R155 are "still missing" from STRAIN_PARTS. They are in it (plate_model.py line 40) | no |
| R25-TRI-09 | MECHANICS-02 | doc | ORDERING says "plate ≤ 0.8 mm keeps h + t < 5.3 mm", but 4.5 + 0.8 = 5.3 mm. This conflicts with the strict < 5.3 mm limit | no |
| R25-TRI-10 | mechanics obs 1 (promoted) | doc | R10_VALIDATION row 32 has C421 at 125 g, while ORDERING gives 133 g, and calls 98–163 g "above" 125 g | no |

### R25-TRI-01: the chatter bench criterion

My own model (`chatter.py`) uses the D-R24-19 corner: R80 / R165 +1 %, R81 −1 %, C87 0.72 × 220 nF, U9 sinking 0.1 µA,
D402 50 nA and VUVLO(F) 1.116 V. A search over every ± corner confirms that this corner is the worst. The model reproduces
the records: 8.204 / 10.345 ms single drop-out at 5.73 / 6.0 V, a 5.96 V pack floor, EN 1.4014 V, and averaged trip
fractions of 20.01 / 24.41 %.

**Periodic trip fraction against drop-out length:**

| Pack | 0.1 ms | 1 ms | 2 ms | 4 ms | 6 ms | 8 ms | 9.9 ms |
|---|---|---|---|---|---|---|---|
| 5.73 V | 19.9 % | 18.9 % | 17.7 % | 15.1 % | 11.8 % | 5.8 % | trips even as a single drop-out |
| 6.0 V | 24.3 % | 23.4 % | 22.3 % | 20.0 % | 17.2 % | 13.7 % | 8.3 % |

So the 20.0 / 24.4 % figures are only the d → 0 limit.

**The proposed replacements fail too:**
- Clustered drop-outs defeat any rule keyed to the longest single drop-out, which is why I reject REQUIREMENTS-01 option 2.
  For example, 3 × 4 ms at 12 % trips at both 5.73 and 6.0 V.
- A nominal board with C87 at 150 nF (option 3) still tolerates 25.4 / 21.3 % at 0.5 / 4 ms, against 19.5 / 15.1 % on the
  worst-case board.
- The functional "U9 stays on" run tests only the bench board.

**Chosen criterion (correct at the worst corner and executable from the contact record the test already takes):**
- Record the J400 contact state at ≥ 10 kS/s under flight-level vibration.
- Pass only if the open time in every sliding 100 ms window is **< 7 ms**, and U9 stays on for the whole run at 5.73 V.
- The worst-case limit is 7.63 ms at 5.73 V (9.59 ms at 6.0 V, 5.87 ms at 5.5 V). An adversarial search over 4000 trains
  that respect the window gave EN ≥ 1.1173 V (`window_rule.py`).

This one rule replaces both the < 18 % line and the < 10 ms rule. A switch that fails it may still pass on a replay of its
recorded waveform through the worst-corner model (option 1). The trip-fraction table is guidance only. Raising C87 (BOM
only) remains the owner's alternative.

**Every place the rule is quoted:**
- AGENTS §1 power row
- STATUS lines 11 and 16
- REQUIREMENTS F6 (line 60); F4 (line 58) and line 106 cite the test and the immunity
- M3_R10 lines 260 and 577–578
- ORDERING 8.3 line 617
- R10_VEHICLE_HANDOFF lines 67–68
- R10_VALIDATION lines 1906, 2073, 2150 (row 21) and 2435; line 1686 is history
- The chatter obligation in `m3_design/r10_sch_check.py` line 295, which generates the binding note and is pinned in `tools/test_r10_check.py` at about lines 394–400
- D-R24-19 (history: record the change as a new D-R25 decision)

### R25-TRI-04: the generator must be re-run

1. Edit `m3_design/r10_parts.py`: the comment at lines 378–379, `peak(9.97, …)` and the `9V97_*` keys at line 501, and the
   9.97 V term in the U9 bound at lines 520–521.
2. Re-run `r10_parts.py --budget-only` (r10_build.sh line 55) to regenerate `parts_budget.json`. `tools/check.sh` line 58
   (`r10_parts.py --check`) pins the file and fails it as stale until then.
3. The assert at r10_parts.py:626 still holds: the U9 bound becomes about 3.74386 A, below the 3.946 A minimum. The buck
   peak becomes about 3.657 / 3.627 A.
4. Update `parts_qualification.md` lines 137 and 639. Line 639 sits in a superseded port-switch paragraph, which may be
   labelled as history.

### Other fixes (text or generated text only)

- **TRI-02:** quote 0.10–0.16 / 0.29–0.43 ms, "from VLOGIC 4.84–5.17 V", in:
  - M3_R10 line 616 (strike "about 5.3 V") and lines 1017–1018;
  - REQUIREMENTS F6;
  - ORDERING line 674;
  - R10_VALIDATION rows 5 and 25 ("about a fifth to a third");
  - rule 8 in `r10_sch_check.py` line 322, then regenerate the binding note.
- **TRI-03:** strike the F6 sentence.
- **TRI-05:** FMEA line 36 window becomes 4.29–4.80 / 4.72–5.25 V.
- **TRI-06:** change the two hashes to `92c3ad59…`.
- **TRI-07:** Pack row figures become 4.802 / 4.835 / 4.875 V.
- **TRI-08:** "R150–R155 were added in the round 19 gate pass".
- **TRI-09:** either "plate < 0.8 mm", or a ≤ 5.3 mm limit inside the exact 5.365 mm.
- **TRI-10:** row 32 reads "can exceed the 125 g at which … C431 (C421 at 133 g)".

## Observations

All 72 are listed in the JSON. The ones I re-examined against the records:
- **Safety 2:** the Q124 gap is in a disclosed class.
- **Safety 5:** a persistent PA6 trip on a good pack needs a pack outside the stated range, and the prescribed action is
  harmless.
- **Safety 11:** I measured 1.041135 / 0.341344 mm. That is within KiCad's 5 µm arc-approximation error, and nothing depends
  on it.
- **Power 4:** "≤ 2.06 V with 1 % parts" is scoped to the parts.
- **Power 9:** the "All three ports shorted" figures are superseded by the file header.
- **MCU 10:** the via-pair hole edge is 0.266 mm, at least the 0.25 mm rule.
- **Gate 1:** 0.173 mm violates no rule, so it is not a gate miss.
- **Mechanics 2 and 7:** the contact list is not stated as exhaustive, and "not re-run" is true.
- **Routing 1 and 4:** review-only counts; the final-board deviation list is not yet due.

Everything else is a confirmation or a disclosed item. Round 24's observations stand.

## Not reproducible

None.
