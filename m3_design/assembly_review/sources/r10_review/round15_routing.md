# Round15: routing, M2 and visible AVA layout

**0 Critical / 0 Major / 2 Minor groups (one new, one carried).** Fresh full lens on commit `789f4d516251991bdf1518254d537ff7b41f65bb`; PCB `7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783` before and after, 2,257,812 bytes. No production files changed. This is CAD review, not owner acceptance, physical or firmware qualification.

The complete native board was reviewed, including inherited copper: 209 footprints, 957 straight segments, 296 vias (168 GND), 1,797.140178 mm track; 380 F.Cu / 564 B.Cu / 13 In2 segments and no In1 signal routing. All six production route families, selected from the actual build sequence, dry-draw **every segment and via exactly** against current pad positions. This is source correspondence, not a new complete build.

## R15-RTE-01 — Minor, new: avoidable fixed-anchor routing length

An independent screen of all nets considered 265 same-width two-to-eight-segment windows and 695 exact one/two-segment alternatives. It removes the gate's turn-back threshold and permits changed bend locations on the same headings. It found 22 overlapping sketches. Fifteen non-overlapping windows below survive a genuine combined-copy refill, native reference/region checks, full routing gate and real KiCad10.0.7 all-severity/parity DRC: **0 violations, 0 unconnected, 0 parity, 0 ignored checks**.

They shorten track by **10.008727 mm**, replacing 38 segments with 30; 919 target segments, every via, footprint/pad pose/net and zone outline match. Candidate hash is `7f49c3c75965594e4b33b2d3bb433eb00a89485db7fff8d6a09246b4bdc2ac1e`. Exact original/new integer geometries and source families are preserved in the JSON.

| Net | Layer | Source family | Width mm | Save mm | Candidate points mm |
|---|---|---|---:|---:|---|
| GND | B.Cu | core | 0.3 | 0.287035 | `(23.86,54.85) → (23.86,53.69) → (24.35,53.2)` |
| PORT_5V3 | B.Cu | power | 0.4 | 0.322183 | `(25.9,10.3) → (26.45,10.85) → (26.45,12.6)` |
| 3V3 | B.Cu | signals (r10_route_sd) | 0.2 | 0.190381 | `(27.725,17.9) → (27,18.625) → (27,19)` |
| SWDIO | F.Cu | usb | 0.2 | 1.376598 | `(3.73,38.45) → (6.08,36.1) → (12.6,36.1)` |
| SWCLK | F.Cu | usb | 0.2 | 0.263604 | `(5,38.45) → (6.85,36.6) → (14.3,36.6)` |
| ACT_EN_MCU | F.Cu | pyro | 0.2 | 0.451056 | `(25.3,67.2) → (21.77,67.2) → (19.6,69.37)` |
| 3V3A | B.Cu | core | 0.25 | 0.263604 | `(17.05,48.31) → (17.5,47.86) → (17.5,46.86)` |
| 3V3A | B.Cu | core | 0.25 | 0.415908 | `(15.79,46.65) → (15.79,47.6) → (16.5,48.31)` |
| BAT_FAULT_N | F.Cu | signals | 0.2 | 1.221930 | `(22.175,70) → (22.175,80.475) → (19.3,83.35)` |
| BAT_FAULT_N | B.Cu | signals | 0.2 | 0.234315 | `(26,47.3) → (26,51.55) → (26.9,52.45)` |
| SD_CS | B.Cu | signals (r10_route_sd) | 0.2 | 2.697547 | `(20.8,33.5) → (26.105,28.195) → (26.105,24.3)` |
| BAT_ENABLE | F.Cu | power | 0.2 | 0.585786 | `(14.075,67) → (15.3,67) → (16.3,66)` |
| BAT_ENABLE | B.Cu | power | 0.2 | 0.776167 | `(19.675,66.4) → (21,67.725) → (21,68.6)` |
| CAM_5V | B.Cu | power | 0.4 | 0.336827 | `(34.2,49.325) → (33.625,48.75) → (33.15,48.75)` |
| BUZZ_G | B.Cu | signals | 0.2 | 0.585786 | `(17.5,58.7) → (17.5,60.2) → (18.5,61.2)` |

This is not a proposal to apply the whole copy. Its information count is **140 versus139**: collinear nodes0→1, off-centre entries57→59, inside-pad segments22→23, extra-bend instances6→7; tiny jogs6→4 and U-turns6→4. Noncritical hygiene leftovers fall8→6. Geometry savings alone do not make every drawing choice better. Windows were qualified together, not individually, and no production build, fit/fab/budget regeneration or electrical test follows from this copy.

Concrete fix: choose worthwhile windows through the named generators, retain exact widths/anchors/T contacts, merge new collinear nodes and assess pad entries; then regenerate, rebind and run the complete unchanged gate. Re-extract affected electrical models. Retain any worthwhile remaining compromises for owner acceptance.

## R15-RTE-02 — Minor, carried: complete M2 and return inventory

Fresh target `route_check --profile r10 --bumps-all --routes` exits0: no blocking, allowlisted, stale, removable-critical-bump or removable-noncritical-bump instance (54 gate bump windows). Its **139 actual information instances =109 ordinary +22 AUD-10 inside-pad +8 noncritical hygiene**. Supplemental search sketches are not extra production instances.

| Category | Current count |
|---|---:|
| detour | 1 |
| extra_bends | 6 |
| pad_end_offcentre | 57 |
| passes_through_pad | 1 |
| power_via_no_gnd | 24 |
| segment_inside_pad | 22 |
| short_layer_hop | 3 |
| short_segment | 1 |
| tiny_jog | 6 |
| u_turn | 6 |
| via_on_track_in_fill | 1 |
| width_change_junction | 11 |

The eight location-only leftovers, counted once as audit2 requires, are:

| Category | Net | Layer | x,y mm |
|---|---|---|---|
| short_segment | BAT_OVLO | B.Cu | 16.4,83 |
| tiny_jog | BAT_FAULT_N | B.Cu | 26,47.3 |
| tiny_jog | BUZZ_DRV | F.Cu | 20.5,51.8 |
| tiny_jog | BAT_FAULT_N | B.Cu | 28.2,47.5 |
| tiny_jog | I2C1_SDA | B.Cu | 9.97,51.5 |
| tiny_jog | BAT_ENABLE | F.Cu | 19.675,66 |
| tiny_jog | BAT_ENABLE | B.Cu | 21,68.6 |
| detour | USB_ILIM | net | 14.825,27.2 |

The JSON contains every current instance, all per-net routes and18 review-only no-pour chain stretches exceeding1.25× and0.5mm. Those stretches are geometric observations, not proof of needless routing around current obstacles. USB_ILIM is the sole net-level detour:3.332107mm against1.049264mm MST, one required transition. No general impossibility claim is made.

An independent literal-polygon query finds **nine track-end matches at five pad sites**, using <=0.03mm depth and >0.1mm centre offset: C129.2 `(29.35,52)` twice, L1.2 `(24.2,77)` once, R432.1 `(35.02,58.05)` twice, J3.A4B9 `(7.45,28.4)` twice and R120.2 `(18.23,73.3)` twice. R432 depth is0.020mm; the other listed endpoints reach the polygon boundary. This broader diagnostic includes GND/VBUS entries and is distinct from the earlier narrower five-record inventory. Track width still supplies copper contact; it is not a demonstrated open circuit or new mandatory penetration floor.

Four current between-pad lanes are explicitly retained: 3V3 through C84 (minimum0.540mm), BAT_FAULT_N through C22 (0.200mm), USB_FAULT_N through C28 (0.200mm), RAW_ACT sense branch through R87 (0.275mm). These are native polygon distances; the earlier0.200041mm figure used another polygonization. The source/copy comparison also preserves U4's small MOSI entry offset and the unmodified fast-interface cells.

**Returns and numerical scope.** All25 required signal transitions have a GND via within1.5mm; worst is PYRO1_GATE `(14.4,53.3)` to `(15.35,52.15)`,1.491643389mm. K-reference has159,810 samples,10,051 unreferenced:10,045 inside own antipads and6 matched by5 REF_STRAY records around SPI1_MISO/SCK; **0 loose**. K-region has163 items/62,590 samples and0 issues. A passing reference gate does not mean every sample lies over continuous copper.

AUD-2 is exactly14 named slow nets; fast UART/USB/HSE/SPI/QSPI/SD and critical hygiene retain their gate scope. Deliberately applying region checks to all14 yields11 disclosed observations (5 runs,5 pads,1 connected chain), not11 distinct nets. NRST/BOOT0/I2C are outside the specified fast companion rule; nearest-GND maxima are3.679674/1.662077/2.232543mm. SWD/reset reference coverage remains in the reference check. The three short power hops remain PORT_5V3 F.Cu0.8mm, RAW_PROTECTED F.Cu1.4mm and B.Cu0.8mm. Twenty-four power-via companion observations and C98's in-fill overlapping-ring stitch remain information, not silently exempted critical failures.

Fresh S-8, S-9, K-width, K-inner, K-copper and K-retained checks pass. Fire paths use1.0mm BAT_IN and0.5mm RAW_ACT/IGN/OUT; seven exact0.4mm source bridges retain their measured exception. No series fire via is introduced. Two exact U401 filled/capped in-pad vias remain the sole ordinary-SMD exception. Flash/C29 direct route1.870mm and SD bypass distances2.680019/5.057571mm pass their retained bounds. Maker recommendations on short/wide bypass/return geometry are qualitative, not a measured transient or thermal guarantee.

Concrete fix: keep these exact target-bound counts, locations and return-scope limits in the final deviation inventory; simplify practical residuals through generators without trading away safety/reference/power behavior solely to lower counts, and obtain dated owner acceptance of retained M2 deviations. Reset/I2C/HSE/power/interface bench qualification remains separate.

## Full-lens coverage and primary sources

The review covered all current owner amendments (116 D IDs and22 owner-mandate records), current requirements/physics, route families, signal classification, slow exemptions, fire/power widths, layer transitions/reference regions, all-net angles/staircases/jogs/stubs/dead copper/overlaps/crossings/neck-downs, pad entries, short/extra hops and source correspondence. The JSON records exact checks and rejected Major/Critical hypotheses. No actual AGENTS section2 violation or demonstrated required-function failure was found.

All four copper layers were freshly plotted from this PCB and inspected. The creator's [R2 studio photograph](https://x.com/bps_space/status/1299081393029382144), SHA`298e3f2c91a2db2864bc0ec61d38b74014358995eb724a9632205ec4cdac7255`, was independently inspected after root supplied the exact primary bytes. It supports comparison of visible edge rows, a central processor, bottom passive rows/local cells and supply/buzzer placement. R10 follows those visible organizational choices under its later single-switch, always-on-port, hinged-SD and seven-DB125 amendments. GPS/radio cells are not exact translated copies after the maximum-terminal/THT clearance corrections; camera isolation and the retained fast core constrain their pockets. The photo establishes no inner copper, private circuit or alternate mandatory safety design. No new AVA-layout function defect is demonstrated.

Complete relevant primary pages were rendered with Poppler and inspected fresh: [Diodes DS41326 Rev3-2](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf) p15; [TI TPS25947 SLVSFC9C](https://www.ti.com/lit/ds/symlink/tps25947.pdf) pp62–63; [TI TPS2121 SLVSEA3F](https://www.ti.com/lit/ds/symlink/tps2121.pdf) p33; [TI TPS7A91 SBVS282A](https://www.ti.com/lit/ds/symlink/tps7a91.pdf) p25. Their layout guidance informed the power/return review; no physical performance was inferred from pictures or geometry alone.

## Limits and rejected probes

The independent search is bounded to fixed anchors, widths/layers and exact one/two-segment alternatives; it uses0.16mm diagnostic copper screening versus actual0.15mm DRC and does not prove global optimality. The BUZZ_G sketch bypassing an unsplit T was rejected by candidate-A DRC. Candidate-B passed DRC but the probe's float round-trip caused1nm width changes and synthetic neck-downs; exact-width candidate-C passes both routing and DRC. Its writer had a post-save SWIG teardown failure; only later independent readers/CLI results are credited. One inadvertent candidate-B DRC/API-scan overlap was disclosed to root. The first obsolete-family, SVG-rasterization and direct-photo-fetch attempts failed and were corrected, not treated as successful checks.

No current peer15 report/probe was read; no GUI, subagent, canonical build/full check, git mutation or production edit was used. Existing stale0c50b9fd copper renders were not current evidence. Target CLI DRC was not separately rerun by this lens; the stated CLI DRC results belong to ignored candidate copies. No firmware, physical, electrical/thermal/transient/endurance, installed RF/ESD, e-match or manufacturing qualification is claimed. The two reports are the only new durable outputs from this lens; ignored probes preserve exact reproduction evidence for the supervisor.
