# R11 stage B: board, stackup and placement (2026-11-02)

Stage B of `r11_plan.md` §4. `m3_design/r11_pcb.py` builds `m3_design/r11/m3.kicad_pcb` from the stage-A netlist
(`schematic.net.xml`) and `m3_design/r11_place.tsv`; `m3_design/r11_build.sh` runs it after stage A, then
`fit_check --profile r11` and a native DRC with schematic parity. The board carries no copper but the footprints' own.
Nothing is committed or ordered. Decisions D-R11-10 … -14 are in `R11_DECISIONS.md`.

Evidence labels as AGENTS §2.5. Coordinates are board mm: x east (0 … 46), y forward (0 aft … 50 forward, R10's
convention), F = top, B = bottom; bottom rotations are KiCad's after the flip.

## 1. Outline 46 × 50 mm, and why it is not shorter

46 × 50 mm meets D-R11-02's target (ceiling 56). The length is set by the west column of the top face, which holds
parts that are either tall or on the fire path and so cannot move to the bottom (Measured, courtyards on the board):

| y (mm) | Top, west column (x 4.7 … 19.4) |
|---|---|
| 0.555 – 6.545 | aft GH row (J400) |
| 6.905 – 11.495 | D8 TVS, C80 / C96 |
| 12.055 – 16.345 | R166 damper, C89 / C95 |
| 17.655 – 21.545 | Q120 / Q121 load switch |
| 22.455 – 26.745 | R134 2 Ω |
| 27.105 – 33.575 | Q124, gate network, C128 |
| 33.755 – 42.845 | C84 (10 mm can; top face only, P2) |
| 43.455 – 49.445 | forward GH row (J420) |

The bottom of the same column is full as well (U9, its divider and timing parts, D9, C82, the sense banks, the probe
pads, U11, U5). The GH rows cannot shrink: each port's mouth must face its own short edge (a plug across a long edge
leaves the bore, D-R11-12), and the corner supports keep 7.3 mm of each short edge free. Going to 48 mm would need
about 90 mm² of the west column moved to the bottom, which has no room there; not attempted (Inference).

## 2. Density

| Face | Parts | Courtyard (union, inside the outline) | Face | Fill |
|---|---|---|---|---|
| Top | 79 | 1301 mm² | 2300 mm² | 56.6 % |
| Bottom | 137 | 745 mm² | 2300 mm² | 32.4 % |
| Both | 216 | 2046 mm² | 4600 mm² | 44.5 % |

LEVIA-H7 is 45 % (r11_plan §2). The top is denser because the connectors, C84, LS120, J3, U1 and U3 are there; the
bottom keeps the routing room under U1 and the via fields.

## 3. Stackup (D-R11-03)

JLCPCB **JLC06161H-3313**, 6 layers, 1.6 mm, ENIG, from JLC's published table
(https://jlcpcb.com/impedance, 6-layer stackups, item 2; read 2026-11-02; Datasheet):

| Layer | Role | Thickness |
|---|---|---|
| F.Cu | parts, signals | 0.035 mm (1 oz finished) |
| prepreg 3313 × 1 | | 0.0994 mm |
| In1.Cu | GND, solid | 0.0152 mm (0.5 oz) |
| core | | 0.55 mm |
| In2.Cu | power regions | 0.0152 mm |
| prepreg 2116 × 1 | | 0.1088 mm |
| In3.Cu | signals | 0.0152 mm |
| core | | 0.55 mm |
| In4.Cu | GND, solid | 0.0152 mm |
| prepreg 3313 × 1 | | 0.0994 mm |
| B.Cu | parts, signals | 0.035 mm |

Copper and dielectric sum 1.538 mm; the board thickness is set to the nominal 1.6 mm (fit_check's transform). Inner
copper is 0.5 oz: stage C's IPC-2152 widths for inner-layer power use 0.0152 mm, not R10's 1 oz. JLC offers 1 oz
inner copper at extra cost (the impedance page lists 0.5 / 1 / 2 oz inner options); not chosen. The F / In1 and
B / In4 spacings are 0.0994 mm (each outer signal layer over solid GND); In3 is 0.1088 mm under In2 and 0.55 mm over
In4, as check_r11 K-region assumes. Dielectric constants are not used (no controlled impedance; USB 2.0 full speed).
The other 6-layer table entries (e.g. JLC06161H-2116: 0.3 mm cores, 2 × 7628 between In2 and In3) were not chosen:
-3313 matches LEVIA-H7's thin-outer, thick-core arrangement. The "No requirement" entry (2116 prepreg 0.1164 mm) is
not the same build; the order must name JLC06161H-3313 (stage D, ORDERING).

Layer names are KiCad's canonical ones; In1, In2 and In4 are typed "power", In3 "signal".

## 4. Mounting holes (D-R11-10)

Four M3 supports, 3.2 mm, at (3.5, 3.5), (42.5, 3.5), (3.5, 46.5), (42.5, 46.5); nylon hardware, ≥ 4 mm standoffs as
R10. fit_check: nearest bottom envelope J430 3.55 mm (≥ 3.5), nearest top body J1.2's wire allowance 3.95 mm (≥ 3.8).
Plate stiffness: spans 39 × 43 mm, shorter than R10's (Inference; `tools/plate_model.py` has no r11 profile and was
not run). check_r11's M-3 with pinned supports calls R10's five-support rule, so stage B does not pin them in
`r11_gate_data.json`; the corner rule (fit_check / M-3 unpinned) holds them.

## 5. Edge assignment (D-R11-13)

| Edge | Part (side) | Position | Wires / plug | Reason |
|---|---|---|---|---|
| Aft (y 0) | J400 GH-2 (F) | x 11.0, mouth aft | switch pair | beside the power front end (U9, R80, R165, D402) |
| Aft | J122 GH-5 servo (F) | x 21.4, mouth aft | servo signals | servo leads come from the fin can aft |
| Aft | J9 GH-6 camera (F) | x 32.8, mouth aft | camera | camera supply chain (U402, C431, U13) aft-centre |
| Forward (y 50) | J420 / J410 / J440 GH-4 (F) | x 12.4 / 23.0 / 33.6, mouths forward | radio / GPS / AUX | the three identical ports together; U1's UART balls (J8–K9, E10 / F10) face east / forward |
| West (x 0) | J1 wire pads (F, plated) | (2.3, 10.5) GND, (2.3, 14.3) BAT_IN | AWG 20 from the pack | pack is aft of the board; leads turn aft along the west side |
| West | J121 wire pads (F, plated) | (2.3, 20.9) IGN, (2.3, 24.7) OUT | AWG 20 pigtail | beside the pyro cell; pigtail runs forward to the bulkhead terminal |
| East (x 46) | J3 USB-C (F) | y 30.0, mouth east | bench | shell 0.45 mm proud of the edge, as R10's J3 |
| East | J430 microSD (B) | (37.5, 13.05) | card | bottom, east-aft; hinge opened with the board unbolted (as R10) |

GH mouths sit 1.1 mm inside their edge (fit_check: within 3 mm). Mated GH envelopes stay in the bore with the plug
beyond the edge (fit_check OK). The wire-pad allowances (fit_check's 1.8 mm OD model) clear the bore by 0.36 mm.

## 6. IMU axis map (D-R11-11)

U4 (ISM6HG256X; LSM6DSV320X alternate on the same land) at B(23.0, 20.5), rotation 180 after the flip, as R9 / R10:

| IMU axis | Board axis |
|---|---|
| +X_imu | −x_board (west) |
| +Y_imu | −y_board (aft) |
| +Z_imu | out of the bottom face |

Roll rate = −gyro_Y; forward thrust reads −a_Y. Lever arm to the roll axis: x = 0.000 mm (U4 centre on x = 23; R10
−6 mm), z ≈ −2.06 mm (Inference, as R10). U4 sits 7.5 mm aft of U1's centre, between the support pairs, ≥ 19 mm from
LS120 (top, (40.0, 39.6)). Pads: 1 MISO, 4 INT1, 12 CS, 13 SCK, 14 MOSI face U1's row A (aft row: A5–A7, C4, C5). The
R10 rule areas are re-derived on B.Cu from the placed courtyard: IMU_body_B (no via, no pour), IMU_no_internal_tracks
(pad-ring interior), BARO_body_B, BARO_no_inter_row_tracks. `r11_gate_data.json` 'imu': rotation 180, lever 0.0 mm.

## 7. Heat sources and the barometer (D-R11-14)

U5 at B(9.0, 40.0), west-forward. Distances centre to centre (Calculation on the placement):

| Source | Where | Distance to U5 |
|---|---|---|
| U401 TPS7A91 LDO (largest, up to about 0.37 W, Inference) | F(41.5, 22.4) | 37.0 mm |
| U400 AP63201 buck | F(40.0, 9.6) | 43.4 mm |
| L400 | F(33.9, 10.5) | 38.6 mm |
| U402 camera switch | F(22.0, 9.4) | 33.2 mm |
| U2 3V3 buck | F(23.6, 35.8) | 15.2 mm |
| L1 | F(18.6, 36.0) | 10.4 mm |
| U9 eFuse | B(11.5, 10.6) | 29.5 mm |
| R166, D9 (transients only) | F(10.1, 14.0), B(10.6, 15.6) | 26.0, 24.5 mm |

C84 is above U5 on the top (not a heat source). The port faces the sled side and must not be covered (stage E).

## 8. Pyro cell

All on the west side between J1 and C84, the fire path wholly on F.Cu:

* Top: Q120 F(8.0, 19.6) and Q121 F(12.3, 19.6) (BAT_IN → ACT_FET_S → RAW_ACT), their gate network R119 / R120 /
  R121 / C120 east of them, Q122 F(17.6, 25.4) with R122 / R123 / C123; R134 F(11.6, 24.6) from RAW_ACT to J121.2
  (IGN); Q124 F(7.9, 29.3) beside J121.1 (OUT) with R126 / R127 / R128 / C126 and TP122; C128 at Q124's drain; TP120
  on RAW_ACT; the high legs of both sense dividers on OUT / RAW_ACT (R173, R131, R132) on the top beside their nets.
* Bottom, under the cell: the low-voltage halves of the continuity (R129, R130, R178, C127) and bus-sense (R175,
  R133, R180, C129) banks, D120, and the probe pads TP80 / TP81 / TP88.
* U1's pyro-control balls are on its west column (PE4 C3, PC1 F2, PC0 F1, PC5 H4), about 4–14 mm from their parts (centre to centre).

Fire loop (J1.1 → Q120 → Q121 → R134 → J121.2 → match → J121.1 → Q124 → GND → J1.2) spans about 12 × 20 mm.

## 9. S-8 plan (≥ 1.0 mm from pyro / arming plated barrels to foreign inner copper, all four inner layers)

Placement keeps the BARREL_NETS (RAW_ACT, PYRO1_IGN, PYRO1_OUT, PYRO1_GATE, PYRO1_GATE_N, ACT_GATE, ACT_DRV, ACT_EN,
ACT_EN_MCU, BAT_ENABLE, BAT_SW_RETURN) on one face wherever possible, so stage C needs few barrels:

* Every part on RAW_ACT, IGN, OUT, PYRO1_GATE, ACT_GATE, ACT_DRV and ACT_EN is on the top: those nets need no via. The
  only barrels are J121.1 / J121.2 themselves.
* PE4 (C3) and PC1 (F2) escape U1 on F.Cu to R126 / R122 (west, no via; C3 takes the C / D channel past C2 / C1).
* BAT_ENABLE (U9.1, R81, C87, R165) is all on the bottom: no via. BAT_SW_RETURN needs J400.2 (top) → D402 / R165
  (bottom): one via pair at J400, given 1.0 mm voids on In1–In4.
* J121.1 (PYRO1_OUT, GND counts): voids of 1.0 mm beyond the barrel wall (Ø1.3 hole → Ø3.3 void) on In1 and In4 GND
  and on In2 / In3; J121.2 (IGN): same on In2 / In3, GND exempt. J121.1 / J121.2 carry no unconnected inner rings
  (R10 D-R20-05).
* No other plated hole lies within 5 mm of J121 (J1's pads are 6.6 mm away, centre to centre).

## 10. Routing plan for stage C

**Vias** (JLC multilayer: 0.15 mm hole / 0.25 mm via minimum; filled and plated-over vias are the default from six
layers; https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-02): signal vias 0.40 / 0.20 mm (annular
0.10 mm); power and GND vias 0.45 / 0.25 or 0.6 / 0.3 mm. No via in an SMD pad (M2); the BGA uses dog-bone vias.

**TFBGA-100 fan-out** (0.8 mm pitch, 0.40 mm lands; 0.1 mm track / 0.1 mm clearance rules from the DRU):

* A via 0.40 / 0.20 at an interstitial site is 0.566 − 0.2 − 0.2 = 0.166 mm from the four balls round it; vias at
  adjacent sites are 0.40 mm apart. A 0.1 mm track passes between two lands (0.40 mm gap, 0.15 mm each side).
* Ring 1 (rows A / K, columns 1 / 10) and ring 2 (rows B / J, columns 2 / 9) escape on F.Cu, one track per channel.
  Ring 3 and inward is mostly NC or power (E4–E6 GND; F4–F7 3V3; E7 / F8 VCAP), so the signal balls there (C3 PE4,
  C4 / C5 IMU, C6, C8 / D8 SD, D5 BOOT0, D6, G3, G5 QSPI_CLK, H3–H6) escape on F.Cu through channels whose outer balls
  are NC, or by one dog-bone via to In3.
* Power: each 3V3 ball (B2, D2, F4–F7, K1) and GND ball (C2, E4–E6, G1, J1) takes its own dog-bone via to In2 3V3 /
  In1 + In4 GND; VCAP1 (F8) / VCAP2 (E7) and the 3V3 decouplers C13–C18, C21 sit on B.Cu directly under the field
  and join those vias; VDDA (H1) to the In2 3V3A island.
* Directions (U1 rotation 0): column 1 west (HSE C1 / D1 to Y1 B(16.6, 26.0); NRST; PC0 / PC1 / PE4 / PC5 to the
  pyro cell); row A aft (SPI1 to U4, I2C1 to U5 via In3, SWD to J2, BUZZ_DRV); column 10 east (USB to D4 / J3, AUX
  USART6 to J440 on In3, SD to J430 on B.Cu); rows J / K forward (GPS / radio to J410 / J420 on In3, camera UART to
  U12, servo PWM to R150–R153 at J122 on In3, QSPI IO1 / IO3 to U3).

**Planes**: In1 / In4 solid GND. In2 regions: BAT_IN / RAW_PROTECTED west-aft (front end), VLOGIC west-forward (U11,
C84, U2), 3V3 under U1 and the east-forward block, a 3V3A island from R164 B(16.4, 30.8) over VDDA, U4 and U5,
PORT_5V3 / PORT_4V8 east-aft and a PORT_4V8 strip to the forward ports, CAM_5V at J9. In3: signals referenced to In4.

**Channels left open**: top x 13.5 … 19.4 between the pyro cell and U1 (PE4 / PC1 / HSE); bottom x 19 … 29 aft of
U4 and forward of U1 (In3 drops for camera / servo / ports); the bottom band y 32 … 43 between U1 and the forward
ports. Crystal: Y1 on the bottom 3.8 mm from C1 / D1; keep In2 / In3 clear under it (R10's Y1_In2_keepout) in stage C.

## 11. Checks run (this stage)

* `r11_pcb.py` legality (in the build): no courtyard overlap on either face; courtyards ≥ 0.25 mm from the long
  edges and ≥ 0.5 mm from the short edges (J3 excepted, as R10); bottom courtyards ≥ 3.5 mm from support centres and
  ≥ 1.5 mm from foreign plated pads; top courtyards ≥ 3.8 mm from support centres. Passed.
* `fit_check --profile r11`: OK (CAD envelopes only); worst bore margin 0.36 mm (wire-pad allowances), deepest bottom
  part C421 at z −4.30 mm (2.7 mm below the board).
* Native DRC (`kicad-cli pcb drc --schematic-parity --severity-all`): 0 violations, 0 parity issues, 497 unconnected
  items (stage C). The parity check needed KiCad's '{slash}' escape on one pin-derived net name (U4 pad 9).
* `tools/check_r11.py --stage placement` (read only; the gate is another lane's): S-5, S-6, S-7, W-1, W-2, LC-1, M-1,
  M-5, M-6, M-7, M-8 and K-lands pass. S-1 / S-3 (`KeyError: 'PC0'` / `'PC1'`, the pin-table lookup), S-2 (U1's
  ball ties), S-4 (J1 / J121 wire pads are excluded from BOM / CPL by D-R11-05) and K-loader (R10's LQFP allowances)
  fail in the gate's own data, not on the placement; M-3 failed only while supports were pinned (now unpinned).
* Determinism: two builds gave the same SHA-256.
* Renders (`kicad-cli pcb render`, top / bottom): in the session scratchpad, not committed.

Not verified: plate modes (no r11 plate profile), wire bend room and harness, GH plug insertion with real wires, JLC
DFM on the panel and the short-edge rails, copper (none yet), every electrical figure that depends on copper.
