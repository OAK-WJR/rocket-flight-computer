# Round 20 polish pass: CAD lane (hand-back)

## Scope

The brief is `.supervisor/r20_fix_cad_brief.md`: 11 items from round 20's seven board lenses on `50a39de5…` (0
Critical / 0 Major). The coordinator added three notes:
1. Delete the named gate entries.
2. List every designator the new any-size courtyard test moves.
3. FMEA I-11 belongs to the docs lane.

Changes are in:
- **Generators:** `m3_design/r10_pcb.py`, `r10_place.tsv`, `r10_route_power.py`, `r10_route_usb.py`,
  `r10_route_signals.py`, `r10_route_ground.py`, `r10_post.py`, `r10_sch.py`, `r10_sch_check.py`.
- **Generated footprints:** `r10_parts.py` writes `kilib/rocket.pretty/M3_DB125_2P_BK` / `_GN`.
- **Checks and tests:** `tools/check_r10.py`, `tools/test_r10_check.py`.
- **Records:** `R10_DECISIONS.md` (D-R20-01..11) and `AVA_LAYOUT.md`.
- Everything `m3_design/r10_build.sh` regenerates.

Not touched:
- No native CAD was hand-edited.
- STATUS.md, AGENTS.md, docs/*.md and parts_qualification.md are unchanged.
- No git state was changed.
- AGENTS section 2 is unchanged.

Machine-readable twin: `round20_fix_cad.json`.

## New board

PCB `0dc847761de94a45cf68b1c82ec91f38e9d4ebb7297abc7108e3df9a454940d3`, 46 x 90 x 1.6 mm.

| Board | Bytes | Footprints | Segments | Vias (GND) | Track |
|---|---|---|---|---|---|
| Round 19 `50a39de5…` | 2,336,742 | 215 | 984 | 301 (169) | 1870.487095 mm |
| Round 20 `0dc84776…` | 2,340,154 | 215 | 985 | 302 (169) | 1874.854252 mm |

- **Parts moved:** three. TP82 B(11.0,17.6) -> B(11.2,20.7). D440 F(13.9,17.2) -> B(4.45,19.45) -90. D441 F(13.9,21.4)
  -> B(4.45,23.05) -90.
- **Unchanged:** every other pose, land, net and support, U1's pin map and the IMU axis map (K-binding OK).
- **Vias:** added PORT_4V8 (30.575,11.6) and GND (3.75,19.775), (3.75,23.375); removed GND (14.225,16.45) and
  (14.225,22.15).
- **New rule area:** `R20_TAB_KEEPOUT_WEST_AFT` (In2, fill-only).
- **Pads:**
  - U1.74 has no pour connection (a board pad override).
  - J121.1, J400.2 and J1.2 carry no unconnected inner rings (set in the generated library).

## Builds and gate

**Two complete `r10_build.sh` builds** (KiCad CLI 10.0.7, `NUMPY_PY=.supervisor/venv/bin/python`):
- Both exit 0 and end in `tools/check.sh` exit 0, with PCB `0dc84776…` in both.
- Snapshot compare: 890 files identical. 4 differ only by date stamps (both assembly PDFs, the Gerber zip, the
  manifest). None is in only one build.
- Before them, scratch builds (through the ground family, then r10_post, on a project copy) with DRC, fit, check_r10
  and route_check on each. They carried the trials described under items 1, 2, 8 and 9.

**check.sh:**
- DRC 0 / unconnected 0 / schematic parity 0 / ERC 0.
- Metadata / 3D audit, `r10_parts --check` and fit (eight wire rooms) all OK.
- **check_r10: 35 / 35 rules OK.**
- route_check r10: 0 failing (22 bump windows; 7 unrecorded noncritical leftovers, unchanged). With `--bumps-all`, 148
  information instances (was 149: USB_LIMITED's extra_bends is gone, nothing added).
- Fab content checks and the six-output manifest pass.
- Self-tests: shell 10, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 68, **R10 239** (6 NumPy
  skips) and NumPy `HotplugNumerics Plate` 6: all OK.

**Fab package (`r10_fab.sh`):**
- BOM 81 lines; the BOM file is unchanged. 205 placed parts.
- CPL: 69 top / 122 bottom rebuilt (was 71 / 120), plus 14 placement-only.
- Paste: F 253 / B 375 flashes.
- Owner BOM: C84.
- Manifest bound to `0dc84776…`. Cost and stock were not re-run (same parts and quantities).

**Hot-plug:** 2304 cases, 0 failures, qualification pass; extremes identical to round 19.

**Binding note:** regenerated for `0dc84776…`.

## Items

**1. U9 EN pull-down at the pin (R20-SAF-01, D-R20-01): not done.** The measured reason:
- **No room on B.Cu.** U9.1 is U9's south-west corner pin, and every B.Cu exit is closed:
  - D9's courtyard is 0.210 mm from U9's;
  - BAT_OVLO runs from U9.2 round EN to R82 / R83;
  - U9.5's BAT_IN trunk is east of it;
  - R82.2 is 0.350 mm from that trunk, where a 0.2 mm run needs 0.50 mm. R82 can move only 0.275 mm.
- **Too small.** The reachable pocket, about 1.4 x 0.9 mm, is smaller than an 0603's 0.95 x 2.45 mm pad span. The
  triangle inside the BAT_IN loop allows at most 1.64 mm of pad span.
- **Scratch trial, reverted.** R81 at B(16.775,85.475) with one straight run from U9.1. It needed R82 moved, the U9 IN
  via moved 0.1 mm, the R82 / R167 tap rerouted and two GND vias in a pour island enclosed by BAT_IN. route_check then
  failed four ways: acute angles at R82.1 and U9.1, a BAT_IN detour of 1.61 and a local bump.
- **Residual.** EN still reaches R81 through three vias and about 20 mm of track. C87 stays at the switch end. This is a
  respin item: re-lay U9's west cell.

**2. U401 feedback tap (R20-PWR-02, D-R20-02): done.**
- **Change.** A PORT_4V8 via (30.575,11.6) straight north of R402.1, landing in the In2 output plane both OUT vias feed,
  with a 0.4 mm F.Cu stub. GPS_RX_MCU's run stays; the via is 0.25 mm from it.
- **Before -> after.** Opening (29.75,12.6) cut R402.1 off -> no single PORT_4V8 via (9 tested) does.
- **Gate.** K-power gains `single_via_opens` (`SINGLE_OPEN_TAPS`), with a seeded test.
- **First trial.** A B.Cu stub to U401's run made a staircase, so the via has no B.Cu stub.

**3. U1.74 pour debris (R20-RTE-02, D-R20-03): done.**
- U1 pad 74 has `ZONE_CONNECTION_NONE`.
- The 0.282 mm^2 piece is gone; pour pieces 35 -> 34; no debris.
- The `POUR_DEBRIS` entry is deleted, and a seed restores the piece.

**4. TP82 (R20-RTE-01, D-R20-04): done.**
- TP82 is at B(11.2,20.7). The spur is one 6.152 mm segment.
- The stub past the old bend is 0.849 mm (was 3.785 mm with two bends).
- 1.075 mm to the nearest foreign copper (R90's pads); the GND pour is held at 1.0 mm.
- M-6: 1.855 mm. These match the lens's figures.

**5. Inner rings on the S-8 terminal barrels (R20-SAF-05, D-R20-05): done for J121.1 and J400.2.**
- **Method.** "Remove unconnected layers, keep start and end", set in the generated library: BK pad 1 and GN pad 2. A
  board override failed DRC library parity (2 lib_footprint_mismatch).
- **J121.2 keeps its rings.** GND is exempt there, and removing the rings would bring GND from 0.55 to 0.25 mm.
- **Gate.** S-8 now also measures the rings a barrel keeps (`barrel_rings`); seeds and a synthetic case are added.
- **Ring-to-copper before -> after.** Barrel walls are unchanged unless noted. Every via barrel has no ring before or
  after (unchanged).

| Barrel | Before | After |
|---|---|---|
| J121.1 (PYRO1_OUT) | ring 0.750 In1 GND, 0.750 In2 GND, 0.761 In2 3V3 | no ring; wall 1.050 / 1.050 / 1.061 |
| J400.2 (BAT_SW_RETURN) | ring 0.750 In2 RAW_PROTECTED, 0.750 In2 GND, 0.250 In1 GND (exempt) | no ring; wall 1.050 / 1.050; In1 GND wall 0.550 -> 0.250 (exempt: a short holds EN low) |
| J121.2 (PYRO1_IGN, GND exempt) | ring 0.25 In1 / In2 GND; wall 0.550 | unchanged |
| Vias: OUT (11.63,55.1); ACT_GATE (16.2,73.3), (11.14,71.7); BAT_ENABLE (19.675,66.6), (21.3,68.9), (17.1,82.8); PYRO1_GATE (14.4,53.3) | walls 1.021 / 1.050 / 1.050 / 1.050 / 1.050 / 1.050 (to hazardous copper); PYRO1_GATE GND 0.251 (exempt) | unchanged |

- **Side effect at J1.2.** GN pad 2 is also J1.2 (GND). Its unconnected In2 ring goes, and In2 RAW_PROTECTED comes from
  0.55 to 0.25 mm of that GND barrel, the hole clearance of every GND via in a RAW region.

**6. Designators (R20-MFG-02, D-R20-06): done.** Courtyard offenders 3 -> 0, and the three named entries are deleted.
- **Moved by the gate lane's any-size courtyard test (intended):**
  - C400 F(9.743,6.048) -> F(9.707,5.75);
  - C94 and R461 hidden, since no spot is nearer their own part.
- **Moved by this pass's copper and parts:**
  - R402 F(29.574,11.373) 0 -> F(28.638,11.429) 90;
  - R463 B(11.175,20.453) -> B(11.0,18.9);
  - C444 B(12.04,12.986) 0 -> B(12.577,11.904) 90;
  - R470 F(16.957,21.951) -> F(16.454,21.954);
  - D440 and D441 shown again on the bottom, at B(5.572,18.043) and B(3.669,24.672);
  - C28 shown again at B(14.18,22.338);
  - C404, R90 and U401 hidden (U401's spot now holds the FB via, R90's sits beside TP82);
  - J440's 3:TXO legend B(5.7,17.5) 90 -> B(10.5,17.5) 0.
- Hidden 94 -> 96, all kept on F.Fab. Nothing else moved (silkscreen diff against `50a39de5…`).

**7. Fab references (R20-MFG-03, D-R20-07): done.**
- Crossings 6 -> 0. Before: C123 0.0013, C445 0.1915, D440 0.0479, D441 0.0479, R119 0.6935, R173 0.011 mm^2.
- `FAB_REFERENCE_CLEARANCES_R13` entries:
  - C445 (0, 0, 0.7);
  - D440 / D441 (0, -1.0, 0.8);
  - C123 (0, -0.1, 0.4);
  - R119 (0, 0.1, 0.4);
  - R173 (-0.1, 0, 0.4).
- The six named entries are deleted, and seeds restore each round 19 text.

**8. Panel tabs (R20-MFG-01, D-R20-08): west aft done, east tabs not done.**
- **West aft.** In2 3V3 under the 5 x 3 mm band: 12.498 mm^2 -> 0. K-plane, K-reference and K-region pass.
- **East aft, not done** (RAW_PROTECTED 7.497 and PORT_5V3 3.077 mm^2 stay). The keep-out splits In2 RAW_PROTECTED; the
  245.01 mm^2 north piece is left with 0 links, even at 2.0 mm depth.
- **East forward, not done** (RAW 12.244 mm^2 stays). That piece is left on a 0.45 mm neck at 2.8-3.0 mm depth.
- The owner chooses the east tab plan.

**9. AUX ESD clamps (R20-RTE-05, D-R20-09): done.**
- D440 / D441 sit on the bottom under J440, on the wire side, as D410 / D411 sit under J410.
- B.Cu runs go from each pin to its clamp, and each return goes to its own via 0.7 mm beyond.
- Pin to clamp: 6.227 / 6.176 -> 3.157 / 3.194 mm. M-6: 1.681 / 1.713 mm.
- The interior side is taken by TP82 and R90.

**10. Optional (R20-RTE-04 / -03, D-R20-10): not done.**
- Both are cleanliness only.
- The VLOGIC in-line pair would move the pinned `PARALLEL_VIAS` entry and two tests.
- The GPS jogs need C90's fan-out vias moved.

**11. C87 text (R20-SAF-04, D-R20-11): done.** The binding-note obligation and the battery_entry sheet note carry the
worst case with I_ENLKG ±0.1 µA (TI SLVSFC9C p9):

| Figure | Before | After |
|---|---|---|
| Drop-out immunity at 6.0 / 7.4 / 8.4 V | 11.4 / 21 / 27 ms | 10.6 / 20.5 / 26.4 ms |
| At the 5.73 V four-stall BAT_IN | 9.3 ms | 8.5 ms |
| At 5.5 V | not stated | 6.6 ms |
| Pack needed for the 10 ms criterion | not stated | ≥ 5.92 V |
| Turn-on | 31-122 ms | 30-129 ms |

These are a Calculation, reproducing the safety lens. C87 stays 220 nF.

## Tests

- **Added:** RealBoardSeeds.test_r20_s8_terminal_inner_rings and test_r20_fb_tap_survives_one_via_open.
- **Changed:**
  - the synthetic S-8 test (now models ringless vias, plus a 0.900 mm ring seed);
  - test_r19_pour_debris_seed;
  - the two round 20 designator and Fab tests (they now seed the round 19 state);
  - test_r19_doubled_feeds_keep_two_vias (U401 OUT now drops two vias).
- **Harness fix.** Via-removal seeds now use `RealBoardSeeds.drop`, which leaves the removed via undeleted.
  - Why: KiCad 10's SWIG hands a removed item to its Python proxy, which deleted it while the board still referenced
    it. Later board reads failed ('SwigPyObject').
  - The round 19 seeds passed by luck.

## Renders

**Checked:** `.supervisor/r10_renders/r10_top.png` and `r10_bottom.png` (r10_fab.sh, 1016 x 1988), plus a 2016 x 3952
bottom crop of the J440 corner and zoom-3 top views of the AUX cell and the U401 corner.

**Seen:**
- **Top.**
  - The AUX cell has no clamps; the R470 / R471 / C445 / C444, AUX and 1:4V8 texts are whole.
  - R402's designator stands vertical beside R402 / R403.
  - No silkscreen sits over the new via.
- **Bottom.**
  - D440 / D441 sit under J440 with their designators beside them.
  - 2:GND, 3:TXO (now east of pin 3) and 4:RXI are whole and clear of pads.
  - TP82 sits on its diagonal.
  - No silkscreen sits over a pad, a via or the edge.
- **Note.** R463's designator ink sits 0.203 mm under 3:TXO's and 0.967 mm from TP82's pad, between R463 and TP82.
  It passes the courtyard rule; no gate sets a text-to-text gap.

## For the docs lane

- FMEA I-11 overclaims S-6's scope (coordinator note 3).
- The C87 figures (item 11) appear in AGENTS, M3_R10 and REQUIREMENTS F6.
- The "terminal-hole inner rings 0.30 mm closer" deviation:
  - now resolved for J121.1 / J400.2;
  - J121.2 keeps its rings;
  - J1.2 lost its In2 ring.
- Positions and the hidden list: TP82, D440, D441; 96 hidden.
- ORDERING 8.1: the In2 net under each tab.
- The R20-SAF-01 respin item.
