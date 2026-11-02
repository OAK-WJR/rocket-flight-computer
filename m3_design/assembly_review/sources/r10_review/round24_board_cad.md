# Round 24 board pass: CAD lane (hand-back)

## Scope

Brief: `.supervisor/r24_board_brief.md` items 1-16, plus the owner's item 17 (every 90-degree bend chamfered to 45
degrees, and a gate that fails any that remain). During the pass the root made two calls:

- item 11 (J400 ESD): fit a ninth ESD103-B1-02EL from J400.2 to GND;
- item 12 (Fab bodies): stays deferred.

This pass changes the board. The fallback is `9b27268` (board `5516eeec…`). Records D-R24-01..17 are in
`sources/r10_design/R10_DECISIONS.md` (record index 207 through D-R24-17; D-R24-11 is rewritten as done).

Changes were made through the generators only. Nothing was hand-edited in the CAD. AGENTS section 2 still holds:

- S-1 to S-9 pass;
- the pyro gate networks stay local with no vias;
- the new clamp goes to GND only.

No git state was changed.

## Board

New PCB SHA-256 `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e` (2363869 bytes). Builds C and D gave the same hash. Builds A and B gave `e7e9f757…`, the
board before D402; they are superseded. The board is 46 x 90 x 1.6 mm, outline unchanged. The previous board was
`5516eeec…`.

| Count | 5516eeec | New |
|---|---|---|
| Footprints | 215 | 216 |
| Track segments | 983 | 1057 |
| Vias (GND) | 300 (167) | 307 (168) |
| Track length | 1871.612 mm | 1867.023 mm |
| Hidden designators | 93 | 92 |

- **Hidden designators:** C87 and R402 are newly hidden. C16, C20 and C404 are now shown. D402's designator is shown.
  The full list is in the JSON.
- **Vias:** 10 added, 3 removed and 8 moved.
  - Added: ACT_GATE (15.4, 72.85) and (11.74, 72.3); BOOT0 (14.2, 46.0); VCAP2 (18.3, 36.8); VLOGIC (34.5, 62.4);
    LOGIC_SOURCE_ST (30.45, 51.4); 3V3 (28.1, 59.4); GND (32.3, 60.1); USB_LIMITED (16.6, 28.0); GND (5.15, 65.575)
    (D402's return).
  - Removed: PORT_LDO_FB (29.75, 13.6), PORT_4V8 (30.575, 11.6), GND (31.4, 14.4).
  - Moved:
    - BAT_IN (17.5, 87.3) -> (17.5, 87.15);
    - GND (20.9, 83.53) -> (19.59, 84.06);
    - PORT_4V8 (29.75, 12.6) -> (29.75, 11.65);
    - RAW_PROTECTED (14.1, 9.0) -> (14.1, 8.5), (21.1, 79.1) -> (21.1, 78.25) and (30.175, 86.5) -> (30.175, 85.9);
    - GND (32.65, 87.5) -> (32.65, 86.7) and (36.6, 87.0) -> (36.6, 86.4).
- **BOM:** 81 JLC codes, 45 Extended / 36 Basic. The only change is the C535146 (ESD103-B1-02EL) line, 8 -> 9 per board,
  with D402 added. Placed parts go from 205 to 206. C84 is still hand-fitted.
- **CPL:** one row added and four changed.
  - Added: D402 at B(4.45, 65.9), rot 90.
  - C88 moves to B(18.67, 83.56).
  - R92 moves to F(31.0, 86.7).
  - R402 and R403 move from F.Cu to B.Cu, at (30.9, 12.85) and (30.9, 14.6).
  - CPL rows go from 72 top + 133 bottom to 70 + 136 (205 -> 206). The orientation-reconstructed counts go from
    69 + 122 to 67 + 125, plus 14 placement-only (corrected in the fix pass, D-R24-23).
- **Paste:** F 253 -> 249, B 375 -> 381.
- **Supplier evidence,** re-run on the final files (`fab/cost_check.json`, `fab/stock_check.json`):
  - Cost (2026-11-02T01:43:55Z): $85.60 per board at 5 boards (parts $60.81 + 81 codes x $1.53 / 5). That is $1.19
    over the $84.41 cap. It was $85.36 before D402, so D402 adds $0.24, its 9th piece at $0.2306 plus price movement.
    The cap stays the owner's row. JLC fixed fees add $16.79 per board.
  - Stock (2026-11-02T01:42:53Z): two lines are short.
    - U9 (C3662793): 28 in stock, -83 orderable, against a minimum purchase of 7.
    - U4 (C51931514): 9 in stock, 2 orderable, against 5 needed.
    - C535146: 201 in stock and 194 orderable, against the 45 needed.
    - The ORDERING section 8.1 options are unchanged.

## Items

| # | Item | Result | Before -> after (measured) |
|---|---|---|---|
| 1 | U4.6 / U4.7 GND via | kept (D-R24-01) | The legal region beside (16.75, 47.6) is about 0.38 x 0.32 mm. It is bounded by M-7's U4 body keep-out, the 3V3A legs (x 15.79 / 17.5) and U1.98's F.Cu IMU_INT1 escape (y 48.0 / 48.36), so it holds one via. A C30-move trial shorted to IMU_INT1 and was reverted. The fix needs an MCU-core reroute. |
| 2 | Q120 / Q121 gate vias | done (D-R24-02) | Q120: second barrel (15.4, 72.85) between the parallel F / B diagonals. Q121: second barrel (11.74, 72.3) with a B.Cu link under the F.Cu run. Neither crosses the ACT_FET_S bridge. B.Cu clearances are 0.361 / 0.342 mm. Both exception entries are gone. |
| 3 | BOOT0 | done (D-R24-03) | Second barrel (14.2, 46.0) with a B.Cu link. It sits 0.150 mm (the floor) from I2C1_SCL on F.Cu. R5 stays on B.Cu because U1.94's run is boxed by IMU_CS and I2C1_SCL. |
| 4 | VCAP1 / VCAP2 | VCAP2 done, VCAP1 kept (D-R24-04) | VCAP2: second barrel (18.3, 36.8). VCAP1: C19 is boxed on B.Cu, and U1.48's pad lies east of the via. Moving C19 to F.Cu needs U1.49's GND via moved. |
| 5 | U9 EN (R81 / C87) | kept (D-R24-05) | The B.Cu pocket at U9.1 is about 1.4 x 2.2 mm against the roughly 2.0 x 2.45 mm two 0603s need. Their GND would be an island enclosed by BAT_IN and BAT_OVLO. A via pair needs BAT_FAULT_N's F.Cu run at y >= 83.6, which meets the BAT_DAMP run. The fix is a west-cell re-layout with the OVLO divider moved. |
| 6 | Row 22 feeds | kept (D-R24-06) | U11.2: every spot breaks D-R18-03's 0.5 mm ACT_EN_MCU floor (best 0.402 mm). 3V3A (16.0, 50.2): U1.1 / QSPI_IO2 above (0.131-0.150 mm) and the In2 USB_LIMITED run below. 3V3A (27.0, 49.25): D-R19-09's reasons hold. |
| 7 | TPS2553 grounds | U402 done, U10 / R8 kept (D-R24-07) | U402.2 / R430.2: second GND via (32.3, 60.1). U10's island sits inside the VBUS ring and already holds two vias. R8.2's island lies under D4 / USB_DP and In2 USB_LIMITED. |
| 8 | Monitor taps | done (D-R24-08) | R60.1 (34.5, 62.4), U1.28 (30.45, 51.4), R91.1 (28.1, 59.4). Three entries are gone. |
| 9 | U401.3 FB | done (D-R24-09) | R402 B(30.9, 12.85), R403 B(30.9, 14.6). FB, the divider top and the divider bottom join U401 with no via. Three vias were removed. The OUT via moved to (29.75, 11.65). The OUT run's T sits 0.075 mm inside R402.1's land (a route_check review item, not blocking). Both alternatives were measured and are worse: 0.085 mm from J440's second via, or 0.057 mm from GPS_RX_MCU. |
| 10 | ILIM / USB OV legs | R87.1 (16, 28) done; R87.1 (22, 62.25) and R85.1 kept (D-R24-10) | Second barrel (16.6, 28.0). At the drop to R87.1, a second via necks the In2 3V3 fill (K-plane), and BUZZ_OUT, RAW_ACT and PYRO1_CONT_MID close the other spots. R85.1 has no legal spot. |
| 11 | J400 ESD | done, the root's call (D-R24-11) | D402 is a ninth ESD103-B1-02EL (C535146, on the existing line, so no new code or fee). It sits at B(4.45, 65.9) between J400's pins (M-6 1.768 / 1.808 mm). A 4.114 mm B.Cu tap runs to it from J400.2's own pad, ahead of R165, and its return is 0.7 mm to its own GND via. S-5 and K-actuators pin BAT_SW_RETURN to exactly J400.2, R165.1 and D402.1, with D402.2 on GND. S-4 now requires D402, and K-ports checks its side of R165, its path and its return. EN moves by at most 5.7 mV (Calculation; Inference: no 85 C figure), and the EN timing figures are kept. |
| 12 | Fab body outlines | deferred, the root's call (D-R24-12) | No stated rule requires them. The 14 lands are SHA-pinned vendor footprints: drawing bodies needs 11 library edits, a Fab sync in r10_post and re-pins. |
| 13 | Order-mark placeholder | done (D-R24-13) | JLCJLCJLCJLC is no longer drawn (r10_post) and no longer allowed (K-legends). The seeded test now fails it. |
| 14 | Tabs over GND only | kept as a deviation (D-R24-14) | The In2 RAW_PROTECTED strip and the PORT_5V3 band run side by side along the whole east edge, and the strip joins only at its forward end (y 63.3). Fixing this is a plane redesign. |
| 15 | Short-edge parts | R92, TP88 moved; the rest stay DFM queries (D-R24-15) | R92 -> F(31, 86.7) and TP88 -> F(35.5, 86.4) (courtyards >= 2.5 mm). Kept: C95, R166, R400 / R401 / R404, C403 (hot-plug and buck loops). |
| 16 | Optional cleanliness | not taken (D-R24-16) | Unchanged. |
| 17 | 90-degree bends | done (D-R24-17) | 59 -> 0 (F.Cu 25 -> 0, B.Cu 31 -> 0, In2 3 -> 0). route_check's new `right_angle` rule fails on every net, and its allowlist is empty. The chamfer pass takes the 53 plain bends (54 with D402's tap); the 6 pad / via bends and the U9 trunk are redrawn at source. Pairs keep their pitch (outer cut = inner + 0.586 p: CAM_FAULT_N 0.65, SD_SCK 0.77). USB: only USB_DM's J3 D- strap had bends, so the strap, a stub off the pair's run, is 0.422 mm shorter and the D+ / D- run is unchanged. J440's clamp runs each get 0.211 mm shorter (3.864 / 3.964 mm, under the 4.5 mm limit). |

## Checks and tests

- **Builds A and B** (`e7e9f757…`, before D402): A exited 1 and B exited 0 (1474 / 1590 s). They are superseded by C and
  D. A's three failing test seeds were fixed in tests only.
- **Build C:** `1407e850…`, 1642 s, exit 0.
- **Build D:** `1407e850…` (identical), 1637 s, exit 0.
- **Builds C and D:**
  - `r10_sch_check` OK. The sheets and netlist were regenerated with D402, and the seeds catch the clamp removed and its
    return moved off GND.
  - DRC 0, unconnected 0, schematic parity 0, ERC 0.
  - check_r10: 36 / 36 rules OK. S-1 to S-9 and every K-rule pass.
  - route_check: 0 failing, 0 allowlisted, 0 stale, `right_angle` 0. There are 5 unrecorded noncritical leftovers, as
    before.
  - Fab: the S-4 BOM / CPL, JLC-footprint CPL rebuild (206 rows) and paste (249 / 381) content checks pass, and the
    six-output manifest is bound.
  - The binding note was regenerated (K-binding OK).
- **check.sh:** exit 0 in builds C and D. After D, only the supplier evidence, the record text and these hand-back files
  changed, and no gate step reads them.
- **Hot-plug model:** 2304 cases, 0 failures.
  - Minimum -14.807 V (limit -15.0 V).
  - Steepest fall 8.995 V/us (limit 10).
  - Steepest rise 5.088 V/us (limit 100).
  - On 5516eeec the three were -14.807 / 8.991 / 5.091. C88 still intercepts the feed.
- **Tests (build D):** shell 11, procurement OK, fab validation 34, fit 33, paste 16, R10 parts 5, route 71, R10 262
  (6 numpy skips), numpy hot-plug / plate 6. All OK.
  - Route tests go from 69 to 71. Added: `test_r24_named_parallel_via_on_a_critical_net`, `test_r24_right_angle`.
  - R10 goes from 261 to 262. Added: `test_r24_j400_contact_clamp`. Fifteen tests were re-measured for the new board,
    including the synthetic S-5 pair, which now carries D402.
- **Not run:** no simulation beyond the hot-plug model, and no physical test.

## Files changed

- Generators:
  - `m3_design/r10_route.py` (chamfer pass, CHAMFER_CUTS);
  - `r10_route_core.py`, `r10_route_pyro.py`, `r10_route_power.py` (D402's tap and via), `r10_route_signals.py`,
    `r10_route_usb.py` and `r10_route_ground.py`;
  - `r10_post.py` (D402's Fab reference);
  - `r10_stage_check.py`, `r10_place.tsv` (D402) and `r10_fanout.tsv`;
  - `r10_sch.py` (D402 on the battery_entry sheet) and `sources/r10_design/circuit.json` (D402).
- Checks:
  - `tools/route_check.py`: `right_angle`; named parallel vias are also left out of the via count and the hop test;
    new PARALLEL_VIAS.
  - `tools/check_r10.py`: S-5's exact BAT_SW_RETURN membership and D402; SAFETY_FITTED, PARTS and PORT_CLAMPS gain D402;
    SINGLE_OPEN_EXCEPTIONS 22 -> 11; POWER_NARROW re-measured; PASTE_TOTALS 249 / 381; the order mark.
  - `m3_design/check_actuators.py`: the r10 BAT_SW_RETURN members.
  - `m3_design/r10_sch_check.py`: two D402 seeds.
- Tests: `tools/test_route_check.py` and `tools/test_r10_check.py`.
- Records: `R10_DECISIONS.md` (D-R24-01..17; D-R24-11 rewritten as done).
- Regenerated by the builds:
  - the sheets and netlist;
  - the board;
  - the binding note;
  - the parts budget's board binding;
  - the hot-plug inputs / results;
  - the fab package.
- Re-run supplier evidence: `fab/cost_check.json` and `fab/stock_check.json`.
- `STATUS.md`, `AGENTS.md`, `docs/*.md` and `parts_qualification.md` were not touched. No git state was changed.

## For the docs lane

- New board hash `1407e850…`, counts, paste 249 / 381, 206 placed parts and the hidden-designator list. Cost is
  $85.60 ($1.19 over the cap). Stock is short on U4 and U9.
- D402, J400.2's ESD clamp (D-R24-11), needs adding to the J400 rows and the ESD handling text. The clamp is now the
  first layer and the handling rule the second. The per-flight checks are unchanged (a shorted clamp keeps the board
  off, which the closed-switch check sees).
- Single points left: U4.6 / U4.7, VCAP1, U9 EN (R81 / C87), U11.2 and 3V3A x 2, U10 / R7 / R85.2, R8.2, R85.1, and
  R87.1's drop. The row 22 / 29 text needs updating.
- The order form no longer needs a mark. East tabs remain a deviation (rows 16 / 28). Fab bodies stay deferred.
- `right_angle` should be added to the AGENTS section 3 / REQUIREMENTS M2 wording.
