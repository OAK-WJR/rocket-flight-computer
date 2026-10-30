# Round 12: routing, AVA, M2, planes and returns

Frozen commit `d57b216c365fc8d18896bceba37f63caf20d52a4`, PCB
`0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`.
**0 Critical / 0 Major / 4 Minor groups: one new exact cleanup, three carried with fresh measurements.**
The PCB SHA-256 is identical before and after review. This independent lens made no canonical edit.
Full native coordinates, measurements, source hashes, every M2 instance and exact alternative geometry are in
[round12_routing.json](round12_routing.json).

## Current findings

### R12-RTE-01 — Minor, new exact window: BAT_ENABLE tail has a checked removable bend

`m3_design/r10_route_power.py:89`, **BAT_ENABLE / F.Cu**:
`(18.2,78.3) → (19.9,80) → (17.1,82.8)` is **6.363961 mm**.
The exact replacement
`(18.2,78.3) → (18.0232,78.4768) → (18.0232,81.8768) → (17.1,82.8)`
is **4.955635 mm**, saving **1.408326 mm**, with no pad/via movement or layer change.
This is a noncritical M2 cleanliness Minor, not a failure of the named fast-return rules.

I replaced only those two segments in a temporary native project, refilled, and checked:
all-severity KiCad 10.0.7 DRC **0**, unconnected **0**, schematic parity **0**;
`route_check --profile r10` **0 failing / 0 allowlisted / 0 stale**;
S-8/S-9/F9-2/K-copper/K-inner/K-reference/K-region/K-width/K-retained all pass.
The strict redraw geometry also passes. Production CAD remains unchanged.

Concrete generator fix: replace the complete line89 polyline with
`[(21.3,68.9),(21.3,75.2),(18.0232,78.4768),(18.0232,81.8768),(17.1,82.8)]`.
That merges the intermediate collinear node. The JSON preserves the two removed native UUIDs and lengths.
No full build, electrical model, firmware or physical qualification is claimed for this alternative.
The six prior R11 cleanup windows are covered by the current full-board scan; this is a distinct remaining tail window.

### R12-RTE-02 — Minor, carried: C98 still has a remote GND return

`r10_route_power.py` joins C98.2 **B(23.8,62.2)** to U11.6, which is PR1 tied to GND.
The device GND is U11.12. C98.2, U11.6, R133.2, R180.2 and C129.2 occupy a
**20.300299 mm² B.Cu GND island** whose sole stitch is **(30.15,52)**.
Fresh native 0.05 mm through-copper distances to that stitch are **13.496804 mm at C98.2** and
**15.171068 mm at U11.6**. A B/In1 shortest-GND-path diagnostic from C98.2 to U11.12 is
**31.812237 mm**, including conservative full 1.6 mm penalties at its two layer changes.
The search margin was expanded from 2 to 12 mm only to include the actual remote stitch.

TI identifies pin12 as GND and pin6 as PR1 on p4, and asks for close bypassing and short, wide supply routing
on p33 of [SLVSEA3F Rev F](https://www.ti.com/lit/ds/symlink/tps2121.pdf), freshly read for this lens.
There is no numerical maker loop limit here and no observed switchover failure. The measurements are geometric,
not an inductance, current-distribution or transient result; severity remains Minor.

Concrete disposition: provide a checked local C98.2-to-U11.12 return through the ground/fanout generators,
or retain this exact deviation for owner acceptance and USB/supply-transition qualification.
**No fully checked local alternative is proved by this lens.** The prior partial-via sketch is not requalified here
and is not represented as a local-return fix.

### R12-RTE-03 — Minor, carried: noncritical return companions

Fresh nearest-GND-via measurements, all at F/B transitions:

| Net | Transition, mm | Nearest GND via, mm | Centre distance, mm |
|---|---|---|---:|
| NRST | 14.2,37.3 | 11.7,40 | 3.679674 |
| NRST | 22.54,38.5 | 21.4,37.3 | 1.655174 |
| BOOT0 | 13.8,45.6 | 13.35,44 | 1.662077 |
| I2C1_SDA | 9.97,51.5 | 11.23,53.343 | 2.232543 |

NRST's third transition is1.486607 mm; I2C1_SCL is1.443087 mm.
These nets are outside the named numerical1.5 mm signal scope. Retain the exact inventory and reset/boot/I2C
qualification obligation; a stitch cleanup needs its own checked native alternative. This lens does not claim all
possible stitches are impossible and requests no fast-net or AUD-2 scope expansion.
Files: `r10_route_usb.py`, `r10_route_core.py` and `r10_fanout.tsv`.

### R12-RTE-04 — Minor, carried: pad entries and between-pad lanes

The inherited `r9_route_imu_baro.py`, used by R10's core family, still enters **U4.14 / SPI1_MOSI / B.Cu**
at **(17.55,44.94) mm** against the pad centre **(17.50,44.94) mm**: **0.05 mm offset**.
No new on-axis alternative was tested here. The fixed IMU exclusion and adjoining SPI routes remain present;
current native copper, DRC and fast-reference checks pass.

The complete two-pad-axis crossing scan finds these four current foreign routes:

| Part | Route/layer | Crossing, mm | Minimum pad-to-track edge gap, mm |
|---|---|---|---:|
| C84 | 3V3 / F | 27.5,79.26 | 0.540007 |
| C22 | BAT_FAULT_N / B | 27,47.3 | 0.200041 |
| C28 | USB_FAULT_N / B | 13.05,24.9 | 0.200041 |
| R87 | RAW_ACT / B | 22,63.875 | 0.275038 |

Five literal near-edge endpoints occur at three pads: **L1.2 B(24.2,77), zero polygon depth**;
**R432.1 B(35.02,58.05),0.020 mm depth, twice**; **R120.2 B(18.23,73.3),zero depth, twice**.
The former J122.2 near-edge entries are absent. These are connected entries; no open circuit or clearance failure
is asserted. Retain exact positions pending a fully checked entry cleanup in the power/signal generators.

## Fresh gate and complete M2 sweep

Native counts: **209 footprints, 973 straight segments, 295 vias including 167 GND,
1809.708732 mm track, no arcs**. An identical temporary project copy has fresh all-severity DRC/unconnected/parity
**0 / 0 / 0**. An initial incorrect scratch-library symlink produced199 library-resolution markers only;
correcting that temporary link and rerunning gives the zero result above. Those setup markers are excluded from findings.
No full build, full `check.sh`, ERC or fabrication-generation run was performed by this lens.

- Fresh `route_check r10 --routes --bumps-all`: **0 failing,0 allowed,0 stale**, no critical removable bump;
  **25 critical and 32 noncritical bump windows** searched. The single noncritical candidate is R12-RTE-01.
- Selected native **S-8,S-9,F9-2,K-copper,K-inner,K-reference,K-region,K-width,K-retained,K-fill** all pass.
  K-fill refills all 9 zones in memory with 0 stale fills. The two exact U401 VIPPO sites remain the sole soldered-SMD via-in-pad exception.
- K-reference: **160761 samples**,10056 outside fill, comprising **10049 own-antipad samples** and
  **seven samples covered by six recorded strays**, **zero loose samples**.
  K-region: **165 items,62984 samples,39 in-scope nets**, zero issues.
  All **25 required critical transitions** have GND partners≤1.5 mm; worst is PYRO1_GATE(14.4,53.3),**1.491643 mm**.
- S-8's four barrel minima to foreign non-GND inner copper are **1.103,1.900,2.699,2.100mm** for
  J121.1,J121.2,OUT via and GATE via. The unchanged floor is1.0 mm.
  Fire widths pass with all seven exact source-bridge exceptions; no generic neck exemption.
- F9-2 current OUT/GND/total paths: **C82 3.577817/9.426346/13.004163mm**;
  **D9 6.585534/8.176346/14.761880mm**, within the original engineering bounds.
  These are saved-copper geometry, not physical transient qualification.

The **140 literal route instances** partition into **108 ordinary information items,22 AUD-10 inside-pad
representations,nine noncritical hygiene leftovers,and one noncritical bump**. Exact collinear-node and duplicate
counts are zero. Categories overlap with the separate sweep and must not be added as independent defects.

| Ordinary information | Count | Scope/reason |
|---|---:|---|
| Off-centre pad ends | 57 | Connected entries retained for tidiness review |
| Power vias without1.5 mm GND companion | 24 | Numerical rule is for the named signal scope; exact distances in JSON |
| Width changes at junctions | 11 | Branch/via/pad widths; no forbidden plain-node neck-down |
| U-turns | 6 | Whole-chain angle, not alone an acute copper wedge |
| Extra-bend runs | 6 | Long escapes/lanes, not a short-segment staircase |
| Short layer hops | 3 | Power links with plane/branch contacts |
| Through-pad pass | 1 | Common GND bar through Q124.2 |
| AUD-10 inside-pad segments | 22 | Enclosed exact representations; counted without a partial-overlap waiver |

The nine audit2 noncritical leftovers are freshly counted and located here. The production tool has no
per-instance LEFTOVERS metadata for them; that bookkeeping is informational under audit2.

| Category | Net/layer | Location, mm |
|---|---|---|
| short_segment | BAT_OVLO / B | 16.4,83 |
| tiny_jog | V3V3_SENSE / B | 26.25,52.5 |
| tiny_jog | BAT_FAULT_N / B | 26,47.3 |
| tiny_jog | BUZZ_DRV / F | 20.5,51.8 |
| tiny_jog | BAT_FAULT_N / B | 28.2,47.5 |
| tiny_jog | I2C1_SDA / B | 9.97,51.5 |
| tiny_jog | BAT_ENABLE / F | 19.675,66 |
| tiny_jog | BAT_ENABLE / B | 21,68.6 |
| detour | USB_ILIM / net | R85.1,14.825,27.2 |

The separate complete M2 sweep measures **28 no-pour chain detours,31 track/via adjacency rows below0.2 mm,
42 pad/net adjacency rows below0.2 mm,three via-ring steps,three short poured links,38 route/MST/via rows,
five pad-edge ends,32 cross-layer via folds,and 27 power/short-hop rows**. Every location is in JSON.
The0.2 mm adjacency threshold is a review trigger; ordinary DRC remains0.15 mm and passes.
The margin-free search searches 57 windows, repeats the one strict bump, and emits 11 chain-redraw sketches.
Strict same-net geometry rejects USB_LIMITED and ACT_FET_S sketches; the other nine remain unqualified sketches,
including power/fire/USB changes. Only the separately named BAT_ENABLE alternative has this lens's DRC and native-contract evidence.
Fixed-terminal1–3 segment searches do not prove global routing optimality.

## Planes, inherited core and AVA scope

- **In1 GND:** one connected **3760.541955 mm²** filled piece, all 167 GND vias represented; no foreign In1 track.
  **In2:** RAW_PROTECTED 1254.087658,PORT_5V3 218.615257,PORT_4V8 323.791161 mm², each one piece;
  crystal GND 37.176062 mm² / eight vias and CH1 GND 237.869755 mm² / eleven vias.
  3V3 is 1448.057652 mm² in three stitched pieces with routed ties; the buck-to-core F.Cu bridge remains
  **4.4 mm × 0.4 mm**,(26.4,79.26)–(30.8,79.26). This is topology, not a DC/thermal field solve.
- Named cuts retain **1.151902 mm** summed PORT_5V3 crossband copper at x41 and **0.899 mm** through the
  3V3 feedback finger at y67.775, split into 0.4245 / 0.4745 mm paths round a via.
  That finger serves feedback, not the main output bridge. No  >3 mm power fringe narrower than0.5 mm is found;
  two sub-1 mm 3V3 fringe pieces remain, located in JSON.
- Outer GND has **15 F / 16 B filled pieces**. Native 0.05 mm through-copper raster finds no unreached point.
  Maximum reach: **F 12.885534 mm at(45.475,77.525)** and **B 15.953911 mm at(12.025,69.925)**;
  copper beyond 4 mm is23.132%/23.299%. No new global 4 mm requirement is inferred. C98's functional return is separately identified.
- The diagnostic region walk beyond mandatory scope covers **42 nets / 233 items / 55992 samples** with 51 item/chain
  notices, including named slow ADC/ACT/camera controls and ordinary reset/servo/status routes.
  AUD-2 drops only its exact named partner/reference checks; fast interfaces, critical hygiene and S-8 still block.
  These diagnostic split/void notices are not promoted to functional failures.
- QSPI lengths remain **CLK 7.850000,IO0 4.110955,IO1 9.714966,IO2 14.524012,IO3 9.760408,NCS 6.165635 mm**, exactly
  one transition each. Spread 10.413057 mm. IO2's F chain is 12.954 mm versus 9.687 mm octilinear distance;
  the current fixed-terminal search finds no 1–3 segment whole-chain replacement. No timing qualification follows.
  Y1's nominal projection is x21.6–24.1/y45–48.2: only foreign F.Cu **NRST 0.777817 mm** crosses it;
  BUZZ_DRV/QSPI_IO2 do not. Solid In1 GND intervenes; HSE bench stimulation remains open.
- The native floorplan and visible AVA reference support the adopted intent: outward terminal rows at west
  x 7.4 and east x 38.6, local battery/buzzer cells, repeated sense columns and short local port ends.
  BUZZ_DRV is 8.212742 mm / one via, and the two port resistor pairs still translate exactly 16 mm.
  GPS/radio clamps/capacitors are no longer identical translated cells after the through-hole-floor fixes;
  their actual shifts and poses are in JSON, consistent with D-R11-01's recorded local constraints.
  I inspected local copies of the creator's [R2 photograph](https://x.com/bps_space/status/1299081393029382144)
  and [R3 bottom footage](https://youtu.be/REYTmK1-Cl0?t=217), plus all four freshly generated native R10 copper-layer projections.
  Photographs supply visible arrangement/outer-routing inspiration only. No private AVA netlist, inner planes,
  firmware or protection performance is inferred.

Read-only scope includes the review packet, AGENTS/requirements, every owner decision/newest amendment through
D-R11-05 and its final addenda, AVA_LAYOUT, M3_R10, R10 validation, R9 severity precedents and read-only VEHICLE.
No current-round peer report was read. No canonical CAD/source change, Git action, build/full gate, firmware,
electrical/thermal/EMC/physical or flight test occurred. The sole alternative is a temporary native copy.
KiCad GUI launch was not retried after the recorded Computer Use rejection.

**PCB SHA-256 before = after:** `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`.
