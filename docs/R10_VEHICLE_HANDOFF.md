# R10 vehicle integration handoff

The separately owned `../../docs/VEHICLE.md` candidate entry still describes removed R10 hardware (GH connectors, ARM and IGN
terminals on the x = 0 edge, a GH-2 power-switch connector near the forward edge, the coax loop zone). This handoff supplies
the replacement facts without editing that worktree. Preserve the accepted R9 entry. R10 remains unaccepted and no physical
fit is claimed.

**Status.** PCB `a3144b15…`, 46 × 90 × 1.6 mm; not accepted, nothing ordered. It replaces `632a9ad3…` (round 18 fix pass), so the earlier clean reviews do not carry over to it;
rounds 19 and 20 will review it after the gate pass. Review results, checks, cost and open items are
in [M3_R10.md, "Current state"](M3_R10.md#current-state); the owner's decision list is in
[R10_VALIDATION.md](R10_VALIDATION.md#r10-deviations-for-owner-acceptance).

## Terminals

All coordinates are PCB millimetres, as in `m3_design/r10_place.tsv`. Every terminal is a DORABO DB125 3.5 mm screw terminal,
unkeyed: wire each one from its printed pin legend, never from the connector body.

| Terminal | Centre / rotation | Wire entry | Pins (silkscreen legend) |
|---|---|---|---|
| J121 black DB125-2 (igniter) | (7.4,55.85), −90° | west | 1 OUT (`1:E1−`), 2 IGN (`2:E1+`) |
| J400 green DB125-2 (switch) | (7.4,65.85), −90° | west | 1 and 2: the external screw-switch pair (`1:SW`, `2:SW`) |
| J1 green DB125-2 (battery) | (7.4,75.85), −90° | west | 1 BAT+ (`1:BAT+`), 2 GND (`2:GND`) |
| J410 green DB125-4 (GPS) | (38.6,15.5), 90° | east | 1 supply (`1:4V8`), 2 GND, 3 board TXO, 4 board RXI |
| J420 green DB125-4 (radio) | (38.6,31.5), 90° | east | 1 supply (`1:4V8`), 2 GND, 3 board TXO, 4 board RXI |
| J9 green DB125-4 (camera) | (38.6,47.5), 90° | east | 1 camera supply (`1:5V4`), 2 GND, 3 board RXI, 4 board TXO |
| J122 green DB125-5 (servos) | (38.6,71.5), 90° | east | 1–4 SERVO1–4 signals (`1:S1` … `4:S4`), 5 reference GND (`5:GND`) |

- **J121.** Pin 1 is OUT (net PYRO1_OUT, silkscreen `E1−`); pin 2 is IGN (net PYRO1_IGN, silkscreen `E1+`). E1+ is the supply side, fed through R134
  from the post-switch bus; E1− is the side that Q124 switches to ground. An e-match itself has no polarity.
- **J410, J420 and J9: "board TXO" and "board RXI" are the board's directions.** Board TXO is a line the board drives: wire the module's **RX** to it.
  Board RXI is a line the board receives on: wire the module's **TX** to it. On J410 and J420, pin 3 is the board's transmit line (driven by PC6 for the
  GPS and PB13 for the radio) and pin 4 is the board's receive line (PC7 and PB12), so the module's RX goes on pin 3 and its TX on pin 4. **J9 is the
  reverse:** pin 3 is where the board receives (the camera's TX goes there) and pin 4 is where it transmits (to the camera's RX). `J9 1:5V4` abbreviates the nominal
  5.456 V buck output through U402; it is not a separate setpoint or guarantee.
- **What R10 does not have:** J124, an ARM plug, link or fuse, a pull-pin, GH connectors, servo headers or tie holes, on-board radio or GNSS, and
  an SMA or coax overhang. The GPS and the LR900-F radio use the shared PORT_4V8 supply (nominal 4.792 V) and direct protected UARTs. The camera alone keeps its switch and
  UART isolation. The USB-C shell still reaches 0.45 mm past the west PCB edge.

## Power, arming and USB

The sole J400 screw switch is the power and pad-arming device, reachable on the rail; turn it on last and off first. Connect the e-match without USB or
any self-powered module (GPS, radio, camera) attached. USB bench work requires the pack or the e-match to be disconnected.
**The GPS and radio ports are fed from the battery path, so they are off on USB-only power:** during a USB-only session either disconnect the J410 and J420
leads or check that pins J410.3 and J420.3 stay near 0 V (the board's TX lines must not drive an unpowered module). Per flight, before the e-match is inserted:
with the pack connected and J400 open, measure J121.2 (IGN) to GND with a floating meter; it must read below 0.1 V.
Preserve AGENTS section 2 and the electrically isolated Blue Jay. Qualify dry contacts, strain relief, ferrules and gauge, polarity and UART order and installed RF immunity.

## Board, supports and hardware

The board is 46 × 90 × 1.6 mm. Retain the five supports at (4,4), (42,4), (4,44.3), (3.7,86) and (42,86) and underside insulation.
**Use nylon (or otherwise insulated) screws and washers at all five supports:** at (4,44.3) the exposed LED2, LED1 and J2 lands (GND, GND, 3V3 and NRST) lie
only 3.808–3.918 mm from the support centre, against a 3.8 mm washer gate. Start with the selected 4 mm standoffs, nut on the sled side and head on top; keep the nut-inclusive
h + t below 6.0 mm at x = 4 and 42 and below 5.3 mm at x = 3.7. Program J2 before installing the adjacent mid support, or remove it for programming.
Hardware maxima, eccentricity, solder tails, plate strength and shock clearance remain unqualified. The optional 100 g / D5 model (run on `632a9ad3…`, not re-run on the current board) leaves only 0.270913 mm below C431
at h = 4 mm and predicts overlap at h = 3.5 mm. This is an inference, not a physical result. The east edge carries 34 g of the 70.5 g board mass on an unsupported 82 mm edge
(see M3_R10, "East-edge asymmetry"): require a first-article vibration and shock check.

**Terminal bodies and wires.** Maximum DB125 insulating bodies are in the VRML models. The fit checker separately allocates all 23 solder tails to their native pad XY boxes and
3.80 mm maximum length below the seating plane (conservative Inference, not a solder-joint model). Their minimum calculated bore clearance is 7.558359 mm; projection below the 1.60 mm
PCB is 2.20 mm, leaving 1.80 mm to a nominal 4 mm sled plane. Seating, solder fillets and bent tails still need inspection. **Wire room** is measured to the nominal Ø 50.8 mm bore wall
at 5 mm wire height (the 0.5 mm wall allowance is not subtracted): it is 5.003012 mm at every wire face, against the accepted 4.95 mm floor, only 0.053012 mm of margin. It is not a ferrule, bend
or tool-envelope qualification. DB125 accepts 28–16 AWG; verify the actual leads, 4–5 mm strip, ferrules, screw access and retention. Its maximum body height is 8.90 mm and its tail is
3.50 ± 0.30 mm. Stake all seven terminals, including J400. The nominal Ø 1.30 mm holes and Ø 1.90 mm lands do not establish pin insertion at all process corners. Obtain the maker and assembler
insertion profile and the fabricator's hole, pattern and barrel allocation; inspect all 23 contacts for seating, undamaged plating and barrels, and solder fill. The nominal S-8 minimum of 1.050 mm (the load-switch gate and enable barrels, held by fill keep-outs; the J121.1 barrel is 1.103 mm) is not
a fabricated-clearance qualification. Exact C19/C20 combined operating capacitance and ESR, process, rework and aging, and actual regulator-mode and local-temperature qualification also remain open; see
[ORDERING section 8.2](ORDERING.md#82-assembly-order-remarks-and-placement-preview).

**microSD.** J430 is the bottom hinged Molex microSD socket at (24,24.3). The current fit check covers a 15.05 × 15.70 × 2.10 mm closed socket and card allocation, including the maker's nails
and general tolerances. Common seating and the undimensioned card front remain Inference; verify the actual assembly. Open it unpowered with the PCB removed or unbolted from a continuous sled, or
qualify a lid-access window. The maker does not dimension the full open sweep. Card retention and the selected card's latency, current and power-loss behaviour remain unqualified.

**U5.** The retained 1.1 mm model and cover height is an engineering allocation; TE's package height is 1.0 mm +0 / −0.10 (06/2017 p. 15 Fig. 18). At 4 mm the allocated gap is 2.9 mm and the
package-only gap 3.0 mm; seating, cover compression, adhesive and venting remain unqualified.

## Position in the stack, pack and harness

Keep the entire board, including axial mounting tolerance, forward of joint + 47 mm at every roll orientation (OQ-7). Freed PCB length stays slack. Do not reuse the old GH 0.03 mm margin or the SMA/coax
lead zone as fit evidence. Fit the actual pack, external GPS and radio, antenna, harness, accessible switch, sled and camera shroud together. Use
[ORDERING section 8.1.1](ORDERING.md#811-pad-energy-worksheet-d-r17-01-calculationinference) (D-R17-01): C_tested_Ah ≥ (Q_pad_board + Q_pad_motors + Q_flight_all + Q_recovery) / 0.8. The conditional
two-hour board-only capacities at camera 0 / 0.5 / 2 h are 2.265821 / 2.987991 / 5.154503 Ah under the stated 6 V and 80 % allocations; they exclude motor, flight and recovery charge and select no pack.
Keep the camera off unless recording; verify aged and cold capacity, fire-time source reserve and resistance, transients and the installed mass and dimensions. The previous approximately 80 mm pack
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

The target is $84.41 per board, R3's cost per board for parts plus JLC feeder fees only. The supplier data (stock 2026-10-30T23:50:54Z, cost 23:51:50Z) give $79.12 placed, with no minimum-purchase uplift (every minimum is 1);
JLC's fixed fees add $16.79 per board (5 boards). The cost target passes; U4 (0 < 5; consign it) alone keeps the stock release failing, and quote, process and owner acceptance are open. R430 is now C2999509 (84,923 in stock) and U9 has 45
with a minimum of 1 for 5 fitted. C84 is on the owner BOM, bought by the owner and hand-fitted after both reflows. No physical fit, firmware or order is qualified. Table and basis: [M3_R10.md, "Cost and stock"](M3_R10.md#cost-and-stock).

Current source and qualification details: [M3_R10.md](M3_R10.md), [ORDERING.md section 8](ORDERING.md), and the maker-linked `sources/r10_design/parts_qualification.md`. Apply the parent mirror update only within its
separately authorized repository workflow.
