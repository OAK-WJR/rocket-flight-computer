# R8 review pass 2: power, thermal and hot-plug

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d`.
I checked the hash before and after the review, and it did not change. This was a read-only review: the only repository file
I changed is this report. I measured with KiCad 10.0.6 pcbnew, using scratch scripts. Every script that wrote anything
(the seeded-neck copy in §1) ran on a scratch copy, which I have since deleted. The methods below are enough to repeat
each measurement.

**Result: 0 Critical, 0 Major, 5 Minor (2 worth fixing).**
- **Pass 1 findings:** all six power findings are closed or properly dispositioned (§2). U10's bypass C83 now sits
  beside U10.1 and U10.2.
- **7.7 A copper:** it reproduces the record and meets D12. The build's DC gate fails when it should: I tested it with a
  seeded neck.
- **Servo GND return:** it reproduces the record's figure.
- **Regressions:** I found none in the power copper.
- **The two findings worth fixing:**
  - **POWER-01:** the new ORDERING §5 stall test cannot judge D12 as written. Two of its three "necks" lie on Q120's
    pads and under its body, where the FET's own dissipation dominates. Its duration refers to a firmware stall limit
    that is not defined anywhere.
  - **POWER-02:** a dead-end part of the In2 BAT_IN island (about 220 mm², carrying no current) puts unfused battery
    copper 0.5 mm from the east and forward edges, under the right forward panel tab and round the M3 hole at
    (42, 114.4). Trimming it is a single table edit.

## 1. What was run

| Check | Result |
|---|---|
| `tools/check.sh` (full gate, on the repository board) | exit 0: DRC 0, unconnected 0, parity 0, ERC 0; audit, silk, check_r8 OK; route_check r8 0 failing, 3 allowlisted, 0 leftovers; check_actuators OK; fit_check OK |
| `DC_GND=0.1 tools/run_dc.sh <board> <scratch> 0.1` | The output's first line carries the board hash `6600ef94…`. **RAW_ACT** 1.45 mΩ; neck 5.90 mm F.Cu (x 20.2–21.8, y 80.75–86.25); 17.6 °C; vias 66, max 0.89 A at (11.3, 85.6), 8 over 0.5 A. **BAT_IN** 0.42 mΩ; 6.86 mm B.Cu; 14.8 °C; mid-path 49 % B.Cu / 41 % In2 / 10 % F.Cu; vias 15, max 0.70 A at (21.25, 100.9), 5 over 0.5 A. **ACT_FET_S** 0.19 mΩ; 4.80 mm B.Cu; 22.3 °C; no vias. These equal the build's 0.1 mm gate figures in fix1_progress, and match the record's 0.05 mm figures (5.94 / 7.00 / 4.97 mm; 0.86 / 0.67 A) within the 3 % grid difference D49 gives. No level was dropped by the < 1 mm filter. GND return: see below |
| Servo GND return (the same run's DC_GND row, 0.1 mm, window x 0–46, y 64–118) | Reproduces fix pass 1's evidence exactly: R = 0.72 mΩ (5.6 mV and 0.043 W at 7.7 A). Mid-path shares In1 85 %, In2 9 %, B.Cu 5 %, F.Cu 1 %. 110 vias carry current, the largest 0.38 A at (37.35, 100.6), none over 0.5 A. The 'neck' is 1.97 mm at level 0.030, cut box (24.5–26.6, 109.4–111.4), which is J1.2's spokes. Run time about 25 min of CPU |
| DC gate fail path (scratch copy; a keep-out rule area cutting the ACT_FET_S B.Cu pour down to a 0.75 mm passage at x 12.0–12.6, y 104.2–104.95; native refill; `dc_solve.py --necks --max-rise 30`) | R rose 0.19 → 1.45 mΩ. 230 levels fell under the < 1 mm filter, but the next levels (1.00 mm at the passage mouth) still gave **NECK FAIL 136 °C, exit 1**. So the filter does not hide a real narrow neck. I deleted the copy afterwards |
| Pour contact at the 7.7 A through-hole pads (fill sampled on rings at 0.85 / 1.1 mm) | J1.1 solid on F / In2 / B. J122.2 / .5 / .8 / .11 and J124.2 solid on F / In2 / B. J122's GND pins partly ringed on F, B and In2 (servo lanes cut the fill) and solid all round on In1. J1.2 has four spokes per layer on F, In1 and B, none on In2 (it sits in the In2 BAT_IN island) |
| Hole-to-foreign-copper on inner layers (terminal holes) | ≥ 0.50 mm everywhere (J122 signal pins 0.50 mm; J1 0.75–0.80 mm; J124 / J121 0.80–1.0 mm) |
| Zone map (every zone, fill islands, pad connection) | Every zone fills to a single island: In2 GND 2396 mm², 3V3 1514 mm², RAW_ACT west 288 mm² and J122 finger 58 mm², BAT_IN 506 mm². The power pours connect full. GND_F / GND_B use THT thermals (SMD pads full), and In1 uses thermals |
| Decoupling, nearest same-net capacitor to every IC power pin (script over all U*) | Unchanged from pass 1 except for C83. **U10.1 to C83.1 is 1.73 mm of track** (was 17.5 mm). U9.6 to C82 is still 7.34 mm (POWER-04, recorded). U13's two capacitors are 5.6 / 6.75 mm of track away (R8P2-POWER-03) |
| Tests | `test_dc_solve`, `test_r8_power`: 10 tests OK |
| Maker documents read | AOS AON6403 Rev 2.1, Sep 2023 (https://www.aosmd.com/res/datasheets/AON6403.pdf): RθJA steady state 40 typ / 55 max °C/W (Note A: 1 in², 2 oz, still air); RθJC 1.5 °C/W max; RDS(on) < 4.3 mΩ at VGS −4.5 V. TI TPS709 SBVS186H, Jul 2021 (https://www.ti.com/lit/ds/symlink/tps709.pdf): §8.1.1 (Cout ≥ 1.5 µF effective at ≥ 1.5 V, ≤ 47 µF, ESR 0–0.2 Ω) and §10.1 ("Place input and output capacitors as close to the device pins as possible … the ground connection for the output capacitor must be connected directly to the device GND pin"). Diodes AP63300/AP63301 DS42002 Rev 3-2 (https://www.diodes.com/datasheet/download/AP63300_AP63301.pdf): θJA 89 °C/W, measured on a single-layer 2 oz board (Note 6); operating TJ +125 °C; absolute maximum +160 °C |

## 2. Previous findings in this dimension (pass 1 → board `6600ef94…`)

| Pass-1 item | Disposition in fix pass 1 | Verified on `6600ef94…` |
|---|---|---|
| R8P1-POWER-01: F4 record lacks the servo GND return and per-via currents | Fixed: `dc_solve --window / --via-currents`, `run_dc.sh` DC_GND row, M3_R8 "DC solve", MARGIN P1-9, D95 | **Closed.** The tool options exist and work, and I reproduced the figures (§1). The record states the equipotential-sink caveat and how the J1.2 spokes are judged. M3_R8's conduction arithmetic is right: 0.49 mΩ per F/B spoke and 0.36 mΩ per In1 spoke, about 0.04 mΩ for twelve in parallel. One small records slip remains (R8P2-POWER-05 a) |
| R8P1-POWER-02: the cited stall test is missing from ORDERING §5 | Fixed: ORDERING §5 "7.7 A stall test" | **Closed as a gap, but the new text cannot judge what it claims to judge:** see R8P2-POWER-01 |
| R8P1-POWER-03: C83 17.5 mm of track from U10.1 | Fixed: C83 at (9.55, 36.0) rot 90 B (D88); D42 corrected | **Closed.** C83.1 sits on the VBUS run into U10.1: 1.125 + 0.601 = 1.73 mm of 0.3 mm B.Cu. C83.2 reaches U10.2 over 1.62 mm of 0.2 mm track, and both pads sit in the B.Cu GND pour. The loop is about 1.5 × 1 mm. TI SLVS841F §12.1 is now met. Side effect: VBUS's layer change at (7.95, 36.0) lost its GND via (2.06 mm, recorded as information, C8). J3's THT GND leg J3.1 is 1.94 mm away and serves the same return. VBUS is not on AGENTS §3's critical list |
| R8P1-POWER-04: D9 / C82 on a stub beyond U9.6's via | Recorded, not reworked (M3_R8 Power) | **Properly dispositioned.** The geometry is unchanged |
| R8P1-POWER-05: single-via series links | Recorded as accepted single points (M3_R8 Power, MARGIN R15) | **Properly dispositioned.** I found no new single-via rail link. The fold-table row for the In2 3V3 feed via is mislabelled: R8P2-POWER-05 (c) |
| R8P1-POWER-06: dc_solve docstring on THT pads | Fixed (docstring) | **Closed** (`tools/dc_solve.py` l. 17–19) |

Fix pass 1's copper changes that touch power, re-measured:
- **ACT_FET_S chamfer (D85).** The neck is unchanged at 4.80 mm (0.1 mm grid). J124.1 is 1.089 mm away (the pyro
  dimension checks this).
- **RAW_ACT chamfer at (21.3, 87.3).** It lies outside the neck's cut box. The neck is 5.90 mm, unchanged.
- **ACT_GATE stub chamfer.** It lies outside every cut box.
- **U9.5 entry (D94).** It now runs 0.3 mm B.Cu from C88.1 (41.25, 87.6) to the pad centre. The feed is 0.5 mm B.Cu
  on x 41.25 from (41.25, 102.4), 16.9 mm long in all. It passes over In2 GND from y 100.3 to y 85.5 and over In2
  BAT_IN for its first 2.1 mm.
  - D76's 5 nH model corner still covers it (microstrip estimate about 4.5 nH, Inference).
  - Its R_feed (17.3 mΩ) equals the re-run J1:1 → U9:5 figure (17.26 mΩ).
- **VLOGIC hold-up via moved 0.15 mm (D87).** No change to the hold-up path (C84 → U2: 2.60 mΩ).

## 3. Findings

### R8P2-POWER-01 (Minor, worth fixing): the ORDERING §5 stall test cannot test D12 as written

**Requirement.** REQUIREMENTS F4 asks for "a thermal-camera stall test (R8: ORDERING §5 '7.7 A stall test', at the R8
hot spots against D12's estimates)". D12's estimates are IPC-2152 rises of the **copper alone**, with no plane credit.

**What ORDERING §5 l. 166 specifies:**
- 7.7 A "for the firmware's stall limit (the longest the firmware lets a stall last)";
- imaging of the RAW_ACT neck, the BAT_IN neck (B.Cu x 17.25–20.25, y 98.65–104.5), the ACT_FET_S bridge
  (B.Cu x 11.8–14.15), Q120 / Q121, and J1.2's spokes "both faces";
- pass: "each neck's rise at or below D12's estimate (RAW_ACT 17.5 °C, BAT_IN 14.5 °C, ACT_FET_S 21.5 °C …), and the
  FETs within MARGIN_PRESCRIPTION R1".

**What is wrong (measured on the board unless marked):**

1. **The BAT_IN "neck" is Q120's drain pad area.**
   - Its cut box (x 17.25–20.25, y 98.65–104.5) lies almost wholly inside Q120's courtyard (B.CrtYd x 12.75–20.00,
     y 99.05–104.39).
   - It covers the 4.6 × 4.1 mm drain pad 9 (x 15.02–19.12) and drain pins 5–8 (x 19.28).
   - So most of that copper lies under the package body, and a bottom-face camera sees the FET.
   - The ACT_FET_S cut box (x 11.8–14.1) ends on Q120's source pins (x 13.19–13.77), with Q121's source row 0.6 mm
     from its other side.
2. **The FET's own heat dominates those readings.**
   - At 7.7 A each AON6403 dissipates about 0.34 W (MARGIN_PRESCRIPTION l. 73: 7.68 A × 5.83 mΩ hot).
   - AOS gives RθJA 40–55 °C/W on 1 in² of 2 oz copper. MARGIN estimates 65–90 °C/W on this board.
   - That is an 18–31 °C rise at the drain tab, since RθJC is only 1.5 °C/W (Inference from those figures). The
     copper's own I²R rise adds to it.
   - BAT_IN's 14.5 °C pass limit is therefore likely to fail on a correctly sized board. ACT_FET_S's 21.5 °C, heated
     from both sides, is marginal.
   - A tester then has to improvise. Either the test rejects good copper, or it is waved through and stops checking
     anything.
3. **The duration is undefined.**
   - No document defines a firmware stall limit. My grep of docs/, AGENTS, STATUS and m3_firmware finds only this
     sentence and its R5 ancestor, and the R8 firmware is "not started" (AGENTS §1).
   - D12 and IPC-2152 are steady-state figures (M3_R7 l. 1030: "a stall of seconds heats the copper less").
   - A short stall would pass trivially and prove nothing about D12.
4. **J1.2's top-side spokes cannot be imaged.** J1's body (F.Fab x 11.88–34.12, y 104.83–116.17) covers J1.2
   (25.54, 110.4). Only the bottom face can be imaged there.
5. **The ACT_FET_S figure is out of date.** ORDERING still quotes step 9's 21.5 °C, while the record (M3_R8, F4,
   R8_VALIDATION l. 85) is 21.4 °C.

**Impact.** No hardware risk: the copper meets D12 by the solve. But the only planned measurement of the 7.7 A copper
would give a false fail, or no information.

**Fix (ORDERING §5 l. 166, and the matching sentence in F4 / M3_R8 if wanted).**
- **Duration:** run until steady state (hottest reading changing by less than about 0.5 °C per minute, typically
  minutes: Inference). Or state the stall duration the flight profile allows and record which one was used.
- **Pass criteria:** judge the copper where the FETs do not dominate, and the FETs with their own limit:
  - RAW_ACT neck (F.Cu, ≥ 12 mm from either FET's courtyard): rise ≤ 17.5 °C.
  - Q120 / Q121 drain tabs and the BAT_IN / ACT_FET_S copper beside them: rise ≤ 100 °C (R1: TJmax 150 °C − 50 K)
    − 70 °C bay maximum − 0.34 W × 1.5 °C/W ≈ 29 °C.
  - Record the BAT_IN / ACT_FET_S readings against D12's 14.5 / 21.4 °C as information.
- **J1.2:** image it from the bottom only.
- **Figure:** use 21.4 °C.

### R8P2-POWER-02 (Minor, worth fixing): a dead-end part of the In2 BAT_IN island runs unfused battery copper to the east and forward edges, the right panel tab and an M3 hole

**Board.**
- `r8_power.py` l. 71 draws `IN2_BAT_IN = [(12.4, 100.3), (45.5, 100.3), (45.5, 117.5), (12.4, 117.5)]`.
- The other BAT_IN pours stop at x 33.5 (F.Cu) and x 41.3 (B.Cu, at y 101.9–105.6 only), and at y 112.6.
- **The island's eastern part carries no current.**
  - Every BAT_IN via lies at x ≤ 26.2: there are 15, at x 17.7–26.2, y 100.9–107.0.
  - J1.1 (x 30.62) is the only BAT_IN through-hole pad.
  - So the In2 copper east of J1.1, about 220 mm² of the island's 506 mm² east of x 31 (pcbnew boolean on the fill),
    is a dead end joined only through J1.1's barrel.
  - The same holds for the forward strip y 112.6–117.5.
  - The 7.7 A current runs west from J1.1 to Q120's via field (the solve's In2 share sits on that path).
- **Where that copper reaches (fill sampled 0.01 mm in from the edge):**
  - In2 BAT_IN comes to 0.51 mm from the east edge at every sampled y from 100.5 to 115, and to the forward edge
    (y 117.5).
  - Under it, B.Cu GND is 0.2 mm away (7628 prepreg), and the B.Cu GND fill also runs to 0.51 mm from the edge.
  - It surrounds the M3 hole at (42, 114.4) at 0.5 mm from the hole edge. ORDERING §7 needs nylon hardware partly for
    this reason.
  - It lies under the right forward panel tab (y 105–110). ORDERING §3: "lies over the In2 BAT_IN island, as every
    right-edge window forward of y 104 does".

**Why it matters.**
- Pass 1 DFM-02 and D93 moved the left forward tab off the RAW_ACT band for this exact mechanism (flex cracking at a
  snapped or nibbled tab). The right tab was kept only because "every window forward of y 104" has BAT_IN.
- That is true only because of copper with no electrical purpose.
- A crack at the tab or the hole between the battery plane and B.Cu GND, which sit 0.2 mm apart, would short the pack
  through the external 15 A fuse. That is an improbable fault (Inference), but this copper buys nothing in return:
  - its plane capacitance is about 40 pF;
  - it is not in the input node's current path: C80, C96 and D8 connect to J1.1 on B.Cu and F.Cu, with no BAT_IN via
    east of x 26.2;
  - the U9 feed lane's first 2.1 mm runs over it, so it even breaks the lane's In2 GND reference.

**Fix.**
- Give `IN2_BAT_IN` the extent of the outer BAT_IN pours, for example `[(12.4, 100.3), (33.5, 100.3), (33.5, 112.6),
  (12.4, 112.6)]`. J1.1's In2 annulus stays whole: its pad edge is 1.6 mm inside x 33.5 and 0.9 mm inside y 112.6.
- Rebuild with `r8_ground.tsv` regenerated (`make_ground.py --built`, as in fix pass 1).
- Expected results (to confirm on the rebuilt board):
  - In2 GND fills the east and forward strip;
  - the right forward tab and the (42, 114.4) hole see GND on all four layers;
  - the U9 feed runs over In2 GND for its whole length;
  - D18 is unchanged or larger (its 2.65 mm minimum is at x 25, R134.1);
  - the BAT_IN neck (Q120, B.Cu) is unchanged. Re-run `run_dc.sh`: the path R should barely move, because the trimmed
    copper carries no current (Inference).
- Then update ORDERING §3 (the right tab) and §7 (the hole list).

### R8P2-POWER-03 (Minor): U13's input and output capacitors are 5.6 / 6.75 mm of track from its pins (TI SBVS186H §10.1)

- **Board.**
  - U13 (TPS70933, (40.8, 49.6) B) has its output U13.5 (42.1, 50.55) joined to C92.1 (22 µF, (39.8, 55.0)) by
    0.65 + 2.3 + 3.8 = 6.75 mm of 0.3 mm B.Cu.
  - C93 (100 nF) on the same net sits by U12, about 9.2 mm of track away.
  - U13.1 (CAM_5V) reaches C91.1 (1 µF, (44.17, 49.975)) by 1.3 + 0.95 + 3.37 = 5.6 mm, running under U13's body.
  - C92.2 returns to U13.2 through the B.Cu GND pour, not directly.
- **Datasheet.** TI §10.1 asks for both capacitors "as close to the device pins as possible" and the output
  capacitor's ground "connected directly to the device GND pin". §8.1.1's stability window (≥ 1.5 µF effective,
  ≤ 47 µF, ESR 0–0.2 Ω) is still met: the track adds about 11 mΩ and 5 nH (Inference).
- **Impact.** Small. CAM_IO_3V3 feeds only U12's camera-side I/O (mA), and R7 had C92.1 about 4.75 mm (centre to centre) from U13.5. No
  record mentions it.
- **Fix (optional).** If U13's neighbourhood is touched, put C92 (or a 2.2 µF 0603) beside U13.5 / U13.2. Otherwise
  add one line to M3_R8 Power.

### R8P2-POWER-04 (Minor): the build's new DC gate has no seeded test, and `dc_solve.py`'s new `--window` / `--via-currents` have none either

- **What the tests cover.** `tools/test_dc_solve.py` tests only the stack-up reader (3 tests). Fix pass 1 added seeded
  tests for its three new `check_r8` gates (D85, D87, D92), but not for D95's DC gate, which the build relies on to
  hold F4 / D12.
- **What I verified by hand.** The gate's fail path works today: the seeded 0.75 mm neck in §1 gave NECK FAIL and
  exit 1.
- **The risk.** A later edit could break it silently. For example, a refactor that drops the `return 1` would leave the
  build printing "neck OK".
- **Fix (optional).** Add a test that seeds a narrow passage into a copy of the board (a rule area, native refill, as in
  §1) and asserts exit 1, plus one `--via-currents` assertion. Each run is about 1 min at 0.1 mm on ACT_FET_S.

### R8P2-POWER-05 (Minor): record slips in the power figures

- **(a) Via count.** MARGIN P1-9's R8 status (l. 196) says BAT_IN has "5 over 0.5 A". The 0.05 mm evidence
  (`step9/evidence/fix1_dc_bat.txt`) and M3_R8 say 4. Five is the 0.1 mm figure.
- **(b) "Nearest pad edge" is really centre to centre.**
  - Where: M3_R8 l. 40 and l. 415, R8_DECISIONS D76 (l. 1801), R8_VALIDATION l. 105 and STATUS l. 67 all place the
    protection parts "within 3.9–10.6 mm of J1.1 (nearest pad edge; R167 3.86 mm …)".
  - What the figures are: the distance from J1.1's centre to each part's nearest pad **centre**. The 3.86 mm is
    R167.2's centre, and that pad is GND; the 10.6 mm is C96.1's centre.
  - Measured pad edge to pad edge, the range is **2.0–8.4 mm**: R167 2.04, D8 3.86, C95 5.78, R166 5.85, C80 6.21,
    C89 7.24, C96 8.35 mm.
  - The premise holds either way. Only the label is wrong.
- **(c) Wrong reason in the fold table.** R8_VALIDATION C14 (l. 315) gives via (34.4, 69.65) the reason copied from
  (34.4, 73.2) ("T to D121.5; the In2 tap into the F.Cu hop …"). Via (34.4, 69.65) is the In2 3V3 region's only feed
  from U2 / L1's output line (B.Cu y 70.4), the single point that POWER-05 recorded. Its fold reason should say so.
- **Fix.** Correct the text in the next records pass. No copper change.

## 4. Checked, no finding

- **7.7 A paths and D12.**
  - Reproduced at 0.1 mm (§1). All three necks are within D12, and the build gate holds them.
  - BAT_IN has no series via.
  - RAW_ACT has one series via stage: 66 vias, at most 0.89 A each.
  - ACT_FET_S is a single B.Cu bridge.
  - None of the three cut boxes moved in fix pass 1.
- **Servo GND return.** Reproduced (§1). The J1.2 spokes are judged correctly by conduction.
  - At the 0.1 mm grid the F / B spoke cuts total only 1.18 / 1.21 mm, because the 45° spokes rasterise poorly. The
    F/B spoke facing aft-east also feeds only a small sliver; the main fill lies forward.
  - Even with a third of the spokes effective, the spokes stay below 0.15 mΩ and dissipate a few mW. That is no
    finding.
- **In2 map.** Each region is one island. D47's regions are as recorded. The RAW_ACT west and BAT_IN islands are
  1.4 mm apart at y 100.3–108. The 3V3–RAW_ACT gap of 0.3 mm on In2 is inner layer only (as in pass 1).
- **Input protection at J1 and F9.**
  - D8.2 sits in the B.Cu GND pour, with GND vias at (30.6, 99.1) and (35.0, 99.2). C80.2 and C96.2 sit in the B.Cu
    pour, with vias at (37.35, 100.6) and (39.0, 99.2). R166.2 is on F.Cu GND.
  - The protection loop closes on In1 to J1.2: about 10 mm under the band, about 1 nH. That is negligible beside the
    0.1–2 µH harness (Inference).
  - U9's feed and GND are as in pass 1. C88 is 0.9 mm from U9.5's pad end. C88.2 has a GND via at (42.9, 87.6).
- **Bucks.**
  - U2: C6 is 1.79 mm from VIN; the SW strap is 0.8 mm.
  - U8: U8.4 runs 0.6 mm B.Cu to C72.2 with a via at (43.41, 37.6). In1 and In2 are GND under both stages.
  - U8's junction estimate is unchanged from pass 1: about 100–105 °C at 70 °C using the single-layer θJA of 89 °C/W.
    That is inside R1's 110 °C. The four-layer board does better (Inference).
- **The RAW_PROTECTED gate-drive feed** (F.Cu 0.25 mm on y 99.75) runs through the band with GND on both sides at
  0.4–0.5 mm. No BAT_IN copper is beside it, so it creates no path round U9.
- **C121 (470 µF on RAW_ACT).** Its RAW_ACT pad sits in the F / B / In2 RAW_ACT pours. Its GND pad sits in the main
  F.Cu GND pour (2214 mm², 259 vias), with the nearest via 3.25 mm away. Adequate for bulk capacitance.
- **Mounting and tie holes.** The tie holes (21.5, 68.6) and (27.0, 82.6) have RAW_ACT at 0.5–0.8 mm. The ties are
  nylon, so this is not a finding. For the M3 hole at (42, 114.4), see POWER-02.
- **USB VBUS ringing on hot-plug** (4.7 µF ceramic, TPS2553 IN 7 V absolute maximum). This is a circuit item carried
  since R4, and it is a recorded bench check (M3_R4 l. 128, ORDERING §5). C83's move improves the HF bypass. There is
  no layout change to ask for.

## 5. Not verified

- I did not rerun the 0.05 mm qualification grid. The 0.1 mm run matches the build gate exactly, and the record's
  0.05 mm evidence is bound to the same SHA-256.
- The supply-path table (`step9/run_supply_dc.sh`) was read, not rerun.
- The hot-plug script was read, not rerun (it needs numpy).
- POWER-02's expected effects on the rebuilt board are Inferences until someone rebuilds and solves it.
- Every temperature and inductance figure above is an Inference unless it says "measured". I did no bench work.
