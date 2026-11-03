# R10 round 25 fix pass: docs lane (2026-11-01)

Brief: `.supervisor/r25_fix_docs_brief.md`. The base is `c4bb56b`.

The board is unchanged: `92c3ad59…`, SHA-256 checked. Figures come from these sources:
- `round25_triage.md` / `.json` (R25-TRI-01 … -10);
- `round25_fix_cad.md` (D-R25-01 … -03; 216 D IDs);
- `parts_budget.json` (SHA-256 `f92611a8…`).

The R92 bleed is 3.147 mA. It is derived from the budget's U9 bound of 3.743861 A minus its stated terms. The margin is
now 0.202327 A.

Constraints kept:
- Docs only, and no git change.
- AGENTS §2 is byte-identical (md5 `5549c80b…`).
- No absolute paths were added.
- Links and anchors: 0 bad.

## Files and statements changed

### AGENTS.md (§1 battery row, status paragraph)
- Single-drop-out immunity, with repeated drop-outs adding up.
- The new chatter rule (under 7 ms open in every sliding 100 ms window, U9 on at 5.73 V, limit 7.63 ms). It replaces
  the < 10 ms and < 18 % rules, and the root's < 18 % call was wrong.
- Post-trip hold-up 0.103–0.164 / 0.291–0.430 ms.
- Status: round 25's results, and the closing pair is now rounds 26 and 27.

### STATUS.md
- Status lines: round 25, rounds 26 / 27, and the new chatter rule.
- New round 25 entry, with tests, DRC / gate, simulation and physical reported separately.
- The round 24 sentence is fixed: "every record carries the ramp window" now says FMEA H-6 lagged (TRI-05), and the
  18 % line is marked replaced.
- 216 decisions.

### docs/REQUIREMENTS.md
- F4: what the 5.96 V pack means, and the chatter test.
- F6:
  - single drop-out, with repeated drop-outs adding up;
  - the new bench rule and the 20.0 / 24.4 % explanation corrected (fast-chatter limit only, guidance table);
  - post-trip hold-up;
  - "100–220 µF would do" struck (0.03–0.12 ms) (TRI-03);
  - "10 ms criterion" wording.
- Pack row: 4.802 / 4.835 / 4.875 V (TRI-07).
- P3: plate thinner than 0.8 mm (TRI-09).
- Tab-reboot bullet; status line.

### docs/M3_R10.md
- Summary, review table (rows 25, 25 fix pass, 26 and 27), closing paragraph, 216 IDs, a round 25 checks bullet, and
  evidence records.
- Switch network and Power "Logic and switch": the new rule.
- Hold-up (Power) and firmware rule 8 (TRI-02).
- R150–R155 (TRI-08).
- The fix-pass table row notes D-R25.
- Open items: rounds 26 / 27.

### docs/ORDERING.md
- Status.
- §8.3: single drop-out; the chatter bullet rewritten; post-trip hold-up.
- §8.4: plate thinner than 0.8 mm.

### docs/R10_VEHICLE_HANDOFF.md
- Status.
- Chatter rule.
- Plate bound.

### docs/FMEA_REDUNDANCY.md
- H-6 ramp window: 4.29–4.80 / 4.72–5.25 V (TRI-05).
- I-11: current board `92c3ad59…` (TRI-06).

### docs/R10_VALIDATION.md
- Head, latest review and log (rows 25, 26 and 27).
- New "Round 25: ten lenses on committed `c4bb56b`" (the findings index) and "Round 25 fix pass".
- Owner preamble.
- Owner rows:
  - 5 and 25: hold-up, with "about a third" corrected;
  - 21: the rule;
  - 20: 216 / 90;
  - 32: TRI-09 and TRI-10.
- Decision rows D-R25-01 … -03; ledger counts 216 / 90.
- S-8 paragraph: `92c3ad59…` (TRI-06).
- C87 row; §4 U9 bound 3.743861 / 0.202327 A.
- §8: R150–R155 (TRI-08).
- R23-POWER-02 and R24-TRI-02 dispositions annotated as superseded.

### parts_qualification.md
- Status line.
- Line 20 (D402 row): the 5.96 V rule replaced by D-R25-01.
- Line 34 (C87 row): single drop-out and the rule.
- Line 137: R92 bleed 3.147 mA at 10.18 V, bound 3.743861 A, margin 0.202327 A.
- Line 639: the superseded all-shorts paragraph labelled historical, with the 10.18 V corner and the current
  3.657 / 3.627 A noted; "asserts" corrected to past tense, since no such assert exists in `r10_parts.py` now.
- Budget SHA-256.

## Completeness sweep

`git grep -n` was run across docs/, STATUS.md, AGENTS.md and `m3_design/assembly_review/sources/` (sources/r10_review
records and R10_DECISIONS excluded). Residual hits after the fixes:

| Old value or phrase | Hits | Residuals: why each stays |
|---|---|---|
| `< 10 ms`, `18 %`, `longest drop-out`, `however short` | 9, 22, 0, 0 | Each current hit states that the rule was replaced. History: STATUS round 24 entries, R10_VALIDATION R19-REQ-02, the R23-POWER-02 / R24-TRI-02 dispositions (annotated) and the round 24 / 25 indexes. Unrelated: M3_R8, MARGIN_PRESCRIPTION and r8_design current-share percentages |
| `drop-out shorter than` | 8 | All now read "a single … drop-out", with repeated drop-outs adding up; the binding note is generated |
| `5.96 V` | 9 | The single 10 ms drop-out pack floor (a labelled Calculation); the M3_R10 round 24 fix-pass table (history, annotated); M3_R4 (USB OV, unrelated); round 24 index; parts_qualification line 20 ("replaced") |
| `20–24 %`, `20.0 / 24.4` | 1, 5 | Round 24 index (history); the rest now say fast-chatter limit, guidance only |
| `0.157–0.182`, `0.44–0.48`, `from 5.3 V`, `about a third` | 2, 2, 3, 4 | Quoted as the superseded figures (M3_R10 Power, row 25) and in the round 25 index. R9 history. r10_plan O5's 5.3 V buck is unrelated |
| `100–220 µF would do` | 6 | Every hit says it is struck |
| `4.5–4.8 V`, `4.9–5.2 V` | 1, 1 | Round 24 index (history) |
| `4.778` / `4.811` / `4.851 V` | 0 current | REQUIREMENTS keeps them only as "without D402" |
| `still missing` | 4 | Round 25 index; R7 / R8 / R9 review history |
| `plate ≤ 0.8 mm`, `C421 at 125` | 1, 1 | Round 25 index |
| `9.97 V`, `9V97`, `3.7437`, `3.083`, `0.202391` | 4, 1, 1, 6, 2 | Given as "was" figures (parts_qualification lines 139 and 475, R10_VALIDATION §4), the labelled historical paragraph (line 640), the round 25 index, the round 13 ledger and R7 history |
| `3.645`, `3.616` | 12, 0 | Numeric coincidences in hotplug_capacitors.json and R9 evidence |
| `rounds 25 and 26` | 0 | — |

Not edited, as R4 history: `docs/M3_R4.md` A2's 9.63–9.96 V.

## Not done or not verified

- The triage's 4000-train adversarial search was not re-run here.
- No review of the round 25 fix pass exists yet. Rounds 26 and 27 are planned.
