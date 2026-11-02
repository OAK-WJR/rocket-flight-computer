# R10 validation and adversarial review

**Where R10 stands.** M3-ASSY-R10 is a CAD candidate on branch `m3-assy-r10`. It is not accepted and nothing is ordered; R9 stays the accepted board and R8 its fallback.
The current PCB is `a0ec075e…`, made by the [round 26 fix pass](#round-26-fix-pass) (D-R26-01 … D-R26-04) from `92c3ad59…`, which the [round 24 fix pass](#round-24-fix-pass) (D-R24-18 … D-R24-23) made from `1407e850…`, which the [round 24 board pass](#round-24-board-pass) (D-R24-01 … D-R24-17) had made from `5516eeec…`. Rounds 22 and 23 were a clean closing pair on `5516eeec…`; that pair does not carry to later boards. Round 24 found 17 real errors on `1407e850…`, round 25 found 10 (none on the board) on `92c3ad59…`, and round 26 found 12 (one on the board) on `92c3ad59…`. Round 27 found 7 (none on the board) on `a0ec075e…`, round 28 found 9 (one Major, none on the board) on it, round 29 found 5 (one Major, none on the board) on it, and round 30 found 2 (Minor, text only, none on the board) on it; all four fix passes left the board unchanged. Rounds 31 and 32 review `a0ec075e…` under the owner's strict rule: only real errors count (false statements, broken links or anchors, wrong calculations, unusable procedures), and iteration stops after two consecutive rounds with zero verified real errors.
What the owner must accept or do is in the [owner decision table](#owner-decision-table). The full state (checks, cost and stock, retained deviations, what is not verified) is stated once, in
[M3_R10.md, "Current state"](M3_R10.md#current-state). This file is the review record: the rounds, the owner questions and the deviation list.

**Latest review.** Round 30's ten lenses reviewed PCB `a0ec075e…` at commit `0afaed3`: **0 Critical / 0 Major / 2 raw Minor findings** (safety 2; the other nine lenses 0), which the triage kept as **2 real errors** (both Minor, text only, none on the board: §1's ARM1_SENSE-to-CAM_IO_3V3 bridge figures left out the D120 / R131 cold pull-up, and round 29's "LS120 ≤ 70 °C" chamber-test pass clause could not pass), 107 observations not counted and none not reproducible (see [Round 30](#round-30-ten-lenses-on-committed-0afaed3)); the round 30 fix pass left the board unchanged, and rounds 31 and 32 are planned. Round 29's ten lenses reviewed PCB `a0ec075e…` at commit `09a564e`: **0 Critical / 1 Major / 4 raw Minor findings**, which the triage kept as **5 real errors** (one Major, an AGENTS §2.5 labelling violation: figures resting on inferred inputs still marked Calculation only or unlabelled, and four round 28 status lines claiming that every such figure was labelled; 4 Minor; none on the board), 139 observations and none not reproducible (see [Round 29](#round-29-ten-lenses-on-committed-09a564e)); the round 29 fix pass left the board unchanged, and round 30 reviewed the same board (above). Round 28's ten lenses reviewed PCB `a0ec075e…` at commit `19dd0b5`: **0 Critical / 0 Major / 8 raw Minor findings**, which the triage kept as **9 real errors** (one Major, promoted from a safety observation: firmware rule 3's gate-fight figures were stated without their Inference label, against AGENTS §2.5; 8 Minor; none on the board), 102 observations and none not reproducible (see [Round 28](#round-28-ten-lenses-on-committed-19dd0b5)); the round 28 fix pass left the board unchanged, and round 29 reviewed the same board (above). Round 27's ten lenses reviewed PCB `a0ec075e…` at commit `816038c`: **0 Critical / 0 Major / 7 raw Minor findings**, which the triage kept as **7 real errors** (all Minor, none on the board), 19 observation entries and none not reproducible (see [Round 27](#round-27-ten-lenses-on-committed-816038c)); the round 27 fix pass left the board unchanged, and round 28 reviewed the same board (above). Round 26's ten lenses reviewed PCB `92c3ad59…` at commit `3d8e845`: **0 Critical / 0 Major / 14 raw Minor findings**, which the triage reduced to **12 real errors** (all Minor, one needing a board change), 107 observations and none not reproducible (see [Round 26](#round-26-ten-lenses-on-committed-3d8e845)); the round 26 fix pass changed the board to `a0ec075e…`, which round 27 reviewed (above). Round 25's ten lenses reviewed PCB `92c3ad59…` at commit `c4bb56b`: **0 Critical / 0 Major / 14 raw Minor findings**, which the triage reduced to **10 real errors** (all Minor, none on the board), 72 observations and none not reproducible (see [Round 25](#round-25-ten-lenses-on-committed-c4bb56b)); the round 25 fix pass left the board unchanged. Round 24's ten lenses reviewed PCB `1407e850…` at commit `f2b8251`: **0 Critical / 0 Major / 24 raw Minor findings**, which a fresh triage verifier reduced to **17 real errors** (all Minor), 11 observations and none not reproducible (see [Round 24](#round-24-ten-lenses-on-committed-f2b8251)). The round 24 fix pass then changed the board to `92c3ad59…`, which round 25 reviewed (above). Round 23's ten lenses reviewed PCB `5516eeec…` at commit `c70d261`: **0 Critical / 0 Major / 55 Minor** (see [Round 23](#round-23-ten-lenses-on-committed-c70d261)). With round 22's 0 / 0 / 22 on the same board, rounds 22 and 23 are the closing pair: two consecutive clean reviews. Round 22's ten lenses reviewed PCB `5516eeec…` at commit `ec8cb98`: **0 Critical / 0 Major / 22 Minor**. The between-rounds pass that followed changed only checks, one schematic note and records; the board is still `5516eeec…`. See [Round 22](#round-22-ten-lenses-on-committed-ec8cb98). Round 21 reviewed PCB `0dc84776…` at commit `accfff4` with ten Claude lenses: **0 Critical / 0 Major / 35 Minor** (29 new, 6 carried).
See [Round 21](#round-21-ten-lenses-on-committed-accfff4). Round 20 (seven board lenses, `50a39de5…`) found 0 / 0 / 32 Minor; see [Round 20](#round-20-board-lenses-on-committed-6628488). Round 19 (ten lenses, `a3144b15…`) found 0 / 0 / 57 Minor; see [Round 19](#round-19-second-claude-review-of-committed-1e60441). Round 18 (the first Claude review, on `632a9ad3…`) found 0 / 0 / 68 raw Minor observations.
Rounds 16 and 17 (the reviewer family of rounds 1 to 15) were a clean pair on `632a9ad3…`; that pair does not carry to later boards.

**Current PCB.** `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`: 46 × 90 × 1.6 mm, 2,369,507 bytes; 216 footprints, 1059 segments, 309 vias (170 GND), 1866.794 mm of track;
123 visible and 93 hidden references, 44 legends; eight DB125 terminals with 27 contacts. The round 26 fix pass (D-R26-01 … D-R26-04) changed it from `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` (2,363,951 bytes; 1057 segments, 307 vias (168 GND), 1867.046187 mm; 124 visible / 92 hidden references) by adding two GND vias at J440 and moving C10, C11, R164, R173 and R164's 3V3 via with their copper (its first layout, the intermediate `4108e6fa…`, was never committed or reviewed). The round 24 fix pass (D-R24-18 … D-R24-23) had made `92c3ad59…` from `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e` (the same counts, 2,363,869 bytes, 1867.022756 mm) by capping BAT_FAULT_N's chamfer at (16.55,83.35) (D-R24-18). The round 24 board pass (D-R24-01 … D-R24-17) had made `1407e850…` from `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` (215 footprints, 983 segments, 300 vias (167 GND), 1871.611826 mm). The round 21 fix pass (D-R21-01 … D-R21-09) changed it from `0dc84776…`, which the round 20 polish pass (D-R20-01 … D-R20-11) made from `50a39de5…`, which the round 19 fix pass
(D-R19-01 … D-R19-15) had made from `a3144b15…`, including the spare AUX port J440, approved by the owner on 2026-10-30 (D-R19-14).

Evidence: [AVA layout hand-off](../m3_design/assembly_review/sources/r10_design/AVA_LAYOUT.md) and its metrics, validation and review-item JSON files.

**About older text.** Earlier status banners, which say "now" about superseded boards, are kept as written under [Historical banners](#historical-banners).
Historical round sections keep their original text, including numbers glued to words; only the current sections (this head, Rounds 19 to 21, the round 24 board pass and the deviation list) are respaced.

## Round 1 owner decisions (historical implementation state)

The owner resolved R1-01, R1-02 and R1-03 in plan §8, commit `40a1d28`.
O5 supplies the camera from an adjustable buck and both external UART ports from
an approximately 4.8 V LDO, with separate current-limited switches. Exact setpoints
and module-input corners remain implementation qualification, not owner questions.
O6 routes servo positive and negative power directly to the pack; J122 GND remains
a signal reference with a calculated, explicitly bounded residual current.

Round 1 Phase B is in progress. No passing R10 implementation has been committed.

## Round 1 artifact and review status (historical)

The R10 generators and scratch layout are under implementation, not qualified. Starting commit:
`f5579f4a9c248d4aa6cf7a2add162cb813a93c63`. The unchanged inherited R9 PCB is
46 × 102 mm, SHA-256
`4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14`.
Neither that board nor its accepted deviations are relabelled R10.

Round 1 reviews the plan, proposed circuit changes and an unfrozen 46 × 84 mm
floorplan concept: MCU near (23,42), functional connector groups at the edges,
power near the battery terminals and passives on the back. These coordinates are
not a placement result, fit claim or length commitment.

The session permits three concurrent reviewers besides the orchestrator. The
requested CLI fallback failed to initialize (`Operation not permitted`). Independent
reviewers therefore run in parallel batches with fresh contexts. Interrupted
reviewers were restarted; incomplete reviews do not count. This is not ten
simultaneously running reviewers. No qualifying clean-board review rounds have
occurred, and no implementation pass has been committed.

All ten independent review lenses completed. **Consolidated round-1 plan findings:
0 Critical, 7 Major, 9 Minor** after duplicate consolidation. R1-m01 and R1-m06
below are retained as traceability rows within Major findings, not extra Minor
counts. These totals do not describe a committed R10 board. The required last two
clean board-review totals are unavailable; the stop condition is not met.

| Lens | Reported Critical / Major / Minor | Consolidated disposition |
|---|---|---|
| 1 Requirements (restarted) | 0 / 4 / 3 | R1-01,03,04,05; m01,04,05 |
| 2 Safety | 0 / 2 / 1 | R1-03,04; external-radio immunity merged into R1-04 |
| 3 Power/electrical | 0 / 2 / 1 | R1-01,02; shedding transition merged into R1-05 |
| 4 Parts/BOM (restarted) | 0 / 0 / 1 | R1-m08; candidate sourcing in round1_parts.md |
| 5 MCU/signals (restarted) | 0 / 1 / 2 | R1-04; m06,07 |
| 6 Mechanics | 0 / 1 / 3 | R1-06; m01,02,03 |
| 7 Routing/AVA | 0 / 1 / 0 | R1-03; no routing claim without R10 copper |
| 8 Manufacturing | 0 / 0 / 2 | R1-m05,09 |
| 9 Gate adversary | 0 / 1 / 1 | R1-07; m10; root independently reproduced both seeds |
| 10 Documentation/firmware | 0 / 0 / 1 | R1-m11; M1/M3 portions merge into m05,09 |

## Confirmed plan findings and dispositions

The following are consolidated findings, not counts of independently discovered
duplicates. Major means unresolved qualification or a requirement conflict that
must close before the R10 implementation can pass. A missing implementation alone
is expected at this stage and is not counted as a defect.

| ID | Severity | Evidence and independent verification | Disposition / concrete fix |
|---|---|---|---|
| R1-01 | Major | O1 and plan §7 specify switched existing 3V3; HGLRC minimum 3.3 V versus AP63203 minimum 3.27 V. Root verified both maker sources. | Owner resolved through O5 (§8). Qualify the new LDO supply and per-port switches. |
| R1-02 | Major | The proposed shared fixed 5 V rail cannot guarantee both camera and radio input ranges. RunCam minimum 5 V; MicoAir LR900 4.5–5 V; AP63205 feedback 4.95–5.05 V before load-switch/harness losses. Root verified original sources. | Owner resolved the architecture through O5 (§8). Qualify separate module-input voltage budgets. D-R1-03 records the basis. |
| R1-03 | Major | O3/§7 removes positive servo copper but retains J122 GND and describes only positive injection. Root verified plan lines 103,117–120 and F4; ordinary three-wire plugs leave a possible PCB motor-return path. Safety and requirements reviewers independently found this. | Owner selected external positive and negative power through O6 (§8). Specify the pack-star signal-reference harness and bound residual PCB current; do not claim zero return current. |
| R1-04 | Major | Plan §§6–7 defines port switching without a complete reset/unpowered UART contract. MCU pins reset analog; switched supply alone does not establish isolation. Safety, signals and requirements reviews agree. Root verified the missing contract and the retained camera isolation requirement. Actual GPS/radio injection current is unmeasured: **Inference** only. | Hardware default-off enables; safe FAULT pull-ups; state table for reset, boot, off, active UART and independently powered endpoint. Qualify isolation or datasheet-backed sequencing; include new port-net exclusions and installed maximum-power radio immunity tests. |
| R1-05 | Major | F6 separately requires ≥150 ms switch-bounce immunity and short battery-lead-break ride-through. Plan shedding estimates lack a threshold, maximum latency and retained-load envelope. Root checked F6 and plan §§2,7; power and requirements reviewers agree. | Preserve bounce and watchdog/recovery obligations. Derive battery-break acceptance from actual rail topology, worst-case loads, capacitor tolerance/ESR, clock/flash states, switch turn-off and detection latency. Mark estimates conditional until qualified. |
| R1-06 | Major | Root inspected `tools/fit_check.py:253–264,386–396`: five-support contract and reference-specific mated envelopes. `tools/plate_model.py:34–40,108–110` retains R9 masses and omits mated-envelope masses. Simply removing RF/adding GH does not migrate these contracts. | Introduce explicit R10 mechanical profile, all body/mated/wire envelopes and appropriate masses; seeded absent-envelope/support tests. Retain P2's effective fifth support unless a measured alternative is accepted. Four corner holes do not forbid a fifth support. |
| R1-07 | Major | Gate reviewer and root independently seeded `exclude_from_bom exclude_from_pos_files` on each of R134, R127, R128 and C126 in memory. `check_actuators.check` returns no issues for baseline or any mutant. Root inspected `quality_audit/audit_artifacts.py:22–25,28–72`: excluded parts are considered unfitted; no required-population set. Exporter omits these parts. | Add explicit required-fitted safety-component checks across schematic, PCB and exported assembly lists, including omission/DNP seeds. Preserving topology checks alone does not preserve assembled safety. Whole-gate mutant survival has not been tested; do not claim it has. |

Electrical source details for R1-02:
[RunCam Split 4K manual](https://www.runcam.com/download/split4k/RC_Split_4k_Manual_EN.pdf), input specification;
[MicoAir LR900 manual](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry), specifications;
Diodes DS41326 p.5. With the candidate TPS2553's 135 mΩ maximum on-resistance,
the camera lower corner at 1 A is 4.815 V before wire loss. This calculation does
not qualify a final circuit. See [TI SLVS841F](https://www.ti.com/lit/ds/symlink/tps2553.pdf), p.7.

## Minor findings and implementation obligations

These remain open until implemented or explicitly accepted as deviations. No
unmeasured board geometry is asserted here.

| ID | Evidence | Required disposition |
|---|---|---|
| R1-m01 | Plan §7 permits four corner holes; P2 retains an effective fifth support. Mechanics reviewer reproduced the R9 model at 256.610 Hz with five supports and 128.720 Hz with four; these are R9 sensitivity calculations, **not R10 predictions**. | Retain the fifth support as the conservative default, update masses and solve R10; record sensor modal displacement/strain and bench vibration qualification. Merged with R1-06's gate migration. |
| R1-m02 | O1/O2 move modules into the vehicle but do not allocate their installed volume, harness, antenna or retention. Reviewer cites LR900-F 43.4 × 25.8 × 11 mm / 8 g excluding antenna and GPS 15 × 15 × 5.2 mm / 2.6 g. | Verify maker dimensions, allocate the installed envelopes and retention loads in the vehicle record; do not claim shorter PCB proves whole-bay fit. |
| R1-m03 | R9 terminal model review already records stacking-nub/body-clearance limits; new terminal family has different tails and wire/screw access. | Include complete maker geometry, tolerance and wire-entry envelope; measure actual J124 copper gap ≥1.5 mm and support the board during tightening. |
| R1-m04 | Plan §7 allows one 3.5 mm family; F8 and `check_actuators.py:486–493` require battery/pyro distinction. | Select a distinguishable battery body/colour with unambiguous polarity/role legends and preserve an automated distinction check. |
| R1-m05 | M3's $42 allowance is expressly for on-board RF. | Use the original $84.41 board-cost cap and ≤52 extended codes as the conservative target; report external modules/harness separately. A higher cap would need owner acceptance. |
| R1-m06 | New EN/FAULT GPIOs are not yet allocated. STM32 pins reset analog; TPS2553 FAULT reporting takes 5–10 ms. | Hardware EN bias and final reset/boot state table; select nonconflicting EXTI lines. Do not use delayed FAULT as immediate supply-drop detection. Merged with R1-04/R1-05. |
| R1-m07 | Root inspected `tools/critical_reference.py:25–28`; its explicit nets omit the new UARTs. | Include applicable new critical nets in reference-plane and routing profiles; seed a split crossing. A nearby GND via alone does not prove an uninterrupted reference. |
| R1-m08 | Plan's missing-C84-datasheet statement is stale; parts reviewer located the exact MA-series electrical row, independently opened by root. | Use the source and tolerance/endurance limits in `sources/r10_design/round1_parts.md`; verify assembled height and land. |
| R1-m09 | The located C84 sheet contains no reflow profile or allowed cycle count; M1's existing polymer exception names C121, which O3 removes. | Obtain maker assembly qualification or explicitly document C84's measured-qualification exception before release. Incompatibility is **not proven**. |
| R1-m10 | Root independently reproduced an in-memory J124 with 3.5 mm pitch / Ø2.3 mm pads: actual gap 1.2 mm, but `r9_pyro_check.gate_bridges` returns zero issues because `bridge_table` exempts same-part pairs. | Plan already demands ≥1.5 mm, so this is a migration hazard rather than a missing requirement: add a direct actual-pad/adjoining-copper gap check and a seeded undersized gap. Do not reuse the bridge check as proof. |
| R1-m11 | Plan §4 omits the operating-assumption migration; REQUIREMENTS still bases pack/pad endurance and board position on on-board RF and SMA/coax. `jlc_cost.py` also defaults to the RF-inclusive cap. | Recalculate installed-system load, pad endurance/reserve and bay allocation; update assumptions and explicit cost-gate limit. M1/M3 aspects merge into m05/m09. |

The existing radio immunity procedure's +22 dBm/on-board placement assumptions
must become an installed LR900 maximum-power/dummy-load test, including GPS
coexistence. Safety's original Minor and requirements' Major are consolidated into
R1-04's missing external-port qualification contract, not counted twice.

The power reviewer identified shedding-transition energy as a conditional
calculation gap; it is consolidated into R1-05 rather than counted separately.
No assumption that U11 prevents every reverse-discharge transient is accepted
without checking its threshold and the actual rail topology.

## Requirement coverage at the plan stage

| Requirement | Required implementation / remaining verification |
|---|---|
| O1 | Adopted external GPS; supply architecture resolved by O5; implementation budget pending |
| O2 | Adopted external UART radio; voltage, reset/off-state and installed RF qualification R1-02/04 |
| O3 | Adopted external servo positive power; return architecture resolved by O6; residual-current qualification R1-03; accepted power-switch loss must be listed |
| O4 | Adopted regulated camera supply; qualify input envelope R1-02 and retain U12/U13 |
| F1/F2 | Retain sensor ranges; derive final signed orientation/lever arm; flight-range and vibration qualification |
| F3 | Retain barometer, vent, foam/coating exclusions and transonic estimator behavior |
| F4 | Four protected PWM outputs; full harness/return-current qualification R1-03 |
| F5 | Preserve logging/sample-rate/memory policy through shedding and fault recovery |
| F6 | Separate bounce/battery-break criteria; watchdog, independent safety task, neutral-first PWM and live-evidence reset recovery retained; R1-05 |
| F7 | Retain complete fire path, 2 Ω limit and ≤20 ms cutoff; final copper/harness pulse budget, quiet-before-fire and assembly inclusion R1-07 |
| F8 | Complete ARM break and defined-off gates retained; default spacing authorized; divider single-fault safety and connector distinction requalified |
| F9 | Split battery/switch connector and new supplies: hot-plug, reverse/overvoltage, overload, pin ratings and backfeed requalified; pull-pin stays advisory |
| F10 | External-port net separation, no radio arming/firing commands, band setup and installed RF/GPS tests |
| P1 | 46 mm width; final length, all-height bore fit and external module/harness installation unmeasured |
| P2 | Effective fifth support/servo retention carried forward; new mated envelopes and vibration model R1-06 |
| P3 | Staking/coating retained; external-equipment retention allocated |
| M1 | Lands/models/metadata/orientation and assembly/paste qualification; C84 reflow gap m09 |
| M2 | Empty-allowlist R10 route profile plus complete review sweep; no route geometry exists to qualify |
| M3 | Conservative $84.41/≤52-extended target, explicit cost-gate setting, installed-system accounting m05/m11 |

The firmware reviewer found the existing builder remains R1-bound, has no R10
target, and requires ICM-45686 while the inherited board uses LSM6DSV320X; its R1
pin map differs from the inherited R9 netlist on 12 pins. No hash bypass was found.
A new R10 binding note must carry actual pins/AFs, port states, IMU map and fit-derived
lever arms. Firmware implementation/bench behavior remains unverified. Shedding
must preserve PWM timing, timestamps, bounded transfers and the fire-pulse cutoff.

## MCU review evidence

The independent signals reviewer checked [ST DS12110 Rev. 11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf),
Tables 9/10, pp.79/82/92: PC6 pin63 USART6_TX AF7, PC7 pin64 USART6_RX AF7,
PD0 pin81 UART4_RX AF8 and PD1 pin82 UART4_TX AF8. These match the candidate plan.
[ST AN2606 Rev.70](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf),
Table135 pp.320–323, excludes these interfaces/pins from the H743 ROM bootloader.
This is reviewed pin feasibility, not a new firmware binding. Freed PB10/PB14
remain unsuitable default choices for peripheral enables because ROM USART uses
them. Final GPIO/EXTI assignment and signed IMU map remain to be bound to R10.

## Rejected or narrowed interpretations

- No datasheet for C84: withdrawn after locating the MA-series sheet; assembly
  qualification remains R1-m09.
- Four corner holes necessarily require an owner decision: not established.
  Section 7 permits review-driven changes, and four corners do not prohibit an
  effective fifth support. Retaining P2 needs no relaxation.
- An M3 owner decision is unavoidable: not established while the stricter original
  cost ceiling remains available. Do not silently reuse the on-board RF allowance.
- UART backfeed damage/current: not proven without module input-circuit evidence.
  The confirmed finding is the missing state/isolation qualification contract.
- Missing R10 files or unmeasured routes before Phase B: expected, not standalone
  Critical/Major findings. No R9 measurement qualifies new R10 geometry.

## Verification performed on the inherited R9 baseline

The plain gate reached these results before environment failures:

```text
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
silkscreen outside the board outline (46.00 x 102.00 mm): 0 stroke points
fit check: OK (CAD envelopes only)
```

Default Python lacked NumPy. A temporary Python environment resolved that dependency.
The seeded scratch-project DRC then encountered KiCad 10.0.6's headless
`wxGetMousePosition ` crash. A scratch interposer following the existing R9
D-S6-14/D-S9-06 precedent allowed scratch DRC execution; it changes mouse-coordinate
queries, not DRC results. A subsequent full wrapped gate run was interrupted before
the seeded-suite summary. Its exit status is unavailable and it is **not a pass**.
The successful lines above do not establish a zero-exit full gate.

Independent read-only actuator checks reported `actuator safety contract: OK`
(exit 0) on R9. No R10 build, R10 route profile, R10 seeded suite, complete R10
BOM stock/cost run, fab package, firmware binding or bench test exists yet.

Root's in-memory seeded probes (no saved CAD mutation) returned:

```text
check_actuators.check baseline: []
R134 excluded from BOM/positions: []
R127 excluded from BOM/positions: []
R128 excluded from BOM/positions: []
C126 excluded from BOM/positions: []
J124 3.5 mm pitch / 2.3 mm copper diameter: gap 1.2 mm on both faces
r9_pyro_check.gate_bridges: issues [], forbidden 0, own_part True
```

An empty list means the existing function did not reject the seed. It is not a
full `tools/check.sh` result. The manufacturing reviewer also ran the existing R9
fab manifest check: five outputs matched. This remains R9 evidence only.

## Required eventual deviation headings — not owner acceptance

- Dropped pyro spacing and strict pad rules; accepted single-fault loss while
  retaining the complete ARM break and functional safety constraints.
- O3: loss of board-level servo power switching; final harness and return contract.
- O1/O2: external GPS/radio, L5 loss, closed LR900 protocol, band setup and installed
  antenna/module qualification.
- Parts lacking a maker datasheet, including any unresolved C84 documentation.
- Remaining Minor findings, each with measured reason and board-hash binding.
- Remaining mechanical, vibration, electrical, firmware and RF bench verification.

No final deviation list is possible before the design is implemented and reviewed.
(Round-1 note, superseded 2026-10-27: the parent `../../docs/VEHICLE.md` board entry is now edited for 46 × 90 mm in the
parent repository and left uncommitted there for the owner.)

## Historical R10 build state (2026-10-28, after round 8's fix pass)

**Board** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`407d1d8408330849526dbd31cf70ec94b9f012b23ff5c8324eb8a7b1f98bed05`, 46 × 90 mm, built by `m3_design/r10_build.sh` from
the hash-pinned R9 inputs; the worktree build and the routing slice's clone build byte-identical. Netlist SHA-256
`a9516746…`. (Review round 3 examined `883d2db5…`, round 4 `579575bd…`, round 5 `af18ac49…`, round 6 `3b6e15f3…`,
rounds 7 and 8 `b242ab8e…`.)

**Gates on the board** (CAD only; nothing below is a bench, physical or flight result):

| Gate | Result |
|---|---|
| `r10_sch_check.py` (pins, parts, safety / UART-isolation contracts, strict ERC, deterministic regeneration, nine seeded faults) | OK, 0 ERC, all nine seeds caught |
| `r10_stage_check.py` after each routing family (core, usb, pyro, power, signals, ground) | OK at every family; after ground: DRC 0, 0 unconnected, route_check 0 failing |
| KiCad DRC, every severity incl. silkscreen (min_silk_clearance 0.15), with schematic parity | 0 violations, 0 unconnected, 0 parity |
| ERC | 0 |
| Metadata / 3D model audit (quality_audit) | OK |
| Silkscreen outline (tools/silk_check.py) | 0 stroke points outside |
| fit_check --profile r10 | OK (CAD envelopes; GH ports mated 0.03 mm margin to the bore); wire room J1 / J121 / J124 printed |
| plate_model --profile r10 | f1 275.6 Hz pinned (≥ 209 Hz); every mass placed or refused; masses are Inference allowances |
| check_r10 (S-1 … S-9, K-contract, K-loader, K-actuators, LC-1, M-1, M-2, M-3, M-5, M-6, M-7, P-8, P-11, F9-1, T-1, K-legends, K-copper, K-inner, K-reference, K-region, K-fill, K-rules, K-retained) | OK; P-11 and F9-1 hold R10's recorded figures pending OQ-1 / OQ-2 |
| route_check --profile r10 (empty allowlist; arcs fail; port UART / control and ACT_* nets critical; needless-hop test) | 0 failing, 0 leftovers |
| check_actuators --profile r10 | OK |
| tools/test_r10_check.py (109 tests), test_check_shell (4), test_fit_check (23), test_paste_check (5): all run by `tools/check.sh` | OK (KiCad python; the numpy-only plate test under the numpy python) |
| tools/test_route_check.py (run by `tools/check.sh` since round 4) | 57 OK |
| Fab (`m3_design/r10_fab.sh`): jlc_orient, export, S-4 on the exported BOM / CPL, CPL rebuild, paste, manifest | OK (229 placed parts, 82 BOM lines; BOM unchanged since round 3), bound to `407d1d84…`; `tools/check.sh` verifies the binding since round 8 |
| JLC cost / stock (live data 2026-10-27) | **$87.01 per board vs the $84.41 target: missed** (OQ-3); 47 extended codes (≤ 52); short: R430 C185349 (17 in stock, 3,610 minimum purchase), U4 C26633007 (0, consign) |

**Rules re-derived for R10 with a recorded basis** (R10_DECISIONS): K-reference (D-R2-10, extended to the port control
nets D-R3-04 / -10); T-1 (D-R2-13); K-loader, S-8, S-9 (D-R3-10). **Held pending the owner** (D-R2-14): P-11 (OQ-1),
F9-1 (OQ-2).

### Owner questions and answers (2026-10-28)

The answers in `R10_DECISIONS.md` (commits `afed4d0`, `1076059`, `f202ec3`) supersede the earlier open questions.
They do not constitute acceptance of the complete R10 candidate or its remaining deviation list.

| Item | Owner disposition | Remaining verification |
|---|---|---|
| OQ-1, terminal wire room | Accept 4.95 mm, with 16–22 AWG in the DB125-3.5 terminals; P-11 holds that floor | Physical fit of wires and bends; measured CAD room is 4.953 mm, bare-bore method (4.44–5.39 mm on the actual openings with P2's wall allowance) |
| OQ-2, reverse hot plug | Re-model with R10's actual feeds and parasitics; move parts only if it fails; F9-1 must require the R10 model to pass | Model implementation and qualification in progress; old distance-only F9-1 is not electrical qualification |
| OQ-3, cost | **Unanswered:** $87.01 per board versus $84.41 ($2.60 over) on the 2026-10-27 snapshot; remains for owner acceptance and does not block a clean review round | Fresh supplier quote and stock, R430 minimum purchase, U4 stock or consignment |
| OQ-4, panel | Keep placement; aft-edge tab and panel rail/frame | JLC acceptance before ordering |
| OQ-5, loaded battery break | No hardware cutoff; C84 and PA6 analog-watchdog firmware shedding; accept 0.55–1.0 ms ports-on estimate as a deviation | Specify and measure detection, OE/EN latency and actual load decay; 8.7–13.6 ms applies only after ports are off and logic is shed |
| OQ-6, revised battery-lead fuse | **No battery-lead fuse.** Remove J1 fuse legend/instructions; keep J124's 5 A fast ARM-link fuse | Accepted unfused pack-to-U9/Q120 short risk: strain relief, no chafe points, crimped or soldered leads; inspect and measure the installed harness |
| OQ-7, shroud | Keep the board wholly forward of joint +47 mm, including sled axial tolerance; preserve stack slack | Physical sled, harness, external modules and shroud fit; no shroud clocking needed for the selected axial rule |

## Round 3: independent review of the built board (`883d2db5…`)

Ten reviewers, one lens each (requirements, safety, power / electrical, parts / BOM, MCU pins, mechanics, routing / AVA,
manufacturing, gate adversary, docs / firmware binding), each a fresh read-only context told to prove the design wrong,
all started together in one batch. Every reported Critical or Major was re-verified by the root on the board, the
generators or the cited datasheet before acceptance. **Result on `883d2db5…`: 0 Critical, 7 Major (confirmed; four
reviewers found R3-REQ-01 independently), 49 Minor after de-duplication.** The fix pass (five file-disjoint implementer
slices in their own clones, merged and integrated by the root, R10_DECISIONS D-R3-01 … D-R3-13) produced `579575bd…`.

| ID (duplicates) | Severity | Finding (evidence on `883d2db5…`) | Disposition |
|---|---|---|---|
| R3-REQ-01 (PWR-03, BOM-01, DOC-01) | Major | R410 is 100 kΩ on the board, BOM and gate but 120 kΩ in parts.json / r10_parts.py / parts_budget / parts_qualification: GPS limit 0.230–0.309 A, not 0.191–0.260; "all port shorts < 2 A" false (2.022 A) | **Fixed** (records, D-R3-01): 100 kΩ everywhere, budget re-derived on the peak-current criterion; the 2.507 A OVLO / 470 kHz corner listed |
| R3-SAF-01 | Major | Pyro barrels 0.25 mm from In2 3V3 (PYRO1_GATE via (14.40, 53.30), PYRO1_OUT) and RAW_PROTECTED (PYRO1_BUS / IGN, J124's window): single inner defects could fire at power-up or bypass both ARM plug and load switch; deviation 1 named only RAW-to-bus | **Fixed** (copper + gate, D-R3-02): In2 GND under the CH1 column, barrels ≥ 1.458 mm from non-GND inner copper, J124 window GND on all layers, R122's via 1.72 mm from R134.2; S-8 and widened S-5; deviation 1 rewritten with the remaining cases |
| R3-PWR-01 | Major | All logic and port power through a 0.25 mm neck and a 0.4 mm track with two vias at U9 (TI SLVSFC9C §8.4.1: 2× full load); IPC-2152 rise 23–35 °C at design load, not recorded | **Fixed** (D-R3-03): full-width entries, 1.0 mm runs, four vias; IPC-2152 table in M3_R10 |
| R3-PWR-02 | Major | F6's "14.5 ms with shedding" holds only with no port load: C84 back-feeds the port buck through U11 (reverse blocking above 0.2–2 A only); ports on ≈ 0.6–0.9 ms | **Fixed** (records, D-R3-13): F6 restated for ports off / on at 300.8 and 470 µF; hardware option as **OQ-5** |
| R3-MCU-01 | Major | D-R2-07 / -09 and deviation 5 claim no loader pin; PA4 / PA5 / PA6 (SPI1) and PE11 / PE12 (SPI4) are AN2606 Table 119 loader pins; check_r10 had dropped R8 / R9's loader rule (electrically harmless: PA6 ≤ 0.36 mA) | **Fixed** (gate + records, D-R3-10, -13): check_r10 K-loader with an allowance table and seeds; pin_table loader-role column; deviation 5 corrected |
| R3-RTE-01 (GATE-04, SAF-03) | Major | Twelve port-signal layer changes (RADIO_*, GPS_*, CAM UART) and ACT_GATE without a GND via within 1.5 mm; route_check's r10 critical set narrower than M2 and than K-reference | **Fixed** (copper + gate, D-R3-04, -07, -09, -10): one critical-net definition; every layer change ≤ 1.455 mm from a GND via; every B.Cu control run over one In2 region |
| R3-GATE-01 | Major | Arc tracks bypassed route_check and K-reference (seeded USB_DP arc passed check.sh) | **Fixed** (D-R3-10): `arc_segment`, arcs sampled; seeds |
| R3-REQ-02 (DOC-05) | Minor | REQUIREMENTS rows stated R9 facts as current for R10 | **Fixed**: R10 amendments (D-R3-13) |
| R3-REQ-03 | Minor | No R10 coat region or bench-gate text | **Fixed**: ORDERING §8 |
| R3-REQ-04 (BOM-02) | Minor | J410 / J420 no pin legends; mixed TX / RX conventions | **Partly fixed**: one board-side convention, J9 table; J410 / J420 tables do not fit (**listed**, deviation 10) |
| R3-REQ-05 | Minor | 15 A fuse vs J1's 10 A rating | **OQ-6** |
| R3-REQ-06 (MFG-04, DOC-09) | Minor | Fuse / ARM notes centred on the wrong terminals; J122 key only on the bottom | **Fixed** (D-R3-11) |
| R3-REQ-07 | Minor | J122 GND pads solid (R9's 7.7 A reason gone) | **Fixed**: thermal relief (D-R3-07) |
| R3-REQ-08 | Minor | Camera ≥ 5 V needs a ≤ 150 mΩ loop | **Recorded**: loop split in parts_qualification (harness spec); listed (deviation 13, C-9) |
| R3-REQ-09 (PWR-08) | Minor | LR900-F 1 W average, band 890–915 MHz (US overlap 902–915 only); TX peak vs R420's 0.348 A minimum | **Recorded**: binding note, parts_qualification; bench measurement before flight (C-9) |
| R3-REQ-10 (MCU-03, DOC-02) | Minor | Binding note's EXTI14 obligation on the buzzer pin | **Fixed** (D-R3-13) |
| R3-REQ-11 (DOC-08) | Minor | "≈ 1 A buck input" understated, unlabelled | **Fixed**: M3_R10 IPC-2152 bullet |
| R3-REQ-12 | Minor | Tin GH J400 in the ≈ 7 µA dry-circuit switch loop | **Recorded** (REQUIREMENTS F9 note), listed (deviation 13, C-9) |
| R3-SAF-02 | Minor | Port back-feed through an enabled TPS2553 is not blocked below ≈ 0.7 A; can keep the MCU and ACT_EN alive with the switch open | **Recorded**: firmware obligation, ORDERING §8 bench step, REQUIREMENTS / FMEA; listed (deviation 4) |
| R3-PWR-04 | Minor | PORT_5V3 In2 column 0.376 mm at y 24.8 | **Fixed** (D-R3-04): 2.395 mm |
| R3-PWR-05 | Minor | Buck input loop 7 mm | **Fixed** (D-R3-05) |
| R3-PWR-06 | Minor | No ≥ 1 µF / Schottky at U9's OUT (C82 13.3 mm, D9 18.9 mm) | **Open, listed** (C-10): needs a part; the In2 RAW_PROTECTED plane and its decoupling serve meanwhile |
| R3-PWR-07 | Minor | Port-switch bypass 4.3–4.9 mm away; single 0.3 mm vias at 1.25 A | **Partly fixed**: CAM_5V via 0.8 / 0.45 mm; no room for a second U402.1 via; bypass placement **listed** (deviation 13, C-10) |
| R3-PWR-09 (BOM-03) | Minor | U401 pad 11 has no thermal vias (via-in-pad barred by M2) | **Recorded**: parts_qualification corrected (junction ≈ 117–130 °C at 85 °C ambient, Inference); listed (deviation 13, C-10) |
| R3-BOM-04 | Minor | R430 stock / minimum purchase | **Listed** (OQ-3; deviation 13, C-11) |
| R3-MCU-02 | Minor | PC14 (≤ 3 mA) drives the buzzer gate through 220 Ω | **Fixed** (D-R3-12): 1 kΩ |
| R3-MCU-04 | Minor | Wrong / mixed DS12110 citations | **Fixed** |
| R3-MCU-05 | Minor | ESD103 RF clamp on the port UARTs not justified | **Recorded** in parts_qualification |
| R3-MEC-01 | Minor | Plate model silently dropped six masses | **Fixed** (D-R3-10): f1 275.7 Hz |
| R3-MEC-02 | Minor | Wire-room basis; J1 not gated; fit_check silent | **Fixed** (gate); basis in OQ-1 |
| R3-MEC-03 / -04 / -05 | Minor | TC2030 nose vs (4, 44.3) hardware; J9 mating load; GH cable dressing | **Recorded**: ORDERING §8 |
| R3-MEC-06 | Minor | Tie-channel wording; lever-arm z | **Fixed** (M3_R10) |
| R3-RTE-02 | Minor | R9's crystal In2 GND (D-S8-20) dropped without a record | **Fixed** (D-R3-06) |
| R3-RTE-03 | Minor | Extra vias / hops | **Fixed** where needless (CAM_MCU_TX); the rest cross named copper (needless-hop test), **listed** (deviation 13, C-12) |
| R3-RTE-04 | Minor | PULLPIN between U3's pads / 0.16 mm from J3's shell; long BUZZ_DRV | **Fixed** for PULLPIN (0.63 / 1.01 mm); BUZZ_DRV length **listed** (deviation 13, C-12) |
| R3-RTE-05 | Minor | Outer GND fragmented, no west-edge stitching | **Fixed** (D-R3-08) |
| R3-RTE-06 | Minor | Untidy pad entries, tracks between pads | **Partly fixed** (TP86, R162); the rest **listed** (deviation 13, C-12) |
| R3-RTE-07 | Minor | B.Cu nets on In2 splits | **Fixed** for every critical net (K-reference); SERVO2_MCU (R155 / D121 / R151 straddle the RAW / 3V3 split), LOGIC_SOURCE_ST **listed** (deviation 13, C-12) |
| R3-RTE-08 | Minor | No R10 M2 sweep record | **Fixed** by this record and the deviation list C-12 |
| R3-MFG-01 | Minor | Q121's EasyEDA arc ring over C120.1's opening, unseen by DRC | **Fixed** (D-R3-11) + K-legends polygon check |
| R3-MFG-02 | Minor | 59 silk items < 0.15 mm from pads | **Fixed**: 0 below 0.15 mm, asserted |
| R3-MFG-03 | Minor | Two via rings touching pad openings | **Fixed** (holes ≥ 0.15 mm from those openings); plugged-via 0.35 mm guidance: tent (ORDERING §8) |
| R3-MFG-05 | Minor | Legends under support hardware | **Fixed** (keep-outs asserted) |
| R3-GATE-02 / -03 / -05 / -07 | Minor | S-1 copper text / multi-net parts; needless hop; S-4 on the exported lists never run; no fire-path width floor | **Fixed** (D-R3-10) |
| R3-GATE-06 | Minor | "44 seeded tests on the committed board" overstated | **Fixed**: 68 tests, 20 on the board |
| R3-DOC-03 | Minor | F6 neutral-first / IWDG obligation missing from the binding note | **Fixed** |
| R3-DOC-04 | Minor | README / ORDERING describe the package as R9's | **Fixed**: R10 banners, ORDERING §8 |
| R3-DOC-06 / -07 | Minor | Counts (20 re-maps, six strays, no M-4); "nothing overhangs" | **Fixed** (AGENTS, M3_R10, this record) |
| R3-DOC-10 | Minor | Ambiguous U401 / U410 pin-1 dots | **Fixed** (asserted rule) |
| R3-DOC-11 | Minor | Local absolute paths in R6 records | **Fixed** in 19 files; six hash-pinned R6 records keep theirs (**listed** (deviation 13, C-14)) |

## Round 4: independent review of `579575bd…` (commit 8f10f17)

Ten reviewers, one lens each (as round 3), fresh read-only contexts, all started together in one batch. Every reported
Major was re-verified by the root on the board, the gates or the records before acceptance (the root's own In2
sampling, the DRU / project pinning code path, ORDERING §3–§8 text); one reported Major was downgraded and one Minor
rejected, with reasons below. **Result on `579575bd…`: 0 Critical, 4 Major (confirmed), 28 Minor after
de-duplication.** The fix pass (three file-disjoint implementer slices in their own clones, merged and rebuilt by the
root, R10_DECISIONS D-R4-01 … D-R4-04) produced `af18ac49…`.

| ID (duplicates) | Severity | Finding (evidence on `579575bd…`) | Disposition |
|---|---|---|---|
| R4-REQ-01 (MEC-02) | Major | ORDERING §8 said "sections 1–7 apply with R10's designators", but §3–§7 carry R9-only facts an R10 order would act on: the placement preview's "J1 toward the forward edge (y = 102)", J1 C2915641 with a +180° correction, J121 / J124 C430601, J30 / J31 / U30 / U31 / C121 in the polarity and pin-1 lists, J123 at (40.0, 29.6), the 102 mm size, R9's sled, hardware and battery-lead rows; on R10 J1 is C466970 at (7.0, 75.85) with its entry toward −x | **Fixed** (records, D-R4-04): ORDERING 8.1–8.4 supersede each item with R10's measured fact |
| R4-RTE-01 | Major | K-reference sampled no pyro net, and two pyro sense runs crossed an In2 split: PYRO1_CONT (15.15–19.85, 56.8) over 3V3 and GND with a 0.25 mm gap at x ≈ 17.45, ARM1_SENSE_MID at x ≈ 20.91 (y 58.75); RAW_ACT_SENSE's end at R124.2 over no In2 copper (root: 93 / 39 / 12 unreferenced samples). R3-RTE-07's "fixed for every critical net" was false for them | **Fixed** (copper + gate, D-R4-01, D-R4-03): In2 GND strip under PYRO1_CONT, CH1 band edges re-cut; K-reference on every signal-critical net |
| R4-RTE-02 | Major | M3_R10's "every such B.Cu run lies over one In2 region (route_check / K-reference)" was gated by neither tool (K-reference accepted any In2 plane) | **Fixed** (gate, D-R4-03): check_r10 K-region; synthetic seeds |
| R4-GATE-01 | Major | In profile r10 nothing pinned `m3.kicad_dru` or the project's design rules (check_actuators skips its DRU pins for r10): a seeded zero-clearance PYRO1_BUS / 3V3 rule, or `min_clearance` 0, passed `check.sh` (reviewer's seeds; root read the skip at check_actuators.py:526) | **Fixed** (gate, D-R4-03): check_r10 K-rules; both seeds now fail |
| R4-MEC-01 | Minor (reported Major) | P3's "≥ 5× at 100 g" had no R10 figure for C84, the DB125 terminals, J122, LS120, the GH plugs | **Fixed** (records): M3_R10 retention table. Downgraded: P3 verifies it by staking and external retention after inspection, and P3's R10 text names every R10 tall part and plug; R9 carried no per-part figure either |
| R4-GATE-02 | Minor (reported Major) | The self-tests listed in this record's gate table were not run by `check.sh` | **Fixed** (D-R4-03): `check.sh` runs both suites. Downgraded: the table reported runs that had happened, not a `check.sh` stage |
| R4-REQ-02 | Minor | REQUIREMENTS F8 / F9 named legends not on the board | **Fixed** |
| R4-REQ-03 (MFG-01, DOC-01) | Minor | ORDERING §8: TP120 at (18.0, 68.1); it is at (18.0, 67.3) | **Fixed** |
| R4-REQ-04 (MFG-02, DOC-02, DOC-03) | Minor | Stale `883d2db5…` bindings in REQUIREMENTS M2, ORDERING §8, parts_qualification, check_r10 comments | **Fixed** |
| R4-REQ-05 (MEC-06) | Minor | REQUIREMENTS P2 f1 276.4 Hz; the model gives 275.7 Hz | **Fixed** |
| R4-REQ-06 | Minor | J9 has RX on pin 3 / TX on pin 4, J410 / J420 the reverse; deviation 10 said they follow J9's convention | **Fixed** (records): M3_R10, ORDERING 8.2 cable check; deviation 10 reworded. The pin order itself stays (**listed**) |
| R4-REQ-07 | — (rejected) | VEHICLE.md has no R10 entry | Rejected: `../../docs/VEHICLE.md` line 39 carries the R10 candidate entry (root read it) |
| R4-SAF-01 | Minor | S-3 accepted a gate series resistor fed from 3V3 (check_actuators caught it) | **Fixed** (gate) |
| R4-SAF-02 (GATE-03) | Minor | S-1 / S-2 exempted rails and parts with > 4 nets (check_actuators caught the seeds) | **Fixed** (gate): named ties only |
| R4-SAF-03 | Minor | Deviation 1 case (c) omitted Q124's own gate–drain pad gap (≈ 0.5 mm) and the 3V3 via 0.75 mm from gate copper | **Recorded** (deviation 1 (c)); the via could not move (D-R4-02) |
| R4-PWR-01 | Minor | U9's 0.3 mm pad entries (0.6 mm beyond each 0.3 × 2.4 mm pad), the 0.4 mm via ladder and U400's 0.4 mm feeds not in the IPC record | **Recorded** (M3_R10; root measured the U9 copper): pad-pitch-limited short necks, bench thermal check |
| R4-PWR-02 | Minor | Plane-only DC solve of In2 RAW_PROTECTED available | **Recorded** (Inference): 36 mV, narrowest cut 3.6 mm |
| R4-BOM-01 / -02 / -03 | Minor | L400's proxy land (C189932); TXU0202 0.147 mm residual, pin 1 unrecorded; C84 CPL polarity unrecorded | **Recorded**: parts_qualification, ORDERING 8.2 preview checklist |
| R4-MCU-01 | Minor | Port RX nets float while OE is low and U1 in reset | **Recorded**: binding-note obligation (pull-ups before OE) |
| R4-MCU-02 / -04 | Minor | No ADC instance per sense; NC-pin rule incomplete | **Recorded**: binding note (Inference until checked against DS12110) |
| R4-MCU-03 | Minor | REQUIREMENTS F10 carried R8's EXTI map | **Fixed** |
| R4-MEC-03 / -04 | Minor | L1's 3.02 mm bottom hang unrecorded; camera-shroud window not reconciled | **Recorded**: M3_R10, ORDERING 8.4; shroud an open fit item (**listed**) |
| R4-MEC-05 | Minor | M-7 did not assert the lever arm or pad 1 | **Fixed** (gate) |
| R4-RTE-03 | Minor | NRST / BOOT0 outside route_check's critical classes; NRST layer changes 1.66–3.35 mm from GND vias, 3 vias | **Listed** (C-12): AGENTS §3's critical list does not name them; K-reference samples NRST |
| R4-RTE-04 | Minor | Four port IO / CAM_5V vias 1.73–2.80 mm from a GND via (route_check information) | **Listed** (C-12) |
| R4-RTE-05 | Minor | 0.212 mm 45° stubs into J410.3 / J420.3 / J9.3; R120 entries 0.27 mm off centre | **Fixed** (D-R4-02); ACT_GATE enters R120.2 by a 45° approach |
| R4-GATE-04 | Minor | S-1 copper skipped NPTH pads with copper | **Fixed** |
| R4-GATE-05 | Minor | No fill-freshness gate | **Fixed**: K-fill |
| R4-GATE-06 | Minor | Contract tables read from the repo without a printed hash | **Fixed** |

## Round 5: independent review of `af18ac49…` (commit 4d3fe72)

Ten reviewers, one lens each, fresh read-only contexts, all started together in one batch. The one reported Major was
re-verified by the root (ORDERING §8 text and the board's via-to-mask-opening distances: 225 of 350 via rings within
0.35 mm of a pad opening, 111 within 0.15 mm). **Result on `af18ac49…`: 0 Critical, 1 Major (confirmed), 36 Minor**
(one row per reviewer ID; duplicates in parentheses are not counted again). The round is not clean. The fix pass (three
file-disjoint implementer slices in their own clones, merged and rebuilt by the root, R10_DECISIONS D-R5-01 … D-R5-04)
produced `3b6e15f3…`.

| ID (duplicates) | Severity | Finding (evidence on `af18ac49…`) | Disposition |
|---|---|---|---|
| R5-MFG-01 | Major | ORDERING §8 carried no via-covering instruction (§8.1: "plugged, as section 3"; §4's tent remark not among the §4 items §8 keeps) although 225 of 350 vias sit within JLC's 0.35 mm plug-ink clearance of a pad opening; R3-MFG-03's "tent (ORDERING §8)" pointed at text that was not there | **Fixed** (records, D-R5-04): ORDERING 8.1 via row and 8.2 order remarks (plug where allowed, otherwise tent, never open mask; expected DFM query); counts on `3b6e15f3…`: 222 / 108 |
| R5-REQ-01 | Minor | ORDERING §8 bottom coat list omitted R177 (RAW_ACT) inside its box | **Fixed**: added; every part in the boxes coated, unlisted ones named |
| R5-REQ-02 | Minor | J9 legend "5V4" not backed by a record | **Fixed** (records): 5.456 V nominal PORT_5V3 |
| R5-REQ-03 | Minor | F6's 0.15 s bounce figure not re-derived for R10 | **Fixed** (records): U9's EN network equals R9's (values compared with the hash-pinned R9 netlist) |
| R5-REQ-04 | Minor | Parent VEHICLE.md put J400 on the x = 0 edge | **Fixed** in the parent repo (uncommitted there, for the owner) |
| R5-SAF-01 | Minor | S-1 / S-2 skipped parts with > 4 nets for sense-net bridges | **Fixed** (gate): any non-U1 multi-net part on both a RAW-side and an armed-side net fails |
| R5-SAF-02 (GATE-02) | Minor | S-3 did not bound the series resistor or GATE_N's pull; a unitless capacitor parsed as farads (check_actuators caught the seeds) | **Fixed** (gate) |
| R5-SAF-03 | Minor | BUS via (17.0, 63.7) 1.139 mm from Q121.8 (RAW_ACT), outside S-5's window; tented | **Listed** (deviation 1 (a): surface RAW-to-bus at the default clearance) |
| R5-SAF-04 | — (information) | Sense vias 0.151 mm from In2 3V3; harmless (≥ 10 kΩ, no gate) | No action |
| R5-PWR-01 | Minor | U9 OVLO pin above its recommended 0.5–1.5 V for inputs > 12.2 V (2.44 V at the clamp; abs max 6.5 V) | **Recorded** (parts_qualification, M3_R10) |
| R5-PWR-02 | Minor | TP89 on U9 ILM (analog, "do not leave floating") | **Recorded**: ORDERING 8 bench rule (high-impedance probe only) |
| R5-PWR-03 | Minor | AP63201 IQ 258 µA (LCSC's 22 µA is another variant) | **Recorded** |
| R5-PWR-04 | Minor | AP63201 loaded dropout typical-only | **Recorded**: bench step at a 6.0 V loaded pack |
| R5-BOM-01 | Minor | C120 (ACT gate–source, 16 V) sees ≈ 17.5–18 V Vgs during a 19.9 V clamp event; short fails safe (gate = source, off) | **Listed** (deviation 13): a 25 V part needs a new code or C29936 1 µF (changes the gate time constant); clamp events are transient |
| R5-BOM-02 | Minor | C84 Manufacturer "jieerrui" vs LCSC "JIERR" | **Listed** (deviation 6, the C84 maker gap) |
| R5-MCU-01 | Minor | 26 DS12110 page citations in pin_table.tsv off by one | **Fixed** (citation column only; no gate pins the file) |
| R5-MCU-02 | Minor | No obligation keeping LSE off (PC14 = OSC32_IN drives the buzzer) | **Fixed**: binding-note obligation |
| R5-MCU-03 | Minor | Sentinel pins "driven low" vs "analog" contradiction | **Fixed** in the binding note; pin_table's mode text left (marked superseded) |
| R5-MCU-04 | Minor | PA6 / PB1 single-fault over-voltage paths (no 4.7 kΩ pin resistor) | **Listed** (deviation 13), recorded in parts_qualification |
| R5-MCU-05 | Minor | VBUS_SENSE (VBUS/2) below VIH at VBUS < 4.62 V | **Recorded**: M3_R10, binding note (never a safety input) |
| R5-MEC-01 | Minor | Retention table's mated loads omitted the body mass | **Fixed** |
| R5-MEC-02 | Minor | LS120 not in masses.json | **Fixed**: 0.3 g (Inference); f1 275.6 Hz |
| R5-MEC-03 | Minor | J3 missing from the retention table | **Fixed** |
| R5-MEC-04 | Minor | Shroud window: the stack does place the board | **Fixed** (records): placement rule aft edge ≥ joint + 37.2 mm, else ≤ 0.75 mm radial overlap at J410 (listed as a fit item) |
| R5-MEC-05 | Minor | No upper bound on standoff + plate | **Fixed**: h + t ≤ 6.9 mm for a 46 mm plate (Calc) |
| R5-RTE-01 / -02 / -06 | Minor | K-region had no margin, skipped pads and chains; pads R124.2, R175.2, C127.1, R411.1 straddled In2 edges; PYRO1_CONT strip 0.57 mm on the diagonal; QSPI_NCS chain over 3V3 and GND | **Fixed** (copper + gate, D-R5-01, D-R5-03): 0.1 mm margin, pads, chains; In2 edges re-cut; CH1 strip ≥ 1.05 mm |
| R5-RTE-03 | Minor | 0.212 mm 45° stubs inside D410.1 / D420.1 / D401.1 | **Fixed**: diodes 0.15 mm north, straight entries |
| R5-RTE-04 | Minor | 0.05 mm off-axis entries (SPI1_MOSI → U4.14, PULLPIN → U1.7, RADIO_FAULT_N → R422.1, IO rails → U411.7 / U421.7, VBUS → U10.1) | **Partly fixed** (RADIO_FAULT_N); the rest **listed** (C-12) with the measured blocker (SPI1 lanes 0.03 mm short; C25.2's via 0.12 mm; D4.5's paste; IO-rail antipad on the OE run) |
| R5-RTE-05 (GATE-01) | Minor | Own-THT-pad exemption applied without a void (a seeded slot passed) | **Fixed** (gate): a sample is exempt only inside a no-copper component wholly within the pad's clearance disc |
| R5-RTE-07 | Minor | 0.1 mm collinear segments inside vias (GPS_IO_3V3, RADIO_IO_3V3, CC1) | **Partly fixed** (the IO rails); CC1's needs K-reference's REF_STRAY entry moved: **listed** (C-12) |
| R5-MFG-02 | Minor | Top-silk strokes 0.34 / 0.225 mm from the edges | **Fixed**: every legend and designator ≥ 0.615 mm inside; TP89 / TP81 moved; TP88's footprint silk 0.426 mm (its vias block a move) **listed** |
| R5-MFG-03 | Minor | Silk stroke exactly at JLC's 0.15 mm minimum | **Listed** (deviation 10) |
| R5-GATE-03 | Minor | check.sh's self-tests used the repo board; Debug-only output hid the failure message | **Fixed** |
| R5-DOC-01 | Minor | Deviation 1's "In2 and sense runs only" narrower than round 4's diff | **Fixed**: cases re-measured on `3b6e15f3…` |
| R5-DOC-02 | Minor | Round 4's count basis unstated | **Fixed**: this round states it |
| R5-DOC-03 | Minor | R6-era files with local absolute paths (pre-R10) | **Listed** (C-14) |

Root's own additions in the fix pass: K-region's no-copper samples inside another net's via antipad (via pad radius +
0.30 mm) are clearance holes, not plane boundaries (the SPI1_SCK / SPI1_MISO samples beside the MOSI via at (17.55,
43.5), which K-reference already holds; D-R5-03).

## Round 6: independent review of `3b6e15f3…` (commit b3ed2fe)

Ten reviewers, one lens each, fresh read-only contexts, all started together in one batch. The one reported Major was
re-verified by the root against `../../docs/VEHICLE.md` line 41 (shroud to within 18.4 mm of the axis, joint + 4…+47)
and fit_check's envelopes (GH-4 mated x 40.95–45.20, J122 mated 23.5 mm tall). **Result on `3b6e15f3…`: 0 Critical,
1 Major (confirmed), 39 Minor** (counting rule: each reviewer ID once; a row may carry several IDs; IDs in parentheses
are duplicates and are not counted again). Not clean. The fix pass (three file-disjoint slices, merged and rebuilt by
the root, R10_DECISIONS D-R6-01 … D-R6-03) produced `b242ab8e…`.

| ID (duplicates) | Severity | Finding (evidence on `3b6e15f3…`) | Disposition |
|---|---|---|---|
| R6-MEC-01 | Major | The round-5 shroud record understated the conflict and gave a wrong placement rule: "0.45 / 0.75 mm overlap" was only the envelope's inner edge crossing 18.4 mm (the GH-4 envelopes penetrate ≈ 3.8 mm, the board edges ≈ 4.6 mm, J122's mated plugs ≈ 5.1 mm if the shroud faces the top), and "aft edge ≥ joint + 37.2 mm" left y 0–9.8 of the board in the window | **Fixed** (records, D-R6-03): M3_R10, ORDERING 8.4, REQUIREMENTS P2: board wholly forward of joint + 47 mm in any clocking unless a measured clearance replaces it; owner question **OQ-7** |
| R6-REQ-01 | Minor | No R10 F7 fire-loop budget | **Fixed** (Calc): 4.50 Ω loop, 1.64 A at 7.4 V; 1.52 / 1.45 / 1.39 A with 2 / 3 / 4 stalled servos (F7: ≥ 1.5 A with up to two); 1.33 A at 6.0 V (below F7's 7.4 V point); DC solve open |
| R6-REQ-02 (MFG-01) | Minor | ORDERING 8.2 order remark still 225 / 111 vias | **Fixed**: 222 / 108 |
| R6-REQ-03 | Minor | Via counts' method not reproducible as stated | **Fixed**: method stated, labelled approximate (MFG and DOC reviewers reproduced 222 / 108 with it) |
| R6-REQ-04 | Minor | Nearest coated part to U4 is C11 (3.93 mm), not TP122 | **Fixed** |
| R6-REQ-05 | Minor | J3 staking inconsistent between the retention table and ORDERING | **Fixed**: J3 staked; J123 / J400 tie or RTV |
| R6-REQ-06 | Minor | cost_check.json bound to an older CPL | **Recorded**: cost evidence is BOM-bound (BOM unchanged since round 3) |
| R6-REQ-07 | Minor | No R10 line in M3; "R430 short" wording | **Fixed** |
| R6-REQ-08 | Minor | "Wire room 4.95 mm" read as nominal | **Fixed**: worst case, 4.95–5.55 mm; fit_check prints two decimals |
| R6-SAF-01 / -02 | Minor | S-8 ignored foreign pads and RAW_ACT's barrel (seeds passed) | **Fixed** (gate) |
| R6-SAF-03 | Minor | "Inner-layer shorts meet GND only" not literal: CONT / sense / ACT_GATE vias 0.25–0.81 mm from In2 3V3 / RAW_PROTECTED (benign) | **Fixed** (deviation 1 reworded with the measured exceptions) |
| R6-SAF-04 | Minor | Deviation 1 (c) omitted R126.1 (GATE_N, 0.835 mm from the 3V3 via) and the gate track 0.62 mm from Q124.5 | **Fixed** (deviation 1 (c)) |
| R6-PWR-01 | Minor | PORT_5V3 band narrowest 1.20 mm (8.5 °C), not 1.49 mm | **Fixed** (records) |
| R6-PWR-02 | Minor | No USB-only attach / inrush record (C84 behind U10) | **Recorded**: ORDERING 8 bench step; host ≥ 450 mA (Inference) |
| R6-PWR-03 | Minor | Q120 / Q121 turn-on time unrecorded | **Recorded**: τ ≈ 20 ms (Calc) |
| R6-BOM-01 | Minor | U4, L1, J121 / J124 codes not visible on LCSC's API | **Recorded**: confirm on jlcpcb.com/parts before ordering (ORDERING 8) |
| R6-BOM-02 | Minor | U4 mask web 0.100 mm, at JLC's limit | **Listed** (already an ORDERING remark) |
| R6-MCU-01 | Minor | "PE1 polled" stale; F6's roll interrupt needs IMU_INT1 | **Fixed**: PE1 on EXTI1, pull-down (binding note, pin_table, REQUIREMENTS F10, schematic note) |
| R6-MCU-02 | Minor | pin_table mode text "driven low for sentinels" | **Fixed**: "analog, never driven" |
| R6-MCU-03 | Minor | ADC channels still labelled Inference after round 5 verified them | **Fixed** |
| R6-MCU-04 | Minor | PE4 / PE2 are TRACED1 / TRACECLK; no trace-off / LCKR obligation | **Fixed** (binding note) |
| R6-MCU-05 | Minor | No QE / IMU SPI clock / gyro Ton / blocking-erase obligations | **Fixed** (binding note; erase figure Inference) |
| R6-MEC-02 | Minor | TP89's "0.006 mm spare" misleading | **Fixed**: 0.306 mm to a nominal 7.0 mm washer; washer OD measured |
| R6-MEC-03 | Minor | Lever-arm frame unlabelled | **Fixed**: `lever_arm_frame` in the binding note and M3_R10 |
| R6-MEC-04 | Minor | fit_check printed 5.0 for 4.95 | **Fixed** |
| R6-MEC-05 | Minor | fit report's mated_envelopes kept J123's PH box | **Fixed** |
| R6-MEC-06 | Minor | Nut side at the supports unstated | **Fixed**: nut on the sled side |
| R6-RTE-01 | Minor | CH1 In2 GND arms ended in 0.3 mm slivers round the sense vias, unstitched (5.9 mm reach) | **Fixed** (copper, D-R6-01): arms widened round each via; ≥ 0.65 mm round every via hole; farthest point ≤ 2.9 mm from a GND via |
| R6-RTE-02 (GATE-01) | Minor | K-region's REGION_ANTIPAD wider than the real hole, untested | **Fixed** (gate): exempt only inside a fill hole covered by foreign-via discs |
| R6-RTE-03 | Minor | CH1 bay mostly a via hole | **Fixed** (wording) |
| R6-MFG-02 | Minor | Silk edge keep-in basis unstated; not gated | **Recorded**: stroke centreline (ink ≈ 0.075 mm less), generator constant only; TP88 / J3 footprint silk listed |
| R6-GATE-02 … -05 | Minor | K-region margin, arcs, step, pad-chain join, void-disc radius untested; OwnPadVoids missed 0.03 mm slots | **Fixed** (12 tests; void test on polygon geometry) |
| R6-GATE-06 | Minor | parse_value misread infix values (4k7 → 4000) | **Fixed** |
| R6-GATE-07 / -08 | Minor | S-1 test-point rule by name; S-3 allowed a GATE_N pull-up (check_actuators caught both) | **Fixed** (gate): ARMED_PARTS allowlist; GATE_N membership |
| R6-DOC-01 | Minor | Round 5's counting rule wording | **Fixed** (this round's rule) |

## Round 7: independent review of `b242ab8e…` (commit 9dadb9a)

Ten reviewers, one lens each, fresh read-only contexts, all started together in one batch. **Result on `b242ab8e…`:
0 Critical, 0 Major, 33 Minor** (counting rule as round 6; R7-PWR-01 merged into R7-REQ-02). **First clean round.** The root re-checked the one copper
item that could matter electrically (R7-RTE-01: the In2 3V3 lobe that carries U2's output via (31.6, 74.6) into the
plane): the widest path from the lobe to the plane under U1 is ≈ 1.3 mm wide at its narrowest (26.7, 42.6), so the
0.24 mm neck beside the GND via (30.903, 62.022) is a parallel branch, not the feed. The fix pass changed gates and
records only (R10_DECISIONS D-R7-01, D-R7-02); **the board is unchanged** (`b242ab8e…`), so round 8 reviews the same
board.

| ID | Severity | Finding (evidence on `b242ab8e…`) | Disposition |
|---|---|---|---|
| R7-REQ-01 | Minor | F10's R8 parenthetical duplicated | **Fixed** |
| R7-REQ-02 (PWR-01) | Minor | F7 budget's paths not tabulated; two-stall case 1.52 A ignored R134 ±1 %, hot FETs, contacts | **Fixed** (Calc, re-measured fire path): 4.533 Ω; 1.633 A at 7.4 V; 1.506 A with two stalls (no margin: treated as failing until the harness is measured), 1.442 / 1.379 A with three / four; 1.32 A at 6.0 V |
| R7-SAF-01 | Minor | S-1's per-part allowlist covered BUS / IGN / OUT only | **Fixed** (gate): every armed-side net (`ARMED_NET_PARTS`) |
| R7-SAF-02 | Minor | MCU-side nets recognised by suffix only | **Fixed** (gate): `*_MCU` / GATE_N topology asserted |
| R7-SAF-03 | Minor | Trace pin override on the H743 unchecked | **Recorded** (binding note: no trace-capable debugger with the ARM link in; Inference) |
| R7-PWR-02 | Minor | USB attach inrush ≈ 2.4 mC beyond USB 2.0's allowance (Inference) | **Recorded**: ORDERING 8 bench step on a current-limited hub; USB-only programming host-dependent (**listed**) |
| R7-BOM-01 | Minor | C29936 (1 µF 25 V X7R, extended) could merge into C15849 (1 µF 50 V X5R, basic): one code, ≈ $0.31 per board | **Listed** (OQ-3 cost options; board frozen for the clean-round pair) |
| R7-BOM-02 | Minor | Seven capacitor Values carry no voltage / dielectric | **Listed** |
| R7-BOM-03 | Minor | R430 order acceptance unconfirmed | **Recorded**: confirm in the quote; 22 kΩ C31850 fallback (1.070–1.282 A) needs a port-budget re-check |
| R7-MCU-01 | Minor | PA15 resets to JTDI with a pull-up, not analog | **Fixed** (binding note; Inference until RM0433 is read) |
| R7-MCU-02 | Minor | No GPIOE_LCKR read-back; FMEA F-16 still locked PE3 / 5 / 6 / 12–14 as outputs | **Fixed**: LCKK read-back before arming; loader-jump sequence; FMEA F-16 R10 line |
| R7-MCU-03 | Minor | Loader jump vs a running IWDG; "≤ 32 ms" nominal | **Fixed** (binding note: jump only before the IWDG starts; ≈ 34 ms at the LSI corner, Inference) |
| R7-MCU-04 | Minor | Erase time (W25Q128JV 4 KB: 45 ms typ / 400 ms max, read) not in F5's margin; pad ring buffer | **Recorded**: firmware obligation (erase-suspend slices or a single pre-erase before arming) |
| R7-MEC-01 | Minor | Bore bound ignored the nut under the sled | **Fixed** (Calc): h + t < 6.3 mm at x = 4 / 42, < 5.7 mm at (3.7, 86) |
| R7-MEC-02 / -03 / -04 | Minor | Shroud list missed J3 (5.05 mm) and washers (4.1 mm); offsets vs radial values; the stack (≈ joint + 79–83 mm) already clears + 47 | **Fixed** (records; OQ-7 kept: it bites only if the bay or lead zone shrinks by ≈ 30 mm) |
| R7-MEC-05 | Minor | ORDERING §7's battery-lead row is R9's | **Fixed**: R10 row in 8.4 supersedes it |
| R7-MEC-06 | Minor | M3_R10 named J400 as the nearest top hardware | **Fixed**: TP89 3.806 mm |
| R7-MEC-07 | Minor | Board frame is left-handed (KiCad y-down) | **Fixed** (records): rotations in the IMU frame |
| R7-RTE-01 | Minor | In2 3V3 neck ≈ 0.24 mm beside the GND via (30.903, 62.022) | **Listed**: a parallel branch (root: the lobe's widest path ≈ 1.3 mm) |
| R7-RTE-02 | Minor | Two In2 3V3 slivers (26.0–29.8, 54.5–54.9; 27.1–27.6, 46.2–46.5) | **Listed** (plane copper, connected; board frozen) |
| R7-RTE-03 | Minor | VBUS_SENSE 0.225 mm flat jog between two 45° runs at (18.98–19.2, 30.9) | **Listed** (non-critical net; board frozen) |
| R7-MFG-01 | Minor | §1 / §2 output text is R9's | **Fixed** (8: what differs on R10) |
| R7-MFG-02 | Minor | The 0.8 mm CAM_5V via cannot be plugged | **Fixed**: 127 pluggable; CAM_5V via tented |
| R7-MFG-03 | Minor | J3 hand-finish neighbours on R10 unrecorded | **Fixed**: C83 / R7 / R8, 1.95 / 2.01 / 2.15 mm copper gap (R7 added in round 26, R26-TRI-12) |
| R7-MFG-04 | Minor | Order-number anchor rounding | **Fixed** |
| R7-GATE-01 | Minor | parse_value: "4.7 kΩ" → 4.7 | **Fixed** |
| R7-GATE-02 | Minor | Via-hole exemption tested vertices only (a 10 mm slot between two vias exempt) | **Fixed**: hole minus disc union must be empty (≤ 2e-3 mm²) |
| R7-GATE-03 | Minor | Extra parts on PYRO1_GATE / armed-side nets passed S-rules (K-actuators caught them) | **Fixed** (S-3 `GATE_PARTS`, S-1 `ARMED_NET_PARTS`) |
| R7-GATE-04 | Minor | P-11 / F9-1 constants survived mutation | **Fixed**: seeded real-board tests |
| R7-DOC-01 | Minor | "fit_check prints 5.0–5.6" stale | **Fixed** |
| R7-DOC-02 | Minor | AGENTS GNSS / radio cell read as if the ports were removed | **Fixed** |

## Round 8: independent review of `b242ab8e…` (commit 6bc0a63)

Ten reviewers, one lens each, fresh read-only contexts, all started together in one batch, on the same board as round 7.
Each reported Major was re-verified by the root: R8-GATE-01 by running `tools/test_check_shell.py` at HEAD (2 tests,
1 failure) and at 8f10f17 (OK), so round 4's check.sh change broke the gate's own fail-closed test; R8-MEC-01 by
measuring U5's pad extents against R13 / R64 / TP122 (0.69 / 0.42 / 1.40 mm) and reading ORDERING §8's coat list;
R8-MFG-01 by reading ORDERING §8's remarks block and its "not carried over" rule. **Result on `b242ab8e…`: 0 Critical,
3 Major (confirmed), 22 Minor** (counting rule as round 6). Not clean: the clean-round count restarts. The fix pass
(three slices, merged and rebuilt by the root, D-R8-01 … D-R8-03) produced `407d1d84…`.

| ID (duplicates) | Severity | Finding (evidence on `b242ab8e…`) | Disposition |
|---|---|---|---|
| R8-GATE-01 | Major | `tools/test_check_shell.py` (check.sh's fail-closed test) red since round 4 (its temp tree lacked the self-test scripts check.sh now runs) and not run by check.sh | **Fixed** (gate): stubs, a failure case per self-test stage, run by check.sh; a mutation removing the self-test stage fails it |
| R8-MEC-01 | Major | ORDERING §8 coated R13 / R64 "whole" 0.69 / 0.42 mm from U5's pads (MS5611, open pressure port) and TP122 1.40 mm; U5's exclusion had no distance | **Fixed** (records): coat ≥ 3 mm off U5's pads and body; R13 / R64 masked; U5 taped whole while coating; TP122 brushed from its south / east side, coat edge ≥ 1.0 mm from U5 |
| R8-MFG-01 (MFG-02) | Major | ORDERING §8's "type these" remarks held only the via items; no-cleaning, reflow order, paste-as-supplied, U4 mask webs, stencil, THT method and hole-fill lived in §4 with R9 designators, which §8 says are not carried over | **Fixed** (records): one complete R10 remarks block (a–j) in R10 designators; §4's u-blox profile, MSL bake, SMA, C121 and R9 hole-fill lines named as not applying |
| R8-REQ-01 (DOC-02) | Minor | F7's ACT_FET_S path is an upper bound; 62.6 mΩ rounding | **Fixed** |
| R8-REQ-02 | Minor | Board-position row figure; "no conflict as drawn" rests on R9's coax zone | **Fixed** (records; OQ-7 stands) |
| R8-REQ-03 | Minor | Pad-time pack size with the LR900-F at full power not restated | **Fixed** (Calc, Inference): ≈ 1.65–1.9 Ah before reserve; pack ≥ 2 Ah if the radio transmits continuously |
| R8-REQ-04 | Minor | 6.9 mm plate bound led, the nut-inclusive 6.3 / 5.7 mm followed | **Fixed** |
| R8-SAF-01 | Minor | PE4 trace override unmeasured; no bench step | **Fixed** (records): ORDERING 8 bench step (ARM link out, trace enabled, PE4 / TP122 observed) |
| R8-BOM-01 / -02 | Minor | GH-2 envelope is the mated height; .wrl header path | **Listed**: the .wrl files are hash-bound by the fab manifest and `r10_parts.py --check`; comment change deferred to the next part-library change |
| R8-MCU-01 | Minor | Unplugged port with OE high drives a continuous UART break (TXU0202's 5 MΩ input pull-down) | **Recorded**: binding-note obligation (DMA / IDLE reception, error masking, drop OE after repeated framing errors) |
| R8-MCU-02 | Minor | GPS UART level not specified by HGLRC; SH1.0 cable | **Recorded**: Inference; SH1.0-to-GH1.25 adapter |
| R8-MEC-02 | Minor | L1-to-plate gap 0.48 mm minus ≈ 0.29 mm static 100 g deflection | **Recorded**: standoffs ≥ 4.0 mm recommended (Calc) |
| R8-MEC-03 | Minor | U4 under U1's west pin row; no thermal record | **Recorded**: bench item (U4 / U5 temperature against U1 load) |
| R8-MEC-04 | Minor | U4–U5 spacing not re-measured | **Fixed**: ≈ 2.0 mm body, 1.71 mm courtyard; foam capped at U5 + 1 mm |
| R8-MEC-05 | Minor | DB125 height from the model only | **Fixed**: DORABO T0-1 read: 8.60 ± 0.30 mm |
| R8-RTE-01 | Minor | QSPI skew not recorded | **Recorded** (M3_R10): ≤ 10.4 mm (Inference: harmless at W25Q clocks) |
| R8-RTE-02 | Minor | Four F.Cu nets (BUZZ_DRV ≈ 3 mm of a 4 kHz square wave) cross over Y1, In1 GND between | **Listed**; HSE bench check (ORDERING 8) |
| R8-RTE-03 | Minor | I2C1 layer-change vias 4.53 / 1.88 mm from a GND via | **Partly fixed**: GND via (7.4, 51.2) 1.43 mm from SCL's; SDA's has no DRC-clean spot (U5 keep-out, R13 / R64) **listed** |
| R8-MFG-03 | Minor | cost / stock evidence files sit in fab/ | **Fixed**: stated as evidence, not uploads |
| R8-GATE-02 | Minor | Safety / revision legend text not pinned | **Fixed** (gate, K-legends) |
| R8-GATE-03 | Minor | A hidden designator on J124 passed | **Fixed** (gate): 14 safety / connector designators must stay shown; hidden set reported |
| R8-GATE-04 | Minor | BAT_IN / RAW_PROTECTED width not gated outside the fire path | **Fixed** (gate, K-width) |
| R8-GATE-05 | Minor | fab package drift not checked by check.sh; unrun tool tests | **Fixed**: check.sh verifies the fab manifest on the repository board (skipped inside `r10_build.sh`, which runs before `r10_fab.sh`); test_fit_check, test_paste_check added |
| R8-DOC-01 | Minor | README layout cells said fab / ORDERING are R9's | **Fixed** |

Also fixed in this pass (round 7 Minors that had been listed to keep the board frozen; the clean-round count had
restarted anyway): VBUS_SENSE's flat jog (R7-RTE-03), the In2 3V3 neck beside the GND via at (30.9, 62.0) (R7-RTE-01:
0.24 → ≈ 0.59 mm by moving U11.3's GND via to (31.5, 63.3)), the In2 3V3 tooth beside the crystal island (R7-RTE-02,
the island bumped to x 28.6); the 3V3 finger R7-RTE-02 reported at (26.0–29.8, 54.5–54.9) was not found on the fill.

## Round 9 prelude: incomplete review, stopped at the owner-decision boundary

The Codex hand-off started from committed round 8 (`04d0b04`) with no uncommitted changes to finish or discard.
The board remains SHA-256 `407d1d8408330849526dbd31cf70ec94b9f012b23ff5c8324eb8a7b1f98bed05`,
46 × 90 mm, 2,541,053 bytes. Three independent fresh validator contexts started together, within the session's
three-reviewer concurrency limit. None completed its full lens before the stop; the remaining seven were not started.
The findings below are a partial review record, not ten-lens round totals.

The requirements reviewer measured P-11 / F9-1 directly on the saved board. The root independently checked their
gate implementations, the inherited limits, D-R2-14 and the open OQ-1 / OQ-2 dispositions. The power reviewer also
confirmed the F9-1 qualification gap. These are existing unresolved departures, not newly introduced geometry.
The user's explicit instruction to stop when a requirement needs an owner decision applies: D-R2-14 reserves these
choices to the owner. No substituted gate limit is treated as owner acceptance or as electrical qualification.

| ID | Severity | Evidence | Concrete disposition |
|---|---|---|---|
| R9-REQ-01 | Major | P-11 measures 4.953 mm wire room at each of J1 / J121 / J124 against the recorded 6.25 mm floor. `check_r10.p11` passes against `WIRE_ROOM_R10 = 4.95` and explicitly reports OQ-1; D-R2-14 says the changed floor needs an owner decision. | **Resolved by owner 2026-10-28:** accept the measured clearance; P-11 floor 4.95 mm. Physical wire fit is unverified. |
| R9-REQ-02 | Major | F9-1 measures D8 12.86, C80 21.59, C96 20.93, C89 20.58, C95 20.55, R166 29.75, R167 25.47 and U9 32.22 mm from J1.1. The inherited hot-plug premises are 10.6 mm for protection parts and 27.07 mm for U9. `check_r10.f9` discards the inherited distance issues and holds R10's recorded distances; it does not simulate the transient. | **Owner selected requalification 2026-10-28:** model actual R10 feed parasitics and move parts only if the model fails. Qualification remains pending the implementation below. |
| R9-PWR-01 | Minor | `r10_parts.power_budget()` uses 62.5 °C/W for `ldo_ambient_85C_junction_inference_C`, yielding 110.386 °C at 0.40618 W. `parts_qualification.md` explicitly rejects that reference-board coefficient for U401's layout and uses an inferred 80–110 °C/W, yielding 117.49–129.68 °C. Root confirmed the generator expression against the qualification text. | **Fixed in owner-answer implementation:** generator and regenerated budget use the same 80–110 °C/W inference range (117.49–129.68 °C). Thermal bench obligation retained; no overheating is established by this discrepancy. |

Partial safety checks passed: actuator contract; S-1 … S-9 and P-8; independent pad/net inspection of the ARM break,
load-switch topology and gate network. J124's RAW–BUS gap is 1.600 mm on all four layers. An independent ideal DC
divider calculation gives 1.4003 V maximum at 8.4 V with ±1% resistor corners after one upper resistor shorts or one
lower resistor opens. These checks do not establish transient/reset behavior or bench safety.

Partial power checks confirmed U400 EN and VIN both on RAW_PROTECTED: the proposed OQ-5 hardware cutoff was absent. Conditional
ride-through recalculates to 0.555–0.651 ms with ports on and 8.880 ms with ports off and logic shed at 300.8 µF to
3.5 V. These were calculations, not transient measurements, before the later R92 allowance. OQ-3 … OQ-7 were
open at that stop; the owner answers above supersede that state. Supplier data was not refreshed. The deviation
list remains unfinished because the two-clean-round stop condition is unmet.

The root's fresh `tools/check.sh` run on the unchanged board completed with **exit 0**, using the supplied
NumPy-capable interpreter. No gate was skipped or weakened for this run. Summary:

```text
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
fit check: OK (CAD envelopes only)
R10 CAD contract (full): OK
routing hygiene: 0 failing, 0 allowlisted, 0 leftovers recorded
actuator safety contract: OK
Fab manifest: OK; 5 outputs match the current CAD and export inputs
```

Self-tests: shell 4, fit 23, paste 5 and routing 57 passed; R10 109 tests passed with the NumPy-only plate test
skipped under KiCad Python, then that one test passed separately under NumPy Python. Nonfatal wx initialization
warnings were emitted. This passing gate does not resolve OQ-1 / OQ-2. No fix pass was performed or committed;
the stop record was subsequently committed in `afed4d0`. Rebuild reproducibility was not rerun in that interrupted round.

### Owner-answer pass completed before the audit cuts (2026-10-28)

The interrupted changes were retained and rebuilt; none were discarded. At that hand-off, committing was blocked by the environment's denial of Git's `index.lock` write.
The supervisor subsequently committed this pass in `6fdac43`; no staging or commit was performed by this continuation. Two fresh executions of
`m3_design/r10_build.sh` produced byte-identical board SHA-256
`b860afbe406d7daec9757ccde89987d3439b32e0b1f8078bb01363be1704baa1` (46 × 90 mm, 2547258 bytes).
The electrical signature is `1f638065…`. Each build passed its complete board gate. The fabrication package was
then regenerated, including orientation and paste checks, and an unskipped `tools/check.sh` passed at zero with
the current fab manifest. The supplied NumPy interpreter was used without recording its local path.

```text
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
fit check: OK (CAD envelopes only)
R10 CAD contract (full): OK
routing hygiene: 0 failing, 0 allowlisted, 0 leftovers recorded
actuator safety contract: OK
Fab manifest: OK; 5 outputs match the current CAD and export inputs
```

Self-tests: shell 4, fit 23, paste 5 and routing 57 passed; R10 120 tests ran under KiCad Python (3 NumPy tests
skipped there), and those 3 passed under NumPy Python. The headless CLI required D-R1-05's mouse-coordinate
interposer; it does not alter any CAD or DRC rule. The runtime wrapper and logs remain outside the repository.
A fresh read-only verifier found no Critical or Major in the owner-answer source/model scope, passed the seven
hot-plug evidence tests and two independent numerical tests, and reproduced all four selected extrema exactly.
The full 2304-case sweeps, refined extrema and 60 local sensitivities pass (simulation / Inference): minimum
−14.497873371 V, maximum falling slew 8.525257186 V/µs. No bench result is claimed. R166 pulse durability,
installed unfused harness R/L, simultaneous IN/OUT waveforms, retained output and package/ground parasitics
remain qualification obligations. The earlier interrupted snapshot is not substituted for these two fresh builds.

This is a preparatory fix pass, not review round 9 and not a clean-round credit. AUD/GAP adoption is recorded
in R10_DECISIONS; its circuit and layout changes have not been included in this owner-answer board.

### Single screw-switch preparatory pass (2026-10-28)

J124 and its ARM-link fuse / legends are removed; canonical RAW_ACT now feeds R134 / J121 behind Q120 / Q121.
Source inspection exposed the old automatic divider enable. D-SS-01 assigns previously NC PC1 through a 1 kΩ
R122 to Q122, with the existing 100 kΩ pull-down; PE4 separately drives Q124. The schematic, circuit manifest,
pin table and binding agree. S-1…S-5 and check_actuators check this topology, required population, reset-off
bias and switch circuit; seeded bypass, pin, component and legend faults are rejected. R134 moves to B.Cu at
(7, 64.335): Q121 → R134 is 6.50 mm and R134 → J121 is 4.16 mm, both direct 1.0 mm copper without layer changes.
D-SS-03 preserves required visible safety references; Q124 has a reserved legal 1.0 mm label at (13.9, 61.0).
The DRU re-pin changes only its ARM-to-switch comment. Historical R9 profiles retain their behavior.

Two fresh complete builds produce byte-identical SHA-256
`60be35eaff86dd7a5fb8e065aa4204a51e7d786d7dfc8d2456cdd66c4b86f901`: 46 × 90 mm, four layers, 2,521,622 bytes,
244 footprints (94 top / 150 bottom), 934 straight track segments, no arcs, 349 vias (210 GND).
Netlist SHA-256 `3e08722d7ac997131cb11d7c9cb2d25e1b3babcfb853b71230db01118bc70e69`. The generated binding is refreshed.
Each build passes its complete board gate. Self-tests: shell 4, fit 23, paste 5, route 57 and R10 122
(3 NumPy tests skipped under KiCad Python and then passed separately); 3 standalone plate tests and 15 focused
real-board fault seeds also pass. The plate model, after removing J124's body / wire masses, gives f1 276.8 Hz
pinned (Calc / Inference; modeled mass 47.5 g). Physical gate timing, sense thresholds, firmware, vibration and fit
remain unmeasured.

The board-bound hot-plug model retains electrical signature `1f638065…` and passes 2304 required cases,
refined extrema and 60 local-path sensitivities: minimum IN −14.497873371 V and maximum falling slew
8.525257186 V/µs (simulation / Inference, not bench). `r10_fab.sh` regenerates 228 CPL rows and 83 BOM lines;
orientation, paste (323 F / 400 B flashes), required-fitted checks and the five-output manifest pass. The last
supplier-price / stock snapshot remains historical; no fresh procurement claim is made for this topology.
The final unskipped `tools/check.sh` passes at zero, including the regenerated manifest:

```text
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
fit check: OK (CAD envelopes only)
R10 CAD contract (full): OK
routing hygiene: 0 failing, 0 allowlisted, 0 leftovers recorded
actuator safety contract: OK
Fab manifest: OK; 5 outputs match the current CAD and export inputs
```

No interrupted source edits
were discarded. This preparatory pass is not round 9 and earns no clean-round credit. AUD/GAP implementation
is next; the pull-pin and IO LDO cells remain fitted at this boundary.

### Requirements-audit preparatory pass (2026-10-28)

This follows single-switch commit `73af96b`; it is not a full review round. All PCB changes come from the
placement, routing, footprint and schematic generators. No interrupted source edits were discarded.
AUD entries mentioning the former J124 / ARM link are superseded by the single-switch decision.

| Item | Implemented disposition and evidence |
|---|---|
| AUD-1 | C92 becomes C19666, 4.7 µF / 16 V X5R 0603. Maker typical bias plus recorded allowances estimates 2.211 µF effective (Inference), above TPS709's 1.5 µF minimum; bench qualification remains. |
| AUD-2 | One shared exact slow-net list narrows only partner-via / reference-region geometry. Fast interfaces, critical hygiene and S-8 stay blocking; slow-only partners and CH1 sense-plane arms are removed. |
| AUD-3 | Q120 / Q121 become AONR21357 / C431196 on the maker DFN3x3A_8L_EP1 land, source-facing at B(13.5,72.6) / B(13.5,67.6). Datasheet / hot-current / SOA assumptions and ≥100 ms enable settling are recorded. |
| AUD-4 | J123 / R160 / R161 / C160 / D122 and pull-pin legends removed; PC13 NC / analog, buzzer PC14 retained. |
| AUD-5 | TP84/85/86/87/89/92 and dedicated branches removed. Remaining probe map is in ORDERING §8; U9 ILM is probed only at its component pad, high impedance. |
| AUD-6 | Fire-only RAW_ACT / IGN / OUT tracks 0.5 mm; continuous input / U9 feeds unchanged. Saved fire-track total 19.304478 mm; total credited loop copper 30.1231 mΩ at 70 °C (Calc / Inference). |
| AUD-7 | R412/422/432 use 10 kΩ 1% 0402; R150–153 use 1 kΩ 100 mW 0603. Conservative 8.4 V fault stress is 72 mW through 70 °C. |
| AUD-8 | U412 / U422 and LDO-only parts removed; both GPS/radio TXU supplies use main 3V3. C443 / C453 local bypasses retained; OE-low requirement and back-feed limitations recorded. Camera U13 remains. |
| AUD-9 | U10 / U11 retained for USB-only programming / log download. |
| AUD-10 | Only exact collinear nodes, duplicate segments, inside-pad segments and 6 mm legend-distance findings become review-counted. Partial overlaps, crossings, connectivity, required/correct legends, text and mask rules still block. Eight inside-pad representations remain; no legend-distance findings. Full J410 / J420 pin tables now fit. |
| GAP-1 | Coupled source budget includes all pack loads: 7.4 V at fire gives 1.550071 A idle / 1.485263 A one persistent stall / 1.420229 A two. Original idle-servo F7 case passes; a jam is not cleared by a neutral command. No bench current claim. |
| GAP-2 | C82 / D9 / R92 moved into a measured local output cell. OUT+GND paths are 12.568808 / 16.691778 mm, projected areas 2.3153 / 17.4197 mm². These are engineering geometry bounds, not TI numerical limits or transient proof; detour / absent-return seeds fail. |
| GAP-3 | Exactly two 0.5/0.3 mm U401.11 GND vias, (27.3,13.6)/(27.9,13.6), with unchanged maker paste. Resin-filled, copper-capped, planar VIPPO manufacture required; wrong-net / extra / misplaced vias fail. |
| GAP-4 | C84 remains required-fitted in BOM/CPL but is manually fitted after both reflows under a separately validated local soldering process. No borrowed reflow or iron-temperature qualification. |
| GAP-5 | Normal physical firing including tail ≤20 ms. IWDG ÷4 / RLR239 gives 960 LSI cycles, nominal 30 ms; no refresh through firing. Recorded worst intact-hardware allocation 34.853 ms is guarded at ≤36 ms; R134 pulse graph and physical tail require bench correlation. |

Low-risk corrections: C120 becomes the existing 1 µF / 25 V C29936, fixing the old
16 V clamp-event overstress. Stacked replacement MOSFET pins share one drawn lead without changing the netlist,
removing six ERC junction warnings. Fabrication identity preflight then caught mixed same-code lands on C92 and C120; D-AUD-01a standardizes both to their existing part groups, with three 75 µm C92 route adjustments and C120 moved 75 µm north. The early schematic gate now catches both split-land seeds (22 total). The supplier orientation map is matched on all eight distinct numbered
fingers with fixed body origin: maximum actual delta 0.100124 mm, θ=0°, unchanged 0.35 mm limit. Custom EP anchors
are not treated as package origins. Source attribution and factory-preview obligation are retained.

Two fresh complete builds pass and produce byte-identical boards. The current fabrication checks and final
unskipped gate also pass. The preceding mixed-land candidate passed two CAD builds but failed export and was not committed. Current board SHA-256
`877d01996a59e9dd5c6dbc367274bb9a323a13982d67960fe46df9b0ee53205d`, 46 × 90 mm, four layers, 2,365,477 bytes:
225 footprints (89 top / 136 bottom), 883 straight track segments, no arcs, 323 vias (190 GND).
Netlist SHA-256 `0843da709e2d7a757e9b35cdff48158a54012c5353619cbf409ab961efd2c3ca`.
The native geometry inventory is `sources/r10_design/audit_native_inventory.json `; it records QSPI lengths,
Y1 crossings, support clearances, silk edge clearances and S-8's 1.458 mm minimum on this board.

Both complete builds and the final unskipped gate pass: DRC / unconnected / schematic parity / ERC all zero; metadata, fit, plate,
all R10 rules, routing and actuator contracts pass. Self-tests: shell 4, fit 24, paste 5, route 59, R10 131
(3 NumPy cases rerun separately and passed). Additional focused legacy-hook, standalone plate and actual-board
fault-seed tests pass. Plate f1 is 280.9 Hz pinned, modeled mass 45.5 g (Calc / Inference, not vibration evidence).
Hot-plug signature `cbebb332…` passes all 2304 required cases and convergence / local-path controls, with the
same −14.497873371 V / 8.525257186 V/µs extrema. The reduced capacitor inventory gives a 5.836941131 V retained-OUT
bound after two seconds (Inference). The unfused harness's ≥0.03 Ω / 0.1–2 µH limits still require measurement.

Fabrication passes: 215 CPL rows / 82 BOM codes; 203 independent pad reconstructions plus 12 placement-only
nonpolar-resistor checks, no orientation errors, 317 top / 365 bottom paste flashes, five manifest outputs.
Both rendered sides were inspected. Supplier evidence: 2026-10-28 21:37:13 UTC stock / 21:38:04 UTC cost,
**$84.43 vs $84.41**, 46 Extended / 36 Basic codes. Minimum purchases give about $86.23 including feeder share,
before fixed fees. R430 has 17 vs its 3610-piece minimum; U4 has 0 vs 5 needed. Procurement returns 1 for these
disclosed misses; OQ-3 remains a deviation and does not block CAD review. No quote or process is accepted,
nothing ordered. `sources/r10_design/audit_prep_evidence.json ` binds the complete summary to this board.
The final unskipped gate exits zero, including the current five-output manifest. This pass earns no clean-round
credit; a fresh full round 9 is next on the supervisor-committed board.

One build attempt stopped on the six new drawing junctions and was corrected in the generator. Another stopped
after the passing model because an editorial change to its running shell file disrupted the shell's read
position; the complete builds above use frozen executable sources. Neither interrupted attempt counts as a
passing complete build or a review round. Firmware, physical switch/gate/sense behavior, thermal performance,
VIPPO / manual-capacitor assembly, RF immunity and actual fit remain unverified.

## Round 9: full independent review of `877d0199…` (commit `8bccb07`)

Ten fresh read-only validator contexts, one lens each, ran in parallel batches of at most three. The lenses were
requirements / O1–O6, safety, power, parts / BOM, MCU interfaces, mechanics, routing / AVA, manufacturing,
gate adversary, and docs / firmware binding. The whole Phase A left the board and working tree unchanged.
The root deduplicated their findings and independently reproduced the cold-sequence discrepancy, hardware-stack
arithmetic, rule-selection and procurement failures. No Critical or Major finding was reported or accepted.

**Result: 0 Critical, 0 Major, 21 Minor groups: 17 new and four explicitly re-raised routing groups.** Existing
adopted architecture / bench-qualification obligations are carried in the deviation inventory rather than counted
again as new findings. This is a full round; the earlier three-lens owner-decision prelude is not. Its existing
R9-PWR-01 remains the historical thermal-record finding; the new fault-delay item is R9-PWR-02.

| Finding | Severity | Evidence on the reviewed board / source | Disposition |
|---|---|---|---|
| R9-REQ-03 (MFG / MEC / DOC duplicates) | Minor | REQUIREMENTS F10 retains PC13 / EXTI13; P2 / P3 retain J123, three DB125 terminals and 275.6 Hz. Native U1.7 is NC, J123 / J124 absent, two terminals; plate 280.9 Hz | Fixed records: current PC13 / EXTI / mating / retention / modal inventory; historical R7–R9 clauses remain qualified |
| R9-REQ-04 | Minor | M3_R10 current open-cost row says $87.43 / 47 Extended, versus bound $84.43 / 46 | Fixed current snapshot and history distinction; OQ-3 remains nonblocking |
| R9-SAF-01 (DOC duplicate) | Minor | M3_R10 firmware order enables PC1 before the passive test; generated obligations omit D-SS-04's pre-enable screen. A shorted Q124 can conduct before a later powered-bus refusal | Fixed schematic note, binding generator, ORDERING and FMEA: both controls low, qualified cold screen first, ≥1 s discharge check after prior enable, then PC1 high / PE4 low ≥100 ms and powered checks. Firmware absent; not an observed startup fire |
| R9-PWR-02 | Minor | Current TI SLVS841G p7 / revision p27 gives overcurrent FAULT 3–11 ms, while qualification says maximum 10 ms | Fixed source / firmware budget to 11 ms plus actual handling / decay latency; electrical limit calculations unchanged |
| R9-BOM-01 | Minor | Seven abbreviated capacitor Value strings across 21 fitted parts; exact identities already agree in PCB / XML / BOM | Fixed generator/source labels from seven primary source groups; no substitution / net / land change |
| R9-MCU-01 | Minor | ORDERING and binding prescribe nonexistent H743 TRACE_IOEN / TRACE_MODE controls; RM0433 Rev8 p3209 and ST header give bit20 TRACECLKEN | Fixed H743 debugger procedure, observed PE2 clock and retained GPIO-mode / lock validity; actual override remains unmeasured |
| R9-MEC-01 | Minor | Nut-stack calculation omits 0.3 mm vertical tolerance. Correct h+t maxima 6.018413 / 5.365256 mm; documented 5.7 mm at west support gives r25.037185 versus usable r24.9 | Fixed <6.0 / <5.3 mm bounds; measured 4.0 mm standoffs / ≤1.0 mm plate selected as starting stack; actual hardware maxima / eccentricity still qualify fit |
| R9-RTE-01 | Minor | BAT_SW_SOURCE F0.2 path 6.950000 mm | Fixed generator corners: 6.257107 mm, saves 0.692893 mm |
| R9-RTE-02 | Minor | NRST F0.2 prefix 5.864214 mm via (5,41.3) / (8.5,41.3) | Fixed corners (6.2021,41.5521) / (8.2479,41.5521): 5.516563 mm, saves 0.347651 mm |
| R9-RTE-03 | Minor | USB_FAULT_N B0.2 prefix 13.707716 mm via (16.15,38.5), (11.2,38.5), (11.2,32.5) | Fixed via corners (11.85,39.05) / (11.85,31.85): 13.110660 mm, saves 0.597056 mm; remaining endpoint branches preserved |
| R9-RTE-04 (carried) | Minor | NRST return companions 1.6552 / 3.3534 mm; BOOT0 1.6621; I2C1_SDA 1.8806. SCL now 1.4431 | Retain as noncritical-return deviations; these nets are outside the AGENTS named fast/critical set. The reference contract and bench obligations remain; no untested claim that every possible new stitch is impossible |
| R9-RTE-05 (carried) | Minor | SPI1_MOSI U4.14 x17.55 vs pad x17.50; IO entries and U10.1 offset 0.05 mm; between-pad routes at LED1 / R33 / C86 | Partly fixed: IO entries / vias centred x35.45 and U10.1 VBUS centred x11.30 after combined DRC / reference checks. Rejected on-axis MOSI via (17.50,44.30): IMU_body_B violation and 11 unreferenced SCK samples. Keep SPI / between-pad cases with measured reasons |
| R9-RTE-06 (carried) | Minor | SERVO2_MCU B tail crosses 3V3 / RAW_PROTECTED split for ≈0.42 mm; LOGIC_SOURCE_ST B chain crosses near y57.7–58.0 | Retain slow/control routing; a plane redraw needs power and return requalification. Fast interfaces remain held to their own reference contracts |
| R9-RTE-07 (carried) | Minor | BUZZ_DRV 36.38 mm / 3 vias; F.Cu projections over Y1: BUZZ 2.732695 mm / NRST 0.777648 | Retain necessary hops: simple BUZZ layer swaps cross VBUS_SENSE or USB_LIMITED. Solid In1 GND intervenes; HSE / buzzer interference is a bench item |
| R9-GATE-01 (root duplicate) | Minor | Unknown-only selector exits 0 with no rules; default full gate unaffected | Fixed API / CLI validation for unknown, mixed and explicit-empty selections; valid stage scope retained |
| R9-GATE-02 | Minor | Single wrong J410 / J420 / J122 pin texts and altered harness note pass K-legends, while GPS / radio generator validation catches them | Fixed final required / unique / correct tables and harness-note checks; AUD-10 distance-only relaxation preserved |
| R9-GATE-03 | Minor | EP9 anchor 0.43 ×0.43 mm vs actual copper 3.21 ×1.98 mm allows entire RAW_ACT 6.5 mm / BAT_IN 2.121 mm tracks at 0.43 mm through S-9 / K-width | Fixed by removing implicit pad-neck exemption. Current board passes; both width seeds fail; seven measured source-bridge exceptions remain exact |
| R9-PROC-01 (root) | Minor | Input-bound hypothetical under-budget R10 report at $84.40 / target $84.41 is rejected by shared fixed $126.41 target; same report with R9 target accepted | Fixed explicit R10 $84.41 / 52 profile, used by R10 fab / ordering; legacy default preserved. Procurement regressions run in check.sh. This seed is not a real supplier quote |
| R9-DOC-01 | Minor | Current FMEA F-16 R10 row says only PE4 locked; binding / PC1 enable require two locks | Fixed PC1 + PE4 locks, each LCKK / pin-bit readback; no firmware implementation claimed |
| R9-DOC-02 | Minor | ORDERING counts QSPI_IO2 as a foreign Y1 crossing; native clipping gives zero | Fixed two foreign crossings; HSE_OUT own crossing 2.565488 mm. Keep QSPI and buzzer bench stimulation |
| R9-DOC-03 | Minor | M3_R10 claims all port controls / ACT_GATE have ≤1.5 mm return partners and one In2 region after AUD-2; ACT_GATE examples 8.055674 / 3.506293 mm | Fixed wording to the retained critical scope and named AUD-2 slow exceptions; not a new unauthorized routing relaxation |

Independent baseline evidence: all 100 U1 pins agree across native PCB, XML, table and binding; all four binding
hashes match; 225 component identities / 700 pin mappings agree; expanded schematic contract and 22 fault seeds
pass. Sixteen selected functional / mechanical checks, all nine focused safety checks, hot-plug native extraction
and four fresh worst-corner solves, fit / plate, required-fitting, metadata and the five-output fab manifest pass.
The parts reviewer queried all 82 supplier codes at 22:03 UTC: exact MPN matches, only the known R430 / U4
shortages. Orientation reconstructs 203 rows plus 12 placement-only nonpolar resistors; paste 317 F / 365 B;
silk 144 shown / 81 hidden references plus 38 legends, text ≥1.0 mm and strokes ≥0.15 mm.

Routing baseline: 110,724 reference samples, 7,139 own-antipad exceptions, seven samples covered by six recorded
strays, zero loose samples; K-region 57 items / 21,777 samples, zero issues. All 22 explicit fast-net signal vias
have a GND partner within 1.4916 mm. In1 is one connected 3,778.91 mm² GND island. QSPI spread 10.413 mm, one via
per signal. AVA photographs inform placement / simplicity only, not an inferred electrical qualification.

Each of the three detour redraws passes all-severity DRC in a refilled temporary copy; their combination also
passes K-reference / K-region and removes all three noncritical local-bump candidates. The root's additional
combined IO / USB entry trial also passes DRC / unconnected / reference / region / route checks. The rejected
SPI trial is recorded separately and is not transferred to CAD. The fix pass uses generator edits only.

The source and gate fixes completed their focused checks: value-only schematic overlays,
22 existing contract seeds, 15 new gate regressions, 19 procurement tests and four shell fail-closed tests.
Two fresh complete canonical builds now pass and reproduce all 21 CAD / binding files byte for byte.
Fabrication / orientation / paste / the five-output manifest pass; the final unskipped `tools/check.sh` exits 0.
Live cost / stock refresh remains a disclosed failure ($84.43 vs $84.41; R430 / U4 short). R10_DECISIONS D-R9-01…D-R9-06 records the choices.
Round 10 reviews every changed CAD label / route and the full committed fix-pass target. Under the owner’s
continuation, clean rounds 9 and 10 form the required pair; no later PCB change is planned.

Scope incident: one reviewer ran a read-only legacy check in the R9 worktree. No files changed; this run is
excluded, access stopped, and later legacy evidence is limited to this worktree's pinned inputs. Computer Use
rejected KiCad / PCB Editor launch; native geometry and rendered CAD were used, with no GUI bypass. No physical,
firmware, installed RF-immunity or fit result is claimed.

### Round 9 fix-pass completion (2026-10-28)

Board **`b337fe63c258c85ba4120e75ad018afa0c22241f8bc21a4172787cf2887208d9`**, 46 × 90 mm,
2,366,509 bytes; netlist `ca70b6dd…`. All 21 generated CAD / binding files agree after two complete builds,
including the regenerated evidence note. Native comparison to this worktree’s committed `8bccb07` blob finds
225 unchanged footprint poses / lands / pad nets and 21 expanded Value labels; the five changed routing nets
are BAT_SW_SOURCE, NRST, USB_FAULT_N, 3V3 and VBUS (D-R9-04). No part substitution or MCU pin change.

The unskipped final `tools/check.sh` exits 0: DRC / unconnected / schematic parity / ERC **0 / 0 / 0 / 0**;
metadata, silk, fit / plate, all 33 R10 rules, routing, actuator and current five-output fab manifest pass.
Tests: shell 4, procurement 19, fit 24, paste 5, routing 59, R10 140; the three NumPy cases skipped by KiCad
Python pass in the separate NumPy invocation, leaving no unresolved skip. Full output with routine tool noise
and temporary paths omitted: `sources/r10_review/round9_fix_check.txt`; hashes, counts and limits:
`round9_fix_validation.json `; native current-board measurements: `round9_geometry.json `.

The 2304 required hot-plug cases and refinement / cold-output checks pass as simulation / Inference; numerical
results equal the baseline, with fresh input/model binding for the expanded C88 label. Fab has 82 BOM codes /
215 CPL rows, 203 pad reconstructions plus 12 nonpolar placement-only checks, paste 317 F / 365 B. Live stock
23:24:17Z / price 23:25:10Z remains **$84.43 vs $84.41, 46 Extended codes**, R430 17 vs minimum 3610 and U4 0 vs 5.
`FAB_NET=1` exits 1 for those real procurement misses; it is not a CAD/export failure or a release pass.

This restart’s first plain CLI attempt aborted in the known headless wx mouse query. The external D-R1-05
interposer restores that query only; the native DRC engine still reports the expected intermediate violations,
and all final gates / fault seeds run. No repository runtime dependency or rule changes for the workaround.
Software / CAD and simulation pass; firmware, bench, installed RF immunity, physical fit, process and order
qualification remain unverified. Round 10 freshly reviews the committed fix pass; no new PCB change is planned.

### Review-round log

| Round | Board reviewed | Critical / Major / Minor (confirmed) | Fix pass → board |
|---|---|---|---|
| 1 (plan) | none (plan, inherited R9) | 0 / 7 / 9 | owner decisions O5 / O6; R10 built (`883d2db5…`) |
| 3 (first board round) | `883d2db5…` | 0 / 7 / 49 | D-R3-01 … D-R3-13 → `579575bd…` |
| 4 | `579575bd…` | 0 / 4 / 28 | D-R4-01 … D-R4-04 → `af18ac49…` |
| 5 | `af18ac49…` | 0 / 1 / 36 | D-R5-01 … D-R5-04 → `3b6e15f3…` |
| 6 | `3b6e15f3…` | 0 / 1 / 39 | D-R6-01 … D-R6-03 → `b242ab8e…` |
| 7 | `b242ab8e…` | **0 / 0 / 33 (clean)** | D-R7-01, D-R7-02 (gates and records; board unchanged) |
| 8 | `b242ab8e…` | 0 / 3 / 22 | D-R8-01 … D-R8-03 → `407d1d84…` |
| 9 (full; prelude excluded) | `877d0199…`, `8bccb07` | **0 / 0 / 21 (17 new, 4 carried; clean)** | D-R9-01 … D-R9-06 → `b337fe63…`; full round 10 covers the Minor fix pass |
| 10 | `b337fe63…`, `619db7e` | **0 / 0 / 8 (4 new, 4 carried; clean)** | D-R10-01…03, gates/records only; PCB unchanged |
| 11 | `0c50b9fd…`, `21bc3b2` | **0 / 1 / 16; not clean** | D-R11-01…05 → `0ad0135c…`; two full passing builds / 42 identical generated files; fresh full rounds follow |
| 12 | `0ad0135c…`, `d57b216` | **0 / 0 / 12; clean for that PCB** | D-R12-01…03 → `7355ae1a…`; two complete builds/check 0 and 42-file equality; fresh full same-board 13/14 required |
| 13 | `7355ae1a…`, `fa897c8` | **0 / 0 / 17; clean for that PCB** | 24 active raw; three closed historical MCU entries excluded; source fixes require fresh 14/15 on committed result |
| 14 | `e0e3ad84…`, `f5e4a5a` | **0 / 0 / 14; clean for that PCB** |20 raw; fixes require fresh 15/16 on `7866d6b8…` |
| 15 | `7866d6b8…`, `789f4d5` | **0 / 0 / 14; clean for that PCB** |20 raw; source fixes produce `632a9ad3…`, requiring full 16/17 |
| 16 | `632a9ad3…`, `b1b8658` | **0 / 0 / 11; first clean on this PCB** |17 raw; gate/record fixes only, PCB unchanged |
| 17 | `632a9ad3…`, `ac483f4` | **0 / 0 / 13; same-board pair earned** | 23 raw, 4 new / 9 carried; closing records/checks only, PCB unchanged |
| 18 | `632a9ad3…`, `dcbb6c8` | **0 / 0 / 68 raw (57 new, 11 carried); first review by a different model family** | 36 consolidated groups ([Round 18](#round-18-first-claude-review-of-committed-dcbb6c8)); the fix pass changed the board (`a3144b15…`), which needs a new clean pair |
| 19 | `a3144b15…`, `1e60441` | **0 / 0 / 57 (41 new, 16 carried); second Claude review** | D-R19-01 … D-R19-14 (including the owner-approved AUX port) → `50a39de5…` ([Round 19](#round-19-second-claude-review-of-committed-1e60441)); the changed board needs a new clean pair |
| 20 | `50a39de5…`, `6628488` | **0 / 0 / 32 (25 new, 7 carried); seven Claude board lenses** | D-R20-01 … D-R20-11 (polish pass; D-R20-01 and D-R20-10 not done) → `0dc84776…` ([Round 20](#round-20-board-lenses-on-committed-6628488)); the changed board needs a new clean pair |
| 21 | `0dc84776…`, `accfff4` | **0 / 0 / 35; ten Claude lenses** | D-R21-01 … D-R21-09 → `5516eeec…` ([Round 21](#round-21-ten-lenses-on-committed-accfff4)); the changed board needs a new clean pair |
| 22 | `5516eeec…`, `ec8cb98` | **0 / 0 / 22** | Between-rounds pass of checks, one schematic note and records, D-R22-NN ([Round 22](#round-22-ten-lenses-on-committed-ec8cb98)); board unchanged |
| 23 | `5516eeec…`, `c70d261` | **0 / 0 / 55** | Second review of the closing pair on the same board, complete; closing pass of text and checks, D-R23-01 … D-R23-11 ([Round 23](#round-23-ten-lenses-on-committed-c70d261)); board unchanged |
| 24 board pass | `5516eeec…` (no review; owner request and round 22 / 23 dispositions) | — | D-R24-01 … D-R24-17: second barrels where they fit, D402 at J400.2, every 90° bend chamfered (new `right_angle` rule), order mark removed, R92 / TP88 moved → `1407e850…` ([Round 24 board pass](#round-24-board-pass)) |
| 24 | `1407e850…`, `f2b8251` | **0 / 0 / 24 raw Minor; 17 real errors after triage** | First review under the owner's strict rule; R24-TRI-01 … -17 ([Round 24](#round-24-ten-lenses-on-committed-f2b8251)); fix pass D-R24-18 … D-R24-23 and the docs lane → `92c3ad59…` ([Round 24 fix pass](#round-24-fix-pass)); the changed board needs a new clean pair |
| 25 | `92c3ad59…`, `c4bb56b` | **0 / 0 / 14 raw Minor; 10 real errors after triage** | R25-TRI-01 … -10, none on the board ([Round 25](#round-25-ten-lenses-on-committed-c4bb56b)); fix pass D-R25-01 … -03 and the docs lane ([Round 25 fix pass](#round-25-fix-pass)); board unchanged, but round 25 was not clean |
| 26 | `92c3ad59…`, `3d8e845` | **0 / 0 / 14 raw Minor; 12 real errors after triage** | R26-TRI-01 … -12, one on the board (TRI-09) ([Round 26](#round-26-ten-lenses-on-committed-3d8e845)); fix pass D-R26-01 … -04 and the docs lane → `a0ec075e…` ([Round 26 fix pass](#round-26-fix-pass)); the changed board needs a new clean pair |
| 27 | `a0ec075e…`, `816038c` | **0 / 0 / 7 raw Minor; 7 real errors after triage** | R27-TRI-01 … -07, none on the board ([Round 27](#round-27-ten-lenses-on-committed-816038c)); fix pass D-R27-01 … -03 and the docs lane ([Round 27 fix pass](#round-27-fix-pass)); board unchanged, but round 27 was not clean |
| 28 | `a0ec075e…`, `19dd0b5` | **0 / 0 / 8 raw Minor; 9 real errors after triage (1 Major, 8 Minor)** | R28-TRI-01 … -09, none on the board; the Major is an AGENTS §2.5 labelling violation promoted from a safety observation ([Round 28](#round-28-ten-lenses-on-committed-19dd0b5)); fix pass D-R28-01 … -04 with the docs and audit lanes ([Round 28 fix pass](#round-28-fix-pass)); board unchanged, but round 28 was not clean |
| 29 | `a0ec075e…`, `09a564e` | **0 / 1 / 4 raw; 5 real errors after triage (1 Major, 4 Minor)** | R29-TRI-01 … -05, none on the board; the Major is an AGENTS §2.5 labelling violation with four false status claims ([Round 29](#round-29-ten-lenses-on-committed-09a564e)); fix pass D-R29-01 … -02 and the docs lane ([Round 29 fix pass](#round-29-fix-pass)); board unchanged, but round 29 was not clean |
| 30 | `a0ec075e…`, `0afaed3` | **0 / 0 / 2 raw Minor; 2 real errors after triage** | R30-TRI-01 … -02, text only, none on the board ([Round 30](#round-30-ten-lenses-on-committed-0afaed3)); fix pass by the docs lane ([Round 30 fix pass](#round-30-fix-pass)); board unchanged, but round 30 was not clean |
| 31 (planned) | `a0ec075e…` | — | First of the closing pair under the strict rule |
| 32 (planned) | `a0ec075e…` or its successor | — | Second review; iteration stops after two consecutive rounds with zero verified real errors |

## Historical banners

These banners opened this file when their boards were current. Every "now" in them refers to the named board, not to the current PCB.

**Rounds 16 and 17 closing changes (history).** Documentation, checker explanations, manifest enforcement and evidence only. No PCB, circuit or layout generator, pin assignment, pose, land, via, axis or AGENTS section 2 change. Four new Minor groups were corrected, and the courtyard metric was
corrected while its graphic residual remains. Nine groups remained measured deviations. D-R16-03 cancelled further Minor CAD cleanup at that point; the Claude supervisor applied the listed Minors in the round 18 fix pass by supervisor decision (see Round 18). The complete ledger indexes 126 decisions and 23 owner-mandate records; the original full R17 scope was 122 decisions and 23 mandates.
The round 17 power review repeated the 2304 required + 60 local hot-plug cases on the unchanged extracted feed; its mechanics review repeated 181.1 Hz (pinned D5), 70.4976 g estimated mass and the 0.270913 mm C431 gap at h = 4 mm; manufacturing DRC / unconnected / parity / ERC 0, 14 normalized CAM members, orientation, 618 paste geometries and the five-output manifest passed.
The gate adversary's missing-manifest control was corrected separately and covered by final native verification. See round17_reconciliation, round17_pad_energy, round17_gate_fix and round17_fix_validation under `m3_design/assembly_review/sources/r10_review/`.

> **Historical circuit pass, owner/supervisor 2026-10-28 (superseded by the layout above):** always-on GPS/radio,
> retained camera switch/isolation, SPI3 hinged microSD, sole bus sense/direct
> ADC inputs, all wired DB125 terminals and requirements audit2. This pass proves
> circuit/CAD integration only. The separate layout agent owns the AVA pass,
> full reviews beginning11 and the final board-bound deviation list. No clean
> round is credited to this changed board. The older acceptance inventory and
> rounds9/10 below apply only to b337fe63…; they must be refreshed after layout.
> Evidence/hand-over: `sources/r10_review/circuit_pass/`. No physical/firmware
> qualification, owner acceptance or order is claimed.
>
> **Circuit-pass board (2026-10-29):** SHA-256
> `6e73b6ebe7e25d7a8c810493887fbaa7cce34f6fe1d379828dc67017e14235aa` (electrical signature `6446a957…`),
> 46 × 90 mm, 2,244,550 bytes, 209 footprints / 887 track segments / 303 vias. Software / CAD: two complete
> `m3_design/r10_build.sh` runs gave the identical SHA-256; both pass every stage and the full `tools/check.sh`
> (DRC 0 / unconnected 0 / parity 0 / ERC 0, metadata, silkscreen, fit, every `check_r10` rule incl. K-reference,
> S-1 … S-9, F9-1 and K-actuators, route_check profile r10 0 failing, all gate self-tests). Simulation / Inference: the
> hot-plug model re-extracted from this board's actual feed (R166 moved) passes 2304 / 2304 cases. Fabrication:
> package regenerated and bound (manifest OK), 82 BOM codes (46 extended / 36 basic), 199 placed parts, CPL 72 top +
> 115 bottom rows plus 12 placement-only checks; live JLC 2026-10-29 $82.59 per board vs $84.41 (met), R430 and U4
> short (preliminary evidence, not a release pass). **No review round has been run on this board.** The deviation
> list at the end of this file and every count in it (including OQ-3's $84.43) are `b337fe63…`'s; a refreshed
> inventory is due after the layout pass and fresh rounds from 11. Firmware, SD latency / power loss, harness and
> DB125 fit and the e-match lot's 20 ms firing are unverified.


> **Historical completion before the circuit changes, 2026-10-28:** full rounds 9 and 10 are clean: **0 Critical / 0 Major / 21 Minor** on
> `877d0199…`, then **0 / 0 / 8** (four new / four carried) on committed`b337fe63…` /`619db7e`. The round-9 fix
> pass was committed after two identical builds and gate0. Round10 covers every changed CAD byte; final fixes
> affect gates/records only. The completed current-board deviation list below awaits owner acceptance, including
> OQ-3 **$84.43 vs $84.41**. Procurement/process/physical/firmware qualifications remain open; nothing ordered.

> **2026-10-28 hand-off check: round 9 stopped for owner decisions.** Starting worktree clean at `04d0b04`,
> board `407d1d84…`. Three fresh read-only reviewers started in parallel (requirements, safety, power); the
> owner-decision boundary below stopped the review before the other seven lenses. This is not a completed round
> or a clean pass. The consecutive-clean count remains zero. No implementation fix pass or rebuild was performed.

> **Historical (board `407d1d84…`, superseded): 2026-10-27 update.** The R10 board is built and committed; review rounds 3 (on `883d2db5…`), 4 (on `579575bd…`),
> 5 (on `af18ac49…`) and 6 (on `3b6e15f3…`) and their fix passes are done (board `b242ab8e…`, 46 × 90 mm;
> `docs/M3_R10.md`); round 7 on `b242ab8e…` was clean (0 Critical, 0 Major), round 8 on the same board was not
> (3 Major, all records / gate tests, fixed; board now `407d1d84…`); `tools/check.sh` passes at zero. See "R10 build
> state", "Round 3" … "Round 8", the review-round log and "R10
> deviations for owner acceptance" at the end. The round-1 plan-review record below is kept as written; statements in it that no R10 implementation
> exists describe that time.

## Round 10: full independent review of `b337fe63…` (commit `619db7e`)

Ten fresh independent contexts, one lens each, reviewed the immutable round-9 fix-pass commit: requirements /
owner decisions, safety, power, parts / BOM, MCU, placement / mechanics, routing / AVA, manufacturing, gate
adversary, and docs / firmware binding. Every reviewer verified the target before and after; Phase A made no
canonical edit. Full records: `m3_design/assembly_review/sources/r10_review/round10_reviews.json `.

**Result: 0 Critical, 0 Major, 8 Minor groups: four new and four re-raised routing groups.** This uses round 9's
counting convention: existing architecture / qualification / procurement obligations are inventoried rather than
recounted as new discoveries. The independent manufacturing coating finding duplicates the mechanics finding.
No Critical / Major candidate required a fresh verifier. Manufacturing and the root independently reproduced the
coating geometry; gate seeds and MCU limits carry direct native / primary-source evidence.

| Finding | Severity | Evidence on the reviewed target | Disposition |
|---|---|---|---|
| R10-GATE-01 | Minor | A conflicting F.Silk PCB_TEXTBOX `J420 3:RXI`, box (2,10)–(14,12), passes K-legends and native all-severity DRC; actual board has none | Include PCB_TEXTBOX in required/unique/correct port and harness legends; fault regressions reject conflicting/duplicate tables and notes |
| R10-GATE-02 | Minor | In2 graphic (5.75,53.7)–(5.75,54.5), width 0.2 mm, is 0.500 mm from J121.1 barrel yet S-8 and refilled DRC pass; actual board has no inner graphics | Use complete copper_nodes geometry for S-8, including drawings/text/fields/footprint zones; no-net and net-labelled graphics/text fault tests |
| R10-MCU-01 | Minor | PA6 current record says 7.3 V. DS12110 Rev11 Table109 pp207–208 notes 3–5 gives4 V ADC-mode ceiling, digital FT ceiling≤6 V | Correct generator/qualification and regenerate note; scope historical7.3 V claims. Normal divider and carried single-fault damage conclusion unchanged |
| R10-MEC-01 / R10-MFG-01 | Minor, counted once | Whole-coated C11.1 lies2.818449 mm from U5 nominal body, versus stated3 mm; old3.027515 mm was pad-only | Mask C11 whole, keep3 mm from body+pad union and whole-U5 tape; preserve controlled TP122 exception. C10 conservative Fab/pad clearance3.333144 mm, others≥5.075 mm |
| R9-RTE-04 | Minor, carried | NRST returns1.655174/3.353357 mm, BOOT0 1.662077, SDA1.880571; SCL1.443087 | Retain exact noncritical-return deviations; no fast-return waiver |
| R9-RTE-05 | Minor, carried | MOSI U4.14 offset0.05 mm; between-pad LED1/R33/C86 lanes; new IO/U10 entries centred | Independent on-axis trial reproduces IMU keep-out and 11 loose SCK samples; retain measured residuals |
| R9-RTE-06 | Minor, carried | SERVO2 slow tail0.42 mm over split; LOGIC_SOURCE_ST crosses near(33.65,57.70)–(33.8,58.01) | Retain slow routes; a plane redraw requires power/return requalification |
| R9-RTE-07 | Minor, carried | BUZZ_DRV 36.376450 mm/3 vias; Y1 foreign projections BUZZ_DRV 2.732695/NRST 0.777648 mm | Simple swaps independently collide with named copper; solid In1GND intervenes; HSE stimulation remains bench work |

Fresh evidence includes all 100 U1 pins /25 AF assignments; four hashes / exact in-memory binding regeneration;
101 safety pins across 41 parts; 65536 passive corner/state solves; independent hot-plug descriptor-MNA control
and four refined worst corners; all 82 exact live supplier identities; independent 203 supplier-pad CPL
reconstructions plus 12 nonpolar placement-only rows; fit /plate /seven mechanical rules; native all-severity
DRC / unconnected /parity /ERC0/ 0/ 0/ 0; paste 317F/365B; current five-output manifest. No firmware or physical claim.

Routing independently reproduces82 counted instances, no failures/allowlist/stale/leftovers/removable bumps;
110625 reference samples with 7139 own-antipad and 7 samples matched by6 exact strays, zero loose; K-region
57 items / 21777 samples; all 22 fast signal transitions have GND partners≤1.491643 mm. AVA photographs support only
visible floorplan/routing inspiration. Supplier23:51:13Z confirms$84.43 vs $84.41,46 Extended and onlyR430/U4 short.

Rounds9 and 10 are the required consecutive clean pair under the owner's continuation. After this review, only
low-risk gate/regression and record/generator-text fixes are applied. The PCB is frozen at `b337fe63…`; no land,
part, pose, net, track, via, plane or silkscreen changes follow. The binding note's PA6 obligation is regenerated
from the corrected source; its four CAD/input hashes stay the same. Final rebuild/check evidence follows below.

### Round 10 final fix validation (2026-10-28 local date)

Both fresh complete final builds exit 0 and reproduce **all 21 generated CAD / binding files byte for byte**.
The PCB remains **`b337fe63c258c85ba4120e75ad018afa0c22241f8bc21a4172787cf2887208d9`**, 46 × 90 mm,
2,366,509 bytes. Relative to reviewed `619db7e`, the only changed generated file is the binding note: one PA6
limit obligation, with all four CAD/input hashes unchanged. No part, pin, land, pose, copper, plane or silk change.

Final **unskipped `tools/check.sh` exits 0**: DRC / unconnected / parity / ERC **0 / 0 / 0 / 0**, all 33 R10 rules,
metadata / 3D, silk, fit / plate, routing, actuator and current **five-output fab manifest pass**. Self-tests:
shell 4, procurement 19, fit 24, paste 5, route 59, R10 **143**; three NumPy cases pass separately, **no unresolved
skip**. Both builds freshly pass the 2304-case hot-plug sweep / refinement / cold / local checks (simulation /
Inference). Routing remains 0 failing / 0 allowlisted / 0 leftovers; 215 CPL / 82 BOM codes, paste 317 F / 365 B,
unchanged package inputs. Actual cost / stock still fail at $84.43 vs $84.41 with R430 / U4 short; no procurement
or physical release is claimed.

Evidence: `m3_design/assembly_review/sources/r10_review/round10_fix_validation.json` and `round10_fix_check.txt`;
independent reviews, selected seed/geometry evidence and complete reconciliation: `round10_reviews.json`,
`round10_evidence.json`, `round10_deviations.json`. The final consistency follow-up found no new review finding;
its stale-status/current-USB-range/readability/test-count corrections are included. AGENTS §2 is byte-unchanged.
The completed deviation list below remains pending owner acceptance; no ordering/push/other-worktree edit.

## Round11: full AVA-board review (2026-10-29)

Target: committed`21bc3b2`, PCB SHA-256
`0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`,46×90mm,
2,245,484bytes,209footprints/981straightsegments/294vias/1818.769511mm track.
Ten independent lenses ran in batches of at most three, without reading each
other's current-round reports. Native CAD remained byte-unchanged throughout
review. The terminal Major received a separate fresh verifier. The source-fix/decision index is
`sources/r10_review/round11_reconciliation.json` (all107 decisions; not final acceptance). Consolidated
result: **0 Critical,1 confirmed Major,16 Minor groups. Consecutive-clean count0.**

| Lens | Reported Critical/Major/Minor | Evidence under`sources/r10_review/` |
|---|---|---|
| Requirements/all owner decisions | 0/0/3 | `round11_requirements.md` |
| Safety/AGENTS§2 | 0/0/1 | `round11_safety.md` |
| Power/electrical | 0/0/1 | `round11_power.md`,`.json` |
| Parts/BOM/lands/stock/orientation | 0/1/1 | `round11_parts.md`,`.json` |
| MCU/pins/back-feed/ESD | 0/0/2 | `round11_mcu.md`,`.json` |
| Placement/mechanics | 0/0/3 | `round11_mechanics.md`,`.json` |
| Routing/AVA/planes/returns | 0/0/4 | `round11_routing.md`,`.json` |
| Manufacturing/silk/fab | 0/0/2 | `round11_manufacturing.md`,`.json` |
| Gate adversary | 0/0/3 | `round11_gate.md`,`.json` |
| Docs/firmware binding | 0/0/2 | `round11_docs_binding.md`,`.json` |
| Fresh Major verifier (not an eleventh lens) | 0/1/0 | `round11_terminal_verification.md` |

### Confirmed Major

**R11-BOM-01, also R11-MEC-01:** DORABO T0-1 p1 permits a wire face4.00mm
from the pin row: maximum depth7.70 minus minimum rear datum3.70. The generated
model used3.65mm. Correcting the full asymmetric envelope gives4.603012mm wire
room at all seven terminals versus the accepted4.95mm floor. The fresh verifier
confirmed an acceptance-bound Major, not an observed physical collision. Keep
the floor: correct the models/courtyards, move each row inward0.40mm, clear local
neighbours and redraw affected routes through the generators (D-R11-01).
The generator fix, DRC/fit/hot-plug/fab/binding and 42-file reproducibility
now pass; see the fix-validation receipt below. Fresh full review rounds remain
required. AGENTS §2 is unchanged.

### Consolidated Minor ledger

| ID | Source findings | Concrete disposition |
|---|---|---|
| R11-m01 | REQ-01,PWR-01,DOC-01; SAF-01 fire portion | Bind fire-copper calculation to native paths; refresh final hot-plug/output-path/U9 ladder records (D-R11-03). Old IGN4.85mm is actually10.396068mm on this target. Conditional firing margin remains above1.125A. |
| R11-m02 | REQ-02,DOC-02; BOM-02 | Correct active parked-radio/future-AVA/GH/header wording and J9 pin3 boardRX/pin4 boardTX. |
| R11-m03 | REQ-03 | Parent VEHICLE still describes older connectors. Record the in-worktree handoff; leave the separately owned worktree untouched. |
| R11-m04 | SAF-01 assembly portion,MEC-02,DOC-02 retention portion | Refresh coating/probes/staking/hardware worksheet; TP121 is bottom(10.5,71.5), retained ARMbank reachesx28.86, all seven DB125s require retention. |
| R11-m05 | MCU-01 | Scope translator ESD rationale to camera; GPS/radio are direct1k/ESD and installed survival remains unqualified. |
| R11-m06 | MCU-02 | Correct seven Rev11 AF citations to Table10 and PC1 analog reset wording; regenerate binding provenance without changing pins. |
| R11-m07 | MEC-03 | Require board removal from continuous sled or a qualified access window before opening bottom SD hinge. |
| R11-m08 | RTE-01 | Redraw four proved bumps and two checked monotone shortcuts through generator tables; full DRC still required. |
| R11-m09 | RTE-02 | Retain measured C98 remote-return deviation pending a fully checked local path:13.497mm pad-to-stitch/31.812mm diagnostic device loop. No transient failure demonstrated. |
| R11-m10 | RTE-03 (carried) | Record actual NRST/BOOT0/I2C noncritical companion gaps; maximum3.679674mm at NRST(14.2,37.3). No scope expansion. |
| R11-m11 | RTE-04 (carried) | Record actual IMU0.05mm entry offset, four between-pad routes and current pad-edge entries; no open circuit demonstrated. |
| R11-m12 | MFG-01 | Set explicit thermals on all five terminal GND contacts, including four currently solid on In1; refill/DRC/hole-fill qualification. |
| R11-m13 | MFG-02 | Move J122 Fab reference clear of centre drill and regenerate drawing/package. |
| R11-m14 | GATE-01 | Validate individual text/textbox/footprint terminal words against their exact nearest pin, including+/− and duplicates; preserve AUD-10 scope. |
| R11-m15 | GATE-02 | Extend existing final required-fitted invariant to all199 reviewed functional parts/support; add native DNP/list omission regressions. |
| R11-m16 | GATE-03 | Reject nonfinite/nonpositive/degenerate model transforms/envelopes in fit and P-11; seed invalid and valid conversion cases. |

Reported duplicates are counted once in this ledger; the mechanics lens's
terminal Minor is consolidated into the freshly confirmed Major. All remaining
architecture/process/qualification deviations from older rounds need a new
current-board inventory after fixes, rather than automatic credit from round10.

### Round 11 fix validation

The supervisor withdrew its build service on 2026-10-29. Direct native builds
use the verified official KiCad 10.0.7 CLI to avoid the upstream 10.0.6 headless
DRC failure (D-R11-05); generators use the project's KiCad 10.0.6 Python API.
All native-board DRCs use the unmodified vendor CLI; shell regression fixtures
stub external commands only to test failure handling. No real-board gate is skipped. Stale supervisor build
files are ignored. Commits still use the supervisor request service.

Two complete `m3_design/r10_build.sh` runs exit 0 on PCB
`0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`: 46 × 90 mm, 2,263,730 bytes,
209 footprints / 973 segments / 295 vias (167 GND) / 1809.708732 mm track.
All **42** recorded generated CAD, library/model, native-budget, hot-plug and
binding files match byte for byte. Each build includes the unskipped full gate:
DRC / unconnected / parity / ERC **0 / 0 / 0 / 0**, metadata/models, silk, fit,
all **31** R10 rules, route hygiene and current five-output fab manifest pass.
Gate suites pass; the two NumPy numerical cases and optional plate regression
were also run successfully, resolving all three native-interpreter skips.

The earlier complete-board attempt (`419a8f49…`) had sixteen M-6 assembly
keep-outs and two camera K-region failures. Real regenerated courtyards also
exposed collisions missed by stale-cache position-only prototypes. The final
port/servo/core changes preserve the floors and allowlists; final native DRC,
M-6, K-region and routing all pass. The full implementation and reproducibility
receipt is `sources/r10_review/round11_fix_validation.json`;
`round11_m6_fix.*` and `round11_servo_fix.*` retain scoped prototype evidence.

The fresh final-target verifier closes R11-BOM-01 / R11-MEC-01:
all seven wire rooms **5.003011866 mm**, minimum repaired-part THT gap
**1.536 mm**, no terminal/body collision, 483 terminal/top-courtyard pairs
clear. See `round11_terminal_closure.*`. Three nonblocking bottom courtyard
graphics residuals and the longer C91 bypass remain measured review inventory.
No AGENTS §2 change occurred. The original round-11 result stays **0 Critical /
1 confirmed Major / 16 Minor groups** and earns **zero clean rounds**; fixes
are not a second full independent round.

Fresh actual-feed hot-plug gives **2304/2304 required cases** and 60 local
sensitivity cases passing (Simulation / Inference). The native-bound fire
budget, output loops and two-via U9 ladder are refreshed in `parts_qualification.md`.
The optional current plate diagnostic is **181.3 Hz** pinned D5, **70.3 g**
estimated mass, with **1.24 mm** modeled 100 g transverse deflection;
`round11_plate.json` states the assumptions. The old 280.9 Hz/45.5 g figures
belong to the earlier connector population. Fresh procurement evidence (`round11_procurement.json`, supplier 2026-10-30 05:00 UTC)
meets cost at $79.53/$84.41, or about $81.87 with minimum purchases and feeder share
before fixed/process/PCB/shipping. Stock fails: R430 17<3610 minimum, U4 0<5;
U9 minimum 7 versus 5 required. No quote or order is accepted. Physical and firmware
qualification, procurement/process acceptance and the final current deviation inventory remain open.

## Round 12: full independent review of committed `d57b216`

Target PCB `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`,46 x90 mm,2,263,730 bytes,
209 footprints/973 segments/295 vias. All ten fresh independent lenses finished
in batches of at most three without current-round report crossreading. The
canonical board and sources stayed unchanged throughout the full review.
**0 Critical /0 Major /12 consolidated Minor groups** (17 raw observations).
No C/M candidate required reclassification; no new C/M verifier was needed.
R9's precedents supply severity practice, not a literal rubric: a demonstrated
failure is distinguished from a prospective gap or disclosed pending qualification.
AGENTS section2 stays unchanged and blocking.

| Lens | Critical/Major/Minor | Report under `sources/r10_review/` |
|---|---|---|
| 1 requirements | 0/0/3 | `round12_requirements.md`, `.json` |
| 2 safety | 0/0/0 | `round12_safety.md`, `.json` |
| 3 power | 0/0/1 | `round12_power.md`, `.json` |
| 4 parts | 0/0/1 | `round12_parts.md`, `.json` |
| 5 mcu | 0/0/1 | `round12_mcu.md`, `.json` |
| 6 mechanics | 0/0/1 | `round12_mechanics.md`, `.json` |
| 7 routing | 0/0/4 | `round12_routing.md`, `.json` |
| 8 manufacturing | 0/0/1 | `round12_manufacturing.md`, `.json` |
| 9 gate | 0/0/3 | `round12_gate.md`, `.json` |
| 10 docs_binding | 0/0/2 | `round12_docs_binding.md`, `.json` |

### Consolidated round-12 ledger

| ID | Sources | Concrete disposition |
|---|---|---|
| R12-m01 | R12-REQ-01, R12-DOC-01 | **Active current-board records:** Correct current snapshots, pending-build wording and parallel old power/copper prose. |
| R12-m02 | R12-REQ-02, R12-MEC-01, R12-DOC-02 | **Parent vehicle mirror:** Retain separate-worktree mismatch with an exact in-worktree handoff; never edit parent worktree. |
| R12-m03 | R12-REQ-03, R12-RTE-04 | **M2 drawing, pad-entry and noncritical residuals:** One final inventory: nine count/location-only leftovers, actual entry/near-edge/between-pad measurements; overlapping inventory is counted once. |
| R12-m04 | R12-PWR-01, R12-RTE-02 | **C98 remote bypass return:** Try bounded temporary local stitches; adopt only a checked generator fix or retain31.812237mm diagnostic return with qualification. |
| R12-m05 | R12-BOM-01 | **L400 heel land:** Retain exact0.15mm possible uncovered heel strip for owner/assembler qualification; changing power land requires covered requalification. |
| R12-m06 | R12-MCU-01 | **PC14 current-bound evidence:** Withdraw2.9mA maximum; use resistor-only3.3mA nominal/3.363636mA corner and unmeasured dynamics, retain R1621k, refresh binding. |
| R12-m07 | R12-RTE-01 | **BAT_ENABLE removable bend:** Apply exact checked complete generator polyline;1.408326mm shorter without pad/via/layer change. |
| R12-m08 | R12-RTE-03 | **Noncritical return companions:** Retain actual NRST/BOOT0/I2C distances and reset/boot/interface qualification; no fast-rule scope expansion. |
| R12-m09 | R12-MFG-01 | **Five obscured Fab labels:** Apply checked five Fab-only0.4mm/0.06mm replacements/offsets, preserve1mm silk and vector-zoom readability limit. |
| R12-m10 | R12-GATE-01 | **Positive model shrinkage:** Validate reviewed normalized terminal/closed-SD envelope identity with positive-shrink and valid-unit-conversion seeds. |
| R12-m11 | R12-GATE-02 | **Connected foreign inner copper representations:** Extend K-inner over zones/drawings, preserving legitimate through-hole barrels; connected native seeds. |
| R12-m12 | R12-GATE-03 | **BOM quantity semantics:** Positive integer production BOM Qty equals distinct row designators; retain quantity-free CPL and test malformed/zero/mismatched quantities. |

Current native all-severity/all-track DRC/unconnected/parity/ERC is0/0/0/0,
with no ignored checks. Independent population, orientation, paste, manifest,
selected native contracts and numerical controls pass as scoped in each report.
The gate adversary performed378 probe executions; its three prospective gaps
were rejected at broader stale bindings, so no whole-gate escape is claimed.
The fresh06:11:29 UTC supplier snapshot gives$82.65 placed parts/feeder share,
$84.99 with minimum purchases (a$0.58 excess versus$84.41); R430/U4 stock and
the complete quote/process acceptance remain owner items. No order is inferred.

Round12 is clean for its exact reviewed PCB. Low-risk copper/Fab fixes will
change that PCB; the final same-board pair must therefore come from complete
fresh rounds13/14 on the committed result. R11/R12 geometry receipts and focused
C98 candidate work are not substituted for those rounds. Firmware, physical,
thermal/transient, harness/fit, assembly process and selected-lot firing remain
unverified. Reconciliation and report hashes: `round12_reconciliation.json`.

### Round12 completed integration fix pass

The generator fixes are rebuilt as PCB
`7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`,46x90mm,
2,264,839bytes;209 footprints/973 segments/296 vias/1808.300406mm track. Both
complete direct native builds exit0 and reproduce all42 recorded generated
files byte for byte. DRC/unconnected/parity/ERC0, all31 R10 rules, routing,
fit, orientation, paste, manifest and full gate pass. All171 R10 tests are
covered, with all three native NumPy skips separately resolved; fit29 and
routing60 pass. Final full-page/detail assembly rasters match the inspected
drawings exactly; exported binaries are separately manifest-bound.

Native multiset comparison proves all original part poses,pad lands/nets,GND
tracks and via geometry/flags unchanged. Three BAT_ENABLE segments change,
one ordinary C98 ground stitch is added, and five Fab text items change.
The complete native gate, geometry, return and bounded redraw screen are in
`sources/r10_review/round12_fix_native.json`; two-build/hash proof and all limits
are in `round12_fix_validation.json`. Source-level gate/Fab/routing receipts are
separate from full-round credit. All12 ledger dispositions above now have their
actual outcomes in `round12_reconciliation.json` and the complete inventory.

The R12 full review was clean on its original committed0ad board. These changes
require fresh full rounds13/14 on committed7355; no same-board pair is credited
yet. AGENTS section2 is byte-identical. Firmware, physical/bench/flight and
factory/process qualifications remain open; R10 is not accepted or ordered.

## Round 13: full independent review of committed `fa897c8`

PCB `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`,46x90mm,
2,264,839bytes;209 footprints/973 segments/296 vias. All ten fresh independent
lenses completed in batches of at most three. All63 frozen canonical files
remained byte-identical through the final handoff; no peer current-round reports
were read. Result: **0 Critical /0 Major /17 consolidated Minor groups**
(24 active raw findings;13 new/4 carried groups). Three closed historical MCU
findings are excluded. No C/M candidate required a fresh verifier.

| Lens | Critical/Major/Minor | Report under `sources/r10_review/` |
|---|---|---|
| 1 requirements | 0/0/4 | `round13_requirements.md`, `.json` |
| 2 safety | 0/0/1 | `round13_safety.md`, `.json` |
| 3 power | 0/0/2 | `round13_power.md`, `.json` |
| 4 parts | 0/0/2 | `round13_parts.md`, `.json` |
| 5 mcu | 0/0/1 | `round13_mcu.md`, `.json` |
| 6 mechanics | 0/0/2 | `round13_mechanics.md`, `.json` |
| 7 routing | 0/0/3 | `round13_routing.md`, `.json` |
| 8 manufacturing | 0/0/2 | `round13_manufacturing.md`, `.json` |
| 9 gate | 0/0/3 | `round13_gate.md`, `.json` |
| 10 docs_binding | 0/0/4 | `round13_docs_binding.md`, `.json` |

### Consolidated round-13 ledger

| ID | Source findings | Disposition |
|---|---|---|
| R13-m01 | R13-REQ-01, R13-SAF-01, R13-PWR-01, R13-DOC-01 | **O6 signal-reference wording:** Correct active motor-branch typo to signal-reference branches; retain conditional return-current qualification. |
| R13-m02 | R13-REQ-02 | **Current ledger states:** Replace stale PREPARATION/final-binding/107-index language with actual integrated receipts and a complete current decision index. |
| R13-m03 | R13-REQ-03, R13-MEC-02, R13-DOC-03 | **Parent vehicle mirror:** Retain separately owned mirror mismatch; current in-worktree handoff supplies exact seven-terminal, switch, SD and support facts. |
| R13-m04 | R13-REQ-04, R13-RTE-03 | **M2 routing inventory:** Re-extract complete final route partition and location-only noncritical leftovers; preserve measured entry/return and unqualified alternatives as deviations. |
| R13-m05 | R13-PWR-02 | **U9 current-limit tolerance:** Use R84 +/-0.35% inverse-R sensitivity:3.946188..4.856999A, headroom0.202391A; Calc/Inference, no transient qualification. |
| R13-m06 | R13-BOM-01, R13-MFG-02 | **L400 heel land:** Retain possible0.15mm uncovered heel for owner/assembler qualification; no unqualified power-land change. |
| R13-m07 | R13-BOM-02 | **SD nails/tolerances:** Generate15.05x15.70x2.10mm closed allocation including nails/tolerances; datum/card seating remain Inference. |
| R13-m08 | R13-MEC-01 | **DB125 tail coverage:** Allocate all23 tails separately using pad AABBs and3.8mm seating length; body-only models no longer overclaimed. |
| R13-m09 | R13-MCU-01 | **UART operating pulls:** Disable direct RX pulls throughout operation; relevant I/O supply+0.3V operating condition differs from4V absolute stress. |
| R13-m10 | R13-MFG-01 | **Fab reference intersections:** Correct77 actual border/dot/polarity collisions with fixed source overrides; preserve132 references and all non-reference objects; vector zoom remains. |
| R13-m11 | R13-RTE-01 | **Local signal detours:** Adopt CAM_RX_BUFFER and only additional native-qualified bounded same-layer sketches; exact adopted sources and preserved limits in routing-fix receipt. |
| R13-m12 | R13-RTE-02 | **Noncritical return companions:** Retain measured NRST/BOOT0/I2C companion distances and noise qualification; fast numeric rules unchanged. |
| R13-m13 | R13-GATE-01 | **Contradictory identity aliases:** Reject contradictory normalized extra MPN/LCSC identity fields; matching and blank aliases valid. |
| R13-m14 | R13-GATE-02 | **Cross-row BOM duplicates:** Reject repeated designators across rows while preserving production quantity and quantity-free CPL controls. |
| R13-m15 | R13-GATE-03 | **Paste geometry parity:** Compare actual aperture polygons to native paste geometry within1um, preserving real margins/split EP windows; no volume qualification. |
| R13-m16 | R13-DOC-02 | **Executable binding distinction:** R10 evidence JSON is board-bound provenance; executable binding and v0.8.1/diagnostics remain R1-bound. |
| R13-m17 | R13-DOC-04 | **Flight harness description:** Replace active obsolete M1.75 prose with current estimated Mach1.9; actual flight-load/harness qualification remains open. |

The independent manufacturing review ran native all-severity/parity DRC,
unconnected and ERC with zero findings. Selected contracts, actual BOM/CPL,
source/pin/axis facts, critical references and adversarial controls are scoped
in their reports. Three prospective gate gaps were rejected by broader stale
bindings; no whole-gate escape is claimed. Fresh supplier08:38:52.797802UTC
is$82.6458 placed/feeder share or$84.9862 with minimum purchases, before fixed/
process/PCB/shipping. R430/U4 supply and owner cost/process/deviation acceptance
remain open. Round13 is clean on7355 only. Its low-risk source fixes change
that PCB; complete fresh14/15 on the newly committed result must supply the
final same-board clean pair. Focused fix receipts are implementation evidence,
not extra full rounds. Full report hashes, source freeze and grouping are in
`round13_reconciliation.json`. AGENTS section2 is unchanged.

### Round13 completed integration fix pass

Generator result `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`,46x90x1.6mm,
2,259,597bytes;209footprints/966segments/296vias/1802.125220mm track. Two
complete native builds/check0 reproduce all42 recorded generated CAD,library,
model,budget,hot-plug and binding files byte for byte. Pads/nets,part poses,
vias,GND tracks,supports and axes are identical to7355. Twelve qualified same-
layer signal redraws save6.175186mm/seven segments;77 Fab references change.
Closed SD nails/tolerances and all23 terminal tails have explicit fit allocations.
The native all-severity/unconnected/parity/ERC result is0/0/0/0; all31 R10
rules,fit,routing,orientation,618 paste geometries and five-output manifest pass.

BuildA passes172 R10 tests with3 native NumPy skips. A subsequent optional-plate
bookkeeping correction excludes23 collision-only tail rows from already lumped
connector mass,with a new regression; it changes no CAD generator or any of the
42 reproduced artifacts. BuildB includes173tests with4 native NumPy skips;
the supplied interpreter resolves all4 cases. Fit30,paste11 and routing60 pass.
Current plate diagnostic181.3Hz/70.3g and C431 h4 gap0.274363mm are Inference,
not physical shock/mass qualification. Root and the focused Fab worker inspect
the complete pages/details; both builds' assembly rasters equal those drawings.
All original full-review reports remain immutable. Exact proof is
`round13_fix_native.json`, `round13_fix_validation.json` and `round13_plate.json`.

The current route inventory is140=110 ordinary+22AUD10+8noncritical leftovers,
54 all-net bump windows,zero blocking/allowed/stale findings. Slow AUD-2 has
11 observations(5runs,5pads,1chain),not11 distinct nets. Retained L400 heel,
noncritical return/entry/M2 compromises,physical/process/firmware and owner
cost/stock acceptance remain explicit deviations. Fresh complete14/15 must
review this newly committed result; no earlier clean pair transfers. AGENTS
section2 is byte-identical. R10 remains unaccepted and unordered.

## Round 14: full independent review of committed `f5e4a5a`

Target PCB `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`.
Ten full lenses ran in batches of at most3 with1879 preexisting tracked files
frozen throughout. Result:0Critical/0Major/14consolidatedMinor groups from20raw
observations (10new/4carried). Every original MD/JSON stays immutable; the
reconciliation embeds exact originals and source hashes. No C/M candidate
needed a fresh verifier. Routing disclosed unrelated probe-script lines from a
broad CLI lookup after its initial sketches; it did not read peer reports or use
those lines. This method limit remains explicit; fresh rounds use exact lookup.
The requirements report's663-XML-node label has a root erratum:651XML nodes/
unique mappings agree with663numbered physical pads after12duplicate fingers.
All100MCU pins match. These post-review errata do not inflate full-round totals.

Low-risk fixes adopt12 individually/combined-qualified local redraws, retire
only obsolete USB_DM reference information, close legacy-paste subset guards,
reject collision-only mass keys,use maker0.5g LS120 and correct operating/data/
ordering/inventory records.16courtyard stroke pairs,possible0.15mm L400 heel,
noncritical remote return companions,M2 compromises and stale parent mirror
retain measured owner/qualification dispositions. Decisions:D-R14-01..03.
Two complete source builds/check0 reproduce42 generated files on successor
`7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783` (2,257,812bytes,957segments/296vias),saving4.985043mm/nine segments.
DRC/unconnected/parity/ERC0,31rules,route/fit/legends/fab/note pass; actual-feed
2304required+60local simulation cases pass. Optional plate181.1Hz/
70.5g remains Inference. Gate/route/model old-fault and valid controls
are scoped in fix receipts. No safety limit or AGENTS section2 was weakened.
The changed PCB requires fresh full15/16 on its committed target; no clean pair
is yet credited. R10 remains unaccepted/unordered and physically/FW unqualified.
Evidence:`sources/r10_review/round14_reconciliation.json`,round14_fix_native,
round14_fix_validation,round14_routing_fix,round14_gate_fix,round14_root_fix and
round14_plate; exact paths are catalogued by the current deviation ledger.

## Round 15: full independent review of committed `789f4d5`

Target PCB `7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`.
Ten fresh full lenses ran in batches of at most3; all1909 preexisting tracked
files stayed byte-identical through the final handoff. Results:0Critical/
0Major/14consolidatedMinor groups from20raw observations(10new/4carried).
Original MD/JSON reports are immutable; reconciliation retains exact findings,
hashes and deduplication. Fresh focused verifiers checked DB125 insertion/S8
process allocation and VCAP combined-condition/ESR hypotheses; both remain
Minor qualification gaps,not demonstrated required-function failures.

| Lens | Critical / Major / Minor |
|---|---|
| Requirements |0/0/3|
| Safety |0/0/0|
| Power/electrical |0/0/2|
| Parts/BOM |0/0/2|
| MCU/signals |0/0/1|
| Placement/mechanics |0/0/3|
| Routing/AVA |0/0/2|
| Manufacturing |0/0/2|
| Gate adversary |0/0/3|
| Docs/firmware binding |0/0/2|

Eight groups are corrected:active records,UVLO temperature prose,IMU pad-row
joins,handoff plate gap,fifteen route windows,BOM identities,C84 model guard
and equal-area stale fills. Six remain explicit deviations:parent vehicle
mirror,M2/returns,L400 heel,DB125 process allocation,VCAP qualification and
courtyard stroke intersections. Decisions:D-R15-01..03; the complete ledger
maps all119D-* IDs and22owner-mandate records.

The root corrected window1's producer label from core to pyro without editing
the original report. An initial rectangular IMU escape failed four native GND
tiny-jog checks despite DRC0/unconnected0; it was rejected. Individual pad-axis/
45degree escapes to the unchanged vias pass without a rule waiver. Two probe
errors(SWIG identity representation and1nm coordinate rounding) were corrected
and disclosed; neither was a physical board defect.

Two complete source builds/check0 reproduce42 generated files on successor
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`,
2,256,162bytes,951segments/296vias. Fifteen route windows save10.008727mm/
eight segments; IMU escapes deliberately add1.544214mm/two segments,combined
8.464513mm/six fewer. Pads,poses,identities,models,vias and zone outlines match
exactly; native output equals the source dry draw. DRC/unconnected/parity/ERC0,
31rules and fabrication checks pass. Native176R10/31fit/16paste/60route tests
pass; supplied NumPy resolves all four skips. Actual-feed2304required+60local
cases pass. Optional181.1Hz/70.5g plate results remain Inference. Original and
final assembly pages were inspected; regenerated build rasters match exactly.
No electrical,physical,firmware or complete MEMS stress qualification is implied.

Fresh complete16/17 must review this changed PCB after its supervisor commit;
no clean pair transfers. AGENTS section2 is byte-identical. R10 is unaccepted
and unordered. Evidence:round15_reconciliation,round15_root_fix,
round15_gate_fix,round15_qualification_fix,round15_terminal_verification,
round15_vcap_verification,round15_fix_native,round15_plate and
round15_fix_validation under`sources/r10_review/`.

## Round 16: full independent review of committed `b1b8658`

Target PCB `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
Ten fresh full lenses ran in batches of at most3; all1942preexisting tracked
files remained byte-identical through final handoff. Result:0Critical/0Major/
11consolidatedMinor groups,17raw observations,5new/6carried. Exact original
MD/JSON reports remain immutable. No unresolved Critical/Major candidate was
reclassified or deferred; rejected hypotheses and execution limits remain in
the authored evidence. Engineering prototypes do not supply full-round credit.

| Lens | Critical / Major / Minor |
|---|---|
| Requirements |0/0/3|
| Safety |0/0/0|
| Power/electrical |0/0/1|
| Parts/BOM |0/0/2|
| MCU/signals |0/0/1|
| Placement/mechanics |0/0/2|
| Routing/AVA |0/0/2|
| Manufacturing |0/0/2|
| Gate adversary |0/0/2|
| Docs/firmware binding |0/0/2|

Three groups are corrected:the stale active plan header,saved binding evidence
validation and collateral topology failures from exact duplicate tracks. A
complete copied-project gate genuinely accepted only-corrupted binding evidence;
the canonical note was correct. New native-derived K-binding rejects missing/
malformed/hash/pin/axis differences without rewriting the saved file. Generation
moves before the full build gate. R10 exact net/layer/native-endpoints/width
track duplicates now have one topology representation while their review count
remains. Partial overlaps,different widths,crossings,genuine loops and legacy
profile behavior remain blocking. Native tests exercise complete scan/evaluate.

Eight groups remain retained:parent VEHICLE mirror,M2/returns,L400
heel,DB125 process allocation,VCAP combined-condition/ESR,MEMS signal/supply
stress guidance,SD_MOSIcleanup and courtyard ink. The qualified SD copy saves
1.994603mm/two segments; exact native source precision is proved separately.
The new supervisor steer/D-R16-03 supersedes the queued adoption policy and
forbids PCB,placement,routing and circuit-generator changes for Minors. Keep
this measured SD cleanup as an explicit M2 deviation. If full R17 is also0C0M,
finalize records,commit and report without any later Minor CAD change. Only
confirmed Critical/Major permits a board change. The bounded MEMS recipe is rejected for a45degree free CS junction;
its first supply attempt also violates clearance. Current geometry is retained
with its actual guidance departure and first-article qualification obligation.

One new complete native source build/check0 reproduces the same PCB and all42
recorded generated files against both R15 builds. Standalone check0 passes
DRC/unconnected/parity/ERC0,all32rules and the current five-output fab manifest.
Native180R10/31fit/16paste/67route tests pass; all four NumPy skips separately
pass. Hot-plug2304required+60local cases pass again. The optional plate result
is the prior same-PCB calculation,not a new run. No physical or firmware
qualification follows. The exact15:30supplier snapshot is rebound with its
original query times:79.5232USDplaced/81.3254USDminimums; R430/U4still short.

No native CAD file changed after the full review; AGENTS section2 is exact.
Fresh full17 remains required. The current ledger maps122DIDs through D-R16-03 and23
owner mandates; the full R16 target historically contained119DIDs/22scopes. Evidence:round16_reconciliation,round16_gate_fix,
round16_minor_prototypes and round16_fix_validation under`sources/r10_review/`.

## Round 17: full independent review of committed `ac483f4`

Target commit `ac483f40d38db6e0424227bd32d2a5d5f9f60c3e`, PCB
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
Ten fresh full independent lenses ran in batches of at most3, with all1,966
preexisting tracked files frozen through the last immutable handoff. Result:
**0 Critical / 0 Major / 13 consolidated Minor groups**, from23 raw observations
(4 new groups,9 carried). No C/M candidate remained requiring a fresh verifier.
The original scope was122 D-* decisions and23 owner mandates. The final four
record/check amendments do not rewrite that historical review scope.

| Lens | Critical / Major / Minor | Original report under `sources/r10_review/` |
|---|---|---|
| requirements | 0 / 0 / 4 | `round17_requirements.md`, `.json` |
| safety | 0 / 0 / 0 | `round17_safety.md`, `.json` |
| power | 0 / 0 / 2 | `round17_power.md`, `.json` |
| parts | 0 / 0 / 4 | `round17_parts.md`, `.json` |
| mcu | 0 / 0 / 2 | `round17_mcu.md`, `.json` |
| mechanics | 0 / 0 / 4 | `round17_mechanics.md`, `.json` |
| routing | 0 / 0 / 3 | `round17_routing.md`, `.json` |
| manufacturing | 0 / 0 / 2 | `round17_manufacturing.md`, `.json` |
| gate | 0 / 0 / 1 | `round17_gate.md`, `.json` |
| docs_binding | 0 / 0 / 1 | `round17_docs_binding.md`, `.json` |

| Group | Original findings | Disposition / measured reason |
|---|---|---|
| R17-m01 | R17-REQ-01, R17-MEC-02, R17-DOC-01 | **Separately owned vehicle mirror:** Retain the explicit local vehicle handoff; the parent candidate still names removed GH/ARM hardware. Update only through its separately authorized workflow. |
| R17-m02 | R17-REQ-02, R17-RTE-02 | **M2 drawing, pad-entry and return compromises:** Retain the exact140-item route inventory and sole6-row noncritical location list; all blocking native rules pass. Owner acceptance and physical noise/interface qualification remain due. |
| R17-m03 | R17-REQ-03, R17-PWR-01, R17-BOM-01, R17-MFG-01 | **L400 heel-land departure:** Retain native1.8x2.5mm at+/-2.35 versus maker2.0x1.8 at+/-2.25; conditional0.15mm uncovered heel requires owner/assembler first article. No Minor CAD change. |
| R17-m04 | R17-REQ-04, R17-MEC-01, R17-RTE-03 | **MEMS component-side signal and supply guidance:** Retain measured CS0.760+0.091923882mm and MISO/INT1/3V3A0.325mm under-body portions and0.20/0.25mm width departure. Rejected sketches supply no qualification; first-article bias/temperature/vibration remains. |
| R17-m05 | R17-PWR-02 | **Common-corner pad-energy worksheet:** Supersede active mixed-basis capacity examples using explicit current-board duty/load/efficiency/voltage arithmetic and complete motor/flight/recovery charge formula. Preserve dated D-CIR-02 history. |
| R17-m06 | R17-BOM-02 | **DB125 insertion and fabricated S8 allocation:** Retain23 nominal contact/drill allocations and nominalS8minimum1.102501576mm; maker/fabricator tolerance allocation and first-article insertion/solder fill remain unqualified. No blind drill enlargement or CAD change. |
| R17-m07 | R17-BOM-03, R17-MCU-01 | **VCAP combined operating C/ESR:** Retain exact2.2uF16VX5R10% C19/C20 nominal selection; establish ST conditions and supported combined C/ESR or qualify actual modes/process/aging/temperature. No unqualified larger-cap substitution. |
| R17-m08 | R17-BOM-04 | **Exact-code stock release:** Rebind original17:15 supplier snapshot:79.5232USDplaced/81.8636USDminimums before exclusions. R43017<3610/U4zero<5 stock blocks; U9stock83/min7 adds minimum uplift. Owner quote/process/cost acceptance remains. |
| R17-m09 | R17-MCU-02 | **BOOT0 and boot-address assumption:** Correct PA2/checker wording: BOOT0 low selects BOOT_ADD0, which can enter ROM at0x1FF0. Require intended user-flash boot configuration readback and reset-entry acceptance; refresh text-only table/binding provenance, with unchanged pins/axes. |
| R17-m10 | R17-MEC-03, R17-MFG-02 | **Courtyard graphic residuals and stroke metric:** Correct active penetration to actual0.050mm half-stroke sum minus polygon gap:0.010..0.040mm. Retain all16 separate-polygon graphic pairs and minimum nominal body gap0.499938mm for owner/assembler first article; no placement/CAD change. |
| R17-m11 | R17-MEC-04 | **U5 model-height source attribution:** Label1.1mm as conservative engineering model/cover allocation; TE maker package height is1.0mm+0/-0.10. Preserve model and2.9mm cover gap; actual seating/foam/venting remain unqualified. |
| R17-m12 | R17-RTE-01 | **SD_MOSI fixed-anchor cleanup:** Retain the disclosed1.994602820mm/two-segment avoidable turn. D-R16-03 cancels adoption; no PCB/routing/circuit-generator change for Minors. |
| R17-m13 | R17-GATE-01 | **Absent canonical fabrication manifest:** Require and verify the manifest for canonical full checks even when absent; preserve explicit build phase and external-copy semantics. Add missing-file regression and real native negative. Actual target package remains correct. |

Fresh evidence includes651 native pad pairs/100 MCU assignments, all32 contract
rules,187 reconstructed+12 placement-only orientations,618 paste geometries,
all44 fitted land patterns,199 relative models and14 date-normalized CAM members.
Both complete assembly pages and600dpi details were inspected. Nominal S8 minimum
is1.102501576mm; all23 terminal contacts and five4-spoke GND thermals are checked.
The routing scan matches all951 segments/296 vias to sources, with140 review
annotations and6 noncritical location rows;67 routing regressions pass. The
independent routing all-severity/parity DRC is0/0/0. These are CAD/source checks.

The genuine gate positive exits0 and checks five manifest outputs. Deleting only
the copied canonical manifest also exits0, establishing R17-GATE-01's prospective
checker gap; the actual target package is correct. The closing fix requires the
canonical manifest, preserving explicit build-stage and external-copy behavior.
Its real missing-manifest negative and final canonical positive are recorded in
round17_gate_fix and round17_fix_validation, without fabricating whole-gate credit
from focused controls. The four native NumPy cases are separately resolved.

R17-PWR-02 replaces mixed-basis active sizing with the explicit pad worksheet.
At allocated6V/80%, the current upper loads and0/0.5/2h camera duty over2h use
1.812657/2.390393/4.123602Ah of board charge. Board-only capacity leaving20%
unused is2.265821/2.987991/5.154503Ah; add motor,flight and recovery charge before
selection and independently satisfy fire-time source reserve and real bay fit.
Camera stays off on the pad unless recording. These unmeasured allocations do
not qualify a chosen pack. R17-MCU-02 corrects BOOT0/BOOT_ADD0 wording and adds
future programming readback; only the table-text provenance hash changes in the
native record. U5's1.1mm height is an engineering allocation, while TE specifies
1.0mm+0/-0.10. Courtyard graphic penetration uses actual0.050mm combined half-
strokes, correcting prior active values without moving any component.

Full R16 onb1b8658 and full R17 onac483f4 are two consecutive clean rounds on
the identical committed PCB. No native CAD or circuit/layout generator changes
follow the pair. Four record/check groups close, one carried graphic metric is
corrected, and nine measured groups remain owner-acceptance deviations. All20
original reports, source hashes and exact raw finding/group pointers remain in
round17_reconciliation and the complete final ledger. AGENTS section2 is exact.
No physical/firmware qualification, owner acceptance or order follows.

## Round 18: first Claude review of committed `dcbb6c8`

Target commit `dcbb6c8f040b7012f78934e1caf1b401db84d356`, PCB `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`. The PCB hash was the same
before and after in all ten reports. Ten independent lenses ran, one report each (`.md` and `.json` under `sources/r10_review/`). Result:
**0 Critical / 0 Major / 68 Minor raw observations** (57 new, 11 carried). Rounds 1 to 17 were all reviewed by one reviewer family; round 18 is the first
review by a different model family, so it is not part of the same-family clean pair of rounds 16 and 17. It found no inadvertent-fire path that needs fewer than two
independent faults.

| Lens | Critical / Major / Minor | New / carried | Original report under `sources/r10_review/` |
|---|---|---|---|
| requirements | 0 / 0 / 12 | 11 / 1 | `round18_requirements.md`, `.json` |
| safety | 0 / 0 / 6 | 6 / 0 | `round18_safety.md`, `.json` |
| power | 0 / 0 / 3 | 3 / 0 | `round18_power.md`, `.json` |
| parts | 0 / 0 / 4 | 0 / 4 | `round18_parts.md`, `.json` |
| mcu | 0 / 0 / 4 | 3 / 1 | `round18_mcu.md`, `.json` |
| mechanics | 0 / 0 / 4 | 3 / 1 | `round18_mechanics.md`, `.json` |
| routing | 0 / 0 / 6 | 3 / 3 | `round18_routing.md`, `.json` |
| manufacturing | 0 / 0 / 6 | 5 / 1 | `round18_manufacturing.md`, `.json` |
| gate | 0 / 0 / 9 | 9 / 0 | `round18_gate.md`, `.json` |
| docs_binding | 0 / 0 / 14 | 14 / 0 | `round18_docs_binding.md`, `.json` |
| **Total** | **0 / 0 / 68** | **57 / 11** | |

**How to read the dispositions.** "Fixed in the round 18 fix pass" means the change is made in this repository, in one of three lanes: *records* (documents, this pass), *board change* (the saved
PCB changes through the generators) or *check change* (gates and tools, each with a seeded regression test). The final board hash (`a3144b15…`), metrics and measurements of the board and check lanes are in M3_R10 "Current state" and `round18_fix_cad.md`
under `sources/r10_review/`; the decisions are `D-R18-…` in `R10_DECISIONS.md`. **Policy:** the Claude supervisor applied the round 18 Minors in CAD by supervisor decision, under the owner's standing instruction to decide from flight physics and AVA without asking; D-R16-03 (no board change for Minors) governed the R16/R17 pair only. "Records fixed" means only the text was wrong and is corrected. "Deviation" means the finding stays open, with the measured reason and
who must accept it (the owner decision table at the top of the next section). **The board changed (`632a9ad3…` → `a3144b15…`), so the R16/R17 clean pair does not carry to the new PCB** (REQUIREMENTS, R10 acceptance); rounds 19 and 20 are planned (the gate pass is done).

### Consolidated Minor groups

| Group | Original findings | What was found | Disposition |
|---|---|---|---|
| R18-m01 | R18-SAF-01, R18-GATE-01 | The two ACT_GATE vias, (16.2,73.3) and (11.8,70.725), have their barrel walls 0.2505 mm from In1 GND and from In2 RAW_PROTECTED; the BAT_ENABLE vias and the J400.2 ring are 0.2505–0.251 mm from RAW_PROTECTED. S-8 does not cover them (it exempts GND, which is the dangerous neighbour for a P-FET gate). One inner-layer defect or leak there can turn Q120/Q121 on with the switch open (RAW_ACT then follows BAT_IN); Q124 still blocks firing. | **Fixed in the round 18 fix pass** (D-R18-04; board change: fill-only keep-outs hold In1 and In2 copper 1.050 mm from the ACT_GATE barrels (the second via moved to (11.14,71.7)), from the BAT_ENABLE barrels on In2 and from the J400.2 hole. Barrel wall to foreign inner copper, before → after: ACT_GATE to In1 GND and In2 RAW_PROTECTED 0.251 → 1.050 mm; BAT_ENABLE to In2 RAW_PROTECTED / 3V3 0.251 → 1.050 mm, with In1 GND kept at 0.251 mm because a short to GND holds U9 off; J400.2 to In2 RAW_PROTECTED 0.551 → 1.050 mm and In2 GND 0.850 → 1.050 mm, with In1 GND kept at 0.551 mm. Check change: S-8 covers these seven nets with GND counted as foreign for ACT_GATE and ACT_DRV, and seeded tests fail on the old 0.251 mm geometry). The nominal margin over the 1.0 mm floor is 0.050 mm. |
| R18-m02 | R18-SAF-02 | Q121 (the forward-blocking FET) reaches its off-bias R120 and gate capacitor C120 only through two single vias and an F.Cu run; one open leaves its gate floating or drifting on (Inference for the floating case). | **Fixed in the round 18 fix pass** (D-R18-02; board change: Q121 has its own via-free gate–source resistor R119, 100 kΩ (C25741), on B.Cu at B(11.57,71.10); Q120 keeps R120 and the shared node sees R119 ∥ R120 = 50 kΩ, so any single via or track open leaves both gates biased off. TP121 moved from B(10.5,71.5) to B(4,70). Check change: the new S-3 sub-rule `local_gate_bias` requires it and fails on the old board). |
| R18-m03 | R18-MCU-01, R18-SAF-03 | R123 (100 kΩ) does not dominate a PC1 internal pull-up (30–50 kΩ): the Q122 gate would sit at 2.19–2.52 V, above its 1.45 V maximum threshold, and the bus would switch on. ACT_EN_MCU also runs 12.4 mm beside BAT_FAULT_N at 0.17–0.20 mm and passes 0.251 mm from the V3V3_SENSE via; a bridge there would enable the bus. After reset all GPIOs are analog with no pull, so AGENTS 2.4 holds. | **Fixed in the round 18 fix pass** (D-R18-01, D-R18-03; board change: R123 100 kΩ → 2 kΩ (C4109). Q122 gate with a 30 kΩ PC1 pull-up at 3.6 V 2.748 → 0.218 V (0.220 V as first written; corrected by R19-DOC-05), and with a BAT_FAULT_N bridge 2.97 → 0.554 V, both under the 0.65 V minimum threshold; with PC1 high the gate is 2.19 V (1.92 V at the VOH floor), and that Q122 saturates there is Inference (AO3400A RDS(on) is specified only at 2.5 V). ACT_EN_MCU re-spaced: to BAT_FAULT_N 0.171 → 0.550 mm, to BUZZ_OUT 0.400 → 0.520 mm, to the USB_LIMITED via 0.550 → 0.670 mm; the V3V3_SENSE via is gone with its net (m36). Still under 0.5 mm: ACT_EN to BAT_ENABLE 0.330 mm at R123.1 (a bridge loads U9's 470 kΩ-fed EN with 2 kΩ, so U9 stays off), the NRST via 0.425 mm, GND 0.251 mm (fail-safe) and the U1.15 / U1.17 pin pitch 0.200 mm). **Records fixed:** firmware rule never to enable a pull-up, RTC_TAMP3 or the wakeup function on PC1 (M3_R10, Firmware). |
| R18-m04 | R18-SAF-04 | The OUT sense branch runs 0.250 mm from R134.2 (RAW_ACT) and 0.175 mm from Q123.1, and the IGN track 0.222 mm from R131.1. A single surface bridge could bypass R134 (a fire command then becomes a near pack short of about 28 A, Calculation) or the e-match, undetected by the cold and powered readings. | **Fixed in the round 18 fix pass** (D-R18-05; board change: R173 (5.1 kΩ) moved to B(16.87,59.70) at the OUT end. OUT to R134.2 0.250 → 2.825 mm, OUT to Q123.1 0.175 → 1.577 mm, IGN to R131.1 0.222 → 0.575 mm). **Residual, measured:** the PYRO1_CONT_MID node behind R173 takes the corridor, 0.250 mm from R134.2 and 0.175 mm from Q123.1 (the 0.625 mm corridor cannot hold 0.5 mm to both pads). A RAW_ACT bridge to it passes at most 8.4 V / 5.1 kΩ = 1.6 mA (no R134 or e-match bypass) and raises the CONT reading to about 1.38 V against about 0.75 V intact, which a firmware upper bound can flag (Inference); a BUZZ_G bridge puts at most about 4.6 V on PC14 through R162 1 kΩ, inside the FT limit of VDD + 4 V. The OUT–GND approaches stay 0.177 and 0.180 mm (default-clearance class). |
| R18-m05 | R18-RTE-01, R18-PWR-01 | The In2 USB_LIMITED track (63.6 mm) and the 3V3A track cut the In2 3V3 fill into three pieces (1354.23, 63.11 and 30.54 mm²). The 63 mm² island feeds the 3V3A filter (U4, U5, VDDA), the buzzer and the cold pull-up through one 0.30 mm, 4.74 mm B.Cu link (32.83 mΩ); the finger carries U2's FB sense. No failure is shown (buzzer ripple at 3V3A about 1–2 mV, Calculation). | **Fixed in the round 18 fix pass** (D-R18-06; board change: the IN2_GND_CH1 tongue is removed and the In2 3V3 fill gains a shoulder and a bay round the USB_LIMITED via ends, so it is one piece of 1466.52 mm², was three; the narrowest fill necks are about 0.55 and 0.50 mm by polygon deflation, approximate. Check change: the new K-plane rule requires every non-GND inner power fill to be one piece, or each residual piece to have two links of at least 0.5 mm of outer copper, and it fails on the old board). |
| R18-m06 | R18-SAF-06 | After the on-rail checks the bus stays enabled, and nothing checks "IGN dead with the switch open" per flight, so a latent bus fault is seen only at first article or on the pad. | **Records fixed:** per-flight check in ORDERING 8.3 (J121.2 below 0.1 V, pack connected, J400 open, before the e-match goes in). **Deviation, owner decision:** whether firmware should return PC1 low after the pad check and re-enable it only on launch detection (M3_R10, Firmware); not adopted because it changes the accepted single-switch design. |
| R18-m07 | R18-MCU-02, R18-PWR-02 | On USB-only power the GPS and radio ports are off (U11 blocks reverse current), yet the binding obliges PC6 / PB13 to idle high: about 2.7 mA per TX line into an unpowered module, against u-blox guidance. The same applies during hold-up after the switch opens. Separately, the USB-only budget was undocumented: 1.4 W logic + 0.825 W SD writes would draw 0.4596–0.4856 A, above U10's 0.453 A maximum limit (bench mode only). | **Records fixed:** USB-only budget and bench rule (M3_R10 Power; ORDERING 8.3), firmware rule to park PC6 / PB13 while the ports are unpowered, wording "powered whenever the battery path is on" instead of "whenever the board is on". The binding note's "TX idle-high" obligation needs the qualifier "only while the ports are powered": a text change in the CAD-owned note. |
| R18-m08 | R18-MCU-03 | The PE4 record (net PYRO1_GATE_N, "as R7") reads active low; PE4 high turns Q124 on. | **Records fixed:** active-high, ODR low before output mode, GPIOE_LCKR, and the R126 / R127 / R128 / C126 contract in M3_R10, AGENTS and REQUIREMENTS. **Fixed in the round 18 fix pass** in the pin table and binding note text. The net rename waits for the next CAD change. |
| R18-m09 | R18-REQ-01, R18-REQ-02, R18-SAF-05 | Schematic notes are stale: the mcu sheet swaps the camera enable and fault pins and lists removed radio / loader pins and a removed footprint; battery_entry names a switch on J1.3--4 (the switch is J400) and R166 as 0.33 Ω (it is 0.36 Ω). The board is right. | **Fixed in the round 18 fix pass** (text-only edits in the schematic generators; no copper change). |
| R18-m10 | R18-MCU-04, R18-BOM-04 | C19 / C20 (VCAP, 2.2 µF X5R ±10 %) meet ST's nominal 2.2 µF ±20 % with ESR below 100 mΩ, but tolerance, temperature, bias and aging corners fall to about 1.52–1.68 µF (Inference, not maker curves). | **Deviation:** keep D-R15-02; bench-qualify, or adopt a reviewed X7R part whose maker curves bound at least 1.76 µF. |
| R18-m11 | R18-BOM-02 | DB125: 1.30 mm finished holes and 1.90 mm lands against the maker's 1.20 mm; S-8 fabrication allocation open. New evidence: the maker's pin is 0.50 × 0.85 mm (0.986 mm diagonal), which leaves at least 0.234 mm in JLC's 1.22 mm minimum finished hole, and the annular ring is at least 0.235 mm against JLC's 0.20 mm; the earlier 0.70 × 1.05 mm corner would not fit the maker's own 1.20 mm hole, so the parts reviewer does not treat it as a credible insertion failure (Inference). | **Deviation:** no CAD change. The fabricator's S-8 allocation (nominal minimum 1.050 mm at the load-switch gate and enable barrels, 1.103 mm at J121.1) and a first-article check of all 23 contacts for seating and solder fill remain. The reviewer proposes closing the insertion sub-item; it is kept as a first-article check. |
| R18-m12 | R18-BOM-03 | L400 (SRP5030T) uses a proxy land (1.8 × 2.5 mm pads at ±2.35 mm) instead of Bourns' 2.0 × 1.8 mm at ±2.25 mm; about 0.15 mm of the terminal heel can lie off the pad at worst tolerance. | **Fixed in the round 18 fix pass** (D-R18-08; board change: Bourns' SRP5030T recommended land, 2.0 × 1.8 mm pads at ±2.25 mm (2.50 mm gap, 6.50 mm overall), generated by `r10_parts.srp5030t()`; the JLC EasyEDA proxy residual goes 0.15 → 0.05 mm). |
| R18-m13 | R18-MFG-02 | U4's solder-mask webs are exactly 0.100 mm, with no margin to JLC's green-mask minimum. | **Fixed in the round 18 fix pass** (D-R18-08; board change: that footprint's mask expansion 0.025 → 0 mm, so the webs between its 0.35 mm lands go 0.100 → 0.150 mm; paste unchanged at 88.4 % of the land, inside TN1383's 70–90 %). |
| R18-m14 | R18-BOM-01, R18-REQ-11 | Stock still blocks release: R430 (C185349) 17 against a 3,610 minimum; U4 (C26633007) 0; U9 (C3662793) down to 78 in the parts reviewer's later live query, minimum 7. No JLC-stocked IMU meets both ±4000 dps and at least ±64 g. | R430: **fixed in the round 18 fix pass** (D-R18-09; board change: FOJAN FRC0603F2262TS C2999509, an exact 22.6 kΩ 1 % 0603 drop-in, 84,923 in stock, minimum 1). U9 has 45 in stock with a minimum of 1 in the run of 2026-10-30T23:50:54Z, so its 7-piece minimum is gone. **Deviation, owner action:** U4 still has 0 against 5 fitted; consign it with spares. |
| R18-m15 | R18-REQ-10, R18-MFG-06 | C84 is an ordinary SMT line in the JLC BOM and CPL although the order requires it absent from both reflows. | **Fixed in the round 18 fix pass** (D-R18-09: C84 stays on the schematic and board, and `export_fab.MANUAL_FIT` routes it to the owner BOM `fab/m3_bom_owner.csv` and out of the JLC BOM and CPL; JLC BOM 82 → 81 lines, CPL 199 → 197 rows; S-4 and `jlc_orient --verify-cpl` fail on a C84 row in the JLC upload; ORDERING 8.2 and REQUIREMENTS M1 state it). |
| R18-m16 | R18-MFG-01, R18-MFG-03 | No R10 tab plan existed (R9's Gerber spans lie beyond the 90 mm outline); the two filled-and-capped vias exist only as a free-text order request. | **Records fixed:** tab and rail plan table, and the VIPPO fallback, in ORDERING 8.1. |
| R18-m17 | R18-MFG-04 | All 158 visible silkscreen texts are at JLC's minimum, 1.0 mm high with 0.15 mm stroke (1 : 6.7 against the preferred 1 : 6). | **Deviation:** legibility only. If respun, use a 0.17 mm stroke on legends (not on designators crowded near pads). The gate lane now pins the 1.0 mm height and 0.15 mm stroke floors (R18-GATE-06). |
| R18-m18 | R18-GATE-02 to R18-GATE-09 | Gate gaps shown by seeded faults: K-width counts only 0.30 mm tracks (a U9 output path narrowed from 0.7 to 0.31 mm passes); no gate for power-path via count or the fire-current GND return; the fab manifest is bound before the S-4 / CPL / paste validators run, and a reversed D9 or a swapped R134 BOM code passes; the canonical board test is a string match and an unowned skip flag exists; the silkscreen text floors, the five support centres, the terminal word-legend association and the non-generated safety lands are not pinned. | **Fixed in the round 18 fix pass** (gate lane, checks only, PCB unchanged; D-R18-11; per-gap results in "Gate lane" below: GATE-02/-03 new rule K-power, GATE-04 the fab content checks gate the manifest, GATE-05 the repository board is recognised by identity and the skip flag is gone, GATE-06 silkscreen floors pinned, GATE-07 support centres pinned, GATE-08 word legends pinned, GATE-09 new rule K-lands; check_r10 has 35 rules). **Open Minors it leaves:** see "Gate lane". |
| R18-m19 | R18-RTE-04 | SD_MOSI keeps a 1.995 mm, two-segment dogleg; the redraw (20.1,32.8) to (25.005,27.894999) to (25.005,24.3) was qualified on a copy in round 16. | **Fixed in the round 18 fix pass** (D-R18-07; board change: the redraw through `r10_route_sd.py`; SD_MOSI 36.098 → 34.104 mm, 12 → 10 segments). |
| R18-m20 | R18-RTE-03 | Detours and extra vias outside the gate: the 114 non-pour nets total 1454.6 mm against an octilinear spanning-tree length of 1194.3 mm (1.218×); ten nets hold 136 mm of the 260 mm excess and 17 vias above need sit on 11 nets. | **Records fixed:** the per-net table is in deviation section 6. **Deviation:** most of the excess comes from placement and the pin map; AVA-level directness would need re-placement. |
| R18-m21 | R18-RTE-02 | 21 of the 25 required critical-signal layer changes move from an In1 GND reference to an In2 power rail (3V3 ×17, PORT_4V8 ×4); the nearest rail-to-GND capacitor is 1.29–6.19 mm away and 12 of the 21 are beyond 4 mm (13 by the same via-to-pad metric on `92c3ad59…` and `a0ec075e…`, CAM_MCU_RX at 4.02 mm; R26-TRI-08, §6). The In1–In2 sheet capacitance (about 3.8 pF/cm²) is too small to carry the return. | **Deviation:** a gate gap (nothing measures via-to-capacitor distance); not fixed now. A 100 nF 0402 3V3–GND at B(11.25,41.25) would bring the SD cluster to 2.3–3.4 mm in a respin. First-article SD and QSPI signal checks. |
| R18-m22 | R18-RTE-05 | The USB D+ and D− run uncoupled: 1.90 mm apart with a VBUS via and a GND via between them, trunks differing by 1.75 mm. Benign at full speed (Inference). | **Deviation:** not fixed now; in a respin move the two vias and route DP alongside DM at 0.4 mm. |
| R18-m23 | R18-RTE-06 | B.Cu runs under U4's body outside its lands: IMU_CS 0.760 + 0.092 mm, SPI1_MISO / IMU_INT1 / 3V3A 0.325 mm each (TN1383 stress guidance). | **Deviation** (carried): see deviation section 8; first-article bias, temperature and vibration qualification. |
| R18-m24 | R18-DOC-01, -02, -10, -11, -13, -14 | The same 48-line status block was pasted into six files; numbers were glued to words and units (about 1,500 tokens); the AGENTS table mixed R7 to R9 history with R10 facts; STATUS carried nine superseded bullets; the M3_R10 placement paragraph was a review changelog; "the pair is earned" did not say who reviewed. | **Records fixed:** the current state is stated once (M3_R10, "Current state") and the other files carry a short summary and a link; superseded interim-board records moved to M3_R10 "Board history"; current-state text respaced and broken into short sentences or tables; the clean-pair sentence now names the reviewer family. |
| R18-m25 | R18-REQ-03, R18-DOC-12, R18-PWR-03 | Removed hardware still described in current-looking rows: REQUIREMENTS (GH-4 ports, on-board RF in P1 and M1, the actuator rail, the R7 to R9 fuse and servo-containment clauses, R9 gate-spacing); ORDERING section 7 (ARM link with a 5 A fuse, 15 A battery fuse); parts_qualification.md (U410 / U420 / U411 / U421, R410 / R420, "two at LDO output", a 0.762 A shorted-port bound, a GH-era camera-loop split). | **Records fixed:** the rows are R10-only or marked R9 history; parts_qualification.md sections marked historical with the current budgets stated. |
| R18-m26 | R18-DOC-03, -04, -09 | The GPS / radio pin order omitted the board's perspective (a harness could swap TX and RX); J121 was "OUT / IGN" in the docs and "E1− / E1+" on the silkscreen; ARM1_SENSE reads like an ARM-link state. | **Records fixed** in AGENTS, the handoff terminal table, ORDERING 8.2, M3_R10 and REQUIREMENTS (board TXO drives the module RX; OUT = E1−, IGN = E1+; ARM1_SENSE is the bus sense, a name kept from R9). The matching pin-table note is a text change in the CAD-owned file. |
| R18-m27 | R18-DOC-05, R18-MFG-05 | The cost headline hid the all-in figure and the $84.41 target was never defined where it is used; AGENTS carried an older supplier time. | **Records fixed:** the target is defined (R3's cost per board, parts plus feeder fees) and the all-in table is in M3_R10 and ORDERING 8.1 (about $96–$99 per board on the current package before PCB, shipping and tax; $96–$102 on `632a9ad3…`). |
| R18-m28 | R18-DOC-06 | The deviation list had no list of decisions. | **Records fixed:** the owner decision table at the top of "R10 deviations for owner acceptance". |
| R18-m29 | R18-DOC-07 | ORDERING quoted a 1.705 Ah camera increment beside a table that gives 1.733 Ah for the same 1.5 h. | **Records fixed** (1.733 Ah on the table's 5.546 V basis; 1.705 Ah is the nominal 5.456 V case). |
| R18-m30 | R18-DOC-08 | The same facts are cited to different datasheet revisions (DS12110 Rev 10 / 11, AN2606 Rev 64 / 70). | **Records fixed** in the current documents (M3_R10 "Sources and datasheet revisions"); the binding note's Rev 10 cites are a text change in the CAD-owned file. |
| R18-m31 | R18-MEC-01 | The plate and strain evidence omits the east-edge terminals: the east column carries 34 g of 70.5 g on an unsupported 82 mm edge; the reviewer's run gives 1.2–1.4 millistrain at J410, J420, J9, C431 and J400 at 100 g, and C431 deflects 0.973 mm (Inference). | **Records fixed:** M3_R10 states the asymmetry. **Fixed in the round 18 fix pass** (gate lane: J410, J420, J9, J400, C431, C421 and C411 are in the plate tool's strain table; R150–R155, also named, are not: open Minor; the plate calculation was not re-run). **Deviation:** no east mid-span support; first-article vibration and shock check. |
| R18-m32 | R18-MEC-02, R18-MEC-03 | The (4,44.3) support's top hardware gate passes by 8 µm (LED2.2 GND 3.808 mm against 3.8 mm); the wire-room figure (5.003 mm) is to the bare bore while P2 names a 0.5 mm wall allowance. | **Records fixed:** nylon or insulated screws and washers at all five supports are now an explicit ORDERING and REQUIREMENTS line; wire room is defined (to the nominal Ø 50.8 mm wall at 5 mm height, allowance not subtracted) in P2 and M3_R10. **Fixed in the round 18 fix pass** (gate lane: `fit_check` prints and reports the wire room of all seven DB125 terminals, 5.003 to 5.603 mm). |
| R18-m33 | R18-MEC-04, R18-REQ-04 | The parent `../../docs/VEHICLE.md` stack row still describes GH ports, an ARM / IGN terminal pair on the x = 0 edge and a coax loop zone; the board-position arithmetic uses the coax-inclusive zone (conservative). | **Deviation:** separately owned; the handoff supplies the replacement text and terminal table. |
| R18-m34 | R18-REQ-05, R18-REQ-06, R18-REQ-09, R18-REQ-12 | Requirements without a recorded root: the pack size was stated three ways (and the pad-energy basis charges continuous SD writes and 1.4 W logic on the pad); P3's 5 × 100 g (500 g) retention; the microSD; F6's 0.15 s switch-bounce immunity. | **Records fixed:** one pack-size worksheet (ORDERING 8.1.1), no fixed pack capacity in REQUIREMENTS; P3 kept with its basis written (DESIGN_ASSURANCE 6.1: landing 92 to 367 g, GEVS 500 g, axial deployment pull; no ejection figure in VEHICLE.md); F5 states the card is an owner-chosen convenience log (about 2 MB per flight against 16 MB of QSPI); F6 relabels 0.15 s as inherited and adds a chatter test. **Deviation:** the conservative SD and logic allocations are kept because re-basing would reissue the sealed D-R17-01 numbers. |
| R18-m35 | R18-REQ-07 | Port UART nets are treated as fast interfaces by the GND-partner and one-reference-region rules, and dead RF classes (`rfif`, RADIO_SCK / MOSI / MISO, GNSS_) remain in the tools and in AGENTS section 3. | **Records fixed:** AGENTS section 3 and REQUIREMENTS M2 now say R10 has no RF, RADIO_* or GNSS_* nets. **Deviation:** moving the UART nets to the slow list is a gate-scope change (D-AUD-02 lists UARTs as fast) that the owner has not asked for; the existing vias stay. |
| R18-m36 | R18-REQ-08 | LEDs, buzzer and USB-C had no requirement ID; the buzzer sets the cold end of the temperature range; V3V3_SENSE (R62 / R63, PC3_C) divides the rail that is also the ADC reference, so it reads half scale whatever 3V3 is and duplicates VREFINT. | **Records fixed:** F11 added, temperature row restated, V3V3_SENSE redundancy recorded. **Fixed in the round 18 fix pass** (D-R18-01; board change: R62 and R63 removed and PC3_C NC; VREFINT and the VBAT/4 channel carry the information). |

### Confirmed by round 18

These checks passed on `632a9ad3…`, so they needed no action; they are recorded so the next review does not repeat them. They do not carry to `a3144b15…` unless re-measured; what changed is listed in [M3_R10.md, "What the round 18 fix pass changed"](M3_R10.md#board-history-superseded-interim-boards).

- **Documents.** The hash, size, byte count, footprint, segment, via, GND-via and track-length figures, the positions in AGENTS (J1, J400, J121, J9, J410, J420, J122, U1, U4, U5, U9, R166, LS120) and the five support holes, the IMU axis map, the 118 visible / 91 hidden references, 40 legends and 23 terminal pin legends, the cost and stock figures
  (79.52 / 81.8636, 82 codes, 46 Extended, R430 17 < 3610, U4 0 < 5, U9 83 with minimum 7), the BOM and CPL counts (82 codes; 199 rows = 67 top + 132 bottom = 187 reconstructed + 12 placement-only) and the fire-timing sums (32.653 + 0.2 + 0.5 + 1.5 = 34.853 ms; 35.797 W × 36 ms = 1.2887 J) all matched. The 126 decision IDs and 23 owner mandates match
  `r10_final_deviations.json`; all relative links in the six status files resolved; no inference was found written as fact.
- **MCU.** A fresh kicad-cli 10.0.7 netlist matches the native PCB on 651 / 651 pad nets; `pin_table.tsv` `r10_net` and the binding note agree on 100 / 100 pins; the symbol names match the datasheet pinout on 100 / 100 pins; all 32 NC pads are isolated; there is no back-feed into an unpowered MCU (PC7 and PB12 at 3.3 V with VDD = 0 are under the 4.0 V limit; leakage is at the µA level).
  The state recurs for tens of ms at every battery power-up because U11's 470 nF soft-start makes 3V3 lag PORT_4V8 (Inference), and stays within limits while a module's output high level is at most 3.6–4.0 V. PE4's gate inrush is at most 18.7 mA against 20 mA. Crystal: CL 8–10 pF against the 8 pF crystal and gm_crit 0.49–0.71 mA/V against 1.5 mA/V; the drive level could reach about 242 µW
  at worst-case ESR and swing, so add an OSC_IN amplitude check on the bench (Inference).
- **Power.** Recomputed: U9 UVLO 4.96 V, OVLO 9.77 V, ILIM 4.445 A, dV/dt 0.426 V/ms; U11 ILM 1.49 A and OV1 trip 5.76–6.27 V; regulator bands 5.367–5.546 V and 4.712–4.873 V; switch limits camera 1.041–1.250 A and USB 0.348–0.453 A; L400 Isat 4.3 A against a 3.1 A converter limit, and L1 rated 2.9 A against 3.1 A, which matters only at a fault; hold-up 0.490–0.571 ms.
  DC solves: every continuous neck is at least 1.0 mm with an IPC rise of at most 5.1 °C at 1.5 A. A new forward-polarity hot-plug sweep of all 2304 cases gives at most 13.796 V, 3.855 V/µs falling and 7.090 V/µs rising, inside TI's limits; reverse-polarity pin currents are EN 6.7 µA and OVLO 5.4 µA, under 10 µA.
- **Parts.** 209 symbols, 199 fitted parts, 82 rows and 651 pin-net nodes agree between schematic, board and BOM / CPL with 0 mismatches; the reviewer's own reconstruction of all 199 CPL rows puts every pad on our pad of the same number (R134 0.491 mm and LS120 0.45 mm differ only by land size; every other residual is at most 0.25 mm); the lands match their makers' drawings; R134 sees 35.8 W for 36 ms against about 46 W on the Bourns
  pulse curve (an interpolation, Inference); C128 is the only MLCC across the fire path and must stay unmerged.
- **Mechanics.** The IMU map is confirmed (+X = −x, +Y = −y, +Z = −z; roll = −gyro_Y; lever arm x = −6.0 mm). Bore fit with `fit_check` (radius 24.9 mm, tolerance 0.3 mm): worst margin J3 0.89 mm, DB125 bodies 2.98 mm, all 23 solder tails 7.56 mm; tail projection 2.20 mm leaves 1.80 mm to a 4 mm standoff plane. Plate model 181.1 Hz and 70.5 g reproduced.
- **Routing and manufacturing.** All 951 segments are octilinear; only 7 A-B-A jogs exceed the gate's thresholds (offsets 0.36–0.63 mm); every required critical layer change has a GND via within 1.5 mm (worst 1.492 mm). KiCad 10.0.7 DRC (all severities, schematic parity) 0 / 0 / 0; `route_check --profile r10` exits 0 with 140 information instances and 6 noncritical leftovers. The Gerbers regenerate identically and the manifest hashes match.
- **Gate.** The gate caught 14 seeded faults, three of them only incidentally: a pad moved in the placed footprint only, a 3V3 patch near the PYRO1_GATE barrel, a deleted GND partner via, silk over a pad, swapped PC1 / PE4 nets, a DNP pull-down, a narrowed fire path, a narrowed BAT_IN feed, a stale fab package, a wrong binding hash, a split In1 plane, a lowered rule severity, a moved support and swapped BAT / SWITCH legends. The gaps it missed are groups R18-m01 and R18-m18; both are closed in the round 18 fix pass (m01 by the CAD pass's S-8 and K-plane, m18 by the gate lane below).

### Gate lane (round 18 fix pass, checks only)

The gate lane closed the check gaps of group R18-m18 (R18-GATE-02 to -09) and the tool part of groups m31 and m32 (R18-MEC-01, R18-MEC-03). It changed `tools/check.sh`, `tools/check_r10.py`, `tools/fab_manifest.py`, `tools/export_fab.py`, `tools/fit_check.py`, `tools/plate_model.py`, `m3_design/r10_fab.sh` and their tests. **The PCB is unchanged** (`a3144b15…` before and after).
The fab package was rebound because two of those tools are manifest inputs: the BOM, owner BOM and CPL are byte-identical, and the Gerber zip changed in its creation dates only. Source: `round18_fix_gate.md` and `.json` under `sources/r10_review/`; decision D-R18-11.

| Gap | Finding | Check added or changed | Seeds that now fail |
|---|---|---|---|
| 1 | R18-GATE-05: the canonical board test is a string match and an unowned skip flag exists | `check.sh` recognises the repository board by device and inode; the `R10_SKIP_FAB_MANIFEST` branch is removed; a missing board fails before any stage | The canonical board through a symlinked folder, a `..` spelling and a case variant; the skip flag set to 1 or yes; a missing board path. The old `check.sh` fails 8 of the 10 new shell tests |
| 2 | R18-GATE-04: the manifest is bound before the S-4 / CPL / paste validators run; a reversed D9 or a swapped R134 BOM code passes | `export_fab.py` never writes the manifest; `fab_manifest.py --bind` runs S-4 on the BOM and CPL, `jlc_orient --verify-cpl` and the paste check, and writes the manifest only if all pass and nothing changed since the export; `r10_fab.sh` is export then bind; `check.sh` runs `fab_manifest.py --content` | D9's CPL row turned 180°; R134's BOM code C3013496 → C25744; B_Paste removed from the Gerber zip; an output or input edited after the export; a standalone export (no manifest, so `check.sh` fails); `check.sh` calling the verifier without `--content` |
| 3 | R18-GATE-02, -03: K-width counts only 0.30 mm tracks; no gate for power-path via count or the fire-current GND return | New rule K-power. U9 input (J1.1 to U9.5 through C88) floor 1.0 mm, U9 output (U9.6 to its In2 vias) floor 0.7 mm, with six exactly named narrow entries (stale ones fail); input at least one via of 1.0 / 0.5 mm, output at least two of 0.5 / 0.3 mm on the In2 RAW_PROTECTED fill; Q124 source pads 1 to 3 on tracks of at least 0.3 mm to at least two In1 GND vias of 0.5 / 0.3 mm. The input floor is S-9's 1.0 mm BAT_IN width, stricter than one 0.7 mm floor | U9 output 0.7 mm runs at 0.31 mm; U9 input 1.0 mm F.Cu runs at 0.31 mm; a C88-local run at 0.6 mm; output via (21.1,79.1) and its link removed; input via 0.5 / 0.3 mm; Q124 bar and stubs at 0.15 mm; a return via removed; synthetic cases (output vias with no In2 fill, a 0.2 mm drill, a feed that skips C88, a source pad on no return track, a stale named entry) |
| 4 | R18-GATE-06: the silkscreen text floors are not pinned | K-rules pins text height 1.0 mm, thickness 0.15 mm, silk clearance 0.15 mm and 2 resolved spokes | Each floor lowered (0.5 mm, 0.08 mm, 0.05 mm, 1 spoke) |
| 5 | R18-GATE-07: the five support centres are not pinned | M-3 pins the five Edge.Cuts circle centres to (4,4), (42,4), (4,44.3), (3.7,86) and (42,86) within 0.01 mm; any other circle fails | (4,44.3) moved to (3.5,46.8); (42,86) moved to (40,84) |
| 6 | R18-GATE-08: the terminal word-legend association is not pinned | K-legends: each of IGN, BAT, SWITCH, CAM, SWD, SERVO, GPS and RADIO exactly once and nearer its own connector's courtyard box than any other on its face by more than 0.01 mm; only named seams; a stale seam fails | BAT and IGN exchanged; BAT and SWITCH exchanged; GPS and RADIO exchanged; SWITCH removed; RADIO lifted 1 mm off its seam |
| 7 | R18-GATE-09: the non-generated safety lands are not pinned | New rule K-lands: the footprint library table is exactly `rocket` (`${KIPRJMOD}/kilib/rocket.pretty`); every board footprint is generated by `r10_parts` (9, checked by `r10_parts --check`) or pinned by SHA-256 (37 files); unpinned and stale entries fail | Q124's gate pad moved 0.08 mm in `M3_AON7524_DFN3x3A.kicad_mod`; an unpinned footprint (R0402); a stale pin; a second library |
| 8 | R18-MEC-01, -03: the strain table omits the east-edge parts; `fit_check` prints three terminals | `STRAIN_PARTS` gains J410, J420, J9, J400, C431, C421 and C411; `fit_check.wire_rooms()` prints and reports every DB125 terminal (key `wire_room_mm`): 5.003 to 5.603 mm on this board against the 4.95 mm floor | The old strain parts fail the strain test (NumPy); the old printout listed J1, J121 and J9 only |
| 9 | Not a review ID: `test_connector_mechanical_tabs_are_independently_checked` mutated R9's GH J9, which R10 does not have, and failed | Rewritten to shift J3's USB-C shell tabs (C165948 pads 1 and 2) and J430's microSD nails (C164170 pads 9 and 10); `test_fab_validation.py` now runs in `check.sh` (34 tests; it was 23 with one failing, outside the gate) | Shifted J3 tabs and J430 nails fail `--verify-cpl` and name the part |

Real-board measurements the new checks pin: U9 input 15 segments (1.0 / 0.7 / 0.3 mm) with the feed via (17.5,87.3) of 1.0 / 0.5 mm; U9 output 5 segments (0.7 / 0.4 / 0.3 mm) with vias (20.3,79.1) and (21.1,79.1) of 0.5 / 0.3 mm on the In2 fill; Q124 return 3 tracks of 0.3 mm to vias (15.85,57.695) and (15.85,58.345) of 0.5 / 0.3 mm.

**Counts.** These are the gate implementer's numbers from its two `tools/check.sh` runs; commit `1e60441` was made after them. The round 19 docs lens later reproduced check_r10 35 / 35 rules, route_check 0 failing, fit OK and the test counts by read-only runs on that commit, without running the full gate (R19-DOC-07). `tools/check.sh` exit 0 on the canonical tree, twice (the second after the last test edit): DRC 0 / unconnected 0 / parity 0 / ERC 0, audit OK, silkscreen 0, `r10_parts` current, fit OK, check_r10 **35 rules** (33 plus K-power and K-lands), route_check 0 failing, the three fab content checks and the six-output manifest.
Self-tests: shell 10 (was 7), procurement 20, fab_validation 34 (newly in the gate), fit 33 (was 31), paste 16, r10_parts 5, route 67, R10 201 (was 187; 5 NumPy skips under KiCad Python), NumPy HotplugNumerics and Plate 5 (was 2).

**Open Minors the gate lane leaves (no board change).**

| Open Minor | What it is | Closure |
|---|---|---|
| SWITCH is listed twice | `m3_design/r10_post.py` builds its word list from `WORD_LEGENDS_R10` plus its own `('J400', 'SWITCH')`, so SWITCH is not in `WORD_LEGENDS_R10`; adding it there would place it twice at the next build. The identity check uses `WORD_SUBJECTS_R10`, the list plus SWITCH | A generator-lane change that makes one list the source |
| The RADIO legend sits on the J410 / J420 seam | Its ink box is 0.000 mm from both courtyard boxes (the courtyards are 0.09 mm apart; by courtyard polygon or pad distance it is about 0.02 mm nearer J410). It heads J420 at its top-left corner as SERVO heads J122, so it is the one named `WORD_SEAMS` entry, accepted only while the tie holds. J430 (the bottom microSD under RADIO) is not ranked against top-side legends. BAT and SWITCH are 0.000 mm from their own terminal and 0.040 mm from the neighbouring west-edge one, so they clear the 0.01 mm tie threshold by only 0.030 mm | A legibility call for review |
| R150–R155 are not in `STRAIN_PARTS` | R18-MEC-01 also names these 0603 resistors beside J122 | Add them and re-run the plate model |
| No width floors for VLOGIC, PORT_5V3, CAM_5V, PORT_4V8 and 3V3 | The "other rails" of R18-GATE-02. There is also no real-board seed for a U9 output via without In2 fill (synthetic only) | Add floors with a measured basis, and the seed |
| The historic `m3_design/r8_fab.sh` and `r9_fab.sh` fail closed on this branch | They were not edited and now stop at their manifest check, because the export no longer binds | Use `r10_fab.sh`, or run the R8 and R9 flows from their own branches |

Status after round 19: the single word list and the RADIO seam are closed by the round 19 CAD lane (D-R19-06). The other rows are with the round 19 gate lane.

### Fix pass

The documentation lane of this pass restructured the record: the current state is in M3_R10 "Current state" and the other files link to it; the owner decision table opens the deviation list; and the stale R7 to R9 text in the current rows was removed or marked as history. The Claude supervisor applied the round 18 Minors in CAD by supervisor decision, under the owner's standing instruction to decide from flight physics and AVA without asking.
The board and generator lanes produced PCB `a3144b15…` (`round18_fix_cad.md`); the gate lane changed checks and the fab package only (`round18_fix_gate.md`, "Gate lane" above). Both are recorded in `R10_DECISIONS.md` (D-R18-01 … D-R18-11, 137 decision IDs in all). Rounds 1 to 17 and their original reports are unchanged.
**The changed board needs its own two consecutive clean reviews: rounds 19 and 20 are planned (the gate pass is done).**

## Round 19: second Claude review of committed `1e60441`

Target commit `1e60441` (the round 18 gate commit), PCB `a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918`. The power, routing and safety reports name commit `acba196`, the round 18 CAD commit; the PCB is the same in both.
The PCB hash was the same before and after in all ten reports. Ten Claude lenses ran, one report each (`.md` and `.json` under `sources/r10_review/`). Result: **0 Critical / 0 Major / 57 Minor** (41 new, 16 carried).
No lens found an inadvertent-fire path that needs fewer than two independent faults. Round 19 reviewed a different board from round 18, so the two rounds are not a same-board pair.

| Lens | Critical / Major / Minor | New / carried | Original report under `sources/r10_review/` |
|---|---|---|---|
| requirements | 0 / 0 / 10 | 5 / 5 | `round19_requirements.md`, `.json` |
| safety | 0 / 0 / 6 | 4 / 2 | `round19_safety.md`, `.json` |
| power | 0 / 0 / 1 | 1 / 0 | `round19_power.md`, `.json` |
| parts | 0 / 0 / 5 | 2 / 3 | `round19_parts.md`, `.json` |
| mcu | 0 / 0 / 5 | 4 / 1 | `round19_mcu.md`, `.json` |
| mechanics | 0 / 0 / 2 | 2 / 0 | `round19_mechanics.md`, `.json` |
| routing | 0 / 0 / 8 | 4 / 4 | `round19_routing.md`, `.json` |
| manufacturing | 0 / 0 / 4 | 4 / 0 | `round19_manufacturing.md`, `.json` |
| gate | 0 / 0 / 7 | 6 / 1 | `round19_gate.md`, `.json` |
| docs_binding | 0 / 0 / 9 | 9 / 0 | `round19_docs_binding.md`, `.json` |
| **Total** | **0 / 0 / 57** | **41 / 16** | |

**How to read the dispositions.** *Board fix* means the CAD lane changed the board through the generators; the decision is D-R19-NN in `R10_DECISIONS.md` and the measurements are in `round19_fix_cad.md`.
*Records fixed* means the text was wrong or missing and is now corrected (docs lane, `round19_fix_docs.md`). *Carried* means the finding stays open, with its reason, in the deviation list below. *Gate lane* means a check change, recorded by that lane.
The Claude supervisor applied the board fixes under the owner's standing instruction to decide from flight physics and AVA without asking. The AUX port is the one owner-approved addition.

### Round 19 dispositions

| Finding | What was found (short) | Disposition |
|---|---|---|
| R19-SAF-01 | S-8 exempted GND at the PYRO1_OUT barrels; the OUT via wall was 0.251 mm from In1 and In2 GND (OUT to GND bypasses Q124) | **Board fix** (D-R19-01): fill-only keep-outs; OUT via to In1 / In2 GND 0.251 → 1.021 mm, J121.1 0.551 → 1.050 mm; S-8 now counts GND at PYRO1_OUT |
| R19-SAF-02 | Four EN-node neighbours within 0.2–0.33 mm and the J400.2 lead can bypass or latch the switch; EN network uncoated; no per-flight switch-off step | **Board fix** for one pair (D-R19-02: BAT_ENABLE via to R134.2 0.300 → 0.500 mm). **Records fixed:** the other pairs and their leak thresholds in §1; coating list and the per-flight switch-off check in ORDERING 8.3 |
| R19-SAF-03 | TP121's 7.14 mm ACT_GATE stub doubled the GND-adjacent ACT_GATE copper | **Board fix** (D-R19-03): TP121 and its stub removed; probe ACT_GATE at R119.1 or R120.2 |
| R19-SAF-04 | §1 cited a stale 34-row surface inventory | **Records fixed:** §1 now carries the round 19 inventory (49 rows, minimum 0.173 mm) and the consequence of each pair |
| R19-SAF-05 | S-8 measures from the hole wall, not from the terminal's own inner ring | **Records fixed:** §1 and row 9 give both the wall and the ring figures from the CAD hand-back. **Carried:** ring figures 0.750 mm (J121.1 to GND, J400.2 to In2 GND) and 0.251 mm (J121.2, J400.2 to In1 GND); see §1 |
| R19-SAF-06 | Whether AGENTS §2.4 covers Q122, which had no gate–source capacitor | **Board fix** (D-R19-04): C123 10 nF gives Q122 the full §2.4 network (R122 1 kΩ series, R123 2 kΩ pull-down, C123). **Records fixed:** REQUIREMENTS F8 states the scope |
| R19-PWR-01 | Several power feeds change layer through one via; U11.2 is the only battery path into VLOGIC | **Board fix** for five feeds (D-R19-09). **Carried:** U11.2 RAW_PROTECTED and the two 3V3A feeds (no legal spot; measured reasons in §4); first-article pack-only power-up and C84 check in ORDERING 8.3 |
| R19-MCU-01 | The USB-only UART rule keyed on the inverted TPS2121 status polarity | **Records fixed** (D-R19-13, pin table and binding note; M3_R10 Firmware): UARTs enabled only while PA4 reads low (U11 on IN2, the battery); park analog when PA4 rises or PA6 trips |
| R19-MCU-02 | DS12110 cites mixed revisions | **Records fixed** (D-R19-13): all cites are Rev 8, rev V chapter |
| R19-MCU-03 | Two retained schematic notes contradicted the pin map (camera OE, sentinels) | **Board-source text fix** (D-R19-13): sheet notes corrected; netlist unchanged |
| R19-MCU-04 | No obligation kept VREFBUF disabled, with VREF+ tied to VDDA | **Records fixed** (D-R19-13): new binding-note obligation; M3_R10 Firmware |
| R19-MCU-05 | VCAP operating C and ESR unqualified | **Carried** (D-R15-02; owner table row 10) |
| R19-BOM-01 | U4 stock 0; a land-identical ISM6HG256XTR meets F1 / F2 | **Board fix** (D-R19-11): ISM6HG256XTR C51931514 fitted (9 in stock for 5, thin); LSM6DSV320X is the consigned alternate. The R18-m14 sentence is corrected in §10 |
| R19-BOM-02, R19-MFG-02 | C84's lands carried stencil paste although C84 is hand-fitted | **Board fix** (D-R19-07): no F.Paste on C84; S-4 fails paste on a hand-fit part |
| R19-BOM-03 | The temperature row named LS120 as the only part rated above −40 °C | **Records fixed:** REQUIREMENTS temperature row lists LS120, J430, LED1 and J3 |
| R19-BOM-04 | DB125 1.30 mm holes against the maker's 1.20 mm | **Carried** (§9; first-article check of all 27 contacts) |
| R19-BOM-05 | VCAP X5R ±10 % has no maker-bounded worst case | **Carried** (§9; owner table row 10) |
| R19-MFG-01, R19-GATE-06 | RADIO sat on the J410 / J420 seam | **Board fix** (D-R19-06): RADIO inside J420's span; one word list; `WORD_SEAMS` empty |
| R19-MFG-03 | ORDERING line 100 kept the old U4 mask values | **Records fixed:** ORDERING |
| R19-MFG-04, R19-MEC-01 | Pin legends under or at the edge of the DB125 bodies; wire-side legends hidden by wires | **Board fix** (D-R19-08, -12): every top legend outside every DB125 envelope. **Records fixed:** ORDERING 8.3 adds a harness pin-identity continuity check before first power |
| R19-MEC-02 | C84 hand-fit heats four bottom joints under its pads; R166 is 0.56 mm away | **Records fixed:** ORDERING 8.2 heat limit and re-inspection of L1, C7, C9 and R166. **Round 26 correction** (R26-TRI-11): five joints sit under the lands (L1.1, L1.2, C7.1, C7.2, C9.2), C9.1 is 0.545 mm away, and C8 (0.605 mm) is added to the fixture and inspection lists |
| R19-RTE-01 | A 1.693 mm² unstitched GND fragment at U1.19 | **Board fix** (D-R19-05) |
| R19-RTE-02 | TP121's stub missing from the owner's M2 list | **Board fix** (D-R19-03: removed) |
| R19-RTE-03 | BAT_FAULT_N's 0.18 / 0.38 mm via neighbours unrecorded; stale §6 table | **Records fixed:** §6 |
| R19-RTE-04 | Six 0603 resistors with a fanout via under the body | **Records fixed:** §6 owner M2 list. Respin item |
| R19-RTE-05 … -08 | Layer-change returns over In2 rails; placement detours; USB pair; copper under U4 | **Carried** (§6, §8) |
| R19-REQ-01 | The pad-energy worksheet stacks unrooted margins | **Records fixed:** ORDERING 8.1.1 states each margin's root or says it has none; the basis is an owner choice (owner table row 17) |
| R19-REQ-02 | C87 2.2 µF made recovery after a real power loss take 0.4–1.1 s | **Board fix** (D-R19-10): C87 220 nF; turn-on 30–129 ms worst; chatter immunity worst 10.6 / 20.5 / 26.4 ms at 6.0 / 7.4 / 8.4 V. The < 10 ms chatter bench test stays |
| R19-REQ-03 | `M3_ACTUATOR_MERGE.md` cited as current | **Records fixed:** superseded banner; citations point to M3_R10 "Power" |
| R19-REQ-04 | FMEA I-7 said R123 100 kΩ | **Records fixed:** 2 kΩ |
| R19-REQ-05 | REQUIREMENTS F9 had run-together words | **Records fixed** |
| R19-REQ-06 | P3's 5 × 100 g retention has no flight root | **Carried:** owner choice (owner table row 12) |
| R19-REQ-07 | C84's hold-up has no required duration | **Carried as an open owner question** (owner table row 25); no design change |
| R19-REQ-08 | R7–R9 history inside current REQUIREMENTS rows | **Records fixed:** moved to `HISTORY.md` and the matching M3_R* files |
| R19-REQ-09 | Parent `VEHICLE.md` stack row is stale | **Parent repository:** handled by the root (outside this worktree) |
| R19-REQ-10 | Port UARTs treated as fast; dead RF and sense classes in the gate | **Gate lane** |
| R19-DOC-01 | ORDERING 8.2 named C126's GND via at its old spot | **Records fixed** |
| R19-DOC-02, -03 | Owner table not decision-ready; stale banners at the file head | **Records fixed:** this file's head and the owner decision table |
| R19-DOC-04 | Numbers glued to words in live text | **Records fixed** in the live sections of this file, AVA_LAYOUT and R10_DECISIONS; historical sections keep their text |
| R19-DOC-05 | Q122 gate bound 0.220 V in the docs, 0.218 V in the pin table | **Records fixed:** 0.218 V (3.6 V × 2 kΩ / 33 kΩ) |
| R19-DOC-06 | "Seven nets" did not match `BARREL_NETS` or the board | **Records fixed:** §1 gives the barrel count |
| R19-DOC-07 | A committed sentence promised a check run in the future tense | **Records fixed:** past tense, naming the runs |
| R19-DOC-08 | AGENTS pointed to AVA_LAYOUT for current placement | **Records fixed:** AGENTS and the AVA_LAYOUT head |
| R19-DOC-09 | Sense levels without "powered" or "cold"; "no bypass" hid a 5.1 kΩ path | **Records fixed:** §1 and the owner table |
| R19-GATE-01 … -07 | Gate gaps (pad paste overrides, LCSC re-codes, plane necks, other-rail via floors, a second U9 IN via, word-legend tie, silkscreen allowlist) | **Gate lane.** The CAD lane already closed the board side of GATE-04 / -05 (second vias, K-power paths, D-R19-09) and GATE-06 (D-R19-06) |

### Round 19 fix pass

The CAD lane made PCB `50a39de5…` (D-R19-01 … D-R19-14; `round19_fix_cad.md` and `.json`). Two complete `m3_design/r10_build.sh` builds (9 and 10) gave the same PCB, and each ended in `tools/check.sh` exit 0.
At the CAD pass: check_r10 35 rules; route_check 0 failing, 22 bump windows, 7 unrecorded noncritical leftovers (was 6). After the gate pass (D-R19-15, `round19_fix_gate.md`; PCB unchanged): `tools/check.sh` exit 0 twice; **check_r10 35 rules, all OK** (six titles now name the round 19 checks); route_check 0 failing; fab content checks 3 / 3; self-tests shell 10, procurement 20, fab_validation 34, fit 33, paste 16, r10_parts 5, route 68, **R10 234** (6 NumPy skips under KiCad Python), NumPy `HotplugNumerics Plate` **6**. D-R19-15 keeps the port UARTs under the strict return-path rules (R19-REQ-10). The new pour-debris check admits one piece by a named, stale-failing entry (U1.74, §6); BAT and SWITCH word-centre margins (0.080 / 0.040 mm against 1.0 mm) are reported only (§7).
The board changes are: PYRO1_OUT barrel keep-outs (D-R19-01); the BAT_ENABLE via moved (-02); TP121 removed (-03); C123 on Q122's gate (-04); no pour on U1.19 (-05); word legends (-06); no paste on C84 (-07); pin legends outside the DB125 bodies (-08); second vias on five feeds (-09); C87 220 nF (-10); U4 ISM6HG256XTR (-11); nine fixed designator spots (-12); MCU text (-13).
**The spare AUX port (D-R19-14, owner-approved 2026-10-30).** J440 at F(7.4,16.25) is a copy of the GPS and radio ports (pin 1 4.8 V, 2 GND, 3 board TXO, 4 board RXI; same resistors and ESD; no new BOM codes). The GPS on J410 now uses USART3 PD8 / PD9, the AUX port USART6 PC6 / PC7, and the radio stays on UART5.
J410, J420 and J440 are electrically identical, so firmware keeps a port map (default GPS J410, radio J420, AUX spare). J9 is not interchangeable. The AUX port may draw up to 100 mA at 4.8 V (U401 thermal). It raises the live JLC cost to $85.35 per board against the $84.41 cap: an open owner decision (owner table row 14).
**The changed board needs its own two consecutive clean reviews: rounds 20 and 21 are planned.**

## Round 20: board lenses on committed `6628488`

Seven Claude lenses (manufacturing, MCU, mechanics, parts, power, routing, safety) reviewed PCB `50a39de5…` at commit
`6628488`, with the round 19 gate pass's checks. **0 Critical / 0 Major / 32 Minor (25 new, 7 carried).** No lens
found an inadvertent-fire path that needs fewer than two independent faults. Reports: `round20_<lens>.md` / `.json`
under `m3_design/assembly_review/sources/r10_review/`.

| Lens | Report | Minor | New / carried |
|---|---|---|---|
| Manufacturing | `round20_manufacturing` | 4 | 4 / 0 |
| MCU | `round20_mcu` | 4 | 4 / 0 |
| Mechanics | `round20_mechanics` | 2 | 2 / 0 |
| Parts | `round20_parts` | 3 | 1 / 2 |
| Power | `round20_power` | 3 | 3 / 0 |
| Routing | `round20_routing` | 11 | 7 / 4 |
| Safety | `round20_safety` | 5 | 4 / 1 |

### Round 20 dispositions

| ID | Finding | Disposition |
|---|---|---|
| R20-SAF-01 | U9's EN reaches its only pull-down R81 through three series vias; one open floats EN | **Not done** (D-R20-01: no legal B.Cu spot beside U9.1). Owner deviation (row 29) and respin item; mitigated by JLC's electrical test and the per-flight switch-off check |
| R20-SAF-02 | S-6 did not see AUX_ nets or the arming-switch chain | **Gate fix** (round 19 gate lane): S-6 covers AUX_, BAT_ENABLE and BAT_SW_; FMEA I-11 corrected to S-6's real scope |
| R20-SAF-03 | West-face harness rules missed the AUX leads | **Records fixed:** J440 lead dressing and routing (ORDERING 8.4, handoff, FMEA) |
| R20-SAF-04 | C87 timing omitted the EN leakage | **Records fixed** (D-R20-11): 10.6 / 20.5 / 26.4 ms at 6.0 / 7.4 / 8.4 V, 8.5 ms at 5.73 V, 6.6 ms at 5.5 V; 10 ms needs ≥ 5.92 V; turn-on 30–129 ms |
| R20-SAF-05 | Terminal inner rings near hazardous inner copper (carried) | **Board fix** (D-R20-05): J121.1 and J400.2 have no inner rings; J121.2 keeps its (GND exempt); J1.2's In2 ring went too (RAW_PROTECTED 0.25 mm from that GND barrel) |
| R20-PWR-01 | AUX thermal basis counts U401 alone | **Records fixed:** AUX allowance provisional; first-article power-knot measurement (row 26) |
| R20-PWR-02 | U401 FB tap on one via | **Board fix** (D-R20-02): via (30.575,11.6); the PORT_4V8 level check stays as a check |
| R20-PWR-03 | "U11 blocks reverse current" during hold-up | **Records fixed** (IRCB 0.2 / 1 / 2 A) |
| R20-MCU-01 … -04 | VREFBUF, port endpoint level, unmapped port, parts_qualification pin map | **Records fixed** (binding note and docs) |
| R20-MEC-01, -02 | J440 lead path; plate model re-run | **Records fixed** (lead row; 180.8 Hz, 78.6 g, 0.261 / 0.320 mm) |
| R20-MFG-01 | Panel tabs over In2 power copper | **Partly fixed** (D-R20-08): west aft keep-out; east tabs are the owner's choice (row 28) |
| R20-MFG-02, -03 | Designators in large courtyards; Fab references over outlines | **Board fix** (D-R20-06, -07) |
| R20-MFG-04 | R10 order-number location | **Records fixed** (ORDERING 8.1) |
| R20-BOM-01 | U4 9 in stock but 2 orderable | **Gate and records:** the stock check now fails (2 < 5); confirm on order day or consign the LSM6DSV320X |
| R20-BOM-02, -03 | DB125 holes; VCAP worst case | **Carried** (rows 9 and the VCAP row) |
| R20-RTE-01, -02 | TP82 stub; U1.74 fragment | **Board fix** (D-R20-04, -03) |
| R20-RTE-03, -04 | GPS jogs; VLOGIC via pair | **Not done** (D-R20-10, optional cleanliness): next board change |
| R20-RTE-05 | AUX clamps 6.2 mm from pins | **Board fix** (D-R20-09): 4.08 / 4.18 mm centre to centre (3.16 / 3.19 mm pad edge to pad edge). *Corrected in round 28 (audit lane A): 4.08 / 4.18 mm is the track path, 3.157 / 3.194 mm the straight centre-to-centre distance and 1.865 / 1.900 mm the pad-edge gap; on `a0ec075e…` the tracks are 3.864 / 3.964 mm (D-R24-17)* |
| R20-RTE-06, -07 | C89 / 1210 under-body vias; stale routing records | **Records fixed** (§6) |
| R20-RTE-08 … -11 | Returns over In2 rails, detours, USB pair, copper under U4 | **Carried** (§6) |

### Round 20 polish pass

The CAD lane's polish pass (`round20_fix_cad.md`; D-R20-01 … D-R20-11) made PCB `0dc84776…`. Two complete builds both
ended in `tools/check.sh` exit 0: check_r10 35 / 35 rules, route_check 0 failing (`--bumps-all` 148 information
instances, was 149), self-tests shell 10, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 68,
R10 239 (6 NumPy skips), NumPy 6. Hot-plug 2304 cases pass. Fab package: BOM unchanged (81 lines), CPL 69 top / 122
bottom + 14 placement-only, paste 253 / 375. Cost and stock were not re-run. The pre-commit circuit check (on the staged change)
passed with 2 Minor: the D-R20-01 F.Cu respin option, and stale C87 / inner-ring figures in REQUIREMENTS / AGENTS, both fixed in that commit. No physical, firmware or owner acceptance is claimed.


## Round 21: ten lenses on committed `accfff4`

Ten Claude lenses reviewed PCB `0dc84776…` at commit `accfff4`. **0 Critical / 0 Major / 35 Minor (29 new, 6
carried).** Reports: `round21_<lens>.md` / `.json` under `m3_design/assembly_review/sources/r10_review/`.

| Lens | Minor | New / carried |
|---|---|---|
| Docs binding | 8 | 8 / 0 |
| Requirements | 6 | 5 / 1 |
| Safety | 5 | 3 / 2 |
| Gate | 5 | 5 / 0 |
| Parts | 4 | 1 / 3 |
| Power | 2 | 2 / 0 |
| Manufacturing | 2 | 2 / 0 |
| MCU | 1 | 1 / 0 |
| Mechanics | 1 | 1 / 0 |
| Routing | 1 | 1 / 0 |

### Round 21 dispositions

| ID | Finding | Disposition |
|---|---|---|
| R21-PWR-02, R21-BOM-01, R21-MFG-01, R21-GATE-02 | J1.2 / J400.2 holes 0.25 mm from inner copper (JLC PTH pad hole 0.3 mm); DRU looser than JLC | **Board fix** (D-R21-01): inner-layer PTH pad hole to copper 0.55 mm; J1.2, J400.2 and J3's shell holes now 0.550 mm; K-rules pins JLC's hole table |
| R21-PWR-01, R21-GATE-01 | Regulator FB / sense taps on one via; only R402.1 gated | **Board and gate fix** (D-R21-02): U2.1 second path; `SINGLE_OPEN_TAPS` 26 taps, 8 exact exceptions |
| R21-REQ-01, -02 | Stale schematic notes (U4 part, camera regulator, battery fuse) | **Fixed** (D-R21-03) |
| R21-REQ-04, R21-SAF-02 | Arming chain not critical in route_check | **Fixed** (D-R21-04) |
| R21-SAF-01 (carried) | U9 EN through three series vias | **Board fix** (D-R21-05): R81 / C87 at U9's end, one via left (owner row 29); respin: U9's west cell |
| R21-GATE-03, -04, -05 | Tab keep-out, clamp placement and Fab references not held by the gate | **Gate fix** (D-R21-06, -07, -08) |
| R21-SAF-03 | FMEA I-5 and C128 missing from the enabled-bus fire list | **Records fixed:** §1, owner row 1, FMEA I-5 (R10 row); owner row 18 is the lever |
| R21-MEC-01 | THT procedure: selective soldering, no keep-offs | **Records fixed:** ORDERING 8.2 hand-solder, keep-offs, U5 port mask, clamp inspection |
| R21-MCU-01 | Binding-note obligation cited by number | **Records fixed:** cited by content |
| R21-BOM-02 (carried) | U4 short; LSM alternate also unavailable | **Records fixed:** consign franchised ISM6HG256XTR first |
| R21-BOM-03, -04 (carried) | DB125 holes; VCAP worst case | **Carried** (rows 9 and the VCAP row) |
| R21-REQ-03, -05, -06 | Camera row, flight-2 envelope, R7–R9 text in current rows | **Records fixed** (REQUIREMENTS, HISTORY §3); the envelope is an owner / simulator item |
| R21-RTE-01, R21-SAF-05, R21-DOC-05 | Deviation list bound to a superseded board; stale detour table | **Records fixed:** header and inventory basis bound to `5516eeec…`; §6 detour table recomputed on it |
| R21-DOC-01 … -08, R21-SAF-04 | Stale or inconsistent records | **Records fixed** (handoff TP81 / C15.1, stock check, supplier evidence, circuit check, 50a39de5 leftovers, plate wording, the C87 sentence) |
| R21-MFG-02 | Via inventory of the previous board | **Records fixed:** 300 vias = 295 at 0.5 / 0.3, 4 at 0.6 / 0.3, 1 at 1.0 / 0.5 mm (ORDERING 8.1) |

### Round 21 fix pass

The CAD lane's fix pass (`round21_fix_cad.md`; D-R21-01 … D-R21-09) made PCB `5516eeec…`. Two complete builds both
ended in `tools/check.sh` exit 0: check_r10 36 / 36 rules (K-ports new), route_check 0 failing (6 unrecorded noncritical
leftovers), self-tests shell 10, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 69, R10 247
(6 NumPy skips), NumPy 6. Hot-plug 2304 cases pass. Fab package: BOM unchanged (81 lines, 45 Extended / 36 Basic), CPL
69 top / 122 bottom + 14 placement-only, paste 253 / 375. Fresh supplier evidence on the final files: $85.37 per board
(M3 not met by $0.96); the stock check fails on U4 and U9. The pre-commit circuit check (Opus, max effort, on the staged change): PASS, 6 Minor. Five are records and notes, fixed by the CAD lane before the commit: the U2.1 run width, the battery_entry note naming Q120 / C88, the 3V3 via INFO, the plane strips at the west-edge terminals, and two wrong statements. The sixth is the AUD-2 sentence in AGENTS §3 (now names the J400 switch chain; owner row 30). It confirmed: the netlist is identical to HEAD (701 pad nets); with J400 open the single opens that float EN dropped from 13 to 4; every S-8 barrel and ring is ≥ 1.021 mm; the EN figures reproduce from SLVSFC9C and EN stays ≤ 2.06 V; U2.1 stays connected with each of the 31 3V3 vias opened; the inner Gerbers show J1.2 / J400.2 / J3 at 0.5505 mm; the JLC table figures hold. No physical, firmware or owner acceptance is claimed.


## Round 22: ten lenses on committed `ec8cb98`

Ten Claude lenses reviewed PCB `5516eeec…` at commit `ec8cb98`: **0 Critical / 0 Major / 22 Minor**, with no
Critical or Major to verify. Each lens's Minor count is below. Reports: `round22_<lens>.md` / `.json` under `m3_design/assembly_review/sources/r10_review/`.

| Lens | Minor |
|---|---|
| Requirements | 4 |
| Docs binding | 4 |
| Parts | 3 |
| Power | 2 |
| Manufacturing | 2 |
| Routing | 1 |
| MCU | 1 |
| Mechanics | 1 |
| Safety | 1 |
| Gate | 3 |

### Round 22 dispositions

| ID | Finding | Disposition |
|---|---|---|
| R22-ROUTING-01 | §6 detour table left out nine larger excesses; R89's via not in the counted list | **Records fixed:** nine rows added (every net ≥ +3.4 mm now listed); R89's via (23.0,70.0) at 2.182 mm counted |
| R22-POWER-01, -02 | U10.2 / U402.2 / R8.2 GND and the PA6 / PA4 / R91 taps on single vias | **Records fixed:** M3_R10 Retained deviations, firmware plausibility rules, ORDERING 8.3 pre-flight PA6 / PA4 check, owner row 27; second vias are a next-board-change item. **Gate (D-R22-02):** the R85.2 / R430.2 exceptions now say each via is a TPS2553's only ground; seven taps are new exact entries (U10.2, R7.2, U402.2, R8.2, R60.1, PA4, R91.1), so `SINGLE_OPEN_TAPS` 26 → 33 and the exceptions 8 → 15 |
| R22-PARTS-01, R22-DOCS_BINDING-01 / -02, R22-REQUIREMENTS-04 | Franchised fallback not obtainable; stale supplier figures and U4 rows | **Records fixed:** dated franchised status (U9 DigiKey due 14-Dec-2026, U4 22-Mar-2027), franchised or JLC sources only, never brokers, the owner's procurement choices (ORDERING 8.1, with option (d), the same-land alternates of `round22_alternates.md`, not adopted), U4 rows, 23:23Z stamp, $102.16 / $105.15, DB125-4 37,757 / 36,979 |
| R22-PARTS-02, -03 (carried) | DB125 holes; VCAP worst case | **Carried** (rows 9 and the VCAP row) |
| R22-MECHANICS-01, R22-MANUFACTURING-01 | DB125 keep-off list missed R102, C431, C410, C420 | **Records fixed** (ORDERING 8.2) |
| R22-MANUFACTURING-02 (carried) | 14 parts with no Fab body outline | **Records fixed:** ORDERING 8.2 check against the silkscreen and JLC's preview; outlines are a next-board-change item. Round 24: deferred (D-R24-12); no stated rule requires them, and the Fab references keep the courtyard box (D-R22-06) |
| R22-SAFETY-01 | §1 inventory not carried to `5516eeec…` | **Records fixed:** removed row marked, new least RAW_ACT-to-GND 0.300 mm, minimum 0.150 mm ARM1_SENSE to U13.5 (benign), R81 / C87 neighbours added |
| R22-DOCS_BINDING-03 | REQUIREMENTS lagged U9 and C88 | **Records fixed** (R10 acceptance; OQ-6 risk) |
| R22-DOCS_BINDING-04 | "EN never exceeds 2.03 V" stated as an absolute | **Records fixed:** 2.03 V nominal, ≤ 2.06 V with 1 % parts, while R81 is intact; 8 % of C87's 25 V rating |
| R22-REQUIREMENTS-01 | Row 30's reason | **Records fixed:** the exemption rests on physics; a legal GND spot exists 0.671 mm from three of the four vias |
| R22-REQUIREMENTS-02 | PTH ring and NPTH minimum not held by the gate | **Gate fixed (D-R22-01):** K-rules measures the board, whatever the DRU says, against JLC's PTH ring 0.20 mm (least 0.200 mm, J3's shell slots), via ring 0.05 mm (0.100), plated hole 0.15 mm (0.30), NPTH hole 0.50 mm (0.60, J3), NPTH ring 0.45 mm (no NPTH pad has copper) and NPTH to copper 0.2 mm (0.200 mm, J3's locating holes to its GND lands: HRO's land, held by the DRU pair rule, K-lands and this check). Seeded copies fail |
| R22-REQUIREMENTS-03 | No requirement covers ESD on J400 | **Records fixed:** F8 / F9, ORDERING 8.3 handling and first-article check. **Closed on `1407e850…` by D-R24-11:** D402 (ESD103-B1-02EL, C535146) at J400.2 ahead of R165; EN moves at most 5.7 mV (Calculation; Inference: no 85 °C leakage figure); the handling rule stays the second layer |
| R22-GATE-01 | The JLC hole table read only a "(min N mm)" written first, matched only the exact pinned layer word, and had no board measure for three rows | **Gate fixed (D-R22-05):** every "(min …)" is read in any position and unit (mm, mil, um, in), and an unreadable one fails; any later rule on a layer that can meet the pinned one counts as an override. New board measures: via hole to copper ≥ 0.2 mm (least 0.25 mm), PTH hole to outer copper ≥ 0.28 mm (0.55 mm, J1.1), pad hole to hole ≥ 0.45 mm (0.835 mm, J3). Seeds g01e / f / g / h, a um spelling and three board seeds fail |
| R22-GATE-02 | Fab references not tied to their part | **Gate fixed (D-R22-06):** each Fab reference within 1.5 mm of its own part's body box (courtyard box for the 14 parts without a Fab outline; farthest on the board 0.968 mm, D9); stroke ≥ 0.1 × height or 0.05 mm; no board-level Fab text. Seeds g08a / c / d and U1's reference moved off fail |
| R22-GATE-03 | Port clamp ground legs not held | **Gate fixed (D-R22-07):** each port clamp's GND pad must reach a GND via through tracks within 1.0 mm (0.7 mm for D410 / D411 / D420 / D421 / D440 / D441, 0.8 mm for D400 / D401). Seeds g07b and a 1.5 mm return fail |
| R22-MCU-01 | Diagnostics sheet note example | **Fixed (D-R22-03, note text only):** nominal 5.456 V reads 0.496 V; a failed U400 passes RAW_PROTECTED, held under U9's OVLO (9.77 V nominal), and reads about 0.89 V; even D8's 19.9 V clamp would read 1.81 V |

The mechanics lens re-ran the plate model on `5516eeec…` with figures identical to round 20's.

### Round 22 between-rounds pass

The CAD lane (`round22_fix_cad.md`; D-R22-01 … D-R22-07) changed only checks, one schematic note's text and records.
- **Builds.** Two complete `r10_build.sh` builds, the first for items 1–4 and the second with the gate items, both gave
  PCB `5516eeec…` again. Each ended in `tools/check.sh` exit 0:
  - DRC 0 / unconnected 0 / schematic parity 0 / ERC 0;
  - check_r10 36 / 36 rules; route_check 0 failing (6 unrecorded noncritical leftovers, unchanged);
  - self-tests: shell 10, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 69, R10 253 (6 NumPy
    skips), NumPy 6.
- **Package.** The first build changed the diagnostics sheet and the four date-stamped fab outputs, and `r10_fab.sh`
  re-bound the package. The second build changed only the date-stamped outputs.
- **Supervisor run.** `tools/check.sh` exit 0 on the final tree (DRC 0 / unconnected 0 / parity 0 / ERC 0; check_r10 36 / 36; route_check 0 failing; fab content checks and the manifest OK; self-tests 10 / 34 / 33 / 16 / 5 / 69 / 253 (6 NumPy skips) / 6 OK).
- **Not done in this pass.** No supplier re-run (the BOM and CPL are unchanged), and no physical, firmware or owner
  acceptance is claimed.


## Round 23: ten lenses on committed `c70d261`

Ten Claude lenses reviewed the same PCB `5516eeec…` at commit `c70d261`, the second review of the closing pair after
round 22. Nine have reported, all **0 Critical / 0 Major**, 48 Minor so far. A fresh max-effort verifier confirmed
R23-SAFETY-08 (a) and R23-SAFETY-05 as Minor (`round23_safety_severity_check.md`); it also corrected the physics: Q124's
gate capacitor is C126 (220 nF), not C128 (100 nF, on the drain). Reports: `round23_<lens>.md` / `.json` under
`m3_design/assembly_review/sources/r10_review/`. The closing pass is text and checks only; the board does not change.

| Lens | Minor |
|---|---|
| Docs binding | 10 |
| Safety | 9 |
| Requirements | 8 |
| Manufacturing | 5 |
| MCU | 4 |
| Mechanics | 4 |
| Power | 4 |
| Parts | 3 |
| Routing | 1 |
| Gate | 7 |

### Round 23 dispositions (docs lane; the root decisions in `.supervisor/r23_fix_brief.md` set the wording)

| ID | Finding | Disposition |
|---|---|---|
| R23-SAFETY-01 | Per-flight switch-off check runs with the bus off | **Records fixed:** closed-switch check with a 1–2 Ω dummy in J121 (ORDERING 8.3); owner row 24 says it is the only per-flight screen of the three PC1 / bus pairs; FMEA H-6 |
| R23-SAFETY-02 | No stay-off check after the e-match is in; recovery order | **Records fixed:** stay-off and recovery steps (ORDERING 8.3, handoff, FMEA H-6); firmware PC1 source rule (PA4 low, VBUS_SENSE consistent; an extra barrier, not a guarantee) |
| R23-SAFETY-03 | No per-flight igniter-resistance check | **Records fixed:** meter test current < 40 mA, J400 open, record the value (ORDERING 8.3) |
| R23-SAFETY-04 | No post-landing disarm | **Records fixed:** LANDED rule (M3_R10 Firmware, FMEA F-8, REQUIREMENTS F12) |
| R23-SAFETY-05 | Q120 gate on one via; four stalls 1.063–1.128 A (verified Minor) | **Records fixed:** powered BUS ≥ 0.96 × pack ground refusal; §1 row; first-article ACT_GATE probe; respin item (row 27). **Gate (D-R23-02):** exact single-open entries for both gate vias, Q120 (16.20, 73.30) and Q121 (11.14, 71.70) |
| R23-SAFETY-06 | J400 ESD outcomes not all covered | **Records fixed:** outcomes (a)–(c), worst case about 9.6 V beside 7.5 V nominal, bench supply ramp in the first-article check (ORDERING 8.3, REQUIREMENTS F9). **Closed on `1407e850…` by D-R24-11:** a discharge into the screw now reaches D402 at J400.2 before R165; the handling rule stays the second layer |
| R23-SAFETY-07 | Launch rule ambiguous | **Records fixed:** LIFTOFF AND a barometric altitude gain (LAUNCH_CORROBORATED); no inertial-only fire path; FMEA F-6 noted as not enough on R10 |
| R23-SAFETY-08 | QSPI_IO2–PE4 bridge, OUT–3V3 / 3V3A pairs, PYRO1_IGN-to-GND consequence (verified Minor) | **Records fixed:** firmware QSPI rules and ground refusal, cold-screen traffic test, first-article U1 / U3.3–R127.1 check; three §1 rows; the PYRO1_IGN wording (fail-safe for firing; R134 overloads to 22–29 W) |
| R23-SAFETY-09 | Alternate TPS259470A record; cold-screen wording | **Records fixed:** cold screen after every power-up or reset (M3_R10, FMEA); `round22_alternates.md` "Round 23 corrections" |
| R23-POWER-01 | Hold-up after the PA6 trip | **Records fixed:** PA6 trip window and trip-to-3.8 V hold-up (owner row 25, M3_R10, REQUIREMENTS F6); "100–220 µF would do" struck |
| R23-POWER-02 | J400 chatter train | **Records fixed:** functional pass rule at 5.73–6.0 V under vibration, < 20 % open fraction per 100 ms (REQUIREMENTS F6, ORDERING 8.3, handoff); since round 24 the line is < 18 %, because D402's leakage lowers the worst-case trip to about 20 % at 5.73 V (R24-TRI-02, root decision). **Superseded in round 25** (R25-TRI-01, D-R25-01): open-fraction rules pass trains that trip a worst-case U9; the rule is now total open time under 7 ms in every sliding 100 ms window, with U9 on for the whole run at 5.73 V |
| R23-POWER-03 | TPS259470A short behaviour | **Records fixed** (`round22_alternates.md` corrections, ORDERING 8.1 option (d)) |
| R23-POWER-04 | PA5 also pulses on U9 reverse blocking | **Records fixed** (M3_R10 Firmware); the pin_table note is the CAD lane's |
| R23-MCU-01 | Bring-up configuration missing | **Records fixed** (M3_R10 Firmware; RM0433 items Inference) |
| R23-MCU-02 | BOOT0 / VCAP1 / VCAP2 single vias | **Records fixed** (retained deviations, row 27 respin). **Gate (D-R23-01):** exact single-open entries for BOOT0 (13.80, 45.60), VCAP1 (29.25, 38.00) and VCAP2 (18.00, 37.30) |
| R23-MCU-03 | LSM6DSV80X 1.6× claim wrong | **Records fixed** (`round22_alternates.md` corrections; IMU rule) |
| R23-MCU-04 | PB1 TT_a | CAD lane (binding note); parts_qualification corrected in the round 28 fix pass (R28-TRI-06) |
| R23-ROUTING-01 | No installed GNSS self-interference check | **Records fixed:** ORDERING 8.3 check; clock-harmonic rule (Inference until run) |
| R23-MECHANICS-01 | 16–18 AWG cannot turn in the wire room | **Records fixed:** ≤ 20 AWG (22 preferred), OD ≤ 1.8 mm, bend at the wire face, 4.493 mm; owner row 31 |
| R23-MECHANICS-02 | Landing basis not rooted | **Records fixed:** chute-based load, sled relief (owner row 32) |
| R23-MECHANICS-03, R23-PARTS-01 | Hot-end ratings against bay air | **Records fixed:** part temperature, chamber test, ≤ 55 °C interim limit (owner row 33) |
| R23-MECHANICS-04 | No battery-lead route | **Records fixed** (ORDERING 8.4, handoff) |
| R23-PARTS-02 | Consignment process | **Records fixed** (ORDERING 8.1) |
| R23-PARTS-03 | LSM6DSV320X swap needs the CPL rotation changed | **Records fixed** (`round22_alternates.md`, ORDERING 8.1) |
| R23-REQUIREMENTS-01 | Flight envelope | **Records fixed:** derived envelope labelled Inference (REQUIREMENTS) |
| R23-REQUIREMENTS-02 | ≤ 30 s window has no root | **Records fixed** (REQUIREMENTS F1) |
| R23-REQUIREMENTS-03 | F3's 10 km basis | **Records fixed:** ≥ 300 hPa with a vacuum-chamber characterisation before flight 2 |
| R23-REQUIREMENTS-04 | P3's 200 g option | **Records fixed:** 2 × the landing load of the chosen chute (owner row 12) |
| R23-REQUIREMENTS-05 | Servo stall during boost | **Records fixed:** chatter test at 5.73 V; q-scheduled deflection limit as a simulator item. **Round 26 correction** (R26-TRI-02, D-R26-03): the test runs at 5.71 V, the four-stall point with the AUX allowance |
| R23-REQUIREMENTS-06 | No landed requirement | **Records fixed:** F12 "Landed" |
| R23-REQUIREMENTS-07 | No pad pack check | **Records fixed:** pad READY refused below 7.4 V plus the PA6 divider error |
| R23-REQUIREMENTS-08 | No in-flight thermal basis | **Records fixed** (REQUIREMENTS F1) |
| R23-MANUFACTURING-01 | Electrical Test field | **Records fixed:** Flying Probe Full Test (ORDERING 8.1; rows 29, 34) |
| R23-MANUFACTURING-02 | Order-number mark | **Records fixed:** Mark on PCB none / Remove Mark; placeholder leftover (row 35). **Closed on `1407e850…` by D-R24-13** (placeholder removed) |
| R23-MANUFACTURING-03 | No single order-form value set | **Records fixed:** "R10 order form" table (ORDERING 8.1) |
| R23-MANUFACTURING-04 | VIPPO request | **Records fixed:** via-covering article, two named vias, first-article X-ray |
| R23-MANUFACTURING-05 | Short-edge parts within 2.5 mm | **Records fixed:** expected DFM queries (ORDERING 8.1). Round 24 (D-R24-15): R92 and TP88 moved (courtyards ≥ 2.5 mm); C95, R166, R400 / R401 / R404 and C403 remain expected DFM queries |
| R23-DOCS_BINDING-01 | Round 22 status not carried | **Records fixed** (this file's head, rows, decisions table, owner row 20; other files by the docs lane) |
| R23-DOCS_BINDING-02 | Two cold-screen bases | **Records fixed:** 96.2 / 96.1 / 141.5 mV labelled "at Vf = 0.30 V" |
| R23-DOCS_BINDING-03 | Bring-up facts missing | **Records fixed** (M3_R10 Firmware) |
| R23-DOCS_BINDING-04 | DS12110 revision basis mixed | **Records fixed** (M3_R10 Sources, AGENTS) |
| R23-DOCS_BINDING-05 | U9 probe points under the QFN | **Records fixed** (ORDERING 8.3) |
| R23-DOCS_BINDING-06 | Per-flight checks differ between files | **Records fixed:** one numbered list in ORDERING 8.3, linked from the handoff and AGENTS |
| R23-DOCS_BINDING-07 | Consignment and form values | **Records fixed** (ORDERING 8.1) |
| R23-DOCS_BINDING-08 | "Consigned alternate" | **Records fixed:** "second-fallback alternate" |
| R23-DOCS_BINDING-09 | Bottom legend list | **Records fixed** (ORDERING 8.2, handoff) |
| R23-DOCS_BINDING-10 | Broken anchor | **Records fixed** (`M3_R10.md#board-history-superseded-interim-boards`) |
| R23-GATE-01 | The DRU reader missed unquoted rule names, quoted layers and `#`-commented rules | **Gate fixed (D-R23-05):** the DRU is tokenised as KiCad reads it; anything unreadable fails K-rules. Seed h01 and the quoted / commented variants fail |
| R23-GATE-02 | The JLC board measures skipped copper drawings, copper text and footprint zones | **Gate fixed (D-R23-06):** `_copper_items` comes from S-8's `copper_nodes`; every figure on the board is unchanged; the h01 In1 drawing 0.16 mm from a via hole fails |
| R23-GATE-03 | DRU minimums outside the hole rows, and `(severity ignore)`, had no floor | **Gate fixed (D-R23-07):** every constraint minimum is floored (the project floor where stricter than JLC's table); only error severity passes. Seeds h03 / h04 (SERVO1 to SERVO2 at 0.0636 mm) fail |
| R23-GATE-04 | Fab label check missed text boxes, visible fields, squashed labels and board-level Fab shapes | **Gate fixed (D-R23-08):** seeds f01b / f02 / f03 / f05 fail |
| R23-GATE-05 | A generator edit stripping Q120 / Q121's paste passed | **Gate fixed (D-R23-09):** r10_parts' nine footprints SHA-pinned and the paste totals (253 / 375) pinned; x02 fails |
| R23-GATE-06 | A hand-reverted sheet note passed check.sh | **Gate fixed (D-R23-10):** check.sh runs the schematic contract and sheet replay first (about 6 s); d01 fails |
| R23-GATE-07 | U4's power-ground via and the VCAP vias not single-open taps | **Gate fixed (D-R23-01, D-R23-11):** exact entries for U4.6 / U4.7's GND via (16.75, 47.60) (an open: IMU dead, primary does not fire, roll control lost; respin: a second via) and C19 / C20 |

### Round 23 closing pass

The CAD lane (`round23_fix_cad.md`; D-R23-01 … D-R23-11) changed only checks, two schematic notes' text (sensors,
diagnostics), the binding-note obligations, `pin_table.tsv` notes and records.
- **Single-open taps.** 33 → 40 taps with 22 exact exceptions: BOOT0, VCAP1 / VCAP2, the Q120 / Q121 gate vias and U4's
  power-ground via.
- **Gate fixes.** The seven gate-lens items: DRU reader, copper set, DRU floors, Fab labels, footprint / paste pins, and
  the replay in check.sh.
- **Binding note.** The 13 root firmware rules (49 obligations), PB1 TT_u, and the second-fallback wording for the
  LSM6DSV320X.
- **Build.** One complete `r10_build.sh` (1586 s) gave PCB `5516eeec…` again, byte-identical to `c70d261`. Its
  `tools/check.sh` exited 0:
  - DRC / unconnected / parity / ERC 0;
  - check_r10 36 / 36; route_check 0 failing;
  - self-tests: shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 69, R10 261 (6 NumPy
    skips), NumPy 6.

  BOM and CPL are unchanged; the package was re-bound.
- **Supervisor run.** `tools/check.sh` exit 0 on the final tree (DRC 0 / unconnected 0 / parity 0 / ERC 0; schematic contract and sheet replay OK; check_r10 36 / 36; route_check 0 failing; fab content checks and the manifest OK; self-tests 11 / 34 / 33 / 16 / 5 / 69 / 261 (6 NumPy skips) / 6 OK).

## Round 24 board pass

Rounds 22 and 23 were the closing pair on `5516eeec…`. The round 24 board pass (CAD lane, `round24_board_cad.md`;
D-R24-01 … D-R24-17, 2026-11-01) then changed the board on the owner's request ("I see 90 degree bends lol. why not 45")
and on the round 22 / 23 dispositions, so the closing pair does not carry. The new board is PCB
`1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e` (2,363,869 bytes; outline 46 × 90 × 1.6 mm,
unchanged). Rounds 24 and 25 review it under the owner's strict rule: only real errors count (false statements, broken
links or anchors, wrong calculations, unusable procedures), and iteration stops after two consecutive rounds with zero
verified real errors.

| Count | `5516eeec…` | `1407e850…` |
|---|---|---|
| Footprints | 215 | 216 (D402) |
| Track segments | 983 | 1057 |
| Vias (GND) | 300 (167) | 307 (168): 10 added, 3 removed, 8 moved |
| Track length | 1871.611826 mm | 1867.022756 mm |
| Visible / hidden references, legends | 122 / 93, 45 | 124 / 92, 44 (the order mark removed) |
| Placed parts; CPL top + bottom | 205; 72 + 133 | 206; 70 + 136 (67 + 125 reconstructed, + 14 placement-only) |
| Paste apertures F / B | 253 / 375 | 249 / 381 |
| JLC BOM codes | 81 (45 Extended / 36 Basic) | 81 (45 / 36); the C535146 line 8 → 9 per board |

Per item (measured on the round 24 board; full text in `R10_DECISIONS.md`):

- **Second barrels added (done).**
  - D-R24-02: Q120 (15.4, 72.85) and Q121 (11.74, 72.3) gate drive (B.Cu 0.361 mm from Q120.9 (BAT_IN) / 0.342 mm from ACT_FET_S; both lands are 0.2505 mm from the outer GND fill, the accepted surface class; corrected by the round 24 fix pass, R24-TRI-05; "from the nearest foreign copper" was wrong). A via named in `PARALLEL_VIAS` is now left out of the net's via count and the hop test as well as the loop search.
  - D-R24-03: BOOT0 (14.2, 46.0), 0.150 mm from I2C1_SCL on F.Cu (the board floor, DRC 0).
  - D-R24-04: VCAP2 (18.3, 36.8).
  - D-R24-07: U402.2 / R430.2's GND island (32.3, 60.1).
  - D-R24-08: R60.1 VLOGIC (34.5, 62.4), U1.28 LOGIC_SOURCE_ST (30.45, 51.4), R91.1 3V3 (28.1, 59.4).
  - D-R24-10: R87.1's input layer change, USB_LIMITED (16.6, 28.0).
- **U401's divider (done, D-R24-09).** R402 B(30.9, 12.85) and R403 B(30.9, 14.6) (were F.Cu): FB, the divider top and
  its bottom join U401 with no via; the FB via, R402.1's via and R403.2's return via are removed, and U401's OUT via
  moves to (29.75, 11.65). The OUT run's T at (29.75, 12.85) lies 0.075 mm inside R402.1's land, a review-only routing
  item (AUD-10; §6).
- **Single points kept, with measured reasons (respin items).**
  - D-R24-01: U4.6 / U4.7's GND via (16.75, 47.6): the legal region is about 0.38 × 0.32 mm, room for one via; a trial
    with C30 moved shorted to the F.Cu IMU_INT1 escape and was reverted.
  - D-R24-04: VCAP1: C19 is boxed on B.Cu, and U1.48's pad lies east of the via on F.Cu.
  - D-R24-05: U9's EN through one via: the B.Cu pocket at U9.1 is about 1.4 × 2.2 mm against the roughly 2.0 × 2.45 mm
    R81 and C87 need, and no via pair fits (owner row 29).
  - D-R24-06: owner row 22's three feeds: U11.2 (best spot 0.402 mm from ACT_EN_MCU against D-R18-03's 0.5 mm floor)
    and 3V3A (16.0, 50.2) / (27.0, 49.25).
  - D-R24-07: U10.2 / R7.2 / R85.2 (the island inside the VBUS ring already holds two vias) and R8.2 (every island spot
    lies under D4 / USB_DP or In2 USB_LIMITED).
  - D-R24-10: R87.1's drop (22.0, 62.25) (the only spot necks the In2 3V3 fill under 0.5 mm) and R85.1 (no legal spot
    within 1.6 mm).

  SINGLE_OPEN_EXCEPTIONS go from 22 to 11.
- **J400.2's ESD clamp D402 (done, D-R24-11).** A ninth ESD103-B1-02EL (C535146, on the existing line: no new code or
  feeder fee) at B(4.45, 65.9), rot 90, between J400's pins (M-6 1.768 / 1.808 mm against the 1.5 mm floor). A 4.114 mm
  B.Cu tap from J400.2's own pad reaches it ahead of R165, and it returns 0.7 mm to its own GND via (5.15, 65.575). S-5
  and K-actuators pin BAT_SW_RETURN to exactly {J400.2, R165.1, D402.1}; S-4 requires D402 fitted; K-ports checks its
  path. Its 50 nA maximum leakage at 15 V (Infineon ESD103 Rev 1.3) moves EN by at most 5.7 mV (Calculation). The EN timing figures do not stand as this pass said: that leakage adds to
  U9's own ±0.1 µA EN leakage (R24-TRI-02), and D-R24-19 gives the corrected figures. Inference: there is no 85 °C leakage figure. Shorted, the clamp holds the board off, which
  the pad check sees; open, the board is back to the old state. The handling rule stays as the second layer.
- **Fab body outlines (deferred, D-R24-12).** No stated rule requires them; the 14 lands are SHA-pinned vendor
  footprints (11 library edits and re-pins). The Fab references keep using the courtyard box (D-R22-06).
- **Order-number placeholder (removed, D-R24-13).** r10_post no longer draws JLCJLCJLCJLC and K-legends no longer
  admits it.
- **East panel tabs (deviation kept, D-R24-14).** The In2 RAW_PROTECTED strip (x 44.0–45.7) and the PORT_5V3 band
  (x 41.0–43.7) run side by side along the whole east edge, and the strip joins the forward RAW region only at y 63.3,
  so every east tab band (x 43–46) lies over one of them: a plane redesign (owner rows 16 / 28).
- **Short edge (D-R24-15).** R92 → F(31, 86.7) and TP88 → F(35.5, 86.4), courtyards ≥ 2.5 mm from the forward edge.
  C95, R166, R400 / R401 / R404 and C403 stay expected DFM queries.
- **Optional cleanliness (not taken, D-R24-16).** The GPS pair's forced jogs and the VLOGIC in-line via pair are
  unchanged.
- **90° bends (done, D-R24-17).** 59 bends on `5516eeec…` (F.Cu 25, B.Cu 31, In2 3) → 0. route_check's new RULE
  category `right_angle` fails any that remain, on every net and copper layer, with an empty allowlist (§6).
  - The chamfer pass cut 54 plain bends (including D402's tap); the 6 pad / via bends were redrawn at source with U9's
    input trunk (C88 now B(18.67, 83.56) rot 0).
  - Pairs turning together keep their pitch. USB_DM's J3 strap is 0.422 mm shorter; the D+ / D- run is unchanged.
    J440's clamp runs are each 0.211 mm shorter (3.864 / 3.964 mm, under the 4.5 mm limit).

**Gate (builds C and D, both `1407e850…`, exit 0).**
- DRC 0, unconnected 0, schematic parity 0, ERC 0; `r10_sch_check` OK.
- check_r10 36 / 36.
- route_check: 0 failing, 0 allowlisted, 0 stale, `right_angle` 0, with 5 unrecorded noncritical leftovers.
- Fab content checks (206 CPL rows; paste 249 / 381) and the six-output manifest pass.
- Self-tests: shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 71 (was 69), R10 262
  (was 261; 6 NumPy skips), NumPy 6.
- Hot-plug model: all 2304 cases pass (minimum −14.807 V, steepest fall 8.995 V/µs, rise 5.088 V/µs).
- Not run: no other simulation and no physical test.

**Supplier evidence on the final files.** Cost (2026-11-02T01:43:55Z): $85.60 per board at 5 boards (parts $60.81 +
81 codes × $1.53 / 5), $1.19 over the $84.41 cap (owner row 14). Stock (2026-11-02T01:42:53Z): U9 (C3662793) 28 in
stock, −83 orderable against a minimum purchase of 7; U4 (C51931514) 9 in stock, 2 orderable against 5; C535146 201 in
stock, 194 orderable against 45.


## Round 24: ten lenses on committed `f2b8251`

Ten Claude lenses reviewed PCB `1407e850…` at commit `f2b8251` (2026-11-01), the first round under the owner's strict
rule. They reported **0 Critical / 0 Major / 24 raw Minor findings**: safety 6, power 2, routing 0, MCU 4, parts 0,
mechanics 0, manufacturing 0, requirements 4, docs-binding 5, gate 3. A fresh triage verifier
(`round24_triage.md` / `.json`) reproduced every one: 22 merge into 16 real errors, R24-GATE-01 and R24-MCU-03 are
observations, and one root-flagged gate observation was promoted (R24-TRI-17). Totals: **17 real errors (all Minor),
11 observation items, 0 not reproducible.** None of the errors needed a board change, but the root took the board route
for R24-TRI-01. Reports: `round24_<lens>.md` / `.json` under `m3_design/assembly_review/sources/r10_review/`.

| Triage ID | Lens IDs | Error | Disposition |
|---|---|---|---|
| R24-TRI-01 | R24-SAFETY-01, R24-DOCS_BINDING-01 | The BAT_ENABLE via (17.1,82.8) to BAT_FAULT_N gap was 0.173 mm on `1407e850…` (D-R24-17's chamfer), not the 0.200 mm the records called unchanged | **Board fixed** (D-R24-18): the chamfer is capped, so the gap is 0.200 mm again on `92c3ad59…` (the chamfer itself 0.2015 mm). The docs bind the 0.200 mm statements to `92c3ad59…` |
| R24-TRI-02 | R24-SAFETY-02, R24-POWER-01, R24-REQUIREMENTS-01 | "The EN timing figures stand" was wrong: D402's 50 nA adds to U9's ±0.1 µA EN leakage | **Generated text fixed** (D-R24-19) and **records fixed**: drop-out 10.3 / 20.1 / 26.0 ms at 6.0 / 7.4 / 8.4 V, 8.2 ms at 5.73 V, 6.3 ms at 5.5 V; pack ≥ 5.96 V for 10 ms; turn-on 30–130 ms; chatter trip about 20–24 %; PA6 corner 4.80 V (AGENTS §1, REQUIREMENTS F4 / F6 / F9, M3_R10, ORDERING 8.3, this file, STATUS, parts_qualification). The bench chatter pass line goes from below 20 % to **below 18 %** of any 100 ms window: with D402 the worst-case trip is about 20 % at 5.73 V, so the root set 18 % from that physics. **Round 25 correction** (R25-TRI-01, D-R25-01): the < 18 % line was wrong (it passes trains that trip a worst-case U9); it is replaced by the sliding-window rule, total open time under 7 ms in every 100 ms. **Round 26 correction** (R26-TRI-02, D-R26-03): 5.73 V predated the 100 mA AUX allowance; the four-stall point is 5.71 V, where a single drop-out may last 8.07 ms and the fast-chatter limit is 19.7 % |
| R24-TRI-03 | R24-SAFETY-03, R24-POWER-02 | The bench-ramp window (off 4.5–4.8 V, on 4.9–5.2 V) rejected in-spec boards and disagreed with the sheet note | **Generated text fixed** (D-R24-19) and **records fixed**: expect off 4.29–4.80 V and on 4.72–5.25 V; above 4.80 V means extra leakage to GND at EN or J400.2, below 4.29 V leakage from IN; or compare with each board's first-article values (ORDERING 8.3, REQUIREMENTS F9, M3_R10) |
| R24-TRI-04 | R24-SAFETY-04 (a)(b)(c), R24-MCU-01, R24-MCU-02 | Firmware rules 4 / 5 and §1 still put Q120's gate, R91.1 and U1.28 on one via | **Generated text fixed** (D-R24-19, binding note) and **records fixed** (M3_R10 rules 4 / 5; §1 Q120 row) |
| R24-TRI-05 | R24-SAFETY-04 (d)(e) | Q121 barrel "0.342 mm from the nearest foreign copper" (GND fill 0.2505 mm), and "eight" barrel keep-outs (ten) | **Records fixed** (the round 24 board pass section; M3_R10 CH1) |
| R24-TRI-06 | R24-SAFETY-05 | M3_R10 Power still had via (30.575,11.6) joining R402.1 | **Records fixed** (M3_R10 Power, D-R24-09's layout) |
| R24-TRI-07 | R24-SAFETY-06, R24-REQUIREMENTS-02 | REQUIREMENTS M1 quoted the 2026-10-31 stock run | **Records fixed** (2026-11-02T01:42:53Z, U9 28 / −83 / minimum 7) |
| R24-TRI-08 | R24-REQUIREMENTS-03 | 8.0 m/s over 20 mm is 163 g, not 168 g | **Records fixed** (98–163 g in REQUIREMENTS P3, ORDERING 8.4, owner rows 12 and 32) |
| R24-TRI-09 | R24-REQUIREMENTS-04 | J2 land distances were bounding-square figures | **Records fixed** (J2.1 3.880 mm, J2.3 3.987 mm; range 3.808–3.987 mm; 0.31–0.49 mm from a 7.0 mm washer edge) |
| R24-TRI-10 | R24-MCU-04 | §5 QSPI lengths up to 14.524012 mm; on `1407e850…` QSPI_IO2 is 14.102245 mm | **Records fixed** (§5) |
| R24-TRI-11 | R24-DOCS_BINDING-02 | ORDERING said 14 bottom pin legends; there are 13 | **Records fixed** |
| R24-TRI-12 | R24-DOCS_BINDING-03 | §9 C84 row gave paste 253 / 375 | **Records fixed** (249 / 381) |
| R24-TRI-13 | R24-DOCS_BINDING-04 | round24_board_cad called the orientation counts CPL rows | **Record fixed** (D-R24-23: CPL rows 72 + 133 → 70 + 136; reconstructed 69 + 122 → 67 + 125, plus 14 placement-only); M3_R10's fab bullet also corrected |
| R24-TRI-14 | R24-DOCS_BINDING-05 | STATUS said the R10 section was last updated 2026-10-31 | **Records fixed** |
| R24-TRI-15 | R24-GATE-02 | No check held the 2.5 mm short-edge clearance | **Gate fixed** (D-R24-20): check_r10 rule M-8 with exactly six recorded DFM queries; seeded test |
| R24-TRI-16 | R24-GATE-03, R24-MCU observation 6 | BOOT0's second via cited as D-R24-05 | **Fixed** (D-R24-21: cited as D-R24-03 in five places) |
| R24-TRI-17 | R24-GATE observation 5 | check_actuators' R10 message named J1.3 | **Fixed** (D-R24-22: names J400.1 / J400.2) |

Observations (not counted; reasons in the triage): R24-GATE-01 (a 0.05 mm cut seed passes as a short-segment leftover;
the generator floor forbids it), R24-MCU-03 (a historical BOOT0 companion figure), five routing observations (the
BUZZ_G T, five chamfers starting inside a pad land with pad_end_offcentre 57 → 70 and segment_inside_pad 22 → 27 to be
counted in the final deviation list, seven three-way forks, the J440 port tracks, the leftover-locations JSON), safety
obs 2 (a leaky D402 is caught by the corrected ramp window), manufacturing obs 10 (stackup name; confirm on the quote
page), docs-binding obs 2 (folded into TRI-13), and the remaining confirmations.

## Round 24 fix pass

The CAD lane (`round24_fix_cad.md` / `.json`; D-R24-18 … D-R24-23) changed the board to
`92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` (2,363,951 bytes). The copper diff against
`1407e850…` is exactly BAT_FAULT_N's three F.Cu pieces at (16.55,83.35); footprints 216, segments 1057, vias 307 (168
GND) and hidden references 92 are unchanged, and track length is 1867.023 → 1867.046 mm. BOM, owner BOM and CPL are
byte-identical (81 codes; 206 CPL rows, 70 + 136; paste 249 / 381), so the 2026-11-02 supplier evidence still binds
and was not re-run. The pass also regenerated the battery_entry sheet note and the binding note (D-R24-19), added
check_r10 rule M-8 (D-R24-20) and fixed three comment, message and record texts (D-R24-21 … -23). The docs lane fixed
the records (`round24_fix_docs.md`).

- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 71, R10 263
  (6 NumPy skips; new `test_r24_short_edge_clearance`; three tests extended), NumPy 6.
- *DRC and CAD gate:* builds E and F both gave `92c3ad59…` and `tools/check.sh` exit 0: DRC 0 / unconnected 0 /
  parity 0 / ERC 0; check_r10 37 / 37 (M-8 new); route_check 0 failing, 0 allowlisted, `right_angle` 0, 5 unrecorded
  noncritical leftovers; fab content checks and the six-output manifest; K-binding OK.
- *Simulation and calculation:* the hot-plug model passes all 2304 cases, extremes unchanged (Simulation/Inference);
  the EN corner model with D402 (D-R24-19, Calculation).
- *Physical tests:* none.


## Round 25: ten lenses on committed `c4bb56b`

Ten Claude lenses reviewed PCB `92c3ad59…` at commit `c4bb56b` (2026-11-01) under the owner's strict rule. They reported
**0 Critical / 0 Major / 14 raw Minor findings**: safety 3, power 4, MCU 1, mechanics 2, requirements 3, docs-binding 1;
routing, gate, parts and manufacturing 0. A fresh triage verifier (`round25_triage.md` / `.json`) reproduced all 14:
they merge into 9 real errors, and one mechanics observation was promoted (R25-TRI-10). Totals: **10 real errors (all
Minor, none on the board), 72 observations, 0 not reproducible.** Reports: `round25_<lens>.md` / `.json` under
`m3_design/assembly_review/sources/r10_review/`.

| Triage ID | Lens IDs | Error | Disposition |
|---|---|---|---|
| R25-TRI-01 | R25-POWER-03, R25-REQUIREMENTS-01, safety obs 9 | The chatter rule (< 10 ms per drop-out, < 18 % open in any 100 ms) passed trains that turn a worst-case U9 off (8 ms every 50 ms at 6.0 V: EN 1.095 V; 3 × 4 ms with 0.2 ms closures at 5.73 V: EN 1.028 V) | **Generated text fixed** (D-R25-01) and **records fixed**: total open time under 7 ms in every sliding 100 ms window, recorded at ≥ 10 kS/s, with U9 on for the whole run at 5.73 V (worst-corner limit 7.63 ms); replaying the recorded waveform through the worst-corner model is the fallback. The root's round 24 < 18 % decision was wrong and is corrected (AGENTS §1, STATUS, REQUIREMENTS F4 / F6, M3_R10, ORDERING 8.3, the handoff, this file, parts_qualification). **Round 26 correction** (R26-TRI-02 / -03, D-R26-03): the run is at 5.71 V, the four-stall point with the AUX allowance (limit 7.50 ms), and the triage's 4000-train search was a sample, not the worst case |
| R25-TRI-02 | R25-SAFETY-02, R25-POWER-02, R25-MCU-01, R25-REQUIREMENTS-02 | Post-trip hold-up was computed from 5.3 V, outside the trip window | **Generated text fixed** (D-R25-02, rule 8) and **records fixed**: 0.103–0.164 ms all ports on, 0.291–0.430 ms shed, from VLOGIC 4.84–5.17 V, 0.22–0.31 of the break-to-3.8 V hold-up (M3_R10, REQUIREMENTS F6, ORDERING 8.3, rows 5 and 25) |
| R25-TRI-03 | R25-POWER-01 | REQUIREMENTS F6 still said "100–220 µF would do" | **Records fixed**: struck; from the trip 100–220 µF gives 0.03–0.12 ms |
| R25-TRI-04 | R25-POWER-04 | The 9.97 V OVLO corner omitted IOVLKG ±0.1 µA | **Generator re-run** (D-R25-03): 10.18 V; buck prospective peak 3.657 / 3.627 A; U9 bound 3.743861 A; parts_qualification's R92 bleed (3.147 mA) and the historical all-shorts paragraph corrected |
| R25-TRI-05 | R25-SAFETY-01 | FMEA H-6 kept the old ramp window | **Records fixed**: 4.29–4.80 / 4.72–5.25 V; STATUS's round 24 "every record" sentence corrected |
| R25-TRI-06 | R25-SAFETY-03, R25-DOCS_BINDING-01, safety obs 7 | FMEA I-11 and this file's S-8 paragraph named `1407e850…` as current | **Records fixed** (`92c3ad59…`) |
| R25-TRI-07 | R25-REQUIREMENTS-03 | REQUIREMENTS Pack row turn-off corners omitted D402 | **Records fixed**: 4.802 / 4.835 / 4.875 V |
| R25-TRI-08 | R25-MECHANICS-01 | R150–R155 called "still missing" from STRAIN_PARTS | **Records fixed**: they were added in the round 19 gate pass (M3_R10, §8) |
| R25-TRI-09 | R25-MECHANICS-02 | "plate ≤ 0.8 mm keeps h + t < 5.3 mm" with 4.5 mm standoffs | **Records fixed**: a plate thinner than 0.8 mm (ORDERING 8.4, REQUIREMENTS P3, the handoff, row 32) |
| R25-TRI-10 | mechanics obs 1 (promoted) | Row 32 put C421 at 125 g and called 98–163 g "above" 125 g | **Records fixed**: "can exceed the 125 g at which … C431 (C421 at 133 g)" |

## Round 25 fix pass

The board did not change (`92c3ad59…`; one complete build reproduced it). The CAD lane (`round25_fix_cad.md` / `.json`;
D-R25-01 … -03) regenerated the binding note and the battery_entry sheet note (the chatter rule and rule 8's hold-up)
and `parts_budget.json` (the OVLO corner). The docs lane fixed the records (`round25_fix_docs.md`).

- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 71, R10 263
  (6 NumPy skips; two tests updated), NumPy 6.
- *DRC and CAD gate:* `tools/check.sh` exit 0: DRC 0 / unconnected 0 / parity 0 / ERC 0; check_r10 37 / 37 (K-binding
  OK); route_check 0 failing; fab content checks and the manifest; `r10_parts.py --check` passes.
- *Simulation and calculation:* hot-plug 2304 cases pass, extremes unchanged (Simulation/Inference); the window
  limits, hold-up and OVLO corner are Calculations; the adversarial search is the triage's, not re-run (round 26 found
  it a sample, not the worst case: R26-TRI-03).
- *Physical tests:* none.

## Round 26: ten lenses on committed `3d8e845`

Ten Claude lenses reviewed PCB `92c3ad59…` at commit `3d8e845` (2026-11-02) under the owner's strict rule. They reported
**0 Critical / 0 Major / 14 raw Minor findings**: safety 4, routing 3, power 2, manufacturing 2, requirements 2,
mechanics 1; MCU, gate, parts and docs-binding 0. A fresh triage verifier (`round26_triage.md` / `.json`) reproduced all
14: they merge into 12 real errors, with safety observations 2 and 8 folded in and routing observation 7 promoted. Totals:
**12 real errors (all Minor; one, R26-TRI-09, needs a board change), 107 observations (24 entries in the JSON), 0 not
reproducible.** Reports: `round26_<lens>.md` / `.json` under `m3_design/assembly_review/sources/r10_review/`.

| Triage ID | Lens IDs | Error | Disposition |
|---|---|---|---|
| R26-TRI-01 | R26-SAFETY-01 | §1's "None of the pairs below fires the match by itself" and owner row 2's "Firing still needs a second fault at Q124" were false for PYRO1_OUT to 3V3 (R173.1–D120.3, 0.5135 mm) and 3V3A (R164.2, 0.5662 mm), for the J440.1 / J440.2 harness row and for the OUT-to-GND residuals | **Board changed** (D-R26-02, the respin item): PYRO1_OUT is ≥ 1.040 mm from 3V3 / 3V3A on every layer; D-R26-04 then held 3V3 / 3V3A ≥ 1.0585 mm from Q124's gate nets, after the first layout put R164's via 0.331 mm from PE4's net. **Records fixed:** §1's summary, owner rows 1 and 2, FMEA I-5; the bridge cases a cold screen refuses and those it does not are stated, with D-R26-04's audit rows |
| R26-TRI-02 | R26-POWER-02, R26-SAFETY-02, R26-REQUIREMENTS-01 | "The fire budget's four-stall BAT_IN of 5.73 V" predated the AUX allowance; the bound budget gives 5.713 V | **Generated text fixed** (D-R26-03) and **records fixed**: single drop-out 8.07 ms, window limit 7.50 ms, margin 0.50 ms, fast-chatter fraction 19.7 % (19.6 / 14.8 / 4.5 % at 0.1 / 4 / 8 ms), bench run at 5.71 V (AGENTS §1, STATUS, REQUIREMENTS F4 / F6, M3_R10, ORDERING 8.3, the handoff, this file, parts_qualification) |
| R26-TRI-03 | R26-POWER-01, safety obs 2 | The 4000-train search's EN ≥ 1.1173 V was a sample: one late open block per 100 ms reaches 1.1162 V at 7.62 ms (1.1168 V at 7.6 ms) | **Generated text and records fixed:** the worst admissible train is one open block per 100 ms placed late in the window; it trips U9 at 7.50 ms at 5.71 V and holds EN at 1.1295 V at the 7 ms line |
| R26-TRI-04 | R26-SAFETY-03 | Rule 8's "5.37 V four-stall-plus-fire corner" counted the fire current twice | **Generated text and records fixed:** 5.71 V (healthy match), 5.55–5.56 V (match shorted), 5.50 V (match and leads shorted), VLOGIC 0.09–0.16 V lower; no rule changes |
| R26-TRI-05 | R26-SAFETY-04 | U11.5 called OV2 | **Record fixed:** OV1, IN1's USB over-voltage input (§1) |
| R26-TRI-06 | R26-REQUIREMENTS-02, safety obs 8 | F4's "pack ≥ 5.96 V under four stalls" option rested on the single-drop-out rule F6 replaced | **Record fixed:** the pack option is a four-stall BAT_IN at or above the F6 bench run's 5.71 V; 5.96 V stays only as the labelled single-drop-out figure |
| R26-TRI-07 | R26-ROUTING-01, routing obs 7 (promoted) | Owner row 8 said six under-body 0603 vias (five since D-R24-09) and ten detour nets (the §6 table listed 22) | **Records fixed:** five (R86, R89, R91, R101, R401); the table's count on `a0ec075e…` is 23 (PYRO1_CONT_MID joins it, §6); R19-RTE-04 annotated |
| R26-TRI-08 | R26-ROUTING-02 | "12 of the 21 are beyond 4 mm" is 13 (CAM_MCU_RX 4.02 mm) | **Record fixed** (§6) |
| R26-TRI-09 | R26-ROUTING-03 | AUX_TX_WIRE / AUX_RX_WIRE change layer at J440.3 / J440.4 with the nearest GND via 3.900 / 4.037 mm away, against D-R19-15; route_check tested vias only | **Board and gate fixed** (D-R26-01): GND vias (7.4,16.5) and (7.4,20.0), 1.500 mm from the pins; route_check `pad_layer_changes` (profile r10); the four-position terminal's pins 3 / 4 carry no unconnected inner ring; K-region exempts a pad's merged void with its GND partner's antipad |
| R26-TRI-10 | R26-MECHANICS-01 | §8 gave the wall-allowance wire room as 4.503 mm | **Record fixed:** 4.493 mm |
| R26-TRI-11 | R26-MANUFACTURING-01 | The C84 heat-limit list named the wrong bottom joints and omitted C8 | **Records fixed** (ORDERING 8.2, §8): L1.1, L1.2, C7.1 and C7.2 under land 2 and C9.2 under land 1; C9.1 0.545 mm, C8.2 / C8.1 0.605 / 0.814 mm away; C8 added to the fixture and inspection lists |
| R26-TRI-12 | R26-MANUFACTURING-02 | The J3 slot hand-finish neighbours omitted R7 (2.010 mm), nearer than R8 | **Records fixed** (ORDERING 8.2, R7-MFG-03): C83 / R7 / R8, 1.952 / 2.010 / 2.145 mm |

Observations (not counted; reasons in the triage): the TCR sensitivity of the window limit (7.31 ms at 5.73 V and 7.18 ms at 5.71 V,
at 70 °C; still above 7 ms; R27-TRI-01), the TP81 timing alternative, the BUZZ_OUT / BAT_FAULT_N pairs beside the PC1 chain (the disclosed row 2
class), the 5.5 V sensitivity point, the disclosed PA6 lower edge, the D8 under-body via (an M2 review item for the
final report), row 30's labelled `5516eeec…` distances, the hand-typed budget figures (gate observation 2; the 5.73 V
point was the stale one), L1's saturation rating (not required above the AP63203 limit), and the remaining
reproductions.

## Round 26 fix pass

The CAD lane (`round26_fix_cad.md` / `.json`; D-R26-01 … -04) changed the board to
`a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (2,369,507 bytes). Its first layout (builds 2 and 3)
gave the intermediate `4108e6fa…`, which was never committed or reviewed: the docs lane found R164's moved 3V3 via there
0.331 mm from R126.1 on PE4's net (0.835 mm on `92c3ad59…`) and C10's coat envelope 2.994 mm from U5, and the root's
follow-up D-R26-04 moved both (builds A and B gave `a0ec075e…`). The copper diff against `92c3ad59…`:
- two GND vias added at (7.4,16.5) and (7.4,20.0) (D-R26-01);
- C11, R164 and R173 moved 0.65 mm toward the aft edge (y − 0.65 mm) and C10 0.60 mm, to B(17.5,53.5), with the 3V3A
  trunk; R164's 3V3 via moved (19.05,55.9) → (19.55,55.825), its strap now (18.15,55.25) → (18.975,55.25) →
  (19.55,55.825) (D-R26-02, -04);
- the C11.2 / C10.2 return vias moved to (19.423,52.373) / (19.65,53.45) (C10.2's stub leaves its pad 0.05 mm north of
  the pad centre) and R13's 3V3 via to (9.2,52.55) (was (9.2,52.98));
- PYRO1_OUT's last vertical and PYRO1_CONT_MID's run, now (16.87,59.48) → (16.87,60.82) → (17.85,61.8) → (20.83,61.8),
  were redrawn (11 segments removed, 13 added);
- the four-position terminal's pins 3 / 4 carry no unconnected inner rings; C18's designator is hidden.

Footprints 216, segments 1059, vias 309 (170 GND), hidden references 93, track 1866.794 mm. Every 3V3 / 3V3A item is
now at least 1.0585 mm from Q124's gate nets and 1.040 mm from PYRO1_OUT on every layer (§1). The BOM and owner BOM are
byte-identical (81 codes); the CPL keeps 206 rows (70 + 136) with four moved (C10, C11, R164, R173); paste 249 / 381.
The supplier evidence was re-run on the final files (cost 2026-11-02T12:44:13Z, stock 12:43:17Z: $85.26 per board, U4
and U9 short). The pass also regenerated the binding note (D-R26-03). The docs lane fixed the records
(`round26_fix_docs.md`).

- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 72, R10 267
  (6 NumPy skips; five new tests across the two suites, among them `test_r26_gate_nets_clear_of_3v3_and_3v3a`;
  `test_r23_binding_note_rules_and_pin_table` extended), NumPy 6.
- *DRC and CAD gate:* builds A and B both gave `a0ec075e…` and `tools/check.sh` exit 0, and a standalone
  `tools/check.sh` on the final tree exited 0: DRC 0 / unconnected 0 / parity 0 / ERC 0; check_r10 37 / 37 (K-binding
  OK); route_check 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers (`critical_via_no_gnd` 2 → 0 under the
  new pad test); fab content checks and the six-output manifest.
- *Simulation and calculation:* the hot-plug model passes all 2304 cases, extremes unchanged (Simulation/Inference;
  C10 / C11 re-extracted); the EN window limits, the late-block train and rule 8's corner are Calculations (D-R26-03);
  D-R26-04's bridge analyses are Calculations or labelled Inferences, and its whole-board adjacency audit compares every
  net pair under 1.2 mm with `92c3ad59…` (§1).
- *Docs lane, measured on `a0ec075e…`* (KiCad 10.0.7 pcbnew, read-only, on a copy; Calculation on native geometry):
  the PYRO1_OUT, gate-net and pyro / arming adjacency inventory (§1), S-8 (unchanged minima), the detour table and the
  layer-change returns (§6), the under-body via scan, the C84 and J3 neighbour scans (unchanged) and C10's distance to
  U5's coat exclusion (3.017 mm; pads alone 3.449 mm), each agreeing with D-R26-04.
- *Physical tests:* none.

## Round 27: ten lenses on committed `816038c`

Ten Claude lenses reviewed PCB `a0ec075e…` at commit `816038c` (2026-11-02) under the owner's strict rule. They reported
**0 Critical / 0 Major / 7 raw Minor findings**: power 3, MCU 1, mechanics 1, requirements 1, safety 1; gate, parts,
manufacturing, routing and docs-binding 0. A fresh triage verifier (`round27_triage.md` / `.json`) reproduced all 7 and
merged one sibling it found (the stall-input pack sag on the pre-AUX port allocation, power observation 14) into
R27-TRI-02. Totals: **7 real errors (all Minor, none on the board), 19 observation entries in the JSON (the lenses listed
125 observations), 0 not reproducible.** Reports: `round27_<lens>.md` / `.json` under
`m3_design/assembly_review/sources/r10_review/`.

| Triage ID | Lens IDs | Error | Disposition |
|---|---|---|---|
| R27-TRI-01 | R27-POWER-01 | Round 26's observations said the 70 °C TCR window limits 7.31 / 7.18 ms were both computed at 5.73 V and not re-run at 5.71 V; 7.18 ms is the 5.713 V figure (`round26_safety.md`) | **Records fixed:** "7.31 ms at 5.73 V and 7.18 ms at 5.71 V, at 70 °C; still above 7 ms" (Round 26's observations); an erratum line in `round26_fix_docs.md` item 5 |
| R27-TRI-02 | R27-POWER-02, power obs 14 (sibling) | parts_qualification's GAP-3 paragraph used the pre-AUX 460 mA allocation (0.406 W, 102.5–114.7 °C at 70 °C, 135.4 °C/W), and its stall-input paragraph and the generator's `loaded_pack` the pre-AUX 1.46 A port load (5.921 / 4.436 V in the text, 5.899 / 4.414 V in the budget) | **Generator fixed** (D-R27-01: `loaded_pack` counts the 0.1 A AUX allowance; with the 11 mA quiescent load restored by the round 28 correction, R28-TRI-03 / D-R28-01, the budget gives 5.881 / 4.388 V: 5.880831 / 4.388491 V at 1.561 A = 1.461 A + 0.1 A AUX; D-R27-01's 1.46 A + 0.1 A gave 4.389 V) and **records fixed** (parts_qualification: 560 mA, 0.490 W, 109.2–123.9 °C at 70 °C, 124.2–138.9 °C at 85 °C, ceiling 112.3 °C/W; the stall input at 1.561 A since round 28, with the generator's 0.6375 A logic allocation). No limit is crossed |
| R27-TRI-03 | R27-POWER-03 | M3_R10 Power gave the In2 3V3 fill as 1466.52 mm², D-R18-06's figure on `a3144b15…` | **Record fixed:** 1430.05 mm² in one piece on `a0ec075e…` (re-measured by the docs lane), with 1466.52 mm² kept as D-R18-06's history |
| R27-TRI-04 | R27-MCU-01 | The binding note said every DS12110 citation in it is Rev 8, but its R5-MCU-04 obligation cites Rev 11 Table 109 | **Generated text fixed** (D-R27-02, `r10_sch_check.py`; the note regenerated): the two design limits read from Rev 11 Table 109 in round 14 (the 6.0 V FT cap and the 4.0 V ADC-mode maximum) are named as exceptions; **record fixed:** §5's "all DS12110 cites are now Rev 8" names the same exceptions |
| R27-TRI-05 | R27-SAFETY-01 | FMEA I-5 (R10), §1's single-fault routes and `round26_triage.md` called the 3V3 over-voltage clamp "H-9"; §4.2's H-9 is the load-switch gate-source capacitor, fitted on R10 as C120 | **Records fixed** (FMEA I-5 (R10), §1); FMEA's historical I-5 row marked as a mislabel; an erratum note in `round26_triage.md` |
| R27-TRI-06 | R27-MECHANICS-01 | ORDERING 8.4 and the handoff said J440's leads stay "south of y 23.5"; in the records' compass (north = smaller y = aft) that is forward, into the zone the same row forbids | **Records fixed:** "aft of y 23.5 (y < 23.5; J440's forward body end is at y 23.45)"; erratum pointers in `round20_mechanics.md` and `round19_fix_docs.md` |
| R27-TRI-07 | R27-REQUIREMENTS-01 | J410 / J420 / J440 used the camera terminal symbol, whose pin names ("5V OUT", "RX FROM CAMERA TX", "TX TO CAMERA RX") reverse F10's 3 TXO / 4 RXI and misstate the 4.8 V supply; the names reach neither the PCB nor the fab package | **Schematic fixed** (D-R27-03): the three ports get their own symbol, M3:PortTerminal (pins 4V8 / GND / TXO / RXI), and `r10_sch_check` asserts the names with four seeded faults; J9 keeps M3:CameraTerminal. Nets, copper and the PCB are unchanged |

Observations (not counted; reasons in the triage): ORDERING's 0.030 mm finished inner copper for 1 oz (the stackup's
figure, conservative for the DC solver), the stale `tools/test_r10_plate.py` (missing J430 / J440 masses; `tools/check.sh`
does not run it and no current document cites it as passing), the PYRO1_IGN–3V3 0.735 mm and RAW_ACT–3V3 0.837 mm
pairs (the I-5 lists do not claim to be complete, and §1 bounds only PYRO1_OUT and the gate nets), the In2 pinch of
0.47 mm against the labelled "about 0.50 mm", USB_LIMITED at 63.115 mm against the labelled round 18 63.605 mm (under
1 % in resistance), the 4.74 V |VGS| at 6.0 V (about 4.73 V at the 5.71 V point, still above 4.5 V), and the remaining
reproductions.

## Round 27 fix pass

The board did not change (`a0ec075e…`). The CAD lane (`round27_fix_cad.md` / `.json`; D-R27-01 … -03) changed the
generator's `loaded_pack` (the AUX allowance; `parts_budget.json` regenerated, then `ecc45417…`, `4267634…` since
round 28), the binding note's revision sentence (then `e8f10fb3…`; `30796f5e…` in round 28, `c5cd0fa3…` since round 29) and the ports' schematic symbol (M3:PortTerminal; `schematic.net.xml` `535a8fdf…`,
`circuit.json` `3220e5f9…`). The docs lane fixed the records (`round27_fix_docs.md`).

- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 72, R10 268 (was 267; 6 NumPy skips; new `test_r27_port_terminal_pin_names`; `test_r23_binding_note_rules_and_pin_table` extended) and NumPy `HotplugNumerics Plate` 6, all OK.
- *DRC and CAD gate:* one complete `m3_design/r10_build.sh` (KiCad CLI 10.0.7) reproduced PCB `a0ec075e…` and ended in `tools/check.sh` exit 0: r10_sch_check OK (43 seeds caught: 39 contract, 4 pin-name); DRC 0, unconnected 0, schematic parity 0, ERC 0; check_r10 37 / 37 (K-binding OK); route_check 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers; fab content checks and the manifest. The build re-exported the fab outputs with only their creation dates changed (BOM, owner BOM, CPL and paste byte-identical), so the supplier evidence stands.
- *Simulation and calculation:* the hot-plug model passes all 2304 cases with 0 failures, its inputs and results
  byte-identical (Simulation/Inference); the pack-sag and U401 thermal figures are Calculations / Inferences from the
  budget model (R27-TRI-02).
- *Docs lane, measured on `a0ec075e…`* (KiCad 10.0.7 pcbnew, read-only, on a copy; Calculation on native geometry): the
  In2 3V3 fill is one piece, 1430.05 mm² (1431.06 mm² on `92c3ad59…`).
- *Physical tests:* none.

## Round 28: ten lenses on committed `19dd0b5`

Ten Claude lenses reviewed PCB `a0ec075e…` at commit `19dd0b5` (2026-11-02) under the owner's strict rule. They reported
**0 Critical / 0 Major / 8 raw Minor findings**: power 3, MCU 2, requirements 2, safety 1; gate, parts, manufacturing,
routing, mechanics and docs-binding 0. A fresh triage verifier (`round28_triage.md` / `.json`) reproduced all 8 and
promoted safety observation 4 to a Major: an AGENTS §2.5 labelling violation, which the review brief rates Major.
Totals: **9 real errors (1 Major, 8 Minor; none on the board), 102 observations, 0 not reproducible.** Reports:
`round28_<lens>.md` / `.json` under `m3_design/assembly_review/sources/r10_review/`.

| Triage ID | Lens IDs | Error | Disposition |
|---|---|---|---|
| R28-TRI-01 | R28-SAFETY-01 | FMEA's R10 disposition credited the bus / continuity dividers with "ADC series protection"; audit 2 removed R168 / R170, so R10 has none | **Record fixed** (FMEA's R10 row): the dividers (two 5.1 kΩ tops in series, two parallel 2 kΩ bottoms, 10 nF) feed PC0 / PC5 directly, with no double-fault pin-current limit (REQUIREMENTS F8) |
| R28-TRI-02 | R28-POWER-01 | parts_qualification's GAP-1 paragraph said the budget includes 12.370807 W; it holds 13.064091 W (12.370807 W was the pre-AUX figure) | **Record fixed** by audit lane A (parts_qualification: 13.064091 W, with 12.370807 W named as the pre-AUX figure) |
| R28-TRI-03 | R28-POWER-02 | D-R27-01's `loaded_pack` used 1.46 A + AUX, though its comment and record say it matches `ports_w` (1.461 A + AUX); on that basis the 6 V four-stall figure is 4.388 V, not 4.389 V | **Generator fixed** (D-R28-01: `loaded_pack` takes `ports_w`'s port current, `port_A`; the budget gives 5.880831 / 4.388491 V, SHA-256 `4267634…`) and **records fixed** (STATUS's round 27 entry and this file's R27-TRI-02 row: 5.881 / 4.388 V at 1.561 A; parts_qualification's stall input and budget hash by audit lane A; D-R27-01 annotated) |
| R28-TRI-04 | R28-POWER-03 | parts_qualification counted four C21397 22 µF on PORT_4V8; the board has five (C445) and a third 100 nF (C444) | **Record fixed** by audit lane A (five C21397 on PORT_4V8 with C445, and the 100 nF C444) |
| R28-TRI-05 | R28-MCU-01 | The first-article check "meter U3.3 (QSPI_IO2) to R127.1: it must read open" fails an intact board in one meter polarity: with the red lead on R127.1 the U1 / U3 input clamps conduct into R127.1's 0.91 kΩ to GND | **Generated text fixed** (D-R28-02: firmware rule 3 and its test string) and **records fixed** (M3_R10 rule 3, FMEA I-2 / H-2, §1; ORDERING 8.3 by audit lane B): before first power, with the board unpowered, resistance mode, both polarities; an intact board reads above 0.9 kΩ, or open, both ways; a continuity beep or under 100 Ω in either polarity is a bridge |
| R28-TRI-06 | R28-MCU-02 | parts_qualification called PB1 a TT_a pin (DS12110 Rev 8 Table 9 p70: TT_u), and this file's R23-MCU-04 row said the docs already say TT_u | **Records fixed** (parts_qualification by audit lane A: TT_u, DS12110 Rev 8 Table 9 p70; the R23-MCU-04 row) |
| R28-TRI-07 | R28-REQUIREMENTS-01 | REQUIREMENTS F4 gave flight 2's max-q hinge moment as 73–84 % of the HV6120 stall torque; 73 % is the flight-1 K850DM case | **Record fixed:** about 64–84 % over flight 2's derived envelope (77–84 % nominal to high; supersonic linear theory, Inference) |
| R28-TRI-08 | R28-REQUIREMENTS-02 | REQUIREMENTS asked to re-check "the Temperature row's 525 s"; that row has said about 1200 s since round 23 | **Record fixed:** the stale figure is dropped, and the round 23 re-check is recorded |
| R28-TRI-09 | safety observation 4 (promoted; **Major**) | Firmware rule 3 stated the QSPI_IO2 / PE4 fight figures (1.19–1.98 V on the gate, a fire after about 0.55 ms, at most 6 mA RMS) as fact; they rest on inferred driver resistances, the flash drive, AON7524's extrapolated sub-amp curve and the match thermal model (AGENTS §2.5) | **Generated text fixed** (D-R28-03: the binding note, which also labels five more obligations: the AUX allowance, the GAP-5 bound, the chatter text and rules 4 and 8) and **records fixed** (M3_R10 rule 3, FMEA I-2 / H-2, §1; ORDERING 8.3 by audit lane B), with the source's qualifiers "the MCU driving IO2 high" and "in all but one modelled corner": "(Calculation / Simulation; driver resistances, flash drive, the AON7524 sub-amp curve and the match thermal model are Inference)". **Class sweep (docs lane):** M3_R10's current state, CH1 pyro, Power and Firmware sections, FMEA's R10 rows, REQUIREMENTS, the owner rows, AGENTS and STATUS. Figures resting on an inferred input that were labelled Calculation only, or not at all, are now labelled Calculation / Inference: the fire budget and rule 4's body-diode currents, the EN chatter and turn-on figures (C87's X7R bias allowance), the hold-up figures, rule 8's four-stall-plus-fire corner and the load-switch \|VGS\| settling (Q122's conduction). Round 29 found further places that this sweep had missed (R29-TRI-01); the round 29 fix pass labelled them |

Observations (not counted; reasons in the triage): the pre-microSD / pre-AUX ride-through table in parts_qualification
(covered by its header's supersession line), Q122's 0.218 V against 0.2203 V with 1 % parts (stated with its nominal
formula), tracked documents citing untracked probe artefacts as provenance (`.supervisor/` is excluded by design, and
each claim reproduces from the board), LED_YEL's 0.500 mm on the boundary of a non-critical test, and the remaining
reproductions.

## Round 28 fix pass

The board did not change (`a0ec075e…`). Four lanes ran in parallel:
- **CAD lane** (`round28_fix_cad.md` / `.json`; D-R28-01 … -04):
  - the generator's `loaded_pack` (TRI-03, D-R28-01; `parts_budget.json` now
    `4267634220f4254aef28dfc9756c68b29784560c11b994c14274790dd631fab2`, lines 91–92 5.880831 / 4.388491 V);
  - firmware rule 3's meter criterion (TRI-05, D-R28-02);
  - rule 3's Inference label and five more labelled obligations (TRI-09 and the §2.5 sweep, D-R28-03);
  - rule 4's Q120 pass criterion, obligation 15's port supply lead ("tens of ms", Calculation / Inference) and rule 3's
    "before first power" (D-R28-04, siblings routed from audit lane B).

  The binding note was then `30796f5ece9f3660264ca855dd6e4c1dbd8f97ee3f37983aed200ea27ef32ede` (`c5cd0fa3…` since the round 29 fix pass, D-R29-01; `a40e21a4…` at build 3, before the DS15034 Table 2 citation fix, D-R28-04). D-R27-01 and D-R21-07 are
  annotated.
- **Audit lane A** (`round28_audit_pq.md`): the whole of `parts_qualification.md`, section by section. It fixed TRI-02,
  -03, -04 and -06 and about 35 more stale or mislabelled current statements, and it marks every historical section as
  such.
- **Audit lane B** (`round28_audit_proc.md`): every R10 procedure step in ORDERING 8 and the handoff, re-derived from the
  netlist, the board and the datasheets. It changed 17 steps, among them:
  - the QSPI_IO2 / PE4 meter check (TRI-05 / -09);
  - a C84 capacitance pass value at TP83;
  - the Q120 gate-drive pass criterion;
  - the J400 ESD test's dummy-load condition;
  - the port supply's lead;
  - per-flight step 4's no-USB precondition.

  It verified the rest unchanged.
- **Docs lane** (`round28_fix_docs.md`): TRI-01, -03, -05, -06, -07, -08 and -09 in its files; the §2.5 class sweep;
  rules 3 and 4 aligned with the generated text; and the routed siblings. These are the J440 clamp distances, the USB
  attach inventory, DS15034 Table 2's page, the U400 / L400 distance and the cold-screen labels.

Results:
- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 72, R10 268
  (6 NumPy skips; `test_r23_binding_note_rules_and_pin_table` extended), NumPy 6, all OK.
- *DRC and CAD gate:* build 3, on the tree before the DS15034 citation fix (D-R28-04 regenerated the binding note after it; the committed tree passed the root's `tools/check.sh`), reproduced PCB `a0ec075e…` (as build 1 had) and ended in
  `tools/check.sh` exit 0:
  - r10_sch_check OK;
  - DRC 0 / unconnected 0 / parity 0 / ERC 0;
  - check_r10 37 / 37 (K-binding OK);
  - route_check 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers;
  - fab content checks and the manifest.

  The fab outputs changed only in their creation dates (BOM, owner BOM, CPL and paste byte-identical), so the supplier
  evidence stands.
- *Simulation and calculation:* the hot-plug model passes all 2304 cases with 0 failures, its inputs and results
  byte-identical (Simulation/Inference). The pack-sag figures are Calculations / Inferences on the budget model (stall input, parts_qualification; R28-TRI-03), and the
  relabelled figures keep their values.
- *Physical tests:* none.

## Round 29: ten lenses on committed `09a564e`

Ten Claude lenses reviewed PCB `a0ec075e…` at commit `09a564e` (2026-11-02) under the owner's strict rule. They reported
**0 Critical / 1 Major / 4 raw Minor findings**: safety 1 (the Major); gate, MCU, mechanics and requirements 1 Minor
each; power, parts, manufacturing, routing and docs-binding 0. A fresh triage verifier (`round29_triage.md` / `.json`)
reproduced all 5 and merged four observations into them (safety observation 12 into TRI-02, gate observations 3–5 into
TRI-05). Totals: **5 real errors (1 Major, 4 Minor; none on the board), 139 observations, 0 not reproducible.**
Reports: `round29_<lens>.md` / `.json` under `m3_design/assembly_review/sources/r10_review/`.

| Triage ID | Lens IDs | Error | Disposition |
|---|---|---|---|
| R29-TRI-01 | R29-SAFETY-01 (**Major**) | AGENTS §2.5: current statements still gave figures resting on inferred inputs as "Calculation" or bare model output: the unclamped J400 ESD 9.6 V (FMEA H-6, REQUIREMENTS F9; C87's 0.72 × minimum carries the inferred X7R DC-bias allowance), C128's 991 microstrain (FMEA I-5), the fire currents (§2; Q124's inherited hot factor), the 34.853 ms guard (§5, owner row 7), the plate model's 125 / 133 g (owner row 32), the gate-net bridge's 3.23 V (M3_R10) and the pack-sag "Calculations" (STATUS, the round 28 fix pass). Four round 28 status lines (AGENTS, M3_R10 twice, STATUS) claimed that every such figure was labelled | **Records fixed** (docs lane): every listed place, and the three borderline places, labelled Calculation / Inference with its inferred input named; the docs lane's own sweep labelled three more: M3_R10's EN switch-network paragraph and the gate-net bridge's fire in FMEA I-2 and §1 (`round29_fix_docs.md`); the four status claims now say what each pass did |
| R29-TRI-02 | R29-MCU-01, safety observation 12 | Rule 3 gave Q124's gate time constant as 47–53 µs, which covers C126 only from −10 % to nominal; C126 at +10 % gives 58.3 µs | **Generated text fixed** (D-R29-01: rule 3 and the binding note; the phrase pinned and "47–53 µs" rejected) and **records fixed** (M3_R10 rule 3, FMEA I-2 / H-2, §1): about 47–58 µs over C126's ±10 % (53 µs nominal; Calculation, driver resistances Inference) |
| R29-TRI-03 | R29-MECHANICS-01 | §8 said 23 tails of seven terminals had fit allocations and J440's four were "not re-run"; fit_check allocates all 27 on every gate run | **Record fixed** (§8): all 27 tails of the eight terminals, minimum tail/bore clearance 7.558359 mm (unchanged on `a0ec075e…`); the "not re-run" sentence deleted |
| R29-TRI-04 | R29-REQUIREMENTS-01 | LS120 (MLT-5020 p2 item 6) is rated −20…+70 °C operating, so it is out of rating at the stated 70 °C bay; the hot-end disposition, the 55 °C interim limit and the chamber test covered only the 85 °C parts | **Records fixed** (REQUIREMENTS Temperature, M3_R10 hot end, ORDERING 8.3, owner row 33, parts_qualification, AGENTS buzzer row): LS120 named as a +70 °C part; the chamber test passes only with LS120 ≤ 70 °C (thermocouple on LS120); new owner row 36: buzzer annunciation is best-effort when bay air is above about 48 °C (70 °C − 22 K; Inference), recovery and logging do not depend on the buzzer, and the respin option is a +85 °C buzzer on the same land. Round 30 replaced the "LS120 ≤ 70 °C" pass clause (R30-TRI-02): the chamber test passes on the 85 °C parts alone and records LS120's measured rise, which sets the best-effort bay-air limit (70 °C minus that rise) in place of the inferred 48 °C |
| R29-TRI-05 | R29-GATE-01, gate observations 3–5 | D-R28-03 said the test pins each new label, but the chatter obligation's turn-on label was not pinned (a revert to the round 27 text passed every check), nor were six other D-R28-02 … -04 qualifiers | **Test fixed** (D-R29-02: the turn-on label and qualifiers (a)–(f) pinned, "EN turn-on delay. Resume" rejected; D-R28-03 annotated) |

Observations (not counted; reasons in the triage): the 6 V open pack's four-stall 4.39 V, below the REQUIREMENTS pack
floor (its paragraph states a shedding policy, not a guarantee); the "$102.05 plus fixed fees" row, on the target basis
as §10 says; the nominal-resistor pull-up bounds (already ruled); power observation 2 (1.128 against a re-solved
1.12747 A, both above 1.125 A); and the remaining reproductions.

## Round 29 fix pass

The board did not change (`a0ec075e…`). Two lanes ran in parallel:
- **CAD lane** (`round29_fix_cad.md` / `.json`; D-R29-01 … -02):
  - rule 3's gate time constant, about 47–58 µs over C126's ±10 % (TRI-02, D-R29-01);
  - the binding-note test pins the turn-on label and the six other D-R28-02 … -04 qualifiers, and rejects the round 27
    form and "47–53 µs" (TRI-05, D-R29-02); D-R28-03 is annotated.

  The binding note is now `c5cd0fa313d3e973bf0542e806f82ae1bfea357943ec49d3c84e522449836cca` (was `30796f5e…`; only rule 3's time-constant phrase
  changed, and its board, netlist, pin-table and circuit hashes are unchanged).
- **Docs lane** (`round29_fix_docs.md`): TRI-01 in full (every listed and borderline place, its own sweep and the four
  status claims); TRI-02's docs places; TRI-03; TRI-04 with owner row 36; and the round 29 records.

Results:
- *Software tests:* shell 11, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 72, R10 268
  (6 NumPy skips; `test_r23_binding_note_rules_and_pin_table` extended in place: its D-R28-03 block has 20 required
  phrases, was 9, and 14 rejected forms, was 12), NumPy 6, all OK.
- *DRC and CAD gate:* one complete `m3_design/r10_build.sh` (1668 s) reproduced PCB `a0ec075e…` and ended in
  `tools/check.sh` exit 0:
  - r10_sch_check OK;
  - DRC 0 / unconnected 0 / parity 0 / ERC 0;
  - the R10 CAD contract OK (K-binding included);
  - route_check 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers;
  - fab content checks and the manifest.

  The fab outputs changed only in their creation dates (BOM, owner BOM, CPL and paste byte-identical), so the supplier
  evidence stands. `parts_budget.json` is unchanged.
- *Simulation and calculation:* no model was re-run for the docs; the relabelled figures keep their values, and rule
  3's 47.8 / 53.0 / 58.3 µs are Calculations on the round 23 model with inferred driver resistances.
- *Physical tests:* none.

## Round 30: ten lenses on committed `0afaed3`

Ten Claude lenses reviewed PCB `a0ec075e…` at commit `0afaed3` (2026-11-02) under the owner's strict rule. They reported
**0 Critical / 0 Major / 2 raw Minor findings**: safety 2; power, routing, MCU, parts, mechanics, manufacturing,
requirements, docs-binding and gate 0. A fresh triage verifier (`round30_triage.md` / `.json`) reproduced both and merged
requirements observation 20 into TRI-02. Totals: **2 real errors (both Minor, text only; none on the board), 107 lens
observations not counted, 0 not reproducible.** Reports: `round30_<lens>.md` / `.json` under
`m3_design/assembly_review/sources/r10_review/`.

| Triage ID | Lens IDs | Error | Disposition |
|---|---|---|---|
| R30-TRI-01 | R30-SAFETY-01 | §1's ARM1_SENSE-to-CAM_IO_3V3 bridge figures (about 1.73 V on RAW_ACT, about 0.15 mA in the match) left out the D120 / R131 cold pull-up, which is live whenever CAM_IO_3V3 is up; sibling: §1 gave the RAW_ACT bridge's EN load as 11.2 kΩ, leaving out the e-match path | **Record fixed** (§1): about 2.19–2.21 V on RAW_ACT and about 0.107–0.109 mA through the match at a BAT54 drop of 0.20–0.24 V (Calculation / Inference); EN load 5.6 kΩ with the e-match or the step-3 dummy fitted. Conclusions unchanged: no fire, the cold screen refuses, and the board does not start |
| R30-TRI-02 | R30-SAFETY-02, requirements observation 20 | Round 29 added "LS120 ≤ 70 °C" to the first-article 70 °C chamber test's pass criterion, which no board can meet at the pad load (LS120 runs above chamber air), so the interim 55 °C limit could never be lifted; it contradicted owner row 36, which accepts LS120 as best-effort | **Records fixed** (REQUIREMENTS Temperature, M3_R10 hot end, ORDERING 8.3, owner rows 33 and 36, `parts_qualification.md`, STATUS's round 29 entry, the R29-TRI-04 row; also the AGENTS buzzer row): the pass criterion is every 85 °C part ≤ 85 °C alone; the test records LS120's measured rise over chamber air at the pad load (thermocouple on LS120), which is not a pass / fail gate; the bay-air limit above which buzzer annunciation is best-effort is 70 °C minus that measured rise, which replaces the inferred 48 °C (now only the pre-test estimate, Inference) |

Observations (not counted; reasons in the triage): the U1.15 / U1.17 pad-gap wording (already ruled); check_r10's
"DS41271" citation for the AP63203 2.0 A (the figure is right; the document number could not be identified); fail-safe
pairs not in §1's table (the table does not claim completeness); outward-rounded bounds (R134 22–29 W, U9.1–U9.5
1.52–1.83 MΩ); and the remaining reproductions.

## Round 30 fix pass

The board did not change (`a0ec075e…`). One lane ran: the **docs lane** (`round30_fix_docs.md`): TRI-01 (§1's bridge
figures and the RAW_ACT bridge's EN load), TRI-02 in every place the triage listed and the AGENTS buzzer row, and the
round 30 records. No generator, test, decision or CAD change, so no new D-R30 decision; `r10_sch_check.py` and the
binding note carry neither statement.

Results:
- *Software tests:* none run by the docs lane.
- *DRC and CAD gate:* not run by the docs lane; root runs `tools/check.sh` before the commit.
- *Simulation and calculation:* no model re-run; TRI-01's figures are the triage's three-node solve (Calculation /
  Inference: the BAT54 drop at about 0.1 mA), checked by hand.
- *Physical tests:* none.

## R10 deviations for owner acceptance

### Owner decision table

Each row is one thing you decide. Nothing here is accepted yet; R9 stays the accepted board. The sections below the table (1 to 13) are the supporting detail, with the measured numbers.
Rows that block the order must be answered before ordering. Rows marked "accepted now, closed by test" are a risk you accept before ordering, which a test on the delivered board then closes.
The board is PCB `a0ec075e…` ([round 26 fix pass](#round-26-fix-pass), `round26_fix_cad.md`), made from `92c3ad59…` ([round 24 fix pass](#round-24-fix-pass)), which was made from `1407e850…` ([round 24 board pass](#round-24-board-pass)). Rounds 22 and 23 found 0 / 0 / 22 and 0 / 0 / 55 on `5516eeec…`, the closing pair for that board. Round 24 found 17 real errors on `1407e850…` ([Round 24](#round-24-ten-lenses-on-committed-f2b8251)), and the fix pass changed the board. Round 25 found 10 real errors on `92c3ad59…` ([Round 25](#round-25-ten-lenses-on-committed-c4bb56b)), none on the board, and round 26 found 12 on it ([Round 26](#round-26-ten-lenses-on-committed-3d8e845)), one of which changed the board. Round 27 found 7 real errors on `a0ec075e…` ([Round 27](#round-27-ten-lenses-on-committed-816038c)), round 28 found 9 ([Round 28](#round-28-ten-lenses-on-committed-19dd0b5), one Major) round 29 found 5 ([Round 29](#round-29-ten-lenses-on-committed-09a564e), one Major) and round 30 found 2 ([Round 30](#round-30-ten-lenses-on-committed-0afaed3), Minor, text only), none on the board, so the board still needs its closing pair: rounds 31 and 32 (planned) under the owner's strict rule, which stops after two consecutive rounds with zero verified real errors.
Write your answer and the date in the "Owner answer / date" column, or in a dated note in this file that names the row number.

**Accept (a risk or limit you take on)**

| # | You accept | What it means | Closed by | When | Blocks order? | Owner answer / date | Detail |
|---|---|---|---|---|---|---|---|
| 1 | One screw switch, no fuse in the battery lead, no physical break while powered | With the board on, the pyro bus is live after the on-rail check (Q120 and Q121 are then on), so Q124 and the firmware that drives it alone keep the e-match from firing; before that check the series pair Q120 / Q121 is a second barrier. USB or a self-powered module can keep the board running with the switch open. A hard short from the pack to U9 or Q120 is not current-limited. Single faults that fire with the bus enabled include FMEA I-5 (battery or port voltage onto 3V3 drives PE4: U2 high-side short, In2 3V3 next to RAW_PROTECTED / PORT_5V3 / PORT_4V8 at 0.300 mm, or the J440.1 / J9.1 In2 rings 0.2505 mm from 3V3), a short in C128, the only MLCC across Q124 (991 microstrain at 100 g, plate model) (R21-SAF-03, Inference; §1), a PYRO1_OUT bridge to GND (surface 0.177 / 0.180 mm; R173.1 to Q124's source via 0.500 mm), to 3V3 or to 3V3A (bus voltage onto the rail through the match; at least 1.040 mm since D-R26-02; R26-TRI-01), a 3V3 / 3V3A bridge to Q124's gate nets (it drives the gate as a fire command does; at least 1.0585 mm since D-R26-04), and possibly a PYRO1_OUT bridge to BUZZ_DRV (R173.1 to R162.1, 0.794 mm; firing not excluded, Inference, D-R26-04) (§1). Owner row 18 is the lever that restores a second barrier on the pad. | Bench tests (ORDERING 8.3); harness rules (strain relief, no chafe, crimped or soldered leads); connect the e-match only with no USB or self-powered module attached | Before order | Yes | Open | §1 |
| 2 | Latent faults at the load switch, the switch's EN node and the fire path | One inner-layer or surface defect near the load-switch gate, the PC1 enable chain, U9's EN node or the sense branches can switch the bus on with the switch open, keep the board on after J400 opens, or bypass R134. For these load-switch, PC1 enable-chain, EN-node and sense-branch defects firing still needs a second fault at Q124; the PYRO1_OUT-to-GND residuals (0.177 / 0.180 mm; R173.1 to Q124's source via 0.500 mm) fire an enabled match by themselves, and a PYRO1_OUT bridge to BUZZ_DRV (R173.1 to R162.1, 0.794 mm) may (Inference, D-R26-04) (row 1). PYRO1_OUT is at least 1.040 mm from 3V3 and 3V3A since D-R26-02 (0.5135 / 0.5662 mm before; R26-TRI-01), and Q124's gate nets at least 1.0585 mm since D-R26-04 (0.835 / 0.676 mm before). The round 18 and 19 fix passes removed the measured inner-layer adjacencies; the surface residuals are listed under "Row 2 residuals" below. | Conformal coat (ORDERING 8.3 list), the "RAW_ACT dead with the switch open" bench step, and the per-flight checks: J121.2 below 0.1 V and the board off with J400 open, before the e-match goes in | Before order | Yes | Open | §1, row 24 |
| 3 | Servo return through the shared GND pin | The board's share of the servo return is inferred to be at most 0.6144 A (with a 1 A allowance); a servo short loads the harness and pack and can pull the computer down. The motor power and return are not fused on the board. | Measure stall currents and the neutral position; per-servo inline fuses in the harness | Before order | Yes | Open | §2 |
| 4 | Always-on GPS, radio and AUX ports on one supply | One cable fault can remove all three ports (J410, J420, J440) and make the 5.4 V buck hiccup (U401 limits at 1.5–1.9 A). On USB-only power all three are off. | Short test with camera and SD load; installed RF and ESD tests | Before order | Yes | Open | §3 |
| 5 | Hold-up of only 0.46–0.54 ms with all ports on | A break in the battery lead resets the board unless firmware sheds load in time (C84 470 µF, counted as 300.8 µF, plus the PA6 watchdog). With the camera off, logic shed and the card idle the figure is 1.30–1.41 ms. Both include the 100 mA AUX allowance (Calculation/Inference). Both are counted from the battery break. Counted from the PA6 trip, which is where firmware can first act, hold-up is 0.22–0.31 of that: 0.103–0.164 ms with all ports on and 0.291–0.430 ms with the camera off and the logic shed (from the trip window, VLOGIC 4.84–5.17 V; R25-TRI-02, D-R25-02; Calculation / Inference). Whether this is enough is row 25. | PA6 threshold and latency, actual load decay (bench) | Before order | Yes | Open | §4, row 25 |
| 6 | Two single-fault pin-damage cases on diagnostic inputs | A shorted top resistor on the PA6 divider can put 8.4 V on a 4.0 V analog pin; an open bottom resistor on the PB1 divider can bring 5.456 V through 10 kΩ to the pin. The two pyro sense banks (PC0, PC5) are safe for a single fault. | None planned; accept, or ask for a respin of those two dividers | Before order | Yes | Open | §5 |
| 7 | The e-match's 20 ms firing and the 36 ms watchdog guard are calculations on allocations and inferred models | The selected MJG J-Tek is rated 0.75 A for 0.5 s; the 1.125 A floor and the 34.853 ms guard allocation (Calculation on allocations / Inference: the 0.2 / 0.5 / 1.5 ms allocations need bench tests, and the gate-discharge model's 0.4 V off criterion and hot gate charge are inferred) are not measured on your lot and harness. | Selected-lot firing with a dummy load, hot R134 and the real source (bench) | Before order | Yes | Open | §2, §5 |
| 13 | The microSD card is a convenience log | About 2 MB per flight against 16 MB of QSPI (Inference); it adds a hinge that needs the PCB unbolted to open and a 0.825 W write allocation. Keep it, or drop it and the parts listed in REQUIREMENTS F5. | Your choice | Before order | Yes | Open | REQUIREMENTS F5 |
| 22 | Three supply feeds still change layer through one via | U11.2 (RAW_PROTECTED, the only battery path into VLOGIC) and the two 3V3A feeds (VREF+ / VDDA, and the IMU / barometer island) have no legal spot for a second via (measured reasons in §4; re-measured on `1407e850…`, D-R24-06: U11.2's best spot is 0.402 mm from the F.Cu ACT_EN_MCU run against D-R18-03's 0.5 mm floor; 3V3A (16.0, 50.2) would sit 0.131–0.150 mm from U1.1 or QSPI_IO2, with In2 USB_LIMITED below; (27.0, 49.25) keeps D-R19-09's reasons). An open via there cuts the primary computer's battery supply (recovery then falls to the isolated Blue Jay) or the sensor and ADC supply. Five other feeds have two vias (D-R19-09). | First-article pack-only power-up with USB disconnected; a respin item | Before order | Yes | Open | §4 |
| 23 | The AUX port and the identical-port rule | J410, J420 and J440 are electrically identical (pin 1 4.8 V, 2 GND, 3 board TXO, 4 board RXI), so the GPS or the radio can go on any of them. Firmware must keep a port map (default GPS J410, radio J420, AUX spare). The AUX device may draw at most 100 mA at 4.8 V (U401 thermal limit, Calculation/Inference). The camera port J9 is not interchangeable (5.4 V, reversed TX / RX, isolated UART). | Firmware port map; harness check against the printed legends; bench current check | Before order | Yes | Open | §3 |
| 36 | The LS120 buzzer is a +70 °C part: best-effort annunciation in a hot bay (R29-TRI-04, R30-TRI-02) | LS120 (MLT-5020, p2 item 6) is rated −20…+70 °C operating. With the pad load's +10–22 K board rise (Inference) it runs at about 80–92 °C in a 70 °C bay and 65–77 °C at the 55 °C interim limit: out of rating. So buzzer annunciation is best-effort when bay air is above about 48 °C (70 °C − 22 K; Inference), the pre-test estimate: once the chamber test measures LS120's rise, the limit is 70 °C minus that measured rise. Recovery and logging do not depend on the buzzer. | The first-article 70 °C chamber test records LS120's rise over chamber air at the pad load (thermocouple on LS120); LS120 is not a pass / fail gate (R30-TRI-02); respin option: a +85 °C buzzer on the same land | Before order (accept); at first article (test) | No, if accepted | Open | §8, row 33, ORDERING 8.3, REQUIREMENTS Temperature |

**Accepted now, closed by test**

| # | You accept | What it means | Closed by | When | Blocks order? | Owner answer / date | Detail |
|---|---|---|---|---|---|---|---|
| 8 | Routing compromises (M2), layer-change returns, the USB pair and the MEMS stress departure | Detours and extra vias on the 23 nets the §6 table lists (at least +3.5 mm, measured on `a0ec075e…`), five 0603 resistors with a fanout via under the body (R86, R89, R91, R101, R401; R403's went with D-R24-09), BAT_FAULT_N 0.180 mm from a GND via (table and list in §6; R26-TRI-07); 21 of the 25 critical-signal vias, and both J440 pin layer changes (J440.3 / J440.4, counted since D-R26-01), return over an In2 power rail; USB D+ / D− not coupled; copper under U4's body departs from ST TN1383. No fault is shown. | First-article SD / QSPI / USB signal checks; bias, temperature and vibration qualification of the IMU | At first article | No, if accepted | Open | §6, §8 |
| 9 | DB125 insertion and the S-8 margin | S-8 (hole wall to foreign inner copper) nominal minima are 1.021 mm at the PYRO1_OUT via and 1.050 mm at J121.1, the load-switch gate and enable barrels and J400.2: 0.021–0.050 mm over the 1.0 mm floor. Since D-R20-05 J121.1 and J400.2 carry no unconnected inner rings, so their copper is as far as their walls (J121.1 1.050 / 1.050 / 1.061 mm; J400.2 1.050 / 1.050 mm); J121.2 keeps its rings, 0.25 mm from GND, where GND is exempt, and S-8 now measures any ring a barrel keeps (R20-SAF-05 closed). Since D-R26-01 pins 3 and 4 of J410, J420, J440 and J9 carry no unconnected inner rings either, so J440.3 / J440.4's GND partner vias at 1.5 mm meet the 0.55 mm inner-layer PTH hole rule. Side effect: J1.2 (GND) lost its In2 ring, so In2 RAW_PROTECTED is 0.25 mm from that GND barrel (was 0.55) (on `0dc84776…`; D-R21-01 then set inner-layer PTH pad hole to copper at 0.55 mm, so J1.2 is 0.550 mm again on `5516eeec…`, against JLC's 0.3 mm for a PTH pad hole; a component hole is not a via, whose JLC figure is 0.2 mm). Fabricated hole and registration tolerances could eat the margin. | Fabricator allocation in writing; first-article check of all 27 contacts | At first article | No, if accepted | Open | §1, §9 |
| 10 | VCAP capacitors in operation | C19 / C20 meet ST's nominal value; worst-case tolerance, temperature, bias and aging may fall to about 1.52–1.68 µF (Inference). | Bench qualification, or a reviewed X7R part | At first article | No, if accepted | Open | §9 |
| 11 | East-edge terminals carry 34 g of the board mass and there is no east mid-span support | Peak strain 1.2–1.4 millistrain at 100 g at J410, J420, J9, C431 and J400 (reviewer's run on `632a9ad3…`, Inference); The plate model was re-run on `50a39de5…` in round 20 (R20-MEC-02): 180.8 Hz, 78.6 g, 0.261 mm under C431 and 0.320 mm under C421 at 4 mm standoffs (Calculation/Inference); the round 22 mechanics lens re-ran it on `5516eeec…` with identical figures, and the strain values remain the `632a9ad3…` run. | First-article vibration and shock check; at least 4 mm standoffs with underside insulation | After delivery | No, if accepted | Open | §8 |
| 12 | Retention of connectors and tall parts at 5 × 100 g is unproven | No maker pull-out figure exists for any of the parts. The 5 × factor has no flight root (R19-REQ-06): you may restate P3 as 2 × the landing load of the chosen chute (R23-REQUIREMENTS-04, R23-MECHANICS-02: a = v² / 2s with s = 20 mm; a 36 in flat chute gives 6.2–8.0 m/s, so 98–163 g, Inference (R24-TRI-08); about 330 g for a flat 36 in, 220 g for a toroidal), or give an ejection or shock-cord snatch figure that needs more. | Your choice of factor; staking, then a pull and mass test of the first article (M3_R10 retention table) | After delivery | No, if accepted | Open | §8 |
| 21 | Switch-bounce immunity after the C87 change | C87 is now 220 nF (D-R19-10). A single J400 drop-out shorter than 10.3 / 20.1 / 26.0 ms (worst case at 6.0 / 7.4 / 8.4 V) cannot trip U9 (repeated drop-outs add up), and turn-on after a real supply interruption takes 30–130 ms (was 0.31–1.22 s) (Calculation / Inference: C87's X7R bias allowance, ≤ 6 % in its 0.72× minimum, is an Inference). The low-voltage corner is tighter: worst case 10.3 ms at 6.0 V (above 10 ms for a single drop-out); about 8.1 ms at the four-stall 5.71 V (8.07 ms; D-R26-03, R26-TRI-02) and 6.3 ms at 5.5 V fall below it, so a single 10 ms drop-out needs a loaded pack of at least 5.96 V (D-R24-19, with U9's ±0.1 µA EN leakage plus D402's ≤ 50 nA; Calculation / Inference, TI SLVSFC9C p9; R24-TRI-02; without D402, D-R20-11 gave 10.6 / 8.5 / 6.6 ms, 30–129 ms and 5.92 V). The 19.7 / 24.4 % trip fractions at 5.71 / 6.0 V hold only for very short drop-outs; longer drop-outs trip at a lower open fraction (5.71 V: 19.6 % at 0.1 ms, 14.8 % at 4 ms, 4.5 % at 8 ms; 6.0 V: 24.3 % at 0.1 ms to 8.3 % at 9.9 ms; Calculation / Inference, guidance only; D-R26-03). | Bench chatter test of the chosen switch: record the J400 contact state at 10 kS/s or faster under flight-level vibration; pass only if the total open time in every sliding 100 ms window is under 7 ms and U9 stays on for the whole run at 5.71 V, the fire budget's four-stall BAT_IN (worst-corner limit 7.50 ms at 5.71 V, 9.59 ms at 6.0 V, 5.87 ms at 5.5 V, so the 7 ms line leaves 0.50 ms and holds down to 5.65 V; the worst admissible train is one open block per 100 ms placed late in the window (exchange argument), which trips U9 at 7.50 ms at 5.71 V (7.63 ms at 5.73 V) and at the 7 ms pass line holds EN at 1.1295 V (1.1330 V at 5.73 V) against the 1.116 V threshold; Calculation / Inference, R25-TRI-01, D-R25-01, corrected by D-R26-03 for R26-TRI-02 / -03). A switch that fails may still pass on a replay of its recorded waveform through the worst-corner EN model; raising C87 (BOM only, same land) stays the owner's alternative. This one rule replaces both the < 10 ms single-drop-out rule and the < 18 % open-fraction rule. The root's round 24 < 18 % decision was wrong and is corrected here: 8 ms open every 50 ms (16 %) takes EN to 1.095 V at 6.0 V, and 3 × 4 ms with 0.2 ms closures (12 %) takes it to 1.028 V at 5.73 V (1.025 V at 5.71 V), both below 1.116 V; otherwise re-size C87 (BOM only, same land) | At first article | No, if accepted | Open | §4, REQUIREMENTS F6 |
| 24 | U9 EN-node leak paths and switch-off | U9.1 (EN) is 0.200 mm from U9.5 (IN) under the QFN; the BAT_ENABLE via (17.1,82.8) is 0.200 mm from BAT_FAULT_N on `92c3ad59…` and `a0ec075e…` (0.173 mm on `1407e850…`, where D-R24-17's chamfer narrowed it, R24-TRI-01; D-R24-18 capped it); R123.1 (ACT_EN) is 0.330 mm from BAT_ENABLE; the J400.2 lead runs at EN potential. A leak or chafe there can keep the board on after J400 opens. J440's leads leave the same west edge: a chafe from J440.1 (4.79 V) or J440.3 (TX) onto J400.2 holds EN at 1.87 V or 1.28 V, above VUVLO(F) max 1.116 V (Calculation), so J400 could not switch the board off. These are fixed by TI's land or U9's fan-out and stay. | Coat U9, R80, R81, R165, C87 and the BAT_ENABLE vias and tracks; per-flight switch-off check with J400 open; the per-flight closed-switch check with a 1–2 Ω dummy load in J121 (ORDERING 8.3, R23-SAFETY-01) is the only per-flight screen of the three PC1 / bus pairs (ACT_EN 0.330 mm, ACT_EN_MCU 0.5205 mm, RAW_ACT 0.5008 mm to BAT_ENABLE), because only with the bus enabled are they energised; twist the J400 pair and dress it away from battery and servo power and from J440's leads (ORDERING 8.3, 8.4) | At first article and every flight | No, if accepted | Open | §1 |

**Do (a decision or an action)**

| # | You do | What it means | Closed by | When | Blocks order? | Owner answer / date | Detail |
|---|---|---|---|---|---|---|---|
| 14 | Decide the AUX cost overrun and fix the stock | Live JLC (2026-11-02T12:44:13Z, final files of `a0ec075e…`; re-run because the round 26 fix pass moved four CPL rows, with the BOM and owner BOM byte-identical): parts $60.47 + feeder fees $24.79 (81 codes × $1.53 / 5) = **$85.26 per board against the $84.41 cap (R3's cost per board): M3 not met, $0.85 over** (it was $85.60 at 2026-11-02T01:43:55Z on the same BOM; the $0.34 is JLC price movement on eight lines; $85.36 before D402, which added its ninth C535146 piece at $0.2306). In round 19 items 1–13 alone gave $84.21 and the AUX port added $1.14. Accept the overrun, or change the AUX parts (changing its ESD or 22 µF breaks the identical-port intent). With JLC's fixed fees ($83.96 per order, two-sided = $16.79 per board) about $102.05; with the possible handling fee ($14.93 per order) about $105.04, before PCB, VIPPO, manual C84, shipping and tax. Stock (`stock_check.json` 2026-11-02T12:43:17Z): the check fails on U4 (ISM6HG256XTR, C51931514: 9 in stock, only 2 orderable against 5; LCSC 0) and on U9 (TPS259470LRPWR C3662793: 30 in stock, −81 orderable, minimum purchase 7); C535146 (now 9 per board) has 196 in stock, 189 orderable, against 45. The check reads JLC's `canPresaleNumber` as the orderable quantity, an Inference about JLC's field. For both, confirm in the JLC cart on order day, else consign franchised parts (R20-BOM-01). Add U4 to the JLC cart first on order day and confirm the quantity before paying; if short, consign franchised ISM6HG256XTR (same CPL rotation and register map), with the LSM6DSV320X, also unavailable at JLC and LCSC, only as a second fallback (R21-BOM-02). No franchised source had either fitted part in stock on 2026-11-01 (DigiKey: U9 due 14-Dec-2026, U4 due 22-Mar-2027). So choose one of ORDERING 8.1's options: wait; order with U4 / U9 unfitted; a partial order; or a same-land alternate, either TPS259470ARPWR for U9 (it retries every 110 ms instead of latching off) or the LSM6DSV320XTR for U4 (in stock at the ST eStore). The alternates are in `round22_alternates.md`. | Your decision; a quote and a fresh supplier run within 24 h of ordering | Before order | Yes | Open | §10, ORDERING 8.1 |
| 15 | Get JLC's written agreement | Tab and rail plan, filled-and-capped vias on U401 (or the fallback in ORDERING 8.1), C84 left out of the upload (its lands have no paste) and fitted by hand after reflow, no washing, two reflows for U5, hand or selective soldering of the terminals. | JLC confirmation before payment | Before order | Yes | Open | ORDERING 8.1 to 8.2 |
| 16 | Choose the tab plan | Four long-edge tabs (all legal since the AVA placement) or your recorded aft-edge tab with an aft rail. The east tabs stay over In2 power (row 28; D-R24-14, measured on `1407e850…`). | Your choice, then JLC's acceptance | Before order | Yes | Open | ORDERING 8.1 |
| 17 | Select the pack, and the pad-energy basis | Use the single worksheet: tested capacity at least (pad + motors + flight + recovery charge) / 0.8, the fire-time 7.4 V-equivalent source and resistance, and the real bay fit. Several of its margins have no measured root (R19-REQ-01); ORDERING 8.1.1 lists each one. Choose the worksheet's conservative basis or the re-based one. | A tested pack | Before flight | No | Open | ORDERING 8.1.1 |
| 18 | Decide the pad-check policy | Whether firmware should return PC1 low after the on-rail check and re-enable it only on confirmed launch detection (keeps both series FETs off while people are near the vehicle). Not adopted; it changes the accepted single-switch design. | Your decision, then firmware | Before flight | No | Open | M3_R10 Firmware |
| 19 | Update the parent vehicle record | `../../docs/VEHICLE.md` still describes GH ports, an ARM terminal and a coax loop zone. It is separately owned. | Apply the handoff text in that repository | Before flight | No | Open | §11, handoff |
| 20 | Accept the list, and the agent decisions | Accept or reject the rows above, the 229 agent decisions through D-R29-02 and the 23 owner mandates. The first 126 decisions are indexed in `r10_final_deviations.json`; the 103 later ones are in the table "Decisions after the ledger" below. Rounds 22 and 23 on `5516eeec…` were the closing pair, both 0 Critical / 0 Major; the round 24 board pass made `1407e850…`, round 24 found 17 real errors on it, and the round 24 fix pass made `92c3ad59…`; rounds 25 and 26 found 10 and 12 real errors on it, the round 26 fix pass made `a0ec075e…`; rounds 27, 28, 29 and 30 found 7, 9, 5 and 2 real errors on it (none on the board), and rounds 31 and 32 review that board. | Your dated acceptance | Before order | Yes | Open | §12, Round 19 |
| 25 | State the hold-up requirement (open question, R19-REQ-07) | No document says how long the logic must stay alive after the PA6 watchdog fires. The PA6 trip window is VLOGIC about 4.8–5.2 V (PA6 0.44–0.47 V): above U9's 4.80 V BAT_IN turn-off corner (4.78 V before D402's leakage, D-R24-19) and below the four-stall-plus-fire corner: BAT_IN 5.71 V with a healthy match (the fire budget's four-stall point, which already includes the 1.28 A fire current), 5.55–5.56 V with the match shorted and 5.50 V with the match and leads shorted, VLOGIC 0.09–0.16 V lower (fire_current_GAP1 model, Calculation / Inference; R26-TRI-04, D-R26-03; the earlier 5.37 V counted the fire current twice), to be qualified with the divider and ADC tolerances (R23-POWER-01). Hold-up after the trip is 0.103–0.164 ms with all ports on and 0.291–0.430 ms with the camera off / shed (Calculation / Inference from the trip window, VLOGIC 4.84–5.17 V, at 300.8 µF; 0.22–0.31 of the break-to-3.8 V hold-up; R25-TRI-02, D-R25-02); the earlier 0.157–0.182 / 0.44–0.48 ms ("about a third") were computed from 5.3 V, above the window. The earlier "100–220 µF would do" is struck: from the trip, 100–220 µF gives 0.03–0.12 ms (R25-TRI-03). If the need is one QSPI page program (tPP 0.4 ms typical, 3 ms maximum: [Winbond W25Q128JV](https://www.winbond.com/resource-files/W25Q128JV%20RevI%2008232021%20Plus.pdf), AC Electrical Characteristics table, as quoted by the round 19 requirements lens; page not re-read in this pass), 470 µF is not enough with the ports on (0.725–0.842 ms, Calculation / Inference). No design change is made now. | Your answer, then a bench measurement of the PA6-to-shed time | Before order | No | Open | §4, REQUIREMENTS F6 |
| 26 | U401 thermal margin with the AUX allowance (provisional) | **The AUX allowance and the port allocations' thermal margin are provisional** (R20-PWR-01): the 123.9 °C figure counts only U401's own heating, while in the same case U400 and L400 (8.7–13.4 mm away, centre to centre) lose 1.2–2.2 W and logic and SD writes 1.4–2.2 W on a board with roughly 10–15 °C/W to the bay air (Inference), and U400 has no junction estimate (about 0.46 W, roughly 41 °C rise at 89 °C/W, Diodes DS41326 p4). Worst outcome: GPS, radio and AUX lost together (thermal shutdown); no pyro hazard. With 100 mA on AUX the port LDO carries 0.56 A in all, within its 1 A rating ([TI SBVS282A](https://www.ti.com/lit/ds/symlink/tps7a91.pdf) pp. 4–5). The junction reaches 123.9 °C at the 70 °C bay limit on the inferred 110 °C/W, against TJ ≤ 125 °C: a 1.1 °C margin that rests on an Inference (the JEDEC RθJA is 62.5 °C/W, but the board's real figure is unmeasured) (round 19 circuit check, Calculation). | First-article power-knot measurement: thermocouples on U401, U400 and L400 at the allocation loads (camera 1 A, 0.56 A on PORT_4V8, SD writing) in 70 °C air, before relying on the AUX allowance (ORDERING 8.3). Hot-end ratings are judged against part temperature, not bay air (R23-PARTS-01, R23-MECHANICS-03): see row 33 | At first article | No, if accepted | Open | §4, M3_R10 Power |
| 27 | Next board change: what is still open (round 26) | Fixed by the round 20 polish pass: the U401 FB tap at R402.1 (D-R20-02), the U1.74 fragment (-03), TP82's stub (-04), the J121.1 / J400.2 inner rings (-05), the courtyard designators and Fab-reference crossings (-06, -07) and the AUX clamp distance (-09). Fixed by the round 21 fix pass: the PTH hole clearances (D-R21-01), U2.1's second path (-02), BAT_ENABLE's jog (-04) and R81 / C87 at U9 (-05). **Fixed by the round 24 board pass (`1407e850…`):** second barrels at Q120's and Q121's gates (D-R24-02), BOOT0 (-03), VCAP2 (-04), U402.2 / R430.2's GND island (-07), the PA6 / PA4 / R91 monitor taps (-08) and R87.1's input layer change (16, 28) (-10); U401's FB divider beside U401 on B.Cu with no via (-09); J400.2's ESD clamp D402 (-11, R22-REQUIREMENTS-03 / R23-SAFETY-06); the order-number placeholder removed (-13, row 35); R92 and TP88 off the short edge (-15); every 90° bend chamfered (-17). **Fixed by the round 26 fix pass (`a0ec075e…`):** the J440.3 / J440.4 GND partner vias (D-R26-01), PYRO1_OUT's spacing to 3V3 / 3V3A, at least 1.040 mm (D-R26-02), and Q124's gate nets' spacing to 3V3 / 3V3A, at least 1.0585 mm (D-R26-04; the pass's first layout, the intermediate `4108e6fa…`, had put R164's 3V3 via 0.331 mm from R126.1 on PE4's net, which the round 26 docs lane found). **Made nearer and not restored (D-R26-04):** BUZZ_DRV to PYRO1_OUT, 0.794 mm (R162.1 to R173.1; 0.964 mm on `92c3ad59…`; a bridge may fire an enabled match, Inference, §1): R173 cannot go back south without losing the 3V3 clearance, and R162 cannot move 0.2 mm east without its courtyard crossing R163's, nor north without crossing R164's via route. **Still open, with measured reasons (respin items):** U9's west cell (the one via left on EN, row 29; D-R24-05); U4.6 / U4.7's GND via (16.75, 47.60) (an open: IMU dead, primary does not fire, roll control lost; the legal region holds one via, and a second needs U1.98's IMU_INT1 escape or the F.Cu QSPI_IO2 run moved; D-R24-01); VCAP1's via (C19 boxed on B.Cu, U1.48's pad east on F.Cu; needs U1.49's GND via moved; D-R24-04); row 22's three feeds (D-R24-06); the U10.2 / R7.2 / R85.2 GND island (enclosed by the VBUS ring, already two vias) and R8.2 (every spot under D4 / USB_DP or In2 USB_LIMITED) (camera / bench-USB loss only, Inference; D-R24-07); R87.1's drop (22.0, 62.25) (the only spot necks the In2 3V3 fill under 0.5 mm) and R85.1 (no legal spot within 1.6 mm) (an ILIM open lowers the limit: fail-safe per TI SLVS841G §8.5.1 p16; the open-pin case is an Inference; D-R24-10); the east panel tabs (row 28; a plane redesign, D-R24-14); the GPS pair's forced jogs (R20-RTE-03) and the VLOGIC in-line via pair (R20-RTE-04), optional cleanliness (D-R24-16); the J440.1 / J9.1 unconnected In2 rings and the In2 3V3 spacing to RAW_PROTECTED (R21-SAFETY-03 respin options). Short-edge parts C95, R166, R400 / R401 / R404 and C403 stay expected DFM queries (each needs 0.5–1.5 mm of a re-laid maker loop or hot-plug feed; D-R24-15). Fab body outlines for 14 parts stay deferred (D-R24-12): no stated rule requires them, and the Fab references keep using the courtyard box (D-R22-06). | Accept these as recorded for this board | At acceptance; CAD at the next board change | No, if accepted | Open | §1, §6 |
| 28 | East panel tabs over In2 RAW_PROTECTED (R20-MFG-01, D-R20-08) | The west aft tab now has an In2 keep-out (no copper under it). Both east tabs and the aft-edge alternative still sit over In2 RAW_PROTECTED (the east aft also PORT_5V3 in its 3 mm band); a keep-out there would cut the In2 RAW_PROTECTED fill (no links, or a 0.45 mm neck). Re-measured on `1407e850…` (D-R24-14): the In2 RAW_PROTECTED strip (x 44.0–45.7, y 4.4–63.3, U400's forward feed) and the PORT_5V3 band (x 41.0–43.7) run side by side along the whole east edge, and the strip joins the forward RAW region only at y 63.3, so any east tab band (x 43–46) lies over one of them; moving both inboard is a plane redesign, not a local move. R8 / R9 required GND only under every tab. | Choose: tabs only over GND (the west aft tab and west y 51.75–66.25; JLC acceptance unconfirmed), or accept the east tabs as a deviation (ORDERING 8.1) | Before order | Yes, until chosen | Open | §9, ORDERING 8.1 |
| 29 | U9 EN reaches its pull-down through one via (R20-SAF-01 / R21-SAF-01; D-R21-05; kept by D-R24-05) | Re-measured on `1407e850…` (D-R24-05): with U9's input trunk re-laid (D-R24-17), the B.Cu pocket at U9.1 is about 1.4 × 2.2 mm against the roughly 2.0 × 2.45 mm R81 and C87 need, with their GND an island enclosed by BAT_IN and BAT_OVLO; a via pair from the F.Cu EN node fits only with BAT_FAULT_N's F.Cu run at y ≥ 83.6, where it meets the hot-plug damper's BAT_DAMP run (y 84.7). Since D-R21-05 R81 (F(18.8482,80.0)) and C87 (F(18.7232,81.8768)) sit at U9's end of the EN run: EN reaches them from U9.1 through one via, (17.10,82.80), over 3.890 mm (was three vias and about 20.9 mm on `0dc84776…`). The single opens between U9.1 and R81 dropped from 13 to 4. If that via opens, EN floats 0.2 mm from BAT_IN, so the board could come on with J400 open (Inference). With C87 beside R81, EN stays at the divider's 2.03 V nominal (≤ 2.06 V with 1 % parts, at 8.4 V; Calculation) while R81 is intact (EN/UVLO absolute maximum 6.5 V, TI SLVSFC9C §6.1 p7). | Accept as a deviation; rely on JLC's Flying Probe Full Test of every bare board (ordered explicitly, with its fee in the quote; ORDERING 8.1, R23-MANUFACTURING-01) and the per-flight check (board off with J400 open; opening J400 turns it off after any closed-switch check, ORDERING 8.3); respin: re-lay U9's west cell with the OVLO divider (R82 / R83) and the R82 / R167 tap moved west | Before order; every flight | No, if accepted | Open | §1, FMEA H-6 |
| 30 | The J400 switch chain is exempt from the 1.5 mm GND partner-via rule (AUD-2, D-R21-04) | D-R21-04 made BAT_SW_SOURCE, BAT_SW_RETURN and BAT_ENABLE critical in route_check and put them on the AUD-2 slow list. No via in the chain has a GND via within 1.5 mm (measured on `5516eeec…` by the pre-commit circuit check): BAT_ENABLE (21.3,68.9) 1.866 mm; BAT_ENABLE (19.675,66.6) 1.875 mm (1.423 mm on `0dc84776…`, to the GND via the R81 move removed); BAT_ENABLE (17.1,82.8) 2.902 mm; BAT_SW_SOURCE (10.8,69.2) 7.467 mm. Reason: the exemption rests on physics, not on lack of room. These are DC switch nodes filtered with tau about 50 ms and carrying about 7 µA, while the partner-via rule protects return-current continuity for fast edges (Inference that no fast edge exists on them in normal use). The project's GND-via spot search finds a legal spot 0.671 mm from three of the four vias and none for (17.1,82.8) (round 22 requirements lens, R22-REQUIREMENTS-01); adding those three vias is a board-change option, not recommended for the closing pair. Hygiene, S-8 and connectivity still apply in full. | Accept the exemption for this board | Before order | No, if accepted | Open | §6, AGENTS §3 |
| 31 | OQ-1 wire gauge narrowed to 20–22 AWG (R23-MECHANICS-01) | No 18 or 16 AWG lead can make its 90° turn in the 5.003 mm wire room. R10 terminal leads are capped at 20 AWG (22 AWG preferred; the e-match leads are 24 AWG), insulation OD ≤ 1.8 mm, with the bend starting at the wire face at an inner radius of about 1 × OD, a recorded deviation from 3 × OD practice (Calculation; REQUIREMENTS P2). With the 0.5 mm wall allowance the room is 4.493 mm (was quoted 4.503). The physical fit check stays pending. | Accept 20–22 AWG in place of OQ-1's 16–22 AWG | Before order | No, if accepted | Open | REQUIREMENTS P2, ORDERING 8.4 |
| 32 | Landing basis and chute choice (R23-MECHANICS-02, R23-REQUIREMENTS-04) | P3's load comes from the chosen chute: a = v² / 2s with s = 20 mm crush. A 36 in flat chute gives 6.2–8.0 m/s, so 98–163 g (Inference; R24-TRI-08), which can exceed the 125 g at which the plate model puts C431 onto a 4 mm sled (C421 at 133 g; plate model, Calculation / Inference; R25-TRI-10). Vehicle item: a sled relief pocket at least 1.5 mm deep under C411 / C421 / C431 (x 31.5–41, y 20–60), or 4.5 mm standoffs with a plate thinner than 0.8 mm (h + t < 5.3 mm at x 3.7; R25-TRI-09). | Choose the chute (descent rate at the computed descent mass); accept the sled relief or standoff change | Before flight | No, if accepted | Open | §8, REQUIREMENTS P3 |
| 33 | Thermal qualification and the ≤ 55 °C interim site limit (R23-MECHANICS-03, R23-PARTS-01) | Hot-end ratings are judged against part temperature, not bay air. The pad load, 1.0–1.5 W, gives +10–22 K over the bay; camera and ports at full load, 2.6–4.4 W, give +26–66 K (Inference, 10–15 °C/W board-to-air). The fitted 85 °C parts (MS5611, the AP6320x bucks, J430) therefore have no margin at a 70 °C bay. The LS120 buzzer is a +70 °C part (MLT-5020 p2 item 6), out of rating at a 70 °C bay (row 36). A 70 °C bay also exceeds the usual 60 °C LiPo discharge limit (vehicle item). | Extend the first-article 70 °C chamber test at the pad load profile, logging MS5611 TEMP, U4's temperature register, the U400 / U2 cases, C6 / C7, C89 and near Y1 / U3; pass if every 85 °C part ≤ 85 °C; also record LS120's measured rise over chamber air (thermocouple on LS120), which is not a pass / fail gate and sets the bay-air limit for best-effort buzzer annunciation (row 36; R30-TRI-02). Until it passes, the site limit is bay air ≤ 55 °C (shade the vehicle; camera off on the pad until shortly before launch, or qualify the full-load case). If it fails: a camera / port duty limit on the pad, or X7R parts on the same lands at the next board change | Before order (site limit); at first article (test) | No, if accepted | Open | §8, ORDERING 8.3 |
| 34 | The Flying Probe Full Test fee (R23-MANUFACTURING-01) | JLC's free default electrical test is a random sample. Row 29's mitigation needs every bare board tested, so the order selects "Flying Probe Full Test", which has a fee. | Accept the fee in the quote | Before order | Yes, until accepted | Open | ORDERING 8.1 |
| 35 | Order-number mark leftover (R23-MANUFACTURING-02) | **Closed by D-R24-13 on `1407e850…`:** r10_post no longer draws the "JLCJLCJLCJLC" placeholder and K-legends no longer admits it (`test_silk_allowlist` fails it). JLC withdrew the order number in May 2026; the order form selects "Mark on PCB: none / Remove Mark". | None (closed) | — | No | Not needed (closed by D-R24-13) | ORDERING 8.1 |

**Row 2 residuals (surface; measured on `a3144b15…` unless a later figure is given).**

- PYRO1_CONT_MID is 0.250 mm from R134.2 and 0.175 mm from Q123.1, behind R173 5.1 kΩ (on `a0ec075e…` its D-R26-04 diagonal is 0.2005 mm from Q123.1 and 0.386 mm from R134.2, so the run keeps both minima). A RAW_ACT bridge there adds only a 5.1 kΩ path (at most 1.65 mA), far below fire current. It raises the powered-bus CONT reading to about 1.38 V against about 0.75 V intact (at 8.4 V); a firmware band can flag it (Inference).
  With an open match the same bridge gives cold readings CONT / BUS 102.0 / 55.5 mV, close to the healthy cold 96.2 / 96.1 mV (at Vf = 0.30 V; the nominal Vf = 0.20 V table in parts_qualification gives 99.369 / 99.338 mV; Calculation / Inference: the BAT54 drop at that current is an Inference), so the cold screen needs a BUS lower band as well as a CONT upper band (R19-SAF-04).
- PYRO1_OUT to GND surface approaches 0.177 mm (track to the GND via (15.85,57.70)) and 0.180 mm (Q124.5 to the GND via (12.78,59.02)), and on `a0ec075e…` R173.1 to Q124's source via (15.85,58.345), 0.500 mm: each fires an enabled match by itself (row 1). PYRO1_OUT is at least 1.040 mm from 3V3 and 3V3A since D-R26-02 (0.5135 / 0.5662 mm before; R26-TRI-01).
- R173.1 (PYRO1_OUT) to R162.1 (BUZZ_DRV), 0.794 mm on `a0ec075e…` (the net pair's minimum was 0.964 mm on `92c3ad59…`; nearer since D-R26-02 moved R173): a bridge may fire an enabled match (Inference, D-R26-04; §1). Q124's gate nets are at least 1.0585 mm from 3V3 / 3V3A since D-R26-04.
- The U9 EN-node pairs of row 24, and the other pairs of the §1 inventory.
- Everything else sits in the ordinary 0.15 mm surface clearance class.

**Decisions after the ledger (D-R18-01 … 11, D-R19-01 … 15, D-R20-01 … 11, D-R21-01 … 09, D-R22-01 … 07, D-R23-01 … 11, D-R24-01 … 23, D-R25-01 … 03, D-R26-01 … 04, D-R27-01 … 03, D-R28-01 … 04, D-R29-01 … 02).** Full text in `R10_DECISIONS.md`.

| ID | Effect | Board change? |
|---|---|---|
| D-R18-01 | R123 100 kΩ → 2 kΩ (PC1 pull-up cannot turn Q122 on); V3V3_SENSE divider removed, PC3_C NC | Yes |
| D-R18-02 | Q121 gets its own via-free gate–source resistor R119 | Yes |
| D-R18-03 | PC1 enable run spaced from reset-high nets | Yes |
| D-R18-04 | Inner copper held 1.05 mm from the load-switch gate and enable barrels | Yes |
| D-R18-05 | CH1 sense branches moved off the fire-current pads (R173 at the OUT end) | Yes |
| D-R18-06 | In2 3V3 fill made one piece; K-plane rule | Yes |
| D-R18-07 | SD_MOSI straightened | Yes |
| D-R18-08 | Bourns land for L400; 0.15 mm mask webs on U4 | Yes |
| D-R18-09 | Stocked R430; C84 hand-fitted outside the JLC upload | Yes (BOM and fab package) |
| D-R18-10 | Schematic notes and pin-record text corrected | No (text) |
| D-R18-11 | Gate hardening (K-power, K-lands, fab content checks) | No (checks) |
| D-R19-01 | In1 / In2 GND held about 1 mm from the PYRO1_OUT barrels; S-8 counts GND there | Yes |
| D-R19-02 | BAT_ENABLE via moved off R134.2 (0.300 → 0.500 mm) | Yes |
| D-R19-03 | TP121 and its ACT_GATE stub removed | Yes |
| D-R19-04 | C123 10 nF on Q122's gate (full AGENTS §2.4 network) | Yes |
| D-R19-05 | No pour connection on U1.19 (unstitched fragment gone) | Yes |
| D-R19-06 | One word list; GPS and RADIO inside their own terminal's span | Yes (silkscreen) |
| D-R19-07 | No stencil aperture on the hand-fitted C84 | Yes (paste) |
| D-R19-08 | Terminal legends outside the DB125 bodies, one terminal per line | Yes (silkscreen) |
| D-R19-09 | Second vias on five single-via supply feeds | Yes |
| D-R19-10 | C87 2.2 µF → 220 nF | Yes (part value) |
| D-R19-11 | U4 ISM6HG256XTR fitted; LSM6DSV320X the second-fallback alternate (needs part fields, BOM and CPL regenerated: ORDERING 8.1) | Yes (part) |
| D-R19-12 | Fixed spots for nine designators | Yes (silkscreen) |
| D-R19-13 | MCU text: port UART enable on U11's status, one DS12110 revision, VREFBUF, sheet notes | No (text) |
| D-R19-14 | Spare AUX port J440; J410 / J420 / J440 electrically identical (owner approval 2026-10-30) | Yes |
| D-R19-15 | Gate hardening (pad paste / mask, MPN decode, plane necks, power-path currents, word margins, silkscreen allowlist, pour debris); the port UARTs stay under the strict rules | No |
| D-R20-01 | U9's EN pull-down stays at the switch end: no legal B.Cu spot at U9.1 (not done; owner row 29) | No |
| D-R20-02 | U401's feedback tap joins the output after both OUT vias; K-power checks single-via opens | Yes |
| D-R20-03 | No pour connection on U1.74 | Yes |
| D-R20-04 | TP82 on the USB_LIMITED diagonal's extension | Yes |
| D-R20-05 | J121.1 and J400.2 drop their unconnected inner rings; S-8 measures rings | Yes |
| D-R20-06 | Designators: C400 moved, C94 and R461 hidden; the gate's named entries deleted | Yes (silkscreen) |
| D-R20-07 | Fab references clear of their own Fab outlines | Yes (Fab only) |
| D-R20-08 | No In2 power copper under the west aft tab; the east tabs need the owner's tab plan | Yes |
| D-R20-09 | AUX clamps under J440 on the bottom | Yes |
| D-R20-10 | Optional cleanliness (VLOGIC via pair, GPS jogs) not done | No |
| D-R20-11 | C87's drop-out immunity includes the EN leakage | No (text) |
| D-R21-01 | Inner-layer PTH pad holes 0.55 mm from copper; JLC's hole table pinned in K-rules | Yes (DRU and refill) |
| D-R21-02 | U2.1 has a second path; every regulator FB / OV / EN / ILIM tap held through one named list | Yes |
| D-R21-03 | Three schematic notes corrected | No (sheet text) |
| D-R21-04 | J400's arming chain is critical in route_check; its B.Cu jog is gone | Yes |
| D-R21-05 | R81 and C87 at U9's end of the EN run | Yes |
| D-R21-06 | Panel-tab keep-out and tab-band copper held by K-plane | No (check) |
| D-R21-07 | Port ESD clamps held beside their pins (K-ports) | No (check) |
| D-R21-08 | Fab references present, readable and apart (K-legends) | No (check) |
| D-R21-09 | Designators re-placed by the post search | Yes (silkscreen) |
| D-R22-01 | K-rules measures the rest of JLC's hole, ring and NPTH rows on the board | No (checks) |
| D-R22-02 | The TPS2553 grounds, the CC Rd returns and the power-state monitors are single-open taps | No (checks) |
| D-R22-03 | Diagnostics sheet note: R10's camera supply and the real worst cases | No (note text) |
| D-R22-04 | Record corrections | No (records) |
| D-R22-05 | K-rules reads every DRU minimum and layer, and measures three more JLC rows on the board | No (checks) |
| D-R22-06 | Fab references held to their own part; stroke floor; no board-level Fab text | No (checks) |
| D-R22-07 | Port clamp ground returns held through tracks (K-ports) | No (checks) |
| D-R23-01 | BOOT0's pull-down and the VCAP capacitors are exact single-open entries | No (checks) |
| D-R23-02 | Q120's / Q121's gate vias are exact single-open entries | No (checks) |
| D-R23-03 | Binding-note obligations (firmware rules 1–13), the sensors note and pin-table notes | No (note text / records) |
| D-R23-04 | JLC's order-number mark withdrawn; the placeholder stays until the next board change | No (records) |
| D-R23-05 | K-rules reads the DRU as KiCad does | No (checks) |
| D-R23-06 | The JLC board measures take S-8's copper set | No (checks) |
| D-R23-07 | Every DRU minimum floored; error severity only | No (checks) |
| D-R23-08 | Fab labels: text boxes, visible fields, character width, board-level shapes | No (checks) |
| D-R23-09 | r10_parts' footprints SHA-pinned; paste totals pinned | No (checks) |
| D-R23-10 | check.sh runs the schematic contract and its sheet replay | No (checks) |
| D-R23-11 | U4's power-ground via is an exact single-open entry | No (checks) |
| D-R24-01 | U4.6 / U4.7's ground via stays single: no second legal spot | No (kept, measured) |
| D-R24-02 | Second barrels for Q120 / Q121's gate drive; named parallel vias leave the via count and hop test | Yes (and checks) |
| D-R24-03 | BOOT0's second via | Yes |
| D-R24-04 | VCAP2's second via; VCAP1 stays single | Yes (VCAP2) |
| D-R24-05 | U9's EN pull-down stays across one via | No (kept, measured) |
| D-R24-06 | Row 22's three feeds stay single | No (kept, measured) |
| D-R24-07 | U402's GND island gets a second via; U10 / R8 keep theirs | Yes (U402) |
| D-R24-08 | Second vias for the power-state monitor taps | Yes |
| D-R24-09 | U401's feedback divider beside U401 on B.Cu | Yes |
| D-R24-10 | USB OV and ILIM legs | Yes (R87.1 (16, 28)) |
| D-R24-11 | J400.2's ESD clamp D402 fitted | Yes (and checks) |
| D-R24-12 | Fab body outlines: not drawn in this pass | No (deferred) |
| D-R24-13 | JLC's order-number placeholder removed | Yes (silkscreen; and checks) |
| D-R24-14 | East panel tabs stay over In2 power: deviation kept | No (kept, measured) |
| D-R24-15 | Short-edge parts: R92 and TP88 moved; the rest stay expected DFM queries | Yes |
| D-R24-16 | Optional cleanliness: not taken | No |
| D-R24-17 | Every 90-degree bend chamfered; route_check fails any that remain | Yes (and checks) |
| D-R24-18 | BAT_FAULT_N's chamfer at the EN via capped (R24-TRI-01) | Yes |
| D-R24-19 | Generated EN text: D402's leakage, the pack windows and the second vias (R24-TRI-02 / -03 / -04) | No (sheet note and binding note) |
| D-R24-20 | M-8: courtyards 2.5 mm from the rail-less short edges (R24-TRI-15) | No (checks) |
| D-R24-21 | BOOT0's second via cited as D-R24-03 (R24-TRI-16) | No (comments) |
| D-R24-22 | check_actuators names R10's own switch pins (R24-TRI-17) | No (check messages) |
| D-R24-23 | round24_board_cad: the CPL counts (R24-TRI-13) | No (record) |
| D-R25-01 | The J400 chatter bench criterion: a sliding 100 ms window (R25-TRI-01) | No (binding note and sheet note) |
| D-R25-02 | Rule 8's hold-up over the PA6 trip window (R25-TRI-02) | No (binding note) |
| D-R25-03 | U9's OVLO corner includes the OVLO pin leakage (R25-TRI-04) | No (parts budget) |
| D-R26-01 | GND partner vias at J440.3 / J440.4; route_check counts a plated pin's layer change (R26-TRI-09) | Yes (and checks) |
| D-R26-02 | PYRO1_OUT held 1.0 mm from 3V3 and 3V3A: C10, C11, R164 and R173 moved (R26-TRI-01's respin item) | Yes |
| D-R26-03 | Generated text: the four-stall point with the AUX allowance, the late-block chatter train, rule 8's corner (R26-TRI-02 / -03 / -04) | No (binding note) |
| D-R26-04 | Gate nets held 1.0 mm from 3V3 and 3V3A, C10 back to 3.0 mm from U5, and a whole-board adjacency audit (round 26 follow-up) | Yes (and checks) |
| D-R27-01 | The budget's four-stall pack sag counts the AUX allowance (R27-TRI-02) | No (parts budget) |
| D-R27-02 | The binding note's DS12110 revision sentence names its two Rev 11 limits (R27-TRI-04) | No (binding note) |
| D-R27-03 | J410 / J420 / J440 get their own schematic symbol, M3:PortTerminal (R27-TRI-07) | No (schematic, netlist and a check) |
| D-R28-01 | The four-stall pack sag uses the ports' 1.461 A plus the AUX allowance, as `ports_w` does (R28-TRI-03) | No (parts budget) |
| D-R28-02 | Rule 3's first-article meter check reads both polarities (R28-TRI-05) | No (binding note and a test) |
| D-R28-03 | Rule 3's gate-fight figures and five more obligations carry their Inference labels (R28-TRI-09, AGENTS §2.5) | No (binding note and a test) |
| D-R28-04 | Rule 4's Q120 pass criterion, the port supply's lead over 3V3 and rule 3's "before first power" (siblings) | No (binding note and a test) |
| D-R29-01 | Rule 3's gate time constant covers C126's full ±10 %: about 47–58 µs (53 µs nominal; Calculation, driver resistances Inference; R29-TRI-02) | No (binding note and a test) |
| D-R29-02 | The binding-note test pins every label D-R28-02 … -04 added, the turn-on label among them (R29-TRI-05) | No (a test) |

### Inventory basis

Inventory for PCB `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, 46 × 90 mm. It was carried to `0dc84776…` with the D-R20 changes, to `5516eeec…` with the D-R21 changes, to `1407e850…` with the D-R24 board-pass changes ([round 24 board pass](#round-24-board-pass)), to `92c3ad59…` with D-R24-18's capped chamfer ([round 24 fix pass](#round-24-fix-pass)) and to `a0ec075e…` with the D-R26 changes ([round 26 fix pass](#round-26-fix-pass)); figures measured only on `50a39de5…`, `0dc84776…` or `5516eeec…` say so. Rows that name `5516eeec…` were not re-measured on `1407e850…`, `92c3ad59…` or `a0ec075e…` by the docs lane unless they say so: the D-R24-17 chamfers and the D-R24 via changes may shift a gap or length there; the round 24 gate (DRC 0, S-8, route_check 0) passed on the new board. The round 26 docs lane re-ran the pyro and arming adjacency on `a0ec075e…`, and D-R26-04 audited every net pair on the whole board (§1): only the pairs named there changed, and the copper diff from `92c3ad59…` is the one in [Round 26 fix pass](#round-26-fix-pass). It was earlier updated by the round 19 fix pass from the inventory of `a3144b15…` (itself updated from `632a9ad3…` by the round 18 fix pass).
Figures that the round 19 CAD lane re-measured on `50a39de5…` say so; figures from the round 19 reviews were measured on `a3144b15…` and say so; measurements that were not repeated say that too. The integration and review status is in
[M3_R10.md, "Current state"](M3_R10.md#current-state). The [complete JSON ledger](../m3_design/assembly_review/sources/r10_review/r10_final_deviations.json)
maps every remaining obligation, 46 historical groups, 229 prior finding rows, the 126 agent-decision IDs through D-R17-04 (D-R18-01 … 11, D-R19-01 … 15, D-R20-01 … 11, D-R21-01 … 09, D-R22-01 … 07, D-R23-01 … 11, D-R24-01 … 23, D-R25-01 … 03, D-R26-01 … 04, D-R27-01 … 03, D-R28-01 … 04 and D-R29-01 … 02, 103 IDs, are in `R10_DECISIONS.md` and the table above, not yet in the JSON) and 23 owner-mandate records. Earlier measurements remain at their original hashes; exact native geometry comparison and current gate, budget and fit evidence
state what carries to this PCB. This supersedes the historical round 10 acceptance inventory without transferring its clean pair. R9 remains accepted; R10 is not accepted or ordered. No physical or firmware qualification follows from the CAD reviews.

### 1. Single switch, surface faults and unfused battery

**R10 single-fault fire routes with the bus enabled (R21-SAF-03; Inference for the I-5 mechanism, as in the FMEA).** (a) **FMEA I-5:** battery or port voltage on 3V3 can make the MCU drive PE4 and fire. On R10 it can come from a U2 (AP63203) high-side short, from an In2 3V3-to-RAW_PROTECTED / PORT_5V3 / PORT_4V8 short (the In2 3V3 fill edge runs within 0.6 mm of RAW_PROTECTED for 132.0 mm, of PORT_5V3 for 35.9 mm and of PORT_4V8 for 34.6 mm, minimum 0.300 mm), or from the unconnected In2 rings of J440.1 (PORT_4V8) and J9.1 (CAM_5V), 0.2505 mm from the 3V3 fill (round 21 safety lens, measured on `0dc84776…`). No part limits 3V3 to the MCU's 4.0 V absolute maximum ([DS12110 Rev 8](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) Table 119 p212). (b) **C128** (100 nF, PYRO1_OUT to GND) is the only MLCC across Q124: a flex-crack short bypasses the fire FET while the bus is enabled; the plate model gives 991 microstrain at C128 at 100 g, at the roughly 1000 microstrain MLCC guide (Calculation/Inference). After the on-rail check the bus stays enabled, so either route fires the match with people at the rail. **Lever on the pad:** owner row 18 (return PC1 low after the on-rail check and re-enable it on launch detection) restores the series pair as a second barrier for both. **Respin options:** a 3V3 over-voltage clamp or crowbar (not an FMEA change-list item; §4.2's H-9 is the load-switch gate-source capacitor, fitted on R10 as C120), In2 3V3 held ≥ 1 mm from RAW_PROTECTED or GND-guarded, the unconnected In2 rings of J440.1 and J9.1 removed with an In2 keep-out (the D-R20-05 method), and C128 as two MLCCs in series.

The owner selected J400 as the sole power/pad-arming switch, removed J124 and
the pull-pin, and retained ordinary 0.15 mm surface clearance. PC1 enables the
Q120/Q121 post-switch RAW_ACT bus; PE4 separately drives Q124. Required external
gate bias/series/capacitor networks remain. Two controls on one MCU do not create
independent software safety. Switching off does not guarantee de-energization
if USB or a self-powered endpoint is attached. Connect the e-match without such
sources; bench USB work requires pack or e-match disconnected. On-rail/on-last/
off-first and AGENTS section 2 remain mandatory.

**Surface inventory (R19-SAF-04; measured by the round 19 safety lens on `a3144b15…`, `adjacency_a3144b15.json`; carried to `5516eeec…` by the round 22 safety lens, R22-SAFETY-01).** Fifteen pyro and arming nets have 49 protected-net / foreign-net outer-layer pair rows within 0.5 mm (27 without GND) on `a3144b15…`.
On `5516eeec…` the minimum is 0.150 mm, ARM1_SENSE (B.Cu (29.75,45.5)–(29.75,49.4)) to U13.5 (CAM_IO_3V3), benign: at most 3.3 V on PC5 and, with the board on (CAM_IO_3V3 is up only then, so the D120 / R131 cold pull-up is live), about 2.19–2.21 V on RAW_ACT with the bus off and about 0.107–0.109 mA through the match against the J-Tek 0.30 A no-fire, at a BAT54 drop of 0.20–0.24 V (Calculation / Inference: the BAT54 drop at about 0.1 mA is inferred; R30-TRI-01: the round 22 figures, about 1.73 V and 0.15 mA, left out the cold pull-up); the cold screen then reads the bus as live and refuses (identical on `a3144b15…`, missed by the round 19 inventory). The round 19 minimum, 0.173 mm (R129.1, PYRO1_CONT_MID, to the GND via (22.330,58.250)), is next. The least RAW_ACT-to-GND pad / track / via gap is now 0.300 mm (B.Cu RAW_ACT (22.8,61.4)–(22.8,63.875) to U11.6); fills keep 0.2505 mm. Full native DRC passes the ordinary 0.15 mm floor. Unchanged Q124 pad geometry has gate-to-own-drain 0.520 mm.
**On `a0ec075e…`** (round 26 docs lane: every foreign copper item within 0.6 mm of the 18 pyro, arming, gate and sense nets PYRO1_*, ARM1_*, ACT_*, RAW_ACT, BAT_ENABLE and BAT_SW_*, on all four layers, and the gate nets and PYRO1_OUT to 1.2 mm, pcbnew shape distance on a read-only copy; Calculation on native geometry) the minimum is still that 0.150 mm pair, and the least RAW_ACT-to-GND gap is 0.316 mm (the D-R24-17 chamfer (22.8,63.535)–(22.46,63.875) to U11.6). D-R26-02 and D-R26-04 changed these pairs against `92c3ad59…`: PYRO1_OUT to 3V3 0.5135 → 1.0500 mm (J121.1's F.Cu run to R13's moved 3V3 via (9.2,52.55); R173.1 to D120.3 1.0511 mm) and to 3V3A 0.5662 → 1.0400 mm; 3V3 to PYRO1_GATE_N 0.835 → 1.065 mm (R127.1) and to PYRO1_GATE 0.676 → 1.0585 mm (R128.1), both to R164's 3V3 via, now at (19.55,55.825); 3V3A to PYRO1_GATE 1.151 → 1.145 mm (C10.1 to the PYRO1_GATE via (14.4,53.3)); R173.2 (PYRO1_CONT_MID) to D120.3 (3V3) 0.400 → 0.415 mm; R173.1 (PYRO1_OUT) to Q124's source via (15.85,58.345) 0.737 → 0.500 mm; R127.1 to C10.2's moved GND via (19.65,53.45) 0.263 → 0.270 mm; and, beyond the 0.6 mm scan, PYRO1_OUT to BUZZ_DRV 0.964 → 0.794 mm (now R173.1 to R162.1) and R173.2 to R162.1 more than 1.2 → 1.133 mm. PYRO1_CONT_MID's D-R26-04 diagonal is 0.2005 mm from Q123.1 and 0.386 mm from R134.2, so the run keeps the pair minima, 0.175 / 0.250 mm. (On the intermediate `4108e6fa…`, never committed or reviewed, R164's via sat at (19.05,55.25), 0.331 mm from R126.1, and the diagonal 0.165 mm from Q123.1; D-R26-04 moved both.) D-R26-04's whole-board audit (every net pair on every layer, run with and without zone fills, for minima under 1.2 mm that dropped by more than 5 µm against `92c3ad59…`) lists, besides those pyro pairs, only non-pyro ones: 3V3 to BUZZ_DRV 0.534 → 0.234 mm and 3V3 to LS120.3 (no net) 0.700 → 0.206 mm (both R164's new via), BUZZ_DRV to GND 0.280 → 0.200 mm (C10.2's via) and GND to U1.5 (PE6, no net) 1.144 → 0.847 mm (C11.2's via; not a regression with fills). Every other pair's minimum is the same or larger.
An OUT-to-GND bridge or a failed-short Q124 can fire an enabled match; coating and a prior cold screen do not prevent a later fault. Rows below that put PYRO1_OUT onto a lower-potential net fire an enabled match by themselves too: the PYRO1_OUT-to-GND pairs (0.177 / 0.180 mm, owner row 2's residuals; R173.1 to Q124's source via, 0.500 mm) and the J440.1 / J440.2 harness row (the OUT-to-GND class). A bridge from R173.1 to R162.1 (BUZZ_DRV, 0.794 mm) may: PC14 cannot hold its pin against the bus, so the current that passes before the pin fails is not known and may exceed the 0.30 A no-fire (Inference, D-R26-04). PYRO1_OUT to 3V3 or 3V3A would fire too, since the bus drives R134 and the match into the rail (about 0.9–1.8 A if the rail held 3.3 V; otherwise the rail rises past U1's 4.0 V, the I-5 mechanism), and so would 3V3 or 3V3A onto Q124's gate nets, which drives the gate as a fire command does; D-R26-02 / -04 hold these at least 1.040 / 1.0585 mm apart on every layer (R26-TRI-01). QSPI_IO2–PE4 needs a sustained IO2-high pattern; the other rows cannot fire. A bridge present at power-up reads out of band in the cold screen and is refused before PC1 (to 3V3: CONT = BUS = 0.295 V against healthy 0.099 V and open CONT 0.146 V; to GND, or a gate net held at 3.3 V so that Q124 conducts: CONT = BUS = 0; Calculation; to BUZZ_DRV: the cold OUT reading moves to PC14's level, which the CONT / BUS bands refuse, D-R26-04); one that forms after PC1 is high is not screened (owner row 18 covers the pad). The pairs with a consequence:

| Pair (on `a3144b15…` unless noted) | Gap | If it bridges (Calculation) |
|---|---|---|
| ~~R134.2 (RAW_ACT) to the GND via (20.706,65.619), R81.2's fan-out~~ **Removed by D-R21-05 on `5516eeec…`** (the via is gone) | was 0.196 mm | Was: with the bus enabled, the pack shorted through Q120 / Q121 without R134, the match or its leads, about 23 A, unfused |
| R81.1 (BAT_ENABLE) to the GND via (17.20,79.90), F.Cu (new with D-R21-05; also 0.223 mm to the GND track (15.875,79.9)–(17.2,79.9)) | 0.173 mm | EN to GND holds U9 off (fail-safe) |
| R81.2 (GND) to the RAW_PROTECTED via (20.30,79.10), F.Cu | 0.307 mm | A U9 output short: U9 limits and latches off |
| C87.1 (BAT_ENABLE) to the F.Cu GND fill | 0.251 mm | EN to GND holds U9 off (fail-safe) |
| C87.2 (GND) to the BAT_FAULT_N track (22.175,80.475)–(19.3,83.35), F.Cu | 0.254 mm | Reads as a U9 fault (diagnostic) |
| RAW_ACT feed under R134's body to R134.1 (IGN) | 0.367 mm | R134 is bypassed: about 12 A into a match that shorts after firing, instead of 4.2 A |
| RAW_ACT sense branch to the USB_OVLO track | 0.175 mm | 7.4–8.4 V on U11.5 (OV1, IN1's USB over-voltage input; R26-TRI-05), above its 6 V absolute maximum ([TI SLVSEA3F](https://www.ti.com/lit/ds/symlink/tps2121.pdf) p6) |
| RAW_ACT sense branch to R87.1 (USB_LIMITED) | 0.225 mm | USB 5 V on the bus with PC1 low whenever USB is attached; the procedure forbids an e-match with USB |
| PYRO1_CONT_MID corridor to R134.2 | 0.250 mm (on `a0ec075e…` the run from R173.2 turns 45° at (16.87,60.82), D-R26-02 / -04: its diagonal is 0.386 mm from R134.2) | Only a 5.1 kΩ path (at most 1.65 mA). With an open match the cold readings are CONT / BUS 102.0 / 55.5 mV against healthy cold 96.2 / 96.1 mV and open 141.5 / 0.0 mV, all at Vf = 0.30 V (nominal Vf = 0.20 V: 99.369 / 99.338 and 146.23 mV; Calculation / Inference: the BAT54 drop at that current is an Inference); the powered CONT is 1.213 V at 7.4 V whether the match is open or intact. So the cold screen needs a BUS lower band, not only a CONT upper band |
| QSPI_IO2 to PE4 (PYRO1_GATE_N) at U1: a three-lead solder bridge across U1.1–U1.3 (0.700 mm pad edge to edge; the no-net PE3 / PE5 between are analog, so a two-lead bridge is inert), or the QSPI_IO2 track under U1 0.550 mm from U1.3 behind solder mask (R23-SAFETY-08 (2); verified Minor, `round23_safety_severity_check.md`) | 0.550 / 0.700 mm | PE4's low fights IO2's driver. Q124's gate capacitor is C126 (220 nF; C128 is 100 nF on the drain), so the gate time constant is about 47–58 µs over C126's ±10 % (53 µs nominal; Calculation, driver resistances Inference). A steady IO2-high fight with the MCU driving IO2 puts 1.19–1.98 V on the gate and fires an enabled match after about 0.55 ms in all but one modelled corner. Page-program logging at a QSPI clock of 25 MHz or more stays at most 6 mA RMS, at least 50× below the 0.30 A no-fire; firing needs a sustained IO2-high pattern (Calculation / Simulation; driver resistances, flash drive, the AON7524 sub-amp curve and the match thermal model are Inference). Rules: M3_R10 Firmware (quad read-verify before PC1 high, QSPI-use limits while PC1 is high, QSPI traffic during the cold screen); first article, before first power: inspect U1 pins 1–5, then, unpowered, meter U3.3 to R127.1 in both polarities: above 0.9 kΩ, or open, both ways passes, and a beep or under 100 Ω either way is a bridge (ORDERING 8.3, R28-TRI-05) |
| PYRO1_CONT_MID to Q123.1 (BUZZ_G), B.Cu: the run (17.85,61.8)–(20.83,61.8), as on `92c3ad59…`; the D-R26-04 diagonal (16.87,60.82)–(17.85,61.8) is 0.2005 mm away (0.165 mm on the intermediate `4108e6fa…`) | 0.175 mm | mA only, behind R173 5.1 kΩ: it cannot fire. A BUZZ_G bridge puts at most about 4.6 V on PC14 through R162 1 kΩ, within the FT limit, and disturbs the CONT reading and the buzzer drive (the row 2 residual class) |
| R173.2 (PYRO1_CONT_MID) to D120.3 (3V3), B.Cu | 0.415 mm (0.400 mm on `92c3ad59…`) | Feeds at most about 1 mA through R173's 5.1 kΩ (D-R26-02): it cannot fire. Cold, it lifts CONT to about 3.3 × 1 / 6.1 = 0.54 V, far above the healthy 0.099 V, so the screen refuses (Calculation) |
| PYRO1_OUT to 3V3: R173.1 to D120.3, B.Cu (R23-SAFETY-08 (2)) | 0.5135 mm on `92c3ad59…`; **1.0511 mm on `a0ec075e…`** (D-R26-02) | With the bus enabled the bus drives the 3V3 rail through R134 and the match: (7.4–8.4 − 3.3) V over a 2.8–4.5 Ω loop, about 0.9–1.8 A if the rail held 3.3 V, against the J-Tek's 0.75 A all-fire; but the AP63203 does not sink in PFM (DS41326, "Pulse Frequency Modulation"), so the rail would instead rise past U1's 4.0 V absolute maximum (Inference; the I-5 mechanism, and the class of the J121.1-to-3V3 barrel case). Either way it can fire an enabled match by itself (R26-TRI-01). A pre-existing bridge reads CONT = BUS = 0.295 V cold and is refused before PC1. **Closed by D-R26-02:** outside the 0.5 mm band |
| PYRO1_OUT to 3V3A: the track (15.5,56.6)–(16.87,57.97) to R164.2, B.Cu (R23-SAFETY-08 (2)) | 0.5662 mm on `92c3ad59…`; **1.0400 mm on `a0ec075e…`** (D-R26-02; the run (10.37,56.6)–(15.5,56.6) is 1.0400 mm too, was 0.6059) | As the row above, through R164 (2.2 Ω) into 3V3A: about 0.6–1.0 A until R164 (0603, 0.8–2.3 W) opens, then VDDA, U4 and U5 are over-driven (R26-TRI-01; Calculation / Inference). **Closed by D-R26-02** |
| R173.1 (PYRO1_OUT) to Q124's source via (15.85,58.345), GND, B.Cu (nearer since D-R26-02 moved R173) | 0.500 mm (0.737 mm on `92c3ad59…`) | Bypasses Q124, so it fires an enabled match by itself, as the 0.177 / 0.180 mm OUT-to-GND residuals of owner row 2 do. A pre-existing bridge reads CONT = BUS = 0 cold and is refused before PC1 (Calculation). R173 is in the bottom coat selection (ORDERING 8.3) |
| R173.1 (PYRO1_OUT) to R162.1 (BUZZ_DRV, PC14's drive), B.Cu: nearer since D-R26-02 moved R173; outside the 0.6 mm scan, from D-R26-04's whole-board audit | 0.794 mm (the pair's minimum was 0.964 mm on `92c3ad59…`) | Inference (D-R26-04): with PC1 high and Q124 off, OUT follows the bus through R134 and the match, and the bridge ties it to PC14 (U1.8). PC14's output is characterised only at ±3 mA (DS12110 Table 159), so it cannot hold the pin against the bus through about 4 Ω: in any PC14 state the pin is driven far above its supply and its protection conducts. The current that passes before the pin fails is not known and may exceed the match's 0.30 A no-fire, so firing is not excluded. A bridge present at power-up moves the cold OUT reading to PC14's level, which the CONT / BUS bands refuse (firmware rule 3 also toggles PC14 during the cold screen). **Not restored** (D-R26-04): R173 cannot go back south without losing the 3V3 clearance, and R162 has no room 0.2 mm east (its courtyard would cross R163's) or north (R164's via route) |
| R173.2 (PYRO1_CONT_MID) to R162.1 (BUZZ_DRV), B.Cu (D-R26-04's audit) | 1.133 mm (more than 1.2 mm on `92c3ad59…`) | Behind R173's 5.1 kΩ an enabled bus feeds PC14 at most 8.4 V / 5.1 kΩ = 1.6 mA: no fire. Cold, CONT leaves its band and is refused (Calculation, D-R26-04) |
| Q124's gate nets to 3V3 / 3V3A: R127.1 / R126.1 (PYRO1_GATE_N, PE4's net) and R128.1 (PYRO1_GATE) to R164's 3V3 via (19.55,55.825), F.Cu; C10.1 (3V3A) to the PYRO1_GATE via (14.4,53.3), B.Cu | **1.065 / 1.081 mm, 1.0585 mm and 1.145 mm on `a0ec075e…`** (D-R26-04); on `92c3ad59…` the via sat at (19.05,55.9), 0.835 mm from R126.1 and 0.676 mm from R128.1; on the intermediate `4108e6fa…` D-R26-02 had put it at (19.05,55.25), 0.331 mm from R126.1, which the round 26 docs lane found | A hard bridge from 3V3 to PE4's net holds it at 3.3 V even with PE4 driven low (the pin's output resistance is far above a solder bridge's; Inference, as is the pin's survival); through R126 220 Ω against R128 10 kΩ the gate then sits at about 3.23 V, the drive of a PE4-high fire command (time constant about 47 µs with C126). A bridge to PYRO1_GATE puts the rail on the gate directly. Either turns Q124 on and fires an enabled match by itself (Calculation / Inference: the 3.23 V rests on the hard-bridge Inference above). Present at power-up, it holds Q124 on, so the cold screen reads OUT grounded (CONT = BUS = 0) and refuses before PC1; one that forms after PC1 is high is not screened. **Closed by D-R26-04:** every 3V3 / 3V3A item is at least 1.0585 mm from both gate nets on every layer (the gate nets' only inner copper is the PYRO1_GATE via's barrel, 2.75 mm from the nearest In2 3V3 fill); the next nearest is U1.6 (3V3) to U1.3 (PE4), 1.200 mm, on U1's own pins. The historical round 10 list below records the class at 0.6761 / 0.8352 mm |
| Q120's gate via (16.2,73.3), once the only link from R121 to Q120.4 (R23-SAFETY-05; verified Minor) | two barrels since D-R24-02 ((16.2,73.3) and (15.4,72.85); R24-TRI-04) | **Fixed by D-R24-02:** leaving Q120 off now takes two opens. The single-open consequence was: with PC1 high Q121 turns on and Q120 stays off, so the bus is fed through Q120's body diode. Four stalls then give 1.128 / 1.063 A (0.7 / 1.0 V drop: AONR21357 VSD typical / maximum at 1 A, Rev 2.1 p2; Calculation / Inference: the fire budget's hot Q124 factor is inferred), 0.93–1.01× the 1.125 A floor but at least 1.39× the maker's 0.75 A all-fire and at least 1.04× its 1.00 A recommended minimum; a first-order thermal model fires the match in 4–5 ms, inside the 20 ms pulse (Inference). Screen: the powered-BUS ≥ 0.96 × pack-voltage ground refusal (M3_R10 Firmware); at first article, before coating, with PC1 high and a dummy load in J121, ACT_GATE at R120.2 / C120.2 against Q120's source at R120.1 must settle at \|VGS\| of at least 4.5 V (a cut-off gate sits near 0 V), and during the dummy-load fire BAT_IN − RAW_ACT above 0.2 V fails the board (R23-SAFETY-05's criterion, D-R28-04; ORDERING 8.3). |
| U9.1 (EN) to U9.5 (IN) and the BAT_IN feed under the QFN | 0.200 mm | Board on with J400 open, for a leak of at most 1.52–1.83 MΩ from BAT_IN (7.4–8.4 V). Fixed by TI's RPW land and pin order; not changed |
| BAT_ENABLE via (17.1,82.8) to BAT_FAULT_N | 0.200 mm | Once the board is on, BAT_FAULT_N (R89 10 kΩ to 3V3) holds EN at 3.19 V, so J400 cannot turn it off: latch for a leak of at most 0.58 MΩ. Inside U9's fan-out. 0.200 mm on `5516eeec…`, `92c3ad59…` and `a0ec075e…`; 0.173 mm on `1407e850…`, where D-R24-17's chamfer narrowed it (R24-TRI-01), until D-R24-18 capped the chamfer |
| BAT_ENABLE via (19.675,66.6) to R134.2 (RAW_ACT) | 0.300 → **0.500 mm** (D-R19-02, re-measured on `50a39de5…`) | Once PC1 has enabled the bus, RAW_ACT holds EN on: latch for a leak of at most 1.69–1.96 MΩ |
| R123.1 (ACT_EN) to the BAT_ENABLE track | 0.330 mm | While PC1 is low, the bridge loads U9's EN with 2 kΩ and U9 stays off. **With PC1 high**, ACT_EN is about 2.2 V through 667 Ω, so EN stays at about 2.2 V and J400 cannot turn the board off (leak of at most 0.29 MΩ). The round 18 text said "U9 stays off" without this condition; it is corrected here |
| The J400.2 lead (BAT_SW_RETURN, at EN potential) touching a pack-voltage conductor (J1.1 lead, servo pack-star +) | harness | EN = 7.4 × 300 / 770 = 2.88 V: the board is on with the switch open |
| The J400.2 lead touching J440.1 (PORT_4V8, 4.79 V) or J440.3 (board TX, 3.3 V) | harness (round 19 circuit check) | EN = 4.79 × 300 / 770 = 1.87 V or 3.3 × 300 / 770 = 1.28 V, both above VUVLO(F) max 1.116 V: J400 can no longer switch the board off |
| J440.1 or J440.2 touching J121.1 (PYRO1_OUT) with the bus on | harness (round 19 circuit check) | Joins the existing OUT-to-GND fire class, as a J1.2 chafe already does, so it fires an enabled match by itself (R26-TRI-01); separate J440's leads from the igniter leads |

The EN thresholds are TPS25947 VUVLO rising 1.183–1.223 V and falling 1.076–1.116 V ([TI SLVSFC9C](https://www.ti.com/lit/ds/symlink/tps25947.pdf) p9). Hard bridges at the BAT_FAULT_N, RAW_ACT and ACT_EN pairs that exist at power-up stop the board starting (EN is loaded by 10 kΩ, 11.2 kΩ (5.6 kΩ with the e-match or the step-3 dummy fitted, R30-TRI-01) or 2 kΩ), so they show themselves.
They defeat the switch only if they form, or start to conduct (moisture, unwashed flux: the order asks JLC for no washing), after power-up. Closure (owner table row 24): coat U9, R80, R81, R165, C87 and the BAT_ENABLE vias and tracks; per flight, with the pack connected and J400 open, confirm the board is off before the e-match goes in, and after any closed-switch check confirm that opening J400 turns it off;
twist the J400 pair, on its own ties, away from the battery and servo power leads and from J440's leads, and keep J440's leads apart from the igniter leads (ORDERING 8.3 and 8.4). Connect the e-match only with no USB and no self-powered module attached on any port, AUX included. A respin option is to divide the EN network impedance by 10 (C87 × 10 keeps the timing), which raises every leak threshold tenfold.
TP121's 7.14 mm ACT_GATE stub (R19-SAF-03) is gone (D-R19-03): ACT_GATE outer copper within 0.30 mm of GND 12.896 → 7.996 mm, and ACT_GATE to BAT_SW_SOURCE 0.400 → 0.470 mm (CAD lane, `50a39de5…`).

**S-8 barrels (R19-DOC-06, R19-SAF-01, R19-SAF-05).** S-8 requires 1.0 mm from each protected plated barrel wall to foreign inner copper. `BARREL_NETS` in `tools/check_r10.py` names 11 nets; 6 of them carry plated barrels on this board (`a0ec075e…`; the same barrels as `92c3ad59…` and `1407e850…`, R25-TRI-06; the round 26 docs lane re-measured the minima: 1.021 mm at the PYRO1_OUT via, 1.050 mm at the other protected vias and at J121.1 and J400.2, unchanged), 12 barrels in all:
the PYRO1_OUT via and the J121.1 hole, the J121.2 hole (PYRO1_IGN), the PYRO1_GATE via, the four ACT_GATE vias (two since D-R24-02, both 1.050 mm from foreign inner copper, re-measured), the three BAT_ENABLE vias and the J400.2 hole (BAT_SW_RETURN). RAW_ACT has no barrel.
GND counts as foreign at ACT_GATE, ACT_DRV and, since D-R19-01, PYRO1_OUT: there a short to GND turns the P-FET pair on, or bypasses Q124 and fires an enabled match (about 1.5 A). Elsewhere GND is permitted. At PYRO1_GATE and BAT_ENABLE it holds the node off. At PYRO1_IGN (J121.2) it is fail-safe for firing (no match current), but with the bus enabled a PYRO1_IGN-to-GND short draws 3.3–3.75 A through R134, 22–29 W against its 2 W rating, until R134 opens: a thermal event and loss of the primary channel (R23-SAFETY-08 (3), Calculation).
Barrel wall to the nearest foreign In1 / In2 copper on `50a39de5…` (CAD hand-back, native pcbnew 10.0.7; GND listed separately):

| Barrel | In1 GND | In1 other | In2 GND | In2 other | Inner ring to foreign |
|---|---|---|---|---|---|
| PYRO1_OUT via (11.630,55.100) | **1.021** (was 0.251) | 2.925 3V3 | **1.021** (was 0.251) | 2.699 3V3 | no inner pad |
| PYRO1_OUT J121.1 hole | **1.050** (was 0.551) | 1.320 3V3 | **1.050** (was 0.551) | 1.061 3V3 (was 1.103) | no inner ring since D-R20-05 (was 0.750 GND on `50a39de5…`) |
| PYRO1_IGN J121.2 hole | 0.551 | 1.900 PYRO1_OUT | 0.551 | 1.900 PYRO1_OUT | 0.251 GND |
| PYRO1_GATE via (14.400,53.300) | 0.251 | – | 0.251 | 2.100 USB_LIMITED | no inner pad |
| ACT_GATE via (16.200,73.300) | 1.050 | – | 1.407 | 1.050 RAW_PROTECTED | no inner pad |
| ACT_GATE via (11.140,71.700) | 1.050 | 2.223 BAT_SW_SOURCE | – | 1.050 RAW_PROTECTED | no inner pad |
| BAT_ENABLE via (19.675,66.600) (moved) | 0.251 | – | 1.123 (was 0.994) | 1.050 RAW_PROTECTED | no inner pad |
| BAT_ENABLE via (21.300,68.900) | 0.251 | 1.624 3V3 | 1.566 | 1.050 3V3 | no inner pad |
| BAT_ENABLE via (17.100,82.800) | 0.251 | 1.678 BAT_FAULT_N | 2.602 | 1.050 RAW_PROTECTED | no inner pad |
| BAT_SW_RETURN J400.2 hole | 0.250 since D-R20-05 (was 0.551; exempt: GND holds EN low) | 1.900 BAT_SW_SOURCE | 1.050 | 1.050 RAW_PROTECTED | no inner ring since D-R20-05 (was In1 0.251 / In2 0.750 GND) |

The PYRO1_OUT via's 1.021 mm is to the ring of its own GND partner via at (10.3,55.6), 1.42 mm centre to centre (the 1.5 mm partner rule holds). S-8 passes with nominal margins of 0.021–0.050 mm over the 1.0 mm floor.
**Ring copper (R19-SAF-05).** Vias keep no inner pad on layers they do not join, but the plated terminal holes keep their 1.9 mm ring on In1 and In2, and S-8 measures from the hole wall. So, copper to copper: J121.1's ring is 0.750 mm from In1 / In2 GND and about 0.761 mm from In2 3V3 (Calculation: the 1.061 mm wall figure minus the 0.30 mm ring width; the round 19 safety lens measured 0.803 mm on `a3144b15…`);
J400.2's ring is 0.750 mm from In2 RAW_PROTECTED (measured on `a3144b15…`, unchanged region) and from In2 GND. A J400.2-to-RAW_PROTECTED short latches U9 on (EN about 2.88 V); a J121.1-to-3V3 short with the bus enabled drives RAW_ACT through R134 and the match into the 3V3 rail (roughly 0.3–0.8 A in the match against the J-Tek 0.30 A no-fire and 0.75 A all-fire; Calculation/Inference, the AP63203 does not sink current in PFM).
**Resolved on `0dc84776…` (D-R20-05):** J121.1 and J400.2 now carry no unconnected inner rings (set in the generated library), so the figures above apply to `50a39de5…` only; their copper is now as far as their walls. Since D-R26-01 (`a0ec075e…`) pins 3 and 4 of the four-position terminal (J410, J420, J440, J9) carry none either; pins 1 and 2 keep theirs, so the J440.1 / J9.1 In2 rings of the I-5 route stay. J121.2 keeps its rings (GND exempt), and S-8 now measures any ring a barrel keeps. Side effect: J1.2 (GND, the same footprint) lost its In2 ring, so In2 RAW_PROTECTED is 0.25 mm from that GND barrel (was 0.55) (on `0dc84776…`; D-R21-01 then set inner-layer PTH pad hole to copper at 0.55 mm, so J1.2 is 0.550 mm again on `5516eeec…`, against JLC's 0.3 mm for a PTH pad hole; a component hole is not a via, whose JLC figure is 0.2 mm). Finished-hole size, registration and outer barrel still need fabricator allocation; this is not fabricated clearance qualification (see §9). No wider isolation is inferred.

OQ-6 leaves battery leads, entry copper, TVS and capacitors unfused; the removed
ARM-link fuse is not protection. Retain strain relief, no chafe and qualified
crimp/solder construction. Shared servo faults can collapse the pack. Keep the
Blue Jay electrically isolated.

The two direct PC0/PC5 sense banks give a conditional single-resistor-fault
maximum 3.342171 V at 19.9 V. Healthy/open passive CONT levels (cold, PC1 and PE4 low) are approximately
99.369/146.226 mV (nominal at 3V3 = 3.3 V and a 0.20 V BAT54 drop; Calculation / Inference); a short match resembles healthy. Powered-bus readings are different numbers (for example about 0.75 V intact at 8.4 V). Both controls stay low for
the passive fault screen. After previous enable, wait at least 1 s and verify
discharge; then enable PC1 with PE4 low and wait at least 100 ms before powered
checks. Thresholds, leakage, ADC errors, gate settling and ground refusal remain
firmware/bench obligations. In flight these readings never veto recovery.

Round 18 additions (R18-SAF-01 to -04 and R18-GATE-01). Items (a) to (d) describe the previous board `632a9ad3…`; the board changes of the round 18 fix pass (group rows m01 to m04 above) and the measured state on `a3144b15…` follow them.
(a) Two more barrels, the ACT_GATE vias at (16.2,73.3) and (11.8,70.725), stand 0.2505 mm from In1 GND and from In2 RAW_PROTECTED, and the BAT_ENABLE vias and the J400.2 ring stand 0.2505–0.251 mm from RAW_PROTECTED; S-8 did not cover them.
With J400 open, RAW_PROTECTED is about 0 V, so a short from ACT_GATE to RAW_PROTECTED or to GND turns Q120 and Q121 on and RAW_ACT follows BAT_IN. A resistive leak of about 0.20–0.52 MΩ to a node near 0 V already reaches the threshold against R120 100 kΩ; a leak of at most about 1.8–2.0 MΩ into EN holds U9 on against R81 300 kΩ (Calculation).
(b) Q121's off-bias R120 and gate capacitor C120 connect through two single vias and an F.Cu run, so one open leaves the gate floating (Inference).
(c) A bridge from BAT_FAULT_N to ACT_EN_MCU gives 3.3 × 100 / (10 + 1 + 100) = 2.97 V at Q122's gate whenever PC1 is not driven (boot, reset, debugger halt, ROM loader); a PC1 internal pull-up (30–50 kΩ) against R123 100 kΩ gives 2.19–2.52 V. Either turns Q122 on and with it Q120 and Q121.
(d) Single surface bridges sit 0.250 mm from R134.2 (the OUT sense branch), 0.175 mm from Q123.1 and 0.222 mm from R131.1 (IGN). A bridge from RAW_ACT to OUT bypasses R134, looks like a healthy match in the cold and powered readings, and turns a fire command into a near pack short of about 28 A
(Calculation/Inference); a bridge from IGN to OUT bypasses the match silently. In every case firing still needs a second fault on Q124's side, so none is a single-fault fire. Inner copper cannot be inspected, coated or reworked, and a bare-board test does not screen later leakage or CAF growth (Inference).
After the fix pass (`a3144b15…`; native measurement and Calculation, D-R18-01 to -06):
(a′) Fill-only keep-outs hold In1 and In2 copper 1.050 mm from the ACT_GATE barrels (the second via moved to (11.14,71.7)), In2 copper 1.050 mm from the BAT_ENABLE barrels and the J400.2 hole. In1 GND stays 0.251 mm from the BAT_ENABLE barrels and 0.551 mm from J400.2 on purpose: a short to GND holds U9 off, fail-safe. The nominal margin over S-8's floor is 0.050 mm.
(b′) Q121 has its own via-free gate–source resistor R119 (100 kΩ, B.Cu, B(11.57,71.10)); Q120 keeps R120, and the shared node sees R119 ∥ R120 = 50 kΩ. S-3 `local_gate_bias` requires a same-layer gate–source resistor for each load-switch FET.
(c′) R123 is 2 kΩ: the Q122 gate is at most 0.218 V (3.6 V × 2 kΩ / 33 kΩ) with a 30 kΩ PC1 pull-up at 3.6 V, and at most 0.554 V with a BAT_FAULT_N bridge, both under the 0.65 V minimum threshold; with PC1 high it is 2.19 V (1.92 V at the VOH floor), and Q122 saturating there is Inference. ACT_EN_MCU to BAT_FAULT_N is 0.550 mm (was 0.171 mm).
(d′) The OUT branch ends at R173 (B(16.87,59.70)): OUT to R134.2 2.825 mm (was 0.250 mm), to Q123.1 1.577 mm (was 0.175 mm); IGN to R131.1 0.575 mm (was 0.222 mm). The PYRO1_CONT_MID node behind R173 now takes the corridor, 0.250 mm from R134.2 and 0.175 mm from Q123.1; a RAW_ACT bridge adds only a 5.1 kΩ path (at most 1.65 mA), far below fire current; it raises the powered-bus CONT reading, and a firmware band can flag it (Inference). The round 19 additions are the inventory and S-8 tables above.

### 2. External servo return and firing reserve

J122 carries four protected PWM signals and shared reference GND only. Each
motor positive/negative pair runs to the pack-star harness. The ≤ 0.6144 A board
share is an inference using ≥ 50 milliohm signal-reference branches and ≤ 1 milliohm star
transfer, with a 1 A design allowance; measure actual four-stall return current
and temperatures. Loss of the former servo power cutoff is retained. Commanded
neutral and physical fin motion need separate qualification.

Native current paths are BAT_IN 6.307107 mm/1.0 mm, aligned ACT_FET_S 2.200000/
0.4, RAW_ACT 5.886133/0.5, IGN 10.523276/0.5 and OUT 7.854478/0.5 (IGN was 10.230382 mm on `632a9ad3…`). No series fire
via or parallel source-leg credit is taken. The 4.617803 ohm loop (4.617458 ohm on `632a9ad3…`) includes the
stated hot copper/FET/contact/harness/source assumptions. On `50a39de5…` (`parts_budget.json`, which now includes the 100 mA AUX allowance in the other load) a 7.4 V equivalent
fire-time source gives 1.540851 A idle and 1.475765 / 1.410416 / 1.344761 / 1.278747 A at one to four persistent
stalls (1.544251 to 1.282918 A on `a3144b15…`; Calculation / Inference: Q124's inherited hot factor is an Inference, and
the FET, hot R134, harness, contact and converter-load figures are unmeasured allowances). The selected MJG J-Tek maker 0.75 A all-fire datum is a 0.5 s test; the
project floor is 1.125 A, and the actual lot's 20 ms firing is unqualified.
Measure pack reserve after pad drain, complete source/harness impedance, hot
FETs/copper, actual charge firing and shorted-match logic survival.

### 3. Always-on GPS/radio, camera and cable interfaces

GPS, radio and the spare AUX port share direct PORT_4V8 and 1 kohm/ground-ESD UART paths; no per-port
power-cycle, fault indication, isolation or shedding remains. A cable short can
remove all three ports and overload the 2 A buck into current limiting/hiccup when
the camera is loaded (camera-short case with GPS, radio and AUX on: 1.810 A, below 2 A; Calculation). The camera alone retains U402/U12/U13 sequencing.

**Identical ports (D-R19-14, owner-approved 2026-10-30).** J410, J420 and the new J440 (F(7.4,16.25), wires west) are electrically identical: pin 1 PORT_4V8, 2 GND, 3 board TXO, 4 board RXI, each with 1 kΩ series resistors and ground-only ESD103 diodes, and no new BOM codes.
The UARTs are USART3 PD8 TX / PD9 RX on J410, UART5 PB13 TX / PB12 RX on J420 and USART6 PC6 TX / PC7 RX on J440. The owner may put the GPS or the radio on any of the three, so firmware keeps a port map (default GPS J410, radio J420, AUX spare; the silkscreen words show the default).
The camera port J9 is not in the set: it carries 5.4 V, its TX / RX are the reverse, and its UART is isolated by U12 / U13. The AUX device may draw up to 100 mA at 4.8 V beyond the GPS 150 mA and radio 300 mA: the binding limit is U401's junction at the 70 °C bay limit, 109.2–123.9 °C against 125 °C with the inferred 80–110 °C/W (Calculation/Inference). The AUX module minimum is 4.642 V at a 0.2 Ω harness (Calculation).
On J440 only 1:4V8 is printed on the top; 2:GND, 3:TXO and 4:RXI are on the bottom beside their pins. Check every port's harness end to end against the printed legends before first power.

| Item | Conditional current result / reason retained | Required closure |
|---|---|---|
| Camera | ≥ 5.031682 V at 1 A; buck 5.366682-5.546269 V, switch ≤ 135 milliohm, other loop ≤ 150 milliohm, negative transient ≤ 50 mV | Four-wire harness/contact loss, startup/load-step and low-pack/dropout tests |
| Radio/GPS/AUX | ≥ 4.601504/4.631504 V at 0.30/0.15 A (on `a3144b15…`); AUX ≥ 4.642 V at 0.1 A and 0.2 Ω; maximum including allocation 4.923250 V | Measure actual peaks, both endpoint voltages, shared-short logic retention and RF immunity |
| UARTs/ESD | Direct GPS/radio/AUX RX pulls always off; operating pull-off threshold relevant I/O supply+0.3 V differs from 4 V absolute stress. No powered-off isolation; camera translator rationale does not apply to them | Levels, sequencing, unpowered behavior, selected baud edges and installed cable/ESD tests |
| Unkeyed terminals | All 27 individual pin legends pass (eight terminals); J9 pin 3 RXI/pin 4 TXO, GPS/radio/AUX pin 3 board TXO (module RX) / pin 4 board RXI (module TX) | End-to-end polarity/UART and ferrule/gauge check; DB125 range 28-16 AWG |
| J400 | About 7 microamp dry-contact loop, no direct contact sensor | Reachability on rail, dry-contact reliability, vibration and intermittency tests |
| GPS/radio capability | M100 Mini L1 only; maker 500 m/s/4 g tracking limits. LR900-F 890-915 MHz; manual 12-25 corresponds to 902-915 MHz | GPS is not the flight estimator; qualify installed GPS operation and maker-supported channel/hop configuration |

USB-only power (R18-MCU-02). The GPS, radio and AUX ports are fed from the battery path only: on USB-only power PORT_4V8 is off while the MCU runs (U11's IN2 channel is off). After the switch opens, C84 may back-feed RAW_PROTECTED through U11 until the reverse current exceeds IRCB (0.2 / 1 / 2 A, [TI SLVSEA3F](https://www.ti.com/lit/ds/symlink/tps2121.pdf) p8), so the ports may stay powered for part or all of the hold-up; the budget assumes they do (R20-PWR-03). An idle-high TX would push about 2.7 mA through 1 kΩ into each unpowered module's RX pin
(Calculation; the module's input structure is unmeasured), against u-blox's guidance not to drive the PIOs while V_IO is unsupplied. Firmware keeps the three TX pins (PD8, PB13, PC6) analog while the ports are unpowered. It enables a port's TX alternate function only while PA4 (LOGIC_SOURCE_ST) reads low, meaning U11 has selected IN2, the battery path ([TI SLVSEA3F](https://www.ti.com/lit/ds/symlink/tps2121.pdf) Table 9-3 p18), and parks the pins analog with no pull when PA4 rises or the PA6 watchdog trips (R19-MCU-01, D-R19-13). During USB-only sessions disconnect the J410, J420 and J440 leads or verify that pins 3 stay near 0 V.
At every battery power-up PORT_4V8 can lead 3V3 by tens of ms because U11's 470 nF soft-start makes 3V3 lag (Inference); PD9, PB12 and PC7 at 3.3 V with VDD = 0 (all FT pins; PD9 is FT_h, [DS12110 Rev 8](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) Table 9 p75) stay under the 4.0 V limit only if the module's output high level is at most 3.6 V. **Rule (R20-MCU-02; binding note `firmware_obligations` entry starting "On VLOGIC undervoltage/shutdown"):** any device on J410, J420 or J440 must drive its TX high at no more than 3.6 V (no 5 V-logic devices); PORT_4V8 can rise tens of ms before 3V3 (U11's 470 nF soft-start and U2's start-up put 3V3 in regulation about 21–26 ms into VLOGIC's slew; Calculation / Inference, D-R28-04) and an FT pin allows only 4.0 V while VDD = 0 (Table 119 p212). Measure the lag on first articles. A port with no mapped device keeps its USART disabled and both pins analog (R20-MCU-03). VREFBUF_CSR is never written (R20-MCU-01, Inference: RM0433 not re-read).

### 4. Power, hold-up and transient models

| Item | Current measurement/calculation and reason retained | Required closure |
|---|---|---|
| Pad energy | Common stated 6 V / 80 % upper-allocation worksheet: 2 h with camera 0 / 0.5 / 2 h uses 1.812657 / 2.390393 / 4.123602 Ah board charge; board-only capacity leaving 20 % unused 2.265821 / 2.987991 / 5.154503 Ah. R19-REQ-01: several margins in it have no measured root (the 0.461 A port current, SD writes on the pad, 1.4 W logic at 200 MHz, Ah at 6 V); ORDERING 8.1.1 lists each one and gives the re-based estimate (Inference) | Owner chooses the basis (owner table row 17). Add motor, flight, recovery charge; measure actual duty/aged-cold usable capacity, fire-time 7.4 V-equivalent source/resistance and real bay fit. Camera off unless recording; round17_pad_energy/D-R17-01, Calculation/Inference |
| C98 return | Ordinary GND stitch (23.8,62.95),0.5/0.3 mm; saved-copper device-loop 7.345584 mm at 0.05 mm grid, 7.270584 mm at 0.025 mm, versus 31.812237 mm before | Local geometric remedy passes native checks; USB attach/source-transfer waveforms and inductance remain unqualified. The separate in-fill M2 annotation is below |
| Camera bypasses | C91 input 4.092142 mm direct/5.035660 mm routed, diagnostic ground return 6.273402 mm; C92 power/return 4.205635/2.531371 mm | Actual stability, startup, transient and effective-capacitance checks |
| Continuous power necks | Native U9 entries, C88-first graph, U400 feed and two 0.5 / 0.3 mm U9 OUT vias are inventoried; long-conductor IPC curve fits do not establish short-neck absolute temperature | Actual copper/plating/current sharing, track/via DC and hot-board tests |
| Single-via feeds (R19-PWR-01) | The round 19 power lens found eight feeds that change layer through one 0.3 mm via on `a3144b15…`. D-R19-09 added a second via to five (`50a39de5…`): C84 hold-up (VLOGIC) (29.8,81.15); U402 IN (PORT_5V3) (42.75,61.8); U401 IN (PORT_5V3) (26.45,11.95); U401 EN (PORT_5V3) (24.9,14.9); U401 OUT (PORT_4V8) (29.75,9.95). Not doubled, with the measured reason: U11.2 RAW_PROTECTED (24.3,66.0), 1.00 A at 1 A, the only battery path into VLOGIC (every legal spot within 1.5 mm is 0.15–0.35 mm from the ACT_EN_MCU run, under D-R18-03's 0.5 mm floor); 3V3A (16.0,50.2) (the USB_LIMITED In2 run 0.65 mm south blocks every spot below; spots above sit 0.15 mm from U1.100 / U1.1); 3V3A (27.0,49.25) (F.Cu spots ≤ 0.10 mm from U1.19's GND stub; a B.Cu spot needs stubs on three layers). An open at U11.2's via removes the primary computer's battery supply; recovery then falls to the isolated Blue Jay | First-article pack-only power-up with USB disconnected (screens a manufacturing open, not a later crack); a C84-connected check (VLOGIC capacitance at TP83, or a measured hold-up); respin item for U11.2 and 3V3A (owner table row 22) |
| U401 thermal | With the 100 mA AUX allowance, 0.490 W (0.406 W before); the inferred 80–110 °C/W gives 109.2–123.9 °C at 70 °C ambient (floor 125 °C; GAP-3 allows 112 mA on the AUX port) and 124.2–138.9 °C at 85 °C, outside the bay range (Calculation/Inference) | Measure U401's temperature on first articles at full port load before relying on the AUX allowance (owner row 26); the margin at 70 °C is 1.1 °C on the inferred 110 °C/W. The two VIPPO vias are geometry, not a measured thermal coefficient |
| U9/R84 tolerance | Calculated 3.946188..4.856999 A from exact 750 ohm TI 3.96..4.84 A and R84 +/-0.35 % over 100 K; fault bound 3.743861 A leaves 0.202327 A (with R92 at U9's 10.18 V OVLO corner, D-R25-03; 3.743797 / 0.202391 A at the earlier 9.97 V) | Inverse-R Inference excludes overshoot/parasitic dips; measure short-port logic retention with camera and SD load |
| Recommended/fault limits | U9 OVLO recommended range is exceeded above about 12.2 V input; AP63201 loaded dropout is typical-only; C92 effective 2.211 uF is an estimate | Fault-state response, loaded low-pack headroom and converter/capacitor stability |
| F6 hold-up | 300.8 µF to 3.8 V, with the 100 mA AUX allowance: all ports and SD writing 0.464–0.539 ms (470 µF: 0.725–0.842 ms); camera off, logic shed, card idle 1.304–1.412 ms (470 µF: 2.038–2.206 ms). Before the AUX port: 0.490–0.571 and 1.533–1.655 ms (Calculation/Inference) | Actual biased/cold/aged capacitance/ESR, PA6 detection, command/current decay and flight-state retention. GPS/radio/AUX/card stay powered; no instantaneous shedding credit. The required hold-up time is an open owner question (owner table row 25) |
| C87 switch-bounce network (R19-REQ-02) | C87 2.2 µF → 220 nF (D-R19-10, C21120, X7R 25 V). With R80 + R165 = 940 kΩ, R81 = 300 kΩ and the [TPS25947 SLVSFC9C](https://www.ti.com/lit/ds/symlink/tps25947.pdf) p9 EN thresholds: turn-on 88 / 56 / 45 ms at 6.0 / 7.4 / 8.4 V (30–130 ms worst; was 0.31–1.22 s); a single J400 drop-out shorter than 19 / 33 / 41 ms (worst 10.3 / 20.1 / 26.0 ms, with U9's ±0.1 µA EN leakage plus D402's ≤ 50 nA, D-R24-19) cannot trip U9; repeated drop-outs add up. The X7R bias loss is taken as ≤ 6 % (Inference). Hot-plug model: all 2304 cases unchanged | Bench chatter test: total open time under 7 ms in every sliding 100 ms window, and U9 on for the whole run at 5.71 V, the four-stall BAT_IN (D-R25-01, D-R26-03; owner table row 21) |
| USB-only steady state (R18-PWR-02) | The upper allocation (1.4 W logic + 0.825 W continuous SD writes, 2.225 W at the converter input) would draw 0.4596 A at VBUS 5.00 V and 0.4856 A at 4.75 V against U10's 0.3477–0.4530 A limit band; the guaranteed input at the minimum limit is about 1.61 W (at most 0.785 W of logic with continuous writes); the lower allocation (0.6 W + 0.776 W) draws 0.281–0.296 A and fits (Calculation). Bench mode only | Run full-speed and SD tests on pack power or cap the clock and SD rate on PA4; measure the USB-only draw; do not raise U10's limit (USB 2.0: 500 mA) |
| USB startup | Nominal 516.1 µF behind U10 (514.1 µF on VLOGIC plus C86 / C98 on USB_LIMITED), 2.426 mC to 4.7 V; zero-load ideal 5.35–6.98 ms at 347.7–453.0 mA | Load-aware startup, current-limited hub, host attach and reverse-source tests; no USB compliance claim |
| Actual-feed hot-plug | Re-extracted from `50a39de5…`: all 2304 required cases pass (2304 required + 60 local on `a3144b15…`); minimum IN −14.807373 V, maximum falling 8.991477 V/µs, refined rising 5.091053 V/µs (on `a3144b15…`); retained-OUT bound 5.914 V after 2 s at 1643.90 µF (`hotplug_results.json`, after C87's change and the AUX cell's C444 / C445; rows unchanged) | Unfused installed harness ≥ 0.03 Ω and 0.1–2 µH, with simultaneous IN / OUT traces. The 0 and 0.01 Ω sensitivities fail, outside the domain. The model uses estimated parasitics and typical capacitor data; the ~0.193 V negative margin is not a physical guarantee |
| R166 endurance | 579.049 W peak/2.979359 mJ in different corners; no maker microsecond pulse guarantee | Maker approval or repeated hot/cold insertion and resistance-drift qualification |
| Local U9 OUT paths | C82 OUT + GND path 13.004163 mm, loop area 6.591563 mm²; D9 14.761880 mm, 7.012188 mm², within unchanged engineering limits (measured on `a3144b15…`, not repeated) | Pin/contact/package parasitics and actual protection waveform; geometric loops are not inductance guarantees |

### 5. Firmware, fire timing and sensors

No R10 firmware is implemented. The generated board binding is evidence, not
execution. Preserve accelerometer+barometer launch detection, hard ground
refusals, in-flight never-veto, two control-pin locks/readback and disabled
synchronous trace. Qualify the supported H743 lock/trace behavior on dummy loads.


BOOT0's 10k pull-down does not constrain BOOT_ADD0: AN2606 Rev 70 Table 2 Pattern 10
allows BOOT0=0/BOOT_ADD0=0x1FF0 ROM entry, and loader USART2_TX can drive servo 3.
Future programming acceptance must record/read back intended user-flash boot
settings and verify reset entry with the e-match disconnected. Retain deliberate
loader preparation before IWDG, PC1/PE4 low and locked, camera EN/OE low, SD_CS high.
No option-byte readback or executable R10 firmware exists in this CAD task.

Every normal physical fire pulse including tail must end by 20 ms. The intact-hardware
watchdog allocation is 960 LSI cycles plus synchronization, reset and current
tail, 34.853 ms against 36 ms (Calculation on allocations / Inference: the 0.2 / 0.5 / 1.5 ms allocations need bench tests, and the gate-discharge model's 0.4 V off criterion and hot gate charge are inferred); the actual temperature/voltage/tail and
watchdog implementation remain unmeasured. R134 at 70 C has conservative 35.797 W/
1.288708 J bounds at 36 ms. Its maker pulse-curve interpolation is an inference,
not repetitive/hot-board qualification. Failed-short hardware is outside this guard.

QSPI remains primary; SPI3 hinged SD is secondary. Qualify ≥ 800 Hz sampling,
flight-log rates/storage, ≥ 25% throughput margin, bounded erase/busy/DMA/error
handling, selected-card ≤ 200 mA write/≤ 30 mA idle, simultaneous interfaces and
reset/power-loss behavior without blocking control/recovery. QSPI lengths span
4.110955-14.102245 mm on `1407e850…` / `92c3ad59…` / `a0ec075e…` (no QSPI copper changed in round 26) (QSPI_IO2 14.102245 mm and QSPI_CLK 7.428234 mm after D-R24-17's chamfers; R24-TRI-10), one via each; no qualified clock/timing result exists.

U4 remains B180 at (17,45.9), roll = −gyro_Y, x lever arm −6 mm. The fitted part is now ISM6HG256XTR (D-R19-11, R19-BOM-01) on the unchanged land; LSM6DSV320X is the second-fallback alternate (needs part fields, BOM and CPL regenerated: ORDERING 8.1).
[DS15034 Rev 1](https://www.st.com/resource/en/datasheet/ism6hg256x.pdf) Figure 5 p9 and Table 2 p11 give the same pin map and axes as DS14623, so the axis map holds. Both read WHO_AM_I 0x73 (p66), but the high-g full-scale codes differ (Table 150 p93), so firmware uses only codes 001 / 010 (binding note). Orientation does not
qualify temperature, vibration, bias or high-g performance. U5 vent/foam/no-clean/
coating and transonic behavior remain open; LEDs stay dark until the actual
opaque-cover test succeeds. Qualify ≤ 50 ms first neutral, live-evidence reset
recovery and actual hinge/servo/flight behavior against the current vehicle.

Retained diagnostic/current limits are separate from the two single-fault-
qualified pyro ADC banks. PA6 uses 100k/10k without a pin tail: normal 8.4 / 11 =
0.764 V, but a shorted top can apply 8.4 V against the ADC-mode 4.0 V ceiling and
zero positive-injection allowance. PB1's 10k/1k top/bottom bank can approach
5.456 V through 10k after an open bottom; its estimated 0.15-0.19 mA clamp current
does not establish a safe 4.0 V pin. These single-fault pin-damage cases remain
owner deviations. PC8 = VBUS/2 needs about 4.62 V for nominal VIH 2.31 V; low PC8
never proves USB absent. See the exact current pin/qualification record (all DS12110 cites are now Rev 8, rev V chapter, D-R19-13, except the two labelled design limits read from Rev 11 Table 109 in round 14, the 6.0 V FT cap and the 4.0 V ADC-mode maximum; R27-TRI-04); ordinary diagnostic damage is not transferred to
PC0/PC5's retained split-top/parallel-bottom fault ratio.

The ESD103 ground clamps have recorded approximately 20/36/48 V TLP clamp levels
at 1/8/16 A, well above an I/O's operating limit. They and the 1k series resistors
do not establish installed cable ESD survival or powered-off isolation. Direct
GPS/radio FT digital limits differ from the camera translator's partial-power
behavior. Firmware must configure the correct digital inputs/pulls and obey
the no-self-powered-port rule. PC14's former 2.9 mA maximum is withdrawn: the
resistor-only initial bound is 3.3 mA nominal/3.363636 mA at 3.33 V/990 ohm initial
tolerance, with about 0.306 mA steady; driver/gate/all-temperature dynamics remain
unmeasured. Keep 4 kHz and LSE disabled; no unsupported minimum driver resistance
is credited. D-R12-01 and the regenerated pin table carry this correction.

PE4 is an active-high fire command (R18-MCU-03): PE4 high turns Q124 on; the net name PYRO1_GATE_N reads as active low and is not. Write ODR low before output mode and lock GPIOE_LCKR; the pin sits behind R127 1 kΩ at the pin, R126 220 Ω, R128 10 kΩ and C126 220 nF, which hold the gate at 0.104 V or less against a 30 kΩ internal pull-up
(AON7524 minimum threshold 0.4 V). PC1 did not have that margin with R123 at 100 kΩ (R18-MCU-01); R123 is now 2 kΩ, which holds the Q122 gate at 0.218 V or less against a 30 kΩ pull-up at 3.6 V (3.6 × 2 / 33; Calculation). Since D-R19-04, C123 10 nF also sits from Q122's gate to GND, so Q122 has the full AGENTS §2.4 network (R122 1 kΩ series, R123 2 kΩ pull-down, C123); the gate time constant is about 7.1 µs (Calculation). Never enable a pull-up, RTC_TAMP3 or the wakeup function on PC1 (whether those functions apply a pull is an Inference, RM0433 not re-read). After reset all GPIOs are analog with no pull, so AGENTS 2.4 holds.
The OSC_IN drive level could reach about 242 µW at worst-case ESR and swing (Inference); add an amplitude check at the first article.

Round 19 firmware obligations (D-R19-13, binding note and pin table; no firmware exists):
- **Port UART enable (R19-MCU-01).** U11 (TPS2121) IN1 is USB_LIMITED and IN2 is RAW_PROTECTED; ST low means IN2, the battery, powers the output ([TI SLVSEA3F](https://www.ti.com/lit/ds/symlink/tps2121.pdf) Table 9-3 p18, p21). Enable each port's TX alternate function (PD8, PB13, PC6) only while PA4 reads low, after a settling delay; park the pin analog, no pull, when PA4 rises or the PA6 watchdog trips. The round 18 text keyed this to the inverted polarity; it is corrected.
- **VREFBUF (R19-MCU-04).** VREF+ (U1.20) is tied to VDDA on 3V3A ([DS12110 Rev 8](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) Figure 95 p286, Table 189 p291). Keep VREFBUF_CSR at its reset value (ENVR = 0, HIZ = 1), never enable the buffer, and scale the ADC from VREFINT / VREFIN_CAL. Applying Table 9 note 7's "kept disabled" to this board-level tie is Inference (RM0433 not re-read).
- **Port map (D-R19-14).** J410, J420 and J440 are identical; firmware maps each device to a port UART (default GPS J410 USART3, radio J420 UART5, AUX J440 USART6). J9 is excluded.
- **One DS12110 revision (R19-MCU-02).** Every cite in the pin table and binding note is Rev 8, rev V chapter; the 6.0 V FT cap and the 4.0 V ADC-mode limit, read from Rev 11 in round 14, stay as labelled design limits (Inference: not in Rev 8).
- **VCAP (R19-MCU-05, R19-BOM-05).** Carried: C19 / C20 meet ST's nominal 2.2 µF; their operating C and ESR stay unqualified (D-R15-02; owner table row 10).

### 6. Routing cleanliness, AVA scope and returns

**Current PCB `a0ec075e…` (round 26 fix pass; routing as on `92c3ad59…` except the D-R26-01 / -02 / -04 copper in [Round 26 fix pass](#round-26-fix-pass); `92c3ad59…` was `1407e850…`, the round 24 board pass, with BAT_FAULT_N's chamfer at (16.55,83.35) capped by D-R24-18).** route_check 0 failing, 0 allowlisted, 0 stale, with 5 unrecorded noncritical leftovers (28 bump windows searched; every category's instance count as on `92c3ad59…`; docs-lane read-only run on a copy). **Plated-pin layer changes (D-R26-01, R26-TRI-09):** profile r10's `pad_layer_changes` treats a plated (PTH) pad that carries a return-required critical signal net's tracks on two or more copper layers as a layer change, and `critical_via_no_gnd` (layer 'pad') fails it with no GND via centre within 1.5 mm of the pad centre; the R7–R9 profiles keep the via-only test. On `92c3ad59…` it finds J440.3 (AUX_TX_WIRE, 3.900 mm) and J440.4 (AUX_RX_WIRE, 4.037 mm), F.Cu from the cell and B.Cu to the D440 / D441 clamps since D-R20-09; on `a0ec075e…` the GND vias (7.4,16.5) and (7.4,20.0) sit 1.500 mm from them (0.300 mm from their own pin's pad, 0.800 mm from the neighbouring pin's), and no other plated pad qualifies (J400.2 is AUD-2-slow, J1.1 is power, and J121, J122, J410, J420, J9, J3 and J2 carry one copper layer each). K-region now exempts a pad's In2 void where it merges with its GND partner via's antipad (the sample must still lie in the pad disc). **No 90° bend remains (D-R24-17, owner 2026-11-01):** every bend between two segments is 45°; the new RULE category `right_angle` fails, on every net and copper layer with an empty allowlist, two track ends of one net and layer meeting at 89.5–90.5° with nothing else there, and a bend at a pad or via whose copper leaves the bend's inner corner bare (a T or three or more ends is not a bend). The pass took 59 bends to 0 (F.Cu 25, B.Cu 31, In2 3): the chamfer pass cut 54 plain bends (including D402's tap) and the 6 pad / via bends and U9's input trunk were redrawn at source; pairs that turn together keep their pitch, and J440's clamp runs each got 0.211 mm shorter. **Review-only residual (AUD-10, D-R24-09):** U401's OUT run meets the C406.1 run at a T (29.75, 12.85) that lies 0.075 mm inside R402.1's land (route_check counts it as pad_end_offcentre / segment_inside_pad, 0.325 mm; not blocking). Both measured alternatives are worse: the C406.1 drop on the land's centre line (x 30.075) passes 0.085 mm from J440's second via (30.5, 9.95), and a T clear of the land puts the OUT via 0.057 mm from GPS_RX_MCU's F.Cu chamfer unless that run, the split via and C406.1's exit all move. The single-via taps K-power still excepts are in owner rows 22, 27 and 29 (SINGLE_OPEN_EXCEPTIONS 22 → 11). The detour table below is recomputed on `a0ec075e…`. **Previous PCB `5516eeec…`.** route_check 0 failing (22 bump windows; 6 unrecorded noncritical leftovers: the BAT_ENABLE jog fixed and its chain critical, D-R21-04); counted, not gated: U2.1's run started 0.35 mm off the pad centre, BAT_ENABLE kept a short layer hop, and R89's 3V3 via (23.0,70.0) had no GND partner within 2.182 mm (power_via_no_gnd). **Previous PCB `0dc84776…`.** route_check 0 failing; `--bumps-all` 148 information instances (USB_LIMITED's extra bends went with TP82's move; nothing added). **Previous PCB `50a39de5…`.** `route_check --profile r10` reports 0 failing (22 bump windows; 7 unrecorded noncritical leftovers, was 6), unchanged by the gate pass. The round 20 routing lens ran `--bumps-all` on this board with the committed checker (R20-RTE-07): 149 information instances, 0 failing, 7 unrecorded leftovers (`a3144b15…` with the same checker: 140 and 6). It added 11 instances and removed 1: a new detour leftover on USB_FAULT_N at (12.1,23.0), 33.91 / 20.89 mm (ratio 1.62; R90's move shortened the tree); extra bends on GPS_TX_MCU, GPS_RX_MCU and USB_LIMITED; short layer hops on BAT_ENABLE B (19.675,66.6), PORT_4V8 B (29.75,9.95) and F (30.5,9.95), PORT_5V3 B (25.65,14.9) and B (42.0,61.8); power vias without a GND partner on PORT_4V8 (29.75,9.95) and VLOGIC (29.8,81.15); removed: an off-centre pad end on USB_FAULT_N at R90.2. Short layer hops are now 8 and off-centre entries 56. The per-net figures further below are `a3144b15…`'s unless noted.

**Round 20 routing and copper records (docs only; measured on `50a39de5…` by the round 20 lenses).**
- *R20-RTE-02, fixed by D-R20-03 on `0dc84776…`.* A via-less 0.282 mm² F.Cu GND piece at (17.50,34.48) touches only U1.74 (also on `a3144b15…`). The gate's pour-debris check admits it by one exact, named entry that fails once the piece is gone. Fix: `ZONE_CONNECTION_NONE` on U1.74, as D-R19-05 did for U1.19; U1.74 keeps its run to via (17.5,39.3).
- *R20-RTE-01, fixed by D-R20-04 on `0dc84776…` (TP82 at B(11.2,20.7), stub 0.849 mm).* TP82's move to B(11.0,17.6) (D-R19-14, M-6) lengthened its USB_LIMITED dead-end stub 1.0 → 4.03 mm with two bends. B(11.2,20.7), on the extension of the existing diagonal, would give a 0.85 mm collinear stub (Inference, not DRC-run).
- *R20-RTE-03, recorded.* The re-routed GPS pair (USART3 PD8 / PD9) takes two forced 45° jogs per trace, because C90's fan-out vias (26.425,32.075) and (26.425,30.525) sit in the PD9 escape. Respin: move them west and redraw each trace as one diagonal.
- *R20-RTE-04, recorded.* The VLOGIC parallel via pair (D-R19-09) sits on 0.42 mm doglegs and a 0.85 mm diagonal (a 2.6 mm loop); an in-line pair on the y 81.75 branch is the respin option.
- *R20-RTE-05, fixed by D-R20-09 on `0dc84776…` (D440 / D441 under J440, 4.08 / 4.18 mm of track from their pins, 3.157 / 3.194 mm centre to centre in a straight line, 1.865 / 1.900 mm pad edge to pad edge; the tracks are 3.864 / 3.964 mm on `a0ec075e…` since D-R24-17).* Before: J440's ESD clamps sit 6.2 mm from its pins (J440.3 → D440.1 6.23 mm, J440.4 → D441.1 6.18 mm), against 3.1–3.4 mm at J410 / J420, because J440's cell is on the top east of its courtyard. Respin: move D440 / D441 toward J440.
- *R20-RTE-06, recorded (adds to R19-RTE-04's under-body list).* C89: R167.2's GND via (13.536,85.161) is 0.186 mm from the BAT_IN pad C89.1, under the 1206 body. Five 1210 capacitors also have a via between their pads at 0.40–0.75 mm: C400, C405, C411, C421, C461.
- *R20-RTE-07, corrected.* D-R19-09's nearest-copper figure for the U401 IN via (26.45,11.95) is 0.929 mm, not 2.000 mm (it was measured before the J410 pair moved). D-R19-01's void left a dead-end In2 GND_CH1 finger with a 0.60 mm neck. The surface adjacency inventory in §1 is still the `a3144b15…` one; it has not been re-run on this board.

**Round 19 routing records (R19-RTE-01 … -08; measured on `a3144b15…` unless noted).**
- *R19-RTE-01, fixed.* A via-less 1.693 mm² F.Cu GND fragment hung on U1.19's pin tip (x 25.12–27.15, y 51.24–53.45). D-R19-05 sets U1.19 to no pour connection on the board, so the fragment is no longer filled; U1.19 keeps its own stub and via (26.0,46.75).
- *R19-RTE-02, fixed.* TP121's 7.14 mm ACT_GATE stub to B(4,70) is removed with TP121 (D-R19-03). ACT_GATE is probed at R119.1 or R120.2, bare pads in the same cell, before coating.
- *R19-RTE-03, recorded.* D-R18-03 moved BAT_FAULT_N to x 27.37. That brought it 0.650 → 0.180 mm from the GND via (27.9,64.25) (R86.2's fanout) and 0.850 → 0.380 mm from the 3V3 via (28.1,60.0) (R91.1's fanout). Both pass DRC (0.15 mm). BAT_FAULT_N is a slow open-drain status line: a GND bridge asserts the fault and a 3V3 bridge masks U9's fault flag (a diagnostic loss, not a hazard). Moving the two fanout vias out from under their resistors in a respin restores at least 0.45 mm.
- *R19-RTE-04, recorded (owner M2 list).* Six 0603 resistors carry a fanout via centred under the body, 0.175 mm (ring) from both pads: R86 B(27.9,64.25) GND via between LOGIC_ILIM / GND; R89 F(23.0,70.0) 3V3 via between 3V3 / BAT_FAULT_N; R91 B(28.1,60.0) 3V3 via between 3V3 / LOGIC_SOURCE_ST; R101 B(34.0,42.0) CAM_UART_OE via between CAM_TX_BUFFER / CAM_TX_WIRE; R401 F(13.0,1.8) GND via between PORT_FB / GND; R403 F(31.4,14.4) GND via between PORT_LDO_FB / GND. R403's via (31.4,14.4) was removed by D-R24-09 on `1407e850…`, which moved R403 to B(30.9,14.6); five remain on `92c3ad59…` and `a0ec075e…` (R86, R89, R91, R101, R401; under-body via scan of every two-pad part, round 26 docs lane; R26-TRI-07).
  DRC and the M2 via-to-opening rule pass. It is an untidy pad-entry pattern (each fanout leaves the outer pad inward to a via between the pads, where a bridge cannot be inspected). A bridge costs a pull-up (R89, R91: diagnostic loss), joins CAM_UART_OE to the camera TX path (R101), or tightens an existing 0.25 mm GND gap to 0.175 mm (R86, R401, R403) (Inference). Respin: put each via beyond the outer end of its own pad.
- *R19-RTE-05 … -08, carried.* Layer-change returns over In2 rails, placement detours, the uncoupled USB pair and copper under U4's body are unchanged; see below and §8.

The finished native --bumps-all pass on `a3144b15…` (a read-only run made for these records) has 139 actual route information
instances: 111 ordinary + 22 AUD-10 inside-pad + 6 noncritical hygiene leftovers, 57 off-centre pad entries and 45 all-net bump windows searched (one new u-turn on PYRO1_CONT_MID at B(16.87,60.13)). On `632a9ad3…` it was 140 instances (111 + 23 + 6), 59 entries and 46 windows. Blocking, critical-allowlisted and stale
counts are zero. Location-only leftovers appear once in
`r10_final_deviations.json#/routing_inventory/noncritical_leftovers_once`.
The current exact partition and numerical reference/region scopes are in
round15_fix_native and the fresh full round16_routing report. The new exact-
duplicate topology guard preserves the unchanged 140 annotations and 46 window
bump inventory; duplicate-only representations remain review information. R14 manual near-entry/lane/slow-companion measurements
remain explicitly scoped historical observations; part/via identity transfers
unchanged geometry only, not an unexecuted current copper search. Supplemental
search sketches do not add actual instances or prove global optimality. The
qualified SD_MOSI alternative saves 1.994603 mm/two segments with unchanged
0.20 mm width, anchors, layer and vias. It was retained as an avoidable M2 Minor under D-R16-03 at
the R16/R17 pair; round 18 found it again (R18-RTE-04) and the round 18 fix pass adopted the redraw as a board change (SD_MOSI 36.098 → 34.104 mm, 12 → 10 segments, D-R18-07).

Fifteen bounded fixed-anchor redraws were adopted through generators; the
separate outward IMU GND escapes implement the recorded stress-guidance choice
with unchanged pads/vias. M2 information and noncritical return-path compromises
remain deviations. C98's unchanged GND stitch still has its 0.300 mm centre offset/
0.050 mm ring overlap; it contacts saved ground fill. The rejected 0.424 mm jog
would introduce a tiny jog. Actual USB transfer/loop inductance remains untested.

AUD-10 changes only its named
categories/legend distance; partial overlaps, crossings, connectivity and critical
hygiene remain blocking. All M2 compromises await owner acceptance.

The R14 manual routing receipt records 57 off-centre entries, four between-pad routes
(minimum 0.200041 mm), the 0.05 mm U4 MOSI entry offset, and five literal near-edge endpoints across L1.2, R432.1 (0.020 mm polygon depth) and ACT_GATE R120.2. The older two-AABB-endpoint count used a different test. NRST/BOOT0/I2C companions remain outside the named fast
numeric rule: maximum 3.679674/1.662077/2.232543 mm respectively. Three short
layer-hop information items and 11 slow AUD-2 split/void observations remain (5 run, 5 pad and 1 connected-chain; not 11 distinct nets).
Fast reference/region and required partner rules pass; no scope expansion or
blanket impossibility of alternatives is claimed. Its Y1 foreign top
projection is NRST 0.777817 mm with In1 GND between; old buzzer/QSPI projections
are absent. Bench reset/I2C/HSE/interface noise tests remain open.

The unchanged R13 LED_YEL redraw clears adjacent U1.89/SPI1_SCK copper by 0.150000..0.150001 mm, meeting native 0.15 mm but below the supplemental search 0.16 mm reserve. The actual DRC/reference/hygiene controls pass; the diagnostic reserve is not a new fabrication rule or proof that no other route exists.

AVA similarity is limited to visible rows, local repeated cells and shorter
battery/buzzer wiring. Images do not establish hidden copper, components or
safety choices. All retained M2 compromises await owner acceptance.

Per-net detours and extra vias (R18-RTE-03; refreshed on `a0ec075e…` by the round 26 docs lane, read-only, with the round 21 routing lens's method: `.supervisor/r21_routing/scripts/dump.py` on a copy of the board, then the `detour.py` calculation: routed track length against the octilinear minimum spanning tree of each net's pad centres, non-pour nets with at least two pads). The 116 non-pour nets total 1500.8 mm against 1236.6 mm (1.214×, +264.2 mm). Every net with an excess of at least +3.5 mm is listed: 23 nets on `a0ec075e…` (22 on `92c3ad59…`, where PYRO1_CONT_MID was below the line). On `92c3ad59…` and `1407e850…` the same method gave 1501.8 / 1237.8 mm (1.213×); on `5516eeec…` 1505.5 / 1236.9 mm (1.217×); on `0dc84776…` the round 21 lens measured 1507.8 / 1243.0 mm (1.213×); on `a3144b15…` 112 nets, 1454.9 / 1195.2 mm (1.217×). The vias column counts every via of the net, named second barrels included (D-R24-02 … -10). The largest excesses:

| Net | Routed / spanning tree (mm) | Excess (mm) | Vias | Cause |
|---|---:|---:|---:|---|
| USB_LIMITED | 81.62 / 53.39 | +28.2 | 4 | In2 detour around U1; R87.1's second barrel (16.6, 28.0), D-R24-10 |
| BAT_IN | 57.02 / 36.89 | +20.1 | 1 | the 1.0 mm U-loop to the board edge around C95.2; hot-plug-qualified; U9's input trunk re-laid (D-R24-17) |
| NRST | 39.48 / 25.27 | +14.2 | 3 | 13.8 mm of F.Cu inside U1's pad ring |
| USB_FAULT_N | 33.28 / 20.89 | +12.4 | 1 | U-turn around the SD vias |
| BAT_FAULT_N | 50.94 / 38.76 | +12.2 | 3 | pin map and placement (50.92 mm on `1407e850…`, before D-R24-18) |
| CAM_IO_3V3 | 25.09 / 15.89 | +9.2 | 2 | |
| SD_MISO, SD_SCK, SD_MOSI, SD_CS | 34.94 / 26.05, 24.26 / 16.75, 34.10 / 26.83, 34.10 / 27.47 | +8.9, +7.5, +7.3, +6.6 | 1 each | pull-ups R460–R463 north of J430 |
| BAT_ENABLE | 25.58 / 17.36 | +8.2 | 3 | the switch-end run to J400.2 (R81 / C87 at U9's end, D-R21-05) |
| PYRO1_OUT | 23.00 / 15.45 | +7.5 | 1 | the sense corridor excess sits on PYRO1_CONT_MID (D-R18-05); R173 0.65 mm nearer since D-R26-02 (23.65 / 15.72 mm, +7.9, before) |
| VBUS_SENSE | 25.27 / 18.41 | +6.9 | 3 | |
| VLOGIC | 45.33 / 39.04 | +6.3 | 4 | R60.1's second barrel (34.5, 62.4), D-R24-08 |
| VBUS | 24.47 / 18.26 | +6.2 | 3 | |
| CAM_PWR_EN | 30.34 / 24.90 | +5.4 | 1 | |
| ACT_GATE | 14.48 / 9.48 | +5.0 | 4 | Q120 / Q121's second gate barrels (D-R24-02) |
| CAM_FAULT_N | 25.17 / 20.26 | +4.9 | 1 | |
| SERVO2_MCU, SERVO1_MCU, SERVO3_MCU | 32.83 / 27.98, 32.61 / 27.95, 27.71 / 24.02 | +4.9, +4.7, +3.7 | 1 each | |
| PYRO1_CONT_MID | 10.57 / 6.81 | +3.8 | 0 | the corridor between R134.2 and Q123.1 behind R173 (D-R18-05); since D-R26-02 R173 sits 0.65 mm further from the corridor, and since D-R26-04 the run turns 45° at (16.87,60.82) to (17.85,61.8) (10.29 / 7.08 mm, +3.2, with a u-turn, on `92c3ad59…`) |
| ACT_EN_MCU | 24.36 / 20.85 | +3.5 | 0 | |

Below +3.5 mm: QSPI_IO2 +3.3 and USB_DM +3.1 mm (its J3 strap 0.422 mm shorter after D-R24-17). These are `a0ec075e…` figures (Calculation on native geometry; they do not establish a shortest route); against `92c3ad59…` only PYRO1_OUT, PYRO1_CONT_MID and 3V3A (36.56 / 33.97 mm, +2.6 as before, below the line) changed among the non-pour nets (D-R26-02), and `92c3ad59…` differed from `1407e850…` only in BAT_FAULT_N, 0.023 mm longer (D-R24-18). Against the `5516eeec…` table, the D-R24-17 chamfers shorten the runs they cut (for example SD_SCK 24.92 → 24.26 mm), and BAT_IN's tree shortened with C88's move (38.99 → 36.89 mm).

A diagnostic octilinear router, with placement and every other net fixed, recovers only a few millimetres per net: USB_FAULT_N −8.2 mm (its via must go to about (13.65,42.7), beside R32), VBUS_SENSE −4.7 mm and two vias, BAT_ENABLE −2.6 mm and two vias, the SD lines −2.0 to −3.6 mm each, and NRST −9.8 mm but only by threading U3's pins.
So most of the excess comes from placement and the pin map. AVA-level directness would need re-placement: the SD pull-ups next to the bus, a rotated input-capacitor column (which needs the F9-1 hot-plug re-extraction), a nudged R32, and BAT_ENABLE and VBUS_SENSE redrawn with one via each. These results are indicative, not qualified.

Layer-change returns (R18-RTE-02). Of the 25 required critical-signal vias, 21 have an In2 power rail on the B.Cu side (3V3 ×17, PORT_4V8 ×4); only the HSE and pyro vias sit over In2 GND. B.Cu is 0.203 mm from In2 and about 1.26 mm from In1, so the B.Cu return runs in the rail, and the gated GND via 0.77–1.43 mm away does not connect In1 to that rail.
The nearest rail-to-GND capacitor is 1.29–6.19 mm away (SD_MISO 6.19 mm, SD_SCK 5.33, SD_MOSI 5.07, SD_CS 4.84, all to C17; SPI1 5.04–5.77; QSPI_NCS 5.32; 13 of the 21 are beyond 4 mm, CAM_MCU_RX's 4.02 mm to C29 the thirteenth, R26-TRI-08; via centre to the rail-side pad centre, re-measured on `a0ec075e…`, unchanged); the In1–In2 sheet capacitance (about 3.8 pF/cm²) is too small to carry the return instead. This is a gate gap (no rule measures the via-to-capacitor distance) and is not fixed now;
a 100 nF 0402 3V3–GND at B(11.25,41.25) would bring the SD cluster to 2.3–3.4 mm in a respin (screened for clearance only).
The two plated-pin layer changes that route_check counts since D-R26-01, J440.3 / J440.4 (AUX_TX_WIRE / AUX_RX_WIRE, F.Cu to B.Cu), also sit over In2 3V3: their GND partner vias are 1.500 mm away, and the nearest 3V3-to-GND capacitor, C460, is 16.3 / 15.9 mm away (rail-side pad; round 26 docs lane on `a0ec075e…`, Calculation). Counted with them, 23 of the 27 critical layer changes return over an In2 power rail.

USB pair (R18-RTE-05). D+ and D− run on F.Cu 1.90 mm apart over x 11.1–15.85 with a VBUS via (11.95,30.6) and a GND via (15.6,30.5) between them, and 0.707 mm apart on the diagonals; the J3-to-U1 trunks differ by 1.75 mm (16.45 against 14.70 mm). Benign at full speed (Inference), but not a hand-quality pair; in a respin move the two vias and route DP alongside DM at 0.4 mm.

### 7. Silkscreen, drawing and courtyard residuals

**Round 20 manufacturing records (fixed by D-R20-06 / -07 on `0dc84776…`; 96 hidden, no courtyard offender, no Fab crossing).** As found on `50a39de5…`: R20-MFG-02: three visible designators sit inside a large neighbour's courtyard, nearer it than their own part: C400 in J440's (0.151 mm² overlap; new with D-R19-14), C94 in U1's (0.266 mm²) and R461 in J430's (0.306 mm²); the courtyard-nearest check skipped large parts. R20-MFG-03: in the assembly PDFs the Fab references of C445 (0.192 mm²), D440 and D441 (0.048 mm² each) and C123 (0.001 mm²) cross their own Fab outlines (new), and R119's does too (carried; it prints as "R1119" at 1200 dpi). The gate lane admits each by a named entry; the fix is a designator and Fab-offset change in `r10_post.py` at the next board change.

Current (`a0ec075e…`) 123 visible / 93 hidden silkscreen references plus 44 legends use ≥ 1.0 mm text and
0.15 mm stroke (124 / 92 on `92c3ad59…` and `1407e850…`; 122 / 93 and 45 on `5516eeec…`; 119 / 96 on `0dc84776…`; 121 / 94 on `50a39de5…`; 120 / 88 and 40 on `a3144b15…`; 118 / 91 on `632a9ad3…`). The round 20 polish pass hid C94, R461, C404, R90 and U401 and showed C28, D440 and D441 again (D-R20-06); the round 21 fix pass showed C126, Q122 and R122 again and moved C80, C87, C89, D123, D8 and R81 (D-R21-09); the round 24 board pass hid C87 and R402 and showed C16, C20 and C404 again, D402's designator is shown, and the JLC order-number placeholder is removed (D-R24-13), so the legends go from 45 to 44; the round 26 fix pass hid C18, whose spot now lies on C11.2 (D-R26-02; no other spot exists, even with C18 placed first). Newly hidden on `50a39de5…`, kept on F.Fab: C28 and R110 (J440's courtyard and R90's move took their spots), C123, D440, D441 and R88 (no unambiguous spot). TP121 is removed. All 93 hidden references are listed in the current M3 record
and retained on Fab; correct individual pin labels and clear mask/edge geometry
remain blocking. J122's visible Fab glyph clears the drill by about 0.093 mm.
The five R12 corrected labels remain; 77 additional Fab-reference-only overrides
clear borders, pin 1 dots and LS120 polarity text. All 209 references/722 rendered
characters (on `632a9ad3…`; not repeated for the 216 on the current board) are checked against 1018 Fab shapes, two polarity texts and 37 drill/
cutout polygons. All 77 corrected references survive 0.025 mm glyph inflation;
132 references and every non-reference object remain unchanged. Actual Fab text
ranges 0.3..1.0 mm (the existing C80/D8 0.3 mm labels are preserved); vector zoom
and first-article identification remain obligations. Silkscreen stays ≥ 1.0 mm.
Final regenerated complete pages/details are checked in the integration receipt.

All 209 native courtyards were inspected in full round 14: 16 stroke-overlap
pairs remain (6 top / 10 bottom), rather than the earlier three-pair inventory. A read-only re-measurement on the 208 footprints of `a3144b15…` finds the same 16 pairs at the same locations and polygon gaps; only the R400/L400 nominal model gap changes, because L400's model body is 5.4 mm instead of 5.5 mm deep.
Native collision polygons remain separate with 0.010..0.040 mm gaps; nominal
model-body gaps are at least 0.499938 mm. The following complete inventory gives
coordinates, polygon gap and ink penetration (actual 0.050 mm combined half-strokes minus polygon gap); these are CAD measurements, not
component-tolerance or assembler-access qualification. Parts/courtyards are
preserved by the route-only successor comparison. Retain owner/assembler
first-article inspection; no physical collision is proved by overlapping ink.

| Pair / side | Location mm | Polygon gap mm | Stroke penetration mm | Nominal model gap mm |
|---|---|---|---|---|
| C97/D123 F | 23.560,63.310 | 0.030 | 0.020 | 0.874882 |
| R400/L400 F | 21.040,2.540 | 0.030 | 0.020 | 0.820061 (0.781025 on `632a9ad3…`) |
| R32/LED1 F | 10.465,42.120 | 0.040 | 0.010 | 1.300002 |
| LED2/R33 F | 10.065,45.545 | 0.020 | 0.030 | 0.648569 |
| C60/R60 F | 33.200,58.165 | 0.040 | 0.010 | 0.749964 |
| R121/D8 F | 14.500,72.745 | 0.020 | 0.030 | 0.854874 |
| C85/R86 B | 27.900,64.987 | 0.025 | 0.025 | 0.674999 |
| C421/U12 B | 32.688,38.350 | 0.010 | 0.040 | 0.500000 |
| R152/D121 B | 33.215,70.260 | 0.020 | 0.030 | 0.949914 |
| R64/U5 B | 11.230,51.405 | 0.020 | 0.030 | 1.179750 |
| U4/C31 B | 15.135,46.875 | 0.040 | 0.010 | 0.550194 |
| D121/R151 B | 33.215,72.740 | 0.020 | 0.030 | 0.949914 |
| C22/C26 B | 26.435,45.935 | 0.040 | 0.010 | 0.827540 |
| C83/C28 B | 11.690,24.900 | 0.030 | 0.020 | 1.249900 |
| Y1/R10 B | 20.885,44.705 | 0.040 | 0.010 | 1.101582 |
| C18/C30 B | 17.475,49.140 | 0.020 | 0.030 | 0.499938 |

The conservative C91/C92 envelope gap remains 0.010 mm versus native collision-
polygon gap 0.110 mm. Adjacent 4P terminal bodies have 0.480 mm gap and courtyard
ink 0.030 mm gap. Inspect real component tolerances and workmanship.

All 167 visible silkscreen texts (123 references and 44 legends on `a0ec075e…`; 168 on `92c3ad59…` and `1407e850…`, 167 on `5516eeec…`, 164 on `0dc84776…`, 160 on `a3144b15…`) are at JLC's minimum, 1.0 mm high with a 0.15 mm stroke (1 : 6.7 against the preferred 1 : 6; R18-MFG-04). Legibility only; if respun, use a 0.17 mm stroke on legends (not on designators crowded near pads).

Word and pin legends (R19-MFG-01, R19-MFG-04, R19-MEC-01; D-R19-06, -08, -12; measured on `50a39de5…`). RADIO now lies inside J420's courtyard span (4.825 mm inside; 5.767 mm from J410's box), GPS inside J410's, and the new AUX word inside J440's; `WORD_SEAMS` is empty and there is one word list.
Every top-side pin and word legend is wholly outside every DB125 fit envelope (smallest 0.133 mm), and no line mixes two terminals. 2:E1+, 2:SW and J440's 2:GND, 3:TXO and 4:RXI are on the bottom beside their pins.
BAT and SWITCH keep thin identity margins (0.060 / 0.040 mm ink-gap; word-centre margins 0.080 / 0.040 mm against the gate's 1.0 mm, reported only, D-R19-15): each fills the 1.19 mm gap at its terminal's north end, and no spot there gives more; each is now the only text on its line. The vertical designators of J1, J121, J400, J410, J420, J440 and J9 touch their envelope's edge by 0.060–0.087 mm and read whole in the render.
After wiring, the wire-side legends are covered by the wires they label, so pin identity is checked by a harness continuity test before first power (ORDERING 8.3), not by eye.

### 8. Mechanics, access and retention

The complete maximum DB125 body unions give 5.003012 mm bare-bore wire room
for all eight terminals (J440 has J121's room; CAD pass on `50a39de5…`),
only 0.053012 mm above the owner 4.95 mm floor; P2's wall/axis allowances and
actual ferrules/bends still need physical verification. Body/bore minimum is
2.976269 mm (on `a3144b15…`). DB125 insulating-body models reach 8.90 mm; all 27 tails of the eight terminals (J440's since its addition) have separate
fit allocations using each native pad XY box and 3.80 mm maximum below the seating
plane (conservative Inference). Minimum tail/bore clearance 7.558359 mm (unchanged on `a0ec075e…`) and 2.20 mm
projection below the PCB leave 1.80 mm to a nominal 4 mm sled plane. Real seating,
solder fillets, bent tails, washer/screw/nut, screwdriver and staking access
remain unqualified; the VRML files alone do not model the tails. Its top washer at (4,4) is 3.93 mm from the fit envelope (≥ 3.8 mm) and J3's courtyard is 1.67 mm away (CAD pass).

Keep all five supports, nut on sled side/head on top, both recorded centring
tolerances and nut-inclusive hardware bounds. Minimum current bottom/top
hardware clearances 4.536177/3.807887 mm meet the 3.5/3.8 mm rules. Program J2
before fitting the nearby mid support, or remove it. Bottom SD/card fit is a
closed-envelope check: remove/unbolt the PCB from a continuous sled before
opening the unpowered hinge, or qualify an access window. The 15.05 × 15.70 × 2.10 mm
closed allocation includes maker nails/tolerances; common seating/card front
remain Inference. Native bore clearance 15.210798 mm and C23 courtyard gap 0.575 mm
do not qualify the actual assembled/socket/card maximum.


U5's 1.1 mm modeled height is a conservative engineering allocation; TE's
MS5611-01BA03 Fig 18 gives 1.0 mm+0/-0.10. Keep the allocated 2.9 mm cover gap at 4 mm
standoffs; qualify real solder seating, foam compression, adhesive, venting and
barometer response. Correcting source attribution changes no model or CAD.

The optional plate diagnostic, re-run on `50a39de5…` by the round 20 mechanics lens (R20-MEC-02, Calculation/Inference) and again on `5516eeec…` by the round 22 mechanics lens, with identical figures (not re-run on `1407e850…`, `92c3ad59…` or `a0ec075e…`; the only added part, D402, is a two-pad TSLP clamp, and round 26 added two vias and moved four small passives by 0.60–0.65 mm, so the mass change is negligible, Inference), gives a first mode of 180.8 Hz pinned (D5; 181.1 Hz on `632a9ad3…`) for an estimated 78.6 g of board and local-wire mass (was 70.5 g); the 256.1 Hz (D10), 287.9 / 407.1 Hz clamped and 1.24 mm maximum 100 g
deflection figures are from `632a9ad3…`. No modal release floor or vibration test is inferred. Qualify
5 × 100 g retention, supports, shroud, board wholly forward of joint + 47 mm with
axial tolerance, every roll orientation, external module/antenna/harness volume
and actual bore/stack. Selected 4 mm standoffs give a 0.261 mm modeled 100 g gap under C431 (was 0.271) and 0.320 mm under C421 on `50a39de5…`; the 3.5 mm sensitivity overlaps C431/C421. This is a local D5 calculation, not physical shock/clearance proof. Freed PCB length stays slack under OQ-7.

The specific remaining U4 B.Cu component-side paths depart from ST TN1383
Rev 1 pp. 7–9 pad-axis/outside-body stress guidance. Lens 0.001 mm midpoint sampling
records IMU_CS 0.7596 + 0.0918 mm, MISO 0.3257 mm, INT1 0.3250 mm and 3V3A 0.3257 mm
under the nominal body outside lands. Exact interval engineering gives 0.760+
0.091923882,0.325,0.325,0.325 mm respectively; these different diagnostics
are not physical measurements. Signal/supply widths 0.20/0.25 mm also differ.
A bounded supply sketch has only 0.106949 mm clearance and is rejected; the
revised combined alternative passes its local 0.16 mm screen but creates a
45 degree free IMU_CS junction at B(14.2,44.7), so it too is rejected. No full
native refill/DRC/reference or build qualification is credited to that sketch.
Retain this explicit advisory departure with first-article bias/temperature/
vibration and process qualification; M-7/P3 passing is narrower than complete
TN1383 compliance. Sources: round16_mechanics and round16_minor_prototypes. No copper under U4 changed in rounds 18 or 19 (R19-RTE-08, carried); the fitted part is now ISM6HG256XTR on the same land.

Round 18 mechanics (R18-MEC-01 to -03). East-edge asymmetry: J122 + J410 + J420 + J9 = 34 g of the 70.5 g board sit on an 82 mm unsupported east edge while the mid support (4,44.3) is on the light west side. At 100 g with D5 pinned the reviewer's run gives peak strains of J410 1359, J420 1348, J9 1312, C431 1232 and J400 1155 microstrain, and 1328–1417 microstrain at R150–R155; C431 deflects 0.973 mm against a 1.30 mm static gap to a 4 mm sled plane, C421 0.897 mm (Inference; none of these parts was in the reported strain table; the gate lane added J410, J420, J9, J400, C431, C421 and C411 to the tool's table, R150–R155 were added in the round 19 gate pass (R25-TRI-08), and the plate calculation was not re-run for these records).
J9's body (y 40.3–55.82) and J122's (y 62.55–81.57) leave 6.73 mm at x = 42, too little for a 7 mm washer. Screws, nuts and washers at all five supports must be nylon or otherwise insulated: at (4,44.3) the exposed LED2.2 GND, LED1.1 GND, J2.1 3V3 and J2.3 NRST lands lie 3.808, 3.860, 3.880 and 3.987 mm from the centre (J2's round lands, R24-TRI-09; 3.871 / 3.918 mm were bounding-square figures) against the 3.8 mm washer gate (0.008 mm margin at LED2.2).
Wire room (5.003 mm) is measured to the nominal Ø 50.8 mm bore wall at 5 mm height without the 0.5 mm wall allowance (4.493 mm with it; R23-MECHANICS-01, R26-TRI-10); `fit_check` printed three terminals before the round 18 gate lane, then all seven, and now all eight (5.003 to 5.603 mm at the CAD pass on `50a39de5…`).

Round 19 mechanics (R19-MEC-01, -02). The pin legends are now outside the DB125 bodies (D-R19-08), but wired terminals hide their wire-side legends: ORDERING 8.3 adds a harness pin-identity continuity check before first power.
C84's hand-fit heats five bottom joints under its lands (L1.1 SW_NODE, L1.2 3V3, C7.1 VLOGIC at its edge and C7.2 GND under land 2; C9.2 GND under land 1), the near joints C9.1 3V3 (0.545 mm) and C8.2 / C8.1 (0.605 / 0.814 mm), and R166, 0.56 mm from its courtyard, through 1.6 mm FR4 (XY projection of C84's lands onto the B.Cu pads, R26-TRI-11; the same on `a0ec075e…`). ORDERING 8.2 now limits the time and temperature, asks for top-side preheat with the bottom supported, and re-inspection of those joints (L1, C7, C8, C9 and R166) with a 3V3 and VLOGIC check after fitting.

### 9. Parts, lands and fabrication process

| Item | Measured reason retained | Required closure |
|---|---|---|
| DB125 holes and process (R18-BOM-02: the maker's pin is 0.50 x 0.85 mm, 0.986 mm diagonal, leaving at least 0.234 mm in JLC's 1.22 mm minimum hole and an annular ring of at least 0.235 mm against 0.20 mm; the carried 0.70 x 1.05 mm corner would not fit the maker's own 1.20 mm hole, so it is not a credible insertion failure: Inference) | 27 nominal 0.50 × 0.85 mm contacts on eight terminals (J440 adds four; R19-BOM-04 carried), 1.30 mm finished holes/1.90 mm lands; metal tolerances/form unresolved. Conditional 0.70 × 1.05 mm sharp diagonal 1.261943 mm exceeds conditional JLC minimum 1.22 mm. CAD S-8 wall minimum 1.021 mm (PYRO1_OUT via; 1.050 mm at J121.1 and the load-switch and enable barrels; J121.1 and J400.2 carry no unconnected inner rings since D-R20-05, §1; every plated pad hole is ≥ 0.55 mm from inner copper since D-R21-01, JLC 0.3 mm) is not a certified fabrication stack | Maker insertion/pattern envelope, fabricator finished-hole/registration/annulus/S-8 allocation and all 27 first-article seating/plating/solder-fill checks; no blind drill enlargement |
| C19/C20 VCAP (R19-MCU-05, R19-BOM-05, carried) | Exact Samsung CL10A225KO8NNNC 2.2 µF 16 V X5R ±10 %; nominal range 1.98–2.42 µF fits ST's 2.2 µF ±20 % (DS12110 Rev 8 Table 124 p216), but combined bias/temperature/AC/aging and ESR are unbounded | Establish ST Table 114 measurement conditions, both effective-C limits/ESR and actual regulator modes/process/temperature/transients; no arbitrary larger-cap substitution |
| L400 land (R18-BOM-03) | Closed by the round 18 fix pass (D-R18-08): the board now has Bourns' 2.0x1.8 mm pads at +/-2.25 mm (inner 2.50, outer 6.50 mm). `632a9ad3…` had a 1.8x2.5 mm proxy at +/-2.35 mm (inner 2.90 mm), whose worst heel could reach x 1.30 against a pad edge of 1.45 mm; the JLC EasyEDA proxy residual is now 0.05 mm | First-article heel-wetting inspection; a factory image is not a soldered first article |
| Camera U12 | Only surviving TXU0202; supplier residual/orientation method is scoped to this part, not removed U411/U421 | Factory preview/pin 1 and first article |
| C84 | Supplier MA-series sheet lacks maker land/reflow/cycle qualification; derived 3.5 x 1.7 lands at +/-3.25 | Manual fit after both reflows under separately validated/accepted operation; polarity/height/capacitance/ESR checks. R18-REQ-10 / R18-MFG-06: it is not in the JLC upload BOM and CPL (the round 18 fix pass moved it to the owner BOM `m3_bom_owner.csv`). R19-MFG-02 / R19-BOM-02: its lands have no stencil aperture since D-R19-07 (paste F 249 / B 381 on `92c3ad59…` and `a0ec075e…`; R24-TRI-12). R19-MEC-02: limit heat and re-inspect L1, C7, C8, C9 and R166 after fitting (ORDERING 8.2; C8 added, R26-TRI-11) |
| U401 | Only vias (27.3,13.6)/(27.9,13.6), 0.5/0.3, may enter soldered pad 11. No fabrication file carries the fill-and-cap request (R18-MFG-03) | Resin-filled, copper-capped planar VIPPO quote and inspection; fallback in ORDERING 8.1 if JLC cannot mix per via; ordinary via rules elsewhere |
| U4 mask (R18-MFG-02) | 0.50 mm pitch, 0.35 mm land width. `632a9ad3…` had 0.025 relief and a 0.100 mm web: 13 neighbour pairs at exactly JLC's green minimum. The round 18 fix pass removed the relief (D-R18-08): the webs are 0.150 mm | Fabricator acceptance and first article |
| Same-net close vias | Native copper ring/land gaps down to 0.014 mm; these are not fabricated mask-web measurements and holes stay outside ordinary pads | Tenting/mask and solder-wicking inspection, no unapproved via-in-pad |
| Part identities/options | JLC BOM 81 lines (45 Extended / 36 Basic), 206 placed parts (CPL 70 top + 136 bottom on `1407e850…`, `92c3ad59…` (byte-identical) and `a0ec075e…`, where the round 26 fix pass moved the C10, C11, R164 and R173 rows; orientation 192 reconstructed (67 top + 125 bottom) + 14 placement-only; 205 and 72 + 133 on `5516eeec…`), plus C84 on the owner BOM (197 placed on `a3144b15…`; 82 codes, 199 fitted on `632a9ad3…`). Round 19: U4 ISM6HG256XTR C51931514 (LSM6DSV320X C26633007 the second-fallback alternate (needs part fields, BOM and CPL regenerated: ORDERING 8.1); CPL rotation 0 → 180° from the EasyEDA footprint, confirm pin 1 in JLC's bottom-side preview), C87 C21120 220 nF, C123 C15195 10 nF, the AUX cell on existing codes. Proposed X7R-to-X5R merge unadopted, no saving credited; R430 is the stocked drop-in C2999509 since the round 18 fix pass | Exact BOM/MPN/land, preview and supplier data; no unqualified substitutions |
| Panel/THT assembly | Explicit thermals on all six DB125 GND contacts (J1.2, J9.2, J410.2, J420.2, J440.2, J122.5); tabs/rails/process remarks are CAD only | JLC acceptance of aft tab/rail, no-clean/two U5 reflows, THT fill, VIPPO, manual C84, consignment and first article |

### 10. Cost, stock and owner items

The exact-code snapshot on the final files of `a0ec075e…` (stock 2026-11-02T12:43:17Z, cost 12:44:13Z; re-run because the round 26 fix pass moved four CPL rows; 82 codes: 81 JLC BOM lines plus C84 on the owner BOM; the cost file binds the JLC BOM `00af5358…`, owner BOM `c48868b3…` and current CPL `1f899750…`, the stock file binds the BOM and owner BOM only, by design) gives **$85.26 per board placed** (parts $60.47 including C84, plus $24.79 feeder share over 81 charged codes) against the $84.41 target. **M3 is not met: $0.85 over.** On the same BOM the 01:43:55Z run (final files of `1407e850…`, kept by `92c3ad59…`) gave $85.60 (parts $60.81); the $0.34 is JLC price movement on eight lines. On `5516eeec…` it was $85.37 (2026-10-31T23:24:13Z), and $85.36 on the round 24 board before D402; D402 added $0.24 (its ninth C535146 piece at $0.2306 plus price movement).
With JLC minimum purchases (U9's minimum is 7) parts are $61.01, about $85.80 per board. In round 19, items 1–13 of the fix pass alone gave $84.21 ($0.20 under; U4 ISM6HG256XTR at $14.34 against the LSM6DSV320X line's $9.27). The AUX port adds $1.14 ($0.403 terminal, $0.271 22 µF, 2 × $0.231 ESD, resistors and 100 nF).
**Owner decision pending (owner table row 14):** accept the overrun, or change the AUX parts; changing its ESD or 22 µF breaks the identical-port intent. `check_procurement --cost-only` fails and was not weakened. Earlier snapshots: $79.12 on `a3144b15…` (2026-10-30T23:51Z), $79.5232 / $81.8636 on `632a9ad3…`.

The target is $84.41 per board, R3's cost per board for parts plus JLC feeder fees only. With JLC's fixed fees ($83.96 per order = $16.79 per board at 5 boards) the figure is about $102.05; with the handling fee JLC may add ($14.93 per order = $2.99 per board) about $105.04. The PCB and rails, VIPPO, manual C84, consignment, attrition, shipping and tax come on top. This is not a complete quote.

Stock: no line is short by `stockCount`. U4 (ISM6HG256XTR, C51931514) shows 9 in stock but only 2 orderable (`canPresaleNumber`; LCSC 0), so the stock check (`stock_check.json` 2026-11-02T12:43:17Z) fails on U4, 2 orderable against 5, and on U9 (TPS259470LRPWR C3662793: 30 in stock, −81 orderable, minimum purchase 7); it reads JLC's `canPresaleNumber` as the orderable quantity, an Inference about JLC's field. For both, confirm the quantity in the JLC cart on order day, else consign franchised parts (R20-BOM-01); for U4 that means consigning franchised ISM6HG256XTR (same CPL rotation and register map), with the LSM6DSV320X, also unavailable at JLC and LCSC, only as a second fallback (R21-BOM-02). Since D-R19-11 a JLC-stocked IMU that meets F1 and F2 (±4000 dps, high-g ±32…256 g) is fitted on the same land; the round 18 sentence "No JLC-stocked IMU meets both ±4000 dps and at least ±64 g" (R18-m14) is out of date (R19-BOM-01).
LSM6DSV320X (C26633007, 0 in stock at JLC) is the second-fallback alternate (needs part fields, BOM and CPL regenerated: ORDERING 8.1). C2757925 (the four-way DB125) is four per board and C535146 (ESD103) nine per board since D402: 35,895 and 196 in stock, 35,052 and 189 orderable, against 20 and 45 (2026-11-02T12:43:17Z). Obtain the process and panel quote and a fresh final-BOM/CPL cost and stock run within 24 h of ordering.
Owner acceptance of the entire deviation list and retained agent choices is pending. No accepted quote or order is recorded.

### 11. Historical applicability and vehicle handoff

The JSON gives all 46 historical groups and 229 prior finding rows explicit current,
closed, mixed or superseded dispositions, preserving their source pointers. Do not retain
removed GH ports, J124/fuse/pull-pin, translator/switch APIs, old three-bank
sense/tails, header/tie-hole geometry or obsolete prices as current facts.
An old fuse-rating mismatch can close while the intentional unfused risk stays;
old RC values can retire while current 100 ms settling qualification stays.

The separately owned VEHICLE mirror remains stale. The in-worktree [vehicle handoff](R10_VEHICLE_HANDOFF.md) gives
current eight-terminal poses (with the AUX port J440), single switch, always-on ports, SD access,
support/hardware and integration limits. No other worktree may be edited.

### 12. Every agent decision

The JSON indexes the 126 unique D-* IDs, including suffixes through D-R17-04; `R10_DECISIONS.md` now holds 229 unique D IDs through D-R29-02 (D-R18-01 … 11, D-R19-01 … 15, D-R20-01 … 11, D-R21-01 … 09, D-R22-01 … 07, D-R23-01 … 11, D-R24-01 … 23, D-R25-01 … 03, D-R26-01 … 04, D-R27-01 … 03, D-R28-01 … 04 and D-R29-01 … 02 are not yet in the ledger; they are listed in the owner decision table's "Decisions after the ledger"),
by ID/title/current applicability/reason, and all 23 owner-mandate records/amendments.
Review-process decisions do not infer owner acceptance of an electrical or
mechanical tradeoff. Each decision has its reason, scope and source line. D-R17-01..04 correct pad energy, boot wording, mechanical labels and manifest enforcement; the current decision-source hash is recorded.

### 13. What remains unverified

Software/CAD gates, simulation/inference and physical/firmware qualifications
must be stated separately. No R10 firmware, USB-only operation with the module leads connected, SD latency/power-loss, selected
e-match lot/charge 20 ms firing, actual watchdog/current tail, sensing/launch/
ground refusal, electrical/thermal/transient/endurance, installed RF/ESD,
harness/switch/retention/coating, screwdriver/card access, bore/sled/shroud/stack,
modal/flight or first-article/process qualification exists. GUI launch was
rejected; native API/CLI/renders were used without bypass. The opening record and final JSON bind review/gate receipts to the same committed
PCB. No CAD change may silently inherit the clean pair.


## Historical round10 deviations for owner acceptance

**Current board only:** `b337fe63c258c85ba4120e75ad018afa0c22241f8bc21a4172787cf2887208d9`,
46 × 90 mm, 2,366,509 bytes, reviewed at `619db7e`. This replaces the obsolete skeleton; J124, its ARM-link fuse,
J123 / pull-pin, the former separate PYRO1_BUS and their old coordinates are not current hardware.
The clean review pair is complete. **Owner acceptance of this list and OQ-3 is pending; nothing is ordered.**
R9 remains the accepted board. Passing CAD gates and simulations do not qualify firmware or physical hardware.

The board-bound `round10_deviations.json ` under `m3_design/assembly_review/sources/r10_review/` maps all 229
historical review rows to their current or closed dispositions and indexes every agent decision. Measurements below
come from the round-10 native reviews, the unchanged round-9 geometry and the named primary sources. A calculated
limit or CAD clearance is not a physical measurement. Every retained drawing-hygiene instance has its measured
reason in `tools/route_check.py`; the round-10 routing record preserves the current instance list.

### 1. Single-switch arming, surface faults and the protected barrel envelope

The external screw switch on J400 is the sole power / pad-arming device, on last and off first, reachable on the
rail. Treat the pyro channel as live whenever the board is powered. PC1 enables Q120 / Q121 through Q122; PE4 separately
controls Q124. Both default off in reset / unpowered, but they share one MCU and software. There is no physical
pyro break while powered, no switch-state sensor, and no ARM-link fuse. USB / self-powered port back-feed can hide a
switch opening and retain logic, ACT_EN and RAW_ACT. Connect an e-match only with no such back-feed source attached;
bench work uses USB with the pack or e-match disconnected and dummy loads. R3-SAF-02 remains an installed test.

Pyro-specific surface spacing is deliberately absent (board default 0.15 mm). The retained single-fault cases
(R4-SAF-03, R6-SAF-04) are concrete, not a claim that CAD is fault-tolerant:

| Current geometry | Measured gap | Residual and disposition |
|---|---:|---|
| Q124 own gate–drain pads / external gate track–drain | 0.5200 / 0.6200 mm | A live-to-gate bridge can fire an enabled igniter; inspect, coat and qualify dummy-load startup / reset waveforms |
| R128.1 / R126.1 to 3V3 via (19.05,55.9), F.Cu | 0.6761 / 0.8352 mm | A bridge can raise the gate; ground cold-screen / coating do not prevent a later defect |
| U1.3 to NC sentinels U1.2 / U1.4; QSPI_IO2 track; U1.1 pad | 0.2000; 0.5500; 0.7000 mm | Pin contamination / internal fault remains possible; no independent software safety follows from two GPIOs |
| OUT B.Cu track near GND via (10,55.6) | 0.2370 mm | OUT–GND can fire an enabled igniter; a passive short screen only detects a pre-existing static fault |
| IGN / RAW_ACT to GND pour | 0.2505 / 0.2505 mm | Default-gap surface defects remain; inspection and coating required |
| Q121 source–drain pads / source bridge–drain pad | 0.5200 / 0.5700 mm | A hard bridge bypasses deliberate load-switch enabling; software cannot clear it |
| ACT_GATE vias (16.2,72.3) / (11.8,69) to In2 RAW_PROTECTED | 0.2505 / 0.8055 mm | Outside S-8's protected set; positive bridge biases the P-FET pair toward off, not proven immunity to all faults |

S-8 remains blocking: four current pyro barrels have nearest foreign inner-copper gaps **1.4583, 1.9000, 2.4788
and 2.1061 mm**, all ≥1.0 mm. Round-10 hardening checks graphical / textual copper too. Inner OUT–GND shorts can
still fire; GND-only proximity is not universal failsafe behavior. The old separate RAW–BUS via-gap item is retired.

Ground checks must run with both controls low **before** PC1 enable. After prior enabling, wait ≥1 s and verify
bus discharge; then enable PC1 with PE4 low for ≥100 ms before powered-bus checks. Independent passive calculations
at ±1.45% resistors give healthy 1 Ω CONT 65.582–87.644 mV and bus 65.547–87.597 mV; open CONT 129.162–168.020 mV.
These exclude leakage / ADC / temperature effects; thresholds are unqualified. A shorted match resembles a healthy
one. The three pyro dividers retain two series 5.1 kΩ top resistors, two parallel 2 kΩ bottom resistors and 4.7 kΩ
ADC series parts: worst one-resistor-fault pin voltage 1.4108 V at 8.4 V or 3.3422 V at 19.9 V (Calc).
Firmware ground refusals, accelerometer + barometer launch detection and in-flight sense-never-veto remain mandatory
and unimplemented. AGENTS §2 is unchanged.

### 2. External servo power, return sharing and fire-source reserve

O3 removes board servo power switching and fault containment: J122's + row is NC; the harness powers every servo
and returns its current to the pack star. There is no board means to remove servo power or prove neutral motion
on reset. Firmware must issue neutral first and within the adopted 50 ms command budget; physical response is a
chosen-servo / harness test. A jam can remain after a neutral command.

O6's board-current bound is **0.6144 A** (Inference), conditional on ≤1 mΩ pack-star transfer resistance and
≥50 mΩ in each signal-reference branch. Four-wire the actual star / branches before flight; ground pins remain
connected references. Per-servo inline protection is a harness choice; OQ-6 leaves pack-to-U9 / Q120 hard shorts
unfused. Strain relief, no chafe points, and crimped or soldered leads are retained mitigations, not current limiting.

GAP-1 superposes **11.545807 W** normal converter load and servo current through the common source. At the stated
7.4 V equivalent source / 0.15 Ω and hot loop bounds, fire current is **1.550071 A idle**, **1.485263 A with one
persistent stall**, **1.420229 A with two**. Only idle meets the 1.5 A criterion. Qualify actual e-match all-fire,
source reserve at deployment, contacts, hot FETs and harness; do not infer that a 7.4 V launch reading guarantees
7.4 V available at recovery. The isolated Blue Jay has no shared copper.

### 3. Camera, external GPS / radio and UART harnesses

| Item / prior finding | Current reason | Required closure |
|---|---|---|
| Camera, R3-REQ-08 | Conditional minimum 5.031682 V at 1 A uses total loop ≤150 mΩ, 135 mΩ switch and 50 mV transient allowance | Four-wire installed board / harness / contacts and scope startup / load steps; keep the 1 A allocation |
| Radio, R3-REQ-09 | LR900-F maker 4.5–5 V / 1 W average / 27 dBm; switch minimum 0.347690 A, peak demand unspecified | Measure full-power TX peak and delivered voltage; installed immunity with dummy loads |
| Radio band / O2 | Maker 890–915 MHz; channels 12–25 correspond to 902–915 MHz; restricted FHSS set undocumented | Verify chosen channel / hop configuration with maker; no regulatory or RF qualification claimed |
| GPS, O1 / R8-MCU-02 | M100 Mini is L1 only (L5 lost), maker 500 m / s / 4 g tracking limits; UART 3.3 V is an Inference, not a maker guarantee | Measure levels and unpowered behavior; qualify SH1.0-to-GH1.25 adapter; GPS is not the flight estimator |
| Port sequence, R4-MCU-01 / R8-MCU-01 | OE-low isolation retained; AUD-8 main-3V3 B sides can feed an unpowered module a few mA through 1 kΩ if OE is wrong | OE low with power off; RX pull-ups and idle-high TX before OE; bounded DMA / framing-error handling and unplug test |
| Cable order, R4-REQ-06 | J9 3=RXI / 4=TXO; J410 / J420 3=TXO / 4=RXI, despite identical GH4 bodies | Per-port end-to-end power / polarity / UART check; current complete correct tables stay blocking |
| J400, R3-REQ-12 | Tin GH contacts in a 6–7 µA dry loop; external screw switch not physically qualified | Vibration / intermittency logging of VLOGIC and 3V3 with mated strain relief |
| ESD, R3-MCU-05 | Exact ESD103 UART identity retained; part naming does not qualify real edges / ESD | Scope selected baud and perform installed cable / ESD tests; no new voltage rating inferred |

O1–O6 move the modules / servo supply off board; they do not remove installed volume, antenna separation, retention,
back-feed or fault obligations. The camera retains U12 / U13; its higher port rail is not placed directly on TXU0202.

### 4. Power routing, thermal, hold-up and transient qualification

| Item / prior finding | Current measurement / calculation and reason retained | Required closure |
|---|---|---|
| U9 / U400 necks, R4-PWR-01 / -02 | U9 entries 0.3 ×1.8 mm, 0.6 mm outside pads; 0.4 mm four-via ladder / U400 feeds; C88 0.7 mm necks total 2.92 mm | Full track / via DC and temperature tests; IPC fit does not bound short-neck absolute temperature |
| Inner power cut | Conservative 1.20 mm PORT_5V3 basis; IPC fit 3.416 / 8.502 °C rise at 1.25 / 2.02 A; 1 mm outer basis 7.412 / 19.238 °C at 1.8 / 2.9 A | Actual copper / plating, pad heating and converter self-heating remain unmeasured |
| Port bypass / feed, R3-PWR-07 | U402–C430 4.309655 mm, U420–C420 4.878332 mm, U410–C410 0.456207 mm; U402 one 0.5 / 0.3 mm via (35.45,40.05), 0.4 ×0.85 mm entry | Retain explicit nonideal bypass / single-via layout; verify load transients; no fresh proof that a second via is impossible |
| U401 / GAP-3 | 0.406177 W normal; inferred 80–110 °C / W gives 102.494–114.679 °C at 70 °C, 117.494–129.679 °C at 85 °C | Exact two filled / capped vias do not establish thermal resistance; measure whole power knot |
| Converter limits, R5-PWR-01 / -03 / -04 | U9 OVLO recommended 1.5 V exceeded above about 12.2 V input (below absolute at assumed clamp); AP63201 loaded dropout is typical-only | Fault-state behavior / loaded 6 V pack and converter capacitor stability tests; do not present recommended-range exceedance as normal compliance |
| IO / gate capacitors | C92 effective 2.211 µF estimate exceeds 1.5 µF; C120 now 1 µF25 V X7R, earlier 16 V issue closed | Typical bias / aging / temperature allowances and C21397 converter effective-capacitance bounds still qualify physically |
| C84 / F6 / OQ-5 | Supplier endpoint basis 300.8 µF /37.5 mΩ; off / shed hold-up 8.6758–13.5560 ms versus max-normal ports-on 0.55375–0.86524 ms | Cold ESR / capacitance, PA6 threshold, detection / command latency, actual current decay and retained state; no hardware cutoff, TPS2553 turn-off up to 3 ms |
| USB attach, R6-PWR-02 / R7-PWR-02 | (Round 10 record; the current figure is 516.1 µF, 2.426 mC, 5.35–6.98 ms, §4.) Nominal 514.1 µF behind limiter,2.416 mC to 4.7 V; current 347.7–453.0 mA, ideal no-load 5.33–6.95 ms | Host-dependent attach / startup and current-limited hub tests; no USB compliance claim |
| OQ-2 actual-feed model | 2304 required cases / refinement pass; four fresh extrema and independent MNA control agree; minimum−14.497873 V, falling 8.525257 V / µs main step, rising 4.523496 refined | Actual unfused harness≥0.03 Ω,0.1–2 µH and simultaneous U9 IN / OUT scope traces;0 / 0.01 Ω sensitivities fail outside domain |
| R166 endurance | Refined 504.293 W peak /2.888490 mJ in different corners; maker V10 has no microsecond pulse curve | Maker approval or repeated hot / cold insertion / resistance-drift test; small energy is not durability proof |
| GAP-2 local output paths | C82 totalOUT+GND12.568808 mm /2.315313 mm²; D9 16.691778 mm /17.419688 mm² | Old missing / local-output-hardware item closed; saved-copper loop is not measured transient protection |

### 5. Fire duration, MCU and firmware obligations

R134's calculated worst **35.797452 W**, **0.715949 J at 20 ms /1.288708 J at 36 ms**, is below the maker's approximate
log-interpolated single-pulse graph 61.2 /44.1 W. This is not repetitive-pulse or 85 °C qualification. Every normal
physical fire, **including tail**, ends by 20 ms. GAP-5's separate intact-hardware watchdog-fault guard is≤36 ms:
960 LSI cycles give 28.571–32.653 ms; allocated worst total 34.853 ms. No watchdog refresh during a fire; hot gate tail,
reset behavior, actual silicon revision, resistor drift and physical current duration must be measured.

All 100 U1 pins and all four evidence hashes match; the evidence note regenerates identically. This is **not R10
firmware**. Existing v0.8.1 / diagnostics remain R1-bound and fail before compilation / artifact creation on this tree.
The required new implementation still includes the launch / ground / in-flight safety policy, two GPIO locks and
LCKK / pin-bit readbacks (PC1 / GPIOC and PE4 / GPIOE), neutral-first reset recovery, PA6 shedding, EXTI shared-vector demux,
per-pin ADC mapping, UART sequence / errors, IMU axes / timing, QSPI QE / clock / logs and watchdog supervision.

- PA4 / PA5 / PA6 / PE11 / PE12 retain exact AN2606 loader allowances and containment; PE11 has R431 pull-down,
  PA6 loader sink≤0.363 mA. UART5 / USART6 are outside the cited H74x ROM UART interfaces. Loader transitions remain tests.
- R5-MCU-04 / -05: ordinary PA6 / PB1 diagnostic dividers retain single-fault pin-damage cases; PA6 ADC-mode stress ceiling is 4 V (digital FT ceiling at powered 3.3 V supplies is 6 V), correcting the old 7.3 V claim; these are not the
  protected three pyro dividers. PC8 VBUS / 2 can read low below about 4.62 V and never proves USB absence.
- H743 synchronous trace uses DBGMCU_CR bit 20 TRACECLKEN (ST CMSIS DBG_TRACECKEN). A valid dummy-load test observes
  PE2 trace clock while both locked-low control modes / locks remain valid; override behavior is unmeasured.
- R7-MCU-04: flash sector erase 400 ms exceeds the fastest 28.571 ms watchdog. Pre-erase or bounded suspend slices /
  buffering are required; program-only 85.33 kB / s ceiling versus 64 kB / s does not include blocking erase overhead.
- Sensor accuracy / clipping / high-g aliasing, updated K850DM / L1000 W trajectory, vibration and temperatures remain
  unqualified. Typical drift, modeled mass and AVA resemblance do not establish≤5° roll accuracy.

### 6. Routing cleanliness and AVA scope

All gates pass with **0 failing / 0 allowlisted / 0 leftovers**. The remaining measured categories are 35 off-centre
pad ends,1 through-pad pass,8 inside-pad segments,11 width-change junctions,6 short layer hops,2 U-turns,4 extra-bend
cases,14 power vias without GND partners and 1 via-on-track-in-fill: **82 instances**. Eight inside-pad segments are
AUD-10 review items;74 other information instances have individual measured reasons in the tool. No partial overlap,
crossing, connectivity failure or fast-return violation is waived.

| Re-raised routing group | Current reason / disposition |
|---|---|
| R9-RTE-04: noncritical returns | NRST GND partners 1.6552 /3.3534 mm, BOOT0 1.6621, I2C1_SDA1.8806; SCL1.4431. Outside named critical set; retain measured deviation and bench checks, not a claim that all alternate stitches are impossible |
| R9-RTE-05: entries / between-pad lanes | SPI1_MOSI U4.14 entry x 17.55 vs pad x 17.50; on-axis trial violated IMU_body_B and lost 11 SCK reference samples. LED1 / R33 / C86 between-pad routes remain. R9 aligned IO entries / vias and U10 VBUS; PULLPIN removed |
| R9-RTE-06: slow split crossings | SERVO2_MCU approximately 0.42 mm over 3V3 / RAW_PROTECTED split; LOGIC_SOURCE_ST near y 57.7–58.0. Retain slow routing; plane redraw requires power / return requalification |
| R9-RTE-07: buzzer / crystal neighbours | BUZZ_DRV 36.38 mm /3 vias; simple layer swaps cross VBUS_SENSE /USB_LIMITED. Foreign F.Cu projection over Y1 BUZZ_DRV 2.732695 mm /NRST 0.777648, solid In1 GND intervenes; no QSPI_IO2 crossing. Stimulate at bench |

Round-9 shortened BAT_SW_SOURCE / NRST / USB_FAULT_N by 0.692893 / 0.347651 / 0.597056 mm and centred three supply
entries. Those changes are covered by the full round 10. QSPI spread 10.413 mm, one via each, is a clock / setup / hold
bench item. The retained reference check has 110625 samples,7139 own-antipad samples,7 samples under 6 exact strays,
zero loose; region check 57 items / 21777 samples. AUD-2 excludes only the shared exact slow-net list; fast interfaces,
S-8 and critical hygiene remain blocking. AVA photographs support arrangement / simplicity only; no private netlist,
inner-plane, firmware or protection-performance claim is inferred from them.

### 7. Silkscreen and assembly identification

Current 144 shown / 81 hidden reference designators and 38 legends meet 1.0 mm text / 0.15 mm stroke; all hidden
references stay on Fab and the complete list is in M3_R10. They are hidden where legal nearest-subject placement is
unavailable. `J2 5:GND 6:NC` is nearerJ3 thanJ2: retain the identification deviation and TC2030 cable check.
TP88 footprint silk edge≈0.425 mm andJ3≈0.50 mm retain generator 0.6 mm centreline-margin exceptions; actual outline /
mask clearances still gate. Minimum 0.15 mm strokes andU4's 0.100 mm mask web sit at the stated JLC limits; inspect the
first article. All current port /servo tables are complete, correct and unique, including text boxes after hardening.
AUD-10 counts distance only; it does not waive missing / wrong legends or mask / text clearances.

### 8. Mechanics, retention and sensor placement

The current five-support / two-tie-hole outline is 46×90 mm. Fresh fit gives minimum matedGH margin 0.028 mm, J122 0.50 mm,
J1 / J121 wire room 4.95–5.55 mm (OQ-1), bottom C88 support clearance 3.844 mm and top J400 3.858 mm. Those are CAD envelopes;
real connectors,16–22AWG bends, insulation, plug retention and workmanship are unmeasured. Program viaTC2030 before
fitting the interfering (4,44.3) support. BottomL1 hangs 3.02 mm. Use nylon / insulated hardware, measured 4 mm standoffs /
plate≤1 mm as starting hardware; include actual screw / nut / washer maxima, eccentricity and both centring tolerances.
Nut-inclusive h+t must be<6.0 mm at x 4 / 42 and<5.3 mm at x 3.7 under the stated nut / screw assumptions.

The nominal 3.5 mm washer discs include non-GND copper: support(4,44.3) nearestF3V3track / via radii 3.4104 /3.2604 mm
andNRST3.4214; support(42,86) BAT_INBtrack 2.7500 mm. Cover ordinary vias and insulate the entire bottom face; mask
and unmeasured nylon hardware are not wear qualification. OQ-7 places board plus axial tolerance wholly forward of
joint+47 mm; freed length remains stack slack. Fitted sled /shroud /harness /modules need a physical fit check.

Plate f1 280.9 Hz /45.5 g uses assumed masses / stiffness, not a modal test. Qualify retention / staking / ties at the flight
load; no measured 100 g joint strength is claimed. U4 B180 at(17,45.9), roll=−gyro_Y, x lever arm−6 mm, sits under U1's
west pin row; log sensor temperatures under MCU load. Mask C11 whole: its nearest pad is 2.818449 mm from U5's body, not the pad-only 3.0275 mm. Preserve the 3 mm body-plus-pad union; next whole-coated C10 has conservative Fab / pad envelope clearance 3.333144 mm (pads alone 3.777017 mm), and other whole-coated envelopes clear at least 5.075 mm. R13 / R64 stay masked and TP122 retains its controlled exception. Do not coat or block U5's pressure port. Generated 3D envelopes
are not vendor fit certification; GH2's old WRL header refers to historical dimensions, actual mated geometry is used.

### 9. Parts, lands and manufacturing process

| Item / prior finding | Measured reason and remaining action |
|---|---|
| L400 proxy land, R4-BOM-01 | Native 1.8×2.5 mm pads at x±2.35, outer 6.50 / inner 2.90 mm versus Bourns p 1 recommended 2.0×1.8 at±2.25, outer 6.50 / inner 2.50. Supplier proxy residual 0.15 mm. Nominal contact covered; worst heel may reachx 1.30 vs land edge 1.45. Retain explicit assembly-qualification deviation or adopt maker land through a new covered CAD revision |
| TXU0202, R4-BOM-02 | U12 / U411 / U421 supplier residual≈0.147 mm, native−90° /CPL 90°. Factory preview / pin 1 and first-article inspection pending |
| C84, R4-BOM-03 /R5-BOM-02 /GAP-4 | Supplier MA sheet only, no maker land / reflow / manual profile. Native derived 3.5×1.7 mm lands at±3.25; positive pad 1 VLOGIC at(38.5,77.25), CPL 90°, residual≈0.045 mm. Maker spelling alias remains; exact part unchanged. Fit manually after BOTH reflows using a separately validated operation; confirm polarity / height / capacitance / ESR |
| U401 /GAP-3 | Only vias(27.3,13.6) / (27.9,13.6),0.5 / 0.3 mm, may enter soldered pad 11; resin-filled, copper-capped planarVIPPO quote / inspection mandatory. Ordinary via-covering rules elsewhere remain |
| U4 /R6-BOM-02 | 0.50 mm pitch,0.35 mm lands,0.025 mm mask relief gives 0.100 mm web; fabricator acceptance /first article pending |
| C29936→C15849 option, R7-BOM-01 | Approx$0.3184 / board apparent saving, X7R→X5R at C86 / C97 / C98 / C120; effective capacitance / aging / temperature and gate-slew behavior unqualified. Retain existing identities; no saving credited |
| Preview /supplier visibility, R6-BOM-01 | Fresh 82 code query matches all exact MPNs; preview of J1 / J121 / L1, U4 stock / consignment and terminal pin-number / order remarks still mandatory. CAD / supplier agreement is not factory assembly evidence |

Package:215 CPL rows / 82 BOM codes;203 supplier pad reconstructions plus 12 nonpolar placement-only rows, paste 317 F / 365 B,
current five-output manifest pass. AONR21357 maker / supplier numbered fingers and Q120 / Q121 opposed rotations agree.
R9 capacitor labels are complete with no substitutions; C120 25 V and exact same-code land resolve earlier issues.
OQ-4 selects aft-edge tab plus rail / frame; obtain JLC acceptance before ordering. VIPPO and manual C84 are process
conditions, not proof that Standard service has accepted the job. No quote has been accepted.

### 10. Cost, stock and owner items

**OQ-3 remains pending:** current bound stock 23:24:17Z /cost 23:25:10Z on 2026-10-28, independently re-queried 23:51:13Z,
gives **$84.43 vs $84.41, a$0.02 miss**,46 Extended / 36 Basic (82total). Parts$59.34 +feeder share$25.092; minimum purchases
raise parts to$61.14, about**$86.23 including feeder share before fixed fees**. R430C185349 has 17 versus 3610minimum;
U4C26633007 has 0 versus 5needed. Cost /stock /procurement correctly fail; export /orientation /paste /manifest pass.
Obtain a compliant quote or dated cost acceptance, resolveR430's actual minimum purchase and secureU4 stock or
consignment. Refresh exact-code cost / stock within 24 h of ordering. No unqualified substitution was made for two cents.

Owner answersOQ-1 / -2 / -4 / -5 / -6 / -7 andO1–O6 are implemented as amended by single-switch / AUD / GAP decisions; their
physical / process obligations above remain. OQ-3 and acceptance of this full list are the outstanding owner items.

### 11. Historical sources and current applicability

Six immutable R6 records under `m3_design/assembly_review/sources/` retain old local paths because other records pin
their full bytes: `r6-independent-routing-reference-review-20261013.json `, `r6_final_dc.json `,
`r6_aux_finish_packet.json `, `r6_final_objectives_review.json `, `r6_final_checks/audit.json ` and
`r6_final_checks/cleanup.json `. They are not R10 qualification; this continuation adds no local absolute path.
The allowed parent VEHICLE mirror still names old ARM terminals; its separate follow-up is to describeJ400 as the
sole power / arming switch and removeJ124 / link text. No other worktree was edited. Current native CAD /R10 records
supersede that stale candidate mirror. The historical reconciliation retires removed pull-pin, old output-loop,
thermal-via absence,16VC120, abbreviated-label and old plane / jog items; it never transfers their old coordinates.

### 12. Every agent decision

All 93 pre-round 10 `D-*` headings are indexed by ID / title / current applicability in `round10_deviations.json ` and remain
reviewable in `R10_DECISIONS.md`. The coverage is exhaustive, including suffixes:

| Decision family | IDs covered | Current scope |
|---|---|---|
| R1 | D-R1-01…07 | Plan / O5 / O6 and process; later owner amendments supersede voltage / arming premises |
| R2 | D-R2-01…16 | Placement / pins / hand routing / planes / fab / silk; later scoped AUD / GAP changes apply |
| R3 | D-R3-01…13 | GPSlimit / safety / returns / power / geometry / gates / records |
| R4 /R5 /R6 | D-R4-01…04;D-R5-01…04;D-R6-01…03 | Successive plane / entry / gate / record fixes; removed hardware does not survive as a current claim |
| R7 /R8 | D-R7-01…02;D-R8-01…03 | Gate hardening / routing / records, as amended |
| Owner-answer implementation | D-OA-01…09 | Fit / harness / shedding / actual-feed model / C88 topology and interrupted-pass completion |
| Single switch | D-SS-01…04 | Two MCU controls / merged post-switch bus / required references / pre-enable cold screen |
| Audit | D-AUD-01…10;D-AUD-01a;D-AUD-03a / 03b / 03c | Exact adopted reductions plus capacitor rating / orientation / same-code lands |
| Gaps | D-GAP-01…05;D-GAP-01a;D-GAP-02a / 02b | Coupled source / local OUT loops / VIPPO / manual C84 / physical fire timing |
| R9 | D-R9-01…06 | Labels / delay / coldorder / gates / localroutes / stack / cleanpaircoverage |
| R10 | D-R10-01…03 | Narrow gate hardening / corrected pin-limit record / frozen PCB and final inventory |

The owner can accept or overrule retained agent choices; this list records no inferred owner acceptance. Measured
routing, land, thermal and harness compromises stay deviations until accepted. Physics-based decisions retain the
one-channel /isolatedbackup /2Spack /K850DM–L1000 W premises; AVA photographs supply only visible design inspiration.

### 13. What remains unverified

**Software /CAD:** two byte-identical complete builds, all-severityDRC / unconnected / parity / ERCzero, metadata / silk/
fit / plate / contracts / routing / actuators / fabmanifest pass. **Simulation /Inference:** hot-plug corners, fire / pulse/
hold-up / thermal estimates and modeled mechanics have the assumptions above. **Physical /firmware:** no R10 firmware,
assembled-board tests, startup / reset / sense / trace / watchdog / current-tail / shedding timing, transient / thermal / endurance,
installed RF / ESD, real harness / switch / sled / shroud / retention, modal / flight or assembly-process qualification is claimed.
The PCB stayed byte-identical after full round 10; final changes are gate coverage, regressions and records only.
Computer Use approval review rejected Preview launch without a further reason; native geometry and generated renders were used,
with no GUI bypass. Ordering still requires acceptance, stock, cost freshness and JLC process / panel approval.
