# Round 25 power lens (Claude)

Target `c4bb56b`, board `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` (verified before and after).
Totals: **0 Critical, 0 Major, 4 Minor.** Probe files: `.supervisor/r25_power/`.

## Findings

### R25-POWER-01 (doc, Minor): REQUIREMENTS F6 still says "100–220 µF would do"
- F6 (REQUIREMENTS line 60) still reads: "If that is about 0.2 ms (Inference), 100–220 µF would do and C84 could be a
  reflow-rated part".
- R10_VALIDATION's R23-POWER-01 row (line 1905) records F6 as fixed, with this sentence struck. Owner row 25 and M3_R10
  line 616 also say it is struck.
- Calculation, from the records' own 5.3 V trip at the all-ports load (11.25–13.06 W): 100 µF gives 0.052–0.061 ms and
  220 µF gives 0.115–0.134 ms. Both are below 0.2 ms.
- **Fix:** strike the sentence in F6, using the M3_R10 / row 25 wording.

### R25-POWER-02 (calc, Minor): the post-trip hold-up is computed from 5.3 V, above the stated trip window
- The records give the trip window as VLOGIC 4.8–5.2 V (0.44 / 0.47 V × 11 = 4.84 / 5.17 V). The hold-up "after the
  trip" (0.157–0.182 ms with all ports on, 0.44–0.48 ms with the camera off / shed) starts from 5.3 V.
- It is quoted in M3_R10 lines 616 and 1017–1018, ORDERING 674, REQUIREMENTS F6, R10_VALIDATION rows 5 and 25, and
  binding-note rule 8 (`r10_sch_check.py` line 322).
- Over the window, with the parts_budget loads at 300.8 µF to 3.8 V:
  - all ports on: 0.103–0.164 ms;
  - camera off / shed: 0.29–0.43 ms.
- The quoted shed range lies entirely above the window's range.
- **Fix:** quote 0.10–0.16 ms and 0.29–0.43 ms, taken from the 4.84–5.17 V window, everywhere it appears, and
  regenerate the binding note.

### R25-POWER-03 (calc, Minor): the chatter trip fraction is the fast-chatter limit, not the worst case
- The records call 20.0 / 24.4 % (at 5.73 / 6.0 V) "the worst-case trip": AGENTS, REQUIREMENTS F6, M3_R10 line 260,
  D-R24-19 and the handoff. They set the < 18 % pass line from it.
- The averaged model holds only when each drop-out is much shorter than R81·C87, which is 47 ms at the worst corner.
- An exact piecewise-exponential solution at D-R24-19's worst corner gives the trip fraction as a function of drop-out
  length:

  | Pack | 2 ms | 4 ms | 6 ms | 8 ms | 9.9 ms |
  |---|---|---|---|---|---|
  | 6.0 V | 22.3 % | 20.0 % | 17.2 % | 13.7 % | 8.3 % |
  | 5.73 V | 17.7 % | 15.1 % | | | |

- Counterexample at 6.0 V that passes both bench lines and still trips U9:
  - 8 ms drop-outs every 51 ms (each < 10 ms, at most 16 % open in any 100 ms window);
  - EN falls to 1.098 V, below the 1.116 V falling threshold.
- At 5.96 V, 8 ms drop-outs every 57 ms also trip (EN 1.106 V).
- **Fix:**
  - state the trip fraction against the longest drop-out, and set the pass line from that;
  - or run the measured contact record through the worst-corner EN model;
  - or raise C87 (BOM only).

### R25-POWER-04 (calc, Minor): the OVLO corner "9.97 V, the highest RAW_PROTECTED can reach" omits I_OVLKG
- TI SLVSFC9C p9 gives an OVLO pin leakage of ±0.1 µA. Through R82 ∥ R83 (245.6 kΩ) that moves the trip ±0.20 V. The
  trip is 9.42–10.18 V, not 9.62–9.98 V.
- The same 9.97 V is in `r10_parts.py` lines 378–379, `parts_budget.json` (the 9V97 keys and the R92 basis) and
  parts_qualification line 639.
- The figures built on it move only slightly: the buck's prospective peak goes from 3.645 to 3.657 A, and R92's bleed
  from 3.021 to 3.084 mA. The conclusions do not change.
- **Fix:** use 10.18 V in `r10_parts.py` and regenerate.

## Fix verification

| Change | Measurement | Verdict |
|---|---|---|
| D-R24-05 | BAT_ENABLE via (17.10,82.80): F.Cu 0.200 mm to BAT_FAULT_N, B.Cu 0.350 mm to BAT_OVLO | confirmed |
| D-R24-07 | (32.3,60.1): 0.200 mm to U402.6, 0.210 mm to SERVO4_MCU | confirmed |
| D-R24-08 | (34.5,62.4) 0.150 mm; (30.45,51.4) 0.171 mm; (28.1,59.4) 0.254 mm | confirmed |
| D-R24-09 | R402 / R403 on B.Cu with no via; OUT vias (29.75,11.65) / (29.75,9.95); 4.792 V | confirmed |
| D-R24-10 | Second via (16.6,28.0) on 0.2 mm B.Cu and 0.4 mm In2 links | confirmed |
| D-R24-11 | D402 tap 4.114 mm ahead of R165; GND via (5.15,65.575); EN shift 5.685 mV | confirmed |
| D-R24-17 | C88 on U9.5's axis; POWER_NARROW pieces match; K-power 0 issues; hot-plug inputs equal the live board | confirmed |
| D-R24-18 | BAT_FAULT_N 0.200 / 0.2015 mm from the EN via | confirmed |
| D-R24-19 | Every figure reproduced: drop-out 10.345 / 20.111 / 26.023 ms; 8.204 ms; 6.300 ms; floor 5.956 V; turn-on 30.3–130.3 ms; EN 1.401 V; ramp 4.72–5.25 / 4.29–4.80 V; 20.0 / 24.4 % | confirmed (related errors reported as R25-POWER-02 / -03) |

## Observations (11, not counted)
1. Every D-R24-19 and D-R20-11 figure reproduces to the quoted precision.
2. D402's arithmetic reproduces: 5.685 mV, 5.216 V, 25 nA, 14.3 mV, about 1 µA.
3. PA6 corner: 4.84 V is above 4.80 V, and VLOGIC is below BAT_IN. The divider-tolerance edge (4.75 V) is disclosed.
4. The AGENTS figure "≤ 2.06 V with 1 % parts" excludes EN leakage. With it the figure is 2.086 V, which is immaterial.
5. Hot-plug validation is clean; the 2304 cases match the stated extremes.
6. K-power: 0 issues, and every floor is at or above its IPC-2152 width.
7. The regulator feedback taps sit at the output caps or the regulator, and the nominal rails check.
8. U400's input run (0.4 mm, about 1.94 A) meets IPC-2152, though it is not in POWER_PATHS.
9. The stale port-switch-era short-circuit paragraph in parts_qualification is covered by the file's supersession
   header.
10. The 0.3 mm U9 entries are named, disclosed exceptions.
11. ORDERING 8.3's "U9 stays on" check still screens the board under test.

## Checks executed
- Board hash verified twice.
- EN corner model; periodic chatter simulation; OVLO and hold-up calculations.
- pcbnew read-only dumps and clearances.
- `check_r10.power_paths`.
- `r10_hotplug` extract and validate.
- Datasheet read: SLVSFC9C pp7–9.
- Cross-document text check.

## Coverage limits
- No physical tests.
- Ideal periodic chatter trains.
- The hot-plug model was validated, not re-run.
- The fire path and AGENTS §2 belong to other lenses.
