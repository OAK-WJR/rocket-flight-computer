# R10 round 24: routing lens

- **Target:** commit `f2b8251`, PCB `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e`, the same hash before and after the review.
- **Reviewer:** Claude.
- **Scope:** AGENTS §3 and REQUIREMENTS M2, applied to every D-R24 change and to the whole board. That covers headings and bends, clean routing, GND partner vias and reference planes.

## Totals

**0 Critical / 0 Major / 0 Minor.** No real error was found in this lens.

## Fix verification

| Change | Measurement | Verdict |
|---|---|---|
| D-R24-17: 59 → 0 right-angle bends | Independent scan of all 1057 segments. No segment is off-angle. All 35 two-end 90° bends have the inner corner inside pad or via copper. Every other 90° branch pair sits at a three-end node. The old-board breakdown matches the record: F.Cu 24 free + 1 via, B.Cu 26 + 3 via + 2 pad, In2 3. route_check on `1407e850`: 0 failing, `right_angle` 0 | confirmed |
| D-R24-17: pairs keep their pitch | CAM_FAULT_N / CAM_PWR_EN 0.502 vs 0.500 mm; SD_SCK / SD_MISO 0.700 vs 0.700 mm | confirmed |
| D-R24-17: USB pair | USB_DP is identical to the old board (16.461 mm). On USB_DM only the J3 strap changed, 19.708 → 19.286 mm (−0.422) | confirmed |
| D-R24-17: J440 clamp runs | 3.864 / 3.964 mm | confirmed |
| D-R24-17: chamfer hygiene | The cuts add no staircase, tiny jog, acute angle or short segment. DRC 0 on a copy. The smallest new clearance is 0.1536 mm | confirmed |
| D-R24-17: U9 trunk redraw | Widths and lengths as recorded: 0.3 / 0.7 / 1.0 mm. The F.Cu chamfer is 1.018 mm | confirmed |
| D-R24-02 / -03 / -04 / -07 / -08 / -10: second barrels | All 10 added vias are present; 3 were removed and 8 moved. Totals: 307 vias (168 GND), 1057 segments, 1867.022756 mm of track | confirmed |
| D-R24-09: U401 divider | Placement and routing as recorded. The OUT T lies 0.075 mm inside R402.1's land | confirmed |
| D-R24-11: D402 routing | Tap 4.114 mm, chamfered; return 0.7 mm | confirmed |
| GND partner vias (whole board) | Every critical layer change outside AUD-2 has a GND via within 1.5 mm; the largest distance is 1.492 mm (PYRO1_GATE) | confirmed |
| Reference planes (whole board) | Unreferenced samples fall only inside own antipads or voids, S-8 barrel voids or the recorded REF_STRAY entries. No B.Cu segment lies over two In2 nets | confirmed |

## Observations (not counted)

1. **Forks with a bare 90° wedge.** Seven three-way forks (not T's) leave a bare 90° wedge between two branches: 3V3A, IMU_CS, RAW_PROTECTED, USB_LIMITED, VBUS and VLOGIC ×2. All of them were on `5516eeec` too. Each branch meets another branch at 135°. M2's `right_angle` definition excludes junctions of three or more ends.
2. **BUZZ_G T short of its chamfer.** On B.Cu, the T at (20.5, 58.70) sits 0.020 mm before the chamfer start at 58.72: the cut is 0.15 where 0.17 would land the chamfer on the T, and that cut clears all other copper by more than 0.4 mm. VBUS keeps the same pattern, 0.05 mm, from before this pass.
3. **Chamfers that start inside a land.** Five chamfers start inside a pad land: D121.3, D121.4, U1.28, C31.2 and R163.2. route_check's pad_end_offcentre count rose from 57 to 70 and segment_inside_pad from 22 to 27; both are AUD-10 counted review items. The records name only R402.1 as a review-only residual.
4. **J440 terminal pins as layer changes.** J440.3 and J440.4 are plated terminal pins with tracks on both outer layers. The nearest GND via is 3.9 mm away and the GND pin J440.2 3.5 mm. The partner-via rule tests vias, not terminal pins. This was on `5516eeec` too.
5. **CAM pair pitch.** The CAM pair's cut is 0.65 mm against the exact 0.653 mm (a 2 µm pitch change).
6. **Other information counts.**
   - extra_bends: 8 → 14 (one chamfer piece each, so none is a staircase).
   - short_layer_hop: 8 → 18 (the named parallel vias).
   - power_via_no_gnd: 27 → 28.
7. **Leftover locations.** The section 6 text for `1407e850` gives the count of noncritical leftovers (5) but not their locations. The JSON location inventory is still bound to `632a9ad3`. M2 needs the locations only in the final board's list.
8. **BAT_IN width change at a T.** The trunk narrows 1.0 → 0.7 mm at the T (18.25, 85.3). A T is exempt from neck_down, and POWER_NARROW records the 0.7 mm feed.

## Checks run

- route_check `--profile r10` on probe copies of `1407e850` and `5516eeec`, with the instance-level diff.
- kicad-cli DRC on a probe copy: 0 copper violations, 0 unconnected.
- Independent scans on a pcbnew dump:
  - headings;
  - inner-corner coverage at every node;
  - end-on-body joints;
  - clearances;
  - pair pitch;
  - USB lengths;
  - GND partner distances.
- Independent reference sampling against the saved fills.

Probe files: `.supervisor/r24_routing/`.

## Limits

- Geometry and rules only.
- The reference void model is approximate; the gate's K-reference passed.
- route_check was not run with `--bumps-all`.
- The detour table was not recomputed.
