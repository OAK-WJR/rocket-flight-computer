# R9 Architecture C: the shortest board

Architect: compact (Architecture C). Input: R8 (`m3_design/assembly_review/m3.kicad_pcb` in the r9 worktree, branch
m3-assy-r9 at 9c8179b, SHA-256 `cc044ea0…`), read only, plus the three R9 surveys (`survey_constraints.md`,
`survey_topology.md`, `survey_baseline.md`). Scratch prototype, scripts and evidence:
`<scratch>/r9_design/compact/`.
The repository was never written (board hash and `git status` re-checked after the work; no `__pycache__` left).

Evidence classes used below: **Measured** = computed on the scratch prototype board by a script listed in section 16;
**Estimate** = scaled from the surveys' calibrated models; **Inference** = engineering judgement not yet checked
against a measurement or a maker document (AGENTS §2.5). The prototype is **placement only**: no tracks, pours, vias
or zones. Every copper-level figure is an estimate.

---

## 0. Verdict

1. **Design point 46 × 86 mm (R8: 118, A2: 92), fallback 46 × 88 mm.** Both are proved placement-legal on a scratch
   KiCad board with all 249 R8 parts. The checks are R8's own placement legaliser (`r8_legalise`): courtyards; pad
   clearances, including pyro rules A–H and rule H; R5 L10 bottom rules; M3 washer and standoff clearances; the J122 tie
   channel; F10's 5 mm separation; strip content. On top of that come two new rules that keep every RF part inside a
   22 mm strip, and a set of **stricter** pyro pad rules: rule H with a 0.2 mm margin, no bridge able to pull the
   actuator gate to GND, and gate pads at least 1.2 mm from sense pads and from always-live pads. `fit_check` passes,
   the five-support geometry included.
2. **The floor is about 85–86 mm.** Below that the battery corner (J1, the actuator switch, the input protection that
   F9's hot-plug premise ties to within about 10 mm of J1.1, and the eFuse network) collapses into the terminals' pin
   keep-outs. At 84 and 85 mm the same specification leaves 7 and 4 parts that the legaliser cannot place, all in that
   corner (Measured). Getting under 85 mm would take a requirement-level change: J1 overhanging the forward edge
   (about −2 mm, a DFM question for JLC), dropping test pads, or moving the input protection away from J1, which breaks
   the F9 premise. I do not recommend any of them.
3. **Topology:** A2's axial stack and handedness (topology survey), compacted in three ways:
   - **The whole RF zone moves into the strip.** The feeds, the interface resistors R306/R313/R315/R310, FB30 and FB31
     move inside a strip boundary at **y 22.0** (R8: strip boundary 23.5, RF zone 30.5). That lets U1 sit with its
     courtyard at y 26.85, 9.5 mm nearer the aft edge than R8.
   - **J122 is turned** (rotation 180, SIG row aft) directly ahead of U1, with its tie holes at its x ends.
   - **A 14.5 × 14 mm pyro interior** between J121 (IGN, west edge) and J124 (ARM, east edge). The R134 bridge sits on
     the terminals' aft pins on one straight line (y = YT − 2.54), with the gate network and the continuity divider
     forward of it and the arm divider aft. **J1 is shifted 4 mm east** so that J1.1 (BAT_IN) and the actuator switch
     (Q120/Q121, on the bottom under J124's outboard half) form one east battery corner on the 7.7 A spine.
4. **What compactness costs, stated plainly:**
   - **Routing density.** Top courtyard utilisation is 0.598 against R8's 0.413. The peak cut demand rises from 27 to
     30 lanes and the mean from 10.8 to 13.7 (Measured proxy). I estimate about 75–85 signal layer-change vias against
     R8's 55 (Estimate).
   - **Rows likely to miss.** Of the routing-simplicity "done" rows, S4 (vias), X6 (bends per mm), Y1 (close pairs) and
     probably S12 (critical layer changes) will miss. S17 (placement MST) is 1696 mm, 3 % above R8, before an MST
     optimisation pass.
   - **Robustness margins that shrink:**
     - J122's mated-plug fit margin falls from 0.71 to 0.50 mm. That is inherent to turning J122; keeping rotation 90
       costs 2 mm of length.
     - Support clearances fall from 4.45 / 5.01 mm to 3.85 / 3.82 mm (rules: 3.5 / 3.8).
     - The radio-to-pyro-terminal distance is 41.6 mm. Pass 1's rationale asked for 68; it is not a requirement.
     - Panel-tab windows are scarce: the east edge has none forward of y 14.
     - The CH1 bounding box (658 mm², within R8's 662) now overlaps the battery corner, so X2g (foreign tracks through
       the box) will miss.
   - **What C gains:**
     - The board is 32 mm shorter, which gives 32 mm more bay slack and roughly doubles the first plate mode
       (Inference).
     - The 7.7 A path drops from 61.5 to 43.1 mm, the servo lanes from 98 to 30 mm and the pyro exit lanes from 130 to
       80 mm.
     - The IMU lever arm drops from 13.0 to 5.4 mm.
     - Rule H margin rises from 0.025 to 0.224 mm.
     - The solder-bridge "fires" class has no pair under 1.5 mm. R8 has two, at 1.03 and 1.49 mm.
     - No rigid hash remains.
5. **Fallback chain:** 86 → 88 (already legal) → A2's 92. The build is parametric in length, so a fallback is a
   re-run, not a redesign.

---

## 1. Length budget (y bands, aft edge y = 0)

| Band | R8 (118) | A2 (92, survey) | **C (86, prototype)** | What sets it in C |
|---|---|---|---|---|
| RF strip / RF zone | 0–23.5 / 0–30.5 | 0–23.5 / ≈ 0–25.3 | **0–22.0 / 0–21.7** | U30's courtyard front at 21.4 (modules at R8's depth), fence row at ≈ 21.8. Every RF part (feeds, interface R, FB30/31) lies inside the strip |
| F10 5 mm band | 30.5–36.35 | 25.3–30.85 | **21.7–26.85** | Slow parts only: LS120, J123, the camera-I/O LDO U13 and its capacitors, U12-side resistors, test pads |
| U1 band | 36.35–53.65 | 30.85–48.15 | **26.85–44.15** | U1 at (23, 35.5) rot 0; J3/J2 on the west edge, J9 on the east edge; IMU, flash, crystal and decoupling under U1 |
| Servo chain | (beside J122) | 48.15–53.66 | **44.15–48.3** | R150–R153 (0805, top) on J122's SIG pitch; D121 and the pull-downs on the bottom |
| J122 band | 70.6–80.8 | 53.66–61.34 | **48.3–56.0** | J122 rot 180 at (23, 52.15), tie holes (16, 52.15) and (30, 52.15); C121 west, C84 east |
| Arm divider / exits | — | (61.3–68.3 gap) | **56.0–61.5** | R132/R175/R133/R180/C129 aft of the bridge; RAW_ACT sense divider on the bottom |
| Terminal band | 81.3–99.2 (block) | 68.3–78.5 | **61.5–71.7** | J121 (10, 66.6) rot 90, J124 (36, 66.6) rot −90, R134 (23, 64.06) on the aft pins |
| CONT row | inside block | — | **71.7–72.75** | R173/R129/R130/R178/C127 between Q124 and J1 |
| J1 band | 104.85–116.14 | 78.85–90.14 | **72.75–84.04** | J1 (27, 78.3) rot 180. Below it: input protection aft of its pads and the damper in the forward strip |

Savings against A2 (92): 1.5 mm from the strip, 3.6 mm from pulling the RF zone inside it, 1 mm from the
U1–J122 gap and 1.6 mm from the J122–terminal gap; the battery corner takes back 1.7 mm of A2's optimism (A2 did not
model input protection at J1). The result is 86 mm. Every band boundary above is measured on the prototype
(`proto/s86.place.tsv`).

---

## 2. Placement (prototype `proto/s86.place.tsv`, KiCad mm, rotation in degrees, F = top / B = bottom)

**Outline and holes:**
- Outline 46 × 86 mm.
- M3 supports at (4, 4), (42, 4), (4, 82), (42.6, 82.7) and **mid-span (42, 41.5) on the east edge**, which is in the
  middle third and suppresses the unsupported-east-edge mode that limited R8.
- Tie holes at (16.0, 52.15) and (30.0, 52.15), at J122's x ends, with a 4 mm channel along y 50.15–54.15.

**RF strip:**
- The modules, jacks and RF lines stay at R8's coordinates and are redrawn from rules, not copied: U30 (10.41, 14.95)
  rot 90, U31 (29.86, 14.0) rot 180, J30 (12.85, 0), J31 (31.54, 0), the chain D30/L30/C302–C305/R304 and
  D31/R316/C313/C314, and the GNSS limiter Q30–Q32/R300–R303/C304 on B.Cu under U30.
- Moved inside the strip:
  - FB30 (19.2, 17.4), C300 (17.6, 15.0) and C301 (17.6, 19.6), between the modules;
  - R305 and R307 (2.2 / 3.4, 18.6), west of U30;
  - R306, R315 and R310 (20.6 / 21.7 / 22.8, 20.6) and R313 (20.6, 14.0), at the strip mouth;
  - FB31 (39.9, 21.1); C310–C312 and R311 as R8, east of U31.
- Stretch (not prototyped): compress the GNSS line from 5.76 to about 4.3 mm and the radio line from 4.76 to about
  3.6 mm, with the chain shunts placed east of the line. That moves the modules about 0.6–1.0 mm aft, to y_f ≈ 21.0,
  but needs a new RF solve of the discontinuity windows (section 6).

**Gap band (y 22–26.85):**
- Top: LS120 (3.8, 24.9), J123 (10.8, 24.2), U13 (33.6, 24.4), C92 (37.6, 24.4), R100 and R101 (41.2, 23.2 / 25.2),
  TP75 and TP76 (44.6), C100 and R102 (30.7).
- Bottom: the buzzer driver Q123, R162, R163 and D123; the pull-pin parts R160, R161, C160 and D122; the camera-I/O
  capacitors C90, C91, C93 and C94; R103–R105; TP90 and TP91.
- None of these is a restricted part (switcher, MCU, flash, crystal) or carries a fast net, so they may sit inside
  F10's 5 mm band.

**U1 band:**
- U1 (23, 35.5) rot 0, its pins 51–75 aft and 1–25 forward, as R8. U3, Y1 and the decoupling under U1 are R8's
  spike-a block moved by −9.5 mm.
- **IMU U4 (17.6, 40.0) B rot 0**, under U1's west half: lever arm 5.4 mm, axis map unchanged.
- Barometer U5 (9.2, 47.4) B.
- West edge: J3 (4.6, 33.6) rot −90 and J2 (2.35, 43.4) rot −90, the USB block as R8, the LEDs as R8.
- East edge: J9 (42.7, 32.4) rot −90.
- Camera supply: U7 (33.8, 30.7) B, U8 (39.95, 34.95) B and C74–C76 on the bottom, with L3 (35.0, 41.45) and
  C72/C73 (37.0, 29.0 / 33.55) on top. U12 (33.6, 35.5) sits beside U1's east-face camera pins 37/38.

**Servo chain and J122:**
- J122 (23, 52.15) rot 180.
- R150–R153 at x 26.81 / 24.27 / 21.73 / 19.19, y 46.25, rot 90, on top.
- D121 (23, 45.4) B, R154–R157 B, and R168 (CONT 4.7 k, MCU end) (23, 43.25) B.
- C121 (8, 52) rot 180 with C150/C151 under it.
- C84 (37.3, 52.45) rot 90, with the logic supply under it (U2 (38.25, 55.85) B, L1 (43, 55.85) B,
  U11 (35.9, 47.85) B).

**CH1 pyro block** (A2 handedness, all on top except TP122):

| Part | Position | Role |
|---|---|---|
| J121 IGN | (10, 66.6) rot 90 | entry −x, west wall; pins IGN (10, 64.06) aft, OUT (10, 69.14) forward |
| J124 ARM | (36, 66.6) rot −90 | entry +x, east wall; pins BUS (36, 64.06) aft, RAW_ACT (36, 69.14) forward |
| R134 2 Ω 2512 | (23, 64.06) rot 0 | IGN pad west, BUS pad east: both feeds are one straight line along y 64.06 |
| Q124 AON7524 | (18.9, 69.0) rot 90 | drain west, toward J121.1 (straight OUT trace along y ≈ 69.1); gate pin on the aft-east corner |
| R128, C126, R126, R127 | (21.75, 67.6), (23, 67.9), (25.75, 68.6), (28.7, 69.4) | gate network east of Q124; R127 (1 k) at the GATE_N exit end |
| R173, R131, R129, R130, R178, C127, C128, D120 | front row y 70.5–73.7, x 7.6–24.2 | continuity divider (split top) and cold pull-up, between Q124 and J1 |
| R132, R175, R133, R180, C129 | (28.3, 61.2), (28.3, 58.6), (26.7, 58.6), (25.5, 58.6), (23.9, 58.8) | arm divider aft of the BUS pad; ARM1_SENSE exits aft-east straight to R170 |
| TP122 | (23.2, 68) B | gate test pad on the bottom. Its via to PYRO1_GATE gets a GND via within 1.5 mm (removes A8) |

**Battery corner (east):**
- J1 (27, 78.3) rot 180: J1.1 BAT_IN at x 34.6.
- **Q121 (42.15, 67.1) B and Q120 (42.15, 74.42) B**, stacked under J124's outboard half and the J1 flank, source rows
  facing.
- D8 (25.5, 73.15) B, C96 (31.95, 74.25) B and C80 (36.95, 74.25) B, aft of J1's pad row.
- The damper C89 / C95 / R166 and R167 in the forward bottom strip (y 83.3).
- R80 and R165 (J1.3 / J1.4 switch legs) at (14.6 / 12.8, 83.3) B.
- U9 (40.35, 76.9) on top, with its network beside it; the gate driver Q122 / R121–R123 / C120 / R120 next to it.
- The RAW_PROTECTED clamp and bulk D9 (43.7, 68.4) and C82 (44.0, 62.5) on the east edge.

Note on the prototype's test pads: the legaliser parked TP80 (BAT_IN) and TP121 (ACT_GATE) at legal but wrong places,
TP121 1.71 mm from the BUS pin. The real table puts TP80 at J1.1 and TP121 at Q120's gate. This is a table edit, not
a feasibility question.

**Variant W** (`proto/w86.place.tsv`, also legal at 86 mm): C121 east on the 7.7 A spine and C84 with the logic supply
west. It keeps all RAW_ACT copper in the east column, but S17 rises to 1774 mm, C84's fit margin falls to 0.49 mm and
RAW_PROTECTED crosses the board. I do not recommend it.

---

## 3. Pin changes

- **Contract pins unchanged:** 3 GATE_N, 15 CONT, 22–25 servos, 33 ARM, 34 RAW sense, the sentinels, and the NC pins
  40/97. The R8 RF map is H0, so the RF interface needs no move: SPI2 PB10/PB11/PB14/PB15 with IOSWP, BUSY PD8,
  RXEN PD9, DIO1 PE15, NRST PE9, GNSS USART6 PC6/PC7, RESET_N PD14, TIMEPULSE PD15.
- **Status-pin moves, recommended because C puts LS120 and J123 in the aft gap band.** Topology survey T9:
  - BUZZ_DRV PC13 → a free aft-face or aft-west pin. PB12 (pin 51) or PA10 (pin 69): PA10 is the ROM USART1_RX input,
    so check its bootloader pull state.
  - PULLPIN PC14 → PD0 (pin 81, west face, aft).
  - BAT_FAULT_N and USB_FAULT_N / VBUS_SENSE moves only if routing asks for them.

  Each move needs a DS12110 / RM0433 / AN2606 citation in `pin_table.tsv`, the D5 loader rule and the D6 EXTI-sharing
  check (owner O-C4). Without them, BUZZ_DRV and PULLPIN run about 25 mm round U1 (Estimate).
- **J122 plug numbering:** turned J122 (rot 180) puts SERVO1 at the east end while U1.22→25 run west→east, a full
  four-lane reversal: 6 crossings, about 4 vias. The recommended fix (owner O-C2) is a numbering-mirrored J122 footprint
  plus a reviewed `check_actuators` item, with the silk legend following, so that SERVOn_OUT lands where the lane
  arrives. The alternative is R8's via solution.
- **No other pin moves.** The camera UART stays on UART7 (east face), which is why the camera block stays east.

---

## 4. Layer plan (JLC041611-7628, unchanged)

| Layer | Use in C |
|---|---|
| F.Cu | Primary signal layer in the U1/servo/strip zones. RF GCPW lines; pyro BUS/IGN/OUT feeds only (no pyro signal on B.Cu under live pads); RAW_PROTECTED trunk and BAT_IN on the east edge. GND pour with stitching |
| In1 | Solid GND everywhere: no tracks (D20), no In1 slots except J3/J123 legs; the RF launch cut-outs keyed to each jack (R-4) |
| In2 | **Three regions:** GND (strip, pyro block and every pyro / servo lane), 3V3 (under U1 / flash / IMU / baro, with Y1's keep-out), RAW_ACT (east column x 39.8–45.5 aft of J124, then a band y 51–59.9 west to J122's RAW row). BAT_IN needs no In2 island (J1.1 → Q120 is about 8 mm on B.Cu). No signal track (S15 = S16 = 0, no rigid exemption) |
| B.Cu | Second signal layer. The 7.7 A spine (Q120 → Q121 → corridor), the GATE_N and CONT exits under R134 (F.Cu is the live layer there), the CONT crossing under the servo lanes, the GNSS limiter under U30. GND pour |

The In2 RAW_ACT band keeps 2.5 mm in plan from BUS/IGN/OUT copper (D18): it stays at x ≥ 39.8 beside J124.1 and
y ≤ 59.9 aft of the bridge. Under every pyro and servo B.Cu lane, In2 is GND.

---

## 5. Routing: what becomes simple, what stays hard

**Simpler than R8 (by construction; lengths are octilinear, Measured on the placement):**
- **Pyro bridge:**
  - IGN and BUS are one straight F.Cu line along y 64.06: J121.2 → R134 → J124.1, about 9 + 9 mm.
  - OUT is one straight line along y 69.1: J121.1 → Q124 drain.
  - Q124's gate is 1.5 mm from R128 and C126, so PYRO1_GATE is under 3 mm long (R8 5.3 mm).
- **Exits:**
  - ARM1_SENSE: 19.4 mm straight aft-east to R170 (R8 55.2).
  - GATE_N: 28.3 mm (R8 39.3), B.Cu under R134 then west of J122's tie hole.
  - CONT: 32.4 mm (R8 35.2).
  - The sum is 80 mm (R8 130), within the R9 stretch row (≤ 80) on the octilinear measure.
- **Servo lanes:** 30 mm in all (R8 98). They are straight if O-C2 is accepted.
- **7.7 A spine:** 43 mm polyline (R8 61.5). J1.1 → Q120 → facing-source bridge → Q121 → B.Cu corridor → via field
  → In2 band → J122. No series via in BAT_IN. RAW_ACT reaches J124.2 by about 4 mm of B.Cu.
- **RF interface:** U1 sits 9.5 mm nearer the modules. R8's rfif copper is 321 mm; I estimate C at about 230–260 mm,
  which reaches the R9 stretch row (≤ 250) on the low side (Estimate).
- **GNSS limiter escapes (A2/A3 removed):** LNA_EN and VCC_RF go straight aft from U30 pins 13/14 to vias at y ≈ 7.4,
  west of the RF line, once the chain shunts (D30's GND pad, L30's cold end, C302, C303, C305) sit east of the line.
  The limiter stays on B.Cu under U30, so F10's text is kept.
- **A8 removed:** TP122's via gets a GND via within 1.5 mm, which leaves C1 and C3 at 0.

**Compromises that remain:**
- **TXEN loop round U31:** forced by the module pinout plus F10. It is one keep-out-forced detour, the only S8/S9
  exception.
- **CONT crossing:** CONT (pin 15) sits inside the servo fan-out, so it drops to B.Cu at U1's forward edge (1 via plus
  a GND via). This is one of A2's two remaining contract crossings.
- **Dense band y 24–44:** USB, SWD, camera, IMU, flash, QSPI and the RF interface converge. Peak cut demand is 30
  lanes at y 31 (R8 27 at y 53). Expect more vias here than R8's U1 field.
- **East column:** carries the camera supply, the logic supply, U9, the RAW_PROTECTED trunk, the RAW_ACT corridor, the
  ARM sense lanes, J9 and C84. The bottom east is the board's densest region; the routing reserve there is the main
  risk to the 86 mm point.
- **Fewer GND via spots in the battery corner and the pyro block:** P9/P10 and R6b are at risk.

---

## 6. RF strip: how it is re-derived (survey §8.4–8.5)

1. **Geometry by rule, not hash:** R-1 to R-13 replace `check_r8`'s five strip groups. The strip boundary y_f = 22.0
   is recorded in one constant, and every RF part's courtyard ends before 21.8 (the prototype's added legaliser rule;
   RF zone depth Measured at 21.7 mm). In1 and In2 carry only GND at y < 22. The F.Cu / B.Cu net lists are
   `check_r7.STRIP_F` and the tightened `STRIP_B` (GND plus the limiter nets, plus RADIO_TXEN only if its loop uses
   B.Cu).
2. **GCPW:** keep the qualified cross-section (W 0.30, gap 0.25–0.30, In1 under ±0.70 mm), so every straight section
   inherits pass 2's 50.3 Ω. Any new section (a compressed-chain window, a bend) is re-solved by a **rebuilt 2-D finite
   volume solver**, `tools/gcpw_solve.py`. It follows pass2_rf §7's method: symmetric half domain, grounded lid at
   3 mm, SOR to 1e-8. It is validated against pass 2's 50.3 Ω / εeff 3.18 and the JLC engine's 50.24 Ω before use.
3. **Launch:** each jack's land, In1 cut-out (x ±0.9, y 0–4.6), the eight stitching vias and In2 GND under the cut-out
   are drawn in the jack's own frame (R-4). Congruence carries the 49.0 Ω launch.
4. **Return loss:** re-list every discontinuity window per line (R-5: ≤ 0.6 mm each, no more windows than R7's chain),
   then re-run pass2_rf §3.12's cascade, aiming at RL ≥ 19 dB GNSS and ≥ 25 dB radio (R7 Inference figures).
5. **Stitching and fence:** side gaps ≤ 2.5 mm on both sides of both lines, which removes R7's 4.0 / 2.7 mm GNSS
   ceilings now that the shunts are off the west side. Fence row at y ≈ 21.8, ≤ 2.0 mm pitch, openings ≤ 2.7 mm.
   Strip GND reach ≤ 4.0 mm.
6. **Keep-outs:** U30_KEEPOUT (F.Cu, In1) and U31_KEEPOUT (all layers) are derived from the footprint body boxes, with
   GND under them sampled every 0.2 mm.
7. **Separations (Measured on the placement):**
   - Nearest RF part to a restricted part: 5.01 mm (FB31 to C72). C72 moves 1 mm to beat R8's 5.94 "done" row.
   - Nearest RF part to a fast pad: 5.66 mm (R306 to U1.70).
   - Module courtyards 7.56 mm apart (unchanged from R8). The RF lines (15.45 mm apart) and the jacks (18.69 mm
     apart) are unchanged, because the modules and jacks keep R8's places.
8. **Coexistence:** radio interface lanes stay ≥ 5 mm from U30's body box. They leave U31's west side at x ≥ 23.2;
   U30's body ends at 15.5. They stay ≥ 6 mm from GNSS RF copper. Radio to pyro terminals is **41.6 mm** (R8 68.3):
   R-13 gates at the proposed 40 mm, but owner acceptance is needed (O-C1). F10's pyro immunity stays a bench test.
9. **Supply:** C311 ≤ 1.8 mm, C312 ≤ 2.0 mm and C310 ≤ 3.6 mm from U31.1 (positions as R8); C300/C301 beside U30's
   VCC pins. GNSS VCC path ≤ 0.2 Ω by DC solve.
10. **Records:** F10's strip text becomes "y 0–22.0 of a 46 × 86 mm board"; the quoted stitching gaps are re-measured;
    ORDERING §5's RF coordinates and the VNA shunt model are updated.

---

## 7. Pyro block: how it is re-derived and re-proved (survey §9.4–9.5)

**Prototype evidence, pad level** (`c_pyro.py`, same rule code as `m3.kicad_dru`; R8 measured with the same script for
comparison):

| Rule | R8 pads: margin / pair | **C 86 (strict) pads: margin / pair** |
|---|---|---|
| B live–gate (0.5) | 0.527 R126.2–R134.2 | **1.360** R128.1–R134.1 |
| C live–sense (0.3) | 0.469 | 0.116 R131.1 OUT–R173.2 CONT_MID (R173's own divider half: tolerated class) |
| D GND–live (0.5) | 0.121 C128.2–R134.1 | **0.514** R128.2–R134.1 |
| E ARM break (1.0) | 1.480 (J124's own pins) | 1.480 (same maker geometry) |
| F live–other (0.5) | 1.325 | 1.210 J124.1–TP121 (test pad parked; moves) |
| G gate–live in block (0.3) | 0.962 | **1.478** |
| **H bridge (1.0)** | **0.025** Q124.5–R129.2 | **0.224** R177.1–R124.2 (stretch ≥ 0.2 met) |
| Bridge class "fires" (< 1.5 mm) | 2 pairs (1.027, 1.491) | **0** |
| "gate to sense node" (< 1.5 mm) | 1 (1.262) | **0** |
| "live past divider top" (< 1.5 mm) | 4 (1.025–1.161) | 3 (1.224–1.326) |
| "actuator switch on" (< 1.5 mm) | 0 | 4–5 at 1.22–1.40 mm (strict rule holds ≥ 1.2; finish ≥ 1.5 by hand) |
| CH1 bounding box | 662.4 mm², fill 0.517 | **658.0 mm²**, fill 0.521 |

The non-strict 86 mm board, legal under R8's rules alone, showed what compactness does when nobody watches. It had
ACT_GATE pads 0.63 mm from GND pads and CONT pads 1.07 mm from a gate pad: about 0.41 V on the gate in reset through
the CONT divider's Thevenin source, against the AON7524's 0.4 V minimum threshold (Calc).
**So C must make the strengthened pad rules part of its gate**: P-5's bridge classes as legaliser rules, P-6 and P-7.

**What to re-prove on the routed board** (each item is a gate or a recorded table, never a hash):
1. **DRC A–H and A2 on every layer**, with per-rule closest pair and margin (`requalify.pyro_rules`).
2. **P-1 PYRO_BLOCK by content:** one rule area containing every CH1 courtyard + 1 mm and all BUS/IGN/OUT/GATE/COLD/MID
   copper, plus GATE_N/CONT/ARM1_SENSE copper to 3 mm past the last CH1 pad. Rule G then covers every gate segment.
   **P-1b** (rule G board-wide outside U1) is recommended for C because GATE_N runs 28 mm.
3. **P-2 armed-live copper confined** to the block. **P-3 purity:** inside the CH1 hull + 1 mm, F.Cu carries CH1 nets,
   GND, RAW_ACT (J124.2) and 3V3 (D120) only; In1/In2 are GND; on B.Cu foreign copper stays ≥ 1.0 mm from CH1 copper.
   In C the battery corner sits outboard and forward of the hull. Q121 and Q120 lie on B.Cu under J124's outboard
   half, so they are inside the hull + 1 mm. P-3 allows that on B.Cu only, with foreign copper ≥ 1.0 mm and bare pads
   ≥ 1.5 mm from the terminals' bottom pads. Their courtyards start 2.16 mm from J124.1's pad edge (X2d 2.36–2.65 mm,
   Measured); this is a check item. On F.Cu, foreign nets must stay outside the hull: the RAW_PROTECTED clamp D9 and
   bulk C82 on the east edge sit within about 0.5 mm of the hull + 1 mm line and move east in the frozen table.
4. **P-4 rule-H liveness:** the seeded-fault suite (each closest H pair moved 0.05 mm inside 1.0; the rule lowered,
   deleted, narrowed; RAW_ACT or ACT_GATE dropped) runs on every build in `tools/test_r9_check.py`.
5. **P-5 bridge table:** every exposed same-face pair < 1.0 mm (reported to 1.5 mm) with a safety net on either side,
   each with its single-bridge consequence and M3_R4 §3 cold-test signature. Only R4's tolerated classes are allowed
   under 1.0 mm. C adds an explicit row: ACT_GATE/ACT_DRV pad ≥ 1.5 mm from a GND pad, Q120–Q122 own pads exempt.
6. **P-6 bare gate pads** ≥ 1.0 mm from bare always-live pads; bare gate to bare BUS/IGN ≥ 1.0 mm (pads: ≥ 1.86).
7. **P-7 gate guard:** PYRO1_GATE and GATE_N copper ≥ 0.5 mm, same layer and layers < 0.5 mm apart, from every net
   whose short would put ≥ 0.2 V on the gate in reset. In C:
   - GATE_N and CONT run 0.5 mm apart on B.Cu, not R8's 0.30.
   - GATE_N passes under R134 on B.Cu, 1.6 mm through the stack from the F.Cu BUS/IGN pads, which is allowed.
   - The divider nodes keep ≥ 1.5 mm pad spacing from the gate network.
8. **Divider fault tolerance (layout preconditions):**
   - Each divider half is a separate part (unchanged netlist).
   - No single bridge shorts a whole divider top (H plus P-5).
   - R168, R170 and R172 sit at the MCU end, with *_MCU copper ≤ 3 mm (P-8).
   - List every node-side lane neighbour with the pin current it could force.
9. **Coating and leakage:** the coat region (P-10) is the block outline plus J2. It stays clear of U4's 3 mm zone: U4
   is under U1, more than 25 mm away. It must stay clear of U9's cluster and the J1 mating face; the region is drawn,
   not implied. Bare gate to bare armed-live pad ≥ 1.027 mm (pads: 1.86).
10. **Gate reset behaviour:** topology and values unchanged (`check_actuators`); each GATE_N / GATE lane neighbour is
    listed with the gate voltage a hard short gives in reset, which must stay < 0.2 V or be guarded.
11. **Fire-loop copper** by `dc_solve.py` on the PYRO1 nets. The estimate is about 30 mm of 1.2 mm 1 oz, about
    12 mΩ, against F7's 0.3 Ω allowance (Calc).
12. **Fit and harness:** both terminals keep R8's wall entries and wire room (6.3–6.9 mm, Measured). J1 sits within
    25 mm of both terminal centres (20.6 / 14.8 mm, Measured). Re-word the fuse-holder keep-off, "never probe R134
    armed" and the GND probe points.

---

## 8. 7.7 A spine and power

**The spine (east column):**
- J1.1 → Q120 by B.Cu, in a band y 75.5–81 at x 34.6–39.5. That band is 5.6 mm wide against D12's ≥ 5.3 mm: a
  **thin margin**, kept by holding C87, R82 and TP89 out of the band.
- Q120 → Q121 across the facing source rows. The neck is pad-limited, as in R8, at about 4.4–5 mm against ≥ 3.71.
- Q121 drain → B.Cu corridor x 38.8–45.5 (6.7 mm) aft to y ≈ 59 → a via field of ≥ 12 vias, from R8's 0.86 A
  worst barrel → In2 RAW_ACT band (≥ 5.7 mm inner, against D12's 5.6) → J122's RAW row and C121.
- `run_dc.sh` at 0.1 mm gates every build; 0.05 mm is the qualification grid.
- Expected rises (Inference, shorter and wider copper): RAW_ACT ≤ 17.5 °C and BAT_IN ≤ 14.5 °C if the band holds
  5.6 mm, ACT_FET_S ≈ R8's 21 °C.

**Other power:**
- **Logic supply** under C84, east (R8 arrangement, translated): RAW_PROTECTED trunk 0.5 mm on F.Cu at x ≈ 44–45.5
  from U9 aft to U11 and U7. Keep it **east of x 41.6**, outside the CH1 box and ≥ 6 mm from J124.1.
- **U9 at the battery corner:** BAT_ENABLE runs J1.4 → U9 along the forward bottom strip, not past the bridge as in R8,
  where it was the worst X2 offender at 0.70 mm. D9 and C82 sit 6–8 mm from U9's OUT, comparable to R8's recorded
  7.3 / 8.1 mm.
- **Bucks:** U2/L1 and U8/L3 follow their makers' layouts. Both are ≥ 5 mm from RF parts (5.01 mm Measured to the
  nearest buck capacitor; C72 moves 1 mm for margin).

**Requalification:**
- Hot-plug premise: D8, C80, C96, C89, C95, R166 and R167 sit 4.1–11.8 mm from J1.1 (Measured, J1.1 centre to each
  part's nearest pad centre; R8 3.9–10.6 mm). R166 (11.8 mm) moves inside 10.6 mm in the frozen table. Re-run
  `step9/hotplug_feed.py`.
- The servo GND return J122 → J1.2 is 27 mm of In1 plus F.Cu/B.Cu under the pyro block (R8 37 mm). Re-run DC_GND.

---

## 9. Prototype evidence (scratch, reproducible)

| Board | Rules | Result |
|---|---|---|
| 46 × 88 | R8 legaliser + RF zone in strip | 0 violations |
| 46 × 86 | same | 0 violations |
| **46 × 86 strict** (`s86`) | + strengthened pyro pad rules (H ≥ 1.2, ACT gate–GND ≥ 1.2, gate–sense ≥ 1.2, P-6) | **0 violations** |
| 46 × 88 strict (`s88`) | same | 0 violations |
| 46 × 85 | R8 legaliser + RF zone | 4 parts unplaceable (battery corner: R81, C81, D8 by TP122, Q122 by J124's pins) |
| 46 × 84 | same | 7 parts unplaceable (same corner, plus C120, R84, D9) |

`fit_check` on s86 (TIE_HOLES patched to C's tie holes) **passes**:

| Item | C (s86) | R8 |
|---|---|---|
| J9 mated | 0.03 | 0.03 |
| **J122 mated** | **0.50** | 0.71 |
| J3 | 0.89 | 0.89 |
| C84 | 1.12 | 1.37 |
| J121 / J124 | 1.15 | 1.15 |
| Worst bottom | 2.06 (L1; −0.3 mm move restores R8's 2.36) | 2.36 |
| Bottom to support | 3.85 (C75) | 4.45 |
| Top to support | 3.816 (TP84) | 5.01 |
| Wire entry | 6.3–6.9 | 6.3–6.9 |

Placement metrics (`c_metrics.py`, s86 against R8, both measured by the same script):

| Metric | R8 | C 86 |
|---|---|---|
| Length | 118 | **86** |
| S17 placement MST, non-pour nets | 1638.9 | 1695.9 (unoptimised; A2s at 88 had 1638 after the survey optimiser) |
| Top / bottom courtyard utilisation | 0.413 / 0.193 | 0.598 / 0.234 |
| Peak / mean cut demand (lanes) | 27 / 10.8 | 30 / 13.7 |
| RF zone depth | 30.52 | 21.7 |
| Rule H minimum pad gap | 1.025 | 1.225 |
| X2, pads only (foreign nets ≤ 3 mm of armed-live pads) | 4 (BAT_DAMP, ACT_GATE, BAT_OVLO, BAT_ENABLE) | 4 (3V3 by design, BAT_IN 2.36, ACT_FET_S 2.65, ACT_GATE 1.71 from the parked TP121). s88: 2 |
| X2d battery-live to armed pads | 3.56 | 2.36 (s88: 2.65) |
| IMU lever arm | 13.0 | 5.4 |
| 7.7 A polyline | 61.5 | 43.1 |
| Exit lanes (octilinear) | 129.7 | 80.1 |
| Servo lanes | 97.8 | 30.3 |
| Radio to terminals | 68.3 | 41.6 |
| Panel-tab windows | west aft, west 48–72, west 86–112; east aft, east 104–112 | west aft, west 61–70; east aft only |

Renders:
- `compact/proto/c86_strict.svg.png` (design point);
- `c86_w.svg.png` (variant W);
- `c88_v2.svg.png`;
- `c84_v1.svg.png`, the first, illegal, 84 mm attempt.

---

## 10. Expected metrics against the R9 scorecard (`survey_baseline.md` §2)

Status: ✓ expected met; ~ at risk; ✗ expected miss (with its cause). Measured = placement prototype; the rest are
estimates for the routed board.

| Row | R8 | R9 hard / done / stretch | C estimate | Status |
|---|---|---|---|---|
| G gate (R9 check.sh) | 0 | 0 | 0 | ✓ (by construction) |
| Rigid hash groups | 12 | **0** | 0 | ✓ |
| X1 length | 118 | ≤ 118 / ≤ 110 / ≤ 104 | **86** (Measured) | ✓✓ |
| C1 / C3 allowlist | 3 / 3 | ≤ 1 / 0 | 0 (A2/A3 by chain-shunt side, A8 by GND via) | ✓ |
| C2 info instances | 91 | ≤ 80 / ≤ 40 | 85–110 | ✗ density: more pad-entry offsets and width junctions |
| S1 signal track | 1497.9 | ≤ 1497.9 / ≤ 1300 | 1300–1450 | ✓ (~ stretch) |
| S4 signal vias | 55 | ≤ 55 / ≤ 40 | 75–85 | ✗ two signal layers under 0.6 top density (survey T7) |
| S6 / S7 detour ratio / excess | 1.174 / 285.8 | ≤ 1.174 / ≤ 285.8 | 1.15–1.20 / 230–300 | ~ |
| S8 / S9 | 4 / 4 | ≤ 1 / ≤ 1 | 1 / 1 (TXEN, keep-out-forced) | ✓ |
| S10b bends / X6 bends per mm | 231 / 0.154 | ≤ 231 / ≤ 0.154 | 230–270 / 0.16–0.19 | ✗ X6 |
| S12 critical layer changes | 25 | ≤ 25 / ≤ 18 | 25–32 | ~ |
| S15 / S16 inner signal | 3.4 / 0 | 0 / 0 hard | 0 / 0 | ✓ |
| S17 placement MST | 1638.9 | ≤ 1638.9 / ≤ 1450 | 1696 Measured unoptimised; 1600–1650 after optimiser + T9 pins | ~ |
| P1 In1 coverage / P2 islands | 0.905 / 1 | ≥ 0.905 / 1 | ≥ 0.91 / 1 | ✓ |
| P4 / P6 In2 regions / perimeter | 5 / 1752 | ≤ 5 / ≤ 900 | 3 / 600–800 | ✓ |
| P7 outer GND islands ≤ 1 via | 1 | 0 | 0 | ✓ (stitching table) |
| P9 / P10 GND-via reach | 4.47 / 9.65 | ≤ 3.5 / ≤ 7 | 3.3–4.0 / 6–8 | ~ battery corner and pyro interior |
| R6b critical reference share | 0.111 | ≤ 0.08 | 0.08–0.11 | ~ more antipads |
| D_raw / D_bat / D_fet | 17.5 / 14.5 / 21.4 °C | ≤ 20 / ≤ 20 / ≤ 30 hard; done = R8 | ≤ 17 / ≈ 14–18 / ≈ 21 | ✓ hard; ~ D_bat done (5.6 mm band) |
| X2 / X2b foreign nets ≤ 3 mm | 6 / 7 | ≤ 2 / ≤ 3 | 2–4 / 3–5 (pads only: 2 at 88, 4 at 86) | ~ |
| X2c / X2d | 0.70 / 1.089 | ≥ 1.0 / ≥ 2.5 | ≥ 1.0 / 2.36–2.65 | ✓ / ~ |
| X2e CH1 bounding box | 662 | ≤ 662 / ≤ 500 | **658** (Measured) | ✓ |
| X2g foreign nets through the box | 6 | ≤ 1 / 0 | 3–6 (ACT_FET_S, ACT_GATE, BAT_IN, VLOGIC/SW at C84's corner) | ✗ the box spans x 4.5–41.6; the battery corner shares the east edge with J124 by topology (T3) |
| X3 strip depth / X3f rfif | 21.39 / 321 | ≤ 21.39 / ≤ 321 (≤ 250) | 21.39 (stretch ≈ 20.4) / 230–260 | ✓ |
| X5 widths | 11 | ≤ 8, signal ≤ 5, power ≤ 5 | 8 | ✓ (width table in the generator) |
| X6c mean segment | 2.63 | ≥ 2.63 / ≥ 3.5 | 2.3–2.7 | ~ |
| X8 pour trims | 8 | 0 | 0 | ✓ |
| X9 RF separations | 5.94 / 5.075 | ≥ 5.0 hard; done = R8 | 5.01 → 6.0 after moving C72 / 5.66 | ✓ |
| X9c inner power to pyro | 2.65 | ≥ 2.5 / ≥ 2.65 | ≥ 2.65 (In2 RAW edge drawn at the 2.5 mm line + 0.15) | ✓ |
| Y1 / Y1b close pairs | 27 / 8 | ≤ 10 / 0 | 15–30 / 0–4 | ✗ density |
| Y3 / Y5 | 23 / 26 | ≤ 12 / ≤ 10 | 12–20 / 10–20 | ~ |
| Z1 pyro margins | H 0.025, C 0.077, B 0.17 | done = R8; stretch H ≥ 0.2 | H 0.224, B ≥ 0.5, C ≥ 0.1 (pads) | ✓ |
| Z2 exit lanes | 137.5 | ≤ 137.5 / ≤ 80 | 85–100 routed | ✓ (~ stretch) |
| Z3 IMU lever arm | 13.0 | ≤ 13 / ≤ 5 | 5.4 → ≤ 5 with a 0.4 mm move | ✓ |
| Z4 vias in test pads | 1 | ≤ 1 / 0 | 0 | ✓ |
| Z5 / Z5b bare gate distances | 1.027 / 0.634 | ≥ R8 | ≥ 1.86 / ≥ 1.0 (P-6) | ✓ |
| F1 / F2 fit | 0.028 / 2.357 | ≥ 0; done = R8 | 0.03 / 2.36 after moving L1. **J122 0.50 against 0.71** | ~ J122 margin |
| F3 / F4 supports | 4.45 / 5.01 | ≥ 3.5 / ≥ 3.8 hard | 3.85 / 3.82 | ✓ hard (no-regression rows want a recorded reason) |
| index_r8 / index_r9 | 100 / 100 | ≤ 86 / ≤ 73 | ≈ 85–95 / ≈ 75–85 | ~ / ✗ the S4, C2, X6 and Y1 misses outweigh the length and pyro gains |

Bottom line: C meets every hard row and the pyro and safety rows, and wins length decisively. It is expected to miss
3–5 routing-texture "done" rows (S4, C2, X6, Y1, X2g), each with the measured cause "density at 86 mm". That is
exactly the owner's P1 versus priority-2 trade, and it must be accepted explicitly (O-C1) or bought back with length
(88 → 92).

---

## 11. Requirements and safety rules at risk, and how they are protected

| Item | Risk in C | Protection |
|---|---|---|
| AGENTS §2.1 ARM break, F8 rule E | ARM terminal shares the east edge with the 7.7 A corridor | RAW_ACT outer copper ≥ 1.0 mm from J124.1 (corridor x ≥ 38.3), inner ≥ 2.5 mm (D18, x ≥ 39.8); rule E in DRC; RAW_ACT reaches J124.2 from forward/outboard only |
| F8 rules A–H, solder bridge | Denser block (fill 0.52) | Strict pad rules in the legaliser; P-4 seeded faults and the P-5 bridge table as gates; Measured H margin 0.224, no "fires" or "gate to sense" pair < 1.5 mm |
| AGENTS §2.4 gate defined off in reset | Sense or actuator nodes near gate pads (seen on the non-strict board) | P-7 guard rule plus the reset-voltage table per neighbour; ≥ 1.2 mm (finish 1.5) pad spacing from sense nodes |
| D85 battery-live to armed-live ≥ 1.0 (target 2.5) | Q121 under J124's outboard half | Measured 2.36–2.65 mm; `battery_pyro` gate; Q121 source row faces forward (away from BUS) |
| F10 5 mm separation | U1 and the camera buck are pulled to the strip boundary | F10 gate (`rf_separation`), 5.01 → 6.0 mm after moving C72; interface R inside the strip |
| F10 strip content, U30/U31 keep-outs | Feeds now inside the strip | R-2 net lists; B.Cu in the strip carries the limiter nets only; keep-outs derived from footprints |
| F9 hot-plug premise | Input protection must stay within ~10 mm of J1.1 | Measured 4.1–11.8 mm (R166 to be pulled within R8's 10.6); `hotplug_feed.py` re-run; this is the rule that sets the 85–86 mm floor |
| F4 / D12 7.7 A necks | BAT_IN band only 5.6 mm wide | Build-time `run_dc.sh` gate; C87, R82 and TP89 kept out of the band; F.Cu under J1 as a parallel path if needed |
| P2 fit | J122 margin 0.50 (R8 0.71); supports 3.82 / 3.85 | `fit_check` gate ≥ 0; M-5 no-regression row needs O-C8 or J122 at rot 90 (+2 mm) |
| P2 vibration | Shorter span; C121 / J121 on the unsupported west edge | `plate_model.py` on the final geometry; gate f1 ≥ 209 Hz, target 241. Estimate ≈ 330–420 Hz (Inference: span 78 against 110 mm) |
| P3 coating / leakage | Coat region close to U9's cluster and J1's mating face | P-10 coat-region check; the region is drawn; TP122 coated last |
| M1 / M2 manufacturability | Tab windows scarce (east forward none); denser bottom (rework) | Tab-window check in the gate; ask JLC for a 4-tab plan (west aft, west y 61–70, east aft, plus a cleared 5 mm east window near y 55–60) before freezing |
| M3 cost | — | BOM unchanged ($106, 52 extended codes); board area −27 % |
| Clean routing (M2) | Detours and vias in dense bands | route_check profile r9 with an empty allowlist; per-family budgets; kill criterion below |
| F10 pyro immunity, coexistence | Radio 41.6 mm from the terminals | Bench test (unchanged); R-13 at ≥ 40 mm; owner acceptance O-C1 |

---

## 12. What must be requalified

Everything placement-bound, since nothing is copied:
- **DC:** D12 necks at 0.05 mm, the GND return and the fire loop.
- **Reference:** the absolute critical-reference audit (R6b).
- **Pyro:** section 7, items 1–12.
- **RF:** section 6, items 1–10, including the rebuilt field solver.
- **Fit:** fit envelopes, M-3 tie holes derived from J122 and wire room.
- **Vibration:** first mode with the new holes and heavy parts.
- **Hot-plug:** the feed model.
- **IMU:** axis map (unchanged, rot 0 bottom) and lever-arm record.
- **Firmware:** binding note and pin table (T9 moves, J122 numbering).
- **ORDERING:** all coordinates, probe and coat points, tab plan, sled hole list.
- **Records:** REQUIREMENTS P1, P2, F4, F8, F10 and M2 text; parent `docs/VEHICLE.md` stack row (length 86, holes,
  board position, slack +32 mm).
- **Bench assumptions unchanged in kind:** the static, leakage and dynamic pyro gates; RF immunity; S21 / C/N0
  coexistence; the stall thermal test; tap or modal check on the sled; NRST ≥ 1 MΩ after coating.

---

## 13. Implementation: a fresh scripted build (reuse of R8's framework)

`m3_design/r9_build.sh` (deterministic, fixed KIID seed, no autorouter), staged like `r8_build.sh`, each stage followed
by its gate:

1. **Schematic:** `r9_sch.py` (pin moves from `r9_design/pin_table.tsv`; the J122 numbering if O-C2), then ERC,
   parity and `r9_sch_check.py`.
2. **Placement:** `r9_pcb.py` builds the outline, holes and tie holes, and places parts from the frozen
   `m3_design/r9_place.tsv` (seeded from `compact/proto/s86.place.tsv` and hand-finished: test pads, C72, L1, TP84, C75).
   `r9_legalise.py` is `r8_legalise` generalised:
   - constants come from the table;
   - the RF-zone-in-strip rule;
   - the strict pyro pad rules (P-5 classes, P-6, H + 0.2 mm);
   - tab windows;
   - M-3 tie holes derived from J122.

   Then `r9_place_check.py`: DRC with parity, F10, fit, MST (a block-level MST optimiser before freezing, like the
   topology survey's `blockopt`), and the J1 grouping.
3. **RF strip:** `r9_rf.py` draws the GCPW lines, launch areas in each jack's frame, keep-outs from footprints,
   stitching and the fence row from rules. Gate: R-1 to R-12 and `gcpw_solve.py` on every non-standard window.
4. **Pyro block:** `r9_pyro.py` draws the BUS/IGN/OUT feeds, the gate lanes with guard, the exits, and TP122 with its
   GND via. Gate: DRC A–H, P-1 to P-11, the bridge table, the seeded faults.
5. **Power:** `r9_power.py` builds the In2 map (3 regions), the 7.7 A spine and via fields, RAW_PROTECTED and the
   bucks. Gate: D18, D19, D85, the In2 islands and `run_dc.sh` at 0.1 mm.
6. **Signals:** `r9_route.py` with the family modules reused from R8 (qspi_hse, rf, servo, pyro, usb_swd, imu,
   camera, status, links) and re-parameterised. Gate per family: budgets on length, vias and ratio, plus
   `route_check` r9.
7. **Ground:** `r9_ground.py` adds stitching, the fence row, GND vias at critical layer changes and reach vias. Gate:
   P7, P9, P10, C6 = 0.
8. **Post:** `r9_post.py` redraws the silkscreen from nothing, then the full gate `tools/check.sh` (R9 contracts).
   `r9_fab.sh` builds the fab package.

**New tools:**
- `tools/check_r9.py`: every R-, P- and M- rule of the survey; no hashes except DRU_SHA, PYRO_RULE_SHA and the reviewed
  `check_actuators` hash.
- `tools/gcpw_solve.py`.
- `tools/bridge_table.py`, grown from the scratch `c_pyro.py`.
- `tools/test_r9_check.py`: seeded defects for every new check, rule-H liveness included.
- `tools/tab_windows.py`, from the scratch `c_tabs.py`.
- route_check profile `r9`, starting empty.

---

## 14. Effort and sequence

Effort is in focused agent days.

| Phase | Content | Effort |
|---|---|---|
| 0 | Owner decisions O-C1…O-C9; pin table rows with citations | 1 |
| 1 | Gate tools first (check_r9, strict legaliser, bridge table, seeded faults, GCPW solver validated, tab windows) | 3.5–4.5 |
| 2 | Schematic (pins, J122 numbering) | 0.5 |
| 3 | Four spikes in parallel: (a) strip copper at y_f 22 with A2/A3-free limiter escapes and the TXEN loop; (b) pyro block copper and its bridge table; (c) battery corner + spine + DC at 0.1 mm + hot-plug; (d) the dense y 24–48 band with the servo chain | 4 (1.5 elapsed) |
| 4 | Placement freeze with MST optimisation | 1.5 |
| 5 | Power | 1.5 |
| 6 | Signal families (denser than R8) | 5–6 |
| 7 | Ground | 1 |
| 8 | Post and fab | 1 |
| 9 | Requalification and records | 3–4 |
| Review | Independent passes until two consecutive have 0 Critical and 0 Major (expect 3–5 passes with fixes) | 4–6 |
| **Total** | | **≈ 26–32 agent days** (an R8-style clean sheet at fixed length: about 18–22) |

**Kill criteria and fallbacks:**
- **Spike (c) fails D12 or the hot-plug premise at 86 mm:** go to 88. The placement there is already legal, and the
  BAT_IN band gains 2 mm.
- **Spike (d) or phase 6 needs more than about 90 signal vias, or C2 exceeds 120:** go to 88, then 92 (A2).
- **Spike (a)'s GCPW solver does not reproduce pass 2 within 1 Ω:** keep R8's exact strip copper geometry translated
  (no compression) and y_f 22.0.
- **Two kills:** stop C and build A2 at 92 with C's strip and pyro work.
- R8 stays the orderable revision throughout.

---

## 15. Owner decisions C needs

| ID | Decision |
|---|---|
| O-C1 | Length 86 mm as the design point (88 fallback), accepting the expected routing-texture misses (S4, C2, X6, Y1, X2g) as the price of P1, and the radio-to-terminal distance of 41.6 mm (pass 1's 68 mm rationale withdrawn; R-13 at ≥ 40) |
| O-C2 | J122 turned (rot 180) with mirrored plug numbering (footprint + reviewed `check_actuators` item + silk), or keep rot 90 (+2 mm) |
| O-C3 | Terminal sides swapped against R8 (IGN west, ARM east; A2's handedness): harness and bay orientation |
| O-C4 | Status-pin moves (BUZZ_DRV, PULLPIN; firmware binding) for LS120 and J123 in the aft gap band |
| O-C5 | F10 text: strip "y 0–22.0 of 46 × 86"; RF interface parts inside the strip; limiter stays on B.Cu under U30 |
| O-C6 | Strengthened pyro rules as gates: P-1b, P-3, P-5 (including the ACT_GATE–GND class), P-6, P-7 |
| O-C7 | Mid-span support at the east edge (42, 41.5); VEHICLE row and sled drawing follow |
| O-C8 | J122 mated fit margin 0.50 mm (R8 0.71) and support clearances 3.82 / 3.85 mm accepted, or the J122 rot 90 option |
| O-C9 | Panel-tab plan with JLC (four long-edge tabs; one east window to be cleared near y 55–60) |

---

## 16. Files (all scratch)

Folder: `<scratch>/r9_design/compact/`

**Scripts:**
- `c_spec.py`: the parametric placement specification (`C_L` env var). `c_spec_w.py` is variant W; `c_spec_v2.py` an
  earlier iteration.
- `c_build.py`: builds a placement-only board from the R8 copy and runs the R8 legaliser plus C's rules
  (`C_STRICT=1` for the strengthened pyro pad rules, `--legalise R` for the spiral placer of small parts).
- `c_metrics.py`, `c_pyro.py`, `c_cuts.py`, `c_tabs.py`, `c_render.py`.

**Library and prototype boards:**
- `lib/`: patched copies of the repo's `r8_legalise`, `check_r7`, `check_r8`, `fit_check` and `route_check` (constants
  configurable; never imported from the repo).
- `proto/s86.kicad_pcb` (design point), `proto/s88.kicad_pcb`, `proto/w86.kicad_pcb`, each with `.place.tsv`,
  `_metrics.json` and a `pyro_*.txt` bridge table.
- `proto/r8.kicad_pcb`: a byte copy of R8, `cc044ea0…`.

**Renders:** `proto/c86_strict.svg.png`, `c86_w.svg.png`, `c88_v2.svg.png`, `c84_v1.svg.png`.

**To reproduce** (about 2.5 min each):
```
cd .../compact
C_STRICT=1 C_L=86 <kicad python> -I -B c_build.py --legalise 6 --out proto/s86.kicad_pcb
```
