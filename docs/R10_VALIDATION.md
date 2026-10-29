# R10 validation and adversarial review

> **Current completion, 2026-10-28:** full rounds 9 and 10 are clean: **0 Critical / 0 Major / 21 Minor** on
> `877d0199…`, then **0 / 0 / 8** (four new / four carried) on committed`b337fe63…` /`619db7e`. The round-9 fix
> pass was committed after two identical builds and gate0. Round10 covers every changed CAD byte; final fixes
> affect gates/records only. The completed current-board deviation list below awaits owner acceptance, including
> OQ-3 **$84.43 vs $84.41**. Procurement/process/physical/firmware qualifications remain open; nothing ordered.

> **2026-10-28 hand-off check: round 9 stopped for owner decisions.** Starting worktree clean at `04d0b04`,
> board `407d1d84…`. Three fresh read-only reviewers started in parallel (requirements, safety, power); the
> owner-decision boundary below stopped the review before the other seven lenses. This is not a completed round
> or a clean pass. The consecutive-clean count remains zero. No implementation fix pass or rebuild was performed.

> **2026-10-27 update.** The R10 board is built and committed; review rounds 3 (on `883d2db5…`), 4 (on `579575bd…`),
> 5 (on `af18ac49…`) and 6 (on `3b6e15f3…`) and their fix passes are done (board `b242ab8e…`, 46 × 90 mm;
> `docs/M3_R10.md`); round 7 on `b242ab8e…` was clean (0 Critical, 0 Major), round 8 on the same board was not
> (3 Major, all records / gate tests, fixed; board now `407d1d84…`); `tools/check.sh` passes at zero. See "R10 build
> state", "Round 3" … "Round 8", the review-round log and "R10
> deviations for owner acceptance" at the end. The round-1 plan-review record below is kept as written; statements in it that no R10 implementation
> exists describe that time.

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
| R7-MFG-03 | Minor | J3 hand-finish neighbours on R10 unrecorded | **Fixed**: C83 / R8, 1.95 / 2.15 mm copper gap |
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

## R10 deviations for owner acceptance

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
| USB attach, R6-PWR-02 / R7-PWR-02 | Nominal 514.1 µF behind limiter,2.416 mC to 4.7 V; current 347.7–453.0 mA, ideal no-load 5.33–6.95 ms | Host-dependent attach / startup and current-limited hub tests; no USB compliance claim |
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
