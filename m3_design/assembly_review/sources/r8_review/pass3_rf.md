# R8 pass 3: RF layout, interface buses and coexistence review

Independent read-only review, 2026-10-20, of `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18` (checked before and after this review, unchanged),
netlist `schematic.net.xml` `0cc1ed69…` (unchanged since pass 1). Dimension: RF (REQUIREMENTS F10, the RF parts of
M1 / M2, the rigid strip and its hashes, the U1-to-strip interface buses, F10's 5 mm separation, GND vias at layer
changes, the fence, coexistence paths and the reset states of the radio and GNSS lines). Vehicle-level choices and
firmware beyond the pin / interface contract are out of scope. Comparisons used the R7 board
(`git show 431025d:…/m3.kicad_pcb`, `c872a3d3…`) and the pass-2 board (`6600ef94…`, taken from fix pass 2's
`pre_fix2_state.tgz`), both copied into the session scratchpad and deleted afterwards.

Coordinates: KiCad mm, y = 0 at the aft (SMA) edge.

## 1. Summary

**No Critical. No Major. Three Minor (R8P3-RF-01 … -03), all records / bench-procedure items; the copper is clean.**

- **Pass 2's one RF finding is closed.** R8P2-RF-01 (limiter via's GND partner): M3_R8 l. 407 and `route_check.py`
  l. 243 now give (10.37, 7.08) at 1.22 mm, which is what the board measures (1.221 mm).
- **Fix pass 2 did not touch the RF area.** A full item diff of `6600ef94…` → `990c8040…` finds 13 items removed and
  16 added. None is in the strip (y < 23.5) or on an RF-family net.
  - The only changes in the bus region (y < 50) are three GND vias that went from 0.6 to 0.5 mm, at the same centres
    (D98), and the C83.2 GND link split (D99).
  - The GND fill is **byte-equal in area** on all four layers in the strip, the band and the bus. In2 3V3 gains
    0.197 mm² round the smaller via (33.9, 45.2).
  - The nearest changed item to RF-family copper is that via, 0.504 mm from the RADIO_NRST lane (pass 2: 0.454 mm).
- **Rigid strip.** All 12 digests equal `RIGID_BASELINE`, recomputed by this review on R7, on the pass-2 board and on
  this board.
- **Interface buses.**
  - All 12 interface nets run on F.Cu over In1 GND, with no via.
  - In1 GND is missing under them only inside the antipads of the five RF-family layer-change vias. The one other gap
    is pass 2's 0.1 mm-outside-the-lane edge at RADIO_NRST beside U1's east face, unchanged.
- **Fence.** 25 vias, 4 openings (2.015 / 2.600 / 2.100 / 2.050 mm, each crossed by its lanes) and 14 crossings, all
  on F.Cu. Every fence via is joined to GND on all four layers.
- **F10 separation.** Nearest part 5.94 mm (R306–U1); nearest fast line 5.075 mm (R306–USB_DM). Both unchanged, both
  gated.
- **GND vias at layer changes.** All five RF-family vias have a GND via within 0.721–1.221 mm.
- **Reset states.** These hold, with the netlist and pin table unchanged.
- **New findings, all Minor:**
  - **R8P3-RF-01:** fix pass 2's bootloader-jump wording allows a GPIOE reset as the first step. That puts the SX1262
    into reset, with BUSY pulled up, before the "put the SX1262 to sleep" step that follows.
  - **R8P3-RF-02:** the coexistence bench step names only the 25 MHz spur near L1. The MAX-F10S always tracks its L5
    band as well, and 25 MHz × 47 = 1175.000 MHz falls inside it.
  - **R8P3-RF-03:** D98 and an `r8_power.py` comment call R78.2's GND via (33.9, 45.2) "C76.2's".

## 2. Previous pass in this dimension: closure

| Pass 2 finding | Fix pass 2 disposition | On `990c8040…` |
|---|---|---|
| R8P2-RF-01 (Minor, not worth fixing): records gave the GNSS_VCC_RF limiter via's GND partner as (9.025, 8.325) at 1.39 mm; the nearest is (10.37, 7.08) at 1.22 mm | Fixed (records): M3_R8, `route_check` A3 reason text | **Closed.** M3_R8 l. 406–407: "GND partners 1.10 / 1.22 mm, the second the rigid strip via (10.37, 7.08)". `route_check.py` l. 243: "(10.37, 7.08) 1.22 mm away". Measured: (10.41, 8.3) → (10.37, 7.08) 1.221 mm; the next is (9.025, 8.325) at 1.385 mm. R8_VALIDATION l. 228 records the disposition. |

Pass 2's observations still hold and are unchanged (§5): In1 under RADIO_NRST at U1's east face, and the F10 fast-line
margin of 5.075 mm.

## 3. Fix pass 2 regression check (RF area)

`bdiff.py` (canonical tracks, vias, footprints with pad nets and zone connections, and zone outlines; for every added
item, its edge-to-edge distance to RF-family copper, which is RADIO_*, GNSS_*, 3V3_RADIO and 3V3_GNSS):

| Change (D) | Where | Nearest RF-family copper |
|---|---|---|
| GND via 0.6 → 0.5 mm, R78.2's (labelled "C76.2", R8P3-RF-03) (D98) | (33.9, 45.2) | 0.504 mm, RADIO_NRST lane x 33.4, F.Cu (was 0.454) |
| GND via 0.6 → 0.5 mm, C75.2's (D98) | (41.4, 47.8) | 8.30 mm |
| GND via 0.6 → 0.5 mm, R72.2's (D98) | (41.45, 32.6) | 6.47 mm (RADIO_NRST) |
| C83.2 GND link split (D99) | B.Cu (9.55–11.1, 35.4) | 7.0 mm plan view (GNSS_TXD_MCU, In1 / In2 between) |
| R81, BAT_ENABLE spine, two grid vias, pad via U9.8, island via, V_IN1 0.5 mm, J123.2 relief, In2 BAT_IN trim, R8_GND_In2 outline | y 60–118 | > 12 mm (none in reach) |

`fillxor.py`, P2 → R8, mm² (lost / gained):

| Region | F.Cu GND | In1 GND | In2 GND | B.Cu GND | In2 3V3 |
|---|---|---|---|---|---|
| strip (y < 23.5) | 810.599 = | 988.259 = | 1003.021 = | 963.440 = | — |
| band (y 23.5–28.5) | 164.427 = | 221.552 = | 57.320 = | 196.154 = | 148.484 = |
| bus (y 28.5–50) | 570.360 = | 920.567 = | 211.825 = | 640.269 = | +0.197 (round (33.9, 45.2)) |

So pass 2's strip, fill, module-ground and pour-piece measurements carry over unchanged to this board. The figures below
were re-measured anyway.

## 4. Measurements on the final board

### 4.1 Rigid strip and its hashes

- **`tools/check.sh`** (run in this review): exit 0.
  - DRC 0 at every severity; unconnected 0; parity 0; ERC 0.
  - Audit OK; silkscreen OK; `check_r8` OK (0 issues).
  - `route_check` r8: 0 failing, 3 allowlisted, 0 stale, 0 leftovers.
  - Actuators OK; fit OK.
- **`tools/test_r8_check.py`:** 23 tests OK.
- **Rigid digests** (`rigid3.py`, `check_r8.rigid` on three boards). All 12 groups are equal to `RIGID_BASELINE` on R7
  `c872a3d3…`, on P2 `6600ef94…` and on R8 `990c8040…`:

  | Group | Items | Digest (first 16) |
  |---|---|---|
  | `strip_parts` | 22 | `c71c1250c4f732ae` |
  | `strip_rf_copper` | 11 | `7a2598349ad81c5f` |
  | `strip_gnd` | 176 | `bfcbe417a3b45e12` |
  | `strip_rule_areas` | 5 | `d105af8bf59da746` |
  | `strip_gcpw` | 8 | `8b46f56919611ca6` |

  The other seven groups (outline, holes, J122 tie, J1, PYRO_BLOCK, CH1 parts and CH1 copper) are also equal.
- **Other `check_r8` evidence on this board:**
  - `rf_strip`: 69 F.Cu, 28 B.Cu and 205 vias, all on allowed nets;
  - line stitching: GNSS west 3.90, east 2.65; radio 1.55 / 1.55 mm; In1 missing under RF copper 0.0 mm²;
  - launches: In2 1025 / 1025 samples each;
  - module ground: U31 In1 / In2 2601 / 2601, U30 In1 1976 / 1976;
  - RF clamp and pi GND pads 0.16 mm from a GND via;
  - strip GND reach: F.Cu 3.04, B.Cu 3.49 mm.
- **Coverage of the hashes.** The hashes leave out the interface resistors, the supply ferrites and bypasses, and
  R311 / R312 (C300, C301, C310–C312, FB30, FB31, R305–R307, R310–R315). They are D11's "feeds and interface", R8's
  to place.
  - Pass 2's item diff showed only the movements D11 allows (C300 0.08, R305 0.13, R312 0.25 mm; R310 left the
    strip).
  - Fix pass 2 moved none of them (§3).
  - Module GND pads (U30.1 / .10 / .12, U31.2 / .7 / .16) are solid (GND_F pad connection THT-thermal, so SMD solid),
    as in R7.

### 4.2 Interface buses U1 → strip

`iface.py`: every track and via of the RADIO_ / GNSS_ / 3V3_RADIO / 3V3_GNSS nets, RF lines excepted. Each F.Cu
segment is sampled every 0.05 mm at its centre and ±0.2 mm against the In1 GND fill (B.Cu against In2 GND); the
launch cut-outs are excluded.

| Net | Copper | Vias |
|---|---|---|
| RADIO_SCK_MCU / RADIO_SCK | 15.73 + 13.19 mm F.Cu | 0 |
| RADIO_MOSI_MCU / RADIO_MOSI | 9.76 + 17.15 mm F.Cu | 0 |
| RADIO_MISO / RADIO_MISO_MCU | 1.48 + 27.90 mm F.Cu (R314 at U31, source end) | 0 |
| RADIO_NSS / BUSY / RXEN / DIO1 / NRST | 32.21 / 32.01 / 40.02 / 25.04 / 41.04 mm F.Cu | 0 |
| GNSS_TXD / GNSS_TXD_MCU | 2.19 + 26.87 mm F.Cu (R305 at U30, source end) | 0 |
| GNSS_RXD_MCU / GNSS_RXD | 9.16 + 19.36 mm F.Cu | 0 |
| GNSS_TP_MCU / GNSS_TIMEPULSE | 25.97 + 2.45 mm F.Cu | 0 |
| GNSS_RESET_N / GNSS_SAFEBOOT_N | 23.89 / 4.26 mm F.Cu | 0 |
| RADIO_TXEN (R7 loop) | 2.45 F.Cu + 22.72 B.Cu | 2 |
| GNSS_LNA_EN / GNSS_VCC_RF (limiter) | 1.9 F + 5.75 B / 1.9 F + 4.30 B | 1 / 1 |
| GNSS_ANT_DC / SRC / GATE / PD | 1.96 F + 9.02 B / 8.57 B / 6.92 B / 3.44 B | 1 / 0 / 0 / 0 |
| 3V3_GNSS / 3V3_RADIO feeds | 7.13 / 7.23 mm F.Cu | 0 |

All of these are identical to pass 2.

- **Reference.** Misses fall only inside the five layer-change via antipads (each with a GND partner, §4.4). The other
  misses are 28 samples at x 33.6, y 42.8–44.35, on the +0.2 mm side of RADIO_NRST: 0.1 mm outside the 0.2 mm lane, where
  CAM_MCU_RX's hop via (33.95, 44.0) and the 3V3 via (34.0, 43.1) bring their antipads. This is unchanged from pass 2,
  and the lane centre is covered.
- **Neighbours of the weakly held or interrupt lines** (`aggr.py`, other-net copper within 0.6 mm, same layer). NSS,
  NRST, RXEN, DIO1, BUSY, RESET_N and SAFEBOOT_N have only these neighbours:
  - U1's and U31's own pin pitch (0.20 / 0.37 mm);
  - R315's pads beside NSS (0.23 mm);
  - CAM_MCU_RX's and a 3V3 via beside NRST (0.20 / 0.25 mm);
  - NSS's corner run past the ends of U1.48–.51 (VCAP1, GND, 3V3, NC; 0.20–0.265 mm);
  - QSPI_CLK's escape 0.35 mm from the U1.39 pad.

  Every one of these lines is driven push-pull or held by a resistor in operation, except GNSS_RESET_N, which is
  released to the module's pull-up. The MAX-F10S needs RESET_N low ≥ 1 ms to reset (DS R03 Table 10, pin 9), so a
  coupled edge cannot reset it (Inference).
- **Bus geometry.** The lanes are orderly rivers at 0.5 mm (radio) and 0.6 mm (GNSS) pitch, with no layer change. The
  info-only items on these nets are R7's or recorded in C19:
  - extra_bends ×3 (GNSS river);
  - u_turn ×2 (NRST round U31's east side; R7's TXEN loop);
  - off-centre entries at U31.15, C310.1, C301.1 and TP30.1.

### 4.3 F10 5 mm separation

`check_r8.rf_separation` (in the gate; `r8.json`). The restricted set is 22 parts: U1, U3, Y1, the buck and camera
supply parts.

- **Nearest restricted part, per RF part:**
  - R306 5.94 mm (U1);
  - R310 / R313 / R315 6.04 mm (U1);
  - FB31 6.66 mm (U7);
  - C310 7.86 mm (C73);
  - U31 9.41 mm (U7).
- **Nearest fast-line copper, per RF part:**
  - R306 5.075 mm (USB_DM track (15.39, 35.64));
  - R315 5.819 mm (USB_DM);
  - R310 / R313 6.285 mm (QSPI_IO3 / IO0 at U1);
  - FB30 6.989 mm (USB_DM at D4.6).

All of these equal pass 2 and M3_R8 §RF.

### 4.4 GND vias at layer changes (RF-family nets)

| Via | Size | Nearest GND via | Next |
|---|---|---|---|
| GNSS_ANT_DC (11.45, 5.15), rigid | 0.6 | 1.011 (11.6, 4.15) | 1.571 |
| RADIO_TXEN (31.13, 20.15) | 0.5 | 0.721 (31.73, 20.55) | 1.912 |
| RADIO_TXEN (28.59, 7.80) | 0.5 | 0.721 (28.19, 7.2) | 1.184 |
| GNSS_LNA_EN (11.51, 8.30) | 0.5 | 1.100 (12.61, 8.3) | 1.670 |
| GNSS_VCC_RF (10.41, 8.30) | 0.5 | 1.221 (10.37, 7.08) | 1.385 |

No other RADIO_ / GNSS_ net has a via. All five are within AGENTS §3's 1.5 mm, as R7 had them.

### 4.5 Fence and crossings

`fence.py`: 25 GND vias (0.5 / 0.3 mm) on y 23.3, at x 0.9, 2.9, 4.9, 6.4, 7.685, 9.7, 12.3, 14.2, 16.2, 18.2, 20.0,
22.1, 24.15, 26.0, 28.0, 30.0, 31.8, 33.0, 34.4, 35.8, 37.8, 39.4, 40.6, 42.6 and 44.6.

- **Gaps:** edge 0.9 / 1.4 mm; largest 2.6 mm.
- **Connection:** every via touches GND fill on all of F.Cu, In1, In2 and B.Cu. F.Cu is partial (6–7 of 8 probe points)
  at the three vias between lanes (7.685, 9.7, 22.1).

| Opening | Width | Lanes |
|---|---|---|
| 7.685–9.70 | 2.015 | GNSS_RXD, GNSS_TP_MCU |
| 9.70–12.30 | 2.600 | 3V3_GNSS (0.3 mm) |
| 20.00–22.10 | 2.100 | RXEN, BUSY, MISO_MCU |
| 22.10–24.15 | 2.050 | MOSI, NSS |

- **Crossings:** 14, all on F.Cu.
  - The single-lane gaps are 1.20–2.00 mm.
  - Lane-to-ring gaps are 0.15 mm (MISO_MCU, MOSI at (22.1, 23.3); C12 #6 / #7), 0.175 mm (GNSS_RXD at 7.685) and
    0.225 mm (TXD_MCU).
- **Planes near the fence:** no In1, In2 or B.Cu track and no via other than GND lies in y 22.6–24.0. The In2 3V3 pour
  starts at y 24.0 (x 0.5–35.3).
- **Why the 2.60 mm opening has no middle via** (Inference from coordinates): a via at x ≈ 10.4–10.6 would come
  within about 0.06 mm of C300.2's pad (9.78–10.58, y ≤ 22.99). The opening is within D16's 2.7 mm and under F10's
  λ/20 (4.4 mm at L1).

### 4.6 Coexistence paths

- **Unchanged (rigid):** RF lines 15.45 mm apart, jacks 18.69 mm, module courtyards 7.66 mm. Each module has its own
  ferrite (FB30 / FB31, BLM18KG221SN1D) with local bulk.
- **Supply:** each ferrite is fed by one 3V3 via from the In2 3V3 pour, (12.33, 24.4) and (35.1, 24.4), 22.8 mm apart.
- **Aggressors:**
  - U8 / L3 (camera buck) are 13.49 / 17.53 mm from U31;
  - U1 is 15.06 mm and Y1 25.37 mm from U30;
  - the logic buck is ≥ 43 mm away.

  None moved in fix pass 2.
- **Shared paths:** no radio lane changes layer or comes within 5.44 mm of U30's body (RXEN), or within 6.0 mm of the
  GNSS RF copper.
- **Clock harmonics in the GNSS bands** (arithmetic):
  - The MAX-F10S receives L1 / E1 / B1C at 1575.42 MHz and L5 / E5a / B2a at 1176.45 MHz, and "single-band operation
    is not supported" (DS R03 §1.3, Table 4).
  - The HSE 25 MHz falls at 63 × 25 = 1575.000 MHz (−0.42 MHz, recorded in ORDERING §5) and at
    47 × 25 = 1175.000 MHz (−1.45 MHz, inside the 10.23 Mcps L5 / E5a main lobe; not recorded). See R8P3-RF-02.

### 4.7 Reset and bootloader states of the radio and GNSS lines

Netlist nodes (`schematic.net.xml`, unchanged):

| Net | Nodes |
|---|---|
| RADIO_NRST | U1.39 (PE9), U31.3, R311.1 (2 kΩ to GND, at (37.0, 14.43) beside U31.3) |
| RADIO_RXEN | U1.56 (PD9), U31.10, R312.1 (100 kΩ to GND) |
| RADIO_NSS | U1.47 (PB11), U31.14, R310.2 (100 kΩ to 3V3, MCU end) |
| RADIO_TXEN | U31.9, U31.19 (DIO2) |
| RADIO_SCK / MOSI / MISO | U1.46 PB10 → R313 33 Ω → U31.15; U1.53 PB14 → R315 33 Ω → U31.13; U31.12 → R314 33 Ω → U1.54 PB15 |
| RADIO_BUSY / DIO1 | U1.55 PD8 / U1.45 PE15 |
| GNSS_RESET_N | U1.61 (PD14), U30.9; no capacitor |
| GNSS_TIMEPULSE → GNSS_TP_MCU | U30.4 → R307 1 kΩ → U1.62 (PD15); pin table row 62: "never pulled down" |
| GNSS_TXD → GNSS_TXD_MCU | U30.2 → R305 220 Ω (at U30) → U1.64 PC7 |
| GNSS_RXD_MCU → GNSS_RXD | U1.63 PC6 → R306 220 Ω → U30.3 |
| GNSS_SAFEBOOT_N | U30.18 → TP30 only |

The U30.5 / 6 / 15 / 16 / 17 pins (EXTINT, V_BCKP, VIO_SEL, SDA, SCL) are open.

- **MCU in reset or blank:** every GPIO is analog and high-Z.
  - R311 holds NRST at about 0.13 V (against the SX1262's 50 kΩ pull-up; R7 pass2_electrical §3.2), so the radio
    cannot transmit.
  - R312 holds RXEN low, and R310 holds NSS high, so MISO is high-Z.
  - The GNSS runs on its RESET_N pull-up (DS R03 Table 11).
  - PD15 is high-Z, so SAFEBOOT_N, which is internally tied to TIMEPULSE through 1 kΩ (DS R03 Table 10 note 14), is
    not pulled low at GNSS start-up.
- **ROM bootloader** (firmware jump only; BOOT0 tied low by R5, not on J2):
  - PB10 / PB11 are USART3, PB14 / PB15 USART1 (AN2606 Table 135, per D2).
  - NSS idles high, so USART3 is never selected.
  - PB14 drives only the MOSI input of an SX1262 held in reset.
  - PB15 sees a high-Z MISO with the loader's pull-up.
  - PE9 keeps its application state unless the binding's step 8 runs. With step 8, R311 holds NRST low. Step 8's new
    wording is R8P3-RF-01.
- **Pins:** `check_r8` contract OK (no RF-part pin on a pyro, arming, actuator, RAW_ACT, BAT_IN, BOOT0 or NRST net;
  U1's map equal to `pin_table.tsv`; loader pins only on the D5 allow-list).

## 5. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P3-RF-01 | Minor (worth fixing) | F10 radio-reset contract ("held low … in the ROM bootloader entered after the firmware's preparation"); D6.8; the binding note is the R8 pin / interface contract | **Fix pass 2's bootloader-jump step lets a GPIOE reset come first, and that puts the radio into reset before the step that sleeps it.** The text now reads: "first drive PE4 low, **or reset GPIOE through RCC_AHB4RSTR** …; **then put the SX1262 to sleep**, drive PE9 low, then return PE9 to analog (or the same GPIOE reset)".<ul><li>A GPIOE reset returns PE9 to analog, so R311 asserts NRST at once. The SX1262 holds BUSY high in reset ("BUSY … PU in reset", R7 pass2_electrical §3.2 row 11; D2 l. 98), so the following SetSleep never sees BUSY low.</li><li>A driver that waits on BUSY before a command (the radio start order in constraint 2 does) hangs, and the jump is not made.</li><li>The result is fail-safe: the radio is in reset and the gate is off, and F10's property still holds. But the contract contradicts itself.</li><li>ORDERING §5 l. 161 describes the preparation as "SX1262 asleep, PE9 returned to analog".</li></ul> | `step9/binding_note.py` l. 50–59 and `r8_binding_note.json` constraint 12; R8_DECISIONS D6.8 (l. 289–299, "First of all, drive PE4 … or reset GPIOE"); REQUIREMENTS F10 l. 60 ("first drive PE4 … low or reset GPIOE …, then put the SX1262 to sleep"); M3_R8 l. 493–497. Pass 1's wording (sleep, PE9 low, then analog or GPIOE reset) had no such conflict. | Reorder in `binding_note.py`, D6.8, F10 and M3_R8: "first drive PE4 low; then (optionally) put the SX1262 to sleep and drive PE9 low; then reset GPIOE through RCC_AHB4RSTR, or return PE4 and PE9 to analog". Regenerate the note. This is text only: no board change and no gate change. |
| R8P3-RF-02 | Minor (worth fixing) | F10 coexistence ("shown on the bench … while GPS C/N0 is logged"); ORDERING §5 coexistence step | **The coexistence step names the 25 MHz spur near L1 only. The receiver always tracks its L5 band too, and a 25 MHz harmonic falls inside that band.**<ul><li>ORDERING §5 l. 164: "25 MHz × 63 = 1575.000 MHz lies 0.42 MHz from L1, an Inference only this test settles".</li><li>The MAX-F10S tracks L5 / E5a / B2a at 1176.45 MHz alongside L1, and "single-band operation is not supported" (DS R03 §1.3, Table 4). By default Galileo E5a and BeiDou B2a are used; GPS L5 is pre-operational.</li><li>25 MHz × 47 = 1175.000 MHz is 1.45 MHz from 1176.45 MHz, inside the 10.23 Mcps main lobe (±10.23 MHz).</li><li>Y1 is 25.37 mm from U30. Any C/N0 drop would show only if the log separates the bands.</li></ul> | DS UBXDOC-963802114-12732 R03 p. 5 §1.3 and Table 4; netlist Y1 "25MHz CL8pF"; ORDERING l. 164; `grep` finds no L5 / 1175 MHz entry in any R8 record. | In ORDERING §5's coexistence step, add: "and 25 MHz × 47 = 1175.000 MHz, 1.45 MHz from L5 / E5a / B2a". Log C/N0 per signal (UBX-NAV-SIG, L1 and L5 separately) in each condition. Optionally add the same to M3_R8 §RF. Text only. |
| R8P3-RF-03 | Minor (not worth fixing) | Records match the board (AGENTS) | **D98 and `r8_power.py` call R78.2's GND via "C76.2's".** On the board, CAMERA_GND's fifth entry is pad (34.675, 45.2), which is **R78.2** (10 kΩ, CAM_5V bleed), with its via at (33.9, 45.2), 0.5 mm since D98. C76.2's own via (pad (35.29, 39.16)) is (34.4, 38.27), still 0.6 mm (D41 l. 1036 has this right). The board matches D98's intent, the four 0.150 mm pairs, so only the label is wrong. | `r8_power.py` l. 469 and l. 475 comment ("C76.2 north-west of the radio lanes"); R8_DECISIONS D98 l. 2048 and D87 correction l. 1934 ("D98's 0.5 mm C76.2 via"); `fix2_handoff.md` ROUTING-01 row; `pads.py`: C76.2 (35.29, 39.16), R78.2 (34.675, 45.2); vias (34.4, 38.27) 0.6 mm, (33.9, 45.2) 0.5 mm. | Replace "C76.2" with "R78.2" in those four places when the files are next edited. The comment does not change the build. |

## 6. Observations (no finding)

- **In1 under RADIO_NRST at U1's east face** (pass 2 §5, unchanged): CAM_MCU_RX's antipad comes 0.05 mm inside the
  lane edge for about 0.3 mm, and the centre is covered. NRST is static and driven, and the SX1262 needs ≥ 100 µs low
  to reset.
- **F10 fast-line margin:** R306–USB_DM 5.075 mm against 5.0 mm. The gate holds it on every build.
- **Fence via (7.685, 23.3)** is 0.155 mm from R305.2's bare pad and 0.175 mm from the GNSS_RXD lane (C12b #2, C12
  #19). This is D16's ≤ 2.7 mm opening rule at a 1.1 mm lane pair. A bridge would only hold a UART line low. It is
  recorded.
- **R7 rigid limiter copper against GND vias.** R301.2 (GNSS_ANT_GATE) is 0.180 mm from the GND via (6.0, 15.0)
  (C12b #22). A bridge there would defeat the antenna current limit; with a shorted antenna as well, it is a double
  fault. It is R7's accepted geometry, held by `strip_gnd` / `strip_parts`, and recorded.
- **Thermal spokes on the radio / GNSS bypass GND pads.** C300.2, C301.2, C310.2–C312.2, R311.2 and R312.2 are
  THERMAL; the module GND pads and the RF clamps are solid. This is the house rule with C16's RF exceptions, unchanged
  from R7. A 0.5 mm spoke adds well under 1 nH to bypasses whose module has its own internal decoupling (Inference).

## 7. Inferences (not measured, or not from a primary source)

- **SX1262 behaviour behind R8P3-RF-01.** BUSY high in reset, and a driver that waits on BUSY before a command, are
  taken from R7 pass2_electrical §3.2 (citing the SX1262 DS Rev 1.2 Table 8-3) and the binding's own start-order
  constraint. I did not re-read Semtech's datasheet for this pass.
- **Harmonic levels in R8P3-RF-02.** Where 25 MHz harmonics fall is arithmetic; their level at U30 is unknown, which
  is why the finding asks for a bench log, not a board change. L5 / E5a / B2a's 10.23 Mcps chip rate is the signal
  definition.
- **Coupling remarks** in §4.2 and §6 (RESET_N pulse width, spoke inductance) are estimates.

## 8. Sources

- **u-blox MAX-F10S data sheet** UBXDOC-963802114-12732 R03 (09-Apr-2025): §1.1, §1.3 Table 4 (supported signals,
  "single-band operation is not supported"), §3.1 Table 10 (pin 9 RESET_N ≥ 1 ms; note 14: SAFEBOOT_N internally tied to
  TIMEPULSE through 1 kΩ), §3.2 Table 11 (pin states):
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
- **u-blox MAX-F10S integration manual** UBXDOC-963802114-12892, §4.4 (layout; as cited in pass 2):
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- **EBYTE E22-900MM22S user manual** v1.3 (pin table; §4.1, no wiring under the module), as verified in R7
  pass2_electrical §3.2:
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2212192008_Chengdu-Ebyte-Elec-Tech-E22-900MM22S_C5333985.pdf
- **Project records:**
  - `docs/REQUIREMENTS.md` F10, M2;
  - `AGENTS.md` §3;
  - `docs/M3_R8.md` §Signal routing, §Ground, §RF, §Firmware;
  - `docs/R8_VALIDATION.md` (Review pass 2, C12, C12b, C16, C19, "R7 pass-4 RF items on R8");
  - `docs/ORDERING.md` §5 l. 157–165;
  - R8_DECISIONS D2, D6 (8), D11, D15–D17, D41, D87, D98;
  - `pin_table.tsv`; `step9/binding_note.py`, `step9/r8_binding_note.json`;
  - `tools/check_r8.py` (`rigid`, `rf_strip`, `fence`, `rf_line_stitching`, `rf_separation`);
  - `tools/route_check.py` l. 243;
  - `m3_design/r8_power.py` l. 469–488;
  - `sources/r7_review/pass2_electrical.md` §3.2;
  - `sources/r8_review/pass2_rf.md`, `fix2_handoff.md`, `fix2_generators.diff`.

## 9. Method (reproduction)

All scripts ran under KiCad 10.0.6's Python (`-I`, `PYTHONDONTWRITEBYTECODE=1`), read only, from the session scratchpad
(`p3rf/py/`). The board copies (R7 from git, P2 from `fix2/pre_fix2_state.tgz`) were deleted afterwards. Nothing in the
repository was written except this report.

- **Gate:** `KICAD_CLI=… tools/check.sh` (exit 0); `python -m unittest test_r8_check` (23 OK).
- **`rigid3.py`:** `check_r8.rigid` on R7, P2 and R8, each group compared with `RIGID_BASELINE`.
- **`bdiff.py`:** canonical item sets (`check_r8.canon_track` / `canon_fp` / `canon_area` plus zone priority), P2
  against R8. For each added item, the minimum edge gap (`check_r8.min_gap`) to RF-family tracks and pads, by layer.
- **`fillxor.py`:** GND and 3V3 fills per layer, intersected with the strip, band, bus and remaining regions, as lost
  and gained areas.
- **`iface.py`:** lengths and vias per net; the nearest two GND vias of each via; In1 (F.Cu) or In2 (B.Cu) GND point
  tests at the centre and ±0.2 mm every 0.05 mm, launch cut-outs excluded; misses beyond 0.6 mm of the net's own vias.
- **`fence.py`:** fence vias at y 23.3 ± 0.06, with GND-fill contact probed at 8 points just outside each ring on every
  layer; the gaps; every non-GND track crossing y 23.3, with its bracket and ring gaps; inner and B.Cu items and non-GND
  pours near the fence.
- **`aggr.py`:** other-net copper within 0.6 mm (same layer) of the weakly held, reset and IRQ lines.
- **`gndpads.py`:** the fraction of each GND pad perimeter (+0.06 mm) inside the F.Cu GND fill; the zone pad-connection
  mode.
- **`pads.py`:** pad nets and positions of U30, U31, the interface parts, C75, C76 and R78.
- **`render.py`:** a PNG of tracks, pads and vias (strip, radio and GNSS halves, the river) for visual inspection.
- **Netlist and records:** `schematic.net.xml` nodes of every RADIO_ / GNSS_ net; binding-note constraints; text
  searches of REQUIREMENTS, M3_R8, R8_DECISIONS, ORDERING and R8_VALIDATION.
