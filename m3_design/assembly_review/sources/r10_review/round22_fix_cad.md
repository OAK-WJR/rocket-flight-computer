# Round 22 between-rounds pass: CAD lane (hand-back)

## Scope

The brief is `.supervisor/r22_fix_brief.md`, items 1-5; item 5, the gate lens's three check items (R22-GATE-01..03,
`round22_gate.md`), came after the first build and went into a second. Round 22's lenses found 0 Critical / 0 Major on
`5516eeec…`, and rounds 22 and 23 are the closing pair on that board, so this pass changes only checks, one schematic
note and record wording.

Changes are in:
- **Checks and tests:** `tools/check_r10.py`, `tools/test_r10_check.py`.
- **Generator, note text only:** `m3_design/r10_sch.py` (the diagnostics sheet note), regenerated into
  `m3_design/assembly_review/diagnostics.kicad_sch` by the build.
- **Records:** `R10_DECISIONS.md` (D-R21-01 / -04 / -05 corrections; D-R22-01..07), `round21_fix_cad.md` / `.json`
  corrections.
- **Re-bound:** the fab package (the sheet hash changed; date-stamped outputs and the manifest).

Not touched: the board (PCB unchanged), every footprint, field and rule area; STATUS.md, AGENTS.md, docs/*.md and
parts_qualification.md (the docs lane's); no git state changed; AGENTS section 2 unchanged.

Machine-readable twin: `round22_fix_cad.json`.

## Board and build

PCB `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` (unchanged), 46 x 90 x 1.6 mm, 2,336,572 bytes;
215 footprints, 983 segments, 300 vias (167 GND), 1871.611826 mm track.

**Two complete `r10_build.sh` runs** (KiCad CLI 10.0.7, `NUMPY_PY=.supervisor/venv/bin/python`): the first for items
1-4 (1399 s), the second with the gate items (item 5, 1424 s). Each: exit 0, PCB `5516eeec…` again, `r10_fab.sh`
re-bound the package, `tools/check.sh` exit 0 (figures from the second):
- DRC 0 / unconnected 0 / schematic parity 0 / ERC 0; metadata / 3D audit, silkscreen outline, `r10_parts --check` and
  fit OK.
- check_r10: 36 / 36 rules OK (R10 CAD contract (full): OK). route_check r10: 0 failing (6 unrecorded noncritical
  leftovers, unchanged).
- Fab content checks and the six-output manifest pass.
- Files the first build changed (snapshot against the tree before it): `diagnostics.kicad_sch` and the four
  date-stamped fab outputs (both assembly PDFs, the Gerber zip, the manifest); 908 others identical. The second
  changed only the date-stamped fab outputs (checks only).

## Items

**1. The rest of JLC's hole table (R22-REQUIREMENTS-02, D-R22-01): done.**
- **JLC's rows, checked on the page** (https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-31): "PTH annular
  ring >=0.20mm" (multilayer, 1 oz: 0.20 mm recommended, 0.15 mm absolute minimum); "Via diameter should be 0.1mm
  (0.15mm preferred) larger than Via hole size"; multilayer drill 0.15-6.3 mm (vias 0.15 / 0.25 mm); "Min. Non-plated
  holes 0.50mm"; "NPTH pad annular ring >=0.45mm"; "NPTH to Track 0.2mm" (no separate NPTH-to-copper row).
- **Gate.** `check_r10.jlc_board_holes`, in K-rules, measures the board itself whatever the DRU says
  (`JLC_BOARD_HOLES`, tolerance 0.001 mm):

| Row | Floor | Board (least, where) |
|---|---|---|
| PTH annular ring (every flashed layer; true slot to copper outline) | 0.20 mm | 0.200 mm, J3's shell slots |
| Via annular ring | 0.05 mm | 0.100 mm (0.5 / 0.3 mm vias) |
| Plated hole | 0.15 mm | 0.30 mm (vias) |
| Non-plated hole | 0.50 mm | 0.60 mm (J3) |
| NPTH pad copper ring | 0.45 mm | no NPTH pad carries copper |
| NPTH hole wall to any copper, any layer | 0.2 mm | 0.200 mm, J3's NPTH to its GND SMD lands (0.201 with polygon arcs) |

- **J3's at-limit row.** J3's NPTH locating holes sit 0.200 mm from its GND SMD lands: HRO's own land pattern, at
  JLC's 0.2 mm and not below. It is held three ways: the DRU rule "HRO M-12 internal SMD lands to locating holes" sets
  that pair's DRC clearance to 0.20 mm, K-lands pins the footprint by SHA-256, and this check holds the board to 0.2 mm.
- **Before -> after.** Before, the lens's seeds (J122.5 ring 0.10 mm, a J2 NPTH at 0.40 mm) passed DRC and check_r10;
  now each fails K-rules.
- **Seeds (each fails):** J122.5 ring 0.10 mm and 0.18 mm; a via ring of 0.025 mm; a 0.1 mm via hole; a J2 NPTH hole
  at 0.40 mm; a 0.20 mm copper ring on a J2 NPTH pad; a GND track 0.1 mm from a J2 NPTH hole.
- **A latent hazard found and fixed on the way.** `pth_inner_copper` and the new check now share `_copper_items`, and
  the hole points are copied out of their polygon: KiCad's `CPoint` returns a reference that dies with the polygon. A
  first refactor read freed memory and reported 0.000 mm walls; the board run caught it before any build.

**2. Single-point taps (R22-POWER-01 / -02, D-R22-02): done.**
- **Reworded:** the R85.2 / R430.2 entries now say that each via is a TPS2553's only ground (U10.2 with R7.2 in one
  B.Cu island; U402.2 in another), so an open floats the IC's ground (TI SLVS841G states no open-GND behaviour:
  Inference); bench USB or camera supply loss, no flight hazard.
- **New taps** (`SINGLE_OPEN_TAPS` 26 -> 33; `SINGLE_OPEN_EXCEPTIONS` 8 -> 15), measured on the board:

| Tap (net, source) | Single via | Consequence of an open |
|---|---|---|
| U10.2 (GND, J1.2) | GND (9.00,27.84) | U10's ground floats (Inference); bench USB loss |
| R7.2 (GND, J1.2) | GND (9.00,27.84) | CC1 Rd shares U10.2's island |
| U402.2 (GND, J1.2) | GND (32.30,59.50) | U402's ground floats (Inference); camera supply loss |
| R8.2 (GND, J1.2) | GND (9.95,30.60) | no CC2 sink; with R7's island open too, no sink at all; bench only |
| R60.1 (VLOGIC, U11.1 / U11.8) | VLOGIC (34.50,63.00) | R61 holds PA6 at 0 V: the firmware rule reads a permanent brown-out and sheds logging / UARTs (Inference; no pyro, deployment or servo effect) |
| U1.28 = PA4 (LOGIC_SOURCE_ST, U11.9) | LOGIC_SOURCE_ST (30.85,51.80) | PA4 floats; port UARTs may flap or stay off (Inference) |
| R91.1 (3V3, L1.2) | 3V3 (28.10,60.00) | PA4 can read "battery" on USB-only power (Inference) |

- Each becomes a second via (R60: or an F.Cu feed from C84.1) at the next board change.
- **Seeds:** each new tap with its entry dropped fails naming its via; an entry the board does not meet is stale.

**3. Diagnostics sheet note (R22-MCU-01, D-R22-03): done** (text only; netlist and board unchanged).
- Line 2 now reads: "Nominal 5.456 V (PORT_5V3 via U402) reads 0.496 V; a failed U400 passes RAW_PROTECTED (held under
  U9's OVLO, 9.77 V nominal) and reads about 0.89 V; even D8's 19.9 V clamp would read 1.81 V."
- **Checked:** R104 10 kOhm / R105 1 kOhm (1 %) give 1/11; 5.456 / 11 = 0.496 V. U9's OVLO: R82 2 MOhm / R83
  280 kOhm (0.1 %) with VOV(R) 1.20 V typ, 1.183-1.223 V (TI SLVSFC9C p9): 9.77 V nominal, 9.98 V maximum; 9.77 / 11 =
  0.89 V. D8 SMBJ12CA VC 19.9 V at 30.2 A (Littelfuse SMBJ datasheet); 19.9 / 11 = 1.81 V.
- **One change from the lens's wording:** "<= 0.89 V" holds at nominal only (about 0.92 V at the maximum OVLO threshold
  with 1 % divider parts), so the note says "about 0.89 V" and "9.77 V nominal".

**4. Record corrections (D-R22-04): done.**
- **D-R21-05** (R22-SAFETY-01): least RAW_ACT-to-GND 0.302 -> 0.300 mm (B.Cu RAW_ACT (22.8,61.4)-(22.8,63.875) to
  U11.6; KiCad shape collision 0.300001 mm; 0.302 was a 2 um step artefact). Also in the round 21 hand-back.
- **D-R21-01** (R22-PARTS): re-measured. J3.1 / J3.4 on In1, 1.375 / 1.345 mm, are slot wall to the VBUS via barrels:
  those vias keep pads only on F.Cu / B.Cu (KiCad's remove-unconnected mode), so In1 holds only their 0.3 mm barrels.
  The parts lens's 1.225 / 1.194 mm count a 0.6 mm pad there that the board does not have. The record now gives both
  bases rather than replacing the figures; the J3 slot shape itself was right in both measurements.
- **D-R21-04** (R22-REQUIREMENTS-01): the exemption rests on physics (470 kOhm feeds, tau about 50 ms, about 7 uA).
  Re-run of `r7_hygiene.gnd_spots`: a legal 0.5 mm GND via 0.671 mm from (10.8,69.2), (21.3,68.9), (19.675,66.6), at
  (10.2,68.9), (20.7,69.2), (20.275,66.3); none for (17.1,82.8).
- **"EN never exceeds 2.03 V"** (R22-DOCS_BINDING-04): in D-R21-05 and the round 21 hand-back, now "2.03 V nominal
  (<= 2.06 V with 1 % parts at 8.4 V; Calculation) while R81 is intact" (8.4 x 300 / 1240 = 2.032 V; 8.4 x 303 /
  1233.6 = 2.063 V).

**5. The gate lens's check items (R22-GATE-01..03, D-R22-05..07): done.** The gate lens reviewed `ec8cb98`, before
items 1-4; its seed scripts (`.supervisor/r22_gate/scripts/`, read only) became self-test seeds.
- **R22-GATE-01, K-rules (D-R22-05).**
  - Before: `dru_rules` read only a "(min N mm)" written first; `jlc_hole_table` counted a later rule as an override
    only on the exact pinned layer word. g01f (10 mil), g01g (6 mil), g01h ((opt) first), g01e (In1.Cu), "um" spellings,
    an F.Cu 0.21 mm rule and an 8 mil hole-to-hole rule passed the table.
  - After: every "(min ...)" in a constraint is read, after (opt) or (max) too, in mm, mil / thou, um or in (a bare
    number as mm); an unreadable one fails. Any later rule whose layer can meet the pinned one counts as an override
    (In*.Cu or "inner" for inner, F.Cu / B.Cu or "outer" for outer, any layer where the pinned rule has none). Each seed
    fails; a later 0.28 mm F.Cu rule does not. Refilled under g01f's DRU, KiCad honours 10 mil (J1.2 / J400.2 at
    0.255 mm) and K-rules names both the override and the walls.
  - Board measures added, independent of the DRU (D-R22-01 measured none of these): via hole wall to foreign copper on
    every layer >= 0.2 mm (JLC "Inner layer via hole to copper clearance 0.2mm", "Via hole to Track 0.2mm"; least 0.25
    mm); PTH hole wall to F.Cu / B.Cu copper >= 0.28 mm ("PTH to Track 0.28mm"; least 0.55 mm, J1.1); pad hole to pad
    hole >= 0.45 mm ("Pad Hole-to-Hole Spacing 0.45mm"; least 0.835 mm, J3's NPTH to J3.4). Seeds: a 3V3 In1 track 0.1
    mm from a via hole, a GND F.Cu track 0.2 mm from J122.1's hole, two J2 NPTH holes 0.3 mm apart: each fails.
- **R22-GATE-02, K-legends (D-R22-06).** Measured first: 20 Fab references sit beside their part's body box, the
  farthest 0.968 mm (D9); every stroke is 0.15 x height; no board-level Fab text. Now: each reference's ink centre
  within 1.5 mm of its own part's Fab body box (the courtyard box for the 14 parts with only a pin-1 dot or no Fab
  marks: U1-U5, D4, D121, Y1, J3, Q122, Q123, D120, D123, J2), stroke >= 0.1 x height or >= 0.05 mm, no board-level
  text on F.Fab / B.Fab. Seeds g08a (R134's 8.4 mm away: 5.147 mm from its 2512 body box), g08c (board-level "Q121"
  on Q120), g08d (R119's 0.005 mm stroke) and U1's 3 mm off its courtyard each fail.
- **R22-GATE-03, K-ports (D-R22-07).** Measured first: every clamp's GND pad reaches its own GND via through 0.7 mm
  of track (D400 / D401 0.8 mm). Now each clamp's GND pad must reach a GND via or plated GND pad through tracks only
  (not the pour) within 1.0 mm. Seed g07b (D420's stub and via removed, kept referenced) fails as reaching no via
  through tracks; D410's stub re-drawn 1.5 mm long fails over the bound.

## Tests

- **Added:** RealBoardSeeds test_r22_jlc_board_holes (8 seeds, two through K-rules),
  test_r22_monitor_and_ic_ground_taps, test_r22_dru_override_spellings (the gate's g01e / f / g / h and more, g01f
  end to end with a refill), test_r22_board_hole_rows, test_r22_fab_reference_placement_and_stroke (g08a / c / d) and
  test_r22_clamp_gnd_returns (g07b).
- **Changed:** test_r21_regulator_taps_survive_one_via_open (33 taps and their single points);
  SchematicContract.test_r21_sheet_notes (the new diagnostics line, the old one gone).
- **Counts in the build's check.sh:** shell 10, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route
  69, **R10 253** (6 NumPy skips; round 21's 247 + the six new tests), NumPy `HotplugNumerics Plate` 6: all OK.

## Not done

- D-R21-01's J3.1 / J3.4 In1 figures were not replaced by the lens's 1.225 / 1.194 mm: re-measured, 1.375 / 1.345 mm
  is the board's copper (the VBUS vias have no In1 pad); both bases are recorded instead (item 4).

## For the docs lane

- The new gate content: K-rules' board hole rows (D-R22-01, D-R22-05), the DRU unit / layer reading (D-R22-05), the
  seven new single-open taps (D-R22-02, each with its consequence for the retained-deviation list), the Fab reference
  reach / stroke / board-text rules (D-R22-06) and the clamp GND returns (D-R22-07).
- J3.1 / J3.4 In1: both measurement bases (D-R22-04).
