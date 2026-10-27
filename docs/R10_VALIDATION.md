# R10 validation — round 1 implementation

## Owner decisions resolved; implementation in progress

The owner resolved R1-01, R1-02 and R1-03 in plan §8, commit `40a1d28`.
O5 supplies the camera from an adjustable buck and both external UART ports from
an approximately 4.8 V LDO, with separate current-limited switches. Exact setpoints
and module-input corners remain implementation qualification, not owner questions.
O6 routes servo positive and negative power directly to the pack; J122 GND remains
a signal reference with a calculated, explicitly bounded residual current.

Round 1 Phase B is in progress. No passing R10 implementation has been committed.

## Artifact and review status

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
`wxGetMousePosition` crash. A scratch interposer following the existing R9
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
The parent `../../docs/VEHICLE.md` has not been changed: no R10 outline is frozen,
and the parent file lies outside this session's writable roots. No parent commit
has been attempted.
