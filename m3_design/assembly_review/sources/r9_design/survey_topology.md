# R9 survey: global placement topology (every part movable)

Analyst: topology. Input board: R8 `m3_design/assembly_review/m3.kicad_pcb` in the r9 worktree (branch m3-assy-r9 @ 9c8179b,
SHA-256 `cc044ea0…`), read only. Netlist and pin map: the R8 board's pads and `sources/r8_design/pin_table.tsv`.
Scripts, data, renders and logs: `<scratch>/r9_design/topology/`
(no KiCad board was written; 4.9 MB of JSON/PNG).

**Status of every number below: CAD-model estimate on pad centres and courtyards. Nothing is routed.** Lengths are
octilinear, crossings are topological or straight-line proxies, via counts are a calibrated estimate. "Inference" marks
reasoning not checked against a measurement or a maker document (AGENTS §2.5).

## 0. Verdict

1. **Keep the axial order: RF strip (aft) | U1 | J122 | pyro block | J1 battery corner (forward)** — but **mirror the
   pyro block relative to R7/R8**: the IGN terminal J121 with Q124, the gate network and the continuity divider on the
   **west** side, the ARM terminal J124 with the arm-sense divider on the **east** side, the actuator switch at J1.1 and
   the RAW_ACT feed and power corridor down the **east** edge past J124's own RAW pin. This is arrangement **A2**.
   It is the only arrangement found in which **no signal or power lane has to cross the pyro BUS→R134→IGN bridge**
   (the RAW_ACT feed passes the pyro "barrier" through J124.2, which is RAW_ACT itself), and the fixed contract pins
   (U1.3 gate, U1.15 CONT, U1.22–25 servos, U1.33 ARM, U1.34 RAW sense) meet their destinations in their cyclic order:
   contract-pin crossings **10 (R8) → 2**.
2. **Length: 92–96 mm is realistic for that topology (R8: 118).** The courtyard-level placement stays legal down to
   84 mm, but below about 88–90 mm the pyro interior is jammed against J122 and U1 and every routing proxy rises steeply.
3. **U1 at rotation 0, about 5.5 mm nearer the strip than R8 (centre y 39.5–43), with R8's RF pin map H0 unchanged:**
   0 RF-lane crossings in every arrangement tested. Rotations 90/180/270 cost +18…+32 % placement MST and +60…+130 %
   U1 flyline.
4. **J122 turned (plugs side by side along x, tie holes at its x ends) saves about 8 mm**, but only gives straight,
   crossing-free servo lanes if the plug numbering runs west→east like U1.22→25 (a footprint-numbering or
   `check_actuators` contract change); otherwise it is a 6-crossing reversal (R8 has the same reversal, solved with vias).
   Unturned (R8 orientation) costs about 2 mm (A2u, 94 mm).
5. Rejected: **B** (long-edge split; pyro block lands beside the MCU, longest RF/USB lanes, worst MST), **D** (J122
   between the terminals; best U1 crossing counts but the BUS bridge must cross the four servo lanes), and an **RF strip
   forward** (F8/F10 put the SMA jacks on the aft edge; bay-stack coax zone is aft; not modelled).
6. **Owner-level trade-off exposed:** pass-1's rationale "radio ≥ 68 mm from J121/J124" (not a requirement; F10's
   immunity is a bench test) is incompatible with a short board: with the strip aft and the terminals ~19 mm from the
   forward edge, 68 mm needs L ≳ 112 mm. A2 at 92 mm gives 48 mm (A2b 95.5 mm: 52 mm).

## 1. Constraints the model enforces (all arrangements)

| Constraint | Source | How modelled |
|---|---|---|
| SMA jacks on the aft edge, RF strip aft, 23.5 mm deep, only RF parts in it | F8, F10 | R8 strip copied unchanged (strip compaction is the RF analyst's; any saving subtracts directly from L) |
| RF parts (incl. interface R306/R313/R315/R310) ≥ 5 mm from U1 | F10, R8 D17 | legaliser rule |
| J1 entry forward, ≤ 25 mm from both terminal centres | owner R6 grouping (check_r7/r8) | hand-set |
| Terminals' wire entries face a long edge; 14.4 mm tall (x-fit) | F8, P2, fit_check | hand-set; fit margin tracked |
| J122 on the axis (|x−23| ≤ 3, 23.5 mm mated), two tie holes beyond its ends, 4 mm under-board tie channel | P2, P3 | tie holes ≥ 1.7 mm from courtyards; no bottom part in the channel |
| Five M3 supports: one within 6 mm of each corner, one in the middle third; bottom 3.5 / top 3.8 mm clear | P2, fit_check | checked (all arrangements pass) |
| Bottom parts SMD only, ≥ 1.5 mm from through-hole pads (pin tails) | R5 L10 | 2.2 mm from pad centres |
| U1 pin contract: pyro gate/CONT/ARM/RAW pins, servo pins, sentinels, PE0/PE10 NC, IMU_INT1 | check_actuators, pin_table.tsv | fixed in the pin optimiser |
| Pin legality: loader-driven pins, backup-domain pins, reset pulls, EXTI exclusivity, TIM4 capture for TIMEPULSE | R8 connectivity survey §4, pin_table.tsv | the R8 `pinopt` rules, R8's cited choices kept legal |
| Battery-live parts (BAT_IN / ACT_FET_S / ACT_GATE) ≥ 1.0 mm in plan from pyro block parts, any side | R8 D18 / D85 spirit (**Inference**: plan-view rule chosen for the survey) | legaliser rule |
| IMU/baro on the bottom, rotation 0 | R5 L8, axis map | not turned |

Not modelled: the pyro rules A–H inside the block (the block's interior is re-derived by the pyro analyst), GCPW/fence,
pours, and the input-protection-at-J1 rule (F9/R8 D36): the block optimiser does not value BAT_IN proximity (BAT_IN is a
pour net), so some battery-entry parts drift from J1 in the renders; assume them at J1.

## 2. Method

- `dump.py`: R8 pads, courtyards, sides. `blocks.py`: 30 functional blocks (strip chains, MCU core, IMU, USB, SWD,
  camera supply / interface, logic supply, input protection, eFuse, actuator switch, J122 + servo chain, C121, terminals,
  and the pyro interior split into gate, continuity, arm-sense and R134 groups).
- `arrs.py`: each arrangement is a hand-set position for every block (the global topology); `blockopt.py` then tries
  quarter-turns, mirrors (passive-only blocks) and ±4 mm offsets per block to minimise MST + overlap/keep-out penalties
  (removes the bias of moving R8's block interiors rigidly); `model.legalise` spirals every small part to a legal spot.
  Every arrangement reported is courtyard-legal (no overlap, outline, strip, supports, tie holes/channel, pin tails,
  RF 5 mm, battery-live/pyro 1 mm): 0 conflicts, 0 unplaced parts.
- Measures (`model.py`, `pins.py`, `bundles.py`, `final.py`):
  - **S17**: Σ octilinear MST of every net without a pour (R8 pours GND, 3V3, BAT_IN, RAW_ACT, ACT_FET_S).
    Calibration: the script gives **1638.9 mm on R8 as built**, R8's recorded value exactly (1642.4 after the model's
    own legalisation, which is the R8 column below).
  - **Bundle model**: one bundle per pair of blocks joined by signal nets, weighted by net count; length and weighted
    crossings. Insensitive to small-part scatter; this is the cleanest global-topology measure.
  - **U1 annulus model** (R8 connectivity survey's): U1 pins' cyclic order vs their chain ends' angular order (RF lanes
    end at their strip-mouth entries in the lane order the modules force), minimised over the cut; plus a pin optimiser
    over the legal alternatives (greedy + 2500-step swap search, also seeded with R8's map; RF crossings penalised so
    hard that none is accepted). "core" excludes status/fault/sense GPIOs; "contract" counts crossings among the fixed
    pyro/servo pins (servo-vs-servo order pairs excluded, see finding T2).
  - **Vias (estimate)**: MST edges joining a top-only and a bottom-only pad, plus 0.093 × 2 × same-layer straight-line
    crossings left after a greedy F/B assignment; the 0.093 is fitted so R8 gives its actual 73 signal vias. Relative only.
  - **Distances**: courtyard-to-polyline; the 7.7 A feed is J1.1 → Q120 drains → Q120/Q121 sources → Q121 drain →
    J122 RAW row; the servo return J122 GND row → J1.2; "pyro block" = terminals + Q124 + R134 + gate network + dividers.
  - **Cut demand**: largest number of signal MST edges crossing one transverse cut.

## 3. Arrangements

Renders (aft/SMA left, forward right, west edge at the bottom; solid = top, dashed = bottom; red = 7.7 A feed,
orange = servo return, purple = fire path): `topology/arr_<NAME>.svg.png`.

- **R8** (118 mm): reference as built. Pyro block forward across the width (J124 ARM west, J121 IGN east, Q124
  centre-east), J122 mid, U1 at y 45.
- **A** (92 mm): R8's topology compacted: U1 to y 39.5 (courtyard 5.5 mm from FB30; interface resistors at the strip
  mouth), J122 turned and right ahead of U1 with C121 west and C84 east beside it, terminals at L−18.6 at both long
  edges with the pyro core between them, J1 and the actuator switch (bottom) at the forward edge; mid-span support at
  (4, 44.5).
- **A2** (92 mm): A with the pyro block mirrored (J121 IGN + Q124 + gate + continuity west; J124 ARM + arm divider
  east; actuator switch and RAW_ACT feed east). Variants: **A2b** U1 at y 43 (95.5 mm), **A2u** J122 unturned (94 mm),
  **A2r** +8 mm routing room (100 mm), **A2s / A2_86 / A2_84** squeezed to 88 / 86 / 84 mm, **A2k1–3** U1 turned.

```
 A2 (top view, aft at the bottom of this sketch is y = 0)          y
 ┌──────────────────────────────────────────────┐ 92  forward edge
 │ [M3]          J1 (BAT+ … SW)           [M3] │      battery corner: Q120/Q121, TVS, caps under J1 (bottom)
 │ J121 IGN ◄─ Q124 gate CONT ─ R134 ─ BUS ─ J124 ARM│ 68–79  pyro barrier; RAW_ACT feed passes at J124.2 (east)
 │  (entry −x)          ╲  servo lanes   ║RAW  (entry +x)│      power corridor (RAW_PROTECTED, ACT_EN, BAT_FAULT_N) east, outboard
 │ C121    tie ○ [ J122 turned ] ○ tie   C84 (U2/L1/U11 under) │ 50–61
 │ [M3]  IMU/baro(B)      U1 (rot 0, flash + crystal under)   J9 │ 31–48
 │ J3 USB-C  J2      interface R, buzzer, pull-pin          LS120 │ 24–31
 │─ ─ ─ ─ ─ ─ ─ ─ fence y 23.3 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
 │   U30 GNSS (+limiter B)          U31 radio                      │ 0–23.5
 └──────J30───────────────────────────J31────────────────────────────┘ 0
```

- **B** (92 mm): long-edge split. Signals east (U1 at x 30, camera connector east edge, IMU on the axis), power and pyro
  along the west edge (logic supply and hold-up, eFuse, both terminals stacked on the west edge with entries −x, pyro
  core aft of them), J122 on the axis forward, battery corner (J1.1, actuator switch, C121) forward-east, mid-span
  support on the east edge.
- **D** (94 mm; **D90** 90 mm): J122 between the terminals. J1 at the forward edge, J121 IGN west and J124 ARM east
  beside J122, R134 bridging BUS→IGN aft of J122, actuator switch under J1, C84 and C121 beside U1's forward corners.
- **RF forward** (not modelled): violates F8/F10 (jacks on the aft edge) and the VEHICLE stack (coax loop zone aft of
  the board), and puts the strip beside J1's forward-facing wire entry; it would need requirement edits first.

## 4. Results

| | R8 | A | **A2** | A2b | A2u | A2r | A2s | A2_84 | B | D | D90 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Board length L (mm)** | 118 | 92 | **92** | 95.5 | 94 | 100 | 88 | 84 | 92 | 94 | 90 |
| Courtyard share top / bottom | 0.39/0.19 | 0.48/0.27 | 0.48/0.27 | 0.46/0.26 | 0.47/0.26 | 0.44/0.25 | 0.50/0.28 | 0.52/0.29 | 0.48/0.27 | 0.47/0.26 | 0.49/0.27 |
| **S17 placement MST (mm)** | 1642 | 1554 | **1529** | 1560 | 1582 | 1592 | 1638 | 1727 | 1693 | 1595 | 1600 |
| Bundle length (mm) | 1279 | 939 | **945** | 1024 | 952 | 1063 | 866 | 871 | 995 | 904 | 849 |
| **Bundle crossings (weighted)** | 30 | 32 | **27** | 30 | 38 | 27 | 56 | 26 | 36 | 40 | 21 |
| …of which pyro-bridge × servo lanes | 0 | 0 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | **12** | 0¹ |
| Straight MST-edge crossings | 142 | 261 | 260 | 252 | 324 | 252 | 358 | 393 | 384 | 286 | 291 |
| **Signal vias (estimate)** | 73² | 86 | **85** | 86 | 91 | 90 | 104 | 112 | 105 | 97 | 100 |
| Max cut demand (lanes) | 27 | 31 | 31 | 37 | 31 | 29 | 34 | 33 | 30 | 32 | 31 |
| U1 flyline, R8 pin map (mm) | 872 | 663 | **662** | 713 | 682 | 768 | 641 | 640 | 808 | 680 | 652 |
| U1 flyline, optimised GPIOs (mm) | 862 | 583 | **573** | 626 | 595 | 679 | 566 | 563 | 773 | 599 | 571 |
| U1 core crossings (optimised) | 20 | 24 | 18 | 18 | 10 | 17 | 19 | 19 | 18 | 6 | 5 |
| **Contract-pin crossings** | 10 | 8 | **2** | 2 | 1 | 1 | 3 | 3 | 5 | 1 | 0 |
| RF-lane crossings (R8 map H0) | 0 | 0 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| U1 lanes: radio / GNSS / pyro / servo (mm) | 141/80/151/97 | 98/68/82/42 | 98/68/81/42 | 125/75/80/42 | 98/68/91/50 | 98/68/109/72 | 98/68/75/30 | 98/68/70/30 | 129/96/86/109 | 98/68/78/106 | 98/68/61/90 |
| 7.7 A feed polyline (mm) | 64 | 65 | 65 | 65 | 66 | 65 | 65 | 61 | 51 | 72 | 72 |
| Servo GND return J122→J1.2 (mm) | 37 | 25 | 25 | 25 | 30 | 25 | 25 | 21 | 18 | 16 | 16 |
| **7.7 A copper → IMU/baro (mm)** | 16.3 | 7.0 | **7.0** | 7.0 | 6.5 | 7.0 | 7.0 | 7.0 | 17.4 | 19.9 | 16.0 |
| 7.7 A → MCU / crystal / ADC series R | 22/25/21 | 9/12/10 | 9/12/7 | 9/12/7 | 10/13/11 | 17/20/15 | 5/8/6 | 5/8/7 | 22/25/18 | 24/27/22 | 20/23/21 |
| 7.7 A → RF modules | 55 | 37 | 37 | 40 | 38 | 45 | 33 | 33 | 49 | 51 | 47 |
| **Pyro terminals → radio U31** | 68.3 | 48.4 | **48.4** | 51.9 | 50.4 | 56.4 | 44.4 | 40.4 | 45.0 | 50.4 | 46.4 |
| Pyro block → radio U31 | 61 | 33 | 41 | 45 | 43 | 49 | 37 | 30 | 28 | 38 | 32 |
| **Pyro block → MCU / IMU** | 28/32 | 5/14 | **12/12** | 12/12 | 14/14 | 20/12 | 8/12 | 0.7/5 | 2.8/4.6 | 8.5/11 | 3.8/6.4 |
| **RF parts → switchers** (pair) | 10.7 FB31–U8 | 7.8 | **7.8** R313–U8 | 8.1 | 7.1 | 10.1 | 4.2 R313–L3 | 4.2 | 4.8 FB31–C74 | 9.3 | 9.3 |
| RF modules → switchers / MCU | 13.4/15.0 | 11.2/9.5 | 11.2/9.5 | 14.2/13.0 | 10.2/9.5 | 14.2/9.5 | 7.9/9.5 | 7.9/9.5 | 7.5/10.7 | 13.2/9.5 | 13.2/9.5 |
| RF parts → MCU (F10 ≥ 5) | 5.8 | 5.1 | 5.1 | 5.1 | 5.1 | 5.1 | 5.1 | 5.1 | 6.8 | 5.1 | 5.1 |
| IMU off the roll axis (mm) | 13 | 10 | 10 | 10 | 9 | 10 | 10 | 10 | 0 | 7 | 7 |
| Fit margin J122 / C84 (mm) | 0.71/1.37 | 0.49/0.95 | 0.49/0.95 | 0.49/0.95 | 0.71/4.19 | 0.49/3.40 | 0.49/0.95 | 0.49/0.95 | 0.71/0.53 | 0.71/4.19 | 0.71/4.19 |

¹ In D90 the servo bundle (series resistors at y 49–57 → J122 at y 68) runs through R134's own position (23, 57), a
degenerate case the straight-segment test misses. Topologically D always has the crossing (finding T5).
² R8's actual signal-via count on the as-built board (73 vias on 57 non-pour nets); the estimate is fitted to it.
RF parts → switchers 4.2–4.8 mm in A2s/A2_84/B is below F10's 5 mm: those floorplans would need the camera buck moved.
U1 rotation (A2 at 92 mm): S17 1529 / 1797 / 2019 / 1855 mm and optimised U1 flyline 573 / 934 / 1343 / 1053 mm for
0 / 90 / 180 / 270°; RF crossings 0 in all (R8's survey: rotation preserves cyclic order, only length changes).

## 5. Topological findings

**T1. The pin contract fixes the pyro block's handedness.** Around U1 (rot 0) the fixed pins run gate U1.3 → CONT
U1.15 (forward face, west half) → servos U1.22–25 (forward face, east end) → ARM U1.33 → RAW sense U1.34 (east face).
Crossing-free destinations must follow the same order: gate network and continuity divider (Q124, J121 OUT/IGN side)
**west** of J122, J122 in the middle, arm-sense divider (J124 BUS side) and the RAW_ACT sense **east**. R7/R8 have the
opposite handedness (J124 west, Q124/J121 east), which is why R8 needs the ARM/RAW sense dives under U1 and has 10
contract crossings; mirroring the block (A → A2, same geometry otherwise) drops them to 2, and to 0–1 with the CONT
divider placed east of the gate network (A2u, D90).

**T2. Servo order is a numbering question.** U1.22→25 run west→east. With J122 turned and its SIG row facing U1, plug
numbering ascending west→east gives four parallel straight lanes (0 crossings, 0 vias); the footprint's present
numbering gives the full 4-lane reversal (6 crossings). Fix by a numbering-mirrored J122 footprint or a reviewed
`check_actuators` edit (SERVOn ↔ plug n), with the silkscreen legend following. The annulus model cannot judge the
unturned orientation (radially stacked pins); geometrically it is also a reversal unless lanes approach from the west.

**T3. The ARM terminal is the natural gate through the pyro barrier.** J121–R134–J124 spans the board's width; anything
going from the battery corner (forward) to the rest (aft) must pass it. In A/A2 the RAW_ACT feed passes **through
J124.2**, which is RAW_ACT itself, and the servo lanes stay aft of the barrier (J122 aft of it): no pyro-bus crossing.
Rule for implementation: the J1.1 pin (BAT_IN) and the actuator switch on the ARM-terminal side; the RAW_ACT spine and
a **power corridor** (RAW_PROTECTED, ACT_EN, BAT_FAULT_N, LOGIC_SOURCE_ST) outboard of the ARM terminal on that edge;
gate/CONT lanes on the other side of J122, the ARM lane inboard of the corridor. The remaining bundle crossings in A2
(27) are almost all this power-control tree (actsw/eFuse/logic/camera supply) crossing pyro lanes in the block
optimiser's placement — a placement detail the corridor rule removes (Inference).

**T4. RF interface is settled by R8's H0 map.** With U1 at rot 0 directly forward of the strip, H0 gives 0 RF-lane
crossings in every arrangement; the optimiser found no better RF map. U1 can sit 5.5 mm nearer the strip than R8
(courtyard 5.55 mm from FB30; interface resistors at the strip mouth, 5.1 mm from U1), shortening the radio and GNSS
lanes from 141/80 to 98/68 mm. The price is density in y 30–40 (top courtyard share 0.84 with J3, J9, J2, LS120 and
J123 beside U1's aft face); A2b (U1 at y 43, +3.5 mm) relieves it at the cost of +27 mm of radio lanes.

**T5. Why not D or B.** D has the best U1 numbers (core crossings 5–6, contract 0–1, return loop 16 mm, 7.7 A copper
≥ 16 mm from the IMU) but its R134 bridge separates U1 from J122: the four servo-out lanes (and the ARM lane) must cross
BUS/IGN copper on another layer (bundle model: 12), and the pyro core needs its own band, so it is not shorter (90–94).
B puts the pyro block 2.8 mm from the MCU and 4.6 mm from the IMU, has the longest RF/GNSS/USB/SWD lanes and the worst
S17 (+3 % over R8); its one win (IMU on the roll axis, shortest feed) can be had in A2 by moving the IMU, not the
topology.

**T6. Length.** The axial topology's floor is set by the forward stack: J1 (11.3 mm courtyard + 1.9 mm edge) +
terminals and pyro core (≈ 12–15 mm) + J122 band (8 mm turned / 17 mm unturned, with tie holes) + U1 (17.3 mm) + the
strip-mouth band (≈ 7 mm) + strip (23.5). Courtyard-legal down to 84 mm, but at 84–88 mm the pyro block sits 0.7–8 mm
from U1, the RF-to-buck spacing drops under F10's 5 mm unless the camera buck moves, and the estimated vias rise from
85 (92 mm) to 104–112. **Recommended: 92–96 mm** (A2 / A2b), i.e. 22–26 mm shorter than R8 with a lower placement MST
(−7 %), −26 % bundle length, −24…−34 % U1 flyline. Extra length beyond ~96 mm buys routing room but lengthens the
servo/pyro/IMU lanes (A2r at 100 mm: S17 +4 %).

**T7. Density costs vias.** Every compact arrangement has more estimated vias than R8 (85 vs 73, +16 %) and twice the
straight-line crossing proxy; the cut demand peaks rise from 27 to 31 lanes. The shorter board is a P1 gain paid for in
routing room; the R8 plan's caution ("a shorter board would spend the routing room that buys simplicity") holds, but
the topology changes (T1–T3) more than pay it back in crossings that matter (pyro/servo/RF).

**T8. Separation trade-offs for the owner.** At 92 mm: radio module 48 mm from the pyro terminals (pass-1 rationale
68 mm needs L ≳ 112), 7.7 A copper 7 mm from the IMU/baro block and 9 mm from U1 (J122 sits right ahead of U1; keep
the IMU and the 3V3A/ADC parts on U1's aft side, away from J122's RAW row and C121, to recover ≥ 10 mm — Inference),
pyro block 12 mm from U1 and the IMU (coating boundary vs the IMU's 3 mm coating-free zone: fine). The servo return
stays forward of J122, away from U1, crystal and IMU, in every axial variant.

**T9. Pin moves beyond H0 pay only in status GPIOs.** The optimiser cuts about 90 mm of U1 flyline and ~50 annulus
crossings in A2, all from LED, buzzer, pull-pin and fault/VBUS pins (e.g. BUZZ_DRV PC13→PB12, PULLPIN PC14→PD0,
BAT_FAULT_N PA4→PC14, VBUS_SENSE PC8→PD1, USB_FAULT_N PD6→PD2, LED_RED/YEL to PC8/PD8). It also proposes RADIO_NSS
PB11→PB13, BUSY PD8→PD9, RXEN PD9→PD10 for a few mm each; those re-open R8's cited RF rows (pin_table.tsv, F10 text)
and are not recommended. Each move needs a DS12110/RM0433/AN2606 check as R8 did; the status-pin set depends on where
the LEDs, buzzer and pull-pin land (their survey positions are provisional).

## 6. Recommendation for the R9 floorplan

Arrangement **A2 at 92–96 mm**: strip (R8's, or the RF analyst's compacted one) | U1 rot 0 at y ≈ 39.5–43 with R8's H0
RF map | J122 on the axis right ahead of U1, turned with west→east plug numbering, tie holes at its x ends, C121 and C84
flanking it | pyro barrier: J121 IGN (west edge) — Q124, gate network, continuity divider — R134 — arm divider — J124 ARM
(east edge) | J1 at the forward edge with J1.1, the actuator switch, TVS, input caps and U9 at the ARM-terminal (east)
side | RAW_ACT spine and power corridor down the east edge outboard of J124 | IMU/baro and ADC parts aft-west of U1,
away from J122's RAW row. Mid-span support on the west edge (≈ y 44.5); five supports pass P2's geometry at every length
tested.

Owner decisions this raises: (O1) target length vs the 68 mm radio–terminal rationale; (O2) J122 plug numbering
(contract / footprint); (O3) swapping the terminal sides (ARM entry east, igniter entry west; harness and bay
orientation); (O4) any status-GPIO pin moves (firmware binding).

## 7. Limits

- Courtyard-level legality only: no routing, no pours, no pyro rules A–H inside the block, no GCPW/fence, no thermal or
  DC solve. The pyro interior and the RF strip interior are other analysts' re-derivations.
- Block interiors are R8's, turned/mirrored/shifted by a ±4 mm local optimiser; small parts are legalised greedily, so
  S17 and the straight-line crossings carry scatter (squeezed variants most). The bundle and annulus models are the
  more robust comparisons.
- The via estimate is a one-parameter fit to R8; the annulus model cannot judge radially stacked destinations (servo
  order, T2).
- Distances are courtyard-to-polyline; the 7.7 A polyline follows part centres, not drawn copper.
