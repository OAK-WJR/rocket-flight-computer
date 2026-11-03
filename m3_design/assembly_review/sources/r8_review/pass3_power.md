# R8 review pass 3: power, thermal and hot-plug

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18`
(fix pass 2). I checked the hash before and after the review, and it did not change. This was a read-only review: the
only repository file I wrote is this report (`git status --short` equal before and after, apart from it). I measured with
KiCad 10.0.6 pcbnew using scratch scripts in the session scratchpad (`p3power/`); nothing was saved to a board, and no
scratch board copy was made. Every figure below is measured on the board unless it is marked Inference.

**Result: 0 Critical, 0 Major, 5 Minor (2 worth fixing).**
- **Pass 2 findings:** all five power findings are closed or properly dispositioned (§2). POWER-02's In2 BAT_IN trim is
  on the board: the right forward tab, the east edge and the M3 hole (42, 114.4) now have GND on all four layers, and the
  U9 feed lane runs over In2 GND for its whole length (510 of 510 samples).
- **7.7 A copper:** reproduced at the build's 0.1 mm grid (RAW_ACT 5.90 mm / 17.6 °C, BAT_IN 6.85 mm / 14.8 °C,
  ACT_FET_S 4.80 mm / 22.3 °C); all within D12. The servo GND return reproduces fix pass 2's figure (§1).
- **Regressions from fix pass 2:** none in the power copper. The new U9.8 GND via (D102) closes C88's bypass loop
  locally; the V_IN1 ring change (D98) keeps the same 0.3 mm barrel; R81's move (D100) leaves the feed lane clean.
- **The two findings worth fixing (both records only):**
  - **POWER-01:** ORDERING §5's stall test now judges the RAW_ACT neck against D12's 17.5 °C because it lies "at least
    12 mm from either FET", but the neck sits 0.34 mm from J122.3 and 0.86 mm from J122.2, whose mated contacts dissipate
    in the neck's own pour. The test can still false-fail for the reason pass 2 raised, with a different heat source.
  - **POWER-02:** U11's IN1 via (35.25, 60.5), the only link from the RAW_PROTECTED trunk to the logic mux, is a
    single-via series point on the battery-fed logic supply, and it is missing from M3_R8's list of accepted single
    points (MARGIN R15: no undocumented single point).
- **Fix pass 2's pass-3 candidate (ACT_GATE's 0.180 mm GND via):** the proposed `make_ground` change would not move the
  nearest GND copper. The B.Cu GND pour already stands 0.151 mm from the same bare ACT_GATE pads, as on R7, and both are
  under solder mask (POWER-03). I recommend closing it without a copper change.

## 1. What was run

| Check | Result |
|---|---|
| `tools/check.sh` (full gate, repository board, KiCad Python) | **exit 0**: DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D audit OK; silkscreen 0; R8 CAD contract OK; route_check r8 0 failing, 3 allowlisted, 0 leftovers; actuator contract OK; fit check OK |
| `DC_GND=0.1 tools/run_dc.sh <board> <scratch> 0.1` | Each output's first line carries `990c8040…`. **RAW_ACT** 1.45 mΩ; neck 5.90 mm F.Cu, cut box (20.2–21.8, 80.75–86.25); 17.6 °C ≤ 20; 66 vias, max 0.89 A at (11.3, 85.6), 8 over 0.5 A, none over 1 A; mid-path 100 % F.Cu. **BAT_IN** 0.45 mΩ; 6.85 mm B.Cu, cut box (17.4–20.5, 98.7–104.7); 14.8 °C ≤ 20; 15 vias, max 0.68 A at (21.25, 100.9), 4 over 0.5 A; mid-path 52 % B.Cu / 37 % In2 / 11 % F.Cu. **ACT_FET_S** 0.19 mΩ; 4.80 mm B.Cu, cut box (11.8–14.1, 98.1–104.4); 22.3 °C ≤ 30; no vias. These equal the build gate's figures in `fix2_handoff.md` exactly, and match the record's 0.05 mm evidence (`step9/evidence/fix2_dc_*.txt`: 5.94 / 6.99 / 4.97 mm, 17.5 / 14.5 / 21.4 °C, 0.86 / 0.65 A) within D49's grid difference |
| Servo GND return (same run, DC_GND 0.1 mm, window x 0–46, y 64–118) | Reproduces `step9/evidence/fix2_dc_gnd.txt` exactly: R = **0.69 mΩ** (5.3 mV, 0.041 W at 7.7 A); mid-path In1 72 %, In2 18 %, B.Cu 9 %, F.Cu 1 %; 112 vias carry current, the largest 0.26 A at (37.35, 100.6) and 0.24 A at (15.0, 107.3), none over 0.5 A; narrowest cut 2.02 mm at J1.2's spokes (cut box 24.5–26.6, 109.4–111.4), judged by conduction as the record says. About 40 min of CPU at the machine's load |
| Supply paths, re-run where fix pass 2 touched them (`dc_solve.py`, 0.1 mm) | RAW_PROTECTED U9:6 → U11:2 **47.29 mΩ** (through the D98 via; equal to `fix2_dc_supply_summary.txt`); BAT_IN J1:1 → U9:5 **17.26 mΩ** (equal), 38 mV at U9's 2.2 A limit; the feed's narrowest cut beyond the 0.5 mm lane itself is 1.04 mm at the lane's start (10.5 °C at 2.2 A) |
| In2 map (fill sampled on a 0.5 mm raster, y 20–118; zone fills and islands listed) | Five regions, each one island: GND 2686.8 mm² (was 2396), 3V3 1513.8, RAW_ACT west 287.7, RAW_ACT J122 finger 57.9, BAT_IN **229.6** (was 505.6). In2 BAT_IN spans x 12.4–33.5, y 100.3–112.6 only |
| Edges, tabs and holes after D97 (fill sampled 0.55–3 mm in from each tab; east edge at seven y from 100.5 to 115; rings of 2.2–3.5 mm round the holes) | East edge y 100.5–115: GND on all four layers at 0.51 mm. Tabs: left forward, right aft, right middle and right forward are GND on all four layers. **Left y 63–68: In2 is 3V3 to 0.55 mm from the edge** (POWER-05). Holes: (42, 114.4) and (4, 114.4) GND on four layers; (4, 64) has In2 3V3 (recorded in ORDERING §7) |
| U9 feed lane over In2 (x 41.0 / 41.25 / 41.5, y 85.5–102.4, 0.1 mm steps) | 510 / 510 samples on In2 GND: no BAT_IN, 3V3 or antipad under it |
| Pour contact at the 7.7 A through-hole pads (rings) | J1.1 solid BAT_IN on F / In2 / B. J1.2: 4 spokes on F, In1 and B; none on In2 (J1.2 lies in the BAT_IN island). J122's + pins and J124.2 solid RAW_ACT on F / In2 / B. J122's GND pins solid on all four layers (C17) |
| Bare-pad gaps, battery-live nets (BAT_IN, RAW_ACT, ACT_FET_S, RAW_PROTECTED) to GND and to BAT_ENABLE, ACT_GATE, ACT_DRV, ACT_EN, other parts only | Nothing under 0.6 mm except R122.1 (RAW_PROTECTED) to R123.1 (ACT_EN) 0.505 mm (the gate-drive divider's own pair) |
| ACT_GATE / ACT_DRV to GND (every copper item, every layer), and R7 for comparison | §3 POWER-03 |
| Single-via series links on every power net (each via removed in memory and the ratsnest recomputed; 123 vias on 15 nets) | §3 POWER-02 |
| Input-protection distances to J1.1 (true pad shapes) | §3 POWER-04 |
| Decoupling: nearest same-net capacitor to every IC power pin (all U*) | Unchanged from pass 2 (C83 at U10.1 1.61 mm centre to centre; U9.6–C82 7.34 mm and U13 recorded) |
| Tests | `test_dc_solve` (3) and `test_r8_power` (7): OK |
| Maker documents | Diodes AP63300/AP63301 DS42002 (https://www.diodes.com/datasheet/download/AP63300_AP63301.pdf): θJA 89 °C/W on a single-layer 2 oz board (Note 6), operating TJ +125 °C, "Place the input capacitors as closely across VIN and GND as possible", "use at least the 2nd and 3rd layers as GND" (Layout 2, 6). TI TPS25947 SLVSFC9C §8.4.1 (https://www.ti.com/lit/ds/symlink/tps25947.pdf): "The GND terminal must be tied to the PCB ground plane at the terminal of the IC with the shortest possible trace". AOS AON6403 Rev 2.1 (https://www.aosmd.com/res/datasheets/AON6403.pdf): RθJC 1.5 °C/W max, RθJA 40 / 55 °C/W (1 in², 2 oz) |

## 2. Previous findings in this dimension (pass 2 → board `990c8040…`)

| Pass-2 item | Disposition in fix pass 2 | Verified on `990c8040…` |
|---|---|---|
| R8P2-POWER-01: the stall test could not judge D12 | Fixed: ORDERING §5 rewritten, D105, F4 / M3_R8 / MARGIN | **Closed for what pass 2 raised.** The duration is now steady state (or a stated flight stall); BAT_IN / ACT_FET_S are information only, the FET tabs are judged against R1 (100 − 70 − 0.34 × 1.5 ≈ 29 °C); J1.2 from the bottom; 21.4 °C. The RAW_ACT neck is 12.78 mm from Q120's courtyard and 16.48 mm from Q121's, as the text says. A residual of the same kind remains: J122 sits against that neck (POWER-01) |
| R8P2-POWER-02: dead-end In2 BAT_IN at the east / forward edges, the right tab and hole (42, 114.4) | Fixed (D97): `IN2_BAT_IN` x 12.4–33.5, y 100.3–112.6 | **Closed.** In2 BAT_IN 229.6 mm², one island. East edge, right forward tab and hole (42, 114.4): GND on four layers (§1). J1.1's In2 annulus whole (ring at 1.45 / 1.7 mm all BAT_IN). D18 2.65 mm (check_r8 OK). BAT_IN neck 6.85 mm (0.1 mm), R 0.45 mΩ, In2 37 % of mid-path. The U9 lane is over In2 GND throughout |
| R8P2-POWER-03: U13's capacitors 5.6 / 6.75 mm of track | Accepted, recorded (M3_R8 Power) | **Properly dispositioned.** The line is in M3_R8 l. 108; the copper is unchanged |
| R8P2-POWER-04: the build's DC gate has no seeded test | Accepted, recorded (R8_VALIDATION open items) | **Properly dispositioned.** `run_dc.sh` and `dc_solve.py` are unchanged by fix pass 2, so pass 2's hand-seeded fail path (NECK FAIL, exit 1) still applies; my run reproduced the gate's figures |
| R8P2-POWER-05: record slips (a) via count, (b) "pad edge" that was centre to centre, (c) a copied fold reason | Fixed (records) | **(a), (c) closed** (MARGIN P1-9 "4 over 0.5 A"; C14 row (34.4, 69.65) names the In2 3V3 feed). **(b) closed as labelled**, but the pad-edge figures it added came from pass 2's own measurement, which treated J1.1 as round; J1.1 is a 2.6 mm square pad, so they are 0.06–0.51 mm high (POWER-04) |

**Fix pass 2's power-relevant copper, re-measured:**
- **In2 BAT_IN trim (D97):** above.
- **U9.8 GND via (D102), (44.65, 86.775):** U9.8's B.Cu GND copper reaches it through the channel between BAT_DVDT
  (y 84.675) and BAT_ILIM (y 85.725), about 0.55 mm wide after clearances. C88's IN-to-GND bypass loop now closes through
  C88.2's via (42.9, 87.6), 1.93 mm of In1 and this via, instead of about 12 mm of In1 (TI §8.4.1 met). The via is
  0.175 mm from R122's 0.25 mm RAW_PROTECTED gate-drive feed on F.Cu (x 45.2). That is DRC-legal and tented; a short
  would load RAW_PROTECTED into U9's 2.2 A limit, and the net pair is already in C12 at 0.171 mm.
- **V_IN1 (D98):** now 0.5 / 0.3 mm, so the barrel is unchanged. RAW_PROTECTED U9:6 → U11:2 is still 47.29 mΩ. It is a
  single-via series point (POWER-02).
- **R81 (D100):** the BAT_IN feed lane now passes no part. Its smallest gaps are 0.151 mm to the B.Cu GND pour (masked)
  and 0.20 mm to the GND via (42.0, 100.6). No bare-pad pair with BAT_IN lies under 0.6 mm.

## 3. Findings

### R8P3-POWER-01 (Minor, worth fixing): the stall test's RAW_ACT neck sits against J122, whose contacts heat the same pour

**Requirement.** REQUIREMENTS F4 asks for a thermal-camera stall test of the 7.7 A copper. D105 and ORDERING §5 l. 166
now pass "the RAW_ACT neck, F.Cu x 20.25–21.8, y 80.65–86.25 (top face, at least 12 mm from either FET)" at "rise
≤ 17.5 °C (D12's estimate, an upper bound)". The reason for picking this neck, in D105 and M3_R8 "DC solve", is that no
heat source other than the copper dominates it.

**Board (measured).**
- The neck's cut box overlaps J122's courtyard (F.CrtYd y 70.58–80.83) by 0.18 mm.
- It is 0.34 mm from J122.3 (GND, (20.46, 79.51)) and 0.86 mm from J122.2 (RAW_ACT, (23.0, 79.51)).
- J122.2 / 5 / 8 / 11 join the RAW_ACT F.Cu pour solid, the same pour the neck is cut from. J122.3 / 6 / 9 / 12 join the
  GND pours solid on four layers (C17).

**Why it matters (Inference).**
- In the test, each servo's + and GND current passes through a mated crimp contact and a header post: 8 contacts at
  about 1.92 A each.
- J122's contact resistance has no datasheet (F4: "J122's 3 A/contact claim remains manufacturer information").
  Typical crimp contacts of 10–30 mΩ would give about 37–110 mW each, about 0.3–0.9 W in J122's 7.7 × 10 mm block. That
  is the same order as one AON6403's 0.34 W, the heat source D105 moved the pass criterion away from.
- That heat enters the neck's own pour through J122.2's solid connection, 0.86 mm away. So the neck's reading carries a
  gradient towards J122 that D12's copper-only estimate does not contain.
- The copper itself probably rises well under 17.5 °C (about half with plane credit, M3_R7). A false fail is therefore
  not certain, but the test could fail, or be argued away, for the reason pass 2 raised.

**Fix (ORDERING §5 l. 166, D105, and the matching M3_R8 sentence).**
- Read the RAW_ACT neck on its forward part, at least 3 mm from J122's pads (F.Cu x 20.25–21.8, y ≥ 83.3).
- Record J122's pin row and the mated plugs as information.
- Name J122's contacts beside the FETs as a local heat source in D105's basis.
- If an electronic load is used, wire it to J122 the same way as the servos (crimped plugs), or record how it was
  connected.

No copper change.

### R8P3-POWER-02 (Minor, worth fixing): U11's IN1 via is an undocumented single-via point on the battery-fed logic supply

**Requirement.** MARGIN_PRESCRIPTION R15: "No undocumented single point may exist on any lose-the-vehicle chain". M3_R8
"Power" (l. 112–125, R8P1-POWER-05) lists the accepted single vias: "the In2 3V3 region's feed (34.4, 69.65),
RAW_PROTECTED out of U9.6 (41.75, 83.7), the camera feed (42.15, 25.6), CAM_5V to J9.1 (40.75, 41.4) and the hold-up
(35.65, 66.6)".

**Board (measured).** I removed each of the 123 vias on 15 power nets in memory and recomputed the ratsnest. Three
RAW_PROTECTED vias disconnect pads when removed: (41.75, 83.7) and (42.15, 25.6), which are listed, and **(35.25, 60.5)**
(`r8_power.V_IN1`), which is not.
- V_IN1 carries all of the logic mux U11's battery input. The path is the F.Cu trunk (45.2, 62.6) → 0.4 mm F.Cu
  (35.25, 62.6) → V_IN1 → B.Cu to U11.2 (IN1) and C97.1. No other copper joins RAW_PROTECTED to U11.2.
- It is in series with the listed U9.6 via on the same chain: battery → U9 → U11 → U2 → 3V3 → MCU, IMU and pyro control.
- Fix pass 2 changed its ring (D98, 0.6 → 0.5 mm, same 0.3 mm drill).
- Its capacity is ample: U11's IN1 carries at most about 0.5 A (supply table), against the "about 9 °C at 1.54 A" barrel
  figure M3_R8 gives for its single points (Inference, the same fit).

The other single vias the scan finds carry a single bypass or pull-up, or the USB, VBUS, radio and GNSS feeds (bench-only
or not on a lose-the-vehicle chain). The exception is the 3V3A hop over the pyro corridor ((20.9, 62.2) and (15.0, 62.2),
two vias in series to the sensors, mA). C13 records it but the single-point list does not.

**Fix.** Add (35.25, 60.5), RAW_PROTECTED into U11.2, to M3_R8's single-point sentence. Optionally add the 3V3A hop pair
too. Records only.

### R8P3-POWER-03 (Minor, not worth fixing): the proposed pass-3 change for ACT_GATE's 0.180 mm GND via would not move the nearest GND copper

**Record.**
- `fix2_handoff.md` "Not done", R8_VALIDATION C12b #19 and "Open after fix pass 2" name a step-7 GND via (15.0, 107.3)
  0.180 mm from bare R120.2 (ACT_GATE). A bridge there turns the actuator switch on with the power switch open.
- They propose giving `make_ground.clearance` the actuator gate nets.

**Board (measured, ACT_GATE / ACT_DRV against every GND item on every layer).**
- **The GND pour is nearer than the via.** The B.Cu GND pour (zone clearance 0.15 mm) is 0.151 mm from bare R120.2 and
  bare C120.2, from ACT_GATE's B.Cu track at Q121.4 and from its via (13.48, 107.16). The F.Cu GND pour is 0.151 mm from
  bare R121.1 / R121.2, bare Q122.3 (ACT_DRV) and the F.Cu hop. The step-7 via (0.180 mm) is not the nearest GND copper.
- **R7 had the same geometry:** B.Cu GND pour 0.151 mm from bare Q121.4, R121.1 / R121.2 and Q122.3.
- **No bare GND pad lies within 2.0 mm of a bare ACT_GATE or ACT_DRV pad,** except Q122.2 inside Q122 itself (rule H
  exempts a FET's own pads). The board tents its vias (`tenting front yes, back yes`), and the pour is under mask. So the
  bare-to-bare solder bridge that rule H guards against has no GND site here, and surface leakage needs two bare
  conductors.

**Assessment.**
- Keeping step-7 vias 0.5 mm from ACT_GATE would change nothing measurable. The governing GND copper is the pour at
  0.151 mm, as on R7. The via is also not idle: it carries 0.24 A of the servo GND return, the second-largest GND via
  current in the DC_GND solve (§1).
- A real margin would need a DRU rule GND ↔ ACT_GATE / ACT_DRV covering pours as well, cutting GND pockets round the
  gate network in the band. That is not worth it for a masked-copper fault that ORDERING §5's "RAW_ACT dead with the
  switch open" and switch-off steps screen.

**Disposition.** Close the candidate without a copper change. Correct C12b #19 and the open-items line: the nearest GND
to the bare gate pads is the pour at 0.151 mm (R7: the same), masked; the via is tented.

### R8P3-POWER-04 (Minor, not worth fixing on its own): the F9 pad-edge distances treat J1.1 as round

**Record.**
- M3_R8 l. 40 and l. 454, R8_DECISIONS D76, R8_VALIDATION l. 124 and STATUS l. 76 give "pad edge to pad edge 2.0–8.4 mm:
  R167 2.04, D8 3.86, C95 5.78, R166 5.85, C80 6.21, C89 7.24, C96 8.35 mm".
- These figures came from pass 2's own R8P2-POWER-05.

**Board (measured).** J1.1 is a 2.6 × 2.6 mm rectangular pad on every layer (`GetShape` = rectangle on F, In2 and B). The
true edge-to-edge distances (pad effective shapes, binary-searched collision) are:

| Part | Pad | Edge to J1.1 (mm) |
|---|---|---:|
| R167 | 2 (GND) | 1.91 |
| D8 | 1 | 3.80 |
| C95 | 1 | 5.34 |
| C80 | 1 | 5.70 |
| R166 | 1 | 5.75 |
| C89 | 1 | 6.70 |
| C96 | 1 | 7.82 |

- The range is **1.9–7.8 mm**, and C80 ranks before R166.
- A hand check of R167.2: its pad spans x 33.825–34.775, y 108.825–109.625; J1.1 spans x 29.32–31.92, y 109.1–111.7;
  the gap is 33.825 − 31.92 = 1.905 mm.
- The centre-to-centre figures in the same sentences (3.86–10.6 mm) are correct.
- `step9/hotplug_feed.py`'s docstring still says "within 4.6-10.6 mm" (D76: corrected in fix pass 1). It also says the
  feed runs "over the In2 BAT_IN island", which has not been so since D97.

**Impact.** None: the parts are nearer than recorded, so the single-node premise holds more strongly.

**Fix.** Correct the figures and the docstring in the next records pass.

### R8P3-POWER-05 (Minor, not worth fixing): the left y 63–68 panel tab has In2 3V3 to 0.5 mm from the edge, and ORDERING §3 does not say so

**Board (measured).**
- At the left tab (KiCad y 63–68), In2 is 3V3 at every sample from 0.55 to 3.0 mm in from the edge (the 3V3 region
  starts at x 0.3, `r8_power.IN2_3V3`).
- The other three layers are GND. B.Cu GND lies 0.2 mm below In2 across the prepreg.
- Every other tab is GND on all four layers.

**Record.** ORDERING §3 l. 75 says the left forward tab and, since D97, the right forward tab are GND on all four layers.
It says nothing of the left middle tab. ORDERING §7 records the 3V3 at the hole (4, 64) beside it.

**Impact (Inference).**
- A crack at this tab joining In2 to B.Cu or In1 shorts 3V3 to GND. U2's current limit, behind U9's 2.2 A limit, bounds
  the energy.
- The board would be dead at first power-up on the bench supply. This is not the battery-energy case that D93 and D97
  removed from the other two tabs.
- ORDERING already requires nibbling, not snapping.

**Fix.** Add one sentence to ORDERING §3 naming the In2 3V3 under the left middle tab. Trimming the 3V3 region back from
the edge there would leave an In2 GND island that needs its own via, for little gain.

## 4. Checked, no finding

- **D12 and IPC-2152.**
  - The three necks were reproduced at 0.1 mm and agree with the 0.05 mm evidence. The build gate holds them.
  - BAT_IN has no series via. RAW_ACT has one via stage: 66 vias, at most 0.89 A each (0.1 mm). ACT_FET_S is a single
    B.Cu bridge.
  - RAW_ACT's peak current density is at the (11.3, 85.6) via entry, the largest-current via (0.86 A at 0.05 mm, about
    3 °C barrel rise by the record's fit, Inference).
- **Copper round the FETs.** Q120's drain net BAT_IN has 217 mm² of B.Cu, 230 mm² of In2 and 93 mm² of F.Cu pour; Q121's
  RAW_ACT has 366 / 346 / 436 mm². The trim removed only In2 copper 14 mm or more from Q120, so its spreading is
  essentially unchanged. MARGIN's 400 mm² is "good practice, not a criterion". No vias sit in the drain pads (M2), and
  the via fields are 1.5–2 mm off.
- **In2 map.**
  - Every In2 region is one island.
  - The 3V3–RAW_ACT west gap (0.3 mm) is inner layer only (IPC-2221B B1, 0.05 mm at ≤ 15 V).
  - The RAW_ACT J122 finger and the west island are as D47 has them.
  - Bucks: In2 is GND east of x 35.3 under both buck stages (DS42002 Layout 6). U7, the camera eFuse at (33.8, 30.7),
    sits over In2 3V3; its GND pad has GND vias at (35.625, 29.625) and (31.0, 31.3); it dissipates about 50 mW
    (Inference).
- **Bucks and hot loops.**
  - U2 (AP63203): C6.1 is 1.79 mm of track from VIN, and C6.2 joins U2.4 through B.Cu GND with no track or pad between
    them (loop about 2.4 × 1.8 mm). The SW strap is 0.8 × 1.95 mm. BST runs through C5 beside the pins.
  - U8 (AP63301): C72 sits on 0.6 mm VIN and GND bars, 2.5 × 2.2 mm.
  - U8's junction at a 1 A camera load is about 0.45–0.5 W × 89 °C/W (the single-layer figure) above ambient. Pass 2
    judged that inside R1's 110 °C, and the four-layer board does better (Inference). Unchanged by fix pass 2.
- **Input protection and F9.**
  - The parts sit 1.9–7.8 mm (pad edge) from J1.1. D8.2 and C80.2 / C96.2 are in the B.Cu GND pour with vias. R167 bleeds
    BAT_IN.
  - The U9 lane is over In2 GND throughout (about 4.2 nH, D76's 5 nH corner covers it). C88 is at U9.5.
  - `hotplug_feed.py`'s conclusions (≤ 0.002 V and 0.8 % slew at 5 nH) do not depend on anything fix pass 2 changed. The
    In2 trim only lowers the lane's inductance (Inference).
- **Feed and trunk widths at U9's limit.**
  - The BAT_IN lane and the RAW_PROTECTED trunk are both 0.5 mm, about 26 °C at 2.2 A and 12 °C at the 1.54 A worst
    steady load (IPC-2221 fit, no plane credit, Inference). D46 records this for the trunk; the lane carries the same
    current.
  - The 0.3 mm entries at U9.5 / U9.6 continue U9's own 0.3 × 2.4 mm pads, with free lengths of 0.6 and 0.3 mm.
- **Battery-live clearances.** No bare-pad pair between BAT_IN, RAW_ACT, ACT_FET_S or RAW_PROTECTED and GND or a
  switch-control net lies under 0.6 mm, except R122.1–R123.1 (0.505 mm, the gate-drive divider's own pair).
  - Masked 0.15–0.20 mm gaps to GND copper are as on R7. BAT_IN at 8.4 V needs 0.10 mm (IPC-2221B B2).
  - J122's GND pins lie 0.30 mm from the RAW_ACT pours on F, In2 and B, as on R7.
  - Q120.9 to R165's BAT_ENABLE via (0.180 mm) is in C12b #18 with its screen.
- **Thermal reliefs and via currents.**
  - J1.2: 4 spokes on F, In1 and B. Its conduction figure (about 0.04 mΩ for twelve spokes in parallel) stands.
  - GND via currents: 112 vias carry the servo return, none over 0.26 A (0.1 mm). The second largest, 0.24 A, is the step-7 via (15.0, 107.3) beside R120.2 (POWER-03).
  - J123.2's new relief (D101) carries only the pull-pin.
- **Decoupling.** Unchanged from pass 2; no IC power pin lost a capacitor in fix pass 2.

## 5. Not verified

- I did not rerun the 0.05 mm qualification grid. The 0.1 mm run reproduces the build gate exactly, and the record's
  0.05 mm evidence is bound to the same SHA-256.
- Of the supply-path table I re-ran the two rows fix pass 2 could touch (U9 → U11, J1 → U9). The rest were read from
  `fix2_dc_supply_summary.txt`.
- `hotplug_feed.py` was read, not rerun (it needs numpy; nothing it models changed).
- J122's contact heating in POWER-01, and every temperature, inductance and leakage figure not marked measured, are
  Inferences. I did no bench work.
