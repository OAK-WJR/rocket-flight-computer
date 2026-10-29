# R8 step 5 handoff: power

**Status:** done, and the step's verification passes in full (below). Nothing is committed (the brief forbids commits).
- Branch `m3-assy-r8`, worktree `rocket-flight-computer-r8`.
- `m3_design/r8_build.sh` now ends with the power stage and its gate. The worktree board
  `m3_design/assembly_review/m3.kicad_pcb` is the R8 step-5 board, SHA-256 `1818b05f…`
  (`1818b05f43af53ec76cda0a26368b2aa325ef853bfeb6c5e0b39d1e46bff22ef`).
- The sheets and `schematic.net.xml` are step 2's, byte for byte (netlist `0cc1ed69…`).
- Decisions taken in this step: R8_DECISIONS **D40–D50** (read them first; summary below).

## What this step produced

| File | Content |
|---|---|
| `m3_design/r8_power.py` (new) | **The power copper**, on r8_pcb.py's placed board, in place: the In2 map, spike (c)'s 7.7 A band, RAW_PROTECTED, the logic supplies, the camera supplies, every power part's GND via; native fill; vias' nets asserted; the 12 rigid digests asserted. Deterministic (KIID seed 8805) |
| `m3_design/r8_power_check.py` (new) | Step-5 gate: 8 gates, listed under verification |
| `tools/test_r8_power.py` (new) | 7 tests: seeded defects for the in2, inner, drc / complete, stale-reservation gates and the narrowness of the exemptions |
| `m3_design/r8_build.sh` | Appends `r8_power.py` and `r8_power_check.py` after the placement gate |
| `m3_design/r8_place.tsv` | 45 rows amended for the power stages (basis D40–D44, D46); every placement gate still passes |
| `m3_design/r8_keepclear.tsv` | Regenerated: 343 rows (D48: the 186 rows step 5 builds dropped; D45's chamfer; D50's 19 status-lane rows) |
| `sources/r8_design/step4/make_keepclear.py` | D45 chamfer; `BUILT_BOARD` argument and `BUILT_NETS` (D48); `STEP5_TRACKS` / `STEP5_VIAS`, family s5 (D50) |
| `sources/r8_design/step5/power_report.json` (new) | The gate report on the final board |
| `R8_DECISIONS.md` | D40–D50 appended; pointers added in D29 (strip_gcpw re-asserted), D31 (table regenerated), D36 (R92, x 45.2) |
| `r8_step5_progress.md` (new) | Running log |

**`r8_power.py` sections:**
1. **In2 (D47).** The GND plane is the board less the other regions, with no GND rings in them. The 3V3 region sits
   under the MCU zone, with the pyro-corridor notch and GND east of x 35.3 under both bucks. Spike (c)'s RAW_ACT west
   island, J122 finger and BAT_IN band follow, then the Y1 keep-out and an L1.2 pour trim.
2. **Band.** Spike (c)'s "west chain": the BAT_IN / ACT_FET_S / RAW_ACT pours on F.Cu, B.Cu and In2, the via fields,
   the ACT_GATE network, the switch legs, the damper and the BAT_IN feed to U9. D43 nudges apply. It replaces D29's
   placeholder `R6_BAT_IN_crossbar_F`.
3. **RAW_PROTECTED (D46).**
4. **Logic (D40, D42, D44).** USB_LIMITED, VLOGIC, the 3V3 buck and its output to In2, the 3V3 F.Cu spine to D121 /
   D120 / R89, the 3V3A filter and trunk, spike (a)'s U1 decoupling / VCAP, and the R164 / R62 / C90 3V3 taps.
5. **Camera (D41).** CAM_INPUT_LIMITED, the buck, and CAM_5V to J9.1 with its sense.

## Decisions in one screen (details in R8_DECISIONS)

- **D40 / D41: both bucks follow the makers' layouts** (Diodes DS41326 Fig. 25, DS42002 Fig. 39).
  - SW is a short strap into the inductor.
  - Cin sits across VIN / GND, BST is local, and Cout sits at the inductor's output.
  - In1 and In2 are GND under both stages.
  - The camera buck's feedback sits on the top over U8 and senses CAM_5V at J9.1's feed via.
- **D42: U11 (TPS2121) at rotation 90.** USB_LIMITED arrives with 2 vias and a minimal 45° F.Cu hop over the RAS
  lane. VLOGIC is one 0.5 mm column through C99 / C6 / U2 VIN / EN, with one via to the hold-up C84.
- **D43: C120 / C88 nudges**, putting the gate bus and the BAT_IN feed on pad centres.
- **D44: the 3V3A column** runs R164 / C10 / C11 into the VDDA pins. Its trunk end (15.0, 62.2) is the one PENDING
  item; step 6 continues it.
- **D45: the RAS lane's chamfer** moves north-east, opening the 3V3A door.
- **D46: RAW_PROTECTED.**
  - A B.Cu column under U9.6 through D9 / C82 / TP81; R92 moves to the top.
  - A 0.5 mm F.Cu trunk down the east edge (x 45.2), between J9's pads, to U7.
  - A 0.4 mm branch to U11 and R122's 0.25 mm feed.
  - No pour. 12 °C at the 1.54 A worst load.
- **D47: the In2 map.**
  - Islands: GND 1, 3V3 1, RAW_ACT 2, BAT_IN 1.
  - D18's nearest copper is 2.65 mm.
  - GND under the CH1 pads (+0.5 mm) and under every pyro / servo B.Cu lane, except the MCU-end dives inside U1's
    field, which spike (a) verified over the 3V3 plane.
- **D48: scope and reservations.**
  - What step 5 builds and what it leaves to step 6 are listed in D48.
  - The reservation table is regenerated against the power copper and gated by an overlay and a stale-row check.
  - Three conflicts were fixed in step-5 copper: C76's GND via, the 3V3 spine past D121's GND via, and the RAS
    chamfer.
- **D49: DC figures** (table below).
- **D50: BAT_FAULT_N and LOGIC_SOURCE_ST lanes reserved.** The power copper leaves one clean way to U1 pins 28 / 29,
  and the reservation keeps it.

## How it was verified

`m3_design/r8_build.sh` runs in about 25 s and exits 0. It ends `R8 placement gate: OK` then `R8 power gate: OK`.
All 8 gates of `r8_power_check.py` pass on `1818b05f…`:

| Gate | Result |
|---|---|
| rigid | 12/12 check_r8 digests equal R7, strip_gcpw included (after the placeholder pour's swap) |
| drc | kicad-cli DRC, `--schematic-parity`, every severity, pyro rules A–H of m3.kicad_dru included: 0 violations, 0 parity items. Allowed: unconnected items of later-step nets; 4 `via_dangling` on the rigid exits; 1 on the 3V3A trunk end (PENDING); the silk classes r8_post settles |
| complete | every net with step-5 copper is fully joined (20 nets), except the shared rails 3V3 / 3V3A / CAM_5V / GND, whose open pads are step 6's (taps, sensors, U13) or the sensors' GND under their rule areas |
| pyro | D18 inner_power_pyro: 0 issues, nearest 2.65 mm (BAT_IN In2 to R134.1 IGN). D19 gate_servo: 0 issues |
| inner | no In1 / In2 track besides the rigid CH1 ARM1_SENSE link |
| in2 | islands GND 1 / 3V3 1 / RAW_ACT 2 / BAT_IN 1; no non-GND In2 fill within 0.5 mm of the 47 CH1 pads; none under any of the B.Cu pyro / servo lanes, built or reserved, outside U1's field |
| route | route_check profile r8: 20 failures, all allowed: 15 on the rigid exits (step 6) and 5 at the PENDING 3V3A trunk end. No other failure. Information only: width_change_junction 14, pad_end_offcentre 7, passes_through_pad 5, power_via_no_gnd 18 (step 7 stitches GND), extra_bends 1 (R122's lane, D46), short_layer_hop 1 (USB_LIMITED's minimal hop, D42) |
| reserved | the 343 reservations drawn over the power copper: 0 DRC copper-rule violations; 0 stale rows |

**7.7 A DC** (`tools/run_dc.sh`, D12 limits; D49):

| Path | 0.1 mm grid | 0.05 mm grid | D12 requirement |
|---|---|---|---|
| RAW_ACT | 5.89 mm F.Cu, 17.7 °C, 1.44 mΩ | 5.93 mm F.Cu, 17.5 °C, 1.44 mΩ | ≥ 5.3 mm outer, ≤ 20 °C |
| BAT_IN | 6.87 mm B.Cu, 14.8 °C, 0.41 mΩ | 7.00 mm B.Cu, 14.5 °C, 0.41 mΩ | ≥ 5.3 mm outer (5.6 inner), ≤ 20 °C |
| ACT_FET_S | 4.78 mm B.Cu, 22.5 °C, 0.19 mΩ | 4.97 mm B.Cu, 21.5 °C, 0.18 mΩ | ≥ 3.71 mm B.Cu (target 4.35), ≤ 30 °C |

The rises are IPC-2152 estimates (Brooks & Adam fit, no plane credit), an upper bound and an **Inference**, not a
measurement. Supply-path resistances are in D49. Every R8 path is lower than R7's except RAW_PROTECTED U9 → U11 and
BAT_IN J1 → U9 (U9 moved aft, D36); both drop under 25 mV.

**Other checks:**
- **Byte-identical rebuild:** two consecutive `r8_build.sh` runs give the same board SHA (`1818b05f…`) and the same
  netlist SHA (`0cc1ed69…`).
- **Tests** (KiCad Python): `test_r8_power` 7, `test_r8_place` 13, `test_r8_check` 19, `test_route_check` 57,
  `test_fit_check` 23, `test_check_shell` 2, `test_r7_check` 35 and `test_dc_solve` 3, all OK.
- **Placement gate** with the amended table: all 11 gates OK.
  - MST 1603.1 mm (step 4: 1632.5).
  - Fit unchanged from D39: minimum 0.028 mm (J9 mated), worst bottom part 2.357 mm (C91), supports 4.70 / 5.008 mm.
  - Tabs and F10 unchanged.
- **Full `check_r8`** on the step-5 board: 21 findings, every one for a later step:
  - C100 / C93 U12 bypass routes (step 6);
  - J2 / J9 pin legends (r8_post);
  - strip fence row and strip GND reach (steps 6/7);
  - the rigid ARM1_SENSE In2 link (step-4 open item 1).

  Step 4's five In2 findings (strip, launches, U31) are resolved. No pin-map, pull, loader, F10, rigid, inner-power,
  gate-servo or TH finding. `check_actuators.py`: OK.
- **Visual review** of the In2 map and both buck stages at 50 px/mm. The scratch viewer and the renders are in the
  session scratchpad `r8_step5/`; neither is needed to rebuild.

## Reproduce

```bash
cd rocket-pcb/rocket-flight-computer-r8
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
m3_design/r8_build.sh                                         # ~25 s; ends "R8 power gate: OK"
shasum -a 256 m3_design/assembly_review/m3.kicad_pcb          # 1818b05f43af53ec...
(cd tools && PYTHONUNBUFFERED=1 $KPY -m unittest test_r8_power test_r8_place)
PYTHONUNBUFFERED=1 $KPY -I m3_design/r8_power_check.py --report /tmp/power.json
PYTHONUNBUFFERED=1 $KPY -I tools/check_r8.py m3_design/assembly_review/m3.kicad_pcb     # 21 later-step findings
tools/run_dc.sh m3_design/assembly_review/m3.kicad_pcb /tmp/dc01 0.1                     # ~2 min
tools/run_dc.sh m3_design/assembly_review/m3.kicad_pcb /tmp/dc005 0.05                   # ~40 min
```

**Reservations after an r8_power.py change.** The gate's stale-row check fails until you regenerate. The table needs
the placed board, which the build overwrites. Make it on a copy, then pass the step-5 board as BUILT_BOARD:

```bash
D=/tmp/r8p; mkdir -p $D && git show 431025d:m3_design/assembly_review/m3.kicad_pcb > $D/m3.kicad_pcb
cp m3_design/assembly_review/m3.kicad_{pro,dru} $D/
PYTHONUNBUFFERED=1 $KPY -I m3_design/r8_pcb.py --board $D/m3.kicad_pcb
PYTHONUNBUFFERED=1 $KPY -I m3_design/assembly_review/sources/r8_design/step4/make_keepclear.py \
    $D/m3.kicad_pcb m3_design/r8_keepclear.tsv m3_design/assembly_review/m3.kicad_pcb
```

Checked: on the final board this recipe reproduces the committed table byte for byte.

## What the next steps must know

1. **Step 6 starts from this board** (`r8_build.sh` appends the routing modules after `r8_power_check.py`) and routes
   against the 343 reservations.
   - Do not port spike (a)'s 3V3 / 3V3A / VCAP / decoupling copper and GND vias, spike (b)'s D121.5 3V3 via and stub,
     spike (c)'s band, or the s4 RAW_PROTECTED / VLOGIC / BAT_IN / RAW_ACT rows. Step 5 drew them, and they are gone
     from the table.
   - `make_keepclear.BUILT_NETS` lists the nets step 5 completed. Step 6 must not touch them.
2. **Step 6 must finish:**
   - **3V3A** from the trunk-end via (15.0, 62.2) to U4 / U5 / C30–C32. r8_power_check's PENDING entry names it.
     check.sh has no exemption, so the board fails until it is joined.
   - **VBUS** at J3 / D4 / U10.
   - **The U13 cluster:** CAM_5V from C75 / L3.2 to U13.1 / C91, R104 by the s4 lane (39.4 → 35.73, y 47.7), and
     CAM_IO_3V3.
   - **3V3 taps into the In2 3V3 region** (x ≤ 35.3, y 24–70, west tongue to 81.3) for J2, R90, R11–R13, R76, LS120,
     D122 / D123, R161, U12 / C100, FB30 / FB31 / R310.
   - **The eFuse / mux control nets.** BAT_FAULT_N and LOGIC_SOURCE_ST have reserved lanes (D50). Without them the
     power copper leaves no clean way.
3. **Hard walls the power copper makes** (plan around them):
   - the F.Cu RAW_PROTECTED trunk on x 45.2 (y 83.7 → 51.5), its branch on y 62.6 (x 35.25–45.2), and the run on
     x 42.15 / y 25.6;
   - the 3V3 B.Cu output line on y 70.4 (x 35.15–42.6) and the F.Cu spine (x 34.4 → 35.2, y 69.65–82.0) with its line
     on y 82.0 (x 32–39.3);
   - the VLOGIC column x 36.75 (B.Cu, y 57.9–66.6);
   - USB_LIMITED's B.Cu x 29.95 (y 37.25–54) and y 37.25 (x 16.3–29.95).
4. **In2 is final** except where a later step adds an island. A signal track on In2 is forbidden (D20).
   - A B.Cu lane over In2 3V3 is acceptable only inside U1's field (D47).
   - Elsewhere, pyro and servo lanes must stay over GND. r8_power_check gates this for every reserved and built
     lane, and the full check (step 8) must keep it.
5. **Step 7 (GND).** route_check reports 18 `power_via_no_gnd` (information). The camera and 3V3 buck GND returns
   rely on the B.Cu GND pour plus one via per capacitor. Stitching should add GND vias beside the RAW_PROTECTED /
   VLOGIC / USB vias where room allows.
6. **Step 8 / 9.**
   - TP75 / TP76 (camera-wire test pads) and R92 are now on the top side: coating mask and ORDERING probe list.
   - The J2 / J9 pin legends are still r8_post's.

## Left open (not escalated; none is unsafe or changes a requirement's intent)

1. **Step-4 open item 1 (D15 against D20)** stands. The rigid ARM1_SENSE In2 link is check_r8's only In2 finding.
   r8_power_check's `inner` gate admits it, as rigid copper only.
2. **Step-4 open item 2 (strip_gcpw fragility)** stands. The step-5 F.Cu power pours keep the digest equal to R7's.
3. **Remote sense of CAM_5V at J9.1's feed via (D41)** is an **Inference**: stable, because the sense point is the
   output node 2–3 mm from the output capacitors. Verify on the bench, with the camera's load step.
4. **The RAW_PROTECTED trunk at the 2.2 A current limit** is estimated at a 24.6 °C rise (IPC-2152 upper bound,
   fault state). At the 1.54 A worst steady load it is 12 °C. Both are estimates, not measurements.
5. **No independent review** of the step-5 generator, gate and table was possible inside this step (r8_plan §4). The
   orchestrator schedules it.
