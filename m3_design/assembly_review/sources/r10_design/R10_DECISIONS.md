# R10 decisions

R10 is a CAD candidate (built by `m3_design/r10_build.sh`; not owner-accepted). R9 remains the accepted board. These records do not change the
owner's decisions in `r10_plan.md` sections 6, 7 and 8.

Sealed historical records keep their original text, including numbers glued to words; only the lines R19-DOC-04 named
(in D-R16-01 … D-R17-01) were respaced, on 2026-10-31, with no change to any value.

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
in the seeded DRC scratch project at `wxGetMousePosition `, because the headless session
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
ROM-loader interfaces. PD0 / PD1 return to NC. Changed: `pin_table.tsv` rows 51 / 52 / 81 / 82, `circuit.json `
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

R410 shares the 100 kΩ line (C14675; 120 kΩ C114607 would add an extended code). `parts.json `, `r10_parts.py` and
`parts_budget.json ` now carry 100 kΩ: GPS limit 0.230–0.309 A (TI SLVS841F eq. 1 p. 15, R ± 2 %); all three ports
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

**R12 correction:** the <=2.9 mA maximum above is withdrawn; see D-R12-01. The resistor value stays1kOhm.

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

## OQ-4 answered (owner, 2026-10-28): panel rails, no layout change

The owner chose the option that keeps the layout cleanest and closest to AVA's simplicity: keep the GH port column on the
east edge as placed and hold the aft-east corner with a tab on the aft edge, so the JLC panel takes a rail (frame) along
the aft edge. Moving a port to free a side tab would cost layout rework and break the port column's straight escapes.
JLC's acceptance of the aft-edge tab and rail is to be confirmed before ordering (docs/ORDERING.md).

## Terminal wire range (OQ-1 context, 2026-10-28)

AVA uses 3.5 mm-pitch screw terminals for every wire (reports/AVA board layout images.md, pitch measured against the
LQFP-64's 0.5 mm pins), the same pitch as R10's DORABO DB125-3.5 (J1 green, J121 / J124 black). DORABO's T0-1 drawing
(parts_qualification.md) rates them 28-16 AWG, 10 A UL / 13.5 A IEC, 4-5 mm strip, 0.2 N m. Against the order's wires:
the XT30 battery pigtail (16 AWG) is at the top of the range (ferrule recommended); the 16-18 AWG and 22 AWG silicone
leads for ARM / igniter fit; the battery current is <= ~6 A peak with servo power off the board, within 10 A. E-match
leads thinner than 28 AWG (their gauge depends on the brand, not yet chosen: Inference) should be spliced to a 22 AWG
lead or ferruled before the terminal.

## Owner answers, 2026-10-28 (OQ-1, OQ-2, OQ-5, OQ-6, OQ-7)

- **OQ-1 (wire room):** accept 4.95 mm (R8 / R9 6.25 mm) with 16-22 AWG in the DB125-3.5 terminals; a deviation, to be
  confirmed by the physical fit check. check_r10 P-11 holds R10's 4.95 mm as the floor (no worse), not R8's figure.
- **OQ-2 (hot plug):** re-model, do not move: re-run the reverse / hot-plug simulation (R8's model, docs F9) with R10's
  actual BAT_IN feed lengths and parasitics to U9 and the protection parts; move the parts only if the model fails. F9-1
  becomes "the R10 model passes" instead of R8's distance premise.
- **OQ-5 (ride-through with ports on):** "do whatever AVA does". AVA has a bulk capacitor on the back and switches its
  peripherals in firmware; no hardware dropout cutoff is known on it (Inference: none visible in the public images,
  reports/AVA board layout images.md). So no port-buck cutoff is added: F6's ride-through relies on C84 plus firmware
  load shedding (ports off on the PA6 analog watchdog), and the 0.55-1.0 ms ports-on figure is listed as a deviation
  with the shedding latency as the firmware requirement.
- **OQ-6 (battery-lead fuse), revised the same day:** **no battery-lead fuse**, as AVA (no fuse visible in its public
  images, Inference). The owner first chose a <= 10 A fuse, then dropped it after weighing it: everything after U9
  (TPS25947 eFuse, 3.96-4.84 A) is current-limited, a shorted igniter is held to about 4.2 A by R134 for <= 20 ms, and
  servo power is off the board; a fuse holder adds a series contact whose vibration break the board rides through for
  only 0.55-1.0 ms with the ports on (F6). Accepted residual risk (R10 deviation list): a hard short between the pack and
  U9 / Q120 (battery lead, J1, BAT_IN copper, D8, C80 / C96 / C89 / C95) is not current-limited. Mitigation is harness
  practice: strain relief, no chafe points, crimped or soldered leads. The `J1 BAT 15A FUSE` legend (r10_post.J1_FUSE)
  is removed; the ARM link's 5 A fuse (`J124 5A FAST 2S`) is unaffected.
- **OQ-7 (camera shroud):** the lower option: keep the board wholly forward of joint + 47 mm, so no shroud clocking is
  needed for fit qualification; VEHICLE.md's stack keeps its slack.
- **OQ-3 (cost $87.01 vs $84.41)** is not yet answered: it stays on the deviation list for the owner's acceptance.

## Owner-answer implementation before the fresh round 9 (2026-10-28)

The interrupted three-lens round 9 is a prelude, not a full review and not a clean pass. The following implements
the answers above before freezing a new committed target for ten fresh review lenses. No overall acceptance of
R10 is inferred from the individual answers.

### D-OA-01. Harness, fit and assembly records (OQ-1 / -4 / -6 / -7)

Remove only the J1 battery-fuse legend from the post generator and its exact-text gate; keep J124's `ARM LAST`
and `5A FAST 2S` legends. R10's active ordering and requirement text specifies an unfused pack-to-U9 / Q120
stretch and its accepted hard-short risk, strain relief, no chafe points and crimped or soldered leads. Earlier
revision fuse instructions stay explicitly scoped to those revisions. The R10-specific harness table retains
the separate 5 A fast 2S ARM-link fuse.

P-11 uses the owner's 4.95 mm floor; the physical harness / bore check remains open. The aft-edge tab and panel
rail are selected, with JLC confirmation before ordering. The fit record and vehicle stack place the board wholly
forward of the booster/main joint + 47 mm, including mounting tolerance, and retain the freed length as slack.
There is no new requirement to clock the board against the camera shroud.

### D-OA-02. Firmware shedding and thermal estimate (OQ-5 / R9-PWR-01)

No hardware port cutoff is added. The binding-note generator explicitly requires the PA6 ADC1/2 analog watchdog,
port OE / EN shutdown, a qualified detection-to-command latency and actual load-current decay. TPS2553's turn-off
can take up to 3 ms, longer than the estimated 0.55–1.0 ms ports-on ride-through; the 8.7–13.6 ms figure cannot be
credited until the ports have actually stopped drawing current. The threshold, worst-case latency and surviving
load envelope must be demonstrated in firmware / bench qualification.

The parts-budget generator now uses the qualification record's inferred 80–110 C/W range for U401, not the
62.5 C/W reference-board figure. At the existing 0.40618 W loss and 85 C ambient this is 117.49–129.68 C junction
temperature (Inference). This fixes a contradictory estimate, not a measured thermal failure.

### D-OA-03. Historical routing aids

The aid README now identifies the router experiments as historical feasibility work. D-R2-08's owner decision
requires every signal to be hand-routed, and D-R2-09's explicit tables are the production implementation. The
obsolete instruction to freeze an autorouter result over those tables is removed.

### D-OA-04. OQ-2 failure confirmation

The saved board's separate J1-to-capacitor and J1-to-U9 branches fail the new transient model within F9's
0.1 uH / 0.03 ohm corner. A fresh verifier reproduced the mechanism with independent RK4 and extracted-MNA
calculations; see `owner_hotplug_reverification.md`. OQ-2's condition for layout remediation is therefore met.
A takeoff downstream of the input capacitor branch is being qualified. No passing model, regenerated production
board or passing fix commit is claimed by this decision alone.

### D-OA-05. Retained U9 output voltage

The TPS25947 cold limit also depends on retained OUT voltage. With C84 allowed to feed RAW_PROTECTED through
U11, the old 10 kohm R92 does not provide a comfortable two-second discharge estimate. Change R92 to 3.3 kohm,
1%, UNI-ROYAL 0603WAF3301T5E / C22978 on the same 0603 land and nets (`circuit.json ` replacement). This adds one
Basic BOM code and no component or extended code. The nominal extra draw is 1.73 mA at 8.5 V, 14.67 mW.

The sensitivity calculation includes every inventoried board capacitor, C84 at twice its nominal capacitance,
every rail initially at 8.5 V, R92 tolerance / temperature coefficient, and no load or divider-bleed credit.
The final inventory is 1675.3395136 µF; its common-node estimate is 5.954856 V at two seconds. C84's temperature behavior and arbitrary
converter reverse-energy behavior remain explicit inferences to verify on the bench; this is not a measured
discharge guarantee. `parts_qualification.md` records the exact part source and `hotplug.md` the final calculation.

The ride-through budget now adds R92's whole 7.4 V maximum dissipation explicitly (16.93 mW), without credit
for an old load-envelope allowance. Ports-off/shed estimates become 8.7 / 13.6 ms at 300.8 / 470 uF to 3.5 V;
ports-on estimates still round to 0.55–1.0 ms. This preserves OQ-5's firmware-only architecture.

### D-OA-06. Input feed and damper requalification

The independently confirmed split-feed failure in D-OA-04 authorizes OQ-2's remediation. U9 now takes BAT_IN
downstream of the protection-column branch, through one 1.0 mm / 0.5 mm drilled via; Q120 retains its separate
J1 feed. No parts move. R166 changes on its existing 2512 land to 0.36 Ω, 1%, UNI-ROYAL 25121WF360LT4E / C168925:
the 0.33 Ω candidate reached −15.10 V at a cold-resistance corner. The 2304-case candidate sweep with 0.36 Ω
passes numerically (−14.497874 V minimum, 8.654349 V/µs maximum falling slew), subject to final-board extraction
and the full build gate. `hotplug.md` records the maker sources, tolerances, numerical controls and limitations.

F9-1 replaces the old part-distance comparison with board-derived model evidence: actual feed tracks, pads,
via and stack-up, capacitor and resistor identities, the source curves, solver, full corner set and refined
extrema must match and pass. The unfused harness must still measure at least 0.03 Ω within the specified
0.1–2 µH envelope; lower-resistance sensitivity cases are failures outside that domain. This does not add a
battery fuse or infer a guaranteed R166 pulse rating. Physical pin waveforms, harness parasitics, retained OUT
and repeated hot/cold R166 pulse durability remain qualification obligations.

The two substituted resistor codes use their own LCSC-to-JLCEDA product mappings for the assembly rotation
check (`tools/jlc_easyeda/pads.json `), fetched 2026-10-28 from the recorded public source URLs. No donor
footprint or price/stock claim is inferred from the old codes.

### D-OA-07. C88 intercepts the feed; local copper remains in the model

The D-OA-06 numerical result used an ideal C88-to-U9 connection. A fresh independent MNA calculation retained
that branch and demonstrated sensitivity to assumed pin capacitance and contact-edge time: 100 pF and 1 ns
gave 13.60 V/µs, or 12.60 V/µs after removing trace counted inside the pads. The exceedances were at most
0.60 ns long. Neither assumed parameter is maker-qualified; this establishes an optimistic model approximation,
not a measured or guaranteed physical failure. The contracted result is superseded as qualification evidence.

The simplest stronger topology feeds C88 before U9: U9 is a dead end beyond its bypass. No component moves or
extra via is needed. The new entry/exit copper is 0.7 mm wide (0.80 + 1.15 + 0.97 mm), with the existing 0.3 mm
U9 entry retained. At 4.84 A and 85 °C, a one-dimensional equal-end-temperature conduction estimate gives
89.16 mW and 5.10 °C added neck rise (Inference, not the local board temperature). The thinner 0.4 mm trial
gave 127.14 mW and 10.38 °C. `parts_qualification.md` records the model and clearances.

The feed via moves from (33.45, 84.0) to (34.7, 84.0), with a 45° approach. This restores the required front
`SERVO + FROM HARNESS` legend without changing its 1.0 mm text or clearance/subject rules; its ink is 0.425 mm
from the via ring (required 0.155 mm). The approach is approximately 0.73 mm shorter to the U9 column. No
post-generator algorithm or gate is weakened.

Schema 3 retains every extracted local edge; the gate requires C88 to separate U9 from every other model terminal.
It also checks finite-edge/pin-capacitance sensitivities and their convergence, labelled as assumptions. Independent
constant-C Python MNA and the charge solver agree within 1.2e-9 V/µs on the 100 pF / 1 ns diagnostic; halving
the 25 ps step changes the falling slew by 0.000183 V/µs. Final-board evidence and the full build gate are required.

### D-OA-08. Record corrections before the fresh full round 9

The GPS translator's B supply is GPS_IO_3V3 from U412, supplied by GPS_4V8; the round-8 qualification paragraph
incorrectly named PORT_4V8. Correct the paragraph against `circuit.json `, without changing the circuit. Keep
historical stop records explicitly historical, resolve the superseded owner questions, and report new CAD/software
checks separately from simulation, firmware, physical and bench qualification.

The first production build's metadata gate rejected R92 / R166: the reused footprint still carried its old
`LCSC Part` field while the native netlist updated `LCSC`. In `r10_pcb.py`, remove that obsolete legacy field
when it contradicts the new canonical field. The schematic's replacement part already omits it. This changes
no copper or geometry, and the metadata audit remains mandatory and unchanged; rebuild before committing.
K-legends also rejects a J1 fuse legend, rather than merely ceasing to require the old one; a seeded old
`J1 BAT 15A FUSE` text fails while J124's ARM-link fuse note stays required.
The actuator contract's R10 profile pins R166 to C168925, matching the qualified model; its R9 profile retains
C25468. All other retained safety-part pins and topology checks remain in force.

### D-OA-09. Complete the interrupted pass before audit implementation

Retain all interrupted owner-answer changes. Two fresh complete builds agree byte for byte on `b860afbe…`;
the regenerated fabrication package and unskipped full gate pass (R10_VALIDATION owner-answer completion).
The CLI crashes at wxGetMousePosition in this headless session; use D-R1-05's external mouse-query interposer
and a temporary wrapper, without changing a DRC result, gate, CAD rule or repository runtime dependency.
The prior incomplete round-9 prelude receives no clean-round credit. Implement the adopted AUD/GAP cuts next,
then freeze a committed target for ten fresh independent review lenses in round 9.

**Commit blocked by the environment:** `git add` and `git commit` cannot create this worktree's `index.lock`
(Operation not permitted), including when invoked from the declared writable common Git directory. No staging or
commit succeeded. Do not label this board committed or count a fresh review round. The source audit cuts have not
started; `audit_preflight.md` preserves the read-only part qualification and layout plan for continuation after the
Git write access is repaired. No AGENTS §2 change or owner decision is required by this technical blocker.

## Requirements audit cuts (owner direction, 2026-10-28)

The owner directed that every requirement be rooted in the flight's physics (flight 1 K850DM ~Mach 1.45, flight 2
L1000W ~Mach 1.9, 2S pack, one roll tab, one recovery channel plus the isolated Blue Jay) or in BPS.space AVA's design
choices, not in margins inherited from R1-R9, and that the agents decide without further owner questions. A read-only
requirements audit (2026-10-28, gpt-6.1-sol) ranked the cuts; these are adopted. AGENTS §2 items 1-5 are untouched.

- **AUD-1 IO-LDO output capacitors** (C92 / C442 / C452 if they survive AUD-8): 22 uF / 25 V 1210 -> the TPS709
  datasheet's requirement (Ceff >= 1.5 uF over bias, tolerance and temperature; TPS709 §8.1 / 8.2.2). Physics: the rail
  feeds a translator and a 1 kOhm bleed (~3.3 mA).
- **AUD-2 Slow nets leave the return-path geometry rules:** filtered ADC sense (tau ~9 us), ACT_EN / ACT_DRV /
  ACT_GATE, port EN / FAULT / OE drop the 1.5 mm GND-partner via and one-In2-region-per-chain rules (AGENTS §3 and
  REQUIREMENTS M2 scope narrowed by name). Fast interfaces (USB, HSE, SPI, QSPI, IMU CS, UARTs) and S-8 keep them. Remove
  the partner vias and CH1 In2 plane arms that only those rules required.
- **AUD-3 Load-switch FETs Q120 / Q121:** replace the 5 x 6 mm pair with a <= 3 x 3 mm back-to-back pair if one is
  qualified: hot RDS(on) <= 40 mOhm at the minimum gate drive, 20 ms SOA at 4.2 A, and VGS tolerance for the ~18 V clamp
  event (reject +-12 V gates). Physics: they now carry <= 4.2 A for <= 20 ms, not 7.7 A continuous. If no JLC-stocked
  part qualifies, keep the incumbent and record why.
- **AUD-4 Pull-pin removed** (J123, R160 / R161, C160, D122; F9 / FMEA F-7 clauses deleted). Root: none in the flight's
  physics; launch is detected by the accelerometer (FMEA F-6) and the pin had no authority after launch. AVA has no
  pull-pin input (Inference). The ARM plug and the power switch stay.
- **AUD-5 Test pads TP84 / 85 / 86 / 87 / 89 / 92 removed;** TP80-83 and TP120-122 kept (hot-plug and pyro gate probes).
  The values stay probeable at part pads, as on AVA.
- **AUD-6 Fire-only copper** (RAW_ACT, PYRO1_BUS / IGN / OUT) 1.0 -> 0.5 mm; the continuous BAT_IN / U9 feed is unchanged.
  Physics: 4.2 A for 20 ms gives ~5.6 K adiabatic rise at 0.5 mm; fire current falls ~0.01 A.
- **AUD-7 Pull-ups and series resistors:** R412 / R422 / R432 10 kOhm 0.1 % 0603 -> 10 kOhm 0402 (a digital pull-up needs
  no precision); R150-R153 1 kOhm 0805 -> 0603 rated >= 100 mW (8.4 V chafe into a low output: 64 mW). Correct the passive
  derating rule to the fault power, not 30 % of rating.
- **AUD-8 GPS and radio IO LDO cells removed** (U412 / U422, R443 / R453, C441-443, C451-453): the GPS / radio TXU0202 B
  side runs from 3V3 (both are 3.3 V UART modules, as AVA wires its peripherals direct). The OE-low isolation, 1 kOhm
  series resistors and ESD stay; firmware holds OE low whenever the port switch is off (firmware obligation). Accepted:
  a mis-set OE can feed an unpowered module a few mA through 1 kOhm. The camera keeps U13 (PORT_5V3 exceeds TXU0202's
  5.5 V supply maximum).
- **AUD-9 USB-only board power kept** (U10 / U11): configuring and downloading logs on the bench without a pack is a real
  use, and the mux is not a redundant protection layer.
- **AUD-10 Drawing hygiene non-blocking:** route_check's harmless graph artifacts (collinear nodes, duplicate
  representations, inside-pad segments) and the 6 mm legend-subject rule become review findings, not gate failures;
  connectivity, DRC, clearance, assembly and fast-return checks stay blocking; 1.0 mm / 0.15 mm silkscreen (JLC) stays.
  Add the missing J410 / J420 pin tables if room allows. Clean routing remains the goal.

Real gaps from the same audit, to be fixed (physics or datasheet roots):
- **GAP-1 Fire-current budget (F7):** superpose all pack loads through the pack resistance,
  I_fire = (Voc - Rpack x I_other) / (Rpack + R_fire); restate the margin honestly (two stalled servos and the ports give
  ~1.46 A vs the 1.5 A all-fire) and record the e-match all-fire / pack requirement that results, without weakening R134.
- **GAP-2 U9 output protection layout:** a >= 1 uF capacitor and the output Schottky within a short loop of U9's OUT pins
  (TPS25947 §8.4.1); today C82 is ~13.3 mm and D9 ~18.9 mm away. Move the existing parts.
- **GAP-3 U401 thermal:** thermal vias under the exposed pad and a junction estimate at 70 °C bay ambient <= 125 °C.
- **GAP-4 C84 order remarks:** remove the inherited OS-CON reflow text from ORDERING §8.2; record the MA capacitor's
  real reflow basis or a hand-solder instruction.
- **GAP-5 Pyro gate timing:** recompute the floating-MCU gate discharge (10 k || 1.22 k with 220 nF, ~0.5 ms) and write one
  worst-fault fire-duration contract consistent with the watchdog period and R134's pulse energy.
- **Owner questions closed by physics:** "neutral quickly" = a neutral PWM command within 50 ms (the servo's physical
  response is a servo / bench matter); pad wait and pack size: REQUIREMENTS' existing operating assumptions stand (no
  circuit depends on them); single-fault envelope = AGENTS §2 plus the pyro single-resistor rule, the rest single-string as AVA.

## Single screw switch for power and arming (owner decision, 2026-10-28)

The owner replaced the separate ARM plug with one external screw switch that both powers and arms the board, as
commercial altimeters (Featherweight Blue Jay, EasyMini, RRC3) do. Owner's words: "Ok go with one switch".
- **Board:** J124 (ARM terminal) is removed; RAW_ACT joins PYRO1_BUS on board copper behind the load switch Q120 / Q121, so
  the pyro feed is still taken after the load switch, never straight from the battery (AGENTS §2.2 unchanged). The R134
  2 ohm limit, Q124's gate network (pull-down, series resistor, gate-source capacitor, off in reset and unpowered) and
  the continuity / bus sense stay. The ARM link's 5 A fuse and its `J124 ...` legends go with J124.
- **Firing chain:** the screw switch on J400 (U9 EN) must be closed, then the MCU must turn on the load switch (ACT_EN)
  and separately drive Q124's gate: two hardware FETs in series on two MCU pins, both defined off in reset. A commercial
  altimeter typically has one.
- **AGENTS §2.1 replaced:** "The external power switch is the pad arming device: the board is switched on only with the
  vehicle on the pad / rail, and the pyro channel is live whenever the board is on. Firmware never fires before it has
  detected launch (accelerometer + barometer), and on the ground continuity / bus readings are hard refusals (§2.3)."
  §2.2's "ARM plug goes in last and comes out first" becomes "the power switch is turned on last and off first".
- **Operating rules:** pad checks (GPS lock, telemetry, IMU) are done with the vehicle on the rail; bench work uses USB
  power (the pyro feed needs the pack and the load switch) or the e-match disconnected.
- **Accepted:** no physical break while the board is on; a back-feeding USB / self-powered port device with the switch
  open can keep the logic up (audit §3 item 7), so the e-match is connected only with no back-feed source attached.

### D-SS-01. Implement the two independent MCU controls in the recorded decision

Source inspection found that the former R122 / R123 divider enabled Q122 automatically from RAW_PROTECTED;
ACT_EN was not an MCU output. Merely deleting J124 would therefore not implement the decision's firing chain.
Use the previously unconnected PC1 (U1.16) as ACT_EN_MCU, through R122 (1 kΩ, 0402WGF1001TCE / C11702) to Q122's
ACT_EN gate; retain R123 (100 kΩ) to GND. Remove the RAW_PROTECTED divider feed. The separate PE4 output still
controls Q124. Both control inputs have external pull-downs and firmware initializes both low before deliberate
on-rail bus checks; only a confirmed launch permits a fire command. No firmware implementation is claimed.

Maker evidence: [ST DS12110 Rev 11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf), Figure 6 p. 55 and
Table 9 p. 67, identifies PC1 at LQFP100 pin 16 as an ordinary GPIO (also TRACED0); the existing ban on synchronous
trace therefore covers PC1 as well as PE4. [AO3400A Rev 3.1](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf),
pp. 1–2, specifies its on-resistance at 2.5 V gate drive. At the 3V3 lower corner of 3.27 V, allowing 0.4 V MCU
output drop and resistor tolerance, ACT_EN is above 2.83 V (Calc). R123 holds the gate below 0.12 V for 1 µA MCU
leakage plus the MOSFET's 0.1 µA gate-leakage limit (Calc; unpowered transient behavior remains a bench test).
PC1 is not an AN2606 Table 119 loader pin. Firmware must keep it low in loader/debug transitions and clear it
on a fault; GPIO configuration locking and read-back extend to PC1. A single shared MCU remains an accepted
single-string limitation; two controls do not establish independent software safety.

### D-SS-02. One named post-switch net and a shorter fire path

Merge the former PYRO1_BUS into RAW_ACT; do not add a net-tie component or a zero-ohm bypass. R134.2 and the bus-sense
divider R132.1 now join the Q121 drain. ARM1_SENSE signal names remain as historical identifiers for bus voltage,
not evidence of a physical ARM link. Move R134 to the bottom at (7, 64.335), rotation −90°, beside J121's through-hole
pad: the Q121 → R134 → J121 fire feed can be drawn directly on B.Cu. The separate RAW_ACT and bus dividers remain
fitted as directed. S-1 / S-2 verify the unified net and its sole supply through Q120 / Q121; S-5 checks the external
switch circuit rather than a nonexistent inter-pad ARM gap. The removed connector, fuse note and ARM legends are
rejected by the current R10 gates. All other AGENTS §2 constraints remain.

### D-SS-03. Keep required assembly references visible

The first full integration build hid Q121 / Q124 after the changed legend and part packing; K-legends correctly
rejected it. Give the existing required connector/safety designators placement priority in the R10 post generator,
including its courtyard and run-on correction pass. The generic designator helper accepts an optional priority list;
its default behavior for historical generators is unchanged. Keep the 1.0 mm text, 0.15 mm stroke, pad clearance
and nearest-subject rules. Re-pin the DRU hash only for its reviewed ARM-to-switch comment: the actual rules are
byte-unchanged. Remove J124's body/wire masses from the R10 plate profile and fix the standalone plate test's
incomplete fixture (LS120 was absent); three standalone mass-profile tests pass. No R9 profile is changed.

## AUD/GAP implementation (2026-10-28, after single-switch commit `73af96b`)

The owner-answer pass was committed by the supervisor in `6fdac43` and the single-switch pass in `73af96b`.
The earlier Git-blocked hand-off is historical. The following decisions implement the adopted audit; statements
in its original snapshot that retain J124 / an ARM fuse are superseded by the later single-switch owner decision.
This pass earns no full-review or consecutive-clean credit. All new copper is drawn explicitly by the generators.

### D-AUD-01. Size the surviving IO-LDO capacitor for its electrical load

C92 uses the existing Samsung CL10A475KO8NNNC / C19666 4.7 µF, 16 V X5R 0603 family. TPS709 requires at least
1.5 µF effective output capacitance; the maker's typical bias curve at 3.4 V, followed by tolerance, temperature
and an explicit aging allowance, gives 2.211 µF (Calc / Inference; `parts_qualification.md`). This is not a
measured worst-case capacitance guarantee; verify stability on the actual part. The deleted GPS / radio LDOs
need no output reservoirs. Sources: [TI TPS709](https://www.ti.com/lit/ds/symlink/tps709.pdf), §8.2.2, and
[Samsung part data](https://product.samsungsem.com/mlcc/CL10A475KO8NNN.do).

### D-AUD-02. Keep fast returns constrained; simplify slow returns by explicit name

One shared, explicit slow-net list covers filtered ADC sense and its divider / MCU tails, ACT_EN / ACT_EN_MCU
/ ACT_DRV / ACT_GATE, and GPS / RADIO / CAM EN / FAULT / OE controls. Only the 1.5 mm partner-via and
one-In2-region / reference checks exclude that list. The critical classification and routing-hygiene checks do
not change. USB, HSE, SPI, QSPI, IMU CS, UARTs, existing SWD / reset checks and S-8 stay blocking. Remove
partner vias and In2 arms used only by the excluded rules; keep the solid In1 GND plane. Slow-path noise and
threshold behavior remain bench checks. Every narrowed gate scope cites AUD-2; the shared executable list is
in `tools/critical_reference.py`, imported by `tools/route_check.py`.

### D-AUD-03. Use a qualified smaller post-switch pair

Select genuine AOS AONR21357 / C431196 for Q120 / Q121, preserving the back-to-back source connection and
independent PC1 enable. The maker's DFN3x3A land is used, including its asymmetric drain shape; a generic
square land or another manufacturer's same-numbered part is not substituted. Its −30 V drain and ±25 V gate
ratings cover the recorded ~18 V gate event. Its maximum 12.3 mΩ at −4.5 V / 25 °C, with the typical hot-ratio
curve, estimates about 17.2 mΩ at 125 °C (Inference), below the 40 mΩ design bound. The actual gate-drive,
SOA / load-line calculation, exact land and source notes are in `parts_qualification.md`.
Allow at least 100 ms from ACT_EN assertion to bus checks, with PE4 held low, to cover the retained slew network;
the former 50 ms delay is withdrawn. Bench-check VGS / VDS / current and heating on a shorted dummy load at 70 °C;
reference-board SOA is not proof for this PCB. Genuine JLC API identity C431196 showed 56, 301 pieces / minimum 1
on 2026-10-28; refresh before ordering. Sources: [AOS device](https://www.aosmd.com/res/datasheets/AONR21357.pdf),
pp. 1–4; [maker land](https://www.aosmd.com/sites/default/files/res/packaging_information/DFN3x3A_8L_EP1_P.pdf);
[JLC exact part](https://jlcpcb.com/partdetail/Alpha_OmegaSemicon-AONR21357/C431196).

### D-AUD-04. Delete the advisory pull-pin as a complete function

Remove J123, R160 / R161, C160 and D122; PC13 becomes NC / analog. R10 F9, FMEA F-7 and pad checklists no longer
require a pull-pin witness or annunciation. Launch detection remains accelerometer plus barometer, independent
of every port or uplink; bus / continuity ground refusals remain. The single screw switch is the pad arming device.
The removed input had no flight authority; its wiring, retention and exposed-wire fault paths disappear with it.
Historical R1–R9 analysis retains its original revision scope.

### D-AUD-05. Remove redundant probe branches

Delete TP84 / TP85 / TP86 / TP87 / TP89 / TP92 and their dedicated copper branches. TP74, TP80–83, TP88 and
TP120–122 remain; hot-plug still has separate IN / OUT access and pyro has a gate probe. The other measurements use
existing component pads. Probing is less convenient; no monitoring function or protection is removed. Probe U9
ILM only at its own pad with a high-impedance instrument; never load or short it.

### D-AUD-06. Size fire-only copper for bounded pulse energy

RAW_ACT / PYRO1_IGN / PYRO1_OUT fire runs use 0.5 mm. Continuous BAT_IN / U9 feed widths are unchanged; the
source-to-source bridge keeps its existing qualified minimum. At 4.2 A / 20 ms the no-plane adiabatic estimate
is about 5.6 K near room temperature (Calc / Inference), about 10.1 K at the 36 ms fault guard. Starting at 70
°C and allowing the low-R134 current corner raises the estimates to approximately 7 K / 13 K; no heat
spreading is credited. Final path lengths, resistance and coupled pack-load current replace the historical
ARM-link loop budget. This does not license a continuous 4.2 A load.

### D-AUD-07. Use ordinary digital pull-ups and fault-rated servo resistors

R412 / R422 / R432 remain 10 kΩ, now the existing C25744 0402 family. R150–R153 remain 1 kΩ, now C21190 0603
rated 100 mW through 70 °C. The conservative 8.4 V chafe into a 0 V output and −2 % resistor is 72 mW (Calc),
leaving about 1.39 × power-rating margin. The physical continuous-fault rating replaces the inherited blanket
rule limiting dissipation to 30 % of rating for these parts; ESD / clamp / MCU-injection functions and bench
tests remain. No 0402 servo series substitution is allowed on that budget.

### D-AUD-08. Share 3V3 for GPS / radio UART IO; retain local bypasses

Remove U412 / U422, R443 / R453 and C441 / C442 / C451 / C452. Both sides of the GPS / radio TXU0202 translators
use main 3V3. **Retain C443 / C453** as local 100 nF VCCB bypasses on 3V3: the maker requires bypassing each supply
(TI TXU0202 §12.1, Figure 12-1). This datasheet-driven refinement of AUD-8 removes eight parts, not ten.
OE pull-downs, 1 kΩ signal resistors, ESD and OE-before-EN shutdown remain. Accepted containment loss: an erroneous
OE high can feed an unpowered module a few mA through 1 kΩ; firmware must hold OE low whenever its port is off.
Main-rail-off isolation still follows TXU0202 partial-power-down behavior. Keep camera U13 because PORT_5V3's
maximum exceeds the translator's 5.5 V recommended supply limit. [TI TXU0202](https://www.ti.com/lit/ds/symlink/txu0202.pdf).

### D-AUD-09. Keep USB-only programming and log download

Retain U10 / U11 and their support. They provide a real pack-free bench function and source selection, with
host-dependent attach inrush already disclosed. No circuit or return-path assumption may silently remove that
function in the name of simplifying the board.

### D-AUD-10. Report harmless drawing artifacts without blocking the electrical gate

For R10 only, exact collinear nodes, exact duplicate segments, inside-pad segments and legend-subject
distances over 6 mm are counted for review. Partial overlaps, crossings without nodes, connectivity, DRC,
required / correct legends, 1.0 mm text / 0.15 mm strokes, mask clearance and fast-return checks remain
blocking. Every counted residual and its measured reason belongs in the final deviation list. Keep the goal of
clean routes; this is not permission to add unnecessary copper. Use the freed LDO space for J410 / J420 pin
tables where a clear legal spot exists.

### D-GAP-01. Superpose all pack loads at the fire instant

Use the final board resistance, hot FET allowance and actual harness with I_fire = (Voc − Rpack × I_other) /
(Rpack + R_fire). Include logic and port power as well as servo stalls; constant-power converter demand
increases as the pack sags. A neutral PWM command cannot unload a jam. Preserve the original F7 idle-servo ≥
1.5 × 1 A all-fire criterion at 7.4 V, with that voltage available at the fire instant after pad / flight
drain. Two simultaneous stalls with all ports on do not meet it; do not claim that the 200 ms neutral wait
proves they have cleared. Derived limits on e-match all-fire current or a higher pack voltage are conditional
acceptance envelopes, not adoption of an unselected igniter. `parts_budget.json ` holds the calculation; final
copper numbers and first-article harness / source-impedance measurements are required before flight.

### D-GAP-02. Make U9's output-protection loop local

Move existing C82 and D9 beside U9 OUT on B.Cu; move R92 to C82's old vacant area. Draw short OUT and local GND
connections and measure the actual copper paths, not just part-center distance. Keep the C88-before-IN feed and
continuous current widths unchanged. [TI TPS25947](https://www.ti.com/lit/ds/symlink/tps25947.pdf), §8.4.1,
requires an output capacitor and a local Schottky for fast input collapse; final loop measurements and detour /
missing-return seeds are recorded with the build evidence.

### D-GAP-03. Add two explicitly manufactured U401 thermal vias

Use only two GND vias with a 0.5 mm ring and 0.3 mm drill inside U401 pad 11, at (27.3, 13.6) and (27.9, 13.6).
Require **resin filling, copper capping and planarization (VIPPO)** at these two vias before assembly; mask / plug
ink is not an equivalent. Preserve TI's split paste windows and the ordinary drill / pad-clearance rules elsewhere.
The gate exception requires exact count, position, size, GND net and containment in U401.11; manufacturing quality
is an order / first-article condition, not something a CAD check proves. Keep the conservative 80–110 °C/W estimate
as an Inference: at 0.406 W and 70 °C bay ambient it predicts 102.5–114.7 °C, below 125 °C. The added vias improve
the heat path but do not prove a particular thetaJA. Measure full-load temperatures before flight; include VIPPO in
the quote rather than hiding its cost. [TI TPS7A91](https://www.ti.com/lit/ds/symlink/tps7a91.pdf), thermal / layout guidance.

### D-GAP-04. Fit C84 after all reflow

C84 is the JIERRUI MA25V470M8x10 / C46550466, not the former Panasonic OS-CON. Its supplier sheet gives no
reflow profile. Keep it listed as required and fitted in BOM / CPL, but instruct the assembler to fit it manually **after both
reflow passes** using a validated local soldering process; confirm this separate operation before placing the
order. Do not infer a 250 °C condition-C qualification or an iron temperature from another capacitor family.
Check polarity, seating / height, capacitance and ESR before and after first-article soldering; record the process
and reject damage or drift outside the maker's electrical limits. This is the hand-solder instruction allowed by
GAP-4, with process qualification remaining explicit. [Exact supplier sheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf).

### D-GAP-05. One physical-current duration contract

Normal commanded firing current must end within **20 ms**, including gate turn-off tail. A timer / DMA clear and
independent abort reserve that tail; the older 25 / 30 ms software backstops do not define the R10 normal pulse.
Use IWDG prescaler ÷ 4 / reload 239: **960 LSI cycles, nominal 30 ms**. DS12110 Rev 11 Table 136 gives Rev V LSI
29.4–33.6 kHz through 125 °C junction, hence 28.571–32.653 ms (Calc); the earlier 29.76 kHz floor does not cover
that entire temperature range. Identify and qualify the fitted silicon revision and its applicable LSI limits.
Refresh immediately before PE4 rises, then **do not refresh throughout firing**. After physical current ends,
complete a valid SAFETY pass and refresh within 5 ms: 20 + 5 ms is below the fastest watchdog expiry.

The fault bound allocates 0.2 ms prefire / synchronization, 0.5 ms reset-to-GPIO-high-impedance and 1.5 ms physical
turn-off tail: 32.653 + 0.2 + 0.5 + 1.5 = 34.853 ms, guarded to **36 ms** with intact gate / watchdog hardware.
A failed-short FET is outside this timed cutoff claim. With MCU floating, 10 kΩ || (220 Ω + 1 kΩ) = 1.087 kΩ;
C126 is 220 nF, not the old 10 nF. Nominal 3.3 → 0.4 V discharge is about 0.50 ms. Tolerance / temperature and a
conservative gate-charge allowance still estimate about 1.01 ms to 0.2 V (Calc / Inference); actual current tail
must be measured ≤ 1.5 ms, including hot behavior. These are firmware / bench obligations, not implemented firmware.

At 70 °C, R134's −1 % / adverse 100 ppm corner is 1.97109 Ω. Ignoring all other resistance at 8.4 V gives 4.262 A,
35.80 W and 0.716 J at 20 ms / 1.289 J at 36 ms (Calc, conservative). Bourns CRM2512's ≥ 1 Ω single-pulse curve
is about 61 W / 44 W at those times by log interpolation (Inference from the graph), approximately 1.7 × / 1.23 ×
the estimated stress. The 85 °C sensitivity has almost no margin after inferred thermal derating; do not qualify
that as the bay design point. No repeated pulse / automatic retry is authorized by a single-pulse graph. On the bench,
qualify hot dummy-load pulses, hang / reset timing and resistance drift. [ST DS12110](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf),
Table 136; [Bourns CRM](https://www.bourns.com/docs/product-datasheets/CRM.pdf), p. 3. The neutral-command allocation
is ≤ 32.653 ms watchdog + ≤ 6 ms reset release + ≤ 10 ms startup = ≤ 48.653 ms (Inference), inside the 50 ms target;
physical tab motion or a jam remains a servo / hinge-load measurement.

### D-AUD-03a. Correct the retained gate-slew capacitor's voltage rating

Replace C120's 2.2 µF / 16 V part with the existing Samsung CL10B105KA8NNNC / C29936, 1 µF / 25 V X7R 0603
family (already C86 / C97 / C98). No new code or fitted component is added; D-AUD-01a corrects the initial
unchanged-land choice to the existing C29936 land for assembly consistency.
The old 16 V rating did not cover the recorded ~18 V clamp event. Maker bias data plus explicit tolerance,
temperature and aging allowances estimate at least 0.588 µF over the 0–4.5 V turn-on interval (Inference);
2 × 70 nC total gate charge divided by this gives about 0.238 V as a conservative transient bound (Calc /
Inference, not a measured Miller waveform). The maximum capacitance / resistor corner gives about 11.73 ms
turn-on RC and reaches 4.5 V within about 23.7 ms at the stated minimum drive. Keep the ≥ 100 ms bus-check
settling delay. The faster slew improves the limited-load SOA calculation; verify hot shorted-dummy turn-on,
Miller / reset / off behavior and the independent Q124 pulse cutoff on the bench. [Samsung maker data](https://product.samsungsem.com/mlcc/CL10B105KA8NNN.do).

### D-AUD-03b. Verify new assembly orientation against the supplier

Fetch only C431196's official supplier pad map into `tools/jlc_easyeda/pads.json `; retain its retrieval date and
source URL. Geometry source: **JLCEDA/EasyEDA Official Library**, [JLCEDA](https://lceda.cn/) /
[EasyEDA](https://easyeda.com), exact-part API linked in that record. The PCB land remains the AOS maker land;
this independent supplier map serves placement orientation and CPL verification. No account / owner metadata is
copied into the repository. Confirm physical pad polarity and both FET bodies in the factory preview before order.

### D-SS-04. Recalculate passive cold readings before enabling the merged bus

With PC1 low / both gates off, the merged RAW_ACT bus adds the second 11.2 kΩ sense-divider load to the cold
network. The nominal 3.1 V diode-side source gives healthy ADC readings about 75.27 mV CONT / 75.22 mV ARM and
RAW, open e-match CONT about 146.23 mV with the RAW readings near 0, and grounded-drain readings near 0 (Calc
/ Inference; tolerance, diode and leakage assumptions in `parts_qualification.md`). The old plug-out bands of
approximately 100 mV do not transfer. For a previously enabled bus, wait at least 1 s with PC1 low and observe
that it has discharged before classifying the passive readings; then wait ≥ 100 ms after deliberate ACT_EN
assertion before bus checks, with PE4 still low. Cold screening precedes enabling the load switch, especially
for a failed-short low-side FET. Bench qualification must establish actual bands / noise / leakage before an
e-match is connected. This ground diagnostic never vetoes an in-flight fire (AGENTS §2.3).

### D-GAP-01a. Final track-based conservative fire envelope

The AUD geometry has 19.304478 mm of 0.5 mm fire-only track, 7.121320 mm of 1.0 mm battery branch and a
conservative single 2.2 mm / 0.4 mm source-bridge path (no parallel credit). At 1.72 × 10⁻⁸ Ω·m / 35 µm copper
this is 25.1760 mΩ at 20 °C, 30.1231 mΩ at 70 °C (Calc / Inference). Add R134 at 2.02909 Ω (hot, upper
tolerance), two 40 mΩ high-side FET ceilings, Q124 at 8.236 mΩ (hot, Inference), 5 mΩ GND and 10 mΩ contact
allowances, 2 Ω e-match, 0.3 Ω leads and 0.15 Ω pack: loop 4.612449 Ω. With 11.545807 W of other normal loads
and pack sag solved consistently, 7.4 V gives 1.550071 A idle, 1.485263 A with one persistent 1.92 A stall,
1.420229 A with two, 1.354934 A with three and 1.289335 A with four. Thus even one persistent stall misses the
conservative 1.5 A margin; the original idle-servo F7 case passes. No assertion that a neutral command clears
a jam is retained. A two-stall envelope would require an all-fire current ≤ 0.946819 A or Voc-equivalent ≥
7.753406 V at fire, with the same harness / source limits; these are derived conditions, not adoption of a new
igniter. The secondary typical-hot FET calculation is not the acceptance basis. Verify these premises against
final saved-board geometry and first-article harness / source / copper temperature measurements.

### D-GAP-02a. Reject the nearer diode position on measured clearance

The candidate D9 B (43.35, 77.0), rotation 90°, would put its RAW pad box at x 42.45–44.25, y 77.75–80.25, overlapping
C81.2 GND at x 42.4–43.35, y 77.65–78.55. Moving east clears that pad only by routing around the DVDT / GND cell.
Retain the noncolliding diode position and simplify its OUT branch through the C82 RAW node. Per-part OUT /
GND / total-loop and detour bounds are engineering regression limits for this cell, explicitly separate from
TI's qualitative short-loop guidance; saved-copper measurements and loop-area evidence accompany the build.

### D-AUD-03c. Match orientation by distinct fingers, not an arbitrary EP anchor

The first C431196 dry run rejected a 0.398 mm nine-pad residual: the custom EP9 anchor is (0, 0), whereas the
supplier's polygon anchor is (0, −0.35001) mm. These are reference points within unlike representations of the
same drain land, not package origins. Compare all eight distinct fingers 1–8 for this footprint only, and fix
its body-origin offset at (0, 0). Maker / supplier source-row centers are y 1.4 / 1.50012 mm (0.10012 mm difference),
drain-row centers −1.495 / −1.50012 mm (0.00512 mm); both origins are package-centered. The eight-finger fit gives
unique theta 0° (best residual 0.053 mm / next rotation 2.52 mm); with the fixed body origin, the largest actual
finger-center delta is 0.10012 mm, inside the unchanged 0.35 mm limit. The part-specific rule preserves the maker
land and does not widen general tolerances. Full CPL verification and the factory preview remain required.

The orientation tool now recomputes its residual after a fixed-origin override instead of reporting the discarded
auto-fit's residual. C431196 reports 0.100 mm at theta 0°, offset (0, 0), with CHECK: none and unchanged general
limits. The official body rectangle and 3D origin coincide with its declared package head; all eight actual
finger residuals are independently checked. The final exported CPL remains a separate check.

### D-GAP-02b. Freeze the actual output and return paths

C82 is B (39.8, 74.75), rotation 90°, with its GND via at (39.8, 74.35); D9 is B (43.35, 73.45), rotation 90°,
and R92 is F (33.9, 65.775), rotation 90°. Saved copper gives C82 OUT 3.390990 mm B.Cu plus GND 9.177817 mm
B.Cu / In1, total 12.568808 mm (the return includes two conservative full 1.6 mm via penalties), projected
loop area 2.3153 mm². D9 has OUT 6.873402 mm B.Cu plus GND 9.818377 mm all B.Cu, total 16.691778 mm, projected
area 17.4197 mm². OUT ratios to pad-center octilinear distance are 0.948 × / 1.175 ×; the cap path terminates
inside its pad, explaining the ratio below 1. The local regression limits are C82 OUT / GND / total ≤ 4 / 10 /
13.5 mm, D9 ≤ 7 / 10.5 / 17 mm, and OUT detour ≤ 1.25 ×. These are measured-layout engineering bounds, not
maker numerical limits, inductance estimates or physical transient qualification. Missing-return and detour
seeds fail. The continuous J1 → C88 → U9 input feed is unchanged; the local output-entry neck is 1.414 mm of
0.7 mm copper before the four 0.5 / 0.3 mm rail vias.

### D-AUD-01a. Keep one assembly land per supplier code

FAB rejected C19666 on both `rocket:C0603` and `rocket:C_0603_1608Metric`. Use `rocket:C0603` for C92,
matching existing C23 / C28. The same inventory check exposed C120 / C29936 on `rocket:C0603` while existing
C86 / C97 / C98 use `rocket:C_0603_1608Metric`; give C120 that established metric land. Values, maker identities
and nets are unchanged. Keep the exporter's one-footprint-per-LCSC-code requirement unchanged.

Local library measurements: C0603 has pad centres x ±0.700 mm, 0.80 × 0.90 mm rectangular pads and a
2.70 × 1.40 mm courtyard; the metric land has centres x ±0.775 mm, 0.90 × 0.95 mm roundrect pads and a
2.96 × 1.46 mm courtyard. At unchanged C92 B (34.2, 45.2), −90°, its pads move 0.075 mm inward to
(34.2, 44.500) / (34.2, 45.900); adapt the three local routing corners. Move C120 0.075 mm north to
B (17.1, 71.525), −90°: metric pad 2 remains on ACT_GATE at (17.1, 72.300), while pad 1 becomes
(17.1, 70.750). Recheck local clearances and the source tap after regeneration. R150–R153 / C21190 already
share `rocket:R_0603_1608Metric` with their retained counterparts, and R412 / R422 / R432 / C25744 share
`rocket:R0402`. These land corrections do not change capacitance, gate timing or bench obligations.

The schematic preflight now checks the same per-supplier-code footprint / part-number grouping as the exporter,
separately for JLC and owner BOMs. A matching wrong schematic/source land must still fail this independent
assembly-group rule. Both split-land seeds are detected; the total is 22 seeded contract faults. The exporter
remains unchanged. This integration correction precedes the fresh full review round 9.

## Round 9 (full review of `877d0199…`, commit `8bccb07`)

Ten fresh validator contexts reviewed the committed board in parallel batches of up to three. Result after
deduplication: **0 Critical, 0 Major, 21 Minor groups: 17 new and four carried routing groups**. The incomplete
owner-decision prelude is not a full round. Its existing R9-PWR-01 identifier remains historical; this round's
TPS2553 finding is R9-PWR-02. No Critical or Major finding required acceptance or an owner choice.

### D-R9-01. Complete existing capacitor labels and use the current fault-delay bound

R9-BOM-01: expand the seven abbreviated Value strings on 21 retained capacitors using the existing exact
manufacturer identities. A small `value_overrides` source map changes labels only, preserving symbols,
footprints, nets and supplier codes. The qualification record lists the seven original-maker / supplier sources;
the schematic contract checks the expanded labels. Update the exact C60 loader-member and C88 hot-plug component
labels too, retaining their original part codes, capacitances and net roles. The first integration build's 2304
numerical corners passed but its component check rejected the old C88 label contract; that attempt is not a
passing build. Complete passing replays follow the correction. No capacitor substitution or inferred rating is introduced.

R9-PWR-02: TI SLVS841G p7 specifies overcurrent FAULT deglitch 3 / 7.5 / 11 ms. Budget 11 ms plus firmware latency
and actual current decay; this is not the PA6 battery-break detector. The maker's live PDF retrieved 2026-10-28 is
Rev G, SHA-256 `d30a12e7b91a23f82b4fdf0d1d00c891534486da9e19ac2c22c42143d4d3d1c0`; a web-indexed copy still
returned Rev F. Reverse-voltage FAULT deglitch (2 / 4 / 7 ms) and MOSFET turn-off (3 / 5 / 7 ms) are distinct.
No current-limit, rail or hold-up credit changes.

### D-R9-02. Put the cold screen before enabling the bus

R9-SAF-01: propagate D-SS-04 into the schematic note, generated firmware obligations, M3_R10 and ORDERING. PC1
and PE4 stay low for the passive cold screen; after prior enable, wait at least one second and verify discharge.
Ground faults refuse enable before PC1 rises. Only then may PC1 go high, with PE4 low for at least 100 ms before
powered-bus checks. A shorted Q124 can otherwise complete the firing circuit at enable before the later check.
The hardware supports the correct order; firmware and threshold qualification remain absent. In-flight sensing
never vetoes recovery.

The first complete gate attempt after the label correction caught an old literal-string assertion in the
binding-note test. Replace it with checks for both-low screening, the discharge wait, pre-enable refusal and
the later powered check. This failed attempt receives no passing-build credit; complete replays follow.

R9-MCU-01 / R9-DOC-01: both PC1 and PE4 require their respective GPIO locks and LCKK / pin-bit readback. The
dummy-load trace experiment uses an STM32H743-capable debugger's supported synchronous ETM setup, real
DBGMCU_CR bit20 / PE2 AF0, observed TRACECLK and retained low-output modes / locks. A missing clock or lost lock
invalidates the test. RM0433 Rev8 pp543 / 3209 and ST's H743 CMSIS header replace the other-family TRACE_IOEN
instruction. No actual override behavior is claimed. FMEA's R10 row now agrees with the binding.

### D-R9-03. Reject unmeasured gate exceptions and select R10 procurement explicitly

R9-GATE-01: reject unknown, mixed-invalid and explicitly empty rule selections before CAD context construction.
R9-GATE-02: require J410 / J420 / J122 pin tables and `SERVO + FROM HARNESS` in the final checker, including
missing, duplicate and conflicting text. AUD-10 relaxes distance only.

R9-GATE-03: remove R10's generic pad-neck width exemption. AONR21357 EP9's 0.43 mm anchor is not its
3.21 × 1.98 mm copper land; it previously let entire 0.43 mm RAW_ACT / BAT_IN tracks pass. The actual board
passes without that heuristic. Keep only the seven exact, measured source-bridge exceptions; their coordinates,
widths and lengths remain held. Both whole-track seeds and changes to any source leg must fail.

R9-PROC-01: use explicit `--profile r10` with the existing $84.41 / 52 limits in R10 fabrication and procurement.
The shared tool's default remains R9's $126.41 / 52. A genuine under-budget R10 report must pass its own profile,
while a forged R9 target or an over-budget R10 report fails. The new procurement regression suite runs in
`check.sh`, with its failure propagation covered. Real cost / stock misses remain disclosed; no target is relaxed.

### D-R9-04. Remove demonstrated detours and align three supply entries

R9-RTE-01 / -02 / -03: shorten BAT_SW_SOURCE, NRST and USB_FAULT_N by 0.692893 / 0.347651 / 0.597056 mm,
respectively, using the review's fixed octilinear vertices. Each redraw and their combined temporary board pass
all-severity DRC, reference and region checks; the combined route scan has no local-bump candidate. No via is added.

R9-RTE-05: align U411.7 / U421.7 and their main-3V3 vias at x35.45 instead of x35.50. Align U10.1's VBUS branch
at x11.30, ending on its pad centre and teeing into the retained horizontal trunk. The combined temporary board
with these changes and all three detours has zero DRC / unconnected / reference / region / routing failures.
The old IO-via/OE-reference blocker is superseded by AUD-2; it is not used to justify keeping an offset.

Retain SPI1_MOSI's 0.05 mm offset at U4.14: the tested on-axis via (17.50,44.30) enters IMU_body_B and loses
11 adjacent reference samples on SPI1_SCK, while invalidating two existing MISO stray entries. This attempt is
rejected, not counted as a passing alternative. Moving the MEMS or adjoining SPI lanes is a broader change.
Current noncritical return distances, slow split crossings, necessary hops, between-pad routes and the remaining
BUZZ_DRV / NRST crystal projections stay measured review deviations, not unqualified claims of impossibility.

### D-R9-05. Include both transverse sled tolerances

R9-MEC-01: add the missing 0.3 mm vertical centring tolerance to the nut / screw calculation. Under the stated
6.35 mm across-corners, 2.4 mm nut and 0.4 mm protrusion assumptions, h+t is bounded by 6.018413 mm at x4 / 42
and 5.365256 mm at x3.7. Use conservative <6.0 / <5.3 mm bounds. Select measured 4.0 mm standoffs and a plate
at most 1.0 mm thick as the starting hardware stack. Substitute actual hardware maxima, hole / screw eccentricity
and tolerances before physical release; no unmeasured nylon hardware or sled strength is qualified by this choice.
R9-REQ-03 / -04 and R9-DOC-02 / -03 correct current pin / connector, cost, crystal-neighbour and AUD-2-scope records.

The native fix-board inventory also closes the previously unmeasured surface-track list under nominal 3.5 mm
washer discs: at (4,44.3), 3V3 F.Cu / its ordinary via have minimum copper radii 3.4104 / 3.2604 mm and NRST F.Cu
3.4214 mm; at (42,86), BAT_IN B.Cu reaches 2.7500 mm. The other three supports have no non-GND surface track / via
inside that disc. Required ordinary via covering, nylon hardware and insulation under the whole bottom face
remain mandatory; this list does not qualify hardware eccentricity, mask wear or physical contact.

### D-R9-06. Cover the Minor fix pass in the fresh round 10

The label and local routing fixes change the CAD bytes. The owner’s continuation explicitly counts clean
rounds 9 and 10 as the required pair if round 10 has no confirmed Critical or Major. Round 10 must therefore
review the committed fix-pass bytes, including every changed route, label, gate and obligation; the older
proposal for two additional rounds is superseded. Rebuild twice, prove byte equality, export the fabrication
package and run the unskipped gate before the supervisor commit. Freeze the PCB after round 10; any later
board change needs explicit review coverage or another full round. Software / CAD / simulation evidence
remains separate from firmware, bench, RF immunity and physical fit.

One reviewer performed an out-of-scope read-only legacy check in the R9 worktree. No files changed there; that
run is excluded from evidence and further access is prohibited. Legacy checks use only this worktree's pinned
R9 snapshot. Computer Use rejected both KiCad and PCB Editor launch, so native geometry and rendered CAD supplied
visual evidence; no alternate GUI-control mechanism bypassed the rejection.


Round-9 fix completion: two full builds reproduce all 21 CAD / binding files on `b337fe63…` (46 × 90 mm,
2,366,509 bytes); the final unskipped gate exits 0, all 33 rules / self-tests and current fab manifest pass.
The 2304-case model passes as simulation / Inference. Fab export/orientation/paste pass; live supplier
23:24–23:25Z evidence still fails at $84.43 vs $84.41, R430 / U4 short. The restart used D-R1-05’s external
headless mouse-query interposer; no repository dependency or CAD/gate relaxation. Evidence:
`../r10_review/round9_fix_validation.json `, `../r10_review/round9_fix_check.txt` and `../r10_review/round9_geometry.json `.
Round 10 covers this low-risk Minor fix pass in the required clean pair; physical / firmware limits remain open.

### D-R10-01. Close two representation gaps without changing CAD

Round 10's fresh gate adversary found two Minor omissions; neither is present in the reviewed PCB. A conflicting
PCB_TEXTBOX port table passes the old K-legends, and an In2 graphic 0.500 mm from J121.1's barrel passes the old S-8
and refilled all-severity DRC. Include text boxes in port / harness-table checks and use the existing complete
copper_nodes geometry for S-8, covering drawings, text, fields and footprint zones as well as routed copper.
Preserve GND / own-net exceptions and the 1.0 mm limit. Add native board / footprint graphics and text seeds plus
conflicting / duplicate text-box tables and harness notes. These are coverage fixes, not new clearance allowances.
The unchanged baseline passes; both demonstrated faults must fail. AUD-2 / AUD-10 / GAP-3 scopes and AGENTS §2 stay.

### D-R10-02. Correct PA6 limits and preserve the barometer coating exclusion

R10-MCU-01: ST DS12110 Rev11 Table109 pp207–208 notes3–5 limits FT_a used by the ADC to 4 V; digital FT VIN is at most
min(min(relevant supplies)+4 V,6 V), or 6 V with powered 3.3 V supplies, with pulls disabled above 4 V. Positive
injection allowance is 0 mA. Correct the generator, regenerate its evidence note and qualify historical 7.3 V
claims; the normal divider and existing single-fault pin-damage conclusion do not change. No hardware mitigation
is inferred from firmware. Source: https://www.st.com/resource/en/datasheet/stm32h743vi.pdf.

R10-MEC-01 / independently reproduced R10-MFG-01: the whole-coat instruction for non-pyro C11 conflicts with the
project's ≥3 mm U5 body-and-pad exclusion. Native C11.1 to nominal maker body is 2.818449 mm; 3.027515 mm was to
pads only. Mask C11 whole, retaining whole-U5 tape, R13 / R64 masks and the controlled TP122 exception. Use the union
of body and pads, not the old pad-only rectangle. Next coated C10 conservative Fab/pad envelope clears 3.333144 mm;
others ≥5.075 mm. Actual fitted tolerances and coating placement still require qualification. This preserves the
sensor rule with no PCB move. TE maker body / handling: 06/2017 pp1/15/17, linked in ORDERING §8 and round-10 review.

### D-R10-03. Freeze the reviewed board and finish the complete acceptance inventory

Ten independent round-10 lenses reviewed committed `619db7e`, PCB `b337fe63…`, finding 0 Critical, 0 Major and
8 Minor groups (4 new, 4 re-raised routing groups; manufacturing coating duplicate counted once). The previously
recorded architecture / qualification / procurement deviations remain in the inventory, not new discoveries.
Clean rounds 9 and 10 meet the owner's explicit consecutive-pair rule; no later PCB change is made. Final narrow
gate/regression and record/generator-text fixes preserve every land, pose, part, net and copper / silk byte.
Rebuild and verify the regenerated PA6 obligation, current bindings, unchanged PCB and final unskipped gate.

Retain the measured routing / land compromises with their reasons. In particular the L400 proxy land differs
from Bourns' recommendation: native 1.8 ×2.5 mm at ±2.35 versus maker 2.0 ×1.8 at ±2.25 mm; nominal contact coverage
is not worst-tolerance qualification. Correcting it now requires a separately covered CAD revision or actual
assembly qualification; do not describe factory preview as an assembled result. Do not use the approximately
$0.3184 C29936→C15849 saving: X7R→X5R effective capacitance / temperature / gate-slew behavior is unqualified.
Correctness takes priority over closing the $0.02 miss with an unqualified substitution.

The completed final list in R10_VALIDATION is current-board-bound and reconciles all 229 historical review rows,
all 93 prior agent decisions plus these three, remaining Minors, O1–O6, OQ answers and the narrow AUD/GAP changes.
OQ-3 remains $84.43 vs $84.41, R430 / U4 short; owner acceptance is pending. Nothing is ordered. Software / CAD,
simulation / Inference and physical / firmware evidence remain distinct. No change to AGENTS §2. Computer Use
approval review rejected Preview launch without a further reason; native geometry and generated renders supplied
visual evidence without bypassing GUI control approval. No push, other-worktree edit or Git index mutation.

## AVA layout comparison follow-up (owner decision, 2026-10-28)

A read-only part-by-part comparison with BPS.space AVA (gpt-6-astra, 2026-10-28) found that AVA has a bridging ARM
terminal beside its power switch (Joe Barnard, "The AVA Flight Computer", 2:07 and 3:15), correcting the earlier
inference that AVA arms by its power switch alone. The owner keeps the single screw switch anyway ("Keep one switch"):
commercial altimeters arm by one switch, and R10 still needs two MCU-driven FETs in series to fire.
- **Duplicate bus sense removed:** with J124 gone, RAW_ACT_SENSE and ARM1_SENSE divide the same RAW_ACT node; keep one
  six-part chain (the one whose ADC pin and binding are simpler), delete the other, and update the sense contract, ground
  refusals and firmware binding to the one reading. Continuity sense (PYRO1_CONT) and its single-fault ratios stay.
- **Layout changes adopted** (comparison §6, ranks 1-10): compact the battery / protection cell at J1; make the three
  port cells local and identical in pattern; repeated compact sense-divider cells near their ADC pins; buzzer cell next
  to its MCU pin; remove obsolete In2 notches; align ordinary bottom R / C in rows; re-escape flash / translator nets to
  drop two-via hops; full pin tables beside connectors; GND stitching grouped per cell; probe pads beside their
  subjects. Not adopted: a 45 deg U1, microSD, or any deletion of C84 / U10 / U11 / U401 / UART isolation / R134.

## Always-on ports and a microSD slot (owner decisions, 2026-10-28)

- **Port switches and GPS / radio translators removed** (owner: "Yes, cut them"; revises O5's "each port with its own
  switch"). U410 / U420 / U402 (TPS2553) and the GPS / radio TXU0202 cells (U411 / U421 and their support) go; the GPS
  and radio UARTs reach the MCU through the kept 1 kOhm series resistors and ESD, ports powered whenever the board is
  on, as AVA (Inference). Physics: a shorted port cable is already limited by the port LDO / buck current limits; the
  switches could not shed load inside the 0.55-1.0 ms ports-on hold-up (TPS2553 turn-off up to 3 ms), so F6's
  ports-on ride-through is unchanged and the firmware shedding requirement drops the port switches. Accepted: no
  firmware power-cycle of a hung GPS / radio (reset by the board's power switch); a self-powered GPS / radio can
  back-feed a powered-off MCU pin through 1 kOhm (limited to a few mA; ground rule: no self-powered module on the
  ports with the board off). **The camera keeps its isolation (U12 / U13) and its switch** if removing the switch would
  let a self-powered camera back-feed CAM_5V into the board (F9 back-feed); otherwise apply the same cut and record why.
- **microSD slot added alongside the QSPI flash:** QSPI stays the crash-safe primary log; the card is the large,
  removable log. SPI mode on SPI3 (PC10 SCK, PC11 MISO, PC12 MOSI, a free GPIO CS; all NC today), or 4-bit SDMMC1 if
  VBUS_SENSE moves off PC8 cleanly; on 3V3 with local bypass and pull-ups per the SD physical layer spec. The socket
  must retain the card under the flight's shock and vibration: hinged or push-pull, not push-push, JLC-stocked; card
  insertion reachable with the board out of the bay.

## Connectors: screw terminals for every wired connection (owner decision, 2026-10-28)

Owner: "actually can we do screw terminals for the servos?" (after the comparison of pin header, JST GH and DB125).
- **Servos:** J122's 3 x 4 pin header is replaced by one 5-position DORABO DB125 3.5 mm screw terminal: SERVO1-4 signal
  plus one shared GND (servo power and return stay on the harness, O3 / O6). Keep the 1 kOhm series resistors,
  pull-downs and the SRV05-4 clamp at the terminal. Use a colour other than the battery's green and the igniter's black
  if JLC stocks one (otherwise the 5-position body and the SERVO / pin legends tell it apart, F8). Physics: a clamped
  wire cannot vibrate off under boost (a friction-fit servo plug can, freezing the tab); every servo lead is reworked
  anyway because the board's + pin was dead. Cost ~+60 mm2 over the header (Inference). The servo-plug tie holes
  become unnecessary: remove them if nothing else uses them.
- **Power / arm switch J400:** JST GH-2 -> a 2-position DB125 (the J1 / J121 body; colour per F8 legends). Physics: the
  loop carries ~7 uA, below tin GH contacts' reliable wetting current (Inference); a screw clamp's contact force is
  better for a dry circuit, and the GH-2 part code goes away.
- Result: DB125 screw terminals for the battery, igniter, switch and servos (as AVA's power / pyro rows); JST GH-4 only
  for the three ports; plus USB-C and the microSD socket.

### Connector amendment and circuit-only hand-off (Steer 1, 2026-10-28)

Owner: "switch everything to screw terminals". J410, J420 and J9 also become 4-position DORABO DB125 3.5 mm
terminals. Preserve the existing pin convention: supply, GND, TX, RX on GPS/radio; supply, GND, RX, TX on camera.
Every position is labelled, with unmistakable supply/GND legends because physical keying is lost. DB125 accepts
28–16 AWG: port leads must be at least 28 AWG at the clamp, with suitable ferrules or splices for thinner module leads.
The servo and switch changes above stand. USB-C and the hinged microSD socket are the remaining connector types.

The supervisor assigns re-placement, the AVA-layout pass and subsequent full review rounds to a separate layout
agent. This pass finishes the circuit, contracts, firmware evidence and records; makes only the placement/routing
changes needed for a complete connected DRC-clean board; proves reproducibility and check.sh zero; requests a
supervisor commit; then stops with a layout hand-over. Rounds 9/10 remain evidence of the previous board only.
Exploratory unqualified AVA sense/buzzer moves are withdrawn from production source; the duplicate sense chain
is still deleted as directed. The original battery cell is retained for this circuit-only pass unless a required
connector interferes with it. Any subsequent battery move requires a fresh actual-feed hot-plug qualification.


## Requirements audit 2 (owner direction, 2026-10-28)

Owner direction: keep only what physics or the project needs; relax oversized margins to the physics value and
remove redundancy. Supervisor Steer 2 adopts audit items 1–13 and 15, and item 16 only after the installed opaque
U5 cover passes its light check. Item 14 retains check.sh zero before every commit; the PR carries a concise
summary/evidence link, STATUS changes once per reviewed change, and an electrical/axis firmware review is required
when those facts change. Cosmetic board changes still require refreshed reviewed hash provenance. AGENTS §2 is unchanged.

| Item | Applied scope and measured basis (Calc / Inference unless maker-cited) |
|---|---|
| 1 | Delete R177/R124/R125/R182/R172/C122 and PB0 bus input. ARM1_SENSE PC5 is the sole RAW_ACT bank; PC0 continuity remains. Saves 0.75 mA / 6.30 mW at 8.4 V. |
| 2 | Delete R168/R170 and their separate ADC-tail nets. Keep two 5.1 kΩ tops, two parallel 2 kΩ bottoms and each 10 nF filter. At the 19.9 V clamp, one top-short or bottom-open gives ≤3.342171 V versus the 4.0 V analog absolute maximum (ST DS12110 tables 109–110). Double-fault MCU damage remains possible; no double-fault current guarantee. Local source 910.714 Ω, nominal RC 9.107 µs. |
| 3 | ACT_FET_S fire-current floor 0.5 mm, retaining the seven qualified 0.4 mm source-pin bridges. At 4.262 A / 36 ms, 35 µm hot copper rises about 13.04 K; 28 µm sensitivity 20.61 K within the 25 K pulse allocation. BAT_IN remains ≥1 mm. |
| 4 | Only resistor dead-end taps R80.1/R82.1/R167.1/R92.1 to first junction may use 0.15 mm without a length cap. At rounded 10 mA, a 10 mm / 35 µm / 70 °C tap loses 0.393 mV / 3.93 µW. No load feed is exempt. |
| 5 | In1 may contain GND tracks joined to its plane; no foreign-net tracks. Reference continuity and actual fill gates remain. |
| 6 | Delete the inherited 209 Hz release floor and mandatory/stale plate-report failures. The optional plate calculation is not vibration qualification. Five supports, actual fit, retention/staking and physical assembly checks remain. |
| 7 | Count and locate noncritical routing leftovers once in final review; per-instance measured paperwork and stale coordinates do not block. Actual routing rules, critical exceptions, their measured validation and AUD-10 scopes remain. |
| 8 | NRST leakage ≥250 kΩ, powered reading ≥0.90×3V3 using a 10 MΩ meter, after coating and before each flight. Worst 50 kΩ pull-up needs 116.7 kΩ for guaranteed 0.7×VDD; the meter criterion implies ≥277.5 kΩ even with 30 kΩ pull-up. |
| 9 | Remove the independent ≤52 Extended-code cap for R10. Actual count remains informational; $84.41/board, quote, stock and pre-order checks remain. |
| 10 | Remove duplicate population, bare-contact and standalone actuator walks; retain native fitted population plus schematic/BOM/CPL checks, full KiCad DRC's J2/TP rules and K-actuators. Standalone check_r10 does not certify the DRC contact clearances. |
| 11 | The reviewed r10_net column in pin_table.tsv is the sole complete MCU map; bootloader, connector, control-role and binding checks remain separate. |
| 12 | Remove only the redundant 13 mm IMU-offset ceiling; actual −6.0±0.05 mm and pin-1/axis binding remain. At 4000°/s the current 6 mm offset adds 2.98 g centripetal acceleration. |
| 13 | Local overrides are legal only at/above the applicable clearance: J2 0.508 mm, TP footprints 1.0 mm, ordinary pads/footprints 0.15 mm. Actual DRC remains. |
| 15 | Always-on GPS/radio have no EN/FAULT/OE/isolation or shedding promises. Camera retains U402/U12/U13 because the reverse path would otherwise back-feed. QSPI stays; whole-flight storage is shared with microSD and verified by actual latency/power-loss tests. |
| 16 | LEDs may remain active in flight only after the installed opaque U5 cover passes LED-toggle/ambient-light testing during barometer checkout. No assembly exists to verify here, so retain the dark-in-flight firmware restriction until that test passes. |

### D-CIR-01. Select the real e-match before choosing the all-fire margin

No project e-match model was previously selected. Choose **MJG J-Tek LEAD-FREE**, standard 24 AWG leads,
with its protective shroud retained. Maker [technical sheet p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF)
gives minimum all-fire 0.75 A (a 0.5 s test at 1.5 V), recommended minimum 1.00 A / nominal 1.25 A, average
bridgewire 1 Ω (standard deviation 0.09 Ω), maximum test 40 mA, no-fire 0.30 A and minimum all-fire energy 4 mJ.
Keep one current margin, **1.5×0.75 = 1.125 A**, replacing the inherited 1.5 A derived from an unnamed 1 A part.
Retain the conservative 2 Ω match/0.3 Ω external-lead loop bounds; R134 stays 2 Ω and its short/brownout qualification
is unchanged. With the new SD/always-on normal allocation the present loop calculation gives 1.546041 A idle,
1.481042 A one persistent stall and 1.284404 A four stalls at the 7.4 V equivalent fire-time source floor: all exceed
1.125 A (Calc / Inference). Neutral commands do not clear a jam. The maker's 0.5 s all-fire test does not certify
our ≤20 ms physical pulse; lot-specific 20 ms firing qualification, source/harness measurement and charge testing
remain required before flight. Current margin alone is not a firing reliability claim.

### D-CIR-02. Switched camera pad energy

GPS/radio are always powered; camera U402 is off on the pad unless recording. The adopted two-hour pad model
retains the previous 1.76 Ah estimate including up to 30 minutes of 1 A camera recording and continuous radio,
plus up to 0.275 Ah for continuous allocated SD writes at the conservative 6.0 V / 80% converter corner: about
2.04 Ah before reserve. Choose **≥2.6 Ah** for that maximum case, with at least 20% capacity reserve, and verify
7.4 V equivalent source reserve at firing. Camera recording throughout two hours adds about 1.155 Ah to the
30-minute case: approximately 3.19 Ah before reserve / **≥4 Ah** with the same reserve (Inference). Actual device
duty, temperature, aged capacity and pack/servo/harness load need measurement and physical battery-bay fit. A 2 Ah pack is not qualified for
the new worst continuous-write case. This is a capacity choice, not new protection hardware.

### D-CIR-03. Circuit-pass placement and routing (minimum for a connected DRC-clean board)

Board `6e73b6ebe7e25d7a8c810493887fbaa7cce34f6fe1d379828dc67017e14235aa`. Scope per the Steer 1 hand-off: only what is
needed for a connected, DRC-clean, reproducible board; the layout agent re-arranges the identical terminals into
AVA-like rows afterwards. U1, the core block, U4 (bottom, rotation 180, roll = −gyro_Y, lever x −6.0 mm), the pyro FETs,
J121 and J1 are unchanged.

| Choice | Reason (constraint, not preference) |
|---|---|
| J410 on the east edge at (41.5, 15.5) rot 90; J9 on the east edge at (41.5, 59.5) rot 90 | Terminal rows face the east edge as J9 did in R9; DB125 courtyards (about 3.5 mm pitch, 4 positions) leave room for only these two plus the camera cell. |
| J420 **parked on the west edge** at (5, 16) rot −90 | The east edge holds J410 and the camera cell, and a second 4-position DB125 does not fit there without moving the camera cell. West is a stop-gap: the layout agent will re-arrange the identical terminals, so J420's final position is not a decision. Consequence: the radio lanes cross the USB / SD corridor (signal integrity of those lanes is unmeasured). |
| J400 at (12.7, 85); J122 (5-position, no tie holes) at (27, 84.8); J430 on the bottom at (24, 24.3) | Forward-edge terminal row; the screw terminal clamps wires, so the servo-plug tie holes have no function (D-CIR terminal decision). J430 sits near U1's SPI3 pins 78–81 and the QSPI flash. |
| SPI3 escape from U1 pins 78–81 fanned south-west with 45° steps, every via ≥ 0.6 mm from other critical centrelines | K-reference counts the In1 antipad of a via at radius 0.4 mm. Pin pitch is 0.5 mm, so parallel lanes with vias at pitch always failed; the fan opens the via-to-foreign-critical-centreline distance to ≥ 0.6 mm. |
| SWCLK lane y 36.6, SWDIO y 36.1, NRST a **single via** at (14.2, 37.3) on the same one-via leg | The west bundle (SWDIO / SWCLK / NRST / SD) is crowded; NRST keeps exactly one via per D-R2-09 (one reference region, one layer change), so the neighbours move rather than NRST gaining a hop. USB_FAULT_N runs on B.Cu at y 41.2. |
| USB_LIMITED uses an F.Cu overpass over the four B.Cu SD lanes (two vias); BUZZ_DRV hop pair over USB_LIMITED | The USB corridor (x 16–22, y 26–34) is boxed by VBUS_SENSE, USB_LIMITED and USB_DM; the SD lanes occupy B.Cu there, so USB_LIMITED must cross them on F.Cu. BUZZ_DRV crosses USB_LIMITED by the same two-via hop. |
| Radio TX series resistor R451 on B.Cu at the forced hop | The hop is forced by the J420 west park; putting R451 on B.Cu keeps the net within route_check's extra-vias limit (pads + 2) instead of adding a third via. |
| R85 / R90 / R110 / C86 / R464 / C460 moved locally | Clearance to the new DB125 / J430 courtyards and the SPI3 fan; each stays inside its own cell, no net change. |
| R166 to (35.25, 64) north-south; R82 shifted slightly | DB125 J9 / J122 courtyard clearance on the battery-feed side. R166 is in the hot-plug damper path, so the move is qualified only by the re-run actual-feed model: **2304 / 2304 pass** (simulation / Inference; `hotplug.md`, 2026-10-29). The model runs inside `r10_build.sh`, so any later feed move is re-gated automatically. |
| Four pour-only keep-outs R8_POUR_TRIM_C1–C4 | Unfillable pour slivers between the new terminals; they are fill-trim areas only (no copper, no net), and route_check recognises the `R8_POUR_TRIM` prefix. |

No hand editing of the production board; every item is generated by `r10_pcb.py` / `r10_route_*.py` with
`r10_place.tsv` and `r10_fanout.tsv`. `r10_fanout.tsv` carries hand edits for this pass, so re-running
`r10_fanout_aid.py` would drop them. Verified: two complete builds byte-identical, full `tools/check.sh` zero (software
/ CAD). Not verified: any bench or physical routing effect (UART signal integrity on the long west radio lanes is an
Inference).

### D-CIR-04. Gate fixes

Three gate / test fixes, none weakening a rule: each corrects a gap in the check or its fixture, not the design.

1. **K-contract seeds (`tools/test_r10_check.py`):** the seeded fixtures did not feed the seeded board text to the
   text-based rules, so the rule read the unmodified text and the seed proved nothing. Root cause: fixture, not rule.
   The seeds now pass the seeded text; each seeded fault is caught again.
2. **`terminal_legend_conflicts()` in `check_r10` K-legends:** the terminals are now labelled by individual `n:NAME`
   legends, and nothing examined a second, contradicting legend: a combined `Jnn n:NAME` table (text or text box) or a
   bare `n:NAME` that is not one of the terminal words. The old seed only appeared to pass because its text box sat on
   J420.1's mask opening after J420 moved. Root cause: gate gap plus a stale fixture. The new function names the
   conflicting pin (for example `J420.3`); the seed text box moved to a free spot and asserts that it adds no mask
   overlap. The existing legend, distance and text rules are unchanged.
3. **Probe-clearance seeds (J2 / TP122):** a fixed offset placed TP122's seeded track on a PYRO1_GATE via, so DRC
   reported a short rather than the custom-rule clearance under test. The seed now picks the first side (or sibling
   contact) whose seeded track is at least 0.25 mm from all other copper and holes, with the same gap and expected rule.
   Root cause: fixture.

Result: the full `tools/check.sh` passes at zero on `6e73b6eb…` in both builds; the self-test counts and every threshold
are otherwise unchanged. AGENTS §2 is unchanged.


## D-AVA-01. AVA terminal rows and local cells (2026-10-29; CAD layout complete)

The supervisor verified the circuit-pass baseline `6e73b6eb…` at check.sh exit 0 outside the sandbox. KiCad CLI's
sandbox-only Swift crash is an environment fault; subsequent builds and DRC use the supervisor build service.
The completed relayout is PCB `0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`.
No AGENTS §2 rule, electrical connection, MCU pin assignment, part selection, support or IMU pose changes.
[AVA_LAYOUT.md](AVA_LAYOUT.md) records measurements, the ten §6 dispositions and remaining review items.

- **Terminals:** west x = 7 mm, east x = 39 mm, all wires outward. The west IGN / switch / battery centres are
  y = 55.85 / 65.85 / 75.85 mm, giving a 10 mm pitch and one power/pyro zone. IGN remains black and BAT green (F8).
  The east GPS / radio / camera centres are y = 15.5 / 31.5 / 47.5 mm, giving a 16 mm pitch; servos continue the same
  column at y = 71.5 mm. This fixes parked J420 and keeps the five supports. Calculated wire room is 4.953 mm at
  every DB125; physical harness, bore and stack qualification remain pending.
- **Port cells:** GPS and radio use identical bottom-side resistor / ESD / decoupling coordinates translated 16 mm.
  Camera uses the same terminal-side resistor / ESD lanes, with its retained U12/U13 isolation and U402 switch
  immediately inboard. U12 is rotated to 0° at (31.6, 39.8), C93 is directly beside its IO supply and C100 immediately west of it;
  the RX/TX entries each cross sides once. Camera retains a larger envelope than the circuit pass to accommodate
  its separate switch/isolation, ADC column and the uninterrupted servo/status lanes. Removed GPS/radio switches and translators stay
  removed; the owner's always-on circuit takes precedence over the older AVA comparison.
- **Sense cells:** continuity and RAW_ACT divider/filter chains use matching vertical columns at x = 23 and 28 mm,
  beside the pyro block and MCU ADC edge. Camera and VLOGIC sense chains use one east-side column. Series safety
  resistors, parallel lower legs and filters remain as audited; no duplicate RAW_ACT reading is restored.
- **Battery:** D8, input capacitors, damper, U9 and its local clamp / dividers cluster at J1. C88 stays before U9;
  the actual regenerated input feed passes all 2304 hot-plug cases (simulation / Inference). U11, U2 and C84 sit immediately inboard.
  R166 is horizontal below the capacitor row, keeping its return short and clear of the forward supports.
  D9 is vertical beside U9 OUT; its GND return shares the C80/C96 return. R83 moves west of D9 to retain courtyard
  clearance. C82 and D9 keep the original measured-loop limits, without widening those limits.
- **Buzzer:** LS120, Q123, R162/R163 and D123 form one cell immediately below U1's PC14 edge; BUZZ_DRV has one via.
  PC13 remains unused. The drive is no longer routed across the board.
- **Bottom rows and escapes:** passive rows follow their terminals and local power/sense cells. Core placement and
  fast buses are retained; C24 turns to 90° at (25.45, 49) and C14 turns to 180° at (21.4, 52.15), opening the status
  and buzzer escapes with local supply/ground redraws. C19 moves 0.8 mm north and C16 moves 1.5 mm west to free
  U12's short bypass; C15 moves 0.15 mm west to clear the bus-sense lane. C16/C23 and C100/the QSPI guard share
  existing GND vias. C13's return clears the USB power trunk. C92 and R103 form the IO-rail branch below U13.
  QSPI already uses one layer transition per signal and remains so. C90 moves into the core 3V3 plane region.
- **In2:** wider contiguous rail regions replace the narrow terminal-following fingers. A short 3V3A trunk and the
  USB_LIMITED feed use In2 power copper, freeing outer-layer status corridors; neither carries a signal on In2.
  A short 0.4 mm F.Cu 3V3 bridge joins the buck and core regions across the RAW/VLOGIC corridor; the two vias avoid
  isolating either region. The CH1 GND region follows the entire firing-resistor pads, with the mandated barrel
  clearance. Crystal reference, fast-interface reference continuity and S-8 barrel exclusions remain mandatory gates.
- **Ground, legends and probes:** regenerate the frozen ground fan-out for the moved cells, retain required fast-via
  partners, and place terminal pin legends beside their subjects. TP80/81/83/88 follow the battery and supply cell,
  TP120/121/122 follow the pyro switch / gate / firing cell, and TP82 follows USB protection. Probe spacing stays gated.
  R90 moves into the USB limiter cell at (7.8, 23.1), and the SPI3 transitions share two compliant return vias;
  the redundant (12.25, 40.65) partner and (8.7, 37.75) stitch are removed. This reserves six short 1 mm J2 pin
  legends, each nearer J2 than any other connector and within 6 mm. R110’s return moves to (11.6, 23.9), clear
  of the pull-up feed. R405 shares D410's return; C60 shares C431's. The camera ADC divider and filter have their
  own short returns where sharing would cross the supply via. No GND trim removes a pad's pour contact. The SOT-23-3 library pin-1 dot moves alongside pin 1, clear of R134 openings; U12's library pin-1 dot moves 0.2 mm away from C100's mask opening. Neither changes a land or pad.

Two complete builds exit 0 and reproduce the PCB and all 23 recorded CAD/binding/model files byte for byte.
Both run the full check.sh: DRC 0 / unconnected 0 / parity 0 / ERC 0, all 31 R10 rules, routing, fit, fabrication
and required regression tests pass. The actual-feed hot-plug model passes 2304/2304 cases (simulation / Inference).
This remains CAD evidence only; no independent review round, physical qualification or owner acceptance is claimed.

### D-AVA-02. Gates and reproducibility support

P-11 now applies the accepted 4.95 mm floor and outward entry to all seven DB125 terminals, with seeded failures
for each newly covered connector. S-9's seven source-bridge records translate exactly 1 mm with Q120/Q121; widths
and lengths are unchanged. Three regression fixtures follow the new layout: the free-area conflicting textbox is
now nearest J410.3, and the width seeds select a real long terminal-to-FET path instead of silently missing old
coordinates. They still inject and detect the same faults. No safety, width, reference, thermal or clearance limit
is reduced. The full build regenerates the fabrication package before check.sh so its manifest is checked without
an override. Rendering uses an optional local output directory; no machine-specific path is stored in the project.

## D-R11-01. Maximum DB125 envelopes and row clearance (2026-10-29)

Round11 parts and mechanics independently found an understated terminal envelope;
a fresh verifier confirmed R11-BOM-01 as Major against P2 and OQ-1. The maker's
[T0-1 sheet1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
gives a maximum wire face of7.70−3.70=+4.00mm from the pad row. The repeated3.90mm
dimension names one rear datum. Include that datum, length tolerances and the
interlock: local x unions are[−4.62,+3.70]/[−8.32,+7.20]/[−10.07,+8.95]mm for
2/4/5positions, local y[−4.10,+4.00], height8.90mm. These are unions of permitted
tolerance corners, not dimensions of one individual body. Tail length is
3.50±0.30mm;3.90mm is not the tail dimension.

Retain the accepted4.95mm wire-room floor. The old row centres7/39mm give only
4.603012mm with the corrected envelope. Move west to7.4 and east to38.6mm,
preserving axial pitch, outward orientation, supports, pins and IMU pose. Native
in-memory calculations then give5.003012mm at all seven terminals. They are CAD
calculations, not harness or screwdriver qualification.

Courtyards enclose the full tolerance union with0.20mm assembly margin. This
leaves0.48mm between maximum4P body unions at16mm pitch;0.25mm courtyards would
overlap by0.02mm before stroke. No maker or project rule mandates0.25mm here;
the additional0.20mm outside the complete maximum insulating body is a placement
allowance, not an electrical spacing reduction. Actual assembly/tool access stays
unverified. Shift Q124 0.30 mm east, R80/R165 0.25 mm east, C80 0.05 mm east,
and the east ADC resistor column/C94 0.30 mm west. Move C60 to F(33.2,56.8), rotation90, and
R60 to F(33.2,58.6), with the camera-enable branch/via at y=57.4 mm.
This keeps C60 clear of both the terminal courtyard and the servo-signal lane.
The prototype shows no terminal/body or courtyard intersection. Keep C80's
straight copper bus0.05mm off its moved pad centre, well inside the pad, rather
than creating a needless tiny jog. Redraw affected power/pyro/sense paths and the
OUT via's GND partner through generators only.

Also adopt the six low-risk R11-RTE-01 route simplifications (four bumps, switch
and VLOGIC monotone branches), explicit thermal relief on every DB125 GND contact,
and a drill-clear J122 Fab reference. None changes a circuit connection or limit.
**Status when proposed:** generator changes in progress; full supervised build, DRC, actual-feed
hot-plug, fabrication, binding, reproducibility and subsequent reviews are pending.
AGENTS§2 is unchanged. Do not label the prototype as a rebuilt/checked board.

## D-R11-02. Close the demonstrated gate gaps

R11-GATE-01…03 concern prospective faults, not faults present on the review board.
Use one R10 terminal-label walk for board/footprint text and text boxes: exact
nearest connector pin, exactly one individual label, polarity characters included.
Keep R8's archived behavior and AUD-10's distance-only treatment unchanged.
Extend the existing required-fitted invariant to all199 reviewed functional parts
and support components across native CAD, schematic and BOM/CPL. Reuse the current
walks; add no redundant full schematic walk. Reject nonfinite/nonpositive model
transforms and degenerate envelopes; make both fit and P-11 fail on invalid
geometry while preserving valid positive unit-conversion scales.

The draft's focused/native tests pass139 unique cases and its new seeds expose20
failed subtests against the old code. That evidence is not a full build/DRC pass.
The patch is applied for the next supervised build; final integrated counts follow
in the validation record. No safety/clearance/population limit is weakened.

## D-R11-03. Bind electrical calculations to native firing copper

R11-PWR-01/REQ-01/DOC-01 found circuit-pass length literals after AVA rerouting.
Use native retained firing paths, pruning dead sense branches. Include routed
copper inside a terminal pad when it joins a retained endpoint to the pad anchor:
BAT_IN has6.000000mm external trace plus0.707107mm routed drain-pad entry on the
review target. Do not count the dead RAW_ACT sense stub within R134.2. Use only
the aligned Q120.2→Q121.3 source path,2.2mm at0.4mm, with no parallel-leg credit.
Mixed widths or series layer changes must stop extraction until their resistance
model is reviewed; never silently ignore a via.

At the existing35µm/20°C resistivity and hot material assumptions, the review
target gives29.820114/35.679767mΩ at20/70°C, loop4.618006Ω and fire current
1.544183/1.479263/1.414096/1.348645/1.282861A for0…4stalls. All remain above the
selected1.125A criterion. These are conditional calculations, not measured source,
pad, FET, copper, harness or e-match performance. Re-extract after row/route fixes.

Generate library assets before the schematic and the native-bound budget after
the final PCB; check both deterministically in the final gate. Bind the budget
to its board SHA, without a fab-manifest dependency cycle. Preserve all existing
load, temperature, pulse, contact, source and harness assumptions. The full
actual-feed hot-plug sweep and final output-path measurements must also be
refreshed after the geometry changes; old named-board results remain historical.

## D-R11-04. Current assembly records and retained qualification limits

Correct active GH/header/parked-radio prose, J9 board RX/TX parentheticals, Rev11
AF citations and PC1 analog-reset terminology. Refresh coating/probes/staking
from current parts and copper, preserving the full U4/U5 exclusions and sole
controlled TP122 brush exception. All seven terminals, including J400, require
staking and externally supported leads. The closed microSD envelope does not
allocate lid travel: remove the board from the continuous sled, or qualify a
physical access window, before opening it off/out of the bay.

Do not claim translator protection on direct GPS/radio UARTs. Their1k/ground-ESD
architecture is the owner's decision; pin/injection limits and installed ESD,
back-feed and radio-immunity tests remain open. Retain the measured C98 remote
return Minor:13.497mm pad-to-stitch and31.812mm diagnostic device loop. A partial
via option halves the geometric loop but does not establish a local return or
transient performance; no fully checked local alternative is proved. Preserve
the noncritical-return/pad-entry inventory for owner acceptance and bench tests.

The parent VEHICLE mirror is stale, but this task forbids another-worktree edits.
Record the exact required update in the in-worktree review handoff; do not edit it
or invent owner acceptance. Procurement remains preliminary: fresh review lookup
is$82.61 placed-parts/feeder share versus$84.41, but minimum purchases give$84.95
before fixed/process/PCB/shipping costs; R430/U4 are short and U9's minimum is7
against5 needed. Refresh within24h of any order and obtain the process quote.
No order, firmware, physical qualification or AGENTS§2 change is authorized here.


### D-R11-01 verification addendum

The fresh fix verifier caught and corrected five initial source-prototype
clearance groups before any CAD save: both C92/U402 return sites, camera enable,
IGN's shifted diagonal and Q124 source-via/paste entry. Apply the exact passing
alternatives recorded in`round11_fix_geometry.json` under the review directory.
The source dry runs total977segments/294vias; this is not an official build.
The in-memory alternative passes the listed shape/angle/partner/fit/S-8 checks,
but all full build, connectivity, reference/region, model, fabrication and
reproducibility checks remain pending through the supervisor.

Retain the prototype's three measured same-net ring webs (≈0.050mm at the two
Q124 returns;≈0.066mm at C92.2). Hole gaps≈0.150/0.166mm pass ordinary rules; no
hole/paste entry is waived. Q124's farther x16.05 via would give only0.035376mm
to the B.Cu OUTdiagonal; selected x15.85 gives0.176802mm. Recount all mask/web
residuals on the actual rebuilt board and list them for owner acceptance.

## D-R11-05. Use the vendor's headless DRC fix

The supervisor withdrew its build service and authorized direct CLI builds on
2026-10-29. Writable preference/cache/document folders did not cure the installed
KiCad 10.0.6 failure: the first staged PCB DRC aborted, and normal, clean-config
and terminal probes reported `SwiftNativeNSArray` array-index failure. No DRC or
full-gate pass is inferred from those attempts.

Upstream [issue25413](https://gitlab.com/kicad/code/kicad/-/issues/25413) and
[fix f0ca3b0](https://github.com/KiCad/kicad-source-mirror/commit/f0ca3b0510c3bcccd76223a06447eecfc7ebe0eb)
identify the headless commit's GUI cursor query. The first stable release with
the guard is 10.0.7. Use the [official vendor package](https://kicad-downloads.s3.cern.ch/osx/stable/kicad-unified-universal-10.0.7.dmg) in a temporary directory,
verify its published SHA-256 before execution, and rerun the unchanged stages
and full gate. Do not patch KiCad, skip a gate, or infer a pass from a crash.
The package SHA-256 is
`fbc27419b841a9a2a8b143b5875a87b8bd943ffcf487d53c78a8fb6d24c59e27`.
Tool versions and final results belong in the round11 fix-validation record.
Commit requests still use the supervisor; no safety or design limit changes.

### D-R11-01 integrated-check corrections

The first real complete-board DRC with the updated CLI found Q124's moved
courtyard overlapping C126 by 0.05 mm. Move C126 east by 0.15 mm to (16.85,
57.675), retaining its pose and connections; adjust its 45-degree gate entry
and GND stitch together. The un-stroked courtyard gap is then 0.10 mm.

The staged routing gate also rejected the moved camera-sense supply branch's
removable bump. Use R104.1 → (34.2,47.07) → (34.2,49.325), with the same via
centre explicit in the bottom C91/U13 branch. This removes one segment and
keeps 0.187 mm copper clearance from R105.2. No allowlist or rule change is
needed. Both corrections require the final build and full-gate evidence below.

### D-R11-01 bottom-cell integration

The first complete gate also found sixteen bottom parts inside the unchanged
1.5 mm through-hole assembly floor and two camera wire references escaping
their permitted pad voids. Correct the local cells rather than weaken either
rule. Actual rebuilt courtyard polygons and real DRC supersede the earlier
position-only API prototype, whose courtyard caches were stale.

Keep the servo clamp and pull-down poses. Move R150–R153 to B(34.6,75.9),
B(34.7,72.77), B(34.7,70.23) and B(34.6,68), respectively. Move the shared R154
return stitch to (33.4,74.96), preserving the via count. It is 1.021567/1.483653 mm
from the first two PWM transitions. Turn the first two output routes beside
their resistors so the terminals retain centred entries without redundant
in-pad tails. The servo receipt records 49 segments/10 vias, minimum M-6 gap
1.536 mm and actual courtyard gap 0.020 mm. The existing third PWM companion
distance of 1.747413 mm remains outside the critical-signal rule's scope and
stays a review deviation; this is no electrical-return qualification.

The port cells must also clear the microSD socket, ADC trunks, solder-paste
apertures and terminal barrels. Their exact poses and stitches are in
`sources/r10_review/round11_m6_fix.json`. C411 moves below the SD return;
C431 uses the pocket below the camera terminal. Keep U13 fixed and place C91
at B(34.95,53.9), rotation −90°, with C92 at B(32.35,52.5). This compact pocket
keeps the input bypass 4.092 mm directly/5.036 mm by its drawn 0.4 mm supply
route from U13. It is longer than the original 2.300/2.775 mm connection and
remains a measured return/transient qualification item. The conservative C91/C92
courtyard-envelope gap is 0.010 mm (native collision-polygon gap 0.110 mm);
the conservative C91 courtyard-envelope-to-terminal-pad gap is 1.505 mm.
Do not infer a measured transient response from those CAD distances.

Move both camera clamp returns west of the front control lanes, retain the
GPS shared return that clears R405, and move the LOGIC_SOURCE_ST transition
to (30.85,51.8) to clear C92. R13 moves east 0.28 mm, not 0.40 mm, to preserve
R64 clearance. The integrated build, full gate, binding and reproducibility
receipts determine final closure; isolated worker prototypes are scoped
implementation evidence only. Circuit connections, pins, supports, axes,
clearance limits, allowlists and AGENTS §2 are unchanged.

### D-R11-01 completed fix validation

The final PCB is `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`.
Two complete direct native builds exit zero and reproduce all 42 recorded
CAD/library/model, electrical-evidence and binding files byte for byte. Both
full gates pass DRC/unconnected/parity/ERC zero, all 31 R10 rules, routing and
current fabrication checks. The fresh terminal verifier closes the Major with
5.003011866 mm wire room at all seven contacts, preserving the 4.95 mm floor.
The sixteen bottom keep-outs and two camera-reference failures in the earlier
intermediate attempt are corrected without weakening a gate. Exact receipts,
remaining graphics/return/entry inventory and limitations are in
`sources/r10_review/round11_fix_validation.json` and the scoped receipts it links.

The final native fire loop is 4.617458126 Ω, giving 1.544366072 A idle and
1.283013039 A at four persistent stalls under the stated source/material/harness
conditions; selected-lot 20 ms firing remains unqualified. Actual-feed hot-plug
2304 required cases and 60 local sensitivities pass as Simulation / Inference.
The optional current plate calculation is 181.3 Hz pinned D5 / 70.3 g estimated
mass, replacing the former connector population's 280.9 Hz / 45.5 g record.
None is a bench or flight result. The current bare-barrel S-8 minimum is 1.103 mm;
the unchanged 1.0 mm floor remains blocking.

The final-CPL public supplier snapshot at 2026-10-30 05:00 UTC supersedes the
preliminary $82.61/$84.95 figures above: $79.53 placed parts plus feeder share,
approximately $81.87 with minimum purchases, against $84.41. Fixed fees,
possible handling, PCB, rails, joints, consignment, process and shipping are
additional. R430 17<3610 and U4 0<5 remain stock blockers; U9 has a 7-piece
minimum for five needed. No quote, process/deviation acceptance or order is
inferred. Fresh complete rounds 12+ must still earn two consecutive clean rounds
on the committed PCB; round 11 remains 0 Critical / 1 Major / 16 Minor groups.
AGENTS §2 and all owner decisions remain authoritative and unchanged.

## D-R12-01. Correct the evidence without an unsupported circuit change

The full committed-board round12 found no Critical or Major. Its PC14 review
(R12-MCU-01) correctly rejects the old2.9mA proof: [ST DS12110 Rev11
Table149 p244](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) bounds
output drop at the3mA characterization point. Dividing0.4V by3mA cannot supply
a minimum driver resistance for a maximum-current calculation. Withdraw that
claim in the current pin-table source and mark the old D-R3-12 basis corrected.

Retain R1621kOhm and Q123: a hard transient-current violation or failed buzzer
is not demonstrated. The resistor-only initial bound is3.3mA nominal and
3.363636mA at the stated3.33V/990Ohm initial-tolerance corner; steady current is
about0.306mA. These are calculations, not measured gate/driver waveforms or
all-temperature limits. Table150 note2 p246's2MHz limit remains; use the4kHz
buzzer with LSE disabled. Regenerate binding provenance after the note change;
electrical nets, pin assignments, axes and AGENTS section2 are unchanged.

Refresh active status/geometry from the current native budget/ordering worksheet
rather than duplicate superseded coordinates. Keep every earlier review tied to
its exact PCB. Parent VEHICLE remains a separately owned stale mirror; supply an
in-worktree integration handoff without editing that worktree. The fresh
2026-10-30T06:11:29Z public supplier record is82.65USD placed/feeder share and
84.99USD with minimum purchases,0.58USD above84.41; R430/U4 supply and full
process/quote/deviation acceptance remain owner items. No acceptance/order is
inferred and no AGENTS section2 rule changes.

## D-R12-02. Local return, direct control route and readable Fab references

R12-RTE-01 identifies a removable BAT_ENABLE bend. In the complete power
generator polyline, replace the tail through (18.2,78.3)/(19.9,80) with
(18.0232,78.4768)/(18.0232,81.8768), ending at the existing (17.1,82.8) via.
This saves1.408326mm without moving a pad, via or layer transition. Preserve
the complete diagonal from (21.3,75.2); do not introduce a collinear sliver.
The resulting complete four-segment chain is15.639697mm, equal to its unobstructed
45degree geodesic. The fresh route pass counts it as one `extra_bends` information
item, while the former removable bump is gone. Native0.15mm copper screening
rejects both two-segment vertical/diagonal alternatives: the east route has only
0.100mm to the (20.85,76.4) GND via and collides with the U9 OUT-via field;
the west route hits ACT_EN copper and the D8/GND return. Retain this shortest-
length routed compromise; this bounded screen is not a proof about every
possible whole-board relayout. The ordinary C98 stitch is a separate new
informational item. Final count/category definitions are refreshed from the
finished native board, not added to an old review's supplementary bump total.

R12-PWR-01/RTE-02 finds C98.2's remote return. Add one ordinary0.5/0.3mm GND
stitch at (23.8,62.95), preserving every existing GND track and the fanout table.
The focused native candidate connects C98's B.Cu island through the continuous
In1 plane to U11.12's existing ground fanout. Its0.05mm-grid saved-copper return
is7.345584mm versus31.812237mm before; the0.025mm-grid result is7.270584mm.
These are geometric diagnostics, not measured inductance or transient response.
[TI TPS2121 SLVSEA3F p33](https://www.ti.com/lit/ds/symlink/tps2121.pdf) calls
for close bypasses/short wide returns without a numerical loop limit. No
functional failure was demonstrated. The ordinary hole-to-paste/mask minimum
is0.125mm against0.1mm, and native DRC, fit and routing pass on the candidate.
Its in-fill via/track annotation remains an explicit M2 deviation: the centre
is0.300mm off the preserved track and its ring overlaps it0.050mm; the via also
contacts the saved ground pour. Do not add the rejected0.424mm tiny jog merely
to remove that annotation. Full integration and provenance checks remain required.

R12-MFG-01 is addressed only in the Fab-reference generator: R10, C29, C92,
R8 and C5 use0.4mm text/0.06mm strokes, preserving angle and mirroring; R10
moves0.10mm and C29 moves0.05mm. The checked focused candidate changes only
those five text items, is idempotent and has0.027960mm minimum glyph-to-own-Fab
clearance. Root inspected the complete bottom drawing and enlarged details.
Small Fab text needs vector zoom; silkscreen remains at least1.0mm/0.15mm.
The focused receipts are implementation evidence, not a new full review round.
Rebuild all native artifacts twice and run fresh full rounds13/14 on the
resulting committed PCB. Circuit, pins, axes, supports, gate scope and AGENTS
section2 are unchanged.

## D-R12-03. Gate the manufactured geometry and fitted quantities

Close the three prospective R12 gate gaps without altering design limits.
Compare normalized local physical boxes for all seven DB125s and the closed
microSD/card union with the reviewed maker-derived dimensions and pose. An
equivalent model-unit conversion is valid; a positive scale that shrinks the
physical envelope is not. The tolerance is0.000020mm: the measured maximum
endpoint discrepancy is0.00000149mm, with0.000001905mm bound from six-decimal
VRML endpoint quantization. Include0.01/0.99999 shrink and0.000030mm offset
faults as well as equivalent-unit positive controls.

Extend K-inner's existing In1-GND-only/In2-power-and-GND policy across actual
manufactured drawings, text and filled board/footprint zones using the existing
native copper walk. Legitimate pads/vias still traverse inner layers. Test real
connected foreign copper; an empty footprint-zone fixture is not coverage.
Production BOM Qty must be a positive integer equal to the row's distinct
designators; a production BOM requires Qty while a CPL remains quantity-free.
Test zero, malformed and mismatched counts. These are prospective gate gaps;
the frozen mutants also hit existing stale-binding checks, so no whole-gate
escape was established. Test receipts and complete integration checks record
the actual closure; no physical or firmware qualification is inferred.

## D-R13-01. Allocate actual tails and socket nails; clear Fab references

Round13 found no Critical or Major on committed7355ae1a/fa897c8. Correct the
mechanical evidence without moving parts, lands, supports or the IMU. The
DORABO T0-1 drawing gives3.50+/-0.30mm terminal tails below seating. Body-only
VRML boxes are not tail coverage. Allocate all23 tails separately in fit_check:
use each native copper-pad XY box as a conservative transverse Inference and
3.80mm below seating. Projection below the1.60mm PCB is2.20mm; nominal4mm
standoffs leave1.80mm to the plate. The current calculated minimum tail/bore
clearance is7.558359mm. Real seating, solder fillets, bent leads and loaded sled
clearance remain inspection/physical obligations, not model facts.

The optional plate calculator must not add those23 collision-only rows as new
component masses: the explicit DB125 lump already includes the connector's
metal pins. A focused old-code control adds a spurious0.547998g; exclude only
the named tail collision rows while preserving all explicit mass keys. The new
positive/negative regression and supplied-interpreter numerical controls pass.
The final native-fit diagnostic remains181.3Hz pinnedD5/70.3g estimated mass;
C431's100g rigid-sled gap is0.274363mm at h4 and negative at h3.5. This source-
only optional-calculation correction was found after buildA and is included in
buildB's full gate; it cannot change the42 generated CAD/binding artifacts.
Round13_plate records exact inputs and scope. No physical mass,stiffness,
shock or vibration qualification is inferred.

[Molex SD-47219-001G sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
includes fitting nails and general tolerances outside the previous14mm model.
Use width(13.60+0.15)+2(0.50+0.15)=15.05mm, socket y-9.70..+5.35mm,
and the existing inferred card-front+6.00mm/height2.10mm. The resulting closed
allocation is15.05x15.70x2.10mm, centred at local(0,-1.85). Common seating,
centring and undimensioned card projection remain Inference; this is not a
maker-certified assembled maximum. Native fit remains clear, including0.575mm
to C23's courtyard and15.210798mm to the bore. Keep unpowered off-sled card
service or qualify a real hinge window; no open-hinge fit is inferred.

Apply77 measured Fab-reference-only offsets/sizes to remove border, pin1-dot
and polarity-text intersections. Preserve132 other references, all non-reference
objects and silkscreen rules. Use the fixed source table, never a runtime search.
All209 references/722 rendered characters are checked, including37 drill-cutout
polygons; clearance survives0.025mm glyph inflation. Small Fab labels still
need vector zoom and first-article identification. The detailed source and
visual receipts are round13_fab_fix. Delete the two unreferenced circuit-pass
r10_top/r10_bottom PNG previews; current assembly PDFs and their native manifest
supply board-bound drawings. No electrical or physical qualification follows.

## D-R13-02. Reject contradictory identities, duplicate BOM rows and wrong paste

Close three prospective adversarial gaps while preserving actual design limits.
Recognize normalized alternate part-number fields, including MPN, and reject
contradiction with the canonical Manufacturer Part/LCSC identity; matching or
blank aliases remain valid. Reject a designator appearing in more than one
production BOM/CPL row, preserving positive integer BOM quantities and
quantity-free CPL semantics. Compare the actual Gerber aperture polygons with
native plotted paste geometry within1micrometre, including native margins,
rotations and reviewed split exposed-pad windows. Do not invent a universal
paste-coverage percentage or stencil-volume qualification. Unsupported geometry
operations fail closed. Current618 apertures pass; the contradictory R134MPN,
duplicate R134 row and0.001mm aperture seeds now reject. Earlier broader stale
bindings also rejected those mutants; no original whole-gate escape is claimed.
The focused regressions, old-code failures and native positive controls are
recorded in round13_gate_fix. Full integrated gates remain required. No owner
rule, physical acceptance or AGENTS section2 constraint is weakened.

## D-R13-03. Correct operating evidence and adopt only qualified local redraws

R84 is RT0603BRD07750RL,0.1%/25ppm/K. TI TPS25947 RevC p9/eq7 p32's exact750ohm
3.96..4.84A range does not include that resistor's full tolerance. Apply inverse-R
sensitivity over100K, +/-0.35%:3.946188..4.856999A (Calculation/Inference, not new
TI characterization). The3.743797A conservative fault allocation retains
0.202391A margin to the lower result. Comparator overshoot, parasitic dips,
continuous fault operation and hot-plug/endurance remain unmeasured; no circuit
change or higher load allowance is justified by this correction.

DS12110 Rev11 Table112 note3 p210/Table147 note6 p242 require internal pulls off
when an input exceeds its relevant I/O supply+0.3V. This is separate from
Table109 note4 p208's4V absolute-stress condition. Keep the direct GPS/radio RX
pulls disabled throughout operation; retain no-self-powered-port-with-board-off
and no-back-feed-while-connecting-match rules. Correct source notes, schematic
checks and binding evidence without moving any of the100 MCU pins. The R10
evidence JSON is not an executable firmware binding: assembly_binding.py and
v0.8.1/diagnostics remain R1-bound and cannot qualify this PCB.

Replace CAM_RX_BUFFER's local B.Cu detour with the checked U12.1 to R100.2
vertical/45degree path through(30.05,42.625), saving1.156928mm and two segments.
Bounded additional same-layer signal sketches may be adopted only after native
all-severity/parity DRC and unchanged reference/critical-hygiene rules pass;
round13_routing_fix enumerates the actual adopted source paths and rejected or
unqualified sketches. Do not change pads, vias, planes, layers, power/pyro or
fast-interface cells merely to lower an information count. Remaining M2 choices,
remote noncritical return companions and L400's possible0.15mm uncovered heel
remain measured deviations for owner/assembler and bench qualification, not
claims that all alternatives are impossible.

The bounded qualification adopts all12 named source paths in that receipt:
CAM_RX_BUFFER,LED_YEL,BUZZ_DRV,V3V3_SENSE,LOGIC_SOURCE_ST,RADIO_TX_MCU,
VBUS_SENSE,CAM_PWR_EN,CAM_FAULT_N,GPS_TX_WIRE,GPS_RX_WIRE and NRST. Genuine
individual and combined all-severity/parity DRC and unchanged reference/hygiene
controls pass. The canonical native comparison saves6.175186mm and seven
segments; all pads,nets,poses,vias and GND tracks are identical. LED_YEL's
0.150000..0.150001mm clearance meets native0.15mm but is below the supplemental
search's0.16mm reserve; disclose this numerical scope rather than claiming the
search proves no alternative. Final inventory is140 actual information items:
110 ordinary+22 inside-pad+8 noncritical leftovers,54 all-net bump windows.
The11 slow AUD-2 observations are5 runs,5 pads and1 connected-chain observation,
not11 distinct nets. All these M2 compromises still await owner acceptance.

Correct O6's signal-reference-branch wording, actual R432.1 endpoint name, stale
PREPARATION/final-binding ledger states and the active flight's estimated
Mach1.9 harness statement. Parent VEHICLE remains a separately owned stale
mirror; the in-worktree handoff records current geometry without editing that
worktree. Preserve each older review at its exact board hash. The fresh public
supplier snapshot2026-10-30T08:38:52.797802Z gives82.6458USD placed/feeder share
and84.9862USD including minimum purchases, before fixed/process/PCB/shipping.
R43017<3610 and U4 0<5 remain stock blockers; U9 minimum7 for5 fitted. No quote,
order or owner cost/process/deviation acceptance is inferred. Rebuild twice,
check0, refresh all native provenance and commit; because these fixes change the
PCB, fresh complete rounds14/15 must earn the final same-board clean pair.
AGENTS section2 is unchanged.

## D-R14-01. Apply twelve individually qualified local route corrections

Full round14 on f5e4a5a/e0e3ad84 found0Critical/0Major/14 consolidated Minor
groups from20 raw observations. Replace only the twelve source polylines named
in round14_routing_fix: PORT_4V8,3V3,USB_DM,SD_MISO,SD_CS,I2C1_SDA,ACT_GATE,
CAM_IO_3V3,USB_LIMITED,BAT_IN,USB_DP and PYRO1_GATE. Individual and combined
native all-severity/parity DRC, reference/region and critical-hygiene controls
qualify these redraws. Preserve every pad,part pose,via,layer,track width and
unselected track; retire only the now-unused R10 USB_DM REF_STRAY entry. The
source-generated957-track/296-via candidate saves4.985043mm and nine segments.
Do not change R9 sources or relax actual clearance/reference/IPC-2152 limits.
The changed BAT_IN feed requires fresh canonical extraction and the complete
2304 required/60 local hot-plug sweep, not transfer of an old board's binding.

The remaining M2 compromises still need owner acceptance. The new production
information denominator is139=109ordinary+22inside-pad+8noncritical hygiene
leftovers; supplementary search windows are not extra production observations.
Remote noncritical return companions and the possible0.15mm L400 heel strip
remain measured deviations. Neither native checks nor local search prove a
physical noise margin, manufacturing qualification or globally shortest layout.
Rebuild twice, check0 and refresh native/fab/firmware-evidence provenance.
Because the PCB changes, fresh complete rounds15/16 must earn the final same-
board clean pair. AGENTS section2 remains byte-identical.

## D-R14-02. Correct maker mass, operating citations and current records

Use Huaneng MLT-5020 maker sheet p2 item9's nominal0.5g for LS120, replacing
the unsupported0.3g allocation. [Maker sheet](https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598)
SHA256 db73c860afd42abdf9a2e69c4a34ac915d68e07108a2188d6ee0a9c02f723be9.
At100g the nominal inertial force is0.4903325N and its fivefold retention
allocation2.4516625N. Actual assembled mass/retention remain unmeasured. Run
the optional plate calculation on the final native fit and corrected mass;
keep its stiffness,support,wire and shock assumptions labelled Inference.

Correct the UART AF citation to DS12110 Rev11 Table10 p91 PB12/PB13 and p92
PC6/PC7. Direct GPS/radio RX internal pulls stay disabled throughout operation;
Table112 note3 p210/Table147 note6 p242's relevant-I/O-supply+0.3V operating
condition is distinct from Table109 absolute stress. These are source-note
corrections; all100 MCU pins and electrical decisions remain unchanged.
Correct FMEA's active fire currents from the final board-bound budget, P1's
obsolete SMA-overhang parenthesis, the current ordering-board pointer and both
active eight-location ledger labels. Inventory all16 courtyard stroke overlaps
(6top/10bottom); their small polygon gaps and model separation do not prove
physical collisions or qualify assembly access. Retain each measured pair for
owner/assembler first article rather than altering a courtyard for a counter.

Keep the separately owned VEHICLE mirror as an explicit integration obligation;
use this worktree's R10_VEHICLE_HANDOFF without editing another worktree.
The exact82-code public supplier queries2026-10-30T11:02:47.315965 through
11:03:42.599036UTC give82.6434USD placed/feeder share and84.4456USD with minimum
purchases, before fixed/process/PCB/shipping. The latter is0.0356USD over84.41.
U9 is113available/minimum1; R43017<3610 and U4 0<5 remain stock blockers.
This dated evidence is not a quote, order, procurement release or owner acceptance.
Preserve all earlier review executions and supplier snapshots at their own hashes.

## D-R14-03. Fail closed on ambiguous paste commands and collision-only masses

The native-Gerber checker advertises a closed supported subset. Reject
non-default legacy image transforms instead of silently accepting IR/MI/OF/SF;
retain only explicit default AS/IP policy and native/neutral/metadata positives.
[Ucamco Rev2026.05](https://www.ucamco.com/files/downloads/file_en/554/gerber-layer-format-specification-revision-2026-05_en.pdf)
pp186-195 permits ignoring legacy commands. Thus the seeded acceptance is a
project parser-boundary ambiguity, not proof of shifted CAM output or an actual
bad native package. Keep modern transform/polarity rejection and unsupported
unit/notation/stop guards; preserve reviewed split-pad/manual-paste semantics.
The original manifest rejects a mutated archive. Do not invent universal paste
coverage or claim the prior whole gate accepted a corrupt production package.
Actual old-fault/new-reject and native positive controls are in round14_gate_fix.

Filter the23 named terminal-tail collision rows before validating optional plate
mass keys. Explicit connector lumps already contain their pins. A mass key on a
collision-only row, including a mated allowance parent, must fail rather than be
accepted and silently discarded or placed. Valid mass-bearing inputs remain
identical; old-code negative and current positive/negative controls document this
root integration finding separately from the20 full-review observations.

Preserve the requirements review's original count-label error with a root erratum:
651 raw XML nodes/651 unique reference-pin mappings agree with663 numbered
physical pads collapsed to651 unique pairs; twelve duplicate fingers explain
the difference. All100 MCU pins agree. No electrical discrepancy is implied.
The routing reviewer disclosed a broad CLI-location search that exposed unrelated
probe-script lines after initial sketches; it did not read peer reports or use
those lines as evidence. Preserve that method limit and use exact CLI pointer
lookup in fresh rounds. No historical total or independence claim is rewritten.
All changes require integrated check0; firmware/bench/physical and owner process
qualification stay open. AGENTS section2 is unchanged.

## D-R15-01. Shorten fixed-anchor routes and escape IMU grounds outward

Full round15 reviewed committed789f4d5/PCB7866d6b8 with all1909 tracked files
frozen:0Critical/0Major/14consolidated Minor groups from20raw observations.
Adopt the fifteen exact fixed-anchor windows in round15_routing through the
R10 generators, preserving pads,part poses,widths,layers and vias. The combined
copy passes genuine DRC,reference,region and routing checks. It saves10.008727mm
and eight segments, but has140 information annotations versus139 and six
noncritical hygiene leftovers versus eight. Those counters are review evidence,
not an optimization objective or proof of globally shortest routing. Window1's
source-family label is corrected by root: its GND producer is pyro,not core;
the original report remains immutable. Preserve its rejected branch-bypass
sketch,copy-writer/probe failures and stated search limits.

[ST TN1383 Rev1 pp7–9](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf)
recommends component-side escapes outside the MEMS package to reduce stress.
Replace U4's two shared pad-row GND straps with individual outward escapes,
joining only at the existing GND vias(19.6,45.9)/(16.75,47.6),outside the nominal
body. Each escape follows its pad axis,then45degrees to its via. The initial
rectangular joins produced four blocking tiny jogs in the ground-stage gate;
reject that version and retain the actual routing rule. Keep all lands and the
B180 pose. The revised source deliberately adds1.544214mm/two GND segments;
it removes the under-body joins instead of trading sensor guidance for the
shortest GND trace. The source-only exact multiset is951segments/296vias,net
saving8.464513mm/six segments. Qualify the generated
result with native DRC,reference,region,fill and complete gates. Neither this
local correction nor M-7's narrower checks establishes complete TN1383 process
compliance or measured bias/thermal/vibration performance.

Refresh actual native budget,hot-plug,fab and record-only firmware provenance,
rebuild twice and check0. Because copper changes,fresh full rounds16/17 on the
committed result must earn the final same-board pair; earlier pairs do not
transfer. AGENTS section2 is byte-identical.

## D-R15-02. Retain bounded VCAP and terminal process qualifications

Fresh independent verifiers retain R15-MCU-01/R15-BOM-02 as Minor qualification
gaps,with no demonstrated required-limit failure. Their complete read-only
authored reports are round15_vcap_verification and round15_terminal_verification;
the authorized scribe persists the supplied bodies verbatim. Keep their actual
native-interpreter and primary-source scopes separate from the production build.

C19/C20 remain Samsung CL10A225KO8NNNC/C23630. Nominal2.2uF±10% meets nominal
selection. [ST DS12110 Rev11 Table114 p211](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
states2.2uF±20% and ESR<0.1ohm without resolving the relevant test conditions.
The numerical1.76–2.64uF interpretation remains to be closed for actual regulator
modes. Multiplying separate typical Samsung temperature/bias curves and initial
tolerance gives1.716525uF at70C/1V; it is an Inference,not a guaranteed joint
corner. The maker's biased-temperature example shows those factors need not
separate; AC amplitude,process and aging also matter. Obtain supported combined
bounds or qualify actual fitted parts,regulator modes,local temperature,aging,
both capacitance limits,ESR and startup/load transients. No larger nominal part
is prequalified:3.3uF±10% already exceeds2.64uF nominally. Retention is bounded
to the unqualified CAD candidate,not a regulator-stability claim.

Keep all23 DB125 contacts at nominal1.30mm holes/1.90mm lands. The maker's
0.50x0.85mm nominal section and1.20mm recommended hole do not close insertion
at all process corners. An independent sharp0.70x1.05mm envelope has diagonal
1.261943mm versus1.22mm minimum finished hole under JLC's stated−0.08mm bound.
The drawing's general-tolerance reference concerns moulded plastics; its metal
pin applicability,corner/form and relative pattern limits need clarification.
This is not a demonstrated insertion failure. Native S-8 minimum1.102501576mm
is nominal CAD: finished diameter,position,registration and outer barrel need a
fabricator allocation. Enlarging drills alone reduces annulus and S-8 reserve
without closing pattern/form/solder constraints. Obtain maker/assembler profile
and process allocation; validate all contacts on first articles. Revise generated
drills/lands and protected inner copper only if that allocation requires it,
with covered DRC/S-8/fill/thermal/fab/reproducibility checks. Primary sources and
bounded options are in the fresh verifier and parts_qualification records.

## D-R15-03. Bind BOM identity, model bounds and fill geometry; correct records

Extend S-4's existing production BOM walk to each native fitted part's LCSC,
canonical MPN and footprint. A correct population/quantity is insufficient when
R134's row can name R166's0.36ohm order identity. Preserve valid merged rows and
quantity-free CPL semantics. Add C84's reviewed normalized conservative model
envelope to the existing model guard; retain equivalent-unit positives. Compare
saved/refilled zone geometry using symmetric difference with the existing
0.01mm2 tolerance rather than area alone. Complete test copies retain their
project/rules. Native6 unchanged baseline difference is zero; native7's small
refill difference remains below that same tolerance. No interpreter migration,
fake CLI,actual rule relaxation or prior whole-gate escape is claimed. Genuine
old-fault/new-reject and valid native controls belong to round15_gate_fix.

Correct active decision/round/ledger pointers and completed integration states;
do not leave a perpetual precommit status merely to avoid a self-referential
commit hash. Bind current geometry by full PCB SHA and record known immutable
review targets separately. Preserve every earlier review/supplier execution at
its own source hash. Correct C431's current modeled h4 gap to0.270913mm.
Pack UVLO4.778382V is the25C resistor corner; ±100ppm/K gives4.811062V at70C
resistor temperature (the same absolute excursion at−20C). The125C4.851401V
sensitivity is outside the bay assumption; gradients,leakage,contact bounce and
transients remain unqualified. This changes no circuit or firmware threshold.

The exact82-code public supplier snapshot2026-10-30T13:13:17.644478 through
13:13:48.643735UTC gives79.5232USD placed/feeder share and81.3254USD including
minimum purchases,before fixed/process/PCB/shipping. U9 is123available/minimum1;
R43017<3610 and U4zero<5 remain stock blockers. Rebind original responses without
requery or a new supplier timestamp. Full quote,process and owner cost/deviation
acceptance remain pending; no order. Firmware,physical,thermal/transient,
harness/retention and first-article qualification remain open. AGENTS section2
is unchanged.

## D-R16-01. Validate the saved binding and honor exact-duplicate review scope

Full round16 on committed b1b8658/632a9ad3 found no Critical or Major. The
current saved binding is correct, but a genuine complete copied-project
check.sh also accepts a note with a zero board hash, wrong U1.3 net and reversed
roll sign. Compare the saved record with fresh native board-derived generation
without rewriting it. Reject missing, malformed or different evidence. The
note remains firmware evidence, never an approval or executable R10 firmware.
Generate it before the full build gate so that a newly generated PCB is checked
against its own record; do not add a skip or regenerate inside the checker.

Owner AUD-10 makes exact duplicate segments review annotations. A duplicate
of the actual13.2mm GPS_RX_MCU segment leaves the copper union unchanged but
incorrectly creates two blocking fold-backs and one loop. For R10 topology,
path-length and loop analysis, use one representation only when integer native
net, layer, unordered endpoints and width all match. Keep duplicate annotations
and every partial overlap, different-width overlap, crossing, genuine cycle and
connectivity rule. Regressions must evaluate the complete scan, with unchanged
native positives and actual negative controls. This corrects a false rejection;
it does not weaken physical copper requirements or other revision profiles.

Correct the stale active plan header and refresh exact current evidence links.
The82-code public supplier execution2026-10-30T15:30:06.601825 through
15:30:40.008183UTC gives79.5232USD placed/feeder share and81.3254USD with
minimum purchases. Rebind these original responses without changing their
supplier timestamp. Cost is below84.41; R43017<3610 and U4zero<5 still block
stock release. Quote, process and owner acceptance remain pending; no order.
No circuit, pin map, pad, placement, axis or AGENTS section2 change is made.

## D-R16-02. Preserve the same-board pair and cover the final bounded CAD delta

All1942 committed files remained byte-identical through all ten independent
round 16 lenses. Consolidation gives 0 Critical / 0 Major / 11 Minor groups from 17 raw
observations, five new and six carried. Correct gate/record Minors while
retaining PCB632a9ad3 for the fresh full round17. No Critical or Major is
deferred; the pair is earned only if the second complete round is also clean.

The SD_MOSI fixed-anchor alternative saves1.994603mm/two segments with unchanged
0.20mm width, layer, anchors and vias. Its genuine refilled native copy passes
DRC, reference, region and routing. Keep this isolated cleanup queued until the
same-board pair closes. Adoption must use the source generator, preserve its
exact native diagonal, rebuild twice with42-file byte comparison, rebind
electrical/fab/firmware evidence and pass the complete gate. Fresh independent
delta verifiers must inspect the exact removed/added geometry and its affected
interfaces and returns. The user's explicit final-board-change clause permits
this coverage; record both the full-round PCB and final PCB, without claiming
two full rounds on a changed successor. If a blocking change or incomplete
coverage remains, run another full round instead.

Round16 also identifies retained B.Cu component-side IMU_CS, SPI1_MISO, IMU_INT1
and 3V3A paths under U4 outside its lands: sampled centreline portions 0.7596 +
0.0918, 0.3257, 0.3250 and 0.3257 mm respectively. This specifically departs from
[ST TN1383 Rev 1 pp. 7–9](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf)
pad-axis / outside-body stress guidance. Existing M-7 / P3 passing is narrower;
no sensor offset or flight failure has been measured. Assess only bounded
outside-body escapes with unchanged pads, widths and vias; an initial supply
sketch fails clearance and is rejected. Any adopted alternative needs the
same exact-delta and build coverage. Otherwise retain these measured advisory
departures and first-article bias / temperature / vibration qualification explicitly.
No complete TN1383 or physical performance compliance is inferred. DB125
insertion / S-8 process allocation, VCAP combined-condition / ESR, L400 heel, drawing
residuals and the separately owned vehicle mirror remain bounded deviations.

The bounded MEMS source exploration is complete: its first supply T has only
0.106949 mm copper clearance and is rejected. The revised combined sketch
passes a local 0.16 mm screen but makes a 45 degree free IMU_CS branch at
B(14.2,44.7); reject it without changing the angle rule. Retain the present
signal / supply guidance departure explicitly. Exact interval lengths are 0.760 +
0.091923882 mm for CS and 0.325 mm each for MISO, INT1 and 3V3A, distinct from the
lens's0.001mm midpoint diagnostic. Neither is physical evidence. Different
0.20mm signal/0.25mm supply widths also depart from equal-width guidance.
The engineering task did not qualify refill, DRC, references or production
builds for this rejected recipe. Its durable record is round16_minor_prototypes.

## D-R16-03. Apply the supervisor's unchanged-board Minor disposition

The new supervisor steer2026-10-30, received after full round16 and before its
commit request, supersedes D-R16-02's queued post-pair CAD adoption:

> From now on: **do not change the PCB (`m3.kicad_pcb`, placement, routing,
> circuit generators) for Minors.** Fix round 16's Minors only where the fix is
> docs / checks / evidence with the board byte-identical (632a9ad3…); record
> every other Minor with its measured reason in "R10 deviations for owner
> acceptance". Commit round 16, then run round 17 on that same board. If round
> 17 is also 0 Critical / 0 Major, you are done: write the deviation list,
> STATUS.md and AGENTS.md rows, commit and report. Change the board only for a
> confirmed Critical or Major.

Retain PCB632a9ad3 and its circuit/placement/routing generators unchanged.
Cancel adoption of the qualified SD_MOSI alternative: its measured avoidable
1.994603mm/two segments remains an explicit M2 Minor for owner acceptance.
The retained MEMS signal/supply, L400 land, DB125 insertion/S-8 allocation,
VCAP operating conditions, drawing/return and vehicle-mirror deviations keep
their measured reasons. The rejected MEMS sketches and qualified ignored SD
copy remain evidence of bounded exploration, not an authorization to alter CAD.

The saved-binding gate, exact-duplicate checker semantics and record fixes are
allowed without a PCB change. One new full native build/check0 and a separate
standalone check0 reproduce the same42 generated files against both R15 builds;
all 32 rules and 180 R10 / 31 fit / 16 paste / 67 route tests pass, with all four NumPy skips
resolved. Full R16 remains 0 Critical / 0 Major / 11 Minor groups on committed b1b8658.
Commit these unchanged-board fixes, then fresh full R17 on the same PCB. If it
is also clean, finalize records/deviations and report; no subsequent Minor CAD
cleanup is planned. Any confirmed Critical/Major still requires fresh
verification and correction before qualifying completion. This changes no
AGENTS section2 rule, physics requirement, cost cap or owner acceptance state.

## D-R17-01. Use one explicit pad-energy basis

R17-PWR-02 demonstrates that D-CIR-02's retained 1.76Ah subtotal and camera
increment mix operating points. Preserve that dated decision as history; its
2.04/3.19Ah totals and generic 2.6/4Ah selections are superseded for current
planning. Do not add a repaired camera increment to the unreproduced subtotal.

Use the unchanged native upper allocations: port buck5.546269302559V,
camera1A when recording, GPS/radio/quiescent0.461A, unshed logic1.4W and SD
write3.3V*0.2A/0.8=0.825W. Preserve the existing conservative R92 loss allocation
7.4V squared/(3300ohm*0.98)=0.016933W. At the allocated80% converter efficiency,
camera input is 6.932837 W and the remaining board input 5.437970 W. Divide pad
energy by6V for the conditional capacity worksheet. Neither efficiency nor
device duty is a measured or maker-guaranteed bound.

| Two-hour board operation | Camera on | Board charge at6V | Board-only capacity leaving20% unused |
|---|---:|---:|---:|
| Continuous GPS/radio/unshed logic/allocated SD write | 0h | 1.812657Ah | 2.265821Ah |
| Same | 0.5h | 2.390393Ah | 2.987991Ah |
| Same | 2h | 4.123602Ah | 5.154503Ah |

These rows exclude motors, flight and recovery. Select tested usable capacity
with C_Ah >= (Q_pad_board + Q_pad_motors + Q_flight_all + Q_recovery)/0.8.
Independently satisfy aged/cold capacity, fire-time7.4V-equivalent source and
source resistance, transients and real bay fit. Keep camera off on the pad
unless recording. At nominal5.456V,6V/80%, the extra1.5h camera term is1.705Ah;
0.77A/1.155Ah is not the current common-corner calculation. No pack is released
by this worksheet. Source: unchanged r10_parts.py load/divider allocations,
Diodes AP63201 DS41326 Rev3-2 pp5/13, and round17_pad_energy.json. This is
Calculation/Inference, with no PCB, circuit-generator or AGENTS section2 change.

## D-R17-02. Qualify the boot address as well as BOOT0

Correct R17-MCU-02's active PA2 table and checker explanations. R5's10k pull-down
fixes BOOT0's sampled level; it does not fix BOOT_ADD0. ST [AN2606 Rev70
Table2 Pattern10 p35](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf)
permits ROM entry with BOOT0=0 and BOOT_ADD0=0x1FF0. The H74x/75x Table135 p321
identifies PA2 as loader USART2_TX; R152's1k and R156's10k do not hold a driven
servo3 output low. No actual option bytes or R10 firmware were programmed/read
here, and this does not demonstrate unexpected ROM entry on a qualified board.

Future R10 programming acceptance must record and read back the intended
user-flash BOOT_ADD0 and relevant boot settings, then verify reset enters the
bound application with the e-match disconnected. Retain serviced-ROM entry only
before IWDG starts, PC1/PE4 locked low, camera EN/OE low and SD_CS high, using
dummy loads. PC1/PE4 are not loader pins. Preserve all pin assignments and gate
predicates; refresh only table/binding provenance and the explanatory strings.
The current primary text was inspected; unavailable current PDF rasters are
not claimed as visual evidence. R10 evidence remains record-only and the R1
executable binding remains unqualified for R10. No circuit or safety-rule change.

## D-R17-03. Correct mechanical source labels while retaining allocations

For R17-MEC-04, retain the conservative1.1mm U5 model/cover allocation and its
2.9mm gap under a nominal4mm sled plane. Label it as engineering allocation.
[TE MS5611-01BA03 06/2017 p15 Fig18](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50)
specifies1.0mm +0/-0.10 package height; the native triangulated model measures
1.100074mm. Package-only clearance3.0mm does not qualify solder seating, foam,
adhesive, compression, venting or barometer response. No model/CAD change.

For R17-MEC-03/MFG-02, retain all16 courtyard graphic pairs, positions, separate
collision polygons and nominal body gaps. Correct active graphic penetration
to actual half-stroke sum0.050mm minus polygon gap0.010..0.040mm, giving
0.010..0.040mm penetration. Prior active cells used0.060mm and were0.010mm high.
The minimum nominal body gap is0.499938mm; no physical collision is established.
Keep assembler/owner first-article acceptance. Earlier report bytes/metrics
remain source-scoped history. No placement, routing or circuit-generator change.

## D-R17-04. Require canonical fabrication binding evidence

R17-GATE-01 establishes a prospective complete-gate gap: genuine copied-project
positive and only-manifest-deletion negative both exit0. The actual target's
five-output package is present and correct. Require its manifest during a
canonical repository-board full check; absence must fail. Preserve the explicit
documented build-stage mode and external-board-copy behavior. Add missing-file
sequence regression and validate an actual native copied-project negative,
then the complete canonical positive. Existing native checks and self-tests
remain required. This changes a checker, not PCB or circuit generators.

Full rounds16/17 have no confirmed Critical or Major on the identical committed
632a9ad3 PCB. Follow D-R16-03: retain measured SD/MEMS/L400/DB125/VCAP/M2 and
other CAD/process Minors. Finish records and the deviation ledger; no further
Minor CAD adoption is queued. Refresh procurement from the original17:15:34..
17:15:45UTC exact-code snapshot:79.5232USD placed/feeder,81.8636USD including
minimums; R43017<3610/U4zero<5 stock blocks, U9stock83/minimum7. Fixed/process/
PCB/shipping remain additional. Owner cost/deviation/process acceptance and
quote/order remain pending. AGENTS section2 stays byte-identical; no physical,
firmware or flight qualification is inferred.

**Supervisor handover, received before the final request (2026-10-30):** commit
completed round17 and its clean-round deviations/STATUS/AGENTS records through
`.supervisor/request.txt`, then stop and report. Do not start round18 or a new
board change. This reaffirms D-R16-03's closing boundary and adds no hardware
choice; it is attached as an amendment to the existing consolidated supervisor
mandate. The final index remains126 D-* IDs/23 mandate records.

## D-R18-01. Stiffen the PC1 bus-enable pull-down; remove the redundant 3V3 divider (2026-10-30)

Round 18 fix pass (R18-MCU-01, R18-SAF-03 circuit part, R18-REQ-08); CAD through the generators, two complete
builds. **R123** (ACT_EN to GND at Q122's gate) changes from 100 kohm (C25741) to **2 kohm 1 % 0402, UNI-ROYAL
0402WGF2001TCE, LCSC C4109**, the BOM line already fitted for R130/R133/R178/R180; same R0402 land at F(20.6,70.66)
-90 degrees, no copper change. With PC1 high the Q122 (AO3400A) gate is VOH x 2k/(1k+2k): 2.19 V at VDD 3.3 V and
1.92 V at the [DS12110 Rev 8](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) Table 61 p141 CMOS floor
VOH >= VDD-0.4 V with 1 % resistor tolerance (r10_parts native budget; VOH is specified at -8 mA, PC1 now sources
1.1 mA). [AO3400A Rev 3.1 p2](https://www.aosmd.com/res/datasheets/AO3400A.pdf):
VGS(th) 0.65/1.05/1.45 V; RDS(on) <= 48 mohm is specified only at 2.5 V. That Q122 saturates at 1.92-2.19 V is
Inference from its load: R121 10 k plus R119 || R120 (50 k, D-R18-02) from ACT_FET_S, <= 0.143 mA. The P-FET
gate then sits at about -V_S x 50/60 (-6.17 V at 7.4 V); the budget's settled worst-case |VGS| goes 5.19 -> 4.74 V
and its time to -4.5 V 23.6 -> 31.9 ms, against [AONR21357 Rev 2.1 p2](https://www.aosmd.com/res/datasheets/AONR21357.pdf)
VGS(th) -1.3/-1.7/-2.3 V and RDS(on) <= 12.3 mohm at -4.5 V (pin_table keeps the >= 100 ms enable-to-check wait).
Off-state dominance (Calculation): a PC1 weak pull-up (RPU 30/40/50 kohm, DS12110 Rev 8 Table 60 p139) now gives
ACT_EN <= 0.220 V (was up to 2.75 V); a BAT_FAULT_N bridge (R89 10 k to 3V3) <= 3.6 x 2/13 = 0.554 V (was 2.97 V);
both below VGS(th) min 0.65 V. The native budget (parts_budget.json load_switch_AUD3: Q122_gate_on_V_nominal_and_
VOH_floor, Q122_gate_with_30k_pullup_PC1_unconfigured_V, Q122_drain_load_max_A), check_actuators and S-3 pin the
2 kohm value. The four-stall CH1 fire current moves 1.283013 -> 1.282918 A with D-R18-05's longer IGN run
(above the 1.125 A J-Tek floor; Calculation, native copper).

**V3V3_SENSE removed.** R62/R63 (10 k/10 k) divided 3V3 into PC3_C. The ADC reference VREF+ (U1.20) and VDDA
(U1.21) are 3V3A, fed from 3V3 through R164 2.2 ohm (C22939), so the pin read about half scale whatever 3V3 was:
it carried no 3V3 information beyond what VREFINT/VREFIN_CAL (DS12110 Rev 8 Tables 28-29 pp111-112) and the
internal VBAT/4 channel with VBAT tied to 3V3 (section 3.19 p37, Table 94 p180) give. circuit.json lists R62/R63
as removed; the schematic, placement (r10_place.tsv), routing (r10_route_signals) and Fab-reference table drop them;
U1.18 PC3_C is NC in pin_table.tsv and the binding note; check_r10 (REQUIRED_FITTED / REMOVED) and r10_sch_check's
obligations follow. Before -> after: R123 100k -> 2k; V3V3_SENSE copper present -> absent (it also removes the
V3V3_SENSE via that sat 0.251 mm from ACT_EN_MCU); footprints 209 -> 208 with D-R18-02's R119.

## D-R18-02. Give Q121 its own via-free gate-source resistor (2026-10-30)

R18-SAF-02. Before: Q121.4's B.Cu island (Q121.4, the via at (11.800,70.725), TP121 at B(10.5,71.5)) reached
R120/C120 only through two single vias and F.Cu at R121, so one open via left Q121, the forward-blocking FET,
without off-bias. After: **R119 100 kohm 1 % 0402 (UNI-ROYAL 0402WGF1003TCE, C25741, R120's BOM line)** at
B(11.57,71.1) 0 degrees: Q121.4 -> (11.14,70.0) -> R119.1 -> via (11.14,71.7) and R119.2 -> (12.525,71.1) on the
ACT_FET_S source bridge, all B.Cu with no via between Q121's gate/source pads and R119. TP121 moves to B(4,70)
between J400 and J1 on a B.Cu stub along y = 70.0 (M-6 1.5 mm and the test-pad 1.0 mm clearances hold). R119 || R120
= 50 kohm on the shared ACT_GATE node (C120 1 uF, R121 10 k); the gate drive is in D-R18-01. New S-3 sub-rule
`local_gate_bias`: each load-switch P-FET's gate and source pads must each reach a pad of one 1 k - 100 k
gate-source resistor through copper on the FET's own layer alone (`same_layer_islands`; a layer change never
joins). R17 board: Q121 fails; this board: Q120 -> R120, Q121 -> R119. Tests:
`Synthetic.test_s3_local_gate_bias_needs_same_layer_copper`, `RealBoardSeeds.test_r18_q121_local_bias_seed`.

## D-R18-03. Space the PC1 enable run from reset-high nets (2026-10-30)

R18-SAF-03 (geometry). ACT_EN_MCU F.Cu runs (24.5,51.6) -> (26.62,53.72) -> (26.62,65.344) -> (24.764,67.2) ->
(21.77,67.2) -> R122.1 (was x 26.5 and (26.5,66.0) -> (25.3,67.2)). BAT_FAULT_N F.Cu moves east to x 27.37
((26.9,52.45) -> (27.37,52.92) -> (27.37,65.655) -> (23.85,69.175)), still one 45-degree run to R89.2. U11.12's GND
fan-out via (25.8,65.9) leaves the corridor (r10_fanout.tsv row removed; U11.12 joins C99.2's return at (25.8,66.9)).
Measured edge gaps, before -> after: ACT_EN_MCU-BAT_FAULT_N 0.171 mm (0.200 mm along 12.4 mm) -> 0.550 mm;
-V3V3_SENSE via 0.251 mm -> net removed (D-R18-01); -BUZZ_OUT pad LS120.2 (3V3 through the buzzer coil, so a strong
source) 0.400 -> 0.520 mm; -USB_LIMITED via 0.550 -> 0.670 mm. Remaining enable-chain neighbours under 0.5 mm:
U1.15/U1.17 pin pitch 0.200 mm (package), the NRST via 0.425 mm (a weak pull-up: <= 0.22 V at ACT_EN with 2 k),
GND 0.251 mm (fail-safe) and ACT_EN-BAT_ENABLE 0.330 mm at R123.1, unchanged: a bridge loads U9's 470 kohm-fed EN
with R123's 2 k, so U9 stays off (fail-safe; Calculation).

## D-R18-04. Keep inner-layer copper 1 mm from the load-switch gate and enable barrels (2026-10-30)

R18-SAF-01 / R18-GATE-01. `r10_route_ground.barrel_keepouts` places a fill-only rule area (16-gon, circumscribed,
radius drill/2 + 1.05 mm, named R18_BARREL_KEEPOUT_<net>_<i>) round every drawn plated via or pad barrel of ACT_GATE
and ACT_DRV on In1 and In2 (GND turns the P-FETs on) and of BAT_ENABLE, BAT_SW_RETURN, ACT_EN, ACT_EN_MCU and
PYRO1_GATE_N on In2 only (In1 GND holds U9, Q122 and Q124 off). Barrels present: ACT_GATE vias (16.2,73.3) and
(11.14,71.7); BAT_ENABLE vias (19.675,66.4), (21.3,68.9), (17.1,82.8); the J400.2 hole. ACT_DRV, ACT_EN, ACT_EN_MCU
and PYRO1_GATE_N have no barrel. Barrel wall to foreign inner copper, before -> after: ACT_GATE In1 GND 0.251 ->
1.050 mm and In2 RAW_PROTECTED 0.251 -> 1.050 mm at both vias; BAT_ENABLE In2 RAW_PROTECTED/3V3 0.251 -> 1.050 mm at
all three (In1 GND 0.251 mm kept: fail-safe); J400.2 In2 RAW_PROTECTED 0.551 -> 1.050 mm and In2 GND 0.850 -> 1.050
mm (In1 GND 0.551 mm kept). In2 RAW_PROTECTED fill 1253.99 -> 1222.74 mm^2. **S-8** now covers these seven nets
(`BARREL_NETS`) and counts GND as foreign for `BARREL_GND_HAZARD` = {ACT_GATE, ACT_DRV}. Tests:
`R3Synthetic.test_s8_load_switch_gate_and_enable_barrels` (the R17 0.251 mm GND geometry at an ACT_GATE barrel
fails, 1.101 mm passes; GND beside BAT_ENABLE passes, RAW_PROTECTED there fails) and
`RealBoardSeeds.test_r18_barrel_keepouts_removed` (disabling the areas and refilling restores R17's 0.251 mm on
this board and S-8 fails). AGENTS section 2 is unchanged.

## D-R18-05. Keep the CH1 sense branches off the fire-current pads (2026-10-30)

R18-SAF-04. R173 (5.1 k, CONT divider top) moves from B(23.0,59.2) 90 degrees to **B(16.87,59.7) -90 degrees**, at
the OUT end: PYRO1_OUT B.Cu now ends at R173.1 ((10.37,56.6) -> (15.5,56.6) -> (16.87,57.97) -> R173.1), and the
corridor between R134.2 (RAW_ACT) and Q123.1 (BUZZ_G) carries PYRO1_CONT_MID behind R173 (R173.2 -> (16.87,61.8) ->
(20.83,61.8) -> (23.0,59.63) -> R129.1, drawn in r10_route_signals.buzzer after the gate lead and BUZZ_OUT via that
bound it, so the per-family gate judges it in place). The IGN 0.5 mm diagonal moves 0.5 mm south-west ((7.4,59.9)
-> (11.5,64.0)); BUZZ_G's west lead moves 0.25 mm east to x 17.75 (0.15 mm from Q123.2); C126.2's GND fan-out via
moves along its own 45-degree stub from (16.178,59.047) to (15.8,59.425). Measured, before -> after: OUT-R134.2 0.250
-> 2.825 mm; OUT-Q123.1 0.175 -> 1.577 mm; OUT-BUZZ_G track 0.510 mm; OUT-3V3 (D120.3) 0.514 mm; OUT-C126 GND via
0.550 mm; IGN-R131.1 (OUT) 0.222 -> 0.575 mm. Retained and recorded: MID-R134.2 0.250 mm and MID-Q123.1 0.175 mm. A
RAW_ACT bridge to MID passes at most 8.4 V/5.1 kohm = 1.6 mA through R173 (no R134 or e-match bypass); it raises the
CONT reading to 8.4 x 1/6.1 = 1.38 V against about 0.75 V intact, which a firmware upper bound can flag (Inference).
A BUZZ_G bridge puts at most MID = 0.545 x OUT, about 4.6 V, on PC14 through R162 1 kohm, inside FT VDD + 4 V.
OUT-GND 0.177 mm (via (15.85,57.70)) and Q124.5-GND via 0.180 mm are unchanged (the owner-accepted default-clearance
class).

## D-R18-06. Fill the In2 3V3 plane as one piece and gate it (2026-10-30)

R18-RTE-01 / R18-PWR-01. IN2_GND_CH1 loses the tongue (x 17.45-24, y 59.0-62.3) that only R17's PYRO1_OUT crossing
needed (D-R18-05); IN2_3V3 gains a shoulder (x 20.5-22, y 61.5-64.0) and a bay (x 23.7-27.2, y 61.5-64.6), so both
In2 USB_LIMITED via ends (22.0,62.25) and (25.6,63.0) lie inside the 3V3 fill; IN2_RAW is notched to match. The In2
USB_LIMITED route and the 3V3A trunk under U1 are unchanged. Measured: the 3V3 In2 fill was three pieces (1354.23 /
63.11 / 30.54 mm^2; island A and the finger each had 0 links of >= 0.5 mm outer copper, island A only R17's 0.3 mm
B.Cu link) and is now **one piece, 1466.52 mm^2**; by polygon deflation the narrowest fill neck joining the former
island A is about 0.55 mm and the former finger's about 0.50 mm (approximate). New rule **K-plane**: every non-GND inner power fill must be one
piece, or each residual piece needs >= 2 links, each an outer-layer path of >= 0.5 mm tracks, pads and vias from a
via or plated pad landing in it to one landing in another piece (GND regions on In2 are separate by design). R17
board: 2 K-plane issues; this board: 0. Tests: `R3Synthetic.test_k_plane_split_fill_needs_two_links` and
`RealBoardSeeds.test_r18_split_power_plane`.

## D-R18-07. Straighten SD_MOSI (2026-10-30)

R18-RTE-04. B.Cu 0.2 mm (20.1,32.8) -> (25.005,27.895) -> (25.005,24.3) replaces (20.1,32.8) -> (20.1,27.7) ->
(21.6,26.2) -> (25.005,26.2) -> (25.005,24.3) (r10_route_sd.py; the J430 offset DX is 0 on this placement, so the
corner is round 16's qualified (25.005,27.894999) within KiCad's 1 nm grid). SD_MOSI copper 36.098 -> 34.104 mm
(-1.995 mm), 12 -> 10 segments; DRC, route_check, K-reference and K-region pass.

## D-R18-08. Bourns land for L400; 0.15 mm mask webs on U4 (2026-10-30)

R18-BOM-03: `r10_parts.srp5030t()` now generates M3_SRP5030TA from
[Bourns SRP5030T p1 "Recommended Layout"](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf) (6.50 mm
over both lands, 2.50 mm inner gap, 1.8 mm land height): pads 2.0 x 1.8 mm at x = +/-2.25 mm (asserted). L400 pads
1.8 x 2.5 mm at +/-2.35 mm (2.90 mm inner gap) -> 2.0 x 1.8 mm at +/-2.25 mm (2.50 mm gap, 6.50 mm outer); its
PORT_SW / PORT_5V3 entries follow the pad centres; jlc_orient's EasyEDA proxy residual goes 0.15 -> 0.05 mm.
R18-MFG-02: the LSM6DSV320X LGA-14 footprint's solder-mask expansion 0.025 -> 0 mm, so the webs between its
0.35 mm lands at 0.5 mm pitch go 0.100 -> 0.150 mm; the paste stays -3 % per axis (0.5405 x 0.329 mm, 88.4 % of the land), inside
[ST TN1383 Rev 1 p6](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf)'s
70-90 % stencil range; TN1383's "land + 0.1 mm where applicable" mask opening would leave no web at this pitch.
`r10_pcb.sync_lands` copies only the pad mask/paste margins from the library to the retained R9 U4 instance and
asserts that its pad numbers, positions, shapes and sizes already match.

## D-R18-09. Stocked R430; C84 hand-fitted outside the JLC upload (2026-10-30)

R18-BOM-01: R430 (CAM_ILIM, B(36.0,60.0), 0603, nonpolar, land unchanged) changes from YAGEO RC0603FR-0722K6L
C185349 (stock 17, minimum 3610) to **FOJAN FRC0603F2262TS, LCSC C2999509**: 22.6 kohm +/-1 %, +/-100 ppm/C,
100 mW, 75 V, thick film, -55..+155 C, JLC extended, stock 84,923, minimum 1, $0.0021 (live JLC component query
2026-10-30T21:53Z; LCSC page https://www.lcsc.com/product-detail/C2999509.html). circuit.json, the schematic
fields, check_r10's pinned identity and tools/jlc_easyeda/pads.json follow. R18-REQ-10 / R18-MFG-06: C84
(MA25V470M8x10) stays on the schematic and board but `export_fab.MANUAL_FIT` routes it to the owner BOM
(m3_bom_owner.csv, "manual, after both reflow passes (docs/ORDERING.md section 8.2)") and out of the JLC BOM and CPL;
`jlc_orient --verify-cpl` and S-4 (`MANUAL_FIT`, owner-BOM check) agree, so a C84 row in the JLC upload, or a
missing owner row, fails (`RealBoardSeeds.test_r18_manual_fit_c84_s4`). JLC BOM 82 -> 81 lines, CPL 199 -> 197 rows.
Refreshed supplier evidence on this package (`FAB_NET=1 m3_design/r10_fab.sh`; stock_check.json 2026-10-30T23:50:54Z,
cost_check.json 23:51:50Z, exact codes): the only short line is U4 (0 < 5, consigned per ORDERING section 1); U9 45,
R430 84,923 (minimum 1); $79.12/board placed plus feeder share for 81 charged codes and $54.33/board parts with
minimum purchases (the R430 3610-piece minimum is gone), against the $84.41 target before fixed, process, PCB and
shipping costs; C84 is an owner purchase (about $0.28/board). Not a release pass: stock changes daily.

## D-R18-10. Correct generated schematic and pin-record text (2026-10-30)

R18-REQ-01, R18-REQ-02, R18-SAF-05, R18-MCU-03; text only, no copper. r10_sch.py replaces the R9 MCU notes with the
R10 map (CAM_PWR_EN PE11/pin41, CAM_FAULT_N EXTI12 PE12/pin42; UART5 PB12/PB13 radio; the loader-driven pins SERVO3
PA2, VLOGIC_SENSE PA6, SD_MISO PC11, USB PA11/PA12, QSPI_NCS PB6 and I2C1_SDA PB9, matching K-loader) and asserts
the pins it names; battery_entry names the switch contact J400.1 / J400.2 (BAT_SW_SOURCE / BAT_SW_RETURN) and R166
0.36 ohm; the stale M3_GH_BM04B_GHS_TBT footprint filters are dropped. pin_table.tsv: PE4 (pin 3) is an
ACTIVE-HIGH fire command (ODR low before output mode, GPIOE_LCKR locked, no pull-up, R127/R126/R128/C126 reset
contract: gate <= 0.104 V against a 30 kohm pull-up); PC1 (pin 16) carries R123 2 k; PC3_C (pin 18) is NC. The
binding note is regenerated from the finished board.

**Follow-up text pass (after `acba196`; records only, PCB unchanged at `a3144b15…`).** The docs lane's leftovers
(`round18_fix_docs.md`, reconcile item 11), with no build and nothing that writes the board:
- `pin_table.tsv` pin 33 (PC5, mode now "ADC (ADC12_INP8)") says what it is: the bus sense, the sole RAW_ACT pyro-bus
  reading behind Q120 / Q121 (PC0 is the continuity sense). ARM1_SENSE is a net name kept from R9; R10 has no ARM
  link. The note also names the divider: R132 and R175 (5.1 kohm each) over R133 and R180 (2 kohm each), with C129
  (10 nF).
- Pins 51, 52, 63, 64 and 78 to 81 are respaced, e.g. "R460 (10 kohm) to 3V3". The UART rows also name their
  1 kohm resistor and ground-only ESD diode (R450 / D421, R451 / D420, R441 / D410, R440 / D411).
- The TX pins 52 (PB13) and 63 (PC6), and the binding note's start-up rules, now say that TX idles high only while
  the GPS / radio ports are powered (battery path on). On USB-only power the modules are unpowered, so firmware parks
  PB13 / PC6 as inputs (no pull) or drives them low. This prevents back-feed into a module through the 1 kohm.
- Pin 3 (PE4) wording rechecked: active-high fire command, ODR written low before output mode, GPIOE_LCKR lock and
  read-back. The reset contract now carries its values (R127 1 kohm, R126 220 ohm, R128 10 kohm, C126 220 nF; gate
  <= 0.104 V against a 30 kohm pull-up at 3.6 V) and the
  [AON7524 Rev 1.1 p. 2](https://www.aosmd.com/res/datasheets/AON7524.pdf) 0.4 V minimum threshold.
- Pin 18's cite is respaced to match the binding note.

DS12110 cites are harmonised. The binding note now cites the same Rev 11 tables as the pin table:
- USART6 AF7 is Table 10 p. 92 and UART5 AF14 is Table 10 p. 91 (pins 63-64 and 51-52). They were Rev 10 Table 12
  p. 91 and Table 11 p. 90.
- PC13 / PC14 / PC15 at ±3 mA is Table 149 p. 244, and the 2 MHz limit is Table 150 note 2 p. 246 (pin 8). They
  were Rev 10 Table 62 p. 141 and Table 63 note 2.

The pin table's Rev 11 "Table 10" was checked rather than copied. In the cached Rev 8 (April 2021) the eleven port
alternate-function tables are Tables 10 to 20: Port B is Table 11 (PB12 / PB13 AF14 UART5 on p. 91), Port C is
Table 12 (PC6 / PC7 AF7 USART6 and PC10 to PC12 AF6 SPI3 on p. 92), read from the page images. Every Rev 11 table
cited after them is exactly ten lower than its Rev 8 table:
- voltage characteristics 119 -> 109;
- general operating conditions 122 -> 112;
- LSI 146 -> 136;
- I/O static characteristics 157 -> 147;
- PC13 to PC15 output voltage 159 -> 149;
- output timing 160 -> 150.

The Rev 11 Table 9 pages cited match Rev 8's to within a page. Both facts fit Rev 11 merging the port tables into
one Table 10 on the same pages, so the pin table's Rev 11 numbers are kept (Inference: Rev 11 itself could not be
downloaded here). The VREFINT / VBAT cites stay Rev 8 in both pin 18 and the note.

The binding note was regenerated by the record step (`r10_sch_check.py --binding-note`):
- `pin_table_sha256` ca5a4af4… -> ae686cd1…;
- the pin 3 and pin 33 modes;
- three port states, the fire-timing basis and eight obligations.

The board, netlist and circuit hashes are unchanged. `r10_sch.py` reads only the pin and net columns, so no sheet
changed. Checks run:
- the `r10_sch_check` gate: OK, ERC 0, 34 / 34 seeds, sheets and netlist reproduce byte for byte;
- `check_r10 --only K-binding,K-contract,K-loader`: OK;
- `kicad-cli` 10.0.7 ERC 0, and DRC 0 / unconnected 0 / schematic parity 0;
- the binding-note content and evidence tests: 5 OK.

## D-R18-11. Harden the gate (R18-GATE-02 to -09, R18-MEC-01 / -03) (2026-10-30)

Checks only, by the round 18 gate lane (`../r10_review/round18_fix_gate.md` / `.json`). The PCB is unchanged at
`a3144b15…`. The fab package was rebound: the Gerber zip, both PDFs and the manifest changed; the BOM, owner BOM, CPL
and `tools/jlc_corrections.json` are byte-identical. What each gap now checks:
- **Board identity and the skip flag (R18-GATE-05).** `check.sh` recognises the repository board by file identity
  (`[[ "$BOARD" -ef "$CANON" ]]`, device and inode), not by a path string, and a missing board fails before any
  stage. `R10_SKIP_FAB_MANIFEST` and its `unset` are removed, which for R10 supersedes the build-stage skip clause
  (recorded in D-R8-02's gate list; the gate hand-off cites it as D-R8-03).
- **Fab binding after content checks (R18-GATE-04).** `export_fab.py` no longer writes the manifest: it deletes any
  old one and, with `--pending RECORD`, records the export. `m3_design/r10_fab.sh` exports with `--pending`, then
  `fab_manifest.py --bind RECORD` runs the content checks before binding: check_r10 S-4 `--bom / --cpl`,
  `jlc_orient --verify-cpl` and `paste_check`. It writes the manifest only if all three pass and neither inputs nor
  outputs changed since the export. `check.sh` runs `fab_manifest.py --content` (the binding plus the same three
  checks) on the repository board. It also runs `test_fab_validation.py`: 34 tests; R9's GH J9 case is retired, and
  R10's J3 shell tabs and J430 nails are seeded instead.
- **K-power (R18-GATE-02 / -03), new rule.**
  - U9 IN path, J1.1 to U9.5 through C88.1: floor 1.0 mm (S-9's BAT_IN floor); at least one via of >= 1.0 / 0.5 mm.
  - U9 OUT path, U9.6 to its In2 vias: floor 0.7 mm; at least two vias of >= 0.5 / 0.3 mm joined to the In2
    RAW_PROTECTED fill.
  - Exactly six named `POWER_NARROW` entries are allowed: two 0.3 mm bar entries, three C88-local 0.7 mm runs and the
    0.4 mm via link. A stale entry fails.
  - `FIRE_RETURN`: Q124 source pads 1 to 3, tracks >= 0.3 mm, at least two In1 GND vias of >= 0.5 / 0.3 mm.
- **K-lands (R18-GATE-09), new rule.** `fp-lib-table` is exactly `rocket` -> `${KIPRJMOD}/kilib/rocket.pretty`.
  Every board footprint comes from it and is either generated by r10_parts (9, held by `r10_parts --check`) or
  SHA-256-pinned in `FOOTPRINT_SHA256` (37 files). Unpinned and stale entries fail.
- **M-3 support centres (R18-GATE-07).** The five Edge.Cuts circle centres are pinned to `SUPPORTS_R10` (4, 4),
  (42, 4), (4, 44.3), (3.7, 86) and (42, 86) within 0.01 mm; any other circle fails.
- **K-legends word identity (R18-GATE-08).** IGN, BAT, SWITCH, CAM, SWD, SERVO, GPS and RADIO each appear exactly
  once. Each must sit nearer its own connector's courtyard than any other connector on its face, by > 0.01 mm. Only
  named `WORD_SEAMS` ties are allowed, and stale seams fail.
- **Text floors (R18-GATE-06).** K-rules `PRO_FLOORS` adds `min_text_height` 1.0, `min_text_thickness` 0.15,
  `min_silk_clearance` 0.15 and `min_resolved_spokes` 2, so DRC's text checks hold every silkscreen text.
- **STRAIN_PARTS and wire rooms (R18-MEC-01 / -03).** `plate_model.STRAIN_PARTS` adds J410, J420, J9, J400, C431,
  C421 and C411. `fit_check.wire_rooms()` reports and prints every DB125 terminal: all seven have 5.003 to 5.603 mm,
  against P-11's 4.95 mm floor.

Each gap has a seeded regression. The gate lane's `check.sh` exits 0 in two runs:
- check_r10: 35 rules (33 + K-power + K-lands);
- fab: content checks 3 / 3, manifest 6 outputs;
- self-tests: shell 10, procurement 20, fab_validation 34, fit 33, paste 16, r10_parts 5, route 67, R10 201
  (5 native NumPy skips), and NumPy `HotplugNumerics Plate` 5.

The historic `m3_design/r8_fab.sh` / `r9_fab.sh` were not edited. Because the export no longer binds, they now stop
at their manifest check: they fail closed on this branch.

Open items:
- SWITCH has two sources. `r10_post.py` places it from its own `('J400', 'SWITCH')` beside `WORD_LEGENDS_R10`, and
  check_r10 adds it to that list as `WORD_SUBJECTS_R10`. Adding it to `WORD_LEGENDS_R10` would place it twice. One
  list should become the source.
- RADIO sits on the J410 / J420 seam. Its ink box is 0.000 mm from both courtyard boxes, which are 0.09 mm apart; by
  polygon or pad distance it is about 0.02 mm nearer J410. It is the one named `WORD_SEAMS` tie, and its legibility
  is a review call.
- R150 to R155 are not in `STRAIN_PARTS`.
- There is no width floor for VLOGIC / PORT_5V3 / CAM_5V / PORT_4V8 / 3V3 (the other rails of R18-GATE-02).
- An OUT via without In2 fill is seeded only synthetically.

The record index is now **137 unique D IDs through D-R18-11**.

## D-R19-01. Keep In1 / In2 GND 1 mm from the PYRO1_OUT barrels (2026-10-30)

Round 19 CAD fix pass (R19-SAF-01, R19-SAF-05; `../r10_review/round19_fix_cad.md`). PYRO1_OUT is Q124's drain, so a
short from OUT to GND bypasses the fire FET and, with the bus enabled, fires the match (about 1.5 A): unlike the bus
nodes, GND is a hazard there. `r10_route_ground.BARREL_KEEPOUT` adds `PYRO1_OUT: (In1, In2)`, giving the OUT via
(11.630, 55.100) and the J121.1 hole the round 18 fill-only 16-gon (drill/2 + 1.05 mm: radius 1.20 / 1.70 mm), and
`check_r10.BARREL_GND_HAZARD` adds PYRO1_OUT, so S-8 counts GND there. Measured wall to foreign inner copper, before
-> after: OUT via In1 / In2 GND 0.251 -> 1.021 mm (the nearest is now the ring of OUT's own GND partner via
(10.3, 55.6), 1.42 mm centre to centre, so the 1.5 mm partner rule still holds); J121.1 In1 / In2 GND 0.551 -> 1.050
mm, its own inner ring to GND 0.251 -> 0.750 mm. Every other S-8 barrel is as round 18 (ring and wall table in the
hand-back). A 0.5 mm opening leaves In1 GND and In2 GND_CH1 one piece each; near the new voids it removes only corner
cusps of <= 0.04 mm^2, so no inner neck below 0.5 mm is new. The voids leave PYRO1_OUT's own F.Cu and B.Cu runs
unreferenced next to its barrels (758 K-reference samples and one K-region run on the first scratch build): S-8 forbids the
copper K-reference asks for there, so `check_r10.own_barrel_voids` exempts a BARREL_GND_HAZARD net's own samples
within drill/2 + 1.071 mm of its own barrels (the 16-gon's corner reach); every other net's samples over the voids are
still taken (no fast net crosses them). Tests: `R19Gate.test_r19_s8_gnd_is_a_hazard_at_pyro1_out`,
`R4Synthetic.test_r19_own_barrel_void_is_exempt_for_hazard_nets_only`, `RealBoardSeeds.test_r19_pyro_out_barrels_clear_gnd`.

## D-R19-02. Move the R81 BAT_ENABLE via off R134.2 (2026-10-30)

R19-SAF-02. The BAT_ENABLE via (19.675, 66.4) moves to (19.675, 66.6); its F.Cu stub runs to 66.6 and the B.Cu run
is (19.675, 66.6) -> (21.0, 67.925) -> (21.0, 68.6) -> (21.3, 68.9), as the reviewer measured. BAT_ENABLE to R134.2
(RAW_ACT; once the bus is on, a leak there holds EN on) 0.300 -> 0.500 mm; the via's In2 RAW_PROTECTED wall stays 1.050
mm (S-8) and In2 GND 0.994 -> 1.123 mm; In1 GND 0.251 mm is kept (fail-safe: holds U9 off). Not changed: U9.1 (EN) to
BAT_IN under the QFN is 0.200 mm, fixed by TI's RPW land and pin order (EN beside IN; SLVSFC9C pin table), and the
BAT_ENABLE via (17.1, 82.8) to BAT_FAULT_N 0.200 mm sits inside U9's fan-out; neither opens without moving U9's
pins. Both stay recorded leak paths for the coating and per-flight checks R19-SAF-02 asks the docs lane to state.

## D-R19-03. Remove TP121 and its ACT_GATE stub (2026-10-30)

R19-SAF-03 / R19-RTE-02. TP121 (B(4, 70)) and the 7.14 mm B.Cu stub (11.14, 70.0) -> (4.0, 70.0) are removed
(circuit.json `removed_refs`, r10_place.tsv, r10_route_pyro, r10_post's Fab table). ACT_GATE is probed at R119.1 or
R120.2 (bare pads in the same cell, before coating). ACT_GATE outer copper within 0.30 mm of GND 12.896 -> 7.996 mm
(this lane's sampling; the reviewer's 12.872 -> 7.629); ACT_GATE to BAT_SW_SOURCE 0.400 -> 0.470 mm. check_actuators'
r10 ACT_GATE membership drops TP121.1 and rejects any part named TP121; check_r10 lists TP121 as removed.

## D-R19-04. Give Q122 its gate-source capacitor (2026-10-30)

R19-SAF-06 (AGENTS 2.4 for the load-switch enable FET). **C123 10 nF 50 V X7R 10 % 0402, Samsung CL05B103KB5NNNC,
LCSC C15195** (C408's BOM line, Basic) at F(18.22, 71.85) 0 degrees: pad 1 (ACT_EN) straight below Q122.1 on a 1.1 mm
F.Cu run, pad 2 (GND) to R123.2's fan-out via (19.967, 71.09) by (19.207, 71.85) -> 45 degrees; courtyard clear of
Q122 (0.085 mm) and D8. Gate node (Calculation): R122 || R123 = 667 ohm, 10 nF + AO3400A Ciss 630 pF typical
([AO3400A Rev 3.1 p2](https://www.aosmd.com/res/datasheets/AO3400A.pdf)): tau 7.1 us, VGS(th) max 1.45 V reached
7.6 us after PC1 rises, below VGS(th) min 0.65 V 8.6 us after it falls and 26 us after a reset (R123 alone). Both are
microseconds against the load switch's millisecond C120 network and D-SS-04's >= 100 ms wait; the fire path (PE4,
Q124) and the GAP-5 budget are untouched. A 7.4 V step on Q122's drain couples about 35 mV into the gate through Crss
50 pF (0.54 V without C123; Inference from the typical capacitances). S-3 now requires C123 (10 nF, ACT_EN to GND) and
ACT_EN = {R122, R123, Q122, C123}; check_actuators pins C123's value, code, land and nets. Nearest foreign copper:
R122.2 (ACT_EN) to the C123 GND run 0.436 mm, C123.1 to the F.Cu GND fill 0.251 mm (both fail-safe: GND holds Q122 off). Tests:
`Synthetic.test_r19_s3_q122_gate_source_capacitor` (the synthetic S-3 fixture now carries C123),
`RealBoardSeeds.test_r19_load_switch_enable_cap_and_removed_probe`.

## D-R19-05. No pour connection on U1.19 (2026-10-30)

R19-RTE-01. `r10_pcb.py` sets U1 pad 19 (VSSA) to `ZONE_CONNECTION_NONE` on the board (a pad override; the library
footprint is unchanged and DRC's library comparison stays clean). U1.19 keeps its own fan-out stub and via
(26.0, 46.75); the via-less 1.693 mm^2 F.Cu GND fragment that hung on its pin tip (x 25.12-27.15, y 51.24-53.45) is no
longer filled.

## D-R19-06. One word list; GPS and RADIO inside their own terminal's span (2026-10-30)

R19-MFG-01, R19-GATE-06 and the coordinator's additions. `check_r10.WORD_LEGENDS_R10` is the one list (SWITCH last,
where r10_post placed it); `WORD_SUBJECTS_R10` and r10_post's own `('J400', 'SWITCH')` are gone, and r10_post's
final self-check now runs `check_r10.word_legends`. `WORD_SEAMS` is empty. New K-legends rule (D-R19-06): GPS and
RADIO, the only names of the identically pinned J410 / J420, lie inside their own courtyard's y-span by >= 0.5 mm.
r10_post places RADIO, BAT and IGN at reviewed `WORD_SPOTS` (free-spot and reach checked); every other word keeps its
search spot. Every word stays at the same end of its own terminal. Centre of the ink box to the own / nearest other
connector courtyard box (mm) and the ink-gap margin, before -> after:

| Word | Own | Centre: own / nearest other | Ink-gap margin | Inside own y-span | Spot |
|---|---|---|---|---|---|
| RADIO | J420 | 2.130 / 2.051 J410 -> 2.051 / 5.767 J410 | 0.000 -> 4.815 | -1.150 -> 4.825 | moved off the J410 / J420 seam into J420's span |
| GPS | J410 | 1.361 / 14.539 J420 | 13.900 | 0.950 | unchanged |
| BAT | J1 | 1.256 / 1.275 J400 -> 0.555 / 0.635 J400 | 0.040 -> 0.060 | heads J1 | J400 / J1 gap, 0.55 mm east (clear of 1:BAT+) |
| SWITCH | J400 | 0.575 / 0.615 J121 | 0.040 | heads J400 | unchanged: no clean spot |
| IGN | J121 | 1.240 / 8.965 J2 -> 2.194 / 7.460 J2 | 8.390 -> 5.380 | heads J121 | one line north, over 1:E1- |
| CAM, SWD, SERVO | | unchanged | 4.04 / 3.155 / 5.09 | | unchanged |

RADIO sits in J420's span between the (30.3, 27.8) / (31.2, 28.4) and (30.875, 31.6) vias, ink y 28.88-30.03. BAT and
SWITCH keep the 0.040 mm identity margin of round 18: each fills a 1.19 mm gap between two terminals at their north
end, which is where the coordinator wants them, and no clean spot gives more there (the board-edge strip beside J1 is
needed for 1:BAT+, D-R19-08; the vias at x 0.9 and 1:SW leave none beside J400). With 2:E1+ and 2:SW on the bottom
(D-R19-08), each is now the only text on its line, so neither reads as part of another terminal's legend. Tests:
`R18Gate.test_word_legend_face_and_subject_map`, `R19Gate.test_r19_port_words_inside_their_own_span`,
`RealBoardSeeds.test_r18_word_legends_are_beside_their_own_terminal` (RADIO back on its seam and GPS at J410's edge fail).

## D-R19-07. No stencil aperture on the hand-fitted C84 (2026-10-30)

R19-MFG-02 / R19-BOM-02. C84 is soldered by hand after both reflows (export_fab `MANUAL_FIT`, D-R18-09), so its
generated library footprint `M3_MA_8x10` (r10_parts `polymer()`, used only by C84) drops F.Paste from both pads;
copper and mask openings are unchanged, and the placed pads match the library copy (no board override). The pin is
`r10_parts --check`, as for every generated footprint. S-4 now fails paste on any MANUAL_FIT part's lands.
Paste flashes F 245 -> 245 (C84's two gone, C123's two added) / B 371 -> 371. Test:
`RealBoardSeeds.test_r19_hand_fitted_c84_has_no_paste`.

## D-R19-08. Terminal legends fully outside the DB125 bodies, one terminal per line (2026-10-30)

R19-MEC-01 / R19-MFG-04 and the coordinator's top-render check (kicad-cli 10.0.7 `pcb render --quality high`, which
draws each DB125 as its VRML fit envelope: 8.32 x 8.10 mm for two ways, 15.52 / 19.02 mm long for four / five, offset
toward pin 1, so it reaches 1.12-1.32 mm past the DORABO nominal body at the pin-1 end). r10_post `PIN_SPOTS` places
twelve terminal pin legends at reviewed spots, each nearest its own pin by OWN_MARGIN (0.3 mm), and the words in
D-R19-06. Ink to the nearest DB125 envelope (mm, round 18 -> now; negative = under the envelope):

| Legend | Spot | To envelope | Owner margin |
|---|---|---|---|
| 1:E1- (J121) | horizontal on J121's north line, under IGN | -0.716 -> 0.245 | 3.32 |
| 2:E1+ (J121) | bottom side beside J121.2 | (top) -> bottom | 1.83 |
| 1:SW (J400) | 0.50 west on the board-edge strip | -0.030 -> 0.470 | 0.65 |
| 2:SW (J400) | bottom side beside J400.2 | (top, under J400) -> bottom | 1.77 |
| 1:BAT+ (J1) | vertical on the board-edge strip beside J1.1 | -0.700 -> 0.550 | 0.38 |
| 1:S1 (J122) | horizontal along J122's south end, clear of the (42, 86) washer | -0.920 -> 0.180 | 3.50 |
| 1:5V4 (J9) | 1.15 south | -0.937 -> 0.213 | 3.44 |
| 4:RXI (J410) | 0.50 north | 0.220 -> 0.720 | 3.50 |
| 1:4V8 (J410), 4:TXO (J9) | 0.20 east, inner column | -0.067 -> 0.133 | 0.31 |
| 4:RXI, 1:4V8 (J420) | outer column x 44.18-45.38 | -0.067 / 1.333 -> 1.583 / 1.583 | 0.45 / 0.32 |

Every top-side pin and word legend is now wholly outside every DB125 envelope (smallest 0.133 mm, the inner east column)
and outside the 0.42 mm latch plus 0.15 mm half tolerance of the nominal bodies. Lines: 2:E1+ and 2:SW go to the bottom
beside their pins (as J410 / J420 / J9 / J122 already carry their inner pins), so SWITCH and BAT are each the only text
on their gap's line, where round 18 read "SWITCH 2:E1+" and "BAT 1:BAT+ 2:SW"; J420's two wire-side legends move to an
outer column so J410's 1:4V8 and J420's 4:RXI no longer run on across the seam. The remaining shared lines belong to one
terminal: IGN over 1:E1- and SERVO 5:GND. 1:BAT+ cannot stay in the J400 / J1 gap: anywhere wholly outside J1's envelope
there it is nearer J400.2 than J1.1 (check_r8.terminal_legends would give it to J400). Text stays 1.0 mm, off every pad,
within 6 mm of its part. Checked in the top and bottom renders of the final board (`.supervisor/r10_renders/`) and by
measurement. Every terminal designator also reads whole in the render: J1, J121, J400, J410, J420 and J9 touch their
envelope's edge by 0.060-0.087 mm, and J122's moves into the C84 / J122 gap (D-R19-12).

## D-R19-09. Second vias on single-via supply feeds (2026-10-30)

R19-PWR-01 / R19-GATE-04 / R19-GATE-05. Added where a legal octilinear spot exists (every one at >= 0.15 mm to foreign
copper, 0.25 mm hole spacing, in its own In2 fill, scanned on the round 18 board):
- C84 hold-up (VLOGIC): (29.8, 81.15) on the B.Cu trunk, F.Cu 45 degrees to the C84.1 run's bend (29.2, 81.75);
- U402 IN (PORT_5V3): (42.75, 61.8), 0.75 mm further into the In2 strip;
- U401 IN (PORT_5V3): (26.45, 11.95) on the C405.1 -> U401.10 run;
- U401 EN (PORT_5V3): (24.9, 14.9), 0.75 mm west of the first;
- U401 OUT (PORT_4V8): (29.75, 9.95), at the C406.1 run's bend.
Not doubled, measured: U11.2 RAW_PROTECTED (24.3, 66.0): no spot within 1.5 mm keeps 0.5 mm from ACT_EN_MCU
(D-R18-03's floor for strong nodes beside the PC1 enable; 22 spots exist without it, all 0.15-0.35 mm from that run),
so it stays a respin item, as the reviewer found. 3V3A (16.0, 50.2): the USB_LIMITED In2 run 0.65 mm south blocks every
spot below the 3V3A In2 run, and every spot above sits 0.15 mm from U1.100 / U1.1 and off the B.Cu trunk. 3V3A
(27.0, 49.25): every F.Cu spot is <= 0.10 mm from U1.19's GND fan-out stub or the pin row, and a B.Cu spot joins the
In2 run only through the first via's own pad, needing a stub on all three layers. K-power adds the doubled feeds
(U401 IN / EN / OUT, U402 IN >= 2 In2 vias; C84 hold-up >= 2 vias) and the buck outputs (U400 OUT: L400.2 >= 2 In2
PORT_5V3 vias; U2 OUT: L1.2 >= 2 In2 3V3 vias, the F/B-only bridge via (26.4, 79.26) named, measured: it sits in the
In2 RAW region). The VLOGIC pair closes one loop on a net without a pour: route_check's r10 `PARALLEL_VIAS` names it
with its measured reason; loops() leaves only that via out (any other loop still fails), and a named via that is
missing or not parallel fails as `parallel_via`. The other four are in their own In2 fills (no loop). Tests:
`R10AuditScope.test_r19_named_parallel_via_closes_only_its_own_loop`, `R19Gate.test_r19_named_bridge_via`,
`RealBoardSeeds.test_r19_doubled_feeds_keep_two_vias` (each via of each feed, the reviewer's (26.0, 8.0) seed and the
bridge).

## D-R19-10. C87 2.2 uF -> 220 nF (2026-10-30)

R19-REQ-02. **C87: Samsung CL10B224KA8NNNC, 220 nF 25 V X7R 10 % 0603, LCSC C21120** (C126's BOM line, Basic), same
land at F(17, 65). EN stays at most 2.06 V (8.4 V x 300/1240 with 1 % resistors), 8 % of the 25 V rating; the X7R
DC-bias loss there is taken as <= 6 % in the 0.72 x minimum (Inference: Samsung's curve not re-read). With
(R80 + R165) = 940 k, R81 = 300 k and the [TPS25947 SLVSFC9C p9](https://www.ti.com/lit/ds/symlink/tps25947.pdf)
EN thresholds (rising 1.183 / 1.20 / 1.223 V, falling 1.076 / 1.09 / 1.116 V), Calculation: charge tau 50.0 ms,
turn-on 88 / 56 / 45 ms at 6.0 / 7.4 / 8.4 V (31-122 ms over C 0.72-1.27 x, 1 % resistors and thresholds; was
0.31-1.22 s); discharge tau 66 ms through R81, so a J400 drop-out shorter than 19 / 33 / 41 ms (worst 12 / 22 / 27 ms;
was 0.19 / 0.33 / 0.41 s, worst 0.12 / 0.21 / 0.27 s) cannot trip U9. That is above the proposed 10 ms chatter
acceptance (REQUIREMENTS F6), and recovery after a real supply interruption is about ten times faster. The schematic
note, the binding-note obligation (which had kept ">= 150 ms") and check_actuators' r10 pin follow. Hot-plug model (re-extracted from the
native board): all 2304 required cases and every row are unchanged (qualification pass, convergence pass); only its
retained-output envelope moves, the shared capacitance 1616.12 -> 1613.41 uF (C87 3.036 -> 0.304 uF in the
+38 % envelope, C123 +0.014 uF) and the 2 s output bound 5.878 -> 5.874 V; the cold-input minimum stays at the -15 V
clamp. These two figures are for items 1-13 alone. After D-R19-14 added C444 / C445, `hotplug_results.json` gives
1643.90 uF and 5.914 V (every row unchanged, passed = true; docs-lane correction 2026-10-31 from the round 19 circuit
check). Low-voltage corner (same check, Calculation, SLVSFC9C p9; the regenerated binding note's figures): worst-case
drop-out immunity is 11.4 / 21 / 27 ms at 6.0 / 7.4 / 8.4 V (the 12 / 22 / 27 ms above leave out R81's 1 % tolerance and the ±0.1 µA EN leakage that the binding note includes) and about 9.3 ms at
the fire budget's four-stall BAT_IN of 5.73 V, below the proposed 10 ms F6 criterion;
if the bench drop-out exceeds these, C87 is re-sized (BOM only, same land).

## D-R19-11. U4: ISM6HG256X fitted, LSM6DSV320X the consigned alternate (2026-10-30)

R19-BOM-01. LSM6DSV320X (C26633007) had 0 JLC stock. **ST ISM6HG256XTR, LCSC C51931514** (live 2026-10-31T04:01Z:
9 in stock, Extended, $14.34 at 1-9) is fitted on the same `LGA-14_L3.0-W2.5-P0.50-TL` land (K-lands pin unchanged).
[DS15034 Rev 1](https://www.st.com/resource/en/datasheet/ism6hg256x.pdf): LGA-14L 2.5 x 3.0 x 0.83 mm, drawing p187
the same as DS14623's (14 x 0.475 x 0.25 mm pads); Figure 5 p9 and Table 2 pp10-11 give the same pin map and axis
directions as DS14623 Rev 1 p9, so roll stays -gyro_Y and the lever arm is unchanged; F1 / F2: gyro +/-4000 dps,
low-g +/-16 g and high-g +/-32..256 g (>= +/-64 g); -40..105 C. WHO_AM_I reads 0x73 on both (p66), and the high-g
full-scale codes differ (Table 150 p93: ISM 100 = +/-256 g, 011 reserved; LSM 011 = +/-256, 100 = +/-320), so the
binding note tells firmware to use only 001 / 010. Pins 10-11 (OCS_Aux, SDO_Aux) are "VDDIO or unconnected" on the
ISM6HG256X; they stay unconnected. tools/jlc_easyeda/pads.json gains C51931514 (EasyEDA LGA-14_L3.0-W2.5-P0.50-BR),
tools/verified_part_metadata.json its identity; jlc_orient derives the CPL rotation from it (bottom side 0 -> 180 degrees, residual 0.040 mm; confirm pin 1 in JLC's placement preview). Live JLC data 2026-10-31T05:30Z (`fab/cost_check.json`, `stock_check.json`, bound to this BOM / CPL): $84.21 per board at 5 boards (parts $59.43 plus the $1.53 feeder fee on 81 codes), $0.20 under REQUIREMENTS M3's $84.41 (U4 $14.34 against the LSM6DSV320X line's $9.27); no line short, U4 thin (9 in stock for 5). The margin is small: a price change re-runs `FAB_NET=1 m3_design/r10_fab.sh` before ordering.

## D-R19-12. Fixed spots for nine designators (2026-10-30)

C123 beside Q122, the second vias and the moved terminal legends reorder r5_post's most-constrained-first designator
search, which on the scratch builds hid R80, R81, R123 and C5, showed Q122 and R403, moved C404, C407, C408, D8, J400,
R88 and R89, and put J121's and J400's designators into the J121 / J400 and J400 / J1 gaps, on SWITCH's and BAT's lines.
r10_post `FIXED_REFS` keeps R80, R81, R123, C5, C407, R89 and J121 at their round 18 spots and J400 on the board-edge
strip beside its body (2.937, 67.617, 90 degrees; round 18 had it on the bottom). J122's goes into the C84 / J122 gap
(33.3, 78.6, 90 degrees): the search's spot south of the body, beside the moved 1:S1, clears the nominal body but sits
0.910 mm under the DB125 fit model the 3D render draws (round 18: 0.772 mm), so it read as a sliver; the new spot is
0.395 mm from its own courtyard and 0.705 mm from C84's. The existing free-spot and own-courtyard checks pass. Moved by
their own copper: D8 (C123 covers its spot), C404 and C408 (the new vias), R88 (hidden: the moved BAT_ENABLE via covers
its spot); LED2 takes the spot the old 1:E1- left. C123 is hidden (no unambiguous spot). Hidden designators 88 -> 90.

## D-R19-13. MCU text: port UART enable on U11's status, one DS12110 revision, VREFBUF, sheet notes (2026-10-30)

R19-MCU-01 / -02 / -03 / -04. Text, binding note and sheet notes; no net or land changes.
- **R19-MCU-01.** U11 (TPS2121) IN1 is USB_LIMITED and IN2 RAW_PROTECTED; ST low means IN2 powers the output
  ([SLVSEA3F Table 9-3 p18, p21](https://www.ti.com/lit/ds/symlink/tps2121.pdf)). The pin table (rows 28, 52, 63) and
  binding note now enable the GPS / radio TX alternate function only while PA4 reads low after a settling delay, and
  park PC6 / PB13 in analog mode, no pull, when PA4 rises or the PA6 watchdog trips (one parking mode everywhere).
  Obligation 14 says the ports stay powered whenever the battery path is on (off on USB-only power).
- **R19-MCU-02.** Every DS12110 citation in pin_table.tsv (82 rows) and the binding note is Rev 8 (April 2021), revision
  V chapter, re-read page by page from the cached copy (SHA-256 0c4f0169…, byte-identical to LCSC's): Table 9 per pin,
  AF Tables 10-14, Table 119 pp212-213, Table 120 p213, Table 122 note 3 p215, Table 146 p238, Table 157 note 7 p247,
  Table 159 p249, Table 160 note 2 p251, Tables 127-128 pp218-219, Table 192 p293. The 6.0 V FT cap and the 4.0 V
  ADC-mode maximum, read from Rev 11 in round 14, stay as labelled design limits (Inference: not in Rev 8). This
  supersedes D-R18-10's keeping of Rev 11 table numbers.
- **R19-MCU-03.** camera_uart: OE is PE9 (pin 39, R102 10 k pull-down), not PA7; mcu: PE3 / PE5 flank PE4 and
  PE3 / PE5 / PE6 / PC4 have no net and stay analog, never driven (the notes' pins asserted against the pin table);
  check_actuators' comment matches.
- **R19-MCU-04.** New obligation: keep VREFBUF_CSR at reset (ENVR = 0, HIZ = 1), never enable the buffer, scale ADC
  readings from VREFINT: VREF+ (U1.20) is tied to VDDA on 3V3A (Figure 95 p286; Table 189 p291). Applying Table 9 note
  7's "kept disabled" to this board-level tie is Inference (RM0433 not re-read).
- **D-R19-11's IMU obligation** and the INT1 polarity (IF_CFG PP_OD / H_LACTIVE, DS15034 / DS14623 p60) are in the same
  regeneration; the usb_sense and telemetry notes cite Rev 8.

## D-R19-14. Spare AUX port J440; J410 / J420 / J440 electrically identical (owner approval, 2026-10-30)

The owner approved a spare four-way port in the empty north-west corner ("Add spare port", 2026-10-30; brief
`.supervisor/r19_aux_port_brief.md`): a stand-in if the GPS or radio port is damaged in the field (the camera cannot use
it) and a spare serial port for flight 2 without a respin. The owner also asked that J410, J420 and J440 be electrically
identical so the GPS and the radio can each be wired to any of the three. Firmware maps each device to a port UART;
the default map is GPS J410, radio J420, AUX spare, and the silkscreen words keep that default. J9 is not in the set.
- **Circuit (no new codes).** J440 copies J410: DB125-3.5-4P-GN-S C2757925, pin 1 PORT_4V8, 2 GND, 3 board TXO
  (AUX_TX_WIRE), 4 board RXI (AUX_RX_WIRE); R471 / R470 1 kohm C21190 (R441 / R440), D440 / D441 ESD103-B1-02EL C535146
  (D410 / D411), C444 100 nF C14663 and C445 22 uF C21397 (C410 / C411). C440-C443 are retired R9 references, so the
  capacitors are C444 / C445; the resistors follow GPS / radio's terminal + 30 numbering.
- **UART.** The free UART is USART3 on PD8 / PD9 (option A: AF7, [DS12110 Rev 8](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
  Table 13 p94; FT_h, Table 9 p75; not loader pins: AN2606 Rev64 Table 119 p278 maps the loader's USART3 to PB10 / PB11
  only). PD8 / PD9 lie on U1's north row between the GPS pair (PC6 / PC7) and the radio pair. A route from them to the
  north-west corner must cross the GPS pair; its only B.Cu crossing lies over the microSD contact row (J430.1-4,
  y 23.55-25.05) and the parallel SD_CS / SD_MOSI runs under the GPS diagonals, and east of them it straddles the In2
  3V3 / PORT_4V8 boundary at x 28.0-28.3 (K-region): measured infeasible for two nets. The other way round is an
  80 mm F.Cu detour past the port LDO and buck. Option B (UART8 PE0 / PE1) moves the reviewed IMU_INT1 pin and must
  still cross the I2C1 / SWD / SD / USB fan-out west of U1. So J410 takes USART3 PD8 TX / PD9 RX and J440 takes the
  GPS's former USART6 PC6 TX / PC7 RX, whose pins face the corner. Both routes are F.Cu only: the AUX pair has no layer
  change (no GND partner via needed), and the J410 pair changes only its first 7 mm before rejoining the former GPS run.
  C23.2's fan-out via moves from (27.1, 34.2) to (25.95, 34.15) to free PD8's escape. All three ports keep the R19-MCU-01
  rule: each TX pin (PD8, PB13, PC6) takes its alternate function only while PA4 reads low and is parked analog, no pull,
  when PA4 rises or the PA6 watchdog trips. PC6 / PC7 can also serve TIM3 / TIM8 channels (Table 12 p92); PD8 / PD9
  have no ADC input or timer channel (pin_table rows 55-56, 63-64).
- **Placement.** J440 F(7.4, 16.25), rotation -90, wires leaving west like J121 / J400 / J1. Top washer at (4, 4):
  3.93 mm to the fit envelope (>= 3.8); J3's courtyard 1.67 mm; wire room 5.003 mm (5.00-5.60 with tolerance), the
  other west terminals' figure. The cell is on the top east of the body: C444 F(12.5, 12.6), C445 F(15.2, 13.4), D440
  F(13.9, 17.2), R471 F(16.1, 18.0), D441 F(13.9, 21.4), R470 F(16.1, 20.6); the TX wire runs straight west to J440.3,
  the RX wire takes one 45 degree step to J440.4. M-6 (bottom parts 1.5 mm from THT pads) moved TP82 B(10.8, 21.3) ->
  B(11.0, 17.6) and R90 B(7.8, 23.1) -> B(11.275, 23.0) (its 3V3 via (6.2, 23.1) -> (9.6, 23.0); its run no longer
  doubles back west). Stitch vias: (7.0, 22.0) removed (J440.4), (2.0, 9.0) -> (0.9, 9.0), (16.5, 12.5) -> (17.5, 12.0).
- **Feed.** In2 under J440 is the 3V3 region, so PORT_4V8 reaches J440.1 on a 0.4 mm F.Cu run from the In2 PORT_4V8
  region through (29.75, 9.95) and a new second via (30.5, 9.95), along y 9.95 and 11.0 (22.8 mm, about 28 mohm, 8.5 mV
  at 300 mA if the radio is moved there). K-power gates it as "J440 feed" (two vias).
- **AUX allowance.** U401 TPS7A9101 is rated 1 A ([TI SBVS282A](https://www.ti.com/lit/ds/symlink/tps7a91.pdf) p1,
  current limit 1.5-1.9 A p5). The binding floor is GAP-3: junction <= 125 C at the 70 C bay limit with the inferred
  80-110 C/W, i.e. (buck_max 5.546 V - ldo_min 4.712 V) x (0.46 A + AUX) + 22 mW <= 0.5 W, which allows 112 mA. Documented
  limit: **the spare port may draw up to 100 mA at 4.8 V** beyond GPS 150 mA and radio 300 mA, whichever ports they use.
  Changed cases (`parts_budget.json`, Calculation / Inference): LDO loss 0.406 -> 0.490 W; junction at 70 C 102.5-114.7
  -> 109.2-123.9 C (85 C, outside the bay range: 124.2-138.9 C); camera-short buck case 1.710 -> 1.810 A (< 2 A); ports-on
  battery-break ride-through at 300.8 uF to 3.8 V 0.490-0.571 -> 0.464-0.539 ms (470 uF 0.725-0.842 ms), ports on with
  the camera off 1.533-1.655 -> 1.304-1.412 ms; fire current at 7.4 V 1.544 -> 1.541 A, four stalls 1.283 -> 1.279 A
  (>= 1.125 A). LDO-limited short cases are unchanged (U401's limit covers all three ports). Hot-plug: 2304 cases pass.
- **Legends.** AUX word F(13.4, 10.2), inside J440's courtyard span (WORD_SPAN); 1:4V8 on the west board-edge strip
  F(2.4, 10.6, 90); 2:GND, 3:TXO and 4:RXI on the bottom beside their pins. No top spot for 4:RXI is nearer J440.4
  than J3's shell pads (west and south) or J430's shell pad 11 (east) by OWN_MARGIN; B(4.2, 21.5) has 1.74 mm. The
  designator search moves C400, C401, R90, R462 and R463 and finds no unambiguous spot for C28, R110 (J440's courtyard
  now claims its former spot), D440 or D441: hidden, kept on F.Fab (90 -> 94).
- **Checks.** R10_PORT_UART / R10_PORT_NETS add AUX (route_check and K-reference); uart_ports holds all three ports
  (J410 on pins 55 / 56); CONNECTORS, PARTS, REQUIRED_FITTED, WIRE_ENTRY, TERMINAL_PINS_R10, SHOWN_REFS,
  WORD_LEGENDS_R10 and WORD_SPAN_R10 add J440 / AUX; POWER_PATHS adds the J440 feed; plate_model STRAIN_PARTS adds J440
  and C445 (masses: J440 6 g + 2 g mated, the J410 allowance, Inference); r10_sch_check pins the three ports' MCU and
  resistor nets and seeds three AUX faults. K-power's path graph also counts the via behind (29.75, 9.95) on C406.1's B.Cu
  run, so it would not notice the loss of (30.5, 9.95) alone; the seeded test drops (29.75, 9.95).
- **Cost (owner decision).** AUX adds $1.14 per board ($0.403 terminal, $0.271 22 uF, 2 x $0.231 ESD, resistors and
  100 nF): live JLC 2026-10-31 gives $85.35 per board against the $84.41 M3 cap, $0.94 over; `check_procurement
  --cost-only` fails and is not weakened. Stock: none short; C2757925 4 per board (37,827 in stock), C535146 8 per board
  (201), U4 thin (9 for 5).

The record index is now **151 unique D IDs through D-R19-14**.

## D-R19-15. Harden the gate (R19-GATE-01 to -07, R19-REQ-10, R19-RTE-01, R18-MEC-01, AUX feed) (2026-10-31)

Checks only, by the round 19 gate lane (`../r10_review/round19_fix_gate.md` / `.json`). The PCB is unchanged at
`50a39de5…`. No fab-manifest input changed, so the package was not rebound; `fab_manifest.py --content` passes on it.
What each gap now checks:
- **K-lands paste and mask (R19-GATE-01).** Each placed footprint's paste margin, paste ratio and mask margin, and
  each pad's local paste margin, paste ratio, mask margin and paste / mask layers, must equal its library copy
  (`pcbnew.FootprintLoad` on `kilib/rocket.pretty`). Pads are paired by number and local position (within 2 µm,
  mirrored for a bottom part). 701 pads are compared and none differs. C84's missing paste is its library variant
  (D-R19-07), so no exception is named. Zone-connection and clearance overrides stay with K-copper / LC-1.
- **Part codes (R19-GATE-02).** check_actuators' r10 block pins R131 = 10k, C25744 / 0402WGF1002TCE, R0402, and
  C127 / C129 = 10nF 50V X7R 10%, C57112. S-4 decodes the Manufacturer Part of every fitted R / C part (the field the
  JLC BOM is exported from; S-4 `--bom` holds the BOM's code, MPN and footprint to it). The decoded value must equal
  the Value field, and so must any tolerance, voltage or dielectric the Value states. Decoded: 157 parts in eleven
  families (UNI-ROYAL 73, Samsung CL 44, Murata GRM 14, Yageo CC 9, Yageo RT 7, Fenghua 4, Yageo RC 2, and one each of
  Bourns CRM, FOJAN FRC, Murata GCJ and Vishay MCT). Listed as not decoded: C84, an aluminium polymer part.
- **K-plane necks (R19-GATE-03).** Each non-GND inner fill is unfractured and deflated by PLANE_LINK_W / 2. A
  landing-via cluster that the deflation cuts off from the largest piece then counts as a split piece and needs two
  outer links of >= 0.5 mm. Necks under 1.0 mm are reported, located by bisection. The fill must be unfractured
  first: KiCad's fracture slits otherwise showed a false 0.474 mm neck. Calibration on the board, all in In2 3V3:
  - 0.549 mm, with landings (18.8, 60.25), (22.6, 52.15) and (19.05, 55.9);
  - 0.549 mm, with landings (23.1, 78.1), (23.0, 70.0) and (23.2, 68.6) (the east path the gate report measured at
    0.54 mm);
  - 0.589 mm, landing (9.2, 52.98);
  - 0.706 mm, landing (19.5, 49.15).
  PORT_4V8, PORT_5V3 and RAW_PROTECTED have no neck under 1.0 mm.
- **Rail widths (R19-GATE-04).** Every K-power path names its design current, with the basis in the code. Its floor
  must be at least `ipc2152.ipc_width` for that current at a 30 C rise (external fit, no plane credit; Inference), or
  the table fails. New paths:
  - VLOGIC trunk, U11 to U2 through C99: 0.4 mm floor, 1.294 A, IPC width 0.167 mm;
  - CAM_5V out, U402.6 to J9.1 through C431: 0.4 mm, 1.249 A, 0.157 mm;
  - J410 feed and J420 feed (PORT_4V8, one In2 via each): 0.4 mm, 1.9 A, 0.326 mm.
  Existing paths now carry currents too: U401 IN / OUT 1.9 A, U402 IN 1.249 A, U400 OUT 1.81 A, U2 OUT 2.0 A,
  C84 hold-up 1.294 A, U9 IN / OUT 2.9 A. U401's two 0.25 mm pin links (0.5 mm DSK pitch) are new named POWER_NARROW
  entries, making 8.
- **Simple paths (R19-GATE-05).** `fire_path` and `path_graph` keep only copper on simple paths between the terminal
  sets: biconnected blocks along the block-cut tree between the terminal hubs. A loop that hangs off one cut vertex is
  dropped, not only a leaf. On the board all six fire paths and every earlier K-power path are unchanged; only the
  J440 feed changed, by the item 11 change below. U9 IN needs at least one via of >= 1.0 / 0.5 mm; any further via
  needs >= 0.5 / 0.3 mm. route_check already had its measured-reason list (PARALLEL_VIAS_R10, D-R19-09), and no
  generic exemption was added. Seeds c01 (1.0 / 0.5 mm) and c01b (0.6 / 0.3 mm) were drawn cleanly on a copy of the
  post-CAD tree: the second via at the F.Cu feed node (17.5, 88.891), joined on B.Cu by 1.0 mm straight to
  (17.5, 87.3). With one PARALLEL_VIAS_R10 line, each passes every check.sh checker step after the r10_build
  regeneration, including the real hot-plug re-solve (passed). S-9 evidence is identical; K-power changes only in U9
  IN's added via and run; the budget differs only in its board hash. The adversary's own drawing (V2 at
  (18.9, 88.891), a 0.707 mm B.Cu diagonal, then north to (19.4, 85.4)) now passes the budget, r10_parts and
  check_r10; the refusal in the gate report is gone. It still fails route_check on three faults of the drawing itself,
  which M2 rejects and the clean drawing does not have:
  - the 0.707 mm short segment;
  - a 45 degree junction at (19.4, 85.4);
  - a BAT_IN net detour: 64.67 mm of copper against 1.6 x the 38.99 mm MST = 62.38 mm (the clean drawing has
    61.16 mm).
- **Word centre margins (R19-GATE-06).** Each word's ink-box centre must be at least 1.0 mm nearer its own courtyard
  than any other. This blocks for GPS (13.178 mm), RADIO (3.716), AUX (14.465), IGN (5.265), SERVO (3.764),
  CAM (3.451) and SWD (2.853). BAT (0.080) and SWITCH (0.040) are reported only. They fill the 1.19 mm gaps between
  DB125 courtyards, where D-R19-06 keeps them, and the per-pin legends and J121's black body disambiguate.
- **Silkscreen allowlist (R19-GATE-07).** Every visible silkscreen text must be a designator or an allowed legend:
  board text, text box and footprint text or field, on either face. Allowed legends are the TERMINAL_PINS_R10 pins,
  the words, the PORT_LEGENDS_R10 rows, SERVO_HARNESS_NOTE, PINNED_TEXTS and the JLC mark. On the board: 39 legends,
  6 port rows and 121 designators.
- **Stale names and port UART scope (R19-REQ-10).** critical_reference drops V3V3_SENSE, which went with its divider
  in D-R18-01. R10's extended set is now `EXTENDED_R10` = SWDIO / SWCLK / NRST; the radio SPI names stay in `EXTENDED`
  for the R7-R9 record tools. The CAM_TX_MCU / CAM_RX_MCU names, which exist on no R10 board, are also dropped from
  `R10_PORT_UART` / `R10_PORT_NETS`. K-reference fails on any listed name that is not a board net. **Decision:** the
  GPS / RADIO / AUX / CAM port UART nets stay under the stricter 1.5 mm GND-partner-via and one-In2-region rules.
  R19-REQ-10 proposed relaxing them (115200 baud behind 1 kohm), but the frozen board meets them, and relaxing a gate
  rule needs a reason that board does not give.
- **Pour debris (R19-RTE-01).** K-copper: every zone fill piece, of any size, must hold a via of its net or touch two
  or more of its net's pads. Only an exact, measured POUR_DEBRIS entry is excepted, and an entry fails as stale once
  its piece is gone. The board has 35 pieces. One fails: a 0.282 mm^2 F.Cu GND piece at U1.74 (17.50, 34.48), which
  touches only that pin. It was already on the round 18 board beside the 1.693 mm^2 U1.19 piece that D-R19-05
  removed. It is the one named entry. CAD fix: ZONE_CONNECTION_NONE on U1.74, as D-R19-05 did for U1.19, then delete
  the entry.
- **STRAIN_PARTS (R18-MEC-01).** R150-R155 are added (NumPy test).
- **AUX feed (CAD hand-back, open item).** The J440 feed path is held to F.Cu (`layers=('F.Cu',)`). Its two In2 vias
  are (29.75, 9.95) and (30.5, 9.95). The via (29.75, 12.6), behind them on U401's B.Cu run, no longer counts, so
  losing (30.5, 9.95) alone fails K-power.

Each gap has a seeded regression on a copy of the post-CAD board:
- R19-GATE-01: b19a (Q124 paste margin -0.1 mm), a U9 paste ratio, an R134 mask margin and a removed paste layer;
- R19-GATE-02: b08e (R131 re-coded to C11702 / 0402WGF1001TCE with Value 10k) fails K-actuators and S-4;
- R19-GATE-03: b10b (0.30 mm neck);
- R19-GATE-04: a 0.2 mm run on VLOGIC, PORT_5V3 (twice), CAM_5V, PORT_4V8 and 3V3;
- R19-GATE-06: RADIO moved 4.2 mm north;
- R19-GATE-07: b21b ("BATT+") and a shown Value field;
- R19-REQ-10: V3V3_SENSE back in the list;
- R19-RTE-01: U1.19's pour connection restored, giving the 1.693 mm^2 piece;
- item 11: the via (30.5, 9.95) removed.
The gate lane's `check.sh` exits 0:
- check_r10: 35 rules;
- fab: content checks 3 / 3, manifest 6 outputs;
- self-tests: shell 10, procurement 20, fab_validation 34, fit 33, paste 16, r10_parts 5, route 68, R10 234 (6
  NumPy skips under KiCad Python), and NumPy `HotplugNumerics Plate` 6.

Open items:
- U1.74's GND piece needs the CAD fix above.
- BAT and SWITCH word centre margins are below 1.0 mm (reported only).
- check_procurement `--cost-only` still fails at $85.35 against the $84.41 cap. That is an owner decision, outside
  check.sh, and was not touched.

The record index is now **152 unique D IDs through D-R19-15**.

## Round 20 polish pass (CAD lane, board 0dc84776…)

Brief `.supervisor/r20_fix_cad_brief.md`: round 20's seven lenses found 0 Critical / 0 Major on `50a39de5…`; this last surgical pass before the closing pair touches only the items below. PCB `0dc847761de94a45cf68b1c82ec91f38e9d4ebb7297abc7108e3df9a454940d3` (two identical complete builds, check.sh exit 0); hand-back `../r10_review/round20_fix_cad.md`.

## D-R20-01. U9's EN pull-down stays at the switch end: no legal clean B.Cu spot at U9.1 (2026-10-31)

R20-SAF-01 (Minor). Not changed; measured reason, for the owner's respin list. U9.1 (EN) is the south-west corner pin
of U9 at B(18.5, 81.6). On B.Cu every way out of it is closed:
- west / north-west: D9's courtyard ends 0.210 mm from U9's, and BAT_OVLO leaves U9.2 (north of EN) west and then south
  round EN to R83 and R82;
- east: U9.5's BAT_IN trunk (x 18.25, 0.3 / 0.7 mm);
- south: R82 (the OVLO divider top). R82.2's pad is 0.350 mm from the 0.7 mm trunk; a 0.2 mm run at 0.15 mm clearance
  needs 0.50 mm. R82 can move at most 0.275 mm west (R167's courtyard).
The only B.Cu reachable from U9.1 is the pocket round the BAT_ENABLE via (17.1, 82.8), about 1.4 x 0.9 mm, against
an 0603's 0.95 x 2.45 mm pad span. Beyond R82 the triangle inside the BAT_IN loop gives at most 1.64 mm of pad span
(2.45 needed) and is enclosed by BAT_IN, so a pull-down there would also hang on a GND via of its own.

A trial on a scratch copy (not built into the board) placed R81 at B(16.775, 85.475) rot 180 with one straight
B.Cu run from U9.1 at x 17.6. It needed R82 0.25 mm west, the 1.0 mm U9 IN via 0.1 mm east, the R82 / R167 BAT_IN tap
rerouted round R81's cell (south to y 87.8, west, north) and R81's return on two GND vias inside the BAT_IN loop.
Even then:
- R81's return sits in a B.Cu pour island enclosed by BAT_IN, not in the main pour: it reaches GND only through those
  two vias (C95's F.Cu pad and the IN via leave room for no more);
- route_check failed four ways: acute angles at R82.1 and U9.1, a BAT_IN net detour ratio of 1.61 and a removable
  local bump on the new tap.
That is a re-layout of U9's west cell (the hot-plug feed and the OVP divider included), outside this surgical pass.
The class stays as round 20 measured it: EN reaches R81 through three series vias and about 20 mm of 0.2 mm track
(Inference: an open floats EN toward ON). The respin option is that cell re-layout, with the R82 / R167 tap routed so
R81's return joins the main B.Cu pour.
The F.Cu route is closed today too. The pre-commit circuit check searched a 0.025 mm grid and found no legal centre
for a second EN escape via beside (17.1, 82.8): U9.1's pad, BAT_OVLO, the BAT_IN trunk, R82.2 and BAT_FAULT_N's F.Cu
corner (16.55, 83.35) block it. A second respin option:
- move that BAT_FAULT_N corner at least 0.1 mm west and 0.075 mm south;
- replace the escape via with a pair, for example (16.95, 82.5) and (17.3, 82.925), at the 0.25 mm hole-to-hole limit
  and with a second S-8 In2 void;
- put R81 on the F.Cu EN run near (18.6, 81.3), in the F.Cu GND island with the GND vias (20.2, 81.0) and
  (20.85, 76.4).

## D-R20-02. U401's feedback tap joins the output after both OUT vias; K-power checks single via opens (2026-10-31)

R20-PWR-02. R402.1 (U401's FB divider top) hung on the OUT via (29.75, 12.6) alone. Open, FB falls to GND through
R403 and the LDO drives all three ports to its dropout (about 5.2-5.55 V, the power lens's figure).
- **Board.** A PORT_4V8 via (30.575, 11.6) straight north of R402.1, in the In2 PORT_4V8 output plane that both OUT
  vias feed, with a 0.4 mm F.Cu stub to R402.1 (precision note, round 21 docs lane: 0.4 mm is the stub's track width;
  it is 1.0 mm long). GPS_RX_MCU's F.Cu run at y 11.0 stays (0.25 mm from the via). No B.Cu
  stub: a first trial with one formed a staircase on U401's output run (route_check).
- **Measured.** Removing any one of the net's 9 PORT_4V8 vias leaves R402.1 joined to U401.1 / U401.2. On the round
  19 board, removing (29.75, 12.6) cut it off.
- **Gate.** `check_r10.single_via_opens` and `SINGLE_OPEN_TAPS` add this to K-power. The check builds the net's copper
  graph (pads, tracks, vias, fill pieces touching on a shared layer) and removes each via in turn.
- **Seeded test.** test_r20_fb_tap_survives_one_via_open removes the new via: opening (29.75, 12.6) then fails.
- **Side effect.** U401 OUT's K-power path now reaches three In2 vias (the new one through R402.1's 0.4 mm F.Cu run).
  The doubled-feed seed drops both (29.75, 9.95) and (30.575, 11.6) to reach one.
- **Test harness.** The real-board seeds that remove a via now leave it undeleted (`RealBoardSeeds.drop`). KiCad 10's
  SWIG hands a removed item to its Python proxy, and a temporary proxy deleted it while the board's caches still
  pointed at it. Later board reads in the same process then failed ('SwigPyObject' footprints); the round 19 seeds
  passed by luck of memory reuse.

## D-R20-03. No pour connection on U1.74 (2026-10-31)

R20-RTE-02. `r10_pcb.py` sets U1 pad 74 to `ZONE_CONNECTION_NONE`, as D-R19-05 did for pad 19 (a board pad
override; the library is unchanged and DRC's library comparison stays clean). U1.74 keeps its own F.Cu stub and via
(17.5, 39.3). The via-less 0.282 mm^2 F.Cu GND piece on its pin tip (17.50, 34.48) is gone; pour pieces 35 -> 34, no
debris. `POUR_DEBRIS` is empty (its one entry deleted). The seeded test restores pad 74's pour connection, which
brings the 0.282 mm^2 piece back and fails K-copper.

## D-R20-04. TP82 on the USB_LIMITED diagonal's extension (2026-10-31)

R20-RTE-01. TP82 B(11.0, 17.6) -> B(11.2, 20.7). Its spur is now the one segment (15.55, 25.05) -> (11.2, 20.7)
(6.152 mm). This replaces the three segments (11.8, 21.3) -> (11.8, 18.4) -> (11.0, 17.6) and the diagonal's end.
- **Stub past the old bend (11.8, 21.3):** 3.785 -> 0.849 mm, no bend.
- **Nearest foreign copper:** 1.075 mm (R90.1 / R90.2 pads), with the GND pour held at TP82's 1.0 mm local clearance.
- **M-6:** 1.855 mm to J440.4.
These are the routing lens's figures, confirmed on the board.

## D-R20-05. The protected terminal barrels drop their unconnected inner rings; S-8 measures rings (2026-10-31)

R20-SAF-05 (owner table row 9). `r10_parts.terminal(..., bare=...)` generates the pads with KiCad's "remove
unconnected layers, keep start and end", as every via has had since D-S8-19. The setting is in the generated library
footprint, so DRC's library parity holds; a board-level override failed it (two lib_footprint_mismatch warnings,
measured).
- **Which pads.** M3_DB125_2P_BK pad 1 (J121.1, PYRO1_OUT) and M3_DB125_2P_GN pad 2 (J400.2, BAT_SW_RETURN).
- **Not J121.2.** J121.2 (PYRO1_IGN) keeps its rings: GND is exempt there, and removing them would bring In1 / In2 GND
  from 0.550 to 0.250 mm of its wall.
- **Before -> after (ring / wall to the nearest foreign inner copper, mm):**
  - J121.1: In1 GND 0.750 / 1.050 -> no ring / 1.050; In2 GND 0.750 / 1.050 -> no ring / 1.050; In2 3V3 0.761 / 1.061
    -> no ring / 1.061.
  - J400.2: In2 RAW_PROTECTED 0.750 / 1.050 -> no ring / 1.050; In2 GND 0.750 / 1.050 -> no ring / 1.050.
  - J400.2, In1 GND (exempt: a short holds EN low, board off): ring 0.250 / wall 0.550 -> wall 0.250.
- **Side effect at J1.2.** GN pad 2 is also J1.2 (GND). It keeps its In1 thermal; its unconnected In2 ring goes, and
  In2 RAW_PROTECTED fills to 0.25 mm of its barrel (was 0.55 mm), the hole clearance every GND via in a RAW region has.
- **Unchanged.** The vias already had no inner rings, so every via barrel is unchanged.
- **Gate.** S-8 now also measures an inner ring a protected barrel keeps (`barrel_rings`). The seeded test restores
  J121.1's rings (GND 0.750 mm fails) and J400.2's (RAW_PROTECTED 0.750 mm fails). The synthetic S-8 test models the
  board's ringless vias and adds a 0.900 mm ring seed.

## D-R20-06. Designators: C400 moved, C94 and R461 hidden; the gate's named entries deleted (2026-10-31)

R20-MFG-02. With the gate lane's change to `r7_post` / `r8_post` (every courtyard tested, D-R19-15), the post step
re-places C400 F(9.743, 6.048) -> F(9.707, 5.75). It finds no spot nearer their own part for C94 (inside U1's
courtyard before) or R461 (inside J430's), so both are hidden and kept on F.Fab (AGENTS section 3).
`DESIGNATOR_COURTYARD_R20` is empty; no designator is nearer another part's courtyard.

This pass's copper and part moves re-place these designators through the same search:
- **Moved:** R402 (by the new via); R463 (TP82 now sits on its spot); C444, R470 (the clamps left the top); D440, D441
  (shown again on the bottom).
- **Shown again:** C28.
- **Hidden:** C404, R90 (TP82), U401 (the new via sits on its former spot).
Hidden 94 -> 96, all kept on Fab. J440's 3:TXO legend moves B(5.7, 17.5) 90 -> B(10.5, 17.5) 0, east of its pin (D440
and its run took the old spot). No other designator or legend moved (silkscreen diff against 50a39de5).

## D-R20-07. Fab references clear of their own Fab outlines (2026-10-31)

R20-MFG-03. `r10_post.FAB_REFERENCE_CLEARANCES_R13` entries (dx, dy, size mm), each measured with no intersection
with its own Fab shapes:
- C445 (0, 0, 0.7), as C411;
- D440 / D441 (0, -1.0, 0.8), beside their bodies as D410 / D411;
- C123 (0, -0.1, 0.4), clear of its pin-1 mark;
- R119 (0, 0.1, 0.4); its 1.0 mm text had read "R1119";
- R173 (0.1 -> -0.1, 0, 0.4).
Crossings 6 -> 0 (C123 0.0013, C445 0.1915, D440 / D441 0.0479, R119 0.6935, R173 0.011 mm^2). `FAB_REF_CROSSINGS_R20`
is empty. The seeded test brings back each round 19 text and fails it.

## D-R20-08. No In2 power copper under the west aft panel tab; the east tabs need the owner's tab plan (2026-10-31)

R20-MFG-01. A fill-only In2 rule area, `R20_TAB_KEEPOUT_WEST_AFT`, covers x -0.5 to 3.0, y 12.5 to 17.5. In2 3V3 under
that tab's 5 x 3 mm band: 12.498 mm^2 -> none. 3V3 stays one piece, and its necks are unchanged (0.549 mm least).
K-plane, K-reference and K-region pass on the built board.

Not done for the two east tabs, measured on a copy of the board with each keep-out added (K-plane):
- **East aft** (x 43-46, y 6.75-11.75; RAW_PROTECTED 7.497 mm^2, PORT_5V3 3.077 mm^2): the north In2 RAW_PROTECTED
  region joins the rest only along the east edge, so the keep-out splits RAW_PROTECTED in two. The 245.01 mm^2 piece
  is left with no link; a 2.0 mm deep keep-out splits it too.
- **East forward** (y 63.75-68.75; RAW_PROTECTED 12.244 mm^2): the same piece is left on a 0.45 mm neck (under 0.5),
  at keep-out depths of 3.0, 2.9 and 2.8 mm.
The owner chooses the east tab plan (another span, or In2 RAW reshaped).

## D-R20-09. The AUX clamps sit under J440 on the bottom, as D410 / D411 under J410 (2026-10-31)

R20-RTE-05.
- **Placement.** D440 F(13.9, 17.2) -> B(4.45, 19.45) rot -90 (between pins 3 and 4). D441 F(13.9, 21.4) ->
  B(4.45, 23.05) rot -90 (beyond pin 4). Both are on the wire side under J440's body, mirroring J410's clamps.
- **Copper.** Each pin runs west on B.Cu and drops into its clamp. Each return goes 0.7 mm further west to its own GND
  via. The top-side taps and their two GND vias, (14.225, 16.45) and (14.225, 22.15), are gone.
- **Measured.** Pin to clamp pad: 6.227 / 6.176 -> 3.157 / 3.194 mm (J410 / J420: 3.1-3.4). M-6: 1.681 / 1.713 mm.
- **Why the wire side.** The interior (east) side is taken by TP82 (D-R20-04) and R90.
- **Legends.** J440's bottom 3:TXO legend moves east of its pin, B(10.5, 17.5) (D-R20-06); 4:RXI keeps B(4.2, 21.5),
  its ink 1.365 mm from D441's nearest pad.

## D-R20-10. Item 10 (optional cleanliness) not done (2026-10-31)

R20-RTE-04 / -03. Neither change is needed for a gate, and both stay recorded findings:
- **VLOGIC via pair in line (R20-RTE-04).** It would move the pinned `route_check.PARALLEL_VIAS` entry and two tests.
- **GPS jogs (R20-RTE-03).** They need C90's 3V3 / GND fan-out vias moved west.
Both were left out of the last surgical change.

## D-R20-11. C87's drop-out immunity includes the EN leakage (2026-10-31)

R20-SAF-04. C87 stays 220 nF. A larger value would lengthen recovery after a real supply break, which F6 also
constrains.

The binding-note obligation (`r10_sch_check.py`) and the battery_entry sheet note now carry the worst case with
I_ENLKG +/-0.1 uA ([TPS25947 SLVSFC9C p9](https://www.ti.com/lit/ds/symlink/tps25947.pdf)). Calculation (C87
0.72-1.27 x 220 nF, 1 % divider, thresholds 1.183-1.223 V rising and 1.076-1.116 V falling):
- **Drop-out immunity:** 10.6 / 20.5 / 26.4 ms at 6.0 / 7.4 / 8.4 V (was 11.4 / 21 / 27); about 8.5 ms at the 5.73 V
  four-stall BAT_IN (was 9.3); 6.6 ms at 5.5 V.
- **10 ms chatter criterion:** needs a loaded pack of at least 5.92 V.
- **Turn-on:** 30-129 ms (was 31-122).
These reproduce the safety lens's figures.

The record index is now **163 unique D IDs through D-R20-11**.

## Round 21 fix pass (CAD lane, board 5516eeec…)

Brief `.supervisor/r21_fix_brief.md`: round 21's ten lenses found 0 Critical / 0 Major on `0dc84776…`; four of them
found J1.2 and J400.2 0.250 mm from inner copper (D-R20-05), under JLC's 0.3 mm. Items 1-5 change the board or its
generators, items 6-8 are checks only. PCB `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` (two
identical complete builds, check.sh exit 0); hand-back `../r10_review/round21_fix_cad.md`.

## D-R21-01. Inner-layer PTH pad holes 0.55 mm from copper; JLC's hole table pinned in K-rules (2026-10-31)

R21-PWR-02 / R21-BOM-01 / R21-MFG-01 / R21-GATE-02. JLCPCB's capabilities page
(https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-31) gives "Inner layer PTH pad hole to copper clearance
0.3mm", "Inner layer via hole to copper clearance 0.2mm", "PTH to Track 0.28mm" (0.35 mm recommended) and "Pad
Hole-to-Hole Spacing 0.45mm". The project DRU held every hole at its general 0.25 mm, so DRC passed J1.2 and J400.2.
- **Rule.** `r10_sch.py` adds three rules to `m3.kicad_dru` (`JLC_HOLE_RULES`): inner-layer PTH pad hole to copper
  0.55 mm (condition `A.Type == 'Pad' && A.Pad_Type == 'Through-hole' && (B.Type != 'Pad' || B.Pad_Type ==
  'Through-hole')`), outer-layer PTH hole to track 0.28 mm, pad hole to hole 0.45 mm. DRC and the zone filler apply
  them.
- **Why 0.55 mm, the largest of 0.55 / 0.35 / 0.3.** It keeps every plane and reference rule passing: DRC 0, K-plane's
  landing necks unchanged (least 0.549 mm), K-reference and K-region OK, and every inner power fill still one piece. It
  is what the other plated pads already had, J3's four shell holes (0.451 mm) excepted; D-R20-05 had taken J1.2 and
  J400.2 from 0.550 to 0.250.
- **Plane strips it narrows (measured on the fills, before -> after, mm).** At the west-edge terminals:
  - J1.1-J1.2 (In2 RAW_PROTECTED) and J400.1-J400.2 (In1 GND), along the pin line: 1.40 -> 1.10;
  - J3.1 / J3.4 to the VBUS via voids (8.0, 33.7) / (7.95, 27.9) (In2 3V3), least gap between the two voids: 0.633 /
    0.599 -> 0.566 / 0.537;
  - J3.2 / J3.3 slot to the west edge (In2 3V3): 0.479 -> 0.379.
  Each J3 strip runs in parallel with the J3.2-J3.1 / J3.3-J3.4 slot-to-slot strips (1.729 -> 1.529), and the inner
  fill pieces are the same as on `0dc84776…` (3V3, PORT_4V8, PORT_5V3 and RAW_PROTECTED one piece each on In2), so
  nothing splits.
- **Condition.** The partner must be copper. With an A-only condition, J3's PTH shell pads failed against J3's own
  NPTH locating holes (DRC hole_clearance: the NPTH holes are 0.535 mm from the shell pads' rings, 0.835 mm hole wall to
  slot wall); a clause on `B.Pad_Type` alone is false for zones and tracks, so the rule missed the fills (measured:
  J1.2 stayed at 0.251 mm with DRC 0).
- **Before -> after (hole wall to the nearest foreign inner copper, 31 plated pads, In1 / In2).** Changed: J1.2 In2
  RAW_PROTECTED 0.251 -> 0.550; J400.2 In1 GND 0.251 -> 0.550; J3.1-J3.4 In2 3V3 0.451 -> 0.550. Unchanged: every
  other pad and layer, 0.550 mm or more (the full table is in the hand-back).
- **Gate (K-rules).** `JLC_HOLE_TABLE` pins the four figures: each named DRU rule must exist once with its pinned
  layer and condition and a minimum at least JLC's; no later rule on the same layers (KiCad lets the last matching rule
  win) may set that constraint lower; no hole rule anywhere may be under 0.2 mm. `pth_inner_copper` measures every
  plated pad hole wall to foreign In1 / In2 copper on the board itself against 0.3 mm, whatever the DRU says.
  `DRU_SHA256` re-pinned 5acf6db7… -> 1d2dbe77….
- **Seeded tests.** The inner rule at 0.25 mm, dropped or narrowed, the outer rule at 0.25 mm, hole to hole at 0.4 mm, a
  later inner override at 0.25 mm and the general rule at 0.15 mm each fail; the 0.25 mm inner rule fails K-rules even
  with the DRU re-pinned. Refilled under the round 20 DRU, J1.2 and J400.2 come back at 0.25 mm and the geometry check
  names both.

## D-R21-02. U2.1 has a second path; every regulator FB / OV / EN / ILIM tap is held through one named list (2026-10-31)

R21-PWR-01 / R21-GATE-01. U2.1 (AP63203 FB, its output sense) reached 3V3 only through the via (23.2, 68.6).
- **Board.** A 0.4 mm B.Cu 3V3 run (24.05, 68.95) -> (23.0, 70.0) from U2.1's south end into R89's via (the gate
  lens's f01b). The in-line second via (22.55, 68.6) was not used: it sits 0.886 mm (In2) / 0.986 mm (In1) from the
  BAT_ENABLE barrel (21.3, 68.9), under S-8's 1.0 mm (measured). U2.1 now survives every single via open.
- **Counted, not gated (route_check).** R89's via (23.0, 70.0) is now a two-layer 3V3 via (R89's F.Cu stub, the new
  B.Cu run), so route_check counts an INFO `power_via_no_gnd` there: its nearest GND via is 2.182 mm away. The run also
  leaves U2.1 0.35 mm off the pad centre (INFO `pad_end_offcentre`).
- **Gate (K-power).** `SINGLE_OPEN_TAPS` holds 26 taps: the gate lens's survey of every FB, OVLO, EN and ILIM node and
  its divider ends (U2, U400, U401, U9, U10, U11, U402). `single_via_opens` tests only the vias on one tap-to-source
  path (a via every path needs lies on that one), so the 26 taps run in about 10 s. A single point passes only as an
  exact `SINGLE_OPEN_EXCEPTIONS` entry (tap, via, measured reason); an entry no longer met fails as stale.
- **Exceptions (8).**
  - U401.3 / via PORT_LDO_FB (29.75, 13.60): no legal second via spot (the round 21 power lens's scan). Open, FB is
    held only by its +/-100 nA leakage (TI SBVS282A p5) and PORT_4V8 is undefined up to dropout (Inference). Respin:
    R402 / R403 beside U401 on B.Cu.
  - R87.1 / vias USB_LIMITED (22.00, 62.25) and (16.00, 28.00): R87.1 (22.0, 63.1) is boxed on B.Cu by RAW_ACT (x 22.8,
    y 61.4-63.875, and y 63.875 to x 19.2) and PYRO1_CONT_MID (from (20.83, 61.8) north-east), so no B.Cu second path
    exists; a second In2 via would be a parallel-via loop and would still leave U10's end on one via. Open, the USB
    over-voltage cut-off is lost; USB is bench power only.
  - R85.1 / via USB_ILIM (14.82, 26.00), R85.2 / via GND (9.00, 27.84), R430.2 / via GND (32.30, 59.50): TI SLVS841G
    section 8.5.1 p16: the TPS2553 current-limit threshold is proportional to the current sourced out of ILIM, so an
    open ILIM leg sets a lower limit (fail-safe). TI does not state the open-pin case: Inference.
  - R81.1 and C87.1 / via BAT_ENABLE (17.10, 82.80): see D-R21-05.
- **Seeded tests.** Without the new run, U2.1 hangs on (23.20, 68.60) and the gate names it; an entry for U2.1 is stale;
  R85.1 and R81.1 with their entries dropped fail.

## D-R21-03. Three schematic notes corrected (2026-10-31)

R21-REQ-01 / R21-REQ-02; text only, `r10_sch.py` `R21_SHEET_NOTES`.
- **sensors:** U4 is the fitted ISM6HG256X (DS15034 Rev 1 p1: high-g +/-32..256 g; FS_XL_HG codes Table 150 p93, use
  only 001 / 010, as D-R19-11), the LSM6DSV320X the consigned alternate on the same land; pins 10 / 11 open (DS15034
  Table 25 p52; the alternate the same, DS14623 table 25). Was the LSM6DSV320X (+/-32..320 g, DS14623).
- **diagnostics:** CAM_5V_SENSE lets a battery-powered self-test check the camera supply (U400 buck, U402 switch); on
  USB-only power PORT_5V3 and CAM_5V are off. Was a USB self-test of a camera regulator "U8" (no U8 on R10).
- **battery_entry:** no battery-lead fuse (owner decision OQ-6, 2026-10-28; REQUIREMENTS scopes it as pack to U9 /
  Q120). Limited only by the pack and lead: the lead, J1, BAT_IN copper, D8, C80 / C96, C88 (100 nF, BAT_IN to GND) and
  C89 / C95. U9 (TPS259470L) current-limits and latches off RAW_PROTECTED. Q120's drain (pads 5-9) is on BAT_IN, so
  the RAW_ACT fire path bypasses U9 and R134 (2 Ohm) limits it. Was "Input supply must be fused/current-limited
  externally" (and, in the first round 21 text, U9 limiting "everything after it", which left out Q120 and C88).

## D-R21-04. J400's arming chain is critical in route_check; its B.Cu jog is gone (2026-10-31)

R21-REQ-04. `tools/route_check.py` R10_CLASSES puts BAT_SW_SOURCE, BAT_SW_RETURN and BAT_ENABLE in the pyro / arming
class (AGENTS section 2.1: J400 is the arming device). They are slow filtered nodes (R165 / R81 / C87, tau about 50 ms),
so `critical_reference.R10_SLOW_RETURN_NETS` lists them for AUD-2: only the 1.5 mm partner-via and one-In2-region rules
are excluded; critical hygiene applies.
- **Jog.** BAT_ENABLE's B.Cu hop (19.675, 66.6) -> (21, 67.925) -> (21, 68.6) -> (21.3, 68.9) ended in a 0.424 mm jog
  0.3 mm off the F.Cu run (tiny_jog, now gated). Its last bend moves 0.3 mm west: (19.675, 66.6) -> (20.7, 67.625) ->
  (20.7, 68.3) -> (21.3, 68.9), a 0.849 mm 45 degree run into the via. TP120's 1.0 mm clearance and R88.2 stay clear
  (a straight (19.675, 67.275) -> (21.3, 68.9) entry missed TP120's 1.0 mm by 0.011 mm, measured); the D-R19-02 via
  (19.675, 66.6) and the S-8 keep-outs are unchanged.
- **Other hygiene the reclassification exposed.** One more on the same net: R81's removed stub (D-R21-05) left the F.Cu
  corner (19.675, 66.0) -> (19.675, 66.6) as a removable local bump; the run now turns at (19.075, 66.0) into the via on
  a 45 degree piece. Left, as counted review items (not gated): BAT_ENABLE's short_layer_hop (the B.Cu hop, 2.973 mm,
  which crosses the F.Cu RAW_ACT / ACT_* corridor). BAT_SW_SOURCE and BAT_SW_RETURN show none. route_check r10: 0
  failing.
- **Seeded test.** On a test board round 20's hop fails tiny_jog on BAT_ENABLE and the round 21 hop does not; neither
  needs a GND partner via.

## D-R21-05. R81 and C87 at U9's end of the EN run (2026-10-31)

R21-SAF-01; a partial fix for D-R20-01 (R81 is still not on B.Cu at U9.1, which has no legal spot).
- **Placement.** R81 F(20.5, 65) -> F(18.8482, 80.0) rot 0, pad 1 on the F.Cu EN run (x 18.0232). C87 F(17, 65) ->
  F(18.7232, 81.8768) rot 0, pad 1 on the run's last bend, so the run's diagonal to the via (17.1, 82.8) leaves from
  its centre (no run piece inside a pad). Pads 2 sit in the F.Cu GND pour piece of U9.8's via (20.2, 81.0).
- **Copper removed.** R81's BAT_ENABLE stub (19.675, 66.0)-(19.675, 65.0), C87's tap, both GND stubs and the GND vias
  (20.706, 65.619) (R81.2) and (16.639, 63.939) (C87.2) (`r10_fanout.tsv`). The (20.706, 65.619) via was the closest
  RAW_ACT-to-GND pad / track / via approach on the board, 0.196 mm from R134.2; the least is now 0.302 mm (RAW_ACT
  (22.8, 63.875) to U11.6; fills keep 0.25 mm).
- **Measured.** Between U9.1 and R81.1 / C87.1: three series vias -> one (17.10, 82.80); track 20.920 / 24.295 ->
  3.890 / 2.013 mm. An open anywhere up the switch run now leaves EN held low by R81 (U9 off). Foreign copper by the
  new pads (F.Cu): R81.1 (EN) 0.173 mm from the GND via (17.2, 79.9); R81.2 (GND) 0.307 mm from the RAW_PROTECTED via
  (20.3, 79.1) (the pad's rounded corner; the safety lens's 0.232 mm treats it as square); C87.1 (EN) 0.251 mm from
  the GND fill; C87.2 (GND) 0.254 mm from a BAT_FAULT_N track. An EN-to-GND
  short holds U9 off and a GND-to-RAW_PROTECTED short trips U9's limit (both fail safe); a GND-to-BAT_FAULT_N short
  reads as a U9 fault.
- **C87.** Moved too. TI SLVSFC9C section 6.1 p7: EN/UVLO absolute maximum -0.3 to 6.5 V (recommended at most 5 V,
  section 6.3). Left at the switch end with R81 moved, an open between them with J400 closed would let C87 charge
  toward BAT_IN (8.4 V) through R80 + R165 and dump into EN when the open recloses, above 6.5 V (Inference from the
  circuit). Beside R81 it never charges above the divider's 2.03 V (8.4 V x 300k / 1240k). The D-R19-10 values (R80 /
  R165 470 kOhm, R81 300 kOhm, C87 220 nF), the D-R19-02 via and the S-8 keep-outs are unchanged; so are D-R20-11's
  timing figures (same node).
- **Gate.** R81.1 / C87.1 keep one single via, (17.10, 82.80), as exact `SINGLE_OPEN_EXCEPTIONS` entries (respin: U9's
  west cell re-laid, D-R20-01). `FIXED_REFS` drops R81's round 18 spot; the post search places it.
- **Seeded tests.** Positions, the removed via and stub; round 20's two switch-end vias as exceptions are stale.

## D-R21-06. Panel-tab keep-out and tab-band copper held by K-plane (2026-10-31)

R21-GATE-03 (checks only). Deleting `R20_TAB_KEEPOUT_WEST_AFT` returned 12.498 mm^2 of In2 3V3 under the west aft tab
and the complete check.sh still passed (seed d07).
- **Keep-out.** `TAB_KEEPOUTS_R10` pins it: In2 only, outline (-0.5, 12.5) (3.0, 12.5) (3.0, 17.5) (-0.5, 17.5),
  fill-only (tracks, vias, pads and footprints allowed).
- **Bands.** `TAB_BANDS_R10` holds the non-GND In1 / In2 copper (fills, tracks, via and pad copper) under each planned
  tab's 3 mm band (ORDERING 8.1): west aft x 0-3, y 12.5-17.5: none; west forward x 0-3, y 60-65: none; east aft
  x 43-46, y 6.75-11.75: In2 RAW_PROTECTED 7.497, PORT_5V3 3.077 mm^2; east forward x 43-46, y 63.75-68.75: In2
  RAW_PROTECTED 12.244 mm^2 (re-measured on this board, unchanged). Growth over 0.005 mm^2 fails; a smaller figure
  fails as stale until re-recorded. The east tab plan stays the owner's (D-R20-08).
- **Seeded tests.** d07 fails (12.498 mm^2 3V3 and the missing keep-out), as do a moved outline corner and a keep-out
  that also bars tracks; a recorded figure above the board's is stale.

## D-R21-07. Port ESD clamps held beside their pins (K-ports) (2026-10-31)

R21-GATE-04 (checks only). D440 back at F(13.9, 17.2), 6.2 mm of track from J440.3, passed the complete check.sh (seed
d08). New rule K-ports: for each clamp of J410, J420, J440 and J9 (pins 3 and 4), the track-graph path from the pin's
centre to the clamp pad's centre, with the port's 1 k series resistor's pads removed, must exist and be at most 4.5 mm
(`PORT_CLAMPS`, `CLAMP_PATH_MAX`). Measured (centre to centre): J410 4.288 / 4.388, J420 3.975 / 3.975, J440 4.075 /
4.175 (3.157 / 3.194 pad edge to pad edge, D-R20-09), J9 3.975 / 3.975 mm. Seeded tests: d08 fails at 6.975 mm; a
clamp re-fed from its resistor's far side fails as reached only through the resistor.

## D-R21-08. Fab references present, readable and apart (K-legends) (2026-10-31)

R21-GATE-05 (checks only). A deleted, mistyped, 0.1 mm or misplaced Fab designator passed every stage (seeds d06a /
d06b / d06d / d06e). `fab_ref_crossings` now also requires, for every footprint: exactly one Fab `${REFERENCE}` text,
on its own side's Fab layer and visible; no other Fab text (LS120's "+" / "-" polarity marks allowlisted,
`FAB_TEXT_ALLOWED`); at least 0.3 mm high (`FAB_REF_MIN_H`; the smallest on the board, two parts); its ink box
crossing no other footprint's Fab outline strokes or Fab reference ink box; and its ink centre inside no other
footprint's Fab outline box (a text wholly on another part's body crosses no stroke). The board: 215 references, none
crossing or inside another. Seeded tests: d06a (Q120's deleted), d06b (R134's as "R143"), d06d (R120's on Q120's
body), d06e (R119's at 0.1 mm), a stray Fab text, a reference on the other side's Fab layer and R81's moved onto C84's
can each fail. d06c (a hidden Fab text) is not representable in KiCad 10 (the gate lens's finding).

## D-R21-09. Designators re-placed by the post search (2026-10-31)

The moved R81 / C87 and the removed vias and stubs re-place these designators through the same search (silkscreen diff
against `0dc84776…`):
- **Shown again:** C126 F(17.693, 61.175) 90, Q122 F(16.151, 66.056) 90, R122 F(20.878, 66.649) 90.
- **Moved:** C80 F(17.6, 78.902) -> F(17.593, 78.127); C87 F(14.857, 64.503) 90 -> F(19.023, 83.448) 0; C89 F(17.0,
  84.7) 90 -> F(17.594, 84.9) 0; D123 F(17.901, 62.9) 0 -> F(19.319, 63.301) 90; D8 F(19.005, 76.927) 0 -> F(19.7,
  75.0) 90; R81 F(21.558, 66.697) 0 (its round 18 fixed spot, dropped from `FIXED_REFS`) -> F(21.255, 80.983) 90.
Hidden 96 -> 93, all kept on Fab. No other designator or legend moved.

The record index is now **172 unique D IDs through D-R21-09**.
