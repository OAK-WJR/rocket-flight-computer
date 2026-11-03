# R11 stage C4: family `ground` and the last routing clean-up (2026-11-03)

Stage C of `r11_plan.md` §4, last family. Nothing is committed or ordered. Decisions D-R11-50 … -59 are in
`R11_DECISIONS.md`. Evidence labels as AGENTS §2.5 (Measured / Calculation / Inference). Coordinates are board mm (x
east, y forward from the aft edge, KiCad's y). Every new run was drafted with a scratch aid (straight or one-bend GND
stubs checked against every layer's copper, holes, edges and rule areas) or by hand, reviewed, and frozen as explicit
tables (D-R11-07: the build never searches; the aid is not in the repository).

**State.** Stage C copper is complete: **0 unconnected items** and 0 DRC violations on the built board (Measured).
The build's final stage check (`ground`) still fails on exactly three route_check findings on two nets, each forced and
written up as an allowlist request for the gate lane (section 4). check_r11 fails K-legends (stage D) and K-reference
(section 6); every other rule passes.

## 1. What this stage drew

**Ground family (D-R11-50), `m3_design/r11_route_ground.py`, run last.**
* In1 and In4: one GND zone each over the whole board (outline inset 0.3 mm), clearance 0.12 mm, minimum width 0.1 mm
  (as D-R11-46), thermal reliefs on pads, island removal always. The S-8 rule areas of the pyro and power families stay
  as they were (ACT_GATE ×4, ACT_DRV, J121.1 on In1..In4; J121.2 and BAT_SW_RETURN on In2 / In3) and keep the planes
  out (section 7).
* No F.Cu / B.Cu GND pour: every GND pad has its own path, and an outer pour at R11's 0.1 mm rules would leave
  one-pad pieces with no via (K-copper pour debris) (Inference).
* Every GND pad without a via (115 pads, stageC3.md O-C3-7 and stageC1b.md O-C1b-6, plus C26.2, Measured) gets a stub:
  100 drafted runs with 59 new vias, 18 hand runs with 7 vias, and 5 second-barrel runs with 5 vias (Measured on the
  tables). Stubs are straight or one 45-degree bend from the pad centre, legs at least max(width, 0.2) + 0.05 mm, and at
  least 135 degrees between tracks that meet at a pad or via centre (route_check angle and jog rules).
* The 69 GND vias the earlier families left dangling now land on the planes (DRC: no via_dangling, Measured).
  Q124's two fire-return vias (6.925, 31.6) and (8.225, 31.6) land on In1 / In4 (check_r11 K-power fire return OK,
  Measured). D402.2 (J400's clamp) has its via (8.375, 5.0) (K-ports OK, Measured).

**Clean-up of the pending nets.**
* ARM1_SENSE (D-R11-51): one In3 diagonal; C26.2's core via removed. route_check clean; in pyro's NETS.
* GPS_TX_MCU (D-R11-52): jog middle 0.5 mm; route_check clean; in ports' NETS.
* SD_MOSI (D-R11-53): B.Cu straight after the In3 via (no jog). The via count and the GND partner stay forced (section 4).
* CAM_RX_BUFFER (D-R11-54): unchanged, forced (section 4).
* 3V3 (D-R11-55): the power family's 7 route_check findings and the In2 pour sliver are gone.
* Other families touched so the last GND pads could be reached (D-R11-55 … -57): USB C86.2's via, the VLOGIC trunk
  through C6.1, LOGIC_SOURCE_ST's duplicate run, R103 / R155 rotated, CAM_IO_3V3 / SERVO2_MCU / CAM_TX_BUFFER corners,
  U4's GND node, the R46x 3V3 via. `r11_fanout.tsv`: unchanged rows; r11_escape_check OK (69 rows, 0 open, Measured;
  exits N 16, E 15, S 12, W 10, P 16 as before).

## 2. Hand-drawn GND joints (HAND_RUNS; the aid found no legal site)

U11.12 to C32.2's pad; C85.2 / R86.2 to one via (16.40, 39.00) freed by the VLOGIC trunk change; R130.2 / R178.2 (under
Q120's BAT_IN tab) into C127.2; C14.2 to C16.2; C11.2 to C10.2's via; C60.2 into R61.2; C29.2 into C17.2; J2.5 from
inside its pad (south of Tag-Connect's keep-out) to (33.75, 41.42); R157.2 to R156.2; R105.2 into C94.2; R155.2 to
R105.2; R103.2 to (20.50, 12.03); C93.2 to R430.2's via; R430.2 from inside its pad to (24.70, 11.55); C430.2 into U402.2;
D121.2 to (24.80, 5.60); U4.6 / U4.7's second barrel (21.20, 22.50). Each was checked with DRC and route_check (Measured).

## 3. Gate results (Measured, `m3_design/r11_build.sh`, twice)

| Family | NETS done (cumulative) | r11_stage_check | unconnected after |
|---|---|---|---|
| core | 22 | OK | 470 |
| usb | 32 | OK | 437 |
| pyro (+ ARM1_SENSE) | 47 | OK | 387 |
| power | 75 | OK | 243 |
| ports (+ GPS_TX_MCU) | 89 | OK | 230 |
| servo | 97 | OK | 214 |
| sd | 102 | OK | 210 |
| signals | 110 | OK | 193 |
| status | 117 | OK | 184 |
| ground | 118 (all) | **FAIL**: route_check 3 (section 4) | **0** |

* DRC on the final board: 0 violations, 0 unconnected (Measured). The build stops at the `ground` gate (exit 1), so
  r11_escape_check was run by hand on the built board: OK.
* Both full builds give SHA-256 `142ec65f40efa3d7b02b398d26fb3f7a80cbd52313cbdc26885f61fcc43fd8e9`.
* route_check `--profile r11` on the zone-filled board: 3 failing (section 4), 0 allowlisted; 27 non-critical leftovers
  are reported without recorded reasons (INFO, not gated).
* check_r11 (full) on a zone-filled copy with its fit report:

| Rule | Result |
|---|---|
| S-1 … S-9, W-1, W-2, LC-1, M-1, M-3, M-5 … M-8 | OK |
| K-copper, K-inner, K-region, K-plane, K-fill, K-rules, K-lands, K-width, K-power, K-ports, K-loader | OK |
| K-legends | FAIL 394: silkscreen and designators not placed (stage D) |
| K-reference | FAIL 1 finding, 869 samples (section 6) |

## 4. Allowlist requests for the gate lane (forced findings)

| Finding | Measured reason |
|---|---|
| `critical_via_no_gnd SD_MOSI via (29.80, 17.05)` (nearest GND via 2.242 mm) | The via is the B.Cu-to-F.Cu change where R461.1 (the pull-up) and the F.Cu run east to J430 meet. Inside 1.5 mm: R460-R464's F.Cu pads (x 28.2-29.7), C400.1 (F.Cu, x 29.9-30.9, y ≤ 16.54), C404.1 (F.Cu, y ≥ 17.74), J430.10 (B.Cu, x 29.9-31.35, y 17.75-19.75), SD_MOSI / SD_CS F.Cu runs at y 16.75 / 17.45. A scan of every 0.05 mm grid point within 1.45 mm with the DRU floors found no legal GND via site (Measured on the final board). Moving the junction is blocked too: the F.Cu lane between C400 / C401 and C404 / C405 carries SD_MOSI and SD_CS with no room for a via, and SD_MOSI's B.Cu pocket at J430.3 is closed by SD_SCK and SD_CS's B.Cu runs. |
| `extra_vias SD_MOSI` (4 vias, need 1 + 2) | Pads U1.C8 (F), R461.1 (F), J430.3 (B). The MCU side must leave the field on In3 under 3V3 (K-region), drop to B.Cu before the PORT_5V3 region (x ≥ 29.4, y ≤ 20.55), cross to F.Cu at R461 and go back to B.Cu inside J430.3's B.Cu pocket. No route with fewer vias exists: router with the In3 region held to 3V3, U1.C8 to R461.1 or to J430.3 with at most 2 vias: none (Measured on the scratch board). |
| `extra_vias CAM_RX_BUFFER` (4 vias, need 0 + 2) | U12.1 and R100.2 are B.Cu pads. B / F only: 4 vias minimum (stageC1b.md section 8.6). With In3: the only 2-via route runs In3 from the 3V3 region into RAW_PROTECTED (y < 9.95), which K-region forbids for a port UART net; holding In3 to one region (RAW or 3V3) the router finds none (Measured on the scratch board). |

## 5. K-power single-via exceptions (D-R11-58, `r11_gate_data.json`)

Second barrels fixed U400.4, R401.2, R403.2, R81.2, R83.2, U4.6 / U4.7; U9.8 is tied to R84.2 (B.Cu, 0.1 mm under R84)
and C87.2 to R81.2's run (Measured: K-power OK). Five entries remain as `single_open_exceptions`, each with its measured
scan in the JSON: R86.2 / C85.2's shared via (16.40, 39.00) (pocket between LOGIC_ILIM, USB_LIMITED, U11 and R86 / R91:
no legal site in x 15.3-17.5, y 36.6-40.2), R88.2's via (18.95, 32.47) (every other site joins at 45 or 90 degrees),
R430.2's two vias (one legal site only), U402.2's via (22.15, 9.75) (no site in the U402 area). They are owner / gate
deviations of the same form as D-R11-45 / -48.

## 6. K-reference (open, D-R11-59)

869 critical samples lack In1 / In4 reference (Measured on the zone-filled final board):
* **624: NRST (621) and HSE_OUT (3) on B.Cu over the In4 void of the ACT_DRV barrel's S-8 keep-out** (15.40, 29.70),
  radius 1.3 mm on In1..In4 (S-8: GND counts for ACT_DRV). NRST's B.Cu run (16.55, 29.75) - (14.75, 27.95) and HSE_OUT
  at C26.1 lie inside it. A drafting-router search for an NRST B.Cu path from C24.1 to its In3 via that keeps 1.38 mm
  from the barrel found none (HSE_OUT's B.Cu run and Y1 / C26 close the north side; Measured). Ways out (Inference):
  move the ACT_DRV barrel (R121.2 / Q122.3 side) so the keep-out clears NRST and C26.1, or re-plan NRST's In3 leg with
  ARM1_SENSE's (both cross the same area).
* **245: copper edges of critical runs placed exactly at the 0.25 mm hole clearance from a foreign via**, where the
  plane's antipad (the same 0.25 mm hole clearance, plus the hole radius) ends (e.g. SD_DAT1 F.Cu at (29.10, 14.21-14.29)
  beside SD_MISO's via (29.45, 14.25)). With an inner-layer GND plane hole clearance of 0.2 mm in a scratch copy of
  `m3.kicad_dru` all 245 vanish and only the 624 remain (Measured). Owner: the gate lane (`m3.kicad_dru` is pinned by
  K-rules; JLC's inner-layer hole-to-copper floor to be checked against the capability page).

## 7. S-8 and PTH-to-inner-copper (Measured on the zone-filled final board)

* check_r11 S-8 OK: 8 barrels, 24 inner rings, gap 1.0 mm. Smallest distance from a BARREL_NETS barrel (its inner ring,
  or the hole wall where it keeps none) to foreign inner copper, GND counted foreign for ACT_GATE / ACT_DRV / PYRO1_OUT:
  1.01 mm (ACT_GATE via (14.60, 15.90) to BAT_FAULT_N's via ring on In1), 1.05 mm (ACT_GATE (13.95, 21.65) to In2 3V3A),
  1.10 mm for the others; J121.1 (PYRO1_OUT, no inner ring) to the In1 GND plane 1.10 mm.
* PTH hole wall to foreign inner copper: minimum 0.55 mm (J1.1, J1.2 and J121.2 to the In1 / In2 / In4 planes), the
  DRU's 0.55 mm rule and above JLC's 0.3 mm; check_r11 K-rules (pth_inner_copper) OK.
* The J121 / J1 / ACT_GATE / BAT_SW_RETURN keep-outs are unchanged.

## 8. Open items (not verified)

* O-C4-1 the three route_check allowlist requests (section 4): gate lane.
* O-C4-2 K-reference (section 6): NRST / HSE_OUT over the ACT_DRV keep-out (design re-plan) and the plane antipad
  boundary samples (gate lane).
* O-C4-3 the five single_open_exceptions (section 5) stay owner / gate deviations; each is a respin item if a site is
  found by a later placement change.
* O-C4-4 stage D (silkscreen, designators, title block, zone fill in `r11_post.py`), then `tools/check.sh` with the R11
  profile.
* Not verified: JLC DFM of the 0.1 mm plane necks between ball-field vias, plane current capacity, signal integrity, any
  electrical test.

## 9. Loader note added to stageC1b.md §8.4 (gate lane request)

stageC1b.md §8.4 now says (Inference unless labelled) that with R155 holding PA15 (SPI3_NSS) low the loader's SPI3 slave
is selected; whether it drives MISO (PC11) without SCK was not re-read from AN2606; at most PC11 sits at a static level,
and that is harmless because SD_MISO's other members are the card's DO, high-impedance while SD_CS (PD0, not a loader
pin) is held high by R460 10 k to 3V3 (Measured on the netlist), and R462 10 k (at most 0.33 mA, Calculation).
check_r11 K-loader is OK on this board (Measured; the gate lane's LOADER_R11).

## 10. Checks run

* `m3_design/r11_build.sh` end to end, twice: stage A gate, fit_check r11 and every family's stage check OK up to
  `ground`, which fails on section 4's three findings; identical SHA-256 (section 3).
* `r11_escape_check --board`: OK.
* `tools/check_r11.py` (full) on a zone-filled copy of the built board with its `fit_check --profile r11` report.
* `tools/route_check.py --profile r11` on the zone-filled copy.
* Not run: `tools/check.sh` (not this lane), signal integrity, JLC DFM, any electrical test. Nothing committed.
