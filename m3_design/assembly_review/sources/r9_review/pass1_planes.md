# R9 review pass 1: planes and return paths

Reviewer: independent, dimension "planes and return paths". Board under review: `m3_design/assembly_review/m3.kicad_pcb`,
SHA-256 `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51` (R9 steps 1–10), design rules
`ea77b791…`, netlist `8b0e04ea…`.

I hashed the board before and after the review, and it is unchanged. I edited nothing in the repository except this file.
Every trial edit (two scratch boards with added vias) was made on copies in the session scratchpad, refilled there with
KiCad's native filler, and measured. The board copies, the R8 board extract and the Gerber extract were deleted after
use. The read-only scripts and their text outputs stay in the scratchpad's `r9review/planes/`. The R8 board for the
comparisons is `git show 9c8179b:m3_design/assembly_review/m3.kicad_pcb` (SHA-256 `cc044ea0…`).

## Verdict

**0 Critical, 1 Major, 5 Minor.**

- **R9P1-PLANES-01 (Major).** C121 is the 470 µF / 25 V polymer bulk capacitor on the 7.7 A servo rail. Its GND pad sits
  in a 60 mm² F.Cu GND region that holds no GND via. Its whole return runs through about 15 mm of F.Cu: a 0.66 mm guard
  strip beside ARM1_SENSE that narrows to 0.37 mm, then into GND vias inside PYRO_BLOCK. The return measures
  **11.98 mΩ** (C150's, through one via, is 2.58 mΩ). The region's far end is **28.4 mm of copper from a GND via**, the
  worst on the board (R8's worst 15.4 mm). No gate or record shows it. A scratch trial with two GND vias beside the pad
  gives **0.89 mΩ** and leaves the RAW_ACT 7.7 A path unchanged (0.79 mΩ, neck 12.8 °C) and DRC clean.
- **Minor:**
  - 02: an unstitched F.Cu GND strip on the forward edge, 12.5 mm of copper from a via, has a legal via spot (worth fixing).
  - 03: R9's deviation list dropped R8's C15 row (unstitched GND pieces 0.5–1.0 mm wide, GND-pad copper reach), so the owner
    cannot see 01 or 02 (worth fixing).
  - 04: the crystal plane's records say AN2867 is met but omit that its "distinct from the application ground" clause is
    not, and undercount the plane's vias.
  - 05: the reference gate samples only the R6 and extended nets, not all of AGENTS §3's critical classes.
  - 06: M3_R9 gives step 6's In2 region areas as the final board's.
- **What holds.** In1 is one solid GND plane; every critical net is referenced (own antipads only); no critical net
  crosses an In2 split; D-S8-19's via pads are correct and within JLC's capability; the crystal plane is sound (Inference
  on the stray-capacitance cost); P9, P10, R6b and the nine pockets are as recorded.

## 1. The previous pass in this dimension

There is no earlier R9 review pass. The last pass in this dimension is R8 pass 5 (`sources/r8_review/pass5_planes.md`,
board `cc044ea0…`).

| Item | Status | Evidence |
|---|---|---|
| R8P5-PLANES-01 (R8_VALIDATION scorecard intro: "no P, R or D row moved") | **Closed** | `docs/R8_VALIDATION.md` l. 398, "Fixed (records)"; R8 only |
| R8 pass-5 observation: crystal keep-out trade-off (In2 void under Y1) | **Superseded** | R9 replaces the void with a local GND plane (D-S8-20); reviewed in §5 |
| R8 pass-5 observation: ARM1_SENSE 14.5 mm over In2 3V3 | **Gone** | R9 ARM1_SENSE is 40.08 mm on F.Cu, all over In1 GND (§4) |
| R8 pass-5 observation: D4.2's single-via pocket | **Carried** | the same geometry is R9's WEAK_EXCEPT entry (F, 2.82 mm², via (9.95, 34.1)); R8 D63's exception (§9) |
| R8 C15 class: unstitched GND pieces 0.5–1.0 mm and GND-pad copper reach | **Not carried** | R9 records have no such row; R9's worst items exceed R8's (R9P1-PLANES-01, -02, -03) |

## 2. Gates and tools run on `fc3d5b34…`

| Run | Result |
|---|---|
| `m3_design/r9_ground_check.py --report` | **all 12 gates OK** (table, drc, route, stitch, in2, xtal, islands, reach, reference, pyro, contract, actuators), 3 min 22 s. Reach: 18,544 points, P9 p95 3.45 mm, P10 max 7.32 mm at (31.25, 91.25). P7 9. Reference: R6 set 3,206 / 31,359 (R6b 0.1022), extended set 3,930 own-via plus 1 recorded stray. xtal: area 36.73 mm², cover 0.9612, one piece, 6 vias with their centres inside |
| `tools/dc_solve.py` (GND net, 0.1 mm, window x 18–40, y 54–82, sink J122:3,6,9,12) | C121:2 **11.98 mΩ**, F.Cu 100 % at mid-path, peak 3.73 A/mm at (28.85, 75.75); C150:2 2.58 mΩ, all of it through the via (31.4, 73.6) |
| `tools/dc_solve.py` RAW_ACT (Q121:5–9 → J122:2,5,8,11, 0.1 mm, `--necks`) on a scratch copy and on the trial | both 0.79 mΩ; neck 7.79 / 7.77 mm on B.Cu at Q121, 12.8 °C (D12 20) |
| kicad-cli DRC on scratch copies (no schematic, so no parity) | original copy and both trials: 0 violations but 199 `lib_footprint_issues` (the scratch folder has no library table: identical on the original copy), 0 unconnected |
| Gerber package `fab/m3_gerber.zip` (inner layers, drill file) | In1: 255 + 170 ViaPad flashes = 425; In2: 212 + 201 = 413; via drill tool T1 0.300 mm `ViaDrill`; component drills keep their inner pads |
| Own read-only pcbnew scripts | listed at the end |

## 3. In1

- **The plane.** One GND outline, 4,215.6 mm², with 172 holes totalling 311.9 mm². There is no track on In1 or In2: the
  board's 861 tracks are 432 on F.Cu and 429 on B.Cu.
- **Large voids (≥ 5 mm²): 16.** These are:
  - the seven routed holes: the four corner M3 holes, (42, 59.5), and the tie holes (15.6, 62) and (30.8, 59);
  - the four 2.6 mm terminal pads of J121 and J124: 16.3, 16.3 and 13.2 mm² round the bus, igniter and drain pads
    (rule D's 0.75 mm fill margin), and 8.1 mm² round J124.2 (RAW_ACT, 0.3 mm);
  - J1's four pins (6.4–10.7 mm²; J1.2's is its thermal-relief ring);
  - J123's slot.
- **Slots (survey P3b): 4.** None lies under an F.Cu signal except at that signal's own via.
  - J123's two pins merged: 3.9 × 1.44 mm, x 38.05–41.95, y 28.65–30.55.
  - J3's two leg pairs: 2.84 mm each, at (5.0–7.6, 29.1–32.0) and (5.0–7.6, 36.6–39.5).
  - The antipads of the three strip vias GNSS_VCC_RF, GNSS_ANT_DC and GNSS_LNA_EN, merged: 2.65 × 0.59 mm at
    (10.0–12.65, 7.0–7.8). They are 0.9–0.95 mm apart, and the 0.40 mm antipads leave 0.1 mm, below In1's 0.2 mm minimum
    width. GNSS_RF_ANT's edge at x 13.44 is 0.79 mm from it.
- **Necks.** Eroding In1 by 0.25, 0.5 or 1.0 mm leaves one large piece each time. Only the bits between J122's pin
  antipads, under 1.3 mm² each, fall away. In1 has no neck narrower than 2 mm on any return path.

## 4. Critical-signal references and split crossings

- **R6 and extended sets** (`tools/reference_audit.py`, `r9_ground_check`). The R6 set has 3,206 unreferenced samples of
  31,359; the extended set has 3,931 of 83,715.
  - Every one lies inside the net's own via antipad, but one: USB_DM's edge sample at CC1's via (7.85, 32.75), the
    recorded REF_STRAY.
  - The per-side counts equal D-S8-17's: 21 one-branch sides at 119–133, HSE_OUT B.Cu 241, QSPI_NCS B.Cu 242, IMU_CS
    B.Cu 172.
  - The R6b floor arithmetic holds: 24 sides × 119 = 2,856 samples, 0.091 of the set. "12 is the minimum" holds too:
    U3, Y1 and U4 are on the bottom under U1, and each of the 12 nets has exactly one via.
- **Extension to every AGENTS §3 critical class.** route_check's classes are rf, pyro (PYRO\*, ARM\*), crystal, usb, spi
  and rfif (every RADIO_\* / GNSS_\*): 60 nets, sampled on the centre line and both edges every 0.02 mm (`refall.py`).
  Unreferenced samples fall in only four places:
  - their own via antipads;
  - the In1 antipads of their own terminal pads: PYRO1_BUS, PYRO1_IGN and PYRO1_OUT for 2.06 mm each, J121 and J124
    being 2.6 mm pads with the 0.75 mm margin;
  - the two launch windows (GNSS_RF_ANT and RADIO_RF_ANT, y 2.3–4.6, R7's qualified launch, R-4);
  - three tangency samples, where a track edge lies exactly 0.400 mm from another net's via centre. That is the DRC's
    0.15 mm edge clearance plus the 0.25 mm pad radius, which equals the 0.40 mm antipad radius:
    - USB_DM at CC1 (7.85, 32.75), the recorded one;
    - ARM1_SENSE_MCU (25.55–27.67, y 47.0) at RAW_ACT_SENSE_MCU's via (26.95, 46.5);
    - RADIO_NRST (25.55–33.65, y 44.0) at CAM_MCU_RX's via (33.15, 44.5).
- **Split crossings.** No critical track crosses an In2 boundary or lies over a foreign In2 region (RAW_ACT or BAT_IN).
  - HSE_IN's and QSPI_NCS's B.Cu branches pass from In2 3V3 onto the crystal plane inside their own via antipads, as
    D-S8-20 says.
  - B.Cu critical runs over In2 3V3: QSPI × 6, SPI1 × 3 and IMU_CS, 0.29–7.37 mm each. Each has a GND via 0.77–1.30 mm
    away and a 3V3 or 3V3A capacitor 1.71–5.40 mm from its via (C29, C16, C17, C31; `critvias.py`).
  - The largest critical-via-to-GND-via distance is 1.39 mm, at PYRO1_GATE (9.125, 61.955). All are within AGENTS §3's
    1.5 mm (S13 0).
- **Non-critical split crossings (information).** These are slow status and sense lines; I infer the effect is
  negligible.
  - BAT_FAULT_N and LOGIC_SOURCE_ST run 5.1 / 5.7 mm on B.Cu over the In2 RAW_ACT region. They cross 3V3 → RAW_ACT → 3V3
    → GND at (33.5–38.1, 57.0–60.3).
  - CAM_UART_OE, CAM_FAULT_N, VLOGIC_SENSE, USB_OVLO and PULLPIN_EXT cross 3V3 / GND boundaries.

## 5. The crystal's local In2 ground plane (D-S8-20) against ST AN2867

- **Source.** I read ST AN2867, DocID15287 Rev 10 (August 2015), the revision D-S8-20 cites; ST's site refused
  automated download, so I used the copy at
  https://www.raltron.com/webproducts/technical/technical_notes/Oscillator-design-guide-for-STM8S-STM8A-and-STM32-microcontrollers-ST-MICRO-1.pdf.
  Section 5.1 "PCB design guidelines" (p. 26):
  - "The oscillator PCB should be underlined with a dedicated underneath ground plane, distinct from the application PCB
    ground plane. The oscillator ground plane should be connected to the nearest microcontroller ground. It prevents
    interferences between the oscillator components and other application components."
  - It also asks for a guard ring connected to ground, for high-frequency paths routed away, and for "high values of stray
    capacitance" to be avoided.
  - Figure 10 shows a "Local ground plane (other layer)".
  - D-S8-20's quotation is accurate.
- **As built.**
  - R9_GND_In2_Y1 (GND, priority 11) fills 35.31 mm² in one piece; its outline is the rule area less NRST's notch.
  - On In2 it is an island inside R9_3V3_In2: no other In2 GND fill lies within 7.98 mm, and a ring 0.5 mm outside the
    area is 3V3 or empty.
  - It is tied by **nine** GND vias flashed on In2. Six have their centres inside: (14.53, 49.95) for C25.2,
    (14.6, 47.4), (17.65, 45.85), (19.875, 49.859), (20.35, 48.75) and (20.42, 49.6). Three overlap its edge:
    (16.0, 50.6), (19.69, 45.75) and (21.95, 47.0) for C26.2.
  - Every one of the nine also joins In1 GND, the board's ground plane.
  - **Nearest MCU ground: met.** U1.10 (VSS, (16.5, 52.05)) is the VSS pin next to OSC_IN and OSC_OUT (U1.12 / .13). It
    is solidly in the F.Cu GND piece that holds via (16.0, 50.6), about 1 mm of copper away.
  - **"Distinct from the application ground": not met**, though D-S8-20 does not say so. The plane is bonded to In1 at
    nine points, and U4's GND pins 2 and 3 return through plane via (14.6, 47.4).
  - With a solid In1 GND 0.203 mm under the top layer, multi-point bonding is the usual 4-layer practice, and the IMU's
    mA-level return makes µV-level differences (Inference). So I find no electrical defect, only an incomplete record
    (R9P1-PLANES-04).
- **Guard and neighbours.**
  - Y1.2 and Y1.4 sit in the main B.Cu GND island (2,815.6 mm²); C25.2 and C26.2 each have their own GND via.
  - B.Cu tracks inside the area are HSE_IN and HSE_OUT, their GND straps, R10's 3V3 tap, QSPI_NCS's pull-up stub to R10.1
    (3 mm from C25 and Y1), and VLOGIC_SENSE (slow) at the area's north-east corner.
  - No In2 track exists anywhere.
- **Stray capacitance (D-S8-20's Inference, checked).** Stack-up B.Cu–In2 is 0.203 mm, εr 4.4. Y1's 1.4 × 1.2 mm pad
  gives 0.32 pF, C25.1 / C26.1 give 0.05 pF, and the B.Cu runs give 0.12 pF (HSE_IN, 3.03 mm) and 0.06 pF (HSE_OUT,
  1.63 mm). That is about 0.4 pF per node and C_L about +0.2 pF, as recorded.
  - Scaling the frozen-design margin of 1.35× (C0 = 7 pF) by ((C0 + C_L) / (C0 + C_L + 0.19))² gives about 1.32× (Inference).
  - The bench HSE check in ORDERING §5 covers it.

## 6. Via pads (D-S8-19)

- **Mode.** All 579 vias (343 of 0.5 / 0.3 mm, 236 of 0.6 / 0.3 mm) are `UNCONNECTED_LAYER_MODE_REMOVE_EXCEPT_START_AND_END`.
- **Flashing follows connectivity on every via** (0 mismatches between `FlashLayer` and same-net fill contact).
  - In1: 425 flashed, which is every GND via. 344 are flashed on both inner layers. 81 GND vias are unflashed on In2:
    they sit in the 3V3, RAW_ACT or BAT_IN regions.
  - Six GND vias on the In2 3V3 / GND boundary are unflashed on In2. Harmless: In1 is solid.
- **The Gerbers agree.** The inner layers carry exactly 425 and 413 ViaPad flashes.
- **Antipads.**
  - Unflashed vias leave a 0.400 mm radius clear (minimum 0.4005 mm) on In1 and In2. In the 0.3 mm-clearance RAW_ACT and
    BAT_IN regions it is 0.450 mm.
  - That puts copper 0.25 / 0.30 mm from the 0.30 mm hole, against JLC's "Inner layer via hole to copper clearance:
    0.2mm" (https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-25).
- **Component holes keep all their inner pads**, so inner copper is ≥ 0.5 mm from every plated component hole. That meets
  JLC's "Inner layer PTH pad hole to copper clearance: 0.3mm". The NPTH holes of J2 and J3 keep 0.25 mm.
- **Effect.** The only effect is more plane copper round foreign holes; no clearance shrinks. D-S8-19 is correct.

## 7. In2 regions

- **Regions, each one piece** (in2 gate on this board): GND main 1,742.2 mm², the GND strip 982.1 mm², the crystal plane
  35.3, 3V3 1,037.1, RAW_ACT 241.9, BAT_IN 115.3 mm².
  - The main GND and strip GND fills share the edge y = 23.0 (union one outline, zero overlap), so they are one piece of
    copper.
  - The main zone's 0.25 mm sliver along y 23.0–23.25 merges into the strip zone along its whole length.
- **Necks (erosion).**
  - 3V3 keeps one piece at 0.5 mm. At 0.75 mm the spine finger (x 36.3–37.8, y 56.7–79) vanishes. At 1.0 mm the via field
    under U1 splits it into 14 pieces.
  - In2 GND splits at 1.0 mm into 900 + 239 mm² near (35–44, 56–58).
  - Neither matters for return currents (In1 is solid; every critical B.Cu sample is referenced) or for DC (3V3 paths
    solved, ≤ 44.85 mΩ).

## 8. Stitching density: P9 / P10, and copper reach

- **P9 / P10.** P9 3.45 mm and P10 7.32 mm are confirmed.
  - P10's point (31.25, 91.25) has BAT_IN on F.Cu, In2 and B.Cu, so no GND copper there needs stitching. The miss carries
    no plane risk, and D-S8-16's cause is correct.
  - Straight-line distance from outer GND-pour points: p95 2.86 mm, max 5.85 mm at (32.725, 64.225). R8's gate held
    pour_max ≤ 7.0 mm.
- **What P9, P10 and the pour figure cannot see.** They measure straight lines, so a via counts as covering copper it is
  not joined to.
- **Through-copper reach.** `route_check.gnd_reach` is the gate's own finger reach, run over every outer GND point on a
  0.05 mm raster:

| | F.Cu p95 / max | F.Cu points > 10 mm | B.Cu p95 / max |
|---|---|---|---|
| R8 `cc044ea0…` | 3.17 / 15.36 mm at (18.6, 103.3) | 4,203 (≈ 10.5 mm²) | 3.32 / 11.68 mm |
| R9 `fc3d5b34…` | 3.99 / **28.41 mm at (37.45, 73.75)** | **23,303 (≈ 58 mm²)** | 2.79 / 6.67 mm |

  - B.Cu improved on R8. F.Cu regressed, almost all of it in one region round C121 (R9P1-PLANES-01).
  - The other F.Cu clusters beyond 4 mm of copper, with their maximum reach and box:

    | Max reach | Box | Note |
    |---|---|---|
    | 12.5 mm | x 22.1–33.2, y 98.4–100.1 | R9P1-PLANES-02 |
    | 9.2 mm | x 40.6–41.8, y 40.5–46.0 | |
    | 8.9 mm | x 38.5–41.8, y 44.4–48.5 | J9.2's piece |
    | 8.45 mm | x 26.5–35.7, y 87.7–96.2 | |
    | 7.1 mm | x 4.9–8.1, y 48.3–50.5 | |
    | 6.8 mm | x 38.1–39.5, y 72.6–75.6 | |
    | 6.8 mm | x 26.4–29.6, y 40.4–42.2 | |
    | 6.5 mm | x 33.7–37.0, y 51.7–56.1 | |
    | 6.2 mm | x 6.6–8.8, y 61.5–63.6 | |

## 9. The nine single-via pockets (P7, D-S8-15)

- **Confirmed.** My island enumeration (`islands.py`) finds F.Cu 23 outlines and B.Cu 16. Each has at least one GND via
  or plated GND hole (zones remove islands always). Exactly nine have one, the nine WEAK_EXCEPT entries, at their recorded
  areas.
- **No second via.** No legal spot exists in any of them:
  - the aid's own `legal()` on the final board gives 0 mm² in each;
  - my simplified independent search (pad inside the deflated pocket; 0.40 + 0.05 mm to foreign copper on both outer
    layers; hole-to-hole 0.25 mm and 0.6 mm to GND vias; 0.3 mm to GND SMD pads; 1.0 mm to test pads; via-barring areas;
    two-to-four-pad bodies) finds none either.
- **The pockets that carry component GND pads:**
  - D4.2, the USBLC6 ESD return, one via (R8 D63's exception);
  - C150.2 and C151.2 (2 × 22 µF on RAW_ACT): 2.58 mΩ to J122's GND pins, the whole current through via (31.4, 73.6);
  - R125.2, R182.2 and C122.2, the RAW_ACT_SENSE divider's bottom. µA currents; if that via opened, the divider would
    read high (benign).
- **The other five carry no pad.** The recorded reasons hold.

## 10. GND islands, fingers and GND-pad reach

- **Gate items.** route_check r9 reports no pour sliver, no pour finger and no starved thermal. DRC is 0.
- **Thin pieces** (opening at 0.75 mm, length ≥ 2 mm, area ≥ 0.15 mm²): F.Cu 39, B.Cu 51, In1 0, In2 one (the merging
  sliver of §7).
- **GND-pad copper reach.** Every GND SMD pad of C / U / D / Q / R / L / Y / J parts, 174 pads (`capreach.py`):
  - **R103.2 20.53 mm** and **C121.2 14.85 mm**, both in the region of R9P1-PLANES-01;
  - J9.2, the camera return, 6.40 mm;
  - R102.2 4.50 mm;
  - C87.2 4.08 mm;
  - every other pad ≤ 3.63 mm.
  - For comparison, R8's C15 recorded R123.2 12.98, Q122.2 12.42, U13.2 9.28, C93.2 7.24 and J9.2 6.92 mm.

## 11. Findings

### R9P1-PLANES-01: Major

**C121's GND return is about 15 mm of F.Cu through a 0.37 mm neck. C121 is the 470 µF polymer bulk capacitor on
RAW_ACT, the 7.7 A servo rail. Its GND pad lies in a 60 mm² F.Cu GND region with no GND via, walled in by a µA sense
track, and the return measures 11.98 mΩ. Two vias beside the pad bring it to 0.89 mΩ.**

- **Requirement.**
  - AGENTS §3: hand-route critical nets; GND is route_check's critical "power" class. It also asks to "size high-current
    copper per IPC-2152".
  - REQUIREMENTS M2 lists "unstitched GND pour fingers". D-S8-03 extends that to strips the gate's 0.5 mm test cannot
    see: "A strip 0.5–0.6 mm wide would pass route_check's 0.5 mm finger test yet be the same unstitched copper".
  - The owner's second priority is a robust layout. M3_R5 already named C121's "bulk return impedance" as a concern when
    its GND via was 1.18 mm away.
- **Evidence** (pcbnew on `fc3d5b34…`; scripts below).
  - **The part.** C121 is a 470 µF / 25 V polymer, C46550466 (M3_ACTUATOR_MERGE l. 22), on F.Cu at (33.4, 66.6). The GND
    pad C121.2 spans x 32.77–34.03, y 61.50–65.11; the RAW_ACT pad sits in the R9_RAW_ACT_F pour.
  - **The region round C121.2 is walled on all sides.** An exact polygon clip of R9_GND_F gives 42.39 mm² in x 28.7–37.5,
    y 54–65.4, and 60.46 mm² with its two strips to y 76.2. Its walls:
    - north: VLOGIC's F.Cu tap, 0.25 mm: (30.4, 56.0) → (30.8, 56.4) → (35.0, 56.4) → (37.6, 59.0);
    - east: the same tap, (37.6, 59.0) → (37.6, 68.7) → the hold-up via (38.5, 69.6). It feeds the R60 / R61 sense divider
      (D-S7-14): microamps;
    - west: the ARM1_SENSE lane, x 28.53 (y 47.0–75.64);
    - south: the R9_RAW_ACT_F pour.
  - It holds C121.2 and R103.2 (CAM_IO_3V3's 1 kΩ load) and **no GND via**. The only GND vias in x 28.7–37.5, y 56–75 are
    in other pieces:
    - (32.067, 56.975), the divider pocket's via, in a separate F.Cu piece by exact clip;
    - (31.4, 73.6), inside the RAW_ACT pour.
    The GND via column at x 38.45–38.8 (y 57.2–68.3) lies 0.85 mm east of the VLOGIC tap.
  - **Its only exit** is the guard strip between the ARM1_SENSE lane and the pour (D-S8-05). The strip is x 28.785–29.445,
    0.66 mm, for y 65.5–75.0. It then narrows to **0.37 mm** (x 28.725–29.095) at y ≈ 75.8, where R9_RAW_ACT_F's west edge
    steps back from 29.75 to 29.4 (its outline vertex (29.4, 75.6)).
  - The strip ends at GND vias (27.95, 77.55), (27.5, 77.95) and (27.95, 78.35). All three are **inside PYRO_BLOCK**,
    0.81–0.84 mm from ARM1_SENSE. The strip itself runs 0.155 mm (edge to edge) from ARM1_SENSE for about 10 mm.
  - **DC.** `dc_solve.py --net GND --source C121:2 --sink J122:3,6,9,12 --grid 0.1 --window 18,54,40,82`:
    - **R = 11.98 mΩ**; F.Cu carries **100 %** at mid-path; peak **3.73 A/mm at (28.85, 75.75)**, the neck.
    - Into In1 the current goes through the three PYRO_BLOCK vias above (0.42, 0.22 and 0.17 A per A).
    - The same solve from C150:2 gives 2.58 mΩ.
  - **Copper reach** (`route_check.gnd_reach`, 0.05 mm raster):
    - C121.2: 14.75–20.02 mm (min–max over the pad's box grown by 0.1 mm, `reachpad.py`; `capreach.py`'s box gives
      14.85–19.87). R8 `cc044ea0…`: 1.10–4.60 mm.
    - R103.2: 20.24–21.63 mm.
    - The east strip's tip (37.45, 73.75): 28.4 mm. That strip is x 36.05–37.35, y 65.4–74.2, dead-ended between the pour
      and the VLOGIC tap.
    - F.Cu points beyond 10 mm of copper: about 58 mm² on R9 against about 10.5 mm² on R8 (§8).
  - **Why nothing caught it.**
    - route_check's pour_finger needs a piece under 0.5 mm wide and over 3 mm long. The strip is 0.66 mm wide, and the
      0.37 mm neck is under 1 mm long.
    - P9 / P10 and the pour figure measure straight lines. The pour maximum, 5.85 mm, lies at (32.725, 64.225) inside this
      very region, judged "covered" by vias it is not connected to.
    - D-S8-05 widened the guard from 0.30 to 0.69 mm "joined at both ends: a guard, not a finger". Its north end joins
      this via-free region, so the strip is the region's only path.
    - No R9 record lists GND-pad copper reach (R9P1-PLANES-03).
  - **Why no via was placed.** `r9_ground_aid.legal()` on the final board finds 0 mm² of legal centres in the region and in
    both strips. The blockers are the B.Cu RAW_ACT pour and the In2 RAW_ACT region (inside the RAW_ACT corridor box
    (17.19, 60.0)–(36.63, 83.51)), the In2 3V3 finger and TP90's 1.0 mm rule.
    - Relaxing only "no GND via in the RAW_ACT B.Cu pour / In2 corridor" gives 13.4 mm² of legal centres
      (`legal_relaxed.py`): x 29.43–32.85, y 60.61–64.98 west of the pad, and x 34.58–35.70, y 61.32–64.81 east of it.
    - The east spots are off the main RAW_ACT path, which runs from Q121 north-west to J122's RAW row at y 62.0, x 19–27.
  - **Impact** (part Inference).
    - The polymer's own ESR is not published (ORDERING: "C121's maker publishes no datasheet"). Comparable 470 µF / 25 V
      polymers are 14–20 mΩ (Inference). So 12 mΩ of GND path roughly doubles the reservoir's low-frequency series
      resistance and adds the strip's loop inductance.
    - At 1 A of ripple the 0.37 mm neck carries 2.7 A/mm (IPC-2221 external: about 1.2 A for a 10 °C rise at that width;
      Inference). ORDERING §5 asks to scope RAW_ACT at C121 for "ripple and the step on release" without knowing this.
    - The servo bulk's return current also enters the planes inside the pyro column, beside the arming sense lane. That
      is contrary to the B-spine's intent: power in the east spine, the pyro column a dead end. The coupling into
      ARM1_SENSE is negligible (Inference: about 0.3 nH mutual over 10 mm).
- **Fix** (one of the two; both verified as far as a scratch trial can):
  1. **Two GND vias (0.5 / 0.3 mm) east of C121.2 at ≈ (35.15, 62.0) and (35.15, 64.0)** as recorded rows of
     `r9_ground.tsv`. Each is an exception to D-S8-02's "power pours and 7.7 A corridors uncut" policy for a bulk-capacitor
     GND pad, justified by the DC re-check.
     - Scratch trial (copy refilled natively): R(C121:2 → J122 GND) 11.98 → **0.89 mΩ** (In1 89 %).
     - C121.2's reach 14.75–20.02 → 0–3.81 mm; R103.2's 20.24–21.63 → 0.74–2.18 mm (`reachpad.py`).
     - RAW_ACT path 0.79 → 0.79 mΩ, neck 7.79 → 7.77 mm, 12.8 °C (D12 20).
     - kicad-cli DRC adds no violation and no unconnected item.
     - `r9_ground_check`'s stitch gate (no In2 power region cut inside a 7.7 A corridor) needs a recorded exception for
       these two rows, and `r9_ground_aid.py --check` an equivalent stage, so the table stays reproducible.
     - Re-run `tools/run_dc.sh`, `r9_ground_check.py` and `tools/check.sh`.
  2. **Re-route VLOGIC's sense tap** so it no longer separates the region from the x 38.45 GND via column (D-S7-14 /
     D-S8-10 copper; for example, take R60's VLOGIC from the north instead of up x 37.6 from the hold-up via). The aim is
     C121.2 within about 4 mm of copper of a via and R(C121:2 → J122 GND) within about 3 mΩ.
  - In either case, extend D-S8-05's 29.75 mm pour edge to y ≈ 76.6 so the 0.37 mm neck becomes 0.66 mm.
  - In either case, add a through-copper reach check to `r9_ground_check.py`: every GND SMD pad of a C / U / Q / J part
    within a ceiling (for example 5 mm of copper to a GND via) or a recorded exception, so the class cannot return
    unseen.

### R9P1-PLANES-02: Minor, worth fixing

**An unstitched F.Cu GND strip on the forward edge reaches 12.5 mm of copper from a GND via, and the aid's own rules have
a via spot in it.**

- **Requirement.**
  - M2: "unstitched GND pour fingers", with D-S8-03's 0.5–0.6 mm note.
  - R8 recorded the same class at this edge (C15: F.Cu x 19.82–43.37, y 98.66–99.51, 10.3 mm).
- **Evidence.**
  - The F.Cu GND piece lies between R9_BAT_IN_F (fill to y 99.2, clearance 0.3) and BAT_ENABLE's F.Cu edge lane
    (20.48, 100.4)–(35.0, 100.4), w 0.2. It is about 0.65 mm wide (y 99.5–100.15) and dead-ends at x 33.25.
  - Copper reach ≥ 4 mm over x 22.1–33.2 (9.3 mm²); **12.50 mm at the tip (33.225, 100.075)**.
  - `r9_ground_aid.legal(revive=True, spacing=0.6)` has 0.034 mm² of legal centres at ≈ (32.61, 99.83) inside it. The
    stitching stages never searched it because P9 counted the area as covered.
  - Scratch trial with a via there: the strip's maximum falls to **6.00 mm** at (26.475, 100.125). DRC is unchanged.
- **Fix.** One `r9_ground.tsv` row at the aid's legal spot (for example, a finger stage on copper reach rather than on
  the 0.5 mm width), then re-run the ground gate. Or record the strip with its reach in the deviation list (R9P1-PLANES-03).

### R9P1-PLANES-03: Minor, worth fixing (records)

**R9's deviation list has no row for unstitched GND pieces wider than the gate's 0.5 mm, or for GND-pad copper reach.
R7 (C11) and R8 (C15) recorded both, and M2 requires every review-only residual to be listed. R9's worst items are
beyond R8's, and the owner cannot see them.**

- **Requirement.** REQUIREMENTS M2: "every review-only residual is listed, with location, rule, measured reason". "Unstitched
  GND pour fingers" are gated only under 0.5 mm. R8P2-PLANES-03 put GND-pad reach in C15.
- **Evidence.**
  - `docs/R9_VALIDATION.md` C1–C18 and table F have no such category. M3_R9 "Ground" gives only P7, P9, P10 and R6b.
  - Measured on `fc3d5b34…` (§8, §10):
    - F.Cu pieces 28.4, 12.5, 9.2, 8.9, 8.45 and 7.1 mm of copper from a via; B.Cu worst 6.67 mm;
    - pads R103.2 20.53, C121.2 14.85, J9.2 6.40 (the camera return; R8 6.92, recorded), R102.2 4.50 and C87.2 4.08 mm;
    - thin pieces at 0.75 mm: F.Cu 39, B.Cu 51.
- **Fix.** Add a C row in R8 C15's form: the method (route_check pour_pieces at 0.75 / 1.0 mm, `route_check.reach`), the
  worst pieces with the GND pads they serve, and the reason each stays. Re-measure after 01 and 02.

### R9P1-PLANES-04: Minor, not worth fixing on its own (records)

**D-S8-20 and R9_VALIDATION C14 rest the crystal plane on AN2867 §5.1 without saying that its "distinct from the
application PCB ground plane" clause is not followed. They also count six vias where nine tie the plane.**

- **Evidence (§5).**
  - The plane is bonded to In1 GND by nine vias: six centres inside, plus (16.0, 50.6), (19.69, 45.75) and
    (21.95, 47.0) overlapping its edge.
  - U4.2 and U4.3 return through plane via (14.6, 47.4) (`padgnd.py`).
  - The "nearest microcontroller ground" clause is met through U1.10 and via (16.0, 50.6).
- **Effect.** None measured. Multi-point bonding to a solid In1 is normal 4-layer practice (Inference). The owner's C14
  decision should be made knowing which clause is departed from.
- **Fix** (fold into the next records edit): D-S8-20 and C14 should say "local plane bonded to In1 at nine vias, including
  U1.10's via, the nearest VSS; AN2867's 'distinct' clause deliberately not followed on a 4-layer board with a solid In1
  GND; U4's GND shares (14.6, 47.4)".

### R9P1-PLANES-05: Minor, not worth fixing on its own (tool coverage)

**The reference gate (`r9_ground_check` reference, `reference_audit.py`, R6b) samples only the R6 and extended nets. The
AGENTS §3 critical classes pyro / arming and the non-SPI RADIO_\* / GNSS_\* nets are never sampled, so a later split
crossing on, say, PYRO1_GATE_N or RADIO_NRST would pass the gate.**

- **Evidence.** `critical_reference.R6_NETS` and `EXTENDED` lack PYRO\*, ARM\* and RADIO_BUSY / DIO1 / NRST / RXEN /
  TXEN / GNSS_\*. Measured on this board (§4), all 60 AGENTS §3 nets are clean but for two tangency samples at exactly
  the 0.40 mm antipad radius: ARM1_SENSE_MCU at (26.95, 46.5) and RADIO_NRST at (33.15, 44.5), the same kind as the
  recorded USB_DM stray.
- **Fix** (with the next gate change): sample route_check's SIGNAL_CRITICAL classes in the reference gate, with the two
  tangencies as REF_STRAY entries.

### R9P1-PLANES-06: Minor, not worth fixing on its own (records)

**M3_R9 "Power" gives step 6's In2 region areas as the final board's.**

- **Evidence.**
  - `docs/M3_R9.md` l. 107–108: "RAW_ACT (244.5 mm²), BAT_IN (115.3 mm²), 3V3 (… 1098.9 mm²)", from
    `r9_step6_handoff.md` l. 40.
  - On `fc3d5b34…` (the in2 gate's own figures): RAW_ACT 241.9, BAT_IN 115.3, 3V3 **1037.1 mm²**. Step 8's crystal plane
    (35.3 mm²) and the GND vias' antipads account for the difference.
- **Fix.** Quote the final board's areas (or label them step 6's) in the next records edit.

## 12. Observations (not findings)

- **C150 and C151.** Two 22 µF capacitors share one GND via (31.4, 73.6): 2.58 mΩ, 1.00 A per amp through one barrel.
  This is a recorded pocket with no legal second spot. It is adequate at servo-ripple frequencies (Inference).
- **D4.2.** The USB ESD return is one via. It is R8 D63's accepted exception.
- **Power layer changes without a GND via within 1.5 mm.** There are seven, recorded as information (AGENTS §3 asks it of
  critical nets only).
- **BAT_FAULT_N and LOGIC_SOURCE_ST.** They run over the In2 RAW_ACT region for about 5 mm each. Both are slow
  open-drain flags; I infer the injection is negligible.
- **R6b.** The 0.08 row stays missed for the recorded, correct causes: own antipads of the 12 unavoidable critical vias.
  The metric counts no physical reference loss.

## Method and scripts

The scripts are in the session scratchpad, `r9review/planes/`. All are read-only on the repository board. The trials
were built on scratch copies by `fixtrial.py`: copy `m3.kicad_pcb`, `.kicad_pro` and `.kicad_dru` together, then run
`fixtrial.py COPY OUT x,y …`, which adds 0.5 / 0.3 mm GND vias in D-S8-19's pad mode and refills.

- **Planes and vias:**
  - `zones.py`: the zone inventory and fills;
  - `vias.py`: every via's pad mode, flashing against fill contact, and its antipad radius;
  - `thtpads.py`: inner clearance round every plated and NPTH hole.
- **Islands and pockets:**
  - `islands.py`: outer GND islands with their vias, holes and pads;
  - `pocketspots*.py`: the independent second-via search;
  - `legal_region.py` / `legal_relaxed.py`: `r9_ground_aid.legal()` on the final board, as is and with the RAW_ACT
    relaxation.
- **References and crystal:**
  - `refall.py`: the reference and split-crossing sampling of every signal net;
  - `graze.py`, `unrefloc.py`: unreferenced runs and tangencies;
  - `critvias.py`: critical vias, their GND partners and decoupling;
  - `xtal.py`, `xtal2.py`, `u1gnd.py`: the crystal plane, its vias, U1's VSS pins.
- **Shape and reach:**
  - `erode.py`, `thin.py`: necks and thin pieces;
  - `reachall*.py`, `cluster2.py`, `reachpad.py`, `reachwin*.py`, `capreach.py`: through-copper reach
    (`route_check.gnd_reach`), R8 against R9;
  - `pourmax.py`: straight-line pour reach;
  - `padgnd.py`: GND pad connections;
  - `dump.py`, `plot.py`: F.Cu, B.Cu and In2 renders of x 24–46, y 52–80.
- **Gerbers:** `gcount.py`, inner-layer flash counts.
- **Repository tools:**
  - `m3_design/r9_ground_check.py --report`;
  - `tools/dc_solve.py` (GND from C121:2 and C150:2; RAW_ACT on a copy and on the trial);
  - kicad-cli DRC on the scratch copies.
- **Sources:**
  - ST AN2867 Rev 10 (Raltron's copy, URL above), §5.1 and Figure 10;
  - JLC PCB capabilities (URL above, read 2026-10-25): "Inner layer via hole to copper clearance 0.2mm", "Inner layer PTH
    pad hole to copper clearance 0.3mm".
