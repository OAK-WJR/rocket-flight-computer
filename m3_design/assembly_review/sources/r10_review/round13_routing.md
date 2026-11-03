# Round 13: full routing, M2, AVA, planes and returns

Target commit `fa897c81abac3026e75ca5cc88bef0c2659a7130`, PCB SHA-256
`7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`.
**0 Critical / 0 Major / 3 Minor groups: one new cleanup, two carried geometry groups.**
The PCB hash is identical before and after review. Canonical CAD and sources were read-only.
Complete native measurements, every routing instance, redraw coordinates and check evidence are in
[round13_routing.json](round13_routing.json).

## Findings

**R13-RTE-01 — Minor, new: a simpler camera RX-buffer route is fully checked.**

`m3_design/r10_route_signals.py:53`, CAM_RX_BUFFER, B.Cu, 0.2 mm:

- Current: U12.1 `(30.05,40.55)` → `(30.25,40.75)` → `(30.25,44.8)` → `(31.2,45.75)` → R100.2 `(33.174999,45.75)`.
- Tested redraw: U12.1 → `(30.05,42.625001)` → R100.2.
- Length **7.651345 → 6.494417 mm**, saving **1.156928 mm**; four segments become two. Pads and vias stay fixed.

The isolated native alternative was refilled and passes all-severity KiCad 10.0.7 DRC/unconnected/parity
**0/0/0**, S-8/S-9/F9-2/K-copper/K-inner/K-reference/K-region/K-width/K-retained/K-fill and the complete production
route scan, with no critical removable bump. Both CLI invocations had exclusive reservations, explicitly released.
This is a bounded M2 tidiness Minor, with no demonstrated electrical or timing failure.

Concrete source fix: replace `camera_local()`'s CAM_RX_BUFFER polyline by
`[p('U12.1'), (30.05,42.6250), p('R100.2')]`, keeping B.Cu/0.2 mm. The generator rounds to 0.0001 mm;
the tested native knee above retains the endpoint's 1 nm representation difference. Any implementation still needs
a complete native rebuild/gate and refreshed provenance. Alternatively retain this exact M2 deviation for owner acceptance.
The production bump detector intentionally requires backtracking; this monotone route belongs to the rest of M2's manual review.

**R13-RTE-02 — Minor, carried: noncritical return companions remain remote.**

Fresh native F/B-transition measurements:

| Net | Transition, mm | Nearest GND via distance, mm |
|---|---|---:|
| NRST | 14.2,37.3 | 3.679674 |
| NRST | 22.54,38.5 | 1.655174 |
| BOOT0 | 13.8,45.6 | 1.662077 |
| I2C1_SDA | 9.97,51.5 | 2.232543 |

NRST's third transition is 1.486607 mm; I2C1_SCL is 1.443087 mm. Files are `r10_route_usb.py`,
`r10_route_core.py` and `r10_fanout.tsv`. These nets are outside the named numerical 1.5 mm signal scope;
no reset, boot or I2C failure is demonstrated. Retain the actual distances and qualification obligation,
or provide a checked local stitch/route through the generators. This review does not claim every possible
alternative is impossible and requests no fast-rule waiver.

**R13-RTE-03 — Minor, carried: pad entries and other M2 residuals remain.**

Inherited SPI1_MOSI enters U4.14 on B.Cu at `(17.55,44.94)` versus pad centre `(17.50,44.94)`:
**0.05 mm offset**. No new on-axis alternative is qualified here. The native M-7, DRC and fast-reference checks pass.

The full two-pad-axis sweep finds four foreign routes:

| Part | Route/layer | Crossing, mm | Minimum pad-to-track gap, mm |
|---|---|---|---:|
| C84 | 3V3/F | 27.5,79.26 | 0.540007 |
| C22 | BAT_FAULT_N/B | 27,47.3 | 0.200041 |
| C28 | USB_FAULT_N/B | 13.05,24.9 | 0.200041 |
| R87 | RAW_ACT/B | 22,63.875 | 0.275038 |

Five literal near-edge endpoints occur at three pads: L1.2 B `(24.2,77)`, zero polygon depth;
R432.1 B `(35.02,58.05)`, 0.020 mm depth, twice; R120.2/ACT_GATE B `(18.23,73.3)`, zero depth, twice.
Current R10_VALIDATION prose calls that R432.2; correct it to **R432.1**, as the current JSON already does.
These are connected entries, not open circuits. The separate C98 in-fill via/track annotation is also retained:
its centre is 0.300 mm off the preserved track, with 0.050 mm ring overlap and an independent saved-pour contact.

Concrete disposition: retain the single count/location inventory below and exact entry measurements for owner M2
acceptance; fully check any cleanup against native pad shapes, MEMS exclusions and fast references. Do not introduce
noncritical measured-exception paperwork or stale-coordinate gate failures.

## Fresh whole-board evidence

Native inventory: **209 footprints, 973 straight segments, 296 vias including 168 GND, 1808.300406 mm track,
46 × 90 mm, 2,264,839 bytes; no arcs**. Real target KiCad 10.0.7 all-severity DRC has **0 violations,
0 unconnected, 0 parity issues, no ignored checks**. No build, full `check.sh`, ERC or fabrication-generation run was performed.

- Production `route_check --profile r10 --routes --bumps-all`: **0 blocking, 0 critical exceptions, 0 stale**;
  25 critical and 31 noncritical bump windows, no candidate at the production clearance margin.
- All ten selected native routing/power/reference/fill rules pass. K-reference has **160761 samples**, 10056 outside
  fill: 10049 own-antipad samples and seven points covered by six recorded strays; **zero loose samples**.
  K-region checks **165 items / 62984 samples / 39 nets**, zero issues.
- All **25 required critical transitions** have partners ≤1.5 mm; worst is PYRO1_GATE `(14.4,53.3)`, **1.491643 mm**.
  AUD-2's exact slow list does not waive fast interfaces, critical hygiene or S-8.
- S-8's four nearest foreign non-GND inner gaps are **1.103/1.900/2.699/2.100 mm** at J121.1/J121.2/OUT via/GATE via.
  The 1.0 mm floor holds. S-9 holds all fire widths and seven exact source bridges, without a generic neck exemption.
- F9-2 measures C82 OUT/GND/total **3.577817/9.426346/13.004163 mm** and D9
  **6.585534/8.176346/14.761880 mm**, within unchanged engineering limits. These are geometric loops.
- M-7 passes the actual MEMS/via/fill and axis rule. All five terminal GND pads have explicit thermal-relief settings.
  K-copper holds the two exact U401 VIPPO sites as the sole soldered-SMD via-in-pad exception.
- Six focused native synthetic adversaries pass: removable versus walled bump, paired-layer reference preservation,
  overlap-only via, AUD-2 scope, audit2 informational bookkeeping and AUD-10 versus real overlaps.

The **141 production instances** partition as **110 ordinary information items + 22 AUD-10 inside-pad
representations + nine noncritical hygiene leftovers**. Exact collinear-node and duplicate counts are zero.
Ordinary categories are 57 off-centre entries, 24 power vias without a numerical GND companion, 11 width changes at
junctions, seven extra-bend runs, six U-turns, three short layer hops, one through-pad pass and one in-fill via annotation.
Categories overlap the separate sweep and are not added as independent defects.

The nine audit2 leftovers are listed once, by count and location:

| Category | Net/layer | Location, mm |
|---|---|---|
| short_segment | BAT_OVLO/B | 16.4,83 |
| tiny_jog | V3V3_SENSE/B | 26.25,52.5 |
| tiny_jog | BAT_FAULT_N/B | 26,47.3 |
| tiny_jog | BUZZ_DRV/F | 20.5,51.8 |
| tiny_jog | BAT_FAULT_N/B | 28.2,47.5 |
| tiny_jog | I2C1_SDA/B | 9.97,51.5 |
| tiny_jog | BAT_ENABLE/F | 19.675,66 |
| tiny_jog | BAT_ENABLE/B | 21,68.6 |
| detour | USB_ILIM/net | 14.825,27.2 |

The fresh complete M2 sweep finds **28 no-pour chain-detour rows, 32 track/via adjacency rows below0.2 mm,
43 pad/net adjacency rows, three via-ring steps, three short poured links, 38 route/MST/via rows, five pad-edge
ends, 32 cross-layer via folds and 27 power/short-hop rows**. Every row is in JSON. The0.2 mm threshold is a review
trigger; ordinary native DRC remains0.15 mm. An additional all-net fixed-junction 1–2 segment search checks
**80 chains / 203 alternatives**, yielding14 strict geometry candidates. Only CAM_RX_BUFFER receives this lens's full
native alternative qualification; the other13 are explicitly unqualified sketches.

A method correction matters: the inherited R8 sweep's `margin_free()` changes `r7_hygiene.rule_clearance`, but
R10's clearance adapter hardcodes its own extra0.01 mm. That mutation alone therefore does **not** remove R10's
margin. I reran an explicit R10 model at the applicable clearance minus0.0005 mm quantization slack, with controls
that pass a0.155 mm gap and reject0.145 mm. It searches all56 windows and finds **one noncritical LED_YEL sketch**:
`(14.4,43) → (14.4,43.7) → (13.5,44.6) → (12.3,44.6)`,4.200→3.173 mm, plus11 chain sketches.
This LED option has no full native DRC/refill/reference qualification and is not promoted to a demonstrated
functional failure. Keep this supplementary diagnostic separate from the141 production instances and the fully
checked camera fix. No production threshold or canonical source was changed.

## Planes, current returns and AVA scope

In1 is one connected **3760.541955 mm² GND piece**, with all168 GND vias represented and no foreign In1 track.
In2 contains one RAW_PROTECTED piece **1253.985582 mm²**, PORT_5V3 **218.615257**, PORT_4V8 **323.791161**;
crystal GND **37.176062/eight vias**, CH1 GND **237.869755/eleven vias**. 3V3 is **1447.879736 mm²** in three
stitched pieces, with the retained **4.4 ×0.4 mm F.Cu bridge** across the supply corridor.

The named crossband cuts retain1.151902 mm summed PORT_5V3 copper at x41 and0.899 mm in the 3V3 feedback finger
at y67.775, split0.4245/0.4745 mm around a via. That finger is feedback, not the main output bridge.
No >3 mm power fringe narrower than0.5 mm is found; two sub1 mm 3V3 fringe pieces remain in JSON.
These topology/cut measurements are not DC or thermal field solves.

Outer GND has15 F/16 B pieces. The fresh0.05 mm through-copper raster finds no unreached point; maximum reach is
**F12.885534 mm at(45.475,77.525)** and **B15.953911 mm at(12.025,69.925)**. Copper beyond4 mm is
**23.0936%/23.0763%**. No global4 mm requirement is invented. The out-of-scope region diagnostic covers42 nets,
233 items/55992 samples and records51 notices, including slow AUD-2/control/reset/servo routes; it does not turn
those notices into required-function failures.

The former C98 remote-return geometry is remedied: the new ordinary stitch gives **7.345584 mm** from C98.2 to
U11.12 through B/In1, including two conservative full-board via penalties, versus the prior31.812237 mm diagnostic.
[TI SLVSEA3F p33](https://www.ti.com/lit/ds/symlink/tps2121.pdf) gives qualitative close-bypass/short-wide routing guidance,
not a numerical loop limit. Inductance and source-transfer performance remain unmeasured. BAT_ENABLE's complete
four-segment15.639697 mm chain equals its45-degree geodesic; the former1.408326 mm excess is absent in both fresh searches.
Its extra-bend and C98's in-fill annotations remain M2 review items, without restoring the old geometric defects.

QSPI lengths are CLK7.850000, IO0 4.110955, IO1 9.714966, IO2 14.524012, IO3 9.760408 and NCS6.165635 mm,
each with one transition; spread10.413057 mm. No clock/setup/hold qualification follows. Only foreign F.Cu
**NRST0.777817 mm** crosses Y1's nominal body projection; BUZZ_DRV/QSPI_IO2 do not, and In1 GND intervenes.
Reset/I2C/HSE/EMC checks remain bench work.

I inspected all four fresh native copper projections and the creator's
[R2 studio photograph](https://x.com/bps_space/status/1299081393029382144). The visible AVA arrangement supports terminal
rows, a central controller and repeated bottom passives as inspiration. Native R10 has west x7.4 and east x38.6
outward terminal rows, compact battery/buzzer/sense cells and local port ends. The retained camera isolation,
SD socket and through-hole floor explain unequal port pockets; exact translated cells are not an owner requirement.
White solder mask conceals AVA copper. No AVA schematic, inner plane, hidden protection or safety behavior is inferred.

The read-only review covers AGENTS first, both packets, requirements, all110 D IDs and22 owner mandates/newest
amendments, AVA_LAYOUT, M3_R10, R10 validation, R9 severity precedents and the read-only vehicle source.
R9 has no literal severity-definition table; the packet's operational meanings were used. No current-round13 peer
report was read, no subagents were used and no Git action, GUI launch/retry or other-worktree edit occurred.
No physical, firmware, electrical/thermal/EMC, SD/e-match-lot, harness/retention, fit/access, process or flight
qualification is claimed. Owner M2 acceptance remains pending.

**PCB SHA-256 before = after:** `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`.
