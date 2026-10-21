# R8 pass 4: RF layout, interface buses and coexistence review

This is an independent, read-only review made on 2026-10-20.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54`. I checked it before and after this review; it was
  unchanged.
- **Netlist:** `schematic.net.xml` `0cc1ed69…`, unchanged since pass 1.
- **Pin table:** `pin_table.tsv` `bd4687a8…`, unchanged.
- **Checker:** `tools/check_r8.py` `93715601…`, unchanged since fix pass 3 started (`fix3_baseline_sha256.txt`).

**Dimension:** RF. That covers:

- REQUIREMENTS F10 and the RF parts of M1 / M2;
- the rigid strip and its hashes;
- the interface buses from U1 to the strip;
- F10's 5 mm separation;
- GND vias at layer changes;
- the fence: its openings and the lanes crossing it;
- coexistence paths;
- the reset states of the radio and GNSS lines.

Vehicle-level choices are out of scope, and so is firmware beyond the pin / interface contract.

**Comparison boards:**

- **R7:** `git show 431025d:…/m3.kicad_pcb`, SHA-256 `c872a3d3…`.
- **Pass-3 board:** `990c8040…`, rebuilt from the coordinator's backup (`r8_backup_990c8040/tracked.diff` applied to R7)
  and SHA-checked.

Both were copied into the session scratchpad and deleted afterwards.

Coordinates are KiCad mm, with y = 0 at the aft (SMA) edge.

## 1. Summary

**No Critical and no Major findings. There are two Minor findings (R8P4-RF-01 and -02), both about the bench procedure
and the records. The RF copper is byte-identical to the board pass 3 reviewed.**

**Pass 3's three RF findings are all closed (§2):**

- **RF-01 (bootloader order).** All five records now give the same order: PE4 low, then SX1262 asleep with PE9 low,
  then the GPIOE reset last. The five are the regenerated binding note on `c84f00b8…`, D6.8, F10, M3_R8 and
  ORDERING §5.
- **RF-02 (L5 spur).** ORDERING §5 now names 1175.000 MHz and asks for C/N0 per signal (UBX-NAV-SIG). M3_R8 matches.
- **RF-03 (via label).** The via is now called R78.2's everywhere.

**Fix pass 3 did not touch the RF area (§3):**

- **Item diff, pass-3 board to final:** 14 items removed and 14 added. Every changed track is on B.Cu, and the one moved
  GND via does not touch RF copper.
  - The B.Cu items are CAM_PWR_EN, USB_LIMITED, RAW_ACT_SENSE / _MCU and R172.
  - The other via changes are the BAT_ENABLE via at y 104.5 and the step-7 cover via (28.875, 32.875) → (29.125, 32.625).
  - No RF-family item (RADIO_\*, GNSS_\*, 3V3_RADIO, 3V3_GNSS) was added, removed or moved.
  - The nearest added item to RF-family copper on the same layer is the moved cover via: 1.135 mm from RADIO_SCK_MCU on
    F.Cu.
- **GND fill:** byte-equal in area on all four layers in the strip, and byte-equal on F.Cu, In1 and In2 in the band and
  the bus.
  - So the In1 reference under every F.Cu interface lane is unchanged.
  - The only changes in reach are B.Cu GND round the rerouted B.Cu tracks, and In2 3V3's antipad following the moved
    cover via.

**The gate passes.** `tools/check.sh` exits 0 in this review, and `test_r8_check` passes (23 OK). `check_r8`'s report on
`c84f00b8…` equals pass 3's report on `990c8040…` key for key, apart from the board SHA. That report covers the rigid
digests, `rf_strip`, the fence, stitching, launches, module ground, strip reach, the loader pins and `rf_separation`.

**Re-measured on the final board, all equal to pass 3:**

- **Rigid strip:** all 12 digests equal `RIGID_BASELINE`, and equal on R7, on the pass-3 board and on R8.
- **Interface buses:** lengths, vias and In1 reference misses are identical line for line.
- **Fence:** 25 vias; 4 openings of 2.015 / 2.600 / 2.100 / 2.050 mm; 14 crossings, all on F.Cu. Identical line for
  line.
- **Neighbours of the interface nets** (within 0.6 mm): identical.
- **GND partners of the five RF-family layer changes:** 0.721–1.221 mm.
- **F10 separation:** nearest part R306–U1 5.94 mm; nearest fast line R306–USB_DM 5.075 mm.
- **Reset states:** confirmed against the primary datasheets (§4.7).
  - SX1262 Table 8-3: BUSY is pulled up and DIO2 pulled down in reset.
  - SX1262: NRESET's V_IL is 0.2·VBAT.
  - MAX-F10S: RESET_N must be held low ≥ 1 ms.

**New findings, both Minor:**

- **R8P4-RF-01 (worth fixing).** ORDERING §5's coexistence step only records C/N0 *changes* between conditions. Both
  on-board clocks run in every one of those conditions, so the step cannot see the in-band spurs it names.
  - The spurs named are the HSE's 25 MHz × 63 near L1 and × 47 near L5.
  - The step also cannot see one spur it does not name: the radio's 32 MHz crystal × 37 = 1184.000 MHz, 7.55 MHz from
    L5 / E5a / B2a, inside its main lobe.
  - R7's pass-2 RF review accepted the coexistence risk partly on a planned UBX-MON-SPAN check, which never reached
    ORDERING.
- **R8P4-RF-02 (not worth fixing).** ORDERING §5 says the camera supply "U7 / U8 / L3 moved to 13.5 mm from U31 and
  24.8 mm from U30". Those are U8's figures. U7 is 9.41 / 17.98 mm, as M3_R8's table already says.

## 2. Previous pass in this dimension: closure

| Pass 3 finding | Fix pass 3 disposition | On `c84f00b8…` |
|---|---|---|
| R8P3-RF-01 (Minor, worth fixing): bootloader-jump order allowed a GPIOE reset before the SX1262 sleep | Fixed (records): `binding_note.py`, D6.8, F10, M3_R8, ORDERING §5 | **Closed.** See the notes below the table. |
| R8P3-RF-02 (Minor, worth fixing): coexistence step named only the L1 spur | Fixed (records): ORDERING §5, M3_R8 RF | **Closed.** See the notes below the table. |
| R8P3-RF-03 (Minor, not worth fixing): R78.2's via called C76.2's | Fixed (records) | **Closed.** See the notes below the table. |

**R8P3-RF-01, what was checked:**

- **`binding_note.py` l. 50–60** now reads "(1) drive PE4 … low; (2) put the SX1262 to sleep (the radio is still out of
  reset, so BUSY can go low) and drive RADIO_NRST (PE9) low; (3) last, reset GPIOE through RCC_AHB4RSTR …". It adds
  "Never reset GPIOE before step 2".
- **`r8_binding_note.json`** was regenerated with `board_sha256` `c84f00b8…`, netlist `0cc1ed69…` and pin table
  `bd4687a8…`, and carries the same text.
- **The other records agree:**
  - D6.8 (R8_DECISIONS l. 289–306, with the fix-pass-3 note);
  - REQUIREMENTS F10 ("first drive PE4 … low, then put the SX1262 to sleep and drive PE9 low, and only then reset
    GPIOE");
  - M3_R8 l. 525–531;
  - ORDERING §5 l. 161 ("PE4 driven low; the SX1262 asleep and PE9 driven low; then GPIOE reset").
- **The datasheet basis is now verified, not inferred** (SX1261/2 DS Rev 1.2 Table 8-3): in Reset, BUSY is "PU" and
  DIO1–3 are "PD". So the step-2-before-step-3 order is the right one.

**R8P3-RF-02, what was checked:**

- ORDERING §5 l. 164 now gives both HSE spurs: 1575.000 MHz (0.42 MHz from L1) and 1175.000 MHz (1.45 MHz from
  L5 / E5a / B2a).
- It cites DS R03 §1.3 / Table 4 and says "log C/N0 per signal (UBX-NAV-SIG), L1 and L5 separately, in every condition".
- M3_R8 l. 422–427 matches.
- I re-read DS R03 §1.3: "Single-band operation is not supported. Both L1 and L5 signals must be enabled or disabled".
  The remaining blind spot is new and is R8P4-RF-01.

**R8P3-RF-03, what was checked:**

- `r8_power.py` l. 471 and l. 477 now say R78.2.
- D98 (l. 2059–2060) and D87's correction (l. 1941–1942) carry the corrected name with a fix-pass-3 note.
- So do `fix2_handoff.md` l. 37 and `fix2_progress.md` l. 10.
- Where C76.2 still appears (D41 l. 1043, l. 1228), it means C76.2's own 0.6 mm via at (34.4, 38.27), which is correct.

Pass 3's observations still hold unchanged (§6):

- In1 under RADIO_NRST at U1's east face;
- the F10 fast-line margin of 5.075 mm;
- the fence via at (7.685, 23.3);
- R301.2 at 0.180 mm;
- the RF bypass thermal spokes.

## 3. Fix pass 3 regression check (RF area)

`bdiff.py` compares canonical item sets (`check_r8.canon_track` / `canon_fp` / `canon_area` plus zone priority) between
the pass-3 board and the final board. For each added item it reports the edge distance to RF-family copper. A distance
in "plan" means a different layer, with In1 GND and In2 between.

| Change (D) | Item(s) on R8 | Nearest RF-family copper |
|---|---|---|
| ROUTING-01 (D106) | USB_LIMITED B.Cu trunk y 37.25 → 37.3, TP82 stub, corner (16.3 → 16.35, 37.3) | Same layer: none. In plan it crosses under GNSS_TP_MCU, RADIO_RXEN and RADIO_NSS (F.Cu), as at y 37.25 before. |
| ROUTING-01 (D106) | R172 (30.6 → 30.65, 48.1) B; RAW_ACT_SENSE / _MCU B.Cu x 30.6 → 30.65 | 2.74 mm in plan (RADIO_NRST) |
| ROUTING-03 (D107) | CAM_PWR_EN B.Cu (31.85, 36.8) → (28.25, 36.8) → (28.25, 30.025) → R74.1 (30.775, 27.5) | Same layer: none. In plan it crosses under RADIO_NSS, as the x 28.0 leg did. The new 45° leg is 1.425 mm in plan from RADIO_DIO1. |
| Stage-A ground table | Cover via GND (28.875, 32.875) → (29.125, 32.625), 0.5 / 0.3 mm | **1.135 mm same layer** (RADIO_SCK_MCU, F.Cu) |
| ROUTING-02 (D108) | BAT_ENABLE via (16.6, 104.5) 0.6 → 0.5 mm | Out of reach (> 80 mm) |

`fillxor.py`: GND and 3V3 fills compared region by region, pass-3 board to R8, in mm².

| Region | F.Cu GND | In1 GND | In2 GND | B.Cu GND | In2 3V3 |
|---|---|---|---|---|---|
| strip (y < 23.5) | 810.599 = | 988.259 = | 1003.021 = | 963.440 = | — |
| band (y 23.5–28.5) | 164.427 = | 221.552 = | 57.320 = | 196.154 → 197.378 (−0.380 / +1.605 at x 27.75–30.55, y 27.2–28.5: CAM_PWR_EN's new leg) | 148.484 = |
| bus (y 28.5–50) | 570.360 = | 920.567 = | 211.825 = | 640.269 → 640.485 (USB_LIMITED / CAM_PWR_EN reroutes) | 645.782 = (0.347 mm² antipad moved with the cover via) |

The strip, the GCPW ground profile and the In1 reference under the interface buses are therefore exactly pass 3's. The
B.Cu GND changes lie forward of y 27.1, ≥ 3.8 mm from the fence row, and outside the strip. CAM_PWR_EN, USB_LIMITED and
RAW_ACT_SENSE are static or DC nets, and none is on F10's fast-line list.

## 4. Measurements on the final board

### 4.1 Rigid strip and its hashes

- **`tools/check.sh`**, run in this review: exit 0.
  - DRC 0 at every severity; unconnected 0; parity 0; ERC 0.
  - Audit OK; silkscreen OK; R8 CAD contract OK.
  - `route_check` r8: 0 failing, 3 allowlisted, 0 leftovers, 0 removable (22 bump windows).
  - Actuators OK; fit OK.
  - `git status --porcelain` digest is identical before and after the run.
- **`tools/test_r8_check.py`:** 23 tests OK.
- **Rigid digests** (`rigid3.py`, `check_r8.rigid` run on all three boards). All 12 groups equal `RIGID_BASELINE` on R7
  `c872a3d3…`, on the pass-3 board `990c8040…` and on R8 `c84f00b8…`, with 0 issues each:

  | Group | Items | Digest (first 16) |
  |---|---|---|
  | `strip_parts` | 22 | `c71c1250c4f732ae` |
  | `strip_rf_copper` | 11 | `7a2598349ad81c5f` |
  | `strip_gnd` | 176 | `bfcbe417a3b45e12` |
  | `strip_rule_areas` | 5 | `d105af8bf59da746` |
  | `strip_gcpw` | 8 | `8b46f56919611ca6` |

  The other seven groups are also equal: outline `9558fcd7…`, m3_holes, j122_tie, j1, pyro_block_area, ch1_parts and
  ch1_copper.
- **Other `check_r8` evidence** (key for key equal to pass 3's report):
  - `rf_strip`: 69 F.Cu, 28 B.Cu and 205 vias, all on allowed nets.
  - Line stitching: GNSS west 3.90, east 2.65; radio 1.55 / 1.55 mm. In1 missing under RF copper: 0.0 mm².
  - Launches: In2 1025 / 1025 samples each.
  - Module ground: U31 In1 / In2 2601 / 2601; U30 In1 1976 / 1976.
  - RF clamp and pi GND pads: 0.16 mm from a GND via.
  - Strip GND reach: F.Cu 3.04, B.Cu 3.49 mm.
- **CPL:** the pass-3 CPL (rebuilt from the backup) and the final CPL differ in R172's row only. Every RF part's
  position and rotation is unchanged.
- **Fab manifest:** binds `c84f00b8…`.

### 4.2 Interface buses U1 → strip

`iface.py` covers every track and via of the RADIO_ / GNSS_ / 3V3_RADIO / 3V3_GNSS nets, RF lines excepted. Each segment
is sampled every 0.05 mm, at its centre and at ±0.2 mm, against In1 GND (F.Cu segments) or In2 GND (B.Cu segments); the
launch cut-outs are excluded. **The output is identical, line for line, on the pass-3 board and on R8.**

| Net | Copper | Vias |
|---|---|---|
| RADIO_SCK_MCU / RADIO_SCK | 15.73 + 13.19 mm F.Cu | 0 |
| RADIO_MOSI_MCU / RADIO_MOSI | 9.76 + 17.15 mm F.Cu | 0 |
| RADIO_MISO / RADIO_MISO_MCU | 1.48 + 27.90 mm F.Cu | 0 |
| RADIO_NSS / BUSY / RXEN / DIO1 / NRST | 32.21 / 32.01 / 40.02 / 25.04 / 41.04 mm F.Cu | 0 |
| GNSS_TXD / GNSS_TXD_MCU | 2.19 + 26.87 mm F.Cu | 0 |
| GNSS_RXD_MCU / GNSS_RXD | 9.16 + 19.36 mm F.Cu | 0 |
| GNSS_TP_MCU / GNSS_TIMEPULSE | 25.97 + 2.45 mm F.Cu | 0 |
| GNSS_RESET_N / GNSS_SAFEBOOT_N | 23.89 / 4.26 mm F.Cu | 0 |
| RADIO_TXEN (R7's loop) | 2.45 F.Cu + 22.72 B.Cu | 2 |
| GNSS_LNA_EN / GNSS_VCC_RF (limiter) | 1.9 F + 5.75 B / 1.9 F + 4.30 B | 1 / 1 |
| GNSS_ANT_DC / SRC / GATE / PD | 1.96 F + 9.02 B / 8.57 B / 6.92 B / 3.44 B | 1 / 0 / 0 / 0 |
| 3V3_GNSS / 3V3_RADIO feeds | 7.13 / 7.23 mm F.Cu | 0 |

- **Reference.** There are reference misses only inside the five layer-change via antipads. Each of those vias has a GND
  partner (§4.4).
  - One other gap remains: 28 samples at x 33.6, y 42.8–44.35, on the +0.2 mm side of RADIO_NRST. That is 0.1 mm
    outside the 0.2 mm lane, where CAM_MCU_RX's hop via and a 3V3 via bring their antipads. It is unchanged since
    pass 2, and the lane centre is covered.
- **Foreign neighbours** (`aggr.py`, other-net copper within 0.6 mm on the same layer, 22 rows): identical on the
  pass-3 board and R8. The nearest is FB30.2 at 0.172 mm from its own 3V3 feed via (C12b #6); the rest are U1's and the
  modules' pin pitch and the known items that pass 3 listed.
- **Lane-to-lane parallel runs** (new in this pass, `xtalk.py`: F.Cu runs at ≤ 0.36 mm edge gap, ≥ 1 mm long).
  - RADIO_BUSY runs 28.7 mm beside RXEN and 27.6 mm beside MISO_MCU.
  - DIO1 runs 10.6 mm beside NRST.
  - MISO_MCU runs 9.4 mm beside MOSI_MCU, and NSS 7.6 mm beside MOSI_MCU.
  - The GNSS UART and timing lanes run 7.0–7.5 mm beside each other.
  - **RADIO_SCK / SCK_MCU has no parallel neighbour longer than 2.0 mm.**
  - Every victim among the long runs is driven push-pull, or held, while its aggressor toggles: BUSY and DIO1 by the
    SX1262, RXEN and NRST by the MCU. GNSS_RESET_N, which only the module's 10 kΩ pull-up holds (DS R03 Table 12,
    Rpu 7–13 kΩ), needs ≥ 1 ms low to reset. Its 7.5 mm neighbour is GNSS_TP_MCU, a 1 Hz edge behind R307's 1 kΩ. No
    coupled glitch can act on it (Inference).

### 4.3 F10 5 mm separation

`check_r8.rf_separation` runs in the gate, and its `r8.json` result is equal to pass 3's. No restricted part and no
fast-line copper moved in fix pass 3. The changed nets (CAM_PWR_EN, USB_LIMITED, RAW_ACT_SENSE, BAT_ENABLE) are not in
F10's fast-line set.

**Nearest restricted part, per RF part:**

- R306 5.94 mm (U1);
- R310 / R313 / R315 6.04 mm (U1);
- FB31 6.66 mm (U7);
- C310 7.86 mm (C73).

**Nearest fast-line copper, per RF part:**

- R306 5.075 mm (USB_DM);
- R315 5.819 mm (USB_DM);
- FB30 6.989 mm (USB_DM at D4.6);
- C300 9.349 mm (USB_DM at D4.1).

**Module courtyards to aggressors** (`dist.py`), equal to M3_R8's table:

| Module | U7 | U8 | L3 | U1 | U3 | Y1 | U2 | L1 |
|---|---|---|---|---|---|---|---|---|
| U31 | 9.41 | 13.49 | 17.53 | 16.56 | 20.46 | 26.46 | 45.06 | 44.72 |
| U30 | 17.98 | 24.81 | 26.07 | 15.06 | 19.01 | 25.37 | 47.77 | 49.11 |

### 4.4 GND vias at layer changes (RF-family nets and the strip feeds)

| Via | Size | Nearest GND via | Next |
|---|---|---|---|
| GNSS_ANT_DC (11.45, 5.15), rigid | 0.6 | 1.011 (11.6, 4.15) | 1.571 |
| RADIO_TXEN (31.13, 20.15) | 0.5 | 0.721 (31.73, 20.55) | 1.912 |
| RADIO_TXEN (28.59, 7.80) | 0.5 | 0.721 (28.19, 7.2) | 1.184 |
| GNSS_LNA_EN (11.51, 8.30) | 0.5 | 1.100 (12.61, 8.3) | 1.670 |
| GNSS_VCC_RF (10.41, 8.30) | 0.5 | 1.221 (10.37, 7.08) | 1.385 |
| 3V3 feed to FB30 (12.33, 24.4) | 0.6 | 1.100 (fence via 12.3, 23.3) | 2.170 |
| 3V3 feed to FB31 (35.1, 24.4) | 0.6 | 1.304 (fence vias 34.4 / 35.8) | 1.304 |

No other RADIO_ / GNSS_ net has a via. All five RF-family layer changes and both feeds are within AGENTS §3's 1.5 mm.

### 4.5 Fence and crossings

`fence.py`'s output is identical, line for line, on the pass-3 board and on R8.

- **Vias:** 25 GND vias, 0.5 / 0.3 mm, on y 23.3. Every one touches GND fill on all of F.Cu, In1, In2 and B.Cu.
  - F.Cu contact is partial at the vias between lanes: 6/8 probe points at x 7.685, 9.7 and 22.1, and 7/8 at 12.3.
- **Gaps:** 0.9 mm at the edge; 1.2–2.0 mm along the row, except the openings.

| Opening | Width | Lanes |
|---|---|---|
| 7.685–9.70 | 2.015 | GNSS_RXD, GNSS_TP_MCU |
| 9.70–12.30 | 2.600 | 3V3_GNSS (0.3 mm) |
| 20.00–22.10 | 2.100 | RXEN, BUSY, MISO_MCU |
| 22.10–24.15 | 2.050 | MOSI, NSS |

- **Crossings:** 14, all on F.Cu.
  - Lane-to-ring gaps are 0.15 mm for MISO_MCU and MOSI at (22.1, 23.3) (C12 #5 / #6 after fix pass 3's renumbering),
    0.175 mm for GNSS_RXD (C12 #18) and 0.225 mm for TXD_MCU.
- **Other layers near the fence:** no In1, In2 or B.Cu track, and no non-GND via, in y 22.6–24.0. The In2 3V3 pour starts
  at y 24.0 (x 0.5–35.3).
- **Openings against the limits:** the widest, 2.60 mm, is within D16's 2.7 mm and under F10's λ/20 (about 4.4 mm at L1).

### 4.6 Coexistence paths

- **Unchanged (rigid):**
  - the RF lines are 15.45 mm apart, the jacks 18.69 mm and the module courtyards 7.66 mm;
  - each module has its own ferrite (FB30 / FB31, BLM18KG221SN1D) with local bulk;
  - the supply vias are 22.8 mm apart, each 1.10–1.30 mm from fence GND vias.
- **Radio lines near U30:** no radio lane changes layer. None comes within 5.44 mm of U30's body (RXEN), or within
  6.0 mm of the GNSS RF copper.
- **Clock harmonics in the GNSS bands** (arithmetic):
  - The MAX-F10S always receives L1 / E1 / B1C at 1575.42 MHz and L5 / E5a / B2a at 1176.45 MHz (DS R03 §1.3, Table 4).
  - **HSE 25 MHz** (Y1, 25.37 mm from U30):
    - × 63 = 1575.000 MHz, −0.42 MHz from L1;
    - × 47 = 1175.000 MHz, −1.45 MHz from L5.
    - Both are recorded since fix pass 3.
  - **Radio crystal: passive 32 MHz** inside U31's shield (EBYTE E22-900MM22S manual §4.2, "The module uses a 32 MHz
    passive crystal oscillator"; also M3_R7 l. 153). Its oscillator runs in STBY_XOSC, FS, RX and TX (SX1261/2 DS §9).
    - × 37 = 1184.000 MHz, **+7.55 MHz from L5 / E5a / B2a, inside the 10.23 Mcps main lobe (±10.23 MHz)**;
    - × 49 = 1568.000 MHz, −7.42 MHz from L1, just outside E1 / B1C's BOC(6,1) side lobes (Inference).
    - No R8 record names either harmonic. See R8P4-RF-01.
- **What the bench step can see.** ORDERING §5's coexistence step logs C/N0 in four conditions:
  - radio idle, with the MCU at its flight clock and the camera on;
  - radio keyed, camera on;
  - and both again with the camera off.

  The step records each C/N0 change against those runs. The HSE runs in all of them, and the radio's crystal runs in all
  of them unless "idle" means sleep or reset. So a steady spur from either clock is in every baseline, and the procedure
  cannot attribute it. The receiver's own spectrum monitor exists for exactly this: UBX-MON-SPAN, "sufficient to
  identify noise or jammers in the reception band … helpful in assessing the impact of running other onboard
  components" (MAX-F10S Integration manual R01 §4.2.3). R7's pass-2 RF review accepted the coexistence risk partly
  because "u-center UBX-MON-SPAN while the radio and SPI are active" was "already planned" (`r7_review/pass2_rf.md`
  §3.10, l. 276). No R7 or R8 ORDERING ever carried that step (`grep` finds MON-SPAN only in that review).

### 4.7 Reset and bootloader states of the radio and GNSS lines

The netlist nodes are unchanged (`0cc1ed69…`), so pass 3's table holds:

- R311 2 kΩ RADIO_NRST → GND;
- R312 100 kΩ RADIO_RXEN → GND;
- R310 100 kΩ RADIO_NSS → 3V3;
- RADIO_TXEN = U31.9 + DIO2;
- GNSS_RESET_N PD14 with no capacitor;
- TIMEPULSE → R307 1 kΩ → PD15;
- SAFEBOOT_N on TP30 only.

The `pin_table.tsv` rows match (PE9 push-pull GPIO; PD9 GPIO out; PB11 software NSS; PD14 open drain; PD15 TIM4_CH4
input; PC6 / PC7 USART6; loader roles per AN2606 Table 135).

**Checked against the primary datasheets in this pass:**

- **SX1262 in reset** (SX1261/2 DS Rev 1.2 Table 8-3):
  - DIO1–DIO3 are pulled down (50 kΩ), so RADIO_TXEN = DIO2 is low and RADIO_RXEN is low through R312. Both RF-switch
    controls are off.
  - BUSY is pulled up. MISO / MOSI / SCK are high-Z.
  - NRESET's V_IL maximum is 0.2·VBAT = 0.66 V at 3.3 V (Table 3-10, "VIL_N"). R311 against the 50 kΩ internal pull-up
    gives about 0.13 V. ORDERING §5 tests for "below 0.66 V", which matches.
- **SX1262 in sleep:** "the BUSY pin is held high through a 20 kΩ resistor" (§8.3.1). Pins are "HIZ PU" / "IN PU".
- **E22-900MM22S:** the manual lists NRST as "input … active low" and TXEN / RXEN as high-active inputs. It shows no
  added pull-up on NRST, so this review cannot say whether the module adds one; the bench reading at R311.1 settles it.
- **MAX-F10S** (DS R03 Table 10 and Table 11):
  - RESET_N must be low ≥ 1 ms, and has an internal 7–13 kΩ pull-up.
  - In reset, all PIOs are input pull-up.
  - SAFEBOOT_N is tied internally to TIMEPULSE through 1 kΩ. PD15 is analog and high-Z in MCU reset, so the module never
    starts in safe boot.
- **Bootloader:**
  - With D6.8's order, the radio is held in reset by R311 and the gate off by R127.
  - PB10 / PB14, the loader's TX pins, drive only the SCK / MOSI inputs of an SX1262 in reset.
  - NSS stays high through R310, so USART3 is never selected.

## 5. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P4-RF-01 | Minor (worth fixing) | F10 coexistence ("shown on the bench with the radio keyed continuously while GPS C/N0 is logged"); ORDERING §5 coexistence step; the R7 coexistence acceptance (`pass2_rf.md` §3.10) | **The coexistence step cannot see a steady in-band spur. It omits the radio crystal's L5 harmonic and the UBX-MON-SPAN check that R7's acceptance relied on.** See the notes below this table. | ORDERING l. 164; MAX-F10S IM UBXDOC-963802114-12892 R01 §4.2.3 (p. 63); MAX-F10S DS R03 §1.3, Table 4; EBYTE E22-900MM22S manual §4.2; SX1261/2 DS Rev 1.2 §9 (crystal on in STBY_XOSC / FS / RX / TX); `r7_review/pass2_rf.md` l. 276; `grep -rl MON-SPAN docs m3_design/assembly_review/sources` → only that file; M3_R7 l. 153 (32 MHz) | Text only; no board or gate change. See the notes below this table. |
| R8P4-RF-02 | Minor (not worth fixing) | Records match the board (AGENTS) | **ORDERING §5 gives U8's distances for the whole camera supply.** It says "the camera supply U7 / U8 / L3 moved to 13.5 mm from U31 and 24.8 mm from U30". Measured courtyard gaps: U7 (camera eFuse, in F10's restricted set) 9.41 / 17.98 mm; U8 13.49 / 24.81 mm; L3 17.53 / 26.07 mm. M3_R8's RF table gives all three correctly. Since U7 is not a switcher, the bench consequence is nil. | ORDERING l. 164; M3_R8 RF table ("U31: U7 9.41 mm (U8 13.49, L3 17.53 …)"); `dist.py` on `c84f00b8…` | At the next edit of that sentence, write: "the camera buck U8 / L3 13.5 / 17.5 mm from U31 and 24.8 / 26.1 mm from U30 (U7, the eFuse, 9.4 / 18.0 mm)". |

**R8P4-RF-01, the finding in detail:**

- **The step records only changes.** ORDERING §5 logs C/N0 per signal with the radio idle and then keyed, camera on and
  off. It "record[s] each C/N0 change against the same run with the camera off".
- **Both clocks run in every condition.** The HSE always does, and the radio's 32 MHz crystal does in STBY_XOSC, FS,
  RX and TX. A steady spur from either clock is therefore in every baseline, and no change reveals it.
  - That covers the HSE spurs the step names, 1575.000 and 1175.000 MHz.
  - It also covers one the step does not name: the radio crystal × 37 = **1184.000 MHz, 7.55 MHz from 1176.45 MHz,
    inside L5 / E5a / B2a's ±10.23 MHz main lobe**, which the MAX-F10S always tracks.
- **So the step's own words do not hold.** It calls the HSE spur "an Inference only this test settles", but as written
  the test cannot settle it.
- **R7 relied on a step that was never written.** R7's pass-2 RF review judged coexistence acceptable partly because
  "u-center UBX-MON-SPAN while the radio and SPI are active" was "already planned". No ORDERING, R7 or R8, carries it.
- **The tool exists.** u-blox documents MON-SPAN for exactly this use.
- **Severity.** The level of every spur is unknown, and the module shield and FB31 reduce the crystal's (Inference).
  This is a gap in the procedure, not a known defect.

**R8P4-RF-01, the fix (ORDERING §5 coexistence step):**

1. **Spectrum in every condition.** Capture UBX-MON-SPAN for both RF blocks (L1 and L5) in every condition, with max
   hold. Note any peak at 1575.000, 1175.000, 1184.000 or 1568.000 MHz, or any other peak, against the noise floor
   (MAX-F10S IM §4.2.3).
2. **Separate the radio's crystal from its PA.** Add one condition with the radio in sleep or held in reset (crystal off)
   against one in RX (crystal on, not keyed).
3. **Compare against a reference.** Compare C/N0 per signal with a reference receiver fed from the same antenna through
   a splitter, or a known-good receiver in the same place. Optionally enable CFG-ITFM and record UBX-SEC-SIG's
   jammingState.

**Also:** name the 32 MHz × 37 harmonic beside the HSE harmonics in M3_R8 §RF.

## 6. Observations (no finding)

- **In1 under RADIO_NRST at U1's east face** (unchanged since pass 2): CAM_MCU_RX's antipad comes 0.05 mm inside the
  lane edge for about 0.3 mm. The lane centre is covered. NRST is static and driven.
- **F10 fast-line margin:** R306–USB_DM is 5.075 mm against a 5.0 mm limit. The gate holds it on every build.
- **Fence via (7.685, 23.3):**
  - It is 0.155 mm from R305.2's bare pad (C12b #2) and 0.175 mm from GNSS_RXD (C12 #18).
  - FB30.2 is 0.172 mm from its own feed via (C12b #6).
  - C300.1 and FB30.2 are 0.196 / 0.197 mm from the fence via (12.3, 23.3) (C12b #28 / #29).
  - All of these are recorded. A short at any of them holds a UART line low or bypasses the ferrite; none is an RF
    hazard.
- **R7's rigid limiter copper:** R301.2 (GNSS_ANT_GATE) is 0.180 mm from the GND via (6.0, 15.0) (C12b #19). That is
  R7's accepted geometry, held by `strip_gnd` / `strip_parts`, and recorded.
- **Thermal spokes:** C300.2, C301.2, C310.2–C312.2, R311.2 and R312.2 have thermal spokes (the house rule). The module
  GND pads and the RF clamp pads are solid (C16). Unchanged.
- **LNA_EN during a GNSS reset.** With RESET_N held low, the MAX-F10S makes all PIOs inputs with pull-ups (DS R03
  Table 11), including LNA_EN (PIO 7). So the limiter's enable sees a weak pull-up rather than a driven level while the
  MCU holds the GNSS in reset. This is R7's rigid circuit and only affects the antenna bias while the receiver is not
  running anyway (Inference); it is noted here for the bench team.

## 7. Inferences (not measured, or not from a primary source)

- **Spur levels** in R8P4-RF-01. Where the harmonics fall is arithmetic. Their level at U30 is unknown. The radio's
  crystal is inside U31's shield and behind FB31, which should lower its harmonics, but this review cannot quantify by
  how much.
- **Whether the 1568 MHz harmonic matters for E1 / B1C** depends on the receiver's L1 processing bandwidth, which
  u-blox does not publish.
- **E22's NRST.** The manual does not say whether the module adds a pull-up. The 0.13 V estimate assumes only the
  SX1262's 50 kΩ (Table 8-3). ORDERING §5's "below 0.66 V" reading at R311.1 settles it.
- **Coupling remarks** in §4.2 (parallel runs, RESET_N) are estimates.

## 8. Sources

- **u-blox MAX-F10S data sheet** UBXDOC-963802114-12732 R03 (09-Apr-2025):
  - §1.3 ("Single-band operation is not supported");
  - Table 4 (L1 1575.42, L5 / E5a / B2a 1176.450 MHz);
  - Table 10 (pin 9 RESET_N ≥ 1 ms; note 14: SAFEBOOT_N internally tied to TIMEPULSE through 1 kΩ);
  - Table 11 (pin states; reset mode all PIOs input pull-up);
  - Table 12 (Rpu RESET_N 7–13 kΩ).
  - https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
- **u-blox MAX-F10S integration manual** UBXDOC-963802114-12892 R01 (14-Aug-2024): §4.2.1–4.2.3 (in-band interference;
  UBX-MON-SPAN spectrum analyser, p. 63) and §3.5.1 (CFG-ITFM, UBX-SEC-SIG jammingState).
  - https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- **Semtech SX1261/2 data sheet** Rev 1.2 (June 2019):
  - Table 8-3 (digital pads per chip mode: Reset → DIO1–3 PD, BUSY PU, SPI HIZ);
  - §8.3.1 (BUSY; sleep: held high through 20 kΩ);
  - §9.1 (start-up);
  - Table 3-10 (VIL_N, NRESET, 0.2·VBAT).
  - Copy used: https://cdn.sparkfun.com/assets/6/b/5/1/4/SX1262_datasheet.pdf
- **EBYTE E22-900MM22S user manual** (LCSC C5333985, revision 1.0 2022-10-21 as served): ch. 3 pin table (NRST, TXEN,
  RXEN); §4.2 ("The module uses a 32 MHz passive crystal oscillator"; DIO2 to TXEN).
  - https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
- **Project records:**
  - `docs/REQUIREMENTS.md` F10;
  - `AGENTS.md` §3;
  - `docs/M3_R8.md` §RF and §Firmware;
  - `docs/ORDERING.md` §5 l. 159–165;
  - `docs/R8_VALIDATION.md` ("Review pass 3", C12, C12b, C16, "R7 pass-4 RF items on R8");
  - R8_DECISIONS D6.8, D16, D41, D87, D98, D106–D108;
  - `step9/binding_note.py` and `step9/r8_binding_note.json`;
  - `pin_table.tsv`;
  - `m3_design/r8_power.py`;
  - `fix3_handoff.md`, `fix3_progress.md`, `fix3_generators.diff`;
  - `sources/r7_review/pass2_rf.md` §3.10–3.11;
  - `docs/M3_R7.md` l. 153.

## 9. Method (reproduction)

All scripts ran under KiCad 10.0.6's Python (`-I`, `PYTHONDONTWRITEBYTECODE=1`), read only, from the session scratchpad
(`p4rf/py/`; pass 3's scripts, retargeted, plus three new ones).

**Boards used:**

- R7 from `git show 431025d`;
- the pass-3 board rebuilt from `r8_backup_990c8040/tracked.diff`, SHA verified `990c8040…`;
- a copy of the final board.

The board copies and the downloaded datasheets were deleted afterwards. Nothing in the repository was written except
this report. `git status --porcelain` is identical before and after, and the board SHA is unchanged.

**Gate and tests:**

- `KICAD_CLI=… KICAD_PY=… tools/check.sh`: exit 0.
- `python -m unittest test_r8_check`: 23 OK.
- The `r8.json` from the gate run was compared key by key with pass 3's.

**Scripts:**

- **`rigid3.py`:** `check_r8.rigid` on R7, the pass-3 board and R8, each group compared with `RIGID_BASELINE`.
- **`bdiff.py`:** canonical item diff, pass-3 board → R8, with each added item's edge gap to RF-family copper, by layer.
- **`fillxor.py`:** GND and 3V3 fills per layer and region (strip, band, bus, rest), as lost and gained areas.
- **`iface.py`:** lengths and vias per net, plus In1 / In2 point tests along every lane. Run on both boards and diffed.
- **`fence.py`:** fence vias, contact per layer, openings, crossings and inner / B.Cu items near y 23.3. Run on both
  boards and diffed.
- **`aggr.py`:** foreign copper within 0.6 mm of the interface nets. Run on both boards and diffed.
- **`xtalk.py`** (new): F.Cu parallel runs of each interface lane beside any other net at ≤ 0.36 mm edge gap.
- **`dist.py`** (new): courtyard and pad gaps between the modules and the aggressors.
- **`feedvias.py`** (new): GND partners of the two 3V3 strip-feed vias.
- **CPL diff:** the pass-3 CPL (rebuilt from the backup) against the final CPL.
- **Records:** text searches of the records for GPIOE, 1175, NAV-SIG, MON-SPAN, 32 MHz and C76.2 / R78.2.
- **Datasheets:** `pdftotext` of the four datasheets above.
