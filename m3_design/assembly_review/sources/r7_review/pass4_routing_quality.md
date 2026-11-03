# R7 review pass 4: routing quality of critical and new nets

Reviewer scope: electrical routing quality of the critical and new nets against the owner's clean-routing criterion
(REQUIREMENTS M2, AGENTS.md §3) and reference continuity. Nets: the radio/GNSS interface, SWD, the camera UART and
enable, QSPI, SPI1 (IMU), USB, the power feeds (3V3, VCAP, FB30/FB31) and the pyro nets. For each I measured detour
ratio, vias and layer hops, bus tidiness, reference-plane continuity and split crossings, and asked whether a cleaner
route fits.

Board reviewed: `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650` (fix pass 3 final, the hash bound in
`docs/R7_VALIDATION.md`). The hash was the same before and after this review. References: pass-3 board
`7660620c…7c9c`, R6 `3b215ba` (`184a87e8…`, moved +18 mm in y).

The review was read-only. Boards were copied to a scratch directory and never saved; the only repository file written
is this report.

## 1. Method

1. **Gate.** `tools/check.sh` on the repository board: exit 0. DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silk 0;
   R7 contract OK; `routing hygiene: 0 failing, 42 allowlisted, 0 stale`; actuator contract OK; fit OK.
   `tools/route_check.py --report` and `--routes` on the final board and on the pass-3 board (same tool).
2. **Copper diff.** Every track and via of the pass-3 board against the final board, per net (`diffp3.py`). Changed nets:
   SWCLK, SWDIO, PYRO1_CONT, PYRO1_GATE_N, PYRO1_COLD, 3V3, GND, RAW_PROTECTED, SERVO1_MCU; plus 21 new
   `R7_POUR_TRIM_n` keep-out areas. Every other net's copper is byte-identical.
3. **Per-line metrics.** The pass-2/3 path tracer (shortest pad-to-pad copper path, octilinear ratio, layer changes).
4. **Reference planes.** The pass-3 `refscan.py` (0.05 mm samples, reference layer F→In1, B→In2, In1→F, In2→B, with
   holes; antipads filtered), extended to SWD, CAM_PWR_EN and CAM_UART_OE, run on both boards and compared event by
   event. Also `tools/critical_reference.py` R6→final (R6 method) and pass-3→final (`--extended`).
5. **Plane islands.** Every zone fill island per layer and net on both boards, with the vias and pads inside each.
6. **Adjacency.** Same-layer edge gaps and adjacent-layer (B/In2, F/In1) broadside overlaps between each rerouted net
   and every critical net (`adj.py`); exact shape distances with `SHAPE::Collide` (`mind.py`).
7. **Candidate routes.** `fitprobe.py` (pass 3) for one candidate; the F4 router outputs in `<scratchpad>/fx3/rt/` and
   `fx3/det/` were read, not re-run. I did not run an independent route search.
8. **Renders**, rasterised and inspected: SWD region, PYRO1_CONT/SPI1 bundle, pyro block, L1.2 node, CAM_PWR_EN.

## 2. Pass-3 findings in this dimension: closure

| Pass 3 | Disposition in R7_VALIDATION | Checked on the final board | Verdict |
|---|---|---|---|
| P3-ROUTING_QUALITY-01 (Minor) | Recorded deviation (8 interface vias) | The 8 vias are present, nearest GND via 1.65 / 1.65 / 2.11 (band), 1.71 / 2.60 / 3.18 / 3.57 (U1 escape), 2.23 mm (RXEN). The two moved GND vias give RXEN (21.2, 30.45) **1.491 mm** and GNSS_RXD_MCU (2.2, 51.5) **1.499 mm** (≤ 1.5). Allowlist reasons match | **Closed** (properly dispositioned) |
| P3-ROUTING_QUALITY-02 (Minor) | Recorded deviation; not changed | refscan: no RADIO_* reference event changed; the 14 GND↔BAT_IN crossings are as on pass 3 | Dispositioned; the stated reason is incomplete at the band end (P4-ROUTING_QUALITY-03 a) |
| P3-ROUTING_QUALITY-03 (Minor) | Recorded deviation; not changed | NRST B.Cu over CAM_MCU_TX In2 unchanged; CAM_MCU_TX 65.87 mm / 5 vias (2.67×) | **Closed** (dispositioned) |
| P3-ROUTING_QUALITY-04 (Minor) | Fixed | PYRO1_COLD (29.72, 86.1)→(29.72, 85.33)→(31.05, 84.0), 2.65 mm, ratio 1.00 | **Closed**. New neighbour: PYRO1_CONT's new F.Cu run passes 0.315 mm from it (sense to sense, no pyro rule; fine) |
| P3-ROUTING_QUALITY-05 (Minor) | Recorded deviation (inherited R6) | VCAP2 12.67 mm / 1 via, 25.4 mΩ of copper; VCAP1 6.71 mm / 2 vias, 13.9 mΩ. U12/C100 3V3 feed unchanged | **Closed** (dispositioned). Supporting check: ST DS12110 §6.3.2 "VCAP operating conditions" requires CEXT 2.2 µF with ESR < 100 mΩ (https://www.st.com/resource/en/datasheet/stm32h743vi.pdf, local copy); copper 25.4 / 13.9 mΩ plus the 0603 X5R's 10–30 mΩ (docs/CIRCUIT_REVIEW.md) is 24–55 mΩ, inside the limit |
| P3-ROUTING_QUALITY-06 (Minor) | Fixed (record) | RQ-11 row lists the four kept items; the `_NOGND`/PYRO1_GATE_N allowlist reason states the 1.03 mm DRC-legal spot and the ViaCheck refusal (`tools/route_check.py` l.184–188) | **Closed** |

No pass-3 Major was raised in this dimension. **P3-REQUIREMENTS-01 (Major, requirements dimension)** covers the SWD
and camera detours; it stays open in R7_VALIDATION pending more rerouting or owner acceptance. My measurements agree
with its record (SWCLK 62.70 mm / 4 vias, SWDIO 53.72 / 4, CAM_PWR_EN 81.90 / 8, CAM_MCU_TX 65.87 / 5), apart from the
precision points in P4-ROUTING_QUALITY-03.

## 3. What fix pass 3 changed (copper diff, pass-3 board → final)

| Net | Removed | Added | Notes |
|---|---|---|---|
| SWCLK | 46 tracks, 117.20 mm, 14 vias (19.47 mm on In1) | 16 tracks, 62.70 mm, 4 vias, F/B only | ratio 3.55 → 1.90; U-turn (north under U1, back down its east side) |
| SWDIO | 32 tracks, 70.82 mm, 11 vias (7.77 mm on In1) | 12 tracks, 53.72 mm, 4 vias | ratio 1.95 → 1.48; **13.73 mm on In2** (8.15 mm between J122's rows + 5.58 mm under the SPI1/I2C1 bundle); 2.58 mm B.Cu hop over PYRO1_GATE_N's In2 run |
| PYRO1_CONT | 22 tracks, 54.09 mm, 7 vias | 12 tracks, 41.80 mm, 4 vias | net 59.89 → 47.60 mm; route through the SPI1/servo bundle (P4-ROUTING_QUALITY-01) |
| PYRO1_GATE_N | 4 tracks (83 µm hook) | 1 straight 0.2 mm run x 21.9 into R126.1 (0.3 mm off centre, inside the pad) | clean |
| PYRO1_COLD | 2 tracks | 2 tracks | see §2 |
| 3V3 | 22 tracks (In2 dead runs at L1 and U1, L1.2 node), 2 vias | 9 tracks, 1 via | L1.2 node redrawn; C17.1 entry square; J2.1 feed via 0.6 → 0.5 mm |
| GND | 43 tracks (dead stubs, corners), 2 vias | 10 tracks, 8 vias | GND vias moved (2), PYRO1_CONT return (2), C160.2 (1), strip stitching (3) |
| RAW_PROTECTED, SERVO1_MCU | corner / via shift | | trivial |

**In1** now carries only NRST (3.24 mm) and CAM_TX_WIRE (3.67 mm); the SWD In1 runs (27.2 mm) are gone, so the In1
GND plane under every F.Cu critical run is more continuous (fill 4,686.8 → 4,718.0 mm²).

## 4. Per-line metrics, final board

Unchanged from pass 3 (identical copper): radio NSS 57.40 mm / 1.57 / 4 layer changes, SCK 1.60, MOSI 1.56, MISO
1.60, BUSY 1.57, NRST 85.44 / 1.92 / 4, DIO1 69.09 / 1.77 / 4, RXEN 51.31 / 1.26 / 4, TXEN 25.17 / 2.30; GNSS TXD/RXD/TP
1.36 / 1.39 / 1.44, RESET_N 1.69; QSPI_IO0..3 1.16–1.25 (2–3 vias), QSPI_NCS 1.13; SPI1_SCK/MOSI/MISO 1.20 / 1.12 /
1.04, IMU_CS 1.08 (1 via each); USB_DP/DM 30.57 / 30.86 mm (3 / 2 vias, J3 crossover); HSE_IN/OUT 1.00 / 1.18; FB31
feed 5.61 mm one 0.4 mm F.Cu run; 3V3_RADIO 1.63 (through C310→C312→C311), 3V3_GNSS 1.16; RF lines straight, 0.30 mm,
no via.

Changed nets (`route_check --routes`, pass 3 → final): SWCLK 117.2 mm / 3.55× / 14 vias → 62.7 / 1.90 / 4; SWDIO
70.8 / 1.95 / 11 → 53.7 / 1.48 / 4; PYRO1_CONT 59.9 / 1.47 / 7 → 47.6 / 1.17 / 4; PYRO1_COLD 1.12 → 1.00;
PYRO1_GATE_N 42.96 → 42.79 mm. Not changed: CAM_PWR_EN 81.9 / 2.52 / 8, CAM_MCU_TX 65.9 / 2.67 / 5, CAM_MCU_RX 32.8 /
1.24 / 6, VCAP1 4.89×, VCAP2 4.22×.

## 5. Reference planes and split crossings

**refscan, pass 3 → final, every critical and focus net.** Only these nets changed:

| Net | Change |
|---|---|
| SWCLK | void 41.97 → 6.96 mm (GND 51.93, 3V3 4.11) |
| SWDIO | void 37.79 → 26.06 mm; B.Cu (18.55, 65.45–73.1) 7.7 mm and (20.8, 63.2)→(18.55, 65.45) 3.2 mm over In2 void |
| PYRO1_CONT | GND 41.05 → 23.91 mm, void 19.40 → **23.89 mm** (32 % → 50 % of the net unreferenced). B.Cu over In2 void: (33.98, 53.85–57.95) 4.15, (24.68, 68.65)→(27.48, 71.45) 4.01, (27.48, 71.45–76.9) 5.5, (27.48, 76.9)→(29.23, 78.65) 2.5 mm |
| **SPI1_SCK** | **new 0.652 mm void at (23.85–24.27, 67.25–67.67) between two 3V3 pieces: a split crossing** (P4-…-01) |
| ARM1_SENSE | In2 (16.6, 70.4)→(19.5, 67.4): B.Cu GND under it 3.1 mm void + a GND piece → 4.2 mm void (SWDIO's B.Cu run at x 18.55 and trim 12) |
| PYRO1_GATE_N, BAT_FAULT_N, CAM_MCU_TX, CAM_PWR_EN, PULLPIN, VLOGIC_SENSE | ±0.3–1.5 mm of B.Cu GND under In2 runs (pour trims, removed dead GND tracks, SWD B.Cu runs). No new plane-net change |
| RADIO_*, GNSS_*, QSPI_*, SPI1_MOSI/MISO, IMU_CS, USB_D*, HSE_* | **no change** |

**critical_reference.py.** R6 method, R6 (+18 mm) → final: 864 lost / 1,122 candidate-new, matching the record. The
only critical-net losses against the pass-3 board are SPI1_SCK 215 samples at (23.74–24.34, 67.14–67.84) and
SPI1_MISO 46 at (24.14–24.46, 68.18–68.50), both from PYRO1_CONT. The R6 method counts the 3V3 plane as a reference, so
it does not see that the two sides of the SPI1_SCK crossing are now different 3V3 islands (§P4-…-01).

**In2 3V3 islands.** Pass 3: 7 islands, including one of 72.15 mm² at (22.10–31.69, 51.24–70.20) stitched by 4 vias.
Final: that island is cut by PYRO1_CONT's In2 diagonal into **41.93 mm² (3 vias: (27.9, 56.3), (27.85, 62.75),
(30.7, 57.18)) and 22.69 mm² (1 via: (30.17, 65.1))**. Probe points (23.7, 67.1) and (24.4, 67.8), either side of the
SPI1_SCK crossing, were in one island on pass 3 and are in different islands now. In2 BAT_IN (770.8 mm²), In2 GND
(1,223.2), In2 CAM_5V and 3V3A are unchanged or larger. B.Cu GND islands went from 32 to 39 and F.Cu GND from 39 to 43
(trims, SWD B.Cu runs); every new GND via ties F.Cu, B.Cu and In1 fills (checked for all 8).

## 6. Findings

No Critical, no Major. Three Minor.

| ID | Sev. | New in fix pass 3 | Finding |
|---|---|---|---|
| P4-ROUTING_QUALITY-01 | Minor | yes | PYRO1_CONT's new route runs inside the SPI1/servo bundle: 7.6 mm side by side with SPI1_SCK at 0.195–0.228 mm, splits the In2 3V3 island under SPI1_SCK and passes 0.191 mm from a PYRO1_GATE_N via; recorded only as "+261 reference samples" |
| P4-ROUTING_QUALITY-02 | Minor | yes | SWD reroute side effects: SWCLK's via 1.10 mm from Y1's HSE_OUT pad, SWDIO's B.Cu run cuts the B.Cu GND under ARM1_SENSE; the SWDIO In2 length is misreported |
| P4-ROUTING_QUALITY-03 | Minor | records | Disposition reasons that overstate "no option": P3-RQ-02's band-end crossings, CAM_PWR_EN's "search returns the present route", and r7_polish's "power pours kept whole" |

### P4-ROUTING_QUALITY-01 (Minor): PYRO1_CONT routed through the SPI1/servo bundle

**Evidence (final board).**

- Route (`r7_polish.PYRO1_CONT_ROUTE`): R168.1 (33.03, 52.9) B.Cu → via (33.98, 57.95) → F.Cu → via (29.93, 61.55) →
  **In2 (29.93, 61.55)→(23.98, 67.5)→(23.98, 68.65)** → via → **B.Cu (24.68, 68.65)→(27.48, 71.45)→(27.48, 76.9)→
  (29.23, 78.65)** → via → F.Cu (29.23, 78.65)→(29.23, 85.39)→R178.1. 0.15 mm.
- **Side by side with SPI1_SCK** (0.2 mm, B.Cu, U1.89 → U4.13, the IMU clock): PYRO1_CONT's B.Cu diagonal runs
  parallel to SCK's (22.25, 65.65)→(27.85, 71.25) at 0.228 mm edge gap, and its vertical x 27.48 parallel to SCK's
  x 27.85 (71.25–74.85) at **0.195 mm**. Length within 0.25 mm edge gap: **7.60 mm**. On the other side SERVO1_MCU
  (x 26.9) is 0.40–0.45 mm away for 8.1 mm. All of it is over In2 void (refscan: "neighbours None"); the nearest solid
  plane is In1, 0.203 + 0.03 + 1.03 = 1.26 mm below B.Cu (board stackup).
- **Split crossing:** the In2 diagonal cuts the 72.15 mm² In2 3V3 island into 41.93 + 22.69 mm² (§5). SPI1_SCK's B.Cu
  run crosses the cut at (23.85–24.27, 67.25–67.67) from one island to the other (0.652 mm void; 215 R6-method
  samples). The via (23.98, 68.65) antipad in In1 sits under SPI1_MISO's F.Cu (46 samples).
- **Pyro sense next to a pyro gate:** the F.Cu leg (33.98, 57.95)→(30.38, 61.55) passes the PYRO1_GATE_N via (31.9,
  59.23) at **0.191 mm** (pass 3: 1.079 mm minimum between the two nets). DRC-legal: rule G covers gate nets only inside
  `PYRO_BLOCK`.
- PYRO1_CONT's own reference fell from 68 % to 50 % of its length (§5).
- The pass-3 route had none of this: its closest critical neighbour was SWDIO at 0.172 mm for 2.9 mm (SWD is idle in
  flight); its minimum gap to SPI1_SCK was 2.673 mm.
- **Record:** M3_R7 §"Return paths" lists the 261 samples and says "the only PYRO1_CONT route found that keeps the
  3V3 plane whole there has 6 vias". M3_R7 §"Close adjacencies kept" lists SPI1_MOSI–IMU_CS and
  BAT_SW_RETURN–QSPI_IO0, not PYRO1_CONT–SPI1_SCK or PYRO1_CONT–PYRO1_GATE_N. The `r7_polish.pyro1_cont` docstring
  says "the power pours kept whole", which this route does not do.
- **A route that avoids the bundle exists:** F4's `fx3/rt/pc_route2.json`, 6 vias, east of U4 (B → In2 → F → In2 → F
  → In2 → F), with the 3V3 plane whole. Not re-checked by me.

**Impact (inference).** PYRO1_CONT is the continuity-divider output: 10.2 kΩ from PYRO1_OUT, R130 2 kΩ and C127 10 nF
to GND in the pyro block, then 45 mm of trace to R168 (4.7 kΩ) at the ADC pin. SCK edges couple roughly 0.4–0.8 pF over
7.6 mm. The coupled charge flows into C127, about 0.3 mV per edge, and R168 with the pin capacitance filters what is
left. In flight the reading never vetoes a fire (AGENTS §2.3); on the ground a wrong reading can only refuse. The split
adds a little loop inductance to a clock line that is already 77 % unreferenced (inherited). A bridge between
PYRO1_CONT and PYRO1_GATE_N needs a fabrication defect at 0.191 mm, and the project already accepts about 0.2 mm
between PYRO1_GATE_N and logic nets outside the pyro block (CAM_UART_OE 0.200 mm on In2 at (31.9, 77.83), SERVO2_MCU
0.208 mm at U1.3; inherited). None of this is functional. The finding is about tidiness
and bus separation on a pyro-class net, and about an undisclosed trade-off.

**Fix (either).**
- Record it as a recorded deviation in M3_R7 §"Close adjacencies kept" and R7_VALIDATION, with the numbers above:
  PYRO1_CONT–SPI1_SCK 0.195 mm × 7.6 mm over no plane, the 3V3 island split, and PYRO1_CONT–PYRO1_GATE_N 0.191 mm.
  Correct the `r7_polish` docstring.
- Or take the 6-via plane-preserving route, and rerun `check_actuators` and the gate.

### P4-ROUTING_QUALITY-02 (Minor): SWD reroute side effects and a misreported In2 length

**Evidence.**

- **The new SWD copper is clean.** It is 0/45/90 only, with no tiny jogs and no short segments
  (`route_check`: SWD instances are only `detour`/`extra_vias`, information on a non-critical net, plus a SWCLK
  `u_turn` and a SWDIO `short_layer_hop` of 2.58 mm). Both lines enter J2 0.215 mm off the pad centres, inside the
  pads, as in R6. Neither touches In1 or the pyro block. No same-layer gap under 0.4 mm to any critical net, except
  0.30–0.33 mm to USB_DP/VCAP2 at U1's own pin pitch. The SWDIO hop crosses PYRO1_GATE_N's In2 run at 90°.
- **Crystal:** SWCLK's via (24.7, 50.95) is **1.100 mm** (copper to copper, B.Cu) from Y1's HSE_OUT pad (24.5, 52.9).
  Pass 3's minimum SWCLK–HSE gap was 2.157 mm. The router "kept the crystal clear" in the sense of a keep-out, not a
  distance. HSE_IN is 3.07 mm away.
- **B.Cu GND under In2 runs:** SWDIO's B.Cu verticals x 18.55 (65.45–73.1) and x 20.8 (56.8–63.2), with trim area 12,
  remove B.Cu GND under ARM1_SENSE's In2 diagonal (void 3.1 → 4.2 mm at (16.6, 70.4)→(19.5, 67.4)). They do the same
  under CAM_PWR_EN's In2 runs ((17.35, 79.25–83.9) 4.7 mm; (20.85, 56.05)→(17.16, 59.74) 5.3 mm).
- **Record:** the F4 handoff and M3_R7 call SWDIO's In2 part "a 5.9 mm In2 hop". The final copper has **13.73 mm on
  In2**: (18.55→26.7, 73.1) 8.15 mm between J122's rows, plus (26.7, 73.1)→(30.15, 69.65)→(30.85, 69.65) 5.58 mm.
  The 5.9 mm figure is from the earlier candidate (`fx3/rt/n1.txt`, `o3.txt`), whose J122-row run was on F.Cu.

**Impact (inference).** SWCLK is idle unless a probe is attached (PA14 pull-down), so the crystal proximity matters
only on the bench and is next to the driven HSE_OUT side. ARM1_SENSE is a DC divider node. Net effect: the SWD lines
are much better than R6's (117 → 63 mm, 14 → 4 vias, off In1). The side effects are small.

**Fix.** Correct "5.9 mm In2" to 13.7 mm in M3_R7, the F4 handoff and R7_VALIDATION if quoted. Record the SWCLK–Y1
1.10 mm gap and the ARM1_SENSE B.Cu reference change with the SWD reroute. Optional: move SWCLK's (20.5, 52.95)→
(24.7, 50.95) B.Cu hop and its via ≥ 2 mm from Y1 if a lane exists; not probed.

### P4-ROUTING_QUALITY-03 (Minor): disposition reasons that overstate "no option"

1. **P3-ROUTING_QUALITY-02 (14 GND/BAT_IN crossings).** R7_VALIDATION: "Moving them cuts U9's In2 BAT_IN arm or moves
   the band onto In2 GND; stitching needs a new BAT_IN–GND capacitor (schematic and BOM change)".
   - **U1 end** (y 47.5–50.5): true. The arm carries U9's feed, and C80 (10 µF) is 1.7–4.6 mm away.
   - **Band end** (y 27.2–30.2, the weakly stitched end): the arm north of U9 serves only C89.1, C95.1 and the two
     BAT_IN vias (7.6/8.8, 26.6). C89.1 and C95.1 already sit in the F.Cu BAT_IN pour (4.4–9.0, 25.7–36.9), which
     reaches In2 again through via (9.2, 36.05). R80's B.Cu feed also lands at that via.
   - So, by inference (connectivity checked, clearances not): pulling the In2 BAT_IN arm's north end back to about
     y 34.5 and extending the GND strip would put the band-end stubs over GND. It would drop the two vias at y 26.6 and
     need no schematic change. The record should name this option, or say why it was rejected.
2. **CAM_PWR_EN.** R7_VALIDATION P3-REQUIREMENTS-01: "no F/B path, and the raster search returns the present route".
   F4's own runs found 55.09 mm / 7 vias (`fx3/rt/cpe_fbi.txt`) and 72.35 mm / 4 vias (`cpe_6.txt`) through the two
   one-track corridors that SWDIO and SWCLK now occupy. The present route is the best only after the corridors went to
   SWD. M3_R7 says so ("with the SWD lines moved"); R7_VALIDATION drops the condition. The owner's acceptance
   (P3-REQUIREMENTS-01 option b) should see the trade-off:
   - SWD on the corridors: SWCLK 4 vias, SWDIO 4, CAM_PWR_EN 8;
   - versus CAM_PWR_EN on a corridor: about 7 vias or 4, and SWD longer.
   CAM_PWR_EN (8 vias, a hook round the pyro block to y 99.75) remains the messiest route on the board.
3. **`r7_polish.pyro1_cont` docstring:** "the power pours kept whole". The route splits the In2 3V3 island (P4-…-01).

**Fix.** Amend the three texts. No copper change is required by this finding.

## 7. What is clean

- **Interface, QSPI, SPI1 MOSI/MISO/IMU_CS, USB, HSE, FB30/FB31 feeds, RF lines:** copper identical to pass 3, and no
  reference event changed.
- **SWD:** 117.2 + 70.8 mm and 25 vias → 62.7 + 53.7 mm and 8 vias, off In1 and out of the pyro block; geometry clean.
- **In1:** In1 signal copper 34.2 → 6.9 mm (NRST and CAM_TX_WIRE only).
- **PYRO1_CONT:**
  - every layer change has a GND via (0.70, 0.95, 1.19, 1.49 mm);
  - the two new return vias tie F.Cu, B.Cu and In1 GND;
  - rule clearances: 2.34 mm to RAW_ACT (rule A 0.5), 0.751 mm to PYRO1_OUT (rule C 0.3).
- **Pyro block:** PYRO1_GATE_N is one straight run into R126.1 and PYRO1_COLD is two segments. PYRO1_CONT's in-block
  U-turn (R130.1 → C127.1, 3.61 mm) is forced: the north path collides with R178.2's and R130.2's GND copper
  (fitprobe, 0.15 mm).
- **L1.2 node:** tracks start from the pad; two 0.6 mm plane vias (24.8, 34.3) and (26.4, 36.6). C9.1's 45° step at
  (25.2–25.7, 36.6–36.1) is forced: the straight run hits USB_LIMITED's via (25.8, 37.15).
- **VCAP1/VCAP2:** inside ST's ESR limit (§2). The loops are inherited and recorded.
- **New GND vias:** the 2 moved vias, 1 by C160.2 and 3 strip stitches all tie F/B/In1, and In2 in the strip. None
  adds a void under a critical net (refscan, `critical_reference`).

## 8. Scripts and renders (scratch, not in the repository)

`<scratch>/p4rq/`:

- **Boards:** `r7.kicad_pcb` (`636a6bdc…`), `p3.kicad_pcb` (`7660620c…`), `r6.kicad_pcb`.
- **Dumps:** `r7.json`, `p3.json`, `r6.json`.
- **Gate and route_check:** `check.log`; `route_r7.json`, `routes_r7.txt`, `routes_p3.txt`.
- **Reference:** `ref_r7.json`, `ref_p3.json`, `refcmp.py`; `cref_r6_r7.txt`, `cref_p3_r7_ext.txt`.
- **New scripts:** `diffp3.py` (copper diff), `chain.py`, `islands.py` / `island_conn.py`, `adj.py`, `mind.py`; the
  pass-3 `metrics.py`, `trace.py`, `refscan.py` (pattern extended), `fitprobe.py`, `render.py`.
- **Renders:** `img/*.svg.png`: `swd`, `pc1`, `pc2`, `pblock`, `l1`, `cpe1`, `cpe2`.
