# M1 logic review record — rev H

> Reference only: M1 was the power + actuator half of the abandoned two-board design (see `../../docs/HISTORY.md`). Its pyro, arming, servo and buzzer circuits still have to be merged into M3. The checking scripts named below (`fit.py`, `netcheck.py`, `check1.py`) belonged to the legacy build tree and are not in this repository; `m1.py` needs that tree's footprint library to run, so treat it as a readable netlist.

Board: 46 × 66 mm, 4 layers, 34 parts, 27 nets, 117/117 pads assigned.
DRC errors 0 / unconnected 0; electrical checks 25/25 passing (`check1.py`, re-runnable).

Three automatic gates, re-run on every change:

| Script | Catches | Why DRC cannot |
|---|---|---|
| `fit.py` | Part bodies colliding | Most easyeda2kicad footprints have no `F.CrtYd` layer, so KiCad's courtyard check never triggers |
| `netcheck.py` | Copper netlist ↔ schematic netlist | A pin rotation is electrically legal and DRC stays green |
| `check1.py` | Current / voltage / power / margin | DRC doesn't know Ohm's law |

---

## 1. Defects found and fixed this round (10)

### 1. J1's pins rotated by one position — **reversed-battery class**
The copper said `SW / BAT+ / GND / SW`, while J1's silkscreen value in the same file, the as-drawn netlist and the frozen design table all said `BAT+ / BAT- / SW / SW`.
Copied wrong when the single board was split into M1/M2. Wired per the silkscreen, battery positive would land on the switch terminal and negative on BAT+.
DRC can never see this — a rotated connector is electrically legal. Fixed, and turned into the permanent `netcheck.py` gate (83 nets, 0 mismatches).

### 2. ID0–ID3 all floating — M1 would report itself "absent"
The architecture document: `ID0–ID3 = GPIO jumpers (shorted to GND or left open, 0 parts), internal pull-ups on the M2 side, 0b1111 = absent`.
All four open → M2 reads `0b1111` → concludes the M1 bolted to it doesn't exist.
**M1 rev H = 0b0101** (ID0 open, ID1 low, ID2 open, ID3 low). Neither 0000 nor 1111: those are exactly the readings of the two gross faults — a solder bridge across the row reads 0000, a detached cable reads 1111. 0101 is Hamming distance 2 from both and contains both 1s and 0s, so any single stuck bit lands on an unassigned code rather than another module's identity.

### 3. Three test points buried under connector plastic — unprobeable
TP5/TP6/TP7 were at x = 8.5–9.0, while the DB128V body covers from the board edge to x = 10.2. Electrically fine, so it was a **silkscreen warning** that exposed it. All three moved right, with their copper pours extended.

### 4. Servo failsafe pull-downs sat in the signal path
With R40–R43 placed vertically, their ground ends landed between J10 and the series resistors, forcing the servo traces across a GND pad. **A shunt branch to ground must not block the main path**; changed to horizontal, tapped from the side. DRC had reported 4 shorts + 4 solder-mask bridges.

### 5. All four servo channels crossed over in reverse
With J10 rotated 180°, its pins counted right to left, the exact reverse of J5, so the four signals needed 8 vias on B.Cu to cross over — **exactly what makes a board impossible to check by eye**.
The footprint body actually sits on the +y side, so rot = 180 made the cable U-turn into the board: **the orientation was wrong anyway**. Changing to rot = 0 fixed both, without changing a word of the interface definition (ICD).

### 6. Five part-body collisions
C1 (470 µF can) hit the J4 terminal body, C1 sat on the Q1/Q2 footprints, and the J1 terminal body sat on Q1.
Root cause: `fit.py` **symmetrised** footprint outlines (taking `max(|min|, |max|)`). Switching to signed asymmetric outlines exposed 11 collisions at once.

### 7. FET_S copper had only 5.6 % margin
7.90 A vs the 7.48 A design current — the only piece of copper on the board carrying the entire load current. Widened 5.2 → 6.6 mm, margin now 26 %.

### 8. Igniter resistance not stated as a design constraint
The igniter is off-board, so its resistance is a **specification, not a measurement**. Nominal 0.7 Ω → 3.7 W (safe); a home-made 0.35 Ω low-resistance bridgewire → 22 A / 13.8 W → the SOT-23 junction rises about 346 °C in a 10 ms pulse.
Not a part-selection error but **an operating range that must be written down**. Now printed on the back next to J4: `E-MATCH >= 0.7 OHM`, plus `2S ONLY 8.4V MAX` (the TVS is the 12 V-standoff SMBJ12CA).

### 9. GND pour broken into an island
Between the Q4 gate network and the two MOSFETs, 12.5 mm² of ground copper had no via down to In1 — and R21 and C36 sat on it, **exactly the two parts that only work if their ground is solid**. DRC reported it as "zone unconnected to itself", which sounds like a fill glitch. Vias added, plus a self-check: every filled island must carry at least one via to a plane.

### 10. Two sources of silkscreen truth
The test-point coordinates in `silk1.py` were a hand copy of those in `m1.py`, and the copy didn't follow when the test points moved. **A label pointing at the wrong hole is worse than no label**, and no tool can see it. Changed to read directly from `m1.py`.

---

## 2. Independent recomputation, consistent with the frozen design

| Item | Document | Independent result |
|---|---|---|
| Gate divider 100k/10k | Vgs −7.64 V @ 8.4 V, −5.45 V @ 6.0 V | −7.636 / −5.455 V ✓ |
| Bridgewire test current | 0.764 mA, 327× below no-fire | 0.7636 mA, 327.4× ✓ |
| Continuity lower arm 1k rather than 3.3k | After a bridgewire opens the drain avalanches; 3.3k would put 8.93 V on a 4.0 V-limit ADC | 3.64 V at the 40 V worst case, inside the FT pin's 7.3 V ✓ |
| 10 nF anti-Miller | Without it ΔVgs 1.34 V, the FET partly turns on | 3.9 mV with / 55.6 mV without, against a 650 mV threshold ✓ |
| Pyro bus taken from RAW | Otherwise inserting the arming plug with the board off energises the pyros | J4.1 = RAW ✓ |
| Bidirectional TVS across BAT+/GND | A unidirectional part forward-biases on reversal = dead short across an unfused LiPo | On reversal Q1's body diode is reverse-biased and the TVS does not conduct at 8.4 V → **reversed = no power, not a burnt board** ✓ |

Power-up surge: 18.1 mJ all in Q2, a ramp of about 288 µs, 63 W average; DFN5×6 single-pulse Zth (0.3 ms) ≈ 0.3 °C/W → about 20 °C rise. **Passes, and the big 9 kΩ gate resistance is what makes it gentle.** *(Superseded by SPICE: see `../../docs/SIMULATION.md` §7.1 — Q2 actually takes about 8.1 mJ with a 138 W peak, and the ramp is 332–389 µs with the M2 capacitance included.)*

---

## 3. Remaining risks (not defects — they must go into the procedures)

**1. A pyro FET drain-source short = the charge fires the instant the board is armed.** The single point with the heaviest consequence on this board: if Q3 is shorted D-S, the bridgewire takes the full 8.4 V the moment the arming plug goes in.
Once armed, "bridgewire open" and "FET shorted" cannot be told apart — both read 0 — but **the operational decision is the same (do not launch)**, so it is a diagnostic ambiguity, not a safety hole.
**Removing it needs no hardware**: with the arming plug out, no igniter connected and the board powered, measure **TP6 → G** and **TP7 → G** with an ohmmeter. Normally open; near 0 means the FET is shorted. This step must come before connecting the igniters.

**2. No fuse.** The frozen design explicitly accepts it (it literally says "an unfused LiPo"). A short on RAW has no overcurrent protection. The dilemma of adding a fuse is real: a rating that stops a short will nuisance-blow with four servos stalled, and a nuisance blow is an in-flight failure. *(MARGIN_PRESCRIPTION.md P0-3 later made an in-line 15/20 A fuse mandatory.)*

**3. The SRV05-4 ESD clamp was on M2**, while the ESD entry point is the exposed J5 servo connector on M1, with a 220R series resistor and a cable in between. The series-R + clamp combination works, but the clamp was two boards away from the entry. Listed as an open M2 design item. *(Moot on a single board: place the clamp next to the servo header.)*

**4. The 3D models could not be trusted.** J11's footprint silkscreen body is 7.86 mm wide, but the model was drawn 11.9 mm wide and shifted about 5 mm left; J10 the same. The footprint silkscreen matches the JST PH datasheet. **It does not affect the Gerbers**, but any mechanical clearance judged in the 3D view does not count — real fit is verified with the connector coupon.

**5. J5 at 3 A per pin is exactly 100 % of rating.** The board's only hard constraint on servo choice: **servo stall ≤ 3 A**; four 2 A servos are 67 %, four 3 A servos exactly full rating. *(The chosen MKS HV6120 stalls at 1.916 A at 8.4 V, 63.9 %.)*
