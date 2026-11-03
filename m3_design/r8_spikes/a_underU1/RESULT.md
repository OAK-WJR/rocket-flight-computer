# R8 spike (a): under U1

**Verdict: the primary approach passed.** The flash (U3) and the crystal (Y1) sit on the bottom under U1, with U1 at rotation 0. The decoupling and the QSPI, HSE, NRST and ARM1_SENSE dives route on a scratch board built from R7 with the rigid copper present:
- DRC: 0 items on the spike's nets and parts;
- route_check: 0 failures on the spike's nets;
- all 12 rigid hash groups equal R7's.

The fallback (flash on top) was not needed and was not tested.

Scratch only: no repository file outside this folder was changed, and nothing is committed.

## Files (this folder)

| File | Role |
|---|---|
| `spike_geom.py` | **The geometry to reuse:** `PLACE` (parts), `KEEPOUTS` (In2 under Y1), `copper()` (every track and via, as polylines) |
| `spike_build.py` | Scratch builder: R7 → R8 netlist → rigid copper only → seed placement (`b0_place_final.tsv`) plus `PLACE` → zones → `copper()` → native fill in the project folder → `m3s.kicad_pcb`. KIID seed 8301 |
| `spike_verify.py` | Gate on a scratch board: `check_r8.rigid()`, the kicad-cli DRC filtered to the spike's nets and parts, and route_check filtered to the spike's nets |
| `spike_diff.py` | Diff of DRC, unconnected items and route_check between the seed board (`--no-routes`) and the spike board. It catches anything the spike copper does to other nets |
| `run_verify.sh` | Build plus DRC plus route_check plus verify |
| `render.sh` | Cropped layer PNGs, for review only |
| `b0_place_final.tsv` | Seed placement, copied from the survey scratchpad (`partial/`) |
| `PROGRESS.md` | Log |

**Reproduce** (about 10 s):

```bash
S=<scratch>; A=m3_design/r8_spikes/a_underU1
git show 431025d:m3_design/assembly_review/m3.kicad_pcb > $S/r7.kicad_pcb
$A/run_verify.sh $S/seed --build $S/r7.kicad_pcb    # with spike_build --no-routes for the true seed baseline
$A/run_verify.sh $S/final --build $S/r7.kicad_pcb   # SPIKE PASS
python3 $A/spike_diff.py $S/seed $S/final
```

Two builds give the same file: SHA-256 `3d922707…8df1`.

## Verification (final board)

| Check | Result |
|---|---|
| Rigid groups (`check_r8.rigid`) | 12/12 equal R7: outline, m3_holes, j122_tie, j1, pyro_block_area, ch1_parts, ch1_copper `94128319…`, strip_parts, strip_rf_copper, strip_gnd, strip_rule_areas, strip_gcpw `8b46f569…` |
| DRC (kicad-cli, `--severity-all --all-track-errors`), spike nets and parts | 0. The 33 silkscreen and library-link items are not counted: silkscreen belongs to the post step, and the scratch folder has no footprint library table |
| DRC against the seed board, all nets | 0 new violations. 2 resolved: the dangling ARM1_SENSE exit via, and the then-unfed In2 3V3 zone |
| route_check (profile r8), spike nets | 0 failures, 0 leftovers. Information only: NRST `pad_end_offcentre` at J2.3 (deliberate, see NRST below) and VCAP2 `power_via_no_gnd` |
| route_check against the seed board, all nets | 0 new failures. New information items: 8 × `power_via_no_gnd` on 3V3, 3V3A and VCAP vias, and the J2.3 entry |
| check_r8 against the seed board | Only change: the two C29 findings are gone (C29.1 is 1.87 mm from U3.8, direct route 1.87 mm). No new finding |
| check_r8 F10 separation | No RF part within 5 mm of U3, Y1 or any QSPI/HSE copper. The nearest QSPI copper to an RF part is U1.58 (a fixed pin) to R315, 6.14 mm |
| Clearance probe (extra 0.2 mm DRC rule on the spike nets, pours excluded) | Every spike item ≥ 0.20 mm from foreign copper. The three items under 0.2 mm are R7 geometry: the rigid exit via (18.18, 91.30) to the rigid block GND track, 0.173 mm; and the block's In2-link vias to R7's two GND vias, restored at R7's positions, 0.171 mm |

## What the real build should reuse (`spike_geom.py`)

**Common:**
- Signal width is 0.2 mm everywhere, and vias are 0.5/0.3 mm.
- Every track ends on a pad centre or a via centre, except J2.3 (see NRST).
- The B.Cu runs under U1 sit over the continuous In2 3V3 plane, except at the Y1 keep-out.

### Flash U3
**Placement:**
- (22.6, 43.2), rotation 90, bottom (the seed).
- West row pins 1–4 run forward to aft: NCS, IO1, IO2, GND. East row pins 5–8 run aft to forward: IO0, CLK, IO3, VCC.

**The six dives (each one via, each with a GND via within 1.5 mm):**

| Net | Route |
|---|---|
| NCS | F.Cu from pin 92 to a via west of U3.1 at (17.5, 45.1), then B.Cu. R10 (16.7, 44.67) pulls up beside the via; its 3V3 via at (16.7, 43.25) also feeds C23 |
| IO2 | F.Cu from pin 1 down the west side at x 17.0, then x 18.1 (east of the NCS via), to a via west of U3.3 at (17.5, 42.57) |
| IO1 | Pin 59 stub to a via at (25.0, 39.4), then B.Cu diagonally under the flash body into U3.2 from inside |
| IO0 | Pin 58 to a via aft of U3.5 at (26.13, 40.55) |
| IO3 | F.Cu from pin 60, round the IO1 and IO0 vias, diagonally over the flash to a via east of U3.7 at (27.75, 43.83) |
| CLK | F.Cu from pin 36 along x 29.3 (0.35 mm from the east pad row, so no pour sliver forms) to a via east of U3.6 at (27.75, 42.57) |

**GND vias:**
- (17.5, 41.3) on U3.4;
- (28.6, 43.2) for IO3 and CLK;
- (25.5, 40.0) for IO0 and IO1;
- (16.8, 45.9) for NCS.

**Flash decoupling:** C29 at (28.0, 45.52), rotation 270. U3.8 to C29.1 is 1.87 mm on B.Cu, with a 3V3 via at (28.75, 45.1).

**Totals:** QSPI is 49.5 mm with 6 vias (R7: 151 mm, 11 vias; plan estimate about 50 mm, 6 vias). Per-net ratios run from 1.00 to 1.38.

### Crystal Y1
**Placement:**
- (22.85, 48.6), rotation **90** (seed: 0), bottom.
- Pad 1 (HSE_IN) fwd-W (22.0, 49.7); pad 3 (HSE_OUT) aft-E (23.7, 47.5); pads 2 and 4 are GND.
- In2 keep-out (18.9–26.8, 46.3–50.95) under Y1, C25 and C26 (R5 V1).

**HSE_IN:**
- Pin 12, 0.5 mm stub, then a 45° step into pin 11's column, to a via at (22.0, 51.1).
- B.Cu straight down into Y1.1, then on to C25.1. C25 sits at (19.95, 49.7), rotation 180, outside Y1's 4.7 × 4.0 mm courtyard.

**HSE_OUT:**
- Pin 13 F.Cu straight aft over the crystal (In1 GND between them) to a via at (23.7, 46.35).
- B.Cu into Y1.3, then on to C26.1. C26 sits at (25.75, 47.5), rotation 0.

**GND vias:**
- (21.0, 51.1) and (22.65, 46.35), one within 1.5 mm of each HSE via;
- (18.75, 49.7) and (26.95, 47.5) at the load-cap GND pads.

**Lengths:** HSE_IN 4.7 mm and HSE_OUT 9.3 mm, including the cap branches; pin to crystal pad about 2.5 mm and 7.6 mm. 2 vias.

### NRST
**Route:**
- Pin 14 steps 45° into pin 15's column, to a via at (24.0, 51.1).
- C24 (25.75, 51.1) sits right beside the via.
- B.Cu runs west along y 51.95, just inside the forward pad row, then diagonally to (12.0, 47.85), west to x 7.6, and south to a via at (7.6, 42.6) west of J2.
- An F.Cu stub enters J2.3.

**The J2.3 entry:** the stub ends at (8.65, 42.6), 0.215 mm off the pad centre, because J2's footprint keep-out spans the pad centres. R7 did the same (43.85 for 43.635).

**Totals:** 27.7 mm, 2 vias. NRST is not a critical net.

### ARM1_SENSE (the inherent crossover)
**Series resistor:** R170 at (28.0, 47.93), rotation 90, at pin 33. Pin 33 runs F.Cu to a via at (29.3, 47.5) (GND vias (28.6, 46.6) and (29.2, 48.2)), then B.Cu into R170.2.

**The lane, all on B.Cu, no new via:**
- R170.1 north along x 28.0;
- 45° to y 52.45;
- **west under the forward pad row** to x 18.83;
- 45° to x 18.18;
- **one straight run** to the rigid exit via (18.18, 91.30).

**Lengths:** the lane is 52 mm (route_check: net 65.5 mm with the block copper; ratio 1.16; 0 new vias). ARM1_SENSE_MCU is 2.55 mm with 1 via.

**Exit via GND:** a new GND via at (17.4, 90.2), 1.35 mm from the exit via. R7's GND via at (18.18, 90.55) sits on the straight lane.

**Block-internal In2 link:** the two GND vias at its vias are restored at R7's positions, (13.95, 93.75) and (13.95, 97.15).

**Why this topology:**
- ARM1_SENSE (east → north-west corridor) and NRST (forward centre → J2 south-west) must cross once.
- Here they cross at NRST's F.Cu pad and stub over ARM's B.Cu lane.
- They then run as a pair: NRST at y 51.95 and ARM at y 52.45. The 0.3 mm gap is too narrow for any pour, so no sliver forms.
- Coupling into NRST is negligible: about 0.35 pF against C24's 100 nF (**Inference**, not measured).

### Decoupling
Every VDD pin has its own 100 nF at a via beside the pin; the GND returns are local vias or the pour.

| Supply | Pins | Via | Cap and GND |
|---|---|---|---|
| VBAT | pin 6 | inward, V6 (19.5, 51.15) | C18 (18.3, 51.15), GND via (17.88, 50.35) |
| VDD | pin 27 | V27 (29.2, 50.5) | C15 (29.2, 49.4), GND via (29.2, 48.2) |
| VDD | pin 50 | V50 (29.25, 39.0) | C16 (28.1, 38.62), GND by pour |
| VDD | pin 75 | V75 (17.0, 38.75) | C17 (17.0, 39.9) |
| VDD | pin 100 | outward, V100 (14.1, 51.0) | C13 (14.1, 52.1), GND via (14.1, 53.3) |
| VDD | pin 11 | outward, V11 (22.0, 54.15) | C14 (22.0, 55.2), GND via (22.0, 56.4) |
| VCAP1 | pin 48 | V48 (29.25, 40.0) | C19 (28.35, 40.7), GND via (29.25, 41.4) |
| VCAP2 | pin 73 | V73 (18.0, 39.3) | C20 (19.8, 39.3), GND via (21.4, 39.3) |
| VDDA / VREF+ | pins 20/21, joined on F.Cu | outward, (26.5, 54.4) | C21 (26.5, 55.6), C22 (28.4, 55.18), GND via (27.2, 56.1) |

**Bulk and pins without a via:**
- C23 (4.7 µF) at (15.45, 43.95), on the R10 3V3 via.
- VSSA (19) and the VSS pins reach the F.Cu GND pour under the body.

**Why pins 11 and 100 decouple outward:** pin 12's HSE_IN escape uses pin 11's inner column, and IO2's dive uses pin 100's inner corner.

**BOOT0:** pin 94 has an inward via at (16.75, 48.0); R5 sits at (17.9, 48.0) on B.Cu.

## Placement changes the spike needs (step 4 must carry them)

1. **Y1:** rotation 90 at (22.85, 48.6), not the seed's rotation 0 at (22.6, 49.9). Its 4.7 × 4.0 mm courtyard is the binding constraint under U1. C25 and C26 sit outside it as above.
2. **The sense dividers (R60–R63, C60) no longer fit under U1.** ARM1_SENSE, C24, C15 and R170 take the NE corner.
   - The spike parks them, legal but **unrouted**, forward of pins 17/18 on B.Cu: R62/R63 at (24.9, 56.45/57.4), R60/R61 at (27.5/29.4, 56.95), C60 at (30.2, 53.65).
   - Their real home is step 4's. Inward vias for pins 17/18 would collide with C24 and its GND via.
3. **The ARM1_SENSE corridor on B.Cu:** x 18.18 ± 0.55 must stay clear from y 52.45 to 91.3.
   - Q123 moves 0.4 mm west to (16.0, 66.4).
   - R162 (0805) turns to rotation 90 at (16.4, 62.95); at the seed position its pad overlapped the lane.
4. **GATE_N and CONT corridor (not routed here; checked by geometry only).** They must run **east** of ARM, with ARM the westmost lane, or they would cross it at the exits (23.0, 88.33) and (28.4, 88.61).
   - Two 0.2 mm lanes fit at about x 18.6 and 19.0, ≥ 0.2 mm from ARM, J122's west pins (19.66) and the tie hole's 0.25 mm keep (19.65).
   - GATE_N's via near pin 3 must then sit east of ARM, about (18.75, 54.3); ARM is 0.22 mm from it.
   - CONT reaches R168 (23.6, 54.6) from the north, about y 57.5, clear of C14 and its GND via.
5. **The decoupling caps move forward of U1:** C13 outside the NW corner, and C14, C21 and C22 forward of U1, all on B.Cu.
   - The 3V3A feed (R164, C10, C11) still has to join C21/C22 (power/imu family).
   - IMU drop vias must stay clear of NRST's B.Cu lane: (16.1, 51.95) → (12.0, 47.85) → (7.6, 47.85) → (7.6, 42.6).
6. **TH1–TH3 removed (D8),** as in the seed.

## Findings for the orchestrator (not unsafe; each needs a decision outside this spike)

1. **D15 conflicts with D20.**
   - `check_r8.inner_signal` (D20: no signal track on In2) flags the rigid CH1 block's internal ARM1_SENSE In2 link: (14.55, 94.15)–(14.55, 97.55), 3.4 mm.
   - That link is part of the hash-asserted `ch1_copper` group (D15), and D9 forbids re-baselining that group.
   - As written, check_r8 can never pass. It needs a named exemption for that one rigid segment, or a decision.
   - The seed board and R7 show the same finding.
2. **`strip_gcpw` is fragile.**
   - Removing R7's four far F.Cu power zones together (R6_RAW_ACT_F, BAT_IN_F, RAW_ACT_F, R6_BAT_IN_crossbar_F; none within 2 mm of the strip) moves the F.Cu GND fill beside the RF lines by 0.01 mm at 13 of 372 samples. The digest changes from `8b46…` to `b92e…`.
   - Removing any one of them alone keeps it. Deleting all non-rigid tracks and vias keeps it.
   - The spike therefore keeps those four zones on its scratch board.
   - Step 5, which replaces the power zones, will probably trip this group. A tolerance or quantised profile, or a recorded re-baseline of `strip_gcpw` only, is needed. The RF lines themselves are unchanged.
3. **The native refill must run beside the project rules.**
   - Loading the board without `m3.kicad_pro` / `m3.kicad_dru` in its folder and refilling changes `strip_gcpw` (`8b46…` → `281d…`).
   - Inside the project folder, a refill, save and reload reproduces `8b46…`.
   - `r8_build.sh` must fill in place, as `quality_audit/refill_zones.py` does.
4. **GND vias near the CH1 block:**
   - A GND via that touches the end of a block GND track joins `ch1_copper` (`_graph_reach`) and changes its digest (measured, with a via at (17.43, 90.55)).
   - Step 7's stitching must keep GND vias off block track ends.
   - The three R7 GND vias beside the ARM1_SENSE vias are not rigid. Step 7 must re-create two of them, and a third replacing (18.18, 90.55), or `critical_via_no_gnd` fails on ARM1_SENSE.
5. **R7's fence-row CAM_INPUT_LIMITED vias** at (37.8 / 39.4, 23.3) survive the rigid filter of this scratch builder, which keeps every via with y < STRIP_Y on GND only. check_r8 flags them on the seed board too. This has no effect on the spike; the real builder's strip filter should drop them.

## Limits of this spike
- **Only the spike's own copper is routed.** Other families stay unrouted on the scratch board: the RF buses, USB/SWD, IMU, servo, the other pyro exits, power, the camera and the status lines.
  - "DRC 0" is filtered to the spike's nets and parts.
  - The diff against the seed board shows that the spike copper adds no DRC or route_check problem to any other net.
- **Parts outside the spike were moved:** the parked dividers, Q123 and R162. Their legality is DRC-checked, but they are not routed.
- **Silkscreen** was not checked (step 8).
- **The decoupling GND returns of C16, C17, C23 and the Y1 GND pads go through the B.Cu pour,** about 1–2.6 mm to the nearest GND via.
- **route_check information items:** `power_via_no_gnd` on 8 supply vias. This is information only; AGENTS §3 sets the GND-via rule for signals.
- **No electrical measurement:**
  - Crystal trace lengths (about 2.5 and 7.6 mm pin to pad) and load capacitance are not simulated.
  - The NDK drive-level bench check stays as ORDERING §5 says.
