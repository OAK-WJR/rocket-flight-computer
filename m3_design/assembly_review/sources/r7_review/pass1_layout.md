# R7 pass 1: layout, DFM and mechanical-fit review (on-board GNSS and 915 MHz radio)

Read-only review, 2026-10-15, of `m3_design/assembly_review/m3.kicad_pcb`: the R6 board at commit 3b215ba plus
the uncommitted F10/P1/M3 changes in `docs/REQUIREMENTS.md`. Scope: KiCad layout, DFM and mechanical fit.
Vehicle-level choices and firmware are out of scope.

What was run. `tools/check.sh` on the unchanged baseline gave DRC 0, unconnected 0, parity 0 and ERC 0, with
the metadata, silkscreen, R6-contract, actuator and fit checks OK. `tools/fit_check.py` passed: worst margin
J9 mated 0.03 mm, and LED2.2 sits exactly 3.800 mm from support (42.3, 4). Courtyards, pads, zones and Edge.Cuts
were read with KiCad 10.0.6's `pcbnew`; no file was saved. The JLC parts API, JLC's stackup template API and
JLC's own impedance engine were queried on 2026-10-15. Maker datasheets are cited in §7.

Coordinates:
- **R6** coordinates are the board's current KiCad coordinates: y = 0 is the aft edge, y = 100 the forward edge.
- **R7** coordinates are the proposal's. Every existing item moves +18.0 mm in y, and the RF strip fills y 0–23.5.

## 1. Summary

**Recommendation: put the RF strip at the aft end. The board becomes 46 × 118 mm.**
- Both SMA jacks sit on the aft short edge: GNSS at x = 12.85, radio at x = 31.54, 18.7 mm apart centre to centre.
- The MAX-F10S sits on the left and the E22-900MM22S on the right, both on the top side.
- Nothing safety-qualified moves. J1, the pyro block, the actuator copper and the MCU keep their positions
  relative to each other. Only the superseded port parts are removed, the two aft supports move to the new
  corners, and J123 is relocated (recommended).

Clearances achieved (courtyard to courtyard):

| From | To | Distance |
|---|---|---|
| GNSS module | Logic-buck IC U2 | 9.6 mm |
| GNSS module | Buck input capacitor C6 | 7.4 mm |
| GNSS module | QSPI flash | 10.7 mm |
| GNSS module | MCU | 23.4 mm |
| GNSS module | 25 MHz crystal | 31.4 mm |
| GNSS module | Radio module | 8.3 mm |
| Radio module | J121, J124 | ≥ 68 mm |
| Radio module | J1 | 85 mm |

The forward end is better for RF distance and cable direction, but it was rejected for three reasons (§3.2):
- J1's wire entry faces +y and is 1.9 mm from the forward edge, so the battery leads would cross the strip.
- About 12 SPI/UART lines plus 3V3 would have to run about 60 mm through the congested right side. The tightest
  point is a 2.7 mm top-side channel between C121 and J2, past the IMU and baro keep-outs, J121 and the camera
  buck.
- The 22 dBm transmitter would sit 8–25 mm from J121, J124 and Q121.

The cost of the aft end is mechanical: the coax leaves aft, toward the battery and the camera shroud. RG316
(13 mm minimum bend radius) needs a loop zone of about 40 mm behind the board, and the board moves forward in
the stack. The stack keeps about 59–72 mm of slack (§6). P2 and `fit_check` must model this explicitly.

**SMA.** In-stock 50 Ω end-launch jacks for 1.6 mm boards exist at JLC: Kinghelm KH-SMA-KE8-G (C530661),
BAT WIRELESS BWSMA-KE-P001 (C496550), XUNPU SMA-KE-347-H13.5-1.6 (C5723200) and Molex 73251-1150 (C841205).
- JLC lists all four as "Assembly Type: Wave Soldering". It fits them in the through-hole step after both
  reflows.
- The rails stay on the long edges. The 9.5 mm jack overhang on the aft short edge does not interfere with
  them.
- The Cinch 142-0701-801 (2 in stock) is not needed.

**GCPW.** The ordered stackup (4 layers, 1.6 mm, 1 oz outer and inner) is JLC template **JLC041611-7628**:
- 7628 prepreg 0.203 mm, Dk 4.4;
- 1.03 mm core, Dk 4.38;
- 0.030 mm inner copper.

The KiCad stackup (0.2104 / 1.0392 mm, 35 µm inner) does not match it. JLC's own impedance engine gives
**W 0.30 mm / gap 0.25 mm on F.Cu over In1 → 50.2 Ω** (coated, εeff 3.19). Without an In1 cut-out the SMA
launch pad is 22 Ω; with In1 removed under the pad it is 51.7 Ω.

Findings: Critical 0, Major 4 (L1–L4), Minor 11 (L5–L15).

## 2. Findings

| ID | Sev. | Req. | Finding | Evidence | Recommended fix |
|---|---|---|---|---|---|
| L1 | Major | F10, P1 | There is no RF floorplan. The superseded external-port design still holds two areas. The aft end has the 4.8 V port buck U14 (21.5, 5.5) with L4 (27.0, 4.5), plus U16, U15 and C170–C178/R190–R195/R206/TP130 (x 7–31, y 0.7–17.1). The right edge has J130/J131, D130/D131 and R196–R205 (x 33.5–45.3, y 29–48.5). There is no strip, SMA, GCPW or module footprint. (The electrical and requirements reviews flag the circuit side; this row is the geometry.) | pcbnew footprint dump; R6 renders; nets TLM_*/RADIO_*/GPS_* | Apply the §3.3 floorplan: aft RF strip, board 46 × 118 mm, a global +18 mm translation of the existing design, the parts listed in §3.3 removed, supports and J123 moved. |
| L2 | Major | F10 ("sized … for the ordered stackup"), M1 | No stackup is ordered: ORDERING §3 says "Impedance control: Not specified". The KiCad stackup (prepreg 0.2104 mm Dk 4.4, inner Cu 0.035, core 1.0392 mm Dk 4.6) matches no JLC template. Its prepreg is that of the **0.5 oz-inner** template JLC04161H-7628 (core 1.065 mm, inner Cu 0.0152 mm); its core and inner copper match neither template. For the ordered 1 oz inner copper, JLC's default ("No requirement") is **JLC041611-7628**: prepreg 0.203 mm Dk 4.4, inner Cu 0.030 mm, core 1.03 mm Dk 4.38. The pass-1 requirements review (R7P1-14) proposes JLC04161H-7628, which is the wrong template for 1 oz inner copper. On the current KiCad stackup the recommended GCPW reads 51.1 Ω instead of 50.2 Ω, so the electrical error is small. The finding is that the requirement cannot be shown against the stackup actually ordered. | JLC template API (live, 2026-10-15): `getImpedanceTemplateSettings` {cuprum 1, insideCuprum 1, 4 layers, 1.6 mm} → "No requirement" = JLC041611-7628; calculator template data (`selectPageImpedanceDefaultTemplate`); `m3.kicad_pcb` stackup and `m3-job.gbrjob` | Set the KiCad stackup to JLC041611-7628. Name "Layer stackup JLC041611-7628" in ORDERING §3 and M1. Size the GCPW per §5: W 0.30 / G 0.25 mm. Impedance control is optional at these lengths (§5.2). |
| L3 | Major | P2 | Neither the SMA jacks nor their mated plugs and coax bends are modelled. With the jacks on the aft edge the cables leave toward the battery and the camera shroud. RG316's 13 mm minimum bend radius then needs about 40 mm of axial room behind the board: 9.5 mm jack, about 16 mm plug, the loop. The loops pass about 20–22 mm from the axis, which clears the bore, but inside the shroud's axial range (joint +4…+47) they would hit the shroud on the camera side (18.4 mm from the axis). The REQUIREMENTS "Board position" assumption (aft edge about 70 mm below the coupler's forward end) no longer holds. | §6 calculation from the VEHICLE stack and shroud rows; L-com RG316 spec (13 mm bend radius); maker drawings (9.5 mm beyond the edge) | Add an SMA mated-plug envelope to `fit_check` and REQUIRED_MATED (§6.4). Define the coax loop zone in VEHICLE and ORDERING §7: the board's aft edge at or forward of joint +88, or the loops oriented away from the shroud, measured in Onshape. Update the board-position assumption. |
| L4 | Major | M1/M2 (DFM), ORDERING §3–4 | The ORDERING tab windows are R5 values and break their own rules on R6. The left tab at y 71–76 is 1.30 mm from the Q120 courtyard (the rule is ≥ 1.5 mm). The left tab at y 78.5–83.5 is 1.31 mm from Q121 and 2.10 mm from capacitor C120 (the rule is ≥ 5 mm). The right tab at y 43.75–48.75 is 0.66 mm from the J131 courtyard and 1.20 mm from its pad. No rule-compliant 5 mm window exists forward of R6 y ≈ 54 (the forward 46 mm) on either long edge. The left edge has Q120/Q121/C120 at 1.3–2.1 mm; the right edge has C77/L3/R71/R72/C72–C76 at 1.0–1.2 mm. | Scripted clearance scan of the four ORDERING windows and of every 5 mm window, with ORDERING's 1.5 mm / 5 mm rules | Use the R7 windows in §3.3: left Y 63–68; right Y 62–67 and Y 8–13 (new, ≥ 11 mm from the radio courtyard). For the forward end, either move C120 about 3 mm inboard and Q120/Q121 ≥ 0.2 mm inboard, then add a left tab near R7 Y 96.5–101.5 and re-solve the actuator copper; or have JLC confirm a 50 mm unsupported forward end in "Confirm Production file". |
| L5 | Minor | F10 (unbroken ground, launch) | R6_BAT_IN_In2 starts at the aft edge (R6 (0.3, 0.3)–(15, 14.6)). After the extension it would lie under the GNSS module's forward half and its decoupling (R7 y 18.3–23). The SMA launch needs an In2 GND reference under its In1 cut-out. | Zone outlines from pcbnew | Clip R6_BAT_IN_In2 to R7 Y ≥ 23.5. R80.1 (BAT_IN) at R7 (15.5, 24.5) stays reachable. Add an In2 GND zone over R7 Y 0–23.5 with priority above BAT_IN. |
| L6 | Minor | M2 | The board's copper-to-edge rule is 0.5 mm, but the SMA launch pads must reach the routed edge. | Design settings; JLC capabilities: "Copper clearance from routed board edges: ≧0.2 mm", outline ±0.2 mm | Start the SMA pads at Y 0.2. Add a footprint-scoped `edge_clearance` rule of 0.2 mm for J30/J31. Add a JLC remark that the edge copper at the jacks is deliberate. |
| L7 | Minor | M1/M2 (paste) | u-blox recommends a 150 µm stencil with T-shaped paste extending to a 12.5 mm span. ORDERING prefers 0.10 mm (for U11's apertures). The MAX-F10S is MSL 4. | MAX-F10S IM R01 Fig. 25–26 ("Recommended stencil thickness is 150 µm"); DS R03 Table 22 (MSL 4) | Keep 0.10 mm and give the MAX-F10S the T-shaped apertures with about 1.5× pad area (Inference). Add the MSL 4 bake remark. Both modules go on the top side, which is reflowed last (IM §5.2: "soldering the module upside down … not recommended"). |
| L8 | Minor | M1 (maker-rated soldering) | The low-cost jacks state no soldering temperature: XUNPU, BAT WIRELESS, DreamLNK. Kinghelm KH-SMA-KE8-G states "Wave solder resistance 240～250℃, 5S". Molex 73251-1150 states reflow 260 °C, 10 s, 2 cycles. | Maker datasheets (§7) | Prefer Kinghelm C530661 (low cost) or Molex C841205. If BAT/XUNPU is used, record the missing rating as an M1 exception: brass/PTFE body, hand-soldered (Inference). |
| L9 | Minor | M2 (fit) | Jack slots are 1.7 mm (Kinghelm, BAT, HenryTech), 1.73 mm (DreamLNK) and 1.75 ± 0.1 mm (XUNPU). JLC's 1.6 mm board is ±10 % (1.44–1.76 mm). JLC041611-7628 laminates to 1.566 mm, about 1.6 mm across the pads (Inference). | JLC capabilities ("± 10%"); template compressionThickness 1.566 | Put no paste on the jack pads (pre-tinned bumps eat the slot play). Check jack fit on the first boards. |
| L10 | Minor | ORDERING accuracy | Beyond L4, ORDERING gives TH3 at (1.4, 90.0); it is at (1.4, 94.0). It says "Y = 0 is the battery-terminal end with J1" and "J1 toward the aft edge"; in R6, J1 is at y = 92.4 with its entry facing y = 100, 1.9 mm from the edge. | NPTH drill file (T3 X1.4 Y−94.0); J1 silk arrows at y 95.0–95.8 | Rewrite with R7 coordinates (§3.3), including the order-number mark (23, 85.25). |
| L11 | Minor | F10 (alternates) | The MAX-M10S fits the U30 footprint (same LCC-18). The E22-900M22S (20 × 14 mm) does not fit the reserved radio area (x 24–34, y 9–19). | F10 text; EBYTE drawing | Record that the M22S alternate needs a layout change. Do not plan a dual footprint (Inference: a 20 × 14 mm land would push the GNSS block). |
| L12 | Minor | P3, M1 | Hand-soldering the edge jacks next to four solid GND planes is heat-limited. The pads need the THT-class handling remark. | JLC part pages: "Assembly Type: Wave Soldering … Assembly Difficulty: High" | Keep the leg pads solid with fence vias ≥ 0.8 mm from them. Remark: "J30/J31 hand-soldered after reflow with board preheat; centre contact on the top signal pad; flange flush to the routed edge; all four legs soldered top and bottom." |
| L13 | Minor | F10 | Unmoved, J123 (pull-pin, R7 x 31.2–37.8, y 19.75–24.95) abuts the radio block. It is 0.9 mm from a radio at y 8–18 and overlaps the recommended radio courtyard (y 9–19) by 0.1 mm. It blocks the radio's forward escape and squeezes the GNSS–radio gap to 6.3 mm. | §3 model | Move J123 to R7 (36.0, 34.5), the place of R205 (removed by F10). Nudge R61 (B.Cu) about 0.5 mm. Recheck J123's mated envelope; it clears J9's: x 33–39 against ≥ 40.95. |
| L14 | Minor | F10 ("no signals under the modules") | Nothing in the CAD enforces it. u-blox: "Avoid signal lines crossing below the module at these two layers." EBYTE: no wiring under the module on any layer. The MAX-F10S has a de-paneling tab of up to 0.6 mm (dimension P) that the keep-out must include. | MAX-F10S IM §4.4; DS Table 21; E22-900MM22S manual §4.1 | Add DRC rules: disallow non-GND tracks and vias on F.Cu and In1 within U30/U31 courtyards, and on B.Cu within U31. Make the U30 courtyard include the 0.6 mm tab and the 12.5 mm paste span. |
| L15 | Minor | F10 (≥ 34 dB isolation) | Board-level coupling between the two RF ports is not budgeted. The two fenced GCPWs and jacks 18.7 mm apart should be far below −34 dB (Inference), but nothing shows it. | Geometry §3.3 | First-article bench item: VNA S21 between J30 and J31 at 915, 1176 and 1575 MHz, target ≤ −50 dB, before the keyed-transmitter C/N0 test. |

## 3. Floorplan

### 3.1 Current R6 placement around both ends

| Role | Part (side) | R6 position or courtyard |
|---|---|---|
| Logic supply buck | U2 AP63203WU-7 (B), L1 4.7 µH (B); input/output C6–C9 (B) | U2 x 16.25–19.75, y 12.96–17.05; L1 x 21.8–27.2, y 12.71–17.3 |
| Camera 5 V buck | U8 AP63301WU-7 (B), L3 6.8 µH (B), C72–C76 (B), FB R71/R72/C77 (F) | U8 x 39.9–43.7, y 74.6–78.2; L3 x 38.8–44.8, y 78.6–85.6 |
| Port 4.8 V buck (F10 removes) | U14 AP63301WU-7 (F), L4 (F), U16/U15 limiters (F) | U14 (21.5, 5.5), L4 (27.0, 4.5), U16 (10, 7), U15 (10, 10.5) |
| Actuator switch (DC load switch carrying pulsed servo current, not a switcher) | Q120, Q121 AON6403 (B); gate drive Q122/R120–R123 (B) | Q120 (4.0, 73.0), Q121 (4.0, 87.3), courtyards x 1.3–6.7 |
| MCU / HSE / QSPI | U1 (F); Y1 25 MHz (B); U3 W25Q128 (F) | U1 x 13.2–30.5, y 26.9–44.2; Y1 (25.6, 35.75); U3 x 19.6–29.6, y 13.1–19.0 |
| Pyro terminals | J124 ARM (F, entry −x), J121 IGN (F, entry +x), Q124 (F) | J124 x 4.5–15.7 and J121 x 30.3–41.5, both y 70.2–80.4 |
| Battery entry | J1 DB128V-4P (F, rot 180) | x 11.9–34.1, y 86.9–98.1; pins y 92.4; entry face y ≈ 98.1, facing +y |
| Supports | Edge.Cuts Ø3.2 | (4, 4), (42.3, 4), (4, 46), (4, 96.4), (42, 96.4); ties (21.5, 50.6), (27.0, 64.6) |
| Tooling holes | TH1–TH3 Ø1.152 NPTH | (44.8, 9.2), (1.4, 64.6), (1.4, 94.0) |

The MCU pins the electrical review proposes for the radio are on U1's left side near its aft corner: pins
51–57 at x 14.3, y 29.5–32.5, and PE15 (pin 45) at (18.35, 27.95). The GNSS UART pins 68/69 are at x 14.3,
y 38–38.5. Both groups face the aft half of the board.

### 3.2 Aft end against forward end

| Factor | Aft end (recommended) | Forward end |
|---|---|---|
| Bay stack and cable direction | Jacks point at the battery-lead zone and camera shroud. Coax must loop back (RG316: about 40 mm of axial room, loops about 20–22 mm from the axis). The board moves forward; slack stays about 59–72 mm (§6.2). | Jacks point at the eyebolt/charge-wiring zone. Straight plugs, cables run straight forward. The bulkhead moves forward about 26 mm; slack about 69 mm. |
| 22 dBm transmitter and cable vs J121/J124 and J1 | Radio ≥ 68 mm from J121/J124 and 85 mm from J1. Coax runs back under the sled, shielded from the top-side terminals by the board. | Radio 8.5–25 mm from Q121, J124 and J121. **J1's entry faces +y, 1.9 mm from the edge, so the battery leads would cross the strip.** J1 must move: to the aft edge, which reverses the owner's "battery + CH1 terminal group" and puts the 7.7 A servo return under the MCU; or turned to a long edge, which puts the radio next to the battery/ARM leads. |
| GNSS to switchers | Logic buck U2 9.6 mm, L1 11.6 mm, its input capacitor C6 7.4 mm; camera buck ≥ 75 mm. U14/L4 are removed. | Camera buck L3 about 13 mm, U8 about 20 mm (GNSS on the right) or about 27 mm (left); logic buck ≥ 81 mm. |
| GNSS to MCU, crystal, QSPI | 23.4 / 31.4 / 10.7 mm | ≥ 54 / ≥ 61 / ≥ 80 mm |
| Digital and 3V3 routing to U1 | About 25–35 mm through the area freed by U14/L4/U15/U16 (R7 y 18–30). The 3V3 In2 pour starts at R7 y 27. | About 60–75 mm along the right side: C121/J2 leave a 2.7 mm top channel at R6 y 53–62; then the U4/U5 B.Cu keep-outs, U7, J121 pins, the U8/L3 buck and the CAM_5V In2 strip. 3V3 has to be brought about 40 mm past the 3V3 pour. |
| Existing parts that move | U14/L4/U15/U16/J130/J131 group removed (F10 removes them anyway); two aft supports; J123 (recommended); BAT_IN In2 pour clipped. | J1 and its BAT_IN/BAT_SW copper; two forward supports; the PYRO_BLOCK area; a long digital corridor; F4 copper re-solved. |
| Verdict | Fewest changes to qualified copper; meets every F10 distance with margin. | Best RF distances and cabling, but blocked by J1 and the routing corridor. |

### 3.3 Proposed R7 floorplan

**Outline and translation.**
- Edge.Cuts becomes (0, 0)–(46, 118).
- Translate every existing item, including zones, rule areas, graphics and supports, by +18.0 mm in y. KiCad
  coordinates then still equal board coordinates (y = 0 aft).
- A pure translation keeps the R6 routing, DRC spacing and actuator copper geometry identical in the unchanged
  region (Inference). DRC and the copper solve must still be rerun.
- Alternative: extend the outline to y = −18 and move the drill/aux origin. This changes fewer coordinates but
  breaks the y = 0-is-aft convention used across the docs.

**Removed** (F10; confirm against the electrical review §6.3): J130, J131, D130, D131, R196–R205, U14, L4, U15,
U16, C170–C178 (C177 is U16's input bypass), R190–R195, R206 and TP130.

**Moved:**
- Aft supports from R7 (4, 22) and (42.3, 22) to **(4, 4) and (42.3, 4)**.
- J123 to **(36.0, 34.5)**, R6 (36.0, 16.5); see L13.

**Supports (five M3).**
- (4, 4) and (42.3, 4): new corners, all-GND strip. Nearest top part 4.0 mm (the GNSS feed area), nearest bottom
  pad 5.4 mm (J30's leg pad).
- (4, 64): mid-span, inside the middle third (39.3–78.7).
- (4, 114.4) and (42, 114.4): forward corners, unchanged relative geometry.
- Ties: (21.5, 68.6) and (27.0, 82.6).
- The left side's longest unsupported span grows from 42 to 60 mm, (4, 4) to (4, 64). P2 asks for the
  support-span and vibration estimate to be redone on the final geometry; it is not done here.

**Tooling holes**, translated, Economic-only per ORDERING: TH1 (44.8, 27.2), TH2 (1.4, 82.6), TH3 (1.4, 112.0).

**RF strip: x 0–46, y 0–23.5, all four layers GND.**
- In2 gets a GND pour over the strip (L5).
- F.Cu holds only module pads, the two GCPWs and the RF-chain parts, inside GND.
- B.Cu is GND except the J30/J31 leg pads and, if used, the GNSS feed-limiter parts under U30's west half.
- A GND via fence runs along y ≈ 23.5 at 2 mm pitch, opened only where interface lines cross on F.Cu/B.Cu.

| Block | Item | R7 coordinates and orientation |
|---|---|---|
| GNSS | J30 SMA jack | Axis x = 12.85. Flange on the aft edge (y = 0), body y −9.5…0. Pads y 0.2–4.4 (§4 land). |
| | RF line (GCPW W 0.30 / G 0.25) | x = 12.85, y 4.4 → 10.1 (5.7 mm). Order from the jack: D30 ESD shunt (y 4.6–5.6, east) → L30 47 nH bias tap (y ≈ 6.0, west; C302 10 nF at its cold end, ≈ (11.3, 6.0)) → C303 shunt (y ≈ 7.0, east, DNP) → R304 0 Ω series (y 7.3–8.3) → C305 shunt (y ≈ 8.7, east, DNP) → RF_IN. The bias tap is on the antenna side of the pi network, as the electrical review requires. |
| | U30 MAX-F10S | Body x 4.5–14.6, y 10.1–19.8. Pins 10–18 face the aft edge; RF_IN (pin 11) at (12.85, 10.1); GND pins 10/12 flank it. Pins 1–9 face forward at y 19.8. The 0.6 mm de-paneling tab sits at the west end (x 3.9–4.5). If the five RF-chain parts need more room, move U30 forward up to 1 mm and the fence to y 24.5 (freed area). |
| | Feed limiter (Q30–Q32, R300–R303) | B.Cu under U30's west half (x 5–11, y 11–19). Vias beside pins 13/14 (LNA_EN, VCC_RF) at y ≈ 8.8. This follows u-blox's top-two-layer rule (L14). |
| | FB30, C300, C301, R305–R307 | Forward of U30: x 5–14, y 20.2–23. |
| Radio | J31 SMA jack | Axis x = 31.54, pads y 0.2–4.4. |
| | RF line (GCPW W 0.30 / G 0.25) | x = 31.54, y 4.4 → 9.0 (4.6 mm). D31 ESD shunt (y 4.6–5.6); L31 0402 shunt option (y ≈ 6.0); optional DNP pi network (y 6.5–8.5) for VNA tuning. |
| | U31 E22-900MM22S | Body x 24.0–34.0, y 9.0–19.0, rotated 180° from the EBYTE top view. Pins 6–10 face the aft edge: ANT (pin 6) at (31.54, 9.0), GND pin 7 beside it. SPI pins 11–15 on the west column (x 24), DIO1–3 on the forward row (y 19), VCC/NRST on the east column (x 34): VCC (pin 1) at y 16.5. |
| | FB31, C310 (0805), C311, C312 | East of U31: x 34.8–37.5, y 14–19. |
| | R310–R315 | Forward of U31: x 24–34, y 19.6–23. |
| Interface zone | GNSS UART/reset; radio SPI/BUSY/DIO1/NRST/RXEN; 3V3 | R7 y 23.5–30 (freed U14/L4/U15/U16 area). 3V3 comes from vias into the In2 3V3 pour (which starts at y 27) to FB30/FB31. |

**Routing corridors to U1** (suggestions, Inference). Keep every digital line ≥ 5 mm from U30 and its RF line.
- GNSS lines: B.Cu along x 2–9 to U1's left side.
- Radio lines: F.Cu right of U3 (x 29.6–34), or B.Cu between D8 and U2 (x 14.2–16.2, R7 y 27.5–35).
- The electrical review could also assign the radio to U1's aft-facing pins (26–50) to shorten the routes.

**Rails and tabs.**
- Rails on the long edges only, tab-routed, no V-cut. J3 still overhangs the left edge by 0.45 mm.
- No rail or frame member on the aft short edge: the jacks overhang it by 9.5 mm and are fitted in JLC's
  through-hole step after reflow.
- Rule-compliant 5 mm windows, with ORDERING's ≥ 1.5 mm to parts/pads and ≥ 5 mm to capacitors, R166, LED2,
  tooling holes and both RF modules:
  - left x = 0: **Y 63.0–68.0**. J3 is 1.83 mm away, C84 5.23 mm.
  - right x = 46: **Y 62.0–67.0**. TP75/TP76 are about 2.0 mm away, C11 6.6 mm.
  - right x = 46: **Y 8.0–13.0**, new. The radio courtyard is 11.2 mm away, its decoupling (C310–C312)
    about 8.5 mm, C92 13.3 mm.
- The forward 46 mm (R7 y ≳ 72) needs the L4 fix.
- Remove the tabs by nibbling, as now. The nearest tab is ≥ 11 mm from either module.

ASCII sketch, top view, aft edge at the top (not to scale):

```
 y=0  |==[J30 SMA x12.85]=============================[J31 SMA x31.54]======|  <- aft edge, jacks overhang 9.5 mm
      | o(4,4)  D30 L30 pi                            D31  (pi)    o(42.3,4)|
 y≈10 |   [U30 MAX-F10S  x4.5-14.6]        SPI lane   [U31 E22  x24-34] C310 |
 y≈20 |   pins 1-9 -> UART/RESET        (x19.6-24)    DIO/SPI ->  R310-315  |
 23.5 |.. GND via fence .....................................................|
      |   freed U14/L4/U15/U16 area: FB30/FB31, series R, 3V3 entry  J123 (36,34.5)
 ~31  |   D8/D9/U9 (input)      U2+L1 logic buck (B) / U3 QSPI (F)   LEDs  J9 cam |
      |   ... unchanged R6 layout shifted +18 mm (MCU y 44.9-62.2, pyro y 84-114.4, J1 y 104.9-116.1) ...
 118  |__________________________________________________________________________|
```

### 3.4 Distances achieved (R7 model; courtyard to courtyard, mm)

| From | U2 | L1 | C6 | U3 | U1 | Y1 | U8 | L3 | Q120 | Q121 | J121 | J124 | J1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| U30 GNSS | 9.6 | 11.6 | 7.4 | 10.7 | 23.4 | 31.4 | 75.4 | 78.8 | 65.9 | 80.2 | 68.5 | 66.8 | 83.4 |
| U31 radio | 11.6 | 10.9 | 8.8 | 11.2 | 25.0 | 31.9 | 72.9 | 76.8 | 69.5 | 83.4 | 68.4 | 68.8 | 85.0 |

- U30 to U31: 8.3 mm, against u-blox's "at least a 5 mm distance to any RF component".
- U30's nearest parts are R80 at 2.2 mm (B.Cu, a 470 kΩ switch leg), then C89, D8 and R166 at 5.8–6.2 mm.
  All are DC parts.

## 4. Edge-launch SMA (end-launch PCB jack, 50 Ω, ≥ 3 GHz, 1.6 mm board)

JLC stock and price at 10 come from the JLC parts API on 2026-10-15. Two jacks per board, so 10 boards need
≥ 20. "Body beyond edge" means flange face to mating face.

| Part | LCSC | Stock | $/pc @10 | Rating | Board slot; legs | Body beyond edge | Footprint source | JLC assembly |
|---|---|---|---|---|---|---|---|---|
| **Kinghelm KH-SMA-KE8-G** (recommended, low cost) | C530661 | 959 | 0.359 | 50 Ω, DC–6 GHz, VSWR ≤ 1.35; wave-solder 240–250 °C 5 s; −40…+85 °C | 1.7 mm (±0.2 general); four legs 0.9 mm square at 5.1 mm c-c (4.2 inner, 6.0 outer); Ø0.95 pin | 9.5 mm (13.5 − 4.0); 6.5 mm square flange; 1/4-36UNEF | Maker drawing, LCSC datasheet p. 2; no maker land. Derive: centre pad 1.2 × 4.2, ground pads 1.2 × 4.2 at ±2.55, top and bottom | "Wave Soldering", Economic and Standard, difficulty High |
| BAT WIRELESS BWSMA-KE-P001 | C496550 | 73,004 | 0.318 | 0–6 GHz; IL 0.15 dB @ 6 GHz; 500 cycles; −45…+85 °C; no soldering rating | 1.7 mm; drawing shows the same 6.5 / 4.2 / 6 / 2.8 / 1.7 family as the Kinghelm | 9.5 mm | Maker drawing (datasheet p. 6); EasyEDA footprint per JLC page | "Wave Soldering", Standard only, High |
| XUNPU SMA-KE-347-H13.5-1.6 | C5723200 | 1,498 | 0.413 | 0–3 GHz (exactly the floor); no soldering rating | 1.75 ± 0.1 mm; legs 0.9 mm | 9.5 mm (13.5 − 4.0); 6.5 mm square flange | **Maker recommended land**: three 1.20 × 4.20 mm pads, 5.65 mm span | "Wave Soldering", Standard only, High |
| DreamLNK SMA-KE-P902 | C914557 | 1,188 | 0.783 | 0–6 GHz, VSWR ≤ 1.5, −55…+125 °C | 1.73 mm; 9.5 × 7.9 mm flange, legs at the corners (about 8.5 mm c-c) | 9.5 mm (14.28 − 4.75) | Maker drawing | not checked |
| Molex 73251-1150 (premium) | C841205 | 211 | 3.894 | Jack, 18 GHz, for a 1.60 mm board; reflow 260 °C, 10 s, 2 cycles | Sales drawing 732511150_sd.pdf **not retrieved** (molex.com timed out). The requirements review cites an EasyEDA land with legs 8.5 mm apart, which needs the GNSS jack at x ≥ 13.6. | not retrieved | Molex SD (URL §7) | "Wave Soldering", Standard only, High |
| Kinghelm KH-SMA-KE8-G48H | C6915272 | 97 | 0.448 | DC–6 GHz | as KE8-G | 9.5 mm | Maker drawing | not checked; stock thin for 20 |
| HenryTech HL-SMA-KEP-02 | C22355857 | 650 | 0.354 (@1) | **No frequency rating published**, so ≥ 3 GHz is unshown | 1.7 ± 0.05 mm; "suitable for 1–1.6 mm" | 9.5 mm | Maker drawing | not checked |
| Cinch 142-0701-801 | C3173345 | **2** | 8.90 | 18 GHz | .062 board | not checked | Maker drawing | short |
| Samtec SMA-J-P-H-ST-EM1 / Amphenol 132322 | C5199907 (651) / C42394535 (38) | | 4.75 / 3.09 | Listing only; the LCSC datasheet for C5199907 is a cable-assembly page | not verified | not verified | not retrieved (samtec 429, amphenolrf 403) | not used |

**Recommendation.**
- Use Kinghelm KH-SMA-KE8-G (C530661). It is the only low-cost jack with a maker soldering rating (M1, L8),
  rated to 6 GHz, with enough stock.
- BAT WIRELESS C496550 is the same geometry with huge stock: a drop-in second source on the same land, with an
  M1 note.
- XUNPU C5723200 needs its own land (5.65 mm span).
- Molex C841205 is the higher-grade choice if its drawing confirms the land and the GNSS jack moves to
  x ≥ 13.6.
- Every jack listed is 9.5 mm beyond the edge with a 6.5 mm or wider flange, so the placements in §3.3 hold for
  all of them.

**JLC process and rails.**
- JLC assembles these jacks in its through-hole step, the "Wave Soldering" class, on Standard PCBA. That means
  hand or selective soldering after both reflows; ORDERING already forbids wave.
- So the 9.5 mm overhang only has to clear the panel at that step. Rails on the long edges only; nothing on the
  aft edge (§3.3).
- Put no paste on the jack pads (L9).
- Expect a DFM query for a body outside the outline; confirm it as deliberate.

**Fallback if stock fails.** Consign Molex or Cinch jacks to JLC, or hand-solder after delivery. M1 says
"Standard PCBA including through-hole parts" and "every part in stock". A post-delivery hand-soldered jack
would be a documented M1 exception, and the board would ship without its RF launch tested at JLC. Not needed
on 2026-10-15 stock.

## 5. 50 Ω GCPW

### 5.1 Stackup actually ordered

ORDERING orders 4 layers, 1.6 mm, 1 oz outer and **1 oz inner**. JLC's live template API returns
"No requirement" = **JLC041611-7628** for that build:

| Layer | Thickness | Dk |
|---|---|---|
| L1 copper | 0.035 mm | |
| 7628×1 prepreg | 0.203 mm | 4.4 (RC 49 %) |
| L2 copper | 0.030 mm | |
| Core "1.1mm 1/1OZ with copper" | 1.03 mm | 4.38 |
| L3 copper | 0.030 mm | |
| 7628×1 prepreg | 0.203 mm | |
| L4 copper | 0.035 mm | |

Laminate total 1.566 mm (NP-155F). The 0.2104 mm / 15.2 µm values belong to the 0.5 oz-inner template
JLC04161H-7628. Other zero-fee templates exist, for example JLC041611-3313 with 0.092 mm prepreg, but they
would halve the line width and gain nothing here.

### 5.2 JLC impedance engine results

Model "共面单端（外层）", CoatedCoplanarWaveguideWithLowerGnd1B: coplanar single-ended on the outer layer, coated,
with a lower ground. These are JLC's own calculator values:
- H1 = 0.203 mm, Er1 = 4.4;
- T1 = 1.6 mil, with W2 = W1 − 0.5 mil;
- solder mask 1.0 mil over the laminate and 0.6 mil over copper, CEr 3.8.

The thickness, trace-taper and mask values are those the calculator itself applies for 1 oz outer copper
(its config lists).

| Gap G \\ W | 0.26 | 0.28 | 0.30 | 0.32 | 0.34 | 0.36 |
|---|---|---|---|---|---|---|
| 0.15 mm | 49.55 | 47.98 | 46.52 | 45.15 | 43.88 | 42.68 |
| 0.20 mm | 52.17 | 50.45 | 48.85 | — | — | — |
| 0.25 mm | — | — | **50.24** (εeff 3.194) | 48.68 | — | — |
| 0.30 mm | 54.70 | 52.84 | 51.11 | 49.51 | 48.01 | 46.60 |

Ω; blanks were not returned by the engine's rate limit.

Sensitivity at W 0.30 / G 0.25:

| Change | Result |
|---|---|
| Prepreg 0.183 / 0.223 mm | 47.8 / 52.4 Ω |
| Dk 4.2 / 4.6 | 51.2 / 49.4 Ω |
| W 0.27 / 0.33 mm | 52.8 / 47.9 Ω |
| G 0.20 / 0.30 mm | 48.9 / 51.1 Ω |
| The present KiCad prepreg, 0.2104 mm | 51.1 Ω |
| No mask | 52.3 Ω |

The GNSS line is 5.7 mm and the radio line 4.6 mm long: about 0.05 λ at L1 and 0.03 λ at 915 MHz (εeff 3.19). Any of
these deviations costs < 0.01 dB of mismatch (Inference), so impedance-controlled ordering is optional. Naming
the stackup is not optional (L2).

### 5.3 Recommended geometry

- **Line:** F.Cu, **W = 0.30 mm, gap G = 0.25 mm** to F.Cu GND on both sides, referenced to In1 GND. Use a
  netclass `RF50` (0.30 mm track) and a custom rule: `(rule "RF50 GCPW gap" (condition "A.NetClass == 'RF50' &&
  B.NetName == 'GND'") (constraint clearance (min 0.25mm)))`. The GND zones keep their 0.15 mm elsewhere.
- **Launch:**
  - jack centre pad 1.2 × 4.2 mm, with F.Cu GND poured to **0.30 mm** from it, joining the leg pads;
  - **In1 cut out under the centre pad** (1.8 × 4.6 mm rule area, no copper on In1), so the pad references In2
    GND at 1.263 mm. JLC engine: **51.7 Ω** (55.3 Ω at a 0.40 mm gap);
  - without the cut-out the pad is **22.3 Ω**: |Γ| ≈ 0.23, about 0.24 dB at L1 and about 0.09 dB at 915 MHz
    (Inference);
  - taper from 1.2 to 0.30 mm over the last 0.5–1.0 mm of the pad.
- **Module pads:** run straight into RF_IN and ANT. The 0.8 mm-wide lands are short (< 0.02 λ).
- **Part pads on the line:** 0402 pads sit on the 0.30 mm line. Shunt parts go with one pad on the line edge and
  the other in the coplanar GND, so there are no stubs. u-blox: "Any stubs at the ground planes must be avoided
  or ended with a via."

### 5.4 Fencing, ground continuity, keep-outs

- **Via fence:**
  - GND vias 0.3 mm drill / 0.6 mm pad (the board's standard via), centres 0.85 mm from each line centreline,
    pitch ≤ 1.5 mm along both sides;
  - ≥ 3 vias beside each jack leg pad pair, tying F.Cu, In1, In2 and B.Cu;
  - vias beside every module GND castellation;
  - the strip-boundary fence at y ≈ 23.5, 2 mm pitch.
  - Pitch rationale (Inference): 1.5 mm is far below λ/20 (about 5 mm at L1, about 2.4 mm at 3.5 GHz).
- **L2 (In1):** solid GND under the whole strip except the two launch cut-outs. No In1 signal tracks anywhere
  (unchanged R6 practice).
- **L3 (In2):** GND in the strip; clip BAT_IN to y ≥ 23.5 (L5).
- **Keep-outs:**
  - No signals on F.Cu or In1 inside U30/U31 courtyards, and none on B.Cu inside U31 (L14).
  - No digital line within 5 mm of U30 or of either RF line, except each module's own interface pins.
  - No pours other than GND within the strip.
  - Conformal coating stays off both modules and the jack mating faces. u-blox: coating "will void the
    warranty". Add them to the ORDERING §5 masking list; the pyro block is ≥ 60 mm away.

## 6. Fit

### 6.1 Radial margins

Method: `fit_check`, usable radius 24.9 mm, axis x = 23, sled tolerance 0.3 mm, top face on the axis.

| Item | Extent | Margin |
|---|---|---|
| U30 MAX-F10S (top, height 2.5, max 2.7) | x 3.9–14.6 | 5.3 mm |
| U31 E22-900MM22S (top, 2.5) | x 23.4–34.6 (lands) | 12.7 mm |
| J30 jack body (6.5 mm flange, z −2.74…+3.76; axis 0.45–0.51 mm above the top face) | x 9.6–16.1 | 10.6 mm |
| J31 jack body | x 28.3–34.8 | 12.2 mm |
| J30 mated straight plug (Inference: SMA coupling nut 5/16″ hex, 9.17 mm across corners; about 16 mm beyond the jack face) | x 8.3–17.4, z −4.1…+5.1 | 8.9 mm |
| J31 mated straight plug | x 27.0–36.1 | 10.4 mm |
| RG316 loop (13 mm bend radius, Ø2.49), oblique U-turn down and inward to run forward under the sled. J30 cable from (−10.2, +0.5) to about (+6.6, −19.4) relative to the axis; J31 mirrored | r ≤ 21.8 | about 2.3–2.8 mm (Inference) |

The bottom face in the strip carries only the jack legs (about 1.0 mm below it) and, optionally, the
SOT-23/0402 limiter (≤ 1.2 mm). L1 at 3.0 mm stays the deepest bottom part. The support clearances in §3.3
meet the 3.5 mm bottom and 3.8 mm top rules.

### 6.2 Axial bay stack (VEHICLE numbers)

Now: battery 80 + leads 15 + board 100 + eyebolt/charge 25 + recovery 260, about 115 mm of slack. The board's
aft edge sits at joint +50 ± 3.

With the aft strip:
- the board is 118 mm (+18);
- the 15 mm lead zone becomes a coax-loop and lead zone of about 40 mm: jack 9.5 + plug about 16 + loop
  13 + OD (Inference).
- Slack becomes about **72 mm** if the loop zone may overlap the camera shroud's axial range.
- If the loops must clear the shroud entirely (shroud ends at joint +47), the aft edge goes to about
  **joint +88**:
  - slack about **59 mm**: bulkhead at joint +231, recovery to +491, nose shoulder at +550;
  - only about 32 mm of the board then sits in the Ø50.8 coupler, the rest in the Ø54.6 tube. `fit_check`
    keeps the conservative coupler radius.

For comparison, the forward strip would leave about 69 mm.

### 6.3 Camera shroud and sled

- **Shroud** (VEHICLE: joint +4…+47, 45 mm wide, to within 18.4 mm of the axis):
  - The jack bodies (r ≤ 13.9 mm) and mated plugs (r ≤ 15.6 mm) clear its inner chord wherever they sit.
  - The loops (r about 20–22 mm) do not, if they lie in its axial range on the camera side.
  - The shroud's angular position relative to the board is not in VEHICLE. Measure it in Onshape (CLAUDE.md
    rule) before choosing between "aft edge ≥ joint +88" and "loops oriented away from the shroud".
- **Sled:** it must end at the board's aft edge, or be relieved there, for the jacks' lower flange (1.1 mm
  below the bottom face, beyond the edge). It must leave a channel under the plate for two Ø2.5 mm coax runs.
  Tie each coax to the sled within about 2 cm of its jack (report; P3).

### 6.4 `tools/fit_check.py` changes

| Line | Now | Change |
|---|---|---|
| 41–47 | `MATED` entries `M3_SH_BM07B_SRSS_TB` / `M3_SH_BM04B_SRSS_TB` (J130/J131) | Delete. Add the chosen SMA footprint with refs ('J30', 'J31') and a mated-plug box in footprint-local coordinates: x ±4.6 about the jack axis; from the board edge outward 0…25.5 mm (jack 9.5 + plug 16); z −4.1…+5.1 about the top face. Cite the plug drawing actually bought, and state the coax loop as a separate harness allocation (§6.1). |
| 58 | `REQUIRED_MATED` includes the SH footprints | {'M3_GH_BM04B_GHS_TBT', <SMA footprint>} |
| 62 | `RETENTION_HOLES = ((21.5, 50.6), (27.0, 64.6))` | ((21.5, 68.6), (27.0, 82.6)) |
| 65 | `SIDE_ENTRY` lists J120/J125 (CH2 removed) | ('J9', 'J121', 'J124') |
| 325 | reviewed refs include J130/J131 | Replace with J30/J31; keep J123 at its new position |
| 339–340 | `length > 110.01` / "R6 110 mm maximum" | `> 120.01` / "120 mm maximum (P1)" |
| 349, 385 | 80–90 mm target | Drop it, or report "as short as possible" per P1 |

Also: `test_fit_check.py` (110 → 120; the J130 mate test becomes an SMA test).

Other absolute geometry:
- `check_r6.py` L309–312: 110 mm / 80–90 mm.
- `check_actuators.py` ~L372: the PYRO_BLOCK rectangle must become (4, 84)–(42, 114.4), and its TLM rules L377+
  go.
- ORDERING §3–4: tabs, TH1–TH3, order-number mark (23, 85.25).
- AGENTS "forward pair at y = 96.4" and "(4, 46)" become 114.4 and (4, 64).

### 6.5 Parent `docs/VEHICLE.md`

In the "Main-section stack" row, replace
"flight computer board 100 (M3-ASSY-R5, 46 × 100 mm … mid-span at PCB (4, 46) mm …)"

with
"flight computer board 118 (M3-ASSY-R7, 46 × 118 mm; two edge-launch SMA jacks on its aft edge, 9.5 mm
beyond it; five M3 holes at PCB (4, 4), (42.3, 4), (4, 64), (4, 114.4), (42, 114.4) mm; …)".

Replace "battery leads ~15" with
"battery leads and RF coax loop zone ~40 (two RG316, 13 mm bend radius; keep out of the camera-shroud side
between joint +4 and +47)".

Update "Leaves ~115 mm of slack" to "~59–72 mm". In REQUIREMENTS "Board position", replace "about 70 mm below
the coupler's forward end" with the value fixed after the Onshape shroud check (joint +75…+88).

## 7. Sources

- u-blox MAX-F10S data sheet UBXDOC-963802114-12732 R03:
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
  - Table 10 and Figure 2 (pins);
  - Table 21 (A 10.1, max 10.7 with tab P ≤ 0.6; B 9.7; C 2.5, max 2.7);
  - Table 22 (MSL 4).
- u-blox MAX-F10S integration manual UBXDOC-963802114-12892 R01:
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
  - §4.4: 5 mm to RF parts; ground the top two layers under the module; CPW with ground on layer 2; stub vias;
  - Figures 25–26: land; 150 µm T-paste;
  - §5.2: single upright reflow; no coating, no cleaning;
  - Table 42: L4 47 nH LQG15HS47NJ02.
- EBYTE E22-900MM22S manual, via LCSC:
  https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
  - §3: 10 × 10 × 2.5 mm, 1.27 mm pitch, first pin 2.46 mm, pin 6 ANT;
  - §4.1: no wiring under the module.
- Kinghelm KH-SMA-KE8-G: https://datasheet.lcsc.com/datasheet/pdf/35ad22a9bea57e53d493009a20c931ef.pdf?productCode=C530661
  - JLC part page (Wave Soldering; Economic and Standard): https://jlcpcb.com/partdetail/ShenzhenKinghelmElec-KH_SMA_KE8_G/C530661
- Kinghelm KH-SMA-KE8-G48H: https://datasheet.lcsc.com/datasheet/pdf/7bf36849b07ef9a992a853c34af6ee3b.pdf?productCode=C6915272
- BAT WIRELESS BWSMA-KE-P001: https://datasheet.lcsc.com/datasheet/pdf/7c879a63da0ce2c4dfeca5bcba605d6f.pdf?productCode=C496550
  - JLC part page (Wave Soldering; Standard Only; High): https://jlcpcb.com/partdetail/BATWIRELESS-BWSMA_KE_P001/C496550
- XUNPU SMA-KE-347-H13.5-1.6: https://datasheet.lcsc.com/datasheet/pdf/e3e9b75c1c094a8b2b2fd16eda6a22a3.pdf?productCode=C5723200
  - JLC part page: https://jlcpcb.com/partdetail/XUNPU-SMA_KE_347_H13_5_1_6/C5723200
- DreamLNK SMA-KE-P902: https://datasheet.lcsc.com/datasheet/pdf/05c07b98880941b5c16d96057ab79896.pdf?productCode=C914557
- HenryTech HL-SMA-KEP-02: https://datasheet.lcsc.com/datasheet/pdf/4a12ce035bd9ebb64181d181ed72e3fd.pdf?productCode=C22355857
- Molex 73251-1150:
  - part data (jack, edge mount, 1.60 mm, 18 GHz, reflow 260 °C 10 s 2 cycles): https://docs.rs-online.com/50ba/A700000015082286.pdf
  - sales drawing, not retrieved: https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/732/73251/732511150_sd.pdf
  - JLC part page: https://jlcpcb.com/partdetail/MOLEX-0732511150/C841205
- Cinch 142-0701-801: https://datasheet.lcsc.com/datasheet/pdf/ca1a9fb5de27cad5591d0c7fa9ee2bd3.pdf?productCode=C3173345
- JLC parts API (stock and prices, 2026-10-15): POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
- JLC stackup templates (live, 2026-10-15): POST https://cart.jlcpcb.com/api/overseas-shop-cart/v1/shoppingCart/getImpedanceTemplateSettings
  with {"cuprumThickness":1,"insideCuprumThickness":1,"stencilLayer":4,"stencilPly":1.6}
- JLC impedance calculator: https://jlcpcb.com/pcb-impedance-calculator
  - backend POST https://jlcpcb.com/api/jlcTools/impedance/calc, with results over wss://tools.jlc.com/jlcTools/webSocket/;
  - template and material data from `/api/jlcTools/impedance/selectPageImpedanceDefaultTemplate`;
  - copper and coverlay config from `/api/jlcTools/impedance/impedance-config/{copper-trace-width,coverlay}/list`;
  - user guide (mask Dk 3.8, coating, copper): https://jlcpcb.com/help/article/User-Guide-to-the-JLCPCB-Impedance-Calculator
- JLC PCB capabilities (copper to routed edge ≥ 0.2 mm; outline ±0.2 mm; thickness ±10 %): https://jlcpcb.com/capabilities/pcb-capabilities
- L-com RG316 (OD 2.49 mm; minimum bend radius 13 mm; 102 dB/100 m at 1.5 GHz): https://l-com.com/Images/Downloadables/2D/RG316-1K_2D.pdf
- Project: `docs/REQUIREMENTS.md` (F10, P1–P3, M1–M3), `docs/ORDERING.md` §3–5 and §7, parent `docs/VEHICLE.md`,
  `reports/Compact rocket GPS and radio.md`, `research_notes/…/rf_integration.md`, and the pass-1 electrical and
  requirements reviews (block contents and part references).

## 8. Inferences (not measured, not taken from a primary source)

- The SMA coupling-nut size (5/16″ hex) and the mated-plug length (about 16 mm beyond the jack face) are
  allocations. Verify them against the harness plug actually bought.
- The coax-loop envelope assumes RG316 bent once at 13 mm radius in an oblique plane. Repeated-flex limits are
  larger, and a thinner coax (RG178 or 1.13 mm) shrinks the zone.
- The sub-0.01 dB mismatch figures and the pad-mismatch estimates are hand calculations from JLC's impedance
  values.
- That a pure +18 mm translation leaves R6 DRC, actuator copper and reference-plane results unchanged in the
  untouched region. Rerun the gate and the copper solve.
- The board-level isolation between the two fenced RF lines (L15).
- The 1.5× paste-area suggestion for the MAX-F10S on a 0.10 mm stencil.
- The suggested routing corridors to U1.
- The BAT WIRELESS jack sharing the Kinghelm KE8-G geometry (similar drawing values). Confirm on parts.
- Thermal: the GNSS TCXO sits 9.6 mm from the logic-buck IC on the opposite side. Expected benign; not measured.
