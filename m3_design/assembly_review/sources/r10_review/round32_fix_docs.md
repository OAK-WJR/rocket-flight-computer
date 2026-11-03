# R10 round 32 fix pass: docs lane (2026-11-02)

Brief: `.supervisor/r32_fix_docs_brief.md`. Base commit `3366287`, board `a0ec075e…` (unchanged). Input: the triage
`round32_triage.md` / `.json` (R32-TRI-01 … -03, `all_places` and wording) and the round 31 triage (`round31_triage.md`,
clean). This was the only lane.

**Files edited (docs lane only):** AGENTS.md (outside §2: the R10 status paragraph), STATUS.md, docs/M3_R10.md,
docs/ORDERING.md, docs/R10_VALIDATION.md, docs/R10_VEHICLE_HANDOFF.md, docs/REQUIREMENTS.md, `parts_qualification.md`,
and the one-line erratum in `round19_fix_docs.md`.

**Constraints kept:**
- AGENTS §2 byte-identical to HEAD (md5 of the `## 2.` … `## 3.` span `5549c80b6abf5f5b5a93fbd61698e178` in HEAD and in
  the working tree);
- no generator, test, decision-record, CAD or git change; no new D-R32 decision;
- no local absolute paths added (0 in the diff);
- links: 184 relative links and anchors in the nine edited files, 0 bad (new anchors
  `#round-31-ten-lenses-on-committed-3366287`, `#round-32-ten-lenses-on-committed-3366287` and `#round-32-fix-pass`
  resolve).

## Items

### R32-TRI-01 (R166-to-C84 courtyard gap)

| Place | Before → after |
|---|---|
| ORDERING 8.2 heat limit (:435) | "R166's courtyard is 0.56 mm from C84's" → "0.65 mm from C84's (courtyard centrelines; 0.60 mm between the courtyard lines' outer edges; R32-TRI-01)" |
| R10_VALIDATION §8 C84 hand-fit paragraph (was :3063) | "R166, 0.56 mm from its courtyard" → "R166, whose courtyard is 0.65 mm from C84's (courtyard centrelines; 0.60 mm between the courtyard lines' outer edges; R32-TRI-01)" |
| R10_VALIDATION R19-MEC-02 row (was :1685) | Appended "**Round 32 correction** (R32-TRI-01): R166's courtyard is 0.65 mm from C84's (courtyard centrelines; 0.60 mm between the lines' outer edges); 0.56 mm was a bounding-box figure"; the row's title column keeps the round 19 wording as history |

Historical review records (`round19_mechanics.json` / `.md`, `round28_audit_proc.md`:59, `round29_mechanics.json` /
`.md`) stay as written; this record and R10_VALIDATION's Round 32 section cite the correction.

### R32-TRI-02 (C84 heat limit summary)

R10_VALIDATION §8 (was :3063): "ORDERING 8.2 now limits the time and temperature, asks for top-side preheat with the bottom
supported, and re-inspection …" → "ORDERING 8.2 now limits the dwell time and asks for the tip temperature and time to be
recorded, for top-only heating with the bottom supported on a heat-sinking fixture (no preheat and no temperature limit;
R32-TRI-02), and for re-inspection …". ORDERING 8.2:436 itself was already right and is unchanged.
`round19_fix_docs.md`:38: in-line erratum after "top preheat": "(erratum, R32-TRI-02: ORDERING 8.2 asks for no preheat
and no temperature limit, only top-only heating with the bottom supported, a short dwell and a recorded tip temperature
and time)".

### R32-TRI-03 (fitted 85 °C parts)

| Place | After |
|---|---|
| R10_VALIDATION owner row 33 | "The fitted 85 °C parts (among them MS5611, the AP6320x bucks, J430, U3, Y1, LED1, LED2 and the 16 fitted X5R capacitors C6–C11, C19, C20, C22, C23, C28, C80, C89, C92, C95, C96; R32-TRI-03) therefore have no margin …" (this place never named the U4 alternates) |
| M3_R10 hot end (:499, was :496) | "The fitted 85 °C parts (among them … C95, C96; the U4 alternates if fitted; R32-TRI-03) then have no margin …" |
| `parts_qualification.md`:40 (Round 23 notes) | "the fitted 85 °C parts (among them … C95, C96; the U4 alternates if fitted; round 32, R32-TRI-03) need bay air …" |

Count: C6–C11 (6) plus C19, C20, C22, C23, C28, C80, C89, C92, C95, C96 (10) = 16, matching the triage. The pass rule
("every 85 °C part ≤ 85 °C") is unchanged.

### Records (item 4)

- **STATUS:** status line (round 31 clean, round 32 not; closing pair rounds 33 and 34); new "Round 32 review and fix
  pass" entry (2 raw Minor: manufacturing 1, parts 1; triage 3 Minor, none on the board, 132 observations, 11
  re-examined, 0 not reproducible; the three fixes; tests and gate reported separately, gate as root's run, no result
  claimed) and "Round 31 review" entry (ten lenses 0, triage confirmed, clean, on `3366287`; no fix pass); the round 30
  entry's physical-tests line now says rounds 31 and 32 reviewed the board.
- **R10_VALIDATION:** "Where R10 stands" and "Latest review" (round 32 and 31 sentences); the round table (rows 31 and 32
  filled, rows 33 / 34 planned); new sections "Round 31: ten lenses on committed `3366287`", "Round 32: ten lenses on
  committed `3366287`" (index of R32-TRI-01 … -03 with dispositions, observations) and "Round 32 fix pass"; owner-table
  intro; owner row 20 (rounds 27–32 counts, rounds 33 and 34). Decision counts unchanged (229 through D-R29-02).
- **M3_R10:** summary; review-status rows 31, 32, 32 fix pass, and 33 and 34; the closing-pair paragraph (round 30 now in
  its history list); the PCB-history bullet.
- **AGENTS (status paragraph), ORDERING 8 status, the handoff, REQUIREMENTS (R10 status), `parts_qualification.md`:**
  round 31 and 32 sentences; closing pair rounds 33 and 34.

## Completeness sweep

`git grep -n -F` over docs/, STATUS.md, AGENTS.md and `m3_design/assembly_review/sources/` (excluding the immutable
`r10_review/round*_` records unless noted) for `0.56 mm`, `preheat`, `MS5611, the AP6320x`, `MS5611, AP6320x`,
`31 and 32`, `rounds 31`, `Rounds 31` and `limits the time and temperature`:

| Residual | Why it stays |
|---|---|
| `0.56 mm` in STATUS:17, R10_VALIDATION R19-MEC-02 row title and R32-TRI-01 row | Quotes of the error, each with the 0.65 mm correction |
| `0.56 mm` in M3_R4, M3_R5, R7_VALIDATION, r7 / r8 review records, R8_DECISIONS | Unrelated figures on other boards |
| `0.56 mm` in `round19_mechanics`, `round28_audit_proc.md`:59, `round29_mechanics` | Historical review records, left as written by the triage's rule |
| `preheat` in AGENTS:32, STATUS:18, M3_R10:43, R10_VALIDATION:8 / R32-TRI-02 row / §8 paragraph | Each says ORDERING 8.2 sets no preheat |
| `preheat` in ORDERING:83 / :95 / :96, R9_VALIDATION, r7 / r9 records, R9_DECISIONS | LS120 reflow rating and R9 THT notes, unrelated to C84 |
| `top preheat` in `round19_fix_docs.md`:38 | Historical fix record, with the R32-TRI-02 erratum in line |
| `MS5611, the AP6320x` in STATUS:19, R10_VALIDATION R32-TRI-03 row | Quote of the old list as the error / the new list |
| `MS5611, the AP6320x` in M3_R10:499, owner row 33, `parts_qualification.md`:40 | The corrected "among them" lists |
| `MS5611, AP6320x` | 0 hits |
| `31 and 32` / `rounds 31` / `Rounds 31` in STATUS:42, R10_VALIDATION:8, owner row 20 | Past tense ("reviewed") or the round counts; none plans rounds 31 and 32 |
| `limits the time and temperature` in R10_VALIDATION R32-TRI-02 row | Quote of the error |

## Not done or not verified

- No board, generator, test, decision-record or git change. No check run by this lane; root runs `tools/check.sh`
  before the commit, and STATUS / R10_VALIDATION say so without claiming a result.
- No pcbnew re-run; TRI-01's 0.65 / 0.60 mm figures are the triage's probe. No physical test. Rounds 33 and 34 are
  planned on `a0ec075e…`.
