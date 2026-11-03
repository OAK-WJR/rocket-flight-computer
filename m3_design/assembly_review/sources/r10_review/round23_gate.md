# R23 gate adversary (Claude)

Target `c70d261`; PCB SHA-256 `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` before and after
(verified). **0 Critical / 0 Major / 7 Minor**, all gate gaps; no copper on the committed board found below a limit.
Machine-readable twin: [round23_gate.json](round23_gate.json). Probe material: `.supervisor/r23_gate/` (ignored).

## Method

- Each seed is an APFS clone of `git archive c70d261`, seeded with KiCad 10.0.7 pcbnew (zones refilled where copper
  changed; removed items kept referenced) or a file edit. DRU seeds go through the copy's generator (`r10_sch.py`) and
  re-pin `DRU_SHA256`, as a reviewed change would. Generator seeds edit `r10_parts.py`, regenerate its library and make
  the matching board edit.
- Then the post-board regeneration (budget, hot-plug, orient / export / bind / verify, binding note) and every check.sh
  checker with the copy's own tools: DRC + ERC, metadata audit, silk, `r10_parts --check`, fit, check_r10, route_check
  and fab `--content`.
- Every seed applied (SEED exit 0) before it was judged. A "pass" below means every checker step exited 0.
- Gate self-tests were run on the d01 and h01 copies.

## Findings (all Minor)

**R23-GATE-01: the K-rules DRU reader misses three spellings that KiCad honours.**
- What it misses:
  - unquoted rule names, `(rule relief ...)`: the regex needs `(rule "`;
  - quoted layers, `(layer "In1.Cu")`: the quotes defeat `dru_layers_meet`; seed h06 shows KiCad applies such a rule
    (130 DRC hits);
  - `#`-commented rules, which the table counts but KiCad ignores.
- `probe/dru_spell.py` gives 0 issues for each, including an unquoted 0.10 mm rule under the 0.20 mm floor.
- **h01** (unquoted 0.10 mm via relief, re-pinned, plus an In1 GND copper drawing 0.16 mm from the hole wall of via 3V3
  (36.13, 58.80); JLC's figure is 0.2 mm) **passes every checker step**. h01b, the same seed with a quoted name, fails
  K-rules.
- *Fix (checks):* a comment-stripping s-expression reader that accepts bare or quoted names and layers, and fails on
  any unparsed rule.

**R23-GATE-02: the JLC board measures skip copper drawings, copper text and footprint zones.**
- `_copper_items` reads only board zones, tracks, vias and pads. `copper_nodes`, used by S-8, reads all of these.
- In h01b, K-rules reports only the DRU-table issues and nothing for the 0.16 mm wall.
- *Fix (checks):* build `_copper_items` from `copper_nodes`.

**R23-GATE-03: DRU constraints other than the hole rows, and rule severity, have no floor.**
- KiCad honours a DRU clearance below the board-setup 0.15 mm, and a `(severity ignore)` clause.
- **h04** (`clearance (min 0.05mm)` on SERVO1_MCU) and **h03** (`(severity ignore)`, min kept at 0.15 mm), each with
  SERVO1_MCU F.Cu (30.3, 54.8)-(30.3, 73.2) widened to 0.38 mm, **pass every checker step**. The gap is 0.0636 mm, under
  JLC's 0.09 mm spacing.
- dru_spell also finds no check on DRU track_width, edge_clearance, annular_width, text_height or hole_size.
- *Fix (checks):* floor every DRU minimum to PRO_FLOORS / JLC, and reject any `(severity)` other than error.

**R23-GATE-04: the K-legends Fab rule misses four kinds of item.** Each of these passes every checker step:
- f01b: a footprint `PCB_TEXTBOX` "Q121" in Q120 on B.Fab, in clear board;
- f02: Q120's Value field made visible on B.Fab (a part number in the assembly drawing);
- f03: R119's reference squashed to a 0.02 mm character width (only the height is floored);
- f05: a board-level filled B.Fab rectangle over R134's reference.

Caught: f04 (un-mirrored B.Fab reference, by DRC), and round 22's g08a, g08c and g08d.
*Fix (checks):* treat text boxes and visible fields on a Fab layer as Fab text; add a width floor; reject board-level
Fab shapes.

**R23-GATE-05: `r10_parts.py`'s own footprints are pinned only to their own generator.**
- **x02** strips F.Paste from `load_switch()`, the AONR21357 behind Q120 / Q121 on the fire bus. It regenerates the
  library and unpastes the 18 board pads to match, and **passes every checker step**. The bound package shows B_Paste
  357 against the recorded 375.
- x01 (DB125 drill 1.3 → 1.0 mm through the generator) is caught only incidentally, by K-reference after the refill.
  Nothing holds the drill itself.
- *Fix (checks):* SHA-pin the generated `.kicad_mod` files, or their paste, mask and drill, and pin the paste totals.

**R23-GATE-06: check.sh does not hold the committed sheets to the generator.**
- **d01** hand-reverts `diagnostics.kicad_sch` line 2 to the wrong text D-R22-03 removed, and re-binds the fab package.
  It **passes every checker step and all check.sh self-tests**: test_r10_check (253 tests), route, fab, parts and
  paste.
- `test_r21_sheet_notes` checks only the generator's output. The replay in `r10_sch_check.py` catches the edit
  ("nonreproducible"), but only `r10_build.sh` runs it.
- *Fix (checks):* run the replay comparison from check.sh.

**R23-GATE-07: `SINGLE_OPEN_TAPS` still omits flight-relevant single-via pins** (`probe/single_via_all.py`; none is a
tap or appears in the records):
- GND via (16.75, 47.60) alone carries U4.6 / U4.7, the IMU's only supply-ground pins (DS14623 pin table: 6 and 7 are
  "GND, 0 V supply"; 2 and 3 are SDx / SCx);
- the VCAP vias (29.25, 38.00) and (18.00, 37.30) each carry C19 or C20 alone;
- also Q123.2, C21.2 and C28.2.

What an open does to U4 or to the MCU core is an Inference. *Fix (checks now):* add these as taps with exact exceptions.
The second vias wait for the next board change.

## Fix verification

| Fix | Verdict | Evidence |
|---|---|---|
| D-R22-01 | partly | g01e / g01f: K-rules names J400.2 at 0.251 mm and J1.2 at 0.255 mm. Copper drawings are not measured (GATE-02). |
| D-R22-02 | confirmed (coverage partly) | `tap_drop.py`: each of the 15 exceptions dropped gives exactly one issue naming its via. Coverage gap: GATE-07. |
| D-R22-03 | partly | Generator and test are correct; a hand-reverted committed sheet passes (GATE-06). |
| D-R22-04 | confirmed | No PCB change between ec8cb98 and c70d261 (git diff). Figures not re-measured. |
| D-R22-05 | partly | g01e / f / g / h each fail K-rules. Missed: unquoted names, quoted layers, comments (GATE-01); non-hole constraints and severity (GATE-03). |
| D-R22-06 | partly | g08a (5.147 mm), g08c and g08d each fail. Missed: GATE-04. |
| D-R22-07 | confirmed | g07b fails K-ports. Pad nodes are layer-aware. |
| D-R21-01 / -02 / -08 | partly / confirmed / partly | As above. |

## Fix now (checks only, no board change)

GATE-01: DRU reader. GATE-02: copper item set. GATE-03: DRU floors and severity. GATE-04: Fab text kinds, width floor
and shapes. GATE-05: pin r10_parts' lands and the paste totals. GATE-06: replay in check.sh. GATE-07: three new taps.

## Closed

- h05: two GND vias 0.15 mm wall to wall (JLC 0.2 mm) are caught by route_check `via_overlap`. Vias of 0.5 / 0.3 mm
  cannot get closer without their pads overlapping.
- f01 (caught incidentally), f04 (DRC) and x01 (K-reference).
- Controls h01c, h03b and h05c are each caught by DRC.
- The ACT_GATE single vias are fail-safe: each FET keeps its own bias (D-R18-02).

Compared with round 22's gate report afterwards: it has none of these. Its R22-GATE-01 and -02 are the parents of -01
and -04.

## Limits

- No full `r10_build.sh` of a generator-edited copy: the script changes to the git top level, which is the canonical
  tree.
- The hot-plug solve was reused where the electrical inputs were unchanged.
- Self-tests ran on d01 and h01 only.
- What an open does to U4 and to VCAP is an Inference.
- At hand-back, the worktree showed uncommitted edits to tracked files (`tools/check_r10.py`, AGENTS.md, docs,
  `r10_sch.py` and others). Another session made them during this review. Every probe here used
  `git archive c70d261`, so the findings are against the committed tools.
