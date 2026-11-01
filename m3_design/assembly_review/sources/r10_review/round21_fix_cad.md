# Round 21 fix pass: CAD lane (hand-back)

## Scope

The brief is `.supervisor/r21_fix_brief.md`: eight items from round 21's ten lenses on `0dc84776…` (0 Critical / 0
Major). Items 1-5 change the board or its generators; items 6-8 are checks only (each passed on `0dc84776…` and each
gate-lens seed now fails it).

Changes are in:
- **Generators:** `m3_design/r10_sch.py` (DRU rules, sheet notes), `r10_place.tsv` (R81, C87), `r10_route_power.py`
  (U2.1 run, BAT_ENABLE route), `r10_fanout.tsv` (two GND vias removed), `r10_post.py` (R81's fixed designator spot
  dropped).
- **Checks and tests:** `tools/check_r10.py`, `tools/route_check.py`, `tools/critical_reference.py`,
  `tools/test_r10_check.py`, `tools/test_route_check.py`.
- **Records:** `R10_DECISIONS.md` (D-R21-01..09) and `AVA_LAYOUT.md` (round 21 section, reading guide).
- Everything `m3_design/r10_build.sh` regenerates (board, DRU, sheets, fab package, binding note, hot-plug evidence).

Not touched: no native CAD hand-edited; `kilib/rocket.pretty` unchanged; STATUS.md, AGENTS.md, docs/*.md and
parts_qualification.md unchanged by this lane (the docs lane's edits in the tree are its own); no git state changed;
AGENTS section 2 unchanged.

Machine-readable twin: `round21_fix_cad.json`.

## New board

PCB `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1`, 46 x 90 x 1.6 mm.

| Board | Bytes | Footprints | Segments | Vias (GND) | Track |
|---|---|---|---|---|---|
| Round 20 `0dc84776…` | 2,340,154 | 215 | 985 | 302 (169) | 1874.854252 mm |
| Round 21 `5516eeec…` | 2,336,572 | 215 | 983 | 300 (167) | 1871.611826 mm |

- **Parts moved:** two. R81 F(20.5,65) -> F(18.8482,80.0) 0; C87 F(17,65) -> F(18.7232,81.8768) 0.
- **Copper:** added the U2.1 B.Cu run (24.05,68.95) -> (23.0,70.0); BAT_ENABLE's B.Cu hop re-bent and its F.Cu run
  re-drawn through R81.1 / C87.1; removed R81's and C87's switch-end stubs and the GND vias (20.706,65.619),
  (16.639,63.939).
- **Rules:** three DRU rules added (`JLC_HOLE_RULES`); the fills were refilled under them (J1.2, J400.2 and J3's
  shell holes now 0.550 mm from inner copper).
- **Unchanged:** every other pose, land, net and support, the rule areas, U1's pin map and the IMU axis map (K-binding
  OK).

## Builds and gate

**Two complete `r10_build.sh` builds** (KiCad CLI 10.0.7, `NUMPY_PY=.supervisor/venv/bin/python`):
- Both exit 0 and end in `tools/check.sh` exit 0, with PCB `5516eeec…` in both (build 1: 1321 s; build 2: 1322 s).
- Snapshot compare: 921 files: 916 identical; 5 differ: the four date-stamped fab outputs (both assembly PDFs, the
  Gerber zip, the manifest; as in round 20, contents not re-diffed) and `tools/test_r10_check.py`, edited between the
  builds (the notes test no longer prints, so check.sh's summary shows the R10 test count). None is in only one build.
- Before them, scratch builds (through the ground family, then r10_post, on a project copy) with DRC, fit, check_r10
  and route_check on each, for the DRU condition trials (item 1), the U2.1 candidates (item 2), the BAT_ENABLE hop
  (item 4) and two C87 spots (item 5: pad 1 at y 81.55 left a 0.327 mm run piece inside C87.1 and an off-centre pad
  end; on the run's last bend at y 81.8768 neither).

**check.sh (both builds):**
- DRC 0 / unconnected 0 / schematic parity 0 / ERC 0.
- Metadata / 3D audit, silkscreen outline (0 points), `r10_parts --check` and fit (eight wire rooms 5.00-5.60 mm) OK.
- **check_r10: 36 / 36 rules OK** (K-ports is new).
- route_check r10: 0 failing (22 bump windows; 6 unrecorded noncritical leftovers, round 20's 7 less the BAT_ENABLE
  jog, which is now critical and fixed). Information instances 148 -> 148: + 3V3 `pad_end_offcentre` (U2.1) and
  `power_via_no_gnd` (R89's via), - BAT_ENABLE `extra_bends` and `tiny_jog`.
- Fab content checks (S-4 BOM / CPL, CPL rebuilt from JLC footprints, paste) and the six-output manifest pass.
- Self-tests: shell 10, procurement OK, fab_validation 34, fit 33, paste 16, r10_parts 5, route 69, **R10
  247** (6 NumPy skips), NumPy `HotplugNumerics Plate` 6: all OK.

**Fab package (`r10_fab.sh`):**
- BOM 81 lines, unchanged; 205 placed parts. CPL 69 top / 122 bottom rebuilt plus 14 placement-only; only the R81 and
  C87 rows changed. Paste F 253 / B 375 flashes. Owner BOM: C84.
- Manifest bound to `5516eeec…`. Cost and stock were not re-run (same parts and quantities).

**Hot-plug:** inputs re-extracted (C87 moved); 2304 cases, 0 failures, qualification pass; extremes identical to round
20 (-14.8074 V, 2.0 V, 8.9915 / 5.0907 V/us).

**Binding note:** regenerated for `5516eeec…`; K-binding OK (pin map and IMU axis unchanged). The native fire budget
(`parts_budget.json`) changed only its board hash.

## Items

**1. Inner-layer PTH pad hole to copper (R21-PWR-02 / -BOM-01 / -MFG-01 / -GATE-02, D-R21-01): done, 0.55 mm.**
- **JLC's table, checked on the page** (https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-31): "Inner
  layer via hole to copper clearance 0.2mm"; "Inner layer PTH pad hole to copper clearance 0.3mm"; "PTH to Track
  0.28mm" (0.35 mm recommended); "Pad Hole-to-Hole Spacing 0.45mm". The brief's four figures match.
- **Rules** (`r10_sch.py` `JLC_HOLE_RULES`, into `m3.kicad_dru`): inner-layer PTH pad hole to copper 0.55 mm,
  outer-layer PTH hole to track 0.28 mm, pad hole to hole 0.45 mm. Vias keep the general 0.25 mm (JLC 0.2).
- **Why 0.55 mm.** The largest of 0.55 / 0.35 / 0.3, and every plane and reference rule holds at it: DRC 0, K-plane's
  landing necks unchanged (least 0.549 mm), K-reference and K-region OK, every inner power fill still one piece. It is
  what the other plated pads already had, J3's four shell holes (0.451 mm) excepted.
- **Plane strips it narrows** (measured on the fills, before -> after, mm): J1.1-J1.2 (In2 RAW_PROTECTED) and
  J400.1-J400.2 (In1 GND) along the pin line 1.40 -> 1.10; J3.1 / J3.4 to the VBUS via voids (8.0,33.7) / (7.95,27.9)
  (In2 3V3, least gap) 0.633 / 0.599 -> 0.566 / 0.537; J3.2 / J3.3 slot to the west edge (In2 3V3) 0.479 -> 0.379.
  The J3 strips run in parallel with the slot-to-slot strips (1.729 -> 1.529), and the fill pieces match `0dc84776…`
  (3V3, PORT_4V8, PORT_5V3, RAW_PROTECTED one piece each on In2): nothing splits.
- **Condition.** `A.Type == 'Pad' && A.Pad_Type == 'Through-hole' && (B.Type != 'Pad' || B.Pad_Type ==
  'Through-hole')`. Trials: an A-only condition failed DRC (J3's NPTH locating holes are 0.535 mm from its shell pads'
  rings, 0.835 mm hole wall to slot wall); the probe's `B.Pad_Type` clause alone is false for zones and tracks, so the
  fills stayed at 0.251 mm with DRC 0.
- **Gate (K-rules).** `JLC_HOLE_TABLE` pins the four figures by named DRU rule (layer, condition, minimum at least
  JLC's), rejects a later rule that could override one and any hole rule under 0.2 mm; `pth_inner_copper` measures
  every plated pad hole wall on the board against 0.3 mm whatever the DRU says. `DRU_SHA256` 5acf6db7… -> 1d2dbe77….
- **Hole wall to the nearest foreign copper, every plated pad (mm; bold = changed):**

| Pad (net) | In1: before -> after (nearest) | In2: before -> after (nearest) |
|---|---|---|
| J1.1 (BAT_IN) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (RAW_PROTECTED) |
| J1.2 (GND) | 1.901 -> 1.901 (J1.1 barrel) | **0.251 -> 0.550 (RAW_PROTECTED)** |
| J121.1 (PYRO1_OUT) | 1.050 -> 1.050 (GND) | 1.050 -> 1.050 (GND) |
| J121.2 (PYRO1_IGN) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (GND) |
| J122.1 (SERVO1_OUT) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (RAW_PROTECTED) |
| J122.2 (SERVO2_OUT) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (RAW_PROTECTED) |
| J122.3 (SERVO3_OUT) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (RAW_PROTECTED) |
| J122.4 (SERVO4_OUT) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (RAW_PROTECTED) |
| J122.5 (GND) | 1.901 -> 1.901 (J122.4 barrel) | 0.550 -> 0.550 (RAW_PROTECTED) |
| J3.1 (GND) | 1.375 -> 1.375 (VBUS) | **0.451 -> 0.550 (3V3)** |
| J3.2 (GND) | 5.203 -> 5.203 (VBUS) | **0.451 -> 0.550 (3V3)** |
| J3.3 (GND) | 5.154 -> 5.154 (VBUS) | **0.451 -> 0.550 (3V3)** |
| J3.4 (GND) | 1.345 -> 1.345 (VBUS) | **0.451 -> 0.550 (3V3)** |
| J400.1 (BAT_SW_SOURCE) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (GND) |
| J400.2 (BAT_SW_RETURN) | **0.251 -> 0.550 (GND)** | 1.050 -> 1.050 (GND) |
| J410.1 (PORT_4V8) | 0.550 -> 0.550 (GND) | 1.751 -> 1.751 (PORT_5V3) |
| J410.2 (GND) | 1.901 -> 1.901 (J410.1 barrel) | 0.550 -> 0.550 (PORT_4V8) |
| J410.3 (GPS_TX_WIRE) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (PORT_4V8) |
| J410.4 (GPS_RX_WIRE) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (PORT_4V8) |
| J420.1 (PORT_4V8) | 0.550 -> 0.550 (GND) | 0.900 -> 0.900 (3V3) |
| J420.2 (GND) | 1.901 -> 1.901 (J420.1 barrel) | 0.550 -> 0.550 (PORT_4V8) |
| J420.3 (RADIO_TX_WIRE) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (PORT_4V8) |
| J420.4 (RADIO_RX_WIRE) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (PORT_4V8) |
| J440.1 (PORT_4V8) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (3V3) |
| J440.2 (GND) | 1.901 -> 1.901 (J440.1 barrel) | 0.550 -> 0.550 (3V3) |
| J440.3 (AUX_TX_WIRE) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (3V3) |
| J440.4 (AUX_RX_WIRE) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (3V3) |
| J9.1 (CAM_5V) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (3V3) |
| J9.2 (GND) | 1.513 -> 1.513 (CAM_IO_3V3) | 0.550 -> 0.550 (3V3) |
| J9.3 (CAM_RX_WIRE) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (3V3) |
| J9.4 (CAM_TX_WIRE) | 0.550 -> 0.550 (GND) | 0.550 -> 0.550 (3V3) |

  J3.1 / J3.4 on In1 (re-measured for R22-PARTS): slot wall to the VBUS via barrels. Those vias keep pads only on
  F.Cu / B.Cu, so In1 holds only their 0.3 mm barrels; counting a 0.6 mm pad there gives 1.225 / 1.194 mm.

**2. Regulator sense / OV / EN / ILIM taps (R21-PWR-01 / R21-GATE-01, D-R21-02): done.**
- **U2.1.** The f01b 0.4 mm B.Cu 3V3 run (24.05,68.95) -> (23.0,70.0) into R89's via: U2.1's single point via
  (23.20,68.60) -> none. Chosen by M2: the in-line via (22.55,68.6) sits 0.886 mm (In2) / 0.986 mm (In1) from the
  BAT_ENABLE barrel (21.3,68.9), under S-8's 1.0 mm. route_check counts two INFO items from it (not gated): the run
  starts 0.35 mm off U2.1's pad centre (`pad_end_offcentre`), and R89's via (23.0,70.0) is now a two-layer 3V3 via
  whose nearest GND via is 2.182 mm away (`power_via_no_gnd`).
- **Gate.** `SINGLE_OPEN_TAPS` 1 -> 26 taps (the gate lens's survey, same nets / taps / sources), with
  `('3V3', 'U2.1', ('L1.2',))` and `('USB_LIMITED', 'R87.1', ('U10.6',))`. `single_via_opens` tests only the vias on
  one tap-to-source path (any via every path needs lies on it): 26 taps in about 10 s.
- **Exact `SINGLE_OPEN_EXCEPTIONS` (8), stale when no longer met:**
  - U401.3 / via PORT_LDO_FB (29.75,13.60): no legal second via spot; open, FB is held only by its +/-100 nA leakage
    (TI SBVS282A p5) and PORT_4V8 is undefined up to dropout (Inference). Respin: R402 / R403 beside U401 on B.Cu.
  - R87.1 / vias USB_LIMITED (22.00,62.25) and (16.00,28.00): no clean second path. R87.1 (22.0,63.1) is boxed on B.Cu
    by RAW_ACT (x 22.8 from y 61.4 to 63.875, then west along y 63.875) and PYRO1_CONT_MID (north); a second In2 via
    would close a parallel-via loop and still leave U10's end on one via. Open, the USB over-voltage cut-off is lost
    (USB is bench power only).
  - R85.1 / via USB_ILIM (14.82,26.00), R85.2 / via GND (9.00,27.84), R430.2 / via GND (32.30,59.50): TI SLVS841G
    section 8.5.1 p16: "The current-limit threshold is proportional to the current sourced out of ILIM", so an open
    leg lowers the limit (fail-safe); TI does not state the open-pin case (Inference). The p7 R_ILIM table agrees
    (larger R_ILIM, lower limit).
  - R81.1 and C87.1 / via BAT_ENABLE (17.10,82.80): item 5.

**3. Schematic notes (R21-REQ-01 / -02, D-R21-03): done** (`r10_sch.py` `R21_SHEET_NOTES`, text only).
- sensors: the fitted ISM6HG256X (DS15034 Rev 1 p1; FS_XL_HG Table 150 p93: use 001 / 010, as D-R19-11; pins 10 / 11
  open, Table 25 p52), the LSM6DSV320X the consigned alternate. Was the LSM6DSV320X, +/-32..320 g.
- diagnostics: a battery-powered self-test checks the camera supply (U400, U402); on USB-only power PORT_5V3 and
  CAM_5V are off. Was a USB self-test of "U8".
- battery_entry: no battery-lead fuse (OQ-6, 2026-10-28). Limited only by the pack and lead: the lead, J1, BAT_IN
  copper, D8, C80 / C96, C88 (100 nF) and C89 / C95. U9 (TPS259470L) limits and latches off RAW_PROTECTED. Q120's
  drain is on BAT_IN, so the RAW_ACT fire path bypasses U9 and R134 (2 Ohm) limits it. Was "must be fused".

**4. Arming nets in route_check (R21-REQ-04, D-R21-04): done.**
- BAT_SW_SOURCE, BAT_SW_RETURN and BAT_ENABLE are in the pyro / arming class and on the AUD-2 slow list (filtered
  DC nodes, tau about 50 ms: exempt only from the 1.5 mm partner via and the one-In2-region rule).
- **Jog removed.** B.Cu (19.675,66.6) -> (21,67.925) -> (21,68.6) -> (21.3,68.9) (0.424 mm jog, 0.3 mm offset) ->
  (19.675,66.6) -> (20.7,67.625) -> (20.7,68.3) -> (21.3,68.9). TP120 keeps its 1.0 mm and R88.2 its clearance (a
  straight (19.675,67.275) entry missed TP120's 1.0 mm by 0.011 mm). D-R19-02's via and the S-8 keep-outs unchanged.
- **Why exempt (R22-REQUIREMENTS-01):** physics, not lack of room: 470 kOhm feeds (R80, R165), tau about 50 ms, about
  7 uA. The project's spot search finds a legal 0.5 mm GND via 0.671 mm from (10.8,69.2), (21.3,68.9) and
  (19.675,66.6), none for (17.1,82.8).
- **Exposed by the reclassification** (on `0dc84776…`): the tiny jog (gated; fixed); extra_bends on the F.Cu run
  (counted; gone with the re-drawn run); short_layer_hop 2.973 mm (counted; the B.Cu hop under the F.Cu RAW_ACT /
  ACT corridor, stays). Removing R81's stub then left the F.Cu corner (19.675,66.0) -> (19.675,66.6) a removable local
  bump (gated); the run now turns on a 45 degree piece from (19.075,66.0). BAT_SW_SOURCE / BAT_SW_RETURN: none.

**5. R81 at U9's end of the EN run (R21-SAF-01, D-R21-05): done, with C87.**
- **Placement.** R81 F(18.8482,80.0) 0, pad 1 on the F.Cu EN run (x 18.0232); C87 F(18.7232,81.8768) 0, pad 1 on
  the run's last bend. Pads 2 in the F.Cu GND piece of U9.8's via (20.2,81.0). Removed: R81's stub (19.675,66.0)-
  (19.675,65.0), C87's tap, both GND stubs and the GND vias (20.706,65.619), (16.639,63.939).
- **Measured (lens figure in brackets where given):**

| | Before | After |
|---|---|---|
| Series vias U9.1 -> R81.1 / C87.1 | 3 / 3 | 1 / 1, (17.10,82.80) |
| Track U9.1 -> R81.1 / C87.1 | 20.920 / 24.295 mm | 3.890 [3.889] / 2.013 mm |
| R81.1 (EN) to GND via (17.2,79.9) | - | 0.173 mm [0.173] |
| R81.2 (GND) to RAW_PROTECTED via (20.3,79.1) | - | 0.307 mm [0.232] |
| C87.1 (EN) / C87.2 (GND) nearest foreign copper | - | GND fill 0.251 / BAT_FAULT_N track 0.254 mm |
| Least RAW_ACT to GND pad / track / via gap (fills keep 0.25 mm) | 0.196 mm (R134.2 to via (20.706,65.619)) | 0.300 mm (B.Cu RAW_ACT (22.8,61.4)-(22.8,63.875) to U11.6; 0.302 in the first text was a 2 um step artefact, R22-SAFETY-01) |

  The lens's 0.232 mm treats R81.2 as a sharp rectangle; KiCad's pad shape has a rounded corner there, which gives
  0.307 mm (shape collision stepped at 1 um). The EN-to-GND and GND-to-RAW_PROTECTED shorts fail safe (U9 off; U9's
  limit); GND to BAT_FAULT_N reads as a U9 fault.
- **EN absolute maximum.** TI SLVSFC9C section 6.1 p7: EN/UVLO -0.3 to 6.5 V (recommended at most 5 V, section 6.3).
  With R81 alone moved, an open between C87 (switch end) and R81 with J400 closed could charge C87 toward BAT_IN
  (8.4 V) and dump it into EN on reclosure (Inference); beside R81, C87 stays at the divider's 2.03 V nominal
  (<= 2.06 V with 1 % parts at 8.4 V; Calculation) while R81 is intact (corrected for R22-DOCS_BINDING-04).
- **Kept:** D-R19-02's via, the S-8 keep-outs and the D-R19-10 values; D-R20-11's timing (same node).
- **Residual:** EN still crosses the via (17.10,82.80) to U9.1 on B.Cu (exact exceptions; respin: U9's west cell).

**6. Panel-tab keep-outs (R21-GATE-03, D-R21-06): done (check).** K-plane pins `R20_TAB_KEEPOUT_WEST_AFT` (In2,
(-0.5,12.5)-(3.0,17.5), fill-only) and holds the non-GND inner copper under the four tab bands: west aft 0, west
forward 0, east aft In2 RAW_PROTECTED 7.497 + PORT_5V3 3.077, east forward In2 RAW_PROTECTED 12.244 mm^2 (re-measured
on `5516eeec…`, unchanged). Growth over 0.005 mm^2 fails; a smaller figure fails as stale. Seed d07: fails (3V3 12.498
mm^2, keep-out missing).

**7. Port ESD clamp placement (R21-GATE-04, D-R21-07): done (check).** New rule K-ports: pin centre to clamp pad
centre along the net's track graph, with the 1 k resistor's pads removed, at most 4.5 mm. Measured: J410 4.288 /
4.388, J420 3.975 / 3.975, J440 4.075 / 4.175 (3.157 / 3.194 pad edge to edge), J9 3.975 / 3.975 mm. Seed d08: fails
at 6.975 mm; a clamp re-fed from R471's far side fails as reached only through R471.

**8. Fab references (R21-GATE-05, D-R21-08): done (check).** `fab_ref_crossings` also requires one visible
`${REFERENCE}` on the footprint's own Fab layer (LS120's "+" / "-" allowlisted), at least 0.3 mm high, its ink box
crossing no other footprint's Fab outline or reference and its ink centre inside no other footprint's Fab outline box.
The board: 215 references, none crossing, least height 0.3 mm. Seeds d06a / d06b / d06d / d06e fail; d06c is not
representable in KiCad 10.

## Tests

- **Added (test_r10_check.py):** RealBoardSeeds test_r21_jlc_hole_table_pinned_in_k_rules,
  test_r21_pth_holes_clear_inner_copper (the 0.25 mm refill seed), test_r21_regulator_taps_survive_one_via_open,
  test_r21_en_pull_down_and_filter_at_u9, test_r21_tab_keepout_and_bands_held (d07),
  test_r21_port_clamps_beside_their_pins (d08), test_r21_fab_references_present_readable_and_apart (d06a / b / d / e);
  SchematicContract test_r21_sheet_notes.
- **Added (test_route_check.py):** R10AuditScope test_r21_arming_chain_is_critical_slow_and_its_old_jog_fails.
- **Changed:** none of the existing tests. Removal seeds use `RealBoardSeeds.drop` (a removed footprint text sets
  `thisown = False` too), and each seed asserts its own finding, so a seed that did not apply fails.
- **Before the builds** the full R10 suite ran on a trial copy (247 tests, 863 s): its only failures were the copy's
  missing binding note, fab package and hot-plug evidence, and the new item 5 test's C87 position, then updated to the
  last-bend spot. In both builds: R10 247 (6 NumPy skips), route 69, all OK.

## Renders

**Checked:** `.supervisor/r10_renders/r10_top.png` and `r10_bottom.png` (r10_fab.sh, 984 x 1960), plus zoom-4 top
and zoom-5 bottom views (kicad-cli 10.0.7 render) of the U9 corner and of U2 / L1.

**Seen:**
- **Top.** R81 and C87 sit on the EN run west of C84, with R81's designator vertical east of it and C87's below it;
  C80, C89 and D8 read beside their parts. C126, D123, Q122 and R122's designators (shown again or moved) read beside
  their parts in the switch / ACT cell. The old R81 / C87 spots by R165 are empty. No silkscreen sits over a pad, a via
  or the edge.
- **Bottom.** U2, L1, C5 and the C120 / Q120 / Q121 area read as before; no silkscreen over a pad or via. The B.Cu
  runs under the mask (the U2.1 run, the BAT_ENABLE hop) are too faint to judge in the render; their geometry is held
  by DRC, route_check and the single-via check.

## Residuals

- R81.1 / C87.1 still cross one via, (17.10,82.80), to U9.1 (respin: U9's west cell, D-R20-01).
- U401.3's FB tap on one via (respin: R402 / R403 beside U401).
- R87.1 on two single vias (bench-only USB OV cut-off).
- The TPS2553 ILIM legs on single vias (fail-safe; Inference for the open-pin case).
- The east panel tabs stay over In2 RAW_PROTECTED / PORT_5V3 (owner's tab plan, D-R20-08), now held by K-plane.
- route_check counted (not gated): U2.1's run starts 0.35 mm off the pad centre (pad_end_offcentre); R89's via
  (23.0,70.0), now a two-layer 3V3 via, has its nearest GND via 2.182 mm away (power_via_no_gnd); BAT_ENABLE's
  short_layer_hop; 6 unrecorded noncritical leftovers.
- The 0.55 mm refill narrows four plane strips at the west-edge terminals (item 1); none splits a fill.

## Not done

Nothing in items 1-8 is left undone. Item 2's R87.1 second path was not added: no clean local one (measured above).

## For the docs lane

- Board `5516eeec…`: 983 segments, 300 vias (167 GND), 1871.611826 mm; 93 designators hidden.
- ORDERING 8.1 VIPPO paragraph via count (R21-MFG-02): 300 vias on this board = 295 at 0.5 / 0.3, 4 at 0.6 / 0.3,
  1 at 1.0 / 0.5 mm (round 20: 302 = 297 / 4 / 1).
- R21-SAF-01: the handoff's "not fixable on this board" now reads: R81 / C87 moved to U9's end (one via left).
- J1.2 / J400.2 are 0.550 mm from inner copper again (JLC 0.3); J3's shell holes 0.550 (was 0.451).
- K-ports, the JLC hole table, the tab-band figures and the Fab reference rule are new gate content.

## Follow-up: pre-commit circuit check Minors (same board)

The pre-commit circuit check returned PASS with six Minors; this lane fixed its five, none a copper change:
1. The U2.1 run is 0.4 mm (`W`), not 0.3 mm: corrected in D-R21-02, AVA_LAYOUT and this hand-back.
2. The battery_entry note (`r10_sch.py`) now names C88 (100 nF, BAT_IN to GND) among the parts limited only by the
   pack and lead, and Q120: its drain is on BAT_IN, so the RAW_ACT fire path bypasses U9 and R134 (2 Ohm) limits it.
3. R89's via (23.0,70.0) INFO `power_via_no_gnd` (2.182 mm) recorded in D-R21-02 and the residuals.
4. The four plane strips the 0.55 mm refill narrows, measured on the fills (they match the check's figures), recorded
   in D-R21-01 and item 1.
5. Wording: 0.55 mm was not every pad's prior clearance (J3.1-J3.4 were 0.451); the `r10_sch.py` comment now gives the
   J3 NPTH holes as 0.535 mm from the shell pads' rings (0.835 mm hole wall to slot wall), both measured.

One more complete `r10_build.sh` (1321 s): exit 0, PCB `5516eeec…` again, `r10_fab.sh` re-bound (the battery_entry
sheet changed), check.sh exit 0 (DRC 0 / 0 / 0 / ERC 0, check_r10 36 / 36, route_check 0 failing, R10 247 tests).
The supplier reports `cost_check.json` / `stock_check.json` were refreshed at 2026-10-31T23:23Z by another lane, not
by this build; they are left as found.
