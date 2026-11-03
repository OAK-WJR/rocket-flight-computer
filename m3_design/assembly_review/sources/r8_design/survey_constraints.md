# R8 re-layout survey: constraints map

Read-only survey of the owner-accepted R7 board, written as input for a possible R8 re-layout.
- **Board:** `rocket-flight-computer-r7/m3_design/assembly_review/m3.kicad_pcb`. SHA-256
  `c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3`, re-hashed for this survey. Branch m3-assy-r7, commit 431025d.
- **Method:**
  - KiCad 10.0.6 `pcbnew`: a footprint, courtyard, Edge.Cuts and zone dump; U1's pin sides; pyro-rule margins.
  - `tools/fit_check.py` on that board.
  - A scan of the long edges for tab windows.
  - Reading `AGENTS.md`, `docs/REQUIREMENTS.md`, `M3_R7.md`, `R7_VALIDATION.md`, `ORDERING.md`, `MARGIN_PRESCRIPTION.md`, `M3_R4/R5/R6.md`, `m3.kicad_dru`, `tools/check_r7.py`, `tools/fit_check.py`, `m3_design/check_actuators.py`, `tools/critical_reference.py`, `tools/dc_solve.py`, `sources/r7_review/pass1_layout.md`, and the parent `CLAUDE.md` and `docs/VEHICLE.md`.
- **Scripts and raw dumps:** `survey_tools/`, next to this file.
- **Coordinates:** KiCad mm. x = 0 is the left long edge; y = 0 is the aft edge, where the SMA jacks are; y = 118 is the forward edge, at J1. The bore axis is x = 23, with the top face on it.

**Inference** marks anything not measured or not taken from a requirement or a maker document (AGENTS §2.5).

## 0. Status legend used below

| Code | Meaning |
|---|---|
| **FIX** | Position or orientation is set by requirement text or a safety contract. Changing it needs an owner or requirement change. |
| **FIX\*** | Set by a recorded owner decision and enforced in check code, but not written in a requirement line. Change only with the owner's agreement. |
| **RIG** | A member of the CH1 rigid group. It moves only with the whole group: translation, or a 180° turn as R5 did. Its internal geometry is frozen. |
| **LOC** | Locus-constrained: must stay on an edge, in a band, on a side, or at a named pin or part. Free inside that locus. |
| **MOV** | No recorded positional requirement. Place it by electrical adjacency. The local rules still apply: decoupling at its pin, series resistor at the driving end, the bottom-side rules. |
| **MOV\*\*** | Free by the rules, but an existing qualification assumed a particular placement (stated in the row). |

## 1. Summary

**Truly fixed: requirement or safety text**
- **Outline:** 46 mm wide; length ≤ 120 mm, as short as possible (P1). The width sits at the bore limit, so it is fixed.
- **Fit:**
  - Every part and every mated plug fits the Ø50.8 mm bore with a 0.5 mm wall allowance.
  - Top face on the axis, ±0.3 mm (P2). Section 2 gives the height allowed at each x.
- **Supports:**
  - Five M3 supports: four corners and one mid-span. No sixth (P2).
  - ≥ 3.5 mm bottom and ≥ 3.8 mm top clearance around each one (P2, `fit_check`).
  - Two tie holes beyond J122's ends, with a 4 mm under-board tie path (P2, P3).
- **SMA jacks J30/J31:**
  - On the aft edge, top side, rotation 0, ≥ 12 mm apart (F8, F10, `check_r7`).
  - No paste; fitted in the through-hole step (M1).
- **RF strip:**
  - At the aft end, y 0–23.5. F10's text gives these coordinates, for a 46 × 118 board.
  - In1 and In2 GND only; per-layer net lists; module keep-outs; GCPW W 0.30 / G 0.25 mm over In1.
  - Limiter on B.Cu under U30. RF parts ≥ 5 mm from the bucks, the MCU, the crystal and fast digital lines.
  - U30/U31 on the top side.
- **U1 pins:** the radio and GNSS pin contract (F10), the pyro, servo and sentinel pins (`check_actuators`), and the NC pins (`check_r7`).
- **Pyro safety:**
  - The ARM break (AGENTS §2.1) and the pyro bus after the load switch (§2.2).
  - The gate network (§2.4) and DRC rules A–H. These are net-based and hold anywhere on the board.
  - TP122 on the bottom; no test pad on BUS, IGN or OUT.
  - The block conformal-coated (P3).
- **No vias or copper fill under the MEMS sensors** on their component side (P3).
- **Two-sided Standard PCBA** on JLC041611-7628 (M1).
- **≤ 52 extended codes:** there is no margin left. Any new extended part is forbidden. ≤ $126.41 per board (M3).

**Fixed by owner decision (FIX\*)**
- J1 within 25 mm of both CH1 terminal centres: the owner's R6 "battery + CH1 screw-terminal group", in `check_r7`.
- J1's wire entry faces the forward edge.
- The aft RF strip was chosen in R7 pass 1 over a forward one, partly because of J1's entry.
- IMU and barometer on the bottom (R5 L8). The firmware axis map follows from it.

**Rigid (RIG)**
- The CH1 block: J124, J121, Q124, R126–R134, R173, R175, R178, R180, C126–C129, D120 and TP122, with its copper.
- `check_r7` freezes the pairwise distances of seven pads to 0.02 mm, against R5's coordinates: J121.1/.2, J124.1/.2, Q124.5, R134.1/.2. Translation and rotation pass that test; any internal change fails it.
- `check_actuators` pins the PYRO_BLOCK rule area to the exact rectangle x 4–42, y 84–114.4. Even a pure translation needs a reviewed edit of that check, as R5 and R7 did.
- The bore leaves the block about ±1.45 mm of x shift (terminals 14.4 mm tall, fit margin 1.15 mm). In practice it moves only in y, or turns 180°.

**Everything else is movable.** That includes U1 and its whole support set, all power conversion, USB, the camera supply and UART, the sensors (within their side rule), the actuator switch, J122 (within the axis band), J3 and J9 (on a long edge), J123, J2, LEDs, the buzzer and the tooling holes. Only check-code constants and qualification records bind them to R7's spots (sections 12–13).

**What a re-placement invalidates** (section 13):
- The F4 DC solve and the IPC-2152 neck estimate, with the owner's acceptance of C1, which is bound to `c872a3d3`.
- The critical-reference comparison. Its "lost samples" metric is relative to R6 moved +18 mm, so it means nothing after re-placement. It needs an absolute metric.
- The vibration estimate, and the tap-test comparison against it.
- The tab windows, the order-number mark and every coordinate in ORDERING.
- The deviation list. All 45 + 29 + 25 entries are coordinate-bound, and stale allowlist entries fail the gate.
- The pyro block's measured coating and leakage distances, only if the block is not moved rigidly.
- The R4 hot-plug model's premise that the input parts sit at the entry. R7 already violates it: D8, U9 and the damper are 70–85 mm from J1.
- The IMU axis map, if U4 turns or changes side.
- The firmware board binding, always.

## 2. Board envelope

| Item | Rule | Source |
|---|---|---|
| Width | 46.00 mm (± 0.01 in `check_r7` and `fit_check`) | P1 |
| Length | ≤ 120.01 mm. R7 is 118. "As short as possible." The SMA overhang (9.5 mm), mated plugs and coax loop zone (44–48 mm) count in the bay stack, not in the outline. | P1; VEHICLE stack row; operating assumption "Board position" |
| Stack-up | 4 layers, 1.6 mm, 1 oz outer and inner, JLC041611-7628. In1 is the solid GND plane: R7 has no In1 signal copper, keep it so. In2 is split power (BAT_IN, CAM_5V, 3V3, 3V3A) plus GND under the strip. | M1; ORDERING §3; M3_R7 |
| Track, space, via | 0.15 / 0.15 mm; vias 0.3 / 0.5 minimum (0.6 standard); copper ≥ 0.5 mm from edges (SMA pads 0.2 mm by rule); hole clearance 0.25 mm | ORDERING §3; `m3.kicad_dru` |
| Bore fit (`fit_check`) | Margin = 24.9 − hypot(\|x − 23\| + 0.3, \|z\| + 0.3) ≥ 0, for each model box and mated envelope | P2 |
| Height allowed above the top face, by x | x 0: 8.5 · x 1: 10.8 · x 2: 12.6 · x 3: 14.1 · x 4: 15.4 · x 5: 16.6 · x 6: 17.6 · x 8: 19.3 · x 10: 20.8 · x 14: 22.8 · x 18: 24.0 · x 23: 24.6 mm (mirror for x > 23) | computed from `fit_check`'s formula |
| Tall parts that bind | J122 mated (23.5 mm): \|x_c − 23\| ≤ 3.0. J121/J124 (14.4): margin 1.15 mm, about ±1.45 mm of x room. J1 (14.5): margin 6.4. C84 (12.8): centre x 7.4–38.6, margin 0.11 now. C121 (10.5): margin 6.6. J9 mated (10.3): margin **0.03**. J3: 0.89. | `fit_check` run on R7 |
| Bottom depth | No bore limit in practice (≥ 6.9 mm at the edge). The real limit is the sled: standoffs ≥ 3.5 mm. Today the deepest parts are L1 and L3 at 3.0 mm below the bottom face, and the C72–C76/C92 1210s at 2.7 mm. SMA jack lower flanges reach 1.2–1.4 mm below, and the plug nuts 2.6 mm below. Keep bottom parts ≤ 3.0 mm, or the standoffs grow. | ORDERING §7 Sled, Mounting hardware |
| Parts on the bottom | Only SMD parts and test pads. Heavy and tall parts on the top: C84, C121, terminals, J3, J9, J122, J123, LS120, U1, both modules, both jacks. Engineering rule R5 L10; M1's single-final-reflow rule for U30/U31. | R5 L10; ORDERING §4; `check_r7` |
| Bottom placement keep-outs | No bottom part within 1.5 mm of a through-hole pad (pin tails, selective soldering); 3.5 mm of an M3 hole centre; 1.0 mm of a pyro via; 2.0 mm of the bare gate test pad TP122 | R5 L10 |
| Sled | Non-conductive under the whole bottom face, clear of bare pin tails, test pads, TP122 and the BAT_IN, ACT_FET_S and RAW_ACT bottom pours. A tongue carries both SMA plugs 25–30 mm aft. | ORDERING §7; P2/P3 |

## 3. Holes

| Feature | R7 position | Rule |
|---|---|---|
| M3 supports (Edge.Cuts circles r 1.6, milled) | (4, 4), (42.3, 4), (4, 64), (4, 114.4), (42, 114.4) | **P2:** five supports, four corners and one effective mid-span; no sixth.<br>**`fit_check`:** exactly five Ø3.2 supports besides the two declared tie holes; one support within 6 mm of each corner on both axes; one in the middle third of the length (39.3–78.7 at 118 mm); bottom parts and pads ≥ 3.5 mm from each centre; top bodies and exposed pads ≥ 3.8 mm (7 mm washer plus 0.3).<br>**Nylon hardware:** washer ≤ 7.0 mm OD; standoff ≤ 5.5 mm AF, ≥ 3.5 mm tall. ORDERING sized the washer from the nearest pads, which a re-layout changes: C76.2 4.42 mm, TP92 4.60 mm, TP30 5.01 mm.<br>**Recorded in the parent `docs/VEHICLE.md` stack row.** Moving a hole means updating VEHICLE, ORDERING and the vibration estimate.<br>**Positions are movable within P2's rules.** The (42.3, 4) asymmetry is inherited (LED2 clearance in R6). The mid-span hole on the left edge leaves the right edge unsupported for 110.4 mm, and that edge is mode 1 (M3_R7 "Mechanical"). |
| J122 tie holes (Ø3.2, Edge.Cuts) | (21.5, 68.6), (27.0, 82.6) | Beyond both ends of J122, so a tie passes over all four plugs and closes under the board (MARGIN P1-13, P2, P3). Keep a ~4 mm under-board channel between them, with room for the tie head (sled). The coordinates are hard-coded in `fit_check.RETENTION_HOLES` and must be updated if J122 moves. The forward hole sits off the axis because the RAW_ACT column runs there (R5 L11). |
| Tooling holes TH1–TH3 (Ø1.152 NPTH, footprint M3_ToolingHole_JLC) | (44.8, 27.2), (1.4, 82.6), (1.4, 112.0) | Economic-PCBA legacy. Standard PCBA does not need them; JLC's rails carry their own (ORDERING §4). They are 5 mm tab-rule items. `fit_check` treats `TH[123]` as board features. **Removable or movable.** |
| J2 locating holes (3 NPTH, TC2030-IDC-NL) | in J2 | Part of the footprint. Covered and coated before flight with the pads (P3). |
| J3 locating holes (2 NPTH, HRO M-12) | in J3 | 0.20 mm to the internal SMD lands by the HRO layout; scoped DRU rule. |
| In1 launch cut-outs `R7_J30/J31_launch_In1` | x 11.95–13.75 and 30.64–32.44, y 0–4.6 | Centred on each jack axis, In1 only, no fill (`check_r7`). In2 GND must lie under each cut-out ± 0.3 mm (`launch_reference`). |

## 4. Panel rails and tab windows

**Delivery (ORDERING §3)**
- Single PCB, with tab-routed rails (mouse bites) on both long edges. No V-cut: J3 overhangs the left edge by 0.45 mm.
- **Nothing on the aft edge:** the SMA jacks overhang it by 9.5 mm.
- JLC is asked for a forward rail on y = 118 with two 5 mm tabs, or for written confirmation that it assembles without one.

**Rules for any 5 mm window**
- ≥ 1.5 mm from every part and pad (JLC mouse-bite clearance).
- ≥ 5 mm from every capacitor, R166, LED2, the tooling holes and both RF modules.
- JLC's 2 mm keep-out near connectors (the R7 left tab breaks it at 1.83 mm from J3, accepted under DFM-04).
- Off the webs in front of the forward M3 holes: x 2.4–5.6 and 40.4–43.6 at y = 118.
- 5 mm minimum tab width.
- Mouse-bite hole edges ≥ 0.50 mm from copper, with hole centres ≥ 0.30 mm outside the outline.
- JLC suggests 4–6 tabs for a board over 100 mm. R7 has 3 long-edge tabs, plus 2 requested forward ones.

**R7 windows** (ORDERING §3)
- Left x = 0: y 63–68.
- Right x = 46: y 62–67 and y 8–13.
- Forward y = 118 (requested): x 6–11 and 35–40.

**This survey's scan** of the R7 courtyards, against the 1.5 / 5 mm rules:
- Left edge clear: y 0–7, 12–22.5 and 63–68.
- Right edge clear: y 0–21 and 61.5–71.5.
- **No legal long-edge window forward of y ≈ 71.5 on either side.** The parts that block it:
  - Left: J3, TH2, Q120, C120, Q121 and TH3 (parts within 1.5 mm, or capacitors and tooling holes within 5 mm).
  - Right: J2, the camera-buck parts C72–C77, L3, R71 and R72.

**Re-layout lever:** keep a 5 mm × ~5 mm strip clear at both long edges somewhere in y 85–110. That removes the forward-rail dependency, which is an open "before ordering" item (pass1 L4: move C120 about 3 mm inboard, and Q120/Q121 inboard).

## 5. Edges, harness entries and connector directions

| Part | Edge / locus | Entry direction and harness | Fixed by |
|---|---|---|---|
| J30, J31 (SMA) | Aft edge (y = 0), flange on the routed edge, 9.5 mm overhang | Plugs and RG316 run aft. The sled saddle carries each plug 25–30 mm aft. The loops stay off the camera-shroud side, axially staggered (44–48 mm zone). | F8, F10, P1–P3; `check_r7` |
| J1 (battery / switch, green DB128V-4P, rot 180) | Forward end, entry face ~1.9 mm from y = 118 | Entry faces +y. Leads come from the aft battery bay, run past the board and turn back into J1. The 15 A fuse is in-line in the harness. | Owner R6 grouping (`check_r7` 25 mm rule); pass1 floorplan; CPL +180° correction |
| J124 (ARM) | Left side of the CH1 block | Entry faces −x. 6.3–6.9 mm to the wall at 5 mm wire height. Uninsulated ferrules, bent within 2 mm. The fuse holder must stay off the pyro block. | F8; ORDERING §7; `fit_check` SIDE_ENTRY |
| J121 (IGNITER 1) | Right side of the CH1 block | Entry faces +x, same room. Leads go forward to the charge wells. | same |
| J122 (servo 3 × 4) | Axis band, \|x_c − 23\| ≤ 3.0 | Vertical. The mated envelope is 23.5 mm tall. Servo leads come from the fin can by the external raceway (aft). A tie over the plugs through both tie holes. Middle row RAW_ACT (DESIGN_ASSURANCE hard rule: a reversed plug is harmless). | P2/P3; `fit_check` MATED; `check_actuators` rule 7 |
| J9 (camera GH4, keyed, top-entry) | Right long edge (rot −90) | Plug from above, 3 mm straight-wire allocation. Mated margin 0.03 mm: never further out. The camera is in the shroud aft. | F8 (keyed), F10; `fit_check` MATED |
| J3 (USB-C) | A long edge (left now) | Horizontal receptacle. Used only out of the bay; faces the airframe wall when installed. HRO overhang 0.45 mm. | F9; ORDERING §3 |
| J123 (pull-pin, JST PH top entry) | Free; right of the axis now | Latch faces inboard. Wires bend toward the axis and are tied to the sled. RTV, since there is no tie point. | P3; ORDERING §4/§7 |
| J2 (TC2030-IDC-NL) | Free, top side | Probe from above. Bare pads stay coating-free until the last SWD session, then are taped and coated. | P3; AGENTS |

## 6. RF strip: what is hard and what is a code constant

**Hard: requirement text and `check_r7` contracts**
- **Strip extent:** the aft end, x 0–46, y 0–23.5. F10's text names the coordinates for a 46 × 118 board. A different strip depth means editing F10, plus `check_r7.STRIP_Y` and `FENCE_Y`.
- **Per-layer content:**
  - In1 and In2 GND only; vias of strip nets may pass through.
  - F.Cu: GND, GNSS_*, RADIO_*, 3V3_GNSS, 3V3_RADIO and 3V3 only.
  - B.Cu: GND, the limiter nets, RADIO_TXEN, RADIO_DIO1 and RADIO_NSS only. The last three are R7's own documented exceptions, written into the regex `STRIP_B`. A cleaner R8 should not need them.
  - No non-GND pour reaches the strip.
- **Keep-outs (rule areas, by name in `m3.kicad_dru`):**
  - `U30_KEEPOUT` on F.Cu and In1.
  - `U31_KEEPOUT` on all four layers, covering U31's whole 10 × 10 body on B.Cu and In2.
  - In1 and In2 GND under U31's body; In1 GND under U30's keep-out. Sampled every 0.2 mm (`module_ground`).
- **Module rules:**
  - U30 and U31 on the top side (single final reflow; MSL 4 for U30).
  - The MAX-M10S fits U30's land.
  - The E22-900M22S alternate needs a respin (L11).
- **Jacks:** front side, rotation 0, local y = 0 on the aft edge, ≥ 12 mm centre to centre, no paste, "GNSS" / "RADIO" legends within 10 mm and nearer their own jack.
- **GCPW:**
  - W 0.30 mm exactly, 0.25 mm gap to GND (DRU), launch gap 0.30 mm, SMA pads 0.2 mm to the edge.
  - In1 GND under every RF track and pad plus 0.3 mm, except the launch cut-outs.
- **Stitching:**
  - Fence vias at FENCE_Y, ≤ 2 mm apart except the named openings.
  - Line-side gaps ≤ 2.5 mm, except the named ceilings: GNSS west 4.0, east 2.7.
  - F10 accepts the continuous 4.27 / 3.68 mm gaps in its own text.
  - Every outer GND point in the strip within 4.0 mm of copper of a GND via (`rf_gnd_reach`).
- **RF ground pads:** D30.2, D31.2, C303.2, C305.2, C313.2 and C314.2 connect solid, each with a GND via ≤ 0.6 mm away. C302.2 has a thermal relief.
- **Chain topology:** jack → ESD → bias tap (GNSS) → pi network → module. The bias sits on the antenna side. The limiter is on B.Cu under U30.
- **Separation:**
  - ≥ 5 mm from switching regulators, MCU, crystal and fast digital lines. R7's closest: 5.87 mm, FB30 to C6.
  - No RF-part pin on a safety net (pad level).
- **Interface resistors at their driving ends:** R313 and R315 at U1; R314 at U31; R306 at U1; R305 and R307 at U30.

**Code constants that only encode R7's geometry**

| Constant | Value |
|---|---|
| `JACKS` | x 12.85 / 31.54 |
| `U31_BODY` | (24.86, 9.0, 34.86, 19.0) |
| `MODULE_GND` U30 box | (5.36, 11.25, 15.46, 18.65) |
| `FENCE_Y` | 23.3 |
| `FENCE_OPENINGS` | x 6.0–12.7, 19.7–24.1 |
| `STITCH_ACCEPTED` | GNSS west 4.0, east 2.7 |
| `STRIP_B` / `STRIP_VIA` | the regex exceptions above |

They can be changed with a reviewed edit when the strip moves or is redrawn.

**Re-layout freedom in the strip**
- **Rigid copy:** keep R7's qualified strip copper (pass-2 field solve 50.3 Ω, launch 49 Ω, isolation geometry) as one rigid unit. That avoids re-qualifying the RF.
- **Redraw:** or redraw it. Then re-qualify:
  - the field solve and JLC impedance engine run;
  - the stitching gaps, now quoted in F10;
  - the 0.94 mm shunt traces in the VNA model;
  - the S21 isolation geometry (nearest copper 15.45 mm, jacks 18.69 mm).
- **Side swap:** the GNSS/radio side assignment is free in principle (F10 does not fix it). The coax loops only have to avoid the camera-shroud side, and that bay orientation is still open.
- **Deviations to remove:** R7's strip-side deviations are interface topology:
  - the B.Cu NSS hop and the TXEN loop round U31;
  - the detours of GNSS_LNA_EN and GNSS_VCC_RF (limiter under U30, F.Cu pads on its aft row);
  - RADIO_TXEN (U31's pad field holds only GND).

  An R8 aiming at zero exceptions needs a strip interface designed for its MCU-side entry point (section 9).

## 7. CH1 pyro block: what "rigid translation only" means

**What is frozen**
1. **`check_r7` `CH1_PADS`.** It holds R5's immutable pad centres for J121.1 (36, 72.78), J121.2 (36, 77.86), J124.1 (10, 77.86), J124.2 (10, 72.78), Q124.5 (27.4, 72.8), R134.1 (24.975, 77.8) and R134.2 (19.825, 77.8). For all 21 pairs, the on-board distance must equal the R5 distance within 0.02 mm. That allows any rigid motion: translation, rotation, even a mirror, though the flip-side rules forbid a mirror.
   - It fails any relative move of those seven pads: re-spacing the terminals, moving R134 or Q124 inside the block.
   - The other block parts are not in this test. Their spacing is held by DRC rules A–H and by the R4 tuning (item 3).
2. **`check_actuators` 15b.** Exactly one `PYRO_BLOCK` rule area, on F.Cu, In1, In2 and B.Cu, exactly the rectangle (4, 84)–(42, 114.4), restricting nothing.
   - Rule G (gate nets ≥ 0.3 mm from every other live net) applies only inside that area.
   - When the block moves, the area must move with it and the pinned rectangle in `check_actuators.py` must be edited. R5 and R7 both did this as reviewed edits.
   - The `.kicad_dru` itself need not change. Rule G names the area, not coordinates. `DRU_SHA` and `PYRO_RULE_SHA` stay valid if the file is untouched.
3. **R4 passes 2–14 tuned the block's spacing**, and R5 moved it "as one rigid group, turned 180° and 24 mm forward" to keep that work (M3_R5 L3). Margins measured on R7 (this survey, same-layer copper):

   | Rule | Minimum | Measured on R7 |
   |---|---|---|
   | H (pads, solder bridge) | 1.0 mm | **1.025** (Q124.5 to R129.2); 1.027 (R134.2 to R126.2); 1.028 (Q124.5 to R130.1); 1.15 (R134.2 to C129.1) |
   | B | 0.5 mm | 0.670 (Q124.5 to a PYRO1_GATE track) |
   | C | 0.3 mm | 0.377 (PYRO1_BUS track to R132.2) |
   | D | 0.5 mm | 0.546 |
   | F | 0.5 mm | 0.503 (PYRO1_OUT track to the SERVO4_MCU via at (29.8, 92.8)) |
   | A, E | — | no pair within 1.5 / 2 mm |

   The block is tight against rules H and F. Re-arranging it means repeating a spacing pass of R4 quality, not just passing DRC.
4. **Facts that depend on this geometry:**
   - ORDERING §5's coating rationale: "bare gate copper 0.79–1.74 mm from bare bus or 3V3 copper".
   - The coating mask list, which is part-based and survives.
   - TP122's in-pad via, the M2 exception.
   - The RAW_ACT zone notch at (21.0, 85.8) that keeps RAW_ACT off the block.
   - PYRO1_CONT's asserted 1.0 mm to PYRO1_GATE_N.

**What may change**
- The block's position in y, and a 180° turn. After a turn, J124 and J121 swap sides, but each entry still faces its long edge.
- An x shift only within about ±1.45 mm: the terminal fit margin is 1.15 mm.
- No 90° turn: the terminal row spans 26 mm across x, and the entries would face ±y.
- No flip: the terminals are through-hole, and TP122 must stay on B.Cu.
- The block's **exits** (gate and sense lanes to U1, the BUS / RAW / OUT feeds) are free to reroute.
- **J1 must stay within 25 mm of both terminal centres:** J1 moves with the block.
- **Non-block parts inside today's rectangle** need not stay there: J1, Q120/Q121 and the gate drive, the servo chain R150–R157/D121, the camera supply U7/U8/L3/C70–C77/R70–R78, and C150/C151.
- **Distances outside the group:**
  - `check_actuators`/rule H: ACT_GATE and ACT_DRV pads ≥ 1.0 mm from live pads.
  - Bottom parts 1.0 mm from pyro vias and 2.0 mm from TP122.
  - The ARM-link fuse holder must not cross the block (ORDERING §7).
  - Rationale, not a number: keep the transmitter far from the pyro terminals (pass1: radio ≥ 68 mm from J121/J124).
- **A deliberate internal re-layout** of the block, for example to shorten exits or relieve rule H, is possible only as a new spacing qualification:
  - edit `CH1_PADS`, or replace it with a new reference board;
  - re-measure the coating and leakage distances;
  - put it through a review pass with the three-skeptic Critical/Major check.

  Treat it as out of scope unless the owner asks.

## 8. Other safety and electrical rules that act on placement

**Pyro and arming**
- **ARM break (AGENTS §2.1; `check_actuators` 1):**
  - PYRO1_BUS = {J124.1, R134.2, R132.1} and PYRO1_IGN = {J121.2, R134.1}.
  - No copper, part or test point bypasses the ARM link.
  - RAW_ACT ≥ 1.0 mm from bus and igniter copper (rule E).
- **Pyro bus after the load switch (§2.2):** RAW_ACT is Q121's drain; Q120's drain is on BAT_IN; no pyro terminal pin on BAT_IN.
- **Test pads:** none on PYRO1_BUS, IGN or OUT. TP120 (RAW_ACT) and TP121 (ACT_GATE) are allowed.
- **Gate network (§2.4):** the 1k pull-down sits on the MCU side (GATE_N). MARGIN P0-1 "preserve by moving, not deleting".

**MCU pins**
- **Sentinels:** U1.2 PE3, U1.4 PE5, U1.5 PE6, U1.16 PC1 and U1.32 PC4 carry no net. Any pin swap keeps the gate (U1.3), continuity (U1.15) and arm-sense (U1.33) pins flanked by no-net pins (P1-10 adjacency).
- **Servo PWM:** TIM5 on U1.22–25 (PA0–PA3), each with a 10k pull-down. The clamp D121 on SERVO*_MCU (pins 1/3/4/6), the 1k 0805 between clamp and header.

**Power and supply**
- **Load switch:** every net pinned exactly (`ACT_NETS`). C120 gate-to-source, so a shorted C120 turns the switch off.
- **7.7 A feed:**
  - F4: final copper solved and IPC-2152-sized.
  - MARGIN P1-9 (not met in R7): ≥ 10 mm equivalent, mirrored and stitched on L1/L4, 6.1 mm only at pad necks, ideally zero series vias, J1 / Q120 / Q121 / J122 in one corner.
  - The owner accepted R7's 38 / 44 / 30 °C neck rises only "as estimated" for `c872a3d3`.
- **Input:** D8 across BAT_IN–GND; C80/C96 input capacitors; the damper C89 + C95 + R166 (2512 UNI-ROYAL land); the R167 bleed. All pinned by net and LCSC code. TP80 is the "below 1 V before re-plugging" probe point (F9 operating rule).
- **Supply rails:**
  - 3V3A filter R164 2.2 Ω plus C10/C11 (sensor and ADC reference supply).
  - Radio and GNSS each fed from main 3V3 through its own ferrite (F10).
- **Crystal:** In2 keep-out under Y1 and its load capacitors (R5 V1), ≥ 5 mm from RF parts. NDK drive-level bench check (ORDERING §5).

**Routing rules (AGENTS §3, M2)**
- A GND via within 1.5 mm of every critical-net layer change: RF, pyro and arming, crystal, USB data, SPI/QSPI/IMU CS, RADIO_*/GNSS_*.
- 0/45/90° only, and the rest of M2's clean-routing list.
- R7 needed 10 AGENTS §3 exceptions. Their placement causes:
  - **A6, A7, A9–A14:** radio interface via columns too dense for GND vias.
  - **A8:** PYRO1_GATE's layer change inside TP122's pad.
  - **C1:** the three 7.7 A necks.

  Each has a placement-level cure: interface lanes with GND-via room, TP122 reached by a B.Cu stub from a via that has its own GND via, and the battery-corner layout.

## 9. MCU (U1) pin geometry and pin-swap levers

U1 sits top-side at (21.85, 53.5), rotated 90°. Pin sides as placed:

| Side | Pins | Signals |
|---|---|---|
| West (x 14.3), facing the left edge and the power column C84/C80/C96/U9 | 51–75 | **All radio SPI2/BUSY/NRST/DIO1 (51–57) and GNSS (61, 63–65)**; QSPI IO0/1/3 (58–60); USB (70/71); SWDIO (72); VCAP2 (73); 3V3/GND |
| Aft (y 45.95), facing the flash U3, the buck and the RF strip | 26–50 | RXEN (45); camera UART (46/47); LEDs (37/38); QSPI CLK (36); the sense ADC pins (33–35); buzzer (29); **free: PE9 (39), PE11–PE14 (41–44), PA4 (28), PA6 (30); PA7 (31) freed** |
| East (x 29.4), facing J9 and the camera-UART buffer | 1–25 | servos (22–25); HSE (12/13); NRST (14); continuity ADC (15); PULLPIN (8); PYRO1_GATE_N (3); QSPI IO2 (1); sentinels |
| Forward (y 61.05), facing J122, the IMU and the pyro block | 76–100 | SWCLK (76); IMU SPI1 (89–91), IMU_CS (93), INT1 (98); QSPI NCS (92); I2C1 (95/96); BOOT0 (94); CAM_PWR_EN/FAULT; free PA15, PC10–PC12, PD2, PD5, PD7 |

**What follows for routing**
- The radio and GNSS pins exit west, into the power column. That is why R7 needed the left-edge B.Cu corridor, the F.Cu band and its GND-via-less via columns.
- QSPI spans three package sides: IO0/1/3 west, IO2 east (pin 1), CLK aft, NCS forward. That is set by the silicon's alternate functions.

**Levers (each a requirement or schematic change, with a new firmware binding)**
- **Rotate or move U1** with the pin contract unchanged. No rule fixes U1's position. F10 only fixes which pins carry which signals.
- **Re-assign the radio SPI to SPI4 on the aft-facing free pins.**
  - **Inference, from memory of the STM32H7 alternate-function map. Verify against DS12110 Tables 9–10 before using:** SPI4 on PE11 NSS, PE12 SCK, PE13 MISO and PE14 MOSI. These are pins 41–44, free today, on U1's aft face toward the strip.
  - The GNSS UART could similarly move to an aft-side UART, for example UART7 on PE7 / PE8 (pins 37/38, today the LED lines).
    Same Inference flag: verify the alternate functions, and the TIMEPULSE input-capture pin, in DS12110 first.
  - This rewrites F10's pin contract (owner, 2026-10-15 text), `check_r7.RF_MCU_PINS`/`FREED_NC`, the EXTI analysis in F10, and the firmware binding.
  - PE15 (45, RXEN) is already aft.
- **Pins that must stay as they are:**
  - Do not put the GNSS on PA9/PA10 (ROM bootloader USART1; F10).
  - Do not use the pyro sentinels PE3, PE5, PE6, PC1 and PC4. PE5 and PE6 are SPI4 alternates, but they are sentinels.
  - Keep PE10 (40) and PE0 (97) NC (`check_r7.OTHER_NC`, `check_actuators`).
  - Keep IMU_INT1 on PE1 (98).
  - Keep the EXTI-sharing constraints of F10 in any new map.

## 10. Bottom-side and sensor rules

| Item | Rule | Source |
|---|---|---|
| U4 IMU | Bottom side, rotation 0 today. KiCad mirrors bottom parts in board y, so roll = +gyro_Y, thrust +a_Y, Z out of the bottom face. A new rotation or side rewrites the axis table in M3_R5 §3 and the firmware binding (bench sign check either way). | R5 L8, M3_R5 §3; AGENTS table |
| U4 surroundings | No via or copper fill under it on B.Cu (`IMU_body_B`, `IMU_no_internal_tracks` areas). Keep about 3 mm coating-free round it on both faces. No staking epoxy near it (C121's staking is W and N only because U4 and U5 sit under C121 today). | P3; ORDERING §5 |
| U4 distance from the roll axis | 13.0 mm in x today. Centripetal acceleration ω²r: 1.4 g at 1850 °/s and about 6.5 g at 4000 dps (Calc from ω²r; FMEA F-5 notes that it pollutes the velocity integral). Placing U4 near x = 23 is a free improvement (Inference: no requirement asks for it). | M3_R5 §3; F1/F2 |
| U5 barometer | Bottom side: the port faces the sled, away from the top LEDs. Black foam over it; the bay vented. No tracks between its pad rows (`BARO_*` areas). It takes two reflows (TE confirmation pending). Never cleaned or washed. | R5 L8; operating assumptions; ORDERING §4 |
| TP122 | Bottom only. Coated last. Bottom parts ≥ 2.0 mm away. | `check_actuators` 4; R5 L10; ORDERING §5 |
| Bare test pads | 1.0 mm foreign-copper clearance on their exposed face (`check_r7.foreign_clearances`). Exposed bottom lands count for standoff clearance (`fit_check`). | `check_r7`; `fit_check` |
| Deep parts | L1 and L3 (3.0 mm below the face), the 1210 caps (2.7 mm), D8 (2.15 mm). All must clear the sled plate; ≤ 3.0 mm keeps the ≥ 3.5 mm standoffs. | ORDERING §7 |

## 11. Per-footprint map (all 252 footprints)

**Columns.** Position = current R7 centre (x, y), rotation and side. Status = section 0. Side: T, B or T/B (free).

**Rotation**
- "free" for passives.
- "edge-set" where an edge or entry direction sets it.
- "group" for RIG.

**Rows not shown here.** MOV rows still obey the local rules:
- decoupling at its pin;
- series resistor at the driving end (`check_r7.SERIES`);
- C29 ≤ 2 mm from U3.8 with a ≤ 3 mm route; C100 and C93 at U12 (`check_r7`);
- the bottom keep-outs of section 2;
- the buck loop topology of the Diodes and TI layouts;
- F10's 5 mm RF separation for every switching part and fast digital line.

#### RF strip: GNSS chain (F10; check_r7)

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| J30 (12.85, 0, 0, F) | FIX | T | 0 only | aft edge, local y=0 on Edge.Cuts y=0; no paste, THT step; x is a check_r7 constant (JACKS 12.85), not a requirement; >= 12 mm c-c to J31; "GNSS" legend < 10 mm |
| D30 (13.175, 5.2, 0, F) | LOC | T | free | ESD shunt on the line at the jack; D30.2 solid GND + GND via <= 0.6 mm (rf_grounds) |
| L30 (12.387, 6.18, 0, F); C302 (10.58, 6.18, 180, F) | LOC | T | free | bias tap on the antenna side of the pi network (F10); C302 at L30 cold end, thermal relief |
| C303 (11.49, 7.13, 180, F); R304 (13.28, 7.13, 0, F); C305 (15.07, 7.13, 0, F) | LOC | T | free | pi network between bias tap and RF_IN; C303/C305 DNP, no paste; shunt GND pads solid + via |
| U30 (10.41, 14.95, 90, F) | LOC | T | RF pin to jack | top only (check_r7, M1 last reflow); inside y 0-23.5; U30_KEEPOUT F/In1 (coordinates hard-coded in check_r7 MODULE_GND); MAX-M10S same land; >= 5 mm from bucks/MCU/crystal/fast digital |
| Q30 (4.75, 11.75, -90, B); Q31 (12, 14.25, 0, B); Q32 (8.75, 13.25, 90, B); R300 (8.75, 10.75, 180, B); R301 (5.75, 14.25, 0, B); R302 (7.75, 15.75, 0, B); R303 (12.25, 11.75, 90, B); C304 (7.74, 16.9, 0, B) | LOC | B | free | antenna-bias limiter on B.Cu under U30 (F10 text); C304 DNP no paste |
| FB30 (11.58, 24.5, 90, F); C300 (10.88, 22.62, 180, F); C301 (13.16, 21.88, 0, F) | LOC | T | free | GNSS 3V3 feed in the strip at U30 VCC; FB30 <= 0.2 ohm path (F10) |
| R305 (7.11, 22.45, -90, F); R307 (9, 22.45, -90, F) | LOC | T/B | free | series R nearer U30 than U1 (check_r7 SERIES: driving end) |
| R306 (2.2, 47.5, 90, B) | LOC | T/B | free | series R nearer U1 than U30 (MCU TX drives) |
| TP30 (2, 9.6, 0, F) | MOV | T/B | - | bare SAFEBOOT_N pad; 1.0 mm foreign-copper clearance on its exposed face (check_r7) |

#### RF strip: radio chain (F10; check_r7)

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| J31 (31.54, 0, 0, F) | FIX | T | 0 only | aft edge as J30; x constant 31.54 in check_r7; "RADIO" legend |
| D31 (31.865, 5.2, 0, F) | LOC | T | free | ESD shunt at the jack; solid GND + via <= 0.6 mm |
| C313 (30.18, 7.6, 180, F); R316 (31.97, 7.6, 0, F); C314 (33.76, 7.6, 0, F) | LOC | T | free | pi network, C313/C314 DNP no paste |
| U31 (29.86, 14, 180, F) | LOC | T | ANT pin to jack | top only; inside strip; U31_KEEPOUT all four layers over the whole 10x10 body (U31_BODY hard-coded in check_r7); nothing but GND under it |
| FB31 (35.1, 21.5, 90, F); C310 (37.78, 19.6, 0, F); C311 (37.2, 16.54, 0, F); C312 (37.2, 17.5, 0, F) | LOC | T | free | radio 3V3 feed at U31 VCC |
| R314 (23, 12.73, 180, F) | LOC | T/B | free | series R nearer U31 (MISO driven by U31) |
| R313 (5.7, 44, 90, B); R315 (5.2, 42, 90, B) | LOC | T/B | free | series R nearer U1 (SCK/MOSI driven by U1) |
| R310 (24.2, 20.82, 90, F); R311 (37, 14.43, -90, F); R312 (25.6, 7, 90, F) | MOV | T/B | free | NSS pull-up to 3V3_RADIO, NRST 2k pull-down (holds radio in reset: F10 safety), RXEN pull-down |

#### CH1 pyro block (rigid group; F7/F8; check_r7 CH1_PADS, check_actuators, m3.kicad_dru)

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| J124 (10, 93.32, 90, F); J121 (36, 93.32, -90, F) | RIG | T | group 0/180 | black DB128L 2P, ARM / IGN legends; entries face the long edges (J124 -x, J121 +x), 6.3-6.9 mm wire room to the wall; 14.4 mm tall: fit margin 1.15 mm, so the block may shift at most about +-1.45 mm in x; pads in CH1_PADS |
| Q124 (27.4, 90.8, -90, F); R134 (22.4, 95.8, 180, F) | RIG | T | group | Q124.5 and R134.1/.2 in CH1_PADS (pairwise distances frozen to 0.02 mm) |
| R126 (21.6, 91.4, -90, F); R127 (21.9, 88.4, 90, F); R128 (24.7, 91.5, 90, F); C126 (23.4, 91.4, 90, F) | RIG | T | group | gate network (AGENTS 2.4): series 220R, 1k pull-down on GATE_N, 10k + 220 nF gate-source; rule B/G/H spacing |
| R129 (28.3, 87.9, 180, F); R130 (26.4, 87.9, 180, F); R131 (30.15, 86.1, 180, F); R173 (30.15, 87.35, 180, F); R178 (27.44, 86.75, 180, F); C127 (23.9, 87.2, 180, F); C128 (28, 93.85, 180, F) | RIG | T | group | continuity divider (split top), cold pull-up, drain cap; rule C/H |
| R132 (16.17, 96.5, -90, F); R133 (16.85, 92.4, 180, F); R175 (16.17, 98.25, -90, F); R180 (16.85, 93.55, 180, F); C129 (19.2, 91.7, 90, F) | RIG | T | group | arm-sense divider; rule C/H |
| D120 (32, 83, -90, F) | RIG | T | group | BAT54A cold pull-up (FMEA H-1) |
| TP122 (20.45, 92.4, 0, B) | RIG | B | group | bare gate test pad, must stay on B.Cu (check_actuators); in-pad via is a named M2 exception; bottom parts >= 2.0 mm (R5 L10) |

#### Pyro sense paths outside the block

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| R168 (32.6, 52.9, 180, B); R170 (24.4, 46, 90, B); R172 (22.6, 48.4, 0, B) | LOC | T/B | free | 4.7k series at each ADC pin (F8): at the MCU end of the sense lane |
| R177 (10.4, 65.1, -90, F); R124 (11.8, 66.4, 0, F); R125 (11.8, 65.1, 180, F); R182 (11.8, 64.1, 180, F); C122 (13.75, 68.1, -90, F) | MOV | T/B | free | RAW_ACT_SENSE divider (2x5.1k over 2x2k): rule A2 0.3 mm, rule H 1.0 mm RAW_ACT pad to sense pads (now 1.277 mm) |

#### Battery entry and actuator switch (7.7 A path; F4, F8, F9)

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| J1 (23, 110.4, 180, F) | FIX* | T | 180 (entry +y) | green DB128V 4P; within 25 mm of both CH1 terminal centres (check_r7; owner R6 "battery + CH1 screw-terminal group"); entry faces the forward edge; CPL +180 correction; 14.5 mm tall (near axis) |
| Q120 (4, 91, 180, B); Q121 (4, 105.3, 0, B) | LOC | T/B | free | on the J1 -> J122/J124 path; Q121 drain = RAW_ACT feeds pyro bus via J124.2 (AGENTS 2.2); now at the left edge (block forward long-edge tab, ORDERING L4) |
| Q122 (10.15, 107.6, -90, B); R120 (5.6, 96, 0, B); R121 (9.75, 105.1, 0, B); R122 (11.75, 104.6, -90, B); R123 (10.65, 110.1, 180, B); C120 (3.5, 100, 0, B); TP121 (7, 99.2, 0, B) | MOV | T/B | free | load-switch gate drive beside Q120/Q121; ACT_GATE/ACT_DRV pads 1.0 mm from live pads (rule H); C120 gate-source (check_actuators 8b) |
| C121 (32.9, 75.4, 0, F) | LOC | T | free | 470 uF RAW_ACT can, 10.5 mm tall, staked; near J122; U4/U5 currently under its body (staking W/N only) |
| C150 (15, 87, 0, B); C151 (15, 84.7, 0, B); TP120 (9, 87, 0, B) | MOV | T/B | free | RAW_ACT bulk and bare test pad (TPs forbidden on BUS/IGN/OUT only) |
| J122 (23, 75.7, 90, F) | LOC | T | 90 (rows along y) | 3x4 servo header; mated 23.5 mm envelope needs \|x_c - 23\| <= ~3.0; middle row RAW_ACT; tie holes beyond both ends (fit_check RETENTION_HOLES hard-coded); 4 mm under-board tie channel |
| R150 (25.2, 95.2, 180, B); R151 (15.5, 89.3, 180, B); R152 (31.2, 98.1, 180, B); R153 (26.1, 98.4, 90, B); R154 (29.8, 95.6, -90, B); R155 (18.6, 89, 0, B); R156 (32.2, 100.3, -90, B); R157 (26.1, 101.5, -90, B); D121 (32, 82.4, 0, B) | MOV | T/B | free | servo chain MCU -> 10k pull-down + SRV05-4 clamp -> 1k 0805 -> header (netlist order, check_actuators 7) |

#### Input protection and logic power path (F6, F9)

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| D8 (11.9, 31.2, 90, B); C80 (9.15, 52.1, 180, B); C96 (8.3, 56, -90, B); C89 (5.9, 29.6, -90, F); C95 (7.1, 34.6, 90, F); R166 (2.4, 32, 90, F); R167 (6, 55.3, -90, B); TP80 (3.8, 54.4, 0, B) | MOV** | T/B | free | TVS, input caps, RC damper, bleed: the reverse-hot-plug model (M3_R4 X1/Y1) is lumped; R4/R5 had them at the entry; R7 has them 70-85 mm from J1. R166 is a 5 mm tab-rule item, UNI-ROYAL 2512 land |
| U9 (11.2, 40.6, 90, F); R81 (7.6, 41.3, 180, F); R82 (8.63, 43.25, 180, F); R83 (5.35, 43.25, 180, F); R84 (10.65, 37.3, -90, F); C87 (7.25, 39.7, 180, F); C88 (9.15, 38.85, 90, F); C81 (12.6, 37.15, 90, F); R89 (12.8, 43.1, 180, F); TP84 (1.5, 41, 0, F); TP89 (8.1, 33.6, 0, B) | MOV | T/B | free | TPS25947 eFuse with its network at its pins (TI; R5 L7); TP84 top (top-only net) |
| R80 (16.3, 24.45, 0, B); R165 (3.3, 38.3, 90, F) | MOV | T/B | free | 470k legs on each side of the external switch (F9, check_actuators 12): logically at J1.3/J1.4; R7 has R80 at y 24 (86 mm from J1) |
| D9 (16, 31.2, 0, F); C82 (14.95, 40.35, 0, F); R92 (14.4, 39.5, 90, B) | MOV | T/B | free | eFuse OUT -> RAW_PROTECTED |
| U11 (29.2, 28.2, 0, B); R86 (30.7, 33.1, -90, B); R87 (26.8, 38.1, 0, F); R88 (29.4, 38.8, -90, F); R91 (29.9, 38.6, 0, B); C85 (28.2, 36.7, 180, B); C97 (24.925, 27.25, 180, B); C98 (33.875, 26.45, 0, B); C99 (28.925, 29.95, 0, F); TP82 (23, 60.5, 0, B); TP83 (16, 29.5, 0, B); TP87 (18.9, 58, 0, B) | MOV | T/B | free | TPS2121 power mux; R86 close to ILIM pin (TI) |
| C84 (7.5, 51.3, 90, F) | LOC | T | free | OS-CON hold-up, tallest part 12.8 mm: centre x 7.4-38.6 for the bore; staked; now margin 0.11 mm |
| U2 (18, 33, 0, B); L1 (24.5, 33, 0, B); C5 (17.5, 35.65, 180, B); C6 (19.2, 29.4, 0, B); C7 (20.8, 33, -90, B); C8 (28.6, 33.6, 90, B); C9 (23.1, 36.6, 180, B) | MOV | T/B | free | 3V3 buck: compact switching loop; >= 5 mm from RF parts (F10); L1 the deepest bottom part (3.0 mm below the face) |
| R60 (32.1, 37, 0, B); R61 (33.5, 32.5, 90, B); C60 (35.1, 30.9, 90, B); R62 (33.7, 59.2, 90, B); R63 (35.4, 59.6, 0, B); R164 (32.3, 45.3, 90, B); C10 (40.1, 46.4, 90, B); C11 (40.1, 55.6, -90, B); TP85 (16.4, 58, 0, B); TP86 (23.7, 58, 0, B) | MOV | T/B | free | sense dividers, 3V3A filter |

#### USB (F9)

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| J3 (4.6, 75.3, -90, F) | LOC | T | edge-set | USB-C on a long edge (used out of the bay; faces the airframe wall), HRO overhang 0.45 mm, no V-cut; JLC 2 mm tab keep-out |
| D4 (11, 74, 0, B); R7 (13.7, 74.05, 0, B); R8 (9.6, 79, 0, B) | LOC | T/B | free | ESD and CC pull-downs beside J3 |
| U10 (15, 80.6, 0, B); R85 (7, 83, 180, B); C28 (6.8, 75.6, 90, B); C83 (14.1, 82.15, 0, F); C86 (17.5, 82.15, 0, F); R90 (16.3, 70, 0, B); R9 (14.5, 72.1, 90, B); R110 (16.1, 72.7, -90, B); TP92 (8, 68, 0, B) | MOV | T/B | free | TPS2553 limiter and VBUS sense |

#### MCU core

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| U1 (21.85, 53.5, 90, F) | MOV | T | 0/90/180/270 | no positional requirement; top (fine pitch, heavy-on-top rule R5 L10); pin contract fixed (F10 RF pins, check_actuators pyro/servo pins and sentinels) |
| Y1 (25.6, 53.75, 180, B); C25 (27.12, 57.1, 0, B); C26 (22.6, 52.88, 90, B) | LOC | T/B | free | at HSE pins 12/13; In2 keep-out under the crystal (R5 V1); >= 5 mm from RF |
| C13 (29.4, 57.4, -90, B); C14 (29.4, 54.9, 90, B); C15 (27.8, 45.9, 0, B); C16 (16.3, 45.9, 0, B); C17 (14.5, 60.3, -90, B); C18 (27.4, 61, 180, B); C21 (29.4, 49.6, 90, B); C22 (32.3, 48.6, 90, B); C23 (32.3, 55, -90, B); C24 (29.4, 47.5, 90, B); R5 (24.4, 63.6, 180, B) | LOC | T/B | free | decoupling / NRST cap / BOOT0 pull-down at their pins (ORDERING NRST gate probes C24.1 with C15.1 "beside it") |
| C19 (18.9, 45.9, 0, B); C20 (16.7, 60.8, 0, B) | LOC | T/B | free | VCAP1/VCAP2 at pins 48/73 (R7: 4.9x / 4.2x detours, A-list) |
| U3 (24.6, 34, 90, F); C29 (19.2, 36.5, -90, F); R10 (27.4, 39.7, 0, F) | MOV | T/B | free | QSPI flash; C29 <= 2 mm from U3.8 with <= 3 mm direct route (check_r7) |
| J2 (43, 76.65, 90, F) | MOV | T | free | TC2030-IDC-NL bare pattern, 0.508 mm foreign-copper rule, 3 locating NPTH, coated before flight; avoid in-pad vias (R7 J2.1 via is a named M2 exception) |

#### Sensors (F1-F3, P3)

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| U4 (36, 78.3, 0, B) | LOC | B | 0 (or record) | IMU on the bottom (R5 L8): roll = +gyro_Y at rot 0; a rotation/side change rewrites the axis map; no via/fill under it on B.Cu (P3, IMU_* rule areas); 3 mm coating-free; 13 mm off axis now |
| U5 (36.3, 73, 0, B) | LOC | B | free | barometer on the bottom (port to the sled, away from LEDs, foam); no tracks between pad rows (BARO_* areas) |
| R11 (36.5, 81.2, -90, B); R12 (32.7, 73.6, 90, B); R13 (32.2, 75.3, 180, B); R64 (39.2, 76.2, 0, B); C30 (39.1, 78.8, 0, B); C31 (39.1, 77.5, 0, B); C32 (32.3, 71.9, 180, B) | LOC | T/B | free | local to U4/U5 (C30/C31 to pins on F.Cu, C32 beside VDD: R4 V8) |

#### Camera (F9, F10 GH4)

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| J9 (42.7, 42, -90, F) | LOC | T | edge-set | keyed GH4 at a long edge; mated envelope margin 0.03 mm: may move inward/along y, not outward |
| U7 (38.2, 86.65, -90, B); U8 (41.8, 94.4, 0, B); L3 (41.8, 100.1, -90, B); C70 (32.4, 86.5, -90, B); C71 (35.7, 84.9, 90, B); C72 (41.8, 90.8, 0, B); C73 (42.4, 87.4, 0, B); C74 (44.7, 94.6, -90, B); C75 (41.8, 105.5, 0, B); C76 (41.8, 108.9, 0, B); C77 (43.7, 98.6, 0, F); R70 (32.4, 89.9, -90, B); R71 (43.7, 93.9, 0, F); R72 (43.7, 92, 0, F); R74 (36.7, 85.8, 90, F); R75 (34, 85.7, 180, F); R76 (20.8, 97, 90, B); R77 (38.6, 85.4, -90, F); R78 (32.4, 104.5, 90, B); TP70 (38.5, 83.2, 0, B); TP71 (32.5, 95.5, 0, B); TP72 (33.5, 107.5, 0, B); TP73 (26, 92.5, 0, B); TP74 (23.5, 98, 0, B); TP81 (39.5, 81, 0, B); TP88 (23, 100.6, 0, B) | MOV | T/B | free | camera eFuse + 5 V buck: compact loop; >= 5 mm from RF; C72-C76/L3 2.7-3.0 mm below the face (sled); TP74/TP88 are the GND probe points (ORDERING) |
| U12 (41.8, 51, 90, B); C93 (43, 47.6, 0, B); C100 (42, 53.9, 0, B); R100 (43, 56.65, 0, B); R101 (44.4, 51.3, -90, B); R102 (43, 45.7, 0, B); TP75 (43, 64, 0, B); TP76 (44.5, 59, 0, B); TP91 (38, 62.5, 0, B) | MOV | T/B | free | UART translator; C100/C93 within 3 mm of U12.3/U12.7 with direct copper <= 3 (same side) / 5 mm (check_r7 camera_bypass) |
| U13 (41.5, 31.5, 0, B); C90 (40.2, 37.3, 0, B); C91 (43.3, 36, -90, B); C92 (41.2, 27.7, 180, B); R103 (37.8, 28.6, -90, B); R104 (32.6, 30.8, 180, B); R105 (32.2, 29.1, 90, B); C94 (34.4, 28.4, 0, B); TP90 (40.5, 34.5, 0, B) | MOV | T/B | free | camera-IO LDO and 5 V sense |

#### Pull-pin, buzzer, LEDs (F9)

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| J123 (36, 34.6, 0, F) | LOC | T | latch inboard | JST PH top entry, mated 9.5 mm envelope; RTV retention |
| R160 (32.9, 26.6, -90, F); R161 (34.6, 26.8, 180, F); C160 (34.9, 28.5, -90, F); D122 (32.5, 29.6, 90, F) | MOV | T/B | free | pull-pin input network |
| LS120 (14.1, 76, 0, F); Q123 (10.6, 82.2, 0, B); R162 (5.3, 85.1, 0, B); R163 (11.6, 79.4, 90, B); D123 (13.7, 79.8, 0, F) | MOV | T* | free | buzzer top (model < 8.5 mm, check_r7); driver |
| LED1 (38.3, 26.8, 90, F); LED2 (41.3, 26.5, 0, F); R32 (37.6, 29.7, 0, F); R33 (41.7, 29.4, 0, F) | MOV | T | free | status LEDs (top); LED2 is a 5 mm tab-rule item |

#### Board features

| Refs (x, y, rot, side now) | Status | Side | Rotation | Rule / why |
|---|---|---|---|---|
| TH1 (44.8, 27.2, 0, F); TH2 (1.4, 82.6, 0, F); TH3 (1.4, 112, 0, F) | MOV | - | - | JLC tooling holes 1.152 NPTH; not needed for Standard PCBA (ORDERING); >= 5 mm from tab windows; removable |

## 12. Check-code constants that encode R7 geometry

None of these is a requirement. A re-placement edits them as reviewed changes and records each edit.

| File | Constant / test | R7 value | Changes when |
|---|---|---|---|
| `tools/check_r7.py` | `JACKS` | J30 x 12.85, J31 x 31.54, on outline y min | jacks move in x |
| | `STRIP_Y`, `FENCE_Y`, `FENCE_PITCH`, `FENCE_OPENINGS` | 23.5; 23.3; 2.0; x 6.0–12.7 and 19.7–24.1 | strip depth or interface entry changes |
| | `U31_BODY`, `MODULE_GND` | (24.86, 9, 34.86, 19); U30 box (5.36, 11.25, 15.46, 18.65) | modules move |
| | `STITCH_ACCEPTED`, `STITCH_GAP` | GNSS west 4.0, east 2.7; 2.5 | RF chain redrawn |
| | `STRIP_B`, `STRIP_VIA` regexes | include RADIO_TXEN, RADIO_DIO1, RADIO_NSS (R7 exceptions) | cleaner interface (tighten them) |
| | `CH1_PADS` | R5 pad centres; rigid motion allowed | never, for a rigid move |
| | J1 ≤ 25 mm from both CH1 terminals | — | owner decision only |
| | C29 / U3.8 ≤ 2 mm, route ≤ 3 mm; C100 / C93 at U12 | — | never: placement must satisfy them |
| | `SERIES` driving-end test | — | never: placement must satisfy it |
| `m3_design/check_actuators.py` | PYRO_BLOCK rectangle | (4, 84)–(42, 114.4), exact | block moves |
| | `DRU_SHA`, `PYRO_RULE_SHA` | file and rule-text hashes | only if `m3.kicad_dru` is edited (RF-rule or keep-out changes) |
| `tools/fit_check.py` | `RETENTION_HOLES` | (21.5, 68.6), (27.0, 82.6) | J122 moves |
| | Corner and middle-third support test, `MATED` envelopes, `SIDE_ENTRY` | — | rules, not positions |
| `tools/route_check.py` | `ALLOWLIST` (45), `LEFTOVERS` (29), with coordinates and measured lengths | R7 | **always.** An entry that matches nothing fails the gate, so R8 starts with both empty. The target is to keep them empty. |
| `m3_design/r7_post.py` | Order-number mark search seed (23, 94); `LEGEND_REACH` 6 mm | — | new board |
| `m3_firmware/build.py` / `assembly_binding.py` | Board SHA-256 binding and pin table | R1 binding (R7 has none yet) | any PCB change (AGENTS §3) |

## 13. Qualifications a re-placement invalidates

| Qualification | Bound to | Invalidated by | What an R8 must redo | Survives? |
|---|---|---|---|---|
| **F4 DC solve of the 7.7 A copper** | R7 final board SHA. 0.05 mm: RAW_ACT Q121:5–9 → J122:2,5,8,11 3.71 mΩ; BAT_IN J1:1 → Q120:5–9 3.03 mΩ; ACT_FET_S Q120:1–3 → Q121:1–3 1.16 mΩ. Plus about 20 logic/camera/3V3 rows. | Any change to those nets' copper. F4's text names "the R7 solve". | Re-run `tools/dc_solve.py` (pad-set based, reusable; the board's own stack-up). Rewrite F4's line for R8. | Method yes; numbers no |
| **IPC-2152 neck estimate and the owner's C1 acceptance** | `c872a3d3`; necks 3.00 / 2.65 / 3.82 mm, rise 38 / 44 / 30 °C (accepted "as estimated") | Any change. The cut-analysis script `f8/dc_ipc.py` is in a past session scratchpad, **not in the repo**. | Re-do the cut analysis (rebuild the script from M3_R7's method text) and get a new owner decision. Or meet MARGIN P1-9 (≥ 10 mm equivalent, mirrored; zero series vias) with a battery-corner layout, which removes the C1 deviation. | No |
| **Critical-reference sampling** | `tools/critical_reference.py` compares the base (R6, moved +18 mm) with the candidate. R6 accepted 0 lost; R7 recorded 603 lost, 882 new. | Any re-placement: the "lost vs R6" metric is positional and becomes meaningless. | Replace it with an absolute metric on R8 itself: every 0.01 mm sample of the 14 critical nets (plus the extended set) referenced, with every unreferenced sample listed. Recommendation (Inference): 100 %, no list. Include USB_DM over the In2 BAT_IN/3V3 gap, R7's inherited 18.6 mm. | Method partly; base no |
| **Pyro spacing** | DRC rules A–H: net-based, valid anywhere. `CH1_PADS`: R5 geometry. PYRO_BLOCK rectangle. R4's tuned distances (rule H minimum 1.025 mm). ORDERING's leakage distances (0.79–1.74 mm, bare gate copper to bus/3V3). | **Rigid move:** only the rectangle constant and the exit routes; DRC re-runs. **Internal change:** everything. | Rigid move: edit the rectangle, re-run DRC and `check_actuators`, re-measure the exits' clearances (rule F on the SERVO4_MCU via is now 0.503 mm). Internal change: a new R4-style spacing pass, a new `CH1_PADS` reference, and re-measured coating and leakage distances. | Yes if rigid |
| **Bench-test and procedure assumptions (ORDERING §3–§7)** | R7 coordinates and adjacencies. | Any re-placement. | Regenerate ORDERING. See the list after this table. | Topology-only gates survive |
| **Reverse hot-plug model (M3_R4 X1/Y1, F9)** | Lumped harness (0.1–2 µH, ≥ 0.03 Ω) and part values. R4/R5 had D8, the damper and U9 at the entry (Inference: board copper not modelled). R7 has J1 → U9 13.6 mΩ over about 71 mm of In2, J1 → D8 80 mm. | Already strained in R7. A re-layout either restores the premise (input parts at J1) or keeps it strained. | Group J1, D8, C80/C96, C89/C95/R166, R167 and U9 together. Otherwise add the board inductance to the model (Inference). Re-run the bench hot-plug test either way. | Model yes; premise placement-dependent |
| **RF qualification** (pass-2 field solve 50.3 Ω, launch 49 Ω, return loss ≥ 19 / 25 dB inferred; stitching gaps; 5.87 mm minimum separation; nearest RF copper 15.45 mm, jacks 18.69 mm; control lines 3.06–4.88 mm from U30) | The R7 strip copper | Redrawing the strip or the modules. A rigid copy keeps it, but the separations to the bucks/MCU/crystal must be re-measured. | `check_r7` re-runs automatically. Re-do the field solve and the stitching review if redrawn. F10's quoted 4.27 / 3.68 mm gaps change text. VNA tuning model (shunt traces). | Yes if rigid copy |
| **Mechanical: vibration f1 estimate** (221–533 Hz with plugs carried, computed on the pass-2 board; 100 g strains: U31 560, U30 538, U4 688, J121 873 µε) | Hole positions, outline, heavy-part masses and positions | Moving holes, the outline or heavy parts | Re-run the plate model (pass2_mechanical method). The tap check compares against the new estimate. A sixth support stays declined (P2); moving the mid-span support or the right edge's support is an owner topic. | No |
| **`fit_check` figures quoted in documents** (C84 0.11 mm, J9 mated 0.03, J122 mated 0.71, J3 0.89, wire room 6.3–6.9 mm, L1 deepest 3.0, nearest pads to holes for the 7 mm washer) | R7 | Any move | Automatic re-run. Update REQUIREMENTS, ORDERING and VEHICLE text. | Tool yes; numbers no |
| **IMU axis map** (roll = +gyro_Y, thrust +a_Y, Z out of the bottom face) | U4 bottom, rotation 0 | Rotating U4 or changing its side | Rewrite the M3_R5 §3 table and the firmware binding; bench sign check | Yes if rotation 0 and bottom kept |
| **Firmware binding** | Board SHA | Always | New binding (AGENTS §3) and a pin-table review, more so if pins are swapped | No |
| **Deviation list and owner acceptance** (45 allowlist, 29 leftovers, 25 C rows, 252 info instances, 10 AGENTS §3 items) | `c872a3d3` | Any copper change | R8 goal: empty allowlist and leftovers, no C rows. Whatever remains needs a new dated owner acceptance (M2). | No |
| **Review history** (passes 1–8, 0 Critical/Major on R7) | R7 | Any change | A new independent review loop (memory: stop at no Critical/Major with the gate at zero) | No |
| **Fab package and manifest; CPL orientation corrections** | R7 BOM, CPL, Gerbers | Any change. Rotations change CPL rows; the per-footprint corrections stay valid. | `export_fab.py`, `fab_manifest.py`, `jlc_orient.py --verify-cpl` | Per-footprint corrections yes |
| **Cost and code count (M3)** | R7 BOM: 92 codes, 52 extended, $105.98 | Only BOM changes | Unchanged if the BOM is unchanged. Any new extended code breaks the 52 limit. New basic codes add $1.53 / 5 per board each. Re-run `jlc_cost.py` within 24 h of ordering. | Yes if the BOM is unchanged |
| **Circuit-level analyses** (F6 ride-through, F7 fire budget, F8 divider faults, limiter currents, gate-network margins, MARGIN tables) | Schematic values | Not by placement. The F7 harness budget and the limiter thermal estimate (Q30 on 0.2 mm B.Cu, 2–3× RθJA) are layout-touched. | Q30 thermal note; F7 "revalidate on the final copper" | Yes, mostly |
| **REQUIREMENTS and VEHICLE text carrying R7 coordinates** | F10 (strip y 0–23.5 "of a 46 × 118 board", gaps 4.27 / 3.68 mm); M2 (J2.1 via at (44.035, 77.92) named exception, TP122 in-pad via); P1 (46 × 118); F4 (R7 solve); M3 (R7 cost); VEHICLE stack row (118 mm, five hole coordinates) | Any geometry change | Owner-visible text edits. Removing the J2.1 via retires that M2 exception. | No |

**ORDERING items tied to R7 geometry** (§3–§7)
- **Panel and DFM:**
  - tab spans and the forward-rail request;
  - TH1–TH3 coordinates;
  - order-number mark at (22.9, 86.15);
  - the expected DFM queries with coordinates: the J2.1 via (44.035, 77.92), TP122's via;
  - "J3 overhangs 0.45";
  - rail-removal cautions: R166 0.75 mm and TP84 0.7 mm from the left edge; J9 tabs 0.5 mm, TP76 0.7 mm and C74 0.73 mm from the right;
  - "bottom parts 1.4–2 mm from several pins", hence hand or selective soldering.
- **Bench probe points:**
  - NRST gate: C24.1 with C15.1 "beside it", and the C24-short reset method once J2 is coated;
  - TP80 below 1 V;
  - the GND probe points TP88 and TP74 ("never probe R134 armed");
  - TP122 leakage and coating order.
- **Coating and staking:**
  - the coating mask list (part-based, survives if the parts keep their roles);
  - U4's 3 mm coating-free zone;
  - C121 staking on its W and N sides only, because U4/U5 sit under it.
- **Sled:**
  - five hole coordinates;
  - L1 3.0 mm deepest;
  - tie channel between (21.5, 68.6) and (27.0, 82.6);
  - bottom pours BAT_IN, ACT_FET_S and RAW_ACT that must not touch the sled;
  - jack lower-flange and plug-nut depths;
  - J3 overhang.
- **Hardware and harness:**
  - washer ≤ 7 mm, from the nearest pads (C76.2 4.42, TP92 4.60, TP30 5.01);
  - arming-link and igniter wire room of 6.3–6.9 mm;
  - camera plug 0.03 mm margin;
  - pyro-block extent x 4–42, y 84–114.4 for the fuse-holder keep-out.
- **RF:**
  - D30/D31 0.5 mm from the centre pads (inspection);
  - shunt-trace lengths in the VNA tuning model.

**Topology-based gates that survive any placement:** the static, leakage and dynamic pyro gates, RF immunity, commanded fire, plug-out cold test, antenna-short test, radio reset-hold test, coexistence and S21 targets, NRST ≥ 1 MΩ, and the reverse-hot-plug procedure.

## 14. Placement facts a planner should know

Measured on R7 (centre-to-centre unless stated). These are not constraints, but each one is a source of R7's routing compromises.

1. **The power input is split across the board.**
   - J1 is at y 110 (forward, owner's CH1 grouping, R6). The logic-side input chain stayed aft, where R5 had J1: D8 TVS (11.9, 31.2), damper C89/C95/R166 (y 29–35), U9 eFuse (11.2, 40.6), R80 switch leg (16.3, 24.5) and input caps C80/C96 (y 52–56).
   - J1 → U9 is 70.8 mm and J1 → D8 80 mm, carried by the In2 BAT_IN pour along the left half (x 0.3–32.2, y 26–115.5).
   - BAT_SW_SOURCE runs the board length (C27 leftover).
2. **The camera supply loops.** RAW_PROTECTED leaves U9 (y 41) for U7/U8 (y 85–95): 153 mΩ, 0.15 V at 1 A. CAM_5V then returns aft on the In2 CAM_5V strip (x 34.6–40.4, y 33–107) to J9 (y 42) and U13 (y 31.5). U8/L3 → J9 is about 52–58 mm.
3. **USB loops.** J3 (4.6, 75.3) → U10 (15, 80.6) → USB_LIMITED to U11 (29.2, 28.2), 54 mm (72 mΩ).
4. **The 7.7 A actuator path loops.** J1 (23, 110) → Q120 (4, 91) → Q121 (4, 105) → RAW_ACT back down the left side to J122 (23, 75.7). The path runs single-layer on F.Cu, In2 and B.Cu in turn, with necks 2.65–3.82 mm (P1-9 not met).
5. **The radio and GNSS MCU pins face west** into the power column (C84, C80/C96, U9 network). Free GPIOs sit on U1's aft face (39, 41–44), toward the strip (section 9).
6. **QSPI spans three U1 sides,** with U3 aft of U1 (19.7 mm). **VCAP1/VCAP2** detour 4.9× / 4.2× (C19/C20 placement). **CAM_MCU_TX** is 65.9 mm with 5 vias; **CAM_PWR_EN** 81.9 mm with 8 vias; **SWCLK/SWDIO** 62.7 / 53.7 mm with 4 vias each. J2 sits on the right edge (43, 76.65), 31.4 mm from U1, while SWDIO (72) and SWCLK (76) leave U1's west and forward-west corner, so both cross the board.
7. **The logic buck sits next to the strip.** U2/L1 (y 30–36) is 19.6–19.7 mm from the modules; the closest RF part is 5.87 mm from C6. Moving the power conversion forward, beside J1, would put the strip next to quiet circuitry only (Inference: a layout choice, not a requirement).
8. **The IMU is 13 mm off the roll axis** (centripetal acceleration, section 10).
9. **The forward 50 mm offers no long-edge tab window** (section 4).
10. **Tooling holes TH1–TH3 are unnecessary for Standard PCBA,** and they cost tab-rule area.

## 15. Owner decisions a full re-layout would touch

These are things a re-layout could want, each needing the owner's word before it is designed in:
- Changing J1's place or entry direction. That breaks the R6 "battery + CH1 screw-terminal group" rule and `check_r7`'s 25 mm test.
- Re-assigning MCU pins for the radio or GNSS: F10's pin contract.
- A different RF-strip depth, or modules on the other sides: F10's text and the camera-shroud side of the coax loops.
- Moving the M3 support positions, especially the mid-span one: VEHICLE stack row, sled, vibration estimate. A sixth support stays declined.
- Re-arranging the CH1 block's interior: a new spacing qualification.
- The allowed temperature rise on the 7.7 A copper. The battery-corner layout can meet P1-9 outright.
- Any new part (an extended code is impossible at 52/52). A shorter board is an open P1 objective, not a requirement.

Inside these limits, everything else in section 11 marked LOC, MOV or MOV\*\* can be re-placed. The RIG group moves only in y or by a 180° turn. FIX stays.

## Sources

**In `rocket-flight-computer-r7`**
- **Rules:** `AGENTS.md` §2–3; `docs/REQUIREMENTS.md` F4, F6–F10, P1–P3, M1–M3, operating assumptions.
- **R7 records:** `docs/M3_R7.md` (placement, RF strip, interface, DC solve, IPC-2152, return paths, mechanical); `docs/R7_VALIDATION.md` (deviation list, owner summary, pass 8).
- **Procedure and margins:** `docs/ORDERING.md` §3–§7; `docs/MARGIN_PRESCRIPTION.md` P0-1, P0-2, P1-9, P1-13, P1-14, R14 (R7).
- **History:** `docs/M3_R4.md` X1/Y1/V8; `docs/M3_R5.md` L1–L14, V1, §3; `docs/M3_R6.md` decisions.
- **Rules files and checks:** `m3_design/assembly_review/m3.kicad_dru`; `tools/check_r7.py`, `tools/fit_check.py`, `m3_design/check_actuators.py`, `tools/critical_reference.py`, `tools/dc_solve.py`, `tools/route_check.py`, `tools/check.sh`.
- **R7 review sources:** `m3_design/assembly_review/sources/r7_review/pass1_layout.md`.

**In the parent repository:** `CLAUDE.md`; `docs/VEHICLE.md` (bay stack, camera shroud, bore).

**This survey:** `survey_tools/dump_fp.py` (fp.json, fp.txt), `u1_pins.py`, `pyro_margins.py`, `gen_table.py`, `fit.json`.
