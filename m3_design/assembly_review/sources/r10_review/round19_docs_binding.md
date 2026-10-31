# Round 19 review: docs_binding lens

Target commit 1e60441, board `a3144b15...` (SHA-256 unchanged before and after). Reviewer: Claude. Result: **0 Critical / 0 Major / 9 Minor** (all new).

The documents bind well to the board: hash, size, counts, positions, pin map, binding hashes, fab package, cost and stock all reproduce. The defects are a few stale coordinates and figures, glued text that survived the round 18 respacing, and an owner decision table that lists the right items but is not yet laid out for someone to decide from.

## Findings

### R19-DOC-01 (Minor, new): ORDERING 8.2 names C126.2's GND via at its pre-fix position

docs/ORDERING.md section 8.2 (the "Also confirm" list, Q124 / C126 bullet) says C126 is F(16.85,57.675), -90 deg "with its GND via at (16.178,59.047)". D-R18-05 moved that via to (15.8,59.425) (R10_DECISIONS D-R18-05; AVA_LAYOUT "Round18 CAD fix pass" table). Native board a3144b15: C126 at F(16.85,57.675) -90 confirmed; GND vias near C126.2 (16.85,58.375) are (15.85,58.345), (15.85,57.695) and (15.8,59.425); no via at (16.178,59.047).

Impact: The assembly-preview checklist the owner will compare with JLC's order preview carries a coordinate that no longer exists, so the check cannot be completed as written.

Fix: Replace "(16.178,59.047)" with "(15.8,59.425)" in docs/ORDERING.md 8.2, and add a one-line "last verified against a3144b15" note to that bullet list.

### R19-DOC-02 (Minor, new): The owner decision table is not yet decision-ready

docs/R10_VALIDATION.md "Owner decision table" (line ~1613, 20 rows). (a) It opens "Each row is one thing you must accept or do before R10 can be ordered", but rows 8-12 close only by first-article, vibration, pull and bench tests, which can only happen after an order (ORDERING 8.3 is "After delivery"); the table does not separate "decide before ordering" from "accepting now, closing after delivery". (b) No row says whether it blocks the order, what the recommended answer is, or where the owner records a dated yes / no (row 20 asks for a "dated acceptance" but there is no column or place for it). (c) Row 2 is one ~190-word cell with unexplained tokens ("Round 18 m01 to m06", "S-8", "OUT-GND approaches", "CONT_MID"). (d) Row 20 asks the owner to accept "the 137 agent decisions through D-R18-11" and "the open Minors under Gate lane", but the only list is the 1,000+ line R10_DECISIONS.md; the JSON ledger stops at 126 and does not index D-R18-01..11 (M3_R10 says so). (e) The table is at line 1611 of a 2296-line file and the file head (lines 1-60) does not link to it.

Impact: A person cannot tell which of 20 items gate the order, which they can defer, or what exactly they are signing in row 20. The Accept rows read as risks already taken rather than choices.

Fix: Add a "When" column (before order / at first article / after delivery) and a "Blocks order?" column; move rows 8-12 to a "Accepted now, closed by test" group; add an "Owner answer / date" column; cut row 2 to 3 short sentences and put the residual list under a sub-heading; for row 20 add a half-page table of D-R18-01..11 (ID, one-line effect, board change yes/no) and say the earlier 126 are covered by the existing JSON; link the table from the first paragraph of R10_VALIDATION.md.

### R19-DOC-03 (Minor, new): R10_VALIDATION opens with three stacked historical banners that say "now" about superseded boards

docs/R10_VALIDATION.md lines 20-60: "Historical circuit pass ... Circuit-pass board (6e73b6eb)", "Historical completion before the circuit changes" (rounds 9/10, "OQ-3 $84.43 vs $84.41") and an unlabelled "2026-10-27 update" block that says "board now `407d1d84...`", "tools/check.sh passes at zero", "The R10 board is built and committed". The first two are marked historical; the third has no historical label and uses present-tense "now". Current board a3144b15, cost $79.12.

Impact: The first screen of the validation file contradicts M3_R10 "Current state" (board, cost, round count) for a reader who does not read the labels.

Fix: Move lines 20-60 under a "## Historical banners" heading below the review-round log, or prefix the 2026-10-27 block with "Historical (board 407d1d84, superseded)"; keep only "Where R10 stands", "Latest reviews", "Current PCB" and a link to the owner table at the head.

### R19-DOC-04 (Minor, new): Numbers glued to words remain in live deviation text and in two records the current docs point to

R18-DOC-02 claimed respacing of current text. Remaining in docs/R10_VALIDATION.md "R10 deviations for owner acceptance": line 1775 "allocation is960LSIcycles plus"; 1755 "min IN-14.807373 V", "traces.0/0.01 ohm sensitivities fail"; 1757 "OUT+GND13.004163 mm/6.591563 mm 2" (mm2 split into "mm 2"); 1853 "NRST0.777817 mm"; 1974 "IMU_CS0.7596+0.0918 mm"; 1995 "ST2.2 uF+/-20%". m3_design/assembly_review/sources/r10_design/AVA_LAYOUT.md (20 lines, including the current-status paragraphs 299 "reviewed632a9ad3", 324-325 "is0C/0M/11Minor groups from17raw(5new/6carried),all1942files"); R10_DECISIONS.md has about 81 such lines (e.g. 2405, 2423-2441, 2472-2473, 2491). Historical round sections 1246-1354 also carry them.

Impact: The fire-pulse watchdog allocation (line 1775) and the hot-plug / loop-geometry rows are the numbers an owner or reviewer reads when judging safety timing; the glue makes them error-prone to copy.

Fix: Respace the seven live lines in R10_VALIDATION (1755, 1757, 1775, 1853, 1974, 1995) and AVA_LAYOUT 299-340; leave sealed historical round text but say so in a one-line note at the head of AVA_LAYOUT and R10_DECISIONS. A one-shot regex lint ([a-z]\d, \d[a-z]{3,} outside code spans) in tools/check.sh would keep it from recurring.

### R19-DOC-05 (Minor, new): PC1 / Q122 gate bound is 0.220 V in the docs but 0.218 V in the pin table

pin_table.tsv row 16 (PC1): "gate <=0.218 V at 3.6 V". docs/M3_R10.md lines 42, 302, 578 and R10_VALIDATION lines 1520, 1816 say 0.220 V. Arithmetic with R122 1 kOhm, R123 2 kOhm (native values) and a 30 kOhm pull-up at 3.6 V: 3.6 x 2 / (30+1+2) = 0.2182 V, so 0.218 V is the derived figure; no tolerance is stated that would give 0.220. (The BAT_FAULT_N bridge figure 0.554 V = 3.6 x 2 / 13 is derived the same way.) The pin table is hash-bound into the binding note, so the two cannot be reconciled by editing one silently.

Impact: Two different bounds for one hand-calculated worst case, in the record the firmware engineer reads (pin table) versus the one the owner reads (M3_R10). Margin to the 0.65 V threshold is large either way.

Fix: Pick 0.218 V (or state the tolerance corner that gives 0.220 V) and use it in M3_R10 (3 places), R10_VALIDATION (2) and ORDERING; the pin_table text is already 0.218, so only docs change.

### R19-DOC-06 (Minor, new): "Seven nets" / "four protected barrels ... and RAW_ACT" does not match BARREL_NETS or the board

AGENTS.md pyro row, docs/M3_R10.md CH1 pyro ("It now covers seven nets (BARREL_NETS): the four protected barrels (PYRO1_IGN, PYRO1_OUT, PYRO1_GATE and RAW_ACT) and ... the ACT_GATE vias, the BAT_ENABLE vias and the J400.2 hole") and R10_VALIDATION section 1 ("covers seven nets"). tools/check_r10.py BARREL_NETS has 11 names (RAW_ACT, PYRO1_IGN, PYRO1_OUT, PYRO1_GATE, ACT_GATE, ACT_DRV, BAT_ENABLE, BAT_SW_RETURN, ACT_EN, ACT_EN_MCU, PYRO1_GATE_N). Native board: plated barrels exist on 6 of those nets (BAT_ENABLE 3 vias, ACT_GATE 2, PYRO1_OUT via + J121.1, PYRO1_GATE 1, PYRO1_IGN J121.2, BAT_SW_RETURN J400.2) = 10 barrels; RAW_ACT has none. The four "original" barrels are J121.1, J121.2, the PYRO1_OUT via and the PYRO1_GATE via.

Impact: A reviewer or the owner reading "seven nets, RAW_ACT included" would look for a RAW_ACT barrel that does not exist, and the count does not reproduce from the code or the board.

Fix: Reword to "S-8 holds 10 plated barrels on 6 nets (list), measured 1.050 mm at the ACT_GATE / BAT_ENABLE / J400.2 barrels and 1.103 mm at J121.1", in the three places; or reword to "the 11 net names in BARREL_NETS (6 carry barrels)".

### R19-DOC-07 (Minor, new): Committed record promises a verification that is not recorded as done

docs/M3_R10.md "Software and CAD checks", gate-hardening bullet: "These are the gate implementer's numbers; the supervisor's own tools/check.sh run on the final tree confirms them before the commit." The text is committed (1e60441) but is in the future tense, no receipt or log is cited, and STATUS.md says only "Verified by the gate implementer's two tools/check.sh runs (exit 0)". My own read-only runs on the committed tree reproduced check_r10 35 / 35 rules OK, route_check 0 failing (22 bump windows, 6 unrecorded leftovers), fit_check OK with wire room 5.00-5.60 mm, and the counts of test_* functions (shell 10, procurement 20, fab_validation 34, fit 33, paste 16, parts 5, route 67, R10 201 incl. 5 NumPy), but I did not run the self-tests or the full gate.

Impact: The doc leaves it unclear who ran the final gate; a reader cannot tell whether "exit 0" on the final tree is supervisor-confirmed.

Fix: Replace with a past-tense sentence naming the run (who, when, commit, exit code) and the log path, or delete the sentence and keep STATUS wording; use the same wording in STATUS.md and M3_R10.

### R19-DOC-08 (Minor, new): AGENTS points to AVA_LAYOUT.md for "current placement" but the file is mostly a record of older boards

AGENTS.md line after the status paragraph: "Current placement, section 6 disposition and metrics: AVA_LAYOUT.md". The file opens "This is the immutable hand-off measurement record for 0c50b9fd... below", then a bold "Full R16/R17 pair complete" block for 632a9ad3, and the a3144b15 data is only in the last section (line 345, "Round18 CAD fix pass"). ava_layout_metrics.json and ava_layout_validation.json still carry hashes 0c50b9fd / 6e73b6eb; there is no metrics file for a3144b15.

Impact: A reader following the pointer gets placement tables for a board that no longer exists; the current placement is in r10_place.tsv and the board.

Fix: Say in AGENTS "current placement: m3_design/r10_place.tsv; AVA_LAYOUT.md section Round18 for the latest changes; the rest is history", and add a top-of-file line to AVA_LAYOUT.md naming the section to read.

### R19-DOC-09 (Minor, new): Sense-level figures are given without saying powered or cold, and the "no bypass" wording hides a 5.1 kOhm path

docs/M3_R10.md "Retained deviations": a RAW_ACT bridge to PYRO1_CONT_MID "passes at most 1.6 mA (no R134 or e-match bypass) and raises the CONT reading to about 1.38 V against about 0.75 V intact". R10_VALIDATION section 1 gives healthy / open passive CONT as 99.369 / 146.226 mV. The 0.75 V and 1.38 V figures are the powered-bus readings (8.4 V x 1 kOhm / 11.2 kOhm = 0.75 V; 8.4 V / 6.1 kOhm x 1 kOhm = 1.38 V), the 99 mV figure is the cold reading; neither text says which. The 1.6 mA is the current through R173 (5.1 kOhm) from RAW_ACT to OUT (8.4 V / 5.1 kOhm = 1.65 mA), i.e. a 5.1 kOhm bypass of R134, which is not "no bypass".

Impact: An owner or firmware engineer comparing the two documents sees 0.75 V and 99 mV for the "intact" CONT reading and cannot reconcile them.

Fix: Write "powered-bus reading" / "cold reading" beside each figure and replace "no R134 or e-match bypass" with "only a 5.1 kOhm path (<= 1.65 mA), far below fire current".

## Readability judgement

- **M3_R10 "Current state"**: the summary, board table, review-status table and cost table are clear and consistent. The 13-row "what the fix pass changed" table and the check-count bullets are engineering detail placed before the owner-relevant items; the owner should be pointed to "Review status" and "Open items" first. It also contains the future-tense check claim (R19-DOC-07).
- **R10_VALIDATION owner decision table**: right items, wrong packaging (R19-DOC-02).

## Fix verification

| Fix | Verdict | Measurement |
|---|---|---|
| D-R18-01 / R18-DOC-13 (AGENTS rows) | confirmed | Cells measure 194-629 characters; no R168/R170/R172 and no D-ID lists; board facts checked against native board (positions of J1, J400, J121, J122, J9, J410, J420, U1, U4, U5, U9, R166, L400, Q120-Q124, C84, D9 all match; 100 U1 pad nets match pin_table and binding note) |
| R18-DOC-01 status block stated once | confirmed | STATUS, AGENTS, ORDERING 8, handoff, REQUIREMENTS each have a short block with a working link; all markdown links and anchors in the 7 documents resolve; footprints 208 / segments 947 / vias 292 (166 GND) / 1788.737627 mm / 120 visible + 88 hidden refs / 40 legends / 2,250,842 bytes all match the native board |
| R18-DOC-02 numbers and words respaced | partly | Seven live lines in R10_VALIDATION and about 20 in AVA_LAYOUT still glued (R19-DOC-04); M3_R10 current sections and ORDERING 8 are clean |
| R18-DOC-03 / -04 J410, J420, J9, J121 pin wording | confirmed | Legends on the board (23 pin labels) each sit nearest their own pad and the nets agree (J410.3 GPS_TX_WIRE, J9.3 CAM_RX_WIRE, J121.1 PYRO1_OUT, J121.2 PYRO1_IGN) |
| R18-DOC-05 cost headline and definition | confirmed | cost_check.json: parts 54.334 (sum of lines), feeder 123.93 / 5 = 24.786, total 79.12; +83.96 / 5 = 16.79 -> 95.91; +14.93 / 5 -> 98.90; stock_check fails only U4 (0 < 5); R430 C2999509 84,923, U9 45, C84 111,385; every minimum purchase is 1; 81 charged codes; all match the docs |
| R18-DOC-06 owner decision table | partly | Exists and is linked, but see R19-DOC-02 (when / blocks / recommendation / answer missing) |
| R18-DOC-07 camera energy increment | confirmed | 4.123602 - 2.390393 = 1.733209 Ah; 6.932837 W / 6 V x 1.5 h = 1.7332 Ah; worksheet arithmetic (0.825 W, 0.016933 W, 2.265821 etc.) reproduces |
| R18-DOC-10 / -11 / -12 / -14 | confirmed | Placement and STATUS read cleanly; ORDERING 7 header says "R9 only; for R10 use section 8.4"; "same reviewer family" wording present everywhere checked |
| D-R18-10 text: pin_table rows 3, 16, 18 and regenerated binding note | confirmed (one numeric inconsistency) | pin_table sha256 ae686cd1... equals the binding note's pin_table_sha256; binding board_sha256 equals the board; circuit.json sha256 cac82c2d... equals the binding note's; all 100 pins agree between board, table and note (PC3_C NC); IMU block (x 17, y 45.9, 180, lever arm -6.0 / -2.06 Inference) matches the board and the IMU frame algebra is self-consistent; PC1 bound differs (R19-DOC-05) |
| Fab package counts (D-R18-09, D-R18-11) | confirmed (orientation 185 + 12 and paste 245 / 371 not rerun) | BOM 81 lines / 197 refs, CPL 197 rows (66 / 131), owner BOM 1 line (C84), manifest 6 outputs and 193 inputs all re-hash correctly and bind a3144b15; orientation and paste counts are quoted from tools I did not rerun |

## Fix now

- ORDERING 8.2: replace the C126 GND via coordinate (16.178,59.047) with (15.8,59.425) (R19-DOC-01)
- Respace the seven glued live lines in R10_VALIDATION (1755, 1757, 1775, 1853, 1974, 1995) and use 0.218 V for the PC1 gate bound in M3_R10 / R10_VALIDATION (R19-DOC-04, R19-DOC-05)
- Add "When" and "Blocks order?" columns and an "Owner answer / date" column to the owner decision table; link it from the head of R10_VALIDATION; label the 2026-10-27 banner historical (R19-DOC-02, R19-DOC-03)
- Reword the S-8 "seven nets" sentence in AGENTS, M3_R10 and R10_VALIDATION to the 10 barrels on 6 nets (R19-DOC-06)

## Coverage limits

- Did not run tools/check.sh, the self-test suites, the NumPy hot-plug / plate tests, jlc_orient or paste_check (pcbnew / NumPy environment and no-full-gate rule), so orientation 185 + 12, paste 245 / 371, DRC / ERC / parity zero and the test pass counts are quoted, not re-executed.
- Did not recompute netlist_sha256 of the binding note, the 2304-case hot-plug result, the plate model (181.1 Hz, 70.5 g, 0.270913 mm, run on the previous board), or any datasheet citation.
- Read all of M3_R10 sections that describe the current board and the owner table sections 1-5, 9-13; sections 6-8 of the deviation list and the historical rounds were sampled, not read line by line.
- Readability judgement of the owner table and Current state is mine; I did not test it with the owner.
