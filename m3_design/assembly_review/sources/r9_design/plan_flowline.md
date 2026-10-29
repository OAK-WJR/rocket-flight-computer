# R9 Architecture A: the flow line

Read-only plan. The repository `rocket-flight-computer-r9` (R8, board `cc044ea0…`, commit `9c8179b`) was not touched.
Prototypes are scratch files under `…/scratchpad/r9_design/flowline/` (section 16).

Coordinates are KiCad mm as in R7/R8: x 0 is the west long edge, y 0 the aft (SMA) edge, and y grows forward.

How each figure was obtained is marked inline:
- **Proto**: measured on the scratch pyro-block prototype with kicad-cli DRC and the project's own `m3.kicad_dru`.
- **Model**: the topology survey's courtyard model rerun on this floorplan; nothing is routed.
- **Calc**: arithmetic.
- **Inference**: not measured (AGENTS §2.5).

---

## 0. Verdict

**The flow line works.** Its order along the board is: RF strip (aft) → strip mouth → U1 → sensor band → J122 →
pyro barrier → battery band → J1 (forward). It is the topology survey's A2 order, made concrete.

**Planned outline: 46 × 96 mm** (R8: 118). An attempt at 92 mm is gated on the step-4 placement spike.

**The pyro block was rebuilt from scratch and is DRC-clean (Proto).** It is the mirrored, A2-handed block, with the
copper drawn in full. Measured against R8:

| Rule | R8 margin (mm) | Prototype margin (mm) |
|---|---:|---:|
| A | 0.001 | 0.30 |
| B | 0.17 | 0.27 |
| C | 0.077 | 0.24 |
| E | 0.30 | 0.80 |
| F | 0.20 | 0.63 |
| G | 0.000 | 0.70 |
| H | 0.025 | 0.22 |

- Rule D stays at the pour clearance, as R8's does by construction.
- The block's bounding box is 639 mm² (R8: 662).
- Only one foreign net comes within 3 mm of armed-live copper: 3V3, at D120's anode, by design (R8: six).
- The gate test via has a GND via 1.2 mm away, which removes allowlist entry A8.
- A seeded rule-H fault is caught. With rule H deleted, the same fault passes silently.

**Three findings change the plan:**
1. **The A2 "mirror" needs pad-renumbered terminal footprints.** The DB128L's pin order relative to its wire entry is
   fixed. The topology survey's mirrored model puts BUS forward / RAW aft on J124 at the east edge, which the
   standard footprint cannot do. A same-land, same-part variant can: the terminal's two clamps are identical. J122
   needs the same treatment.
2. **The east side between J122 and the board edge is the bottleneck.** The 7.7 A RAW feed, C121, the ARM sense lane
   and the tie hole all need that space. So C84 and the logic supply move to the west column, fed by a
   RAW_PROTECTED corridor outboard of J121.
3. **The battery corner does not fit beside J1 at 92 mm** (Model: Q121 is pushed aft). A battery band between the
   barrier and J1 holds it. That band is the +4 mm in 96 mm.

**Cost of this architecture:**
- More vias, because the board is denser. Model estimate: about +36 % against R8's equivalent.
- J122 fit margin 0.49 mm when the header is turned (R8: 0.71).
- The radio sits 48 mm from the pyro terminals (pass 1's rationale asked for 68).
- The IMU moves onto the roll axis, about 7 mm from the 7.7 A copper. Its lever arm drops from 13 mm to 0.

---

## 1. What "flow line" means here, and where it deviates

- **Signals flow forward:** antennas → modules → U1 → sensors → outputs (J122 servos, CH1 pyro).
- **Battery power flows aft:**
  - J1 → battery band (input protection, eFuse, actuator switch);
  - RAW_ACT up the east edge to J124.2 and J122;
  - RAW_PROTECTED up both edges to the regulated supplies.
- **They meet in planes, not at a block boundary.** No signal lane crosses the pyro bus bridge, and no power lane
  crosses the pyro block.

**Deviations from a pure flow line (each forced):**
- **The camera block (J9, U12/U13, U7/U8/L3) sits beside U1 on the east, not at the forward end.**
  - Its six MCU pins are on U1's east face: 31, 35, 37, 38, 41, 42.
  - The camera lead runs aft to the shroud.
  - It is fed by an east RAW_PROTECTED branch.
- **The logic supply (U11, U2/L1, C84) sits in the west column beside J122.**
  - C84 is 11.1 mm wide and fits no east position: the east side carries the RAW feed (finding 2).
  - USB_LIMITED from J3 is short there.
- **The sensors sit between U1 and J122**, as the flow line asks. This trades distance from the 7.7 A copper for an
  IMU on the roll axis (section 5).

---

## 2. Floorplan (46 × 96 mm)

![floorplan](flowline/floorplan_FL96.png)

*In the picture, aft is on the left and the west edge at the bottom. Model courtyards: solid fill is the top side,
dashed is the bottom. The red line is a schematic 7.7 A polyline; the real copper follows the east spine.*

| Band (y, mm) | Contents | Constraint that sets the depth |
|---|---|---|
| 0 – 22.0 | RF strip: J30/J31, both chains, U30/U31, limiter (B.Cu), feeds, MCU-end interface resistors; GND fence row at y_f = 22.0 | U30's forward pads (courtyard to 21.4); escape vias outside the paste |
| 22.0 – 27.6 | Strip mouth: interface lanes only | F10/D17: U1 courtyard ≥ 5 mm from every RF part (X9 kept at ≥ 5.94) |
| 27.6 – 45.0 | U1 (23, 36.3) rot 0, with U3/Y1/decoupling under it. West: J3, D4/U10, J2, LEDs. East: J9, U12/U13, camera supply (U7/U8/L3, bottom), radio east-face lanes | U1 courtyard 17.3 mm |
| 45.0 – 51.5 | Sensor band: U4 IMU (23, 47.0) B rot 0, U5 (17.4, 47.6) B, R168 (top, at pin 15), V-sense dividers, 3V3A filter, servo chain (R150–R153 top in the four lanes, pull-downs and D121 near pins 22–25); LS120 and J123 east | servo chain + IMU |
| 51.5 – 59.2 | J122 (23, 55.3) rot 180 (W→E variant), tie holes (15.6, 52.2) / (30.0, 52.2). West: C84 (8.75, 60.75), logic supply under it. East: RAW corridor into the RAW row, ARM/3V3/RAS lanes, RAS divider, C121 | J122 turned (7.7 mm) |
| 59.2 – 78.6 | Pyro barrier (prototype, section 7): J121 IGN (10.5, 73.0) west, J124 ARM (36.0, 73.0) east, core between, R134 forward | terminals 10.2 mm + core aft part |
| 78.6 – 84.8 | Battery band: Q120 (34.4, 82.4) r−90 B and Q121 (41.8, 82.4) r90 B facing, D8 / C80 / C96 / C89 / C95 / R166 / R167 at J1.1, U9 and passives, Q122 / R120–R123 / C120 | battery-live copper ≥ 2.5 mm from R134's pads; J1 pin tails |
| 84.8 – 96 | J1 (23, 88.4) rot 180, entry +y, 1.9 mm from the edge | J1 courtyard 11.3 mm |

**Supports:**
- M3 holes at (4, 4), (42, 4), (4, 49), (4, 92.4), (42, 92.4).
- The mid hole (4, 49) is in the middle third (32–64 mm).
- Model check: P2's clearances pass, and C84 (the heaviest part) sits next to the mid support.

**Fit (Model):**

| Part | R9 margin (mm) | R8 margin (mm) |
|---|---:|---:|
| J122 | 0.49 | 0.71 |
| J121 | 1.54 | — |
| J124 | 1.15 | 1.15 |
| C84 | 1.16 | 1.37 |
| C121 | 1.51 | — |
| J9 | 1.28 | 0.03 |
| J123 | 1.45 | — |
| J3 | 0.89 | 0.89 |

---

## 3. Placement and pin changes

| Item | Change | Why |
|---|---|---|
| U1 | (23, 36.3) rot 0 (R8: (23, 45)) | Strip mouth only 5.6 mm; R8 pin map H0 keeps 0 RF crossings |
| J121 IGN / J124 ARM | Swap edges (IGN west, ARM east) with **pad-renumbered variants** of `M3_DB128L_2P_BK`: same land and part (C430601), pads 1/2 exchanged. J124: BUS forward, RAW aft. J121: OUT aft, IGN forward. Legends follow. `check_actuators` stays byte-identical (J124.1 = BUS) | Contract pins 3 / 15 (west) and 33 / 34 (east) meet their nets in cyclic order. The fire bridge lies forward and the exits leave aft |
| J122 | Turned (rot 180, SIG row aft) with a W→E pad-renumbered variant (plug 1 west), tie holes on its long axis | Four straight servo lanes from U1.22–25 (west→east) with no crossing. Fit 0.49 (owner call: unturned costs about 2 mm) |
| U4 / U5 | Bottom, rot 0 (axis map unchanged), U4 on the roll axis | Lever arm 13 mm → 0 (1.0 g at 4000 dps instead of 6.6 g) |
| C84 + logic supply | West column, beside the mid support | East side full (section 8); f1 rises (Inference) |
| R168 | Top side beside pin 15 | The IMU takes the bottom under U1's forward face |
| Q120 / Q121 | Facing each other in the battery band: J1.1 → Q120 → Q121 → east spine, all in one line | P1-9 "one corner"; shortest 7.7 A path |
| Strip: C300, C301, FB30, R305, R307 | B.Cu under U30's forward row (vias just beyond the pad ends, outside the paste) | Strip depth; decoupling nearer the VCC pins than R7 |
| Strip: FB31 | Beside C310 / C311 / C312 (east of U31) | Strip depth |
| Strip: R306, R315, R310, R313 | Inside the strip at its mouth (y 21.25, R8's x order) | U1 can sit 5 mm behind them |
| Limiter (Q30–Q32, R300–R303, C304) | B.Cu west of the GNSS line's stitching row and under U30's west half. LNA_EN and VCC_RF keep R8's via spots (10.41 / 11.51, 8.3) but run **west**, not forward under U30 | Removes allowlist entries A2 / A3 (detour 2.06× / 2.37× → about 1.3×; Calc on pad positions) |
| **Pin moves** (status only; contract pins untouched) | LOGIC_SOURCE_ST → a free west-face GPIO (PC10 or PD0). BUZZ_DRV and PULLPIN → free east-face GPIOs (PE13 / PE14). Each with a DS12110 / AN2606 row, D5 / D6 checks, a new `pin_table.tsv` and binding note | U11 is west; LS120 and J123 are east (the west column holds C84) |
| **Optional:** C128 | 100 nF 0603 → 0805 (a JLC basic part) | Its own pads are a drain-to-GND solder-bridge pair at 0.65 mm. R4 accepted this class; 0805 widens it. Owner / BOM call |

No new extended part is needed: the variants are footprints only.

---

## 4. RF strip (re-optimised, qualification kept)

**Unchanged and congruent:**
- Both jacks, both chains (jack → ESD → bias tap → pi → module) and both modules stay where R7/R8 put them.
- The launch (R-4), the GCPW profile (R-5), the line length (R-6) and the module keep-outs (R-8) therefore carry over.
  The new rule-based checks prove this on every build, instead of hashing it.
- The chain is already near-minimal: 4.4 mm pad plus 3.7–4.1 mm of chain before the module courtyard.

**Compaction (Model, placement level):**
- The fence moves from y 23.3 to 22.0. The strip parts stay inside 21.4 mm (X3 no regression).
- The RF zone (X3g/X3h), which includes the MCU-end resistors, shrinks from 30.5 mm / 1185 mm² to about 22 mm.
- Interface track (X3f) is estimated at about 240 mm (R8: 321; stretch ≤ 250).
- With U1 5.6 mm closer, radio / GNSS lanes shrink from about 141 / 80 mm to about 95 / 65 mm (topology figures).

**Limiter:**
- R8's two allowlisted detours exist only because the limiter parts sit forward of their vias under U30.
- Putting the limiter on B.Cu west and aft of the via spots makes both leads run straight. The vias stay 0.15 mm
  clear of the paste aperture (R8 D87).
- This keeps "B.Cu under / beside U30". F10's sentence "sits on B.Cu under U30" needs a text update (owner).

**Coexistence (R-11):**
- Radio MCU-end resistors stay at x ≥ 22.1: ≥ 6 mm from U30's body box for SPI.
- GNSS feed under U30, radio feed east of U31.
- RF line to RF line 15.45 mm, unchanged.

**Separations:**
- RF parts to switchers 8.0 mm (C310–U8; R8 10.7).
- RF parts to U1 5.94 mm (no regression, by U1's y).
- Crystal under U1, more than 14 mm away.

**What still has to be done:**
- Rebuild the GCPW field solver as a tool. It is not in the repo; the method is in pass2_rf §7.
- Confirm the B.Cu decoupling under U30: via inductance about 0.5 nH, Inference.
- Re-run the return-loss cascade on the unchanged chains (formality).
- Redraw the fence on the new y_f.
- Prove R-7 stitching ≤ 2.5 mm, removing R7's 4.0 / 2.7 ceilings. The B.Cu limiter frees via spots west of the GNSS
  line.

---

## 5. MCU and sensors

**U1 at rotation 0** keeps the cyclic order:
- RF on the aft face (51–75) and the aft part of the east face (39, 45–47);
- pyro / servo on the forward face (3, 15, 22–25);
- arm / RAW sense on the east face (33, 34);
- IMU SPI / baro I2C on the forward half of the west face (89–98).

**Under U1:**
- The flash (U3) and crystal (Y1) stay as R8's spike (a), translated.
- Y1's In2 keep-out becomes In2 GND (In2 there is no longer 3V3). The HSE lines then keep a reference, which
  attacks R6b (R8: 26 % of its unreferenced samples).

**IMU (U4):**
- Bottom, rot 0, at (23, 47.0) on the roll axis. Z3 = 0 (R8: 13.0).
- No vias or fill under it on B.Cu. Rule areas are derived from the footprint.
- The pyro / servo lanes pass above it on F.Cu, with In1 GND between.
- **Trade:** the 7.7 A copper (J122's RAW row) is about 7 mm away (R8: 16.3). Ground and magnetic coupling are not
  an issue (In1 between, no magnetometer). The thermal effect is a few °C during a stall (Inference).
- **Open risk (vibration):** the IMU sits mid-plate, possibly near the mode-1 antinode.
  - The step-4 plate model (`step9/plate_model.py`) decides between (23, 47) and a spot by the mid support,
    (10, 49), which has a 13 mm lever arm like R8.
  - Recorded either way; bench sign check.

**Baro (U5):** bottom at (17.4, 47.6). I2C is 4–6 mm from pins 95 / 96.

---

## 6. J122 and the servo chain

- The SIG row faces U1.
- The W→E variant gives four parallel lanes. Each runs: pin 22–25 → 10 kΩ pull-down + SRV05-4 tap → 1 kΩ 0805 →
  SIG pad. No crossing and no via. R8 needed vias for a six-crossing reversal.
- GND row forward: the servo return goes straight to J1.2 through the planes, 31 mm (Model).
- RAW row fed from the east end by the B.Cu + In2 corridor.
- **Tie:** holes (15.6, 52.2) and (30.0, 52.2) are derived from J122 (M-3). The tie crosses all four plug housings.
  The under-board channel (y 50.2–54.2) is clear of bottom parts (Model).

---

## 7. Pyro block: the prototype

**Build:** `flowline/pyro_proto.py` and `pyro_copper.py`, built on the R8 copy with all R8 copper removed and 46 × 92
outline geometry. The block coordinates are the same at 96 mm, because the block is referenced to the terminals.

**Checks:** DRC with the project `m3.kicad_dru` gives 0 errors; the only unconnected items are the MCU-side ends and
the RAS divider, which are not modelled.

### 7.1 Geometry (all F.Cu unless noted)

**Fire loop (one F.Cu loop that never leaves the block):**
- RAW_ACT → J124.2 (aft) → link → J124.1 BUS (forward).
- BUS run 1.0 mm along y 75.54 → R134 (23.0, 76.4) rot 0 → IGN run 1.0 mm.
- J121.2 IGN (forward) → igniter → J121.1 OUT (aft).
- OUT run 1.0 mm into Q124's drain. Q124 is at (19.0, 70.0) rot 180, with source / gate pins aft and the gate pin
  westmost.
- Copper resistance 15 mΩ (Calc), 5 % of F7's 0.3 Ω allowance. Adiabatic width as MARGIN P1-9.

**Gate network:** one straight GATE column at x 18.025: Q124.4 → R128 (10 k) → C126 (220 n) → R126 (220 Ω).
- GATE_N leaves at R126.1, with R127 (1 k) beside it.
- TP122 on the bottom at (20.9, 63.2), joined by a via at (19.3, 64.55). Its GND partner is 1.2 mm away, so
  AGENTS §3 holds and A8 is removed.
- PYRO1_GATE copper: 5.3 mm on F.Cu plus 2.6 mm on B.Cu to TP122.

**Continuity divider:**
- R173 taps OUT at the drain's east tab.
- CONT spine x 23.6: R129 (MID→CONT), R130 / R178 (2 k each), C127.
- Cold pull-up: R131 off R173's OUT pad; D120 (25.75, 72.15) rot 180.
- 3V3 enters D120 by a lane west of the ARM spine.

**Arm divider:** spine x 28.6, between R134's BUS pad and J124: R132 (BUS→MID), R175 (MID→ARM), R133 / R180, C129.

**Exits (west→east, crossing nothing):**
- GATE_N and CONT go aft-west past J122's west end (in the build, x 12.45 / 13.45 west of the tie hole, with a GND
  guard between).
- ARM1_SENSE goes aft-east past the RAW corridor on F.Cu: the corridor is on B.Cu + In2 there. This is the block's
  only plan-view crossing of RAW, with In1 GND between.
- Estimated exit length about 85 mm (R8: 137.5; stretch ≤ 80).

**RAW spine:** outboard of J124.1 by rule E:
- F.Cu / B.Cu from x 38.3 (7.2 mm wide);
- In2 from x 39.15 for D18's 2.5 mm (6.35 mm wide).

### 7.2 Measured on the prototype (Proto)

**Rule margins.** Every rule's minimum was raised in a scratch DRU copy, and DRC reported each pair's actual gap
under its governing rule. Margin = closest − minimum.

| Rule | Min | Closest pair | Margin | R8 |
|---|---:|---|---:|---:|
| A RAW_ACT to control | 0.5 | ARM1_SENSE lane – RAW F.Cu pour, 0.80 | **0.30** | 0.001 |
| B bus / IGN / drain to gate | 0.5 | GATE track leaving Q124.4 – drain pad, 0.77 (pin-4 pad itself 0.52, own part) | **0.27** | 0.17 |
| C bus / IGN / drain to sense | 0.3 | R173.2 MID – R131.1 OUT, 0.54 | **0.24** | 0.077 |
| D GND to bus / IGN / drain | 0.5 | drain pad – F.Cu GND pour, 0.5004 | 0.0004 (pour at rule, as R8) | 0.001 |
| E ARM break | 1.0 | BUS run end – RAW pour, 1.80 | **0.80** | 0.30 |
| F bus / IGN / drain to live | 0.5 | R134.2 – D120 NC pad, 1.125 | **0.63** | 0.20 |
| G gate nets in block | 0.3 | GATE_N – CONT lanes, 1.00 | **0.70** | 0.000 |
| H pad bridge | 1.0 | R129.2 CONT – R173.1 OUT, 1.216 | **0.22** (stretch ≥ 0.2 met) | 0.025 |
| A2 RAW to RAW_ACT_SENSE | 0.3 | 3.35 | 3.05 | — |

**Rule-H liveness (P-4 method):**
- R129 was moved 0.27 mm toward R173, which puts the pair at 0.946 mm. DRC flags it under rule H.
- With rule H deleted from the DRU, the same fault passes. So `PYRO_RULE_SHA` plus the seeded suite must stay in the
  gate.

**Bridge table (P-5).** All 17 exposed pad pairs under 1.0 mm between different parts are in tolerated or fail-safe
classes:

| Class | Pairs |
|---|---|
| Midpoint vs its own sense node (R4 pass 11) | R129.2 / R173.2, 0.44 mm |
| COLD vs its own midpoint (R4) | D120.1 / R129.1, 0.70 mm |
| Sense to GND (reads no continuity / disarmed; cold test) | 11 pairs, 0.49–0.97 mm |
| Gate to GND (holds the FET off) | 4 pairs, 0.71–0.97 mm |

- No live-to-sense, live-to-gate, 3V3-to-sense, or bus-to-anything pair under 1.0 mm.
- First drafts had two such pairs: 3V3 – ARM1_SENSE at 0.58 mm and the drain – C128 GND at 0.83 mm. Both were removed
  by moving D120 and C128. This shows the table catches real layout problems.
- 27 more pairs at 1.0–1.5 mm are listed in `proto/bridge.txt`.

**Gate neighbours (P-7).**
- GATE / GATE_N copper within 3 mm: only PYRO1_CONT, 1.0 mm edge gap (R8: ARM1_SENSE 0.22, CONT 0.30), plus Q124's
  own drain.
- Calc: a hard GATE_N–CONT short with the MCU in reset and the board armed puts 0.38 V on the gate. The source is the
  0.75 V CONT node through 0.91 kΩ, against R127's 1 kΩ, through 220 Ω / 10 kΩ.
- **Plan:** a GND guard track between the two exit lanes. GATE_N's only non-GND neighbours then disappear.

**Armed-live neighbours (X2).**
- One foreign net within 3 mm: 3V3, D120.3 at 1.865 mm, by design (R8: six).
- Plus D120's no-connect pad.
- Battery-live copper to bus / IGN / drain is ≥ 2.5 mm by construction of the battery band (X2d; R8: 1.089).

**Block size.** Bounding box 639 mm² (R8: 662; stretch 500 not met). Courtyard fill 0.54. The terminals' 36.6 mm span
sets the box.

**Coat region (P-10):**
- The CH1 hull + 1 mm is ≥ 9 mm from U4 and contains no U5, J122, U30/U31 or other test pad.
- J122's GND row ends 1.0–2.2 mm aft of the boundary, depending on where R126 / R127 finally sit. The build moves the
  gate column 0.6 mm forward to keep ≥ 2 mm.

### 7.3 Contracts that replace the rigid hashes

- **Adopted:** the survey's P-1 to P-11, with one refinement. **P-3's hull is the CH1 copper and pad hull + 1 mm, not
  the courtyard hull.** Then the outboard RAW spine under J124's plastic body is J124's own feed, and the RAW_PROTECTED
  corridor outboard of J121 lies ≥ 5.8 mm from its pads. The rule is still stricter than R8, which had no purity rule
  at all.
- **P-7 as GND-only neighbours:** the guard track.
- **New gates:**
  - the bridge-table script (P-5);
  - the seeded-fault suite (P-4);
  - the DRC margin probe as a record, with R8's margins as no-regression floors (Z1).

---

## 8. Power: battery band, 7.7 A spine, regulated supplies

**7.7 A path:**
- J1.1 (30.62, 88.4) → BAT_IN copper (4 mm, F + B + In2) → Q120 (BAT_IN pins west) → facing ACT_FET_S bridge (as R8,
  pad-limited) → Q121 → RAW pins east, straight into the east spine.
- The spine runs aft at x 38.3–45.5 (In2 from 39.15), past J124.1, to J124.2 and C121 (39.35, 62.54) rot 90.
- It then enters the B.Cu + In2 corridor (x 27.75–33, y 54–59.4), the RAW row's east end, and the row strip
  (2.9 mm × 3 layers).
- Estimate: about 1.0 mΩ for Q121 → J122 (R8: 1.45; Calc: 31 mm at about 6.5 mm × 2.5 effective layers).
- Necks: spine 7.2 / 7.2 / 6.35 mm; corridor 5.35 mm × 2 layers.
- **Not solved yet.** `tools/run_dc.sh` gates it in the build (0.1 mm grid), and the 0.05 mm solve is the record.

**Servo return:** J122's GND row → In1 and the outer pours → J1.2. It crosses under the pyro block in In1 only.
- Calc: a few mV of offset against a 0.4 V threshold.

**RAW_PROTECTED:**
- U9 (TPS25947) sits in the battery band beside J1.1, with the input protection at J1 (F9 premise; U9 is closer to J1
  than R8's 27 mm).
- **West branch:** along the J1 band, then up the west edge at x 0.8–3.4, outboard of J121 (≥ 5.8 mm from its pads,
  outside the block hull), to U11 / U2 under C84.
- **East branch:** on B.Cu outboard of the RAW pour (x 44.8–45.3), to U7, the camera eFuse.
- BAT_FAULT_N runs up the east edge to pin 28. BAT_ENABLE crosses under J1 from J1.4's 470 kΩ.
- **Not ideal:** two long corridors instead of R8's one. Each is ≥ 7 mm from armed-live copper and crosses no lane
  (Calc: 54 mΩ at 1 A for 55 mm × 0.5 mm, fine for a buck input).

**Supplies:**
- U2 / L1 (3V3 buck) under C84's west half, ≥ 4 mm from the GATE_N / CONT lanes, with In1 between.
- 3V3 reaches U1, the strip feeds and D120 through an In2 3V3 region covering the west and aft parts.
- U8 / L3 (camera buck) east of U1, at y ≥ 26.

---

## 9. Layer plan

**F.Cu (signals and fire loop):**
- RF lines and launch (unchanged), U1 escapes, interface lanes, pyro block and exits, servo lanes.
- GND pour elsewhere, plus the RAW pour east of the ARM lane.

**In1:** solid GND (D20; no track). Antipads only for vias.
- Slots allowed only at J3's legs and the TC2030 pins (P3b ≤ 2 as stretch).

**In2 (power, no signal track):**
- 3V3 region: west column and U1 band, west and aft of the block.
- RAW_ACT region: east spine and the J122 corridor; ≥ 2.5 mm from BUS / IGN / OUT copper (D18).
- GND everywhere else, explicitly under the CH1 hull (P-3), under U31 (EBYTE §4.1), under the launch cut-outs and
  under Y1.
- Target 3 regions and P6 ≤ 900 mm (R8: 5 regions, 1752 mm).

**B.Cu:** limiter and GNSS feed under U30, IMU / baro and their SPI / I2C, flash / crystal / decoupling under U1,
battery band FETs, logic and camera supplies.
- The RAW corridor. The ARM lane does not use B.Cu where it crosses RAW.
- GND pour with stitching.

**Widths:**

| Use | Width (mm) |
|---|---|
| Signal | 0.2 (0.15 only at U1 fine-pitch escapes) |
| RF | 0.30 (DRU) |
| Power | 0.3 / 0.5 / 1.0 |
| Wide power | zones only |

- That gives X5 at 6 (signal 2, power 3, RF 1), against a target of ≤ 8.
- Vias: 0.5/0.3 signal, 0.6/0.3 power (X5e 2).
- **Pour trims (X8): 0 by design.** Zone shapes come from the rule set, not patches.

---

## 10. What becomes simple, and what remains

**Simple:**
- Pyro exits: three lanes, no crossing among the contract pins. Topology: 10 → 2 contract crossings; here 1 plan-view
  crossing, ARM over In2 RAW.
- Pyro block: never cut by a foreign lane (X2g 1, 3V3 to D120; R8: 6).
- RF interface lanes: 0 crossings on the H0 map, about 35 % shorter.
- Servo lanes: four parallel lanes, no vias.
- 7.7 A path: J1.1 → Q120 → Q121 → spine in a straight line.
- No rigid-copy exemptions: A2, A3, A8 and the S15 In2 link all disappear (C1 / C3 / C6 = 0).
- RAW_ACT_SENSE_MCU: R172 at pin 34, so R8's VLOGIC crossover disappears (S8 / S9 → 0 except TXEN).

**Remains (with reason):**
- **TXEN loop round U31:** maker pinout plus F10. Keep-out-forced, D10 baseline.
- **ARM1_SENSE over In2 RAW:** topologically forced in an A2-handed block with RAW passing outboard of J124.
- **Two RAW_PROTECTED corridors:** C84's width.
- **Density:** about +36 % estimated vias (Model 99.6 against R8's fitted 73).
  - S4 ≤ 55 is at risk.
  - Mitigations: the three status-pin moves, sensors and their buses on B.Cu, the IMU / baro / flash cluster
    escaping on B.Cu.
  - If S4 still misses, the measured cause is P1 length against priority 2, an owner-ranked trade.
- **J122 fit 0.49 < R8's 0.71:** the turned header.
- **Radio 48 mm from the pyro terminals:** short board; bench immunity test.
- **IMU 7 mm from the 7.7 A copper:** on the axis.

---

## 11. Expected metrics against the baseline scorecard

*All are estimates unless marked Proto.*

**Length and placement:**

| Row | R8 | Expected | Done / stretch |
|---|---:|---:|---|
| X1 length | 118 | **96** (92 gated) | done ✓, stretch ✓ |
| S17 placement MST | 1639 | 1595 (Model) | ✓ |
| S1 signal track | 1498 | 1300–1450 | ✓ likely |

**Routing:**

| Row | R8 | Expected | Done / stretch |
|---|---:|---:|---|
| S4 layer-change vias | 55 | 55–70 | **at risk** |
| S8 / S9 | 4 / 4 | 0–1 / 0–1 (TXEN only) | ✓ |
| S15 | 3.4 | 0 | hard ✓ |
| C1 / C3 / C6 | 3 / 3 / 1 | 0 / 0 / 0 | stretch ✓ |
| C2 info-only instances | 91 | 60–85 | likely ✓ |
| Deviations | 3 + 20 | 0 + about 5 | ✓ |

**Planes and reference:**

| Row | R8 | Expected | Done / stretch |
|---|---:|---:|---|
| P6 In2 perimeter | 1752 | 900–1200 | at risk |
| P7 | 1 | 0 | ✓ |
| P9 / P10 | 4.47 / 9.65 | ≤ 3.5 / ≤ 7 | likely: GND vias inside the block now (Proto: 10), battery band open |
| R6b | 0.111 | ≤ 0.08 | likely, with Y1 over In2 GND |

**7.7 A copper:**

| Row | R8 | Expected | Done / stretch |
|---|---:|---:|---|
| D_raw | 1.45 mΩ / 17.5 °C | about 1.0 mΩ / lower | ✓ (to solve) |
| D_bat | 0.45 mΩ / 14.5 °C | ≤ R8 | ✓ (to solve) |
| D_fet | 21.4 °C | about R8 | done; stretch ≤ 20 via field |

**Pyro block:**

| Row | R8 | Expected | Done / stretch |
|---|---:|---:|---|
| X2 / X2b | 6 / 7 | **1 / 1** (Proto) | done ✓ |
| X2c | 0.70 | 1.865 (Proto) | ✓ |
| X2d | 1.089 | ≥ 2.5 | ✓ |
| X2e | 662 | 639 (Proto) | done ✓ |
| X2g | 6 | 1 | ✓ |
| Z1 margins | see section 7 | all ≥ R8 (Proto), H 0.22, G 0.70 | stretch ✓ |
| Z2 exits | 137.5 | about 85 | done ✓, stretch about |
| Z4 | 1 | 0 | ✓ |
| Z5 | 1.027 | 1.90 (Proto) | ✓ |
| Z3 lever arm | 13 | 0 | stretch ✓ |

**RF and separations:**

| Row | R8 | Expected | Done / stretch |
|---|---:|---:|---|
| X3 / X3f | 21.4 / 321 | about 21.4 / about 240 | ✓ |
| X9 | 5.94 / 5.075 | ≥ 5.94 / ≥ 5.1 (by U1's y) | ✓ |
| X9c | 2.65 | ≥ 2.65 (In2 RAW at x ≥ 39.15) | ✓ |

**Texture and robustness:**

| Row | R8 | Expected | Done / stretch |
|---|---:|---:|---|
| X5 widths | 11 | 6 | ✓ |
| X8 trims | 8 | 0 | ✓ |
| Y1 close pairs | 27 | ≤ 10 | target |

**Fit and vibration:**

| Row | R8 | Expected | Done / stretch |
|---|---:|---:|---|
| F1 worst top | 0.028 | 0.49 (J122) | ✓ (per-part J122 regression recorded) |
| f1 | 209 Hz | ≥ 241 likely (L 96, C84 at the support; Inference) | plate model |

---

## 12. Requirements and safety rules at risk, and how each is protected

**AGENTS §2.1 ARM break:**
- Net membership is unchanged; `check_actuators` 1 is unchanged.
- The pad renumbering moves BUS / RAW physically, so the legends and the ORDERING / FMEA harness text follow.
- Rule E margin is 0.80.
- RAW passes J124.1 only outboard, under the terminal body, never under BUS copper on any layer.

**§2.4 gate defined off:** topology and values are unchanged. P-7 guard track. Reset-short table in the record.

**F8 rules A–H / A2, D85, D18, D19:**
- DRC on every build.
- Margins with R8 as the floor.
- Bridge table and seeded suite as gates.
- Battery band ≥ 2.5 mm by legaliser rule.
- In2 RAW ≥ 2.65 mm.
- D19: servo lanes ≥ 5 mm from GATE_N.

**F8 divider fault tolerance:** the circuit is unchanged.
- Layout preconditions hold: each half is a separate part, no single bridge shorts a whole top (Proto table), and
  R168 / R170 / R172 sit at the pins (P-8 ≤ 3 mm).

**F7 fire-loop budget:** 15 mΩ (Calc), re-solved on the final copper.

**F10:**
- Strip content rules: net-based, unchanged.
- Module keep-outs: derived from the footprints.
- 5 mm separations: U1's y.
- **Text edits for the owner:** strip coordinates and board size, the limiter's place, B.Cu decoupling under U30,
  the quoted stitching gaps.

**F9 hot-plug:** input protection at J1. Rerun `step9/hotplug_feed.py` for U9's new feed.

**P1:** 96 mm. **P2:** fit table (J122 0.49 recorded); supports and tie holes by rule (M-3); plate model gate
f1 ≥ 209 Hz, target 241.

**P3:**
- Coating region rule P-10.
- J122's 2 mm keep-off from the coat region is to be ensured in placement.
- IMU zone free of staking (LS120 and J123 moved east, away from U4).

**M1 / M3:** BOM unchanged (52 / 52 extended codes); variants are footprints in `kilib/rocket.pretty`.

**M2:** see section 10. The S4 risk is disclosed.

**Firmware / binding:**
- The three status-pin moves and the J122 / J121 / J124 numbering.
- IMU axis map unchanged (bottom, rot 0); lever arm now about 0.
- New binding note required, as for every placement change.

---

## 13. What must be requalified

**DC (F4 / D12):**
- Three `run_dc.sh --necks` solves at 0.05 mm (record) and 0.1 mm (build gate).
- GND return solve.
- Via barrel currents.

**Critical reference:** `reference_audit.py` on both net sets (R6b ≤ 0.08).

**Pyro (survey §9.4, all twelve):**
- DRC A–H with margins: Proto method `drc_probe.py`.
- Seeded rule-H suite (P-4).
- Bridge table (P-5): Proto method `pair_probe.py bridge` plus a consequence classifier.
- Divider preconditions.
- Coating and leakage distances: `step9/requalify.py bare` (Proto Z5 1.90).
- Gate-neighbour reset table: `pair_probe.py gate` (Proto).
- Exits: `requalify.py exits`.
- Purity and neighbours: `pyro_neighbours.py` (Proto X2 1).
- TP122: via partner 1.2 mm; bottom parts ≥ 2 mm from TP122.
- Terminal wire room: same x as R8's terminals, so 6.3 mm.
- Fire-loop solve.
- RF–pyro distance (R-13: 48 mm, owner).

**RF (survey §8.4):**
- Field solver rebuilt.
- Launch congruence (R-4, by jack frame).
- GCPW profile (R-5).
- Cascade.
- Stitching ≤ 2.5 mm (R-7).
- Keep-outs (R-8).
- Chain order (R-9).
- Separations (R-10 / R-11).
- Supply: C300 / C301 under U30 by vias; GNSS VCC ≤ 0.2 Ω by DC solve.
- Limiter thermal: Q30 copper on B.Cu.
- Jack mechanics: unchanged jack x positions.
- Records.

**Fit and mechanics:** `fit_check` with derived RETENTION_HOLES; plate model; sled hole list; tab windows (keep tabs
off the west edge at y 68–78 and off the corridors); staking surfaces.

**Bench assumptions (unchanged tests, new coordinates):**
- Static / leakage / dynamic pyro gates, cold plug-out test.
- RF immunity with the radio 48 mm away; S21 J30↔J31.
- Coexistence, antenna short.
- NRST ≥ 1 MΩ, hot-plug.
- Thermal stall test of the new spine.
- IMU sign check.

**Records:** REQUIREMENTS F10 / F8 / P1 / P2 / F4 / M2 text; AGENTS §1 rows; ORDERING §3–7 coordinates; parent
`docs/VEHICLE.md` stack row (96 mm, holes); `pin_table.tsv` and binding note.

---

## 14. Reproducible scripted build (`m3_design/r9_build.sh`)

**Basis:** R8's framework, minus every rigid group. Deterministic, with a fixed KIID seed per stage, and each stage
gated.

| Stage | New / reused | Content |
|---|---|---|
| r9_sch.py | adapted from r8_sch.py | the three status-pin moves (pin_table.tsv), footprint fields for the J121 / J124 / J122 variants, optional C128 0805; netlist regenerated |
| kilib | new footprints | `M3_DB128L_2P_BK_R` (pads 1 / 2 exchanged), `HDR_3x4_SERVO_W2E` (plug 1 west when the SIG row faces aft) |
| r9_pcb.py + r9_place.tsv + r9_legalise.py | adapted from r8_pcb / r8_legalise | Starts from R8's committed board for footprints and nets only. Every track, via and zone removed. Outline from the tsv header (L). Every one of the 249 parts placed from the table. The legaliser holds R9's rules: P2 supports, J122-derived tie holes and channel, pin tails, F10 5 mm, battery-live ≥ 2.5 mm from bus / IGN / drain copper, bottom parts ≥ 2 mm from TP122, IMU zone, coat region. Rule areas derived from footprints: U30 / U31 keep-outs, per-jack launch areas, PYRO_BLOCK by P-1, IMU / baro |
| r9_rf.py | new, from R7's strip copper turned into jack-frame templates | launch, GCPW lines, stitching and fence generated from jack and module positions (identical copper here), limiter leads, feeds under U30, interface resistors |
| r9_pyro.py | new, productionised from `flowline/pyro_copper.py` | the block's copper tables (pad-referenced endpoints), exits, guard track, TP122 via with partner |
| r9_power.py | adapted from r8_power.py | In2 map (3 regions), 7.7 A copper and via fields, RAW_PROTECTED corridors, logic and camera supplies |
| r9_route.py + r9_route_<family>.py | r8_route.py's Draw primitives and family pattern reused (explicit octilinear tables, budgets) | families qspi_hse, rf_if, servo, pyro_exits, usb_swd, imu_baro, camera, status, power_ctl, links |
| r9_ground.py / .tsv | adapted | stitching grid, fence on y_f, GND partners, guard-track stitching; no pour trims |
| run_dc.sh 0.1 mm | reused | D12 gate in the build |
| r9_post.py | adapted from r8_post | silkscreen from nothing, variant pin legends |
| tools/check.sh → check_r9.py | new, replaces check_r8's hashes | R-1 to R-13, P-1 to P-11 (P-3 copper hull), M-2 to M-7, D18 / D19 / D85, X2d ≥ 2.5; route_check profile r9 (empty allowlist target); check_actuators with 15b → P-1 (reviewed, re-pinned hash); fit_check with derived holes |
| new tools | new | `gcpw_solve.py` (2-D FV field solver, pass2_rf §7 method), `bridge_table.py` (P-5 classifier), `rule_h_seed.py` (P-4), `drc_margin_probe.py` (Z1 record) |
| r9_fab.sh | adapted | package, manifest, CPL orientation corrections (unchanged parts) |

The prototype scripts in `flowline/` already show the stages for the pyro block: pad-referenced copper tables, DRC
with the DRU, the margin probe and the pair probes.

---

## 15. Effort, gates and owner calls

**Effort:** about 15–20 focused sessions plus a review loop of at least two clean passes. Steps:

| Step | Content | Sessions |
|---|---|---:|
| 0 | contracts and tools: check_r9, field solver, bridge / seed scripts, scorecard rows | 2–3 |
| 1 | schematic, pin moves, variants | 0.5 |
| 2–3 | placement spike at 92 and 96, legaliser, plate model and IMU spot decision | 2 |
| 4 | RF strip copper and RF requalification | 1.5–2 |
| 5 | pyro block productionised and requalified | 1.5 |
| 6 | power, 7.7 A and DC | 1.5 |
| 7 | routing families | 3–4 |
| 8 | ground | 1 |
| 9 | silkscreen and fab | 0.5 |
| 10 | records and requalification evidence | 2 |

**Highest-risk items:** S4 / density; the battery band packing (decides 92 vs 96); the east-side congestion; the
plate model and IMU spot.

**Decision gates:**
- **G1 (after step 3):** 92 mm only if the placement spike routes the sensor band and the battery band with no gated
  exception and an S4 estimate ≤ 60. Otherwise 96.
- **G2 (after step 5):** the pyro block's Z1 margins are ≥ R8's and the bridge table has no new class. This already
  holds in the prototype.

**Owner calls:**
1. Length: 96 planned, or the 92 attempt.
2. Pad-renumbered variants for J121 / J124 / J122, or the equivalent `check_actuators` / netlist remap.
3. J122 turned (fit 0.49) or unturned (+2 mm, fit 0.71).
4. F10 text: strip boundary, limiter place, B.Cu decoupling under U30.
5. Strengthened pyro rules: P-1b, P-3 (copper-hull form), P-7 with the guard track.
6. Mid support west (4, 49), and the IMU on the axis or by the support (plate model).
7. RF–pyro 48 mm, against pass 1's 68 mm rationale.
8. The three status-pin moves (firmware binding).
9. Optional C128 0805.

---

## 16. Evidence (scratch, `…/scratchpad/r9_design/flowline/`)

- **Prototype builder:** `pyro_proto.py`, `pyro_copper.py`, `proto_lib.py`. Builds `proto/m3.kicad_pcb` from the
  baseline R8 copy with the project DRU and project file.
- **Margin and pair probes:** `drc_probe.py` (rule margins → `proto/probe_real.json`) and `pair_probe.py`:
  - `bridge` → `proto/bridge.txt`;
  - `gate` → `proto/gate_neighbours.txt`;
  - `live3` → `proto/armed_live_neighbours.txt`.
- **Floorplan model:** `topo/arrs_fl.py` and `topo/run_fl.py`, the topology survey's model with this floorplan,
  terminal-pad swaps and J122 numbering → `topo/out_FL.json`, `floorplan_FL96.png`.
- **R8 dump:** `dump_pads.py` → `r8_pads.json` (R8 pads, tracks, zones).
