# Round 18 — routing cleanliness and AVA-likeness (Claude)

**0 Critical / 0 Major / 6 Minor (3 new, 3 carried).** Commit `dcbb6c8`, PCB
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982` before and after (unchanged).
Official KiCad 10.0.7 DRC (all severities, schematic parity) is 0 violations / 0 unconnected / 0 parity;
`route_check --profile r10 --routes --bumps-all` exits 0 (140 information instances, 6 noncritical leftovers).
Full data: [round18_routing.json](round18_routing.json); probe scripts and renders in `.supervisor/r18_routing/`.

## What the board does well

All 951 segments are octilinear, with no acute turns or staircases. Only 7 A-B-A jogs exceed the gate's thresholds
(offsets 0.36–0.63 mm). Of the 15 segments shorter than 0.3 mm, 12 sit inside pads or are via-alignment kinks.
Buses are grouped: four SD lanes, one via per QSPI line, four servo lanes and paired UARTs. In1 is one solid GND
plane, and every F.Cu fast run sits over In1 GND. The crystal sits on an In2 GND island. Every required critical layer
change has a GND via within 1.5 mm (worst 1.492 mm).

## Findings

**R18-RTE-01 — Minor, new: the In2 3V3 plane is cut into three pieces.** The In2 USB_LIMITED track (0.4 mm, 63.6 mm)
and the In2 3V3A track (0.25 mm, 11.4 mm) run 0.65 mm apart under U1's south pin row and down x = 26.2. Together they
split the saved 3V3 fill into three pieces:

- main, 1354.2 mm²;
- an island of 63.1 mm² at (17.71–25.75, 51.30–61.35);
- a finger of 30.5 mm² at (22.0–23.7, 62.25–81.7).

At x = 24 there is no 3V3 copper from y = 48.82 to 51.30; only the two tracks cross that band.

The island holds U1 pin-11 (VDD) decoupling C14 and the LS120 buzzer supply. Its only copper link to the main plane is
the B.Cu 0.3 mm trace (22.6,52.15)–(21.82,52.15)–(21.82,51.47)–(19.5,49.15), 4.741 mm long. In parallel, current can
also pass through U1's pin 11 and internal VDD ring (Inference).

The finger joins the main plane only through the buck output node (via (23.1,78.1) → L1.2 → (26.4,79.26) → F.Cu →
(30.8,79.26)). It carries U2's FB, 0.203 mm under SW_NODE and BST. Diodes DS41326 p15 asks for feedback parts close to
FB and a GND layer under the device; the SW-to-FB coupling here is an Inference.

Slow nets ride the slots with no In2 copper beneath them: USB_FAULT_N for 6.6 mm at x = 9.3, V3V3_SENSE for about
4.6 mm at x = 25.93, and BAT_FAULT_N; I2C1_SDA, BARO_SDO, CC1 and VBUS cross them. K-region merges fills by net name, so
it cannot see any of this. D-AVA-01 describes "contiguous rail regions"; R14 only noted the three pieces in passing.

**Fix:** re-plan In2. Move the USB_LIMITED south leg into the existing 3V3/CH1-GND boundary gap or onto an outer
layer. Feed R87 from the C98/U11.7 side instead of the In2 branch (26.2,61.8)–(22.0,62.25). Take 3V3A off y = 50.2.
Then refill and require one 3V3 piece. Gate: report rail fill pieces and make K-region piece-aware.

**R18-RTE-02 — Minor, new (gate gap): layer-change return.** Of the 25 required critical-signal vias, 21 have an In2
power rail on the B.Cu side (3V3 ×17, PORT_4V8 ×4); only the HSE and pyro vias sit over In2 GND. B.Cu is 0.203 mm from
In2 and about 1.26 mm from In1, so the B.Cu return runs in the rail. The gated GND via (0.77–1.43 mm away) does not
connect In1 to that rail. The nearest rail-to-GND capacitor is 1.29–6.19 mm away:

- SD_MISO 6.19 mm, SD_SCK 5.33, SD_MOSI 5.07, SD_CS 4.84 (all to C17);
- SPI1 5.04–5.77 and QSPI_NCS 5.32;
- RADIO_TX 5.12; 12 of the 21 are beyond 4 mm.

The SD lines run 21–33 mm each on B.Cu over 3V3. The In1–In2 sheet capacitance (about 3.8 pF/cm²) is too small to
carry the return instead. D-R2-10 itself rests this AC-reference role on bypass capacitors (Inference), and no gate
measures how close those capacitors are.

**Fix:** add a counted review rule that reports the via-to-rail-capacitor distance and lists these 21 instances. A
clearance screen found room for a 100 nF 0402 3V3–GND at B(11.25,41.25); it would bring the SD cluster to 2.3–3.4 mm.
This is not fix-now.

**R18-RTE-03 — Minor, carried (R17-RTE-02) with new per-net evidence: detours and extra vias outside the gate.** The
114 non-pour nets total 1454.6 mm against an octilinear MST of 1194.3 mm (1.218×, +260 mm). The top ten nets account
for 136 mm of that, and 17 vias above need sit on 11 nets.

| Net | Routed / MST (mm) | Vias / needed | Cause |
|---|---:|---:|---|
| USB_LIMITED | 81.7 / 53.5 | 3 / 1 | In2 detour around U1 |
| BAT_IN | 59.6 / 39.0 | 1 / 1 | 7.23 mm 1.0 mm U-loop to the board edge around C95.2; hot-plug-qualified |
| NRST | 39.7 / 25.3 | 3 / 1 | 13.8 mm of F.Cu inside U1's pad ring; 11 bends |
| USB_FAULT_N | 37.2 / 23.3 | 1 / 1 | U-turn around the SD vias |
| BAT_FAULT_N | 51.0 / 38.8 | 3 / 1 | pin map / placement |
| PYRO1_OUT | 33.1 / 22.0 | 1 / 1 | 17.9 mm sense branch |
| SD bus | +6.6 to +9.3 each | 1 / 1 | pull-ups R460–R463 north of J430: 7.9–9.7 mm stubs |
| CAM_IO_3V3 | 25.1 / 15.9 | 2 / 1 | |
| VBUS_SENSE | 25.3 / 18.4 | 3 / 1 | |
| BAT_ENABLE | 27.9 / 23.4 | 3 / 1 | 3.2 mm B.Cu hop (19.675,66.4)–(21.3,68.9) |

A diagnostic octilinear router, with placement and every other net fixed, recovers only a few millimetres per net:

- USB_FAULT_N −8.2 mm (its via must go to about (13.65,42.7), beside R32);
- VBUS_SENSE −4.7 mm and two vias; BAT_ENABLE −2.6 mm and two vias;
- SD lines −2.0 to −3.6 mm each;
- NRST −9.8 mm, but only by threading U3's pins.

So most of the excess comes from placement and the pin map. R10_VALIDATION §6 lists only counts.

**Fix:** add this table to the deviation list. AVA-level directness needs re-placement:

- move the SD pull-ups next to the bus;
- rotate the input-capacitor column (requires F9-1 hot-plug re-extraction);
- nudge R32 for USB_FAULT_N;
- redraw BAT_ENABLE and VBUS_SENSE with a single via each.

**R18-RTE-04 — Minor, carried (R17-RTE-01): SD_MOSI.** On B.Cu, replacing (20.1,32.8)–(20.1,27.7)–(21.6,26.2)–
(25.005,26.2)–(25.005,24.3) with (20.1,32.8)–(25.005,27.894999)–(25.005,24.3) saves 1.995 mm and two segments. It is the
only window that survives an independent whole-board fixed-anchor redraw screen (minimum clearance 0.79 mm).

**R18-RTE-05 — Minor, new: the USB pair is not coupled.** D+ and D− run on F.Cu at 1.90 mm centre spacing over x
11.1–15.85, with the VBUS via (11.95,30.6) and a GND via (15.6,30.5) between them, and 0.707 mm apart on the diagonals.
The J3-to-U1 trunks differ by 1.75 mm (16.45 vs 14.70 mm). This is benign at full speed (Inference), but it is not a
hand-quality pair.

**Fix:** move the two vias, then route DP alongside DM at 0.4 mm. This is not fix-now.

**R18-RTE-06 — Minor, carried (R17-RTE-03): B.Cu under the U4 body.** Fresh measurements: IMU_CS 0.760 + 0.092 mm,
SPI1_MISO / IMU_INT1 / 3V3A 0.325 mm each. TN1383 is cited as in R17; it was not re-read, because the fetch timed out.

## Fix now

1. **SD_MOSI** (R18-RTE-04). Exact geometry above, through `r10_route_sd.py`. Zero risk, and R16 qualified a saved
   copy.
2. **Checks and records only, board byte-identical (allowed by D-R16-03):**
   - an In2 rail-piece report and a piece-aware K-region (R18-RTE-01);
   - the via-to-rail-capacitor report (R18-RTE-02);
   - the per-net detour/extra-via table in R10_VALIDATION §6 (R18-RTE-03).

These need re-planning rather than a fix now: the In2 re-plan, the stitching capacitors, SD pull-up relocation, the
input-capacitor column, the USB pair, and the R32 nudge.

## Rejected or closed

- BUZZ_G, PYRO1_GATE, QSPI_IO3, ACT_FET_S and 3V3A local redraws: each breaks a T-junction, creates an acute junction,
  drops to 0.150 mm on a fast bus, or touches a qualified bridge.
- U11 0.3 mm GND exits leave through the long edge of corner pins, so there is no bridging.
- The 0.28 mm² F.Cu GND sliver touches the U1.74 GND pad.
- In1 merged antipads are 1.6 mm² or less.
- J430 has no copper keep-out (Molex SD-47219-001).
- ACT_EN_MCU runs 12.4 mm beside BAT_FAULT_N at a 0.20 mm gap; the coupling is negligible (Inference).
- The outer GND pour is at most 12.3 mm from a stitch, at the empty east edge (observation only).

## Limits

This was a CAD and geometry review only: no build, check.sh, simulation, field solve, firmware or physical test. The
router and redraw screen check copper, edge, NPTH and keep-out clearance only; apart from SD_MOSI, their results are
indicative, not qualified. The capacitor spot was screened for clearance only. AVA copper and stack-up are unknown and
nothing about them is inferred. No peer round18 material was opened.
