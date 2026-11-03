# R10 round 34 triage

Target: commit `c2a11fd`, board `a0ec075e…` (SHA-256 identical before and after). The ten lenses reported 0 real errors.
I re-checked every observation and the root's flags independently.

**Totals: 0 Critical / 0 Major / 1 Minor real error. No board change. 16 observation groups, 0 not reproducible.**
Because of R34-TRI-01, round 34 is not clean. The fix is text only, so it does not restart the board count, but round 34
cannot be the first of the two clean rounds.

## Real error

### R34-TRI-01 (doc, Minor, board_change false). Pointer to the hot-plug results names a stale file
- `parts_qualification.md:1061-1062` says: "the current hot-plug results are in `hotplug.md` and `hotplug_results.json`".
  The round 28 audit A added this sentence (`09a564e`), and no triage has ruled on it since.
- `hotplug.md` was last changed in round 11 (`d57b216`) and holds no result for `a0ec075e…`. Its top section, "Round-11
  fix-pass target", is the only one not labelled Historical; lines 40, 47, 62 and 67 are. It says the inputs and results
  bind `0ad0135c…`, with input digest `7528385…`.
- The two sources disagree:

  | Figure | `hotplug.md` (round 11, `0ad0135c…`) | Current |
  |---|---|---|
  | Falling slew | 8.991477 V/µs | 8.994764 V/µs |
  | Rising slew | 5.091053 V/µs | 5.087664 V/µs |
  | Retained output | 1616.123714 µF / 5.877715 V | 1643.90 µF / 5.914 V |
  | Input digest | `7528385…` | `f4d1b57d…` |

  The current slews are from the committed `hotplug_inputs.json`, bound to `a0ec075e…`, and the rows of
  `hotplug_results.json`, which I recomputed. The current retained-output figures are in M3_R10:346-348 / 743.
- Only the −14.807 V minimum and the R166 579.049 W / 2.979 mJ agree.
- **All places:**
  - `parts_qualification.md:1061-1062`;
  - `hotplug.md:3-22`, the unlabelled top section.

  The other mentions of `hotplug.md` are dated decision or verification records: R10_DECISIONS:893 / 906,
  owner_hotplug_reverification:51 and r10_hotplug.py:5 (method).
- **Fix (text only):**
  - `parts_qualification.md:1061`: point to `hotplug_results.json` and M3_R10 "Current state" for the current figures;
    `hotplug.md` keeps the model, the sources, the limitations and the round-11 run.
  - `hotplug.md:3`: retitle the section "Historical round-11 fix-pass target …", and add a one-line pointer to the
    current bound inputs and results.

## Root flags
- **M3_R10:1202 "R121 × C120 = 10 ms": observation.**
  - 10 kΩ × 1 µF (BOM) is exactly the product the sentence names.
  - The value lies inside the calculated envelope: Thevenin (10 k ∥ 50 k) × 1 µF = 8.33 ms nominal, and
    `parts_budget.json` tau_max is 10.75 ms.
  - The conclusion, "turn on within a few ms … well before apogee", holds.
  - The sentence sits in a not-adopted owner option. Round 30 saw it and did not promote it.
- **U9 IN-to-OUT 0.200 mm: observation.** No record claims that owner row 2 or the §1 table is complete, and per-flight
  step 2 detects the bridge.
- **PYRO1_OUT-BUZZ_G 0.510 mm: observation.** §1's surface inventory covers pairs within 0.5 mm, and the table is not
  claimed complete.
- **R10_VALIDATION:2954, R101 B(34.0,42.0): observation.** Measured with pcbnew:
  - The list gives each via's coordinate; the R86, R89, R91 and R401 vias coincide with their parts.
  - R101 is at B(34.0,42.25). Its via is midway between the pads, 0.175 / 0.175 mm from each.
  - The "five remain" count is true. Rounds 29 and 31 ruled the same way.
- **parts_qualification:655, SLVS841F eq. 1: observation.** Revision F is a real revision; line 1007 gives all three
  expressions as its eq. 1. The constants match Rev G. Round 32 ruled the same way.
- **hotplug.md's header:** promoted as R34-TRI-01, through the current pointer that names the file.

## Other observations
The remaining observations in all ten lenses are reproductions, fail-safe bridges, already-ruled classes, or the stale
session-context copy of AGENTS. The committed AGENTS.md has $85.26, 12:44:13Z and 5.71 V, which match
`cost_check.json`. The JSON gives one line per group.

## Spot checks
All 13 reproduce:
1. Q122 gate 0.218 V.
2. EN divider 2.032 V.
3. EN tau 50.0 ms; turn-on at 7.4 V 55.5 ms.
4. IWDG 28.571–32.653 ms.
5. GAP-5 34.853 ms.
6. Port rails 5.456 / 4.792 V.
7. Cost $85.26 / $102.05.
8. Wire room 5.003 mm.
9. Cold CONT 99.36 / 146.2 mV.
10. R167 7.1 weeks.
11. C120 / R121 / R119 / R120 values.
12. The five under-body vias.
13. The `hotplug_results.json` extrema.

Probe scripts: `.supervisor/r34_triage/`.
