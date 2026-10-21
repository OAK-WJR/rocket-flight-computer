# R8 review pass 1: planes and return paths

Reviewer: independent, dimension "planes and return paths". Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987` (re-hashed before and after this review: unchanged;
`git status` unchanged by the runs). Read-only: nothing in the repository was edited except this file.

## Verdict

**0 Critical, 0 Major, 4 Minor.** The R8 planes are clean where it matters. In1 is one solid GND plane with no track and no
slot under any foreign critical track. In2 has no split under any critical B.Cu track except one: ARM1_SENSE, a DC sense
node, inside D47's U1-field exemption. Every critical layer change except A8 has a GND via within 1.5 mm. The crystal
sits in a stitched B.Cu GND guard with In1 GND above and no In2 copper. D63 and D64 were re-measured and are dispositioned
correctly. The four Minor items:
1. R7's C11 class (GND fingers 0.5 to 1.0 mm wide, which the gate doesn't stitch-check) is missing from R8's deviation
   list. The worst R8 piece is a 0.54 mm F.Cu sliver between two radio SPI lanes whose tip is 15.1 mm of copper from a
   GND via.
2. The reference audit covers only 24 of the 59 AGENTS §3 critical nets, so the ARM1_SENSE split crossing is not
   recorded.
3. The R8 records don't say that the In2 3V3 plane is the reference under U1 and under both sensors (R7 had 3V3A or no
   copper under the sensors).
4. The ground half of the 7.7 A servo loop has never been solved. Its narrowest point is the battery GND terminal J1.2,
   which joins the planes through thermal spokes only.

## Gates run (on the board as built)

| Run | Result |
|---|---|
| `tools/check.sh` | exit 0: DRC 0, unconnected 0, parity 0, ERC 0; metadata OK; silk OK; check_r8 OK; route_check r8 OK (0 failing, 3 allowlisted); check_actuators OK; fit OK |
| `m3_design/r8_ground_check.py --report` | all 14 gates OK; reach board p95 4.48 / max 9.65 mm (max at (0.25, 88.25)); outer pours p95 2.90 / max 5.89 mm; islands 18, the one weak island is D4.2's (F, 2.891 mm², 1 via) |
| `tools/route_check.py --profile r8` | OK; information: power_via_no_gnd 6 (C8) |
| `tools/reference_audit.py` | R6 set 47,769 samples, 5,525 unreferenced (11.57 %): own via 3,589, Y1 keep-out 1,710, other via 226 (matches D74 / M3_R8) |

My own scripts are listed at the end. They are read-only pcbnew scripts in the session scratchpad, which is deleted after
this review.

## 1. Previous findings in this dimension

This is the first R8 pass, so no earlier R8 planes finding exists. The R7 deviations that belong to this dimension were
checked against R8:

| R7 item | R8 status (measured on `429b6db4…`) |
|---|---|
| C2 return paths (603 R6 samples lost) | Superseded by D74's absolute audit. On the R6 and extended sets, no sample lies over a foreign fill, along a split or over a void. See finding 02 for the nets outside those sets. |
| C5 radio lines across In2 BAT_IN | **Closed.** Every RADIO_* interface line runs on F.Cu over In1 GND (no layer change). RADIO_TXEN's B.Cu run inside the strip lies over In2 GND for 21.8 mm. |
| C6 RADIO_NRST over an In2 track | **Closed.** No In2 signal track except D70's rigid 3.4 mm ARM1_SENSE link. |
| C8 SWCLK via 1.10 mm from Y1.3 | **Closed.** SWCLK is F.Cu only: 15.9 mm over In1 GND, no via. |
| C9 / C10 / C22 voids and stacking at In2 runs | **Closed.** No In2 runs. |
| C11 unstitched GND fingers 0.5–1.0 mm wide | **Open, not recorded for R8.** See finding 01. |
| C13 D30.2 / D31.2 solid to GND | Carried with the rigid strip (RF dimension). |
| C14 GND pieces on one via | **Closed** to P7 = 1, the D4.2 pocket (D63 / D68). Re-measured: 2.891 mm², one via at (9.0, 33.8), 0.85 mm from D4.2. U10.2 reaches the same via through a 0.2 mm B.Cu track. U10.2 also sits in the B.Cu GND pour, and its pin carries only quiescent current. |
| C20 forward-edge reach | Superseded by D62's pour cover: P11 p95 2.90 / max 5.89 mm, both within the plan's 3.5 / 7 mm. |
| D63 (P7 = 1), D64 (P9 / P10 floors) | **Properly dispositioned.** P9 / P10 measure 4.48 / 9.65 mm. The maximum is at the west edge (0.25, 88.25). There, F.Cu, In2 and B.Cu are all RAW_ACT (x 0.5–16.5, y 81.6–108), so In1 is the only GND layer and nothing needs stitching to it. No signal runs in that region. D64's cause matches the copper. |

## 2. In1

- **One outline**, 4,869.5 mm² of fill, with no In1 track (S16 = 0). It has 197 holes totalling 377 mm²: mounting holes,
  barrels and via antipads.
- **Holes larger than one antipad:**
  - J122.1's barrel merged with the tie hole: 18.3 mm², x 24.49–29.10, y 78.46–84.70.
  - The J121 / J124 barrels: 10.2–12.8 mm².
  - The SPI1 / IMU_CS four-via cluster at the bottom-side IMU: 2.95 mm², 2.71 × 1.70 mm, x 8.29–11.00, y 55.15–56.85.
    This is P3b's one "slot".
  - Ten two-via pairs of 1.44–1.62 mm².
- **No foreign critical track crosses any of these holes**, with one exception. The edge of RADIO_NRST (F.Cu, x 33.4)
  runs along the merged antipad of the 3V3 / CAM_MCU_RX via pair (33.40–34.50, 42.60–44.50) for 1.26 mm; its centre
  line is over the hole for only 0.14 mm. RADIO_NRST is a quasi-static reset line. Every other critical F.Cu track that
  enters a hole enters its own via's antipad.
- **The PYRO lines over the barrels:** PYRO1_BUS (1.85 mm), PYRO1_OUT (1.80 mm) and PYRO1_IGN (1.70 mm) of F.Cu lie over
  their own J124 / J121 barrel antipads. These are DC and pulse lines.

## 3. In2

| Region | Net | Fill mm² | Outlines |
|---|---|---:|---:|
| R8_GND_In2 | GND | 2,396.4 | 1 |
| R8_3V3_In2 | 3V3 | 1,512.4 | 1 |
| R8_RAW_ACT_In2_west / _j122 | RAW_ACT | 287.7 / 57.9 | 1 / 1 |
| R8_BAT_IN_In2 | BAT_IN | 505.6 | 1 |
| Y1_In2_keepout | (no fill) | x 18.9–26.8, y 46.3–50.95 | — |

- **Necks in the 3V3 region.** No neck under 1 mm cuts it: eroding by 0.5 mm leaves one 1,461.7 mm² core. Necks under
  2 mm split it into three lobes (562 / 143 / 131 mm²), at the crystal keep-out, at the U1 east side (x 31.4–35.3,
  y 42.6–48.4) and at the J2 / USB west edge. That is supply impedance, not a reference problem: U1's bypass capacitors
  sit 1.5–2.7 mm from its pins, and their GND pads are 0.78–1.09 mm from GND vias.
- **The south-west In2 GND pocket** (65.6 mm², x 0.8–12, y 108.4–117.5) joins the rest of In2 GND only through a 0.8 mm
  strip at x 11.2–12.1, y 100.3–108.4, between the RAW_ACT and BAT_IN islands. It is harmless: GND vias tie every In2 GND
  area to In1.
- **The In2 track** is D70's rigid ARM1_SENSE link at x 14.55, y 94.15–97.55. It leaves a 0.7 × 4.3 mm slot in In2 GND,
  and no B.Cu track crosses over the slot.
- **Split crossings on B.Cu, every signal net** (reference net changing along a track's centre line):
  - ARM1_SENSE: In2 3V3 → GND at (18.18, 53.9). See finding 02.
  - ACT_GATE: In2 GND → BAT_IN at (12.4, 107.16), and RAW_ACT → GND at (11.35, 107.16). This is the actuator P-FET gate,
    a slow switch between the two facing FETs.
  - BAT_SW_SOURCE / BAT_SW_RETURN: 1.9 / 2.5 mm over In2 BAT_IN. These are the DC harness lines of the external switch.
  - **None on F.Cu.**
- **Totals.** Signal B.Cu lies 245.1 mm over In2 GND, 215.3 mm over 3V3, 5.4 mm over BAT_IN and 2.4 mm over RAW_ACT; the
  remaining 51.0 mm are own antipads and the crystal keep-out. Signal F.Cu lies 969.4 mm over In1 GND; its remaining
  45.5 mm are antipads, the J30 / J31 launch cut-outs and the barrels.

## 4. Critical-signal references and layer changes

`refall.py` sampled every track of every route_check signal-critical net (classes rf, pyro, crystal, usb, spi and rfif:
59 nets) plus SWDIO, SWCLK and NRST. Samples were taken every 0.02 mm along the centre line and both copper edges,
against the adjacent plane, with B.Cu checked against In2.

- **F.Cu:** every critical net lies over In1 GND, except its own antipads and the intended launch cut-outs. GNSS_RF_ANT
  and RADIO_RF_ANT each have 2.32 mm over R7_J30 / J31_launch_In1, as designed (In2 GND below, check_r7
  launch_reference). Fully referenced with no via at all: USB_DP 17.5 mm, USB_DM 20.3 mm, SWDIO 20.2 mm, SWCLK 15.9 mm,
  and all ten radio interface lines (9.8–41.0 mm each).
- **B.Cu over In2 GND:** PYRO1_CONT 45.0 mm, PYRO1_GATE_N 36.9 mm, ARM1_SENSE 36.9 mm, RADIO_TXEN 21.8 mm and the GNSS
  limiter nets.
- **B.Cu over In2 3V3** (U1's field and the sensors):
  - the QSPI stubs: IO1 7.28 mm, NCS 1.37 mm, CLK and IO3 1.13 mm each, IO2 1.07 mm, IO0 0.25 mm (12.2 mm in all);
  - SPI1 / IMU_CS: 0.39–0.71 mm each;
  - ARM1_SENSE 14.48 mm, ARM1_SENSE_MCU 0.81 mm;
  - NRST 27.25 mm (not an AGENTS §3 net).
- **B.Cu over no copper:** HSE_IN 2.90 mm and HSE_OUT 2.82 mm, under Y1_In2_keepout, with In1 GND 1.23 mm above.

Critical layer changes (28 vias). Each row gives the nearest GND via or plated GND hole. Where the B side lies over In2
3V3, it also gives the nearest 3V3 bypass capacitor.

| Net | Via | GND via | B-side In2 | Nearest 3V3 bypass |
|---|---|---:|---|---|
| QSPI_CLK / IO3 | (27.75, 42.57) / (27.75, 43.83) | 1.06 / 1.06 | 3V3 | C29 2.96 / 1.71 mm |
| QSPI_IO0 / IO1 | (26.13, 40.55) / (25.0, 39.4) | 0.84 / 0.78 | 3V3 | C16 2.76 / 3.20 mm |
| QSPI_IO2 / NCS | (17.5, 42.57) / (17.5, 45.1) | 1.27 / 1.06 | 3V3 | C23 2.47 / 2.35 mm |
| SPI1_MISO / MOSI / SCK, IMU_CS | (8.79, 55.75) … (10.5, 55.65) | 0.88–1.47 | 3V3 | C13 5.1–6.4 mm (B.Cu stubs 0.39–0.71 mm) |
| HSE_IN / HSE_OUT | (22.0, 51.1) / (23.7, 46.35) | 1.00 / 1.05 | keep-out (In1 is the reference) | — |
| PYRO1_GATE_N | (18.75, 54.3) / (23.0, 88.33) | 1.33 / 1.31 | GND notch / GND | — |
| PYRO1_CONT_MCU / ARM1_SENSE_MCU | (24.0, 53.7) / (29.3, 47.5) | 1.01 / 0.71 | 3V3 + GND / 3V3 | C14 2.5 / C15 1.9 mm |
| ARM1_SENSE | (18.18, 91.3), (14.55, 94.15 / 97.55) | 1.35, 0.72, 0.72 | GND | — |
| PYRO1_CONT | (28.4, 88.61) | 1.41 | GND | — |
| RADIO_TXEN | (28.59, 7.8) / (31.13, 20.15) | 0.72 / 0.72 | GND | — |
| GNSS_ANT_DC / LNA_EN / VCC_RF | (11.45, 5.15) / (11.51, 8.9) / (10.41, 8.9) | 1.01 / 1.25 / 1.50 | GND | — |
| PYRO1_GATE (A8) | (20.45, 92.4) | 2.72 | GND | allowlisted, D9 |

- AGENTS §3's GND-via rule holds everywhere except A8.
- For the 3V3-referenced B.Cu stubs, the return crosses from In1 GND to In2 3V3 through the 3V3 bypass capacitors, not
  through the GND via. Finding 03.

## 5. Crystal, QSPI, SPI, USB, SWD

- **Crystal (Y1 at (22.85, 48.60), bottom side).** The B.Cu GND pour floods round Y1 and between its pads (Y1.2 / Y1.4
  joined). C25 and C26 tie to it through their own GND stubs and vias. Seven GND vias lie within 2.2 mm of the crystal
  pads: (19.0, 47.3), (22.65, 46.35), (19.95, 50.65), (21.0, 51.1), (18.75, 49.7), (26.95, 47.5), (26.95, 51.1). In2 has
  no copper under Y1, C25, C26 or the HSE B.Cu runs. In1 GND is solid above them, which shields the crystal from the U1
  F.Cu inside its pin ring.
- **The crystal's neighbours.** HSE's F.Cu escapes run beside NRST and a 3V3 pin for 0.5–2.4 mm at 0.30 mm, which the
  LQFP pin order forces (pins 12, 13, 14). No other signal lies within 0.5 mm.
- **D74's trade-off.** An In2 GND island in the keep-out would add about 0.1–0.2 pF per HSE node (parallel-plate
  estimate; Inference) against CIRCUIT_REVIEW's start-up margin. Keeping the keep-out as a hole in the fill is defensible,
  and is not a finding.
- **QSPI.** The flash sits under U1. Its stubs dive at six vias, each with a GND via 0.78–1.27 mm away and a 3V3 bypass
  1.71–3.20 mm away; the B.Cu stub lengths are in section 4.
- **SPI1.** It runs on F.Cu over In1 GND and drops to the bottom-side IMU through a four-via cluster (P3b's slot). GND
  vias sit 0.88–1.47 mm from the cluster, and the stubs are under 0.75 mm.
- **USB and SWD.** They run on F.Cu over solid In1 for their whole length with no via; D4 is a flow-through part.
- **Radio interface lanes.** They run on F.Cu over In1 GND and cross the fence through D67's openings.

## 6. GND pours: islands, fingers, stitching

- **Islands.** F.Cu has 10 GND islands and B.Cu 8. Every island has two or more GND vias or plated GND holes except the
  D4.2 pocket (D63). Thin islands with 2 vias: F.Cu (21.85–22.35, 22.53–30.19), a 0.5 mm strip between RADIO_MISO_MCU
  and RADIO_MOSI, stitched at (22.1, 23.3) and (22.1, 26.7); and F.Cu (7.36–8.69, 20.70–27.95).
- **Fingers by R7's C11 method** (`route_check.pour_pieces` with the finger width at 0.75 or 1.0 mm and no relief-ring
  exclusion, which reproduces R7's 23 / 48 exactly on `c872a3d3…`):

  | Board | F/B pieces < 0.75 mm beyond 4 mm of copper from a GND via | < 1.0 mm | Worst copper distance |
  |---|---:|---:|---|
  | R7 `c872a3d3…` | 23 | 48 | 16.52 mm (B.Cu 15.39–16.92, 68.11–74.16); the record's "10.7 mm" is the x 40 F.Cu finger |
  | R8 `429b6db4…` | 12 | 18 | 15.09 mm (F.Cu radio-lane sliver, below) |

  R8's twelve pieces narrower than 0.75 mm, each with its maximum copper distance to a GND via (0.1 mm raster, whole
  layer):

  | Layer | Box (x; y) | Area | Max distance |
  |---|---|---:|---:|
  | F.Cu | 23.76–32.0; 27.83–38.6 | 6.68 mm² | **15.09 mm** |
  | B.Cu | 42.05–44.79; 84.93–87.23 | 1.98 mm² | 14.77 mm |
  | B.Cu | 43.97–45.5; 82.44–85.54 | 1.28 mm² | 11.70 mm |
  | B.Cu | 33.55–40.5; 47.7–51.13 | 6.67 mm² | 10.91 mm |
  | F.Cu | 34.25–36.14; 49.3–52.21 | — | 7.10 mm |
  | B.Cu | 44.75–45.5; 59.01–64.0 | — | 7.07 mm |
  | F.Cu | 17.5–22.19; 100.03–104.69 | — | 5.26 mm |
  | F.Cu | 14.15–17.67; 47.87–51.55 | — | 5.18 mm |
  | B.Cu | 16.69–17.93; 63.2–66.24 | — | 4.87 mm |
  | B.Cu | 9.3–12.15; 40.31–42.48 | — | 4.46 mm |
  | B.Cu | 17.58–20.9; 42.77–43.58 | — | 4.37 mm |
  | F.Cu | 18.0–21.48; 90.37–93.72 | — | 4.01 mm |

- **Why the gates miss them.** P9–P11 and D62's pour cover measure Euclidean distance to the nearest GND via, and these
  slivers lie beside well-stitched pours. route_check's `pour_finger` measures copper distance, but only for pieces under
  0.5 mm.
- **Stitching.** P9 / P10 / P11 and the strip fence were re-measured above (gate OK). Strip GND reach is F.Cu 3.04 mm and
  B.Cu 3.49 mm (limit 4.0).

## 7. The ground half of the 7.7 A servo loop

- **The loop.**
  - Supply: J1.1 → BAT_IN pours → Q120 → Q121 → RAW_ACT west pours → J122's + pins.
  - Return: J122's four GND pins (x 20.46, y 71.9–79.5; solid zone connection) → the GND planes → **J1.2 (25.54,
    110.4)**.
  - J1.2 has **no GND track** and joins the planes only through the zone thermals. F.Cu has 4 spokes totalling 2.02 mm
    (0.5 mm gap), In1 has 4 totalling 1.61 mm (0.25 mm gap), and B.Cu has 4 totalling 2.02 mm. There is no In2
    connection: J1.2 sits inside the In2 BAT_IN island.
  - On the same terminal, J1.1 (BAT_IN) is solid on F, In2 and B, with 8.5 mm of contact per layer.
- **How narrow that is.** The spoke ring carries the whole board return: the 7.7 A stall plus the logic and camera
  loads.
  - Equivalent 35 µm width: 2.02 + 2.02 + 1.61 × 30/35 = **5.42 mm**. D12's 20 °C width for an outer 7.7 A neck, with no
    plane credit and a long-conductor fit, is 5.3 mm. The spokes are only 0.25–0.5 mm long, so the real rise is much
    lower (Inference).
  - By conductance (w·t/L), In1's four spokes carry about 41 %, roughly 0.8 A per 0.4 mm spoke (about 66 A/mm²) at
    7.7 A (Inference).
- **Not covered by any solve.** REQUIREMENTS F4's solves (`tools/run_dc.sh`) cover RAW_ACT, BAT_IN and ACT_FET_S only.
  M3_R7 recorded "the servo GND return (planes) was not analysed", and R8 left it so.
- **Path.** The return flows south from J122 to J1, away from U1 and the sensors (both at y < 63), and through the pyro
  block's GND. The drop is a few mV at 7.7 A (Inference: In1 alone is about 1.5 squares at 0.57 mΩ/sq, with the outer
  pours in parallel), negligible against the 0.2 V arm-sense thresholds.
- **The solve attempted here.** I started `tools/dc_solve.py --net GND --source J122:3,6,9,12 --sink J1:2 --grid 0.1`. On
  the whole-board GND net it had not converged after the time this review allowed (more than 17 CPU-minutes; the
  pure-Python CG has no numpy), so no solved figure is given. Finding 04.

## 8. Findings

### R8P1-PLANES-01: Minor, worth fixing
**R7's C11 class (unstitched GND fingers 0.5–1.0 mm wide) is not in R8's deviation list. Its worst piece is a 0.54 mm
F.Cu sliver between RADIO_NSS and RADIO_SCK_MCU, 15.1 mm of copper from a GND via.**

- **Requirement.** REQUIREMENTS M2 "every review-only residual is listed". The gate checks unstitched fingers only below
  0.5 mm. R7 recorded the 0.5–1.0 mm class as C11 (pass-4 P4-RF-01), and the owner accepted it for `c872a3d3…` only.
- **Evidence.** By R7's own method, R8 has 12 F/B pieces narrower than 0.75 mm, and 18 narrower than 1.0 mm, that reach
  beyond 4 mm of copper from a GND via (R7: 23 / 48). R8_VALIDATION's C list has no row for them.
- **The worst piece.** F.Cu, box x 23.76–32.0, y 27.83–38.6, 6.68 mm²:
  - It lies between RADIO_NSS's diagonal (31.65, 38.722)→(23.2, 30.272) and RADIO_SCK_MCU's diagonal
    (32.25, 37.85)→(25.1, 30.7). The centre lines are 1.041 mm apart, so the GND strip is 0.541 mm wide.
  - It joins the rest of its island (F.Cu island box 23.45–32.0 × 15.52–38.6, 20.25 mm², 3 vias) only through the
    0.43 mm gap between R310.2 and R313.1, and its vias are at y ≤ 26.7.
  - Its tip at (31.98, 38.58) is **15.09 mm of copper from a GND via** (0.1 mm raster; the box-limited 0.05 mm raster
    gives 15.06 mm).
- **Why the gates miss it.** It is Euclidean-close (< 3 mm) to the stitched pour east of RADIO_SCK_MCU. P11 and D62's
  pour cover are therefore satisfied, and `pour_finger` skips it because it is wider than 0.5 mm.
- **Effect.** About λ/9 at 1.575 GHz. RF effect small (Inference, as R7 judged the class); it sits in the MCU zone 7 mm
  south of the fence. A via fits only at DRC + 0.001 mm (0.5 + 2 × 0.17 = 0.84 mm against a 0.841 mm gap).
- **Fix.**
  1. Remove the sliver with a seventh pour trim, R8_POUR_TRIM_G7. It is an F.Cu fill-only rule area whose outline runs
     on the centre lines of the two lanes, from below R310.2 / R313.1 (y ≈ 30.3) to the lanes' ends at U1, generated by
     `step7/make_ground.py` like G1–G6 (D65). The `trims` gate proves that only GND fill goes, and no pad loses pour
     contact.
  2. Add an R8_VALIDATION C row for the remaining pieces, with the table in section 6 (layer, box, copper distance) and
     the reason each cannot be stitched or trimmed.
  3. Optionally, raise `route_check.FINGER_W` to 0.75 mm in the r8 profile, so that the class becomes gated.

### R8P1-PLANES-02: Minor
**The reference audit's net set is 24 of the 59 AGENTS §3 critical nets, so the one critical split crossing on R8
(ARM1_SENSE) is not recorded.**

- **Requirement.** AGENTS §3's critical list: RF, pyro and arming, crystal, USB data, SPI / QSPI / IMU CS and the other
  RADIO_* / GNSS_* nets. The task names "every critical signal's reference" as a review item.
- **Evidence.** `tools/critical_reference.py` R6_NETS + EXTENDED holds 24 nets. Pyro and arming, RADIO_NRST / BUSY /
  DIO1 / RXEN / TXEN, all GNSS_* nets and the RF nets are not sampled.
- **The full set, sampled here** (59 nets + SWD / NRST, 0.02 mm, centre and both edges):
  - **One split crossing:** ARM1_SENSE on B.Cu, track (18.18, 53.10)→(18.18, 91.30), crosses In2 3V3 → GND at
    **(18.18, 53.86)**, after 14.48 mm over In2 3V3 (28.0, 48.36)→(18.83, 52.45)→(18.18, 53.10).
  - Otherwise only own antipads, the J30 / J31 launch cut-outs (2.32 mm each, intended) and the J121 / J124 barrels under
    PYRO1_BUS / OUT / IGN (1.70–1.85 mm).
- **Is the board wrong?** No. ARM1_SENSE there is the divider's low node, behind 4.7 kΩ to the ADC, and the crossing lies
  inside D47's U1-field exemption, whose stated reason holds: GND under that run would cut the 3V3 finger feeding U1's
  VDD via (22.0, 54.15). But M3_R8 "Return paths" and D74 state their "0 along a split" result without saying it covers
  only the R6 and extended sets.
- **Fix.**
  1. Add one line to M3_R8 "Return paths" / D47 naming the crossing (net, point, the 14.48 mm over 3V3) and the set the
     audit covers.
  2. Give `tools/reference_audit.py` an `--agents3` set built from `route_check.CLASSES` (signal-critical classes), and
     record its result beside R6b. No copper change.

### R8P1-PLANES-03: Minor
**In2 3V3 is now the reference plane under U1's B.Cu critical stubs and under both bottom-side sensors. R7 had 3V3A or no
copper under the sensors. The R8 records state neither the change nor the reference-transition path.**

- **Requirement.** AGENTS §2.5 (an inference must be labelled), and REQUIREMENTS M2 (review residuals listed).
- **Evidence** (share of In2 under each part's pads + 0.5 mm):

  | Part | R8 | R7 |
  |---|---|---|
  | U4 (IMU) | 3V3 97 %, no copper 3 % | no copper 76 %, 3V3A 24 % |
  | U5 (baro) | 3V3 99 % | 3V3A 84 %, no copper 14 % |
  | U3 (flash) | 3V3 98 % | — |

  - D47 defines no 3V3A In2 region (D44 makes 3V3A a trunk), so 39.6 mm of 3V3A B.Cu (9.96 mm²) lies over the digital
    3V3 plane: about 1.9 pF, parallel plate.
  - The QSPI, SPI1 / IMU_CS, ARM1_SENSE_MCU and PYRO1_CONT_MCU stubs reference In2 3V3, so their layer-change return goes
    from In1 GND to In2 3V3 through the 3V3 bypass capacitors 1.71–3.20 mm away (QSPI) or 5.1–6.4 mm away (SPI1 stubs of
    0.39–0.71 mm). AGENTS §3's GND via does not carry that transition.
- **Effect.** Inference: negligible. 1.9 pF is about 830 Ω at 100 MHz against the 3V3A node's roughly 0.3 Ω local
  decoupling (about −69 dB), and the stubs are 0.25–7.3 mm long.
- **Fix.** No copper change. Add a paragraph to M3_R8 "Power: In2 map" / D47 stating the reference plane under U1, the
  flash and the sensors, the bypass capacitors that close the return at each critical layer change (this table), the
  change from R7 and the Inference.

### R8P1-PLANES-04: Minor
**The ground half of the 7.7 A servo loop is unsolved. Its narrowest point is the battery GND terminal J1.2, which joins
the planes only through 12 thermal spokes (5.42 mm equivalent width), while J1.1 on the same terminal is solid.**

- **Requirement.** REQUIREMENTS F4 ("size and independently solve the final copper … at this load, including pad/via
  transitions and necks"), and AGENTS §3 (high-current copper sized per IPC-2152).
- **Evidence.**
  - J1.2 (GND, 2.6 mm pad, 1.6 mm drill) has no track and inherits the zone connection: GND_F / GND_B THT-thermal
    (0.5 mm spokes, 0.5 mm gap), GND_In1 thermal (0.4 mm, 0.25 mm), and none on In2 (BAT_IN island).
  - The arcs of fill just outside the pad measure F.Cu 4 spokes / 2.02 mm, In1 4 / 1.61 mm, B.Cu 4 / 2.02 mm, In2 none.
  - J1.1 (BAT_IN) is solid with 8.48 mm per layer on F, In2 and B, and J122's GND pins are solid (pad override).
  - The return current is the full 7.7 A plus the logic and camera loads, so the ring is the return's narrowest cut. Its
    equivalent width, 5.42 mm, is level with D12's 5.3 mm outer limit; the spokes are 0.25–0.5 mm long.
  - `tools/run_dc.sh` solves only RAW_ACT, BAT_IN and ACT_FET_S. M3_R7 recorded the GND return as not analysed, and R8 is
    the same.
- **Effect.** Low thermal risk. The spokes are short and heat-sunk by the barrel and the planes (Inference), and flight 1
  flies one servo (1.92 A, 1/16 of the I² heating). The DC drop to the pyro sense ground is a few mV (Inference).
- **Fix.**
  1. Add the return as a fourth `run_dc.sh` path (`--net GND --source J122:3,6,9,12 --sink J1:2 --necks --max-rise 20`)
     and record its resistance and neck in M3_R8 "DC solve". Whole-board GND at 0.1 mm is slow in the pure-Python
     solver, so a windowed GND solve (x 0–46, y 68–118) is enough.
  2. Optionally, give J1.2 a solid zone connection like J1.1 and J122's GND pins. This is a rigid-J1 re-baseline, and it
     makes J1's THT solder joint sink more heat; that trade-off is for the owner.

## 9. Observations (not findings)

- **ACT_GATE.** It crosses In2 GND, BAT_IN and RAW_ACT over 3.2 mm of B.Cu between the FETs. It is a slow gate drive, and
  the crossing is inherent to the facing-FET band (D12).
- **Bucks.** U2 / L1 and U8 / L3 sit 98–100 % over In2 GND (In1 GND above). Each hot loop closes on B.Cu: U8.4 →
  0.6 mm track → C72.2 → via (43.41, 37.6).
- **U1 decoupling.** Each U1 supply pin has its bypass capacitor 1.51–2.68 mm away on the bottom side, and that
  capacitor's GND pad is 0.78–1.09 mm from a GND via.
- **IMU.** Its GND pads reach their vias, (7.5, 53.8) and (10.5, 52.1), through 0.2 mm B.Cu tracks of 1.3 mm and
  0.74 mm, because IMU_body_B forbids vias under the body. C30 / C31 share the via (13.545, 54.485).
- **R7 → R8 trend.** Planes improved markedly. Unstitched fingers fell from 23 / 48 to 12 / 18. P7 fell from 32 to 1.
  R7's 11,516 foreign, split and void samples fell to 0 on the audited set, and to one crossing on the full set.

## Method and scripts (scratchpad, read-only)

- `zones.py`: zone and rule-area inventory, fill areas and outline counts.
- `holes.py` / `holes2.py`: In1 holes, unfractured, with the items inside each and the critical tracks crossing them.
- `refall.py`: the reference of all 59 critical nets + SWD / NRST. `splitall.py`: reference changes on every signal net.
- `vias.py`: critical vias, their GND via, the B-side In2 net and the nearest bypass.
- `region.py`: copper and fill maps per layer. `islands.py` / `necks.py`: opening-based thin parts.
- `fingers*.py`: route_check `pour_pieces` at 0.5 / 0.75 / 1.0 mm, with and without relief rings; copper distance
  through route_check's `reach`.
- `under.py`: In2 net under parts, R7 against R8. The R7 board was extracted from `git show 431025d` into the
  scratchpad; nothing in `../rocket-flight-computer-r7` was touched.
- `spokes.py`: arcs of fill at J1.1 / J1.2. `decap.py`: U1 bypass distances. `len3v3a.py`: 3V3A copper over In2 3V3.
- All of these ran on `429b6db4…` with KiCad 10.0.6's Python.
