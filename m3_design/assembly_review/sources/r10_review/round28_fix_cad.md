# Round 28 fix pass: CAD lane (generators, generated text, checks)

## Scope

- **Brief:** `.supervisor/r28_fix_brief.md` items 1-3, on `round28_triage.md` / `.json`: R28-TRI-03, R28-TRI-05,
  R28-TRI-09, the sweep of the generated obligations for other unlabelled inferences, and the records.
- **Root's additions:**
  - rule 3 says what docs/M3_R10.md and ORDERING 8.3 now say: the MCU driving IO2 high, all but one modelled
    corner, before first power, unpowered, "or open";
  - audit lane B's two siblings (`round28_audit_proc.md`): the port supply's lead over 3V3 and rule 4's Q120 pass
    criterion.
- **Base:** `19dd0b5`, board `a0ec075e…`.
- **Records:** D-R28-01 … D-R28-04 in `sources/r10_design/R10_DECISIONS.md` (record index 227 through D-R28-04), and
  a correcting note on D-R27-01 (its code used 1.46 A).
- **Rules kept:**
  - Changes went through the generators only; nothing in the CAD was hand-edited.
  - AGENTS section 2 holds, and every check is unchanged or stricter (more test pins).
  - No git state was changed.
  - The docs lane's, audit lane A's and audit lane B's files and other review records were not touched.

## Board and builds

- **PCB SHA-256:** `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, **unchanged**.
  - Build 1 (1677 s, exit 0) reproduced it with the brief's items and the triage's rule 3 wording.
  - Build 2 was stopped after 207 s when the root's second addition arrived; its tree was not final.
  - Build 3, on the final tree (1671 s, exit 0), reproduced it again and ended with `tools/check.sh` exiting 0.
  - The hash never changed, so no second build of the same tree was needed.
- **`parts_budget.json`:** SHA-256 `ecc45417…` -> `4267634220f4254aef28dfc9756c68b29784560c11b994c14274790dd631fab2`.
  - Line 91: `"pack_7V4_four_stall_loaded_V": 5.8808312447840425,`
  - Line 92: `"pack_6V0_four_stall_loaded_V": 4.388490666810671,`
  - Both match the brief's 5.880831 / 4.388491 V, and they are the file's only change.
- **Binding note:** SHA-256 `e8f10fb3…` -> `a40e21a4…` (build 3) ->
  `30796f5ece9f3660264ca855dd6e4c1dbd8f97ee3f37983aed200ea27ef32ede` (item 7's DS15034 citation, the final note).
  - Eight obligations changed: the port map, GAP-5, obligation 15 (port supply lead), the chatter text, the IMU
    obligation and rules 3, 4 and 8 (indices 2, 7, 15, 17, 34, 38, 39, 43).
  - The board, netlist, pin table and circuit hashes in it are unchanged. K-binding passes.
- **Fab outputs:** only creation dates changed, in the Gerber zip and the two assembly PDFs (checked).
  - BOM, owner BOM, CPL and paste (249 / 381) are byte-identical, and the manifest's inputs are unchanged.
  - The builds' own `r10_fab.sh` re-exported the package; no networked run was needed, and the supplier evidence
    still binds.
- **Hot-plug model:** inputs and results byte-identical. 2304 cases, 0 failures; minimum -14.807 V (limit -15.0),
  steepest fall 8.995 V/us (limit 10), steepest rise 5.088 V/us (limit 100).

## Items

| # | Item | Before -> after | Files |
|---|---|---|---|
| 1 | R28-TRI-03 (D-R28-01) | `loaded_pack` power 5.456 V x (1.46 A + aux_A) -> 5.456 V x `port_A`, where `port_A = 1.461 + aux_A` is the variable `ports_w` now also takes. Lines 91-92: 5.881014 / 4.388745 V -> 5.880831 / 4.388491 V. | `m3_design/r10_parts.py`; regenerated `parts_budget.json` |
| 2 | R28-TRI-05 (D-R28-02) | Rule 3's meter check: "it must read open" -> the triage's both-polarity criterion with the root's additions (before first power, board unpowered; intact reads above 0.9 kΩ, or open, both ways; a beep or under 100 Ω either way is a bridge: reject; the clamp reading labelled Inference). | `m3_design/r10_sch_check.py`, `tools/test_r10_check.py`; regenerated binding note |
| 3 | R28-TRI-09 and the sweep (D-R28-03) | Rule 3's fight figures carry the triage's label; five more obligations (AUX allowance, GAP-5 bound, chatter, rule 4, rule 8) name their inferred inputs. | `m3_design/r10_sch_check.py`, `tools/test_r10_check.py`; regenerated binding note |
| 4 | root's siblings (D-R28-04) | Obligation 15: "rises about 44 ms or more before 3V3" -> "can rise tens of ms before 3V3" with the labelled derivation (3V3 regulates about 21–26 ms into the slew). Rule 4: "record the dummy-load drop" -> the Q120 pass criterion (\|VGS\| at least 4.5 V; BAT_IN − RAW_ACT above 0.2 V fails). Rule 3: before first power. | `m3_design/r10_sch_check.py`, `tools/test_r10_check.py`; regenerated binding note |
| 5 | records | D-R28-01 … -04; D-R27-01 annotated twice (its What and its figures). | `R10_DECISIONS.md` |
| 6 | D-R21-07 annotation (root, from audit lane A) | D-R21-07's "3.157 / 3.194 pad edge to pad edge" annotated, dated 2026-11-02: those are straight-line pad-centre distances; pad edge to pad edge is 1.865 / 1.900 mm; the J440 clamp paths on `a0ec075e…` are 3.864 / 3.964 mm of track (4.075 / 4.175 mm on `5516eeec…`, before D-R24-17). | `R10_DECISIONS.md` |
| 7 | DS15034 citation (root, from the docs lane; D-R28-04 note) | IMU obligation: "Table 2 pp. 10-11" -> "Table 2 p. 11", checked on the PDF. D-R19-11's line also carries a note. | `m3_design/r10_sch_check.py`, `tools/test_r10_check.py`, `R10_DECISIONS.md`; regenerated binding note |

### Item 1 (R28-TRI-03)

- `port_A = 1.461 + aux_A` (camera 1 A, radio 0.3 A, GPS 0.15 A, 11 mA, AUX 0.1 A) is defined once.
  - `ports_w = [buck_min * port_A / .85, buck_max * port_A / .80]` is the same expression as before, so its values,
    the battery-break loads and the fire budget (5.713 V, 1.279 A) are unchanged.
  - `loaded_pack`'s power is `5.456 * port_A` = 8.517 W.
- Re-solved before the build: 5.8808312 / 4.3884907 V; only those two budget keys differ.

### Item 2 (R28-TRI-05)

- **Triage's criterion:** "it must read open" became the both-polarity criterion. Build 1 carried that wording.
- **Root's additions,** taken from docs/M3_R10.md / ORDERING 8.3: before first power, the board unpowered, "or
  open", and the clamp reading labelled Inference.
- **Final first-article sentence:** "First article, before first power and coating: inspect U1 pins 1–5 for
  bridges, and, with the board unpowered (pack and USB disconnected), meter U3.3 (QSPI_IO2) to R127.1 (the PE4 gate
  network) in resistance mode, both polarities: an intact board reads above 0.9 kΩ, or open, both ways (red lead on
  R127.1: a diode drop plus about 0.91 kΩ through the U1 / U3 input clamps; reversed: open or slowly rising); a
  continuity beep or under 100 Ω in either polarity is a bridge: reject (0.91 kΩ is R127's 1 kΩ in parallel with
  R126 + R128, Calculation; the meter's reading through the clamps is an Inference)."
- **Full rule 3:** under "Final texts" below.

### Item 3 (R28-TRI-09 and the AGENTS 2.5 sweep)

- **Rule 3:** "... at least 50× below the 0.30 A no-fire (Calculation / Simulation; driver resistances, flash drive,
  the AON7524 sub-amp curve and the match thermal model are Inference); firing needs ...".
- **Sweep:** all 49 obligations plus `port_states`, `imu` and `fire_timing`, each read against its inputs. Labelled:
  - **Port map:** the 100 mA AUX allowance rests on U401's inferred 110 C/W theta-JA. It now reads "(U401 thermal
    floor: junction <= 125 C at the 70 C bay with the inferred 110 C/W theta-JA, Inference; parts_budget.json)".
  - **GAP-5:** the 34.853 ms fault bound is a sum of allocations. It now reads "(Calculation on allocations: the
    0.2 / 0.5 / 1.5 ms need bench tests, and the 1.5 ms covers a 0.74 ms gate-discharge model whose 0.4 V off criterion
    and hot gate charge are Inference; parts_budget.json pyro_fault_GAP5)".
  - **Chatter:** the drop-out times and window limits are now "Calculation / Inference". The note names C87's 0.72 x
    minimum (X7R DC-bias loss taken as at most 6 % without the maker's curve, D-R19-10) and the fire budget's 5.71 V
    point (its hot Q124 factor is inferred). The 30-130 ms turn-on is marked as the same model.
  - **Rule 4:** 1.128 / 1.063 A now cite AONR21357's VSD (p. 2) and say "Calculation / Inference: the fire budget's hot
    Q124 factor is inferred".
  - **Rule 8:** the fire-model corner and the hold-up are now "Calculation / Inference". The hold-up note says the loads
    are the budget's allocations and C84 has no cold-capacitance factor.
- **Unchanged:** items already labelled Inference (PA15, trace override, VREFBUF, back-feed, R5-MCU-04's Rev 11
  limits, rules 7 / 10 / 12, the IMU lever arm's z), and datasheet or plain-arithmetic figures (watchdog, deglitch,
  W25Q erase, IMU codes, VIH, dividers).
- **Missed by this sweep:** the port supply's lead over 3V3 (obligation 15), which I took for a datasheet
  calculation. Audit lane B showed that its 44 ms was VLOGIC's full slew, not a lower bound; item 4 (D-R28-04)
  corrects and labels it.

### Item 6 (D-R21-07 annotation)

- **Measured with pcbnew:** check_r10 `port_clamps` on the board, plus pad shapes. The figures match audit A.

| Board | J440.3 -> D440.1 track path | J440.4 -> D441.1 track path | Centre to centre, straight | Pad edge to pad edge (B.Cu) |
|---|---|---|---|---|
| `a0ec075e…` (and `92c3ad59…`) | 3.864 mm | 3.964 mm | 3.157 / 3.194 mm | 1.865 / 1.900 mm |
| `5516eeec…` (before D-R24-17) | 4.075 mm | 4.175 mm | 3.157 / 3.194 mm | 1.865 / 1.900 mm |

- **No build needed:** this is a records change only.

### Item 7 (DS15034 Table 2 page)

- **The PDF:** in `ism6hg256x.pdf`, DS15034 Rev 1, Figure 5 (pin connections) is on p. 9 and p. 10 is section 3.1 /
  Figure 6. Table 2 (pin description, pins 1-14 and its notes) is on p. 11 alone, and p. 12 starts section 4.
- **Generator:** "(DS15034 Rev 1 Figure 5 p. 9 and Table 2 pp. 10-11; DS14623 Rev 1 p. 9)" -> "... and Table 2 p. 11 ...".
- **Shortest valid path, as the root asked:**
  - The build's own step, `r10_sch_check.py --project … --board … --binding-note …` with the pinned 10.0.7 CLI,
    regenerated the note. It runs the schematic contract (ok) before writing. Only line 606 changed.
  - `check_r10 --only K-binding`: OK.
  - `test_r10_check` SchematicContract and BindingEvidence: 11 tests, OK. The test now pins "Figure 5 p. 9 and
    Table 2 p. 11" and rejects "Table 2 pp. 10-11".
  - Per the root, I ran neither `tools/check.sh` nor a full build for this item; root runs check.sh on the final tree.
- **Residual hits:** `round19_fix_cad.md`:80 and :287 and `round20_parts.json`:78 and :111 (review records, history).

## Final texts (binding note)

- **Rule 3:**

  > R23 firmware rule 3, QSPI_IO2 / PE4 bridge (R23-SAFETY-08 (1); verified Minor by round23_safety_severity_check.md). Physics: Q124's gate capacitor is C126, 220 nF, not C128 (100 nF, on the drain); the gate time constant is 47–53 µs; a steady IO2-against-PE4 fight with the MCU driving IO2 high puts 1.19–1.98 V on the gate and fires the match after about 0.55 ms in all but one modelled corner; page-program logging at a QSPI clock of 25 MHz or more stays at most 6 mA RMS, at least 50× below the 0.30 A no-fire (Calculation / Simulation; driver resistances, flash drive, the AON7524 sub-amp curve and the match thermal model are Inference); firing needs a sustained IO2-high pattern. Ground refusal: before PC1 goes high, run a QSPI quad read-verify of a known pattern, and refuse on any mismatch: the bridge corrupts quad reads. QSPI use while PC1 is high: PE2 stays in its QSPI alternate function, never a GPIO driven high; no memory-mapped or parked quad reads; no long all-ones writes at a low clock; the flash output drive is not at 100 %. Cold screen: during part of the passive cold screen, run sustained QSPI traffic and toggle PC14 and the servo PWM; refuse if CONT or BUS moves out of band. First article, before first power and coating: inspect U1 pins 1–5 for bridges, and, with the board unpowered (pack and USB disconnected), meter U3.3 (QSPI_IO2) to R127.1 (the PE4 gate network) in resistance mode, both polarities: an intact board reads above 0.9 kΩ, or open, both ways (red lead on R127.1: a diode drop plus about 0.91 kΩ through the U1 / U3 input clamps; reversed: open or slowly rising); a continuity beep or under 100 Ω in either polarity is a bridge: reject (0.91 kΩ is R127's 1 kΩ in parallel with R126 + R128, Calculation; the meter's reading through the clamps is an Inference).

- **Rule 4:**

  > R23 firmware rule 4, bus voltage (R23-SAFETY-05): on the ground, after PC1 goes high and a 100 ms settle, the powered BUS must read at least 0.96 × the pack voltage derived from VLOGIC_SENSE, else refuse (this catches Q120 left off and the bus fed through its body diode). Qualify the band on first articles. Verified Minor: four stalls give 1.128 / 1.063 A (0.7 / 1.0 V drop: AONR21357 VSD typical / maximum at 1 A, p. 2; Calculation / Inference: the fire budget's hot Q124 factor is inferred), 0.93–1.01× the 1.125 A floor but at least 1.39× the maker's 0.75 A all-fire and at least 1.04× its 1.00 A recommended minimum. A first-order thermal model fires the match in 4–5 ms, inside the 20 ms pulse (Inference). At first article, before coating, with PC1 high and a dummy load in J121: ACT_GATE at R120.2 / C120.2, against Q120's source at R120.1, must settle at |VGS| of at least 4.5 V (a Q120 gate cut off from R121 sits near 0 V), and during the dummy-load fire BAT_IN − RAW_ACT above 0.2 V fails the board (R23-SAFETY-05's criterion: Q120's body diode adds 0.7–1.0 V). Since D-R24-02 each gate drive has a second barrel (Q120 (16.2, 73.3) + (15.4, 72.85), Q121 (11.14, 71.7) + (11.74, 72.3)): leaving Q120 off this way takes two opens (D-R24-19).

- **Obligation 15 (port supply lead), the changed sentence:**

  > a device on J410 / J420 / J440 must drive its TX high at no more than 3.6 V, because PORT_4V8 can rise tens of ms before 3V3 (the 470 nF U11 soft-start (C85) slews VLOGIC at about 166–196 V/s after its settling time, TI SLVSEA3F Table 9-1 p. 13 scaled to 470 nF, and U2 (AP63203) starts at 3.3–3.7 V with a 4 ms soft-start, Diodes DS41326 p. 5, so 3V3 regulates about 21–26 ms into the slew; Calculation / Inference: the table is scaled linearly and the settling time is not quantified; measure the PORT_4V8-to-3V3 lag on first articles) and an FT pin allows only 4.0 V while VDD = 0 (DS12110 Rev 8 Table 119 p. 212; R20-MCU-02).

## Checks and tests

- **Build:** build 3 on the final tree, exit 0. Results:
  - r10_sch_check OK;
  - every stage check;
  - DRC 0, unconnected 0, schematic parity 0, ERC 0;
  - check_r10 37 / 37 OK (K-binding included);
  - route_check 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers as before;
  - fab content checks and the manifest.

  `tools/check.sh` ran as the build's last step and exited 0.
- **After build 3:**
  - `R10_DECISIONS.md` and the hand-back changed.
  - Item 7 changed `r10_sch_check.py`, `test_r10_check.py` and the regenerated binding note. Their checks are listed
    under item 7.
  - Root runs check.sh on the final tree.
- **Tests:** all OK in build 3 (and in build 1): shell 11, procurement OK, fab validation 34, fit 33, paste 16, R10
  parts 5, route 72, R10 268 (6 numpy skips), numpy hot-plug / plate 6.
  - Extended: `test_r23_binding_note_rules_and_pin_table`. It adds 16 required phrases (rule 3's criterion and
    qualifiers, rule 4's Q120 criterion, the port supply lead, the nine labels) and rejects 12 old forms.
- **Not run:** no physical test.

## Residual grep hits, by file

Every tracked text file was swept for each replaced value, phrase or hash:
`5.456 * (1.46`, `1.46 + aux_A`, `5.881014`, `4.388745`, `4.389`, `ecc45417`, `e8f10fb3`, `it must read open`,
`U401 thermal floor, parts_budget.json)`, `fire_current_GAP1 model, Calculation,`, `Calculation, D-R25-02`,
`Calculation, R26-TRI-03)`, `cannot trip U9 (Calculation, R20`, `(0.7 / 1.0 V drop),`, `44 ms or more`,
`record the dummy-load drop`, `First article, before coating`, `pad edge to pad edge, D-R20-09`,
`3.16 / 3.19 mm pad edge` and `within the 36ms contract.`

**In this lane's files:**
- **`r10_binding_note.json`, the generators and the checks:** none. The binding note is regenerated.
- **`R10_DECISIONS.md` (history):**
  - D-R27-01, lines 4555-4557 and 4585, annotated;
  - the D-R28 records' own before figures (4640-4642, 4654, 4666, 4683, 4694-4695, 4707, 4715, 4727-4729);
  - D-R21-07, line 3563, annotated.
- **`tools/test_r10_check.py` lines 483-488 (deliberate):** the rejected old forms.
- **`tools/jlc_easyeda/pads.json` (coincidence):** `4.389` inside pad coordinates.
- **round 27 review records (history, sealed):** `round27_fix_cad.*`, `round27_fix_docs.md`, `round27_triage.*`.

**In other lanes' files, for root to route:**
- **Docs lane:**
  - STATUS.md:28 (`4.389`);
  - docs/M3_R10.md:132 (`3.16 / 3.19 mm pad edge`), :1100 (`First article, before coating`), :1109
    (`(0.7 / 1.0 V drop),`), :1112 (`record the dummy-load drop`), :1179 (`44 ms or more`);
  - docs/REQUIREMENTS.md:64 (`44 ms or more`);
  - docs/FMEA_REDUNDANCY.md:38 (`First article, before coating`);
  - docs/R10_VALIDATION.md:1756 and :2735 (`3.16 / 3.19 mm pad edge`), :2244 and :2288 (`4.389`), :2262
    (`ecc45417`), :2263 (`e8f10fb3`), :2290 (`it must read open`), :2532 (`(0.7 / 1.0 V drop),`,
    `record the dummy-load drop`), :2637 (`44 ms or more`).
  - Some of the R10_VALIDATION rows may be dated history; root decides.
- **Audit lane A (parts_qualification.md):**
  - :36 (`3.16 / 3.19 mm pad edge`);
  - :106 ("about 44 ms or more", quoted there as the earlier figure: history);
  - :493 (`5.881014` / `4.388745` / `4.389` V and the budget SHA `ecc45417`);
  - :700 (`5.881014` / `4.388745` V).
- **Audit lane B:** none.

