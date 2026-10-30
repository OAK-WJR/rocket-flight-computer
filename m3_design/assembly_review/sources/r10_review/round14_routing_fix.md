**Round14 routing source fix handoff**

Implemented the twelve source polylines explicitly elected by root after the full R14 review. Six R10 routing modules change, plus deletion of the single unused USB_DM REF_STRAY row in `tools/check_r10.py`. No pinned/shared R9 input, canonical CAD, numeric rule, other allowlist entry or original review report changes. Final canonical integration remains root work.

Actual six-family generator dry-run: **966→957 segments,296vias unchanged,1802.125220→1797.140178mm track**, saving **9segments/4.985043mm**. Its complete957-track multiset matches the qualified combined12 copy at exact native nanometre precision; digest`4d8b6b1cc1fc8918cc29950f42a1f3d48d901213ac3e96a3ca96a49a9380d5ca`. All296 generated via specifications also match, including net/position/diameter/drill/fill/cap flags. Part/pad/net/pose data, via geometry/modes/flags, zone outlines/layers/nets and all other track tuples remain identical.

| Route | R10 source | Segments | Length old→new(mm) |
|---|---|---:|---:|
| PORT_4V8 / B.Cu | `r10_route_power.py:port_supply` | 3→2 | 4.559188→4.559188 |
| 3V3 / B.Cu | `r10_route_core.py:draw` | 3→2 | 3.960975→3.960975 |
| USB_DM / F.Cu | `r10_route_usb.py:draw` | 3→2 | 2.085685→2.085685 |
| SD_MISO / B.Cu | `r10_route_sd.py:draw` | 3→2 | 10.051068→9.711312 |
| SD_CS / B.Cu | `r10_route_sd.py:draw` | 3→2 | 7.860366→7.860366 |
| I2C1_SDA / F.Cu | `r10_route_core.py:CoreTable.track` | 3→2 | 8.000042→7.343961 |
| ACT_GATE / F.Cu | `r10_route_pyro.py:draw` | 3→2 | 3.747792→3.352386 |
| CAM_IO_3V3 / B.Cu | `r10_route_signals.py:camera` | 3→2 | 6.236102→6.236102 |
| BAT_IN / B.Cu | `r10_route_power.py:battery` | 2→2 | 5.400000→4.228427 |
| USB_DP / F.Cu | `r10_route_usb.py:draw` | 2→3 | 2.020000→1.759325 |
| PYRO1_GATE / F.Cu | `r10_route_pyro.py:draw` | 2→2 | 2.540000→1.989361 |
| USB_LIMITED / B.Cu | `r10_route_usb.py:draw` | 5→3 | 10.864214→9.253301 |

USB/SDA redraws are R10 intercepts of exact inherited rows; pinned R9 source stays intact. The C14 supply tee, SD pull-up branches, R121/R126 subsequent gate branches, camera isolation and all existing anchors/widths/layers/cells are preserved. SD_MISO/SD_CS retain DX-aware diagonal knees. BAT_IN changes only feed→R82.1, preserving the C88-first U9 feed. The USB_DM exception at(8.0793,29.5793) is removed because the replacement no longer needs it; the other five entries and every other checker byte are exactly preserved.

Fresh fix-phase controls pass: seven AST parses; reversing only the stated edits reconstructs all seven pre-edit files byte for byte; actual complete source dry-run; complete track generation/refill into an ignored native copy; twelve selected native contracts including reference/region/fill/fire widths/bypass/legends; full production routing/critical-bump scan with0failures/0allowed/0stale/0bumps and139information items(one fewer extra-bends annotation). All51pinned R9 source/input files and both original R14 report hashes remain unchanged.

Generated ignored copy SHA`8bb1a87c82db697ba6db1ff870b7c92642378b1ec2cc1257ab551d95471f64d1`; qualified combined review copy SHA`4ea3464eec8d8b75e8cdccb53e34dc72864f6708451828aba96f589e97f976f0`. Track UUIDs differ. In1/all In2 fills compare exactly; maximum outer-GND symmetric-difference area is4.04661e-07mm², below the explicit0.000001mm² comparison threshold. The existing full fill-current gate also passes. No new DRC was invoked in this fix phase; the thirteen genuine10.0.7 individual/combined review DRCs remain attributed to their exact qualified files. Root’s final builds/checks must supply fresh canonical DRC evidence.

Fresh hot-plug extraction on the source-generated copy has electrical SHA`e4f13accbe3011affc9e9f748c0f72c48eb4f444536248a25903b8c6a0a25ed3`, identical to the previously fully swept2304required+60local alternative cases with convergence/cold controls. The full nonlinear sweep was not repeated here. This remains Simulation/Inference, not waveform, thermal or endurance qualification; final board-bound evidence must be regenerated during integration.

Rejected controls remain rejected: first TP82 sketch’s in-pad bend, BUZZ_G’s offcentre in-pad bend and ACT_FET_S’s S-9-contract change. The initial1nm SDA DRC failure remains preserved in the original review; the source output now matches the exact qualified native anchors. One initial fix probe stopped at an invalid pad API accessor; the complete replay uses the correct accessor and passes. No incomplete run is credited.

Canonical PCB before and after remains`e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`, based on commit`f5e4a5a94013514edb952fd328325341b63a98df`. Original report hashes remain MD`b5ce9d6dba8518831ca06fa8bdd0ade99c725c8b96e9840b191aab27639b868e`, JSON`20174636ee0c2faa328ffb8c35ce579c15e117ddc7719140c63209fc29266c09`. No new canonical PCB hash or commit is claimed.

Root must run two complete native builds/check0, refresh final electrical/fab/manifest/binding and decision/status/ledger records, then obtain fresh full committed-board rounds15/16. Carried noncritical return companions and remaining M2 entry/fill observations are unchanged; no physical, firmware, assembly, flight, first-article or owner acceptance follows. Exact source diffs/hashes, all twelve old/new polylines, native evidence and preservation controls are in [round14_routing_fix.json](round14_routing_fix.json).
