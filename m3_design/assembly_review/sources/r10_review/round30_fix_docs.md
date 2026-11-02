# R10 round 30 fix pass: docs lane (2026-11-02)

Brief: `.supervisor/r30_fix_docs_brief.md`. Base commit `0afaed3`, board `a0ec075e…` (unchanged). Input: the triage
`round30_triage.md` / `.json` (R30-TRI-01, -02, `all_places` and wording). This was the only lane.

**Files edited (docs lane only):** AGENTS.md (outside §2: the buzzer row and the R10 status paragraph), STATUS.md,
docs/M3_R10.md, docs/REQUIREMENTS.md, docs/ORDERING.md, docs/R10_VEHICLE_HANDOFF.md, docs/R10_VALIDATION.md and
`parts_qualification.md`. AVA_LAYOUT.md and docs/FMEA_REDUNDANCY.md needed no change (neither carries either statement).

**Constraints kept:**
- AGENTS §2 byte-identical to HEAD (md5 of the `## 2.` … `## 3.` span `5549c80b6abf5f5b5a93fbd61698e178` in HEAD and in
  the working tree);
- no generator, test, decision-record, CAD or git change; no new D-R30 decision;
- no local absolute paths added (0 in the diff);
- links: 175 relative links and anchors in the eight edited files and this one, 0 bad (new anchors
  `#round-30-ten-lenses-on-committed-0afaed3` and `#round-30-fix-pass` resolve).

## Items

### R30-TRI-01 (R10_VALIDATION §1)

| Place | Before → after |
|---|---|
| R10_VALIDATION §1, ARM1_SENSE to U13.5 (was :2603) | "about 1.73 V on RAW_ACT with the bus off, about 0.15 mA through the match … (Calculation; …)" → "with the board on (CAM_IO_3V3 is up only then, so the D120 / R131 cold pull-up is live), about 2.19–2.21 V on RAW_ACT with the bus off and about 0.107–0.109 mA through the match against the J-Tek 0.30 A no-fire, at a BAT54 drop of 0.20–0.24 V (Calculation / Inference: the BAT54 drop at about 0.1 mA is inferred; R30-TRI-01: …); the cold screen then reads the bus as live and refuses" |
| R10_VALIDATION §1, EN thresholds paragraph (was :2636) | "(EN is loaded by 10 kΩ, 11.2 kΩ or 2 kΩ)" → "(EN is loaded by 10 kΩ, 11.2 kΩ (5.6 kΩ with the e-match or the step-3 dummy fitted, R30-TRI-01) or 2 kΩ)" |

Hand check of the triage's three-node solve: (3.3 − V)/10.2 k + (3.3 − Vf − V)/10 k = V/11.2 k gives V = 2.205 / 2.191 V
and I = (3.3 − V)/10.2 k = 0.107 / 0.109 mA at Vf = 0.20 / 0.24 V; 11.2 k ∥ (11.2 k + about 4 Ω) = 5.6 kΩ.
Conclusions unchanged. The round 22 lens records that carry 1.73 V are frozen history and were not edited.

### R30-TRI-02 (chamber-test pass criterion, LS120)

In every place the triage listed, the pass criterion is now "every 85 °C part ≤ 85 °C" alone; the test also records
LS120's measured rise over chamber air at the pad load (thermocouple on LS120); LS120 is not a pass / fail gate; the
bay-air limit above which buzzer annunciation is best-effort is 70 °C minus that measured rise, which replaces the
inferred 48 °C (kept only as the pre-test estimate, Inference):

| Place | Change |
|---|---|
| REQUIREMENTS:94 Temperature row | LS120 clause removed from the pass criterion; recorded-rise sentence added; 48 °C marked "the pre-test estimate" |
| M3_R10 "Hot-end temperature" (:496–505) | Same; 48 °C marked "the pre-test estimate, below" |
| ORDERING 8.3 "Board temperature at the pad load" (:608) | "Pass: every 85 °C-rated part ≤ 85 °C." then the record instruction; 48 °C as the pre-test estimate; "Until the test passes" |
| Owner row 33 | "pass if every 85 °C part ≤ 85 °C; also record LS120's measured rise … not a pass / fail gate … (row 36; R30-TRI-02)" |
| Owner row 36 | Title cites R30-TRI-02; "What it means": 48 °C is the pre-test estimate, then 70 °C minus the measured rise; "Needed": the chamber test records LS120's rise (thermocouple on LS120), not a pass / fail gate; respin option kept |
| `parts_qualification.md`:40 (Round 29 note) | "the chamber test passes only with LS120 ≤ 70 °C" → the recorded rise, not a gate, the 70 °C − rise limit, replacing round 29's clause |
| STATUS round 29 entry, LS120 bullet | "now passes only with" → "The round 29 fix pass made …"; added "Round 30 replaced that pass clause (R30-TRI-02) …" |
| R10_VALIDATION R29-TRI-04 row | Pointer appended: round 30 replaced the "LS120 ≤ 70 °C" clause (R30-TRI-02) |
| AGENTS §1 buzzer row (own sweep, not in the triage list) | "above about 48 °C (Inference, the pre-test estimate: the first-article chamber test records LS120's rise, not as a pass / fail gate, and the limit becomes 70 °C minus that rise, R30-TRI-02; …)" |

### Generated text (item 3)

`git grep` "LS120", "chamber", "1.73 V" (and "48 °C", "11.2 k") in `m3_design/r10_sch_check.py` and
`m3_design/assembly_review/sources/r10_design/r10_binding_note.json`: **0 hits**. Nothing to list for root. A wider
`git grep` outside docs/, STATUS, AGENTS and the review sources found only an unrelated S8550 entry in
`procurement_catalog.json`.

### Round 30 records (item 4)

- **STATUS:** status line (round 30 sentence; closing pair rounds 31 and 32); new "Round 30 review and fix pass" entry
  (raw 0 / 0 / 2, safety 2, other nine 0; triage 2 Minor real errors, 107 observations not counted, 0 not reproducible,
  none on the board; the two fixes; software tests, DRC / CAD gate, simulation and physical tests reported separately,
  with the gate stated as root's run before the commit, no result claimed); the round 29 entry's physical-tests line
  now says round 30 reviewed the board.
- **R10_VALIDATION:** "Where R10 stands" and "Latest review"; the round table (row 30 filled, rows 31 / 32 planned); new
  sections "Round 30: ten lenses on committed `0afaed3`" (index, two dispositions, observations) and "Round 30 fix pass";
  owner-table intro; owner row 20 (rounds 27–30 counts, rounds 31 and 32). Decision counts unchanged (229 through
  D-R29-02; no D-R30 decision).
- **M3_R10:** summary; review-status rows 30, 30 fix pass, and 31 and 32; the closing-pair paragraph; the "Open items"
  review sentence. No checks bullet added (this lane ran no check).
- **AGENTS (status paragraph), ORDERING 8, the handoff, REQUIREMENTS (R10 status), `parts_qualification.md`:** round 30
  sentence; closing pair rounds 31 and 32.

## Completeness sweep

`git grep -n -F` over docs/, STATUS.md, AGENTS.md and `m3_design/assembly_review/sources/` (excluding the immutable
`r10_review/round*_` records) for `30 and 31`, `rounds 30`, `Rounds 30`, `LS120 ≤ 70`, `passes only with LS120`,
`1.73 V`, `0.15 mA`, `11.2 kΩ or 2 kΩ` and `48 °C`:

| Residual | Why it stays |
|---|---|
| `30 and 31`, `rounds 30`, `Rounds 30`, `11.2 kΩ or 2 kΩ` | 0 hits |
| `LS120 ≤ 70` in AGENTS:32, STATUS:10 / :18 / :31, M3_R10:42, R10_VALIDATION:8 / :2366 / :2417, `parts_qualification.md`:40 | Each quotes round 29's replaced clause as history, marked as replaced by R30-TRI-02 |
| `passes only with LS120` in R10_VALIDATION:2366 (R29-TRI-04 row) | History of round 29's fix, with the R30-TRI-02 pointer appended |
| `1.73 V` / `0.15 mA` in STATUS:17, R10_VALIDATION:2416 / :2637 | Quotes of the error ("was …", "the round 22 figures … left out") |
| `0.15 mA` in docs/R3_VALIDATION.md:104 | Unrelated (R3 diode Vf) |
| `48 °C` in AGENTS:21, REQUIREMENTS:94, M3_R10:499 / :505, ORDERING:608, owner row 36, STATUS:18 / :31, R10_VALIDATION:2366 / :2417, `parts_qualification.md`:40 | Each now either marks 48 °C as the pre-test estimate (Inference) or says the measured rise replaces it |
| `48 °C` in AGENTS:32 (round 29 sentence) | Dated history of what the round 29 fix pass recorded; the round 30 sentence that follows states the replacement |
| Round 22 lens records `round22_safety.json:38` / `.md:128` | Frozen history (excluded by the triage) |

## Not done or not verified

- No board, generator, test, decision-record or git change. No check run by this lane; root runs `tools/check.sh`
  before the commit, and STATUS / R10_VALIDATION say so without claiming a result.
- No model re-run; TRI-01's figures are the triage's, checked by hand above. No physical test. Rounds 31 and 32 are
  planned on `a0ec075e…`.
