# R10 vehicle integration handoff

The separately owned `../../docs/VEHICLE.md` candidate entry still describes removed R10 hardware (GH connectors, ARM and IGN
terminals on the x = 0 edge, a GH-2 power-switch connector near the forward edge, the coax loop zone). This handoff supplies
the replacement facts without editing that worktree. Preserve the accepted R9 entry. R10 remains unaccepted and no physical
fit is claimed.

**Status.** PCB `92c3ad59…`, 46 × 90 × 1.6 mm; not accepted, nothing ordered. Rounds 22 and 23 were the closing pair on `5516eeec…`. The round 24 board pass (D-R24-01 … D-R24-17) made `1407e850…` (among other changes it added D402, J400.2's ESD clamp, and moved C88, R92, TP88, R402 and R403); round 24's ten lenses found 0 Critical / 0 Major / 17 Minor real errors on it, and the round 24 fix pass (D-R24-18 … D-R24-23) changed the copper to `92c3ad59…` (one BAT_FAULT_N chamfer capped; no part, terminal or support moved), so no earlier review carries over to it. Round 25 then found 10 Minor real errors on `92c3ad59…` (R25-TRI-01 … -10, none on the board), and its fix pass (D-R25-01 … -03) left the board unchanged, so rounds 26 and 27 review `92c3ad59…` under the owner's strict rule (only real errors count; iteration stops after two consecutive rounds with zero verified real errors). Review results, checks, cost and open items are
in [M3_R10.md, "Current state"](M3_R10.md#current-state); the owner's decision list is in
[R10_VALIDATION.md](R10_VALIDATION.md#r10-deviations-for-owner-acceptance).

## Terminals

All coordinates are PCB millimetres, as in `m3_design/r10_place.tsv`. There are eight terminals. Every terminal is a DORABO DB125
3.5 mm screw terminal, unkeyed: wire each one from its printed pin legend, never from the connector body. Some pin legends are on the
bottom beside their pins (J121 `2:E1+`, J400 `2:SW`, J440 pins 2–4, pins 2–3 of J410 / J420 / J9 and pins 2 and 4 of J122; R23-DOCS_BINDING-09). Once wired, the wires and
bodies can hide the top legends, so **check every lead's pin identity by continuity against this table before first power**
(R19-MEC-01).

| Terminal | Centre / rotation | Wire entry | Pins (silkscreen legend) |
|---|---|---|---|
| J121 black DB125-2 (igniter) | (7.4,55.85), −90° | west | 1 OUT (`1:E1−`), 2 IGN (`2:E1+`) |
| J400 green DB125-2 (switch) | (7.4,65.85), −90° | west | 1 and 2: the external screw-switch pair (`1:SW`, `2:SW`); J400.2 is clamped to GND by D402 at B(4.45,65.9), between the pins (D-R24-11) |
| J1 green DB125-2 (battery) | (7.4,75.85), −90° | west | 1 BAT+ (`1:BAT+`), 2 GND (`2:GND`) |
| J440 green DB125-4 (spare AUX port) | (7.4,16.25), −90° | west | 1 supply (`1:4V8`, top), 2 GND, 3 board TXO, 4 board RXI (`2:GND`, `3:TXO`, `4:RXI` on the bottom) |
| J410 green DB125-4 (GPS by default) | (38.6,15.5), 90° | east | 1 supply (`1:4V8`), 2 GND, 3 board TXO, 4 board RXI |
| J420 green DB125-4 (radio by default) | (38.6,31.5), 90° | east | 1 supply (`1:4V8`), 2 GND, 3 board TXO, 4 board RXI |
| J9 green DB125-4 (camera) | (38.6,47.5), 90° | east | 1 camera supply (`1:5V4`), 2 GND, 3 board RXI, 4 board TXO |
| J122 green DB125-5 (servos) | (38.6,71.5), 90° | east | 1–4 SERVO1–4 signals (`1:S1` … `4:S4`), 5 reference GND (`5:GND`) |

- **J121.** Pin 1 is OUT (net PYRO1_OUT, silkscreen `E1−`); pin 2 is IGN (net PYRO1_IGN, silkscreen `E1+`). E1+ is the supply side, fed through R134
  from the post-switch bus; E1− is the side that Q124 switches to ground. An e-match itself has no polarity.
- **J410, J420, J440 and J9: "board TXO" and "board RXI" are the board's directions.** Board TXO is a line the board drives: wire the module's **RX** to it.
  Board RXI is a line the board receives on: wire the module's **TX** to it. On J410, J420 and J440, pin 3 is the board's transmit line (PD8, PB13 and PC6)
  and pin 4 is the board's receive line (PD9, PB12 and PC7), so the module's RX goes on pin 3 and its TX on pin 4. **J9 is the
  reverse:** pin 3 is where the board receives (the camera's TX goes there) and pin 4 is where it transmits (to the camera's RX). `J9 1:5V4` abbreviates the nominal
  5.456 V buck output through U402; it is not a separate setpoint or guarantee.
- **J410, J420 and J440 are electrically identical** (owner request, D-R19-14): the GPS or the radio may be wired to any of them. Firmware keeps the
  port map (default GPS on J410, radio on J420, AUX spare, as the silkscreen words show); record any other wiring in the firmware map before flight.
  The AUX port may draw up to 100 mA at 4.8 V beyond the GPS 150 mA and radio 300 mA (provisional until the first-article
  power-knot temperature check, ORDERING 8.3). Any device on J410, J420 or J440 must drive its TX high at no more than 3.6 V:
  no 5 V-logic devices (R20-MCU-02). Before connecting any module, check PORT_4V8 at J410.1, J420.1 and J440.1 reads
  4.71–4.87 V on pack power, e-match disconnected (R20-PWR-02). **J9 is not interchangeable** with them: it carries the 5.4 V
  camera supply, the reversed TX / RX order and an isolated UART.
- **What R10 does not have:** J124, an ARM plug, link or fuse, a pull-pin, GH connectors, servo headers or tie holes, on-board radio or GNSS, and
  an SMA or coax overhang. The GPS, the LR900-F radio and the AUX port use the shared PORT_4V8 supply (nominal 4.792 V) and direct protected UARTs. The camera alone keeps its switch and
  UART isolation. The USB-C shell still reaches 0.45 mm past the west PCB edge.

## Power, arming and USB

The sole J400 screw switch is the power and pad-arming device, reachable on the rail; turn it on last and off first. Connect the e-match without USB or
any self-powered module (GPS, radio, AUX or camera) attached. USB bench work requires the pack or the e-match to be disconnected.
**The GPS, radio and AUX ports are fed from the battery path, so they are off on USB-only power:** during a USB-only session either disconnect the J410, J420
and J440 leads or check that pins J410.3, J420.3 and J440.3 stay near 0 V (the board's TX lines must not drive an unpowered module). **Per-flight checks: use the one numbered list in [ORDERING section 8.3](ORDERING.md#83-after-delivery-probes-coating-staking-and-bench-gates), "Per-flight checklist"** (R23-DOCS_BINDING-06). In short:
touch the airframe or pad ground before J400, and keep the screwdriver grounded (ESD handling; the second layer behind D402, J400.2's clamp to GND, which cannot turn the board on and, if shorted, only holds it off, which the closed-switch check sees); board off with J400 open and J121.2 below 0.1 V before any
e-match; the closed-switch check with a 1–2 Ω dummy in J121 (PC1 raised, powered BUS / CONT and the PA6 / PA4 log checked: PA6 = VLOGIC / 11, PA4 low; then J400
open, board off within 1 s and J121.2 below 0.1 V); the igniter resistance on a meter under 40 mA; no telemetry or buzzer before closing J400 and a fresh power-up when it
closes; and the recovery order (J400 open, board off, match fired or disconnected, pack disconnected, only then USB). The NRST check is per installation, with the
board off the sled. Surface leaks at U9's EN node or a chafed J400.2 lead can hold the board on (R19-SAF-02), and an open in the one via left between EN and its
pull-down R81 can let it come on with J400 open (R21-SAF-01, Inference). R81 and C87 now sit at U9's end of the EN run, so one via, (17.10,82.80), is left (D-R21-05; kept after the round 24 re-lay of U9's input, D-R24-05); the respin item is U9's west cell. Run the J400 pair twisted, on its own ties, away from the battery and servo
power leads and from J440's leads, which leave the same west edge: a chafe from J440.1 (4.79 V) or J440.3 (TX) onto J400.2 holds U9 on
(EN 1.87 V or 1.28 V, Calculation), and J440.1 or J440.2 onto J121.1 with the bus on joins the OUT-to-GND fire class. Keep J440's leads apart from the igniter leads too.
**J440 lead routing (R20-MEC-01):** route J440's leads aft, over or around the (4, 4) nylon screw head, keep them south of
y 23.5, and take them past the aft edge on the side away from the camera shroud, tied to the sled. Never run them forward
along x = 0, where they would cross the USB-C plug zone, ride over the (4, 44.3) support head and run beside the J121 / J400
exits. The same applies if the GPS or the radio is moved to J440.
**J400 chatter (R23-POWER-02, R25-TRI-01).** Record the J400 contact state at 10 kS/s or faster under flight-level vibration. Pass only if the total
open time in every sliding 100 ms window is under 7 ms and U9 stays on for the whole run at 5.73 V (RAW_PROTECTED at TP81 never below about 5 V, or no
reset in the log); the worst-corner limit is 7.63 ms at 5.73 V (Calculation, D-R25-01). This replaces the < 10 ms and < 18 % rules; the root's round 24
< 18 % decision was wrong, because open-fraction rules pass trains that trip a worst-case U9 (ORDERING 8.3).
Preserve AGENTS section 2 and the electrically isolated Blue Jay. Qualify dry contacts, strain relief, ferrules and gauge, polarity and UART order and installed RF immunity.

## Board, supports and hardware

The board is 46 × 90 × 1.6 mm. Retain the five supports at (4,4), (42,4), (4,44.3), (3.7,86) and (42,86) and underside insulation.
**Use nylon (or otherwise insulated) screws and washers at all five supports:** at (4,44.3) the exposed LED2, LED1 and J2 lands (GND, GND, 3V3 and NRST) lie
only 3.808–3.987 mm from the support centre (J2.1 3.880 mm, J2.3 3.987 mm to the round lands), against a 3.8 mm washer gate. Start with the selected 4 mm standoffs, nut on the sled side and head on top; keep the nut-inclusive
h + t below 6.0 mm at x = 4 and 42 and below 5.3 mm at x = 3.7. Program J2 before installing the adjacent mid support, or remove it for programming.
Hardware maxima, eccentricity, solder tails, plate strength and shock clearance remain unqualified. The optional 100 g / D5 model, re-run on `50a39de5…` by the round 20 mechanics lens (R20-MEC-02) and again on `5516eeec…` by the round 22 mechanics lens, with identical figures (not re-run on `1407e850…` or `92c3ad59…`), gives a first mode of 180.8 Hz pinned (was 181.1)
for an estimated 78.6 g (was 70.5 g), and leaves only 0.261 mm below C431 (was 0.271) and 0.320 mm below C421 at h = 4 mm at 100 g; it predicts overlap at
h = 3.5 mm. These are Calculation/Inference, not physical results. The east edge carries 34 g of the board mass on an unsupported 82 mm edge
(see M3_R10, "East-edge asymmetry"): require a first-article vibration and shock check.

**Terminal bodies and wires.** Maximum DB125 insulating bodies are in the VRML models. The fit checker separately allocates all 27 solder tails to their native pad XY boxes and
3.80 mm maximum length below the seating plane (conservative Inference, not a solder-joint model). Their minimum calculated bore clearance is 7.558359 mm; projection below the 1.60 mm
PCB is 2.20 mm, leaving 1.80 mm to a nominal 4 mm sled plane. Seating, solder fillets and bent tails still need inspection. **Wire room** is measured to the nominal Ø 50.8 mm bore wall
at 5 mm wire height (the 0.5 mm wall allowance is not subtracted): it is 5.003 mm at every wire face of all eight terminals, against the accepted 4.95 mm floor, only 0.053 mm of margin. It is not a ferrule, bend
or tool-envelope qualification. DB125 accepts 28–16 AWG, but R10 leads are at most 20 AWG (22 AWG preferred; the e-match leads are 24 AWG), insulation OD ≤ 1.8 mm, bent from the wire face at an inner radius of about 1 × OD, a recorded deviation from 3 × OD practice (R23-MECHANICS-01; arithmetic in ORDERING 8.4; with P2's 0.5 mm wall allowance the room is 4.493 mm). Verify the actual leads, 4–5 mm strip, ferrules, screw access and retention. Its maximum body height is 8.90 mm and its tail is
3.50 ± 0.30 mm. Stake all eight terminals, including J400 and J440. The nominal Ø 1.30 mm holes and Ø 1.90 mm lands do not establish pin insertion at all process corners. Obtain the maker and assembler
insertion profile and the fabricator's hole, pattern and barrel allocation; inspect all 27 contacts for seating, undamaged plating and barrels, and solder fill. The nominal S-8 minimum of 1.021 mm (the PYRO1_OUT via; the load-switch gate and enable barrels and the J121.1 hole are 1.050 mm, held by fill keep-outs; J121.1 and J400.2 carry no unconnected inner rings since D-R20-05) is not
a fabricated-clearance qualification. Exact C19/C20 combined operating capacitance and ESR, process, rework and aging, and actual regulator-mode and local-temperature qualification also remain open; see
[ORDERING section 8.2](ORDERING.md#82-assembly-order-remarks-and-placement-preview).

**microSD.** J430 is the bottom hinged Molex microSD socket at (24,24.3). The current fit check covers a 15.05 × 15.70 × 2.10 mm closed socket and card allocation, including the maker's nails
and general tolerances. Common seating and the undimensioned card front remain Inference; verify the actual assembly. Open it unpowered with the PCB removed or unbolted from a continuous sled, or
qualify a lid-access window. The maker does not dimension the full open sweep. Card retention and the selected card's latency, current and power-loss behaviour remain unqualified.

**U5.** The retained 1.1 mm model and cover height is an engineering allocation; TE's package height is 1.0 mm +0 / −0.10 (06/2017 p. 15 Fig. 18). At 4 mm the allocated gap is 2.9 mm and the
package-only gap 3.0 mm; seating, cover compression, adhesive and venting remain unqualified.

## Position in the stack, pack and harness

Keep the entire board, including axial mounting tolerance, forward of joint + 47 mm at every roll orientation (OQ-7). Freed PCB length stays slack. Do not reuse the old GH 0.03 mm margin or the SMA/coax
lead zone as fit evidence. Fit the actual pack, external GPS and radio (and any AUX module), antenna, harness, accessible switch, sled and camera shroud together. Use
[ORDERING section 8.1.1](ORDERING.md#811-pad-energy-worksheet-d-r17-01-calculationinference) (D-R17-01): C_tested_Ah ≥ (Q_pad_board + Q_pad_motors + Q_flight_all + Q_recovery) / 0.8. The conditional
two-hour board-only capacities at camera 0 / 0.5 / 2 h are 2.265821 / 2.987991 / 5.154503 Ah under the stated 6 V and 80 % allocations; they exclude motor, flight and recovery charge and select no pack.
**Battery-lead route (R23-MECHANICS-04):** below the sled, up round the forward edge (y > 90) and into J1 from the west, tied to the sled's forward end; never aft along the west top side. Give each terminal a sled tie point within about 20 mm of its wire face, and anchor J121's leads at the forward-bulkhead pass-through. **Sled under the east 1210 column (R23-MECHANICS-02):** a relief pocket at least 1.5 mm deep under C411 / C421 / C431 (x 31.5–41, y 20–60), or 4.5 mm standoffs with a plate thinner than 0.8 mm (h + t < 5.3 mm at x 3.7; the plate model puts C431 onto a 4 mm sled at 125 g, Calculation/Inference). Keep the camera off unless recording; verify aged and cold capacity, fire-time source reserve and resistance, transients and the installed mass and dimensions. The previous approximately 80 mm pack
description and the retired 2.6 / 4 Ah examples prove none of them.

## Boot, programming and retained deviations

Future R10 programming must record and read back the intended user-flash BOOT_ADD0 and the relevant boot settings, then verify that reset reaches the bound application, with the e-match disconnected.
BOOT0 low alone permits ROM entry at BOOT_ADD0 = 0x1FF0, and PA2 can then drive loader USART2_TX onto servo3. No actual programming, readback or R10 firmware is claimed. Preserve the
dummy-load / no-e-match, before-IWDG, locked-low PC1/PE4, camera EN/OE low and SD_CS high service procedure.

**R16 retained MEMS stress deviation (R16-MEC-01, Minor).** Component-side B.Cu still crosses U4's nominal body outside its lands: IMU_CS 0.7596 + 0.0918 mm, SPI1_MISO 0.3257 mm, IMU_INT1 0.3250 mm and
3V3A 0.3257 mm (0.001 mm midpoint sampling; native body x 15.50..18.50 / y 44.65..47.15). Signal widths are 0.20 mm; the 0.25 mm 3V3A rail also departs from the same-width guidance. These specifically depart from
[ST TN1383 Rev 1 pp. 7–9](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf) pad-axis and outside-body stress guidance. The R15 GND correction and
the passing M-7/P3 checks are narrower than complete compliance. The bounded supply prototype has only 0.106949 mm clearance; the next combined recipe creates an acute 45° CS junction at B(14.2,44.7). Both are rejected, with
no production copper change and no full PCB, CLI or gate qualification of that MEMS recipe. Retain first-article bias, temperature and vibration qualification.
[Prototype evidence](../m3_design/assembly_review/sources/r10_review/round16_minor_prototypes.json) and R16-MEC-01 / D-R16-02 preserve the limits; no offset error or physical failure is demonstrated.

## Cost

The target is $84.41 per board, R3's cost per board for parts plus JLC feeder fees only. The supplier data, run on the final files of `1407e850…`, whose BOM and CPL `92c3ad59…` keeps byte for byte (cost 2026-11-02T01:43:55Z, bound to the JLC BOM, owner BOM and current CPL; stock 2026-11-02T01:42:53Z, bound to the BOM and owner BOM), give $85.60 placed (about $86.14 with JLC minimum purchases);
JLC's fixed fees add $16.79 per board (5 boards). **The cost target fails by $1.19:** the owner-approved AUX port (+$1.14) and, since round 24, D402 (a ninth C535146 at $0.2306; with price movement the files went from $85.36 to $85.60, D-R24-11); the owner decides whether to accept it. U4 (now the ISM6HG256X) shows 9 in stock but only 2 orderable, so the stock check (`stock_check.json` 2026-11-02T01:42:53Z) fails on U4, 2 orderable against 5, and also on U9 (TPS259470LRPWR C3662793: 28 in stock, −83 orderable, minimum purchase 7); it reads JLC's `canPresaleNumber` as the orderable quantity, an Inference about JLC's field. For both, confirm the quantity in the JLC cart on order day, else consign franchised parts (R20-BOM-01); for U4 that means consigning franchised ISM6HG256XTR (same CPL rotation and register map), with the LSM6DSV320X, also unavailable at JLC and LCSC, only as the second-fallback alternate (needs part fields, BOM and CPL regenerated: ORDERING 8.1; R21-BOM-02, R23-DOCS_BINDING-08).
Quote, process and owner acceptance are open. C84 is on the owner BOM, bought by the owner and hand-fitted after both reflows. No physical fit, firmware or order is qualified. Table and basis: [M3_R10.md, "Cost and stock"](M3_R10.md#cost-and-stock).

Current source and qualification details: [M3_R10.md](M3_R10.md), [ORDERING.md section 8](ORDERING.md), and the maker-linked `sources/r10_design/parts_qualification.md`. Apply the parent mirror update only within its
separately authorized repository workflow.
