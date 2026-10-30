# R10 vehicle integration handoff

The separately owned `../../docs/VEHICLE.md` candidate entry still describes
removed R10 hardware. This handoff supplies its replacement facts without
editing that worktree. Preserve the accepted R9 entry. The exact current PCB,
review and build binding is in [R10_VALIDATION.md](R10_VALIDATION.md); R10 remains
unaccepted and no physical fit is claimed.

**Full R16/R17 pair complete (2026-10-30):** PCB
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`,
46 x 90 x 1.6 mm, 2,256,162 bytes; 209 footprints, 951 segments, 296 vias
(168 GND), 1788.675665 mm track. Full R16 on `b1b8658` found
0 Critical / 0 Major / 11 Minor groups from 17 raw observations (5 new/6 carried),
with all 1,942 files frozen. Full R17 on `ac483f4` found
0 Critical / 0 Major / 13 Minor groups from 23 raw observations (4 new/9 carried),
with all 1,966 files frozen through ten complete lenses. The same-PCB clean pair
is earned; original reports remain immutable. R16 reviewed 119 D IDs/22 owner
mandates; R17 reviewed 122/23. The final record index has **126 D IDs through
D-R17-04 and 23 mandates**; later record/check amendments do not enlarge either
sealed review's scope.

**Software/CAD:** two complete R15 builds/check0 reproduced 42 generated files
on this PCB; one complete R16 build/check0 matched both snapshots. There is no
new R17 full build. R15 retains its 31-rule/176-R10-test/60-route-test scope;
R16 passed 32 rules, 180 R10/31 fit/16 paste/5 parts/67 route tests, with all four
native NumPy skips separately resolved. Orientation, all 618 paste geometries
and the five-output manifest passed in that execution. R17 corrections affect
docs/checks and text-only pin-table/binding provenance. The refreshed binding
changes only pin_table_sha256; electrical assignments/axes and the other41
recorded generated files stay unchanged. The manifest-gate fix has7 shell
regressions. **Final post-R17 canonical check: exit0.** All32rules,7shell/180R10/31fit/16paste/5parts/67route tests and five-output manifest pass; all4native NumPy skips separately resolved. Evidence: round17_fix_validation.json.

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

All coordinates below are PCB millimetres, as in `m3_design/r10_place.tsv`.

| Terminal | Centre / rotation | Outward entry | Contact order |
|---|---|---|---|
| J121 black DB125-2 | (7.4,55.85), -90 degrees | west | OUT, IGN |
| J400 green DB125-2 | (7.4,65.85), -90 degrees | west | external screw-switch pair |
| J1 green DB125-2 | (7.4,75.85), -90 degrees | west | BAT+, GND |
| J410 green DB125-4 | (38.6,15.5), 90 degrees | east | 4V8, GND, board TXO, board RXI |
| J420 green DB125-4 | (38.6,31.5), 90 degrees | east | 4V8, GND, board TXO, board RXI |
| J9 green DB125-4 | (38.6,47.5), 90 degrees | east | camera supply, GND, board RXI, board TXO |
| J122 green DB125-5 | (38.6,71.5), 90 degrees | east | SERVO1-4, reference GND |

There is no J124, ARM plug/link/fuse, pull-pin, wired GH connector, servo header,
servo tie hole, on-board radio/GNSS or SMA/coax overhang. GPS and LR900-F radio
use always-on shared PORT_4V8 and direct protected UARTs. The camera alone keeps
its switch and UART isolation. The USB-C shell still reaches 0.45 mm past the
west PCB edge.

Future R10 programming must record/read back intended user-flash BOOT_ADD0
and relevant boot settings, then verify reset reaches the bound application with
e-match disconnected. BOOT0 low alone permits ROM entry at BOOT_ADD0=0x1FF0;
PA2 can then drive loader USART2_TX onto servo3. No actual programming/readback
or R10 firmware is claimed. Preserve the dummy-load/no-e-match,before-IWDG,
locked-low PC1/PE4,camera EN/OE low and SD_CS high service procedure.

U5's retained1.1 mm model/cover height is an engineering allocation; TE's package
height is1.0 mm +0/-0.10 (06/2017 p15 Fig18). At4 mm the allocated gap is2.9 mm,
package-only3.0 mm; seating,cover compression,adhesive and venting remain unqualified.

The sole J400 screw switch is the power/pad-arming device, reachable on the rail,
on last and off first. Connect the e-match without USB or self-powered back-feed
sources. USB bench work requires the pack or e-match disconnected. Preserve
AGENTS section 2 and the electrically isolated Blue Jay. Qualify dry contacts,
strain relief, ferrules/gauge, polarity/UART order and installed RF immunity.

The board is 46 x 90 x 1.6 mm. Retain supports at (4,4), (42,4), (4,44.3),
(3.7,86) and (42,86), nylon/covered hardware and underside insulation. Start
with the selected 4 mm standoffs, nut on sled side and head on top, measured
nut-inclusive h+t below 6.0 mm at x4/42 and below 5.3 mm at x3.7. Program J2
before installing the adjacent mid support, or remove it for programming.
Hardware maxima, eccentricity, solder tails, plate strength and shock clearance
remain unqualified. The optional 100 g/D5 model leaves only 0.270913 mm below C431
at h4; h3.5 predicts overlap. This is an inference, not a physical result.

Maximum DB125 insulating bodies are in the VRML models. The fit checker separately
allocates all 23 solder tails to their native pad XY boxes and 3.80 mm maximum
length below the seating plane (conservative Inference, not a solder-joint model).
Their minimum calculated bore clearance is 7.558359 mm; projection below the
1.60 mm PCB is 2.20 mm, leaving 1.80 mm to a nominal 4 mm sled plane. Seating,
solder fillets and bent tails still need inspection. The bare-bore OQ-1 benchmark
is 5.003012 mm at every wire face against the accepted 4.95 mm floor, only
0.053012 mm margin. It is not a ferrule/bend/tool-envelope qualification.
DB125 accepts 28-16 AWG; verify actual leads, 4-5 mm strip, ferrules, screw
access and retention. Its maximum body height is 8.90 mm and tail is
3.50 +/-0.30 mm. Stake all seven terminals, including J400. The nominal
Ø1.30mm holes/Ø1.90mm lands do not establish pin insertion at all process corners.
Obtain the maker/assembler insertion profile and fabricator hole/pattern/barrel
allocation; inspect all23 contacts for seating, undamaged plating/barrels and solder
fill. Nominal S-8 minimum1.102501576mm is not a fabricated-clearance qualification.
Exact C19/C20 combined operating capacitance/ESR, process/rework/aging and actual
regulator-mode/local-temperature qualification also remain open; see ORDERING §8.2.

J430 is the bottom hinged Molex microSD socket at (24,24.3). The current fit
check covers a 15.05 x 15.70 x 2.10 mm closed socket/card allocation, including
the maker's nails and general tolerances. Common seating and the undimensioned
card front remain Inference; verify the actual assembly. Open it unpowered with
the PCB removed/unbolted from a continuous sled, or qualify a lid-access window.
The maker does not dimension the full open sweep. Card retention and selected-
card latency, current and power-loss behavior remain unqualified.

Keep the entire board, including axial mounting tolerance, forward of
joint+47 mm at every roll orientation (OQ-7). Freed PCB length stays slack.
Do not reuse the old GH 0.03 mm margin or SMA/coax lead zone as fit evidence.
Fit the actual pack, external GPS/radio, antenna, harness, accessible switch,
sled and camera shroud together. Use [ORDERING section8.1.1](ORDERING.md#811-pad-energy-worksheet-d-r17-01-calculationinference)
and D-R17-01: C_tested_Ah >= (Q_pad_board + Q_pad_motors + Q_flight_all
+ Q_recovery)/0.8. The conditional two-hour board-only capacities at camera
0/0.5/2 h are2.265821/2.987991/5.154503 Ah under the stated6 V/80% allocations;
they exclude motor,flight and recovery charge and select no pack. Camera off
unless recording; verify aged/cold capacity,fire-time source reserve/resistance,
transients and installed mass/dimensions. The previous approximately80 mm pack
description and retired2.6/4 Ah examples prove none of them.

**R16 retained MEMS stress deviation (R16-MEC-01, Minor):** component-side B.Cu
still crosses U4's nominal body outside its lands: IMU_CS 0.7596+0.0918 mm,
SPI1_MISO 0.3257 mm,IMU_INT1 0.3250 mm and3V3A 0.3257 mm (0.001mm midpoint sampling;
native body x15.50..18.50/y44.65..47.15). Signal widths are0.20mm; the0.25mm
3V3A rail also departs from the same-width guidance. These specifically depart from
[ST TN1383 Rev1 pp7–9](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf)
pad-axis/outside-body stress guidance. The R15 GND correction and passing M-7/P3
checks are narrower than complete compliance. The bounded supply prototype
has only0.106949mm clearance; the next combined recipe creates an acute45degree
CS junction at B(14.2,44.7). Both are rejected, with no production copper change
or full PCB/CLI/gate qualification of that MEMS recipe. Retain first-article
bias/temperature/vibration qualification. [Prototype evidence](../m3_design/assembly_review/sources/r10_review/round16_minor_prototypes.json)
and R16-MEC-01/D-R16-02 preserve the limits; no offset error or physical failure
is demonstrated.

The exact2026-10-30T17:15:34.705395..17:15:45.842149UTC supplier snapshot gives
79.5232USD placed/81.8636USD minima before fixed/process/PCB/shipping. Cost-only
target passes; R43017<3610/U4zero<5 keep stock release,quote/process and
owner acceptance open. U9stock83/minimum7 for five fitted is included. No physical
fit,firmware or order is qualified.

Current source/qualification details: [M3_R10.md](M3_R10.md),
[ORDERING.md section 8](ORDERING.md),
and the maker-linked `sources/r10_design/parts_qualification.md`. Apply the parent
mirror update only within its separately authorized repository workflow.
