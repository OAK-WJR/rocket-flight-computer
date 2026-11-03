# R10 round 28 fix pass: docs lane (2026-11-02)

Brief: `.supervisor/r28_fix_docs_brief.md`, then the root's final binding message. Base commit `19dd0b5`, board
`a0ec075e…`. Inputs:
- the triage `round28_triage.md` / `.json`;
- the three other lanes' hand-backs: `round28_fix_cad.md` / `.json` (D-R28-01 … -04), `round28_audit_pq.md` §4 and
  `round28_audit_proc.md` "Siblings in other files";
- the source of rule 3's figures, `round23_safety_severity_check.md`.

This is the final state. In the last pass this lane was the only one editing, and root allowed it to edit
docs/ORDERING.md, docs/R10_VEHICLE_HANDOFF.md and `parts_qualification.md` as well as its own files (STATUS.md,
AGENTS.md outside §2, M3_R10, FMEA, REQUIREMENTS, R10_VALIDATION, AVA_LAYOUT).

**Bound** (read from the files at the end; root confirmed the three hashes):

| Item | Value |
|---|---|
| PCB | `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (unchanged; build 3 on the final tree reproduced it, with `tools/check.sh` exit 0) |
| `parts_budget.json` | `4267634220f4254aef28dfc9756c68b29784560c11b994c14274790dd631fab2`; lines 91–92 5.8808312447840425 / 4.388490666810671 V |
| Binding note | `a40e21a4c115d88bcfdfecedada26e5253a0fef8c8b0972b6bba5c5aeabce046` (root, after this hand-back: `30796f5e…`, regenerated for the DS15034 Table 2 citation, D-R28-04) |
| Decisions | D-R28-01 … -04; 227 unique D IDs through D-R28-04, 101 after the ledger |
| Tests | R10 268, route 72, the rest unchanged; hot-plug 2304 cases, 0 failures; fab outputs changed only in their creation dates |

**Constraints kept:**
- AGENTS §2 byte-identical to HEAD (md5 `e3bdcdaa…`);
- no CAD, generator, tool, decision-record or git change;
- no local absolute paths added;
- links: 174 checked in the ten edited docs and 157 across `docs/*.md` and README.md, 0 bad.

## Items

| Item | Files and statements changed |
|---|---|
| R28-TRI-01 | FMEA's R10 row: the bus / continuity dividers (two 5.1 kΩ tops in series, two parallel 2 kΩ bottoms, 10 nF) read directly by PC0 / PC5, with no double-fault pin-current limit (netlist checked; no R168 / R170 / R172) |
| R28-TRI-03 (docs) | STATUS's round 27 entry and R10_VALIDATION's R27-TRI-02 row: 5.881 / 4.388 V (5.880831 / 4.388491 V at 1.561 A; D-R28-01). parts_qualification's stall input and budget hash were already bound to the new budget by audit lane A |
| R28-TRI-05 / -09 and rules 3 / 4 | Details below |
| R28-TRI-06 | R10_VALIDATION's R23-MCU-04 row: "parts_qualification corrected in the round 28 fix pass" (audit lane A made the correction: TT_u, Table 9 p70) |
| R28-TRI-07 | REQUIREMENTS F4: about 64–84 % of stall over flight 2's derived envelope (77–84 % nominal to high; Inference) |
| R28-TRI-08 | REQUIREMENTS: the stale "525 s" dropped; the round 23 re-check (about 1200 s) is recorded |

**R28-TRI-05 / -09, and rules 3 and 4 against the generated texts.**
- M3_R10 "Firmware" rule 3, FMEA I-2 / H-2 and R10_VALIDATION §1's QSPI_IO2 / PE4 row now state the same facts as the
  CAD lane's rule 3 and ORDERING 8.3:
  - "with the MCU driving IO2 high" and "in all but one modelled corner";
  - the full Inference label: driver resistances, flash drive, the AON7524 sub-amp curve and the match thermal model;
  - the first article before first power and coating, the board unpowered (pack and USB disconnected), resistance mode
    and both polarities;
  - "above 0.9 kΩ, or open, both ways", and a beep or under 100 Ω either way is a bridge: reject;
  - 0.91 kΩ labelled Calculation, the clamp reading Inference.
- M3_R10 rule 4 and R10_VALIDATION §1's Q120 row now carry rule 4's pass criterion. At first article, before coating,
  with PC1 high and a dummy in J121:
  - |VGS| at R120.2 / C120.2 against R120.1 of at least 4.5 V;
  - BAT_IN − RAW_ACT above 0.2 V during the dummy-load fire fails;
  - the 1.128 / 1.063 A labelled "AONR21357 VSD p2; Calculation / Inference: the fire budget's hot Q124 factor is
    inferred".
- ORDERING's QSPI and Q120 steps (audit lane B's) were checked against the generated texts; they already agree.

## Siblings fixed (routed by the CAD and audit lanes)

| Where | Before → after |
|---|---|
| M3_R10 round 20 change table (AUX clamps) | "centre to centre 6.23 / 6.18 → 4.08 / 4.18 mm (3.16 / 3.19 mm pad edge to pad edge)" → straight-line centre to centre 6.23 / 6.18 → 3.157 / 3.194 mm; 4.08 / 4.18 mm along the track (3.864 / 3.964 mm on `a0ec075e…` since D-R24-17); pad edge to pad edge 1.865 / 1.900 mm; the earlier mislabel noted |
| R10_VALIDATION R20-RTE-05 row (history) | Annotated with the same correction |
| R10_VALIDATION §6 | Correct labels and the current track lengths |
| M3_R10 Power (USB-only) | "attach load (nominal 514.1 µF, 2.416 mC)" → 516.1 µF behind U10 (514.1 µF on VLOGIC plus C86 / C98, 1 µF each, checked in the netlist), 2.426 mC, 5.35–6.98 ms |
| R10_VALIDATION §4 "USB startup" | The same correction |
| R10_VALIDATION round 10 record | Annotated with the current figure |
| R10_VALIDATION §5 | DS15034 "Table 2 pp10–11" → "Table 2 p11" |
| ORDERING 8.1 U4 row | Same fix |
| M3_R10 "Firmware" port endpoint rule, REQUIREMENTS F9, R10_VALIDATION §3 | "PORT_4V8 rises about 44 ms or more before 3V3 (Calculation)" → "can rise tens of ms before 3V3", with the D-R28-04 derivation (166–196 V/s; 3V3 regulates about 21–26 ms into the slew), labelled Calculation / Inference |
| R10_VALIDATION owner row 26 | U400 / L400 "8.7–13.3 mm away" → "8.7–13.4 mm away, centre to centre" |
| FMEA header, REQUIREMENTS F8, R10_VALIDATION row 2 residuals, §1 and §2, M3_R10 retained deviations | The cold-screen nominal figures (99.369 / 99.338 / 146.23 mV, and 96.2 / 96.1 / 102.0 / 55.5 mV at Vf 0.30 V) labelled Calculation / Inference (the BAT54 drop at that current) |
| AGENTS §1 shorted-igniter row | "34.853 ms (calculated)" → Calculation on allocations / Inference, as the generated GAP-5 obligation now says |
| R10_VALIDATION round 27 fix pass | "now `ecc45417…` / `e8f10fb3…`" → "then …; `4267634…` / `a40e21a4…` since round 28" |
| ORDERING 8.2 | "These are the round 26 fix pass's build results" → reproduced by the round 27 and 28 builds, which re-exported the package with only its dates changed and re-bound the manifest |

**Correction to this lane's interim hand-back.** The interim version listed "the 44 ms port-supply lead (U11's slew
formula)" as a correct pure Calculation. It was not. Audit lane B showed that 44 ms was VLOGIC's whole slew to 7.4 V, not
a lower bound on the lead over 3V3. The figure is now corrected everywhere and labelled Calculation / Inference.

## AGENTS §2.5 class sweep (item 7, from the interim pass)

The figures resting on inferred inputs were relabelled Calculation / Inference:
- C87's X7R bias allowance, in its 0.72× minimum, behind the EN chatter, turn-on and window figures;
- the fire budget's conditional inputs and Q124's inherited hot factor, behind the four-stall currents and rule 8's
  corner;
- the hold-up model's capacitance, allocations and efficiencies;
- Q122's conduction, behind |VGS| 4.74 V / 31.9 ms.

Where:
- M3_R10's current state, CH1 pyro, Power and Firmware;
- FMEA's R10 rows, REQUIREMENTS and the owner rows;
- AGENTS §1 and STATUS.

This pass extended the sweep in three ways:
- the cold-screen nominal figures, the 34.853 ms guard and the port supply's lead are labelled;
- ORDERING, the handoff and `parts_qualification.md` were re-scanned, and audit lanes A and B had already labelled their
  EN, hold-up and fire-budget figures;
- the CAD lane labelled five more generated obligations (D-R28-03).

**Left as Calculation** (pure arithmetic on component values or datasheet figures):
- the EN divider 2.03 / 2.06 V;
- the J440 chafe EN 1.87 / 1.28 V;
- D402's 5.7 mV;
- the bench-ramp window 4.29–4.80 / 4.72–5.25 V;
- Q122's 7.1 µs;
- R134's 22–29 W;
- the off-state 0.218 / 0.554 V;
- the USB-only figures, on stated allocations;
- the wire-bend geometry.

## Round 28 records

- **STATUS:**
  - status line, with D-R28-01 … -04 and the two audit lanes;
  - the round 28 entry, finalised. It covers the four lanes, firmware rules 3 and 4, the §2.5 sweep, the pack sag, audit
    lane A (about 35 more stale statements), audit lane B (17 steps) and the routed siblings. Software tests, DRC / gate,
    simulation and physical tests are kept separate;
  - the decision count, 227 through D-R28-04.
- **R10_VALIDATION:**
  - the round 28 index dispositions, now with decision IDs and the audit lanes' figures;
  - "Round 28 fix pass": the four lanes, the hashes, tests, DRC / gate, hot-plug and fab;
  - "Decisions after the ledger": heading and rows D-R28-01 … -04;
  - owner row 20 (227 / 101), the inventory basis (101 IDs) and §12 (227).
- **M3_R10:**
  - summary and the "28 fix pass" review row, with D-R28-01 … -04;
  - a new "Round 28 fix pass" checks bullet;
  - the fab-package note (round 28 builds re-exported, dates only);
  - the decision counts, in two places.
- **AGENTS:** the status paragraph, with D-R28-01 … -04 and the two audit lanes.
- **parts_qualification:** the status line "(D-R28-01 … -04 and two audit lanes) left the board unchanged".
- ORDERING's and the handoff's status lines (audit lane B's) already named rounds 29 and 30.

## Completeness sweep

`git grep -n` over docs/, STATUS.md, AGENTS.md and `m3_design/assembly_review/sources/` for the CAD lane's residual list
(`5.456 * (1.46`, `1.46 + aux_A`, `5.881014`, `4.388745`, `4.389`, `ecc45417`, `e8f10fb3`, `it must read open`,
`fire_current_GAP1 model, Calculation,`, `Calculation, D-R25-02`, `Calculation, R26-TRI-03)`,
`cannot trip U9 (Calculation, R20`, `(0.7 / 1.0 V drop),`, `44 ms or more`, `record the dummy-load drop`,
`First article, before coating`, `pad edge to pad edge, D-R20-09`, `3.16 / 3.19 mm pad edge`) and this pass's own
replacements (`514.1`, `2.416`, `5.33–6.95`, `pp10–11`, `8.7–13.3`, `(calculated)`):

| Residual | Why it stays |
|---|---|
| `5.881014` / `4.388745` / `4.389` / `ecc45417` in parts_qualification's budget-hash chain and stall-input history; STATUS's round 27 entry; R10_VALIDATION's R27-TRI-02 and R28-TRI-03 rows | Labelled history (what D-R27-01's code gave) or quotes of the error |
| `ecc45417` / `e8f10fb3` in R10_VALIDATION's round 27 fix pass | Annotated "then …, … since round 28" |
| `it must read open`, `44 ms or more` in the R28 index, STATUS's round 28 entry and parts_qualification's labelled "earlier" figure | Quotes |
| `3.16 / 3.19 mm pad edge` in M3_R10's round 20 change table, R10_VALIDATION's R20-RTE-05 row and parts_qualification | Each now says it was a mislabel, with the correct figures |
| `514.1` | parts_qualification and M3_R10, as VLOGIC's share; R10_VALIDATION's round 10 record (annotated) |
| `Table 2 pp. 10-11` in `m3_design/r10_sch_check.py:361`, so in the binding note; `Table 2 pp10-11` in R10_DECISIONS:3020 | **For root:** the generator (CAD file); the decision is a record |

## Not done or not verified

- No board, generator, check, decision-record or git change by this lane.
- The relabelled figures keep their values; this lane did not re-run the EN, hold-up or fire models. Rule 3 / rule 4
  and the cold-screen figures come from the generated texts, the audit lanes' derivations and the netlist.
- No physical test. Rounds 29 and 30 are planned on `a0ec075e…`.
