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

## D-R2-05. U9 cell moved; In2 split into four rails

**Decision.** U9's cell (eFuse, OVLO divider, ILIM, dV/dt, bleed, bypass) moves to the free forward-east bottom
(U9 at (39.0, 79.6), rotation 0: control pins west toward the MCU, analog pins east); BAT_IN reaches it on one 1 mm
B.Cu run from Q120's drain row, west of J122's tie hole and under J122's GND row. In2 has four regions: RAW_PROTECTED
(forward area, east strip x > 40, aft band to the buck input), PORT_5V3 (column x 33.4-39.7 plus the buck-output strip
and the LDO-input finger), PORT_4V8 (x 28.3-33.1, y 9.1-29: the LDO output and both port switches), 3V3 (the rest, with
a forward finger for the 3V3 buck output). Every rail pad reaches its plane by its own via; no long rail tracks.

**Basis.** Routability and simplicity (owner priority); measured: core + USB + pyro + power families 0 DRC violations.

## Handover state (2026-10-27, after the power family)

Done: schematic; legal placement (46 x 90 mm); routing families core, usb, pyro, power (0 DRC violations, 288
unconnected: GND 158, 3V3 19, RAW_PROTECTED 5, battery control / switch / damper, and the non-critical signals);
the R10 gate (`tools/check_r10.py`, route_check profile r10, check.sh) by a parallel agent, 44 tests passing.
Next: (1) power leftovers (RAW_PROTECTED vias at U11.2 / C97 / C82 / D9 / TP81, BAT_DAMP to R166, BAT_ENABLE /
BAT_SW to J400 / R80 / R165 / C87 / TP84 / R81, 3V3 plane vias for the remaining 3V3 pads); (2) ground family (F.Cu /
B.Cu GND pours, stitching, a GND via for every GND pad the pours miss); (3) non-critical signals (Freerouting allowed,
D-R2-04, frozen into a table): port UART / EN / FAULT / OE, servo PWM, LEDs, buzzer, pull-pin, camera UART, sense
lines; move the radio UART to UART5 PB12 / PB13 first (DS12110 AF check); (4) silkscreen; (5) `m3_design/r10_build.sh`,
fab script; (6) docs; (7) review rounds. Gate findings to settle: P-11 wire room (4.95 vs R8's 6.25 mm), F9-1's
10.6 mm hot-plug premise with the split J1, legend wording. Since ff1ca18 check.sh targets R10 while the committed
board is R9, so WIP commits do not pass the gate.

## Handover update (2026-10-27, ground family started)

`m3_design/r10_route_ground.py` (F.Cu / B.Cu GND pours, THT thermals; SMD GND pads get the DRU's small-pad relief) draws
the frozen plane-via table `m3_design/r10_fanout.tsv`, made by the design aid `m3_design/r10_fanout_aid.py` on the
routed board (run it after the core, usb, pyro and power families, on a filled copy). State with families core, usb,
pyro, power, ground: 111 unconnected (the non-critical signals plus 19 rail pads the aid found no spot for: R62.1,
U12.3, U421.3 on 3V3; C82.1, U11.2 on RAW_PROTECTED; C11.2, C98.2, D421.2, D9.2, Q122.2, R178.2, R420.2, R5.2,
U1.10 / 49 / 74, U10.2, U11.6, U9.8 on GND, some of which the pours may reach) and 3 violations (a 3V3 fan-out via
0.10 mm from a GND fan-out stub, C98.2 starved thermal, one GND stub not centred on a via). Fix those by hand in the
power / ground tables, then route the non-critical signals.

## D-R2-06. Rail fan-out finished; radio UART on UART5 (PB12 / PB13)

**Decision (rails).** In2 is re-cut so every rail pad's via lands in its own plane: a 3V3 strip x 32.7-34.9 (y 9.1-42.8)
under the three port buffers and pull-ups, PORT_5V3 narrowed to x 35.2-39.7 and ending at y 42.5 below the camera
switch, PORT_4V8 narrowed to x 28.3-32.4, and the area x 33.4-39.7 forward of y 42.8 joined to 3V3 (C90). The fan-out
aid (`m3_design/r10_fanout_aid.py`) now accepts a via only inside its net's plane region (>= 0.35 mm from the region
edge; GND on In1), never overlapping other copper of its own net (no off-centre joins), and stops reporting a pad whose
island got a via earlier in the same run. Pads it cannot serve are joined by hand in `r10_route_power.joins()`: R62.1
to C14.1 (3V3), C82.1 east to a RAW via, U1.74 south between pin 75's and pin 73's vias to a via shared with C17.2
(TP82 forbids a via north of it), U9.8 and C88.2 to their own GND vias (C88.2's sits in R166's GND pad, >= 1 mm from
TP89), C98.2 straight to U11.6, U11.2 and C97.1 (stacked) to one shared RAW via; the buck output caps C8 / C9 join
L1.2. Each port buffer's 3V3 pin joins its decoupling capacitor on F.Cu. No placement row changed.

**Result (measured).** Families core, usb, pyro, power, ground: 0 DRC violations, 0 dangling vias; every unconnected
item is a non-critical signal net (96 items in 52 nets). The 15 pads the aid still reports (C11.2, C98.2, D421.2,
Q122.2, R178.2, R420.2, R5.2, R8.2, U1.10, U1.49, U10.2, U11.12, U11.4, U11.6, U401.4) are GND pads joined by the outer
pours' thermals or by the hand joins.

**Decision (radio UART).** The radio UART moves from UART4 on PD0 / PD1 (U1 pins 81 / 82, west edge) to UART5 on
PB12 (RX, pin 51) / PB13 (TX, pin 52) on U1's north edge, next to the radio port cell. Verified in ST DS12110 Rev 10
(March 2023, https://www.st.com/resource/en/datasheet/stm32h743vi.pdf): Table 11 "Port B alternate functions
(continued)", p. 90, PB12 AF14 = UART5_RX and PB13 AF14 = UART5_TX; Table 9 pp. 73-75, LQFP100 pins 51 (PB12) and 52
(PB13), both FT_u (footnote 9: VDD33USB supplies the pad only in USB configuration). ST AN2606 Rev 64 Table 119
(pp. 277-280, STM32H74xxx/75xxx system-memory boot) uses neither UART5 nor PB12 / PB13, so the radio port stays off the
ROM-loader interfaces. PD0 / PD1 return to NC. Changed: `pin_table.tsv` rows 51 / 52 / 81 / 82, `circuit.json`
(mcu_changes, telemetry note), the schematic note in `r10_sch.py`, the binding note's pin entries and firmware
obligation (`r10_sch_check.py --binding-note`), `tools/check_r10.py`'s MCU map and the seeded "radio USB injection
bypass" fault (now on U1.51). `r10_sch_check.py`: ok, 0 ERC, all nine seeded faults caught. The previous record cited
DS12110 Rev 11 Table 10 p. 92 for PD0 / PD1; the Rev 10 copy checked here numbers the Port B table 11 (p. 90).

## D-R2-07. Signal routing: pin re-map, re-placements, hand-routed escapes and a frozen router table

**Pins (plain GPIO, each in DS12110 Rev 10 Table 9; none an AN2606 Rev 64 Table 119 loader pin).** Chosen so each
port's control nets leave U1 on the side of their cell without crossing the UART lanes: GPS_UART_OE PE9 -> PD15
(U1.62, between the GPS lanes and GPS_PWR_EN), CAM_UART_OE PA7 -> PE9 (U1.39, with the camera pins, north of the pyro
sense escapes), RADIO_UART_OE PD8 -> PE15 (U1.45), RADIO_PWR_EN PD9 -> PD8 (U1.55), RADIO_FAULT_N PE15 -> PD9 (U1.56,
EXTI9), CAM_PWR_EN / CAM_FAULT_N swapped onto PE11 / PE12 (U1.41 / U1.42, EXTI12), BUZZ_DRV / PULLPIN swapped onto
PC14 / PC13 (U1.8 / U1.7; both VBAT-domain pins, 2 MHz limit, DS12110 Table 63 note 2, pp. 142-143). pin_table,
circuit.json, the binding note, check_r10's MCU map and port-power tuples and the test follow; r10_sch_check ok.

**Placement (r10_place.tsv, basis cites this record).** R150-R153 turned 180 deg (MCU pad toward the clamp, OUT pad
toward J122); D121 turned 90 deg and the pull-downs R154-R157 regrouped round it (servo cell); R422 (RADIO_FAULT_N
pull-up) moved into the radio-control strip north of U1 and R432 (CAM_FAULT_N pull-up) to the top of U1's east pin row,
both off the east escape channel. 0 placement violations (ptool).

**Copper.** `r10_route_signals.py` (family `signals`, before `ground` so the fan-out aid sees it): the critical port
UARTs and IO rails by hand (unchanged from the previous commit), and by hand also the GPS / radio connector-side wires
(RX on a short B.Cu hop: the buffer orders RX above TX, the connector TX above RX), the camera control escapes (RX and
TX each on one B.Cu hop east of USB_LIMITED), GPS_UART_OE, the servo cell's bottom copper (inner lanes down the channel
between D121's pin columns) and six GND joins the signal copper boxes in. RADIO_4V8 crosses the radio cell on In2
(one 0.4 mm In2 run between two vias) so B.Cu under the cell stays free. The other non-critical nets come from the
design aid `m3_design/r10_aid/ncroute.py` (octilinear A*, negotiated congestion, kernel `astar.c`), frozen into the
module's AUTO table and hand-cleaned (CAM_RX_WIRE, BUZZ_G, BUZZ_OUT, PULLPIN, the IO bleed runs, RADIO_PWR_EN).
Freerouting 2.4.1 was tried first on a DSN with the critical copper fixed; on this board two runs ended with 9 and 11 connections
unrouted and 1162 / 624 reported violations (its 0.2 mm rule against the fixed copper), and its output would have needed a full redraw to
meet M2, so the octilinear aid was used for the same non-critical scope (D-R2-04). The fan-out aid's clearance is now
0.17 mm and its search reaches 3 mm.

**Result (measured, families core usb pyro power signals ground, board SHA-256 6ea9d8be...):** DRC 0 violations, 13
unconnected items in 7 nets, all open by design of this pass (below); route_check r10: 15 failing, of which 10 are the
four dangling servo entry vias and their stubs (open lanes), 1 C93's 0.68 mm GND stub into the bottom pour (needed for
DRC's two-spoke rule, judged dead copper by route_check), and 4 unrecorded non-critical leftovers (BUZZ_OUT detour,
CAM_5V_SENSE detour and 4 vias, NRST 5 vias inherited from the usb family).

**Open.** SERVO1-4_MCU (U1.22-25 to the four servo-cell entry vias at (19.3, 65.05), (22.7, 66.5), (23.3, 67.2),
(28.3, 65.6)), VLOGIC_SENSE, LOGIC_SOURCE_ST and BAT_FAULT_N. They share the area south of U1, where the F.Cu escapes
are fenced by TP85's 1 mm bare-pad clearance, D9, the ARM1 / RAW_ACT sense diagonals and their vias, and B.Cu by the
two sense resistor chains, R91, R61 / C60 and USB_LIMITED; BAT_FAULT_N (U1 SE corner -> TP85 -> R89 -> U9) crosses the
servo lanes topologically. The router leaves 132 conflict cells there at any iteration count. Candidate fixes (owner
or next pass): move TP85 off the servo lanes' path (it may sit anywhere on BAT_FAULT_N), turn D9 so its pads leave a
3-lane gap, and move R91 off the corridor east of the ARM1 vias.

## Handover update (2026-10-27, signals family)

State: schematic and pin map per D-R2-06 / D-R2-07; families core, usb, pyro, power, signals, ground; DRC 0
violations, 13 unconnected in 7 nets (D-R2-07 "Open"). Build: `r10_sch.py`, `r10_pcb.py`, then `r10_route.py` for
core, usb, pyro, power, signals; run `m3_design/r10_fanout_aid.py` on that board to refresh `r10_fanout.tsv`; then
`r10_route.py ground`; fill zones. Two builds are byte-identical. Next: route the seven open nets (placement relief
first), clear route_check's leftovers (BUZZ_OUT, CAM_5V_SENSE, NRST), then silkscreen, build / fab scripts, docs and
review rounds as in the earlier handover list.

## D-R2-08. Owner: hand-route every signal (2026-10-27)

**Owner decision.** Asked which gives the better-organized, AVA-like board, the owner chose hand-routing for all
remaining and all non-critical signals too. The design-aid router's frozen output (`r10_route_signals.py` AUTO table,
`m3_design/r10_aid/ncroute.py`) is to be replaced by deliberate hand-drawn tables; it may serve only as a sketch of
feasible paths. First relieve the placement south of U1 (TP85, D9, R91, the sense-resistor chains and their diagonal
runs) so the servo, sense and status lines can run as straight, grouped lanes, AVA-style.

## D-R2-09. Placement relieved south and east of U1; three status pins re-mapped

**Why.** D-R2-07's open nets were boxed in by one topology, not by lack of space: the ARM1 / RAW_ACT sense runs
(chains south-west of U1, MCU pins U1.33 / U1.34 on its east edge) had to cross the servo bundle and the status lines
from U1.28 / U1.29, and USB_LIMITED's bottom run at x 32.3 walls U1's east pins off on B.Cu from the U11 / U9 cells.
U1.33 / U1.34 and the U1.32 sentinel stay (check_actuators pins them: sense resistors at the MCU end and the pyro
guard pin), so the fix is: sense lanes outside, status lines inside crossing under them on B.Cu east of the wall.

**Pins (plain GPIO / ADC, DS12110 Rev 10 Table 9 p. 69, LQFP100; none an AN2606 Rev 64 Table 119 loader pin).**
LOGIC_SOURCE_ST PA5 -> PA4 (U1.28, EXTI4), BAT_FAULT_N PA4 -> PA5 (U1.29, EXTI5), VLOGIC_SENSE PC2_C (U1.17) -> PA6
(U1.30, FT_a, ADC12_INP3; the F6 ADC watchdog input moves with it); U1.17 is NC. pin_table, circuit.json, the
schematic note, the binding note's firmware obligations and check_r10's MCU map follow (the map now also carries
D-R2-07's camera / buzzer / pull-pin moves, which it had missed). r10_sch_check: ok, 0 ERC, nine seeded faults caught.

**Placement (r10_place.tsv rows citing this record; ptool: 0 placement violations).**
- D9 (RAW_PROTECTED clamp) (23, 65) -> (41, 61) rot 180, beside C82 on the east, as R9 had it; its F.Cu band south of
  U1 becomes the servo bundle's path. R122's RAW_PROTECTED end now takes its own In2 via (19.6, 66.0).
- TP85 (BAT_FAULT_N) (25, 57.5) -> (37, 65.5), on BAT_FAULT_N's F.Cu column east of C82; R89 (its pull-up) B (28.3,
  66.6) -> F (37.825, 55.0) on the same column. TP87 (LOGIC_SOURCE_ST) F (39, 62.8) -> B (34.6, 56.6) and R91 (its
  pull-up) (28, 56.4) -> (33.8, 54.025) rot -90, both stubs off LOGIC_SOURCE_ST's straight B.Cu run to U11.9.
- R170 / R172 (sense series 4.7k) turned horizontal at (32.56, 46.2) / (32.56, 45.25) beside U1.33 / U1.34 (P-8:
  1.9 / 1.7 mm of *_MCU track), leaving U1.28-30's escapes and vias between them and the sense lanes.
- VLOGIC divider R61 / C60 / R60 from x 29-33 (it straddled USB_LIMITED: VLOGIC_SENSE was unroutable) to a column at
  x 38.7 on B.Cu with R60's VLOGIC pad on the spine (spine extended to R60.1).
- R157 turned (GND pad east) so SERVO4 enters it straight; R105 turned and C94 / TP74 moved so the camera-5V divider
  is one straight column R104 -> R105 -> C94 at x 39.57.

**Copper.** SERVO1-4_MCU: one F.Cu bundle from U1.22-25, straight south, one staggered 45 deg turn (0.6 / 0.7 / 0.6 mm
between diagonals), straight south over the bottom sense rows to one via each, then the servo cell unchanged.
ARM1_SENSE / RAW_ACT_SENSE: one 45 deg run each from the chain vias, parallel to the servo bundle, then straight
north at x 34.4 / 35.1 into R170 / R172 (chains, their vias and GND vias unchanged). BAT_FAULT_N, LOGIC_SOURCE_ST,
VLOGIC_SENSE: straight escapes, one via each, straight B.Cu runs (two of them under C92's body, between its pads).
CAM_5V_SENSE: one F.Cu run, no via (under R102's body, between its pads). C82's RAW via moved under C82
(33.1, 66.6) off BAT_FAULT_N's column. The fan-out aid was re-run (its table stays legal: DRC 0).

**Result (measured).** Families core, usb, pyro, power, signals, ground: DRC 0 violations, 0 unconnected; check_r10
S-1..S-7, P-8 and K-contract OK; test_r10_check 44 tests OK.
