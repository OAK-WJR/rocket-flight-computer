# R10 round 26: power lens

Target: commit `3d8e845`. Board SHA-256 `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f`, the same
before and after the review. The review was read-only; probes are in `.supervisor/r26_power/`, and the JSON twin is
`round26_power.json`.

**Totals: 0 Critical, 0 Major, 2 Minor.** Both are calculation errors in the generated text and docs. Neither needs a
board change.

## Findings

### R26-POWER-01 (calc, Minor): the quoted adversarial bound is not a bound

**What the records say.** In `r10_sch_check.py` line 295, and so in binding note line 589: "an adversarial search over
4000 trains under 7.62 ms per window kept EN at or above 1.1173 V". The same figure is in:
- REQUIREMENTS F6;
- M3_R10 line 270;
- ORDERING line 617;
- R10_VALIDATION row 21;
- D-R25-01.

**The counter-example.** The train is one 7.6199 ms open block at the end of every 100 ms, starting from the closed
steady state at 5.73 V.
- Every sliding 100 ms window holds 7.6199 ms open, which is under 7.62 ms.
- At the D-R25-01 worst corner, EN falls to 1.13050, then 1.11716, then 1.11629 V, and settles at 1.11623 V. That is
  below 1.1173 V.
- At 7.6 ms, which was the triage search's own budget (76 samples of 0.1 ms), it gives 1.11677 V. So the search missed
  an admissible train inside its own grid.

**Why this train is the worst.** Let O and C be the affine open and closed maps. Then C∘O − O∘C = (1−a)(1−b)(vc−vo) > 0:
moving open time later always lowers EN. Under a sliding-window budget, the latest packing is therefore one block per
100 ms. A further 3000 random admissible trains found nothing lower than this train.

**Impact.** The 7.63 ms limit and the 7 ms pass line both stand. At 7 ms the worst train gives EN 1.1330 V. The error
is the margin: the records claim 1.3 mV, and the real figure is 0.23 mV.

**Fix.** Quote the analytic worst case: 1.1162 V at 7.62 ms and 1.1330 V at 7 ms. Then regenerate the binding note and
update the docs listed above.

### R26-POWER-02 (calc, Minor): the 5.73 V four-stall BAT_IN is stale

**What the records say.** The text calls 5.73 V "the fire budget four-stall BAT_IN". It is the basis of three figures:
- the 8.2 ms single drop-out;
- the 7.63 ms window limit;
- the bench rule "U9 stays on for the whole run at 5.73 V".

**What the budget gives.** The current `parts_budget.json` (`fire_current_GAP1`, four stalls) gives 5.713 V, or 5.711 V
with the typical-hot FETs.
- 5.732 V was the value before D-R19-14: `git show 6628488^`, with other load 12.371 W.
- The AUX allowance raised the other load to 13.064 W.

**Re-run at the current point:**

| Pack | Single drop-out | Window limit | EN at the 7 ms line |
|---|---|---|---|
| 5.713 V | 8.067 ms | 7.503 ms | 1.1295 V |
| 5.711 V | 8.051 ms | 7.488 ms | 1.1291 V |

**Impact.** The quoted figures are 0.13–0.15 ms high, and the bench functional check runs 17–19 mV above the current
worst case. The 7 ms line still holds, with a 0.49 ms margin rather than the stated 0.63 ms. Rule 8's 5.37 V corner was
derived from 5.73 V too.

**Fix.**
- Quote 5.71 V (5.713 / 5.711 V) and the re-derived figures.
- Run the bench at 5.71 V or below.
- Edit `r10_sch_check.py` line 295 and the pins at `tools/test_r10_check.py` lines 399–402, then regenerate the binding
  note.
- Update the docs that quote 5.73 V: AGENTS §1, STATUS, REQUIREMENTS F4 / F6 / line 106, M3_R10, ORDERING, the vehicle
  handoff and R10_VALIDATION.
- Optionally, have `r10_parts.py` export the four-stall point, so that the text cannot drift from the budget again.

## Fix verification

| Change | Measurement | Verdict |
|---|---|---|
| D-R25-01 window rule | 7.629 / 5.871 / 9.594 ms and the trip-fraction table reproduced exactly. The 1.1173 V bound is not one, and the 5.73 V basis is stale | partly (01, 02) |
| D-R25-02 post-trip hold-up | 0.1034–0.1643 / 0.2906–0.4303 ms, fraction 0.223–0.305 | confirmed |
| D-R25-03 OVLO and buck peak | 10.1765 V; 3.6565 / 3.6268 A; U9 bound 3.743861 A < 3.94619 A; R92 3.147 mA | confirmed |
| D-R24-19 EN figures | 10.345 / 20.111 / 26.023 / 8.204 / 6.300 ms; turn-on 30.3–130.3 ms; on 4.723–5.251 V, off 4.288–4.802 V; floor 5.956 V | confirmed |
| D-R24-11 D402 topology | BAT_SW_RETURN = {D402.1, J400.2, R165.1} | confirmed |
| D-R24-17 U9 IN / OUT copper | K-power 0 issues; POWER_NARROW entries match | confirmed |

## Rails checked (observations, not counted)

There are 14 observations in the JSON. In brief:
- **K-power** (run read-only): 0 issues. Every path floor is at or above its IPC-2152 width at a 30 °C rise.
- **Hot-plug:** the input and model digests match the results, and the limits match SLVSFC9C 6.1. The minimum is
  −14.807 V, and with OUT at 5.914 V the −15 V bound holds.
- **Regulator taps:** the values match the budget inputs and the datasheet VFB and IFB.
- **PA6 window:** with 1 % parts it reaches down to 4.753 V. The records disclose it as still to be qualified.
- **5.5 V:** the 7 ms rule fails there, but 5.5 V is only a sensitivity point.

## Coverage limits

- There was no physical test.
- The fill necks and the hot-plug sweep were not re-run.
- The 5.37 V corner was not re-derived.
