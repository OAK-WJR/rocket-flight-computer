# R7 review pass 2: routing quality of critical and new nets

Reviewer scope: electrical routing quality (the owner's "clean routing" acceptance criterion and AGENTS.md §3) of
the new radio/GNSS interface, the RF lines, the 3V3 feeds to FB30/FB31, the R6 copper that step B rerouted or
redrew, the left-edge B.Cu corridor and the area round U1's left side. Untouched R6 copper is reported too,
labelled as R6, because the criterion applies to the whole board.

Board reviewed: `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`03fe75720f46b1382d9d3216dbffd8ae642d0125722c04589ff97c964aa86d54` (the step B handoff hash), snapshotted to a
scratch directory before measuring. Reference: R6 board `git show 3b215ba:m3_design/assembly_review/m3.kicad_pcb`,
translated +18 mm in y. Read-only: no repository file other than this report was written, and the board was never
saved.

## 1. Method

1. KiCad 10.0.6 Python (`pcbnew.LoadBoard`) dumped every track, via, pad (with bounding box and copper layers),
   footprint and filled zone polygon of both boards to JSON. All further analysis is plain Python on that dump.
2. **Origin tagging.** Each R7 track is tagged R6 if a track with the same layer, width and endpoints (within
   2 µm, after +18 mm in y) exists on the R6 board, otherwise R7. Result: 2,327 R6 and 450 R7 tracks; 422 R6 and
   277 R7 vias (most R7 vias are strip GND stitching).
3. **Geometry hygiene, whole board.** The checks were: angle off 0/45/90°; interior angle at plain two-segment
   joints (no pad or via there); unmerged collinear joints; collinear overlaps; parallel same-net segments that
   overlap or nearly touch (gap < 0.1 mm); T-joints on segment interiors; segments < 50 µm and < 0.25 mm; jogs
   (in and out segments parallel, middle ≤ 1 mm); dangling ends (no pad, via, track, T-joint or same-net fill at the
   end); redundant copper loops (cycle rank of each net's track graph, with every pad and via contracted to one
   node).
4. **Per-line metrics.** For each logical line (through its series resistor), I took the shortest copper path from
   pad to pad, with its length, vias and layer changes. The detour ratio is that length divided by the octilinear
   distance (max(dx,dy) + 0.414·min(dx,dy), the shortest 0/45/90 path), with Manhattan distance alongside.
5. **Reference plane.** Each segment was sampled every 0.1 mm, and the pour net filling the adjacent layer was
   looked up (F.Cu→In1, B.Cu→In2, In2→B.Cu). Runs of 0.4–0.7 mm at segment ends are via antipads, not voids.
6. **Return vias.** For every via of the critical/new nets I measured the distance to the nearest GND via and the
   nearest GND through-hole pad.
7. **Clearance.** For each R7 non-GND segment I measured the minimum edge distance to same-layer foreign copper
   (tracks, vias, pad bounding boxes). I also probed candidate GND via sites: a 0.6/0.3 mm via, ≥ 0.2 mm from all
   non-GND copper on every layer.
8. **3V3 feeds.** A resistance-weighted shortest path ran from FB30.1/FB31.1 to the In2 3V3 fill (35 µm outer and
   30 µm inner copper, 1.72e-8 Ω·m).
9. **Renders.** I made cropped SVG views drawn from the dump (F.Cu red, B.Cu blue, In2 teal, pours shaded, keep-outs
   dashed magenta, focus nets labelled), rasterised with Quick Look, and looked at each one. They are in the
   reviewer's scratch directory, not in the repository (see §8).

## 2. Per-line metrics (new interface and critical nets)

| Line | Routed (mm) | Octilinear (mm) | Ratio | Ratio vs Manhattan | Layer changes | Segments | Copper (mm) |
|---|---|---|---|---|---|---|---|
| RADIO_NSS U1.51→U31.14 | 57.40 | 36.62 | 1.57 | 1.34 | **4** | 14 | F 32.0, B 25.4 |
| RADIO_SCK U1.52→R313→U31.15 | 57.52 | 35.85 | 1.60 | 1.37 | 2 | 14 | F 31.3, B 25.3 |
| RADIO_MOSI U1.54→R315→U31.13 | 61.62 | 39.39 | 1.56 | 1.35 | 2 | 15 | F 35.0, B 25.8 |
| RADIO_MISO U31.12→R314→U1.53 | 64.24 | 40.16 | 1.60 | 1.39 | 2 | 15 | F 33.0, B 30.4 |
| RADIO_BUSY U1.55→U31.11 | 66.66 | 42.43 | 1.57 | 1.37 | 2 | 13 | F 36.1, B 30.6 |
| RADIO_NRST U1.56→U31.3 | **85.44** | 44.50 | **1.92** | 1.51 | **4** | 16 | F 32.3, B 53.1 |
| RADIO_DIO1 U1.57→U31.20 | 69.09 | 39.05 | **1.77** | 1.39 | **4** | 14 | F 17.5, B 51.6 |
| RADIO_RXEN U1.45→U31.10 | 48.52 | 40.62 | 1.19 | 1.06 | 4 | 15 | F 38.8, B 9.7 |
| RADIO_TXEN U31.9→U31.19 | 25.17 | 10.95 | 2.30 | 2.02 | 2 | 7 | B 22.7 (round the keep-out) |
| GNSS_TXD U1.64→R305→U30.2 | 50.61 | 37.28 | 1.36 | 1.22 | 2 | 8 | F 17.5, B 32.2 |
| GNSS_RXD U1.63→R306→U30.3 | 50.39 | 36.32 | 1.39 | 1.26 | 2 | 8 | F 18.4, B 31.1 |
| GNSS_TP U30.4→R307→U1.61 | 50.21 | 34.87 | 1.44 | 1.33 | 2 | 10 | F 17.7, B 31.7 |
| GNSS_RESET_N U1.65→U30.9 | 59.34 | 35.01 | **1.69** | 1.68 | 2 | 8 | F 18.5, B 40.8 |
| QSPI_IO0 U1.58→U3.5 (R7 reroute) | 25.90 | 21.70 | 1.19 | 1.01 | 2 | 9 | R6 had 27.64 mm, 0 vias |
| QSPI_IO1 (R6 reference) | 26.31 | 22.60 | 1.16 | 0.86 | 2 | 5 | |
| QSPI_IO3 (R6 reference) | 24.06 | 20.17 | 1.19 | 1.00 | 2 | 10 | |
| VBUS_SENSE U1.62→R9.2 | 22.93 | 18.75 | 1.22 | 1.22 | 2 | 10 | In2 20.4 |
| 3V3_RADIO FB31.2→U31.1 | 6.40 | 4.43 | 1.44 | 1.39 | 0 | 4 | F, through C310/C312/C311 (intended) |
| 3V3_GNSS FB30.2→U30.8 | 5.25 | 5.03 | 1.04 | 0.84 | 0 | 5 | F |
| **3V3 FB31.1→In2 3V3 fill** | **16.90** | ≈5.4 to the plane edge | **≈3.1** | | 1 | 9 | **34.4 mΩ** |
| 3V3 FB30.1→In2 3V3 fill | 1.05 | | | | 1 | 1 | 2.3 mΩ |
| GNSS_RF_ANT J30.5→R304.1 | 4.83 | 4.83 | 1.00 | 1.00 | 0 | 1 | F, W 0.30 |
| RADIO_RF_ANT J31.5→R316.1 | 5.30 | 5.30 | 1.00 | 1.00 | 0 | 1 | F, W 0.30 |

The interface lines' ~1.6× ratio comes from the left-corridor topology: about 16 mm per line goes west to x 1–6
and back east. Step B forced this topology (VLOGIC hold-up rail on B.Cu at x 11–11.9, the power-input area and C84
west of U1's radio pins), and I did not count it as a defect in itself. NRST, DIO1, GNSS_RESET_N and TXEN go
beyond it; see the findings.

**RF lines are clean.** They are straight, 0.30 mm wide on every segment, with no via and no bend apart from the
0Ω pi-row dogleg (0.86 mm across x, deviation 2 in the handoff). In1 GND is solid under them except the
deliberate launch cut-out (2.2 mm under each SMA centre pad). The only stubs are the DNP shunt pads (0.94 mm).

## 3. Reference planes and return vias

**B.Cu runs of the new lines over an In2 void.** After the band cut, In2 at y 23.5–26/27 is GND only in the strip
(y < 23.5), 3V3 only in the FB30 lobe (x 9.9–14), and empty elsewhere.

| Net | Segment (B.Cu) | In2 under it |
|---|---|---|
| RADIO_NRST | (19.00,24.50)–(40.00,24.50) | **void 21.0 mm**; also directly over In2 CAM_MCU_TX (28.55–38.75, y 24.55) for **10.2 mm at 0.05 mm offset** |
| RADIO_DIO1 | (18.40,24.00)–(32.10,24.00) | **void 13.7 mm** |
| GNSS_RESET_N | (2.40,24.10)–(14.30,24.10) | void 7.4 mm, then the **3V3 lobe 3.9 mm** (plane change under the track) |
| GNSS_TP_MCU | (3.00,25.75)–(9.31,25.75) | void 6.3 mm |
| GNSS_RXD | (2.80,25.20)–(8.21,25.20) | void 5.4 mm (+0.85 on the 45° corner) |
| GNSS_TXD_MCU | (2.60,24.65)–(7.11,24.65) | void 4.5 mm (+1.27 on the corner) |
| Corridor columns (all 11) | x 1.2–6.2, y ≈ 26–52 | In2 **BAT_IN** plane (R6_BAT_IN_In2, x 0.3–9.9, y 26–80), 18–27 mm per line |

F.Cu segments of every focus net run over In1 GND apart from antipads. The In2 3V3 plane as a whole is not worse
than R6: it has 6 fill islands and 608 mm² in R7, against 11 islands and 479 mm² in R6.

**Ground return next to layer changes (AGENTS §3).** On the R6 board, 7 of the 8 QSPI vias have a GND via
0.75–0.92 mm away. The new vias:

| Via group | Vias | Nearest GND via (mm) | Free GND via site found (0.2 mm probe) |
|---|---|---|---|
| Corridor bottom, radio (x 9.4/10.0, y 27.2–30.2) | NSS, SCK, MOSI, MISO, BUSY, NRST, DIO1 | **7.52, 6.84, 6.62, 5.91, 5.75, 5.01, 4.92** | (9.7,30.95) and (8.8,26.6): max ≈ 1.8 |
| Corridor top, GNSS (x 1.2–2.7, y 51.0–52.5) | RESET_N, TXD_MCU, RXD_MCU, TP_MCU | **9.78, 9.08, 8.38, 7.68** | (2.0,53.3): 1.1–2.4 |
| U1 side, radio (x 9.3–10.7, y 47.5–50.5) | NSS 0.95, MOSI 1.94, SCK 1.72, MISO 2.55, BUSY 3.07, NRST 3.41, DIO1 4.03 | (C84's GND via (9.0,46.6)) | none within 2 mm for BUSY/NRST/DIO1 |
| QSPI_IO0 (R7 vias) | (12.90,44.40) 3.55; (15.55,50.85) 1.61 | | (13.7,44.4): 0.81; none for the inner via |
| NSS hop in the strip | (23.20,17.30) 3.28; (23.60,15.27) 3.61 | | (23.9,17.6) 0.76; (22.9,14.97) 0.76 |
| RXEN | (21.20,44.45) 3.61; (23.80,39.45) 2.23; (21.20,30.45) 2.74; (20.60,27.05) 1.05 | | (20.3,43.65) 1.20; (19.8,30.25) 1.41 |
| GNSS strip side | TP (9.31,25.75) 3.88; RXD (8.21,25.2) 2.69; TXD (7.11,24.65) 1.57; RESET_N (14.3,24.1) 0.81 | | (8.3,26.4): 1.2 |
| Strip, others | TXEN (31.13,20.15) 3.09; DIO1 (32.4,20.15) 1.97; NRST (19.0,24.5) 1.44, (40.0,24.5) 0.94; DIO1 (18.4,24.0) 0.73 | | |

No GND through-hole pad is closer for any of these (the nearest is ≥ 17.9 mm). R6, for comparison: the USB_DP/DM
vias at (8.9,76.35), (8.9,74.75) and (10.05,76.3) are 4.6–6.1 mm from a GND via and 3.1–3.8 mm from J3's shell pads.

## 4. Board-wide hygiene counts

| Check | R6-origin copper (untouched) | R7-new copper |
|---|---|---|
| Segment off 0/45/90° | 1 (3V3 B.Cu (41.35,58.55)–(42.95,57.15), 3.81° off) | 0 |
| Acute joint (interior < 90°, outside pads), including 0° fold-backs | **11** (3 fold-backs) | **2** |
| Unmerged collinear joints | 25 | 3 (+1 mixed) |
| Collinear overlaps | 75 | 3 |
| Parallel same-net pairs overlapping or < 0.1 mm apart | **76** | **6** |
| Redundant copper loops (nets) | 5 (all from overlap duplicates) | **2 (BAT_ILIM 3 loops, PULLPIN 1)** |
| Segments < 50 µm | **287** | 7 |
| Segments < 0.25 mm | 463 | 27 |
| Jogs (middle ≤ 1 mm) | 103 (55 on critical-class nets) | 23 |
| T-joints on segment interiors | 75 | 5 |
| Dangling ends | 0 | 0 |

**Redrawn R6 nets (step B session file), R6 → R7.** BUZZ_DRV 67.0→64.1 mm, 6→5 vias; BAT_FAULT_N 41.9→42.9,
6→6; BAT_SW_SOURCE 128.6→128.9, 9→7; BAT_SW_RETURN 164.3→161.5, 9→7; **LED_RED 42.0→62.7, 6→2**; LED_YEL
28.8→33.2, 6→6; CAM_MCU_TX 88.6→70.6, 3→5; CAM_MCU_RX 40.4→40.6, 4→4; **PULLPIN 45.9→55.0, 2→6**; **PULLPIN_EXT
5.6→13.7, 1→2**; **VLOGIC_SENSE 36.2→43.5, 3→6**; BAT_ILIM 37.8→36.8, 2→4. In total, 727→754 mm and 57→60 vias.
LOGIC_SOURCE_ST and CAM_FAULT_N have no changed copper.

Per connection (octilinear ratio): LED_RED R32.1→U1.38 62.45 mm, **2.79×**; CAM_MCU_TX U1.46→U12.5 70.27 mm,
**2.85×**, 5 layer changes; PULLPIN D122.3→U1.8 46.45 mm, 1.74×, 6 layer changes; VLOGIC_SENSE U1.17→R60.2
31.73 mm, 2.01×; BAT_FAULT_N TP85.1→U1.81 20.0 mm, 5.19×. That last ratio is mostly R6: BAT_FAULT_N's R6 length
was similar.

## 5. Left-edge B.Cu corridor and U1's left side

**Corridor: a tidy bus with three weaknesses.**

- **Layout.** 11 columns sit at a uniform 0.5 mm pitch, x 1.2–6.2, 0.15 mm wide (0.35 mm gaps). West to east:
  GNSS_RESET_N, GNSS_TXD_MCU, GNSS_RXD, GNSS_TP_MCU | RADIO_DIO1, NRST, BUSY, MISO_MCU, MOSI, SCK, NSS. There are
  no crossings inside it, and both ends turn on nested 45° corners. The west column is 1.125 mm from the board edge.
- **Swaps.**
  - MISO/MOSI is swapped at U1's escape vias ((10.7,48.5)/(9.4,48.5)) with no extra via. This is the right pattern.
  - NSS/SCK is swapped with an extra via pair and a B.Cu hop inside the RF strip, (23.2,17.3)→(23.6,15.27) (RQ-09).
- **Series resistors.** R313 (x 5.7), R315 (x 5.2) and R306 (x 2.2) sit inline in their columns, and the
  neighbouring columns pass their pads at 0.155 mm, against the 0.15 mm minimum (RQ-14).
- **Weaknesses:**
  - the B.Cu corridor references In2 BAT_IN rather than GND (RQ-14);
  - no GND via is within 5–10 mm of either end's layer changes (RQ-01);
  - the GNSS rows turn east over an In2 void (RQ-13).

**Corridor bottom and F.Cu band.**

- **Pitch change.** The B.Cu rows (y 27.2–30.2, 0.5 pitch) come up through staggered vias at x 9.4/10.0, then
  compress to a 0.4 mm F.Cu band (y 27.2–29.6). This uses a fan of 45° jogs of 0.1–0.6 mm (NRST's is 0.1 mm; DIO1
  has an unmerged zero jog at (10.6,27.2)).
- **Why the fan is forced.**
  - The band is boxed in by D9's pads above (y 30.3, x 12.75–19.25), by FB30's feed via below ((11.58,26.2)) and by
    R6 BAT_IN vias at (4.6/5.9, 26.6).
  - Keeping 0.5 mm throughout does not fit, so the fan is a forced compromise (Minor, RQ-11).
- **Strip columns.** RXEN 20.6, BUSY 21.2, MISO 21.6, MOSI 22.0, SCK 22.4, NSS 23.2: pitches 0.6/0.4/0.4/0.4/0.8.

**U1's left side.**

- **Radio escapes.** They are clean: straight F.Cu at the 0.5 mm pin pitch to the vias.
- **Via columns.** The columns are mixed: x 9.3 (NSS, NRST), 9.4 (MOSI), 10.0 and 10.7.
- **GNSS escapes.**
  - They run west and then down a 45° fan at uneven pitch: 1.34, 0.50 and 0.42 mm between the diagonals.
    TP_MCU's diagonal starts at x 12.4, the others at x 11.2–11.5.
  - They then pass under C84's body between its pads.
- **QSPI_IO0.**
  - The inward reroute is shorter than R6's (25.9 against 27.6 mm). It drops R6's U-meander (11.15–12.9,
    48.4–49.4) and follows the IO1/IO3 B.Cu pattern.
  - Its via sits 0.15 mm off the pin row, (15.55,50.85), which costs a 0.212 mm 45° jog. This is forced by
    QSPI_IO3's diagonal 0.566 mm away.
  - Downstream, the R6 F.Cu staircase (12.9,42.5)→(13.5,41.9)→(14.0,41.9)→(15.6,40.3) is unchanged.
- **VBUS_SENSE.** Its inward via has a 0.2 mm In2 jog, (15.65,53.0)–(15.65,53.2), before joining the R6 run end
  to end.
- **C84's GND.** Three 0.5 mm stubs to vias at x 9.0 are fine.

## 6. Findings

Criticality: power, pyro, crystal, USB, SPI/QSPI, RF and the new radio/GNSS interface are critical. "R7" means the
copper is new or changed in R7.

| ID | Severity | R7 | Finding |
|---|---|---|---|
| RQ-01 | Major | yes | No GND via next to the layer changes of the new radio SPI, GNSS and QSPI_IO0 vias (corridor ends 4.9–9.8 mm) |
| RQ-02 | Major | yes | RADIO_NRST and RADIO_DIO1: 1.92×/1.77× detours, 4 vias each, 21.0/13.7 mm of B.Cu over an In2 void, NRST broadside over CAM_MCU_TX for 10.2 mm |
| RQ-03 | Major | yes | FB31's 3V3 feed: 16.9 mm / 34 mΩ through R161.1's pad, a 0.2 mm neck and a 7.8 mm In2 U-detour to a plane 1.2 mm from its via |
| RQ-04 | Major | yes | Two acute (45°) hairpin joints in R7 copper: PULLPIN at D122.3 and BAT_SW_RETURN at (11.9,44.125) |
| RQ-05 | Major | yes | R7 duplicate/overlapping copper, loops and micro-segments: BAT_ILIM (37 µm slot, 3 loops), PULLPIN (1.45 mm overlap, loop), GNSS_RESET_N's leftover 0.4 mm R6 stub, 3–50 µm pieces |
| RQ-06 | Major | yes | The grid-router replay left autorouter-style routes: LED_RED 2.79× with a U-turn and a meander under U1, CAM_MCU_TX 2.85×, PULLPIN/PULLPIN_EXT/VLOGIC_SENSE grown, 23 jogs |
| RQ-07 | Major | no (R6) | Untouched R6 rule violations: 11 acute joints (PYRO1_COLD fragments, 3 fold-backs), 1 off-angle segment, USB layer changes with no GND return within 3 mm |
| RQ-08 | Major | no (R6) | Untouched R6 debris: 76 overlapping/near-touching same-net pairs (USB_LIMITED, 3V3A, PYRO1_GATE…), 287 segments < 50 µm, 55 jogs on critical nets |
| RQ-09 | Minor | yes | NSS/SCK swapped by an extra via pair and a B.Cu hop inside the strip; R310 on 3V3_RADIO also forces a 10.15 mm supply run along y 21.6 |
| RQ-10 | Minor | yes | Width steps away from pads (RXEN mid-run at (20.6,25.4); 0.15→0.2 at vias) and unmerged collinear joints |
| RQ-11 | Minor | yes | Small jogs and doglegs on the interface (band fan, R307/C301 off-axis, RESET_N via off-axis, QSPI_IO0/VBUS_SENSE jogs, uneven via column and diagonal pitch) |
| RQ-12 | Minor | yes | RXEN runs 2.06 mm under U31's body edge and enters pad 10 from its side; passes U3.5 at 0.165 mm |
| RQ-13 | Minor | yes | GNSS rows turn east over an In2 void; RESET_N crosses onto the 3V3 lobe; RESET_N detour 1.69× for vertically aligned pins |
| RQ-14 | Minor | yes | Corridor references In2 BAT_IN (power) instead of GND; inline series resistors leave 0.155 mm to neighbours |
| RQ-15 | Minor | yes | GNSS limiter: the R300/Q32 pin order crosses VCC_RF and ANT_SRC, forcing ANT_SRC into a 6.6 mm U-detour (2.7×) |

### RQ-01 (Major, R7): no GND via at the new interface layer changes

**Evidence (§3 table).**
- Corridor-bottom radio vias: NSS (9.40,30.20) 7.52 mm, SCK (10.00,29.70) 6.84, MOSI (9.40,29.20) 6.62, MISO
  (10.00,28.70) 5.91, BUSY 5.75, NRST 5.01, DIO1 4.92. In every case the nearest is the fence via (12.4,23.3).
- Corridor-top GNSS vias: RESET_N (1.20,52.50) 9.78 mm, TXD_MCU 9.08, RXD_MCU 8.38, TP_MCU 7.68; nearest (9.0,46.6).
- QSPI_IO0's two new vias are at 3.55 and 1.61 mm.
- NSS hop vias 3.28/3.61; RXEN 2.23–3.61; GNSS TP strip-side 3.88.
- R6 practice: 7 of 8 QSPI vias have a GND via within 0.75–0.92 mm.
- Rule: AGENTS §3, "add ground vias next to layer changes", for critical nets, which include SPI/QSPI.

**Fix.** Add GND vias (0.6/0.3 mm) at the sites below. Each was probed free: ≥ 0.2 mm from all non-GND copper on
every layer. Confirm with DRC after adding.

| Site | Serves | Max distance after |
|---|---|---|
| (9.7,30.95) and (8.8,26.6) | corridor-bottom group | 7.5 → ≈ 1.8 mm |
| (2.0,53.3) | GNSS corridor top | 9.8 → 2.4 mm |
| (13.7,44.4) | QSPI_IO0 outer via | 0.81 mm |
| (23.9,17.6) and (22.9,14.97) | NSS hop (or remove the hop, RQ-09) | 0.76 mm |
| (20.3,43.65) and (19.8,30.25) | RXEN | 1.2 / 1.4 mm |
| (8.3,26.4) | GNSS TP/RXD strip-side vias | 1.2 mm |

No free site exists within 2 mm of the U1-side BUSY/NRST/DIO1 vias or QSPI_IO0's inner via (15.55,50.85). Opening
one needs the escape re-spaced. For example, move the four GNSS F.Cu rows (y 51.0–52.5) 0.5 mm aft and put a GND
via near (10.0,51.1). This has not been verified.

Because the corridor's B.Cu references In2 BAT_IN, a GND via alone does not close the return loop. Inference: a
BAT_IN–GND 100 nF at each corridor end, or a GND reference for the corridor (RQ-14), is also needed for a short
return path.

### RQ-02 (Major, R7): NRST and DIO1 routes

**RADIO_NRST.**
- **Length and vias.** 85.44 mm against 44.50 mm octilinear (1.92×); 4 vias, F→B→F→B→F.
- **Path.** (9.3,50.0) → corridor x 3.7 → (10.0,27.7) → F.Cu y 27.6 → (19.0,24.5) → B.Cu y 24.5 to (40.0,24.5) → F.Cu
  x 40 → R311.1 → U31.3 (34.81,14.0). The route overshoots 5.19 mm east of pin 3 to clear C310/C311/C312/R311.
- **Reference.** The B.Cu (19.0,24.5)–(40.0,24.5) is over an In2 void for all 21.0 mm. It lies directly over In2
  CAM_MCU_TX (28.55,24.55)–(38.75,24.55) for 10.2 mm, offset 0.05 mm, across 0.203 mm of prepreg (broadside).
- **Jog.** A 0.141 mm jog sits at (10.6,27.7)–(10.7,27.6).
- **Width.** 0.15 mm, stepping to 0.2 mm at the via (40,24.5).

**RADIO_DIO1.**
- **Length and vias.** 69.09 mm against 39.05 mm (1.77×); 4 vias.
- **Reference.** The B.Cu (18.4,24.0)–(32.1,24.0) is over an In2 void for all 13.7 mm.

**What is forced and what is not.** Both lines must cross the F.Cu SPI/BUSY/RXEN columns: their B.Cu runs cross
BUSY, MISO, MOSI, NSS, RXEN, SCK and 3V3_RADIO/3V3. They cannot stay on B.Cu from the corridor, because R6
BAT_IN/RAW_PROTECTED B.Cu at x 13.4–15.5, y 24.5–31.9 blocks the way. So the hops are forced. The void reference,
the broadside overlap and the NRST jog are not.

**Fix.**
1. Give the y 23.5–24.75 band an In2 GND reference. Extend `R7_GND_In2_strip` north to y ≈ 24.75 between x 14
   and 41. In2 there holds only vias today, apart from CAM_MCU_TX's run at y 24.55.
2. Move that CAM_MCU_TX In2 run (a redrawn non-critical net) to y ≥ 25.3 or off In2. This also removes the
   broadside overlap.
3. Put NRST's F.Cu band row on one y (27.7) to delete the 0.1 mm jog.
4. Use one width end to end.

Alternative, not checked: return DIO1 to F.Cu right after the bus (via ≈ (24.2,24.0)) and run it over In1 GND.

### RQ-03 (Major, R7): FB31's 3V3 feed

**Evidence.** The resistance-weighted path from FB31.1 to the In2 3V3 fill is 16.90 mm and 34.4 mΩ (FB30's is
1.05 mm and 2.3 mΩ). In order:

1. F.Cu 0.4 mm (35.10,22.15)–(35.10,25.10)–(35.10,26.60). This is split at the dropped band via's position and
   enters R161.1 0.07 mm off-centre.
2. **R161.1's pad** (a 10 k pull-up) as the junction.
3. R6 F.Cu **0.2 mm** (35.03,26.80)–(35.03,27.34), then 0.25 mm to the R6 via (35.73,27.34). The via is outside
   the plane, whose edge is at x 34.5.
4. R6 In2 0.25 mm (35.73,27.34)→(36.73,28.34)→(36.73,31.54)→(36.23,32.04)→(35.23,32.04)→(34.53,31.34): a 7.8 mm
   U-detour to reach a plane 1.2 mm from the via.

The ratio is about 3.1× the straight distance from FB31.1 to the plane edge. Ampacity is not the problem.
Inference: about 4 mV at the radio's 119 mA, and 0.2 mm outer copper is within IPC-2152 at that current. The
problem is a messy, detoured feed for the RF PA supply that rides through a resistor pad.

**Fix.**
1. Add a small 3V3 lobe to `3V3_In2` (≈ x 34.5–36.2, y 26.6–28.0) so that the existing via (35.73,27.34), or a
   dedicated FB31 via inside the lobe, lands on the plane. The lobe stays ≥ 1 mm from BAT_SW_SOURCE's In2 diagonal
   (35.16,25.0)–(42.26,32.1). A free on-plane site does not exist today: none was found in x 32.5–35.5,
   y 26.8–29.8.
2. Run one merged 0.4 mm F.Cu from FB31.1 to that via, and tap R161.1 off it.
3. Delete the 7.8 mm In2 detour.

### RQ-04 (Major, R7): acute joints

**PULLPIN at D122.3.**
- The R7 path …(32.6675,28.1404)→(32.6675,30.4404)→(32.1675,30.9404) turns back on (32.1675,30.9404)→(32.5,30.9404)
  with a **45° interior angle**.
- The tip is 7.5 µm outside D122.3's pad (bounding box x ≥ 32.175). This is step B's `_pad_joints` fix-up.
- There is also an 8 µm segment, (32.2,30.9079)–(32.2,30.9).

**BAT_SW_RETURN at (11.9,44.125).**
- R7 (11.9,45.025)→(11.9,44.125) meets R6 (11.9,44.125)→(11.2,44.825) at **45°**, a 0.7 mm spur doubling back.

**Rule.** AGENTS §3: no acute angles.

**Fix.**
- **PULLPIN.** End the R7 run at C160.1. Its R6 copper already joins D122.3, R160.2, R161.2 and C160.1:
  D122.3→(32.5,29.853)→(32.76,29.593)→(32.76,27.70)→R160.2→…→C160.1. Delete the R7 segments west of C160.1:
  (33.968,27.94)–(36.468,27.94) trimmed to C160.1, (33.968,27.94)–(33.867,27.84), (33.867,27.84)–(32.968,27.84),
  (32.968,27.84)–(32.667,28.14), (32.667,28.14)–(32.667,30.44), (32.667,30.44)–(32.167,30.94),
  (32.167,30.94)–(32.5,30.94) and (32.2,30.9079)–(32.2,30.9). This also clears RQ-05's PULLPIN overlaps and loop.
- **BAT_SW_RETURN.** Replace both segments with (11.9,45.025)→(11.7,44.825), and extend R6's (9.7,44.825)–(11.2,44.825)
  to x 11.7.

### RQ-05 (Major, R7): duplicate copper, loops and micro-segments

**BAT_ILIM.**
- The R7 0.15 mm copy (10.975,39.3)→(10.475,38.8)→(10.075,38.8)→(9.875,38.6) lies on top of R6's 0.2 mm path, with
  centres 0.07–0.10 mm apart.
- R7 (9.875,37.6)→(11.075,36.4) runs parallel to R6 (9.875,37.3)→(10.675,36.5). Both end in R84.1's pad, and the
  same-net copper between them leaves a **37 µm slot over 1.13 mm**.
- These form 3 redundant loops.

**PULLPIN.**
- R7 x 32.667 runs 0.093 mm beside R6 x 32.76 for 1.45 mm.
- R7 y 27.94 runs over R6 y 28.08 for 0.52 mm.
- R7 (32.667,30.44)–(32.167,30.94) overlaps R6 (32.2,30.9)–(32.5,30.6) for 0.424 mm.
- Together these form 1 loop.

**GNSS_RESET_N.**
- R6's C172.2 GND stub, F.Cu 0.4 mm (14.8,18.85)–(14.8,19.8), survived C172's removal and is now on GNSS_RESET_N.
- It overlaps U30.9 and the new 0.2 mm track ((14.81,19.7)–(14.81,23.59), 0.1 mm overlap at a 10 µm offset).
- Its rounded end reaches y 18.65, 0.15 mm past the pad toward the module, touching U30_KEEPOUT's edge.
- The net now carries 0.15, 0.2 and 0.4 mm widths.

**Micro-segments.**
- CAM_MCU_TX: 3 µm and 5 µm at (36.55,46.85)–(36.5533,46.8562).
- PULLPIN_EXT: 30 µm (35.0,34.57)–(35.0,34.6).
- BUZZ_DRV: 50 µm (4.25,85.0)–(4.25,85.05) inside R162.1, next to a doubled R6 (4.25,85.05)–(4.3,85.1).
- BAT_ILIM: 25 µm (4.975,59.4)–(5.0,59.4).

**Fix.**
- **BAT_ILIM.** Delete (10.975,39.3)–(10.475,38.8), (10.475,38.8)–(10.075,38.8), (10.075,38.8)–(9.875,38.6) and
  (9.875,37.6)–(11.075,36.4). Keep the stub (11.075,36.4)–(11.575,36.4), which already starts in R84.1's pad.
- **PULLPIN.** As in RQ-04.
- **GNSS_RESET_N.** Delete the 0.4 mm stub.
- **Micro-segments.** Snap each one away so the neighbours meet at one point (CAM_MCU_TX: end the vertical on the R6
  diagonal's start). Also delete the duplicated R6 BUZZ_DRV piece.
- **Session replay.** Make its `_dedupe` reject near-duplicates (parallel same-net copper < 0.1 mm apart), not only
  exact retraces.

### RQ-06 (Major, R7): the router replay reads as autorouter output

**Evidence (§4, renders `redrawn.svg.png` and `ledred.svg.png`).**
- **LED_RED.** 62.73 mm against R6's 41.99 (2.79× octilinear). Its path:
  - from R32.1 (36.6,29.7) east to x 39.45;
  - down to y 57.45 and back up (a 2 × 10 mm U-turn through a via pair at (35.75,54.65)/(33.45,51.05));
  - then west under U1's body: F.Cu (28.35,46.85)→(27.05,48.15)→(26.85,48.15)→(24.75,50.25)→(24.75,50.45)→
    (24.35,50.85)→(23.75,50.85)→(21.75,48.85)→(21.75,45.85), inside the pad ring.
  - It enters U1.38 from its heel, with two 0.2 mm jogs.
- **CAM_MCU_TX.** 70.27 mm (2.85×), 5 layer changes.
- **PULLPIN.** D122.3→U1.8: 6 layer changes against R6's 2 vias.
- **PULLPIN_EXT.** 5.6 → 13.7 mm.
- **VLOGIC_SENSE.** 3 → 6 vias.
- **Jogs.** 23 R7 jogs ≤ 1 mm: LED_RED ×5, BAT_SW_RETURN ×3, PULLPIN, PULLPIN_EXT ×2, BAT_ILIM ×2, BUZZ_DRV (In2,
  0.071 mm), CAM_MCU_TX, plus the interface fan in RQ-11.
- **Assessment.** These are slow nets, so each item alone is Minor. Together they are widespread and fail "nothing
  that looks like autorouter debris".

**Fix.**
- Hand-redraw the 12 replayed connections, with targets of ≤ 1.5× octilinear, no route under U1's body, and no
  U-turns.
- LED_RED: leave U1.38 outward from its toe (y < 45.15), and follow R6's original corridor north of the strip
  except the strip-crossing piece.
- Merge collinear runs and remove the jogs listed.
- Keep the session file only as a starting point.

### RQ-07 (Major, R6): untouched R6 rule violations

**Acute joints outside pads.**
- PYRO1_COLD at (18.95,112.3) and (18.92,112.3): 21–141 µm fragments, 0.15/0.2 mm, on a pyro net.
- RAW_PROTECTED at (37.2,83.6) and (37.2,83.575).
- CAM_5V at (35.53,33.5); SERVO4_MCU at (31.0,83.0); IMU_CS at (37.35,79.75); CAM_INPUT_LIMITED at (34.3,93.5).

**0° fold-backs (a segment doubling back over another).**
- RAW_ACT_SENSE In2 (14.63,78.0): a 5.0 mm 0.15 mm segment folded back over a 20.3 mm 0.2 mm one.
- VBUS In2 (12.6,80.55).
- VLOGIC F.Cu (27.57,27.2).

**Off-angle.** 3V3 B.Cu (41.35,58.55)–(42.95,57.15), 3.81° off (handoff §4.13).

**USB.** The USB_DP/DM layer changes at (8.9,76.35), (8.9,74.75) and (10.05,76.3) have no GND return within
3.1 mm (GND vias at 4.6–6.1 mm; J3 shell pads at 3.1–3.8 mm). USB is a §3 critical net.

**Fix.** Redraw each joint as a clean 0/45/90 joint (delete the fragments and fold-backs), straighten the off-angle
segment, and add a GND via beside each USB via, or move the USB layer change next to J3's shell.

### RQ-08 (Major, R6): untouched R6 debris

**Evidence.**
- **Overlapping or near-touching same-net parallel pairs: 76.**
  - USB_LIMITED: 0.3/0.4 mm doubled for 10.5 mm at x 28.7–28.73 and 6.1 mm at x 29.1–29.125.
  - CAM_IO_3V3: 6.2 mm at x 42.9–43.05.
  - 3V3A: several 1.7–3.4 mm pairs near (29.4–40.1, 48–54).
  - PYRO1_GATE: (21.6–26.0, 91.78–92.1).
  - RAW_PROTECTED: (15.65/15.7, 32.35–35.75).
  - CAM_5V, CAM_FB, NRST In2 (30.4–31.3, 46.6–52.2).
  - VBUS_SENSE: a 3 µm same-net slot at (13.4–15.2, 71.5–71.7).
- **Segments < 50 µm: 287.** 3V3 44, RAW_PROTECTED 16, VBUS 10, USB_LIMITED 9, 3V3A 9, CAM_5V 9, PYRO1_COLD 5,
  PYRO1_OUT 4.
- **Jogs ≤ 1 mm on critical-class nets: 55.** SWCLK ×7, VBUS_SENSE ×5, RAW_PROTECTED ×5, RAW_ACT ×3, and the
  QSPI_IO0/QSPI_CLK/QSPI_NCS steps.

**Fix.** Run a cleanup pass: merge each overlapping pair into one track of the intended width, snap and delete
sub-50 µm segments, merge collinear runs and remove jogs. Then rerun the gate. Pyro and actuator copper is hashed
by `check_actuators`, so its hashes need a deliberate update.

### RQ-09 (Minor, R7): NSS/SCK swap and R310's placement

- **The swap.** U31's west-row order from y-high is SCK, NSS, MOSI, MISO, while the ribbon from U1 delivers NSS
  outermost. NSS therefore hops F.Cu→B.Cu at (23.2,17.3), runs (23.2,17.3)→(23.2,15.67)→(23.6,15.27) under SCK's
  stub, and comes up at (23.6,15.27). That is 2 extra vias on an SPI line and a B.Cu SPI segment inside the RF
  strip.
- **Why it is forced.** R310 (NSS pull-up to 3V3_RADIO, at (24.2,20.82)) must sit east of the bus, beside the 3V3
  run. So NSS must be the east-most column above y 20.39, and the crossing is forced below it.
- **The supply run.** R310 also pulls a 10.15 mm, 0.3 mm 3V3_RADIO run along y 21.6 across the strip top.
- **Cleaner option (schematic/contract change).**
  - Pull R310 to 3V3 at the U1 end. 3V3 and 3V3_RADIO are the same rail through FB31; at DC this is equivalent
    (Inference).
  - Do the NSS/SCK swap at U1's escape vias exactly like MISO/MOSI: NSS via (10.7,47.5) with a B.Cu dogleg to row
    48.0, and SCK on F.Cu to (9.9,48.0)→via (9.4,47.5).
  - Swap corridor columns 6.2/5.7, with R313 moving to x 6.2.
  - This deletes both hop vias and the y 21.6 run.

### RQ-10 (Minor, R7): widths and merges

- **RXEN.** It changes 0.15→0.2 mm at a plain collinear joint (20.6,25.4), 1.9 mm outside the strip.
- **0.15→0.2 mm at vias.** NRST at (40,24.5); DIO1 at (32.4,20.15); GNSS_TXD_MCU, GNSS_RXD and GNSS_TP_MCU at their
  strip-side vias.
- **Unmerged collinear joints.** RADIO_DIO1 (10.6,27.2), RADIO_RXEN (20.6,25.4) and 3V3 (35.1,25.1), the last left
  where the band via was dropped.
- **Fix.** Use one width per net class end to end (0.15 or 0.2), with neck-downs only at pads, and merge the three
  joints.

### RQ-11 (Minor, R7): small jogs and pitch irregularities on the interface

**Evidence.**
- **Band fan.** Jogs of 0.1/0.2/0.3/0.4/0.5/0.6 mm (NRST/BUSY/MISO/MOSI/SCK/NSS) after the corridor vias. They are
  forced by D9 (y 30.3) and the BAT_IN vias (y 26.6).
- **GNSS_TP.** Two 0.438 mm 45° doglegs: R307 sits at x 9.0 while pin 4 and the via are on x 9.31.
- **3V3_GNSS.** A kink inside C301.1: C301 is at x 12.74 against pin 7's axis at 12.61.
- **GNSS_RESET_N.** Its via (14.3,24.1) is 0.51 mm off pin 9's axis, which costs a 0.72 mm diagonal. This is
  forced: an on-axis via at (14.81,24.1) would be 0.015 mm from R80.1 (BAT_IN), and one at y 23.6 hits the fence
  via (14.2,23.3). I record it, but propose no fix.
- **QSPI_IO0 and VBUS_SENSE.** QSPI_IO0 has a 0.212 mm jog into its via; VBUS_SENSE has a 0.2 mm In2 jog.
- **Pitch.** U1-side via columns are mixed (x 9.3/9.4); the GNSS diagonals are 0.42/0.50/1.34 mm apart; the strip
  columns are 0.6/0.4/0.4/0.4/0.8 mm apart.

**Fix.**
- Place R307 at x 9.31 and C301 at x 12.61.
- Put the via columns on 9.4/10.0/10.6 and the GNSS diagonals at one pitch, with all four starting at the same x.
- Space the strip columns at 0.4 mm. With RQ-09's swap, NSS no longer needs the 0.8 mm gap.

### RQ-12 (Minor, R7): RXEN at U31

- **Under the body.** F.Cu (20.9,9.05)–(27.32,9.05) runs inside U31's body outline (F.Fab y ≥ 8.95) for 2.06 mm
  (x 24.81–26.87). F10 and EBYTE say no wiring under the module. The drawn keep-out (25.66–34.06 × 9.8–18.2)
  excludes the pad rows, so DRC is silent.
- **Pad entry.** It enters pad 10 from its long side, not its outer end.
- **Clearance at U3.** Upstream, its diagonal (23.5,32.75)–(21.2,30.45) passes U3.5 at 0.165 mm.
- **Fix.**
  - Approach pad 10 from the south: run at y ≈ 8.0 from x 20.6, tapping R312.1 (25.6,7.43) on the way, and go up
    into the pad's outer end at y 8.3. No via or F.Cu pad lies within 0.15 mm of a 0.2 mm track at y 8.0 between
    x 20.6 and 27.32 (checked). Not DRC-checked against the pour.
  - Move the diagonal off U3.5.
  - Widen U31_KEEPOUT to the F.Fab outline on F.Cu.

### RQ-13 (Minor, R7): GNSS rows and RESET_N reference

- **Void.** GNSS_TXD_MCU, GNSS_RXD and GNSS_TP_MCU turn east on B.Cu over the In2 void (4.5, 5.4 and 6.3 mm).
- **Split.** GNSS_RESET_N crosses from void onto the 3V3 lobe (7.4 mm + 3.9 mm), a reference change under a
  reset line.
- **Detour.** RESET_N runs 59.3 mm for pins that are almost vertically aligned: U1.65 (14.3,54.5) to U30.9
  (14.81,19.7), 1.69×.
- **Fix.**
  - Extend `R7_GND_In2_strip` on the left to y 25.9 (x 0.3–9.6). That In2 area is empty, and it is clear of
    BAT_IN (y ≥ 26.0) and of the lobe (x ≥ 9.9).
  - Bring RESET_N up to F.Cu west of the lobe.

### RQ-14 (Minor, R7): corridor reference and clearance hugging

- **Reference.** The 11 B.Cu corridor columns reference the In2 BAT_IN plane for 18–27 mm each. Inference: the
  returns must cross to GND through BAT_IN decoupling at the ends, and C80/C96 are 2–5 mm from the U1-side vias.
- **Clearance.** R313, R315 and R306 inline in a 0.5 mm-pitch bus leave 0.155 mm to the neighbouring columns.
- **Fix.**
  - Preferred: give the corridor an In2 GND strip (x 0.5–6.7) by trimming `R6_BAT_IN_In2`'s west edge, if BAT_IN's
    current path allows. That is a power-integrity question for the electrical review.
  - Otherwise, add BAT_IN–GND decoupling at both corridor ends.
  - Open the neighbour columns locally round each resistor (45° jogs of 0.1 mm), or move the resistors into the F.Cu
    escape at U1.

### RQ-15 (Minor, R7): GNSS limiter crossing

- **Evidence.** R300.1 (VCC_RF, north) feeds Q32.2 (south), while R300.2 (ANT_SRC, south) feeds Q32.1 (north). The
  crossing pushes GNSS_ANT_SRC into a detour, R300.2→(8.25,12.0)→(6.6,13.65)→(5.4,13.65)→(5.1,13.35)→(5.1,11.95)→
  Q32.1 (6.0,11.05): 6.6 mm for a 2.4 mm gap (2.7×).
- **Fix.** Rotate R300 by 180°, or swap its pad numbering. A 2-pin resistor allows this. Both links then become
  short and direct.

## 7. What is clean

- The RF lines (§2).
- The corridor as a bus: uniform pitch, ordered, no crossings.
- The MISO/MOSI swap done inside the existing escape vias.
- The radio escapes at U1.
- The SPI fan-in at U31's west row: 45° chamfers, R314 inline.
- 3V3_GNSS (apart from the C301 kink) and FB30's 1 mm feed.
- QSPI_IO0's reroute, which is shorter than R6's.
- TXEN's loop, which keeps outside U31's body: x 24.5 against the body edge at 24.81.
- No dangling ends and no off-angle segment in the R7 copper.

## 8. Renders

Images made for this review are in the reviewer's scratch directory, not in the repository:
`<scratch>/rq/img/`.

| File | View |
|---|---|
| `corridor.svg.png` | x 0–26, y 22–48, F/B.Cu, interface nets labelled |
| `u1left.svg.png` | x 0–22, y 38–60: U1's left side escapes, QSPI_IO0, VBUS_SENSE |
| `strip_radio.svg.png` / `strip_gnss.svg.png` | the RF strip round U31 / U30 |
| `rxen.svg.png` | RXEN's path round U3 and the band |
| `in2.svg.png` | In2 pours and routed In2 tracks, x 0–46, y 18–64 |
| `redrawn.svg.png` / `ledred.svg.png` | the replayed R6 nets east of U1, and LED_RED/PULLPIN |
| `debris_pullpin.svg.png` / `debris_batilim.svg.png` | RQ-04/05 zooms |
| `fb31_feed.svg.png` | RQ-03, F.Cu and In2 with the 3V3 fill |

The analysis scripts (`dump.py`, `geom.py`, `metrics.py`, `refplane.py`, `trace.py`, `jogs.py`, `redrawn.py`,
`render.py`) are in the parent directory of `img/`.
