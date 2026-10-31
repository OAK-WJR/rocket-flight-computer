# Round 18 fix pass: CAD lane (hand-back)

Scope: the generators (`m3_design/r10_*.py`, `r10_place.tsv`, `r10_fanout.tsv`), the footprint library, the checks
(`tools/check_r10.py`, `m3_design/check_actuators.py`, `tools/export_fab.py`, `tools/jlc_orient.py`,
`tools/jlc_easyeda/pads.json`) and their tests, the design records (`circuit.json`, `pin_table.tsv`,
`R10_DECISIONS.md` D-R18-01..10, `AVA_LAYOUT.md`, `r10_plan.md`) and everything `m3_design/r10_build.sh`
regenerates. No native CAD was hand-edited. STATUS.md, AGENTS.md, docs/*.md and parts_qualification.md were not
touched; no git state was changed. AGENTS section 2 is unchanged. Machine-readable twin: `round18_fix_cad.json`.

## New board

PCB `a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918`, 46 x 90 x 1.6 mm, 2,250,842 bytes;
208 footprints, 947 segments, 292 vias (166 GND), 1788.737627 mm track.
R17 `632a9ad3…`: 2,256,162 bytes; 209 footprints, 951 segments, 296 vias (168 GND), 1788.675665 mm track.

- Footprints: R62 and R63 removed; R119 added; R173 and TP121 moved. Every other pose, land, net and support is
  unchanged; the IMU axis map (roll = -gyro_Y) and the U1 pin map (except PC3_C, now NC) are unchanged.
- Vias removed: V3V3_SENSE (25.5,51.75), 3V3 (25.07,54.7), GND (25.07,57.6), GND (25.8,65.9). Moved: ACT_GATE
  (11.8,70.725) -> (11.14,71.7); GND (16.178,59.047) -> (15.8,59.425).
- Six fill-only rule areas `R18_BARREL_KEEPOUT_*` (two ACT_GATE vias, three BAT_ENABLE vias, J400.2).
- Silkscreen designators (r10_post's unchanged rule): 91 -> 88 hidden. R91 is newly hidden (kept on F.Fab); R132 and
  R163 are now shown; R119 and TP121 are shown.

## Builds and gate

- **Two complete `m3_design/r10_build.sh` builds (A and B)**, KiCad CLI 10.0.7, `NUMPY_PY=.supervisor/venv/bin/python`:
  both exit 0, each ending in `tools/check.sh` exit 0. The PCB is `a3144b15…` in both (and in an earlier build 1 of
  the same board inputs). Across A and B, 923 files (board, sheets, netlist, libraries, binding note, budget, hot-plug
  inputs/results, BOM / owner BOM / CPL, `tools/jlc_corrections.json`) are byte-identical; only the date-stamped
  Gerber zip, assembly PDFs and manifest differ, plus the supplier reports refreshed between them (below).
- **Per-family stage gates:** core / usb / pyro / power / signals / ground all OK (no route_check failure outside the
  pending nets; after ground: DRC 0, unconnected 0, route_check 0).
- **check.sh:** DRC 0 / unconnected 0 / schematic parity 0 / ERC 0; metadata and 3D-model audit OK; silkscreen outline
  0; `r10_parts --check` OK; fit OK; **check_r10 full contract 33 rules OK** (32 + new K-plane; S-3 and S-8
  extended); route_check r10 0 failing (22 bump windows); fab manifest OK (6 outputs). Self-tests: shell 7, procurement
  20, fit 31, paste 16, r10_parts 5, route 67, **R10 187** (180 + 7 new; 4 native NumPy skips) and HotplugNumerics 2
  under NumPy: all OK.
- **Fab package (`r10_fab.sh`):** orientation CHECK none; 81 JLC BOM lines, 197 placed (CPL 65 top / 120 bottom
  rebuilt from JLC footprints plus 12 placement-only checks, worst pad residual 0.491 mm); owner BOM C84 (C46550466);
  S-4 OK; paste F 245 / B 371 flashes on as many pasted pads; manifest bound to `a3144b15…`.
- **Supplier refresh** (`FAB_NET=1 m3_design/r10_fab.sh`, exact codes, stock 2026-10-30T23:50:54Z, cost 23:51:50Z;
  both reports' input hashes match the final BOM / owner BOM / CPL): the only short line is U4 (0 < 5, consigned); U9
  45; R430 C2999509 84,923. $79.12/board placed plus feeder share (81 charged codes), $54.33/board parts with minimum
  purchases; target $84.41 met before fixed, process, PCB and shipping costs (not a release pass).
- **Binding note:** regenerated from the finished board; K-binding OK.
- **Final standalone `tools/check.sh`** on the finished tree (after the supplier refresh and these records): exit 0,
  same results as above.
- **New tests:** `Synthetic.test_s3_local_gate_bias_needs_same_layer_copper`,
  `R3Synthetic.test_s8_load_switch_gate_and_enable_barrels`, `R3Synthetic.test_k_plane_split_fill_needs_two_links`,
  `RealBoardSeeds.test_r18_barrel_keepouts_removed`, `RealBoardSeeds.test_r18_split_power_plane`,
  `RealBoardSeeds.test_r18_q121_local_bias_seed`, `RealBoardSeeds.test_r18_manual_fit_c84_s4`; the
  BOM-identity seed now writes `m3_bom_jlc.csv` beside the owner BOM.

## Per item (brief numbering)

All gaps are edge to edge, measured on the native boards (pcbnew 10.0.7 shapes, `check_r8.min_gap`).

| # | Finding | Status | Change | Before -> after |
|---|---|---|---|---|
| 1 | R18-SAF-01, R18-GATE-01 | Done (D-R18-04) | Fill-only keep-outs (radius drill/2 + 1.05 mm) round every ACT_GATE / ACT_DRV barrel on In1 and In2, and every BAT_ENABLE / BAT_SW_RETURN / ACT_EN / ACT_EN_MCU / PYRO1_GATE_N barrel on In2. S-8 covers these nets; GND counts as foreign for ACT_GATE / ACT_DRV | ACT_GATE barrels (both): In1 GND 0.251 -> 1.050, In2 RAW_PROTECTED 0.251 -> 1.050. BAT_ENABLE barrels (three): In2 RAW_PROTECTED / 3V3 0.251 -> 1.050 (In1 GND 0.251 kept, fail-safe). J400.2: In2 RAW_PROTECTED 0.551 -> 1.050, In2 GND 0.850 -> 1.050 (In1 GND 0.551 kept). ACT_DRV, ACT_EN, ACT_EN_MCU, PYRO1_GATE_N: no barrel. S-8 on R17: fails; now: passes |
| 2 | R18-SAF-02 | Done (D-R18-02) | R119 100 k 0402 (C25741, R120's line) at B(11.57,71.1); Q121's gate and source reach it on B.Cu with no via; TP121 B(10.5,71.5) -> B(4,70). New S-3 sub-rule `local_gate_bias` | Q121 same-layer gate-source resistor: none -> R119 (Q120: R120). S-3 on R17: fails; now: passes |
| 3 | R18-MCU-01, R18-SAF-03 | Done (D-R18-01, D-R18-03) | R123 100 k -> 2 k (C4109, same land). ACT_EN_MCU x 26.5 -> 26.62, BAT_FAULT_N x 26.9 -> 27.37, U11.12's GND via (25.8,65.9) removed (it joins C99.2's return). V3V3_SENSE removed (item 10) | Q122 gate with a 30 k PC1 pull-up (3.6 V): 2.748 -> 0.220 V. Q122 gate on: 2.19 V nominal, 1.92 V at the VOH floor (AO3400A VGS(th) max 1.45 V; RDS(on) only specified at 2.5 V, so saturation at <= 0.143 mA load is Inference). ACT_EN_MCU-BAT_FAULT_N 0.171 -> 0.550; -V3V3_SENSE 0.251 -> net removed; -BUZZ_OUT (LS120.2) 0.400 -> 0.520; -USB_LIMITED via 0.550 -> 0.670 |
| 4 | R18-SAF-04 | Done (D-R18-05) | R173 B(23.0,59.2) 90 -> B(16.87,59.7) -90 at the OUT end; the 5.1 k-isolated MID node takes the corridor; IGN diagonal 0.5 mm SW; BUZZ_G lead x 17.5 -> 17.75; C126.2 GND via moved along its stub | OUT-R134.2 0.250 -> 2.825; OUT-Q123.1 0.175 -> 1.577; IGN-R131.1 0.222 -> 0.575. New nearest OUT neighbours: BUZZ_G track 0.510, D120.3 (3V3) 0.514, C126 GND via 0.550 |
| 5 | R18-RTE-01, R18-PWR-01 | Done (D-R18-06) | IN2_GND_CH1 tongue removed; IN2_3V3 shoulder and bay round the USB_LIMITED In2 via ends; IN2_RAW notched. New rule K-plane | 3V3 In2 fill: 3 pieces (1354.23 / 63.11 / 30.54 mm^2) -> 1 piece (1466.52 mm^2). K-plane on R17: 2 issues (0 links >= 0.5 mm each); now: 0 |
| 6 | R18-RTE-04 | Done (D-R18-07) | SD_MOSI B.Cu (20.1,32.8) -> (25.005,27.895) -> (25.005,24.3) | SD_MOSI 36.098 -> 34.104 mm, 12 -> 10 segments |
| 7 | R18-BOM-03, R18-MFG-02 | Done (D-R18-08) | L400: Bourns SRP5030T p1 recommended land, generated by `r10_parts.srp5030t()`. U4 LGA-14: mask expansion 0.025 -> 0 | L400 pads 1.8 x 2.5 at +/-2.35 (gap 2.90) -> 2.0 x 1.8 at +/-2.25 (gap 2.50, outer 6.50); JLC proxy residual 0.15 -> 0.05 mm. U4 mask webs 0.100 -> 0.150; paste unchanged at 88.4 % of the land (TN1383 70-90 %) |
| 8 | R18-BOM-01, R18-REQ-10, R18-MFG-06 | Done (D-R18-09) | R430 -> FOJAN FRC0603F2262TS C2999509 (22.6 k 1 %, 100 ppm/C, 0.1 W, 75 V, 0603; JLC stock 84,923, minimum 1, query 2026-10-30T21:53Z). C84 stays on schematic and board but goes to the owner BOM only (`export_fab.MANUAL_FIT`); S-4 and `jlc_orient --verify-cpl` agree | JLC BOM 82 -> 81 lines; CPL 199 -> 197 rows; owner BOM: C84 (C46550466); paste flashes F 245 / B 373 -> 245 / 371 |
| 9 | R18-REQ-01, R18-REQ-02, R18-SAF-05, R18-MCU-03 | Done (D-R18-10) | mcu and battery_entry note text, ki_fp_filters, pin_table rows 3 (PE4 active-high fire, ODR low, LCKR, reset contract), 16 (R123 2 k) and 18 (PC3_C NC); binding note regenerated | Text only, no copper |
| 10 | R18-REQ-08 | Done (D-R18-01) | VREF+ (U1.20) and VDDA (U1.21) are 3V3A, fed from 3V3 through R164 2.2 ohm, so V3V3_SENSE always read about half scale; R62 / R63 removed, PC3_C NC; VREFINT and VBAT/4 give the information | R62 / R63 fitted -> removed |
| 11 | R18-GATE-02..09, R18-MEC-01, R18-MEC-03 | Not in this pass (brief) | The item-1 S-8 extension and the item-5 K-plane rule are kept | - |

## Residuals and things not done (each measured)

- **MID in the corridor:** PYRO1_CONT_MID-R134.2 0.250 mm and MID-Q123.1 0.175 mm (the 0.625 mm corridor cannot
  hold 0.5 mm to both pads). MID sits behind R173 5.1 k: a RAW_ACT bridge passes <= 1.6 mA (no R134 or e-match
  bypass) and raises the CONT reading to about 1.38 V against 0.75 V intact (a firmware upper bound can flag it:
  Inference); a BUZZ_G bridge puts <= about 4.6 V on PC14 through R162 1 k, within FT VDD + 4 V.
- **Unchanged OUT-GND approaches:** track (15.5,56.6) to GND via (15.85,57.70) 0.177 mm; Q124.5 to GND via
  (12.78,59.02) 0.180 mm (the owner-accepted default-clearance class).
- **Enable chain:** ACT_EN-BAT_ENABLE 0.330 mm at R123.1 (unchanged; a bridge loads U9's 470 k-fed EN with 2 k, so U9
  stays off); ACT_EN_MCU-NRST via 0.425 mm (weak pull-up: <= 0.22 V at ACT_EN); U1.15/U1.17 pitch 0.200 mm.
- **TP121 stub:** TP121 had to leave R119's spot. With its 1.0 mm test-pad clearance and M-6's 1.5 mm from the
  J400 / J1 pads, no nearer legal spot was found beside Q121, J400 / J1 or R120 / C120. At B(4,70) its ACT_GATE B.Cu
  stub is 7.14 mm long at the board's 0.25 mm pour clearance: ACT_GATE B.Cu track 7.24 -> 14.82 mm (F.Cu 5.47 ->
  5.72 mm). The inner-layer barrels are now 1.05 mm from GND; outer copper stays in the default-clearance class.
- **In2:** the 3V3A trunk under U1 (R18-RTE-01 suggestion b) stays on In2; the 3V3 fill is one piece without moving
  it. Island A now joins the plane through fill necks instead of one 0.3 mm B.Cu link: by polygon deflation the
  narrowest neck is about 0.55 mm (island A) and 0.50 mm (the finger); approximate, not a current-capacity analysis.
- **Q122 drive:** AO3400A RDS(on) is not specified below 2.5 V gate; with <= 0.143 mA drain load the 1.92-2.19 V gate is
  Inference, not maker-guaranteed.
- **Not a check.sh suite:** `tools/test_fab_validation.py`
  `test_connector_mechanical_tabs_are_independently_checked` fails on both the R17 and this package: it mutates
  C161692 (R9's GH J9), but R10's J9 is DB125 C2757925. Left for the gate follow-up.
- **For the docs lane:** numbers that change with this board: 136 D IDs (D-R18-01..10 added); JLC BOM 81 lines /
  197 placed / owner BOM C84; R430 C2999509; budget four-stall fire current 1.283013 -> 1.282918 A; P-FET settled
  |VGS| 5.19 -> 4.74 V and time to -4.5 V 23.6 -> 31.9 ms; hidden designators (above).

## Files changed

Generators and inputs: `m3_design/r10_sch.py`, `r10_sch_check.py`, `r10_parts.py`, `r10_pcb.py`, `r10_place.tsv`,
`r10_fanout.tsv`, `r10_route_pyro.py`, `r10_route_signals.py`, `r10_route_power.py`, `r10_route_usb.py`,
`r10_route_sd.py`, `r10_route_ground.py`, `r10_post.py`; `kilib/rocket.pretty/LGA-14_L3.0-W2.5-P0.50-TL.kicad_mod`.
Checks and tests: `tools/check_r10.py`, `m3_design/check_actuators.py`, `tools/export_fab.py`, `tools/jlc_orient.py`,
`tools/jlc_easyeda/pads.json`, `tools/test_r10_check.py`.
Records: `sources/r10_design/circuit.json`, `pin_table.tsv`, `R10_DECISIONS.md` (D-R18-01..10), `AVA_LAYOUT.md`,
`r10_plan.md`; this file and `round18_fix_cad.json`.
Regenerated by the build: `m3.kicad_pcb`; sheets `actuator_power`, `battery_entry`, `camera_connector`,
`camera_power`, `diagnostics`, `mcu`, `telemetry`; `schematic.net.xml`; `kilib/m3.kicad_sym`;
`kilib/rocket.pretty/M3_SRP5030TA.kicad_mod` and `rocket.3dshapes/M3_SRP5030TA.wrl`; `sources/r10_design/`
`hotplug_inputs.json`, `hotplug_results.json`, `parts_budget.json`, `r10_binding_note.json`;
`tools/jlc_corrections.json`; `fab/` (Gerber zip, JLC BOM, CPL, new `m3_bom_owner.csv`, assembly PDFs, manifest,
`cost_check.json`, `stock_check.json`).

## Follow-up (text pass)

This pass was records and text only, after the root committed `acba196`. No build ran, nothing wrote
`m3.kicad_pcb` (SHA-256 `a3144b15…` before and after), there is no git change, and the gate lane's unstaged tools /
`r10_fab.sh` / fab edits were left alone.

- **`pin_table.tsv`:**
  - pin 33 is the bus sense, not an ARM link (ARM1_SENSE is an R9 name);
  - pins 51, 52, 63, 64 and 78 to 81 are respaced, e.g. "R460 (10 kohm) to 3V3", and name their 1 kohm resistor and
    ESD diode;
  - TX pins 52 / 63 idle high only while the ports are powered; on USB-only power they are parked as inputs or low;
  - pin 3 (PE4) wording rechecked, with values and the AON7524 cite;
  - pin 18's cite respaced.
- **Binding note:** regenerated by `r10_sch_check.py --binding-note`. Its DS12110 cites now match the pin table:
  Rev 11 Table 10 pp. 91 / 92 for UART5 / USART6, Table 149 / 150 for PC13 to PC15 (were Rev 10 Tables 11 / 12 / 62 /
  63). The same TX rule is in its start-up obligations. The Rev 11 single "Table 10" was checked against the cached
  Rev 8 page images: there every table after the eleven port tables is exactly ten lower in Rev 11, which is why the
  pin table's numbers were kept (Inference). Only `pin_table_sha256`, two pin modes and the edited texts changed.
- **Checks:**
  - schematic gate: OK, ERC 0, 34 / 34 seeds; sheets and netlist reproduce, so no sheet changed (`r10_sch.py` reads
    only pin / net columns);
  - `check_r10 --only K-binding,K-contract,K-loader`: OK;
  - ERC 0; DRC 0 / unconnected 0 / schematic parity 0 (CLI 10.0.7);
  - binding-note tests: 5 OK.
- **R10_DECISIONS:** a follow-up note under D-R18-10 and the new **D-R18-11** (gate hardening, from
  `round18_fix_gate.md` / `.json`), making 137 unique D IDs.

