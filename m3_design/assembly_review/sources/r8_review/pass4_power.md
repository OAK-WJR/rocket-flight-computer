# R8 review pass 4: power, thermal and hot-plug

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54`
(fix pass 3). I checked the hash before and after the review, and it did not change. This was a read-only review: the
only repository file I wrote is this report (`git status --short` equal before and after, apart from it). I measured with
KiCad 10.0.6 pcbnew using scratch scripts in the session scratchpad (`r8p4power/`). Nothing was saved to a board, and no
scratch board copy was made. The one modified tool is a scratch copy of `tools/dc_solve.py` (`r8p4power/dc_dump.py`) that also
prints the current density near the RAW_ACT neck. Every figure below is measured on the board unless it is marked
Inference.

**Result: 0 Critical, 0 Major, 2 Minor (1 worth fixing, records only).**
- **Pass 3 findings:** all five power findings are closed or properly dispositioned (§2).
- **Fix pass 3's copper in this dimension:** no regression (§3).
  - USB_LIMITED's new trunk is at least 0.200 mm from every other net (pours 0.151 mm).
  - R165's smaller BAT_ENABLE via is 0.23 mm from Q120.9. Its barrel is now 0.40 mm from the In2 BAT_IN island (was
    0.45 mm), a fair trade.
  - The moved cover via joins GND on F.Cu, In1 and B.Cu.
  - The In2 BAT_IN island grew by 0.2 mm² round that via. No other power copper moved.
- **7.7 A copper:** reproduced at the build's 0.1 mm grid. RAW_ACT 5.90 mm / 17.6 °C, BAT_IN 6.85 mm / 14.8 °C, ACT_FET_S
  4.80 mm / 22.3 °C, all within D12. The servo GND return is 0.69 mΩ, equal to the evidence line for line. The six
  supply paths I re-solved equal
  `fix3_dc_supply_summary.txt` to the printed digit. All zone fills on the board equal a fresh in-memory refill.
- **The finding worth fixing (records only):**
  - **POWER-01:** fix pass 3 moved the stall test's RAW_ACT reading to the neck's forward part, away from J122's contacts.
  - That part carries the least current in the neck: 0.83 A/mm in F.Cu, against the 1.31 A/mm D12's 17.5 °C assumes and
    1.6 A/mm at the aft end. Two RAW_ACT vias inside the window take 1.26 A down to In2.
  - So a pass there checks D12 less strongly than the text says.
  - J122 is imaged but has no pass line. It is the one part in the 7.7 A path whose rating has no datasheet.

## 1. What was run

| Check | Result |
|---|---|
| `tools/check.sh` (full gate, repository board, KiCad Python) | **exit 0**: DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D audit OK; silkscreen 0; R8 CAD contract OK; route_check r8 0 failing, 3 allowlisted, 0 leftovers, 0 removable (22 bump windows); actuator contract OK; fit check OK |
| Zone fills (every copper zone, refilled in memory with `ZONE_FILLER`, not saved) | 14 zone-layers, **0 differ** from the saved fill in area or island count: the Gerbers carry current fills |
| `DC_GND=0.1 tools/run_dc.sh <board> <scratch> 0.1` | Each output's first line carries `c84f00b8…`. **RAW_ACT** 1.45 mΩ; neck 5.90 mm F.Cu, cut box (20.2–21.8, 80.75–86.25); 17.6 °C ≤ 20; 66 vias, max 0.89 A at (11.3, 85.6), 8 over 0.5 A, none over 1 A; mid-path 100 % F.Cu. **BAT_IN** 0.44 mΩ (pass 3 at this grid: 0.45; the 0.05 mm evidence still 0.45: rounding, as R165's smaller via added 0.2 mm² of pour); 6.85 mm B.Cu, (17.4–20.4, 98.7–104.7); 14.8 °C ≤ 20; 15 vias, max 0.68 A at (21.25, 100.9), 4 over 0.5 A; mid-path 52 % B.Cu / 37 % In2 / 11 % F.Cu. **ACT_FET_S** 0.19 mΩ; 4.80 mm B.Cu, (11.8–14.1, 98.1–104.4); 22.3 °C ≤ 30; no vias. These equal the build gate's figures in `fix3_handoff.md` and match the 0.05 mm evidence (`step9/evidence/fix3_dc_*.txt`: 5.94 / 6.99 / 4.97 mm, 17.5 / 14.5 / 21.4 °C) within D49's grid difference. **GND** (servo return, J122:3,6,9,12 → J1:2, window x 0–46, y 64–118): R = **0.69 mΩ** (5.3 mV, 0.041 W at 7.7 A); mid-path In1 72 %, In2 18 %, B.Cu 9 %, F.Cu 1 %; 112 vias carry current, the largest 0.26 A at (37.35, 100.6) and 0.24 A at (15.0, 107.3), none over 0.5 A; narrowest cut 2.02 mm at J1.2's spokes (24.5–26.6, 109.4–111.4). It equals `step9/evidence/fix3_dc_gnd.txt` line for line. `run_dc.sh` exit 0 |
| Supply paths (`dc_solve.py`, 0.1 mm) | USB_LIMITED U10:6 → U11:7 **52.62 mΩ**; RAW_PROTECTED U9:6 → U11:2 **47.29**, → U7:3,4 **76.34**; BAT_IN J1:1 → U9:5 **17.26**; VLOGIC C84:1 → U2:2,3 **2.60**; 3V3 L1:2 → U1:75 **16.16**. All equal `fix3_dc_supply_summary.txt` |
| RAW_ACT current along the neck's equipotential (scratch `dc_dump.py`, 0.1 mm, V = 0.160 of the drop: straddling-edge currents and marching-squares cut length in 0.5 mm bands of y; a cell-vector profile at ± 0.004 agrees) | §4 POWER-01 |
| In2 map (zone fills) | Five regions, each one island: GND 2686.8 mm², 3V3 1513.8, RAW_ACT west 287.7, RAW_ACT J122 finger 57.9, BAT_IN **229.8** (pass 3: 229.6; R165's via shrank, D108). Outer BAT_IN: B.Cu 217.5, F.Cu 92.9 mm² |
| Panel tabs (fill sampled 0.55 / 1 / 2 / 3 mm in, 26 points along each tab) | Left y 63–68: F.Cu, In1 and B.Cu GND, In2 3V3, as ORDERING §3 now says. The other four tabs are GND on all four layers |
| Fix pass 3's copper (every net's copper and every pour against the changed items) | §3 |
| Bare-pad gaps, battery-live nets (BAT_IN, RAW_ACT, ACT_FET_S, RAW_PROTECTED) to every other net, F.Cu and B.Cu, other parts | Nothing under 0.6 mm except R122.1 (RAW_PROTECTED) to R123.1 (ACT_EN), 0.505 mm (the gate-drive divider's own pair; unchanged) |
| RAW_PROTECTED to every other net, all copper | Pours 0.151 mm; discrete copper 0.171 mm (camera feed via to GND via (42.55, 25.0)) and 0.175 mm (R122's 0.25 mm feed on y 99.75 to R166.1 / R166.2, recorded C12b #11 / #12); unchanged |
| GND pour islands (F.Cu 12, B.Cu 9, In1 1, In2 1), with stitching vias and pads per island | Every island carries GND vias or GND pads; the buck U2's local B.Cu island (41.8 mm², U2.4, C6–C9 side) has 7 vias; B.Cu round J122's GND pins (16 mm²) joins through the four pins only (C17) |
| Thermal spokes on capacitor GND pads (fill intersected with a 0.08–0.20 mm ring round each pad) | §4 POWER-02 |
| Decoupling: nearest same-net capacitor to every IC supply pin | Unchanged from pass 3: U9.6–C82 7.34 mm and U13's caps recorded; U7.5's nearest output cap C73 8.86 mm (not required at the eFuse; U8's input caps C72 / C73 are the load's); every other pin ≤ 3.7 mm |
| Tests | `test_dc_solve` and `test_r8_power`: 10 tests OK |
| Maker documents (no network this pass: the quotations are pass 3's and the records', with their URLs) | Diodes AP63300/AP63301 DS42002 (https://www.diodes.com/datasheet/download/AP63300_AP63301.pdf): input capacitors "as closely across VIN and GND as possible". TI TPS25947 SLVSFC9C §8.4.1 (https://www.ti.com/lit/ds/symlink/tps25947.pdf). AOS AON6403 Rev 2.1 (https://www.aosmd.com/res/datasheets/AON6403.pdf): RθJC 1.5 °C/W max. The J122 rating basis: MARGIN_PRESCRIPTION l. 50 and GEOMETRY_REV_G l. 366 (HX PZ2.54-3×4P, the LCSC approval spec: 3 A per contact, no dimension drawing, no temperature-rise curve) |

## 2. Previous findings in this dimension (pass 3 → board `c84f00b8…`)

| Pass-3 item | Disposition in fix pass 3 | Verified on `c84f00b8…` |
|---|---|---|
| R8P3-POWER-01: the stall-test neck sits against J122, whose contacts heat the same pour | Fixed (records): ORDERING §5, D105 correction, M3_R8 | **Closed for what pass 3 raised.** ORDERING §5 l. 166 reads the neck at y 83.35–86.25. That window starts 3.04 mm from J122.3's pad edge (y 80.31). J122's pin row and the mated plugs are recorded, and an electronic load goes through crimped plugs or is recorded. D105's correction (R8_DECISIONS l. 2145) and M3_R8 "DC solve" say the same. The new window has its own weakness (POWER-01 below) |
| R8P3-POWER-02: U11's IN1 via an undocumented single point | Fixed (records) | **Closed.** M3_R8 l. 120–127 lists (35.25, 60.5) and the 3V3A hop pair (20.9, 62.2) / (15.0, 62.2). The via is unchanged (0.5 / 0.3 mm), and RAW_PROTECTED U9:6 → U11:2 is still 47.29 mΩ |
| R8P3-POWER-03: the ACT_GATE GND-via candidate gains nothing | Closed without copper (D109) | **Properly dispositioned.** D109 gives the 0.151 mm pour figure and the screens. The copper is unchanged |
| R8P3-POWER-04: F9 pad-edge figures treated J1.1 as round | Fixed (records) | **Closed.** M3_R8 l. 40 / 485, D76 (l. 1812), R8_VALIDATION l. 134 and STATUS l. 89 give 1.9–7.8 mm pad edge to pad edge and 3.9–10.6 mm centre to nearest pad centre. `hotplug_feed.py`'s docstring is corrected, including the In2 BAT_IN note. The remaining "2.0–8.4" is the pass-2 history row (R8_VALIDATION l. 222), which is correct as history |
| R8P3-POWER-05: the left middle tab's In2 3V3 unrecorded | Fixed (records) | **Closed.** ORDERING §3's tab paragraph names it (In2 3V3 from 0.5 mm in; the other three layers GND; nibble, never snap). I re-sampled it (§1) |

## 3. Fix pass 3's copper, re-measured in this dimension

- **USB_LIMITED trunk on y 37.3 (D106).** USB_LIMITED is a power net with a 0.45 A limit and a 0.4 mm B.Cu track.
  - Its nearest copper of every other net: CAM_PWR_EN 0.200, ARM1_SENSE_MCU 0.200, RAW_ACT_SENSE 0.200 (lane to the hop
    via (31.25, 55.3)), USB_ILIM 0.200 (U10's own pin), RAW_ACT_SENSE_MCU 0.230 (R172.2), 3V3 / VCAP1 vias 0.25,
    GND pours 0.151 mm.
  - Nothing is under 0.2 mm except the pour. The path resistance is 52.62 mΩ (26 mV at 0.5 A).
- **R165's BAT_ENABLE via (16.6, 104.5), now 0.5 / 0.3 mm (D108).**
  - B.Cu: 0.23 mm to Q120.9 (bare BAT_IN drain pad); 0.301 mm to the BAT_IN pour. F.Cu: 0.383 mm to the BAT_IN pour.
  - In2: the via crosses the In2 BAT_IN island with 0.301 mm between its inner ring and the fill. The ring is flashed on
    In1 and In2, and the via centre is 0.551 mm from the fill. So the hole wall is now 0.40 mm from In2 BAT_IN copper; it
    was 0.45 mm with the 0.6 mm ring.
  - That trade is right. The surface gap to a bare, solder-wetted drain pad, where a bridge or residue is far likelier,
    grew by 0.05 mm. The inner barrel gap is still about twice a typical 0.2 mm hole-to-copper limit (JLC's capability
    figure, not re-checked this pass, no network). Inference: no CAF concern at 8.4 V over 0.40 mm of FR-4.
  - BAT_ENABLE's nearest BAT_IN copper is now U9.1 against U9.5 / C88's lane, 0.200 mm, which is U9's own pitch.
  - The latch threshold (Inference from the divider): R165 470 kΩ / R81 300 kΩ, with U9's EN rising threshold of about
    1.2 V (not re-read this pass). A leak under about 1.8 MΩ from BAT_IN to BAT_ENABLE would hold U9 on with the switch open. ORDERING §5's
    20 power-switch cycles screen that class.
- **Cover via (28.875, 32.875) → (29.125, 32.625) (step 7 regenerated).** It joins GND on F.Cu, In1 and B.Cu (B.Cu
  island 7, 1720 mm², 263 vias). On In2 it sits in the 3V3 region with a 0.251 mm antipad. It is 0.525 mm from
  CAM_PWR_EN's new x 28.25 leg. It is not in any buck loop: U7 (camera eFuse) is 5.1 mm away and U8 11.1 mm (centre to
  centre).
- **CAM_PWR_EN reroute (D107)** is a B.Cu signal. Its centre line passes 2.75 mm from U7's GND via (31.0, 31.3), and it
  does not split the B.Cu GND island U7's GND pad sits in (island 7, as before).
- **DC:** RAW_ACT, BAT_IN, ACT_FET_S and the six supply rows re-solved (§1) equal fix pass 3's evidence.

## 4. Findings

### R8P4-POWER-01 (Minor, worth fixing, records only): the stall test now reads the neck where it carries the least current, and J122 has no pass line

**Requirement.** REQUIREMENTS F4: a thermal-camera stall test of the 7.7 A copper. "J122's 3 A/contact claim remains
manufacturer information without a datasheet." The test is in ORDERING §5 l. 166 and D105 (with its fix-pass-3
correction). It passes "the RAW_ACT neck, F.Cu x 20.25–21.8, y 80.65–86.25 … read on its forward part, y 83.35–86.25" at
a rise of ≤ 17.5 °C (D12's estimate). It records "J122's pin row and the mated plugs as information".

**Board (measured; 0.1 mm solve of the same copper, scratch `dc_dump.py`).** I took the F.Cu current crossing the neck's
own equipotential (V = 0.160 of the drop, the cut the neck figure comes from) at 7.7 A. For each 0.5 mm band of y, the
table gives the straddling-edge current and the marching-squares cut length in that band:

| Part of the cut | y band (mm) | Current (A) | Cut length (mm) | Density (A/mm) |
|---|---|---:|---:|---:|
| Aft end, beside J122.3 / J122.2 | 80.5–82.0 | 0.73, 0.73, 0.65 | 0.30, 0.50, 0.51 | 2.39, 1.46, 1.28 (1.61 over the band) |
| Middle | 82.0–83.5 | 0.59, 0.67, 0.56 | 0.51, 0.52, 0.55 | 1.16, 1.30, 1.01 |
| **ORDERING's window** | **83.5–86.5** | 0.42, 0.37, 0.46, 0.45, 0.52, 0.28 | 0.52, 0.57, 0.55, 0.54, 0.53, 0.30 | 0.81, 0.65, 0.84, 0.84, 0.98, 0.93 (**0.83** over the band) |
| Whole cut, F.Cu | 80.5–86.5 | 6.44 | 5.90 | 1.09 |
| D12's basis | — | 7.7 | 5.90 | **1.31** |

- The cut carries 6.44 A in F.Cu. The other 1.26 A crosses the same level down the two RAW_ACT vias inside the window,
  (20.6, 85.6) and (20.6, 84.2): 0.68 / 0.58 A in `run_dc.sh`'s via list, into the In2 J122 finger. That is why F.Cu in
  the window carries less.
- The window carries 0.83 A/mm. That is 0.63 of the density D12's 17.5 °C assumes (7.7 A over 5.90 mm), and about 0.4
  of its Joule heat per unit area (∝ J²).
- The aft 1.5 mm carries 1.6 A/mm (2.4 in the last 0.3 mm against J122.3's antipad), 1.2–1.8 times D12's basis. It is
  the neck's hottest copper by current, and it is also where J122's contacts add heat.
- So D12's 17.5 °C (the whole neck as a 5.9 mm conductor) is compared with the part of the neck that runs coolest.
  Lateral spreading in 35 µm copper over a 5.9 mm cut evens this out partly but not wholly (Inference).
- J122 itself is in the image but has no criterion. It is the one part in the 7.7 A path whose rating rests on no datasheet
  curve. MARGIN_PRESCRIPTION l. 50 gives its basis: the maker's 3 A per contact, read as a 30 K rise at 3 A, "11.7 K" at
  1.87 A per contact, with "no loaded-contact-count basis". Eight contacts are loaded at once in a 7.7 × 10 mm block.

**Why it matters.**
- No false fail now: pass 3's concern is met.
- But the window reads where the copper is coolest, so a pass there is weak evidence for D12. D12 is already an upper
  bound with no plane credit.
- With 0.63 of D12's density in the window, copper of half the ordered weight would probably still pass there (Inference).
  The test is the only bench check of both the copper and J122's rating, and as written it can confirm neither strongly.

**Fix (ORDERING §5 l. 166, D105's correction, M3_R8 "DC solve"; records only, no copper).**
- Say that the forward window carries about 0.63 of the current density D12's 17.5 °C assumes (0.1 mm solve; two
  RAW_ACT vias in it take 1.26 A down to In2). A pass there bounds the neck's copper only loosely.
- Record the neck's hottest pixel over its whole cut box, and the aft end beside J122, as information.
- Give J122 a line: its hottest pin or housing rise at 7.7 A, steady state, ≤ 30 K (the maker's 3 A rating basis that
  MARGIN uses). Alternatively, state that J122's rise is accepted as recorded information only.
- Nothing else in the procedure needs to change.

### R8P4-POWER-02 (Minor, not worth fixing): twelve 0805 / 1206 capacitor GND pads are on 0.3 mm spokes, while the DRU comment says only 0402 / 0603 pads are

**Record.** `m3.kicad_dru` l. 89–90: "r5_post.pour_relief puts the GND pads of two-pad 0402/0603 parts on thermal spokes
… Other GND SMD pads stay solid." (`r5_post.pour_relief` l. 679: "0402 and 0603 only".)

**Board (measured).** Twelve GND pads larger than 1 mm carry a local THERMAL connection. They join the outer GND pours
through 0.3 mm spokes with a 0.25 mm gap (the DRU's "Small GND pad thermal relief"):

| Pad | Value | Role | Spokes |
|---|---|---|---:|
| C6.2, C7.2 | 22 µF 0805 | U2 (AP63203) input | 4, 4 |
| C8.2, C9.2 | 22 µF 0805 | U2 output | 4, 4 |
| C10.2, C11.2 | 22 µF 0805 | 3V3A | 2, 3 |
| C80.2, C96.2 | 10 µF 50 V 1206 | J1 input (F9 node) | 3, 3 |
| C150.2, C151.2 | 22 µF 0805 | RAW_ACT at J122 | 3, 3 |
| C310.2 | 22 µF 0805 | radio supply | 3 |
| C91.2 | 1 µF 1206 | CAM_5V | 4 |

- `r6_pcb.py` l. 166–168 set these pads when it widened the rule to every R / C GND pad up to 2.0 mm. R7's board has
  the same twelve (checked), so this is a carry-over, not an R8 change. M3_R6 l. 163 calls them "small GND pads". The
  DRU comment was never updated.
- U2's own GND pad U2.4 is solid. 1210 parts (C72, C73, C75, C76, C82; pads 2.3 mm) stay solid.

**Impact (Inference).**
- Each relief adds about 0.25 mm of 0.3 mm strip per spoke, in parallel. Over In2 GND 0.2 mm below, that is about
  0.05 nH and about 0.1 mΩ per pad.
- That is negligible against U2's roughly 2.4 × 1.8 mm input loop and against the 0.1–2 µH harness in F9's hot-plug
  model. Diodes' layout guidance, as pass 3 quotes it from DS42002, asks for Cin "as closely across VIN and GND as
  possible"; C6.1 is 1.79 mm from VIN.
- Adiabatically, a 0.3 mm × 35 µm spoke carries thousands of amps for the hot-plug's microseconds. No pad is starved:
  DRC is 0, and the fewest spokes is 2, at C10.2.

**Fix.** None needed on the board. In a records pass, M3_R8 could name the rule as built (R / C GND pads ≤ 2.0 mm,
R6). The DRU file is SHA-pinned by `check_actuators`, so its comment is left as is.

## 5. Checked, no finding

- **D12 and IPC-2152.**
  - Three necks reproduced at 0.1 mm (§1). The build gate holds them, and the 0.05 mm evidence is bound to the same SHA-256.
  - BAT_IN has no series via. RAW_ACT has one via stage (66 vias, at most 0.89 A). ACT_FET_S is a single B.Cu bridge.
  - REQUIREMENTS F4's widths (≥ 5.28 mm outer, ≥ 5.56 mm inner for 20 °C) follow from `tools/ipc2152.py`.
- **Servo GND return.** 0.69 mΩ, reproduced exactly (§1). The narrowest cut is J1.2's spokes, judged by conduction as
  M3_R8 does. The return runs south from J122 to J1, away from U1 and the sensors. Fix pass 3's step-7 change (one
  cover via at y 32.6) lies outside the solve window.
- **In2 map and islands.**
  - Every In2 region is one island. Areas are as in §1.
  - The U9 feed lane is over In2 GND (the copper is unchanged from pass 3's 510 / 510 samples).
  - The In2 BAT_IN island is bounded at x ≤ 33.5 and y ≤ 112.6. Under the buck stages (x > 35.3), In2 is GND.
- **Supply paths and drops.** At the loads: BAT_IN → U9 38 mV at U9's 2.2 A limit; U9 → U11 24 mV at 0.5 A; U9 → U7
  76 mV at 1 A; USB 26 mV at 0.5 A; VLOGIC 1.3 mV. All are small against the 6.0 V pack floor and the converters'
  headroom.
- **Bucks and hot loops** (copper unchanged by fix pass 3).
  - U2: C6.1 is 1.79 mm of 0.5 mm track from VIN (U2.3). C6.2 is 0.84 mm pad to pad from U2.4 through B.Cu GND
    (C6.2 on 4 spokes, POWER-02). The SW strap is 0.8 × 1.95 mm, and BST runs through C5 beside the pins. The local
    B.Cu GND island (41.8 mm²) has 7 vias to In1.
  - U8: C72 sits on 0.6 mm VIN and GND bars. GND is solid, with a via at (43.41, 37.6).
- **Input protection and F9.** The parts sit 1.9–7.8 mm pad edge to pad edge from J1.1, unchanged. D8.2 is solid in the
  B.Cu GND pour, with GND vias 1.82 mm (30.6, 99.1) and 2.76 mm (35.0, 99.2) away, centre to centre. C80.2 / C96.2 are on 3 spokes (POWER-02), which is immaterial at the harness's 0.1–2 µH.
  `hotplug_feed.py`'s conclusions do not depend on anything fix pass 3 changed.
- **Battery-live clearances.** Bare-pad pairs as in §1. Masked 0.151 mm pour gaps are as on R7. R122's 0.25 mm
  RAW_PROTECTED feed is 0.175 mm from R166's pads (C12b #11 / #12, recorded).
- **Thermal reliefs and via currents.**
  - J1.2 has 4 spokes on F.Cu, In1 and B.Cu, and none on In2 (it sits in the BAT_IN island). By conduction, a 0.5 mm
    spoke at about 1.2 A rises about 0.01 °C (q L² / 8 k A; Inference), so M3_R8's conduction argument stands.
  - The 7.7 A through-hole pads keep their full connections (J1.1, J122's + and GND pins, J124.2).
  - Vias always join zones solid. No power via carries 1 A: RAW_ACT 0.89 A and BAT_IN 0.68 A at most.
- **Panel tabs.** As ORDERING §3 states (§1).
- **Single points.** No power-net via changed in fix pass 3. The list in M3_R8 (now including U11's IN1 via and the 3V3A
  hop) stands. BAT_ENABLE's two vias are signal vias on the enable chain (µA), of the class every signal on a
  lose-the-vehicle chain has; not raised.

## 6. Not verified

- I did not rerun the 0.05 mm qualification grid. The 0.1 mm run reproduces the build gate exactly, and the record's
  0.05 mm evidence is bound to the same SHA-256.
- The other supply rows (3V3 branches but the one in §1, 3V3A, CAM_5V, RAW_ACT → J124 / R177, the other BAT_IN rows) were
  read from `fix3_dc_supply_summary.txt`; their copper is unchanged.
- `hotplug_feed.py` and the plate model were read, not rerun (numpy; nothing they model changed).
- Every temperature, inductance, leakage and CAF statement not marked measured is an Inference. The current-density
  profile is a DC model figure (cell-averaged at a 0.1 mm grid). I did no bench work.
