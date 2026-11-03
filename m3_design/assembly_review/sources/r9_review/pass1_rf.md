# R9 pass 1: RF layout, interface buses and coexistence review

Independent, read-only review, 2026-10-25. Dimension: RF.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51`, hashed before and after this review: unchanged.
- **Other inputs:**
  - netlist `schematic.net.xml` `8b0e04ea…`;
  - DRU `m3.kicad_dru` `ea77b791…`;
  - pin table `sources/r8_design/pin_table.tsv` `bd4687a8…`;
  - `tools/check_r9.py` `c38ad9a0…`, `tools/gcpw_solve.py` `fab2eef0…`, `m3_design/r9_rf.py` `eb468064…`,
    `m3_design/r9_route_rf_if.py` `8d6f85aa…`.
- **`git status --porcelain` digest:** `a142894c…`, identical before and after (including across a full
  `tools/check.sh` run).
- **Comparison boards:** R7 (`git show 431025d`, `c872a3d3…`) and R8 (`git show 9c8179b`, `cc044ea0…`). Both were
  copied to the session scratchpad and deleted afterwards.

**Scope:**

- the regenerated RF strip: congruence with R7, the GCPW, stitching and fence, keep-outs, chain order, and the limiter;
- the interface buses from U1;
- F10's separations and the coexistence paths;
- the radio-to-pyro distance;
- the reset states of the radio and GNSS lines;
- the RF parts of the records.

Coordinates are KiCad mm, with y = 0 at the aft (SMA) edge and +y forward. For a line run from the jack to the module,
"east" is +x. **Inference** marks anything not measured and not taken from a maker document.

## 1. Summary

**No Critical and no Major findings. There are three Minor findings: two worth fixing, and one worth fixing in the
gate's evidence.**

**The RF copper is sound and congruent with R7 where the plan says it is:**

- **Chain parts:** every one sits at R7's place in its jack's frame, except the two recorded deviations (D30 turned,
  C303 at the bias node).
- **Launches:** equal to R7's J31 (XOR 0.0 mm²).
- **Line samples:** every one outside the declared windows has F.Cu GND at 0.26–0.29 mm on both sides (0.31–0.32 mm at
  the two bend samples), over unbroken In1. gcpw_solve gives 50.17–51.08 Ω, inside 50 ± 2.5.
- **Windows:** this review also solved the window sections, where a coplanar ground opens to about 1.3 mm beside
  L30 / C303 / R304 and R316. They stay at or below 52.7 Ω, the microstrip limit for W 0.30 over 0.203 mm.
- **Stitching, fence, keep-outs, chain order, the limiter (no detour) and the separations:** all hold.
- **Interface lanes:** every one is on F.Cu, with no via, over In1 GND.
- **Netlist:** identical to R8 on all 32 RF-family nets, so R8 pass 4's reset-state analysis carries over.
- **Radio to pyro:** 46.13 mm, and the owner-required immunity test is in ORDERING §5 and F10.

**The previous pass's RF findings are closed in R9's records (§2).**

**Findings:**

- **R9P1-RF-01 (Minor, worth fixing).** The radio module's three ground pins lost R7's pin-adjacent GND vias. The copper
  path from U31.2 / U31.7 / U31.16 to the nearest via is 1.15 / 1.12 / 1.05 mm on R9, against R7 / R8's qualified 0.20
  / 0.35 / 0.35 mm.
  - U31.7 is the only ground beside the antenna pin. The patch next to it is now the strip's farthest GND copper from a
    via: 3.10 mm, where R7 / R8 had 2.12 mm.
  - No R9 rule measures this.
  - The fix is three GND vias at R7's spots in U31's frame, and they are legal on this board.
- **R9P1-RF-02 (Minor, worth fixing).** The records swap the sides of the R-7 stitching gaps.
  - F10 says "2.38 / 1.75 mm on the GNSS west / east sides". In fact east is 2.38 and west 1.75. The radio's 2.405 mm
    is on the west side, not the east as the step-4 handoff says.
  - ORDERING §4 still says each shunt joins "the series pad". C303 now joins at the bias-tap node.
- **R9P1-RF-03 (Minor, worth fixing; gate evidence, overlaps the gate-integrity dimension).** R-5's attribution of
  window samples to parts changes from run to run, and in this review the radio's split changed too (D-S10-18 says it
  is stable).
  - The cause is that `check_r9.chain_parts` returns a Python `set`, iterated in a hash-seed-dependent order. It is not
    an Inference.
  - The verdict and the totals do not change.

## 2. Previous pass in this dimension: closure

The last RF pass was R8 pass 4 (`sources/r8_review/pass4_rf.md`). R8 fix pass 4 fixed both findings
(`docs/R8_VALIDATION.md` l. 345–346), and R9's ORDERING carries both fixes, re-measured on R9.

| Previous finding | Disposition | On `fc3d5b34…` |
|---|---|---|
| R8P4-RF-01 (Minor, worth fixing): the coexistence step could not see a steady in-band spur; the radio crystal's harmonics and UBX-MON-SPAN were missing | Fixed in R8 fix pass 4 (records) | **Closed.** ORDERING §5 (l. 164) names the HSE's 1575.000 / 1175.000 MHz and the 32 MHz × 37 = 1184.000 MHz and × 49 = 1568.000 MHz harmonics. It also requires (1) UBX-MON-SPAN on both blocks in every condition with max hold, (2) a radio-asleep or reset condition against RX, and (3) a reference receiver, with CFG-ITFM optional. MAX-F10S IM §4.2.3 is cited. |
| R8P4-RF-02 (Minor, not worth fixing): U8's distances were given for the whole camera supply | Fixed in R8 fix pass 4 (records) | **Closed and re-measured for R9.** ORDERING §5 gives U8 / L3 17.3 / 21.5 mm from U31 and 26.9 / 28.8 mm from U30, U7 13.4 / 20.0 mm, and U1 / Y1 16.1 / 26.4 mm and 15.5 / 25.4 mm. This review measured, courtyard to courtyard: U8–U31 17.35, L3–U31 21.49, U8–U30 26.89, L3–U30 28.82, U7 13.41 / 20.04, U1 16.06 / 15.46, Y1 26.43 / 25.36 mm. All match. |

**R8 pass 4's observations, re-checked on R9:**

| R8 pass 4 observation | On R9 |
|---|---|
| In1 under RADIO_NRST at U1's east face | Still present: 18 samples, all on the +0.2 mm side, at (32.9–33.15, 44.2), inside a via antipad. The lane centre is covered. |
| F10 fast-line margin, R306–USB_DM | Now 5.005 mm (R8 5.075). Observation O1. |
| Thermal-spoke GND pads (the house rule) | Unchanged: C300.2, C301.2, C302.2, C310.2–C312.2, R311.2, R312.2. |
| LNA_EN during a GNSS reset | Same circuit, same remark. |
| The R8 fence-via remarks (R301.2 0.18 mm, R305.2 0.155 mm) | No longer apply: the geometry is new. The nearest foreign item to a fence via is 0.21 mm (lanes; §3.4). |

## 3. Measurements

### 3.1 Gate and tools, run in this review

- **`NUMPY_PY=…/cfd/venv/bin/python3 tools/check.sh`:** exit 0 in 203 s.
  - DRC 0 at every severity, unconnected 0, parity 0, ERC 0.
  - check_r9 OK on every rule, R-1 … R-13 included.
  - route_check r9: 0 failing, 0 allowlisted, 0 leftovers.
  - actuators OK.
  - The repository's status digest and the board SHA were unchanged afterwards.
- **`check_r9.py --only R-1…R-13,K-contract,K-copper`:** all OK.
- **`python -m unittest test_r9_rf`:** 16 OK.
- **`gcpw_solve.py --validate`:** coated 49.959 Ω (pass 2 50.3), bare 51.995 (52.2), launch 48.790 (49.0). OK within 1 Ω.

### 3.2 RF lines: geometry and impedance

Both lines are W 0.30 mm on F.Cu.

- **GNSS:** J30 (13.59, 0) → (13.59, 2.3 … 7.13) → the R304 jog to x 14.45 → U30.11 (14.45, 9.3). Path from the jack pad
  end to the module pad edge: 4.85 mm, two bends.
- **Radio:** J31 (32.29, 0) → (32.29, 2.3 … 7.6) → the R316 jog to x 33.15 → U31.6 (33.15, 9.05). Path: 4.75 mm, two
  bends.
- Both agree with check_r9 R-6.

**Independent sampler (`rfline.py`):** every 0.025 mm along every RF track, with F.Cu copper scanned at 0.005 mm on
each side (GND and any foreign net told apart) and In1 GND checked at the centre, ±0.15, ±0.45 and ±0.70 mm.

| Section | GND gaps (left / right) | In1 |
|---|---|---|
| GNSS y 4.725–5.725, ESD window included | 0.26–0.29 mm | full ±0.70 |
| GNSS y 5.75–6.455: bias tap (L30.2 on the line) and the C303 stub T | west 0.52 to L30.1 (its own cold pad); east open about 1.25–1.31 | full |
| GNSS y 6.48–7.13: L30 to R304.1 | west 0.32–0.39; east open (no GND within 2 mm between C303.1 and R304.2) | full |
| GNSS_RF_IN y 7.655–8.13, before the U30.11 entry | 0.26–0.30 | full |
| Radio y 4.725–7.075 | 0.26–0.30 | full |
| Radio y 7.1–8.3: R316 / C313 / C314 T and the U31.6 entry | 1.1–1.3, then 0.55 at the pad entry | full |
| Launch (pad to y 4.6) | In1 cut out by design (x ±0.9, y 0–4.6), In2 present | — |

**Comparison with R7:** the R7 board, sampled the same way, has the same windows. In R7 the GNSS line's west side was
open from y 6.5 to 7.13 (C303 sat west in the pi row), where R9's east side is open. R9's GNSS_RF_IN line before
U30.11 is 0.9 mm shorter (U30 moved aft, D-S3-04).

**Z0 from `tools/gcpw_solve.py`** (coated, over In1; this review's solves):

| Gaps (mm) | Z0 (Ω) | Where |
|---|---|---|
| 0.26 / 0.26 | 50.165 | most line samples |
| 0.28 / 0.28 | 50.514 | most line samples |
| 0.29 / 0.32 | 50.867 | bend samples |
| 0.38 / 0.38 | 51.615 | stub and T edges |
| 0.32 / 1.25 | 51.829 | GNSS east void at C303 |
| 0.39 / 2.5 | 52.156 | GNSS y 6.6–7.1 |
| 1.25 / 1.29 | 52.631 | radio T, GNSS_RF_IN at R304.2 |
| 2.5 / 2.5 | 52.655 | microstrip limit |

So every section that is not a part pad lies within 50.2–52.7 Ω. The gate's 79 line samples, outside the windows, give
50.16–51.08 Ω (`requalify_r9.json` `rf.gcpw`).

The windows are where R7's were. The cascade's line value of 50.34 Ω slightly understates those 0.4–1.4 mm sections
(about +2 Ω). Effect on |S11| at 1.6 GHz: about 0.003 (Inference: |Γ| ≈ 0.02 over βl ≈ 0.08 rad). So D-S10-02's
estimate (RL ≥ 22.6 dB) stands as an Inference.

### 3.3 Launch congruence

- **check_r9 R-4:** both jacks have one In1-only cut-out at x ±0.9, y 0–4.6, and In2 GND under it grown 0.3 mm (0
  missing). The eight vias are at the qualified spots (offsets ≤ 0.02 mm, R7's built y 3.58). The pad is 0.301 mm from
  F.Cu GND.
- **`rf.launch`:** window copper XOR against R7's J31 is 0.0 mm² for both jacks, and J30 = J31.
- **Transition:** the 0.2 mm of line over the cut-out (y 4.4–4.6) is R7's.

### 3.4 Stitching, fence and strip ground

**Stitching beside the lines** (check_r9's own path and `beside()` rule, with sides named by compass).

GNSS:

- East vias at (14.59, 4.8), (15.34, 6.18) and (16.25, 7.7), the last beyond the jog. Largest east gap **2.38 mm**
  (s 3.88 → 6.26).
- West vias at (12.29, 5.15) and (12.8, 6.9), the latter counted on two segments. Largest west gap **1.75 mm**.

Radio:

- East vias at (33.54, 5.65), (33.68, 6.3) and (33.14, 6.75), plus the jog's (33.14, 6.75) / (33.54, 5.65). Largest
  east gap **1.70 mm**.
- West vias at (31.44, 5.65), (30.95, 6.09) and (31.44, 6.75), then none until the U31.6 pad edge (y 8.295). Largest
  west gap **2.405 mm**.

check_r9 calls +d "left". For a path run in +y on KiCad's y-down canvas, that is east. The gate evidence
(GNSS_left 2.38, RADIO_left 1.70) agrees with the figures above. The records name the sides the other way round:
R9P1-RF-02.

**Fence (y 22.2):**

- 24 GND vias at x 1.95 … 44.65 (0.5 / 0.3 mm), every one with pads on all four layers.
- Gaps 1.3–1.95 mm, except four openings:

  | Opening | Width | Lanes |
  |---|---|---|
  | 17.25–19.4 | 2.15 | GNSS_RESET_N |
  | 20.95–23.05 | 2.10 | RXEN, BUSY, MISO_MCU |
  | 23.05–25.2 | 2.15 | MOSI, NSS, SCK |
  | 38.8–41.3 | 2.50 | NRST |

- 14 crossings, all on F.Cu: the ten lanes above, TXD_MCU, RXD, TP_MCU, DIO1 and the FB30 / FB31 3V3 feeds. Lane to
  fence-via edge gaps are 0.21–0.71 mm.
- No non-GND via within 1 mm of the row.

**Strip ground:**

- **GND reach** (route_check raster): F.Cu 3.10 mm, B.Cu 3.57 mm (≤ 4.0).
- **Coverage:** F.Cu 77.8 %, In1 95.1 %, In2 96.7 %, B.Cu 92.9 % (R7 76.7 / 95.1 / 96.6 / 92.0).
- **In1:** GND across the strip except the two launch cut-outs.
- **In2:** strip GND to y ≈ 23.2; the 3V3 region starts at y ≈ 23.6.
- **3V3 feed vias:** FB30's at (16.2, 24.2), with its nearest GND via 1.41 mm away; FB31's at (34.5, 24.3), 1.30 mm
  away.

**Ground at the module pads** (through-copper path to the nearest GND via, F.Cu raster, the metric of R7 pass 3 §3.6):

| Pad | R7 (qualified, pass 3 §3.6) / R8 (rigid copy) | R9 |
|---|---|---|
| U31.2 (radio GND) | 0.20 | **1.154** |
| U31.7 (radio GND beside ANT) | 0.35 | **1.116** |
| U31.16 (radio GND) | 0.35 | **1.05** |
| C310.2 (radio bulk, thermal pad) | 0.30 | 0.941 |
| C311.2 / C312.2 | 1.004 / 1.024 | 0.15 / 0.50 |
| U30.1 / U30.10 / U30.12 (GNSS GND) | 0.85 / 0.60 / 0.75 | 0.20 / 0.20 / 0.55 |
| C300.2 / C301.2 | 1.649 / 1.066 | 0.604 / 0.25 |

The GNSS side and the small decoupling capacitors improved. The radio module's three ground pins, which are its only
ground connections (EBYTE manual ch. 3: pins 2, 7, 16), regressed three- to six-fold.

- **Where R7's vias were:** R7 / R8 had a dedicated via behind each of those pins, at U31-relative (+3.74, +1.27),
  (+1.27, −3.60) and (−2.54, +3.60). R7 pass 3 §3.1 records them as the joints of the module ground pins.
- **What replaced them:** R9's regular 2.5 mm grid under U31 has its nearest vias 2.05–2.19 mm from the pin centres.
- **The farthest strip copper:** the F.Cu patch west of RADIO_RF's last 0.7 mm, between R316 / C313 and U31.7, is now
  the strip's farthest GND copper from a via: 3.10 mm at (32.28, 8.13). The same module-relative spot measures 2.12 mm
  on R7 and R8.
- **The thinnest R-7 margin:** the radio's west stitching gap (2.405 mm) ends at this pad.
- **No rule covers it:** R-7's `rf_grounds` covers only the chain's RF ground pads (D30.2 0.23, D31.2 0.16, C303.2
  0.05, C305.2 0.06, C313.2 / C314.2 0.16 mm), and R-8 only samples fill. The requalification list
  (survey_constraints §8.4 items 4–5) left out pass 3's module-pad table. Finding R9P1-RF-01.

### 3.5 Keep-outs and per-layer nets

- **R-8:** U30_KEEPOUT (F.Cu and In1, x 6.1–16.2, y 10.35–17.75) and U31_KEEPOUT (F.Cu and In1 for the pad-ring
  interior; In2 and B.Cu for the 10 × 10 body) leave 0 mm² uncovered. GND fill is present at every 0.2 mm sample, and
  no non-GND track or via lies inside.
- **Vias under the modules:** all are GND (14 under U30, 12 under U31) and plugged (ORDERING §3).
- **R-2:** In1 and In2 are GND only in the strip. B.Cu carries GND, the limiter nets and RADIO_TXEN (22.719 mm, at
  R8's 22.72).
- **Module approaches:** the radio lanes enter U31's west pads from outside the pad ring. The TXEN B.Cu loop runs at
  x 25.25, 0.29 mm outside the body box.
- **Against the makers' guidance:**
  - u-blox IM §4.4 p. 67: "ground the area below the module, on the top and second layer. Avoid signal lines crossing
    below the module at these two layers" — met.
  - EBYTE §4.1: no high-frequency wiring under the module — met.

### 3.6 Chain order and the limiter

**R-9:**

- ESD 0.795 mm (path) from each jack pad end.
- C302 0.925 mm from L30's cold pad.
- Shunt stubs 0.94 mm.
- Order jack → ESD → bias tap → pi → module.
- The radio chain is R7's exactly.
- D30 is bidirectional, so turning it is electrically neutral (D-S4-02).
- C303 (DNP) sits at the bias node, its stub joining the line at L30.2's pad.

**Limiter:**

- **Placement:** on B.Cu under U30. VCC_RF, ANT_DC and LNA_EN change layer at V1 (10.4, 7.4), V3 (11.3, 7.4) and V2
  (12.25, 7.4).
- **GND partners:** 0.695, 0.814 and 0.743 mm away (≤ 1.5, AGENTS §3).
- **TXEN vias:** (29.34, 7.8) and (31.88, 20.15), with partners 0.721 mm away.
- **No detour or allowlist entry:** route_check r9 reports only information instances on RF-family nets (the TXEN loop
  u-turn, RXEN / RESET_N extra bends, the NRST u-turn, pad entries).
- **Q30's drain lead:** 0.40 mm. Thermal: an Inference, with a bench test (D-S4-03, ORDERING §5).

### 3.7 Interface buses U1 → strip

`iface.py` and `segs.py` cover every RADIO_* / GNSS_* track and via except the RF lines.

| Net | Copper | Vias |
|---|---|---|
| RADIO_SCK_MCU / SCK | 13.73 + 14.17 mm F.Cu (R313 at the MCU end) | 0 |
| RADIO_MOSI_MCU / MOSI | 8.13 + 17.09 mm F.Cu (R315 at the MCU end) | 0 |
| RADIO_MISO / MISO_MCU | 1.48 + 25.95 mm F.Cu (R314 at the radio end) | 0 |
| RADIO_NSS / BUSY / RXEN / DIO1 / NRST | 29.73 / 30.06 / 36.89 / 26.49 / 45.76 mm F.Cu | 0 |
| GNSS_TXD / TXD_MCU | 2.13 + 20.37 mm F.Cu | 0 |
| GNSS_RXD_MCU / RXD | 8.54 + 14.37 mm F.Cu (R306 at the MCU end) | 0 |
| GNSS_TIMEPULSE / TP_MCU | 2.13 + 21.94 mm F.Cu (R307 at the module end) | 0 |
| GNSS_RESET_N / SAFEBOOT_N | 20.40 / 4.87 mm F.Cu | 0 |
| RADIO_TXEN | 2.45 F.Cu + 22.72 B.Cu | 2 |
| GNSS_LNA_EN / VCC_RF / ANT_DC | 1.90 F + 2.40 B / 2.21 F + 2.55 B / 2.33 F + 1.75 B | 1 / 1 / 1 |

**Reference:**

- In1 under every F.Cu segment (centre and ±(w/2 + 0.1) every 0.05 mm) is missing only inside layer-change antipads
  and at two edge spots: NRST +0.2 mm at (32.9–33.15, 44.2), and NSS −0.2 mm at (23.25, 27.45–27.7) by R310's 3V3 via.
- Both lane centres are covered.

**Coexistence geometry** (R-11 and `requalify_r9.json`):

- Radio lines to U30's body: RXEN 5.2, BUSY 5.7, MISO_MCU 6.2, MOSI 7.3, NSS 7.75, SCK 8.35 mm. These are ≥ 5.0, and
  ≥ 6.0 for SPI.
- Radio lines to GNSS RF copper ≥ 6.16 mm.

**Parallel F.Cu runs at ≤ 0.36 mm edge gap** (`xtalk.py`; observation O2):

| Pair | Gap | Parallel length |
|---|---|---|
| BUSY / RXEN | 0.30 | 22.9 mm |
| BUSY / MISO_MCU | 0.30 | 21.6 mm |
| NSS / SCK_MCU | 0.29–0.30 | 10.8 mm |
| MOSI / NSS | 0.25 | 9.2 mm |
| DIO1 / SCK_MCU | 0.30 | 8.9 mm |
| RESET_N / TP_MCU | 0.30 | 8.35 mm |
| RXD / TP_MCU | 0.25 | 7.7 mm |
| CAM_MCU_TX / RADIO_NRST | 0.30 | 6.25 mm |

R8 pass 4 had BUSY at 28.7 / 27.6 mm and no SCK neighbour longer than 2.0 mm.

### 3.8 F10 separations and coexistence

**F10 separations (check_r9 R-10, re-run in `dist.py`):**

- Nearest RF part to a restricted part: R313–U1 6.04 mm. The next are R310 / R315 6.24 and R306 6.29 mm (≥ 5.94, hard
  X9).
- Nearest fast-line copper: R306–USB_DM 5.005 mm (≥ 5.0; observation O1).
- The modules:
  - U30 ≥ 15.46 mm from U1;
  - U31 ≥ 13.38 mm from C73;
  - U2 / L1 ≥ 49.99 mm from both modules;
  - U8 / L3 26.89 / 28.82 mm from U30 and 17.35 / 21.49 mm from U31.
- u-blox IM §4.4 p. 67 ("Keep at least a 5 mm distance to any RF component") is met: no restricted part or fast line
  comes within 5 mm.

**Other aggressors near the strip:**

- J3 (USB-C) 8.43 mm and U10 8.79 mm from U30.
- LS120 (MLT-5020 magnetic buzzer, driven from 3V3 at 4 kHz by Q123): **2.71 mm** from U31's courtyard and 8.91 mm
  from U30's.
  - The buzzer drive copper is 3.9–5.9 mm from U31_KEEPOUT. LS120.3, the unconnected mechanical pad, is the nearest at
    3.9 mm; BUZZ_G and BUZZ_OUT come at 5.45 and 5.67 mm.
  - **RADIO_DIO1's diagonal (27.75, 33.0)–(33.15, 27.6) passes 0.36 mm from the corner of LS120.2 (BUZZ_OUT), the
    switched coil node** (observation O3).
  - D-S7-14 and C17 record the buzzer as an Inference, and ORDERING §5's coexistence step is repeated with the buzzer
    sounding.

**Coupling paths otherwise as R7 / R8:**

- RF line to RF line 15.46 mm (R7 15.45); jacks 18.7 mm apart; module courtyards 7.67 mm apart.
- Separate ferrites FB30 / FB31 with local bulk. The GNSS VCC path is 0.088 Ω (≤ 0.2).
- Decoupling distances to the module VCC pins: C311 1.97, C312 2.191, C310 3.639 mm (U31.1); C301 2.13, C300 2.556 mm
  (U30.7 / 8).
- The clock-harmonic list (HSE × 63, × 47; radio crystal × 37, × 49) is in ORDERING §5 (§2).

### 3.9 Radio to pyro

- **check_r9 R-13:** 46.13 mm (U31 courtyard to Q124.5, PYRO1_OUT).
- **Independent point sampling (`pyrodist.py`):** U31 courtyard to armed copper 46.12 mm; J31 courtyard 61.84 mm; radio
  RF copper 58.94 mm. Other CH1 copper: U31 to R170.2 (ARM1_SENSE_MCU) 26.89 mm.
- **Radio interface lanes:** they come within 2.63 mm of R170.2 at U1's east face. That is the MCU-side sense resistor,
  which P-7 and P-8 cover, and it is 24.0 mm from armed copper.
- **Records:** F10's R9 clause and ORDERING §5 both make the keyed-radio immunity test a required gate before any
  flight (owner decision 3).

### 3.10 Reset states

The netlist nodes of all 32 RADIO_* / GNSS_* / 3V3_GNSS / 3V3_RADIO nets are identical to R8's (`9c8179b`), and so are
the part values:

- R311 2 k NRST → GND;
- R312 100 k RXEN → GND;
- R310 100 k NSS → 3V3;
- R313 / R315 / R314 33 Ω;
- R305 / R306 220 Ω;
- R307 1 k;
- TXEN = U31.9 + DIO2 (U31.19);
- RESET_N to PD14 with no capacitor;
- SAFEBOOT_N on TP30 only.

The U1 map equals R8's pin table (check_r9 K-contract). So R8 pass 4 §4.7's datasheet analysis carries over: SX1262 DS
Rev 1.2 Table 8-3 (in reset, DIO1–3 PD, BUSY PU, SPI high-Z) and V_IL_N 0.2·VBAT; MAX-F10S RESET_N ≥ 1 ms with a 7–13 kΩ
internal pull-up. With the MCU in reset, NRST is held low (about 0.13 V by R311 against 50 kΩ), RXEN low, TXEN low and
NSS high.

**R9 placement:** the pull-downs sit at the radio end of their lanes (R311.1 at (37.75, 14.0) on NRST beside U31.3;
R312.1 at (26.55, 7.58) on RXEN, 1.6 mm from U31.10). R310 sits at the MCU end, where its purpose (USART3 idle on PB11,
F10) needs it. The ORDERING §5 probe coordinates for R311.1, R312.1 and C304 (9.6, 13.97) match the board.

### 3.11 Records checked

- **REQUIREMENTS F10 R9 clause:** every figure matches the board but the stitching sides (R9P1-RF-02).
- **M3_R9 "RF strip" and its requalification line:** all match.
- **R9_VALIDATION "RF (F10)" table:** all match. The radio and GNSS gap pairs are listed in different side orders,
  with no sides named.
- **ORDERING §3:** impedance, stackup and via plugging match.
- **ORDERING §4:** the DNP shunt text says "to the series pad", which no longer holds for C303 (R9P1-RF-02). The
  jack-to-ESD 0.5 mm matches.
- **ORDERING §5:** RF bench items, coordinates and aggressor distances match.
- **STATUS R9 section and AGENTS §1:** the RF line matches.

## 4. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R9P1-RF-01 | Minor (worth fixing) | r9_plan §1 graft "RF chains and modules congruent with R7"; R7 pass 3 §3.6 (module ground pads' copper path to a via); EBYTE manual §4.1 ("the module must be reliably grounded"); u-blox IM §4.4 ("the ground plane around should be filled with GND vias") | **The radio module's three ground pins lost R7's pin-adjacent GND vias.** The copper path from U31.2 / U31.7 / U31.16 to the nearest via went from 0.20 / 0.35 / 0.35 mm (R7, R8) to 1.154 / 1.116 / 1.05 mm. These are the E22's only ground pins, and U31.7 is the one beside ANT. The patch west of RADIO_RF's final 0.7 mm became the strip's farthest GND copper from a via: 3.10 mm at (32.28, 8.13), against 2.12 mm on R7 / R8. No R9 rule measures module ground pins. | `padreach.py` and `modvias.py` on R7 / R8 / R9 (§3.4). R7's vias at (31.13, 10.4), (33.6, 15.27), (27.32, 17.6) (pass3_rf.md l. 89–90, 150–151). R9's nearest grid vias are (31.0, 11.0), (33.5, 16.0), (28.5, 21.0). E22 manual ch. 3 pin table. `r9_rf.GND_MODULE` has only partner and decoupling vias. Strip reach: route_check `gnd_reach` | Add R7's three module-frame vias to `r9_rf.GND_MODULE` (U31-relative, board axes, rot 180 as R7): (+3.74, +1.27), (+1.27, −3.60), (−2.54, +3.60), that is board (34.35, 15.27), (31.88, 10.40), (28.07, 17.60), 0.6 / 0.3 mm. This review checked the spots on `fc3d5b34…`: ≥ 1.06 mm from every via centre, ≥ 0.72 mm from foreign copper (U31.6 RF pad 0.72, U31.17 / U31.8 NC 0.72–0.75), rings 0.2–0.35 mm off their own pads' paste (check_r8.via_paste needs no overlap). Rebuild, then re-run `r9_rf_check`, `r9_ground_aid --check` and the gate. Optionally add a module-ground-pin reach row to R-7 (≤ R7's 0.35 mm). |
| R9P1-RF-02 | Minor (worth fixing) | Records match the board (AGENTS §2.5 / §3); REQUIREMENTS F10 | **The records name the sides of the R-7 stitching gaps the wrong way round.** F10's R9 clause says "2.38 / 1.75 mm on the GNSS west / east sides and 1.70 / 2.405 mm on the radio sides". Measured: GNSS east 2.38, west 1.75; radio east 1.70, **west 2.405** (the thinnest margin, ending at U31.7). `r9_step4_handoff.md` §5 says "radio east 2.41". R9_VALIDATION gives "GNSS 2.38 / 1.75, radio 2.405 / 1.70" with no sides, in opposite orders. Separately, ORDERING §4 still says each DNP shunt "joins its RF line through a 0.94 mm trace to the series pad". C303 now joins at the bias-tap node (L30.2), 0.95 mm before R304.1. | `stitch.py` (§3.4). check_r9 `beside()`: d = (p − a) × u, so +d ("left") is +x for a +y path. Gate `R-7` evidence GNSS_left 2.38, RADIO_left 1.70. ORDERING l. 84 | F10: "2.38 / 1.75 mm on the GNSS east / west sides and 2.405 / 1.70 mm on the radio west / east sides". R9_VALIDATION: name the sides. ORDERING §4: "…to the series pad (in R9, C303's trace joins the line at the bias-tap node)". Optionally rename the evidence keys to east / west in a later checker change. |
| R9P1-RF-03 | Minor (worth fixing; overlaps gate integrity) | Determinism of the gate's evidence (r9_plan §5); D-S10-18 | **R-5's attribution of window samples to parts is nondeterministic, and its cause is known.** `check_r9.chain_parts()` returns a `set` of designators. R-5 assigns a sample to the *first* part in that set with a pad within 0.3 mm, so where two parts' pads are both in reach (L30 / C303 / R304, R316 / C313) the owner depends on the per-process string-hash seed. This review's runs gave GNSS C303 12 / L30 24 / R304 36 / D30 2 and RADIO C313 12 / R316 34. The step-10 report gave GNSS 8 / 28 / 32 / 2 and RADIO C313 8 / R316 38. Totals are 286 every time, and the verdict does not change. D-S10-18 says the radio split is stable, and it is not. | `tools/check_r9.py` `chain_parts` (a set) and the attribution loop in `r5`. Three R-5 evidence dicts compared (`step10_evidence/gate/r9.json` and two runs of this review) | Iterate `sorted(chain_parts(ch))`, or assign each sample to the nearest pad. Re-pin check_r9's hash where the records bind it. |

## 5. Observations (no finding)

- **O1. F10 fast-line margin.** R306 to USB_DM (track at (11.95, 33.15)) is 5.005 mm, against a 5.0 mm limit (R8
  5.075 mm).
  - R306 is the GNSS RXD series resistor at the MCU end. It is an "RF part" by name only (D-S1-03), and the gate holds
    the margin on every build.
  - The owner's 98 mm option (reclassifying R306 / R310 / R313 / R315, C1) would remove the question.
- **O2. Parallel runs.**
  - SCK_MCU now runs 8.9 mm beside DIO1 and about 10.8 mm beside NSS at 0.29–0.30 mm, and MOSI runs 9.2 mm beside NSS
    at 0.25 mm. R8 kept SCK free of neighbours longer than 2 mm.
  - CAM_MCU_TX runs 6.25 mm beside RADIO_NRST at 0.30 mm.
  - Every victim is driven push-pull or held stiff while its aggressor toggles: DIO1 by the SX1262, NSS by PB11, NRST
    by PE9, or R311's 2 k in reset. NRST needs a sustained low (more than 100 µs) to act.
  - Estimated backward coupling, with lines electrically short (2·TD ≈ 0.1 ns against edges of 1 ns or more): a few
    millivolts (Inference). No action.
- **O3. Buzzer next to the radio.**
  - LS120's courtyard is 2.71 mm from U31's, and RADIO_DIO1 passes 0.36 mm from the corner of LS120.2 (BUZZ_OUT).
  - Coupling estimate, for a corner proximity of about 0.03 pF:
    - into the driven IRQ line, about 3 mV;
    - with the radio in reset, DIO1 is held only by the SX1262's 50 kΩ pull-down, and the glitch is limited by
      charge sharing to about 13 mV.
    - Both are Inference.
  - ORDERING §5 already repeats the coexistence test with the buzzer sounding. Naming DIO1's adjacency there would
    point an IRQ-glitch symptom at its cause.
- **O4. Widest fence opening.** The NRST opening, 38.8–41.3 (2.50 mm, one lane at x 40.6), is the widest. One fence via
  at about (39.8, 22.2) would make it ≤ 2.0 mm (0.45 mm to the lane). That is cosmetic: it is within R-7's 2.7 mm and
  far below λ/20.
- **O5. Window impedance.** Beside L30 / C303 / R304 and R316 the line runs with one or both coplanar grounds open. The
  solve gives ≤ 52.7 Ω (§3.2), R7 had the same windows (mirrored at C303), and R-5's windows behave as R7's did.
- **O6. Thermal reliefs.** The radio's bulk capacitor C310 has a thermal-relief GND pad, 0.94 mm of copper from a via
  (R7 0.30). That is the house thermal policy and harmless for a bulk part; C311 and C312 improved.

## 6. Inferences (not measured, or not from a primary source)

- **The RF effect of R9P1-RF-01.**
  - The F.Cu pour around U31's ground pins lies 0.2 mm over In1, and several vias sit 2.0–2.2 mm away. The added
    ground-return inductance is estimated at a few tenths of a nanohenry, roughly 1–2 Ω of reactance at 915 MHz.
  - That should be small for the 50 Ω match, but it departs from the qualified R7 module grounding.
- **The cascade's window correction** (§3.2) and the crosstalk and buzzer coupling estimates (O2, O3).
- **Unchanged from R8 pass 4:** spur levels, E22 NRST internal pull-up, and Q30's thermal bound (D-S4-03).

## 7. Sources

- **u-blox MAX-F10S Integration manual** UBXDOC-963802114-12892 R01, §4.4 "Layout" pp. 66–67: 5 mm to any RF
  component; GND stubs ended with a via; ground under the module on the top two layers; CPW with ground on layer 2; GND
  vias around the RF line.
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- **EBYTE E22-900MM22S user manual** (LCSC C5333985):
  - ch. 3 pin table (GND = pins 2, 7, 16; NC 4, 5, 8, 17; TXEN to DIO2);
  - §4.1 hardware design ("the module must be reliably grounded"; no high-frequency or power routing under the module);
  - §4.2 (32 MHz passive crystal).
  - https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
- **Semtech SX1261/2 DS Rev 1.2:** Table 8-3, Table 3-10, as verified in `sources/r8_review/pass4_rf.md` §4.7 (the
  netlist is unchanged).
- **Project records:**
  - `docs/REQUIREMENTS.md` F10;
  - `docs/M3_R9.md`;
  - `docs/R9_VALIDATION.md`;
  - `docs/ORDERING.md` §3–§5;
  - `AGENTS.md` §3;
  - `R9_DECISIONS.md` D-S1-04/05/19/22, D-S3-04, D-S4-01…08, D-S7-03/04/14, D-S8-19, D-S10-02/18;
  - `r9_step4_handoff.md`;
  - `survey_constraints.md` §8.4–8.5;
  - `sources/r7_review/pass2_rf.md` §3.6, `pass3_rf.md` §3.1 / §3.6;
  - `sources/r8_review/pass4_rf.md`;
  - `docs/R8_VALIDATION.md` l. 345–346.

## 8. Method (reproduction)

**Scripts.** All ran under KiCad 10.0.6's Python (read-only), from the session scratchpad (`r9review/rf/py/`), on a copy
of the board and on R7 / R8 from git:

- `dump_rf.py`: strip parts, pads, RF tracks.
- `rfline.py`: GCPW gap sampler with In1 / In2 checks, on R9 and R7.
- `stitch.py`: check_r9's path and `beside()`, sides by compass.
- `fence.py`: fence vias, gaps, crossings, edge gaps.
- `iface.py`, `segs.py`: lane copper, references, neighbours.
- `xtalk.py`: parallel runs.
- `dist.py`: separations, through `check_r8.rf_separation`.
- `pyrodist.py`: radio to pyro.
- `gndpads.py`, `padreach.py`, `modvias.py`, `reach.py`, `reach2.py`: ground at pads, GND reach (route_check raster), on
  R7 / R8 / R9.
- `viaspot.py`: legality of the three proposed via spots.
- `buzz.py`, `buzz2.py`: buzzer copper against the RF family.
- `zpairs.py`: gcpw_solve on the window gap pairs.

**Gate runs.** `tools/check.sh` (with `NUMPY_PY`), `check_r9 --only R-*`, `test_r9_rf` and `gcpw_solve --validate`, as
in §3.1.

**Netlist comparison.** RF-family nets in `schematic.net.xml`, compared with `git show 9c8179b:…schematic.net.xml`.

**Datasheets.** pdftotext of the u-blox IM and the EBYTE manual, each downloaded into its own scratch folder.

**Clean-up.** The scratch folder (board copies, downloads, scripts) and check.sh's temporary report folder were deleted
afterwards. Nothing in the repository was written but this report. The board SHA and the repository status digest are
unchanged.
