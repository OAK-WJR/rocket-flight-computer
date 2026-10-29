# R7 review pass 3: routing quality of critical and new nets

Reviewer scope: electrical routing quality, measured against the owner's clean-routing criterion (REQUIREMENTS M2,
AGENTS.md §3). The nets covered are:

- the radio SPI2 group and its control lines;
- the GNSS lines;
- the 3V3 feeds to FB30 and FB31;
- the RF lines;
- QSPI_IO0 and QSPI_IO1;
- the 12 R6 nets that F2 redrew;
- the power and pyro nets that F3 canonicalised.

For each I measured detour ratio, vias and layer hops, bus tidiness, reference-plane continuity, split crossings and
return vias.

Board reviewed: `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c`. That is the F3 final board and the hash bound in
`docs/R7_VALIDATION.md`. The hash was the same before and after this review.

References:

- pass-2 board `03fe7572…6d54`;
- R6 board `3b215ba`, translated +18 mm in y.

The review was read-only. The board was copied to a scratch directory before measuring and was never saved. The only
repository file written is this report.

## 1. Method

1. **Gate.** I ran `tools/check.sh` on the repository board. It exited 0:
   - DRC 0, unconnected 0, parity 0, ERC 0;
   - audit OK, silkscreen OK, `check_r7` OK;
   - `routing hygiene: 0 failing, 20 allowlisted, 0 stale`;
   - actuator contract OK, fit OK.

   I also ran `tools/route_check.py --report` on the final board, the pass-2 board and R6. I compared their info
   categories by location, with R6 shifted +18 mm.
2. **Geometry dump.** I dumped the geometry of all three boards with KiCad 10.0.6 `pcbnew` and reused the pass-2 RQ
   scripts on the dumps: shortest pad-to-pad copper path, octilinear detour ratio, and vias on the path.
3. **Reference planes.** I wrote a new scan, `refscan.py`. It samples every track of the critical and focus nets every
   0.05 mm and looks up the filled pour, holes included, on the reference layer (F.Cu→In1, B.Cu→In2, In1→F.Cu,
   In2→B.Cu). It reports two kinds of event:
   - every void run not explained by an antipad (a foreign hole within 0.6 mm and a run ≤ 1.3 mm);
   - every change of plane net along a track, which is a split crossing.
4. **Return-via sites.** I wrote a second new scan, `viaprobe.py`, to look for GND-via sites within 1.5 mm of each of
   the 14 allowlisted `critical_via_no_gnd` vias:
   - 0.5/0.3 mm via on a 0.025 mm grid;
   - the board's own rules exactly: 0.15 mm copper, 0.25 mm hole-to-copper, 0.25 mm hole-to-hole, 0.5 mm edge, RF
     0.25 mm, SMA 0.30 mm, Tag-Connect 0.508 mm, bare TP 1.0 mm, Pyro D 0.5 mm;
   - the `check_r7` via-in-pad rule, paste apertures and via keep-outs.

   I then cross-checked every site it found against `r7_route.ViaCheck`.
5. **Candidate routes.** A small clearance probe, `fitprobe.py`, tested candidate replacement routes against
   other-net copper with `SHAPE::Collide`. Its results are geometry only, not a DRC run.
6. **Renders.** I made cropped SVG renders, rasterised them and looked at each one:
   - the U1 left side, the band, the band east and strip top;
   - the radio strip and the GNSS strip;
   - CAM_MCU_TX, the pyro block, VCAP2 and the U12 3V3 feed.

   They are listed in §9.

## 2. Pass-2 findings in this dimension: closure

Each disposition was checked on the final board. "R7_VAL" means the row in `docs/R7_VALIDATION.md`.

| Pass 2 | Sev. (skeptic majority) | R7_VAL disposition | Verified on the final board | Pass-3 verdict |
|---|---|---|---|---|
| RQ-01 / RG-05 | Major / Major | Partly fixed; open for pass 3 or owner acceptance | 60 of 75 critical-signal vias have a GND via ≤ 1.5 mm. The 10 interface vias left are at 1.553–3.569 mm; QSPI_IO1 and RADIO_MISO_MCU's U1 via sit at exactly 1.500 mm. My exact-rule probe found **no legal site within 1.5 mm** for any of the 10. The allowlist claim holds | **Closed as Minor** (P3-ROUTING_QUALITY-01). The underlying return-path issue is P3-…-02 |
| RQ-02 | Major → Minor | Partly fixed | NRST/DIO1 still 85.44/69.09 mm, 1.92×/1.77×, 4 vias each. In2 GND now under most of their B.Cu. NRST's B.Cu y 24.5 still lies over In2 CAM_MCU_TX (28.55–38.75, y 24.55) | Disposition accurate; residual Minor (P3-…-03) |
| RQ-03 | Major | Fixed | FB31.1→via (35.73, 27.34) is one 0.4 mm F.Cu run, 5.45 mm with one 45° dogleg past R161.1, and R161.1 is tapped by a 0.7 mm stub. The via lands in the main In2 3V3 polygon (434.8 mm², 11 vias). No pad pass-through, no neck, no In2 U-turn | **Closed** |
| RQ-04 | Major | Fixed | `route_check`: acute_angle 0 and fold_back 0 board-wide. PULLPIN and BAT_SW_RETURN hairpins gone | **Closed** |
| RQ-05 | Major | Fixed | BAT_ILIM is 9.3 mm, 1 via, 0.2 mm only. PULLPIN is 39.4 mm, 2 vias, no loop. GNSS_RESET_N is 0.15 mm only. micro_segment, side_by_side_overlap and track_loop are 0 | **Closed** |
| RQ-06 | Major | Fixed except CAM_MCU_TX | LED_RED 32.59 mm (1.46×), LED_YEL 36.26 (1.44×), VLOGIC_SENSE U1.17→R60.2 18.81 (1.19×), PULLPIN_EXT 1.19×, BUZZ_DRV 1.24×. No redrawn net appears in `u_turn` or `staircase`. CAM_MCU_TX is 65.59 mm, 2.66×, 5 vias | Closed except CAM_MCU_TX, a Minor residual (P3-…-03) |
| RQ-07 / RQ-08 | Major | Fixed | `route_check`: off_angle, acute, fold_back, dead_copper, micro_segment, duplicate, collinear and side-by-side overlap, crossing_without_node, overlap_only_joint and track_loop are all 0 | **Closed** |
| RQ-09 | Minor | Not done | The NSS hop (23.2, 17.3)→(23.6, 15.27) is still there. GND vias sit 0.721 mm from both hop vias | Accurate; stays Minor |
| RQ-10 | Minor | Fixed | Every RADIO_/GNSS_ interface net is 0.15 mm end to end | **Closed** |
| RQ-11 | Minor | Partly fixed | Band fan-in staircases allowlisted (forced). The VBUS_SENSE jog is gone. The IO0 B.Cu corner is chamfered, but **the 0.212 mm jog into IO0's via (15.4, 51.0)→(15.55, 50.85) remains**. Also unchanged and not mentioned: U1-side via columns at x 9.3/9.4/10.0/10.7, and the GNSS fan diagonals at uneven offset (TP_MCU 1.5 mm from x 12.4; the others 2.0 mm from x 11.2–11.5) | Stays Minor; record incomplete (P3-…-06) |
| RQ-12 | Minor | Fixed | RXEN runs along y 8.0, aft of U31's body (y ≥ 9.0), and enters pad 10 at its outer end. Edge-to-pad gap to U3.5 is 1.14 mm | **Closed** |
| RQ-13 | Minor | Partly fixed | The GNSS strip-side B.Cu runs are over In2 GND: GNSS_RXD void 7.0 → 1.1 mm, GNSS_RESET_N 12.5 → 2.4 mm, all at antipads. The RESET_N detour (1.69×) stays | Accurate; Minor |
| RQ-14 | Minor | Fixed (reference) | The corridor B.Cu at x < 7 is over In2 GND. **The stubs from x ≈ 7.0 to the vias are over the In2 BAT_IN arm, so each radio line crosses a GND/BAT_IN split twice.** This is not recorded | Reference closed; new split crossings, P3-…-02 |
| RQ-15 | Minor | Fixed | Limiter re-placed. GNSS_ANT_SRC is 8.6 mm, the links are direct and there is no loop | **Closed** |

## 3. Per-line metrics, final board

Routed means the shortest pad-to-pad copper path through any series resistor. Ratio is routed length over octilinear
distance.

| Line | Routed (mm) | Ratio | Layer changes | Change since pass 2 |
|---|---:|---:|---:|---|
| RADIO_NSS U1.51→U31.14 | 57.40 | 1.57 | 4 (incl. strip hop) | none |
| RADIO_SCK (R313) | 57.52 | 1.60 | 2 | none |
| RADIO_MOSI (R315) | 61.62 | 1.56 | 2 | none |
| RADIO_MISO (R314) | 64.24 | 1.60 | 2 | none |
| RADIO_BUSY | 66.66 | 1.57 | 2 | none |
| RADIO_NRST | 85.44 | 1.92 | 4 | none |
| RADIO_DIO1 | 69.09 | 1.77 | 4 | none |
| RADIO_RXEN | 51.31 | 1.26 | 4 | rerouted aft of U31 (was 48.52, 1.19) |
| RADIO_TXEN U31.9→U31.19 | 25.17 | 2.30 | 2 | none (pinout-forced loop round the module) |
| GNSS_TXD / RXD / TP | 50.61 / 50.39 / 50.21 | 1.36 / 1.39 / 1.44 | 2 each | none |
| GNSS_RESET_N | 59.34 | 1.69 | 2 | none |
| QSPI_IO0 | 25.67 | 1.18 | 2 | corner chamfered |
| QSPI_IO1 | 26.31 | 1.16 | 2 | none (R6) |
| 3V3 FB31.1→plane via | 5.45 | 1.20 | 1 | was 16.9 mm / 34 mΩ |
| 3V3_RADIO FB31.2→U31.1 | 7.23 | 1.63 | 0 | through C310→C312→C311, the smallest cap last (intended) |
| 3V3_GNSS FB30.2→U30.8 | 5.85 | 1.16 | 0 | bar at y 20.75 beyond the pads |
| GNSS_RF_ANT / RADIO_RF_ANT | 4.83 / 5.30 | 1.00 | 0 | none: straight, 0.30 mm, no via |

`route_check` on the final board versus the pass-2 board and R6:

- **New info instances on critical nets:** essentially none. Every u_turn, short_layer_hop and chain_detour on the
  interface nets was already on the pass-2 board.
- **Power-net instances tagged "new":** VLOGIC u-turn, the 3V3/3V3A/CAM_5V short hops, and the USB_LIMITED/3V3A/
  CAM_IO_3V3 extra bends. I traced each one. Every one follows R6's topology with micro-pieces and duplicates merged
  away. None is a new detour or a new via.

## 4. Reference planes and split crossings (refscan, final against pass 2 and R6)

**Interface nets.**

- GNSS_* lines: In2 GND under every B.Cu run. The only voids are antipads.
- RADIO_DIO1: 13.7 mm of void at pass 2, now GND except antipads.
- RADIO_NRST:
  - In2 GND under 65.5 mm;
  - **11.05 mm of void at (28.15–39.15, 24.5)**: the GND strip is cleared around CAM_MCU_TX's In2 track, which lies
    directly under NRST.
- **Split crossings (new).** Every one of the 7 radio lines crosses from the In2 GND corridor strip to the In2 BAT_IN
  arm at x ≈ 6.93–7.19 at both corridor ends. That is 14 GND↔BAT_IN crossings. RADIO_MISO_MCU also has a 3V3↔BAT_IN
  change at (10.2–10.7, 49.0). Length over BAT_IN per line, both ends together:

  | Line | Over BAT_IN (mm) |
  |---|---:|
  | NSS | 3.10 |
  | SCK + SCK_MCU | 1.85 + 1.75 |
  | MOSI + MOSI_MCU | 1.66 + 1.66 |
  | MISO_MCU | 3.82 |
  | BUSY | 3.53 |
  | NRST | 3.43 |
  | DIO1 | 3.53 |

  None of this existed on the pass-2 board. There the whole corridor was over BAT_IN, so it had no crossing.
  Details in P3-…-02.

**QSPI, USB, HSE, SPI1, IMU_CS.**

- Their void and slot events are byte-identical to R6, all inherited:
  - QSPI_IO3 0.65 mm at (20.16, 42.64) and 1.15 mm at (17.5, 46.05–47.15);
  - QSPI_NCS 0.90 mm at (24.86, 42.34);
  - QSPI_IO2 2.88 mm under U1;
  - USB_DM 15.25 mm over an In2 void (In1 GND below is continuous).
- IO0 and IO1 have voids only at their own vias.
- **No new split crossing on any QSPI/USB/HSE/SPI1 net.**
- In1 carries only SWDIO, NRST, SWCLK and CAM_TX_WIRE (21 tracks; R6 had 71). In1 GND under the F.Cu critical runs is
  continuous.

**RF lines.** In1 GND under both lines, except the deliberate 2.3 mm SMA launch cut-outs.

## 5. Return vias: the allowlisted layer changes

Exact-rule probe, 0.5/0.3 mm GND via, 0.025 mm grid, within 1.5 mm:

| Via (allowlist) | Nearest GND via | Legal site within 1.5 mm? | Main blockers |
|---|---:|---|---|
| RADIO_RXEN (21.2, 30.45) | 1.553 | none | 3V3, RXEN, NSS tracks; hole spacing |
| RADIO_RXEN (23.8, 39.45) | 2.230 | none | RXEN, RAW_PROTECTED, QSPI_CLK |
| RADIO_NRST (9.3, 50.0) | 3.178 | none | via-column hole spacing, GNSS_TP_MCU row |
| RADIO_BUSY (9.4, 28.2) / (10.0, 49.5) | 1.649 / 2.596 | none | band and escape via columns |
| RADIO_MOSI (9.4, 29.2) | 1.649 | none | band via columns |
| RADIO_DIO1 (10.0, 50.5) | 3.569 | none | GNSS_TP_MCU row, via columns |
| RADIO_MISO_MCU (10.0, 28.7) | 2.110 | none | band via columns |
| RADIO_MOSI_MCU (9.4, 48.5) | 1.709 | none | escape via columns |
| GNSS_RXD_MCU (2.2, 51.5) | 1.556 | none | GNSS via diagonal |
| PYRO1_GATE_N (23.0, 88.33) | 1.815 | **yes, by board rules: (22.450, 87.455), 1.03 mm**. Refused by `ViaCheck` because it is within 0.15 mm of GND solder pads C127.2 and R127.2 (the project's own DFM rule) | — |
| PYRO1_CONT (41.1, 78.80) | 3.052 | none | 3V3, RAW_PROTECTED, SWDIO |
| ARM1_SENSE (14.55, 94.15) / (14.55, 97.55) | 5.112 / 7.885 | yes, by board rules: (13.975, 93.75) and (13.85, 97.55), 0.70 mm. They fail only `ViaCheck`'s +0.02 mm margin to ARM1_SENSE's own via, and both sit in the J1→Q120 BAT_IN corridor the entry names | — |

So the "no spot" claim holds for every interface entry. For PYRO1_GATE_N it holds under `ViaCheck`'s rules but not
under the board's DRC rules, so the wording "no DRC-legal" overstates it (P3-…-06). Both of those pyro nets are slow
or DC nodes.

## 6. Redrawn and canonicalised nets

**F2's 12 redrawn nets.**

- All are 0.15 mm (BAT_ILIM 0.2 mm).
- Copper and via counts (R6 → final):

  | Net | R6 mm / vias | Final mm / vias |
  |---|---|---|
  | LED_RED | 42.0 / 6 | 32.6 / 3 |
  | LED_YEL | 28.8 / 6 | 36.3 / 3 |
  | PULLPIN | 45.9 / 2 | 39.4 / 2 |
  | VLOGIC_SENSE | 36.2 / 3 | 32.6 / 3 |
  | BAT_ILIM | 37.8 / 2 | 9.3 / 1 |
  | BUZZ_DRV | 67.0 / 6 | 59.8 / 3 |
  | BAT_FAULT_N | 41.9 / 6 | 40.0 / 4 |
  | BAT_SW_SOURCE | 128.6 / 9 | 129.2 / 7 |
  | BAT_SW_RETURN | 164.3 / 9 | 160.3 / 5 |
  | CAM_MCU_RX | 40.4 / 4 | 32.8 / 6 |

- CAM_MCU_RX's 2 extra vias are its F.Cu hop, which keeps the In2 plane under QSPI_NCS joined (F2 §3, justified).
- `route_check` finds no rule or hygiene instance on these nets.
- Residuals:
  - CAM_MCU_TX 2.66× (P3-…-03).
  - BAT_FAULT_N U1.81→TP85.1 is 20.0 mm for 3.9 mm (5.2×). This tree topology is R6's: the R6 length was similar,
    pass-2 §4.

**F3's canonicalised power and pyro nets.**

- I compared net length, vias and width set against R6 for every changed net. Every net got shorter or stayed the same
  length. VLOGIC went from 6 to 5 vias (justified in F3 §4). No width set lost a value it needed.
- PYRO1_COLD went from 36.5 mm to 3.0 mm. The removed 33 mm branch to (18.85, 102.7) carried no pad, so it was a dead
  antenna on a pyro net. Removing it was correct.
- PYRO1_GATE is one straight 0.2 mm line through C126.1, R128.1 and Q124.4.
- USB_DP/DM copper is untouched R6.

Three inherited items remain:

- PYRO1_COLD keeps a cosmetic kink (P3-…-04).
- VCAP2 and the 3V3 feed to U12 keep their R6 loops (P3-…-05).
- `width_change_junction` on power nets lists 31 T/via width changes. None of them is a neck in a conductor's own
  current path that I could find (spot-checked BAT_IN (9.8, 40.85), RAW_PROTECTED (12.6, 40.35), CAM_5V
  (39.35, 104.55)).

## 7. Findings

No Critical and no Major. Six Minor.

| ID | Sev. | R7 copper | Finding |
|---|---|---|---|
| P3-ROUTING_QUALITY-01 | Minor | yes | RQ-01/RG-05 residual: 10 interface layer changes with no GND via within 1.5 mm. Verified that no legal site exists; acceptable once recorded |
| P3-ROUTING_QUALITY-02 | Minor | yes (F1) | 7 radio lines each cross the In2 GND-strip/BAT_IN split at both corridor ends (14 crossings). The band-end stitching is weak. Not recorded |
| P3-ROUTING_QUALITY-03 | Minor | yes | RQ-02/RQ-06 residual: NRST runs 10.2 mm broadside over In2 CAM_MCU_TX, with 11 mm of no plane under it. CAM_MCU_TX 2.66× |
| P3-ROUTING_QUALITY-04 | Minor | yes (F3) | PYRO1_COLD keeps the junction kink of its deleted dead branch. A two-segment route fits |
| P3-ROUTING_QUALITY-05 | Minor | no (R6, F3-touched) | VCAP2 (12.7 mm, via, U-turn, 4.2×) and the 3V3 feed to U12/C100 (16.3 mm, 270° wrap) are inherited loops on power nets, recorded nowhere |
| P3-ROUTING_QUALITY-06 | Minor | — | Record and allowlist precision: the RQ-11 row omits remaining items, and the `_NOGND` wording overstates PYRO1_GATE_N |

### P3-ROUTING_QUALITY-01 (Minor): RQ-01/RG-05 residual is justified

**Evidence.**

- The interface vias without a GND via within 1.5 mm, with the nearest GND via centre:

  | Group | Vias (mm) |
  |---|---|
  | Band (vias at x 9.4/10.0) | BUSY (9.4, 28.2) 1.649, MOSI (9.4, 29.2) 1.649, MISO_MCU (10.0, 28.7) 2.110 |
  | U1 escape | MOSI_MCU (9.4, 48.5) 1.709, BUSY (10.0, 49.5) 2.596, NRST (9.3, 50.0) 3.178, DIO1 (10.0, 50.5) 3.569 |
  | Other | RXEN (21.2, 30.45) 1.553 and (23.8, 39.45) 2.230; GNSS_RXD_MCU (2.2, 51.5) 1.556 |

- With the exact board rules and a 0.5/0.3 via on a 0.025 mm grid, I found no legal GND-via site within 1.5 mm of any
  of them (§5).
- Only three of the ten are SPI: MOSI, MISO_MCU and MOSI_MCU, at 1.65–2.11 mm. The others are quasi-static control or
  low-rate lines: reset, busy, IRQ, RF-switch enable and UART RX.
- The EBYTE E22-900MM22S manual gives the SPI as 0–10 Mbps (spec table "Communication interface"), at
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2212192008_Chengdu-Ebyte-Elec-Tech-E22-900MM22S_C5333985.pdf.
- At the band vias and at MOSI_MCU/BUSY/NRST/DIO1 on the U1 side, the B.Cu side of the transition references the In2
  BAT_IN arm (x 7.2–9.9), not GND. A GND via there would not carry the return. The return the change actually needs
  is P3-…-02's BAT_IN–GND stitch.

**Assessment.** The fix pass did what fits without re-spacing the escape. AGENTS §3's intent is met as far as the
geometry allows. Treat it as Minor and accept it.

**Fix.**

- Record the acceptance in R7_VALIDATION, giving the probe result and the BAT_IN-reference reason.
- Re-spacing the U1 escape (pass 2 RQ-01's suggestion) would give at most one site, near (10.0, 51.25), and only after
  the four GNSS F.Cu rows move about 0.8 mm aft. Not verified; optional.

### P3-ROUTING_QUALITY-02 (Minor): new GND/BAT_IN split crossings at the corridor ends

**Evidence (refscan, §4).**

- **Where.** On every radio line, B.Cu is over In2 GND (`R7_GND_In2_strip`) at x < 6.9. It is then over the void at
  x 6.93–7.19, then over In2 BAT_IN (`R6_BAT_IN_In2` arm) up to the vias at x 9.3–10.7. This happens at:
  - the band end, y 27.2–30.2;
  - the U1 end, y 47.5–50.5.
- **How much.** 14 GND↔BAT_IN crossings. Per line, 3.1–3.8 mm over BAT_IN.
- **Cause.** F1's RQ-14 fix: In2 GND under the corridor, with BAT_IN keeping its arm to U9.
- **Stitching at each end:**
  - **U1 end.** C80 (10 µF, BAT_IN (10.625, 52.1) / GND (7.675, 52.1), B.Cu) is 1.7–4.6 mm from the crossings.
  - **Band end.** The only direct BAT_IN–GND capacitor is C88, 100 nF at (9.15, 38.43–39.27), 8.5–11.4 mm away.
    C89 sits at the crossing, but it is BAT_IN–BAT_DAMP and reaches GND only through R166, a 0.33 Ω 2512 at
    (2.4, 28.7–35.3). That is a long, resistive loop.
- **Record.** R7_VALIDATION's RQ-14 row ("corridor over In2 GND 0 → 98.6 %") counts x < 7 only and does not mention
  the crossings.

**Impact (inference).** At 0–10 Mbps on 0.15 mm lines, with stubs ≤ 3.8 mm, the effect is a modest increase in loop
inductance. The SCK/MOSI/MISO lines share the returns that go through C88 and the damper, so there is some extra
crosstalk margin to give up. Nothing functional.

**Fix (choose one).**

- Add a 100 nF BAT_IN–GND 0402 on the BAT_IN arm close to the band-end crossing, for example beside (7.6–8.8, 26.6),
  the BAT_IN stitch vias. Placement not checked.
- Or record the crossings, with C80, C88 and C89/R166 as the stitch, and accept them.

### P3-ROUTING_QUALITY-03 (Minor): NRST over CAM_MCU_TX, and CAM_MCU_TX's length

**Evidence.**

- RADIO_NRST B.Cu (19.0, 24.5)–(40.0, 24.5) lies over CAM_MCU_TX In2 (28.55, 24.55)–(38.75, 24.55): 10.2 mm, 0.05 mm
  offset, across the 0.2 mm prepreg.
- The In2 GND strip is cleared round the CAM_MCU_TX track, so NRST has no plane under it for 11.05 mm,
  (28.15–39.15, 24.5).
- CAM_MCU_TX U1.46→U12.5 is 65.59 mm (2.66×) with 5 vias. Its In2 run along y 24.55 is the cause of the NRST overlap.
- **Is there room to move either?**
  - NRST cannot move. The only lane between the strip fence (via copper to y 23.6) and CAM_MCU_TX's clearance
    (y ≈ 24.28) is DIO1's at y 24.0.
  - CAM_MCU_TX has no free In2 lane south of it: BAT_SW_SOURCE at y 25.0, BAT_SW_RETURN at y 26.325 (F2 §8).

**Assessment.** Both are unchanged since pass 2, where the skeptics' majority graded RQ-02 Minor. NRST is a
quasi-static reset held by R311 (2.0 kΩ), and CAM_MCU_TX is a UART. Minor.

**Fix.** Owner acceptance, recorded. Optionally, a later pass could reorganise the band so that CAM_MCU_TX crosses it
on F.Cu or at y ≥ 25.3. That would clear both items.

### P3-ROUTING_QUALITY-04 (Minor): PYRO1_COLD kink

**Evidence.**

- PYRO1_COLD is now R131.2 (29.72, 86.1)→(29.335, 85.715)→D120.1 (31.05, 84.0).
- The first leg runs 0.54 mm away from D120.1 (north-west), and the route then turns 90° north-east. The scan flags it
  as `right_angle_corner` plus 45° entries into both pads.
- The kink point is where R6's deleted 33 mm dead branch joined.
- **A cleaner route fits:** (29.72, 86.1)→(29.72, 85.33)→(31.05, 84.0). With `fitprobe` at a 0.3 mm clearance it has no
  collision. Pyro rule C (PYRO1_OUT to the sense nets) is 0.3 mm. The nearest copper is R131.1, PYRO1_OUT, 0.48 mm
  from the vertical and 0.66 mm from the diagonal. Geometry only, not a DRC run.

**Fix.** Replace the two segments with the route above and rerun the gate. `check_actuators` hashes pyro copper, so
its hash needs an update.

### P3-ROUTING_QUALITY-05 (Minor): inherited power-net loops recorded nowhere

**Evidence.**

- **VCAP2** (U1.73, STM32H743 core-regulator capacitor pin → C20.1 2.2 µF, B.Cu (16.0, 60.8)):
  - route: F.Cu (14.3, 58.5)→(11.1, 58.5)→(10.6, 59.0)→(10.6, 59.6)→(13.4, 62.4)→via (16.0, 62.4)→B.Cu→C20.1;
  - 12.67 mm and 1 via for a 3.0 mm octile distance (4.2×). `route_check` lists it as `u_turn`;
  - the topology is R6's. F3 narrowed the former 0.3 mm stretch to 0.25 mm, which meets its own narrowest-width rule.
- **3V3 feed to U12.3/C100** (camera translator VCCA):
  - via (36.94, 52.65)→…→(39.13, 56.07)→(38.45, 56.75)→(40.25, 58.55)→(41.55, 58.55)→(42.95, 57.15)→(42.95, 54.5)
    →(41.58, 54.5)→C100.1;
  - 16.32 mm for 5.16 mm (3.2×), with a 270° wrap and a backward jog. R6 topology; F3 fixed only its off-angle
    segment.
- **Direct alternatives collide (`fitprobe`):**
  - VCAP2 via (12.9, 58.5) with B.Cu to C20: collides with C17.1/C17.2, 3V3 B.Cu and the USB_DP via.
  - VCAP2 via inside the ring at (15.7, 58.5): collides with SWDIO, SWCLK and TP85.
  - A direct 3V3 B.Cu run at y 53.55: collides with 3V3A B.Cu.

  So a fix means moving parts (C20/C17, or a different 3V3 tap).
- **Record.** RG-15's disposition names only slow signal nets (SWCLK, SWDIO, CAM_PWR_EN). These two power-net loops
  are not dispositioned.

**Impact (inference).** About 4–5 nH and about 25 mΩ in VCAP2's loop. ST's guidance is to place the VCAP capacitors
close to the pins; I did not re-check it in ST's documents in this pass. The 3V3 wrap feeds a low-current translator,
so it is cosmetic.

**Fix.** Add both to R7_VALIDATION as accepted inherited debt. Alternatively, move C20 next to U1.73 in a later
revision.

### P3-ROUTING_QUALITY-06 (Minor): record and allowlist precision

1. **RQ-11 row incomplete.** R7_VALIDATION says "IO0 corner and VBUS_SENSE jog fixed". Four items are left out:
   - the 0.212 mm 45° jog into IO0's via, (15.4, 51.0)→(15.55, 50.85), which remains;
   - the U1-side via columns, still at mixed x 9.3/9.4 (NSS and NRST at 9.3, MOSI_MCU at 9.4);
   - the GNSS fan diagonals, still uneven: TP_MCU steps 1.5 mm from x 12.4, the others 2.0 mm from x 11.2–11.5;
   - the strip columns, still at 0.6/0.4/0.4/0.4/0.8 mm pitch.

   All are Minor. They should be listed as kept.
2. **Allowlist wording.** `tools/route_check.py` `_NOGND` says "no DRC-legal GND via spot within 1.5 mm".
   - For PYRO1_GATE_N (23.0, 88.33), a 0.5/0.3 via at (22.45, 87.455), 1.03 mm away, meets the board's DRC rules. It is
     refused only by `ViaCheck`'s own "no via within 0.15 mm of a GND solder pad" rule (C127.2, R127.2).
   - Suggested wording: "no spot under r7_route.ViaCheck (board rules + 0.02 mm, not within 0.15 mm of a GND solder
     pad), bare TP 1.0 mm, Tag-Connect 0.508 mm, Pyro D".

## 8. What is clean

- **RF lines.** Straight, 0.30 mm, no via, In1 GND continuous except the launch cut-outs.
- **FB31 feed.** One 0.4 mm run, no pad pass-through, lands on the main 3V3 plane. FB30's feed is 1.05 mm. 3V3_RADIO and
  3V3_GNSS are daisy-chained through their capacitors.
- **Corridor bus.** 11 columns at 0.5 mm pitch, ordered, no crossings, In2 GND under it. The GND strip is stitched
  mid-corridor at (6.85, 40.5) and at both ends.
- **Interface widths.** One width (0.15 mm) on every interface net. MISO/MOSI swapped inside the escape vias.
- **RXEN and TXEN.** RXEN stays off U31's body and enters pad 10 at its end. TXEN's loop stays outside U31's keep-out.
- **QSPI.**
  - IO0's layer changes have GND vias at 0.776 mm, and IO1's at 1.500 mm.
  - No new slot under any QSPI net. The remaining slots are R6's, at identical positions.
- **Hygiene.** Board-wide, every `route_check` rule and hygiene category is 0 on critical nets.
- **Redrawn nets.** All shorter than or equal to R6 except LED_YEL, with fewer vias and no U-turns.
- **Pyro block.** The dead PYRO1_COLD branch is gone and PYRO1_GATE is a single line.
- **Fix-pass regressions.** None found apart from P3-…-02, a by-product of the RQ-14 fix.

## 9. Scripts and renders (scratch, not in the repository)

`<scratch>/p3rq/`:

- **Board snapshots:** `r7.kicad_pcb` (final, `7660620c…`), `p2.kicad_pcb` (`03fe7572…`), `r6.kicad_pcb`
  (`184a87e8…`).
- **Dumps:** `r7.json`, `p2.json`, `r6.json`.
- **Scripts:**
  - `refscan.py` (reference/split scan) → `ref_{r7,p2,r6}.json`;
  - `viaprobe.py` (exact-rule GND-via site search);
  - `fitprobe.py` (candidate-route clearance);
  - `near.py` (per-net copper compare R6/P2/R7);
  - `metrics.py` and `trace.py` (from pass 2);
  - `route_check` reports `route.json`, `route_p2.json`, `route_r6.json`;
  - pass-2 `scan.py` output `scan_r7.json`;
  - gate log `check.log`.
- **Renders** (`img/*.svg.png`): `u1left_FB`, `band`, `bandeast`, `strip_radio`, `strip_gnss`, `camtx`, `pyro`,
  `vcap2`, `u12`.
