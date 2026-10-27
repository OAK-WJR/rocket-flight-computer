# R10 decisions

R10 is not built. R9 remains the accepted fallback. These records do not change the
owner's decisions in `r10_plan.md` sections 6, 7 and 8.

## D-R1-01. Review the plan before changing CAD

**Decision.** Round 1 reviews the plan and inherited implementation contracts. Do not
rename R9 as R10 or claim R9 verification as R10 evidence. Build only through new
reproducible generators after the supply contract is settled.

**Basis.** The task's Phase A/Phase B order and its instruction to stop at a requirement
that needs an owner decision. The starting commit is
`f5579f4a9c248d4aa6cf7a2add162cb813a93c63`; its board is R9,
`4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14`.

## D-R1-02. O1 needs a voltage decision

**Status: resolved by O5 in §8, commit `40a1d28`.** O1 specifies the HGLRC M100 Mini
on the existing 3V3 rail through a current limiter. The maker specifies 3.3–5 V input.
The AP63203's guaranteed feedback range is 3.27–3.33 V in CCM. Its low corner is
already below 3.3 V, before switch, PCB and cable losses. The root independently
checked the maker sources after the electrical reviewer identified the conflict.

**Options.** Supply GPS through its own current limiter from a regulated rail within
the module's range, proposed nominal 4.8 V; or retain O1 and obtain maker qualification
for the actual low-voltage corner/select a compatible module. A nominal bench success
does not establish a temperature/load guarantee. Neither option is accepted yet.

**Sources.** [HGLRC M100 Mini specification](https://www.hglrc.com/products/hglrc-m100_mini-gps),
Input; [Diodes DS41326 Rev. 3-2](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf),
p.5, electrical characteristics. See `docs/R10_VALIDATION.md` for review disposition.

## D-R1-03. Separate camera and radio voltage budgets

**Decision for implementation after D-R1-02.** Replace section 7's directly shared
nominal-5 V default with separately qualified voltage envelopes at the module inputs.
No circuit or part choice is frozen. The camera requires at least 5 V; the radio's
maker specifies 4.5–5 V. A fixed AP63205 has a 4.95–5.05 V feedback range before
downstream losses, so its candidate circuit cannot guarantee both envelopes.

**Basis.** Section 7 explicitly permits review-driven changes with a recorded basis.
O2's external radio and O4's regulated camera stay. Candidate implementation: an
adjustable camera buck with enough lower-corner headroom, and a separate approximately
4.8 V regulator for the radio. Recompute loading, heat, U9 coordination, current-limit
tolerances, startup and back-feed before approving parts.

**Sources.** [RunCam Split 4K manual](https://www.runcam.com/download/split4k/RC_Split_4k_Manual_EN.pdf),
input specification; [MicoAir LR900 manual](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry),
Specifications; Diodes DS41326 p.5;
[TI TPS2553 SLVS841F](https://www.ti.com/lit/ds/symlink/tps2553.pdf), p.7.

## D-R1-04. Review concurrency limit

**Execution limitation.** The session provides three concurrent reviewer slots besides
the root. The requested read-only `codex exec` fallback failed during app-server
initialization with `Operation not permitted`. Reviewers therefore run in parallel
batches, each as a new independent agent with a fresh context. This does not meet the
requested ten-at-once concurrency; it must not be reported as if it did.

## D-R1-05. Baseline environment

**Decision.** Keep environment fixes outside the repository. Default Python lacks
NumPy; use a temporary virtual environment for the plate model. KiCad 10.0.6 crashes
in the seeded DRC scratch project at `wxGetMousePosition`, because the headless session
has no screen. Use the existing R9 D-S6-14/D-S9-06 workaround: a temporary interposer
returns zero mouse coordinates. It does not replace DRC checks or alter CAD. Record
plain and wrapped results separately; neither is R10 qualification.

## D-R1-06. Close round 1 at the owner-decision boundary

**Decision.** Ten independent plan-review lenses have completed in batches, including
fresh restarts of interrupted reviewers. Consolidated findings are 0 Critical,
7 Major and 9 Minor; evidence and duplicate dispositions are in
`docs/R10_VALIDATION.md`. The root independently verified every accepted Major,
including in-memory assembly-omission seeds. This is not a clean board review.

**Basis.** D-R1-02 remains unanswered. The task explicitly requires stopping rather
than guessing when a requirement needs an owner decision. No R10 CAD, generator,
gate dispatch, firmware binding or fabrication package is released or committed.
Review notes remain uncommitted because no passing implementation pass exists and
the complete baseline gate did not produce a known zero exit.

**Conservative implementation defaults after the blocker is resolved.** Preserve
P2's effective fifth support; target the original $84.41 board cap with at most
52 extended codes and account for external hardware separately. Both avoid silently
relaxing requirements. Specify servo positive/negative wiring and port power-state
isolation before freezing placement. The specified C84 now has a located electrical
datasheet; its reflow qualification remains open. None of these defaults resolves
or substitutes for the O1 voltage choice.

## D-R1-07. Implement O5 and O6

**Decision.** Resume Phase B under the owner's §8 decisions. An adjustable camera
buck feeds the camera switch and a separate LDO for the GPS/radio switches. Exact
voltage/current/temperature budgets are in `parts_qualification.md`; they must pass
before the circuit is qualified. Port UART isolation must remain effective when
either endpoint is unpowered or the MCU is in reset.

**O6 harness contract.** Servo power pairs run directly to the pack. The four J122
reference leads terminate at the pack-negative star, not at motor-negative terminals.
Each reference branch has at least 50 mΩ resistance. The star transfer resistance
between power and reference taps must be at most 1 mΩ. At 7.68 A total motor current,
the conservative residual board-current bound is 4 × 7.68 mV / 50 mΩ = 0.6144 A;
use 0.62 A as the listed bound and qualify the board return for 1 A. Ignoring J1
return impedance makes this upper bound conservative. **Inference:** this describes
a specified harness, not a measured installed harness. Four-wire resistance and
loaded voltage measurements are required before flight; failure to meet either
bound invalidates this calculation.

**Placement.** The first integrated candidate is 46 × 90 mm with five supports,
MCU centred across the width, west battery/ARM/igniter terminals, east GH ports and
an end-mounted servo header. Length is provisional; routing simplicity takes
priority over shortening it. No placement or copper qualification is implied.

## D-R2-01. Placement legalised by moves, not rebuilt

**Decision.** Keep the round-1 placement's floorplan (screw terminals on the west edge, GH ports in an east column with
their circuits under them, U1 central, J122 at the forward end) and remove its 36 placement violations by moves
recorded in `m3_design/r10_place.tsv` (basis column cites this record). The MCU core block stays at R9 + (5, -1.5) so
R9's hand-routed core tables (QSPI / HSE, IMU / barometer, decoupling) apply unchanged; the terminals and the pyro /
load-switch cluster moved 1.85 mm forward for the barometer's clearance to J121's pins.

**Basis.** Owner priority: correctness, then simple, clean routing; reusing qualified R9 tables is simpler than redrawing
them. Measured with `m3_design/r10_aid/ptool.py` and DRC: 0 courtyard, outline and hole violations.

## D-R2-02. Pyro channel and USB / SWD routing redrawn from the pads

**Decision.** `m3_design/r10_route_pyro.py` replaces round 1's table: 1.0 mm F.Cu fire loop (J124.1 -> R134 -> J121.2,
J121.1 -> Q124 drain), Q124's source bar with two GND vias, continuity / ARM / RAW_ACT sense chains with a GND via within
1.5 mm of every layer change (AGENTS 3), the load switch Q120 / Q121 on B.Cu with a 0.4 mm source bridge clear of both
gates. Small passives were aligned so each chain is straight. `m3_design/r10_route_usb.py`: SWD leads end inside J2's
pads but outside its F.Cu keep-out and clear of its locating holes (as R9); NRST hops USB_FAULT_N on F.Cu; USB_LIMITED
runs on B.Cu east of U1 instead of under it. Core + USB + pyro: 0 DRC violations.

## D-R2-03. Port supply re-planned for routability

**Decision.** The 5.3 V buck (U400 / L400 / C400-C404 / feedback divider) moves to the empty aft-west top area as one
row (input west, output east); the 4.8 V LDO U401 sits on the bottom beside it, input facing the 5.3 V side and output
facing the two port switches; each port switch's EN pull-down sits on its EN side and its ILIM resistor on its ILIM
side (round 1 had them swapped); the camera switch U402 moves into the camera cell (bottom, beside J9) so CAM_5V is
local; the switches' FAULT pull-ups move toward the MCU ends of their lines.

**In2 plan (to implement in the power stage):** In1 solid GND. In2 split into RAW_PROTECTED (the forward area y > 58,
an east strip x > 40 and an aft band reaching the buck input), PORT_5V3 (a column x 33-40 from the buck output finger
to the camera switch), and 3V3 (the rest, with a forward finger x 17.5-32 for the 3V3 buck output, D120 and the servo
clamp). F.Cu / B.Cu GND pours last. Inference until the zones are filled and checked.

**Pending:** the radio UART should move from PD0 / PD1 (U1's west edge, away from its port) to UART5 on PB12 / PB13
(pins 51 / 52, north edge, free in the R9 netlist) after checking DS12110's alternate-function table; the 3V3 buck
(U2 / L1) stays forward and reaches In2 3V3 through the finger.

## D-R2-04. Hand-routing kept for critical nets (owner, 2026-10-26)

The owner chose to keep AGENTS 3's hand-routing of critical nets (power, pyro, crystal, USB, SPI / QSPI). Freerouting may
be used only for non-critical signals (LEDs, buzzer, servo PWM, port enables / faults / OE and UARTs, non-pyro sense),
its result frozen into a table and held to `tools/route_check.py`.

## Handover state (2026-10-27)

Done: schematic (r10_sch, 9 seeded faults caught), legal placement, core / USB / pyro routing families (0 DRC errors).
In progress: power family (U9 cell, BAT_IN / RAW_PROTECTED / VLOGIC / port rails, In2 zones). Not started: ports,
servo, status, camera UART routing; ground pours and stitching; silkscreen; `m3_design/r10_build.sh`; fab script;
docs (M3_R10, REQUIREMENTS F6/F8/F9/F10/P1/M2, STATUS, AGENTS rows, VEHICLE.md); review rounds 2+. The R10 gate
(`tools/check_r10.py`, route_check profile r10, check.sh) is being written in parallel. Design aids:
`m3_design/r10_aid/README.md`.
