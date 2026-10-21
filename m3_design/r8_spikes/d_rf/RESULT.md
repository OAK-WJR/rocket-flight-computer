# Spike (d): RF buses and status cluster

**Verdict: the primary approach passed.** The radio and GNSS interface buses route from U1's new strip-facing pins to
the rigid RF strip on F.Cu. They use the H0 pin map (R8_DECISIONS D2 / D4, IOSWP), the seed floorplan, and no new
signal via. The fallbacks were not needed: no H1′ map, and no "+2 vias without IOSWP".

On the scratch board:
- DRC is 0 on the spike's nets and parts, and route_check (profile r8, unchanged) is 0 on the spike's nets and on pour
  findings in the region.
- All 12 rigid digests equal R7's, including `strip_gcpw` (0 of 744 samples differ).
- Fence (D16), F10 separation (D17), rf_strip, line stitching and rf_gnd_reach pass, and so do launch and module ground.
- Rebuilds are byte-identical.

The status LEDs sit legally on the west edge, as D3's primary placement asks, once J2 moves (below).

Rule changes for later steps are listed as proposals (P1–P9). The brief limits this spike to its own folder, so
R8_DECISIONS is not edited here. The findings for the orchestrator are F-1 to F-8.

## 1. Scope

- **Nets routed:**
  - every non-RF radio and GNSS interface net, MCU and module side: SCK, NSS, MOSI, MISO, BUSY, RXEN, DIO1, NRST and
    TXEN; GNSS RESET_N, TP, RXD, TXD, TIMEPULSE and SAFEBOOT_N;
  - the module supplies in the strip (3V3_GNSS, 3V3_RADIO) and their In2 3V3 feed vias;
  - the strip fence row;
  - the status LED nets.
- **Kept verbatim:** the antenna-bias limiter's DC copper (D11 says regenerate). It is in the scratch board so that the
  strip is complete; see F-3.
- **Status cluster:** read as the status LEDs (LED1/LED2/R32/R33). r8_plan §3 names them, and D3 puts them on the west
  edge, with a fallback (LEDs east, CAM_UART_OE on PE14) that would add a lane to the radio's crowded east-face escape.
  - The camera status lines CAM_FAULT_N / CAM_PWR_EN also share U1's east face with the radio lanes (D3). They are the
    camera family's to route; F-4 records the corridor this spike leaves them.

## 2. Files (this folder)

| File | What |
|---|---|
| `run_spike.sh OUTDIR` | Reproduces everything. It extracts R7 (431025d, `c872a3d3…`) with its project files, builds base and routed boards, and runs every check (~35 s) |
| `spike_base.py` | Builds the scratch base board: R7 with the R8 netlist, the seed placement plus `d_rf_place.tsv`, only the 247 rigid tracks and vias (check_r8 D15 definitions), TH1–TH3 removed, In2 GND strip / 3V3 / GND, native fill |
| `rf_route_r8.py` | **The routing module to port into step 6 (`rf_iface` / `gnss`).** Every polyline is a table or a formula of one; it also holds the fence row, the stitching vias, the status lanes and the designators of its parts |
| `d_rf_place.tsv` | Placement overrides on the seed: proposed `r8_place.tsv` rows (P1–P3) |
| `seed_b0_place_final.tsv` | Copy of the seed, `partial/b0_place_final.tsv` |
| `spike_verify.py` | Runs check_r8 / check_r7 strip functions, kicad-cli DRC and route_check, each unchanged and on the whole board. It sorts findings into spike (a spike net or part takes part) and elsewhere |
| `gcpw_compare.py` | Compares the `strip_gcpw` profile with R7's sample by sample (F-1 / F-2 diagnostics) |
| `tab_scan.py` | Panel-tab window scan (`partial/tabs.py` rule) |
| `strip_mouth_fcu.png` | F.Cu render, x 0–46, y 0–47 (y down = aft edge at the top) |
| `PROGRESS.md` | Running log |

## 3. Verification (final run, `run_spike.sh`)

| Check | Result |
|---|---|
| Rigid groups (check_r8 `rigid`, 12 digests) | **all equal R7**: outline, m3_holes, j122_tie, j1, pyro_block_area, ch1_parts, ch1_copper, strip_parts, strip_rf_copper, strip_gnd, strip_rule_areas, strip_gcpw |
| `strip_gcpw` sample comparison | 0 of 744 side samples differ |
| DRC (kicad-cli, all severities, all track errors) | **0** on spike nets and parts. The 731 elsewhere are other families' unrouted nets and seed-placement issues. Library-link checks are excluded because the scratch project has no footprint table |
| route_check `--profile r8` | **0** failing on spike nets and on pour findings in x 0–46, y 0–46. The 14 elsewhere are the CH1 exit stubs (other spikes) and GNSS_LNA_EN / GNSS_VCC_RF (F-3) |
| Fence (D16) | 25 GND vias at y 23.3; openings below |
| rf_strip (STRIP_F / STRIP_B / STRIP_VIA, keep-outs, U31 body) | OK |
| rf_line_stitching | GNSS W 3.90 / E 2.65, radio 1.55 / 1.55 mm (= R7); In1 under the RF lines 0.000 mm² missing |
| rf_gnd_reach (strip) | F.Cu 3.04 mm, B.Cu 3.49 mm (≤ 4.0) |
| F10 separation (D17) | OK. Nearest RF part to a restricted part: FB31 to U7 5.16 mm. Nearest to a fast line: R306 to USB_DP (D4.3) 6.01 mm. R310 / R313 / R315 are 6.04 mm from U1, and 6.29 / 6.29 / 6.45 mm from QSPI pads |
| check_r8 contract (pin map, PULLS with R310 on 3V3 at the MCU end, SERIES driving ends, loader pins) | no finding on a spike net or part. All 24 findings are other families' or the seed's (F-5, F-7). The four J2 legend findings also fail with the seed's J2: the legends still sit at R7's J2 position until r8_post |
| AGENTS §3 GND via at layer changes | Only TXEN changes layer (R7's loop): 2 vias, each with a rigid GND via 0.72 mm away |
| In1 / In2 tracks (S15 / S16) | none from this spike |
| Byte-identical rebuild | base `191397e4…`, routed `485cd0c4…`, the same on two runs (KIID seeds 8401 / 8402) |

## 4. Geometry the real build should reuse

KiCad mm, y = 0 at the aft edge. U1 is at (23, 45), rotation 0, so aft pins 51–75 sit at y 37.45 with x = 29 − 0.5(n −
51), and east pins 26–50 sit at x 30.55 with y = 51 − 0.5(n − 26). Lanes are 0.2 mm on F.Cu over In1 GND, with
pad-centre ends and no autorouter.

**One "river".** The GNSS and radio lanes leave U1's aft face and south-east corner as parallel 45° runs:
- GNSS on the north-west side, radio on the south-east side;
- 0.6 mm perpendicular between the groups;
- mitered corners, so each group keeps its pitch through the 45° run.

**GNSS bus (4 lanes, 0 vias):**
- Pins 64 / 63 / 62 / 61 (x 22.5 / 23.0 / 23.5 / 24.0) go straight down, then into a 45° run that starts at y
  36.40 − 0.25·i.
- They meet a vertical section at x 18.2 / 18.8 / 19.4 / 20.0 (0.6 mm pitch). R306 sits inline on RXD at (18.8, 29.6),
  rotation 90.
- A mitered turn west (0.6 mm 45° legs) leads into rows at y 28.2 / 27.6 / 27.0 / 26.4.
- Each lane then turns down at its strip x: 7.11 (R305.2), 8.21 (U30.3), 9.00 (R307.2), 14.81 (U30.9).

**Radio bus (0 new vias):**
- **Aft trio (RXEN / BUSY / MISO, pins 56 / 55 / 54):**
  - 0.5 mm pitch, 45° run from y 36.400 / 36.193 / 35.986 to x 20.6 / 21.1 / 21.6, straight through the fence;
  - inside the strip, one mitered 0.4 mm step east (at y 22.40 / 22.61 / 22.81) to x 21.0 / 21.5 / 22.0;
  - straight down to square-cornered turns into U31.11 and R314.2;
  - RXEN rounds the south-west corner along y 7.58, through R312.1, to U31.10.
- **MOSI (pin 53):** 45° run on x − y = −7.779 to x 22.6, R315 inline (22.6, 29.5), then straight down to a 45° peel
  into U31.13.
- **NSS (pin 47):** east stub, down x 31.65 past pins 48–50, 45° run on x − y = −7.072 to x 23.2, then straight down to
  a 45° peel into U31.14.
  - R310 is tapped by a 0.8 mm stub at y 29.93: R310 at (24.1, 29.5), rotation −90, with its 3V3 via at (24.1, 28.45)
    into In2.
- **SCK (pin 46):** east stub, down x 32.25, 45° run on x − y = −5.6 to x 25.1, R313 inline (25.1, 29.5).
  - Inside the strip one 45° step to x 24.5. It passes the rigid GND via (23.8, 17.7) on its east side, 0.3 mm from the
    via and 0.26 mm clear of U31's body edge, and enters U31.15 from the north.
- **DIO1 (pin 45):** east stub, down x 32.85 beside NRST, one 45° step at y 30.9 to x 32.4, then straight down between
  the rigid GND vias (31.73 / 33.0, 20.55) to U31.20.
- **NRST (pin 39):** east stub, down x 33.4 (0.2 mm from U12's pad 8), one 45° run from (33.4, 31.0) to (40.0, 24.4),
  then R7's strip path: down x 40, west along y 14.0 through R311.1 to U31.3.
- **TXEN:** R7's B.Cu loop, verbatim (inherent; passes on the D10 baseline, ratio 1.25).
- **East-face escape order:** NSS 31.65, SCK 32.25, DIO1 32.85, NRST 33.4. NSS runs 0.2 mm from the pin 48–50 pad
  ends, so those pins' decoupling must dive inward (F-4).

**Module supplies:**
- 3V3_GNSS keeps R7's geometry, with C300 nudged (P2).
- 3V3_RADIO runs FB31.2 → C310.1 → C312.1 → C311.1 → U31.1, 0.4 mm wide.
- The FB30 and FB31 3V3 sides take one 0.6 mm via each into In2 3V3: (12.33, 24.40) and (35.10, 24.40).

**Fence row (y 23.3, 0.5 / 0.3 mm GND vias):**

0.90, 2.90, 4.90, 6.40, 7.685, 9.70, 12.30, 14.20, 16.20, 18.20, 20.00, 22.10, 24.15, 26.00, 28.00, 30.00, 31.80,
33.00, 34.40, 35.80, 37.80, 39.40, 40.60, 42.60, 44.60.

Openings wider than 2.0 mm:

| x (mm) | Width (mm) | Lanes |
|---|---:|---|
| 7.685–9.70 | 2.015 | RXD, TP |
| 9.70–12.30 | 2.60 | 3V3_GNSS |
| 20.00–22.10 | 2.10 | RXEN, BUSY, MISO |
| 22.10–24.15 | 2.05 | MOSI, NSS |

The other lane gaps (TXD, RESET_N, SCK, DIO1, the FB31 3V3 feed, NRST) are 1.2–2.0 mm.

**Stitching outside the strip:** GND vias (22.10, 26.70) and (24.15, 26.50), in the MISO–MOSI slot and the NSS–SCK gap
above the fence.

**Status cluster (D3 primary), F.Cu, 0 vias:**
- LED_RED leaves pin 86 west, turns aft first in a 2.2 mm 45° run, and goes to R32 (11.1, 41.8, rot 180), then LED1
  (6.6, 41.8, rot 0).
- LED_YEL leaves pin 88 west and drops one 1.0 mm 45° run to R33 (11.3, 44.0, rot 180), then LED2 (6.6, 44.0, rot 180).
- LED_RED sits aft of LED_YEL, and the two lanes never cross.

## 5. Measurements

| | R7 (431025d) | Spike |
|---|---:|---:|
| Interface copper, 20 RADIO / GNSS non-RF nets (route_check `--routes`) | 748.5 mm | **394.8 mm** |
| Signal vias on those nets | 34 | **2** (R7's TXEN loop only) |
| Critical layer changes without a GND via | — | 0 |

**Per-net ratio** (copper / octilinear MST):

| Net | Ratio | Note |
|---|---:|---|
| RXEN | 1.30 | D10 baseline 1.21 |
| GNSS_RXD (module side) | 1.33 | |
| GNSS_TP_MCU | 1.26 | |
| GNSS_TXD_MCU | 1.25 | |
| NRST | 1.19 | |
| BUSY | 1.19 | |
| SCK_MCU | 1.18 | |
| NSS | 1.14 | |
| RESET_N | 1.11 | |
| Every other spike net | ≤ 1.07 | |
| TXEN | 2.30 | D10 baseline 1.25 |

- **Bends:** 83 over the 27 spike nets (route.json).
- **Spike nets:** 118 segments, 426.3 mm, including the supply, 3V3 and LED copper.
- **Panel tabs (5 mm windows):**
  - left edge y 0.5–6.0 and 48.5–117.5 (seed: 41.5–117.5; J2 and LED2 now block y 41.5–48.5);
  - right edge y 0.5–25.0 (unchanged).
- **Tight spots** (legal, at or near the 0.15 mm minimum):
  - the fence via at 22.10 against MISO and MOSI: 0.15 / 0.15;
  - the via at 7.685 against RXD 0.175 and against R305.2 0.155;
  - NSS against the pin 48–50 pad ends: 0.20;
  - NRST against U12.8: 0.20;
  - DIO1 against the rigid vias at y 20.55: 0.20 / 0.27.

## 6. Proposed decisions (for R8_DECISIONS; each from the plan, the requirements and the measurements)

| # | Proposal | Basis |
|---|---|---|
| P1 | RF interface resistors at the MCU end, in one row at y 29.5: R315 (22.6, 29.5, 90), R310 (24.1, 29.5, −90), R313 (25.1, 29.5, 90); R306 at (18.8, 29.6, 90) | F10 / D17: 6.04 mm from U1 (R306 5.94). SERIES / D4: nearer U1 than the module by 0.57 (R313), 1.00 (R310), 1.61 (R315) and 0.92 mm (R306), centre to centre. On straight lanes |
| P2 | Strip small parts nudged clear of the fence row: R305 0.13 mm aft (y 22.32), C300 0.08 mm aft (y 22.54), R312 to (25.8, 7.15) under the RXEN lane | D16 openings ≤ 2.7 mm need GND vias between the GNSS lanes, and the R7 pads sat 0.2 mm from y 23.3. None is a D15 rigid part. U30's courtyard and the rigid via (11.975, 21.575) bound the moves |
| P3 | TP71 (camera eFuse output, a D17 restricted part) leaves the seed's (38.4, 23.9), which was 1.79 mm from FB31. It goes to (33.6, 50.0) B until step 4 re-places the camera supply block | F10. A search found no legal bottom spot nearer the CAM_INPUT_LIMITED node except (30.8, 40.8), which would block the CAM dive corridor (F-4). U7 stays (FB31–U7 5.16 mm) |
| P4 | Fence row (D16) as in §4, with 0.5 / 0.3 mm vias | The checked geometry |
| P5 | The aft trio steps 0.4 mm east inside the strip mouth, and the trio's module-end corners are square | A 1.0 mm fence slot left open below y 23.3 is a GND finger that no via may stitch, because strip_gnd is rigid. A 45° corner after the 45° step is a route_check staircase |
| P6 | SCK passes the rigid via (23.8, 17.7) on its east side | A west pass makes a removable local bump (route_check). D11 keeps the rigid via, so no strip_gnd re-baseline is needed |
| P7 | J2 (TC2030) moves to the west edge, (2.35, 42.75), rotation −90. R32 / LED1 go in a row at y 41.8 and R33 / LED2 in a row at y 44.0 | D3 primary: the seed's J2 (9.5, 42.6) lies across both LED lanes, and J3 / R8 / U1 leave no other spot. Courtyards are clear, DRC 0, and the left tab window is 48.5–117.5 |
| P8 | Keep R7's limiter DC copper verbatim and carry its two detour entries (D11 fallback), or amend D10 (F-3) | Geometry: no redraw can pass the detour test |
| P9 | Spike tools save with `pcbnew.SaveBoard(path, board, True)` and copy the project files (F-6) | Measured pitfall |

## 7. Findings for the orchestrator

- **F-1 Fill noise without an F.Cu power pour.** If the board has no non-GND F.Cu pour at all, a native refill moves
  GND_F's boundary by a few µm. Then 15 of 744 `strip_gcpw` samples change by 0.01–0.02 mm, 4 of them inside 0.30 mm of
  a line.
  - Any F.Cu power pour present avoids it, and R8 will have them. This spike kept R7's `R6_BAT_IN_crossbar_F` as a
    stand-in.
  - The digest is exact otherwise. Expect the same sensitivity in step 5 if the F.Cu pours are rebuilt in stages.
- **F-2 The plan's 0.5–0.6 mm pitch is not achievable everywhere.** The rigid strip GND vias (20, 19), (23.8, 17.7) and
  (23.2, 14.67) bound the module gap: 6 lanes fit only at 0.5 mm, with SCK east of the (23.8, 17.7) via.
  - (23.8, 17.7) and (23.2, 14.67) were R7's GND partners for its NSS hop. They now only constrain the lanes.
  - No re-baseline was needed (P6). Note it if a later step wants more margin.
- **F-3 D11's limiter redraw cannot clear the two detours.** U30_KEEPOUT (F.Cu / In1, y 11.2–18.6) and the 0.3 mm pad
  gaps force the GNSS_LNA_EN and GNSS_VCC_RF vias south of U30's pad row (y ≤ 8.9). Best possible copper:
  - LNA_EN 6.32 mm against a 3.72 mm MST (1.70×);
  - VCC_RF 5.05 mm against 2.61 mm (1.93×).

  Both are above route_check's 1.6× and 2 mm limits. This is a calculation from pad and keep-out coordinates
  (**Inference**, not drawn). R7's copper gives 2.00× and 2.37×. D10 does not count a via keep-out as a hard keep-out.
  - Owner choice: the D11 fallback (two allowlist entries, P8), or a D10 amendment for layer changes from a pad whose
    only layer is closed to vias.
- **F-4 The east face is too crowded for the camera status lines on F.Cu.** CAM_FAULT_N and CAM_PWR_EN (pins 41 / 42,
  D3) sit between NRST and DIO1. U12's pad 8 (x 33.7) bounds NRST at x 33.4, so DIO1 and NRST are 0.55 mm apart and no
  F.Cu lane fits between them.
  - Recommendation: CAM_FAULT_N and CAM_PWR_EN dive inward under U1 (F.Cu stub into the body, via, B.Cu). The seed's
    bottom side is free at x 27.8–31.1, y 37.4–46.6.
  - Pins 48–50 (VCAP1, VSS, VDD) also dive inward: NSS runs 0.2 mm from their pad ends.
  - USB_FAULT_N (pin 87, between the LED pins) also dives inward. USB / SWD copper keeps ≥ 5 mm from R306's courtyard,
    which means y ≥ 35.52 across x 13.3–24.3.
  - These are interfaces for spike (a), camera, status and usb_swd.
- **F-5 The seed's camera supply block breaks its own rules.** Besides TP71's F10 break, check_r8 and DRC show TP 1.0 mm
  clearances (TP72 / TP73 / TP75), the C70 / R74 courtyards, and the C93 / C100 bypass distances to U12. Step 4 re-places
  this block. U7 itself is legal with P1.
- **F-6 Saving to another folder rewrites the project file.** `board.Save()` to a path in another folder rewrote
  `m3.kicad_pro` with KiCad's defaults (clearance 0.2, no minimum). The next load then filled and checked with the wrong
  rules, which showed up as a false `strip_gcpw` drift and false DRC clearances.
  - Any r8 script that writes a board elsewhere must use `SaveBoard(..., aSkipSettings=True)` and keep the project
    files.
- **F-7 Two step-1 rules conflict.** check_r8 `inner_signal` (D20: no In2 signal track) fails on the rigid CH1 block's
  own In2 ARM1_SENSE link (3.4 mm, D9 / D15, plan_partial §6). Spike (c) or the orchestrator must settle it.
- **F-8 Status cluster fallback avoided.** D3's LED fallback would put CAM_UART_OE on PE14 (pin 44), inside the crowded
  east-face escape. The primary west-edge placement is legal with P7, so the fallback is not needed. J2's move lengthens
  SWD lanes; the usb_swd family routes them, and its legends follow in r8_post.

## 8. What was not done

- **Not routed here:**
  - the camera status lines, SWD to the moved J2, USB_FAULT_N's dive;
  - every other family.
- **Not tested here:**
  - the limiter redraw (F-3 is calculated);
  - silkscreen beyond the spike's own designators (board legends stay at R7 positions until r8_post);
  - the field solve and S21 (rigid strip, unchanged digests);
  - any bench measurement.
