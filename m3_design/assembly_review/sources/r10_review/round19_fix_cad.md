# Round 19 fix pass: CAD lane (hand-back)

Scope: the brief `.supervisor/r19_fix_cad_brief.md` (13 board-changing Minors from round 19's 0 Critical / 0 Major
review of `a3144b15…`), the coordinator's additions to items 6 and 8 (one word list, the top-render legend check), and
item 14, the owner-approved spare AUX port (`.supervisor/r19_aux_port_brief.md`, D-R19-14). Items 1-13 were finished
and checked first (build 7, PCB `f33587f2…`, check.sh exit 0); item 14 then went into the same pass. Changes are in the
generators (`m3_design/r10_*.py`, `r10_place.tsv`, `r10_fanout.tsv`), the generated footprint library (`r10_parts.py`),
the design sources (`circuit.json`, `pin_table.tsv`, `masses.json`), the checks (`tools/check_r10.py`,
`tools/route_check.py`, `tools/critical_reference.py`, `tools/plate_model.py`, `tools/fit_check.py`,
`m3_design/check_actuators.py`), the JLC data (`tools/jlc_easyeda/pads.json`, `tools/verified_part_metadata.json`) and
their tests, the records (`R10_DECISIONS.md` D-R19-01..14, `AVA_LAYOUT.md`, `r10_plan.md`) and everything
`m3_design/r10_build.sh` regenerates. No native CAD was hand-edited. STATUS.md, AGENTS.md, docs/*.md and
parts_qualification.md were not touched; no git state was changed; AGENTS section 2 is unchanged. The round 19 review
reports stay untracked where they were. Machine-readable twin: `round19_fix_cad.json`.

## New board

PCB `50a39de5b76dec3cb58bbb1b0ab528fd4d65098de9dfe8f89f49e2e7adcbd976`, 46 x 90 x 1.6 mm, 2,336,742 bytes;
215 footprints, 984 segments, 301 vias (169 GND), 1870.487095 mm track.
Round 18 `a3144b15…`: 2,250,842 bytes; 208 footprints, 947 segments, 292 vias (166 GND), 1788.737627 mm track.

- Footprints: TP121 removed; C123 added at F(18.22,71.85); the AUX port J440 F(7.4,16.25) and its top cell C444, C445,
  D440, D441, R470, R471 added (D-R19-14); R90 B(7.8,23.1) -> B(11.275,23.0) and TP82 B(10.8,21.3) -> B(11.0,17.6) for
  M-6 beside J440.4. U4 is now ISM6HG256X and C87 220 nF, on their unchanged lands and poses. Every other pose, land and
  support is unchanged; the IMU axis map (roll = -gyro_Y, lever arm x = -6.0 mm) is unchanged (K-binding OK).
- U1's pin map changes only at pins 55 / 56 (J410 GPS_TX / RX_MCU, USART3 PD8 / PD9) and 63 / 64 (J440 AUX_TX / RX_MCU,
  USART6 PC6 / PC7): the GPS's former UART goes to the AUX port, whose pins face the north-west corner (D-R19-14).
- Vias added: VLOGIC (29.8,81.15); PORT_5V3 (42.75,61.8), (26.45,11.95), (24.9,14.9); PORT_4V8 (29.75,9.95) and, for
  the AUX feed, (30.5,9.95); the AUX cell's GND returns. Moved: BAT_ENABLE (19.675,66.4) -> (19.675,66.6); C23.2's
  fan-out GND (27.1,34.2) -> (25.95,34.15); R90's 3V3 (6.2,23.1) -> (9.6,23.0); stitches (2.0,9.0) -> (0.9,9.0) and
  (16.5,12.5) -> (17.5,12.0); (7.0,22.0) removed. Tracks removed: TP121's 7.14 mm ACT_GATE stub and the old GPS
  diagonals from U1.63 / U1.64.
- Rule areas: two more fill-only `R18_BARREL_KEEPOUT_PYRO1_OUT_*` (In1 and In2), eight in all.
- U1.19 has no pour connection (board pad override; library unchanged).
- Silkscreen: RADIO, BAT, IGN and AUX at reviewed word spots; fourteen terminal pin legends at reviewed spots, 2:E1+,
  2:SW and J440's 4:RXI on the bottom (D-R19-08 / -14); nine designators at fixed spots (D-R19-12); D8, C404, C408, LED2,
  C400, C401, R90, R462 and R463 moved by the search; R88, C123, C28, R110, D440 and D441 hidden (88 -> 94, all kept on
  F.Fab).

## Builds and gate

- **Two complete `m3_design/r10_build.sh` builds (9 and 10)**, KiCad CLI 10.0.7, `NUMPY_PY=.supervisor/venv/bin/python`:
  both exit 0, each ending in `tools/check.sh` exit 0, PCB `50a39de5…` in both. Snapshot compare of the two builds: 922 files identical, 4 differ only by their date stamps (m3_assembly_top.pdf, m3_assembly_bottom.pdf, m3_gerber.zip, m3_fab_manifest.json), none only in one.
  Earlier builds: 1 stopped at the record step (a sheet note corrected while it ran); 2 failed six S-3 synthetic tests
  (fixture without C123; fixed, test added); 3-4 (`3370552d…`), 5-6 (`814f1504…`) and 7 (`f33587f2…`, items 1-13 only)
  were complete, exit 0, and superseded by the render-driven legend layout, J122's designator and item 14; build 8 made
  the final PCB but its check.sh stopped on two self-tests that still expected seven DB125 terminals and the old GPS
  segment (updated). The final PCB equals build 8's.
- **Per-family stage gates:** core / usb / pyro / power / signals / ground all OK (no route_check failure outside the
  pending nets; after ground: DRC 0, unconnected 0, route_check 0).
- **check.sh:** DRC 0 / unconnected 0 / schematic parity 0 / ERC 0; metadata and 3D-model audit OK; `r10_parts --check`
  OK; fit OK (eight wire rooms); **check_r10 full contract 35 rules OK**; route_check r10 0 failing (22 bump windows; 7
  unrecorded noncritical leftovers, was 6); fab content checks and manifest OK (6 outputs). Self-tests: shell 10,
  procurement 20, fab_validation 34, fit 33, paste 16, r10_parts 5, **route 68**, **R10 212** (5 native NumPy skips)
  and NumPy `HotplugNumerics Plate` 5: all OK.
- **Fab package (`r10_fab.sh`):** orientation CHECK none; 81 JLC BOM lines, 205 placed (CPL 71 top / 120 bottom rebuilt
  from JLC footprints plus 14 placement-only checks, worst pad residual 0.491 mm); owner BOM C84 (C46550466); S-4 OK;
  paste F 257 / B 371 flashes on as many pasted pads; manifest bound to `50a39de5…`.
- **Supplier refresh** (`tools/jlc_stock.py`, `tools/jlc_cost.py --profile r10`, `check_procurement --cost-only`, live
  2026-10-31, inputs = this BOM / CPL): 82 codes (46 extended / 36 basic incl. the owner line), none short, U4 thin
  (9 for 5); **$85.35 per board against $84.41: M3 not met** (item 14 adds $1.14; PRELIMINARY, not a release pass).
- **Binding note:** regenerated from the finished board (`board_sha256` 50a39de5…, IMU bottom 180, roll -gyro_Y, lever
  x -6.0 mm, U1 pins 55 / 56 / 63 / 64 per the new map); K-binding OK.
- **Hot-plug model:** inputs re-extracted (C444 / C445 in the retained-output inventory), 2304 required cases pass.

## Per item (brief numbering)

| # | Finding | Status | Change | Before -> after (measured, edge to edge, native pcbnew 10.0.7 shapes) |
|---|---|---|---|---|
| 1 | R19-SAF-01, -05 | Done (D-R19-01) | `BARREL_KEEPOUT['PYRO1_OUT'] = (In1, In2)`: fill-only 16-gons r 1.20 mm (OUT via) / 1.70 mm (J121.1); `BARREL_GND_HAZARD` += PYRO1_OUT; K-reference / K-region skip a hazard net's own samples inside its own S-8 void (drill/2 + 1.071 mm) | OUT via wall to In1 / In2 GND 0.251 -> 1.021 (the nearest is OUT's own GND partner via ring, centres 1.42 mm); J121.1 wall to In1 / In2 GND 0.551 -> 1.050, its inner ring to GND 0.251 -> 0.750. 0.5 mm opening: In1 GND and In2 GND_CH1 stay one piece; only corner cusps <= 0.04 mm^2 near the voids (no new neck < 0.5 mm). Every S-8 barrel: table below |
| 2 | R19-SAF-02 | Done (D-R19-02); U9 EN-IN recorded | via (19.675,66.4) -> (19.675,66.6); B.Cu (19.675,66.6)-(21.0,67.925)-(21.0,68.6)-(21.3,68.9) | to R134.2 (RAW_ACT) 0.300 -> 0.500; In2 RAW 1.050 (kept), In2 GND 0.994 -> 1.123; F.Cu nearest non-GND 1.556 (ACT_EN_MCU). U9.1-U9.5 0.200 (TI RPW land pitch) and via (17.1,82.8)-BAT_FAULT_N 0.200 unchanged |
| 3 | R19-SAF-03, R19-RTE-02 | Done (D-R19-03) | TP121 and its 7.14 mm B.Cu stub removed; probe at R119.1 / R120.2 | ACT_GATE outer copper within 0.30 mm of GND 12.896 -> 7.996 mm; ACT_GATE-BAT_SW_SOURCE 0.400 -> 0.470 |
| 4 | R19-SAF-06 | Done (D-R19-04) | C123 10 nF X7R 0402 C15195 at F(18.22,71.85): ACT_EN 1.1 mm from Q122.1, GND to R123.2's via | gate tau 7.1 us (on 7.6 us, off 8.6 us, reset 26 us) vs ms-scale load switch and the 100 ms D-SS-04 wait; fire budget untouched; R122.2-C123 GND run 0.436, C123.1-GND fill 0.251 (fail-safe) |
| 5 | R19-RTE-01 | Done (D-R19-05) | U1.19 `ZONE_CONNECTION_NONE` (board pad override in r10_pcb; library unchanged) | 1.693 mm^2 via-less F.Cu GND fragment -> none; DRC library mismatch 0 |
| 6 | R19-MFG-01, R19-GATE-06 + coordinator | Done (D-R19-06) | RADIO / BAT / IGN at WORD_SPOTS; one WORD_LEGENDS_R10 list; WORD_SEAMS empty; GPS / RADIO y-span rule | RADIO centre 2.130 own / 2.051 J410 -> 2.051 / 5.767 (inside J420 by 4.825); GPS 1.361 / 14.539 (inside J410 by 0.95); BAT 1.256 / 1.275 -> 0.555 / 0.635, SWITCH 0.575 / 0.615 (both stay in their gaps, ink margins 0.060 / 0.040) |
| 7 | R19-MFG-02, R19-BOM-02 | Done (D-R19-07) | `M3_MA_8x10` (generated, only C84) drops F.Paste; S-4 fails paste on a MANUAL_FIT part | paste F 245 / B 371 (C84's 2 gone, C123's 2 added); no board override |
| 8 | R19-MEC-01, R19-MFG-04 + coordinator render check | Done (D-R19-08, -12) | twelve PIN_SPOTS: 2:E1+ / 2:SW to the bottom, 1:BAT+ to the board-edge strip, 1:E1- under IGN, 1:S1 along J122's south end, the east wire-side legends east of the envelopes in two columns; J121 / J400 / J122 designators at fixed spots | every top pin and word legend wholly outside every DB125 VRML envelope (worst 0.133 mm; round 18: 1:BAT+ -0.70, 1:E1- -0.72, 1:S1 -0.92, 1:5V4 -0.94, east column -0.07); no line mixes two terminals; J122's designator 0.910 mm under its envelope -> clear (round 18: 0.772 under) |
| 9 | R19-PWR-01, R19-GATE-04 / -05 | Done for 5 feeds (D-R19-09); 3 recorded | second vias VLOGIC (29.8,81.15), PORT_5V3 (42.75,61.8) / (26.45,11.95) / (24.9,14.9), PORT_4V8 (29.75,9.95); K-power +7 paths; route_check `PARALLEL_VIAS` (VLOGIC) | nearest non-GND copper: 1.44 / 2.83 / 1.275 / 0.783 / 0.70 mm; In2 joined: n/a / yes / yes / yes / yes. Not doubled: U11.2 RAW (no spot keeps 0.5 mm from ACT_EN_MCU), 3V3A west and east |
| 10 | R19-REQ-02 | Done (D-R19-10) | C87 C23630 2.2 uF -> C21120 220 nF 25 V X7R, same land | turn-on 0.31-1.22 s -> 31-122 ms; chatter immunity 116-275 ms -> 12-27 ms worst (>= 10 ms F6 proposal); hot-plug 2304 cases unchanged |
| 11 | R19-BOM-01 | Done (D-R19-11) | U4 ISM6HG256XTR C51931514 fitted; LSM6DSV320X the consigned alternate | same land / pins / axes (DS15034 Fig. 5 p9, Table 2 pp10-11, p187); CPL rotation 0 -> 180 (EasyEDA BR footprint, residual 0.040 mm); stock 9 >= 5; cost below |
| 12 | R19-MCU-03 | Done (D-R19-13) | camera_uart / mcu notes, check_actuators comment | PE9 OE; PE3 / PE5 / PE6 / PC4 analog, never driven |
| 13 | R19-MCU-01 / -02 / -04 | Done (D-R19-13) | pin_table rows 28 / 52 / 63 / 98 and 82 re-cites; binding note re-cites, PA4-low TX rule, obligation 14, VREFBUF, IMU codes | regenerated by the record step; K-binding OK |
| 14 | Owner: spare AUX port (`r19_aux_port_brief.md`) | Done (D-R19-14) | J440 F(7.4,16.25) -90 + top cell (no new codes); J410 to USART3 PD8 / PD9, J440 on USART6 PC6 / PC7; F.Cu feed through two In2 vias; R90 / TP82 moved for M-6; 100 mA AUX allowance | wire room 5.003 mm (floor 4.95); washer 3.93 mm (>= 3.8); U401 junction at 70 C 114.7 -> 123.9 C (floor 125); cost $84.21 -> $85.35 vs $84.41 (over, owner decision) |

## S-8 barrels (R19-SAF-05)

Barrel wall to the nearest foreign In1 / In2 copper (GND listed separately; S-8 counts GND only for ACT_GATE,
ACT_DRV and, new, PYRO1_OUT). Vias keep no inner pad on layers they do not join, so only the plated terminal holes
have an inner ring; their ring-to-foreign column is the ring's own edge.

| Barrel | In1 GND | In1 other | In2 GND | In2 other | Inner ring to foreign |
|---|---|---|---|---|---|
| PYRO1_OUT via (11.630, 55.100) | **1.021** (was 0.251) | 2.925 3V3 | **1.021** (was 0.251) | 2.699 3V3 | no inner pad |
| PYRO1_OUT J121.1 hole | **1.050** (was 0.551) | 1.320 3V3 | **1.050** (was 0.551) | 1.061 3V3 (was 1.103) | **0.750** GND (was 0.251) |
| PYRO1_IGN J121.2 hole | 0.551 | 1.900 PYRO1_OUT | 0.551 | 1.900 PYRO1_OUT | 0.251 GND |
| PYRO1_GATE via (14.400, 53.300) | 0.251 | - | 0.251 | 2.100 USB_LIMITED | no inner pad |
| ACT_GATE via (16.200, 73.300) | 1.050 | - | 1.407 | 1.050 RAW_PROTECTED | no inner pad |
| ACT_GATE via (11.140, 71.700) | 1.050 | 2.223 BAT_SW_SOURCE | - | 1.050 RAW_PROTECTED | no inner pad |
| BAT_ENABLE via (19.675, 66.600) (moved) | 0.251 | - | 1.123 (was 0.994) | 1.050 RAW_PROTECTED | no inner pad |
| BAT_ENABLE via (21.300, 68.900) | 0.251 | 1.624 3V3 | 1.566 | 1.050 3V3 | no inner pad |
| BAT_ENABLE via (17.100, 82.800) | 0.251 | 1.678 BAT_FAULT_N | 2.602 | 1.050 RAW_PROTECTED | no inner pad |
| BAT_SW_RETURN J400.2 hole | 0.551 | 1.900 BAT_SW_SOURCE | 1.050 | 1.050 RAW_PROTECTED | In1 0.251 / In2 0.750 GND |

The PYRO1_OUT via's 1.021 mm is its own GND partner via's inner ring at (10.3, 55.6), 1.42 mm centre to centre (the
1.5 mm partner rule holds). A 0.5 mm opening of the In1 GND and In2 GND_CH1 fills leaves each one piece; near the
new voids it removes only corner cusps of 0.011-0.038 mm^2, so no new inner neck is below 0.5 mm.

## Word legends (item 6 and the coordinator's additions)

Centre of each word's ink box to its own and to the nearest other connector's courtyard box (mm, on the word's face),
the ink-gap margin (`check_r10.word_legends`) and how far the ink lies inside the own courtyard's y-span:

| Word | Own | Centre to own | Centre to nearest other | Ink-gap margin | Inside own y-span |
|---|---|---|---|---|---|
| RADIO | J420 | 2.130 -> **2.051** | 2.051 J410 -> **5.767** J410 | 0.000 -> **4.815** | -1.150 -> **4.825** |
| GPS | J410 | 1.361 | 14.539 J420 | 13.900 | 0.950 (unchanged, >= 0.5) |
| BAT | J1 | 1.256 -> 0.555 | 1.275 J400 -> 0.635 J400 | 0.040 -> 0.060 | heads J1 (J400 / J1 gap) |
| SWITCH | J400 | 0.575 | 0.615 J121 | 0.040 | heads J400 (J121 / J400 gap) |
| IGN | J121 | 1.240 -> 2.194 | 8.965 J2 -> 7.460 J2 | 8.390 -> 5.380 | heads J121, one line north |
| SWD | J2 | 1.278 | 4.131 J3 | 3.155 | 0.890 |
| SERVO | J122 | 2.337 | 6.101 J9 | 5.090 | heads J122 |
| CAM | J9 | 1.361 | 4.811 J420 | 4.040 | 4.050 |
| AUX (new, D-R19-14) | J440 | 1.631 | 16.096 J3 | 14.885 | 1.895 |

One list: `check_r10.WORD_LEGENDS_R10` now holds all nine words (AUX added before SWITCH, which stays last, where r10_post placed it);
`WORD_SUBJECTS_R10` and r10_post's own `('J400', 'SWITCH')` are gone and `WORD_SEAMS` is empty. r10_post places the same
words in the same order and its final self-check now runs `check_r10.word_legends`; the list change alone moved
nothing (checked on the first scratch build). Deliberate moves: RADIO into J420's span; IGN one line north; BAT 0.55 mm
east inside its gap. BAT and SWITCH keep the round 18 thin identity margin: each fills the 1.19 mm gap at its
terminal's north end, where the coordinator wants it to stay; a clear-margin spot for BAT inside J1's span (tried
first) is the board-edge strip that 1:BAT+ now needs. Each is now the only text on its line.

## Terminal legends and the top render (item 8 and the coordinator's render check)

Ink to the nearest DB125 VRML envelope (the body the top render draws; negative = under it) and the owner margin
(check_r8.terminal_legends ranking, >= OWN_MARGIN 0.3 mm):

| Legend | Spot | Ink to envelope | Owner margin |
|---|---|---|---|
| 1:E1- (J121) | horizontal on J121's north line, under IGN | -0.716 -> 0.245 | 3.32 |
| 2:E1+ (J121) | bottom side beside J121.2 | top -> bottom | 1.83 |
| 1:SW (J400) | 0.50 west on the board-edge strip | -0.030 -> 0.470 | 0.65 |
| 2:SW (J400) | bottom side beside J400.2 | top (under J400) -> bottom | 1.77 |
| 1:BAT+ (J1) | vertical on the board-edge strip beside J1.1 | -0.700 -> 0.550 | 0.38 |
| 2:GND (J1) | unchanged, south end | 0.230 | 3.50 |
| 1:S1 (J122) | horizontal along J122's south end, clear of the (42, 86) washer | -0.920 -> 0.180 | 3.50 |
| 5:GND, 3:S3 (J122) | unchanged | 0.220, 0.249 | 3.50, 0.53 |
| 1:5V4 (J9) | 1.15 south | -0.937 -> 0.213 | 3.44 |
| 4:RXI (J410) | 0.50 north | 0.220 -> 0.720 | 3.50 |
| 1:4V8 (J410), 4:TXO (J9) | 0.20 east, inner column | -0.067 -> 0.133 | 0.31 |
| 4:RXI, 1:4V8 (J420) | outer column x 44.18-45.38 | -0.067 / 1.333 -> 1.583 / 1.583 | 0.45 / 0.32 |
| 1:4V8 (J440, new) | vertical on the west board-edge strip | 0.470 | 0.33 |
| 2:GND, 3:TXO, 4:RXI (J440, new) | bottom side beside their pins | bottom | 1.41 / 0.30 / 1.74 |

Every top-side terminal pin and word legend is now wholly outside every DB125 envelope (smallest 0.133 mm) and
outside the 0.42 mm latch plus 0.15 mm half tolerance of the DORABO nominal bodies. 1:BAT+ cannot stay in the J400 /
J1 gap: anywhere there outside J1's envelope it is nearer J400.2 than J1.1, so it moves to the board-edge strip. Lines:
2:E1+ and 2:SW go to the bottom beside their pins, as J410 / J420 / J9 / J122 already carry their inner pins, so the
round 18 lines "SWITCH 2:E1+" and "BAT 1:BAT+ 2:SW" are gone; J420's wire-side legends move to an outer column, so
J410's 1:4V8 and J420's 4:RXI no longer run on across the seam; J121's and J400's designators are held on the
board-edge strip (the search had moved them into the two gaps). Lines still shared belong to one terminal: IGN over
1:E1- and SERVO 5:GND. J122's designator, which the search put beside 1:S1 and 0.910 mm under J122's envelope (round
18: 0.772 mm, read as a sliver), now stands vertical in the C84 / J122 gap at (33.3, 78.6), 0.395 mm from its own
courtyard and 0.705 mm from C84's.

**Render check.** The build's own renders of the final board (`r10_fab.sh`: kicad-cli 10.0.7 `pcb render
--quality high`, 1016 x 1988) are `.supervisor/r10_renders/r10_top.png` and `r10_bottom.png`; I looked at both (build 8,
the same PCB as builds 9 and 10), and at 2032 x 3976 renders cropped to the west terminals (J121 / J400 / J1), the east
terminals (J410 / J420 / J9 / J122), the north-west corner (J440) and the bottom J121 / J400 / J440 pins. Every pin
legend reads whole, including the four the round 18 render hid (1:BAT+, 1:5V4 at J9's south end, 1:S1 at J122's south
end, J410's 4:RXI) and 1:E1-. SWITCH and BAT each stand alone on their gap line, SWITCH against J400 and BAT against J1;
both sit in the ambient-occlusion shade between two bodies, as 3:S3 and 1:S1 do, and read clearly. E1+ appears only on
the bottom, as 2:E1+ beside J121.2, with 2:SW beside J400.2. Every word legend is at the same end of its own terminal as
in round 18 (RADIO and GPS at their terminals' north ends, now inside their spans); AUX sits at J440's north end like
GPS at J410's. The build 6 render showed J122's designator as a sliver under its body; after its move it reads whole.
J440's 1:4V8, the AUX word and the J440 designator read whole on the top, and 2:GND / 3:TXO / 4:RXI beside its pins on
the bottom. By measurement (ink box against the VRML envelopes), no top-side text is under a DB125 body except the
seven vertical terminal designators (J1, J121, J400, J410, J420, J440, J9) whose ink touches an envelope edge by
0.060-0.087 mm and reads whole. Bottom leftovers are listed under Residuals.

## Second vias (item 9)

| Feed | Via added | Nearest non-GND copper (F / B) | Hole to hole | In2 joined | K-power |
|---|---|---|---|---|---|
| C84 hold-up (VLOGIC) | (29.8, 81.15) | 1.440 3V3 / 1.638 3V3 via | 0.649 | n/a (no plane) | C84 hold-up >= 2 |
| U402 IN (PORT_5V3) | (42.75, 61.8) | - / 2.831 C431.1 | 0.450 | yes | U402 IN >= 2 |
| U401 IN (PORT_5V3) | (26.45, 11.95) | 2.000 GPS_RX_MCU / 1.275 U401.8 | 1.556 | yes | U401 IN >= 2 |
| U401 EN (PORT_5V3) | (24.9, 14.9) | - / 0.783 C408.1 | 0.450 | yes | U401 EN >= 2 |
| U401 OUT (PORT_4V8) | (29.75, 9.95) | 0.700 GPS_RX_MCU / 1.983 | 2.183 | yes | U401 OUT >= 2 |
| U400 OUT (buck, existing) | - | - | - | yes | U400 OUT >= 2 |
| U2 OUT (buck, existing) | - | - | - | (23.1, 78.1), (30.8, 79.26); bridge (26.4, 79.26) named | U2 OUT >= 2 + bridge |

The GND pours are 0.251 mm from every new via (zone clearance). Not doubled, with the measured reason:
- **U11.2 RAW_PROTECTED (24.3, 66.0):** a scan of every 0.05 mm spot within 1.5 mm (0.15 mm clearance, 0.25 mm hole
  rules, In2 RAW fill, a straight stub) finds 22 legal spots, every one 0.15-0.35 mm from the ACT_EN_MCU run at
  y 67.2; with D-R18-03's 0.5 mm floor between strong nodes and the PC1 enable it finds none. Respin item.
- **3V3A (16.0, 50.2):** the USB_LIMITED In2 run at y 50.85 is 0.65 mm from the 3V3A In2 run; the only legal spots
  (x 16.30-16.45, y 49.50-49.65) sit 0.15 mm from U1.100 / U1.1 and off the B.Cu trunk.
- **3V3A (27.0, 49.25):** F.Cu spots are <= 0.10 mm from U1.19's GND fan-out stub (x 26.0) or the pin row; the B.Cu
  spots beside C21 / C22 reach the In2 run only through the first via's own pad, needing a stub on F, In2 and B (three
  loops round one barrel). Not a clean spot.
The VLOGIC pair closes one loop on a net without a pour: route_check's r10 `PARALLEL_VIAS` names that via with its
measured reason, loops() leaves only it out, and a missing or non-parallel named via fails as `parallel_via`.
`check_r10.fire_path` is untouched (no fire-path net was doubled); K-power's path graph keeps the VLOGIC loop and
counts both vias.

## Spare AUX port (item 14, D-R19-14; owner approval 2026-10-30)

**Circuit.** J440 is an electrical copy of J410 with no new BOM codes: DB125-3.5-4P-GN-S C2757925 (pin 1 PORT_4V8,
2 GND, 3 board TXO, 4 board RXI), R471 / R470 1 kohm C21190, D440 / D441 ESD103-B1-02EL C535146, C444 100 nF C14663 and
C445 22 uF C21397 (C410 / C411 / D410 / D411 / R441 / R440 copies; C440-C443 are retired R9 references). The
schematic gate pins J440.1 / R470.2 / R471.1 and all six port MCU pins, and seeds three AUX faults.

**MCU pins and why.** The free UART is USART3 on PD8 / PD9 (option A): AF7 ([DS12110 Rev 8](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
Table 13 p94), FT_h (Table 9 p75), not loader pins (AN2606 Rev64 Table 119 p278: the loader's USART3 is PB10 / PB11).
Measured on the round 18 board, PD8 / PD9 sit on U1's north row between the GPS pair and the radio pair, so a route to
the north-west corner must cross the GPS pair. Its only B.Cu crossing lies over the microSD contact row (J430.1-4,
y 23.55-25.05) and the SD_CS / SD_MOSI runs parallel under the GPS diagonals, and east of them it straddles the In2
3V3 / PORT_4V8 boundary (x 28.0-28.3, K-region); PD8's own north escape was blocked by C23.2's fan-out via. The other
way round is an 80 mm F.Cu detour past the port LDO and buck. Option B (UART8 PE0 / PE1) moves the reviewed IMU_INT1 pin
and still crosses the I2C1 / SWD / SD / USB fan-out west of U1. So the free USART3 goes to J410 and J440 takes the
GPS's former USART6 PC6 TX / PC7 RX, whose pins face the corner. Both routes are F.Cu only: the AUX pair has no layer
change (no GND partner via), and the J410 pair changes only its first 7 mm before rejoining the former GPS run (C23.2's
via moves 1.2 mm west). All three ports keep the R19-MCU-01 rule (TX AF only while PA4 reads low, parked analog
otherwise); the binding note now names PD8 / PB13 / PC6 and records the configurable port map (default GPS J410, radio
J420, AUX spare; J9 excluded). PC6 / PC7 can also serve TIM3 / TIM8 channels (Table 12 p92); PD8 / PD9 have no ADC or
timer function (pin_table rows 55-56, 63-64).

**Placement and wire room.** J440 F(7.4, 16.25), rotation -90, wires leaving west like J121 / J400 / J1. Top washer at
(4, 4): 3.93 mm to the fit envelope (>= 3.8); J3's courtyard 1.67 mm away; wire room 5.003 mm (5.00-5.60 with the
sled tolerance), the other west terminals' figure, against the 4.95 mm floor. The cell sits on the top east of the
body (C444 F(12.5,12.6), C445 F(15.2,13.4), D440 F(13.9,17.2), R471 F(16.1,18.0), D441 F(13.9,21.4), R470
F(16.1,20.6)); the TX wire runs straight to J440.3 and the RX wire takes one 45 degree step to J440.4. M-6 (bottom parts
1.5 mm from THT pads) moved TP82 and R90 (above). PORT_4V8 reaches J440.1 on a 0.4 mm F.Cu run from the In2 PORT_4V8
region through two vias, (29.75, 9.95) and a new (30.5, 9.95): In2 under J440 is the 3V3 region. 22.8 mm, about
28 mohm: 8.5 mV at 300 mA if the radio moves there.

**AUX allowance.** U401 (TPS7A9101) is rated 1 A ([TI SBVS282A](https://www.ti.com/lit/ds/symlink/tps7a91.pdf) p1;
limit 1.5-1.9 A p5). The binding floor is GAP-3: junction <= 125 C at the 70 C bay limit with the inferred 80-110 C/W,
i.e. (5.546 - 4.712 V) x (0.46 A + AUX) + 22 mW <= 0.5 W, which allows 112 mA. **The spare port may draw up to
100 mA at 4.8 V** beyond GPS 150 mA and radio 300 mA, whichever ports they use (buck camera-short case 1.810 A < 2 A).

| Budget case (`parts_budget.json`) | Round 18 | With AUX 100 mA |
|---|---|---|
| U401 loss | 0.406 W | 0.490 W |
| U401 junction at 70 C bay (80 / 110 C/W, Inference) | 102.5 / 114.7 C | 109.2 / 123.9 C (floor 125) |
| U401 junction at 85 C (outside the bay range) | 117.5 / 129.7 C | 124.2 / 138.9 C |
| Buck, camera short with GPS / radio / AUX on | 1.710 A | 1.810 A (< 2 A) |
| LDO-limited port short cases (all three ports share U401's limit) | 2.911 / 3.160 / 4.420 A | unchanged |
| Battery-break ride-through, ports on, 300.8 uF to 3.8 V | 0.490-0.571 ms | 0.464-0.539 ms (470 uF 0.725-0.842) |
| Ride-through, GPS / radio / AUX on, camera off, logic shed | 1.533-1.655 ms | 1.304-1.412 ms (470 uF 2.038-2.206) |
| Fire current at 7.4 V, 0 / 4 stalled servos | 1.544 / 1.283 A | 1.541 / 1.279 A (>= 1.125 A) |
| AUX module minimum at 0.2 ohm harness | - | 4.642 V |

The hot-plug model passes all 2304 cases with C444 / C445 in the retained-output inventory (1.644 mF).

**Cost and stock (owner decision).** Live JLC 2026-10-31: AUX adds $1.14 per board ($0.403 terminal, $0.271 22 uF,
2 x $0.231 ESD, resistors and 100 nF): **$85.35 per board against the $84.41 M3 cap, $0.94 over**;
`check_procurement --cost-only` fails and was not weakened (82 codes, unchanged). Stock: none short; C2757925 now four
per board (37,827 in stock), C535146 eight (201), U4 still thin (9 for 5).

**Legends and renders.** AUX word F(13.4, 10.2), inside J440's courtyard span (the WORD_SPAN rule now covers AUX);
1:4V8 up the west board-edge strip F(2.4, 10.6); 2:GND, 3:TXO and 4:RXI on the bottom beside their pins. No top spot
for 4:RXI is nearer J440.4 than J3's shell pads (west and south) or J430's shell pad 11 (east) by OWN_MARGIN; B(4.2,
21.5) has 1.74 mm. In the final renders the AUX word, 1:4V8 and the J440 designator read whole on the top and the three
bottom legends beside their pins; no top legend is under a DB125 envelope (J440's designator touches its envelope edge
by 0.087 mm, as J1's and J121's do).

**Checks extended (each seeded).** `critical_reference.R10_PORT_UART` / `R10_PORT_NETS` add AUX (route_check and
K-reference); `uart_ports` holds all three ports (J410 on pins 55 / 56); CONNECTORS, PARTS, REQUIRED_FITTED,
WIRE_ENTRY, TERMINAL_PINS_R10, SHOWN_REFS, WORD_LEGENDS_R10 (AUX before SWITCH) and WORD_SPAN_R10 add J440 / AUX;
POWER_PATHS adds "J440 feed" (two vias); `plate_model.STRAIN_PARTS` adds J440 and C445 (masses J440 6 g + 2 g mated,
the J410 allowance, Inference); `fit_check.wire_rooms` lists eight terminals; `r10_parts` carries the allowance and
asserts the GAP-3 floor. K-power's path graph also counts the via behind (29.75, 9.95) on C406.1's B.Cu run, so losing
(30.5, 9.95) alone would pass it; the seeded test drops (29.75, 9.95).

## C87, U4 and the text items (items 10-13)

- **C87 (D-R19-10):** C21120 Samsung CL10B224KA8NNNC 220 nF 25 V X7R 0603 (Basic, C126's line), same land. EN at most
  2.06 V (8 % of rating). TPS25947 SLVSFC9C p9 thresholds: turn-on 88 / 56 / 45 ms at 6.0 / 7.4 / 8.4 V (31-122 ms
  worst; was 0.31-1.22 s); chatter immunity 19 / 33 / 41 ms (worst 12 / 22 / 27 ms; was 0.19 / 0.33 / 0.41 s, worst
  0.12 / 0.21 / 0.27 s), above the proposed 10 ms F6 bench criterion. The binding-note obligation that still said
  ">= 150 ms" now states these numbers. Hot-plug model re-run on the native board: all 2304 required cases and every
  row unchanged (pass); only the retained-output envelope moves (1616.12 -> 1613.41 uF, 2 s bound 5.878 -> 5.874 V,
  cold-input minimum still the -15 V clamp).
- **U4 (D-R19-11):** ISM6HG256XTR C51931514 fitted on the unchanged land; DS15034 Rev 1 Figure 5 p9 / Table 2
  pp10-11 / p187 match DS14623 (pins, axes, LGA-14L 2.5 x 3.0 mm, 14 x 0.475 x 0.25 mm pads); F1 / F2 met (+/-4000
  dps, +/-16 g, +/-32..256 g). WHO_AM_I 0x73 on both parts, FS_XL_HG codes differ (Table 150 p93): the binding note
  restricts firmware to 001 / 010. CPL rotation 0 -> 180 degrees from the EasyEDA LGA-14_L3.0-W2.5-P0.50-BR footprint
  (14 pads matched, residual 0.040 mm, next best 2.005 mm; confirm pin 1 in JLC's bottom-side preview). LSM6DSV320X
  (C26633007) stays the consigned alternate (its pads.json record kept). Live JLC 2026-10-31T05:30Z: **$84.21 per
  board** at 5 boards ($59.43 parts + $1.53 x 81 codes / 5), $0.20 under the $84.41 cap; stock: none short, U4 thin
  (9 for 5). `fab/cost_check.json` and `fab/stock_check.json` are refreshed and bound to this BOM / CPL.
- **Notes (D-R19-13, R19-MCU-03):** camera_uart: OE is PE9 / pin 39 with R102; mcu: PE3 / PE5 flank PE4, and
  PE3 / PE5 / PE6 / PC4 are no-net, analog, never driven (r10_sch asserts the pins against the pin table);
  check_actuators' comment matches; battery_entry's C87 note and usb_sense / telemetry cites updated.
- **Binding note / pin table (D-R19-13, R19-MCU-01 / -02 / -04):** PA4-low TX enable and the analog park on PA4 rising
  or the PA6 watchdog (pin rows 28 / 52 / 63, port_states, obligations 12, 14 and UART start-up); all DS12110 cites
  Rev 8 rev V (82 pin-table rows and the note; `sources.mcu_revision` says so); VREFBUF obligation (Inference for
  RM0433); the IMU obligation for both parts; INT1 polarity now cited (DS15034 / DS14623 p60). Regenerated by the
  record step; K-binding OK.

## Tests (every check change seeded)

New: `R19Gate.test_r19_s8_gnd_is_a_hazard_at_pyro1_out`, `R19Gate.test_r19_named_bridge_via`,
`R19Gate.test_r19_port_words_inside_their_own_span`, `R19Gate.test_r19_aux_word_inside_j440_span`,
`R4Synthetic.test_r19_own_barrel_void_is_exempt_for_hazard_nets_only`, `Synthetic.test_r19_s3_q122_gate_source_capacitor`,
`RealBoardSeeds.test_r19_load_switch_enable_cap_and_removed_probe`, `RealBoardSeeds.test_r19_doubled_feeds_keep_two_vias`,
`RealBoardSeeds.test_r19_hand_fitted_c84_has_no_paste`, `RealBoardSeeds.test_r19_pyro_out_barrels_clear_gnd`,
`RealBoardSeeds.test_r19_aux_port_feed_and_contract` (test_r10_check, 201 -> 212) and
`R10AuditScope.test_r19_named_parallel_via_closes_only_its_own_loop` (test_route_check, 67 -> 68). Changed: the S-3
synthetic fixture carries C123; `R3Synthetic.test_s8_load_switch_gate_and_enable_barrels` (hazard set is a superset);
`R18Gate.test_word_legend_face_and_subject_map` (one list, r10_post.WORDS derived from it, no seams);
`RealBoardSeeds.test_r18_word_legends_are_beside_their_own_terminal` (RADIO back on the seam and GPS at J410's edge
fail; both span margins >= 0.5 mm); `SchematicContract.test_binding_note_has_pad_policy_and_both_trace_locks` (the
R19-MCU texts, the PD8 / PB13 / PC6 parking rule and the port-map obligation); item 14: the direct-UART seeds add the
AUX port and J410's new pins, `test_one_port_definition_for_both_gates` adds AUX, the Plate tests add J440 / C445,
`test_conflicting_silkscreen_textboxes` moves its free spot off the AUX cell, `test_fit_check` lists eight wire rooms
(J440 at J121's room) and `test_route_check`'s exact-duplicate target follows GPS_RX's new run.

## Files changed

- Generators: `m3_design/r10_parts.py` (C84's footprint without paste; a comment cite), `r10_sch.py` (C123 symbol,
  R19 sheet notes, sentinel pins asserted), `r10_sch_check.py` (binding note), `r10_pcb.py` (U1.19), `r10_place.tsv`
  (C123 in, TP121 out; J440 and its cell in, R90 / TP82 moved), `r10_route_pyro.py` (TP121 stub out, C123 runs),
  `r10_route_power.py` (BAT_ENABLE via, five second vias, the AUX feed and its second via), `r10_route_signals.py` (the
  J410 pair from PD8 / PD9, the AUX pair and wires), `r10_route_usb.py` (R90 / TP82 runs), `r10_route_ground.py`
  (PYRO1_OUT keep-outs, three stitches), `r10_fanout.tsv` (C23.2's via, C444 / C445 returns), `r10_pcb.py` (J440's GND
  thermal), `r10_post.py` (one word list, WORD_SPOTS incl. AUX, PIN_SPOTS incl. J440, FIXED_REFS for nine designators,
  word_legends in its self-check, TP121 Fab entry out).
- Sources: `sources/r10_design/circuit.json` (C123, TP121, C87, U4, the AUX parts and notes), `pin_table.tsv` (rows
  51-52, 55-56, 63-64 for the port map), `masses.json` (J440).
- Checks: `tools/check_r10.py` (S-3 C123, S-4 manual-fit paste, S-8 PYRO1_OUT, K-reference / K-region own-barrel void,
  K-power seven paths and named bridge vias, one word list and the GPS / RADIO span, TP121 removed, C123 required),
  `tools/route_check.py` (PARALLEL_VIAS, parallel_via), `m3_design/check_actuators.py` (C123, TP121, C87 code, comment),
  and for item 14 `tools/check_r10.py` (port tables, uart_ports, word list / span, J440 feed), `tools/critical_reference.py`
  (AUX port nets), `tools/plate_model.py` (STRAIN_PARTS), `tools/fit_check.py` (docstring), `m3_design/r10_sch_check.py`
  (port pins, three seeds, binding-note obligations), `m3_design/r10_sch.py` (MCU notes), `m3_design/r10_parts.py` (the
  AUX allowance and the GAP-3 assert).
- Data: `tools/jlc_easyeda/pads.json` (C51931514), `tools/verified_part_metadata.json` (ISM6HG256XTR).
- Tests: `tools/test_r10_check.py`, `tools/test_route_check.py`, `tools/test_fit_check.py`.
- Records: `R10_DECISIONS.md` (D-R19-01..14; 151 unique D IDs), `AVA_LAYOUT.md`, `r10_plan.md`, this hand-back and its
  JSON twin.
- Regenerated by the build: the 15 sheets (8 change), `schematic.net.xml`, `kilib/rocket.pretty/M3_MA_8x10.kicad_mod`,
  `m3.kicad_pcb`, `r10_binding_note.json`, `parts_budget.json` (board hash only), `hotplug_inputs.json` /
  `hotplug_results.json`, `tools/jlc_corrections.json`, the fab package (BOM, CPL, Gerbers, PDFs, manifest) and, by the
  supplier refresh, `fab/cost_check.json` / `fab/stock_check.json`.

## Residuals and not done

- **Not doubled:** U11.2 RAW_PROTECTED, 3V3A (16.0, 50.2) and (27.0, 49.25): measured reasons above.
- **Not opened:** U9.1 (EN) to U9.5 (IN) 0.200 mm is TI's RPW pad pitch; the BAT_ENABLE via (17.1, 82.8) to
  BAT_FAULT_N 0.200 mm and R123.1 to BAT_ENABLE 0.330 mm (R19-SAF-02's other rows) were outside item 2 and are unchanged.
- **SWITCH and BAT** keep their thin identity margins (0.040 / 0.060 mm; no spot with a clear margin at their
  terminal's north end); each is now the only text on its line.
- **AUX cost is over the M3 cap:** $85.35 per board against $84.41 (live JLC 2026-10-31); `check_procurement
  --cost-only` fails. Owner decision: accept the AUX port's $1.14 above R3's cost, or change its parts (any saving that
  touches the ESD or the 22 uF breaks the identical-port intent).
- **K-power's path graph** counts the via behind (29.75, 9.95) on C406.1's B.Cu run, so it would not notice the loss of
  the AUX feed's second via (30.5, 9.95) alone (gate-lane item; the seeded test drops (29.75, 9.95)).
- **Item 14 designators:** C28 and R110 lost their spots to J440's courtyard and R90's move (hidden, kept on F.Fab, as
  D440 / D441); `tools/test_r10_plate.py` (not run by check.sh) was already stale on J430 and is unchanged.
- **Render leftovers, unchanged since round 18 (not terminal legends):** on the bottom, J430's designator lies mostly
  under the microSD socket model (its ink is outside the Fab body but inside the courtyard-sized model) and R461's lower
  half under the same model's edge. On the top, the vertical designators of J1, J121, J400, J410, J420, J440 and J9
  touch their envelope's edge by 0.060-0.087 mm and read whole.
- **Designators:** R88 (moved BAT_ENABLE via), C123, C28, R110, D440 and D441 are hidden, kept on F.Fab (94 hidden);
  the docs lane's hidden list needs them and drops TP121.
- **Cost:** items 1-13 alone were $84.21 ($0.20 under the cap with U4 at $14.34); with item 14, $85.35. Re-run the
  supplier refresh before ordering. U4's stock is thin (9 for 5).
- **Docs lane (not mine):** REQUIREMENTS F10 / M3_R10 still say GPS USART6 PC6 / PC7 and two ports; F6's ports-on
  ride-through figures (0.490-0.571 ms) are now 0.464-0.539 ms; the bench probe notes need TP82's new spot.
- **Inference / unmeasured:** C87's X7R DC-bias allowance; the Crss coupling figure; applying Table 9 note 7 to the
  VREFBUF tie; the 6.0 V FT cap and 4.0 V ADC-mode limit (Rev 11, not re-read); JLC's bottom-side rotation convention
  for U4's new footprint.
- **Not mine (left for the gate pass):** R19-GATE-01, -02, -03, -05's K-power IN-via wording, -07, the other rails'
  width floors, the stale V3V3_SENSE entry in `critical_reference.R10_SLOW_RETURN_NETS` and the R150-R155 strain rows.
  The SWITCH single word list, listed there, was done here at the coordinator's request.
- **No physical, firmware, bench or owner qualification** is claimed; the board is a CAD candidate.

## Decisions

D-R19-01 PYRO1_OUT barrels; D-R19-02 BAT_ENABLE via; D-R19-03 TP121 removed; D-R19-04 C123; D-R19-05 U1.19;
D-R19-06 word legends; D-R19-07 C84 paste; D-R19-08 pin legends; D-R19-09 second vias; D-R19-10 C87; D-R19-11 U4;
D-R19-12 nine fixed designator spots; D-R19-13 MCU text; D-R19-14 spare AUX port and identical port UARTs (owner
approval 2026-10-30). `R10_DECISIONS.md` now has 151 unique D IDs through D-R19-14.
