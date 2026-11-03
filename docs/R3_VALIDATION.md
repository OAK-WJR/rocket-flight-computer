# M3-ASSY-R3 design validation (KiCad)

**Follow-up:** every finding below is answered in M3-ASSY-R4 ([M3_R4.md](M3_R4.md) §1–2), which also records a first-principles validation pass against [REQUIREMENTS.md](REQUIREMENTS.md).

**Scope:** the KiCad design only. That covers rule checks, the schematic, component ratings against the makers' datasheets, layout, manufacturability and fit.

**Not covered:** firmware, vehicle-level choices and anything physical. Nothing in the project was edited.

**Files reviewed:**
- `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `516f6a49…63d43f5`.
- `m3.kicad_sch`, SHA-256 `2606bd96…c4054e`.

**Method:** five parallel reviews covered power, MCU and digital, sensors and analog, the actuator band, and manufacturing and fit. Every finding marked Confirmed was re-checked against the board file and the maker's datasheet. Labels follow AGENTS.md rule 5:
- **Confirmed:** checked against the board file and a primary source.
- **Inference:** a calculation or assumption that was not measured.

## 1. Automated checks: all clean

- **Rule checks:** DRC 0, unconnected 0, schematic parity 0 and ERC 0. This holds with every severity and all exclusions included, and again after refilling every zone. No rule is set to ignore, and there are no exclusions.
- **Actuator checker:** `m3_design/check_actuators.py` passes.
- **Fab package:** `fab/m3_gerber.zip` matches a fresh export of this board, 16/16 files once timestamps are ignored.
- **BOM and placement file (CPL):** the BOM and the placement file match the board (180 parts). The placement file's rotations reproduce exactly from `tools/jlc_corrections.json`.

## 2. Fix before ordering

### A1. A switch bounce browns out the MCU (regression from the R2 merge)

- **Evidence:**
  - `BAT_ENABLE` connects only J1.4, R81 (280 k), TP84 and U9.1 (EN/UVLO); there is no capacitor.
  - The external switch is in series with the UVLO divider, which is R80 (1 M) from `BAT_IN`.
- **Why:**
  - The TPS25947 turns off 23–64 µs after EN/UVLO falls (SLVSFC9C, Switching Characteristics, t_D,OFF), with no deglitch.
  - Restarting takes t_D,ON plus the dVdt ramp: C81 = 4.7 nF gives about 0.43 V/ms typical, so 5–24 ms before the logic rail is back.
  - C84 (330 µF) holds VLOGIC for only a few milliseconds.
  - MARGIN_PRESCRIPTION P0-4 already identified 1–5 ms of reed/magnetic-switch bounce at 30 g as a vehicle-loss path and fixed it with a capacitor on the old FET gate. The R2 merge moved the switch onto U9's EN with no equivalent capacitor.
  - C120 (on `ACT_GATE`) now protects only the servo/pyro rail.
- **Fix:** add 2.2 µF (C23630, already on the BOM) from U9.1 to GND.
  - Ride-through becomes about 0.1 s at 6.0 V and 0.3 s at 8.4 V.
  - Power-on is delayed by 0.5–1.3 s.
  - It also filters short battery dips from servo stalls. At 6.0 V with all servos stalled, the input dips to about 5.15 V, against U9's 4.92–5.10 V turn-off (Inference).
- **Status:** the topology and timing are Confirmed (netlist, TI datasheet, design records). The exact hold-up time depends on the logic load (Inference).

### A2. The overvoltage lockout can hold the board off at full charge

- **Evidence:**
  - R82/R83 = 2 M / 300 k (×7.667).
  - Trip: V_OV(R) is 1.183–1.223 V, so the input trips at 9.07–9.38 V.
  - Restart: per §7.3.3 the output turns on again only once the OVLO pin is below V_OV(F), 1.076–1.116 V. That means an input of 8.25–8.56 V, with a further ±0.2 V from pin leakage. A full pack is 8.4 V.
- **Consequence:**
  - After any trip, U9 stays off until the pack drops below the restart point, and an unloaded pack doesn't sag.
  - Q122 drops the servo/pyro rail along with the logic rail.
  - Trip response is 1.2 µs, and the OVLO node is unfiltered.
- **Fix:** change R83 to 280 k (the same part as R81).
  - Trip becomes 9.63–9.96 V; restart becomes 8.76–9.09 V (at least 8.56 V with leakage).
  - It still trips on a 3S pack.
  - Optionally add 1 nF from OVLO to GND.
- **Status:** thresholds and behaviour are Confirmed (TPS25947 §6.5, §6.6, §7.3.3). How likely a trip is in service (for example, battery hot-plug ringing) is an Inference.

### A3. A terminal mix-up can fire an igniter with the ARM plug out

- **Evidence:**
  - J1, J9, J120 and J121 are the same part: C2915641, a green 4-pin 5.08 mm terminal.
  - J121 (igniters) and J9 (camera) are on the same long edge.
  - Every function label is on B.Silkscreen, which faces the sled: E1−/E1+/E2+/E2−, RAW/BUS2/BUS1/RAW, 5V OUT/GND/RX/TX, S/+/−, PULL/GND and BAT+/GND/SW/SW.
  - The top silkscreen carries only reference designators, and J120/J121 have no top pin-1 mark.
- **Consequence:**
  - If the igniter harness goes into J9, igniter 1 sits across `CAM_5V` (5.25 V, about 1.1–1.2 A limit). It fires as soon as the camera rail is enabled, and the ARM plug is not in that path.
  - Igniters wired into J120 sit on `RAW_ACT` all the time.
- **Already raised?** DESIGN_ASSURANCE (ARM-connector row, Tier-2 item 9) asked for a different pitch or colour; this was not implemented.
- **Fix:**
  - Put function and pin-1 labels on F.Silkscreen at every terminal, plus S/+/− at J122.
  - Use a different colour or pitch for J121 (and J120) than for J9 and J1. Dorabo lists colour variants; LCSC stock is unverified.
- **Status:** Confirmed (board file, BOM).

### A4. The IMU supply ramp is outside its power-on-reset spec

- **Evidence:**
  - U4's VDD and VDDIO are on 3V3A, which is 3V3 through L2.
  - 3V3 comes from U2 (AP63203, 4 ms internal soft start), so the 10–90 % ramp is about 3.2 ms.
- **Requirement:** TDK DS-000577 Rev 1.0 (AC characteristics) requires a monotonic 10–90 % supply ramp of 0.01–1 ms for a valid power-on reset.
- **Consequence:**
  - Every brown-out recovery repeats the slow ramp.
  - Nothing on the board can power-cycle U4 on its own.
- **Fix:**
  - Feed U4 from a small GPIO-enabled load switch whose rise time is within 0.01–1 ms.
  - Move R11 (the AP_CS pull-up) to the switched rail so it can't back-power U4.
  - This also lets the IMU be power-cycled.
- **Status:** the spec violation is Confirmed. Whether real parts actually fail to reset is unverified.

## 3. Should fix

### B1. USB unplug isn't detectable on PD15

- **Mechanism:**
  - Firmware enables the internal D+ pull-up (0.9–1.6 kΩ; DS12110 Rev 8, USB OTG_FS characteristics).
  - When the cable is unplugged, D+ keeps feeding VBUS through D4's I/O→VBUS diode. D4.5 is on the connector `VBUS` net, together with R9/R110 and U10.
  - VBUS settles at about 2.2–2.6 V, so PD15 sits at about 1.35–1.6 V.
- **Why it fails:**
  - That is between VIL max 1.22 V and VIH min 1.80 V (Table 60, at 3.3 V), so the unplug is never detected.
  - About 2.5 V also stays on the receptacle's VBUS pin.
- **Fix, either:**
  - Change R9/R110 from 6.2 k / 10 k to 3.9 k / 3.0 k. Back-fed PD15 is then at most about 1.1 V, and plugged 4.4 V gives 1.91 V. Margins are thin.
  - Or record the firmware rule "disconnect the pull-up before sampling PD15".
- **Status:** the topology and thresholds are Confirmed. Diode Vf at about 0.15 mA is an Inference.

### B2. The servo feed copper is below the project's own margin rule

- **Geometry:**
  - `RAW_ACT` runs from the load switch to J122 on F.Cu only.
  - First a 3.0 mm × 14 mm strip at y ≈ 35–38.
  - Then a 2.6 mm × 14 mm strip at y ≈ 70–73, narrowing to 2.36 mm where the ARM1_SENSE via cuts in.
  - No other layer carries `RAW_ACT` in parallel.
  - This settles the STATUS open item "2.6 mm feed neck".
- **IPC-2152 at 7.66 A continuous (4 × HV6120 stalled):**
  - about 45–50 °C rise without plane credit;
  - about 16–23 °C with the In1 plane underneath;
  - flight 1's single servo: about 3 °C.
- **Project rule:** MARGIN_PRESCRIPTION P1-9 asks for ≥ 10 mm equivalent, mirrored on another layer.
- **Fix:**
  - Add a ≥ 5 mm `RAW_ACT` strap on In2 under the top strip (In2 is empty there), stitched at both ends.
  - Move the ARM1_SENSE via and add a parallel strap for the bottom strip.
  - Or accept it formally with a stall-duty limit and a thermal-camera stall test at bring-up.
- **Status:** geometry Confirmed; temperatures are an Inference.

### B3. The IMU land pattern and the copper under the IMU break TDK's guidelines

- **Under the part:**
  - a GND via at the package centre (38.5, 168.5) and a BOOT0 via at its corner;
  - F.Cu GND pour under about 70 % of the body;
  - SPI1_SCK and BOOT0 running on B.Cu underneath.
- **Land and stencil:** lands are 0.675 × 0.28 mm, with mask = land and 100 % paste.
- **TDK guidance (AN-000393):**
  - land = pin size, 0.475 × 0.25 mm;
  - mask opening = land + 0.1 mm;
  - 90 % paste;
  - no traces, vias or filled copper under the part.
- **Already reviewed?** R2_VERIFICATION rated U4 "OK" without applying these rules.
- **Fix:**
  - Add an F.Cu keep-out under U4, move both vias out, and use TDK's land.
  - Likewise keep TE's reserved area between U5's pad rows clear (about 73 % is GND pour today).
- **Status:** Confirmed.

### B4. The zip-tie hole sits beside the pyro-1 gate network

- **Evidence:**
  - The servo-harness tie hole at (26.5, 68.2) is about 0.5 mm from the copper pour, from R126/R127 (pyro-1 gate series resistor and pull-down) and from the ARM1_SENSE track.
  - The part bodies are 0.2–0.4 mm from the hole edge.
  - DESIGN_ASSURANCE §5 item 4 requires ≥ 2.0 mm, and a cinched tie bears on those parts.
  - The second hole, at (24.0, 85.6), has copper 0.5–1.5 mm away.
- **Fix:** move the hole(s) or the parts.
- **Status:** Confirmed.

### B5. An exposed test pad sits 0.8 mm from the armed pyro-1 bus

- **Evidence:**
  - TP122 (`PYRO1_GATE`) is a bare 1.5 mm top-side pad at (26.6, 64.0), 0.8 mm from R134 pad 2 (`PYRO1_BUS`).
  - A solder ball or wire strand bridging the two would fire channel 1 when the ARM plug goes in.
  - By comparison, TP123 (channel 2) is 4.65 mm from R135.
- **Fix:** move TP122 at least 2–3 mm away, or delete it.
- **Status:** Confirmed.

### B6. Vias open into SMD pads

- **Evidence:**
  - C72.2 and C73.2 (U8 input caps, GND): the via centre sits on the pad edge, so half of each 0.3 mm hole is inside the pad opening.
  - D8.2: about 11 % of the hole is inside the opening.
  - R11.2: the hole is 0.04 mm from the opening.
  - Vias are tented only, so solder can wick into them.
- **Fix:** move these vias ≥ 0.25 mm off the pads, or order filled-and-capped vias.
- **Status:** Confirmed.

### B7. Two parts at the airframe wall

Both checks use GEOMETRY_REV_G's board-plane model: board flat and centred, top face 1.263 mm above the bore axis, 0.5 mm wall allowance.
- **J123 (pull-pin, x = 42):** a mated vertical 2.54 mm housing needs 16.75 mm of height. At its outer edge in the Ø54.6 bore only 16.31 mm is available, so it is 0.44 mm short.
- **C84 (Ø10 × 12.6 mm OSCON at 38.5, 27, inside the Ø50.8 coupler):** at maximum size it is 0.11 mm into the wall allowance, leaving 0.39 mm to the bare wall.
- **Fix:**
  - Move J123 inboard, or use a right-angle or soldered harness.
  - Move C84 at least 1.35 mm inboard, or fix the sled so the board top sits no more than 0.5 mm above the axis.
- **Status:** positions Confirmed; clearances are an Inference (they depend on the sled).

### B8. The 3V3A filter is under-damped and has no bypass position

- **Calculation:**
  - L2 is 4.7 µH with 60–78 mΩ DCR. C10/C11 are 24–31 µF effective after DC-bias derating; the R3 record assumed 45 µF.
  - That gives f0 ≈ 13–15 kHz and Q ≈ 4.4–6.2.
- **Effect:** 3V3 transients reach 3V3A about 1.8× larger. A ~40 mV dip on 3V3 becomes ~70 mV on 3V3A, above the IMU's 50 mV p-p supply-noise maximum.
- **Context:**
  - DESIGN_ASSURANCE §5 R2 asked for DNP pads across L2; they are not on R3.
  - The u-blox series-resistance limit that forced an LC filter instead of a resistor went away with the GNSS.
- **Fix:**
  - Add 1–2.2 Ω in series with L2, or replace L2 with 2.2–10 Ω (the load is a few mA).
  - At minimum, restore the DNP pads.
- **Status:** Inference (calculated with the real parts).

## 4. Minor

- **U9 power-pin layout:** U9's IN and OUT are fed by 0.3 mm stubs with no copper area or vias, and C80 is about 11 mm away (TI §8.4.1). Widen them, add copper and vias, and add 0.1–1 µF at IN.
- **Paste and lands:**
  - U9's IN/OUT bars print at 100 % against TI's 82 %, and U7's exposed pad at 100 % against 87 %.
  - The AON6403 paddle prints at 100 %, about 120 % of the package's exposed pad.
  - The generic AON6403 land leaves Q120.4 (gate) 0.32 mm from Q121.1 (source). A bridge there would disable the servo/pyro rail.
  - Fix: use the AOS PO-00044 land and window the paddle paste to about 60 %.
- **ADC inputs:**
  - V3V3_SENSE has a 5 kΩ source with no capacitor. That is outside ST's characterised source impedance at 10-bit and above (DS12110 Rev 8, Table 185).
  - The 10 nF filter caps for PB0, PC0, PC1, PC4 and PC5 sit 89–122 mm from the pins. Those traces run beside servo PWM, camera TX, buzzer and pyro-gate lines.
  - Fix: add 1–10 nF at the MCU pins.
- **Decoupling placement:**
  - C32 is 4.5 mm from U5's VDD pin and connects through two vias.
  - C30 and C31 reach U4 only through vias into In2.
  - VDDA/VREF+'s 1 µF (C22) is about 20 mm away; CIRCUIT_REVIEW assumed the values the other way round.
- **Split crossings:** B.Cu digital traces cross the 3V3/3V3A split on In2: SPI1_SCK, IMU_CS, QSPI_IO2, NRST, LED_YEL and USB_FAULT_N.
- **USB routing:** D+ reaches D4 through a ~3–4 mm stub instead of flowing through it, and the pair isn't routed as a 90 Ω pair. This is fine at 12 Mb/s, but PA12's ESD protection is weaker.
- **NRST:** C24 is 38 mm and 4 vias from U1 pin 14, and 13.8 mm of the trace runs 0.15 mm from QSPI_IO2.
- **Routing cleanup (AGENTS.md rule):** no electrical effect.
  - 0.1 mm grid-router jogs on QSPI_IO2 (16 jogs), QSPI_NCS, VLOGIC_SENSE, V3V3_SENSE, NRST and a few others.
  - One real staircase on PULLPIN at (25.5–26, 157.1–157.6).
  - A few 45° T-junctions, and a 22° hairpin on VBUS_SENSE.
  - 7 zero-length and 14 duplicate segments.
- **Silkscreen:**
  - U7–U11 and U13 have no pin-1 mark, and U7–U11 look identical rotated 180°.
  - 13 reference designators are hidden under J120, J121 or C121.
  - There is no IMU axis triad. With U4 as placed, roll (board +y) is IMU −Y; DESIGN_ASSURANCE and AUTOTEST_DESIGN say "gyro Z".
- **Courtyards:**
  - C121, D120, D122, D123, Q120–Q123 and LS120 have courtyards drawn around the body only, which defeats the courtyard-overlap check.
  - Because of that, two pad contacts went unnoticed: R123.2 touches C121.2 (tombstone risk for the 0402) and Q123.3 touches LS120.2.
- **Thermal relief:** the through-hole GND pins (J1, J9, J122, J123, J2 and the J3 shell) and J1.1's connection to the In2 BAT_IN plane have no thermal relief. Holes may not fill when JLC hand- or wave-solders them.
- **Washer areas:** signal tracks run inside the 3.5 mm washer radius of the four middle M3 holes. From the hole centre: CAM_5V 2.88 mm, PULLPIN 2.75, ARM2_SENSE 2.23, VBUS 3.3. Use nylon washers or reroute.
- **ORDERING.md gaps:**
  - It doesn't say that vias are tented, that this is an Economic assembly order, or that ENIG is mandatory (U11's 0.2 mm lands are below JLC's minimum SMD pad otherwise).
  - It doesn't address edge clearance and rails: J3 overhangs the edge by 1.0 mm and J1 is flush, and JLC's own pages conflict on rails and fiducials.
  - J3's shell legs have no paste although the BOM lists J3 as SMT; confirm that JLC solders them.
- **Stale schematic notes:** sheet 12 says "D120 + 47k", but R131/R143 are 10 k. Sheet 14 still calls PA5 TIM8_CH1N an inference.
- **Part status:** C45783 (Samsung CL21A226MAQNNNE, used at C6–C11, C150 and C151) is marked not recommended for new designs; the replacement is CL21A226MAYNNN. This is likely, from the maker's page.

## 5. Open items this pass settles or updates

- **STATUS "servo stall current vs the 2.6 mm feed neck":** it is a 14 mm run plus an unrecorded 3.0 mm strip; see B2.
- **M3_R3 P2 (PB0):** at the 15.4 V TVS clamp, R125 = 4.7 k gives 4.92 V, 3.3 k gives 3.82 V (passes the 4.0 V limit) and 3.0 k gives 3.55 V.
- **Pyro current:** the "4–10 A" design point predates R134/R135. A dead short now draws about 4.1 A, and a 1.2 Ω bridgewire gets 1.7–2.5 A (about 1.7 A at 6.0 V). Check igniter all-fire against those numbers.
- **HSE crystal (frozen-design open item):** gain margin is fine. gm_crit is 0.65–1.19 mA/V against the 1.5 mA/V limit, and the effective load is about 8.2–8.5 pF.

## 6. Hardware facts the firmware will have to respect (not reviewed)

- **IMU:** soft reset and a WHO_AM_I check at boot (see A4). AUX1 powers up enabled with pins 10 and 11 grounded, so disable it first.
- **USB:** if B1 is not fixed, disconnect the USB pull-up before sampling PD15.
- **Roll axis:** roll rate is −gyro_Y with U4 as placed.

## 7. Checked, no issue

- **Power:**
  - U9: turns on at 5.41–5.59 V and off at 4.92–5.10 V; current limit 1.80–2.20 A against a worst load of about 1.54 A; dVdt and latch behaviour as intended; reverse battery handled.
  - D8: standoff and clamp are within U9's absolute maximum.
  - U10: current limit 351–449 mA.
  - U11: thresholds, priority, current limit, soft start and pin map.
  - D9 and C84 ratings; U2's inductor, output caps, loop and feedback routing; U13.
  - U7: current limit 1.09–1.24 A, and dVdt.
  - U8: output 5.25 V; L3.
  - Q120/Q121: gate drive and inrush.
  - Battery-input copper and vias.
- **MCU and digital:**
  - Every power pin and its decoupling, VCAP and BOOT0.
  - Pin-mux re-checked independently: QUADSPI, SPI1, I2C1, TIM5, TIM8_CH1N, USART3, OTG_FS, SWD and the ADC channels.
  - HSE load and gain margin.
  - USB CC resistors, D4 pin mapping and VBUS capacitance.
  - QSPI pinout and skew; IMU SPI and barometer I2C.
  - TXU0202 camera UART; J2; the LEDs.
- **Sensors:**
  - U4 and U5 pinouts, straps and footprint pitch and pin 1.
  - Pin types and divider limits: everything is within limits except PB0 (section 5).
  - Back-feed with VDD = 0; sampling error on the 10 nF chains.
- **Actuators:**
  - Arming break: no bypass, and physical spacing ≥ 1 mm.
  - AON7524: current, SOA, gate drive and land.
  - Gate networks hold the FETs off in reset.
  - R134/R135 pulse rating: 1.9× margin at 20 ms.
  - Dividers and cold pull-ups.
  - J122 pinout: S/+/−, with V+ in the middle.
  - The 10 k pull-downs hold the servo lines low during reset.
  - D121, buzzer and pull-pin circuits.
  - Pyro and servo return currents stay below y ≈ 66, clear of the logic area.
- **Manufacturing and fit:**
  - Measured minimums are all within JLC's 4-layer limits.
  - The stackup in ORDERING matches the frozen design.
  - The U7, U9, U11 and U12 footprints match TI, and AON7524 matches AOS.
  - Heights clear for J120/J121, C121, the plugged J122 and J9.
  - Mounting holes; all 25 test pads are reachable.

## 8. Not covered

- Firmware.
- Vehicle-level choices: servo behaviour on signal loss, battery, igniters.
- Signal-integrity and thermal simulation.
- Anything physical.
