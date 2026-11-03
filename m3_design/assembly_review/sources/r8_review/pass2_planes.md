# R8 review pass 2: planes and return paths

Reviewer: independent, dimension "planes and return paths". Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d`. I hashed it before and after the review, and it is
unchanged. `git status` is also unchanged by my runs. Read-only: I edited nothing in the repository except this file. The
one trial edit (finding 01) was made on a scratch copy, which I deleted afterwards.

## Verdict

**0 Critical, 0 Major, 3 Minor.**

All four pass-1 findings in this dimension are closed or properly dispositioned. Fix pass 1 caused no plane regression:
- In1 is still one GND outline with no track.
- In2's five regions keep their pass-1 structure.
- Every F.Cu critical track lies over In1 GND, apart from its own antipads and the intended J30 / J31 launch cut-outs.
- The only critical split crossing is still ARM1_SENSE (already recorded).
- Every critical layer change except A8 has a GND via within 1.47 mm.
- The new HSE_OUT via has its GND partner 1.25 mm away, and the crystal's B.Cu guard is intact.
- G7 removed the radio-bus sliver.

The three Minor items:

1. **(Worth fixing.)** The worst unstitched GND piece in C15 is the ground island of U9, the logic eFuse. It holds U9's
   only GND terminal, its ILIM resistor and its dVdt capacitor, and it reaches a GND via only after 14.1 mm of B.Cu copper.
   TI's layout guidance asks for the GND terminal to be tied to the ground plane at the IC.
   - C15's reason ("a 0.5 mm via needs about 0.84 mm of copper") does not hold here: a legal spot exists.
   - One via at (44.6, 87.0) passes DRC on a refilled scratch copy, and cuts U9.8's copper reach to 2.8 mm.
2. **(Worth fixing, records.)** M3_R8 "Ground" still gives fix pass 1's predecessor figures: "90.65 % of the board, one
   slot". The board has 90.54 % and three slots, because J3's legs are now relieved (D89).
3. **(Not worth fixing.)** No gate or record measures copper distance from a GND pad to a via. Apart from U9's island, the
   long ones are J9.2 (the camera return, 6.9 mm), U13.2 / C93.2 (9.3 / 7.2 mm) and Q122.2 / R123.2 (12.4 / 13.0 mm). I
   found no legal via spot that shortens any of them; Q122's pocket lies over the B.Cu BAT_IN neck.

## Gates and tools run (on `6600ef94…`)

| Run | Result |
|---|---|
| `tools/check.sh` | **exit 0**: DRC 0, unconnected 0, parity 0, ERC 0; metadata OK; silk OK; check_r8 OK; route_check r8 0 failing, 3 allowlisted; check_actuators OK; fit OK |
| `m3_design/r8_ground_check.py --report` | all 14 gates OK. reach: board p95 4.48 / max 9.65 mm at (0.25, 88.25); pours p95 2.90 / max 5.89 mm. islands: **20** (pass 1: 18), the one weak island is D4.2's (F, 2.891 mm², 1 via) |
| `tools/reference_audit.py` (R6 set / extended) | 46,845 / 5,186 (11.07 %): own via 3,592, keep-out 1,368, other via 226. Extended: 102,384 / 5,944 (5.81 %). **Equal to M3_R8 "Return paths"** |
| `NO_GATE=1 NO_DC=1 tools/run_survey.sh` | P1 0.9054, P3b 3, P4 5, P6 1782.9 mm, P7 1, P9 / P10 4.48 / 9.65 mm, P11 2.90 mm, R6b 0.1107, S12 25, C6 1. **Equal to R8_VALIDATION's scorecard** |
| Own scripts (pcbnew, read-only, listed at the end) | full critical-net sampling, split crossings on every B.Cu signal net, In1 holes, In2 erosion, island and fill diff against `429b6db4…`, finger pieces at 0.75 / 1.0 mm, GND-pad copper reach |

I compared against the pass-1 board `429b6db4…`, using the copy that pass-1's routing reviewer left in the session
scratchpad (`r8p1rt/r8.kicad_pcb`, hash checked). I read it only.

## 1. Pass-1 findings in this dimension

| Pass-1 item | Status on `6600ef94…` | Evidence |
|---|---|---|
| R8P1-PLANES-01: C11-class fingers unlisted; radio-bus sliver 15.1 mm | **Closed.** The C15 record's reason is inaccurate for one piece; see finding 01 | G7 is a fill-only rule area whose outline lies on the RADIO_NSS / RADIO_SCK_MCU centre lines, from y 30.3 to U1 (`r8_ground.tsv`). The sliver is gone: the F.Cu island it hung on is now 14.06 mm² with its box ending at y 30.29 (pass 1: 20.25 mm², to y 38.6). The fill diff loses exactly 6.19 mm² of F.Cu GND at x 23.76–32.0, y 30.21–38.60. I re-measured C15's counts: R7 method (rings kept, F/B) **11 / 17**; gate method (rings excluded, all layers) **6 / 14**. Both equal C15 |
| R8P1-PLANES-02: reference audit covers 24 of 59 nets; ARM1_SENSE crossing unrecorded | **Closed** (records) | M3_R8 "Return paths" now has a Scope paragraph that names the crossing and the audited net set. I re-sampled all 59 AGENTS §3 nets plus SWD / NRST (0.02 mm, centre and both edges). The one crossing is unchanged: ARM1_SENSE, B.Cu, In2 3V3 → GND at **(18.18, 53.86)**, after 14.52 mm over 3V3. The `--agents3` option was not added. That disposition is acceptable, but after any copper change the full-set sampling must be repeated by hand |
| R8P1-PLANES-03: In2 3V3 is the reference under U1's stubs and the sensors; unrecorded | **Closed** (records) | The M3_R8 "Power" paragraph is present. Its figures still hold: the QSPI B.Cu over 3V3 totals 12.30 mm (CLK 1.14, IO0 0.26, IO1 7.30, IO2 1.08, IO3 1.14, NCS 1.38); SPI1 / IMU_CS 0.40–0.72 mm; ARM1_SENSE_MCU 0.82 mm |
| R8P1-PLANES-04: servo GND return unsolved; J1.2 spokes | **Closed** | `step9/evidence/fix1_dc_gnd.txt` is SHA-bound to `6600ef94…`: R = 0.72 mΩ; In1 carries 85 %; 110 vias carry current, the largest 0.38 A. My independent check of the spokes by conduction: an In1 spoke (0.4 × 0.25 mm, 30 µm) is 0.36 mΩ. At 54 % / 4 of 7.7 A it carries 1.04 A and dissipates 0.39 mW, so its self-heating along a 0.25 mm length is far below 0.1 K (Inference). The record's judgement holds |

## 2. In1

- **Plane.** One GND outline, 4,863.6 mm² (pass 1: 4,869.5), with no In1 track (check_r8 S16 = 0).
- **Holes larger than an antipad** (from a hole scan of the In1 fill inside the outline less 0.55 mm):
  - the J121 / J124 / J1 / J122 barrels;
  - the J30 / J31 launch cut-outs (7.29 mm² each, intended);
  - the SPI1 / IMU_CS four-via cluster (2.95 mm²);
  - **two new J3 relief rings**, each 3.99 mm², at x 5.03–7.59, y 28.43–31.26 and y 35.94–38.77 (D89; P3b 1 → 3, within its ≤ 4 target).
- **Critical F.Cu tracks over a foreign In1 hole.** Edge samples only; no centre line crosses one:
  - RADIO_NRST: 0.60 mm along the 3V3 / CAM_MCU_RX via pair's merged antipad (pass 1: 1.26 mm edge, 0.14 mm centre line). The CAM_MCU_RX hop via moved to (33.95, 44.0), D91.
  - USB_DM: 0.48 mm at VBUS_SENSE's via (16.6, 35.1).
  - QSPI_CLK: 0.46 mm at a 3V3 via (28.75, 45.1).
  - QSPI_IO2: 0.14 mm at QSPI_NCS's via.
- **J3 relief rings.** No USB, CC or SWD track crosses them. The USB lanes leave J3 at y 32.85–34.35, between the two rings.

## 3. In2

- **Region structure, by erosion of the unfractured fills** (unchanged from pass 1):
  - The 3V3 region keeps one core at 0.5 mm erosion; it splits only at necks under 2 mm (the crystal keep-out, U1's east side, the J2 / USB west edge).
  - In2 GND splits at 0.4 mm into the main area plus the south-west pocket (x 0.8–12, y 108.4–117.5) joined by the 0.8 mm strip at x 11.2–12.1. That pocket is tied to In1 by GND vias anyway.
  - The RAW_ACT islands are solid at 1.0 mm erosion.
- **Fill diff against `429b6db4…`.** Only via-antipad moves in the 3V3 region: GND vias round C83's old and new spots, the new HSE_OUT pair, VLOGIC's via. Plus the ACT_FET_S / RAW_ACT chamfers of D85. No In2 structure change.
- **B.Cu signals over In2, every non-power net** (centre line): GND 244.3 mm, 3V3 212.4 mm, BAT_IN 5.3 mm, RAW_ACT 0.8 mm, crystal keep-out 4.6 mm; the remaining 43.2 mm are antipads. The crossings are:
  - ARM1_SENSE (18.18, 53.86), recorded;
  - ACT_GATE at (11.31, 105.97) RAW_ACT → GND and (12.41, 107.07) GND → BAT_IN. This is pass 1's observation, with the coordinates moved by D91's chamfer: a slow actuator gate, inherent to the facing-FET band.
- **RF strip.** In1 and In2 are GND-only for y < 23.75 (sampled every 0.1 mm: 95.5 % / 96.9 % GND, the rest antipads and the launch cut-outs).
- **Buck switch nodes.** SW_NODE, CAM_SW, BST and CAM_BST lie 100 % over In2 GND, and no signal track comes within 1.5 mm of them except their own BST nets and 3V3.

## 4. Critical-signal references and layer changes

- **F.Cu.** Every AGENTS §3 critical net, plus SWDIO / SWCLK, runs over In1 GND, apart from its own antipads and the J30 / J31 launch cut-outs (GNSS_RF_ANT and RADIO_RF_ANT, 2.32 mm each, In2 GND below). Fully referenced with no via: USB_DP 17.6 mm, USB_DM 19.2 mm (D91's 45° redraw), SWDIO 20.2 mm, SWCLK 16.0 mm, and all radio interface lines.
- **B.Cu over In2 GND.** PYRO1_CONT 45.1 mm, PYRO1_GATE_N 36.9 mm, ARM1_SENSE 36.9 mm, RADIO_TXEN 21.8 mm, and the limiter nets.
- **B.Cu over In2 3V3.** As in section 1 (PLANES-03).
- **B.Cu over the crystal keep-out.** HSE_IN 2.92 mm and HSE_OUT 1.68 mm, with In1 GND about 1.26 mm above (JLC041611-7628 stack-up as modelled in `dc_solve`).
- **Critical vias** (28): nearest GND via or plated GND hole 0.71–1.47 mm, except A8 (PYRO1_GATE in TP122, 2.72 mm, allowlisted).
  - New or moved since pass 1: HSE_OUT (24.69, 47.5) with GND 1.25 mm; GNSS_LNA_EN / GNSS_VCC_RF at y 8.3 with GND 1.10 / 1.22 mm.
  - NRST's (24.0, 51.1) is 2.93 mm from GND, but NRST is not an AGENTS §3 net.
- **B.Cu over a foreign In2 antipad** (every net):
  - SPI1_SCK over the IMU_CS / SPI1_MOSI via antipads (0.20 + 0.42 mm; C12 #11 / #14, the U4 pitch). This is within M3_R8's "226 other-via samples".
  - PULLPIN_EXT edge along the antipad of grid via (10.05, 75.3), 0.5 mm. It is a DC external line and not critical; the same as pass 1.

## 5. Crystal, QSPI, SPI, USB, SWD

- **Crystal.**
  - D86 moved HSE_OUT's via to (24.69, 47.5), between Y1.3 and C26.1. The B.Cu now runs straight Y1.3 → via → C26.1 at y 47.5, inside `Y1_In2_keepout`. Its GND partner (24.69, 46.25) joins F.Cu, In1 and B.Cu GND fill.
  - The B.Cu guard (rendered) still floods round Y1 and between its pads. Y1.2 / Y1.4 are solid; C25.2 / C26.2 have reliefs, with stubs to the vias (18.75, 49.7) / (26.95, 47.5). Eight GND vias lie within 2.3 mm of the crystal pads.
  - U1's VSS pin 10 (21.5, 52.55) reaches the guard's via (21.0, 51.1) through the F.Cu fill, 1.53 mm away, so the oscillator return loop is compact.
  - HSE_OUT's F.Cu diagonal (23.0, 49.19) → (24.69, 47.5) runs under U1's body over In1 GND.
- **QSPI / SPI1.** Unchanged from pass 1 (section 1 and the pass-1 table): stubs 0.26–7.3 mm, a GND via 0.78–1.47 mm from each dive, 3V3 bypass 1.7–3.2 mm (QSPI).
- **USB.** DP / DM run on F.Cu over solid In1 from J3 to U1.
  - D91's DM redraw separates DM from DP for about 3 mm east of D4. The triangle it encloses lost its F.Cu GND fill (2.48 mm², an island with no via, removed by the fill). In1 below is solid. USB is full-speed on the H743's internal PHY, so the pair spacing is not impedance-critical (Inference).
  - D4.2's ESD return is still D63's single via (9.0, 33.8), 0.85 mm away. C83.2 and U10.2 also reach it, but each of them also has its own B.Cu fill contact (C83.2: 0.53 mm² of fill within 0.05 mm of the pad).
- **SWD.** F.Cu over In1 GND for its whole length, with no via.

## 6. GND pours: islands, fingers, stitching

- **Islands.** F.Cu has 12, B.Cu 8. The two new F.Cu islands are the pours on either side of J3's relieved legs: (6.06–13.66, 34.60–38.65) with 2 vias, and (6.06–20.48, 28.45–35.39) with 5 vias. With solid legs, the leg pads used to merge them into the west pour. Every island has ≥ 2 GND vias or plated GND holes, except the D4.2 pocket (D63 / D68).
- **D63 / D64.** Re-measured, equal to the record: P7 = 1 (2.891 mm², 1 via); P9 / P10 4.48 / 9.65 mm against floors of 4.32 / 9.42 mm; the maximum at (0.25, 88.25), under the triple-layer RAW_ACT band where In1 is the only GND. The dispositions hold.
- **Fingers (C15).** Counts as in section 1. Worst copper distance per piece (0.1 mm raster, whole-layer reach to 40 mm):

  | Layer | Box (x; y) | Width class | Max copper distance | What it serves |
  |---|---|---|---:|---|
  | B.Cu | 42.05–45.5; 82.44–87.27 | < 1.0 mm (rings kept) | **14.8 mm** | **U9.8 (eFuse GND), R84.2 (ILIM), C81.2 (dVdt)**: finding 01 |
  | B.Cu | 33.55–40.5; 47.7–53.93 | < 1.0 mm | 11.1 mm | U13.2, C93.2 (camera IO LDO) |
  | F.Cu | 19.82–43.37; 98.66–99.51 | < 1.0 mm | 10.5 mm | guard between BAT_ENABLE and RAW_PROTECTED in PYRO_BLOCK |
  | In1 | 0.5–5.88; 91.88–107.74 | < 1.0 mm | 10.0 mm | west edge under the RAW_ACT band (no load) |
  | B.Cu | 43.75–45.5; 57.11–64.0 | < 1.0 mm | 7.1 mm | east edge |

- **Stitching.** P11 2.90 / 5.89 mm. The strip fence and strip reach pass check_r8. 191 step-7 vias, matching `r8_ground.tsv`.

## 7. GND-pad copper reach (new measurement)

The gates measure the Euclidean distance from pour points to vias (P9–P11, D62's cover), and route_check measures copper
distance only for pieces under 0.5 mm. Neither asks how far an IC's or connector's GND pad is, through copper, from a via.
`gndpads.py` computes that for every GND SMD pad (route_check's own `reach`, 0.1 mm raster; spot checks at 0.05 mm):

| Pad | Layer | Copper distance to nearest GND via / plated hole | Current it carries |
|---|---|---:|---|
| **U9.8** TPS259470 GND | B | **14.06 mm** | bias and IC reference (TI: quiet ground for ILM / dVdt / ITIMER) |
| **R84.2** ILIM 750 Ω | B | **12.81 mm** | ILM bias |
| R123.2 / Q122.2 (actuator gate drive) | F | 12.98 / 12.42 mm | gate charge of Q120 / Q121 |
| U13.2 TPS70933 GND / C93.2 | B | 9.28 / 7.24 mm | camera IO LDO, mA |
| C81.2 dVdt | B | 8.64 mm | soft-start charge |
| J9.2 camera GND | F | 6.92 mm | camera return, up to the 1 A supply (M3_R6) |
| R102.2 | F | 5.32 mm | — |
| U1 VSS pins | F | 1.8–2.8 mm | — |
| every other GND SMD pad | F / B | ≤ 4.3 mm | — |

## 8. Findings

### R8P2-PLANES-01: Minor, worth fixing
**U9's ground island (U9.8 GND terminal, R84.2 ILIM and C81.2 dVdt returns) reaches a GND via only after 14.1 mm of
B.Cu copper. C15 lists the piece as a finger "by BAT_ILIM / R84" with a "no via fits" reason, but a legal via spot exists.**

- **Requirement.** TI TPS25947 data sheet SLVSFC9C (revised May 2026), §8.4.1 Layout Guidelines
  (https://www.ti.com/lit/ds/symlink/tps25947.pdf):
  - "The GND terminal must be tied to the PCB ground plane at the terminal of the IC with the shortest possible trace … TI
    recommends to have a separate ground plane island for the eFuse … connected to the system power ground plane using a
    star connection."
  - "Take care to minimize the loop area formed by the bypass-capacitor connection, the IN terminal, and the GND terminal
    of the IC."
  - REQUIREMENTS M2 "every review-only residual is listed, with … measured reason". C15's reason is inaccurate for this
    piece.
- **Evidence** (pcbnew on `6600ef94…`):
  - U9 (TPS259470LRPWR, B.Cu) has one GND pad, U9.8 at (42.4, 85.275). R84.2 (GND) is at (43.8, 86.075) and C81.2 (GND)
    at (44.68, 83.125). The three sit in one B.Cu GND strip bounded by:
    - the RAW_PROTECTED B.Cu trunk at x 41.75 (y 80–85.5) to the west;
    - the board edge to the east;
    - BAT_DVDT (y 84.675) and BAT_ILIM ((43.0, 85.725) → (43.0, 86.925) → (43.8, 87.725)).
  - **The only GND vias in x 41.9–46, y 73–88.5 are (43.51, 74.2), D9.2's, and (42.9, 87.6).** (42.9, 87.6) lies
    south-west of BAT_ILIM's diagonal, in C88's piece.
  - Copper distance to a GND via (route_check `reach`, 0.05 mm raster): **U9.8 14.06 mm, R84.2 12.81 mm, C81.2
    8.64 mm**. The same figures appear on `429b6db4…`, so this was not introduced by fix pass 1.
  - U9's IN bypass C88 (100 nF; C88.1 BAT_IN (41.25, 87.6), C88.2 GND (42.09, 87.6)) returns through the via
    (42.9, 87.6), 0.35 mm of copper away. Its loop to U9.8 therefore closes through about 12 mm of In1 and back along the
    14 mm strip, not "closest to the IN and GND terminals".
- **Why no gate or record caught it.**
  - D62's cover step judges Euclidean distance: (42.9, 87.6) is about 2 mm from U9.8 as the crow flies.
  - route_check's `pour_finger` sees nothing under 0.5 mm here once the relief rings are excluded.
  - C15 records the piece (14.8 mm), but its reason, "a 0.5 mm via needs about 0.84 mm of copper between its
    neighbours", is not true here. "Not searched one by one" left this spot unfound.
- **A legal spot.** (44.6, 87.0), east of R84:
  - GND fill on F.Cu, In1, In2 and B.Cu at the point.
  - 1.4 mm from the outline; outside PYRO_BLOCK (x ≤ 42); no panel tab nearby (right tabs y 8–13, 18–23, 105–110).
  - Ring clearances: 0.22 mm to R84.1 (BAT_ILIM), 0.35 mm to R84.2, 1.8 mm to the nearest GND via.
  - My approximation of D62's rules found 28 legal centres round (44.45–44.65, 86.8–87.25).
  - **Trial on a scratch copy** (one 0.5 / 0.3 mm GND via at (44.6, 87.0), native `ZONE_FILLER`, then deleted):
    - kicad-cli DRC: 0 violations other than the scratch folder's missing footprint library, 0 unconnected;
    - `route_check --profile r8`: 0 failing;
    - check_r8: only LS120's 3D-model check failed, because `kilib` was not copied;
    - **U9.8 14.06 → 2.77 mm, R84.2 12.81 → 0.78 mm, C81.2 8.64 → 3.78 mm**;
    - the 14.8 mm piece leaves the top of the C15 list.
- **Effect.** Inference: functionally small today.
  - ILM and dVdt return to U9.8 through the same island over about 2 mm, as TI asks, so the current-limit setpoint is
    unaffected.
  - The DC offset between U9.8 and the plane is µV: the bias is under 1 mA, and the strip is about 10 mΩ.
  - The remaining exposure is high-frequency: the IN–GND bypass loop is enlarged, and the IC's reference is star-tied at
    the OUT clamp D9's via rather than at the IC.
  - Nothing here can fire a channel. The cost is a margin on the logic supply's protection IC.
- **Fix.**
  1. Add one GND via at (44.6, 87.0) through `step7/make_ground.py`. Two ways:
     - a "return U9.8" row, like stage 2's power returns;
     - better, a stage-2b rule: every GND pad of an IC (≥ 4 pads) whose copper reach exceeds 4 mm gets the legal spot
       nearest it.
  2. Regenerate `r8_ground.tsv` and rebuild.
  3. Update C15, with the piece gone and the pads each remaining piece serves, and add one line in M3_R8 "Power" citing
     §8.4.1.
  4. This is a copper change: the deviation list's binding moves to the new SHA, which pass 3 needs anyway.

### R8P2-PLANES-02: Minor, worth fixing (records)
**M3_R8 "Ground" states In1 as "90.65 % of the board, one slot". Fix pass 1 made it 90.54 % and three slots.**

- **Requirement.** REQUIREMENTS M2 / AGENTS §3: records state the board as built. R8_VALIDATION already gives the new
  figures, so the two records disagree.
- **Evidence.**
  - `docs/M3_R8.md` line 141: "In1 is one GND plane (90.65 % of the board, one slot)".
  - Survey on `6600ef94…`: P1 0.9054, P3b 3. The two new In1 slots are J3's leg 1 / 4 relief rings, 3.99 mm² each
    (D89).
  - R8_VALIDATION's scorecard rows P1 / P3b say this correctly.
  - The outer GND island count also rose from 18 to 20, because J3's relieved legs split the west F.Cu pour into pieces
    with 2 and 5 vias. That count is stated nowhere and needs no change, but the Ground paragraph could name it.
- **Fix.** Change the sentence to "90.54 % of the board; three slots: the SPI1 / IMU_CS via cluster and the relief rings
  round J3's legs 1 and 4 (D89)".

### R8P2-PLANES-03: Minor, not worth fixing
**No gate or record measures copper distance from GND pads to a via. Besides U9's island (finding 01), J9.2 (camera
return) is 6.9 mm, U13.2 / C93.2 9.3 / 7.2 mm and Q122.2 / R123.2 12.4 / 13.0 mm. None of these can take a legal via.**

- **Evidence.** Section 7.
  - J9.2's F.Cu pocket is boxed in by CAM_RX_WIRE, J9.1's CAM_5V stub and the RAW_PROTECTED F.Cu trunk at x 42.15. My
    spot search finds no legal centre in x 37.5–41.8, y 41.5–45.5. C8 already lists the companion: the CAM_5V feed via
    (40.75, 41.4) has no GND via within 2.94 mm.
  - In U13's B.Cu piece, the legal spots at y ≥ 53 do not join U13.2's copper (the simulated reach is unchanged).
  - Q122's F.Cu pocket (x 17–20, y 98.7–103.5) lies over the B.Cu BAT_IN neck (the 7.00 mm D12 cut). D62 forbids
    antipads there, so this is part of D64's accepted trade.
- **Effect.** Inference: small.
  - J9.2's up to 1 A camera return crosses a pocket about 1–1.5 mm wide: about 3 mΩ, 3 mV.
  - U13 and Q122 carry mA or gate charge.
- **Fix (optional, records).** Add a "GND pad copper reach" line to `m2_sweep.py` (route_check `reach` from each GND
  pad), and name in C15 the pads each listed piece serves, so that a future copper change shows these figures.

## 9. Observations (not findings)

- **ARM1_SENSE over 3V3** (14.5 mm, D47 exemption).
  - Inference: the coupling into the 0.9 kΩ divider node is small. The trace-to-plane capacitance is about 0.6 pF, which
    is about 26 kΩ at 10 MHz.
  - It stays recorded (PLANES-02).
- **D4.2's single ESD-return via** (D63 / D68). The path is a 0.85 mm × 0.2 mm track plus the via, about 0.35 nH
  (Inference), which adds roughly 10 V for 1 ns at an IEC 8 kV contact strike. The USB port is a bench interface. D63's
  two-via alternative was rejected for clearance; no change is proposed.
- **G7 and the radio bus.** RADIO_NSS and RADIO_SCK_MCU now run 1.041 mm apart for about 12 mm with no GND between them.
  Inference: the edge gap is 0.84 mm at h = 0.21 mm, so the crosstalk onto NSS is at most a few percent. The removed
  sliver was not a shield anyway, being 15 mm of copper from a via.
- **J3 relief rings.** They add a little inductance to the shell legs. They keep REQUIREMENTS M2's THT-relief rule, and
  the spokes are not starved (DRC passes).

## Method and scripts

The scripts are in the session scratchpad, `p2planes/`, and are read-only on the board. One trial copy was made under
`p2planes/trial/` and deleted after use.
- `zones.py`, `islands.py`, `filldiff.py`: zone inventory, outer and inner GND islands with their via counts, and the fill
  diff against `429b6db4…`.
- `refall.py`: the reference of every AGENTS §3 critical net plus SWD / NRST, with split crossings.
- `splitall.py`, `b_over_antipad.py`: B.Cu signal crossings and foreign antipads.
- `in1holes.py`, `necks.py`: In1 holes, and In2 erosion of the unfractured fills.
- `critvias.py`: critical vias with their nearest GND via and the In2 net round them.
- `fingers.py`: route_check `pour_pieces` at 0.75 / 1.0 mm, with and without rings, and the whole-layer copper distance.
- `gndpads.py`, `padreach.py`, `reachmap.py`: GND-pad copper reach.
- `viaspot.py` / `viaspot2.py`, `simvia.py` / `simvia2.py`: approximate D62 legal-spot search, and the simulated reach
  with an added via.
- `plot.py`: copper renders (crystal, U9, J9, Q122).
- The TI datasheet was fetched from the URL above and read with `pdftotext` (§8.4.1, p. 62–63). The copy was deleted.
