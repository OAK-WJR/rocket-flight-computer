# R10 decisions

R10 is a CAD candidate (built by `m3_design/r10_build.sh`; not owner-accepted). R9 remains the accepted board. These records do not change the
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

**Hand-drawn signal table (D-R2-08).** `r10_route_signals.py` no longer has an AUTO table: every non-critical signal
is a deliberate polyline in a named cell function (port_links, port_control, leds, buzzer, pullpin, servo_out besides
the lanes above), the old router output used only as a sketch. Changes beyond transcription: RADIO_UART_OE straight
U421.6 -> R452.1; RADIO_PWR_EN / RADIO_FAULT_N as a parallel 45 deg escape pair, each with one via; GPS_PWR_EN's via
moved north of USB_LIMITED so its bottom lane is one straight run; BUZZ_OUT one via under LS120.2 on Q123's drain
column (Q123 (20.6, 17) -> (20.85, 17), the row cites this record; removes route_check's detour); CAM_PWR_EN
unchanged. NRST (usb family): leaves J2.3 south on F.Cu and crosses USB_FAULT_N with one via instead of a J2 via and
a two-via hop (5 -> 3 vias; route_check's extra_vias gone, a u_turn is counted). C93's GND pad, boxed in on three
sides, is strapped on B.Cu to U13.2 (its regulator's GND pin) instead of a stub into the pour (route_check's
dead_copper gone, DRC's two-connection thermal rule met). The fan-out aid (`r10_fanout_aid.py`) now also rejects a
via whose ring comes within 0.06 mm of any SMD pad, its own included (check_r8.via_paste, D87); re-run, its table
stays legal and leaves 20 rail pads to the pours as before.

**Result (measured, build reproduced byte for byte, board SHA-256 9bed1410...).** DRC 0 violations, 0 unconnected,
0 dangling vias; route_check --profile r10: 0 failing, empty allowlist, 0 leftovers; check_r10 S-1..S-7, P-8 and
K-contract OK, the full gate 79 findings against 102 on D-R2-07's board (none new: the remaining ones are silkscreen,
fit / M-rules, K-reference, T-1 and pre-existing K-copper paste items outside the routed signals); test_r10_check 44
tests OK; r10_sch_check ok.

## D-R2-10. K-reference re-derived on R10's planes; via inner pads removed

**Why.** check_r10's K-reference counted every unreferenced critical sample as a failure (10,761 on D-R2-09's board),
against R9's own method (R9_DECISIONS D-S8-17), which passes a sample inside its own net's via antipad, and it took
only GND / 3V3 / 3V3A on In2 as B.Cu reference while R10's In2 carries four rail regions.

**Decision.** (1) The ground family now strips every via's unconnected inner pads (KiCad "remove unconnected layers,
keep start and end"), as R9's ground stage did (D-S8-19): the In1 / In2 planes clear a via by the 0.25 mm hole
clearance (antipad r 0.40 mm) instead of r 0.50 mm. (2) K-reference: F.Cu over In1 GND; B.Cu over any In2 rail plane
(GND, 3V3, 3V3A, PORT_5V3, PORT_4V8, RAW_PROTECTED); In1 / In2 tracks over F.Cu / B.Cu GND (critical_reference's
extended set plus the R10 port nets); an unreferenced sample passes only within 0.45 mm of a same-net via (its own
antipad) or as a recorded REF_STRAY entry (seven edge samples where the translated R9 IMU fan-out and USB_DM graze a
neighbouring via's antipad, as R9's one USB_DM entry). (3) RADIO_4V8's In2 hop is redrawn north of RADIO_RX_WIRE's
B.Cu run (it crossed under it and cut the PORT_5V3 plane there: 393 unreferenced samples), and the ESD return vias of
D411 / D421 move 0.1 mm east, off the RX runs' antipads.

**Basis.** R9 D-S8-17 / D-S8-19; R6 counted the decoupled 3V3 plane as reference. That R10's PORT_5V3, PORT_4V8 and
RAW_PROTECTED regions act as AC reference through their bypass capacitors is an **Inference** (no field solve), as for
3V3 in R6. Result (measured, build of this record): 98,844 samples, 6,344 unreferenced, all inside their own via
antipads but the 6 recorded strays.

## D-R2-11. Copper fixes for K-copper, K-retained and schematic parity

**Decision (measured on the build; DRC 0, route_check r10 0 failing).**
- Vias off pads (check_r7.vias_in_smd_pads, check_r8.via_paste): J410.1 / J420.1 feed vias 0.3 mm aft of the pads on a
  B.Cu spine moved from x 39.9 to 40.05 (one 45 deg F.Cu entry into each pad); D411.2 / D421.2 ESD return vias x 39.3
  -> 39.4; C401's second buck-input via east of the pad (14.95, 9.0) instead of inside it; the VLOGIC via 0.35 mm aft
  of C84.1 (it sat in the pad); L1.2's 3V3 via off the pad corner (31.6, 74.6); U1.74 / C17.2 into the core table's
  existing GND via (17.5, 39.3); D121's GND strap via (21.05, 71.6), off R123.2's mask on the top; the USB-C GND
  contacts A1B12 / B1A12 strapped onto the receptacle's plated shell tabs instead of fan-out vias over the tabs' paste
  (two r10_fanout.tsv rows removed, recorded in the table's header).
- TP122 (the pyro gate's bare test pad) on the bottom (check_actuators; R9 practice): one PYRO1_GATE via beside it,
  its GND partner (15.35, 52.15) 1.49 mm away and >= 1.0 mm from the bare pad (no route_check exception).
- C93 (U12.7's bypass): the U13.5 -> C93.1 run has a node at the VCCB via, so the bypass route is endpoint-linked
  (check_r7.camera_bypass: 4.1 mm by track and via, limit 5 mm across faces).
- Schematic parity: the generated sheets placed symbol instances on `/root/<sub-sheet file uuid>`, which differs from
  the root's sheet-symbol uuid for camera_power, battery_entry and camera_uart; KiCad's parity then lost U401.5 (PG,
  no-connect). r10_sch.py now uses the root's sheet-symbol uuid (`sheet_path`); netlist and board are unchanged.

## D-R2-12. Placement relief for the supports, J122's pins and the tie channel

**Why.** fit_check / M-5 / M-6 / M-3 failed on D-R2-09's board: R166 (top) 2.2 mm, C88 / TP89 (bottom) 2.1-2.6 mm
from the (42, 86) support; C32 (bottom) 3.1 mm and J2's pads 3.58 mm from (4, 44); J400 3.56 mm from (4, 86);
R150-R153 and R167 0.45-1.23 mm from J122's pins (1.5 mm); R152 / R153 / C9 inside the 4 mm tie channel.

**Decision (r10_place.tsv rows cite this record).** R166 turned north-south at (36.0, 84.0) so BAT_DAMP is one 45 deg
run from C95.2; C88 east of U9's BAT_IN bar (39.9, 81.95) with its own GND via; TP89 to the top (44.7, 81.85) through
one via; R83.2's fan-out via out from under R166.1 (35.075, 78.9); C32 north of U5.1 on the 3V3A line (8.72, 45.85),
its R9 straps and via skipped in the translated core table (r10_route_core.CoreTable) and redrawn; the west mid
support (4, 44) -> (4, 44.3) and the forward-west support (4, 86) -> (3.7, 86); R150-R153 1.15 mm aft (y 75.25) and
D121 0.6 mm aft with their lanes (corners and taps moved, no new via); R167 0.65 mm east; the east tie hole
(30.8, 79) -> (30.8, 79.5). Every support keeps >= 3.5 mm to bottom parts and >= 3.8 mm to top hardware (fit_check),
M-6 >= 1.5 mm to J122's pins, M-3's channel clear. The plate model is re-run on the moved supports (M-2).

## D-R2-13. T-1 re-derived for R10

R9 barred the aft edge from tabs because the SMA jacks overhung it (ORDERING §3); R10 has no jack, and the east edge's
aft third is the GH port column (each connector needs JLC's 2 mm, so the east edge has no legal tab there). R10's
T-1: each end third is held on both sides: the west edge has a legal tab in the aft and the forward third; on the east
side each end third has a legal east-edge tab or a legal tab on that end's short edge within its east third
(tab_windows.py's clearances unchanged). Measured: west 0.5-23.25 and 43.0-89.5; east 49.25-58.75 and 84.5-89.5;
aft edge 0.5-7.0 and 37.0-45.5. So the aft-east hold is an aft-edge tab (x 37.0-45.5), which needs a rail or frame on
the aft edge as well as the long edges: a panel request to confirm with JLC (deviation list), not a board change.

## D-R2-14. P-11 and F9-1: owner questions, R10 figures held meanwhile

Neither rule's R8 / R9 figure is a derived need on R10, and changing either is an owner decision (r10_plan handover):
- **OQ-1 (P-11).** R8 / R9's 6.25 mm wire room is R8's measured value (a non-regression floor). R10's west-edge 3.5 mm
  terminals leave 4.95 mm from their wire face to the bore wall. Accept 4.95 mm, or move the terminals inboard?
- **OQ-2 (F9-1).** R8's hot-plug model (D76) lumps the harness at J1 and modelled D8, C80, C96, the C89 / C95 / R166
  damper and R167 within 10.6 mm of J1.1 and U9 within 27.07 mm. On R10 they sit 12.9-29.8 mm away and U9 32.2 mm.
  Re-model the reverse hot plug with R10's feed, or re-place the protection cluster at J1?
Until the owner answers, check_r10 holds R10's recorded figures (no regression: WIRE_ROOM_R10, F9_R10) and reports
R8's figures in its evidence; both are on the R10 deviation list, not passed silently.

## D-R2-15. Build and fab scripts

`m3_design/r10_build.sh` rebuilds m3_design/assembly_review from the hash-pinned R9 sources (r10_sch.py's manifest,
r10_pcb.py's pinned R9 blob) through the schematic, its gate, the placement, every routing family, the ground family,
the post stage and the final fill, with a DRC / route_check gate after every family and tools/check.sh last;
`m3_design/r10_fab.sh` makes the fab package. The fan-out table stays frozen (r10_fanout_aid.py is a design aid, not a
build stage).

## D-R2-16. Silkscreen

`m3_design/r10_post.py` (R9's post stage on R10's geometry): J122's plug numbers, the connector words (ARM, IGN, BAT,
CAM, SWD, SERVO, PULL, GPS, RADIO, SWITCH), J9 / J2 pin tables, J122's row table `J122 1:S 2:NC 3:GND` and the note
`SERVO + FROM HARNESS` (O3 / O6), R8's ARM-plug and fuse notes, the terminal pin legends by pin, M3-ASSY-R10, JLC's
order mark, pin-1 dots (R9's four required; U402 has no free spot within 1 mm of its pad 1 and keeps its Fab mark), the
designators by the R4 rule and the final zone fill, with no copper, zone or pad change (asserted).

## Round 3 (first board review round on `883d2db5…`, fix pass; board `579575bd…`)

Ten independent reviewers (one lens each, fresh contexts, started together) reviewed the committed board `883d2db5…`;
findings and dispositions: `docs/R10_VALIDATION.md` "Round 3". The fix pass ran in five file-disjoint slices (power and
planes, signals, gates, silkscreen, records), each built and gated in its own clone, then merged and rebuilt here.

## D-R3-01. R410 (GPS ILIM) stays 100 kΩ; the port budget re-derived on it

R410 shares the 100 kΩ line (C14675; 120 kΩ C114607 would add an extended code). `parts.json`, `r10_parts.py` and
`parts_budget.json` now carry 100 kΩ: GPS limit 0.230–0.309 A (TI SLVS841F eq. 1 p. 15, R ± 2 %); all three ports
shorted 2.022 A, 1.1 % above the AP63201's 2 A continuous rating. The criterion that matters is the peak current limit:
peak inductor current at that load 2.38–2.40 A at 8.4 V and 2.48 A (500 kHz) / 2.507 A (470 kHz, the −6 % spread
edge) at U9's 9.97 V OVLO corner, against AP63201's 2.5 A minimum (DS41326 p. 5): the last corner (three port shorts
plus an over-range input) ends in cycle-by-cycle limit / hiccup of the port rails only, recorded as a deviation. U9 at
all port shorts 2.917 A against its 3.96 A minimum limit.

## D-R3-02. In2 is GND under the CH1 pyro column (R3-SAF-01)

`R10_GND_In2_CH1` (In2, priority over the rail planes; x 0.3–22, y ≈ 51.3–68.4, to y 69.7 west of x 16.3): every
PYRO1_BUS / IGN / OUT / GATE barrel is ≥ 1.458 mm from any non-GND In2 or In1 fill (was 0.25 mm to 3V3 and
RAW_PROTECTED), and J124's inter-pad window is GND on all four layers. A notch serves R13's 3V3 via and a tongue D120's.
R122's RAW_PROTECTED via moved to (18.9, 69.37), 1.72 mm from R134.2 (was 0.50 mm); TP120 to (18.0, 67.3) for its 1 mm
bare-pad clearance. A short from a pyro barrel to inner copper now meets GND only. This is a plane assignment at zero
area, not a pyro spacing rule (r10_plan §2 item 1 keeps the board default clearance); check_r10 S-8 and the widened S-5
hold it. In1 GND still sits 0.25 mm from PYRO1_OUT barrels (a defect there fires an armed igniter, as a shorted Q124
would): on the deviation list.

## D-R3-03. U9's power path widened (R3-PWR-01)

U9's IN and OUT bars are entered at their full 0.3 mm width; 1.0 mm runs end 0.6 mm from the bars; RAW_PROTECTED reaches
In2 through four vias at 0.7 mm pitch on y 76.725 (was two, behind a 0.25 mm / 0.4 mm path). IPC-2152 (tools/ipc2152.py,
external, no plane credit) at 1.8 / 2.9 A: 1.0 mm runs 7.4 / 19.2 °C; the 0.4 mm via links (0.7 mm long) 21.3 / 55.2 °C
as long conductors and the 0.3 mm pad entries (≈ 0.1 mm exposed) negligible (**Inference**: short-length conduction to
the pads and vias). Fire loop at 4.2 A / 20 ms (adiabatic): 1.0 mm runs 1.4 °C, ACT_FET_S 0.4 mm bridge 9.0 °C, Q124's
0.3 mm source bar 16 °C. Basis: TI SLVSFC9C §8.4.1 p. 62; AGENTS §3.

## D-R3-04. In2 regions re-cut for the port control nets (R3-RTE-01, R3-PWR-04)

RADIO_4V8 now runs on B.Cu (In2 carries no tracks). PORT_4V8 covers U410's cell (x 28.3–33.6, y ≥ 7.1) and reaches
x 32.75 at y 24.4–26.0; the PORT_5V3 band runs aft of U410 at y 4.7–6.8 (narrowest 1.49 mm: IPC-2152 internal at 1.25 /
2.02 A 2.7 / 6.7 °C), RAW_PROTECTED's aft band ends at y 4.4 east of x 24.2 (narrowest 3.09 mm); PORT_5V3 extends west
under the camera switch's enable and fault runs. Every port UART and control net's B.Cu run lies over one In2 region,
F.Cu runs keep ≥ 0.55 mm from other nets' vias (IO-rail vias at (35.5, 17.7 / 29.7), RADIO_FAULT_N x 27.45,
RADIO_PWR_EN x 27.95). PORT_5V3 column narrowest 2.395 mm (was 0.376 mm). K-reference 0 loose samples, REF_STRAY
unchanged (6).

## D-R3-05. Buck input loop (R3-PWR-05)

C401 at (17.35, 9.0) rot 0 straddles U400's VIN (pin 3) and GND (pin 4), each pad edge 1.0 mm from its pin (the GND pad
was 6.97 / 7.34 mm away). Basis: Diodes DS41326 p. 15 item 4, Fig. 25.

## D-R3-06. Crystal In2 GND restored (R3-RTE-02)

R9's D-S8-20 (owner-accepted with R9) was dropped without a record when the core block moved. Restored translated by
(5, −1.5): `R10_GND_In2_Y1` (x 18.9–26.8, y 44.3–48.95, NRST notch) and its In2 track keep-out, 35.39 mm² in one piece
(R9 35.31), 7 GND vias.

## D-R3-07. Camera supply vias, ACT_GATE partner, J122 relief

CAM_5V's single layer change is a 0.8 / 0.45 mm via (a second via on a pour-less net is a track loop); U402.1's PORT_5V3
via at (35.45, 40.05), hole 0.15 mm from the pad opening and 0.15 mm from CAM_UART_OE (no room for a second via). ACT_GATE
(16.2, 72.3) gets a GND partner 1.10 mm away (ACT_* are pyro-class on R10). J122's GND pads take thermal relief (O6: no
designed servo current; DRC 0, no starved spoke).

## D-R3-08. GND stitching (R3-RTE-05)

37 stitching vias frozen in `r10_route_ground.STITCH` (a west-edge row x 0.9–5.0, the review's two voids, second vias
in the larger single-via islands, coverage spots), clear of signal vias, legend spots and support keep-outs. Outer GND
more than 4 mm from a GND via: 28.2 / 28.8 % → 7.7 / 7.8 % (F / B, slice measurement before the merge).

## D-R3-09. Port-signal layer changes and hops (R3-RTE-01, -03, -04, -06, -07)

Every layer change of a port UART / control net has a GND via within 1.5 mm (worst 1.455 mm), 9 new GND partners in the
signal family. CAM_MCU_TX's hop removed (CAM_UART_OE enters U12.6 from the north, one 90° pair); CAM_MCU_RX keeps one
hop (it crosses CAM_MCU_TX, CAM_UART_OE and CAM_FAULT_N); the remaining two-via hops each cross named copper
(route_check's new needless-hop test passes all). PULLPIN now drops west of U3 (0.63 mm from U3.3, was 0.165) and climbs
the west edge at x 4.15 (1.01 mm from J3.4, was 0.160). USB_LIMITED's bottom lane at x 31.8. TP86 and R162.2 entries end
at pad centres. Remaining pad-entry / between-pad items are listed with measured reasons in R10_VALIDATION.

## D-R3-10. Gates

`route_check --profile r10`: `arc_segment` (any arc fails); one R10 critical-net definition shared with K-reference
(`critical_reference.R10_PORT_UART` / `R10_PORT_CONTROL`: port UART nets at MCU, buffer and wire, `*_PWR_EN`,
`*_FAULT_N`, `*_UART_OE`), ACT_GATE / ACT_DRV / ACT_EN in the pyro class; on critical nets a two-via hop is needed only if
the other-layer run crosses other-net copper. `critical_reference` samples arcs. `check_r10`: K-loader (AN2606 Rev 64
Table 119 pp. 277–280; allowance table with each pin's electrical reason: PA6 VLOGIC_SENSE ≤ 0.36 mA into R60 / R61, PE11
held off by R431, PA4 / PA5 / PE12 inputs, PA2 / PA3 servos, PA11 / PA12 USB, PB6 / PB9); S-8 (In1 / In2 ≥ 1.0 mm from
pyro barrels); S-5 window (only GND, RAW_ACT, PYRO1_BUS between J124's pads on any layer); S-9 (fire path ≥ 1.0 mm,
ACT_FET_S 0.4 mm bridge a named exception); S-1 counts copper text / footprint zones and any multi-net part; K-legends
checks silkscreen against mask openings as polygons and R10's port tables; P-11 holds J1's −x entry. `plate_model`
refuses or places every mass (f1 275.7 Hz pinned, was 276.4). `r10_fab.sh` runs S-4 on the exported BOM / CPL.
`r10_stage_check` treats `critical_via_no_gnd` as pending before the ground family. `test_r10_check.py`: 68 tests, 20 on
the real board.

## D-R3-11. Silkscreen and footprint graphics

Footprint silkscreen trimmed in `kilib` (pads untouched): PDFN-8's stray EasyEDA arc deleted, near-full arcs made
circles, corner ticks removed; `r10_pcb.py` copies the library silkscreen onto the board (`r10_post.sync_silk`) so
DRC's library parity holds; `min_silk_clearance` 0.15 (JLC pad-to-silkscreen) and the post stage asserts ≥ 0.15 mm from
every mask opening (minimum 0.150 mm). Notes shortened and centred on their terminals: `J124 ARM LAST`,
`J124 5A FAST 2S`, `J1 BAT 15A FUSE` (fuse rating in one constant, OQ-6). One port convention: pin 1 supply, GND, then
board-side TXO / RXI: J9 `1:5V4 2:GND` / `3:RXI 4:TXO`; J410 / J420 tables do not fit within 6 mm (deviation). J122 gets a
top key (`S`, `NC`, `GND`, `SERVO + FROM HARNESS` on top). Every pin-1 mark is ≥ 0.5 mm nearer its own pad 1 than any
other (U401 keeps its footprint mark). Support hardware circles (3.5 mm bottom, 3.8 mm top) are legend keep-outs.

## D-R3-12. R162 1 kΩ (PC14's 3 mA)

R162 (BUZZ_DRV gate resistor) 220 Ω → 1 kΩ (C17513, the existing 1k 0805 line): edge current ≤ ≈ 2.9 mA (DS12110 Rev 10
Table 62 p. 141 characterises PC13–PC15 at ± 3 mA), the gate still reaches 3.0 V (AO3400A V_GS(th) ≤ 1.45 V).

## D-R3-13. Records

F6's battery-break ride-through recomputed (parts_budget.json; 300.8 / 470 µF, to 3.5 V): ports off and logic shed
8.9 / 13.9 ms; ports off, no shedding 4.3–9.1 / 6.7–14.3 ms; camera, radio and GPS on 0.55–0.65 / 0.87–1.02 ms (C84
back-feeds the port buck through U11 below its reverse-blocking threshold; R9 had the camera-on case at 1–3 ms). The
14.5 ms figure is withdrawn as a general claim. Hardware option (port-buck EN cutoff) offered as OQ-5, not implemented.
pin_table gains `an2606_t119_loader_role`; the binding note gains EXTI13 PULLPIN, neutral-first servo output with IWDG
≤ 32 ms, dropping port EN / OE on a power-switch opening or VLOGIC sag, the loader pins and the LR900 band facts; DS12110
citations are Rev 10 throughout. REQUIREMENTS carries R10 amendments (owner-decision bullet, F4, F6, F8, F9, F10, P2,
P3, M1, operating assumptions); ORDERING §8 and README carry R10 banners; FMEA has an R10 row. Local paths removed from
19 R6 records; six R6 records pinned by SHA-256 in other records keep theirs (listed deviation).

## Round 4 (second board review round on `579575bd…`, fix pass; board `af18ac49…`)

Ten independent reviewers (one lens each, fresh contexts, started together) reviewed the committed board `579575bd…`
(commit 8f10f17); findings and dispositions: `docs/R10_VALIDATION.md` "Round 4". Every reported Major was re-verified by
the root before acceptance. The fix pass ran in three file-disjoint slices (routing, gates, records), each built and
gated in its own clone, then merged and rebuilt here; the worktree build and the routing clone's build gave the same
board byte for byte (`af18ac4987ce…`).

## D-R4-01. In2 under the CH1 sense runs re-cut to one region (R4-RTE-01)

PYRO1_CONT's B.Cu run (15.15, 56.8)–(19.85, 56.8) crossed the In2 3V3 / GND boundary with a 0.25 mm unreferenced gap at
x ≈ 17.45, ARM1_SENSE_MID's at x ≈ 20.91 (y 58.75), and RAW_ACT_SENSE's end at R124.2 (22.23, 64.0) had no In2 copper
under it (root's sampling on `579575bd…`: 93, 39 and 12 unreferenced edge / centre samples). `R10_GND_In2_CH1` now
carries a 0.78 mm GND strip under PYRO1_CONT's whole run (R178.1 → C127.1 → the via (24, 55)), its east edge in the
ARM / RAW_ACT sense band moves to x 21.8 and the band's top to y 58.2, the 3V3 west edge to x 22.1 (so 3V3 covers
R124.2), and the GND west edge steps back to x 18.0 at y 53.4–56.45 so R164.1's 3V3 via (19.05, 55.9) keeps its In2 3V3
connection. R128.2's GND joins C127.2's via (21.3, 57.55) on F.Cu (its own via at (18.933, 57.835) blocked the 3V3
tongue's corridor; one GND via fewer). Outline areas: GND CH1 355.81 → 359.83 mm², 3V3 1816.79 → 1819.59 mm²; filled
In2 areas on `af18ac49…`: GND CH1 335.5 mm², 3V3 1521.8 mm², RAW_PROTECTED 1375.2 mm². D-R3-02's tongue and S-8 hold
(every pyro barrel ≥ 1.0 mm from non-GND inner copper). Side effect, recorded: In2 3V3 now lies under R126.1's pad
(PYRO1_GATE_N, F.Cu); In1 GND lies between them and no barrel is involved, so no single inner defect joins them.
check_r10 K-region and the widened K-reference hold the result (D-R4-03).

## D-R4-02. Pad entries straightened (R4-RTE-05)

GPS_TX_WIRE → J410.3 and RADIO_TX_WIRE → J420.3 leave the ESD diode's pad on a 45° run and enter the connector pad
straight on its centre line; CAM_RX_WIRE comes down x 39.4 to y 38.625 and enters J9.3 straight, D401.1 joining it by a
45° run (the 0.212 mm 45° stubs inside the pads are gone). ACT_FET_S enters R120.1 straight on its centre line;
ACT_GATE ends on R120.2's centre by a 45° approach (a straight entry needs a 0.27 mm jog, which route_check refuses).
Not done: the 3V3 via (19.05, 55.9), 0.75 mm from PYRO1_GATE copper on F.Cu (R4-SAF-03): with the CH1 GND strip in
place every other 3V3 spot is sealed from In2 3V3 by GND via antipads or crosses the B.Cu CONT run; listed (deviation
1 case (c)).

## D-R4-03. Gates (R4-RTE-01/-02, R4-GATE-01 … -06, R4-SAF-01/-02, R4-MEC-05)

- **K-reference** samples every signal-critical net of route_check's r10 classes (pyro, crystal, usb, spi, uart,
  portctl; `check_r10.signal_critical_nets()` calls route_check's classifier, one definition). Own-net plated
  through-hole pads count as antipads at half the pad size + 0.6 mm (the In1 / In2 clearance void round a pyro
  terminal barrel cannot be routed away; without it PYRO1_BUS / IGN / OUT fail at J121 / J124).
- **K-region (new):** every B.Cu track of those nets lies over exactly one In2 plane net, with no sample over no In2
  copper outside its own via antipads (the "one In2 region" claim of M3_R10 was not gated before).
- **K-rules (new):** `m3.kicad_dru` pinned by SHA-256 (it is generated by `r10_sch.py`); the project's min clearance
  and every net-class clearance ≥ 0.15 mm, the min track / via / hole figures as floors, no rule severity `ignore`, no
  DRC exclusions. Seeds: a zero-clearance PYRO1_BUS / 3V3 rule and `min_clearance` 0 (both passed `check.sh` before).
- **K-fill (new):** a copy of the board refilled in memory must match the saved fills zone by zone (0.01 mm²).
- **S-1 / S-2:** any part, whatever its net count, with pads on an armed or RAW_ACT-side net and on a supply or rail is
  a finding unless it is a named tie (`GND_TIES`: the divider, filter, gate and FET ties to GND; `SUPPLY_TIES`: D120
  3V3 → PYRO1_COLD, the cold pull-up; Q121 RAW_ACT → ACT_FET_S), each with its reason.
- **S-3:** the gate series resistor's far net must be a non-supply U1 net; the gate pull-down 1 k–100 k; the gate-source
  capacitor ≥ 100 nF (Value fields).
- **S-1 copper:** NPTH pads that carry copper are copper nodes.
- **M-7:** U4's centre −6.0 mm from the roll axis (± 0.05) and pad 1 at (+1.21, −0.75) from its centre (± 0.05).
- **tools/check.sh** runs `tools/test_route_check.py` (57), `tools/test_r10_check.py` (84; the plate test under
  NUMPY_PY) and fails on any failing test; `RealBoardSeeds` raises rather than skips when pcbnew imports but the board
  is missing. The report carries the SHA-256 of the contract tables it read (pin tables, masses).

## D-R4-04. Records (R4-REQ-01 … -06, R4-MEC-01 … -04, R4-PWR-01/-02, R4-BOM-01 … -03, R4-MCU-01 … -04, R4-DOC-*)

ORDERING §8 now supersedes every R9-specific item of §3–§7 (8.1 PCB options, 8.2 assembly / placement preview with
R10's terminal codes, colours, positions and wire-entry sides, the R10 polarity and pin-1 lists, 8.3 after-delivery
positions with TP120 at (18.0, 67.3), 8.4 battery lead, sled, mounting hardware). REQUIREMENTS F8 / F9 legends as on
the board, P2 f1 275.7 Hz, F10's R10 EXTI map. M3_R10: U9 / U400 short necks and a plane-only DC solve (Inference),
L1's 3.02 mm bottom hang, the camera-shroud window as an open fit item, an R14-style 100 g retention table (≥ 5×
rests on staking and external retention, REQUIREMENTS P3's R10 text), the ports' differing UART pin order. Binding
note: RX pull-ups before OE, ADC instance per sense (Inference until checked against DS12110), every no-net pin
analog, lever arm z −2.06 mm (Inference). parts_qualification: L400's proxy land, TXU0202 pin 1 and C84 polarity to
confirm in JLC's preview.

## Round 5 (third board review round on `af18ac49…`, fix pass; board `3b6e15f3…`)

Ten independent reviewers (one lens each, fresh contexts, started together) reviewed the committed board `af18ac49…`
(commit 4d3fe72): 0 Critical, 1 Major, 36 Minor (`docs/R10_VALIDATION.md` "Round 5"). Three file-disjoint slices
(routing / placement / silk, gates, records), merged and rebuilt by the root; two consecutive worktree builds gave
`3b6e15f3…` byte for byte.

## D-R5-01. In2 edges re-cut for pads, margins and chains (R5-RTE-01 / -02 / -06)

Every B.Cu track of a signal-critical net, with its edges pushed 0.1 mm out, every B.Cu SMD pad of such a net (+0.1 mm)
and every connected B.Cu chain now lies over one In2 plane net. `IN2_GND_CH1` rewritten: a strip round C127.1 (x
19.85–21.5, y 54.55–55.6), south edge y 57.2, two arms east to x 27.9 (y 58.05–59.45 and 63.35–64.7) carrying the
ARM / RAW_ACT sense pads and runs, a bay at x 10.5–12.3 to y 71.5 (Q121.4), the strip under PYRO1_CONT ≥ 1.05 mm.
`IN2_GND_Y1` notched at x 18.9–20.6, y 44.3–45.45 so QSPI_NCS's chain is wholly over 3V3. PORT_5V3 band bottom
y 6.8 → 6.55 and a camera bump at x 33.95 (y 38.4–39.79); PORT_4V8 top y 7.1 → 6.85, radio bump x 32.75 → 33.05; 3V3
edges by U420.4 and the camera cell moved 0.3 mm. GND vias moved: D401.2 (38.8, 37.275) → (38.8, 37.0), R411.2
(30.3, 6.6) → (30.3, 4.9), C127.2 (21.3, 57.55) → (22.1, 57.55) with R128.2's strap. Filled In2 areas on `3b6e15f3…`:
RAW_PROTECTED 1371.8, 3V3 1499.4, GND CH1 355.5, PORT_5V3 220.0, PORT_4V8 87.8, GND Y1 33.4 mm²; each region one
piece; S-8 holds (every pyro barrel ≥ 1.0 mm from non-GND inner copper).

## D-R5-02. Pad entries, stubs and silkscreen edge margin (R5-RTE-03 / -04 / -07, R5-MFG-02)

D401 / D410 / D420 0.15 mm north so their UART lines enter the diode pad and the connector pad straight; R422 0.05 mm
east (RADIO_FAULT_N on its axis); GPS_IO_3V3 / RADIO_IO_3V3 vias at (35.5, 17.8 / 29.8) with the 45° runs from the via
centre (no 0.1 mm stub). `r10_post.py` keeps every legend and designator stroke ≥ 0.615 mm inside the outline; TP89
(BAT_ILIM) moved to (44.42, 81.83) with its via and run, TP81 to (44.3, 68.0) and its RAW_PROTECTED via to (43.2,
68.0) so its ring stays off the bare pad. TP89 is now the nearest top pad to the (42, 86) support: 3.806 mm against
fit_check's 3.8 mm. Not done, each with its measured blocker: SPI1_MOSI → U4.14 (the SCK / MISO lanes leave 0.03 mm too
little for a via on the pad axis), PULLPIN → U1.7 (C25.2's via 0.12 mm from an on-axis run), VBUS → U10.1 (D4.5's
paste), IO rails → U411.7 / U421.7 (the via's antipad would reach the OE run), CC1's 0.113 mm segment inside its via
(the clean geometry makes K-reference's REF_STRAY entry for USB_DM stale; left for a later gate edit), TP88's footprint
silk 0.426 mm from the edge (its vias block a move). One more designator is hidden (93: C89 and R453 hidden, R153
shown) because the silkscreen keep-in moved.

## D-R5-03. Gates (R5-RTE-01 / -02 / -05 / -06, R5-SAF-01 / -02, R5-GATE-01 … -03)

- **K-region:** tracks and arcs sampled every 0.02 mm on the centre line and on both edges pushed 0.1 mm out; B.Cu SMD
  pads on a 0.05 mm grid over the pad grown by 0.1 mm; each sample over exactly one In2 plane net; each connected B.Cu
  chain (track ends, or a track ending on a pad of the net) over one plane net. Exempt: samples within 0.45 mm of an
  own-net via; samples in an own through-hole pad's real clearance void (a no-copper component wholly inside the pad's
  disc of half size + zone clearance + 0.05 mm, by flood fill; a seeded slot running beyond it now fails); no-copper
  samples inside another net's via antipad (via pad radius + 0.30 mm), a clearance hole that K-reference already
  holds (root, for the SPI1_SCK / MISO samples beside the MOSI via (17.55, 43.5)). REF_STRAY no longer applies to
  K-region.
- **S-1 / S-2:** any part other than U1 with more than four nets on both a RAW-side net (RAW_ACT, its SENSE / MID / MCU
  nets, ACT_*) and an armed-side net (PYRO1_*, ARM1_*) fails.
- **S-3:** gate series resistor 100 Ω – 10 kΩ; a capacitor value without a unit is refused; GATE_N needs a resistor to
  GND of 100 Ω – 100 kΩ.
- **check.sh:** exports `R10_BOARD="$BOARD"` for the self-tests; a self-test failure prints its message even when the
  output is only Debug lines. `tools/test_r10_check.py` 90 tests.

## D-R5-04. Records (R5-MFG-01, R5-REQ-01 … -04, R5-PWR-01 … -04, R5-MCU-01 … -05, R5-MEC-01 … -05, R5-DOC-01 / -02)

ORDERING 8.1 / 8.2: vias plugged where JLC's 0.35 mm plug-ink clearance allows, otherwise tented, never an opening
over a via, the expected DFM query (222 of 350 vias within 0.35 mm of a pad opening, 108 within 0.15 mm, on
`3b6e15f3…`); the bottom coat list with R177 and every part in the boxes; TP89 high-impedance probing; a 6.0 V
loaded-pack port-rail step; standoff + plate ≤ 6.9 mm; the shroud placement rule (aft edge ≥ joint + 37.2 mm).
REQUIREMENTS F6: R9's EN network (bounce figure carried). M3_R10: OVLO pin range, AP63201 IQ, VBUS_SENSE ≥ 4.62 V,
retention table with body + plug masses and J3 / LS120 rows, "5V4". masses.json: LS120 0.3 g (Inference); f1 275.6 Hz.
Binding note: LSE never enabled, every no-net pin analog, PA6 / PB1 pin-fault notes, VBUS_SENSE not a safety input.
pin_table.tsv: 26 DS12110 page citations corrected (citation column only; no gate pins the file; the binding note
records its new hash).

## Round 6 (fourth board review round on `3b6e15f3…`, fix pass; board `b242ab8e…`)

Ten independent reviewers (one lens each, fresh contexts, started together) reviewed `3b6e15f3…` (commit b3ed2fe):
0 Critical, 1 Major, 39 Minor (`docs/R10_VALIDATION.md` "Round 6"). Three file-disjoint slices (In2 copper, gates,
records), merged and rebuilt by the root; two consecutive worktree builds and the slice's clone gave `b242ab8e…`.

## D-R6-01. CH1 In2 GND arms widened round the sense vias (R6-RTE-01)

`IN2_GND_CH1` now widens round each sense via: PYRO1_CONT x 22.5–25.7, y 53.9–56.1; ARM1_SENSE x 25.2–28.6,
y 57.65–60.8; RAW_ACT_SENSE x 25.8–28.6, y 62.85–65.75 (its south edge pushed out over x 23.4–25.8). Existing GND vias
that sat in In2 3V3 now fall inside the arms and stitch them ((25.2, 55.0); (24.8, 60.24), (26.8, 60.15), (28.2, 59.6),
(21.917, 59.61); (23.93, 64.86), (24.8, 65.49), (27.2, 65.4), (26.67, 66.07)). Measured on the filled polygon (0.05 mm
raster): no GND strip narrower than 0.5 mm; 0.65–1.65 mm of GND round each via hole; farthest arm point 2.64–2.89 mm of
copper from a GND via. Filled In2 areas: GND CH1 377.5 mm², 3V3 1477.2 mm² (others unchanged). The ARM1_SENSE and
RAW_ACT_SENSE F.Cu diagonals cross over In2 3V3 as before (F.Cu references In1 GND; K-reference holds).

## D-R6-02. Gates and the fit tool (R6-RTE-02, R6-SAF-01 / -02, R6-GATE-01 … -08, R6-MEC-04 / -05)

- **K-region:** a no-copper sample is exempt only inside a hole of the In2 fill that contains a foreign via centre and
  whose every vertex lies within (that via's pad radius + 0.3 mm) of a via centre (so merged holes of adjacent vias,
  like SPI1's three at (16.7, 43.1), (17.55, 43.5), (17.55, 44.25), stay exempt; a slot or pull-back does not).
  `OwnPadVoids` tests on polygon geometry (64-gon disc) instead of the 0.04 mm grid, so a 0.03 mm exit slot counts.
- **S-1:** any part with a pad on an armed net must be in `ARMED_PARTS` (J124, J121, R134, Q124, R132, R131, R173,
  C128), each with its nets. **S-3:** PYRO1_GATE_N may touch only U1, the series resistor and 2-pad resistors to GND.
  **S-8:** plated pads of other nets count; RAW_ACT (J124.2) is a barrel net.
- **parse_value:** infix values (4k7, 2R2, 4n7, 100k5) and a fully consumed token.
- **Tests:** `tools/test_r10_check.py` 102 (margin, arcs, step, pad-chain join, void radius, slots, via holes, the
  round-6 seeds).
- **fit_check:** wire room with two decimals (4.95–5.55 mm); the r10 report's `mated_envelopes` uses the GH-2 box for
  J123 / J400.

## D-R6-03. Records (R6-MEC-01 … -06, R6-REQ-01 … -08, R6-PWR-01 … -03, R6-MCU-01 … -05, R6-SAF-03 / -04, R6-MFG-02, R6-RTE-03)

Camera shroud rewritten (M3_R10, ORDERING 8.4, REQUIREMENTS P2): the board, its GH-4 plugs and (if the shroud faces the
top) J122's plugs would penetrate the shroud by ≈ 4.6 / 3.8 / 5.1 mm wherever the board overlaps joint + 4…+47 axially,
so the board sits wholly forward of joint + 47 mm in any clocking unless a measured clearance replaces the rule; owner
question OQ-7. REQUIREMENTS F7 R10 hand budget (Calc), M3 R10 line, R430 wording; ORDERING 8: via counts 222 / 108 in
the order remark, method, C11 nearest coated part to U4, J3 staked (J123 / J400 tie or RTV), USB-only attach and
ACT_GATE turn-on bench steps, nut on the sled side, TP89 0.306 mm to a nominal washer; M3_R10: PORT_5V3 neck 1.20 mm,
τ ≈ 20 ms, lever-arm frame, silk keep-in basis. Binding note and pin_table: PE1 EXTI1 data-ready with pull-down,
sentinels analog never driven, ADC channels verified, no synchronous trace and GPIOE_LCKR on PE4, W25Q QE bit, IMU SPI
≤ 10 MHz, 40 ms gyro Ton, no blocking erase in flight. Schematic note (mcu sheet, r10_sch.py): "PE1 remains polled"
replaced (the netlist is unchanged).

## Round 7 (fifth board review round on `b242ab8e…`; first clean round; gates and records only)

Ten independent reviewers reviewed `b242ab8e…` (commit 9dadb9a): 0 Critical, 0 Major, 33 Minor (`docs/R10_VALIDATION.md`
"Round 7"). The fix pass changed no generator input that reaches the board, so the board stays `b242ab8e…` and round 8
reviews the same board. Copper Minors (R7-RTE-01 … -03) and part-code Minors (R7-BOM-01 / -02) are listed rather than
fixed, to keep the board frozen for the second clean round.

## D-R7-01. Gates (R7-GATE-01 … -04, R7-SAF-01 / -02)

`parse_value` accepts "4.7 kΩ", "220 Ω", Ω / ohm after the multiplier and Greek mu, refuses a capacitor "100m" and any
unconsumed tail. K-region's via-hole exemption requires the hole polygon minus the union of via discs (pad radius +
0.3 mm, 64-gons) to leave ≤ 2e-3 mm² (SPI1's merged three-via hole leaves 4.95e-4 mm²; a 10 mm slot ≈ 8 mm²). S-1:
`ARMED_NET_PARTS` names every part on every armed-side net (PYRO1_BUS / IGN / OUT / COLD / GATE / CONT / CONT_MID,
ARM1_SENSE / _MID, RAW_ACT / _SENSE / _SENSE_MID); `mcu_side_issues` asserts each `*_MCU` net and PYRO1_GATE_N is U1
plus one 3.3–6.8 kΩ resistor (R126 for GATE_N, plus its pull-downs). S-3: only R126, R128, C126, Q124 and TP122 on
PYRO1_GATE. Seeded P-11 (J121 −0.6 mm) and F9-1 (D8 +3 mm) tests. `tools/test_r10_check.py` 108 tests.

## D-R7-02. Records (R7-REQ-01 / -02, R7-PWR-02, R7-SAF-03, R7-MCU-01 … -04, R7-MEC-01 … -07, R7-MFG-01 … -04, R7-BOM-03, R7-DOC-01 / -02)

REQUIREMENTS F7: the re-measured fire path (27.1 mΩ of track, 5 mΩ GND allowance, FETs × 1.42 hot, 10 mΩ contacts,
R134 + 1 %: 4.533 Ω; 1.633 A at 7.4 V, two stalled servos 1.506 A with no margin, treated as failing until the harness
is measured). Binding note: PA15 set to analog explicitly; GPIOE_LCKR LCKK read-back before arming and the loader-jump
sequence; loader jump only before the IWDG starts (≈ 34 ms at the LSI corner); W25Q128JV erase 45 ms typ / 400 ms max
and the pad ring-buffer obligation; no trace-capable debugger with the ARM link in. FMEA F-16 R10 line (only PE4
locked). ORDERING 8: R10 differences from §1 / §2, 127 pluggable vias (CAM_5V tented), J3 hand-finish neighbours,
R430 confirmation and fallback, USB attach inrush, nut-inclusive bound h + t < 6.3 mm (< 5.7 mm at (3.7, 86)), R10
battery-lead row. M3_R10: shroud list with J3 and washers, offsets vs radial, the stack arithmetic (OQ-7 bites only if
the bay or lead zone shrinks by ≈ 30 mm), left-handed board frame, TP89 nearest top hardware, fit_check's two-decimal
print. AGENTS GNSS / radio cell wording.

## Round 8 (review of `b242ab8e…` again, commit 6bc0a63; fix pass; board `407d1d84…`)

Ten independent reviewers: 0 Critical, 3 Major (a red gate test and two ORDERING records), 22 Minor
(`docs/R10_VALIDATION.md` "Round 8"). The clean-round count restarts. Three slices (copper clean-ups, gates, records),
merged and rebuilt by the root; the slice's clone build and the worktree build gave `407d1d84…`.

## D-R8-01. Copper clean-ups (R7-RTE-01 / -02 / -03, R8-RTE-03)

VBUS_SENSE is one B.Cu run via (17.875, 29.8) → apex (19.0875, 31.0125) → TP92.1 (no flat jog). U11.3's GND via
(31.5, 62.9) → (31.5, 63.3), widening the In2 3V3 neck beside C97.2's via from 0.24 to ≈ 0.59 mm (C97.2's own via has no
clean spot: R87.2 / R88.1 leave 0.525 mm). `IN2_GND_Y1` gains a bump (x 26.8–28.6, y 45.8–47.0) that takes the 3V3 tooth
beside C22.2's via into the crystal GND island (35.6 mm²). A GND stitch via at (7.4, 51.2), 1.43 mm from I2C1_SCL's
layer change, 1.0 mm from U5's pads; I2C1_SDA's via (9.97, 51.5) keeps 1.88 mm (no DRC-clean spot within 1.5 mm:
U5's 1.0 mm keep-out, R13 / R64, the 3V3 via (9.2, 52.98)). Side effect: U5's designator is now hidden (94 hidden).

## D-R8-02. Gates (R8-GATE-01 … -05)

`tools/test_check_shell.py` stubs every self-test and the fab manifest step, adds a failing case per self-test stage,
and runs in check.sh's self-test stage (a mutation that removes the stage fails it). K-legends pins the exact
"M3-ASSY-R10", "J124 ARM LAST", "J124 5A FAST 2S", "J1 BAT 15A FUSE" texts and refuses a hidden designator on J1, J121,
J124, J122, J400, J9, J410, J420, J123, J3, Q120, Q121, Q124, R134; the hidden set is reported. K-width (new): no
BAT_IN / RAW_PROTECTED track below 0.3 mm and no 0.3 mm run longer than 2.0 mm. check.sh verifies the fab manifest
when it checks the repository board (`R10_SKIP_FAB_MANIFEST=1` inside `r10_build.sh`, which runs before `r10_fab.sh`)
and runs test_fit_check (23) and test_paste_check (5).

## D-R8-03. Records (R8-MEC-01, R8-MFG-01 / -02 / -03, R8-REQ-01 … -04, R8-SAF-01, R8-MCU-01 / -02, R8-MEC-02 … -05, R8-RTE-01 / -02, R8-DOC-01 / -02)

ORDERING 8: coat ≥ 3 mm off U5's pads and body, R13 / R64 masked, U5 taped whole while coating, TP122 brushed from its
south / east side; one complete R10 order-remarks block (no cleaning, reflow order, paste and U4 mask as supplied,
stencil, THT method and hole-fill pins, J3 legs, vias, consigned U4, preview checks) and the §4 lines that do not apply;
cost / stock files are evidence; trace-override and HSE bench steps; standoffs ≥ 4.0 mm recommended (L1 gap 0.48 mm
minus ≈ 0.29 mm static deflection). REQUIREMENTS: F7 path wording, board position, pad-time pack ≥ 2 Ah with continuous
transmit, binding plate bound 6.3 / 5.7 mm. M3_R10: QSPI lengths, nets over Y1, DB125 8.60 ± 0.30 mm (DORABO T0-1),
U4–U5 spacing, foam cap. Binding note: UART break handling on an unplugged port, trace-override step. README cells.
