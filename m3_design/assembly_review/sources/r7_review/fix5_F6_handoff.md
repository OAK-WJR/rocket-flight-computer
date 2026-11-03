# R7 fix pass 5, agent F6 (board, tools): handoff

Worktree branch `m3-assy-r7`, uncommitted, on R6 commit `3b215ba`. Start: the fix-pass-4 board, SHA-256
`c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7`. Nothing committed, pushed or opened as a PR. I did
not edit `docs/*.md`, `STATUS.md`, `AGENTS.md`, the schematic, `m3.kicad_dru`, `check_actuators.py` or `check_r7.py`.
Running log: `fix5_F6_progress.md`. Scratch evidence: `<scratchpad>/fx5/` (`base.kicad_pcb` = start board,
`final.kicad_pcb` = final board, `an/` analyses, `c/` clearance probes, `probe.py`, `dev.sh`, `gate.sh`, `an5.sh`).

**Final board SHA-256 `1ffc2585cbbb2a49623a5010b2792500849f06989cf43e48fb3e56068cddf9df`.** `m3_design/r7_build.sh`,
run unmodified from the SHA-checked R6 board, produced exactly this file and exited 0 (its `tools/check.sh` passed);
build log `fx5/build4.log` (14 min 55 s). The post-hygiene board it builds on is byte-identical to F5's
(`dfca97c4…`): every change is in `r7_polish.py` and `r7_post.py`. (A first full run aborted after `r7_hygiene`
because I edited the script's comments while bash was reading it; it was rerun untouched.)

Fab package regenerated (`tools/export_fab.py`, `tools/fab_manifest.py`: "Fab manifest: OK; 5 outputs match"); BOM and
CPL byte-identical (no part moved), so `stock_check.json` / `cost_check.json` still bind (`check_procurement.py
--cost-only`: OK, $105.98 per board; the full check still fails on U4 stock, as before). `jlc_orient.py --verify-cpl`:
92 + 119 rows, worst 0.491 mm, no errors. Renders `r7_top.png` / `r7_bottom.png` regenerated (984 × 2184:
`kicad-cli pcb render --side top|bottom -w 1016 -h 2208 --quality high`).

## 1. What changed on the board (all in `m3_design/r7_polish.py` / `r7_post.py`)

`r7_polish` stages (new or changed in bold), each with its measured reason in its docstring:

| Stage | Change |
|---|---|
| **pyro1_cont** | PYRO1_CONT F.Cu run drawn S / SE / S (35.78, 65.25) → (40.88, 70.35) → (40.88, 74.75) instead of S/SE/S/SE (P5-RQ-02); same length 47.53 mm, 6 vias, same GND return vias, gap to PYRO1_GATE_N still 1.080 mm (asserted) |
| **band5** | RADIO_BUSY / RADIO_MISO_MCU east chamfers 1.004 mm (allowlist A1, A2 gone); MISO_MCU's and RADIO_MOSI's fan-in steps 0.35–0.4 mm later (lanes keep 0.25 mm) |
| **qspi5** | RADIO_RXEN on its via column x 23.8 (D12 gone); QSPI_CLK step 0.36 mm (A5 gone) |
| **jogs5** | CAM_EN W/S/SW (B1 gone); CAM_FAULT_N straight at y 103.938 and down x 15.19 with a square stub to its via (B2, D6 staircase gone); SERVO4_MCU straight down x 15.505 (RQ-04 step gone); LOGIC_ILIM S/SW/SE (RQ-04 step gone); CAM_RX_WIRE one In2 run x 44.251, R100 branch square, layer change moved to the run end (D13 and its across-via step gone); **CAM_TX_WIRE off In1** (D16): RX leaves J9.3 on F.Cu to a via (43.75, 42.625) and goes down In2, TX runs straight east on F.Cu to one via (45.1408, 43.875) — 2 vias → 1, no In1 copper on the board; GND stitching via (43.7, 43.5) → (42.2, 43.25); LOGIC_SOURCE_ST and PULLPIN_EXT steps across their vias gone; CAM_5V_SENSE's 2.9 mm F.Cu hop gone (2 vias fewer; its In2 runs in a 3V3_In2 void, fill checked); LED_RED's B.Cu hop moved to F.Cu (one via fewer) |
| **tidy5** | D1 ACT_GATE square T (acute wedge gone); D2 GND C94.2 run redrawn (staircase + T-jog gone); D3 CAM_5V R78.1 → via in two segments (jog through the via and the redundant 0.425 mm piece gone); D4 3V3_RADIO straight through FB31.2 into C310.1; D7 RAW_ACT tail ends 0.5 mm inside its fill (was 3.19 mm); D9 three jack-leg GND vias 20 µm aft (ring overlaps gone); D10 USB_LIMITED corner + square branch; D11 VLOGIC runs end at U2.2 / U2.3 centres |
| **arm_gnd** | GND vias 0.5 mm at (13.95, 93.75), (13.95, 97.15), 0.721 mm from ARM1_SENSE's layer changes (A17, A18 gone; P5-RG-03): the nearest spots that pass GndFit's rules, inside the J1 → Q120 corridor that `gnd_vias` avoids by policy; cost measured below (+0.03 mΩ) |
| **band_end** | `R7_GND_In2_strip` also covers x 6.9–9.9, y 25.0–31.3; BAT_IN vias (7.6, 26.6), (8.8, 26.6) removed (P5-RQ-01: the 7 band-end split crossings gone, 12.1 mm of radio B.Cu no longer over In2 BAT_IN) |
| pour_trim | 23 rule areas (was 21): new GND finger between moved RXEN and QSPI_IO2 (24.0–24.4, 36.0–40.0) as the review predicted, and a 0.26 mm 3V3_In2 sliver beside SERVO4_MCU (15.0–15.2, 67.0–70.2, −0.12 mm² of 3V3 fill) |
| **edge_stitch** | D15: 12 GND vias (0.5 mm) so every F.Cu / B.Cu GND point at y ≥ 112 is within 4 mm of copper of a via (the RF strip's rule), except 621 raster points (≈ 1.6 mm²) of B.Cu at (18–20.5, 112.0), worst 4.75 mm, where every spot lies in the J1 → Q120 corridor (GndFit policy) |
| **gnd_pieces** | P5-REGRESSION-02: second GND vias (41.375, 70.625) F.Cu piece by J2, (35.85, 53.275) B.Cu east of U1, (27.4, 76.4) B.Cu by U4, (34.05, 57.025) F.Cu by CAM_UART_OE |
| (all via placements) | new `npth_ok`: via copper ≥ 0.27 mm from non-plated holes (ViaCheck tests hole-to-hole only; an edge via first hit TH3's 0.25 mm copper-to-hole rule in DRC); stitching and second vias use the full `r7_hygiene.GndFit` test |

`r7_post`: every visible designator must pass the courtyard test (ink polygon to courtyard polygon, the pass-4/5
reviewers' measure) or is placed again with `courtyard_designator`, else hidden; the run fails if one is left. D17:
C301, D120, R155, R172, R80, R83, TP84 found no passing spot and are hidden (R88 too, but it was already hidden on
the start board); U13 is now visible. Hidden designators 84 → 90; full list: C100 C126 C128 C129 C13 C14 C15 C150
C151 C160 C25 C30 C301 C302 C303 C305 C31 C311 C312 C313 C314 C60 C7 C71 C74 C8 C88 C90 C92 C94 D120 D123 D30 D31 FB31
J123 L30 LED1 Q32 R10 R101 R102 R103 R104 R105 R11 R12 R125 R128 R129 R130 R133 R155 R157 R161 R162 R163 R164 R172 R173
R178 R180 R301 R302 R303 R304 R311 R312 R316 R32 R63 R64 R74 R75 R8 R80 R83 R86 R88 R91 TP71 TP74 TP81 TP83 TP84 TP88
TP90 U11 U7 Y1.

Totals: tracks 1809 → 1777, vias 694 → 706 (+18 GND: 2 ARM, 12 edge, 4 pieces; −6 signal/BAT_IN), In1 signal copper
3 tracks / 3.67 mm → 0.

## 2. Per finding

| Finding | Done? | What changed, or why not |
|---|---|---|
| **P5-ROUTING_GEOMETRY-01** / P5-RQ-05 (A1, A2, A5) | **Yes** | band5 + qspi5 (reviewers' edits, re-probed). Allowlist entries A1, A2, A5 deleted. Measured: BUSY chamfer 0.25 mm to MISO_MCU, 0.176 mm to GND via (20.0, 27.45); QSPI_CLK 0.24 mm to RXEN's via, 0.325 mm to LED_YEL; RXEN 0.329 mm to GND via (23.92, 30.8). A3/A4 (the 0.2 / 0.3 mm row-offset fan-in steps) stay, re-measured by the new gated `alt_audit` (no clean redraw) |
| **P5-ROUTING_GEOMETRY-02** (B1, B2, B8–B11, D13, NRST) | **Yes** | B1, B2, D13 removed (jogs5). B8 CAM_5V_SENSE: its F.Cu hop and 2 vias removed (extra_vias entry gone; detour re-reasoned with the measured U1.35 box-in: the only legal via spots within 1 mm of U1.35 lie beyond RAW_ACT_SENSE_MCU's diagonal). B9 gone. B10 LED_RED: hop moved to F.Cu, 3 → 2 vias (entry gone). B11 SERVO2_MCU: re-reasoned with measured blockers (B.Cu run at y 58.6 collides with C13.2's GND tie; In2 hop crosses SPI1_SCK). NRST 46.11 mm (now gate-checked) |
| **P5-ROUTING_GEOMETRY-03** (ARM1_SENSE) | **Yes** | arm_gnd. BAT_IN J1 → Q120 4.55 → 4.58 mΩ (the two vias alone: 4.55 without, 4.58 with, same board); In2 peak 6.17 A/mm unchanged |
| **P5-ROUTING_GEOMETRY-04** (route_check soundness) | **Yes** | §3 below: every allowlist / leftover reason category is now re-measured by a gated check (no-GND: `nognd_audit`; jog / staircase / short segment: `alt_audit`; detour / extra_vias: `measured_check`); jogs and staircases through T / via / pad nodes, every acute pair, partial pour stubs, pad layer changes and same-net via overlaps detected; LEFTOVER_CATS = every hygiene category. 9 new tests |
| **P5-ROUTING_QUALITY-01** (band-end crossings) | **Yes** | band_end. BAT_IN J1 → U9.5 15.14 → 15.18 mΩ (whole board, incl. the ARM vias) |
| **P5-ROUTING_QUALITY-02** (PYRO1_CONT) | **Yes** (1); records (2) | S/SE/S run. Close approaches of the PYRO1_CONT copper stand as the review listed (0.175 CAM_UART_OE, 0.191 SWCLK, 0.195 NRST, 0.193 R129.1, 0.212 3V3A, 0.220 R168.1–SWCLK, 0.225 R75.1); new: GND via (41.375, 70.625) 0.171 mm from its x 40.88 run (a short reads "no continuity": fail-safe) |
| **P5-ROUTING_QUALITY-03** (NRST records) | Records only | No copper change; for the docs agent: the x 36.3 In2 run (10.35 mm) has no B.Cu fill above, 3V3A's B.Cu track over ≈ 6.4–7.2 mm, no PYRO1_CONT above |
| **P5-ROUTING_QUALITY-04** (three lengthened steps) | **2 of 3 removed**, 1 forced | LOGIC_ILIM (S/SW/SE) and SERVO4_MCU (straight) have no jog now. I2C1_SCL's 0.36 mm step is forced (measured): straight down the pin column x 25.35 it collides with BOOT0's via (25.05, 62.85) and the GND via (24.97, 64.4); a BOOT0 via anywhere between IMU_CS (x 24.35) and that column needs 1.095 mm of a 1.0 mm channel; the only BOOT0 via spot that would also straighten BOOT0 (x 24.94) puts its In1 antipad under IMU_CS for 0.5 mm (51 reference samples) — tried and reverted. It is not a route_check instance (not tiny), so it is recorded here and in `r7_polish.jogs5`'s docstring. QSPI_CLK's new step (0.509 mm / 0.36 mm, the reviewers' fix) is of the same kind: forced by QSPI_IO3's via and RXEN's via |
| **P5-REGRESSION-01 / -04** | Records only | for the docs agent (no copper concerned) |
| **P5-REGRESSION-02** | **Yes** | gnd_pieces (4 second vias). Single-via GND pieces on F/B 40 → 35 (the other 35 inherited, each holds one via) |
| **P5-REGRESSION-03** | Records; no nudge | the GND via (28.55, 87.21) stays: 5 legal spots within 1.45 mm of PYRO1_CONT's via (28.4, 88.61), none ≥ 0.25 mm from R129.1 / R178.1 (measured). Close neighbours of all new copper: §5 |
| **P5-DOCS-01 (b)** (part D) | **Yes** except D5, D8, D14 kept | D1, D2, D3, D4, D6, D7, D9, D10, D11, D12, D13, D15, D16, D17 removed or fixed; D18 (tool blind spots S1–S5) closed in route_check. D8 (PYRO1_GATE into TP122) is now a gated instance with an allowlist entry and a measured reason (any GND via within 1.5 mm comes within 0.45 mm of the bare test pad, rule 1.0 mm; `nognd_audit` re-checks). D5 (GND (31.3, 53.7) → (31.5, 53.5)) and D14 (RADIO_NRST's 0.141 mm step) lie wholly inside a via's copper: route_check counts no jog there (the via is the joint), as for PULLPIN_EXT's new step |
| **P5-DOCS-01 (c), (d)** | Tool side done | (c) every hygiene category on a non-critical net must now be recorded; information-only counts for the list: §4. (d) LEFTOVERS' search wording now states the search's stricter rule (every power pour blocked) and that "no route" holds under it only |
| P5-DOCS-02 / -03 / -04 | Not mine (records) | DC numbers for the IPC note: §6 |

## 3. `tools/route_check.py` (and tests)

New categories / detections (all gated as before: rule categories on every net, hygiene on critical nets, non-critical
hygiene instances need a LEFTOVERS entry):
- `tiny_jog` through T / via / pad nodes (`at='T'|'via'|'pad'`, across a via onto another layer too); a side branch off
  a straight run (via fan-out, rung) and a middle segment wholly inside one pad or via are not jogs.
- `staircase` followed through T / via / pad nodes on one layer (`at='node'`).
- `acute_angle`: every branch pair at a node is tested (S1).
- `pour_stub` (rule): a pour-only track end whose run lies > 1.0 mm inside its own fill (S3).
- `critical_via_no_gnd`: a via into a same-net pad counts as a layer change (S4; `into_pad`).
- `via_overlap` (hygiene): same-net via rings overlapping (S5).
- `LEFTOVER_CATS` = all 15 hygiene categories (P5-RG-04 (c)).

Reason audits (gated, P5-RG-04 (a), (b)):
- `measured_check`: every detour / extra_vias entry (allowlist or LEFTOVERS) is tied to `ROUTE_FIGURES[net] = (len_mm,
  vias)`; the gate fails when the route differs by > 0.05 mm or one via.
- `alt_audit`: for every allowed or recorded tiny_jog / staircase / short_segment, all 1–3 segment octilinear redraws of
  its window (its segments plus one plain-joined neighbour each side; bends on a 0.025 mm grid) are tested against
  `r7_hygiene.Clearance`, track keep-outs and the board edge (0.3 mm), and must not themselves make an acute turn, short
  segment, tiny jog or staircase with the branches at either end, nor be longer than 1.1 × the window + 0.2 mm (power
  rails: no longer than the window). A clean one fails the gate ("removable"). Pads and vias stay put; a 4+ segment
  redraw is not searched (both stated in the docstring). This audit found the PULLPIN_EXT step removable (applied), and
  SW_NODE redraws 11–13 % longer than the present switch-node copper (kept: power-rail slack; the `_SW` reason now
  quotes them).
- Search results quoted in detour / extra_vias reasons (F5's raster runs) are not re-run in the gate; the entries say
  which board they were run on.

Tests: `tools/test_route_check.py` 41 OK (32 → 41: node jog + fan-out exemption, node staircase, every acute pair,
pour stub, pad layer change, via overlap, measured figures, `path_defects`, `alt_audit` free vs blocked). Entries are
read as `e[:5]` (tuples may carry a sixth `measured` dict in tests).

## 4. Counts — before / after

`route_check` (all (critical) / failing / allowlisted / leftovers):

| | Start board, F5's tool | Start board, final tool | **Final board** |
|---|---|---|---|
| total | 323 / 0 / 37 / 34 | 342 / 14 failing + 5 unrecorded / 37 / 34 | **312 / 0 / 33 / 30** |
| staircase | 2 (2) | 6 (4) | **0** |
| tiny_jog | 6 (4) | 15 (8) | **3 (3)** (A3, A4, A6) |
| short_segment | 2 (2) | 2 (2) | 2 (2) (A7, A8) |
| critical_via_no_gnd | 10 | 11 (+TP122) | **9** (8 radio + TP122) |
| acute_angle / pour_stub / via_overlap | – | 1 / 1 / 3 | **0 / 0 / 0** |
| detour / extra_vias | 22 (9) / 29 (10) | same | 22 (9) / 27 (10) |
| info: pad_end_offcentre / width_change_junction / segment_inside_pad / passes_through_pad / extra_bends / u_turn / short_layer_hop / power_via_no_gnd | 93 / 30 / 3 / 10 / 34 / 25 / 21 / 36 | same | 93 / 31 / 3 / 10 / 32 / 25 / 20 / 35 |

Information-only instances on non-critical nets (for the deviation list, P5-DOCS-01 (c)): 69 — pad_end_offcentre 29,
extra_bends 20, short_layer_hop 11, u_turn 7, width_change_junction 1, segment_inside_pad 1. On critical nets: 180 —
pad_end_offcentre 64, power_via_no_gnd 35, width_change_junction 30, u_turn 18, extra_bends 12, passes_through_pad 10,
short_layer_hop 9, segment_inside_pad 2.

Pass-2 `scan.py` (unchanged, `rg/scan.py`), all (critical): **958 (595) → 945 (591)** — staircase 2 → 0, tiny_jog
2 (1) → 0, critical_via_no_gnd 10 → 8, extra_bends 34 → 32, short_layer_hop 21 → 20, chain_detour 62 → 61, dogleg
148 → 147, acute_at_padvia 11 → 10, off_angle_rounding 26 → 25, pad_end_offcentre 208 → 205; up: right_angle_corner
55 → 57, width_change_free 17 → 18, pad_entry_diagonal 173 (111) → 173 (112).

Pass-5 independent `scan5.py` (`p5rg/`), all (critical): **545 → 501** — jog_tiny 11 (8) → 4 (4) (BUSY, MISO_MCU fan-in;
SW_NODE; the GND step inside via (31.5, 53.5)), staircase_any 7 (4) → 0, acute wedge exposed 1 → 0, redundant track
copper 1 → 0, via ring overlap 3 → 0, tiny jog across a via 6 (1) → 1 (0) (BOOT0, kept: above), critical layer change
without GND via 11 → 9.

## 5. Final allowlist (33) and leftovers (30)

Allowlist (`route_check.ALLOWLIST`, every reason measured, re-checked as stated):
- tiny_jog RADIO_BUSY (9.4, 28.2), RADIO_MISO_MCU (10.0, 28.7): 0.2 / 0.3 mm row-offset fan-in steps (a 45° step of
  < 0.354 mm offset is tiny at any length; the step cannot sit before the 10.0 column: BUSY at y 28.0 overlaps
  RADIO_NRST's via by 0.025 mm) — `alt_audit`.
- tiny_jog + 2 short_segment SW_NODE: the C7.2 / C9.2 gap needs a straight piece; two-bend redraws exist but lengthen
  the switching node 3.23 → 3.58 mm and 2.77 → 3.12 mm (+11–13 %) — `alt_audit` (power slack).
- critical_via_no_gnd ×8 radio (RXEN (23.8, 39.45) 2.23 mm; NRST (9.3, 50.0) 3.18; BUSY (9.4, 28.2) 1.65, (10.0, 49.5)
  2.60; MOSI (9.4, 29.2) 1.65; DIO1 (10.0, 50.5) 3.57; MISO_MCU (10.0, 28.7) 2.11; MOSI_MCU (9.4, 48.5) 1.71) and
  PYRO1_GATE into TP122 (20.45, 92.4) 2.93 mm — `nognd_audit` finds no legal spot (gate log: 0 out-of-date).
- detour / extra_vias (figures gated): GNSS_RESET_N 59.34 / 2, RADIO_DIO1 69.09 / 4, RADIO_NRST 85.44 / 4, RADIO_NSS
  58.4 / 4, RADIO_RXEN 51.88 / 4, RADIO_TXEN 25.17 / 2, GNSS_LNA_EN 7.45 / 1, GNSS_VCC_RF 6.2 / 1, PYRO1_CONT 53.33 / 6
  (net copper; rerouted chain 47.53), ARM1_SENSE 63.73 / 4, QSPI_IO2 33.26 / 3, VCAP1 6.71 / 2, VCAP2 12.67 / 1, VBUS
  42.49 / 6, RAW_PROTECTED 143.53 / 7, VLOGIC 66.97 / 5 (+0.1 mm: D11).

Leftovers (`route_check.LEFTOVERS`, 13 detour + 17 extra_vias, figures gated): BAT_FAULT_N 39.97 / 4 (d, e),
BAT_SW_RETURN 160.34 / 5 (d, e), BAT_SW_SOURCE 129.2 / 7 (e), BUZZ_OUT 22.55 / 1 (d), CAM_5V_SENSE 36.75 / 2 (d; was
36.91 / 4), CAM_EN 6.95 / 1 (d), CAM_FAULT_N 95.62 / 5 (d, e), CAM_MCU_RX 32.81 / 6 (e; its F.Cu hop crosses a
3V3_In2 fill bridge, measured), CAM_MCU_TX 65.87 / 5 (d, e), CAM_PWR_EN 81.9 / 8 (d, e), CAM_UART_OE 30.68 / 4 (e),
LED_YEL 36.26 / 3 (e), LOGIC_SOURCE_ST 58.31 / 11 (e; its F.Cu hop crosses a 3V3_In2 fill bridge, measured), NRST
46.11 / 4 (e), RAW_ACT_SENSE 38.93 / 2 (d), SERVO1_MCU 65.32 / 5 (e), SERVO2_MCU 76.72 / 9 (e; measured blockers),
SERVO2_OUT 37.07 / 1 (d), SERVO4_MCU 96.38 / 3 (d), SERVO4_OUT 46.92 / 3 (d, e), SWCLK 62.7 / 4 (d, e), SWDIO 53.72 /
4 (e), VBUS_SENSE 43.13 / 4 (e). Gone: B1, B2 (tiny jogs), B9 (CAM_5V_SENSE vias), B10 (LED_RED).

Close neighbours of every new or moved track / via (fix pass 5 copper, edge gap < 0.2 mm, all ≥ the 0.15 mm rule;
`fx5/c/newgap.py`): SERVO4_MCU – CAM_FAULT_N In2 0.162–0.166 (parallel runs and CAM_FAULT_N's via); CAM_FAULT_N –
CAM_PWR_EN via 0.165; band lanes 0.168–0.176 (MISO_MCU / MOSI steps, BUSY – GND via (20.0, 27.45)); GND via
(41.375, 70.625) – PYRO1_CONT 0.171; GND vias (13.95, 93.75) / (13.95, 97.15) – ARM1_SENSE vias 0.172 (a short reads
disarmed: on the ground a refusal, in flight only logged — fail-safe); CAM_5V_SENSE – GND via (31.5, 37.8) 0.175;
PULLPIN_EXT – C60.2 0.176; GND via (27.4, 76.4) – SERVO1_MCU 0.176; GND via (35.85, 53.275) – 3V3A 0.176; CAM_RX_WIRE
– BAT_SW_SOURCE via 0.184; GND via (42.2, 43.25) – BAT_SW_SOURCE In2 0.185; CAM_5V_SENSE – CAM_MCU_RX via 0.191;
CAM_TX_WIRE – R101.1 0.191; LOGIC_ILIM – 3V3 via 0.194; USB_LIMITED – BAT_SW_RETURN via 0.194; CAM_FAULT_N – SERVO4_MCU
0.195. Fix pass 4's (P5-REGRESSION-03 (a)–(d)) stand unchanged.

## 6. Electrical evidence (final board against the start board)

- **Connectivity:** pad groups with pours identical for all 191 nets, no track-only split or merge, KiCad unconnected 0
  (`an/final_groups.txt`). **CH1 pyro copper** (PYRO1_BUS / IGN / OUT): 0.00000 mm² lost or gained on every layer
  (`an/final_pyro_xor.txt`). Pyro sentinel pins untouched, `m3.kicad_dru` untouched, `check_actuators` OK.
- **Critical reference** (`tools/critical_reference.py`): against the start board **0 lost** (R6 method and extended).
  Against R6 (+18 mm): lost **603 → 603**, candidate-new **861 → 882** (+21 QSPI_CLK F.Cu at (23.31, 39.35–39.55): the
  0.36 mm step's lane edge passes RADIO_RXEN's via In1 antipad for 0.2 mm — accepted as the price of A5); extended
  2,312 → 2,312 lost, 4,304 → 4,325 candidate-new (the same 21).
- **Pours:** BAT_IN In2 770.8 → 760.3 mm² (band end, ARM antipads; one piece), GND In2 +12.5, GND B.Cu +12.1, GND F.Cu
  −2.2 (43 pieces), GND In1 +7.3, 3V3_In2 −0.12 (5 pieces; the trimmed sliver); every GND piece holds a via.
- **DC** (`tools/dc_solve.py`, board stack-up, 0.1 mm grid, mΩ, start → final):

  | Path | Start | Final |
  |---|---:|---:|
  | RAW_ACT Q121:5–9 → J122:2,5,8,11 (7.7 A) | 3.95 | **3.95** (F.Cu 100 %, peak 5.75 A/mm unchanged: the D7 tail lay inside its fill) |
  | BAT_IN J1:1 → Q120:5–9 (7.7 A) | 4.55 | **4.58** (+0.7 %, the two ARM1_SENSE GND vias: 4.55 without them on the same board; 35.2 mV, 0.271 W; In2 peak 6.17 A/mm unchanged) |
  | ACT_FET_S Q120:1–3 → Q121:1–3 (7.7 A) | 1.36 | 1.36 |
  | BAT_IN J1:1 → U9:5 (1 A) | 15.14 | **15.18** (+0.3 %: band end and ARM vias; peak 2.71 A/mm unchanged) |
  | 3V3 L1:2 → U1:75 / FB31:1 / FB30:1 / U1:27 / U3:8 / C9:1 | 15.64 / 14.66 / 5.53 / 6.85 / 6.76 / 2.48 | unchanged |
  | 3V3 L1:2 → U1:100 / U1:6 | 78.23 / 78.05 | unchanged |
  | 3V3_RADIO FB31:2 → C310:1 | 1.27 | 1.27 |
  | RAW_PROTECTED U9:6 → U11:2 / U7:3,4 / TP81:1 | 35.23 / 153.45 / 144.52 | unchanged |
  | VLOGIC C84:1 → U2:2,3 | 36.39 | 36.39 |
  | USB_LIMITED U10:6 → U11:7 | 72.37 | **72.32** (D10) |
  | CAM_5V L3:2 → J9:1 | 27.79 | 27.79 |

  (`an/dc_base.txt`, `an/dc_final.txt`, `an/dc_batin_t5*.txt`.) No high-current path's peak current density moved;
  the IPC-2152 note (P5-DOCS-02) is unaffected.

## 7. Gate and tests (final board)

```
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
silkscreen outside the board outline (46.00 x 118.00 mm): 0 stroke points
R7 CAD contract: OK
routing hygiene: 0 failing, 33 allowlisted, 0 stale allowlist entries, 0 out-of-date no-GND reasons, 30 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0 removable jog / staircase / short-segment exceptions: OK
actuator safety contract: OK
  nearest bottom/pin envelope: C76, 4.150 mm from support (42.0, 114.4) (minimum 3.5 mm)
  nearest top hardware clearance: TP30.1 exposed top pad, 5.008 mm from support (4.0, 4.0) (minimum 3.8 mm)
fit check: OK (CAD envelopes only)
```
(`tools/check.sh` exit 0, run by `r7_build.sh`.) Tests (KiCad Python): check_shell 2, dc_solve 3, fab_validation 23,
fit_check 23, maze_clearances 10, procurement 15, r6_check 17, r7_check 34, route_check 41 — 168 OK; quality_audit 21 OK
under KiCad Python and python3; test_r5_repair 1 error, the known `routing_lands_spacing`.

## 8. For the records (docs agent / next pass)

- R7_VALIDATION deviation list: part A 37 → 33 (A1, A2, A5, A17, A18 gone; PYRO1_GATE/TP122 added); part B 34 → 30
  (B1, B2, B9, B10 gone; B8 / B11 / B16 / B23 re-reasoned; NRST 46.11); part C: C5 band-end half gone (U1 end stays),
  C10 / NRST wording (P5-RQ-03, P5-REG-01), C11 forward strip now stitched; part D: only D5 / D14 (steps inside a via,
  not counted) and the forced non-tiny steps (I2C1_SCL, QSPI_CLK, CAM_RX_WIRE's 0.5 mm In2 offset past BAT_SW_RETURN's
  run) remain, plus BOOT0's via beside its line (measured reason above).
- M3_R7: build description (new stages, `npth_ok`, courtyard test), board SHA, 90 hidden designators (list above), 23
  pour trims (F.Cu 9 / B.Cu 13 / In2 1), route_check's new checks, In1 carries no signal copper, DC table §6.
- REQUIREMENTS M2 "what the gate enforces": add the node jogs / staircases, every acute pair, pour stubs, pad layer
  changes, via overlaps, `measured_check`, `alt_audit`, LEFTOVERS for every hygiene category.
- Not done here: owner acceptance; IPC-2152 note (P5-DOCS-02); MARGIN 85 °C row (P5-DOCS-03); the sheet-15 notes; the
  BOM comment; a review pass on board `1ffc2585…`.

## 9. Files changed by F6

`m3_design/r7_polish.py`, `m3_design/r7_post.py`, `m3_design/r7_build.sh` (comments only), `tools/route_check.py`,
`tools/test_route_check.py`; `m3_design/assembly_review/m3.kicad_pcb`; `fab/m3_gerber.zip`,
`m3_assembly_{top,bottom}.pdf`, `m3_fab_manifest.json` (BOM / CPL rewritten byte-identical); `r7_top.png`,
`r7_bottom.png`; this file and `fix5_F6_progress.md`.
