# R9 clean-sheet plan, Architecture B: power spine

Architect: B (power spine). Input: R8 board `cc044ea0…` (worktree `rocket-flight-computer-r9`, commit `9c8179b`), the three
surveys in this folder (`survey_constraints.md`, `survey_topology.md`, `survey_baseline.md`). The repository was only
read: R8's board SHA-256 is unchanged and no file in the worktree was written. The repo tools left no `__pycache__`
folders (every run used `-B`).

**Status of the numbers.** A KiCad 10.0.6 prototype of the forward half was built, filled under the project's own
`m3.kicad_dru`, and measured with the repo's own tools. It holds every CH1, battery-island, servo-chain and spine part
at its planned spot, the armed-live bars, the RAW branch, the RAW_ACT / BAT_IN / ACT_FET_S copper and GND planes. The
signal lanes and the aft half are not routed. The aft half is the topology survey's model placement and is not
legalised in KiCad. "Measured" means measured on that prototype (board `28802f0c…`; the RAW_ACT solve is on the same
copper). "Model" means the topology survey's courtyard model, and "Inference" means a value that was not measured.

---

## 0. Verdict

1. **The literal B is not viable.** Putting power and pyro on one long edge and signals on the other (the topology
   survey's B) loses, as that survey found. The contract pins fix the gate and CONT pins on U1's forward-west face and
   the ARM and RAW sense pins on its east face. A pyro block on the power edge therefore puts the block next to U1, and
   the lanes cross.
2. **The viable B ("B-spine") is power east, pyro west, signals in the middle.**
   - **East edge:** the whole battery and power chain. J1.1 (BAT+) sits at the east end of J1. The face-to-face
     actuator FETs, U9, the damper and all supplies follow. A short, wide RAW_ACT spine runs on F.Cu, B.Cu and In2 down
     to J122 and C121.
   - **West edge:** the CH1 pyro block as a compact column. J124 (ARM) sits above J121 (IGN), both entering from −x.
     R134 bridges their facing pins with two 8 mm straight bars. Q124 and the gate and continuity network sit directly
     aft, 8–13 mm from U1.3 and U1.15.
   - **Middle:** U1 at rotation 0, 5 mm west of the axis.
   - **Aft:** the RF strip, re-derived but topologically unchanged.
   - **Length:** 98 mm.
3. **What the prototype shows (measured):**
   - **Pyro DRC:** 0 rule violations.
   - **Foreign nets near armed copper:** none within 3 mm on the same layer or in plan view (X2 = X2b = 0; R8 6 / 7),
     and none crossing the CH1 box (X2g = 0; R8 6).
   - **Battery-live copper to armed copper:** 7.6 mm (R8 1.089).
   - **Rule H margin:** 0.225 mm (R8 0.025).
   - **Bare gate pad to armed-live pad:** 2.47 mm (R8 1.03).
   - **7.7 A copper (0.1 mm grid):**

     | Path | R8 (quick grid) | B prototype |
     |---|---|---|
     | BAT_IN | 0.44 mΩ, 6.85 mm, 14.8 °C | 0.18 mΩ, neck 10.25 mm, 9.3 °C |
     | RAW_ACT | 1.45 mΩ, 17.6 °C | 0.58 mΩ, neck 7.87 mm (In2-equivalent), 13.6 °C |
     | ACT_FET_S | 0.19 mΩ, 22.3 °C | 0.27 mΩ, neck 4.94 mm, 21.6 °C (part-limited, as R8) |

   - **First plate mode** (repo `plate_model.py`, jacks only, pinned, D = 5 N·m): 264 Hz with the mid support on the
     east edge, 377 Hz with an interior mid support. R8 is 209 Hz and R6's target is 241 Hz.
4. **Against A2** (the topology survey's recommendation):
   - **Pyro isolation (B wins):** zero foreign nets by construction. A2 runs RAW_PROTECTED, BAT_FAULT_N and ACT_EN in
     a corridor outboard of J124 inside the barrier band.
   - **7.7 A path (B wins):** 43 mm against 65 mm.
   - **Armed copper (B wins):** the bridge is 2 × 8 mm instead of a 26 mm bar across the board, and the spine never
     passes a BUS pad.
   - **Pyro exit lanes (B wins):** about 63 mm in total, against R8's 137.5.
   - **Length (B loses):** about 6 mm longer than A2's 92 mm. A2's 92 mm leaves no room for the 350 mm² battery
     island; its own render scatters those parts. A realistic A2 is about 96–98 mm (Inference).
   - **ARM sense lane (B loses):** it is the one CH1 lane that must leave the west side, and it crosses the spine on
     F.Cu over B.Cu and In2.
   - **Radio distance (B loses):** about 44.5 mm from the radio to the pyro terminals (A2 48).
   - **J122:** both architectures turn it, with the same fit-margin cost (0.50 against R8's 0.71).
5. **Cross-cutting finding (applies to R8, A2 and every R9 option): local clearances override the pyro rules.**
   - **What happens:** in KiCad 10 a pad's local clearance override takes precedence over the custom DRU rules, in the
     zone filler and in DRC alike.
   - **Where on R8:** J124.2 and the four J122 RAW pads carry 0.3 mm local clearances, so pyro rules A (0.5), E (1.0)
     and A2 are not enforced by DRC at those five pads.
   - **Verified on the prototype:** a PYRO1_GATE_N track 0.35 mm from J122.8 passes DRC, and DRC flags rule A once the
     override is removed. When the R8 footprint's net order was swapped, the 0.3 mm override silently set the GND fill
     at 0.30 mm from a BUS pad. DRC passed it; `requalify.pyro_rules` caught it.
   - **R9 fix:** clear every such override (the DRU's "RAW_ACT pins to pours" already gives the 0.3 mm to GND pours),
     add a gate check LC-1, and keep the independent geometry check (`requalify`) as a gate, not only a record.
6. **Second finding: the topology survey's A2 numbers assume mirrored terminals.** The survey built A2 by mirroring R8's
   CH1 block (`mirror_x`), which reverses the terminals' pin order. With the stocked footprints rotated to those
   entries, J124's BUS is aft and RAW forward, and J121's OUT is forward. A2's bridge and contract counts therefore
   assume pad-renumbered terminal footprints. B uses such variants deliberately (section 2.3); A2 would need them too,
   or a re-derivation.

---

## 1. Floorplan (L = 98 mm, 46 mm wide; y = 0 aft edge, x = 0 west edge)

```
 y 98 ┌──────────────────────────────────────────────┐ forward edge
      │[M3 4,94]  J1 (x 20, BAT+ pin x 27.6) ──┐ [M3 42,94]│  battery leads arrive along the EAST wall
      │ R165 R80 (B, at J1.4/J1.3)   D8(B) C96 C80│ Q120(B)  U9(B) net │  BAT_IN island 9.3 C
 y 84 │ J124 ARM ◄entry −x  RAW pin fwd ─RAW branch─┘ │ C89 C95 R166 (F)   │
      │   BUS pin ══8 mm══ R134 ── ARM divider     │ ACT_FET_S bridge   │
 y 74 │ J121 IGN ◄entry −x  IGN pin ══8 mm══ R134   │ Q121(B) drains aft │
      │   OUT pin ║ (D120 R131 R173 R129)          │ RAW_ACT spine F/B/In2 (x 28-45.5) │
 y 63 │ Q124 C128 │ gate net, CONT divider  ○tie   │ C121 (F)  TP120    │
      │ R126 R127 TP122(B)   J122 turned (x 23)  ○tie (mid support) │  In2 RAW round J122
 y 52 │ R150-153 in the four servo lanes, D121(B)  RAW sense divider (B)   │
      │ U4 IMU(B)   U1 rot 0 at (18, 39.5)   │ C84 U11 U2/L1 (logic)       │
 y 31 │ J3 USB-C  J2  LEDs       │ U12/U13  J9 camera  U7 U8 L3 (camera supply) │
      │ ── strip mouth: R306/R313/R315/R310, FB30/FB31 (≥ 5 mm from U1) ─────────────│
 y 22 │═ fence y_f ≈ 22 ══════════════════════════════════════════════════════════════│
      │  limiter (F, west)  U30 GNSS (rot 90)        U31 radio (rot 180)               │
 y 0  └────────J30 (aligned to U30 RF_IN)──────────J31 (aligned to U31 ANT)────────────┘
```

**Why this arrangement is the one the pin contract allows for a spine:**
- U1 at rotation 0 has R8's RF map H0: 0 RF-lane crossings, the survey's T4.
- The gate (U1.3) and CONT (U1.15) pins face forward-west, so Q124 and the CONT divider sit directly forward of them on
  the west.
- The servo pins (U1.22–25) face forward-east, so J122 sits on the axis directly forward of them.
- The RAW sense pin (U1.34) faces east, so its divider sits at the spine's west edge.
- The ARM sense pin (U1.33) faces east, which is the only contract destination on the "wrong" side. Its lane runs east
  of J122 and crosses the spine on F.Cu; the spine dips to B.Cu and In2 there.

**Supports:**
- Corners: (4, 4), (42, 4), (4, 94), (42, 94).
- Mid-span: interior at about (30.5, 50) is recommended. It gives 377 Hz but still has to be legalised against C84 and
  the RAW sense divider (section 5). The fallback is the east edge at (42, 55.5), at 264 Hz.
- J122 tie holes: (16.0, 58.0) and (29.9, 55.0). The east hole sits 3 mm off the RAW row so the spine enters the RAW row
  freely. R8 already has an off-axis tie hole.

---

## 2. Placement and pin changes

### 2.1 Key coordinates (prototype, KiCad mm/deg)

| Part | x | y | rot | side | note |
|---|---|---|---|---|---|
| J1 | 20.00 | 90.40 | 180 | F | entry +y; BAT_IN pin at x 27.62; within 25 mm of both CH1 terminals (14.8 / 23.8 mm) |
| J124 (ARM) | 10.10 | 79.40 | 90 | F | entry −x; pad-renumbered variant: RAW pin forward (81.94), BUS pin aft (76.86) |
| J121 (IGN) | 10.10 | 68.80 | 90 | F | entry −x; pad-renumbered variant: IGN pin forward (71.34), OUT pin aft (66.26) |
| R134 | 18.10 | 74.10 | −90 | F | IGN pad at y 71.53, BUS pad at y 76.67; both bars straight, 1.5 mm, 8.0 mm long |
| Q124 | 10.10 | 60.60 | 180 | F | drain under the OUT bar (J121 OUT pin straight down, 4.7 mm); gate pin west |
| C128 / R173 / R129 / R131 / D120 | 6.0–17.5 | 60.8–63.5 | 90/180 | F | OUT stubs at y 63.03 / 62.57; D120's 3V3 pad 3.9 mm from the nearest OUT pad |
| R130 / R178 / C127 / R128 / C126 / R126 / R127 | 5.0–13.0 | 53.2–56.8 | 90/−90 | F | two parallel rows: CONT pads on one line, GATE pads on another |
| TP122 | 7.60 | 53.60 | 0 | B | GATE via beside the pad (not in it) plus a GND via ≤ 1.5 mm: removes A8 |
| R132 / R175 / R133 / R180 / C129 | 21.6–25.4 | 74.8–77.6 | 0 | F | arm divider on the BUS bar's extension; to be tucked to x ≤ 24 (X2e) |
| J122 | 23.00 | 58.00 | 180 | F | turned (plugs along x), SIG row aft (y 55.46), mirrored numbering (SERVO1 at the west plug) |
| R150–R153 | 19.19 / 21.73 / 24.27 / 26.81 | 52.0 | 90 | F | one 1 k series resistor under each plug column, straight lanes |
| D121, R154–R157 | 19.9–26.1 | 49.6–51.0 | 0 | B | clamp and pull-downs (or all on top to remove 4 vias, section 5) |
| Q121 / Q120 | 32.73 / 34.00 | 78.20 / 87.50 | 180 / 0 | B | face to face along y; Q120's drains on y 88.4 level with J1.1; ACT_FET_S 4.94 mm |
| D8, C80, C96, R167 | 19–36.5 | 85.2–95.6 | — | B | input protection at J1.1 / J1.2 (F9 premise: harness lumped at J1) |
| C89, C95, R166, Q122, R121–R123 | 38–45 | 78–90 | — | F | damper and gate drive, east of the FET pair |
| U9 and network | 38–45.5 | 61–90 | — | B | east column; RAW_PROTECTED runs aft inside the column |
| C121, TP120 | 38.50 / 38.60 | 64.50 / 72.40 | 180 / 0 | F | on the spine |
| R124 / R177 / R125 / R182 / C122 | 33–35 | 49.8–53.6 | — | B | RAW sense divider at the spine's south-west corner, next to U1.34 |
| U1 | 18.00 | 39.50 | 0 | F | 5 mm west of the axis; courtyard 9.35–26.65 × 30.85–48.15 |
| U4 (IMU) | 12.00 | 43.00 | 0 | B | lever arm 11 mm (R8 13); the coat region is 8 mm away |

The aft half (U30, U31, J30, J31, strip mouth, J3, J2, J9, camera and logic supplies, C84) keeps R8's relative
arrangement shifted to the S floorplan. It is not legalised in the prototype; the R9 legaliser places it.

### 2.2 MCU pins

- **Kept:** R8's pin map, including every `check_actuators` contract pin (3, 15, 22–25, 33, 34, 98), the sentinels and
  the RF map H0. No firmware-binding change follows from the floorplan.
- **Optional:** the topology survey's status-pin moves (T9) are not needed for B. U1's west and aft faces keep their R8
  destinations.

### 2.3 Footprint variants (BOM-neutral; reviewed additions to `kilib/rocket.pretty`)

- **`M3_DB128L_2P_BK_SW`:** the DB128L terminal with pads 1 and 2 swapped. It is used for J124 and J121.
  - Same body, same LCSC C430601, same 3D model; the part is symmetric. The netlist (J124.1 BUS, J124.2 RAW, J121.1 OUT,
    J121.2 IGN) is unchanged, so `check_actuators` 1 holds byte for byte.
  - The silkscreen pin legends move with the pads (F8, D92).
  - Any pad-level property must move with its role: the clearance override on the RAW pad is deleted, not moved (LC-1).
- **J122 with mirrored plug numbering** (owner O2, shared with A2): turned at rotation 180, pin 1 at the west end, so
  U1.22→25 meet plugs 1→4 west to east as four straight lanes. Without it, the lanes reverse (R8 solved this with
  vias).

---

## 3. Layer plan

| Layer | Content |
|---|---|
| F.Cu | Signals, all short. The armed bars (BUS, IGN, OUT, 1.5 mm; total armed track 32 mm). The RAW branch to J124's RAW pin (1.5 mm, adiabatic, ≤ 4.1 A for 20 ms). The RAW_ACT spine east of the ARM sense lane, plus a J122 RAW-row bar between the SIG and GND rows. The BAT_IN entry pour. GND pour everywhere else, at rule D's 0.5 mm from armed copper. |
| In1 | Solid GND, no tracks (D20). Under the pyro column it is the only copper besides the terminal barrels. |
| In2 | Four simple power regions with straight edges: RAW_ACT (spine plus the whole J122 area, feeding the RAW pads between the antipads; ≥ 2.5 mm plan from armed copper, measured 3.03), BAT_IN (entry), 3V3 (one region under the MCU domain; Y1's In2 keep-out stays, R5 V1), and GND elsewhere, including the whole pyro column and the RF strip (F10). No signal tracks (S15 = 0; the In2 ARM1_SENSE link disappears). |
| B.Cu | The RAW_ACT spine and J122 RAW bar. The ACT_FET_S bridge. BAT_IN. Bottom parts. A few signal crossings. GND pour. The bare B.Cu pads of the terminals are surrounded by GND at 0.5 mm. |

The 7.7 A path has no series vias. The spine's layers are paralleled by a 2 mm stitching field: 28 vias, the largest barrel current 0.85 A (R8 0.86 A).

---

## 4. Routes that become simple

| Route | R8 | B |
|---|---|---|
| 7.7 A feed J1.1 → Q120 → Q121 → J122 (polyline) | 64 mm, part on In2 | 43 mm; F.Cu + B.Cu + In2 in parallel; BAT_IN 9.3 °C, RAW_ACT 13.6 °C |
| Fire loop on the board | BUS→R134→IGN bar across 26 mm of board width, through the battery corridor | J124.BUS ═8 mm═ R134 ═8 mm═ J121.IGN; OUT 4.7 mm straight down into Q124's drain; armed pads inside a 15 × 16 mm area |
| PYRO1_GATE_N exit | 40 mm, F + B, one via, 0.22 mm beside ARM1_SENSE | ≈ 11 mm, F.Cu, no via, from R127 straight to U1.3 |
| PYRO1_CONT exit | 45 mm on B.Cu, 9.3 mm chain detour | ≈ 13 mm, F.Cu, to R168 at U1.15; stays west of the servo lanes |
| ARM1_SENSE exit | 52 mm with an In2 link | ≈ 40 mm on F.Cu, no via (the spine dips under it) |
| Servo lanes | 97 mm, reversal solved with vias | ≈ 30 mm, four straight fan lanes through R150–R153 (mirrored J122) |
| Power control (RAW_PROTECTED, BAT_ENABLE, BAT_FAULT_N, ACT_EN, BAT_OVLO) | Through and beside the CH1 block (X2 6, X2g 6) | All inside the east column; none within 3 mm of armed copper; X2g 0 |
| GND return J122 → J1.2 | 37 mm | 30 mm (model), under the spine on In1 |

---

## 5. Compromises that remain (with measured causes)

1. **The ARM1_SENSE lane is the only CH1 lane that leaves the west.** It must reach U1.33 on U1's east face.
   - **West route:** crosses the four servo lanes (the model's annulus count: 3 contract crossings). Rejected.
   - **East route (chosen):** crosses the spine on F.Cu while the spine passes underneath on B.Cu and In2. No via on the
     sense lane, but rule A (0.5 mm) is the only spacing to RAW_ACT copper for that stretch.
   - **Mitigation:** the F.Cu spine is split at the crossing, so the lane runs over In1 GND with no F.Cu RAW_ACT beside
     it for more than the crossing width. The P-5 bridge table must list the ARM1_SENSE to RAW_ACT copper pairs (track,
     not pad; the consequence is an over-voltage on an ADC pin, limited by R170 4.7 kΩ).
2. **The J122 RAW mouth.**
   - **The limit:** current enters J122's RAW row only between its SIG and GND rows: 3.08 mm per layer at the row end,
     plus In2 webs between the antipads. The first prototype fed it through In2 only and failed D12 (60 °C at a 2.0 mm
     neck).
   - **The fix:** feed it on all three layers plus an In2 region round the whole header. That gave 15.8 °C with the neck at Q121's drain. With the FET pair at R8's spacing (item 3), the final copper gives 7.87 mm and 13.6 °C, with the neck back at the J122 mouth.
   - **Constraint:** the ARM lane must therefore not pass through the mouth.
3. **ACT_FET_S is limited by the parts.**
   - **The limit:** facing DFN5×6 FETs put their gate pins at opposite ends, so the current passes between them. The
     first prototype gave 4.40 mm and 24.7 °C at a 2.2 mm row pitch.
   - **The fix:** at R8's 3.5 mm spacing it gives 4.94 mm and 21.6 °C at the quick grid (R8 22.3), now limited by Q120's
     own source pins.
4. **J122 turned loses fit margin:** 0.50 mm against R8's 0.71 mm (rotation 180, centre x 23). M-5 needs a recorded
   reason, or J122 unturned (rotation 270, numbering mirrored) for about +6 mm of servo band (L ≈ 104).
5. **Length.** The west column sets L:

   | Item | Depth |
   |---|---|
   | U1 top | 48.2 |
   | CH1 cluster | 11 |
   | J121 + J124 | 2 × 10.23 + 0.4 |
   | J1 band | 13.2 |

   That gives about 98 mm. Shrinking the cluster by 2–3 mm (a tighter 0402 grid, D120 and R131 into the IGN-bar bay)
   could reach about 95–96 mm (Inference).
6. **Pyro to radio:** 44.5 mm (R8 68). It meets the R-13 proposal (≥ 40 mm, Inference); F10's immunity stays a bench
   test.
7. **The Q124 cluster is 4.5 mm from U1's courtyard.** Gate and CONT lanes are short, and the coat region (block
   outline) stays 8 mm from U4's body (P-10 needs ≥ 5). U1 is not on the coat keep-off list, but the block-outline coat
   mask must not reach U1's west pins: brush edge 4 mm from the U1 courtyard (ORDERING §5 text).
8. **X2e (CH1 bounding box) is 719 mm²** (R8 662, no-regression line): the column is tall (32 mm). Moving the arm
   divider to x ≤ 24 brings it to about 650 mm² (Inference). The 500 mm² stretch is not reachable with both terminals
   in one column.
9. **The IMU lever arm is 11 mm** (≤ 13 done; ≤ 5 stretch not met). Under U1's centre (|x − 23| ≈ 5) is possible only
   with the flash moved off U1's bottom, which costs QSPI routing. Not recommended.
10. **Model via estimate: no better than A2.** It is about 92–106 (model, noisy) against R8's 73 and A2's 85. B's own
    forward half needs few vias: the GATE, CONT and ARM lanes need none; the servo lanes need 4 if D121 stays on the
    bottom, 0 with D121 and the pull-downs on top.
11. **Harness rules (bay):** battery leads run along the east wall to J1. The igniter and ARM leads leave west (J121,
    J124) and run forward along the west wall. Record them in ORDERING §7 and the VEHICLE stack row.

---

## 6. Expected metrics against the baseline scorecard

M = measured on the prototype; E = estimate or model; R8 values from `baseline/out/r8` (0.1 mm quick grid where noted).

| Row | R8 | B | R9 done / stretch | Status |
|---|---:|---:|---|---|
| X1 length | 118 | **98** (M) | ≤ 110 / ≤ 104 | stretch met |
| X2 / X2b foreign nets ≤ 3 mm of armed copper | 6 / 7 | **0 / 0** (M, lanes unrouted) | ≤ 2, ≤ 3 / 0 | stretch; gate P-3 holds it through routing |
| X2c nearest foreign copper to armed | 0.70 | 1.39 (an unconnected pad, D120.2); > 3 for nets (M) | ≥ 1.0 / ≥ 3 | met |
| X2d battery-live to bus/IGN/drain | 1.089 | **7.6** plan, any layer (M) | ≥ 2.5 | met |
| X2e CH1 bbox | 662 | 719 (M) → ≈ 650 planned | ≤ 662 / ≤ 500 | at risk until the arm divider is tucked |
| X2g foreign nets through the CH1 box | 6 | **0** (M) | ≤ 1 / 0 | stretch |
| Z1 rule margins | A 0.001, B 0.17, C 0.077, D 0.001, E 0.30, F 0.20, G 0.000, H 0.025 | A, B, E, G, A2: none within search radius; C 0.077, D 0.001 (pour at rule), F 0.89, **H 0.225** (M) | H ≥ 0.2, G ≥ 0.05 stretch | H stretch met; recheck A, B, G after routing |
| Z2 exit lanes CH1 → U1 | 137.5 | ≈ 63 (E: 11 + 13 + 40) | ≤ 137.5 / ≤ 80 | stretch |
| Z5 bare gate pad to bare armed pad | 1.027 | **2.466** (M) | ≥ 1.027 / ≥ 2.0 | stretch |
| Z5b bare actuator gate to other always-live | 0.634 | 0.487 (R120.2 to C120.1, M); co-orienting R120 and C120 fixes it | ≥ 0.634 | fix in placement |
| Z4 / C6 vias in test pads (A8) | 1 | 0 (planned) | ≤ 1 / 0 | stretch |
| Z3 IMU lever arm | 13.0 | 11.0 (M) | ≤ 13 / ≤ 5 | done |
| D_raw RAW_ACT (0.1 mm grid) | 1.45 mΩ, 17.6 °C | **0.58 mΩ, 7.87 mm, 13.6 °C** (M) | ≤ 17.5 °C, ≤ 1.45 mΩ | met |
| D_bat BAT_IN | 0.44 mΩ, 14.8 °C | **0.18 mΩ, 10.25 mm, 9.3 °C** (M) | ≤ 14.5 °C | met |
| D_fet ACT_FET_S | 0.19 mΩ, 22.3 °C | 0.27 mΩ, 4.94 mm, 21.6 °C (M) | ≤ 21.5 °C at 0.05 mm; ≤ 30 hard | ≈ R8; requalify at 0.05 mm |
| Largest via barrel current | 0.86 A | 0.85 A (M) | ≤ 1.0 | met |
| D18 inner RAW/BAT_IN to armed (X9c) | 2.65 | 3.03 (M) | ≥ 2.65 | met |
| D85 battery_pyro | 1.089 | none within 2 mm; 7.6 (M) | ≥ 1.0 | met |
| f1 (plate model, jacks only, pinned, D 5) | 208.7 | **264.5** (east mid) / **376.7** (interior) (M, model) | ≥ 209 / 241 | met |
| F1 worst top fit margin | 0.028 (J9) | 0.37 J9, **0.50 J122** (model) | ≥ 0.028; M-5 per category | J122 category regresses (0.71 → 0.50) |
| Terminal fit | 1.15 | 1.27 (model) | ≥ 1.15 | met |
| Contract-pin crossings (U1 annulus) | 10 | 0 with the ARM lane over the spine (3 if routed west) (E) | — | better than A2 (2) |
| S17 placement MST | 1638.9 | ≈ 1589 (model, hybrid) | ≤ 1638.9 / ≤ 1450 | done |
| Signal vias (model) | 73 | ≈ 92–106 (model) | S4 ≤ 55 layer changes | at risk (all compact floorplans) |
| C1 / C3 routing exceptions | 3 / 3 | 0 / 0 planned: A2/A3 removed by the limiter move (F10 text), A8 by the TP122 via | ≤ 1 / 0 | stretch, conditional on the F10 edit |
| S8 / S9 detour nets | 4 / 4 | ≤ 1 (RADIO_TXEN, keep-out-forced) (E) | ≤ 1 | done |
| S15 In2 signal track | 3.4 | 0 | 0 hard | met |
| P6 In2 perimeter | 1752 | ≈ 800–900 (E: 4 straight-edged regions plus Y1's keep-out) | ≤ 900 | expected |
| P9 / P10 GND-via reach | 4.47 / 9.65 | ≤ 3.5 / ≤ 7 expected (E): no corridor next to the block; vias at 0.5 mm from armed copper round the column | ≤ 3.5 / ≤ 7 | expected |
| X9 F10 separation | 5.94 / 5.075 | aft half unchanged in topology: ≥ 5.1 / ≥ 5.0 (survey A2 values, same strip mouth) (E) | ≥ 5.0 hard | to be re-measured |
| Pyro terminals to U31 | 68.3 | 44.5 (model) | R-13 ≥ 40 (proposal) | met marginally |

The composite indexes are not computed (the prototype is not routed). On the rows above, `index_r9` should land under
73 if routing keeps R8's texture rows (Inference).

---

## 7. Requirements and safety rules at risk, and how B protects them

| Rule | Risk in B | Protection |
|---|---|---|
| AGENTS §2.1 / F8 ARM break; rule E | The spine and RAW branch are RAW_ACT near the BUS pin of J124 | J124's RAW pin points forward and its BUS pin aft, so the RAW branch arrives from the J1 band at y 81.9: 3.0 mm from the BUS pad, against rule E's 1.0. The spine never passes BUS. The local-clearance override is removed from J124.2 (LC-1), so DRC enforces E there (it did not on R8). |
| AGENTS §2.4 gate network; reset-safe gate | Gate parts near U1 and near CONT | The gate network sits within 5 mm of Q124. GATE_N goes straight to U1.3 with no neighbour but GND and its own parts. CONT pads sit on a separate row 1.4 mm from GATE pads, so the P-7 gate guard (≥ 0.5 mm from any net that could put ≥ 0.2 V on the gate in reset) holds by layout. R8's 0.22 mm ARM1_SENSE neighbour is gone. |
| Rules A–H / A2 | Pad-swapped footprints; pours | Prototype pyro DRC is 0; H 0.225, F 0.89, C 0.077, D 0.001 (pour at rule). LC-1 gate; requalify pyro_rules becomes a gate; seeded-fault suite P-4 on every build. |
| D85 / D18 / D19 | Battery-live copper near the block | Battery-live copper is 7.6 mm away (plan); inner RAW_ACT is 3.03 mm away. D19 (GATE_N ≥ 0.5 mm from servo PWM) holds: the GATE_N lane is 8 mm from the servo lanes. |
| Divider fault tolerance (F8) | Layout preconditions | Each half is a separate 0402. No single bridge shorts a whole top (R173/R129 and R132/R175 in line, OUT/BUS pad at the far end). R168, R170 and R172 sit at U1 with ≤ 3 mm *_MCU copper (P-8). |
| P3 coating | Block near U1 and J122 | Coat region = PYRO_BLOCK outline (x 3.4–27.5, y 52.7–84.5): 8 mm from U4, outside J122 and U1. Keep-off list per ORDERING §5. J2 is coated separately at the west edge, 5.7 mm from U4. |
| F9 reverse hot-plug premise | U9 and the input parts move | D8, C80, C96, the damper and R167 stay at J1.1 / J1.2 (≤ 8 mm). U9 is about 15 mm from J1.1 (R8 27 mm); re-run `hotplug_feed.py`. |
| F10 RF | Strip unchanged in topology; U1 5 mm west | U1 stays ≥ 5 mm from RF parts (the strip-mouth resistors set it). Camera buck U8/L3 stays east at ≥ 10 mm from FB31 (model 10.7). Re-derive every strip check (R-1…R-13). |
| P1 / P2 fit, supports, ties | J122 turned; mid-span support moved | J122 margin 0.50 (recorded reason, or unturned at +6 mm). Five supports pass the P2 corner and middle-third geometry; interior mid support legalised by the R9 legaliser (3.8 / 3.5 mm). Tie holes derived from J122 (M-3). |
| OWN J1 grouping (≤ 25 mm) | West terminals, J1 at x 20 | 14.8 mm (J124) and 23.8 mm (J121): met. J1 east of x ≈ 22.7 would break the J121 distance; keep J1 at x ≤ 22.7. |
| M2 clean routing; AGENTS §3 GND via at critical layer changes | ARM lane, servo vias | No via on GATE_N, CONT or ARM1_SENSE. TP122's gate via gets a GND via within 1.5 mm. Servo lanes have 0 vias if D121 goes on top. |
| M1 / M3 BOM | Footprint variants | No new part and no new extended code (52/52 unchanged). |

---

## 8. What must be requalified

- **DC (F4):** the three 7.7 A solves at 0.05 mm (prototype at 0.1 mm: RAW_ACT 13.6 °C, BAT_IN 9.3 °C, ACT_FET_S 21.6 °C), bound to the final SHA. The GND return (DC_GND). The D12 limits stay
  as a build gate at 0.1 mm.
- **Critical references (R6b) and reference audit:** re-run. Y1's In2 keep-out stays (R5 V1), so route the HSE lines off it to recover R8's 1,368 keep-out samples (R6b).
- **Pyro (constraints survey §9.4, all twelve items):**
  - **Already measured on the prototype:** DRC A–H with per-rule margins, the bare and coating distances, the
    neighbours (`pyro_neighbours`: only own nets near armed copper), D85 and D18.
  - **Still to do:**
    - the H liveness fault suite (P-4);
    - the R4-style bridge table (P-5), including the new ARM1_SENSE-over-spine crossing;
    - the divider preconditions;
    - the GATE_N neighbours with their reset gate voltage;
    - the exits;
    - TP122 (A8 removal);
    - terminal wire room for the west-edge entries (same x as R8's J124: 6.3–6.9 mm);
    - the fire-loop copper solve (BUS, IGN and OUT on F.Cu; 32 mm of track);
    - RF to pyro geometry.
- **Fit (P2):** `fit_check` with the derived tie holes and the new support set; the J122 category reason.
- **Vibration:** `plate_model.py` on the final board (gate ≥ 209 Hz, target ≥ 241).
- **RF (constraints survey §8.4):** GCPW profile, launch congruence, return-loss cascade, stitching and fence, module
  keep-outs, chain order, separations, coexistence, limiter thermal on F.Cu (better than R7's B.Cu 0.2 mm), the
  ≤ 0.2 Ω GNSS supply, jack mechanics. The 2-D field solver is rebuilt as `tools/gcpw_solve.py` (pass2_rf §7 method).
- **Bench assumptions, unchanged in kind:**
  - the 7.7 A thermal stall test (new neck locations: the J122 RAW mouth, and Q120's source pins for ACT_FET_S);
  - the pyro static, leakage and dynamic gates;
  - RF immunity at +22 dBm, with the terminals 44.5 mm from the radio;
  - coexistence S21;
  - the NRST ≥ 1 MΩ leakage gate;
  - the hot-plug premise, re-run with U9 at 15 mm;
  - the plug-out cold test;
  - a tap check on the new supports.
- **Records:**
  - F10 text: strip coordinates and the limiter's place;
  - P1 (98 mm), P2 (f1), F4 (solves), the new M2 list;
  - ORDERING §3–§7: tabs (both long edges keep 5 mm windows near the ends), mark, probe points, coat region, sled
    holes, harness sides;
  - the parent VEHICLE stack row: 98 mm, the hole coordinates, a bay slack gain of about 20 mm.
- **Firmware binding:** a new note. No pin change. The J122 plug legend and the terminal pin legends follow the
  footprint variants.

---

## 9. Reproducible implementation (fresh scripted build on R8's framework)

`m3_design/r9_build.sh` follows R8's stage, gate and fill-digest discipline (deterministic, fixed KIID seed, no
autorouter). It drops R8's rigid digests.

1. **`r9_sch.py`.** Start from R8's sheets and netlist (no net change). Assign the J121 and J124 footprints to
   `M3_DB128L_2P_BK_SW` and J122 to the mirrored-numbering header. Regenerate `schematic.net.xml`, check parity, and
   clear every pad and footprint local clearance (LC-1).
2. **`r9_pcb.py`.** Load R8's footprints, delete all copper and zones. Draw the outline and holes from `r9_outline.tsv`
   (L, supports, tie holes derived from J122). Place from `r9_place.tsv`: the forward half from this prototype's
   `build_proto.py` table, the aft half from the legaliser seed.
3. **`r9_legalise.py`.** R8's legaliser with rule-based keep-clears:
   - courtyards, pin tails 1.5 mm, supports 3.5 / 3.8 mm, the tie channel, TP122 2.0 mm, R5 L10;
   - P-10 coat keep-off;
   - F10 5 mm;
   - the battery-live to CH1 plan distance ≥ 2.5 mm;
   - the J1 25 mm grouping.

   The build stops on any violation.
4. **`r9_place_check.py`.** DRC with parity, fit, tab windows, placement MST, `check_actuators`, P-1 (derived
   PYRO_BLOCK area), M-3, M-4.
5. **`r9_power.py`.** Parametric polygons for the spine, the J122 RAW bar and the In2 RAW region round J122, BAT_IN, the
   ACT_FET_S bridge, the In2 map (RAW_ACT, BAT_IN, 3V3, GND), the RAW branch, the armed bars, and the stitching fields.
   Native fill inside the project, so the DRU applies.
6. **`r9_power_check.py`.** `tools/run_dc.sh` at 0.1 mm with the D12 limits (moved early: the spine is placement-bound),
   D18, D85, LC-1, P-2, P-3.
7. **`r9_route_<family>.py`**, in order:
   - `rf`: straight jack lines, limiter escapes on F.Cu;
   - `qspi_hse`;
   - `pyro`: GATE_N, CONT and the TP122 via plus its GND via;
   - `arm_lane`: ARM1_SENSE over the split spine;
   - `servo`;
   - `usb_swd`, `imu`, `camera`, `status`, `links`.

   Each family has a `r9_route_check.py` gate: budget, D19, P-7, route_check profile r9.
8. **`r9_ground.py`.** Fence on a recorded y_f, the 2.5 mm RF stitching rule, a 4 mm GND grid, vias round the pyro
   column at rule D + 0.1, reach and island rules. Then `r9_ground_check.py`.
9. **`r9_post.py`.** Silkscreen: R8's post-process, with the legends for the swapped pins and the plug numbering.
10. **`tools/check_r9.py`.** Replaces `check_r8`'s twelve digests with the rule contracts:
    - P-1…P-11 (P-1b, P-3, P-7 pending owner sign-off);
    - R-1…R-13;
    - M-2…M-7;
    - LC-1 (no local clearance override on any pad, footprint or zone touching a pyro, RAW, gate, sense, BAT_IN or
      ACT_* net);
    - requalify `pyro_rules` as a gate (independent of DRC);
    - P-4 (seeded H-fault suite) on every run.

    The route_check r9 profile starts with an empty allowlist.

Prototype assets to seed it (scratch):
- `spine/proto/build_proto.py`: placement table and power polygons;
- `spine/topo/arrs_spine.py` and `hybrid.py`: model metrics;
- `spine/fit_hybrid.py`: plate-model input.

---

## 10. CH1 block qualification for this geometry (what the prototype already shows)

- **Purity:** inside the CH1 hull, only CH1 nets, GND, RAW_ACT (J124's RAW pin and branch) and 3V3 (D120, 3.9 mm
  from the nearest OUT pad). In1 and In2 under the column are GND only. P-3 passes as proposed.
- **Bridge candidates (pads under 1.5 mm):** R131.1/.2 (OUT to COLD, own part), R132 and R173 own halves (tolerated
  classes), Q124.5 to Q124.4 (own FET). The nearest non-own live-to-sense pair is Q124.5 to R129.2 at 1.225 mm. There
  is no gate pad within 2.4 mm of any armed pad.
- **Gate in reset:** PYRO1_GATE copper's nearest non-GND, non-own neighbour is beyond the search radius (≥ 1.4 mm). The
  P-7 table is expected to be empty of driven nets (to be confirmed after routing).
- **TP122:** on B.Cu at (7.6, 53.6), 1.0 mm from GND fill. Its GATE via goes beside the pad with a GND via at ≤ 1.5 mm
  (AGENTS §3). No via in the pad, so the M2 exception and A8 are gone.

---

## 11. RF strip re-optimisation (architecture-independent; B adopts it)

1. **Keep the topology.** U30 at rotation 90 (RF side facing J30, UART side facing U1) and U31 at rotation 180 (ANT
   facing J31, SPI facing U1's aft-east corner). This gives 0 RF-lane crossings with map H0, as the survey's T4 found.
2. **Align each jack with its module's RF pin.** J30 at U30.RF_IN.x and J31 at U31.ANT.x make straight lines with 0
   bends, at least as short as R7's 5.76 / 4.76 mm (R-6). The jacks stay ≥ 12 mm apart (≈ 18.7) and the RF lines
   ≥ 15 mm apart (R-11).
3. **Move the antenna-bias limiter** (Q30–Q32, R300–R303, C304) off "B.Cu under U30" onto F.Cu west of U30, outside
   U30_KEEPOUT. Shift U30 and J30 east by about 3 mm to open x 0.5–7. GNSS_LNA_EN and GNSS_VCC_RF then escape on F.Cu
   without vias near the paste: allowlist A2 and A3 and two S8/S9 nets disappear. This needs the F10 text edit (owner).
   Limiter thermal gets ≥ 1 mm F.Cu copper instead of R7's 0.2 mm on B.Cu.
4. **Stitching** ≤ 2.5 mm on both sides of both lines (R-7, no named ceilings). Fence on a recorded y_f ≈ 22.0.
5. **Depth** ≤ 21.4 mm (no regression). The TXEN loop round U31 stays (maker-forced), routed outside U31_KEEPOUT on
   the VCC/NRST side.
6. **Requalify** with the rebuilt 2-D solver and the JLC engine for any section outside the qualified W 0.30 / gap 0.25
   cross-section.

---

## 12. Effort

| Stage | Work | Estimate |
|---|---|---|
| Owner decisions | Section 13 | 1 exchange |
| Footprint variants and LC-1 | J121/J124 pad-swapped terminal, J122 numbering, override clean-up, review | 0.5 session |
| `check_r9` rule contracts and tools | P-1…P-11, R-1…R-13, M-2…M-7, LC-1, P-4 fault suite, P-5 bridge table, gcpw_solve | 3–4 sessions (the largest new piece; shared with any R9 architecture) |
| Placement and legaliser | Forward half from the prototype; aft half legalised; interior support | 1–2 sessions |
| Power copper | Spine, J122 feed, In2 map; DC gate | 1 session (prototyped) |
| Routing families | 10 families; the ARM lane and RF strip are new | 3–4 sessions |
| Ground, post, gate | Fence, grid, silkscreen | 1–2 sessions |
| Requalification | 0.05 mm DC, pyro §9.4, RF §8.4, fit, vibration, records | 2–3 sessions |
| Review loop | Two consecutive passes with no Critical or Major | 2–4 passes |

That is about 13–19 agent sessions; R8's partial re-place took 10 steps plus 4 fix passes. B's forward half is
de-risked by this prototype. The open risks are the aft-half legalisation at 98 mm (model share 0.47 top, near R6's
proven 0.449; Inference) and the via count.

---

## 13. Owner decisions B needs

1. **Terminal arrangement:** both CH1 terminals on the west edge (J124 forward, J121 aft, both entering −x), with the
   pad-renumbered DB128L footprint variant. Harness: igniter and ARM leads along the west wall, battery leads along the
   east wall to J1.
2. **J122:** turned with mirrored plug numbering (fit margin 0.50 against 0.71), or unturned at about +6 mm length.
3. **Mid-span support:** interior at about (30.5, 50) (377 Hz) or east edge (42, 55.5) (264 Hz). This updates the sled
   and the VEHICLE row.
4. **Length target:** 98 mm as prototyped, or about 95–96 with a tighter cluster (Inference).
5. **F10 text:** strip coordinates; the limiter may leave B.Cu-under-U30 (removes A2 and A3).
6. **Strengthened pyro rules** P-1b, P-3, P-7, plus LC-1. All four only tighten.
7. **R8 record note** on the local-clearance override at J124.2 and J122's RAW pads, even if R8 is never re-ordered:
   DRC did not enforce rules A, E and A2 there.

---

## Files (scratch, `…/r9_design/spine/`)

- **`proto/`** (KiCad prototype):
  - `build_proto.py`: the build, L parameter;
  - `m3.kicad_pcb`: SHA-256 `28802f0c…`;
  - `m3.kicad_dru` / `m3.kicad_pro`: copies of R8's;
  - `drc.json`;
  - `requalify.json`: repo `step9/requalify.py`;
  - `x_metrics.json`: baseline `r9_extra_metrics.py`;
  - `dc/{raw,bat,fet}.txt`: repo `tools/dc_solve.py --necks`, 0.1 mm;
  - `safety.py`: `check_r8.battery_pyro` and `inner_power_pyro`;
  - `f_cu_fwd.svg.png`, `b_cu_fwd.svg.png`, `in2_fwd.svg.png`: forward-half layer images.
- **`topo/`** (topology model copy):
  - `arrs_spine.py`: arrangements S, S92, S100, S98;
  - `hybrid.py`: S98 aft half with the prototype's forward half;
  - `out_S98.json`, `final_S98.json`, `arr_S98.svg.png`.
- **Vibration:** `fit_hybrid.py`, `fit_{east,west,interior,eastmid62}.json`, `plate_*.json` (repo `plate_model.py`,
  run with the cfd venv's numpy; R8 calibration 208.7 Hz reproduced).
