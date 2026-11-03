# R22 gate adversary (Claude)

Target `ec8cb98`; PCB SHA-256 `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` before and after (verified). **0 Critical / 0 Major / 3 Minor**, all gate gaps; no board copper found below a limit. Machine-readable twin: [round22_gate.json](round22_gate.json). Probe material: `.supervisor/r22_gate/` (ignored).

## Method

Each seed is an APFS clone of `git archive ec8cb98`, seeded with KiCad 10.0.7 pcbnew (zones refilled; removed items leaked) or a file edit. The post-board regeneration (budget, hot-plug, jlc_orient, export / bind / verify, binding note) then runs, followed by every check.sh checker with the copy's tools. A seed that failed to apply was never judged. The control passes every step. Gate-code edits were also run against the matching self-tests.

## Findings

**R22-GATE-01 (Minor): the JLC hole table misses overrides in other spellings.** `jlc_hole_table` reads only a `(min N mm)` written first, and treats a later rule as an override only when its layer is the exact pinned word. A re-pinned DRU override slips past it if it is written in mil or um, puts `(opt)` before `(min)`, or names a layer such as `In1.Cu` or `F.Cu`. probe/table_parse: 0 issues for each such case, 1 for the control.
- **g01f** (generator-consistent, 10 mil PTH override, re-pinned): the binding regenerates, KiCad honours the mil value (J1.2 / J400.2 fills at 0.255 mm), and the table is silent. Only the board measure catches it.
- **g01g** (6 mil = 0.152 mm via rule, under JLC's 0.2): every checker step exits 0.
- Via hole to inner copper, outer PTH to track and pad hole-to-hole have no board measure.
- *Fix (checks):* unit-aware, position-independent min parsing, with an unparsable min failing; any named-layer later rule counts as an override; add a board via-hole-to-inner-copper ≥ 0.2 mm measure.

**R22-GATE-02 (Minor): Fab designators are not tied to their part.** Three seeds pass every checker step:
- g08a: R134's Fab reference moved 8.4 mm away into open board.
- g08c: a board-level B.Fab text "Q121" on Q120's body.
- g08d: R119's reference drawn at a 0.005 mm stroke.

d06a / b / d / e and g08e are caught (K-legends), and g08b by DRC (library mismatch). *Fix (checks):* require own-part proximity, reject board-level Fab text, and set a stroke floor.

**R22-GATE-03 (Minor): port ESD clamp ground legs are not held.** g07b removes D420's 0.7 mm GND stub and its via, and passes every checker step. D420.2 then reaches GND only through the B.Cu pour, with the nearest GND vias 2.7–2.8 mm away. K-ports measures only the pin-to-clamp signal path. *Fix (checks):* each clamp's GND pad must reach a GND via within a recorded track bound.

## Fix verification

| Fix | Verdict | Evidence |
|---|---|---|
| D-R21-01 | partly | g01a / b / c / f02 caught by K-rules (SHA, table, J1.2 / J400.2 at 0.251). g09a / b / d (table edits, coordinated weakening) caught by self-tests. Override spellings slip past (GATE-01). |
| D-R21-02 | confirmed | g02a / g02b: U2.1 hangs on (23.20, 68.60). g03a / g03b: K-power plus a stale entry. g03c / g03d caught by self-tests. |
| D-R21-04 | confirmed | g05: route_check tiny_jog BAT_ENABLE (0.424 / 0.3 mm). |
| D-R21-05 | confirmed | g04a: K-power names vias (19.68, 66.60) and (21.30, 68.90). g04b (R81 10 mm up its run) is held only by the self-test position pin. |
| D-R21-06 | confirmed | d07 12.498 mm²; g06b 3V3 3.745 + RAW 7.447 mm²; g06c PORT_5V3 3.502 > 3.077 mm². |
| D-R21-07 | partly | d08 caught; g07d 5.475 mm > 4.5. The GND leg is not held (GATE-03). |
| D-R21-08 | partly | d06a / b / d / e and g08e caught; g08a / c / d pass (GATE-02). |
| Round 19 seeds | confirmed | 69 re-run: 63 caught, 6 pass by design (b09c, b12c, b16d, c02, c02b, c03), as in round 21. |

## Fix now (checks only, no board change)
- GATE-01: unit- and order-aware DRU parsing, a named-layer override rule, a via hole-to-inner-copper board measure.
- GATE-02: Fab reference proximity to its own part, no board-level Fab text, a stroke floor.
- GATE-03: a bound on each clamp's GND via distance (0.7 mm today).

## Closed
- g01d (generator rule at JLC's 0.30) is legal.
- g03e: exception reason text is not validated; the geometry is pinned.
- g09c: the floor constant is redundant.
- g07c collided with other copper and was not judged.
- f01b now duplicates the committed run, as expected.

## Limits
- The complete copy check.sh on the misses (g01g, g03e, g08a, g08c, g08d, g07b) was queued but not finished. These are shown to pass every checker step, not the self-tests.
- The generator-consistent re-runs of g01b–e, g01h and g07c2 had not finished. The first-pass g01b–e also failed K-binding incidentally, because the DRU-only edit broke r10_sch_check.
- No canonical edit, build, check.sh or git change.
