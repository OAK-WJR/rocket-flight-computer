# R10 AVA layout hand-off

**How to read this file (R19-DOC-08).** For the current board `a0ec075e…` read "Round 26 fix pass" at the end (two
GND vias added at J440, and four bottom parts and four vias moved from `92c3ad59…`), then "Round 24 fix pass" (one
capped chamfer, which made `92c3ad59…`) and, before it, "Round 24 board pass", which lists the changes from `5516eeec…` ("Round 21 CAD fix
pass", the board of rounds 22 and 23) to `1407e850…`. The current placement itself is
`m3_design/r10_place.tsv` and the board; everything above the round 18 section is history of earlier boards.
Sealed historical sections keep their original text, including run-together words and numbers (R19-DOC-04); only the
current-status paragraphs were respaced in round 19.

This is the immutable hand-off measurement record for `0c50b9fd…` below.
**Round 26 fix pass (2026-11-02):** the current CAD candidate is the PCB recorded in "Round 26 fix pass" at the end
(D-R26-01..04); "Round 24 fix pass" records its predecessor `92c3ad59…`, which rounds 25 and 26 reviewed, and "Round 24
board pass" records `1407e850…`, which round 24 reviewed.
**Round 24 board pass (2026-11-01):** the round 24 PCB is recorded in "Round 24 board pass"
(D-R24-01..17); "Round 21 CAD fix pass" records its predecessor `5516eeec…`, which rounds 22 and 23 reviewed.
**Round 21 CAD fix pass (2026-10-31):** the current CAD candidate is the rebuilt PCB recorded in
"Round 21 CAD fix pass" at the end (D-R21-01..09); "Round 20 CAD polish pass" records its predecessor `0dc84776…`.
**Round 20 CAD polish pass (2026-10-31):** the round 20 PCB is recorded in "Round 20 CAD polish pass"
(D-R20-01..11); "Round19 CAD fix pass" records its predecessor `50a39de5…`.
**Round 19 CAD fix pass (2026-10-30):** the round 19 PCB is recorded in "Round19 CAD fix pass"
(D-R19-01..14); "Round18 CAD fix pass" records its predecessor `a3144b15…`.
**Round 18 CAD fix pass (2026-10-30):** the round 18 PCB is recorded in "Round18 CAD fix pass" below
(D-R18-01..10); the 632a9ad3 paragraphs below are its predecessor's record.
**Full R16/R17 pair complete (2026-10-30):** PCB
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`,
46 x 90 x 1.6 mm, 2,256,162 bytes; 209 footprints, 951 segments, 296 vias
(168 GND), 1788.675665 mm track. Full R16 on `b1b8658` found
0 Critical / 0 Major / 11 Minor groups from 17 raw observations (5 new/6 carried),
with all 1,942 files frozen. Full R17 on `ac483f4` found
0 Critical / 0 Major / 13 Minor groups from 23 raw observations (4 new/9 carried),
with all 1,966 files frozen through ten complete lenses. The same-PCB clean pair
is earned on that board (it does not carry to `a3144b15…` or `50a39de5…`); original reports remain immutable. R16 reviewed 119 D IDs/22 owner
mandates; R17 reviewed 122/23. The final record index has **126 D IDs through
D-R17-04 and 23 mandates**; later record/check amendments do not enlarge either
sealed review's scope.

**Software/CAD (on `632a9ad3…`):** two complete R15 builds with check exit 0 reproduced 42 generated files
on this PCB; one complete R16 build with check exit 0 matched both snapshots. There is no
new R17 full build. R15 retains its scope of 31 rules, 176 R10 tests and 60 route tests;
R16 passed 32 rules and 180 R10 / 31 fit / 16 paste / 5 parts / 67 route tests, with all four
native NumPy skips separately resolved. Orientation, all 618 paste geometries
and the five-output manifest passed in that execution. R17 corrections affect
docs, checks and text-only pin-table / binding provenance. The refreshed binding
changes only pin_table_sha256; electrical assignments, axes and the other 41
recorded generated files stay unchanged. The manifest-gate fix has 7 shell
regressions. **Final post-R17 canonical check: exit 0.** All 32 rules, 7 shell / 180 R10 / 31 fit / 16 paste / 5 parts / 67 route tests and the five-output manifest pass; all 4 native NumPy skips separately resolved. Evidence: round17_fix_validation.json.

**Simulation/Inference:** the R16 actual-feed 2304 required +60 local hot-plug
cases passed. The optional 181.1 Hz pinned-D5/70.5 g plate result remains the
R15 calculation on this same PCB. No physical qualification follows.

**Procurement:** original supplier queries 2026-10-30T17:15:34.705395..
17:15:45.842149Z give $79.5232 placed/feeder share and $81.8636 with minimum
purchases, below $84.41 before fixed/process/PCB/shipping costs. R430 17<3610
and U4 0<5 still fail stock release; U9 has 83 available/minimum7 for five fitted.
Quote/process and owner cost/deviation acceptance remain pending; nothing ordered.

**Retained Minors:** no PCB, placement, routing or circuit-generator change for
Minors (D-R16-03). SD_MOSI's measured 1.994603 mm/two-segment alternative remains
a deviation; no adoption is queued. MEMS signal/supply stress guidance, L400 land,
DB125 insertion/S-8 process allocation, VCAP conditions, M2/returns, courtyard
graphics and the separate vehicle mirror remain measured deviations with open
qualification limits.
The four new R17 groups receive record/check corrections; no physical or owner
acceptance is inferred. Only a confirmed Critical/Major permits a board change.

**Not verified:** R10 firmware/boot configuration, physical safety timing and
selected-lot 20 ms firing, SD latency/power loss, electrical/thermal/transient/
endurance, installed RF/ESD, harness/switch/retention, tool/card access, physical
bore/stack/flight and first-article/process. AGENTS section2 is unchanged.
R9 remains accepted; R10 remains unaccepted and unordered.
Current integration scope: [R10_VALIDATION](../../../../docs/R10_VALIDATION.md), round16.

Round11 found one confirmed Major/16Minor groups on the hand-off board and
fixed it as `0ad0135c…`; its named historical proof remains separate. The
historical measurements below describe `0c50b9fd…`; fix deltas are at the end.

Candidate PCB SHA-256: `0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`. Baseline: commit `ff15523`, PCB
`6e73b6ebe7e25d7a8c810493887fbaa7cce34f6fe1d379828dc67017e14235aa`. This is a placement/routing change generated by
`r10_place.tsv`, the R10 routing families and `r10_post.py`; the circuit, parts, pin assignments,
five supports, outline and IMU pose are unchanged. AGENTS §2 is unchanged.

Two complete `m3_design/r10_build.sh` runs, including full `tools/check.sh` with
`NUMPY_PY=.supervisor/venv/bin/python`, exited 0. The PCB and all 23 recorded generated
CAD, binding and model files are byte-identical between builds.

At this hand-off no independent round had run. Round11 is now complete and is
not clean; rounds9/10 cover historical`b337fe63…` only. No acceptance or order is claimed.

## Placement and the AVA comparison's §6

This §6 table is the hand-off record for `0c50b9fd…` (seven terminals, 40 legends); the round sections at the end hold the later changes.
The owner-supplied AVA comparison is a layout reference. Later owner decisions supersede its old
three-sense-bank, switched-port and connector assumptions. Reasons and local placement choices are
in [R10_DECISIONS.md](R10_DECISIONS.md).

The west terminal centres are x=7 mm: J121 IGN at y=55.85, J400 switch at 65.85 and J1 battery at 75.85
(10 mm pitch). The east centres are x=39 mm: J410 GPS at y=15.5, J420 radio at 31.5 and J9 camera at 47.5
(16 mm pitch), then J122 servos at 71.5. Every wire entry faces outward. Calculated wire room is
**4.953 mm at all seven terminals**, against the accepted 4.95 mm floor. IGN remains black and BAT green.
Terminal pin roles and labels remain unchanged; the radio is no longer parked on the west edge.

| §6 item | Result and qualification |
|---|---|
| 1. Battery/protection | U9, D8, C80/C96/C88, damper, C82/D9 and bias parts cluster at J1; U11/U2/C84 immediately inboard. C88 remains before U9. The actual-feed hot-plug model passes 2304/2304 cases (simulation / Inference). C82 and D9 keep the original local-loop bounds. |
| 2. Port cells | GPS and radio use identical bottom resistor/ESD/capacitor cells translated 16 mm. Camera repeats their terminal-side lanes and keeps U402/U12/U13. Its larger envelope is the cost of its switch/isolation, ADC column and clear through-lanes. |
| 3. Sense cells | The two retained pyro banks use repeated series/parallel/filter columns at x=23/28 mm, with the filtered ends toward the MCU. Camera and VLOGIC diagnosis form an east column. The owner-deleted duplicate bus bank and ADC tail resistors stay deleted. |
| 4. Buzzer | Whole cell below PC14: BUZZ_DRV 53.186 to 8.213 mm, seven vias to one. PC13 remains NC. |
| 5. In2 | Recut the rails into broader regions; short 3V3A trunk and the USB_LIMITED feed use power-only In2 copper. Preserve the local crystal GND region, fire-barrel exclusion, In1 GND and continuous fast references. USB power is longer because it uses the west corridor clear of the SPI3 fan. |
| 6. Bottom R/C | Terminal lanes, divider ladders, servo pull-down pairs and the battery cell use local rows. Decouplers, switching loops and gate parts follow their electrical constraints. C14/C24 turn for adjacent escapes; C15/C16/C19 move only enough to clear the bus-sense and U12 bypass. No package conversion. |
| 7. Flash/buffer escapes | All six QSPI signals retain one F-to-B transition. Radio RX/TX and camera RX/TX now each have one transition; their old two-via hops are gone. QSPI_IO2 remains 14.524 mm: its pin map and sensor/reference corridor are retained, with no matching meander or timing claim. |
| 8. Legends | All 40 legends fit, including individual terminal pin legends and six short J2 rows beside J2. No connector-association fallback and no >6 mm legend-distance item. Text/mask/support checks pass. Two library pin-1 dots move for clearance; pads/lands do not change. |
| 9. GND stitches | Local returns follow the moved cells; C16/C23, C100/QSPI guard, R405/D410, C60/C431 and C80/C96/D9 share existing/local returns where legal. Camera divider/filter returns remain separate to clear the supply via. GND vias fall 171 to 166; fast partners and the exact two U401 VIPPO thermal vias remain. |
| 10. Probes | TP80/81/83/88 follow battery/supply subjects; TP120/121/122 follow the bus switch and fire gate; TP82 follows USB protection. Bare-contact and support clearances remain gated. **Current board (R19-RTE-02):** TP121 and its ACT_GATE stub are removed (D-R19-03), so ACT_GATE is probed at the bare R119.1 / R120.2 / C120.2 pads before coating, as AVA probes values at part pads (D-AUD-05); TP82 moved to B(11.0,17.6) beside J440 (D-R19-14), then to B(11.2,20.7) on its spur's diagonal (D-R20-04). |

## Measurements

Track lengths are sums of straight track centre-lines, excluding pours and via barrels.

| Measure | Baseline | Candidate |
|---|---:|---:|
| Vias | 303 | 294 |
| Track length (mm) | 1878.150 | 1818.770 |
| Track segments | 887 | 981 |
| Footprints | 209 | 209 |
| Board area (mm²) | 4140 | 4140 |

Block area is the orthogonal bounding envelope of member courtyards projected across both faces, including gaps.
Block envelopes overlap and are **not additive occupied board area**. Membership is identical on both boards;
[ava_layout_metrics.json](ava_layout_metrics.json) records every member, box and actual courtyard-area sum.

| Block | Footprints | Envelope before / after (mm²) |
|---|---:|---:|
| Battery and protection | 26 | 1475.3 / 890.5 |
| USB, mux, hold-up and 3V3 | 34 | 2431.9 / 2324.3 |
| MCU, clock and debug | 18 | 549.8 / 551.3 |
| QSPI and sensors | 12 | 333.6 / 333.6 |
| Voltage diagnosis and indicators | 12 | 473.1 / 507.5 |
| Port buck and LDO | 18 | 628.0 / 530.1 |
| GPS | 7 | 249.0 / 172.1 |
| Radio | 7 | 631.9 / 172.1 |
| Camera | 21 | 462.4 / 614.0 |
| Pyro bus switch | 10 | 91.2 / 103.2 |
| Pyro firing and sense | 21 | 407.8 / 406.6 |
| Servos | 10 | 402.0 / 252.0 |
| Buzzer | 5 | 118.6 / 71.4 |
| microSD | 8 | 349.2 / 349.2 |

The number of segments increases despite the lower total length; via escapes and explicit local cell connections
account for that change. Some routes grow to preserve reference/clearance and repeat the terminal pattern:

| Net | Length before / after (mm) | Vias before / after |
|---|---:|---:|
| BAT_IN | 81.727 / 61.292 | 1 / 1 |
| BUZZ_DRV | 53.186 / 8.213 | 7 / 1 |
| GPS_RX_MCU | 28.521 / 31.745 | 0 / 1 |
| GPS_TX_MCU | 26.463 / 28.765 | 0 / 1 |
| RADIO_RX_MCU | 23.402 / 11.618 | 2 / 1 |
| RADIO_TX_MCU | 23.386 / 10.703 | 3 / 1 |
| CAM_MCU_RX | 8.741 / 7.381 | 2 / 1 |
| CAM_MCU_TX | 5.795 / 7.311 | 0 / 1 |
| PYRO1_CONT | 16.166 / 6.876 | 1 / 1 |
| ARM1_SENSE | 24.642 / 12.868 | 1 / 1 |
| QSPI_IO2 | 14.524 / 14.524 | 1 / 1 |
| USB_LIMITED | 56.042 / 83.269 | 2 / 3 |

The battery feed is measured separately from its resistor/TVS branches:

| Feed | Before / after (mm) |
|---|---:|
| J1.1 to C88.1 | 47.412 / 30.671 |
| C88.1 to U9.5 | 3.920 / 3.920 |

The extracted hot-plug graph and numerical results are in `hotplug_inputs.json` / `hotplug_results.json`.
They remain simulation / Inference; the actual pin waveforms, harness and component behavior are unmeasured.

## Review items and limits

The full board contract has 31 passing rules, including S-1…S-9, K-reference, K-region, K-copper, K-retained,
F9-1/F9-2, P-11 and fit. Routing has zero blocking findings and zero critical allowlist entries. P-11 was extended
to all seven DB125s; the source-bridge coordinate records move with unchanged copper; three fault-injection fixtures
were repaired for the new placement. No limit was relaxed. The build regenerates fabrication before the full gate,
so the manifest is checked without a skip. Firmware binding evidence is refreshed by the complete build;
firmware itself is not implemented or approved.

Both full gates pass the shell (4), fit (25), paste (5), routing (60) and R10 (160) regression suites.
The R10 suite reports three skips in KiCad Python: its two required hot-plug numerical tests are separately
rerun successfully with NumPy; the remaining skip is the optional plate diagnostic. No required gate is skipped.
The fabrication package has 82 BOM codes / 199 placed parts, 66 top + 121 bottom CPL rows and 12 additional
placement-only checks. Orientation, paste and all five manifest outputs pass.
[ava_layout_validation.json](ava_layout_validation.json) records both build-log hashes and the 23 matching file hashes.

Audit 2 keeps the following **12 noncritical routing findings** for review. They are not hidden by new exceptions:

| Category | Net | Layer | x, y (mm) |
|---|---|---|---|
| micro_segment | SERVO1_OUT | B.Cu | 39.015, 78.5 |
| micro_segment | SERVO1_MCU | B.Cu | 34.21, 75.31 |
| short_segment | BAT_OVLO | B.Cu | 16.4, 83 |
| tiny_jog | V3V3_SENSE | B.Cu | 26.25, 52.5 |
| tiny_jog | BAT_FAULT_N | B.Cu | 26, 47.3 |
| tiny_jog | LED_YEL | F.Cu | 15.45, 43 |
| tiny_jog | BUZZ_DRV | F.Cu | 20.5, 51.8 |
| tiny_jog | BAT_FAULT_N | B.Cu | 28.2, 47.5 |
| tiny_jog | BAT_ENABLE | F.Cu | 19.675, 66 |
| tiny_jog | BAT_ENABLE | B.Cu | 21, 68.6 |
| detour | USB_FAULT_N | net | 8.625, 23.1 |
| detour | USB_ILIM | net | 14.825, 27.2 |

AUD-10 also counts 27 inside-pad segments and two collinear nodes for review. Their exact locations, the
noncritical findings above, and the hidden-reference list are in
[ava_layout_review_items.json](ava_layout_review_items.json). There are 122 shown designators and 87 hidden
where no unambiguous ≥1 mm spot fits; every hidden reference remains on Fab. Four top parts use a bottom
reference under their own part. Every required legend and reference check passes.

Not done: shortening QSPI_IO2 beyond the retained one-via route; removing every informational routing item;
independent review rounds; owner acceptance; firmware, SD latency/power-loss tests, electrical/thermal/EMC tests,
e-match lot firing, harness/DB125 screwdriver and bore/stack fit, coating/assembly/process qualification.
The unchanged BOM carries forward the circuit-pass cost/stock evidence only; no new supplier quote is claimed.

Four copper SVG/PNG pairs and their board-hash manifest are under `.supervisor/r10_copper/`, with assembly
renders under `.supervisor/r10_renders/`. They are local review artifacts and are not committed.

## Round 11 fix-pass delta

The corrected maximum DB125 envelopes require row centres x=7.4/38.6 mm.
Every terminal now has 5.003011866 mm calculated wire room against 4.95 mm;
the old 4.953 mm hand-off claim used an understated body and is superseded.
Maximum adjacent 4P bodies have 0.48 mm gap. Native fit/DRC and a fresh
terminal verifier pass; physical wiring and screwdriver access remain open.

Local bottom cells move to retain the unchanged 1.5 mm THT assembly floor.
GPS/radio cells therefore no longer remain exact translated copies: the SD
socket, camera isolation and existing signal corridors constrain their pockets.
C91's input connection is 4.092 mm directly / 5.036 mm routed; transient and
return qualification remain open. Servo clamps and pull-downs stay fixed;
the first two output routes retain centred terminal entries without in-pad tails.
Exact poses and measured reasons are in D-R11-01 and the M6/servo receipts.

The fix pass has 973 segments, 295 vias (167 GND) and 1809.708732 mm of track,
versus 981 / 294 / 1818.769511 mm at hand-off. Six routing simplifications and
the necessary local returns account for the net change. Circuit, pin map,
supports, outline and IMU pose are unchanged. The current 40 legends pass;
118 designators are visible and 91 are hidden on Fab, with four top-part
designators on the bottom under their subject. Ordinary terminal GND contacts
now have explicit thermals. The two specified U401 VIPPO sites remain the sole
SMD via-in-pad exception. No flight, firmware, physical or owner acceptance is implied.

## Round12 fix-pass delta

The current PCB is `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`,
46x90mm,2,264,839bytes;973 segments/296 vias/1808.300406mm track.
This supersedes the opening R11 pointer while retaining every historical
measurement at its stated hash. Native comparison preserves all original part
poses, pad lands/nets, GND tracks and via geometry/flags; only BAT_ENABLE's three
F.Cu segments change, one ordinary0.5/0.3mm GND stitch at(23.8,62.95) is added,
and the five recorded Fab labels change. BAT_ENABLE saves1.408326mm. C98's
saved-copper return falls31.812237->7.345584mm; its in-fill annotation and actual
transient qualification remain deviations. No AVA-hidden-copper claim follows.

Two full native builds/check0 reproduce all42 recorded generated files byte
for byte. Package/binding are refreshed; all31 R10 rules and current fabrication
checks pass. R12 on the prior committed0ad board was0Critical/0Major/12Minor
groups; fresh full rounds13/14 must review this committed result. Exact proof,
scope and limits: `sources/r10_review/round12_fix_validation.json`. AGENTS
section2, circuit/pins/axes/supports and owner decisions are unchanged. No
firmware/physical qualification, acceptance or order is inferred.

## Round13 fix-pass delta

PCB `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`:209footprints,
966segments/296vias/1802.125220mm track. Exact native comparison
preserves all parts/lands/nets,vias,GND tracks,supports and axes. Qualified
same-layer signal redraws and77 Fab references change; the microSD model now
includes maker nails/tolerances and fit separately allocates23 maximum terminal
tails. No electrical,thermal,assembly,harness or physical qualification follows.
The source receipts are round13_routing_fix,round13_fab_fix,round13_root_fix
and round13_gate_fix; complete canonical integration is round13_fix_native and
round13_fix_validation. Full R13 was0C/0M/17Minor groups on7355/fa897c8. Fresh
complete14/15 on this committed result must earn the final clean pair.

## Round14 fix-pass delta

PCB `7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`:209footprints/957segments/296vias,
1797.140178mm track. Twelve individually qualified source redraws
save4.985043mm/nine segments; all part poses,pads,nets,vias,zone outlines and Fab
references remain unchanged. Only the obsolete USB_DM reference exception is
retired. Native hot-plug is freshly extracted/swept; no physical result follows.
Maker LS1200.5g,optional mass-key/paste-subset guards and current records are
corrected. Full proof:round14_fix_native/round14_fix_validation; source decisions
D-R14-01..03. Full15/16 on the committed successor are pending.


## Round15 fix-pass delta

PCB `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`:
209 footprints,951 segments,296 vias (168 GND),1788.675665mm track,2,256,162 bytes.
Fifteen exact fixed-anchor route windows save10.008727mm/eight segments. U4's two
shared pad-row GND straps are replaced by individual pad-axis/45degree escapes
that join outside the nominal body at the same vias. This adds1.544214mm/two
segments, giving net8.464513mm/six segments saved. All part poses,lands/nets,
fields/models,vias,zone outlines and Fab references remain unchanged. GND tracks
change; this is not complete TN1383 stress/process or sensor-performance qualification.

Both complete native builds with check exit 0 pass all 31 rules, DRC / unconnected / parity / ERC 0, routing, fit,
orientation, 618 paste geometries and the five-output manifest. R10 suite 176, fit 31,
paste 16, routing 60 and the four separately resolved native NumPy skips pass.
All 42 generated files reproduce byte for byte; final assembly-page rasters match
and complete pages were inspected. Fresh optional plate estimates: 181.1 Hz
pinned (D5) at 70.497598846 g (70.5 g rounded), Calculation/Inference. The actual-feed 2304 + 60
hot-plug cases pass as Simulation/Inference. Routing on that board had 140 information
instances = 111 ordinary + 23 AUD-10 inside-pad + 6 noncritical hygiene leftovers, 59 off-centre
entries and 46 all-net bump windows; blocking, allowed, stale and critical bumps are 0.
The new 0.475 mm CAM_5V B(33.625,48.75) segment inside U13.1 is AUD-10 information.
These and other M2 compromises remain owner deviations; full native counts are in
[round15_fix_native](../r10_review/round15_fix_native.json). Exact DB125 insertion/fabricated
barrel allocation and C19/C20 operating C/ESR/process qualification are open.
D-R15-01…03 records those changes. Full R16 has now reviewed 632a9ad3;
current pair/gate status is in the opening record and the follow-up below.

## Round16 records and gate follow-up (unchanged PCB)

**R16 retained MEMS stress deviation (R16-MEC-01, Minor):** component-side B.Cu
still crosses U4's nominal body outside its lands: IMU_CS 0.7596+0.0918 mm,
SPI1_MISO 0.3257 mm, IMU_INT1 0.3250 mm and 3V3A 0.3257 mm (0.001 mm midpoint sampling;
native body x 15.50–18.50, y 44.65–47.15). Signal widths are 0.20 mm; the 0.25 mm
3V3A rail also departs from the same-width guidance. These specifically depart from
[ST TN1383 Rev 1 pp 7–9](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf)
pad-axis / outside-body stress guidance. The R15 GND correction and passing M-7 / P3
checks are narrower than complete compliance. The bounded supply prototype
has only 0.106949 mm clearance; the next combined recipe creates an acute 45 degree
CS junction at B(14.2,44.7). Both are rejected, with no production copper change
or full PCB / CLI / gate qualification of that MEMS recipe. Retain first-article
bias / temperature / vibration qualification. [Prototype evidence](../r10_review/round16_minor_prototypes.json)
and R16-MEC-01 / D-R16-02 preserve the limits; no offset error or physical failure
is demonstrated. (Still true on `50a39de5…`: no copper under U4 changed in rounds 18 and 19; R19-RTE-08 carried.)

The exact-duplicate and saved-binding gate corrections change no production
copper, part, pose, pin or axis. One integrated R16 build with check exits 0 with 32 rules,
180 R10 tests and 67 route tests; all four native NumPy skips are separately resolved. Its 42
files exactly match both R15 snapshots, with no second new-build pair claimed.
Full R16 on b1b8658 /
632a9ad3 is 0 Critical / 0 Major / 11 Minor groups from 17 raw observations (5 new / 6 carried), all 1942 files unchanged;
full R17 on ac483f4 / 632a9ad3 is complete: 0 Critical / 0 Major / 13 Minor groups from 23 raw observations (4 new / 9 carried), all 1966 files unchanged. The same-PCB pair is earned on that board. The text-only R17 binding provenance is refreshed; the final post-R17 canonical check exits 0; no new R17 full build is claimed. R16's separate standalone check exited 0
with the same 32 rules / 180 R10 / 67 route tests and all four native NumPy skips resolved.
The supervisor steer of that time cancelled queued SD_MOSI adoption and kept the measured
1.994603 mm / two-segment saving for owner acceptance (the round 18 fix pass later adopted it, D-R18-07). No PCB, placement, routing or
circuit-generator changes for Minors were made then; only confirmed Critical / Major changes
warranted CAD edits. Then-current 126 D IDs through D-R17-04 and 23 owner scopes are indexed in
the final ledger; full R16's sealed original scope remains 119 / 22. D-R16-03
supersedes D-R16-02's former post-pair adoption plan without erasing that history.


## Round17 record completion (unchanged PCB)

The opening record states the completed same-PCB R16/R17 pair. The four new
R17 groups receive pad-energy,boot-address,U5 source-label and manifest-gate
corrections; courtyard stroke metrics are corrected in R10_VALIDATION without
changing the 16 graphic pairs or physical geometry. Retain all measured M2,
SD / MEMS / L400 / DB125 / VCAP / process / vehicle qualifications and no queued Minor CAD
adoption. D-R17-01..04 are record / check amendments after R17's 122-ID
review; they do not enlarge its sealed scope. The final canonical check exits 0. No new R17 full build or physical, firmware or owner acceptance is claimed.


## Round18 CAD fix pass (new PCB; D-R18-01..10)

The root orchestrator reopened CAD for ten round-18 Minors (brief `.supervisor/r18_fix_cad_brief.md`); every change
is in the generators, footprints and checks, with two complete `r10_build.sh` builds. PCB
`a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918`, 46 x 90 x 1.6 mm, 2,250,842 bytes;
208 footprints, 947 segments, 292 vias (166 GND), 1788.737627 mm track (R17 632a9ad3: 209 / 951 / 296 (168) /
1788.675665 mm).

| Change | Placement / copper |
|---|---|
| R62, R63 removed (D-R18-01) | V3V3_SENSE divider and vias (25.5,51.75), (25.07,54.7), (25.07,57.6) gone; PC3_C NC |
| R123 2 k (D-R18-01) | same land F(20.6,70.66) -90 |
| R119 added (D-R18-02) | B(11.57,71.1) 0; ACT_GATE via (11.8,70.725) -> (11.14,71.7) |
| TP121 (D-R18-02) | B(10.5,71.5) -> B(4,70) |
| ACT_EN_MCU / BAT_FAULT_N (D-R18-03) | x 26.5 -> 26.62 / x 26.9 -> 27.37; U11.12 GND via (25.8,65.9) removed |
| Barrel keep-outs (D-R18-04) | 6 fill-only areas round the ACT_GATE / BAT_ENABLE vias and J400.2 |
| R173 (D-R18-05) | B(23.0,59.2) 90 -> B(16.87,59.7) -90; IGN diagonal 0.5 mm SW; BUZZ_G lead x 17.5 -> 17.75; C126.2 GND via (16.178,59.047) -> (15.8,59.425) |
| In2 zones (D-R18-06) | CH1 GND tongue removed; 3V3 shoulder + bay; RAW notched; 3V3 In2 fill 1 piece |
| SD_MOSI (D-R18-07) | one 45-degree run, -1.995 mm, -2 segments |
| L400 / U4 lands (D-R18-08) | L400 2.0 x 1.8 mm at +/-2.25 mm; U4 mask expansion 0 (webs 0.150 mm) |
| R430 / C84 (D-R18-09) | R430 C2999509 (no copper change); C84 in the owner BOM only |

Silkscreen designators (r10_post's unchanged rule): 91 -> 88 hidden; R91 is newly hidden (kept on F.Fab); R132 and
R163 are now shown; R119 and TP121 are shown; R62/R63 are gone. All other part poses, lands, nets and supports are
unchanged; the IMU axis map (roll = -gyro_Y) and U1's pin map except PC3_C are unchanged.


## Round19 CAD fix pass (new PCB; D-R19-01..14)

The root orchestrator reopened CAD for thirteen round-19 Minors (brief `.supervisor/r19_fix_cad_brief.md`) and the
owner's spare AUX port (item 14, `.supervisor/r19_aux_port_brief.md`, D-R19-14); every change is in the generators,
footprints and checks, with two complete `r10_build.sh` builds (`../r10_review/round19_fix_cad.md`). PCB
`50a39de5b76dec3cb58bbb1b0ab528fd4d65098de9dfe8f89f49e2e7adcbd976`, 46 x 90 x 1.6 mm, 2,336,742 bytes; 215 footprints,
984 segments, 301 vias (169 GND), 1870.487095 mm track (round 18 a3144b15: 208 / 947 / 292 (166) / 1788.737627 mm).

| Change | Placement / copper |
|---|---|
| PYRO1_OUT barrels (D-R19-01) | 2 fill-only areas on In1 / In2 round the OUT via (11.63,55.1) r 1.20 and J121.1 r 1.70 |
| BAT_ENABLE via (D-R19-02) | (19.675,66.4) -> (19.675,66.6); B.Cu (19.675,66.6) -> (21.0,67.925) -> (21.0,68.6) |
| TP121 (D-R19-03) | removed with its B.Cu stub (11.14,70.0) -> (4.0,70.0) |
| C123 added (D-R19-04) | F(18.22,71.85) 0; ACT_EN Q122.1 -> C123.1; GND C123.2 -> (19.207,71.85) -> via (19.967,71.09) |
| U1.19 (D-R19-05) | pad zone connection none; the 1.693 mm^2 F.Cu GND fragment is gone |
| Second vias (D-R19-09) | VLOGIC (29.8,81.15); PORT_5V3 (42.75,61.8), (26.45,11.95), (24.9,14.9); PORT_4V8 (29.75,9.95) |
| C87 / U4 (D-R19-10 / -11) | same lands; C21120 220 nF; ISM6HG256XTR C51931514 (CPL rotation 0 -> 180 from its EasyEDA footprint) |
| C84 (D-R19-07) | no paste on its library footprint |
| AUX port J440 (D-R19-14) | F(7.4,16.25) -90, wires west; top cell C444 F(12.5,12.6) -90, C445 F(15.2,13.4) -90, D440 F(13.9,17.2), R471 F(16.1,18.0) 180, D441 F(13.9,21.4), R470 F(16.1,20.6); AUX pair F.Cu only from U1.63 / U1.64 (USART6) |
| J410 UART (D-R19-14) | GPS pair from U1.55 / U1.56 (USART3): north between C90's vias and RADIO_TX, NE beside the radio pair, then the former run at x 28.8 / 29.3; C23.2's fan-out via (27.1,34.2) -> (25.95,34.15) |
| AUX feed (D-R19-14) | F.Cu 0.4 mm from vias (29.75,9.95) and new (30.5,9.95) along y 9.95 / 11.0 to J440.1 |
| R90 / TP82 (D-R19-14, M-6) | R90 B(7.8,23.1) -> B(11.275,23.0), 3V3 via (6.2,23.1) -> (9.6,23.0); TP82 B(10.8,21.3) -> B(11.0,17.6); stitches (7.0,22.0) removed, (2.0,9.0) -> (0.9,9.0), (16.5,12.5) -> (17.5,12.0) |

Silkscreen: RADIO and BAT at reviewed word spots (D-R19-06); twelve terminal pin legends at reviewed spots wholly
outside the DB125 render envelopes, 2:E1+ and 2:SW on the bottom beside their pins and J420's wire-side pair in an outer
column (D-R19-08); R80 / R81 / R123 / C5 / C407 / R89 / J121 held at their round 18 designator spots, J400's on the top
board-edge strip and J122's in the C84 / J122 gap (D-R19-12); D8, C404, C408 and LED2 moved, R88 and C123 hidden.
D-R19-14: AUX word F(13.4,10.2), J440 1:4V8 on the west strip, its 2:GND / 3:TXO / 4:RXI on the bottom; the AUX cell and
J440's courtyard move the C400, C401, R90, R462 and R463 designators and leave no unambiguous spot for C28, R110, D440
or D441 (hidden, kept on F.Fab: 88 -> 94 hidden in all). All other part poses, lands, nets and supports are unchanged;
the IMU axis map (roll = -gyro_Y) is unchanged; U1's pin map changes only at pins 55 / 56 (GPS, USART3) and 63 / 64
(AUX, USART6).

Counts on `50a39de5…` (round 19 docs lane, read-only parse of the board): 121 designators shown and 94 hidden
(C28, R110, C123, D440, D441 and R88 newly hidden; TP121 removed), 45 silkscreen legends, eight DB125 terminals with
27 contacts. The full hidden list is in `docs/M3_R10.md`, "Silkscreen and assembly identification".

## Round 20 CAD polish pass (new PCB; D-R20-01..11)

The supervisor's last surgical pass before the closing review pair (brief `.supervisor/r20_fix_cad_brief.md`), from
round 20's seven board lenses (0 Critical / 0 Major on `50a39de5…`). Every change is in the generators, the generated
footprint library and the checks, with two complete `r10_build.sh` builds (`../r10_review/round20_fix_cad.md`). PCB
`0dc847761de94a45cf68b1c82ec91f38e9d4ebb7297abc7108e3df9a454940d3`, 46 x 90 x 1.6 mm, 2,340,154 bytes; 215 footprints, 985 segments, 302 vias (169 GND), 1874.854252 mm track
(round 19 `50a39de5…`: 215 / 984 / 301 (169) / 1870.487095 mm).

| Change | Placement / copper |
|---|---|
| U9 EN pull-down (D-R20-01) | not moved: no legal clean B.Cu spot at U9.1 (measured; respin item) |
| U401 FB tap (D-R20-02) | PORT_4V8 via (30.575,11.6) into the In2 output plane, 0.4 mm F.Cu stub to R402.1; no single via cuts R402.1 off |
| U1.74 (D-R20-03) | pad zone connection none; the 0.282 mm^2 F.Cu GND piece is gone |
| TP82 (D-R20-04) | B(11.0,17.6) -> B(11.2,20.7); spur one segment (15.55,25.05) -> (11.2,20.7) |
| Terminal rings (D-R20-05) | library M3_DB125_2P_BK pad 1 and M3_DB125_2P_GN pad 2 keep copper only where connected: J121.1 and J400.2 have no inner rings; J1.2 keeps its In1 thermal, loses its unconnected In2 ring |
| Fab references (D-R20-07) | C445 / D440 / D441 / C123 / R119 / R173 clear of their Fab outlines |
| West aft tab (D-R20-08) | fill-only In2 area R20_TAB_KEEPOUT_WEST_AFT, x -0.5..3.0, y 12.5..17.5: no In2 3V3 under the tab; the east tabs unchanged |
| AUX clamps (D-R20-09) | D440 F(13.9,17.2) -> B(4.45,19.45) -90, D441 F(13.9,21.4) -> B(4.45,23.05) -90, under J440 on the wire side; B.Cu pin -> clamp runs; returns (3.75,19.775), (3.75,23.375); top taps and vias (14.225,16.45), (14.225,22.15) removed |

Silkscreen (D-R20-06): C400 re-placed and C94 / R461 hidden by the any-size courtyard test. This pass's copper also
moves R402, R463, C444, R470, D440 and D441 and J440's 3:TXO (to B(10.5,17.5)), shows C28, and hides C404, R90 and
U401 (94 -> 96 hidden, all kept on F.Fab). Every other part pose, land, net and support is unchanged. U1's pin map and
the IMU axis map (roll = -gyro_Y) are unchanged.

## Round 21 CAD fix pass (new PCB; D-R21-01..09)

The CAD lane's pass on round 21's ten lenses (0 Critical / 0 Major on `0dc84776…`; brief
`.supervisor/r21_fix_brief.md`). Every change is in the generators and the checks, with two complete `r10_build.sh`
builds (`../r10_review/round21_fix_cad.md`). PCB `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1`,
46 x 90 x 1.6 mm, 2,336,572 bytes; 215 footprints, 983 segments, 300 vias (167 GND), 1871.611826 mm track (round 20
`0dc84776…`: 215 / 985 / 302 (169) / 1874.854252 mm).

| Change | Placement / copper |
|---|---|
| Inner PTH hole clearance (D-R21-01) | DRU rule "JLC inner-layer PTH pad hole to copper" 0.55 mm (+ outer PTH to track 0.28, pad hole to hole 0.45): J1.2 In2 RAW_PROTECTED and J400.2 In1 GND 0.251 -> 0.550 mm, J3.1-4 In2 3V3 0.451 -> 0.550 mm; every other plated pad unchanged; plane strips at J1 / J400 1.40 -> 1.10 mm and at J3 0.479-0.633 -> 0.379-0.566 mm, no fill splits |
| U2.1 second path (D-R21-02) | B.Cu 3V3 0.4 mm (24.05,68.95) -> (23.0,70.0) into R89's via; no single via cuts U2.1 off |
| Schematic notes (D-R21-03) | text only (sensors, diagnostics, battery_entry) |
| BAT_ENABLE hop (D-R21-04) | B.Cu (19.675,66.6) -> (20.7,67.625) -> (20.7,68.3) -> (21.3,68.9) (was (21,67.925) -> (21,68.6), a 0.424 mm jog); F.Cu corner (19.675,66.0) -> diagonal from (19.075,66.0) |
| EN pull-down and filter (D-R21-05) | R81 F(20.5,65) -> F(18.8482,80.0) 0; C87 F(17,65) -> F(18.7232,81.8768) 0; pads 1 on the F.Cu EN run, pads 2 in U9.8's F.Cu GND; stubs and the GND vias (20.706,65.619), (16.639,63.939) removed |

Silkscreen (D-R21-09): C126, Q122 and R122 shown again, and C80, C87, C89, D123, D8 and R81 re-placed by the designator
search (96 -> 93 hidden, all kept on Fab); no legend moved. Every other part pose, land, net and support is unchanged.
U1's pin map and the IMU axis map (roll = -gyro_Y) are unchanged. Items 6-8 (D-R21-06..08) are checks only.

## Round 24 board pass (new PCB; D-R24-01..17)

The CAD lane's pass after the closing pair (rounds 22 and 23, 0 Critical / 0 Major on `5516eeec…`). Every change is in
the generators and the checks, with complete `r10_build.sh` builds C and D giving the same board
(`../r10_review/round24_board_cad.md`). PCB `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e`,
46 x 90 x 1.6 mm, 2,363,869 bytes; 216 footprints, 1057 segments, 307 vias (168 GND; 302 at 0.5 / 0.3, 4 at 0.6 / 0.3,
1 at 1.0 / 0.5 mm), 1867.022756 mm track (`5516eeec…`: 215 / 983 / 300 (167) / 1871.611826 mm).

| Change | Placement / copper |
|---|---|
| J400.2 ESD clamp (D-R24-11) | New D402 (ESD103-B1-02EL, C535146) B(4.45,65.9) rot 90 under J400 between its pins; B.Cu tap from J400.2's own pad (7.4,67.6) -> (4.81,67.6) -> (4.45,67.24) -> (4.45,66.225), 4.114 mm, ahead of R165; D402.2 0.7 mm to its own GND via (5.15,65.575) |
| Q120 / Q121 gate drive (D-R24-02) | Second ACT_GATE barrels (15.4,72.85) and (11.74,72.3), each joined on F.Cu and B.Cu to the first |
| BOOT0 (D-R24-03) | Second barrel (14.2,46.0), B.Cu diagonal to (13.8,45.6); R5 stays on B.Cu |
| VCAP2 (D-R24-04) | Second barrel (18.3,36.8) on stubs to U1.73's drop and C20.1's run; VCAP1 unchanged (no legal spot) |
| U402.2 GND island (D-R24-07) | Second GND via (32.3,60.1) on a 0.3 mm B.Cu link; U10.2 / R8.2 islands unchanged |
| Monitor taps (D-R24-08) | Second vias R60.1 (34.5,62.4), U1.28 (30.45,51.4), R91.1 (28.1,59.4) |
| U401 divider (D-R24-09) | R402 F(31.4,12.6) -> B(30.9,12.85) rot 0; R403 F(31.4,14.4) -> B(30.9,14.6) rot 180; vias (29.75,13.6), (30.575,11.6), (31.4,14.4) removed; U401 OUT via (29.75,12.6) -> (29.75,11.65) |
| USB OV leg (D-R24-10) | Second barrel (16.6,28.0) at R87.1's input layer change |
| Order mark (D-R24-13) | JLCJLCJLCJLC no longer drawn |
| Short-edge parts (D-R24-15) | R92 F(31,87.5) -> F(31,86.7); TP88 F(35.5,87) -> F(35.5,86.4); their vias (30.175,85.9), (32.65,86.7), (36.6,86.4) |
| 90-degree bends (D-R24-17) | 59 -> 0, chamfered or redrawn at source; C88 B(19.4,83.95) rot 90 -> B(18.67,83.56) rot 0 with its GND via (19.59,84.06); U9's IN via now (17.5,87.15); C82.1's second In2 via (21.1,79.1) -> (21.1,78.25); U400's second input via (14.1,8.5) |

Kept, measured (no change): U4.6 / U4.7's GND via (D-R24-01), U9's EN cell (D-R24-05), U11.2 and the two 3V3A feeds
(D-R24-06), R87.1's drop and R85.1 (D-R24-10), the east tabs (D-R24-14), the Fab body outlines (D-R24-12) and the
optional cleanliness items (D-R24-16). Silkscreen: C87 and R402 hidden, C16, C20 and C404 shown again, D402's designator
shown (93 -> 92 hidden, 124 visible, 44 legends; all hidden references kept on Fab). Every other part pose, land, net
and support is unchanged. U1's pin map and the IMU axis map (roll = -gyro_Y) are unchanged.

## Round 24 fix pass (new PCB; D-R24-18..23)

The CAD lane's pass on the round 24 triage (0 Critical / 0 Major, 17 Minor real errors on `1407e850…`;
`../r10_review/round24_fix_cad.md`). Builds E and F gave the same board. PCB
`92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f`, 46 x 90 x 1.6 mm, 2,363,951 bytes; 216 footprints,
1057 segments, 307 vias (168 GND), 1867.046187 mm track (`1407e850…`: the same counts, 1867.022756 mm).

| Change | Placement / copper |
|---|---|
| BAT_FAULT_N chamfer at the EN via (D-R24-18) | CHAMFER_CUTS ('BAT_FAULT_N', 'F', 16.55, 83.35): 0.32 (was the fixed 0.36): (16.55,80.9)-(16.55,82.99) -> (16.55,80.9)-(16.55,83.03); (16.55,82.99)-(16.91,83.35) -> (16.55,83.03)-(16.87,83.35); (16.91,83.35)-(19.3,83.35) -> (16.87,83.35)-(19.3,83.35). BAT_ENABLE via (17.1,82.8) to BAT_FAULT_N 0.173 -> 0.200 mm (the legs; the chamfer 0.2015 mm) |

No via, pad, footprint, legend or support moved; the zone fills were re-poured around the new corner. D-R24-19 ..
D-R24-23 change generated text, checks and records only (check_r10 rule M-8 holds every courtyard 2.5 mm from the
short edges, with six recorded DFM queries). U1's pin map and the IMU axis map (roll = -gyro_Y) are unchanged.

## Round 26 fix pass (new PCB; D-R26-01..04)

The CAD lane's pass on the round 26 triage (0 Critical / 0 Major, 12 Minor real errors on `92c3ad59…`;
`../r10_review/round26_fix_cad.md`), with the root's follow-up D-R26-04. Builds A and B gave the same board. PCB
`a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, 46 x 90 x 1.6 mm, 2,369,507 bytes; 216 footprints,
1059 segments, 309 vias (170 GND), 1866.794 mm track (`92c3ad59…`: 1057 segments, 307 vias (168 GND), 1867.046187 mm).
Builds 2 and 3 had first given the intermediate `4108e6fa…` (1058 segments, 1866.026 mm; never committed or reviewed),
on which R164's 3V3 via at (19.05,55.25) sat 0.331 mm from R126.1 (PE4's net PYRO1_GATE_N, F.Cu) and C10's Fab /
pad envelope at B(17.5,53.45) 2.994 mm from U5's body-and-pad union (inside ORDERING 8.3's 3 mm coat exclusion);
D-R26-04 moved that via, C10 and PYRO1_CONT_MID's diagonal again. C10's envelope is now 3.017 mm from that union
(pads alone 3.449 mm).

| Change | Placement / copper |
|---|---|
| AUX GND partner vias (D-R26-01) | GND vias 0.5 / 0.3 mm at (7.4,16.5) and (7.4,20.0), 1.500 mm from J440.3 / J440.4, in the F.Cu / B.Cu GND pours and joined to In1 GND (the In2 3V3 fill clears them); M3_DB125_4P_GN pins 3 / 4 keep no unconnected inner ring (J410, J420, J440, J9) |
| 3V3A column and R173 (D-R26-02 / -04) | C11 B(17.5,52.1) -> B(17.5,51.45), C10 B(17.5,54.1) -> B(17.5,53.5) (0.60 mm, D-R26-04), R164 B(17.325,55.9) -> B(17.325,55.25), R173 B(16.87,59.7) -> B(16.87,59.05), rotations unchanged; 3V3A trunk (16.5,50.2)-(16.5,51.45)-(16.5,53.5)-(16.5,55.25); C11.2 return (18.5,51.45)-(19.423,52.373) to via (19.423,52.373); C10.2 return (18.5,53.45)-(19.65,53.45) to via (19.65,53.45), leaving the pad on the via's line, 0.05 mm from the pad centre inside the land (D-R26-04) |
| R164's 3V3 via (D-R26-02 / -04) | (19.05,55.9) -> (19.55,55.825); strap (18.15,55.25)-(18.975,55.25)-(19.55,55.825) |
| R13's 3V3 via (D-R26-02) | (9.2,52.98) -> (9.2,52.55); strap (10.25,52.98)-(9.63,52.98)-(9.2,52.55) |
| PYRO1_OUT / PYRO1_CONT_MID (D-R26-02 / -04) | PYRO1_OUT's last vertical (16.87,57.97)-(16.87,58.62); PYRO1_CONT_MID (16.87,59.48)-(16.87,60.82)-(17.85,61.8)-(20.83,61.8) (the chamfered 90 at (16.87,61.8) is gone) |

11 segments removed and 13 added; the zone fills were re-poured. C18's designator is hidden (its spot (19.32,50.38) now
lies on C11.2; 92 -> 93 hidden, 123 visible, 44 legends); no other designator or legend moved. PYRO1_OUT is at least
1.040 mm from 3V3 / 3V3A on every layer, and Q124's gate nets (PYRO1_GATE_N, PE4's net, and PYRO1_GATE) at least
1.0585 mm (R128.1; D-R26-04; 0.835 / 0.676 mm on `92c3ad59…`). R164's new via is 0.2335 mm from BUZZ_DRV's B.Cu
diagonal and 0.206 mm from LS120.3 (no net, F.Cu). BUZZ_DRV / PYRO1_OUT's minimum fell from 0.964 to 0.794 mm
(R162.1 to R173.1, B.Cu): a bridge there may fire an enabled match (Inference, D-R26-04), and the cold screen refuses
one present at power-up. D-R26-03 changes generated text only. Every other part pose, land, net and support is
unchanged. U1's pin map and the IMU axis map (roll = -gyro_Y) are unchanged.
