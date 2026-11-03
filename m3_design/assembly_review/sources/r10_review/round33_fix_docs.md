# R10 round 33 fix pass: docs lane (2026-11-02)

Brief: `.supervisor/r33_fix_docs_brief.md`. Base commit `feed21f`, board `a0ec075e…` (unchanged). Input: the triage
`round33_triage.md` / `.json` (R33-TRI-01 and its wording). This was the only lane.

**Files edited (docs lane only):** AGENTS.md (outside §2: the R10 status paragraph), STATUS.md, docs/M3_R10.md,
docs/ORDERING.md, docs/R10_VALIDATION.md, docs/R10_VEHICLE_HANDOFF.md, docs/REQUIREMENTS.md and
`parts_qualification.md`.

**Constraints kept:**
- AGENTS §2 byte-identical to HEAD (md5 of the `## 2.` … `## 3.` span `e3bdcdaa37e08ca027ab2f80fad0f2e7` in HEAD and in
  the working tree);
- no generator, test, decision-record, CAD or git change; no new D-R33 decision;
- no local absolute paths added (0 in the diff);
- links: 189 relative links and anchors in the eight edited files, 0 bad (new anchors
  `#round-33-ten-lenses-on-committed-feed21f` and `#round-33-fix-pass` resolve).

## Items

### R33-TRI-01 (U9 pad exposure, ORDERING 8.3)

| Place | Before → after |
|---|---|
| ORDERING 8.3 probe table, U9 IN / OUT row (:552) | "U9's pads 5 and 6 expose only 0.10 × 0.30 mm beyond the body at each end" → "U9's pads 5 and 6 expose 0.15–0.25 mm (0.20 mm nominal; RPW0010A body 1.9–2.1 mm, SLVSFC9C) × 0.30 mm beyond the body at each end" |
| ORDERING 8.3 ILM probe line (:555) | "(R84 750 Ω, BAT_ILIM; pad 9 itself is under the body)" → "(R84 750 Ω, BAT_ILIM; pad 9 exposes only 0.15–0.25 × 0.25 mm beyond the body)" |

The probe points and the R84.1 instruction are unchanged. The frozen round 23 record (`round23_docs_binding.md`:55,
`round23_docs_binding.json`:82) stays as written.

### Records (item 2)

- **STATUS:** status line (round 32 summarised; round 33 not clean; closing pair rounds 34 and 35); new "Round 33 review
  and fix pass" entry (1 raw Minor, docs binding; triage 1 Minor, none on the board, 98 observations in 11 groups, 0 not
  reproducible; the fix; tests and gate reported separately, gate as root's run, no result claimed); the round 32
  entry's physical-tests line now says round 33 reviewed the board.
- **R10_VALIDATION:** head line (round 33 added, six fix passes, rounds 34 and 35); "Latest review" (round 33 sentence;
  round 32's now says round 33 reviewed the board); round table (row 33 filled, rows 34 / 35 planned); new sections
  "Round 33: ten lenses on committed `feed21f`" (findings index with disposition, observations) and "Round 33 fix pass";
  owner-table intro; owner row 20 (rounds 27–33 counts, rounds 34 and 35). Decision counts unchanged (229 through
  D-R29-02).
- **M3_R10:** summary; review-status rows 33, 33 fix pass, and 34 and 35; the closing-pair paragraph (round 32 and 31 now
  in its history list); the PCB-history bullet.
- **AGENTS (status paragraph), ORDERING 8 status, the handoff, REQUIREMENTS (R10 status), `parts_qualification.md`:**
  round 32 and 33 sentences (the round 31 sentence dropped as history); closing pair rounds 34 and 35.

## Completeness sweep

`git grep -n -F` over docs/, STATUS.md, AGENTS.md and `m3_design/assembly_review/sources/` for `0.10 × 0.30`,
`under the body`, `beyond the body`, and (excluding the immutable `r10_review/round*_` records) `33 and 34`,
`rounds 33`, `Rounds 33` and `33 (planned)`:

| Residual | Why it stays |
|---|---|
| `0.10 × 0.30` | 0 hits outside the frozen round 23 record |
| `beyond the body` in ORDERING:552 / :555 | The corrected text |
| `beyond the body` / `under the body` in `round23_docs_binding.md`:55 / `.json`:82 | Frozen history, left as written by the brief |
| `under the body` elsewhere (FMEA I-9, M3_R4, MARGIN_PRESCRIPTION, R10_VALIDATION R19-RTE-04 rows, R8 records, r7–r9 and other r10 review records) | Unrelated parts or boards (0603 fanout vias, IMU, MS5611, DB125 latch); none about U9 |
| `33 and 34` in STATUS round 32 entry ("the closing pair is now rounds 33 and 34") | Dated round 32 record, true when written; the round 33 entry above it moves the pair to rounds 34 and 35 |

## Not done or not verified

- No board, generator, test, decision-record or git change. No check run by this lane; root runs `tools/check.sh`
  before the commit, and STATUS / R10_VALIDATION say so without claiming a result.
- No pcbnew re-run; TRI-01's figures are the triage's probe (`.supervisor/r33_triage/u9.py`) against SLVSFC9C. No
  physical test. Rounds 34 and 35 are planned on `a0ec075e…`.
