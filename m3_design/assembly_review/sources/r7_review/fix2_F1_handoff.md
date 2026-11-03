# R7 review pass 2: board, schematic and tool fixes (F1 handoff)

Fix agent F1 (board, schematic, `m3_design` scripts, `kilib`, `tools`). Worktree branch `m3-assy-r7`, uncommitted,
on R6 commit `3b215ba`. Nothing committed, pushed or opened as a PR. I did not edit `docs/*.md`, `STATUS.md` or
`AGENTS.md`; §6 lists what the records/documentation agents need to carry into them.

**Final board SHA-256 `9371d0376d37fd32805a9f411b7ab18c82f2034349cd7de72f113f67ae225047`**
(pass-2 board: `03fe75720f46…6d54`). Two clean consecutive `m3_design/r7_build.sh` runs from the SHA-checked R6
board produced this same file, and the saved board matches it. Schematic `m3.kicad_sch` SHA-256 `47057f7d97c7d748…`.

## 1. How the board is built now

`r7_build.sh`: `r7_pcb.py` → `r7_route.py` (session replay) → **`r7_rework.py` (new)** → `r7_post.py` →
`tools/check.sh`. `r7_rework.py` holds the post-route fixes as named stages (`ilim`, `fault`, `buzz`, `returns`,
`cam_rx`, `rxen`, `tidy`, `widths`, `fb31`, `planes`, `iface_returns`). It deletes copper only by exact endpoint
match (10 nm) and asserts every match, so a changed upstream board stops the build instead of being patched
silently (KIID seed 7401). Changes made before the reroute stage (limiter, radio and GNSS local copper, surgery, stitch)
changed the pre-reroute digest, so I re-recorded `m3_design/r7_reroute_session.json` with `r7_route.py --search`
each time. Each re-record gave the same router result (10 R6 items removed, 0 modified, 239 added; only
`before_digest` changed).

Files changed by me: `m3_design/r7_{build.sh,pcb.py,route.py,rework.py (new),post.py,lib.py,sch.py,parts.py}`,
`r7_reroute_session.json`; `kilib/rocket.pretty/C0402_DNP.kicad_mod` (new), `M3_MLT5020_3pad.kicad_mod`,
`kilib/m3.kicad_sym`; `m3.kicad_pcb`, `m3.kicad_sch` and sheets, `schematic.net.xml`; `tools/check_r7.py`,
`tools/test_r7_check.py`, `tools/export_fab.py`, `tools/test_fab_validation.py`, `tools/critical_reference.py` (new);
`fab/*` (regenerated, plus `stock_check.json` and `cost_check.json` from the existing supplier snapshot);
`r7_top.png` / `r7_bottom.png` re-rendered from the final board (`kicad-cli pcb render --quality high --floor
-w 1016 -h 2208`, which gives the old 984 × 2184 size; the old renders still showed TP89 on top).

## 2. Changes per finding

### QSPI return path: REGRESSION-01 / REGRESSION-08

| Item | Before (pass-2 board) | Now |
|---|---|---|
| BAT_FAULT_N In2 leg under QSPI_IO0/IO1 | B.Cu x 13.5 + In2 diagonal under both | U9.4 → via (12.3, 42.1) → In2 x 12.3 (west of IO0's B.Cu x 12.9) → via (12.3, 56.2) → B.Cu y 56.2 to TP85; R6 via (15.60, 55.90) to U1.81 tapped square. Via first tried at y 56.45, but its In1 antipad cut USB_DM's reference (80 samples), so I moved it to 56.2 (0 lost) |
| GND via near (12.7, 53.7) | removed by step B | not restored at that spot: BAT_FAULT_N and BUZZ_DRV now cross there. IO0's two layer changes instead have GND vias at (13.65, 44.6) and (15.75, 50.1), **0.78 mm** from (12.9, 44.4) and (15.55, 50.85) |
| BUZZ_DRV gap to QSPI_IO1 | 0.275 mm | **1.098 mm** (B.Cu under U1, then via (13.0, 55.6), F.Cu y 55.6, via (9.0, 55.6), B.Cu round C96 to x 1.55) |
| BAT_ILIM test-pad branch beside IO0/BUZZ_DRV | 36.8 mm, 3 vias, 0.225 mm from IO0 | router branch deleted; **TP89 moved to the bottom side at (8.1, 33.6)**, fed by a 6.5 mm B.Cu run from R84.1's via; nearest approach to IO0 now **3.14 mm**. Duplicate 0.15 mm U9.9–R84.1 copy and the R84.1 micro-segments also removed |
| QSPI_IO0 B.Cu 90° corner | 90° | chamfered 0.4 mm |

**R6 critical-reference sampling, rerun** (`tools/critical_reference.py`, the R6 method: 14 critical nets, centre and both edges
every 0.01 mm, F.Cu→In1 GND, B.Cu→In2 GND/3V3/3V3A; R6 board moved +18 mm). The R6 board gives 104,232 samples
(R6 record: 104,241; the 9-sample difference is from end-point rounding, an inference), 76,869 of them referenced.

| | Pass-2 board | Final |
|---|---|---|
| R6-referenced samples that lose their reference | 1,427 | **557** |
| … of which R6's IO0 F.Cu path R7 abandoned (no track there now) | 490 | 410 |
| … USB_DP B.Cu (BUZZ_DRV In2 under it) | 489 | **0** |
| … QSPI_IO1 B.Cu | 301 | 15 (IO0's inner-via antipad) |
| … USB_DM F.Cu | 15 | **0** |
| … QSPI_IO1/IO2/IO3/NCS beside R6 router vias (LED_YEL, BAT_SW_RETURN), unchanged | 132 | 132 |
| Candidate samples unreferenced where R6 was referenced | 1,905 | **820** |

All 700 remaining QSPI_IO0/IO1 new-loss samples lie within 0.6 mm of a via (measured):
- IO0's own two vias: 652, including IO1's 15 at IO0's inner via
- the BAT_SW_RETURN via (15.0, 37.725): 36
- the LED_YEL via (25.8, 42.3): 11
- IO1's own via: 1

Extended set (adds SWD, NRST and the radio SPI nets, In1/In2 tracks against F.Cu/B.Cu GND): lost 2,085 → 557. NRST In2 lost 658 → 0, USB_DP 489 → 0, IO1 301 → 15.
Candidate unreferenced, extended: 101,408 → 75,086.

### REGRESSION-02 / REGRESSION-03: return vias

- BUZZ_DRV's In2 leg under USB_DP and the U1.75 island is gone (rerouted as above). USB_DP B.Cu crossing → 1.5 mm clear.
- NRST-area B.Cu GND island (x 36.4–37.1, y 46.6–51) gets via (35.7, 50.15).
- D9.2: 0.5 mm via (19.65, 30.55), the only spot (band north, U2/VLOGIC/3V3 under it). Nearest-via path **>7 → 2.0 mm**; it also serves C6.2 (2.7 → 1.4 mm).
- C80.2: R6's leftover stub removed; via (6.3, 53.05): 10.8 → 2.05 mm.
- R167.2 (whose R6 GND link to C96.2 blocked BUZZ_DRV): own via (6.0, 57.2), 5.35 → 0.95 mm.

### DFM-01 / REQUIREMENTS-03: via in pad

- CAM_RX_WIRE via moved to (42.175, 55.82): hole edge is 0.205 mm outside R100.1's opening (it was 0.248 mm inside).
- `check_r7.vias_in_smd_pads`: every via hole must keep ≥ 0.1 mm from every SMD pad's mask opening. Only bare contacts are exempt (`TP\d+`, J2).
- Tests: via in pad fails; bare TP is exempt.

### RF-01 / DFM-02: no paste on the DNP shunts

- New library footprint `rocket:C0402_DNP`: C0402 copper, mask, courtyard and model, with no F.Paste. Generated by `r7_parts.c0402_dnp()`, which also adds it to the `M3:C` footprint filter.
- C303, C305, C313, C314 and the new C304 use it. This avoids the `lib_footprint_mismatch` warning that per-pad edits cause.
- `check_r7.dnp_paste` fails any DNP part with paste. Test added.
- Gerber check:
  - no paste flashes at C303/C304/C305/C313/C314
  - R304/R316 (fitted) have 2 each

### RF-02 / DFM-07: solid RF grounds

- D30, D31, C302, C303, C305, C313 and C314 GND pads are `ZONE_CONNECTION_FULL` (`r7_lib.RF_SOLID_GND`, `r7_pcb`). Each has a GND via 0.16 mm from its pad edge: D30.2 (14.05, 4.65), D31.2 (32.79, 4.75), C302.2 (9.76, 5.48), C303.2 (10.37, 7.08), C305.2 (15.89, 6.43), C313.2 (29.36, 6.9), C314.2 (34.58, 6.9).
- `check_r7.rf_grounds` checks both the solid connection and a via within 0.6 mm, and `thermal_policy` exempts these pads. Tests added.
- DFM-07: `ViaCheck` now rejects vias within 0.1 mm of paste apertures, so the two lattice vias at (12.86, 8.83) and (14.56, 8.83) are no longer placed. There was no other spot for them inside the T.
- RF-line stitching is unchanged on the `check_r7` metric: fence 21 vias, openings (6.3–12.4) and (20.0–23.8); largest line-side gaps GNSS west 3.90, east 2.65, radio 1.55 / 1.55 mm (same on the pass-2 board); In1 missing 0. The remaining vias (12.61, 8.3) and (14.81, 8.3) are 2.2 mm apart, just over the 2 mm pitch. They straddle the GNSS RF line (x 13.71), so no via fits between them; the removed pair sat 0.59 mm from them.

### ELECTRICAL-01: compensation placeholder

- C304 is an unfitted 0402 (C0402_DNP) between GNSS_ANT_GATE and GND, in the schematic (`r7_sch.py`, with a note to fit 1–2.2 nF only if the bench short test oscillates) and on B.Cu under R302 at (7.74, 16.9), with pad 1 in line with R302.1.
- It is DNP: excluded from the BOM and CPL.

### Interface routing quality

| ID | Done | Measured result / reason |
|---|---|---|
| RG-05 / RQ-01 | Partly | GND vias added beside interface layer changes: (10.0, 46.9), (9.8, 26.6), (9.0, 30.8), (1.6, 53.1), (3.3, 50.4), (9.61, 25.0), (20.0, 27.45), (20.3, 43.65), plus 5 in the strip at 0.72 mm (NSS hop ×2, TXEN ×2, DIO1) and IO0's 2 at 0.78 mm. Of the 29 corridor/band/RXEN layer changes, 10 are ≤ 1.0 mm and 17 are ≤ 1.5 mm. Layer changes with no GND via within 1.5 mm (scan `critical_via_no_gnd`): **29 → 12**. Still beyond 1.5 mm, with no legal spot (ViaCheck rules plus 1.0 mm from bare TPs): U1 column MOSI_MCU 1.71, MISO_MCU 1.75, BUSY 2.6, NRST 3.18, DIO1 3.6; band BUSY 1.65, MISO_MCU 2.11, MOSI 1.65; GNSS head RXD_MCU 1.56; strip entry TXD_MCU 1.57; RXEN (21.2, 30.45) 1.55, (23.8, 39.45) 2.23; QSPI_IO1's via (13.0, 51.5): no spot within 3 mm. Opening sites at the U1 column needs the escape re-spaced (pass2 RQ-01's suggestion, not done) |
| RQ-02 | Partly | In2 GND now under the radio B.Cu runs (strip GND zone grown forward to y 24.75 for x 14.3–41). NRST/DIO1 B.Cu over In2 GND: **2.7 % → 76.8 %** of samples. Not done: the 4-via detours stay. NRST's band run x 28.5–40 (y 24.5) still lies over router net CAM_MCU_TX on In2 (y 24.55); moving it means re-routing a session net. The rest of the unreferenced part is via antipads at the corridor/band turns |
| RQ-03 | Yes | FB31.1 → F.Cu 0.4 mm, 5.2 mm, to via (35.73, 27.34) in a new In2 3V3 lobe (34.5–36.4 × 27.0–27.9). R161.1 is tapped off the feed with its own 0.4 mm link; the path through its pad, the 0.2 mm neck and the In2 U-turn are gone. DC L1.2 → FB31.1: **29.3 → 12.22 mΩ** (§4) |
| RQ-09 | No | NSS/SCK swap left as is. The pass-2 suggestion moves R310 to 3V3 at the U1 end, a schematic and pin-contract change, and I found no clean spot at U1 for it. GND vias were added at both hop vias (0.72 mm) |
| RQ-10 | Yes | One width for the interface nets: 28 segments 0.2 → 0.15 mm, pads included; collinear joints merged (2). Scan: width_change_free 6 → 1, width_change_at_pad 2 → 0 |
| RQ-11 / RG-11 | Partly | RXEN gap to QSPI_CLK 0.175 → 0.25 mm (F.Cu x 23.575). QSPI_IO0 corner and VBUS_SENSE jog fixed. Left: band fan jogs including NRST's 0.1 mm jog, which the 0.5 mm via pitch against the 0.4 mm lane pitch forces; R307/C301 off-axis (C300's courtyard sits 0.01–0.02 mm from both, with no other spot); RXEN 90° at (18.35, 44.75) (U1.44 clearance) |
| RG-12 | No | Shifting the corridor east would put it over the In2 BAT_IN arm (x 7.2–9.9) and lose the GND reference RQ-14 now gives it. The inline resistors' 0.155 mm clearance stays (DRC-legal, ≥ 0.15 mm) |
| RQ-12 | Yes | RXEN leaves pad 10 from its outer end, runs aft of U31 along y 8.0 (body y ≥ 9.0) with R312 tapped, then up x 20.6. It passes U3.5 at **1.2 mm** (was 0.165, now F.Cu along y 30.45) |
| RQ-13 | Partly | In2 GND under the GNSS rows: the strip zone now reaches y 25.0 for x 9.6–14.3 and y 25.9 for x 0.3–9.6. FB30's 3V3 lobe now starts at y 25.4, so RESET_N's row has GND under it. R6's 0.4 mm stub on U30.9 / RESET_N deleted. RESET_N's 1.69× detour stays (pin geometry against the corridor order) |
| RQ-14 | Yes (reference); No (clearance) | The corridor references In2 GND: B.Cu corridor samples (x < 7, y 26–53) over In2 GND **0 % → 98.6 %**. The In2 BAT_IN plane keeps an arm along x 7.2–9.9 to U9; its BAT_IN_F stitch vias moved to (7.6, 26.6) and (8.8, 26.6). Cost: J1 → U9.5 rises 10.48 → 13.37 mΩ (§4). The 0.155 mm resistor clearance stays (see RG-12) |
| RQ-15 / RG-13 | Yes | Limiter re-placed (seeded annealing over the 8 parts, top 25 routed by r5_maze): R300 across x with Q32 under it. The sense pair now runs straight, with no loop round Q32. Copper is explicit geometry in `r7_route.limiter`: 38.0 mm of B.Cu (was 50.3 mm, worst link 2.9×; now every link ≤ 1.11×). The reviewer's "rotate R300" was trialled and is worse (55.2 mm) |
| RG-14 | Mostly | 3V3_GNSS bar at y 20.75, beyond the pad ends. C311/C312 pad 1 on C310.1's axis (x 37.2), so the supply runs straight pad centre to pad centre; FB31 enters C310.1 on one 45° leg; R310 link chamfered into R310.1; RXEN pad-10 entry fixed. Not taken: R307/C301 and TP30 (TP30 on SAFEBOOT_N's row breaks the "TP30 SAFEBOOT" legend window) |

### Legends, silk and BOM

| Finding | Change |
|---|---|
| DFM-10 / REQUIREMENTS-09 | `r7_post`: legends try the top face first with a wider box. GNSS at (8.05, 8.1) and RADIO at (35.74, 6.2) are now both on F.SilkS |
| FB31 designator | The courtyard test found no spot nearer FB31 than any other part, so it is hidden per AGENTS §3 (F.Fab keeps it) |
| REQUIREMENTS-08 | LS120 silk 0.12 → 0.15 mm, in the library footprint (`M3_MLT5020_3pad`) and `r7_post.SILK_W` |
| DFM-11 | `export_fab.write_bom` groups by LCSC code, joins comments with "; ", and stops when one code maps to several footprints/MPNs. 3 tests (`BomLinesByCode`). BOM: **92 lines = 92 codes**, CPL 219 rows; DNP C303, C304, C305, C313, C314 |

### RF-05: strip keep-out and checks

- `r7_lib`: a second `U31_KEEPOUT` rule area on B.Cu and In2 covers the whole body (24.86–34.86 × 9.0–19.0). A DRC trial showed `m3.kicad_dru` honours both same-name areas.
- New `check_r7` checks, each with tests:
  - `u31_body_keepout`
  - `rf_stitching`:
    - fence pitch ≤ 2.0 mm except the two named openings
    - line-side gap ≤ 2.5 mm, with named measured ceilings GNSS west 4.0 and east 2.7
    - In1 GND under every RF track and pad +0.3 mm, except the SMA launch cut-outs
- `KEEPOUTS` handles several areas with the same name.

Test count: `test_r7_check` 19 → 28.

## 3. Gate and tests (final board)

`tools/check.sh` exit 0:

```
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
silkscreen outside the board outline (46.00 x 118.00 mm): 0 stroke points
R7 CAD contract: OK
actuator safety contract: OK
nearest bottom/pin envelope: C76, 4.150 mm from support (42.0, 114.4) (minimum 3.5 mm)
nearest top hardware clearance: TP30.1 exposed top pad, 5.008 mm from support (4.0, 4.0) (minimum 3.8 mm)
fit check: OK (CAD envelopes only)
```

Tests (rerun on the final board; pcbnew tests with KiCad's Python): check_shell 2, fab_validation 23, fit_check 22,
maze_clearances 10, procurement 15, r6_check 17, r7_check 28, quality_audit 21, all OK. test_r5_repair: 1 error,
the known pre-existing `routing_lands_spacing` failure. `fab/m3_fab_manifest.json` verifies against the current CAD
(5 outputs). Stock/cost from the existing snapshot: $110.93 per board, 92 codes (52 extended), U4 short (consign).

Not edited in this pass: `m3.kicad_dru`'s pyro/arming/actuator rules and `check_actuators.py`. CH1 pyro copper and
the pyro sentinel pins (no net) are untouched; the actuator safety contract passes.

## 4. DC solves (`tools/dc_solve.py`, grid 0.1 mm)

| Path | Pass-2 board | Final |
|---|---|---|
| 3V3 L1.2 → U1.75 | 42.85 mΩ (R6 21.93) | **13.77 mΩ** |
| 3V3 L1.2 → FB31.1 | 29.3 mΩ | **12.22 mΩ** |
| 3V3 L1.2 → FB30.1 | 4.81 mΩ | 4.83 mΩ |
| BAT_IN J1.1 → U9.5 (logic feed) | 10.48 mΩ | **13.37 mΩ** (13.4 mV at 1 A): the cost of putting In2 GND under the corridor (BAT_IN keeps an arm at x 7.2–9.9) |
| BAT_IN J1.1 → Q120 (7.7 A actuator path) | 3.91 mΩ | 3.91 mΩ (30.1 mV, 0.232 W) |
| RAW_ACT Q121 → J122 (7.7 A) | 3.96 mΩ | 3.96 mΩ (30.5 mV, 0.235 W) |

## 5. Routing scan (scratchpad `rg/scan.py`, R7-era copper; pass-2 board → final)

Instances on R7-era copper: **364 → 269**. R6-inherited instances: 2,657 → 2,618 (reduced only where R7 work removed
inherited debris).

| Category | Before | After | | Category | Before | After |
|---|---|---|---|---|---|---|
| critical_via_no_gnd | 29 | 12 | | short_segment | 26 | 18 |
| pad_end_offcentre | 62 | 38 | | u_turn | 14 | 12 |
| pad_entry_diagonal | 40 | 26 | | acute_angle | 10 | 5 |
| segment_inside_pad | 10 | 2 | | acute_at_padvia | 12 | 8 |
| width_change_free | 6 | 1 | | collinear_unmerged | 8 | 5 |
| width_change_at_pad | 2 | 0 | | right_angle_corner | 6 | 3 |
| side_by_side_overlap | 5 | 3 | | extra_bends | 6 | 4 |
| collinear_overlap | 1 | 0 | | tiny_jog | 4 | 3 |
| dogleg | 28 | 31 | | chain_detour | 24 | 25 |
| off_angle_rounding | 5 | 7 | | staircase, short_layer_hop, net_length, passes_through_pad, crossing_without_node, end_in_zone_only, via_offcentre_joint | unchanged | unchanged |

Increases, by net:
- dogleg +3 (6 new, 3 gone):
  - new: BUZZ_DRV ×3 (round C96 and under U1), BAT_FAULT_N ×1 (In2), the 3V3 FB31 feed's jog to the lobe via ×1, GNSS_ANT_SRC ×1 (limiter)
  - gone: BAT_ILIM ×2, LNA_EN ×1
- chain_detour +1:
  - new: TP89's B.Cu branch 6.54 vs 4.64 mm, and the 3V3_GNSS bar outside U30's pads (RG-14) 2.15 vs 1.54 mm
  - gone: GNSS_ANT_SRC
- off_angle_rounding +2: RXEN and BUZZ_DRV, deviation 0.00014° and 0.00001° (coordinate rounding).

Most remaining R7 instances are:
- forced (corridor topology, band fan),
- on session-router nets (PULLPIN, LED_RED, CAM_MCU_*, BAT_SW_*; RQ-04/06 are other agents' findings), or
- rounding.

## 6. Not done, and notes for the records/documentation agents

Not done (reasons above):
- RQ-09
- RG-12 and the 0.155 mm resistor clearance
- RQ-02's detours, and its NRST band run over In2 CAM_MCU_TX
- RQ-13's RESET_N detour
- RQ-11's band jogs, R307/C301 and TP30
- RXEN 90° at (18.35, 44.75)
- the 12 interface layer changes listed under RG-05 with no GND via within 1.5 mm, including QSPI_IO1's via
- GND via at (12.7, 53.7) not restored (alternative vias placed)
- D9.2's via is 0.5 mm

Also not done:
- BAT_SW_RETURN hook (RQ-04, another agent)
- the R7 firmware board binding (none exists yet; the board change leaves nothing to rebind)
- `tools/route_check.py` (named by the documentation handoff) does not exist; I did not create it

For `docs/M3_R7.md` / `R7_VALIDATION.md` / `STATUS.md` (records agent):
- board SHA above; build chain now includes `r7_rework.py`
- hidden designators 92: +FB31, Q32, R302; −Q30
- TP89 is now on the bottom at (8.1, 33.6). ORDERING §7's washer note citing TP89 3.86 mm from (4, 64) is stale; nearest bottom envelope is now C76, 4.150 mm
- C304 DNP (ELECTRICAL-01); BOM 92 lines; the `C0402_DNP` footprint
- "104,241" is the R6 total sample count (the referenced count is 76,869 on the R6 board)
- critical-reference and DC tables (§2, §4)
- RF stitching: on `check_r7`'s method the gaps are GNSS west 3.90 / east 2.65 and radio 1.55 / 1.55 mm (the same on the pass-2 board). REQUIREMENTS F10 cites pass2_rf's 4.27 / 3.68 mm, measured another way; reconcile the method before quoting either
- R310 unchanged
