# Round 29 fix pass: CAD lane (generated text, test pins, records)

## Scope

- **Brief:** `.supervisor/r29_fix_brief.md` items 1-4, on `round29_triage.md` / `.json`: R29-TRI-02 (rule 3's gate
  time constant), R29-TRI-05 (the test pins), any generated text among R29-TRI-01's places, and the records.
- **Base:** `09a564e`, board `a0ec075e…`.
- **Records:** D-R29-01 and D-R29-02 in `sources/r10_design/R10_DECISIONS.md` (record index 229 through D-R29-02), and a
  correcting note on D-R28-03's test line.
- **Rules kept:**
  - Changes went through the generator only; nothing in the CAD was hand-edited.
  - AGENTS section 2 holds, and every check is unchanged or stricter (11 more pins, 2 more rejected forms).
  - No git state was changed.
  - The docs lane's files and other review records were not touched.

## Board and build

- **PCB SHA-256:** `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, **unchanged**.
  - One complete `m3_design/r10_build.sh` on the generator and test changes (1668 s, exit 0) reproduced it, and ended
    with `tools/check.sh` exiting 0.
  - `R10_DECISIONS.md` was edited during the build. No gate reads it (no tool or test references that file's content).
- **Binding note SHA-256:** `30796f5e…` -> `c5cd0fa313d3e973bf0542e806f82ae1bfea357943ec49d3c84e522449836cca`.
  - Its only change is rule 3's time-constant phrase (one line of the JSON).
  - The board, netlist, pin table and circuit hashes in it are unchanged, and K-binding passes.
- **`parts_budget.json`:** unchanged.
- **Fab outputs:** only creation dates changed, in the Gerber zip (27 date lines) and the two assembly PDFs (6 bytes
  each, same size).
  - BOM, owner BOM, CPL and paste (249 / 381) are byte-identical, and the manifest's inputs are unchanged. The
    supplier evidence still binds.

## Items

| # | Item | Before -> after | Files |
|---|---|---|---|
| 1 | R29-TRI-02 (D-R29-01) | Rule 3: "the gate time constant is 47–53 µs" -> "the gate time constant is about 47–58 µs over C126's ±10 % (53 µs nominal; Calculation, driver resistances Inference)". The 47.8 / 53.0 / 58.3 µs figures are the triage's, recomputed from round23_safety_severity_check.md's model (238.6 ohm, Ciss 2.25 nF). | `m3_design/r10_sch_check.py`, `tools/test_r10_check.py`; regenerated binding note |
| 2 | R29-TRI-05 (D-R29-02) | The pin "after a 30-130 ms EN turn-on delay" -> "after a 30-130 ms EN turn-on delay (the same model over C87 0.72-1.27 x)", plus pins for (a) through (f) below. Rejected forms added: "EN turn-on delay. Resume" and "47–53 µs". | `tools/test_r10_check.py` |
| 3 | R29-TRI-01, generated text | Of the triage's places, only rule 3's time constant is generated text, and item 1 labels it. A grep of the generators, checks and generated JSON for 9.6 V, 991 microstrain, 3.23 V, "Calculations on the budget", 1.540851 and "calculated 34.853" finds no R10 generated text. The only hits are R9 history evidence and `parts_budget.json`'s bare `fire_A` number. | none |
| 4 | records | D-R29-01 and D-R29-02 added. D-R28-03's "pins each new label" now carries "(Corrected by D-R29-02 …)". | `R10_DECISIONS.md` |

**The (a)–(f) pins,** each the exact generated text:
- (a) GAP-5: "and the 1.5 ms covers a 0.74 ms gate-discharge model whose 0.4 V off criterion and hot gate charge are
  Inference".
- (b) Chatter: "and the 5.71 V point is the fire budget's, whose hot Q124 factor is inferred".
- (c) Rule 8: "; the loads are the budget's allocations, and C84 has no cold-capacitance factor".
- (d) Obligation 15: "Calculation / Inference: the table is scaled linearly and the settling time is not quantified;
  measure the PORT_4V8-to-3V3 lag on first articles".
- (e) Rule 4, four pins:
  - "At first article, before coating, with PC1 high and a dummy load in J121:";
  - "against Q120's source at R120.1, must settle";
  - "(R23-SAFETY-05's criterion: Q120's body diode adds 0.7–1.0 V)";
  - "(0.7 / 1.0 V drop: AONR21357 VSD typical / maximum at 1 A, p. 2;".
- (f) Port map: "junction <= 125 C at the 70 C bay with the inferred 110 C/W theta-JA, Inference".

## Checks and tests

- **Build, final generator and test tree, exit 0.** Results:
  - r10_sch_check OK;
  - every stage check;
  - DRC 0, unconnected 0, schematic parity 0, ERC 0;
  - schematic contract and sheet replay OK;
  - metadata / 3D audit OK;
  - R10 CAD contract (full) OK, K-binding included;
  - route_check: 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers, as before;
  - fab content checks and the manifest OK.
- **Tests (check.sh inside the build), all OK:**

  | Suite | Tests |
  |---|---|
  | shell | 11 |
  | procurement | OK |
  | fab validation | 34 |
  | fit | 33 |
  | paste | 16 |
  | R10 parts | 5 |
  | route | 72 |
  | R10 | 268 (6 numpy skips) |
  | numpy hot-plug / plate | 6 |

  `test_r23_binding_note_rules_and_pin_table` was extended in place, so the count is the same as in round 28. Its
  D-R28-03 block now has 20 required phrases (was 9) and 14 rejected forms (was 12). The old rule 3 text contains
  "47–53 µs" and the round 27 chatter text contains "EN turn-on delay. Resume", so either revert now fails.
- **Not run:** no physical test.

## Residual grep hits, by file

Every tracked text file was swept for `47–53 µs`, `47-53 µs`, `EN turn-on delay. Resume`, `pins each new label` and
`30796f5e` (the old binding note).

**In this lane's files:**
- **`r10_binding_note.json`, the generators and checks:** none. The binding note is regenerated.
- **`tools/test_r10_check.py:507` (deliberate):** the rejected forms.
- **`R10_DECISIONS.md` (history):**
  - D-R28-03 test line 4707, annotated;
  - D-R28-04 line 4736, the old note hash;
  - the D-R29 records' own before text (4755, 4763, 4784, 4786, 4788).
- **Round 28 review records (history, sealed):** `round28_fix_cad.md` / `.json` (`47–53 µs` in the quoted rule 3,
  `30796f5e`) and `round28_fix_docs.md`.
- **`round23_safety_severity_check.json` (source, history):** its own 47–53 statement.

**In the docs lane's files, for root to route:**
- **The binding note hash `30796f5e…` given as current:** STATUS.md:35, docs/M3_R10.md:233 and
  docs/R10_VALIDATION.md:2314. It is now `c5cd0fa3…`.
- **History:** docs/R10_VALIDATION.md:2264.
- **Round 29 change rows, which quote the old form:** STATUS.md:18 / :21 and docs/R10_VALIDATION.md:2363 / 2366 /
  2379.
- **Coincidence:** docs/ORDERING.md:152 ("y 47–53").
- **Already fixed by the docs lane:** docs/M3_R10.md:1095, docs/FMEA_REDUNDANCY.md:39 and docs/R10_VALIDATION.md:2561
  no longer carry "47–53 µs".
