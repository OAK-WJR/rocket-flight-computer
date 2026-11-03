# Round 11 — routing, AVA, M2, planes and returns

Target: commit `21bc3b2`, native PCB SHA-256
`0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`.
**0 Critical / 0 Major / 4 Minor groups: two new, two carried with fresh measurements.**
This is an independent read-only lens, not acceptance or a complete fresh board gate.
The complete locations, measurements, retained-item reasons, source hashes and alternative vertices are in
[round11_routing.json](round11_routing.json). Counts below are literal instances, so coincident endpoints can appear twice.

## Findings

### R11-RTE-01 — Minor, new: demonstrated noncritical route cleanups

The ordinary passing gate leaves four removable noncritical bumps. `route_check --profile r10 --bumps-all`
finds them with its strict redraw geometry checks. I independently replaced each window in memory, refilled,
and ran K-reference and K-region: all four pass with zero loose reference samples. Two additional monotone
chain shortcuts also pass the same native subset. None adds a via or moves a pad.

| Net / layer | Exact replacement polyline, mm | Current → proposed, mm | Saved, mm |
|---|---|---:|---:|
| SERVO2_MCU / B | (30.55,72.65), (30.55,71.85), (33.255,71.85), (34.175,72.77) | 5.408 → 4.806 | 0.602 |
| USB_FAULT_N / B | (16.7,39.05), (15.0383,40.7117), (9.3,40.7117), (9.3,34.1) | 16.650 → 14.700 | 1.950 |
| LED_YEL / F | (14.4,43), (14.0464,42.6464), (12.3,42.6464), (12.3,44.6) | 4.646 → 4.200 | 0.446 |
| BAT_ENABLE / F | (21.3,68.9), (21.3,75.2), (18.2,78.3), (19.9,80) | 14.046 → 13.088 | 0.957 |
| BAT_SW_SOURCE / B | (7,64.1), (10.8,67.9), (10.8,69.2) | 8.900 → 6.674 | 2.226 |
| VLOGIC sense branch / B | (29.8,68.6), (29.8,67.7), (34.5,63) | 9.714 → 7.547 | 2.167 |

Concrete fix: change the corresponding polylines in `m3_design/r10_route_signals.py` (servo/LED),
`r10_route_usb.py` (USB fault) and `r10_route_power.py` (enable/switch/VLOGIC branch).
The two collinear vertices at USB_FAULT_N B(9.3,35.5) and VLOGIC B(29.8,70) can also be removed from their
generator tables without changing the conductive envelope. AUD-10 already permits these two nodes.
These are M2 cleanliness Minors. **No alternative has a DRC, full gate or model pass from this lens**;
native subset passes are not manufacturing qualification. Do not replace unrelated branches with the window table.

### R11-RTE-02 — Minor, new: C98 bypass return takes a remote GND island

`r10_route_power.py`, `joins()`, joins C98.2 to U11.6 on B.Cu. U11.6 is the PR1 input tied to GND;
the device GND is U11.12. C98.2 at (23.8,62.2), U11.6 at (23.5,63.75), R133.2, R180.2 and C129.2 share a
**20.552 mm² B.GND island whose sole via is (30.15,52)**. Native 0.05 mm through-copper distances to a
stitch are C98.2 **13.497 mm** and U11.6 **15.171 mm**. A B/In1 shortest-return diagnostic from C98.2 to
U11.12 gives **31.812 mm**, including conservative full 1.6 mm via penalties; its search window was expanded
to include the actual remote via. This is geometry, not an inductance or transient result.

TI's TPS2121 **SLVSEA3F, §11–12, p33** asks for close bypass placement and short, wide routing
([maker datasheet](https://www.ti.com/lit/ds/symlink/tps2121.pdf)). The part's nearby position alone does not give C98 a local return.
No USB switchover failure is demonstrated, and the maker gives no numerical loop limit here; severity is Minor.

Concrete fix: provide a checked local C98-to-device-GND path through the ground/fanout generators.
A conservative 0.05 mm search did not prove a simple fully local via/strap. A **partial** option is one GND via
at **(27.45,59.1), 0.5 mm ring / 0.3 mm drill**, inside the same island, requiring no strap. In memory it passes
ViaCheck's conservative pad/paste/hole geometry and K-copper/K-reference/K-region/K-inner/S-8 after refill;
the modeled return becomes **15.141 mm**. It is not a complete local-return solution and has no DRC pass.
The full probe, including old/new paths, is in the JSON. Prefer a fully checked local return if implementing this item.

### R11-RTE-03 — Minor, carried/updated: noncritical return companions

The current native nearest-GND-via distances are:

| Net | Transition, mm | Distance, mm |
|---|---|---:|
| NRST | (14.2,37.3) | 3.679674 |
| NRST | (22.54,38.5) | 1.655174 |
| BOOT0 | (13.8,45.6) | 1.662077 |
| I2C1_SDA | (9.97,51.5) | 2.232543 |

NRST's third via is 1.486607 mm away; I2C1_SCL is 1.443087 mm. These nets are outside the named numerical
partner-via scope. This updates historical R9-RTE-04; its old 3.3534/1.8806 mm figures do not describe this board.
Keep the measured residual in the acceptance inventory and qualify reset/I2C behavior; no claim is made that every
alternate stitch is impossible. No fast-interface waiver or AUD-2 scope expansion is requested.

### R11-RTE-04 — Minor, carried/updated: pad entries and between-pad lanes

SPI1_MOSI still enters U4.14 at x17.55 against the pad axis x17.50: **0.05 mm offset**, as the inherited core table
states (`r9_route_imu_baro.py`). The fixed IMU pose/body exclusion and adjacent SPI lanes remain; this lens does not
claim a qualified on-axis replacement. This is the surviving R9-RTE-05 entry issue.

The exhaustive two-pad-axis intersection scan finds **four current between-pad routes**:

| Part | Foreign route / layer | Crossing, mm | Minimum pad-to-track edge gap, mm |
|---|---|---|---:|
| C84 | 3V3 / F | (27.5,79.26) | 0.540007 |
| C22 | BAT_FAULT_N / B | (27,47.3) | 0.200041 |
| C28 | USB_FAULT_N / B | (13.05,24.9) | 0.200041 |
| R87 | RAW_ACT / B | (22,63.875) | 0.275038 |

These pass the ordinary clearance floor; M2 still asks review of pad adjacency/tidiness. The former LED1/R33/C86
between-pad list is not the current list. Seven near-edge endpoints occur at four pads: L1.2 (0 mm polygon-depth),
J122.2 (0.004 mm, twice), R432.1 (0.020 mm, twice), R120.2 (0 mm, twice). Native endpoint/connectivity hygiene
passes; no gap or open circuit is asserted. Retain the exact coordinates/depths pending any checked pad-entry cleanup.

## Fresh checks and complete M2 inventory

I ran native KiCad Python parsing/checkers on the actual saved PCB, without invoking kicad-cli, check.sh, a full
build or a service request. The board hash is unchanged after the probes. Native geometry is **209 footprints,
981 straight segments, 294 vias (166 GND), 1818.769511 mm track**, no arcs.

- Route scan including all-net bump review: **0 failing, 0 allowlist, 0 stale entries, 12 noncritical leftovers**.
  Thirty critical bump windows and thirty noncritical windows were searched. Four noncritical bumps are additional
  review items; no critical bump exists. No forbidden angle/staircase/stub, partial overlap, crossing without node,
  dangling via, pure series pour hop, pour sliver/finger or removed pad-pour contact is reported.
- Fresh selected contracts **S-8, F9-2, K-copper, K-inner, K-reference, K-region, K-width, K-retained all pass**.
  K-reference: **159306 samples, 10060 outside fill: 10053 own-antipad and seven samples under six recorded strays,
  zero loose**. K-region: **161 items / 62278 samples**, 39 in-scope nets, zero issues. All **25 required critical
  transitions** have a GND via within 1.5 mm; worst PYRO1_GATE (14.4,53.3), **1.491643 mm**.
- S-8 checks four barrels. C82's fresh OUT/GND/total paths are **3.577817 / 9.426346 / 13.004163 mm**;
  D9's are **6.585534 / 8.176346 / 14.761880 mm**, within the existing F9-2 engineering bounds.
  This lens does not claim fresh DRC or hot-plug numerical results; root owns those checks.

The **162 literal route instances** divide into **117 ordinary information items**, **29 AUD-10 review items**,
**12 noncritical hygiene leftovers**, and **four noncritical bump candidates**. Every instance has coordinates,
measurements and a retained-item reason in JSON `native_route.instances`.

| Ordinary information | Count | Why counted, not a blocking rule instance |
|---|---:|---|
| Off-centre pad ends | 64 | Same-net connected pad entries; exact offsets retained |
| Power vias without a 1.5 mm GND partner | 23 | Numerical rule applies to the named signal scope; actual nearest distances retained |
| Width changes at junctions | 12 | Branch/via/pad-entry widths; no forbidden plain-node neck-down |
| U-turns | 8 | Whole-chain heading count, not by itself an acute copper wedge |
| Extra-bend runs | 6 | Long lanes/escapes, not a short-segment staircase |
| Short layer hops | 3 | Power links with plane/branch contacts; not pure redundant series hops |
| Through-pad pass | 1 | GND bar through Q124.2 |
| AUD-10 inside-pad segments | 27 | Enclosed redundant representations; individual pad/length/location retained |
| AUD-10 collinear nodes | 2 | Exact straight nodes listed above; duplicate-segment count is zero |

The 12 noncritical leftovers are unchanged in count from the AVA handoff and are all located here, as audit 2 asks:

| Category | Net / layer | Location, mm | Measurement |
|---|---|---|---|
| micro_segment | SERVO1_OUT / B | (39.015,78.5) | 0.015 mm |
| micro_segment | SERVO1_MCU / B | (34.21,75.31) | 0.035 mm |
| short_segment | BAT_OVLO / B | (16.4,83) | 0.150 mm |
| tiny_jog | V3V3_SENSE / B | (26.25,52.5) | 1.800/0.453/1.080 mm pieces |
| tiny_jog | BAT_FAULT_N / B | (26,47.3) | 1.450/0.400/3.200 mm pieces |
| tiny_jog | LED_YEL / F | (15.45,43) | 1.050/0.424/1.700 mm pieces |
| tiny_jog | BUZZ_DRV / F | (20.5,51.8) | 0.424 mm middle, 0.300 mm offset |
| tiny_jog | BAT_FAULT_N / B | (28.2,47.5) | 0.283 mm middle, 0.200 mm offset |
| tiny_jog | BAT_ENABLE / F | (19.675,66) | 0.400 mm middle/offset |
| tiny_jog | BAT_ENABLE / B | (21,68.6) | 0.424 mm middle, 0.300 mm offset |
| detour | USB_FAULT_N / net | R90.2 (8.625,23.1) | 39.130 mm / 23.300 mm MST, ratio 1.68 |
| detour | USB_ILIM / net | R85.1 (14.825,27.2) | 3.330 mm / 1.050 mm MST, ratio 3.18 |

The separate complete M2 sweep gives **29 no-pour chain detours; 31 track/via adjacency pairs below 0.2 mm;
38 pad/net adjacency pairs below 0.2 mm; five steps within via rings; three short poured links; 39 route-ratio/via
review rows; seven pad-edge ends; 33 cross-layer via folds; 26 power/short-hop rows**. These categories overlap;
they must not be added as independent defects. Every location and measurement is in JSON `m2_sweep`.
The margin-free search examines 60 windows, repeats the same four bumps and yields 12 chain-redraw sketches.
Only the six replacements above have this lens's native alternative subset passes. Two other sketches fail strict
same-net geometry (USB_LIMITED: existing via; ACT_FET_S: existing track); the remaining sketches are unqualified,
including source-bridge/fire/USB geometry. No critical allowlist is introduced.

## Planes, returns, inherited QSPI and AVA coverage

- In1 GND is one **3776.019 mm²** filled piece, all 166 GND vias represented; K-inner finds no foreign-net track.
  In2: RAW_PROTECTED **1254.088**, PORT_5V3 **218.615**, PORT_4V8 **323.905 mm²**, each one piece;
  crystal GND **37.176 mm² / eight vias**, CH1 GND **237.889 mm² / eleven vias**.
  In2 3V3 is **1448.210 mm² in three pieces**, all with vias. Its feedback finger and local core lobe have routed
  ties; the buck-to-core F.Cu bridge is **4.4 mm × 0.4 mm**, (26.4,79.26)–(30.8,79.26), between two vias.
  This is not an unconnected plane island or a DC/thermal field solve.
- Named cross-section scans: PORT_5V3's aft crossing band has minimum summed copper **1.151902 mm at x41**;
  the 3V3 feedback finger has **0.899 mm at y67.775**, split around a via clearance into 0.4245/0.4745 mm paths.
  The latter serves the feedback branch, not the main output bridge. No power sliver longer than 3 mm below
  0.5 mm is found. Two 3V3 fringe pieces below 1 mm remain, boxes (17.814,48.809)–(20.939,49.825) and
  (7.643,27.547)–(10.709,28.907); exact areas are in JSON. These geometric cuts do not certify ampacity.
- Outer GND fills have **16 F / 18 B pieces**. On the 0.05 mm full-copper raster every GND point reaches a via/PTH;
  even the 0.282 mm² F fill piece without an internal via connects through routed GND. F max reach is **13.094 mm
  at (45.475,77.325)**; B max **15.395 mm at (23.225,63.875)**. Copper beyond 4 mm is **22.721% F / 22.277% B**.
  These are current review measurements, not an added global 4 mm requirement. C98's functional return is separately
  identified above; broad outer-edge copper is not asserted to carry switching current.
- A diagnostic applying the region sampler outside its mandatory scope covers **42 nets / 240 items / 56937
  samples**. It records 58 item/chain notices, including slow split crossings for BAT_SW_SOURCE, LOGIC_SOURCE_ST,
  BAT_FAULT_N, USB_OVLO, BUZZ_G and PYRO1_CONT_MID. V3V3_SENSE includes an uncovered B run at x26.25,
  y52.5–54.3. The full positions are in JSON. AUD-2's named slow exclusions and ordinary noncritical scope remain;
  these diagnostic notices are not new blocking findings. The former SERVO2_MCU split claim is not reproduced.
- QSPI lengths are CLK **7.850000**, IO0 **4.110955**, IO1 **9.714966**, IO2 **14.524012**, IO3 **9.760408**,
  NCS **6.165635 mm**, exactly **one transition each**. Spread is **10.413057 mm**. The current IO2 F chain
  (17,50.05)–(17.5,40.57) is 12.954 mm versus 9.687 mm octilinear distance; fixed-terminal redraw search finds
  no clean 1–3-segment whole-chain replacement. This is limited search evidence, not a proof of optimality or
  setup/hold qualification. HSE/USB/SPI/QSPI/UART/microSD reference and critical return coverage remain mandatory.
- Current Y1 nominal body projection is x21.6–24.1 / y45–48.2. The only foreign F.Cu centre-line crossing is
  NRST **0.777817 mm**; BUZZ_DRV and QSPI_IO2 do not cross it. Solid In1 GND intervenes. The old 2.733 mm buzzer
  crossing is retired by this placement, without claiming measured HSE immunity.
- The visible AVA arrangement is supported: west terminals x7 at y55.85/65.85/75.85; east x39 at
  y15.5/31.5/47.5/71.5, all outward. J410/J420, their two UART resistor pairs and both clamp pairs are exact
  (0,+16 mm) translations with equal side/rotation. The compact battery/buzzer and row pattern follow D-AVA-01.
  Comparison sources are the public R2 photograph and R3 outer-layer footage recorded in
  `reports/AVA board layout images.md`: [R2 photograph](https://x.com/bps_space/status/1299081393029382144) and
  [R3 footage](https://youtu.be/REYTmK1-Cl0?t=217). They support placement/visible outer routing only. AVA's private netlist,
  inner copper, protection performance and firmware are not evidence for R10.

Read-only coverage includes the review packet, AGENTS/requirements, owner decisions through D-AVA-02, AVA handoff,
M3_R10 and the historical R10/R9 severity/deviation context, the native board/netlist and routing generators.
No other current-round lens report was read. No production edit/save, Git action, service/CLI request, firmware,
electrical/thermal/EMC/physical test or full DC solve was performed. Retained M2 deviations still need the refreshed
board-bound owner inventory; AUD-2/AUD-10 and pending bench qualification are not promoted to automatic Majors.
The source hashes are snapshots taken while assembling this report; concurrent Phase B generator edits may already
contain proposed fixes. All native counts, findings and baseline checks above remain bound to the frozen PCB hash,
not to an unbuilt source edit.
