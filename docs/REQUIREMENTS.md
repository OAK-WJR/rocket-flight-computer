# Flight computer requirements (first principles)

What the board must do, derived from the project goals (`../../CLAUDE.md`), the owner's decisions,
the flight envelope of both flights, and the board's own design points. Every design review checks
the board against this file. Verification column: **CAD** = KiCad files and checks, **Calc** =
datasheet calculation, **Bench** = measured on a built board, **Flight**.

## Sources

- **Project goals:**
  - hold roll rate near zero, and fly a commanded roll program (e.g. a 90° turn and hold);
  - flight 1 on an AeroTech K850DM, about Mach 1.45, roll only (owner confirmation; parent CLAUDE.md);
  - flight 2 on an L1000W, about Mach 1.9, possibly adding pitch/yaw;
  - single deploy at apogee: one primary pyro channel, with a fully isolated Featherweight Blue Jay backup.
- **Owner decisions:**
  - one board flies both flights with no respin, so flight 2's worst case applies now;
  - flight condition (Mach, dynamic pressure) is estimated from accelerometer + barometer;
  - roll angle is integrated gyro, relative to the orientation at liftoff;
  - on a flight-computer reset, hang or brownout the tab must return to neutral quickly;
  - roll control is active during the burn as well as the coast (exact start and stop points open);
  - flight 2's pitch/yaw surfaces are undecided, so the board's 4-servo limit becomes their constraint;
  - no in-flight tab-deflection sensing (servos are characterised on the bench, under load);
  - external EBYTE E22-900T22D telemetry radio and HGLRC M100 Mini GPS on separate UARTs; the radio uplink must never arm or fire recovery;
  - Tripoli/NAR safety code.
- **Flight envelope:** the parent project and owner confirmation supersede the old I500T baseline.

  | | Flight 1 (K850DM) | Flight 2 (L1000W) |
  |---|---|---|
  | Motor / booster | 54 × 635 mm / 721 mm | 54 × 635 mm / 721 mm |
  | Max Mach, project design point | About 1.45 | About 1.9 |
  | Vehicle mass, axial acceleration, altitude and duration | Recalculate for K850DM; do not reuse the I500T values | Earlier L1000W estimate: 3.7–4.9 kg, 28–37 g, 3.4–3.6 km, 460–525 s; update for the current vehicle and Mach 1.9 design point |

  These are project design points and inherited estimates, not flight measurements.
  K850DM certification lists 2041 g motor mass and 1224 g propellant; the old vehicle
  2.36/2.05 kg mass pair is not applicable. Sources and disposition: M3_R6.md.
  Keep ≥ ±64 g accelerometer capability (U4 supports higher ranges), ±4000 dps gyro,
  a ≤30 s high-rate control window, ≥10 km barometer capability and the 100 g
  retention design load. Final vehicle simulation/weighing must establish that the
  selected sensor ranges, logging duration, servo/harness loads and battery reserve
  cover both flights before launch.

  The earlier M0.9 stuck-tab roll estimate was about 1100 °/s; the earlier uncontrolled
  roll estimate was 1000–1850 °/s. They are historical estimates, not K850DM predictions.
  Scaling the latter linearly to M1.9 approaches ±4000 dps (Inference); verify range
  and control margin against the updated flight model.

## Functional

| ID | Requirement | Verified by |
|---|---|---|
| F1 | Gyro range ≥±4000 dps on the roll axis. Proposed roll-angle error budget ≤5° over a ≤30 s powered/coast window, with pad zeroing and MCU timestamps. The inherited ST figures (0.006 dps/°C bias drift, approximately 0.02° angle random walk, ±0.3% typical sensitivity and ±1% output-rate accuracy) are not worst-case vibration/high-g performance. Recheck the current datasheet, measure temperature/vibration/acceleration sensitivity and validate the current Mach 1.45/1.9 flight model. A failed or stuck control surface may still saturate the gyro; do not infer fault-case range from the former I500T trajectory | CAD, Calc, Bench |
| F2 | Accelerometer covers every axial acceleration of both flights without clipping (≥ ±64 g, for margin over 37 g), plus a precise low-g channel for pad calibration and coast | CAD (part), Calc |
| F3 | Barometer works to ≥ 10 km. It is not trusted near Mach 1, where the accelerometer carries the estimate | CAD (part) |
| F4 | Four servo PWM outputs, 3.3 V logic at 333 Hz, feeding HV servos directly from the 2S pack. Each servo stalls at ≤1.92 A, total ≤7.7 A. Size and independently solve the final R6 copper at this load, including pad/via transitions and necks; perform a thermal-camera stall test. R5’s 4.82 mΩ calculation is historical and does not qualify changed R6 copper. J122’s 3 A/contact claim remains manufacturer information without a datasheet (MARGIN_PRESCRIPTION). This bounds flight 2 servo selection; hinge loads above the available M1.2 CFD sweep and at the current M1.45/M1.9 flight design points remain to be established | CAD, Calc, Bench |
| F5 | IMU sampled at ≥ 800 Hz. 16 MB flash holds a whole flight 2 under this logging policy: 500 Hz from launch to apogee + 30 s, ≤ 50 Hz on the parachute, ring buffer before launch. The flash keeps up with ≥ 25 % margin: page programming takes up to 3 ms per 256 B, so records are ≤ 128 B at 500 Hz | CAD (part), Calc |
| F6 | Failsafe. **Hardware:** servo signals are a defined low through reset, brownout and boot; the logic supply rides through power-switch bounce of ≥ 0.15 s from the 7.4 V launch floor up (worst case 0.21 s at 7.4 V; 0.11 s at 6.0 V; about 0.13 s if four servos are stalled at the 7.4 V floor at the same moment, Inference), and the dips of a four-servo stall from a pack inside the operating assumptions below; pyro gates are off in reset. **A brownout longer than the ride-through** restarts the board in up to about 1.1 s (C87 recharges through 227 kΩ); meanwhile the servo is powered without pulses, then unpowered. **Tab to neutral quickly** after a reset or hang (target ≤ 50 ms from fault to neutral command, proposed here): neutral is the first servo output after any reset, and a stalled roll loop is caught and the tab commanded neutral within the target without waiting for a reset. No single sensor, bus or loop failure may cause repeated resets or block deployment, and the watchdog is serviced in every phase from the pad to landing (FMEA V-1: a watchdog started in hardware and fed by the IMU-driven loop resets forever if the IMU never comes up). Allocation that meets both: FMEA F-1's structure (a 100 Hz safety task, independent of the IMU, supervises the roll loop and alone feeds the hardware watchdog at the end of each complete pass) with the IWDG period cut from ~400 ms to ≤ 32 ms; the roll-control interrupt bounds its own run time (a timeout on every sensor transfer), so only a fault can starve the safety task, and the watchdog then resets the board; reset release takes up to about 6 ms after a watchdog reset (C24, 100 nF on NRST, charging through the MCU's 30–50 kΩ pull-up; MARGIN_PRESCRIPTION P1-6), and neutral (1520 µs) follows within about 10 ms of release (clock and timer start-up, Inference). Any hang, in the roll interrupt, the safety task or the CPU, then ends in a neutral command within about 48 ms, while a dead IMU stops the roll interrupt instead of resetting the board. Work that cannot fit a ≤ 32 ms pass (flash erase) runs before flight or in bounded slices. The board supports this as built (STM32H743 IWDG from the 32 kHz LSI, servo lines a defined low through reset); it is a firmware requirement, verified on the bench. The HV6120's behaviour with no pulses, unpowered under hinge load, and with its input against the board's 11 kΩ reset pull-down is measured on the bench. A break in the battery lead itself is ridden through for only about 5–15 ms (C84; about 1–3 ms with the camera on, since C84 then also feeds it through U11, Inference): the battery harness has crimped or soldered leads and a locking fuse holder. **Pyro after a reset in flight:** re-enabled only under FMEA §7.4′.4 (live post-lift-off evidence), never by default | CAD, Calc, Bench |
| F7 | Recovery: one primary pyro channel (CH1, J124 ARM and J121 IGNITER 1), with continuity and arm sensing and an external 5 A arming fuse. Fire 1–2 Ω e-matches with ≥1.5× their all-fire current for ≤20 ms at the 7.4 V launch floor, including the harness. The retained CH1 budget is 7.4 V / (0.15 Ω pack + 2 Ω R134 + 2 Ω e-match + ≤0.3 Ω leads/fuse/arming harness) = 1.66 A against 1 A all-fire. This assumes idle servos: command all servos neutral ≥200 ms before fire; three/four concurrent stalls do not meet the all-fire margin. Revalidate on the final copper and harness. The independent Featherweight Blue Jay has its own battery and deployment circuit, with no shared electrical connection. No CH2 hardware, net, MCU binding or second on-board recovery event remains | CAD, Calc, Bench |
| F8 | Tripoli/NAR. Pyro is disarmed until the ARM plug goes in on the pad; the ARM plug is a complete break of the CH1 pyro bus; nothing fires at power-up or reset, on ARM-link insertion or removal (contact bounce included), or while armed with the MCU unpowered, in reset, booting or idle (bench gates with dummy loads before any real igniter, ORDERING §5). Power is switched by an external reed/magnetic or dry-circuit switch. Pyro terminals cannot be mistaken for the battery or camera terminals: black ARM and orange igniter 2-pin screw terminals, green 4-pin battery/switch terminal J1, and a keyed 4-pin GH camera connector, with unambiguous pin legends. Radio SH7 and GPS SH4 are keyed and share a separate edge block. **How the ARM links go in on the pad is open** (FMEA H-6): an external arming plug wired to J124, with its 5 A fuse at the board end of the RAW lead so the plug only joins fused RAW to BUS, or links fitted before the airframe closes with the power switch as the pad arming device (then the switch must be operable on the rail with an audible state, and the camera must be verified not to back-feed its 5 V input, which would otherwise power the pyro buses with the switch open). Pyro copper keeps its spacing on every layer, enforced by DRC (`m3.kicad_dru`, nine rules): RAW_ACT ≥ 1.0 mm from bus and igniter copper (the ARM break), ≥ 0.5 mm from every gate and sense net and ≥ 0.3 mm from RAW_ACT_SENSE; bus/igniter/drain ≥ 0.5 mm from gate nets, all GND copper and every other live net, and ≥ 0.3 mm from sense nets; gate nets ≥ 0.3 mm from every other live net inside the pyro block; and, against a single solder bridge, every exposed bus, igniter, drain and RAW_ACT pad ≥ 1.0 mm from every sense and gate pad and every divider-midpoint pad ≥ 1.0 mm from every gate pad, the actuator switch's gate nets included (rule H). Exposed gate copper near bus or 3V3 copper is covered by the mandatory local coating (P3). No single shorted or open resistor in a sense divider may drive an MCU pin past its ratings or pass meaningful current through an igniter: each divider's top is two 5.1 kΩ in series and its bottom two 2 kΩ in parallel, so any one fault leaves the node at ≤ 1.4 V (3.3 V at the 19.9 V clamp) and an armed igniter at ≤ 1.4 mA; each ADC pin also has its own 4.7 kΩ (R168, R170 and R172 (the surviving CH1 and RAW_ACT ADC paths)), which limits the current if two faults coincide (both halves of a top shorted: about 1 mA into the pin, Inference, igniter ≤ about 9.4 mA). The plug-out FET-short self-test (FMEA H-1) is possible in hardware (cold pull-up) | CAD, Bench |
| F9 | Interfaces: 2S LiPo input (6.0–8.4 V) behind an external 15 A fuse, surviving reverse polarity and a wrong 3S pack (the logic stays off; at 12.6 V only the 10 kΩ input bleed and U9's own OVLO-state draw conduct, about 1.5 mA). A chafed power-switch wire, or a battery lead in the switch terminal, must not damage the board. A reverse-polarity hot-plug through a harness of 0.1–2 µH and ≥ 0.03 Ω keeps U9's input inside its limits (−15 V, 10 V/µs), also when it follows an unplug by two seconds or more (whatever the input still holds then: with the switch closed the actuator FETs can stay on for about 1.3 s after an unplug, so the operating rule is to wait 2 s and see TP80 below 1 V, with the ARM links out for every pack change). In every fault case above (TVS clamp at 19.9 V, wrong or reversed pack, chafed switch wire) no MCU or sensor pin exceeds its absolute maximum rating: the sense dividers keep every ADC pin ≤ 1.81 V at 19.9 V (1.78 V for the pyro and RAW_ACT dividers, 1/11.2). USB-C for configuration and log download, with reliable plug and unplug detection; it is used with the board out of the bay (J3 faces the airframe wall when installed). Camera 5 V ≤ 1 A plus UART; the camera must not drive its own 5 V input (back-feed). Pull-pin input: an advisory pad-arming witness (FMEA F-7), ignored after launch; launch itself is detected by the accelerometer (FMEA F-6), so the pin never starts the roll reference, the control window or flight logging. Audible status by buzzer | CAD, Calc, Bench |
| F10 | Camera GH4 retains its existing 5 V/GND/UART nets and RunCam Device Protocol. Radio SH7 serves only EBYTE E22-900T22D (M0, M1, RXD, TXD, AUX, VCC, GND); GPS SH4 must mate correctly with the HGLRC M100 Mini included lead. Use free MCU UARTs, 1 kΩ series protection on every harness signal, connector-side ESD protection, and a separately enabled 5 V buck plus harness limiter, off during reset. Both UARTs, bootloader pin behavior, module supply limits, exact contact mapping, powered/unpowered backfeed and fault indication must be verified. A simultaneous camera fault and UART-harness fault must not trip the main input limiter across operating corners and startup. Radio commands can never arm or fire recovery. Record new firmware bindings; no firmware is implemented by this PCB task | CAD, Calc, Bench |

## Physical

| ID | Requirement | Verified by |
|---|---|---|
| P1 | 46 mm wide; target length 80–90 mm, maximum 110 mm if required for routing or robustness (owner). Fit the Ø50.8 mm coupler along the complete board length. Record final outline, orientation and bay stack in M3_R6 and parent VEHICLE; historical R5 geometry is not R6 evidence | CAD, Calc |
| P2 | Every fitted part and every mated plug with wire bend fits the Ø50.8 mm bore with 0.5 mm wall allowance. The sled places the top PCB face on the bore axis and centers it within ±0.3 mm in both transverse directions. Check all part models and explicit GH/SH/servo/pull-pin mating envelopes. Provide five M3 supports, four corners and one effective mid-span support; ≥3.5 mm bottom part/pad clearance around each support, nylon hardware, and a non-conductive sled clear of all bottom parts and pin tails. Preserve both servo retention holes and clearance for its approximately 4 mm-wide underboard tie path. Re-derive all positions and support-span/vibration estimates on final R6 geometry; qualify actual sled, harness and camera-shroud fit | CAD, Calc, Bench (fit) |
| P3 | Survives both specified flights' boost and vibration (updated K850DM acceleration qualification pending), ejection and landing shock: every connector and tall part holds ≥ 5× its load at 100 g, and two-terminal tall parts are staked (MARGIN_PRESCRIPTION R14; checked by inspection after staking, no vibration level is specified). Mated connectors have external retention (zip ties, or RTV where no tie point exists, as at J123). No vias or copper fill under MEMS sensors on the component side. Tall cans and terminals are staked. **The pyro block and J2 are locally conformal-coated** (MARGIN_PRESCRIPTION §4.13; masking list in ORDERING §5): roughly 13–22 kΩ of leakage from 8.4 V to a gate turns its FET on, and the main section flies twice | CAD, Bench |

## Manufacturing and cost

| ID | Requirement | Verified by |
|---|---|---|
| M1 | JLCPCB 4-layer, 1.6 mm, 1 oz outer and inner, ENIG, Standard PCBA including through-hole parts. Every part in stock for 5 boards. Every placement-file rotation verified against JLC's footprint. Every part rated, per its maker's datasheet, for Standard PCBA's 240 ± 5 °C reflow: U5 (MS5611) and C84 (OS-CON SVPK) allow a 250 °C peak; the replacement LS120 needs its own verified profile, below Economic PCBA's 255 ± 5 °C. C121 (jieerrui MA25V470M8x10) has no maker datasheet: inspected and measured on the bench | CAD, tools |
| M2 | Design rules within JLC's limits. No via holes open into soldered SMD pads, and every via hole ≥ 0.1 mm from a pad opening (bare test pads may carry in-pad vias). Courtyards enclose pads. Paste apertures follow the makers' stencil guidance where it exists, IPC-7525 practice otherwise. Through-hole GND pins use thermal reliefs wherever their spokes are not starved (exceptions listed in M3_R4 §2). Silkscreen ≥ 0.15 mm lines, ≥ 1.0 mm text, never on pads or off the board edge | CAD |
| M3 | Lowest cost that keeps every requirement above. R6 must not cost more than R3 per board at 5 boards, counting what parts cost the owner: placed-quantity prices plus JLC's per-part feeder fee for the tier ordered (Standard: $1.53 per unique code, Basic or Extended; Economic: $3.07 per unique Extended code). Standard's fixed fees (setup and stencil per assembled side, plus the fixture: $50.19 per order for R4's one side, $83.96 for R5's two, plus a $14.93 handling fee JLC may add, against Economic's $9.71 for one side only) and JLC's edge rails buy the reflow margin M1 needs; `tools/jlc_cost.py` reports them without gating them. R3: $54.94 + 48 × $3.07 / 5 = $84.41, with a hard limit of 48 unique extended codes (`tools/jlc_cost.py`; it also reports the order price including JLC minimum purchases, which must not hide a large surcharge) | tools |

## Operating assumptions (the board's design points; set by the vehicle and its procedures)

| Item | Assumption | Why the board needs it |
|---|---|---|
| Pack | 2S LiPo (not LiHV), ≥ 1.0 Ah for flight 1 and ≥ 1.5 Ah for flight 2 (pad-time row), ≥ 7.4 V resting at launch after the pad wait, ≤ 0.15 Ω source resistance at the coldest pack temperature, including leads, connector and fuse | Four stalled servos must leave BAT_IN above U9's worst-case turn-off (4.78 V); the servos are rated to 8.4 V |
| Pad time | ≤ 2 h with the camera off until arming: about 70 mA typical on flight 1, up to about 290 mA worst case on flight 2 (four idle servos, peripherals on). The camera adds 0.24–0.77 A at the pack for 0.3–1 A at 5 V: with a 1 A camera on for the last 30 minutes, flight 2 needs about 1.3 Ah, so use a pack of ≥ 1.5–2 Ah or a ≤ 0.5 A camera. No reserve is budgeted for the wait after landing; switch off promptly (U9 turns off only at about 2.2 V per cell) | Pack capacity above |
| Igniters | 1–2 Ω e-matches, all-fire ≤ 1 A within ≤ 20 ms (bench-fire the chosen e-match at about 1.3 A for 20 ms; the board drives 1.3–2.8 A for ≤ 20 ms, from 6.0 V with 0.15 Ω source and 1 m of 26 AWG to 8.4 V into 1 Ω), no-fire well above the 0.75 mA continuity current and at least about 20 mA: one shorted divider resistor passes at most 1.4 mA through an armed igniter, and both halves of one divider top shorted (two faults) about 9.4 mA | F7 |
| ARM link | One CH1 2-wire link, with a 5 A fast-acting fuse at the board end (ORDERING.md §7) | F7, F8 |
| Board position | Aft edge about 70 mm below the coupler's forward end, ± 3 mm | Where the board sits in the stack; R5 fits the coupler bore along its whole length (P1, P2), so the position no longer limits the fit |
| Temperature | Bay −20…+70 °C (the buzzer's rating sets the cold end; ≤ 70 °C on the pad in sun) | The IMU, barometer and flash are rated −40…+85 °C; the buzzer −20…+70 °C. The MCU's junction limit is 105 °C at 480 MHz (VOS0) and 125 °C at ≤ 400 MHz (VOS1), with 45 °C/W (DS12110). A typical part draws 0.4–1.1 W at 480 MHz, a worst-case part 1.3–1.8 W, and even at 400 MHz a worst-case part settles near 126–128 °C in a 70 °C bay. So firmware runs at 200 MHz (300 MHz at most) from power-on to landing (flight 2 lasts up to 525 s), or at 400 MHz only together with junction-temperature monitoring that throttles the clock. The 70 °C bay assumes a shaded or vented bay on the pad; DESIGN_ASSURANCE §6.1 gives 85 °C as the unshaded worst case, where 200 MHz keeps a worst-case MCU near 110–120 °C (Inference) |
| Static ports | Bay vented so the barometer sees ambient pressure; opaque black foam over U5, and both LEDs dark from arming to landing | F3 |
| Camera | Draws ≤ 1 A at 5 V and does not drive its own 5 V input: a back-feeding camera (internal battery) turns on the actuator rail, and can boot the logic, with the switch open (bench check) | F9 |
| Battery harness | 0.1–2 µH and ≥ 0.03 Ω (any real 2S harness with a blade fuse); crimped or soldered leads, a locking fuse holder | F6, F9 |
| Storage | The pack is disconnected between uses: the input bleed (R167) draws 0.84 mA with the switch open, so a 1 Ah pack is flat in about 7 weeks | Pack health |

## Accepted risks (recorded decisions)

- **No on-board servo-fault containment.** A hard short on a servo lead or inside a servo draws tens of amps from the pack until the external 15 A fuse opens. The primary computer goes down with it, and recovery relies on the isolated backup altimeter (R2_VERIFICATION §2). On-board fusing of four servo feeds does not fit the 2.54 mm header's middle row. If containment is wanted, put an inline fast fuse on each servo's + lead in the harness.
- **The tab's state while the computer reboots depends on the servo** (hold or go limp with no pulses): bench item under F6. A brownout longer than the ride-through extends the reboot to about 1.1 s.
- **Flight 2's servo harness** runs in an external raceway at up to M1.75, so a lead short is more likely: per-servo inline fuses are recommended there.
- **A reversed 3S pack** (two faults at once) can ring U9's input to about −19 V, past its −15 V limit.
- **Harness miswiring remains hazardous.** Camera J9 is now keyed GH, eliminating the former green screw-terminal ambiguity. An incorrectly assembled adapter can still put a recovery load on a powered harness; continuity-check connector polarity and wiring with all recovery loads disconnected.
- **Gate-net spacing outside the pyro block** is the board's 0.15 mm default (under mask or inner layers, covered by JLC's electrical test; a bridge to an always-on net shows in the plug-out cold test). Inside the block DRC keeps 0.3 mm.
- **No hardware revision ID**: firmware cannot tell this board from another revision by itself; the firmware build is bound to the board by hash (AGENTS.md §3).



## R6 implementation contract — 2026-10-13

The authoritative R6 objectives for this iteration are the user's supplied technical objectives. Acceptance requires tools/check.sh with zero DRC, unconnected, schematic parity and ERC findings; check_actuators.py and fit_check.py OK; no Critical/Major independent-review findings; cost ≤ $84.41/board and ≤ 48 extended codes; regenerated fabrication outputs. These release conditions are not yet all satisfied.

Selected peripheral modules: EBYTE E22-900T22D and HGLRC M100 Mini. The nominal 5 V peripheral branch is implemented at 4.8 V to respect the GPS's specified 5 V maximum under DC component tolerances. Verify startup and load-transient peaks on hardware. Reset disables the AP63301 and upstream current switch; GPIO must be high impedance around software-controlled power transitions. J131 requires a verified harness using the documented pad-number contract.

The present mechanical choice is 46 × 100 mm: it meets the 110 mm maximum, while the preferred 80–90 mm length remains unmet. Preserve five supports including the mid-span hole, channel-1 spacing, 1 mm exposed-test-pad foreign-copper clearance, 0.3 mm RAW_ACT through-hole foreign-copper clearance, minimum-size thermal relief on small GND pads, no vias on through-hole pads and no overlap-only joints. The flash bypass requires a short direct connection at VCC.


## R6 validation checkpoint — 2026-10-13 continuation

The current PCB remains a work in progress, not released for fabrication. Six connections remain open: GPS_TX_MCU, TLM_FAULT_N, SWCLK, RADIO_M1_MCU, IMU_INT1 and RADIO_AUX_MCU. The existing fab package predates this checkpoint and must be regenerated after final validation.

All 13 overlap-only joint findings were repaired (10 centerline bridges, 3 redundant stubs removed), preserving connected pad groups and existing reference coverage. The long IMU In1 routing experiment was rejected for a Major ground-return detour near the oscillator and MCU decoupling. Its helper now rejects normal application. SWCLK candidates also remain unapproved pending VCAP2/reference-island repair.

This checkpoint supersedes earlier port-enable pin assignments: TLM_PWR_EN is now PB12 / U1.51 through R192 1 kohm; PE1 / U1.98 is NC. TLM_FAULT_N remains PE0 / U1.97. The external R193 10 kohm pulldown keeps the supply disabled during reset. Firmware must use PB12 as the enable output and preload it low before configuring output mode. PB12 is a non-debug GPIO with analog reset state (ST DS12110 Rev 11, section 3.8 and Table 9: https://www.st.com/resource/en/datasheet/stm32h743vi.pdf). All radio/GPS UART and mode pin assignments remain as specified.

The synchronized PB12 schematic/PCB passed native ERC and schematic parity with zero findings, the actuator contract, and 13 R6 geometry regression tests. The routing change introduces no In1 signal tracks, no additional existing front-trace reference losses, and zero losses over 104241 critical reference samples. Numbered connector legends were regenerated, including J9 3:TX / 4:RX from the peripheral perspective; all 40 required labels fit. R6 CAD contract, silkscreen bounds and fit checks pass. Native connectivity still reports six opens and dangling copper; tools/check.sh is not yet zero.

Board size is 46 x 100 mm: below the 110 mm maximum, outside the 80–90 mm target. Procurement remains on hold for the previously identified unavailable U4; prior cost estimates require final BOM/fab revalidation. Final independent review could not resume because the review agents reported exhausted workspace credits. No final Critical/Major clearance or hardware qualification is claimed.

Evidence: m3_design/assembly_review/sources/r6_validation_iterations.json, r6_joint_integration.json, r6_enable_pb12_packet.json, r6_enable_pb12_migration.json, r6_silk_integration.json, r6_current_contract.json and r6_current_fit.json.

Update: the existing independent review agents resumed successfully after the credit error. Their renewed reviews are pending. Full tools/check.sh checkpoint reports 6 opens, 10 dangling vias and 5 dangling tracks; ERC and parity remain zero.


### 2026-10-13 SWCLK validation iteration

The reviewed SWCLK crossover is now integrated (PCB SHA256 3c2525af6720fb123a95393b0885d20c43defba78d9c2f1fee6bf054149777a9). Native candidate DRC reports five remaining unconnected items and zero hard violations. Independent review finds zero Critical or Major issues for this change. Its short back-layer crossover restores the original 5.697 mm transverse MCU ground path; reviewed HSE and C17/C20 ground returns remain unchanged. All 104,241 critical reference samples are preserved. One Minor finding remains for reduced direct reference under the USB fault monitor and an auxiliary stitching-path detour. R128 pad 2 uses a 22.5 degree thermal angle with existing gap, spoke width and minimum-spoke rules retained. The replay helper reproduces all added copper and is idempotent. Fault-input and IMU remapping candidates are still under review and are not part of this checkpoint. Full zero-error acceptance and regenerated fabrication release remain pending.


### R6 routing and pin assignment checkpoint — 2026-10-13

The reviewed PA7 port-fault route and radio M1 route are integrated. Port enable remains PB12 with the hardware reset-off pulldown. IMU INT1 moves from PE10 to PE1 as a plain polled input; PD1 retains EXTI1. PE3/PE6 and all channel-1 guard pins remain no-net sentinels, with PE3 driven low by the bench firmware. The schematic/netlist pin-map delta is exactly U1.40 and U1.98. Native ERC and schematic parity are zero; actuator and R6 contracts pass. The PE1 firmware change passes 42 host tests; no ARM binary was built because an ARM compiler is unavailable.

The current PCB has two remaining unrouted signals (GPS TX and radio AUX), 13 dangling-copper warnings and no other native DRC errors. Independent reviews found no Critical/Major defects in the adopted routes; minor auxiliary ground-return detours remain recorded. The board is 46 × 100 mm: within the 110 mm maximum but outside the preferred 80–90 mm length. This is an intermediate checkpoint, not fabrication release.

The legacy GNSS bench driver still assigns GPS to USART6. R6 hardware assigns GPS to USART1 PA9/PA10 and radio to USART6 PC6/PC7; firmware bring-up must migrate the GNSS driver and keep port outputs high impedance while port power is off. The existing bench firmware is not an R6 flight-firmware release.


### Fully routed R6 checkpoint — 2026-10-13

GPS TX and radio AUX are now connected. The saved PCB has zero unrouted connections, 13 existing dangling-copper warnings, and no other native DRC errors. The final AUX review found zero Critical/Major issues after restoring two MCU ground returns: a 1.273 mm, 0.25 mm wide In2 ground bridge between existing vias, and a local AUX/GPS-RX layer change that preserves the baseline ground passage. All 104,241 sampled critical-signal reference points remain supported. Minor auxiliary return detours are recorded in the independent review archive.

Fabrication release remains held for the newly identified U12 camera UART translator bypass issue: C100 is too far from VCCA and is being moved close to its supply pin. Final dangling-copper cleanup, combined review, all required checks and fabrication regeneration will follow that fix. The prior temporary candidate passed the complete automated gate but was rejected by the independent ground-return and decoupling reviews; it was not adopted.


## Final R6 CAD validation — 2026-10-13 PDT

This is the authoritative closeout checkpoint. PCB SHA-256: `184a87e84e67576341244c82517de3e9f55f5c1c22995dfad83631d48c856680`.

The requested R6 CAD changes are implemented and fully routed: channel 2 removed; J9 is GH4; LS120 is the smaller MLT-5020 (C94598); J2 is TC2030; radio and GPS use USART6 and USART1 respectively with 1 kΩ series resistance and ESD protection; AP63301/TPS2553 port power is reset-off. The port rail is 4.8 V nominal to respect the HGLRC M100 Mini 5 V maximum. PB12 enables power and PA7 reads fault. IMU status moved to PE1 as a polled input only; PD1 keeps EXTI1 and the pyro-adjacent PE3 sentinel remains output-low.

The final review/implementation loop closed the remote camera-translator VCCA bypass, ground-return barriers and incomplete connections. C100 is now beside U12 on B.Cu, with a 1.362 mm supply centerline and 1.503 mm direct ground centerline. Final cleanup removed 38 dangling copper items, repaired one overlap-only joint, and regenerated 40 required legends. No retained component geometry or clearance rules changed during cleanup.

`tools/check.sh` passed: DRC 0, unconnected 0, schematic parity 0, ERC 0; metadata/models, silkscreen, R6 contract, `check_actuators.py` and `fit_check.py` all passed. Independent routing review 27 and the objective review found Critical 0 / Major 0. All 104,241 critical-reference samples were preserved, with no old pad-group splits. Existing minor return-path tradeoffs remain in the review archive. Regression evidence: 18 fabrication, 15 procurement, 17 R6 geometry and 42 narrow firmware host tests passed.

Board size is **46 × 100 mm**: the 110 mm maximum passes, but the 80–90 mm target is not met. Five supports, including the mid-span support, pass the CAD envelope check. J9's mated envelope has only 0.03 mm residual margin after the modeled tolerance; confirm the real harness and airframe fit.

Fabrication outputs are regenerated in `m3_design/assembly_review/fab/`, with a matching source/output manifest. Gerber ZIP: 11 layers, PTH/NPTH drills and job file. All 222 CPL rows pass; 214 use independent supplier pad matching and 8 use placement-only validation. Top/bottom native renders and assembly PDFs were inspected.

The five-board Standard-PCBA cost check is **$84.14/board, 48 extended codes**. This is components plus feeder fees, not an all-in delivered-board price. Fixed two-sided assembly fees are $83.96/order; possible handling is $14.93/order; PCB fabrication, rails, joints and shipping are excluded. Supplier snapshot: 2026-10-13T19:17:09.804712+00:00. The smaller buzzer has stock 91,636. **Procurement remains on hold: U4 LSM6DSV320XTR / C26633007 has stock 0 for 5 required.** `check_procurement.py --cost-only` passes; the full procurement gate correctly fails on stock.

Power-copper calculations at 7.7 A, 35 µm copper, 20 µm via plating and 20 °C converged:

| Path | Resistance | Drop | Copper loss |
|---|---:|---:|---:|
| RAW_ACT | 3.96 mΩ | 30.5 mV | 0.235 W |
| BAT_IN | 3.91 mΩ | 30.1 mV | 0.232 W |
| ACT_FET_S | 1.36 mΩ | 10.5 mV | 0.081 W |

These calculations exclude component/contact resistance and do not establish thermal or flight qualification. GPS maximum current is unpublished; bench validation still covers combined radio/GPS startup and transmit load, supply overshoot, reset/off behavior, harness fit and ESD. Existing GNSS firmware still uses USART6 PC6/PC7 and must migrate to USART1 PA9/PA10 for R6; broader flight firmware was not qualified.

Pinouts (RX/TX at the module): J9 = 1:5V, 2:GND, 3:TX, 4:RX. J130 = 1:M0/PC8, 2:M1/PC9, 3:RX←PC6, 4:TX→PC7, 5:AUX/PA8, 6:port power, 7:GND. J131 = 1:port power, 2:GND, 3:TX→PA10, 4:RX←PA9. J2 TC2030 = 1:3V3 VTref, 2:SWDIO, 3:NRST, 4:SWCLK, 5:GND, 6:NC.

Evidence: `m3_design/assembly_review/sources/r6_final_validation.json`, `r6_final_checks/`, `r6_final_dc.json`, `r6_final_objectives_review.json` and `r6-independent-routing-reference-review-20261013.json`. CAD validation is complete; manufacturing procurement and physical qualification are not complete.
