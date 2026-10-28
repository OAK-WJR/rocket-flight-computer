# R10 validation and adversarial review

> **Current continuation, 2026-10-28:** the interrupted owner-answer pass is complete and verified. Two fresh
> full builds produced byte-identical board `b860afbe…`; the regenerated fab package and final `tools/check.sh`
> pass. The required commit is blocked: Git cannot create the worktree's `index.lock` (Operation not permitted),
> despite the session declaring the common Git directory writable. No commit was created. Requirements-audit
> cuts AUD-1…AUD-10 / GAP-1…GAP-5 are the next implementation pass, before ten fresh
> review lenses in round 9. OQ-3 cost acceptance remains pending and does not block clean review. Focused model
> checks and owner answers are not a full clean review round.

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
(Round-1 note, superseded 2026-10-27: the parent `../../docs/VEHICLE.md` board entry is now edited for 46 × 90 mm in the
parent repository and left uncommitted there for the owner.)

## R10 build state (2026-10-28, after round 8's fix pass)

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

The interrupted changes were retained and rebuilt; none were discarded. The commit remains blocked by the
environment's denial of Git's `index.lock` write; neither staging nor committing succeeded. Two fresh executions of
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

## R10 deviations for owner acceptance (skeleton; completed when two consecutive rounds are clean)

Each item needs its measured reason and the board hash it was measured on; review rounds add their Minor findings.

1. **Pyro spacing rules dropped** (r10_plan §2 item 1): no rules A–H / A2, strict pad rules, battery-live 2.5 mm or
   P-3 / P-6 / P-7; pyro copper at the board default 0.15 mm (DRC). Kept: the ARM plug as a complete break (S-1, by
   copper connectivity), the feed only through the load switch (S-2), gates defined off (S-3), required-fitted parts
   (S-4), J124's RAW–BUS1 gap ≥ 1.5 mm with only GND between the pads on every layer (S-5), In1 / In2 GND only within
   ≥ 1.0 mm of every pyro barrel (S-8; measured ≥ 1.458 mm, D-R3-02), the 2 Ω limit, bench gates and inspection.
   **Accepted single-fault cases remaining (re-measured on `b242ab8e…`, after rounds 4–6 changed CH1's In2 edges, the
   sense runs, R128.2's GND strap, C127.2's via and the R120 entries; D-R4-01, D-R4-02, D-R5-01, D-R6-01):** a surface
   defect (solder bridge, strand, debris) across a default gap can (a) join RAW_ACT or another live net to the armed bus
   or igniter on the outer layers (nearest outside J124's window: the BUS via (17.0, 63.7) 1.139 mm from Q121.8, tented;
   R5-SAF-03); (b) join PYRO1_OUT to GND: In1 GND sits 0.25 mm from PYRO1_OUT's barrels and the outer GND pour at the
   default clearance, so such a defect fires an armed igniter, as a shorted Q124 would (the plug-out continuity
   self-test, H-1, and the ORDERING bench gates screen a static short); (c) join the gate to a live net on the surface:
   R128.1's neighbours; Q124's own gate pad to its drain pad (PYRO1_GATE–PYRO1_OUT 0.52 mm inside the DFN package) and
   the gate track 0.62 mm from Q124.5 (OUT sits at bus potential when armed with Q124 off, so a bridge turns Q124 on and
   fires; R4-SAF-03, R6-SAF-04); the 3V3 via (19.05, 55.9) 0.676 mm from R128.1 (PYRO1_GATE) and 0.835 mm from R126.1
   (PYRO1_GATE_N, held only by R127's 1 kΩ: a direct bridge puts ≈ 3.2 V on the gate) on F.Cu (no other spot keeps its
   In2 3V3 connection, D-R4-02); on the MCU side U1.3 (PYRO1_GATE_N) has the no-net sentinels U1.2 / U1.4 0.2 mm away
   and QSPI_IO2 0.55–0.75 mm away. Inner layers: every PYRO1_BUS / IGN / OUT / GATE and RAW_ACT barrel meets only GND
   within 1.0 mm on In1 / In2 (S-8, pads included since round 6), so an inner short from them meets GND (safe for the
   gate and bus; OUT-to-GND is case (b)); the exceptions are the ACT_GATE vias (10.8, 71.3) and (16.2, 72.3), 0.251 mm
   from In2 RAW_PROTECTED (a bridge holds Q120 / Q121 off: fails safe, no fire; R6-SAF-03). JLC's electrical test
   screens manufactured shorts.
2. **O3, no board-level servo-power switching or failsafe:** the board can no longer cut servo power, so F6's "tab to
   neutral on reset" has no board-level means; it becomes a harness and servo matter (neutral-on-reset qualified with the
   chosen servo and harness). The firmware still outputs neutral first after any reset (binding note).
3. **O6, servo return through the harness:** each servo's − wire runs to the pack star; J122's GND row is a signal
   reference only. Bounded board share: ≤ 0.62 A (4 × 7.68 mV / 50 mΩ with ≤ 1 mΩ star transfer resistance and ≥ 50 mΩ
   per reference branch; an **Inference** from the specified harness, to be measured four-wire before flight).
4. **External GPS and radio (O1 / O2):** L5 lost (M100 Mini is L1 only); the LR900-F link is a closed protocol
   (transparent telemetry); its band is 890–915 MHz, so its channels must be set inside 902–915 MHz (setup and
   firmware; FHSS channel restriction undocumented); module supply envelopes and installed immunity to be
   bench-qualified; **port back-feed:** a self- or USB-powered module (or camera) on an enabled port back-feeds through
   the TPS2553 (not blocked below ≈ 0.7 A, indefinitely), PORT_4V8 / PORT_5V3 and (Inference) the regulators' body
   diodes into RAW_PROTECTED, which can keep the MCU and ACT_EN alive and RAW_ACT live with the power switch open:
   firmware drops every port enable on a switch opening or VLOGIC sag, and ORDERING §8 bench-tests it (R3-SAF-02); the
   uplink still has no path to arming or firing (S-6, binding note).
5. **MCU pin re-maps** (D-R2-06, D-R2-07, D-R2-09): radio on UART5 PB12 / PB13; port enables / faults / OE on freed GPIOs;
   PULLPIN / BUZZ_DRV swapped onto PC13 / PC14; LOGIC_SOURCE_ST / BAT_FAULT_N swapped onto PA4 / PA5; VLOGIC_SENSE moved
   to PA6 (F6 watchdog input). Checked against DS12110 Rev 10; **PA4 / PA5 / PA6 and PE11 / PE12 are AN2606 Table 119
   loader pins** (SPI1 / SPI4), each allowed with its electrical reason by check_r10 K-loader (PA6 ≤ 0.36 mA; PE11 held
   off by R431); firmware binding new.
6. **Parts without a maker datasheet:** C84 (MA25V470M8x10, C46550466; supplier-hosted JIERRUI datasheet only, reflow
   qualification open, conservative 300.8 µF used for hold-up); generated 3D envelopes, not vendor models, for the five
   new lands.
7. **P-11 / F9-1:** OQ-1 accepts 4.95 mm terminal wire room, physical fit pending. OQ-2 requires a passing model of R10's actual input feeds; implementation pending. The former distance-only premise is superseded by the owner's 2026-10-28 answer.
8. **T-1 re-derived** (D-R2-13): the owner selected an aft-edge tab and panel rail/frame (OQ-4, 2026-10-28; ORDERING §8); JLC acceptance remains an ordering condition.
9. **Cost** $87.01 per board against $84.41 (OQ-3); R430's stock / minimum purchase.
10. **Silkscreen and port pin order:** 94 designators hidden on `407d1d84…` (U5's since round 8: the I2C GND via took its spot) (kept on Fab); J410 / J420 without pin
    tables (no legal spot within 6 mm, D-R3-11); their UART pin order differs from J9's (J9: 3 RX_WIRE, 4 TX_WIRE;
    J410 / J420: 3 TX_WIRE, 4 RX_WIRE; R4-REQ-06): each cable is checked end to end before mating (ORDERING 8.2);
    `J2 5:GND 6:NC` beside J2 but nearer J3.
11. **Agent decisions** D-R1-01 … D-R1-07, D-R2-01 … D-R2-16, D-R3-01 … D-R3-13, D-R4-01 … D-R4-04, D-R5-01 … D-R5-04, D-R6-01 … D-R6-03, D-R7-01 / D-R7-02 and D-R8-01 … D-R8-03 (R10_DECISIONS.md), each to be
    accepted or overruled.
12. **Not verified:** DC solve (the IPC-2152 estimates of D-R3-03 are an upper-bound fit), hold-up simulation, port-supply
    corners, plate model masses, bore fit with real plugs and wires, every bench test.
13. **Round 3 Minors left open or partly fixed** (measured on `579575bd…` unless noted): see the round's table (C-9:
    camera loop ≤ 150 mΩ, LR900 TX peak vs R420, tin J400 contacts; C-10: no capacitor / Schottky at U9's OUT, port-switch
    bypass placement, one PORT_5V3 via into U402.1, U401 without thermal vias; C-11: R430 stock; C-12: routing review
    items — hops that cross named copper, BUZZ_DRV's 3-via route, SERVO2_MCU and LOGIC_SOURCE_ST over In2 splits,
    remaining off-centre pad entries and tracks between pads (LED_YEL_A through LED1, LED_RED_A through R33, BUZZ_DRV
    through C86, J3.A4B9's VBUS entry); C-14: six hash-pinned R6 records with local paths). To be completed with
    measured reasons when two consecutive rounds are clean.
14. **Round 4 and 5 Minors listed** (see their tables): R4-RTE-03 (NRST / BOOT0 not in the critical classes, NRST's
    layer changes 1.66–3.35 mm from GND vias), R4-RTE-04 (port IO / CAM_5V vias 1.73–2.80 mm from GND vias), R4-REQ-06
    (port UART pin order), R5-SAF-03 (BUS via 1.139 mm from Q121.8, tented), R5-BOM-01 (C120 16 V at ≈ 18 V clamp-event
    Vgs, fails safe), R5-BOM-02 (C84 maker name), R5-MCU-04 (PA6 / PB1 single-fault pin over-voltage), R5-RTE-04
    (0.05 mm off-axis entries: SPI1_MOSI → U4.14, PULLPIN → U1.7, IO rails → U411.7 / U421.7, VBUS → U10.1),
    R5-RTE-07 (CC1's 0.113 mm segment inside its via), R5-MFG-02 (TP88's footprint silk 0.426 mm from the east edge),
    R5-MFG-03 (silk stroke at JLC's 0.15 mm minimum), R5-DOC-03 (pre-R10 absolute paths), R6-BOM-02 (U4 mask web
    0.100 mm, JLC's limit), R6-MFG-02 (silk edge keep-in by generator constant; J3 footprint silk 0.50 mm), R6-REQ-06
    (cost evidence BOM-bound), R7-BOM-01 (C29936 → C15849 merge, OQ-3 option), R7-BOM-02 (capacitor Values without
    rating), R8-BOM-01 / -02 (envelope comments), R8-RTE-02 (F.Cu nets over Y1), R8-RTE-03 (I2C1_SDA's via 1.88 mm from
    GND), R8-MCU-01 (UART break on an unplugged port: firmware); shroud placement: OQ-7.

    **R3-DOC-11 / R5-DOC-03 inventory:** the six immutable records under `m3_design/assembly_review/sources/` are
    `r6-independent-routing-reference-review-20261013.json`, `r6_final_dc.json`, `r6_aux_finish_packet.json`,
    `r6_final_objectives_review.json`, `r6_final_checks/audit.json` and `r6_final_checks/cleanup.json`.
    They retain historical local paths because other records pin their complete bytes by SHA-256. They are not
    R10 qualification evidence; no new local path is introduced by this continuation.

    **R7-BOM-02 inventory:** incomplete capacitor Value strings occur on C6–C11 (`22uF`), C23 / C28 (`4.7uF`),
    C19 / C20 / C87 / C120 (`2.2uF`), C22 (`1uF`), C25 / C26 (`10pF`), C60 / C94 / C122 / C127 / C129 (`10nF`),
    C88 / C99 (`100nF 50V`, no dielectric): seven strings across 22 parts. Their exact Manufacturer Part / LCSC
    identity fields remain present and audited. The inherited display strings are retained; no ambiguous
    substitute is permitted by omitting a rating from Value.

    **R7-BOM-01 cost option:** C29936 → C15849 changes X7R to X5R. The replacement's effective capacitance versus
    bias/temperature has not been qualified for these locations. Retain the existing qualified identity; do not
    credit the proposed ≈ $0.31 saving until that check is complete. This replaces the expired board-freeze reason.

15. **OQ-5, no hardware port cutoff** (owner 2026-10-28): C84 and firmware shedding retained; the loaded
    battery-break estimate is 0.55–1.0 ms, not the ports-off 8.7–13.6 ms. The PA6 analog watchdog must trigger
    port OE/EN shutdown, and firmware must specify and bench-verify the threshold, detection-to-command latency,
    actual current decay and retained load. TPS2553 turn-off can take 3 ms, so no loaded-break guarantee is inferred.
16. **OQ-6, no battery-lead fuse** (revised owner answer 2026-10-28, `f202ec3`): a hard short between the pack and
    U9 / Q120 (battery lead, J1, BAT_IN copper, D8, C80 / C96 / C89 / C95) is not current-limited. Accepted harness
    mitigations: strain relief, no chafe points, crimped or soldered leads. J124's 5 A fast ARM-link fuse remains.
17. **OQ-7, axial placement** (owner 2026-10-28): the board and sled axial tolerance stay wholly forward of joint
    +47 mm; freed length stays stack slack, so shroud clocking is unnecessary for this rule. Actual fit is unverified.
