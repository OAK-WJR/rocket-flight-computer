# R10 round 25 — requirements lens (Claude)

Target commit `c4bb56b`; board SHA-256 `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` before and after.
Totals (real errors only): **0 Critical / 0 Major / 3 Minor.** Probes: `.supervisor/r25_requirements/`.

## Findings

**R25-REQUIREMENTS-01 (calc, Minor). The 18 % chatter pass line rests on the averaged trip fraction.**
F6 (and ORDERING 8.3, R10_VEHICLE_HANDOFF, R10_VALIDATION, AGENTS) set the pass line at 18 % because "the worst-case
trip is about 20 % at 5.73 V". The averaged model (20.0 / 24.4 % at 5.73 / 6.0 V, which reproduces) is only the limit
for very short drop-outs. Each drop-out of length d pulls EN about (V/R81 + I)·d/C below the mean. At the records' own
worst corner (R ±1 %, C87 0.72 × 220 nF, 0.1 µA + 50 nA sink, VUVLO(F) 1.116 V; tau 35.8 ms closed / 47.0 ms open),
the periodic trip fraction is:
- at 5.73 V: 17.7 % for 2 ms drop-outs, 13.6 % for 5 ms and 5.8 % for 8 ms;
- at 6.0 V: 18.6 % for 5 ms and 13.7 % for 8 ms.

A time-domain run from the closed steady state turns U9 off with trains that pass both numeric criteria:
- at 6.0 V: 8 ms open every 50 ms (16 % of any 100 ms window), or 9.5 ms every 92 ms (17.5 %);
- at 5.96 V: 8 ms every 50–60 ms.

The functional check runs on one nominal bench board, whose trip fraction is 26–30 %, so it does not cover this.
Fix: pass on the recorded contact waveform replayed through the worst-case EN model (EN stays > 1.116 V at 5.73 V), or
give the allowed fraction against the longest drop-out, or run the functional test with C87 at 150 nF. Restate
"about 20 %" as the d → 0 limit.

**R25-REQUIREMENTS-02 (calc, Minor). Post-trip hold-up is computed from 5.3 V, outside the stated trip window.**
PA6 = VLOGIC × 10k / 110k (R60 / R61), so 0.44–0.47 V gives VLOGIC 4.84–5.17 V. C84 sits on VLOGIC. The records'
load powers are 13.06–11.25 W with all ports on and 4.66–4.30 W with the camera off / shed. With these:
- from the window, the hold-up is 0.104–0.164 ms (all ports) and 0.29–0.43 ms (camera off / shed);
- the records quote 0.157–0.182 ms and 0.44–0.48 ms, which is 11–52 % high;
- the fraction of the break-to-3.8 V figure is 0.22–0.30, not "about a third".

Affected: F6, M3_R10 (lines 616 and 1017), ORDERING 674, and R10_VALIDATION rows 5 and 25. Fix: requote these over
the window.

**R25-REQUIREMENTS-03 (doc, Minor). The Pack row's U9 turn-off corner is stale.**
The Operating-assumptions Pack row gives 4.778 / 4.811 / 4.851 V (25 / 70 / 125 °C). Those are the corners without
D402. With D402's 50 nA they are 4.802 / 4.835 / 4.875 V, and F6 in the same file already says 4.80 V (D-R24-19).
Fix: update the row.

## Fix verification
| Item | Verdict |
|---|---|
| D-R24-19 EN figures (10.3 / 20.1 / 26.0, 8.2 / 6.3 ms, 5.96 V, 30–130 ms; ramp 4.72–5.25 / 4.29–4.80 V) | Confirmed (Pack row missed: -03) |
| R24-TRI-02 18 % line in the docs | Partly (the text is present; its physics basis is -01) |
| R24-TRI-08 P3 98–163 g | Confirmed |
| R24-TRI-09 P2 J2.1 3.880 / J2.3 3.987 mm | Confirmed (pcbnew) |
| D-R24-11 BAT_SW_RETURN set and D402 pose | Confirmed |

## Observations (8, not counted)
EN, ramp and D402 arithmetic reproduce. The F1 35 s recompute is disclosed. F2, F3, F5, F7, F8, P3, Storage, M1, M3
and the board-position stack reproduce. Connector pin maps match. The OVLO trips at 9.63–9.96 V, so a deeply
discharged 3S pack is not blocked; no stated limit is contradicted. Full list in the JSON.

## Limits
This was a read-only review: no check.sh, DRC or route_check run. Bore fit and wire room were left to the mechanics
lens. The X7R allowance and D402's leakage were taken from the records.
