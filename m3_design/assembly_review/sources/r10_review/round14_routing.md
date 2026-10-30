**Round14 independent routing, AVA/M2, planes and returns review**

**0 Critical, 0 Major, 3 Minor groups**: one new bounded cleanup group and two carried M2 deviation groups. No demonstrated functional failure or AGENTS section2 violation. Target commit `f5e4a5a94013514edb952fd328325341b63a98df`; PCB `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6` before and after. Canonical files remain frozen. This report reviews the target; no alternative below has been adopted.

Fresh native inventory:46×90×1.6mm,2,259,597bytes,209footprints,966segments,296vias(168GND),1802.125220mm track and118 nets with pads/copper. Complete F/B/In1/In2 native rasters and full source/net inventories were inspected. All113 decisions through D-R13-03 and22 owner mandate groups were considered under current amendments; the JSON contains their index and source hashes. Historical results are context, not current proof.

**Active findings**

| ID | Severity / origin | Evidence and concrete disposition |
|---|---|---|
| R14-RTE-01 | Minor / new | Twelve same-layer cleaner alternatives are demonstrated below. Combined:9 fewer segments and4.985043mm less track; all pads/nets/poses/vias/zone outlines/unselected tracks identical. Implement only through the source/requalification workflow, including the exact USB_DM exception retirement and refreshed BAT_IN evidence. |
| R14-RTE-02 | Minor / carried | Four general noncritical transitions retain remote GND companions: NRST(14.2,37.3)3.679674mm; NRST(22.54,38.5)1.655174mm; BOOT0(13.8,45.6)1.662077mm; I2C1_SDA(9.97,51.5)2.232543mm. The mandatory1.5mm fast-net rule does not apply to these. Keep their M2 disposition and qualify reset/boot/I2C; any stitch/reroute needs native reference/clearance/DRC controls. No impossibility or functional-failure claim. |
| R14-RTE-03 | Minor / carried |140 current information items remain(110ordinary+22AUD10 inside-pad+8noncritical leftovers). Specific review entries include U4.14 SPI1_MOSI entry(17.55,44.94),0.05mm from pad center(17.5,44.94); C98 GND via(23.8,62.95),0.300mm from track axis with independent fill contact; four foreign inter-pad lanes and five near-edge endpoint records. Retain board-bound owner/assembler disposition; do not invent per-instance noncritical metadata gates or call native-clear entries open circuits. |

**Checked source alternatives for R14-RTE-01**

Every row was applied independently to a fresh native target copy, refilled, checked against12 selected contracts and full routing hygiene, then passed real KiCad10.0.7 all-severity/schematic-parity DRC:0violations/0unconnected/0parity. Native anchors use exact rounded integer coordinates. All lengths exclude via barrels and pours. Source files below are under `m3_design/`; full old/new polylines, UUIDs, widths, sources and individual DRC hashes are in [round14_routing.json](round14_routing.json).

| Net / layer / width(mm) | Window endpoints; replacement bends | Length old→new(mm) | Segments | R10 source |
|---|---|---:|---:|---|
| PORT_4V8 / B.Cu / 0.4 | (28.4,8.6) → (29.75,12.6); via (29.75,9.95) | 4.559188→4.559188 | 3→2 | `r10_route_power.py:port_supply` |
| 3V3 / B.Cu / 0.3 | (21.82,52.15) → (19.5,49.15); via (21.82,51.47) | 3.960975→3.960975 | 3→2 | `r10_route_core.py:draw` |
| USB_DM / F.Cu / 0.2 | (6.88,30.05) → (8.8,29.65); via (8.4,30.05) | 2.085685→2.085685 | 3→2 | `r10_route_usb.py:draw` |
| SD_MISO / B.Cu / 0.2 | (20.605,24.3) → (15.025,16.9); via (20.605,22.48) | 10.051068→9.711312 | 3→2 | `r10_route_sd.py:draw` |
| SD_CS / B.Cu / 0.2 | (26.105,24.3) → (26.975,16.8); via (26.105,17.67) | 7.860366→7.860366 | 3→2 | `r10_route_sd.py:draw` |
| I2C1_SDA / F.Cu / 0.2 | (15.45,47) → (9.97,51.5); via (14.47,47) | 8.000042→7.343961 | 3→2 | `r10_route_core.py:CoreTable.track` |
| ACT_GATE / F.Cu / 0.3 | (11.8,70.725) → (14.5,72.3); via (13.375,72.3) | 3.747792→3.352386 | 3→2 | `r10_route_pyro.py:draw` |
| CAM_IO_3V3 / B.Cu / 0.2 | (36.55,48.18) → (30.55,48.75); via (31.12,48.18) | 6.236102→6.236102 | 3→2 | `r10_route_signals.py:camera` |
| BAT_IN / B.Cu / 0.4 | (17.5,87.3) → (15.5,83.9); via (15.5,85.3) | 5.400000→4.228427 | 2→2 | `r10_route_power.py:battery` |
| USB_DP / F.Cu / 0.2 | (6.88,30.55) → (7.9,31.55); via (7.455,30.55) → (7.9,30.995) | 2.020000→1.759325 | 2→3 | `r10_route_usb.py:draw` |
| PYRO1_GATE / F.Cu / 0.3 | (14.4,53.3) → (16,54.24); via (15.06,53.3) | 2.540000→1.989361 | 2→2 | `r10_route_pyro.py:draw` |
| USB_LIMITED / B.Cu / 0.4 | (15.55,28) → (10.8,21.3); via (15.55,25.05) → (11.8,21.3) | 10.864214→9.253301 | 5→3 | `r10_route_usb.py:draw` |

USB data changes belong in R10 wrapper intercepts; the pinned R9 input stays frozen. USB_DM removes one obsolete exact REF_STRAY at(8.0793,29.5793): unmodified K-reference correctly rejects the stale entry, while deleting only that unused row in memory passes with0loose samples and5retained strays. No new exception or numeric relaxation was used. ACT_GATE preserves the remainder after R121.1; PYRO1_GATE preserves every branch after R126.2. BAT_IN changes only feed-to-R82.1, not the C88-first U9 feed.

The combined twelve-route scratch has957segments/296vias/1797.140178mm track, SHA`4ea3464eec8d8b75e8cdccb53e34dc72864f6708451828aba96f589e97f976f0`. It passes the same controls and a thirteenth genuine DRC, report SHA`3537a04fa43751bffcdc8a0f6005ab0cfd732928491103a975c11a08b5a7fcd3`. A fresh combined connected-polygon-component replay also passes(163items/62590samples/39nets). Independent BAT_IN hot-plug re-extraction/full2304required+60local sensitivity cases, refinement and cold controls pass; combined electrical SHA matches exactly. Minimum simulated IN−14.807373V, maximum falling/rising8.991477/5.090700V/µs under this model. These are Simulation/Inference using typical maker curves and estimated parasitics, not physical qualification. Equal-length alternatives improve bend count only. D-R13-03's retained power/pyro/fast-interface scope still applies; passing scratch controls is evidence for a source decision, not automatic authorization to change cells or a complete final build.

**Current M2 inventory and sweep**

| Production category | Count | Current scope |
|---|---:|---|
| pad_end_offcentre | 57 | Review-only entry geometry |
| segment_inside_pad | 22 | AUD10 counted representation |
| passes_through_pad | 1 | Review-only own-pad geometry |
| short_segment | 1 | Noncritical count/location only |
| width_change_junction | 11 | Review-only pad/branch geometry |
| short_layer_hop | 3 | Own-fill or junction hops |
| u_turn | 6 | Review-only route geometry |
| extra_bends | 7 | Review-only bend inventory |
| tiny_jog | 6 | Noncritical count/location only |
| power_via_no_gnd | 24 | Power observation, not a signal1.5mm violation |
| via_on_track_in_fill | 1 | Independent GND fill contact |
| detour | 1 | Noncritical count/location only |

Eight noncritical leftovers are located once here; their tiny/short/detour metadata is not a new blocking requirement.

| Category | Net | Layer | Location(mm) |
|---|---|---|---|
| short_segment | BAT_OVLO | B.Cu | (16.4,83) |
| tiny_jog | BAT_FAULT_N | B.Cu | (26,47.3) |
| tiny_jog | BUZZ_DRV | F.Cu | (20.5,51.8) |
| tiny_jog | BAT_FAULT_N | B.Cu | (28.2,47.5) |
| tiny_jog | I2C1_SDA | B.Cu | (9.97,51.5) |
| tiny_jog | BAT_ENABLE | F.Cu | (19.675,66) |
| tiny_jog | BAT_ENABLE | B.Cu | (21,68.6) |
| detour | USB_ILIM | net | (14.825,27.2) |

Full supplemental sweep:22 no-pour chain windows,37 track/via adjacency observations,45 pad/net adjacency observations,3steps inside via rings,3own-fill/junction hops,31via-ring folds and36net/MST rows. These overlapping diagnostics are not independently proved defects. The0.2mm adjacency review threshold exceeds the ordinary0.15mm native floor. Steps occur at3V3 B(29.2,48.5)0.212mm, CAM_MCU_TX F(32.2,42.85)0.212mm and CC1 B(7.85,29.25)0.113mm. Hops are PORT_5V3 F(26.8,8)→(26,8)0.8mm; RAW_PROTECTED F(14.1,7.6)→(14.1,9)1.4mm; RAW_PROTECTED B(20.3,79.1)→(21.1,79.1)0.8mm. None is a prohibited isolated series-hop chain.

Foreign lanes between two-pad axes: C84/3V3 F(27.5,79.26), minimum pad gap0.540007mm; C22/BAT_FAULT_N B(27,47.3),0.200041mm; C28/USB_FAULT_N B(13.05,24.9),0.200041mm; R87/RAW_ACT B(22,63.875),0.275038mm. Near-edge endpoint records are L1.2(24.2,77)depth0; R432.1(35.02,58.05)depth0.020mm twice; R120.2(18.23,73.3)depth0 twice. Native connectivity/clearance passes; retain entry/assembler review rather than infer opens.

Production route_check:0failures/0allowed/0stale,0exact-duplicate/collinear-node observations. All54 all-net bump windows(25critical/29noncritical) yield0removable bumps. A fresh78-chain/200one-or-two-segment redraw search and explicit actual-clearance54-window sweep supplied the trials. The legacy “margin_free” mutation alone leaves R10’s hardcoded0.01mm reserve active; a separate max(0.15mm,local rule) model with0.0005mm quantization slack accepts a0.155mm control and rejects0.145mm. Production rules were unchanged. Six focused positive/negative route/AUD2/AUD10/reference/overlap controls passed.

**Planes, critical returns and AVA comparison**

All11 selected native routing/reference/width/fill/MEMS contracts pass; additional K-legends/K-rules/T-1 pass. Required fast/pyro transitions:25/25 GND companions≤1.5mm, worst PYRO1_GATE(14.4,53.3)1.491643mm. K-reference:160170samples,10052unreferenced=10045own-antipad+7samples covered by6exact recorded strays,0loose. K-region:165items/62653samples/39nets pass. A separate per-named-zone connected-polygon-component replay also passes, so no required chain switches between disconnected pieces of the same plane net. There are3actual3V3 In2 pieces; they were not merged merely by net name.

All9 saved zone fills reproduce within0.01mm². F/B GND have14/16pieces, In1 GND onepiece; local CH1/crystal In2 GND eachone. In2 holds only power/GND. No sampled GND cell is unreachable from the flashed-through via field; geometric maximum same-layer reach is12.886mm F,15.954mm B and10.050mm In2. These0.05mm raster paths are not noise/impedance proof, and4mm is only a diagnostic bucket. PORT_5V3 aft crossband minimum1.151902mm; the0.899mm combined3V3 feedback-finger opening is not the main output bridge. Two3V3 fragments have>3mm diagonal below1mm width; no>3mm fragment below0.5mm was found under the supplemental0.15mm² area filter. Fast reference checks, not plane area alone, supply the geometric constraint evidence.

S-8 barrel-to-inner-copper minimum1.103mm at J121.1 versus1.0mm floor. S-9 fire/source and BAT_IN floors pass with precisely7existing0.4mm source-bridge exceptions. C82 local OUT/GND/total paths3.577817/9.426346/13.004163mm; D9 paths6.585534/8.176346/14.761880mm satisfy unchanged bounds. C98→U11.12 ground return is7.345584mm using conservative1.6mm layer penalties; transient behavior remains unqualified. All5terminal GND contacts are explicitly thermal. The sole soldered SMD via-in-pad exceptions remain U401.11(27.3,13.6)/(27.9,13.6),0.5/0.3mm, requiring filled/capped/planar VIPPO manufacture. No physical process compliance is inferred.

AVA-likeness was judged against visible organization and the latest owner amendments. Current terminal axes are westx7.4mm/eastx38.6mm, outward; U1 F(23,43)rotation0;106of154ordinary R/C parts are on bottom, all on0/90mod180 axes. Current GPS/radio passive pockets are not exact16mm translated copies after the documented THT/SD integration. Local decouplers, crystal, gate parts, camera isolation and power loops remain electrical constraints. All23terminal pin legends are correct/unique; no silk-mask overlap or>6mm legend observation;91hidden references remain on Fab. The [creator’s AVA R2 photo](https://x.com/bps_space/status/1299081393029382144) was viewed directly: visible terminal rows/controller/passive rows support this limited comparison; concealed copper/circuit/plane choices do not. No AVA circuit equivalence or physical access claim is made.

**Rejected controls and closure**

The first SDA scratch DRC failed one track_not_centered_on_via warning due to a1nm float conversion mismatch; its report is preserved, and exact-integer independent/combined replacements pass. First USB_LIMITED sketch added two0.7071mm offcentre entries inside TP82; the centered refinement replaces it. BUZZ_G added two0.13mm offcentre entries inside R162.2 and remains disqualified. ACT_FET_S failed the exact S-9 source-bridge contract; no waiver was changed. Early SWIG multi-board/removed-object probe failures and one incorrect component-label prototype were discarded and rerun successfully; no failed run is credited. No failure above is a target-board DRC failure.

Closed geometric items: former BAT_ENABLE window now15.639697mm, equal to its octile minimum; former C98 remote31.812mm return is now7.345584mm, while its fill/qualification compromise remains; CAM_RX_BUFFER has the adopted two-segment route via(30.05,42.625). Prior figures are not carried as active current defects.

Root independently ran the exact target’s real10.0.7 all-severity/parity DRC:0violations/0unconnected/0parity, report SHA`98f4bfc26c6e3dade86a6d24ced04b199b8c6fb730b7da532e15e56e1204d489`. That is root-run evidence, separate from this reviewer’s13scratch DRCs. This lens did not run canonical builds/fullcheck, all31final rules, fabrication exports or executable R10 firmware. Any source adoption needs regenerated binding/electrical/fab evidence and complete fresh checks/reviews. Native geometry and conditional simulation do not qualify timing/USB impedance, reset/EMI, SD power loss, fire behavior, hot R134, installed harness/retention, regulator stability, assembly/VIPPO, physical tool/card/stack access, first article or flight. No acceptance/order follows.

Full measured evidence, source hashes,113decision IDs/22mandates, fifteen trial outcomes and exact controls: [round14_routing.json](round14_routing.json).

Protocol disclosure: an overly broad CLI-location search over .supervisor/r14* inadvertently emitted unrelated current-round probe-script lines. It occurred after the fresh full-board inventory/sweeps, initial routing findings and all14 sketches had been independently generated, but before the final official candidate DRC batch/combined qualification and report. That output was not used to derive or calibrate findings; no peer report files were inspected and no further current peer artifacts were accessed. All claimed native routing geometries/controls are independently reproduced. This is a narrow isolation limitation; perfect blinding is not claimed.
