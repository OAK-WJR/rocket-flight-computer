# M3 requirements and implementation status

> Repository note: the complete projects and review packages of the historical candidates (CORE / PWR / UART / USB / GNSS / PDIAG) are not included. On this branch (`m3-assy-r10`) the repository holds the M3-ASSY-R10 KiCad project (a CAD candidate, not accepted), built from the hash-pinned R9 inputs by `m3_design/r10_build.sh`; R9's project (built from the committed, owner-accepted R8 sources, commit 9c8179b, by `m3_design/r9_build.sh`) stays on branch `m3-assy-r9` (R8 came from R7 by `m3_design/r8_build.sh`, R7 from R6 by `m3_design/r7_build.sh`, R6 from R5, R5 from R4, R4 from R3), plus the R1 board under `reference/m3_assy_r1/` that the v0.8.1 firmware is bound to. R8's project stays on branch `m3-assy-r8` (9c8179b) and R7's on `m3-assy-r7` (431025d). The older candidates are mentioned below only as the evolution record.

Last updated 2026-11-05 (R12 and R11 candidate sections below; R10 candidate section as of 2026-11-02; the rest as of 2026-10-25). Governing requirements: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md). M3-ASSY-R2 was the first candidate with every hardware function in the requirements; R3 dropped the GNSS (owner decision); R4 is R3 with its validation fixes; R5 is R4's circuit on a two-sided 46 × 100 mm board; R6 has one recovery channel, a GH camera connector and external radio/GPS ports; R7 is R6 with the GNSS and radio on the board, 46 × 118 mm, owner-accepted on 2026-10-18; R8 is R7's circuit re-placed and re-routed around R7's rigid RF strip and pyro block, owner-accepted on 2026-10-20; **M3-ASSY-R9 (R8's circuit laid out again from a clean sheet, 46 × 102 mm) is the current candidate, owner-accepted on 2026-10-25, and R8 is the accepted fallback.** All are CAD designs with a manufacturing package, not measured or flown boards.

## R12 candidate: M3-ASSY-R12 (R11's circuit pruned and re-sourced, one-sided four-layer board for JLC Economic, 46 × 100 mm; CAD candidate, NOT accepted)

**Status (2026-11-05).** Branch `r12-stage-d` (from `m3-assy-r12`); the R12 KiCad project is `m3_design/r12/`, built by `m3_design/r12_build.sh` (stages A–D: schematic, placement, frozen copper `r12_routes.tsv`, post stage from `r12_legends.tsv`, fab package). PCB `d776c5d7…` (full hash and metrics in [docs/M3_R12.md, "Current state"](docs/M3_R12.md#current-state)), 46 × 100 × 1.6 mm, four layers, every part on the top face. Not accepted, nothing ordered; R9 stays the accepted board. No review round has run on R12 yet. What the owner must accept or do: [docs/R12_VALIDATION.md](docs/R12_VALIDATION.md). Harness pin map and per-flight procedure: [docs/R12_VEHICLE_HANDOFF.md](docs/R12_VEHICLE_HANDOFF.md).

| Kind | Verified (with its record) | Not verified |
|---|---|---|
| *Software tests and CAD gate* | Board built twice with the same SHA-256; DRC 0 violations, 0 unconnected, 0 schematic parity; `r12_sch_check` OK (187 parts, 37 / 37 seeded faults); `tools/check_r12.py` every rule OK (S-1 … S-9, K-legends with D-R12-81's one waiver, K-reference, K-region, K-plane, K-fill); `route_check --profile r12` 0 failing, 2 allowlisted (D-R12-75A); R12 fab manifest and content checks OK; `tools/check.sh` exit 0 with the R12 board and fab package tracked (stageD.md §1, Measured, 2026-11-05). | No review round (stage F). |
| *Simulation and calculation* | Hot-plug: R10's model on R12's copper with C79 (D-R12-78), 2304 / 2304 required cases pass, minimum −14.255 V, steepest fall 9.251 V/µs (Simulation / Inference). Fire budget 4.726699 Ω, 1.249978 A at four stalls (+11.1 % over 1.125 A); EN / chatter, hold-up (2.23–6.12 ms from a break), PA6 corners, rail DC solves and IPC-2152, U6 supply ≥ 3.227 V (Calculation / Inference; stageD_analysis.md). | Plate model; signal integrity; PORT_4V8 at the ports under load is under the LR900's 4.5 V (owner item). |
| *Datasheet reads* | Stage A / B part choices (R12_DECISIONS D-R12-04 … -19, -49 … -52). | DS12110 alternate-function numbers of the stage C re-pins (read from KiCad's ST symbol only, O-R12-23); FXLS90322 dual-channel and LSM6DSVE datasheets (O-R12-21); 255 °C reflow ratings of most parts (O-R12-02). |
| *Physical, electrical and firmware tests* | None. | No board exists; no firmware; JLC DFM not queried. |

Cost (Live 2026-11-05): parts + feeder $61.88 per board at 2 boards, $44.38 at 5, against the $84.41 cap; all-in about $164 / $265 for 2 / 5 boards (Calculation); no part short (stageD.md §4).

## R11 candidate: M3-ASSY-R11 (R10's circuit on a compact six-layer board, 46 × 50 mm; CAD candidate, NOT accepted)

**Status (2026-11-03).** Branch `m3-assy-r11` (cut from `m3-assy-r10` at `deb179e`); the R11 KiCad project is `m3_design/r11/`, built by `m3_design/r11_build.sh`, and R10's `m3_design/assembly_review/` stays the frozen R10 record. PCB `3bb83272…` (full hash and metrics in [docs/M3_R11.md, "Current state"](docs/M3_R11.md#current-state)), 46 × 50 × 1.6 mm, six layers. Not accepted, nothing ordered; R9 stays the accepted board. No review round has run on R11 yet. What the owner must accept or do: [docs/R11_VALIDATION.md](docs/R11_VALIDATION.md). Harness pin map and per-flight procedure: [docs/R11_VEHICLE_HANDOFF.md](docs/R11_VEHICLE_HANDOFF.md).

| Kind | Verified (with its record) | Not verified |
|---|---|---|
| *Software tests and CAD gate* | Board built twice with the same SHA-256; DRC 0 violations, 0 unconnected, 0 schematic parity, ERC 0; `r11_sch_check` OK (strict ERC, 218 parts against R10's contract plus D-R11-86's divider, 55 seeded faults); metadata / 3D audit OK; `tools/check_r11.py` every rule OK (K-legends with the R11 legend set, K-copper GAP-3, K-exti, K-neighbours, K-reference, K-power, S-1 … S-9); `route_check --profile r11` 0 failing, 3 allowlisted, 0 stale; R11 fab manifest and content checks OK; `tools/test_r11_check.py` 50 tests OK with `R11_BOARD_REQUIRED=1`; `tools/check.sh` exit 0 with the R11 board staged (stageD3.md §1, §5, Measured). | The supervisor's final gate run on this tree is recorded by the supervisor, not here. No review round (stage F). |
| *Simulation and calculation* | Hot-plug: R10's model on R11's copper, 2304 / 2304 required cases pass, steepest fall 8.663 V/µs (Simulation / Inference, D-R11-79). Fire budget 4.620493 Ω, 1.278004 A at four stalls; guard 34.853 ms < 36 ms; EN / chatter and hold-up equal to R10's; rail DC solves and IPC-2152 widths (Calculation / Inference; stageD_analysis.md, stageD2.md §4). | The plate model (no r11 profile); U401's thermal figure (Inference, D-R11-80); plane current capacity in the 0.16 mm necks; signal integrity. |
| *Datasheet reads* | Stage A: the TFBGA-100 ball map and land (DS12110 Rev 8). Stage E: PC2_C is a TT_a pad (DS12110 Rev 8 Table 9 p. 67) with a 4.0 V absolute maximum (Table 119 p. 211) and 0 mA injection (Table 156 p. 244), as cited by the stage E docs lane; ST's PDF did not download in this lane. D-R11-86's divider keeps the pin ≤ 0.94 V on one resistor fault (Calculation). The SYSCFG_EXTICR layout (one port per line) was checked against ST's CMSIS header `stm32h743xx.h` (cmsis-device-h7 commit 8f922cdc; `docs/M3_R11.md` "Sources"). | RM0433 was not read (SYSCFG_PMCR.PC2SO, USB regulator bypass, VREFBUF on TFBGA-100); DS12110 was not re-fetched from ST. |
| *Physical, electrical and firmware tests* | None. | No board exists; no firmware (the binding note is a record only); JLC DFM not queried (0.1 mm rules, plane necks, short-edge rails, VIPPO, X-ray of U1); no harness, fit, thermal or vibration test. |

Cost: $79.80 per board (parts + feeder fees, 5 boards, 2026-11-04T01:15Z) against the $84.41 cap; stock short on U9, U4 and U2 (stageD3.md §5).

## R10 candidate: M3-ASSY-R10 (leaner AVA-informed board, 46 × 90 mm; CAD candidate, NOT accepted)

**Status (2026-11-02).** PCB `a0ec075e…` (full hash and metrics in [docs/M3_R10.md, "Current state"](docs/M3_R10.md#current-state)), 46 × 90 × 1.6 mm. Not accepted, nothing ordered; R9 stays the accepted board.
Rounds 22 and 23 (ten Claude lenses each) were the closing pair on `5516eeec…`: 0 Critical / 0 Major. The round 24 board pass (D-R24-01 … D-R24-17) made `1407e850…`; round 24 found 17 Minor real errors on it, and the round 24 fix pass (D-R24-18 … D-R24-23) changed the board to `92c3ad59…`. Round 25 found 10 Minor real errors on `92c3ad59…`, none on the board; its fix pass (D-R25-01 … -03) left the board unchanged. Round 26 found 12 Minor real errors on `92c3ad59…`, one of them on the board; its fix pass (D-R26-01 … -04) changed the board to `a0ec075e…`. Round 27 found 7 Minor real errors on `a0ec075e…`, none on the board; its fix pass (D-R27-01 … -03) corrected the budget's four-stall pack sag, the ports' schematic symbol, the binding note's revision sentence and the records, and left the board unchanged. Round 28 found 9 real errors on `a0ec075e…` (R28-TRI-01 … -09: one Major, an AGENTS §2.5 labelling violation in firmware rule 3, and 8 Minor; none on the board), and its fix pass (D-R28-01 … -04 and two audit lanes) left the board unchanged. Round 29 found 5 real errors on `a0ec075e…` (R29-TRI-01 … -05: one Major, AGENTS §2.5 again, with figures resting on inferred inputs still marked Calculation only or unlabelled and four round 28 status lines claiming they were all labelled, and 4 Minor; none on the board), and its fix pass (D-R29-01 … -02 and the docs lane) left the board unchanged. Round 30 found 2 Minor real errors on `a0ec075e…` (R30-TRI-01 … -02, text only, none on the board: the ARM1_SENSE-to-CAM_IO_3V3 bridge figures left out the D120 / R131 cold pull-up, and round 29's "LS120 ≤ 70 °C" chamber-test pass clause could not pass), and its fix pass (docs lane) left the board unchanged. Round 33's ten lenses (commit `feed21f`) gave 1 Minor real error after triage (R33-TRI-01, text only, none on the board), which its docs fix pass corrected. Round 34's ten lenses reviewed `a0ec075e…` at commit `c2a11fd` and found 0 real errors; the triage found and kept 1 Minor real error itself (R34-TRI-01, text only, none on the board), and its fix pass (docs lane) left the board unchanged. Round 34 had real errors, so rounds 35 and 36 review `a0ec075e…` under the owner's strict rule (only real errors count; iteration stops after two consecutive rounds with zero verified real errors).
The J400 switch timing counts D402's leakage (D-R24-19, Calculation / Inference: C87's X7R bias allowance is an Inference): single-drop-out immunity 10.3 / 20.1 / 26.0 ms at 6.0 / 7.4 / 8.4 V and about 8.1 ms at the four-stall 5.71 V (repeated drop-outs add up; D-R26-03), turn-on 30–130 ms. The bench chatter pass rule (D-R25-01) is total open time under 7 ms in every sliding 100 ms window, with U9 on for the whole run at 5.71 V (worst-corner limit 7.50 ms; D-R26-03); it replaces the < 10 ms and < 18 % rules.
The cost target fails: parts plus feeder fees are $85.26 per board against the $84.41 cap (R3's cost per board), $0.85 over (the owner-approved spare AUX port and D402); the owner decides. JLC's fixed fees add $16.79. The stock check (2026-11-02T12:43:17Z) fails on U4 (9 in stock, 2 orderable against 5) and U9 (30 in stock, −81 orderable, minimum 7): confirm both in the JLC cart on order day, else consign franchised parts (ORDERING 8.1 has the owner's other choices).
The full state (checks, cost and stock, retained deviations, what is not verified) is in [docs/M3_R10.md](docs/M3_R10.md#current-state).
What the owner must accept or do: [docs/R10_VALIDATION.md, "R10 deviations for owner acceptance"](docs/R10_VALIDATION.md#r10-deviations-for-owner-acceptance).

**Round 34 review and fix pass (2026-11-02).** Round 34's ten Claude lenses reviewed `a0ec075e…` at commit `c2a11fd`: 0 Critical / 0 Major / 0 Minor findings (all ten lenses 0). A fresh triage verifier (`round34_triage.md`) re-checked every observation and the root's flags, and found and kept **1 real error** itself (R34-TRI-01, Minor, text only, none on the board), with the observations in 16 groups, none otherwise promoted and 0 not reproducible. Round 34 is not clean, so the closing pair is now rounds 35 and 36 on `a0ec075e…`. The docs lane (`round34_fix_docs.md`) fixed it:
- **Hot-plug results pointer (TRI-01).** `parts_qualification.md` (the R166 and R92 sections) now sends readers to `hotplug_results.json` / `hotplug_inputs.json` and M3_R10 "Current state" for the current hot-plug results, and keeps `hotplug.md` for the model, sources and limitations. `hotplug.md`'s top section is retitled "Historical round-11 fix-pass target" (board `0ad0135c…`), under a new pointer to the current bound inputs and results and M3_R10's figures (falling 8.995 / rising 5.088 V/µs, retained output 1643.90 µF / 5.914 V).

Index: R10_VALIDATION, "Round 34".
- *Software tests:* none run by the docs lane.
- *DRC and CAD gate:* not run by the docs lane; root runs `tools/check.sh` before the commit.
- *Simulation and calculation:* no model re-run; the current figures are the committed `hotplug_results.json` (inputs digest `f4d1b57d…`, bound to `a0ec075e…`) as recomputed by the triage.
- *Physical tests:* none. Rounds 35 and 36 will review `a0ec075e…`.

**Round 33 review and fix pass (2026-11-02).** Round 33's ten Claude lenses reviewed `a0ec075e…` at commit `feed21f`: 0 Critical / 0 Major and 1 raw Minor finding (docs binding; power, routing, MCU, mechanics, parts, manufacturing, requirements, safety and gate 0) and 98 observations. A fresh triage verifier (`round33_triage.md`) merged R33-DOCS_BINDING-01 with the lens's observation 0 and kept **1 real error** (R33-TRI-01, Minor, text only, none on the board), with the other observations in 11 groups, none promoted and 0 not reproducible. Round 33 is not clean, so the closing pair is now rounds 34 and 35 on `a0ec075e…`. The docs lane (`round33_fix_docs.md`) fixed it:
- **U9 pad exposure (TRI-01).** ORDERING 8.3 now says U9's pads 5 and 6 expose 0.15–0.25 mm (0.20 mm nominal; RPW0010A body 1.9–2.1 mm, SLVSFC9C) × 0.30 mm beyond the body at each end, and that pad 9 exposes only 0.15–0.25 × 0.25 mm beyond the body (was 0.10 × 0.30 mm, and pad 9 "under the body": round 23 read the B.Fab line's outer edge as the body). The probe points and the R84.1 instruction are unchanged; the round 23 review record stays as written.

Index: R10_VALIDATION, "Round 33".
- *Software tests:* none run by the docs lane.
- *DRC and CAD gate:* not run by the docs lane; root runs `tools/check.sh` before the commit.
- *Simulation and calculation:* no model re-run; TRI-01's figures are the triage's pcbnew probe (`.supervisor/r33_triage/u9.py`) against the SLVSFC9C body tolerance.
- *Physical tests:* none. Round 34 reviewed `a0ec075e…` (above).

**Round 32 review and fix pass (2026-11-02).** Round 32's ten Claude lenses reviewed `a0ec075e…` at commit `3366287`, the commit round 31 reviewed: 0 Critical / 0 Major and 2 raw Minor findings (manufacturing 1, parts 1; power, routing, MCU, mechanics, requirements, safety, docs binding and gate 0). A fresh triage verifier (`round32_triage.md`) split R32-MANUFACTURING-01 into two and kept **3 real errors** (R32-TRI-01 … -03, all Minor, text only, none on the board); it re-examined 11 of the 132 observations, promoted none and found 0 not reproducible. **Round 32 is not clean**, so the closing pair is now rounds 33 and 34. The fix pass ran one lane, the docs lane (`round32_fix_docs.md`), fixed all three and left the board at `a0ec075e…`:
- **R166-to-C84 courtyard gap (TRI-01).** 0.65 mm between the courtyard centrelines (0.60 mm between the lines' outer edges), was 0.56 mm, a bounding-box figure; in ORDERING 8.2, R10_VALIDATION's C84 hand-fit paragraph and the R19-MEC-02 row. The historical review records stay as written.
- **C84 heat limit (TRI-02).** R10_VALIDATION now says what ORDERING 8.2 asks: top-only heating with the bottom supported on a heat-sinking fixture, a short dwell, and the tip temperature and time recorded; no preheat and no temperature limit. `round19_fix_docs.md` carries a one-line erratum.
- **Fitted 85 °C parts (TRI-03).** Owner row 33, M3_R10's hot end and `parts_qualification.md` now read "the fitted 85 °C parts (among them MS5611, the AP6320x bucks, J430, U3, Y1, LED1, LED2 and the 16 fitted X5R capacitors C6–C11, C19, C20, C22, C23, C28, C80, C89, C92, C95, C96)", keeping the U4 alternates where they were named. The pass rule (every 85 °C part ≤ 85 °C) is unchanged.

Index: R10_VALIDATION, "Round 32".
- *Software tests:* none run by the docs lane.
- *DRC and CAD gate:* not run by the docs lane; root runs `tools/check.sh` before the commit.
- *Simulation and calculation:* no model re-run; TRI-01's figures are the triage's pcbnew probe.
- *Physical tests:* none. Round 33 reviewed `a0ec075e…` (above).

**Round 31 review (2026-11-02).** Round 31's ten Claude lenses reviewed `a0ec075e…` at commit `3366287`: 0 Critical / 0 Major / 0 Minor findings (all ten lenses 0) and 151 observations. A fresh triage verifier (`round31_triage.md`) re-examined the 151 observations and one of its own, promoted none and found 0 not reproducible: **0 real errors, a clean round** (the first of a pair). There was no fix pass. Round 32 then found real errors on the same commit (entry above), so round 31's clean result does not close the board.

Index: R10_VALIDATION, "Round 31".
- *Software tests, DRC and CAD gate, simulation:* none run for this round's record.
- *Physical tests:* none.

**Round 30 review and fix pass (2026-11-02).** Round 30's ten Claude lenses reviewed `a0ec075e…` at commit `0afaed3`: 0 Critical / 0 Major and 2 raw Minor findings (safety 2; power, routing, MCU, parts, mechanics, manufacturing, requirements, docs binding and gate 0). A fresh triage verifier (`round30_triage.md`) kept both as **2 real errors** (R30-TRI-01 … -02, both Minor, text only, none on the board), merged requirements observation 20 into TRI-02, did not count the other 107 observations and found 0 not reproducible. The fix pass ran one lane, the docs lane (`round30_fix_docs.md`), fixed both and left the board at `a0ec075e…`:
- **Bridge figures (TRI-01).** R10_VALIDATION §1's ARM1_SENSE-to-CAM_IO_3V3 bridge now counts the D120 / R131 cold pull-up, live whenever CAM_IO_3V3 is up: about 2.19–2.21 V on RAW_ACT and about 0.107–0.109 mA through the match at a BAT54 drop of 0.20–0.24 V (Calculation / Inference), was about 1.73 V and 0.15 mA. The RAW_ACT bridge's EN load is 5.6 kΩ with the e-match or the step-3 dummy fitted, not only 11.2 kΩ. Conclusions unchanged: no fire, the cold screen refuses, the board does not start.
- **Chamber-test pass criterion (TRI-02).** Round 29's "LS120 ≤ 70 °C" clause could not pass (LS120 runs above chamber air at the pad load) and contradicted owner row 36. The first-article 70 °C chamber test now passes on "every 85 °C part ≤ 85 °C" alone and records LS120's measured rise over chamber air (thermocouple on LS120), which is not a pass / fail gate; the bay-air limit above which buzzer annunciation is best-effort is 70 °C minus that rise, which replaces the inferred 48 °C (now only the pre-test estimate). Changed in REQUIREMENTS, M3_R10, ORDERING 8.3, owner rows 33 and 36, `parts_qualification.md`, the AGENTS buzzer row and the round 29 records.
- **Generated text:** `m3_design/r10_sch_check.py` and the binding note carry neither statement; no generator, test or decision change.

Index: R10_VALIDATION, "Round 30".
- *Software tests:* none run by the docs lane.
- *DRC and CAD gate:* not run by the docs lane; root runs `tools/check.sh` before the commit.
- *Simulation and calculation:* no model re-run; TRI-01's figures are the triage's three-node solve, checked by hand.
- *Physical tests:* none. Rounds 31 and 32 reviewed `a0ec075e…` (entries above).

**Round 29 review and fix pass (2026-11-02).** Round 29's ten Claude lenses reviewed `a0ec075e…` at commit `09a564e`: 0 Critical / 1 Major and 4 raw Minor findings (safety 1, the Major; gate, MCU, mechanics and requirements 1 Minor each; power, parts, manufacturing, routing and docs binding 0). A fresh triage verifier (`round29_triage.md`) kept all **5 as real errors** (R29-TRI-01 … -05, 1 Major and 4 Minor, none on the board), 139 observations and 0 not reproducible. The fix pass ran two lanes, fixed all 5 and left the board at `a0ec075e…`: the CAD lane (`round29_fix_cad.md`, D-R29-01 … -02) and the docs lane (`round29_fix_docs.md`):
- **AGENTS §2.5, again (TRI-01, Major).** Figures resting on inferred inputs were still marked "Calculation" only or unlabelled: the unclamped J400 ESD 9.6 V (C87's X7R bias allowance and a full charge transfer), C128's 991 microstrain, the fire currents (Q124's hot factor), the 34.853 ms guard, the plate model's 125 / 133 g, the gate-net bridge's 3.23 V and the pack sag; and four round 28 status lines, this file's among them, claimed every such figure was labelled. The docs lane labelled every listed and borderline place, its own sweep labelled three more (M3_R10's EN switch-network paragraph and the gate-net bridge's fire in FMEA and §1), and the status lines now say what each pass did.
- **Rule 3's gate time constant (TRI-02, D-R29-01):** about 47–58 µs over C126's ±10 % (53 µs nominal; Calculation, driver resistances Inference), in the generated text and the records; it was 47–53 µs, nominal and below only.
- **Tail allocation (TRI-03):** fit_check allocates all 27 tails of the eight terminals, J440's included (minimum 7.558359 mm); R10_VALIDATION §8 no longer says 23 and "not re-run".
- **LS120 hot end (TRI-04).** LS120 is a +70 °C part (MLT-5020 p2 item 6), out of rating at a 70 °C bay (about 80–92 °C at the pad load) and at the 55 °C interim limit (65–77 °C; Inference). The round 29 fix pass made the chamber test pass only with LS120 ≤ 70 °C (thermocouple on LS120), and new owner row 36 records buzzer annunciation as best-effort when bay air is above about 48 °C (70 °C − 22 K; Inference); recovery and logging do not depend on the buzzer, and the respin option is a +85 °C buzzer on the same land. Round 30 replaced that pass clause (R30-TRI-02): the chamber test passes on the 85 °C parts alone and records LS120's measured rise, and the best-effort bay-air limit becomes 70 °C minus that rise in place of the inferred 48 °C.
- **Test pins (TRI-05, D-R29-02):** the chatter obligation's turn-on label and six other D-R28-02 … -04 qualifiers are pinned, and the round 27 form is rejected, so D-R28-03's "pins each new label" is now true (D-R28-03 annotated).

Index: R10_VALIDATION, "Round 29".
- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 72, R10 268 (6 NumPy skips; `test_r23_binding_note_rules_and_pin_table` extended in place: 20 required phrases in its D-R28-03 block, was 9, and 14 rejected forms, was 12) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* one complete `m3_design/r10_build.sh` (1668 s, KiCad CLI 10.0.7) reproduced PCB `a0ec075e…` and ended in `tools/check.sh` exit 0: r10_sch_check OK; DRC 0, unconnected 0, schematic parity 0, ERC 0; the R10 CAD contract OK (K-binding included); route_check 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers; fab content checks and the manifest. The binding note is now `c5cd0fa3…` (was `30796f5e…`; only rule 3's phrase changed). The fab outputs changed only in their creation dates (BOM, owner BOM, CPL and paste byte-identical), so the supplier evidence stands; `parts_budget.json` is unchanged.
- *Simulation and calculation:* no model re-run; the relabelled figures keep their values, and rule 3's 47.8 / 53.0 / 58.3 µs are Calculations on the round 23 model with inferred driver resistances.
- *Physical tests:* none. Round 30 reviewed `a0ec075e…` (next entry above).

**Round 28 review and fix pass (2026-11-02).** Round 28's ten Claude lenses reviewed `a0ec075e…` at commit `19dd0b5`: 0 Critical / 0 Major and 8 raw Minor findings (power 3, MCU 2, requirements 2, safety 1; gate, parts, manufacturing, routing, mechanics and docs binding 0). A fresh triage verifier (`round28_triage.md`) kept **9 real errors** (R28-TRI-01 … -09, none on the board): one **Major**, promoted from a safety observation (R28-TRI-09: firmware rule 3 stated the QSPI_IO2 / PE4 gate-fight figures without their Inference label, against AGENTS §2.5), and 8 Minor; 102 observations and 0 not reproducible. The fix pass ran four lanes, fixed all 9 and left the board at `a0ec075e…`: the CAD lane (`round28_fix_cad.md`, D-R28-01 … -04), audit lane A (`round28_audit_pq.md`) on `parts_qualification.md`, audit lane B (`round28_audit_proc.md`) on the procedures in ORDERING 8 and the handoff, and the docs lane (`round28_fix_docs.md`):
- **Firmware rules 3 and 4** (D-R28-02 … -04). Rule 3's gate-fight figures carry their Inference label, with "the MCU driving IO2 high" and "in all but one modelled corner" (TRI-09). Its first-article meter check, before first power with the board unpowered, reads both polarities: an intact board reads above 0.9 kΩ, or open, both ways, and a beep or under 100 Ω in either polarity is a bridge (TRI-05). Rule 4 gains the Q120 pass criterion: |VGS| at least 4.5 V, and BAT_IN − RAW_ACT above 0.2 V during the dummy-load fire fails. The port supply's lead over 3V3 is "tens of ms" (Calculation / Inference), not "44 ms or more".
- **§2.5 sweep.** The CAD lane labelled five more generated obligations, and the docs lane the same class through M3_R10, FMEA, REQUIREMENTS, the owner rows, AGENTS and STATUS. It labelled the fire-budget, EN-timing, hold-up, cold-screen and load-switch figures it found that rest on inferred inputs as Calculation / Inference; round 29 found more such places, and four status lines (this one among them) that claimed all were labelled (R29-TRI-01), which the round 29 fix pass labelled and corrected.
- **Four-stall pack sag** (D-R28-01): the ports' 1.461 A plus the AUX 0.1 A, as `ports_w` does, gives 5.881 / 4.388 V (5.880831 / 4.388491 V) from a 7.4 / 6 V open pack (TRI-03; Calculation / Inference on the budget model's stall input).
- **Audit lanes.** Audit lane A made `parts_qualification.md` current in one pass: TRI-02, -03, -04 and -06 and about 35 more stale or mislabelled current statements. Audit lane B re-derived every R10 procedure step in ORDERING 8 and the handoff and fixed 17, among them the C84 capacitance pass value, the J400 ESD test's dummy-load condition and per-flight step 4's no-USB precondition.
- **Record fixes:** FMEA's R10 row no longer credits the dividers with ADC series protection (TRI-01); REQUIREMENTS F4's hinge moment is about 64–84 % of stall over flight 2's envelope (Inference; TRI-07), and the stale 525 s is gone (TRI-08). Also the routed siblings: the J440 clamp distances (3.864 / 3.964 mm of track, 1.865 / 1.900 mm pad edge to pad edge), the USB attach inventory (516.1 µF, 2.426 mC, 5.35–6.98 ms), DS15034 Table 2 on p11 and the U400 / L400 distance 8.7–13.4 mm.

Index: R10_VALIDATION, "Round 28".
- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 72, R10 268 (6 NumPy skips; `test_r23_binding_note_rules_and_pin_table` extended with 16 required phrases and 12 rejected old forms) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* build 3 (KiCad CLI 10.0.7), on the tree before the DS15034 citation fix, reproduced PCB `a0ec075e…` and ended in `tools/check.sh` exit 0 (build 1 had reproduced it too): r10_sch_check OK; DRC 0, unconnected 0, schematic parity 0, ERC 0; check_r10 37 / 37 (K-binding OK); route_check 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers; fab content checks and the manifest. `parts_budget.json` is `4267634…`, the binding note then `30796f5e…` (regenerated after build 3 for the DS15034 Table 2 citation, D-R28-04; `a40e21a4…` at build 3; `c5cd0fa3…` since the round 29 fix pass); the committed tree, with that note, passed the root's `tools/check.sh`. The fab outputs changed only in their creation dates (BOM, owner BOM, CPL and paste byte-identical), so the supplier evidence stands.
- *Simulation and calculation:* hot-plug 2304 cases, 0 failures, inputs and results byte-identical (Simulation/Inference); the pack-sag figures are Calculations / Inferences on the budget model (stall input, parts_qualification); the relabelled figures keep their values.
- *Physical tests:* none. Round 29 then reviewed `a0ec075e…` (above).

**Round 27 review and fix pass (2026-11-02).** Round 27's ten Claude lenses reviewed `a0ec075e…` at commit `816038c`: 0 Critical / 0 Major and 7 raw Minor findings (power 3, MCU 1, mechanics 1, requirements 1, safety 1; gate, parts, manufacturing, routing and docs binding 0). A fresh triage verifier (`round27_triage.md`) kept **7 real errors** (R27-TRI-01 … -07, all Minor, none on the board; a pack-sag sibling it found is merged into TRI-02) and 0 not reproducible. The fix pass (CAD lane `round27_fix_cad.md`, D-R27-01 … -03; docs lane `round27_fix_docs.md`) fixed all 7 and left the board at `a0ec075e…`:
- The budget's four-stall pack sag now counts the AUX port's 0.1 A: 5.881 / 4.388 V from a 7.4 / 6 V open pack (5.880831 / 4.388491 V at 1.561 A = 1.461 A + 0.1 A AUX, after the round 28 correction R28-TRI-03, D-R28-01: D-R27-01's code used 1.46 A + 0.1 A and gave 5.881 / 4.389 V; 5.899 / 4.414 V before the AUX allowance), and the U401 thermal paragraph uses the 560 mA allocation: 0.490 W, 109.2–123.9 °C at a 70 °C bay, 124.2–138.9 °C at 85 °C, ceiling 112.3 °C/W (TRI-02; the generator's `loaded_pack`, D-R27-01, and parts_qualification).
- J410, J420 and J440 get their own schematic symbol, M3:PortTerminal (pins 4V8 / GND / TXO / RXI), which `r10_sch_check` asserts; J9 keeps M3:CameraTerminal (TRI-07, D-R27-03). The binding note's DS12110 revision sentence names the two limits read from Rev 11 Table 109 (TRI-04, D-R27-02).
- Record fixes: the 70 °C TCR window limits are 7.31 ms at 5.73 V and 7.18 ms at 5.71 V (TRI-01); the In2 3V3 fill is 1430.05 mm² on `a0ec075e…` (TRI-03); the 3V3 clamp is not FMEA H-9, which is the load-switch gate-source capacitor C120 (TRI-05); J440's leads stay aft of y 23.5 (TRI-06).

Index: R10_VALIDATION, "Round 27".
- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 72, R10 268 (was 267; 6 NumPy skips; new `test_r27_port_terminal_pin_names`; `test_r23_binding_note_rules_and_pin_table` extended) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* one complete `m3_design/r10_build.sh` (KiCad CLI 10.0.7) reproduced PCB `a0ec075e…` and ended in `tools/check.sh` exit 0: r10_sch_check OK (43 seeds caught: 39 contract, 4 pin-name); DRC 0, unconnected 0, schematic parity 0, ERC 0; check_r10 37 / 37 (K-binding OK); route_check 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers; fab content checks and the manifest. The build re-exported the fab outputs with only their creation dates changed (BOM, owner BOM, CPL and paste byte-identical), so the supplier evidence stands.
- *Simulation and calculation:* hot-plug 2304 cases pass with 0 failures, inputs and results byte-identical (Simulation/Inference); the pack-sag and U401 figures are Calculations / Inferences from the budget model (R27-TRI-02); the docs lane measured the In2 3V3 fill on `a0ec075e…` (KiCad 10.0.7 pcbnew, read-only, on a copy): 1430.05 mm², one piece.
- *Physical tests:* none. Round 28 then reviewed `a0ec075e…` (above).

**Round 26 review and fix pass (2026-11-02).** Round 26's ten Claude lenses reviewed `92c3ad59…` at commit `3d8e845`: 0 Critical / 0 Major and 14 raw Minor findings (safety 4, routing 3, power 2, manufacturing 2, requirements 2, mechanics 1; MCU, gate, parts and docs binding 0). A fresh triage verifier (`round26_triage.md`) kept **12 real errors** (R26-TRI-01 … -12, all Minor, one needing a board change), 107 observations and 0 not reproducible. The fix pass (CAD lane `round26_fix_cad.md`, D-R26-01 … -04; docs lane `round26_fix_docs.md`) fixed all 12 and changed the board to `a0ec075e…`:
- J440.3 / J440.4, where the AUX pair changes layer, now have GND partner vias 1.500 mm away, (7.4,16.5) and (7.4,20.0), and route_check's new `pad_layer_changes` test fails a plated pin that carries a critical net on two copper layers with no GND via within 1.5 mm (TRI-09, D-R26-01); the four-position terminal's pins 3 / 4 dropped their unconnected inner rings to make room.
- C10, C11, R164 and R173 moved (0.60 mm for C10, 0.65 mm for the others), so PYRO1_OUT is at least 1.040 mm from 3V3 and 3V3A (was 0.5135 / 0.5662 mm; TRI-01's respin item, D-R26-02); the records now say that PYRO1_OUT's GND pairs fire an enabled match by themselves (TRI-01).
- **The root's follow-up (D-R26-04).** The pass's first layout, the intermediate `4108e6fa…` (never committed or reviewed), had put R164's 3V3 via 0.331 mm from R126.1 on PE4's net and C10's coat envelope 2.994 mm from U5; the docs lane found both. D-R26-04 moved the via to (19.55,55.825) and C10 to B(17.5,53.5): every 3V3 / 3V3A item is now at least 1.0585 mm from Q124's gate nets on every layer (R127.1 1.065 mm, R128.1 1.0585 mm; 0.835 / 0.676 mm on `92c3ad59…`), and C10's coat envelope is 3.017 mm from U5's union, outside ORDERING 8.3's 3 mm exclusion. Its whole-board audit lists the remaining nearer pairs: BUZZ_DRV to PYRO1_OUT is 0.794 mm (R162.1 to R173.1; 0.964 mm before), where a bridge may fire an enabled match (Inference) and one present at power-up is refused by the cold screen (R10_VALIDATION §1).
- The generated text and the records quote the four-stall BAT_IN with the AUX allowance, 5.71 V (single drop-out 8.1 ms, window limit 7.50 ms, fast-chatter fraction 19.7 %; Calculation / Inference: C87's X7R bias allowance and the fire budget's hot Q124 factor are inferred), the late-block worst chatter train in place of the sampled search, and rule 8's corrected corner, 5.71 / 5.55–5.56 / 5.50 V (TRI-02 … -04, D-R26-03).
- Record fixes: U11.5 is OV1; F4's 5.96 V option; owner row 8's counts; 13 of the 21 rail returns beyond 4 mm; 4.493 mm wire room; the C84 heat-limit joints, with C8 added; R7 among the J3 slot neighbours (TRI-05 … -08, -10 … -12).

Index: R10_VALIDATION, "Round 26".
- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 72 (was 71), R10 267 (was 263; 6 NumPy skips; five new tests across the two suites, one extended) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* builds A and B both made PCB `a0ec075e…` and both ended in `tools/check.sh` exit 0, and a standalone `tools/check.sh` on the final tree exited 0: DRC 0, unconnected 0, schematic parity 0, ERC 0; check_r10 37 / 37 (K-binding OK); route_check 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers (`critical_via_no_gnd` 2 → 0 under the new pad test). Four CPL rows moved (BOM and owner BOM byte-identical), so the supplier evidence was re-run on the final files: $85.26 per board, U4 and U9 short.
- *Simulation and calculation:* hot-plug 2304 cases pass, extremes unchanged (Simulation/Inference; C10 / C11 re-extracted); the EN window limits, the late-block train and rule 8's corner are Calculations (D-R26-03); the bridge analyses are Calculations or labelled Inferences (D-R26-04); the docs lane's adjacency, detour and clearance figures are Calculations on native geometry.
- *Physical tests:* none. Round 27 then reviewed `a0ec075e…` (above).

**Round 25 review and fix pass (2026-11-01).** Round 25's ten Claude lenses reviewed `92c3ad59…` at commit `c4bb56b`: 0 Critical / 0 Major and 14 raw Minor findings (power 4, safety 3, requirements 3, mechanics 2, MCU 1, docs binding 1; routing, gate, parts and manufacturing 0). A fresh triage verifier (`round25_triage.md`) kept **10 real errors** (R25-TRI-01 … -10, all Minor, none on the board), 72 observations and 0 not reproducible. The fix pass (CAD lane `round25_fix_cad.md`, D-R25-01 … -03; docs lane `round25_fix_docs.md`) fixed all 10: the J400 chatter rule is now total open time under 7 ms in every sliding 100 ms window with U9 on at 5.73 V (5.71 V since D-R26-03; the round 24 < 18 % line passed trains that trip a worst-case U9); the post-trip hold-up is 0.103–0.164 / 0.291–0.430 ms over the trip window; "100–220 µF would do" is struck from REQUIREMENTS F6; the OVLO corner counts the pin leakage (10.18 V); FMEA H-6's ramp window, two current-board hashes, the Pack-row turn-off corners (4.802 / 4.835 / 4.875 V), R150–R155's status, the plate-thickness bound and row 32's C421 load are corrected. Index: R10_VALIDATION, "Round 25".
- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 71, R10 263 (6 NumPy skips; two tests updated) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* one complete build reproduced PCB `92c3ad59…` and `tools/check.sh` exited 0: DRC 0, unconnected 0, schematic parity 0, ERC 0; check_r10 37 / 37 (K-binding OK on the regenerated binding note); route_check 0 failing; `r10_parts.py --check` passes on the regenerated budget. BOM, owner BOM and CPL unchanged; supplier evidence not re-run.
- *Simulation and calculation:* hot-plug 2304 cases pass, extremes unchanged (Simulation/Inference); the chatter window limits (7.629 / 5.871 / 9.594 ms at 5.73 / 5.5 / 6.0 V), the post-trip hold-up and the OVLO corner are Calculations (D-R25-01 … -03); the 4000-train adversarial search is the triage's and was not re-run (round 26 found it a sample, not the worst case: R26-TRI-03).
- *Physical tests:* none. Round 26 then reviewed `92c3ad59…` (above).

**Round 24 review and fix pass (2026-11-01).** Round 24's ten Claude lenses reviewed `1407e850…` at commit `f2b8251`, the first round under the owner's strict rule: 0 Critical / 0 Major and 24 raw Minor findings (safety 6, docs binding 5, MCU 4, requirements 4, gate 3, power 2; routing, parts, mechanics and manufacturing 0). A fresh triage verifier (`round24_triage.md`) found **17 real errors** (R24-TRI-01 … -17, all Minor), 11 observations and 0 not reproducible. The fix pass (CAD lane `round24_fix_cad.md`, D-R24-18 … D-R24-23; docs lane `round24_fix_docs.md`) fixed all 17: BAT_FAULT_N's chamfer at the BAT_ENABLE via capped (0.173 → 0.200 mm; board now `92c3ad59…`); the generated EN text and the records carry D402's leakage and the corrected bench-ramp window (off 4.29–4.80 V, on 4.72–5.25 V), except FMEA H-6, which kept the old window until round 25 (R25-TRI-05); the 18 % chatter line set then (the root's call) was wrong and was replaced in round 25 (D-R25-01); check_r10 rule M-8 holds the 2.5 mm short-edge clearance; and the remaining text, figure and message fixes. Index: R10_VALIDATION, "Round 24".
- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 71, R10 263 (6 NumPy skips; new `test_r24_short_edge_clearance`) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* builds E and F both made PCB `92c3ad59…` and both ended in `tools/check.sh` exit 0: DRC 0, unconnected 0, schematic parity 0, ERC 0; check_r10 37 / 37 (M-8 new); route_check 0 failing, `right_angle` 0, 5 unrecorded noncritical leftovers. BOM, owner BOM and CPL are byte-identical to `1407e850…`'s, so the supplier evidence still binds (not re-run); the Gerbers were re-exported and the manifest re-bound.
- *Simulation and calculation:* hot-plug 2304 cases pass, extremes unchanged (Simulation/Inference); the EN corner model with D402 (Calculation, D-R24-19).
- *Physical tests:* none. Round 25 then reviewed `92c3ad59…` (above).

**Round 24 board pass (2026-11-01).** The CAD lane changed the board to `1407e850…` through the generators (D-R24-01 … D-R24-17; record `round24_board_cad.md`): second vias for Q120 / Q121's gate drive, BOOT0, VCAP2, U402's GND island, the PA6 / PA4 / R91 monitor taps and R87.1's input via; U401's feedback divider moved beside U401 on B.Cu (no via in the loop); D402, a ninth ESD103-B1-02EL, clamps J400.2 to GND ahead of R165; all 59 90° bends chamfered to 45° and a new route_check `right_angle` rule (every net, empty allowlist); the JLCJLCJLCJLC placeholder removed; R92 and TP88 moved off the forward edge. Kept, with measured reasons: U4.6 / U4.7's GND via, VCAP1, U9's EN via, U11.2 and the two 3V3A feeds, the U10 / R7 / R8 islands, R87.1's drop and R85.1, the east tabs and the Fab body outlines.
- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 71, R10 262 (6 NumPy skips under KiCad Python) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* builds C and D both made PCB `1407e850…` and both ended in `tools/check.sh` exit 0: DRC 0, unconnected 0, schematic parity 0, ERC 0; check_r10 36 / 36; route_check 0 failing, `right_angle` 0, 5 unrecorded noncritical leftovers; SINGLE_OPEN_EXCEPTIONS 22 → 11. The fab package is bound and the supplier evidence was re-run ($85.60; U4 and U9 short).
- *Simulation and calculation:* hot-plug 2304 cases pass (minimum −14.807 V, steepest fall 8.995 V/µs, rise 5.088 V/µs; Simulation/Inference). D402's leakage moves EN by at most 5.7 mV (Calculation).
- *Physical tests:* none. Round 24 then reviewed this board (above).

**Round 23 review and closing pass (2026-11-01).** Round 23's ten Claude lenses reviewed `5516eeec…` at commit `c70d261`, the second review of the closing pair. All ten reported 0 Critical / 0 Major, with 55 Minor (docs binding 10, safety 9, requirements 8, gate 7, manufacturing 5, MCU 4, mechanics 4, power 4, parts 3, routing 1). Rounds 22 and 23 are therefore the closing pair: two consecutive full rounds with no Critical or Major on the same board, `5516eeec…`; a fresh max-effort verifier confirmed SAFETY-08(a) and SAFETY-05 as Minor (`round23_safety_severity_check.md`). The closing pass is text and checks only; the board stays `5516eeec…`. The docs lane added the 13 root firmware rules (M3_R10 "Firmware"), one numbered per-flight list with a dummy-load closed-switch check and an igniter-resistance check (ORDERING 8.3), the R10 JLC order form (Flying Probe Full Test, Remove Mark, VIPPO request, consignment), the derived flight envelope (Inference), F3 ≥ 300 hPa, an F12 "Landed" row, the chute-based landing load, the 20–22 AWG harness limit, part-temperature thermal limits with an interim bay limit of ≤ 55 °C, and the round 23 corrections to `round22_alternates.md`.
- *What the checks gained (D-R23-01 … D-R23-11; checks, two note texts, the binding note and records only):*
  - single-open taps 33 → 40, with 22 exact exceptions: BOOT0, VCAP1 / VCAP2, both pyro-bus FET gate vias, and U4's power-ground via;
  - K-rules reads the DRU as KiCad does and floors every DRU minimum (error severity only);
  - the JLC board measures take S-8's copper set;
  - K-legends covers Fab text boxes, visible fields, character width and board-level Fab shapes;
  - K-lands pins r10_parts' footprints and the paste totals (253 / 375);
  - check.sh runs the schematic contract and sheet replay first (about 6 s);
  - the binding note carries the 13 firmware rules (49 obligations).
- *Software tests, DRC and CAD gate:* the CAD lane's complete `r10_build.sh` (1586 s) gave PCB `5516eeec…` again, byte-identical to `c70d261`; its `tools/check.sh` exited 0:
  - DRC / unconnected / parity / ERC 0;
  - check_r10 36 / 36 rules; route_check 0 failing;
  - self-tests: shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 69, R10 261 (6 NumPy skips), NumPy 6.

  The package was re-bound (the sensors sheet note and the date-stamped outputs changed; BOM and CPL unchanged). Supervisor run: `tools/check.sh` exit 0 on the final tree (DRC 0 / unconnected 0 / parity 0 / ERC 0; schematic contract and sheet replay OK; check_r10 36 / 36; route_check 0 failing; fab content checks and the manifest OK; self-tests 11 / 34 / 33 / 16 / 5 / 69 / 261 (6 NumPy skips) / 6 OK).
- *Simulation and calculation:* none new from the docs lane; the lens figures quoted are Calculation / Inference as labelled.
- *Physical tests:* none.

**Round 22 review and between-rounds pass (2026-11-01).** Round 22's ten Claude lenses reviewed `5516eeec…` at commit `ec8cb98`: 0 Critical / 0 Major / 22 Minor (routing 1, power 2, parts 3, MCU 1, mechanics 1, safety 1, manufacturing 2, requirements 4, docs binding 4, gate 3). The between-rounds pass changed checks, one schematic note and records only (D-R22-NN), and the board is still `5516eeec…`, so rounds 22 and 23 remain the closing pair. The docs records: the §6 detour table now lists every net over +3.4 mm; the §1 surface inventory is carried to `5516eeec…`; single-via IC grounds and sense taps are recorded with firmware plausibility rules and a pre-flight PA6 / PA4 check; the dated franchised status of U4 / U9 and the owner's procurement choices (wait, order with U4 / U9 unfitted, a partial order, or a same-land alternate: TPS259470ARPWR for U9, which retries instead of latching off, or the LSM6DSV320XTR for U4; franchised or JLC sources only, never brokers) are in ORDERING 8.1; DB125 keep-offs and parts without a Fab outline are in ORDERING 8.2; J400 ESD handling and a first-article check are added; "EN 2.03 V" is now stated as nominal while R81 is intact.
- *What the checks gained (D-R22-01 … D-R22-07; checks, one schematic note and records only):*
  - K-rules now measures the board against the rest of JLC's hole table, whatever the DRU says: rings, holes, NPTH, via hole to copper, PTH to track, and hole to hole.
  - K-rules reads every DRU minimum in any unit or position.
  - K-power has seven more single-via taps as exact entries.
  - K-legends ties each Fab reference to its own part.
  - K-ports holds each port clamp's ground leg (≤ 1.0 mm; 0.7–0.8 mm on the board).
- *Software tests, DRC and CAD gate:* the CAD lane's two complete builds (items 1–4, then the gate items) both made PCB `5516eeec…` again and ended in `tools/check.sh` exit 0:
  - DRC 0 / unconnected 0 / parity 0 / ERC 0;
  - check_r10 36 / 36 rules; route_check 0 failing (6 unrecorded noncritical leftovers);
  - self-tests: shell 10, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 69, R10 253 (6 NumPy skips), NumPy 6.

  The fab package was re-bound because the diagnostics sheet changed. Supervisor run: `tools/check.sh` exit 0 on the final tree (DRC 0 / unconnected 0 / parity 0 / ERC 0; check_r10 36 / 36; route_check 0 failing; fab content checks and the manifest OK; self-tests 10 / 34 / 33 / 16 / 5 / 69 / 253 (6 NumPy skips) / 6 OK).
- *Simulation and calculation:* none new; the round 22 mechanics lens re-ran the plate model on `5516eeec…` with identical figures (Calculation/Inference).
- *Physical tests:* none.

**Round 21 fix pass (2026-10-31).** What changed: inner-layer copper is held 0.55 mm from every plated pad hole (J1.2, J400.2 and J3's shell holes were 0.251–0.451 mm; JLC's PTH pad limit is 0.3 mm); U2.1 got a second path and 26 regulator taps are checked for single-via opens (8 named exceptions); three schematic notes corrected; the arming chain is critical in route_check and BAT_ENABLE's jog is gone; R81 and C87 moved to U9's end of the EN run (one via left between U9.1 and R81, was three; the single opens there dropped from 13 to 4); new checks hold the tab keep-out, the port clamp placement (K-ports) and the Fab references; 93 designators hidden. Record: `round21_fix_cad.md`.
- *Software tests:* self-tests shell 10, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 69, R10 247 (6 NumPy skips under KiCad Python) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* two complete builds both made PCB `5516eeec…` and both ended in `tools/check.sh` exit 0 (DRC 0, unconnected 0, schematic parity 0, ERC 0; check_r10 36 / 36 rules; route_check 0 failing). The fab package is bound to the board, and fresh supplier evidence was run on the final files ($85.37; U4 and U9 short).
- *Simulation and calculation:* hot-plug inputs re-extracted, 2304 cases pass, extremes unchanged (Simulation/Inference). The fire budget changed only its board hash. With C87 beside R81, EN stays at the divider's 2.03 V nominal (≤ 2.06 V with 1 % parts, at 8.4 V; Calculation) while R81 is intact (EN absolute maximum 6.5 V, TI SLVSFC9C §6.1 p7).
- *Circuit check:* The pre-commit circuit check (Opus, max effort, on the staged change): PASS, 6 Minor. Five are records and notes, fixed by the CAD lane before the commit: the U2.1 run width, the battery_entry note naming Q120 / C88, the 3V3 via INFO, the plane strips at the west-edge terminals, and two wrong statements. The sixth is the AUD-2 sentence in AGENTS §3 (now names the J400 switch chain; owner row 30). It confirmed: the netlist is identical to HEAD (701 pad nets); with J400 open the single opens that float EN dropped from 13 to 4; every S-8 barrel and ring is ≥ 1.021 mm; the EN figures reproduce from SLVSFC9C and EN stays ≤ 2.06 V; U2.1 stays connected with each of the 31 3V3 vias opened; the inner Gerbers show J1.2 / J400.2 / J3 at 0.5505 mm; the JLC table figures hold.
- *Physical tests:* none. No firmware, bench or physical result exists. Rounds 22 and 23 later reviewed this board.

**Round 20 polish pass (2026-10-31).** What changed: U401's feedback tap now survives either OUT via (new via (30.575,11.6)); U1.74's pour fragment removed; TP82 moved to B(11.2,20.7); J121.1 and J400.2 lost their unconnected inner rings (J1.2's In2 ring went too, so In2 RAW_PROTECTED is 0.25 mm from that GND barrel); designators and Fab texts cleaned (96 hidden); an In2 keep-out under the west aft tab; D440 / D441 under J440; C87 text with the EN leakage. **Not done:** U9's EN pull-down beside U9.1 (D-R20-01: no legal B.Cu spot; owner deviation and respin item), the east tab keep-outs (owner's tab plan) and the optional VLOGIC via pair and GPS jogs (D-R20-10). Record: `round20_fix_cad.md`.
- *Software tests:* self-tests shell 10, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 68, R10 239 (6 NumPy skips under KiCad Python) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* two complete builds both made PCB `0dc84776…` and both ended in `tools/check.sh` exit 0 (DRC 0, unconnected 0, schematic parity 0, ERC 0; check_r10 35 / 35 rules; route_check 0 failing). The fab package is bound to the board; cost and stock were not re-run ($85.35 stands; the stock check fails on U4, 2 orderable against 5). The pre-commit circuit check (on the staged change) passed with 2 Minor: the D-R20-01 F.Cu respin option, and stale C87 / inner-ring figures in REQUIREMENTS / AGENTS, both fixed in that commit.
- *Simulation and calculation:* hot-plug 2304 cases pass, extremes unchanged (Simulation/Inference). C87 drop-out immunity 10.6 / 20.5 / 26.4 ms at 6.0 / 7.4 / 8.4 V and 8.5 ms at 5.73 V; turn-on 30–129 ms (Calculation).
- *Physical tests:* none. No firmware, bench or physical result exists. Round 21 later reviewed this board (`0dc84776…`).

**Round 19 fix pass (2026-10-30 to 2026-10-31).** What changed: PYRO1_OUT inner-layer keep-outs (GND now ≥ 1.021 mm from its barrels), the BAT_ENABLE via moved off R134.2, TP121 and its stub removed, C123 added (Q122's gate–source capacitor), U1.19's pour fragment removed, legends moved clear of the DB125 bodies, C84's paste removed, five second vias on single-via supply feeds, C87 2.2 µF → 220 nF, U4 changed to the in-stock ISM6HG256X, MCU text corrected, and the spare AUX port J440 (owner-approved 2026-10-30; the GPS moved to USART3 PD8 / PD9 and AUX took USART6 PC6 / PC7). Records: `round19_fix_cad.md` (board) and `round19_fix_docs.md` (documents) under `m3_design/assembly_review/sources/r10_review/`.
- *Software tests:* after the gate pass (D-R19-15), self-tests shell 10, procurement 20, fab_validation 34, fit 33, paste 16, r10_parts 5, route 68, R10 234 (6 NumPy skips under KiCad Python) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* the CAD lane ran two complete builds (9 and 10); both made PCB `50a39de5…` and both ended in `tools/check.sh` exit 0 (DRC 0, unconnected 0, schematic parity 0, ERC 0; check_r10 35 rules; route_check 0 failing). The fab package is bound to the board. The gate lane then hardened the checks without changing the board (D-R19-15: pad paste / mask against the library, part-number decoding, inner-fill necks, power-path design currents, a word-centre margin, a silkscreen allowlist, a pour-debris check; the port UARTs stay under the strict rules) and ran `tools/check.sh` twice, exit 0: check_r10 35 rules, all OK. It admits one 0.282 mm² GND pour fragment on U1.74 by a named entry (fix at the next board change) and reports the BAT / SWITCH word margins (0.080 / 0.040 mm against 1.0 mm) without blocking.
- *Simulation and calculation:* the hot-plug model passes all 2304 required cases on the new board (Simulation/Inference). Fire current 1.541 A idle, 1.279 A with four stalls; hold-up 0.464–0.539 ms with all ports on; C87 turn-on 30–129 ms (Calculation).
- *Physical tests:* none. No firmware, bench or physical result exists. Round 20 later reviewed this board (`50a39de5…`).

**IMU axis map.** U4 is on the bottom at B(17,45.9), rotation 180°. +X_imu = −x_board, +Y_imu = −y_board, +Z_imu points out of the bottom face. Roll about +y_board reads **−gyro_Y**, and forward thrust reads −a_Y.
The lever arm to the roll axis (x = 23) is x = −6.0 mm and z = −2.06 mm (z from the U4 3D model: Inference). In the IMU frame it is (+6.0, ·, +2.06) mm. Detail: [docs/M3_R10.md, "IMU axis map"](docs/M3_R10.md#imu-axis-map).

**Pin map and terminals.** The only reviewed pin map is column `r10_net` of `m3_design/assembly_review/sources/r10_design/pin_table.tsv`. The eight terminals, with positions, pin roles and wire entries, are in the [terminal table](docs/R10_VEHICLE_HANDOFF.md#terminals).

**Records.** Design record: [docs/M3_R10.md](docs/M3_R10.md). Reviews, owner questions and the deviation list: [docs/R10_VALIDATION.md](docs/R10_VALIDATION.md). Layout measurements and review items: [AVA_LAYOUT.md](m3_design/assembly_review/sources/r10_design/AVA_LAYOUT.md). Plan and decisions: `m3_design/assembly_review/sources/r10_design/` (`r10_plan.md`, `R10_DECISIONS.md`, with all 227 recorded agent decisions through D-R28-04). Earlier interim R10 boards (circuit pass, single switch, AUD/GAP, owner answers) and the round 3 to 8 fix-pass notes are in [docs/M3_R10.md, "Board history"](docs/M3_R10.md#board-history-superseded-interim-boards).

## Current candidate: M3-ASSY-R9 (clean-sheet B-spine layout, 46 × 102 mm, owner-accepted 2026-10-25)

**CAD and manufacturing files complete after build steps 1–10 of `r9_plan.md` (2026-10-20 to 2026-10-25), independent
review pass 1 (2026-10-25, on step 10's board `fc3d5b34…`) and its fix pass, which made the current board `4f841a0e…`:
R8's circuit laid out again from a clean sheet, with every safety and RF qualification re-derived on the current board.
Pass 1 found 0 Critical, 1 Major (confirmed as Minor) and 50 Minor; review pass 2 (on `4f841a0e…`) found 0 Critical,
0 Major and 32 Minor, so `r9_plan.md` §5's two consecutive clean passes are met and the pass-2 Minors are recorded, not
reworked (R9_VALIDATION "Review pass 2"). Owner-accepted on 2026-10-25 (REQUIREMENTS M2, "R9 acceptance"): the deviation
list, including the agent decisions (U4 turned 180° with roll = −gyro_Y, the crystal's local In2 GND plane), with the
board kept at 102 mm. Not a fabrication or flight release. R8 (below) stays the owner-accepted fallback.**
- Committed and pushed on branch `m3-assy-r9` (base R8 `9c8179b`) at the accepted state on 2026-10-25; the commit that adds
  this line holds board `4f841a0e…`.
- Board SHA-256 `4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14`, rebuilt byte for byte from R8's
  committed sources by `m3_design/r9_build.sh` (stages 0–38: schematic and footprint variants → placement → RF strip →
  pyro column → power → ten routing families → ground → silkscreen → `tools/check.sh`, each stage with its gate; two
  builds identical: the fix pass's stage replay and `r9_build.sh` run whole in a scratch clone); netlist `8b0e04ea…`
  (unchanged); fab package `m3_design/r9_fab.sh`. Step 10's board was `fc3d5b34…`.
- Record: [docs/M3_R9.md](docs/M3_R9.md); validation, requalification, review pass 1 and the deviation list:
  [docs/R9_VALIDATION.md](docs/R9_VALIDATION.md); ordering: [docs/ORDERING.md](docs/ORDERING.md) (now R9's; until R9 is
  accepted, order R8 from `m3-assy-r8`); plan, owner decisions (2026-10-20) and agent decisions D-S1-01 … D-S10-19 and
  D-F1-01 … D-F1-11: `m3_design/assembly_review/sources/r9_design/`; review pass 1 and its fix pass:
  `m3_design/assembly_review/sources/r9_review/`.

What changed from R8 (details in M3_R9):
- **Clean sheet:** nothing is held rigid by hash; `tools/check_r9.py` judges every block by rules (LC-1, P-0 … P-11,
  R-1 … R-13, M-2 … M-7, F9-1, T-1, the K-rules); the RF chains and launches are regenerated by template in each jack's
  and module's frame and shown congruent with R7's; the pyro column is drawn from its pads.
- **Layout (B-spine):** the RF strip aft (y 0–22.0, owner decision 3); U1 in the middle; the CH1 pyro column on the west
  edge as a dead end, both terminals' wires entering from −x; all power in the east column with a RAW_ACT spine on F.Cu,
  In2 and B.Cu; J122 turned. 102 mm long, owner decision 1's last fallback (D-S3-03): the plan's 98 mm and the 100 mm
  fallback cannot legalise the four MCU-end interface resistors against r9_plan's hard row X9 (≥ 5.94 mm from U1 / U3 /
  Y1, R8's measured R306–U1 distance) and the SERIES rule; under F10's own 5 mm the kill path holds at 100 mm (an owner
  option, R9_VALIDATION C1; R9P1-REQUIREMENTS-01).
- **Stricter pyro rules (owner decision 2):** rule G's P-1b scope, no local clearance override (LC-1; R8 had 29), zone
  fill margins, the strict pad rules (H + 0.2, gate-to-sense 1.2, actuator gate-to-GND 1.2 mm), battery-live copper
  ≥ 2.5 mm from armed copper (R8 1.0), inner RAW_ACT / BAT_IN ≥ 2.65 mm (R8 2.5), U1's gate pin ≥ 0.5 mm from any
  passing net (check_r9 P-7b, review pass 1); J121, J124 and J122 on mirrored-number variants of the same footprints
  (pads named by role).
- **IMU turned 180°** on the bottom (D-S7-06): roll = −gyro_Y (R8 +gyro_Y).
- **Unchanged:** every part, value and LCSC code (the BOM is R8's line for line but the three footprint fields); U1's pin
  map.

Review pass 1's fix pass (R9_VALIDATION "Review pass 1"; R9_DECISIONS D-F1-01 … D-F1-11), every copper change through
the generators: QSPI_IO2's escape 0.55 mm from the pyro gate pin U1.3 (was 0.25); R7's three ground vias at the radio
module's GND pins (0.20 / 0.35 / 0.35 mm of copper to a via, was about 1.1); RADIO_TXEN at the 0.2 mm signal width (five
track widths); no via in TP120's opening (was two); C98 beside U11's USB input; C121's GND return 1.38 mΩ (was
11.98 mΩ) through a recorded exception to the 7.7 A corridor rule and the ground aid's new copper stage (the worst outer
GND copper 9.50 mm of copper from a via, was 28.41; the forward-edge strip 6.04, was 12.45); check_r9 and pyro_probe
deterministic, R-7 sides named by compass, R-8 over U31's whole body; the records corrected (the length's cause, the
like-for-like R8 figures, the thin margins, the U9 limit, the single points, the bay stack, the IMU's modal position,
FMEA's IGN–BUS1 adjacency, ORDERING's order remarks).

Verification, stated separately:
- **CAD checks (done, `4f841a0e…`):** `tools/check.sh` exit 0 (the fix pass's build replay and its standalone gate run
  on 2026-10-25, with a GUI session and no shim): DRC 0 at every severity, unconnected 0, parity 0, ERC 0; metadata /
  3D audit OK; silkscreen inside the outline; fit OK (worst J9 mated 0.028 mm); plate model; seeded rule-H suite OK;
  check_r9 OK on all 40 rules; route_check r9 0 failing, 0 allowlisted, 0 leftovers; check_actuators OK. Every hard row
  of r9_plan §2 met; 34 done rows met and 16 missed, each miss with its record (R9_VALIDATION).
- **Manufacturing files (done, fix pass):** 92 BOM lines, 219 placed parts, CPL verified (78 top and 133 bottom rows
  rebuilt from JLC's footprints, 8 placement-only), paste check OK, manifest bound to `4f841a0e…`
  (`sources/r9_design/step10_evidence/fab.txt`).
- **Software tests:** 478 tests in 26 suites (KiCad Python) and quality_audit 21 (both Pythons) pass on `4f841a0e…`
  (`sources/r9_design/step10_evidence/tests.txt`); audit_artifacts exit 0.
- **Independent review:** pass 1 on `fc3d5b34…` (0 Critical, 1 Major confirmed as Minor, 50 Minor; every finding
  dispositioned in R9_VALIDATION "Review pass 1"); pass 2 on `4f841a0e…` (0 Critical, 0 Major, 32 Minor, recorded in
  R9_VALIDATION "Review pass 2").
- **Calculation (the requalification re-run on `4f841a0e…`, R9_VALIDATION "Requalification"):**
  - 7.7 A DC at 0.05 mm: RAW_ACT 0.80, BAT_IN 0.16, ACT_FET_S 0.26 mΩ; necks 7.89 / 8.15 / 5.18 mm on B.Cu, rising
    12.6 / 12.1 / 20.4 °C (IPC-2152, no plane credit, Inference), within D12's 20 / 20 / 30 °C and below R8's 17.5 / 14.5 /
    21.4 °C; largest via barrel currents 0.47 / 0.61 / 0.22 A; the servo GND return 0.32 mΩ (2.4 mV at 7.7 A, an upper bound; R8 0.69 mΩ);
  - fire loop (F7): 17.7 mΩ of board copper and 32.1 mΩ with the three FETs at their data-sheet maxima, so F7's budget is
    1.65 A at the 7.4 V floor against 1.5 × 1 A all-fire (met on the final copper; the harness stays a bench item);
  - supply paths (26, 0.1 mm): every drop under 80 mV at its load (the largest RAW_PROTECTED to U7, 77 mV at 1 A, as R8's
    76 mV; USB_LIMITED 43 mV at 0.5 A, R8 26 mV);
  - pyro: rule margins ≥ max(R8, 0.2 mm) but rule G's 0.112 mm at U1.3's pin entry (D-S5-13); U1's gate pin 0.55 mm
    from the nearest passing net (P-7b); 134 exposed pairs under 1.5 mm, 0 forbidden; no foreign net within 3 mm of
    armed copper (R8 6 / 7); bare gate copper ≥ 2.354 mm from bare armed copper (R8 1.027 mm);
  - RF: GCPW 50.16–51.08 Ω at all 79 samples; launches congruent with R7's; return loss (Inference) GNSS ≥ 22.6 dB,
    radio ≥ 23.6 dB; nearest RF part to a restricted part 6.04 mm; the radio module 46.13 mm from armed copper (owner
    decision 3);
  - critical-net reference (absolute): 10.22 % of samples unreferenced (R8 11.07 %), every one inside an own via
    antipad but one;
  - plate model f1 256.6 Hz pinned (R8 208.7 Hz); U4 and U5 on mode 1's antinode (0.76 / 0.89 of the peak; R8 0.18);
  - reverse hot-plug premise: the protection 4.69–8.90 mm and U9 13.22 mm from J1.1; U9 IN within 0.0021 V and × 1.028
    slew of the input node (Inference);
  - IMU axis map: roll = −gyro_Y, lever arm x −11.0 mm.
- **Cost and stock (live, 2026-10-26 00:59Z, the fix pass's `FAB_NET=1 m3_design/r9_fab.sh`):** $109.38 per board, 52
  extended codes (limits $126.41 and 52); short none, thin none (U4 40 and U30 34 in JLC stock); valid 24 h, so rerun
  before ordering.
- **Simulation:** none (the hot-plug, plate and fire-loop scripts are calculations). **Firmware:** none; a binding note
  records what the R9 binding must carry (`sources/r9_design/step10_evidence/r9_binding_note.json `). **Physical tests:**
  none.

**Needs the bench or the airframe** (ORDERING §5): every R8 item below, plus, for R9: the IMU sign check (roll =
−gyro_Y), the keyed-radio pyro-immunity test at the 46 mm radio-to-pyro distance (required before flight, owner
decision 3), the HSE frequency by MCO with the crystal's local In2 GND plane, the stall test with the FETs and J122 as
the judged items (on R9 D12's neck limits are a CAD check only: the RAW_ACT and ACT_FET_S necks lie at the FETs, the
BAT_IN neck under J1), the tap check against 256.6 Hz with the accelerometer at U4 and U4 logged, the reverse hot-plug at
U9 IN.

Open items:
- The pass-2 Minors (23 of 32 marked worth fixing, mostly record and procedure items) and the open pass-1 Minors not
  in the fix brief: recorded, not reworked under `r9_plan.md` §5's stopping rule (R9_VALIDATION "Review pass 1",
  "Review pass 2"); a later polish pass may take them.
- Before ordering R9: U4 in JLC stock or consigned; JLC's acceptance of four long-edge tabs on a 102 mm board (Inference,
  ORDERING §3); a cost and stock run within 24 h (`FAB_NET=1 m3_design/r9_fab.sh`).
- R9 firmware board binding (the IMU map changes, the pins do not).

## Previous candidate (owner-accepted, orderable fallback): M3-ASSY-R8 (R7 re-placed and re-routed, 46 × 118 mm)

**CAD and manufacturing files complete after build steps 0–9 of `r8_plan.md` (2026-10-19), review pass 1 (2026-10-19:
0 Critical, 1 Major, 38 Minor, on `429b6db4…`), fix pass 1 (2026-10-19), review pass 2 (2026-10-19: 0 Critical, 0 Major,
31 Minor, on `6600ef94…`), fix pass 2 (2026-10-20), review pass 3 (2026-10-20: 0 Critical, 0 Major, 26 Minor, on
`990c8040…`), fix pass 3 (2026-10-20), review pass 4 (2026-10-20: 0 Critical, 0 Major, 16 Minor, on `c84f00b8…`), its
records pass (2026-10-20, no copper change) and fix pass 4 (2026-10-20: pass 4's two copper Minors, D110 / D111, and four
record items), review pass 5 (2026-10-20: three reviewers, build integrity, planes and routing, on `cc044ea0…`:
0 Critical, 0 Major, 3 Minor) and its records pass (2026-10-20, no copper change). Passes 2–5 found no Critical or Major;
the other five review dimensions were not re-run on `cc044ea0…` (a further re-check is the owner's call); the owner accepted the R8 deviation list on 2026-10-20 (REQUIREMENTS M2 met in CAD, C10 vibration
item and agent decisions included); still open: U4 consigned, JLC's tab acceptance and a cost and stock run within 24 h. Not a fabrication or flight release.
R7 (below) was its fallback until then; R8 is now the fallback to R9 (above).**
- Committed as `9c8179b` on branch `m3-assy-r8` (base R7 `431025d`; board `cc044ea0…`), after the text below was written; its
  project and ORDERING live there (this branch's `docs/ORDERING.md` is R9's).
- Board SHA-256 `cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7` (fix pass 4; review pass 1 reviewed the
  step-9 board `429b6db4…`, review pass 2 fix pass 1's `6600ef94…`, review pass 3 fix pass 2's `990c8040…`, review pass 4
  fix pass 3's `c84f00b8…`; this board's copper differs from `c84f00b8…` by exactly the pass-4 routing reviewer's trialled
  `rec4`; review pass 5 re-checked this board), rebuilt byte for byte from R7 by `m3_design/r8_build.sh` (schematic → placement →
  power → nine signal families → ground → the 7.7 A neck limits → silkscreen, each with its gate, then `tools/check.sh`;
  two consecutive builds identical); netlist `0cc1ed69…`; fab package `m3_design/r8_fab.sh`.
- Generator state: committed since as `9c8179b` (before that commit: commit or tag it (`git add -A`) and record the commit beside
  `cc044ea0…` here and in R8_VALIDATION, owner action; R8P3-INTEGRITY-04, R8P4-INTEGRITY-01, R8P5-INTEGRITY-01: the
  state pass 4 reviewed survives only in the coordinator's scratchpad backup, and `cc044ea0…`, the one pass 5 reviewed,
  only in this worktree); the hashes fix passes 2, 3 and 4 started from are in
  `sources/r8_review/fix2_baseline_sha256.txt`, `fix3_baseline_sha256.txt` and `fix4_baseline_sha256.txt`, with each
  pass's code diff (`fix2_generators.diff`, `fix3_generators.diff`, `fix4_generators.diff`).
- Record: [docs/M3_R8.md](docs/M3_R8.md); validation and the deviation list: [docs/R8_VALIDATION.md](docs/R8_VALIDATION.md);
  ordering: [docs/ORDERING.md](docs/ORDERING.md) (now R8's); decisions D1–D111 (fix pass 1: D85–D96; fix pass 2: D97–D105; fix pass 3: D106–D109; fix pass 4: D110–D111):
  `m3_design/assembly_review/sources/r8_design/R8_DECISIONS.md`.

What changed from R7 (details in M3_R8):
- **Kept rigid and hash-asserted** (12 digest groups, `tools/check_r8.py`): the outline, the five M3 holes, J122 and its tie
  holes, J1, the CH1 pyro block with its copper and PYRO_BLOCK area, and the RF strip's parts, RF lines and GND copper.
  `check_actuators` is byte-identical.
- **Re-placed:** 193 parts (58 changed side): U1 at rotation 0 with the flash and crystal under it; every block beside the
  U1 face it talks to; the input protection at J1; the actuator FETs face to face beside J1; TH1–TH3 removed.
- **Pins:** 27 U1 pins (radio SPI2 on PB10 / PB11 / PB14 / PB15 with IOSWP, RXEN PD9, DIO1 PE15, NRST PE9; GNSS RESET_N
  PD14, TIMEPULSE PD15; camera UART on UART7 PE8 / PE7) and R310 on 3V3; every pin cited in `pin_table.tsv`. The pyro,
  servo and sentinel pins are unchanged. BOM identical to R7's.
- **Copper:** all new, from tables: 1500 mm of signal track (R7 3355 mm), 55 signal layer-change vias (R7 217), no signal on
  In1 / In2 but the rigid block's 3.4 mm link, a GND via by every critical layer change but A8; 7.7 A necks 5.94 / 6.99 / 4.97 mm
  (R7 3.00 / 3.82 / 2.65 mm).
- **Fix pass 1** (R8_DECISIONS D85–D96): battery-live ACT_FET_S and RAW_ACT pours pulled ≥ 1.0 mm from J124.1 and the
  gate pad R127.1; HSE_OUT's fold-back removed; the GNSS limiter vias and the VLOGIC hold-up via clear of paste
  apertures; U10's bypass C83 beside U10; J3's GND legs thermally relieved; pour trim G7 in the radio bus; four
  signal-to-signal gaps opened and three chain detours redrawn; J1's pin legends over their own pins; the left forward
  panel tab off the battery band; new gates (`check_r8` battery_pyro, via_paste, terminal_legends; the DC neck limits in
  the build); the M2 review sweep as a script and a completed deviation list.
- **Fix pass 2** (R8_DECISIONS D97–D105): the In2 BAT_IN island cut back to the outer BAT_IN pours (no battery copper at
  the right panel tab or the M3 hole (42, 114.4)); four close vias at the board's 0.5 mm size; R81 moved off the battery
  feed; C83.2's GND link without its jog; J123.2 thermally relieved on the final copper; a GND via at the logic eFuse's
  GND terminal (U9.8, 14.1 → 2.5 mm of copper) from a new step-7 rule; `check_r8.battery_pyro` also guards the drain;
  the M2 sweep measures pad-to-copper gaps; the stall test rewritten; the bootloader binding puts the pyro gate (PE4) low.
- **Fix pass 3** (R8_DECISIONS D106–D109): USB_LIMITED's 5 V trunk and R172 moved 0.05 mm (CAM_PWR_EN 0.150 → 0.200 mm,
  R172's pads, one on PB0's pin side, 0.180 → 0.230 mm); CAM_PWR_EN's lower leg redrawn with one 45° run (1.98 mm
  shorter); R165's BAT_ENABLE via drawn as the 0.5 mm signal via (0.180 → 0.23 mm from Q120's bare BAT_IN drain pad); the
  M2 sweep also searches at DRC's threshold; the actuator-gate-to-GND item closed without copper (the pour, not the via,
  is the nearest GND, as on R7); records: the bootloader-jump order (PE4 low, radio asleep, GPIOE reset last), new bench
  steps in ORDERING §5 (the pyro gate in the bootloader, the camera supply's load step, IMU signs, the L5 spur, the stall
  test read clear of J122), F9's pad-edge figures, single-via points, and record slips.
- **Records pass after review pass 4** (no copper, schematic, placement or build-output change; no D-number): ORDERING §5's
  bootloader pyro-gate check moved into the pyro-gate list (repeated after any firmware change) with a check that the
  board is still in the bootloader; the coexistence step gains UBX-MON-SPAN spectra of both GNSS bands, a radio-asleep
  condition and a reference receiver (the radio crystal's 32 MHz × 37 = 1184 MHz harmonic named); the stall test states
  that its forward window bounds the neck loosely and gives J122 a ≤ 30 K pass line; `step9/requalify.py` gains pyro rule
  G (0.300 mm, the one rule at zero margin); the pull-pin no longer called a launch detect; stale figures and the review
  status made consistent across README, ORDERING, STATUS, AGENTS and R8_VALIDATION.
- **Fix pass 4** (R8_DECISIONS D110–D111; the pass-4 routing reviewer's trialled `rec4`, nothing else in the copper): the
  radio trio RXEN / BUSY / MISO centred in its strip-fence opening (its below-fence lanes 0.1 mm west, step 0.5 mm) with
  two fence vias and the MISO–MOSI stitch via 0.05 mm west, so MISO and MOSI are 0.200 mm from both GND vias (were
  0.150 mm; C12 #5 / #6 gone); R87.1's branch drawn as one T drop off the USB_LIMITED trunk (1.86 mm shorter, the acute
  branch and doubled run gone; C21 gone); records: ORDERING §5's camera-supply distances per part, the thermal-relief rule
  as built (twelve 0805 / 1206 GND pads on spokes), R70's fix-pass-3 designator move, `r8_build.sh`'s trim count. No part,
  designator or silkscreen item moved; BOM and CPL unchanged.
- **Records pass after review pass 5** (no copper, schematic, placement or build-output change; no D-number): the
  scorecard intro and fix pass 4's handoff now say that of the P, R and D rows only R7's extended sample count moved
  (+24, R8P5-PLANES-01); fix pass 4's notes name the In2 3V3 antipad that moved with the stitch via, area unchanged
  (R8P5-INTEGRITY-02); the review status updated in R8_VALIDATION, M3_R8, README and ORDERING (AGENTS.md not edited:
  its §1 row still calls the board unreviewed).

Verification, stated separately:
- **CAD checks (done, final board `cc044ea0…`, fix pass 4, both builds and standalone):** `tools/check.sh` exit 0: DRC 0 at every severity, unconnected 0,
  schematic parity 0, ERC 0; metadata / 3D audit OK; silkscreen inside the outline; R8 CAD contract (`check_r8`) OK;
  routing hygiene 0 failing, 3 allowlisted (A8 and D51's two limiter detours), 0 leftovers; actuator safety contract OK;
  fit OK (CAD envelopes; every category ≥ R7's: J9 mated 0.03 mm, C84 1.37 mm).
- **Manufacturing files (done, fix pass 4):** 92 BOM lines (R7's byte for byte), 219 CPL rows (`ef90bfa1…`, unchanged by
  fix pass 4; only R172's row changed in fix pass 3), every row with a verified
  correction (85 top + 126 bottom rebuilt from JLC's footprints, worst residual 0.491 mm); paste check OK; manifest bound to
  `cc044ea0…`.
- **Software tests:** 272 tests in 17 suites (KiCad Python; fix pass 1 added three seeded-defect tests, fix pass 2 a drain
  case to the battery-live one) and quality_audit 21 (both Pythons) pass, run after the fab step (fix pass 4's log:
  `step9/evidence/fix4_tests.txt`).
- **Independent review:** pass 1 (eight reviewers, 2026-10-19, `429b6db4…`): 0 Critical, 1 Major (the deviation list
  left out whole M2 review categories), 38 Minor; every finding fixed or dispositioned in fix pass 1 (R8_VALIDATION
  "Review pass 1"). Pass 2 (eight reviewers, 2026-10-19, `6600ef94…`): 0 Critical, 0 Major, 31 Minor; every finding fixed
  or dispositioned in fix pass 2 (R8_VALIDATION "Review pass 2"). Pass 3 (eight reviewers, 2026-10-20, `990c8040…`):
  0 Critical, 0 Major, 26 Minor; every finding fixed or dispositioned in fix pass 3 (R8_VALIDATION "Review pass 3").
  Pass 4 (eight reviewers, 2026-10-20, fix pass 3's board `c84f00b8…`): 0 Critical, 0 Major, 16 Minor; nine fixed in its
  records pass (procedure, records, `requalify.py`), the two copper Minors and the four record items left open applied in
  fix pass 4, the commit left to the owner (R8_VALIDATION "Review pass 4"). Pass 5 (three reviewers: build integrity,
  planes and return paths, routing; 2026-10-20, fix pass 4's board `cc044ea0…`): 0 Critical, 0 Major, 3 Minor; the two
  record items fixed in its records pass, the commit left to the owner (R8_VALIDATION "Review pass 5"). The other five
  dimensions (pyro, requirements, RF, power, DFM) were not re-run on `cc044ea0…` (a further re-check is the owner's call).
- **Calculation (CAD copper and datasheets; step 9 on the final board):**
  - 7.7 A DC at 0.05 mm on `cc044ea0…` (equal to fix passes 2 and 3's, line for line): RAW_ACT 1.45, BAT_IN 0.45, ACT_FET_S 0.18 mΩ; IPC-2152 neck rises 17.5 / 14.5 / 21.4 °C
    (no plane credit, Inference), within D12's 20 / 20 / 30 °C (R7: 38 / 30 / 44 °C, accepted as estimated); largest via
    barrel currents 0.86 A (RAW_ACT) and 0.65 A (BAT_IN); the servo GND return 0.69 mΩ (5.3 mV and 0.041 W at 7.7 A);
  - critical-net reference (`tools/reference_audit.py`, absolute): 11.07 % of samples unreferenced, every one at a via
    antipad or under the crystal's deliberate In2 keep-out; none over another net's fill, a split or a void (R7 27.9 %);
  - pyro block: rigid, spacing margins and bare-copper leakage distances re-measured (R8 = R7 inside the block; 7 non-pyro
    nets within 3 mm of armed copper against R7's 23; battery-live copper ≥ 1.0 mm from the ARM side since fix pass 1);
  - RF: strip rigid (50.3 Ω field solve, launch, stitching carry over); nearest RF part to a restricted part 5.94 mm
    (R306–U1), logic buck ≥ 43 mm from both modules;
  - plate model f1 209–490 Hz with the sled carrying the SMA plugs, 6–8 % below R7 (C84 on the mode-1 antinode; Inference
    inputs);
  - reverse hot-plug: the protection parts at J1 (3.9–10.6 mm, J1.1's centre to each part's nearest pad centre; 1.9–7.8 mm
    pad edge to pad edge) restore the R4 model's premise; U9's 27 mm feed adds ≤ 0.002 V and 0.8 %
    slew at U9 IN (Inference);
  - IMU axis map unchanged; the lever arm's sign flips (U4 13 mm west of the axis).
- **Cost and stock (live, 2026-10-19 23:51Z, step 8):** $106.00 per board, 52 extended codes (limits $126.41 and 52); U4
  out of JLC stock, to be consigned (ORDERING §1). The BOM is unchanged by fix passes 1–4; the reports' CPL binding is
  stale (C83's, R81's and R172's rows; fix pass 4 changed none) until the next `FAB_NET=1` run, due within 24 h of
  ordering.
- **Simulation:** none (the hot-plug and plate scripts are calculations). **Firmware:** none; a binding note records what
  the R8 binding must carry (`sources/r8_design/step9/r8_binding_note.json `). **Physical tests:** none.

**Needs the bench or the airframe** (ORDERING §5): every R7 item below, plus, for R8: the reverse hot-plug scoped at U9 IN
(now 27 mm from the input node), the camera buck's remote sense at J9.1 under a load step (D41), the IMU signs with the
new lever-arm sign, the tap check against 209–490 Hz, the 7.7 A thermal-camera stall test (ORDERING §5: steady state,
the RAW_ACT neck against D12 read at least 3 mm from J122's pads, a loose bound there, with the whole neck recorded, J122
at ≤ 30 K rise, the FETs against MARGIN R1, D105), the board turning off with the ARM link in, the GNSS C/N0 per band (L1
and L5: the HSE's 63rd and 47th harmonics, the radio crystal's 37th) with the camera supply on, plus UBX-MON-SPAN spectra,
a radio-asleep condition and a reference receiver, the radio held in reset in the ROM bootloader, and the pyro gate there
(D6.8; ORDERING §5's pyro-gate list: TP122, the bootloader confirmed with USB unplugged, the static gate; repeated after any
firmware change).

Open items:
- The owner's dated acceptance of R8_VALIDATION "R8 deviations for owner acceptance" (3 allowlist entries, 0 leftovers,
  20 review rows, 91 information instances, and the agent decisions it names), or more work first. Fix pass 4 applied
  review pass 4's two removable copper Minors (C12 #5 / #6 and C21 are gone); review pass 5 re-checked `cc044ea0…` in
  three dimensions and changed no list entry; a re-check in the other five is the owner's call.
- Commit or tag `m3-assy-r8` at this state and record the commit beside `cc044ea0…` here and in R8_VALIDATION (owner
  action, R8P5-INTEGRITY-01): done, `9c8179b`.
- Vibration (R8_VALIDATION C10): f1 6–8 % below R7's; moving C84 toward a support recovers about 17 Hz (owner or review).
- Before ordering R8: U4 consigned; JLC's acceptance of five long-edge tabs without a forward rail (D35, Inference); a cost
  and stock run within 24 h.
- R8 firmware board binding; 52 of 52 extended codes (any new code needs one removed).

## Earlier candidate (owner-accepted 2026-10-18): M3-ASSY-R7 (on-board GNSS and radio, 46 × 118 mm)

**CAD and manufacturing files complete after review passes 2–8 and their fixes (2026-10-18); review pass 8 on the final
board found 0 Critical / 0 Major (10 Minor, recorded in R7_VALIDATION). Not a fabrication or flight release.**
- Committed as `431025d` on branch `m3-assy-r7` (base R6 `3b215ba`); its project and ORDERING live there (this branch's
  `docs/ORDERING.md` is R8's).
- Board SHA-256 `c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3` (fix pass 7), rebuilt byte for
  byte from the R6 board by `m3_design/r7_build.sh` (twice, by F8): `r7_pcb` → `r7_route` (with `r7_redraw`) → `r7_rework` →
  `r7_hygiene` → `r7_polish` → `r7_post`. No router session is replayed.
- Record: [docs/M3_R7.md](docs/M3_R7.md); validation: [docs/R7_VALIDATION.md](docs/R7_VALIDATION.md); ordering:
  `docs/ORDERING.md` on branch `m3-assy-r7` (431025d).
- **Owner acceptance (2026-10-18):** the R7 deviation list (R7_VALIDATION "R7 deviations for owner acceptance": 45
  allowlist entries, 29 leftovers, 25 review rows; 10 AGENTS §3 items) is accepted, with the 7.7 A copper rise accepted as
  estimated, so REQUIREMENTS M2 is met in CAD. **Before ordering:** U4 consigned and JLC's written confirmation of the
  forward panel rail.

What changed from R6 (details in M3_R7):
- **Removed:** the external radio/GPS harness ports J130/J131, their reset-off 4.8 V port supply (U14–U16, L4)
  and protection (37 references).
- **Added, in an RF strip at the aft end (y 0–23.5):**
  - u-blox MAX-F10S GNSS (U30) and EBYTE E22-900MM22S SX1262 LoRa radio (U31), both on the main 3V3 through
    ferrites;
  - an edge-launch SMA jack for each on the aft edge (J30, J31; 9.5 mm overhang), with RF ESD;
  - 0 Ω pi networks with DNP shunts (C303, C305, C313, C314; no paste);
  - a hardware current limiter on the antenna bias, with a DNP compensation footprint (C304).

  The radio is held in reset by a pull-down whenever the MCU is not driving it.
- **Board:**
  - 46 × 118 mm, every R6 item +18 mm in y; supports at (4, 4), (42.3, 4), (4, 64), (4, 114.4), (42, 114.4);
  - stackup JLC041611-7628; 50 Ω coplanar lines (W 0.30 / gap 0.25 mm) with In1 cut under the SMA pads; GND
    fence and stitching lattice; zone-fill keep-outs against pour slivers and unstitched fingers, which never take a
    pad's relief;
  - U1 re-pinned: radio on SPI2 (PB12–PB15) plus PD8–PD10 and PE15, GNSS on USART6 (PC6/PC7) plus PC8 and PD14.
- **Routing:** the whole board, inherited R6 copper included, was cleaned in fix passes 2–6 (SWCLK and SWDIO
  rerouted in pass 3; PYRO1_CONT on a plane-preserving route, CAM_UART_OE and NRST's J2 branch rerouted, 10 nets'
  debris redrawn and two band staircases removed in pass 4; in pass 5 the last band staircases, QSPI_CLK's tiny jog
  and the non-critical jogs removed, CAM_TX_WIRE taken off In1 (no signal copper on In1), GND vias at ARM1_SENSE's
  layer changes, the band-end split crossings removed, the forward edge stitched, and the part-D tidy-ups made; in
  pass 6 QSPI_IO3's square bump, SW_NODE's jog and short segments, LOGIC_SS's knee, the 3V3 C179 dip, RAW_ACT's B.Cu
  duplicate and six GND ties removed, BAT_IN_F given two stitching vias, and SERVO4_MCU / CAM_FAULT_N spaced; in pass 7
  the local bumps on 3V3A, CAM_5V, VLOGIC and both ends of A34's 3V3 run, a redundant 3V3 via joined only by
  overlap, ACT_EN's layer hop, two duplicate 3V3 plane hops, ARM1_SENSE's pass through R180.1 and CAM_FAULT_N's,
  I2C1_SDA's and CAM_5V_SENSE's detours removed, the BAT_IN_B lobe fenced off again, the 3V3A hop restored to its
  0.200 mm drawing and the 7.7 A necks widened without moving a part) and is held by a clean-routing gate
  (`tools/route_check.py` in `tools/check.sh`; since fix pass 5 it re-measures every allowlisted or recorded reason,
  since fix pass 6 it gates detours and series layer hops on nets with a pour, and since fix pass 7 local bumps and
  vias joined only by overlap on critical nets).
  What the gate enforces and what review checks is in REQUIREMENTS M2.
- **Requirements:** F10 rewritten for the on-board modules; P1 maximum 120 mm; M2 clean routing over the whole
  board; M3 cap $126.41 per board and 52 extended codes (owner, 2026-10-15).

Verification, stated separately:
- **CAD checks (done, final board):** `tools/check.sh` exit 0:
  - DRC 0, unconnected 0, schematic parity 0, ERC 0;
  - metadata/3D audit OK; 0 silkscreen points outside the outline;
  - R7 CAD contract OK (pin contract, reset-state parts, strip net lists, RF-part coverage, RF grounds, DNP paste,
    via-in-SMD-pad, stitching, launch In2 reference, module ground, strip GND reach, thermal reliefs, legends beside
    their parts);
  - routing hygiene 0 failing, 45 allowlisted with measured reasons, 0 stale, 0 out-of-date no-GND reasons, 29
    non-critical leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0 removable jog /
    staircase / short-segment / chain-detour exceptions, 1 removable local bump (USB_LIMITED's, allowlisted with its
    measured reason);
  - actuator safety contract OK;
  - fit OK (CAD envelopes only; worst J9 mated 0.03 mm, C84 0.11 mm; supports clear, bare and DNP bottom pads
    included).
- **Manufacturing files (done, final board):** `tools/export_fab.py`:
  - 92 BOM lines (one per LCSC code), 219 placed parts and CPL rows; no part without an LCSC code; BOM and CPL
    byte-identical to fix pass 6's (CPL unchanged since fix pass 2);
  - every CPL row has a verified correction (`--verify-cpl`: 211 rebuilt from JLC footprints, 8 placement-only,
    worst residual 0.491 mm);
  - DNP placeholders (C303, C304, C305, C313, C314) in no BOM or CPL; no paste on them or on the SMA pads
    (Gerbers parsed);
  - manifest OK, bound to `c872a3d3…` (regenerated by F8 and again by the records agent).
- **Software tests:** test_check_shell 2, test_dc_solve 3, test_fab_validation 23, test_fit_check 23,
  test_maze_clearances 10, test_procurement 15, test_r6_check 17, test_r7_check 35, test_route_check 50 and
  quality_audit 21 (under both Pythons) pass (199 tests). `test_r5_repair` fails one subtest that checks literal R5 geometry; it fails
  on R6 too (M3_R7).
- **Independent review:**
  - Pass 1, three reviewers on the R6 baseline: 0 Critical, 16 Major, all dispositioned.
  - Pass 2, eight reviewers on the step-B board, with three skeptics per Major: 0 Critical, 26 Major (all upheld;
    7 re-graded to Minor), 51 Minor.
  - Pass 3, eight reviewers on the fix-pass-2 board: 0 Critical, 3 Major (all upheld; 1 re-graded to Minor),
    36 Minor.
  - Pass 4, five reviewers on the fix-pass-3 board: 0 Critical, 2 Major (both upheld; the skeptics' majority
    re-graded P4-ROUTING_GEOMETRY-01 to Minor), 16 Minor. P4-ROUTING_GEOMETRY-01 (a false "no legal GND via spot"
    reason on PYRO1_GATE_N) is fixed, with a gated audit of every such reason. **P4-DOCS-01 (M2 not met) is partly
    fixed:** staircases 4 → 2, critical layer changes without a GND via 11 → 10, non-critical debris 14 → 2, every
    leftover recorded with a measured reason; the owner's acceptance is open. Every finding is dispositioned in
    R7_VALIDATION.
  - Pass 5, four reviewers on the fix-pass-4 board: 0 Critical, 2 Major (both upheld; P5-ROUTING_GEOMETRY-01
    re-graded to Minor), 15 Minor. P5-ROUTING_GEOMETRY-01 (three untrue allowlist reasons) is fixed by removing the
    three instances; **P5-DOCS-01 (M2 not met) is partly fixed:** 15 of the 18 part-D items removed, D8 counted and
    reasoned, the deviation list rewritten with the AGENTS §3 instances marked; the owner's acceptance is open. Every
    Minor is fixed or recorded.
  - Pass 6, four reviewers on the fix-pass-5 board: 0 Critical, 2 Major (both upheld; P6-ROUTING_QUALITY-01
    re-graded to Minor), 11 Minor. P6-ROUTING_QUALITY-01 (QSPI_IO3's inherited square bump) is fixed. **P6-DOCS-01
    (detours and extra vias on poured nets neither gated nor listed) is fixed in the gate and the records**: the gate
    now holds them (13 allowlisted, 10 removed), and the records pass measured the chain detours and the short layer
    hops the gate does not judge (C17, C23–C26), finding five items it judged removable (one, LED_RED, proved not
    to be); pass 7 found the sweep incomplete (local bumps inside longer runs, a 3V3 via joined only by overlap and an
    8 mm layer hop: P7-ROUTING-01, P7-DOCS-01). The two misplaced silkscreen legends (P6-DOCS-04(d)) were fixed in
    fix pass 7.
  - Pass 7, three reviewers on the fix-pass-6 board: 0 Critical, 2 Major (both upheld), 8 Minor. P7-ROUTING-01
    (needless local bumps on critical power nets that neither the gate nor the list held) and P7-DOCS-01 (a redundant
    3V3 via joined only by overlap, unlisted) are fixed in copper, and the gate now tests both classes (`local_bump`,
    `via_on_track`); every Minor is fixed or recorded, the two far legends included. Of the fix-pass-6 records' five
    "removable" items four were removed and one (LED_RED) proved not removable. The owner's acceptance is open.
  - Pass 8, three reviewers on the fix-pass-7 board `c872a3d3…`: 0 Critical, 0 Major, 10 Minor (recorded, not reworked;
    R7_VALIDATION "Review pass 8"). This met the review-loop stopping rule; the owner accepted the deviation list on
    2026-10-18.
- **Calculation (CAD copper and datasheets):**
  - DC solve on the final board with its own stack-up (30 µm inner copper; `tools/dc_solve.py` reads it since fix
    pass 4): RAW_ACT 3.74, BAT_IN J1 → Q120 3.03, ACT_FET_S 1.19 mΩ at 0.1 mm (3.71 / 3.03 / 1.16 at 0.05 mm; fix
    pass 6: 3.98 / 4.58 / 1.36); BAT_IN drops 23 mV and dissipates 0.18 W at 7.7 A; BAT_IN J1 → U9.5 13.64, C89 / C95
    → U9.5 7.05 / 5.60 mΩ; 3V3 L1 → U1.75 15.6 mΩ, L1 → FB31 12.9 mΩ; track-limited paths good to about ±5 % (M3_R7
    §"DC solve");
  - IPC-2152 estimate of the 7.7 A copper (F8 on the final board; M3_R7): necks RAW_ACT 3.00 mm (F.Cu), BAT_IN
    3.82 mm (In2), ACT_FET_S 2.65 mm (B.Cu) (fix pass 6: 2.18 / 3.71 / 2.15); Brooks & Adam's IPC-2152 fits give 38,
    30 and 44 °C for a long conductor of the neck width at a continuous 7.7 A with no plane, 19, 13 and 37 °C at the
    median width, about 18–20 °C at the necks with plane credit (Inference); MARGIN P1-9's 10 mm mirrored copper is
    not met; no requirement sets the limit (owner; F4 bench stall test);
  - antenna-bias short current 37–48 mA cold, 25–38 mA hot (Inference); 3V3 load 0.69 A worst case against the
    2 A buck;
  - RF lines 50.3 Ω by field solve (JLC 50.24 Ω);
  - plate model f1 221–313 Hz pinned with the sled carrying the SMA plugs (R6 241–341 Hz; Inference inputs;
    computed on the pass-2 board);
  - critical-net reference sampling: 603 R6-referenced samples lost (R6: 0), at vias, on R6 paths R7 abandoned and
    at CAM_MCU_RX's In2 crossing under QSPI_NCS (fix pass 3's PYRO1_CONT losses are gone); 882 candidate-new (21
    from QSPI_CLK's fix-pass-5 step past RXEN's via antipad); fix passes 6 and 7: 0 lost, 0 new.
- **Cost and stock (live, 2026-10-18 22:02Z cost, 22:03Z stock):** $105.98 per board, 52 extended codes (limits $126.41 and 52;
  no code to spare); fixed two-sided fees $83.96 per order. **U4 (LSM6DSV320X) is out of JLC stock:** buy and
  consign it (ORDERING §1). `check_procurement.py --cost-only` OK; the full gate fails on U4.
- **Simulation:** none. **Firmware:** none; the R7 board binding is a follow-up (AGENTS §3). **Physical tests:**
  none.

**Shown in CAD:**
- connectivity and every DRC rule (pyro spacing, RF line width and gap, module keep-outs, SMA edge clearance);
- the gated part of M2's clean-routing list (`route_check`: 0 failing), with 45 allowlisted deviations, 29 recorded
  leftovers and the review items listed in R7_VALIDATION "R7 deviations for owner acceptance" (M2 itself is not met
  until the owner accepts that list);
- the pin contract and the reset-state parts (`check_r7`);
- no RF part pin on a pyro, arming, actuator, RAW_ACT, BAT_IN, BOOT0 or NRST net (`check_r7` at pad level, with
  every part on a radio or GNSS net covered, plus DRC and parity);
- the strip's ground copper within 4 mm of a GND via, In2 under the launches, In1/In2 under the modules;
- RF-part distances from the bucks, MCU and crystal; fit envelopes including the mated SMA plugs; placement
  corrections; DC copper resistance.

**Needs the bench or the airframe** (ORDERING §5):
- the antenna-short current and limiter stability (fit C304 if it oscillates);
- RF match (pi-network tuning, shunt stubs included), J30–J31 isolation and GNSS C/N0 with the radio keyed
  (≥ 39 dB);
- pyro-channel immunity to the transmitter; radio NRST held low in reset;
- 3V3/3V3A disturbance at transmit key-up; the USB-only transmit budget;
- SMA joints (centre-to-shell check, leg fillets), D30, D31 and C302 seated flat (first-article inspection),
  counter-held torque and staking; U30 paste at 0.10 mm;
- the NRST gate after J2 is taped and coated;
- the tap/modal check on the sled; the thermal-camera servo stall test;
- coax and camera-shroud fit; every R6 bench gate.

Open items:
- (Done 2026-10-18: the owner accepted R7_VALIDATION "R7 deviations for owner acceptance"; review pass 8 on
  `c872a3d3…`, the board that would be ordered, found 0 Critical / 0 Major.) Optional further rerouting (left removable:
  C27's two non-critical local bumps, kept by judgement; not examined: C23's 0.74 mm BAT_IN piece; not attempted: the
  cosmetic C17 / C19 / C21 / C22 tidy-ups).
- The IPC-2152 rise of the 7.7 A copper (deviation C1): the owner's limit, or ACT_GATE / parts moved or a
  battery-corner re-layout; the F4 bench stall test either way.
- Minors not done: wider unstitched GND fingers (C11: 23 under 0.75 mm, 48 under 1.0 mm; fix pass 7 added two and
  narrowed one, not searched for a via spot) and RF checks in the gate (P4-RF-01, P4-RF-02).
- The JLC order-number placeholder moved to (22.9, 86.15) on B.SilkS (ORDERING §3).
- U4 consignment; the stock tools have no consignment path (`pass1_requirements.md` R7P1-18).
- JLC's written confirmation of the forward panel rail, or of assembly with the forward 50 mm unsupported
  (ORDERING §3).
- Board position and coax loop zone against the camera shroud (Onshape measurement); plug and coax choice, with
  its mating torque. The parent VEHICLE.md stack row and CLAUDE.md E22 wording are done (parent `43af048`); two
  additions to the row (J1's forward entry, standoffs ≥ 3.5 mm) are proposed to the coordinator.
- 52 of 52 extended codes: any new code needs one removed.
- R7 firmware board binding.

## Previous candidate: M3-ASSY-R6 (one recovery channel, external radio/GPS ports, 46 × 100 mm)

Committed as `3b215ba`. Its final CAD validation (DRC/parity/ERC 0, review Critical 0 / Major 0, $84.14 per board and 48 extended codes, U4 short) is recorded in [docs/M3_R6.md](docs/M3_R6.md) §"Final R6 CAD validation" and in the R6 sections at the end of this file, which are its working log; the early "stopped incomplete" notes there were superseded by that final validation. R6 was never ordered. R7 replaces its external ports with the on-board modules.

## Previous candidate: M3-ASSY-R5 (two-sided re-layout, 46 × 100 mm)

**Fourth implementation pass complete (2026-10-12):** [R5_VALIDATION.md](docs/R5_VALIDATION.md) records the independent findings, repairs and remaining qualifications. The final native board is SHA-256 `6fc208d613dc2c1a6e9381ec3e1a5888c223ea6246336ae8320421272ca93a43`. Local bypassing, crystal-area QSPI routing, MEMS routing/lands, assembly spacing, five annotation objects and nine route fragments are repaired and independently reviewed. Fresh DRC, unconnected, schematic-parity and ERC counts are all zero; the actuator contract, modeled fit, metadata/model and silkscreen checks pass. The fabrication package is regenerated and independently checked against this board. **These are CAD and manufacturing-file results, not physical robustness or flight qualification.** Earlier “no open Critical or Major” statements below describe their historical review scope.

Design record: [docs/M3_R5.md](docs/M3_R5.md); requirements: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md); ordering: [docs/ORDERING.md](docs/ORDERING.md). R5 uses R4's circuit on a new board, with four additional local bypass capacitors from the reopened review: generated from the R4 board by `m3_design/r5_build.sh` (`r5_pcb.py`, `r5_routes.py`, `r5_maze.py`, `r5_route.py` with the Freerouting session in git, `r5_finish.py`, `r5_post.py`, then `r5_repair.py` and the verified metadata fill). **236 footprint positions / 209 fitted parts / 24 test pads / 3 tooling holes**.

What changed (details and reasons in M3_R5 §1):
- **Board:** 46 × 100 mm (R4: 46 × 193 mm), parts on both sides: top 93 (84 SMD, 9 through-hole) and 2 test pads; bottom 116 SMD parts and 22 test pads. Five M3 holes (the corners and mid-span at (4, 46)); two Ø3.2 tie holes for J122's plug tie.
- **Floorplan:** power entry at the aft edge, the MCU behind it, USB-C, the servo header and SWD in the middle, the pyro block (R4's, moved as one rigid group) at the forward end; the IMU and barometer on the bottom (the IMU's Y and Z axes flip: roll is +gyro_Y, the opposite sign to R4).
- **Routing:** critical nets scripted on a grid router (0/45/90°); the rest by Freerouting v2.4.1, then the grid router for what it leaves.
- **Requirements changed:** P1 (length and position in the bay), P2 (sled: five standoffs, the corners and mid-span, plate clear of the bottom parts), F4 (DC solve), M3 (two-sided fixed fees).

Verification, stated separately:
- **CAD checks (done)**: `tools/check.sh`: DRC 0 (pyro spacing rules included), unconnected 0, schematic parity 0, ERC 0; audit OK; no silkscreen outside the outline. `m3_design/check_actuators.py`: OK. `tools/fit_check.py`: OK (worst margin 0.11 mm, C84 on the top; deepest bottom part L1 at 4.62 mm, bottom margin ≥ 2.34 mm). `tools/export_fab.py`: 84 BOM lines, 209 placed, nothing missing; 200 supplier-pad reconstructions plus nine placement-only checks pass. Independent fabrication review verifies 150 source inputs and five outputs; all 14 archive members match a native re-export ignoring timestamps. Replay, manufacturing and quality suites pass 13, 17 and 19 tests respectively; repeated metadata fill changes zero fields.
- **Historical evaluation before the reopened review (CAD, datasheets):** two passes of six independent reviews (pyro, power, signal integrity, DFM, fit, silkscreen) against REQUIREMENTS.md. Pass 1: no Critical, nine Majors, fixed or recorded (M3_R5 §1b). Pass 2, on the re-routed board: no Critical, three Majors, all fixed: a via in J9.3's through-hole pad, the IMU's roll sign in the record (it is +gyro_Y), and bottom-side designators beside other parts (M3_R5 §1c). Pass 3 (one reviewer) confirmed the three fixes and found no new Critical or Major. A robustness round then kept live copper 1 mm from the bare gate test pads and re-routed (M3_R5 §1d); pass 4 (six reviewers from first principles, on robustness) found no Critical and two Majors, fixed: an overlap-only PULLPIN joint and corner-only mounting (a fifth, mid-span hole) (M3_R5 §1e). Pass 5 (two reviewers) confirmed both fixes; no open Critical or Major. Robustness round 2 (M3_R5 §1f): 0.3 mm GND-pour clearance at the RAW_ACT pins, thermal spokes on 77 small GND pads (pass 6 found the first version filled with no gap; fixed, and pass 7 confirmed it with no open Critical or Major), a fixed reflow order; the bring-up gate before flight is listed in M3_R5 §5. The pyro block is R4's to the micrometre (41 footprints, the same .kicad_dru, the same solder-bridge spacings); its DRC rules were shown live on the new copper.
- **Calculation:** servo feed DC solve (Q121 → J122, 0.05 mm grid) 4.82 mΩ, 37.1 mV and 0.29 W at 7.7 A, all of it on the In2 RAW_ACT strip at mid-path (R4: 5.05 mΩ, 0.30 W); the reverse hot-plug model is R4's (same circuit).
- **Cost and stock (2026-10-12)**: Standard PCBA: $55.26 parts (rounded) plus 81 codes × $1.53 feeder fee / 5 gives $80.05 per board from unrounded prices (target ≤ $84.41); 47 unique extended codes (target ≤ 48). **Two-sided fixed fees $83.96 per order** (setup, stencil, fixture; one side: $50.19; JLC may add a $14.93 handling fee). No shortage; U4 is thin (5 in stock for 5 boards).
- **Simulation**: no new SPICE run; the local bypass additions were checked in CAD and against manufacturer guidance.
- **Firmware**: none for R5; the board binding in `m3_firmware/build.py` must be redone (M3_R5 §3: IMU axes).
- **Physical tests**: none. The sled fit is not physically verified.

Open owner decisions: as R4 (below), plus the sled design (REQUIREMENTS P2).

Remaining qualifications and engineering exceptions (current geometry; see R5_VALIDATION.md and M3_R5 §2):

- **Flash supply and timing:** C29 (100 nF) is 5.872 mm from U3 VCC; C9 bulk is 3.11 mm away. This is an unqualified supply-noise/timing compromise. The previous “slow or current-limited” justification does not apply to the flash. Check supply droop and read/write integrity at the intended clock under buck, servo and camera load.
- **Power return and temperature:** C150/C151's nearest GND vias are 4.333/3.094 mm away; C121's is 1.179 mm. The camera's 78.33 mm × 0.4 mm supply trunk is about 0.096 Ω (0.12 V drop, 0.15 W at 1.24 A), with temperature unmeasured. U9 and camera-feed single vias, both RAW_ACT necks at J3 and the servo-feed column still require load/thermal and transient qualification.
- **Return paths and harness noise:** IMU_INT1's two transitions have GND vias 1.812/1.518 mm away; other inherited return-path exceptions and long cable-side servo traces remain subject to EMC, sensor-noise and armed dummy-load tests. Low repetition rate does not establish immunity to fast edges or harness transients.
- **Pyro and mechanical exceptions:** MCU-side pyro vias near bottom parts are tented, not exposed solder-bridge sites; they remain an exception to L10's 1 mm engineering placement target. Mandatory pyro/J2 coating, retention and armed dummy-load gates remain. Use nylon hardware at all five supports and a non-conductive sled clear of bottom parts, pin tails and the J122 tie. Physical sled/harness fit, vibration/shock and thermal tests are unperformed.
- **Panelization:** ORDERING now specifies exact 5 mm tab windows in KiCad coordinates at X = 0, Y = 45–50, 71–76 and 78.5–83.5 mm, and X = 46, Y = 43.75–48.75 mm. Independent geometry review passes against all 236 pad/courtyard envelopes. The production panel must reproduce these positions, keep mouse-bite hole edges at least 0.50 mm from all-layer copper and place Ø0.60 mm perforation centers at least 0.30 mm outside the finished board in sacrificial tabs; on-edge centers are not allowed. Supplier rail/support review remains required.
- **Assembly and firmware:** preserve sensor paste/mask apertures and the required reflow sequence; confirm MS5611's two reflows. R5 firmware binding, IMU-axis checks, supply/USB/reverse-hot-plug tests and all REQUIREMENTS/ORDERING physical gates remain open.

The final annotation pass fixes J1's reference and switch-pair label, hides obscured U1/U3/J3 references and leaves 83 references represented on the fabrication layers/assembly drawing. Earlier defect claims for R32, R81, TP122 and J1 BAT+/GND were not supported by final geometry. Eight redundant route segments were removed and one trimmed; the USB_DM fold is needed for its layer change and was not shown to be a stub. SERVO4's hand-solder clearance is repaired to 0.3125 mm at all four RAW_ACT pads.

## Previous candidate: M3-ASSY-R4 (R3 validation fixes, new IMU, thirteen evaluation passes)

Design record: [docs/M3_R4.md](docs/M3_R4.md); requirements: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md); R3 findings: [docs/R3_VALIDATION.md](docs/R3_VALIDATION.md); ordering: [docs/ORDERING.md](docs/ORDERING.md). R4 is generated from the R3 files by `m3_design/r4_build.sh` (`r4_lib.py`, `r4_sch.py`, `r4_pcb.py`). **232 footprint positions / 205 fitted parts / 24 test pads / 3 tooling holes**, 14 schematic sheets.

What changed (details and reasons in M3_R4 §1–1m):
- **IMU:** U4 is the ST LSM6DSV320X (adds a ±32–320 g channel; flight 2 reaches ~37 g).
- **Input protection:** D8 SMBJ12CA (a wrong 3S pack no longer destroys it); 470 kΩ on each side of the external contact; UVLO lowered to 4.45–4.61 V; C87 switch-bounce ride-through; OVLO release above a full pack; 2 × 10 µF at the input plus an RC damper (2 × 22 µF + 0.33 Ω) and a 10 kΩ input bleed, so a reverse hot-plug stays inside U9's input limits even soon after an unplug (modelled with measured DC-bias curves); USB OV trip raised to 5.66–6.37 V.
- **Pyro safety:** black ARM and orange igniter 2-position terminals with top labels; TP122/TP123 on the bottom; nine pyro spacing rules in DRC (RAW_ACT ≥ 1.0 mm from the buses and ≥ 0.5 mm from every pyro control net; bus/igniter/drain ≥ 0.5 mm from gates, other live nets and GND, ≥ 0.3 mm from sense nets; gate nets ≥ 0.3 mm from other live nets inside the pyro block; exposed live pads ≥ 1.0 mm from sense and gate pads, against one solder bridge); soft-termination drain capacitors; every sense divider's top split into two 5.1 kΩ in series (pass 11) and its bottom into two 2 kΩ in parallel (pass 12), so one shorted or open resistor leaves its MCU pin at ≤ 1.4 V and an igniter at ≤ 1.4 mA, plus a 4.7 kΩ series resistor at each ADC pin (R168–R172, passes 9–10) as a second layer; mandatory local coating of the pyro block and J2.
- **Servo feed:** one continuous In2 RAW_ACT pour under the F.Cu ring (47 stitching vias).
- **Debug header:** J2.6 unconnected; BOOT0 ends at its pull-down (pass 9: the run under J2's base passed 0.18–0.19 mm from 3V3 and NRST).
- **Sensors:** full-body copper/via keep-outs under the IMU and MS5611; direct decoupling; RC (not LC) 3V3A filter; MS5611 paste on TE's land size.
- **Fit and assembly:** JST PH pull-pin header; JLC placement corrections incl. the DB128V terminals' 180° body correction; USB-C legs pin-in-paste plus hand finishing; AON6403 windowpane paste; R166 on UNI-ROYAL's land; printable silkscreen marks kept inside the outline (gate check); order-number placeholder; JLC tooling holes; ENIG stackup in the job file; ORDERING pins green mask, plugged vias, single-board delivery, the paste layer as supplied and no washing; the order is Standard PCBA (240 ± 5 °C reflow, tab-routed edge rails) because U5, LS120 and C84 allow only a 250 °C peak, below Economic's 255 ± 5 °C.
- **Stock and cost:** U8 → AP63301WU-7 (the AP63300 had 5 in stock); Basic parts for the 100 nF and 10 k lines that carried minimum-purchase or 0.1 % premiums.

Verification, stated separately:
- **CAD checks (done)**:
  - `tools/check.sh`: DRC 0 (including the pyro spacing rules), unconnected 0, schematic parity 0, ERC 0; audit OK; no silkscreen outside the outline.
  - `m3_design/check_actuators.py`: OK; it pins the safety parts by LCSC code and checks every spacing rule's content; 78 seeded faults each make it or DRC fail (passes 9–12 added the load-switch nets, the sense series resistors and the split dividers; the final iteration rule H).
  - `tools/export_fab.py`: 84 lines, 205 placed, nothing missing, every placement rotation verified; an assembly drawing from the fab layers (every designator, hidden ones included).
- **Independent evaluation (CAD, datasheets):** pass 1 by six reviewers, passes 2 and 3 by five each, pass 4 by two focused reviewers (input protection; DFM, assembly and fit), pass 5 by five reviewers from first principles, pass 6 by two focused reviewers, passes 7 and 8 by one each, pass 9 by five reviewers from first principles, pass 10 by one focused reviewer, against REQUIREMENTS.md. Pass 10 found no Critical or Major issue; it added R172 on PB0 (for the arming option where the board powers up armed), corrected what the record claimed about the pins in a resistor-short fault, and tidied four designators (M3_R4 §1k). Pass 11 then closed the one gap pass 10 had kept: every sense divider's top is now two resistors in series, so no single shorted resistor drives an MCU pin past its ratings (M3_R4 §1l). Pass 12 (one focused reviewer) found no Critical or Major issue; its fixes make the divider bottoms two parallel resistors (so an open is tolerated too), widen the ARM stack's facing bus/sense pad gaps to 0.94 mm, un-shadow pyro rule B, and hide twelve designators that had no unambiguous spot (M3_R4 §1m). Pass 13 (one focused reviewer) found no Critical or Major issue; it measured four more single-solder-bridge paths past a divider (0.65–0.82 mm), seven neighbouring designators that missed the label rule, and document nits (M3_R4 §1n). A final CAD iteration fixed them: the ARM stack became two vertical columns, five parts moved, and DRC rule H now keeps every exposed live pad 1.0 mm from every sense and gate pad (M3_R4 §1o). Pass 14 (one focused reviewer) found no Critical or Major issue in that iteration; its findings were fixed in it: R143 moved clear of the actuator switch's gate pad and rule H covers that gate, the label rule measures to pad edges, the assembly drawing shows every designator, and the record no longer claims rule H covers 3V3 next to a gate (the cold test shows that case). Pass 9's Major (a single shorted 0402 divider resistor put armed drain or bus copper on an MCU analog pin, with the igniter in the drain-side path) is fixed on the board with R168–R171, and BOOT0 no longer runs to J2; its other findings are procedure, checker and document fixes (M3_R4 §1j). Pass 8 found no board or tool defect; its bench-procedure findings (safe probing of the armed pyro gates) are fixed in ORDERING §5 (M3_R4 §1i). Pass 7's Major (a pyro bench gate that a healthy board could not pass) is fixed in ORDERING §5 (M3_R4 §1h). Pass 6's Majors (owner-fitting the barometer against TE's no-hand-soldering rule, now Standard PCBA instead; no armed-not-firing gate; the remote-plug fuse location; F6's claim about FMEA F-1) are fixed (M3_R4 §1g). Pass 5's Majors (JLC's reflow above two parts' limits; the control window and the watchdog rule contradicting the project and the FMEA; a TIM15 instruction in the record that could fire a channel) are fixed (M3_R4 §1f). Pass 4's Major (a reversed pack plugged in while the input still held charge) is fixed with the input bleed; pass 3's board Major (reverse hot-plug margin) is fixed; its other two Majors are the open owner decisions below. Pass 1's Majors (3S TVS, J1/J9 entry direction) and pass 2's (ARM/igniter terminals interchangeable; coating made optional against the margin prescription; post-brownout behaviour unspecified; U8 stock) are fixed or recorded; the Minor findings are fixed or recorded as deviations (M3_R4 §1b–1f, §2).
- **Calculation:** servo feed DC solve 5.05 mΩ / 0.30 W at 7.7 A; reverse hot-plug harness model with Samsung's measured DC-bias curves (0.1–2 µH, ≥ 0.03 Ω): U9 IN ≥ −14.6 V and ≤ 9.2 V/µs at every corner from the ≤ 2.0 V the bleed leaves within 0.73 s of an unplug with the switch open, about 1.3 s with it closed (pass 9; hence the 2 s rule) (≥ −13.0 V from an empty input up to 1 µH).
- **Cost and stock (2026-10-09)**: Standard PCBA: $55.22 parts + 81 codes × $1.53 feeder fee / 5 = $80.00 per board (R3: $84.41 at Economic's fees); Standard's fixed fees $50.19 per order (setup, stencil, fixture; JLC may add a $14.93 handling fee; Economic: $9.71); no shortages, no line under twice its order.
- **Simulation**: no SPICE (ngspice not installed).
- **Firmware**: none for R4; the board binding in `m3_firmware/build.py` must be redone (firmware consequences: M3_R4 §3).
- **Physical tests**: none.

Open owner decisions:
- ARM link physical form and reachability (FMEA H-6, V-18): how the links go in on the pad (REQUIREMENTS F8). The link fuses cannot sit at the terminals inside the coupler (ORDERING §7).
- Flight 2's servos: stall current within F4's 1.92 A per servo, and hinge moments above M1.2 (the CFD sweep stops there).
- External switch part.
- Servo-fault containment (recorded as an accepted risk; per-servo inline fuses recommended for flight 2).
- The control window's exact start and stop points (a flight parameter; the board supports any window, and F7 requires the servos at neutral ≥ 200 ms before any fire). Tab-to-neutral within 50 ms of a hang is allocated to firmware in REQUIREMENTS F6 (IWDG ≤ 32 ms fed only by the 100 Hz safety task, bounded roll-interrupt run time, neutral first after reset; about 48 ms with NRST release); the board supports it as built.
- The camera model (it must not back-feed its 5 V input).

## Previous candidate: M3-ASSY-R3 (GNSS removed, 46 × 193 mm, cost-down)

Design record: [docs/M3_R3.md](docs/M3_R3.md). R3 is R2 with the GNSS (U6, C33, C34, GPS nets, its 3V3A branch) removed and the board cut from 238 to **193 mm** so it fits the main-section electronics bay. The forward M3 pair moved to y = 189. **No remaining track, via or footprint moved** (checked against R2 by UUID and geometry). **205 footprint positions / 180 fitted parts / 25 test pads**, 14 schematic sheets. The 1 k 1 % resistors moved to a JLC Basic part.

Verification, stated separately:
- **CAD checks (done)**:
  - `tools/check.sh`: DRC 0, unconnected 0, schematic parity 0, ERC 0; audit OK.
  - `m3_design/check_actuators.py`: OK.
  - `quality_audit` unit tests: 12/12.
  - `tools/export_fab.py`: 75 lines, 180 placed, nothing missing.
  - Pre-fab pin-mux audit against DS12110 Rev 11: no wrong assignment (`docs/M3_R3.md` §6).
- **Cost and stock (2026-10-05)**:
  - Parts: $54.94 per board at 5 boards, 48 unique extended codes; all-in about $100–110 per board.
  - The $75 target is not reachable without giving up robustness (`docs/M3_R3.md` §4).
  - **U4 ICM-45686 is out of stock at JLC**; it needs Global Sourcing or consignment.
- **Simulation**: not re-run (ngspice not installed). The actuator band is unchanged.
- **Firmware**: none for R3 yet (plan in `docs/superpowers/plans/`).
- **Physical tests**: none.

Open owner decisions:
- PB0 4.0 V FT_a limit (R125 → 3.3 k option).
- PE4/PE5 trace-pin risk, accepted procedurally.
- `PYRO*_GATE_N` naming.
- Cost relaxations.
- U4 sourcing.

## Previous candidate: M3-ASSY-R2 (actuator merge)

Design record: [docs/M3_ACTUATOR_MERGE.md](docs/M3_ACTUATOR_MERGE.md). One 46 × **238** mm four-layer board: R1 plus a 52 mm actuator band inserted between the battery/logic-power block and the camera block. **208 footprint positions / 183 fitted parts / 25 test pads**, 14 schematic sheets.

Added in R2 (all from the frozen M1 design as corrected by `MARGIN_PRESCRIPTION.md`, `FMEA_REDUNDANCY.md` and `CIRCUIT_REVIEW.md`):
- **Actuator power switch**: back-to-back AON6403 load switch from the battery input, gated by the logic path so the single external switch still controls everything; 470 µF bulk; RAW_ACT sense/bleed.
- **Dual pyro, single-deploy redundancy (owner ruling 2026-09-25)**: two AON7524 low-side channels on **two independently fused buses** (FMEA H-5); 4-position ARM terminal (two-fuse plug) and a separate 4-position igniter terminal on opposite long edges; per-bus arm sense, per-channel continuity, cold pull-up for plug-out FET-short detection (H-1), gate networks per P0-1/P0-2, PE3/PE6 sentinels.
- **Four servos**: 3×4 header on the centreline, 1.0 k series (P0-5), 10 k pull-downs, SRV05-4 clamp, zip-tie holes.
- **Pull-pin** (BAT54S-clamped, PC14) and **buzzer** (MLT-8530 on PA5; the §3.4 pad-pairing question is closed from the maker's specification).
- **Backup altimeter: fully isolated by ruling** — no interface on this board.
- Manufacturing package: `tools/export_fab.py` → Gerber/drill zip, JLC BOM and CPL in `m3_design/assembly_review/fab/`.

Verification, stated separately:
- **CAD checks (done)**: `tools/check.sh` = DRC 0 / unconnected 0 / schematic parity 0 / ERC 0, metadata and 3D-model audit OK; `quality_audit/verify_board.py` (refilled zones) PASS; `m3_design/check_actuators.py` (arming break, gate networks, sentinels, servo chain, buzzer/pull-pin mapping read from the PCB copper netlist) OK, with negative tests that break the ARM break and a sentinel.
- **Software tests**: `quality_audit` unit tests pass; **no R2 firmware exists** and v0.8.1 must not run on R2 (see `m3_firmware/README.md`).
- **Simulation**: ngspice suite for the R2 actuator band in `m3_design/sim_r2/` (`FINDINGS.md`): every case for the current design passes (switch, fire, fired-into-short, plug insertion, sense states, chafe). The shorted-igniter brown-out found in the merged R2 is fixed by R134/R135 (`docs/M3_ACTUATOR_MERGE.md` §2.6).
- **Physical tests**: none. No board has been built.

What changed in R1 copper, for reviewers: everything below y = 34 mm moved +52 mm unchanged; seven tracks that crossed the cut continue as straight B.Cu lanes; LED_RED was re-routed to PE8; the CAM_PWR_EN and CAM_FAULT_N routes under U1's top-left corner were re-routed to free the servo/continuity escape; U12 gained its missing LCSC code (C5186957).

Still open before a fab order (details in the design record §4): real-board power-up and fire tests into dummy loads, servo stall current vs. the 2.6 mm feed neck (≈ 7.7 A all-stalled is an inference, not measured), the in-line 15 A battery fuse and 5 A fast plug fuses as vehicle hardware, JLC rotation/THT review of the CPL, R84/R86/R9 sourcing, sled/enclosure fit of the 238 mm board.

## Previous candidate: M3-ASSY-R1

[Assembly and footprint review](m3_design/assembly_review/ASSEMBLY_REVIEW.md), [v0.8.1 bench diagnostics](m3_firmware/ASSEMBLY_DIAGNOSTICS.md). One 46 × 186 mm four-layer board, 135 footprint positions / 115 nominally fitted parts / 20 test points. The two LEDs have separate lands, cathode silkscreen and 3D orientation corrected against each manufacturer's drawing; U3's 208 mil package choice was confirmed. All 2201 existing tracks/vias were kept; native DRC, unconnected items, schematic parity and ERC are all zero. Functionally it provides ordinary power, acquisition, ~1 Hz diagnostic logging, USB, GNSS and the camera interface; **it is not a finished product with every rocket function, and there is no real-board or manufacturing-release evidence**.

M3-PDIAG-R1 and firmware v0.8 remain as the previous baseline; their input FAULT/ST signals and history carry over. The new firmware binds to the exact ASSY-R1 board, and the host tools reject a mismatched board ID or build identity. Active attitude control, servo/pyro actuation and a complete recovery backup are **not** implemented in this revision and must not be counted as delivered.

The host side has a [unified triage entry point and test-point map](diagnostics/TRIAGE.md): the network and location of the 20 test pads and 10 auxiliary test points are cross-checked against native KiCad data; failed or partial USB captures still produce a report linking faults to a branch and the next test point. The independent-instrument template starts empty, so power, device and whole-board stability have **no** physical PASS from it.

## Evolution record (not in the repository)

| Candidate | What it added | Evidence at the time |
|---|---|---|
| PWR-R3 | Battery / USB logic supply, acquisition core and camera branch on a provisional 46 × 168 mm board; 121 positions, 17 test pads, U6 GNSS not fitted, 103 fitted parts, 8 schematic sheets | 91 software/CAD regression tests and 5 passive hold-up simulations bound to that revision; no board measurements |
| UART-R1 | Camera UART transmit/receive, a separate camera logic supply, a reset-default-off enable and two test points; 133 positions, 113 fitted, 9 sheets | DRC/ERC/parity zero; 10 wrong-wiring / version-identity tests passed |
| USB-R1 | Corrected the ordinary-GPIO USB cable-detect divider, added R110 and TP92; 135 positions, 114 fitted, 10 sheets | 16 USB negative / numeric tests passed; 3 passive RC simulations matched the analytic results, one deliberately showing detection fails under strong back-feed |
| GNSS-R1 | U6 changed from DNP to fitted; corrected the receiver-area ground plane, distance to flash layer changes, stencil and 3D envelope | 238 software regression tests and 10 CAD error-input checks passed |
| PDIAG-R1 | Battery, USB and camera FAULT inputs and the source-select ST signal with current/historical evidence | Firmware v0.8 |

Firmware history: v0.2 bench acquisition (ADC3 voltages, MS5611, HSE / IMU / flash identity, SWD readback of 2–30 records to JSON/JSONL); v0.3 camera UART query; v0.4 raw IMU observations; v0.5 on-board diagnostic log with single/quad-line write verification; v0.6 USB CDC (pinned TinyUSB 0.21.0, HSE/PLL3 48 MHz USB clock, PD15 software VBUS detect); v0.7 GNSS receive / 1024-byte log / USB export; v0.8 power status; v0.8.1 binding to ASSY-R1. All are compiled and software-tested only; **none has run on a real board**. Older firmware images cannot be used as compatibility evidence for a newer board.

## Requirement status

> Historical table (R1–R2 era), kept for its evidence trail. The current requirements and their verification are in [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) and the R5 and R4 records above; where a row below still says GNSS, 46 × 186 mm or an LC filter, R3/R4 superseded it.

| Requirement | Current evidence / implementation | Still needed for the complete M3 |
|---|---|---|
| Merge the two boards into one | M3-ASSY-R1 is a single-board candidate for power + core + camera supply/UART + USB + GNSS; 10 schematic sheets consistent with the PCB | Other interfaces not all merged; this does not equal all functions of the old two boards |
| Fits the bay (Ø54.6 mm bore, Ø50.8 mm inside the coupler), installable / maintainable | R5: 46 × 100 mm with parts on both sides, top face on the bore axis (REQUIREMENTS P1/P2; R3/R4: 46 × 193 mm). Historical: core baseline 46 × 96 mm; candidate provisionally 46 × 186 mm; height envelope for the 14.5 mm terminals / 12.8 mm C84 capacitor | All connectors, plugs, harnesses, fasteners, sled, clearances and a physical coupon; final length not frozen |
| 2S supply, switch, reverse protection, logic hold-up | PWR-R3 added U9 battery protection, U10 USB current limit, U11 source selection and 330 µF hold-up; contacts are low-current enables | Start-up / switchover / back-feed / thermal / USB current and coordination with external protection must be measured; the 100 µs typical switchover time is not a maximum |
| Stable sensor supply | Core has the AP63203, L2 and sensor supply | Start-up, input capacitance / USB load, LC damping, tolerance / bias and measurements |
| STM32H743, USB, SWD, crystal | CORE schematic/PCB reconciled, DRC/ERC zero | Real power-up, clocks, buses, and running without a probe |
| USB connection and download | USB-R1 hardware; v0.6 implements the 48 MHz PLL3, CDC stack, descriptors, GPIO plug detection, snapshot / log download and identity checks; software fault tests pass | Real clock accuracy, enumeration / suspend / cross-platform behaviour, throughput, power / back-feed / inrush and signal integrity; development VID/PID and current compliance unresolved |
| IMU / barometer recording | Core circuit; pressure/temperature acquisition; v0.4 adds raw IMU samples with timestamps / configuration / error diagnostics | Continuous storage chain, real interrupt line, built-in self-test, real liveness / noise / accuracy; scripted software tests do not replace measurements |
| QSPI logging and export | Diagnostic append at up to 1 Hz with single/quad-line write-back verification; v0.7 records the full 1024 bytes including GNSS/USB; recovers older prefixes; software fault tests | Real quad-line operation, throughput / capacity, power-loss consistency, real USB download; model tests are not board passes |
| GNSS | U6 fitted in the candidate; 9600 baud USART6 receive, read-only identity / PVT queries, raw bytes / errors / freshness diagnostics, full log and USB export; software tests pass | Real UART / power / cold and warm start, antenna / enclosure / structure / accuracy; currently ~1 Hz bench observation, not a mission validation |
| Camera 4-position terminal, 5 V / GND / UART × 2 | UART hardware routed; v0.3 implements one device-information query with raw bytes / CRC / timeout diagnostics, off by default | Camera logic levels, power-down isolation, real protocol communication, recording and the full camera application still to be verified; the old v0.2 does not drive this UART |
| Servos and actuation interface | R2: four channels routed (3×4 header, 1 k series, pull-downs, SRV05-4), actuator rail switched with the logic path | Stall-current / thermal check of the header feed, servo firmware (TIM5, quiet-before-fire), real-servo test |
| Recovery backup and physical interlocks | R2: single deploy with two independently fused on-board channels; commercial backup altimeter kept **fully isolated** (ruling 2026-09-25); ARM plug is a complete break of both buses (PCB-netlist check) | Recovery firmware, ARM-plug hardware (two 5 A fast fuses, locking connector), ground ejection tests; the backup altimeter's own installation |
| Pull-pin, buzzer / indicators, spare interfaces | R2: clamped pull-pin (PC14) and driven buzzer (PA5) routed; LED_RED moved to PE8 | Firmware, audibility inside the closed airframe, pull-pin harness |
| Automated diagnosis and fault localisation | SWD register readback, voltage / pressure acquisition, camera UART and raw IMU bytes / errors; sequence numbers / bound hashes and JSONL evidence; v0.8 input FAULT/ST sampling and history | Real-board probing, instrument capture and a fixture still to be done; no real measurements |
| Trustworthy footprints / 3D | R2: all 99 BOM lines / 205 positions checked against manufacturer datasheets (pinout, land pattern, polarity, part number, 3D orientation); every issue found was fixed (`docs/R2_VERIFICATION.md` §3) | Physical fit of harness, plugs and sled; envelopes are not physical proof |
| Clean manual layout and routing | CORE and camera copper kept; new power paths and fine-pitch escapes hand-routed, support nets searched with constraints then straightened; native checks pass | Remaining critical nets and return paths on the full board; the old M2 is not final |
| Simulation and reliability study | The power candidate has 5 ngspice passive hold-up cases bound to the PCB hash, cross-checked analytically | No complete regulator / current-limit / thermal model or measured correlation yet; RC simulation does not prove whole-board stability |
| ≤ 3 iterations, replaceable / decoupled | Traceable engineering revisions, a diagnostic evidence framework; legacy coupon files | Quantified exit criteria before each fab, reworkable design, assembly strategy and revisions after measurement |
| Manufacturing package and cost | R2: BOM / CPL / Gerbers from `tools/export_fab.py`; every line has an LCSC code and JLC stock for 5 boards except U6 (consign, DigiKey); CPL orientation corrected per LCSC footprint; how to order: `docs/ORDERING.md` | Quote for the shipping destination; nothing ordered; bench-prototype only |

Items from the original requirements (ADXL375, microSD, LoRa, board width / copper weight, etc.) have been through several rounds of trade-offs. This table does not silently restore old configurations, nor silently drop unimplemented items; they must be closed with the final functions and verification evidence of the unified version. The frozen two-board architecture has been superseded by the single-board requirement (see `docs/HISTORY.md`).

**Priority**: on the routed power / acquisition candidate, add continuous acquisition and on-board logging, USB, real camera communication, purchasing and mounting constraints and dynamic board evidence; keep listing every unimplemented requirement explicitly. Every acceptance must distinguish software tool tests, design-rule checks, simulation and physical tests.

**R2 additions**: five 22 µF capacitors changed to the real Murata 1210 package, C82 moved 0.5 mm; 10 references (precision resistors, inductors, etc.) bound to specific part numbers, with maker and supplier evidence kept in the package. Exact bias capacitance and total cost are still open.

**R3 additions**: 28 more references given part numbers; corrected C70's minimum capacitance, C70/C81 unified as 4.7 nF C0G; D9 set to B340A-13-F. Added wrong-value / wrong-part-number / wrong-wiring negative tests and resistor TCR corner estimates. No selection has real-board dynamic, cold, assembly or stock verification yet.


## R6 update — 2026-10-13

R6 native schematic and PCB implementation is in progress. Module choices: EBYTE E22-900T22D radio and HGLRC M100 Mini GPS. Pyro 2 removal, compact connectors/buzzer, dedicated reset-disabled port supply and edge-port placement are implemented. Schematic/PCB parity has reached zero. Independent review drove corrections to actuator power distribution and buck feedback layout.

Release gate remains pending: finish signal routing, eliminate all native DRC/unconnected findings and overlap-only joints, repeat independent review, regenerate fab/BOM/CPL and final cost evidence. Do not treat old fabrication artifacts as the completed R6 release. Current size is 46 × 100 mm; preliminary estimate $84.14/board and 48 extended codes. Retained IMU stock is unavailable. See the appended R6 implementation section in docs/M3_R6.md for pin contracts and qualification limits.


## R6 validation checkpoint — 2026-10-13 continuation

The current PCB remains a work in progress, not released for fabrication. Six connections remain open: GPS_TX_MCU, TLM_FAULT_N, SWCLK, RADIO_M1_MCU, IMU_INT1 and RADIO_AUX_MCU. The existing fab package predates this checkpoint and must be regenerated after final validation.

All 13 overlap-only joint findings were repaired (10 centerline bridges, 3 redundant stubs removed), preserving connected pad groups and existing reference coverage. The long IMU In1 routing experiment was rejected for a Major ground-return detour near the oscillator and MCU decoupling. Its helper now rejects normal application. SWCLK candidates also remain unapproved pending VCAP2/reference-island repair.

This checkpoint supersedes earlier port-enable pin assignments: TLM_PWR_EN is now PB12 / U1.51 through R192 1 kohm; PE1 / U1.98 is NC. TLM_FAULT_N remains PE0 / U1.97. The external R193 10 kohm pulldown keeps the supply disabled during reset. Firmware must use PB12 as the enable output and preload it low before configuring output mode. PB12 is a non-debug GPIO with analog reset state (ST DS12110 Rev 11, section 3.8 and Table 9: https://www.st.com/resource/en/datasheet/stm32h743vi.pdf). All radio/GPS UART and mode pin assignments remain as specified.

The synchronized PB12 schematic/PCB passed native ERC and schematic parity with zero findings, the actuator contract, and 13 R6 geometry regression tests. The routing change introduces no In1 signal tracks, no additional existing front-trace reference losses, and zero losses over 104241 critical reference samples. Numbered connector legends were regenerated, including J9 3:TX / 4:RX from the peripheral perspective; all 40 required labels fit. R6 CAD contract, silkscreen bounds and fit checks pass. Native connectivity still reports six opens and dangling copper; tools/check.sh is not yet zero.

Board size is 46 x 100 mm: below the 110 mm maximum, outside the 80–90 mm target. Procurement remains on hold for the previously identified unavailable U4; prior cost estimates require final BOM/fab revalidation. Final independent review could not resume because the review agents reported exhausted workspace credits. No final Critical/Major clearance or hardware qualification is claimed.

Evidence: m3_design/assembly_review/sources/r6_validation_iterations.json, r6_joint_integration.json, r6_enable_pb12_packet.json, r6_enable_pb12_migration.json, r6_silk_integration.json, r6_current_contract.json and r6_current_fit.json.

Update: the existing independent review agents resumed successfully after the credit error. Their renewed reviews are pending. Full tools/check.sh checkpoint reports 6 opens, 10 dangling vias and 5 dangling tracks; ERC and parity remain zero.


### 2026-10-13 SWCLK validation iteration

The reviewed SWCLK crossover is now integrated (PCB SHA256 3c2525af6720fb123a95393b0885d20c43defba78d9c2f1fee6bf054149777a9). Native candidate DRC reports five remaining unconnected items and zero hard violations. Independent review finds zero Critical or Major issues for this change. Its short back-layer crossover restores the original 5.697 mm transverse MCU ground path; reviewed HSE and C17/C20 ground returns remain unchanged. All 104,241 critical reference samples are preserved. One Minor finding remains for reduced direct reference under the USB fault monitor and an auxiliary stitching-path detour. R128 pad 2 uses a 22.5 degree thermal angle with existing gap, spoke width and minimum-spoke rules retained. The replay helper reproduces all added copper and is idempotent. Fault-input and IMU remapping candidates are still under review and are not part of this checkpoint. Full zero-error acceptance and regenerated fabrication release remain pending.


### R6 routing and pin assignment checkpoint — 2026-10-13

The reviewed PA7 port-fault route and radio M1 route are integrated. Port enable remains PB12 with the hardware reset-off pulldown. IMU INT1 moves from PE10 to PE1 as a plain polled input; PD1 retains EXTI1. PE3/PE6 and all channel-1 guard pins remain no-net sentinels, with PE3 driven low by the bench firmware. The schematic/netlist pin-map delta is exactly U1.40 and U1.98. Native ERC and schematic parity are zero; actuator and R6 contracts pass. The PE1 firmware change passes 42 host tests; no ARM binary was built because an ARM compiler is unavailable.

The current PCB has two remaining unrouted signals (GPS TX and radio AUX), 13 dangling-copper warnings and no other native DRC errors. Independent reviews found no Critical/Major defects in the adopted routes; minor auxiliary ground-return detours remain recorded. The board is 46 × 100 mm: within the 110 mm maximum but outside the preferred 80–90 mm length. This is an intermediate checkpoint, not fabrication release.

The legacy GNSS bench driver still assigns GPS to USART6. R6 hardware assigns GPS to USART1 PA9/PA10 and radio to USART6 PC6/PC7; firmware bring-up must migrate the GNSS driver and keep port outputs high impedance while port power is off. The existing bench firmware is not an R6 flight-firmware release.


### Fully routed R6 checkpoint — 2026-10-13

GPS TX and radio AUX are now connected. The saved PCB has zero unrouted connections, 13 existing dangling-copper warnings, and no other native DRC errors. The final AUX review found zero Critical/Major issues after restoring two MCU ground returns: a 1.273 mm, 0.25 mm wide In2 ground bridge between existing vias, and a local AUX/GPS-RX layer change that preserves the baseline ground passage. All 104,241 sampled critical-signal reference points remain supported. Minor auxiliary return detours are recorded in the independent review archive.

Fabrication release remains held for the newly identified U12 camera UART translator bypass issue: C100 is too far from VCCA and is being moved close to its supply pin. Final dangling-copper cleanup, combined review, all required checks and fabrication regeneration will follow that fix. The prior temporary candidate passed the complete automated gate but was rejected by the independent ground-return and decoupling reviews; it was not adopted.


## Final R6 CAD validation — 2026-10-13 PDT

This is the authoritative closeout checkpoint. PCB SHA-256: `184a87e84e67576341244c82517de3e9f55f5c1c22995dfad83631d48c856680`.

The requested R6 CAD changes are implemented and fully routed: channel 2 removed; J9 is GH4; LS120 is the smaller MLT-5020 (C94598); J2 is TC2030; radio and GPS use USART6 and USART1 respectively with 1 kΩ series resistance and ESD protection; AP63301/TPS2553 port power is reset-off. The port rail is 4.8 V nominal to respect the HGLRC M100 Mini 5 V maximum. PB12 enables power and PA7 reads fault. IMU status moved to PE1 as a polled input only; PD1 keeps EXTI1 and the pyro-adjacent PE3 sentinel remains output-low.

The final review/implementation loop closed the remote camera-translator VCCA bypass, ground-return barriers and incomplete connections. C100 is now beside U12 on B.Cu, with a 1.362 mm supply centerline and 1.503 mm direct ground centerline. Final cleanup removed 38 dangling copper items, repaired one overlap-only joint, and regenerated 40 required legends. No retained component geometry or clearance rules changed during cleanup.

`tools/check.sh` passed: DRC 0, unconnected 0, schematic parity 0, ERC 0; metadata/models, silkscreen, R6 contract, `check_actuators.py` and `fit_check.py` all passed. Independent routing review 27 and the objective review found Critical 0 / Major 0. All 104,241 critical-reference samples were preserved, with no old pad-group splits. Existing minor return-path tradeoffs remain in the review archive. Regression evidence: 18 fabrication, 15 procurement, 17 R6 geometry and 42 narrow firmware host tests passed.

Board size is **46 × 100 mm**: the 110 mm maximum passes, but the 80–90 mm target is not met. Five supports, including the mid-span support, pass the CAD envelope check. J9's mated envelope has only 0.03 mm residual margin after the modeled tolerance; confirm the real harness and airframe fit.

Fabrication outputs are regenerated in `m3_design/assembly_review/fab/`, with a matching source/output manifest. Gerber ZIP: 11 layers, PTH/NPTH drills and job file. All 222 CPL rows pass; 214 use independent supplier pad matching and 8 use placement-only validation. Top/bottom native renders and assembly PDFs were inspected.

The five-board Standard-PCBA cost check is **$84.14/board, 48 extended codes**. This is components plus feeder fees, not an all-in delivered-board price. Fixed two-sided assembly fees are $83.96/order; possible handling is $14.93/order; PCB fabrication, rails, joints and shipping are excluded. Supplier snapshot: 2026-10-13T19:17:09.804712+00:00. The smaller buzzer has stock 91,636. **Procurement remains on hold: U4 LSM6DSV320XTR / C26633007 has stock 0 for 5 required.** `check_procurement.py --cost-only` passes; the full procurement gate correctly fails on stock.

Power-copper calculations at 7.7 A, 35 µm copper, 20 µm via plating and 20 °C converged:

| Path | Resistance | Drop | Copper loss |
|---|---:|---:|---:|
| RAW_ACT | 3.96 mΩ | 30.5 mV | 0.235 W |
| BAT_IN | 3.91 mΩ | 30.1 mV | 0.232 W |
| ACT_FET_S | 1.36 mΩ | 10.5 mV | 0.081 W |

These calculations exclude component/contact resistance and do not establish thermal or flight qualification. GPS maximum current is unpublished; bench validation still covers combined radio/GPS startup and transmit load, supply overshoot, reset/off behavior, harness fit and ESD. Existing GNSS firmware still uses USART6 PC6/PC7 and must migrate to USART1 PA9/PA10 for R6; broader flight firmware was not qualified.

Pinouts (RX/TX at the module): J9 = 1:5V, 2:GND, 3:TX, 4:RX. J130 = 1:M0/PC8, 2:M1/PC9, 3:RX←PC6, 4:TX→PC7, 5:AUX/PA8, 6:port power, 7:GND. J131 = 1:port power, 2:GND, 3:TX→PA10, 4:RX←PA9. J2 TC2030 = 1:3V3 VTref, 2:SWDIO, 3:NRST, 4:SWCLK, 5:GND, 6:NC.

Evidence: `m3_design/assembly_review/sources/r6_final_validation.json `, `r6_final_checks/`, `r6_final_dc.json `, `r6_final_objectives_review.json ` and `r6-independent-routing-reference-review-20261013.json `. CAD validation is complete; manufacturing procurement and physical qualification are not complete.
