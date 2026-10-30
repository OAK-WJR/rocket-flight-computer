# R10 vehicle integration handoff

The separately owned `../../docs/VEHICLE.md` candidate entry still describes
removed R10 hardware. This handoff supplies its replacement facts without
editing that worktree. Preserve the accepted R9 entry. The exact current PCB,
review and build binding is in [R10_VALIDATION.md](R10_VALIDATION.md); R10 remains
unaccepted and no physical fit is claimed.

Current PCB is `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`,
46x90x1.6mm,2,256,162bytes,951segments/296vias/1788.675665mm track.
Full R16 onb1b8658/632a9ad3 completed0Critical/0Major/11Minor groups from17raw
(5new/6carried); all1942committed files stayed unchanged. FullR17 on this same
PCB is pending. The two R15 complete builds/check0 and42-file equality apply
to it. One new R16 integrated build/check exits0:DRC/unconnected/parity/ERC0,
all32rules including K-binding,180R10tests,31fit/16paste/5parts/67route. All four
native NumPy skips are separately resolved. Its42generated files match both
R15snapshots; orientation,618paste geometries and five-output manifest pass.
Fresh2304+60local hot-plug cases pass as Simulation/Inference; assembly-page
rasters match b1b8658 despite PDF metadata-byte changes. This is one new build,
not a second new-build pair. The separate final standalone check also exits0
with32rules/180R10tests/67route and all four native NumPy skips resolved.
Full R16 originally covered119D IDs/22mandates; current amendments total122D IDs
throughD-R16-03/23mandates. The latest supervisor steer forbids PCB,placement,
routing or circuit-generator changes for Minors and cancels queued SD adoption.
Retain its measured1.994603mm/two-segment saving for owner acceptance. Commit
R16,then fullR17 on the same632a9ad3; if also0Critical/0Major,finalize the
records,commit and report. Only a confirmed Critical or Major warrants PCB changes.
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
sled and camera shroud together. The conditional 2.6 Ah / 4 Ah pad-duty pack
cases require installed capacity, voltage reserve, mass and dimensional checks;
the previous approximately 80 mm pack description proves none of them.

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

The exact2026-10-30T15:30:06.601825..15:30:40.008183UTC supplier snapshot gives
79.5232USD placed/81.3254USD minima before fixed/process/PCB/shipping. Cost-only
procurement passes; R43017<3610/U4zero<5 keep stock release,quote/process and
owner acceptance open. No physical fit,firmware or order is qualified.

Current source/qualification details: [M3_R10.md](M3_R10.md),
[ORDERING.md section 8](ORDERING.md),
and the maker-linked `sources/r10_design/parts_qualification.md`. Apply the parent
mirror update only within its separately authorized repository workflow.
