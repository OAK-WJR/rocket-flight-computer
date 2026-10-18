# R7 step B → step C handoff (board placement and routing done)

Step B is done in the worktree, uncommitted (branch `m3-assy-r7`, base `3b215ba`). The board
`m3_design/assembly_review/m3.kicad_pcb` is M3-ASSY-R7: 46 × 118 mm, 4 layers, stackup JLC041611-7628,
two-sided. The running log with every decision and its basis is `stepB_progress.md`; the record is
`docs/M3_R7.md` §"R7 board". The fab package is **not** regenerated (step C).

## 1. How the board is built

`m3_design/r7_build.sh` restores the R6 board from git (`3b215ba`, SHA-256 checked) and runs, in order:

1. `r7_pcb.py`: +18 mm translation, outline, supports, J123 move, R6 port parts and their copper out, R7 parts
   from the netlist, RF-strip placement, stackup, pours, keep-outs (KIID seed 7101).
2. `r7_route.py`: scripted copper (U1-side surgery, both GCPW lines, the limiter, both modules, the interface
   corridor and band, U1 fan-out), R6 clean-up, strip fence and stitching, then the displaced non-critical links
   replayed from `m3_design/r7_reroute_session.json` (KIID seed 7201).
3. `r7_post.py`: silkscreen and refill (seed 7301).
4. `tools/check.sh`.

About 75 s. Two consecutive runs give the same file. **Board SHA-256
`03fe75720f46b1382d9d3216dbffd8ae642d0125722c04589ff97c964aa86d54`.**

**The session file** is the house grid router's (r5_maze) recorded result, kept in git like R5's
Freerouting session. Replay checks a digest of the pre-reroute board and refuses a stale session.
`r7_route.py --search` reruns the router with the pinned order (`FIRST`) and rewrites the session; the rerun
reproduced the file byte for byte. No Freerouting session is used. A Freerouting trial restricted to the 13
nets left 11–13 of 15 connections open (`stepB_progress.md` §5).

## 2. Gate (`tools/check.sh`, final board)

```
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
silkscreen outside the board outline (46.00 x 118.00 mm): 0 stroke points
R7 CAD contract: OK
actuator safety contract: OK
radius 24.9 mm, axis x 23.0 mm, sled tolerance 0.3 mm; top face on the axis
  J9 mated     F  margin   0.03 mm   x  40.95.. 45.20  z   0.00.. 10.30
  C84          F  margin   0.11 mm   x   2.25.. 12.75  z   0.00.. 12.80
  J122 mated   F  margin   0.71 mm   x  19.00.. 27.00  z   0.00.. 23.50
  J3           F  margin   0.89 mm   x  -0.45..  7.45  z  -0.85..  3.25
  J121         F  margin   1.15 mm   x  30.65.. 41.35  z   0.00.. 14.40
  J124         F  margin   1.15 mm   x   4.65.. 15.35  z   0.00.. 14.40
  J9           F  margin   1.98 mm   x  40.22.. 45.18  z  -0.00..  4.20
  C74          B  margin   2.34 mm   x  44.30.. 45.10  z  -2.40.. -1.60
  R166         F  margin   2.38 mm   x   0.80..  4.00  z   0.00..  0.60
  L3           B  margin   2.51 mm   x  39.05.. 44.55  z  -4.60.. -1.60
  R101         B  margin   2.68 mm   x  44.00.. 44.80  z  -2.05.. -1.60
  Q120         B  margin   2.76 mm   x   1.35..  6.65  z  -2.61.. -1.60
  Q121         B  margin   2.76 mm   x   1.35..  6.65  z  -2.61.. -1.60
  C73          B  margin   2.96 mm   x  40.65.. 44.15  z  -4.30.. -1.60
  C77          F  margin   3.07 mm   x  42.90.. 44.50  z   0.00..  0.80
  deepest bottom part: L1 (z -4.62 mm), worst bottom margin 2.34 mm (C74)
  five-support geometry: [(4.0, 4.0), (4.0, 64.0), (4.0, 114.4), (42.0, 114.4), (42.3, 4.0)]
  board: 46 x 118 mm; 120 mm maximum (P1)
  nearest bottom/pin envelope: C76, 4.150 mm from support (42.0, 114.4) (minimum 3.5 mm)
  nearest top hardware clearance: TP89.1 exposed top pad, 3.858 mm from support (4.0, 64.0) (minimum 3.8 mm)
  wire entry to the bore wall at 5.0 mm height: J121 6.3-6.9, J124 6.3-6.9
fit check: OK (CAD envelopes only)
```

Exit status 0. Zone fill uses `ZONE_FILLER` from the scripts; kicad-cli's refill is not used.

**Unit tests (`tools/`, KiCad Python):**

| Result | Tests |
|---|---|
| Pass | test_check_shell (2), test_fit_check (22), test_maze_clearances (10), test_procurement (15), test_r6_check (17), test_r7_check (19); `quality_audit/test_quality_tools` OK |
| **Fail, step C** | `test_fab_validation`: 7 failures, 1 error. Every one comes from the R6 fab package: the CPL lacks the R7 refs and lists the removed ones, and the new parts have no verified JLC placement corrections (C300, C302, C312, D30, D31, FB30, FB31, J30, J31, L30, Q30, Q32, R300, R304–R306, R313–R316, U30, U31) |
| **Fail, pre-existing** | `test_r5_repair`: 1 error. The R5 scoped repair `routing_lands_spacing` no longer matches. It fails on the committed R6 board too (checked) |

## 3. RF measurements (final board; zones filled with the project rules)

**Lines.** 50 Ω GCPW on F.Cu over In1 GND, **W 0.30 mm on every RF segment**. The minimum gap to GND
copper (fill and pads) is **0.251 mm** against the 0.25 mm DRC rule; the SMA centre pads keep the 0.30 mm
launch gap (rule). In1 is cut out under both centre pads (x ± 0.9, y 0–4.6).

| Run | Path | Track length |
|---|---|---|
| GNSS | J30 pad 5 (12.85, 2.3) → straight north to R304.1 (12.85, 7.13); pad end y 4.4 | 4.83 mm, 2.73 beyond the jack pad |
| GNSS | D30.1 at y 5.20 and L30.2 (bias tap) at y 6.18 sit on the line | — |
| GNSS | R304 0 Ω across x (pitch 0.86 mm), then GNSS_RF_IN north to U30.11 (13.71, 10.2) | 3.07 mm |
| GNSS | DNP shunt stubs C303 (west) and C305 (east) | 0.94 mm each |
| Radio | J31 pad 5 (31.54, 2.3) → R316.1 (31.54, 7.6); D31.1 at y 5.20 | 5.30 mm, 3.2 beyond the jack pad |
| Radio | R316 across x, then RADIO_RF north to U31.6 (32.40, 9.05) | 1.45 mm |
| Radio | DNP stubs C313 (west) and C314 (east) | 0.94 mm each |

**Stitching.** GND vias sit 0.85–1.45 mm from the line centre, at each jack leg (24 in all) and at the
module GND pins (6). The fence is 21 vias at y 23.3, pitch 1.4–2.0 mm. Its openings are x 6.3–12.4 (GNSS
leads, FB30 feed) and x 20.0–23.8 (radio lanes). A 121-via lattice (2 mm, staggered) covers the strip on
every layer's GND.

Largest gap between stitching points along each side of each line (the line ends count):

| Run | West | East |
|---|---|---|
| GNSS_RF_ANT | **2.98** | 1.50 |
| GNSS_RF_IN | 1.37 | **2.17** |
| RADIO_RF_ANT | 1.50 | 1.50 |
| RADIO_RF | **2.30** | 1.85 |

**Separation (courtyard to courtyard, mm).**

| From | U2 | L1 | C6 | U3 | U1 | Y1 | U8 | L3 |
|---|---|---|---|---|---|---|---|---|
| U30 | 9.6 | 10.8 | 7.1 | 10.2 | 23.5 | 31.1 | 75.0 | 78.4 |
| U31 | 11.8 | 10.8 | 9.0 | 11.2 | 25.0 | 31.9 | 72.8 | 76.7 |

- U30 to U31 is 7.6 mm.
- The modules are the RF parts nearest each of these; the chain parts sit further aft.
- Every RF part is ≥ 5 mm from U2/L1/C6, U8/L3, the MCU and Y1.

**Interface routes (track copper to the U30 courtyard / to the RF tracks, mm).**

| Net | To U30 | To RF tracks |
|---|---|---|
| RADIO_NSS | 6.72 | 9.33 |
| RADIO_SCK | 5.92 | 10.37 |
| RADIO_MOSI | 5.52 | 8.34 |
| RADIO_MISO_MCU | 5.12 | 8.16 |
| RADIO_BUSY | **4.72** | 6.65 |
| RADIO_NRST | **3.97** | 5.26 |
| RADIO_DIO1 | **3.21** | 9.65 |
| RADIO_RXEN | **4.10** | **3.34** |
| RADIO_TXEN | 7.99 | **1.77** |

- The GNSS lines are ≥ 8.9 mm from U31. To the RF tracks: SAFEBOOT_N (to TP30) 6.4 mm, the UART, TIMEPULSE and
  RESET_N lines ≥ 8.4 mm.
- **Exceptions (bold), all Minor:**
  - BUSY, RXEN, NRST and DIO1 run in the 7.6 mm gap between the modules: BUSY at x 21.2, RXEN at x 20.6,
    and NRST and DIO1 at their B.Cu turns, (19.0, 24.5) and (18.4, 24.0).
  - TXEN and RXEN are U31's own control pins. TXEN's via is at (28.59, 7.8) and RXEN leaves pin 10 at
    (27.3, 9.05). Each lies next to U31's own RF stub, inherent to the module pinout.

## 4. Deviations (each with its reason)

1. **J123 at (36.0, 34.6), not (36.0, 34.5).** At 34.5, pin 1 is 0.1 mm short of clearance to R6's CAM_5V
   branch. At 34.6 it clears by 0.2 mm without moving a supply track.
2. **Module centres moved +0.86 mm in x (U30 10.41, U31 29.86), pi rows laid across x.** Five RF parts in
   series do not fit between the jack and module courtyards along y.
3. **Fence at y 23.3, not 23.5.** The fence vias have to sit inside the strip pours.
4. **Stitching gaps above the target (≤ 2 mm; the handoff's ≤ 1.5 mm).** The gaps are 2.98 mm (GNSS_RF_ANT
   west, where L30 and C302 sit), 2.17 mm (GNSS_RF_IN east, between C305's pad and U30's pad row) and 2.30 mm
   (RADIO_RF west, between the C313/R316 row and U31's pads). The module GND pads close the far end. No via
   fits clear of the chain parts' pads (ViaCheck rules).
5. **B.Cu in the strip carries three radio signals besides the limiter:** the TXEN loop (x 24.5), DIO1's lead
   (x 32.4) and NSS's hop under SCK.
   - All three are outside U31's keep-out, with solid In1 GND above them.
   - `check_r7` lists the allowed nets.
   - Nothing runs under U31 on any layer. Only GND runs on F.Cu/In1 under U30 (DRC rules).
6. **Interface proximity exceptions:** see §3.
7. **Series resistors not at U1.** R313/R315 (SCK/MOSI, 33 Ω) and R306 (GNSS RXD, 220 Ω) sit in the left
   corridor, about 10–12 mm of trace from U1, not at U1: U1's escape rows leave no room.
   - Inference: 10–12 mm is short against the edge rates of these lines.
8. **In2 3V3 band cut to a lobe round FB30's feed via (x 9.9–14, y 23.9–27).**
   - FB31's band via was dropped. FB31 takes 3V3 on a 0.4 mm F.Cu link from R161.1, whose R6 via and 0.25 mm
     In2 trace reach the plane. Calculation (Inference): about 33 mΩ, about 4 mV at 119 mA.
   - Reason: with the band, the displaced east-west links found no way in 12 orders (§5 of the log).
9. **Thirteen non-critical R6 nets redrawn by the grid router (session file):**
   - BUZZ_DRV, BAT_FAULT_N, LOGIC_SOURCE_ST, BAT_SW_SOURCE, BAT_SW_RETURN, LED_RED, LED_YEL, CAM_MCU_TX/RX,
     PULLPIN, PULLPIN_EXT, VLOGIC_SENSE, BAT_ILIM.
   - 12 connections, 8 of them using In2 inside the 3V3 plane, which stays connected (DRC unconnected 0).
   - They are slow nets: LEDs, switch legs, UART, sense lines. The router's layer changes carry no extra GND
     vias.
10. **R6 copper changed by script near U1 and the strip:**
    - QSPI_IO0 now leaves pin 58 inward and runs on B.Cu (the IO1/IO3 pattern).
    - VBUS_SENSE escapes inward and joins its In2 run end to end.
    - C84's GND: three vias at x 9.0 replace its diagonal trace. C80's BAT_IN via joins C96's.
    - R6 GND vias in the strip and on the new leads were removed. New GND vias: (6.85, 40.5),
      (24.15, 28.25), (32.2, 27.033) at R105.2, and (19.55, 27.05) for C6's pad (session).
    - None of these touch pyro, arming, actuator or battery-entry copper (check_actuators OK).
11. **Silkscreen.**
    - GNSS sits on F.Cu, 5–8 mm from J30: the strip vias leave no closer spot. RADIO sits on B.Cu behind J31.
    - TP30 SAFEBOOT runs up the left edge in a lattice window. The lattice skips (0.85–2.05, 10.75–22.65),
      costing about 6 edge vias.
    - J123's pin names are per pin (`1:PULL`, `2:GND`, B.Cu, about 5 mm forward of its pins). The single
      R6-style row found no spot nearer than 12 mm.
12. **D30.2/D31.2 have thermal relief like every small GND pad** (house policy, check_r7).
    - Inference: four 0.3 mm spokes add a little inductance to the ESD return.
13. **Inherited:** one off-angle 3V3 B.Cu segment, (41.35, 58.55)–(42.95, 57.15). It is R6's, translated and
    untouched; R6 had five.

## 5. Open items for step C

- **Fab outputs:**
  1. `tools/jlc_orient.py`: verify placement corrections for the new parts listed in §2.
  2. Then `tools/export_fab.py`, `tools/jlc_stock.py` and `tools/jlc_cost.py`.
  3. `test_fab_validation` then has to pass.
- **ORDERING tab windows.** Measured on this board (courtyard/pad boxes); all meet the ≥ 1.5 mm to parts and
  ≥ 5 mm to capacitor rules:

  | Window | Nearest part | Nearest capacitor |
  |---|---|---|
  | Left x = 0, Y 63–68 | J3, 1.83 mm | C84, 5.23 mm |
  | Right x = 46, Y 62–67 | TP75, 1.95 mm | C11, 6.6 mm |
  | Right x = 46, Y 8–13 | C310, 8.38 mm | C310, 8.38 mm |

  Still open: the forward-end unsupported span (pass1_layout L4), and no rail on the aft edge.
- **JLC remarks / ORDERING §3:**
  - Stackup JLC041611-7628, impedance control optional.
  - The edge copper at the jacks is deliberate (L6).
  - MAX-F10S MSL 4 bake and the T-shaped paste apertures (L7).
  - Both modules top side, reflowed last.
  - SMA jacks need the manual joints (`JLC_Assembly`); SMA pads carry no paste.
- **Docs and requirement text:**
  - REQUIREMENTS F10 power text (pass1_electrical E12) and the P2 board-position / coax loop zone (L3).
  - A STATUS.md row for R7, saying what was and was not verified.
  - The `docs/M3_R7.md` header still says "step A only" in places: check it.
- **Firmware:** the board change invalidates the `m3_firmware/build.py` hash binding. Make an R7 binding per
  AGENTS.md §3.
- **Decide whether to accept:** the three stitching gaps (§4 item 4) and the interface proximity exceptions
  (§3).
- **Tools:** `tools/check_r6.py` stays, because `r6_joints.py` and `test_maze_clearances.py` import it.
  `tools/check.sh` runs `check_r7.py`.
