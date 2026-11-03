# Round 23 safety review (Claude)

Target commit `c70d2614c9f187c46bce6225047ef4d03484848a`, PCB `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1`
(the same before and after this review). **0 Critical / 0 Major / 9 Minor** (8 new, 1 carried from R22-REQUIREMENTS-03).

This round walked the pad procedure and the flight step by step, as the operator does them and as the hardware sees
them. The board itself holds up:
- With J400 open, or with PC1 low, no single fault fires the e-match. Firing needs Q121 (the forward-blocking FET,
  because Q120's body diode conducts forward) and Q124 to conduct together, and every gate is held off by its own
  via-free network.
- The fire-current path has no single via.
- U9 cannot reach the pyro chain.

The findings are about the procedure and the firmware rules that are meant to cover the residual faults. Nine are
Minor. All their fixes are text only; one also names a respin item.

## Method

- **Geometry.** Native pcbnew (KiCad 10, read-only) and my own polygon code, with arcs at 1 µm.
  - Adjacency of 23 pyro, arming, switch and buzzer nets against every net, on all four layers: pads, tracks, via
    pads, barrels and fill pieces; 0.6 mm on the outer layers and 1.1 mm on the inner layers.
  - It reproduces the recorded 0.150 / 0.173 / 0.177 / 0.180 / 0.200 / 0.300 / 0.330 / 0.367 / 0.500 / 1.021 /
    1.050 / 1.061 mm figures.
- **Opens.** A per-net copper graph, with single via and track opens tested on 52 terminal pairs: the fire path, the
  gate drives and pull-downs, the J400 chain and U2's FB.
- **Gate.** kicad-cli 10.0.7 DRC with all severities and schematic parity: 0 / 0 / 0.
- **D-R22 pass.** The Gerber zip contents of `ec8cb98` and `c70d261` are identical apart from date and comment lines.
  The `tools/check_r10.py` diff was read for removed or weakened rules.
- **Calculations.** `.supervisor/r23_safety/calc/calcs.json`. The fire budget was re-solved from `parts_budget.json`;
  my solver reproduces its 1.5409 … 1.2787 A.
- **Maker data.**
  - TI SLVSFC9C pp4, 7–11, 30–31 and 37–38;
  - TI SLVSEA3F p18;
  - AOS AON7524 and AONR21357 p2;
  - Bourns CRM2512 p1;
  - the MJG J-Tek sheet.

## Step walk (single faults: fire / stop a required fire / board on with J400 open)

| Step | Fire | Stop a required fire | Board on with J400 open |
|---|---|---|---|
| 1 Pack in, J400 open | **Impossible: no match.** Hot-plug cannot turn the switch on: C120 1 µF holds VGS near 0; C123 holds Q122's gate to about 40 mV; C126 holds Q124's to about 2.5 mV. A reversed or 3S pack: U9 blocks, and Q120 / Q121 stay at VGS 0 | – | **Covered by check (1).** EN leak at U9.1–U9.5 (0.200 mm); U9 HFET or EN–IN short; back-feed; a short in the J400 pair |
| 2 Board-off checks, e-match in | **Covered by J121.2 < 0.1 V.** A live bus (Q121 short, ACT_GATE leak below about 270 kΩ, Q122 short). **Impossible:** with the bus off no single fault drives more than 0.75 mA through the match. A match put into J1 fires at once; only J121's black body and its legends guard against that | **Gap, -03:** a strand or a shorted match reads healthy | As step 1 |
| 3 Close airframe, carry, rail | Needs the board on plus a second fault | – | **Gap, -02:** a pinched J400 pair or a leak forming now |
| 4 J400 closed: power-up, passive screen | **Covered by the passive screen.** Pre-existing Q124, C128, OUT–GND and OUT–3V3 faults read out of band, so it refuses. **Gap, -08:** a QSPI_IO2–PE4 bridge shows only if QSPI is active. **Recorded:** I-5. **ESD:** -06 | EN stuck low: a dark board, no-go | ESD outcomes (-06) |
| 5 PC1 high, on-rail checks | **Recorded (row 1, lever row 18):** the bus-enabled class. **Gap, -01:** faults that conduct only at bus voltage are first exercised now | **Refused:** an open at the Q121 gate via (11.14,71.7). **Margin, -05:** an open at the Q120 gate via (16.2,73.3). **Blue Jay:** the Q124 gate chain | **Gap, -01:** three latches that need PC1 high |
| 6 Hold on the pad | **Recorded:** the bus-enabled class. **Ambiguous, -07:** an IMU fault faking lift-off. **Firmware rule:** the uplink. **Bench test:** RF | **Pad-energy worksheet:** pack drain. **-08:** an IGN–GND short loads R134 with 22–29 W | n/a |
| 7 Lift-off, burn, coast | **Recorded class:** premature fire (C128, Q124, OUT chafe) | **Covered by the chatter test and F-4:** J400 / J1 drop-outs. **-06:** EN damaged by ESD | n/a |
| 8 Apogee | – | **Measured:** no single via on the fire path. **Blue Jay:** single-string parts. **-05:** the body-diode case | n/a |
| 9 Descent, landing | **Gap, -04:** an unfired match stays on an enabled bus (landing shock on C128) | – | n/a |
| 10 Recovery, safing | **Gaps, -04 and -02:** the bus stays enabled, and USB re-arms | – | **Gap, -02:** latches, U9 failures and a failed-on switch have no stated action, and RAW_ACT cannot be checked in flight configuration |

## Findings

**R23-SAFETY-01 (Minor, new). The switch-off check never runs with the bus on.**
- **The three latch paths.** They are at BAT_ENABLE, and each holds EN with J400 open only while PC1 is high or the bus
  is enabled (Calculation):
  - R123.1 (ACT_EN), 0.330 mm: latches for a leak below 291 kΩ;
  - the ACT_EN_MCU run, 0.5205 mm, outside the 0.5 mm inventory: below 587 kΩ;
  - R134.2 (RAW_ACT), 0.5008 mm: below 1.69–1.96 MΩ.
- **Why the per-flight check misses them.** The closed-switch check comes before the e-match goes in. With no match
  the passive screen reads "open", so PC1 stays low and none of the three is energised. That is an Inference about the
  unwritten firmware, which may raise PC1 only after a valid passive check.
- **Bus voltage first seen with the match fitted.** Q124 and C128 get bus voltage for the first time each flight with
  the e-match fitted and the operator at the rail. The passive screen biases them at only about 1.08 V.
- **Fix (text).** Run the per-flight closed-switch check with a 1–2 Ω dummy load in J121, so that PC1 rises.
  1. Check the powered BUS / CONT readings.
  2. Open J400 and confirm within 1 s that the board is off and J121.2 is below 0.1 V.
  3. Then fit the match.

  Correct row 24's closure to match.

**R23-SAFETY-02 (Minor, new). Nothing is stated after the e-match is in.**
- **(a) No check while the vehicle is carried.** Nothing confirms the board stays off between fitting the match and
  closing J400. A pinched twisted J400 pair, or an EN leak, arms the vehicle while it is carried.
- **(b) J400 does not cut the bus feed.** The feed is BAT_IN, ahead of U9 (Q120.5–9). So a failed-on load switch,
  which the passive screen reports as "bus live", stays live with J400 open.
  - RAW_ACT cannot be checked in flight configuration: TP120 faces the sled and J121 is inside the bay.
  - No action is stated for a board or a bus that will not go dead.
- **(c) USB re-arms with J400 open.** USB powers the logic through U11 IN1 (TI: ST is high for IN1). At recovery, with
  the pack and an unfired match still connected, plugging USB can re-arm. Only the bench rule covers it.
- **Fix (text).**
  1. Confirm no telemetry and no buzzer before carrying, and again before closing J400; confirm a fresh power-up when
     J400 closes.
  2. State what to do when the board or the bus stays live.
  3. Recovery order: J400, then the match, then the pack, then USB.
  4. Firmware rule: PC1 high only while PA4 reads low and VBUS_SENSE agrees. R91.1 and U1.28 each hang on one via, so
     this is an extra barrier, not a guarantee.

**R23-SAFETY-03 (Minor, new). No per-flight igniter-resistance check.**
- **The fault.** A strand across J121, or a shorted match, reads healthy in the passive screen. The fire current then
  bypasses the bridgewire (R134 limits it to about 4.2 A).
- **The rule exists but was not carried.** The FMEA's R10 row says to retain the igniter-resistance check; ORDERING 8.3
  has no such step.
- **Fix (text).** After fitting the match, with J400 open, read J121.1–J121.2 with a test current below 40 mA. It must
  read the match (about 1–2 Ω), not 0 Ω and not open. Record the value. The board path in parallel is about 22 kΩ.

**R23-SAFETY-04 (Minor, new). No post-landing disarm.**
- **The gap.** The binding note and M3_R10 have no LANDED rule. FMEA I-8 / F-8 / 7.4′.9 are not carried, and row 18
  covers the pad only.
- **The consequence.** An unfired match stays on an enabled bus through landing and the crew's approach.
- **Fix (text).** LANDED sets PE4 and PC1 low, latched until power-off.

**R23-SAFETY-05 (Minor, new). Q120's gate hangs on one via, (16.2,73.3).**
- **The topology.** Q120.4 and Q121.4 meet only at R121.1 on F.Cu. The off-bias is local (D-R18-02), so an open is
  off-safe.
- **The failure.** With PC1 high, Q120 stays off and the bus runs through its body diode (VSD −0.7 V typical, −1 V
  maximum at 1 A; AONR21357 p2).
- **The fire current.** At four stalls it falls to 1.128 A (typical) or 1.063 A (maximum), against the 1.125 A floor; at
  three stalls, to 1.194 / 1.129 A.
- **Detection.** The idle bus reads about 0.4–0.55 V low (Inference). Only a powered-BUS band of about 4 % would catch
  it.
- **Fix.** Text now: a powered-BUS ≥ 0.96 × pack ground refusal. Respin: a second F.Cu–B.Cu via at Q120's gate. A
  direct B.Cu link to Q121.4 would have to cross the ACT_FET_S source bridge at y 71.1.

**R23-SAFETY-06 (Minor, carried R22-REQUIREMENTS-03). J400 ESD: fire-safe holds, but two outcomes are not covered.**
- **Fire-safe holds for every EN outcome I can derive:** latch-up, an EN–IN short, a pin stuck high or low, and
  leakage. Q120 / Q121 / Q124 share no part or single via with U9 or BAT_ENABLE. U2.1 has no single open, so U9
  cannot raise 3V3.
- **Not covered:**
  - **(a) J400 stops working.** It can no longer turn the board off after an EN–IN short, an EN stuck high, or a
    latch-up with the HFET on. The discharge happens at the arming touch, after the match is in.
  - **(b) Drop-out moves into the pack's working range.** EN leakage to GND raises U9's turn-off voltage: 2 µA gives
    6.49 V and 3 µA gives 7.43 V, against 4.71 V at TI's 0.1 µA (p9). The board then boots on a fresh pack but resets
    at two stalls or at the fire's own sag.
  - **(c) The 7.5 V is nominal.** At C87's low bound the same 8 kV / 150 pF discharge gives about 9.6 V.
- **Fix (text).** List these outcomes. After the first-article discharge, also measure the board's turn-on and
  turn-off pack voltages.

**R23-SAFETY-07 (Minor, new). The launch rule is ambiguous.**
- **The two readings.** AGENTS §2.1 and F8 say "accelerometer + barometer". F-6, cited for R10, latches lift-off on
  the accelerometer alone.
- **The single-IMU-fault path.** FLIGHT_PROVEN and F-11's V2 + V3 (after 60 % of the apogee time) can also come from
  U4 alone. So one "valid" IMU fault can walk the pad hold through every gate except the velocity lock (Inference).
- **The trade-off.** Requiring AND would let a blocked vent stop both deployments, because the Blue Jay shares the
  vent.
- **Fix (text).** State the rule and its trade-off, or record F-6's pad path with the gates that block it.

**R23-SAFETY-08 (Minor, new). Fire-route inventory.**
- **(a) QSPI_IO2 next to PE4.** QSPI_IO2 (U1.1, PE2) runs 0.5507 mm from U1.3's inner end under U1. It is also two pins
  from PE4, with the NC PE3 between: one three-pin solder bridge or one pad-to-track bridge joins them. With PE4 low
  against IO2 high the gate sits near 1.58 V, against AON7524 VGS(th) 0.4–1.2 V. With the bus on that fires during
  logging. The passive screen sees it only if QSPI is active then.
- **(b) OUT to 3V3, just past 0.5 mm.** Two pairs are bus-enabled fire routes left out of the 0.5 mm inventory:
  - OUT to 3V3, 0.5135 mm (R173.1 to D120.3);
  - OUT to 3V3A, 0.5662 mm.
- **(c) "GND holds the node off" is wrong for PYRO1_IGN.** With the bus on, an IGN–GND short loads R134 with 22–29 W
  (2 W rated) until it opens. Round 22 measured the same physics and closed it without a record change.
- **Fix (text).**
  1. Add a firmware aggressor test: run QSPI traffic and toggle PC14 and PWM during the passive screen, and refuse on
     any CONT / BUS movement.
  2. Add the pairs to the inventory.
  3. Correct the IGN wording.

**R23-SAFETY-09 (Minor, new; the U9 alternate analysis).** TPS259470A changes no AGENTS §2 property. But
`round22_alternates.md` gets two things wrong:
- **"The MCU reboots repeatedly into a persistent short".** A hard RAW_PROTECTED short keeps the logic off through every
  retry. Only an overload of about 0.8–2.1 Ω lets the logic run at all; below TSD that case behaves the same on both
  variants.
- **The in-flight retry is left out.** It recovers only through F-4's post-reset rules: the power loss clears the
  record, because VBAT is tied to VDD.
- **The bus lingers after a reset.** It stays on for 49–84 ms after a reset with PC1 high (C120 × 50 kΩ), so the
  cold-screen wait has to apply after every power-up.
- **Fix (text).** Correct §1.3, and reword binding-note obligation 9.

## Answers to the two questions

- **U9 alternate.** No AGENTS §2 property changes:
  - PC1 / PE4 stay off through each reset; no single-via open exists on R123 / C123 / R127 / R128 / C126.
  - J400 still disables the part (TI: it retries only "if it is still enabled").
  - A hard short keeps the logic dark.
  - The enable sequence cannot complete inside a TSD on-time.
  - An in-flight retry loses the lift-off latch, as any in-flight power loss does with 470L.
- **J400 ESD.** Fire-safe is true for every derived outcome. It is not safe in the J400-control and UVLO-shift senses
  (R23-SAFETY-06).

## Fix verification

| Item | Verdict | Measurement |
|---|---|---|
| D-R22 pass | confirmed | PCB hash unchanged; Gerber contents identical apart from dates; check changes additive (taps 26 → 33), S-1…S-9 untouched |
| R22-SAFETY-01 records | confirmed | §1 has the removed row, 0.300 mm, the 0.150 mm minimum and the R81 / C87 neighbours |
| R22-REQUIREMENTS-03 records | partly | Text present; the outcome list is incomplete (-06) |
| D-R22-02 | confirmed (R60.1) | Via (34.50,63.00) is R60.1's only link |
| D-R22-04 | confirmed | 0.3000 mm to U11.6; 2.032 / 2.063 V |
| D-R21-05 | confirmed | Via (17.10,82.80) plus three tracks; 0.1740 / 0.2242 / 0.2505 / 0.2536 mm |
| D-R21-04 | confirmed (geometry) | Hop segments present; 0.5008 mm to R134.2 |
| D-R21-01 | confirmed | J400.2 0.5505; J121.1 1.050 / 1.0613 mm; DRC 0 / 0 / 0 |
| D-R21-02 | confirmed | U2.1 → L1.2: no single open (the I-5 route through FB is closed) |
| D-R21-03 | confirmed | Q120.5–9 on BAT_IN; R134 limits only the igniter branch |
| D-R20-05 | confirmed | Ring-free J121.1 / J400.2 figures reproduce |
| D-R20-11 | confirmed | 10.6 ms at 6.0 V reproduced |
| D-R19-01/02/03/04, D-R18-02 | confirmed | 1.0210 mm; 0.5008 mm; no TP121 / J123 / J124; C123 present; local bias via-free |

## Fix now (all text or checks; no board change)

| Finding | Change |
|---|---|
| -01 | Per-flight closed-switch check with a dummy load in J121, bus on, then confirm the board turns off |
| -02 | Handling, abort and recovery steps; PC1 interlock on PA4 |
| -03 | J121 resistance reading after fitting the match |
| -04 | LANDED disarm rule |
| -05 | Powered-BUS ≥ 0.96 × pack refusal |
| -08 | Aggressor test during the passive screen; inventory and IGN wording |

-06, -07 and -09 are text corrections, to be made when those documents are next edited.

## Closed, not filed

- No single fault fires with J400 open or PC1 low.
- No single via on the fire-current path; none on any gate-control or pull-down path.
- Miller coupling at bus turn-on is negligible.
- No RAW_ACT, ACT_FET_S or BAT_IN copper within 0.6 mm of PYRO1_GATE / PYRO1_GATE_N.
- The BAT_SW_SOURCE barrels are on the source side of the switch: a fault there is fail-safe.
- An EN–OVLO bridge is fail-safe: OVLO trips at about 1.55 V.
- The bus-enabled class is not re-filed: it is owner row 1, with row 18 as the lever.

## Comparison with round 22 (opened after these findings were written)

Round 22's single finding (R22-SAFETY-01, inventory not carried) is fixed in the records. Round 22 also measured the
IGN–GND R134 overload (about 34 W) and a brief ESD U9-on, and closed both without filing. My -08 (c) and -06 go
further:
- **-08 (c):** the record wording.
- **-06:** the J400-control and UVLO-shift outcomes.

No other finding here appears in round 22's report.

## Limits

- No bench, firmware or physical test was run; R10 firmware does not exist.
- These are Inference:
  - ESD arc paths;
  - damaged-pin leakage values;
  - driver impedances.
- Adjacency is CAD copper only: no mask, coating or fabrication tolerance.
- The open search does not model partial or solder-joint opens.

Machine-readable twin: `round23_safety.json` (includes `step_walk`). Scripts and outputs: `.supervisor/r23_safety/`.
