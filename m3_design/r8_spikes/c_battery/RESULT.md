# Spike 3(c) battery band: result

**Verdict: PASS, primary approach.** This is Strategy B's battery band, adapted to the C grafts that r8_plan §1
adopted: D18, and "In2 GND under every pyro/servo lane". The fallback (strategy C's battery corner) was not built
because the primary passed. As drawn, the fallback does not fit R8's rigid J122 anyway (§7).

All work is scratch. The scripts are in this folder and the boards are in
`$SCRATCH/r8_design/spike_c_battery/`. Nothing outside this folder was edited, and nothing is committed.

## 1. What passed (final scratch board `final/m3.kicad_pcb`, SHA-256 `15e33b31c377ee15…`)

| Check | Result |
|---|---|
| KiCad DRC on the spike nets (`drc_filter.py`; project `m3.kicad_dru` with rules A–H unchanged) | **0** copper violations and **0** unconnected items on BAT_IN, BAT_DAMP, ACT_FET_S, RAW_ACT, ACT_GATE / ACT_DRV / ACT_EN, BAT_SW_SOURCE / RETURN and RAW_ACT_SENSE_MID, and on band GND. No courtyard overlap involves a band part |
| `tools/route_check.py` (profile r8) | **0** failures and **0** instances (info-only included) on the spike nets and band GND |
| Rigid hash groups (`check_r8.rigid`, after a native fill) | **12 / 12 equal to R7's baseline** (strip_gcpw included) |
| D18 (`check_r8.inner_power_pyro`) | 0 issues. Nearest 2.65 mm: BAT_IN In2 to R134.1 (IGN), against a 2.5 mm minimum |
| M2 vias in SMD pads, bare-TP 1.0 mm, overlap-only joints, vias on THT pads (check_r7 functions) | 0 on spike nets / band parts |
| `m3_design/check_actuators.py` | actuator safety contract: OK |
| `tools/fit_check.py` | OK. No band part is among the binding margins. Supports unchanged |
| Rebuild | `base.py` and `battery.py` reproduce the board byte for byte (KIID seed 8301) |

**Pyro-rule margins, same layer, measured (`margins.py`).** Every one meets its minimum.
- **E**, RAW_ACT to BUS/IGN, 1.0 mm minimum: **1.300 mm**. This is the F.Cu strip edge, x 7.4, to J124.1.
- **A**, RAW_ACT to the control nets: 0.501 mm. The filler stops exactly at the rule, here at C127.1 (CONT).
- **A2**: 0.301 mm.
- **F**, other live nets to BUS/IGN/OUT: 0.501 mm (filler). RAW_ACT has no OUT copper within reach.
- **H**, live pads to ACT_GATE/ACT_DRV pads: **2.88 mm**. Each FET's own pads are exempt.
- **H**, RAW_ACT pads to sense/gate pads: **1.313 mm** (R177.1 to R124.2).

**7.7 A DC solve, `tools/run_dc.sh` at 0.1 mm** (`final/dc/`). D12 limits: RAW_ACT and BAT_IN at most 20 °C;
ACT_FET_S at most 30 °C, target 4.35 mm.

| Path | R (R7) | Neck: width, layer, place | IPC-2152 rise (R7) | D12 |
|---|---|---|---|---|
| RAW_ACT Q121:5–9 → J122:2,5,8,11 | **1.44 mΩ** (3.74) | **5.88 mm** F.Cu, at the J122 box entry, x 20.3–21.8, y 80.7–86.2 | **17.7 °C** (38) | OK |
| BAT_IN J1:1 → Q120:5–9 | **0.40 mΩ** (3.03) | **7.15 mm** B.Cu, at Q120's drain, x 17.1–20.4 | **14.1 °C** (30) | OK |
| ACT_FET_S Q120:1–3 → Q121:1–3 | **0.19 mΩ** (1.19) | **4.77 mm** B.Cu, across the facing-row bridge | **22.5 °C** (44) | OK |

Confirmation at 0.05 mm, the qualification grid (`final/dc05/`); all within D12:

| Path | R | Neck | Rise |
|---|---|---|---|
| RAW_ACT | 1.44 mΩ | 5.93 mm F.Cu | 17.5 °C |
| BAT_IN | 0.41 mΩ | 7.22 mm B.Cu | 14.0 °C |
| ACT_FET_S | 0.18 mΩ | 4.97 mm B.Cu | 21.5 °C |

The three paths total 2.03 mΩ, against R7's 7.96 mΩ.

## 2. Why B's seed band had to change (measured on the base board)

**The seed:**
- Q121 sat under the CH1 block at (29, 96.5) and fed an In2 RAW_ACT plane through a via field.
- That plane spanned y 67–102, under J122, the block and the pyro exits.

**The C grafts make this illegal:**
- The block's live copper runs across the board: J124.1 BUS at (10, 95.86), then the F.Cu BUS track, R134, the IGN
  track, and J121.2 at (36, 95.86). PYRO1_OUT runs from Q124 to J121.1.
- With a 2.5 mm plan-view margin, D18 closes In2 to power from about y 86 to y 100. Only two edge strips stay open:
  x ≤ 6.2 on the west and x ≥ 39.8 on the east.

**J122's RAW_ACT middle column is boxed in.** Pins 2, 5, 8 and 11 sit at x 23.
- The outer layers reach it only from its forward end, the "box" at x 19.65–25.1, y 80.4–86.4.
- **West of it:** the B.Cu pyro exits GATE_N, CONT and ARM1_SENSE run aft at x 17.8–19.0 (plan_partial §5.5), and
  In2 must be GND under them.
- **East of it:** the servo lanes enter the east column, again with In2 GND under them.
- **North:** the block.
- **The tie hole** at (27, 82.6) closes the box's east side, leaving channels of 1 mm or less.
- So RAW_ACT has to cross the pyro corridor exactly once, on F.Cu over B.Cu. This is plan C's "crossings only F
  over B".

## 3. The geometry to reuse (`battery.py` is the source of truth)

### 3.1 Topology: "west chain"

The chain runs:
1. J1.1, onto BAT_IN: a B.Cu pour, the In2 band and F.Cu under J1.
2. Q120, at rotation 90, drain east.
3. An ACT_FET_S bridge between the facing, aligned source rows.
4. Q121, at rotation 270, drain west.
5. RAW_ACT, down the **west strip** past J124 on F.Cu, In2 and B.Cu.
6. The **west region**, which holds J124.2, C121, C150/C151, TP120 and the RAW_ACT_SENSE divider.
7. An **F.Cu-only bridge** over the pyro corridor, y 79.6–88.0. It is F.Cu-only between x 16.5 and x 19.65,
   where B.Cu carries the pyro lanes and In2 is GND.
8. The **J122 box**: F.Cu, the B.Cu box and an In2 finger.
9. J122's middle column.

### 3.2 Placement (all B unless F is noted; changes from the seed `partial/b0_place_final.tsv`)

| Group | Parts |
|---|---|
| FET pair | Q121 (8.0, 103.0, 270). Q120 (16.38, 101.72, 90) = Q121 + (8.38, −1.28): source rows aligned, 1.5 mm pad-edge gap. Each gate is outside the bridge, Q121's at the forward end and Q120's at the aft end (D12) |
| Gate-source network, on the bridge's forward end | C120 (12.5, 106.6, 270); R120 (14.3, 106.87, 270) |
| Gate drive, on F east of the ACT_GATE hop (x 13.48) | TP121 (13.48, 103.2) F; R121 (13.91, 100.85, 0) F; Q122 (16.6, 100.85, 0) F; R122 (17.6, 103.36, 90) F; R123 (18.9, 102.5, 90) F |
| Switch legs, under J1's body | R80 (20.46, 107.9, 270) at J1.3; R165 (16.6, 107.9, 90) at J1.4 |
| Input protection at J1.1 | D8 (32.3, 101.6, 90); C80 (35.8, 102.3, 90); C96 (38.9, 102.3, 90); R167 (34.3, 108.4, 270). Damper on the top strip, aft of J1's body: C89 (24.0, 102.15, 90) F, C95 (26.5, 102.15, 90) F, R166 (32.2, 101.7, 0) F |
| eFuse input side (U9 stays at the seed, (41, 91.4)) | C88 (41.17, 93.6, 0), R82 (39.93, 95.2, 180) and TP80 (40.75, 97.8) on the BAT_IN feed at x 40.75. R81 (38.6, 92.8, 90), C87 (38.6, 89.6, 90), C81 (37.9, 86.0, 0) and R83 (43.0, 96.1, 90) nudged clear |
| eFuse output parts, aft of U9 | D9 (43.6, 79.5, 90); C82 (39.6, 78.6, 0); R92 (39.6, 81.6, 0). GND test pads TP74 (44.6, 99.0) and TP88 (44.6, 101.6) |
| RAW_ACT bulk | C121 (12.0, 83.8, 180) F, with its RAW_ACT pad east on the bridge. C150 (8.0, 81.8, 90) and C151 (5.4, 81.8, 90) straddle the B.Cu pour's aft edge. TP120 (3.0, 88.0) |
| RAW_ACT_SENSE divider, in a notch at x 12.6–16.5, y 81.8–85.3 | R177 (13.2, 85.61, 90), R124 (14.6, 85.18, 0), R125 (13.6, 83.23, 90), R182 (14.6, 83.23, 90), C122 (15.85, 82.96, 90). The SENSE lane joins the pyro corridor at x 17.2 |

### 3.3 Copper (zones: FULL connection, 0.3 mm clearance, 0.3 mm minimum width)

**B.Cu**
- **ACT_FET_S bridge:** priority 40, x 9.6–14.78, y 97.6–106.9.
  - It extends aft to y 97.6 so that copper passes south of via B, which reconnects the aft lobe.
  - Without that, the neck is 4.34 mm.
- **RAW_ACT west:** priority 36. It covers the strip x ≤ 7.4 at J124.1 (rule E), Q121's drain area up to y 108, and
  the west region y 81.8–93.2 up to x 16.5, with the divider notch.
- **RAW_ACT box:** priority 36, x 19.65–25.1, y 80.35–86.9, plus the middle-column strip x 21.3–24.7 down to y 70.9.
- **BAT_IN:** priority 34.
  - It runs from Q120's drain (x ≥ 15.0) to x 31, then over y 101.9–105.6 to x 41.3 (the D8 / C80 / C96 BAT_IN
    pads).
  - It wraps J1.1 in a lobe at x 27.8–33.4 up to y 112.6, and stays 0.5 mm clear of J1.2 / J1.3 / J1.4.

**F.Cu**
- **RAW_ACT:** priority 36. It covers:
  - the west strip and region, x ≤ 7.4 at y 93–109.5, and x ≤ 12.8 at y 99.9–108;
  - a GND bay at C121's GND pad, x 6.6–10.8, y 79.6–84.8;
  - the bridge, x 15.8–19.7 / 21.3 up to y 88.0;
  - the box, up to y 86.3: rule A at C127 and R127;
  - the middle-column strip.
- **BAT_IN:** priority 34. It lies under J1's body, x 17–33.5, y 104.9–108.6, around J1.1, with a dip to y 103.0 at
  the damper's BAT_IN pads.

**In2**
- RAW_ACT west, priority 12: x 0.5–16.4, y 79–91.6; the strip x ≤ 6.0 to y 100.3; and x ≤ 11.0 at y 100.3–108.
- RAW_ACT J122 finger, priority 12: x 20.2–24.6, y 70.5–86.4.
- BAT_IN band, priority 12: x 12.4–45.5, y 100.3–117.5.
- GND as the band's background, priority 8. It lies under the block, the pyro corridor (x ≈ 16.7–20) and the servo
  corridor (x ≥ 24.9).

**ACT_GATE**
- On B.Cu: Q121.4's stub runs north to a bus at y 107.3 (C120.2, R120.2) and on to via A at (13.48, 107.3). A stub
  runs from Q120.4 to via B at (13.48, 98.95).
- On F.Cu: a straight hop at x 13.48 carries R121.1 and TP121.

**Other tracks:** ACT_DRV and ACT_EN locally on F; BAT_DAMP on F at y 100.675, with a 45° step into R166.1; the
BAT_IN feed to U9.5 (0.5 mm, then 0.3 mm into the pad); short switch legs to J1.3 and J1.4.

**Via fields** (0.6 / 0.3 mm, pitch 1.4 mm, so that In1 keeps webs between antipads):
- RAW_ACT 66: the strip, Q121's drain, the west region and the J122 box (first column at x 20.6);
- BAT_IN 15: north and east of Q120's drain;
- GND 7;
- ACT_GATE 2.

## 4. Proposed R8 decisions (for the orchestrator to number and merge into R8_DECISIONS; this spike edits no file outside its folder)

1. **Battery-band topology: "west chain"** (§3.1), replacing B's seed band.
   - Basis: D18; r8_plan §1, "In2 GND under the CH1 pads and every pyro/servo lane"; J122, the tie holes and the CH1
     block are rigid (D15); measured in §2.
   - J1, the switch, the input chain and the In2 BAT_IN band stay at J1, as B intends (F9 premise: every input part
     within about 22 mm of J1.1).
2. **FET pair.**
   - Q120 at rotation 90 with its drain east, and Q121 at rotation 270 with its drain west, side by side.
   - The source rows face each other and are aligned, with a 1.5 mm gap, so neither gate lies inside the bridge.
   - Measured: 4.77 mm and 22.5 °C at 0.1 mm; 4.97 mm and 21.5 °C at 0.05 mm. That beats D12's 4.35 mm target.
   - A bare bridge with no gate stubs gives 5.51 mm (`fet_exp.py`). The gate stubs cost about 0.5–0.7 mm.
3. **ACT_GATE takes a 2-via F.Cu hop.**
   - With facing rows the two gates sit at diagonally opposite corners of the bridge. A B.Cu path would have to cut
     the bridge or ring one FET's drain, and In2 carries power only (D20).
   - ACT_GATE is not a route_check critical net, and 2 vias are within its via budget.
   - This replaces plan A's "ACT_GATE on local B.Cu", which assumed R7's FET geometry.
4. **In2 map in the band** (§3.3).
   - RAW_ACT and BAT_IN stay at least 2.5 mm, in plan view, from the block's live copper (measured 2.65 mm).
   - GND lies under the block and both lane corridors.
5. **Gate drive on the top side, east of the hop.**
   - R122.1 (RAW_PROTECTED) is then reachable from the east without crossing ACT_GATE.
   - Rule H margin 2.88 mm.
   - These parts sit inside the PYRO_BLOCK rectangle. The coating mask is part-based (ORDERING §5); confirm in step 9.
   - TP121 moves to the top side, which ORDERING's probe-point list must reflect.
6. **Input protection.**
   - D8, C80, C96 and R167 sit on B at J1.1, the damper on F aft of J1's body, and U9 at its seed position. The eFuse
     input parts sit on a BAT_IN feed at x 40.75.
   - The eFuse output parts move aft of U9, because OUT leaves U9.6 southward.
7. **The RAW_ACT_SENSE divider** sits in the west region's notch, with R177.1 on RAW_ACT (H 1.31 mm). Its lane is
   the pyro corridor's west slot, x 17.2, joining ARM1_SENSE's route to U1's east face.

## 5. Interfaces with the other spikes and steps (assumed here; reserved by tracks or keep-outs on the scratch board)

**Pyro exits** (step 6, `pyro_exits`):
- Reservation lanes on B.Cu, 0.2 mm wide:
  - GATE_N runs (23, 88.33) → west at y 88.33 → aft at x 18.4.
  - CONT runs (28.4, 88.61) → west at y 87.6 → aft at x 19.0 (rule G 0.3 mm to GATE_N).
  - ARM1_SENSE runs (18.18, 91.3) → aft at x 17.8.
  - RAW_ACT_SENSE runs aft at x 17.2.
- The band's copper is DRC-legal against them.
- **If the lanes move**, re-check the box's west edge (19.65) and north edge (86.9) and the west region's east edge
  (16.5).

**Servo** (spike 3(b)):
- The band keeps every RAW_ACT layer at x ≤ 25.1 near J122.
- In2 is GND for x ≥ 24.9 (rule: In2 GND under servo lanes).
- J122's east column is untouched.

**Not routed here; reserved:**
- **BAT_ENABLE** (R165.2 → U9.1, with a via at (16.6, 106.0)) and **RAW_PROTECTED** (U9 → R122.1). They have F.Cu
  lanes on the top strip at y 99.25 and 99.75, east to x 38.5.
  - The strip is free between the block (R175's pad top at 98.95) and the damper row (pads at y ≥ 100.05).
  - R166 had to sit at y 101.7 to leave room for both lanes.
- **U9's network** (EN, OVLO, ILIM, DVDT, FLT) and its test pads are only partly legalised. This is step 4 and
  step 6 work.
- **The rest of RAW_PROTECTED aft** has no route yet.

## 6. Open items and risks (none unsafe; none needs the owner now)

- **RAW_ACT neck margin is 0.6 mm** (5.88 mm against 5.28 mm).
  - The neck is the F.Cu-only entry to the J122 box, between J122.3 and the rule-A limit at C127 / R127.
  - Raising the F.Cu outline under R127 (step to y 87.35) gives 6.17 mm and 16.7 °C, but starves the thermals of the
    block's GND pads C127.2 and R127.2. It was reverted.
  - Other ways to widen it: a GND via at C127.2 / R127.2 inside the block, or step 4 moving J122's pyro-side
    neighbours. Neither is needed for D12.
- **The ACT_GATE hop** is two layer changes on a slow gate signal. It is inherent with facing rows (decision 3).
- **D20 conflict found in the rigid copy:** check_r8 flags R7's **ARM1_SENSE In2 link** (CH1 block internal, 3.4 mm,
  at (14.55, 94.15–97.55)) as In2 signal copper. It is rigid `ch1_copper`, so it conflicts with D20 = 0. Step 1 or the
  orchestrator must resolve this; it is not band copper.
- **In1 coverage:** 83 band vias cross In1, at 1.4 mm pitch with 1.1 mm antipads. Measure P1 / P3b in step 5.
- **Seed placement issues outside the band remain:** TP clearances in the camera area, C8/C9, C70/R74, C85/R91 and
  C90/R103 courtyards. These are step 4 (legaliser) work.
- **Panel tabs:** C151 (x 5.4) blocks a left-edge tab window at y about 80–84. The planned tabs at y 75 and 100 are
  unaffected. Run `partial/tabs.py` in step 4.
- **Silkscreen** is not placed here (step 8).
- **BAT_IN's neck** fell from 8.25 mm to 7.15 mm once the via column moved for the RAW_PROTECTED reservation and a
  GND via was added north of Q120's drain (14.1 °C, still well inside 20 °C).

## 7. Strategy C's battery corner (fallback): not needed, and it does not fit as drawn

- C put Q120/Q121 at J1.1 (east), ran a three-layer RAW_ACT spine down the east edge, and fed J122 through an
  F.Cu + In2 band at y 76.3–81.
- C moved J122 to (23, 71.5) and moved the tie holes. With R8's rigid J122 at (23, 75.7):
  - that band lands on J122.1 / J122.4 (servo pins);
  - its F.Cu could reach the middle column only through 0.34–0.4 mm gaps;
  - the box at the column's forward end is closed from the east by the tie hole at (27, 82.6).
- C's own figures also show its BAT_IN neck at Q120's drain-pad row as 4.27 mm, which is 25.6 °C and outside D12's
  20 °C.
- Making C work would need a J122 or tie-hole move (rigid, D15), or In2 RAW_ACT under the servo lanes (against
  r8_plan §1).

## 8. Reproduce

```bash
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
SC=$SCRATCH/r8_design/spike_c_battery          # session scratchpad
cd rocket-pcb/rocket-flight-computer-r8
git show 431025d:m3_design/assembly_review/m3.kicad_pcb > $SC/r7.kicad_pcb                       # c872a3d3...
cd m3_design/r8_spikes/c_battery
PYTHONUNBUFFERED=1 $KPY -I base.py $SC/r7.kicad_pcb $SCRATCH/r8_design/partial/b0_place_final.tsv $SC/base  # 638e76d3...
PYTHONUNBUFFERED=1 $KPY -I battery.py $SC/base $SC/final                                         # 15e33b31...
kicad-cli pcb drc --severity-all --format json -o $SC/final/drc.json $SC/final/m3.kicad_pcb
python3 drc_filter.py $SC/final/drc.json                                                         # 0 / 0
(cd ../../.. && $KPY -I tools/route_check.py $SC/final/m3.kicad_pcb --report $SC/final/route.json)
PYTHONUNBUFFERED=1 $KPY -I verify.py $SC/final/m3.kicad_pcb $SC/final/route.json                 # hashes, D18, M2
PYTHONUNBUFFERED=1 $KPY -I margins.py $SC/final/m3.kicad_pcb                                     # rules A-H margins
(cd ../../.. && bash tools/run_dc.sh $SC/final/m3.kicad_pcb $SC/final/dc 0.1)                    # D12 verdicts
```

**Pitfalls found:**
- **`BOARD.Remove` breaks later SWIG proxies** in this KiCad build. Use `BOARD.Delete`.
- **The base keeps R7's stale fills.** `BuildConnectivity` then re-nets new vias from them, so RAW_ACT vias turned
  into GND. `battery.py` therefore UnFill()s first and asserts that no via changed net after the fill.
- **A via placed on a foreign pad is silently re-netted**, which is how one first-draft GND via ended up in Q121's
  drain pad. The same assertion catches this.

**Files in this folder:**

| File | Purpose |
|---|---|
| `base.py` | Builds the scratch base board |
| `battery.py` | The band's placement and copper |
| `fet_exp.py` | The bare-bridge ACT_FET_S experiment (§4, decision 2) |
| `drc_filter.py` | Filters the DRC report to the spike's nets and parts |
| `verify.py` | Hashes, D18 / D20, M2 / TP checks, route_check filter |
| `margins.py` | Rule A–H margins |
| `PROGRESS.md` | Running log |
