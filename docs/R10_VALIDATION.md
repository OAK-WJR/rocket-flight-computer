# R10 validation — round 1 implementation

> **2026-10-27 update.** The R10 board is built and committed; review round 3 (the first on the built board, ten
> lenses on `883d2db5…`) and its fix pass are done (board `579575bd…`, 46 × 90 mm; `docs/M3_R10.md`); `tools/check.sh`
> passes at zero. See "R10 build state", "Round 3", the review-round log and "R10 deviations for owner acceptance" at the
> end. The round-1 plan-review record below is kept as written; statements in it that no R10 implementation exists
> describe that time.

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
(Round-1 note, superseded 2026-10-27: the parent `../../docs/VEHICLE.md` board entry is now edited for 46 × 90 mm in the
parent repository and left uncommitted there for the owner.)

## R10 build state (2026-10-27, after round 3's fix pass)

**Board** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`579575bdb63469e2a5aedea95e843fb7c0640ba21c713a6a3bc95c2b785a646f`, 46 × 90 mm, built by `m3_design/r10_build.sh` from
the hash-pinned R9 inputs; two consecutive builds byte-identical. Netlist SHA-256 `a9516746…`. (The first built board,
`883d2db5…`, is the one review round 3 examined.)

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
| plate_model --profile r10 | f1 275.7 Hz pinned (≥ 209 Hz); every mass placed or refused; masses are Inference allowances |
| check_r10 (S-1 … S-9, K-contract, K-loader, K-actuators, LC-1, M-1, M-2, M-3, M-5, M-6, M-7, P-8, P-11, F9-1, T-1, K-legends, K-copper, K-inner, K-reference, K-retained) | OK; P-11 and F9-1 hold R10's recorded figures pending OQ-1 / OQ-2 |
| route_check --profile r10 (empty allowlist; arcs fail; port UART / control and ACT_* nets critical; needless-hop test) | 0 failing, 0 leftovers |
| check_actuators --profile r10 | OK |
| tools/test_r10_check.py (68 tests: 20 on the committed board, 41 synthetic, 7 on design data) | OK (KiCad python; the numpy-only plate test under the numpy python) |
| tools/test_route_check.py | 57 OK |
| Fab (`m3_design/r10_fab.sh`): jlc_orient, export, S-4 on the exported BOM / CPL, CPL rebuild, paste, manifest | OK (229 placed parts, 82 BOM lines), bound to `579575bd…` |
| JLC cost / stock (live data 2026-10-27) | **$87.01 per board vs the $84.41 target: missed** (OQ-3); 47 extended codes (≤ 52); short: R430 C185349 (17 in stock, 3,610 minimum purchase), U4 C26633007 (0, consign) |

**Rules re-derived for R10 with a recorded basis** (R10_DECISIONS): K-reference (D-R2-10, extended to the port control
nets D-R3-04 / -10); T-1 (D-R2-13); K-loader, S-8, S-9 (D-R3-10). **Held pending the owner** (D-R2-14): P-11 (OQ-1),
F9-1 (OQ-2).

### Owner questions

- **OQ-1 (P-11, wire room).** R10's west-edge 3.5 mm terminals leave 4.95 mm from their wire face to the bore wall
  (R8's method: 5.0 mm wire height, bare bore radius; 4.44–5.39 mm on the DB125's own wire openings and with P2's 0.5 mm
  wall allowance, R3-MEC-02); R8 / R9 recorded 6.25 mm (R8's measured value, used as a floor). Accept, or move J121 /
  J124 / J1 inboard (costs length or re-placement)?
- **OQ-2 (F9-1, reverse hot-plug premise).** R8's model lumps the harness at J1 with the protection parts within
  10.6 mm of J1.1 and U9 within 27.07 mm; on R10 they are 12.9–29.8 mm away (D8 12.86, C80 21.59, C96 20.93, C89 20.58,
  C95 20.55, R166 29.75, R167 25.47) and U9 32.22 mm. Re-model the hot plug with R10's feed (the board copper as added
  harness inductance), or re-place the protection cluster beside J1?
- **OQ-3 (cost).** The parts and feeder fees are $87.01 per board, $2.60 over M3's $84.41: accept, or reduce
  (e.g. basic-library substitutes for extended codes)?
- **OQ-4 (panel).** The aft-east corner can only be held by an aft-edge tab (east edge's aft third is the GH port column):
  accept rails / frame on the aft edge as well (JLC to confirm), or move a port?
- **OQ-5 (battery-break ride-through with the ports on; R3-PWR-02).** C84 sits on VLOGIC after U11; the port buck U400
  sits on RAW_PROTECTED with EN tied to VIN, and U11 does not block reverse current below its 0.2–2 A threshold, so in a
  battery-lead break C84 feeds the ports: 0.55–1.0 ms ride-through with the camera, radio and GPS on (8.9–13.9 ms with
  the ports off and the logic shed; R9's camera-on figure was 1–3 ms). Option: a 47 kΩ / 10 kΩ EN divider at U400.2
  (existing codes) stops the port buck at 5.73–6.30 V and restarts it at 6.49–6.94 V, giving ≥ 4.6 / 7.2 ms with the
  ports on (300.8 / 470 µF, with shedding), at the price of the ports dropping out in deep pack sags (e.g. four stalled
  servos at a low pack). Adopt, or accept the ports-on figure? (`parts_qualification.md`, Calc / Inference.)
- **OQ-6 (battery-lead fuse; R3-REQ-05).** F9 and the J1 note call for a 15 A fuse, sized for the 7.7 A servo feed that
  O3 removed; R10's J1 (DB125) is rated 10 A UL / 13.5 A IEC, and the board's own peak is the ≈ 4.2 A fire pulse plus
  U9's ≤ 2.9 A. Adopt a ≤ 10 A board-lead fuse (the legend constant changes in `r10_post.py`), or keep 15 A?

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

### Review-round log

| Round | Board reviewed | Critical / Major / Minor (confirmed) | Fix pass → board |
|---|---|---|---|
| 1 (plan) | none (plan, inherited R9) | 0 / 7 / 9 | owner decisions O5 / O6; R10 built (`883d2db5…`) |
| 3 (first board round) | `883d2db5…` | 0 / 7 / 49 | D-R3-01 … D-R3-13 → `579575bd…` |

## R10 deviations for owner acceptance (skeleton; completed when two consecutive rounds are clean)

Each item needs its measured reason and the board hash it was measured on; review rounds add their Minor findings.

1. **Pyro spacing rules dropped** (r10_plan §2 item 1): no rules A–H / A2, strict pad rules, battery-live 2.5 mm or
   P-3 / P-6 / P-7; pyro copper at the board default 0.15 mm (DRC). Kept: the ARM plug as a complete break (S-1, by
   copper connectivity), the feed only through the load switch (S-2), gates defined off (S-3), required-fitted parts
   (S-4), J124's RAW–BUS1 gap ≥ 1.5 mm with only GND between the pads on every layer (S-5), In1 / In2 GND only within
   ≥ 1.0 mm of every pyro barrel (S-8; measured ≥ 1.458 mm, D-R3-02), the 2 Ω limit, bench gates and inspection.
   **Accepted single-fault cases remaining (measured on `579575bd…`):** a surface defect (solder bridge, strand,
   debris) across a default gap can (a) join RAW_ACT or another live net to the armed bus or igniter on the outer layers;
   (b) join PYRO1_OUT to GND: In1 GND sits 0.25 mm from PYRO1_OUT's barrels and the outer GND pour at the default
   clearance, so such a defect fires an armed igniter, as a shorted Q124 would (the plug-out continuity self-test, H-1,
   and the ORDERING bench gates screen a static short); (c) join the gate to a live net on the surface (R128.1's
   neighbours). Inner-layer shorts from pyro barrels now meet GND only (safe direction for the gate and bus; OUT-to-GND
   is case (b)). JLC's electrical test screens manufactured shorts.
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
7. **P-11 / F9-1** at R10's recorded figures (OQ-1, OQ-2) until the owner decides.
8. **T-1 re-derived** (D-R2-13): tabs on the aft edge needed (OQ-4; ORDERING §8).
9. **Cost** $87.01 per board against $84.41 (OQ-3); R430's stock / minimum purchase.
10. **Silkscreen:** 93 designators hidden (kept on Fab); J410 / J420 without pin tables (no legal spot within 6 mm; their
    pins follow J9's convention, D-R3-11); `J2 5:GND 6:NC` beside J2 but nearer J3.
11. **Agent decisions** D-R1-01 … D-R1-07, D-R2-01 … D-R2-16 and D-R3-01 … D-R3-13 (R10_DECISIONS.md), each to be
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
