# Round16: routing, M2 and visible AVA layout

**0 Critical / 0 Major / 2 Minor groups: one new, one carried.** Full independent lens on commit `b1b8658d5bf541795b7e7636c09f2e886ea8c67a`, PCB `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982` before and after, 2,256,162 bytes. No production file changed. This is CAD review, without physical, firmware or owner acceptance.

Fresh native geometry has209footprints,951straight segments,296vias(168GND),1788.675665mm track:377F.Cu/561B.Cu/13In2power segments, no In1tracks. Dry-drawing all six actual production families reproduces every native segment and via exactly; this is source correspondence, not a new complete build. All119decision IDs and22owner mandates were considered under their current amendments, including the narrow AUD-2/AUD-10 scope.

## R16-RTE-01 — Minor, new: SD_MOSI retains an avoidable turn sequence

`m3_design/r10_route_sd.py:24`, B.Cu, exact200000nm width. A fixed-anchor alternative replaces the indicated final four segments with two, saving **1.994602820mm**:

| | Exact native points in mm | Length mm |
|---|---|---:|
| Current | `(20.1,32.799999) → (20.1,27.7) → (21.6,26.2) → (25.005,26.2) → (25.005,24.3)` |12.526319344|
| Qualified copy | `(20.1,32.799999) → (25.005,27.894999) → (25.005,24.3)` |10.531716523|

The saved copy is `24a5880c0b1ceab27273dc101cec6225e87af25dea8f89eb88ec86b9d193bc5b`:949segments/296vias/1786.681062mm. It passes genuine native refill, unchanged pad groups, reference/region checks, the complete routing gate and official KiCad10.0.7 all-severity/schematic-parity DRC: **0violations/0unconnected/0parity/0ignored checks**. A fresh reader confirms947unselected segments and all via geometry, part/pad poses/nets and zone outlines identical. All209complete footprint blocks, including fields/models, and296via blocks are byte-identical. Its routing information count remains140; a lower information count is not the objective.

Concrete fix: adopt the worthwhile pair through the SD generator, preserving exact width, anchors and branches, then regenerate and qualify the production result and all required provenance/fab outputs. The exact checked bend is `(25005000,27894999)`nm. The generator rounds to four decimals, so nominal27.895mm source input still needs regenerated native verification; this copy is not itself an adopted generator patch. No SD electrical/timing/power-loss qualification follows.

The independent screen considered218same-width two-to-twelve-segment windows and561exact one/two-segment polylines, with≥0.1mm saving and0.16mm diagnostic copper clearance. Two other sketches were rejected: BUZZ_G bypassed the unsplit T at `(20.5,58.7)` and actually disconnected Q123.1; a GND alternative at `(14.2,48)` created a blocking10µm microsegment. Only SD_MOSI received complete saved-copy qualification. REQUIREMENTS M2 is the length/organization criterion; no maker numerical length violation or flight-function failure is claimed.

## R16-RTE-02 — Minor, carried: current M2 and return compromises

Fresh `route_check --profile r10 --routes --bumps-all` exits0: no blocking, critical allowlisted, stale or removable local-bump instance;46bump windows searched. There are **140actual information instances=111ordinary+23inside-pad+6noncritical hygiene**. The one exact collinear node belongs to AUD-10's review scope and is included in that historical111ordinary partition. Its separate AUD-10 review list has24rows; do not add them again.

| Information category | Count |
|---|---:|
|pad_end_offcentre|59|
|power_via_no_gnd|24|
|segment_inside_pad|23|
|width_change_junction|11|
|extra_bends|7|
|u_turn|4|
|tiny_jog|4|
|short_layer_hop|3|
|short_segment, collinear_unmerged, passes_through_pad, via_on_track_in_fill, detour|1each|

The six noncritical leftover locations are recorded once in the JSON. USB_ILIM remains the sole net detour:3.332106781mm versus1.049264069mm pad MST, one required transition between opposite-face pads. No fully qualified alternative for it, moving vias or rearranging its cell was established. It has not been removed; no impossibility claim is made.

Manual whole-board diagnostics find37route-pair rows and47pad-to-foreign-net rows below0.2mm, with0.15mm minimum;29pad rows involve another net on the same component, including5fine-pitch rows, and18involve another component. Actual DRC0.15mm passes. Nine literal near-boundary endpoint matches occur at five pad sites: C129.2, L1.2, R432.1, J3.A4B9 and R120.2; R432 depth is0.020mm, the others reach the polygon boundary. Track width still provides contact; this is not an open circuit or a new pad-penetration rule. Four between-pad lanes remain:3V3/C84 minimum0.540mm, BAT_FAULT_N/C22 and USB_FAULT_N/C28 each0.200mm, RAW_ACT/R87 0.275mm.

Other review observations are35net routes above the broader review threshold,18no-pour chain stretches,30projected via-arm folds and3steps inside via copper. These are diagnostics, not independent counts of needless routing. The three short power pairs are PORT_5V3 F.Cu0.8mm and RAW_PROTECTED F.Cu1.4mm/B.Cu0.8mm; their own pour/pad contacts and parallel rail transfer distinguish them from two pure serial layer-change vias. C98's saved-fill stitch retains0.300mm centre offset/0.050mm ring overlap, with no new tiny jog added to hide that annotation.

All25required critical transitions have a GND companion within1.5mm; worst PYRO1_GATE `(14.4,53.3)` to GND `(15.35,52.15)` is1.491643389mm. K-reference has158499samples,10051unreferenced:10045inside own antipads and6samples matched by5SPI1_MISO/SCK stray records; **0loose**. K-region has161items/62176samples and0issues. Passing these methods does not mean every sample lies above uninterrupted copper.

AUD-2 is exactly14named slow nets. Applying the region diagnostic deliberately to them yields11observations(5runs/5pads/1connected chain), not11distinct nets or actual gate failures. Fast UART/USB/HSE/SPI/QSPI/SD and critical hygiene retain their rules. NRST/BOOT0/I2C companion maxima remain3.679674/1.662077/2.232543mm, outside the named fast numeric rule. SWD/reset reference sampling still applies.

Concrete fix: retain these exact board-bound counts/locations, simplify practical residuals in the existing generators while preserving T contacts/widths/returns/power/safety behavior, and obtain dated owner acceptance of what remains. Actual reset/I2C/HSE, bypass, power-transfer and installed-interface behavior still needs bench qualification. Qualitative maker locality guidance does not turn those correctly disclosed pending tests into a demonstrated function failure.

## Coverage, primary evidence and limits

Fresh target official10.0.7 DRC is0/0/0. Native10.0.6 checks S-8/S-9/K-width/K-inner/K-copper/K-retained/M-7/F9-2/K-reference/K-region pass. Fire paths retain1.0mm BAT_IN,0.5mm fire copper and seven exact0.4mm source bridges. The two exact U401VIPPO sites remain the sole ordinary-SMD in-pad exception, conditional on manufacture. C82/D9 OUT+return loops are13.004163/14.761880mm within unchanged engineering bounds; these are geometric measurements, without a transient/inductance guarantee. All four actual copper layers were freshly plotted and visually inspected.

Complete primary pages were freshly rendered and inspected: [Diodes DS41326 Rev3-2 p15](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf), [TI TPS25947 SLVSFC9C pp62–63](https://www.ti.com/lit/ds/symlink/tps25947.pdf), [TPS2121 SLVSEA3F p33](https://www.ti.com/lit/ds/symlink/tps2121.pdf), and [TPS7A91 SBVS282A p25](https://www.ti.com/lit/ds/symlink/tps7a91.pdf). Their locality, return and thermal recommendations inform the review; reference-board pictures do not qualify this board. [ST TN1383 Rev1 pp7–9](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf) was read afresh as official web-PDF text. Individual outward IMU escapes do not establish complete stress/process or sensor-performance qualification.

The creator's [R2 studio image](https://x.com/bps_space/status/1299081393029382144), SHA`298e3f2c91a2db2864bc0ec61d38b74014358995eb724a9632205ec4cdac7255`, was independently inspected from exact retained primary bytes. It supports visible edge terminals, central processor, bottom passive rows and local cells. R10 follows that organization with its later single-switch, always-on-port, seven-DB125 and hinged-SD decisions. The image supplies no private netlist, inner copper or mandatory alternate safety design. No new AVA-layout function failure is demonstrated.

The search is bounded to fixed anchors/widths/layers and exact one/two-segment alternatives; it proves no global optimum or universal inability to simplify retained routes. Initial probe unit/pad-boundary/string and via-normalization errors were corrected before interpretation. A multi-candidate SWIG failure stops credit after the first saved copy; separate fresh readers/CLI establish that copy. Initial SVG-output/raster attempts failed and were corrected. Direct TN1383curl transport failed; only its official web text is credited. Full details and rejected C/M hypotheses are preserved in the JSON.

No current-round peer report/probe was read. Prior R15 routing was context after fresh measurements. No GUI retry/bypass, subagent, canonical build/full check, git action, source/CAD/fab edit or other-worktree edit occurred. There is no physical/electrical/thermal/transient/endurance/RF/ESD, SD/e-match, manufacturing/harness/retention/fit or firmware qualification. Reports are immutable after handoff.
